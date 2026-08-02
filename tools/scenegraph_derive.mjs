// scenegraph_derive.mjs — DERIVE public/world/scenegraph.json from the map files.
//
//   node tools/scenegraph_derive.mjs            # write public/world/scenegraph.json
//   node tools/scenegraph_derive.mjs --check    # fail if the shipped file is stale
//   node tools/scenegraph_derive.mjs --print    # dump, write nothing
//   node tools/scenegraph_derive.mjs --out <p>  # write a PROPOSAL elsewhere, for review
//
// THERE IS NO --town, AND THERE MUST NOT BE. This generator is already multi-town: it
// enumerates every `class: "town"` landmark in world/world.json, reads each one's
// `refinesTo` map, and MERGES all of their nodes and edges into one document — which is
// what scenegraph.json is, the wiring of the whole game. A --town flag could only mean
// "derive one town", and writing that over the shared file would delete the others. A
// second town joins by appearing in world.json with a bundle on disk; nothing here
// changes, and nothing about the first town is re-derived differently. Use --out (or
// --print) to inspect what a new town would add BEFORE it is merged into the live file,
// then diff it against the shipped one.
//
// WHY THIS EXISTS (canon, MIGRATION.md): transitions are DOWNSTREAM OF THE MAP.
// Portals and enterable landmarks are the wiring truth, so the runtime's scene
// graph must be a projection of the map files, never a hand-authored parallel
// document that can disagree with them. scenegraph.json is a build artifact:
// re-run this after any map edit. NEVER hand-edit it.
//
// WHAT IT READS
//   public/world/world.json                  regions, towns, portal graph
//   public/world/regions/<id>.region.json     road polyline + portals (per region)
//   public/townmap/<town>.map.json            landmarks (enterable/interiorSceneKey),
//                                             walk-network edges, exits
//   public/assets/scenes/<key>/scene.glb      GEOMETRY CROSS-CHECK ONLY (pad centers,
//                                             walk-surface heights). The map decides;
//                                             the bundle is asked "is that where the
//                                             pad actually is?" and a mismatch is a
//                                             reported warning, not a silent override.
//   public/assets/scenes/<key>/meta.json      region<->bundle resolution
//
// COORDINATE FRAMES (both verified against the shipped bundles, see docs/plans/
// slice-findings.md):
//   town map   pos [x, y, h] -> runtime (x, h, -y)          (== play3d loadNet T())
//   region/world pos [x, y, h] -> runtime (x-CX, h, CY-y)   (== valley_map.w2r,
//                                                            CX,CY = tile/2)
// Runtime axes are +x east, +y up, +z south.
import fs from 'fs';
import path from 'path';
import {loadGlb} from './glb_read.mjs';
import {loadCine, cutGeometry, shotRegions, inShot} from './cine_regions.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const PUB = path.join(ROOT, 'public');
const ARGS = process.argv.slice(2);
const opt = (n, d) => { const i = ARGS.indexOf(n); return i >= 0 ? ARGS[i + 1] : d; };
const SHIPPED = path.join(PUB, 'world/scenegraph.json');
// --check ALWAYS asks about the shipped file — staleness is a question about what the
// runtime loads, never about a proposal sitting in a scratch directory.
const OUT = opt('--out', null) ? path.resolve(process.cwd(), opt('--out', null)) : SHIPPED;
const rd = (p) => JSON.parse(fs.readFileSync(path.join(PUB, p), 'utf8'));
const warn = [];
const W = (m) => { warn.push(m); console.error('  WARN ' + m); };
// map connections that carry no walkable geometry, so no camera boundary is placed on
// them. Recorded rather than silently dropped: if a ladder is ever made climbable its
// cut appears by itself.
const noRibbon = [];
// THE UNWIRED INVENTORY (2026-08-02). Every declared passage the derive did NOT turn
// into an edge, by name and with its reason. Before this existed the derive skipped an
// unpaired region portal with a wordless `continue`, so "Emberbrook's old gate has no
// entry marker" was invisible in the tooling: no edge, no prompt, no marker, no warning,
// nothing to grep. These three arrays ship inside scenegraph.json so the declared-vs-
// derived audit (tools/trigger_probe.mjs --static) can call a row EXPLAINED instead of
// leaving a reader to re-derive why it is missing.
const unpaired = [];      // region portals that reached no town
const sealed = [];        // portal<->exit pairs held shut by the map's own `sealed`
const paired = new Set(); // "<town>:<exit id>" that DID become an edge

// ---------------------------------------------------------------- tunables (DATA)
// Everything the transition layer can be tuned by lives here and ships inside
// scenegraph.json, so tuning the feel of the whole game is a data edit. The
// runtime reads these; it has no radii, no timings and no labels of its own.
const DEFAULTS = {
  fadeMs: 350,          // fade-to-black duration each way
  key: 'e',             // prompt key (per-edge overridable)
  vTol: 2.0,            // |dy| gate: Dellhollow stacks tiers 5u apart, so 2.0 keeps
                        // a quay door from triggering through the shelf street above
  doorRadius: 1.8,      // landmark door pads are 2.6u squares
  gateRadius: 3.2,      // an overworld portal at miniature scale (road is 2u wide)
  portalRadius: 2.2,    // a town-side gate pad
  passageRadius: 1.8,   // an in-town prompted transition: a door-sized pad, because it
                        // stands on a street the same way a door does
  spawnBackoff: 1.1,    // arrival is pushed this far PAST the reciprocal radius, so
                        // you never materialise inside the prompt you just used
  promptFmt: '{label}? [{key}]',
  // THE POSITIONAL SAFETY NET (play3d.html sgCorrect). Seams stay primary; this only
  // catches travel that never crossed one — a slide down a slope beside a flight, a
  // jump, a future knockback. grace is in PHYSICS STEPS, so it is ~1-2 m of travel:
  // long enough that a boundary straddle never flickers, short enough that a player
  // who has left frame is back in one almost immediately.
  correctionGrace: 20,
  correctionPad: 0.6,   // body radius: ribbons are ~2 m wide and you stand ON the edge
  correctionVTol: 1.2,  // this town STACKS; without a height gate the quay deck would
                        // resolve to Westweave directly beneath it
  correctionReach: 12,  // when the player is on NOBODY's ground, correct to the nearest
                        // shot's — but only within this far. Past it you are falling, and
                        // the void-fall respawn owns that, not the camera.
};

// -------------------------------------------------------------------- geometry
const bundleDir = (key) => path.join(PUB, 'assets/scenes', key);
const hasBundle = (key) => fs.existsSync(path.join(bundleDir(key), 'scene.glb'));
const _glb = new Map();
function glb(key) {
  if (!_glb.has(key)) {
    const p = path.join(bundleDir(key), 'scene.glb');
    _glb.set(key, fs.existsSync(p) ? loadGlb(p) : null);
  }
  return _glb.get(key);
}
const WALK = /^walk/i;
// height of the walk surface at (x,z) nearest to `near`, or null
function walkY(key, x, z, near) {
  const G = glb(key); if (!G) return null;
  const ys = G.tops(WALK, x, z);
  if (!ys.length) return null;
  let b = ys[0];
  for (const y of ys) if (Math.abs(y - near) < Math.abs(b - near)) b = y;
  return b;
}
// height of the walk surface AT (x,z), or from a ring inside `r` if the point
// itself is off-surface. The ow-valley road ribbon ends 0.11u short of its own
// gate portal, so "no surface exactly under the map's point" is normal and must
// not silently leave a map height in a runtime field.
function walkYNear(key, x, z, near, r) {
  const at = walkY(key, x, z, near);
  if (at != null) return {y: at, off: 0};
  for (const f of [0.5, 0.85]) for (let k = 0; k < 8; k++) {
    const a = k * Math.PI / 4, px = x + Math.cos(a) * r * f, pz = z + Math.sin(a) * r * f;
    const y = walkY(key, px, pz, near);
    if (y != null) return {y, off: r * f};
  }
  return null;
}
// a pad's standing point: its centre in xz, its TOP in y (that is where feet go)
function padStand(key, name) {
  const G = glb(key); if (!G) return null;
  const n = G.nodesNamed(new RegExp('^' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '$', 'i'));
  if (!n.length) return null;
  const b = G.nodeBox(n[0].i);
  return b && [b.center[0], b.max[1], b.center[2]];
}
const norm2 = (dx, dz) => { const L = Math.hypot(dx, dz) || 1; return [dx / L, dz / L]; };
const r3 = (v) => v.map((n) => Math.round(n * 1000) / 1000);

// ------------------------------------------- THE SPAWN-IN-CUT-BAND RULE ------
// A camera cut's trigger is a BAND, not a circle (cine_regions.cutGeometry), and the
// runtime arms it ON ENTRY: play3d's sgTick fires any `auto` edge whose band the
// player is inside, on the very next physics step. So AN ARRIVAL SPAWN INSIDE A BAND
// IS A PLAYER WHO MATERIALISES ALREADY HOLDING A CUT. The arrival applies its own
// camera, the band fires immediately, and one door renders TWO shots.
//
// MEASURED (2026-08-01, this file's own validation pass below, against the shipped
// scenegraph.json — the clearances are the runtime's own firing predicate, signed):
//   del-weapon-int>del-cine@weapon-shop        -0.951 m   INSIDE (0.149 m off the
//                                                         seam centreline, across 0.000)
//   del-armor-int>del-cine@armor-shop          -0.157 m   INSIDE
//   del-cottage-int>del-cine@keepers-cottage   +0.050 m   outside, 0.45 m under the floor
// The first is transition_test's door 7: leaving the weapon shop applied `shelf-east`,
// the shelf-west<->shelf-east band fired on entry, and the frame carried +510 geometries
// over the per-(scene, shot) baseline — TWO SHOTS' ART, not a leak — which is also why
// the "every repeated (scene, shot) has identical counts" assertion drifted. Long-
// standing: it has been true since the cuts were first derived, and nothing about
// b6b9566 caused it.
//
// THE RULE. An ARRIVAL spawn — a door's return spawn, a portal's town-side spawn —
// must clear EVERY cut band in the scene it lands in by BAND_CLEAR. Two classes are
// deliberately NOT subject to it:
//   * CUT arrivals, which have their own and tighter rule in cine_regions (they must
//     clear THE BAND THEY JUST CROSSED; standing clear of one seam while inside a
//     different one is how two seams on one street are supposed to work);
//   * CORRECTION targets — the positional safety net is ALLOWED to put you in a band,
//     because it only ever runs when you are already on ground the cameras disagree
//     about, and refusing bands there would leave the player uncorrected.
//
// BAND_CLEAR is 0.5 m: one stride, the same hard FLOOR cine_regions puts under a
// hand-authored cut arrival, and for the same reason — under one step, walking on
// re-enters the band.
const BAND_CLEAR = 0.5;

