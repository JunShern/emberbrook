// slice_test.mjs — VERIFY the connected slice, headlessly, from the shipped files.
//
//   node tools/slice_test.mjs              assert everything, print the report
//   node tools/slice_test.mjs --plan       also print the browser walk plans (the
//                                          dense polylines tools/slice_walk.js walks)
//
// It asserts three different kinds of thing, because each can be broken alone:
//
//   GRAPH     every node has a bundle; every edge has a reciprocal; every node is
//             reachable from the start scene; no edge points at a scene nobody can
//             reach; scenegraph.json is not stale against the maps.
//   GEOMETRY  every trigger and every arrival point stands on the WALK NETWORK of
//             the scene it belongs to (down-ray over that bundle's walk_ meshes —
//             the same surfaces the runtime's walkFloors() uses). A trigger you
//             cannot reach on foot and an arrival that drops you off the network
//             are the two ways a correct-looking graph is unplayable.
//   ROUTE     the FULL LOOP is walkable in the town-map's own walk network: each
//             leg is routed landmark-to-landmark over the map's edges (Dijkstra on
//             the real segments, waypoints included), so a leg with no path fails
//             here instead of in the browser.
//
// What it deliberately does NOT do: drive the collision walker. That needs the
// real runtime, and it lives in tools/slice_walk.js (browser payload, SIM-driven).
// The two together cover "the graph is right" and "a player can walk it".
import fs from 'fs';
import path from 'path';
import {execFileSync} from 'child_process';
import {loadGlb} from './glb_read.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const PUB = path.join(ROOT, 'public');
const rd = (p) => JSON.parse(fs.readFileSync(path.join(PUB, p), 'utf8'));
const SG = rd('world/scenegraph.json');
const START = 'ow-valley';            // the slice starts in the region
// The town's scene key is DERIVED, never spelled: Dellhollow's play scene moved from
// the real-time `townwalk` bundle to the fixed-camera `del-cine` one the night the
// cinematic cameras landed, and a test that hard-codes a scene key turns a deliberate
// data change into a red build.
// ...and with a SECOND town in the graph, "the first node of kind town" stops being a
// derivation and becomes a coin toss on object key order: scenegraph_derive walks
// world.json's landmarks, Emberbrook is listed before Dellhollow, and this file would
// silently start asserting against a town whose map it does not read.
//
// "The town START has a portal to" is ALSO wrong, and was tried: the valley reaches both
// towns, and it reaches Emberbrook first. THE SLICE IS NOT GENERIC — it is a specific
// named journey (the Valley Gate, the inn, the Moorage, the deep stairs) through one
// town's own landmarks. So resolve the town that CAN ACTUALLY BE WALKED: the town node
// whose map contains every landmark this slice names. Self-describing, and it stays right
// however many towns join the graph.
const SLICE_LANDMARKS = ['valley-gate', 'inn', 'moorage', 'north-landing'];
const townNodes = Object.entries(SG.nodes).filter(([, n]) => n.kind === 'town');
const TOWN = (townNodes.find(([, n]) => {
  const m = (n.origin || '').match(/^\S+\.map\.json/);
  if (!m) return false;
  const ids = new Set(rd(m[0]).landmarks.map((l) => l.id));
  return SLICE_LANDMARKS.every((id) => ids.has(id));
}) || townNodes[0])[0];

let pass = 0, fail = 0;
const ok = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); }
  else { fail++; console.log('  FAIL ' + m + (extra ? '  ' + JSON.stringify(extra) : '')); } };
const head = (s) => console.log('\n== ' + s);

// ---------------------------------------------------------------- 1. GRAPH ----
head('GRAPH');
try {
  execFileSync(process.execPath, [path.join(ROOT, 'tools/scenegraph_derive.mjs'), '--check'],
               {stdio: 'pipe'});
  ok(true, 'scenegraph.json is up to date with the map files');
} catch (e) {
  ok(false, 'scenegraph.json is STALE against the map files (re-run tools/scenegraph_derive.mjs)');
}
for (const [k, n] of Object.entries(SG.nodes))
  ok(fs.existsSync(path.join(PUB, n.bundle, 'scene.glb')), `node ${k}: bundle exists (${n.bundle})`);
