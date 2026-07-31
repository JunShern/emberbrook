// scene_redteam.mjs — THE SCENE CRITIQUE JUDGE (automated red-teaming of shipped plates).
//
//   node tools/scene_redteam.mjs --calibrate          # THE GATE. Run this first, always.
//   node tools/scene_redteam.mjs --town dellhollow    # the sweep, both modes, all shots
//   node tools/scene_redteam.mjs --town emberbrook    # (blockout mode arms itself)
//   node tools/scene_redteam.mjs --shots gate,waterfront --mode naive
//   node tools/scene_redteam.mjs --judge stub --dry   # harness self-check, no API
//   node tools/scene_redteam.mjs --replay <newStamp>,<oldStamp> --stamp <out>
//                                                     # ONE report from several runs: each
//                                                     # shot resolves from the first listed
//                                                     # run that holds it, and says so.
//
// Then open the report:
//   python3 -m http.server 8009 --directory docs/qa
//   http://localhost:8009/redteam/run-<stamp>/index.html      (or open the file directly —
//   the run directory is self-contained: every image it shows is copied into it)
//
// ---------------------------------------------------------------------------
// WHY THIS EXISTS. The user has been red-teaming the town BY HAND: play, screenshot,
// circle the ugly thing in red, write "unnecessary occlusion, replace with rope fence".
// Five of those annotated frames are committed under docs/qa/refs/. Every gate we own
// passed while those complaints were true — because the complaints are not geometric,
// not navigational in nav_eval's sense, and not photometric. They are "this looks wrong
// / this is confusing / I cannot see the stair". This tool hires the eye that makes them.
//
// TWO MODES, AND THE SECOND ONE EXISTS BECAUSE THE FIRST HAS A HOLE.
//
//   NAIVE (context-free critique). One frame, no map, no town name, no history — the
//   same innocence nav_eval's judge is given, for the same reason: everything in the
//   answer then came out of the PICTURE. It is the only mode that can catch CONFUSION,
//   because confusion is a property of a first look.
//
//   CHECKLIST (map-informed audit). A context-free judge CANNOT REPORT THE ABSENCE OF
//   WHAT IT NEVER KNEW EXISTED. An occluded staircase is not a complaint to someone who
//   does not know a staircase belongs there — it is just a wall, and a wall is not a
//   defect. So the second mode hands the judge THE SHOT'S OWN CONTRACT, derived
//   mechanically (never typed): cameras.json owns.landmarks + owns.edges, the map's
//   mapVisible landmarks that project into the frame, the shot's door/portal pads, and
//   its frameExits from routes.json. Per item it must answer FINDABLE / OCCLUDED /
//   VISIBLE-BUT-ILLEGIBLE / ABSENT.
//
//   **VISIBLE-BUT-ILLEGIBLE IS THE WHOLE POINT.** Raw pixel visibility is already
//   measured deterministically and better — the bake's own ray-cast (cine.json
//   visibleFrac), cine_visprobe, and the census this file runs alongside every checklist
//   answer (project the landmark, read the shot's own depth plate, compare). What no
//   deterministic instrument can answer is whether an object that IS on screen and IS
//   unoccluded READS as what it is. That is the LLM's unique layer and it is the one the
//   scorecard should be judged on.
//
//   The judge is NEVER told where an item is on screen. It reports where it found it;
//   the census says where it actually is. A confident location that disagrees with the
//   census is itself a legibility finding.
//
// STAGE 2 — VERIFY. Every finding from either mode must survive one of:
//   (i)  an ADVERSARIAL second call on the same plate, asked to REFUTE it ("is this
//        actually a problem, or normal for this style / a misreading of the picture?").
//        Batched one call per shot so a whole town stays inside a few dozen calls.
//   (ii) an INSTRUMENT that already answers the question deterministically: an OCCLUDED
//        checklist verdict the ray census agrees with survives on the census, not on a
//        second opinion. Geometry findings carry a `geometry_audit --region` command
//        unprojected from their own bbox, so the next pass has an instrument, not a vibe.
// SURVIVORS ONLY are reported. The refuted list is written to the run dir for audit,
// because a metric that hides what it threw away cannot be checked.
//
// ---------------------------------------------------------------------------
// WHAT A PLATE JUDGE STRUCTURALLY CANNOT SEE  (seam-canon §10.3, amended 2026-08-01)
//
// This tool looks at PIXELS. The canon's most expensive lesson is that pixels are the
// fourth of at least five different questions, and not the one the player's feet ask:
//
//     "in frame" != "visible" != "unobstructed ray" != CATCHES A FOOT
//
// The loop-stairs defect was 72% visible, correctly framed, unoccluded and handsome, and
// it was UNWALKABLE: walkGround keeps the highest surface in the step window, the market
// flight's top tread covered the head of the quay flight, and the quay flight caught a
// foot in 0 of 72 entries. NO CRITIQUE OF THAT PLATE COULD EVER HAVE FOUND IT. It was
// hidden for a day by a written interpretation ("walker pessimism") and found by an
// instrument (tools/ls_nav_probe.mjs). Neither mode here can see:
//
//   * whether a walk surface catches a foot        -> ls_nav_probe.mjs, seam_walk.mjs
//   * whether a solid blocks the body              -> WALKLOCK / boxSolid, seam_test.mjs
//   * whether a naive reading of a frame ESCAPES   -> nav_eval.mjs (it walks the answer)
//   * whether a seam fires where it should         -> seam_test.mjs, transition_test.mjs
//   * true occlusion in metres over a whole object -> the bake ray-cast, the ONLY
//                                                     visibility oracle / cine_visprobe.py
//   * anything outside the shipped fixed frames    -> the user plays with a free orbit
//                                                     camera; ALL FIVE reference frames
//                                                     were taken from angles no shipped
//                                                     plate holds (measured: best
//                                                     normalised cross-correlation of any
//                                                     plate against any ref = 0.35).
//
// A finding from this tool is a PERCEPTION, and a perception is not a measurement. It
// earns a fix when an instrument seconds it. That is what stage 2 is for, and it is why
// geometry hints are emitted as geometry_audit commands rather than as verdicts.
//
// THE JUDGE IS PINNED — gemini-3.6-flash, the same model and the same key as nav_eval:
// one channel, one bill, and two runs that stay comparable. Critique quality may well
// justify a stronger pinned model later (a critic is a harder job than "point at the
// road"); calibrate on flash FIRST so the upgrade has a baseline to beat.
import fs from 'fs';
import path from 'path';
import {PNG} from 'pngjs';
import {loadCine, camBasis, project, charPx, m2r, r2m, PUB, ROOT, rd} from './cine_regions.mjs';

// ------------------------------------------------------------------ args ----
const ARGS = process.argv.slice(2);
const flag = (n) => ARGS.includes(n);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const CALIBRATE = flag('--calibrate');
const TOWN = opt('--town', 'dellhollow');
const MODEL = opt('--model', 'gemini-3.6-flash');
const JUDGE_NAME = opt('--judge', 'gemini');
const MODE = opt('--mode', 'both');                    // naive | checklist | both
const ONLY = (opt('--shots', '') || '').split(',').filter(Boolean);
const CONC = +opt('--conc', 3);
const TEMP = +opt('--temp', 0.4);
const DRY = flag('--dry');
const WITH_CHAR = flag('--with-char');
const MAXITEMS = +opt('--max-items', 12);
const N = +opt('--n', 3);                              // independent looks per plate, naive mode
const TAG = opt('--tag', null);
const REPLAY = opt('--replay', null);        // re-derive a finished run from its stored replies

// Emberbrook ships as a MASSING BLOCKOUT and is judged as one. Told to the judge, not
// filtered out afterwards: a judge that spends its findings on "the materials are grey
// placeholder" has learned nothing about the layout, which is the thing under test.
const BLOCKOUT_DEFAULT = {dellhollow: false, emberbrook: true};
const BLOCKOUT_FLAG = flag('--blockout') ? true : flag('--no-blockout') ? false : null;

const STAMP = opt('--stamp', new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '')
  .replace('T', '-') + (TAG ? '-' + TAG : '') + (CALIBRATE ? '-calib' : ''));
const RTDIR = path.join(ROOT, 'docs/qa/redteam');
const OUTDIR = path.join(RTDIR, 'run-' + STAMP);
// --replay TAKES A LIST. `--replay fresh,old` resolves each shot's stored replies from the
// FIRST listed run that holds them, which is what makes ONE report out of a town that was
// only partly re-swept: the plates that had to be judged again come from today's run, the
// unchanged ones replay from the older one at no API cost, and every shot records WHICH —
// because "12 of these 16 critiques are a day old" is a fact about the result, not a
// footnote. Single-stamp --replay behaves exactly as before.
const REPLAY_LIST = (REPLAY || '').split(',').map((s) => s.trim()).filter(Boolean);
const replaySrc = (id) => REPLAY_LIST.find((st) =>
  fs.existsSync(path.join(RTDIR, 'run-' + st, 'raw', id + '.json'))) || null;

// ------------------------------------------------------- CALIBRATION TRUTH ---
// The user's five complaints, as filed, with the shots that hold the object complained
// about. PRE-REGISTERED: the matcher is mechanical and was written before any judge
// output was read, so "found it" cannot be decided after the fact by whoever writes the
// report.
//
// TWO NUMBERS, BOTH REPORTED, because there is a real ambiguity and hiding it would be
// the failure mode this file exists to avoid:
//   STRICT  — found only if raised on `primary`, the one plate whose frame most nearly
//             holds what the user circled.
//   LENIENT — found if raised on ANY shot in `shots`. Defensible because the user
//             complained about an OBJECT IN THE TOWN and the sweep sees the town through
//             sixteen windows; but it is the generous reading and is labelled as one.
//
// NOT REPRODUCIBLE, STATED UP FRONT: all five references were screenshot from a FREE
// ORBIT CAMERA, not from a shipped plate (measured — see the header). The judge is
// therefore never shown the user's pixels; it is shown the shipped frame that holds the
// same object. The waterfront character walking ON WATER cannot appear at all — no plate
// composites a character unless --with-char is on, and none stands there. The GEOMETRY
// JUMBLE is the target of that row, as the handover says.
const CALIBRATION = {
  town: 'dellhollow',
  complaints: [
    {id: 'canopy-wall', ref: 'user_entrance_ref.png',
     title: 'Canopy wall across the entrance',
     said: 'A wall of tree canopy stands between the camera and the road into town — the only way IN is behind foliage.',
     primary: 'gate', shots: ['gate', 'shelf-west'],
     tracked: 'DAYLOG 15:10 legibility audit — "WORST BY IMPACT: gate + shelf-west — the rim canopy sits between camera and road, the only way INTO Dellhollow measures 0% visible".',
     keys: [['canopy', 'foliage', 'tree', 'trees', 'leaf', 'leaves', 'shrub', 'bush', 'vegetation',
             'hedge', 'branch', 'plants', 'brush'],
            ['block', 'hide', 'hides', 'hidden', 'hiding', 'obscur', 'occlud', 'conceal', 'wall of',
             'screen', 'cover', 'in front of', 'behind', 'interrupt', 'break']]},
    {id: 'gate-stair', ref: 'user_gatestair_ref.png',
     title: 'The gate stair is occluded / hard to navigate',
     said: '"Staircase very occluded, hard to navigate."',
     primary: 'gate', shots: ['gate', 'shelf-west', 'deep-stairs'],
     tracked: 'dellhollow.cameras.json gate._framing_note — stair visibility measured 14.6% -> 6.1% post-bake at yaw 125; reverted, "the gate stair is the art pass\'s row now".',
     keys: [['stair', 'stairs', 'staircase', 'steps', 'stairway', 'flight', 'descent'],
            ['occlud', 'hidden', 'hide', 'obscur', 'block', 'behind', 'cut off', 'unclear', 'hard to',
             'cannot', "can't", 'not visible', 'disappear', 'partial', 'illegible', 'ambiguous', 'unreadable']]},
    {id: 'stray-cliff', ref: 'user_gatestair_ref.png',
     title: 'Stray / weird cliff geometry',
     said: '"Stray / weird cliff geometry."',
     primary: 'gate', shots: ['gate', 'shelf-west', 'crossing', 'waterfront'],
     tracked: 'docs/plans/cliff-completion.md + tools/t2_cliff_{east,south}.py; geometry_audit counts strays every pass (last: 2 offenders / 0 strays in the loop-stairs region).',
     keys: [['cliff', 'rock', 'rocks', 'rockface', 'rock face', 'terrain', 'canyon', 'gorge', 'cliffside',
             'stone', 'ground', 'earth', 'mesa', 'butte'],
            ['stray', 'weird', 'strange', 'incomplete', 'unfinished', 'flat', 'floating', 'stretch',
             'sliver', 'shard', 'odd', 'blocky', 'untextured', 'abrupt', 'cut off', 'clip', 'intersect',
             'ugly', 'low detail', 'smear', 'artifact', 'unnatural', 'featureless', 'blank']]},
    {id: 'plank-screens', ref: 'user_ropefence_ref.png',
     title: 'Solid plank screens where a rope fence belongs',
     said: '"Unnecessary occlusion, replace with rope fence."',
     primary: 'quay-west', shots: ['quay-west', 'shelf-east', 'waterfront', 'lockfive', 'weave', 'crossing'],
     tracked: 'tools/master_rail_trim.py already trims bar_ rails off flat deck; this is the complementary ART call (solid panel -> rope) and is NOT tracked anywhere.',
     keys: [['fence', 'railing', 'rail', 'panel', 'panels', 'screen', 'screens', 'partition', 'board',
             'boards', 'plank', 'planks', 'barrier', 'parapet', 'balustrade', 'wall', 'divider'],
            ['block', 'occlud', 'hide', 'hides', 'hidden', 'obscur', 'view', 'unnecessary', 'solid',
             'opaque', 'conceal', 'cover', 'in front of']]},
    {id: 'waterfront-jumble', ref: 'user_waterfront_ref.png',
     title: 'Waterfront: confusing / incomplete geometry, walking on water',
     said: '"Extremely confusing / incomplete geometry, walking on water. Simplify and tidy up please."',
     primary: 'waterfront', shots: ['waterfront', 'lockfive', 'fishdock', 'boatyard', 'crossing', 'north-landing'],
     tracked: 'DAYLOG legibility audit bucket 4 (cottage-steps floating plank slabs) is the same CLASS; the waterfront deck cluster itself is not tracked.',
     keys: [['deck', 'decks', 'platform', 'platforms', 'walkway', 'walkways', 'pier', 'jetty', 'dock',
             'boardwalk', 'piling', 'pilings', 'stilts', 'water', 'structure', 'structures', 'geometry',
             'scaffold', 'timber'],
            ['confus', 'cluttered', 'clutter', 'jumble', 'busy', 'incomplete', 'unclear', 'hard to read',
             'hard to tell', 'float', 'disconnect', 'ambiguous', 'messy', 'tangle', 'chaotic', 'overlap',
             'which', 'unfinished', 'no clear', 'not clear', 'maze', 'muddle']]},
  ],
  // the shots the gate must run — the union of every complaint's `shots` and nothing
  // else, so the gate costs ~9 shots, not 16, and never sees Emberbrook.
  get shots() { return [...new Set(this.complaints.flatMap((c) => c.shots))]; },
};

