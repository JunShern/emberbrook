"""valley_land.py — THE LANDSCAPE PASS for ow-valley: L2 and L3, as build steps.

Called from tools/valley_build.py's main() immediately after the terrain materials
are solved, because both halves read the ground's own SLOT CHOICE (grass / dry /
rock) and that is what `B3.terrain_pbr_f2` writes.

WHERE THIS CAME FROM.  The user rejected three overworld candidates with "I'm not
convinced that 'adding more stuff' is more important than 'improving the quality of
our existing stuff'", and set the bar at the FFIX-reimagined references — which
contain no forest at all.  docs/qa/ow-land measured ours against them and found the
reframe: THE REFERENCES ARE PICTURES OF LIGHT, NOT OF GROUND DETAIL.  Three of our
four DAYLIGHT cameras were darker than the reference's NIGHT plate, b-r was negative
in both quartiles of every frame, and the bundle's own COLOR_0 had grass at L 0.383
against rock at L 0.502 — THE GRASS WAS DARKER THAN THE ROCK.  Three techniques came
out of it, measured orthogonal (each barely moves the others' column):

  L1  the hour        light/air/fog        -> public/play3d.html's overworld rig
  L2  ground-is-geometry  +113,924 tris    -> `tufts()` below
  L3  the surface     COLOR_0 only, +0     -> `surface()` below

L2's PLACEMENT RULE *IS* THE CANDIDATE.  A tuft is emitted only where the ground
CHANGES — road edge, grass/sand seam, grass/rock seam — and nowhere else, because a
uniform meadow carpet is exactly the "add more stuff" that was refused, and it is
also the only version that costs real triangles.  Flowers go in PATCHES of 6-14,
never scattered: an even scatter at the same count reads as noise, and that
difference is the whole trick.

FAITHFULNESS.  This is a PORT of tools/ow_probe/land.js, which is the artifact the
decision was made on.  The probe's PRNG, its iteration order and its early-`continue`
sequence are reproduced exactly, so the placement is the same placement — the port is
checked by its own counts against the probe's report:

    17,837 tufts at 6,467 seam cells + 261 clumps + 841 flowers in 89 patches
    ground_valley_1 grass L 0.383 -> 0.638   (16,293 verts)
    ground_valley_2 dry   L 0.345 -> 0.428   ( 1,958 verts)
    ground_valley_3 rock  L 0.502 -> 0.543   (55,793 verts)

A port that lands different numbers than the probe is a PORT BUG until proven
otherwise.  Both functions print theirs.

THREE TRAPS ALREADY PAID FOR, all still live in this file's numbers:
  * SCALE IS AGAINST THE BODY.  Vesper is 1.45 u.  The probe's first tufts were
    0.4-1.0 u tall and the gorge shelf grew a hedge of black agave; the reference's
    grass is ankle-to-shin on its character, so 0.10-0.34.
  * THE SLOPE GATE IS NOT OPTIONAL.  A seam test fires HARDEST where grass meets
    vertical rock, so without it 60 m of gorge wall sprouts grass growing straight
    out of it.  Reject on the terrain's local GRADIENT, never on the zone.
  * AMPLITUDE.  L3's first pass multiplied the rock's blue by 1.10 and the cliff did
    not move: the brown is in the MAP and COLOR_0 only multiplies it, so a 10 % push
    against the smallest channel is nothing.  r x0.66 / b x1.62 is what it took.

THE RUNTIME CONTRACT.  Every mesh here is `veg_`, which play3d.html removes from
collision entirely (`noStand`) — 113,924 triangles of grass that BLOCKED the player
would be a far worse defect than the flatness this pass exists to fix.  Verify that
in the ENGINE (tools/walk_engine_gate.mjs), never in the file.

COORDINATES.  The probe works in RUNTIME space (+x east, +y up, +z south) and so does
everything below, converting to Blender (x, -z, y) only at the moment a vertex is
written.  The map [x, y, z]_rt -> [x, -z, y]_bl is a proper rotation, so handedness
and normals carry across unchanged.
"""
import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import overworld_build as B

# ---------------------------------------------------------------------------
# THE PROBE'S PRNG, BIT FOR BIT.  Reproduced rather than replaced so the ported
# placement IS the placement that was looked at and decided on; a different
# stream would be a different picture with the same statistics, and the counts
# would stop being a port check.
# ---------------------------------------------------------------------------
_M32 = 0xFFFFFFFF


