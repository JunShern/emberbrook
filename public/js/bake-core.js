/* Shared scene bake pipeline — browser mirror of tools/bakemask.py (the
   production baker; the two must stay in sync — same stages, same order,
   same params). Per-scene config comes from assets/scenes/<name>/bake.json.
   bake-square.html runs it for the square and saves the outputs;
   workflow.html runs it with recording on for ANY scene and shows every
   intermediate stage for review.

   Flood key is AUTO-DETECTED per maskraw (mirrors bakemask.py):
     legacy GREEN flood -> v1 pipeline: strict threshold, close r=3, dilate 1
     MAGENTA flood      -> v2 pipeline: loose threshold (magenta is absent
       from the art), close r=2, NO blanket dilate, gradient edge-snap
       against the painting's own drawn edges.

   bakemask.py stage order (mirrored exactly):
     threshold -> close -> heal specks -> bay-fill -> corridors+segments ->
     [v1: dilate] + despeck -> [v2: edge-snap] -> blockedRects ->
     clearance carve

   SLOP METRIC (also mirrored): walkable cells sitting on strong image
   edges (per-cell mean sobel >= p85), as % of the WHOLE grid. Grid-
   normalized on purpose: dividing by walkable-cell count instead punishes
   tight masks (a sloppy mask covering big FLAT surfaces — water, lock
   walls — dilutes its own edge fraction).                              */