// ------------------------------------------------------------ WHAT'S KNOWN ---
// Triage bucket 1. Kept SHORT, and every line carries its source — the documentation bar
// says an interpretation may be recorded only alongside the instrument that proved it,
// and a "known issues" list is nothing but interpretation. Anything unmatched is
// reported as NEW and left for a human to place.
const TRACKED = [
  {id: 'canopy-over-road', where: 'DAYLOG 15:10 legibility audit (gate + shelf-west, road 0% visible)',
   terms: [['canopy', 'foliage', 'tree', 'shrub', 'leaves', 'vegetation', 'bush'],
           ['block', 'occlud', 'hide', 'hidden', 'obscur', 'cover', 'in front of']]},
  {id: 'gate-stair-occluded', where: 'dellhollow.cameras.json gate._framing_note (stair 6.1% post-bake)',
   terms: [['stair', 'steps', 'staircase'], ['occlud', 'hidden', 'obscur', 'block', 'behind']]},
  {id: 'cottage-steps-slabs', where: 'DAYLOG legibility audit bucket 4 — disconnected floating plank slabs',
   terms: [['step', 'stair', 'slab', 'plank'], ['float', 'disconnect', 'gap', 'no stair']]},
  {id: 'unprotected-falloff', where: 'DAYLOG legibility audit — 91 unprotected fall-off places measured town-wide',
   terms: [['edge', 'drop', 'fall', 'ledge'], ['unprotect', 'no rail', 'no fence', 'no barrier', 'fall off', 'fall into']]},
  {id: 'exit-out-of-frame', where: 'DAYLOG 15:10 SYSTEMIC — 5 exits sit outside their own frame',
   terms: [['exit', 'way out', 'seam', 'way on'], ['off frame', 'out of frame', 'not visible', 'cannot see', 'absent']]},
  // TOWN-SCOPED, and it had to be: unscoped, this rule swallowed Dellhollow's
  // "untextured greybox staircase" and "bright magenta polygon" findings into the
  // already-known bucket, which is the worst possible triage error — the tool would have
  // hidden its own best result behind a label meaning "nothing to do here".
  {id: 'emb-blockout-materials', town: 'emberbrook',
   where: 'Emberbrook ships as a massing blockout; the dressing pass owns materials',
   terms: [['material', 'texture', 'untextured', 'grey', 'gray', 'flat shad', 'placeholder', 'low poly',
            'low-poly', 'faceted', 'detail', 'simplistic', 'unfinished look'], []]},
];

// ------------------------------------------------------------------ data ----
const C = loadCine(`townmap/${TOWN}.map.json`, `townmap/${TOWN}.cameras.json`);
const MAP = C.map;
const SCENE = C.camFile.sceneKey;
const SCENE_DIR = path.join(PUB, 'assets/scenes', SCENE);
// --plates points the whole tool at a DIFFERENT bake of the same cameras, exactly as
// nav_eval's does, and it is not a convenience. The art pass re-baked `gate` three
// minutes after the first run read it, so replaying that run against the live scene
// directory would have annotated findings onto a picture they were never made about — and
// worse, would have decoded the OLD depth plate with the NEW bake's near/far. A critique
// names its bake, plates AND cine.json together, or it is worthless a day later.
const PLATES = opt('--plates', SCENE_DIR);
const CINE_PATH = opt('--cine', fs.existsSync(path.join(PLATES, 'cine.json'))
  ? path.join(PLATES, 'cine.json') : path.join(SCENE_DIR, 'cine.json'));
const CINE = JSON.parse(fs.readFileSync(CINE_PATH, 'utf8'));
const CAMBY = Object.fromEntries(CINE.cameras.map((c) => [c.id, c]));
const AUTH = Object.fromEntries(C.camFile.cameras.map((c) => [c.id, c]));
const LM = Object.fromEntries(MAP.landmarks.map((l) => [l.id, l]));
let ROUTES = {shots: {}, frame: [1344, 768]};
try { ROUTES = rd(`townmap/${TOWN}.routes.json`); } catch { /* a town may have none yet */ }
const FRAME = ROUTES.frame || [1344, 768];
const ASPECT = C.D.aspect, CHARH = C.D.charH;
const IS_BLOCKOUT = BLOCKOUT_FLAG === null ? !!BLOCKOUT_DEFAULT[TOWN] : BLOCKOUT_FLAG;

// ------------------------------------------------------- camera + geometry ---
const camOf = (id) => { const c = CAMBY[id];
  return c && {id, pos: c.pos, aim: c.aim, fov: c.fov, depth: c.depth, art: c.art}; };
function plateFiles(id) {
  const c = CAMBY[id];
  const bg = path.join(PLATES, c && c.art ? c.art.bg : `cameras/${id}/bg.png`);
  const dp = path.join(PLATES, c && c.art ? c.art.depth : `cameras/${id}/depth.png`);
  return {bg, depth: dp, ok: fs.existsSync(bg) && fs.existsSync(dp)};
}
const _png = new Map();
const readPng = (p) => { if (!_png.has(p)) _png.set(p, PNG.sync.read(fs.readFileSync(p))); return _png.get(p); };
// map point -> normalised image coords. The projection lives in cine_regions and this
// file never owns a second copy of it.
function toImg(cam, mp) {
  const s = project(cam.pos, cam.aim, cam.fov, ASPECT, mp);
  if (s.behind) return {behind: true};
  const u = s.sx * 0.5 + 0.5, v = 0.5 - s.sy * 0.5;
  return {behind: false, u, v, z: s.z, on: u >= 0 && u <= 1 && v >= 0 && v <= 1,
          charPx: charPx(cam.fov, s.z, CHARH, FRAME[1])};
}
function rayOf(cam, u, v) {
  const b = camBasis(cam.pos, cam.aim);
  const ty = Math.tan(cam.fov * Math.PI / 180 / 2), tx = ty * ASPECT;
  const sx = u * 2 - 1, sy = 1 - v * 2;
  return [b.f[0] + b.r[0] * sx * tx + b.u[0] * sy * ty,
          b.f[1] + b.r[1] * sx * tx + b.u[1] * sy * ty,
          b.f[2] + b.r[2] * sx * tx + b.u[2] * sy * ty];
}
// view-space z at a normalised image coord, decoded exactly as play3d.html's shader does.
function depthAt(cam, u, v) {
  const img = readPng(plateFiles(cam.id).depth);
  const x = Math.min(img.width - 1, Math.max(0, Math.round(u * img.width)));
  const y = Math.min(img.height - 1, Math.max(0, Math.round(v * img.height)));
  const i = (y * img.width + x) * 4;
  const raw = (img.data[i] * 65536 + img.data[i + 1] * 256 + img.data[i + 2]) / 16777215;
  const {near, far} = cam.depth;
  return {z: near + (far - near) * raw, raw, sky: raw > 0.999};
}
// THE CENSUS — the deterministic half of the checklist mode: where is this thing on
// screen, how big is it, and is the plate drawing something NEARER at that pixel.
// WHAT IT IS NOT: a visibility fraction. That is the bake's ray-cast (cine.json
// visibleFrac), the only visibility oracle. This is a POINT PROBE at the landmark's own
// origin and it is reported as one — a wide building whose origin sits behind a post
// reads "occluded" here and is 90% visible in truth. It exists to cross-examine the
// judge, not to replace the oracle.
function census(cam, mp) {
  const s = toImg(cam, mp);
  if (s.behind) return {state: 'behind-camera', on: false};
  const out = {u: +s.u.toFixed(4), v: +s.v.toFixed(4), z: +s.z.toFixed(2),
               charPx: Math.round(s.charPx), on: s.on};
  if (!s.on) { out.state = 'off-frame'; return out; }
  const d = depthAt(cam, s.u, s.v);
  out.plateZ = +d.z.toFixed(2);
  out.state = d.sky ? 'sky-at-pixel' : d.z < s.z - 0.6 ? 'occluded' : 'clear';
  out.behindBy = +(s.z - d.z).toFixed(2);
  return out;
}
// a judged bbox -> a world region, so a geometry finding ships with a command.
function bboxWorld(cam, bb) {
  if (!Array.isArray(bb) || bb.length !== 4) return null;
  const cx = (bb[0] + bb[2]) / 2, cy = (bb[1] + bb[3]) / 2;
  const pts = [[bb[0], bb[1]], [bb[2], bb[1]], [bb[0], bb[3]], [bb[2], bb[3]], [cx, cy]];
  const xs = [], ys = [];
  for (const [u, v] of pts) {
    const uu = Math.max(0, Math.min(1, u)), vv = Math.max(0, Math.min(1, v));
    const {z, sky} = depthAt(cam, uu, vv);
    if (sky) continue;
    const dir = rayOf(cam, uu, vv);
    xs.push(cam.pos[0] + dir[0] * z); ys.push(cam.pos[1] + dir[1] * z);
  }
  if (!xs.length) return null;
  const pad = 1.5;
  const r = [Math.min(...xs) - pad, Math.max(...xs) + pad, Math.min(...ys) - pad, Math.max(...ys) + pad]
    .map((n) => +n.toFixed(1));
  return {region: r.join(','),
          cmd: `Blender -b tools/blends/${TOWN}-master.blend -P tools/geometry_audit.py -- --region ${r.join(',')}`};
}

