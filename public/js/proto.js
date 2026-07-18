'use strict';
/* ============================================================
   SCENE PROTOTYPE — painted backdrops + walkable polygons +
   a generated sprite walking around. Two scenes:
     square   — layout-locked workflow (blockout → painting)
     interior — free-form workflow (painting → walkable mask)
   ============================================================ */

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let cw = 0, ch = 0, dpr = 1;
function resize() {
  dpr = Math.min(window.devicePixelRatio || 1, 2);
  cw = innerWidth; ch = innerHeight;
  canvas.width = cw * dpr; canvas.height = ch * dpr;
  canvas.style.width = cw + 'px'; canvas.style.height = ch + 'px';
}
addEventListener('resize', resize);
resize();

/* ---------- scenes (coordinates in image pixels) ---------- */
const SCENES = {
  square: {
    img: 'assets/square-scene.png',
    // how much of the image the viewport shows vertically (smaller = more zoomed)
    viewH: 560,
    charH: 95,
    speed: 187,
    spawn: [670, 600],
    walk: [[295, 235], [1055, 235], [1300, 430], [1300, 720], [1040, 762], [330, 762], [80, 620], [80, 430]],
    blocked: [
      { kind: 'circle', x: 668, y: 500, r: 78 },              // heartlight pedestal
      { kind: 'rect', x: 530, y: 210, w: 250, h: 165 },       // stall upper-center
      { kind: 'rect', x: 275, y: 360, w: 150, h: 185 },       // stall left
      { kind: 'rect', x: 945, y: 355, w: 150, h: 180 },       // stall right
      { kind: 'rect', x: 455, y: 625, w: 250, h: 145 },       // stall bottom-left
      { kind: 'rect', x: 730, y: 615, w: 215, h: 155 },       // stall bottom-right
      { kind: 'rect', x: 195, y: 200, w: 280, h: 175 },       // bakery
      { kind: 'rect', x: 860, y: 90, w: 320, h: 200 },        // elder hall
      { kind: 'rect', x: 1020, y: 500, w: 330, h: 220 },      // thatched cottage
      { kind: 'circle', x: 250, y: 470, r: 16 },              // lamps
      { kind: 'circle', x: 765, y: 330, r: 14 },
      { kind: 'circle', x: 1095, y: 460, r: 16 },
      { kind: 'rect', x: 165, y: 460, w: 45, h: 105 },        // notice board
      { kind: 'rect', x: 195, y: 570, w: 90, h: 80 },         // crates/barrels
      { kind: 'rect', x: 320, y: 520, w: 60, h: 60 },         // barrel by left stall
    ],
  },
  interior: {
    img: 'assets/cottage-interior-sample.png',
    viewH: 700,
    charH: 165,
    speed: 286,
    spawn: [880, 590],
    walk: [[430, 470], [620, 380], [900, 430], [1080, 500], [1050, 620], [780, 740], [520, 720], [400, 610]],
    blocked: [
      { kind: 'rect', x: 600, y: 240, w: 310, h: 210 },       // bed
      { kind: 'rect', x: 505, y: 470, w: 185, h: 145 },       // table + chair
      { kind: 'rect', x: 920, y: 250, w: 150, h: 240 },       // shelves right
      { kind: 'rect', x: 390, y: 230, w: 210, h: 230 },       // hearth + wood pile
    ],
  },
};

let sceneKey = 'square';
let scene = SCENES[sceneKey];
const cam = { x: 0, y: 0, leadX: 0, leadY: 0 };
const images = {};
for (const [k, s] of Object.entries(SCENES)) {
  images[k] = new Image();
  images[k].src = s.img;
}

