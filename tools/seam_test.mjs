// seam_test.mjs — THE SEAM GATE. Prove that a cinematic town's camera cuts are
// where a player expects them, that there is never more than one per passage, and
// that no cut can fire twice, backwards, or on somebody else's path.
//
//   node tools/seam_test.mjs                     assert dellhollow, print the report
//   node tools/seam_test.mjs --town emberbrook   any town with a <town>.cameras.json
//   node tools/seam_test.mjs --cameras <rel>     solve a PROPOSED camera file instead
//                                                (path relative to public/)
//   node tools/seam_test.mjs --verbose           print every passage, not only failures
//
// WHY THIS EXISTS. cine_test.mjs proves the town is COVERED and REACHABLE: every
// walk mesh has an owner, every arrival is on screen, the graph is connected. All of
// that was green on 2026-07-30 while a player walking the town hit, within one hour:
// a camera that changed three times on one small bridge (and, walking it westward,
// changed FOREVER — a 30-cut strobe reproduced headlessly below); a stair whose
// camera cut fired mid-flight and teleported him 3.6 m down the steps; and a quay
// junction where three shots met inside eight metres. Coverage was never the
// problem. WHERE THE SEAMS SIT was, and nothing measured it.
//
// So this gate measures the thing the player actually experiences — the sequence of
// camera changes produced by WALKING — instead of the ownership table that implies
// it. Its simulation is a line-by-line mirror of play3d.html's sgTick() + sgCorrect()
// (band test, arm/disarm, camera gating, the 20-tick positional correction), so a
// green run here is a claim about the runtime and not about a model of it.
//
// The invariants are written up, with the live failure that motivated each, in
// docs/plans/seam-canon.md. This file is that document's enforcement.
import fs from 'fs';
import path from 'path';
import {loadCine, walkMeshes, ownerOfWalk, cutGeometry, shotRegions, derivedCuts,
        edgePoint, edgeDir, m2r, PUB} from './cine_regions.mjs';

const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const TOWN = opt('--town', 'dellhollow');
const VERBOSE = ARGS.includes('--verbose');
const CAMREL = opt('--cameras', `townmap/${TOWN}.cameras.json`);