def _imul(a, b):
    return (a * b) & _M32


def rng(seed):
    """mulberry32, matching land.js's `rng()` exactly (JS `|0`/`>>>` on 32 bits)."""
    state = [seed & _M32]

    def nxt():
        a = (state[0] + 0x6D2B79F5) & _M32
        state[0] = a
        t = _imul(a ^ (a >> 15), 1 | a)
        t = ((t + _imul(t ^ (t >> 7), 61 | t)) & _M32) ^ t
        return ((t ^ (t >> 14)) & _M32) / 4294967296.0

    return nxt


def h2(x, y, s):
    n = math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453
    return n - math.floor(n)


def vnoise(x, y, cell, s):
    """Deterministic value noise on a lattice — no random() anywhere in a builder."""
    fx, fy = x / cell, y / cell
    ix, iy = math.floor(fx), math.floor(fy)
    tx, ty = fx - ix, fy - iy
    sx = tx * tx * (3 - 2 * tx)
    sy = ty * ty * (3 - 2 * ty)
    a = h2(ix, iy, s)
    b = h2(ix + 1, iy, s)
    c = h2(ix, iy + 1, s)
    d = h2(ix + 1, iy + 1, s)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy


def _jsround(v):
    """JS Math.round: halves go UP, not to even (python's round() is bankers')."""
    return int(math.floor(v + 0.5))


# ---------------------------------------------------------------------------
# THE TERRAIN SAMPLER — the probe's `T`, against the ACTUAL built triangles.
# ---------------------------------------------------------------------------
# It answers two questions in one lookup and the second is the one the reference
# frames are about: what is the SURFACE here (grass / dry / rock), so a transition
# can be found without any zone at all.  The hard grass->sand cut at the Emberbrook
# gate is a MATERIAL SLOT boundary, not a zone boundary — the zone raster calls both
# sides `meadow` and cannot see it.
class Terrain:
    KIND = {0: 1, 1: 2, 2: 3}          # slot -> the probe's kind numbering

    def __init__(self, ground):
        me = ground.data
        nsides = np.zeros(len(me.polygons), dtype=np.int32)
        me.polygons.foreach_get("loop_total", nsides)
        if not (nsides == 3).all():
            # BVHTree.FromPolygons splits a quad into two triangles and the hit
            # index stops mapping 1:1 onto polygons — which would silently return
            # the WRONG surface kind rather than fail.
            raise RuntimeError("valley_land: terrain is not all triangles (%d n-gons)"
                               % int((nsides != 3).sum()))
        mw = ground.matrix_world
        verts = [tuple(mw @ v.co) for v in me.vertices]
        polys = [tuple(p.vertices) for p in me.polygons]
        self.bvh = BVHTree.FromPolygons(verts, polys, all_triangles=True)
        mi = np.zeros(len(me.polygons), dtype=np.int32)
        me.polygons.foreach_get("material_index", mi)
        self.kind = np.array([self.KIND.get(int(k), 1) for k in mi], dtype=np.int32)
        self._down = Vector((0.0, 0.0, -1.0))

    def at(self, x, z):
        """Highest ground surface under RUNTIME (x, z) -> (height, kind) or None."""
        hit = self.bvh.ray_cast(Vector((x, -z, 400.0)), self._down)
        if hit[0] is None:
            return None
        return (hit[0].z, int(self.kind[hit[2]]))


def zone_at(zg, x, z):
    """The zone raster as a MASK, at RUNTIME (x, z).  Same indexing as zones.json."""
    c = int(math.floor((x - zg.origin[0]) / zg.cell))
    r = int(math.floor((z - zg.origin[1]) / zg.cell))
    if c < 0 or r < 0 or c >= zg.cols or r >= zg.rows:
        return -1
    return int(zg.idx[c, r])


