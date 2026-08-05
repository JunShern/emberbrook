// nav_eval.mjs — THE PERCEPTUAL NAVIGABILITY EVAL.
//
//   node tools/nav_eval.mjs                        # the whole town, N=5, gemini judge
//   node tools/nav_eval.mjs --shots gate,crossing  # a subset
//   node tools/nav_eval.mjs --judge oracle         # the harness's own self-check (no API)
//   node tools/nav_eval.mjs --plates <dir> --cine <cine.json> --tag old   # calibration
//   node tools/nav_eval.mjs --n 5 --temp 1 --conc 4 --stamp <name>
//   node tools/nav_eval.mjs --compare <runA> <runB>   # the eval-of-the-eval
//
// Then open the viewer:
//   python3 -m http.server 8009 --directory docs/qa   (or the repo server)
//   http://localhost:8009/naveval/viewer.html?run=<stamp>
//
// ---------------------------------------------------------------------------
// WHY THIS EXISTS. The town has two verification pillars and they measure the same
// kind of thing twice. `seam_test`/`seam_walk` prove the GEOMETRY of the cuts (the walk
// is sound); `shot_probe` proves a route is VISIBLE in the baked plate (the pixels
// exist). Neither answers the user's actual complaint, which was never geometric:
//
//   "it is hard to figure out where the character needs to walk."
//
// §9.3 of the seam canon names four causes of "invisible" — off frame, occluded, too
// small, not there. This tool adds the FIFTH: **perceptually misleading** — every
// pixel present, correctly framed, big enough, and the player still reads the wrong
// way on. That failure is invisible to every geometric gate by construction, because
// the geometry is fine. The only instrument that can see it is a first-time player.
//
// SO WE HIRE ONE, 80 TIMES A RUN. A context-free vision model is shown ONE composited
// image — the baked plate with the character standing at an entry spawn — and nothing
// else: no map, no town name, no route data, no history. It answers where it would
// walk, in image coordinates. Those waypoints are unprojected through THAT SHOT'S OWN
// baked depth map into world points, and the real WALKLOCK stepping rules are run
// along them. If the naive reading of the picture escapes the scene, the shot is
// legible. If it walks into a wall, the shot is not — and the number says so before a
// player has to. THE WALKER ONLY EVER AIMS AT WHAT THE PICTURE SHOWED: a waypoint on an
// occluded pixel is walked to the last ground visible along that line of sight, never
// to the floor hiding behind the occluder (see UNPROJECT, fixed 2026-08-01).
//
// THE METRIC IS ONLY WORTH ITS CALIBRATION. `--plates` points the whole pipeline at a
// different bake, which is how the eval is evaluated: run it against plates whose
// legibility failures were MEASURED (the pre-surgery gate/shelf-west, stair 12%/26%
// visible) and against the fixed plates, and report the separation. A metric that does
// not separate known-bad from known-good is not a metric, and this file says so out
// loud rather than being tuned until it flatters the bake.
//
// FIDELITY, STATED. The walk is play3d.html's own model, ported: WALKLOCK
// (`walkGround` — only walk_ meshes catch the foot, and there is no walking off an
// edge), the same STEP_UP/STEP_DN/0.18-crack tolerances, the same SPD, the same seam
// band test + arm/disarm + 20-tick sgCorrect from `seam_walk.mjs` against the SHIPPED
// scenegraph.json. What is NOT ported: prop body-box blocking (`boxSolid`), which
// needs the 52 MB collide bundle's triangles. Under WALKLOCK the walk network is the
// dominant constraint and props sit beside it, so the omission makes the walker
// slightly OPTIMISTIC. In the other direction, the walker steers LOCALLY (a bounded fan
// off the bearing to the next waypoint) and cannot back up out of a pocket: measured on
// the ground truth, that costs it two of sixteen shots. Both errors are bounded and both
// are measured every run by `--judge oracle-world`, which is why that mode exists.
//
// THE JUDGE IS A SEAM. `--judge <name>`; a judge is {name, ask(imagePath, prompt)}.
//   gemini  (default)  gemini-3.6-flash, multimodal, temperature/N configurable. The
//                      model is PINNED, not an alias: `gemini-flash-latest` would move
//                      under the metric and make two runs incomparable.
//   oracle             replays the GROUND-TRUTH route THROUGH the image: projected to
//                      waypoints, unprojected again, then walked. The end-to-end check.
//   oracle-world       the same route handed straight to the walker. This one isolates
//                      the WALKER: if it is not ~1.0 the bug is in this file and no
//                      plate is to blame. RUN IT FIRST, ALWAYS.
//   stub               a fixed dumb answer (walk to the bottom centre). No API.
// A Claude-subagent judge slots in at the same seam with no other change.
//
// SEE ALSO docs/plans/seam-canon.md §10 (the perceptual gate), and the run artifacts
// under docs/qa/naveval/run-<stamp>/.
import fs from 'fs';
import path from 'path';
import {PNG} from 'pngjs';
import {loadCine, camBasis, project, charPx, m2r, r2m, PUB, ROOT, rd} from './cine_regions.mjs';
import {loadGlb} from './glb_read.mjs';

// ------------------------------------------------------------------ args ----
const ARGS = process.argv.slice(2);
const flag = (n) => ARGS.includes(n);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const TOWN = opt('--town', 'dellhollow');
const N = +opt('--n', 5);
const TEMP = +opt('--temp', 1);
const CONC = +opt('--conc', 4);
const JUDGE_NAME = opt('--judge', 'gemini');
const MODEL = opt('--model', 'gemini-3.6-flash');
const ONLY = (opt('--shots', '') || '').split(',').filter(Boolean);
const ENTRIES_MODE = opt('--entries', 'primary');      // primary | all
const TAG = opt('--tag', null);
const DRY = flag('--dry');

// ------------------------------------------------------------------ data ----
const C = loadCine(`townmap/${TOWN}.map.json`, `townmap/${TOWN}.cameras.json`);
const SCENE = C.camFile.sceneKey;
const SCENE_DIR = path.join(PUB, 'assets/scenes', SCENE);
const CINE_PATH = opt('--cine', path.join(SCENE_DIR, 'cine.json'));
const PLATES = opt('--plates', SCENE_DIR);             // dir holding cameras/<id>/{bg,depth}.png
const CINE = JSON.parse(fs.readFileSync(CINE_PATH, 'utf8'));
const CAMBY = Object.fromEntries(CINE.cameras.map((c) => [c.id, c]));
const SOLVED = rd(`townmap/${TOWN}.cameras.solved.json`);
const SOLVEDBY = Object.fromEntries(SOLVED.cameras.map((c) => [c.id, c]));
const ROUTES = rd(`townmap/${TOWN}.routes.json`);
const SG = rd('world/scenegraph.json');
const SCENE_KEY = C.map.playSceneKey || SCENE;
const NODE = SG.nodes[SCENE_KEY];
const FRAME = ROUTES.frame || [1344, 768];
const ASPECT = C.D.aspect, CHARH = C.D.charH;
const POSE = path.join(PUB, 'assets/characters/vesper/pose.png');

// runtime movement constants — play3d.html:297-300, quoted not guessed
const STEP_UP = 0.63, STEP_DN = 0.8, SPD = 0.075;
const D = SG.defaults || {};
const GRACE = D.correctionGrace ?? 20, CPAD = D.correctionPad ?? 0.6,
      CVTOL = D.correctionVTol ?? 1.2, CREACH = D.correctionReach ?? 12;

const STAMP = opt('--stamp', new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '')
  .replace('T', '-') + (TAG ? '-' + TAG : ''));
const OUTDIR = path.join(ROOT, 'docs/qa/naveval', 'run-' + STAMP);

