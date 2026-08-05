#!/usr/bin/env node
/* findability_test.mjs — THE FINDABILITY GATE. Can a HUMAN see the person the
 * game just told them to talk to?  (no browser, no network, ~1 s)
 *
 *   node tools/findability_test.mjs
 *   node tools/findability_test.mjs --scene emb-cine --verbose
 *
 * WHY THIS EXISTS — the bug it was written from, 2026-08-02.
 * The user could not get past Chapter One's FIRST objective ("greet the villagers
 * (Poppy, …)") because they could not find Poppy. Every gate in the repo was green.
 * dialogue_test had her bust, her post and her arrival clearance; story_test had her
 * flags and her beat; playthrough_test fired `ch1.see.poppy` and set `npc.met.poppy`
 * — because the harness calls SIM.tp() to her coordinate and Npc.talk('poppy') by id.
 * A TEST THAT TELEPORTS TO A COORDINATE AND CALLS A FUNCTION DOES NOT PROVE A HUMAN
 * CAN FIND THE PERSON STANDING THERE.
 * Measured cause: Poppy's post sat 0.9 m from her own festival stall, and from the
 * `square` camera — the ONLY shot whose band owns that ground — the stall's canopy
 * (3.3–3.8 m up) covered her whole body column. play3d's exact-pixel depth occlusion
 * therefore discarded every one of her pixels. She was in the scene, `visible:true`,
 * projecting to a valid on-screen pixel, and INVISIBLE. 2.1% of her body samples
 * survived the depth map; the fix moved her 3.3 m to 100%.
 *
 * WHAT IT MEASURES. For every villager in a cinematic bundle, and for every story
 * beat that plants a proximity trigger on the ground:
 *   §1 SOME SHOT'S BAND OWNS THE POST. The shot bands in scenegraph.json are what
 *      chooses the camera the player is looking through while standing there. A post
 *      no band owns is a person the player meets under an undefined camera.
 *   §2 THE BODY COLUMN IS IN FRAME, with margin — an NPC clipped by the frame edge
 *      is a smear, not a character.
 *   §3 THE BODY COLUMN SURVIVES THE PLATE'S DEPTH MAP. This is the check nothing
 *      else in the repo makes. cine_bake's ray-cast asks "can the camera see this
 *      REGION"; nobody ever asked it about a PERSON, and a person is 0.6 m wide and
 *      stands where the art director put a stall.
 *   §4 THE FIGURE IS BIG ENOUGH TO READ — on-screen height in plate pixels.
 *
 * PROJECTION, MEASURED NOT ASSUMED (2026-08-02). cine.json's `fov` is the VERTICAL
 * field of view and the aspect is depth.width/depth.height. Confirmed against the
 * running page: three.js reported cam.fov 35 / cam.aspect 1.75 for `square`, and the
 * NDC this file computes for Poppy's post (+0.548) matches the runtime's own
 * projection (+0.554) to three thousandths. Reading `fov` as HORIZONTAL puts her at
 * +0.96 — hard against the frame edge — which is a completely different and completely
 * wrong diagnosis. If this file ever disagrees with the page, the page is right.
 *
 * IT IS A SCREEN, NOT A VERDICT, IN ONE DIRECTION ONLY: passing means the pixels are
 * there, not that the figure reads at a glance (lighting, contrast and clutter are
 * nav_eval's and the red-team's business). FAILING means the player cannot see them
 * at all, and that is a verdict.
 */
import fs from 'fs';
import path from 'path';
import { PNG } from 'pngjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i >= 0 ? process.argv[i + 1] : d; };
const has = (k) => process.argv.includes('--' + k);
const VERBOSE = has('verbose');
const ONLY = arg('scene', null);

