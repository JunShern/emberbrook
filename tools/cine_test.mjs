// cine_test.mjs — PROVE the cinematic town: that all of Dellhollow is playable as a
// sequence of fixed cameras, and that nothing about it can silently rot.
//
//   node tools/cine_test.mjs             assert everything, print the report
//   node tools/cine_test.mjs --town emberbrook   any town with a <town>.cameras.json
//   node tools/cine_test.mjs --plan      also print the browser playthrough plan
//                                        (dense polylines for tools/cine_walk.js)
//   node tools/cine_test.mjs --no-bundle skip the baked-art assertions (pre-bake runs)
//
// It asserts five independent kinds of thing, because each can break alone:
//
//  A. COVERAGE     every walk_ mesh of the explorable town lies inside exactly one
//                  camera's owned region, and every landmark and every walk edge of
//                  the town map has an owner. This is the brief's hard requirement:
//                  no walkable metre of Dellhollow without a camera that shows it.
//  B. FRAMING      per shot: its region's character-height sample points project
//                  inside the frame (in-frame fraction), the character is legible at
//                  the far end (pixel height), and — from the bake — the camera could
//                  actually SEE the region it owns (Blender ray-casts, recorded in
//                  cine.json as visibleFrac).
//  C. CHAIN        cameras.json -> cameras.solved.json -> cine.json -> the shipped
//                  PNGs all agree about every camera's pos/aim/fov. A camera the
//                  render and the runtime disagree about is the image-vs-geometry
//                  disease this project keeps curing.
//  D. GRAPH        the town is one connected component under camera cuts alone: from
//                  the entry shot, walking the emitted cut edges reaches every shot;
//                  every cut is reciprocal; every arrival stands on the walk network;
//                  every interior door is still reachable and still prompts.
//  E. HYSTERESIS   crossing a boundary back and forth N times produces EXACTLY N
//                  cuts: every arrival is clear of the band that sends you back, by a
//                  reported margin. A promptless auto edge that oscillates would
//                  strobe the screen.
//
// What it deliberately does NOT do: drive the collision walker or read a pixel. That
// needs the real runtime and lives in tools/cine_walk.js (browser payload, SIM-driven).
// The two together cover "the shot list is right" and "a player can walk it".
import fs from 'fs';
import path from 'path';
import {execFileSync} from 'child_process';
import {loadGlb} from './glb_read.mjs';
import {occluders, NEAR_HARD, NEAR_FIELD_MIN, NEAR_SOFT_RAYS} from './cine_occlude.mjs';
import {loadCine, walkMeshes, ownerOfWalk, project, charPx, edgePoint, edgeT,
        shotRegions, shotAt, inShot, nearestShot, shotDist,
        m2r, r2m, PUB, rd} from './cine_regions.mjs';