// Signed clearance of a runtime point from ONE cut band, in the runtime's own terms.
// play3d's sgTick fires the cut when ALL THREE of its gates are satisfied at once —
// |along| <= t AND |across| <= w AND dy <= vTol — so the honest measure is the
// SEPARATING AXIS: how far outside the gate you are on whichever axis is saving you.
//   > 0   metres of margin on the axis that keeps the cut from firing
//   < 0   inside on every axis: the depth on the shallowest one, i.e. how far the
//         player would have to move to get out
// THE HEIGHT AXIS COUNTS, and it counts the same as the others. Treating "above the
// vTol gate" as infinite clearance is how the keepers' cottage's first push passed:
// it climbed 1.4 m onto a ledge to sit 1.625 m over a band whose gate is 1.600 m — a
// 25 mm margin, clearance in arithmetic and nonsense on the ground. This is also the
// formula cine_regions already uses on hand-authored cut arrivals (max(|along| - t,
// dy - cvt)), extended with the across axis rather than replaced, so there is one
// definition of "clear of a band" in the repo and not two.
function bandClearance(p, c) {
  const px = p[0] - c.at[0], pz = p[2] - c.at[2];
  const along = px * c.band.n[0] + pz * c.band.n[1];
  const across = -px * c.band.n[1] + pz * c.band.n[0];
  return Math.max(Math.abs(along) - c.band.t,
                  Math.abs(across) - c.band.w,
                  Math.abs(p[1] - c.at[1]) - c.vTol);
}
// the band a point is closest to being caught by, and by how much
function worstBand(cuts, p) {
  let best = {clr: Infinity, cut: null};
  for (const c of cuts) { const d = bandClearance(p, c); if (d < best.clr) best = {clr: d, cut: c}; }
  return best;
}
const cutTag = (c) => c.edge ? `${c.from}<->${c.to} on '${c.edge}'`
                             : `${c.camFrom}<->${c.cam.key} on '${c.of}'`;
// Which shot's ground a point stands on, by the runtime's own containment test — the
// same regions and the same pad/vTol play3d's sgCorrect uses, so this answers exactly
// the question the safety net will ask on the first tick after the arrival.
function ownerShot(regions, p) {
  for (const r of regions || [])
    if (inShot(r, p, DEFAULTS.correctionPad, DEFAULTS.correctionVTol)) return r.id;
  return null;
}
// Push an arrival OFF the bands, along the walk surface, to the NEAREST clear point.
//
// Deliberately a SEPARATE search from the off-network one above rather than an extra
// predicate on it: that search's grid is load-bearing (its results are shipped
// coordinates) and widening it could move a point it already found. This one runs
// after, on a point that is already on the network, and only when a band catches it.
// Same determinism — fixed grid, winner is the least displacement from the point we
// derived, ties broken by (distance, angle) in enumeration order — so no map
// reordering can move it. Three differences, each of them measured rather than
// guessed (2026-08-01, Dellhollow's three offenders):
//
//   FULL CIRCLE, not +/-60 deg off the street. A band is a thing you WALK ACROSS, and
//   the clear side can be the one behind you. streetDir's tie-break is alphabetical,
//   so the weapon shop's `dir` points WEST (`road item-shop->weapon-shop` beat
//   `road weapon-shop->armor-shop` on the string compare — the same fact the arrival
//   override comment above records), and a +/-60 deg sweep can only push the arrival
//   FURTHER from the shop it just left, across the seam, onto shelf-west's ground.
//
//   SAME TIER. walkY takes the surface nearest in height, which in a town that STACKS
//   is not the same as the surface you are standing on: the armor shop's first push
//   swept -40 deg and found the quay deck 5 m BELOW the door. A candidate more than
//   DEFAULTS.vTol from the trigger is a different tier, and leaving a shop must not
//   change which one you are on.
//
//   THE ARRIVAL'S OWN SHOT. This is the whole point of the exercise and it is worth
//   saying plainly: getting clear of the band is not enough if the ground you land on
//   belongs to a DIFFERENT camera, because then the arrival applies its shot, the
//   positional safety net disagrees on the first tick, and the scene renders two shots
//   — the identical defect by another route. The keepers' cottage's first push
//   escaped its band by climbing 1.4 m onto a ledge and out of the band's HEIGHT gate,
//   which is clearance in arithmetic and nonsense on the ground.
function searchClearOfBands(key, cuts, at, dir, sp, back, regions, shot, tol) {
  const vtol = tol == null ? DEFAULTS.vTol : tol;
  const region = shot && (regions || []).find((r) => r.id === shot);
  let best = null;
  for (let di = 0; di <= 24; di++) {                 // out to back + 6 m
    const d = back + di * 0.25;
    for (let ai = 0; ai <= 36; ai++) {               // 0, -10, +10 ... +/-180 deg
      const a = (ai % 2 ? -1 : 1) * Math.ceil(ai / 2) * 10 * Math.PI / 180;
      const ux = dir[0] * Math.cos(a) - dir[1] * Math.sin(a);
      const uz = dir[0] * Math.sin(a) + dir[1] * Math.cos(a);
      const px = at[0] + ux * d, pz = at[2] + uz * d;
      const y = walkY(key, px, pz, at[1]);
      if (y == null) continue;
      if (Math.abs(y - at[1]) > vtol) continue;                     // another tier
      if (region && !inShot(region, [px, y, pz], DEFAULTS.correctionPad,
                            DEFAULTS.correctionVTol)) continue;     // another camera
      const w = worstBand(cuts, [px, y, pz]);
      if (w.clr < BAND_CLEAR) continue;
      const off = Math.hypot(px - sp[0], pz - sp[2]);
      if (!best || off < best.off) best = {px, pz, y, off, d, a, clr: w.clr};
    }
  }
  return best;
}
// Applied to a derived arrival: if a band catches it, push and SAY SO (every pushed
// spawn is printed — an arrival that moved is a fact about the town, and the reader
// should not have to diff two scenegraphs to find it). Mutates sp; returns the note
// that goes into the edge's `source`, so the provenance travels with the coordinate.
function clearBands(ctx, sp, at, dir, back, shot, what) {
  const {key, cuts, cine, glbPath} = ctx;
  if (!cuts || !cuts.length) return '';
  const w0 = worstBand(cuts, sp);
  if (w0.clr >= BAND_CLEAR) return '';
  const regions = cine ? shotRegions(cine, glbPath) : null;
  // The shot constraint is a REQUIREMENT, then a preference: if no point on the
  // arrival's own ground clears the bands, a point on somebody else's still beats a
  // player who materialises holding a cut — but the fallback is stated, not silent.
  let hit = searchClearOfBands(key, cuts, at, dir, sp, back, regions, shot), loose = '';
  if (!hit && shot) {
    hit = searchClearOfBands(key, cuts, at, dir, sp, back, regions, null);
    if (hit) loose = `; NO point clear of every band stands on '${shot}' ground — ` +
                     `the camera will correct on arrival`;
  }
  if (!hit) {
    W(`${what}: spawn (${sp[0].toFixed(2)},${sp[2].toFixed(2)}) clears the ` +
      `${cutTag(w0.cut)} cut band by only ${w0.clr.toFixed(3)} m (floor ${BAND_CLEAR} m) ` +
      `and NO point on the walk surface within ${(back + 6).toFixed(1)}u of the trigger ` +
      `clears every band — the derived point stands and the gate will fail on it, ` +
      `which is correct`);
    return `; WARNING: only ${w0.clr.toFixed(3)}u clear of the ${cutTag(w0.cut)} cut band`;
  }
  const from = sp.slice();
  sp[0] = hit.px; sp[1] = hit.y; sp[2] = hit.pz;
  const own = ownerShot(regions, sp);
  W(`${what}: spawn (${from[0].toFixed(2)},${from[2].toFixed(2)}) sat ` +
    `${w0.clr.toFixed(3)}u from the ${cutTag(w0.cut)} cut band (floor ${BAND_CLEAR}u) — ` +
    `a player would materialise already holding that cut. PUSHED to ` +
    `(${hit.px.toFixed(2)},${hit.pz.toFixed(2)}), ${hit.off.toFixed(2)}u along the walk ` +
    `surface, now ${hit.clr.toFixed(2)}u clear` +
    (own ? `, on '${own}' ground${shot ? (own === shot ? ' (its own shot)' : ` — NOT '${shot}'`) : ''}` : '') + loose);
  return `; the derived point cleared the ${cutTag(w0.cut)} cut band by only ` +
         `${w0.clr.toFixed(3)}u, PUSHED ${hit.off.toFixed(2)}u along the walk surface ` +
         `(${hit.d.toFixed(2)}u out, ${(hit.a * 180 / Math.PI).toFixed(0)} deg off the ` +
         `street) to ${hit.clr.toFixed(2)}u clear` + loose;
}

// short display name: "Inn — The Boatmen's Rest" -> "The Boatmen's Rest",
// "Item Shop (chandlery skin)" -> "Item Shop". Text tidying only — the STRING
// still comes from the map, so renaming a landmark renames its prompt.
function shortName(name) {
  let s = String(name).split(/\s+[—–-]\s+/).pop();
  s = s.replace(/\s*\([^)]*\)\s*/g, ' ').trim();
  return s || name;
}

