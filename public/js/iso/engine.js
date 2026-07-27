'use strict';
/* ============================================================
   ISO-PROTO engine — Emberbrook painted-isometric proof of concept.
   0.5m cells on a 64x32 (2:1) diamond. Sub-cell movement with
   cell-grid collision, painter's y-sort with the character
   billboarded into the sort, door transitions, camera follow.
   Standalone: touches nothing of the shipped game.
   ============================================================ */

const TW = 64, TH = 32;          // screen px per cell diamond at native zoom
const VIEW_W = 896;              // logical viewport width -> 14 cells across
// Character height PINNED to the canonical size table: a person is 1.7 m =
// 3.4 cells, and one cell of world height renders at TW/2 = 32 px, so
// CHAR_H = 3.4 * 32 = 108.8 px. (Pre-fix CHAR_H=130 measured 4.06 cells =
// 2.03 m — the "giant against houses" the director reported.) See
// public/assets/iso/specs.json vesper + tools/height_gate.py.
const CHAR_CELLS = 3.4;
const CHAR_H = Math.round(CHAR_CELLS * (TW / 2));   // 109 px
const SPEED = 4.6;               // cells per second
const RADIUS = 0.30;             // character collision radius in cells

const sx = (x, y) => (x - y) * (TW / 2);
const sy = (x, y) => (x + y) * (TH / 2);

let IsoBlocks = {};              // populated from metrics by buildIsoRegistry()

/* ---------------- asset loading ---------------- */
const Images = {};
function loadImage(src) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => rej(new Error('image load failed: ' + src));
    im.src = src;
  });
}

/* De-halo: the registration-mark slicer keys the magenta pad to transparent
   but leaves a faint pink/lavender de-spill ring along the mark's diamond
   boundary — a sticker-edge halo once the sprite sits on painted ground. We
   strip it deterministically at load: within a thin band of the measured mark
   edges (metrics fitSprite corners) zero any pixel carrying the magenta
   signature (both R and B above G — a hue no warm/green/stone prop pixel has),
   so genuine stone/metal/foliage inside the footprint is untouched. Returns a
   canvas usable as a drawImage source. */
const Cleaned = new Set();
function distSeg(px, py, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy;
  if (L2 === 0) return Math.hypot(px - a[0], py - a[1]);
  let t = ((px - a[0]) * dx + (py - a[1]) * dy) / L2;
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  return Math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy));
}
function deHalo(img, fit, band = 3.6, margin = 5) {
  const w = img.width, h = img.height;
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  const g = cv.getContext('2d');
  g.drawImage(img, 0, 0);
  if (!fit) return cv;
  const [T, R, B, L] = fit;
  const edges = [[T, R], [R, B], [B, L], [L, T]];
  const id = g.getImageData(0, 0, w, h), d = id.data;
  for (let p = 0; p < d.length; p += 4) {
    if (d[p + 3] === 0) continue;
    const r = d[p], gr = d[p + 1], b = d[p + 2];
    if (!(b > gr && r > gr && (r - gr) + (b - gr) >= margin)) continue;  // magenta signature
    const x = (p >> 2) % w, y = (p >> 2) / w | 0;
    let dm = Infinity;
    for (const [u, v] of edges) { const dd = distSeg(x, y, u, v); if (dd < dm) dm = dd; }
    if (dm <= band) d[p + 3] = 0;
  }
  g.putImageData(id, 0, 0);
  return cv;
}

