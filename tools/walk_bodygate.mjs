// walk_bodygate.mjs — CAN A BODY ACTUALLY GET FROM THIS WALK SAMPLE TO THE NEXT ONE?
//
//   node tools/walk_bodygate.mjs                       audit del-cine, print the census
//   node tools/walk_bodygate.mjs --scene townwalk      any shipped bundle
//   node tools/walk_bodygate.mjs --step 0.15           coarser lattice (default 0.075 m)
//   node tools/walk_bodygate.mjs --region x0,x1,z0,z1  runtime coords, a district only
//   node tools/walk_bodygate.mjs --glb <path>          audit a bundle outside public/
//   node tools/walk_bodygate.mjs --json <path>         write the full blocked-step list
//   node tools/walk_bodygate.mjs --max-blocked N       exit non-zero above N (gate mode)
//
// WHY THIS EXISTS, and it is a hole three instruments left between them. On 2026-08-01 a
// handrail (`gs_rail`) was found lying ACROSS the gate stair — the only exit the scene
// graph offers from Dellhollow's entry shot — blocking 1.05 m of a 1.4 m flight at body
// height. It had been there for weeks, and every gate in the project passed it:
//
//   master_walk_qa  [3] RAY COVERAGE fires one ray DOWN and one UP per 0.35 m sample and
//                   asks "does the down-ray first-hit a walk mesh". A rail beside a
//                   sample point is not under it. [4] HEADROOM asks for 2.0 m of clear
//                   air ABOVE the surface; this rail's top is 0.30 m above the landing.
//   GateGrid        (district_lib) faithfully reproduces that same ray contract so a
//                   BUILDER can pre-check itself — so it inherits the same blind spot by
//                   construction, and every rail built through it inherits it too.
//   cine_test /     both reason about the walk network as RECORDS and REGIONS. Neither
//   seam_test       has ever asked whether the geometry between two records is passable.
//
// The thing none of them models is the one thing the runtime actually does: play3d.html
// settles the foot on a walk surface and then intersects THE CHARACTER'S BODY BOX with
// real triangles. A ray is not a body. This file is that body.
//
// IT REPRODUCES play3d.html's walkStep() EXACTLY, and the constants are copied from it
// rather than chosen here (public/play3d.html, `let ... RAD=.42, STEP_UP=.63, STEP_DN=.8`
// and `BODY_R=.30, BODY_H=1.30`):
//
//   walkGround(x,z,fy)  the foot settles on the HIGHEST walk top inside the window
//                       [fy - 0.90, fy + 0.73]  (topsAt from fy+STEP_UP+.1, depth
//                       STEP_UP+STEP_DN+.2). Nothing outside it catches the foot.
//   the body box        y from max(gB + STEP_UP + .02, gA + .02) to gB + BODY_H,
//                       xz a BODY_R square about the DESTINATION. The lower bound is
//                       never below the height you are stepping down FROM, which is why
//                       the slab you are walking off cannot obstruct you — and why an
//                       obstruction like gs_rail only bites in ONE direction and only on
//                       a step, which is exactly why standing-clearance tests miss it.
//
// SO A STANDING TEST CANNOT FIND THIS CLASS, and that is worth stating plainly because
// it is the obvious thing to write instead. gs_rail sits at h 22.11..22.60 over a landing
// whose surface is 22.30: standing there, the body box starts at 22.95 and the rail is
// below it — invisible, and correctly so, because below STEP_UP is a climbable step.
// It only becomes a wall when the foot settles 0.69 m lower on the next tread and the
// box drops to 22.32..22.91 around it. The unit of this audit is therefore a STEP.
//
// WHAT IT DOES NOT MODEL, stated so the number is not over-read: the runtime also slides
// (it retries [dx,0] and [0,dz]), and it slims the body to BODY_R*0.35 when it is already
// penetrating something. Both make the real walker MORE mobile than this audit. So a
// blocked step here is a step the walker cannot take straight; whether it can slide
// around the obstruction depends on its neighbours, and the aggregate to read is
// "samples where every outgoing step is blocked", which is reported separately.
//
// Walk meshes are excluded from the solid set: they are the floor. Verified against the
// live runtime — this tool and a real body driven through SIM in Chrome agree on
// gs_rail's z-extent to the sample.
import fs from 'fs';
import path from 'path';
import {loadGlb} from './glb_read.mjs';
import {PUB} from './cine_regions.mjs';