// ------------------------------------------------------- camera + geometry ---
// The plate's own camera is cine.json's record: it is what cine_bake.py rendered
// with, and it carries the depth encoding's near/far. cameras.solved.json is the
// INTENT; when they disagree the plate is stale and every number below is measured
// against art that no longer matches the runtime, so the drift is reported per shot
// rather than silently averaged away.
function camOf(id) {
  const c = CAMBY[id];
  if (!c) return null;
  const s = SOLVEDBY[id];
  const drift = s ? Math.max(
    Math.hypot(c.pos[0] - s.pos[0], c.pos[1] - s.pos[1], c.pos[2] - s.pos[2]),
    Math.hypot(c.aim[0] - s.aim[0], c.aim[1] - s.aim[1], c.aim[2] - s.aim[2])) : null;
  return {id, pos: c.pos, aim: c.aim, fov: c.fov, depth: c.depth, art: c.art,
          drift: drift === null ? null : +drift.toFixed(3)};
}
// map point -> normalised image coords [0..1], plus px and view depth
function toImg(cam, mp) {
  const s = project(cam.pos, cam.aim, cam.fov, ASPECT, mp);
  if (s.behind) return {behind: true, u: null, v: null, z: s.z};
  const u = s.sx * 0.5 + 0.5, v = 0.5 - s.sy * 0.5;
  return {behind: false, u, v, z: s.z, on: u >= 0 && u <= 1 && v >= 0 && v <= 1,
          px: [u * FRAME[0], v * FRAME[1]],
          charPx: charPx(cam.fov, s.z, CHARH, FRAME[1])};
}
const rtToImg = (cam, rp) => toImg(cam, r2m(rp));
// runtime point -> [u, v] or null when it is behind the camera. Used everywhere the
// viewer needs to draw a world thing on the input image.
const uv1 = (cam, rp) => { const s = rtToImg(cam, rp);
  return s.behind ? null : [+s.u.toFixed(4), +s.v.toFixed(4)]; };
const uvChain = (cam, pts) => pts.map((p) => uv1(cam, p)).filter(Boolean);
// normalised image coords -> a unit-ish ray whose dot with forward is 1
function rayOf(cam, u, v) {
  const {f, r, up} = (() => { const b = camBasis(cam.pos, cam.aim); return {f: b.f, r: b.r, up: b.u}; })();
  const ty = Math.tan(cam.fov * Math.PI / 180 / 2), tx = ty * ASPECT;
  const sx = u * 2 - 1, sy = 1 - v * 2;
  return [f[0] + r[0] * sx * tx + up[0] * sy * ty,
          f[1] + r[1] * sx * tx + up[1] * sy * ty,
          f[2] + r[2] * sx * tx + up[2] * sy * ty];
}

// ------------------------------------------------------------ depth plates ---
const _png = new Map();
function readPng(p) {
  if (!_png.has(p)) _png.set(p, PNG.sync.read(fs.readFileSync(p)));
  return _png.get(p);
}
function plateFiles(id) {
  const c = CAMBY[id];
  const bg = path.join(PLATES, c && c.art ? c.art.bg : `cameras/${id}/bg.png`);
  const dp = path.join(PLATES, c && c.art ? c.art.depth : `cameras/${id}/depth.png`);
  return {bg, depth: dp, ok: fs.existsSync(bg) && fs.existsSync(dp)};
}
// view-space z at a normalised image coord, decoded exactly as play3d.html's shader
// does (line 102): d = near + (far-near) * dot(rgb*255, [65536,256,1]) / 16777215.
function depthAt(cam, u, v) {
  const {depth: dpath} = plateFiles(cam.id);
  const img = readPng(dpath);
  const x = Math.min(img.width - 1, Math.max(0, Math.round(u * img.width)));
  const y = Math.min(img.height - 1, Math.max(0, Math.round(v * img.height)));
  const i = (y * img.width + x) * 4;
  const raw = (img.data[i] * 65536 + img.data[i + 1] * 256 + img.data[i + 2]) / 16777215;
  const {near, far} = cam.depth;
  return {z: near + (far - near) * raw, raw};
}

// -------------------------------------------------------- the walk network ---
// G.tops() is O(all walk triangles) per call and the walker makes ~15 000 of them per
// trial, so the triangles are bucketed into a 2 m xz grid once. Same answer, ~40x.
// The bundle is the TOWN's own stated walk scene, by the house rule (seam_test.mjs):
// the map names its explorable bundle, and a town without one walks its cine bundle.
const GLB = loadGlb(path.join(PUB, 'assets/scenes',
  (C.map.walkSceneKey || C.camFile.sceneKey), 'scene.glb'));
const WALK_RE = /^walk/i;
const CELL = 2.0;
const GRID = new Map();
{
  const key = (i, j) => i + ',' + j;
  for (const T of GLB.tris(WALK_RE)) {
    const [A, B, Cc] = T;
    const ux = B[0] - A[0], uy = B[1] - A[1], uz = B[2] - A[2];
    const vx = Cc[0] - A[0], vy = Cc[1] - A[1], vz = Cc[2] - A[2];
    const ny = uz * vx - ux * vz;
    const nl = Math.hypot(uy * vz - uz * vy, ny, ux * vy - uy * vx) || 1e-12;
    if (Math.abs(ny / nl) <= 0.5) continue;                       // not standable
    const i0 = Math.floor(Math.min(A[0], B[0], Cc[0]) / CELL), i1 = Math.floor(Math.max(A[0], B[0], Cc[0]) / CELL);
    const j0 = Math.floor(Math.min(A[2], B[2], Cc[2]) / CELL), j1 = Math.floor(Math.max(A[2], B[2], Cc[2]) / CELL);
    for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
      const k = key(i, j); let a = GRID.get(k); if (!a) GRID.set(k, a = []); a.push(T);
    }
  }
}
function topsWalk(x, z) {
  const a = GRID.get(Math.floor(x / CELL) + ',' + Math.floor(z / CELL));
  if (!a) return [];
  const ys = [];
  for (const [A, B, Cc] of a) {
    const d = (B[2] - Cc[2]) * (A[0] - Cc[0]) + (Cc[0] - B[0]) * (A[2] - Cc[2]);
    if (Math.abs(d) < 1e-12) continue;
    const l1 = ((B[2] - Cc[2]) * (x - Cc[0]) + (Cc[0] - B[0]) * (z - Cc[2])) / d;
    const l2 = ((Cc[2] - A[2]) * (x - Cc[0]) + (A[0] - Cc[0]) * (z - Cc[2])) / d;
    const l3 = 1 - l1 - l2;
    if (l1 < -1e-6 || l2 < -1e-6 || l3 < -1e-6) continue;
    ys.push(l1 * A[1] + l2 * B[1] + l3 * Cc[1]);
  }
  return ys.sort((a2, b) => b - a2);
}
// play3d.html walkGround(): the highest walk surface inside the step window, with the
// same four 0.18 m plank-crack retries. Returns null = there is no floor here.
function walkGround(x, z, fy) {
  const w = (xx, zz) => {
    const hi = fy + STEP_UP + 0.1, lo = fy - STEP_DN - 0.1;
    for (const y of topsWalk(xx, zz)) if (y <= hi && y >= lo) return y;
    return null;
  };
  let g = w(x, z); if (g != null) return g;
  for (const [ox, oz] of [[0.18, 0], [-0.18, 0], [0, 0.18], [0, -0.18]]) {
    g = w(x + ox, z + oz); if (g != null) return g;
  }
  return null;
}
// is this world point standing on the walk network at all (any height near it)?
function onWalkNet(p, vtol = 1.0, rad = 0.6) {
  for (const [ox, oz] of [[0, 0], [rad, 0], [-rad, 0], [0, rad], [0, -rad]])
    for (const y of topsWalk(p[0] + ox, p[2] + oz)) if (Math.abs(y - p[1]) <= vtol) return true;
  return false;
}
// WHERE ON THE FLOOR IS THIS PIXEL POINTING? March the camera ray until it goes under
// the walk network. This is what a waypoint MEANS — "the place on the ground I am
// walking to" — and it is deliberately a different question from what the depth plate
// says is drawn at that pixel. The pair of answers is the whole diagnosis:
//   ray hits the network, and the plate agrees   -> a clean, readable waypoint
//   ray hits the network, plate is much nearer   -> the floor is THERE but HIDDEN; the
//                                                   player is reading through an occluder
//   ray misses the network                       -> off-route perception: a wall, a
//                                                   roof, the river, the sky
function rayWalkHit(cam, dir, zmax) {
  let prev = null;
  for (let t = 1.0; t <= zmax; t += 0.2) {
    const mp = [cam.pos[0] + dir[0] * t, cam.pos[1] + dir[1] * t, cam.pos[2] + dir[2] * t];
    const rt = m2r(mp);
    const ys = topsWalk(rt[0], rt[2]);
    const top = ys.length ? ys[0] : null;
    const under = top != null && rt[1] <= top + 0.05;
    if (under && prev && !prev.under) {
      let a = prev.t, b = t;                          // bisect the crossing
      for (let i = 0; i < 14; i++) {
        const m = (a + b) / 2;
        const q = m2r([cam.pos[0] + dir[0] * m, cam.pos[1] + dir[1] * m, cam.pos[2] + dir[2] * m]);
        const y2 = topsWalk(q[0], q[2]);
        if (y2.length && q[1] <= y2[0] + 0.05) b = m; else a = m;
      }
      const q = m2r([cam.pos[0] + dir[0] * b, cam.pos[1] + dir[1] * b, cam.pos[2] + dir[2] * b]);
      const y2 = topsWalk(q[0], q[2]);
      return {z: b, rt: [q[0], y2.length ? y2[0] : q[1], q[2]]};
    }
    prev = {t, under};
  }
  return null;
}
// The walk surface at or under a world point, or null when there is none — a roofline,
// a hull, the far bank. Used by UNPROJECT to answer one question: IS THE SURFACE THIS
// PIXEL DRAWS ITSELF THE GROUND? A camera ray's visible span ends at the surface the
// plate draws; everything past that is hidden. If what is drawn stands clear above the
// walk network it is an occluder, and if it is the walk network there is nothing hiding
// anything and the sight line is clean.
function groundUnder(rt) {
  for (const y of topsWalk(rt[0], rt[2])) if (y <= rt[1] + 0.05) return [rt[0], y, rt[2]];
  return null;
}

