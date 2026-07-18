/* Shared square-scene bake pipeline — single source of truth.
   bake-square.html runs it and saves the outputs; workflow.html runs it
   with recording on and shows every intermediate stage for review. */
const BakeCore = {
  CFG: {
    W: 336, H: 192, S: 4, FW: 1344, FH: 768,
    sceneSrc: 'assets/sq-c2.png',
    rawSrc: 'assets/sq-c2-maskraw.png',
    // green-flood threshold: a pixel is walkable if green dominates
    green: { min: 90, ratio: 1.25 },
    closeR: 3,            // noise-fill close radius (cells)
    speckMax: 8,          // blocked specks below this size are removed (both phases)
    bayFillR: 4,          // close on BLOCKED space: seals trap-pockets < ~2r cells
    dilateR: 1,           // final walkable dilation (opens pinch points)
    // authored road corridors (scene px) — unioned in; double as exit mouths
    corridors: [
      { x: 630, y: 0, w: 190, h: 220, label: 'north road' },
      { x: 40, y: 590, w: 340, h: 178, label: 'south-west road' },
      { x: 0, y: 590, w: 150, h: 178, label: 'west lane' },
    ],
    // Gameplay positions that must be reachable from the plaza center with
    // CLEARANCE (a ≥3-cell-wide route, matching the in-game navGate);
    // unreachable ones get a 5-cell corridor carved toward center.
    // Keep this list aligned with the navGate GAMEPLAY list.
    pois: [
      [672, 620],               // heartlight / plaza center
      [790, 610],               // rowan approach
      [390, 605],               // poppy approach (beside the baker stall)
      [985, 700], [945, 705],   // mara + pip approaches
      [765, 350],               // lamp2 base
      [1094, 575],              // lamp3 base
      [240, 575],               // notice board
      [600, 600], [692, 605],   // pact spots
      [180, 730], [40, 650], [720, 60],   // exits S / W / N
      [900, 530], [445, 600],   // plaza flow spots
    ],
  },

  load(src) {
    return new Promise((res, rej) => {
      const i = new Image();
      i.onload = () => res(i);
      i.onerror = rej;
      i.src = src + '?t=' + Date.now();
    });
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

  async run(record) {
    const C = this.CFG, { W, H, S, FW, FH } = C;
    const stages = [];
    const snap = (title, note, m, extra) => {
      if (record) stages.push({ title, note, m: m ? m.slice() : null, ...(extra || {}) });
    };

    const scene = await this.load(C.sceneSrc);
    const raw = await this.load(C.rawSrc);
    snap('input · painted scene', 'whole-scene generation with composition constraints (exits, landmarks) + style ref', null, { img: scene });
    snap('input · green-flood', 'the generator repaints every walkable surface flat green; everything it left alone is an obstacle', null, { img: raw });

    // 1 · threshold at grid resolution
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const g0 = c.getContext('2d'); g0.drawImage(raw, 0, 0, W, H);
    const d = g0.getImageData(0, 0, W, H).data;
    let m = new Uint8Array(W * H);
    for (let i = 0; i < W * H; i++) {
      const r = d[i * 4], gg = d[i * 4 + 1], b = d[i * 4 + 2];
      m[i] = (gg > C.green.min && gg > r * C.green.ratio && gg > b * C.green.ratio) ? 1 : 0;
    }
    snap('1 · threshold', `green-dominance test per ${S}px cell (g>${C.green.min} && g>${C.green.ratio}×r,b) — raw and noisy`, m);

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

    // 5 · corridors + dilation + speck removal
    for (const r of C.corridors) {
      for (let y = Math.floor(r.y / S); y < Math.ceil((r.y + r.h) / S); y++)
        for (let x = Math.floor(r.x / S); x < Math.ceil((r.x + r.w) / S); x++)
          if (x >= 0 && y >= 0 && x < W && y < H) m[y * W + x] = 1;
    }
    m = this.pass(m, true, C.dilateR, W, H);
    for (const b of this.components(m, W, H, 0))
      if (!b.touches && b.cells.length < C.speckMax) for (const c2 of b.cells) m[c2] = 1;
    snap('5 · corridors ∪ dilate ∪ despeck', 'authored road corridors force the exits open (the generator reliably under-floods roads); walkable dilates 1 cell; blocked specks <' + C.speckMax + ' cells vanish', m, { corridors: C.corridors });

    // 6 · clearance-aware POI connectivity carving.
    // "Clear" cells have their whole 3×3 neighbourhood walkable (≥12px of
    // room) — the same standard the in-game navGate demands. Every POI must
    // reach the plaza center through clear cells; failures get a 5-cell-wide
    // corridor carved, which is clear by construction.
    const CLR = 2;   // clearance radius in cells: route must be ≥ (2·CLR+1)·4 px wide
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
      const cx = Math.floor(672 / S), cy = Math.floor(620 / S);
      const q2 = [];
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
        const i2 = (cy + dy) * W + cx + dx;
        if (cl[i2] && !seen[i2]) { seen[i2] = 1; q2.push(i2); }
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
    let carved = 0;
    const carvedPaths = [];
    for (const [px2, py2] of C.pois) {
      const seen = reachClear();
      const gx = Math.floor(px2 / S), gy = Math.floor(py2 / S);
      // POI is fine if a clear-reachable cell sits within 3 cells of it
      let ok = false;
      for (let dy = -3; dy <= 3 && !ok; dy++) for (let dx = -3; dx <= 3; dx++) {
        const nx = gx + dx, ny = gy + dy;
        if (nx >= 0 && ny >= 0 && nx < W && ny < H && seen[ny * W + nx]) { ok = true; break; }
      }
      if (ok) continue;
      const cx = Math.floor(672 / S), cy = Math.floor(620 / S);
      const steps = Math.max(Math.abs(cx - gx), Math.abs(cy - gy));
      for (let t = 0; t <= steps; t++) {
        const x = Math.round(gx + (cx - gx) * t / steps);
        const y = Math.round(gy + (cy - gy) * t / steps);
        for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) {
          const nx = x + dx, ny = y + dy;
          if (nx >= 0 && ny >= 0 && nx < W && ny < H) m[ny * W + nx] = 1;
        }
      }
      carved++; carvedPaths.push([px2, py2]);
    }
    snap('6 · clearance carve (final mask)', 'every gameplay POI must reach the plaza center through cells with ≥12px of room (the navGate standard); failures get a 5-cell corridor carved. Carved this run: ' + carved, m, { pois: C.pois, carvedPaths });

    return { m, carved, scene, raw, stages };
  },
};
