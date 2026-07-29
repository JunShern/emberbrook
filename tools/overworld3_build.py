"""overworld3_build.py — build tools/blends/overworld-proto3.blend (style F2).

  Blender -b --factory-startup -P tools/overworld3_build.py

ROUND 3.  The user picked round-2 style F (PBR miniature) and asked for the next
prototype: F plus a TERRAIN ZONE SYSTEM, plus fixes for the two things they did not
like — the regular sharp triangles, and every tree shipped so far.

So this script re-authors NOTHING.  It imports:

    overworld_lib.Field            round 1's one analytic valley field
    overworld_build.build_base     round 1's blockout (village, road, bridge, dam…)
    overworld_build.dusk_rig       the same dusk key as rounds 1 and 2
    overworld2_lib                 the tar boat, the dock, the mooring basin
    overworld2_build.pbr_mat       F's material recipe, unchanged

and spends its whole budget on the three new things, which live in
overworld3_lib: the ZONE GRID, the zone-driven TERRAIN treatment, and the four
TREE constructions.

The scale contract, the dusk rig, the Standard view transform and the chase-cam
rig (42 deg vfov, dist 16, pitch 0.62) are all inherited so F2 can be compared to
F on sight.
"""
import bpy
import math
import os
import sys
import time
import json

import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overworld_lib as L
import overworld_build as B
import overworld2_lib as O2
import overworld2_build as B2                # F's pbr_mat / bands / art direction
import overworld3_lib as O3

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TEX = os.path.join(ROOT, "tools/textures")
TEXO = os.path.join(TEX, "overworld")
OUT_BLEND = os.path.join(ROOT, "tools/blends/overworld-proto3.blend")
STYLE = "f2"

srgb = B.srgb
sstep = L.sstep
pbr_mat = B2.pbr_mat

# round-1/2 classes, plus round 3's four
(GRASS, GRASS_HI, AUTUMN, ROCK, PEAK, SAND, DIRT, WATER, WALL, ROOF, WOOD, STONE,
 FOL_A, FOL_B, FOL_C, TRUNK, EMIT, BASE, METAL, MIST) = range(20)
TAR, CANVAS, ROPE, LEAF, TUFT, LAMP = range(20, 26)
LEAFM, LEAFC, BARK, MARK = O3.LEAFM, O3.LEAFC, O3.BARK, O3.MARK

# F2's palette IS F's palette (the treatment must not drift), plus the four new
# classes.  The veg entries are deliberately pale: they only TINT real albedo, and
# glTF's baseColorTexture * COLOR_0 can never brighten (round-1 finding).
PAL_F2 = dict(B.PAL["f"])
PAL_F2.update({LEAFM: "8fa07e", LEAFC: "ffffff", BARK: "9b8a74", MARK: "d9d2c2"})
B.PAL[STYLE] = PAL_F2
B.PAL_LIN[STYLE] = {c: srgb(h) for c, h in PAL_F2.items()}

BUILD = {}


# --------------------------------------------------------------- field sampling
def gsamp(A, x, y):
    """Bilinear sample of a Field array shaped (NX, NY) or (NX, NY, k).

    Round 2's bands()/art_colors() index their weights BY VERTEX INDEX, which
    only works while the terrain is exactly the NX x NY lattice.  F2's terrain
    has hashed diagonals and extra centre vertices, so every field lookup has to
    go through position instead — this is that lookup.
    """
    fx = np.clip((np.asarray(x, float) + L.TILE_X / 2) / L.STEP, 0, L.NX - 1.001)
    fy = np.clip((np.asarray(y, float) + L.TILE_Y / 2) / L.STEP, 0, L.NY - 1.001)
    i0, j0 = fx.astype(int), fy.astype(int)
    tx, ty = fx - i0, fy - j0
    if A.ndim == 3:
        tx, ty = tx[..., None], ty[..., None]
    return (A[i0, j0] * (1 - tx) * (1 - ty) + A[i0 + 1, j0] * tx * (1 - ty)
            + A[i0, j0 + 1] * (1 - tx) * ty + A[i0 + 1, j0 + 1] * tx * ty)


