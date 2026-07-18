'use strict';
/* ============================================================
   SPRITES2 — generated sprite sheets: slicing (soft chroma key,
   despill, feather), direction picks, per-tint grading cache.
   ============================================================ */

// picks: arrays of either [col,row] grid cells or {x,y,w,h} pixel rects
const SpriteDefs = {
  june: {
    src: 'assets/sprite-june-chibi.png', cell: 256,
    picks: { down: [[0, 0]], up: [[1, 0]], left: [[1, 2], [1, 3]] },
  },
  cole: {
    src: 'assets/sprite-cole.png', cell: 256,
    picks: { down: [[0, 0]], up: [[1, 0]], left: [[1, 2], [2, 2]] },
  },
  rowan: { src: 'assets/sprite-rowan.png', cell: 256,
    picks: { down: [[1, 0]], up: [[2, 1]], left: [[1, 2]] } },
  poppy: { src: 'assets/sprite-poppy.png', cell: 256,
    picks: { down: [[0, 0]], up: [[2, 0]], left: [[1, 2]] } },
  finn: { src: 'assets/sprite-finn.png',
    picks: { down: [{ x: 305, y: 245, w: 175, h: 265 }], up: [{ x: 305, y: 245, w: 175, h: 265 }], left: [{ x: 315, y: 515, w: 175, h: 255 }] } },
  pip: { src: 'assets/sprite-pip.png', cell: 256,
    picks: { down: [[0, 0]], up: [[3, 0]], left: [[0, 3]] } },
  mara: { src: 'assets/sprite-mara.png',
    picks: { down: [{ x: 170, y: 0, w: 205, h: 260 }], up: [{ x: 550, y: 0, w: 200, h: 260 }], left: [{ x: 285, y: 505, w: 200, h: 265 }] } },
  mochi: { src: 'assets/sprite-mochi.png', cell: 512,
    picks: { down: [[0, 0]], up: [[1, 0]], left: [[0, 1]] }, wide: true },
  stranger: { src: 'assets/sprite-stranger.png', cell: 512, cellH: 256,
    picks: { down: [[0, 0]], up: [[1, 0]], left: [[0, 2]] } },
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
    fr.right = fr.left.map(c => {
      const m = makeCanvas(c.width, c.height), g = m.getContext('2d');
      g.translate(c.width, 0); g.scale(-1, 1); g.drawImage(c, 0, 0);
      return m;
    });
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
    const fr = list[e.moving ? Math.floor(e.animT * 5.5) % list.length : 0];
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
