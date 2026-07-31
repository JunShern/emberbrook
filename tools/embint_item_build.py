#!/usr/bin/env python3
"""emb-item-int -- THE VILLAGE STORE.  A farmhouse that sells things.

CANON THIS ROOM SERVES
----------------------
The map says only this: *"village general store -- preserves, twine, lamp
oil"*, resident `shopkeep`, standing on the square's east side.  And
`docs/MECHANICS.md` says there are NO shops in Emberbrook in Chapter One --
the festival runs on gifts, by LAW -- which is the most useful constraint in
the brief, because it settles what the room IS: not a shop counter with a
till, but the ground floor of a working farmhouse where the village's stores
happen to live and where the ledger is a BORROW BOOK.

Dellhollow's item shop is a chandlery: rope, tar, oil, lamps, the trade of a
river town, and it shares its shell and its camera with the weapon and armour
shops (`tools/item_int_build.py` is explicitly "the SHOP ARCHETYPE... the same
room with a different skin").  This is not that room and does not use that
shell.  A farm-village store is a HOUSE: it has a cold larder, a lean-to, a
family living upstairs and a trapdoor for getting sacks to them.

THE PLAN, AND WHY IT IS NOT A BOX
---------------------------------
Three spaces at three temperatures, which is the whole idea:

  THE SHOP      the middle, warm, lamplit, timber, the counter across it.
  THE LARDER    a stone alcove projecting NORTH out of the back wall, TWO
                steps DOWN (-0.34) into the old dairy: cold, blue, slate
                shelves, and every preserve in the village on them.
  THE LEAN-TO   projecting EAST through a post-and-beam opening, one step
                DOWN (-0.18), half outdoors under a glazed roof: lamp oil,
                roots, the heavy things nobody wants to carry far.  Daylight
                lands here and nowhere else.

Above all three, the ceiling is the FAMILY'S FLOOR -- joists and boards, not a
lid -- with a real TRAPDOOR and a rope hoist, because that is how the sacks get
up to the people who live over the shop.

CAMERA PERSONALITY: the deep one.  The inn is wide and low, the bakery is a
close working lens, the cottage is a tight held breath; this is the only room
of the four built for AXIAL RECESSION -- fov 34 at pitch 15, looking down the
length of the shop so the cold larder sits at the far end of a warm corridor
and the lean-to's daylight cuts across it.

FORMAT: FF9 cutaway.  SCALE: character 1.70, door 2.15, counter 1.05.

Run headless (ALWAYS -b --python-exit-code 1):
    Blender -b --python-exit-code 1 -P tools/embint_item_build.py -- \
        --out tools/blends/interiors/emb-item-int.blend \
        --render docs/qa/interiors/emb-item-int_v1.png --samples 160
"""
import bpy, math, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import embint_lib as L

CM = L.CM
OUTBLEND = "tools/blends/interiors/emb-item-int.blend"
SEED = 20260804

# ============================================================== the plan ===
XL, XR = 0.00, 7.20
YF, YB = 0.00, 6.20
WH = 3.35
CEIL = 3.35
THICK = 0.24

# the larder, projecting north out of the back wall
AL_X0, AL_X1, AL_Y1 = 1.20, 3.60, 8.00
AL_Z = -0.34

# the lean-to, projecting east through a post-and-beam opening
LT_X1 = 9.60
LT_Y0, LT_Y1 = 1.00, 4.40
LT_Z = -0.18
LT_EAVE, LT_HIGH = 2.35, 3.05

# the door, in the back wall, onto the square
DOOR_X0, DOOR_X1 = 5.15, 6.35
DOOR_TOP = 2.15
# and the shop window beside it
WIN_X0, WIN_X1 = 4.05, 4.85
WIN_SILL, WIN_TOP = 1.00, 2.20

# the counter: an L across the shop, facing the door
CT_X0, CT_X1, CT_Y0, CT_Y1, CT_H = 1.55, 4.55, 2.55, 3.25, 1.05
CT_RET_Y1 = 4.60                    # the return leg, running north

# the trapdoor to the family's floor
TRAP = (5.30, 6.45, 1.20, 2.30)


def deg(a):
    return math.radians(a)


# =============================================================== the shell ==

def build_floor():
    c = L.coll("SHELL")
    L.floor_planks("shop", (YF - 0.02, YB + 0.02),
                   L.rects_yfn([(YF - 0.02, YB + 0.02, XL - 0.02, XR + 0.02)]),
                   z=0.0, c=c, mat="mat_int_floor", mat_alt="mat_int_floor_pale",
                   alt=0.12, dir_="x", w=(0.17, 0.245), run=(2.0, 3.8))
    L.floor_void("floor_void_shop", XL, XR, YF, YB, 0.0, c=c)

    # THE LARDER: flagstone, and cold.  Two steps down, because the dairy was
    # dug into the bank before the shop was ever a shop.
    L.prism("walk_floor_larder",
            [(AL_X0 - 0.04, YB - 0.30), (AL_X1 + 0.04, YB - 0.30),
             (AL_X1 + 0.04, AL_Y1 - 0.06), (AL_X0 - 0.04, AL_Y1 - 0.06)],
            AL_Z - 0.06, AL_Z, "mat_int_stone", c, bevel=0.010)
    for k in range(2):
        z = AL_Z + 0.17 * (k + 1)
        y = YB - 0.28 - 0.28 * k
        L.box("walk_step_larder_%02d" % k, ((AL_X0 + AL_X1) / 2, y, z - 0.030),
              (0.80, 0.14, 0.030), "mat_int_stone", c, bevel=0.010, tex_off=L.toff())
        L.box("step_larder_%02d_riser" % k, ((AL_X0 + AL_X1) / 2, y - 0.14, z - 0.115),
              (0.79, 0.020, 0.085), "mat_int_stone", c, bevel=0.004)

    # THE LEAN-TO: brick on earth, one step down, and it is the only floor in
    # the room daylight ever lands on.
    L.prism("walk_floor_leanto",
            [(XR - 0.04, LT_Y0 + 0.04), (LT_X1 - 0.06, LT_Y0 + 0.04),
             (LT_X1 - 0.06, LT_Y1 - 0.04), (XR - 0.04, LT_Y1 - 0.04)],
            LT_Z - 0.06, LT_Z, "mat_int_hearth", c, bevel=0.008)
    L.box("walk_step_leanto", (XR - 0.16, (LT_Y0 + LT_Y1) / 2, LT_Z / 2 - 0.024),
          (0.16, (LT_Y1 - LT_Y0) / 2 - 0.24, 0.030), "mat_int_stone", c, bevel=0.010,
          tex_off=L.toff())
    L.box("step_leanto_riser", (XR + 0.01, (LT_Y0 + LT_Y1) / 2, LT_Z / 2 - 0.02),
          (0.026, (LT_Y1 - LT_Y0) / 2 - 0.24, abs(LT_Z) / 2), "mat_int_beam", c,
          bevel=0.004)


