// cine_solve.mjs — solve the cinematic cameras' framing and write the ONE numeric
// truth every downstream consumer reads.
//
//   node tools/cine_solve.mjs           write public/townmap/dellhollow.cameras.solved.json
//   node tools/cine_solve.mjs --check   fail if the solved file is stale (build gate)
//   node tools/cine_solve.mjs --print   report only, write nothing (the framing loop)
//
// WHY A SOLVED FILE. A shot is authored as INTENT ("look from out over the gorge at
// 104 degrees, 15 up, leave 12% air") because a hand-typed camera position cannot
// know whether the region it must cover actually fits in frame — that is the exact
// mistake that buried the map's draft ortho cameras inside the cliffs. The solver
// turns intent into pos/aim by fitting the region's CHARACTER-HEIGHT samples, then
// reports the character's on-screen pixel height so legibility is measured. The
// result is a build artifact: cine_bake.py builds the Blender camera from it and
// play3d.html builds the THREE camera from it, so the render and the game cannot
// disagree about where a camera is (supervisor condition 1).
//
// Also emits, per camera: the owned walk-mesh count, the derived xz hull (the
// region polygon), the region's runtime AABB and its entry points — consumed by
// cine_test.mjs and by the region map.
import fs from 'fs';
import path from 'path';
import {loadCine, walkMeshes, ownerOfWalk, solveCamera, cutGeometry, edgePoint,
        PUB, r3, m2r, r2m} from './cine_regions.mjs';

const ARGS = process.argv.slice(2);
const OUT = path.join(PUB, 'townmap/dellhollow.cameras.solved.json');
const C = loadCine();
const WALK_BUNDLE = 'assets/scenes/townwalk/scene.glb';

// ---- assign every walk mesh of the explorable town to its owning camera ------
const {meshes} = walkMeshes(path.join(PUB, WALK_BUNDLE));
const orphans = [];
for (const m of meshes) {
  const o = ownerOfWalk(C, m.name, m.center);
  m.owner = o.cam; m.ownerVia = o.via;
  if (!o.cam) orphans.push({name: m.name, why: o.via});
}
const byCam = {};
for (const m of meshes) if (m.owner) (byCam[m.owner] = byCam[m.owner] || []).push(m);

// ---- the seams, placed against the real walk geometry ------------------------
// Solved BEFORE the cameras, because a shot must frame not only the ground it owns
// but every point a player can MATERIALISE on inside it. "A player must never walk
// off-screen confused" starts with never arriving off-screen.
const CG = cutGeometry(C, path.join(PUB, WALK_BUNDLE), (m) => C.warn.push(m));
const arrivalsIn = {};                        // camera id -> [map-space arrival points]
for (const c of CG.cuts) {
  (arrivalsIn[c.to] = arrivalsIn[c.to] || []).push(r2m(c.spawnTo));
  (arrivalsIn[c.from] = arrivalsIn[c.from] || []).push(r2m(c.spawnFrom));
}
// door and portal arrivals too: coming back out of a shop, or in through the gate,
// both put the player on a specific metre of street that has to be on screen
for (const l of C.map.landmarks) {
  if (!l.enterable || !l.interiorSceneKey) continue;
  const own = C.lmOwner[l.id];
  if (own) (arrivalsIn[own] = arrivalsIn[own] || []).push(l.pos.slice());
}
for (const ex of C.map.exits || []) {
  const own = C.lmOwner[ex.at];
  const lm = C.LM[ex.at];
  if (own && lm) (arrivalsIn[own] = arrivalsIn[own] || []).push(lm.pos.slice());
}

