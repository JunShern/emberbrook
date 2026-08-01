// cine_sweep.mjs — WHICH ANGLE SHOULD THIS SHOT BE AT? The framing loop, offline.
//
//   node tools/cine_sweep.mjs --town emberbrook                 sweep every camera
//   node tools/cine_sweep.mjs --town emberbrook --cams arch,square
//   node tools/cine_sweep.mjs --town emberbrook --yaw 0,20,..   yaw candidates
//                                               --pitch 10,18,.. pitch candidates
//   node tools/cine_sweep.mjs --town emberbrook --top 12        rows printed per shot
//   node tools/cine_sweep.mjs --town emberbrook --json <path>   full grid, machine-readable
//
// WHY IT EXISTS, AND WHY IT IS NOT tools/cine_visprobe.py. Two questions decide a shot's
// angle and neither one answers the other:
//
//   DOES THE REGION FIT?      cine_solve.mjs, milliseconds, no occluders. It is the
//                             reason the standoff is trustworthy and the reason a shot
//                             can report charPx at all.
//   CAN THE CAMERA SEE IT?    a ray-caster. It is the reason the map's 13 draft cameras
//                             were found buried inside cliffs, and the reason `yaw 5`
//                             on the north lane (which fits perfectly) is a wall of
//                             leaves at the near clip.
//
// cine_visprobe.py asks the second against the master blend in Blender, reading a
// SOLVED file — so it can only sweep angles for cameras that are already solved, it
// re-implements the solver's fit in a second language (the two must agree or the sweep
// is useless), and it costs a Blender launch and the memory cap that comes with it.
// This asks BOTH, in one process, by calling the actual solver — solveCamera() from
// cine_regions.mjs, with yaw/pitch overridden — so the fit reported here is not a
// re-implementation of the shipped fit, it IS the shipped fit. The ray-cast runs over
// the walk bundle's own triangles through a BVH built once.
//
// THE OCCLUDER SET IS THE WHOLE BUNDLE, deliberately: every mesh node in
// assets/scenes/<walkSceneKey>/scene.glb, walk pads and GateGrid bars included. That is
// what bpy `scene.ray_cast` hits in cine_bake.py's own visibility() — hide_render
// objects stay in the depsgraph — so the fractions printed here are on the same scale
// as every `% of 64 probes` already recorded in the camera notes and in cine.json's
// `visibleFrac`. `--nobars` drops the 20 bar_ meshes to measure what an invisible
// collision wall is costing a frame; on Emberbrook it costs nothing (measured 2026-08-01:
// identical fractions on all seven shots), which is worth knowing and not worth assuming.
//
// AND IT IS A SCREEN, NOT A VERDICT. The bundle is the BLOCKOUT: its trees are cones and
// its buildings are massing. A shot that measures 90% here can still be a wall of dressed
// foliage, and the bake's ray-cast against the dressed master remains the only oracle
// (docs/plans/town-legibility.md; CLAUDE.md's world-building doctrine). What this buys is
// that no angle is CHOSEN blind, and that the choice is re-runnable in eleven seconds.
import fs from 'fs';
import path from 'path';
import {loadCine, walkMeshes, ownerOfWalk, solveCamera, cutGeometry, charPx,
        PUB, r3, r2m} from './cine_regions.mjs';
import {occluders, NEAR_HARD, NEAR_FIELD_MIN, NEAR_SOFT_RAYS} from './cine_occlude.mjs';

const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const TOWN = opt('--town', 'dellhollow');
const TOP = +opt('--top', '10');
const NOBARS = ARGS.includes('--nobars');
// --cameras <rel>: sweep a PROPOSED shot list instead of the shipped one (path relative
// to public/), so "would splitting this shot help?" is a measurement and not an argument.
const C = loadCine(`townmap/${TOWN}.map.json`,
                   opt('--cameras', `townmap/${TOWN}.cameras.json`));
const WALK_BUNDLE = `assets/scenes/${C.map.walkSceneKey || C.camFile.sceneKey}/scene.glb`;
const GLB = path.join(PUB, WALK_BUNDLE);
const YAWS = (opt('--yaw', null) || Array.from({length: 18}, (_, i) => i * 20).join(','))
  .split(',').map(Number);
const PITCHES = (opt('--pitch', null) || [10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 56].join(','))
  .split(',').map(Number);