# THREE slots, not round 2's four.  The dirt layer is gone from the TERRAIN
# because one-material-per-FACE means every slot boundary is a hard zigzag along
# the triangulation, and the road's apron is the one boundary the chase camera
# stares straight down at — round 2's per-face argmax is why the road wore a
# sawtooth.  A road apron is a COLOUR gradient (COLOR_0, per-vertex, smooth), and
# the ribbons themselves keep their own stony-dirt material.  Bonus: three fewer
# images in the GLB.
TERRAIN_LAYERS = [
    ("grass", "leafy_grass_diff_1k.jpg", "leafy_grass_nor_gl_1k.jpg", "leafy_grass_rough_1k.jpg"),
    ("dry", "withered_grass_diff_1k.jpg", "withered_grass_nor_gl_1k.jpg", "withered_grass_rough_1k.jpg"),
    ("rock", None, None, None),                          # rock_face_03 lives in TEX
]
SLOT_GRASS, SLOT_DRY, SLOT_ROCK = range(3)


def layer_paths():
    out = []
    for nm, d, n, r in TERRAIN_LAYERS:
        if nm == "rock":
            out.append((nm, os.path.join(TEX, "rock_face_03_Diffuse.jpg"),
                        os.path.join(TEX, "rock_face_03_nor_gl.jpg"),
                        os.path.join(TEX, "rock_face_03_Rough.jpg")))
        else:
            out.append((nm, os.path.join(TEXO, d), os.path.join(TEXO, n), os.path.join(TEXO, r)))
    return out


def bands_at(F, x, y):
    """F's four terrain-layer weights, sampled at arbitrary positions."""
    w7 = gsamp(F.w, x, y)
    W = np.stack([w7[..., GRASS] + w7[..., GRASS_HI] + 0.35 * w7[..., AUTUMN]
                  + w7[..., DIRT],
                  0.5 * (w7[..., AUTUMN] + w7[..., SAND]),
                  w7[..., ROCK] + w7[..., PEAK]], -1)
    W = np.maximum(W, 0.0)
    base = np.clip(1.0 - W[..., 1:].sum(-1), 0.0, 1.0)
    W[..., 0] = np.maximum(W[..., 0], base)
    return W / np.maximum(W.sum(-1, keepdims=True), 1e-6)


def art_colors_at(F, zg, x, y):
    """F's per-vertex art direction — plus a ZONE tint, so the zone system is
    visible in the art and not only in the debug overlay: forest ground goes
    deeper and greener, crag goes grey and loses its chroma."""
    pal = B.PAL_LIN[STYLE]
    P = np.array([pal[c] for c in range(7)])
    c = gsamp(F.w, x, y) @ P
    fw = zg.wsample(zg.forest_w, x, y)[..., None]
    c = c * (1 - 0.30 * fw) + srgb("4e6b3c") * (0.30 * fw)
    cw = zg.wsample(zg.crag_w, x, y)[..., None]
    c = c * (1 - 0.34 * cw) + srgb("8e8880") * (0.34 * cw)
    # Round-2 finding 127 is unfixable inside glTF (no second UV blend, no detail
    # multiply on baseColor) — but it is only visible because the repeat is the
    # ONLY variation on a 40u rim.  A low-frequency ridged wash in COLOR_0, at a
    # wavelength far longer than the 6.2u tile, gives the eye something else to
    # read and the lattice stops being the pattern it finds.
    br = O3.ridged(x, y, 0.085, 61, oct_=2)[..., None]
    c = c * (1.0 - cw * (0.30 - 0.46 * br))
    # the road's worn apron, as a smooth per-vertex gradient
    drd = F.road_dist(np.asarray(x, float).ravel(),
                      np.asarray(y, float).ravel()).reshape(np.shape(x))
    dw = ((1.0 - L.sstep(1.1, 5.2, drd))
          * L.sstep(2.2, 4.4, gsamp(F.dr, x, y)))[..., None]
    c = c * (1 - 0.62 * dw) + srgb("6d5b45") * (0.62 * dw)
    c = c * (1.0 + (gsamp(F.shade, x, y) - 1.0) * 0.55)[..., None]
    return np.clip(c, 0.0, 1.0)