/* Vesper sprite frames, sliced from the transparent HD sheet. */
const CharFrames = { down: [], up: [], right: [] };
async function loadCharacter() {
  const img = await loadImage('assets/characters/vesper/sheet.png');
  const CELL = 256;
  const picks = {
    down: [[0, 0], [1, 0], [2, 0], [3, 0]],
    up: [[0, 1], [1, 1], [2, 1], [3, 1]],
    right: [[0, 2], [1, 2], [2, 2], [3, 2], [4, 2], [5, 2]],
  };
  for (const [dir, cells] of Object.entries(picks)) {
    for (const [cx, cy] of cells) {
      const c = document.createElement('canvas');
      c.width = CELL; c.height = CELL;
      const g = c.getContext('2d');
      g.drawImage(img, cx * CELL, cy * CELL, CELL, CELL, 0, 0, CELL, CELL);
      const d = g.getImageData(0, 0, CELL, CELL).data;
      let minX = CELL, minY = CELL, maxX = 0, maxY = 0;
      for (let i = 3; i < d.length; i += 4) {
        if (d[i] > 24) {
          const p = (i - 3) / 4, x = p % CELL, y = (p / CELL) | 0;
          if (x < minX) minX = x; if (x > maxX) maxX = x;
          if (y < minY) minY = y; if (y > maxY) maxY = y;
        }
      }
      const w = maxX - minX + 1, h = maxY - minY + 1;
      const out = document.createElement('canvas');
      out.width = w; out.height = h;
      out.getContext('2d').drawImage(c, minX, minY, w, h, 0, 0, w, h);
      CharFrames[dir].push(out);
    }
  }
}

/* ---------------- scene state ---------------- */
const G = {
  scene: null, sceneName: null,
  userZoom: 0.8,                    // camera zoom (1 = old 14-cells-across; <1 zooms out); -/= adjust
  solid: null, W: 0, H: 0,
  grounds: [], flats: [], backdrops: [], props: [],
  triggers: [],
  char: { x: 4, y: 4, vx: 0, vy: 0, dir: 'down', frame: 0, ft: 0, moving: false },
  cam: { x: 0, y: 0, init: false },
  fade: { a: 0, mode: 'in', t: 1, next: null },   // mode in|out|idle
  armed: false,          // door triggers armed only after leaving them
  errors: [],
};

function blocked(x, y) {
  if (x < 0.15 || y < 0.15 || x > G.W - 0.15 || y > G.H - 0.15) return true;
  const i = x | 0, j = y | 0;
  return !!G.solid[j * G.W + i];
}
function charBlocked(x, y) {
  return blocked(x - RADIUS, y - RADIUS) || blocked(x + RADIUS, y - RADIUS) ||
         blocked(x - RADIUS, y + RADIUS) || blocked(x + RADIUS, y + RADIUS);
}

async function loadScene(name, spawn) {
  const scene = await (await fetch('assets/iso/scenes/' + name + '.json')).json();
  const [W, H] = scene.size;
  G.scene = scene; G.sceneName = name; G.W = W; G.H = H;
  G.solid = new Uint8Array(W * H);
  G.grounds = []; G.flats = []; G.backdrops = []; G.props = [];
  G.triggers = scene.triggers || [];

  // ground supertiles from the charmap (2-cell pitch)
  const pitch = scene.groundPitch || 2;
  (scene.ground || []).forEach((row, jr) => {
    [...row].forEach((ch, ir) => {
      const name2 = scene.tiles[ch];
      if (!name2) return;
      G.grounds.push({ name: name2, i: ir * pitch, j: jr * pitch });
    });
  });

  // placed blocks (all painted pieces render through the one anchor path;
  // ground materials come from the charmap, never the block list)
  const needed = new Map();                 // load key -> url
  for (const g of G.grounds) {
    const gd = IsoBlocks[g.name];
    if (gd.tex) needed.set(gd.tex, 'assets/iso/blocks/' + gd.tex + '.png');
    else needed.set(g.name, gd.img || 'assets/iso/blocks/' + g.name + '.png');
  }
  for (const [bname, i, j, opts] of scene.blocks || []) {
    const def = IsoBlocks[bname];
    if (!def) { console.error('unknown block', bname); G.errors.push('unknown block ' + bname); continue; }
    needed.set(bname, def.img || 'assets/iso/blocks/' + bname + '.png');
    const p = { name: bname, i, j, def, opts: opts || {} };
    if (def.kind === 'flat') G.flats.push(p);
    else G.props.push(p);                    // free + building both sort in
    if (def.kind === 'flat') continue;
    const cells = def.walk
      ? (def.solid || []).map(([a, b]) => [i + a, j + b])   // walkable: only explicit solids
      : allFootCells(def, i, j);                            // else block the footprint
    for (const [ci, cj] of cells) {
      if (ci >= 0 && cj >= 0 && ci < W && cj < H) G.solid[cj * W + ci] = 1;
    }
  }

  await Promise.all([...needed].map(async ([n, url]) => {
    if (!Images[n]) Images[n] = await loadImage(url);
  }));
  // strip keyed-mark halo rings once per painted block that carries a fit
  for (const [bname] of (scene.blocks || []).map(b => [b[0]])) {
    const def = IsoBlocks[bname];
    if (def && def.fit && !Cleaned.has(bname)) {
      Images[bname] = deHalo(Images[bname], def.fit);
      Cleaned.add(bname);
    }
  }

  // expand building-anchored transition triggers into absolute doorstep cells
  for (const tr of G.triggers) {
    if (tr.cells) continue;
    if (tr.block) {
      const b = (scene.blocks || []).find(bl => bl[0] === tr.block);
      const def = b && IsoBlocks[tr.block];
      if (b && def && def.doorstep) {
        tr.cells = def.doorstep.map(([a, c]) => [b[1] + a, b[2] + c]);
      }
    }
    if (!tr.cells) tr.cells = [];
  }

  // sort static layers once
  G.grounds.sort((a, b) => (a.i + a.j) - (b.i + b.j));
  G.props.sort((a, b) => sortKey(a) - sortKey(b));
  bakeGround();

  const [sxp, syp] = spawn || scene.spawn;
  G.char.x = sxp; G.char.y = syp;
  G.cam.init = false;
  G.armed = false;
}

