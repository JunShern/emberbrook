// emb_plate_object.mjs — WHICH OBJECT IS AT THESE PIXELS.  No Blender, no browser.
//
//   node tools/emb_plate_object.mjs --shot square --bbox 0.1,0.2,0.4,0.6
//   node tools/emb_plate_object.mjs --shot homerow --world 29.2,44.8,55.3,74.3,1.9,5.1
//   node tools/emb_plate_object.mjs --findings docs/qa/redteam/run-<stamp>/findings.json
//
// WHY IT EXISTS.  `plate_probe` reconstructs a world XYZ per pixel and is explicit that
// it "names a REGION, never an object — a world box out of `crushed` is the input to a
// Blender ray census".  Round 3 twice recorded a worklist item whose named object was the
// wrong one; round 8's headline was a four-run "hole in the world" verdict that put its
// bbox on a market awning at 5.3 m.  The Blender ray census is the right instrument and
// it is unavailable to any lane that does not own the GPU — so a judge finding could not
// be put on the geometry at all while a bake was running.  This closes that: the same
// reconstruction, attributed against the bundle's OWN collision GLB.
//
// WHAT IT DOES.  Reconstructs world XYZ for the pixels inside a bbox exactly as
// plate_probe does (the bundle's solved camera + its rgb24-viewz depth.png, NEAREST
// resample only), converts glTF Y-up to the bake's Blender Z-up (bx=gx, by=-gz, bz=gy),
// and finds the nearest triangle in `scene.glb` for each sample through a uniform grid.
// It reports the node names holding those pixels, their share, and the residual distance.
//
// WHAT IT CANNOT SEE, SAID UP FRONT — this is not the Blender census and does not replace
// it.  `emb-cine/scene.glb` is exported from `emberbrook-master.blend`, THE GRAY BLOCKOUT
// (CLAUDE.md, "the 146x trap"): dressing scatter, leaves, awnings and every render-only
// card are NOT in it.  So a high residual distance means "the thing making this pixel is
// dressing, not massing" and is itself the answer — it is reported, never hidden.  A
// `camera-only` mesh is likewise absent.  Attribution is nearest-surface, not a ray, so a
// pixel equidistant between two skins can go either way; the residual is the honesty.
import fs from 'fs';
import path from 'path';
import {PNG} from 'pngjs';
import {loadGlb} from './glb_read.mjs';

const ROOT = path.dirname(new URL(import.meta.url).pathname).replace(/\/tools$/, '');
const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const BUNDLE = opt('--bundle', path.join(ROOT, 'public/assets/scenes/emb-cine'));
const MAXS = +opt('--max-samples', 3000);
const TOPN = +opt('--top', 6);

const CINE = JSON.parse(fs.readFileSync(path.join(BUNDLE, 'cine.json'), 'utf8'));
const CAMS = Object.fromEntries(CINE.cameras.map((c) => [c.id, c]));

// ------------------------------------------------------------ reconstruction ---
function basis(pos, aim) {
  const f = [aim[0] - pos[0], aim[1] - pos[1], aim[2] - pos[2]];
  const fl = Math.hypot(...f); f.forEach((_, i) => f[i] /= fl);
  let up = [0, 0, 1];
  if (Math.abs(f[2]) > 0.9999) up = [0, 1, 0];
  const r = [f[1] * up[2] - f[2] * up[1], f[2] * up[0] - f[0] * up[2], f[0] * up[1] - f[1] * up[0]];
  const rl = Math.hypot(...r); r.forEach((_, i) => r[i] /= rl);
  const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
  return [r, u, f];
}

function depthOf(shot) {
  const c = CAMS[shot];
  if (!c) throw new Error('no such shot: ' + shot);
  const png = PNG.sync.read(fs.readFileSync(path.join(BUNDLE, 'cameras', shot, 'depth.png')));
  return {c, png};
}

