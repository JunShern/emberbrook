// seam_walk.mjs — the JOURNEY check, against SHIPPED runtime data.
//
//   node tools/seam_walk.mjs        walk the town's canonical journeys, assert the cuts
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

const SG = JSON.parse(fs.readFileSync(path.join(PUB, 'world/scenegraph.json'), 'utf8'));
const C = loadCine();
const NODE = SG.nodes['del-cine'];
const REG = NODE.shots;                                   // shipped region boxes
const D = SG.defaults || {};
const SPD = 0.075, GRACE = D.correctionGrace ?? 20, CPAD = D.correctionPad ?? 0.6,
      CVTOL = D.correctionVTol ?? 1.2, CREACH = D.correctionReach ?? 12;
// shipped in-scene auto edges only (camera cuts)
const EDGES = SG.edges.filter((e) => e.from === 'del-cine' && e.to === 'del-cine' && e.band);
// heights come from the same walk bundle the runtime collides against
const walkY = cutGeometry(C, path.join(PUB, 'assets/scenes/townwalk/scene.glb'), () => {}).walkY;

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
const ep = (k, t0, t1) => { const E = C.MEDGE[k], N = Math.max(10, Math.ceil(Math.abs(t1-t0)*E.L*6)), o = [];
  for (let i=0;i<=N;i++) o.push(m2r(edgePoint(E, t0+(t1-t0)*i/N))); return o; };
const cat = (...a) => [].concat(...a);

const W = [
  ['THE DESCENT, market flight  (shop street -> shelf-homes -> market -> lockhead)',
   cat(ep('armor-shop__shelf-homes',0.3,1), ep('shelf-homes__market-stalls',0,1), ep('market-stalls__lockhead',0,0.35)), 'shelf-east', 3],
  ['THE DESCENT, quay flight    (shop street -> shelf-homes -> harbour deck -> cookhouse)',
   cat(ep('armor-shop__shelf-homes',0.3,1), ep('shelf-homes__quay-deck',0,1), ep('quay-deck__cookhouse',0,0.7)), 'shelf-east', 2],
  ['THE DESCENT, then east      (quay flight down, then across the plaza to the stalls)',
   cat(ep('shelf-homes__quay-deck',0,1), ep('quay-deck__market-stalls',0,1)), 'loop-stairs', 1],
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
];
let bad = 0;
for (const [label, pts, start, expect] of W) {
  const r = walk(pts, start, label);
  const okc = r.cuts === expect && r.corr === 0 && !r.run;
  console.log('  => ' + (okc ? 'OK' : 'MISMATCH') + `  expected ${expect} cut(s), 0 corrections`);
  if (!okc) bad++;
}
console.log(`\n${bad ? 'FAIL' : 'PASS'} — ${W.length - bad}/${W.length} scripted walks match expectation`);
process.exit(bad ? 1 : 0);