// ------------------------------------------------------------ scene resolution
// No scene key is invented from a town/region id: each is resolved from data that
// already exists (a bundle's own meta.json, the map's interiorSceneKey, or the
// bundle whose walk pads ARE this town's landmarks) so a second town/region needs
// no edit here.
// A region STATES its scene: world.json regions[].sceneKey. No naming convention
// is inferred from the region id — when the choice is "assume a convention" or
// "ask for a data field", the data field wins.
function regionSceneKey(reg) {
  if (!reg.sceneKey) { W(`region '${reg.id}': no sceneKey in world.json — skipped (add regions[].sceneKey)`); return null; }
  if (!hasBundle(reg.sceneKey)) { W(`region '${reg.id}': sceneKey '${reg.sceneKey}' has no bundle — skipped`); return null; }
  return reg.sceneKey;
}
function townSceneKey(map) {
  // playSceneKey = the scene the GAME routes into (Dellhollow: the cinematic
  // fixed-camera town). walkSceneKey = the real-time explore bundle, which stays a
  // developer view. Which one is wired is a data choice in the map, not a naming rule.
  if (map.playSceneKey) return map.playSceneKey;
  if (map.walkSceneKey) return map.walkSceneKey;      // preferred: the map says so
  // FALLBACK (warns): a district bundle carries the WHOLE town's collision (canon),
  // so pad names alone cannot tell the town's explorable scene from one district's
  // fixed-camera bundle. Discriminate on what a fixed-camera scene has and an
  // explore scene never does: a baked depth map. Then pad coverage, then name.
  const ids = new Set(map.landmarks.map((l) => l.id));
  const hits = [];
  for (const d of fs.readdirSync(path.join(PUB, 'assets/scenes'))) {
    if (!hasBundle(d)) continue;
    const buf = fs.readFileSync(path.join(bundleDir(d), 'scene.glb'));
    // cheap probe: the walk-pad node names live verbatim in the JSON chunk
    let n = 0;
    for (const id of ids) if (buf.includes('walk_pad_' + id)) n++;
    if (n >= Math.max(3, ids.size * 0.4))
      hits.push({key: d, pads: n, fixed: fs.existsSync(path.join(bundleDir(d), 'depth.json')) ? 1 : 0});
  }
  hits.sort((a, b) => a.fixed - b.fixed || b.pads - a.pads || (a.key < b.key ? -1 : 1));
  if (!hits.length) return null;
  W(`town '${map.town}': no "walkSceneKey" in the town map — resolved '${hits[0].key}' from bundles on disk (${hits.map((h) => `${h.key}:${h.pads}pads${h.fixed ? ',fixed-cam' : ''}`).join(', ')}). REQUEST: add "walkSceneKey" so this is stated, not inferred.`);
  return hits[0].key;
}

// =============================================================== derivation ===
const world = rd('world/world.json');
const nodes = {};
const edges = [];
const addNode = (key, o) => { if (key) nodes[key] = Object.assign(nodes[key] || {}, o); };
const eid = (from, to, of_) => `${from}>${to}@${of_}`;

// --- towns: their walk scene, their interiors, their door edges ---------------
const townMaps = {};            // townId -> {map, key}
for (const lm of world.landmarks) {
  if (lm.class !== 'town' || !lm.refinesTo) continue;
  const map = rd(lm.refinesTo);
  const key = townSceneKey(map);
  if (!key) { W(`town '${lm.id}' has no walkable bundle — skipped`); continue; }
  // ...and a sceneKey the map DECLARES but no bundle on disk is the same thing.
  // A town is founded map-first: Emberbrook has a ratified map, a portal off the
  // overworld and no `emb-cine/scene.glb` yet, and without this guard the derive
  // shipped a node and two portal edges for a scene that does not exist —
  // cine_test failed on "the way out is only offered in shot 'undefined'" and
  // slice_test crashed opening the missing GLB. The interiors below have always
  // been guarded this way (`hasBundle(ikey)`); towns were not, and only a stale
  // scenegraph.json was hiding it. The node reappears by itself the day the
  // bundle is baked.
  if (!hasBundle(key)) { W(`town '${lm.id}': scene '${key}' has no bundle yet — skipped`); continue; }
  // A town with a cameraFile is played through FIXED cameras: it is not a real-time
  // explore scene, so it must not be handed rt=1. Both facts come from the map.
  let cine = null;
  if (map.cameraFile) {
    try { cine = loadCine(lm.refinesTo, map.cameraFile); }
    catch (e) { W(`town '${lm.id}': cameraFile '${map.cameraFile}' unreadable (${e.message}) — no camera cuts`); }
    if (cine) for (const m of cine.warn) W(`cameras(${lm.id}): ${m}`);
  }
  const fixedCam = !!(cine && cine.camFile.sceneKey === key);
  // THE CUTS ARE SOLVED BEFORE THE DOORS, because a door's return spawn now has to be
  // checked against the bands (THE SPAWN-IN-CUT-BAND RULE above) and the portal loop
  // further down needs the same answer for its town-side spawn. cutGeometry is a pure
  // function of the cameras and the walk geometry, so hoisting it only reorders the
  // WARNINGS (the cuts' warnings now precede the doors' — they are the precondition).
  const glbPath = path.join(bundleDir(key), 'scene.glb');
  const CG = fixedCam ? cutGeometry(cine, glbPath, W) : null;
  townMaps[lm.id] = {map, key, lm, glbPath, CG,
                     cine: fixedCam ? cine : null,
                     cuts: CG ? CG.cuts : []};
  addNode(key, {
    label: map.displayName || lm.name, kind: 'town',
    rt: !fixedCam, params: fixedCam ? {} : {rt: '1'},
    cinematic: fixedCam || undefined,
    shotCount: fixedCam ? cine.cams.length : undefined,
    // THE OWNERSHIP REGIONS, shipped with the wiring rather than with the art, because
    // that is what they are: which shot owns which ground is the same decision the cut
    // edges are derived from, and the runtime already fetches this file. Consumed by
    // play3d.html's positional correction — the safety net under the seams for travel
    // that never crossed one (a slide down a slope beside a flight, a jump, a knockback).
    shots: fixedCam ? shotRegions(cine, path.join(bundleDir(key), 'scene.glb')) : undefined,
    bundle: `assets/scenes/${key}/`,
    origin: `${lm.refinesTo} (town '${map.town}')` +
            (fixedCam ? ` — fixed-camera play scene, ${cine.cams.length} shots from ${map.cameraFile}` : ''),
  });
}

// Direction to step OFF a landmark pad onto a street that actually exists.
//
// DETERMINISM RULE (deliberate — "the first edge in the list" would let a
// reordered map silently move every arrival point): among the walk-network edges
// touching the landmark, rank by
//   1. FLAT type first (road/deck/path/bridge) — stairs and ladders are trimmed
//      back from their landing by the runtime's net builder, so stepping onto one
//      can land you off the network;
//   2. then by |slope| of the first sub-segment leaving the pad (flattest wins —
//      an arrival should not be mid-flight);
//   3. then lexicographically by "type from->to".
// Order in the map file never enters into it.
const FLAT = ['road', 'deck', 'path', 'bridge'];
function streetDir(map, id, T) {
  const here = T(map.landmarks.find((l) => l.id === id).pos);
  const cand = [];
  for (const e of map.edges) {
    if (e.from !== id && e.to !== id) continue;
    const wps = (e.waypoints || []).map(T);
    const far = e.from === id ? (wps[0] || T(map.landmarks.find((l) => l.id === e.to).pos))
                              : (wps[wps.length - 1] || T(map.landmarks.find((l) => l.id === e.from).pos));
    const h = Math.hypot(far[0] - here[0], far[2] - here[2]);
    if (!h) continue;
    cand.push({e, dir: norm2(far[0] - here[0], far[2] - here[2]),
               flat: FLAT.includes(e.type) ? 0 : 1,
               slope: Math.abs(far[1] - here[1]) / h,
               tag: `${e.type} ${e.from}->${e.to}`});
  }
  cand.sort((a, b) => a.flat - b.flat || a.slope - b.slope || (a.tag < b.tag ? -1 : 1));
  if (!cand.length) { W(`${id}: no walk-network edge touches it; arrival direction fell back to +x`); return {dir: [1, 0], via: '(no walk edge — +x)'}; }
  return {dir: cand[0].dir, via: cand[0].tag};
}