const byId = new Map(SG.edges.map((e) => [e.id, e]));
for (const e of SG.edges) {
  ok(!!SG.nodes[e.from] && !!SG.nodes[e.to], `edge ${e.id}: both endpoints are nodes`);
  const r = e.reciprocal && byId.get(e.reciprocal);
  ok(!!r, `edge ${e.id}: reciprocal ${e.reciprocal} exists`);
  if (r) ok(r.from === e.to && r.to === e.from, `edge ${e.id}: reciprocal is the way back`);
  ok(Array.isArray(e.at) && e.at.length === 3 && Array.isArray(e.spawn) && e.spawn.length === 3,
     `edge ${e.id}: has a 3D trigger and a 3D arrival`);
  // An `auto` edge is a SILENT camera cut and must have NO label; everything a player
  // is OFFERED must have a short one. Both are assertions, in opposite directions.
  if (e.auto) ok(!e.label && !e.key, `edge ${e.id}: silent auto cut (no label, no key)`);
  else ok(typeof e.label === 'string' && e.label.length > 0 && e.label.length < 40,
          `edge ${e.id}: prompt label is short and non-empty ("${e.label}")`);
}
// reachability from the start scene
const adj = {};
for (const e of SG.edges) (adj[e.from] = adj[e.from] || []).push(e.to);
const seen = new Set([START]), q = [START];
while (q.length) for (const t of adj[q.shift()] || []) if (!seen.has(t)) { seen.add(t); q.push(t); }
for (const k of Object.keys(SG.nodes))
  ok(seen.has(k), `node ${k}: reachable from ${START}`);
for (const e of SG.edges)
  ok(seen.has(e.from), `edge ${e.id}: its source scene is reachable (edge is not orphaned)`);

// ------------------------------------------------------------- 2. GEOMETRY ----
head('GEOMETRY — triggers and arrivals stand on the walk network');
const WALK = /^walk/i;
const _g = new Map();
const G = (k) => { if (!_g.has(_g)) {} if (!_g.has(k)) _g.set(k, loadGlb(path.join(PUB, SG.nodes[k].bundle, 'scene.glb'))); return _g.get(k); };
function onWalk(key, p, tol, radius) {
  const g = G(key);
  const hit = (x, z) => g.tops(WALK, x, z).some((y) => Math.abs(y - p[1]) <= tol);
  if (hit(p[0], p[2])) return {on: true, off: 0};
  if (radius) for (const f of [0.5, 0.85]) for (let k = 0; k < 8; k++) {
    const a = k * Math.PI / 4;
    if (hit(p[0] + Math.cos(a) * radius * f, p[2] + Math.sin(a) * radius * f))
      return {on: true, off: +(radius * f).toFixed(2)};
  }
  return {on: false};
}
for (const e of SG.edges) {
  // a TRIGGER may sit up to its own radius from walkable ground (a gate arch
  // stands beside the road, not on it); an ARRIVAL may not — you spawn there.
  // a TRIGGER may sit up to its own reach from walkable ground (a gate arch stands
  // beside the road, not on it); a camera cut's reach is its band, not a radius.
  const reach = e.band ? Math.max(e.band.t, 0.6) : e.r;
  const t = onWalk(e.from, e.at, 0.6, reach);
  ok(t.on, `edge ${e.id}: trigger is reachable (walk surface within reach in ${e.from})`,
     t.on ? undefined : {at: e.at});
  if (t.on && t.off) console.log(`       note: trigger's walk surface is ${t.off}u away, inside reach=${reach}`);
  const s = onWalk(e.to, e.spawn, 0.35, 0);
  ok(s.on, `edge ${e.id}: ARRIVAL lands on the walk network of ${e.to}`,
     s.on ? undefined : {spawn: e.spawn, tops: G(e.to).tops(WALK, e.spawn[0], e.spawn[2]).slice(0, 4)});
}
// an arrival must not sit inside the radius of the edge that sends you back
for (const e of SG.edges) {
  const r = byId.get(e.reciprocal);
  if (!r) continue;
  let inside;
  if (r.band) {                       // a camera seam: an oriented band, not a circle
    const ax = e.spawn[0] - r.at[0], az = e.spawn[2] - r.at[2];
    inside = Math.abs(ax * r.band.n[0] + az * r.band.n[1]) <= r.band.t &&
             Math.abs(-ax * r.band.n[1] + az * r.band.n[0]) <= r.band.w &&
             Math.abs(e.spawn[1] - r.at[1]) <= (r.vTol ?? SG.defaults.vTol);
  } else {
    const d = Math.hypot(e.spawn[0] - r.at[0], e.spawn[2] - r.at[2]);
    inside = d <= r.r && Math.abs(e.spawn[1] - r.at[1]) <= (r.vTol ?? SG.defaults.vTol);
  }
  // interiors are the deliberate exception: they spawn ON their door pad, which IS
  // the exit trigger, and the runtime's arm-on-exit rule covers exactly that.
  ok(!inside || SG.nodes[e.to].kind === 'interior',
     `edge ${e.id}: arrival is clear of the return trigger` +
     (inside ? ' (interior door pad — armed only after you step off)' : ''), inside ? {spawn: e.spawn, at: r.at} : undefined);
}

