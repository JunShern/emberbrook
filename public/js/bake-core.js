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
    islandMinCells: 8,    // smaller interior blobs are specks, healed outright
    footBand: 0.22,       // bottom fraction of an island that stays blocked
    footInset: 0.08,      // sideways inset of the footprint rect
    borderShaveR: 1,      // walkable growth into the border region
    bayFillR: 4,          // close on BLOCKED space: seals trap-pockets < ~2r cells
    dilateR: 1,           // final walkable dilation (opens pinch points)
    speckMax: 8,          // blocked specks below this size are removed
    // authored road corridors (scene px) — unioned in; double as exit mouths
    corridors: [
      { x: 630, y: 0, w: 190, h: 220, label: 'north road' },
      { x: 40, y: 590, w: 340, h: 178, label: 'south-west road' },
      { x: 0, y: 590, w: 150, h: 178, label: 'west lane' },
    ],
    // POIs that must be reachable from the plaza center; unreachable ones
    // get a straight corridor carved toward center
    pois: [
      [672, 620], [350, 580], [740, 580], [940, 650], [672, 480],
      [765, 350], [1094, 575], [240, 575], [720, 60], [180, 730], [40, 650],
      [445, 600], [900, 530], [612, 655], [700, 655],
    ],
    cutMinArea: 1200,     // px² — smaller silhouettes get no occluder
    cutPad: 4,
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

    // 3 · island healing → rect footprints
    const islands = this.components(m, W, H, 0);
    const anchors = [], propIslands = [];
    for (const isl of islands) {
      if (isl.touches) continue;
      for (const c2 of isl.cells) m[c2] = 1;
      if (isl.cells.length < C.islandMinCells) continue;
      propIslands.push(isl);
      const cut = isl.maxY - Math.max(2, Math.round((isl.maxY - isl.minY) * C.footBand));
      const inset = Math.max(1, Math.round((isl.maxX - isl.minX) * C.footInset));
      for (let y = cut; y <= isl.maxY; y++)
        for (let x = isl.minX + inset; x <= isl.maxX - inset; x++)
          m[y * W + x] = 0;
      anchors.push({ x: Math.round((isl.minX + isl.maxX) / 2 * S), y: Math.round(isl.maxY * S), hPx: Math.round((isl.maxY - isl.minY) * S) });
    }
    snap('3 · island healing → rect footprints', 'interior blobs = free-standing props: walkable behind, blocked only in a clean inset bottom-band rectangle (slides perfectly). Simple, generous collision beats pixel-faithful collision.', m, { anchors: anchors.slice() });

    // 4 · border shave + bay filling
    m = this.pass(m, true, C.borderShaveR, W, H);
    m = this.pass(m, false, C.bayFillR, W, H);
    m = this.pass(m, true, C.bayFillR, W, H);
    snap('4 · border shave + bay-fill (r=' + C.bayFillR + ')', 'walkable grows 1 cell into the organic border; then a close on BLOCKED space seals concave trap-bowls narrower than ~' + (C.bayFillR * 2 * S) + 'px — roads are wider and survive', m);

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

    // 6 · POI connectivity carving
    const reach = () => {
      const seen = new Uint8Array(W * H);
      const start = Math.floor(620 / S) * W + Math.floor(672 / S);
      if (!m[start]) m[start] = 1;
      const q2 = [start]; seen[start] = 1;
      while (q2.length) {
        const q = q2.pop(), qx = q % W;
        for (const dd of [-1, 1, -W, W]) {
          const n = q + dd;
          if (n < 0 || n >= W * H || Math.abs((n % W) - qx) > 1) continue;
          if (m[n] === 1 && !seen[n]) { seen[n] = 1; q2.push(n); }
        }
      }
      return seen;
    };
    let carved = 0;
    const carvedPaths = [];
    for (const [px2, py2] of C.pois) {
      const seen = reach();
      const gx = Math.floor(px2 / S), gy = Math.floor(py2 / S);
      if (seen[gy * W + gx]) continue;
      const cx = Math.floor(672 / S), cy = Math.floor(620 / S);
      const steps = Math.max(Math.abs(cx - gx), Math.abs(cy - gy));
      for (let t = 0; t <= steps; t++) {
        const x = Math.round(gx + (cx - gx) * t / steps);
        const y = Math.round(gy + (cy - gy) * t / steps);
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const nx = x + dx, ny = y + dy;
          if (nx >= 0 && ny >= 0 && nx < W && ny < H) m[ny * W + nx] = 1;
        }
      }
      carved++; carvedPaths.push([px2, py2]);
    }
    snap('6 · connectivity carve (final mask)', 'flood-fill from plaza center; any unreachable POI gets a 3-cell corridor carved toward it. Carved this run: ' + carved, m, { pois: C.pois, carvedPaths });

    // 7 · self-cutout occluders from the scene itself
    const fc = document.createElement('canvas'); fc.width = FW; fc.height = FH;
    const fg = fc.getContext('2d'); fg.drawImage(raw, 0, 0, FW, FH);
    const fd = fg.getImageData(0, 0, FW, FH).data;
    const bF = new Uint8Array(FW * FH);
    for (let i = 0; i < FW * FH; i++) {
      const r = fd[i * 4], gg = fd[i * 4 + 1], b = fd[i * 4 + 2];
      bF[i] = (gg > C.green.min && gg > r * C.green.ratio && gg > b * C.green.ratio) ? 0 : 1;
    }
    const cutRects = [];
    const alphaC = document.createElement('canvas'); alphaC.width = FW; alphaC.height = FH;
    const ag = alphaC.getContext('2d');
    const aid = ag.createImageData(FW, FH);
    for (const isl of propIslands) {
      let gmask = new Uint8Array(W * H);
      for (const c2 of isl.cells) gmask[c2] = 1;
      gmask = this.pass(gmask, true, 1, W, H);
      let minX = FW, maxX = 0, minY = FH, maxY = 0, area = 0;
      for (let y = 0; y < FH; y++) for (let x = 0; x < FW; x++) {
        const i2 = y * FW + x;
        if (!bF[i2] || !gmask[((y / S) | 0) * W + ((x / S) | 0)]) continue;
        aid.data[i2 * 4] = 255; aid.data[i2 * 4 + 1] = 255; aid.data[i2 * 4 + 2] = 255; aid.data[i2 * 4 + 3] = 255;
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
        area++;
      }
      if (area < C.cutMinArea) continue;
      cutRects.push({
        x: Math.max(0, minX - C.cutPad), y: Math.max(0, minY - C.cutPad),
        w: Math.min(FW, maxX + C.cutPad) - Math.max(0, minX - C.cutPad),
        h: Math.min(FH, maxY + C.cutPad) - Math.max(0, minY - C.cutPad),
        baseY: maxY,
      });
    }
    ag.putImageData(aid, 0, 0);
    const alphaOut = document.createElement('canvas'); alphaOut.width = FW; alphaOut.height = FH;
    const aog = alphaOut.getContext('2d');
    aog.filter = 'blur(1.1px)'; aog.drawImage(alphaC, 0, 0);
    snap('7 · self-cutout occluders', 'full-res non-green pixels restricted to each prop island = its silhouette. The game crops the CURRENT backdrop through this alpha — pixel-identical, never doubles, y-sorted with characters. Border-attached objects need no cutout: nothing can walk behind them.', null, { alpha: alphaOut, cutRects, scene });

    return { m, anchors, cutRects, carved, alphaOut, scene, raw, stages };
  },
};
