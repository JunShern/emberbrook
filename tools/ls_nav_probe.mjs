#!/usr/bin/env node
// ls_nav_probe.mjs — WHY A FLIGHT OF STAIRS IS HARD TO WALK DOWN, measured offline.
//
//     node tools/ls_nav_probe.mjs                 # the loop stairs (default)
//     node tools/ls_nav_probe.mjs <edgeA> <edgeB> # any two flights leaving one point
//
// WHY THIS EXISTS. The town already had four instruments for "the player cannot get
// down there" and none of them could see this defect:
//
//   cine_solve      says a region is IN FRAME.
//   shot_probe.py   says a walk edge is VISIBLE against the shipped depth plate.
//   nav_eval.mjs    says a naive READING of the plate leaves the shot onward — and it
//                   states in its own header that it does NOT port play3d.html's
//                   body-box blocking, which makes it OPTIMISTIC; its steering also
//                   deliberately compensates for this exact junction (see its FAN
//                   comment), so the walker succeeds where a player does not.
//   master_walk_qa  samples coverage and headroom, not REACHABILITY.
//
// The missing question is the one a player asks with the stick: standing on this
// flight, does play3d.html's `walkGround` keep my foot on it? `walkGround` returns the
// HIGHEST walk surface in the window [fy - STEP_DN - 0.1, fy + STEP_UP + 0.1]. So a
// second ribbon lying up to 0.73 m ABOVE a tread wins that tread — permanently. The
// flight underneath is drawn, lit, framed, visible and unwalkable, and every existing
// gate passes it.
//
// This is the same shape as the gate campaign's finding (`gate_road`'s lip is the
// surface the walker stays on, DAYLOG 2026-07-31 04:2x) with the layers swapped: there
// the intruder was terrain, here it is the neighbouring flight's own top tread.
//
// Reads only the SHIPPED bundle (public/assets/scenes/<walkSceneKey>/scene.glb) and the
// town map. No Blender, no API key, no browser, seconds to run. The browser cross-check
// is `SIM.tpY(x,z,y)` then `SIM.move(dx,0,1)` in play3d.html — same numbers.
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';
import {loadGlb} from './glb_read.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUB = path.join(ROOT, 'public');

// play3d.html's own constants (line 385 / 388). Keep in step or the answer is fiction.
const STEP_UP = 0.63, STEP_DN = 0.8, SPD = 0.075, BODY_R = 0.30, BODY_H = 1.30;
const WINDOW_UP = STEP_UP + 0.1;                 // walkGround's reach ABOVE the foot

// THE LIFT THRESHOLD, and it is the difference between an instrument and an alarm.
// Any two ribbons leaving one pad overlap in plan near that pad; where they are at the
// SAME height there (two flat lanes off a doorstep, a flight's first tread on its own
// landing) walkGround picking either is not a defect — no foot is displaced and the
// player cannot tell. The defect is a foot LIFTED OFF the surface it was on, which
// needs a real height difference. Calibrated on the two towns that exist:
//   dellhollow  shelf-homes       159 cells at 0.360..0.720 m — one to two treads. REAL.
//   emberbrook  hillside-cottage  418 cells at 0.000..0.038 m — coplanar lanes. NOT.
// 0.15 m is half of Dellhollow's 0.32 m riser: under it the lift is smaller than a step
// and invisible; over it the foot has changed surface. A measured floor, not a taste
// call — re-derive it if a town's risers are a different size. Raw overlap is still
// printed, because hiding the count would make the threshold unfalsifiable.
const LIFT_MIN = 0.15;

const TOWN = process.env.LS_TOWN || 'dellhollow';
const MAP = JSON.parse(fs.readFileSync(path.join(PUB, 'townmap', `${TOWN}.map.json`), 'utf8'));
const LM = Object.fromEntries(MAP.landmarks.map((l) => [l.id, l]));
const G = loadGlb(path.join(PUB, 'assets/scenes', MAP.walkSceneKey, 'scene.glb'));
const m2r = (p) => [p[0], p[2], -p[1]];          // map (x, y, height) -> runtime (x, up, -y)

const A_ID = process.argv[2] || 'shelf-homes__quay-deck';
const B_ID = process.argv[3] || 'shelf-homes__market-stalls';