// ------------------------------------------------------- THE CHECKLIST ITEMS -
// DERIVED, NEVER TYPED. Four sources in order of authority:
//   1. cameras.json owns.landmarks  — the shot's contract: it exists to show these
//   2. cameras.json owns.edges      — the paths it is responsible for
//   3. map mapVisible landmarks that actually project into this frame — what a player
//      can see from here whether or not this camera claims it
//   4. routes.json exits            — frameExits (seams onward) and door / portal pads
// Capped at --max-items by apparent size, largest first: a 40-item checklist is a worse
// instrument than a 12-item one, and Emberbrook has 37 mapVisible landmarks.
const kindOf = (l) => (l.kind && l.kind !== 'undefined' ? l.kind : l.class || 'landmark').replace(/-/g, ' ');
function checklistFor(id, cam) {
  const a = AUTH[id] || {}, owns = a.owns || {}, S = (ROUTES.shots || {})[id] || {};
  const items = [], seen = new Set();
  const push = (it) => { if (!seen.has(it.id)) { seen.add(it.id); items.push(it); } };
  for (const lid of owns.landmarks || []) {
    const l = LM[lid]; if (!l) continue;
    push({id: lid, src: 'owns.landmark', what: `${l.name || lid} — a ${kindOf(l)}` +
          (l.note ? ` (${l.note})` : ''), census: census(cam, l.pos), must: true});
  }
  // AN EDGE'S OWN WORDS. The map says what each path IS — `type` and the author's note
  // ("S-bend flight hugging the cliff side", "cargo only — NOT walkable; pure set
  // dressing") — and the first calibration run proved the difference matters: described
  // as a generic "walkable path", the flight down from the gate is a thing the judge has
  // no reason to look for, and the gate-stair complaint cannot be reproduced. This is
  // read from the map, never typed here.
  const EDGE = Object.fromEntries((MAP.edges || []).map((e) => [`${e.from}__${e.to}`, e]));
  for (const eid of owns.edges || []) {
    const key = eid.replace(/@.*/, ''), [from, to] = key.split('__');
    const A = LM[from], B = LM[to], E = EDGE[key] || {};
    if (!A || !B) continue;
    const mid = [(A.pos[0] + B.pos[0]) / 2, (A.pos[1] + B.pos[1]) / 2, (A.pos[2] + B.pos[2]) / 2];
    push({id: 'path:' + eid, src: 'owns.edge', must: true, census: census(cam, mid),
          what: `the route between ${A.name || from} and ${B.name || to} — a ${E.type || 'path'}` +
                (E.note ? ` (${String(E.note).split('|')[0].trim()})` : '')});
  }
  const exitSeen = new Set();
  for (const e of S.exits || []) {
    const k = (e.toKind === 'shot' ? 'to:' : 'door:') + e.to + (e.label || '');
    if (exitSeen.has(k)) continue;                     // one way on per destination
    exitSeen.add(k);
    if (e.toKind === 'shot')
      push({id: 'exit:' + e.id, src: 'frameExit', must: true, census: census(cam, r2m(e.at)),
            what: `the way out of this area on foot towards ${e.to} — a path that carries on out of the frame`});
    else
      push({id: 'door:' + e.id, src: 'doorPad', must: true, census: census(cam, r2m(e.at)),
            what: `a door / entrance you can go through${e.label ? ` ("${e.label}")` : ''}`});
  }
  const extra = [];
  for (const l of MAP.landmarks) {
    if (!l.mapVisible || seen.has(l.id)) continue;
    const cs = census(cam, l.pos);
    if (!cs.on || cs.state === 'behind-camera') continue;
    extra.push({id: l.id, src: 'mapVisible', must: false, census: cs,
                what: `${l.name || l.id} — a ${kindOf(l)}` + (l.note ? ` (${l.note})` : '')});
  }
  extra.sort((x, y) => (y.census.charPx || 0) - (x.census.charPx || 0));
  for (const e of extra.slice(0, Math.max(0, MAXITEMS - items.length))) push(e);
  return items;
}

// --------------------------------------------------------------- THE INPUT ---
// The plate at the frame every other tool in the pipeline reasons in (1344x768), by the
// same box filter nav_eval uses. --with-char additionally stands the character at the
// shot's primary entry with play3d's ghost pass v2 (half strength where the plate is
// nearer): the rubric asks about SCALE ERRORS and a frame with no figure in it has no
// scale. Default OFF — a figure invites the judge to critique the figure.
function sprite() {
  const p = readPng(path.join(PUB, 'assets/characters/vesper/pose.png'));
  const A = new Uint8Array(p.width * p.height);
  for (let i = 0; i < p.width * p.height; i++) {
    const r = p.data[i * 4], g = p.data[i * 4 + 1], b = p.data[i * 4 + 2];
    A[i] = (r - g > 90 && b - g > 60) ? 0 : (r - g > 50 && b - g > 32) ? 110 : 255;
  }
  let x0 = p.width, x1 = -1, y0 = p.height, y1 = -1;
  for (let y = 0; y < p.height; y++) for (let x = 0; x < p.width; x++)
    if (A[y * p.width + x] > 160) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  const w = x1 - x0 + 1, h = y1 - y0 + 1, rgba = new Uint8Array(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const s = ((y + y0) * p.width + (x + x0)), d = (y * w + x) * 4;
    rgba[d] = p.data[s * 4]; rgba[d + 1] = p.data[s * 4 + 1]; rgba[d + 2] = p.data[s * 4 + 2]; rgba[d + 3] = A[s];
  }
  return {w, h, data: rgba};
}
let _spr = null;
function buildInput(cam, outPath, standPt) {
  const bgp = readPng(plateFiles(cam.id).bg);
  const W = FRAME[0], H = FRAME[1], sc = bgp.width / W;
  const out = new PNG({width: W, height: H});
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    let r = 0, g = 0, b = 0, n = 0;
    for (let dy = 0; dy < sc; dy++) for (let dx = 0; dx < sc; dx++) {
      const sx = Math.min(bgp.width - 1, Math.floor(x * sc + dx));
      const sy = Math.min(bgp.height - 1, Math.floor(y * sc + dy));
      const i = (sy * bgp.width + sx) * 4;
      r += bgp.data[i]; g += bgp.data[i + 1]; b += bgp.data[i + 2]; n++;
    }
    const o = (y * W + x) * 4;
    out.data[o] = r / n; out.data[o + 1] = g / n; out.data[o + 2] = b / n; out.data[o + 3] = 255;
  }
  let charInfo = null;
  if (standPt) {
    const S = (_spr ||= sprite());
    const foot = toImg(cam, standPt), head = toImg(cam, [standPt[0], standPt[1], standPt[2] + CHARH]);
    if (!foot.behind) {
      const fx = foot.u * W, fy = foot.v * H, hpx = Math.max(8, Math.abs(head.v * H - fy));
      const scale = hpx / S.h, wpx = Math.max(4, Math.round(S.w * scale)), hh = Math.max(6, Math.round(hpx));
      const left = Math.round(fx - wpx / 2), top = Math.round(fy - hh), cz = foot.z;
      const dimg = readPng(plateFiles(cam.id).depth), {near, far} = cam.depth;
      let drawn = 0, ghosted = 0;
      for (let y = 0; y < hh; y++) { const sy = Math.min(S.h - 1, Math.floor(y / scale)); const py = top + y;
        if (py < 0 || py >= H) continue;
        for (let x = 0; x < wpx; x++) {
          const sx = Math.min(S.w - 1, Math.floor(x / scale)); const px = left + x;
          if (px < 0 || px >= W) continue;
          const a = S.data[(sy * S.w + sx) * 4 + 3] / 255; if (a <= 0.02) continue;
          const dx2 = Math.min(dimg.width - 1, Math.round(px / W * dimg.width));
          const dy2 = Math.min(dimg.height - 1, Math.round(py / H * dimg.height));
          const di = (dy2 * dimg.width + dx2) * 4;
          const dz = near + (far - near) * (dimg.data[di] * 65536 + dimg.data[di + 1] * 256 + dimg.data[di + 2]) / 16777215;
          const hidden = dz < cz - 0.35, k = a * (hidden ? 0.5 : 1);
          drawn++; if (hidden) ghosted++;
          const o = (py * W + px) * 4;
          for (let c2 = 0; c2 < 3; c2++)
            out.data[o + c2] = Math.round(out.data[o + c2] * (1 - k) + S.data[(sy * S.w + sx) * 4 + c2] * k);
        }
      }
      charInfo = {charPx: Math.round(hpx), occludedFrac: drawn ? +(ghosted / drawn).toFixed(3) : 0};
    }
  }
  fs.mkdirSync(path.dirname(outPath), {recursive: true});
  fs.writeFileSync(outPath, PNG.sync.write(out, {deflateLevel: 9}));
  return charInfo;
}
// The report's copy of the same image. Smaller and 3-bit-quantised (487 KB against 1.9 MB
// at the judging frame) because a run directory is COMMITTED and there will be many of
// them; the judging input itself is deleted after the run, since it is reproducible from
// the shipped plate and this file, and CLAUDE.md says clean temp renders every run.
function writeDisplay(srcPath, outPath, W = 896, q = 8) {
  const src = readPng(srcPath), sc = src.width / W, H = Math.round(src.height / sc);
  const o = new PNG({width: W, height: H});
  const Q = (v) => Math.min(255, Math.round(v / q) * q);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    let r = 0, g = 0, b = 0, n = 0;
    for (let dy = 0; dy < Math.ceil(sc); dy++) for (let dx = 0; dx < Math.ceil(sc); dx++) {
      const sx = Math.min(src.width - 1, Math.floor(x * sc + dx));
      const sy = Math.min(src.height - 1, Math.floor(y * sc + dy));
      const i = (sy * src.width + sx) * 4; r += src.data[i]; g += src.data[i + 1]; b += src.data[i + 2]; n++;
    }
    const oi = (y * W + x) * 4;
    o.data[oi] = Q(r / n); o.data[oi + 1] = Q(g / n); o.data[oi + 2] = Q(b / n); o.data[oi + 3] = 255;
  }
  fs.mkdirSync(path.dirname(outPath), {recursive: true});
  fs.writeFileSync(outPath, PNG.sync.write(o, {deflateLevel: 9}));
}

// ------------------------------------------------------------- THE PROMPTS ---
const STYLE_BLOCKOUT = [
  'IMPORTANT — this scene is an UNTEXTURED MASSING BLOCKOUT. Flat untextured surfaces,',
  'simple faceted shapes, missing surface detail and placeholder colours are INTENDED at',
  'this stage and are NOT problems. Do not report them. Judge only the LAYOUT: what is',
  'where, what blocks what, whether the space and its ways through can be read.',
].join('\n');
const STYLE_ART = [
  'The scene is a finished hand-stylised illustration; a painterly or simplified look is',
  'the intended art style and is not a problem in itself.',
].join('\n');

const NAIVE_PROMPT = [
  'You are a first-time player. The image is one frame of a video game, exactly what is on',
  'screen. You have never been here, you have no map, and nobody has told you anything.',
  '',
  'Critique this frame. Report anything that would make the place HARD TO UNDERSTAND or',
  'HARD TO PLAY. Use exactly these category tokens:',
  '  navigation  — you would not know where to go, or the way on is ambiguous',
  '  occlusion   — something blocks your understanding of the space',
  '  geometry    — incomplete, stray, floating, clipping, or plainly ugly geometry',
  '  exit        — a door or way out that does not read as a door or a way out',
  '  immersion   — floating objects, z-fighting, wrong scale, anything that breaks belief',
  '',
  IS_BLOCKOUT ? STYLE_BLOCKOUT : STYLE_ART,
  '',
  'RULES. Report only things you can actually point at in this image. Do NOT invent',
  'problems to fill the list, and do NOT list matters of taste. If the frame is fine,',
  'return an empty list — that is a valid and useful answer. At most 6 findings.',
  'severity: 3 = a player would be stuck or would think the game is broken, 2 = clearly',
  'wrong but survivable, 1 = a blemish.',
  '',
  'Answer with JSON only, in this exact shape:',
  '{"findings":[{"category":"occlusion","where":"a few words locating it in the frame",',
  ' "bbox":[x0,y0,x1,y1],"severity":2,"desc":"one sentence"}]}',
  'bbox is in normalised image coordinates: x 0 at the left edge and 1 at the right, y 0',
  'at the top edge and 1 at the bottom.',
].join('\n');

