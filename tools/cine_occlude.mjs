// cine_occlude.mjs — the ray-caster the camera tools share, and the NEAR-FIELD GATE.
//
//   const O = occluders('assets/scenes/emb-townwalk/scene.glb');
//   O.seenFrac(posMap, probesMap)      what fraction of a region's probes are visible
//   O.nearField(posMap, aimMap, fov, aspect)  {frac, dist, standoff, ndc, hits}
//
// WHY A SECOND VISIBILITY NUMBER EXISTS, AND WHY THE FIRST ONE CANNOT REPLACE IT.
// `seenFrac` casts rays AT THE SUBJECT: it answers "can this camera see the ground it
// owns", and it is the number every framing note in this project quotes. It is blind by
// construction to anything that does not stand between the lens and a probe — so a slab
// one metre in front of the camera, filling the picture, off to the side of every ray
// that matters, scores ZERO against it. The dressing lane hit exactly that on a district
// stand: subject visibility read **89% clear** while a wall occupied the frame, and the
// near-field bundle read **0.22**. Their finding, ported here verbatim, because the
// camera lane's solver has the same blind spot and its own compositions are chosen by
// the same number.
//
// THE BUNDLE IS THIRTEEN RAYS THROUGH THE FRUSTUM, not at the subject: the centre, the
// four corners, the four edge midpoints, and the four half-corners. Thirteen rather than
// four because corners alone miss a column dead-centre, and rather than a full grid
// because this runs inside a 468-angle sweep — a cheap veto, not a coverage measurement.
//
// THE REDUCTION IS COVERAGE, NOT NEAREST-HIT, and the thresholds are read off Dellhollow's
// sixteen accepted shots rather than assumed. See `nearField` below for the calibration
// table, the two reductions that were tried and measured WORSE, and why the floor a
// camera is aimed at is not a thing covering its frame.
//
// WHAT IT IS NOT: a composition test. A shot can clear the near field, hold every probe
// and still be a bad frame; the bake's own render remains the only thing that knows. What
// the pair closes is the class the coordinator named — that a CLEAR FRACTION IS NOT A
// COMPOSITION TEST, in both of its halves: `seenFrac` misses what covers the FRAME, and
// the subject-in-frame check (in cine_sweep) misses what the region's own samples never
// pointed at.
import path from 'path';
import {PUB, camBasis} from './cine_regions.mjs';
import {loadGlb} from './glb_read.mjs';

const RAD = Math.PI / 180;
export const NEAR_FIELD_MIN = 0.45;   // the dressing lane's threshold — the SOFT line
export const NEAR_HARD = 0.25;        // the HARD line, read off Dellhollow's accepted 16
export const NEAR_SOFT_RAYS = 2;      // rays allowed inside the soft line (the Crossing's)
// TERRAIN IS NOT A NEAR-FIELD BLOCKER — the ruling, and the measurement behind it.
//
// The dressing lane's district-square stand solves 45 m out at 67% clear and the gate named
// its blocker as `emb_ground_valley`: the hillside the village is built on. A gate that
// counts the ground a camera stands on and looks ACROSS would refuse every stand in a town
// on a rise, which is the same error as the bottom-of-frame case this instrument was
// already calibrated against once.
//
// IT IS EXCLUDED BY CLASS, NOT BY GEOMETRY, AND THE GEOMETRIC ALTERNATIVE IS REFUTED. The
// obvious rule — "a near-horizontal face is floor" — was measured and fails: on the arch's
// own low stand, `veg_emb_wood_08_crownA` returns |n.y| = 1.00. A tree crown is a faceted
// blob and some of its triangles face straight up, so horizontality would exempt exactly
// the thing this gate exists to catch. Naming the class is the honest discriminator in a
// project whose meshes are already named by what they are.
//
// AND EXCLUDING IT IS A PROVABLE NO-OP ON THE CALIBRATION SET: across the 27 accepted shots
// of both towns, terrain appears in ZERO of the rays landing inside 0.45 of a standoff.
// (Those rays are 3 tree crowns in Emberbrook and the lock's own water surface under
// Dellhollow's Crossing.) So the exclusion cannot move a verdict that was already made; it
// only stops a verdict that was about to be made wrongly.
//
// NOTHING IS LOST, because terrain occlusion of the SUBJECT is a different instrument's
// job: `seenFrac` casts AT the region, so a ridge standing between camera and subject tanks
// the visibility fraction and always did. The two numbers divide the work — seenFrac owns
// "can it see the ground", nearField owns "is something covering the picture" — and terrain
// belongs to the first.
export const TERRAIN_RE = /(^|_)(ground|terrain)(_|$)|valley_?ground|ground_valley|ground_far/i;