def build_walls():
    c = "SHELL"
    # BACK WALL, in two runs either side of the larder mouth: door + window
    fb = L.WallFrame((XR, YB), (XL, YB), inward=(0, 1))     # u = XR - x
    L.wall_run("wBack", fb, WH, c=c, style="plaster", wain=1.00, thick=THICK,
               openings=[(XR - DOOR_X1, XR - DOOR_X0, DOOR_TOP),
                         (XR - WIN_X1, XR - WIN_X0, WIN_TOP),
                         (XR - AL_X1, XR - AL_X0, 2.10)])
    L.opening_frame("doorframe", fb, XR - DOOR_X1, XR - DOOR_X0, DOOR_TOP, c=c)
    L.opening_frame("winframe", fb, XR - WIN_X1, XR - WIN_X0, WIN_TOP, c=c,
                    sill=WIN_SILL)
    L.opening_frame("larderframe", fb, XR - AL_X1, XR - AL_X0, 2.10, c=c,
                    mat="mat_int_stone")

    # WEST WALL: the deep shelving side, and the one wall with nothing on it
    fw = L.WallFrame((XL, YB), (XL, YF), inward=(-1, 0))
    L.wall_run("wWest", fw, WH, c=c, style="plaster", wain=1.00, thick=THICK)

    # EAST WALL, in two runs either side of the lean-to opening
    fe = L.WallFrame((XR, YF), (XR, YB), inward=(1, 0))
    L.wall_run("wEast", fe, WH, c=c, style="plaster", wain=1.00, thick=THICK,
               openings=[(LT_Y0, LT_Y1, 2.32)])
    # the post-and-beam of the opening, and the half-wall with its gate
    for yy in (LT_Y0, LT_Y1):
        L.box("lt_post_%.1f" % yy, (XR, yy, 1.16), (0.105, 0.105, 1.16),
              "mat_int_beam", L.coll("SHELL"), bevel=0.012, tex_off=L.toff())
    L.box("lt_bressummer", (XR, (LT_Y0 + LT_Y1) / 2, 2.40),
          (0.115, (LT_Y1 - LT_Y0) / 2, 0.145), "mat_int_beam", L.coll("SHELL"),
          bevel=0.014, tex_off=L.toff())
    L.box("lt_halfwall", (XR, LT_Y0 + 0.86, 0.44), (0.075, 0.72, 0.44),
          "mat_int_paint_green", L.coll("SHELL"), bevel=0.010, tex_off=L.toff())
    L.box("lt_halfwall_cap", (XR, LT_Y0 + 0.86, 0.90), (0.100, 0.74, 0.030),
          "mat_int_wood", L.coll("SHELL"), bevel=0.012, tex_off=L.toff())

    # THE LARDER's three stone walls
    for tag, p0, p1, inw in (("aW", (AL_X0, YB - 0.30), (AL_X0, AL_Y1), (-1, 0)),
                             ("aE", (AL_X1, AL_Y1), (AL_X1, YB - 0.30), (1, 0)),
                             ("aB", (AL_X1, AL_Y1), (AL_X0, AL_Y1), (0, 1))):
        fr = L.WallFrame(p0, p1, inward=inw)
        L.wall_run(tag, fr, 2.28, c=c, style="stone", thick=0.30, studs=False,
                   plate=False)

    # THE LEAN-TO's two walls (the third side is the shop)
    for tag, p0, p1, inw, h in (("ltS", (XR, LT_Y0), (LT_X1, LT_Y0), (0, -1), LT_HIGH),
                                ("ltN", (LT_X1, LT_Y1), (XR, LT_Y1), (0, 1), LT_HIGH)):
        fr = L.WallFrame(p0, p1, inward=inw)
        L.wall_run(tag, fr, h, c=c, style="board", thick=0.20,
                   board_mat="mat_int_plank", plate_z=h - 0.12)

    nw = L.box("shadow_nearwall", ((XL + XR) / 2, YF - THICK / 2 - 0.02, WH / 2),
               ((XR - XL) / 2 + THICK, THICK / 2, WH / 2), "mat_int_plaster",
               L.coll("SHELL"), bevel=0)
    L.hide_from_camera(nw)
    nw2 = L.box("shadow_nearwall_lt", ((XR + LT_X1) / 2, LT_Y0 - 0.30, 1.20),
                ((LT_X1 - XR) / 2, 0.10, 1.20), "mat_int_plaster", L.coll("SHELL"),
                bevel=0)
    L.hide_from_camera(nw2)


