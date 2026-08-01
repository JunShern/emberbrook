// cine_regions.mjs — THE shared brain of the cinematic-camera layer.
//
// Everything that knows what a camera OWNS, where it STANDS, and where two
// cameras MEET lives in this one module, and it is imported by all four
// consumers so they cannot drift apart:
//
//   tools/cine_solve.mjs        solves framing -> dellhollow.cameras.solved.json
//   tools/scenegraph_derive.mjs emits the silent cut edges into scenegraph.json
//   tools/cine_test.mjs         proves coverage, framing and reachability
//   tools/cine_bake.py          (indirectly: it reads the solved file)
//
// SINGLE SOURCE OF CAMERA NUMBERS (supervisor condition 1). The chain is:
//   dellhollow.cameras.json   authored INTENT (yaw/pitch/fov/margin, or explicit pos/aim)
//     -> cameras.solved.json  the ONE numeric truth (pos/aim/fov/clip), derived here
//        -> cine_bake.py      builds the Blender camera from it, bakes bg+depth
//        -> del-cine/cine.json  records what was actually baked (adds depth near/far)
//           -> play3d.html     builds the THREE.PerspectiveCamera from cine.json
// cine_test.mjs asserts every link of that chain agrees, and cine_solve.mjs --check
// fails the build if the solved file is stale against the authored one. No camera
// number is ever typed twice.
//
// COORDINATE FRAMES. Authoring, Blender and this module all use MAP coords
// [x, y, h]: x along-gorge, y cliff(0)->river(~30), h height (water ~0). The
// runtime uses [x, h, -y]. Conversions are m2r/r2m below and are the only place
// the swap happens.
import fs from 'fs';
import path from 'path';
import {loadGlb} from './glb_read.mjs';

export const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
export const PUB = path.join(ROOT, 'public');
export const rd = (p) => JSON.parse(fs.readFileSync(path.join(PUB, p), 'utf8'));

// map [x,y,h] <-> runtime [x,y(up),z]
export const m2r = (p) => [p[0], p[2], -p[1]];
export const r2m = (p) => [p[0], -p[2], p[1]];

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const len = (a) => Math.hypot(a[0], a[1], a[2]);
const unit = (a) => { const L = len(a) || 1; return mul(a, 1 / L); };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const RAD = Math.PI / 180;
export const r3 = (v) => v.map((n) => Math.round(n * 1000) / 1000);