/* ---------- June sprite (sliced from the generated sheet) ---------- */
const SHEET = new Image();
SHEET.src = 'assets/sprite-june-chibi.png';
// the sheet's down/up cells are near-duplicates (no real walk poses), so we
// use one frame + procedural bob/sway; the side rows have two true strides
const PICKS = {
  down: [[0, 0]],
  up:   [[1, 0]],
  left: [[1, 2], [2, 2]],   // both from the same (left-facing) row!
};
// per-scene sprite grading — multiplies the sprite toward the scene's light
const TINTS = { square: '#e2a97e', interior: '#f2c091' };
const graded = {};
const frames = { down: [], up: [], left: [], right: [] };
SHEET.onload = () => {
  const CELL = 256;
  const key = (cx, cy) => {
    const c = document.createElement('canvas');
    c.width = CELL; c.height = CELL;
    const g = c.getContext('2d');
    g.drawImage(SHEET, cx * CELL, cy * CELL, CELL, CELL, 0, 0, CELL, CELL);
    const d = g.getImageData(0, 0, CELL, CELL), px = d.data;
    let minX = CELL, minY = CELL, maxX = 0, maxY = 0;
    for (let i = 0; i < px.length; i += 4) {
      const r = px[i], gg = px[i + 1], b = px[i + 2];
      const rg = r - gg, bg = b - gg;                       // magenta-ness
      if (rg > 90 && bg > 60) { px[i + 3] = 0; continue; }  // solid key color
      if (rg > 50 && bg > 32) {
        // fringe pixel: soften alpha and despill the magenta cast
        const t = Math.min(1, ((rg + bg) - 82) / 60);
        px[i + 3] = Math.round(255 * (1 - t * 0.85));
        px[i] = Math.round(gg + rg * 0.35);
        px[i + 2] = Math.round(gg + bg * 0.35);
      }
      const x = (i / 4) % CELL, y = Math.floor(i / 4 / CELL);
      if (x < minX) minX = x; if (x > maxX) maxX = x;
      if (y < minY) minY = y; if (y > maxY) maxY = y;
    }
    // 1px alpha feather to soften the cut edge
    const a0 = new Uint8ClampedArray(px.length / 4);
    for (let i = 0; i < a0.length; i++) a0[i] = px[i * 4 + 3];
    for (let y = 1; y < CELL - 1; y++) for (let x = 1; x < CELL - 1; x++) {
      const i = y * CELL + x;
      const avg = (a0[i] * 4 + a0[i - 1] + a0[i + 1] + a0[i - CELL] + a0[i + CELL]) / 8;
      if (Math.abs(avg - a0[i]) > 8) px[i * 4 + 3] = avg;
    }
    g.putImageData(d, 0, 0);
    const w = maxX - minX + 1, h = maxY - minY + 1;
    const out = document.createElement('canvas');
    out.width = 160; out.height = 230;
    out.getContext('2d').drawImage(c, minX, minY, w, h, (160 - w) / 2, 230 - h, w, h);
    return out;
  };
  for (const [dir, cells] of Object.entries(PICKS)) frames[dir] = cells.map(([cx, cy]) => key(cx, cy));
  frames.right = frames.left.map(c => {
    const m = document.createElement('canvas');
    m.width = c.width; m.height = c.height;
    const g = m.getContext('2d');
    g.translate(c.width, 0); g.scale(-1, 1); g.drawImage(c, 0, 0);
    return m;
  });
  // pre-grade every frame for each scene's light
  const tinted = (src, color) => {
    const c = document.createElement('canvas');
    c.width = src.width; c.height = src.height;
    const g = c.getContext('2d');
    g.drawImage(src, 0, 0);
    g.globalCompositeOperation = 'multiply';
    g.fillStyle = color; g.fillRect(0, 0, c.width, c.height);
    g.globalCompositeOperation = 'destination-in';
    g.drawImage(src, 0, 0);
    return c;
  };
  for (const [sk, tint] of Object.entries(TINTS)) {
    graded[sk] = {};
    for (const d of ['down', 'up', 'left', 'right']) graded[sk][d] = frames[d].map(f => tinted(f, tint));
  }
};

/* ---------- player ---------- */
const player = { x: 0, y: 0, dir: 'down', animT: 0, moving: false };
function enterScene(k) {
  sceneKey = k; scene = SCENES[k];
  player.x = scene.spawn[0]; player.y = scene.spawn[1];
  cam.x = player.x; cam.y = player.y; cam.leadX = 0; cam.leadY = 0;
}
enterScene('square');

/* ---------- input ---------- */
const keys = {};
let showMask = false;
addEventListener('keydown', (e) => {
  if (e.code === 'Tab') { e.preventDefault(); enterScene(sceneKey === 'square' ? 'interior' : 'square'); }
  if (e.code === 'KeyG') showMask = !showMask;
  keys[e.code] = true;
});
addEventListener('keyup', (e) => { keys[e.code] = false; });