def build_ceiling():
    """The family's floor.  Joists, boards, a trapdoor and a hoist."""
    c = L.coll("SHELL")
    lid = L.box("shadow_ceiling", ((XL + XR) / 2, (YF + YB) / 2, CEIL + 0.16),
                ((XR - XL) / 2 + THICK, (YB - YF) / 2 + THICK, 0.08), "mat_int_plank",
                c, bevel=0)
    L.hide_from_camera(lid)
    L.roof_backing("roofvoid", XL - 0.5, LT_X1 + 0.5, YF - 0.5, AL_Y1 + 0.5, 3.86, c=c)

    y = YF
    i = 0
    while y < YB - 0.02:
        w = min(0.235, YB - y)
        segs = [(XL - 0.06, XR + 0.06)]
        if TRAP[2] - 0.02 < y + w / 2 < TRAP[3] + 0.02:
            segs = [(XL - 0.06, TRAP[0]), (TRAP[1], XR + 0.06)]
        for (a, b) in segs:
            if b - a < 0.05:
                continue
            ob = L.box("ceilboard_%02d_%.2f" % (i, a), ((a + b) / 2, y + w / 2,
                                                        CEIL - 0.03),
                       ((b - a) / 2, w / 2 - 0.004, 0.028), "mat_int_beam", c,
                       bevel=0.004, tex_off=L.toff())
            if y + w / 2 < -0.20:
                L.hide_from_camera(ob)
        y += w
        i += 1
    # joists running ACROSS the shop's length, so they read as the depth ladder
    yj, i = 0.34, 0
    while yj < YB - 0.05:
        segs = [(XL - 0.05, XR + 0.05)]
        if TRAP[2] - 0.05 < yj < TRAP[3] + 0.05:
            segs = [(XL - 0.05, TRAP[0]), (TRAP[1], XR + 0.05)]
        for (a, b) in segs:
            L.box("joist_%02d_%.2f" % (i, a), ((a + b) / 2, yj, CEIL - 0.115),
                  ((b - a) / 2, 0.048, 0.080), "mat_int_beam", c, bevel=0.006,
                  tex_off=L.toff())
        yj += 0.40
        i += 1
    # the summer beam down the middle, on two posts
    for k in range(4):
        y0 = YF + (YB - YF) * k / 4.0
        y1 = YF + (YB - YF) * (k + 1) / 4.0
        L.box("summer_%d" % k, (3.40, (y0 + y1) / 2, CEIL - 0.26),
              (0.120, (y1 - y0) / 2, 0.145), "mat_int_beam", c, bevel=0.012,
              tex_off=L.toff())
    # the summer beam is carried on CORBELS at the walls, not on a post in the
    # middle of the room: a 3.0 m post at x 3.40, y 1.55 stood two metres from
    # the lens and put a black bar straight down the centre of the frame.
    for yy in (YF + 0.10, YB - 0.10):
        L.box("summer_corbel_%.1f" % yy, (3.40, yy, CEIL - 0.44), (0.155, 0.16, 0.115),
              "mat_int_beam", c, bevel=0.010, tex_off=L.toff())

    # THE TRAPDOOR, open, with the hoist rope hanging through it
    L.box("trap_trim_s", ((TRAP[0] + TRAP[1]) / 2, TRAP[2], CEIL - 0.115),
          ((TRAP[1] - TRAP[0]) / 2, 0.070, 0.120), "mat_int_beam", c, bevel=0.010,
          tex_off=L.toff())
    L.box("trap_trim_n", ((TRAP[0] + TRAP[1]) / 2, TRAP[3], CEIL - 0.115),
          ((TRAP[1] - TRAP[0]) / 2, 0.070, 0.120), "mat_int_beam", c, bevel=0.010,
          tex_off=L.toff())
    L.box("trap_leaf", (TRAP[0] - 0.10, (TRAP[2] + TRAP[3]) / 2, CEIL + 0.52),
          (0.030, (TRAP[3] - TRAP[2]) / 2 - 0.02, 0.52), "mat_int_plank", c,
          rot=(0, deg(-14), 0), bevel=0.008, tex_off=L.toff())
    L.cyl("hoist_beam", ((TRAP[0] + TRAP[1]) / 2, (TRAP[2] + TRAP[3]) / 2,
                         CEIL + 0.70),
          0.070, 1.30, "mat_int_beam", c, axis="X", verts=10)
    L.cyl("hoist_rope", ((TRAP[0] + TRAP[1]) / 2 - 0.18, (TRAP[2] + TRAP[3]) / 2,
                         1.68),
          0.016, 3.10, "mat_int_bowlwood", c, verts=8)
    L.cyl("hoist_hook", ((TRAP[0] + TRAP[1]) / 2 - 0.18, (TRAP[2] + TRAP[3]) / 2,
                         0.20),
          0.030, 0.20, "mat_int_iron", c, verts=10)

    # THE LEAN-TO's glazed roof: the room's daylight, and its own shape
    for k in range(6):
        t = k / 5.0
        x = XR + (LT_X1 - XR) * t
        z = LT_HIGH + (LT_EAVE - LT_HIGH) * t
        L.box("lt_rafter_%02d" % k, (x, (LT_Y0 + LT_Y1) / 2, z - 0.06),
              (0.055, (LT_Y1 - LT_Y0) / 2, 0.075), "mat_int_beam", c, bevel=0.008,
              tex_off=L.toff())
    ang = math.atan2(LT_HIGH - LT_EAVE, LT_X1 - XR)
    Lg = math.hypot(LT_X1 - XR, LT_HIGH - LT_EAVE)
    L.box("lt_glazing", ((XR + LT_X1) / 2, (LT_Y0 + LT_Y1) / 2,
                         (LT_EAVE + LT_HIGH) / 2 + 0.02),
          (Lg / 2, (LT_Y1 - LT_Y0) / 2, 0.012), "mat_glass_dusk", c,
          rot=(0, ang, 0), bevel=0)


# ================================================================ the trade ==