// ------------------------------------------------------------------ loading --
export function loadCine(townFile = 'townmap/dellhollow.map.json',
                         camFile = 'townmap/dellhollow.cameras.json') {
  const map = rd(townFile), cam = rd(camFile);
  const D = cam.defaults;
  const LM = {}; for (const l of map.landmarks) LM[l.id] = l;
  const warn = [];
  const W = (m) => { warn.push(m); };

  // ---- map walk edges, keyed the way the walk meshes are named -------------
  const edgeKey = (e) => `${e.from}__${e.to}`;
  const MEDGE = {};
  for (const e of map.edges) {
    const k = edgeKey(e);
    if (MEDGE[k]) W(`duplicate map edge '${k}'`);
    const pts = [LM[e.from].pos, ...(e.waypoints || []), LM[e.to].pos];
    const seg = [], cum = [0];
    for (let i = 0; i < pts.length - 1; i++) {
      const L = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]);
      seg.push(L); cum.push(cum[i] + L);
    }
    MEDGE[k] = {rec: e, pts, cum, L: cum[cum.length - 1], key: k};
  }

  // ---- ownership ----------------------------------------------------------
  // landmark id -> camera id; edge key -> [{t0,t1,cam}] tiling [0,1]
  const lmOwner = {}, edgeOwner = {}, cellOwner = {};
  const cams = cam.cameras.map((c) => {
    const f = Object.assign({}, D, c.framing || {});
    return Object.assign({}, c, {F: f});
  });
  for (const c of cams) {
    // `owns` may be absent entirely — that is what a CINEMATIC plate owns (nothing).
    // Guarded here rather than required as an empty object in the data, because an
    // authored `"owns": {}` reads like an oversight and an absent one reads like a
    // statement. Totality over landmarks and edges is unaffected: a plate owning
    // nothing cannot close a coverage hole, so the walkable shots still must.
    if (!c.owns) c.owns = {};
    // ---- landmarks: the whole thing, or A SUBSET OF ITS CELLS -----------------
    // A landmarks entry is a STRING (this camera owns the landmark and every walk mesh
    // named after it) or an OBJECT {id, cells:{min:[x,y], max:[x,y]}} claiming only the
    // cells whose centre falls in that map-space box.
    //
    // WHY THE OBJECT FORM EXISTS (coordinator ruling 2026-08-01). Emberbrook's plaza was
    // one 27.9 m walk mesh and is now 57 derived 3.5 m cells, so a second camera CAN in
    // principle be given part of the floor. It could not be expressed: `ownerOfWalk`
    // resolves `walk_lm_square-plaza.017` through the LANDMARK, which has exactly one
    // owner, so a variant handing a second camera the plaza's south spurs left all 57
    // cells resolving to the first one. This is the smallest change that makes the
    // subset sayable.
    //
    // THE LANDMARK STILL HAS EXACTLY ONE PRIMARY OWNER — the camera that names it as a
    // bare string — and that is deliberate, not an oversight. The primary owner carries
    // the landmark's IDENTITY: totality is checked against it, and `derivedCuts` reads it
    // at both ends of every edge that terminates here. Cell claims move WALK MESHES
    // between regions; they never move the node the map's topology hangs off. A landmark
    // claimed by cells with no primary owner is an error, because every edge touching it
    // would lose its endpoint.
    for (const spec of c.owns.landmarks || []) {
      const id = typeof spec === 'string' ? spec : (spec && spec.id);
      if (!id) { W(`camera '${c.id}': a landmarks entry has no 'id'`); continue; }
      if (!LM[id]) { W(`camera '${c.id}': landmark '${id}' is not in the town map`); continue; }
      if (typeof spec === 'string') {
        if (lmOwner[id]) W(`landmark '${id}' owned by BOTH '${lmOwner[id]}' and '${c.id}'`);
        lmOwner[id] = c.id;
        continue;
      }
      const b = spec.cells;
      // TWO SHAPES, because a box was the wrong primitive for the first real case. A BOX
      // {min,max} is axis-aligned; the thing that divides Festival Square is the market
      // row, a line at 150 degrees, and the best axis-aligned box capturing only its
      // north-east cells got 14 of the 20 — measured, not guessed. So a claim may also be
      // a HALF-PLANE {through:[x,y], bearing:<deg>, side:+1|-1}, which is what an
      // articulation actually is.
      //   BEARING IS DEGREES FROM +x, COUNTER-CLOCKWISE (the maths convention), and it is
      // spelled out because this map ALSO carries `doorFace`, a COMPASS bearing with
      // 0 = +y. The two differ and both look plausible on a diagram: reading the market
      // row's stalls under the wrong one put its axis 30 degrees out and every derived
      // crossing on the wrong line. State the convention, always.
      if (b && Array.isArray(b.through) && b.bearing !== undefined) {
        const r = b.bearing * RAD, sgn = b.side === undefined ? 1 : (b.side < 0 ? -1 : 1);
        (cellOwner[id] = cellOwner[id] || []).push({cam: c.id, kind: 'half',
          through: b.through, n: [Math.cos(r + Math.PI / 2), Math.sin(r + Math.PI / 2)], sgn,
          desc: `half-plane through [${b.through.join(',')}] at ${b.bearing}deg, side ${sgn > 0 ? '+' : '-'}`});
        continue;
      }
      if (!b || !Array.isArray(b.min) || !Array.isArray(b.max) || b.min.length < 2 || b.max.length < 2) {
        W(`camera '${c.id}': cell claim on '${id}' needs cells:{min:[x,y], max:[x,y]} or ` +
          'cells:{through:[x,y], bearing:<deg from +x>, side:+1|-1}');
        continue;
      }
      if (b.min[0] > b.max[0] || b.min[1] > b.max[1])
        W(`camera '${c.id}': cell claim on '${id}' has min past max — it can never match a cell`);
      (cellOwner[id] = cellOwner[id] || []).push({cam: c.id, kind: 'box', min: b.min, max: b.max,
        desc: `box [${b.min.join(',')}]..[${b.max.join(',')}]`});
    }
    for (const spec of c.owns.edges || []) {
      const m = /^(.+?)(?:@([\d.]+)\.\.([\d.]+))?$/.exec(spec);
      const k = m[1], t0 = m[2] === undefined ? 0 : +m[2], t1 = m[3] === undefined ? 1 : +m[3];
      if (!MEDGE[k]) { W(`camera '${c.id}': edge '${k}' is not in the town map`); continue; }
      (edgeOwner[k] = edgeOwner[k] || []).push({t0, t1, cam: c.id});
    }
  }
  for (const k in edgeOwner) {
    edgeOwner[k].sort((a, b) => a.t0 - b.t0);
    let t = 0;
    for (const s of edgeOwner[k]) {
      if (Math.abs(s.t0 - t) > 1e-6) W(`edge '${k}': ownership gap/overlap at t=${t} (next starts ${s.t0})`);
      t = s.t1;
    }
    if (Math.abs(t - 1) > 1e-6) W(`edge '${k}': ownership stops at t=${t}, must tile to 1`);
  }
  // CELL CLAIMS are checked against the same contract the rest of ownership is: every
  // claimed landmark keeps a primary owner, and two cameras may not claim the same cell.
  for (const id in cellOwner) {
    if (!lmOwner[id])
      W(`landmark '${id}' is claimed by CELLS (${cellOwner[id].map((q) => q.cam).join(', ')}) but ` +
        'has no camera owning it outright — a cell claim divides a landmark\'s floor, it cannot ' +
        'replace the landmark, and every edge ending here would lose its endpoint owner');
    const q = cellOwner[id];
    for (let i = 0; i < q.length; i++) for (let j = i + 1; j < q.length; j++) {
      if (q[i].kind !== 'box' || q[j].kind !== 'box') continue;   // half-planes: no static overlap test
      if (q[i].min[0] <= q[j].max[0] && q[j].min[0] <= q[i].max[0] &&
          q[i].min[1] <= q[j].max[1] && q[j].min[1] <= q[i].max[1])
        W(`landmark '${id}': cell claims by '${q[i].cam}' and '${q[j].cam}' OVERLAP — a cell ` +
          'would belong to two shots and which one wins would be authoring order');
    }
  }
  // TOTALITY — the coverage contract, checked against the map, not the geometry
  for (const l of map.landmarks) if (!lmOwner[l.id]) W(`landmark '${l.id}' is owned by NO camera`);
  for (const k in MEDGE) if (!edgeOwner[k]) W(`edge '${k}' is owned by NO camera`);

  return {map, camFile: cam, D, LM, MEDGE, cams, lmOwner, edgeOwner, cellOwner, warn,
          byId: Object.fromEntries(cams.map((c) => [c.id, c]))};
}

// ------------------------------------------------------------- polyline math --
// point at arc-length fraction t along a map edge's polyline (map coords)
export function edgePoint(E, t) {
  const s = Math.max(0, Math.min(1, t)) * E.L;
  for (let i = 0; i < E.cum.length - 1; i++) {
    if (s <= E.cum[i + 1] || i === E.cum.length - 2) {
      const f = E.cum[i + 1] - E.cum[i] < 1e-9 ? 0 : (s - E.cum[i]) / (E.cum[i + 1] - E.cum[i]);
      const a = E.pts[i], b = E.pts[i + 1];
      return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
    }
  }
  return E.pts[0].slice();
}
// horizontal direction of travel at t (map xy, unit)
export function edgeDir(E, t) {
  const a = edgePoint(E, Math.max(0, t - 0.02)), b = edgePoint(E, Math.min(1, t + 0.02));
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
  return [dx / L, dy / L];
}
// arc-length fraction of the polyline point nearest p (map xy only)
export function edgeT(E, p) {
  let best = {d: Infinity, t: 0};
  for (let i = 0; i < E.pts.length - 1; i++) {
    const a = E.pts[i], b = E.pts[i + 1];
    const vx = b[0] - a[0], vy = b[1] - a[1], vv = vx * vx + vy * vy;
    let f = vv < 1e-12 ? 0 : ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / vv;
    f = Math.max(0, Math.min(1, f));
    const qx = a[0] + vx * f, qy = a[1] + vy * f;
    const d = Math.hypot(p[0] - qx, p[1] - qy);
    if (d < best.d) best = {d, t: E.L < 1e-9 ? 0 : (E.cum[i] + Math.hypot(vx, vy) * f) / E.L};
  }
  return best.t;
}