function checklistPrompt(items) {
  return [
    'You are auditing one frame of a video game. The designer says the things listed below',
    'are in this shot and that a player should be able to find them. For EACH item, decide',
    'which of these four is true, using the exact token:',
    '  FINDABLE               a first-time player would find it AND know what it is',
    '  OCCLUDED               it is hidden behind something else (say what hides it)',
    '  VISIBLE-BUT-ILLEGIBLE  part of it is on screen, but it does not read as what it is',
    '                         — too small, too dark, merged into its background, cropped,',
    '                         or it looks like some other kind of thing entirely',
    '  ABSENT                 you cannot see it anywhere in this frame at all',
    '',
    IS_BLOCKOUT ? STYLE_BLOCKOUT : STYLE_ART,
    '',
    'YOU ARE NOT TOLD WHERE ANYTHING IS. Do not guess a position to be helpful: if you',
    'cannot find it, ABSENT is the correct and useful answer. If you DO find it, give the',
    'bbox where you see it so your reading can be checked against the model.',
    '',
    'Two rules that keep the answers useful. (1) Names like "shelf-west" are the designers\'',
    'internal names for other areas; a player never sees them, so NEVER report a missing',
    'sign, label or name as a problem — judge only whether the thing itself can be found and',
    'recognised for what it is. (2) Judge what is DRAWN, not what a game would normally add:',
    'no icons, markers or waypoints exist in this art and their absence is not a finding.',
    '',
    'Items:',
    ...items.map((it, i) => `  ${i + 1}. ${it.what}`),
    '',
    'Answer with JSON only, one entry per item, in order:',
    '{"items":[{"n":1,"verdict":"FINDABLE","where":"a few words","bbox":[x0,y0,x1,y1],',
    ' "desc":"one sentence saying how you recognised it, or what hides it, or why it does',
    ' not read"}]}',
    'bbox is normalised: x 0 left to 1 right, y 0 top to 1 bottom. Use null when ABSENT.',
  ].join('\n');
}

// TWO SCEPTICS, AND THE SECOND ONE IS A BUG FIX WITH A RECEIPT. Run 20260731-calib
// refuted 44 of 81 claims and THIRTY-ONE of those were checklist claims thrown out on the
// grounds that the object was not in evidence — "expecting a pathway to a building that
// does not exist in the scene", "demanding specific named off-camera exits is unfounded".
// A context-free sceptic cannot help doing that, and it deleted the whole map-informed
// mode: checklist scored 0/5 on the calibration in that run. So a checklist claim is put
// to a sceptic that HAS the contract and is told the object's existence is not the
// question. The naive sceptic is unchanged — its innocence is the point, exactly as the
// naive critic's is.
function refutePrompt(claims, mode) {
  const head = mode === 'checklist' ? [
    'You are the sceptic on a game art review. The claims below are about objects that the',
    'DESIGNER\'S OWN MAP says really are in this shot. That they belong here is NOT in',
    'question, and "it is not there" / "this area would not have one" / "expecting it is',
    'arbitrary" are NOT valid refutations. The only question is whether the claim about how',
    'well a player can FIND or READ the object is fair.',
    '',
    'UPHOLD if, looking at the frame yourself, you agree the object is genuinely hard to',
    'find, hidden behind something, or does not read as the kind of thing it is. REFUTE if',
    'you can point straight at it and it is plainly legible, or if the complaint is really',
    'about a missing sign, label, icon or name rather than about the art.',
  ] : [
    'You are the sceptic on a game art review, and your job is to protect the team from',
    'wasted work. Below are criticisms somebody has made of THIS frame. For each one,',
    'decide honestly whether it is a REAL problem for a player, or whether it is a',
    'misreading of the picture, a matter of taste, or simply normal for this art style.',
    '',
    'UPHOLD only if you can find the same thing in the frame yourself AND it would really',
    'cost a player something. REFUTE if the thing described is not there, is not what the',
    'critic thought it was, is normal for the style, or does not matter. Do not be polite:',
    'refuting a weak criticism is the useful answer.',
  ];
  return [...head, '', IS_BLOCKOUT ? STYLE_BLOCKOUT : STYLE_ART, '', 'Claims:',
    ...claims.map((c, i) => `  ${i + 1}. [${c.category}] ${c.where ? c.where + ': ' : ''}${c.desc}`),
    '', 'Answer with JSON only, one entry per claim, in order:',
    '{"verdicts":[{"n":1,"verdict":"upheld","why":"one sentence"}]}',
  ].join('\n');
}

// -------------------------------------------------------------- THE JUDGES ---
function envKey() {
  try {
    const env = Object.fromEntries(fs.readFileSync(path.join(ROOT, '.env'), 'utf8').split('\n')
      .filter((l) => l.includes('=') && !l.trim().startsWith('#'))
      .map((l) => [l.slice(0, l.indexOf('=')).trim(),
                   l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]));
    return env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;
  } catch { return process.env.GEMINI_API_KEY; }
}
const BUDGET = {calls: 0, promptTok: 0, replyTok: 0, errors: 0, byStage: {}};
const geminiJudge = {
  name: `gemini:${MODEL}`,
  async ask(imagePath, prompt, stage) {
    const KEY = envKey();
    if (!KEY) throw new Error('no GEMINI_API_KEY in .env');
    const body = {contents: [{parts: [
      {inline_data: {mime_type: 'image/png', data: fs.readFileSync(imagePath).toString('base64')}},
      {text: prompt}]}], generationConfig: {temperature: TEMP, responseMimeType: 'application/json'}};
    let last = null;
    for (let a = 0; a < 4; a++) {
      BUDGET.calls++; BUDGET.byStage[stage] = (BUDGET.byStage[stage] || 0) + 1;
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${KEY}`,
        {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)});
      const j = await res.json().catch(() => ({}));
      if (res.ok) {
        const u = j.usageMetadata || {};
        BUDGET.promptTok += u.promptTokenCount || 0;
        BUDGET.replyTok += (u.candidatesTokenCount || 0) + (u.thoughtsTokenCount || 0);
        const t = (j.candidates?.[0]?.content?.parts || []).map((p) => p.text || '').join('');
        if (t.trim()) return {text: t};
        last = 'empty reply: ' + JSON.stringify(j).slice(0, 260);
      } else {
        last = `HTTP ${res.status} ` + JSON.stringify(j).slice(0, 260);
        if (res.status !== 429 && res.status < 500) break;
      }
      await new Promise((r) => setTimeout(r, 1500 * (a + 1) * (a + 1)));
    }
    BUDGET.errors++;
    throw new Error(last || 'gemini failed');
  },
};
// the no-API harness self-check: fixed, obviously-fake answers that still exercise every
// line of the parse / verify / dedup / report path.
const stubJudge = {name: 'stub', async ask(_img, prompt, stage) {
  BUDGET.calls++; BUDGET.byStage[stage] = (BUDGET.byStage[stage] || 0) + 1;
  if (stage === 'naive') return {text: JSON.stringify({findings: [
    {category: 'occlusion', where: 'centre', bbox: [0.3, 0.3, 0.7, 0.7], severity: 2,
     desc: 'A stub foliage canopy blocks the road into the area.'},
    {category: 'geometry', where: 'lower right', bbox: [0.6, 0.6, 0.95, 0.95], severity: 1,
     desc: 'A stub stray cliff rock floats with weird flat geometry.'}]})};
  if (stage === 'checklist') { const n = (prompt.match(/^ {2}\d+\. /gm) || []).length;
    return {text: JSON.stringify({items: Array.from({length: n}, (_, i) => ({n: i + 1,
      verdict: i % 3 === 0 ? 'OCCLUDED' : i % 3 === 1 ? 'VISIBLE-BUT-ILLEGIBLE' : 'FINDABLE',
      where: 'stub', bbox: [0.4, 0.4, 0.6, 0.6], desc: 'stub verdict'}))})}; }
  const n = (prompt.match(/^ {2}\d+\. /gm) || []).length;
  return {text: JSON.stringify({verdicts: Array.from({length: n}, (_, i) =>
    ({n: i + 1, verdict: i % 4 === 3 ? 'refuted' : 'upheld', why: 'stub'}))})};
}};
// REPLAY. Every reply the judge ever gave is written to raw/<shot>.json, so a run can be
// re-derived from its own record without spending a call: `--replay <stamp>` re-runs the
// whole parse / verify / dedup / triage / report path over the stored text. It exists
// because the pinned judge's replies are the EXPENSIVE part and this file's parser is the
// cheap part — when the parser was found to be dropping bare-array replies and reading
// bounding boxes in the wrong convention, the fix could be applied to a finished run
// instead of being paid for twice. A claim whose refutation was never asked for (because
// the old parser never produced the claim) is marked `no-verdict` and is therefore
// REFUTED, never silently promoted.
function replayJudge(shotRaw) {
  let k = 0;
  return {name: 'replay', async ask(_img, _prompt, stage) {
    const key = stage === 'naive' ? 'naive_' + (k++) : stage.replace('refute-', 'refute_');
    const t = shotRaw[key] ?? (stage === 'naive' && k === 1 ? shotRaw.naive : undefined);
    if (t === undefined) throw new Error('no stored reply for stage ' + stage);
    return {text: t};
  }};
}
const JUDGES = {gemini: geminiJudge, stub: stubJudge};

// The pinned judge answers the shape it was asked for MOST of the time. Run
// 20260731-calib3 lost the whole `gate` checklist because that one reply came back as a
// bare ARRAY instead of {"items": [...]} — silently, since `j.items` was simply undefined.
// Both shapes are accepted now, and a reply that parses to neither is an error, not an
// empty result.
const parseJson = (text, key) => {
  const t = (s) => { try { return JSON.parse(s); } catch { return null; } };
  let j = t(text);
  if (!j) { const m = /[[{][\s\S]*[\]}]/.exec(text); if (m) j = t(m[0]); }
  if (Array.isArray(j) && key) j = {[key]: j};
  return j;
};
const clamp01 = (n) => Math.max(0, Math.min(1, +n || 0));
// BOXES COME BACK IN TWO CONVENTIONS AND THE WRONG READING PUTS EVERY ANNOTATION IN THE
// WRONG PLACE. Asked for normalised [x0,y0,x1,y1], the judge sometimes answers in its own
// native `box_2d` instead: [ymin,xmin,ymax,xmax] on a 0..1000 grid. The two are told apart
// by scale, and the choice is CHECKED, not assumed — `bboxAgreement()` below scores both
// readings against the ray census (which knows where every checklist item really is) and
// the run report prints the score, so a bad guess shows up as a number instead of as
// quietly misplaced rectangles.
function okBox(b) {
  if (!Array.isArray(b) || b.length !== 4 || !b.every((n) => Number.isFinite(+n))) return null;
  let v = b.map(Number);
  if (Math.max(...v.map(Math.abs)) > 1.5) v = [v[1] / 1000, v[0] / 1000, v[3] / 1000, v[2] / 1000];
  return [clamp01(Math.min(v[0], v[2])), clamp01(Math.min(v[1], v[3])),
          clamp01(Math.max(v[0], v[2])), clamp01(Math.max(v[1], v[3]))];
}
// how often does a judged bbox actually contain the point the census projected? Only
// checklist items can be scored (they are the ones with a known world position) and only
// those the census calls `clear`. A low number means the boxes are not to be trusted as
// annotations, whatever the words say.
function bboxAgreement(shots) {
  let hit = 0, n = 0;
  for (const s of shots) for (const it of s.checklist || []) {
    const b = it.judged && it.judged.bbox, c = it.census;
    if (!b || !c || c.state !== 'clear') continue;
    n++;
    if (c.u >= b[0] && c.u <= b[2] && c.v >= b[1] && c.v <= b[3]) hit++;
  }
  return {n, hit, frac: n ? +(hit / n).toFixed(3) : null};
}

// ---------------------------------------------------------------- THE RUN ----
const CATS = ['navigation', 'occlusion', 'geometry', 'exit', 'immersion'];
async function pool(items, n, fn) {
  const out = new Array(items.length); let i = 0;
  await Promise.all(Array.from({length: Math.min(n, items.length)}, async () => {
    for (;;) { const k = i++; if (k >= items.length) return; out[k] = await fn(items[k], k); }
  }));
  return out;
}
let SEQ = 0;
async function runShot(judge, id, inputPath, wantNaive, wantChecklist) {
  const cam = camOf(id);
  const findings = [], raw = {};
  // N LOOKS AT THE PICTURE, UNIONED. One look mentions two of the six things it could,
  // and which two is close to a coin toss: runs 20260731-calib and -calib2 are the same
  // pinned judge on the same plates, and the gate shot produced six findings in one and
  // two in the other, overlapping in one. nav_eval already carries this lesson (noise
  // +-0.20/shot at N=5). Recall here is therefore a UNION over N independent looks, and
  // every survivor records `support` — how many looks raised it — so a one-sample hunch
  // and a unanimous complaint are told apart instead of being averaged into each other.
  if (wantNaive) {
    const seen = [];
    for (let k = 0; k < N; k++) {
      try {
        const r = await judge.ask(inputPath, NAIVE_PROMPT, 'naive');
        raw['naive_' + k] = r.text;
        const j = parseJson(r.text, 'findings') || {};
        for (const f of (j.findings || []).slice(0, 8)) {
          const cat = CATS.includes(String(f.category || '').toLowerCase())
            ? String(f.category).toLowerCase() : 'geometry';
          const bb = okBox(f.bbox), desc = String(f.desc || '').slice(0, 400);
          const w = words(desc);
          const dup = seen.find((g) => g.category === cat && jac(words(g.desc), w) >= 0.45);
          if (dup) { dup.support++; if (!dup.bbox) dup.bbox = bb; continue; }
          const nf = {fid: 'F' + (++SEQ), mode: 'naive', town: TOWN, shot: id, item: null,
                      category: cat, where: String(f.where || '').slice(0, 90), bbox: bb,
                      severity: Math.max(1, Math.min(3, Math.round(+f.severity || 2))), desc,
                      support: 1, of: N, census: null,
                      hint: cat === 'geometry' || cat === 'immersion' ? bboxWorld(cam, bb) : null};
          seen.push(nf); findings.push(nf);
        }
      } catch (e) { raw['naiveError_' + k] = String(e.message || e); }
    }
  }
  let items = [];
  if (wantChecklist) {
    items = checklistFor(id, cam);
    if (items.length) {
      try {
        const r = await judge.ask(inputPath, checklistPrompt(items), 'checklist');
        raw.checklist = r.text;
        const j = parseJson(r.text, 'items') || {};
        for (const a of (j.items || [])) {
          const it = items[(+a.n || 0) - 1]; if (!it) continue;
          const v = String(a.verdict || '').toUpperCase().replace(/[^A-Z-]/g, '');
          it.judged = {verdict: v, where: String(a.where || '').slice(0, 90),
                       bbox: okBox(a.bbox), desc: String(a.desc || '').slice(0, 400)};
          if (v === 'FINDABLE') continue;                     // not a finding: it worked
          // ABSENT on something the census says is genuinely off-frame is the MAP's
          // problem to state, not this shot's defect, and cine_test already asserts it —
          // so it is recorded and not raised as a finding.
          if (v === 'ABSENT' && (it.census.state === 'off-frame' || it.census.state === 'behind-camera')) {
            it.suppressed = 'census agrees it is not in this frame (cine_test owns that)';
            continue;
          }
          // ABSENT is only a DEFECT against the shot's own contract. A distant mapVisible
          // landmark the judge cannot name is a scenery item, not a broken promise, and
          // run 20260731-calib produced eleven of those ("no distinct boatwright's shed
          // can be seen") for one real one. Recorded, not raised.
          if (v === 'ABSENT' && !it.must) { it.suppressed = 'ABSENT on a scenery item, not on the shot contract'; continue; }
          const cat = v === 'OCCLUDED' ? 'occlusion' : v === 'ABSENT' ? 'navigation' : 'navigation';
          findings.push({fid: 'F' + (++SEQ), mode: 'checklist', town: TOWN, shot: id,
                         item: it.id, itemWhat: it.what, verdict: v, category: cat,
                         where: it.judged.where, bbox: it.judged.bbox, severity: v === 'ABSENT' ? 3 : 2,
                         desc: `${it.what.split(' — ')[0]}: ${v} — ${it.judged.desc}`,
                         census: it.census, hint: null});
        }
      } catch (e) { raw.checklistError = String(e.message || e); }
    }
  }
  // ---- STAGE 2 ------------------------------------------------------------
  // (ii) first, because an instrument beats an opinion: a checklist OCCLUDED verdict the
  // census also calls occluded is UPHELD BY THE CENSUS and never goes to the refuter.
  const toRefute = {naive: [], checklist: []};
  for (const f of findings) {
    if (f.mode === 'checklist' && f.verdict === 'OCCLUDED' && f.census && f.census.state === 'occluded') {
      f.verify = {verdict: 'upheld', by: 'ray-census',
                  why: `the shot's own depth plate draws something ${f.census.behindBy} m nearer at that pixel`};
    } else toRefute[f.mode].push(f);
  }
  for (const mode of ['naive', 'checklist']) {
    const claims = toRefute[mode];
    if (!claims.length) continue;
    try {
      const r = await judge.ask(inputPath, refutePrompt(claims, mode), 'refute-' + mode);
      raw['refute_' + mode] = r.text;
      const j = parseJson(r.text, 'verdicts') || {};
      for (const v of (j.verdicts || [])) {
        const f = claims[(+v.n || 0) - 1]; if (!f) continue;
        f.verify = {verdict: String(v.verdict || '').toLowerCase().startsWith('up') ? 'upheld' : 'refuted',
                    by: 'adversarial-judge:' + mode, why: String(v.why || '').slice(0, 300)};
      }
    } catch (e) { raw['refuteError_' + mode] = String(e.message || e); }
    // a claim the refuter never answered is NOT silently promoted
    for (const f of claims) if (!f.verify)
      f.verify = {verdict: 'refuted', by: 'no-verdict', why: 'the refuter returned no verdict for this claim'};
  }
  return {shot: id, items, findings, raw};
}