// ---- solve each camera -------------------------------------------------------
const solved = [];
for (const cam of C.cams) {
  const s = solveCamera(C, cam, meshes, arrivalsIn[cam.id] || []);
  const mine = byCam[cam.id] || [];
  const bb = {min: [1e9, 1e9, 1e9], max: [-1e9, -1e9, -1e9]};
  for (const m of mine) for (let k = 0; k < 3; k++) {
    bb.min[k] = Math.min(bb.min[k], m.min[k]); bb.max[k] = Math.max(bb.max[k], m.max[k]);
  }
  // PROBES: up to 48 character-head points spread over the owned region, in map
  // coords. Two consumers need the SAME points or their verdicts are not comparable:
  // cine_bake.py ray-casts them in Blender to prove the camera can actually SEE its
  // region (the draft ortho cameras were buried in the cliffs and nobody could tell
  // from the numbers), and cine_test.mjs projects them to assert the in-frame fraction.
  // PROBE AT BODY HEIGHT AS WELL AS HEAD HEIGHT. Head-only probing said the gate shot
  // was 77% visible; in the runtime the character was FULLY occluded at its own spawn,
  // because the rim road has a palisade along its gorge side and a camera out over the
  // gorge sees the fence, not the body behind it. A 1.4 m railing is invisible to a
  // 1.7 m probe and opaque to a walking character — so probe the chest too.
  const S = mine.length ? [...sampleHeads(mine, C.D.charH * 0.5), ...sampleHeads(mine, C.D.charH)] : [];
  const probes = pickSpread(S, 64);
  // SPAWN CANDIDATES: where a bare `?scene=del-cine&cam=<id>` load or a stale edge
  // puts the player. Ranked by closeness to the region centroid, so the fallback is
  // the middle of the shot; the bake keeps the first one the camera can see.
  const cen = mine.length ? mine.reduce((a, m) => [a[0] + m.center[0], a[1] + m.center[1]], [0, 0])
                             .map((v) => v / mine.length) : [0, 0];
  // Ranked, never FILTERED: preferring pads and landings is a preference, and as a hard
  // filter it left every transit shot with NO candidates at all (a flight owns only
  // `..._l0_t00` tread meshes, which match neither pattern) and therefore no fallback
  // spawn. A shot you can open with ?cam= must always have somewhere to stand.
  const rank = (n) => /^walk_(pad|lm)_/i.test(n) ? 0 : /landing/i.test(n) ? 1 : 2;
  const spawnCandidates = mine
    .map((m) => ({p: [m.center[0], m.center[1], m.max[2]], r: rank(m.name),
                  d: Math.hypot(m.center[0] - cen[0], m.center[1] - cen[1]), name: m.name}))
    .sort((a, b) => a.r - b.r || a.d - b.d).slice(0, 16)
    .map((o) => ({at: r3(o.p), from: o.name}));

  solved.push(Object.assign({
    id: cam.id, name: cam.name, entry: !!cam.entry, transit: !!cam.transit,
    shot: cam.shot,
    owns: cam.owns,
    walkMeshes: mine.length,
    bounds: mine.length ? {min: r3(bb.min), max: r3(bb.max)} : null,
    hull: hullXY(mine),
    probes: probes.map(r3), spawnCandidates,
  }, s));
}

// every owned walk mesh's top face, 5 points each, lifted to head height
function sampleHeads(mine, H) {
  const pts = [];
  for (const m of mine) {
    const [x0, y0] = m.min, [x1, y1] = m.max, h = m.max[2] + H;
    pts.push([(x0 + x1) / 2, (y0 + y1) / 2, h], [x0, y0, h], [x1, y0, h], [x0, y1, h], [x1, y1, h]);
  }
  return pts;
}
// deterministic thinning: keep every nth so a big region and a small one both get
// an evenly spread probe set (never "the first 48", which would clump on one flight)
function pickSpread(pts, n) {
  if (pts.length <= n) return pts;
  const out = [], step = pts.length / n;
  for (let i = 0; i < n; i++) out.push(pts[Math.floor(i * step)]);
  return out;
}

// convex hull of the owned walk footprint in map xy — the region polygon, DERIVED
function hullXY(mine) {
  const pts = [];
  for (const m of mine) pts.push([m.min[0], m.min[1]], [m.max[0], m.min[1]],
                                 [m.max[0], m.max[1]], [m.min[0], m.max[1]]);
  if (pts.length < 3) return pts.map(r2);
  pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const half = (arr) => { const h = [];
    for (const p of arr) { while (h.length >= 2 && cr(h[h.length - 2], h[h.length - 1], p) <= 0) h.pop(); h.push(p); }
    return h; };
  const lo = half(pts), hi = half([...pts].reverse());
  return [...lo.slice(0, -1), ...hi.slice(0, -1)].map(r2);
}
function r2(p) { return [Math.round(p[0] * 100) / 100, Math.round(p[1] * 100) / 100]; }

// ---- the cuts (reported so the framing loop can see the seams) --------------
const cuts = CG.cuts.map((c) => ({
  edge: c.edge, t: +c.t.toFixed(4), from: c.from, to: c.to,
  atRuntime: c.at, band: c.band, margin: c.margin,
  spawnTo: c.spawnTo, spawnFrom: c.spawnFrom,
  whatFrom: c.whatFrom, whatTo: c.whatTo,
}));