const BakeCore = {
  CFG: {
    W: 336, H: 192, S: 4, FW: 1344, FH: 768,
    green:   { min: 90, ratio: 1.25 },       // v1 strict key (scene greens exist)
    magenta: { rgDiff: 50, bgDiff: 40 },     // v2 loose key (magenta absent from art)
    speckMax: 8,          // blocked specks below this size are removed (both phases)
    bayFillR: 4,          // close on BLOCKED space: seals trap-pockets < ~2r cells
    v1: { closeR: 3, dilateR: 1, snap: false },
    v2: { closeR: 2, dilateR: 0, snap: true },
    snapScan: 3,          // edge-snap: look up to 3 cells out for a drawn edge
    slopPct: 85,          // strong-edge threshold = p85 of per-cell mean sobel
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

  // Per-scene config + images. bake.json: { center, corridors, segments, pois, blockedRects? }
  async loadScene(name) {
    const base = 'assets/scenes/' + name + '/';
    const resp = await fetch(base + 'bake.json?t=' + Date.now());
    if (!resp.ok) throw new Error(name + '/bake.json: HTTP ' + resp.status);
    const cfg = await resp.json();
    const scene = await this.loadFirst([base + 'festival.png', base + 'main.png', base + 'gray.png']);
    const raw = await this.load(base + 'maskraw.png');
    const shipped = await this.load(base + 'mask.png').catch(() => null);
    return { name, cfg, scene, raw, shipped };
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

  // ---------- flood key (mirrors bakemask.py is_green / is_magenta / detect_key) ----------

  isGreen(r, g, b) {
    const G = this.CFG.green;
    return g > G.min && g > r * G.ratio && g > b * G.ratio;
  },

  isMagenta(r, g, b) {
    const M = this.CFG.magenta;
    return r - g > M.rgDiff && b - g > M.bgDiff;
  },

  // magenta wins if it hits more cells than green does (magenta never
  // appears in the art, green does — moss/hull-paint/water)
  detectKey(d, n) {
    let gn = 0, mg = 0;
    for (let i = 0; i < n; i++) {
      const r = d[i * 4], g = d[i * 4 + 1], b = d[i * 4 + 2];
      if (this.isGreen(r, g, b)) gn++;
      if (this.isMagenta(r, g, b)) mg++;
    }
    return mg > gn ? 'magenta' : 'green';
  },

  // ---------- painting edges (sobel), for edge-snap + slop metric ----------

  // Per-grid-cell MEAN of L1 sobel magnitude over the full-res painting,
  // plus the strong-edge threshold (p'slopPct' of all cells).
  edgeCells(sceneImg) {
    const { W, H, FW, FH, slopPct } = this.CFG;
    const c = document.createElement('canvas'); c.width = FW; c.height = FH;
    const g2 = c.getContext('2d'); g2.drawImage(sceneImg, 0, 0, FW, FH);
    const d = g2.getImageData(0, 0, FW, FH).data;
    const lum = new Uint8Array(FW * FH);
    for (let i = 0; i < FW * FH; i++)
      lum[i] = (d[i * 4] * 77 + d[i * 4 + 1] * 151 + d[i * 4 + 2] * 28) >> 8;
    const csum = new Int32Array(W * H);
    for (let y = 1; y < FH - 1; y++) {
      const r0 = (y - 1) * FW, r1 = y * FW, r2 = (y + 1) * FW;
      const crow = (y >> 2) * W;
      for (let x = 1; x < FW - 1; x++) {
        const a = lum[r0 + x - 1], b = lum[r0 + x], cc = lum[r0 + x + 1];
        const dd = lum[r1 + x - 1], f = lum[r1 + x + 1];
        const gg = lum[r2 + x - 1], h = lum[r2 + x], i2 = lum[r2 + x + 1];
        const gx = (cc + 2 * f + i2) - (a + 2 * dd + gg);
        const gy = (gg + 2 * h + i2) - (a + 2 * b + cc);
        csum[crow + (x >> 2)] += Math.abs(gx) + Math.abs(gy);
      }
    }
    const E = new Int32Array(W * H);
    for (let i = 0; i < W * H; i++) E[i] = (csum[i] / 16) | 0;
    const srt = Array.from(E).sort((a, b) => a - b);
    const T = srt[Math.min(srt.length - 1, Math.floor(srt.length * slopPct / 100))];
    return { E, T };
  },

  // walkable cells on strong edges, as % of the WHOLE grid (see header)
  slop(m, E, T) {
    const { W, H } = this.CFG;
    let hits = 0;
    for (let i = 0; i < W * H; i++) if (m[i] && E[i] >= T) hits++;
    return hits * 100 / (W * H);
  },

  // Expansion-only boundary snap: where the mask stops short of the drawn
  // boundary, walk outward up to snapScan cells; if a strong-edge cell is
  // found, fill the low-gradient cells between (never the edge cell itself).
  // Cannot disconnect anything (only adds cells).
  edgeSnap(m, E, T) {
    const { W, H, snapScan: R } = this.CFG;
    const add = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x;
      if (!m[i]) continue;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H || m[ny * W + nx]) continue;
        let fill = [], hitEdge = false;
        for (let k = 1; k <= R; k++) {
          const px2 = x + dx * k, py2 = y + dy * k;
          if (px2 < 0 || py2 < 0 || px2 >= W || py2 >= H) { fill = []; break; }
          const j = py2 * W + px2;
          if (m[j]) { fill = []; break; }
          if (E[j] >= T) { hitEdge = true; break; }   // drawn edge: fill up to it
          fill.push(j);
        }
        if (!hitEdge) fill = [];                       // no edge within reach: no fill
        for (const j of fill) add.push(j);
      }
    }
    let n = 0;
    for (const j of add) if (!m[j]) { m[j] = 1; n++; }
    return n;
  },

  // ---------- authored geometry ----------

  stampRect(m, r, val) {
    const { W, H, S } = this.CFG;
    for (let y = Math.floor(r.y / S); y < Math.ceil((r.y + r.h) / S); y++)
      for (let x = Math.floor(r.x / S); x < Math.ceil((r.x + r.w) / S); x++)
        if (x >= 0 && y >= 0 && x < W && y < H) m[y * W + x] = val;
  },

  // Polyline corridor: cells whose center lies within w/2 of the path.
  stampSegment(m, seg) {
    const { W, H, S } = this.CFG;
    const hw = seg.w / 2;
    const pts = seg.pts;
    for (let p = 0; p + 1 < pts.length; p++) {
      const [x1, y1] = pts[p], [x2, y2] = pts[p + 1];
      const x0 = Math.floor((Math.min(x1, x2) - hw) / S), x3 = Math.floor((Math.max(x1, x2) + hw) / S) + 1;
      const y0 = Math.floor((Math.min(y1, y2) - hw) / S), y3 = Math.floor((Math.max(y1, y2) + hw) / S) + 1;
      const vx = x2 - x1, vy = y2 - y1;
      const L2 = vx * vx + vy * vy;
      for (let gy = Math.max(0, y0); gy < Math.min(H, y3); gy++) {
        const cy = gy * S + S / 2;
        for (let gx = Math.max(0, x0); gx < Math.min(W, x3); gx++) {
          const cx = gx * S + S / 2;
          const t = L2 === 0 ? 0 : Math.max(0, Math.min(1, ((cx - x1) * vx + (cy - y1) * vy) / L2));
          const dx = cx - (x1 + vx * t), dy = cy - (y1 + vy * t);
          if (dx * dx + dy * dy <= hw * hw) m[gy * W + gx] = 1;
        }
      }
    }
  },

  // run(record[, sceneName[, opts]]) — sceneName defaults to 'square' so old
  // callers (bake-square.html) keep working. opts.thresholdOnly skips the
  // morphology stages (close/heal/bay-fill/dilate/despeck/snap/carve) but keeps
  // threshold + corridors/segments + blockedRects, for judging the minimal pipeline.
  async run(record, sceneName, opts) {
    const C = this.CFG, { W, H, S } = C;
    const thresholdOnly = !!(opts && opts.thresholdOnly);
    const stages = [];
    const snap = (title, note, m, extra) => {
      if (record) stages.push({ title, note, m: m ? m.slice() : null, ...(extra || {}) });
    };

    const { name, cfg, scene, raw, shipped } = await this.loadScene(sceneName || 'square');
    const corridors = cfg.corridors || [];
    const segments = cfg.segments || [];
    const pois = cfg.pois || [];
    const blockedRects = cfg.blockedRects || [];
    const center = cfg.center || [672, 620];

    snap('input · painted scene', 'whole-scene generation with composition constraints (exits, landmarks) + style ref', null, { img: scene });

    // 0 · flood-key autodetect on the grid-resolution raw
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g0 = c.getContext('2d'); g0.drawImage(raw, 0, 0, W, H);
    const d = g0.getImageData(0, 0, W, H).data;
    const key = this.detectKey(d, W * H);
    const V = key === 'magenta' ? C.v2 : C.v1;
    snap('input · ' + key + '-flood', key === 'magenta'
      ? 'v2: the generator repaints every walkable surface flat MAGENTA — absent from the art, so the threshold can be loose (r-g>' + C.magenta.rgDiff + ' && b-g>' + C.magenta.bgDiff + ')'
      : 'v1 (legacy): flat GREEN flood — greens exist in the art, so the threshold must stay strict', null, { img: raw });

    // painting edges: shared by edge-snap and the slop metric
    const { E, T } = this.edgeCells(scene);

    // slop of the SHIPPED python-baked mask.png (the "before" number)
    let slopBefore = null;
    if (shipped) {
      const cs = document.createElement('canvas'); cs.width = W; cs.height = H;
      const gs = cs.getContext('2d'); gs.drawImage(shipped, 0, 0, W, H);
      const ds = gs.getImageData(0, 0, W, H).data;
      const sm = new Uint8Array(W * H);
      for (let i = 0; i < W * H; i++) sm[i] = ds[i * 4] > 127 ? 1 : 0;
      slopBefore = this.slop(sm, E, T);
    }

    // 1 · threshold at grid resolution (bakemask.py: key-dominance test)
    let m = new Uint8Array(W * H);
    for (let i = 0; i < W * H; i++) {
      const r = d[i * 4], gg = d[i * 4 + 1], b = d[i * 4 + 2];
      m[i] = (key === 'magenta' ? this.isMagenta(r, gg, b) : this.isGreen(r, gg, b)) ? 1 : 0;
    }
    snap('1 · threshold', key + '-dominance test per ' + S + 'px cell — raw and noisy', m);

    if (!thresholdOnly) {
      // 2 · close: fill noise holes (v1 r=3, v2 r=2)
      m = this.pass(m, true, V.closeR, W, H); m = this.pass(m, false, V.closeR, W, H);
      snap('2 · close (r=' + V.closeR + ')', 'dilate+erode walkable: fills speck holes the flood missed without moving real boundaries', m);

      // 3 · heal blocked specks (noise blobs, NOT real objects)
      for (const isl of this.components(m, W, H, 0))
        if (!isl.touches && isl.cells.length < C.speckMax) for (const c2 of isl.cells) m[c2] = 1;
      snap('3 · heal specks', 'tiny interior blocked blobs (<' + C.speckMax + ' cells) are flood noise, not objects — healed. Real objects stay FULLY blocked: no walk-behind, by design (simple beats surprising-but-fragile).', m);

      // 4 · bay filling
      m = this.pass(m, false, C.bayFillR, W, H);
      m = this.pass(m, true, C.bayFillR, W, H);
      snap('4 · bay-fill (r=' + C.bayFillR + ')', 'a close on BLOCKED space seals concave trap-bowls and squeeze-gaps narrower than ~' + (C.bayFillR * 2 * S) + 'px — roads are far wider and survive', m);
    }

    // 5 · authored corridors: legacy rects + polyline segments (scene px) —
    // unioned in; double as exit mouths
    for (const r of corridors) this.stampRect(m, r, 1);
    for (const s of segments) this.stampSegment(m, s);
    let snapped = 0;
    if (!thresholdOnly) {
      // v1: blanket dilate 1; v2: none (boundary fidelity)
      if (V.dilateR) m = this.pass(m, true, V.dilateR, W, H);
      for (const b of this.components(m, W, H, 0))
        if (!b.touches && b.cells.length < C.speckMax) for (const c2 of b.cells) m[c2] = 1;
      snap('5 · corridors/segments' + (V.dilateR ? ' ∪ dilate' : '') + ' ∪ despeck',
        corridors.length + ' authored rect(s) + ' + segments.length + ' polyline segment(s) force the connectors open' +
        (V.dilateR ? '; walkable dilates 1 cell' : '; NO blanket dilate (v2 keeps the boundary where the flood put it)') +
        '; blocked specks <' + C.speckMax + ' cells vanish', m, { corridors, segments });
      // v2 · edge-snap the boundary out to the painting's own drawn edges
      if (V.snap) {
        snapped = this.edgeSnap(m, E, T);
        snap('5b · edge-snap', 'expansion-only: boundary cells scan up to ' + C.snapScan + ' cells outward; if a strong drawn edge (sobel ≥ p' + C.slopPct + ') is found, the low-gradient gap up to it is filled — recovers plank strips the loose threshold missed. Added ' + snapped + ' cells.', m);
      }
    } else {
      snap('2 · corridors/segments (threshold-only)', 'authored corridors/segments unioned onto the raw threshold — all morphology (close / heal / bay-fill / dilate / despeck / snap / carve) skipped', m, { corridors, segments });
    }

    // 6 · authored blocked rects (e.g. tall props that must not be walked
    // behind) — bakemask.py applies these AFTER dilate/despeck/snap and BEFORE
    // the clearance carve, so a carved corridor may legally re-open them.
    if (blockedRects.length) {
      for (const r of blockedRects) this.stampRect(m, r, 0);
      snap((thresholdOnly ? '3' : '6') + ' · blocked rects', blockedRects.length + ' authored blocked rect(s) stamped back to BLOCKED (tall props / no-walk zones), before the carve so connectivity is re-checked around them', m, { blockedRects });
    }

    let carved = 0;
    const carvedPaths = [];
    if (!thresholdOnly) {
      // 7 · clearance-aware POI connectivity carving.
      // "Clear" cells have their whole (2·CLR+1)² neighbourhood walkable —
      // the same standard the in-game navGate demands. Every POI must
      // reach the scene center through clear cells; failures get a 7-cell-wide
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
      snap((blockedRects.length ? '7' : '6') + ' · clearance carve (final mask)', 'every gameplay POI must reach the scene center (' + center[0] + ',' + center[1] + ') through cells with ≥12px of room (the navGate standard); failures get a corridor carved. Carved this run: ' + carved, m, { pois, carvedPaths });
    } else {
      snap('final (threshold-only)', 'minimal pipeline result: threshold + corridors/segments' + (blockedRects.length ? ' + blocked rects' : '') + ' — compare against the full pipeline to see what the morphology stages actually buy', m, { pois });
    }

    const slopAfter = this.slop(m, E, T);
    let coverage = 0;
    for (let i = 0; i < W * H; i++) coverage += m[i];
    coverage = coverage * 100 / (W * H);

    return { m, carved, scene, raw, stages, cfg, name,
             key, mode: thresholdOnly ? 'threshold-only' : (key === 'magenta' ? 'v2-magenta' : 'v1-green'),
             snapped, coverage, edgeT: T, slopBefore, slopAfter };
  },
};
