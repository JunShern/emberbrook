"""foliage_lineup.py — the BUSH-LANGUAGE taste gate.

  Blender --python-exit-code 1 -b --factory-startup -P tools/foliage_lineup.py

The user's judging surface for this pass, and deliberately its own scene:
tools/blends/foliage-lineup.blend, renders to docs/qa/overworld/foliage_lineup*.png.
It touches NOTHING in the valley pipeline (the geography session owns that), and
it is built on THE SAME HILLSIDE AS THE OLD TREE LINE-UP — `overworld3_lib`'s
LINEUP_C / LINEUP_ANG on the round-1 field, which is where styles a/b/c/d and the
four tree constructions were compared.  Same ground, same dusk rig, same 1.45u
scale references: only the vegetation language has changed.

WHAT IS ON EXHIBIT
  1..3  three SHELL DENSITIES over identical cores (sparse / medium / dense) —
        the one number the recipe most needs a taste ruling on;
  4     the ROCK sample: two blocks in the two new PolyHaven rock sets, the left
        one with STRATA displacement (large coherent forms) and the right one
        with the fine jitter the crag treatment uses today, so the difference is
        visible side by side rather than argued about.

Two shots, and the second is the one that matters:
  foliage_lineup.png         a 3/4 view across the line, close enough to judge
                             leaf detail
  foliage_lineup_aerial.png  THE CHASE RIG'S OWN GEOMETRY (42 deg, dist 34,
                             pitch 0.61 rad = 35 deg) — the camera this world is
                             actually played through, and the one that catches a
                             card lying flat.
"""
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overworld_lib as L
import overworld_build as B
import overworld2_build as B2
import overworld3_lib as O3
import overworld3_build as B3          # registers B.PAL["f2"]
import bushlang as BL
import foliage_atlas as FA

ROOT = B3.ROOT
TEX = os.path.join(ROOT, "tools/textures")
TEXO = os.path.join(TEX, "overworld")
OUT_BLEND = os.path.join(ROOT, "tools/blends/foliage-lineup.blend")
QA = os.path.join(ROOT, "docs/qa/overworld")
STYLE = "f2"

# the three densities on exhibit, in cards per square unit of visible core
DENSITIES = (("sparse", 1.5), ("medium", 3.2), ("dense", 6.5))
BIG = (1.25, 2.00)                     # big-clump card width, world units
FUZZ = (0.58, 0.98)
MASS_R = 2.5                           # a forest-mass lobe cluster, not a shrub
MASS_H = 3.6

# the old line-up's own site, so the comparison is against a remembered frame
LC = O3.LINEUP_C
LA = O3.LINEUP_ANG
SPOTS = (-20.5, -6.9, 6.9, 20.8)       # three bush groups then the rock block