// ---- the file ---------------------------------------------------------------
const doc = {
  _doc: [
    'SOLVED CINEMATIC CAMERAS — GENERATED by tools/cine_solve.mjs from',
    'townmap/dellhollow.cameras.json (intent) + townmap/dellhollow.map.json (topology)',
    '+ assets/scenes/townwalk/scene.glb (the walk geometry being framed).',
    'NEVER hand-edit: `node tools/cine_solve.mjs --check` fails the build if this file',
    'drifts from those three. Re-run after any camera or map edit, then re-run',
    'tools/scenegraph_derive.mjs and re-bake the affected cameras.',
    '',
    'This is THE numeric truth for a camera: cine_bake.py builds the Blender camera',
    'from pos/aim/fov/clip here, and play3d.html builds the THREE.PerspectiveCamera',
    'from the same numbers (carried into the bundle by cine.json). No camera number',
    'is written twice anywhere in the project.',
    '',
    'pos/aim/bounds/hull are MAP coords [x, y, h] (== Blender). atRuntime is the',
    'runtime frame [x, h, -y]. fov is VERTICAL degrees.',
    'inFrameFrac: fraction of the region\'s character-height samples inside the frame.',
    'charPxNear/Far: on-screen height in px (of 768) of a 1.7 m character at the',
    'nearest/farthest sample — the legibility number, reported not assumed.',
  ],
  generator: 'tools/cine_solve.mjs',
  generated: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
  sources: ['townmap/dellhollow.cameras.json', 'townmap/dellhollow.map.json', WALK_BUNDLE],
  town: C.camFile.town, sceneKey: C.camFile.sceneKey, defaults: C.D,
  totals: {cameras: solved.length, walkMeshes: meshes.length,
           assigned: meshes.length - orphans.length, orphans: orphans.length,
           cuts: cuts.length},
  cameras: solved, cuts, orphans,
  warnings: C.warn,
};

const json = JSON.stringify(doc, null, 1) + '\n';
const strip = (s) => s.replace(/"generated": "[^"]*",?\n?/, '');
let staleExit = 0;
if (ARGS.includes('--check')) {
  const cur = fs.existsSync(OUT) ? fs.readFileSync(OUT, 'utf8') : '';
  if (strip(cur) !== strip(json)) {
    console.error('STALE: townmap/dellhollow.cameras.solved.json differs. Re-run tools/cine_solve.mjs.');
    staleExit = 1;
  } else console.log('cameras.solved.json is up to date.');
} else if (!ARGS.includes('--print')) {
  fs.writeFileSync(OUT, json);
  console.log('wrote public/townmap/dellhollow.cameras.solved.json');
}

// ---- the report (always: a run is self-verifying at a glance) ---------------
console.log(`\ncameras ${solved.length}   walk meshes ${meshes.length} (${orphans.length} orphaned)   cuts ${cuts.length}`);
console.log('id              walk  dist   frame%  charPx near..far  bounds x / y / h');
for (const s of solved) {
  const b = s.bounds;
  console.log(`${s.id.padEnd(15)} ${String(s.walkMeshes).padStart(4)}  ` +
    `${String(s.dist ?? '-').padStart(5)}${s.capped ? '!' : ' '} ` +
    `${((s.inFrameFrac ?? 0) * 100).toFixed(1).padStart(6)}  ` +
    `${String(s.charPxNear ?? '-').padStart(4)}..${String(s.charPxFar ?? '-').padEnd(4)}  ` +
    (b ? `${(b.max[0] - b.min[0]).toFixed(1)} / ${(b.max[1] - b.min[1]).toFixed(1)} / ${(b.max[2] - b.min[2]).toFixed(1)}` : 'NO GEOMETRY') +
    (s.error ? '   ERROR ' + s.error : '') + (s.authored ? '   (authored frame)' : ''));
}
if (orphans.length) { console.log('\nORPHANED walk meshes (owned by no camera):');
  for (const o of orphans.slice(0, 40)) console.log('  ' + o.name + '  — ' + o.why); }
console.log('\ncuts:');
for (const c of cuts) console.log(`  ${c.from.padEnd(14)} <-> ${c.to.padEnd(14)} on ${c.edge.padEnd(38)} t=${c.t.toFixed(3)} band ${c.band.w}u wide  margin ${c.margin >= 0 ? '+' : ''}${c.margin}`);
if (CG.noRibbon.length) { console.log('\nno camera boundary placed:'); for (const n of CG.noRibbon) console.log('  ' + n); }
if (C.warn.length) { console.log('\nWARNINGS:'); for (const w of C.warn) console.log('  ' + w); }
const bad = solved.filter((s) => s.error || (s.inFrameFrac ?? 0) < 0.999 || s.capped);
if (bad.length) console.log('\nFRAMING ATTENTION: ' + bad.map((s) => s.id + (s.capped ? '(capped)' : '') + (s.error ? '(error)' : '')).join(', '));
// --check answers ONE question — is this file stale — and its exit code must mean only
// that. Folding warnings into it made a fresh file report as stale (the four junction
// seams warn by design), which is exactly the kind of gate that gets ignored. Orphaned
// walk geometry is still a hard failure of a normal run: that IS a coverage hole.
process.exit(ARGS.includes('--check') ? staleExit : (orphans.length ? 1 : 0));
