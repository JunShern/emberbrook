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
otherwise.  Both functions print theirs.  TWO DELIBERATE DIVERGENCES ARE NOW ON THE
RECORD, so the check is against these and not against the probe's originals: R14 lets
a tuft stand at a CLIFF LIP (the tight re-probe in `tufts`, which admits sites the
+-0.7 u slope gate rejected) and R14 warps the grass/rock slot boundary
(`overworld3_build.LIP_WARP`), which moves the seam cells the scatter keys off.  Both
change the counts on purpose; a change nobody wrote down would still be a port bug.

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

import bushlang as BL
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
#
# R14 — A SECOND ROCK TONE AND DARKENED CREVICES (the fourteenth critic's single
# highest-value change: "moderately cheap — a material pass, not new models").  Three
# edits, all still COLOR_0 and still +0 triangles:
#
#   (d) THE MOTTLE WAS A PLAN-VIEW NOISE ON A VERTICAL WALL.  `n` is
#       vnoise(x, z, ...) — the two RUNTIME GROUND axes — so it is CONSTANT down any
#       vertical column.  On a 30 u gorge face the only thing that varied with height
#       was `bed`, and that is most of why the wall reads as "one flat tone" however
#       much amplitude the noise is given.  The rock branch now samples a SLANTED
#       section (x + y*k, z - y*k), so the same noise varies down the face too.
#   (e) A SECOND TONE, AND IT HAS TO BE THE COOL ONE.  The rock had ONE hue: a fixed
#       cool multiplier with a value band on it.  The first attempt paired it with a
#       warm ochre AT HELD LUMINANCE, on the theory that a hue move should not have to
#       spend value — and tools/ow_probe/framespread.py said that made the cliff WORSE
#       on the only axis that was short.  Over the gorge cliff box (600,200)-(1390,520),
#       r13 -> that attempt: hue SD 13.4 -> 11.5 deg, the RED sector 78% -> 90%, hue
#       sectors holding >= 8% of the box 2 -> 1.  AN OCHRE BESIDE A WARM ROCK UNDER A
#       WARM KEY IS NOT A SECOND TONE, IT IS MORE OF THE FIRST ONE.  The references
#       hold a fifth of their frame in the cyan-blue sector and we hold none of it, so
#       the second tone is a cool blue-grey stratum — and it is allowed to be DARKER,
#       because COLOR_0 can only multiply: cool over a warm albedo means taking R and G
#       down and there is no version of this that holds luminance.  That is not a cost
#       here, it is the other half of the same ask — 19% between the two bands is value
#       structure the cliff also did not have (its 5-95 range was 0.307 against the
#       references' whole-frame 0.44-0.52).
#   (f) CREVICE OCCLUSION, from the mesh's OWN curvature.  Per vertex, the mean of
#       dot(normalise(neighbour - v), n_v) over its incident edges: positive where the
#       surround sits above the tangent plane, i.e. inside a fissure.  It costs one
#       pass over me.edges and no raycasts, and it is the cheap half of what an AO
#       bake would buy — the crag fan vertices, which are the crevices, get it hardest.
#       AND COLOR_0 HAS A CEILING OF 1.0 THAT THE ROCK IS ALREADY NEAR.  The first
#       cool triple was (0.50, 0.78, 1.75) and it did not read: `terrain_pbr_f2` has
#       already multiplied the rock slot by its own albedo-mean gain of 1.81, so a blue
#       of 1.75 on top CLIPS (9,348 of 160,656 corners at 1.0) and the band's colour is
#       thrown away in the clamp — the cliff came back 88% red-sector, no better than
#       before.  A multiply-only channel cannot be pushed up; the cool band is made by
#       taking R and G DOWN, and 1.42 is the most blue that survives the ceiling.
ROCK_WARM = (1.100, 0.940, 0.720)   # ochre bed       L 0.958
ROCK_COOL = (0.420, 0.660, 1.420)   # blue-grey bed   L 0.664   (R13's single tone: 0.901)
CAV_REF = 0.30                      # curvature that counts as a full crevice
CAV_ROCK = 0.58                     # ... and how far down a full crevice goes
CAV_SOFT = 0.16                     # ... on grass / dry, where it only wants a hint


def _cavity(me, P):
    """Per-vertex concavity in 0..1 from the mesh's own edges and normals."""
    ev = np.zeros(len(me.edges) * 2, dtype=np.int32)
    me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(-1, 2)
    nrm = np.zeros(len(me.vertices) * 3)
    try:                                        # Blender 4.1+ drops vertices.normal
        me.vertex_normals.foreach_get("vector", nrm)
    except (AttributeError, TypeError):
        me.vertices.foreach_get("normal", nrm)
    nrm = nrm.reshape(-1, 3)
    d = P[ev[:, 1]] - P[ev[:, 0]]
    d = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    acc = np.zeros(len(P))
    cnt = np.zeros(len(P))
    np.add.at(acc, ev[:, 0], (d * nrm[ev[:, 0]]).sum(1))
    np.add.at(acc, ev[:, 1], (-d * nrm[ev[:, 1]]).sum(1))
    np.add.at(cnt, ev[:, 0], 1.0)
    np.add.at(cnt, ev[:, 1], 1.0)
    return np.clip(acc / np.maximum(cnt, 1.0) / CAV_REF, 0.0, 1.0)