// --------------------------------------------------------------- the seams ---
const REG = NODE.shots;
const EDGES = SG.edges.filter((e) => e.from === SCENE_KEY && e.to === SCENE_KEY && e.band);
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
    const dd = Math.sqrt(dx * dx + dz * dz + (P[1] - b[4]) ** 2);
    if (dd < nd) { nd = dd; nid = r.id; } }
  return nd > CREACH ? {own: false, other: null} : {own: nid === cam, other: nid};
}

// ------------------------------------------------------------ THE WALKER -----
// One trial's execution. Steps toward each waypoint in turn with play3d.html's own
// walkStep() candidate order ((dx,dz) then (dx,0) then (0,dz)) under WALKLOCK, firing
// the shipped seam bands and sgCorrect on the way. A leg is ABANDONED when the walker
// stops making ground — that is the "stuck" the player feels as "I can't get there".
const REFUSE_TICKS = 60;         // 4.5 m of intent that WALKLOCK refuses outright
const WINDOW = 220, WINDOW_MIN = 0.4;  // 16 m of walking must buy 0.4 m toward the goal
const LEG_TICKS = 900;           // ~67 m: nothing in one shot is that far
function walkChain(startShot, spawn, targets) {
  let P = spawn.slice();
  const y0 = walkGround(P[0], P[2], P[1]); if (y0 != null) P[1] = y0;
  let cam = startShot;
  const armed = new Map(), trace = [P.slice()], ev = [];
  let corrCount = 0, cl = null, ct = 0;
  const tick = () => {                                    // one runtime frame of gating
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
      ev.push({k: 'cut', from: cam, to: fire.e.cam.key, of: fire.e.of, edge: fire.e.id,
               at: P.map((v) => +v.toFixed(2))});
      cam = fire.e.cam.key; P = fire.e.spawn.slice();
      const y = walkGround(P[0], P[2], P[1]); if (y != null) P[1] = y;
      armed.clear(); ct = 0; cl = null; return true;
    }
    const r = regionsFor(P, cam);
    if (r.own || !r.other) { ct = 0; cl = null; return false; }
    if (cl !== r.other) { cl = r.other; ct = 0; }
    if (++ct < GRACE) return false;
    ct = 0; corrCount++;
    ev.push({k: 'correction', from: cam, to: r.other, at: P.map((v) => +v.toFixed(2))});
    cam = r.other; armed.clear(); return false;
  };
  const raw = (dx, dz) => {                               // play3d.html walkStep, WALKLOCK
    for (const [mx, mz] of [[dx, dz], [dx, 0], [0, dz]]) {
      if (!mx && !mz) continue;
      const nx = P[0] + mx, nz = P[2] + mz;
      const g = walkGround(nx, nz, P[1]); if (g == null) continue;
      P[0] = nx; P[2] = nz; P[1] = g; return true;
    }
    return false;                                          // WALKLOCK: the step is refused
  };
  // STEERING. A waypoint is a PLACE, not a joystick heading, and the question the eval
  // asks is whether the player knows WHERE to go — not whether they can drive a straight
  // line down a switchback. So each tick the walker fans out either side of the bearing
  // to the waypoint and takes the candidate that gets it CLOSEST TO THE WAYPOINT IN 3D,
  // which is what somebody looking at the screen does.
  //
  // The 3D part is load-bearing and was learned the hard way. Two of Dellhollow's
  // flights leave the shelf-homes pad heading east within a metre of each other, one
  // dropping to the market and one to the quay. Preferring the straightest walkable
  // candidate takes the wrong one every time (walkGround keeps the HIGHEST surface in
  // the step window, exactly as play3d does); preferring the candidate that closes the
  // distance to a waypoint that is three metres LOWER picks the right flight without
  // being told which one it is. The fan is bounded at 90 degrees: a waypoint you can
  // only reach by walking away from it was not a legible waypoint.
  const FAN = [0, 15, -15, 30, -30, 45, -45, 60, -60, 75, -75, 90, -90]
    .map((d) => d * Math.PI / 180);
  const dist3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const step = (T) => {
    const base = Math.atan2(T[2] - P[2], T[0] - P[0]);
    let best = null;
    for (const f of FAN) {
      const a = base + f;
      const nx = P[0] + Math.cos(a) * SPD, nz = P[2] + Math.sin(a) * SPD;
      const g = walkGround(nx, nz, P[1]);
      if (g == null) continue;
      const d = dist3([nx, g, nz], T) + Math.abs(f) * 0.02;   // tie-break toward straight
      if (!best || d < best.d) best = {d, nx, nz, g};
    }
    if (!best) return false;                                  // WALKLOCK refuses every way
    P[0] = best.nx; P[1] = best.g; P[2] = best.nz;
    return true;
  };
  tick();
  const legs = [];
  let cutFired = false;
  for (let li = 0; li < targets.length && !cutFired; li++) {
    const T = targets[li];
    let ticks = 0, refused = 0, reached = false, why = null;
    let best = dist3(P, T), bestTick = 0;
    while (ticks++ < LEG_TICKS) {
      const L = dist3(P, T);                                  // 3D: a waypoint two metres
      if (L < 0.6) { reached = true; break; }                 // BELOW you is not reached
      const ok = step(T);
      // A CUT ENDS THE TRIAL. The remaining waypoints were read off an image that is no
      // longer on screen, so executing them would be scoring an answer to a question
      // nobody asked. "Did the naive route leave this shot" is the whole question.
      if (tick()) { cutFired = true; why = 'cut'; break; }
      trace.push(P.slice());
      if (ok) refused = 0; else if (++refused > REFUSE_TICKS) { why = 'refused'; break; }
      // progress is measured against the GOAL, not against the ground: a walker sliding
      // back and forth along a rail is moving and is not getting anywhere.
      if (L < best - WINDOW_MIN) { best = L; bestTick = ticks; }
      else if (ticks - bestTick > WINDOW) { why = 'no-progress'; break; }
      if (ev.length > 40) { why = 'oscillates'; break; }
    }
    if (!reached && !why) why = 'timeout';
    legs.push({i: li, target: T.map((v) => +v.toFixed(2)), reached,
               stuck: !reached && why !== 'cut', why, ticks,
               endAt: P.map((v) => +v.toFixed(2)), endCam: cam,
               distLeft: +dist3(P, T).toFixed(2)});
    if (ev.length > 40) break;
  }
  if (!cutFired) for (let i = 0; i < 60; i++) if (tick()) break;   // stand still one second
  return {endCam: cam, endAt: P.map((v) => +v.toFixed(2)), events: ev, legs,
          corrections: corrCount,
          trace: trace.filter((_, i) => i % 4 === 0).map((p) => p.map((v) => +v.toFixed(2)))};
}