def build_counter():
    """An L of counter, facing the door.  On it: the BORROW BOOK, because
    Emberbrook's festival runs on gifts and nobody in this village has ever
    paid for a jar of anything in their life."""
    c = L.coll("PROPS")
    cx, cy = (CT_X0 + CT_X1) / 2, (CT_Y0 + CT_Y1) / 2
    L.box("ct_top", (cx, cy, CT_H - 0.035), ((CT_X1 - CT_X0) / 2, (CT_Y1 - CT_Y0) / 2,
                                             0.035),
          "mat_int_floor_pale", c, bevel=0.014, tex_off=L.toff())
    L.box("ct_front", (cx, CT_Y0 + 0.03, (CT_H - 0.08) / 2),
          ((CT_X1 - CT_X0) / 2, 0.032, (CT_H - 0.08) / 2), "mat_int_paint_green", c,
          bevel=0.008, tex_off=L.toff())
    for sx in (CT_X0 + 0.06, cx, CT_X1 - 0.06):
        L.box("ct_stile_%.2f" % sx, (sx, CT_Y0 + 0.012, (CT_H - 0.08) / 2),
              (0.062, 0.040, (CT_H - 0.08) / 2), "mat_int_paint_red", c, bevel=0.008)
    # the return leg, running north toward the larder
    L.box("ct_ret_top", (CT_X1 - 0.35, (CT_Y1 + CT_RET_Y1) / 2, CT_H - 0.035),
          (0.35, (CT_RET_Y1 - CT_Y1) / 2, 0.035), "mat_int_floor_pale", c, bevel=0.014,
          tex_off=L.toff())
    L.box("ct_ret_front", (CT_X1 - 0.03, (CT_Y1 + CT_RET_Y1) / 2, (CT_H - 0.08) / 2),
          (0.032, (CT_RET_Y1 - CT_Y1) / 2, (CT_H - 0.08) / 2), "mat_int_paint_green",
          c, bevel=0.008, tex_off=L.toff())
    L.box("ct_shelf", (cx, cy, 0.42), ((CT_X1 - CT_X0) / 2 - 0.06,
                                       (CT_Y1 - CT_Y0) / 2 - 0.06, 0.018),
          "mat_int_plank", c, bevel=0.006, tex_off=L.toff())

    # THE BORROW BOOK: open, with a pencil on a string and a bootlace as a
    # bookmark.  Not a till.  There is no till in this village.
    L.box("borrowbook", (CT_X0 + 0.72, cy + 0.08, CT_H + 0.022), (0.24, 0.18, 0.022),
          "mat_int_paper", c, rot=(0, 0, deg(-7)), bevel=0.004)
    L.box("borrowbook_spine", (CT_X0 + 0.72, cy + 0.08, CT_H + 0.010),
          (0.245, 0.185, 0.014), "mat_int_oilskin", c, rot=(0, 0, deg(-7)), bevel=0.006)
    L.cyl("borrow_pencil", (CT_X0 + 1.02, cy - 0.14, CT_H + 0.010), 0.006, 0.16,
          "mat_int_bowlwood", c, axis="X", verts=6, rot=(0, 0, deg(22)), bevel=0)
    L.cyl("borrow_string", (CT_X0 + 1.02, cy - 0.02, CT_H + 0.006), 0.003, 0.34,
          "mat_int_bowlwood", c, axis="Y", verts=5, bevel=0)
    # the scale, its pan worn bright where a thumb steadies it every day
    L.box("scale_base", (CT_X1 - 0.52, cy - 0.06, CT_H + 0.024), (0.15, 0.10, 0.024),
          "mat_int_iron", c, bevel=0.008)
    L.cyl("scale_post", (CT_X1 - 0.52, cy - 0.06, CT_H + 0.15), 0.013, 0.23,
          "mat_int_brass", c, verts=8, bevel=0)
    L.box("scale_beam", (CT_X1 - 0.52, cy - 0.06, CT_H + 0.265), (0.18, 0.012, 0.008),
          "mat_int_brass", c, rot=(0, deg(-5), 0), bevel=0)
    for s in (-1, 1):
        L.lathe("scale_pan_%d" % (s > 0), [(0.0, 0.0), (0.080, 0.012), (0.084, 0.020)],
                (CT_X1 - 0.52 + s * 0.17, cy - 0.06, CT_H + 0.175 - s * 0.016),
                L.M("mat_int_brass"), c, segments=14, thickness=0.003)
    # THE TWINE, on its spindle, with the cut end tucked back under the last turn
    L.cyl("twine_spindle", (CT_X0 + 0.24, cy + 0.16, CT_H + 0.13), 0.012, 0.28,
          "mat_int_iron", c, axis="X", verts=8)
    L.lathe("twine_ball", [(0.0, 0.0), (0.105, 0.03), (0.115, 0.10), (0.095, 0.155),
                           (0.0, 0.175)],
            (CT_X0 + 0.24, cy + 0.16, CT_H + 0.045), L.M("mat_int_linen"), c,
            segments=16)
    L.cyl("twine_end", (CT_X0 + 0.40, cy + 0.05, CT_H + 0.06), 0.004, 0.26,
          "mat_int_linen", c, axis="X", verts=5, rot=(0, deg(24), deg(-36)), bevel=0)
    # a wreath half made, for tonight
    for k in range(11):
        a = deg(360) * k / 11.0
        L.cyl("wreath_%02d" % k, (CT_X1 - 1.15 + 0.20 * math.cos(a),
                                  cy + 0.14 + 0.20 * math.sin(a), CT_H + 0.030),
              0.026, 0.14, "mat_int_felt", c, axis="X", verts=6,
              rot=(0, 0, a + deg(90)), bevel=0.004)
    for k in range(4):
        L.sphere("wreath_berry_%d" % k, (CT_X1 - 1.15 + 0.20 * math.cos(deg(70 * k)),
                                         cy + 0.14 + 0.20 * math.sin(deg(70 * k)),
                                         CT_H + 0.070), 0.022, "mat_int_paint_red", c,
                 segs=8, rings=5)


