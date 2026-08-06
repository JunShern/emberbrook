// seam_walk.mjs — the JOURNEY check, against SHIPPED runtime data.
//
//   node tools/seam_walk.mjs                     walk the town's canonical journeys,
//                                                assert the cuts
//   node tools/seam_walk.mjs --town emberbrook   any town with a <town>.cameras.json
//                                                and a <town>.journeys.json
//
// Complements tools/seam_test.mjs, and the difference is the point:
//
//   seam_test  walks ONE map edge at a time, against seams it RE-DERIVES from
//              cameras.json. It proves the DESIGN is sound, and it can test a
//              proposal (--cameras) before anything is written to public/.
//   seam_walk  walks MULTI-EDGE JOURNEYS — the descent, the bridge, the boatyard
//              approach — against public/world/scenegraph.json itself: the exact
//              bytes the browser loads. It proves what SHIPPED is sound, and it is
//              the only check that would catch a stale scene graph, a generator that
//              wrote something other than what it derived, or a defect that only
//              appears when two edges are walked back to back.
//
// The expected cut count per journey is written down here, so "the descent is one cut
// per passage" is an assertion with a number and not a claim in a document. The
// journeys with an expectation of 0 are the two defects the user hit on 2026-07-30 —
// the harbour plaza's 4 cm double-cut and the boatyard shed path's wrong cut — kept as
// permanent regression walks.
import fs from 'fs';
import path from 'path';
import {loadCine, cutGeometry, edgePoint, m2r, PUB} from
  '/Users/junshernchan/projects/multiplayer-rpg/tools/cine_regions.mjs';

const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const TOWN = opt('--town', 'dellhollow');

const SG = JSON.parse(fs.readFileSync(path.join(PUB, 'world/scenegraph.json'), 'utf8'));
const C = loadCine(`townmap/${TOWN}.map.json`, `townmap/${TOWN}.cameras.json`);
// The cinematic scene key is the camera file's own; the walk bundle is the map's stated
// explorable one (the house rule — tools/seam_test.mjs).
const SCENE = C.camFile.sceneKey;
const WALKGLB = path.join(PUB, 'assets/scenes',
  (C.map.walkSceneKey || C.camFile.sceneKey), 'scene.glb');
const NODE = SG.nodes[SCENE];
if (!NODE) { console.error(`'${SCENE}' is not a node in the shipped scenegraph.json — ` +
  'run tools/scenegraph_derive.mjs first'); process.exit(1); }
const REG = NODE.shots;                                   // shipped region boxes
const D = SG.defaults || {};
const SPD = 0.075, GRACE = D.correctionGrace ?? 20, CPAD = D.correctionPad ?? 0.6,
      CVTOL = D.correctionVTol ?? 1.2, CREACH = D.correctionReach ?? 12;
// shipped in-scene auto edges only (camera cuts)
const EDGES = SG.edges.filter((e) => e.from === SCENE && e.to === SCENE && e.band);
// heights come from the same walk bundle the runtime collides against
const walkY = cutGeometry(C, WALKGLB, () => {}).walkY;

