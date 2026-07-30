// routes_derive.mjs — DERIVE the intended route through every shot of a cinematic town.
//
//   node tools/routes_derive.mjs                 write public/townmap/<town>.routes.json
//   node tools/routes_derive.mjs --check         re-derive and FAIL if the file is stale
//   node tools/routes_derive.mjs --town <id>     another town (default dellhollow)
//   node tools/routes_derive.mjs --print <shot>  dump one shot to stdout
//
// WHY THIS IS DERIVED AND NOT HAND-DRAWN (see docs/plans/legibility-audit-design.md):
// the town already states its intended routes twice over, and neither statement is the
// walkmesh.
//   1. <town>.map.json — typed walk edges (road/deck/path/stairs/bridge) with waypoints.
//      This IS the designed network; the 315 walk_ meshes were GENERATED from it and are
//      wider than it by construction. "The walkable floor is larger than the intended
//      route" (the legibility plan's own diagnosis) is exactly the statement that the map
//      edge is the route and the walk mesh is the coverage.
//   2. <town>.cameras.json — every shot `owns` a set of those edges, with @t0..t1
//      fractions where a flight or a boardwalk is split between two shots.
// So a hand-authored polyline would be a THIRD truth that silently rots. Instead this
// reuses tools/cine_regions.mjs (the same ownership + projection the solver and the
// scene-graph generator use) and public/world/scenegraph.json (the same seams, doors and
// portals the runtime fires), and per-shot `overrides` in the output file are preserved so
// any derived line that is wrong can still be corrected by hand.
//
// ONE SUBTLETY WORTH THE READ: routes are partitioned by SEAM, not by ownership.
// Ownership answers "which shot does this walk mesh belong to" (coverage, corrections).
// A route needs "which camera is up while the player walks this metre", and those differ
// at the top of the gate stair: walk_e_valley-gate__inn_* is owned by shelf-west, but the
// seam sits at t=0.428, so the first 43% of that flight is walked UNDER THE GATE CAMERA
// and belongs to the gate shot's route. Deriving from cuts gets that right; deriving from
// ownership would drop the exit the player is looking for.
import fs from 'fs';
import path from 'path';
import {loadCine, edgePoint, m2r, r2m, project, charPx, PUB, rd} from './cine_regions.mjs';

const ARGS = process.argv.slice(2);
const flag = (n) => ARGS.includes(n);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const TOWN = opt('--town', 'dellhollow');
const OUT = path.join(PUB, 'townmap', `${TOWN}.routes.json`);
const FRAME = [1344, 768];                      // the baked backdrop's pixel size

// walkable classes, and the ones that LOOK like a way on but are not (the map's cargo
// winch and maintenance ladders ship no walk ribbon — scenegraph.json.noRibbon). They are
// emitted with role "blocked" on purpose: a ladder that reads as a route and refuses the
// player is a legibility defect, and the audit has to be able to see it.
const WALKABLE = {road: 1, deck: 1, path: 1, stairs: 1, bridge: 1};
const BLOCKED = {ladder: 1, winch: 1};
const MAXSEG = 2.0;                             // subdivide route polylines to this, metres
const r2 = (v) => v.map((n) => Math.round(n * 100) / 100);
const r3n = (n) => Math.round(n * 1000) / 1000;
const unit2 = (dx, dz) => { const L = Math.hypot(dx, dz) || 1; return [r3n(dx / L), r3n(dz / L)]; };

const C = loadCine(`townmap/${TOWN}.map.json`, `townmap/${TOWN}.cameras.json`);
const SG = rd('world/scenegraph.json');
const SCENE = C.map.playSceneKey || C.camFile.sceneKey;
const CINE = rd(`assets/scenes/${C.camFile.sceneKey}/cine.json`);
const CAMBY = Object.fromEntries(CINE.cameras.map((c) => [c.id, c]));
const warn = [];

