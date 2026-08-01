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
import {loadGlb} from './glb_read.mjs';

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

// ------------------------------------------------------------------- the BVH --
// Median split on the longest axis, leaves of <= 8 triangles. Built once over the whole
// bundle; every ray in the sweep walks it. Triangles are stored flat (9 floats) because
// 145k arrays of arrays is where Node's allocator starts to be the measurement.
const G = loadGlb(GLB);
const RE = NOBARS ? /^(?!bar_)/ : /./;
const tri = [];
for (const T of G.tris(RE)) tri.push(...T[0], ...T[1], ...T[2]);
const NT = tri.length / 9;
const idx = new Int32Array(NT); for (let i = 0; i < NT; i++) idx[i] = i;
const cx = new Float64Array(NT), cy = new Float64Array(NT), cz = new Float64Array(NT);
for (let i = 0; i < NT; i++) {
  const o = i * 9;
  cx[i] = (tri[o] + tri[o + 3] + tri[o + 6]) / 3;
  cy[i] = (tri[o + 1] + tri[o + 4] + tri[o + 7]) / 3;
  cz[i] = (tri[o + 2] + tri[o + 5] + tri[o + 8]) / 3;
}
const nodes = [];                                   // {lo,hi,start,count,left,right}
function build(start, count) {
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (let k = start; k < start + count; k++) {
    const o = idx[k] * 9;
    for (let v = 0; v < 3; v++) for (let a = 0; a < 3; a++) {
      const x = tri[o + v * 3 + a];
      if (x < lo[a]) lo[a] = x;
      if (x > hi[a]) hi[a] = x;
    }
  }
  const me = nodes.length;
  nodes.push({lo, hi, start, count, left: -1, right: -1});
  if (count <= 8) return me;
  const ext = [hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]];
  const ax = ext[0] >= ext[1] && ext[0] >= ext[2] ? 0 : (ext[1] >= ext[2] ? 1 : 2);
  const key = ax === 0 ? cx : ax === 1 ? cy : cz;
  const slice = Array.from(idx.subarray(start, start + count)).sort((a, b) => key[a] - key[b]);
  for (let k = 0; k < count; k++) idx[start + k] = slice[k];
  const mid = count >> 1;
  nodes[me].left = build(start, mid);
  nodes[me].right = build(start + mid, count - mid);
  nodes[me].count = 0;                              // interior: no triangles of its own
  return me;
}
if (NT) build(0, NT);