const hit = (e, P) => {
  const dy = Math.abs(P[1] - e.at[1]), vt = e.vTol ?? (D.vTol ?? 2);
  const px = P[0] - e.at[0], pz = P[2] - e.at[2];
  const along = px * e.band.n[0] + pz * e.band.n[1];
  const across = -px * e.band.n[1] + pz * e.band.n[0];
  return {d: Math.hypot(along, Math.max(0, Math.abs(across) - e.band.w)),
          in: Math.abs(along) <= e.band.t && Math.abs(across) <= e.band.w && dy <= vt};
};
function regionsFor(P, cam) {
  let own = false, other = null, bd = Infinity;
  for (const r of REG) { for (const b of r.boxes) {
      if (P[0] < b[0] - CPAD || P[0] > b[2] + CPAD || P[2] < b[1] - CPAD || P[2] > b[3] + CPAD) continue;
      const dy = Math.abs(P[1] - b[4]); if (dy > CVTOL) continue;
      if (r.id === cam) { own = true; break; }
      if (dy < bd) { bd = dy; other = r.id; } } if (own) break; }
  if (own || other) return {own, other};
  let nid = null, nd = Infinity;
  for (const r of REG) for (const b of r.boxes) {
    const dx = Math.max(b[0] - P[0], 0, P[0] - b[2]), dz = Math.max(b[1] - P[2], 0, P[2] - b[3]);
    const d = Math.sqrt(dx * dx + dz * dz + (P[1] - b[4]) ** 2);
    if (d < nd) { nd = d; nid = r.id; } }
  return nd > CREACH ? {own: false, other: null} : {own: nid === cam, other: nid};
}
function mk(pts) {
  const cum = [0];
  for (let i = 0; i < pts.length - 1; i++)
    cum.push(cum[i] + Math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][2]-pts[i][2]));
  const L = cum[cum.length-1];
  const at = (s) => { s = Math.max(0, Math.min(L, s));
    for (let i = 0; i < cum.length-1; i++) if (s <= cum[i+1] || i === cum.length-2) {
      const g = cum[i+1]-cum[i], f = g < 1e-9 ? 0 : (s-cum[i])/g, a = pts[i], b = pts[i+1];
      return [a[0]+(b[0]-a[0])*f, a[1]+(b[1]-a[1])*f, a[2]+(b[2]-a[2])*f]; } return pts[0].slice(); };
  const proj = (p) => { let bs=0, bd=Infinity;
    for (let i=0;i<pts.length-1;i++){ const a=pts[i],b=pts[i+1];
      const vx=b[0]-a[0], vz=b[2]-a[2], vv=vx*vx+vz*vz;
      let f = vv<1e-12?0:((p[0]-a[0])*vx+(p[2]-a[2])*vz)/vv; f=Math.max(0,Math.min(1,f));
      const d=Math.hypot(p[0]-(a[0]+vx*f), p[2]-(a[2]+vz*f));
      if(d<bd){bd=d;bs=cum[i]+Math.hypot(vx,vz)*f;} } return bs; };
  return {at, proj, L};
}
function walk(pts, cam0, label) {
  const P0 = mk(pts); let cam = cam0, ct = 0, cl = null, s = 0, ev = [], steps = 0, run = false;
  const armed = new Map();
  let P = P0.at(0); const y0 = walkY(P[0], P[2], P[1]); if (y0 != null) P[1] = y0;
  const tick = () => {
    let fire = null;
    for (const e of EDGES) {
      if (e.camFrom && e.camFrom !== cam) continue;
      const h = hit(e, P);
      if (!armed.has(e.id)) { armed.set(e.id, !h.in); continue; }
      if (!h.in) { armed.set(e.id, true); continue; }
      if (!armed.get(e.id)) continue;
      if (!fire || h.d < fire.h.d) fire = {e, h};
    }
    if (fire) {
      ev.push({k: 'cut', s: +s.toFixed(2), from: cam, to: fire.e.cam.key, at: P.map(v=>+v.toFixed(2)), of: fire.e.of});
      cam = fire.e.cam.key; P = fire.e.spawn.slice();
      const y = walkY(P[0], P[2], P[1]); if (y != null) P[1] = y;
      s = P0.proj(P); armed.clear(); ct = 0; cl = null; return;
    }
    const r = regionsFor(P, cam);
    if (r.own || !r.other) { ct = 0; cl = null; return; }
    if (cl !== r.other) { cl = r.other; ct = 0; }
    if (++ct < GRACE) return;
    ct = 0; ev.push({k: 'CORRECTION', s: +s.toFixed(2), from: cam, to: r.other, at: P.map(v=>+v.toFixed(2))});
    cam = r.other; armed.clear();
  };
  tick();
  while (s < P0.L - SPD) {
    if (++steps > 40000 || ev.length > 30) { run = true; break; }
    s += SPD; const q = P0.at(s);
    const dx = q[0]-P[0], dz = q[2]-P[2], L = Math.hypot(dx, dz);
    if (L > 1e-9) { const k = Math.min(1, SPD/L); P[0] += dx*k; P[2] += dz*k; }
    const y = walkY(P[0], P[2], q[1]); if (y != null) P[1] = y;
    tick();
  }
  for (let i = 0; i < 180 && !run; i++) tick();      // stand still THREE seconds
  const cuts = ev.filter(e=>e.k==='cut').length, corr = ev.filter(e=>e.k==='CORRECTION').length;
  console.log(`\n${label}\n  ${cuts} cut(s), ${corr} correction(s), ends in '${cam}'${run?'  *** OSCILLATES ***':''}`);
  for (const e of ev) console.log(`   s=${String(e.s).padStart(6)}  ${e.k==='cut'?'cut       ':'CORRECTION'} ` +
    `${(e.from+' -> '+e.to).padEnd(28)} at ${JSON.stringify(e.at)}${e.of?'   '+e.of:''}`);
  return {cuts, corr, run};
}
// A LEG THAT NAMES AN EDGE THE MAP NO LONGER HAS IS A STALE JOURNEY, and it used to be a
// TypeError three frames deep (`Cannot read properties of undefined (reading 'L')`), which
// says nothing about which journey or which edge. Emberbrook's list named three withdrawn
// edges after the 2x round and this tool could not run for that town at all. Name it.
const ep = (k, t0, t1) => { const E = C.MEDGE[k];
  if (!E) throw new Error(`journey leg names edge '${k}', which is not in ` +
    `townmap/${TOWN}.map.json — the journeys file is STALE against the map ` +
    `(a withdrawn or retyped edge). Fix townmap/${TOWN}.journeys.json.`);
  const N = Math.max(10, Math.ceil(Math.abs(t1-t0)*E.L*6)), o = [];
  for (let i=0;i<=N;i++) o.push(m2r(edgePoint(E, t0+(t1-t0)*i/N))); return o; };
const cat = (...a) => [].concat(...a);