// the 13 frustum directions, in normalised screen coords
export const BUNDLE = [[0, 0],
  [-1, -1], [1, -1], [-1, 1], [1, 1],
  [-1, 0], [1, 0], [0, -1], [0, 1],
  [-0.5, -0.5], [0.5, -0.5], [-0.5, 0.5], [0.5, 0.5]];

const m2r = (p) => [p[0], p[2], -p[1]];      // map (x, y, z-up) -> runtime (x, z, -y)

export function occluders(bundleRel, opts) {
  const O = opts || {};
  const G = loadGlb(path.isAbsolute(bundleRel) ? bundleRel : path.join(PUB, bundleRel));
  const RE = O.re || /./;
  // PER-TRIANGLE PROVENANCE. A hit distance alone cannot be ruled on: "something is 3.5 m
  // from the lens" is a defect if it is a tree and a fact of life if it is the hillside the
  // village stands on. So each triangle remembers which node it came from, and the gate can
  // classify what it hit instead of only how near it is.
  const tri = [], triNode = [];
  for (const o of G.nodesNamed(RE)) {
    const before = tri.length / 9;
    for (const T of G.tris(new RegExp('^' + o.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '$')))
      tri.push(...T[0], ...T[1], ...T[2]);
    for (let i = before; i < tri.length / 9; i++) triNode[i] = o.name;
  }
  const NT = tri.length / 9;
  const idx = new Int32Array(NT); for (let i = 0; i < NT; i++) idx[i] = i;
  const cen = [new Float64Array(NT), new Float64Array(NT), new Float64Array(NT)];
  for (let i = 0; i < NT; i++) { const o = i * 9;
    for (let a = 0; a < 3; a++) cen[a][i] = (tri[o + a] + tri[o + 3 + a] + tri[o + 6 + a]) / 3; }
  // terrain triangles are marked once and skipped by the near-field caster only; seenFrac
  // still sees them, which is the division of labour TERRAIN_RE's note describes.
  const triTerrain = new Uint8Array(NT);
  for (let i = 0; i < NT; i++) if (TERRAIN_RE.test(triNode[i] || '')) triTerrain[i] = 1;
  const nodes = [];
  const build = (start, count) => {
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let k = start; k < start + count; k++) { const o = idx[k] * 9;
      for (let v = 0; v < 3; v++) for (let a = 0; a < 3; a++) { const x = tri[o + v * 3 + a];
        if (x < lo[a]) lo[a] = x; if (x > hi[a]) hi[a] = x; } }
    const me = nodes.length;
    nodes.push({lo, hi, start, count, left: -1, right: -1});
    if (count <= 8) return me;
    const ext = [hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]];
    const ax = ext[0] >= ext[1] && ext[0] >= ext[2] ? 0 : (ext[1] >= ext[2] ? 1 : 2);
    const key = cen[ax];
    const sl = Array.from(idx.subarray(start, start + count)).sort((a, b) => key[a] - key[b]);
    for (let k = 0; k < count; k++) idx[start + k] = sl[k];
    const mid = count >> 1;
    nodes[me].left = build(start, mid);
    nodes[me].right = build(start + mid, count - mid);
    nodes[me].count = 0;
    return me;
  };
  if (NT) build(0, NT);
  const stack = new Int32Array(128);

  // nearest hit distance along a ray, or Infinity. `anyHit` stops at the first one.
  const cast = (o, d, tmax, anyHit, skipTerrain) => {
    if (!NT) return Infinity;
    const inv = [1 / (d[0] || 1e-12), 1 / (d[1] || 1e-12), 1 / (d[2] || 1e-12)];
    let best = Infinity, bestTri = -1, sp = 0; stack[sp++] = 0;
    while (sp) {
      const n = nodes[stack[--sp]];
      let t0 = 0, t1 = Math.min(tmax, best);
      for (let a = 0; a < 3; a++) {
        let p = (n.lo[a] - o[a]) * inv[a], q = (n.hi[a] - o[a]) * inv[a];
        if (p > q) { const t = p; p = q; q = t; }
        if (p > t0) t0 = p; if (q < t1) t1 = q;
      }
      if (t0 > t1) continue;
      if (n.count) {
        for (let k = n.start; k < n.start + n.count; k++) {
          const p = idx[k] * 9;
          const e1 = [tri[p + 3] - tri[p], tri[p + 4] - tri[p + 1], tri[p + 5] - tri[p + 2]];
          const e2 = [tri[p + 6] - tri[p], tri[p + 7] - tri[p + 1], tri[p + 8] - tri[p + 2]];
          const pv = [d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0]];
          const det = e1[0] * pv[0] + e1[1] * pv[1] + e1[2] * pv[2];
          if (det > -1e-9 && det < 1e-9) continue;
          const iv = 1 / det, tv = [o[0] - tri[p], o[1] - tri[p + 1], o[2] - tri[p + 2]];
          const u = (tv[0] * pv[0] + tv[1] * pv[1] + tv[2] * pv[2]) * iv;
          if (u < 0 || u > 1) continue;
          const qv = [tv[1] * e1[2] - tv[2] * e1[1], tv[2] * e1[0] - tv[0] * e1[2], tv[0] * e1[1] - tv[1] * e1[0]];
          const v = (d[0] * qv[0] + d[1] * qv[1] + d[2] * qv[2]) * iv;
          if (v < 0 || u + v > 1) continue;
          const t = (e2[0] * qv[0] + e2[1] * qv[1] + e2[2] * qv[2]) * iv;
          if (skipTerrain && triTerrain[idx[k]]) continue;
          if (t > 1e-4 && t < tmax && t < best) {
            best = t; bestTri = idx[k];
            if (anyHit) return anyHit === 'info' ? {t: best, tri: bestTri} : best;
          }
        }
      } else { stack[sp++] = n.left; stack[sp++] = n.right; }
    }
    return anyHit === 'info' ? {t: best, tri: bestTri} : best;
  };
  // what a hit IS: the node it belongs to, how horizontal its face is, and how high it sits
  const hitInfo = (o, d, tmax, skipTerrain) => {
    const r = cast(o, d, tmax, 'info', skipTerrain);
    if (r.t === Infinity) return {t: Infinity, name: null, up: 0, y: 0};
    const p = r.tri * 9;
    const e1 = [tri[p + 3] - tri[p], tri[p + 4] - tri[p + 1], tri[p + 5] - tri[p + 2]];
    const e2 = [tri[p + 6] - tri[p], tri[p + 7] - tri[p + 1], tri[p + 8] - tri[p + 2]];
    const nx = e1[1] * e2[2] - e1[2] * e2[1], ny = e1[2] * e2[0] - e1[0] * e2[2],
          nz = e1[0] * e2[1] - e1[1] * e2[0];
    const L = Math.hypot(nx, ny, nz) || 1e-12;
    return {t: r.t, name: triNode[r.tri] || null, up: Math.abs(ny / L),
            y: (tri[p + 1] + tri[p + 4] + tri[p + 7]) / 3};
  };

  return {
    triangles: NT,
    hitInfo,
    // the raw caster, exposed so a calibration run can look at the DISTRIBUTION of the
    // bundle rather than at whatever single number a gate happens to reduce it to
    _cast: cast,
    // fraction of a region's probe points with a clear line of sight (map coords in)
    seenFrac(posMap, probesMap) {
      if (!probesMap.length) return null;
      const o = m2r(posMap);
      let n = 0;
      for (const q of probesMap) {
        const t = m2r(q);
        const dx = t[0] - o[0], dy = t[1] - o[1], dz = t[2] - o[2];
        const L = Math.hypot(dx, dy, dz);
        if (L < 1e-4) continue;
        if (cast(o, [dx / L, dy / L, dz / L], L - 0.35, true) === Infinity) n++;
      }
      return n / probesMap.length;
    },
    // THE NEAR-FIELD GATE, CALIBRATED — and the calibration is the point.
    //
    // The rule arrived as "nearest in-frustum hit over the standoff, reject under 0.45".
    // Applied literally to a TOWN camera it rejects seven of Emberbrook's eleven shots
    // AND ONE OF DELLHOLLOW'S SIXTEEN, which are baked, shipped, played and user-accepted
    // — so it was measured before it was believed. In eleven of those twelve rejections
    // the nearest hit sat at ndc (1,-1), (-1,-1) or (0,-1): the BOTTOM of frame, where a
    // camera pitched 10-50 degrees down at the ground it is framing meets that ground a
    // few metres below itself, by construction. THE FLOOR A SHOT IS AIMED AT IS NOT A
    // THING COVERING THE FRAME. (A second formulation — ratio against the ray's own
    // intersection with the aim's horizontal plane — was tried and was worse: 13 of 16
    // Dellhollow rejections, this time at the TOP of frame, where a near-horizontal ray's
    // "expected" ground is 200-870 m away and any real hillside scores near zero. Both
    // failures are recorded because both are the same mistake: reducing the bundle to one
    // number before knowing what the bundle looks like on shots that are known good.)
    //
    // WHAT THE DEFECT ACTUALLY IS, is a wall COVERING the frame — so the measure is
    // COVERAGE, not nearest-hit: how many of the thirteen rays hit inside a fraction of
    // the standoff. Read off Dellhollow's sixteen accepted shots:
    //
    //     rays hitting inside 0.25 of the standoff   max 0 of 13   (all 16 shots)
    //     rays hitting inside 0.45 of the standoff   max 2 of 13   (the Crossing)
    //     nearest ray, as a fraction                 min 0.380     (the Crossing)
    //
    // NOT ONE ACCEPTED SHOT PUTS ANY RAY INSIDE A QUARTER OF ITS OWN STANDOFF. That is
    // the hard line, and it is the town's own, not a number chosen for it. The soft line
    // at 0.45 is the forwarded threshold, which lands exactly where the accepted set's
    // tail already sits — the dressing lane's instinct was right and only its reduction
    // needed replacing.
    //
    //   HARD (reject): any ray inside NEAR_HARD (0.25) of the standoff.
    //   SOFT (warn):   more than NEAR_SOFT_RAYS (2) rays inside NEAR_FIELD_MIN (0.45).
    //
    // It caught two of Emberbrook's eleven on its first run — `gateroad`, which reads
    // 100.0% SUBJECT-VISIBLE and had 5 of 13 rays inside a fifth of its standoff, and
    // `therise` at 1 — which is the forwarded defect reproducing verbatim in this lane.
    nearField(posMap, aimMap, fovDeg, aspect) {
      const standoff = Math.hypot(aimMap[0] - posMap[0], aimMap[1] - posMap[1], aimMap[2] - posMap[2]);
      const {f, r, u} = camBasis(posMap, aimMap);
      const ty = Math.tan(fovDeg * RAD / 2);
      const o = m2r(posMap);
      const hits = [];
      let nearest = Infinity, nearestNdc = null;
      for (const [sx, sy] of BUNDLE) {
        const dm = [f[0] + r[0] * sx * ty * aspect + u[0] * sy * ty,
                    f[1] + r[1] * sx * ty * aspect + u[1] * sy * ty,
                    f[2] + r[2] * sx * ty * aspect + u[2] * sy * ty];
        const dr = m2r(dm);
        const L = Math.hypot(dr[0], dr[1], dr[2]);
        const h = hitInfo(o, [dr[0] / L, dr[1] / L, dr[2] / L], standoff * 4, true);
        const t = h.t / standoff;
        hits.push({ndc: [sx, sy], t, name: h.name, up: h.up, y: h.y});
        if (t < nearest) { nearest = t; nearestNdc = [sx, sy]; }
      }
      const hard = hits.filter((h) => h.t < NEAR_HARD);
      const soft = hits.filter((h) => h.t < NEAR_FIELD_MIN);
      return {frac: nearest === Infinity ? Infinity : +nearest.toFixed(3),
              hits, ndc: nearestNdc, standoff: +standoff.toFixed(2),
              hardRays: hard.length, softRays: soft.length,
              worstNdc: hard.length ? hard.sort((a, b) => a.t - b.t)[0].ndc : nearestNdc,
              pass: hard.length === 0,
              warn: hard.length === 0 && soft.length > NEAR_SOFT_RAYS};
    },
  };
}
