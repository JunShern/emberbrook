"""overworld3_lib.py — round 3 (style F2): the TERRAIN ZONE GRID, the zone-driven
terrain treatment, and four tree-construction approaches.

Round 3 is not a new art treatment.  The user picked round-2 style F (PBR miniature)
and asked for three things on top of it:

  PART 1  a ZONE GRID — the encounter geography, derived from the landform itself and
          exported as public/assets/scenes/ow-proto-f2/zones.json for the runtime.
  PART 2  zone-driven TERRAIN TREATMENT — smooth everywhere, deliberately broken in
          crag cells, with NO regular grid pattern anywhere (the complaint round 2
          earned: "regular sharp triangles").
  PART 3  a TREE LINE-UP — four different tree constructions side by side on one
          hillside, because every tree shipped so far has been rejected.

Everything else — the field, the blockout, the dusk rig, F's material pipeline — is
imported from rounds 1 and 2 and left alone.  Zone derivation is pure numpy and does
not need Blender, so this module imports bpy defensively and the grid can be tested
(and its coverage tuned) from a plain python3.
"""
import math
import os
import json

import numpy as np

try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
except ImportError:                     # no Blender: zone derivation still works
    bpy = bmesh = None
    Vector = Matrix = None

import overworld_lib as L

if bpy is not None:
    import overworld_build as B
    import overworld2_lib as O2

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TEXO = os.path.join(ROOT, "tools/textures/overworld")

# ---------------------------------------------------------------------------
# PART 1 — THE ZONE REGISTRY
# ---------------------------------------------------------------------------
# The types array IS the registry: grid cells store INDICES into it, so a later
# chapter appends "swamp"/"snow"/"ruin" to the end of this list and neither the
# json schema nor a single line of runtime code changes.  Never reorder it —
# an index is a permanent contract once a zones.json ships.
ZONES = ["meadow", "forest", "crag", "road", "water"]
# parallel to ZONES, so the debug overlay needs no code change either
ZONE_COLS = ["9ec45a", "2c6b33", "c47a3c", "d9c48f", "2f7f96"]
Z_MEADOW, Z_FOREST, Z_CRAG, Z_ROAD, Z_WATER = range(5)

# AUTHORED OVERRIDE STAMPS — fiction overruling landform, applied LAST.
#   {"type": <name>, "ellipse": (cx, cz, rx, rz, deg)}   runtime coords
#   {"type": <name>, "polygon": [(x, z), ...]}           runtime coords
# The two settlements are "road" because settled ground is safe ground: the
# encounter table must not roll a wolf inside the village green, and that is a
# fiction rule no slope threshold can express.
OVERRIDES = [
    dict(type="road", ellipse=(-30.0, -20.0, 8.0, 8.0, 0.0), why="village green: settled = safe"),
    dict(type="road", ellipse=(43.0, 29.0, 9.0, 9.0, 0.0), why="clifftown gate apron: settled = safe"),
    # the demonstration hillside is a planted stand, so the grid must AGREE with it
    dict(type="forest", polygon=[(-33.0, 2.0), (-9.0, 2.0), (-7.0, 19.0), (-31.0, 19.0)],
         why="the tree line-up hillside is a stand, not open meadow"),
]


# ------------------------------------------------------------------ noise field
def _hash01(i, j, seed=0):
    """Deterministic 0..1 hash of an integer lattice point.  Vectorised."""
    # the seed term is folded in python (an np.int64 multiply of two large
    # constants overflows and warns, and the warning is noise, not a bug)
    sd = np.int64((int(seed) * 1442695040888963407) & 0x7FFFFFFFFFFFFFFF)
    h = (np.asarray(i).astype(np.int64) * 374761393
         + np.asarray(j).astype(np.int64) * 668265263 + sd)
    h = h & np.int64(0x7FFFFFFFFFFFFFFF)
    h = (h ^ (h >> np.int64(13))) * np.int64(1274126177)
    h = h & np.int64(0x7FFFFFFFFFFFFFFF)
    h = h ^ (h >> np.int64(16))
    return (h & np.int64(0xFFFFFF)) / 16777216.0


def vnoise(x, y, freq, seed=0):
    """Smoothstep-interpolated value noise, 0..1.  Hash-based, so it is
    non-periodic over the whole tile — the point of not using sin() sums."""
    fx = np.asarray(x, float) * freq
    fy = np.asarray(y, float) * freq
    i0 = np.floor(fx).astype(np.int64)
    j0 = np.floor(fy).astype(np.int64)
    tx, ty = fx - i0, fy - j0
    sx = tx * tx * (3.0 - 2.0 * tx)
    sy = ty * ty * (3.0 - 2.0 * ty)
    n00 = _hash01(i0, j0, seed)
    n10 = _hash01(i0 + 1, j0, seed)
    n01 = _hash01(i0, j0 + 1, seed)
    n11 = _hash01(i0 + 1, j0 + 1, seed)
    return (n00 * (1 - sx) + n10 * sx) * (1 - sy) + (n01 * (1 - sx) + n11 * sx) * sy


def fbm(x, y, freq, seed=0, oct_=4, gain=0.52, lac=2.03):
    v = np.zeros(np.broadcast(np.asarray(x, float), np.asarray(y, float)).shape)
    amp, f, tot = 1.0, freq, 0.0
    for o in range(oct_):
        v = v + amp * vnoise(x, y, f, seed + o * 101)
        tot += amp
        amp *= gain
        f *= lac
    return v / tot


def ridged(x, y, freq, seed=0, oct_=3, gain=0.5, lac=2.11):
    """Ridged multifractal in 0..1.  The |2v-1| fold is what puts CREASES in the
    field — a plain fbm displacement makes lumps, and lumps are not crag."""
    v, amp, f, tot = None, 1.0, freq, 0.0
    for o in range(oct_):
        r = 1.0 - np.abs(2.0 * vnoise(x, y, f, seed + o * 77) - 1.0)
        r = r * r
        v = amp * r if v is None else v + amp * r
        tot += amp
        amp *= gain
        f *= lac
    return v / tot


def _box(A, n=1):
    """n box passes over a 2D array with edge clamping (cell-grid smoothing)."""
    for _ in range(n):
        P = np.pad(A, 1, mode="edge")
        A = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:] + P[1:-1, 1:-1]) / 5.0
    return A


def _grid_sample(A, bx, by):
    """Nearest lookup into one of Field's (NX, NY) analysis arrays."""
    fx = np.clip((np.asarray(bx, float) + L.TILE_X / 2) / L.STEP, 0, L.NX - 1.001)
    fy = np.clip((np.asarray(by, float) + L.TILE_Y / 2) / L.STEP, 0, L.NY - 1.001)
    return A[fx.astype(int), fy.astype(int)]