def build_shelving():
    """The west wall, floor to joists, and the harvest that has come in this
    week: apples half sorted, and a rejects basket that is winning."""
    c = L.coll("PROPS")
    fw = L.WallFrame((XL, YB), (XL, YF), inward=(-1, 0))
    for k, z in enumerate((0.52, 1.02, 1.52, 2.02, 2.52)):
        fw.box("shelf_%d" % k, (YB - YF) / 2, -0.20, z, YB - YF - 0.50, 0.40, 0.026,
               L.M("mat_int_plank"), c, bevel=0.006)
        for j in range(9):
            u = 0.55 + j * 0.58
            if u > YB - 0.4:
                break
            p = fw.w(u, -0.20, z + 0.013)
            if (j + k) % 3 == 0:
                L.lathe("shelf_crock_%d_%d" % (k, j),
                        [(0.0, 0.0), (0.070, 0.008), (0.078, 0.15), (0.056, 0.215),
                         (0.062, 0.235)],
                        p, L.M("mat_int_crock" if (j + k) % 2 else "mat_int_crock_blue"),
                        c, segments=14, thickness=0.005)
            elif (j + k) % 3 == 1:
                L.box("shelf_box_%d_%d" % (k, j), (p[0], p[1], p[2] + 0.09),
                      (0.10, 0.13, 0.09), "mat_int_plank", c, rot=(0, 0, L.jit(0.10)),
                      bevel=0.008, tex_off=L.toff())
            else:
                for q in range(3):
                    L.lathe("shelf_jar_%d_%d_%d" % (k, j, q),
                            [(0.0, 0.0), (0.048, 0.006), (0.052, 0.11), (0.040, 0.145),
                             (0.045, 0.155)],
                            (p[0], p[1] - 0.16 + q * 0.16, p[2]),
                            L.M("mat_int_glassjug"), c, segments=12, thickness=0.004)
    # the ladder that reaches the top shelf, hooked on a rail
    L.ladder("shopladder", 0.62, 3.60, 0.0, 2.62, yaw=deg(90), lean=0.30, w=0.44,
             c="PROPS")

    # THE APPLES.  Half sorted: the good ones in the bushel, the bad ones in a
    # basket that is fuller than anybody wants to admit.
    L.lathe("bushel", [(0.0, 0.0), (0.30, 0.02), (0.34, 0.30), (0.32, 0.34)],
            (2.05, 1.35, 0.0), L.M("mat_int_bowlwood"), c, segments=18, thickness=0.014)
    for k in range(14):
        a = deg(137.5 * k)
        r = 0.24 * math.sqrt((k + 1) / 14.0)
        L.sphere("apple_%02d" % k, (2.05 + r * math.cos(a), 1.35 + r * math.sin(a),
                                    0.30 + (k % 3) * 0.045),
                 0.052, "mat_int_paint_red" if k % 4 else "mat_int_paint_green", c,
                 segs=10, rings=6)
    L.lathe("rejects", [(0.0, 0.0), (0.22, 0.02), (0.25, 0.22), (0.23, 0.25)],
            (2.85, 1.05, 0.0), L.M("mat_int_bowlwood"), c, segments=16, thickness=0.012)
    for k in range(9):
        a = deg(137.5 * k)
        r = 0.16 * math.sqrt((k + 1) / 9.0)
        L.sphere("reject_%02d" % k, (2.85 + r * math.cos(a), 1.05 + r * math.sin(a),
                                     0.22 + (k % 2) * 0.04),
                 0.048, "mat_int_bowlwood", c, segs=8, rings=5)
    # pumpkins, in a touching group at the counter's foot (SCENE-LAYOUT: never
    # scattered singletons)
    for k, (px, py, r) in enumerate(((1.25, 1.85, 0.20), (1.58, 1.72, 0.16),
                                     (1.40, 2.10, 0.14))):
        L.sphere("pumpkin_%d" % k, (px, py, r * 0.86), r, "mat_int_paint_red", c,
                 segs=14, rings=9, scale=(1.0, 1.0, 0.80))
        L.cyl("pumpkin_stalk_%d" % k, (px, py, r * 1.68), 0.022, 0.09,
              "mat_int_bowlwood", c, verts=6, rot=(L.jit(0.2), L.jit(0.2), 0),
              bevel=0.004)
    # the broom, mid-sweep, leaning where it was left
    L.cyl("broom_stick", (4.95, 0.95, 0.74), 0.019, 1.48, "mat_int_bowlwood", c,
          verts=8, rot=(deg(13), 0, deg(-9)), bevel=0)
    L.lathe("broom_head", [(0.0, 0.0), (0.10, 0.02), (0.075, 0.22), (0.0, 0.24)],
            (4.79, 0.78, 0.0), L.M("mat_int_felt"), c, segments=12)


