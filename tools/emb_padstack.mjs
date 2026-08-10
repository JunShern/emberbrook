// emb_padstack.mjs — HOW MUCH OF EMBERBROOK'S PAVING IS TWO PAVING SURFACES STACKED,
// AND HOW FAR APART ARE THEY.  No Blender, no browser, ~6 s.
//
//   node tools/emb_padstack.mjs                              # town census
//   node tools/emb_padstack.mjs --cell 0.05 --top 30         # finer grid, more pairs
//   node tools/emb_padstack.mjs --bundle public/assets/scenes/emb-townwalk
//   node tools/emb_padstack.mjs --json /tmp/stack.json
//   node tools/emb_padstack.mjs --holes                      # the OTHER paving defect
//
// WHY IT EXISTS.  `emb_padcoplanar` asks one question — are two walk meshes' bounding-box
// TOPS equal to within 2 mm and do their boxes overlap — and found 55 pairs, of which
// exactly one (`walk_pad_lake-home` / `walk_pad_grandmothers-bench`, dz 0.0000) rendered
// as the black hole round 1 shipped a 4 mm nudge for.  That test answers the Z-FIGHTING
// question and it is the wrong question for everything else: a bounding box is not a
// surface, and TWO SURFACES 70 mm APART DO NOT Z-FIGHT — they photograph as one paved
// plate floating above another, with a lit riser and a shadow line between them.  That is
// the language sixteen of round 1's thirty-seven surviving geometry findings are written
// in ("the concrete path slabs clip and overlap unnaturally", "the path slab terminates
// awkwardly, floating above the ground", "disjointed and floating terrain mesh planes").
//
// WHAT IT MEASURES.  Every up-facing triangle of every `walk_*` node in the shipped
// bundle is rasterised onto a plan grid (default 5 cm).  A cell holding floor faces from
// TWO OR MORE nodes is DOUBLE-COVERED; its step is the gap between the highest node's top
// there and the second highest's.  So the number is an AREA in square metres of real
// double coverage, not a count of bounding boxes that happen to intersect — a pad whose
// box overlaps a ribbon's box but whose faces never share a cell contributes nothing.
//
// WHAT IT CANNOT SEE.  Whether a step is INTENDED.  Emberbrook is terraced and the plaza
// stands above the pond road, so the >250 mm band is mostly real level changes; the bands
// are printed separately for exactly that reason and the tool takes no view.  It also
// reads the bundle, which is the blockout — `walk_*` is the whole of the paving the
// player sees (`emb_pavechop` proved that with a height control) so that is the right
// artifact, but nothing dressing puts on top of it is here.
import fs from 'fs';
import path from 'path';
import {loadGlb} from './glb_read.mjs';

const ROOT = path.dirname(new URL(import.meta.url).pathname).replace(/\/tools$/, '');
const A = process.argv.slice(2);
const opt = (n, d) => { const i = A.indexOf(n); return i >= 0 ? A[i + 1] : d; };
const CELL = +opt('--cell', 0.05);
const TOPN = +opt('--top', 25);
const BUNDLE = opt('--bundle', 'public/assets/scenes/emb-cine');
const JSONOUT = opt('--json', null);
const RE = new RegExp(opt('--re', '^walk'), 'i');
const HOLES = process.argv.includes('--holes');

const glb = path.join(ROOT, BUNDLE, 'scene.glb');
const G = loadGlb(glb);
const T = G.trisFlat(RE);