// ------------------------------------------------- walk-mesh -> owning camera --
// The whole coverage proof rests on this: townwalk's walk meshes are NAMED after
// the map records that generated them, so ownership of the records IS ownership
// of the geometry. Nothing is inferred from position except WHICH PART of a split
// edge a mesh belongs to.
const NAME_PAD = /^walk_pad_(.+?)(\.\d+)?$/i;
const NAME_LM  = /^walk_lm_(.+?)(\.\d+)?$/i;
const NAME_E   = /^walk_e_(.+?)__(.+?)_(l\d+.*|t\d+.*|landing.*|.*)$/i;
export function ownerOfWalk(C, name, centerMap) {
  let m = NAME_PAD.exec(name) || NAME_LM.exec(name);
  if (m) {
    const id = m[1];
    // A CELL CLAIM WINS OVER THE PRIMARY OWNER, and only for the meshes it contains. The
    // guard is written so a town with no claims takes exactly the path it took before
    // this existed: `cellOwner` is empty, the loop never runs, the return is unchanged.
    const claims = C.cellOwner && C.cellOwner[id];
    if (claims && centerMap) {
      for (const q of claims) {
        const hit = q.kind === 'half'
          ? ((centerMap[0] - q.through[0]) * q.n[0] + (centerMap[1] - q.through[1]) * q.n[1]) * q.sgn > 0
          : (centerMap[0] >= q.min[0] && centerMap[0] <= q.max[0] &&
             centerMap[1] >= q.min[1] && centerMap[1] <= q.max[1]);
        if (hit) return {cam: q.cam, lm: id, cells: true, via: `landmark ${id} ${q.desc}`};
      }
    }
    return {cam: C.lmOwner[id] || null, via: `landmark ${id}`, lm: id};
  }
  m = NAME_E.exec(name);
  if (m) {
    const k = `${m[1]}__${m[2]}`, E = C.MEDGE[k];
    if (!E) return {cam: null, via: `unknown edge ${k}`};
    const segs = C.edgeOwner[k] || [];
    if (segs.length === 1) return {cam: segs[0].cam, via: `edge ${k}`, edge: k};
    const t = centerMap ? edgeT(E, centerMap) : 0;
    const s = segs.find((s) => t >= s.t0 - 1e-9 && t <= s.t1 + 1e-9) || segs[segs.length - 1];
    return {cam: s.cam, via: `edge ${k}@${s.t0}..${s.t1} (t=${t.toFixed(3)})`, edge: k, t};
  }
  return {cam: null, via: 'unrecognised walk mesh name'};
}