def build_larder():
    """Cold, blue, and full.  Every preserve in the village, on slate."""
    c = L.coll("PROPS")
    z = AL_Z
    for k, sz in enumerate((0.42, 0.92, 1.42)):
        for side, x in ((-1, AL_X0 + 0.22), (1, AL_X1 - 0.22)):
            L.box("larder_slab_%d_%d" % (k, side > 0), (x, (YB + AL_Y1) / 2 + 0.20,
                                                        z + sz),
                  (0.22, (AL_Y1 - YB) / 2 - 0.10, 0.035), "mat_int_stone", c,
                  bevel=0.008, tex_off=L.toff())
            for j in range(6):
                yy = YB + 0.30 + j * 0.26
                if yy > AL_Y1 - 0.20:
                    break
                L.lathe("preserve_%d_%d_%d" % (k, side > 0, j),
                        [(0.0, 0.0), (0.052, 0.006), (0.056, 0.115), (0.044, 0.150),
                         (0.048, 0.160)],
                        (x, yy, z + sz + 0.035), L.M("mat_int_glassjug"), c,
                        segments=12, thickness=0.004)
                # the cloth cap and string every jar in this valley wears
                L.cyl("preserve_cap_%d_%d_%d" % (k, side > 0, j), (x, yy,
                                                                   z + sz + 0.198),
                      0.056, 0.014, "mat_int_linen", c, verts=12, bevel=0.004)
    # the back slab, and the crock of butter under a damp cloth
    L.box("larder_backslab", ((AL_X0 + AL_X1) / 2, AL_Y1 - 0.28, z + 0.86),
          ((AL_X1 - AL_X0) / 2 - 0.20, 0.22, 0.040), "mat_int_stone", c, bevel=0.008,
          tex_off=L.toff())
    L.lathe("butter_crock", [(0.0, 0.0), (0.115, 0.01), (0.125, 0.19), (0.105, 0.225)],
            ((AL_X0 + AL_X1) / 2, AL_Y1 - 0.28, z + 0.90), L.M("mat_int_crock"), c,
            segments=16, thickness=0.006)
    cl = L.box("butter_cloth", ((AL_X0 + AL_X1) / 2, AL_Y1 - 0.30, z + 1.13),
               (0.16, 0.16, 0.012), "mat_int_linen", c, rot=(0, 0, deg(12)),
               bevel=0.016)
    L.displace(cl, 0.018, 0.30, levels=2, seed_=3)
    # hams and a net of onions on the larder's own beam
    L.cyl("larder_beam", ((AL_X0 + AL_X1) / 2, (YB + AL_Y1) / 2 + 0.10, 2.06),
          0.055, AL_X1 - AL_X0, "mat_int_beam", c, axis="X", verts=10)
    for k, (ox, ln) in enumerate(((-0.62, 0.42), (-0.20, 0.34), (0.34, 0.46))):
        L.lathe("ham_%d" % k, [(0.0, 0.0), (0.085, 0.06), (0.105, ln * 0.5),
                               (0.070, ln * 0.9), (0.0, ln)],
                ((AL_X0 + AL_X1) / 2 + ox, (YB + AL_Y1) / 2 + 0.10, 2.02 - ln),
                L.M("mat_int_paint_red"), c, segments=12)
        L.cyl("ham_string_%d" % k, ((AL_X0 + AL_X1) / 2 + ox,
                                    (YB + AL_Y1) / 2 + 0.10, 2.03), 0.005, 0.10,
              "mat_int_bowlwood", c, verts=5, bevel=0)


def build_leanto(kit):
    """Lamp oil, roots, and the heavy things.  The one place daylight lands."""
    c = L.coll("PROPS")
    z = LT_Z
    # the oil bench and its row of jars, with the funnel and the stained cloth
    L.box("oil_bench", ((XR + LT_X1) / 2 + 0.30, LT_Y1 - 0.50, z + 0.78),
          (0.85, 0.30, 0.030), "mat_int_plank", c, bevel=0.010, tex_off=L.toff())
    for lx in ((XR + LT_X1) / 2 - 0.40, (XR + LT_X1) / 2 + 1.00):
        L.box("oil_bench_leg_%.2f" % lx, (lx, LT_Y1 - 0.50, z + 0.38),
              (0.045, 0.26, 0.38), "mat_int_wood", c, bevel=0.008)
    for k in range(5):
        L.lathe("oil_jar_%d" % k, [(0.0, 0.0), (0.078, 0.010), (0.086, 0.20),
                                   (0.052, 0.28), (0.058, 0.30)],
                ((XR + LT_X1) / 2 - 0.28 + k * 0.29, LT_Y1 - 0.50, z + 0.81),
                L.M("mat_int_glassjug"), c, segments=14, thickness=0.005)
    L.lathe("oil_funnel", [(0.0, 0.0), (0.020, 0.0), (0.020, 0.06), (0.090, 0.17)],
            ((XR + LT_X1) / 2 + 0.92, LT_Y1 - 0.44, z + 0.81), L.M("mat_int_copper"),
            c, segments=14, thickness=0.004)
    rag = L.box("oil_rag", ((XR + LT_X1) / 2 - 0.62, LT_Y1 - 0.44, z + 0.825),
                (0.12, 0.10, 0.016), "mat_int_oilskin", c, rot=(0, 0, deg(-16)),
                bevel=0.014)
    L.displace(rag, 0.014, 0.30, levels=2, seed_=5)
    # the root bins: two open crates of turnips and one of straw
    for k, (bx, by) in enumerate((((XR + LT_X1) / 2 - 0.55, LT_Y0 + 0.70),
                                  ((XR + LT_X1) / 2 + 0.35, LT_Y0 + 0.62))):
        L.box("rootbin_%d" % k, (bx, by, z + 0.24), (0.42, 0.34, 0.24), "mat_int_plank",
              c, rot=(0, 0, deg(6 - 10 * k)), bevel=0.010, tex_off=L.toff())
        for j in range(7):
            a = deg(137.5 * j)
            r = 0.24 * math.sqrt((j + 1) / 7.0)
            L.sphere("root_%d_%d" % (k, j), (bx + r * math.cos(a), by + r * math.sin(a),
                                             z + 0.50),
                     0.062, "mat_int_bowlwood", c, segs=9, rings=6,
                     scale=(1.0, 1.0, 0.78))
    L.place_kit(kit["kit_barrel"], "lt_barrel", (LT_X1 - 0.55, LT_Y1 - 1.35, z),
                rot=(0, 0, deg(18)), c="PROPS")
    L.place_kit(kit["kit_crate"], "lt_crate", (LT_X1 - 0.62, LT_Y0 + 0.62, z),
                rot=(0, 0, deg(-8)), c="PROPS")
    L.place_kit(kit["kit_rope_coil"], "lt_rope", (XR + 0.60, LT_Y0 + 0.42, z),
                c="PROPS")
    # a child's chalk on the glazing's lowest pane, which nobody has wiped off
    for k in range(5):
        L.box("chalk_%d" % k, (LT_X1 - 0.42 + L.jit(0.05), LT_Y0 + 0.28 + k * 0.10,
                               LT_EAVE + 0.06),
              (0.075, 0.006, 0.004), "mat_int_wax", c, rot=(0, deg(-11), L.jit(0.4)),
              bevel=0)