const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const NO_BUNDLE = ARGS.includes('--no-bundle');
// THE TOWN. One id; every file in the chain this gate asserts (cameras.json -> solved ->
// cine.json -> scenegraph.json -> the master blend) is derived from it, exactly as
// tools/seam_test.mjs does. `TOWNID` is the town; `TOWN` below stays the SCENE KEY of the
// cinematic bundle, which is what the rest of this file has always meant by that name.
const DEFAULT_TOWN = 'dellhollow';        // == tools/cine_bake.py's own --town default
const TOWNID = opt('--town', DEFAULT_TOWN);
let pass = 0, fail = 0, warnN = 0;
const ok = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); }
  else { fail++; console.log('  FAIL ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
const note = (m) => console.log('       ' + m);
const soft = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); }
  else { warnN++; console.log('  warn ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
const head = (s) => console.log('\n== ' + s);

const C = loadCine(`townmap/${TOWNID}.map.json`, `townmap/${TOWNID}.cameras.json`);
const SOLVED = rd(`townmap/${TOWNID}.cameras.solved.json`);
const SG = rd('world/scenegraph.json');
// The CINEMATIC bundle's scene key. The camera file states it and the solved file
// copies it from there (cine_solve.mjs writes `sceneKey: C.camFile.sceneKey`), so this
// is the solved file's own scene key by construction and needs no second lookup.
const TOWN = C.camFile.sceneKey;
const BUNDLE = path.join(PUB, 'assets/scenes', TOWN);
const START = 'ow-valley';
// LEGIBILITY GATE. 1.7 m of character in a 768-line frame. 55 px is 7.2% of frame
// height: below that a player loses their own avatar in the backdrop, which is the
// one thing a fixed camera must never allow. Stated here so it can be argued with.
const CHAR_PX_MIN = 50;
const IN_FRAME_MIN = 0.999;
// THE CINEMATIC SHOT CLASS (coordinator ruling). A camera with `"cinematic": true` is a
// non-walkable establishing plate: it is exempt from CHAR_PX_MIN and from owning walk
// records, because the player may be a speck or absent in it. THE EXEMPTION IS NARROW
// AND ITS BOUNDS ARE ASSERTED, not merely intended — see the CINEMATIC section below.
// Without those assertions the flag is a loophole: any under-legible walkable shot could
// be relabelled a plate and stop being measured. What keeps that shut is that a plate
// owns NOTHING, so it cannot be where a player walks, and no seam may deliver one to it.
const CINE_CAMS = C.cams.filter((c) => c.cinematic);
const WALK_CAMS = C.cams.filter((c) => !c.cinematic);
const isCine = (id) => CINE_CAMS.some((c) => c.id === id);

// ============================================================== A. COVERAGE ====
head('COVERAGE — every walkable metre of the town belongs to exactly one shot');
try {
  execFileSync(process.execPath,
    [path.join(PUB, '../tools/cine_solve.mjs'), '--town', TOWNID, '--check'], {stdio: 'pipe'});
  ok(true, 'cameras.solved.json is up to date with cameras.json + the map + the walk bundle');
} catch (e) { ok(false, 'cameras.solved.json is STALE (re-run tools/cine_solve.mjs)'); }
try {
  execFileSync(process.execPath, [path.join(PUB, '../tools/scenegraph_derive.mjs'), '--check'], {stdio: 'pipe'});
  ok(true, 'scenegraph.json is up to date with the map files + the camera file');
} catch (e) { ok(false, 'scenegraph.json is STALE (re-run tools/scenegraph_derive.mjs)'); }

ok(C.warn.length === 0, `camera ownership is well-formed (${C.warn.length} problems)`, C.warn.slice(0, 6));
// the map side: totality over records
for (const l of C.map.landmarks)
  ok(!!C.lmOwner[l.id], `landmark '${l.id}' is owned by a camera` +
     (C.lmOwner[l.id] ? ` ('${C.lmOwner[l.id]}')` : ''));
for (const k of Object.keys(C.MEDGE)) {
  const segs = C.edgeOwner[k] || [];
  const tiled = segs.length && Math.abs(segs[0].t0) < 1e-6 &&
    Math.abs(segs[segs.length - 1].t1 - 1) < 1e-6 &&
    segs.every((s, i) => i === 0 || Math.abs(s.t0 - segs[i - 1].t1) < 1e-6);
  ok(tiled, `walk edge '${k}' is fully owned` +
     (segs.length > 1 ? ` (split ${segs.map((s) => `${s.cam}@${s.t0}..${s.t1}`).join(' | ')})`
                      : segs.length ? ` ('${segs[0].cam}')` : ''));
}
// the geometry side: totality over the shipped walk meshes of BOTH bundles (the
// explorable dev bundle and the cinematic one — they must agree, and the cinematic
// bundle is what the player actually collides with)
const bundles = [{key: C.map.walkSceneKey, why: 'the real-time explore bundle'}];
if (!NO_BUNDLE) bundles.push({key: TOWN, why: 'the cinematic bundle the player collides with'});
const meshSets = {};
for (const b of bundles) {
  const p = path.join(PUB, 'assets/scenes', b.key, 'scene.glb');
  if (!fs.existsSync(p)) { ok(false, `bundle '${b.key}' exists (${b.why})`); continue; }
  const {meshes} = walkMeshes(p);
  let orphan = [], multi = 0;
  for (const m of meshes) {
    const o = ownerOfWalk(C, m.name, m.center);
    m.owner = o.cam; m.via = o.via;
    if (!o.cam) orphan.push(m.name + ' — ' + o.via);
  }
  meshSets[b.key] = meshes;
  ok(orphan.length === 0,
     `${b.key}: all ${meshes.length} walk_ meshes lie in an owned region (${b.why})`,
     orphan.slice(0, 8));
  // "exactly one" — ownership is a function of the mesh NAME, so exclusivity is
  // structural; assert it anyway, it is the claim being made
  ok(meshes.every((m) => typeof m.owner === 'string'), `${b.key}: ownership is single-valued`);
}
if (meshSets[C.map.walkSceneKey] && meshSets[TOWN]) {
  const a = meshSets[C.map.walkSceneKey], b = meshSets[TOWN];
  ok(a.length === b.length,
     `the cinematic bundle carries the same walk network as the explore bundle (${a.length} vs ${b.length} meshes)`);
  const an = new Set(a.map((m) => m.name)), miss = b.filter((m) => !an.has(m.name)).map((m) => m.name);
  ok(miss.length === 0, 'no walk mesh appears in one bundle and not the other', miss.slice(0, 6));
}
const MESH = meshSets[TOWN] || meshSets[C.map.walkSceneKey];
const byCam = {};
for (const m of MESH) (byCam[m.owner] = byCam[m.owner] || []).push(m);
for (const cam of C.cams) {
  const n = (byCam[cam.id] || []).length;
  if (cam.cinematic)
    ok(n === 0, `cinematic plate '${cam.id}' owns ZERO walk geometry (${n} meshes) — bound (a) of the exemption`);
  else
    ok(n > 0, `shot '${cam.id}' actually owns walk geometry (${n} meshes)`);
}

// =============================================================== B. FRAMING ====
// The near-field gate measures against the EXPLORE bundle, the same geometry cine_sweep
// chose the angles against, so the gate and the chooser cannot disagree about what is in
// front of a lens. Skipped with --no-bundle, like every other geometry assertion here.
const NEAR = NO_BUNDLE ? null : occluders(`assets/scenes/${C.map.walkSceneKey || TOWN}/scene.glb`);
head('FRAMING — each shot holds its region, and the character is legible in it');
const solvedById = Object.fromEntries(SOLVED.cameras.map((c) => [c.id, c]));
for (const cam of C.cams) {
  const s = solvedById[cam.id];
  if (!s) { ok(false, `shot '${cam.id}' is in the solved file`); continue; }
  ok(!s.error, `shot '${cam.id}': solved without error`, s.error);
  // A PLATE IS NOT FRAMED AGAINST A REGION, so none of the four framing gates below has
  // anything to say about it: there is no owned ground to be in frame, no standoff the
  // solver chose, and no far corner to measure a character at. It is asserted instead in
  // the CINEMATIC section — which is a strictly stronger requirement than skipping, since
  // that section proves the plate cannot BE walked in.
  if (cam.cinematic) {
    ok(s.cinematic === true && s.authored === true,
       `plate '${cam.id}': carries the cinematic flag into the solved file (authored frame, standoff ${s.dist}u)`);
    ok(s.charPxFar === null && s.charPxNear === null && s.inFrameFrac === null,
       `plate '${cam.id}': reports legibility as NULL, not as a number that looks like a passing gate`,
       {charPxFar: s.charPxFar, inFrameFrac: s.inFrameFrac});
    continue;
  }
  ok((s.inFrameFrac || 0) >= IN_FRAME_MIN,
     `shot '${cam.id}': ${(s.inFrameFrac * 100).toFixed(1)}% of its region's character-height samples are IN FRAME`,
     s.inFrameFrac >= IN_FRAME_MIN ? undefined : {inFrameFrac: s.inFrameFrac, samples: s.samples});
  ok(!s.capped, `shot '${cam.id}': standoff ${s.dist}u is not against its maxDist cap` +
     (s.capped ? ` (solver wanted ${s.solvedDist}u — the region wants splitting)` : ''));
  // PER-SHOT LEGIBILITY OVERRIDE (`charPxMin` on the camera record). One town-wide floor
  // cannot express a ruling about ONE shot, and the alternative that keeps getting reached
  // for — lowering the global floor — would quietly re-grade every camera in the town. So a
  // shot may name its own number, and this gate then enforces THAT number rather than
  // waiving the check: an override is a tighter contract, not an exemption from one. Two
  // conditions keep it from spreading: an override may only be LOWER than the town floor
  // (raising one is fine and needs no ceremony), and it must be accompanied by a
  // `_charPxMin_why` in the same record, so no future reader meets a bare number.
  const floor = cam.charPxMin ?? CHAR_PX_MIN;
  if (cam.charPxMin !== undefined) {
    ok(typeof cam.charPxMin === 'number' && cam.charPxMin > 0 && cam.charPxMin < CHAR_PX_MIN,
       `shot '${cam.id}': charPxMin override ${cam.charPxMin}px is a real relaxation of the ${CHAR_PX_MIN}px town floor`,
       {charPxMin: cam.charPxMin});
    ok(typeof cam._charPxMin_why === 'string' && cam._charPxMin_why.length > 80,
       `shot '${cam.id}': the override is ARGUED in its own record (_charPxMin_why)`);
  }
  ok(s.charPxFar >= floor,
     `shot '${cam.id}': character legible across the shot (${s.charPxFar}px at the far corner, ${s.charPxNear}px near; gate ${floor}px` +
     (cam.charPxMin !== undefined ? ', a NAMED per-shot override of the town\'s ' + CHAR_PX_MIN + 'px' : '') + ')',
     s.charPxFar >= floor ? undefined : {charPxFar: s.charPxFar, floor, zFar: s.zFar});
  // THE NEAR-FIELD GATE. `inFrameFrac` says the region FITS and the bake's visibleFrac
  // says the camera can SEE it; neither can see a slab standing in front of the lens that
  // no ray to the subject happens to pass through. Ported from the dressing lane
  // 2026-08-01 (their district stand read 89% clear with a wall in frame) and calibrated
  // here against Dellhollow's sixteen accepted shots, which put ZERO of thirteen frustum
  // rays inside 0.25 of their standoff — that is the hard line, and it is the towns' own
  // number rather than one chosen for them. tools/cine_occlude.mjs carries the table and
  // the two reductions that were tried and measured worse.
  const nf = NEAR ? NEAR.nearField(s.pos, s.aim, s.fov, C.D.aspect) : null;
  if (nf) {
    ok(nf.pass, `shot '${cam.id}': near field is clear — no frustum ray lands inside ` +
       `${NEAR_HARD} of the ${nf.standoff}u standoff (nearest ${nf.frac})`,
       nf.pass ? undefined : {hardRays: nf.hardRays, nearest: nf.frac, atNdc: nf.worstNdc});
    soft(!nf.warn, `shot '${cam.id}': at most ${NEAR_SOFT_RAYS} frustum rays inside ` +
         `${NEAR_FIELD_MIN} of the standoff (has ${nf.softRays}, nearest ${nf.frac})`);
  }
  // re-derive the projection here rather than trusting the solved numbers: the
  // solved file is an artifact and this is the assertion that it is a CORRECT one
  const mine = byCam[cam.id] || [];
  let inF = 0, tot = 0, worst = 0;
  for (const m of mine) {
    const pts = [[m.center[0], m.center[1], m.max[2]], [m.min[0], m.min[1], m.max[2]],
                 [m.max[0], m.max[1], m.max[2]]];
    for (const g of pts) for (const h of [0, C.D.charH]) {
      const q = project(s.pos, s.aim, s.fov, C.D.aspect, [g[0], g[1], g[2] + h]);
      tot++;
      if (!q.behind && Math.abs(q.sx) <= 1 && Math.abs(q.sy) <= 1) inF++;
      if (!q.behind) worst = Math.max(worst, q.z);
    }
  }
  ok(tot > 0 && inF === tot,
     `shot '${cam.id}': independently re-projected ${tot} region points, ${inF} in frame`,
     inF === tot ? undefined : {inFrame: inF, of: tot});
}

// ================================================================= C. CHAIN ====
head('CHAIN — one number per camera, agreed by the author, the render and the runtime');
let CINE = null;
if (!NO_BUNDLE) {
  const p = path.join(BUNDLE, 'cine.json');
  ok(fs.existsSync(p), `${TOWN}/cine.json exists (the bake's record of what it rendered)`);
  if (fs.existsSync(p)) {
    CINE = JSON.parse(fs.readFileSync(p, 'utf8'));
    const bk = Object.fromEntries(CINE.cameras.map((c) => [c.id, c]));
    ok(CINE.cameras.length === C.cams.length,
       `every authored shot is baked (${CINE.cameras.length} of ${C.cams.length})`,
       CINE.cameras.length === C.cams.length ? undefined
         : {missing: C.cams.filter((c) => !bk[c.id]).map((c) => c.id)});
    for (const cam of C.cams) {
      const b = bk[cam.id], s = solvedById[cam.id];
      if (!b) { ok(false, `shot '${cam.id}': baked`); continue; }
      const same = (u, v) => u.length === v.length && u.every((x, i) => Math.abs(x - v[i]) < 0.002);
      ok(same(b.pos, s.pos) && same(b.aim, s.aim) && Math.abs(b.fov - s.fov) < 1e-6,
         `shot '${cam.id}': the BAKED camera is the SOLVED camera (pos/aim/fov identical)`,
         {baked: [b.pos, b.aim, b.fov], solved: [s.pos, s.aim, s.fov]});
      ok(b.depth && b.depth.width === 1344 && b.depth.height === 768,
         `shot '${cam.id}': depth baked at the runtime drawing-buffer resolution 1344x768`, b.depth);
      ok(b.depth && b.depth.encoding === 'rgb24-viewz',
         `shot '${cam.id}': depth encoding is the one play3d.html's shader decodes`);
      ok(b.depth && b.depth.far > b.depth.near && b.depth.near > 0,
         `shot '${cam.id}': depth range is sane (${b.depth && b.depth.near.toFixed(2)} .. ${b.depth && b.depth.far.toFixed(2)})`);
      ok(b.rtClip && b.rtClip[0] < b.depth.near && b.rtClip[1] > b.depth.far,
         `shot '${cam.id}': the runtime clip range brackets the baked depth range (${b.rtClip})`);
      for (const [what, rel] of [['background', b.art.bg], ['depth map', b.art.depth]]) {
        const f = path.join(BUNDLE, rel);
        const sz = fs.existsSync(f) ? fs.statSync(f).size : 0;
        ok(sz > 20000, `shot '${cam.id}': ${what} is shipped (${rel}, ${(sz / 1e6).toFixed(2)} MB)`);
      }
      // the bake's own answer to "can this camera see its region"
      // CALIBRATED, not invented: the probe set is every owned walk mesh's CORNERS at
      // chest and head height, and a scaffold town occludes its own corners — the
      // human-ACCEPTED Boatyard v10 frame scores 0.48. So 0.45 is the bar. A threshold
      // of 0.75 would flag half the town for failing to beat a frame a human approved.
      // For a PLATE the same instrument answers a different question, because its probes
      // are the WHOLE TOWN's walk meshes rather than an owned region's (cine_solve). So
      // this line reports the vista's honest coverage. NO BAR IS APPLIED: 45% is
      // calibrated to "a shot can see the ground it owns", and re-using it here would
      // silently turn a coverage measurement into a pass/fail nobody calibrated.
      if (cam.cinematic)
        note(`plate '${cam.id}': shows ${((b.visibleFrac ?? 0) * 100).toFixed(1)}% of the ` +
             `town by ray-cast (${b.probes} probes over EVERY walk mesh, not an owned region) ` +
             '— reported, not gated');
      else
        soft((b.visibleFrac ?? 0) >= 0.45,
          `shot '${cam.id}': the camera SEES its region — ${((b.visibleFrac ?? 0) * 100).toFixed(0)}% of ${b.probes} probes unoccluded (bar 45%, the accepted Boatyard v10 frame's own score)`,
          {visibleFrac: b.visibleFrac});
      // A PLATE HAS NO FALLBACK SPAWN and must not: the spawn is picked from the shot's
      // own owned walk meshes, and a plate owns none. `?cam=<plate>` on a bare load falls
      // through to the bundle's default spawn, which is correct — a plate is a frame you
      // are shown, not a place you stand.
      if (cam.cinematic)
        ok(!b.spawn, `plate '${cam.id}': has NO bundle spawn — it is not a place you stand`);
      else
        ok(!!b.spawn, `shot '${cam.id}': has a bundle fallback spawn` + (b.spawn ? ` (from ${b.spawnFrom})` : ''));
    }
    // STALENESS AGAINST THE LIVE MASTER. District detailing happens IN the master, one
    // agent at a time, and a shot rendered before somebody rebuilt the tier it looks at
    // is a picture of a town that no longer exists. Bakes open the master read-only so
    // concurrency is safe — staleness is the only risk, so it is measured, per shot, and
    // the fix is printed. SOFT, because "the market tier is mid-build" is a true and
    // acceptable state to ship a night's work in.
    const master = path.join(PUB, `../tools/blends/${TOWNID}-master.blend`);
    if (fs.existsSync(master)) {
      const mt = fs.statSync(master).mtimeMs;
      const stale = [];
      for (const c of CINE.cameras) {
        const f = path.join(BUNDLE, c.art.bg);
        if (fs.existsSync(f) && fs.statSync(f).mtimeMs < mt) stale.push(c.id);
      }
      soft(stale.length === 0,
        `every shot's art is NEWER than the live master (${new Date(mt).toISOString().slice(11, 19)})` +
        (stale.length ? ` — ${stale.length} stale: ${stale.join(',')}` : ''));
      // The printed command is the MINIMAL correct one: cine_bake.py's --town defaults to
      // DEFAULT_TOWN, so naming it there would be noise, and omitting it for any other
      // town would be wrong. The default is written down once, above.
      if (stale.length) note(`re-bake:  Blender -b tools/blends/${TOWNID}-master.blend ` +
        `-P tools/cine_bake.py -- ` +
        (TOWNID === DEFAULT_TOWN ? '' : `--town ${TOWNID} `) + `--cams ${stale.join(',')}`);
    }
    ok(fs.existsSync(path.join(BUNDLE, 'scene.glb')), `${TOWN}: the SHARED collision GLB is shipped`);
    const g = fs.statSync(path.join(BUNDLE, 'scene.glb')).size;
    note(`one collision GLB of ${(g / 1e6).toFixed(1)} MB shared by ${C.cams.length} shots ` +
         `(per-camera bundles would have shipped ${(g * C.cams.length / 1e6).toFixed(0)} MB of identical bytes)`);
  }
}

// ================================================================= D. GRAPH ====
head('GRAPH — the whole town is walkable camera-to-camera, doors still work');
const town = SG.nodes[TOWN];
ok(!!town, `'${TOWN}' is a node in the scene graph`);
ok(town && town.rt !== true, `'${TOWN}' is NOT wired as a real-time explore scene (fixed cameras)`);
ok(town && !(town.params || {}).rt, `'${TOWN}' is not handed rt=1`);
// SCOPED TO THIS TOWN. These were unfiltered, which was correct while the graph held one
// town and silently wrong the moment it held two: `--town emberbrook` then validated
// DELLHOLLOW's cuts, doors and portals against EMBERBROOK's walk geometry and failed 30
// assertions about a town it was not asked to test. The scene-internal assertion below
// still does its job, because the filter admits an edge with EITHER end in this town and
// then requires BOTH.
const mine = (e) => e.from === TOWN || e.to === TOWN;
const cuts = SG.edges.filter((e) => e.kind === 'cut' && mine(e));
const doors = SG.edges.filter((e) => e.kind === 'door' && mine(e));
const portals = SG.edges.filter((e) => e.kind === 'portal' && mine(e));
ok(cuts.length > 0, `the graph carries camera cuts (${cuts.length} directed, ${cuts.length / 2} seams)`);
ok(cuts.every((e) => e.from === TOWN && e.to === TOWN),
   'every cut is a SCENE-INTERNAL handoff (to === from) — no bundle reload on a camera change');
ok(cuts.every((e) => e.auto === true), 'every cut fires on entry (auto) — no prompt to change camera');
ok(cuts.every((e) => !e.label), 'every cut is SILENT (no label) — prompts are for doors and portals only');
ok(cuts.every((e) => e.band && e.band.n && e.band.w > 0),
   'every cut triggers on a BAND across the corridor, not a sphere you can walk around');
ok(cuts.every((e) => e.camFrom && e.cam && e.cam.key),
   'every cut states the shot it leaves and the shot it applies');
const byId = new Map(SG.edges.map((e) => [e.id, e]));
for (const e of cuts) {
  const r = byId.get(e.reciprocal);
  ok(!!r && r.camFrom === e.cam.key && r.cam.key === e.camFrom,
     `cut ${e.camFrom}->${e.cam.key} on ${e.of}: the way back exists and reverses it`);
}
// CAMERA CONNECTIVITY: walk the cut graph from the entry shot
// THE ENTRY SHOT IS A WALKABLE ONE. A plate is entered by the portal, never by a cut,
// so rooting the cut graph at it would root it at a vertex with no edges.
const entry = WALK_CAMS.find((c) => c.entry) || WALK_CAMS[0];
ok(!!entry && !entry.cinematic, `the entry shot '${entry && entry.id}' is a WALKABLE shot, not a plate`);
const adjC = {};
for (const e of cuts) (adjC[e.camFrom] = adjC[e.camFrom] || []).push(e.cam.key);
const seenC = new Set([entry.id]), qC = [entry.id];
while (qC.length) for (const t of adjC[qC.shift()] || []) if (!seenC.has(t)) { seenC.add(t); qC.push(t); }
for (const cam of WALK_CAMS)
  ok(seenC.has(cam.id), `shot '${cam.id}' is REACHABLE from the entry shot '${entry.id}' by camera cuts alone`);
ok(seenC.size === WALK_CAMS.length,
   `no unreachable pocket: ${seenC.size} of ${WALK_CAMS.length} walkable shots reachable` +
   (CINE_CAMS.length ? ` (${CINE_CAMS.length} cinematic plate(s) excluded — they are entered by portal, not by cut)` : ''),
   seenC.size === WALK_CAMS.length ? undefined : {unreachable: WALK_CAMS.filter((c) => !seenC.has(c.id)).map((c) => c.id)});
// and back: every shot can reach the entry (a one-way cut would trap the player)
const radjC = {};
for (const e of cuts) (radjC[e.cam.key] = radjC[e.cam.key] || []).push(e.camFrom);
const backC = new Set([entry.id]), qB = [entry.id];
while (qB.length) for (const t of radjC[qB.shift()] || []) if (!backC.has(t)) { backC.add(t); qB.push(t); }
for (const cam of WALK_CAMS)
  ok(backC.has(cam.id), `shot '${cam.id}' can get BACK to '${entry.id}' (no one-way trap)`);

// every interior door is still there, still prompts, and is offered in a real shot
const enterable = C.map.landmarks.filter((l) => l.enterable && l.interiorSceneKey);
for (const l of enterable) {
  const d = doors.find((e) => e.from === TOWN && e.of === l.id);
  ok(!!d, `door '${l.id}' -> ${l.interiorSceneKey}: still wired from the cinematic town`);
  if (!d) continue;
  ok(!!d.label && !d.auto, `door '${l.id}': still PROMPTS (label "${d.label}", not auto)`);
  ok(!!d.camFrom && seenC.has(d.camFrom),
     `door '${l.id}': offered in shot '${d.camFrom}', which is reachable`);
  const back = byId.get(d.reciprocal);
  ok(back && back.cam && back.cam.key === d.camFrom,
     `door '${l.id}': coming back out returns to the SAME shot that frames the door`);
}
for (const e of portals) {
  if (e.to === TOWN) ok(!!(e.cam && e.cam.key), `portal '${e.id}': names the shot the town opens on (${e.cam && e.cam.key})`);
  else ok(!!e.camFrom, `portal '${e.id}': the way out is only offered in shot '${e.camFrom}'`);
}
// reachability of the whole graph from the region, as slice_test asserts
const adj = {};
for (const e of SG.edges) (adj[e.from] = adj[e.from] || []).push(e.to);
const seen = new Set([START]), q = [START];
while (q.length) for (const t of adj[q.shift()] || []) if (!seen.has(t)) { seen.add(t); q.push(t); }
for (const k of Object.keys(SG.nodes)) ok(seen.has(k), `scene '${k}': reachable from ${START}`);

// GEOMETRY of the cuts: trigger and arrival on the walk network of the town
head('GRAPH — every seam and every arrival stands on the walk network');
const G = loadGlb(path.join(PUB, 'assets/scenes',
  fs.existsSync(path.join(BUNDLE, 'scene.glb')) ? TOWN : C.map.walkSceneKey, 'scene.glb'));
const WALK = /^walk/i;
const onWalk = (p, tol) => G.tops(WALK, p[0], p[2]).some((y) => Math.abs(y - p[1]) <= tol);
for (const e of cuts) {
  ok(onWalk(e.at, 0.5), `cut ${e.camFrom}->${e.cam.key} (${e.of}): the SEAM is on the walk network`, e.at);
  ok(onWalk(e.spawn, 0.35), `cut ${e.camFrom}->${e.cam.key} (${e.of}): the ARRIVAL is on the walk network`, e.spawn);
}
// AND the arrival must be inside the frame of the shot it arrives in — a player who
// materialises off-screen is exactly the failure the brief names
for (const e of cuts) {
  const s = solvedById[e.cam.key];
  const m = r2m(e.spawn);
  const q = project(s.pos, s.aim, s.fov, C.D.aspect, [m[0], m[1], m[2] + C.D.charH * 0.5]);
  const inF = !q.behind && Math.abs(q.sx) <= 1 && Math.abs(q.sy) <= 1;
  ok(inF, `cut ${e.camFrom}->${e.cam.key}: you arrive IN FRAME of '${e.cam.key}' ` +
     `(screen ${q.sx.toFixed(2)},${q.sy.toFixed(2)}, ${Math.round(charPx(s.fov, q.z, C.D.charH, 768))}px tall)`,
     inF ? undefined : {sx: +q.sx.toFixed(2), sy: +q.sy.toFixed(2)});
}
for (const e of doors.filter((x) => x.to === TOWN)) {
  const s = solvedById[e.cam.key];
  const m = r2m(e.spawn);
  const q = project(s.pos, s.aim, s.fov, C.D.aspect, [m[0], m[1], m[2] + C.D.charH * 0.5]);
  ok(!q.behind && Math.abs(q.sx) <= 1 && Math.abs(q.sy) <= 1,
     `${e.label}: you come back out IN FRAME of '${e.cam.key}'`, {sx: +q.sx.toFixed(2), sy: +q.sy.toFixed(2)});
}
for (const e of portals.filter((x) => x.to === TOWN)) {
  // A portal whose town has no camera over its gate has no `cam` at all. That is
  // already asserted above ("names the shot the town opens on"), and it USED TO
  // CRASH HERE reading e.cam.key — which is worse than a red line, because a gate
  // that throws takes every assertion BELOW it with it: Emberbrook never reached the
  // safety-net, cinematic or hysteresis sections at all. A missing camera is a
  // failure to report, not an exception to raise.
  if (!(e.cam && e.cam.key && solvedById[e.cam.key])) {
    ok(false, `${e.label}: arrives in a solved shot (cam ${e.cam ? e.cam.key : 'null'}) ` +
       `— cannot check the arrival is in frame without one`);
    continue;
  }
  const s = solvedById[e.cam.key];
  const m = r2m(e.spawn);
  const q = project(s.pos, s.aim, s.fov, C.D.aspect, [m[0], m[1], m[2] + C.D.charH * 0.5]);
  ok(!q.behind && Math.abs(q.sx) <= 1 && Math.abs(q.sy) <= 1,
     `${e.label}: you arrive in town IN FRAME of '${e.cam.key}'`, {sx: +q.sx.toFixed(2), sy: +q.sy.toFixed(2)});
}

// ================================================= E. THE POSITIONAL SAFETY NET ===
head('SAFETY NET — a player who never crosses a seam still gets the right camera');
// Seams only fire if you cross them, and a player does not always cross them: collision
// let one SLIDE DOWN THE SLOPE beside the gate stair, bypass the band entirely and arrive
// 25 m away still under the gate camera, completely off-screen. The cure is positional,
// and these are the properties it has to have.
const REG = shotRegions(C, path.join(BUNDLE, 'scene.glb'), MESH);
// COUNTED OVER THE WALKABLE SHOTS. A plate owns no ground, so it has no region — and
// that absence is not a gap, it is the mechanism: with the plate in no region, the
// runtime's positional correction finds the arriving player on the walkable shot's
// ground under a camera that owns none of it and hands off, which is the entire
// implementation of "shown on arrival, then hands off to the first walkable shot".
ok(REG.length === WALK_CAMS.length,
   `every walkable shot has an ownership region shipped (${REG.length} of ${WALK_CAMS.length})`);
ok(REG.every((r) => !isCine(r.id)),
   'no cinematic plate has an ownership region — that absence IS the handoff mechanism');
const regById = Object.fromEntries(REG.map((r) => [r.id, r]));
ok(SG.nodes[TOWN] && Array.isArray(SG.nodes[TOWN].shots) &&
   SG.nodes[TOWN].shots.length === WALK_CAMS.length,
   'the regions are shipped in scenegraph.json, the file the runtime already fetches');
// AN OWNERLESS WALK SURFACE IS A FAILURE, NOT A CRASH — and until 2026-08-01 it was a
// crash: `inShot(regById[undefined])` threw a TypeError and took the whole gate down at
// this line, so Emberbrook's cine_test had never once run to its own summary and the
// eight assertions BELOW this point had never been evaluated for that town at all. The
// condition is real and diagnosable (a walk mesh in the collision bundle that no camera
// claims — usually a bundle exported before the map moved, or an ownership hole), so it
// is stated as its own assertion with the names attached, and the loop that follows
// skips what it cannot answer instead of dying on it. A test that crashes reports one
// bit; a test that fails reports which meshes.
const ownerless = MESH.filter((m) => !m.owner || !regById[m.owner]);
ok(ownerless.length === 0,
   `every one of the ${MESH.length} walk surfaces in the collision bundle is CLAIMED by a shot`,
   ownerless.length ? {count: ownerless.length, sample: ownerless.slice(0, 5).map((m) => m.name),
     hint: `the bundle is assets/scenes/${TOWN}/scene.glb; ownership is decided against ` +
           `${C.map.walkSceneKey || '(the cine bundle)'} — if those two bundles are from ` +
           'different builds of the town this is a STALE BAKE, not an ownership hole'} : undefined);
ok(REG.reduce((a, r) => a + r.boxes.length, 0) === MESH.length,
   `every one of the ${MESH.length} walk surfaces is a box in exactly one region`);

// 1. QUIET DURING NORMAL PLAY: standing on your own shot's ground must never resolve to
//    somebody else, or the net would fight the seams it is meant to back up.
let wrongOwn = [];
for (const m of MESH) {
  if (!m.owner || !regById[m.owner]) continue;             // counted above, by name
  const p = [m.rt.center[0], m.rt.max[1], m.rt.center[2]];
  if (!inShot(regById[m.owner], p)) wrongOwn.push(m.name);
}
ok(wrongOwn.length === 0,
   `standing on any of the ${MESH.length - ownerless.length} CLAIMED walk surfaces is inside ` +
   'its OWN shot\'s region', wrongOwn.slice(0, 5));

// 2. THE REPRO. Slid down the slope beside the gate stair, ending here still in 'gate'.
// A LIVE FAILURE, kept as a permanent regression fixture — and a fixture belongs to the
// town that produced it, so it is stated per town rather than assumed of every town. A
// new town has no such point until one of its own defects earns it; asserting Dellhollow's
// coordinate against Emberbrook's geometry would be a test of nothing.
const REPROS = {dellhollow: {at: [44.7, 19.5, -5.7], stuckIn: 'gate'}};
const REPRO = REPROS[TOWNID] || null;
if (REPRO) {
  const OFFROUTE = REPRO.at;
  const near = nearestShot(REG, OFFROUTE);
  const resolved = shotAt(REG, OFFROUTE) || near.id;
  ok(!!resolved, `the off-route slide point ${OFFROUTE.join(',')} resolves to a shot ` +
     `('${resolved}'${shotAt(REG, OFFROUTE) ? ' by containment' : ` by nearest ground, ${near.dist.toFixed(2)}u away`})`);
  ok(near.dist < 12, `it is near real ground (${near.dist.toFixed(2)}u), not out in the void`);
  ok(resolved !== REPRO.stuckIn,
     `it does NOT resolve to '${REPRO.stuckIn}' — the shot the player was stuck in (got '${resolved}')`);
  ok(!inShot(regById[REPRO.stuckIn], OFFROUTE),
     `'${REPRO.stuckIn}' does not own that ground, so the correction is not suppressed by the in-own-region test`);
  if (resolved) {
    const s = solvedById[resolved];
    const mp = r2m(OFFROUTE);
    const q = project(s.pos, s.aim, s.fov, C.D.aspect, [mp[0], mp[1], mp[2] + C.D.charH * 0.5]);
    const on = !q.behind && Math.abs(q.sx) <= 1 && Math.abs(q.sy) <= 1;
    ok(on, `and the corrected shot '${resolved}' has that point IN FRAME ` +
       `(screen ${q.sx.toFixed(2)},${q.sy.toFixed(2)}, ${Math.round(charPx(s.fov, q.z, C.D.charH, 768))}px) ` +
       '— the player is back on screen',
       on ? undefined : {sx: +q.sx.toFixed(2), sy: +q.sy.toFixed(2)});
  }
}
// 3. EVERY shot's ground is in frame of the shot that owns it, so a correction ALWAYS
//    lands the player on screen no matter where the off-route travel ended.
let offFrame = [];
for (const m of MESH) {
  const s = solvedById[m.owner];
  if (!s) continue;                       // ownerless: named in its own assertion above
  const mp = [m.center[0], m.center[1], m.max[2] + C.D.charH * 0.5];
  const q = project(s.pos, s.aim, s.fov, C.D.aspect, mp);
  if (q.behind || Math.abs(q.sx) > 1 || Math.abs(q.sy) > 1) offFrame.push(m.name + '/' + m.owner);
}
ok(offFrame.length === 0,
   `correcting to the owning shot always puts the player ON SCREEN (checked ` +
   `${MESH.length - ownerless.length} of ${MESH.length} surfaces)`,
   offFrame.slice(0, 5));
ok(SG.defaults.correctionGrace > 0 && SG.defaults.correctionPad > 0 && SG.defaults.correctionVTol > 0,
   `the net's tunables ship as data (grace ${SG.defaults.correctionGrace} steps, ` +
   `pad ${SG.defaults.correctionPad}u, vTol ${SG.defaults.correctionVTol}u)`);

// ====================================================== CINEMATIC — THE BOUNDS ===
// The coordinator's ruling approved the class WITH its fence: "keep the exemption
// NARROW; the class must never become a loophole for under-legible walkable shots."
// These are that fence. A plate is exempt from CHAR_PX_MIN, and in exchange it must be
// provably unwalkable — owning no ground and reachable by no seam. If a future agent
// flags a real walkable shot `cinematic` to quiet the legibility gate, the shot still
// owns its records and its seams still name it, and this section fails.
head(`CINEMATIC — ${CINE_CAMS.length} plate(s): the exemption's bounds hold`);
for (const cam of CINE_CAMS) {
  const own = C.map.landmarks.filter((l) => C.lmOwner[l.id] === cam.id).map((l) => l.id);
  const oe = Object.keys(C.edgeOwner).filter((k) => (C.edgeOwner[k] || []).some((s) => s.cam === cam.id));
  ok(own.length === 0 && oe.length === 0,
     `plate '${cam.id}': owns no map record either (0 landmarks, 0 edges)`, {landmarks: own, edges: oe});
  const asDest = cuts.filter((e) => e.cam.key === cam.id);
  const asSrc = cuts.filter((e) => e.camFrom === cam.id);
  ok(asDest.length === 0,
     `plate '${cam.id}': NO seam targets it as a walk destination — bound (b) of the exemption`,
     asDest.map((e) => e.id));
  ok(asSrc.length === 0, `plate '${cam.id}': no seam leaves from it either`, asSrc.map((e) => e.id));
  ok(!doors.some((e) => e.camFrom === cam.id || (e.cam && e.cam.key === cam.id)),
     `plate '${cam.id}': no door is offered in it and none returns to it`);
  ok(!cam.entry, `plate '${cam.id}': is not the town's cut-graph entry shot`);
}
// THE ESTABLISHING PLATE and its handoff, asserted against the wiring the runtime reads.
const estab = CINE_CAMS.filter((c) => c.establishing);
ok(estab.length <= 1, `at most ONE camera claims "establishing" (${estab.length})`,
   estab.map((c) => c.id));
if (estab.length === 1) {
  const P0 = estab[0];
  const inb = portals.filter((e) => e.to === TOWN);
  ok(inb.length > 0 && inb.every((e) => e.cam && e.cam.key === P0.id),
     `every portal into '${TOWN}' opens on the plate '${P0.id}' (${inb.length} portal(s))`,
     inb.map((e) => e.id + ' -> ' + (e.cam && e.cam.key)));
  for (const e of inb) {
    ok(!!(e.handoff && e.handoff.key),
       `portal '${e.id}': states the walkable shot the plate hands off to` +
       (e.handoff ? ` ('${e.handoff.key}')` : ''));
    ok(e.handoff && !isCine(e.handoff.key) && regById[e.handoff.key],
       `portal '${e.id}': the handoff shot '${e.handoff && e.handoff.key}' is walkable and owns ground`);
    // The handoff must be the shot that owns the ground the player is PUT DOWN ON —
    // otherwise the plate hands off to a camera that is about to be corrected away.
    const land = shotAt(REG, e.spawn) || nearestShot(REG, e.spawn).id;
    ok(e.handoff && e.handoff.key === land,
       `portal '${e.id}': the handoff shot is the one that owns the arrival ground ` +
       `(spawn resolves to '${land}')`);
    // and the way back out is offered in THAT shot, not in the plate
    const back = byId.get(e.reciprocal);
    ok(back && back.camFrom === (e.handoff ? e.handoff.key : null),
       `portal '${e.id}': the way back out is offered in '${back && back.camFrom}', the shot you are handed to`);
  }
}

// ============================================================ E. HYSTERESIS ====
head('HYSTERESIS — a silent auto cut fires once per crossing, never oscillates');
// THE CONDITION, per seam: the arrival must sit OUTSIDE the band that sends you back.
// A band is a 3D test (|along| <= t, |across| <= w, |dy| <= vTol) so being clear in
// ANY ONE of those is being clear — which matters, because on the town's hairpin
// flights along-clearance is geometrically unobtainable and HEIGHT is what separates
// the two sides. Report which dimension each seam relies on.
const inBand = (p, c) => {
  const ax = p[0] - c.at[0], az = p[2] - c.at[2];
  const along = Math.abs(ax * c.band.n[0] + az * c.band.n[1]);
  const across = Math.abs(-ax * c.band.n[1] + az * c.band.n[0]);
  const dy = Math.abs(p[1] - c.at[1]);
  return {in: along <= c.band.t && across <= c.band.w && dy <= (c.vTol ?? 2),
          along, across, dy,
          mAlong: along - c.band.t, mAcross: across - c.band.w, mDy: dy - (c.vTol ?? 2)};
};
let minMargin = Infinity; const relies = {across: 0, along: 0, height: 0};
for (const e of cuts) {
  const r = byId.get(e.reciprocal);
  if (!r) continue;
  const h = inBand(e.spawn, r);
  const m = Math.max(h.mAlong, h.mAcross, h.mDy);
  minMargin = Math.min(minMargin, m);
  const by = h.mAlong === m ? 'across the seam' : h.mDy === m ? 'in height (a hairpin flight)' : 'off the corridor';
  ok(!h.in && m > 0.35,
     `cut ${e.camFrom}->${e.cam.key} (${e.of}): arrival is outside the band that sends you back, by ${m.toFixed(2)}u ${by}`,
     h.in || m <= 0.35 ? {along: +h.along.toFixed(2), t: r.band.t, dy: +h.dy.toFixed(2), vTol: r.vTol} : undefined);
  relies[h.mAlong === m ? 'along' : h.mDy === m ? 'height' : 'across']++;
}
note(`tightest clearance over ${cuts.length} directed cuts: ${minMargin.toFixed(2)}u; ` +
     `${relies.along} seams separate along the path, ${relies.height} by height (hairpins), ${relies.across} across the corridor`);

// ---- AND THE OTHER ARRIVALS: nobody materialises inside a camera-cut band ----
// The assertions above ask a CUT's arrival about the band it just crossed. This one
// asks every OTHER arrival into the town — an interior door's return spawn, a portal
// walking in off the road — about ALL of them, because those arrivals never crossed a
// seam and so nothing above was ever going to look at them.
//
// WHY IT MATTERS (measured 2026-08-01): a spawn inside a band is a player who
// materialises already holding a cut. play3d's sgTick fires an `auto` edge on entry,
// so the arrival applies its own camera and the band fires on the very next physics
// step: ONE DOOR RENDERS TWO SHOTS. Three of Dellhollow's six door arrivals did this —
// weapon-shop (0.951 m inside), armor-shop (0.157 m inside), keepers-cottage (0.450 m
// under the floor) — and the weapon shop's is transition_test's door-7 failure, worth
// +510 geometries over the per-(scene, shot) baseline: two shots' art, not a leak.
//
// THE FLOOR IS 0.5 m, one stride, the same hard floor cine_regions puts under a
// hand-authored cut arrival and the same floor tools/scenegraph_derive.mjs pushes
// derived arrivals out to. This is the gate that holds it: the derive can be re-run,
// scenegraph.json can be hand-edited, and a camera file can move a band under a spawn
// that was clear when it was derived. Any of those three shows up here.
const ARRIVAL_BAND_FLOOR = 0.5;
const arrivals = [...doors, ...portals].filter((e) => e.to === TOWN && e.spawn);
ok(arrivals.length > 0, `there are non-cut arrivals into '${TOWN}' to check (${arrivals.length})`);
let worstArrival = {m: Infinity, id: null};
for (const e of arrivals) {
  let worst = {m: Infinity, c: null, h: null};
  for (const c of cuts) {
    const h = inBand(e.spawn, c);
    const m = Math.max(h.mAlong, h.mAcross, h.mDy);
    if (m < worst.m) worst = {m, c, h};
  }
  if (!worst.c) continue;
  if (worst.m < worstArrival.m) worstArrival = {m: worst.m, id: e.id};
  const by = worst.h.mAlong === worst.m ? 'across the seam'
           : worst.h.mDy === worst.m ? 'in height' : 'off the corridor';
  ok(worst.m >= ARRIVAL_BAND_FLOOR,
     `${e.kind} arrival '${e.id}' clears every cut band — nearest is ` +
     `${worst.c.camFrom}->${worst.c.cam.key} (${worst.c.of}) by ${worst.m.toFixed(2)}u ${by}`,
     worst.m >= ARRIVAL_BAND_FLOOR ? undefined
       : {spawn: e.spawn, band: worst.c.at, along: +worst.h.along.toFixed(3),
          t: worst.c.band.t, across: +worst.h.across.toFixed(3), w: worst.c.band.w,
          dy: +worst.h.dy.toFixed(3), vTol: worst.c.vTol,
          why: 'the arrival would fire this cut on entry — one door, two shots'});
}
note(`tightest non-cut arrival: ${worstArrival.id} at ${worstArrival.m.toFixed(2)}u ` +
     `(floor ${ARRIVAL_BAND_FLOOR}u)`);

// N crossings -> EXACTLY N cuts, through a faithful model of the runtime's own rule
// set: nearest live band wins, an edge only exists in the shot it leaves (camFrom),
// and after every cut EVERY edge is re-armed as `armed = !inRange` so an arrival
// inside a trigger cannot fire it. Taking a cut also MOVES the player to its arrival —
// the thing that makes a promptless auto edge safe. tools/cine_walk.js runs the same
// crossings through the real sgTick in a browser; this catches it without one.
// The player is driven by ARC LENGTH along the seam's own edge polyline, not by
// chasing waypoints in straight lines. Two reasons, both learned the hard way here:
// on a switchback the straight line between two points of one flight cuts across the
// OTHER seam of the same flight (the slice's harness lesson 6 in a new costume), and a
// waypoint-chaser that gets TELEPORTED past its target turns round, walks back through
// the band and ping-pongs forever — a bug in the test that looks exactly like a bug in
// the town. Arc length has neither problem: a cut moves `s`, the direction never
// changes, and the leg ends when `s` passes the far end.
function simSeam(E, sA, sB, startShot, trips) {
  let shot = startShot, fired = [], armed = new Map();
  const rearm = () => { armed = new Map(); for (const c of cuts) armed.set(c.id, null); };
  const sOf = (p) => edgeT(E, r2m(p)) * E.L;
  const at = (s) => m2r(edgePoint(E, Math.max(0, Math.min(1, s / E.L))));
  rearm();
  for (let trip = 0; trip < trips; trip++) {
    for (const [from, to] of [[sA, sB], [sB, sA]]) {
      const dir = Math.sign(to - from) || 1;
      let s = from;
      for (let guard = 0; guard < 2000 && (to - s) * dir > 1e-9; guard++) {
        s += 0.2 * dir;
        const p = at(s);
        let best = null;
        for (const c of cuts) {
          if (c.camFrom !== shot) continue;
          const h = inBand(p, c), a = armed.get(c.id);
          if (a === null) { armed.set(c.id, !h.in); continue; }
          if (!h.in) { armed.set(c.id, true); continue; }
          if (!a) continue;
          if (!best || h.along < best.h.along) best = {c, h};
        }
        if (best) { shot = best.c.cam.key; fired.push(best.c.id); s = sOf(best.c.spawn); rearm(); }
      }
    }
  }
  return {shot, fired};
}
const N = 5;
for (const e of cuts.filter((x) => x.camFrom < x.cam.key)) {
  const r = byId.get(e.reciprocal);
  if (!r) continue;
  const E = C.MEDGE[e.of];
  const res = simSeam(E, edgeT(E, r2m(r.spawn)) * E.L, edgeT(E, r2m(e.spawn)) * E.L, e.camFrom, N);
  ok(res.fired.length === N * 2 && res.shot === e.camFrom,
     `seam ${e.camFrom}<->${e.cam.key} (${e.of}): ${N} round trips along the path fired exactly ${N * 2} cuts, ended in '${e.camFrom}'`,
     {fired: res.fired.length, expected: N * 2, endedIn: res.shot,
      shots: [...new Set(res.fired.map((f) => byId.get(f).cam.key))]});
}

// ============================================================== THE REPORT =====
head('SHOT INVENTORY');
console.log('shot            walk  standoff  charPx      shot type   owns');
for (const c of SOLVED.cameras) {
  const kinds = [c.entry ? 'ENTRY' : '', c.transit ? 'transit' : '', c.authored ? 'authored' : ''].filter(Boolean).join('+') || 'scene';
  const owns = [...(c.owns.landmarks || []), ...(c.owns.edges || []).map((e) => e.replace(/__/g, '>'))];
  console.log(`${c.id.padEnd(15)} ${String(c.walkMeshes).padStart(4)}  ${String(c.dist).padStart(8)}  ` +
    `${String(c.charPxNear).padStart(4)}..${String(c.charPxFar).padEnd(4)}  ${kinds.padEnd(11)} ${owns.length} records`);
}
head('THE CUT MAP (what the player sees change, and where)');
for (const e of cuts.filter((x) => x.camFrom < x.cam.key))
  console.log(`  ${e.camFrom.padEnd(14)} <-> ${e.cam.key.padEnd(14)} on ${e.of.padEnd(38)} band ${e.band.w}u wide`);

if (ARGS.includes('--plan')) {
  head('BROWSER PLAYTHROUGH PLAN (feed to tools/cine_walk.js CINEWALK.plan)');
  // A grand tour: every shot entered at least once, over the map's own walk network.
  const LM = {}; for (const l of C.map.landmarks) LM[l.id] = l;
  const NET = {};
  for (const e of C.map.edges) {
    const pts = [LM[e.from].pos, ...(e.waypoints || []), LM[e.to].pos].map(m2r);
    const L = pts.slice(1).reduce((a, p, i) => a + Math.hypot(p[0] - pts[i][0], p[2] - pts[i][2]), 0);
    (NET[e.from] = NET[e.from] || []).push({to: e.to, L, pts, type: e.type});
    (NET[e.to] = NET[e.to] || []).push({to: e.from, L, pts: [...pts].reverse(), type: e.type});
  }
  const route = (a, b) => {
    const dist = {[a]: 0}, prev = {}, done = new Set();
    for (;;) {
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
    while (cur !== a) { const p = prev[cur]; legs.unshift(p.e); cur = p.from; }
    return legs;
  };
  const dense = (pts, step = 0.6) => {
    const o = [[+pts[0][0].toFixed(2), +pts[0][2].toFixed(2)]];
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], b = pts[i + 1], L = Math.hypot(b[0] - a[0], b[2] - a[2]);
      const n = Math.max(1, Math.ceil(L / step));
      for (let k = 1; k <= n; k++) o.push([+(a[0] + (b[0] - a[0]) * k / n).toFixed(2),
                                          +(a[2] + (b[2] - a[2]) * k / n).toFixed(2)]);
    }
    return o;
  };
  // the tour, landmark to landmark, chosen to enter every shot.
  // AUTHORED PER TOWN, because "a route that enters every shot" is a fact about one town's
  // landmarks. A town states its own in townmap/<town>.tour.json (`{"tour": [ids...]}`);
  // Dellhollow's predates that file and lives here until it is moved. Without one there is
  // no plan to write, and writing a wrong one over world/cine_tour.json would hand
  // tools/cine_walk.js another town's route.
  const TOURS = {dellhollow: ['valley-gate', 'porters-yard', 'valley-gate', 'winch-head', 'valley-gate',
                'inn', 'item-shop', 'weapon-shop', 'armor-shop', 'shelf-homes',
                'market-stalls', 'quay-deck', 'cookhouse', 'deep-stairs-head',
                'deep-stairs-foot', 'winch-foot', 'slipway', 'lockfour-overlook',
                'winch-foot', 'fish-dock', 'tenant-shack', 'moorage', 'lock-five',
                'north-landing', 'lock-five', 'keepers-cottage', 'weave-huts',
                'drying-decks', 'weave-huts', 'pilot-cluster', 'weave-north',
                'pilot-cluster', 'quay-deck', 'market-stalls', 'lockhead',
                'keepers-cottage']};
  const TOURFILE = path.join(PUB, `townmap/${TOWNID}.tour.json`);
  const TOUR = fs.existsSync(TOURFILE)
    ? JSON.parse(fs.readFileSync(TOURFILE, 'utf8')).tour
    : TOURS[TOWNID];
  if (!TOUR) console.log(`  (no tour authored for '${TOWNID}' — add townmap/${TOWNID}.tour.json ` +
                         '{"tour": [landmark ids...]}; nothing written)');
  else {
  const plan = [];
  for (let i = 0; i < TOUR.length - 1; i++) {
    const legs = route(TOUR[i], TOUR[i + 1]);
    if (!legs) { console.log(`  (no route ${TOUR[i]} -> ${TOUR[i + 1]})`); continue; }
    plan.push({from: TOUR[i], to: TOUR[i + 1], walk: dense(legs.flatMap((l) => l.pts))});
  }
  const tour = {
    _doc: ['THE GRAND TOUR — generated by `node tools/cine_test.mjs --plan`.',
           'A route over the town map\'s own walk network that enters EVERY cinematic shot,',
           'resampled to 0.6 m so a straight-line steerer cannot cut a corner into the',
           'flights\' bar_ railings (slice harness lesson 6). tools/cine_walk.js fetches',
           'this and walks it in a real browser through the real collision, recording every',
           'camera cut. It is the playthrough the coverage claim is proven by.'],
    generated: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    scene: TOWN, startCam: entry.id, startAt: m2r(LM[TOUR[0]].pos),
    shots: C.cams.map((c) => c.id), legs: plan,
  };
  // world/cine_tour.json is the path tools/cine_walk.js fetches; a second town writes
  // beside it rather than over it, so one town's tour can never become another's.
  const TOURREL = TOWNID === DEFAULT_TOWN ? 'world/cine_tour.json'
                                          : `world/${TOWNID}.cine_tour.json`;
  fs.writeFileSync(path.join(PUB, TOURREL), JSON.stringify(tour) + '\n');
  console.log(`  wrote public/${TOURREL} — ${plan.length} legs, ` +
    `${plan.reduce((a, l) => a + l.walk.length, 0)} steered points, over ${TOUR.length} landmarks`);
  }
}

console.log(`\n${fail ? 'FAIL' : 'PASS'}  ${pass} assertions ok, ${fail} failed, ${warnN} soft warnings`);
process.exit(fail ? 1 : 0);