// ---- rasterise up-facing faces onto the plan grid -------------------------------
const cells = new Map();                       // ix*1e5+iz -> [nodeId, y] …
let faces = 0;
for (let t = 0; t < T.count; t++) {
  const o = t * 9;
  const ax = T.pos[o], ay = T.pos[o + 1], az = T.pos[o + 2];
  const bx = T.pos[o + 3], by = T.pos[o + 4], bz = T.pos[o + 5];
  const cx = T.pos[o + 6], cy = T.pos[o + 7], cz = T.pos[o + 8];
  const ux = bx - ax, uy = by - ay, uz = bz - az;
  const vx = cx - ax, vy = cy - ay, vz = cz - az;
  const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
  const nl = Math.hypot(nx, ny, nz) || 1e-12;
  if (Math.abs(ny / nl) < 0.5) continue;       // not a floor face (either winding)
  faces++;
  const d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz);
  if (Math.abs(d) < 1e-12) continue;
  const i0 = Math.floor(Math.min(ax, bx, cx) / CELL), i1 = Math.floor(Math.max(ax, bx, cx) / CELL);
  const j0 = Math.floor(Math.min(az, bz, cz) / CELL), j1 = Math.floor(Math.max(az, bz, cz) / CELL);
  for (let ix = i0; ix <= i1; ix++) for (let iz = j0; iz <= j1; iz++) {
    const x = (ix + 0.5) * CELL, z = (iz + 0.5) * CELL;
    const l1 = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d;
    const l2 = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d;
    const l3 = 1 - l1 - l2;
    if (l1 < 0 || l2 < 0 || l3 < 0) continue;
    const k = ix * 100000 + iz;
    let a = cells.get(k); if (!a) { a = []; cells.set(k, a); }
    a.push(T.node[t], l1 * ay + l2 * by + l3 * cy);
  }
}

// ---- per cell: the top surface of each distinct node ----------------------------
const BANDS = [[0.002, '<=2mm  (z-fight)'], [0.02, '2-20mm (near-coincident)'],
               [0.06, '20-60mm'], [0.12, '60-120mm'], [0.25, '120-250mm'],
               [Infinity, '>250mm (terrace?)']];
const band = BANDS.map(() => 0);
const pairs = new Map();
const dzs = [];
let multi = 0;
for (const [, a] of cells) {
  const top = new Map();
  for (let i = 0; i < a.length; i += 2) {
    const p = top.get(a[i]); if (p === undefined || a[i + 1] > p) top.set(a[i], a[i + 1]);
  }
  if (top.size < 2) continue;
  multi++;
  const e = [...top.entries()].sort((p, q) => q[1] - p[1]);
  const dz = e[0][1] - e[1][1];
  dzs.push(dz);
  band[BANDS.findIndex(([hi]) => dz <= hi)]++;
  const key = T.names[e[0][0]] + ' over ' + T.names[e[1][0]];
  const r = pairs.get(key) || {n: 0, dz: []};
  r.n++; r.dz.push(dz); pairs.set(key, r);
}
const CA = CELL * CELL;
dzs.sort((x, y) => x - y);
const q = (p) => (dzs.length ? dzs[Math.floor(p * (dzs.length - 1))] : NaN);
const med = (a) => { const s = [...a].sort((x, y) => x - y); return s[s.length >> 1]; };

console.log(`emb_padstack ${BUNDLE} — ${T.names.length} walk nodes, ${faces} floor faces, ` +
            `grid ${CELL} m`);
console.log(`  paved plan        ${(cells.size * CA).toFixed(1)} m2 over ${cells.size} cells`);
console.log(`  DOUBLE-COVERED    ${(multi * CA).toFixed(1)} m2 (${(100 * multi / cells.size).toFixed(1)}% of it)`);
console.log(`  step |dz|         p05 ${q(.05).toFixed(4)}  p50 ${q(.5).toFixed(4)}  ` +
            `p90 ${q(.9).toFixed(4)}  max ${q(1).toFixed(4)} m`);
BANDS.forEach(([, n], i) =>
  console.log(`    ${n.padEnd(26)} ${String(band[i]).padStart(6)} cells  ${(band[i] * CA).toFixed(2)} m2`));
console.log(`  --- worst stacks by double-covered area (top ${TOPN}) ---`);
const rank = [...pairs.entries()].sort((x, y) => y[1].n - x[1].n);
for (const [k, r] of rank.slice(0, TOPN))
  console.log(`    ${(r.n * CA).toFixed(2)} m2  step p50 ${med(r.dz).toFixed(4)} m  ${k}`);