const ONLY = (opt('--cams', '') || '').split(',').filter(Boolean);
// LENS AND LEASH, sweepable because "widen the lens" and "let it stand further back" are
// the two things everyone reaches for when a shot will not fit, and neither one is
// obviously a lever: a wider lens lets the camera come closer AND shrinks the character
// in the same breath, and a longer leash buys the frame at the character's expense. Both
// default to the town's own authored numbers, so omitting them measures what ships.
const FOV = opt('--fov', null) === null ? null : +opt('--fov', null);
const MAXD = opt('--maxdist', null) === null ? null : +opt('--maxdist', null);
const MARGIN = opt('--margin', null) === null ? null : +opt('--margin', null);
if (FOV !== null) C.D.fov = FOV;
if (MAXD !== null) C.D.maxDist = MAXD;
if (MARGIN !== null) C.D.margin = MARGIN;
for (const c of C.cams) {
  if (FOV !== null) c.F.fov = FOV;
  if (MAXD !== null) c.F.maxDist = MAXD;
  if (MARGIN !== null) c.F.margin = MARGIN;
}

// ---------------------------------------------------------------- the geometry
const meshes = walkMeshes(GLB).meshes;
for (const m of meshes) m.owner = ownerOfWalk(C, m.name, m.center).cam;
const byCam = {};
for (const m of meshes) if (m.owner) (byCam[m.owner] = byCam[m.owner] || []).push(m);

// arrivals + exit seams, exactly as cine_solve builds them: a swept angle that does not
// frame the seam it exits by is not a candidate, and leaving them out would let the
// sweep recommend an angle the solver then refuses.
const CG = cutGeometry(C, GLB, () => {});
const arrivalsIn = {}, exitsIn = {};
for (const c of CG.cuts) {
  (arrivalsIn[c.to] = arrivalsIn[c.to] || []).push(r2m(c.spawnTo));
  (arrivalsIn[c.from] = arrivalsIn[c.from] || []).push(r2m(c.spawnFrom));
  const p = r2m(c.at);
  (exitsIn[c.from] = exitsIn[c.from] || []).push(p.slice());
  (exitsIn[c.to] = exitsIn[c.to] || []).push(p.slice());
}
for (const l of C.map.landmarks) {
  if (!l.enterable || !l.interiorSceneKey) continue;
  const own = C.lmOwner[l.id];
  if (own) (arrivalsIn[own] = arrivalsIn[own] || []).push(l.pos.slice());
}
for (const ex of C.map.exits || []) {
  const own = C.lmOwner[ex.at], lm = C.LM[ex.at];
  if (own && lm) (arrivalsIn[own] = arrivalsIn[own] || []).push(lm.pos.slice());
}

// --------------------------------------------------- occlusion + the near-field gate --
// Both ray-cast questions live in tools/cine_occlude.mjs so cine_sweep and any other
// consumer ask them the same way: `seenFrac` (can the camera SEE its region) and
// `nearField` (is something COVERING the frame). The second was ported from the dressing
// lane on 2026-08-01 and re-calibrated here against Dellhollow's sixteen accepted shots;
// its header carries the table. It is an ACCEPTANCE rule, not a score: a stand that fails
// it is dropped from the candidate list before ranking, because no amount of subject
// visibility redeems a frame whose foreground is a wall.
const OCC = occluders(WALK_BUNDLE, NOBARS ? {re: /^(?!bar_)/} : undefined);
const seenFrac = (posMap, probesMap) => OCC.seenFrac(posMap, probesMap);

// ------------------------------------------------------------------ the sweep --
// The probe set is cine_solve's own: chest AND head over every owned walk mesh, thinned
// to 64 evenly. Head-only probing called the Dellhollow gate 77% visible while the
// character stood fully behind a 1.4 m palisade at its own spawn.
function sampleHeads(mine, H) {
  const pts = [];
  for (const m of mine) {
    const [x0, y0] = m.min, [x1, y1] = m.max, h = m.max[2] + H;
    pts.push([(x0 + x1) / 2, (y0 + y1) / 2, h], [x0, y0, h], [x1, y0, h], [x0, y1, h], [x1, y1, h]);
  }
  return pts;
}
function pickSpread(pts, n) {
  if (pts.length <= n) return pts;
  const out = [], step = pts.length / n;
  for (let i = 0; i < n; i++) out.push(pts[Math.floor(i * step)]);
  return out;
}

const CHAR_PX_MIN = 50;                              // cine_test.mjs's town floor
const out = {town: TOWN, bundle: WALK_BUNDLE, occluders: OCC.triangles, nobars: NOBARS,
             yaws: YAWS, pitches: PITCHES, shots: {}};