// world XYZ (Blender Z-up) for a normalised pixel (u,v); null in the void.
function worldAt(c, png, u, v) {
  const x = Math.min(png.width - 1, Math.max(0, Math.floor(u * png.width)));
  const y = Math.min(png.height - 1, Math.max(0, Math.floor(v * png.height)));
  const i = (y * png.width + x) * 4;
  const n = png.data[i] * 65536 + png.data[i + 1] * 256 + png.data[i + 2];
  if (n >= 16777215 - 0.5) return null;                       // far plane = void
  const {near, far} = c.depth;
  const d = near + (far - near) * n / 16777215.0;
  const ty = Math.tan(c.fov * Math.PI / 360);
  const ar = png.width / png.height;
  const X = (2 * u - 1) * ty * ar, Y = (1 - 2 * v) * ty;
  const [r, up, f] = basis(c.pos, c.aim);
  return [0, 1, 2].map((k) => c.pos[k] + d * (f[k] + X * r[k] + Y * up[k]));
}

// ------------------------------------------------------------------ geometry ---
let GRID = null;
function grid() {
  if (GRID) return GRID;
  const G = loadGlb(path.join(BUNDLE, 'scene.glb'));
  const T = G.trisFlat(/./);
  // glTF Y-up -> the bake's Blender Z-up.  bx = gx, by = -gz, bz = gy.
  const P = new Float32Array(T.count * 9);
  for (let t = 0; t < T.count; t++) for (let k = 0; k < 3; k++) {
    const o = t * 9 + k * 3;
    P[o] = T.pos[o]; P[o + 1] = -T.pos[o + 2]; P[o + 2] = T.pos[o + 1];
  }
  const CELL = 3.0;
  const key = (a, b, c) => a + ',' + b + ',' + c;
  const cells = new Map();
  for (let t = 0; t < T.count; t++) {
    const o = t * 9;
    let mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    for (let k = 0; k < 3; k++) for (let c = 0; c < 3; c++) {
      const v = P[o + k * 3 + c]; if (v < mn[c]) mn[c] = v; if (v > mx[c]) mx[c] = v;
    }
    const a0 = Math.floor(mn[0] / CELL), a1 = Math.floor(mx[0] / CELL);
    const b0 = Math.floor(mn[1] / CELL), b1 = Math.floor(mx[1] / CELL);
    const c0 = Math.floor(mn[2] / CELL), c1 = Math.floor(mx[2] / CELL);
    if ((a1 - a0 + 1) * (b1 - b0 + 1) * (c1 - c0 + 1) > 400) continue;   // a skirt-sized tri
    for (let a = a0; a <= a1; a++) for (let b = b0; b <= b1; b++) for (let c = c0; c <= c1; c++) {
      const k = key(a, b, c); let L = cells.get(k); if (!L) cells.set(k, L = []); L.push(t);
    }
  }
  GRID = {P, node: T.node, names: T.names, cells, CELL, key, count: T.count};
  return GRID;
}