function slabHit(n, ox, oy, oz, ix, iy, iz, tmax) {
  let t0 = 0, t1 = tmax;
  let a = (n.lo[0] - ox) * ix, b = (n.hi[0] - ox) * ix;
  if (a > b) { const t = a; a = b; b = t; } t0 = a > t0 ? a : t0; t1 = b < t1 ? b : t1;
  if (t0 > t1) return false;
  a = (n.lo[1] - oy) * iy; b = (n.hi[1] - oy) * iy;
  if (a > b) { const t = a; a = b; b = t; } t0 = a > t0 ? a : t0; t1 = b < t1 ? b : t1;
  if (t0 > t1) return false;
  a = (n.lo[2] - oz) * iz; b = (n.hi[2] - oz) * iz;
  if (a > b) { const t = a; a = b; b = t; } t0 = a > t0 ? a : t0; t1 = b < t1 ? b : t1;
  return t0 <= t1;
}
const stack = new Int32Array(128);
// Moller-Trumbore, any-hit (occlusion), runtime coords.
function occluded(o, d, tmax) {
  if (!NT) return false;
  const ix = 1 / (d[0] || 1e-12), iy = 1 / (d[1] || 1e-12), iz = 1 / (d[2] || 1e-12);
  let sp = 0; stack[sp++] = 0;
  while (sp) {
    const n = nodes[stack[--sp]];
    if (!slabHit(n, o[0], o[1], o[2], ix, iy, iz, tmax)) continue;
    if (n.count) {
      for (let k = n.start; k < n.start + n.count; k++) {
        const p = idx[k] * 9;
        const e1x = tri[p + 3] - tri[p], e1y = tri[p + 4] - tri[p + 1], e1z = tri[p + 5] - tri[p + 2];
        const e2x = tri[p + 6] - tri[p], e2y = tri[p + 7] - tri[p + 1], e2z = tri[p + 8] - tri[p + 2];
        const px = d[1] * e2z - d[2] * e2y, py = d[2] * e2x - d[0] * e2z, pz = d[0] * e2y - d[1] * e2x;
        const det = e1x * px + e1y * py + e1z * pz;
        if (det > -1e-9 && det < 1e-9) continue;
        const inv = 1 / det;
        const tx = o[0] - tri[p], ty = o[1] - tri[p + 1], tz = o[2] - tri[p + 2];
        const u = (tx * px + ty * py + tz * pz) * inv;
        if (u < 0 || u > 1) continue;
        const qx = ty * e1z - tz * e1y, qy = tz * e1x - tx * e1z, qz = tx * e1y - ty * e1x;
        const v = (d[0] * qx + d[1] * qy + d[2] * qz) * inv;
        if (v < 0 || u + v > 1) continue;
        const t = (e2x * qx + e2y * qy + e2z * qz) * inv;
        if (t > 1e-4 && t < tmax) return true;
      }
    } else { stack[sp++] = n.left; stack[sp++] = n.right; }
  }
  return false;
}
// map (x, y, z-up) -> runtime (x, z, -y), which is the frame the GLB is in
const m2r = (p) => [p[0], p[2], -p[1]];
function seenFrac(posMap, probesMap) {
  if (!probesMap.length) return null;
  const o = m2r(posMap);
  let n = 0;
  for (const q of probesMap) {
    const t = m2r(q);
    const dx = t[0] - o[0], dy = t[1] - o[1], dz = t[2] - o[2];
    const L = Math.hypot(dx, dy, dz);
    if (L < 1e-4) continue;
    if (!occluded(o, [dx / L, dy / L, dz / L], L - 0.35)) n++;
  }
  return n / probesMap.length;
}

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
const out = {town: TOWN, bundle: WALK_BUNDLE, occluders: NT, nobars: NOBARS,
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
    rows.push({yaw, pitch, dist: s.dist, capped: !!s.capped, inFrame: s.inFrameFrac,
               charPxFar: s.charPxFar, charPxNear: s.charPxNear, zFar: s.zFar,
               pos: s.pos, aim: s.aim, vis: seenFrac(s.pos, probes)});
  }
  // RANKED ON VISIBILITY, because that is the question the solver cannot answer and the
  // one that has repeatedly been wrong. Everything else is printed beside it rather than
  // folded into a score: a single number would hide which constraint a row is failing,
  // and these constraints are not commensurable (a shot at 100% visible and 31 px is a
  // different problem from one at 40% and 60 px).
  rows.sort((a, b) => b.vis - a.vis || b.charPxFar - a.charPxFar);
  out.shots[cam.id] = {probes: probes.length, walkMeshes: mine.length, rows};
  const best = rows.filter((r) => !r.capped && r.charPxFar >= CHAR_PX_MIN);
  console.log(`\n=== ${cam.id}  (${mine.length} walk meshes, ${probes.length} probes, ` +
              `authored yaw ${cam.F.yaw} pitch ${cam.F.pitch}) ===`);
  console.log('   yaw  pitch   dist  cap  frame%  charPx n..f   visible');
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
console.log(`\nswept ${YAWS.length}x${PITCHES.length} angles over ${NT} occluder triangles ` +
            `in ${((Date.now() - t0) / 1000).toFixed(1)}s${NOBARS ? '  (bar_ meshes excluded)' : ''}`);
const JSONOUT = opt('--json', null);
if (JSONOUT) { fs.writeFileSync(JSONOUT, JSON.stringify(out, null, 1)); console.log(`wrote ${JSONOUT}`); }