// Thresholds. VIS_FAIL is deliberately generous: half a body behind a barrel is a
// composition note, not a blocker. Under 35% is "the player walks past them".
const VIS_FAIL = 0.35, VIS_WARN = 0.60;
const EDGE_MARGIN = 0.02;      // NDC — 2% of the frame; a body touching the edge warns
/* PX_WARN — APPARENT SIZE, and VISIBLE IS NOT FINDABLE (recalibrated 2026-08-05).
 * This was 12 px, a bare number with no derivation recorded, and nothing in either
 * town ever tripped it. Then run-20260805-013253 — a 200-step NEW GAME run — spent
 * its last SIXTY steps on "See to them — all of them", hunting two villagers this
 * gate scores 100% unoccluded. The sizes it was working with, from this gate's own
 * --verbose, at 1280x720:
 *
 *     mochi-emb  18 px (2.5% of frame height)   found at step 85, 36 after the one before
 *     pip        19 px      emb.girl  19 px
 *     rowan      28 px      poppy     28 px     poppy NOT found in 60 steps
 *     mara       30 px (4.2%)                   found at step 49
 *
 * The founding lesson of this file was "in frame is not visible". The next turn is
 * VISIBLE IS NOT FINDABLE: a 28-pixel smudge at 47 m survives every depth test ever
 * written and is not a person a player can pick out on a TV.
 *
 * 32 px is the top of the population that run demonstrably could not work with, and
 * the calibration is ONE-SIDED ON PURPOSE — the run never entered `pondlane`, so its
 * 40-47 px bodies are untested and nothing here proves larger is sufficient. This is
 * a WARNING, never a failure: it is a judgment call, and a heuristic that fails a
 * build is a heuristic that gets written around. */
const PX_WARN = 32;            // plate pixels of on-screen height

let pass = 0, fail = 0, warn = 0;
const ok = (c, m, x) => { if (c) { pass++; if (VERBOSE) console.log('  ok   ' + m); }
  else { fail++; console.log('  FAIL ' + m + (x !== undefined ? '  ' + JSON.stringify(x) : '')); } };
const wrn = (m) => { warn++; console.log('  warn ' + m); };
const head = (s) => console.log('\n' + s);

const J = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));

// ---------------------------------------------------------------- geometry ----
// Blender/cine space: x east, y north, z up. Runtime space: x east, y up, z south.
// One negation, in ONE place, so the two never get mixed again.
const toCine = (rx, ry, rz) => [rx, -rz, ry];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a) => { const l = Math.hypot(...a); return [a[0] / l, a[1] / l, a[2] / l]; };

function frame(cam) {
  const P = cam.pos, f = norm(sub(cam.aim, P));
  const r = norm(cross(f, [0, 0, 1])), u = cross(r, f);
  const W = cam.depth.width, H = cam.depth.height;
  return { P, f, r, u, W, H, aspect: W / H, tv: Math.tan(cam.fov * Math.PI / 360) };
}
function project(F, p) {
  const v = sub(p, F.P), z = dot(v, F.f);
  const ndcx = (dot(v, F.r) / z) / (F.tv * F.aspect), ndcy = (dot(v, F.u) / z) / F.tv;
  return { ndcx, ndcy, z, px: (ndcx * 0.5 + 0.5) * F.W, py: (0.5 - ndcy * 0.5) * F.H };
}

const _dep = new Map();
function depthOf(scene, camId, cam) {
  const key = scene + '/' + camId;
  if (!_dep.has(key)) {
    const f = path.join(ROOT, 'public/assets/scenes', scene, 'cameras', camId, 'depth.png');
    if (!fs.existsSync(f)) { _dep.set(key, null); }
    else {
      const png = PNG.sync.read(fs.readFileSync(f));
      const { near, far } = cam.depth, n = png.width * png.height, z = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        const o = i * 4;
        const code = (png.data[o] * 65536 + png.data[o + 1] * 256 + png.data[o + 2]) / 16777215;
        z[i] = near + code * (far - near);
      }
      _dep.set(key, { z, w: png.width, h: png.height });
    }
  }
  return _dep.get(key);
}

/* The body column. A person is not a point: sample the body's OWN box — `h` tall,
 * three columns across — and ask the plate's own depth whether each sample is in
 * front of what was baked. 0.15 m of slack absorbs depth quantisation (the 24-bit
 * code over a ~50 m range is ~3 mm, but the plate is a rasterised surface and a
 * sample can land on a silhouette pixel).
 * THE BOX IS THE SUBJECT'S, NOT A CONSTANT. Sampling a fixed 0.9 m column over a
 * 0.30 m cat measures the air above the cat and calls the cat hidden — Mochi read
 * 30% that way and 100% once the column was his own height. */
