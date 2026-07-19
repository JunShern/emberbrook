'use strict';
/* ============================================================
   SPRITES2 — generated sprite sheets: slicing (soft chroma key,
   despill, feather), direction picks, per-tint grading cache.
   ============================================================ */

// picks: arrays of either [col,row] grid cells or {x,y,w,h} pixel rects
const SpriteDefs = {
  june: {
    // HD-2D pixel set: rows = down / up / right (right cells mirrored for left)
    src: 'assets/characters/june/sheet.png', cell: 256,
    picks: {
      down: [[0, 0], [1, 0], [2, 0], [3, 0]],
      up: [[0, 1], [1, 1], [2, 1], [3, 1]],
      left: [[0, 2], [1, 2], [2, 2], [3, 2], [4, 2], [5, 2]],
    },
    sideFacesRight: true,
  },
  cole: {
    // HD-2D pixel set matching June's layout: rows = down / up / right-facing side
    src: 'assets/characters/cole/sheet.png', cell: 256,
    picks: {
      down: [[0, 0], [1, 0], [2, 0], [3, 0]],
      up: [[0, 1], [1, 1], [2, 1], [3, 1]],
      left: [[0, 2], [1, 2], [2, 2], [3, 2], [4, 2], [5, 2]],
    },
    sideFacesRight: true,
  },
  rowan: { src: 'assets/characters/rowan/sheet.png', cell: 256,
    picks: { down: [[0, 0]], up: [[0, 1]], left: [[0, 2]] }, sideFacesRight: true },
  poppy: { src: 'assets/characters/poppy/sheet.png', cell: 256,
    picks: { down: [[0, 0]], up: [[0, 1]], left: [[0, 2]] }, sideFacesRight: true },
  finn: { src: 'assets/characters/finn/sheet.png', cell: 256,
    picks: { down: [[0, 0]], up: [[0, 1]], left: [[0, 2]] }, sideFacesRight: true },
  pip: { src: 'assets/characters/pip/sheet.png', cell: 256,
    picks: { down: [[0, 0]], up: [[0, 1]], left: [[0, 2]] }, sideFacesRight: true },
  mara: { src: 'assets/characters/mara/sheet.png', cell: 256,
    picks: { down: [[0, 0]], up: [[0, 1]], left: [[0, 2]] }, sideFacesRight: true },
  mochi: { src: 'assets/characters/mochi/sheet.png', cell: 256,
    picks: { down: [[0, 0]], up: [[0, 1]], left: [[0, 2], [1, 2], [2, 2], [3, 2]] }, wide: true, sideFacesRight: true },
  stranger: { src: 'assets/characters/stranger/sheet.png', cell: 256,
    picks: { down: [[0, 0]], up: [[0, 1]], left: [[0, 2]] }, sideFacesRight: true },
};

