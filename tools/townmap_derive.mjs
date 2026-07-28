#!/usr/bin/env node
/*
 * townmap_derive.mjs — reference implementation of the town-graph derivation
 * logic used by public/townmap/viewer.html. Town-agnostic.
 *
 *   node tools/townmap_derive.mjs [townName=dellhollow]
 *
 * Prints, per parcel: contained landmarks, internal edges, derived exits
 * (edges with exactly one endpoint inside) + the neighbour parcel that holds
 * the far endpoint, and town-level exits anchored in the parcel.
 * Then prints the validation report.
 *
 * This exists so the viewer's derivation can be unit-checked headlessly.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TREAD_RISE_AIM = 0.4;   // implied tread count = ceil(rise / this)
const MAX_TREAD_RISE = 0.5;   // hard rule that the implied count must satisfy
const MIN_GUTTER = 2.0;       // minimum deliberate gap between parcel bounds

const town = process.argv[2] || 'dellhollow';
const mapPath = path.join(__dirname, '..', 'public', 'townmap', `${town}.map.json`);

// ---------------------------------------------------------------- derivation
// Kept deliberately identical (same semantics, same names) to viewer.html so
// the two can't drift silently.

export function inBounds(pos, bounds) {
  const [x, y, z] = pos;
  const { min, max } = bounds;
  return x >= min[0] && x <= max[0] &&
         y >= min[1] && y <= max[1] &&
         z >= min[2] && z <= max[2];
}

export function parcelsContaining(landmark, parcels) {
  return parcels.filter(p => inBounds(landmark.pos, p.bounds));
}

// Scenes are non-overlapping vignettes; parcels should be separated by a
// deliberate gutter (implied off-screen travel) rather than sitting flush.
export function boxSeparation(a, b) {
  return [0, 1, 2].map(i => Math.max(0, a.min[i] - b.max[i], b.min[i] - a.max[i]));
}
/** Signed overlap extent per axis; negative means a gap on that axis. */
export function boxOverlapExtents(a, b) {
  return [0, 1, 2].map(i => Math.min(a.max[i], b.max[i]) - Math.max(a.min[i], b.min[i]));
}
/** Strict overlap: shared volume. Merely touching is a zero-gutter case. */
export function boxesOverlap(a, b) { return boxOverlapExtents(a, b).every(e => e > 0); }
export function boxGutter(a, b) { return Math.max(...boxSeparation(a, b)); }
export function overlapBox(a, b) {
  const min = [0, 1, 2].map(i => Math.max(a.min[i], b.min[i]));
  const max = [0, 1, 2].map(i => Math.min(a.max[i], b.max[i]));
  return { min, max, size: [0, 1, 2].map(i => max[i] - min[i]) };
}

const COMPASS = ['east', 'north-east', 'north', 'north-west',
                 'west', 'south-west', 'south', 'south-east'];
/** Compass-ish bearing from one point to another (+x = east, +y = north). */
export function compassDir(from, to) {
  const dx = to[0] - from[0], dy = to[1] - from[1], dz = to[2] - from[2];
  const horiz = Math.hypot(dx, dy);
  let dir;
  if (horiz < 1e-6) dir = 'in place';
  else {
    let ang = Math.atan2(dy, dx) * 180 / Math.PI;
    if (ang < 0) ang += 360;
    dir = COMPASS[Math.round(ang / 45) % 8];
  }
  if (Math.abs(dz) > 0.5) dir += (dz > 0 ? ' and up' : ' and down');
  return dir;
}
export function boundsCentre(b) { return [0, 1, 2].map(i => (b.min[i] + b.max[i]) / 2); }