const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const SCENE = opt('--scene', 'del-cine');
const STEP = +opt('--step', '0.075');
const OUTJSON = opt('--json', null);
const MAXB = ARGS.includes('--max-blocked') ? +opt('--max-blocked', '0') : null;
const REGION = opt('--region', null) ? opt('--region', null).split(',').map(Number) : null;

// --- play3d.html's own constants. Copied, not chosen. -------------------------
const BODY_R = 0.30, BODY_H = 1.30, STEP_UP = 0.63, STEP_DN = 0.80;
// THE LATTICE IS THE RUNTIME'S OWN STRIDE, AND THAT IS NOT A TUNING CHOICE — it is the
// difference between this tool and a rumour. phys() moves the body SPD = 0.075 m per
// physics step and evaluates walkGround + the body box at every one of them, so a step
// the runtime never takes is a step this audit must not test. Calibrated against the live
// runtime: at a 0.25 m lattice, 30 sampled "blocked" steps were driven through the real
// SIM and only 4 actually stopped the body — the other 26 were hops the walker never
// makes in one piece. The stride below is play3d.html's SPD, copied.
const WIN_UP = STEP_UP + 0.10, WIN_DN = STEP_DN + 0.10;   // walkGround's search window

// `--glb` points at a bundle that is not the shipped one, so a BEFORE and an AFTER can be
// measured on the same rule without overwriting what ships (walk_water_audit carries the
// same option for the same reason).
const GLB = opt('--glb', null) || path.join(PUB, 'assets/scenes', SCENE, 'scene.glb');
if (!fs.existsSync(GLB)) { console.error(`no bundle at ${GLB}`); process.exit(1); }
const G = loadGlb(GLB);
const J = G.json;

// ---- geometry extraction: one triangle list per node, once -------------------
function nodeTris(i) {
  const n = J.nodes[i]; if (n.mesh === undefined) return [];
  const m = G.world[i], out = [];
  const xf = (p) => [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
                     m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
                     m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]];
  for (const p of J.meshes[n.mesh].primitives) {
    const pi = p.attributes.POSITION; if (pi === undefined) continue;
    const pos = G.accessor(pi);
    const idx = p.indices !== undefined ? G.accessor(p.indices)
              : Uint32Array.from({length: pos.length / 3}, (_, k) => k);
    for (let t = 0; t + 2 < idx.length; t += 3) {
      const tri = [];
      for (let k = 0; k < 3; k++) { const v = idx[t + k] * 3; tri.push(xf([pos[v], pos[v + 1], pos[v + 2]])); }
      out.push(tri);
    }
  }
  return out;
}
const triBox = (T) => {
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const p of T) for (let k = 0; k < 3; k++) { if (p[k] < lo[k]) lo[k] = p[k]; if (p[k] > hi[k]) hi[k] = p[k]; }
  return {lo, hi};
};

const WALKRE = /^walk/i;
const solids = [], walkUp = [];
for (const {i, name} of G.nodesNamed(/./)) {
  if (J.nodes[i].mesh === undefined) continue;
  const tris = nodeTris(i);
  if (WALKRE.test(name)) {
    for (const T of tris) {
      // up-facing only, the same normal.y > .5 rule play3d's colTops applies
      const u = [T[1][0] - T[0][0], T[1][1] - T[0][1], T[1][2] - T[0][2]];
      const v = [T[2][0] - T[0][0], T[2][1] - T[0][1], T[2][2] - T[0][2]];
      const ny = u[2] * v[0] - u[0] * v[2];
      const nx = u[1] * v[2] - u[2] * v[1], nz = u[0] * v[1] - u[1] * v[0];
      const L = Math.hypot(nx, ny, nz) || 1e-12;
      if (Math.abs(ny / L) <= 0.5) continue;
      walkUp.push({T, b: triBox(T), name});
    }
  } else {
    for (const T of tris) solids.push({T, b: triBox(T), name});
  }
}

// ---- broadphase: a uniform xz grid over both sets ----------------------------
const CELL = 1.5;
const key = (x, z) => `${Math.floor(x / CELL)},${Math.floor(z / CELL)}`;
function indexOf(list) {
  const m = new Map();
  for (const it of list) {
    for (let cx = Math.floor(it.b.lo[0] / CELL); cx <= Math.floor(it.b.hi[0] / CELL); cx++)
      for (let cz = Math.floor(it.b.lo[2] / CELL); cz <= Math.floor(it.b.hi[2] / CELL); cz++) {
        const k = `${cx},${cz}`;
        if (!m.has(k)) m.set(k, []);
        m.get(k).push(it);
      }
  }
  return m;
}
const SIDX = indexOf(solids), WIDX = indexOf(walkUp);
const around = (idx, x0, x1, z0, z1) => {
  const out = [];
  for (let cx = Math.floor(x0 / CELL); cx <= Math.floor(x1 / CELL); cx++)
    for (let cz = Math.floor(z0 / CELL); cz <= Math.floor(z1 / CELL); cz++) {
      const l = idx.get(`${cx},${cz}`); if (l) out.push(...l);
    }
  return out;
};

