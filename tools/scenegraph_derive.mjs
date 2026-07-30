// scenegraph_derive.mjs — DERIVE public/world/scenegraph.json from the map files.
//
//   node tools/scenegraph_derive.mjs            # write public/world/scenegraph.json
//   node tools/scenegraph_derive.mjs --check    # fail if the shipped file is stale
//   node tools/scenegraph_derive.mjs --print    # dump, write nothing
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
import {loadCine, cutGeometry, shotRegions} from './cine_regions.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const PUB = path.join(ROOT, 'public');
const OUT = path.join(PUB, 'world/scenegraph.json');
const ARGS = process.argv.slice(2);
const rd = (p) => JSON.parse(fs.readFileSync(path.join(PUB, p), 'utf8'));
const warn = [];
const W = (m) => { warn.push(m); console.error('  WARN ' + m); };
// map connections that carry no walkable geometry, so no camera boundary is placed on
// them. Recorded rather than silently dropped: if a ladder is ever made climbable its
// cut appears by itself.
const noRibbon = [];

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
  // A town with a cameraFile is played through FIXED cameras: it is not a real-time
  // explore scene, so it must not be handed rt=1. Both facts come from the map.
  let cine = null;
  if (map.cameraFile) {
    try { cine = loadCine(lm.refinesTo, map.cameraFile); }
    catch (e) { W(`town '${lm.id}': cameraFile '${map.cameraFile}' unreadable (${e.message}) — no camera cuts`); }
    if (cine) for (const m of cine.warn) W(`cameras(${lm.id}): ${m}`);
  }
  const fixedCam = !!(cine && cine.camFile.sceneKey === key);
  townMaps[lm.id] = {map, key, lm, cine: fixedCam ? cine : null};
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