export function deriveContracts(map) {
  const lmById = new Map(map.landmarks.map(l => [l.id, l]));
  const parcels = map.parcels || [];
  const edges = map.edges || [];

  // parcelId -> Set(landmarkId)
  const contents = new Map(parcels.map(p => [p.id, []]));
  for (const lm of map.landmarks) {
    for (const p of parcelsContaining(lm, parcels)) contents.get(p.id).push(lm);
  }

  const contracts = parcels.map(p => {
    const inside = contents.get(p.id);
    const insideIds = new Set(inside.map(l => l.id));

    const internalEdges = [];
    const derivedExits = [];
    for (const e of edges) {
      const a = insideIds.has(e.from);
      const b = insideIds.has(e.to);
      if (a && b) { internalEdges.push(e); continue; }
      if (a !== b) {
        const nearId = a ? e.from : e.to;
        const farId = a ? e.to : e.from;
        const far = lmById.get(farId);
        // which neighbouring parcel holds the far endpoint?
        const neighbours = far
          ? parcelsContaining(far, parcels).filter(q => q.id !== p.id)
          : [];
        derivedExits.push({
          edge: e,
          type: e.type,
          nearId,
          near: lmById.get(nearId) || null,
          farId,
          far: far || null,
          neighbours,
          direction: far ? compassDir(boundsCentre(p.bounds), far.pos) : 'unknown',
          handoff: e.handoff === 'explicit',
          handoffFrom: e.handoffFrom || null,
          warning: !far
            ? `dangling edge endpoint "${farId}" (no such landmark)`
            : (neighbours.length === 0
                ? `UNASSIGNED: "${far.name}" is in no other parcel`
                : null),
        });
      }
    }

    const townExits = (map.exits || []).filter(x => insideIds.has(x.at));
    return { parcel: p, landmarks: inside, internalEdges, derivedExits, townExits };
  });

  return { contracts, contents, lmById };
}

export function validate(map) {
  const parcels = map.parcels || [];
  const edges = map.edges || [];
  const lmById = new Map(map.landmarks.map(l => [l.id, l]));
  const { contracts } = deriveContracts(map);

  const orphanLandmarks = [];     // error: in no parcel
  const multiParcelLandmarks = []; // info: in 2+ parcels
  for (const lm of map.landmarks) {
    const ps = parcelsContaining(lm, parcels);
    if (ps.length === 0) orphanLandmarks.push(lm);
    else if (ps.length > 1) multiParcelLandmarks.push({ lm, parcels: ps });
  }

  const danglingEdges = edges.filter(e => !lmById.has(e.from) || !lmById.has(e.to));

  const floatingEdges = edges.filter(e => {
    const a = lmById.get(e.from), b = lmById.get(e.to);
    if (!a || !b) return false; // already reported as dangling
    return parcelsContaining(a, parcels).length === 0 &&
           parcelsContaining(b, parcels).length === 0;
  });

  const parcelsNoExits = contracts.filter(c => c.derivedExits.length === 0).map(c => c.parcel);

  const flatStairs = edges.filter(e => {
    if (e.type !== 'stairs') return false;
    const a = lmById.get(e.from), b = lmById.get(e.to);
    if (!a || !b) return false;
    return Math.abs(a.pos[2] - b.pos[2]) === 0;
  });

  // Pure data climbability check, mirrored in tools/townmap_massing.py and
  // viewer.html: run < rise means steeper than 45 deg, no staircase fits.
  const steepStairs = [];
  for (const e of edges) {
    if (e.type !== 'stairs') continue;
    const a = lmById.get(e.from), b = lmById.get(e.to);
    if (!a || !b) continue;
    const rise = Math.abs(a.pos[2] - b.pos[2]);
    const run = Math.hypot(b.pos[0] - a.pos[0], b.pos[1] - a.pos[1]);
    if (run < rise) {
      steepStairs.push({ edge: e, rise, run,
        treads: Math.max(1, Math.ceil(rise / TREAD_RISE_AIM)),
        slope: run > 1e-9 ? Math.atan2(rise, run) * 180 / Math.PI : 90 });
    }
  }

  // parcel box hygiene: vignettes should not overlap, and should have gutters
  const parcelOverlaps = [], tightGutters = [];
  for (let i = 0; i < parcels.length; i++) {
    for (let j = i + 1; j < parcels.length; j++) {
      const a = parcels[i], b = parcels[j];
      if (boxesOverlap(a.bounds, b.bounds)) {
        parcelOverlaps.push({ a, b, box: overlapBox(a.bounds, b.bounds) });
      } else {
        const g = boxGutter(a.bounds, b.bounds);
        if (g < MIN_GUTTER) tightGutters.push({ a, b, gutter: g });
      }
    }
  }

  // Optional edge fields: handoff === "explicit" marks a MATTE SIGHTLINE.
  // The downstream scene depicts the upstream element as distant non-playable
  // imagery (matte/billboard before the backdrop render, never in scene.glb,
  // no collision or occlusion). Not shared geometry, not a build dependency.
  const handoffEdges = [];
  for (const e of edges) {
    if (e.handoff !== 'explicit') continue;
    const a = lmById.get(e.from), b = lmById.get(e.to);
    const involved = [...new Set([
      ...(a ? parcelsContaining(a, parcels) : []),
      ...(b ? parcelsContaining(b, parcels) : []),
    ])];
    const upstream = e.handoffFrom ? (parcels.find(p => p.id === e.handoffFrom) || null) : null;
    handoffEdges.push({
      edge: e, involved, upstream,
      pair: involved.map(p => p.id).join(' <-> ') || '(no parcels)',
      depicted: upstream ? upstream.id : 'either side (no handoffFrom given)',
      badUpstream: !!(e.handoffFrom && !upstream),
    });
  }

  // extra: districts referenced by landmarks that don't exist
  const districtIds = new Set((map.districts || []).map(d => d.id));
  const unknownDistricts = map.landmarks.filter(l => l.district && !districtIds.has(l.district));

  // extra: town exits anchored at a nonexistent landmark
  const badExitAnchors = (map.exits || []).filter(x => !lmById.has(x.at));

  // extra: mapDiscovery.startRevealed referencing unknown parcels
  const parcelIds = new Set(parcels.map(p => p.id));
  const badStartRevealed = ((map.mapDiscovery || {}).startRevealed || [])
    .filter(id => !parcelIds.has(id));

  return {
    orphanLandmarks, multiParcelLandmarks, danglingEdges, floatingEdges,
    parcelsNoExits, flatStairs, steepStairs, unknownDistricts,
    badExitAnchors, badStartRevealed,
    parcelOverlaps, tightGutters, handoffEdges,
  };
}