const Sprites = {
  frames: {},        // char -> dir -> [canvas]
  graded: {},        // `${char}|${tint}` -> dir -> [canvas]
  loaded: {},

  init() {
    for (const [name, def] of Object.entries(SpriteDefs)) {
      const img = new Image();
      img.src = def.src;
      img.onload = () => { this.slice(name, def, img); };
      img.onerror = () => { console.warn('sprite sheet missing:', def.src); };
    }
  },

  slice(name, def, img) {
    const outW = def.wide ? 230 : 160, outH = 230;
    const key = (pick) => {
      let sx, sy, CW, CH;
      if (Array.isArray(pick)) {
        CW = def.cell; CH = def.cellH || def.cell;
        sx = pick[0] * CW; sy = pick[1] * CH;
      } else {
        sx = pick.x; sy = pick.y; CW = pick.w; CH = pick.h;
      }
      const CELL = Math.max(CW, CH);
      const c = makeCanvas(CW, CH), g = c.getContext('2d');
      g.drawImage(img, sx, sy, CW, CH, 0, 0, CW, CH);
      const d = g.getImageData(0, 0, CW, CH), px = d.data;
      let minX = CW, minY = CH, maxX = 0, maxY = 0;
      for (let i = 0; i < px.length; i += 4) {
        const r = px[i], gg = px[i + 1], b = px[i + 2];
        const rg = r - gg, bg = b - gg;
        if (rg > 90 && bg > 60) { px[i + 3] = 0; continue; }
        if (rg > 50 && bg > 32) {
          const t = Math.min(1, ((rg + bg) - 82) / 60);
          px[i + 3] = Math.round(255 * (1 - t * 0.85));
          px[i] = Math.round(gg + rg * 0.35);
          px[i + 2] = Math.round(gg + bg * 0.35);
        }
        if (px[i + 3] < 16) continue;   // transparent-bg sheets: only visible pixels shape the bbox
        const x = (i / 4) % CW, y = Math.floor(i / 4 / CW);
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
      }
      const a0 = new Uint8ClampedArray(px.length / 4);
      for (let i = 0; i < a0.length; i++) a0[i] = px[i * 4 + 3];
      for (let y = 1; y < CH - 1; y++) for (let x = 1; x < CW - 1; x++) {
        const i = y * CW + x;
        const avg = (a0[i] * 4 + a0[i - 1] + a0[i + 1] + a0[i - CW] + a0[i + CW]) / 8;
        if (Math.abs(avg - a0[i]) > 8) px[i * 4 + 3] = avg;
      }
      g.putImageData(d, 0, 0);
      if (maxX <= minX) return makeCanvas(outW, outH);   // empty cell guard
      const w = maxX - minX + 1, h = maxY - minY + 1;
      const out = makeCanvas(outW, outH);
      const s = Math.min(outW / w, outH / h, 1.2);
      out.getContext('2d').drawImage(c, minX, minY, w, h,
        (outW - w * s) / 2, outH - h * s, w * s, h * s);
      return out;
    };
    const fr = {};
    for (const [dir, cells] of Object.entries(def.picks)) fr[dir] = cells.map(pick => key(pick));
    const flip = (c) => {
      const m = makeCanvas(c.width, c.height), g = m.getContext('2d');
      g.translate(c.width, 0); g.scale(-1, 1); g.drawImage(c, 0, 0);
      return m;
    };
    const side = fr.left;
    if (def.sideFacesRight) { fr.right = side; fr.left = side.map(flip); }
    else fr.right = side.map(flip);
    this.frames[name] = fr;
    this.loaded[name] = true;
  },

  tintSet(name, tint) {
    const k = name + '|' + tint;
    if (this.graded[k]) return this.graded[k];
    if (!this.frames[name]) return null;
    const set = {};
    for (const [dir, list] of Object.entries(this.frames[name])) {
      set[dir] = list.map(src => {
        const c = makeCanvas(src.width, src.height), g = c.getContext('2d');
        g.drawImage(src, 0, 0);
        g.globalCompositeOperation = 'multiply';
        g.fillStyle = tint; g.fillRect(0, 0, c.width, c.height);
        g.globalCompositeOperation = 'destination-in';
        g.drawImage(src, 0, 0);
        return c;
      });
    }
    this.graded[k] = set;
    return set;
  },

  // draw an entity: {char, x, y, dir, moving, animT, h(px), alpha, hidden}
  draw(g, e, tint) {
    if (e.hidden) return;
    const set = (tint && this.tintSet(e.char, tint)) || this.frames[e.char];
    if (!set) return;
    const list = set[e.dir] && set[e.dir].length ? set[e.dir] : set.down;
    if (!list || !list.length) return;
    const rate = list.length >= 6 ? 9 : 5.5;
    const fr = list[e.moving ? Math.floor(e.animT * rate) % list.length : 0];
    const h = e.h, w = h * (fr.width / fr.height);
    const stepT = e.animT * 11;
    const bob = e.moving ? Math.abs(Math.sin(stepT)) * h * 0.022 : 0;
    const sway = e.moving && (e.dir === 'down' || e.dir === 'up') ? Math.sin(stepT) * 0.05 : 0;
    g.save();
    if (e.alpha != null) g.globalAlpha = e.alpha;
    g.fillStyle = 'rgba(0,0,0,.3)';
    g.beginPath(); g.ellipse(e.x, e.y + 3, w * 0.3, h * 0.06, 0, 0, 7); g.fill();
    g.translate(e.x, e.y);
    g.rotate(sway);
    g.drawImage(fr, -w / 2, -h - bob, w, h);
    // Cole's ever-lit lighter
    if (e.lightCarrier) {
      const t = performance.now() / 1000;
      const gr = g.createRadialGradient(w * 0.22, -h * 0.42, 1, w * 0.22, -h * 0.42, h * 0.3);
      gr.addColorStop(0, 'rgba(255,200,120,.55)');
      gr.addColorStop(1, 'rgba(255,200,120,0)');
      g.fillStyle = gr;
      g.fillRect(w * 0.22 - h * 0.3, -h * 0.42 - h * 0.3, h * 0.6, h * 0.6);
      g.fillStyle = '#ffe0a0';
      g.fillRect(w * 0.2, -h * 0.44 + Math.sin(t * 10) * 1, 3, 5);
    }
    g.restore();
  },
};
Sprites.init();