def write_vcol_at(ob, F, zg):
    me = ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    cols = art_colors_at(F, zg, co[:, 0], co[:, 1])
    a = B.ensure_col(me)
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    d = np.ones((len(me.loops), 4))
    d[:, :3] = cols[lv]
    a.data.foreach_set("color", d.ravel())
    return cols


# ------------------------------------------------------------------ terrain look
def loop_face(me):
    """Per-loop face index — the bridge between face data and loop data.  Every
    vectorised colour/UV write below needs it, and building it once beats a python
    loop over polygons for meshes with 14 000 faces."""
    lt = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get("loop_total", lt)
    return np.repeat(np.arange(len(me.polygons)), lt)


def face_centers(me):
    c = np.zeros(len(me.polygons) * 3)
    me.polygons.foreach_get("center", c)
    return c.reshape(-1, 3)


def zone_idx_at(zg, bx, by):
    """Vectorised zone-index lookup at BLENDER coords (the array form of
    ZoneGrid.type_at, which is a python call and too slow per face)."""
    c = np.floor((np.asarray(bx, float) - zg.origin[0]) / zg.cell).astype(int)
    r = np.floor(((-np.asarray(by, float)) - zg.origin[1]) / zg.cell).astype(int)
    c = np.clip(c, 0, zg.cols - 1)
    r = np.clip(r, 0, zg.rows - 1)
    return zg.idx[c, r]


def vec_gain(ob, face_gain):
    """Multiply COLOR_0 by a per-FACE gain, vectorised through loop_face()."""
    ca = ob.data.color_attributes.get("Col")
    if ca is None:
        return
    d = np.zeros(len(ca.data) * 4)
    ca.data.foreach_get("color", d)
    d = d.reshape(-1, 4)
    d[:, :3] = np.clip(d[:, :3] * face_gain[loop_face(ob.data)][:, None], 0.0, 1.0)
    ca.data.foreach_set("color", d.ravel())


def vec_planar_uv(ob, scale, F=None, flat_thresh=0.72):
    """Triplanar UVs, vectorised.  Same rule as round 2: flat faces take XY and
    steep faces take the dominant LATERAL axis, and when a field is supplied the
    axis comes from the ANALYTIC GRADIENT at the face centre, not from the facet
    normal — neighbouring facets must agree or the hillside wears a diamond
    lattice (round-2 finding 126).  With no field it falls back to the normal,
    which is the plain box projection the props want.
    """
    me = ob.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    lf = loop_face(me)
    if F is not None:
        gx, gy = np.gradient(F.H, L.STEP, L.STEP)
        ctr = face_centers(me)
        i = np.clip((ctr[:, 0] + L.TILE_X / 2) / L.STEP, 0, L.NX - 1).astype(int)
        j = np.clip((ctr[:, 1] + L.TILE_Y / 2) / L.STEP, 0, L.NY - 1).astype(int)
        a, b = gx[i, j], gy[i, j]
        nz = 1.0 / np.sqrt(1.0 + a * a + b * b)
        flat = nz >= flat_thresh
        xdom = np.abs(a) >= np.abs(b)
    else:
        nr = np.zeros(len(me.polygons) * 3)
        me.polygons.foreach_get("normal", nr)
        nr = nr.reshape(-1, 3)
        ax = np.argmax(np.abs(nr), axis=1)
        flat = ax == 2
        xdom = ax == 0
    ui = np.where(flat, 0, np.where(xdom, 1, 0))
    vi = np.where(flat, 1, 2)
    d = np.column_stack([co[lv, ui[lf]] / scale, co[lv, vi[lf]] / scale])
    uv.data.foreach_set("uv", d.ravel())