// ------------------------------------------------------------------ DEDUP ----
// "the same object seen twice is one finding". Checklist findings dedup exactly, by item
// id. Naive findings have no ids, so they dedup by category + a Jaccard overlap of their
// content words — cheap, deterministic, and WRONG IN BOTH DIRECTIONS at the margins
// (two different rails on two shots read as one; one canopy described twice in different
// words stays two). Every merge records the shots it swallowed so it can be unpicked.
const STOP = new Set(('the a an and or of to in on at is are be it its this that with for from by as' +
  ' there here you your player would could not no very quite some any which what where').split(' '));
const words = (s) => new Set(String(s).toLowerCase().replace(/[^a-z ]/g, ' ').split(/\s+/)
  .filter((w) => w.length > 3 && !STOP.has(w)));
function jac(a, b) { let i = 0; for (const w of a) if (b.has(w)) i++;
  return i / (a.size + b.size - i || 1); }
function dedup(all) {
  const out = [];
  for (const f of all) {
    const fw = words(f.desc);
    const hit = out.find((g) => g.mode === f.mode && g.category === f.category &&
      (f.mode === 'checklist' ? g.item === f.item : jac(words(g.desc), fw) >= 0.55));
    if (hit) { hit.alsoOn = hit.alsoOn || []; hit.alsoOn.push({shot: f.shot, fid: f.fid, desc: f.desc});
               hit.severity = Math.max(hit.severity, f.severity); }
    else out.push({...f});
  }
  return out;
}

// ----------------------------------------------------------------- TRIAGE ----
const hay = (f) => `${f.desc} ${f.where || ''} ${f.itemWhat || ''}`.toLowerCase();
const groupsHit = (h, groups) => groups.every((g) => !g.length || g.some((t) => h.includes(t)));
function triage(f) {
  const h = hay(f);
  for (const t of TRACKED) { if (t.town && t.town !== TOWN) continue;
    if (groupsHit(h, t.terms)) return {bucket: 'known', by: t.id, where: t.where}; }
  if (IS_BLOCKOUT && groupsHit(h, [['material', 'texture', 'colour', 'color', 'grey', 'gray', 'detail',
      'placeholder', 'flat', 'plain', 'bland', 'untextured', 'poly'], []]))
    return {bucket: 'style-bar', by: 'blockout-dressing', where: 'waits for the dressing pass'};
  return {bucket: 'new', by: null, where: null};
}

// ------------------------------------------------------------- CALIBRATION ---
function scoreCalibration(survivors, refuted) {
  const rows = [];
  for (const c of CALIBRATION.complaints) {
    const row = {...c, modes: {}};
    for (const mode of ['naive', 'checklist']) {
      const cand = [...survivors, ...refuted].filter((f) => f.mode === mode &&
        c.shots.includes(f.shot) && groupsHit(hay(f), c.keys));
      const strict = cand.filter((f) => f.shot === c.primary);
      const surv = new Set(survivors.map((f) => f.fid));
      row.modes[mode] = {
        lenient: cand.length > 0, strict: strict.length > 0,
        survivingLenient: cand.some((f) => surv.has(f.fid)),
        survivingStrict: strict.some((f) => surv.has(f.fid)),
        hits: cand.map((f) => ({fid: f.fid, shot: f.shot, desc: f.desc, category: f.category,
                                survived: surv.has(f.fid),
                                verify: f.verify || null})),
      };
    }
    row.foundStrict = row.modes.naive.survivingStrict || row.modes.checklist.survivingStrict;
    row.foundLenient = row.modes.naive.survivingLenient || row.modes.checklist.survivingLenient;
    rows.push(row);
  }
  const n = (k) => rows.filter((r) => r[k]).length;
  const matched = new Set(rows.flatMap((r) => [...r.modes.naive.hits, ...r.modes.checklist.hits])
    .filter((h) => h.survived).map((h) => h.fid));
  return {rows, strict: n('foundStrict'), lenient: n('foundLenient'), total: rows.length,
          extras: survivors.filter((f) => !matched.has(f.fid))};
}

// ---------------------------------------------------------------- REPORTING --
const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
  .replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function boxOverlay(f, cls) {
  const b = f.bbox; if (!b) return '';
  return `<div class="bx ${cls}" style="left:${(b[0] * 100).toFixed(2)}%;top:${(b[1] * 100).toFixed(2)}%;` +
         `width:${((b[2] - b[0]) * 100).toFixed(2)}%;height:${((b[3] - b[1]) * 100).toFixed(2)}%"></div>`;
}
// A CSS crop: the plate as a background, zoomed so the finding's own bbox roughly fills
// the tile. No image processing and no second copy of any plate on disk. Percentage
// background-position is used deliberately — it aligns the image's (cx, cy) point with
// the tile's (cx, cy) point, which cannot scroll the image out of the tile at any zoom,
// so a bad bbox degrades to a wrong-but-visible crop instead of a black rectangle.
function cropTile(f, src) {
  const b = f.bbox && f.bbox.length === 4 ? f.bbox : [0, 0, 1, 1];
  const w = Math.max(0.12, b[2] - b[0]), h = Math.max(0.12, b[3] - b[1]);
  const k = Math.max(1, Math.min(1 / w, 1 / h, 5));
  const cx = ((b[0] + b[2]) / 2 * 100).toFixed(1), cy = ((b[1] + b[3]) / 2 * 100).toFixed(1);
  return `<div class="crop" style="background-image:url('${src}');background-size:${(k * 100).toFixed(0)}% auto;` +
         `background-position:${cx}% ${cy}%"></div>`;
}