/* ---------- collision ---------- */
function inPoly(pts, x, y) {
  let inside = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
function walkable(x, y) {
  if (!inPoly(scene.walk, x, y)) return false;
  for (const b of scene.blocked) {
    if (b.kind === 'rect' && x > b.x && x < b.x + b.w && y > b.y && y < b.y + b.h) return false;
    if (b.kind === 'circle' && Math.hypot(x - b.x, y - b.y) < b.r) return false;
  }
  return true;
}

/* ---------- loop ---------- */
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;

  let vx = (keys.KeyD || keys.ArrowRight ? 1 : 0) - (keys.KeyA || keys.ArrowLeft ? 1 : 0);
  let vy = (keys.KeyS || keys.ArrowDown ? 1 : 0) - (keys.KeyW || keys.ArrowUp ? 1 : 0);
  const len = Math.hypot(vx, vy);
  player.moving = len > 0;
  if (len > 0) {
    vx /= len; vy /= len;
    const nx = player.x + vx * scene.speed * dt;
    const ny = player.y + vy * scene.speed * dt;
    if (walkable(nx, player.y)) player.x = nx;
    if (walkable(player.x, ny)) player.y = ny;
    player.dir = Math.abs(vx) > Math.abs(vy) ? (vx > 0 ? 'right' : 'left') : (vy > 0 ? 'down' : 'up');
    player.animT += dt;
  }

  // smoothed camera with a gentle look-ahead in the walking direction
  const lead = 42;
  cam.leadX += ((len > 0 ? vx * lead : 0) - cam.leadX) * Math.min(1, dt * 2);
  cam.leadY += ((len > 0 ? vy * lead : 0) - cam.leadY) * Math.min(1, dt * 2);
  const k = Math.min(1, dt * 3.2);
  cam.x += (player.x + cam.leadX - cam.x) * k;
  cam.y += (player.y + cam.leadY - cam.y) * k;

  render();
  requestAnimationFrame(frame);
}

function render() {
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#0d0a08';
  ctx.fillRect(0, 0, cw, ch);
  const img = images[sceneKey];
  if (!img.complete || !img.naturalWidth) return;

  const Z = ch / scene.viewH;
  const viewW = cw / Z;
  let camX = Math.max(viewW / 2, Math.min(img.naturalWidth - viewW / 2, cam.x));
  let camY = Math.max(scene.viewH / 2, Math.min(img.naturalHeight - scene.viewH / 2, cam.y));
  if (img.naturalWidth < viewW) camX = img.naturalWidth / 2;
  if (img.naturalHeight < scene.viewH) camY = img.naturalHeight / 2;

  ctx.save();
  ctx.translate(cw / 2, ch / 2);
  ctx.scale(Z, Z);
  ctx.translate(-camX, -camY);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(img, 0, 0);

  // walkable debug overlay
  if (showMask) {
    ctx.fillStyle = 'rgba(80,220,120,.25)';
    ctx.beginPath();
    scene.walk.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(230,60,60,.4)';
    for (const b of scene.blocked) {
      if (b.kind === 'rect') ctx.fillRect(b.x, b.y, b.w, b.h);
      else { ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, 7); ctx.fill(); }
    }
  }

  // June — graded to the scene light, with procedural gait
  const set = graded[sceneKey] || frames;
  const list = set[player.dir] && set[player.dir].length ? set[player.dir] : null;
  if (list) {
    const fr = list[player.moving ? Math.floor(player.animT * 5.5) % list.length : 0];
    const h = scene.charH, w = h * (160 / 230);
    const stepT = player.animT * 11;
    const bob = player.moving ? Math.abs(Math.sin(stepT)) * h * 0.022 : 0;
    const sway = player.moving && (player.dir === 'down' || player.dir === 'up')
      ? Math.sin(stepT) * 0.05 : 0;
    ctx.fillStyle = 'rgba(0,0,0,.3)';
    ctx.beginPath(); ctx.ellipse(player.x, player.y + 4, w * 0.32, h * 0.07, 0, 0, 7); ctx.fill();
    ctx.save();
    ctx.translate(player.x, player.y);
    ctx.rotate(sway);
    ctx.drawImage(fr, -w / 2, -h - bob, w, h);
    ctx.restore();
  }
  ctx.restore();
}
requestAnimationFrame(frame);