if (JSONOUT) {
  fs.writeFileSync(JSONOUT, JSON.stringify({
    bundle: BUNDLE, cell: CELL, nodes: T.names.length, faces,
    pavedM2: cells.size * CA, doubleM2: multi * CA,
    dz: {p05: q(.05), p50: q(.5), p90: q(.9), max: q(1)},
    bands: BANDS.map(([, n], i) => ({band: n, cells: band[i], m2: band[i] * CA})),
    stacks: rank.map(([k, r]) => ({pair: k, m2: r.n * CA, dz50: med(r.dz)})),
  }, null, 1));
  console.log('  wrote ' + JSONOUT);
}

// ---- --holes: A HOLE IN THE PAVING THAT NOTHING STANDS IN IS A BLACK SQUARE ----------
// THE SECOND DEFECT IN THE SAME FAMILY, and it is the other half of round 1's surviving
// geometry language: "the ground mesh has severe geometry tearing and black void seams",
// "visible black hole voids in the ground mesh", "sharp rectangular cutouts in the floor
// geometry, leaving missing tiles and black voids around the pillar bases".  An area
// apron is cut on a 0.45 m lattice around every landmark footprint, and where the cut is
// WIDER than the thing standing in it the player sees terrain 0.12 m below the paving —
// `CUT_DROP` — through a square hole.  This finds every ENCLOSED hole (flood-filled from
// outside the apron's own bbox, so a bay open to the edge is not a hole) and asks whether
// any blockout solid stands in it.
//   THE LIMIT, SAID UP FRONT: the occupancy test reads the COLLISION bundle, which is the
// gray blockout, so a hole covered only by DRESSING reads as empty here.  It is a screen
// that ranks holes for the eye, never a verdict that one is a defect.
if (HOLES) {
  const CH = +opt('--hcell', 0.15);
  const solid = new Set();
  const S = G.trisFlat(/^(lm_|emb_sq_|emb_lamp_|kit_)/i);
  for (let t = 0; t < S.count; t++) {
    const o = t * 9;
    const i0 = Math.floor(Math.min(S.pos[o], S.pos[o + 3], S.pos[o + 6]) / CH);
    const i1 = Math.floor(Math.max(S.pos[o], S.pos[o + 3], S.pos[o + 6]) / CH);
    const j0 = Math.floor(Math.min(S.pos[o + 2], S.pos[o + 5], S.pos[o + 8]) / CH);
    const j1 = Math.floor(Math.max(S.pos[o + 2], S.pos[o + 5], S.pos[o + 8]) / CH);
    if ((i1 - i0) * (j1 - j0) > 40000) continue;              // a skirt, not a footprint
    for (let a = i0; a <= i1; a++) for (let b = j0; b <= j1; b++) solid.add(a * 100000 + b);
  }
  const fams = [...new Set(T.names.map((n) => n.replace(/\.\d+$/, '')))]
    .filter((n) => /^walk_lm_/.test(n));
  console.log(`\n--- enclosed holes, ${CH} m grid, occupancy against ${solid.size} blockout plan cells ---`);
  for (const fam of fams) {
    const F = G.trisFlat(new RegExp('^' + fam.replace(/[-]/g, '[-]') + '(\\.|$)'));
    const cs = new Set(); let x0 = 1e9, x1 = -1e9, z0 = 1e9, z1 = -1e9;
    for (let t = 0; t < F.count; t++) {
      const o = t * 9;
      const A = [F.pos[o], F.pos[o + 1], F.pos[o + 2]];
      const B = [F.pos[o + 3], F.pos[o + 4], F.pos[o + 5]];
      const C = [F.pos[o + 6], F.pos[o + 7], F.pos[o + 8]];
      const ux = B[0] - A[0], uy = B[1] - A[1], uz = B[2] - A[2];
      const vx = C[0] - A[0], vy = C[1] - A[1], vz = C[2] - A[2];
      const ny = uz * vx - ux * vz;
      const nl = Math.hypot(uy * vz - uz * vy, ny, ux * vy - uy * vx) || 1e-9;
      if (Math.abs(ny / nl) < 0.5) continue;
      const d = (B[2] - C[2]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[2] - C[2]);
      if (Math.abs(d) < 1e-12) continue;
      for (let a = Math.floor(Math.min(A[0], B[0], C[0]) / CH); a <= Math.floor(Math.max(A[0], B[0], C[0]) / CH); a++)
        for (let b = Math.floor(Math.min(A[2], B[2], C[2]) / CH); b <= Math.floor(Math.max(A[2], B[2], C[2]) / CH); b++) {
          const x = (a + 0.5) * CH, z = (b + 0.5) * CH;
          const l1 = ((B[2] - C[2]) * (x - C[0]) + (C[0] - B[0]) * (z - C[2])) / d;
          const l2 = ((C[2] - A[2]) * (x - C[0]) + (A[0] - C[0]) * (z - C[2])) / d;
          if (l1 < 0 || l2 < 0 || 1 - l1 - l2 < 0) continue;
          cs.add(a * 100000 + b);
          x0 = Math.min(x0, a); x1 = Math.max(x1, a); z0 = Math.min(z0, b); z1 = Math.max(z1, b);
        }
    }
    if (!cs.size) continue;
    const Wd = x1 - x0 + 3, Hd = z1 - z0 + 3, ix = (a, b) => a * Hd + b;
    const cov = new Uint8Array(Wd * Hd);
    for (const k of cs) { const a = Math.round(k / 100000); cov[ix(a - x0 + 1, (k - a * 100000) - z0 + 1)] = 1; }
    const out = new Uint8Array(Wd * Hd); const st = [0]; out[0] = 1;
    while (st.length) { const c = st.pop(), a = (c / Hd) | 0, b = c % Hd;
      for (const [da, db] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const na = a + da, nb = b + db; if (na < 0 || nb < 0 || na >= Wd || nb >= Hd) continue;
        const n = ix(na, nb); if (out[n] || cov[n]) continue; out[n] = 1; st.push(n); } }
    const hs = new Uint8Array(Wd * Hd); const comps = [];
    for (let a = 0; a < Wd; a++) for (let b = 0; b < Hd; b++) { const i = ix(a, b);
      if (cov[i] || out[i] || hs[i]) continue;
      const q = [i]; hs[i] = 1; const cc = [];
      while (q.length) { const c = q.pop(); cc.push(c); const aa = (c / Hd) | 0, bb = c % Hd;
        for (const [da, db] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const na = aa + da, nb = bb + db; if (na < 0 || nb < 0 || na >= Wd || nb >= Hd) continue;
          const n = ix(na, nb); if (cov[n] || out[n] || hs[n]) continue; hs[n] = 1; q.push(n); } }
      comps.push(cc); }
    let occM = 0, empM = 0, occN = 0, empN = 0; const big = [];
    for (const cc of comps) {
      let k = 0;
      for (const c of cc) { const a = (c / Hd | 0) + x0 - 1, b = (c % Hd) + z0 - 1;
        if (solid.has(a * 100000 + b)) k++; }
      if (k / cc.length >= 0.5) { occM += cc.length; occN++; }
      else { empM += cc.length; empN++; big.push(cc.length * CH * CH); }
    }
    big.sort((a, b) => b - a);
    console.log(`  ${fam.padEnd(24)} paved ${(cs.size * CH * CH).toFixed(1)} m2 · ` +
      `${comps.length} enclosed hole(s): ${occN} occupied (${(occM * CH * CH).toFixed(2)} m2), ` +
      `${empN} EMPTY (${(empM * CH * CH).toFixed(2)} m2 = ${(100 * empM / cs.size).toFixed(1)}% of its own area)` +
      (big.length ? `; biggest ${big.slice(0, 4).map((v) => v.toFixed(2)).join(', ')} m2` : ''));
  }
}