// THE JOURNEYS, and what each one must cost. This is TOWN DATA — "the descent is one cut
// per passage" names Dellhollow's own flights, and the two zero-expectation walks are its
// own live defects of 2026-07-30 kept as permanent regressions. Dellhollow's list predates
// any file for it and stays here; any other town states its own in
// townmap/<town>.journeys.json:
//   {"journeys": [{"label": "...", "start": "<shot id>", "expect": 2,
//                  "legs": [["<edge key>", t0, t1], ...]}, ...]}
// A town with no journeys file has nothing to assert, and this gate says so and FAILS
// rather than printing a green PASS over zero walks.
// LAZY, and it has to be: this literal calls ep() on DELLHOLLOW's edge keys, and ep()
// looks them up in the loaded town's map. Built eagerly it crashed every other town at
// import time — `Cannot read properties of undefined (reading 'L')` — before the journeys
// file it was supposed to read was ever consulted. A default that breaks the non-default
// case is not a default.
const JOURNEYS = () => ({dellhollow: [
  ['THE DESCENT, market flight  (shop street -> shelf-homes -> market -> lockhead)',
   cat(ep('armor-shop__shelf-homes',0.3,1), ep('shelf-homes__market-stalls',0,1), ep('market-stalls__lockhead',0,0.35)), 'shelf-east', 3],
  // THE QUAY BRANCH IS DELETED (Bet 2, 2026-08-06, user simplicity ruling — see the
  // map's _bet2_2026-08-06b on shelf-homes__market-stalls). c046f51's fork landing
  // ('loop-landing') and its edge 'loop-landing__quay-deck' are gone from the map:
  // the branch overlaid the plaza's own walk disc by construction and the market
  // flight already lands one flat hop from the deck. ONE way down. The walk to the
  // harbour deck is now: the yard, the market flight, then west across the plaza.
  ['THE DESCENT, to the deck    (shop street -> shelf-homes -> market flight -> plaza -> cookhouse)',
   cat(ep('armor-shop__shelf-homes',0.3,1), ep('shelf-homes__market-stalls',0,1),
       ep('quay-deck__market-stalls',1,0), ep('quay-deck__cookhouse',0,0.7)), 'shelf-east', 2],
  ['THE DESCENT, then east      (market flight down, then east along the stalls to the lockhead)',
   cat(ep('shelf-homes__market-stalls',0.467,1), ep('market-stalls__lockhead',0,0.35)), 'loop-stairs', 2],
  ['THE CLIMB BACK             (market -> shelf-homes -> shop street)',
   cat(ep('shelf-homes__market-stalls',1,0), ep('armor-shop__shelf-homes',1,0.5)), 'quay-west', 2],
  ['THE PLAZA, walked west     (the 4 cm double-cut in the shipped build)',
   ep('quay-deck__market-stalls',1,0), 'quay-west', 0],
  ['THE BRIDGE, eastbound      (weave huts -> plank bridge -> cottage)',
   cat(ep('pilot-cluster__weave-huts',0.7,1), ep('weave-huts__keepers-cottage',0,1), ep('lockhead__keepers-cottage',1,0.85)), 'weave', 2],
  ['THE BRIDGE, westbound      (the 30-cut softlock in the shipped build)',
   cat(ep('weave-huts__keepers-cottage',1,0), ep('pilot-cluster__weave-huts',1,0.8)), 'cottage', 2],
  ['THE BOATYARD APPROACH      (fish dock -> winch foot -> slipway)',
   cat(ep('fish-dock__winch-foot',0,1), ep('winch-foot__slipway',0,1)), 'fishdock', 2],
  ['THE SHED PATH              (boatwright shed -> pitch kettle: the wrong-cut repro)',
   ep('boatwright-shed__pitch-kettle',0,1), 'boatyard', 0],
]});
const JFILE = path.join(PUB, `townmap/${TOWN}.journeys.json`);
const W = fs.existsSync(JFILE)
  ? JSON.parse(fs.readFileSync(JFILE, 'utf8')).journeys.map((j) =>
      [j.label, cat(...j.legs.map(([k, t0, t1]) => ep(k, t0, t1))), j.start, j.expect])
  : JOURNEYS()[TOWN];
if (!W) {
  console.error(`no journeys authored for town '${TOWN}'. This gate walks MULTI-EDGE ` +
    'routes against the SHIPPED scene graph, so it needs the routes a player of this ' +
    `town actually takes: author public/townmap/${TOWN}.journeys.json ` +
    '{"journeys": [{"label", "start", "expect", "legs": [[edgeKey, t0, t1], ...]}]}.');
  process.exit(1);
}
let bad = 0;
for (const [label, pts, start, expect] of W) {
  const r = walk(pts, start, label);
  const okc = r.cuts === expect && r.corr === 0 && !r.run;
  console.log('  => ' + (okc ? 'OK' : 'MISMATCH') + `  expected ${expect} cut(s), 0 corrections`);
  if (!okc) bad++;
}
console.log(`\n${bad ? 'FAIL' : 'PASS'} — ${W.length - bad}/${W.length} scripted walks match expectation`);
process.exit(bad ? 1 : 0);