def build_openings():
    c = L.coll("SHELL")
    fb = L.WallFrame((XR, YB), (XL, YB), inward=(0, 1))
    a, b = XR - DOOR_X1, XR - DOOR_X0
    # the door stands open on the square: it is Emberwake and the whole village
    # is out there
    L.box("door_leaf", ((DOOR_X0 + DOOR_X1) / 2 + 0.02, YB + 0.66, 1.05),
          (0.026, 0.60, 1.05), "mat_int_plank", c, bevel=0.008, tex_off=L.toff())
    for k in range(3):
        L.box("door_batten_%d" % k, ((DOOR_X0 + DOOR_X1) / 2 - 0.02, YB + 0.66,
                                     0.36 + k * 0.66),
              (0.020, 0.60, 0.055), "mat_int_beam", c, bevel=0.006)
    fb.box("door_threshold", (a + b) / 2, 0.04, 0.018, b - a + 0.10, 0.34, 0.036,
           L.M("mat_int_stone"), c, bevel=0.008)
    fb.box("door_mat", (a + b) / 2, -0.28, 0.014, b - a - 0.10, 0.42, 0.028,
           L.M("mat_int_rug_border"), c, bevel=0.006)

    # the shop window, with the goods facing OUT the way a shop window does
    wa, wb = XR - WIN_X1, XR - WIN_X0
    fb.box("win_glass", (wa + wb) / 2, 0.13, (WIN_SILL + WIN_TOP) / 2,
           wb - wa - 0.06, 0.014, WIN_TOP - WIN_SILL - 0.06, L.M("mat_glass_dusk"),
           c, bevel=0)
    for k in range(3):
        fb.box("win_mullion_%d" % k, wa + (wb - wa) * (k + 1) / 4.0, 0.08,
               (WIN_SILL + WIN_TOP) / 2, 0.034, 0.058, WIN_TOP - WIN_SILL,
               L.M("mat_int_paint_green"), c, bevel=0.004)
    fb.box("win_sill_in", (wa + wb) / 2, -0.14, WIN_SILL - 0.03, wb - wa + 0.22,
           0.26, 0.048, L.M("mat_int_wood"), c, bevel=0.010)

    # the square at dusk, past the door, with its own lamp
    L.dusk_card("dusk_square", (5.10, 8.10, 1.55), (2.60, 0.05, 1.90), c="SHELL",
                top=(0.098, 0.124, 0.196), bottom=(0.018, 0.024, 0.040), strength=1.0)
    L.box("dusk_ground", (5.10, 7.20, -0.03), (2.60, 1.05, 0.03), "mat_int_stone", c,
          bevel=0)
    L.cyl("dusk_lamppost", (6.55, 7.05, 1.22), 0.042, 2.44, "mat_int_iron", c, verts=8,
          bevel=0.004)
    L.box("dusk_lamphead", (6.55, 7.05, 2.52), (0.095, 0.095, 0.145),
          "mat_int_lampglass", c, bevel=0.010)
    # the lean-to's outside: the lane, dimmer, behind the glazing
    L.dusk_card("dusk_lane", (10.40, (LT_Y0 + LT_Y1) / 2, 1.45), (0.05, 2.10, 1.80),
                c="SHELL", top=(0.070, 0.092, 0.150), bottom=(0.013, 0.018, 0.030),
                strength=1.0)


# ================================================================== lights ==