function findingCard(f, plateSrc) {
  const v = f.verify || {};
  return `<div class="card sev${f.severity}">
    <div class="ch"><span class="pill ${f.mode}">${f.mode}</span>
      <span class="pill cat">${esc(f.category)}</span>
      <span class="pill sev">sev ${f.severity}</span>
      ${f.support ? `<span class="pill sup" title="independent looks that raised it">${f.support}/${f.of} looks</span>` : ''}
      <span class="shot">${esc(f.shot)}</span>
      ${f.alsoOn && f.alsoOn.length ? `<span class="pill also">+${f.alsoOn.length} more shot${f.alsoOn.length > 1 ? 's' : ''}</span>` : ''}
    </div>
    ${cropTile(f, plateSrc)}
    <div class="cb"><div class="q">${esc(f.desc)}</div>
      ${f.where ? `<div class="meta">where: ${esc(f.where)}</div>` : ''}
      ${f.census ? `<div class="meta">ray census: <b>${esc(f.census.state)}</b>${
        f.census.state === 'occluded' ? ` (plate is ${f.census.behindBy} m nearer)` : ''}, ${
        f.census.charPx} px tall at ${f.census.z} m</div>` : ''}
      <div class="meta verify ${v.verdict}">verify: <b>${esc(v.verdict)}</b> by ${esc(v.by)} — ${esc(v.why)}</div>
      ${f.hint ? `<div class="meta cmd">${esc(f.hint.cmd)}</div>` : ''}
      ${f.alsoOn && f.alsoOn.length ? `<div class="meta">also on: ${f.alsoOn.map((a) => esc(a.shot)).join(', ')}</div>` : ''}
    </div></div>`;
}