def terrain_pbr_f2(made, F, zg, fcrag):
    """F's four tiled PBR slots — but the SLOT CHOICE is a zone lookup.

    Round 2 picked the slot per face by argmax of the blended class weights,
    which flickers between neighbours on a boundary.  Here crag cells take rock
    and road cells take dirt because the ZONE says so, which is both steadier and
    the same single truth the encounter grid uses.
    """
    ground = made["ground"]
    vec_planar_uv(ground, 6.2, F=F)        # analytic-gradient axis choice: finding 126
    write_vcol_at(ground, F, zg)
    me = ground.data

    ctr = face_centers(me)
    W = bands_at(F, ctr[:, 0], ctr[:, 1])
    dom = np.argmax(W, axis=-1)
    # ZONE DRIVES THE LOOK THROUGH THE SMOOTHED WEIGHTS, NEVER THROUGH THE CELL
    # INDEX.  The first pass forced slots off zg.idx and the road grew a blocky
    # stair-stepped dirt apron and the crag a square grass/rock seam — the zone
    # grid is 1.25u quantised, so anything that reads it discretely wears its
    # cells.  The bilinear weight fields have the same information and a smooth
    # contour, and the discrete grid stays what it is for: gameplay.
    cw = zg.wsample(zg.crag_w, ctr[:, 0], ctr[:, 1])
    fw = zg.wsample(zg.forest_w, ctr[:, 0], ctr[:, 1])
    # the DRY layer is what keeps a 120x90u meadow from being one green sheet, and
    # argmax never reaches for it (round 2 halved its weight on purpose)
    dom[(W[:, SLOT_DRY] > 0.24) & (fw < 0.30) & (cw < 0.30)] = SLOT_DRY
    dom[(fw > 0.45) & (cw < 0.30)] = SLOT_GRASS       # forest floor is not straw
    dom[cw > 0.50] = SLOT_ROCK
    dom[fcrag > O3.FLAT_W] = SLOT_ROCK     # the roughened facets ARE rock
    # the grass<->rock seam is the only slot boundary left, and it is DITHERED by
    # the same hash the tessellation uses: a threshold on a smooth field still
    # draws one clean contour, and a clean contour on a triangulated surface is a
    # zigzag.  Ragged reads as weathering; regular reads as a bug.
    jitter = O3._hash01((ctr[:, 0] * 37.0).astype(int),
                        (ctr[:, 1] * 37.0).astype(int), 4)
    dom[(cw > 0.34) & (cw <= 0.50) & (jitter < (cw - 0.34) / 0.16)] = SLOT_ROCK

    slots = []
    for nm, diff, nor, rgh in layer_paths():
        slots.append(pbr_mat("ow_f2_ter_" + nm, diff, nor, rgh, tile=1.0, vcol=True,
                             gain_to=0.46))
    me.materials.clear()
    for m in slots:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", dom.astype(np.int32))

    # per-slot gain: a multiply only darkens, so each class colour is pre-divided
    # by ITS OWN albedo mean (four photos, four gains)
    gains = np.array([slots[i]["vcol_gain"] for i in range(len(slots))])
    vec_gain(ground, gains[dom])
    cnt = {nm: int((dom == i).sum()) for i, (nm, *_ ) in enumerate(layer_paths())}
    print("  terrain slots by face: %s   gains %s"
          % (cnt, [round(float(g), 2) for g in gains]))

    for key, tint, tex_ in (("road", "8e7a63", "stony_dirt_path"),
                            ("dockpath", "8a765f", "stony_dirt_path"),
                            ("green", "9aa882", "leafy_grass")):
        ob = made[key]
        vec_planar_uv(ob, 2.2)
        m = pbr_mat("ow_f2_" + key, os.path.join(TEXO, tex_ + "_diff_1k.jpg"),
                    os.path.join(TEXO, tex_ + "_nor_gl_1k.jpg"),
                    os.path.join(TEXO, tex_ + "_rough_1k.jpg"), tile=1.0, vcol=True)
        ca = ob.data.color_attributes["Col"]
        d = np.zeros(len(ca.data) * 4).reshape(-1, 4)
        d[:, :3] = np.clip(srgb(tint) * m["vcol_gain"], 0, 1)
        d[:, 3] = 1.0
        ca.data.foreach_set("color", d.ravel())
        ob.data.materials.clear()
        ob.data.materials.append(m)
        ob.data.polygons.foreach_set("material_index", [0] * len(ob.data.polygons))
    return slots