// ---------------------------------------------------------------- geometry ---
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const triOf = (name) => G.tris(new RegExp('^' + esc(name) + '$'));
const CELL = 1.0;
function bucket(tris) {
  const M = new Map();
  tris.forEach((T, k) => {
    const i0 = Math.floor(Math.min(T[0][0], T[1][0], T[2][0]) / CELL), i1 = Math.floor(Math.max(T[0][0], T[1][0], T[2][0]) / CELL);
    const j0 = Math.floor(Math.min(T[0][2], T[1][2], T[2][2]) / CELL), j1 = Math.floor(Math.max(T[0][2], T[1][2], T[2][2]) / CELL);
    for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
      const key = i + ',' + j; let a = M.get(key); if (!a) M.set(key, a = []); a.push(k);
    }
  });
  return M;
}
// play3d.html colTops(): down-ray, keep hits whose normal.y > .5, nearest first.
function topsIn(tris, idx, x, z) {
  const a = idx.get(Math.floor(x / CELL) + ',' + Math.floor(z / CELL)); if (!a) return [];
  const ys = [];
  for (const k of a) {
    const [A, B, C] = tris[k];
    const ux = B[0]-A[0], uy = B[1]-A[1], uz = B[2]-A[2], vx = C[0]-A[0], vy = C[1]-A[1], vz = C[2]-A[2];
    const ny = uz*vx - ux*vz, nl = Math.hypot(uy*vz - uz*vy, ny, ux*vy - uy*vx) || 1e-12;
    if (Math.abs(ny / nl) <= 0.5) continue;
    const d = (B[2]-C[2])*(A[0]-C[0]) + (C[0]-B[0])*(A[2]-C[2]); if (Math.abs(d) < 1e-12) continue;
    const l1 = ((B[2]-C[2])*(x-C[0]) + (C[0]-B[0])*(z-C[2])) / d;
    const l2 = ((C[2]-A[2])*(x-C[0]) + (A[0]-C[0])*(z-C[2])) / d, l3 = 1 - l1 - l2;
    if (l1 < -1e-6 || l2 < -1e-6 || l3 < -1e-6) continue;
    ys.push(l1*A[1] + l2*B[1] + l3*C[1]);
  }
  return ys.sort((p, q) => q - p);
}
// every walk_ ribbon, and the two flights under test, as their own layers
const ALLW = [], ALLN = [];
for (const {name} of G.nodesNamed(/^walk/i)) for (const T of triOf(name)) { ALLW.push(T); ALLN.push(name); }
const ALLI = bucket(ALLW);
const layer = (re) => { const t = [], n = []; for (const {name} of G.nodesNamed(re)) for (const T of triOf(name)) { t.push(T); n.push(name); } return {t, n, i: bucket(t)}; };
const A = layer(new RegExp('^walk_e_' + esc(A_ID)));
const B = layer(new RegExp('^walk_e_' + esc(B_ID)));

function walkGround(x, z, fy) {
  const w = (xx, zz) => { const hi = fy + WINDOW_UP, lo = fy - STEP_DN - 0.1;
    for (const y of topsIn(ALLW, ALLI, xx, zz)) if (y <= hi && y >= lo) return y; return null; };
  let g = w(x, z); if (g != null) return g;
  for (const [ox, oz] of [[0.18,0],[-0.18,0],[0,0.18],[0,-0.18]]) { g = w(x+ox, z+oz); if (g != null) return g; }
  return null;
}
function nameAt(L, x, z, y) {
  const a = L.i.get(Math.floor(x/CELL)+','+Math.floor(z/CELL)); if (!a) return null;
  for (const k of a) { for (const t of topsIn([L.t[k]], new Map([[Math.floor(x/CELL)+','+Math.floor(z/CELL), [0]]]), x, z)) if (Math.abs(t - y) < 1e-3) return L.n[k]; }
  return null;
}