let pass = 0, fail = 0, warnN = 0;
const ok = (c, m, extra) => { if (c) { pass++; if (VERBOSE) console.log('  ok   ' + m); }
  else { fail++; console.log('  FAIL ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
const soft = (c, m, extra) => { if (c) pass++; else { warnN++;
  console.log('  warn ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
const head = (s) => console.log('\n== ' + s);

// ---------------------------------------------------------------- THE NUMBERS --
// Every threshold this gate enforces, in one place, so arguing with the gate is
// arguing with a number and not with a code path.
const RULE = {
  arrivalFloor: 0.5,      // m past the band a cut's arrival must land (NO-RETURN).
                          // cutClearance is the TARGET; this is the hard floor, one
                          // stride, below which the player can walk straight back
                          // into the band that just fired.
  cutsPerPassage: 1,      // camera changes while walking one map edge, end to end.
  correctionsAllowed: 0,  // the positional safety net firing on a NORMAL route means
                          // a seam is in the wrong place; it exists for falls, not walks.
  minRouteMetres: 10,     // a shot must own this much walkable route (NO SLIVER).
  // MISMATCH is not free to drive to zero: cutOffset puts every endpoint seam that
  // many metres out from the pad ON PURPOSE, so a town's floor is 2.8 m x (endpoint
  // cuts) mismatched by construction. The budget is therefore DERIVED from the town's
  // own cutOffset with an allowance for seams the geometry forces to slide further,
  // not a number somebody liked. See mismatchBudget() below.
  mismatchSlack: 1.45,    // x the unavoidable minimum, town-wide
  mismatchStretch: 7,     // and no single stretch longer than this (a switchback's
                          // seam legitimately slides most of a leg to find clean ground).
  // The physics the simulation replays. These MUST match play3d.html.
  SPD: 0.075, GRACE: 20, CPAD: 0.6, CVTOL: 1.2, CREACH: 12,
};

// ------------------------------------------------------------------- the town --
const C = loadCine(`townmap/${TOWN}.map.json`, CAMREL);
const WALKGLB = path.join(PUB, 'assets/scenes',
  (C.map.walkSceneKey || C.camFile.sceneKey), 'scene.glb');
const {meshes} = walkMeshes(WALKGLB);
for (const m of meshes) m.owner = ownerOfWalk(C, m.name, m.center).cam;
const CUTWARN = [];
const CG = cutGeometry(C, WALKGLB, (m) => CUTWARN.push(m));
const REG = shotRegions(C, WALKGLB, meshes);
const REGBY = Object.fromEntries(REG.map((r) => [r.id, r]));
const walkY = CG.walkY;

console.log(`seam gate — town '${TOWN}', ${C.cams.length} shots, ${CG.cuts.length} seams, ` +
            `${meshes.length} walk meshes  (cameras: ${CAMREL})`);
ok(C.warn.length === 0, `camera ownership is well-formed (${C.warn.length} problems)`, C.warn.slice(0, 4));

// ============================================ THE RUNTIME, REPLAYED =============
// A line-by-line mirror of play3d.html. If these two drift the gate is worthless, so
// they are commented with the runtime's own function names.
const EDGES = [];
for (const c of CG.cuts) {
  EDGES.push({id: `${c.from}>${c.to}@${c.edge}`, camFrom: c.from, cam: c.to,
              at: c.at, band: c.band, spawn: c.spawnTo, vTol: c.vTol, edge: c.edge});
  EDGES.push({id: `${c.to}>${c.from}@${c.edge}`, camFrom: c.to, cam: c.from,
              at: c.at, band: c.band, spawn: c.spawnFrom, vTol: c.vTol, edge: c.edge});
}
function sgHit(e, P) {                                   // play3d.html sgHit()
  const dy = Math.abs(P[1] - e.at[1]);
  const px = P[0] - e.at[0], pz = P[2] - e.at[2];
  const along = px * e.band.n[0] + pz * e.band.n[1];
  const across = -px * e.band.n[1] + pz * e.band.n[0];
  const ax = Math.max(0, Math.abs(across) - e.band.w);
  return {d: Math.hypot(along, ax), along, across, dy,
          in: Math.abs(along) <= e.band.t && Math.abs(across) <= e.band.w && dy <= e.vTol};
}
function sgRegionsFor(P, camId) {                        // play3d.html sgRegionsFor()
  let own = false, other = null, bd = Infinity;
  for (const r of REG) {
    for (const b of r.boxes) {
      if (P[0] < b[0] - RULE.CPAD || P[0] > b[2] + RULE.CPAD ||
          P[2] < b[1] - RULE.CPAD || P[2] > b[3] + RULE.CPAD) continue;
      const dy = Math.abs(P[1] - b[4]);
      if (dy > RULE.CVTOL) continue;
      if (r.id === camId) { own = true; break; }
      if (dy < bd) { bd = dy; other = r.id; }
    }
    if (own) break;
  }
  if (own || other) return {own, other};
  let nid = null, nd = Infinity;
  for (const r of REG) for (const b of r.boxes) {
    const dx = Math.max(b[0] - P[0], 0, P[0] - b[2]);
    const dz = Math.max(b[1] - P[2], 0, P[2] - b[3]);
    const d = Math.sqrt(dx * dx + dz * dz + (P[1] - b[4]) ** 2);
    if (d < nd) { nd = d; nid = r.id; }
  }
  if (nid === null || nd > RULE.CREACH) return {own: false, other: null};
  return {own: nid === camId, other: nid};
}
function mkPath(pts) {
  const cum = [0];
  for (let i = 0; i < pts.length - 1; i++)
    cum.push(cum[i] + Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][2] - pts[i][2]));
  const L = cum[cum.length - 1];
  const at = (s) => { s = Math.max(0, Math.min(L, s));
    for (let i = 0; i < cum.length - 1; i++) if (s <= cum[i + 1] || i === cum.length - 2) {
      const seg = cum[i + 1] - cum[i], f = seg < 1e-9 ? 0 : (s - cum[i]) / seg;
      const a = pts[i], b = pts[i + 1];
      return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
    } return pts[0].slice(); };
  const proj = (p) => { let bs = 0, bd = Infinity;
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], b = pts[i + 1];
      const vx = b[0] - a[0], vz = b[2] - a[2], vv = vx * vx + vz * vz;
      let f = vv < 1e-12 ? 0 : ((p[0] - a[0]) * vx + (p[2] - a[2]) * vz) / vv;
      f = Math.max(0, Math.min(1, f));
      const d = Math.hypot(p[0] - (a[0] + vx * f), p[2] - (a[2] + vz * f));
      if (d < bd) { bd = d; bs = cum[i] + Math.hypot(vx, vz) * f; }
    } return bs; };
  return {at, proj, L};
}
// Walk a polyline at the runtime's own speed and return the camera changes it makes.
// `standStill` is the half-second a real player spends deciding at the far end: the
// positional correction counts TICKS, not metres, so a route that only just outruns
// it is not actually safe.
function simWalk(pts, startCam) {
  const P0 = mkPath(pts);
  let cam = startCam, corrTicks = 0, corrLast = null, s = 0, steps = 0, runaway = false;
  const armed = new Map(); for (const e of EDGES) armed.set(e.id, null);
  const events = [];
  let P = P0.at(0); const y0 = walkY(P[0], P[2], P[1]); if (y0 != null) P[1] = y0;
  const tick = () => {
    let fire = null;
    for (const e of EDGES) {
      if (e.camFrom !== cam) continue;                          // CAMERA GATING
      const h = sgHit(e, P);
      if (armed.get(e.id) === null) { armed.set(e.id, !h.in); continue; }  // ARRIVAL SUPPRESSION
      if (!h.in) { armed.set(e.id, true); continue; }
      if (!armed.get(e.id)) continue;
      if (!fire || h.d < fire.h.d) fire = {e, h};
    }
    if (fire) {
      events.push({kind: 'cut', from: cam, to: fire.e.cam, edge: fire.e.edge,
                   at: P.map((v) => +v.toFixed(2))});
      cam = fire.e.cam; P = fire.e.spawn.slice();
      const y = walkY(P[0], P[2], P[1]); if (y != null) P[1] = y;
      s = P0.proj(P);
      for (const e of EDGES) armed.set(e.id, null);
      corrTicks = 0; corrLast = null; return;
    }
    const r = sgRegionsFor(P, cam);
    if (r.own || !r.other) { corrTicks = 0; corrLast = null; return; }
    if (corrLast !== r.other) { corrLast = r.other; corrTicks = 0; }
    if (++corrTicks < RULE.GRACE) return;
    corrTicks = 0;
    events.push({kind: 'correction', from: cam, to: r.other, at: P.map((v) => +v.toFixed(2))});
    cam = r.other;
    for (const e of EDGES) armed.set(e.id, null);
  };
  tick();
  while (s < P0.L - RULE.SPD) {
    if (++steps > 40000 || events.length > 40) { runaway = true; break; }
    s += RULE.SPD;
    const q = P0.at(s);
    const dx = q[0] - P[0], dz = q[2] - P[2], L = Math.hypot(dx, dz);
    if (L > 1e-9) { const k = Math.min(1, RULE.SPD / L); P[0] += dx * k; P[2] += dz * k; }
    // Snap to the walk surface nearest the ROUTE's own height, not the height we
    // happened to be at last tick. On a stacked switchback the two legs pass within
    // a metre of each other in plan, and carrying the previous height forward pins
    // the walker to the leg below — which reads as a missed cut that the real player,
    // who is demonstrably on the upper leg, never misses. The route is the authority
    // on which leg you are on; the mesh is the authority on its exact height.
    const y = walkY(P[0], P[2], q[1]); if (y != null) P[1] = y;
    tick();
  }
  for (let i = 0; i < 60 && !runaway && events.length <= 40; i++) tick();   // stand still 1 s
  return {events, end: cam, runaway,
          cuts: events.filter((e) => e.kind === 'cut').length,
          corr: events.filter((e) => e.kind === 'correction').length};
}
// dense runtime polyline along a map edge
function edgePath(E, back) {
  const N = Math.max(10, Math.ceil(E.L * 6)), out = [];
  for (let i = 0; i <= N; i++) { const t = i / N; out.push(m2r(edgePoint(E, back ? 1 - t : t))); }
  return out;
}
// which shot owns the ground at a runtime point (for choosing a walk's start shot)
const shotAtPoint = (p) => { const r = sgRegionsFor(p, null); return r.other; };

// ======================================== 1. NO-RETURN (arrival clearance) ======
// MOTIVATED BY: the deep-stairs<->waterfront progression loop the user hit live on
// 2026-07-30 — the arrival sat +0.012 u past its own band on a switchback, so walking
// on re-entered the band and cut straight back. cutClearance 1.0->1.6 (eabb63b) moved
// the solver's TARGET; this asserts the RESULT, per seam, in metres, because a target
// the geometry cannot satisfy is silently downgraded to an arc-length fallback.
head('NO-RETURN — every arrival lands clear of the band it just crossed');
for (const c of CG.cuts) {
  for (const [side, spawn] of [['->' + c.to, c.spawnTo], ['->' + c.from, c.spawnFrom]]) {
    const h = sgHit({at: c.at, band: c.band, vTol: c.vTol}, spawn);
    const margin = +(Math.abs(h.along) - c.band.t).toFixed(3);
    const clearInHeight = h.dy - c.vTol;
    const best = Math.max(margin, +clearInHeight.toFixed(3));
    ok(best >= RULE.arrivalFloor,
       `${c.from}<->${c.to} on ${c.edge}${side}: arrival is ${best.toFixed(2)} m clear ` +
       `(floor ${RULE.arrivalFloor}, target ${C.D.cutClearance})`,
       best < RULE.arrivalFloor ? {at: c.at, spawn, along: +h.along.toFixed(2), dy: +h.dy.toFixed(2)} : undefined);
  }
}

// ================================== 2. ONE-CUT-PER-PASSAGE (the simulated walk) ==
// MOTIVATED BY: "there are too many transitions as I'm walking on this one small
// bridge" and "I keep accidentally triggering scene changes between the 3
// unexpectedly". Both are invisible to an ownership check and obvious to a walk.
// A passage is one map edge, end to end, in one direction — the smallest unit of
// travel the town's own topology defines.
//
// THRESHOLD PAIRS: a shot that IS a place you enter and leave (a bridge, a tunnel)
// legitimately costs two cuts. It gets them only by declaring `"thresholdPair": true`
// on the camera record, and only when both its seams sit at the span's abutments.
head('ONE-CUT-PER-PASSAGE — walking any map edge changes the camera at most once');
const passages = [];
for (const k of Object.keys(C.MEDGE)) {
  const E = C.MEDGE[k];
  if (!CG.ribbons.has(k)) continue;                    // no walk ribbon: not walkable
  for (const back of [false, true]) {
    const pts = edgePath(E, back);
    const start = shotAtPoint(pts[0]);
    if (!start) continue;
    const r = simWalk(pts, start);
    // A threshold pair is spent ONLY on entering and leaving the SAME declared shot,
    // by the seams of the edge you are actually walking. Without both conditions the
    // allowance launders unrelated defects: walking the quay's west arm out to the
    // stair head fired the DEEP STAIRS' seam and fired straight back, and 'the deep
    // stairs are a threshold pair' would have excused it.
    const cuts = r.events.filter((e) => e.kind === 'cut');
    const paired = cuts.length === 2 && cuts[0].to === cuts[1].from &&
                   cuts.every((e) => e.edge === k) && (C.byId[cuts[0].to] || {}).thresholdPair;
    const allow = RULE.cutsPerPassage + (paired ? 1 : 0);
    passages.push({edge: k, back, ...r, allow});
    const name = `${k}${back ? ' (reversed)' : ''}`;
    ok(!r.runaway, `${name}: does not oscillate`,
       r.runaway ? r.events.slice(0, 6) : undefined);
    if (!r.runaway) {
      ok(r.cuts <= allow, `${name}: ${r.cuts} camera cut(s) (max ${allow})`,
         r.cuts > allow ? r.events.filter((e) => e.kind === 'cut') : undefined);
      ok(r.corr <= RULE.correctionsAllowed,
         `${name}: ${r.corr} positional correction(s) (max ${RULE.correctionsAllowed})`,
         r.corr > RULE.correctionsAllowed ? r.events.filter((e) => e.kind === 'correction') : undefined);
    }
  }
}

// ================================================= 3. NO SLIVER SHOTS ===========
// MOTIVATED BY: quay-east owned two walk meshes and 12.1 m of route, and BOTH of its
// meshes overlapped the harbour deck's own pad — it was a second camera on somebody
// else's floor, and it produced a user complaint within an hour of real play. The
// test is deliberately in METRES OF ROUTE and EXCLUSIVE FLOOR, not mesh count: the
// Crossing owns three meshes and 21.5 m of bridge that nothing else touches, and it
// is a real place.
head('NO SLIVER SHOTS — every camera owns a region worth cutting to');
for (const cam of C.cams) {
  let m = 0;
  for (const spec of cam.owns.edges || []) {
    const mm = /^(.+?)(?:@([\d.]+)\.\.([\d.]+))?$/.exec(spec);
    const E = C.MEDGE[mm[1]]; if (!E) continue;
    m += E.L * ((mm[3] === undefined ? 1 : +mm[3]) - (mm[2] === undefined ? 0 : +mm[2]));
  }
  ok(m >= RULE.minRouteMetres,
     `${cam.id}: owns ${m.toFixed(1)} m of route (floor ${RULE.minRouteMetres} m)`);
  // exclusive floor: at least one owned walk mesh no other shot's boxes contain
  const mine = meshes.filter((x) => x.owner === cam.id);
  const exclusive = mine.filter((x) => {
    const c = [x.rt.center[0], x.rt.max[1], x.rt.center[2]];
    for (const r of REG) {
      if (r.id === cam.id) continue;
      for (const b of r.boxes)
        if (c[0] >= b[0] && c[0] <= b[2] && c[2] >= b[1] && c[2] <= b[3] &&
            Math.abs(c[1] - b[4]) <= RULE.CVTOL) return false;
    }
    return true;
  });
  ok(exclusive.length > 0,
     `${cam.id}: has floor of its own (${exclusive.length}/${mine.length} walk meshes ` +
     `are not inside another shot's region)`);
}

// ============================================ 5. NO PATH-OVERLAP ================
// MOTIVATED BY: the rim-road bug (a seam at the gate stair's head caught walkers
// heading for the cargo winch) and, still standing on 2026-07-30, the quay seam that
// overlapped walk_e_quay-deck__pilot-cluster. cine_solve prints these as WARNINGS.
// A warning that has been standing for a week is a defect nobody owns, so here it is
// a FAILURE — with one narrow, stated exemption.
//
// EXEMPT: a foreign path that is split between the SAME TWO SHOTS within a metre of
// this seam. Dellhollow's waterfront boardwalk is modelled as two map edges lying on
// top of each other (deep-stairs-foot__fish-dock duplicates the middle of
// fish-dock__winch-foot), so the fishdock<->waterfront frontier necessarily crosses
// both. Two co-located bands separating the same pair fire once; the simulated walk
// above is what actually proves it, and it does.
head('NO PATH-OVERLAP — no seam band sits on a route it does not separate');
const seamsByPair = {};
for (const c of CG.cuts) (seamsByPair[[c.from, c.to].sort().join('|')] ||= []).push(c);
for (const w of CUTWARN) {
  const m = /^cut (\S+)<->(\S+) on '([^']+)': every seam position/.exec(w);
  if (!m) { soft(false, w); continue; }
  const [, a, b, edge] = m;
  const mine = seamsByPair[[a, b].sort().join('|')] || [];
  const here = mine.find((c) => c.edge === edge);
  const twin = mine.find((c) => c.edge !== edge && here &&
    Math.hypot(c.at[0] - here.at[0], c.at[2] - here.at[2]) <= 1.5);
  ok(!!twin, w.replace(/ — a player walking THAT path will be cut; VERIFY THIS SEAM/, ''),
     twin ? undefined : {hint: 'move the seam, or give the crossed path one owner'});
  if (twin) soft(true, '');
}