def build_lights(kit):
    # the shop: two lanterns, the counter's the brighter, exactly as the shop
    # archetype's own note says (the buy/sell spot is the brightest thing).
    L.hang_lantern(kit, "lantern_counter", (CT_X0 + CT_X1) / 2 + 0.20, CT_Y0 - 0.55,
                   2.10, hang_from=CEIL - 0.34, energy=232.0)
    L.hang_lantern(kit, "lantern_shop", 5.55, 4.55, 2.10, hang_from=CEIL - 0.34,
                   energy=148.0)
    L.hang_lantern(kit, "lantern_west", 1.95, 3.30, 2.10, hang_from=CEIL - 0.34,
                   energy=104.0)

    # THE LARDER IS COLD.  One weak blue-grey fill and no warm light at all --
    # the temperature break between the two spaces is the composition.
    a = L.light("LGT_larder", "AREA", ((AL_X0 + AL_X1) / 2, YB + 0.55, 1.95), 72.0,
                (0.58, 0.68, 0.86), shape="RECTANGLE", sx=1.50, sy=1.10, spread=140)
    L.aim(a, ((AL_X0 + AL_X1) / 2, AL_Y1, 0.40))

    # THE LEAN-TO IS DAYLIT, through the glazing: the only cool light that
    # lands on a floor in this room.
    g = L.light("LGT_glazing", "AREA", ((XR + LT_X1) / 2 - 0.10,
                                        (LT_Y0 + LT_Y1) / 2, LT_HIGH - 0.20), 208.0,
                (0.56, 0.66, 0.90), shape="RECTANGLE", sx=2.20, sy=2.60, spread=110)
    L.aim(g, ((XR + LT_X1) / 2 - 0.40, (LT_Y0 + LT_Y1) / 2, LT_Z))

    L.light("LGT_leanto_warm", "POINT", (XR + 0.75, (LT_Y0 + LT_Y1) / 2 - 0.20,
                                        LT_Z + 1.90), 58.0, (1.0, 0.64, 0.30), 0.10)

    # the doorway and the shop window: warm street lamp, cool sky
    d = L.light("LGT_dusk_door", "AREA", ((DOOR_X0 + DOOR_X1) / 2, YB - 0.14, 1.25),
                84.0, (0.52, 0.62, 0.86), shape="RECTANGLE", sx=1.10, sy=1.80,
                spread=140)
    L.aim(d, ((DOOR_X0 + DOOR_X1) / 2 - 1.8, YB - 3.6, 0.70))
    L.light("LGT_square_lamp", "POINT", (6.55, 7.05, 2.52), 132.0, (1.0, 0.66, 0.30),
            0.10)
    w = L.light("LGT_dusk_win", "AREA", ((WIN_X0 + WIN_X1) / 2, YB - 0.12, 1.60), 34.0,
                (0.54, 0.64, 0.88), shape="RECTANGLE", sx=0.72, sy=0.95, spread=150)
    L.aim(w, ((WIN_X0 + WIN_X1) / 2 - 1.4, YB - 3.0, 0.80))

    amb = L.light("LGT_open_amb", "AREA", ((XL + XR) / 2, YF - 3.2, 2.90), 48.0,
                  (0.40, 0.50, 0.70), shape="RECTANGLE", sx=8.6, sy=4.6, spread=170)
    L.aim(amb, ((XL + XR) / 2, (YF + YB) / 2, 1.2))

    up = L.light("LGT_ceiling_bounce", "AREA", (3.60, 3.40, 2.36), 56.0,
                 (1.0, 0.74, 0.48), shape="RECTANGLE", sx=5.6, sy=4.6, spread=150)
    L.aim(up, (3.60, 4.20, 3.40))

    w2 = bpy.data.worlds.new("EMBITEM_WORLD")
    w2.use_nodes = True
    bg = next(n for n in w2.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.060, 0.068, 0.092, 1.0)
    bg.inputs["Strength"].default_value = 0.18
    bpy.context.scene.world = w2
    L.fog_box("FOG_ROOM", ((XL + XR) / 2, (YF + YB) / 2, 1.55),
              ((XR - XL) / 2 - 0.30, (YB - YF) / 2 - 0.20, 1.50), density=0.0026)


# ================================================================== camera ==

CAM = dict(aim=(4.05, 3.70, 1.20), vh=4.80, pitch=15.0, az=-22.0, fov=34.0)

FRAME_CHECKS = [
    ("door opening", ((DOOR_X0 + DOOR_X1) / 2, YB - 0.02, 1.05)),
    ("shop window", ((WIN_X0 + WIN_X1) / 2, YB - 0.06, 1.55)),
    ("larder mouth", ((AL_X0 + AL_X1) / 2, YB - 0.10, 1.05)),
    ("the counter", ((CT_X0 + CT_X1) / 2, CT_Y0 - 0.10, 1.05)),
    ("lean-to opening", (XR, (LT_Y0 + LT_Y1) / 2, 1.20)),
    ("trapdoor", ((TRAP[0] + TRAP[1]) / 2, (TRAP[2] + TRAP[3]) / 2, CEIL - 0.10)),
]


def build_cam():
    return L.build_camera("CAM_int_item", CAM["aim"], CAM["vh"], CAM["pitch"],
                          CAM["az"], CAM["fov"])


def build_pads():
    L.pad("walk_pad_door", (DOOR_X0 + DOOR_X1) / 2, YB - 0.82, 1.10, 0.86)
    L.pad("walk_pad_counter", (CT_X0 + CT_X1) / 2, CT_Y0 - 0.72, 1.90, 0.80)
    L.pad("walk_pad_larder", (AL_X0 + AL_X1) / 2, AL_Y1 - 0.70, 1.30, 0.80, z=AL_Z)
    L.pad("walk_pad_leanto", (XR + LT_X1) / 2 - 0.10, (LT_Y0 + LT_Y1) / 2 - 0.35,
          1.30, 0.80, z=LT_Z)


# ==================================================================== main ==

def build(ref=False):
    L.wipe()
    L.seed(SEED)
    CM.make_all()
    kit = L.append_kit(["kit_crate", "kit_bucket", "kit_barrel", "kit_rope_coil",
                        "kit_lantern_hanging", "kit_lantern_light", "REF_human_1p7"])
    build_floor()
    build_walls()
    build_ceiling()
    build_counter()
    build_shelving()
    build_larder()
    build_leanto(kit)
    build_openings()
    build_lights(kit)
    build_pads()
    cam = build_cam()
    if ref:
        L.place_kit(kit["REF_human_1p7"], "REF_scale_a", (4.30, 4.60, 0.0), c="CAM")
        L.place_kit(kit["REF_human_1p7"], "REF_scale_b", (2.40, 1.80, 0.0), c="CAM")
    L.qa_report(cam, FRAME_CHECKS)
    return cam


def main():
    o = L.argopts(dict(out=OUTBLEND, render="", samples=160, exposure=0.80,
                       res="1344x768", look="AgX - Punchy", ref=False, nosave=False))
    build(ref=bool(o["ref"]))
    L.setup_render(samples=int(o["samples"]), exposure=float(o["exposure"]),
                   res=tuple(int(v) for v in str(o["res"]).split("x")),
                   look=o["look"])
    if not o["nosave"]:
        L.save(o["out"])
    if o["render"]:
        L.render_to(o["render"] if os.path.isabs(o["render"])
                    else os.path.join(L.ROOT, o["render"]))


if __name__ == "__main__":
    main()