// ============================================================ SEAMS AND DOORS ====
// Everything the runtime can fire in this scene, read straight out of the generated
// scene graph so the overlay marks the SAME points play does.
const CUTRE = new RegExp(`^${SCENE}>${SCENE}@cut:(.+?):([\\d.]+):(.+?)>(.+)$`);
const cutsOnEdge = {};                          // edgeKey -> [{t, pair:Set, ids:{}}]
const sgOut = [], sgIn = [];
for (const e of SG.edges) {
  if (e.from === SCENE) sgOut.push(e);
  if (e.to === SCENE && e.from !== SCENE) sgIn.push(e);
  const m = CUTRE.exec(e.id);
  if (!m) continue;
  const [, ek, ts, a, b] = m, t = +ts;
  const list = (cutsOnEdge[ek] = cutsOnEdge[ek] || []);
  let s = list.find((s) => Math.abs(s.t - t) < 1e-6);
  if (!s) { s = {t, shots: new Set(), dir: {}}; list.push(s); }
  s.shots.add(a); s.shots.add(b); s.dir[`${a}>${b}`] = e;
}
for (const k in cutsOnEdge) cutsOnEdge[k].sort((x, y) => x.t - y.t);

// reciprocal lookup: an edge id -> the edge that comes back
const byId = Object.fromEntries(SG.edges.map((e) => [e.id, e]));
const recip = (e) => (e.reciprocal ? byId[e.reciprocal] : null) ||
  SG.edges.find((o) => o.of === e.of && o.from === e.to && o.to === e.from) || null;

// ================================================== WHICH SHOT IS UP AT t ON AN EDGE ==
// The play-time partition of a map edge: walking from `from` to `to`, which camera is
// live over each interval. Seeded from the landmark owner at t=0 and flipped at every
// seam (each seam names exactly two shots, so "the other one" is well defined).
function shotIntervals(k) {
  const E = C.MEDGE[k], segs = C.edgeOwner[k] || [], cuts = cutsOnEdge[k] || [];
  let cur = C.lmOwner[E.rec.from] || (segs[0] && segs[0].cam) || null;
  if (!cuts.length) {                           // no seam on this edge: ownership is whole
    return segs.length ? segs.map((s) => ({t0: s.t0, t1: s.t1, shot: s.cam}))
                       : (cur ? [{t0: 0, t1: 1, shot: cur}] : []);
  }
  const out = [];
  let t0 = 0;
  for (const s of cuts) {
    const pair = [...s.shots];
    if (!pair.includes(cur)) {                  // seeding disagreed with the seam pair
      warn.push(`edge '${k}': seam at t=${s.t} names {${pair}} but shot at t<${s.t} is '${cur}'`);
      cur = pair[0];
    }
    out.push({t0, t1: s.t, shot: cur, seamAt: s.t});
    cur = pair.find((p) => p !== cur);
    t0 = s.t;
  }
  out.push({t0, t1: 1, shot: cur});
  return out.filter((i) => i.t1 - i.t0 > 1e-6);
}

// ======================================================== ROUTE POLYLINE BUILDING ====
// Points are RUNTIME coords. Vertices of the map polyline inside [t0,t1] are kept (the
// walk ribbon was built from those same corners, so the ground is linear between them)
// and long spans are subdivided so the overlay's ribbon can follow a slope.
function polyline(k, t0, t1) {
  const E = C.MEDGE[k], ts = [t0];
  for (let i = 1; i < E.pts.length - 1; i++) {
    const t = E.cum[i] / E.L;
    if (t > t0 + 1e-6 && t < t1 - 1e-6) ts.push(t);
  }
  ts.push(t1);
  const pts = [];
  for (let i = 0; i < ts.length - 1; i++) {
    const a = edgePoint(E, ts[i]), b = edgePoint(E, ts[i + 1]);
    const L = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
    const n = Math.max(1, Math.ceil(L / MAXSEG));
    for (let j = 0; j < n; j++) pts.push(edgePoint(E, ts[i] + (ts[i + 1] - ts[i]) * (j / n)));
  }
  pts.push(edgePoint(E, t1));
  return pts.map((p) => r2(m2r(p)));
}
const plen = (pts) => pts.reduce((s, p, i) => i ? s + Math.hypot(p[0] - pts[i - 1][0],
  p[1] - pts[i - 1][1], p[2] - pts[i - 1][2]) : 0, 0);