# ===========================================================================
# L3 — THE SURFACE.  COLOR_0 only, +0 triangles.
# ===========================================================================
# "Improve the quality of our existing stuff" taken literally: the terrain we
# already have is the wrong colour and has no variation.  Three measured faults,
# three edits, no geometry.
#   (a) the grass is DARKER than the rock (L 0.383 vs 0.502) and barely green
#       (G-R = +0.047).  In every reference the biggest bright area is lit ground
#       and the rock is the mid value.  Lift and green the grass.
#   (b) the rock is warm-neutral, so the frame has no cool anywhere and 44-59 % of
#       coloured pixels sit in one 30-degree hue bin (references: 32-43 %).  Cool
#       it, and give it BEDDING — a banding in world height, which is what strata
#       is — plus a slow drift so no two faces of a wall share a value.
#   (c) every transition is a CUT.  A vertex near a surface change is dragged
#       toward the other surface's tone through a NOISY threshold, so the line goes
#       ragged instead of vector.  THE HONEST LIMIT: the terrain lattice is 1.6 m,
#       so this buys a 1.6-3.2 m ragged seam and NOT a true blend — the textures
#       still change abruptly underneath it.
# R11 — VALUE AND CHROMA, THE TENTH CRITIC'S NAMED LARGEST GAP.  Three asks land
# here and nowhere else, because they are all the ground's own albedo and no post
# pass can undo an albedo without also undoing the light on it:
#   * "re-target the greens OFF YELLOW."  The grass recipe multiplied b by 0.70
#     against g by 1.14 — a b:g of 0.61, which is chartreuse by construction.  It
#     is 0.86 : 1.06 now (b:g 0.81) and the hue is a green again.
#   * "pull global chroma back 15-20%" and "darken and desaturate the ground plane
#     so the orange roofs separate from it."  grass_gain 1.34 -> 1.08, dry 1.16 ->
#     0.84.  L3 originally lifted grass 0.383 -> 0.638 to answer "the grass was
#     darker than the rock"; it overshot into "nothing in the frame is dark."
#   * "the tan slope reads as a missing material assignment — flat untextured sand."
#     It is not missing: SIM.pick returns ground_valley_2 (the DRY slot) on both
#     sides of that boundary.  What is missing is VARIATION — the dry recipe's
#     noise amplitude was 0.24-0.34 against grass's 0.30-0.40 on a gain that made
#     it the brightest thing in the frame, so it clipped flat.  Amplitude doubled,
#     gain cut, and the seam band widened (2.1 -> 3.2 u probe, 0.30 -> 0.42 depth)
#     so the boundary is ragged over 3 m instead of hard over 1.
# The ROCK's mean is deliberately unchanged (0.72 + bed*0.52 and 0.62 + bed*0.72
# both average 0.98): the gorge cliff needed value STRUCTURE, not a darker cliff —
# its L05 was already 0.061 (LOOP.md R3) and taking the mean down would have made
# the frame grim rather than deep.
def surface(ground, T, grass_gain=1.08, dry_gain=0.72, rock_gain=1.16,
            rock_cool=1.0, seam=True):
    me = ground.data
    ca = me.color_attributes.get("Col")
    if ca is None:
        raise RuntimeError("valley_land.surface: ground has no COLOR_0")
    nl = len(me.loops)
    col = np.zeros(nl * 4)
    ca.data.foreach_get("color", col)
    col = col.reshape(-1, 4)

    lv = np.zeros(nl, dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(ground.matrix_world.to_4x4())
    P = co @ mw[:3, :3].T + mw[:3, 3]              # blender world, per vertex

    mi = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", mi)
    lf = _loop_face(me)
    lkind = np.array([Terrain.KIND.get(int(k), 1) for k in mi])[lf]

    lum = lambda a: 0.2126 * a[:, 0] + 0.7152 * a[:, 1] + 0.0722 * a[:, 2]
    before = {}
    for k in (1, 2, 3):
        m = lkind == k
        if m.any():
            before[k] = (float(lum(col[m][:, :3]).mean()), int(m.sum()))

    out = col.copy()
    over = 0
    for i in range(nl):
        v = P[lv[i]]
        # RUNTIME coords, which is the space the probe's recipe was solved in
        x, y, z = float(v[0]), float(v[2]), float(-v[1])
        r, g, b = float(col[i, 0]), float(col[i, 1]), float(col[i, 2])  # ALREADY LINEAR
        kind = int(lkind[i])
        nBig = vnoise(x, z, 15.0, 3.1)
        nMid = vnoise(x, z, 4.6, 8.7)
        nFine = vnoise(x, z, 1.9, 21.3)
        n = nBig * 0.52 + nMid * 0.33 + nFine * 0.15
        if kind == 1:                       # ---- GRASS -------------------------
            # R12 — THE FURTHER 25-30% OFF THE GREENS, and it had to come from here
            # because R12 also NEUTRALISED THE SKY FILL, which put chroma BACK into
            # the grass: measured on the same probe box, lit open grass went sat
            # 0.317 -> 0.398 with nothing but the fill's hue changed.  A blue fill
            # was desaturating the greens as a side effect, so the round that
            # stopped the shadows reading plum also un-did half of R11's chroma
            # ...AND THEN THE WHOLE ATTEMPT WAS WITHDRAWN, WHICH IS THE FINDING.
            # Three builds moved this line (b:g 0.81 -> 0.91 -> 1.03) and the lit
            # meadow moved 1/255 each time.  The decisive test needs no build: set
            # `ground_valley_1`'s COLOR_0.z live in the running page and read the
            # same probe box.  x1.127 -> +2/255.  x2.818 -> +14/255.  A 182% lift in
            # the ground's own albedo blue buys 13% of the screen's, so the grass
            # pixel's blue is NOT mostly albedo x light and THIS IS NOT THE KNOB
            # FOR CHROMA.  R11's numbers stand; the 25-30% green pull the twelfth
            # critic asked for is done in play3d's grade, where it demonstrably
            # lands (search THE PULL IS YELLOW-SELECTIVE).  Fourth knob in this loop
            # to be swept while disconnected — the live-attribute test above is a
            # minute and should come FIRST next time.
            r, g, b = r * (0.80 + n * 0.28), g * (1.06 + n * 0.34), b * (0.86 + n * 0.34)
            s = grass_gain * (0.80 + n * 0.46)
        elif kind == 2:                     # ---- DRY / SAND --------------------
            r, g, b = r * (0.84 + n * 0.36), g * (0.88 + n * 0.42), b * (0.98 + n * 0.58)
            s = dry_gain * (0.86 + n * 0.32)
        else:                               # ---- ROCK --------------------------
            bed = 0.5 + 0.5 * math.sin(y * 1.55 + vnoise(x, z, 22.0, 5.5) * 4.2)
            band = 0.62 + bed * 0.72
            k = rock_cool
            r, g, b = (r * (1 - 0.34 * k + n * 0.14), g * (1 - 0.10 * k + n * 0.14),
                       b * (1 + 0.62 * k + n * 0.20))
            s = rock_gain * band * (0.86 + n * 0.30)
        r, g, b = r * s, g * s, b * s
        if seam:
            other = tot = 0
            for j in range(6):
                a = j * math.pi / 3
                sp = T.at(x + math.cos(a) * 3.2, z + math.sin(a) * 3.2)
                if sp is None:
                    continue
                tot += 1
                if sp[1] != kind:
                    other += 1
            if tot and other:
                wr = other / tot
                # a smooth ramp is just a softer vector edge; reference seams are RAGGED
                t = max(0.0, min(1.0, wr * 1.5 - 0.25 + (nFine - 0.5) * 0.85))
                dark = 0.72 + nMid * 0.30
                m = 1 - t * 0.42 * dark
                r, g, b = r * m, g * m, b * m
        if r > 1.0 or g > 1.0 or b > 1.0:
            over += 1
        out[i, 0], out[i, 1], out[i, 2] = min(r, 1.0), min(g, 1.0), min(b, 1.0)

    ca.data.foreach_set("color", out.ravel())
    me.color_attributes.active_color = ca
    me.color_attributes.render_color_index = list(me.color_attributes).index(ca)
    stats = {}
    names = {1: "grass", 2: "dry", 3: "rock"}
    parts = []
    for k in (1, 2, 3):
        if k not in before:
            continue
        m = lkind == k
        a = float(lum(out[m][:, :3]).mean())
        stats[names[k]] = dict(L0=round(before[k][0], 3), L1=round(a, 3), n=before[k][1])
        parts.append("%s L %.3f->%.3f (%d verts)" % (names[k], before[k][0], a, before[k][1]))
    # THE CLIP IS A REAL DIFFERENCE FROM THE PROBE, so it is reported rather than
    # hidden: three.js leaves a COLOR_0 over 1.0 alone, glTF does not promise to.
    print("  L3 surface — COLOR_0 only, +0 triangles — %s  [%d/%d corners clipped at 1.0]"
          % (" | ".join(parts), over, nl))
    stats["clipped"] = over
    stats["corners"] = nl
    return stats


def _loop_face(me):
    lt = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("loop_total", lt)
    return np.repeat(np.arange(len(me.polygons)), lt)


# ===========================================================================
# L2 — THE GROUND IS GEOMETRY.  Detail placed ONLY where it makes an edge.
# ===========================================================================
Z_MEADOW, Z_FOREST, Z_CRAG, Z_ROAD, Z_WATER = range(5)

# R12 — THE CHARTREUSE WAS IN THE TUFTS, NOT IN THE GROUND.  "Pull green
# saturation down a further 25-30% in A" (twelfth blind critic).  Two builds
# were spent moving `surface()`'s grass multiplier — b:g 0.52 -> 0.66 on the
# terrain's own COLOR_0, verified IN THE EXPORTED GLB — and the meadow moved
# 1/255.  L2 puts 17,908 tufts and 771 flowers over exactly the ground the
# probe box was sampling, so the pixels are these five hexes and the terrain
# underneath them is barely visible: at 8fa845 the palette's own b:g is 0.41.
# THE GROUND UNDER A GRASS SCATTER IS NOT THE GRASS.  Each entry keeps its hue
# and its max channel and has its MIN (blue) lifted so HSV saturation drops
# ~27%: .589 -> .429, .597 -> .436, .525 -> .383, .576 -> .420, .511 -> .373.
PAL = ["8fa860", "7d9a57", "a8b771", "6b844d", "bcae76"]
PALDRY = ["b2a86a", "a39a5e", "c4b878"]
FLOW = ["f2ead6", "e8c85a", "d98fae", "f2ead6", "c9d8ee"]


def _lin(hexes):
    return [B.srgb(h) for h in hexes]


# ---- THE TUFT.  Six blades, ONE TRIANGLE EACH. ----------------------------
# A blade is a triangle whose apex leans.  Six fanned = 6 triangles, an eighth of
# what one lobed bush costs.  THE POINT OF A TUFT IS ITS SILHOUETTE, and a
# silhouette is the cheapest thing in a renderer.  The normals are AUTHORED
# (leaning out and up), not the facet normals: a near-vertical triangle shaded by
# its own face normal is edge-on to the key and goes black.
def _tuft_geo(nb=6, seed=91):
    r = rng(seed)
    pos, nrm = [], []
    for i in range(nb):
        a = (i / nb) * math.pi * 2 + r() * 0.9
        w = 0.055 + r() * 0.035
        h = 0.62 + r() * 0.55
        lean = 0.20 + r() * 0.34
        ca, sa = math.cos(a), math.sin(a)
        bx, bz = ca * 0.055, sa * 0.055
        pos += [(bx - sa * w, 0.0, bz + ca * w), (bx + sa * w, 0.0, bz - ca * w),
                (bx + ca * lean, h, bz + sa * lean)]
        nrm += [(-sa, 0.55, ca)] * 3
    return np.array(pos), np.array(nrm)


# ---- THE CLUMP.  A squashed low icosahedron: a bush at a rock's foot. ------
_ICO_T = (1 + math.sqrt(5)) / 2
_ICO_V = [(-1, _ICO_T, 0), (1, _ICO_T, 0), (-1, -_ICO_T, 0), (1, -_ICO_T, 0),
          (0, -1, _ICO_T), (0, 1, _ICO_T), (0, -1, -_ICO_T), (0, 1, -_ICO_T),
          (_ICO_T, 0, -1), (_ICO_T, 0, 1), (-_ICO_T, 0, -1), (-_ICO_T, 0, 1)]
_ICO_F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
          (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
          (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
          (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]


def _clump_geo():
    # R11: THE SQUASH WAS 0.62 AND IT MADE PANCAKES.  A unit clump 1.0 wide and
    # 0.62 tall, then scaled w in 0.75..1.80 against h in 0.45..1.20, lands at a
    # mean 1.28 x 0.51 — aspect 0.40.  The tenth blind critic's first sentence
    # about the gorge frame was "flat green discs, pancakes lying on the ground,
    # not bushes; the first thing my eye caught."  Measured, not argued: SIM.pick
    # at three of them returns veg_land_clumps with a first-hit normal of
    # (-0.06, 0.99, -0.14) — a horizontal facet.  0.94 keeps the low-poly facet
    # read (which IS the style) and gives the thing a height.
    pos, uv = [], []
    for f in _ICO_F:
        for i in f:
            v = np.array(_ICO_V[i], dtype=float)
            v = v / np.linalg.norm(v) * 0.5
            pos.append((v[0], v[1] * 0.94 + 0.47, v[2]))
    for k in range(len(pos)):
        uv.append((0.42 + (k % 3) * 0.03, 0.44 + ((k // 3) % 3) * 0.03))
    return np.array(pos), np.array(uv)


# ---- THE FLOWER.  Two triangles, in CLUMPS never scattered. ---------------
def _flower_geo():
    s, h = 0.5, 1.0
    pos = [(-s, h - 0.35, 0), (s, h - 0.35, 0), (0, h, 0),
           (0, h - 0.35, -s), (0, h - 0.35, s), (0, h, 0)]
    nrm = [(0, 1, 0)] * 6
    return np.array(pos, dtype=float), np.array(nrm, dtype=float)


def _rot(tilt, yaw):
    """three.js Euler('XYZ') with z=0, i.e. Rx(tilt) @ Ry(yaw) — the probe's order."""
    ct, st = math.cos(tilt), math.sin(tilt)
    cy, sy = math.cos(yaw), math.sin(yaw)
    Rx = np.array([[1, 0, 0], [0, ct, -st], [0, st, ct]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return Rx @ Ry


def _emit(rows, gpos, gnrm, guv):
    """Bake instance rows into one runtime-space soup, then convert to Blender."""
    npv = len(gpos)
    V = np.empty((len(rows) * npv, 3))
    N = np.empty((len(rows) * npv, 3)) if gnrm is not None else None
    C = np.empty((len(rows) * npv, 3))
    U = np.empty((len(rows) * npv, 2)) if guv is not None else None
    for i, row in enumerate(rows):
        R = _rot(row["tilt"], row["yaw"])
        s = np.array([row["w"], row["h"], row["w"]])
        p = np.array([row["x"], row["y"], row["z"]])
        o = i * npv
        V[o:o + npv] = (gpos * s) @ R.T + p
        if N is not None:
            # three.js's normalMatrix on a non-uniform scale: n' ~ R @ (n / s)
            m = (gnrm / s) @ R.T
            N[o:o + npv] = m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-9)
        C[o:o + npv] = row["c"]
        if U is not None:
            U[o:o + npv] = guv
    # runtime (x, y, z) -> blender (x, -z, y)
    Vb = np.stack([V[:, 0], -V[:, 2], V[:, 1]], axis=1)
    Nb = None if N is None else np.stack([N[:, 0], -N[:, 2], N[:, 1]], axis=1)
    return Vb, Nb, C, U


def _mesh(col, name, V, N, C, U, mat, smooth):
    me = bpy.data.meshes.new(name)
    faces = np.arange(len(V), dtype=np.int32).reshape(-1, 3)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in faces])
    if U is not None:
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", U.ravel())
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    d = np.ones((len(V), 4))
    d[:, :3] = np.clip(C, 0.0, 1.0)
    ca.data.foreach_set("color", d.ravel())
    me.color_attributes.active_color = ca
    me.color_attributes.render_color_index = list(me.color_attributes).index(ca)
    me.materials.append(mat)
    me.polygons.foreach_set("use_smooth", [smooth] * len(me.polygons))
    if N is not None:
        # AUTHORED NORMALS, not facet ones — see _tuft_geo.  Blender <4.1 needs
        # use_auto_smooth first; 4.1+ dropped the flag and honours the custom set.
        if hasattr(me, "use_auto_smooth"):
            me.use_auto_smooth = True
        me.normals_split_custom_set([tuple(N[i]) for i in range(len(N))])
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def tufts(col, ground, zg, mats, step=1.0, dens=9.0, band=2.6, maxslope=0.85,
          x0=-75.0, x1=60.0, z0=-50.0, z1=85.0, flower_clumps=900, T=None):
    """L2 — the seam scatter.  Returns (objects, stats)."""
    T = T or Terrain(ground)
    r = rng(4711)
    pal = _lin(PAL)
    paldry = _lin(PALDRY)
    flow = _lin(FLOW)
    tuft_rows, clump_rows, flower_rows = [], [], []
    edge_sites = 0

    # The corridor the player actually walks, plus a margin.  Sampling the whole
    # 280x200 u tile would spend the entire budget on ground no camera ever sees —
    # which is the shipped bundle's own mistake (38,740 tris of tree field, ZERO
    # within 15 m of the road at all seven sampled points).
    x = x0
    while x <= x1:
        z = z0
        while z <= z1:
            zz = z
            z += step
            jx = x + (r() - 0.5) * step * 1.5
            jz = zz + (r() - 0.5) * step * 1.5
            here = T.at(jx, jz)
            if here is None:
                continue
            zt = zone_at(zg, jx, jz)
            if zt == Z_WATER:
                continue
            # ---- is this an EDGE?  probe the surface kind and the zone on a ring
            diff = near = rock_near = road_near = 0
            for k in range(8):
                a = k * math.pi / 4
                for d in (band * 0.45, band):
                    px, pz = jx + math.cos(a) * d, jz + math.sin(a) * d
                    s = T.at(px, pz)
                    if s is None:
                        continue
                    near += 1
                    if s[1] != here[1]:
                        diff += 1
                        if s[1] == 3:
                            rock_near += 1
                    if zone_at(zg, px, pz) == Z_ROAD and zt != Z_ROAD:
                        road_near += 1
            if not near:
                continue
            edge, road = diff / near, road_near / near
            # WEIGHT IS A SEAM WEIGHT AND NOTHING ELSE.  This is the whole
            # candidate: grass geometry stands where the ground CHANGES and nowhere
            # else.  A uniform meadow scatter is the carpet that was refused, and a
            # carpet is also the one thing that costs real triangles.
            wgt = max(edge * 1.9, road * 2.1)
            # the road ribbon itself stays bare — a path with grass ON it is a path
            # nobody uses, and the walk network is law
            if zt == Z_ROAD:
                wgt *= 0.12
            # ONE ration away from the seams, along the walked verge only, so the
            # ground the player is looking at is not bald between edges
            if road > 0.02 or edge > 0.02:
                wgt = max(wgt, 0.16)
            wgt = min(1.0, wgt)
            if wgt < 0.02:
                continue
            edge_sites += 1
            p = paldry if here[1] == 2 else pal
            # ---- SCALE ONE: the blades --------------------------------------
            n = _jsround(wgt * dens * step * step * (0.55 + r() * 0.9))
            for _ in range(n):
                px = jx + (r() - 0.5) * step * 1.4
                pz = jz + (r() - 0.5) * step * 1.4
                s = T.at(px, pz)
                if s is None:
                    continue
                if zone_at(zg, px, pz) == Z_WATER:
                    continue
                # SLOPE GATE — see the module docstring
                sa_ = T.at(px + 0.7, pz)
                sb_ = T.at(px - 0.7, pz)
                sc_ = T.at(px, pz + 0.7)
                sd_ = T.at(px, pz - 0.7)
                if sa_ is None or sb_ is None or sc_ is None or sd_ is None:
                    continue
                grad = math.hypot(sa_[0] - sb_[0], sc_[0] - sd_[0]) / 1.4
                if grad > maxslope:
                    continue
                c = np.array(p[int(r() * len(p))])
                c = c * (0.78 + r() * 0.52)          # a real value spread per tuft
                hh = (0.13 if s[1] == 3 else 0.15 if s[1] == 2 else 0.24) * (0.62 + r() * 0.90)
                tuft_rows.append(dict(x=px, y=s[0] - 0.02, z=pz, w=0.34 + r() * 0.30,
                                      h=hh, yaw=r() * 6.28, tilt=(r() - 0.5) * 0.26, c=c))
            # ---- SCALE TWO: a shrub clump where grass meets ROCK -------------
            # THE COLOUR MULTIPLIER IS AGAINST THE MAP'S OWN MEAN, NOT AGAINST 1.0.
            # ow_valley_bushcore ships COLOR_0 at L 0.311; instance-colouring it at
            # 0.5-0.8 produced faceted BLACK BOULDERS at every rock foot.
            if rock_near > 3 and r() < 0.24:
                cc = np.array(pal[int(r() * len(pal))]) * (1.9 + r() * 0.9)
                # R11: HEIGHT IS DRAWN FROM THE WIDTH, not independently — two
                # independent draws is how a bush becomes a puddle on the unlucky
                # half of them.  The PRNG STREAM IS PRESERVED EXACTLY (same seven
                # calls in the same order), because the port check in this module's
                # docstring is a count check and a different stream is a different
                # picture with the same statistics.
                _cx = jx + (r() - 0.5) * 0.9
                _cz = jz + (r() - 0.5) * 0.9
                _cw = 0.62 + r() * 0.72
                _ch = _cw * (0.86 + r() * 0.46)
                clump_rows.append(dict(x=_cx, y=here[0] - 0.14, z=_cz, w=_cw,
                                       h=_ch, yaw=r() * 6.28, tilt=0.0, c=cc))
        x += step

    # ---- SCALE THREE: FLOWERS IN CLUMPS, never scattered -------------------
    placed = 0
    for _ in range(flower_clumps):
        cx = x0 + r() * (x1 - x0)
        cz = z0 + r() * (z1 - z0)
        if zone_at(zg, cx, cz) != Z_MEADOW:
            continue
        s = T.at(cx, cz)
        if s is None or s[1] != 1:
            continue
        # a clump the player never walks past is a triangle spent on nobody
        seen = False
        k = 0
        while k < 10 and not seen:
            a = k * 0.628
            for d in (6, 12, 18):
                if zone_at(zg, cx + math.cos(a) * d, cz + math.sin(a) * d) == Z_ROAD:
                    seen = True
                    break
            k += 1
        if not seen:
            continue
        placed += 1
        cc = flow[int(r() * len(flow))]
        n = 6 + int(r() * 9)
        rad = 0.55 + r() * 1.35
        for _ in range(n):
            a = r() * 6.28
            d = math.sqrt(r()) * rad
            px, pz = cx + math.cos(a) * d, cz + math.sin(a) * d
            p_ = T.at(px, pz)
            if p_ is None:
                continue
            flower_rows.append(dict(x=px, y=p_[0], z=pz, w=0.055 + r() * 0.045,
                                    h=0.13 + r() * 0.10, yaw=r() * 6.28,
                                    tilt=(r() - 0.5) * 0.3, c=np.array(cc)))

    # ---- materials.  ow_f2_matte is the one shipped material with NO map, so a
    # tuft's colour is entirely its own; the "flat colour beside a mapped crag
    # reads as pale plastic" finding is about metre-scale SOLIDS, and a 0.25 m
    # blade has no room for a texture to read in.
    m_tuft = bpy.data.materials.get("ow_f2_tuft") or B.new_mat("ow_f2_tuft", rough=0.95)
    m_flower = bpy.data.materials.get("ow_f2_flower") or B.new_mat("ow_f2_flower", rough=0.80)
    m_clump = (bpy.data.materials.get("ow_valley_bushcore")
               or mats.get("matte") or m_tuft)

    objs = []
    tris = 0
    gp, gn = _tuft_geo()
    V, N, C, _ = _emit(tuft_rows, gp, gn, None)
    objs.append(_mesh(col, "veg_land_tufts", V, N, C, None, m_tuft, True))
    tris += len(V) // 3
    if clump_rows:
        gp, guv = _clump_geo()
        V, _, C, U = _emit(clump_rows, gp, None, guv)
        objs.append(_mesh(col, "veg_land_clumps", V, None, C, U, m_clump, False))
        tris += len(V) // 3
    if flower_rows:
        gp, gn = _flower_geo()
        V, N, C, _ = _emit(flower_rows, gp, gn, None)
        objs.append(_mesh(col, "veg_land_flowers", V, N, C, None, m_flower, True))
        tris += len(V) // 3

    stats = dict(tufts=len(tuft_rows), seam_cells=edge_sites, clumps=len(clump_rows),
                 flowers=len(flower_rows), patches=placed, tris=tris)
    print("  L2 ground-is-geometry — %d tufts (6 tris each) at %d seam cells + %d clumps "
          "+ %d flowers in %d clumps, %d triangles in, 0 out"
          % (stats["tufts"], stats["seam_cells"], stats["clumps"], stats["flowers"],
             stats["patches"], stats["tris"]))
    return objs, stats