// =============================================================== 1. THE CENSUS
// Every plan cell carrying flight A: is a cell of flight B (or a pad) standing inside
// walkGround's step-up window ABOVE it? Those treads can never be stood on.
console.log(`LOOP-STAIR NAV PROBE — ${TOWN}`);
console.log(`  flight A  ${A_ID}   (${A.t.length} tris)`);
console.log(`  flight B  ${B_ID}   (${B.t.length} tris)`);
console.log(`  play3d.html STEP_UP ${STEP_UP} / STEP_DN ${STEP_DN} -> walkGround reaches ${WINDOW_UP.toFixed(2)} m ABOVE the foot\n`);
console.log('== 1. COVERED-TREAD CENSUS (0.05 m lattice) ==');
let bb = [Infinity, Infinity, -Infinity, -Infinity];
for (const T of A.t) for (const v of T) { bb[0] = Math.min(bb[0], v[0]); bb[1] = Math.min(bb[1], v[2]); bb[2] = Math.max(bb[2], v[0]); bb[3] = Math.max(bb[3], v[2]); }
let cells = 0, covered = 0, lifted = 0, gmin = Infinity, gmax = -Infinity;
let cgmin = Infinity, cgmax = -Infinity;
let px0 = Infinity, px1 = -Infinity, pz0 = Infinity, pz1 = -Infinity;
const byMesh = new Map(), treads = new Map();
for (let x = bb[0]; x <= bb[2]; x += 0.05) for (let z = bb[1]; z <= bb[3]; z += 0.05) {
  const at = topsIn(A.t, A.i, x, z); if (!at.length) continue;
  const ay = at[0]; cells++;
  let hit = null;
  for (const y of topsIn(B.t, B.i, x, z)) if (y > ay + 1e-4 && y <= ay + WINDOW_UP) { hit = ['B', y]; break; }
  if (!hit) continue;
  covered++;
  const cg = hit[1] - ay; if (cg < cgmin) cgmin = cg; if (cg > cgmax) cgmax = cg;
  if (cg < LIFT_MIN) continue;                   // coplanar overlap: no foot is displaced
  lifted++;
  const g = cg; if (g < gmin) gmin = g; if (g > gmax) gmax = g;
  px0 = Math.min(px0, x); px1 = Math.max(px1, x); pz0 = Math.min(pz0, z); pz1 = Math.max(pz1, z);
  const nm = nameAt(B, x, z, hit[1]); if (nm) byMesh.set(nm, (byMesh.get(nm) || 0) + 1);
  const tn = nameAt(A, x, z, ay); if (tn) treads.set(tn, (treads.get(tn) || 0) + 1);
}
console.log(`  flight-A cells sampled                                     ${cells}`);
console.log(`  raw plan overlap inside the step-up window                 ${covered}  (${(100*covered/cells).toFixed(1)}%)` +
            (covered ? `   gap ${cgmin.toFixed(3)}..${cgmax.toFixed(3)} m` : ''));
console.log(`  >>> LIFTED: overlap with a lift >= ${LIFT_MIN.toFixed(2)} m                 ${lifted}  (${(100*lifted/cells).toFixed(1)}%)`);
if (lifted) {
  const pw = px1 - px0 + 0.05, pd = pz1 - pz0 + 0.05;
  console.log(`  lifted patch    x ${px0.toFixed(2)}..${px1.toFixed(2)}   z ${pz0.toFixed(2)}..${pz1.toFixed(2)}   ( = map y ${(-pz1).toFixed(2)}..${(-pz0).toFixed(2)} )`);
  console.log(`  lifted patch    ${pw.toFixed(2)} x ${pd.toFixed(2)} m against a ${(BODY_R*2).toFixed(2)} m body footprint` +
              ` -> ${Math.min(pw, pd) >= BODY_R*2 ? 'A BODY FITS ON IT' : 'SUB-BODY sliver'}`);
  console.log(`  lift            ${gmin.toFixed(3)} .. ${gmax.toFixed(3)} m   against a ${WINDOW_UP.toFixed(2)} m window`);
  console.log('  the covering mesh(es):'); for (const [n, c] of [...byMesh].sort((a, b) => b[1]-a[1])) console.log(`    ${n.padEnd(46)} ${c} cells`);
  console.log('  the treads it makes unstandable:'); for (const [n, c] of [...treads].sort((a, b) => b[1]-a[1])) console.log(`    ${n.padEnd(46)} ${c} cells`);
} else if (covered) {
  console.log(`  none — the ribbons are COPLANAR where they overlap (max lift ${cgmax.toFixed(3)} m,`);
  console.log(`  smaller than half a riser). walkGround picking either displaces no foot.`);
} else console.log('  none — the two flights never share a plan cell.');

// ============================================== 2. THE DESCENT, TREAD BY TREAD
// Stand on flight A's highest tread and push straight down its own line. Print the
// height under the foot at every step and name the ribbon that caught it.
console.log('\n== 2. THE DESCENT (play3d.html walkStep, one 0.075 m step per row) ==');
function edgePts(id) { const [f, t] = id.split('__');
  const e = MAP.edges.find((x) => x.from === f && x.to === t);
  return [LM[f].pos, ...(e.waypoints || []), LM[t].pos].map(m2r); }