function triDist2(P, t, p) {                       // squared point-triangle distance
  const o = t * 9;
  const A = [P[o], P[o + 1], P[o + 2]], B = [P[o + 3], P[o + 4], P[o + 5]],
        C = [P[o + 6], P[o + 7], P[o + 8]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const E0 = sub(B, A), E1 = sub(C, A), D = sub(A, p);
  const a = dot(E0, E0), b = dot(E0, E1), c = dot(E1, E1), d = dot(E0, D), e = dot(E1, D), f = dot(D, D);
  let det = a * c - b * b, s = b * e - c * d, t2 = b * d - a * e;
  if (det < 1e-12) { s = 0; t2 = 0; }
  else if (s + t2 <= det) {
    if (s < 0) { if (t2 < 0) { if (d < 0) { t2 = 0; s = -d >= a ? 1 : -d / a; } else { s = 0; t2 = e >= 0 ? 0 : (-e >= c ? 1 : -e / c); } }
                 else { s = 0; t2 = e >= 0 ? 0 : (-e >= c ? 1 : -e / c); } }
    else if (t2 < 0) { t2 = 0; s = d >= 0 ? 0 : (-d >= a ? 1 : -d / a); }
    else { s /= det; t2 /= det; }
  } else {
    if (s < 0) { const t3 = b + e, n2 = c + 2 * e + f;
      if (t3 > d + b) { const num = t3 - d - b, den = a - 2 * b + c; s = num >= den ? 1 : num / den; t2 = 1 - s; }
      else { s = 0; t2 = t3 <= 0 ? 1 : (e >= 0 ? 0 : -e / c); } void n2; }
    else if (t2 < 0) { const t3 = a + d;
      if (t3 > b + e) { const num = c + e - b - d, den = a - 2 * b + c; s = num >= den ? 1 : num / den; t2 = 1 - s; }
      else { t2 = 0; s = t3 <= 0 ? 1 : (d >= 0 ? 0 : -d / a); } }
    else { const num = c + e - b - d, den = a - 2 * b + c;
      s = num <= 0 ? 0 : (num >= den ? 1 : num / den); t2 = 1 - s; }
  }
  const q = [A[0] + s * E0[0] + t2 * E1[0], A[1] + s * E0[1] + t2 * E1[1], A[2] + s * E0[2] + t2 * E1[2]];
  const dd = sub(q, p); return dot(dd, dd);
}

export function nameAt(p) {
  const g = grid();
  const a = Math.floor(p[0] / g.CELL), b = Math.floor(p[1] / g.CELL), c = Math.floor(p[2] / g.CELL);
  let best = Infinity, bestT = -1;
  for (let R = 1; R <= 4; R++) {
    for (let i = -R; i <= R; i++) for (let j = -R; j <= R; j++) for (let k = -R; k <= R; k++) {
      if (R > 1 && Math.max(Math.abs(i), Math.abs(j), Math.abs(k)) < R) continue;
      const L = g.cells.get(g.key(a + i, b + j, c + k)); if (!L) continue;
      for (const t of L) { const d2 = triDist2(g.P, t, p); if (d2 < best) { best = d2; bestT = t; } }
    }
    if (bestT >= 0 && best <= (R * g.CELL) ** 2) break;
  }
  if (bestT < 0) return {name: '(no massing within 12 m)', dist: Infinity};
  return {name: g.names[g.node[bestT]], dist: Math.sqrt(best)};
}

// ---------------------------------------------------------------------- census ---
export function censusBox(shot, bbox) {
  const {c, png} = depthOf(shot);
  const [x0, y0, x1, y1] = bbox;
  const area = Math.max(1e-6, (x1 - x0) * (y1 - y0));
  const nx = Math.max(4, Math.round(Math.sqrt(MAXS * (x1 - x0) / (y1 - y0)) || 40));
  const ny = Math.max(4, Math.round(MAXS / nx));
  const tally = new Map(); let void_ = 0, n = 0;
  const dists = [];
  for (let iy = 0; iy < ny; iy++) for (let ix = 0; ix < nx; ix++) {
    const u = x0 + (ix + 0.5) / nx * (x1 - x0), v = y0 + (iy + 0.5) / ny * (y1 - y0);
    const p = worldAt(c, png, u, v);
    n++;
    if (!p) { void_++; continue; }
    const r = nameAt(p);
    const e = tally.get(r.name) || {n: 0, d: 0};
    e.n++; e.d += Math.min(50, r.dist); tally.set(r.name, e);
    dists.push(r.dist);
  }
  const rows = [...tally.entries()].map(([name, e]) => ({name, frac: e.n / n, dist: e.d / e.n}))
    .sort((a, b) => b.frac - a.frac);
  dists.sort((a, b) => a - b);
  return {shot, bbox, area, samples: n, voidFrac: void_ / n, rows,
          distP50: dists.length ? dists[dists.length >> 1] : null,
          distP90: dists.length ? dists[Math.floor(dists.length * 0.9)] : null};
}

// A census over an ARBITRARY pixel set, so a mask (plate_probe's crushed regions, a water
// census) can be attributed without pretending it is a rectangle.  `pts` is [[u,v], ...].
export function censusPoints(shot, pts) {
  const {c, png} = depthOf(shot);
  const tally = new Map(); let void_ = 0; const dists = [];
  for (const [u, v] of pts) {
    const p = worldAt(c, png, u, v);
    if (!p) { void_++; continue; }
    const r = nameAt(p);
    const e = tally.get(r.name) || {n: 0, d: 0};
    e.n++; e.d += Math.min(50, r.dist); tally.set(r.name, e);
    dists.push(r.dist);
  }
  const rows = [...tally.entries()].map(([name, e]) => ({name, frac: e.n / pts.length, dist: e.d / e.n}))
    .sort((a, b) => b.frac - a.frac);
  dists.sort((a, b) => a - b);
  return {shot, bbox: [0, 0, 1, 1], area: NaN, samples: pts.length, voidFrac: void_ / pts.length, rows,
          distP50: dists.length ? dists[dists.length >> 1] : null,
          distP90: dists.length ? dists[Math.floor(dists.length * 0.9)] : null};
}

// PER-PIXEL, not aggregated: the name AND the world point for each sample, so a caller can
// join the attribution to what the beauty plate is actually SHOWING there.  This is what
// answers "what is this mesh WEARING" without Blender: name the pixel, then read it.
export function pixelNames(shot, pts) {
  const {c, png} = depthOf(shot);
  const out = [];
  for (const [u, v] of pts) {
    const p = worldAt(c, png, u, v);
    if (!p) { out.push(null); continue; }
    const r = nameAt(p);
    out.push({name: r.name, dist: r.dist, p});
  }
  return out;
}

// ------------------------------------------------------------------------ cli ---
function report(r) {
  console.log(`== ${r.shot}  bbox [${r.bbox.map((v) => v.toFixed(3)).join(', ')}]  `
    + `${(100 * r.area).toFixed(2)}% of frame  ${r.samples} samples  void ${(100 * r.voidFrac).toFixed(1)}%`
    + `  residual p50 ${r.distP50 === null ? 'n/a' : r.distP50.toFixed(2)} m`
    + ` p90 ${r.distP90 === null ? 'n/a' : r.distP90.toFixed(2)} m`);
  for (const row of r.rows.slice(0, TOPN))
    console.log(`   ${(100 * row.frac).toFixed(1).padStart(5)}%  ${row.name}   (residual ${row.dist.toFixed(2)} m)`);
}

if (import.meta.url === 'file://' + process.argv[1]) {
  const shot = opt('--shot', null);
  const bboxS = opt('--bbox', null);
  const FIND = opt('--findings', null);
  if (FIND) {
    const f = JSON.parse(fs.readFileSync(FIND, 'utf8'));
    const out = [];
    for (const s of f.survivors) {
      if (!s.bbox || !CAMS[s.shot]) continue;
      const r = censusBox(s.shot, s.bbox);
      out.push({fid: s.fid, shot: s.shot, mode: s.mode, category: s.category, desc: s.desc,
                verdict: s.verdict, item: s.item, severity: s.severity, ...r});
      console.log(`-- ${s.fid} ${s.shot} [${s.mode}] ${(s.desc || '').slice(0, 90)}`);
      report(r);
    }
    const dest = opt('--out', path.join(path.dirname(FIND), 'object-census.json'));
    fs.writeFileSync(dest, JSON.stringify(out, null, 1));
    console.log('\nwrote ' + dest);
  } else if (opt('--points', null)) {
    // {"<shot>": [[u,v], ...], ...}
    const src = JSON.parse(fs.readFileSync(opt('--points'), 'utf8'));
    const out = {};
    for (const [sh, pts] of Object.entries(src)) {
      const r = censusPoints(sh, pts); out[sh] = r; report(r);
    }
    const dest = opt('--out', null);
    if (dest) { fs.writeFileSync(dest, JSON.stringify(out, null, 1)); console.log('wrote ' + dest); }
  } else if (shot && bboxS) {
    report(censusBox(shot, bboxS.split(',').map(Number)));
  } else {
    console.error('usage: --shot <id> --bbox x0,y0,x1,y1   |   --findings <findings.json>');
    process.exit(2);
  }
}