// ================================================================== MEASUREMENT ====
// Offline, geometric half of the rubric: where a point lands in the shot's frame and how
// big a character standing there would be. Occlusion is NOT guessed here — it is measured
// in the browser against the shot's own baked depth map (ROUTES.probe in route_overlay.js).
function project1(shot, rtPoint, lift) {
  const cam = CAMBY[shot]; if (!cam) return null;
  const p = r2m(rtPoint); p[2] += (lift === undefined ? 0 : lift);
  const s = project(cam.pos, cam.aim, cam.fov, C.D.aspect, p);
  if (s.behind) return {behind: true, onScreen: false, ndc: null, px: null, charPx: 0};
  return {behind: false,
          ndc: [r3n(s.sx), r3n(s.sy)],
          px: [Math.round((s.sx * 0.5 + 0.5) * FRAME[0]), Math.round((0.5 - s.sy * 0.5) * FRAME[1])],
          onScreen: Math.abs(s.sx) <= 1 && Math.abs(s.sy) <= 1,
          edgeMargin: r3n(Math.min(1 - Math.abs(s.sx), 1 - Math.abs(s.sy))),  // 0 = at the frame border
          depth: r3n(s.z),
          charPx: Math.round(charPx(cam.fov, s.z, C.D.charH, FRAME[1]))};
}
// FEET AND HEAD ARE DIFFERENT QUESTIONS, and conflating them mis-grades a shot. A seam
// 6 cm below the bottom of frame still shows the whole character walking into it (their
// head is 0.4 ndc higher) — what is missing is THE GROUND THEY ARE AIMING AT, which is a
// real but milder defect than walking out of frame entirely. So both are measured:
// `screen` = where the standing point is, `screenHead` = the top of the figure there.
function screenOf(shot, rtPoint) {
  const f = project1(shot, rtPoint, 0);
  if (!f) return null;
  const h = project1(shot, rtPoint, C.D.charH);
  f.headNdc = h && h.ndc;
  f.headOnScreen = !!(h && h.onScreen);
  f.figureVisible = f.onScreen || f.headOnScreen;      // any part of a standing player in frame
  f.groundVisible = f.onScreen;                        // the surface itself is shown
  return f;
}

// ============================================================= ENTRIES / EXITS ====
// A seam is an exit of one shot and an entry of its neighbour, so both lists are built
// from the same edge records, per shot, from that shot's point of view.
const shots = {};
const S = (id) => (shots[id] = shots[id] || {entries: [], exits: [], routes: []});
for (const c of C.cams) S(c.id);

for (const e of sgOut) {
  const from = e.camFrom; if (!from || !shots[from]) continue;
  const back = recip(e);
  const isCut = e.kind === 'cut';
  const at = r2(e.at.slice());
  // aim = the direction the player TRAVELS when taking this exit.
  //   seam   : the arrival sits past the band, so spawn-at is the way out.
  //   portal : you pass THROUGH it — the far-side arrival (the way back in) is the axis.
  //   door   : you walk INTO the structure, so at-(the street you come back out onto).
  let aim = null;
  if (isCut) aim = unit2(e.spawn[0] - e.at[0], e.spawn[2] - e.at[2]);
  else if (back && e.kind === 'portal') aim = unit2(back.spawn[0] - e.at[0], back.spawn[2] - e.at[2]);
  else if (back) aim = unit2(e.at[0] - back.spawn[0], e.at[2] - back.spawn[2]);
  S(from).exits.push({
    id: (isCut ? 'seam:' : e.kind + ':') + (e.of || e.id),
    kind: isCut ? 'seam' : e.kind, at,
    to: isCut ? e.cam.key : e.to, toKind: isCut ? 'shot' : 'scene',
    prompt: isCut ? null : (e.key || SG.defaults.key || 'e').toUpperCase(),
    label: e.label || null, aim,
    seam: e.band ? {n: e.band.n, t: e.band.t, w: e.band.w} : null,
    r: e.band ? null : e.r,
    via: e.id, screen: screenOf(from, at)});
  // the same record is an ENTRY of the shot it lands in
  const land = isCut ? e.cam.key : null;
  if (land && shots[land]) S(land).entries.push({
    id: 'seam:' + (e.of || e.id), kind: 'seam', at: r2(e.spawn.slice()),
    from, via: e.id, aim, seam: e.band ? {n: e.band.n, t: e.band.t, w: e.band.w} : null,
    screen: screenOf(land, e.spawn)});
}
for (const e of sgIn) {                          // coming back from an interior / the region
  const shot = e.cam && e.cam.key; if (!shot || !shots[shot]) continue;
  S(shot).entries.push({
    id: e.kind + ':' + (e.of || e.id), kind: e.kind, at: r2(e.spawn.slice()),
    from: e.from, via: e.id, label: e.label || null,
    aim: unit2(e.spawn[0] - e.at[0], e.spawn[2] - e.at[2]),
    screen: screenOf(shot, e.spawn)});
}
for (const c of C.cams) {                        // the bundle's own spawn, where it is real
  const k = CAMBY[c.id]; if (!k || !k.entry || !k.spawn) continue;
  S(c.id).entries.push({id: 'spawn:' + c.id, kind: 'spawn', at: r2(k.spawn.slice()),
    from: null, via: 'cine.json spawn', aim: null, screen: screenOf(c.id, k.spawn)});
}

