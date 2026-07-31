// cine_solve.mjs — solve the cinematic cameras' framing and write the ONE numeric
// truth every downstream consumer reads.
//
//   node tools/cine_solve.mjs           write public/townmap/dellhollow.cameras.solved.json
//   node tools/cine_solve.mjs --check   fail if the solved file is stale (build gate)
//   node tools/cine_solve.mjs --print   report only, write nothing (the framing loop)
//   node tools/cine_solve.mjs --town emberbrook   any town with a <town>.cameras.json
//   node tools/cine_solve.mjs --cameras <rel>     solve a PROPOSED camera file instead
//                                                 (path relative to public/)
//   node tools/cine_solve.mjs --frame-exits --out <path>   propose a re-solve elsewhere
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
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
// THE TOWN. Every path this tool touches is derived from one id, so a second town runs
// the identical pipeline with no edit here (the house convention: see tools/seam_test.mjs).
const DEFAULT_TOWN = 'dellhollow';
const TOWN = opt('--town', DEFAULT_TOWN);
const MAP_REL = `townmap/${TOWN}.map.json`;
const CAMS_REL = opt('--cameras', `townmap/${TOWN}.cameras.json`);
const SHIPPED = path.join(PUB, `townmap/${TOWN}.cameras.solved.json`);
const OUT = opt('--out', null) ? path.resolve(process.cwd(), opt('--out', null)) : SHIPPED;
// This is the FIRST tool a new town runs, so it is the one that must say what is missing:
// everything downstream (cine_test, seam_walk, cine_bake) reads the file this one writes,
// and an ENOENT stack trace from three tools deep is not an answer.
for (const rel of [MAP_REL, CAMS_REL])
  if (!fs.existsSync(path.join(PUB, rel))) {
    console.error(`town '${TOWN}': public/${rel} does not exist. A cinematic town needs ` +
      `townmap/${TOWN}.map.json (topology) and townmap/${TOWN}.cameras.json (the shot ` +
      'list, with sceneKey + defaults + cameras[].owns) before anything can be solved.');
    process.exit(1);
  }
const C = loadCine(MAP_REL, CAMS_REL);
// THE WALK GEOMETRY BEING FRAMED. Same rule as seam_test.mjs: the map states its
// explorable bundle, and a town that has none is framed against its own cine bundle.
const WALK_BUNDLE = `assets/scenes/${C.map.walkSceneKey || C.camFile.sceneKey}/scene.glb`;

// ---- PER-SHOT FRAMING RULINGS (data, not code) -------------------------------
// Two flags belong to the camera RECORD in townmap/<town>.cameras.json:
//
//   "pin": true                  on a camera — this frame is a human ruling. The solver
//                                reproduces its authored pos/aim exactly and excludes it
//                                from new framing constraints. Requires pos+aim.
//   defaults.frameExits: false   for the whole town — opt OUT of framing exit seams
//                                (below). Only ever a MIGRATION flag: a town whose
//                                backdrops are already baked cannot absorb a re-aim until
//                                its re-bake pass, so it says so in its own data.
//
// Until the coordinator moves them into cameras.json they may live in a sidecar beside
// it — `townmap/<town>.cameras.pins.json`, merged onto the camera records here — so the
// solver itself only ever reads `cam.pin` / `C.D.frameExits`, and deleting the sidecar
// once the flags are in cameras.json changes nothing.
const PINFILE = path.join(PUB, CAMS_REL.replace(/\.cameras\.json$/, '.cameras.pins.json'));
const SIDE = fs.existsSync(PINFILE) ? JSON.parse(fs.readFileSync(PINFILE, 'utf8')) : {};
const sideNotes = [];
for (const id in (SIDE.pins || {})) {
  const cam = C.byId[id];
  if (!cam) { sideNotes.push(`pins sidecar names unknown camera '${id}'`); continue; }
  const p = SIDE.pins[id];
  for (const k in p) if (k[0] !== '_' && cam[k] === undefined) cam[k] = p[k];
  if (cam.pin && !(cam.pos && cam.aim))
    sideNotes.push(`camera '${id}' is pinned but has no authored pos/aim — a pin with ` +
                   'nothing to pin to is a no-op; author the frame or drop the pin');
}
// EXIT FRAMING is ON by construction — every future town gets it with no authoring, which
// is the point (a shot that does not frame its own exits is broken in the same way in
// every town). A town opts out explicitly, in its data, and Dellhollow currently does
// while its backdrops are baked against the old frames.
const FRAME_EXITS = ARGS.includes('--frame-exits') ? true
  : ARGS.includes('--no-frame-exits') ? false
  : C.D.frameExits !== undefined ? C.D.frameExits !== false
  : (SIDE.defaults || {}).frameExits !== false;

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
// ---- and the seams each shot is an EXIT of -----------------------------------
// The arrival half above answers "can a player appear off-screen". This answers the
// other half — "can a player WALK off-screen" — and it is derived from exactly the same
// cut geometry, so it needs no authoring and cannot drift: the point that must be in
// frame is the seam's CENTRE, the metre of path where the cut actually fires. Every
// seam is walkable both ways, so it is an exit of both shots it separates and is added
// to both. Doors and the portal are already covered: you leave through the same point
// you arrive on, so their exit IS their arrival.
const exitsIn = {};                           // camera id -> [map-space seam centres]
for (const c of CG.cuts) {
  const p = r2m(c.at);
  (exitsIn[c.from] = exitsIn[c.from] || []).push(p.slice());
  (exitsIn[c.to] = exitsIn[c.to] || []).push(p.slice());
}

