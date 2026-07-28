'use strict';
/* ============================================================
   ISO-PROTO block registry — METRIC-DRIVEN.

   Every painted asset's render entry is built at load time straight from
   the three measured metrics JSONs the proving campaign produced:

     assets/iso/blocks9/blocks9-metrics.json   outdoor props (native 1x)
     assets/iso/festival/festival-metrics.json outdoor props (native 1x, opt.)
     assets/iso/bldg/bldg-metrics.json         building facades (cellScale S=2)
     assets/iso/interior/interior-metrics.json bakery shell + props (S=1.5)

   ONE render convention for every painted piece (the "free"/anchor recipe
   proven in tools/bldg_occlusion.py + tools/interior_prove.py):
       scale  s   = <normalization> * renderFitScale
       anchor a   = metrics.anchorSprite  (the mark centre, in sprite px)
       draw       = place anchor*s at the footprint centre on the diamond
       sortKey    = i + j + (footW + footH)/2   (engine formula, unchanged)

   Normalization per source:
     props      s = TW / cellPx                 (1 painted cell -> 1 engine cell)
     buildings  s = cellScale.renderScale = S*TW/cellPx  (1 painted cell -> SxS)
     interior   s = S*TW/cellPx  for the shell layers; props stay native 1x
   base-containment remedies ride along the metric: AUTOFIT props carry
   renderFitScale (folded into s), REDECLARE props already ship a corrected
   `declared` + `anchorSprite`, so nothing here re-tunes them.

   Collision / triggers are metric-driven too: a prop blocks its declared
   footprint; a building blocks cellScale.engineSolid and exposes
   cellScale.engineDoorstep as the scene-transition trigger row; the interior
   shell is walkable (bounded by the scene rect) with its near band keyed
   ABOVE the character and its back layer keyed BELOW everything.

   The ONLY hand numbers left are engine ground primitives (f-plank, tex-*),
   which are not painted props but the floor material itself.
   ============================================================ */