// ==================================================================== ROUTES ====
for (const k of Object.keys(C.MEDGE)) {
  const E = C.MEDGE[k], type = E.rec.type;
  if (!WALKABLE[type] && !BLOCKED[type]) continue;
  const blocked = !!BLOCKED[type];
  const ivals = blocked
    ? [{t0: 0, t1: 1, shot: C.lmOwner[E.rec.from] || null}]   // no ribbon: one shot shows it
    : shotIntervals(k);
  for (const iv of ivals) {
    if (!iv.shot || !shots[iv.shot]) { if (!blocked) warn.push(`edge '${k}' t=${iv.t0}..${iv.t1}: no shot`); continue; }
    const pts = polyline(k, iv.t0, iv.t1);
    const whole = iv.t0 < 1e-6 && iv.t1 > 1 - 1e-6;
    shots[iv.shot].routes.push({
      id: `${iv.shot}:${k}` + (whole ? '' : `@${iv.t0}..${iv.t1}`),
      class: type, blocked: blocked || undefined,
      from: `node:${E.rec.from}`, to: `node:${E.rec.to}`,
      t: [r3n(iv.t0), r3n(iv.t1)],
      length: r3n(plen(pts)), points: pts,
      source: `map edge ${k}@${r3n(iv.t0)}..${r3n(iv.t1)}`});
  }
}

// role: a shot with no landmarks of its own is a TRANSIT VIGNETTE (4 of Dellhollow's 17
// are, by design) and its routes exist only to be walked on. Elsewhere the SPINE is the
// route that carries a player from one of the shot's entries to one of its exits; a route
// touching only one of them is a spine LINK, a route touching neither is a SPUR (a
// destination: a shop front, a notice board, a dead-end yard).
const NEAR = 3.2;
for (const c of C.cams) {
  const sh = shots[c.id], marks = [...sh.entries, ...sh.exits];
  const touches = (p) => marks.filter((m) => Math.hypot(m.at[0] - p[0], m.at[2] - p[2]) <= NEAR &&
    Math.abs(m.at[1] - p[1]) <= 2.5);
  const vignette = !(c.owns.landmarks || []).length;
  for (const r of sh.routes) {
    const a = touches(r.points[0]), b = touches(r.points[r.points.length - 1]);
    r.role = r.blocked ? 'blocked'
      : vignette ? 'vignette'
      : (a.length && b.length) ? 'spine'
      : (a.length || b.length) ? 'link' : 'spur';
    const ends = [...a, ...b].map((m) => (sh.exits.includes(m) ? 'exit:' : 'entry:') + m.id);
    if (ends.length) r.connects = [...new Set(ends)];
  }
  // measured: how much of this shot's walkable route is even in frame
  const samples = [];
  for (const r of sh.routes) { if (r.blocked) continue; for (const p of r.points) samples.push(p); }
  const on = samples.map((p) => project1(c.id, p, C.D.charH * 0.5)).filter(Boolean);
  const inFrame = on.filter((s) => s.onScreen).length;
  sh.name = c.name;
  sh.intent = c.shot || null;
  sh.district = (c.owns.landmarks || []).map((l) => C.LM[l] && C.LM[l].district).filter(Boolean)[0] || null;
  sh.owns = {landmarks: c.owns.landmarks || [], edges: c.owns.edges || []};
  sh.measure = {
    routeSamples: samples.length,
    routeInFramePct: samples.length ? Math.round(1000 * inFrame / samples.length) / 10 : null,
    routeLen: r3n(sh.routes.filter((r) => !r.blocked).reduce((s, r) => s + r.length, 0)),
    spineLen: r3n(sh.routes.filter((r) => r.role === 'spine' || r.role === 'vignette' || r.role === 'link')
      .reduce((s, r) => s + r.length, 0)),
    entriesGroundOffScreen: sh.entries.filter((e) => e.screen && !e.screen.groundVisible).map((e) => e.id),
    exitsGroundOffScreen: sh.exits.filter((e) => e.screen && !e.screen.groundVisible).map((e) => e.id),
    entriesFigureOffScreen: sh.entries.filter((e) => e.screen && !e.screen.figureVisible).map((e) => e.id),
    exitsFigureOffScreen: sh.exits.filter((e) => e.screen && !e.screen.figureVisible).map((e) => e.id),
    exitsAtFrameEdge: sh.exits.filter((e) => e.screen && e.screen.edgeMargin <= 0.35).map((e) => e.id),
    minCharPx: Math.min(...[...sh.entries, ...sh.exits].map((m) => (m.screen ? m.screen.charPx : 9999)), 9999),
    visibleFrac: CAMBY[c.id] ? CAMBY[c.id].visibleFrac : null};
}