def surface(ground, T, grass_gain=1.08, dry_gain=0.72, rock_gain=1.28,
            rock_cool=1.0, seam=True):
    # rock_gain 1.16 -> 1.28 pays for the cool band, and only for it: splitting one
    # tone into a 0.958/0.664 pair takes the class MEAN down 7% by construction, and
    # R13's ruling that the gorge needed structure and NOT a darker cliff still holds.
    # The gate on the number is the printed class mean (R13 shipped rock L 0.543).
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
    cav = _cavity(me, P)[lv]                   # per-loop crevice weight, 0..1

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
            # (d) a SLANTED section, so the mottle varies DOWN the wall as well as
            # across it.  vnoise(x, z, ..) alone is one value per vertical column.
            rB = vnoise(x + y * 0.62, z - y * 0.48, 17.0, 4.4)
            rM = vnoise(x - y * 0.55, z + y * 0.71, 5.2, 9.9)
            rF = vnoise(x + y * 0.83, z + y * 0.36, 2.1, 23.7)
            n = rB * 0.50 + rM * 0.34 + rF * 0.16
            bedq = y * 1.55 + vnoise(x, z, 22.0, 5.5) * 4.2
            bed = 0.5 + 0.5 * math.sin(bedq)
            band = 0.62 + bed * 0.72
            # (e) the second tone: a slow field, plus the bed's own parity so
            # neighbouring strata differ in HUE and not only in value
            # THE BANDS HAVE TO REACH THE ENDS.  A tone that only ever sits near the
            # middle of the mix is one averaged rock again; the parity term is weighted
            # so `tone` clips at both ends over most of a wall, which is what makes a
            # stratum a stratum rather than a gradient.
            par = 0.5 + 0.5 * math.sin(bedq * 0.5 + 1.1)
            tone = min(1.0, max(0.0, 0.5 + 1.60 * (par - 0.5) + 0.90 * (rB - 0.5)))
            k = rock_cool
            mr = ROCK_COOL[0] + (ROCK_WARM[0] - ROCK_COOL[0]) * tone
            mg = ROCK_COOL[1] + (ROCK_WARM[1] - ROCK_COOL[1]) * tone
            mb = ROCK_COOL[2] + (ROCK_WARM[2] - ROCK_COOL[2]) * tone
            r, g, b = (r * (1 + (mr - 1) * k + n * 0.14),
                       g * (1 + (mg - 1) * k + n * 0.14),
                       b * (1 + (mb - 1) * k + n * 0.20))
            s = rock_gain * band * (0.86 + n * 0.30)
        # (f) the crevices go down.  A cavity term costs no triangles and is the
        # half of an AO bake the eye actually reads on a fissured face.
        s = s * (1.0 - (CAV_ROCK if kind == 3 else CAV_SOFT) * float(cav[i]))
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
    rk = lkind == 3
    if rk.any():
        rc = out[rk][:, :3]
        mx = rc.max(1)
        mn = rc.min(1)
        sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
        # the hue spread is the whole point of the second tone; report it beside the
        # cavity so "did the material pass land" is a number and not an opinion
        print("  L3 rock — cavity p50 %.3f p95 %.3f (%.1f%% of rock corners > 0.25) | "
              "COLOR_0 r/b p10 %.3f p90 %.3f | sat mean %.3f sd %.3f"
              % (float(np.percentile(cav[rk], 50)), float(np.percentile(cav[rk], 95)),
                 100.0 * float((cav[rk] > 0.25).mean()),
                 float(np.percentile(rc[:, 0] / np.maximum(rc[:, 2], 1e-6), 10)),
                 float(np.percentile(rc[:, 0] / np.maximum(rc[:, 2], 1e-6), 90)),
                 float(sat.mean()), float(sat.std())))
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
# R22 — THE ROAD VERGE.  The seam the user named, as a MATERIAL band.
# ===========================================================================
# "the main road is also too 'distinct' from the grass around it in a way that is
# unrealistic, the cuts are too abrupt."  Measured on the gate plate: the ribbon's
# edge is a ONE-TO-TWO PIXEL step in value with nothing either side of it.  It has
# to be, by construction — `walk_road` carried ONE flat COLOR_0 on every vertex
# (overworld3_build.terrain_pbr_f2 writes the tint 8e7a63 to the whole mesh) and
# met a terrain whose own COLOR_0 knows nothing about it.  Two flat fields meeting
# on a polygon edge IS a cut; no amount of fringe scatter hides one, which is
# exactly what f1 carried forward and f2's pads re-learned.
#
# THE FIX IS THE ONE THE REFERENCES SHOW: the dirt feathers OUT into the grass and
# the grass creeps IN over the dirt, so neither side owns the edge.  Both sides
# ramp to the SAME 50/50 mixture AT the seam and back to their own colour away
# from it — which makes the step zero by construction rather than by tuning, and
# is why there are two mix numbers and not one.
#
# IT IS COLOUR ONLY.  No new material (a second material on the road would be a
# second draw call and a second seam), no alpha (an alpha-blended verge sorts, and
# a stipple at this pixel size reads as noise), no geometry on the terrain side at
# all — the ground's own ~0.8 u vertex spacing already gives a 1.4 u band two
# vertices to interpolate across.  The ROAD side needed its lanes (see
# valley_build.ROAD_LANES) because a 2-across strip has no interior vertex to
# ramp from.
#
# THE TWO MESHES ARE IN DIFFERENT COLOUR NORMALISATIONS and this is the trap that
# would have made the band a new seam instead of a cure.  glTF renders
# baseColorTexture * COLOR_0, and pbr_mat pre-divides each class colour by ITS OWN
# texture's albedo mean — so COLOR_0 0.6 on the road and COLOR_0 0.6 on the grass
# are NOT the same brightness on screen.  The blend is therefore done in PERCEIVED
# space (albedo_mean * COLOR_0) and converted back per mesh.
VERGE_GROUND = 1.40      # u the road's colour reaches OUT over the terrain
VERGE_ROAD = 0.34        # u the terrain's colour reaches IN over the ribbon
VERGE_MIX = 0.52         # the mixture both sides carry AT the seam
VERGE_RAG = 0.55         # u the band's own edge wanders, so it is worn not drawn