// ----------------------------------------------------------------- 3. ROUTE ---
head('ROUTE — the full loop is walkable in the map network');
// Dijkstra over the town map's own walk network: nodes are landmarks, edge cost is
// the polyline length through its waypoints. Same records the runtime's net builder
// and the town geometry are made from, so a path here means ribbons exist.
// The town map is the one THIS town node was derived from — scenegraph_derive records it
// in `origin` — never a spelled path, for the same reason the scene key is not spelled.
const TOWNMAP = ((SG.nodes[TOWN] || {}).origin || '').match(/^\S+\.map\.json/);
const town = rd(TOWNMAP ? TOWNMAP[0] : 'townmap/dellhollow.map.json');
const TT = (p) => [p[0], p[2], -p[1]];
const LM = {}; for (const l of town.landmarks) LM[l.id] = l;
const NET = {};
const seg = (e) => [TT(LM[e.from].pos), ...(e.waypoints || []).map(TT), TT(LM[e.to].pos)];
const plen = (pts) => pts.slice(1).reduce((a, p, i) => a + Math.hypot(p[0] - pts[i][0], p[2] - pts[i][2]), 0);
for (const e of town.edges) {
  const pts = seg(e), L = plen(pts);
  (NET[e.from] = NET[e.from] || []).push({to: e.to, L, pts, type: e.type});
  (NET[e.to] = NET[e.to] || []).push({to: e.from, L, pts: [...pts].reverse(), type: e.type});
}
function route(a, b) {
  const dist = {[a]: 0}, prev = {}, done = new Set();
  while (true) {
    let u = null;
    for (const k in dist) if (!done.has(k) && (u === null || dist[k] < dist[u])) u = k;
    if (u === null) return null;
    if (u === b) break;
    done.add(u);
    for (const e of NET[u] || []) if (dist[e.to] === undefined || dist[u] + e.L < dist[e.to]) {
      dist[e.to] = dist[u] + e.L; prev[e.to] = {from: u, e};
    }
  }
  const legs = []; let cur = b;
  while (cur !== a) { const p = prev[cur]; legs.unshift({from: p.from, to: cur, type: p.e.type, pts: p.e.pts}); cur = p.from; }
  return {legs, len: +dist[b].toFixed(1)};
}
// resample to the step a straight-line steerer can follow without cutting corners
// into the rails (the lesson of the S-bend flight: coarse waypoints cut corners)
function dense(pts, step = 0.8) {
  const o = [[+pts[0][0].toFixed(2), +pts[0][2].toFixed(2)]];
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1], L = Math.hypot(b[0] - a[0], b[2] - a[2]);
    const n = Math.max(1, Math.ceil(L / step));
    for (let k = 1; k <= n; k++) o.push([+(a[0] + (b[0] - a[0]) * k / n).toFixed(2),
                                        +(a[2] + (b[2] - a[2]) * k / n).toFixed(2)]);
  }
  return o;
}
// THE LOOP, as the brief specifies it. Region legs follow the region road; town
// legs are routed through the map network; interior legs are a single room.
const region = rd('world/regions/valley.region.json');
const CX = 140, CY = 100;                       // valley tile centre (see generator)
const roadPts = region.road.points.map((p) => [p[0] - CX, p[2], CY - p[1]]);
const gateIdx = roadPts.reduce((bi, p, i, arr) => {
  const d = (q) => Math.hypot(q[0] - (region.road.portals.find((x) => x.id === 'dellhollow-valley-gate').at[0] - CX),
                              q[2] - (CY - region.road.portals.find((x) => x.id === 'dellhollow-valley-gate').at[1]));
  return d(p) < d(arr[bi]) ? i : bi; }, 0);