# ----------------------------------------------------------------- prop materials
def apply_class_gains(ob, cls, group, gains):
    """Pre-divide each face's class colour by ITS OWN material's albedo mean —
    glTF can only do baseColorTexture * COLOR_0, and a multiply only darkens."""
    vec_gain(ob, np.array([gains.get(group.get(int(c), "matte"), 1.0) for c in cls]))


def props_materials_f2(made, mats, group, veg_maps):
    """F's prop PBR set, plus round 3's three vegetation materials."""
    Q = lambda n: os.path.join(TEX, n)
    pm = {
        "plaster": pbr_mat("ow_f2_plaster", Q("clay_plaster_Diffuse.jpg"),
                           Q("clay_plaster_nor_gl.jpg"), Q("clay_plaster_Rough.jpg"),
                           tile=0.55, vcol=True, gain_to=0.46),
        "tiles": pbr_mat("ow_f2_tiles", Q("red_slate_roof_tiles_01_Diffuse.jpg"),
                         Q("red_slate_roof_tiles_01_nor_gl.jpg"),
                         Q("red_slate_roof_tiles_01_Rough.jpg"),
                         tile=0.9, vcol=True, gain_to=0.5),
        "planks": pbr_mat("ow_f2_planks", Q("weathered_planks_Diffuse.jpg"),
                          Q("weathered_planks_nor_gl.jpg"), Q("weathered_planks_Rough.jpg"),
                          tile=1.1, vcol=True, gain_to=0.46),
        "stone": pbr_mat("ow_f2_stone", Q("rock_face_03_Diffuse.jpg"),
                         Q("rock_face_03_nor_gl.jpg"), Q("rock_face_03_Rough.jpg"),
                         tile=0.45, vcol=True, gain_to=0.46),
        "tar": pbr_mat("ow_f2_tar", Q("dark_wooden_planks_Diffuse.jpg"),
                       Q("dark_wooden_planks_nor_gl.jpg"),
                       Q("dark_wooden_planks_Rough.jpg"),
                       tile=1.4, vcol=True, gain_to=0.62),
        # round 3's own: procedural, tileable, generated in numpy (one-off assets)
        "bark": pbr_mat("ow_f2_bark", veg_maps["bark_d"], veg_maps["bark_n"], None,
                        tile=1.0, vcol=True, gain_to=0.50, rough_default=0.94),
        "canopy": pbr_mat("ow_f2_canopy", veg_maps["can_d"], veg_maps["can_n"], None,
                          tile=1.0, vcol=True, gain_to=0.50, rough_default=0.92),
    }
    # the alpha-MASK leaf card.  vcol=False on purpose: the atlas already carries
    # per-leaf variation and a COLOR_0 multiply on an alpha atlas makes black
    # splats (round-2 finding 132).
    pm["leaf"] = pbr_mat("ow_f2_leaf", veg_maps["atlas"], None, None, tile=1.0,
                         vcol=False, alpha_clip=True, twosided=True, rough_default=0.95)
    mats.update(pm)
    group.update({WALL: "plaster", ROOF: "tiles", WOOD: "planks", TRUNK: "planks",
                  STONE: "stone", ROCK: "stone", BASE: "stone",
                  TAR: "tar", CANVAS: "planks", ROPE: "planks", METAL: "stone",
                  FOL_A: "canopy", FOL_B: "canopy", FOL_C: "canopy",
                  LEAFM: "canopy", LEAFC: "leaf", BARK: "bark", MARK: "matte"})
    return pm