// ------------------------------------------------ ground truth for a shot ----
function gtOf(shotId) {
  const S = ROUTES.shots[shotId] || {entries: [], exits: [], routes: []};
  return S;
}
// ONE entry per shot by default, and which one is a design choice worth stating: the
// eval asks "a player who has just arrived here — where do they go?", so the entry has
// to be an ARRIVAL a player really makes. For the town's entry shot that is the portal
// in from the overworld (the literal first thing anyone ever sees of Dellhollow); for
// every other shot it is the seam a player walks in through. `--entries all` runs the
// cross product when a shot needs to be judged from every door.
function primaryEntry(S, shotId) {
  const isEntryShot = (CAMBY[shotId] || {}).entry;
  if (isEntryShot) { const p = S.entries.find((e) => e.kind === 'portal'); if (p) return p; }
  return S.entries.find((e) => e.kind === 'seam') || S.entries.find((e) => e.kind === 'portal')
      || S.entries.find((e) => e.kind === 'spawn') || S.entries[0] || null;
}

// The ground-truth answer to the eval's own question, as a waypoint chain: from this
// entry, along the route that connects to the nearest ONWARD exit, and two metres past
// it in the direction the path runs (an exit is a band you cross, not a spot you stand
// on). This is the oracle's reply and it is also what the viewer draws as GT.
// A shot's routes are a GRAPH, not a line — the weave has seven of them — so the GT
// path is a shortest path over the union of every route polyline, hopping between
// routes wherever two of them pass within a stride. Taking the single route that
// happens to name the exit gets the weave wrong by thirteen metres.
const _gtGraph = new Map();
function routeGraph(shotId) {
  if (_gtGraph.has(shotId)) return _gtGraph.get(shotId);
  const S = gtOf(shotId);
  const V = [], adj = [];
  const add = (p) => { V.push(p); adj.push([]); return V.length - 1; };
  const link = (a, b) => { const w = Math.hypot(V[a][0] - V[b][0], V[a][1] - V[b][1], V[a][2] - V[b][2]);
    adj[a].push([b, w]); adj[b].push([a, w]); };
  for (const r of (S.routes || [])) {
    if (r.blocked) continue;                       // a way on that is not a way on
    let prev = null;
    for (const p of r.points) { const i = add(p); if (prev !== null) link(prev, i); prev = i; }
  }
  for (let i = 0; i < V.length; i++) for (let j = i + 1; j < V.length; j++) {
    const d = Math.hypot(V[i][0] - V[j][0], V[i][2] - V[j][2]);
    if (d <= 1.5 && Math.abs(V[i][1] - V[j][1]) <= 1.5 && !adj[i].some((e) => e[0] === j)) link(i, j);
  }
  const g = {V, adj};
  _gtGraph.set(shotId, g);
  return g;
}
function shortestPath(g, si, ti) {
  const n = g.V.length, dist = new Array(n).fill(Infinity), prev = new Array(n).fill(-1);
  dist[si] = 0;
  const seen = new Array(n).fill(false);
  for (;;) {
    let u = -1, bd = Infinity;
    for (let i = 0; i < n; i++) if (!seen[i] && dist[i] < bd) { bd = dist[i]; u = i; }
    if (u < 0 || u === ti) break;
    seen[u] = true;
    for (const [v, w] of g.adj[u]) if (dist[u] + w < dist[v]) { dist[v] = dist[u] + w; prev[v] = u; }
  }
  if (!Number.isFinite(dist[ti])) return null;
  const out = []; for (let k = ti; k >= 0; k = prev[k]) out.unshift(g.V[k]);
  return {pts: out, len: dist[ti]};
}
const nearestV = (g, p) => { let bi = -1, bd = Infinity;
  g.V.forEach((q, i) => { const d = Math.hypot(q[0] - p[0], q[2] - p[2]) + Math.abs(q[1] - p[1]) * 0.5;
    if (d < bd) { bd = d; bi = i; } }); return bi; };

function gtChain(c) {
  const S = gtOf(c.shot), start = c.entry.at;
  // an EXIT ONWARD is a camera cut to another shot. Doors into interiors and the
  // overworld portal are exits, but "went into the inn" is not "found the way through
  // this scene" — they count only where the shot has no seam to leave by (the gate).
  const all = (S.exits || []).filter((x) => x.to !== (c.entry.from || null));
  let onward = all.filter((x) => x.toKind === 'shot');
  if (!onward.length) onward = all.length ? all : (S.exits || []).slice();
  if (!onward.length) return [];
  const g = routeGraph(c.shot);
  if (!g.V.length) return [start];
  const si = nearestV(g, start);
  let best = null;
  for (const e of onward) {
    const p = shortestPath(g, si, nearestV(g, e.at));
    if (p && (!best || p.len < best.len)) best = {len: p.len, pts: p.pts, exit: e};
  }
  if (!best) return [start];
  const pts = best.pts.slice();
  pts.push(best.exit.at);
  if (best.exit.aim)                                       // two metres PAST the band
    pts.push([best.exit.at[0] + best.exit.aim[0] * 2, best.exit.at[1],
              best.exit.at[2] + best.exit.aim[1] * 2]);
  // THIN BY SHAPE, NOT BY COUNT. Every-nth-point sampling deletes exactly the corners
  // that make a switchback a switchback, and then the oracle "fails" a shot because the
  // straight line between two of its own waypoints crosses thin air. Douglas-Peucker
  // keeps the corners and drops the filler, which is also what a person drawing a route
  // on a picture does.
  const thin = dp(pts, 0.8).slice(1);
  if (thin.length <= 8) return thin;
  const keep = [];                                   // 8 points, and always the last one
  for (let i = 0; i < 7; i++) keep.push(thin[Math.round(i * (thin.length - 2) / 6)]);
  keep.push(thin[thin.length - 1]);
  return keep;
}
function dp(pts, tol) {
  if (pts.length <= 2) return pts.slice();
  // THE DISTANCE IS 3D ON PURPOSE. Measured in plan only, a staircase is a straight
  // line and Douglas-Peucker deletes the whole flight — which is how the loop stairs
  // ended up with two waypoints, one at the head and one at the foot of a switchback,
  // and a walker that could not possibly follow them.
  const d = (p, a, b) => {
    const v = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    const vv = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
    let t = vv < 1e-12 ? 0 : ((p[0] - a[0]) * v[0] + (p[1] - a[1]) * v[1] + (p[2] - a[2]) * v[2]) / vv;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p[0] - (a[0] + v[0] * t), p[1] - (a[1] + v[1] * t), p[2] - (a[2] + v[2] * t));
  };
  let bi = 0, bd = 0;
  for (let i = 1; i < pts.length - 1; i++) { const q = d(pts[i], pts[0], pts[pts.length - 1]);
    if (q > bd) { bd = q; bi = i; } }
  if (bd <= tol) return [pts[0], pts[pts.length - 1]];
  return dp(pts.slice(0, bi + 1), tol).slice(0, -1).concat(dp(pts.slice(bi), tol));
}