const AP = edgePts(A_ID);
// start on A's own topmost tread, on the centre of its first run
let sx = null, sz = null, sy = -Infinity;
for (let x = bb[0]; x <= bb[2]; x += 0.05) for (let z = bb[1]; z <= bb[3]; z += 0.05) {
  const t = topsIn(A.t, A.i, x, z); if (t.length && t[0] > sy) { sy = t[0]; sx = x; sz = z; }
}
const dir = [AP[1][0] - AP[0][0], AP[1][2] - AP[0][2]];
const dl = Math.hypot(dir[0], dir[1]) || 1;
let P = [sx, sy, sz]; let ownA = 0, ownB = 0, ownOther = 0;
console.log(`  start [${sx.toFixed(2)}, ${sy.toFixed(2)}, ${sz.toFixed(2)}] pushing (${(dir[0]/dl).toFixed(2)}, ${(dir[1]/dl).toFixed(2)})`);
console.log('   step      x      up       z   ribbon under the foot');
for (let i = 0; i < 60; i++) {
  const nx = P[0] + dir[0]/dl*SPD, nz = P[2] + dir[1]/dl*SPD;
  const g = walkGround(nx, nz, P[1]); if (g == null) { console.log(`   ${String(i).padStart(4)}  WALKLOCK refuses the step`); break; }
  P = [nx, g, nz];
  const a = nameAt(A, nx, nz, g), b = nameAt(B, nx, nz, g);
  const who = a || b || '(other walk mesh)';
  if (a) ownA++; else if (b) ownB++; else ownOther++;
  if (i < 44) console.log(`   ${String(i).padStart(4)}  ${nx.toFixed(2)}  ${g.toFixed(2)}  ${nz.toFixed(2)}   ${who}${b && !a ? '   <-- THE OTHER FLIGHT' : ''}`);
}
console.log(`  steps landing on flight A ${ownA} · on flight B ${ownB} · elsewhere ${ownOther}`);

// ================================================= 3. THE HELD-HEADING SWEEP
// A player pushes ONE direction. play3d.html has no 3D fan (nav_eval's does, on
// purpose). 72 held headings from a spawn: which flight's foot do they reach?
console.log('\n== 3. HELD-HEADING SWEEP from the shot arrival ==');
const CAMS = JSON.parse(fs.readFileSync(path.join(PUB, 'townmap', `${TOWN}.cameras.solved.json`), 'utf8'));
const AUTH = JSON.parse(fs.readFileSync(path.join(PUB, 'townmap', `${TOWN}.cameras.json`), 'utf8'));
const cut = CAMS.cuts.find((c) => c.edge === A_ID) || CAMS.cuts.find((c) => c.edge === B_ID);
// the point the player is actually PUT at when the shot opens: the owning camera's
// authored arrival override if it has one, else the seam's own spawn.
const own = AUTH.cameras.find((c) => ((c.owns || {}).edges || []).includes(A_ID));
const arr = (own && own.arrivals) ? Object.values(own.arrivals)[0] : null;
const spawn = arr || (cut ? cut.spawnFrom : null);
const footA = (CAMS.cuts.find((c) => c.edge === A_ID) || {}).spawnTo;
const footB = (CAMS.cuts.find((c) => c.edge === B_ID) || {}).spawnTo;
if (!spawn || !footA || !footB) { console.log('  (no arrival / seam spawns in the solved file — skipped)'); }
else {
  const d3 = (p, q) => Math.hypot(p[0]-q[0], p[1]-q[1], p[2]-q[2]);
  let nA = 0, nB = 0, cA = Infinity, cB = Infinity;
  for (let deg = 0; deg < 360; deg += 5) {
    const a = deg * Math.PI/180;
    let Q = spawn.slice(); const g0 = walkGround(Q[0], Q[2], Q[1]); if (g0 != null) Q[1] = g0;
    let stall = 0, hitA = false, hitB = false;
    for (let t = 0; t < 900; t++) {
      let moved = false;
      for (const [mx, mz] of [[Math.cos(a)*SPD, Math.sin(a)*SPD], [Math.cos(a)*SPD, 0], [0, Math.sin(a)*SPD]]) {
        if (!mx && !mz) continue;
        const g = walkGround(Q[0]+mx, Q[2]+mz, Q[1]); if (g == null) continue;
        Q = [Q[0]+mx, g, Q[2]+mz]; moved = true; break;
      }
      if (!moved) { if (++stall > 20) break; } else stall = 0;
      const dA = d3(Q, footA), dB = d3(Q, footB);
      if (dA < cA) cA = dA; if (dB < cB) cB = dB;
      if (dA < 1.0) hitA = true; if (dB < 1.0) hitB = true;
    }
    if (hitA) nA++; if (hitB) nB++;
  }
  console.log(`  spawn [${spawn.map((v) => v.toFixed(2)).join(', ')}]`);
  console.log(`  headings that reach flight A's foot [${footA.map((v) => v.toFixed(2)).join(', ')}]  ${nA}/72   closest approach ${cA.toFixed(2)} m`);
  console.log(`  headings that reach flight B's foot [${footB.map((v) => v.toFixed(2)).join(', ')}]  ${nB}/72   closest approach ${cB.toFixed(2)} m`);
  // WHAT THIS SWEEP CAN AND CANNOT PROVE — read this before treating 0/72 as a verdict.
  // A HELD heading is a fair test only where the route is a straight push: two flights
  // leaving ONE point, where the question is "does the obvious shove get me down the one
  // I aimed at". Where the route FORKS — down a shared flight, then a turn onto a branch
  // — no single heading can execute it, and 0/72 means "this descent needs steering",
  // which is a fact about the shape, not a defect. That is exactly what happened here:
  // pre-fix the two flights shared an origin and 0/72 was damning; post-fix the route
  // turns ~117 deg at the landing and 0/72 is expected. §2's descent trace and
  // tools/seam_walk.mjs's scripted journeys are the functional gate for a forked route.
  const sharedOrigin = A_ID.split('__')[0] === B_ID.split('__')[0];
  console.log(`  the two flights share an origin: ${sharedOrigin ? 'YES — a held heading IS a fair gate here' :
    'NO — this descent FORKS, so no held heading can walk it; 0/72 is expected, not a failure.\n' +
    '     Use §2 and tools/seam_walk.mjs for a forked route.'}`);
}