for (const [townId, {map, key, cine, cuts, glbPath}] of Object.entries(townMaps)) {
  const T = (p) => [p[0], p[2], -p[1]];                     // town map -> runtime
  // which shot frames a given landmark (null when the town has no cameras)
  const shotOf = (id) => (cine && cine.lmOwner[id]) || null;
  const bandCtx = {key, cuts, cine, glbPath};
  for (const lm of map.landmarks) {
    if (!lm.enterable || !lm.interiorSceneKey) continue;
    const ikey = lm.interiorSceneKey;
    if (!hasBundle(ikey)) { W(`${lm.id}: interiorSceneKey '${ikey}' has no bundle — skipped`); continue; }
    const short = shortName(lm.name);
    addNode(ikey, {
      label: lm.name, kind: 'interior', rt: false, params: {},
      bundle: `assets/scenes/${ikey}/`,
      origin: `${townId}.map.json landmark '${lm.id}' interiorSceneKey`,
    });

    // TOWN SIDE: the trigger stands ON the landmark's door pad — x, z AND y. THE WALK
    // PAD IS THE DOORSTEP (CLAUDE.md, world-building doctrine), and a doorstep is not a
    // building centre: the blockout derives it out along the street the door faces
    // (Emberbrook: bd/2 + 1.15, so 3.43 m for a cottage) precisely so the building sits
    // BEHIND it. This line used to take only the HEIGHT from the pad and leave x/z at
    // T(lm.pos), which seats every door trigger inside its own walls — unreachable, and
    // the return spawn measured from it lands off the network. Dellhollow never showed
    // it because its blockout puts each pad AT lm.pos (all six enterables agree to
    // <2e-6 u, far under r3()'s 1e-3), so the map's own point WAS the doorstep there.
    // The map still decides which landmark has a door; the bundle says where its
    // doorstep is, because the bundle is the only thing that knows.
    const at = T(lm.pos);
    let padOff = null;
    const pad = padStand(key, 'walk_pad_' + lm.id);
    // `"doorstepFromMap": true` — THE MAP HAS MOVED AND THE BUNDLE HAS NOT YET (2026-08-02).
    // The rule above is right in steady state: the blockout derives the pad FROM the map,
    // so the bundle is the only thing that knows where the doorstep landed. But that makes
    // the pad DOWNSTREAM of the map, and when the map moves a door the shipped pad is not
    // a better answer — it is a STALE one. This opt-in says so per landmark, so the five
    // Dellhollow doors that have not moved keep byte-identical rows and only the one that
    // did is derived from the map. It is loud, and it retires by itself: once the town is
    // re-baked the pad lands on the map point, the offset falls under the threshold, and
    // the flag can come off with no change to the derived row.
    if (lm.doorstepFromMap) {
      const off = pad ? Math.hypot(pad[0] - at[0], pad[2] - at[2]) : null;
      const ry = walkYNear(key, at[0], at[2], at[1], DEFAULTS.doorRadius);
      if (ry == null) W(`${lm.id}: "doorstepFromMap" point (${at[0].toFixed(1)},${at[2].toFixed(1)}) ` +
                        `has no walk surface within ${DEFAULTS.doorRadius}u — the door will be unreachable`);
      else at[1] = ry.y;
      W(`${lm.id}: "doorstepFromMap" — trigger taken from the MAP, not walk_pad_${lm.id}` +
        (off == null ? ' (no pad in the bundle)' : `, which still stands ${off.toFixed(2)}u away`) +
        `. The bundle is STALE for this landmark: the next blockout/bake moves the pad onto ` +
        `the map point and this flag becomes a no-op.`);
    } else if (pad) {
      padOff = Math.hypot(pad[0] - at[0], pad[2] - at[2]);
      at[0] = pad[0]; at[2] = pad[2];                       // pad CENTRE: the doorstep
      at[1] = pad[1];                                       // pad TOP: the height you stand at
    } else W(`${lm.id}: no walk_pad_${lm.id} in '${key}'`);

    // INTERIOR SIDE: the room's own door pad — where the runtime already spawns
    const ipad = padStand(ikey, 'walk_pad_door');
    if (!ipad) { W(`${ikey}: no walk_pad_door — interior edges skipped`); continue; }

    // return spawn: off the pad, along the street, clear of the enter radius
    const {dir, via} = streetDir(map, lm.id, T);
    const back = DEFAULTS.doorRadius + DEFAULTS.spawnBackoff;
    const sp = [at[0] + dir[0] * back, at[1], at[2] + dir[1] * back];
    let spY = walkY(key, sp[0], sp[2], at[1]);
    let spSearch = '';
    if (spY == null) {
      // THE SPAWN IS SEARCHED, NOT ASSUMED — and only when the derived point has no
      // ground under it, so a town whose streets are whole never enters this branch and
      // cannot be moved by it (Dellhollow: every door spawn is on-network, so the search
      // is dead code there and its scenegraph rows are byte-identical with and without).
      //
      // WHY IT IS NEEDED AT ALL, stated plainly because it is easy to mistake for
      // papering over art: A DOORSTEP PAD CAN NEVER CARRY ITS OWN RETURN SPAWN. The
      // spawn is `trigger + back`, the trigger IS the pad centre, so covering it would
      // need a pad 2 x back = 5.8 m deep — a forecourt, which Emberbrook's blockout
      // measured at 3.0 m taking Festival Square's walk gate from 0 to 11 offenders.
      // The ground `back` metres out belongs to the STREET, and where the street is
      // sparse (Festival Square ships ~42 m2 of scattered cells in a 12.7 x 13.5 m box)
      // the derived point can fall in a hole while walkable ground sits a metre away.
      // Dellhollow never showed this because its shelf streets are continuous.
      //
      // THE RULE IS "the nearest legal point to the one we derived", which is the same
      // rule seam_walk's re-search takes (289 legal points, nearest 4.2 m out, taken) and
      // the same searched-not-authored doctrine as a free-standing solid. Legal means:
      // on the walk network, and at least `back` from the trigger so you never
      // materialise holding the prompt you just used — the constraint the checker below
      // enforces on hand-authored overrides, applied to the derived point as well.
      // Distance is stepped OUT along the street first and swept +/-60 degrees either
      // side; the grid is fixed and the winner is the least displacement from the
      // derived point, ties broken by (distance, angle) in enumeration order, so the
      // result cannot depend on map ordering any more than streetDir's can.
      let best = null;
      for (let di = 0; di <= 10; di++) {
        const d = back + di * 0.25;
        for (let ai = 0; ai <= 12; ai++) {
          const a = (ai % 2 ? -1 : 1) * Math.ceil(ai / 2) * 10 * Math.PI / 180;
          const ux = dir[0] * Math.cos(a) - dir[1] * Math.sin(a);
          const uz = dir[0] * Math.sin(a) + dir[1] * Math.cos(a);
          const px = at[0] + ux * d, pz = at[2] + uz * d;
          const y = walkY(key, px, pz, at[1]);
          if (y == null) continue;
          const off = Math.hypot(px - sp[0], pz - sp[2]);
          if (!best || off < best.off) best = {px, pz, y, off, d, a};
        }
      }
      if (best) {
        spSearch = `; derived point (${sp[0].toFixed(1)},${sp[2].toFixed(1)}) had no walk ` +
                   `surface, SEARCHED to the nearest legal one ${best.off.toFixed(2)}u away ` +
                   `(${best.d.toFixed(2)}u out, ${(best.a * 180 / Math.PI).toFixed(0)} deg off the street)`;
        W(`${lm.id}: return spawn (${sp[0].toFixed(1)},${sp[2].toFixed(1)}) is off the walk ` +
          `network — searched to (${best.px.toFixed(1)},${best.pz.toFixed(1)}), ${best.off.toFixed(2)}u ` +
          `away. THE STREET IS THE DEFECT, not the door: give it ground and this stops firing.`);
        sp[0] = best.px; sp[2] = best.pz; spY = best.y;
      } else {
        W(`${lm.id}: return spawn (${sp[0].toFixed(1)},${sp[2].toFixed(1)}) is off the walk ` +
          `network and NOTHING legal was found within ${(back + 2.5).toFixed(1)}u of the door — ` +
          `the derived point stands and the gate will fail on it, which is correct`);
      }
    }
    if (spY != null) sp[1] = spY;

    // WHICH SHOT frames this door. The town-side edge only exists while that shot is
    // up (camFrom), and the way back out selects it on arrival (cam) — so leaving the
    // inn puts you on the street under the camera that frames the inn's door, never
    // under whatever shot the player happened to enter from.
    const shot = shotOf(lm.id);
    if (cine && !shot) W(`${lm.id}: enterable but owned by no camera — its door has no shot`);

    // ...and then the arrival is pushed off the cut bands. TWO orderings matter here.
    // The point has to be ON the network before "push it along the network" means
    // anything (so this follows the search above), and the SHOT has to be known before
    // the push (so it follows shotOf) — the shot is what says which ground is the
    // right ground to land on.
    spSearch += clearBands(bandCtx, sp, at, dir, back, shot, `${lm.id} return spawn`);

    // A DOOR ARRIVAL MAY BE OVERRIDDEN, for the same reason a cut arrival may
    // (cine_regions.cutGeometry): the derived point is blind to what the camera can
    // SEE. And here the derivation is blinder than usual, because `streetDir`'s
    // tie-break is ALPHABETICAL: the weapon shop is the junction of two equally flat
    // roads, so `road item-shop->weapon-shop` beat `road weapon-shop->armor-shop` on
    // the string compare alone and the player was put down 2.9 m WEST — into the one
    // stretch of the shop street that `shelf-west` cannot see past the weapon shop's
    // own building. Measured with tools/arrival_probe.py against the shipped depth
    // plate: 91 of 91 body samples on screen, 0 surviving the depth test.
    //
    //     "arrivals": { "door:<landmark id>": [x, up, -y] }   RUNTIME coords
    //
    // on the RECEIVING camera's record — the shot that owns the landmark. Same layer,
    // same file, same convention as the cut overrides, and checked here the same way:
    // an override that is off the walk network, or inside the door's own trigger
    // radius (you would materialise holding the prompt you just used), is REJECTED
    // loudly and the derived point stands.
    let spSrc = `via ${via}` + spSearch;
    const dovr = shot && cine.byId[shot] && cine.byId[shot].arrivals
                 && cine.byId[shot].arrivals[`door:${lm.id}`];
    if (dovr) {
      const key2 = `door:${lm.id}`;
      const bad = (why) => W(`arrival override ${shot} '${key2}' REJECTED: ${why}`);
      if (!Array.isArray(dovr) || dovr.length !== 3) bad('not an [x, up, -y] runtime point');
      else {
        const oy = walkY(key, dovr[0], dovr[2], at[1]);
        const dd = Math.hypot(dovr[0] - at[0], dovr[2] - at[2]);
        if (oy == null || Math.abs(oy - dovr[1]) > 0.6)
          bad(`off the walk network (nearest surface ${oy == null ? 'none' : oy.toFixed(2)}, ` +
              `authored ${dovr[1]}) — is the coordinate still in MAP order [x, y, h]?`);
        else if (dd < DEFAULTS.doorRadius + 0.05)
          bad(`stands ${dd.toFixed(2)} m from the door, inside its own ` +
              `${DEFAULTS.doorRadius} m trigger — you would arrive holding the prompt`);
        // ...and the same question for the OTHER trigger class. An override is a
        // PROPOSAL, checked like every other: a hand-authored point inside a cut band
        // is the door-7 defect authored on purpose, so it is refused rather than pushed
        // (pushing would silently move somebody's considered coordinate).
        else if (worstBand(cuts, [dovr[0], oy, dovr[2]]).clr < BAND_CLEAR) {
          const wb = worstBand(cuts, [dovr[0], oy, dovr[2]]);
          bad(`clears the ${cutTag(wb.cut)} cut band by only ${wb.clr.toFixed(3)} m ` +
              `(floor ${BAND_CLEAR} m) — the cut would fire on arrival and the door ` +
              `would render two shots`);
        } else {
          sp[0] = dovr[0]; sp[1] = oy; sp[2] = dovr[2];
          spSrc = `arrival override '${key2}' on camera '${shot}' (derived point was via ${via})`;
        }
      }
    }
    edges.push({
      id: eid(key, ikey, lm.id), from: key, to: ikey, kind: 'door', of: lm.id,
      at: r3(at), r: DEFAULTS.doorRadius, vTol: DEFAULTS.vTol,
      spawn: r3([ipad[0], ipad[1], ipad[2]]), spawnYaw: null, cam: null,
      camFrom: shot,
      label: `Enter ${short}`, key: DEFAULTS.key,
      reciprocal: eid(ikey, key, lm.id),
      source: `${townId}.map.json landmark '${lm.id}' (enterable) -> ` +
              (lm.doorstepFromMap
                ? `its MAP point ("doorstepFromMap": the map moved this door and the bundle's ` +
                  `walk_pad_${lm.id} is stale until the next bake)`
                : `walk_pad_${lm.id}` +
                  (padOff == null ? ' (MISSING — trigger fell back to the landmark centre)'
                                  : `, its doorstep ${padOff.toFixed(2)}u off the landmark centre`)) +
              (shot ? `; offered only in shot '${shot}'` : ''),
    });
    edges.push({
      id: eid(ikey, key, lm.id), from: ikey, to: key, kind: 'door', of: lm.id,
      at: r3([ipad[0], ipad[1], ipad[2]]), r: DEFAULTS.doorRadius, vTol: DEFAULTS.vTol,
      spawn: r3(sp), spawnYaw: null, cam: shot ? {key: shot} : null,
      label: `Leave ${short}`, key: DEFAULTS.key,
      reciprocal: eid(key, ikey, lm.id),
      source: `${ikey} walk_pad_door -> ${townId} street ${spSrc}` +
              (shot ? `; arrives in shot '${shot}'` : ''),
    });
  }

  // --- IN-TOWN PASSAGES --------------------------------------------------------
  // A PASSAGE is a prompted transition between two places INSIDE one town, for a
  // connection the player is meant to make but cannot walk. Added 2026-08-02 for the
  // Dellhollow gate stair (USER REDLINE, live play: "the stairs leading back up to the
  // gate are completely inaccessible... have the transition point to the gate happen
  // more or less where the Boatman's Rest is"). The gate tier and the shelf street are
  // 5 m apart in height and the ONLY map connection between them is that flight, so
  // removing it as a route without putting something in its place would strand the
  // gate — and the town's overworld exit is on it.
  //
  // IT IS NOT A NEW RUNTIME CONCEPT. It is the scene-internal edge the graph already
  // documents (to === from, `cam` filled in), with a prompt instead of `auto`: the
  // runtime fades, moves the player to `spawn`, applies `cam`. Doors already do exactly
  // this across scenes; camera cuts already do exactly this within one. play3d switches
  // on nothing here, and markersTick covers every transition class since 2026-08-02.
  //
  // WHY A MAP RECORD AND NOT AN EDGE TYPE: a walk edge means walkable ground, and every
  // consumer treats it that way (cine_regions looks for its ribbon, routes_derive walks
  // it, the blockout builds a flight for it). A passage carries no ground. It is stated
  // in its own `passages` block so a reader never has to ask which walk edges are real.
  //
  // AN END IS EITHER A LANDMARK OR A STATED POINT. `{"at": "<landmark id>"}` takes the
  // landmark's walk pad, exactly as a door does. `{"pos": [x, y, h], "id": "..."}` states
  // a point in MAP coordinates, for a place the town has no landmark for — the Dellhollow
  // gate stair's FOOT is one: it is the stair's landing, not a building, and giving it a
  // landmark would put a second door-sized pad on top of the inn's. Its height and its
  // owning shot are still MEASURED (walk surface, ownership regions), never declared.
  const pregions = cine ? shotRegions(cine, glbPath) : null;
  const endPoint = (e, what) => {
    if (e.at) {
      const lm = map.landmarks.find((l) => l.id === e.at);
      if (!lm) { W(`${what}: no landmark '${e.at}' in ${townId}.map.json — passage skipped`); return null; }
      const at = T(lm.pos);
      const pad = padStand(key, 'walk_pad_' + e.at);
      if (pad) { at[0] = pad[0]; at[1] = pad[1]; at[2] = pad[2]; }
      else W(`${what}: no walk_pad_${e.at} in '${key}' — trigger fell back to the landmark centre`);
      return {id: e.at, name: lm.name, lm, at, shot: shotOf(e.at)};
    }
    if (!Array.isArray(e.pos) || e.pos.length !== 3) {
      W(`${what}: an end needs "at": "<landmark id>" or "pos": [x, y, h] — passage skipped`); return null;
    }
    const at = T(e.pos);
    const ry = walkYNear(key, at[0], at[2], at[1], DEFAULTS.passageRadius);
    if (ry == null) W(`${what}: stated point (${at[0].toFixed(1)},${at[2].toFixed(1)}) has no walk ` +
                      `surface within ${DEFAULTS.passageRadius}u — the passage will be unreachable on foot`);
    else { at[1] = ry.y; if (ry.off) W(`${what}: trigger height taken from a walk surface ${ry.off.toFixed(2)}u away`); }
    return {id: e.id || 'point', name: e.name || e.id || 'point', lm: null, at,
            shot: pregions ? ownerShot(pregions, at) : null};
  };
  for (const pg of map.passages || []) {
    const ends = pg.ends || [];
    if (ends.length !== 2) { W(`passage '${pg.id}': "ends" must be exactly two`); continue; }
    const A = endPoint(ends[0], `passage '${pg.id}' end 0`);
    const B = endPoint(ends[1], `passage '${pg.id}' end 1`);
    if (!A || !B) continue;
    const back = DEFAULTS.passageRadius + DEFAULTS.spawnBackoff;
    // The ARRIVAL at each end is derived by the same rules a door's return spawn is: step
    // off along the flattest FLAT walk edge touching the landmark (or, for a stated point,
    // toward the other end), take the height from the walk surface, then push clear of
    // every camera-cut band on the arrival's own shot's ground.
    const arrive = (E, other) => {
      let dir, via;
      if (E.lm) ({dir, via} = streetDir(map, E.lm.id, T));
      // AWAY from the other end, not toward it. A passage's arrival is a back-off from
      // the passage's own MOUTH, exactly as a door's return spawn is a back-off from the
      // door: stepping toward the far end walks you back into the thing you just used.
      // Measured on the gate stair — toward-the-gate put the arrival 4.10 m off, on the
      // flight itself; away puts it on the street the player is arriving into.
      else { dir = norm2(E.at[0] - other.at[0], E.at[2] - other.at[2]);
             via = 'the stated point, backing off from the passage mouth'; }
      const sp = [E.at[0] + dir[0] * back, E.at[1], E.at[2] + dir[1] * back];
      const y = walkY(key, sp[0], sp[2], E.at[1]);
      if (y == null) {
        // Same doctrine as the door spawns: SEARCH, do not assume. The winner is the
        // least displacement from the derived point, on the trigger's own tier.
        //
        // TIER TOLERANCE 0.5 m, NOT vTol. A passage end is a stated point on ONE surface,
        // and here the surface 1.2 m above the gate stair's foot is THE STAIR ITSELF: at
        // vTol the search happily returned (24.4, -3.8) at h 20.24, i.e. an arrival
        // standing mid-flight on the very stairs this passage exists to replace. One
        // riser is not "the same ground".
        const hit = searchClearOfBands(key, cuts, E.at, dir, sp, back, pregions, E.shot, 0.5);
        if (hit) { sp[0] = hit.px; sp[1] = hit.y; sp[2] = hit.pz;
          W(`passage '${pg.id}' arrival at '${E.id}': derived point was off the walk ` +
            `network — searched to (${hit.px.toFixed(1)},${hit.pz.toFixed(1)}), ${hit.off.toFixed(2)}u away`); }
        else W(`passage '${pg.id}' arrival at '${E.id}': (${sp[0].toFixed(1)},${sp[2].toFixed(1)}) ` +
               `is off the walk network and nothing legal was found — the derived point stands`);
      } else sp[1] = y;
      const note = clearBands(bandCtx, sp, E.at, dir, back, E.shot, `passage '${pg.id}' arrival at '${E.id}'`);
      return {sp, src: `via ${via}${note}`};
    };
    const aA = arrive(A, B), aB = arrive(B, A);
    if (cine && !A.shot) W(`passage '${pg.id}': end '${A.id}' is owned by no camera`);
    if (cine && !B.shot) W(`passage '${pg.id}': end '${B.id}' is owned by no camera`);
    const idAB = eid(key, key, `passage:${pg.id}:${A.id}>${B.id}`);
    const idBA = eid(key, key, `passage:${pg.id}:${B.id}>${A.id}`);
    const lblAB = ends[0].label || `To ${shortName(B.name)}`;
    const lblBA = ends[1].label || `To ${shortName(A.name)}`;
    const common = {from: key, to: key, kind: 'passage', of: pg.id,
                    r: DEFAULTS.passageRadius, vTol: DEFAULTS.vTol,
                    spawnYaw: null, key: DEFAULTS.key};
    edges.push(Object.assign({}, common, {
      id: idAB, at: r3(A.at), spawn: r3(aB.sp), camFrom: A.shot,
      cam: B.shot ? {key: B.shot} : null, label: lblAB, reciprocal: idBA,
      source: `${townId}.map.json passages '${pg.id}' ${A.id} -> ${B.id}; arrival ${aB.src}` +
              (A.shot ? `; offered only in shot '${A.shot}'` : '') +
              (B.shot ? `; arrives in shot '${B.shot}'` : '') +
              (pg.note ? `; ${pg.note}` : ''),
    }));
    edges.push(Object.assign({}, common, {
      id: idBA, at: r3(B.at), spawn: r3(aA.sp), camFrom: B.shot,
      cam: A.shot ? {key: A.shot} : null, label: lblBA, reciprocal: idAB,
      source: `${townId}.map.json passages '${pg.id}' ${B.id} -> ${A.id} (the same passage, back); arrival ${aA.src}` +
              (B.shot ? `; offered only in shot '${B.shot}'` : '') +
              (A.shot ? `; arrives in shot '${A.shot}'` : ''),
    }));
    // TWO PROMPTS MUST NOT SHARE GROUND. A player standing where a door, a portal and a
    // passage all offer themselves gets whichever the runtime happens to rank first, and
    // the others are unreachable. Checked here rather than left to play testing, because
    // the whole point of this record is that the gate transition TAKES ground another
    // prompt used to hold — measured, the gate stair's own head is 1.42 m from the
    // overworld exit's pad, which is why this passage's gate end stands 4.42 m east.
    for (const E of [A, B]) for (const d of edges) {
      if (d.from !== key || !d.label || d.auto || d.of === pg.id) continue;
      const gap = Math.hypot(d.at[0] - E.at[0], d.at[2] - E.at[2]);
      if (gap < d.r + DEFAULTS.passageRadius && Math.abs(d.at[1] - E.at[1]) <= DEFAULTS.vTol)
        W(`passage '${pg.id}' end '${E.id}': its ${DEFAULTS.passageRadius} m trigger ` +
          `overlaps the '${d.of}' door's ${d.r} m trigger — ${gap.toFixed(2)} m apart, ` +
          `so ONE OF THE TWO PROMPTS IS UNREACHABLE. Move the door's landmark or the passage.`);
    }
  }

  // --- THE CAMERA CUTS ---------------------------------------------------------
  // A cut is DERIVED, not authored: wherever the town's walk network crosses from
  // one camera's owned records into another's, a reciprocal pair of scene-internal
  // edges (to === from) appears. So "the camera changes at every region boundary" is
  // a theorem about the ownership table in dellhollow.cameras.json, not a list
  // anybody maintains. They are labelless and `auto`: the runtime fires them on
  // entry with a fade and no prompt, because a camera change is not a choice — the
  // prompt is reserved for doors and portals, which are.
  if (!cine) continue;
  const CG = townMaps[townId].CG;               // solved above, before the doors
  for (const n of CG.noRibbon) noRibbon.push(n);
  for (const c of CG.cuts) {
    const t3 = c.t.toFixed(3);
    const idF = `${key}>${key}@cut:${c.edge}:${t3}:${c.from}>${c.to}`;
    const idB = `${key}>${key}@cut:${c.edge}:${t3}:${c.to}>${c.from}`;
    const common = {from: key, to: key, kind: 'cut', of: c.edge, at: c.at, band: c.band,
                    vTol: c.vTol, auto: true, label: null, key: null, spawnYaw: null};
    edges.push(Object.assign({}, common, {
      id: idF, camFrom: c.from, cam: {key: c.to}, spawn: c.spawnTo, reciprocal: idB,
      source: `camera boundary '${c.from}' -> '${c.to}' where the walk network crosses ` +
              `${c.whatFrom} into ${c.whatTo}; seam slid to ${c.edge}@t=${t3}, band ` +
              `half-width ${c.band.w}u measured off the walk surface, clearance margin ${c.margin}u`,
    }));
    edges.push(Object.assign({}, common, {
      id: idB, camFrom: c.to, cam: {key: c.from}, spawn: c.spawnFrom, reciprocal: idF,
      source: `camera boundary '${c.to}' -> '${c.from}' (the same seam, back)`,
    }));
  }
}