# ---------------------------------------------------------------------- cameras
def add_cameras_f2(sc, F, zg, fr, base_objs, D):
    """The inherited three, plus the three shots round 3 has to answer for."""
    B.add_cameras(sc, F, base_objs["_charpos"][:3], base_objs["_charpos"][3], STYLE)
    cams = {}

    def cam(name, eye, aim, fov=42.0, fit="V"):
        nm = "cam_%s__%s" % (name, STYLE)
        cd = bpy.data.cameras.new(nm)
        cd.sensor_fit = "VERTICAL" if fit == "V" else "HORIZONTAL"
        if fit == "V":
            cd.angle_y = math.radians(fov)
        else:
            cd.angle_x = math.radians(fov)
        cd.clip_start, cd.clip_end = 0.05, 900.0
        ob = bpy.data.objects.new(nm, cd)
        sc.collection.objects.link(ob)
        ob.location = Vector(eye)
        ob.rotation_euler = (Vector(aim) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cams[name] = ob
        return ob

    # boat: from the village bank looking ALONG the river (round-2 finding 134)
    bx, by, bz = D["boat"]
    nx, ny = D["nrm"]
    tx, ty = D["tg"]
    cx_, cy_ = D["ctr"]
    cam("boat", (cx_ - tx * 8.0 - nx * 1.9, cy_ - ty * 8.0 - ny * 1.9, D["wl"] + 1.95),
        (bx - tx * 0.2, by - ty * 0.2, bz + 0.48))

    # gorge: the crag treatment's own exhibit — the east notch, seen from the lit
    # (south) side so the broken rock is modelled rather than silhouetted
    rt, rx, ry = L.river_pts(601)
    gi = int(np.argmin(np.abs(rt - 0.815)))
    gx, gy = float(rx[gi]), float(ry[gi])
    wl = float(L.water_level(np.array([rt[gi]]))[0])
    ex, ey = gx - 21.0, gy - 27.0
    eg = float(O3.height(F, zg, np.array([ex]), np.array([ey]), fr)[0])
    cam("gorge", (ex, ey, max(eg + 15.0, wl + 27.0)), (gx - 1.0, gy + 5.0, wl + 7.0))

    # line-up: square on to the four groups from the lit side, high enough that
    # the near ground is not in the way of the far group
    lc = O3.LINEUP_C
    px, py = -math.sin(O3.LINEUP_ANG), math.cos(O3.LINEUP_ANG)
    if py > 0:
        px, py = -px, -py                       # stand on the SOUTH (lit) side
    # 17.5u out is what fits four groups across a 42 deg vertical / 69 deg
    # horizontal frame; standing further back to be safe just makes the trees
    # small, and this shot exists to be looked AT closely
    ex, ey = lc[0] + px * 17.5, lc[1] + py * 17.5
    eg = float(O3.height(F, zg, np.array([ex]), np.array([ey]), fr)[0])
    ag = float(O3.height(F, zg, np.array([lc[0]]), np.array([lc[1]]), fr)[0])
    cam("lineup", (ex, ey, eg + 5.0), (lc[0], lc[1], ag + 2.4))

    # zones: a high oblique over the whole valley — the shot the debug tint rides
    cam("zones", (0.0, -104.0, 104.0), (1.0, 2.0, 6.0), fov=68.0, fit="H")
    return cams


# ------------------------------------------------------------------------ build
def main():
    t_all = time.time()
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    t0 = time.time()
    F = L.Field()
    t_field = time.time() - t0
    print("field %dx%d  village_h=%.2f  clifftown_h=%.2f  (%.1fs)"
          % (L.NX, L.NY, F.village_h, F.clifftown_h, t_field))

    base_sc = bpy.data.scenes[0]
    base_sc.name = "BASE"
    base_col = bpy.data.collections.new("base_geo")
    base_sc.collection.children.link(base_col)
    objs = B.build_base(F, base_col)

    # ---- one-off vegetation assets (NOT part of the per-tile cost) ----------
    t0 = time.time()
    can_d, can_n = O3.canopy_maps()
    bark_d, bark_n = O3.bark_maps()
    atlas = O3.leafmass_atlas()
    veg_maps = dict(can_d=can_d, can_n=can_n, bark_d=bark_d, bark_n=bark_n, atlas=atlas)
    t_assets = time.time() - t0
    print("veg maps ready (%.1fs, one-off)" % t_assets)

    # =================================================== the tile itself
    t_tile = time.time()
    sc = bpy.data.scenes.new("style_" + STYLE)
    col = sc.collection
    B.dusk_rig(sc, F, STYLE)

    mats = {"matte": B.new_mat("ow_%s_matte" % STYLE, rough=0.9),
            "water": B.new_mat("ow_%s_water" % STYLE, rough=0.28, alpha=0.82, blend=True),
            "emit": B.new_mat("ow_%s_emit" % STYLE, rough=0.6, emit=srgb("ff9f38"), emit_str=9.0),
            "mist": B.new_mat("ow_%s_mist" % STYLE, rough=1.0, alpha=0.2, blend=True)}
    for k in ("water", "mist"):
        mats[k].show_transparent_back = False       # round-2 finding 135
    group = dict(B.GROUP)

    # ---- the shared blockout, minus the two meshes F2 rebuilds -------------
    made = {}
    for key, ob in objs.items():
        if key.startswith("_") or key in ("trees", "ground", "skirt"):
            continue
        d = ob.copy()
        d.data = ob.data.copy()
        d.name = "%s__%s" % (ob.name, STYLE)
        d.data.name = d.name
        col.objects.link(d)
        made[key] = d

    # ---- PART 1: the zone grid --------------------------------------------
    fr = O2.pool_frame(F)
    t0 = time.time()
    zg = O3.ZoneGrid(F, fr)
    t_zone = time.time() - t0
    cov = zg.coverage()
    print("zone grid %dx%d cell=%.2fu  (%.2fs)  %s"
          % (zg.cols, zg.rows, zg.cell, t_zone,
             " ".join("%s=%.1f%%" % (k, v) for k, v in cov.items())))
    print("  thresholds %s  override cells %d" % (zg.thresh, zg.n_override))

    # ---- PART 2: the zone-driven terrain ----------------------------------
    ground, skirt, fcrag = O3.build_terrain(col, F, zg, fr)
    for ob, key in ((ground, "ground"), (skirt, "skirt")):
        ob.name = "%s__%s" % (ob.name, STYLE)
        ob.data.name = ob.name
        made[key] = ob

    # ---- PART 3: the trees -------------------------------------------------
    lineup, groups = O3.build_lineup(col, F, zg, fr, STYLE)
    field, placed, byzone = O3.plant_field(col, F, zg, fr, STYLE)
    veg_keys = []
    for k, o in list(lineup.items()) + [("field_" + k, o) for k, o in field.items()]:
        made["veg_" + k] = o
        veg_keys.append("veg_" + k)

    # ---- the dock + boat_tar (round 2's, unchanged) ------------------------
    cls = dict(hull=TAR, wood=WOOD, dark=TAR, canvas=CANVAS, rope=ROPE, lamp=LAMP)
    deck = B.Prop("walk_dock")
    props = B.Prop("dock_props")
    D = O2.build_dock(F, deck, props, cls, fr, boat_rig="mast")
    do = deck.finish(col)
    do.name = do.data.name = "walk_dock__" + STYLE
    po = props.finish(col)
    po.name = po.data.name = "boat_tar__" + STYLE
    made["dock"], made["boat"] = do, po
    wp = B.Prop("water_pool")
    O2.pool_water(wp, WATER, fr)
    wo = wp.finish(col)
    wo.name = wo.data.name = "water_pool__" + STYLE
    made["pool"] = wo
    sp = B.Prop("walk_dockpath")
    O2.dock_path(F, sp, DIRT, D["root"], fr)
    spo = sp.finish(col)
    spo.name = spo.data.name = "walk_dockpath__" + STYLE
    made["dockpath"] = spo
    rp = B.Prop("ref_char_dock")
    rx_ = D["root"][0] * 0.72 + D["head"][0] * 0.28
    ry_ = D["root"][1] * 0.72 + D["head"][1] * 0.28
    rp.cone(PEAK, (rx_, ry_, D["head"][2] + 0.72), 0.26, 0.26, 1.05, seg=10)
    rp.ico(PEAK, (rx_, ry_, D["head"][2] + 1.24), (0.26, 0.26, 0.26), subd=1)
    rp.ico(PEAK, (rx_, ry_, D["head"][2] + 0.21), (0.26, 0.26, 0.21), subd=1)
    ro = rp.finish(col)
    ro.name = ro.data.name = "ref_char_dock__" + STYLE
    made["refdock"] = ro

    # ---- prop colours ------------------------------------------------------
    PROPKEYS = (["skirt", "water", "road", "green", "bridge", "village", "clifftown",
                 "dam", "rocks", "ref", "dock", "boat", "dockpath", "refdock", "pool"]
                + veg_keys)
    for i, key in enumerate(PROPKEYS):
        ob = made[key]
        jit = 0.10 if key.startswith("veg_") else 0.055
        made[key + "_cls"] = B.write_prop_colors(ob, STYLE, True, jit, seed=41 + i)

    # ---- shading -----------------------------------------------------------
    # the canopies are SMOOTH (a faceted leaf mass is round 1's rejected blob);
    # the terrain already carries its own per-face smooth flags from build_terrain
    SOFT = {"water", "pool", "rocks", "green"} | set(veg_keys)
    for key in PROPKEYS:
        ob = made[key]
        v = key in SOFT
        ob.data.polygons.foreach_set("use_smooth", [v] * len(ob.data.polygons))
        ob.data.update()

    # ---- materials ---------------------------------------------------------
    pm = props_materials_f2(made, mats, group, veg_maps)
    UVKEYS = ["village", "clifftown", "dam", "bridge", "rocks", "boat", "dock",
              "skirt"] + [k for k in veg_keys if not k.endswith("_cards")]
    for key in UVKEYS:
        scale = 1.35 if key.startswith("veg_") and "trunks" not in key else 1.0
        vec_planar_uv(made[key], 1.0 / scale)
    gains = {g: m["vcol_gain"] for g, m in pm.items()}
    for key in UVKEYS:
        apply_class_gains(made[key], made[key + "_cls"], group, gains)
    for key in PROPKEYS:
        ob = made[key]
        if ob.data.materials:
            continue
        B2.assign_slots2(ob, mats, made[key + "_cls"], group)

    slots = terrain_pbr_f2(made, F, zg, fcrag)

    # ---- the QA-only zone overlay -----------------------------------------
    ovl = O3.build_zone_overlay(col, F, zg, fr)
    ovl.name = ovl.data.name = "qa_zone_overlay__" + STYLE
    om = B.new_mat("ow_%s_zoneovl" % STYLE, rough=1.0, alpha=0.62, blend=True)
    nt = om.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "Col"
    nt.links.new(ca.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    om.show_transparent_back = False
    ovl.data.materials.append(om)

    # ---- cameras + render conventions -------------------------------------
    add_cameras_f2(sc, F, zg, fr, objs, D)
    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.resolution_percentage = 100
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"        # the runtime tone-maps nothing
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
        sc.eevee.shadow_pool_size = 1024                # round-2 finding 135
    except Exception:
        pass

    t_tile = time.time() - t_tile
    BUILD[STYLE] = round(t_tile, 1)
    print("style %s built in %.1fs (zone derivation %.2fs of it)" % (STYLE, t_tile, t_zone))

    # ---- zones.json into the playable bundle -------------------------------
    zp = os.path.join(ROOT, "public/assets/scenes/ow-proto-%s/zones.json" % STYLE)
    zg.write(zp)
    print("zones.json -> %s (%.1f kB)" % (zp, os.path.getsize(zp) / 1e3))

    qa = os.path.join(ROOT, "docs/qa/overworld")
    os.makedirs(qa, exist_ok=True)
    fp = os.path.join(qa, "build_times3.json")
    json.dump({STYLE: round(t_tile, 2), "zone_derivation": round(t_zone, 3),
               "field": round(t_field, 2), "veg_assets_oneoff": round(t_assets, 2),
               "zone_coverage_pct": {k: round(v, 2) for k, v in cov.items()}},
              open(fp, "w"), indent=1, sort_keys=True)

    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
               for o in sc.objects if o.type == "MESH" and not o.name.startswith("qa_"))
    print("tile totals: %d meshes, %d tris (excl. QA overlay)"
          % (len([o for o in sc.objects if o.type == "MESH"]), tris))

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("SAVED %s  (%.1fs total)" % (OUT_BLEND, time.time() - t_all))


if __name__ == "__main__":
    main()