// point-in-triangle in xz, and the plane height there
function triY(T, x, z) {
  const [A, B, C] = T;
  const d = (B[2] - C[2]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[2] - C[2]);
  if (Math.abs(d) < 1e-12) return null;
  const l1 = ((B[2] - C[2]) * (x - C[0]) + (C[0] - B[0]) * (z - C[2])) / d;
  const l2 = ((C[2] - A[2]) * (x - C[0]) + (A[0] - C[0]) * (z - C[2])) / d;
  const l3 = 1 - l1 - l2;
  const E = -1e-6;
  if (l1 < E || l2 < E || l3 < E) return null;
  return l1 * A[1] + l2 * B[1] + l3 * C[1];
}
function walkTops(x, z) {
  const ys = [];
  for (const it of around(WIDX, x, x, z, z)) {
    if (x < it.b.lo[0] || x > it.b.hi[0] || z < it.b.lo[2] || z > it.b.hi[2]) continue;
    const y = triY(it.T, x, z); if (y !== null) ys.push(y);
  }
  return ys.sort((a, b) => b - a);
}
// play3d's walkGround: the highest walk top inside [fy - WIN_DN, fy + WIN_UP]
function walkGround(x, z, fy) {
  for (const y of walkTops(x, z)) if (y <= fy + WIN_UP && y >= fy - WIN_DN) return y;
  return null;
}

// ---- exact triangle vs axis-aligned box (SAT). A conservative AABB test would --
// over-report, and a gate that cries wolf is a gate people switch off.
function triBoxHit(T, lo, hi) {
  const c = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2];
  const e = [(hi[0] - lo[0]) / 2, (hi[1] - lo[1]) / 2, (hi[2] - lo[2]) / 2];
  const v = T.map((p) => [p[0] - c[0], p[1] - c[1], p[2] - c[2]]);
  for (let k = 0; k < 3; k++) {
    const mn = Math.min(v[0][k], v[1][k], v[2][k]), mx = Math.max(v[0][k], v[1][k], v[2][k]);
    if (mn > e[k] || mx < -e[k]) return false;
  }
  const f = [[v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]],
             [v[2][0] - v[1][0], v[2][1] - v[1][1], v[2][2] - v[1][2]],
             [v[0][0] - v[2][0], v[0][1] - v[2][1], v[0][2] - v[2][2]]];
  const n = [f[0][1] * f[1][2] - f[0][2] * f[1][1],
             f[0][2] * f[1][0] - f[0][0] * f[1][2],
             f[0][0] * f[1][1] - f[0][1] * f[1][0]];
  const d = n[0] * v[0][0] + n[1] * v[0][1] + n[2] * v[0][2];
  if (Math.abs(d) > e[0] * Math.abs(n[0]) + e[1] * Math.abs(n[1]) + e[2] * Math.abs(n[2])) return false;
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
    const a = [0, 0, 0]; a[j] = 1;
    const ax = [a[1] * f[i][2] - a[2] * f[i][1], a[2] * f[i][0] - a[0] * f[i][2], a[0] * f[i][1] - a[1] * f[i][0]];
    const r = e[0] * Math.abs(ax[0]) + e[1] * Math.abs(ax[1]) + e[2] * Math.abs(ax[2]);
    let p0 = Infinity, p1 = -Infinity;
    for (const q of v) { const p = ax[0] * q[0] + ax[1] * q[1] + ax[2] * q[2]; p0 = Math.min(p0, p); p1 = Math.max(p1, p); }
    if (p0 > r || p1 < -r) return false;
  }
  return true;
}
function boxSolid(lo, hi) {
  for (const it of around(SIDX, lo[0], hi[0], lo[2], hi[2])) {
    if (it.b.hi[0] < lo[0] || it.b.lo[0] > hi[0] || it.b.hi[1] < lo[1] || it.b.lo[1] > hi[1]
        || it.b.hi[2] < lo[2] || it.b.lo[2] > hi[2]) continue;
    if (triBoxHit(it.T, lo, hi)) return it.name;
  }
  return null;
}