// --- regions: road portals into towns, and the reciprocal town exit -----------
for (const reg of world.regions || []) {
  const R = rd(reg.file);
  const rkey = regionSceneKey(reg);
  if (!rkey) { W(`region '${reg.id}': no bundle — skipped`); continue; }
  // TILE CENTRE, READ FROM THE MAP.  This used to be inferred from the massifs'
  // extent (280 x 196 -> origin 140,98) while tools/valley_map.py hardcoded
  // 280 x 200 -> origin 140,100 — and the tile that ships is valley_map's.  The 2u
  // gap put every ow-valley coordinate in this file 2u north of the road ribbon it
  // was measured on: the del-cine>ow-valley arrival came out 1.86u from a ribbon
  // 1.0u wide, which is the three "arrival stands on walk network" reds (one edge,
  // asserted three times by the itinerary).  world.json regions[].tile is now the
  // single statement.  Inferring is REFUSED rather than fallen back on: a plausible
  // wrong tile is what made this survive a validator, 52 assertions and a review.
  if (!reg.tile) {
    W(`region '${reg.id}': no 'tile' in world.json — the terrain tile and its origin must be STATED, not inferred; region skipped`);
    continue;
  }
  const [TW, TH] = reg.tile.size, [CX, CY] = reg.tile.origin;
  const T = (p) => [p[0] - CX, p[2], CY - p[1]];            // world/region -> runtime
  addNode(rkey, {
    label: reg.name, kind: 'region', rt: true, params: {rt: '1'},
    bundle: `assets/scenes/${rkey}/`,
    origin: `${reg.file} (region '${reg.id}', tile ${TW}x${TH}, origin at ${CX},${CY})`,
  });

  const road = ((R.road || {}).points || []).map(T);
  for (const p of (R.road || {}).portals || []) {
    // AN UNPAIRED PORTAL IS A NAMED ROW, NEVER SILENCE (2026-08-02). This used to be
    // `if (!p.target || !townMaps[p.target]) continue;` — one wordless skip that hid the
    // user-reported defect "there's no entry marker for entering Emberbrook from the old
    // gate" for as long as it existed. No edge is derived, therefore no prompt and no
    // marker CAN render, and nothing anywhere said so. A portal declared in the region
    // and dropped by the derive now prints its own name.
    if (!p.target) {
      W(`region '${reg.id}' road.portals '${p.id}': "target": null — UNPAIRED, so no edge, ` +
        `no prompt and no marker exist at it. Point it at a town (and name the town's ` +
        `exit id in "exit") to wire it; leave it null only if the passage is fiction ` +
        `(${p.note ? String(p.note).slice(0, 90) : 'no note'})`);
      unpaired.push(`region '${reg.id}' road.portals '${p.id}' — target:null`);
      continue;
    }
    if (!townMaps[p.target]) {
      W(`region '${reg.id}' road.portals '${p.id}': target '${p.target}' is not a derived ` +
        `town (no world.json town landmark, or its bundle is missing) — UNPAIRED, no edge`);
      unpaired.push(`region '${reg.id}' road.portals '${p.id}' — target '${p.target}' is not a derived town`);
      continue;
    }
    const {map, key: tkey} = townMaps[p.target];
    const TT = (q) => [q[0], q[2], -q[1]];
    const town = map.displayName || p.target;
    const at = T(p.at);
    const ry = walkYNear(rkey, at[0], at[2], at[1], DEFAULTS.gateRadius);
    if (ry == null) W(`portal '${p.id}': no walk surface within r of the trigger (${at[0].toFixed(1)},${at[2].toFixed(1)}) in '${rkey}' — the gate may be unreachable on foot`);
    else { if (ry.off) W(`portal '${p.id}': trigger height taken from a walk surface ${ry.off.toFixed(2)}u away (the road ribbon stops short of the portal point)`); at[1] = ry.y; }

    // THE TOWN-SIDE EXIT IS CHOSEN BY NAME (2026-08-02). This was
    // `(map.exits||[]).find(e => (e.mode||'land')==='land')` — THE FIRST LAND EXIT IN THE
    // FILE — which is a latent trap of exactly the class the arrival ordering rules above
    // exist to forbid: a town with two land exits paired BOTH of its region portals to the
    // same one, and reordering the map's `exits` array silently re-wired the town. Measured
    // consequence: `old-gate` could never reach Emberbrook's 'sigil-gate-downstream'
    // because 'valley-road-south' is listed first. The portal now DECLARES which exit it
    // is the other half of ("exit": "<exit id>"), the same way world.json regions declare
    // their sceneKey rather than having it inferred. First-in-list survives only as a
    // stated fallback for a town with exactly one land exit.
    const lands = (map.exits || []).filter((e) => (e.mode || 'land') === 'land');
    let exit = null, exitWhy = '', gateFlag = null;
    if (p.exit) {
      exit = lands.find((e) => e.id === p.exit) || null;
      if (!exit)
        W(`region '${reg.id}' portal '${p.id}': names exit '${p.exit}' but ` +
          `${p.target}.map.json has no land exit with that id (has: ` +
          `${lands.map((e) => e.id).join(', ') || 'none'}) — falling back`);
      else exitWhy = `named by the portal ("exit": "${p.exit}")`;
    }
    if (!exit) {
      const open = lands.filter((e) => !e.sealed);
      exit = open[0] || null;
      exitWhy = `first unsealed land exit — the portal names none`;
      if (lands.length > 1)
        W(`region '${reg.id}' portal '${p.id}': no "exit" id, and ${p.target} declares ` +
          `${lands.length} land exits (${lands.map((e) => e.id).join(', ')}) — took ` +
          `'${exit ? exit.id : '(none)'}' by FILE ORDER. REQUEST: add "exit": "<id>" to ` +
          `the portal so the pairing is stated, not positional`);
    }
    // SEALED IS READ, and it is read HERE rather than left to the runtime, because a
    // sealed passage that ships an edge ships a prompt and a floor marker — a red arrow
    // pointing at a gate that does not open. The exit stays declared, the row stays
    // explained (see `sealed` in this document), and the edge appears the day the map
    // stops saying sealed.
    // SEALED IS READ HERE, and since 2026-08-02 it produces one of TWO things.
    //
    //   sealed WITHOUT sealedUntil   -> no edge at all. Nothing can ever open it, so
    //                                   an edge would be a promise the data cannot keep.
    //   sealed WITH sealedUntil      -> a CONDITIONAL edge, carrying
    //                                   `when: {flag: "<sealedUntil>"}`.
    //
    // The second case is new because the runtime half finally exists: play3d.html's
    // sgLive() evaluates `when` with Dialogue.check (the same evaluator dialogue.json's
    // conditions use, reading GS.state.flags) on every physics tick, and sgTick,
    // markersTick, SIM.edges and SIM.door all consult it. So a conditional edge is
    // exactly the absence it used to be — no prompt, no marker, not takeable — until the
    // flag turns true, and then it and its marker appear the same frame, with nothing
    // reloaded. That last property is why the gate is per-tick and not a bind-time
    // filter: the beat that opens the Old Gate stands the player in front of it.
    //
    // The `sealed` block below is still written, because "which pairs are story-gated
    // and on what" is a fact a reader of this document should not have to reconstruct
    // by grepping edges for `when`.
    if (exit && exit.sealed) {
      sealed.push({
        portal: `${reg.id}:${p.id}`, town: p.target, exit: exit.id, at: exit.at,
        opensOn: exit.sealedUntil || null,
        note: `${exit.note || ''}`.slice(0, 200),
        effect: exit.sealedUntil
          ? `a CONDITIONAL edge pair carrying when:{flag:"${exit.sealedUntil}"} — no prompt, ` +
            `no marker and not takeable until that flag is true; live the frame it is`
          : 'NO edge, NO prompt, NO marker — the sealed presentation is the absence',
      });
      if (!exit.sealedUntil) {
        W(`region '${reg.id}' portal '${p.id}' <-> ${p.target} exit '${exit.id}' (${exitWhy}): ` +
          `the exit is SEALED and declares no "sealedUntil" flag — nothing can ever open it, ` +
          `so no edge is derived. State the flag.`);
        continue;
      }
      gateFlag = exit.sealedUntil;
    }
    if (exit) paired.add(`${p.target}:${exit.id}`);
    const gateId = exit ? exit.at : (map.landmarks.find((l) => l.class === 'portal' && l.mapVisible) || {}).id;
    const gate = map.landmarks.find((l) => l.id === gateId);
    if (!gate) { W(`town '${p.target}': no land exit landmark — portal '${p.id}' skipped`); continue; }
    const gAt = TT(gate.pos);
    const gPad = padStand(tkey, 'walk_pad_' + gate.id);
    if (gPad) gAt[1] = gPad[1];

    // region-side spawn: back UP the region's own road polyline, past the radius
    const back = DEFAULTS.gateRadius + DEFAULTS.spawnBackoff;
    let rsp = [at[0], at[1], at[2]];
    let i = 0, bd = Infinity;
    road.forEach((q, k) => { const d = Math.hypot(q[0] - at[0], q[2] - at[2]); if (d < bd) { bd = d; i = k; } });
    for (let k = i, acc = 0; k > 0; k--) {
      const a = road[k], b = road[k - 1], seg = Math.hypot(b[0] - a[0], b[2] - a[2]);
      if (acc + seg >= back) { const t = (back - acc) / seg;
        rsp = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; break; }
      acc += seg; rsp = [b[0], b[1], b[2]];
    }
    const rspY = walkY(rkey, rsp[0], rsp[2], rsp[1]);
    if (rspY == null) W(`portal '${p.id}': region spawn (${rsp[0].toFixed(1)},${rsp[2].toFixed(1)}) is off the walk network`);
    else rsp[1] = rspY;
    // face down the road (toward the gate): ORBIT.yaw places the camera at
    // (cos,sin)*dist from the target, so the VIEW direction is its negation.
    const [fx, fz] = norm2(at[0] - rsp[0], at[2] - rsp[2]);
    const rYaw = Math.round(Math.atan2(-fz, -fx) * 1e4) / 1e4;

    // town-side spawn: on the gate pad, pushed in along its first street
    const {dir, via} = streetDir(map, gate.id, TT);
    const tback = DEFAULTS.portalRadius + DEFAULTS.spawnBackoff;
    const tsp = [gAt[0] + dir[0] * tback, gAt[1], gAt[2] + dir[1] * tback];
    const tspY = walkY(tkey, tsp[0], tsp[2], gAt[1]);
    if (tspY == null) W(`portal '${p.id}': town spawn (${tsp[0].toFixed(1)},${tsp[2].toFixed(1)}) is off the walk network`);
    else tsp[1] = tspY;
    // the shot the town's gate stands in: arriving from the region opens the town on
    // that camera, and the way back out is only offered while it is up
    const tcine = townMaps[p.target].cine;
    const gShot = (tcine && tcine.lmOwner[gate.id]) || null;
    if (tcine && !gShot) W(`town '${p.target}': gate landmark '${gate.id}' is owned by no camera`);

    // A portal's town-side arrival is an ARRIVAL: same rule as a door's return spawn.
    // Walking in from the road must not put the player inside a cut band. The ground
    // it must land on is gShot's even when the town opens on an establishing PLATE —
    // a plate owns no walk record, and the handoff is to the gate's walkable shot.
    const tBandNote = clearBands({key: tkey, cuts: townMaps[p.target].cuts,
                                  cine: tcine, glbPath: townMaps[p.target].glbPath},
                                 tsp, gAt, dir, tback, gShot,
                                 `portal '${p.id}' town spawn`);
    const [tfx, tfz] = norm2(tsp[0] - gAt[0], tsp[2] - gAt[2]);
    // THE ESTABLISHING PLATE (coordinator ruling, cinematic class). A town may open on a
    // CINEMATIC shot — a non-walkable establishing frame that shows the whole place
    // before the player is asked to walk in it. A camera declares itself the town's
    // arrival plate with `"cinematic": true, "establishing": true`, and only ONE may:
    // "the shot the town opens on" is singular by definition.
    //
    // HOW THE HANDOFF HAPPENS, and why it needs no runtime mechanism of its own: a plate
    // owns no walk record, so it appears in NO ownership region, so the moment the
    // arriving player is ticked the runtime's positional safety net (play3d sgCorrect)
    // finds them standing on the walkable shot's ground under a camera that owns none of
    // it, and corrects — which is precisely "show the plate, then hand off to the first
    // walkable shot". The net was built for slides and knockbacks; a plate is the same
    // fact (the camera is wrong for where you are) arriving on purpose. `handoff` states
    // which shot it will land on, so the wiring RECORDS the intent instead of leaving a
    // reader to re-derive it, and so a test can assert it.
    //   THE HOLD IS defaults.correctionGrace PHYSICS STEPS — currently 20, about a third
    // of a second. That is long enough to prove the mechanism and too short to read an
    // establishing shot. A held plate (an authored dwell, skippable) is a play3d.html
    // change and play3d.html is coordinator-owned: requested, not taken.
    const plates = (tcine ? tcine.cams : []).filter((c) => c.cinematic && c.establishing);
    if (plates.length > 1)
      W(`town '${p.target}': ${plates.length} cameras claim "establishing" ` +
        `(${plates.map((c) => c.id).join(', ')}) — a town opens on ONE shot; first wins`);
    const plate = plates[0] || null;
    const arriveShot = plate ? plate.id : gShot;
    edges.push({
      id: eid(rkey, tkey, p.id), from: rkey, to: tkey, kind: 'portal', of: p.id,
      at: r3(at), r: DEFAULTS.gateRadius, vTol: DEFAULTS.vTol,
      spawn: r3(tsp), spawnYaw: Math.round(Math.atan2(-tfz, -tfx) * 1e4) / 1e4,
      cam: arriveShot ? {key: arriveShot} : null,
      ...(plate && gShot ? {handoff: {key: gShot, via: 'positional correction'}} : {}),
      ...(gateFlag ? {when: {flag: gateFlag}, requires: gateFlag} : {}),
      label: `Enter ${town}`, key: DEFAULTS.key,
      reciprocal: eid(tkey, rkey, p.id),
      source: `${reg.file} road.portals '${p.id}' target '${p.target}' -> ${gate.id} (${via})` +
              (gateFlag ? `; SEALED until story flag '${gateFlag}' (the runtime withholds prompt AND marker until then)` : '') +
              tBandNote +
              (plate
                ? `; opens on the CINEMATIC plate '${plate.id}', which owns no ground and ` +
                  `hands off to '${gShot}' by positional correction`
                : gShot ? `; arrives in shot '${gShot}'` : ''),
    });
    edges.push({
      id: eid(tkey, rkey, p.id), from: tkey, to: rkey, kind: 'portal', of: gate.id,
      at: r3(gAt), r: DEFAULTS.portalRadius, vTol: DEFAULTS.vTol,
      spawn: r3(rsp), spawnYaw: rYaw, cam: null, camFrom: gShot,
      ...(gateFlag ? {when: {flag: gateFlag}, requires: gateFlag} : {}),
      label: `Leave ${town}`, key: DEFAULTS.key,
      reciprocal: eid(rkey, tkey, p.id),
      source: `${p.target}.map.json exit '${exit ? exit.id : gate.id}' at '${gate.id}' -> ${reg.file} portal '${p.id}'` +
              (exit ? ` (${exitWhy})` : ''),
    });
  }
}

