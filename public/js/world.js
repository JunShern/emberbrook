'use strict';
/* ============================================================
   WORLD — tiles, autotiling, props, houses, lighting,
   character rendering. Content (the map itself) is built by
   the active chapter file.
   ============================================================ */

const T = 16;
const GRASS = 0, PATH = 1, PLAZA = 2, WATER = 3, SAND = 4, DOCK = 5;

function hash2(x, y) { return (((x * 73856093) ^ (y * 19349663)) >>> 0); }

const World = {
  W: 0, H: 0, tiles: [], coll: [],
  // hand-painted backdrop experiment: replaces terrain/houses/trees when on (P toggles)
  painted: true,
  backdropImg: (() => { const i = new Image(); i.src = 'assets/painted-map2.png'; return i; })(),
  BAKED_PROPS: new Set(['fence', 'crate', 'barrel', 'sign', 'noticeboard', 'waystone', 'stall']),
  usingBackdrop() { return this.painted && this.backdropImg.complete && this.backdropImg.naturalWidth > 0; },
  houses: [], trees: [], props: [], buntings: [], flowers: [],
  heartlight: null, gate: null, gateCells: [], plates: [],
  light: { dark: 0, targetDark: 0, color: '#0e1230', warm: true },
  tempLights: [],

  init(w, h) {
    this.W = w; this.H = h;
    this.tiles = []; this.coll = [];
    for (let y = 0; y < h; y++) {
      this.tiles.push(new Array(w).fill(GRASS));
      this.coll.push(new Array(w).fill(0));
    }
    this.houses = []; this.trees = []; this.props = [];
    this.buntings = []; this.flowers = []; this.tempLights = [];
  },

  fillT(x0, y0, x1, y1, t) {
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++)
      if (x >= 0 && y >= 0 && x < this.W && y < this.H) this.tiles[y][x] = t;
  },
  ellipse(cx, cy, rx, ry, t, solid) {
    for (let y = 0; y < this.H; y++) for (let x = 0; x < this.W; x++) {
      const dx = (x + 0.5 - cx) / rx, dy = (y + 0.5 - cy) / ry;
      if (dx * dx + dy * dy < 1) { this.tiles[y][x] = t; if (solid) this.coll[y][x] = 1; }
    }
  },
  solidRect(x0, y0, x1, y1, v = 1) {
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++)
      if (x >= 0 && y >= 0 && x < this.W && y < this.H) this.coll[y][x] = v;
  },

  setLight(mode) {
    if (mode === 'night') { this.light.targetDark = 0.72; this.light.color = '#0d1130'; this.light.warm = true; }
    else if (mode === 'gray') { this.light.targetDark = 0.34; this.light.color = '#232733'; this.light.warm = false; }
    else this.light.targetDark = 0;
  },

  addHouse(h) { this.houses.push(h); this.solidRect(h.tx, h.ty, h.tx + h.tw - 1, h.ty + h.th - 1); },
  addTree(tx, ty, big) {
    if (!this.tiles[ty] || this.tiles[ty][tx] !== GRASS || this.coll[ty][tx]) return;
    this.coll[ty][tx] = 1;
    this.trees.push({ x: tx * T + 8, y: ty * T + 14, big: !!big });
  },
  addLamp(tx, ty, lit) {
    this.coll[ty][tx] = 1;
    const p = { type: 'lamp', x: tx * T + 8, y: ty * T + 14, lit: !!lit };
    this.props.push(p);
    return p;
  },
  addProp(type, tx, ty, opts) {
    const p = Object.assign({ type, x: tx * T + 8, y: (ty + 1) * T - 2 }, opts || {});
    this.props.push(p);
    if (p.solid !== false) this.solidRect(tx, ty, tx + (p.tw || 1) - 1, ty);
    return p;
  },
  addBunting(x1, y1, x2, y2, lit) {
    const b = { x1, y1, x2, y2, lit: !!lit };
    this.buntings.push(b);
    return b;
  },

  solidAt(pxx, pyy) {
    const tx = Math.floor(pxx / T), ty = Math.floor(pyy / T);
    if (tx < 0 || ty < 0 || tx >= this.W || ty >= this.H) return true;
    return this.coll[ty][tx] === 1;
  },
  blocked(x, y) {
    return this.solidAt(x - 4, y - 5) || this.solidAt(x + 4, y - 5) ||
           this.solidAt(x - 4, y - 1) || this.solidAt(x + 4, y - 1);
  },

  update(dt) {
    this.light.dark += (this.light.targetDark - this.light.dark) * Math.min(1, dt * 1.5);
    // chimney smoke
    if (Math.random() < dt * 1.8) {
      for (const h of this.houses) if (h.smoke !== false)
        Particles.spawn({ kind: 'smoke', x: (h.tx + h.tw - 1.2) * T, y: (h.ty + 0.2) * T, vy: -8, life: 3, r: 1.5 });
    }
    const hl = this.heartlight;
    if (hl && hl.state === 'alive' && Math.random() < dt * 5)
      Particles.spawn({ kind: 'mote', x: hl.x + (Math.random() - 0.5) * 24, y: hl.y - 10, vy: -9, life: 2.2, sway: 8 });
    if (hl && hl.state === 'hollow' && Math.random() < dt * 0.5)
      Particles.spawn({ kind: 'moth', x: hl.x + (Math.random() - 0.5) * 16, y: hl.y - 14, vx: 0, vy: -4, life: 5, seed: Math.random() * 9 });
  },

  /* ---------- terrain ---------- */
  matFamily(t) { return (t === PATH || t === PLAZA) ? 1 : t === WATER || t === DOCK ? 3 : t === SAND ? 4 : 0; },
  tileAt(x, y) { return (x < 0 || y < 0 || x >= this.W || y >= this.H) ? GRASS : this.tiles[y][x]; },

  drawGround(g) {
    const { cw, ch } = Screen;
    const x0 = Math.max(0, Math.floor((Camera.x - cw / 2 / Camera.zoom) / T) - 1);
    const x1 = Math.min(this.W - 1, Math.ceil((Camera.x + cw / 2 / Camera.zoom) / T) + 1);
    const y0 = Math.max(0, Math.floor((Camera.y - ch / 2 / Camera.zoom) / T) - 1);
    const y1 = Math.min(this.H - 1, Math.ceil((Camera.y + ch / 2 / Camera.zoom) / T) + 1);

    // pass 1: grass base everywhere (materials round over it)
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) this.drawGrass(g, x, y);
    // pass 2: materials with rounded exposed corners
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
      const t = this.tiles[y][x];
      if (t === GRASS) continue;
      this.drawMaterial(g, x, y, t);
    }
    // flowers
    for (const f of this.flowers) {
      if (f.x < x0 * T || f.x > (x1 + 1) * T || f.y < y0 * T || f.y > (y1 + 1) * T) continue;
      const sway = Math.sin(time * 1.6 + f.ph) * 0.8;
      g.fillStyle = '#4d6e3a'; g.fillRect(f.x, f.y, 1, 4);
      g.fillStyle = f.c; g.fillRect(f.x - 1 + sway, f.y - 3, 3, 3);
      g.fillStyle = '#fff7dd'; g.fillRect(f.x + sway, f.y - 2, 1, 1);
    }
  },

  GRASS_BASE: ['#72b14c', '#6ead49', '#76b550', '#6aa945', '#79b953'],
  drawGrass(g, x, y) {
    const h = hash2(x, y), patch = hash2(x >> 2, y >> 2);
    g.fillStyle = this.GRASS_BASE[(h % 3 + patch % 3) % 5];
    g.fillRect(x * T, y * T, T, T);
    if (h % 5 === 0) {   // grass tufts, pack-style
      g.fillStyle = '#4e8a35';
      const bx = x * T + (h % 12), by = y * T + ((h >> 4) % 11);
      g.fillRect(bx, by, 1, 3); g.fillRect(bx + 2, by + 1, 1, 2);
      g.fillRect(bx + 1, by + 1, 1, 1);
    }
    if (h % 17 === 0) {  // bright blade highlight
      g.fillStyle = '#8fcc68';
      g.fillRect(x * T + ((h >> 2) % 13), y * T + ((h >> 6) % 12), 2, 1.4);
    }
    if (h % 23 === 0) {  // pebble
      g.fillStyle = '#a8a888';
      g.fillRect(x * T + (h % 10) + 2, y * T + ((h >> 3) % 10) + 2, 2, 1.6);
    }
  },

  roundedTilePath(g, px, py, r, nw, ne, sw, se) {
    g.beginPath();
    g.moveTo(px + (nw ? r : 0), py);
    g.lineTo(px + T - (ne ? r : 0), py);
    if (ne) g.arcTo(px + T, py, px + T, py + r, r);
    g.lineTo(px + T, py + T - (se ? r : 0));
    if (se) g.arcTo(px + T, py + T, px + T - r, py + T, r);
    g.lineTo(px + (sw ? r : 0), py + T);
    if (sw) g.arcTo(px, py + T, px, py + T - r, r);
    g.lineTo(px, py + (nw ? r : 0));
    if (nw) g.arcTo(px, py, px + r, py, r);
    g.closePath();
  },

  drawMaterial(g, x, y, t) {
    const px = x * T, py = y * T, h = hash2(x, y);
    const fam = this.matFamily(t);
    const diff = (dx, dy) => this.matFamily(this.tileAt(x + dx, y + dy)) !== fam;
    const nN = diff(0, -1), nS = diff(0, 1), nW = diff(-1, 0), nE = diff(1, 0);
    const corner = { nw: nN && nW, ne: nN && nE, sw: nS && nW, se: nS && nE };

    if (t === PATH) {
      g.fillStyle = '#e0ae7c';
      this.roundedTilePath(g, px, py, 6, corner.nw, corner.ne, corner.sw, corner.se); g.fill();
      g.fillStyle = '#c98f58';
      if (h % 5 === 0) g.fillRect(px + (h % 11), py + (h % 13), 2, 2);
      if (h % 3 === 0) g.fillRect(px + ((h >> 3) % 13), py + ((h >> 5) % 11), 1, 1);
      g.fillStyle = '#edc294';
      if (h % 7 === 0) g.fillRect(px + ((h >> 4) % 11), py + ((h >> 2) % 12), 3, 1.6);
      if (nN) { g.fillStyle = 'rgba(120,80,40,.25)'; g.fillRect(px + (corner.nw ? 5 : 0), py, T - (corner.nw ? 5 : 0) - (corner.ne ? 5 : 0), 2); }
    } else if (t === PLAZA) {
      g.fillStyle = (x + y) % 2 ? '#dcbb90' : '#e6c89e';
      this.roundedTilePath(g, px, py, 5, corner.nw, corner.ne, corner.sw, corner.se); g.fill();
      g.strokeStyle = 'rgba(160,112,66,.45)'; g.lineWidth = 1;
      g.beginPath();
      g.moveTo(px, py + T - 0.5); g.lineTo(px + T, py + T - 0.5);
      g.moveTo(px + ((x % 2) ? 4 : 10), py); g.lineTo(px + ((x % 2) ? 4 : 10), py + T);
      g.stroke();
      if (h % 7 === 0) { g.fillStyle = 'rgba(255,255,240,.16)'; g.fillRect(px + (h % 9), py + ((h >> 3) % 9), 3, 2); }
    } else if (t === SAND) {
      g.fillStyle = '#ecd29a';
      this.roundedTilePath(g, px, py, 6, corner.nw, corner.ne, corner.sw, corner.se); g.fill();
      if (h % 4 === 0) { g.fillStyle = '#d4b87c'; g.fillRect(px + (h % 12), py + (h % 10), 2, 1); }
    } else if (t === WATER || t === DOCK) {
      const deep = !nN && !nS && !nW && !nE;
      g.fillStyle = deep ? '#3b8fd0' : '#4aa8e8';
      this.roundedTilePath(g, px, py, 6, corner.nw, corner.ne, corner.sw, corner.se); g.fill();
      const w = (x + Math.floor(time * 1.6) + y * 3) % 7;
      if (w === 0) { g.fillStyle = 'rgba(200,232,255,.55)'; g.fillRect(px + 2, py + (h % 10) + 2, 10, 1.6); }
      // foam along shore
      const foamA = 0.35 + 0.2 * Math.sin(time * 1.8 + x + y);
      g.fillStyle = `rgba(220,236,244,${foamA})`;
      if (nN) g.fillRect(px + 1, py + 0.5, T - 2, 1.4);
      if (nW) g.fillRect(px + 0.5, py + 1, 1.4, T - 2);
      if (nE) g.fillRect(px + T - 1.9, py + 1, 1.4, T - 2);
      if (nS) g.fillRect(px + 1, py + T - 1.9, T - 2, 1.4);
      if (t === DOCK) {
        g.fillStyle = '#96703d'; g.fillRect(px, py + 2, T, T - 4);
        g.fillStyle = '#775732'; g.fillRect(px, py + 7, T, 1); g.fillRect(px + 7 + (x % 2), py + 2, 1, T - 4);
        g.fillStyle = 'rgba(255,235,200,.14)'; g.fillRect(px, py + 2, T, 1.4);
      }
    }
  },

  /* ---------- structures & props ---------- */
  // tileset source rects (in 16px tile units) for the pack's assembled buildings
  HOUSE_SRC: {
    cottage: [0, 0, 4, 3],   // tan thatch
    elder:   [4, 0, 4, 3],   // large flat-roof hall
    thatch:  [8, 0, 4, 3],   // second thatch cottage
    bakery:  [12, 0, 4, 3],  // red tiled roof
    hut:     [16, 0, 3, 3],  // round brown hut
  },
  // warm window-glow offsets per style (drawn when the house is lit)
  HOUSE_GLOW: {
    cottage: [[8, 36], [46, 36]],
    elder:   [[10, 36], [44, 36]],
    thatch:  [[8, 36], [46, 36]],
    bakery:  [[9, 36], [45, 36]],
    hut:     [[14, 36], [30, 36]],
  },
  drawHouse(g, h) {
    const ts = GameImages.tileset;
    const src = this.HOUSE_SRC[h.style];
    if (ts.complete && ts.naturalWidth && src) {
      const [sx, sy, sw, sh] = src;
      const x = h.tx * T, y = h.ty * T;
      g.fillStyle = 'rgba(0,0,0,.18)';
      g.beginPath(); g.ellipse(x + sw * 8, y + sh * 16 - 2, sw * 8, 4, 0, 0, 7); g.fill();
      g.drawImage(ts, sx * 16, sy * 16, sw * 16, sh * 16, x, y, sw * 16, sh * 16);
      if (!h.dark) {
        const glows = this.HOUSE_GLOW[h.style] || [];
        for (const [gx, gy] of glows) {
          g.fillStyle = `rgba(255,214,130,${0.75 + Math.sin(time * 3 + gx) * 0.1})`;
          g.fillRect(x + gx, y + gy, 7, 6);
          g.fillStyle = 'rgba(255,240,200,.8)';
          g.fillRect(x + gx + 1, y + gy + 1, 2.5, 2);
        }
      }
      return;
    }
    this.drawHouseProcedural(g, h);
  },
  drawHouseProcedural(g, h) {
    const x = h.tx * T, y = h.ty * T, w = h.tw * T, hh = h.th * T;
    const wallTop = y + hh * 0.40;
    const st = h.style;
    const wall = st === 'elder' ? '#c5bba3' : '#e7d2a8';
    const wallShade = st === 'elder' ? '#a89e88' : '#cbb589';
    const roofA = st === 'bakery' ? '#a5563b' : st === 'elder' ? '#6d7b8a' : '#b5854a';
    const roofB = st === 'bakery' ? '#8a4630' : st === 'elder' ? '#59636f' : '#96702f';
    const roofC = st === 'bakery' ? '#bd6a4a' : st === 'elder' ? '#7e8c9a' : '#c9985e';

    // stone foundation
    g.fillStyle = '#8f8672'; g.fillRect(x - 1, y + hh - 5, w + 2, 5);
    g.fillStyle = '#7a7260';
    for (let i = 0; i < w; i += 7) g.fillRect(x + i, y + hh - 5, 1, 5);
    // walls
    g.fillStyle = wall; g.fillRect(x, wallTop, w, y + hh - 5 - wallTop);
    g.fillStyle = wallShade; g.fillRect(x, y + hh - 10, w, 5);
    if (st !== 'elder') {
      g.fillStyle = '#8a6a45';
      g.fillRect(x, wallTop, 2.4, y + hh - wallTop); g.fillRect(x + w - 2.4, wallTop, 2.4, y + hh - wallTop);
      g.fillRect(x, wallTop, w, 2.4);
      g.fillRect(x + w / 2 - 1.2, wallTop, 2.4, y + hh - wallTop);
      // diagonal braces
      g.strokeStyle = '#8a6a45'; g.lineWidth = 2;
      g.beginPath(); g.moveTo(x + 3, wallTop + 3); g.lineTo(x + w / 2 - 3, y + hh - 8); g.stroke();
      g.beginPath(); g.moveTo(x + w - 3, wallTop + 3); g.lineTo(x + w / 2 + 3, y + hh - 8); g.stroke();
    } else {
      g.strokeStyle = 'rgba(90,80,60,.3)'; g.lineWidth = 1;
      for (let i = 1; i < 4; i++) { g.beginPath(); g.moveTo(x, wallTop + i * 8); g.lineTo(x + w, wallTop + i * 8); g.stroke(); }
    }
    // roof — shingle rows
    const peakY = y - 10;
    g.fillStyle = roofB;
    g.beginPath();
    g.moveTo(x - 6, wallTop + 1); g.lineTo(x + w + 6, wallTop + 1);
    g.lineTo(x + w - 9, peakY); g.lineTo(x + 9, peakY);
    g.closePath(); g.fill();
    const rows = 4;
    for (let i = 0; i < rows; i++) {
      const f = i / rows, f2 = (i + 1) / rows;
      const yA = wallTop + 1 + (peakY - wallTop - 1) * f;
      const yB = wallTop + 1 + (peakY - wallTop - 1) * f2;
      const inA = 6 - 15 * f, inB = 6 - 15 * f2;
      g.fillStyle = i % 2 ? roofA : roofC;
      g.beginPath();
      g.moveTo(x - inA, yA); g.lineTo(x + w + inA, yA);
      g.lineTo(x + w + inB, yB + 1); g.lineTo(x - inB, yB + 1);
      g.closePath(); g.fill();
      g.fillStyle = 'rgba(40,25,15,.18)';
      g.fillRect(x - inA, yA, w + inA * 2, 1.2);
    }
    g.fillStyle = roofB; g.fillRect(x + 8, peakY - 2, w - 16, 3); // ridge
    g.fillStyle = 'rgba(20,12,8,.25)'; g.fillRect(x - 6, wallTop + 1, w + 12, 3); // eave shadow
    // chimney
    g.fillStyle = '#8f8672'; g.fillRect(x + w - T * 1.4, y - 18, 8, 14);
    g.fillStyle = '#6f6552'; g.fillRect(x + w - T * 1.4 - 1, y - 20, 10, 3.4);
    // door
    const dx = x + w / 2 - 6, dyy = y + hh - 19;
    g.fillStyle = '#573823';
    g.fillRect(dx, dyy + 5, 12, 14);
    g.beginPath(); g.arc(dx + 6, dyy + 5, 6, Math.PI, 0); g.fill();
    g.fillStyle = 'rgba(255,220,160,.16)'; g.fillRect(dx + 1.4, dyy + 6, 1.6, 12);
    g.fillStyle = '#3c2717'; g.fillRect(dx + 5.4, dyy, 1.2, 4);
    g.fillStyle = '#e0a94e'; g.fillRect(dx + 9, dyy + 11, 1.8, 1.8);
    // windows (light sources at night)
    const wy = wallTop + 7;
    for (const wx of [x + 6, x + w - 17]) {
      g.fillStyle = '#3c2f1e'; g.fillRect(wx - 1, wy - 1, 13, 11);
      g.fillStyle = h.dark ? '#31404d' : '#f0c56d';
      g.fillRect(wx, wy, 11, 9);
      if (!h.dark) { g.fillStyle = '#f7dfa4'; g.fillRect(wx + 1, wy + 1, 4, 3); }
      g.strokeStyle = '#6b5335'; g.lineWidth = 1.4;
      g.strokeRect(wx, wy, 11, 9);
      g.beginPath(); g.moveTo(wx + 5.5, wy); g.lineTo(wx + 5.5, wy + 9); g.stroke();
      // window box
      g.fillStyle = '#7a5a35'; g.fillRect(wx - 1, wy + 9.6, 13, 2.4);
      g.fillStyle = '#c9666f'; g.fillRect(wx + 1, wy + 8.4, 2, 2);
      g.fillStyle = '#e0a94e'; g.fillRect(wx + 5, wy + 8.4, 2, 2);
      g.fillStyle = '#c9666f'; g.fillRect(wx + 9, wy + 8.4, 2, 2);
    }
    if (st === 'bakery') {
      g.fillStyle = '#8a6a45'; g.fillRect(x + w - 7, wallTop + 3, 1.6, 9);
      g.fillStyle = '#e8d1a0'; g.fillRect(x + w - 13, wallTop + 11, 13, 9);
      g.strokeStyle = '#8a6a45'; g.lineWidth = 1; g.strokeRect(x + w - 13, wallTop + 11, 13, 9);
      g.fillStyle = '#b3792f';
      g.beginPath(); g.ellipse(x + w - 6.5, wallTop + 15.5, 4.4, 2.6, 0, 0, 7); g.fill();
      g.fillStyle = '#e8d1a0'; g.fillRect(x + w - 9.2, wallTop + 14.8, 5.5, 0.9);
    }
  },

  drawTree(g, t) {
    const ts = GameImages.tileset;
    if (ts.complete && ts.naturalWidth) {
      g.fillStyle = 'rgba(0,0,0,.2)';
      g.beginPath(); g.ellipse(t.x, t.y + 1, t.big ? 13 : 9, 3.4, 0, 0, 7); g.fill();
      if (t.big) g.drawImage(ts, 136, 142, 48, 48, t.x - 24, t.y - 46, 48, 48);   // twin pines
      else g.drawImage(ts, 185, 160, 28, 27, t.x - 14, t.y - 25, 28, 27);         // round autumn tree
      return;
    }
    const sway = Math.sin(time * 0.9 + t.x * 0.05) * 0.8;
    const s = t.big ? 1.3 : 1;
    g.fillStyle = 'rgba(0,0,0,.2)';
    g.beginPath(); g.ellipse(t.x, t.y + 1, 8.5 * s, 3, 0, 0, 7); g.fill();
    // trunk with root flare
    g.fillStyle = '#6e4a2b';
    g.fillRect(t.x - 2, t.y - 11 * s, 4, 12 * s);
    g.fillRect(t.x - 3.4, t.y - 2, 6.8, 3);
    g.fillStyle = '#573923'; g.fillRect(t.x + 0.6, t.y - 10 * s, 1.4, 10 * s);
    const cy = t.y - 15 * s, h = hash2(t.x | 0, t.y | 0);
    g.fillStyle = '#3d652c';
    g.beginPath(); g.arc(t.x + sway, cy + 4, 10 * s, 0, 7); g.fill();
    g.fillStyle = '#4c7a37';
    g.beginPath(); g.arc(t.x + sway - 3.5, cy - 1, 8 * s, 0, 7); g.fill();
    g.beginPath(); g.arc(t.x + sway + 4.5, cy, 7.5 * s, 0, 7); g.fill();
    g.fillStyle = '#5f9345';
    g.beginPath(); g.arc(t.x + sway - 2, cy - 4.5, 5 * s, 0, 7); g.fill();
    g.fillStyle = '#71a552';
    g.beginPath(); g.arc(t.x + sway - 4, cy - 6, 2.6 * s, 0, 7); g.fill();
    // dithered edge pixels
    g.fillStyle = '#4c7a37';
    for (let i = 0; i < 5; i++) {
      const a = (h % 360) / 57 + i * 1.3;
      g.fillRect(t.x + sway + Math.cos(a) * 9.6 * s, cy + Math.sin(a) * 8.6 * s, 1.6, 1.6);
    }
  },

  drawHeartlight(g) {
    const hl = this.heartlight;
    if (!hl) return;
    const x = hl.x, y = hl.y;
    const alive = hl.state === 'alive';
    const pulse = alive ? 0.35 + 0.14 * Math.sin(time * 2.2) : 0.04;
    if (alive) {
      const gr = g.createRadialGradient(x, y - 16, 2, x, y - 16, 44);
      gr.addColorStop(0, `rgba(245,180,90,${pulse})`);
      gr.addColorStop(1, 'rgba(245,180,90,0)');
      g.fillStyle = gr; g.fillRect(x - 44, y - 60, 88, 88);
    }
    // carved pedestal
    g.fillStyle = '#a89c85'; g.fillRect(x - 12, y - 7, 24, 8);
    g.fillStyle = '#948a73'; g.fillRect(x - 9, y - 12, 18, 6);
    g.fillStyle = '#7a6f5a'; g.fillRect(x - 12, y + 1, 24, 2);
    g.fillStyle = alive ? '#e0a94e' : '#7a6f5a';
    for (let i = -8; i <= 8; i += 4) g.fillRect(x + i, y - 5.4, 2, 2); // rune dots
    // crystal
    g.save();
    g.translate(x, y - 12);
    const cTop = alive ? '#f7dfae' : '#b5b0a8';
    const cMid = alive ? '#f0b96a' : '#9a958d';
    const cDeep = alive ? '#d98a3c' : '#807b74';
    g.fillStyle = cMid;
    g.beginPath(); g.moveTo(0, -26); g.lineTo(8, -10); g.lineTo(0, 0); g.lineTo(-8, -10); g.closePath(); g.fill();
    g.fillStyle = cTop;
    g.beginPath(); g.moveTo(0, -26); g.lineTo(-8, -10); g.lineTo(-2, -8); g.lineTo(-1, -22); g.closePath(); g.fill();
    g.fillStyle = cDeep;
    g.beginPath(); g.moveTo(0, -26); g.lineTo(8, -10); g.lineTo(3, -6); g.lineTo(0, -20); g.closePath(); g.fill();
    if (alive) {
      g.fillStyle = `rgba(255,250,235,${0.5 + 0.3 * Math.sin(time * 3)})`;
      g.fillRect(-2, -21, 2, 7);
    } else {
      g.strokeStyle = '#5d5952'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(-2, -20); g.lineTo(1, -14); g.lineTo(-1, -9); g.stroke();
      g.beginPath(); g.moveTo(3, -18); g.lineTo(1, -12); g.stroke();
    }
    g.restore();
  },

  drawGate(g) {
    const gt = this.gate;
    if (!gt) return;
    const x0 = gt.x0 * T, y0 = gt.y0 * T, x1 = (gt.x1 + 1) * T, y1 = (gt.y1 + 1) * T;
    const openW = gt.open ? 1 : (gt.opening || 0);
    for (const px of [x0, x1 - 2 * T]) {
      g.fillStyle = '#a89c85'; g.fillRect(px, y0 - 14, 2 * T, y1 - y0 + 14);
      g.fillStyle = '#948a73'; g.fillRect(px + 2 * T - 5, y0 - 14, 5, y1 - y0 + 14);
      g.fillStyle = '#8f836c';
      for (let i = 0; i < 4; i++) g.fillRect(px + (i % 2 ? 3 : 7), y0 - 8 + i * 12, 2 * T - 12, 1.8);
      g.fillStyle = '#bdb29b'; g.fillRect(px - 2, y0 - 19, 2 * T + 4, 6);
      g.fillStyle = '#7a6f5a'; g.fillRect(px - 2, y0 - 13, 2 * T + 4, 1.6);
      // ivy
      g.fillStyle = '#4c7a37';
      g.fillRect(px + 2, y0 - 10, 3, 7); g.fillRect(px + 4, y0 - 4, 3, 9); g.fillRect(px + 2 * T - 8, y0 + 2, 3, 8);
    }
    const doorW = (3 * T / 2) * (1 - openW);
    if (doorW > 0.5) {
      g.fillStyle = '#4d3520';
      g.fillRect(x0 + 2 * T, y0 - 4, doorW, y1 - y0 + 4);
      g.fillRect(x1 - 2 * T - doorW, y0 - 4, doorW, y1 - y0 + 4);
      g.fillStyle = '#5f4128';
      for (let i = 1; i < 4; i++) {
        g.fillRect(x0 + 2 * T + (doorW * i / 4), y0 - 4, 1.4, y1 - y0 + 4);
        g.fillRect(x1 - 2 * T - (doorW * i / 4), y0 - 4, 1.4, y1 - y0 + 4);
      }
      g.fillStyle = '#3a3f4a';
      g.fillRect(x0 + 2 * T + 2, y0 + 8, doorW - 4 > 0 ? Math.min(4, doorW - 4) : 0, 10);
    } else {
      g.fillStyle = '#141b12'; g.fillRect(x0 + 2 * T, y0 - 4, 3 * T, 6);
    }
    g.fillStyle = '#bdb29b'; g.fillRect(x0, y0 - 27, x1 - x0, 10);
    g.fillStyle = '#a89c85'; g.fillRect(x0 + 4, y0 - 25, x1 - x0 - 8, 6);
    const lit = gt.sigilsLit;
    g.strokeStyle = lit ? `rgba(232,134,58,${0.6 + 0.4 * Math.sin(time * 2.5)})` : '#7a6f5a';
    g.lineWidth = 1.5;
    const cx = (x0 + x1) / 2;
    g.beginPath(); g.arc(cx - 4, y0 - 22, 3.4, 0, 7); g.stroke();
    g.beginPath(); g.arc(cx + 4, y0 - 22, 3.4, 0, 7); g.stroke();
  },

  drawPlates(g) {
    for (const pl of this.plates) {
      const gt = this.gate;
      const active = gt && gt.sigilsLit && !gt.open;
      const glow = gt && gt.open ? 1 : pl.hold || 0;
      g.save();
      g.translate(pl.x, pl.y);
      g.fillStyle = '#a89c85'; g.beginPath(); g.arc(0, 0, 9, 0, 7); g.fill();
      g.fillStyle = '#8f836c'; g.beginPath(); g.arc(0, 0, 7, 0, 7); g.fill();
      g.strokeStyle = active || glow > 0 ? `rgba(232,134,58,${0.35 + 0.65 * glow})` : '#7a6f5a';
      g.lineWidth = 1.4;
      g.beginPath(); g.arc(0, 0, 4.6, 0, 7); g.stroke();
      g.beginPath(); g.moveTo(-3, 2); g.quadraticCurveTo(0, -4, 3, 2); g.stroke();
      if (active && glow > 0 && glow < 1) {
        g.strokeStyle = '#f2d16b'; g.lineWidth = 1.6;
        g.beginPath(); g.arc(0, 0, 11, -Math.PI / 2, -Math.PI / 2 + glow * Math.PI * 2); g.stroke();
      }
      if (active && !glow) {
        const p2 = 0.5 + 0.5 * Math.sin(time * 3);
        g.strokeStyle = `rgba(232,134,58,${0.25 + 0.3 * p2})`;
        g.beginPath(); g.arc(0, 0, 11 + p2 * 2, 0, 7); g.stroke();
      }
      g.restore();
    }
  },

  drawProp(g, p) {
    if (p.type === 'lamp') {
      const x = p.x, y = p.y;
      g.fillStyle = 'rgba(0,0,0,.2)';
      g.beginPath(); g.ellipse(x, y + 1, 4.5, 1.8, 0, 0, 7); g.fill();
      g.fillStyle = '#3a3f4a'; g.fillRect(x - 2.6, y - 2.4, 5.2, 2.6);
      g.fillRect(x - 1.2, y - 22, 2.4, 20);
      g.fillStyle = '#2b2f38'; g.fillRect(x + 0.2, y - 22, 1, 20);
      // housing
      g.fillStyle = '#3a3f4a';
      g.fillRect(x - 4.4, y - 31, 8.8, 9.4);
      g.beginPath(); g.moveTo(x - 4.4, y - 31); g.lineTo(x, y - 34.5); g.lineTo(x + 4.4, y - 31); g.closePath(); g.fill();
      g.fillStyle = p.lit ? '#ffd98a' : '#1c202a';
      g.fillRect(x - 3, y - 29.6, 6, 6.8);
      if (p.lit) {
        g.fillStyle = '#fff3cf';
        g.fillRect(x - 1.2, y - 28 + Math.sin(time * 9 + x) * 0.5, 2.4, 3.4);
      }
      g.fillStyle = '#3a3f4a'; g.fillRect(x - 5, y - 22.4, 10, 1.6);
    } else if (p.type === 'stall') {
      const x = p.x - 8, y = p.y, w = (p.tw || 2) * T;
      g.fillStyle = 'rgba(0,0,0,.2)';
      g.beginPath(); g.ellipse(x + w / 2, y + 1, w / 2, 2.4, 0, 0, 7); g.fill();
      // counter
      g.fillStyle = '#96703d'; g.fillRect(x, y - 12, w, 12);
      g.fillStyle = '#775732'; g.fillRect(x, y - 12, w, 2); g.fillRect(x, y - 4, w, 1.4);
      // goods
      if (p.goods === 'buns') {
        g.fillStyle = '#c98a3f';
        for (let i = 0; i < 4; i++) g.beginPath(), g.ellipse(x + 6 + i * 6.5, y - 13.6, 2.6, 1.8, 0, 0, 7), g.fill();
        g.fillStyle = '#e8b46a';
        for (let i = 0; i < 3; i++) g.beginPath(), g.ellipse(x + 9 + i * 6.5, y - 15.6, 2.6, 1.8, 0, 0, 7), g.fill();
      } else {
        g.fillStyle = '#c9666f'; g.fillRect(x + 4, y - 15, 5, 3);
        g.fillStyle = '#4f9f92'; g.fillRect(x + 12, y - 16, 5, 4);
        g.fillStyle = '#e0a94e'; g.fillRect(x + 20, y - 15, 5, 3);
      }
      // poles + awning
      g.fillStyle = '#775732';
      g.fillRect(x + 0.6, y - 30, 2, 18); g.fillRect(x + w - 2.6, y - 30, 2, 18);
      const c1 = p.c1 || '#c9584a', c2 = p.c2 || '#f2e8d0';
      for (let i = 0; i < w / 6; i++) {
        g.fillStyle = i % 2 ? c1 : c2;
        g.fillRect(x - 2 + i * 6, y - 34, 6, 5);
        g.beginPath();
        g.moveTo(x - 2 + i * 6, y - 29); g.lineTo(x + 1 + i * 6, y - 26); g.lineTo(x + 4 + i * 6, y - 29);
        g.closePath(); g.fill();
      }
    } else if (p.type === 'crate') {
      const x = p.x - 6, y = p.y - 11;
      g.fillStyle = '#a5783f'; g.fillRect(x, y, 12, 11);
      g.strokeStyle = '#7c5a2e'; g.lineWidth = 1.2;
      g.strokeRect(x + 0.6, y + 0.6, 10.8, 9.8);
      g.beginPath(); g.moveTo(x, y); g.lineTo(x + 12, y + 11); g.moveTo(x + 12, y); g.lineTo(x, y + 11); g.stroke();
    } else if (p.type === 'barrel') {
      const x = p.x, y = p.y;
      g.fillStyle = '#8a6234'; g.beginPath(); g.ellipse(x, y - 6, 5.5, 7, 0, 0, 7); g.fill();
      g.fillStyle = '#6d4d28'; g.fillRect(x - 5.5, y - 9, 11, 1.4); g.fillRect(x - 5.5, y - 4, 11, 1.4);
      g.fillStyle = '#a5783f'; g.beginPath(); g.ellipse(x, y - 12.4, 5.5, 2, 0, 0, 7); g.fill();
    } else if (p.type === 'sign') {
      const x = p.x, y = p.y;
      g.fillStyle = '#775732'; g.fillRect(x - 1.2, y - 16, 2.4, 16);
      g.fillStyle = '#a5783f'; g.fillRect(x - 9, y - 22, 18, 8);
      g.strokeStyle = '#775732'; g.lineWidth = 1; g.strokeRect(x - 9, y - 22, 18, 8);
      g.fillStyle = '#57432a';
      g.fillRect(x - 6, y - 19.6, 5, 1.2); g.fillRect(x + 1, y - 19.6, 4, 1.2); g.fillRect(x - 6, y - 17, 8, 1.2);
    } else if (p.type === 'noticeboard') {
      const x = p.x, y = p.y;
      g.fillStyle = '#775732'; g.fillRect(x - 8, y - 20, 2.4, 20); g.fillRect(x + 5.6, y - 20, 2.4, 20);
      g.fillStyle = '#96703d'; g.fillRect(x - 11, y - 26, 22, 9);
      g.fillStyle = '#775732'; g.fillRect(x - 11, y - 27, 22, 1.6);
      g.fillStyle = '#f2e4c4'; g.fillRect(x - 8, y - 24.4, 6, 6);
      g.fillStyle = '#e8d5b0'; g.fillRect(x - 0.6, y - 24.4, 5, 5);
      g.fillStyle = '#c9b380'; g.fillRect(x - 7, y - 23, 4, 0.8); g.fillRect(x - 7, y - 21.4, 4, 0.8);
    } else if (p.type === 'waystone') {
      const x = p.x, y = p.y;
      g.fillStyle = 'rgba(0,0,0,.2)';
      g.beginPath(); g.ellipse(x, y + 1, 6, 2.2, 0, 0, 7); g.fill();
      g.fillStyle = '#a89c85'; g.fillRect(x - 5, y - 16, 10, 16);
      g.fillStyle = '#948a73'; g.fillRect(x + 2, y - 16, 3, 16);
      g.fillStyle = '#bdb29b'; g.beginPath(); g.arc(x, y - 16, 5, Math.PI, 0); g.fill();
      g.fillStyle = '#5d7a3a'; g.fillRect(x - 5, y - 6, 4, 6); g.fillRect(x - 2, y - 3, 3, 3);
      g.fillStyle = '#57432a';
      g.fillRect(x - 3, y - 13, 6, 1); g.fillRect(x - 3, y - 11, 4, 1); g.fillRect(x - 3, y - 9, 5, 1);
    } else if (p.type === 'fence') {
      const x = p.x - 8, y = p.y, w = (p.tw || 1) * T;
      g.fillStyle = '#8a6a45';
      for (let i = 0; i <= w; i += 8) { g.fillRect(x + i, y - 10, 2.4, 10); g.fillRect(x + i, y - 11.4, 2.4, 2); }
      g.fillRect(x, y - 8.6, w + 2, 1.8); g.fillRect(x, y - 4.4, w + 2, 1.8);
    }
  },

  drawBuntings(g) {
    for (const b of this.buntings) {
      const midX = (b.x1 + b.x2) / 2, midY = Math.max(b.y1, b.y2) + 10;
      g.strokeStyle = 'rgba(60,45,30,.8)'; g.lineWidth = 0.8;
      g.beginPath(); g.moveTo(b.x1, b.y1); g.quadraticCurveTo(midX, midY, b.x2, b.y2); g.stroke();
      const N = Math.max(4, Math.floor(Math.hypot(b.x2 - b.x1, b.y2 - b.y1) / 10));
      const cols = ['#c9584a', '#e0a94e', '#4f9f92', '#c9666f'];
      for (let i = 1; i < N; i++) {
        const t2 = i / N, omt = 1 - t2;
        const fx = omt * omt * b.x1 + 2 * omt * t2 * midX + t2 * t2 * b.x2;
        const fy = omt * omt * b.y1 + 2 * omt * t2 * midY + t2 * t2 * b.y2;
        if (i % 3 === 0) {
          // paper lantern
          g.fillStyle = b.lit ? '#ffd98a' : '#8a8494';
          g.beginPath(); g.ellipse(fx, fy + 3, 2.6, 3.2, 0, 0, 7); g.fill();
          g.fillStyle = b.lit ? '#f0a052' : '#6d6878';
          g.fillRect(fx - 2.6, fy + 2.4, 5.2, 1);
        } else {
          const sway2 = Math.sin(time * 2 + i) * 1;
          g.fillStyle = cols[i % 4];
          g.beginPath(); g.moveTo(fx - 2.4, fy); g.lineTo(fx + 2.4, fy); g.lineTo(fx + sway2 * 0.3, fy + 4.6); g.closePath(); g.fill();
        }
      }
    }
  },

  /* ---------- characters ---------- */
  DIR_COL: { down: 0, up: 1, right: 3, left: 2 },
  drawChar(g, e) {
    const sheet = GameImages.chars[e.look];
    if (sheet && sheet.complete && sheet.naturalWidth) {
      const col = this.DIR_COL[e.dir] ?? 0;
      const row = e.moving ? Math.floor((e.animT || 0) * 9) % 4 : 0;
      g.save();
      g.translate(Math.round(e.x), Math.round(e.y));
      if (e.alpha != null) g.globalAlpha = e.alpha;
      g.fillStyle = 'rgba(0,0,0,.22)';
      g.beginPath(); g.ellipse(0, 0, 6, 2.4, 0, 0, 7); g.fill();
      g.drawImage(sheet, col * 16, row * 16, 16, 16, -8, -15, 16, 16);
      if (e.lightCarrier) {
        g.fillStyle = '#8a6a30'; g.fillRect(4.6, -6.8, 2.4, 3);
        g.fillStyle = '#ffd98a'; g.fillRect(5.1, -8.6 + Math.sin(time * 10) * 0.4, 1.4, 2);
      }
      g.restore();
      return;
    }
    this.drawCharProcedural(g, e);
  },
  // outlined, shaded procedural sprites driven by LOOKS (fallback)
  drawCharProcedural(g, e) {
    const look = LOOKS[e.look] || LOOKS.june;
    const f = e.moving ? Math.floor(e.animT * 8) % 4 : 0;
    const bob = (f === 1 || f === 3) ? -1 : 0;
    const kid = look.kid ? 0.78 : 1;
    const side = e.dir === 'left' || e.dir === 'right';
    g.save();
    g.translate(Math.round(e.x), Math.round(e.y));
    if (e.dir === 'left') g.scale(-1, 1);
    if (e.alpha != null) g.globalAlpha = e.alpha;
    g.scale(kid, kid);

    g.fillStyle = 'rgba(0,0,0,.22)';
    g.beginPath(); g.ellipse(0, 0, 6, 2.4, 0, 0, 7); g.fill();

    const rects = [];
    const R = (x, y, w, h, c, noOutline) => rects.push({ x, y, w, h, c, noOutline });
    const skin = look.skin, hair = look.hair, tun = look.outfit, shd = look.shade, acc = look.accent;

    if (look.cloak) {
      // hooded figure
      R(-6, -15 + bob, 12, 15, tun);
      R(-6, -3 + bob, 12, 3, shd);
      R(-5, -21 + bob, 10, 7, tun);        // hood
      R(-3.4, -19 + bob, 6.8, 4.6, '#100c18'); // void face
      if (e.dir !== 'up') { R(-1.8, -17.4 + bob, 1.2, 1.2, '#cfd6e8', true); R(0.8, -17.4 + bob, 1.2, 1.2, '#cfd6e8', true); }
    } else if (look.robe) {
      R(-5.4, -14 + bob, 10.8, 14, tun);
      R(-5.4, -3.4 + bob, 10.8, 3.4, shd);
      R(-1, -12 + bob, 2, 8, shd);          // robe fold
      if (look.staff) { R(6.4, -19, 1.8, 19, '#8a6a45'); R(6, -21.4, 2.6, 2.6, '#e0a94e'); }
    } else {
      // legs + boots
      const lo = e.moving ? (f === 1 ? -1.6 : f === 3 ? 1.6 : 0) : 0;
      if (side) {
        R(-3 + lo, -5, 3, 5, shd); R(0.4 - lo, -5, 3, 5, shd);
        R(-3 + lo, -2.4, 3, 2.4, '#3f3428'); R(0.4 - lo, -2.4, 3, 2.4, '#3f3428');
      } else {
        R(-4 + lo * 0.4, -5, 3.2, 5, shd); R(0.8 - lo * 0.4, -5, 3.2, 5, shd);
        R(-4 + lo * 0.4, -2.4, 3.2, 2.4, '#3f3428'); R(0.8 - lo * 0.4, -2.4, 3.2, 2.4, '#3f3428');
      }
      // torso
      R(-5, -12.4 + bob, 10, 7.6, tun);
      R(2, -12.4 + bob, 3, 7.6, shd);                    // side shade
      R(-5, -6 + bob, 10, 1.2, '#3f3428');               // belt
      if (look.apron) { R(-3, -11.4 + bob, 6, 6.4, '#f2e8d0'); R(-3, -11.4 + bob, 6, 1, '#d9cba8'); }
      if (look.shawl) { R(-5.6, -12.8 + bob, 11.2, 3.4, acc); }
      // arms
      const sw = e.moving ? (f === 1 ? 1.2 : f === 3 ? -1.2 : 0) : 0;
      if (side) { R(-1.4, -11 + bob + sw * 0.4, 2.8, 5.4, tun); R(-1.4, -6 + bob + sw * 0.4, 2.8, 1.4, skin); }
      else {
        R(-7, -11.4 + bob + sw, 2.2, 5, tun); R(4.8, -11.4 + bob - sw, 2.2, 5, tun);
        R(-7, -6.8 + bob + sw, 2.2, 1.6, skin); R(4.8, -6.8 + bob - sw, 2.2, 1.6, skin);
      }
      // scarf accent
      R(side ? -3 : -3.4, -13 + bob, side ? 6 : 6.8, 1.8, acc);
    }

    // head
    if (!look.cloak) {
      const hy = (look.robe ? -21.4 : -19.4) + bob;
      R(-4.6, hy, 9.2, 7.4, skin);
      R(2.4, hy + 1, 2.2, 6, look.robe ? skin : skin === Palette.skin ? Palette.skinShade : skin); // cheek shade
      // hair
      R(-4.6, hy - 2.6, 9.2, 3.8, hair);
      if (e.dir === 'up') R(-4.6, hy, 9.2, 6.6, hair);
      if (side) R(1, hy, 3.6, 6, hair);
      if (look.hairstyle === 'braid' && !side) R(3.4, hy + 1, 2, 9.4, hair);
      if (look.hairstyle === 'braid' && side) R(2.6, hy + 2, 2, 8.6, hair);
      if (look.hairstyle === 'bun') R(side ? 2.6 : -1.4, hy - 4.4, 3.4, 3, hair);
      if (look.hairstyle === 'messy') { R(-5.2, hy - 1.4, 2, 2.4, hair); R(3.4, hy - 1.8, 2, 2.4, hair); }
      if (look.beard) R(-2.8, hy + 5.8, 5.6, 3.6, hair);
      if (look.hat === 'puff') { R(-5.2, hy - 4.6, 10.4, 3.6, '#f2e8d0'); R(-4, hy - 6, 8, 2, '#f2e8d0'); }
      if (look.hat === 'bucket') { R(-6, hy - 1.8, 12, 2.4, '#8a7448'); R(-4, hy - 4.4, 8, 3, '#8a7448'); }
      // eyes
      if (e.dir === 'down') { R(-2.4, hy + 3, 1.3, 1.9, '#2b2027', true); R(1.1, hy + 3, 1.3, 1.9, '#2b2027', true); }
      if (side) R(1.6, hy + 3, 1.3, 1.9, '#2b2027', true);
    }

    // ink outline pass, then color pass
    g.fillStyle = Palette.ink;
    for (const r of rects) if (!r.noOutline) g.fillRect(r.x - 0.7, r.y - 0.7, r.w + 1.4, r.h + 1.4);
    for (const r of rects) { g.fillStyle = r.c; g.fillRect(r.x, r.y, r.w, r.h); }

    // Cole's ever-lit lighter — a warm point at his hand
    if (e.lightCarrier) {
      g.fillStyle = '#8a6a30'; g.fillRect(4.6, -7.4 + bob, 2.6, 3.4);
      g.fillStyle = '#ffd98a'; g.fillRect(5.2, -9.4 + bob + Math.sin(time * 10) * 0.4, 1.4, 2.2);
    }
    g.restore();
  },

  drawCat(g, e) {
    const wig = Math.sin(time * 3 + 1) * 2;
    const flip = e.dir === 'left' ? -1 : 1;
    g.save();
    g.translate(Math.round(e.x), Math.round(e.y));
    g.scale(flip, 1);
    g.fillStyle = 'rgba(0,0,0,.18)';
    g.beginPath(); g.ellipse(0, 0, 5, 1.8, 0, 0, 7); g.fill();
    g.fillStyle = Palette.ink; g.fillRect(-5.7, -5.7, 9.4, 6.4); g.fillRect(0.3, -8.7, 6.4, 6.4);
    g.fillStyle = '#d9a441'; g.fillRect(-5, -5, 8, 5); g.fillRect(1, -8, 5, 5);
    g.fillStyle = '#b3792f';
    g.fillRect(-4, -5, 1.4, 5); g.fillRect(-1, -5, 1.4, 5);
    g.beginPath();
    g.moveTo(-5, -4); g.quadraticCurveTo(-8, -6 + wig, -7, -9 + wig);
    g.strokeStyle = '#d9a441'; g.lineWidth = 1.6; g.stroke();
    g.fillStyle = '#d9a441';
    g.beginPath(); g.moveTo(1.4, -8); g.lineTo(2.4, -10.6); g.lineTo(3.4, -8); g.fill();
    g.beginPath(); g.moveTo(3.8, -8); g.lineTo(4.8, -10.6); g.lineTo(5.8, -8); g.fill();
    g.fillStyle = '#3f5c3a'; g.fillRect(4.4, -6.6, 1.2, 1.4);
    g.restore();
  },

  /* ---------- scene assembly ---------- */
  drawScene(g, entities) {
    const painted = this.usingBackdrop();
    if (painted) {
      g.save();
      g.imageSmoothingEnabled = true;
      g.drawImage(this.backdropImg, 0, 0, this.W * T, this.H * T);
      g.restore();
    } else {
      this.drawGround(g);
    }
    this.drawPlates(g);
    const items = [];
    if (!painted) {
      for (const h of this.houses) items.push({ y: (h.ty + h.th) * T - 2, d: () => this.drawHouse(g, h) });
      for (const t of this.trees) items.push({ y: t.y, d: () => this.drawTree(g, t) });
    }
    for (const p of this.props) {
      if (painted && this.BAKED_PROPS.has(p.type)) continue;
      items.push({ y: p.y, d: () => this.drawProp(g, p) });
    }
    if (this.heartlight) items.push({ y: this.heartlight.y + 6, d: () => this.drawHeartlight(g) });
    if (this.gate) items.push({ y: this.gate.y1 * T + T, d: () => this.drawGate(g) });
    for (const e of entities) {
      if (e.hidden) continue;
      items.push({ y: e.y, d: () => (e.cat ? this.drawCat(g, e) : this.drawChar(g, e)) });
    }
    items.sort((a, b) => a.y - b.y);
    for (const it of items) it.d();
    this.drawBuntings(g);
  },

  /* ---------- lighting ---------- */
  lightCanvas: null,
  collectLights(entities) {
    const L = [];
    const painted = this.usingBackdrop();
    for (const p of this.props) if (p.type === 'lamp' && p.lit) L.push({ x: p.x, y: p.y - 27, r: 52, warm: 1 });
    if (painted) {
      // window glow positions still come from house data even when houses are painted
    }
    for (const b of this.buntings) if (b.lit) {
      const midX = (b.x1 + b.x2) / 2, midY = Math.max(b.y1, b.y2) + 10;
      const N = Math.max(4, Math.floor(Math.hypot(b.x2 - b.x1, b.y2 - b.y1) / 10));
      for (let i = 3; i < N; i += 3) {
        const t2 = i / N, omt = 1 - t2;
        L.push({
          x: omt * omt * b.x1 + 2 * omt * t2 * midX + t2 * t2 * b.x2,
          y: omt * omt * b.y1 + 2 * omt * t2 * midY + t2 * t2 * b.y2 + 3,
          r: 22, warm: 0.7,
        });
      }
    }
    if (this.heartlight && this.heartlight.state === 'alive')
      L.push({ x: this.heartlight.x, y: this.heartlight.y - 16, r: 95, warm: 1.2 });
    for (const h of this.houses) if (!h.dark) {
      const glows = this.HOUSE_GLOW[h.style] || [];
      for (const [gx, gy] of glows)
        L.push({ x: h.tx * T + gx + 3, y: h.ty * T + gy + 3, r: 26, warm: 0.8 });
    }
    for (const e of entities) if (e.lightCarrier && !e.hidden) L.push({ x: e.x + 5, y: e.y - 8, r: 30, warm: 1 });
    for (const tl of this.tempLights) L.push(tl);
    return L;
  },
  drawLighting(g, entities) {
    const dark = this.light.dark;
    if (dark < 0.02) return;
    const { cw, ch } = Screen;
    if (!this.lightCanvas || this.lightCanvas.width !== cw || this.lightCanvas.height !== ch)
      this.lightCanvas = makeCanvas(cw, ch);
    const lc = this.lightCanvas.getContext('2d');
    lc.globalCompositeOperation = 'source-over';
    lc.clearRect(0, 0, cw, ch);
    lc.fillStyle = this.light.color;
    lc.globalAlpha = dark;
    lc.fillRect(0, 0, cw, ch);
    lc.globalAlpha = 1;
    lc.globalCompositeOperation = 'destination-out';
    const lights = this.collectLights(entities);
    for (const l of lights) {
      const [sx, sy] = Camera.worldToScreen(l.x, l.y);
      const r = l.r * Camera.zoom * (1 + Math.sin(time * 8 + l.x) * 0.02);
      if (sx < -r || sx > cw + r || sy < -r || sy > ch + r) continue;
      const gr = lc.createRadialGradient(sx, sy, r * 0.1, sx, sy, r);
      gr.addColorStop(0, 'rgba(0,0,0,.96)');
      gr.addColorStop(0.6, 'rgba(0,0,0,.5)');
      gr.addColorStop(1, 'rgba(0,0,0,0)');
      lc.fillStyle = gr;
      lc.fillRect(sx - r, sy - r, r * 2, r * 2);
    }
    g.drawImage(this.lightCanvas, 0, 0);
    // warm glow pass
    if (this.light.warm) {
      g.save();
      g.globalCompositeOperation = 'lighter';
      for (const l of lights) {
        if (!l.warm) continue;
        const [sx, sy] = Camera.worldToScreen(l.x, l.y);
        const r = l.r * Camera.zoom * 0.8;
        if (sx < -r || sx > cw + r || sy < -r || sy > ch + r) continue;
        const gr = g.createRadialGradient(sx, sy, 1, sx, sy, r);
        gr.addColorStop(0, `rgba(255,180,90,${0.12 * l.warm})`);
        gr.addColorStop(1, 'rgba(255,180,90,0)');
        g.fillStyle = gr;
        g.fillRect(sx - r, sy - r, r * 2, r * 2);
      }
      g.restore();
    }
  },
};
