// walk_water_audit.mjs — CAN THE PLAYER STAND ON OPEN WATER?
//
//     node tools/walk_water_audit.mjs [--town dellhollow] [--step 0.4] [--json out.json]
//
// WHY THIS EXISTS.  master_walk_qa asks whether a walk record is COVERED (is there art
// under the surface the player walks on) and geometry_audit asks whether two solids
// interpenetrate.  Neither asks the question a player asks the instant it goes wrong:
// "why am I standing on the river?"  A walk ribbon that overruns its deck still has art
// under it — the WATER — so it passes coverage and reads as a bug to everyone who plays
// it.  The user hit this at the stilt clusters on 2026-07-31 ("extremely confusing /
// incomplete geometry, walking on water").
//
// METHOD, and the one distinction that matters.  Sample every standable triangle of the
// walk network on a `--step` grid.  From just under each sample, ray DOWN and take the
// first RENDER-VISIBLE hit:
//
//   deck / jetty / plank / any solid   -> LEGITIMATE.  A deck over water is the whole
//                                        architecture of this town; the water beneath it
//                                        is correct and must not be flagged.
//   water_*                            -> DEFECT.  The player's visual support IS the
//                                        river.
//   nothing at all                     -> DEFECT (worse).  The foot is over the void.
//
// So the rule is not "is there water below" — it is "is the FIRST thing below the foot
// water".  That is what makes the jetty-overhang case pass and the overrun case fail
// with the same probe.
//
// Reads the shipped walk bundle + the shipped render meshes out of the same GLB, so it
// answers for the geometry that is actually in the player's hands.  READ-ONLY.
import fs from 'fs';
import path from 'path';

const ROOT = '/Users/junshernchan/projects/multiplayer-rpg';
const A = process.argv.slice(2);
const arg = (n, d) => (A.includes(n) ? A[A.indexOf(n) + 1] : d);
const TOWN = arg('--town', 'dellhollow');
const STEP = parseFloat(arg('--step', '0.4'));
const OUT = arg('--json', null);

const MAP = JSON.parse(fs.readFileSync(path.join(ROOT, 'public/townmap', TOWN + '.map.json')));
const SCENE = MAP.walkSceneKey || 'townwalk';
const GLBP = path.join(ROOT, 'public/assets/scenes', SCENE, 'scene.glb');

// --------------------------------------------------------------- GLB -> world tris
function readGlb(file) {
  const buf = fs.readFileSync(file);
  const jlen = buf.readUInt32LE(12);
  const json = JSON.parse(buf.slice(20, 20 + jlen).toString('utf8'));
  let off = 20 + jlen;
  const blen = buf.readUInt32LE(off);
  const bin = buf.slice(off + 8, off + 8 + blen);
  const CT = { 5120: Int8Array, 5121: Uint8Array, 5122: Int16Array, 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array };
  const NC = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
  const acc = (i) => {
    const a = json.accessors[i], bv = json.bufferViews[a.bufferView];
    const T = CT[a.componentType], n = NC[a.type];
    const start = (bv.byteOffset || 0) + (a.byteOffset || 0);
    const stride = bv.byteStride || n * T.BYTES_PER_ELEMENT;
    const out = [];
    for (let k = 0; k < a.count; k++) {
      const o = start + k * stride, row = [];
      for (let c = 0; c < n; c++) row.push(new T(bin.buffer, bin.byteOffset + o + c * T.BYTES_PER_ELEMENT, 1)[0]);
      out.push(n === 1 ? row[0] : row);
    }
    return out;
  };
  const mul = (m, v) => [m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12],
                         m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13],
                         m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14]];
  const trs = (n) => {
    if (n.matrix) return n.matrix;
    const t = n.translation || [0, 0, 0], r = n.rotation || [0, 0, 0, 1], s = n.scale || [1, 1, 1];
    const [x, y, z, w] = r;
    return [(1 - 2 * (y * y + z * z)) * s[0], (2 * (x * y + z * w)) * s[0], (2 * (x * z - y * w)) * s[0], 0,
            (2 * (x * y - z * w)) * s[1], (1 - 2 * (x * x + z * z)) * s[1], (2 * (y * z + x * w)) * s[1], 0,
            (2 * (x * z + y * w)) * s[2], (2 * (y * z - x * w)) * s[2], (1 - 2 * (x * x + y * y)) * s[2], 0,
            t[0], t[1], t[2], 1];
  };
  const mm = (a, b) => {
    const o = new Array(16).fill(0);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) for (let k = 0; k < 4; k++)
      o[j * 4 + i] += a[k * 4 + i] * b[j * 4 + k];
    return o;
  };
  const out = [];
  const walk = (ni, parent) => {
    const n = json.nodes[ni], m = mm(parent, trs(n));
    if (n.mesh != null) {
      const nm = n.name || json.meshes[n.mesh].name || '';
      for (const p of json.meshes[n.mesh].primitives) {
        const P = acc(p.attributes.POSITION).map(v => mul(m, v));
        const I = p.indices != null ? acc(p.indices) : P.map((_, i) => i);
        const tris = [];
        for (let i = 0; i + 2 < I.length; i += 3) tris.push([P[I[i]], P[I[i + 1]], P[I[i + 2]]]);
        out.push({ name: nm, tris });
      }
    }
    for (const c of n.children || []) walk(c, m);
  };
  const ID = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  for (const s of json.scenes[json.scene || 0].nodes) walk(s, ID);
  return out;
}