function allFootCells(def, i, j) {
  const cells = [];
  if (def.solid) {
    for (const [a, b] of def.solid) cells.push([i + a, j + b]);
  } else {
    for (let b = 0; b < def.foot[1]; b++)
      for (let a = 0; a < def.foot[0]; a++) cells.push([i + a, j + b]);
  }
  return cells;
}

function sortKey(p) {
  if (p.def.keyOverride != null) return p.def.keyOverride;
  return p.i + p.j + (p.def.foot[0] + p.def.foot[1]) / 2;
}

/* ---------------- flat ground: texture-cut diamonds, baked once ----------------
   Ground materials are large flat painted textures (pre-squashed 2:1).
   At load we bake the whole floor to an offscreen canvas: every 1x1 cell
   clips a 64x32 diamond and pattern-fills from its material texture at the
   cell's own screen position (continuous surface) plus a small deterministic
   jitter so texture repetition never bands. No baked edges -> no terracing. */
function cellJitter(i, j) {
  let h = (i * 73856093) ^ (j * 19349663);
  h = (h ^ (h >>> 13)) >>> 0;
  return [(h % 13) - 6, ((h >>> 4) % 9) - 4];
}

function bakeGround() {
  G.groundBake = null;
  if (!G.grounds.length) return;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const g of G.grounds) {
    const def = IsoBlocks[g.name];
    const [fw, fh] = def.foot;
    // corners of the supertile diamond
    minX = Math.min(minX, sx(g.i, g.j + fh));
    maxX = Math.max(maxX, sx(g.i + fw, g.j));
    minY = Math.min(minY, sy(g.i, g.j));
    maxY = Math.max(maxY, sy(g.i + fw, g.j + fh));
  }
  const bw = Math.ceil(maxX - minX) + 4, bh = Math.ceil(maxY - minY) + 4;
  const cv = document.createElement('canvas');
  cv.width = bw; cv.height = bh;
  const g2 = cv.getContext('2d');
  const ox = -minX + 2, oy = -minY + 2;
  const pats = {};

  // per-cell material map (for boundary detection between materials)
  const mat = new Map();            // "i,j" -> tex name
  for (const g of G.grounds) {
    const def = IsoBlocks[g.name];
    if (!def.tex) continue;
    for (let b = 0; b < def.foot[1]; b++)
      for (let a = 0; a < def.foot[0]; a++)
        mat.set((g.i + a) + ',' + (g.j + b), def.tex);
  }

  function fillCell(ci, cj, tex, soft) {
    const im = Images[tex];
    if (!im) return;
    if (!pats[tex]) pats[tex] = g2.createPattern(im, 'repeat');
    const cx = sx(ci + 0.5, cj + 0.5) + ox, cy = sy(ci + 0.5, cj + 0.5) + oy;
    const [jx, jy] = cellJitter(ci, cj);
    if (!soft) {
      g2.save();
      g2.beginPath();                     // diamond, slightly outset to kill seams
      g2.moveTo(cx, cy - TH / 2 - 0.8);
      g2.lineTo(cx + TW / 2 + 1.4, cy);
      g2.lineTo(cx, cy + TH / 2 + 0.8);
      g2.lineTo(cx - TW / 2 - 1.4, cy);
      g2.closePath();
      g2.clip();
      g2.translate(jx, jy);               // shifts pattern space -> jittered sample
      g2.fillStyle = pats[tex];
      g2.fillRect(cx - TW / 2 - 4 - jx, cy - TH / 2 - 4 - jy, TW + 8, TH + 8);
      g2.restore();
      return;
    }
    // soft: blurred-edge diamond (slightly enlarged) composited via temp canvas,
    // pattern phase kept identical to the hard fill
    const PAD = 16, tw2 = TW + PAD * 2, th2 = TH + PAD * 2;
    const t = document.createElement('canvas');
    t.width = tw2; t.height = th2;
    const tc = t.getContext('2d');
    tc.filter = 'blur(4px)';
    tc.fillStyle = '#fff';
    tc.beginPath();
    tc.moveTo(tw2 / 2, PAD - 5);
    tc.lineTo(tw2 - PAD + 7, th2 / 2);
    tc.lineTo(tw2 / 2, th2 - PAD + 5);
    tc.lineTo(PAD - 7, th2 / 2);
    tc.closePath();
    tc.fill();
    tc.filter = 'none';
    tc.globalCompositeOperation = 'source-in';
    const bx = cx - tw2 / 2, by = cy - th2 / 2;   // temp origin in bake coords
    tc.translate(jx - bx, jy - by);
    tc.fillStyle = pats[tex];
    tc.fillRect(bx - jx, by - jy, tw2, th2);
    g2.drawImage(t, bx, by);
  }

  // pass 1: every textured cell, hard diamonds
  for (const [key, tex] of mat) {
    const [ci, cj] = key.split(',').map(Number);
    fillCell(ci, cj, tex, false);
  }
  // pass 2: cells bordering a different material get a soft-edged redraw,
  // blending over their neighbors -> no hard zigzag material boundaries
  for (const [key, tex] of mat) {
    const [ci, cj] = key.split(',').map(Number);
    const boundary = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([a, b]) => {
      const n = mat.get((ci + a) + ',' + (cj + b));
      return n && n !== tex;
    });
    if (boundary) fillCell(ci, cj, tex, true);
  }
  // legacy image supertiles (e.g. f-plank), drawn on top
  for (const g of G.grounds) {
    const def = IsoBlocks[g.name];
    if (def.tex) continue;
    const im = Images[g.name];
    if (im) {
      const s = def.s, w = im.width * s, h = im.height * s;
      g2.drawImage(im, sx(g.i, g.j) - w / 2 + ox, sy(g.i, g.j) - 1 + oy, w, h);
    }
  }
  G.groundBake = { cv, x: minX - 2, y: minY - 2 };
}

