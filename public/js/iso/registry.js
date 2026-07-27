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
  // ---- ground materials (flat painted textures, diamond-cut at load) ----
  // tex: shipped pre-squashed (2:1) seamless texture in assets/iso/blocks/.
  // The engine bakes the whole scene floor once: per 1x1 cell it clips a
  // 64x32 diamond and pattern-fills from the texture at the cell's screen
  // position plus a small deterministic jitter (breaks repetition banding).
  'g-cobble-a': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble' },
  'g-cobble-b': { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-cobble' },
  'g-dirt':     { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-dirt' },
  'g-grass':    { foot: [2, 2], kind: 'ground', walk: true, tex: 'tex-grass' },
  'f-plank':    { foot: [2, 2], s: 0.492, kind: 'ground', walk: true },

  // ---- outdoor props (slab-less art; ax/ay = base-diamond center in raw
  //      image px, anchored at the footprint center on the flat ground) ----
  'well':           { foot: [3, 3], s: 0.913, kind: 'free', walk: false, ax: 92.5, ay: 171.8 },
  'lamppost':       { foot: [3, 3], s: 0.863, kind: 'free', walk: false, solid: [[1, 1]], ax: 33.7, ay: 215.8 },
  'bench':          { foot: [2, 2], s: 0.614, kind: 'free', walk: false, ax: 106.3, ay: 158.2 },
  'barrel':         { foot: [2, 2], s: 0.760, kind: 'free', walk: false, ax: 44.0, ay: 102.5 },
  'crates':         { foot: [2, 2], s: 0.722, kind: 'free', walk: false, ax: 57.2, ay: 157.5 },
  'haybale':        { foot: [2, 2], s: 0.665, kind: 'free', walk: false, ax: 103.7, ay: 131.0 },
  'board-pumpkins': { foot: [2, 2], s: 0.645, kind: 'free', walk: false, ax: 45.2, ay: 148.8 },
  'firewood-a':     { foot: [2, 2], s: 0.648, kind: 'free', walk: false, ax: 90.0, ay: 119.2 },
  'firewood-b':     { foot: [2, 2], s: 0.648, kind: 'free', walk: false, ax: 77.0, ay: 119.2 },
  'plinth':         { foot: [3, 3], s: 0.794, kind: 'free', walk: false, ax: 85.7, ay: 167.0 },
  'bunting':        { foot: [6, 3], s: 1.020, kind: 'free', walk: true,
                      solid: [[0, 1], [5, 1]], ax: 113.5, ay: 203.0,
                      shadowCells: [[[0, 1], [0, 1]], [[5, 1], [5, 1]]] },
  'stall-green':    { foot: [3, 3], s: 0.714, kind: 'free', walk: false, ax: 145.8, ay: 242.0 },
  'stall-stripe':   { foot: [3, 3], s: 0.714, kind: 'free', walk: false, ax: 147.0, ay: 241.0 },
  'tree-a':         { foot: [4, 4], s: 0.450, kind: 'free', walk: true,
                      solid: [[1, 1], [2, 1], [1, 2], [2, 2]], ax: 378.3, ay: 725.2 },
  'tree-round':     { foot: [3, 3], s: 0.669, kind: 'free', walk: true,
                      solid: [[1, 1]], ax: 127.7, ay: 266.0 },
  'pumpkin-cart':   { foot: [2, 2], s: 0.547, kind: 'free', walk: false, ax: 199.5, ay: 167.2 },
  'apple-crate':    { foot: [2, 2], s: 0.500, kind: 'free', walk: false, ax: 150.0, ay: 129.8 },
  'planter':        { foot: [2, 2], s: 0.495, kind: 'free', walk: false, ax: 137.5, ay: 153.8 },
  'firepit':        { foot: [3, 3], s: 0.824, kind: 'free', walk: false, ax: 98.2, ay: 147.5 },

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