const PARTS = readGlb(GLBP);
// the render-hidden / non-diegetic classes, exactly master_walk_qa finding 19's list:
// these do not draw, so they cannot be a player's visual support.
const NOT_DRAWN = /^(walk|bar|fx_|cam|CAM|REF_|KEY|lm_)/i;
const WATER = /^water/i;

const walkParts = PARTS.filter(p => /^walk/i.test(p.name));
const drawParts = PARTS.filter(p => !NOT_DRAWN.test(p.name));
console.log(`town ${TOWN}  scene ${SCENE}`);
console.log(`walk records ${walkParts.length}   drawn meshes ${drawParts.length}   step ${STEP} m`);

// --------------------------------------------------------------- a down-ray index
const CELL = 2.0;
const DGRID = new Map();
function idx(grid, tri, payload) {
  const [A2, B, C] = tri;
  const i0 = Math.floor(Math.min(A2[0], B[0], C[0]) / CELL), i1 = Math.floor(Math.max(A2[0], B[0], C[0]) / CELL);
  const j0 = Math.floor(Math.min(A2[2], B[2], C[2]) / CELL), j1 = Math.floor(Math.max(A2[2], B[2], C[2]) / CELL);
  for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
    const k = i + ',' + j; let a = grid.get(k); if (!a) grid.set(k, a = []); a.push(payload);
  }
}
for (const p of drawParts) for (const t of p.tris) idx(DGRID, t, [t, p.name]);

// height of a triangle under (x,z), or null
function triY(T, x, z) {
  const [A2, B, C] = T;
  const d = (B[2] - C[2]) * (A2[0] - C[0]) + (C[0] - B[0]) * (A2[2] - C[2]);
  if (Math.abs(d) < 1e-12) return null;
  const l1 = ((B[2] - C[2]) * (x - C[0]) + (C[0] - B[0]) * (z - C[2])) / d;
  const l2 = ((C[2] - A2[2]) * (x - C[0]) + (A2[0] - C[0]) * (z - C[2])) / d;
  const l3 = 1 - l1 - l2;
  if (l1 < -1e-6 || l2 < -1e-6 || l3 < -1e-6) return null;
  return l1 * A2[1] + l2 * B[1] + l3 * C[1];
}

// FIRST DRAWN SURFACE BELOW y at (x,z)
const EPS = 0.02;                       // the walk mesh's own thickness only
function firstBelow(x, z, y) {
  const a = DGRID.get(Math.floor(x / CELL) + ',' + Math.floor(z / CELL));
  if (!a) return null;
  let best = null;
  for (const [T, nm] of a) {
    const yy = triY(T, x, z);
    if (yy == null || yy > y - EPS) continue;
    if (!best || yy > best[0]) best = [yy, nm];
  }
  return best;
}
// THE FOOT'S SUPPORT, probed as a 25 mm CROSS — CLAUDE.md's own interiors rule, and it
// is load-bearing here for the same reason: a sample that falls in the shadow-gap
// between two deck planks sees straight through to the river, and a naive single ray
// calls the whole harbour a defect.  A foot is supported if ANY of the five points has
// a non-water surface under it.  The raw single-ray count is kept and printed too, so
// the correction stays falsifiable rather than being an unexaminable "fix".
const CROSS = [[0, 0], [0.025, 0], [-0.025, 0], [0, 0.025], [0, -0.025]];
function support(x, z, y) {
  let bestSolid = null, sawWater = null;
  for (const [ox, oz] of CROSS) {
    const b = firstBelow(x + ox, z + oz, y);
    if (!b) continue;
    if (WATER.test(b[1])) { if (!sawWater || b[0] > sawWater[0]) sawWater = b; }
    else if (!bestSolid || b[0] > bestSolid[0]) bestSolid = b;
  }
  return { solid: bestSolid, water: sawWater };
}