// ============================================ CAMERA-vs-FLOOR OWNERSHIP MISMATCH ====
// Where the seam and the walk-mesh ownership DISAGREE, the player walks metres of one
// shot's floor while another shot's camera is up. Two consequences, both felt by a
// player: the positional safety net (sgCorrect) can fire there, and the authored cut
// lands late — you are already on the next tier's stair when the camera finally changes.
// It is a pure consequence of cutOffset (the seam sits 2.8 m out from the landmark pad
// so it is on the path and not on the pad), so it is by design — but it is exactly the
// "transitions take me by surprise" surface and it wants to be measurable.
const mismatch = [];
for (const k of Object.keys(C.MEDGE)) {
  const E = C.MEDGE[k];
  if (!WALKABLE[E.rec.type]) continue;
  const own = C.edgeOwner[k] || [], cam = shotIntervals(k);
  const ownAt = (t) => { const s = own.find((s) => t >= s.t0 - 1e-9 && t <= s.t1 + 1e-9); return s && s.cam; };
  for (const iv of cam) {
    const mid = (iv.t0 + iv.t1) / 2, o = ownAt(mid);
    if (!o || o === iv.shot) continue;
    mismatch.push({edge: k, t: [r3n(iv.t0), r3n(iv.t1)], metres: r3n((iv.t1 - iv.t0) * E.L),
                   cameraUp: iv.shot, floorOwnedBy: o,
                   at: r2(m2r(edgePoint(E, mid)))});
  }
}
mismatch.sort((a, b) => b.metres - a.metres);

// ======================================================================= WRITE ====
const prev = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : null;
const out = {
  _doc: [
    `ROUTES — the INTENDED path through every shot of ${TOWN}, and every point a player`,
    'can enter or leave one by. The legibility layer: scenegraph.json says what the',
    'runtime CAN fire, this says what the player is EXPECTED to do, so the two can be',
    'compared and the difference is a defect with coordinates.',
    '',
    'GENERATED by tools/routes_derive.mjs from <town>.map.json (the typed walk edges ARE',
    'the designed route), <town>.cameras.json (which shot owns which edge) and',
    'world/scenegraph.json (the seams, doors and portals the runtime fires). Re-run after',
    'any map, camera or scene-graph change; `--check` fails if this file is stale. Hand',
    'corrections go in `overrides`, which the generator preserves.',
    '',
    'COORDS: runtime [x, y(up), z], +x east +z south — the same frame as scenegraph',
    'at/spawn, so nothing here needs converting before it is drawn.',
    '',
    'shots: shotId -> { name, intent (what the shot is FOR, from cameras.json),',
    '  entries[], exits[], routes[], measure{} }. The key "*" means "the whole scene, no',
    '  shots" — that is how a real-time scene (townwalk, a future Emberbrook) uses this',
    '  same schema and the same overlay with no code change.',
    'entries/exits: { id, kind: seam|door|portal|spawn, at (where the player STANDS),',
    '  to/from, prompt (null = silent auto cut), aim (unit xz: the way the path runs',
    '  through this point), seam{n,t,w} band geometry, screen{} where it lands in frame }.',
    'routes: { id, class (road|deck|path|stairs|bridge|ladder), role: spine|link|spur|',
    '  vignette|blocked, points[] runtime polyline, connects[] which entries/exits it',
    '  touches, source }. role "blocked" is a way on that LOOKS walkable and is not (the',
    '  map ladders/winch ship no walk ribbon) — a legibility trap the audit must see.',
    'measure: the offline, geometric half of the audit rubric. OCCLUSION IS NOT HERE: it',
    '  is measured in the browser against each shot\'s own baked depth map by',
    '  ROUTES.probe() in public/js/route_overlay.js, because only the depth map knows',
    '  what the backdrop actually hides.',
    'mismatch: metres of walk floor whose OWNING shot is not the shot whose camera is up',
    '  while you walk it (a consequence of cutOffset placing the seam out on the path).',
    '  This is where sgCorrect can fire and where an authored cut lands late.'],
  version: 1, town: TOWN, scene: SCENE,
  generated: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
  generator: 'tools/routes_derive.mjs',
  sources: [`townmap/${TOWN}.map.json`, `townmap/${TOWN}.cameras.json`, 'world/scenegraph.json',
            `assets/scenes/${C.camFile.sceneKey}/cine.json`],
  appliesTo: [SCENE, C.map.walkSceneKey].filter(Boolean),
  coords: 'runtime [x, y(up), z]',
  frame: FRAME,
  defaults: {lift: 0.18, ribbonWidth: 0.55, beaconH: 2.1, labelScale: 1,
             entryColor: '2fff6a', exitColor: 'ff9a2e', routeColor: 'ffe08a',
             spurColor: 'a8c8ff', blockedColor: 'ff4d4d'},
  shots, mismatch, warnings: warn,
  overrides: (prev && prev.overrides) || {}};