def ground_patch(col, F, cx, cy, half=(33.0, 21.0), step=1.0):
    """The hillside itself: a patch of the round-1 field around the line-up."""
    nx = int(2 * half[0] / step) + 1
    ny = int(2 * half[1] / step) + 1
    xs = cx + np.linspace(-half[0], half[0], nx)
    ys = cy + np.linspace(-half[1], half[1], ny)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    H = F.sample(X, Y)
    V = np.stack([X.ravel(), Y.ravel(), H.ravel()], -1)
    idx = np.arange(nx * ny).reshape(nx, ny)
    faces = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                     -1).reshape(-1, 4)
    me = bpy.data.meshes.new("ground_lineup")
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in faces])
    uvl = me.uv_layers.new(name="UVMap")
    loops = np.zeros(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", loops)
    uvl.data.foreach_set("uv", (V[loops][:, :2] / 5.4).ravel())
    ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
    d = np.ones((len(V), 4))
    d[:, :3] = np.array([0.86, 0.88, 0.80])
    ca.data.foreach_set("color", d.ravel())
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("ground_lineup", me)
    col.objects.link(ob)
    return ob


def rock_block(col, mat, cx, cy, cz, r, h, seed, strata=True, name="rock"):
    """A rock sample: an icosphere pushed into PLANES, not jitter.

    The point of the exhibit.  The crag treatment today adds fine per-facet
    jitter, which at region scale reads as gravel however big the cliff is.  A
    real rock face is a few large coherent forms — bedding planes stacked, cut by
    a couple of joints — so the displacement here is BANDED in z (strata) plus
    two planar cuts, and the fine noise is only the last 15%.
    """
    U, Fc = BL.icosphere(3)
    rng = np.random.RandomState(seed)
    ph = rng.rand(8) * 6.283
    s = np.array([r, r * rng.uniform(0.8, 1.05), h])
    P = U * s[None, :]
    if strata:
        # BEDDING, and it has to be big enough to see: 4-6 beds over the block,
        # each stepped in or out by up to 18% of the radius, the whole stack
        # dipping so the beds are not level.  The first pass stepped them by 10%
        # and the block came back reading as a smooth pebble with faint banding.
        nb = rng.randint(4, 7)
        zz = (P[:, 2] / h + 1.0) * 0.5
        dip = 0.22 * (P[:, 0] / max(r, 1e-6))
        bed = np.floor((zz + dip) * nb)
        step = 0.82 + 0.36 * (((bed * 7919) % 13) / 13.0)
        P[:, :2] *= step[:, None]
        # two JOINT PLANES: the vertical lines that make a crag read as rock and
        # not as a boulder.  A plane cut is a large coherent form; noise is not.
        for k in range(2):
            a = ph[k] * 3.0
            d = P[:, 0] * math.cos(a) + P[:, 1] * math.sin(a)
            cut = np.clip((d - r * rng.uniform(0.05, 0.35)) / (r * 0.22), 0, 1)
            P[:, 0] -= cut * math.cos(a) * r * 0.34
            P[:, 1] -= cut * math.sin(a) * r * 0.34
    # the fine noise LAST and small: it is detail, never form
    amp = 0.045 if strata else 0.16
    n = (np.sin(P[:, 0] * 2.9 + ph[3]) * np.sin(P[:, 1] * 3.3 + ph[4])
         + 0.6 * np.sin(P[:, 2] * 5.1 + ph[5]) * np.sin(P[:, 0] * 4.7 + ph[6]))
    P *= (1.0 + amp * n)[:, None]
    P[:, 2] = np.maximum(P[:, 2], -h * 0.35)
    P += np.array([cx, cy, cz + h * 0.42])[None, :]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in P], [], [tuple(t) for t in Fc])
    uvl = me.uv_layers.new(name="UVMap")
    loops = np.zeros(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", loops)
    fn = np.zeros(len(me.polygons) * 3)
    me.polygons.foreach_get("normal", fn)
    ax = np.argmax(np.abs(fn.reshape(-1, 3)), axis=1)
    pl = np.repeat(ax, 3)
    pv = P[loops]
    u = np.where(pl == 0, pv[:, 1], pv[:, 0])
    v = np.where(pl == 2, pv[:, 1], pv[:, 2])
    uvl.data.foreach_set("uv", (np.stack([u, v], -1) / 3.2).ravel())
    ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
    d = np.ones((len(P), 4))
    # a touch of downward darkening so the block is not one flat grey
    d[:, :3] = np.clip(0.62 + 0.42 * (P[:, 2] - cz) / max(h, 1e-6), 0.4, 1.0)[:, None]
    ca.data.foreach_set("color", d.ravel())
    me.materials.append(mat)
    # FLAT facets on rock, smooth on foliage.  F2's crag treatment already shades
    # its roughened facets flat (11735 flat / 39131 smooth in the valley); a
    # smooth-shaded rock reads as a river-worn pebble however good its texture.
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def marker(col, mat_stone, x, y, z, n, ang):
    p = B.Prop("marker_%d" % n)
    p.cube(11, (x, y, z + 0.07), (1.30, 0.90, 0.16))
    for k in range(n):
        ox = (k - (n - 1) / 2.0) * 0.34
        p.cube(29, (x + math.cos(ang) * ox, y + math.sin(ang) * ox, z + 0.50),
               (0.14, 0.14, 0.84), rz=ang)
    ob = p.finish(col)
    ob.name = ob.data.name = "marker_%d" % n
    ca = B.ensure_col(ob.data) if hasattr(B, "ensure_col") else None
    if ca is None:
        ca = ob.data.color_attributes.new("Col", 'FLOAT_COLOR', 'CORNER')
    d = np.ones((len(ca.data), 4))
    d[:, :3] = 0.92
    ca.data.foreach_set("color", d.ravel())
    ob.data.materials.append(mat_stone)
    return ob


def main():
    t0 = time.time()
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    atlas, atlas_nor = FA.build_atlas()
    tile, tile_nor = FA.build_tile()

    F = L.Field()
    sc = bpy.data.scenes[0]
    sc.name = "lineup"
    col = sc.collection
    B.dusk_rig(sc, F, STYLE)

    grass = B2.pbr_mat("lu_grass", os.path.join(TEXO, "leafy_grass_diff_1k.jpg"),
                       os.path.join(TEXO, "leafy_grass_nor_gl_1k.jpg"),
                       os.path.join(TEXO, "leafy_grass_rough_1k.jpg"),
                       tile=1.0, vcol=True, gain_to=0.46)
    stone = B2.pbr_mat("lu_stone", os.path.join(TEX, "rock_face_03_Diffuse.jpg"),
                       os.path.join(TEX, "rock_face_03_nor_gl.jpg"),
                       os.path.join(TEX, "rock_face_03_Rough.jpg"),
                       tile=0.45, vcol=True, gain_to=0.46)
    rock_strata = B2.pbr_mat("lu_rock_strata",
                             os.path.join(TEXO, "dark_rock_02_diff_1k.jpg"),
                             os.path.join(TEXO, "dark_rock_02_nor_gl_1k.jpg"),
                             os.path.join(TEXO, "dark_rock_02_rough_1k.jpg"),
                             tile=1.0, vcol=True, gain_to=0.46)
    rock_crag = B2.pbr_mat("lu_rock_crag",
                           os.path.join(TEXO, "cliff_side_diff_1k.jpg"),
                           os.path.join(TEXO, "cliff_side_nor_gl_1k.jpg"),
                           os.path.join(TEXO, "cliff_side_rough_1k.jpg"),
                           tile=1.0, vcol=True, gain_to=0.46)
    core_mat, card_mat = BL.materials(atlas, atlas_nor, tile, tile_nor,
                                      suffix="lu", pbr_mat=B2.pbr_mat)

    gp = ground_patch(col, F, LC[0], LC[1])
    gp.data.materials.append(grass)

    px, py = -math.sin(LA), math.cos(LA)
    stats = []
    for gi, (label, dens) in enumerate(DENSITIES):
        t = SPOTS[gi]
        gx = LC[0] + math.cos(LA) * t
        gy = LC[1] + math.sin(LA) * t
        M = BL.Mass("veg_bush_" + label)
        rng = np.random.RandomState(4400 + gi * 131)
        # IDENTICAL cores in all three groups (same seed offsets, same layout):
        # the exhibit has to isolate shell density, so only `dens` may differ
        crng = np.random.RandomState(9001)
        for (u, v) in ((0.0, 0.0), (-2.6, 1.9), (2.5, -1.6)):
            x = gx + math.cos(LA) * u + px * v
            y = gy + math.sin(LA) * u + py * v
            z = float(F.sample(np.array([x]), np.array([y]))[0])
            BL.bush(M, crng, x, y, z, MASS_R * crng.uniform(0.82, 1.14),
                    MASS_H * crng.uniform(0.85, 1.12), nlobe=5)
        killed, total = M.cull_interior()
        M.shade_core()
        n = M.shell(rng, density=dens, big=BIG, fuzz=FUZZ, fuzz_frac=0.30)
        made = M.finish(col, core_mat, card_mat)
        for k, ob in made.items():
            nm = "veg_bush_%s%s" % (label, "_cards" if k == "cards" else "")
            ob.name = ob.data.name = nm
        mz = float(F.sample(np.array([gx + px * 5.2]), np.array([gy + py * 5.2]))[0])
        marker(col, stone, gx + px * 5.2, gy + py * 5.2, mz, gi + 1, LA)
        tris = sum(len(p.vertices) - 2 for p in made["core"].data.polygons)
        stats.append((label, dens, n, killed, total, tris))
        print("  %-6s density %.2f -> %5d cards | core %d/%d faces kept (%d tris)"
              % (label, dens, n, total - killed, total, tris))

    # ---- the rock sample: strata vs jitter, side by side --------------------
    t = SPOTS[3]
    rx = LC[0] + math.cos(LA) * t
    ry = LC[1] + math.sin(LA) * t
    for k, (mat, strata, nm) in enumerate(((rock_strata, True, "rock_strata"),
                                           (rock_crag, False, "rock_jitter"))):
        bx = rx + px * (2.4 - 4.8 * k)
        by = ry + py * (2.4 - 4.8 * k)
        bz = float(F.sample(np.array([bx]), np.array([by]))[0])
        rock_block(col, mat, bx, by, bz - 0.6, 2.0, 3.0, 771 + k, strata=strata,
                   name=nm)
    mz = float(F.sample(np.array([rx + px * 5.2]), np.array([ry + py * 5.2]))[0])
    marker(col, stone, rx + px * 5.2, ry + py * 5.2, mz, 4, LA)

    # ---- 1.45u scale references, one per group ------------------------------
    rp = B.Prop("ref_char")
    for gi in range(4):
        t = SPOTS[gi]
        cx_ = LC[0] + math.cos(LA) * t + px * 3.3
        cy_ = LC[1] + math.sin(LA) * t + py * 3.3
        cz_ = float(F.sample(np.array([cx_]), np.array([cy_]))[0])
        rp.cone(4, (cx_, cy_, cz_ + 0.72), 0.26, 0.26, 1.05, seg=10)
        rp.ico(4, (cx_, cy_, cz_ + 1.24), (0.26, 0.26, 0.26), subd=1)
    ro = rp.finish(col)
    ro.name = ro.data.name = "ref_char"
    ca = ro.data.color_attributes.new("Col", 'FLOAT_COLOR', 'CORNER')
    d = np.ones((len(ca.data), 4))
    d[:, :3] = np.array([0.95, 0.93, 0.88])
    ca.data.foreach_set("color", d.ravel())
    ro.data.materials.append(stone)

    # ---- cameras -----------------------------------------------------------
    cams = {}

    def cam(name, eye, aim, fov=42.0, fit="V"):
        cd = bpy.data.cameras.new("cam_" + name)
        cd.sensor_fit = "VERTICAL" if fit == "V" else "HORIZONTAL"
        if fit == "V":
            cd.angle_y = math.radians(fov)
        else:
            cd.angle_x = math.radians(fov)
        cd.clip_start, cd.clip_end = 0.05, 900.0
        ob = bpy.data.objects.new("cam_" + name, cd)
        sc.collection.objects.link(ob)
        ob.location = Vector(eye)
        ob.rotation_euler = (Vector(aim) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cams[name] = ob
        return ob

    agz = float(F.sample(np.array([LC[0]]), np.array([LC[1]]))[0])
    # stand well back and use a HORIZONTAL fit: the line is 32u long and a 40 deg
    # vertical fit at 24u showed two of the four exhibits
    ax_ = LC[0] + math.cos(LA) * 1.5
    ay_ = LC[1] + math.sin(LA) * 1.5
    ex = ax_ + px * 36.0
    ey = ay_ + py * 36.0
    eg = float(F.sample(np.array([ex]), np.array([ey]))[0])
    cam("lineup", (ex, ey, eg + 11.0), (ax_, ay_, agz + 3.0), fov=82.0, fit="H")
    # THE HONEST ONE: the chase rig's geometry, 35 deg down, looking at group 2
    mx = LC[0] + math.cos(LA) * SPOTS[1]
    my = LC[1] + math.sin(LA) * SPOTS[1]
    mg = float(F.sample(np.array([mx]), np.array([my]))[0])
    d_, pit = 24.0, 0.61
    cam("aerial", (mx - px * d_ * math.cos(pit), my - py * d_ * math.cos(pit),
                   mg + 1.0 + d_ * math.sin(pit)), (mx, my, mg + 1.8), fov=42.0)
    # and a CLOSE one PER DENSITY: leaf detail and coverage are what is judged,
    # and the three only differ where you can see individual clumps
    for gi, (label, _d) in enumerate(DENSITIES):
        gx = LC[0] + math.cos(LA) * SPOTS[gi]
        gy = LC[1] + math.sin(LA) * SPOTS[gi]
        gz = float(F.sample(np.array([gx]), np.array([gy]))[0])
        cam("close_" + label, (gx - px * 11.0 - math.cos(LA) * 2.0,
                               gy - py * 11.0 - math.sin(LA) * 2.0, gz + 5.4),
            (gx, gy, gz + 2.0), fov=40.0)
    sc.camera = cams["lineup"]

    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.resolution_percentage = 100
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
    except Exception:
        pass

    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
               for o in sc.objects if o.type == "MESH")
    print("  line-up: %d meshes, %d tris" % (
        len([o for o in sc.objects if o.type == "MESH"]), tris))
    for (label, dens, n, killed, total, ct) in stats:
        print("    %-6s %.2f cards/u2  %5d cards  core %d tris" % (label, dens, n, ct))

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("SAVED %s (%.1fs)" % (OUT_BLEND, time.time() - t0))

    os.makedirs(QA, exist_ok=True)
    import contextlib
    import io
    shots = [("lineup", ""), ("aerial", "_aerial")]
    shots += [("close_%s" % l, "_close_%s" % l) for l, _ in DENSITIES]
    for nm, suffix in shots:
        sc.camera = cams[nm]
        sc.render.filepath = os.path.join(QA, "foliage_lineup%s.png" % suffix)
        t1 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.render.render(write_still=True, scene=sc.name)
        print("RENDERED %s (%.1fs)" % (sc.render.filepath, time.time() - t1))
    density_sheet()


def density_sheet():
    """Stack the three close shots into ONE artifact and delete the singles.

    The density ruling is a COMPARISON, and three 2 MB frames that can only be
    compared by flicking between tabs is the wrong shape for it.  Crops are
    FULL RESOLUTION — downscaling the sheet threw away the very clump detail the
    sheet exists to show.  Each band is tagged with 1/2/3 white ticks, the same
    counting convention as the ground markers in the scene.
    """
    y0, y1 = 150, 640
    bands = []
    for label, dens in DENSITIES:
        fp = os.path.join(QA, "foliage_lineup_close_%s.png" % label)
        im = bpy.data.images.load(fp)
        w, h = im.size
        a = np.zeros(w * h * 4, np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(h, w, 4)[::-1]                 # to y-DOWN
        bands.append(a[y0:y1])
        bpy.data.images.remove(im)
    sheet = np.concatenate(bands, axis=0)
    bh = y1 - y0
    for i in range(len(bands)):                      # i+1 ticks per band
        for k in range(i + 1):
            sheet[i * bh + 14:i * bh + 34, 16 + k * 28:38 + k * 28] = 1.0
    out = os.path.join(QA, "foliage_lineup_density.png")
    FA._write(out, sheet[::-1], "PNG")
    for label, _ in DENSITIES:
        fp = os.path.join(QA, "foliage_lineup_close_%s.png" % label)
        if os.path.exists(fp):
            os.remove(fp)
    print("SHEET %s (%.1f MB)" % (out, os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