// --- the other half of the audit: town exits nothing paired -------------------
// A land exit declared in a town map and named by no region portal is the same hole
// seen from the other side, and it was equally silent. Named here so the count of
// unwired passages in this document is the whole count.
for (const [townId, {map}] of Object.entries(townMaps)) {
  for (const x of (map.exits || [])) {
    if ((x.mode || 'land') !== 'land') continue;
    if (paired.has(`${townId}:${x.id}`)) continue;
    if (sealed.some((s) => s.town === townId && s.exit === x.id)) continue;
    W(`town '${townId}' exit '${x.id}' at '${x.at}' (to ${x.to || '?'}): declared in the ` +
      `map and named by NO region portal — UNPAIRED, so no edge, no prompt and no marker ` +
      `exist at it. Give a region portal "target": "${townId}", "exit": "${x.id}"` +
      (/^overworld-/.test(String(x.to)) ? `, or leave it unpaired until region '${x.to}' exists` : ''));
    unpaired.push(`town '${townId}' exits '${x.id}' at '${x.at}' -> ${x.to || '?'} — no region portal names it`);
  }
}

// ------------------------------------------------------------------ the file --
const doc = {
  _doc: [
    'SCENE GRAPH — the wiring of Emberbrook\'s scenes into one continuous game.',
    'GENERATED by tools/scenegraph_derive.mjs from the map files. NEVER hand-edit:',
    're-run the generator after any map change (`node tools/scenegraph_derive.mjs`,',
    '`--check` fails if this file is stale). Consumed by public/play3d.html.',
    '',
    'nodes: sceneKey -> { label, kind: region|town|interior, rt (real-time explore',
    '  camera vs fixed pre-rendered camera), params (extra URL params the scene needs),',
    '  bundle, origin (provenance) }. A node IS a play3d.html scene key.',
    '',
    'edges: DIRECTED. The player standing in `from` within `r` of `at` (and within',
    '  `vTol` in height — Dellhollow stacks tiers, so the horizontal test alone would',
    '  cross-trigger between them) is offered `label` on key `key`; taking it fades',
    '  out, loads `to` with the player placed at `spawn` (an override the runtime reads',
    '  as ?sx&sy&sz, ahead of every other spawn source), and fades in.',
    '  at/spawn are RUNTIME coords of their OWN scene: [x, y(up), z], +x east +z south.',
    '  `of` is the map record the edge came from; `source` spells out the derivation.',
    '  `reciprocal` is the edge that comes back, so a tester can assert round trips.',
    '',
    'SCENE-INTERNAL EDGES (for the camera-scene navigation layer): an edge with',
    '  to === from is a HANDOFF INSIDE one scene — no page load, no reload of a large',
    '  bundle. The runtime fades, moves the player to `spawn`, applies `cam`, fades in.',
    '  That is how townwalk->townwalk camera cuts are meant to be authored: same record',
    '  type, `to` equal to `from`, and `cam` filled in. `cam` is a reserved slot the',
    '  runtime hands to applyCam() untouched; `spawnYaw` (radians) already steers the',
    '  real-time follow camera on arrival. Nothing in the runtime switches on `kind`.',
    '',
    'ARRIVAL POINTS are derived, and derived ORDER-INDEPENDENTLY: an interior exit puts',
    '  you on the street outside its door, one radius + defaults.spawnBackoff along the',
    '  flattest FLAT-type (road/deck/path/bridge) walk edge touching that landmark, ties',
    '  broken lexicographically — never "the first edge in the map file", which would let',
    '  a reordered map move every arrival. The region-side arrival walks BACK along the',
    '  region road polyline by the same margin. Every arrival is asserted to stand on a',
    '  walk surface by tools/slice_test.mjs. A door arrival that lands on NO walk surface',
    '  is SEARCHED to the nearest legal one (out along the street first, then swept +/-60',
    '  deg, always >= the back-off from the trigger) and `source` says so — a town whose',
    '  streets are whole never enters that branch, so it cannot move one.',
    '',
    'defaults: every tunable of the transition layer (fade time, prompt format, radii,',
    '  the arrival back-off). The runtime has no radii/timings/labels of its own, so',
    '  retuning the whole game is an edit HERE, and adding a scene or a door is a map',
    '  edit + a re-run — never a code change.',
  ],
  version: 1,
  generated: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
  generator: 'tools/scenegraph_derive.mjs',
  sources: ['world/world.json',
            ...(world.regions || []).map((r) => r.file),
            ...Object.values(townMaps).map((t) => t.lm.refinesTo)],
  defaults: DEFAULTS,
  nodes,
  edges,
  warnings: warn,
  noRibbon,
  // THE UNWIRED INVENTORY — every declared passage that is NOT an edge, and why.
  // `sealed` rows are story-gated and their absence is the intended presentation;
  // `unpaired` rows are holes. A row here is an EXPLAINED row in the declared-vs-derived
  // audit; a declared passage in neither list and in no edge is an unexplained one.
  sealed,
  unpaired,
};
doc._doc.splice(doc._doc.length - 6, 0,
  'CAMERA CUTS (kind: "cut"): a town whose map states a `cameraFile` is played through',
  '  FIXED pre-rendered shots, and the walk network crossing from one shot\'s owned map',
  '  records into another\'s becomes a reciprocal pair of scene-internal edges. They are',
  '  `auto` (the runtime takes them on entry, no keypress) and label-less (SILENT — a',
  '  camera change is not a choice; prompts are for doors and portals). `cam:{key}` is',
  '  the shot to apply, `camFrom` the shot in which the edge exists at all — needed',
  '  because a boundary and the boundary back are the SAME ground. Their trigger is a',
  '  BAND, not a circle: `band:{n,t,w}` is an oriented rectangle whose half-width was',
  '  measured off the walk surface, because a seam you can side-step on an 11 m deck is',
  '  a camera that never changes. Doors and portals into a cinematic town also carry',
  '  cam/camFrom, so a shop\'s door is only offered in the shot that frames it.',
  '',
  'PASSAGES (kind: "passage"): a PROMPTED transition between two places inside ONE town,',
  '  for a connection the player is meant to make and cannot walk (Dellhollow\'s gate stair).',
  '  Same scene-internal record as a camera cut — to === from, `cam` applied on arrival —',
  '  but with a label and a key instead of `auto`, because taking it IS a choice. Authored',
  '  in the town map\'s `passages` block, never as a walk edge: a walk edge means walkable',
  '  ground and every consumer treats it that way. An end is a landmark (its walk pad) or a',
  '  STATED POINT, whose height and owning shot are still measured off the bundle.',
  '',
  'SEALED / UNPAIRED (top-level, beside `warnings`): every DECLARED passage that is not an',
  '  edge, by name and with its reason — `sealed` for story-gated ones (with the flag that',
  '  opens them), `unpaired` for holes. Before these existed an unwired region portal was a',
  '  wordless skip, and "Emberbrook\'s old gate has no marker" had no trace in the tooling.',
  '',
  'THE ESTABLISHING PLATE (a camera with "cinematic": true + "establishing": true): the',
  '  portal INTO that town applies the plate instead of the walkable shot that owns the',
  '  gate, and carries `handoff:{key}` naming the shot it defers to. A plate owns no walk',
  '  record and therefore appears in no `shots` region, so the positional safety net makes',
  '  the handoff by itself — the plate is up until the player has been ticked, then the',
  '  camera corrects to the ground they are standing on. No prompt, no seam, no new',
  '  runtime concept.',
  '');