const spawnMeta = JSON.parse(fs.readFileSync(path.join(PUB, 'assets/scenes/ow-valley/meta.json'), 'utf8')).spawn;
const spawnIdx = roadPts.reduce((bi, p, i, arr) =>
  Math.hypot(p[0] - spawnMeta[0], p[2] - spawnMeta[2]) < Math.hypot(arr[bi][0] - spawnMeta[0], arr[bi][2] - spawnMeta[2]) ? i : bi, 0);

const LOOP = [];
LOOP.push({scene: 'ow-valley', what: 'spawn (Emberbrook gate) -> the Valley Gate, down the region road',
           walk: dense(roadPts.slice(spawnIdx, gateIdx + 1), 1.2),
           edge: `ow-valley>${TOWN}@dellhollow-valley-gate`});
const toInn = route('valley-gate', 'inn');
LOOP.push({scene: TOWN, what: 'Valley Gate -> the inn door (the S-bend flight down to the shelf street)',
           route: toInn, walk: dense(toInn.legs.flatMap((l) => l.pts)),
           edge: `${TOWN}>del-inn-int@inn`});
LOOP.push({scene: 'del-inn-int', what: 'inside the inn: door pad -> counter -> back to the door',
           walk: null, edge: `del-inn-int>${TOWN}@inn`});
const toMoorage = route('inn', 'moorage');
LOOP.push({scene: TOWN, what: 'back outside the inn -> the Moorage (down through the quay and the deep stairs)',
           route: toMoorage, walk: dense(toMoorage.legs.flatMap((l) => l.pts)),
           edge: null});
for (const L of LOOP) {
  if (L.route) ok(!!L.route, `leg "${L.what}": a route exists in the walk network` +
                             (L.route ? ` (${L.route.len}u, ${L.route.legs.length} map edges: ${L.route.legs.map((l) => l.type).join('>')})` : ''));
  if (L.edge) ok(!!byId.get(L.edge), `leg "${L.what}": ends on graph edge ${L.edge}`);
}
// every enterable landmark must be routable from the gate, or a door is unreachable
head('ROUTE — every enterable landmark is routable from the town gate');
for (const l of town.landmarks.filter((x) => x.enterable && x.interiorSceneKey)) {
  const r = route('valley-gate', l.id);
  ok(!!r, `landmark ${l.id}: routable from valley-gate` + (r ? ` (${r.len}u)` : ''));
}

if (process.argv.includes('--plan')) {
  head('BROWSER WALK PLANS (feed to tools/slice_walk.js SLICE.plan)');
  for (const L of LOOP) console.log(JSON.stringify({scene: L.scene, what: L.what, edge: L.edge, walk: L.walk}));
}

console.log(`\n${fail ? 'FAIL' : 'PASS'}  ${pass} assertions ok, ${fail} failed`);
process.exit(fail ? 1 : 0);
