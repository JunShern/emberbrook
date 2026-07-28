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
    parcelsNoExits, flatStairs, unknownDistricts, badExitAnchors, badStartRevealed,
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
      console.log(`     - ${x.nearId} --${x.type}--> ${x.farId} ${fpos} -> parcel ${nb}${warn}`);
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
  line('INFO  landmarks in 2+ parcels', v.multiParcelLandmarks, m => `${m.lm.id} -> ${m.parcels.map(p => p.id).join(', ')}`);
  line('ERROR edges with unknown endpoint id', v.danglingEdges, e => `${e.from} -> ${e.to}`);
  line('ERROR edges with neither endpoint in any parcel', v.floatingEdges, e => `${e.from} -> ${e.to}`);
  line('ERROR parcels with zero derived exits', v.parcelsNoExits, p => `${p.id} (${p.name})`);
  line('WARN  stairs edges with zero z-span', v.flatStairs, e => `${e.from} -> ${e.to}`);
  line('WARN  landmarks with unknown district', v.unknownDistricts, l => `${l.id} -> ${l.district}`);
  line('ERROR town exits anchored at unknown landmark', v.badExitAnchors, x => `${x.id} at ${x.at}`);
  line('WARN  mapDiscovery.startRevealed unknown parcel', v.badStartRevealed, id => id);

  // stairs tread check mirrored from the massing script's hard rule
  console.log('\n=== stairs tread budget (rise/tread <= 0.5 hard rule) ===');
  const lmById = new Map(map.landmarks.map(l => [l.id, l]));
  for (const e of map.edges.filter(e => e.type === 'stairs')) {
    const a = lmById.get(e.from), b = lmById.get(e.to);
    if (!a || !b) continue;
    const rise = Math.abs(a.pos[2] - b.pos[2]);
    const treads = Math.max(1, Math.ceil(rise / 0.4));
    const per = rise / treads;
    console.log(`  ${e.from} -> ${e.to}: rise=${rise.toFixed(2)} treads=${treads} rise/tread=${per.toFixed(3)} ${per <= 0.5 ? 'OK' : 'FAIL'}`);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