// THE HAND ADJUDICATION. The matcher above is keyword-and-shot, pre-registered so nobody
// can decide after the fact what counts — and it OVER-CREDITS, which the first two runs
// showed plainly: "the large vertical banners clip into the cliff face" scored a hit for
// "stray/weird cliff geometry" on the words `cliff` and `clip`, and it is not the same
// finding at all. So a human reads the quoted findings and writes adjudication.json
// beside the run; when it is there, BOTH numbers are printed and the gap between them is
// part of the result rather than something the report smooths over. Regenerate the page
// after writing it with `--rerender --stamp <stamp>`.
function loadAdjudication() {
  const p = path.join(OUTDIR, 'adjudication.json');
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; }
}
function writeReport(run) {
  const S = run.survivors, R = run.refuted;
  const BLK = run.blockout;
  const byBucket = (b) => S.filter((f) => f.triage.bucket === b);
  const cal = run.calibration;
  const adj = cal ? loadAdjudication() : null;
  const plate = (shot) => `plates/${shot}.png`;
  const AV = (id) => (adj && adj.rows && adj.rows[id]) || null;

  // §5 shows the judge's prompts verbatim. The templated ones are shown filled with
  // this run's own data so the page needs no reader-side imagination.
  const promptBlock = (title, text) => `<details class="prompt"><summary>${esc(title)}</summary>
<pre style="background:rgba(127,127,127,.12);padding:12px;overflow-x:auto;font-size:12px;line-height:1.45">${esc(text)}</pre></details>`;
  const clShot = (run.shots || []).filter((s) => s.checklist && s.checklist.length)
    .sort((a, b) => b.checklist.length - a.checklist.length)[0];
  const exampleClaims = (mode) => {
    const f = [...S, ...R].find((x) => x.mode === mode);
    return f ? [{category: f.category, where: f.where, desc: f.desc}]
             : [{category: 'occlusion', where: '(no ' + mode + ' claims in this run)', desc: ''}];
  };
  const adjN = adj ? cal.rows.filter((r) => (AV(r.id) || {}).verdict === 'hit').length : 0;
  const adjW = adj ? cal.rows.filter((r) => (AV(r.id) || {}).verdict === 'weak').length : 0;

  const verdictLine = !cal ? 'No calibration was scored in this run.'
    : (adj
      ? `<b>On the user's own five complaints, the judge found ${adjN} outright and ${adjW} weakly ` +
        `(${adjN + adjW}/5), and raised ${cal.extras.length} extra surviving findings.</b>` +
        `<div class="sub">That is the <em>hand-adjudicated</em> count, read off the quotes below. The ` +
        `pre-registered keyword matcher scores the same run ${cal.strict}/5 on the exact plate and ` +
        `${cal.lenient}/5 on any plate holding the object — it over-credits, and the gap is shown ` +
        `row by row rather than averaged away.</div>`
      : `On the user's own five complaints, the judge found <b>${cal.strict}/5</b> on the exact plate ` +
        `(<b>${cal.lenient}/5</b> counting any plate that holds the same object) and raised ` +
        `<b>${cal.extras.length}</b> other surviving findings. <div class="sub">Keyword matcher only — ` +
        `no hand adjudication has been written for this run.</div>`);

  const calRows = cal ? cal.rows.map((r) => {
    const cell = (m) => {
      const M = r.modes[m], live = M.hits.filter((h) => h.survived);
      if (!live.length) return `<td class="miss"><b>MISS</b>${M.hits.length ? `<div class="small">` +
        `${M.hits.length} match${M.hits.length > 1 ? 'es' : ''} raised but REFUTED at stage 2</div>` : ''}</td>`;
      // A cell shows at most four quotes. The waterfront row matched twenty-three and the
      // row grew taller than the screen, which is a way of hiding a result rather than
      // showing it; the rest are counted and live in findings.json.
      const show = live.slice(0, 4);
      return `<td class="hit"><b>${live.some((h) => h.shot === r.primary) ? 'HIT' : 'HIT (other plate)'}</b>` +
        show.map((h) => `<div class="quote">&ldquo;${esc(h.desc)}&rdquo;<span class="src">— ${esc(h.shot)}, ${esc(h.category)}</span></div>`).join('') +
        (live.length > show.length ? `<div class="small">+ ${live.length - show.length} more surviving matches on ${
          [...new Set(live.slice(4).map((h) => h.shot))].map(esc).join(', ')}</div>` : '') + '</td>';
    };
    return `<tr>
      <td class="refcell"><img src="refs/${r.ref}" alt=""><div class="small">${esc(r.ref)}</div></td>
      <td class="whatcell"><b>${esc(r.title)}</b><div class="said">${esc(r.said)}</div>
        <div class="small">plate under test: <code>${esc(r.primary)}</code>${r.shots.length > 1 ?
          ` (also ${r.shots.filter((s) => s !== r.primary).map(esc).join(', ')})` : ''}</div></td>
      ${cell('naive')}${cell('checklist')}${adj ? (() => { const a = AV(r.id) || {verdict: 'miss', why: 'not adjudicated'};
        return `<td class="adj ${a.verdict}"><b>${a.verdict.toUpperCase()}</b><div class="small">${esc(a.why)}</div></td>`;
      })() : ''}</tr>`;
  }).join('\n') : '';

  // WHERE EACH CRITIQUE CAME FROM. A partly re-swept town produces one report whose plates
  // were not all judged at the same time against the same bake; the reader is told per
  // plate rather than left to assume the newest date at the top covers all of them.
  const FRESH = run.freshFrom || null;   // the stamp whose replies were judged this round
  const provOf = (s) => !FRESH ? (s.replayOf ? 'replayed' : 'fresh')
    : s.replayOf === FRESH ? 'fresh' : 'replayed';
  const anyMixed = run.shots.some((s) => provOf(s) !== provOf(run.shots[0]));
  const provTable = !anyMixed ? '' : `<table><tr><th>plate</th><th>critique</th><th>replies from</th>
<th>bake it was judged against</th><th>survivors</th></tr>${run.shots.map((s) => {
    const p = provOf(s), sup = s.supersededBake;
    return `<tr><td><code>${esc(s.shot)}</code> <span class="small">${esc(s.name || '')}</span></td>
      <td class="${p === 'fresh' ? 'hit' : ''}"><b>${p.toUpperCase()}</b></td>
      <td class="small"><code>run-${esc(s.replayOf || run.stamp)}</code></td>
      <td class="small">${esc(s.baked || '?')}${sup ?
        ` <span class="pill sup" title="${esc(sup)}">against-superseded-bake</span>` : ''}</td>
      <td>${S.filter((f) => f.shot === s.shot).length}</td></tr>`;
  }).join('')}</table>
<p class="blurb">A <b>replayed</b> plate is not a weaker critique — it is the <em>same</em> judge replies,
re-parsed and re-verified by today's code against the same pixels, at no API cost. It is only weaker if
the plate has since been re-baked, and that case is flagged <span class="pill sup">against-superseded-bake</span>:
the finding is about a picture the town no longer ships, and it is shown against the picture it was
actually made about, never re-annotated onto the new one.</p>`;

  const shotSection = run.shots.map((s) => {
    const fs2 = S.filter((f) => f.shot === s.shot);
    return `<section class="shot"><h3>${esc(s.shot)} <span class="small">${esc(s.name || '')}${
      s.baked ? ` · bake ${esc(s.baked)}` : ''}${anyMixed ? ` · ${provOf(s)}` : ''}${
      s.supersededBake ? ' · <span class="pill sup">against-superseded-bake</span>' : ''}</span></h3>
      <div class="wrap"><img class="plate" src="${plate(s.shot)}" alt="">
        ${fs2.map((f) => boxOverlay(f, f.mode)).join('')}</div>
      <div class="small">${fs2.length} surviving finding${fs2.length === 1 ? '' : 's'} ·
        ${R.filter((f) => f.shot === s.shot).length} refuted ·
        ${s.items} checklist item${s.items === 1 ? '' : 's'}</div></section>`;
  }).join('\n');

  const bucketBlock = (b, title, blurb) => {
    const list = byBucket(b);
    return `<h3>${title} <span class="count">${list.length}</span></h3><p class="blurb">${blurb}</p>
      <div class="grid">${list.length ? list.map((f) => findingCard(f, plate(f.shot))).join('') :
        '<div class="empty">nothing in this bucket</div>'}</div>`;
  };

  const html = `<meta charset="utf-8"><title>Scene red-team — ${esc(run.town)} — run ${esc(run.stamp)}</title>
<style>
:root{--bg:#14110e;--fg:#efe6d8;--dim:#a2957f;--line:#33291f;--hit:#5fb56b;--miss:#c9584a;
      --naive:#e0a33c;--checklist:#5aa9d6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.55 -apple-system,Segoe UI,Roboto,sans-serif}
.pad{max-width:1240px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:38px 0 6px;border-bottom:1px solid var(--line);
  padding-bottom:6px}h3{font-size:15px;margin:24px 0 4px}
.small{color:var(--dim);font-size:12px}.blurb{color:var(--dim);margin:2px 0 10px;font-size:13px}
code{background:#241d16;padding:1px 5px;border-radius:3px;font-size:12px}
.verdict{background:#1e1912;border:1px solid var(--line);border-left:4px solid var(--naive);
  padding:14px 16px;border-radius:6px;margin:14px 0 6px;font-size:16px;line-height:1.6}
table{border-collapse:collapse;width:100%;margin-top:10px}
th,td{border:1px solid var(--line);padding:9px;vertical-align:top;font-size:13px}
th{background:#1e1912;text-align:left;font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.04em}
.refcell{width:210px}.refcell img{width:100%;border-radius:4px;display:block}
.whatcell{width:250px}.said{color:var(--dim);font-style:italic;margin:4px 0}
td.hit{background:#16240f}td.miss{background:#2a1512}
td.hit b{color:var(--hit)}td.miss b{color:var(--miss)}
.quote{margin-top:6px;padding-left:8px;border-left:2px solid var(--line)}
.src{display:block;color:var(--dim);font-size:11px}
.wrap{position:relative;display:block;line-height:0;border:1px solid var(--line);border-radius:4px;overflow:hidden}
.wrap img.plate{width:100%;display:block}
.bx{position:absolute;border:2px solid var(--naive);border-radius:2px;box-shadow:0 0 0 1px #0008}
.bx.checklist{border-color:var(--checklist)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;align-items:start}
.card{background:#1a1610;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.card.sev3{border-color:#6b3229}
.ch{padding:8px 10px;display:flex;gap:6px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line)}
.pill{font-size:10.5px;padding:1px 6px;border-radius:99px;background:#2a2118;color:var(--dim);
  text-transform:uppercase;letter-spacing:.04em}
.pill.naive{background:#3a2c12;color:var(--naive)}.pill.checklist{background:#122c3a;color:var(--checklist)}
.shot{margin-left:auto;font-size:12px;color:var(--dim)}
.crop{width:100%;aspect-ratio:16/9;background:#000 no-repeat;border-bottom:1px solid var(--line)}
.cb{padding:10px}.q{font-size:13px}
.meta{color:var(--dim);font-size:11.5px;margin-top:5px}
.meta.cmd{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;word-break:break-all;color:#8fa07d}
.verify.upheld b{color:var(--hit)}.verify.refuted b{color:var(--miss)}
.count{color:var(--dim);font-weight:400;font-size:12px}
.empty{color:var(--dim);font-size:12px;padding:10px}
.limits{background:#1c1712;border:1px solid var(--line);border-left:4px solid var(--miss);
  padding:14px 18px;border-radius:6px}
.limits li{margin:5px 0}
section.shot{margin:18px 0 26px}
.budget{color:var(--dim);font-size:12px;margin-top:8px}
.sub{color:var(--dim);font-size:12.5px;font-weight:400;margin-top:8px;line-height:1.5}
td.adj{width:190px}td.adj.hit{background:#16240f}td.adj.hit b{color:var(--hit)}
td.adj.weak{background:#2a2410}td.adj.weak b{color:var(--naive)}
td.adj.miss{background:#2a1512}td.adj.miss b{color:var(--miss)}
.pill.sup{background:#22301f;color:#8fbf7f}
</style>
<div class="pad">
<h1>Scene red-team — ${esc(run.town)}</h1>
<div class="small">run <code>${esc(run.stamp)}</code> · judge <code>${esc(run.judge)}</code> (pinned) ·
  ${run.shots.length} plates · ${run.modes.join(' + ')} · naive N=${run.n} ·
  generated ${esc(run.generated)} by <code>tools/scene_redteam.mjs</code>${(() => {
    const b = run.shots.map((s) => s.baked).filter(Boolean).sort();
    return b.length ? ` · plates baked ${esc(b[0])}${b[0] === b[b.length - 1] ? '' : ' .. ' + esc(b[b.length - 1])}` : '';
  })()}${BLK ?
  ' · <b>blockout mode</b>: the judge was told this town is massing-only' : ''}</div>

<h2>1 &nbsp;The prompts, verbatim</h2>
<p class="blurb">Exactly what each judge call was asked (judge <code>${esc(run.judge)}</code>, pinned) —
read these first; everything below is these prompts' output. The naive prompt is fixed for the whole
run; the checklist and sceptic prompts are templates filled per plate — shown here filled with this
run's own data. The style paragraph switches between art and blockout mode; this run used
${BLK ? 'blockout' : 'art'} mode, and that is the version shown.</p>
${promptBlock('Stage 1 — the naive critic (every plate, each of the N looks)', NAIVE_PROMPT)}
${promptBlock('Stage 1 — the checklist auditor' + (clShot ? ` (filled for plate "${clShot.shot}", ${clShot.checklist.length} items derived from the map/ownership contract)` : ''),
    clShot ? checklistPrompt(clShot.checklist) : '(no checklist-mode plate in this run)')}
${promptBlock('Stage 2 — the naive sceptic (shown with one real claim from this run; the live call lists every claim on the plate)',
    refutePrompt(exampleClaims('naive'), 'naive'))}
${promptBlock('Stage 2 — the checklist sceptic (contract-aware: told the object\'s existence is not in question; shown with one real claim)',
    refutePrompt(exampleClaims('checklist'), 'checklist'))}

<h2>2 &nbsp;How well does this work?</h2>
<div class="verdict">${verdictLine}</div>
<p class="blurb">The gate is recall against complaints the user made <em>by hand</em>, before this tool
existed. The judge is never told what the complaints are; it is shown the shipped plate that holds the
object and asked to criticise it. Two numbers because there is a real ambiguity: <b>exact plate</b> counts
the finding only on the one shot whose frame most nearly holds what the user circled; <b>any plate</b>
counts it on any shot holding the same object. <b>Not reproducible, and said plainly:</b> all five
references were screenshot from a free orbit camera, from angles no shipped plate holds — so this
measures whether the same defect is <em>catchable from the shipped frames</em>, not whether the judge
can reproduce the user's screenshots.</p>
${cal ? `<table><tr><th>The user's frame</th><th>The complaint</th><th>Naive mode</th>
<th>Checklist mode</th>${adj ? '<th>Adjudicated</th>' : ''}</tr>${calRows}</table>
<p class="blurb">Stage 2 refuted <b>${R.length}</b> of ${S.length + R.length} raw findings across this run
(${((R.length / Math.max(1, S.length + R.length)) * 100).toFixed(0)}%). Refuted claims are kept in
<code>refuted.json</code>; a red MISS above with "matches raised but REFUTED" means the judge saw the
thing and the sceptic threw it away — that is a stage-2 miscalibration, not a stage-1 blindness.
${adj ? 'The two mode columns are the <b>pre-registered keyword matcher\'s</b> view and the last column is a ' +
'human reading the same findings; where they disagree the row says so. A row can read MISS in both mode ' +
'columns and HIT when adjudicated — that is the matcher\'s key list having a gap, not the judge missing ' +
'the defect. The keys are deliberately not edited to close such a gap after the fact.' : ''}</p>` : ''}

<h2>3 &nbsp;The sweep — surviving findings, triaged</h2>
<p class="blurb">${S.length} survivors from ${S.length + R.length} raw findings over ${run.shots.length}
plates. Deduped across shots: a finding seen on more than one plate is listed once and says so.</p>
${adj && adj.extras ? `<div class="verdict" style="border-left-color:var(--checklist)">
<b>Hand count of the extras:</b> the ${adj.extras.surviving} surviving findings that are not one of the
user's five are paraphrases of about <b>${adj.extras.distinctObjects}</b> distinct objects; of those
<b>${adj.extras.realLooking} look real</b>, ${adj.extras.doubtful} are doubtful and
${adj.extras.false} are false.<div class="sub">${esc(adj.extras.note)}</div></div>` : ''}
${adj && adj.status ? `<div class="limits" style="border-left-color:var(--naive);margin:14px 0">
<b>Run status.</b> ${esc(adj.status)}</div>` : ''}
${bucketBlock('known', 'Already known / tracked', 'The judge re-found something the repo already ' +
  'knows about. Useful as a confirmation that the instrument sees real defects; not new work.')}
${bucketBlock('new', 'New, and looks real', 'Not matched to anything tracked. This is the bucket ' +
  'that earns the tool its keep — and the bucket a human must read before anybody acts on it.')}
${bucketBlock('style-bar', 'Style bar — waits for the dressing pass', 'Material and detail ' +
  'complaints against a massing blockout. Correct observations, wrong stage.')}

<h2>4 &nbsp;Every plate, with its findings drawn on</h2>
<p class="blurb">Boxes are the judge's own bboxes: <span style="color:var(--naive)">orange = naive</span>,
<span style="color:var(--checklist)">blue = checklist</span>. This is the user's own annotated-screenshot
format, machine-made.</p>
${provTable}
${shotSection}

<h2>5 &nbsp;Limits — what this instrument structurally cannot see</h2>
<div class="limits">
<p>This tool looks at <b>pixels</b>. Seam-canon §10.3 (amended after the loop-stairs post-mortem) is the
reason that sentence needs a warning label:</p>
<p style="font-size:15px;margin:10px 0"><b>&ldquo;in frame&rdquo; &ne; &ldquo;visible&rdquo; &ne;
&ldquo;unobstructed ray&rdquo; &ne; <span style="color:var(--miss)">catches a foot</span></b></p>
<p>The loop-stairs flight was 72% visible, correctly framed, unoccluded and handsome — and unwalkable,
because <code>walkGround</code> keeps the highest surface in the step window and the neighbouring
flight's top tread covered its head. It caught a foot in 0 of 72 entries. <b>No critique of that plate
could ever have found it.</b> What this tool cannot see, and where each of those defects <em>is</em>
caught:</p>
<ul>
<li>whether a walk surface catches a foot &rarr; <code>tools/ls_nav_probe.mjs</code>, <code>seam_walk.mjs</code></li>
<li>whether a solid blocks the body &rarr; WALKLOCK / <code>boxSolid</code>, <code>seam_test.mjs</code></li>
<li>whether a naive reading of the frame actually <em>escapes</em> the shot &rarr; <code>tools/nav_eval.mjs</code> (it walks the answer)</li>
<li>whether a seam fires where it should &rarr; <code>seam_test.mjs</code>, <code>transition_test.mjs</code></li>
<li>true occlusion over a whole object, in metres &rarr; the bake ray-cast — the <em>only</em> visibility oracle — and <code>cine_visprobe.py</code></li>
<li>anything outside the shipped fixed frames &rarr; nothing automated sees it. The user plays with a free orbit camera; all five reference frames were taken from angles no plate holds.</li>
</ul>
<p>A finding here is a <b>perception</b>, and a perception is not a measurement. Geometry findings ship
with a <code>geometry_audit --region</code> command for exactly this reason: the next step is to measure
it, not to believe it.</p>
</div>

<div class="budget">Budget: ${run.budget.calls} judge calls
(${Object.entries(run.budget.byStage).map(([k, v]) => `${k} ${v}`).join(', ')}) ·
${run.budget.promptTok.toLocaleString()} prompt + ${run.budget.replyTok.toLocaleString()} reply tokens ·
${run.budget.errors} errors.${run.bboxAgreement && run.bboxAgreement.n ?
` Box check: ${run.bboxAgreement.hit}/${run.bboxAgreement.n} (${(run.bboxAgreement.frac * 100).toFixed(0)}%) of the
judge's checklist boxes contain the point the ray census projected — the drawn rectangles are
only as trustworthy as that number.` : ''} Raw replies in <code>raw/</code>, findings in
<code>findings.json</code>, discarded claims in <code>refuted.json</code>.</div>
</div>`;
  fs.writeFileSync(path.join(OUTDIR, 'index.html'), html);

  // ---- report.md: the same thing a terminal can read -----------------------
  const md = [`# Scene red-team — ${run.town} — run ${run.stamp}`, '',
    `judge \`${run.judge}\` (pinned) · ${run.shots.length} plates · ${run.modes.join(' + ')}` +
    (BLK ? ' · blockout mode' : ''), ''];
  if (anyMixed) {
    md.push('## 0. Which plates were judged this round', '',
      '| plate | critique | replies from | bake judged against | survivors |', '|---|---|---|---|---|',
      ...run.shots.map((s) => `| ${s.shot} | **${provOf(s).toUpperCase()}** | run-${s.replayOf || run.stamp} | ` +
        `${s.baked || '?'}${s.supersededBake ? ' — AGAINST-SUPERSEDED-BAKE (shipped is now ' +
        s.supersededBake + ')' : ''} | ${S.filter((f) => f.shot === s.shot).length} |`), '');
  }
  md.push('## 1. Calibration', '',
    cal ? (adj ? `**On the user's own five complaints, the judge found ${adjN} outright and ${adjW} ` +
      `weakly (${adjN + adjW}/5), and raised ${cal.extras.length} extra surviving findings.** ` +
      `(hand-adjudicated; the pre-registered keyword matcher scores ${cal.strict}/5 exact / ` +
      `${cal.lenient}/5 any-plate on the same run and over-credits.)`
      : `**On the user's own five complaints, the judge found ${cal.strict}/5 on the exact plate ` +
      `(${cal.lenient}/5 on any plate holding the same object) and raised ${cal.extras.length} ` +
      `other surviving findings.** (keyword matcher only, no hand adjudication)`)
      : '_not scored in this run_', '');
  if (cal) for (const r of cal.rows) {
    const a = AV(r.id);
    md.push(`- **${r.title}** — ${a ? a.verdict.toUpperCase() + ' (adjudicated: ' + a.why + ')'
      : r.foundStrict ? 'FOUND' : r.foundLenient ? 'found (other plate)' : 'MISSED'}`);
    for (const m of ['naive', 'checklist']) {
      const live = r.modes[m].hits.filter((h) => h.survived);
      md.push(`    - ${m}: ${live.length ? live.map((h) => `[${h.shot}] "${h.desc}"`).join(' | ') : 'miss'}`);
    }
  }
  md.push('', '## 2. Survivors by bucket', '');
  for (const b of ['known', 'new', 'style-bar'])
    md.push(`### ${b} (${byBucket(b).length})`, '',
      ...byBucket(b).map((f) => `- [${f.shot}/${f.mode}/${f.category}/sev${f.severity}] ${f.desc}` +
        (f.alsoOn && f.alsoOn.length ? ` _(also on ${f.alsoOn.map((a) => a.shot).join(', ')})_` : '') +
        (f.hint ? `\n      ${f.hint.cmd}` : '')), '');
  md.push('', `## 3. Budget`, '',
    `${run.budget.calls} calls, ${run.budget.promptTok} prompt + ${run.budget.replyTok} reply tokens, ` +
    `${run.budget.errors} errors.`, '',
    '## 4. Limits', '',
    '`"in frame" != "visible" != "unobstructed ray" != catches a foot` (seam-canon §10.3). This tool ' +
    'reads pixels only; the loop-stairs class of defect is invisible to it by construction. See ' +
    'index.html §5 for where each of those defects IS caught.');
  fs.writeFileSync(path.join(OUTDIR, 'report.md'), md.join('\n'));
}

