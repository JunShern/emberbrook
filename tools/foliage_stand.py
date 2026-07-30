"""foliage_stand.py — a REGION-SCALE stand preview, off the valley pipeline.

  Blender --python-exit-code 1 -b --factory-startup -P tools/foliage_stand.py

The line-up answers "is a bush mass good?".  This answers the two questions the
line-up cannot, and answers them without writing a byte the geography session
owns:

  1. WHAT DOES A WHOLE STAND LOOK LIKE at the follow camera's own geometry, with
     the region's card sizes (a clump card is one TREETOP at this scale, not one
     leaf cluster) and the region's lobe spacing?
  2. WHAT DOES IT COST?  `valley_veg.DENSITY` multiplies over ~9 000 square units
     of stand in the real region, so the card count has to be measured on a
     synthetic stand of known area and extrapolated BEFORE the pipeline is
     touched — not discovered in a 28 MB GLB afterwards.

It also stands the new meadow albedo and a strata-crag slab in the same frame,
so the three material upgrades are judged together under one light.

Writes docs/qa/overworld/foliage_stand{,_aerial}.png and prints the extrapolation.
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
import overworld3_build as B3
import bushlang as BL
import foliage_atlas as FA
import valley_veg as VV
import foliage_lineup as FL

ROOT = B3.ROOT
TEXO = os.path.join(ROOT, "tools/textures/overworld")
OUT_BLEND = os.path.join(ROOT, "tools/blends/foliage-stand.blend")
QA = os.path.join(ROOT, "docs/qa/overworld")
STYLE = "f2"

CTR = (6.0, 4.0)                 # a clear patch of the round-1 field
STAND_R = (17.0, 12.0)           # the synthetic stand's half-extents
CELL = 1.25                      # same as the region's zone grid


class FakeZG:
    """The three things `_lobe_sites` needs from a ZoneGrid: BX, BY, wsample."""

    def __init__(self, cx, cy, hx, hy, cell=CELL):
        xs = np.arange(cx - hx - 6, cx + hx + 6, cell)
        ys = np.arange(cy - hy - 6, cy + hy + 6, cell)
        self.BX, self.BY = np.meshgrid(xs, ys, indexing="ij")
        self.x0, self.y0, self.cell = float(xs[0]), float(ys[0]), cell

    def wsample(self, A, x, y):
        fx = np.clip((np.asarray(x, float) - self.x0) / self.cell, 0,
                     A.shape[0] - 1.001)
        fy = np.clip((np.asarray(y, float) - self.y0) / self.cell, 0,
                     A.shape[1] - 1.001)
        i, j = fx.astype(int), fy.astype(int)
        tx, ty = fx - i, fy - j
        return (A[i, j] * (1 - tx) * (1 - ty) + A[i + 1, j] * tx * (1 - ty)
                + A[i, j + 1] * (1 - tx) * ty + A[i + 1, j + 1] * tx * ty)


def main():
    t0 = time.time()
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    atlas, atlas_nor = FA.build_atlas()
    tile, tile_nor = FA.build_tile()
    md, mn = VV.meadow_maps()

    F = L.Field()
    sc = bpy.data.scenes[0]
    sc.name = "stand"
    col = sc.collection
    B.dusk_rig(sc, F, STYLE)

    meadow = B2.pbr_mat("st_meadow", md, mn,
                        os.path.join(TEXO, "leafy_grass_rough_1k.jpg"),
                        tile=1.0, vcol=True, gain_to=0.46)
    rock = B2.pbr_mat("st_rock", os.path.join(TEXO, VV.ROCK_SET + "_diff_1k.jpg"),
                      os.path.join(TEXO, VV.ROCK_SET + "_nor_gl_1k.jpg"),
                      os.path.join(TEXO, VV.ROCK_SET + "_rough_1k.jpg"),
                      tile=1.0, vcol=True, gain_to=0.46)
    core_mat, card_mat = BL.materials(atlas, atlas_nor, tile, tile_nor,
                                      suffix="valley", pbr_mat=B2.pbr_mat)

    gp = FL.ground_patch(col, F, CTR[0], CTR[1], half=(34.0, 26.0))
    gp.data.materials.append(meadow)

    # ---- a synthetic stand: an irregular blob, tapering at its rim -----------
    zg = FakeZG(CTR[0], CTR[1], STAND_R[0], STAND_R[1])
    dx = (zg.BX - CTR[0]) / STAND_R[0]
    dy = (zg.BY - CTR[1]) / STAND_R[1]
    a = np.arctan2(dy, dx)
    lobed = 1.0 + 0.22 * np.sin(3 * a + 0.7) + 0.13 * np.sin(5 * a - 1.4)
    mask = np.hypot(dx, dy) < lobed
    area = float(mask.sum()) * CELL * CELL
    soft = O3._box(mask.astype(float), 3)
    edge = np.clip(soft * 1.45, 0.0, 1.0)
    rng = np.random.RandomState(90210)
    sites = VV._lobe_sites(zg, soft > 0.10, edge, rng)
    M, killed, total, ncards = VV.stand_mass("veg_canopy_sample", F, sites, rng)
    objs = M.finish(col, core_mat, card_mat)
    for key, ob in objs.items():
        ob.name = ob.data.name = "veg_canopy_sample" + ("_cards" if key == "cards" else "")

    # ---- a strata crag slab in the same frame -------------------------------
    for k in range(3):
        bx = CTR[0] - 27.0 + k * 5.4
        by = CTR[1] - 17.0 - k * 2.2
        bz = float(F.sample(np.array([bx]), np.array([by]))[0])
        FL.rock_block(col, rock, bx, by, bz - 1.2, 3.4 - 0.5 * k, 5.2 - 0.7 * k,
                      331 + k, strata=True, name="rock_strata_%d" % k)

    # ---- 1.45u scale reference at the stand edge ---------------------------
    rp = B.Prop("ref_char")
    for (ox, oy) in ((CTR[0], CTR[1] - STAND_R[1] - 3.0),
                     (CTR[0] - 22.0, CTR[1] - 13.0)):
        oz = float(F.sample(np.array([ox]), np.array([oy]))[0])
        rp.cone(4, (ox, oy, oz + 0.72), 0.26, 0.26, 1.05, seg=10)
        rp.ico(4, (ox, oy, oz + 1.24), (0.26, 0.26, 0.26), subd=1)
    ro = rp.finish(col)
    ro.name = ro.data.name = "ref_char"
    ca = ro.data.color_attributes.new("Col", 'FLOAT_COLOR', 'CORNER')
    d = np.ones((len(ca.data), 4))
    d[:, :3] = 0.93
    ca.data.foreach_set("color", d.ravel())
    ro.data.materials.append(rock)

    # ---- the numbers, and the extrapolation --------------------------------
    core_tris = int(len(M._F))
    card_tris = ncards * 2
    verts = core_tris and len(np.unique(M._F))
    print("  stand: %.0f u2 footprint, %d lobes" % (area, len(sites)))
    print("  core %d/%d tris kept (%.0f%% culled), %d cards (%.2f/u2 of footprint)"
          % (core_tris, total, 100.0 * killed / max(total, 1), ncards,
             ncards / max(area, 1)))
    # bytes the GLB will pay: POSITION+NORMAL+COLOR_0 (12 each) + UV (8) + idx
    for label, a_ in (("this sample", area), ("valley canopy stands ~9000 u2", 9000.0)):
        sc_ = a_ / max(area, 1)
        nc = ncards * sc_
        ct = core_tris * sc_
        nv = nc * 4 + ct * 0.55
        mb = (nv * (12 + 12 + 12 + 8) + (nc * 2 + ct) * 3 * 4) / 1e6
        print("    %-32s %7.0f cards %7.0f core tris -> ~%.2f MB geometry"
              % (label, nc, ct, mb))

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

    gz0 = float(F.sample(np.array([CTR[0]]), np.array([CTR[1]]))[0])
    # THE CHASE RIG: 42 deg, dist 34, pitch 0.61 rad — the game's own camera
    d_, pit = 34.0, 0.61
    cam("aerial", (CTR[0], CTR[1] - d_ * math.cos(pit), gz0 + 1.0 + d_ * math.sin(pit)),
        (CTR[0], CTR[1], gz0 + 2.0), fov=42.0)
    cam("stand", (CTR[0] - 30.0, CTR[1] - 40.0, gz0 + 20.0),
        (CTR[0] - 4.0, CTR[1], gz0 + 3.0), fov=60.0, fit="H")
    sc.camera = cams["stand"]
    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.image_settings.file_format = "PNG"
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
    except Exception:
        pass

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("SAVED %s (%.1fs)" % (OUT_BLEND, time.time() - t0))

    import contextlib
    import io
    for nm, suffix in (("stand", ""), ("aerial", "_aerial")):
        sc.camera = cams[nm]
        sc.render.filepath = os.path.join(QA, "foliage_stand%s.png" % suffix)
        t1 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.render.render(write_still=True, scene=sc.name)
        print("RENDERED %s (%.1fs)" % (sc.render.filepath, time.time() - t1))


if __name__ == "__main__":
    main()
