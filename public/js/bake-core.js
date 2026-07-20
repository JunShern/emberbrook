/* Shared scene bake pipeline — browser mirror of tools/bakemask.py (the
   production baker; the two must stay in sync — same stages, same order,
   same params). Per-scene config comes from assets/scenes/<name>/bake.json.
   bake-square.html runs it for the square and saves the outputs;
   workflow.html runs it with recording on for ANY scene and shows every
   intermediate stage for review.

   bakemask.py stage order (mirrored exactly):
     threshold -> close -> heal specks -> bay-fill -> corridors ->
     dilate+despeck -> blockedRects -> clearance carve                */
const BakeCore = {
  CFG: {
    W: 336, H: 192, S: 4, FW: 1344, FH: 768,
    // green-flood threshold: a pixel is walkable if green dominates
    green: { min: 90, ratio: 1.25 },
    closeR: 3,            // noise-fill close radius (cells)
    speckMax: 8,          // blocked specks below this size are removed (both phases)
    bayFillR: 4,          // close on BLOCKED space: seals trap-pockets < ~2r cells
    dilateR: 1,           // final walkable dilation (opens pinch points)
  },

  SCENES: ['square', 'forest', 'entrance', 'interior', 'lane', 'gate',
           'descent', 'dellhollow', 'lockfive', 'landing', 'stairs', 'cottage'],

  load(src) {
    return new Promise((res, rej) => {
      const i = new Image();
      i.onload = () => res(i);
      i.onerror = rej;
      i.src = src + '?t=' + Date.now();
    });
  },

  // first candidate that actually loads wins (scene base images differ by name)
  async loadFirst(srcs) {
    let err;
    for (const s of srcs) {
      try { return await this.load(s); } catch (e) { err = e; }
    }
    throw err || new Error('no image loaded');
  },

  // Per-scene config + images. bake.json: { center, corridors, pois, blockedRects? }
  async loadScene(name) {
    const base = 'assets/scenes/' + name + '/';
    const resp = await fetch(base + 'bake.json?t=' + Date.now());
    if (!resp.ok) throw new Error(name + '/bake.json: HTTP ' + resp.status);
    const cfg = await resp.json();
    const scene = await this.loadFirst([base + 'festival.png', base + 'main.png', base + 'gray.png']);
    const raw = await this.load(base + 'maskraw.png');
    return { name, cfg, scene, raw };
  },

  pass(src, hit, r, W, H) {
    const out = new Uint8Array(W * H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      let v = !hit;
      for (let dy = -r; dy <= r && v !== hit; dy++) for (let dx = -r; dx <= r; dx++) {
        const nx = x + dx, ny = y + dy;
        if (nx >= 0 && ny >= 0 && nx < W && ny < H && src[ny * W + nx] === (hit ? 1 : 0)) { v = hit; break; }
      }
      out[y * W + x] = v ? 1 : 0;
    }
    return out;
  },

  components(m, W, H, val) {
    const comp = new Int32Array(W * H).fill(-1);
    const list = [];
    for (let i = 0; i < W * H; i++) {
      if (m[i] !== val || comp[i] !== -1) continue;
      const queue = [i], cells = [];
      comp[i] = list.length;
      let touches = false, minX = W, maxX = 0, minY = H, maxY = 0;
      while (queue.length) {
        const q = queue.pop(); cells.push(q);
        const qx = q % W, qy = (q / W) | 0;
        if (qx === 0 || qy === 0 || qx === W - 1 || qy === H - 1) touches = true;
        if (qx < minX) minX = qx; if (qx > maxX) maxX = qx;
        if (qy < minY) minY = qy; if (qy > maxY) maxY = qy;
        for (const dd of [-1, 1, -W, W]) {
          const n = q + dd;
          if (n < 0 || n >= W * H || Math.abs((n % W) - qx) > 1) continue;
          if (m[n] === val && comp[n] === -1) { comp[n] = list.length; queue.push(n); }
        }
      }
      list.push({ cells, touches, minX, maxX, minY, maxY });
    }
    return list;
  },

  // run(record[, sceneName[, opts]]) — sceneName defaults to 'square' so old
  // callers (bake-square.html) keep working. opts.thresholdOnly skips the
  // morphology stages (close/heal/bay-fill/dilate/despeck/carve) but keeps
  // threshold + corridors + blockedRects, for judging the minimal pipeline.
  async run(record, sceneName, opts) {
    const C = this.CFG, { W, H, S, FW, FH } = C;
    const thresholdOnly = !!(opts && opts.thresholdOnly);
    const stages = [];
    const snap = (title, note, m, extra) => {
      if (record) stages.push({ title, note, m: m ? m.slice() : null, ...(extra || {}) });
    };

    const { name, cfg, scene, raw } = await this.loadScene(sceneName || 'square');
    const corridors = cfg.corridors || [];
    const pois = cfg.pois || [];
    const blockedRects = cfg.blockedRects || [];
    const center = cfg.center || [672, 620];

    snap('input · painted scene', 'whole-scene generation with composition constraints (exits, landmarks) + style ref', null, { img: scene });
    snap('input · green-flood', 'the generator repaints every walkable surface flat green; everything it left alone is an obstacle', null, { img: raw });

    // 1 · threshold at grid resolution (bakemask.py: green-dominance test)
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g0 = c.getContext('2d'); g0.drawImage(raw, 0, 0, W, H);
    const d = g0.getImageData(0, 0, W, H).data;
    let m = new Uint8Array(W * H);
    for (let i = 0; i < W * H; i++) {
      const r = d[i * 4], gg = d[i * 4 + 1], b = d[i * 4 + 2];
      m[i] = (gg > C.green.min && gg > r * C.green.ratio && gg > b * C.green.ratio) ? 1 : 0;
    }
    snap('1 · threshold', `green-dominance test per ${S}px cell (g>${C.green.min} && g>${C.green.ratio}×r,b) — raw and noisy`, m);

    if (!thresholdOnly) {
      // 2 · close: fill noise holes
      m = this.pass(m, true, C.closeR, W, H); m = this.pass(m, false, C.closeR, W, H);
      snap('2 · close (r=' + C.closeR + ')', 'dilate+erode walkable: fills speck holes the flood missed without moving real boundaries', m);

      // 3 · heal blocked specks (noise blobs, NOT real objects)
      for (const isl of this.components(m, W, H, 0))
        if (!isl.touches && isl.cells.length < C.speckMax) for (const c2 of isl.cells) m[c2] = 1;
      snap('3 · heal specks', 'tiny interior blocked blobs (<' + C.speckMax + ' cells) are flood noise, not objects — healed. Real objects stay FULLY blocked: no walk-behind, by design (simple beats surprising-but-fragile).', m);

      // 4 · bay filling
      m = this.pass(m, false, C.bayFillR, W, H);
      m = this.pass(m, true, C.bayFillR, W, H);
      snap('4 · bay-fill (r=' + C.bayFillR + ')', 'a close on BLOCKED space seals concave trap-bowls and squeeze-gaps narrower than ~' + (C.bayFillR * 2 * S) + 'px — roads are far wider and survive', m);
    }

    // 5 · authored road corridors (scene px) — unioned in; double as exit mouths
    for (const r of corridors) {
      for (let y = Math.floor(r.y / S); y < Math.ceil((r.y + r.h) / S); y++)
        for (let x = Math.floor(r.x / S); x < Math.ceil((r.x + r.w) / S); x++)
          if (x >= 0 && y >= 0 && x < W && y < H) m[y * W + x] = 1;
    }
    if (!thresholdOnly) {
      m = this.pass(m, true, C.dilateR, W, H);
      for (const b of this.components(m, W, H, 0))
        if (!b.touches && b.cells.length < C.speckMax) for (const c2 of b.cells) m[c2] = 1;
      snap('5 · corridors ∪ dilate ∪ despeck', 'authored road corridors force the exits open (the generator reliably under-floods roads); walkable dilates 1 cell; blocked specks <' + C.speckMax + ' cells vanish', m, { corridors });
    } else {
      snap('2 · corridors (threshold-only)', 'authored road corridors unioned onto the raw threshold — all morphology (close / heal / bay-fill / dilate / despeck / carve) skipped', m, { corridors });
    }

    // 6 · authored blocked rects (e.g. tall props that must not be walked
    // behind) — bakemask.py applies these AFTER dilate/despeck and BEFORE
    // the clearance carve, so a carved corridor may legally re-open them.
    if (blockedRects.length) {
      for (const r of blockedRects) {
        for (let y = Math.floor(r.y / S); y < Math.ceil((r.y + r.h) / S); y++)
          for (let x = Math.floor(r.x / S); x < Math.ceil((r.x + r.w) / S); x++)
            if (x >= 0 && y >= 0 && x < W && y < H) m[y * W + x] = 0;
      }
      snap((thresholdOnly ? '3' : '6') + ' · blocked rects', blockedRects.length + ' authored blocked rect(s) stamped back to BLOCKED (tall props / no-walk zones), before the carve so connectivity is re-checked around them', m, { blockedRects });
    }

    let carved = 0;
    const carvedPaths = [];
    if (!thresholdOnly) {
      // 7 · clearance-aware POI connectivity carving.
      // "Clear" cells have their whole 3×3 neighbourhood walkable (≥12px of
      // room) — the same standard the in-game navGate demands. Every POI must
      // reach the scene center through clear cells; failures get a 5-cell-wide
      // corridor carved, which is clear by construction.
      const CLR = 2;   // clearance radius in cells: route must be ≥ (2·CLR+1)·4 px wide
      const ccx = Math.floor(center[0] / S), ccy = Math.floor(center[1] / S);
      const clearMap = () => {
        const cl = new Uint8Array(W * H);
        for (let y = CLR; y < H - CLR; y++) for (let x = CLR; x < W - CLR; x++) {
          let ok = 1;
          for (let dy = -CLR; dy <= CLR && ok; dy++) for (let dx = -CLR; dx <= CLR; dx++)
            if (!m[(y + dy) * W + x + dx]) { ok = 0; break; }
          cl[y * W + x] = ok;
        }
        return cl;
      };
      const reachClear = () => {
        const cl = clearMap();
        const seen = new Uint8Array(W * H);
        const q2 = [];
        for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
          const i2 = (ccy + dy) * W + ccx + dx;
          if (i2 >= 0 && i2 < W * H && cl[i2] && !seen[i2]) { seen[i2] = 1; q2.push(i2); }
        }
        while (q2.length) {
          const q = q2.pop(), qx = q % W;
          for (const dd of [-1, 1, -W, W]) {
            const n = q + dd;
            if (n < 0 || n >= W * H || Math.abs((n % W) - qx) > 1) continue;
            if (cl[n] && !seen[n]) { seen[n] = 1; q2.push(n); }
          }
        }
        return seen;
      };
      for (const [px2, py2] of pois) {
        const seen = reachClear();
        const gx = Math.floor(px2 / S), gy = Math.floor(py2 / S);
        // POI is fine if a clear-reachable cell sits within 3 cells of it
        let ok = false;
        for (let dy = -3; dy <= 3 && !ok; dy++) for (let dx = -3; dx <= 3; dx++) {
          const nx = gx + dx, ny = gy + dy;
          if (nx >= 0 && ny >= 0 && nx < W && ny < H && seen[ny * W + nx]) { ok = true; break; }
        }
        if (ok) continue;
        const steps = Math.max(Math.abs(ccx - gx), Math.abs(ccy - gy), 1);
        for (let t = 0; t <= steps; t++) {
          const x = Math.round(gx + (ccx - gx) * t / steps);
          const y = Math.round(gy + (ccy - gy) * t / steps);
          for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) {
            const nx = x + dx, ny = y + dy;
            if (nx >= 0 && ny >= 0 && nx < W && ny < H) m[ny * W + nx] = 1;
          }
        }
        carved++; carvedPaths.push([px2, py2]);
      }
      snap((blockedRects.length ? '7' : '6') + ' · clearance carve (final mask)', 'every gameplay POI must reach the scene center (' + center[0] + ',' + center[1] + ') through cells with ≥12px of room (the navGate standard); failures get a 5-cell corridor carved. Carved this run: ' + carved, m, { pois, carvedPaths });
    } else {
      snap('final (threshold-only)', 'minimal pipeline result: threshold + corridors' + (blockedRects.length ? ' + blocked rects' : '') + ' — compare against the full pipeline to see what the morphology stages actually buy', m, { pois });
    }

    return { m, carved, scene, raw, stages, cfg, name };
  },
};