// ======================================================= 4. THE YARD'S BUDGET
// Two flights can only leave one pad side by side if the pad is as wide as both.
console.log('\n== 4. DOES THE JUNCTION PAD HAVE THE WIDTH FOR TWO FLIGHT HEADS? ==');
const junction = A_ID.split('__')[0];
const padT = triOf(`walk_pad_${junction}`);
const ext = (t) => { const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const T of t) for (const v of T) for (let k = 0; k < 3; k++) { if (v[k] < lo[k]) lo[k] = v[k]; if (v[k] > hi[k]) hi[k] = v[k]; } return {lo, hi}; };
function headWidth(L) {                        // the widest single mesh at the flight's top
  let best = null, by = -Infinity;
  for (const {name} of G.nodesNamed(new RegExp('^walk_e_' + esc(L)))) {
    const e = ext(triOf(name)); if (e.hi[1] > by) { by = e.hi[1]; best = {name, e}; } }
  return best;
}
const hA = headWidth(A_ID), hB = headWidth(B_ID);
if (padT.length && hA && hB) {
  const p = ext(padT);
  const wA = hA.e.hi[2] - hA.e.lo[2], wB = hB.e.hi[2] - hB.e.lo[2];
  const padW = p.hi[2] - p.lo[2], padL = p.hi[0] - p.lo[0];
  console.log(`  walk_pad_${junction}  ${padL.toFixed(2)} x ${padW.toFixed(2)} m   (x ${p.lo[0].toFixed(2)}..${p.hi[0].toFixed(2)}, z ${p.lo[2].toFixed(2)}..${p.hi[2].toFixed(2)})`);
  console.log(`  A head  ${hA.name}  ${wA.toFixed(2)} m wide`);
  console.log(`  B head  ${hB.name}  ${wB.toFixed(2)} m wide`);
  console.log(`  two heads need ${(wA+wB).toFixed(2)} m of pad across; the pad has ${padW.toFixed(2)} m` +
              `  -> ${(padW-wA-wB) >= 0 ? 'FITS by ' + (padW-wA-wB).toFixed(2) : 'SHORT by ' + (wA+wB-padW).toFixed(2)} m` +
              ` (before any margin between them)`);
}
// the map's own arithmetic: two edges leaving one landmark
console.log('\n== 5. THE MAP LINES THAT PRODUCE IT ==');
const geom = [];
for (const id of [A_ID, B_ID]) {
  const [f, t] = id.split('__');
  const e = MAP.edges.find((x) => x.from === f && x.to === t);
  if (!e) { console.log(`  ${id.padEnd(30)} NOT IN THE MAP (stale id?)`); continue; }
  const pts = [LM[f].pos, ...(e.waypoints || []), LM[t].pos];
  const a = pts[0], b = pts[1];
  const run = Math.hypot(b[0]-a[0], b[1]-a[1]), fall = a[2]-b[2];
  const grad = Math.atan2(fall, run)*180/Math.PI, bear = Math.atan2(b[1]-a[1], b[0]-a[0])*180/Math.PI;
  geom.push({id, from: f, grad, bear});
  console.log(`  ${id.padEnd(30)} first leg ${run.toFixed(3)} m of ground for ${fall.toFixed(3)} m of fall` +
              `  = ${grad.toFixed(1)} deg,  plan bearing ${bear.toFixed(2)} deg`);
}
// THE VERDICT IS DERIVED, NOT PRINTED FROM A SCRIPT. An earlier version of this tool
// ended with a fixed paragraph asserting a stair story; run on two flat lanes it
// asserted it anyway. A conclusion that cannot come out false is not a finding.
if (geom.length === 2) {
  let db = Math.abs(geom[0].bear - geom[1].bear); if (db > 180) db = 360 - db;
  const dg = Math.abs(geom[0].grad - geom[1].grad);
  const shared = geom[0].from === geom[1].from;
  const RIB = 1.4;
  console.log(`  bearing divergence ${db.toFixed(2)} deg · gradient difference ${dg.toFixed(2)} deg` +
              ` · shared origin: ${shared ? 'YES (' + geom[0].from + ')' : 'no'}`);
  // THE FORK ARITHMETIC ONLY MEANS ANYTHING FOR A SHARED ORIGIN. Comparing the first
  // legs of two edges that start in different places measures nothing — an earlier
  // version printed a "2x margin" for exactly that case and then a DEFECT verdict off
  // the back of it. When the origins differ, the census IS the answer.
  if (shared && db > 1e-3) {
    const sep = RIB / Math.sin(db*Math.PI/180);
    const dh = sep * Math.abs(Math.tan(geom[0].grad*Math.PI/180) - Math.tan(geom[1].grad*Math.PI/180));
    console.log(`  two ${RIB} m ribbons clear each other in plan ${sep.toFixed(2)} m from the fork;` +
                ` by then their heights differ by ${dh.toFixed(3)} m`);
    console.log(`  -> headroom against walkGround's ${WINDOW_UP.toFixed(2)} m window: ` +
                (dh > 1e-6 ? `${(WINDOW_UP/dh).toFixed(0)}x` : 'unbounded (identical gradients)'));
  } else if (!shared) {
    console.log('  (the two edges do not share an origin — no fork arithmetic applies;');
    console.log('   the census and the descent above are the whole answer)');
  }
  // THE VERDICT IS THREE-STATE, because "lifted cells > 0" is not the same claim as
  // "a player loses the flight". walkGround is a POINT test, so a sliver narrower than
  // the body can still lift a foot whose centre crosses it — but it cannot be stood on,
  // and whether any walkable line crosses it is what §2 and §3 measure.
  const bodyFits = lifted && Math.min(px1-px0+0.05, pz1-pz0+0.05) >= BODY_R*2;
  if (lifted && bodyFits) {
    console.log('  VERDICT: DEFECT. A body-sized patch of flight A is lifted onto flight B.');
    console.log('  If the two edges share an origin this is a MAP fact (CLAUDE.md: "a conflict');
    console.log('  fix is a landmark move or a lane waypoint") — not something a district');
    console.log('  builder or a camera can undo.');
  } else if (lifted) {
    console.log(`  VERDICT: MARGINAL. ${lifted} lifted cells, but the patch is narrower than the`);
    console.log('  body — no one can stand on it. Read §2 and §3: if the descent stays on');
    console.log('  flight A and the sweep reaches its foot, the flight is walkable and this');
    console.log('  is a nosing overlap to note, not a defect to spend a rebuild on.');
  } else {
    console.log('  VERDICT: CLEAN. No tread of either flight is lifted off by the other.');
  }
}