// ---- solve each camera -------------------------------------------------------
const solved = [];
for (const cam of C.cams) {
  const s = solveCamera(C, cam, meshes, arrivalsIn[cam.id] || [],
                        FRAME_EXITS ? {exits: exitsIn[cam.id] || []} : null);
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
  //
  // A CINEMATIC PLATE PROBES THE WHOLE TOWN, and that is the point of the class. It
  // owns nothing, so "can the camera see its region" is vacuous; the only question a
  // vista has is HOW MUCH OF THE TOWN IT SHOWS, and that is the same question, asked
  // of every walk mesh instead of the owned ones. Same instrument, same 64-probe
  // budget, so the plate's visibleFrac is directly comparable with every other shot's
  // — and it is the bake's ray-cast that answers it, which is this project's only
  // visibility oracle ("in frame" != "visible" != "unobstructed ray").
  const probeSrc = cam.cinematic ? meshes : mine;
  const S = probeSrc.length
    ? [...sampleHeads(probeSrc, C.D.charH * 0.5), ...sampleHeads(probeSrc, C.D.charH)] : [];
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
    ...(FRAME_EXITS ? {pin: !!cam.pin, exitSeams: cam.pin ? 0 : (exitsIn[cam.id] || []).length} : {}),
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
    `${CAMS_REL} (intent) + ${MAP_REL} (topology)`,
    `+ ${WALK_BUNDLE} (the walk geometry being framed).`,
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
  sources: [CAMS_REL, MAP_REL, WALK_BUNDLE],
  ...(FRAME_EXITS ? {
    frameExits: true,
    _doc_frameExits: [
      'FRAMED WITH EXIT SEAMS. Each shot was fitted around its owned region, every',
      'ARRIVAL that lands in it AND the centre of every seam band it is an exit of, so',
      'a player can neither appear nor walk off-screen. Cameras with "pin": true keep',
      'their authored frame and are excluded from the constraint (per-camera `pin`).',
      'A town opts out with defaults.frameExits: false in its cameras file.',
    ],
    pinned: solved.filter((s) => s.pin).map((s) => s.id),
    pinSidecar: fs.existsSync(PINFILE) ? path.relative(PUB, PINFILE) : null,
  } : {}),
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
    console.error(`STALE: ${path.relative(PUB, OUT)} differs. Re-run tools/cine_solve.mjs` +
                  (TOWN === DEFAULT_TOWN ? '' : ` --town ${TOWN}`) + '.');
    staleExit = 1;
  } else console.log('cameras.solved.json is up to date.');
} else if (!ARGS.includes('--print')) {
  fs.mkdirSync(path.dirname(OUT), {recursive: true});
  fs.writeFileSync(OUT, json);
  console.log('wrote ' + path.relative(path.join(PUB, '..'), OUT));
}

// ---- the report (always: a run is self-verifying at a glance) ---------------
console.log(`\ncameras ${solved.length}   walk meshes ${meshes.length} (${orphans.length} orphaned)   cuts ${cuts.length}`);
console.log('exit-seam framing: ' + (FRAME_EXITS
  ? `ON — shots also frame the seams they exit through` +
    (solved.some((s) => s.pin) ? `; pinned (not re-aimed): ${solved.filter((s) => s.pin).map((s) => s.id).join(', ')}` : '')
  : 'OFF (this town opts out in its data while its backdrops are baked against the old frames)'));
for (const n of sideNotes) console.log('  PINS SIDECAR: ' + n);
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