# ---------------------------------------------------------------------------
class ZoneGrid:
    """The zone grid: derived from the field, not hand-painted.

    Blender is +X east / +Y north / +Z up; the runtime is +X east / +Y up /
    +Z SOUTH (runtime z = -blender y).  The grid is stored in RUNTIME axes
    because SIM.zone(x, z) is what game code will call, and a debug format
    that needs a mental axis flip is a debug format that gets misread.
    """

    def __init__(self, F, fr=None, cell=1.25, overrides=OVERRIDES):
        self.F = F
        self.fr = fr
        self.cell = float(cell)
        self.cols = int(round(L.TILE_X / self.cell))
        self.rows = int(round(L.TILE_Y / self.cell))
        self.origin = (-L.TILE_X / 2.0, -L.TILE_Y / 2.0)
        self.overrides = list(overrides or [])

        cx = self.origin[0] + (np.arange(self.cols) + 0.5) * self.cell
        cz = self.origin[1] + (np.arange(self.rows) + 0.5) * self.cell
        CX, CZ = np.meshgrid(cx, cz, indexing="ij")
        self.CX, self.CZ = CX, CZ
        BX, BY = CX, -CZ                                # blender coords per cell
        self.BX, self.BY = BX, BY

        H = F.sample(BX, BY)
        SL = _grid_sample(F.slope, BX, BY)
        DR = _grid_sample(F.dr, BX, BY)
        WL = _grid_sample(F.wl, BX, BY)
        GG = _grid_sample(F.gorge, BX, BY)
        TR = _grid_sample(F.tr, BX, BY)
        ALT = H - WL
        DRD = F.road_dist(BX.ravel(), BY.ravel()).reshape(BX.shape)
        HW = F.water_halfwidth(TR)

        # ---- CRAG: steep rock at gorge rims and drop-offs -------------------
        # thresholds come off the field's OWN percentiles (round-2 finding 142),
        # never off a number that looked right in one render
        P = np.pad(H, 2, mode="edge")
        relief = np.zeros_like(H)
        for dx in range(5):
            for dy in range(5):
                w = P[dx:dx + H.shape[0], dy:dy + H.shape[1]]
                relief = np.maximum(relief, w) if (dx or dy) else w.copy()
        low = np.full_like(H, 1e9)
        for dx in range(5):
            for dy in range(5):
                low = np.minimum(low, P[dx:dx + H.shape[0], dy:dy + H.shape[1]])
        relief = relief - low                            # 5x5-cell local drop
        sl_c = float(np.percentile(SL, 84.0))
        rel_c = float(np.percentile(relief, 88.0))
        self.thresh = dict(slope_p84=round(sl_c, 3), relief_p88=round(rel_c, 2))
        crag = ((SL > sl_c) | ((GG > 0.25) & (SL > 0.85)) | (relief > rel_c)) & (ALT > 1.5)

        # ---- WATER: the analytic river + the round-2 mooring basin ----------
        water = (DR <= HW * 1.05)
        water |= (H <= WL + 0.05) & (DR < 16.0)          # backwaters, not dry hollows
        if fr is not None:
            water |= _pool_w_np(BX, BY, fr) > 0.5

        # ---- ROAD: the carriage road polyline, buffered ---------------------
        road = DRD <= 1.9                                # ribbon is 2.0u wide + verge

        # ---- FOREST: coherent noise patches — and the SAME mask plants the
        #      trees, so the map and the art can never disagree ---------------
        fn = fbm(BX, BY, 0.030, seed=7, oct_=4)
        self.forest_noise = fn
        fn_c = float(np.percentile(fn, 62.0))
        self.thresh["forest_p62"] = round(fn_c, 3)
        forest = (fn > fn_c) & (~crag) & (SL < 1.15) & (ALT > 1.0) & (ALT < 22.0)

        # ---- resolve, lowest priority first --------------------------------
        # road beats water on purpose: the bridge deck is road, and an encounter
        # on a bridge is a road encounter.
        Z = np.full((self.cols, self.rows), Z_MEADOW, dtype=np.int32)
        Z[forest] = Z_FOREST
        Z[crag] = Z_CRAG
        Z[water] = Z_WATER
        Z[road] = Z_ROAD

        # ---- authored override stamps, applied LAST -------------------------
        self.n_override = 0
        for st in self.overrides:
            m = self._stamp_mask(st)
            self.n_override += int(m.sum())
            Z[m] = ZONES.index(st["type"])
        self.idx = Z

        # ---- continuous weights the TERRAIN and the PLANTING read ----------
        # 1-2 cells of smoothing is what makes meadow flow into crag instead of
        # switching; the same array drives displacement amplitude and shading.
        self.crag_w = _box((Z == Z_CRAG).astype(float), 2)
        self.forest_w = _box((Z == Z_FOREST).astype(float), 1)
        # nothing may roughen the road, the water or a settlement, whatever the
        # slope says — so those cells veto crag displacement outright
        veto = ((Z == Z_ROAD) | (Z == Z_WATER)).astype(float)
        self.crag_w *= (1.0 - _box(veto, 2))
        self.crag_w = np.clip(self.crag_w, 0.0, 1.0)

    # ------------------------------------------------------------------ stamps
    def _stamp_mask(self, st):
        X, Z = self.CX, self.CZ
        if "ellipse" in st:
            cx, cz, rx, rz, deg = st["ellipse"]
            a = math.radians(deg)
            dx, dz = X - cx, Z - cz
            u = (dx * math.cos(a) + dz * math.sin(a)) / rx
            v = (-dx * math.sin(a) + dz * math.cos(a)) / rz
            return (u * u + v * v) <= 1.0
        pts = np.array(st["polygon"], float)
        inside = np.zeros(X.shape, bool)
        n = len(pts)
        for i in range(n):
            x0, z0 = pts[i]
            x1, z1 = pts[(i + 1) % n]
            hit = ((z0 > Z) != (z1 > Z)) & \
                  (X < (x1 - x0) * (Z - z0) / (z1 - z0 + 1e-12) + x0)
            inside ^= hit
        return inside

    # ------------------------------------------------------------------ lookup
    def wsample(self, A, bx, by):
        """Bilinear sample of a per-cell weight array at BLENDER x, y."""
        u = (np.asarray(bx, float) - self.origin[0]) / self.cell - 0.5
        v = ((-np.asarray(by, float)) - self.origin[1]) / self.cell - 0.5
        u = np.clip(u, 0, self.cols - 1.001)
        v = np.clip(v, 0, self.rows - 1.001)
        i0, j0 = u.astype(int), v.astype(int)
        tx, ty = u - i0, v - j0
        return (A[i0, j0] * (1 - tx) * (1 - ty) + A[i0 + 1, j0] * tx * (1 - ty)
                + A[i0, j0 + 1] * (1 - tx) * ty + A[i0 + 1, j0 + 1] * tx * ty)

    def type_at(self, x, z):
        """Zone NAME at RUNTIME (x, z) — the same function SIM.zone implements."""
        c = int(math.floor((x - self.origin[0]) / self.cell))
        r = int(math.floor((z - self.origin[1]) / self.cell))
        if c < 0 or r < 0 or c >= self.cols or r >= self.rows:
            return None
        return ZONES[int(self.idx[c, r])]

    def type_at_blender(self, bx, by):
        return self.type_at(bx, -by)

    # ------------------------------------------------------------------ export
    def coverage(self):
        n = float(self.idx.size)
        return {ZONES[i]: 100.0 * float((self.idx == i).sum()) / n for i in range(len(ZONES))}

    def to_dict(self):
        rows = []
        for r in range(self.rows):
            run = []
            col = self.idx[:, r]
            t, k = int(col[0]), 1
            for c in range(1, self.cols):
                if int(col[c]) == t:
                    k += 1
                else:
                    run += [t, k]
                    t, k = int(col[c]), 1
            run += [t, k]
            rows.append(run)
        return {
            "_doc": [
                "Terrain zone grid for the overworld tile — the encounter geography.",
                "AXES: runtime/three.js coords (+x east, +z south). Blender y = -z.",
                "CELL LOOKUP: col = floor((x - origin[0]) / cell), "
                "row = floor((z - origin[1]) / cell); out of range = no zone.",
                "TYPES: 'types' is the REGISTRY and cells store indices into it. "
                "Append new types at the END only — an index is a shipped contract. "
                "Adding a type needs no schema change and no runtime change.",
                "COLORS: 'colors' is parallel to 'types' (hex, no #) so the debug "
                "overlay also needs no code change when a type is appended.",
                "ROWS_RLE: one entry per row, ordered by increasing z from origin[1]. "
                "Each entry is a flat [typeIndex, runLength, typeIndex, runLength, ...] "
                "run-length encoding along +x. Run lengths per row sum to 'cols'.",
                "DERIVATION: crag = slope/local-relief percentiles of the shared field "
                "+ the gorge mask; water = the analytic river channel + mooring basin; "
                "road = the carriage-road polyline buffered to 1.9u; forest = coherent "
                "value-noise patches (the SAME mask that plants the trees); meadow = "
                "everything else. Priority: road > water > crag > forest > meadow.",
                "OVERRIDES: an authored stamp layer (ellipses/polygons) is applied "
                "LAST so fiction can overrule landform (settlements are 'road' = safe).",
                "CONSUMERS: SIM.zone(x, z) -> type string; SIM.zoneInfo() -> registry; "
                "Z toggles the debug tint overlay in public/play3d.html.",
            ],
            "cell": self.cell,
            "origin": [self.origin[0], self.origin[1]],
            "cols": self.cols,
            "rows": self.rows,
            "types": list(ZONES),
            "colors": list(ZONE_COLS),
            "coverage_pct": {k: round(v, 2) for k, v in self.coverage().items()},
            "derivation": dict(self.thresh, overrides=len(self.overrides),
                               override_cells=int(self.n_override)),
            "rows_rle": rows,
        }

    def write(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        d = self.to_dict()
        with open(path, "w") as f:
            json.dump(d, f, separators=(",", ":"))
        return d


def _pool_w_np(x, y, fr, k=1.0):
    """O2.pool_w without the bpy import — the basin ellipse, 0..1.

    `k` scales the ellipse: k > 1 is the flat APRON the jetty root, the dock spur
    and the village bank all need, which is wider than the water itself.
    """
    dx = np.asarray(x, float) - fr["ctr"][0]
    dy = np.asarray(y, float) - fr["ctr"][1]
    u = (dx * fr["tg"][0] + dy * fr["tg"][1]) / (9.5 * k)
    v = dx * fr["nrm"][0] + dy * fr["nrm"][1]
    vv = v / (np.where(v >= 0, 6.4, 2.8) * k)
    return 1.0 - L.sstep(0.58, 1.0, np.sqrt(u * u + vv * vv))


# ---------------------------------------------------------------------------
# PART 2 — ZONE-DRIVEN TERRAIN TREATMENT
# ---------------------------------------------------------------------------
CRAG_AMP = 1.45                 # peak vertical break-up in a full-weight crag cell
# Corridors the treatment must never touch, appended by the build script before the
# terrain is built: [(x0, y0, x1, y1, inner, outer)] in BLENDER coords.  The road has
# its own analytic guard (F.road_dist); the dock spur does not exist as a field, so
# its two endpoints are handed over instead.  Module state rather than a parameter
# because height() is called from the mesh, the planting, the markers and the QA
# overlay, and all five have to agree by construction.
FLAT_PATHS = []
SPLIT_W = 0.45                  # crag weight above which a quad gets a centre fan
FLAT_W = 0.62                   # ... and above which its facets shade FLAT
# THE PLAN AREA A JITTERED LATTICE CELL MUST KEEP, as a share of STEP^2/2.
#
# The jitter below is POLAR with a radius that reaches 0.99*STEP in a full-weight
# crag cell — and two neighbours 1*STEP apart, each free to move 0.99*STEP, CROSS
# OVER.  The cell turns inside out, its triangles come out as slivers, and on a
# near-vertical wall the fan centre then lands outside its own cell, samples
# height() from a different part of the face, and stands out of it as a needle.
# Measured in the SHIPPED r13 GLB (scratchpad census of ow-valley/scene.glb):
# 2,648 of 22,995 ow_f2_ter_rock triangles (11.5%) plan-INVERTED, 1,450 at aspect
# > 20, worst 3,533:1, longest edge 17.7 u — against 0.083% on grass, where the
# crag weight is zero.  That is the "dozens of hard-edged black sliver polygons,
# densest between centre and right" three critics in a row named on the gorge
# wall, and it is why round 12's shadow-map A/B found nothing: IT WAS NEVER
# SHADING.  (The material is doubleSided, so an inverted facet is not culled —
# three.js flips its normal to face the viewer, which is why the fins come out
# bright on one side and black on the other rather than as holes.)
#
# `_relax_jitter` walks the OFFENDING vertices' own jitter back until every cell
# clears this floor, so the free jitter survives everywhere it was already safe —
# a smaller constant would have paid for the fix over the whole tile.  And the
# builder prints its own census and refuses to ship a non-zero one: A CONSTRUCTION
# THAT CAN INVERT NEEDS A GATE ON THE BUILD, NOT A SMALLER CONSTANT.
MIN_CELL_AREA = 0.20
MIN_FAN_AREA = 0.10             # ... and for the four triangles of a centre fan


def crag_disp(F, zg, x, y, fr=None):
    """Analytic crag displacement at BLENDER (x, y).

    Analytic on purpose: the mesh, the tree feet, the marker posts and the QA
    overlay all call this one function, so they agree by construction instead of
    by luck (round-2 finding 141, applied to relief instead of to a pool).

    Zero wherever the SHARED blockout has to stay exact: the road grade, the
    river channel, both settlement shelves, the dam and the mooring basin.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    w = zg.wsample(zg.crag_w, x, y)

    g = L.sstep(3.2, 6.8, F.road_dist(x.ravel(), y.ravel()).reshape(x.shape))
    dr, tr = F._river_dist(x.ravel(), y.ravel())
    dr = dr.reshape(x.shape)
    hw = F.water_halfwidth(tr).reshape(x.shape)
    g = g * L.sstep(0.8, 4.2, dr - hw)                  # the channel stays exact
    vx, vy = L.VILLAGE
    g = g * L.sstep(7.0, 13.5, np.hypot(x - vx, y - vy))
    cx, cy = L.CLIFFTOWN
    g = g * L.sstep(6.5, 12.5, np.hypot(x - cx, y - cy))
    # the dam + mill sit ON the gorge head, which is the craggiest ground here
    rt, rx, ry = L.river_pts(601)
    di = int(np.argmin(np.abs(rt - L.DAM_T)))
    g = g * L.sstep(6.0, 11.0, np.hypot(x - rx[di], y - ry[di]))
    if fr is not None:
        # the basin AND a wider apron: the jetty root, the dock spur and the
        # village bank are all walk ribbons laid 0.09u above this ground, so
        # anything that lifts it here pokes straight through them
        g = g * (1.0 - _pool_w_np(x, y, fr, 1.9))
    for (x0, y0, x1, y1, inner, outer) in FLAT_PATHS:
        g = g * L.sstep(inner, outer, _seg_dist(x, y, x0, y0, x1, y1))

    d = ((ridged(x, y, 0.155, 11) - 0.42) * 1.55
         + (ridged(x, y, 0.410, 23) - 0.42) * 0.85
         + (ridged(x, y, 1.030, 37) - 0.42) * 0.42)
    return d * CRAG_AMP * np.clip(w, 0.0, 1.0) ** 1.35 * g


def road_notch(F, x, y, depth=0.16):
    """The carriage road is WORN INTO the ground by 0.16u.

    Round 1 grades the terrain to the road's own profile, but the walk ribbon is a
    LINEAR interpolation along the polyline while the terrain is a BILINEAR
    interpolation of a nearest-index grade — the two disagree by a few centimetres,
    and a ribbon that floats only 0.09u is then pierced by its own hillside in a
    perfect sawtooth (every terrain triangle that happens to land high).  Sinking
    the corridor costs one line, is invisible at 0.16u, and is also just true: a
    road that has been used is lower than the field beside it.
    """
    drd = F.road_dist(np.asarray(x, float).ravel(), np.asarray(y, float).ravel())
    return -depth * (1.0 - L.sstep(1.5, 4.2, drd)).reshape(np.shape(x))


def _seg_dist(x, y, x0, y0, x1, y1):
    """Distance from every (x, y) to the segment (x0,y0)-(x1,y1)."""
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    t = np.clip(((np.asarray(x, float) - x0) * dx
                 + (np.asarray(y, float) - y0) * dy) / max(L2, 1e-9), 0.0, 1.0)
    return np.hypot(np.asarray(x, float) - (x0 + t * dx),
                    np.asarray(y, float) - (y0 + t * dy))


def height(F, zg, x, y, fr=None):
    """The F2 ground height — the shared field PLUS the crag treatment."""
    return F.sample(x, y) + crag_disp(F, zg, x, y, fr) + road_notch(F, x, y)


def _cell_cross(PX, PY):
    """The four corner cross products of every lattice cell, in PLAN.

    Corners are walked a=(i,j) b=(i+1,j) c=(i+1,j+1) d=(i,j+1), which is CCW on the
    unjittered lattice, so every cross is +STEP^2 there.  A cell whose smallest cross
    has gone to zero or negative is a cell the jitter has folded; testing all four
    (rather than the two triangles that happen to be emitted) makes the result good
    for BOTH diagonals and for the centre fan, which is what the emit picks between.
    """
    ax, ay = PX[:-1, :-1], PY[:-1, :-1]
    bx, by = PX[1:, :-1], PY[1:, :-1]
    cx, cy = PX[1:, 1:], PY[1:, 1:]
    dx, dy = PX[:-1, 1:], PY[:-1, 1:]
    q = ((ax, ay), (bx, by), (cx, cy), (dx, dy))
    out = []
    for k in range(4):
        (x0, y0), (x1, y1), (x2, y2) = q[k], q[(k + 1) % 4], q[(k + 2) % 4]
        out.append((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1))
    return np.stack(out, 0)


def _relax_jitter(X, Y, JX, JY, step, min_area=MIN_CELL_AREA, iters=24):
    """Shrink only the jitter that folds a cell.  Returns (MX, MY, scale, n_bad0).

    Deterministic and monotone: every pass finds the vertices of every cell still
    under the floor and multiplies THEIR OWN scale by 0.72, so a vertex is only ever
    walked back on the evidence of a cell it actually breaks.  Converges because at
    scale 0 the cell is the unjittered lattice, whose crosses are all step^2.
    """
    s = np.ones_like(X)
    floor = min_area * step * step
    bad0 = None
    for _ in range(iters):
        MX, MY = X + JX * s, Y + JY * s
        worst = _cell_cross(MX, MY).min(0)
        bad = worst < floor
        if bad0 is None:
            bad0 = int(bad.sum())
        if not bad.any():
            return MX, MY, s, bad0
        m = np.zeros_like(X, dtype=bool)
        m[:-1, :-1] |= bad
        m[1:, :-1] |= bad
        m[1:, 1:] |= bad
        m[:-1, 1:] |= bad
        s = np.where(m, s * 0.72, s)
    MX, MY = X + JX * s, Y + JY * s
    return MX, MY, s, bad0


def _relax_fan(MX, MY, si, sj, ox, oy, step, min_area=MIN_FAN_AREA, iters=24):
    """Pull each fan centre back toward its own cell's centroid until all four
    triangles of the fan clear the floor.  A convex cell's centroid always does, so
    the halving terminates; the offset survives wherever it was already inside."""
    ax, ay = MX[si, sj], MY[si, sj]
    bx, by = MX[si + 1, sj], MY[si + 1, sj]
    cx, cy = MX[si + 1, sj + 1], MY[si + 1, sj + 1]
    dx, dy = MX[si, sj + 1], MY[si, sj + 1]
    gx, gy = (ax + bx + cx + dx) / 4.0, (ay + by + cy + dy) / 4.0
    t = np.ones(len(si))
    floor = min_area * step * step
    pulled = None
    for _ in range(iters):
        mx, my = gx + ox * t, gy + oy * t
        w = np.full(len(si), np.inf)
        for (x0, y0), (x1, y1) in (((ax, ay), (bx, by)), ((bx, by), (cx, cy)),
                                   ((cx, cy), (dx, dy)), ((dx, dy), (ax, ay))):
            w = np.minimum(w, (x1 - x0) * (my - y1) - (y1 - y0) * (mx - x1))
        bad = w < floor
        if pulled is None:
            pulled = int(bad.sum())
        if not bad.any():
            return mx, my, pulled
        t = np.where(bad, t * 0.5, t)
    return gx + ox * t, gy + oy * t, pulled


def build_terrain(coll, F, zg, fr, name="ground_valley"):
    """The zone-aware terrain mesh.  Returns (ground, skirt, face_crag).

    THREE things kill round 2's "regular sharp triangles", and it takes all three:

     1. the triangulation DIAGONAL is hashed per quad, not alternated.  Round 1's
        herringbone `(i + j) % 2` is a perfectly regular chevron, and any shading
        discontinuity at all makes the eye read the lattice, not the land.
     2. the XY jitter is POLAR (hashed angle x hashed radius) instead of two
        independent uniforms — an axis-aligned jitter box still leaves the grid
        legible along both axes.
     3. crag quads get a jittered CENTRE VERTEX and fan into 4 triangles.  A
        centre fan is crack-free by construction (the quad's own four boundary
        edges are untouched, so there is never a T-junction with a smooth
        neighbour) and it is the cheapest way to make crag denser AND irregular.
    """
    X, Y = F.X, F.Y
    ii, jj = np.meshgrid(np.arange(L.NX), np.arange(L.NY), indexing="ij")
    cwv = zg.wsample(zg.crag_w, X, Y)

    ang = _hash01(ii, jj, 5) * 2.0 * math.pi
    rad = (0.26 + 0.30 * _hash01(ii, jj, 6)) * (0.52 + 1.25 * cwv)
    interior = np.zeros_like(X)
    interior[1:-1, 1:-1] = 1.0                          # the rim must stay on the tile
    JX = np.cos(ang) * rad * L.STEP * interior
    JY = np.sin(ang) * rad * L.STEP * interior
    # ...and then walked back wherever it folds a cell (see MIN_CELL_AREA).
    MX, MY, jscale, fold0 = _relax_jitter(X, Y, JX, JY, L.STEP)
    Z = height(F, zg, MX, MY, fr)

    g = np.arange(L.NX * L.NY).reshape(L.NX, L.NY)
    qw = (cwv[:-1, :-1] + cwv[1:, :-1] + cwv[1:, 1:] + cwv[:-1, 1:]) / 4.0
    hd = _hash01(ii[:-1, :-1], jj[:-1, :-1], 9)
    hc = _hash01(ii[:-1, :-1], jj[:-1, :-1], 12)
    ha = _hash01(ii[:-1, :-1], jj[:-1, :-1], 13)

    # every centre vertex is solved in ONE vectorised height() call.  Calling the
    # analytic field once per quad instead costs 6-7 seconds a tile, and per-tile
    # build cost is the axis this whole comparison is being judged on (finding 148).
    split = qw > SPLIT_W
    si, sj = np.nonzero(split)
    cidx = np.full(split.shape, -1, dtype=np.int64)
    extra = np.zeros((0, 3))
    fan0 = 0
    if len(si):
        th = ha[si, sj] * 2.0 * math.pi
        rr = 0.30 * L.STEP * hc[si, sj]
        # THE CENTRE HAS TO STAY IN ITS OWN CELL.  height() is analytic, so a centre
        # that has wandered outside samples the face somewhere else entirely — on a
        # 30 u gorge wall that is the 17 u needle in the r13 census, not a 0.3 u
        # displacement.  _relax_fan pulls only the ones that escaped.
        mx, my, fan0 = _relax_fan(MX, MY, si, sj, np.cos(th) * rr, np.sin(th) * rr,
                                  L.STEP)
        # the centre vertex also spikes/pits: this is what turns four coplanar
        # triangles into broken rock instead of one flat lozenge
        mz = height(F, zg, mx, my, fr) + (hc[si, sj] - 0.5) * 0.62 * qw[si, sj]
        extra = np.stack([mx, my, mz], -1)
        cidx[si, sj] = L.NX * L.NY + np.arange(len(si))

    verts = np.concatenate([np.stack([MX.ravel(), MY.ravel(), Z.ravel()], -1),
                            extra]).tolist()
    faces, fcrag = [], []
    n_split = int(split.sum())
    for i in range(L.NX - 1):
        for j in range(L.NY - 1):
            a_, b_, c_, d_ = g[i, j], g[i + 1, j], g[i + 1, j + 1], g[i, j + 1]
            w = float(qw[i, j])
            m = int(cidx[i, j])
            if m >= 0:
                faces += [(a_, b_, m), (b_, c_, m), (c_, d_, m), (d_, a_, m)]
                fcrag += [w] * 4
            elif float(hd[i, j]) < 0.5:
                faces += [(a_, b_, c_), (a_, c_, d_)]
                fcrag += [w, w]
            else:
                faces += [(a_, b_, d_), (b_, c_, d_)]
                fcrag += [w, w]

    # ---- THE GATE.  Measured on the triangles that are about to be emitted, not
    # on the jitter that was intended: a builder that checks its own drawing cannot
    # see its own build.  Inverted must be ZERO — a sliver here is a black wedge on
    # the gorge wall in the shipped bundle.
    _V = np.asarray(verts, float)
    _T = _V[np.asarray(faces, np.int64)]
    _sa = 0.5 * ((_T[:, 1, 0] - _T[:, 0, 0]) * (_T[:, 2, 1] - _T[:, 0, 1])
                 - (_T[:, 2, 0] - _T[:, 0, 0]) * (_T[:, 1, 1] - _T[:, 0, 1]))
    _inv = int((_sa <= 0.0).sum())
    _thin = int((_sa < 0.02 * L.STEP * L.STEP).sum())
    print("  terrain jitter gate: %d cells folded / %d fan centres escaped, relaxed "
          "(jitter kept at %.0f%% of authored on average, %.0f%% at worst); emitted "
          "%d tris, INVERTED %d, plan-area<2%% %d (min %.4f u2)"
          % (fold0, fan0, 100.0 * float(jscale.mean()), 100.0 * float(jscale.min()),
             len(faces), _inv, _thin, float(_sa.min())))
    if _inv:
        raise RuntimeError("build_terrain: %d inverted triangles survived the relax "
                           "(MIN_CELL_AREA/MIN_FAN_AREA too low, or iters exhausted)"
                           % _inv)

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ground = bpy.data.objects.new(name, me)
    coll.objects.link(ground)
    ground["ow_terrain"] = 1

    O2.carve_pool(ground, F, fr)                        # the round-2 mooring basin

    fcrag = np.array(fcrag)
    # smooth baseline everywhere; only real crag facets shade flat.  The 0.45 /
    # 0.62 gap IS the 1-2 cell border blend: the outer band is dense and
    # displaced but still smooth, so meadow flows into rock.
    sm = (fcrag <= FLAT_W).astype(np.int8)
    me.polygons.foreach_set("use_smooth", sm.tolist())
    me.update()

    # ---- skirt, rebuilt from the ACTUAL boundary verts so it still welds ----
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    bx = ([(i, 0) for i in range(L.NX)]
          + [(L.NX - 1, j) for j in range(L.NY)]
          + [(i, L.NY - 1) for i in range(L.NX - 1, -1, -1)]
          + [(0, j) for j in range(L.NY - 1, -1, -1)])
    p = B.Prop("edge_skirt")
    top = [tuple(co[int(g[i, j])]) for i, j in bx]
    p.strip(17, [(x, y, -7.0) for x, y, _ in top], top)          # 17 = BASE
    skirt = p.finish(coll)
    print("  terrain: %d verts, %d tris, %d crag quads fanned (%.1f%% of quads)"
          % (len(verts), len(faces), n_split,
             100.0 * n_split / ((L.NX - 1) * (L.NY - 1))))
    return ground, skirt, fcrag


def conform_ribbon(ob, F, zg, fr, clear=0.07):
    """Lift any walk-ribbon vertex the terrain has caught up with.

    The guards above keep the treatment away from the designed corridors, but a
    guard is a smooth falloff and a ribbon is a hard surface 0.06-0.09u off the
    ground: the last few centimetres are cheaper to fix here than to reason about.
    Only ever LIFTS, so the designed grade is preserved everywhere it already
    clears — and it is exactly what overworld3_verify's clearance gate measures.
    """
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    gz = height(F, zg, co[:, 0], co[:, 1], fr) + clear
    n = int((co[:, 2] < gz).sum())
    if n:
        co[:, 2] = np.maximum(co[:, 2], gz)
        me.vertices.foreach_set("co", co.ravel())
        me.update()
    return n


def build_zone_overlay(coll, F, zg, fr, name="qa_zone_overlay"):
    """The Blender-side twin of the runtime's Z overlay: one tinted quad per
    cell, hovering just off the ground.  Render-only — stripped at export, the
    runtime builds its own from zones.json."""
    pal = np.array([B.srgb(h) for h in ZONE_COLS])
    e = zg.cell * 0.46
    cc, rr = np.meshgrid(np.arange(zg.cols), np.arange(zg.rows), indexing="ij")
    bx = zg.origin[0] + (cc + 0.5) * zg.cell
    by = -(zg.origin[1] + (rr + 0.5) * zg.cell)
    off = ((-e, -e), (e, -e), (e, e), (-e, e))               # CCW seen from above
    XS = np.stack([bx + o[0] for o in off], -1)
    YS = np.stack([by + o[1] for o in off], -1)
    ZS = height(F, zg, XS, YS, fr) + 0.34                    # ONE vectorised call
    verts = np.stack([XS, YS, ZS], -1).reshape(-1, 3).tolist()
    n = zg.cols * zg.rows
    faces = (np.arange(n * 4).reshape(n, 4)).tolist()
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    a = B.ensure_col(me)
    d = np.ones((len(me.loops), 4))
    d[:, :3] = np.repeat(pal[zg.idx.ravel()], 4, axis=0)
    a.data.foreach_set("color", d.ravel())
    ob.hide_render = True                               # only the zones shot turns it on
    return ob


# ---------------------------------------------------------------------------
# PART 3 — PROCEDURAL VEGETATION MAPS  (one-off assets, not a per-tile cost)
# ---------------------------------------------------------------------------
def _stamp_wrap(buf, cx, cy, ang, ra, rb, rgb, alpha=1.0):
    """Rasterise one rotated ellipse, WRAPPING at the edges so the map tiles."""
    h, w = buf.shape[:2]
    r = int(max(ra, rb)) + 2
    yy, xx = np.mgrid[int(cy) - r:int(cy) + r + 1, int(cx) - r:int(cx) + r + 1]
    dx, dy = xx - cx, yy - cy
    ca, sa = math.cos(ang), math.sin(ang)
    u = (dx * ca + dy * sa) / max(ra, 1e-3)
    v = (-dx * sa + dy * ca) / max(rb, 1e-3)
    dd = u * u + v * v
    m = dd <= 1.0
    if not m.any():
        return
    shade = (1.0 - 0.30 * np.clip(dd, 0, 1))
    ix = (xx % w)[m]
    iy = (yy % h)[m]
    buf[iy, ix, :3] = np.asarray(rgb)[None, :] * shade[m][:, None]
    buf[iy, ix, 3] = alpha


def _normal_map(hgt, strength=2.4):
    """Tileable normal map from a height field (np.roll = wrap = tiles)."""
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    n = np.stack([-gx * strength, -gy * strength, np.ones_like(hgt)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    out = np.ones(hgt.shape + (4,), np.float32)
    out[..., :3] = n * 0.5 + 0.5
    return out


def _save(name, path, buf, fmt="JPEG"):
    im = bpy.data.images.new(name, buf.shape[1], buf.shape[0], alpha=(fmt == "PNG"))
    im.filepath_raw = path
    im.file_format = fmt
    im.pixels.foreach_set(np.ascontiguousarray(buf[::-1], dtype=np.float32).ravel())
    im.update()
    im.save()
    return im


def canopy_maps(size=1024, seed=17, force=False):
    """A TILEABLE leaf-mass albedo + normal for the sculpted canopies.

    This is approach (a)'s "baked" albedo/normal — but baked in numpy, not in
    Cycles: it is a ONE-OFF asset like round 2's card atlases (finding 148), so
    it never appears in the per-tile build cost.
    """
    d = os.path.join(TEXO, "veg3_canopy_diff_1k.jpg")
    n = os.path.join(TEXO, "veg3_canopy_nor_1k.jpg")
    if not force and os.path.exists(d) and os.path.exists(n):
        return d, n
    rng = np.random.RandomState(seed)
    buf = np.zeros((size, size, 4), np.float32)
    buf[..., :3] = np.array([0.055, 0.085, 0.040])       # gaps read as canopy shadow
    buf[..., 3] = 1.0
    hgt = np.zeros((size, size), np.float32)
    base = np.array([0.30, 0.46, 0.17])
    # three passes, coarse to fine: the coarse leaves make MASSES (which is what
    # a canopy is at 16u) and the fine ones keep it from smearing up close
    for pas, (nleaf, s0, s1, lift) in enumerate(
            ((520, 0.055, 0.085, 0.55), (1500, 0.028, 0.046, 0.80), (3800, 0.013, 0.024, 1.0))):
        for k in range(nleaf):
            lx, ly = rng.rand() * size, rng.rand() * size
            m = fbm(np.array([lx * 0.02]), np.array([ly * 0.02]), 0.6, 3)[0]
            col = base * (0.42 + 1.05 * m * lift + 0.30 * rng.rand())
            if rng.rand() < 0.055:                       # a few turning leaves
                col = np.array([0.52, 0.30, 0.09]) * (0.7 + 0.6 * rng.rand())
            ra = size * (s0 + (s1 - s0) * rng.rand())
            _stamp_wrap(buf, lx, ly, rng.rand() * math.pi, ra,
                        ra * (0.40 + 0.28 * rng.rand()), col)
            # the same leaf, written into the height field the normal map comes from
            hh = 0.25 + 0.75 * (pas / 2.0)
            y0, y1 = int(ly - ra), int(ly + ra) + 1
            x0, x1 = int(lx - ra), int(lx + ra) + 1
            yy, xx = np.mgrid[y0:y1, x0:x1]
            dd = ((xx - lx) / max(ra, 1e-3)) ** 2 + ((yy - ly) / max(ra * 0.5, 1e-3)) ** 2
            mm = dd <= 1.0
            if mm.any():
                hgt[(yy % size)[mm], (xx % size)[mm]] = hh * (1.0 - 0.5 * dd[mm])
    _save("veg3_canopy_diff", d, np.clip(buf, 0, 1), "JPEG")
    _save("veg3_canopy_nor", n, _normal_map(hgt, 3.0), "JPEG")
    print("  canopy maps written")
    return d, n


def bark_maps(size=512, seed=29, force=False):
    """Tileable bark: vertical fissures.  A plank photo on a round trunk reads as
    a plank, which is half of why round 1's trees looked like toys."""
    d = os.path.join(TEXO, "veg3_bark_diff_1k.jpg")
    n = os.path.join(TEXO, "veg3_bark_nor_1k.jpg")
    if not force and os.path.exists(d) and os.path.exists(n):
        return d, n
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    # anisotropic noise: high frequency across the trunk, low frequency along it
    f1 = fbm(xx * 0.055, yy * 0.011, 1.0, 3, oct_=4)
    f2 = fbm(xx * 0.170, yy * 0.030, 1.0, 41, oct_=3)
    ridge = 1.0 - np.abs(2.0 * f1 - 1.0)
    hgt = (0.62 * ridge + 0.38 * f2).astype(np.float32)
    v = 0.20 + 0.62 * hgt
    buf = np.ones((size, size, 4), np.float32)
    buf[..., 0] = v * 0.80
    buf[..., 1] = v * 0.66
    buf[..., 2] = v * 0.50
    buf[..., :3] = np.clip(buf[..., :3] * (0.86 + 0.30 * f2[..., None]), 0, 1)
    _save("veg3_bark_diff", d, buf, "JPEG")
    _save("veg3_bark_nor", n, _normal_map(hgt, 4.5), "JPEG")
    print("  bark maps written")
    return d, n


def leafmass_atlas(size=1024, seed=31, force=False):
    """A 2x2 atlas of DENSE leaf masses for the card approaches.

    Round 2's leaf atlas drew 290 leaves per cell over a lobed blob and the user
    called the result flakes.  This draws ~1500 per cell over a near-cell-filling
    silhouette with a soft but OPAQUE core, so a card reads as a slab of foliage
    and a handful of them read as a canopy.  PNG: the alpha has to survive the
    JPEG-format export (finding 143).
    """
    p = os.path.join(TEXO, "veg3_leafmass_atlas.png")
    if not force and os.path.exists(p):
        return p
    rng = np.random.RandomState(seed)
    buf = np.zeros((size, size, 4), np.float32)
    c = size // 2
    base = np.array([0.30, 0.45, 0.18])
    for cell in range(4):
        ox, oy = (cell % 2) * c, (cell // 2) * c
        R = c * 0.40
        ph = rng.rand(3) * 6.283
        for k in range(2400):
            a = rng.rand() * 2 * math.pi
            # A NEARLY CELL-FILLING ELLIPSE IS THE OTHER WAY TO FAIL: pack the mass
            # right out to the rim and the card stops being a flake and becomes a
            # hard-edged SHEET, which is what the chase camera catches at a shallow
            # angle.  So: dense core (rand**0.5), a lobed rim, and 16% stragglers
            # thrown past R so the silhouette is made of individual leaves.
            lobe = (0.74 + 0.20 * math.sin(3.0 * a + ph[0])
                    + 0.11 * math.sin(7.0 * a + ph[1]))
            rr = R * (rng.rand() ** 0.5) * lobe
            if rng.rand() < 0.16:
                rr = R * lobe * (1.0 + 0.34 * rng.rand())
            lx = ox + c / 2 + math.cos(a) * rr
            ly = oy + c / 2 + math.sin(a) * rr * 0.94
            kk = min(1.0, rr / R)
            col = base * (0.50 + 0.70 * (1.0 - kk) + 0.34 * rng.rand())
            if rng.rand() < 0.06:
                col = np.array([0.55, 0.31, 0.10]) * (0.65 + 0.55 * rng.rand())
            sz = c * (0.020 + 0.018 * rng.rand()) * (1.10 - 0.26 * kk)
            _stamp_wrap_cell(buf, lx, ly, ox, oy, c, rng.rand() * math.pi,
                             sz, sz * (0.38 + 0.26 * rng.rand()), col)
    _save("veg3_leafmass_atlas", p, buf, "PNG")
    print("  leafmass atlas written")
    return p


def _stamp_wrap_cell(buf, cx, cy, ox, oy, c, ang, ra, rb, rgb):
    """Like _stamp_wrap but CLIPPED to one atlas cell — bleeding across a cell
    boundary is how an atlas grows a seam of someone else's leaves."""
    r = int(max(ra, rb)) + 2
    y0, y1 = max(oy, int(cy) - r), min(oy + c, int(cy) + r + 1)
    x0, x1 = max(ox, int(cx) - r), min(ox + c, int(cx) + r + 1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx, dy = xx - cx, yy - cy
    ca, sa = math.cos(ang), math.sin(ang)
    u = (dx * ca + dy * sa) / max(ra, 1e-3)
    v = (-dx * sa + dy * ca) / max(rb, 1e-3)
    dd = u * u + v * v
    m = dd <= 1.0
    if not m.any():
        return
    sub = buf[y0:y1, x0:x1]
    shade = (1.0 - 0.26 * np.clip(dd, 0, 1))[..., None]
    sub[..., :3] = np.where(m[..., None], np.asarray(rgb) * shade, sub[..., :3])
    sub[..., 3] = np.where(m, 1.0, sub[..., 3])


# ---------------------------------------------------------------------------
# PART 3 — THE TREES
# ---------------------------------------------------------------------------
# Round-3 art classes, continuing round 2's table (which ended at LAMP = 25).
LEAFM, LEAFC, BARK, MARK = range(26, 30)
# LEAFM2 — the SECOND canopy hue, same material and same tile, a cooler and
# deeper green class colour.  It exists because a stand of one species is what
# the blind critic saw on the gorge plateau ("identical instances at identical
# scale on regular spacing"), and hue is the one axis a specimen tree could not
# vary: `Prop` writes COLOR_0 from a face's ART CLASS, so per-instance colour
# means a class, not a parameter.  Anything not tagged with it is untouched.
LEAFM2 = 30

# The line-up hillside.  Chosen by SEARCH, not by taste: the site scan wanted a
# 22u run whose slope stays inside 0.18..0.80 (a hillside, not a cliff and not a
# lawn), 7u+ clear of the road, 7u+ above the local waterline, and 14u+ from both
# settlements.  Blender (-20, -10) at 127.5 deg won.
LINEUP_C = (-20.0, -10.0)
LINEUP_ANG = math.radians(127.5)
LINEUP_T = (-9.0, -3.0, 3.0, 9.0)           # the four group centres along the line
LINEUP_R = 15.0                             # field planting keeps out of this radius


class Veg:
    """One accumulator per vegetation group.

    Three separate meshes, and the split is a RUNTIME contract, not tidiness:
    `veg_` is removed from collision entirely (no standing AND no blocking), so a
    trunk baked into the same mesh as its canopy would make the whole tree
    walk-through (round-2 finding 149).  Cards also need their own mesh because
    they are the only alpha-MASK material in the tile.
    """

    def __init__(self, base):
        self.base = base
        self.trunk = B.Prop("tree_%s_trunks" % base)
        self.mesh = B.Prop("veg_%s" % base)
        self.cards = B.Prop("veg_%s_cards" % base)
        self.uvs = []
        self.n = dict(a=0, b=0, c=0, d=0, e=0, shrub=0, cards=0, lobes=0)

    def finish(self, coll, suffix):
        out = {}
        for key, p in (("trunks", self.trunk), ("mesh", self.mesh), ("cards", self.cards)):
            if not len(p.bm.faces):
                p.bm.free()
                continue
            ob = p.finish(coll)
            nm = p.name + "__" + suffix
            ob.name, ob.data.name = nm, nm
            out[key] = ob
        if "cards" in out:
            O2.apply_card_uvs(out["cards"], self.uvs)
        return out


def _lobe(V, cls, cx, cy, cz, rx, ry, rz_, subd=2, seed=0, squash_top=0.12):
    """A SCULPTED canopy lobe: an icosphere pushed around by low-order harmonics.

    A bare icosphere is round 1's rejected "blob"; the whole difference is that
    the radius here varies with direction, so the silhouette has bites in it and
    the top is flattened the way a crown that has met the sky actually is.
    """
    p = V.mesh
    # `bmesh.ops.create_icosphere` INVALIDATES every existing BMVert proxy, so the
    # `v in set(bm.verts)` idiom that rounds 1/2 use for FACES (which survive) says
    # "new" about every vertex in the mesh — and the sculpt below then re-displaces
    # every earlier lobe relative to this centre.  Compounded over 400 lobes the
    # tile flew apart to 4000u.  Count + ensure_lookup_table + slice is exact.
    n0 = len(p.bm.verts)
    p.ico(cls, (cx, cy, cz), (rx, ry, rz_), subd=subd)
    p.bm.verts.ensure_lookup_table()
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    ph = rng.rand(6) * 6.283
    c = Vector((cx, cy, cz))
    for v in p.bm.verts[n0:]:
        d = v.co - c
        n = d.copy()
        n.normalize()
        # LOW-order terms only.  The first pass carried a third harmonic at 0.13
        # and a 162-vert lobe cannot resolve it: smooth shading over sub-facet
        # deformation gives broad creased plates, and the crown read as a cabbage.
        # The silhouette is what has to vary; leaf detail is the normal map's job.
        k = (1.0
             + 0.31 * math.sin(2.7 * n.x + ph[0]) * math.sin(2.2 * n.y + ph[1])
             + 0.17 * math.sin(3.9 * n.y + ph[2]) * math.sin(3.3 * n.z + ph[3])
             + 0.06 * math.sin(6.9 * n.x + ph[4]) * math.sin(5.9 * n.z + ph[5]))
        k -= squash_top * max(0.0, n.z) ** 2            # crowns are flatter on top
        k += 0.10 * max(0.0, -n.z)                      # and hang lower underneath
        v.co = c + d * max(0.55, k)
    V.n["lobes"] += 1


def _trunk(V, x, y, z, s, rz, h, r0, r1, lean=0.0, seg=7):
    """A tapered trunk in two segments with a flared foot, optionally leaning."""
    dx, dy = math.cos(rz) * lean, math.sin(rz) * lean
    V.trunk.cone(BARK, (x, y, z + h * 0.22), r0 * 1.30, r0, h * 0.44, seg=seg, rz=rz)
    V.trunk.cone(BARK, (x + dx * 0.5, y + dy * 0.5, z + h * 0.66),
                 r0, r1, h * 0.50, seg=seg, rz=rz + 0.4)
    return (x + dx, y + dy, z + h)


def _limb(V, a, b_, r):
    O2.beam(V.trunk, BARK, a, b_, r, r)


def tree_a(V, x, y, z, s, rz, rng):
    """(a) CHUNKY SCULPTED CANOPY — mesh only, procedural albedo + normal.

    Three sculpted lobes on a leaning trunk with two visible limbs.  The bet: a
    canopy that is real geometry never breaks up at any camera distance and never
    sorts wrong, and the leaf DETAIL comes from the map rather than the mesh.
    """
    h = 1.55 * s
    top = _trunk(V, x, y, z, s, rz, h, 0.115 * s, 0.075 * s, lean=0.10 * s)
    for k in range(2):
        a = rz + 1.9 + k * 2.6
        _limb(V, (top[0], top[1], z + h * 0.72),
              (top[0] + math.cos(a) * 0.52 * s, top[1] + math.sin(a) * 0.52 * s,
               z + h * 1.02), 0.045 * s)
    R = 1.00 * s
    _lobe(V, LEAFM, top[0], top[1], z + h + 0.52 * s, R, R * 0.94, R * 0.74,
          subd=2, seed=rng.randint(1 << 28))
    for k in range(2):
        a = rz + 1.1 + k * 3.1
        _lobe(V, LEAFM, top[0] + math.cos(a) * 0.50 * s, top[1] + math.sin(a) * 0.50 * s,
              z + h + (0.24 + 0.34 * k) * s, R * 0.66, R * 0.62, R * 0.52,
              subd=2, seed=rng.randint(1 << 28))
    V.n["a"] += 1


def tree_b(V, x, y, z, s, rz, rng):
    """(b) LAYERED ALPHA-MASK CARD CLUSTERS — dense enough to stop being flakes.

    Round 2's H hung SIX cards on a trunk and the user saw flakes.  This hangs
    32-40, in four vertical shells whose radius shrinks upward, each card pitched
    38-72 deg from vertical and leaning OUTWARD (yaw = a - pi/2: the sign decides
    whether the crown opens or collapses into the trunk — round-2 finding 145).
    """
    h = 1.60 * s
    top = _trunk(V, x, y, z, s, rz, h, 0.105 * s, 0.070 * s, lean=0.08 * s)
    for k in range(3):
        a = rz + 0.7 + k * 2.1
        _limb(V, (top[0], top[1], z + h * 0.78),
              (top[0] + math.cos(a) * 0.42 * s, top[1] + math.sin(a) * 0.42 * s,
               z + h * 1.10), 0.038 * s)
    # five shells over 1.55u of crown, not four over 1.0u: the first pass made a
    # wide shallow disc and the render read it as a flying saucer.  Cards are also
    # SMALLER and more numerous, and the lower shells stand more upright (pitch is
    # measured from vertical) so the crown has height instead of just spread.
    LAY = ((0.00, 0.50, 8, 58, 80), (0.26, 0.64, 11, 40, 66),
           (0.54, 0.62, 11, 30, 58), (0.80, 0.46, 8, 24, 50),
           (1.00, 0.26, 5, 18, 42))
    for li, (dz, rad, ncard, p0, p1) in enumerate(LAY):
        for k in range(ncard):
            a = rz + k * (2 * math.pi / ncard) + li * 0.47 + rng.uniform(-0.16, 0.16)
            r = rad * s * rng.uniform(0.80, 1.06)
            O2.card(V.cards, LEAFC,
                    top[0] + math.cos(a) * r, top[1] + math.sin(a) * r,
                    z + h + (0.10 + 1.55 * dz) * s,
                    1.06 * s * rng.uniform(0.84, 1.12),
                    1.06 * s * rng.uniform(0.84, 1.12),
                    a - math.pi / 2,
                    pitch=math.radians(rng.uniform(p0, p1)),
                    cell=rng.randint(4), uvs=V.uvs)
            V.n["cards"] += 1
    V.n["b"] += 1


def tree_c(V, x, y, z, s, rz, rng):
    """(c) HYBRID — a sculpted mesh CORE with an alpha-card FRINGE.

    The mesh core owns the mass and the shading; the cards only break the
    silhouette where the sky shows through, which is the one job a card is
    actually good at.  Fewer cards than (b), and none of them load-bearing.
    """
    h = 1.62 * s
    top = _trunk(V, x, y, z, s, rz, h, 0.115 * s, 0.075 * s, lean=0.09 * s)
    R = 0.70 * s
    cz = z + h + 0.42 * s
    _lobe(V, LEAFM, top[0], top[1], cz, R, R * 0.95, R * 0.78,
          subd=2, seed=rng.randint(1 << 28))
    _lobe(V, LEAFM, top[0] + 0.30 * s, top[1] - 0.22 * s, cz + 0.34 * s,
          R * 0.60, R * 0.58, R * 0.48, subd=1, seed=rng.randint(1 << 28))
    # the fringe rides the crown's LOWER OUTER band only.  Cards laid over the top
    # are what the steep follow camera sees flat, and a card seen flat is a flake —
    # here the mesh core owns everything the camera looks down on.
    for k in range(18):
        a = rz + k * (2 * math.pi / 18) + rng.uniform(-0.18, 0.18)
        r = R * rng.uniform(0.92, 1.16)
        O2.card(V.cards, LEAFC,
                top[0] + math.cos(a) * r, top[1] + math.sin(a) * r,
                cz + rng.uniform(-0.44, 0.06) * s,
                1.02 * s, 0.92 * s, a - math.pi / 2,
                pitch=math.radians(rng.uniform(22.0, 48.0)),
                cell=rng.randint(4), uvs=V.uvs)
        V.n["cards"] += 1
    V.n["c"] += 1


def tree_d(V, x, y, z, s, rz, rng, depth=3):
    """(d) BRANCH-DRIVEN — my own: a recursive limb skeleton carrying small leaf
    CLUSTERS at its tips.

    Both earlier failures came from treating the canopy as one primitive: a blob
    is too simple and a card is too thin.  Here the silhouette is made by
    STRUCTURE — you can see through it, the gaps are branch-shaped, and every
    leaf mass is a small sculpted lobe, so nothing is ever seen edge-on.
    """
    h = 1.55 * s
    top = _trunk(V, x, y, z, s, rz, h, 0.125 * s, 0.080 * s, lean=0.06 * s)
    tips = []

    def grow(p0, d0, ln, rad, dep):
        p1 = (p0[0] + d0[0] * ln, p0[1] + d0[1] * ln, p0[2] + d0[2] * ln)
        _limb(V, p0, p1, rad)
        if dep == 0:
            tips.append(p1)
            return
        for k in range(2 if dep < depth else 3):
            a = rng.uniform(0, 2 * math.pi)
            spread = rng.uniform(0.42, 0.78)
            d1 = (d0[0] + math.cos(a) * spread, d0[1] + math.sin(a) * spread,
                  d0[2] * rng.uniform(0.62, 0.94))
            nn = math.sqrt(sum(v * v for v in d1)) or 1.0
            grow(p1, (d1[0] / nn, d1[1] / nn, d1[2] / nn),
                 ln * rng.uniform(0.62, 0.80), rad * 0.66, dep - 1)

    grow((top[0], top[1], z + h * 0.85), (0.0, 0.0, 1.0), 0.80 * s, 0.070 * s, depth)
    for (tx, ty, tz) in tips:
        r = 0.40 * s * rng.uniform(0.82, 1.24)
        _lobe(V, LEAFM, tx, ty, tz + r * 0.5, r, r * 0.94, r * 0.80,
              subd=1, seed=rng.randint(1 << 28), squash_top=0.06)
    V.n["d"] += 1


# ---- shrubs: one per approach, so the line-up compares understory too --------
def shrub_a(V, x, y, z, s, rz, rng):
    for k in range(2):
        a = rz + k * 2.4
        _lobe(V, LEAFM, x + math.cos(a) * 0.26 * s, y + math.sin(a) * 0.26 * s,
              z + 0.30 * s, 0.52 * s, 0.46 * s, 0.30 * s, subd=2,
              seed=rng.randint(1 << 28), squash_top=0.22)
    V.n["shrub"] += 1


def shrub_b(V, x, y, z, s, rz, rng):
    for k in range(10):
        a = rz + k * 0.63
        O2.card(V.cards, LEAFC, x + math.cos(a) * 0.24 * s, y + math.sin(a) * 0.24 * s,
                z - 0.05, 0.92 * s, 0.60 * s, a - math.pi / 2,
                pitch=math.radians(rng.uniform(20.0, 55.0)),
                cell=rng.randint(4), uvs=V.uvs)
        V.n["cards"] += 1
    V.n["shrub"] += 1


def shrub_c(V, x, y, z, s, rz, rng):
    _lobe(V, LEAFM, x, y, z + 0.28 * s, 0.46 * s, 0.42 * s, 0.28 * s, subd=1,
          seed=rng.randint(1 << 28), squash_top=0.20)
    for k in range(7):
        a = rz + k * 0.90
        O2.card(V.cards, LEAFC, x + math.cos(a) * 0.36 * s, y + math.sin(a) * 0.36 * s,
                z - 0.04, 0.72 * s, 0.50 * s, a - math.pi / 2,
                pitch=math.radians(rng.uniform(34.0, 66.0)),
                cell=rng.randint(4), uvs=V.uvs)
        V.n["cards"] += 1
    V.n["shrub"] += 1


def shrub_d(V, x, y, z, s, rz, rng):
    for k in range(5):
        a = rz + k * 1.27
        p0 = (x, y, z)
        p1 = (x + math.cos(a) * 0.34 * s, y + math.sin(a) * 0.34 * s, z + 0.52 * s)
        _limb(V, p0, p1, 0.030 * s)
        r = 0.22 * s
        _lobe(V, LEAFM, p1[0], p1[1], p1[2] + r * 0.4, r, r * 0.92, r * 0.78,
              subd=1, seed=rng.randint(1 << 28), squash_top=0.10)
    V.n["shrub"] += 1


def tree_e(V, x, y, z, s, rz, rng):
    """(e) THE SPREADING TREE — the second field species, and it is a second
    PROPORTION before it is a second colour.

    (a) is a tall round lollipop: trunk 1.55 s, one crown of radius 1.00 s sat
    0.52 s above it, total height 2.8 s over a width of 2.0 s.  Planted alone at a
    0.86-1.26 scale ramp it gives the gorge plateau a row of identical mushrooms.
    This one inverts both numbers — a SHORT trunk (0.80 s) under a WIDE, FLAT,
    four-lobed crown (1.30 s across, 0.46 s deep) — so at any scale the two read
    as different plants in profile, which is the thing a distant ridge shows.
    It is tagged LEAFM2, so it is also a cooler green.
    """
    h = 0.80 * s
    top = _trunk(V, x, y, z, s, rz, h, 0.135 * s, 0.090 * s, lean=0.16 * s)
    for k in range(3):
        a = rz + 0.5 + k * 2.2
        _limb(V, (top[0], top[1], z + h * 0.80),
              (top[0] + math.cos(a) * 0.66 * s, top[1] + math.sin(a) * 0.66 * s,
               z + h * 1.18), 0.048 * s)
    R = 0.86 * s
    cz = z + h + 0.30 * s
    _lobe(V, LEAFM2, top[0], top[1], cz, R, R * 0.96, R * 0.52,
          subd=2, seed=rng.randint(1 << 28), squash_top=0.26)
    a0 = rng.uniform(0, 6.283)
    for k in range(3):
        a = a0 + k * 2.094 + rng.uniform(-0.42, 0.42)
        d = R * rng.uniform(0.72, 1.02)
        rr = R * rng.uniform(0.52, 0.76)
        _lobe(V, LEAFM2, top[0] + math.cos(a) * d, top[1] + math.sin(a) * d,
              cz + rng.uniform(-0.16, 0.12) * s, rr, rr * rng.uniform(0.86, 1.10),
              rr * 0.50, subd=2 if rr > R * 0.62 else 1,
              seed=rng.randint(1 << 28), squash_top=0.22)
    V.n["e"] += 1


TREE_FN = dict(a=tree_a, b=tree_b, c=tree_c, d=tree_d, e=tree_e)
SHRUB_FN = dict(a=shrub_a, b=shrub_b, c=shrub_c, d=shrub_d)


# ------------------------------------------------------------------- the line-up
def build_lineup(coll, F, zg, fr, suffix, seed=20260730):
    """Four groups, side by side across one hillside, in build order a,b,c,d.

    Each group is its own object set so the GLB names carry the label, and each
    gets a ground marker with N posts (a = 1 post ... d = 4) — countable in a
    render without needing the object list.
    """
    out, groups = {}, []
    for gi, key in enumerate("abcd"):
        rng = np.random.RandomState(seed + gi * 977)
        V = Veg("lineup_" + key)
        t = LINEUP_T[gi]
        gx = LINEUP_C[0] + math.cos(LINEUP_ANG) * t
        gy = LINEUP_C[1] + math.sin(LINEUP_ANG) * t
        px, py = -math.sin(LINEUP_ANG), math.cos(LINEUP_ANG)
        # 3 trees + 2 shrubs, spread across the line so groups read as clumps
        spots = ((0.0, 0.0, 1.14, "t"), (-1.9, 1.5, 0.96, "t"), (1.9, -1.4, 1.05, "t"),
                 (-1.2, -2.4, 0.80, "s"), (1.4, 2.5, 0.72, "s"))
        for (u, v, sc, kind) in spots:
            x = gx + math.cos(LINEUP_ANG) * u + px * v
            y = gy + math.sin(LINEUP_ANG) * u + py * v
            z = float(height(F, zg, np.array([x]), np.array([y]), fr)[0])
            rz = float(rng.uniform(0, 6.283))
            (TREE_FN if kind == "t" else SHRUB_FN)[key](V, x, y, z, sc, rz, rng)
        out.update({("%s_%s" % (key, k)): o for k, o in V.finish(coll, suffix).items()})
        groups.append((key, gx, gy, V.n))

        # ---- the marker: a stone pad plus (gi + 1) pale posts ----------------
        mp = B.Prop("marker_lineup_" + key)
        # the marker sits on the CAMERA side of its group (add_cameras_f2 stands at
        # +(px, py)); behind the trees it would be a post nobody can count
        mx = gx + px * 3.6
        my = gy + py * 3.6
        mz = float(height(F, zg, np.array([mx]), np.array([my]), fr)[0])
        mp.cube(11, (mx, my, mz + 0.07), (1.30, 0.90, 0.16))            # 11 = STONE
        for k in range(gi + 1):
            ox = (k - gi / 2.0) * 0.30
            mp.cube(MARK, (mx + math.cos(LINEUP_ANG) * ox, my + math.sin(LINEUP_ANG) * ox,
                           mz + 0.44), (0.13, 0.13, 0.72), rz=LINEUP_ANG)
        mo = mp.finish(coll)
        nm = "marker_lineup_%s__%s" % (key, suffix)
        mo.name, mo.data.name = nm, nm
        out["marker_" + key] = mo
    for key, gx, gy, n in groups:
        print("  line-up %s at blender(%.1f, %.1f) runtime(%.1f, %.1f): "
              "%d trees %d shrubs %d cards %d lobes"
              % (key, gx, gy, gx, -gy, n["a"] + n["b"] + n["c"] + n["d"],
                 n["shrub"], n["cards"], n["lobes"]))
    return out, groups


# ------------------------------------------------------- zone-driven field planting
# What goes where, once the line-up has answered the question.  forest = dense,
# meadow = sparse specimens, crag = bare (rock does not grow trees), road/water
# never.  The mix is per ZONE, which is the whole point of having a zone grid.
FIELD_MIX = {
    # (b) is deliberately ABSENT from the field: it stays in the line-up as the
    # exhibit it is.  A card shell is at its worst under a steep aerial follow
    # camera — every card the camera looks down on is seen flat — and that is
    # exactly the camera this world is played through.
    "forest": (("c", 0.60), ("d", 0.24), ("a", 0.16)),
    "meadow": (("a", 0.72), ("c", 0.28)),
}
FIELD_SPACING = {"forest": 3.5, "meadow": 9.5}
FIELD_SHRUB = {"forest": 0.55, "meadow": 0.30}


def plant_field(coll, F, zg, fr, suffix, seed=771, target=None):
    """Scatter by ZONE.  One rejection loop, every rule a zone lookup."""
    rng = np.random.RandomState(seed)
    V = Veg("field")
    vx, vy = L.VILLAGE
    cx, cy = L.CLIFFTOWN
    placed = []
    tries = 0
    target = target or dict(forest=64, meadow=22)
    want = dict(target)
    while sum(want.values()) > 0 and tries < 400000:
        tries += 1
        x = rng.uniform(-56.0, 56.0)
        y = rng.uniform(-42.0, 42.0)
        zt = zg.type_at_blender(x, y)
        if zt not in want or want[zt] <= 0:
            continue
        # the demonstration hillside stays a clean comparison: nothing else in it
        if math.hypot(x - LINEUP_C[0], y - LINEUP_C[1]) < LINEUP_R:
            continue
        sp = FIELD_SPACING[zt]
        if any((x - a) ** 2 + (y - b) ** 2 < sp * sp for a, b, *_ in placed):
            continue
        if float(F.slope_at(np.array([x]), np.array([y]))[0]) > 0.85:
            continue
        if float(F.river_dist([x], [y])[0]) < 4.2:
            continue
        if float(F.road_dist([x], [y])[0]) < 3.0:
            continue
        if math.hypot(x - vx, y - vy) < 9.0 or math.hypot(x - cx, y - cy) < 10.0:
            continue
        z = float(height(F, zg, np.array([x]), np.array([y]), fr)[0])
        wlv = float(L.water_level(np.array([F._river_dist([x], [y])[1][0]]))[0])
        if z < wlv + 1.1 or z > wlv + 26.0:
            continue
        # forest density follows the SAME noise the zone grid was cut from, so the
        # stands thin out at their own edges instead of ending at a cell boundary
        if zt == "forest" and rng.rand() > 0.35 + 0.65 * float(zg.wsample(zg.forest_w, x, y)):
            continue
        mix = FIELD_MIX[zt]
        r = rng.rand()
        acc = 0.0
        key = mix[-1][0]
        for k, w in mix:
            acc += w
            if r <= acc:
                key = k
                break
        s = float(rng.uniform(0.85, 1.25))
        rz = float(rng.uniform(0, 6.283))
        TREE_FN[key](V, x, y, z, s, rz, rng)
        if rng.rand() < FIELD_SHRUB[zt]:
            a = rng.uniform(0, 6.283)
            d = rng.uniform(1.4, 2.6)
            sx, sy = x + math.cos(a) * d, y + math.sin(a) * d
            sz = float(height(F, zg, np.array([sx]), np.array([sy]), fr)[0])
            SHRUB_FN[key](V, sx, sy, sz, float(rng.uniform(0.6, 1.0)),
                          float(rng.uniform(0, 6.283)), rng)
        placed.append((x, y, zt, key))
        want[zt] -= 1
    n = V.n
    print("  field planting: %d trees (a=%d b=%d c=%d d=%d), %d shrubs, %d cards, "
          "%d lobes, %d tries" % (len(placed), n["a"], n["b"], n["c"], n["d"],
                                  n["shrub"], n["cards"], n["lobes"], tries))
    byzone = {}
    for _, _, zt, key in placed:
        byzone.setdefault(zt, {}).setdefault(key, 0)
        byzone[zt][key] += 1
    for zt in sorted(byzone):
        print("    %-7s %s" % (zt, byzone[zt]))
    return V.finish(coll, suffix), placed, byzone