// ---- the sweep ---------------------------------------------------------------
// Samples are a LATTICE snapped to `step`, so the same physical point is one sample no
// matter which walk polygon it belongs to — sampling per polygon would test the seams
// between two treads twice and the middle of a wide deck not at all.
const inRegion = (x, z) => !REGION || (x >= REGION[0] && x <= REGION[1] && z >= REGION[2] && z <= REGION[3]);
const samples = new Map();
for (const it of walkUp) {
  for (let ix = Math.ceil(it.b.lo[0] / STEP); ix * STEP <= it.b.hi[0]; ix++)
    for (let iz = Math.ceil(it.b.lo[2] / STEP); iz * STEP <= it.b.hi[2]; iz++) {
      const x = ix * STEP, z = iz * STEP;
      if (!inRegion(x, z)) continue;
      if (triY(it.T, x, z) === null) continue;
      samples.set(`${ix},${iz}`, [x, z]);
    }
}
const DIRS = [[STEP, 0], [-STEP, 0], [0, STEP], [0, -STEP]];
const blockedBy = new Map();          // object name -> {n, examples[]}
let nSteps = 0, nBlocked = 0, nSamples = 0, nStuck = 0;
const blockedList = [];
for (const [, [x, z]] of samples) {
  for (const gA of walkTops(x, z)) {
    nSamples++;
    let out = 0, bad = 0;
    for (const [dx, dz] of DIRS) {
      const nx = x + dx, nz = z + dz;
      const gB = walkGround(nx, nz, gA);
      if (gB === null) continue;                 // no legal destination: an edge, not a wall
      out++; nSteps++;
      const y0 = Math.max(gB + STEP_UP + 0.02, gA + 0.02), y1 = gB + BODY_H;
      if (y1 <= y0) continue;
      const hit = boxSolid([nx - BODY_R, y0, nz - BODY_R], [nx + BODY_R, y1, nz + BODY_R]);
      if (!hit) continue;
      bad++; nBlocked++;
      const e = blockedBy.get(hit) || {n: 0, examples: []};
      e.n++;
      if (e.examples.length < 4) e.examples.push({from: [+x.toFixed(2), +gA.toFixed(2), +z.toFixed(2)],
                                                 to: [+nx.toFixed(2), +gB.toFixed(2), +nz.toFixed(2)]});
      blockedBy.set(hit, e);
      blockedList.push({at: [+x.toFixed(2), +gA.toFixed(2), +z.toFixed(2)],
                        to: [+nx.toFixed(2), +gB.toFixed(2), +nz.toFixed(2)], by: hit});
    }
    if (out > 0 && bad === out) nStuck++;
  }
}

console.log(`\nWALK BODY GATE — ${SCENE}, lattice ${STEP} m, body ${BODY_R * 2} m x ${BODY_H} m, ` +
            `STEP_UP ${STEP_UP} / STEP_DN ${STEP_DN}` + (REGION ? `, region ${REGION.join(',')}` : ''));
console.log(`  ${walkUp.length} up-facing walk triangles, ${solids.length} solid triangles`);
console.log(`  ${nSamples} standing samples, ${nSteps} legal steps tested`);
console.log(`  ${nBlocked} steps blocked by a solid (${(100 * nBlocked / Math.max(nSteps, 1)).toFixed(2)}%)`);
console.log(`  ${nStuck} samples where EVERY outgoing step is blocked (the walker cannot slide out)`);
if (blockedBy.size) {
  console.log('\n  blocked steps by object:');
  for (const [name, e] of [...blockedBy].sort((a, b) => b[1].n - a[1].n))
    console.log(`    ${String(e.n).padStart(5)}  ${name.padEnd(34)} e.g. ${JSON.stringify(e.examples[0].from)} -> ${JSON.stringify(e.examples[0].to)}`);
} else console.log('\n  nothing blocks a step anywhere in range.');
if (OUTJSON) {
  fs.writeFileSync(OUTJSON, JSON.stringify({scene: SCENE, step: STEP, region: REGION,
    body: {BODY_R, BODY_H, STEP_UP, STEP_DN}, nSamples, nSteps, nBlocked, nStuck,
    byObject: Object.fromEntries([...blockedBy].map(([k, v]) => [k, v])),
    blocked: blockedList}, null, 1) + '\n');
  console.log(`\n  wrote ${OUTJSON}`);
}
if (MAXB !== null) {
  const ok = nBlocked <= MAXB;
  console.log(`\n${ok ? 'PASS' : 'FAIL'}  ${nBlocked} blocked steps against a budget of ${MAXB}`);
  process.exit(ok ? 0 : 1);
}
