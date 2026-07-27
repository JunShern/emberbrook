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

/* ground materials — engine primitives, not measured props */
const GROUND = {
  'g-cobble-a': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble' },
  'g-cobble-b': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble' },
  'g-dirt':     { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-dirt' },
  'g-grass':    { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-grass' },
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
  B['bakint-near'] = Object.assign({}, shellBase,
    { img: 'assets/iso/interior/' + room.sprites.near, keyOverride: 1e9 });
  for (const [name, p] of Object.entries(intr.props || {})) {
    if (p && p.sprite) B['i-' + name] = propDescriptor(p, 'assets/iso/interior');
  }

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