// -------------------------------------------------------------- COMPOSITE ----
// The eval's input image: the baked plate with the character standing at the entry.
// Scale is charPx at that point's view depth (the same number the solve report calls
// the legibility number) and the sprite's feet land on the projected standing point.
// OCCLUSION IS HONOURED: where the plate's own depth is nearer than the character,
// the pixel is drawn at half strength — play3d.html's shipped ghost pass v2 — because
// a character the backdrop hides is exactly the case the eval must be able to see.
let _sprite = null;
function sprite() {
  if (_sprite) return _sprite;
  const p = readPng(POSE);
  // chroma key: is_magenta / near_magenta thresholds (from the retired iso_key.py), feathered between them
  const A = new Uint8Array(p.width * p.height);
  for (let i = 0; i < p.width * p.height; i++) {
    const r = p.data[i * 4], g = p.data[i * 4 + 1], b = p.data[i * 4 + 2];
    const core = (r - g > 90 && b - g > 60), near = (r - g > 50 && b - g > 32);
    A[i] = core ? 0 : near ? 110 : 255;
  }
  let x0 = p.width, x1 = -1, y0 = p.height, y1 = -1;
  for (let y = 0; y < p.height; y++) for (let x = 0; x < p.width; x++)
    if (A[y * p.width + x] > 160) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  const w = x1 - x0 + 1, h = y1 - y0 + 1;
  const rgba = new Uint8Array(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const s = ((y + y0) * p.width + (x + x0)), d = (y * w + x) * 4;
    rgba[d] = p.data[s * 4]; rgba[d + 1] = p.data[s * 4 + 1]; rgba[d + 2] = p.data[s * 4 + 2];
    rgba[d + 3] = A[s];
  }
  return (_sprite = {w, h, data: rgba});
}
// The beauty plate is baked at 2688x1536 and the depth at 1344x768 (cine_bake.py --res
// / --dres). The eval's input is written at the DEPTH resolution: it is the frame every
// other tool in the pipeline reasons in, it keeps an 80-image run to ~30 MB instead of
// ~500, and 1344x768 is far past the point where a vision model stops gaining.
function composite(cam, standPt, outPath) {
  const bgp = readPng(plateFiles(cam.id).bg);
  const W = FRAME[0], H = FRAME[1];
  const sc = bgp.width / W;                              // integer 2 in the shipped bake
  const out = new PNG({width: W, height: H});
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    let r = 0, g = 0, b = 0, n = 0;
    for (let dy = 0; dy < sc; dy++) for (let dx = 0; dx < sc; dx++) {
      const sxp = Math.min(bgp.width - 1, Math.floor(x * sc + dx));
      const syp = Math.min(bgp.height - 1, Math.floor(y * sc + dy));
      const i = (syp * bgp.width + sxp) * 4;
      r += bgp.data[i]; g += bgp.data[i + 1]; b += bgp.data[i + 2]; n++;
    }
    const o = (y * W + x) * 4;
    out.data[o] = r / n; out.data[o + 1] = g / n; out.data[o + 2] = b / n; out.data[o + 3] = 255;
  }
  const S = sprite();
  const foot = toImg(cam, standPt);
  const head = toImg(cam, [standPt[0], standPt[1], standPt[2] + CHARH]);
  if (foot.behind) return {ok: false, why: 'entry is behind the camera'};
  const fx = foot.u * W, fy = foot.v * H;
  const hpx = Math.max(8, Math.abs(head.v * H - fy));
  const scale = hpx / S.h;
  const wpx = Math.max(4, Math.round(S.w * scale)), hh = Math.max(6, Math.round(hpx));
  const left = Math.round(fx - wpx / 2), top = Math.round(fy - hh);
  const cz = foot.z;
  const dimg = readPng(plateFiles(cam.id).depth);
  const {near, far} = cam.depth;
  let drawn = 0, ghosted = 0;
  for (let y = 0; y < hh; y++) {
    const sy = Math.min(S.h - 1, Math.floor(y / scale));
    const py = top + y; if (py < 0 || py >= H) continue;
    for (let x = 0; x < wpx; x++) {
      const sx = Math.min(S.w - 1, Math.floor(x / scale));
      const px = left + x; if (px < 0 || px >= W) continue;
      const a = S.data[(sy * S.w + sx) * 4 + 3] / 255;
      if (a <= 0.02) continue;
      const dxp = Math.min(dimg.width - 1, Math.round(px / W * dimg.width));
      const dyp = Math.min(dimg.height - 1, Math.round(py / H * dimg.height));
      const di = (dyp * dimg.width + dxp) * 4;
      const dz = near + (far - near) *
        (dimg.data[di] * 65536 + dimg.data[di + 1] * 256 + dimg.data[di + 2]) / 16777215;
      const hidden = dz < cz - 0.35;
      // the plate is IN FRONT of her here -> ghost pass v2: half strength
      const k = a * (hidden ? 0.5 : 1);
      drawn++; if (hidden) ghosted++;
      const o = (py * W + px) * 4;
      for (let c = 0; c < 3; c++)
        out.data[o + c] = Math.round(out.data[o + c] * (1 - k) + S.data[(sy * S.w + sx) * 4 + c] * k);
    }
  }
  fs.mkdirSync(path.dirname(outPath), {recursive: true});
  fs.writeFileSync(outPath, PNG.sync.write(out));
  return {ok: true, foot: [+foot.u.toFixed(4), +foot.v.toFixed(4)], charPx: Math.round(hpx),
          box: [left, top, wpx, hh], onScreen: foot.u >= 0 && foot.u <= 1 && foot.v >= 0 && foot.v <= 1,
          occludedFrac: drawn ? +(ghosted / drawn).toFixed(3) : 0};
}