const json = JSON.stringify(doc, null, 1) + '\n';
if (ARGS.includes('--print')) { console.log(json); }
else if (ARGS.includes('--check')) {
  const cur = fs.existsSync(SHIPPED) ? fs.readFileSync(SHIPPED, 'utf8') : '';
  const strip = (s) => s.replace(/"generated": "[^"]*",?\n?/, '');
  if (strip(cur) !== strip(json)) { console.error('STALE: public/world/scenegraph.json differs from the maps. Re-run the generator.'); process.exit(1); }
  console.log('scenegraph.json is up to date with the maps.');
} else {
  fs.mkdirSync(path.dirname(OUT), {recursive: true});
  fs.writeFileSync(OUT, json);
  console.log('wrote ' + (OUT === SHIPPED ? 'public/world/scenegraph.json'
                                          : path.relative(process.cwd(), OUT)));
}

// summary (always, so a run is self-verifying at a glance)
console.log(`nodes ${Object.keys(nodes).length}  edges ${edges.length}  warnings ${warn.length}`);
for (const k of Object.keys(nodes)) {
  const out = edges.filter((e) => e.from === k), inn = edges.filter((e) => e.to === k);
  console.log(`  ${k.padEnd(20)} ${nodes[k].kind.padEnd(9)} out ${String(out.length).padStart(2)}  in ${String(inn.length).padStart(2)}  ${nodes[k].label}`);
}
for (const e of edges) {
  if (e.kind === 'cut')
    console.log(`  CUT  ${String(e.camFrom).padEnd(14)} -> ${String(e.cam.key).padEnd(14)} band w${e.band.w} t${e.band.t}  at ${e.at.join(',')}  spawn ${e.spawn.join(',')}  (${e.of})`);
  else
    console.log(`  ${e.from.padEnd(14)} -> ${e.to.padEnd(18)} r${e.r}  at ${e.at.join(',')}  spawn ${e.spawn.join(',')}  "${e.label}"${e.camFrom ? ' [in shot ' + e.camFrom + ']' : ''}${e.cam ? ' [-> shot ' + e.cam.key + ']' : ''}`);
}
if (noRibbon.length) { console.log('\nno camera boundary placed (map connection has no walk ribbon):');
  for (const n of noRibbon) console.log('  ' + n); }