for (const [townId, {map, key, cine}] of Object.entries(townMaps)) {
  const T = (p) => [p[0], p[2], -p[1]];                     // town map -> runtime
  // which shot frames a given landmark (null when the town has no cameras)
  const shotOf = (id) => (cine && cine.lmOwner[id]) || null;
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

    // TOWN SIDE: trigger on the landmark's door pad (map coords; the bundle's
    // walk_pad_<id> is cross-checked below)
    const at = T(lm.pos);
    const pad = padStand(key, 'walk_pad_' + lm.id);
    if (pad) {
      const d = Math.hypot(pad[0] - at[0], pad[2] - at[2]);
      if (d > 0.25) W(`${lm.id}: map pad and bundle walk_pad_${lm.id} disagree by ${d.toFixed(2)}u`);
      at[1] = pad[1];                                       // pad TOP: the height you stand at
    } else W(`${lm.id}: no walk_pad_${lm.id} in '${key}'`);

    // INTERIOR SIDE: the room's own door pad — where the runtime already spawns
    const ipad = padStand(ikey, 'walk_pad_door');
    if (!ipad) { W(`${ikey}: no walk_pad_door — interior edges skipped`); continue; }

    // return spawn: off the pad, along the street, clear of the enter radius
    const {dir, via} = streetDir(map, lm.id, T);
    const back = DEFAULTS.doorRadius + DEFAULTS.spawnBackoff;
    const sp = [at[0] + dir[0] * back, at[1], at[2] + dir[1] * back];
    const spY = walkY(key, sp[0], sp[2], at[1]);
    if (spY == null) W(`${lm.id}: return spawn (${sp[0].toFixed(1)},${sp[2].toFixed(1)}) is off the walk network`);
    else sp[1] = spY;

    // WHICH SHOT frames this door. The town-side edge only exists while that shot is
    // up (camFrom), and the way back out selects it on arrival (cam) — so leaving the
    // inn puts you on the street under the camera that frames the inn's door, never
    // under whatever shot the player happened to enter from.
    const shot = shotOf(lm.id);
    if (cine && !shot) W(`${lm.id}: enterable but owned by no camera — its door has no shot`);
    edges.push({
      id: eid(key, ikey, lm.id), from: key, to: ikey, kind: 'door', of: lm.id,
      at: r3(at), r: DEFAULTS.doorRadius, vTol: DEFAULTS.vTol,
      spawn: r3([ipad[0], ipad[1], ipad[2]]), spawnYaw: null, cam: null,
      camFrom: shot,
      label: `Enter ${short}`, key: DEFAULTS.key,
      reciprocal: eid(ikey, key, lm.id),
      source: `${townId}.map.json landmark '${lm.id}' (enterable) -> walk_pad_${lm.id}` +
              (shot ? `; offered only in shot '${shot}'` : ''),
    });
    edges.push({
      id: eid(ikey, key, lm.id), from: ikey, to: key, kind: 'door', of: lm.id,
      at: r3([ipad[0], ipad[1], ipad[2]]), r: DEFAULTS.doorRadius, vTol: DEFAULTS.vTol,
      spawn: r3(sp), spawnYaw: null, cam: shot ? {key: shot} : null,
      label: `Leave ${short}`, key: DEFAULTS.key,
      reciprocal: eid(key, ikey, lm.id),
      source: `${ikey} walk_pad_door -> ${townId} street via ${via}` +
              (shot ? `; arrives in shot '${shot}'` : ''),
    });
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
  const CG = cutGeometry(cine, path.join(bundleDir(key), 'scene.glb'), W);
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
  // tile centre: the region's terrain tile is the parent massifs' extent, and
  // valley_map puts the blender/runtime origin at its middle.
  const ext = (world.massifs || []).flatMap((m) => m.blob);
  const TW = Math.max(...ext.map((p) => p[0])), TH = Math.max(...ext.map((p) => p[1]));
  const CX = TW / 2, CY = TH / 2;
  const T = (p) => [p[0] - CX, p[2], CY - p[1]];            // world/region -> runtime
  addNode(rkey, {
    label: reg.name, kind: 'region', rt: true, params: {rt: '1'},
    bundle: `assets/scenes/${rkey}/`,
    origin: `${reg.file} (region '${reg.id}', tile ${TW}x${TH}, origin at ${CX},${CY})`,
  });

  const road = ((R.road || {}).points || []).map(T);
  for (const p of (R.road || {}).portals || []) {
    if (!p.target || !townMaps[p.target]) continue;
    const {map, key: tkey} = townMaps[p.target];
    const TT = (q) => [q[0], q[2], -q[1]];
    const town = map.displayName || p.target;
    const at = T(p.at);
    const ry = walkYNear(rkey, at[0], at[2], at[1], DEFAULTS.gateRadius);
    if (ry == null) W(`portal '${p.id}': no walk surface within r of the trigger (${at[0].toFixed(1)},${at[2].toFixed(1)}) in '${rkey}' — the gate may be unreachable on foot`);
    else { if (ry.off) W(`portal '${p.id}': trigger height taken from a walk surface ${ry.off.toFixed(2)}u away (the road ribbon stops short of the portal point)`); at[1] = ry.y; }

    // the town-side gate: the portal-class landmark the map's own exit sits on
    const exit = (map.exits || []).find((e) => (e.mode || 'land') === 'land');
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
    const [tfx, tfz] = norm2(tsp[0] - gAt[0], tsp[2] - gAt[2]);

    // the shot the town's gate stands in: arriving from the region opens the town on
    // that camera, and the way back out is only offered while it is up
    const tcine = townMaps[p.target].cine;
    const gShot = (tcine && tcine.lmOwner[gate.id]) || null;
    if (tcine && !gShot) W(`town '${p.target}': gate landmark '${gate.id}' is owned by no camera`);
    edges.push({
      id: eid(rkey, tkey, p.id), from: rkey, to: tkey, kind: 'portal', of: p.id,
      at: r3(at), r: DEFAULTS.gateRadius, vTol: DEFAULTS.vTol,
      spawn: r3(tsp), spawnYaw: Math.round(Math.atan2(-tfz, -tfx) * 1e4) / 1e4,
      cam: gShot ? {key: gShot} : null,
      label: `Enter ${town}`, key: DEFAULTS.key,
      reciprocal: eid(tkey, rkey, p.id),
      source: `${reg.file} road.portals '${p.id}' target '${p.target}' -> ${gate.id} (${via})` +
              (gShot ? `; arrives in shot '${gShot}'` : ''),
    });
    edges.push({
      id: eid(tkey, rkey, p.id), from: tkey, to: rkey, kind: 'portal', of: gate.id,
      at: r3(gAt), r: DEFAULTS.portalRadius, vTol: DEFAULTS.vTol,
      spawn: r3(rsp), spawnYaw: rYaw, cam: null, camFrom: gShot,
      label: `Leave ${town}`, key: DEFAULTS.key,
      reciprocal: eid(rkey, tkey, p.id),
      source: `${p.target}.map.json exit '${exit ? exit.id : gate.id}' at '${gate.id}' -> ${reg.file} portal '${p.id}'`,
    });
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
    '  walk surface by tools/slice_test.mjs.',
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
  '');

const json = JSON.stringify(doc, null, 1) + '\n';
if (ARGS.includes('--print')) { console.log(json); }
else if (ARGS.includes('--check')) {
  const cur = fs.existsSync(OUT) ? fs.readFileSync(OUT, 'utf8') : '';
  const strip = (s) => s.replace(/"generated": "[^"]*",?\n?/, '');
  if (strip(cur) !== strip(json)) { console.error('STALE: public/world/scenegraph.json differs from the maps. Re-run the generator.'); process.exit(1); }
  console.log('scenegraph.json is up to date with the maps.');
} else {
  fs.writeFileSync(OUT, json);
  console.log('wrote public/world/scenegraph.json');
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