// ------------------------------------------------------------- THE PROMPT ----
// Deliberately context-free: no town, no shot name, no route data, no map, no memory
// of any other image. The only thing it is told is that it is playing and which figure
// is its own. Everything the answer contains therefore came out of the PICTURE, which
// is the whole claim the metric makes.
const PROMPT = [
  'You are playing a video game. The image is what is on screen right now.',
  'Your character is the person standing in the scene.',
  'You want to keep going: leave this area and continue on to the next part of the place you are in.',
  '',
  'Answer with JSON only, in this exact shape:',
  '{"waypoints": [[x, y], [x, y], ...], "reason": "one short sentence"}',
  '',
  'Each waypoint is a point in THIS IMAGE in normalised coordinates: x is 0 at the left',
  'edge and 1 at the right edge, y is 0 at the top edge and 1 at the bottom edge.',
  'List 4 to 8 waypoints in the order you would walk them, starting next to your',
  'character and ending at the place where you think you leave this area.',
].join('\n');

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
const geminiJudge = {
  name: `gemini:${MODEL}`,
  async ask(imagePath, prompt, {temperature}) {
    const KEY = envKey();
    if (!KEY) throw new Error('no GEMINI_API_KEY in .env');
    const body = {
      contents: [{parts: [
        {inline_data: {mime_type: 'image/png', data: fs.readFileSync(imagePath).toString('base64')}},
        {text: prompt}]}],
      generationConfig: {temperature, responseMimeType: 'application/json'},
    };
    let last = null;
    for (let a = 0; a < 4; a++) {
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${KEY}`,
        {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)});
      const j = await res.json().catch(() => ({}));
      if (res.ok) {
        const t = (j.candidates?.[0]?.content?.parts || []).map((p) => p.text || '').join('');
        if (t.trim()) return {text: t, http: res.status};
        last = 'empty reply: ' + JSON.stringify(j).slice(0, 300);
      } else {
        last = `HTTP ${res.status} ` + JSON.stringify(j).slice(0, 300);
        if (res.status !== 429 && res.status < 500) break;
      }
      await new Promise((r) => setTimeout(r, 1500 * (a + 1) * (a + 1)));
    }
    throw new Error(last || 'gemini failed');
  },
};
const stubJudge = {name: 'stub',
  async ask() { return {text: JSON.stringify({waypoints: [[0.5, 0.8], [0.5, 0.95]], reason: 'stub'}), http: 0}; }};
// The ORACLE is not a judge of the plate, it is a judge of THIS FILE: it answers with
// the ground-truth route already projected into the image, so a low oracle score can
// only mean the unprojection or the walker is wrong. Always run it before a real run.
let ORACLE = null;
const oracleJudge = {name: 'oracle',
  async ask() { return {text: JSON.stringify(ORACLE), http: 0}; }};
// oracle-world skips the image entirely and hands the walker the ground-truth world
// points. It isolates the WALKER from the perception pipeline: if this is not ~1.0 the
// bug is in this file, and no plate is to blame.
const oracleWorldJudge = {name: 'oracle-world',
  async ask() { return {text: JSON.stringify(ORACLE), http: 0}; }};
const JUDGES = {gemini: geminiJudge, stub: stubJudge, oracle: oracleJudge,
                'oracle-world': oracleWorldJudge};

function parseReply(text) {
  const tryJson = (s) => { try { return JSON.parse(s); } catch { return null; } };
  let j = tryJson(text);
  if (!j) { const m = /\{[\s\S]*\}/.exec(text); if (m) j = tryJson(m[0]); }
  if (!j) { const m = /\[\s*\[[\s\S]*?\]\s*\]/.exec(text); if (m) j = {waypoints: tryJson(m[0])}; }
  if (!j) return {waypoints: [], reason: null, parseError: true};
  let w = j.waypoints || j.points || j.path || [];
  if (!Array.isArray(w)) w = [];
  w = w.map((p) => Array.isArray(p) ? [+p[0], +p[1]] : [+p.x, +p.y])
       .filter((p) => Number.isFinite(p[0]) && Number.isFinite(p[1]))
       .map((p) => [Math.max(0, Math.min(1, p[0])), Math.max(0, Math.min(1, p[1]))]);
  return {waypoints: w, reason: j.reason || j.reasoning || null, parseError: false};
}

// -------------------------------------------------------------- UNPROJECT ----
// A waypoint is a pixel; the depth plate says what surface that pixel is. If the
// surface is the sky (depth pinned at far) there is no world point at all, and if the
// world point is not near the walk network the player was looking at a wall, a roof or
// the river. Both are recorded as OFF-ROUTE PERCEPTION — the eval's most diagnostic
// sub-score — and the reachable prefix is still executed, because a player would still
// try.
//
// OCCLUSION IS A PERCEPTION FAILURE, NOT A ROUTING HINT (fixed 2026-08-01). Until this
// date an OCCLUDED waypoint — ray reaches walkable floor, plate draws something nearer
// at that pixel — was handed to the walker as `rayWalkHit`'s crossing, which lies
// BEYOND the occluder: a place the picture never showed the judge. Measured over the
// 112 occluded waypoints in four N=10 runs (gate-vista-entrance, gate-walkin-174-20,
// shoprow-before, shoprow-after; instrument: project each stored `rt` back through the
// shot's own camera and take the pixel distance to the judge's own waypoint) that
// fabricated target sat a mean 78.4 px, median 38.0, worst 294.5 from the pixel the
// judge actually chose. The eval was walking a route the judge did not pick and scoring
// the town on it, while its own docstring said occlusion was recorded as a failure.
// The march now STOPS AT THE DRAWN SURFACE: the walker aims at the world point of the
// judge's own pixel, never past it to a floor the picture did not show, walks into the
// occluder as a player would, and the shot is charged for the perception failure it is. `onWalk` no longer counts an occluded pixel as on-route, and every occluded
// waypoint carries `beyond` — the old fabricated target and its pixel error — so the
// change is auditable per waypoint without re-running anything. Measured effect on the
// audit number itself (run-honest-oracle, 65 occluded waypoints on the ground-truth
// route): the distance from the judge's own pixel to the target the walker is handed
// fell from mean 93.8 px / median 7.1 / worst 422.7 to 0 by construction, and the old
// target stood a median 3.28 m (worst 6.96 m) PAST the surface that pixel draws.
//   PIXELS UNDERSTATE IT ON A LONG SIGHT LINE, and the gate is the case in point: over
// the judge's own 57 waypoints at N=10, the fabricated target was a mean 4.1 px from
// the chosen pixel — and a MEDIAN 9.85 m, worst 53.64 m, behind the surface drawn there.
// Near the horizon a pixel is tens of metres deep. Report the metres.
//
// AND OCCLUSION IS NOT MERELY "SOMETHING IS DRAWN NEARER". A grazing sight line down a
// stair or a slope satisfies that by itself; the drawn surface has to stand clear ABOVE
// the walk network to hide anything. See the OCC_GAP block in unproject() — the first
// cut of this fix classified three shots' staircases and quaysides as occlusion and
// dropped the oracle round trip from 13/16 to 11/16 while the walker was provably
// untouched, which is how the false positive was found.
function unproject(cam, u, v) {
  const {z, raw} = depthAt(cam, u, v);
  const sky = raw > 0.999;
  const dir = rayOf(cam, u, v);
  const mp = [cam.pos[0] + dir[0] * z, cam.pos[1] + dir[1] * z, cam.pos[2] + dir[2] * z];
  const seen = m2r(mp);                                  // the surface the PIXEL shows
  const net = rayWalkHit(cam, dir, cam.depth.far);       // the floor the ray is aimed at
  // "The plate draws something NEARER than the floor this ray reaches" is NECESSARY for
  // occlusion and not SUFFICIENT, and the difference is measurable rather than a matter
  // of taste. On a stair or a slope seen from above the ray GRAZES the ground: it flies
  // over several treads before rayWalkHit's 0.2 m march finds one it is under, so the
  // pixel draws the near tread while `net` is a tread or two further on. In depth alone
  // that is indistinguishable from a wall in front of a courtyard — measured on the
  // ground-truth route, loop-stairs' median gap is 0.61 m and waterfront's is 3.46 m,
  // one a staircase and one a boat, both flagged by the same test.
  //
  // THE DISCRIMINATOR IS WHAT THE PIXEL DRAWS. If the drawn surface IS the walk network,
  // the player is looking straight at ground and nothing is hiding anything; the target
  // is that ground, and it is ON ROUTE. Only a drawn surface standing clear ABOVE the
  // walk surface is an occluder. Without this the classifier cost the ORACLE end-to-end
  // round trip three shots (loop-stairs, boatyard, waterfront each 1.00 -> 0.00) while
  // `oracle-world` proved the walker itself unchanged — i.e. a false positive in the
  // classifier, not a finding about the town.
  const OCC_GAP = 0.35;                       // == the walker's own crack tolerance
  const gSeen = groundUnder(seen);            // walk surface at or under the drawn point
  const drawnIsGround = !!(gSeen && seen[1] - gSeen[1] <= OCC_GAP);
  const behindDrawn = !!(net && z < net.z - OCC_GAP);   // the ray's floor is past the pixel
  const occluded = behindDrawn && !drawnIsGround;
  const r2v = (p) => p.map((n) => +n.toFixed(2));
  // px between the judge's own pixel and where a world point lands in this image: the
  // audit number for every target this function hands the walker.
  const pxOff = (rp) => { const s = toImg(cam, r2m(rp));
    return s.behind ? null
      : +Math.hypot((s.u - u) * FRAME[0], (s.v - v) * FRAME[1]).toFixed(1); };
  let rt, aim;
  if (occluded) {
    // THE POINT THE PIXEL SHOWS, and nothing else. There is no ground on this sight
    // line — that is what occluded MEANS — so any "nearest floor" is a guess, and the
    // guess this fix exists to delete was one of them. An intermediate version dropped
    // to the walk surface directly beneath the drawn point; measured, that target sat a
    // median 185 px (max 253) from the judge's own pixel, against 0 by construction for
    // the drawn point itself. Aiming at the drawn surface makes the walker do what a
    // player does — walk at the thing they can see, and be stopped by it — and the
    // waypoint is scored as the perception failure it is (`occluded`, and NOT counted
    // in onWalk), which is where the shot is charged.
    rt = seen; aim = 'occluder-face';
  } else if (net) {
    // Not occluded: the target is the RAY-MARCHED floor, exactly as before this fix.
    // Deliberately NOT the pixel-derived point even in the grazing case, though that
    // is the surface the plate literally drew — measured on the five grazing waypoints
    // the ground truth produces (all on loop-stairs), the pixel-derived target sits a
    // median 17.3 px from the judge's own pixel against the ray-marched target's 2.4,
    // and swapping them cost loop-stairs its oracle round trip. At a grazing angle a
    // one-pixel sampling error in the depth plate is metres along the ray; the 0.2 m
    // march against real geometry is not. THIS FIX IS ABOUT OCCLUDED WAYPOINTS AND
    // TOUCHES NO OTHERS.
    rt = net.rt; aim = behindDrawn ? 'ground-grazing' : 'ground';
  }
  else { rt = seen; aim = 'seen-surface'; }
  return {u: +u.toFixed(4), v: +v.toFixed(4), sky,
          z: +z.toFixed(2), seen: r2v(seen),
          cls: sky ? 'sky' : occluded ? 'occluded'
                : (net || drawnIsGround) ? 'ground' : 'off-route',
          onWalk: (!!net || drawnIsGround) && !occluded, occluded,
          aim, rt: r2v(rt), aimPx: pxOff(rt),            // what the walker aims at, and
          netZ: net ? +net.z.toFixed(2) : null,          // how far that is from the pixel
          // what the pre-2026-08-01 code walked to instead: kept for audit, never used.
          // `m` is the sharp number — how many metres PAST the surface the pixel draws
          // that target stood. It is 0 by construction for every target above.
          beyond: occluded ? {rt: r2v(net.rt), z: +net.z.toFixed(2), px: pxOff(net.rt),
                              gap: +(net.z - z).toFixed(2),
                              m: +Math.hypot(net.rt[0] - seen[0], net.rt[2] - seen[2]).toFixed(2)} : null};
}

// ----------------------------------------------------------------- SCORING ---
function scoreTrial(shotId, entry, wps, pts, walk) {
  const S = gtOf(shotId);
  const from = entry.from || null;
  // "onward" = an exit that is not the door you came in by. A shot whose only exit IS
  // the entry (a dead-end landing) scores on crossing it, or nothing could ever pass.
  const all = S.exits.filter((e) => e.to !== from);
  let onward = all.filter((e) => e.toKind === 'shot');
  if (!onward.length) onward = all.length ? all : S.exits.slice();
  const onwardShots = new Set(onward.filter((e) => e.toKind === 'shot').map((e) => e.to));
  const cuts = walk.events.filter((e) => e.k === 'cut');
  const escaped = cuts.find((c) => c.to !== shotId && (onwardShots.size ? onwardShots.has(c.to) : true));
  const wentBack = !escaped && cuts.some((c) => c.to === from);
  // portals are prompt-gated (press E) — reaching one is not a cut but IS an exit found
  const portal = onward.find((e) => e.toKind === 'scene' && walk.trace.some(
    (p) => Math.hypot(p[0] - e.at[0], p[2] - e.at[2]) <= (e.r || D.portalRadius || 2.2)));
  // progress: how much of the gap from the spawn to the nearest onward exit was closed
  const gap = (p, e) => Math.hypot(p[0] - e.at[0], p[2] - e.at[2]);
  let progress = 0;
  for (const e of onward) {
    const d0 = gap(walk.trace[0], e);
    if (d0 < 1e-6) { progress = 1; continue; }
    const dmin = Math.min(...walk.trace.map((p) => gap(p, e)));
    progress = Math.max(progress, Math.max(0, Math.min(1, (d0 - dmin) / d0)));
  }
  if (escaped) progress = 1;
  const onWalkFrac = pts.length ? pts.filter((p) => p.onWalk).length / pts.length : 0;
  const stuck = walk.legs.filter((l) => l.stuck).length;
  return {
    success: !!escaped,
    exitTaken: escaped ? {to: escaped.to, of: escaped.of} : null,
    wentBack, portalReached: portal ? portal.id : null,
    onWalkFrac: +onWalkFrac.toFixed(3),
    occludedWaypoints: pts.filter((p) => p.occluded).length,
    offRouteWaypoints: pts.filter((p) => p.cls === 'off-route').length,
    skyWaypoints: pts.filter((p) => p.sky).length,
    waypoints: pts.length,
    progressFrac: +progress.toFixed(3),
    stuckLegs: stuck, legs: walk.legs.length,
    cuts: cuts.length, corrections: walk.corrections,
    endCam: walk.endCam,
  };
}

// ------------------------------------------------- GT overlay for the viewer --
// Everything the viewer draws over the input image, precomputed in the SAME normalised
// image coordinates the judge answered in, so the page is a renderer and never a second
// implementation of the projection.
function gtOverlay(cam, shotId) {
  const S = gtOf(shotId);
  const proj = (rp) => { const s = rtToImg(cam, rp); return s.behind ? null : [+s.u.toFixed(4), +s.v.toFixed(4)]; };
  const routes = (S.routes || []).map((r) => ({
    id: r.id, cls: r.class, role: r.role, blocked: !!r.blocked,
    pts: r.points.map(proj).filter(Boolean)}));
  const mark = (e) => ({id: e.id, kind: e.kind, to: e.to || null, from: e.from || null,
                        label: e.label || null, at: proj(e.at), atRt: e.at});
  // a seam band is a rectangle on the ground: centre ± w across, ± t along the normal
  const bands = (S.exits || []).filter((e) => e.seam).map((e) => {
    const n = e.seam.n, t = e.seam.t, w = e.seam.w, p = e.at;
    const px = [-n[1], n[0]];
    const q = (a, b) => proj([p[0] + n[0] * a * t + px[0] * b * w, p[1],
                              p[2] + n[1] * a * t + px[1] * b * w]);
    return {id: e.id, to: e.to, quad: [q(-1, -1), q(-1, 1), q(1, 1), q(1, -1)].filter(Boolean)};
  }).filter((b) => b.quad.length === 4);
  return {routes, entries: (S.entries || []).map(mark), exits: (S.exits || []).map(mark), bands};
}

// ---------------------------------------------------------------- THE RUN ----
const shotIds = CINE.cameras.map((c) => c.id)
  .filter((id) => NODE.shots.some((s) => s.id === id))          // retired cameras are out
  .filter((id) => !ONLY.length || ONLY.includes(id));

async function pool(items, n, fn) {
  const out = new Array(items.length); let i = 0;
  await Promise.all(Array.from({length: Math.min(n, items.length)}, async () => {
    for (;;) { const k = i++; if (k >= items.length) return; out[k] = await fn(items[k], k); }
  }));
  return out;
}

async function main() {
  const judge = JUDGES[JUDGE_NAME];
  if (!judge) { console.error('unknown judge: ' + JUDGE_NAME); process.exit(1); }
  fs.mkdirSync(path.join(OUTDIR, 'inputs'), {recursive: true});
  const run = {
    version: 1, town: TOWN, scene: SCENE, stamp: STAMP, tag: TAG,
    generated: new Date().toISOString(),
    generator: 'tools/nav_eval.mjs',
    judge: judge.name, model: JUDGE_NAME === 'gemini' ? MODEL : null,
    n: N, temperature: TEMP, frame: FRAME,
    plates: path.relative(ROOT, PLATES), cine: path.relative(ROOT, CINE_PATH),
    cineGenerated: CINE.generated || null, solvedGenerated: SOLVED.generated || null,
    prompt: PROMPT,
    shots: [], trials: [],
  };
  // ---- build every (shot, entry) case, composite its input image ------------
  const cases = [];
  for (const id of shotIds) {
    const cam = camOf(id);
    if (!cam) { console.warn(`skip ${id}: no camera record`); continue; }
    if (!plateFiles(id).ok) { console.warn(`skip ${id}: no plate under ${PLATES}`); continue; }
    const S = gtOf(id);
    const ents = ENTRIES_MODE === 'all' ? S.entries : [primaryEntry(S, id)].filter(Boolean);
    if (!ents.length) { console.warn(`skip ${id}: no entry in routes.json`); continue; }
    for (const e of ents) {
      const key = `${id}__${e.id.replace(/[^a-z0-9]+/gi, '-')}`;
      const img = path.join(OUTDIR, 'inputs', key + '.png');
      const c = composite(cam, r2m(e.at), img);
      cases.push({shot: id, cam, entry: e, key, img, comp: c, gt: gtOverlay(cam, id)});
    }
  }
  console.log(`nav_eval: ${cases.length} (shot, entry) cases x ${N} trials, judge=${judge.name}` +
              `, plates=${run.plates}`);
  if (DRY) { console.log(cases.map((c) => c.key).join('\n')); return; }

  // ---- run the trials ------------------------------------------------------
  const jobs = [];
  for (const c of cases) for (let k = 0; k < N; k++) jobs.push({c, k});
  let done = 0;
  const results = await pool(jobs, CONC, async ({c, k}) => {
    let world = null;
    if (JUDGE_NAME.startsWith('oracle')) {
      const pick = gtChain(c);
      world = pick;
      const uv = pick.map((p) => { const s = rtToImg(c.cam, p);
        return s.behind ? null : [+s.u.toFixed(3), +s.v.toFixed(3)]; }).filter(Boolean);
      ORACLE = {waypoints: uv, reason: 'ground truth route (harness self-check)'};
    }
    let reply = null, err = null;
    try { reply = await judge.ask(c.img, PROMPT, {temperature: TEMP}); }
    catch (e) { err = String(e.message || e); }
    const parsed = reply ? parseReply(reply.text) : {waypoints: [], reason: null, parseError: true};
    const pts = parsed.waypoints.map((w) => unproject(c.cam, w[0], w[1]));
    const spawn = c.entry.at;
    const targets = JUDGE_NAME === 'oracle-world' ? world : pts.filter((p) => !p.sky).map((p) => p.rt);
    const walk = walkChain(c.shot, spawn, targets);
    const sc = scoreTrial(c.shot, c.entry, parsed.waypoints, pts, walk);
    process.stdout.write(`\r  ${++done}/${jobs.length}  ${c.shot} #${k} ` +
      `${err ? 'ERR' : sc.success ? 'PASS' : 'fail'}          `);
    return {shot: c.shot, entry: c.entry.id, entryKind: c.entry.kind, entryFrom: c.entry.from || null,
            trial: k, input: `inputs/${c.key}.png`, prompt: PROMPT,
            reply: reply ? reply.text : null, error: err,
            reason: parsed.reason, parseError: parsed.parseError,
            waypoints: parsed.waypoints, points: pts,
            walk: {endCam: walk.endCam, endAt: walk.endAt, events: walk.events,
                   legs: walk.legs, corrections: walk.corrections, trace: walk.trace,
                   // the trace, and every leg's stopping point, PROJECTED BACK into the
                   // input image: the viewer's whole job is to show where the walk went
                   // on the picture the judge was looking at, and it must not own a
                   // second copy of the projection to do it.
                   traceUv: uvChain(c.cam, walk.trace),
                   legUv: walk.legs.map((l) => ({i: l.i, why: l.why, stuck: l.stuck,
                     target: uv1(c.cam, l.target), end: uv1(c.cam, l.endAt)})),
                   eventUv: walk.events.map((e) => ({k: e.k, to: e.to, of: e.of,
                     at: uv1(c.cam, e.at)}))},
            score: sc};
  });
  console.log('');
  run.trials = results;

  // ---- per-shot rollup -----------------------------------------------------
  for (const c of cases) {
    const t = results.filter((r) => r.shot === c.shot && r.entry === c.entry.id);
    const mean = (f) => t.length ? +(t.reduce((a, r) => a + f(r), 0) / t.length).toFixed(3) : 0;
    run.shots.push({
      shot: c.shot, name: (CAMBY[c.shot] || {}).name || c.shot,
      entry: c.entry.id, entryKind: c.entry.kind, entryFrom: c.entry.from || null,
      input: `inputs/${c.key}.png`, composite: c.comp,
      camera: {pos: c.cam.pos, aim: c.cam.aim, fov: c.cam.fov, depth: c.cam.depth,
               solvedDrift: c.cam.drift},
      exits: (gtOf(c.shot).exits || []).map((e) => ({id: e.id, to: e.to, kind: e.kind, toKind: e.toKind})),
      gt: c.gt,
      trials: t.length,
      score: mean((r) => r.score.success ? 1 : 0),
      onWalkFrac: mean((r) => r.score.onWalkFrac),
      // the occlusion classification, rolled up: what share of the judge's waypoints
      // landed on a pixel that hides the floor it was aiming at. Per-waypoint detail
      // (cls / aim / aimPx / beyond) is in every trial's `points`.
      occludedFrac: mean((r) => r.score.waypoints
        ? r.score.occludedWaypoints / r.score.waypoints : 0),
      offRouteFrac: mean((r) => r.score.waypoints
        ? r.score.offRouteWaypoints / r.score.waypoints : 0),
      progressFrac: mean((r) => r.score.progressFrac),
      stuckLegs: mean((r) => r.score.stuckLegs),
      wentBack: t.filter((r) => r.score.wentBack).length,
      errors: t.filter((r) => r.error).length,
    });
  }
  run.town_score = run.shots.length
    ? +(run.shots.reduce((a, s) => a + s.score, 0) / run.shots.length).toFixed(3) : 0;

  fs.writeFileSync(path.join(OUTDIR, 'results.json'), JSON.stringify(run, null, 1));
  scorecard(run);
  console.log(`\nresults: ${path.relative(ROOT, OUTDIR)}/results.json` +
    `\nviewer:  docs/qa/naveval/viewer.html?run=${STAMP}`);
}