// hand overrides win, and survive every re-derivation
for (const id in out.overrides) {
  if (!out.shots[id]) { warn.push(`override for unknown shot '${id}'`); continue; }
  Object.assign(out.shots[id], out.overrides[id]);
}

const text = JSON.stringify(out, null, 1) + '\n';
const strip = (s) => s && JSON.stringify({...JSON.parse(s), generated: null});
if (flag('--print')) { console.log(JSON.stringify(out.shots[opt('--print')], null, 1)); process.exit(0); }
if (flag('--check')) {
  const same = prev && strip(text) === strip(JSON.stringify(prev, null, 1) + '\n');
  if (!same) { console.error(`STALE: ${path.relative(process.cwd(), OUT)} — re-run node tools/routes_derive.mjs`); process.exit(1); }
  console.log(`ok  ${TOWN}.routes.json is up to date (${Object.keys(out.shots).length} shots)`);
  process.exit(warn.length ? 0 : 0);
}
fs.writeFileSync(OUT, text);
const n = (f) => Object.values(out.shots).reduce((s, v) => s + f(v), 0);
console.log(`wrote ${path.relative(process.cwd(), OUT)}`);
console.log(`  ${Object.keys(out.shots).length} shots · ${n((v) => v.entries.length)} entries · ` +
            `${n((v) => v.exits.length)} exits · ${n((v) => v.routes.length)} routes · ` +
            `${r3n(n((v) => v.measure.routeLen))} m of route`);
for (const id of Object.keys(out.shots)) {
  const v = out.shots[id], m = v.measure;
  console.log(`  ${id.padEnd(15)} in:${String(v.entries.length).padStart(2)} out:${String(v.exits.length).padStart(2)} ` +
    `routes:${String(v.routes.length).padStart(2)} spine:${String(m.spineLen).padStart(6)}m ` +
    `inFrame:${String(m.routeInFramePct).padStart(5)}% minCharPx:${String(m.minCharPx).padStart(4)}` +
    (m.entriesGroundOffScreen.length ? `  ENTRY-GROUND-OFF ${m.entriesGroundOffScreen.join(',')}` : '') +
    (m.exitsGroundOffScreen.length ? `  EXIT-GROUND-OFF ${m.exitsGroundOffScreen.join(',')}` : '') +
    (m.exitsFigureOffScreen.length ? `  EXIT-FIGURE-OFF ${m.exitsFigureOffScreen.join(',')}` : ''));
}
if (mismatch.length) {
  console.log(`camera-vs-floor ownership mismatch: ${r3n(mismatch.reduce((s, m) => s + m.metres, 0))} m over ${mismatch.length} spans`);
  for (const m of mismatch.slice(0, 8))
    console.log(`  ${m.metres.toFixed(1).padStart(5)}m  ${m.edge}@${m.t[0]}..${m.t[1]}  camera '${m.cameraUp}' over floor owned by '${m.floorOwnedBy}'`);
}
if (warn.length) { console.log('warnings:'); for (const w of warn) console.log('  ! ' + w); }