function bodyVisibility(scene, camId, cam, rx, rz, groundY, h) {
  const F = frame(cam), D = depthOf(scene, camId, cam);
  const top = Math.max(0.2, h), step = Math.max(0.04, top / 12);
  const halfW = Math.min(0.3, Math.max(0.1, top * 0.28));
  let vis = 0, tot = 0, off = 0, minNdcEdge = 9;
  for (let dh = step; dh <= top + 1e-6; dh += step) {
    for (const dx of [-halfW, 0, halfW]) {
      const p = toCine(rx, groundY + dh, rz);
      p[0] += F.r[0] * dx; p[1] += F.r[1] * dx;
      const q = project(F, p); tot++;
      minNdcEdge = Math.min(minNdcEdge, 1 - Math.abs(q.ndcx), 1 - Math.abs(q.ndcy));
      const iu = Math.round(q.px), iv = Math.round(q.py);
      if (iu < 0 || iu >= F.W || iv < 0 || iv >= F.H) { off++; continue; }
      if (!D) { vis++; continue; }              // no depth map ships => nothing occludes
      if (D.z[iv * D.w + iu] >= q.z - 0.15) vis++;
    }
  }
  const base = project(F, toCine(rx, groundY, rz));
  return { vis: vis / tot, off: off / tot, edge: minNdcEdge, dist: base.z,
           pxH: h / (2 * F.tv * base.z) * F.H, px: [Math.round(base.px), Math.round(base.py)] };
}

// ------------------------------------------------------------------- data ----
const sg = J('public/world/scenegraph.json');
const npcs = J('public/game/npcs.json');
const story = J('public/game/story.json');

function bands(scene) {
  const n = sg.nodes[scene];
  return (n && n.shots) ? n.shots : null;
}
/** Which shot's camera is the player looking through while standing here?
 *  Last match wins — the same rule play3d's own band test uses. */
function ownerShot(scene, x, z) {
  const shots = bands(scene); if (!shots) return null;
  let hit = null;
  for (const s of shots) for (const b of s.boxes)
    if (b[0] <= x && x <= b[2] && b[1] <= z && z <= b[3]) hit = { shot: s.id, y: b[4] };
  return hit;
}
/** The band a post has FALLEN OUT OF, and by how far. A post just outside every box
 *  is not necessarily unreachable — the bands are derived from the walk network and
 *  a villager may stand a step off the path — but it IS the shot the player will be
 *  looking through when they arrive, so the visibility question still has an answer. */
function nearestShot(scene, x, z) {
  const shots = bands(scene); if (!shots) return null;
  let best = null;
  for (const s of shots) for (const b of s.boxes) {
    const dx = Math.max(b[0] - x, 0, x - b[2]), dz = Math.max(b[1] - z, 0, z - b[3]);
    const d = Math.hypot(dx, dz);
    if (!best || d < best.d) best = { shot: s.id, y: b[4], d };
  }
  return best;
}
const _cine = new Map();
function cameras(scene) {
  if (!_cine.has(scene)) {
    const f = path.join(ROOT, 'public/assets/scenes', scene, 'cine.json');
    _cine.set(scene, fs.existsSync(f) ? Object.fromEntries(
      JSON.parse(fs.readFileSync(f, 'utf8')).cameras.map(c => [c.id, c])) : null);
  }
  return _cine.get(scene);
}

/* WHO THE GAME NAMES. The bug this file was written from is not "an NPC is hidden",
 * it is "the game told the player to go and find someone the player cannot see".
 * So a villager the STORY names — a speaker in a story node, or a beat's trigger
 * standing on their post — is a FAILURE when they are invisible; an ambient
 * villager is a WARNING, because a person half behind a crate on a shop street is a
 * composition note and not a blocked playthrough. The distinction is measured from
 * story.json, never from a hand-kept list. */
const named = new Set();
for (const [, node] of Object.entries(story.nodes || {})) {
  const lines = Array.isArray(node) ? node : (Array.isArray(node && node.lines) ? node.lines : []);
  for (const l of lines) if (l && l.speaker) named.add(l.speaker);
}
for (const b of story.beats || []) {
  if (!b.at) continue;
  for (const r of npcs.npcs) {
    const s = Array.isArray(r.scene) ? r.scene : [r.scene];
    if (b.scene && !s.includes(b.scene)) continue;
    if (Math.hypot(r.position[0] - b.at[0], r.position[2] - b.at[2]) <= (b.r || 3) + 0.5) named.add(r.id);
  }
}

const scenes = [...new Set(npcs.npcs.flatMap(r => Array.isArray(r.scene) ? r.scene : [r.scene]))]
  .filter(s => s && bands(s) && cameras(s)).filter(s => !ONLY || s === ONLY).sort();

console.log('findability_test — can a human SEE the person the game names?');
console.log('  scenes: ' + scenes.join(', '));