// ------------------------------------------------------------------- reporting
function main() {
  const map = JSON.parse(fs.readFileSync(mapPath, 'utf8'));
  const { contracts } = deriveContracts(map);

  console.log(`=== ${map.displayName || map.town} — parcel contracts (${contracts.length} parcels) ===\n`);
  for (const c of contracts) {
    const p = c.parcel;
    console.log(`## ${p.id}  "${p.name}"  scene=${p.sceneKey}`);
    console.log(`   bounds min=[${p.bounds.min}] max=[${p.bounds.max}]`);
    console.log(`   landmarks (${c.landmarks.length}):`);
    for (const l of c.landmarks) {
      console.log(`     - ${l.id.padEnd(18)} ${String(l.kind).padEnd(16)} pos=[${l.pos}] mapVisible=${l.mapVisible}`);
    }
    console.log(`   internal edges (${c.internalEdges.length}):`);
    for (const e of c.internalEdges) console.log(`     - ${e.from} --${e.type}--> ${e.to}`);
    console.log(`   derived exits (${c.derivedExits.length}):`);
    for (const x of c.derivedExits) {
      const nb = x.neighbours.map(n => n.id).join(',') || '(none)';
      const warn = x.warning ? `   <<< ${x.warning}` : '';
      const fpos = x.far ? `[${x.far.pos}]` : '[?]';
      const ho = x.handoff ? `  [MATTE SIGHTLINE${x.handoffFrom ? `, depicted parcel ${x.handoffFrom}` : ''}]` : '';
      console.log(`     - toward ${x.direction.padEnd(22)} ${x.nearId} --${x.type}--> ${x.farId} ${fpos} -> parcel ${nb}${ho}${warn}`);
    }
    if (c.townExits.length) {
      console.log(`   town exits (${c.townExits.length}):`);
      for (const x of c.townExits) console.log(`     - ${x.id} at ${x.at} mode=${x.mode} to=${x.to}`);
    }
    console.log('');
  }

  const v = validate(map);
  console.log('=== validation ===');
  const line = (label, arr, fmt) => {
    console.log(`${label}: ${arr.length}`);
    for (const it of arr) console.log(`   - ${fmt(it)}`);
  };
  line('ERROR landmarks in no parcel', v.orphanLandmarks, l => `${l.id} pos=[${l.pos}] (district ${l.district})`);
  line('WARN  parcel bounds overlap', v.parcelOverlaps,
    o => `${o.a.id} n ${o.b.id}: overlap box [${o.box.min}]..[${o.box.max}] size [${o.box.size}]`);
  line(`WARN  parcels with gutter < ${MIN_GUTTER}u`, v.tightGutters,
    g => `${g.a.id} / ${g.b.id}: gap ${g.gutter.toFixed(2)}u`);
  line('WARN  landmarks in 2+ parcels (symptom of overlap)', v.multiParcelLandmarks, m => `${m.lm.id} -> ${m.parcels.map(p => p.id).join(', ')}`);
  line('INFO  sightline pairs (matte depiction, no shared geometry)', v.handoffEdges,
    h => `${h.edge.from} -> ${h.edge.to} [${h.pair}]: depicted element's parcel = ${h.depicted}` +
         (h.badUpstream ? ` <<< handoffFrom "${h.edge.handoffFrom}" is not a parcel id` : ''));
  line('ERROR edges with unknown endpoint id', v.danglingEdges, e => `${e.from} -> ${e.to}`);
  line('ERROR edges with neither endpoint in any parcel', v.floatingEdges, e => `${e.from} -> ${e.to}`);
  line('ERROR parcels with zero derived exits', v.parcelsNoExits, p => `${p.id} (${p.name})`);
  line('WARN  stairs edges with zero z-span', v.flatStairs, e => `${e.from} -> ${e.to}`);
  line('WARN  stairs steeper than 45 deg (run < rise)', v.steepStairs,
    s => `${s.edge.from} -> ${s.edge.to}: rise=${s.rise.toFixed(2)} run=${s.run.toFixed(2)} ` +
         `slope=${s.slope.toFixed(1)}deg treads=${s.treads}`);
  line('WARN  landmarks with unknown district', v.unknownDistricts, l => `${l.id} -> ${l.district}`);
  line('ERROR town exits anchored at unknown landmark', v.badExitAnchors, x => `${x.id} at ${x.at}`);
  line('WARN  mapDiscovery.startRevealed unknown parcel', v.badStartRevealed, id => id);

  // Stair budget, mirrored from tools/townmap_massing.py's data check.
  console.log(`\n=== stairs data check (tread <= ${MAX_TREAD_RISE}; suspect when run < rise) ===`);
  console.log('  edge'.padEnd(50) + 'rise    run  treads     per   slope  verdict');
  const lmById = new Map(map.landmarks.map(l => [l.id, l]));
  for (const e of map.edges.filter(e => e.type === 'stairs')) {
    const a = lmById.get(e.from), b = lmById.get(e.to);
    if (!a || !b) continue;
    const rise = Math.abs(a.pos[2] - b.pos[2]);
    const run = Math.hypot(b.pos[0] - a.pos[0], b.pos[1] - a.pos[1]);
    const treads = Math.max(1, Math.ceil(rise / TREAD_RISE_AIM));
    const per = rise / treads;
    const slope = run > 1e-9 ? Math.atan2(rise, run) * 180 / Math.PI : 90;
    const verdict = rise === 0 ? 'SUSPECT: zero rise'
                  : run < rise ? 'SUSPECT: run < rise (steeper than 45 deg)'
                  : (per <= MAX_TREAD_RISE ? 'OK' : 'FAIL: tread rise');
    console.log('  ' + `${e.from} -> ${e.to}`.padEnd(48) +
      `${rise.toFixed(2).padStart(5)} ${run.toFixed(2).padStart(6)} ` +
      `${String(treads).padStart(6)} ${per.toFixed(3).padStart(7)} ` +
      `${slope.toFixed(1).padStart(6)}d  ${verdict}`);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