// --------------------------------------------------------------- sample the network
const defects = [];
const STEP_DN = 0.60;                   // play3d's own step-down window
let samples = 0, overWater = 0, overVoid = 0, supported = 0, rawWater = 0, marginal = 0;
for (const p of walkParts) {
  for (const T of p.tris) {
    const [A2, B, C] = T;
    const ux = B[0] - A2[0], uy = B[1] - A2[1], uz = B[2] - A2[2];
    const vx = C[0] - A2[0], vy = C[1] - A2[1], vz = C[2] - A2[2];
    const ny = uz * vx - ux * vz;
    const nl = Math.hypot(uy * vz - uz * vy, ny, ux * vy - uy * vx) || 1e-12;
    if (Math.abs(ny / nl) <= 0.5) continue;                       // not standable
    const x0 = Math.min(A2[0], B[0], C[0]), x1 = Math.max(A2[0], B[0], C[0]);
    const z0 = Math.min(A2[2], B[2], C[2]), z1 = Math.max(A2[2], B[2], C[2]);
    for (let x = Math.ceil(x0 / STEP) * STEP; x <= x1; x += STEP) {
      for (let z = Math.ceil(z0 / STEP) * STEP; z <= z1; z += STEP) {
        const y = triY(T, x, z);
        if (y == null) continue;
        samples++;
        const raw = firstBelow(x, z, y);
        if (raw && WATER.test(raw[1])) rawWater++;
        const s = support(x, z, y);
        if (!s.solid && !s.water) {
          overVoid++;
          defects.push({ kind: 'VOID', rec: p.name, at: [+x.toFixed(2), +y.toFixed(2), +z.toFixed(2)], under: null, drop: null });
        } else if (!s.solid) {
          overWater++;
          defects.push({ kind: 'WATER', rec: p.name, at: [+x.toFixed(2), +y.toFixed(2), +z.toFixed(2)], under: s.water[1], drop: +(y - s.water[0]).toFixed(2) });
        } else if (y - s.solid[0] > STEP_DN) {
          // supported, but not by anything the foot is standing ON — the deck is more
          // than a step-down away.  MARGINAL, reported separately, never counted as a
          // walk-on-water defect.
          marginal++;
          defects.push({ kind: 'MARGINAL', rec: p.name, at: [+x.toFixed(2), +y.toFixed(2), +z.toFixed(2)], under: s.solid[1], drop: +(y - s.solid[0]).toFixed(2) });
        } else supported++;
      }
    }
  }
}

console.log(`\nsamples ${samples}   supported ${supported}   MARGINAL (deck > ${STEP_DN} m below) ${marginal}`);
console.log(`OVER OPEN WATER ${overWater}   OVER VOID ${overVoid}   -> defect rate ${(100 * (overWater + overVoid) / Math.max(samples, 1)).toFixed(2)}%`);
console.log(`raw single-ray water count (NO cross probe) ${rawWater} — the difference, ${rawWater - overWater}, is plank shadow-gaps, i.e. what the 25 mm cross exists to not call a hole`);

// group by walk record so the answer names a thing that can be edited
const byRec = new Map();
for (const d of defects) {
  let e = byRec.get(d.rec);
  if (!e) byRec.set(d.rec, e = { rec: d.rec, water: 0, void: 0, marg: 0, pts: [], drops: [] });
  if (d.kind === 'WATER') { e.water++; e.drops.push(d.drop); if (e.pts.length < 4) e.pts.push(d.at); }
  else if (d.kind === 'MARGINAL') { e.marg++; }
  else { e.void++; if (e.pts.length < 4) e.pts.push(d.at); }
}
const rows = [...byRec.values()].filter(r => r.water + r.void > 0)
  .sort((a, b) => (b.water + b.void) - (a.water + a.void));
console.log(`\n${rows.length} walk record(s) carry a WALK-ON-WATER defect — worst first:`);
for (const r of rows) {
  const dr = r.drops.length ? ` drop ${Math.min(...r.drops).toFixed(2)}..${Math.max(...r.drops).toFixed(2)} m` : '';
  console.log(`  ${String(r.water + r.void).padStart(4)}  ${r.rec.padEnd(46)} water ${String(r.water).padStart(4)} void ${String(r.void).padStart(3)}${dr}`);
  console.log(`        e.g. ${r.pts.map(p => `(${p[0]}, ${p[1]}, ${p[2]})`).join('  ')}`);
}

if (OUT) { fs.writeFileSync(OUT, JSON.stringify({ town: TOWN, step: STEP, samples, overWater, overVoid, records: rows }, null, 1)); console.log('\nwrote ' + OUT); }
process.exit(0);