/* Soft programmatic contact shadow under every sorted prop: one ellipse per
   shadow group (default: bbox of solid cells, else the full footprint),
   drawn as a ground decal pass before the props. Restores "resting on the
   ground" contact now that baked dirt skirts are gone. */
function drawContactShadow(ctx, p) {
  const def = p.def;
  if (def.foot[0] < 1 || def.foot[1] < 1 || def.noShadow) return;
  let groups;
  if (def.shadowCells) groups = def.shadowCells;
  else if (def.solid && def.solid.length) {
    let i0 = Infinity, j0 = Infinity, i1 = -Infinity, j1 = -Infinity;
    for (const [a, b] of def.solid) {
      i0 = Math.min(i0, a); i1 = Math.max(i1, a);
      j0 = Math.min(j0, b); j1 = Math.max(j1, b);
    }
    groups = [[[i0, j0], [i1, j1]]];
  } else groups = [[[0, 0], [def.foot[0] - 1, def.foot[1] - 1]]];
  for (const [[i0, j0], [i1, j1]] of groups) {
    const wc = i1 - i0 + 1, hc = j1 - j0 + 1;
    const cx = p.i + (i0 + i1 + 1) / 2, cy = p.j + (j0 + j1 + 1) / 2;
    const px = sx(cx, cy), py = sy(cx, cy);
    const rx = (wc + hc) * (TW / 4) * 0.78;
    ctx.save();
    ctx.translate(px, py);
    ctx.scale(1, 0.5);
    const gr = ctx.createRadialGradient(0, 0, rx * 0.15, 0, 0, rx);
    gr.addColorStop(0, 'rgba(22,11,18,0.28)');
    gr.addColorStop(0.7, 'rgba(22,11,18,0.18)');
    gr.addColorStop(1, 'rgba(22,11,18,0)');
    ctx.fillStyle = gr;
    ctx.beginPath();
    ctx.arc(0, 0, rx, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

/* ---------------- drawing ---------------- */
function drawBlock(ctx, p) {
  const im = Images[p.name];
  if (!im) return;
  const def = p.def, s = def.s;
  const w = im.width * s, h = im.height * s;
  const dy = ((def.dy || 0) + (p.opts.dy || 0)) * s;
  const dx = (p.opts.dx || 0) * s;
  let px, py;
  if (def.kind === 'ground' || def.kind === 'flat') {
    // image top point at the region's back corner
    px = sx(p.i, p.j) - w / 2;
    py = sy(p.i, p.j) - 1;      // 1px overlap to hide seams
  } else if (def.kind === 'slab' || (def.kind === 'backdrop' && def.anchor !== 'free')) {
    // image bottom tip at the region's front corner
    const fx = p.i + def.foot[0], fy = p.j + def.foot[1];
    px = sx(fx, fy) - w / 2;
    py = sy(fx, fy) - h;
  } else {
    // free: anchor pixel (def.ax/ay, pre-scale) at footprint center; when no
    // anchor is set, image bottom-center at footprint center
    const cx = p.i + def.foot[0] / 2, cy = p.j + def.foot[1] / 2;
    if (def.ax != null) {
      px = sx(cx, cy) - def.ax * s;
      py = sy(cx, cy) - def.ay * s;
    } else {
      px = sx(cx, cy) - w / 2;
      py = sy(cx, cy) - h;
    }
  }
  ctx.drawImage(im, px + dx, py + dy, w, h);
}

function drawCharShadow(ctx) {
  const c = G.char;
  const px = sx(c.x, c.y), py = sy(c.x, c.y);
  const r = TW * 0.26;
  ctx.save();
  ctx.translate(px, py + 2);
  ctx.scale(1, 0.5);
  const gr = ctx.createRadialGradient(0, 0, r * 0.18, 0, 0, r);
  gr.addColorStop(0, 'rgba(18,9,15,0.36)');
  gr.addColorStop(0.7, 'rgba(18,9,15,0.22)');
  gr.addColorStop(1, 'rgba(18,9,15,0)');
  ctx.fillStyle = gr;
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawChar(ctx) {
  const c = G.char;
  const frames = CharFrames[c.dir === 'left' ? 'right' : c.dir];
  if (!frames || !frames.length) return;
  const f = frames[c.frame % frames.length];
  const s = CHAR_H / f.height;
  const w = f.width * s;
  const px = sx(c.x, c.y), py = sy(c.x, c.y);
  ctx.save();
  if (c.dir === 'left') {
    ctx.translate(px, 0); ctx.scale(-1, 1);
    ctx.drawImage(f, -w / 2, py - CHAR_H + 4, w, CHAR_H);
  } else {
    ctx.drawImage(f, px - w / 2, py - CHAR_H + 4, w, CHAR_H);
  }
  ctx.restore();
}

/* ---------------- debug overlay (G toggles; default OFF, zero effect off) ----
   Mirrors the main game's KeyG walkability overlay. World-space pass drawn
   after the sorted props: cell walkability fills, grid lines, block
   footprints, base anchors, sort keys, trigger cells, character cell. */
let DBG = false;
addEventListener('keydown', e => {
  if (e.code === 'KeyG' && !e.repeat) DBG = !DBG;
  if (e.code === 'Minus' || e.code === 'Equal') {
    const step = e.code === 'Minus' ? -0.05 : 0.05;
    G.userZoom = Math.round(Math.max(0.5, Math.min(1.4, (G.userZoom || 1) + step)) * 100) / 100;
  }
});

function dbgAnchor(p) {
  const def = p.def;
  if (def.kind === 'slab' || (def.kind === 'backdrop' && def.anchor !== 'free'))
    return [p.i + def.foot[0], p.j + def.foot[1]];
  return [p.i + def.foot[0] / 2, p.j + def.foot[1] / 2];
}

function dbgDiamond(ctx, i0, j0, i1, j1) {
  ctx.beginPath();
  ctx.moveTo(sx(i0, j0), sy(i0, j0));
  ctx.lineTo(sx(i1, j0), sy(i1, j0));
  ctx.lineTo(sx(i1, j1), sy(i1, j1));
  ctx.lineTo(sx(i0, j1), sy(i0, j1));
  ctx.closePath();
}

function drawDebugWorld(ctx) {
  // per-cell walkability: red = blocked, green = walkable
  for (let j = 0; j < G.H; j++) {
    for (let i = 0; i < G.W; i++) {
      dbgDiamond(ctx, i, j, i + 1, j + 1);
      ctx.fillStyle = G.solid[j * G.W + i] ? 'rgba(224,64,48,0.34)' : 'rgba(88,200,112,0.12)';
      ctx.fill();
    }
  }
  // grid lines
  ctx.strokeStyle = 'rgba(240,230,210,0.30)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i <= G.W; i++) { ctx.moveTo(sx(i, 0), sy(i, 0)); ctx.lineTo(sx(i, G.H), sy(i, G.H)); }
  for (let j = 0; j <= G.H; j++) { ctx.moveTo(sx(0, j), sy(0, j)); ctx.lineTo(sx(G.W, j), sy(G.W, j)); }
  ctx.stroke();
  // door trigger cells
  ctx.fillStyle = 'rgba(80,200,255,0.35)';
  for (const tr of G.triggers) {
    for (const [a, b] of tr.cells) { dbgDiamond(ctx, a, b, a + 1, b + 1); ctx.fill(); }
  }
  // footprints + anchors + sort keys
  ctx.font = 'bold 13px system-ui, sans-serif';
  ctx.textAlign = 'center';
  for (const list of [G.backdrops, G.props]) {
    const isProp = list === G.props;
    for (const p of list) {
      const [fw, fh] = p.def.foot;
      if (fw > 0 && fh > 0) {
        dbgDiamond(ctx, p.i, p.j, p.i + fw, p.j + fh);
        ctx.strokeStyle = isProp ? 'rgba(255,177,78,0.9)' : 'rgba(180,138,255,0.9)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      const [ai, aj] = dbgAnchor(p);
      const ax2 = sx(ai, aj), ay2 = sy(ai, aj);
      ctx.fillStyle = '#ffd866';
      ctx.beginPath(); ctx.arc(ax2, ay2, 3.5, 0, Math.PI * 2); ctx.fill();
      if (isProp) {
        ctx.lineWidth = 3;
        ctx.strokeStyle = 'rgba(0,0,0,0.85)';
        ctx.strokeText(sortKey(p).toFixed(1), ax2, ay2 - 8);
        ctx.fillStyle = '#fff';
        ctx.fillText(sortKey(p).toFixed(1), ax2, ay2 - 8);
      }
    }
  }
  // character cell + position
  const ci = G.char.x | 0, cj = G.char.y | 0;
  dbgDiamond(ctx, ci, cj, ci + 1, cj + 1);
  ctx.strokeStyle = 'rgba(80,220,255,0.95)';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.textAlign = 'left';
}

function drawDebugHud(ctx, cw) {
  ctx.font = '13px system-ui, sans-serif';
  ctx.textAlign = 'left';
  const msg = 'DEBUG (G)  ' + G.sceneName + '  char ' + G.char.x.toFixed(2) + ',' + G.char.y.toFixed(2) +
              '  cell ' + (G.char.x | 0) + ',' + (G.char.y | 0) +
              '  sort ' + (G.char.x + G.char.y).toFixed(2);
  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  ctx.fillRect(8, 8, ctx.measureText(msg).width + 16, 24);
  ctx.fillStyle = '#ffe9b0';
  ctx.fillText(msg, 16, 25);
}

/* ---------------- main loop ---------------- */
const keys = {};
addEventListener('keydown', e => {
  keys[e.key.toLowerCase()] = true;
  if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(e.key.toLowerCase())) e.preventDefault();
});
addEventListener('keyup', e => { keys[e.key.toLowerCase()] = false; });

let canvas, ctx, lastT = 0;

function tick(t) {
  const dt = Math.min(0.05, (t - lastT) / 1000 || 0.016);
  lastT = t;
  update(dt);
  render();
  requestAnimationFrame(tick);
}

function update(dt) {
  const c = G.char;
  if (G.fade.mode === 'out') {
    G.fade.t += dt / 0.35;
    if (G.fade.t >= 1) {
      G.fade.t = 1;
      const nx = G.fade.next; G.fade.next = null;
      loadScene(nx.to, nx.spawn).then(() => { G.fade.mode = 'in'; G.fade.t = 0; });
      G.fade.mode = 'hold';
    }
    return;
  }
  if (G.fade.mode === 'hold') return;
  if (G.fade.mode === 'in') {
    G.fade.t += dt / 0.35;
    if (G.fade.t >= 1) { G.fade.t = 1; G.fade.mode = 'idle'; }
  }

  // input: screen-space arrows -> world axes (x: down-right, y: down-left)
  let ix = 0, iy = 0;
  if (keys['arrowright'] || keys['d']) ix += 1;
  if (keys['arrowleft'] || keys['a']) ix -= 1;
  if (keys['arrowdown'] || keys['s']) iy += 1;
  if (keys['arrowup'] || keys['w']) iy -= 1;
  let vx = (ix + iy * 2) / 2, vy = (iy * 2 - ix) / 2;   // screen->world
  const m = Math.hypot(vx, vy);
  c.moving = m > 0.01;
  if (c.moving) {
    vx = vx / m * SPEED; vy = vy / m * SPEED;
    // axis-separated moves with slide
    let nx = c.x + vx * dt;
    if (!charBlocked(nx, c.y)) c.x = nx;
    let ny = c.y + vy * dt;
    if (!charBlocked(c.x, ny)) c.y = ny;
    // facing from screen velocity
    const sdx = vx - vy, sdy = (vx + vy) / 2;
    if (Math.abs(sdx) > Math.abs(sdy) * 1.15) c.dir = sdx > 0 ? 'right' : 'left';
    else c.dir = sdy > 0 ? 'down' : 'up';
    c.ft += dt;
    if (c.ft > 0.12) { c.ft = 0; c.frame++; }
  } else {
    c.frame = 0; c.ft = 0;
  }

  // door triggers
  const ci = c.x | 0, cj = c.y | 0;
  let onTrigger = null;
  for (const tr of G.triggers) {
    if (tr.cells.some(([a, b]) => a === ci && b === cj)) { onTrigger = tr; break; }
  }
  if (!onTrigger) G.armed = true;
  else if (G.armed && G.fade.mode === 'idle') {
    G.fade.mode = 'out'; G.fade.t = 0;
    G.fade.next = { to: onTrigger.to, spawn: onTrigger.spawn };
  }
}

function render() {
  if (!ctx || !G.scene) return;
  const cw = canvas.width, chh = canvas.height;
  const zoom = (cw / VIEW_W) * (G.userZoom || 1);
  const viewH = chh / zoom;

  // camera follow + clamp
  const c = G.char;
  const tx = sx(c.x, c.y), ty = sy(c.x, c.y) - CHAR_H * 0.35;
  if (!G.cam.init) { G.cam.x = tx; G.cam.y = ty; G.cam.init = true; }
  G.cam.x += (tx - G.cam.x) * 0.12;
  G.cam.y += (ty - G.cam.y) * 0.12;
  const effVW = VIEW_W / (G.userZoom || 1);
  const minX = sx(0, G.H) + TW * 0.2, maxX = sx(G.W, 0) - TW * 0.2;
  const minY = -240, maxY = sy(G.W, G.H) + 40;
  let camX = G.cam.x, camY = G.cam.y;
  if (maxX - minX > effVW) camX = Math.max(minX + effVW / 2, Math.min(maxX - effVW / 2, camX));
  else camX = (minX + maxX) / 2;
  if (maxY - minY > viewH) camY = Math.max(minY + viewH / 2, Math.min(maxY - viewH / 2, camY));
  else camY = (minY + maxY) / 2;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = G.scene.bg || '#161014';
  ctx.fillRect(0, 0, cw, chh);
  ctx.setTransform(zoom, 0, 0, zoom, cw / 2 - camX * zoom, chh / 2 - camY * zoom);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  if (G.groundBake) ctx.drawImage(G.groundBake.cv, G.groundBake.x, G.groundBake.y);
  for (const p of G.flats) drawBlock(ctx, p);
  for (const p of G.backdrops) drawBlock(ctx, p);
  for (const p of G.props) drawContactShadow(ctx, p);   // ground-decal shadow pass
  drawCharShadow(ctx);                                   // ground the character too

  // painter's sort with the character billboarded in
  const ck = c.x + c.y;
  let drawn = false;
  for (const p of G.props) {
    if (!drawn && ck < sortKey(p)) { drawChar(ctx); drawn = true; }
    drawBlock(ctx, p);
  }
  if (!drawn) drawChar(ctx);

  if (DBG) drawDebugWorld(ctx);

  // dusk grade (screen space, deterministic): warm top wash over a cool
  // floor, then a soft radial vignette to seat the scene into its frame.
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  let gr = ctx.createLinearGradient(0, 0, 0, chh);
  gr.addColorStop(0, 'rgba(255,178,102,0.13)');
  gr.addColorStop(0.52, 'rgba(255,190,120,0.02)');
  gr.addColorStop(1, 'rgba(26,34,62,0.17)');
  ctx.fillStyle = gr;
  ctx.fillRect(0, 0, cw, chh);
  const vr = Math.hypot(cw, chh) * 0.62;
  let vg = ctx.createRadialGradient(cw * 0.5, chh * 0.46, vr * 0.34, cw * 0.5, chh * 0.55, vr);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(0.72, 'rgba(10,7,12,0)');
  vg.addColorStop(1, 'rgba(8,5,12,0.34)');
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, cw, chh);

  // fade overlay
  if (G.fade.mode !== 'idle') {
    const a = G.fade.mode === 'in' ? 1 - G.fade.t : (G.fade.mode === 'out' ? G.fade.t : 1);
    ctx.fillStyle = `rgba(8,5,8,${a.toFixed(3)})`;
    ctx.fillRect(0, 0, cw, chh);
  }

  if (DBG) drawDebugHud(ctx, cw);
}

/* ---------------- boot ---------------- */
async function boot() {
  canvas = document.getElementById('iso');
  ctx = canvas.getContext('2d');
  const fit = () => {
    const dpr = Math.min(2, devicePixelRatio || 1);
    canvas.width = innerWidth * dpr; canvas.height = innerHeight * dpr;
    canvas.style.width = innerWidth + 'px'; canvas.style.height = innerHeight + 'px';
  };
  fit();
  addEventListener('resize', fit);
  const reg = await buildIsoRegistry();
  IsoBlocks = reg.blocks;
  window.IsoBlocks = IsoBlocks;
  G.interior = reg.interior;
  await loadCharacter();
  await loadScene('square');
  G.fade.mode = 'in'; G.fade.t = 0;
  requestAnimationFrame(tick);
}
boot().catch(e => { console.error(e); });

// tiny debug hooks for automated verification
window.__iso = G;
window.__isoKeys = keys;
window.__isoTeleport = (x, y) => { G.char.x = x; G.char.y = y; };
window.__isoScene = (n, spawn) => loadScene(n, spawn);   // verification hook
window.__isoProbe = (x, y) => charBlocked(x, y);
window.__isoCell = (i, j) => !!(G.solid && G.solid[j * G.W + i]);