(function () {
const TW = 64;
const INTERIOR_S = 1.5;              // proven interior cellScale (interior-prove.json)

/* ground materials — engine primitives, not measured props.

   [groundv2] SAMPLING MODES (see engine bakeGround):
     organic    (default) — per-cell jittered + feathered patches; correct for
                grass/dirt/leaf/water/rock where repetition should never band.
     structured — WORLD-ANCHORED CONTINUOUS sampling: one un-jittered pattern
                space across the whole scene, projected through the iso basis so
                the flat top-down pattern's axes run along the grid diagonals with
                2:1 foreshortening (planks/cobble courses follow the iso axes).
                `patternScale` = world CELLS spanned by one full texture tile
                (smaller -> pattern renders smaller / more honest world size).
     platform   — a structured deck that is BUILT UP into a pier: raised plank
                top, auto edge fascia + stilts where it borders water/non-deck,
                water rendered visibly UNDER the edge. HARD boundary (no blend). */
const GROUND = {
  'g-cobble-a': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble', sampling: 'structured', patternScale: 11.5 },
  'g-cobble-b': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble', sampling: 'structured', patternScale: 11.5 },
  // [ground-r3] DEMO-ONLY corrected-scale cobble materials for the village picker.
  // patternScale tuned per candidate so every re-rendered cobble reads at an honest
  // ~0.2 m sett (round-2 showed chainmail-tiny at ps 5). Not used by any live scene
  // — the live g-cobble-a/b scale is finalised when the director picks a cobble.
  'g-cobble-dA': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble', sampling: 'structured', patternScale: 8.0 },
  'g-cobble-dB': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble', sampling: 'structured', patternScale: 11.5 },
  'g-cobble-dC': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble', sampling: 'structured', patternScale: 10.5 },
  'g-dirt':     { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-dirt' },
  'g-grass':    { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-grass' },
  // Ch1 forest biome ground materials (new textures baked through the same path)
  'g-forestfloor': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-forestfloor' },
  'g-forestpath':  { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-forestpath' },
  // Ch2 Dellhollow ground materials (requested by the Ch2 scene builder)
  'g-water': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-water' },
  'g-deck':  { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-deck', sampling: 'structured', patternScale: 3.8, platform: true },
  'g-cliff': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cliff' },
  // [ground-r3] LEDGE (masonry) platform class — CONSTRUCTED cut-stone quay / lock
  // margin. Unlike g-cliff (natural rock, soft blend) and g-deck (wood pier, water
  // under it), a ledge is a SOLID dressed-stone wall: HARD boundary to water, an
  // auto stone FACE piece drops from its south/east water-facing edges to the
  // waterline, NO stilts, water does NOT continue underneath.
  'g-ledge': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-ledge', sampling: 'structured', patternScale: 4.6, ledge: true },
  // structured plank material for iso-aware interiors. tex-plank = candidate C
  // (director's live default); interiors now use this in place of legacy f-plank.
  'g-plank':    { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-plank', sampling: 'structured', patternScale: 4.8 },
  // alternate BRIGHT interior board set (candidate A) — registry-only, available for
  // future bright rooms; no scene uses it yet.
  'g-plank-bright': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-plank-bright', sampling: 'structured', patternScale: 4.8 },
  'f-plank':    { foot: [2, 2], kind: 'ground', walk: true, s: 0.492,
                  img: 'assets/iso/blocks/f-plank.png' },
};

async function fetchJSON(p) {
  const r = await fetch(p);
  if (!r.ok) throw new Error('metrics fetch failed: ' + p);
  return r.json();
}

/* mark-boundary corners (sprite px) so the engine can strip the keyed-mark
   halo ring along the footprint diamond edge at load */
function fitCorners(m) {
  const f = m.fitSprite;
  return f ? [f.T, f.R, f.B, f.L] : null;
}

/* native-1x painted prop (blocks9 / festival / interior props).
   Height reconciliation: a SCALE-NOTE prop (painted 15-30% off its target
   height, footprint has slack) carries heightFit.heightFitScale — the uniform
   factor that pulls it to the canonical height WITHOUT pushing its base past
   AUTOFIT tolerance (height and footprint scale together on a billboard, so
   this is only emitted when the base can absorb it; see tools/height_gate.py).
   REROLL props carry no heightFitScale and render as-painted until regenerated. */
function propDescriptor(m, dir) {
  const hFit = (m.heightFit && m.heightFit.heightFitScale) || 1;
  return {
    img: dir + '/' + m.sprite,
    foot: m.declared.slice(),
    s: TW / m.cellPx * (m.renderFitScale || 1) * hFit,
    ax: m.anchorSprite[0], ay: m.anchorSprite[1],
    kind: 'free', walk: false, fit: fitCorners(m),
  };
}

/* building facade at its measured cellScale (S engine cells per painted cell) */
function buildingDescriptor(m, dir) {
  const cs = m.cellScale;
  return {
    img: dir + '/' + m.sprite,
    foot: cs.engineFoot.slice(),
    s: cs.renderScale,
    ax: m.anchorSprite[0], ay: m.anchorSprite[1],
    kind: 'building', walk: false, fit: fitCorners(m),
    solid: (cs.engineSolid || []).map(c => c.slice()),
    door: (cs.engineDoorCells || []).map(c => c.slice()),
    doorstep: (cs.engineDoorstep || []).map(c => c.slice()),
  };
}

/* build the whole registry from metrics; returns { blocks, interior } */
async function buildIsoRegistry() {
  const B = {};
  for (const [k, v] of Object.entries(GROUND)) B[k] = v;

  // ---- outdoor props: blocks9 (required) + festival (optional) ----
  const b9 = await fetchJSON('assets/iso/blocks9/blocks9-metrics.json');
  for (const [name, m] of Object.entries(b9)) {
    if (m && m.sprite) B[name] = propDescriptor(m, 'assets/iso/blocks9');
  }
  try {
    const fes = await fetchJSON('assets/iso/festival/festival-metrics.json');
    for (const [name, m] of Object.entries(fes)) {
      if (m && m.sprite) B['f-' + name] = propDescriptor(m, 'assets/iso/festival');
    }
  } catch (e) { /* festival sheet not generated yet — square degrades gracefully */ }

  // ---- building facades (cellScale S=2) ----
  const bldg = await fetchJSON('assets/iso/bldg/bldg-metrics.json');
  for (const name of ['bakery', 'cottage', 'guildhall']) {
    const m = bldg[name];
    if (m && m.cellScale) B[name] = buildingDescriptor(m, 'assets/iso/bldg');
  }

  // ---- bakery interior: shell layers (S=1.5) + native-1x props ----
  const intr = await fetchJSON('assets/iso/interior/interior-metrics.json');
  const room = intr.room;
  const [fw, fh] = room.declared;
  const S = INTERIOR_S;
  const W = Math.round(fw * S), H = Math.round(fh * S);
  const rs = S * TW / room.cellPx;
  const shellBase = {
    foot: [W, H], s: rs, ax: room.anchorSprite[0], ay: room.anchorSprite[1],
    kind: 'free', walk: true, noShadow: true,
  };
  // back layer keyed below everything; near band keyed above the character
  B['bakint-back'] = Object.assign({}, shellBase,
    { img: 'assets/iso/interior/' + room.sprites.back, keyOverride: -1e9 });
  // near band always sorts above the character; it participates in occluder
  // fade (fadeTarget) so she no longer "vanishes at the door" behind it
  B['bakint-near'] = Object.assign({}, shellBase,
    { img: 'assets/iso/interior/' + room.sprites.near, keyOverride: 1e9, fadeTarget: 0.5 });
  for (const [name, p] of Object.entries(intr.props || {})) {
    if (p && p.sprite) B['i-' + name] = propDescriptor(p, 'assets/iso/interior');
  }

  // ---- Ch1 forest biome props (forest-metrics.json) ----
  // Names already carry the f- prefix, so load them verbatim. The tex-*
  // ground-texture entries are floor materials (handled by GROUND), not props.
  try {
    const forest = await fetchJSON('assets/iso/forest/forest-metrics.json');
    for (const [name, m] of Object.entries(forest)) {
      if (!m || !m.sprite || m.kind === 'ground-texture') continue;
      const d = propDescriptor(m, 'assets/iso/forest');
      // The Old Gate is an arch: its passage is walkable, blocked only by the
      // two pillars at the footprint ends (declared 4x2 -> pillars at i=0,3).
      if (name === 'f-gate') { d.walk = true; d.solid = [[0, 0], [0, 1], [3, 0], [3, 1]]; }
      // Fireflies are a diffuse decorative glow, not a physical object: no
      // collision (walkable with an empty solid set) and no contact shadow.
      if (name === 'f-fireflies') { d.walk = true; d.solid = []; d.noShadow = true; }
      B[name] = d;
    }
  } catch (e) { /* forest sheet absent -> forest/gate scenes degrade */ }

  // ---- Ch1 village catalog (village-metrics.json): dressing + festival-fixslice
  // props, interior i-* props, heartlight, and the thatch/townhouse/lake-cottage
  // facades. int-room-lake is the lake interior shell, handled below. ----
  let lakeRoom = null;
  try {
    const vil = await fetchJSON('assets/iso/village/village-metrics.json');
    for (const [name, m] of Object.entries(vil)) {
      if (!m || typeof m !== 'object') continue;
      if (name === 'int-room-lake') { lakeRoom = m; continue; }
      const cs = m.cellScale;
      if (cs && cs.engineFoot) { B[name] = buildingDescriptor(m, 'assets/iso/village'); continue; }
      if (m.sprite) B[name] = propDescriptor(m, 'assets/iso/village');
    }
  } catch (e) { /* village sheet absent */ }

  // ---- lake cottage interior shell (same convention as the bakery shell:
  // back layer keyed below everything, near band above the character with a
  // fade target). Built metric-driven from int-room-lake at INTERIOR_S. ----
  if (lakeRoom && lakeRoom.sprites) {
    const [lfw, lfh] = lakeRoom.declared;
    const lW = Math.round(lfw * S), lH = Math.round(lfh * S);
    const lrs = S * TW / lakeRoom.cellPx;
    const lakeBase = {
      foot: [lW, lH], s: lrs, ax: lakeRoom.anchorSprite[0], ay: lakeRoom.anchorSprite[1],
      kind: 'free', walk: true, noShadow: true,
    };
    B['lakint-back'] = Object.assign({}, lakeBase,
      { img: 'assets/iso/village/' + lakeRoom.sprites.back, keyOverride: -1e9 });
    B['lakint-near'] = Object.assign({}, lakeBase,
      { img: 'assets/iso/village/' + lakeRoom.sprites.near, keyOverride: 1e9, fadeTarget: 0.5 });
  }

  // ---- Ch2 Dellhollow catalog (folded in per the Ch2 scene builder's
  // ch2-registry-needs report). Props/buildings ride the exact blocks9/bldg
  // paths; lockfive-chamber is an interior shell like the bakery/lake rooms.
  // Names are globally unique, so they register verbatim (no prefix). ----
  try {
    const dh = await fetchJSON('assets/iso/dellhollow/dellhollow-metrics.json');
    const DH_BUILDINGS = ['stilthouse-a', 'stilthouse-b', 'keeperscottage'];
    const DH_SKIP = new Set([...DH_BUILDINGS, 'lockfive-chamber',
      'tex-water', 'tex-deck', 'tex-cliff', '_bldgCellScaleFormula', '_summary']);
    for (const [name, m] of Object.entries(dh)) {
      if (DH_SKIP.has(name) || !m || typeof m !== 'object' || !m.sprite) continue;
      B[name] = propDescriptor(m, 'assets/iso/dellhollow');
    }
    for (const name of DH_BUILDINGS) {
      const m = dh[name];
      if (m && m.cellScale && m.cellScale.engineFoot) B[name] = buildingDescriptor(m, 'assets/iso/dellhollow');
    }
    // lockfive interior shell: metric's sprites field wrongly points at bakint2-*,
    // so use the real lockfive-*.png files (per the Ch2 report). Geometry mirrors
    // the bakery/lake shell at INTERIOR_S.
    const lf = dh['lockfive-chamber'];
    if (lf && lf.declared) {
      const [ffw, ffh] = lf.declared;
      const lfBase = {
        foot: [Math.round(ffw * S), Math.round(ffh * S)], s: S * TW / lf.cellPx,
        ax: lf.anchorSprite[0], ay: lf.anchorSprite[1], kind: 'free', walk: true, noShadow: true,
      };
      B['lockfive-back'] = Object.assign({}, lfBase,
        { img: 'assets/iso/dellhollow/lockfive-back.png', keyOverride: -1e9 });
      B['lockfive-near'] = Object.assign({}, lfBase,
        { img: 'assets/iso/dellhollow/lockfive-near.png', keyOverride: 1e9, fadeTarget: 0.5 });
    }
  } catch (e) { /* Ch2 catalog absent -> Ch1 unaffected */ }

  // interior meta the scene rebuild consumes (engine grid, doorstep row)
  const dstep = room.door.interiorDoorstep;            // painted [i,j] inside the door
  const interior = {
    S, W, H,
    doorstepPainted: dstep,
    doorstepCells: [                                    // engine trigger cells
      [Math.round((dstep[0] + 0.5) * S), Math.floor((dstep[1]) * S)],
      [Math.round((dstep[0] + 0.5) * S), Math.round((dstep[1] + 0.5) * S)],
    ],
  };

  return { blocks: B, interior };
}

if (typeof window !== 'undefined') window.buildIsoRegistry = buildIsoRegistry;
})();