// ------------------------------------------------------------------- MAIN ----
async function main() {
  // regenerate index.html / report.md from a finished run — used after a hand
  // adjudication is written beside it. No judge calls, no image work.
  if (flag('--rerender')) {
    const run = JSON.parse(fs.readFileSync(path.join(OUTDIR, 'findings.json'), 'utf8'));
    writeReport(run);
    console.log(`rerendered ${path.relative(ROOT, OUTDIR)}/index.html`);
    return;
  }
  const judge = JUDGES[JUDGE_NAME];
  if (!judge) { console.error('unknown judge: ' + JUDGE_NAME); process.exit(1); }
  let shotIds = CINE.cameras.map((c) => c.id).filter((id) => plateFiles(id).ok);
  if (REPLAY) shotIds = shotIds.filter((id) => replaySrc(id));
  if (CALIBRATE) {
    if (TOWN !== CALIBRATION.town) { console.error(`--calibrate is defined for ${CALIBRATION.town} only`); process.exit(1); }
    // --calibrate NARROWS to the gate's own 12 shots so the gate costs 12 plates and not 16.
    // It does NOT narrow when the caller has already named the set (--shots, or the shots a
    // --replay can serve): the score needs every calibration shot PRESENT, and extra shots
    // can only land in cal.extras, never in the five rows. So a town sweep that happens to
    // contain the gate set is scored on it rather than being forced into a second run.
    if (!ONLY.length && !REPLAY) shotIds = shotIds.filter((id) => CALIBRATION.shots.includes(id));
    // A HOLE IS REFUSED, NOT SCORED. A missing calibration shot deflates recall silently,
    // which is the one number this file exists to state honestly.
    const missing = CALIBRATION.shots.filter((id) => !shotIds.includes(id));
    if (missing.length) { console.error(`--calibrate cannot score: no plates for ${missing.join(', ')}`); process.exit(1); }
  }
  if (ONLY.length) shotIds = shotIds.filter((id) => ONLY.includes(id));
  const modes = MODE === 'both' ? ['naive', 'checklist'] : [MODE];
  console.log(`scene_redteam: ${TOWN}/${SCENE}, ${shotIds.length} plates, modes ${modes.join('+')}, N=${N}, ` +
    `judge ${judge.name}${IS_BLOCKOUT ? ', BLOCKOUT' : ''}${CALIBRATE ? ', CALIBRATION GATE' : ''}`);
  console.log(`  budget forecast: ${shotIds.length * ((modes.includes('naive') ? N + 1 : 0) + (modes.includes('checklist') ? 2 : 0))} calls`);
  if (DRY) { for (const id of shotIds) console.log('   ', id,
    modes.includes('checklist') ? checklistFor(id, camOf(id)).map((i) => i.id).join(' ') : ''); return; }

  fs.mkdirSync(path.join(OUTDIR, 'plates'), {recursive: true});
  fs.mkdirSync(path.join(OUTDIR, 'raw'), {recursive: true});
  // the judge's input (1344x768, the frame every other tool reasons in) and the report's
  // display copy of the same image
  const inputs = {};
  for (const id of shotIds) {
    const cam = camOf(id), p = path.join(OUTDIR, 'inputs', id + '.png');
    let stand = null;
    if (WITH_CHAR) { const S = (ROUTES.shots || {})[id] || {};
      const e = (S.entries || []).find((x) => x.kind === 'seam') || (S.entries || [])[0];
      if (e) stand = r2m(e.at); }
    const ci = buildInput(cam, p, stand);
    writeDisplay(p, path.join(OUTDIR, 'plates', id + '.png'));
    inputs[id] = {path: p, char: ci};
  }
  const results = await pool(shotIds, CONC, async (id, k) => {
    const src = REPLAY ? replaySrc(id) : null;
    const J = src ? replayJudge(JSON.parse(fs.readFileSync(
      path.join(RTDIR, 'run-' + src, 'raw', id + '.json'), 'utf8'))) : judge;
    const r = await runShot(J, id, inputs[id].path, modes.includes('naive'), modes.includes('checklist'));
    r.replayOf = src;
    process.stdout.write(`\r  ${k + 1}/${shotIds.length} ${id} — ${r.findings.length} raw     `);
    fs.writeFileSync(path.join(OUTDIR, 'raw', id + '.json'), JSON.stringify(r.raw, null, 1));
    return r;
  });
  console.log('');

  // WHICH REPLIES ARE THIS ROUND'S. Mechanical, not asserted: of the runs --replay was
  // pointed at, the one generated last is the round just judged; everything sourced from an
  // older run is a replay of an older critique. No flag to get wrong.
  const srcGen = Object.fromEntries(REPLAY_LIST.map((st) => { try {
    return [st, JSON.parse(fs.readFileSync(path.join(RTDIR, 'run-' + st, 'findings.json'), 'utf8')).generated];
  } catch { return [st, '']; } }));
  const freshFrom = REPLAY_LIST.length > 1
    ? REPLAY_LIST.slice().sort((a, b) => (srcGen[a] < srcGen[b] ? 1 : -1))[0] : null;
  // AND WHICH PLATES WENT STALE UNDER US. When --plates pins a bake, the shipped scene may
  // already have moved past it; the tool says so per shot instead of letting a day-old
  // picture pass as current. This is the "against-superseded-bake" mark.
  let LIVE_BAKED = {};
  if (path.resolve(PLATES) !== path.resolve(SCENE_DIR)) { try {
    LIVE_BAKED = Object.fromEntries(JSON.parse(fs.readFileSync(path.join(SCENE_DIR, 'cine.json'), 'utf8'))
      .cameras.map((c) => [c.id, c.baked || null]));
  } catch { /* no shipped cine to compare against */ } }

  const all = results.flatMap((r) => r.findings);
  const survivors0 = all.filter((f) => f.verify && f.verify.verdict === 'upheld');
  const refuted = all.filter((f) => !f.verify || f.verify.verdict !== 'upheld');
  const survivors = dedup(survivors0).map((f) => ({...f, triage: triage(f)}));

  const run = {
    version: 1, town: TOWN, scene: SCENE, stamp: STAMP, generated: new Date().toISOString(),
    generator: 'tools/scene_redteam.mjs',
    judge: REPLAY ? `${judge.name} (replayed from ${REPLAY_LIST.map((s) => 'run-' + s).join(' + ')})` : judge.name,
    model: JUDGE_NAME === 'gemini' ? MODEL : null, replayOf: REPLAY,
    temperature: TEMP, blockout: IS_BLOCKOUT, modes, n: N, freshFrom, replaySources: srcGen,
    plates: path.relative(ROOT, PLATES), cine: path.relative(ROOT, CINE_PATH), withChar: WITH_CHAR, frame: FRAME,
    // WHICH BAKE WAS CRITICISED. A critique of a plate is worthless a day later if nobody
    // can say which plate. Learned the hard way on the very first run: the `gate` plate
    // was re-baked by the art pass three minutes after this tool read it, so the canopy
    // finding is about a picture that no longer exists. Every shot carries its own bake
    // stamp from cine.json and the mtime of the file actually read.
    shots: results.map((r) => ({shot: r.shot, name: (AUTH[r.shot] || {}).name || r.shot,
                                replayOf: r.replayOf || null,
                                baked: (CAMBY[r.shot] || {}).baked || null,
                                supersededBake: (LIVE_BAKED[r.shot] &&
                                  LIVE_BAKED[r.shot] !== ((CAMBY[r.shot] || {}).baked || null))
                                  ? LIVE_BAKED[r.shot] : null,
                                plateMtime: (() => { try {
                                  return fs.statSync(plateFiles(r.shot).bg).mtime.toISOString();
                                } catch { return null; } })(),
                                items: r.items.length, char: inputs[r.shot].char,
                                checklist: r.items.map((i) => ({id: i.id, src: i.src, what: i.what,
                                  census: i.census, judged: i.judged || null, suppressed: i.suppressed || null}))})),
    raw: all.length, survivors, refuted, budget: BUDGET,
    bboxAgreement: null,
    calibration: CALIBRATE ? scoreCalibration(survivors, refuted) : null,
  };

  // the user's own reference frames, copied in so section 1 is self-contained
  if (CALIBRATE) {
    fs.mkdirSync(path.join(OUTDIR, 'refs'), {recursive: true});
    for (const r of new Set(CALIBRATION.complaints.map((c) => c.ref))) {
      const src = path.join(ROOT, 'docs/qa/refs', r);
      if (fs.existsSync(src)) {
        const im = readPng(src), W = 700, sc = im.width / W, H = Math.round(im.height / sc);
        const out = new PNG({width: W, height: H});
        for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
          const i = (Math.min(im.height - 1, Math.round(y * sc)) * im.width +
                     Math.min(im.width - 1, Math.round(x * sc))) * 4, o = (y * W + x) * 4;
          out.data[o] = im.data[i]; out.data[o + 1] = im.data[i + 1];
          out.data[o + 2] = im.data[i + 2]; out.data[o + 3] = 255;
        }
        fs.writeFileSync(path.join(OUTDIR, 'refs', r), PNG.sync.write(out, {deflateLevel: 9}));
      }
    }
  }
  run.bboxAgreement = bboxAgreement(run.shots);
  fs.writeFileSync(path.join(OUTDIR, 'findings.json'), JSON.stringify(run, null, 1));
  fs.writeFileSync(path.join(OUTDIR, 'refuted.json'), JSON.stringify(refuted, null, 1));
  writeReport(run);
  if (!flag('--keep-inputs')) fs.rmSync(path.join(OUTDIR, 'inputs'), {recursive: true, force: true});

  // ------------------------------------------------------------- scorecard --
  console.log(`\nSCENE RED-TEAM — ${TOWN}  (judge ${judge.name}, ${modes.join('+')})`);
  console.log(`raw findings ${all.length}   refuted ${refuted.length}   survivors ${survivors.length}` +
              `   (deduped from ${survivors0.length})`);
  for (const b of ['known', 'new', 'style-bar'])
    console.log(`  ${b.padEnd(10)} ${survivors.filter((f) => f.triage.bucket === b).length}`);
  if (run.calibration) {
    const c = run.calibration;
    console.log('\nCALIBRATION GATE');
    for (const r of c.rows)
      console.log(`  ${(r.foundStrict ? 'HIT ' : r.foundLenient ? 'hit*' : 'MISS')}  ${r.id.padEnd(18)}` +
        `  naive ${r.modes.naive.survivingLenient ? 'y' : '-'}  checklist ${r.modes.checklist.survivingLenient ? 'y' : '-'}`);
    console.log(`\n  VERDICT: on the user's own five complaints, the judge found ${c.strict}/5 on the ` +
      `exact plate\n           (${c.lenient}/5 on any plate holding the object) and raised ` +
      `${c.extras.length} extra findings.`);
    if (c.lenient < 3) console.log('  RECALL BELOW 3/5 — the approach underperforms. STOP and ask for guidance.');
  }
  if (run.bboxAgreement && run.bboxAgreement.n)
    console.log(`bbox check: ${run.bboxAgreement.hit}/${run.bboxAgreement.n} judged boxes contain the census point`);
  console.log(`\nbudget: ${BUDGET.calls} calls, ${BUDGET.promptTok} prompt + ${BUDGET.replyTok} reply tokens, ` +
              `${BUDGET.errors} errors`);
  console.log(`report: ${path.relative(ROOT, OUTDIR)}/index.html`);
}

main().catch((e) => { console.error(e); process.exit(1); });