// ======================================= 6. OWNERSHIP-MISMATCH BUDGET ===========
// MOTIVATED BY: 76.5 m of Dellhollow's floor was walked under a camera that did not
// own it, and that is not cosmetic — it is where the positional safety net fires. The
// bridge strobe was exactly this: walking west off the cottage, the correction fired
// inside the mismatch, which re-armed the seam, which fired the player back east.
head('MISMATCH BUDGET — floor walked under a camera that does not own it');
let total = 0; const stretches = [];
for (const c of CG.cuts) {
  const E = c.E;
  const segs = (C.edgeOwner[c.edge] || []);
  // the ownership boundary this cut realises: the t where the owner changes
  let bnd = c.endpoint === 'from' ? 0 : c.endpoint === 'to' ? 1 : null;
  if (bnd === null) {                              // an authored @t split: the NEAREST
    const cand = [];                               // ownership boundary is the one the
    for (const s of segs) cand.push(s.t0, s.t1);   // seam is realising
    bnd = cand.reduce((a, b) => Math.abs(b - c.t) < Math.abs(a - c.t) ? b : a, cand[0]);
  }
  const metres = Math.abs(c.t - bnd) * E.L;
  if (metres > 0.05) { total += metres; stretches.push({edge: c.edge, metres: +metres.toFixed(2), from: c.from, to: c.to}); }
}
stretches.sort((a, b) => b.metres - a.metres);
const endpointCuts = derivedCuts(C).filter((c) => c.endpoint).length;
const budget = C.D.cutOffset * endpointCuts * RULE.mismatchSlack;
ok(total <= budget,
   `town-wide mismatch ${total.toFixed(1)} m (budget ${budget.toFixed(1)} m = cutOffset ` +
   `${C.D.cutOffset} x ${endpointCuts} endpoint seams x ${RULE.mismatchSlack})`);
for (const s of stretches.slice(0, 6))
  ok(s.metres <= RULE.mismatchStretch,
     `${s.edge} (${s.from}<->${s.to}): ${s.metres} m of mismatch (max ${RULE.mismatchStretch} m)`);

// ==================================================================== report ====
head('PASSAGE MAP — what the player sees change, and where');
for (const p of passages.filter((p) => !p.back)) {
  const cuts = p.events.filter((e) => e.kind === 'cut');
  console.log('  ' + p.edge.padEnd(40) +
    (cuts.length ? cuts.map((e) => e.from + '>' + e.to).join(' , ') : '(no cut)') +
    (p.corr ? '   +' + p.corr + ' CORRECTION' : '') + (p.runaway ? '   *** OSCILLATES ***' : ''));
}
console.log(`\n${fail ? 'FAIL' : 'PASS'}  ${pass} assertions ok, ${fail} failed, ${warnN} soft warnings`);
process.exit(fail ? 1 : 0);