// ------------------------------------------------------- §1-4 the villagers ----
for (const scene of scenes) {
  head('§ ' + scene + ' — every villager, from the shot whose band owns their post');
  const cams = cameras(scene);
  for (const rec of npcs.npcs) {
    const s = Array.isArray(rec.scene) ? rec.scene : [rec.scene];
    if (!s.includes(scene)) continue;
    const [x, , z] = rec.position;
    let own = ownerShot(scene, x, z);
    // §1 — a WARNING for a villager (the bands come off the walk network and a post
    // may legitimately sit a step off the path), a FAILURE for a beat in §5, where
    // the trigger circle IS the ground the player is sent to stand on.
    if (!own) {
      const near = nearestShot(scene, x, z);
      if (!near) { ok(false, `${rec.id}: any shot band exists in ${scene}`); continue; }
      wrn(`${rec.id}: no shot band owns the post — ${near.d.toFixed(2)} m outside '${near.shot}'`
        + '; judged from that shot below');
      own = near;
    }
    const cam = cams[own.shot];
    if (!cam) { ok(false, `${rec.id}: shot '${own.shot}' exists in cine.json`); continue; }
    const h = (rec.body && rec.body.h) || rec.height || (npcs.defaults || {}).adultHeight || 1.1;
    const m = bodyVisibility(scene, own.shot, cam, x, z, own.y, h);
    const tag = `${rec.id} @ ${own.shot}` + (named.has(rec.id) ? ' [named by the story]' : '');
    const hard = named.has(rec.id);
    // §2
    ok(m.off < 0.25, `${tag}: the body is in frame`, m.off ? { offFrame: +(m.off * 100).toFixed(0) + '%' } : undefined);
    if (m.off < 0.25 && m.edge < EDGE_MARGIN) wrn(`${tag}: body touches the frame edge (${m.edge.toFixed(3)} NDC)`);
    // §3 — the check nothing else makes
    const seen = m.vis >= VIS_FAIL;
    if (!seen && !hard)
      wrn(`${tag}: only ${(m.vis * 100).toFixed(0)}% of the body clears the plate at px ${m.px}`
        + ' — ambient villager, so a note and not a blocker');
    else
      ok(seen, `${tag}: survives the plate's depth map (${(m.vis * 100).toFixed(0)}% of the body)`,
        seen ? undefined : { visible: +(m.vis * 100).toFixed(1) + '%', px: m.px, dist: +m.dist.toFixed(1),
          hint: 'the plate has geometry NEARER than this body at these pixels — the player cannot see them' });
    if (seen && m.vis < VIS_WARN) wrn(`${tag}: only ${(m.vis * 100).toFixed(0)}% of the body clears the plate`);
    // §4
    if (m.pxH < PX_WARN) wrn(`${tag}: ${m.pxH.toFixed(0)} px tall on the plate at ${m.dist.toFixed(0)} m — small to read`);
    if (VERBOSE) console.log(`       ${tag}  vis=${(m.vis * 100).toFixed(0)}%  px=${m.px}  ${m.pxH.toFixed(0)}px tall  ${m.dist.toFixed(1)}m`);
  }
}

// ------------------------------------------------ §5 the beats' own ground ----
// A beat with an `at` is a circle drawn on the floor the player must walk into. If
// the beat also names a `cam`, the player will be looking through THAT camera when
// they do — so the target has to be visible in it, or the objective points nowhere.
head('§5 every story beat that plants a trigger on the ground');
for (const b of story.beats || []) {
  if (!b.at || !b.scene) continue;
  const scene = b.scene;
  if (!bands(scene) || !cameras(scene)) continue;
  if (ONLY && scene !== ONLY) continue;
  const [x, , z] = b.at;
  const own = ownerShot(scene, x, z);
  ok(!!own, `${b.id}: a shot band owns the trigger ground at [${x}, ${z}]`);
  if (!own) continue;
  if (b.cam && b.cam !== own.shot)
    wrn(`${b.id}: declares cam '${b.cam}' but the band at its own trigger is '${own.shot}'`);
  const cams = cameras(scene), cam = cams[b.cam || own.shot];
  if (!cam) { ok(false, `${b.id}: cam '${b.cam || own.shot}' is baked in this bundle`); continue; }
  const m = bodyVisibility(scene, b.cam || own.shot, cam, x, z, own.y, 1.6);
  ok(m.vis >= VIS_FAIL, `${b.id}: the ground it names is visible from ${b.cam || own.shot} (${(m.vis * 100).toFixed(0)}%)`,
    m.vis >= VIS_FAIL ? undefined : { visible: +(m.vis * 100).toFixed(1) + '%', px: m.px,
      hint: 'the player is sent to a place the camera cannot show them' });
}

console.log(`\n${pass} passed, ${fail} failed, ${warn} warnings`);
process.exit(fail ? 1 : 0);
