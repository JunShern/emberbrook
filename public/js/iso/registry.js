'use strict';
/* ============================================================
   ISO-PROTO block registry.
   Each block: img (assets/iso/blocks/<name>.png), and:
     foot  [w,h]  footprint in 0.5m cells (visual + default collision)
     s            image scale at native zoom (TW=64 diamond)
     kind  'ground'   top-diamond anchor, unsorted floor pass
           'flat'     like ground but drawn after floor (decals, walkable)
           'slab'     prop on painted dirt slab; image bottom tip anchors to
                      the footprint's front corner
           'free'     slab-less prop; image bottom-center anchors to the
                      footprint's center
           'backdrop' anchored like slab/free but drawn before the sorted
                      pass (facades, interior walls) — always behind actors
     walk  true if the character may stand on the footprint
     solid optional subset of footprint cells that actually block
           (e.g. tree trunk under a wide canopy)
     dy    fine vertical nudge in image px (pre-scale)
     anchor optional 'free' override for backdrop pieces
   ============================================================ */

const IsoBlocks = {
  // ---- ground supertiles (2x2 cells each, inset-diamond rebuilt 264x132) ----
  'g-cobble-a': { foot: [2, 2], s: 0.492, kind: 'ground', walk: true },
  'g-cobble-b': { foot: [2, 2], s: 0.492, kind: 'ground', walk: true },
  'g-dirt':     { foot: [2, 2], s: 0.492, kind: 'ground', walk: true },
  'g-grass':    { foot: [2, 2], s: 0.492, kind: 'ground', walk: true },
  'f-plank':    { foot: [2, 2], s: 0.492, kind: 'ground', walk: true },

  // ---- outdoor props (painted dirt slab = footprint) ----
  'well':           { foot: [3, 3], s: 0.664, kind: 'slab', walk: false },
  'lamppost':       { foot: [3, 3], s: 0.660, kind: 'slab', walk: false, solid: [[1, 1]] },
  'bench':          { foot: [2, 2], s: 0.520, kind: 'slab', walk: false },
  'barrel':         { foot: [2, 2], s: 0.569, kind: 'slab', walk: false },
  'crates':         { foot: [2, 2], s: 0.489, kind: 'slab', walk: false },
  'haybale':        { foot: [2, 2], s: 0.533, kind: 'slab', walk: false },
  'board-pumpkins': { foot: [2, 2], s: 0.470, kind: 'slab', walk: false },
  'firewood-a':     { foot: [2, 2], s: 0.561, kind: 'slab', walk: false },
  'firewood-b':     { foot: [2, 2], s: 0.561, kind: 'slab', walk: false },
  'plinth':         { foot: [3, 3], s: 0.700, kind: 'slab', walk: false },
  'bunting':        { foot: [4, 4], s: 0.842, kind: 'slab', walk: true,
                      solid: [[0, 3], [3, 0]] },
  'stall-green':    { foot: [3, 3], s: 0.658, kind: 'slab', walk: false },
  'stall-stripe':   { foot: [3, 3], s: 0.660, kind: 'slab', walk: false },
  'tree-a':         { foot: [4, 4], s: 0.746, kind: 'slab', walk: true,
                      solid: [[1, 1], [2, 1], [1, 2], [2, 2]] },
  'tree-round':     { foot: [3, 3], s: 0.653, kind: 'slab', walk: true,
                      solid: [[1, 1]] },
  'pumpkin-cart':   { foot: [2, 2], s: 0.518, kind: 'slab', walk: false },
  'apple-crate':    { foot: [2, 2], s: 0.571, kind: 'slab', walk: false },
  'planter':        { foot: [2, 2], s: 0.564, kind: 'slab', walk: false },
  'firepit':        { foot: [3, 3], s: 0.688, kind: 'slab', walk: false },

  // ---- building facades (backdrop: always behind actors) ----
  'bakery':       { foot: [7, 7], s: 0.750, kind: 'backdrop', walk: false },
  'cottage-red':  { foot: [6, 6], s: 1.120, kind: 'backdrop', walk: false },
  'cottage-teal': { foot: [6, 6], s: 1.120, kind: 'backdrop', walk: false },

  // ---- bakery interior shell (one-piece room diorama, 2:1-rectified) ----
  // bakint-room: floor + back walls, backdrop (always behind actors).
  // bakint-stub: the front-right door wall sliced from the same image at the
  // wall plane, drawn as a sorted prop with key 24 (> any reachable char key)
  // so the character is correctly occluded when approaching the exit door.
  // Both share size/anchor/dy so they register pixel-perfectly.
  // Collision comes from the scene rect (12x12 walkable), so walk:true here.
  'bakint-room': { foot: [12, 12], s: 1.25, kind: 'backdrop', walk: true, dy: 41 },
  'bakint-stub': { foot: [0, 0],   s: 1.25, kind: 'slab',     walk: true, dy: 41 },

  // ---- bakery interior props ----
  'counter':     { foot: [3, 2], s: 0.58, kind: 'slab', walk: false },
  'oven':        { foot: [4, 3], s: 0.87, kind: 'free', walk: false },
  'shelf':       { foot: [2, 1], s: 0.787, kind: 'free', walk: false },
  'preptable':   { foot: [2, 2], s: 0.55, kind: 'free', walk: false },
  'rug':         { foot: [3, 2], s: 1.00, kind: 'flat', walk: true },
  'stool':       { foot: [1, 1], s: 0.55, kind: 'free', walk: false },
  'breadcorner': { foot: [2, 2], s: 0.50, kind: 'free', walk: false },
  'kettletable': { foot: [1, 1], s: 0.50, kind: 'free', walk: false },
};

if (typeof window !== 'undefined') window.IsoBlocks = IsoBlocks;