if (sealed.length) { console.log('\nSEALED (declared, story-gated, deliberately no edge/prompt/marker):');
  for (const s of sealed) console.log(`  ${s.portal} <-> ${s.town} exit '${s.exit}' at '${s.at}'` +
    `  opens on ${s.opensOn || 'NO FLAG DECLARED'}`); }
if (unpaired.length) { console.log('\nUNPAIRED (declared passage, no edge — no prompt and no marker can render):');
  for (const u of unpaired) console.log('  ' + u); }

// ---- VALIDATION: no arrival materialises inside a camera-cut band ------------
// Asserted on the DOCUMENT that is about to ship, not on the intermediate values, so
// it is a check on the answer rather than a restatement of the derivation. Every town
// in one pass. The same assertion lives in tools/cine_test.mjs, which is where a
// hand-edit or a stale file gets caught; this one makes a derive run self-verifying.
{
  console.log('\nARRIVAL vs CAMERA-CUT BANDS (floor ' + BAND_CLEAR + ' m):');
  let checked = 0, red = 0;
  for (const e of edges) {
    if (e.kind === 'cut' || !e.spawn) continue;
    const mine = edges.filter((c) => c.kind === 'cut' && c.from === e.to);
    if (!mine.length) continue;
    checked++;
    const w = worstBand(mine, e.spawn);
    const bad = w.clr < BAND_CLEAR;
    if (bad) red++;
    console.log(`  ${bad ? 'RED ' : 'ok  '} ${e.id.padEnd(46)} ` +
      `${w.clr.toFixed(3)}u from ${cutTag(w.cut)}`);
  }
  console.log(`  ${checked - red}/${checked} arrivals clear every cut band` +
    (red ? ` — ${red} RED: a player would materialise already holding a cut` : ''));
  // console.error, not W(): the document has already been serialised above, so a push
  // to `warn` here would be a warning that never reaches the file it claims to describe
  // — and --check compares text, so a warning that appears only sometimes would make
  // the shipped file look stale. The RED lines above are the record; cine_test asserts.
  if (red) console.error(`  WARN ${red} arrival spawn(s) sit inside or within ` +
    `${BAND_CLEAR} m of a camera-cut band — see tools/cine_test.mjs`);
}