def _vnoise_v(x, y, cell, s):
    """vnoise(), vectorised.  Identical arithmetic — checked against the scalar
    on the build's own assert — because a second noise implementation that drifts
    from the first is a bug nobody can see."""
    fx, fy = np.asarray(x, float) / cell, np.asarray(y, float) / cell
    ix, iy = np.floor(fx), np.floor(fy)
    tx, ty = fx - ix, fy - iy
    sx = tx * tx * (3 - 2 * tx)
    sy = ty * ty * (3 - 2 * ty)
    h = lambda a, b: (lambda n: n - np.floor(n))(
        np.sin(a * 127.1 + b * 311.7 + s * 74.7) * 43758.5453)
    a_, b_ = h(ix, iy), h(ix + 1, iy)
    c_, d_ = h(ix, iy + 1), h(ix + 1, iy + 1)
    return (a_ * (1 - sx) + b_ * sx) * (1 - sy) + (c_ * (1 - sx) + d_ * sx) * sy


def _perceived(ob):
    """(mean albedo of this mesh's material, per-loop COLOR_0) — the pair a
    cross-mesh blend has to work in.  Multi-slot meshes get their per-face
    material's own mean, which is what makes the ground's three slots blend
    against the road as three different browns rather than one."""
    me = ob.data
    ca = me.color_attributes.get("Col")
    if ca is None:
        raise RuntimeError("road_verge: %s has no COLOR_0" % ob.name)
    nl = len(me.loops)
    col = np.zeros(nl * 4)
    ca.data.foreach_get("color", col)
    col = col.reshape(-1, 4)
    mi = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", mi)
    means = np.array([float(m.get("albedo_mean", 0.5)) if m else 0.5
                      for m in me.materials]) if me.materials else np.array([0.5])
    am = means[np.clip(mi, 0, len(means) - 1)][_loop_face(me)]
    return ca, col, am


def _loop_world(ob):
    """Per-loop world position, in RUNTIME axes (+x east, +y up, +z south)."""
    me = ob.data
    nl = len(me.loops)
    lv = np.zeros(nl, dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world.to_4x4())
    P = co @ mw[:3, :3].T + mw[:3, 3]
    return P[lv]                                    # BLENDER world, per loop