function scorecard(run) {
  const rows = run.shots.slice().sort((a, b) => a.score - b.score);
  console.log(`\nNAV-EVAL SCORECARD — ${run.town} / ${run.scene}  (judge ${run.judge}, ` +
              `N=${run.n}, plates ${run.plates})`);
  console.log('shot            entry                     score  onWalk  occl  offrt  progress  stuck  back');
  for (const s of rows) {
    console.log(`${s.shot.padEnd(15)} ${String(s.entry).slice(0, 24).padEnd(24)} ` +
      `${s.score.toFixed(2).padStart(5)}  ${s.onWalkFrac.toFixed(2).padStart(6)}  ` +
      `${(s.occludedFrac ?? 0).toFixed(2).padStart(4)}  ${(s.offRouteFrac ?? 0).toFixed(2).padStart(5)}  ` +
      `${s.progressFrac.toFixed(2).padStart(8)}  ${String(s.stuckLegs).padStart(5)}  ` +
      `${String(s.wentBack).padStart(4)}`);
  }
  console.log(`TOWN SCORE  ${run.town_score.toFixed(3)}   ` +
    `(${run.shots.filter((s) => s.score >= 0.8).length} of ${run.shots.length} shots >= 0.80)`);
}

// ------------------------------------------------------------- CALIBRATION ---
// `--compare <runA> <runB>` prints the separation between two runs shot by shot. This
// is the eval-of-the-eval and it is a first-class mode, not a script somebody wrote
// once: a perceptual metric that cannot tell a bake with MEASURED legibility failures
// from the bake that fixed them is not measuring legibility, and the only way to know
// is to put the two numbers next to each other.
function compare(aStamp, bStamp) {
  const load = (st) => JSON.parse(fs.readFileSync(
    path.join(ROOT, 'docs/qa/naveval', 'run-' + st, 'results.json'), 'utf8'));
  const A = load(aStamp), B = load(bStamp);
  const key = (s) => s.shot;
  const bm = Object.fromEntries(B.shots.map((s) => [key(s), s]));
  const rows = A.shots.map((a) => ({a, b: bm[key(a)]})).filter((r) => r.b);
  rows.sort((x, y) => (y.b.score - y.a.score) - (x.b.score - x.a.score));
  console.log(`\nCALIBRATION — ${aStamp}  ->  ${bStamp}`);
  console.log(`  A plates ${A.plates}\n  B plates ${B.plates}`);
  console.log(`  judge ${A.judge} / ${B.judge}, N=${A.n}/${B.n}\n`);
  console.log('shot             A     B     d      progress A->B    onWalk A->B');
  for (const {a, b} of rows) {
    const d = b.score - a.score;
    console.log(`${a.shot.padEnd(16)}${a.score.toFixed(2)}  ${b.score.toFixed(2)}  ` +
      `${(d >= 0 ? '+' : '') + d.toFixed(2)}   ` +
      `${a.progressFrac.toFixed(2)} -> ${b.progressFrac.toFixed(2)}      ` +
      `${a.onWalkFrac.toFixed(2)} -> ${b.onWalkFrac.toFixed(2)}`);
  }
  const up = rows.filter((r) => r.b.score > r.a.score).length;
  const dn = rows.filter((r) => r.b.score < r.a.score).length;
  console.log(`\nTOWN  ${A.town_score.toFixed(3)} -> ${B.town_score.toFixed(3)}  ` +
    `(${(B.town_score - A.town_score >= 0 ? '+' : '')}${(B.town_score - A.town_score).toFixed(3)});` +
    ` ${up} shots up, ${dn} down, ${rows.length - up - dn} unchanged`);
}

if (flag('--compare')) {
  const i = ARGS.indexOf('--compare');
  compare(ARGS[i + 1], ARGS[i + 2]);
} else {
  main().catch((e) => { console.error(e); process.exit(1); });
}