// every walk mesh of a bundle, tagged with its owner and its MAP-space AABB
export function walkMeshes(glbPath) {
  const G = loadGlb(glbPath);
  const out = [];
  for (const o of G.nodesNamed(/^walk/i)) {
    const b = G.nodeBox(o.i);
    if (!b) continue;
    // runtime AABB -> map AABB (y and z swap and z negates, so min/max swap on y)
    const mn = [b.min[0], -b.max[2], b.min[1]], mx = [b.max[0], -b.min[2], b.max[1]];
    out.push({name: o.name, min: mn, max: mx,
              center: [(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2],
              rt: {min: b.min, max: b.max, center: b.center}});
  }
  return {G, meshes: out};
}

// ------------------------------------------------------------ camera solving --
// A camera is a look-at + a vertical fov. `pos` is solved so that every SAMPLE of
// the owned region lands inside the frame with `margin` clear around it. Samples
// are the top face of every owned walk mesh (4 corners + centre) lifted by charH,
// so what is being framed is not the ground plane but the space a CHARACTER
// occupies standing on it — the thing that must never be off-screen.
export function regionSamples(C, camId, meshes, charH) {
  const H = charH === undefined ? C.D.charH : charH;
  const pts = [];
  for (const m of meshes) {
    if (m.owner !== camId) continue;
    const [x0, y0] = m.min, [x1, y1] = m.max, h = m.max[2];
    for (const p of [[(x0 + x1) / 2, (y0 + y1) / 2], [x0, y0], [x1, y0], [x0, y1], [x1, y1]])
      pts.push([p[0], p[1], h]);
  }
  return {ground: pts, head: pts.map((p) => [p[0], p[1], p[2] + H])};
}

export function camBasis(pos, aim) {
  const f = unit(sub(aim, pos));
  const U = [0, 0, 1];
  let r = cross(f, U);
  if (len(r) < 1e-6) r = [1, 0, 0];
  r = unit(r);
  let u = unit(cross(r, f));
  if (u[2] < 0) { r = mul(r, -1); u = unit(cross(r, f)); }
  return {f, r, u};
}
// project a map point into normalised screen coords ([-1,1] = the frame)
export function project(pos, aim, fovDeg, aspect, p) {
  const {f, r, u} = camBasis(pos, aim);
  const v = sub(p, pos), z = dot(v, f);
  if (z <= 1e-6) return {z, sx: Infinity, sy: Infinity, behind: true};
  const ty = Math.tan(fovDeg * RAD / 2);
  return {z, behind: false, sx: (dot(v, r) / z) / (ty * aspect), sy: (dot(v, u) / z) / ty};
}
// on-screen height in px of a charH-tall figure at view depth z
export const charPx = (fovDeg, z, charH, frameH) =>
  (charH / z) / (2 * Math.tan(fovDeg * RAD / 2)) * frameH;

export function solveCamera(C, cam, meshes, arrivals, opts) {
  const O = opts || {};
  const F = cam.F, fov = F.fov, aspect = F.aspect;
  const S = regionSamples(C, cam.id, meshes, F.charH);
  // ---- THE CINEMATIC PLATE (coordinator ruling, cinematic class) --------------
  // `"cinematic": true` on a camera record declares a NON-WALKABLE establishing shot —
  // the FFIX idiom this project is styled on. It owns no walk record, no seam targets
  // it, and the player may be a speck or absent, so THE SOLVER HAS NOTHING TO FIT: the
  // frame is authored pos/aim and stands as a human ruling, exactly as `pin` does.
  //
  // WHY THE CLASS HAD TO EXIST, in one line of arithmetic (2026-08-01 carryover lane):
  // a walkable shot is anchored by the region it owns, and the 50 px legibility floor
  // caps its standoff at ~41 m, which at fov 35 frames a 40-60 m swath. Dellhollow is
  // 100 m long. Widening the fov loses charPx exactly as distance does. So "a vantage
  // point that shows off the entire town" is unreachable for EVERY walkable shot, at
  // every aim, by construction — not for want of searching.
  //
  // THE EXEMPTION IS NARROW BY DESIGN, and its bounds are asserted in cine_test's
  // CINEMATIC section, not merely intended here: a plate owns zero walk records and no
  // seam may name it. Legibility fields are reported as NULL rather than as a number,
  // because a plate that reported charPxFar would look to every future reader like a
  // walkable shot that happened to pass the gate.
  if (cam.cinematic) {
    if (!(cam.pos && cam.aim))
      return {id: cam.id, cinematic: true,
              error: 'a cinematic plate must author pos and aim — it owns no region to solve against'};
    if (S.ground.length)
      return {id: cam.id, cinematic: true,
              error: `a cinematic plate must own NO walk record (it owns ${S.ground.length / 5})`};
    return {id: cam.id, pos: r3(cam.pos.slice()), aim: r3(cam.aim.slice()), fov, aspect,
            cinematic: true, authored: true,
            dist: +len(sub(cam.aim, cam.pos)).toFixed(2),
            samples: 0, inFrameFrac: null, zNear: null, zFar: null,
            charPxNear: null, charPxFar: null, clip: [F.clip[0], F.clip[1]]};
  }
  // ARRIVAL POINTS are framed alongside the owned ground: every seam, door and portal
  // that lands in this shot contributes the standing point AND the head above it, so a
  // player can never materialise off-screen. This is a hard requirement of the brief,
  // and it is enforced here — at the moment the standoff is chosen — rather than
  // discovered afterwards by a test.
  const arr = [];
  for (const p of (arrivals || [])) { arr.push(p.slice()); arr.push([p[0], p[1], p[2] + F.charH]); }
  // EXIT POINTS — the other half of the same requirement, and the half that was missing.
  // An arrival is where a player MATERIALISES in this shot; an exit is where they LEAVE
  // it, i.e. the centre of every seam band this shot is on the sending side of. Framing
  // only arrivals frames the ground you appear on and not the ground you walk to: the
  // legibility audit measured five Dellhollow exits BELOW their own frame (cottage
  // ndc y -1.37), so the player walks out of shot and the cut fires after they are
  // gone — "transitions take me by surprise", mechanised. A seam is walkable in both
  // directions, so it is an exit of BOTH shots it separates and both must frame it.
  // Standing point and head, exactly as for arrivals: the ground you aim at and the
  // figure standing on it are two different questions and the audit grades both.
  //
  // PIN (`"pin": true` in the camera record) opts a shot out of BOTH the new constraint
  // and its measurement, so a pinned shot re-solves to itself byte for byte: its frame is
  // a human ruling and a solver that quietly re-scores it invites the next agent to
  // "improve" it. Boatyard is the user-accepted v10 hero frame; re-aiming it is the
  // user's taste call, not a tool's.
  const ex = [];
  if (!cam.pin) for (const p of (O.exits || [])) { ex.push(p.slice()); ex.push([p[0], p[1], p[2] + F.charH]); }
  const all = [...S.ground, ...S.head, ...arr, ...ex];
  if (!S.ground.length) return {id: cam.id, error: 'owns no walk geometry'};

  if (cam.pos && cam.aim) {                       // a human-accepted frame: do not move it
    const rep = frameReport(C, cam, cam.pos, cam.aim, all, S);
    return {id: cam.id, pos: r3(cam.pos.slice()), aim: r3(cam.aim.slice()), fov, aspect,
            authored: true, dist: +len(sub(cam.aim, cam.pos)).toFixed(2), ...rep};
  }
  // aim: the centroid of the region's ground samples, lifted to eye height
  const c = all.reduce((a, p) => add(a, p), [0, 0, 0]);
  const cen = mul(c, 1 / all.length);
  const aim = [cen[0], cen[1], S.ground.reduce((a, p) => a + p[2], 0) / S.ground.length + F.aimLift];
  const dir = [Math.cos(F.pitch * RAD) * Math.cos(F.yaw * RAD),
               Math.cos(F.pitch * RAD) * Math.sin(F.yaw * RAD),
               Math.sin(F.pitch * RAD)];
  // smallest standoff that fits every sample inside (1 - margin) of the frame
  const fits = (D) => {
    const pos = add(aim, mul(dir, D));
    for (const p of all) {
      const q = project(pos, aim, fov, aspect, p);
      if (q.behind || Math.abs(q.sx) > 1 - F.margin || Math.abs(q.sy) > 1 - F.margin) return false;
    }
    return true;
  };
  let lo = 2, hi = 8;
  while (hi < F.maxDist * 4 && !fits(hi)) hi *= 1.35;
  for (let i = 0; i < 40; i++) { const mid = (lo + hi) / 2; if (fits(mid)) hi = mid; else lo = mid; }
  // minDist is a FLOOR on the standoff, not a fit constraint: a small region (the
  // market's one stall pad, before the stalls are built) fits from four metres away,
  // and a camera four metres from a market is standing inside it. Authoring a floor
  // keeps the shot honest against geometry that is still to come.
  const D = Math.max(Math.min(hi, F.maxDist), F.minDist || 0);
  const pos = add(aim, mul(dir, D));
  const capped = hi > F.maxDist + 1e-3;
  const rep = frameReport(C, cam, pos, aim, all, S);
  return {id: cam.id, pos: r3(pos), aim: r3(aim), fov, aspect, dist: +D.toFixed(2),
          solvedDist: +hi.toFixed(2), capped, ...rep};
}

// what the shot actually delivers: in-frame fraction, and how big a character is
export function frameReport(C, cam, pos, aim, all, S) {
  const F = cam.F, fov = F.fov, aspect = F.aspect;
  let inFrame = 0, zmin = Infinity, zmax = 0;
  for (const p of all) {
    const q = project(pos, aim, fov, aspect, p);
    if (!q.behind && Math.abs(q.sx) <= 1 && Math.abs(q.sy) <= 1) inFrame++;
    if (!q.behind) { zmin = Math.min(zmin, q.z); zmax = Math.max(zmax, q.z); }
  }
  const frameH = 768;
  return {
    samples: all.length,
    inFrameFrac: +(inFrame / all.length).toFixed(4),
    zNear: +zmin.toFixed(2), zFar: +zmax.toFixed(2),
    charPxNear: Math.round(charPx(fov, zmin, F.charH, frameH)),
    charPxFar: Math.round(charPx(fov, zmax, F.charH, frameH)),
    clip: [F.clip[0], F.clip[1]],
  };
}

// ---------------------------------------------------------------- the cuts ---
// A cut is derived, never authored: walk each map edge's ownership sequence
// (owner of landmark A, then each t-segment, then owner of landmark B) and emit a
// pair of directed cuts wherever consecutive owners differ. So "the camera
// changes where the walk network crosses a region boundary" is a THEOREM about
// the ownership table, not a list somebody maintained by hand.
export function derivedCuts(C) {
  const cuts = [];
  for (const k of Object.keys(C.MEDGE)) {
    const E = C.MEDGE[k], segs = C.edgeOwner[k] || [];
    if (!segs.length) continue;
    const seq = [{t: 0, cam: C.lmOwner[E.rec.from] || null, what: `landmark ${E.rec.from}`}];
    for (const s of segs) seq.push({t: s.t0, cam: s.cam, what: `${k}@${s.t0}..${s.t1}`, seg: s});
    seq.push({t: 1, cam: C.lmOwner[E.rec.to] || null, what: `landmark ${E.rec.to}`});
    for (let i = 0; i < seq.length - 1; i++) {
      const a = seq[i], b = seq[i + 1];
      if (!a.cam || !b.cam || a.cam === b.cam) continue;
      // WHERE the seam sits. At an ENDPOINT transition it is cutOffset metres out
      // along the edge from the landmark's pad, so the seam is on the path and not
      // on the pad you are standing on (and never past the edge's midpoint, which
      // keeps both cuts of a short edge apart). At an INTERNAL t-boundary — a split
      // edge, a boardwalk shared by two shots — it is exactly the authored boundary.
      const off = C.D.cutOffset / Math.max(E.L, 0.01);
      const endpoint = i === 0 ? 'from' : i === seq.length - 2 ? 'to' : null;
      const t = endpoint === 'from' ? Math.min(off, 0.5)
              : endpoint === 'to' ? Math.max(1 - off, 0.5)
              : b.t;
      // `endpoint` tells the consumer which way it may SLIDE this seam looking for a
      // spot where the path is straight enough to cut cleanly (see the generator): out
      // from the pad, back from the pad, or a little either side of an authored split.
      cuts.push({edge: k, E, t, endpoint, from: a.cam, to: b.cam,
                 whatFrom: a.what, whatTo: b.what});
    }
  }
  return cuts;
}

// ------------------------------------------- WHICH SHOT OWNS A POINT (SHARED) --
// The positional companion to the seam edges. Seams stay the primary mechanism and give
// play its precise, authored cut points; this answers a different question — "given
// where the player actually IS, whose shot is that?" — which is what catches travel that
// never crossed a seam at all: sliding down the slope beside a flight, a jump, a future
// knockback. Without it a player can leave frame and the camera never follows, which is
// the worst defect the FF grammar has.
//
// The region is the OWNED WALK MESHES THEMSELVES, as axis-aligned boxes — deliberately
// not a convex hull. A hull of the waterfront's L-shaped boardwalk would swallow the
// river, and a hull of any two neighbours on one tier overlaps generously; boxes are
// exact, so "the positional answer agrees with record ownership" holds by construction
// rather than by luck. Boxes are RUNTIME coords [x0, z0, x1, z1, yTop]; yTop is where
// feet stand.
export function shotRegions(C, glbPath, meshes) {
  const list = meshes || walkMeshes(glbPath).meshes;
  const out = {};
  for (const m of list) {
    const owner = m.owner || ownerOfWalk(C, m.name, m.center).cam;
    if (!owner) continue;
    (out[owner] = out[owner] || []).push([
      +m.rt.min[0].toFixed(2), +m.rt.min[2].toFixed(2),
      +m.rt.max[0].toFixed(2), +m.rt.max[2].toFixed(2),
      +m.rt.max[1].toFixed(2)]);
  }
  return C.cams.filter((c) => out[c.id]).map((c) => ({id: c.id, boxes: out[c.id]}));
}
// Dilated in xz because a player stands with a body radius on ribbons only ~2 m wide,
// and gated in HEIGHT because this town stacks — Westweave is directly under the quay,
// so an xz-only test would put a player on the quay deck into the shot beneath it.
export function inShot(region, p, pad, vTol) {
  const d = pad === undefined ? 0.6 : pad, t = vTol === undefined ? 1.2 : vTol;
  for (const b of region.boxes)
    if (p[0] >= b[0] - d && p[0] <= b[2] + d && p[2] >= b[1] - d && p[2] <= b[3] + d &&
        Math.abs(p[1] - b[4]) <= t) return true;
  return false;
}
// 3D distance from p to a region's nearest box (0 when inside one).
export function shotDist(region, p) {
  let best = Infinity;
  for (const b of region.boxes) {
    const dx = Math.max(b[0] - p[0], 0, p[0] - b[2]);
    const dz = Math.max(b[1] - p[2], 0, p[2] - b[3]);
    const dy = p[1] - b[4];
    const d = Math.sqrt(dx * dx + dz * dz + dy * dy);
    if (d < best) best = d;
  }
  return best;
}
// The NEAREST shot's ground, for a player who is on nobody's: the repro slid down the
// slope BESIDE the shop street and came to rest off every ribbon, so containment alone
// had nothing to correct to. Wherever a player ends up, some shot owns the ground
// closest to them, and that is the shot that should be looking at them.
export function nearestShot(regions, p) {
  let id = null, bd = Infinity;
  for (const r of regions) { const d = shotDist(r, p); if (d < bd) { bd = d; id = r.id; } }
  return {id, dist: bd};
}
// The shot whose region contains p, preferring the one whose surface is nearest in
// height (the tie-break that matters in a stacked town). null when p is on nobody's
// ground — callers fall back to nearestShot.
export function shotAt(regions, p, pad, vTol) {
  let best = null, bd = Infinity;
  const d = pad === undefined ? 0.6 : pad, t = vTol === undefined ? 1.2 : vTol;
  for (const r of regions) for (const b of r.boxes) {
    if (p[0] < b[0] - d || p[0] > b[2] + d || p[2] < b[1] - d || p[2] > b[3] + d) continue;
    const dy = Math.abs(p[1] - b[4]);
    if (dy > t) continue;
    if (dy < bd) { bd = dy; best = r.id; }
  }
  return best;
}

// ---------------------------------------------------- cut geometry (SHARED) ---
// WHERE a seam physically goes, how wide its band is, and where you arrive on each
// side. This lives here, and not in the scene-graph generator, because TWO consumers
// need the same answer and a second implementation would be a second truth:
//   * tools/cine_solve.mjs frames each shot around its region PLUS every arrival that
//     lands in it — "entrances and exits must be in frame" is only enforceable if the
//     solver knows where they are;
//   * tools/scenegraph_derive.mjs turns them into the runtime's edges.
// Needs the town's walk geometry, so it takes the bundle path.
export function cutGeometry(C, glbPath, warn) {
  const G = loadGlb(glbPath);
  const W = warn || (() => {});
  const WALK = /^walk/i;
  const D = C.D;
  const clear = D.cutClearance !== undefined ? D.cutClearance : 1.0;
  const cvt = D.cutVTol !== undefined ? D.cutVTol : 2.0;
  const hClear = D.cutHeightClear !== undefined ? D.cutHeightClear : 0.75;
  const slide = (D.cutSlide !== undefined ? D.cutSlide : 6);

  // nearest walk-surface height at a runtime xz, or null
  const walkY = (x, z, near) => {
    const ys = G.tops(WALK, x, z);
    if (!ys.length) return null;
    let b = ys[0];
    for (const y of ys) if (Math.abs(y - near) < Math.abs(b - near)) b = y;
    return b;
  };
  // HALF-WIDTH OF THE SEAM. A camera boundary has to span the frontier between the two
  // regions, because on an 11 m harbour deck a trigger you can side-step is a camera
  // that never changes — so it is MEASURED off the walk surface, not guessed.
  //
  // But it must be measured over THIS crossing's own ground, and the first version was
  // not: a free perpendicular sweep at the head of the Valley Gate stair walked straight
  // out onto the RIM ROAD, which happens to run alongside, and produced a 4 m band. A
  // player heading for the cargo winch then crossed it and got cut to the stairwell shot
  // — found by the playthrough, invisible to every static check.
  //
  // The corridor is therefore this edge's OWN ribbon plus its two endpoint areas: sweep
  // only over `walk_e_<a>__<b>_*`, `walk_pad_<a|b>` and `walk_lm_<a|b>`, and stop the
  // moment the ground under the sweep belongs to some other path. That keeps the wide
  // frontier where the frontier really is wide (two adjacent deck pads) and refuses to
  // borrow width from a road that merely passes by.
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const corridorRe = (E) => new RegExp('^(walk_e_' + esc(E.rec.from) + '__' + esc(E.rec.to) +
    '_|walk_(pad|lm)_(' + esc(E.rec.from) + '|' + esc(E.rec.to) + ')(\\.\\d+)?$)', 'i');
  const halfWidth = (at, n, E) => {
    const re = corridorRe(E), perp = [-n[1], n[0]];
    const reach = (s) => { let d = 0;
      for (let k = 1; k <= 40; k++) {
        const q = 0.35 * k;
        const ys = G.tops(re, at[0] + perp[0] * q * s, at[2] + perp[1] * q * s);
        if (!ys.some((y) => Math.abs(y - at[1]) <= 1.3)) break;
        d = q;
      }
      return d; };
    return Math.min(Math.max(Math.max(reach(1), reach(-1)) + D.cutWidthPad, 1.4), D.cutWidthMax);
  };

  // FOREIGN PATHS INSIDE THE BAND. Narrowing the corridor was necessary but not
  // sufficient: at the head of the gate stair the RIM ROAD passes within 1.5 m across
  // and only 1.1 m above the flight, so the two paths physically overlap in plan and NO
  // band at that seam can avoid catching the road — a player walking to the cargo winch
  // still got cut to the stairwell. The seam has to MOVE, so the placer needs to know
  // when a candidate sits on top of somebody else's path.
  // Every walk mesh, in runtime coords, so a candidate band can be tested against them.
  const allWalk = [];
  for (const o of G.nodesNamed(/^walk/i)) {
    const b = G.nodeBox(o.i);
    if (b) allWalk.push({name: o.name, min: b.min, max: b.max});
  }
  const foreignInBand = (at, n, w, E) => {
    const re = corridorRe(E), perp = [-n[1], n[0]];
    const names = new Set();
    for (let a = -D.cutThickness; a <= D.cutThickness + 1e-9; a += D.cutThickness) {
      for (let q = -w; q <= w + 1e-9; q += 0.4) {
        const x = at[0] + n[0] * a + perp[0] * q, z = at[2] + n[1] * a + perp[1] * q;
        for (const m of allWalk) {
          if (re.test(m.name)) continue;                      // our own corridor: fine
          if (x < m.min[0] - 0.05 || x > m.max[0] + 0.05) continue;
          if (z < m.min[2] - 0.05 || z > m.max[2] + 0.05) continue;
          if (Math.abs(m.max[1] - at[1]) > cvt) continue;      // outside the band's height gate
          names.add(m.name);
        }
      }
    }
    return names;
  };
  // which map edges a player can actually WALK. The map carries three connections with
  // no walkable geometry (the cargo winch and two maintenance ladders), and a camera
  // boundary on a path nobody can walk is dead data — so the answer comes from the
  // shipped GLB, not from a list in a tool.
  //
  // THE QUESTION IS WALKABILITY, NOT MESH NAMING, and for a while those were the same
  // thing by accident. An edge normally ships its own `walk_e_<a>__<b>_*` ribbon, so
  // "has a ribbon" stood in for "is walkable" and nobody paid for the difference.
  // Emberbrook's blockout broke the proxy in the honest direction: an edge whose walk
  // surface is ENTIRELY covered by an area floor or by its endpoints' pads emits no
  // ribbon of its own — the blockout calls those SWALLOWED, and a swallowed edge is MORE
  // walkable, not less. Two of Emberbrook's separate two cameras (`barn__gate-court`,
  // `brook-bridge__square-plaza`), and under the naming test both of their cuts were
  // silently dropped: the player walks the barn into the gate court with the camera never
  // changing, and `sgCorrect` fires on a normal route, which is seam-canon §2's hard zero.
  // So ask the surface. The winch and the ladders still fail — they have no walk surface
  // anywhere along them, which is why they were excluded in the first place.
  const ribbons = new Set();
  for (const o of G.nodesNamed(/^walk_e_/i)) {
    const m = /^walk_e_(.+?)__(.+?)_(?:l\d+|t\d+|landing)/i.exec(o.name);
    if (m) ribbons.add(`${m[1]}__${m[2]}`);
  }
  // ...and the test is: IS THIS EDGE'S OWN CORRIDOR UNDER ITS MIDDLE. Both halves of that
  // sentence were bought with a false positive apiece, on the first two runs:
  //
  //   OWN corridor — the endpoints' pads and area floors, the same regexp the seam's own
  //   width is measured over. A bare "is there ground below" admitted Dellhollow's
  //   `weave-huts__fish-dock`, a MAINTENANCE LADDER off a stilt village that happens to
  //   hang over the drying decks, and placed a camera boundary on a route nobody can
  //   walk. A third party's floor passing beneath an edge is not that edge being walkable.
  //
  //   MIDDLE THIRD, by majority. Every edge in every map stands on its endpoints' pads at
  //   both ends by construction, and a pad is ~2.6 m across, so sampling near the ends
  //   calls the whole map walkable: the same ladder came back a second time on its own
  //   foot, 1.6 m from the fish dock. A SWALLOWED edge is covered by its own ground
  //   ACROSS THE MIDDLE — that is what swallowed means; a ladder is covered only where it
  //   lands. Measured, both towns: the two ladders and the winch score 0 of 5 in the
  //   middle third, Emberbrook's `brook-bridge__square-plaza` scores 5 (the plaza floor
  //   runs under all of it) and `barn__gate-court` scores 3 (the gate court's flagstones
  //   reach half way down it and the north lane's own ribbon overshoots to meet them).
  for (const k of Object.keys(C.MEDGE)) {
    if (ribbons.has(k)) continue;
    const E = C.MEDGE[k];
    const re = corridorRe(E);
    let covered = 0;
    for (const t of [1 / 3, 5 / 12, 1 / 2, 7 / 12, 2 / 3]) {
      const p = m2r(edgePoint(E, t));
      if (G.tops(re, p[0], p[2]).some((y) => Math.abs(y - p[1]) <= cvt)) covered++;
    }
    if (covered >= 3) ribbons.add(k);
  }

  // which camera owns the walk surface under a runtime point (for validating overrides)
  const ownerOfWalkAt = (p) => {
    let best = null, bd = 1e9;
    for (const m of allWalk) {
      if (p[0] < m.min[0] - 0.4 || p[0] > m.max[0] + 0.4) continue;
      if (p[2] < m.min[2] - 0.4 || p[2] > m.max[2] + 0.4) continue;
      const dy = Math.abs(p[1] - m.max[1]);
      if (dy > 1.0 || dy >= bd) continue;
      const cen = [(m.min[0] + m.max[0]) / 2, -(m.min[2] + m.max[2]) / 2, m.max[1]];
      bd = dy; best = {name: m.name, cam: ownerOfWalk(C, m.name, cen).cam};
    }
    return best;
  };
  const overrideNotes = [];
  const out = [], noRibbon = [];
  for (const c of derivedCuts(C)) {
    if (!ribbons.has(c.edge)) {
      noRibbon.push(`${c.from}->${c.to} on '${c.edge}' (no walk ribbon — the map's cargo winch and two maintenance ladders are not walkable; no camera boundary placed)`);
      continue;
    }
    const E = c.E;
    // SEAM PLACEMENT. derivedCuts says WHERE ownership changes; this decides where on
    // the path the trigger goes, and it is not a fixed offset. A HAIRPIN is the problem
    // case: at the turn of a switchback both arrivals sit on the same side of the
    // band's normal, so the cut either fires twice or (worse, and observed) never arms
    // at all. So SLIDE the seam along the window ownership allows and keep the position
    // where the path can put both arrivals genuinely OUTSIDE the band — clear across
    // the seam, or clear in height, which on a flight separates just as well.
    const sl = slide / Math.max(E.L, 0.01);
    const win = c.endpoint === 'from' ? [c.t, Math.min(0.5, c.t + sl)]
              : c.endpoint === 'to'   ? [Math.max(0.5, c.t - sl), c.t]
              : [Math.max(0, c.t - sl * 0.25), Math.min(1, c.t + sl * 0.25)];
    const reach = (tc, nn, sign) => {
      const p0 = m2r(edgePoint(E, tc)), step = 0.15 / Math.max(E.L, 0.01);
      let best = -99, hit = null;
      for (let k = 1; k <= 80; k++) {
        const tt = tc + sign * step * k;
        if (tt < 0 || tt > 1) break;
        const p = m2r(edgePoint(E, tt));
        const along = Math.abs((p[0] - p0[0]) * nn[0] + (p[2] - p0[2]) * nn[1]) - D.cutThickness;
        const dh = Math.abs(p[1] - p0[1]) - cvt;
        const m = Math.max(along - clear, dh - hClear);
        if (m > best) { best = m; }
        if (m >= 0) { hit = p; return {m, p, t: tt}; }
      }
      return {m: best, p: null, t: null};
    };
    // Rank candidates on TWO requirements, in this order:
    //   1. no FOREIGN path inside the band (a seam that overlaps somebody else's route
    //      fires while the player is walking that other route — the rim-road bug);
    //   2. both arrivals genuinely outside the band (hysteresis).
    // Foreign overlap comes first because it is a wrong cut, and a wrong cut is worse
    // than a cut whose arrival is only just clear.
    let seam = null;
    const nCand = Math.max(1, Math.ceil((win[1] - win[0]) * E.L / 0.25));
    // ORDER THE CANDIDATES BY DISTANCE FROM THE AUTHORED POSITION, and take the
    // nearest acceptable one. The window says how far a seam MAY slide to dodge a
    // hairpin or a neighbour's path; it never said sliding was free. Scanning it
    // end to end and keeping the FIRST acceptable spot made every 'to'-endpoint
    // seam and every authored @t split slide the whole window by default, because
    // the window's near end is its far end for those two cases. That is why five of
    // Dellhollow's cuts sat at exactly t=0.500: not because 0.500 was right, but
    // because it was as far from the landmark as ownership allowed. The player felt
    // it as a camera that changed halfway down a flight of stairs, and as two cuts
    // mid-plank on a bridge whose ends were the obvious places to cut.
    const order = [];
    for (let i = 0; i <= nCand; i++)
      order.push(win[0] + (win[1] - win[0]) * (nCand ? i / nCand : 0));
    order.sort((a, b) => Math.abs(a - c.t) - Math.abs(b - c.t));
    for (const tc of order) {
      const dmc = edgeDir(E, tc), nc = [dmc[0], -dmc[1]];   // map xy dir -> runtime xz
      const pc = m2r(edgePoint(E, tc));
      const yc = walkY(pc[0], pc[2], pc[1]);
      if (yc != null) pc[1] = yc;
      // Widest band that stays off other people's paths. Spanning the frontier and not
      // catching a neighbour are both requirements and they compete at a junction, where
      // four routes converge on one deck. Width is the cheaper thing to give up: a band
      // narrow enough to side-step only RISKS a missed cut (which leaves you in the shot
      // you were already in), while a band that overlaps a neighbour GUARANTEES a wrong
      // one for everybody walking it.
      let wc = halfWidth(pc, nc, E), foreign = foreignInBand(pc, nc, wc, E);
      while (foreign.size && wc > 1.4) {
        wc = Math.max(1.4, wc - 0.5);
        foreign = foreignInBand(pc, nc, wc, E);
      }
      const f = reach(tc, nc, +1), b = reach(tc, nc, -1);
      const score = Math.min(f.m, b.m);
      // ON THE NETWORK, first of all. A candidate with no walk surface under it is not a
      // worse seam, it is not a seam: the trigger sits in a hole and the arrivals derived
      // from it are computed against nothing. Emberbrook's plaza is the case that named
      // it — a cell-grid floor with the Heartlight pedestal's footprint cut out of its
      // centre, so a seam offset in from the rim can land inside the hero prop.
      const onNet = walkY(pc[0], pc[2], pc[1]) != null;
      const cand = {t: tc, n: nc, score, f, b, w: wc, foreign: [...foreign], onNet};
      const better = !seam ||
        (cand.onNet !== seam.onNet ? cand.onNet : false) ||
        (cand.onNet === seam.onNet && (
          (cand.foreign.length < seam.foreign.length) ||
          (cand.foreign.length === seam.foreign.length && score > seam.score)));
      if (better) seam = cand;
      // clean, separated AND on the network: take it
      if (cand.onNet && !cand.foreign.length && score >= 0) break;
    }
    if (seam.foreign.length)
      W(`cut ${c.from}<->${c.to} on '${c.edge}': every seam position in t=[${win[0].toFixed(3)},${win[1].toFixed(3)}] overlaps another path (${seam.foreign.slice(0, 3).join(', ')}) — a player walking THAT path will be cut; VERIFY THIS SEAM`);
    if (seam.score < 0)
      W(`cut ${c.from}<->${c.to} on '${c.edge}': no seam position in t=[${win[0].toFixed(3)},${win[1].toFixed(3)}] fully separates the two sides (best margin ${seam.score.toFixed(2)}u) — VERIFY THIS SEAM`);

    const at = m2r(edgePoint(E, seam.t));
    const ay = walkY(at[0], at[2], at[1]);
    if (ay == null) W(`cut ${c.from}->${c.to} on '${c.edge}'@${seam.t.toFixed(3)}: the seam is off the walk network`);
    else at[1] = ay;
    const band = {n: [Math.round(seam.n[0] * 1e4) / 1e4, Math.round(seam.n[1] * 1e4) / 1e4],
                  t: D.cutThickness, w: Math.round(seam.w * 100) / 100};
    const arrive = (side) => {
      let p = side.p;
      if (!p) {
        p = m2r(edgePoint(E, Math.max(0, Math.min(1, seam.t + (side === seam.f ? 1 : -1) * D.cutBackoff / Math.max(E.L, 0.01)))));
        W(`cut ${c.from}<->${c.to} on '${c.edge}': arrival fell back to arc-length back-off on one side`);
      } else p = p.slice();
      const y = walkY(p[0], p[2], p[1]);
      if (y == null) W(`cut ${c.from}<->${c.to} on '${c.edge}': arrival (${p[0].toFixed(1)},${p[2].toFixed(1)}) is off the walk network`);
      else p[1] = y;
      return r3(p);
    };
    // ---- AUTHORED ARRIVAL OVERRIDES ------------------------------------------
    // An arrival is DERIVED: the first point along the path that is clear of the band.
    // That is the right default and it is blind to one thing — what the camera can SEE.
    // A derived arrival can land a player behind a house, under the flight they just
    // walked down, or inside the shot's own hero prop, and no amount of clearance fixes
    // it because clearance is a fact about the BAND, not about the sightline.
    //
    // So a shot may name a better standing point, in its own record, per incoming edge:
    //     "arrivals": { "<from>__<to>:<sending camera>": [x, y, z] }   runtime coords
    // The key carries the sending camera because a shot can receive TWO arrivals on one
    // edge (the Crossing is entered from both ends of the same bridge), and "the edge"
    // alone would silently pick one.
    //
    // AN OVERRIDE IS A PROPOSAL, NOT A FACT. Every one is checked below and REJECTED
    // loudly if it is off the walk network, on another camera's ground (which would put
    // the player somewhere the positional safety net immediately corrects away from), or
    // not clear of the band it just crossed (which re-fires the cut). The first six ever
    // authored included one that sat on the neighbouring shot's road and one whose
    // coordinate had never been converted out of map order; both were caught here.
    let spawnTo = arrive(seam.f), spawnFrom = arrive(seam.b);
    const ovr = (recvId, sendId, derived) => {
      const cam = C.byId[recvId];
      const key = `${c.edge}:${sendId}`;
      const p = cam && cam.arrivals && cam.arrivals[key];
      if (!p) return derived;
      const bad = (why) => { W(`arrival override ${recvId} '${key}' REJECTED: ${why}`); return derived; };
      if (!Array.isArray(p) || p.length !== 3) return bad('not an [x, y, z] runtime point');
      const y = walkY(p[0], p[2], p[1]);
      if (y == null || Math.abs(y - p[1]) > 0.6)
        return bad(`off the walk network (nearest surface ${y == null ? 'none' : y.toFixed(2)}` +
                   `, authored ${p[1]}) — is the coordinate still in MAP order [x, y, h]?`);
      const own = ownerOfWalkAt(p);
      if (own && own.cam !== recvId)
        return bad(`stands on '${own.cam}' ground (${own.name}), not ${recvId}'s — the ` +
                   'positional safety net would correct the camera straight back');
      const px = p[0] - at[0], pz = p[2] - at[2];
      const along = px * band.n[0] + pz * band.n[1];
      const across = -px * band.n[1] + pz * band.n[0];
      const dy = Math.abs(p[1] - at[1]);
      if (Math.abs(along) <= band.t && Math.abs(across) <= band.w && dy <= cvt)
        return bad('is INSIDE the band it just crossed — the cut would re-fire');
      const clr = Math.max(Math.abs(along) - band.t, dy - cvt);
      const dpx = derived[0] - at[0], dpz = derived[2] - at[2];
      const dclr = Math.max(Math.abs(dpx * band.n[0] + dpz * band.n[1]) - band.t,
                            Math.abs(derived[1] - at[1]) - cvt);
      // cutClearance is the TARGET; the FLOOR is one stride (0.5 m), below which walking
      // on re-enters the band and the cut re-fires. seam-canon §1 draws that line, and an
      // override that trades a little clearance for an arrival the camera can actually SEE
      // is a good trade — so below-target WARNS and below-floor REJECTS. Anything else
      // would refuse a one-metre nudge that takes an arrival from 31% occluded to 2%.
      const FLOOR = 0.5;
      if (clr < FLOOR)
        return bad(`clears the band by only ${clr.toFixed(2)} m (hard floor ${FLOOR} m) — ` +
                   'one step forward would re-fire the cut');
      if (clr < clear - 1e-6)
        W(`arrival override ${recvId} '${key}': clears ${clr.toFixed(2)} m, under the ` +
          `${clear} m target (derived point had ${dclr.toFixed(2)} m) — above the ${FLOOR} m ` +
          'floor, so ACCEPTED; the trade is band clearance for a visible arrival');
      overrideNotes.push(`${recvId} <- ${sendId} on ${c.edge}: arrival moved ` +
        `${Math.hypot(p[0]-derived[0], p[1]-derived[1], p[2]-derived[2]).toFixed(2)} m ` +
        `(clears ${clr.toFixed(2)} m)`);
      return r3(p.slice());
    };
    spawnTo = ovr(c.to, c.from, spawnTo);
    spawnFrom = ovr(c.from, c.to, spawnFrom);

    out.push({edge: c.edge, E, t: seam.t, from: c.from, to: c.to,
              whatFrom: c.whatFrom, whatTo: c.whatTo,
              at: r3(at), band, margin: +seam.score.toFixed(3),
              spawnTo, spawnFrom,
              vTol: cvt});
  }
  return {cuts: out, noRibbon, walkY, halfWidth, ribbons, overrideNotes};
}