def _road_offset(F, hl, hr, X, Y):
    """Signed distance OUTSIDE the built ribbon edge, per query point.

    Negative on the carriageway, positive off it.  It has to be measured against
    the WOBBLED halfwidth (valley_build.road_wobble) and not against ROAD_WIDTH/2,
    or the band crosses the ribbon wherever the wobble narrowed it.
    """
    rd = F.road
    # nearest station, chunked so a 160 k x 1.6 k product never materialises
    idx = np.zeros(len(X), dtype=np.int64)
    dist = np.zeros(len(X))
    step = 8192
    for a in range(0, len(X), step):
        b = min(a + step, len(X))
        d2 = ((X[a:b, None] - rd[None, :, 0]) ** 2
              + (Y[a:b, None] - rd[None, :, 1]) ** 2)
        j = np.argmin(d2, axis=1)
        idx[a:b] = j
        dist[a:b] = np.sqrt(d2[np.arange(b - a), j])
    tg = np.gradient(rd, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    # which side: the sign of the cross product of the tangent with the offset
    dx, dy = X - rd[idx, 0], Y - rd[idx, 1]
    side = np.sign(tg[idx, 0] * dy - tg[idx, 1] * dx)
    hw = np.where(side >= 0, hr[idx], hl[idx])
    return dist - hw


# R22 — AND THE SAME CURE FOR THE TERRAIN'S OWN INTERNAL SEAMS.
# overworld3_build's header wrote the rule in round 3 and then applied it to
# exactly one boundary: "one-material-per-FACE means every slot boundary is a hard
# zigzag along the triangulation... a road apron is a COLOUR gradient (COLOR_0,
# per-vertex, smooth)".  The DIRT slot was deleted from the terrain for that reason
# and grass/dry/rock were left to cut against each other unchanged.
#
# A face can only carry ONE material, so the texture WILL switch on a polygon edge
# and no amount of warping changes that.  What the eye reads at 10 m is not the
# texture, it is the VALUE STEP — and COLOR_0 is per-vertex, so the step can be
# taken out even though the material index cannot.  Every vertex that touches more
# than one slot is set to the PERCEIVED mean of the loops meeting there, so the two
# sides are equal AT the seam and Gouraud ramps each back to its own class across
# one triangle.  On the flat that is a ~0.8 u feather; on the far crag wall, where
# the faces are metres across and the teeth were, it is proportionally wider, which
# is the right way round.
SLOT_FEATHER = 0.88      # how far to the shared mean a seam vertex goes (1 = all)


def slot_feather(ground, amt=SLOT_FEATHER):
    me = ground.data
    ca, col, am = _perceived(ground)
    nl = len(me.loops)
    lv = np.zeros(nl, dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    mi = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("material_index", mi)
    lslot = mi[_loop_face(me)]

    nv = len(me.vertices)
    mask = np.zeros(nv, dtype=np.int32)
    np.bitwise_or.at(mask, lv, (1 << lslot).astype(np.int32))
    mixed = (mask & (mask - 1)) != 0            # a vertex on more than one slot

    P = col[:, :3] * am[:, None]                # perceived albedo, per loop
    S = np.zeros((nv, 3))
    np.add.at(S, lv, P)
    N = np.zeros(nv)
    np.add.at(N, lv, 1.0)
    V = S / np.maximum(N, 1.0)[:, None]

    sel = mixed[lv]
    out = col.copy()
    blended = P[sel] * (1 - amt) + V[lv[sel]] * amt
    out[sel, :3] = np.clip(blended / np.maximum(am[sel, None], 1e-6), 0.0, 1.0)
    ca.data.foreach_set("color", out.ravel())

    lum = lambda a: 0.2126 * a[:, 0] + 0.7152 * a[:, 1] + 0.0722 * a[:, 2]
    # THE GATE IS THE STEP ACROSS THE SEAM, and it is measured PER SEAM VERTEX (the
    # spread of perceived luminance among the loops that meet there) rather than as
    # a class mean — a class mean cannot see a seam at all, which is how this one
    # survived fourteen rounds of class-mean reporting.
    def spread(Q):
        mx = np.full(nv, -1e9)
        mn = np.full(nv, 1e9)
        l_ = lum(Q)
        np.maximum.at(mx, lv, l_)
        np.minimum.at(mn, lv, l_)
        return (mx - mn)[mixed]
    Pa = P.copy()
    Pa[sel] = blended
    b, a_ = spread(P), spread(Pa)
    print("  R22 slot feather — %d seam vertices of %d (%.1f%%); step across the "
          "seam p50 %.4f -> %.4f, p95 %.4f -> %.4f, +0 triangles"
          % (int(mixed.sum()), nv, 100.0 * mixed.mean(),
             float(np.percentile(b, 50)), float(np.percentile(a_, 50)),
             float(np.percentile(b, 95)), float(np.percentile(a_, 95))))
    return dict(seam_verts=int(mixed.sum()), verts=nv,
                step_p50_before=round(float(np.percentile(b, 50)), 4),
                step_p50_after=round(float(np.percentile(a_, 50)), 4),
                step_p95_before=round(float(np.percentile(b, 95)), 4),
                step_p95_after=round(float(np.percentile(a_, 95)), 4))


def road_verge(ground, road, F, hl, hr):
    """Paint the transition band into both meshes' COLOR_0.  +0 triangles."""
    gca, gcol, gam = _perceived(ground)
    rca, rcol, ram = _perceived(road)
    GP, RP = _loop_world(ground), _loop_world(road)
    go = _road_offset(F, hl, hr, GP[:, 0], GP[:, 1])
    ro = _road_offset(F, hl, hr, RP[:, 0], RP[:, 1])

    # the band's own edge wanders on the same value noise the surface pass uses,
    # so the verge is ragged at ~1 u — a clean gradient reads as an airbrush and
    # is the other way to fail this
    def rag(P):
        x, z = P[:, 0], -P[:, 1]
        n = _vnoise_v(x, z, 1.8, 47) * 0.62 + _vnoise_v(x, z, 0.55, 53) * 0.38
        return (n - 0.5) * 2.0 * VERGE_RAG

    tg_ = np.clip(1.0 - (go + rag(GP)) / VERGE_GROUND, 0.0, 1.0) ** 1.20
    tg_[go < 0] = 1.0                       # under the ribbon: fully the seam mix
    tr_ = np.clip(1.0 + (ro - rag(RP)) / VERGE_ROAD, 0.0, 1.0) ** 1.20
    tr_[ro > 0] = 1.0

    road_perc = (rcol[:, :3] * ram[:, None]).mean(0)          # one flat tint
    # the ground side takes the road's colour...
    gp = gcol[:, :3] * gam[:, None]
    gp = gp * (1 - (tg_ * VERGE_MIX)[:, None]) + road_perc * (tg_ * VERGE_MIX)[:, None]
    # ...and the road side takes the colour of the ground it is actually crossing,
    # sampled from the nearest ground loop rather than assumed to be grass (the
    # road runs through dry meadow for a third of its length)
    # PREFILTER, or this is a 19 k x 160 k product.  Only ground within 4 u of the
    # ribbon can ever be the nearest neighbour of a point ON the ribbon.
    cand = np.flatnonzero(go < 4.0)
    gxy = GP[cand][:, :2]
    near = np.zeros(len(RP), dtype=np.int64)
    step = 4096
    for a in range(0, len(RP), step):
        b = min(a + step, len(RP))
        d2 = ((RP[a:b, 0, None] - gxy[None, :, 0]) ** 2
              + (RP[a:b, 1, None] - gxy[None, :, 1]) ** 2)
        near[a:b] = cand[np.argmin(d2, axis=1)]
    ground_perc = gcol[near, :3] * gam[near, None]
    rp = rcol[:, :3] * ram[:, None]
    rp = rp * (1 - (tr_ * VERGE_MIX)[:, None]) + ground_perc * (tr_ * VERGE_MIX)[:, None]

    gout, rout = gcol.copy(), rcol.copy()
    gout[:, :3] = np.clip(gp / np.maximum(gam[:, None], 1e-6), 0.0, 1.0)
    rout[:, :3] = np.clip(rp / np.maximum(ram[:, None], 1e-6), 0.0, 1.0)
    gca.data.foreach_set("color", gout.ravel())
    rca.data.foreach_set("color", rout.ravel())

    lum = lambda a: 0.2126 * a[:, 0] + 0.7152 * a[:, 1] + 0.0722 * a[:, 2]
    # THE GATE IS THE STEP AT THE SEAM, in perceived albedo, before and after —
    # the number the complaint is about.  Anything else here is decoration.
    edge = (go > 0) & (go < 0.35)
    redge = ro > -0.20
    b_step = abs(float(lum(gcol[edge][:, :3] * gam[edge, None]).mean())
                 - float(lum(rcol[redge][:, :3] * ram[redge, None]).mean())) if edge.any() else 0.0
    a_step = abs(float(lum(gp[edge]).mean()) - float(lum(rp[redge]).mean())) if edge.any() else 0.0
    print("  R22 road verge — seam step in perceived albedo %.4f -> %.4f "
          "(%.0f%% closed) | band %.2f u out / %.2f u in, ragged +-%.2f u | "
          "%d ground corners touched, %d road corners, +0 triangles"
          % (b_step, a_step, 100.0 * (1 - a_step / max(b_step, 1e-6)),
             VERGE_GROUND, VERGE_ROAD, VERGE_RAG,
             int((tg_ > 0.02).sum()), int((tr_ > 0.02).sum())))
    return dict(step_before=round(b_step, 4), step_after=round(a_step, 4),
                ground_corners=int((tg_ > 0.02).sum()),
                road_corners=int((tr_ > 0.02).sum()))


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


# ---- THE CLUMP.  A LOBED icosphere: a bush at a rock's foot. ---------------
# R24 — the base solid is `bushlang.icosphere`, imported rather than re-typed; the
# hand-written 20-face icosahedron that used to sit here IS `icosphere(0)`.


# THE CLUMP'S SUN, in RUNTIME axes.  bushlang.SUN_TO is (-0.4393, 0.7031, 0.5592)
# in Blender (z-up); this geometry is built in runtime space and converted at the
# end of _emit by (x, y, z) -> (x, -z, y), so the inverse takes the sun vector to
# (x, z, -y).  Derived from the same ratified rig, NOT typed independently.
CLUMP_SUN = np.array([-0.4393, 0.5592, -0.7031])
CLUMP_BASE_DARK = 0.42      # COLOR_0 multiplier at the very bottom of a clump
CLUMP_SUN_AMT = 0.30        # how much of the shading the sun side wins
CLUMP_SINK = 0.16           # share of clump height buried below the terrain
# THE CLUMP'S LEAF SCALE IS THE BUSH'S LEAF SCALE, taken from bushlang rather than
# typed: both wear ow_valley_bushcore's leafmass_tile, and one leaf size across the
# region is the whole point of sharing the map.  See _clump_uv().
CLUMP_UV = BL.CORE_UV       # world units per leafmass_tile repeat
# R24 — THE SILHOUETTE KNOBS.  See _clump_geo() for why each one is here.
CLUMP_SUBD = 1              # bushlang.icosphere subdivisions: 0 = 20 faces, 1 = 80
CLUMP_VARIANTS = 6          # distinct lobed outlines, chosen per instance by hash
CLUMP_LOBE = (0.30, 0.17, 0.07)   # harmonic amplitudes — bushlang._harm's ladder
CLUMP_SKIRT = 0.12          # extra radius straight down: a bush sits INTO its foot


def _clump_harm(n, ph):
    """The clump's radius as a function of direction — bushlang._harm, y-up.

    LOW-order terms only, and for bushlang's own reason: sub-facet deformation
    under smooth shading reads as a cabbage, and THE SILHOUETTE IS WHAT HAS TO
    VARY.  Amplitudes are bushlang's ladder; only the vertical axis is renamed
    (this geometry is built in runtime space, where up is y).
    """
    nx, ny, nz = n[..., 0], n[..., 1], n[..., 2]
    a, b, c = CLUMP_LOBE
    k = (1.0
         + a * np.sin(2.7 * nx + ph[0]) * np.sin(2.2 * nz + ph[1])
         + b * np.sin(3.9 * nz + ph[2]) * np.sin(3.3 * ny + ph[3])
         + c * np.sin(6.9 * nx + ph[4]) * np.sin(5.9 * ny + ph[5]))
    k = k + CLUMP_SKIRT * np.maximum(-ny, 0.0)   # hangs lower underneath
    return np.maximum(k, 0.55)


def _vnormals(P, F):
    """Area-weighted smooth normals of a displaced surface.

    NOT the sphere direction any more.  A radius that varies with direction is no
    longer a sphere, so `v/|v|` would shade the new form with the old form's
    normals — the exact class of error that made every earlier round's "adjust
    the lighting" pass inert on this object.
    """
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    N = np.zeros_like(P)
    for j in range(3):
        np.add.at(N, F[:, j], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)


# RULES THIS OBJECT HAS ALREADY PAID FOR, and which the R24 rewrite keeps:
#   * FIND THE OBJECT THAT IS IN THE FRAME BEFORE FIXING THE OBJECT THAT HAS THE
#     RIGHT NAME (round 2).  `veg_bush` is almost entirely in the west forestwall —
#     only three of its vertices are within 45 m of any of the five fixed views.
#     What is in frame at every one of them is `veg_land_clumps`.
#   * THE SQUASH IS 0.94, NOT 0.62 (R11).  0.62 made pancakes; SIM.pick returned a
#     first-hit normal of (-0.06, 0.99, -0.14), a horizontal facet.
#   * A FORM GRADIENT AND A SINK (round 2).  One flat COLOR_0 over a convex solid
#     has no dark side and no dark underside, and a base tangent to the terrain
#     reads as floating.  `gshade` answers the first, CLUMP_SINK the second.
#   * UVS AND SMOOTH NORMALS (f4c/R19).  The clump lost f4b's A/B to a card bush
#     because it was effectively untextured (uv span 0.06 x 0.06 of the tile over
#     1.4 m2, 20/20 triangles flat) — not because cards beat volumes.
def _clump_geo(subd=None, nvar=None):
    """R24 — THE SILHOUETTE ROUND.  Returns a LIST of `nvar` unit clumps.

    f4c closed the material half of "green rocks" (UVs + smooth normals) and wrote
    down what it could not close: *"A 20-face solid still silhouettes as a hexagon,
    and no unwrap touches a silhouette."*  R22 closed the seam half and repeated it:
    *"no COLOR_0 treatment reaches an outline."*  Two rounds named the same object
    and neither could reach it, because BOTH were colour rounds.  An outline is
    geometry; only geometry moves it.

    Three changes, in the order they matter:
      * SUBDIVISION.  `bushlang.icosphere(CLUMP_SUBD)`.  At 20 faces the outline is
        ~6 straight segments; at a 1.3 m clump seen from 7 m that is ~25 px of
        unbroken line each, which is the hexagon the user sees.  80 faces halves
        the segment length AND gives the displacement below something to displace.
      * DISPLACEMENT.  `_clump_harm` — the same low-order harmonic ladder bushlang
        uses to give a lobe a form, which is the in-repo pattern the brief points
        at.  This is what makes the outline non-convex: subdivision alone buys a
        rounder hexagon, and a rounder hexagon is still a hull.
      * VARIANTS.  One displaced solid at 399 yaws is 399 copies of one silhouette,
        and a repeated outline is the same defect wearing a different face.  Six
        phases, picked per instance by a POSITION HASH — never by the scatter's
        `r()`, because a draw from that stream re-scatters the whole L2 layer and
        the A/B stops being an A/B (R11's note, paid for).

    THE UNIT BOX IS PRESERVED ON PURPOSE.  Each variant is renormalised to width
    1.0 and height 0.94 after displacement, so `w`/`h`/the -0.14 sink in `tufts()`
    still mean exactly what they meant — the form varies, the placement contract
    does not.
    """
    subd = CLUMP_SUBD if subd is None else subd
    nvar = CLUMP_VARIANTS if nvar is None else nvar
    V0, F0 = BL.icosphere(subd)
    # winding: assert the base solid faces OUT before its normals are trusted
    fn0 = np.cross(V0[F0[:, 1]] - V0[F0[:, 0]], V0[F0[:, 2]] - V0[F0[:, 0]])
    ctr0 = V0[F0].mean(axis=1)
    if float((fn0 * ctr0).sum(axis=1).mean()) < 0:
        F0 = F0[:, ::-1].copy()
    rs = np.random.RandomState(9271)
    # THE NORMALISATION REFERENCE IS THE R22 CLUMP ITSELF — the same solid with
    # k = 1 — so "same bulk, different outline" is true by construction and not by
    # eye.  Matching the max radius instead would have shrunk every clump by the
    # lobe amplitude and quietly taken green out of the meadow.
    ref = float(np.hypot(V0[:, 0], V0[:, 2]).mean()) * 0.5
    out = []
    for _ in range(nvar):
        ph = rs.uniform(0.0, 2.0 * math.pi, 6)
        P = V0 * (_clump_harm(V0, ph)[:, None] * 0.5)
        P[:, 1] *= 0.94                       # the R11 squash, on the lobed solid
        # recentre in plan (a lobed solid's centroid drifts off its scatter point)
        P[:, 0] -= P[:, 0].mean()
        P[:, 2] -= P[:, 2].mean()
        rad = float(np.hypot(P[:, 0], P[:, 2]).mean())
        P[:, 0] *= ref / rad
        P[:, 2] *= ref / rad
        lo, hi = float(P[:, 1].min()), float(P[:, 1].max())
        P[:, 1] = (P[:, 1] - lo) * (0.94 / (hi - lo)) - CLUMP_SINK
        N = _vnormals(P, F0)
        idx = F0.ravel()
        pos, nrm = P[idx], N[idx]
        fn = np.cross(P[F0[:, 1]] - P[F0[:, 0]], P[F0[:, 2]] - P[F0[:, 0]])
        uvax = np.repeat(np.argmax(np.abs(fn), axis=1), 3)
        t = np.clip((pos[:, 1] + CLUMP_SINK) / 0.94, 0.0, 1.0)
        base = CLUMP_BASE_DARK + (1.0 - CLUMP_BASE_DARK) * t ** 1.20
        sun = np.clip(nrm @ CLUMP_SUN * 0.5 + 0.5, 0.0, 1.0)
        shade = base * (1.0 - CLUMP_SUN_AMT + CLUMP_SUN_AMT * 2.0 * sun)
        out.append((pos, nrm, uvax.astype(int), shade))
    return out


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


def _clump_uv(gpos, uvax, s, row, seed=17):
    """Per-face planar UVs for ONE instance, in the instance's own scaled frame.

    bushlang's `_mesh_core` convention, in runtime axes: the two coordinates the
    face's dominant axis leaves over, taken off the SCALED local position, so a
    wide clump gets more leaf tile than a small one and the density is the same
    metres-per-repeat the bush core uses.  The yaw is deliberately NOT applied —
    the projection rides the clump's own frame, so 261 clumps at 261 yaws already
    disagree about phase; `off` decorrelates the rest.
    """
    p = gpos * s
    u = np.where(uvax == 0, p[:, 2], p[:, 0])
    v = np.where(uvax == 1, p[:, 2], p[:, 1])
    off = np.array([h2(row["x"], row["z"], seed), h2(row["z"], row["x"], seed + 1)])
    return np.stack([u, v], axis=-1) / CLUMP_UV + off[None, :]


def _emit(rows, gpos, gnrm, guv, gshade=None, uvax=None):
    """Bake instance rows into one runtime-space soup, then convert to Blender.

    R24 — gpos/gnrm/gshade/uvax may each be a LIST of equal-length variants, in
    which case `row["var"]` selects one per instance.  Every variant carries the
    same vertex count by construction (one icosphere, `nvar` phases), so the
    output arrays are still one allocation.
    """
    multi = isinstance(gpos, (list, tuple))
    npv = len(gpos[0] if multi else gpos)
    V = np.empty((len(rows) * npv, 3))
    N = np.empty((len(rows) * npv, 3)) if gnrm is not None else None
    C = np.empty((len(rows) * npv, 3))
    U = np.empty((len(rows) * npv, 2)) if (guv is not None or uvax is not None) else None
    for i, row in enumerate(rows):
        k = int(row.get("var", 0)) if multi else 0
        gp = gpos[k] if multi else gpos
        gn = (gnrm[k] if multi else gnrm) if gnrm is not None else None
        gs = (gshade[k] if multi else gshade) if gshade is not None else None
        ua = (uvax[k] if multi else uvax) if uvax is not None else None
        R = _rot(row["tilt"], row["yaw"])
        s = np.array([row["w"], row["h"], row["w"]])
        p = np.array([row["x"], row["y"], row["z"]])
        o = i * npv
        V[o:o + npv] = (gp * s) @ R.T + p
        if N is not None:
            # three.js's normalMatrix on a non-uniform scale: n' ~ R @ (n / s)
            m = (gn / s) @ R.T
            N[o:o + npv] = m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-9)
        C[o:o + npv] = row["c"] if gs is None else \
            np.asarray(row["c"])[None, :] * gs[:, None]
        if U is not None:
            U[o:o + npv] = guv if ua is None else _clump_uv(gp, ua, s, row)
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
    lip_tufts = 0

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
                lip = False
                if grad > maxslope:
                    # R14 — THE LIP WAS BALD BECAUSE OF THIS GATE, and the bald strip
                    # IS the "knife-straight line at the lip with no transition".  A
                    # clifftop cell is FLAT; the +-0.7 u probe straddles the edge, so
                    # every tuft within 0.7 u of it measured the CLIFF's gradient and
                    # was rejected.  Re-probe at +-0.28 u: if the tuft's OWN ground is
                    # gentle it stands — and it stands right on the brink, where it
                    # gets a bigger lean, which is the overhang the boundary wants.
                    # The slope gate itself is untouched everywhere else (the module
                    # docstring's 60 m of gorge wall sprouting grass stays impossible:
                    # this branch only fires on a GRASS site beside a rock seam).
                    if s[1] != 1 or rock_near < 2:
                        continue
                    ta_ = T.at(px + 0.28, pz)
                    tb_ = T.at(px - 0.28, pz)
                    tc_ = T.at(px, pz + 0.28)
                    td_ = T.at(px, pz - 0.28)
                    if ta_ is None or tb_ is None or tc_ is None or td_ is None:
                        continue
                    if math.hypot(ta_[0] - tb_[0], tc_[0] - td_[0]) / 0.56 > maxslope:
                        continue
                    lip = True
                c = np.array(p[int(r() * len(p))])
                c = c * (0.78 + r() * 0.52)          # a real value spread per tuft
                hh = (0.13 if s[1] == 3 else 0.15 if s[1] == 2 else 0.24) * (0.62 + r() * 0.90)
                if lip:
                    hh *= 1.35
                    lip_tufts += 1
                tuft_rows.append(dict(x=px, y=s[0] - 0.02, z=pz, w=0.34 + r() * 0.30,
                                      h=hh, yaw=r() * 6.28,
                                      tilt=(r() - 0.5) * (0.62 if lip else 0.26), c=c))
            # ---- SCALE TWO: a shrub clump where grass meets ROCK -------------
            # THE COLOUR MULTIPLIER IS AGAINST THE MAP'S OWN MEAN, NOT AGAINST 1.0.
            # ow_valley_bushcore ships COLOR_0 at L 0.311; instance-colouring it at
            # 0.5-0.8 produced faceted BLACK BOULDERS at every rock foot.
            # R14 — MORE BUSHES WHERE THE SEAM IS HARD.  The crest of a heightfield lip
            # is a row of triangles in SILHOUETTE, and no COLOR_0 edit softens a
            # silhouette: only something standing on it does.  Raised from 0.24 to 0.42
            # only where a grass site is more than half surrounded by rock, which is a
            # lip and nothing else.  ONE r() call either way — the stream is preserved.
            _pc = 0.42 if (rock_near > 6 and here[1] == 1) else 0.24
            if rock_near > 3 and r() < _pc:
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
                # R24 — the silhouette variant is a POSITION HASH, never a draw
                # from `r()`: one extra call here would re-scatter every tuft and
                # flower after it, and an A/B whose control layer moved is not an
                # A/B.  Same reason the height is drawn from the width above.
                clump_rows.append(dict(x=_cx, y=here[0] - 0.14, z=_cz, w=_cw,
                                       h=_ch, yaw=r() * 6.28, tilt=0.0, c=cc,
                                       var=int(h2(_cx, _cz, 29) * CLUMP_VARIANTS)
                                       % CLUMP_VARIANTS))
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
        vs = _clump_geo()
        gp = [v[0] for v in vs]; gn = [v[1] for v in vs]
        gax = [v[2] for v in vs]; gsh = [v[3] for v in vs]
        V, N, C, U = _emit(clump_rows, gp, gn, None, gshade=gsh, uvax=gax)
        objs.append(_mesh(col, "veg_land_clumps", V, N, C, U, m_clump, True))
        tris += len(V) // 3
    if flower_rows:
        gp, gn = _flower_geo()
        V, N, C, _ = _emit(flower_rows, gp, gn, None)
        objs.append(_mesh(col, "veg_land_flowers", V, N, C, None, m_flower, True))
        tris += len(V) // 3

    stats = dict(tufts=len(tuft_rows), seam_cells=edge_sites, clumps=len(clump_rows),
                 flowers=len(flower_rows), patches=placed, tris=tris,
                 lip_tufts=lip_tufts)
    print("  L2 ground-is-geometry — %d tufts (6 tris each, %d of them ON THE LIP) at "
          "%d seam cells + %d clumps + %d flowers in %d clumps, %d triangles in, 0 out"
          % (stats["tufts"], lip_tufts, stats["seam_cells"], stats["clumps"],
             stats["flowers"], stats["patches"], stats["tris"]))
    return objs, stats