const t0 = Date.now();
for (const cam of C.cams) {
  if (ONLY.length && !ONLY.includes(cam.id)) continue;
  const mine = byCam[cam.id] || [];
  if (!mine.length) { console.log(`\n=== ${cam.id}: owns no walk geometry — nothing to sweep`); continue; }
  const probes = pickSpread([...sampleHeads(mine, C.D.charH * 0.5),
                             ...sampleHeads(mine, C.D.charH)], 64);
  const rows = [];
  for (const yaw of YAWS) for (const pitch of PITCHES) {
    const probe = Object.assign({}, cam, {F: Object.assign({}, cam.F, {yaw, pitch})});
    delete probe.pos; delete probe.aim; delete probe.pin;
    const s = solveCamera(C, probe, meshes, arrivalsIn[cam.id] || [], {exits: exitsIn[cam.id] || []});
    if (s.error) continue;
    const nf = OCC.nearField(s.pos, s.aim, s.fov, s.aspect);
    rows.push({yaw, pitch, dist: s.dist, capped: !!s.capped, inFrame: s.inFrameFrac,
               charPxFar: s.charPxFar, charPxNear: s.charPxNear, zFar: s.zFar,
               pos: s.pos, aim: s.aim, vis: seenFrac(s.pos, probes),
               near: nf.frac, nearHard: nf.hardRays, nearSoft: nf.softRays, nearOk: nf.pass});
  }
  // RANKED ON VISIBILITY, because that is the question the solver cannot answer and the
  // one that has repeatedly been wrong. Everything else is printed beside it rather than
  // folded into a score: a single number would hide which constraint a row is failing,
  // and these constraints are not commensurable (a shot at 100% visible and 31 px is a
  // different problem from one at 40% and 60 px).
  const refused = rows.filter((r) => !r.nearOk).length;
  const kept = rows.filter((r) => r.nearOk);
  kept.sort((a, b) => b.vis - a.vis || b.charPxFar - a.charPxFar);
  rows.length = 0; rows.push(...kept);
  out.shots[cam.id] = {probes: probes.length, walkMeshes: mine.length, rows};
  const best = rows.filter((r) => !r.capped && r.charPxFar >= CHAR_PX_MIN);   // near-field already filtered
  console.log(`\n=== ${cam.id}  (${mine.length} walk meshes, ${probes.length} probes, ` +
              `authored yaw ${cam.F.yaw} pitch ${cam.F.pitch}) ===`);
  if (refused) console.log(`  ${refused} of ${refused + rows.length} stands REFUSED by the near-field gate ` +
    `(a ray inside ${NEAR_HARD} of the standoff) and are not ranked`);
  console.log('   yaw  pitch   dist  cap  frame%  charPx n..f   visible  near');
  for (const r of rows.slice(0, TOP))
    console.log(`  ${String(r.yaw).padStart(4)}  ${String(r.pitch).padStart(5)}  ` +
      `${r.dist.toFixed(1).padStart(5)}  ${r.capped ? ' ! ' : '   '}  ` +
      `${(r.inFrame * 100).toFixed(1).padStart(5)}  ${String(r.charPxNear).padStart(4)}..` +
      `${String(r.charPxFar).padEnd(4)}  ${(r.vis * 100).toFixed(1).padStart(5)}%`);
  const cur = rows.find((r) => r.yaw === cam.F.yaw && r.pitch === cam.F.pitch);
  if (cur) console.log(`  authored: yaw ${cur.yaw} pitch ${cur.pitch} -> dist ${cur.dist.toFixed(1)}` +
    `${cur.capped ? ' (CAPPED)' : ''}, frame ${(cur.inFrame * 100).toFixed(1)}%, ` +
    `charPx ${cur.charPxNear}..${cur.charPxFar}, visible ${(cur.vis * 100).toFixed(1)}%`);
  const bestPx = rows.reduce((a, r) => Math.max(a, r.charPxFar), 0);
  const bestUncapped = rows.filter((r) => !r.capped);
  console.log(`  CEILINGS over ${rows.length} fitted angles: best charPxFar ${bestPx}px ` +
    `(town floor ${CHAR_PX_MIN}px), uncapped angles ${bestUncapped.length}, ` +
    `angles clearing BOTH ${best.length}` +
    (best.length ? ` (best: yaw ${best[0].yaw} pitch ${best[0].pitch}, ${(best[0].vis * 100).toFixed(1)}% visible)` : ''));
}
console.log(`\nswept ${YAWS.length}x${PITCHES.length} angles over ${OCC.triangles} occluder triangles ` +
            `in ${((Date.now() - t0) / 1000).toFixed(1)}s${NOBARS ? '  (bar_ meshes excluded)' : ''}`);
const JSONOUT = opt('--json', null);
if (JSONOUT) { fs.writeFileSync(JSONOUT, JSON.stringify(out, null, 1)); console.log(`wrote ${JSONOUT}`); }
