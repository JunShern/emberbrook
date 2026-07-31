#!/usr/bin/env python3
"""emb-bakery-int -- POPPY'S BAKERY, Emberbrook.  The oven is the room.

CANON THIS ROOM SERVES
----------------------
Poppy is hospitality-as-law: *"Nobody goes hungry in Emberbrook on Emberwake --
that's not kindness, that's LAW."*  She *"burns her thumb on the first tray
every morning and swears she won't tomorrow"*, and after the Hush she rebuilds
herself out of three words: **honeybuns, Poppy, thumb** (chapter1.js).  Those
three words are the room's brief, and all three are built into it:

  HONEYBUNS  trays of them, cooling on a rack, and one tray empty but for
             crumbs -- the batch already carried up to the square.
  POPPY      her apron on its hook with the flour handprints where she wipes
             her hands, her stool with the short leg wedged with a folded
             paper, the tally chalked on the oven brick.
  THUMB      the pot of burn salve and the wet rag on the window sill, right
             where the peel is set down.  It is the first thing under her hand
             every single morning, and it is the reason it is a prop.

The map calls this building *"warm window on the square"*, so that window is
the room's second light and its social face: this is a village bakery served
THROUGH the window, and the door is the household's.

THE PLAN, AND WHY IT IS NOT A BOX
---------------------------------
  * A WEDGE.  The bakery is squeezed between the square and the lane, so the
    lane wall CANTS in 1.70 m over its 6.40 m run.  Not one wall of this room
    is parallel to another; the floor is a trapezoid.
  * A RAISED BAKEHOUSE.  The oven stands on a brick platform 0.34 m up -- the
    way a real bake-oven does, mouth at working height -- and you go up two
    steps to it.  Two floor levels, and the upper one is a stage the oven's
    light stands on.
  * THREE CEILINGS AGAIN, but a different three from the inn's: boarded joists
    at 3.20 over the shop floor, the HOOD dropping to 2.30 over the oven, and a
    clerestory slot above the bay window throwing the second shaft.
  * The oven is a MASS, not a wall feature: a 2.80 x 1.05 brick block with a
    domed mouth, standing free of the back wall with its own hood over it.

CAMERA PERSONALITY: the opposite of the inn's.  The inn is a wide, low, sat-down
frame (fov 40, pitch 13).  This is a WORKING room, so it gets a LONG lens
(fov 30) at a working height (pitch 20) -- the compression stacks the oven's
glow, the flour haze and the window's cool light into one plane, which is what
a bakery at dusk actually looks like when you stand in the doorway of it.

FORMAT: FF9 cutaway.  SCALE: character 1.70, door 2.15, counter 1.05,
table 0.90 (a work bench is higher than a dining table -- you stand at it).

Run headless (ALWAYS -b --python-exit-code 1):
    Blender -b --python-exit-code 1 -P tools/embint_bakery_build.py -- \
        --out tools/blends/interiors/emb-bakery-int.blend \
        --render docs/qa/interiors/emb-bakery-int_v1.png --samples 160
"""
import bpy, math, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import embint_lib as L

CM = L.CM
OUTBLEND = "tools/blends/interiors/emb-bakery-int.blend"
SEED = 20260802

# ============================================================== the plan ===
XL, XR = 0.00, 6.80          # front edge, west..east
YF, YB = 0.00, 6.40
XR_BACK = 5.10               # the lane wall CANTS in: 6.80 at the front, 5.10 here
WH = 3.20                    # the square-side wall
WH_LANE = 3.20               # was 2.62; the camera's top rays went over it
CEIL = 3.20
THICK = 0.24

# left (square) wall openings, in world y
DOOR_Y0, DOOR_Y1 = 4.05, 5.25
DOOR_TOP = 2.15
WIN_Y0, WIN_Y1 = 2.15, 3.85
WIN_SILL, WIN_TOP = 0.95, 2.35
CLER_Z0, CLER_Z1 = 2.62, 3.02      # the clerestory slot over the bay

# the raised bakehouse
PL_X0, PL_X1 = 1.25, 4.80
PL_Y0 = 4.60
PL_Z = 0.34
ST_W = 1.70                  # the steps up to it
ST_X = 2.55

# the oven mass
OV_X0, OV_X1 = 1.30, 4.10
OV_Y0, OV_Y1 = 5.35, 6.40
OV_TOP = 2.30
MO_X0, MO_X1 = 2.10, 3.30    # the mouth
MO_Z0, MO_Z1 = PL_Z + 0.42, PL_Z + 1.16
HOOD_TOP = 3.10

# the work bench, out on the shop floor
BX0, BX1, BY0, BY1, BH = 2.35, 5.05, 2.05, 3.35, 0.90


def deg(a):
    return math.radians(a)


def lane_frame():
    return L.WallFrame((XR, YF), (XR_BACK, YB), inward=(1, 0))


# =============================================================== the shell ==

def build_floor():
    c = L.coll("SHELL")

    # THE WEDGE.  The lane wall cants, so the floor's east edge is a function
    # of y -- which is exactly what `floor_planks` takes.  A rectangle would
    # have been one line shorter and would have thrown the whole plan away.
    def yfn(y):
        t = max(0.0, min(1.0, (y - YF) / (YB - YF)))
        return [(XL - 0.02, XR + (XR_BACK - XR) * t + 0.02)]

    L.floor_planks("bake", (YF - 0.02, YB + 0.02), yfn, z=0.0, c=c,
                   mat="mat_int_floor", mat_alt="mat_int_floor_pale", alt=0.10,
                   dir_="x", w=(0.17, 0.245), run=(1.8, 3.6))
    L.floor_void("floor_void_bake", XL, XR, YF, YB, 0.0, c=c)

    # THE RAISED BAKEHOUSE: brick, not board -- you do not lay a timber floor in
    # front of an oven mouth.
    L.prism("walk_bakehouse_platform",
            [(PL_X0, PL_Y0), (PL_X1, PL_Y0), (PL_X1, YB - 0.05), (PL_X0, YB - 0.05)],
            -0.05, PL_Z, "mat_int_hearth", c, bevel=0.008)
    # the brick face of the platform, and its worn stone nosing
    L.box("platform_face", ((PL_X0 + PL_X1) / 2, PL_Y0 - 0.03, PL_Z / 2),
          ((PL_X1 - PL_X0) / 2, 0.04, PL_Z / 2), "mat_int_stone", c, bevel=0.008,
          tex_off=L.toff())
    L.box("platform_nosing", ((PL_X0 + PL_X1) / 2, PL_Y0 - 0.06, PL_Z - 0.020),
          ((PL_X1 - PL_X0) / 2 + 0.02, 0.075, 0.024), "mat_int_stone", c,
          bevel=0.010, tex_off=L.toff())

    # two steps up, worn hollow in the middle where thirty years of feet go
    for k in range(2):
        z = PL_Z - 0.17 * (k + 1)
        y = PL_Y0 - 0.16 - 0.30 * k
        L.box("walk_step_oven_%02d" % k, (ST_X, y, z - 0.03),
              (ST_W / 2, 0.16, 0.03), "mat_int_stone", c, bevel=0.010,
              tex_off=L.toff())
        L.box("step_oven_%02d_riser" % k, (ST_X, y - 0.155, z - 0.115),
              (ST_W / 2 - 0.01, 0.022, 0.085), "mat_int_stone", c, bevel=0.004)

    # FLOUR.  It gets everywhere and it never entirely comes up: a pale dusting
    # on the boards in front of the bench and at the foot of the steps, and one
    # scuffed patch where the sack is dragged.
    # A BOX OF WAX read as a lit rectangle on the boards.  Flour is a smear:
    # flattened, overlapping, in linen rather than candle-wax white.
    for k, (fx, fy, r, sq) in enumerate(((3.30, 3.85, 0.62, 0.55),
                                         (2.75, 4.25, 0.42, 0.70),
                                         (2.30, 4.05, 0.30, 0.80),
                                         (4.45, 2.45, 0.34, 0.62),
                                         (2.05, 2.65, 0.26, 0.75))):
        ob = L.sphere("flour_dust_%d" % k, (fx, fy, 0.002), r, "mat_int_linen", c,
                      segs=16, rings=8, scale=(1.0, sq, 0.004))
        L.displace(ob, 0.030, 0.45, levels=0, seed_=k)


def build_walls():
    c = "SHELL"
    made = {}
    # ---- the SQUARE wall (x = 0): door, bay window, clerestory --------------
    fl = L.WallFrame((XL, YB), (XL, YF), inward=(-1, 0))    # u = YB - y
    made["square"] = L.wall_run(
        "wSq", fl, WH, c=c, style="plaster", wain=1.02, thick=THICK,
        openings=[(YB - DOOR_Y1, YB - DOOR_Y0, DOOR_TOP),
                  (YB - WIN_Y1, YB - WIN_Y0, WIN_TOP)])
    L.opening_frame("doorframe", fl, YB - DOOR_Y1, YB - DOOR_Y0, DOOR_TOP, c=c)
    L.opening_frame("winframe", fl, YB - WIN_Y1, YB - WIN_Y0, WIN_TOP, c=c,
                    sill=WIN_SILL)
    made["square_frame"] = fl

    # ---- the LANE wall: canted, lower, and lined with the flour store ------
    fr = lane_frame()
    made["lane"] = L.wall_run("wLane", fr, WH_LANE, c=c, style="board", thick=0.20,
                              board_mat="mat_int_plank", plate_z=WH_LANE - 0.12)

    # ---- the back wall, behind the oven ------------------------------------
    fb = L.WallFrame((XR_BACK, YB), (XL, YB), inward=(0, 1))
    L.wall_run("wBack", fb, WH, c=c, style="stone", thick=0.30, studs=False,
               plate=False)

    # ---- camera-invisible near wall ----------------------------------------
    nw = L.box("shadow_nearwall", ((XL + XR) / 2, YF - THICK / 2 - 0.02, WH / 2),
               ((XR - XL) / 2 + THICK, THICK / 2, WH / 2), "mat_int_plaster",
               L.coll("SHELL"), bevel=0)
    L.hide_from_camera(nw)
    return made


def build_ceiling():
    c = L.coll("SHELL")
    lid = L.box("shadow_ceiling", ((XL + XR) / 2, (YF + YB) / 2, CEIL + 0.16),
                ((XR - XL) / 2 + THICK, (YB - YF) / 2 + THICK, 0.08),
                "mat_int_plank", c, bevel=0)
    L.hide_from_camera(lid)
    L.roof_backing("roofvoid", XL - 0.4, XR + 0.4, YF - 0.4, YB + 0.4, 3.90, c=c)

    # boarded ceiling over the SHOP floor only; over the bakehouse the hood
    # takes over, which is what makes the two halves of the room read as two
    # different places without a wall between them.
    # the boarding now runs the WHOLE depth, splitting round the hood's plan
    # footprint, so there is no unroofed strip over the bakehouse end
    HOODX = (OV_X0 - 0.30, OV_X1 + 0.30)
    y = YF
    i = 0
    while y < YB - 0.02:
        w = min(0.245, YB - y)
        spans = ([((XL + XR) / 2 - 0.3, (XR - XL) / 2 + 0.4)] if y + w < OV_Y0 - 0.55
                 else None)
        if spans is None:
            for (a2, b2) in ((XL - 0.4, HOODX[0]), (HOODX[1], XR + 0.4)):
                if b2 - a2 < 0.05:
                    continue
                L.box("ceilboard_%02d_%.2f" % (i, a2), ((a2 + b2) / 2, y + w / 2,
                                                        CEIL - 0.03),
                      ((b2 - a2) / 2, w / 2 - 0.004, 0.028), "mat_int_beam", c,
                      bevel=0.004, tex_off=L.toff())
            y += w
            i += 1
            continue
        ob = L.box("ceilboard_%02d" % i, ((XL + XR) / 2 - 0.3, y + w / 2, CEIL - 0.03),
                   ((XR - XL) / 2 + 0.4, w / 2 - 0.004, 0.028), "mat_int_beam", c,
                   bevel=0.004, tex_off=L.toff())
        # NO CEILING CUTAWAY.  Dellhollow's interiors hide their ceilings
        # because their cameras sit ABOVE them (pitch 24 puts the lens over
        # the lid); this room's camera stands INSIDE the room's headroom, so
        # the ceiling never occludes anything and hiding it only opened a
        # hole -- 11% of the first inn plate came back pure black at the top
        # where the hidden strip let the frame see the roof void.  The only
        # members hidden are the ones physically between the lens and the
        # floor.
        if y + w / 2 < -0.20:
            L.hide_from_camera(ob)
        y += w
        i += 1
    # joists across, and one heavy summer beam down the length
    yj, i = 0.28, 0
    while yj < PL_Y0 - 0.05:
        ob = L.box("joist_%02d" % i, ((XL + XR) / 2 - 0.3, yj, CEIL - 0.105),
                   ((XR - XL) / 2 + 0.35, 0.045, 0.075), "mat_int_beam", c,
                   bevel=0.006, tex_off=L.toff())
        if yj < -0.20:
            L.hide_from_camera(ob)
        yj += 0.34
        i += 1
    for k in range(4):
        y0 = YF + (PL_Y0 - YF) * k / 4.0
        y1 = YF + (PL_Y0 - YF) * (k + 1) / 4.0
        ob = L.box("summer_%d" % k, (3.10, (y0 + y1) / 2, CEIL - 0.24),
                   (0.115, (y1 - y0) / 2, 0.135), "mat_int_beam", c, bevel=0.012,
                   tex_off=L.toff())
        if (y0 + y1) / 2 < -0.20:
            L.hide_from_camera(ob)
    # the trimmer where the boarding stops and the hood begins
    L.box("hood_trimmer", ((XL + XR_BACK) / 2, PL_Y0 - 0.02, CEIL - 0.14),
          ((XR_BACK - XL) / 2 + 0.2, 0.085, 0.135), "mat_int_beam", c, bevel=0.012,
          tex_off=L.toff())

    # ---- THE CLERESTORY: a slot of cold sky over the bay window ------------
    fl = L.WallFrame((XL, YB), (XL, YF), inward=(-1, 0))
    a, b = YB - WIN_Y1, YB - WIN_Y0
    fl.box("clerestory_reveal", (a + b) / 2, THICK / 2, (CLER_Z0 + CLER_Z1) / 2,
           b - a, THICK + 0.06, CLER_Z1 - CLER_Z0, L.M("mat_glass_dusk"), c, bevel=0)
    for k in range(3):
        fl.box("clerestory_bar_%d" % k, a + (b - a) * (k + 1) / 4.0, 0.02,
               (CLER_Z0 + CLER_Z1) / 2, 0.045, 0.06, CLER_Z1 - CLER_Z0,
               L.M("mat_int_beam"), c, bevel=0.004)
    fl.box("clerestory_head", (a + b) / 2, -0.02, CLER_Z1 + 0.06, b - a + 0.20,
           0.10, 0.12, L.M("mat_int_beam"), c, bevel=0.008)


def build_oven():
    """The subject.  A brick beehive in a masonry block, its mouth a real arch,
    with the hood over it and the whole thing standing on the platform."""
    c = L.coll("OVEN")
    cx = (OV_X0 + OV_X1) / 2
    # the block, built AROUND the mouth
    ycn, ydp = (OV_Y0 + OV_Y1) / 2, (OV_Y1 - OV_Y0) / 2
    for tag, x0, x1 in (("cheekW", OV_X0, MO_X0), ("cheekE", MO_X1, OV_X1)):
        L.box("oven_%s" % tag, ((x0 + x1) / 2, ycn, (PL_Z + OV_TOP) / 2),
              ((x1 - x0) / 2, ydp, (OV_TOP - PL_Z) / 2), "mat_int_stone", c,
              bevel=0.016, tex_off=L.toff())
    # SOOT, not stone: these two blocks form the soffit and the floor of the
    # chamber, and v2/v3 rendered them in pale masonry -- so the mouth read as a
    # lightbox instead of as a fire in a black vault.  A bake-oven's inside is
    # the blackest surface in any village.
    L.box("oven_over", (cx, ycn, (MO_Z1 + OV_TOP) / 2),
          ((MO_X1 - MO_X0) / 2, ydp, (OV_TOP - MO_Z1) / 2), "mat_int_soot", c,
          bevel=0.016, tex_off=L.toff())
    L.box("oven_under", (cx, ycn, (PL_Z + MO_Z0) / 2),
          ((MO_X1 - MO_X0) / 2, ydp, (MO_Z0 - PL_Z) / 2), "mat_int_soot", c,
          bevel=0.016, tex_off=L.toff())
    # the chamber: a sooted vault you can see the back of
    L.box("oven_chamber_back", (cx, OV_Y1 - 0.14, (MO_Z0 + MO_Z1) / 2),
          ((MO_X1 - MO_X0) / 2, 0.14, (MO_Z1 - MO_Z0) / 2), "mat_int_soot", c,
          bevel=0)
    for sgn in (-1, 1):
        L.box("oven_chamber_side_%d" % (sgn > 0), (cx + sgn * ((MO_X1 - MO_X0) / 2 - 0.025),
                                                   ycn, (MO_Z0 + MO_Z1) / 2),
              (0.025, ydp, (MO_Z1 - MO_Z0) / 2), "mat_int_soot", c, bevel=0)
    L.box("oven_chamber_crown", (cx, ycn, MO_Z1 - 0.025),
          ((MO_X1 - MO_X0) / 2, ydp, 0.025), "mat_int_soot", c, bevel=0)
    L.box("oven_hearthslab", (cx, ycn + 0.10, MO_Z0 + 0.012),
          ((MO_X1 - MO_X0) / 2 - 0.02, ydp - 0.16, 0.014), "mat_int_soot", c,
          bevel=0.004, tex_off=L.toff())
    # courses of brick laid over the front face, so it is masonry and not a slab
    z = PL_Z
    k = 0
    while z < OV_TOP - 0.04:
        h = min(0.115, OV_TOP - z)
        spans = ([(OV_X0, OV_X1)] if (z > MO_Z1 - 0.02 or z + h < MO_Z0 + 0.02)
                 else [(OV_X0, MO_X0), (MO_X1, OV_X1)])
        for (sx0, sx1) in spans:
            ob = L.box("oven_course_%02d_%.2f" % (k, sx0), ((sx0 + sx1) / 2,
                                                            OV_Y0 - 0.035, z + h / 2),
                       ((sx1 - sx0) / 2 + 0.01, 0.035, h / 2 - 0.006),
                       "mat_int_hearth" if k % 3 else "mat_int_stone", c, bevel=0.006,
                       tex_off=L.toff())
            L.displace(ob, 0.010, 0.30, levels=2, seed_=k)
        z += h
        k += 1
    # THE MOUTH: a segmental arch of voussoirs, sooted black inside
    mcx = (MO_X0 + MO_X1) / 2
    for k in range(9):
        t = (k + 0.5) / 9.0
        a = deg(180) * t
        L.box("oven_voussoir_%02d" % k,
              (mcx - math.cos(a) * ((MO_X1 - MO_X0) / 2 + 0.09),
               OV_Y0 - 0.06,
               MO_Z1 - 0.14 + math.sin(a) * 0.30),
              (0.075, 0.055, 0.115), "mat_int_stone", c, rot=(0, -a + deg(90), 0),
              bevel=0.008, tex_off=L.toff())
    # the fire inside, raked to one side the way a bake-oven is fired
    L.prism("oven_embers", [(MO_X0 + 0.10, OV_Y0 + 0.22), (MO_X1 - 0.55, OV_Y0 + 0.22),
                            (MO_X1 - 0.55, OV_Y1 - 0.12), (MO_X0 + 0.10, OV_Y1 - 0.12)],
            MO_Z0 + 0.01, MO_Z0 + 0.05, "mat_embers", c)
    for k, (ox, h, r) in enumerate(((-0.40, 0.26, 0.056), (-0.31, 0.38, 0.072),
                                    (-0.22, 0.48, 0.086), (-0.13, 0.40, 0.074),
                                    (-0.04, 0.28, 0.058), (0.06, 0.18, 0.044),
                                    (0.15, 0.12, 0.034))):
        L.lathe("oven_flame_%d" % k, [(0.0, 0.0), (r, 0.05), (r * 0.7, h * 0.55),
                                      (0.0, h)],
                (mcx + ox, OV_Y0 + 0.46 + L.jit(0.06), MO_Z0 + 0.03),
                L.M("mat_fire"), c, segments=10)
    for k in range(5):
        L.cyl("oven_log_%d" % k, (mcx - 0.28 + L.jit(0.06), OV_Y0 + 0.40 + L.jit(0.10),
                                  MO_Z0 + 0.06 + (k // 3) * 0.055),
              0.048, 0.34, "mat_int_charlog", c, axis="X", verts=8,
              rot=(0, 0, L.jit(0.35)), bevel=0.004)
    # the iron door, hooked back against the brick, and the damper chain
    L.box("oven_door", (MO_X0 - 0.34, OV_Y0 - 0.16, (MO_Z0 + MO_Z1) / 2),
          (0.30, 0.030, (MO_Z1 - MO_Z0) / 2 - 0.02), "mat_int_iron", c,
          rot=(0, 0, deg(24)), bevel=0.010)
    L.cyl("oven_door_handle", (MO_X0 - 0.60, OV_Y0 - 0.26, (MO_Z0 + MO_Z1) / 2),
          0.016, 0.20, "mat_int_iron", c, axis="Z", verts=8, bevel=0)

    # ---- THE HOOD: the shape that gives the bakehouse its own ceiling ------
    for k in range(6):
        t = k / 5.0
        z0 = OV_TOP + (HOOD_TOP - OV_TOP) * t
        w = ((OV_X1 - OV_X0) / 2 + 0.24) * (1 - t) + 0.34 * t
        d = ((OV_Y1 - OV_Y0) / 2 + 0.30) * (1 - t) + 0.30 * t
        L.box("hood_%02d" % k, (cx, (OV_Y0 + OV_Y1) / 2 - 0.10, z0 + 0.075),
              (w, d, 0.085), "mat_int_plaster", c, bevel=0.010, tex_off=L.toff())
    L.box("hood_lintel", (cx, OV_Y0 - 0.36, OV_TOP - 0.02),
          ((OV_X1 - OV_X0) / 2 + 0.28, 0.10, 0.115), "mat_int_beam", c, bevel=0.012,
          tex_off=L.toff())
    # the chimney going on up past the ceiling
    L.box("chimney", (cx, (OV_Y0 + OV_Y1) / 2 - 0.10, HOOD_TOP + 0.55),
          (0.36, 0.32, 0.55), "mat_int_stone", c, bevel=0.012, tex_off=L.toff())

    # ---- THE TALLY, chalked on the brick beside the mouth ------------------
    # "how many are promised tonight".  Poppy counts in fives on the oven
    # because that is where her hands are.
    for k in range(13):
        gx = MO_X1 + 0.24 + (k // 5) * 0.135
        gz = MO_Z1 + 0.10 - (k % 5) * 0.055
        lean = (k % 5) == 4
        L.box("tally_%02d" % k, (gx, OV_Y0 - 0.075, gz), (0.008, 0.006, 0.024),
              "mat_int_wax", c, rot=(deg(58) if lean else 0, 0, 0), bevel=0)


def build_bakehouse():
    """What is ON the platform: the peel, the trays, the rack, the trough."""
    c = L.coll("PROPS")
    z = PL_Z
    # the peel, leaning against the oven where it always is
    L.box("peel_blade", (MO_X0 - 0.86, OV_Y0 - 0.30, z + 0.36), (0.20, 0.014, 0.24),
          "mat_int_wood", c, rot=(deg(-16), 0, deg(-6)), bevel=0.008,
          tex_off=L.toff())
    L.cyl("peel_handle", (MO_X0 - 0.94, OV_Y0 - 0.52, z + 1.05), 0.021, 1.42,
          "mat_int_bowlwood", c, verts=10, rot=(deg(-16), 0, deg(-6)), bevel=0.004)
    # the rake and the brush that go with it
    for k, (ox, tilt) in enumerate(((0.34, deg(-11)), (0.52, deg(-14)))):
        L.cyl("oventool_%d" % k, (OV_X1 + 0.10, OV_Y0 - 0.30 - ox * 0.4, z + 0.86),
              0.017, 1.66, "mat_int_bowlwood", c, verts=8, rot=(tilt, 0, deg(7 + k * 5)),
              bevel=0)
    # THE COOLING RACK: four shelves of trays, and the one that is EMPTY
    rx, ry = PL_X0 + 0.42, 5.30
    for k in range(4):
        L.box("rack_shelf_%d" % k, (rx, ry, z + 0.42 + k * 0.34), (0.30, 0.52, 0.020),
              "mat_int_plank", c, bevel=0.006, tex_off=L.toff())
    for (sx, sy) in ((rx - 0.27, ry - 0.48), (rx + 0.27, ry - 0.48),
                     (rx - 0.27, ry + 0.48), (rx + 0.27, ry + 0.48)):
        L.box("rack_post_%.2f_%.2f" % (sx, sy), (sx, sy, z + 0.78),
              (0.026, 0.026, 0.78), "mat_int_wood", c, bevel=0.006)
    for k in range(4):
        tz = z + 0.44 + k * 0.34
        L.box("tray_%d" % k, (rx, ry, tz + 0.012), (0.27, 0.47, 0.012),
              "mat_int_iron", c, bevel=0.006)
        if k == 2:
            # THE EMPTY TRAY.  Crumbs, and nothing else: that batch is already
            # in a basket on its way up to the square.
            for j in range(7):
                L.sphere("crumb_%d" % j, (rx + L.jit(0.20), ry + L.jit(0.38),
                                          tz + 0.028), 0.010, "mat_int_bread", c,
                         segs=8, rings=5)
            continue
        for j in range(12):
            L.sphere("bun_%d_%d" % (k, j),
                     (rx - 0.17 + (j % 3) * 0.17, ry - 0.36 + (j // 3) * 0.24,
                      tz + 0.055),
                     0.058, "mat_int_bread", c, scale=(1.0, 1.0, 0.66))

    # the trough, with risen dough under a cloth: tonight's second batch
    tx, ty = 3.95, 5.05
    L.box("trough", (tx, ty, z + 0.32), (0.42, 0.32, 0.32), "mat_int_plank", c,
          bevel=0.010, tex_off=L.toff())
    L.box("trough_rim", (tx, ty, z + 0.645), (0.44, 0.34, 0.022), "mat_int_wood", c,
          bevel=0.010)
    dough = L.sphere("dough", (tx, ty, z + 0.60), 0.30, "mat_int_bread", c,
                     scale=(1.15, 0.85, 0.42))
    L.displace(dough, 0.020, 0.55, levels=2, seed_=11)
    cl = L.box("trough_cloth", (tx, ty, z + 0.70), (0.44, 0.34, 0.014),
               "mat_int_linen", c, rot=(deg(2), deg(-3), deg(6)), bevel=0.020)
    L.displace(cl, 0.030, 0.25, levels=3, seed_=12)

    # the basket standing ready by the steps, half packed for the square
    L.lathe("basket", [(0.0, 0.0), (0.24, 0.02), (0.28, 0.24), (0.26, 0.27)],
            (PL_X1 - 0.42, PL_Y0 + 0.34, z), L.M("mat_int_bowlwood"), c, segments=18,
            thickness=0.012)
    for j in range(6):
        L.sphere("basket_bun_%d" % j, (PL_X1 - 0.42 + L.jit(0.13),
                                       PL_Y0 + 0.34 + L.jit(0.13), z + 0.22),
                 0.058, "mat_int_bread", c, scale=(1.0, 1.0, 0.66))
    L.box("basket_cloth", (PL_X1 - 0.42, PL_Y0 + 0.30, z + 0.28), (0.26, 0.24, 0.012),
          "mat_int_linen", c, rot=(deg(-4), 0, deg(-14)), bevel=0.016)


def build_shopfloor(kit):
    """The work bench, the flour store down the lane wall, and Poppy herself in
    the negative: her apron, her stool, her tally, her burnt thumb."""
    c = L.coll("PROPS")
    cx, cy = (BX0 + BX1) / 2, (BY0 + BY1) / 2
    # THE BENCH: higher than a table (you stand at it), scrubbed pale, and worn
    # into a dish where the dough gets knocked back
    L.box("bench_top", (cx, cy, BH - 0.035), ((BX1 - BX0) / 2, (BY1 - BY0) / 2, 0.035),
          "mat_int_floor_pale", c, bevel=0.012, tex_off=L.toff())
    L.box("bench_rail", (cx, BY0 + 0.12, BH - 0.145), ((BX1 - BX0) / 2 - 0.14, 0.045,
                                                       0.060),
          "mat_int_beam", c, bevel=0.006, tex_off=L.toff())
    for (lx, ly) in ((BX0 + 0.16, BY0 + 0.16), (BX1 - 0.16, BY0 + 0.16),
                     (BX0 + 0.16, BY1 - 0.16), (BX1 - 0.16, BY1 - 0.16)):
        L.box("bench_leg_%.2f_%.2f" % (lx, ly), (lx, ly, (BH - 0.07) / 2),
              (0.055, 0.055, (BH - 0.07) / 2), "mat_int_wood", c, bevel=0.008,
              tex_off=L.toff())
    # shelf under the bench: tins, a scale, the crock of yeast
    L.box("bench_shelf", (cx, cy, 0.30), ((BX1 - BX0) / 2 - 0.10, (BY1 - BY0) / 2 - 0.10,
                                          0.018),
          "mat_int_plank", c, bevel=0.006, tex_off=L.toff())
    for k, ox in enumerate((-0.95, -0.62, 0.55, 0.92)):
        L.lathe("bench_crock_%d" % k,
                [(0.0, 0.0), (0.105, 0.01), (0.115, 0.16), (0.088, 0.215),
                 (0.095, 0.235)],
                (cx + ox, cy + L.jit(0.10), 0.318),
                L.M("mat_int_crock" if k % 2 else "mat_int_crock_blue"), c,
                segments=16, thickness=0.006)

    # ON the bench: dough on the board, the rolling pin, the flour scoop, and
    # the thing this whole room is a portrait of --
    L.box("bench_board", (cx - 0.55, cy + 0.10, BH + 0.014), (0.42, 0.32, 0.014),
          "mat_int_bowlwood", c, rot=(0, 0, deg(-5)), bevel=0.008)
    d2 = L.sphere("bench_dough", (cx - 0.60, cy + 0.12, BH + 0.055), 0.20,
                  "mat_int_bread", c, scale=(1.2, 0.9, 0.36))
    L.displace(d2, 0.014, 0.60, levels=2, seed_=13)
    L.cyl("rolling_pin", (cx - 0.02, cy - 0.24, BH + 0.048), 0.048, 0.42,
          "mat_int_wood", c, axis="X", verts=14, rot=(0, 0, deg(8)), bevel=0.006)
    for s in (-1, 1):
        L.cyl("rolling_pin_h_%d" % (s > 0), (cx - 0.02 + s * 0.28, cy - 0.24,
                                             BH + 0.048),
              0.019, 0.14, "mat_int_wood", c, axis="X", verts=10, rot=(0, 0, deg(8)),
              bevel=0.004)
    L.lathe("flour_scoop", [(0.0, 0.0), (0.075, 0.005), (0.082, 0.075), (0.070, 0.080)],
            (cx + 0.62, cy + 0.18, BH), L.M("mat_int_copper"), c, segments=14,
            thickness=0.004)
    L.cyl("scoop_handle", (cx + 0.78, cy + 0.10, BH + 0.045), 0.014, 0.16,
          "mat_int_wood", c, axis="X", verts=8, rot=(0, deg(14), deg(-30)), bevel=0)
    # the scale, with its pan worn bright where a thumb steadies it
    L.box("scale_base", (cx + 1.02, cy - 0.02, BH + 0.022), (0.14, 0.10, 0.022),
          "mat_int_iron", c, bevel=0.008)
    L.cyl("scale_post", (cx + 1.02, cy - 0.02, BH + 0.14), 0.012, 0.22,
          "mat_int_brass", c, verts=8, bevel=0)
    L.box("scale_beam", (cx + 1.02, cy - 0.02, BH + 0.25), (0.17, 0.012, 0.008),
          "mat_int_brass", c, rot=(0, deg(6), 0), bevel=0)
    for s in (-1, 1):
        L.lathe("scale_pan_%d" % (s > 0), [(0.0, 0.0), (0.075, 0.012), (0.078, 0.020)],
                (cx + 1.02 + s * 0.16, cy - 0.02, BH + 0.16 + s * 0.018),
                L.M("mat_int_brass"), c, segments=14, thickness=0.003)

    # --- THE THUMB.  A pot of salve and a wet rag on the window sill, exactly
    # where the first tray comes out and exactly where her hand goes next.
    L.lathe("salve_pot", [(0.0, 0.0), (0.042, 0.006), (0.046, 0.058), (0.038, 0.066)],
            (0.16, WIN_Y0 + 0.34, WIN_SILL + 0.015), L.M("mat_int_crock_blue"), c,
            segments=14, thickness=0.004)
    L.cyl("salve_lid", (0.16, WIN_Y0 + 0.54, WIN_SILL + 0.020), 0.046, 0.012,
          "mat_int_crock_blue", c, verts=14, rot=(deg(74), 0, 0), bevel=0.004)
    rag = L.box("wet_rag", (0.20, WIN_Y0 + 0.86, WIN_SILL + 0.022), (0.11, 0.13, 0.020),
                "mat_int_linen", c, rot=(0, 0, deg(21)), bevel=0.014)
    L.displace(rag, 0.016, 0.30, levels=3, seed_=14)

    # --- POPPY.  Her apron on its peg, flour handprints down the front where
    # she wipes her hands twenty times a morning.
    fl = L.WallFrame((XL, YB), (XL, YF), inward=(-1, 0))
    fl.box("apron_pegrail", YB - 1.35, -0.045, 1.72, 1.00, 0.045, 0.075,
           L.M("mat_int_paint_red"), c, bevel=0.008)
    for k, u in enumerate((YB - 1.75, YB - 1.35, YB - 0.95)):
        fl.cyl("apron_peg_%d" % k, u, -0.12, 1.76, 0.020, 0.17, L.M("mat_int_wood"),
               c, axis="V", verts=8)
    ap = L.box("apron", (0.13, 1.35, 1.24), (0.030, 0.30, 0.44), "mat_int_linen", c,
               rot=(0, 0, deg(4)), bevel=0.020)
    L.displace(ap, 0.022, 0.40, levels=3, seed_=15)
    for k in range(4):
        L.box("apron_handprint_%d" % k, (0.095, 1.22 + k * 0.14, 1.10 + L.jit(0.10)),
              (0.006, 0.055, 0.070), "mat_int_wax", c, rot=(0, 0, L.jit(0.3)),
              bevel=0.010)
    L.box("apron_strap", (0.13, 1.35, 1.66), (0.026, 0.13, 0.030), "mat_int_linen", c,
          bevel=0.010)

    # --- her stool, with the short leg wedged with a folded paper -----------
    sx, sy = 4.05, 2.35
    L.lathe("stool_seat", [(0.0, 0.0), (0.19, 0.0), (0.19, 0.035), (0.0, 0.035)],
            (sx, sy, 0.56), L.M("mat_int_wood"), c, segments=16)
    for j in range(3):
        aa = deg(120 * j + 40)
        L.cyl("stool_leg_%d" % j, (sx + 0.13 * math.cos(aa), sy + 0.13 * math.sin(aa),
                                   0.28),
              0.020, 0.56, "mat_int_wood", c, verts=8,
              rot=(deg(8) * math.sin(aa), -deg(8) * math.cos(aa), 0), bevel=0.004)
    L.box("stool_wedge", (sx + 0.13 * math.cos(deg(40)), sy + 0.13 * math.sin(deg(40)),
                          0.012),
          (0.035, 0.030, 0.012), "mat_int_paper", c, rot=(0, 0, deg(18)), bevel=0.004)

    # --- the flour store down the canted lane wall --------------------------
    fr = lane_frame()
    for k in range(4):
        u = 0.85 + k * 1.15
        if u > fr.L - 0.6:
            break
        # 1.86, not 1.28: a shelf you can walk under with your BODY but not
        # with your HEAD is exactly the defect the headroom gate exists for --
        # the runtime's body box stops at 1.30 and would have let a player put
        # their face through a plank.  Sacks live under it; jars live on it.
        fr.box("store_shelf_%d" % k, u, -0.19, 1.86 + (k % 2) * 0.40, 1.05, 0.38,
               0.026, L.M("mat_int_plank"), c, bevel=0.006)
        for j in range(3):
            L.lathe("store_jar_%d_%d" % (k, j),
                    [(0.0, 0.0), (0.070, 0.008), (0.078, 0.13), (0.055, 0.185),
                     (0.062, 0.20)],
                    fr.w(u - 0.30 + j * 0.30, -0.19, 1.874 + (k % 2) * 0.40),
                    L.M("mat_int_crock" if (j + k) % 2 else "mat_int_crock_blue"), c,
                    segments=14, thickness=0.005)
    # sacks of flour, slumped the way full sacks do, one open with a scoop in it
    for k, (u, v, s) in enumerate(((0.95, 0.42, 1.00), (1.55, 0.38, 0.92),
                                   (2.30, 0.45, 1.06), (3.05, 0.40, 0.88))):
        p = fr.w(u, v, 0.0)
        sk = L.lathe("sack_%d" % k,
                     [(0.0, 0.0), (0.24 * s, 0.03), (0.27 * s, 0.22), (0.22 * s, 0.44),
                      (0.13 * s, 0.52), (0.10 * s, 0.55)],
                     (p[0], p[1], 0.0), L.M("mat_int_linen"), c, segments=14)
        L.displace(sk, 0.018, 0.50, levels=1, seed_=20 + k)
    # the front of the room is where the deliveries land: a barrel of water, a
    # sack that has been dragged and left, and the broom mid-sweep
    L.place_kit(kit["kit_barrel"], "barrel_front", (5.55, 0.95, 0.0),
                rot=(0, 0, deg(14)), c="PROPS")
    sk2 = L.lathe("sack_front",
                  [(0.0, 0.0), (0.26, 0.03), (0.29, 0.22), (0.23, 0.44),
                   (0.14, 0.52), (0.11, 0.55)],
                  (1.35, 1.15, 0.0), L.M("mat_int_linen"), c, segments=14,
                  rot=(deg(11), 0, deg(24)))
    L.displace(sk2, 0.020, 0.50, levels=1, seed_=31)
    L.place_kit(kit["kit_bucket"], "bucket_water", fr.w(3.85, 0.40, 0.0),
                rot=(0, 0, deg(20)), c="PROPS")
    L.place_kit(kit["kit_crate"], "crate_kindling", fr.w(4.55, 0.52, 0.0),
                rot=(0, 0, deg(-12)), c="PROPS")

    # --- a child's drawing pinned by the door, and the broom ----------------
    fl.box("drawing", YB - 4.95, -0.012, 1.52, 0.22, 0.012, 0.28,
           L.M("mat_int_paper"), c, bevel=0.004)
    fl.box("drawing_sun", YB - 4.95, -0.020, 1.58, 0.10, 0.010, 0.10,
           L.M("mat_int_paint_red"), c, bevel=0.004)
    L.cyl("broom_stick", (0.42, 5.75, 0.72), 0.019, 1.44, "mat_int_bowlwood", c,
          verts=8, rot=(deg(12), 0, deg(6)), bevel=0)
    L.lathe("broom_head", [(0.0, 0.0), (0.10, 0.02), (0.075, 0.22), (0.0, 0.24)],
            (0.36, 5.60, 0.0), L.M("mat_int_felt"), c, segments=12)


def build_window_and_door():
    """The warm window on the square -- served through, not looked through --
    and the household door beside it.  Both read from the camera: seam canon
    applies indoors."""
    c = L.coll("SHELL")
    fl = L.WallFrame((XL, YB), (XL, YF), inward=(-1, 0))
    a, b = YB - WIN_Y1, YB - WIN_Y0
    fl.box("win_glass", (a + b) / 2, 0.13, (WIN_SILL + WIN_TOP) / 2, b - a - 0.06,
           0.014, WIN_TOP - WIN_SILL - 0.06, L.M("mat_glass_dusk"), c, bevel=0)
    for k in range(4):
        fl.box("win_mullion_%d" % k, a + (b - a) * (k + 1) / 5.0, 0.08,
               (WIN_SILL + WIN_TOP) / 2, 0.036, 0.062, WIN_TOP - WIN_SILL,
               L.M("mat_int_paint_green"), c, bevel=0.004)
    fl.box("win_transom", (a + b) / 2, 0.08, (WIN_SILL + WIN_TOP) / 2 + 0.30,
           b - a, 0.062, 0.036, L.M("mat_int_paint_green"), c, bevel=0.004)
    # THE SERVING SHELF: a board across the opening, worn pale in the middle by
    # thirty years of trays sliding out over it
    fl.box("serving_shelf", (a + b) / 2, -0.16, WIN_SILL - 0.02, b - a + 0.26, 0.34,
           0.050, L.M("mat_int_floor_pale"), c, bevel=0.012)
    fl.box("serving_bracket_a", a + 0.16, -0.26, WIN_SILL - 0.20, 0.06, 0.16, 0.30,
           L.M("mat_int_beam"), c, bevel=0.006)
    fl.box("serving_bracket_b", b - 0.16, -0.26, WIN_SILL - 0.20, 0.06, 0.16, 0.30,
           L.M("mat_int_beam"), c, bevel=0.006)
    # the shutter, hooked open flat against the inside wall
    fl.box("win_shutter", b + 0.62, -0.055, (WIN_SILL + WIN_TOP) / 2, 1.05, 0.040,
           WIN_TOP - WIN_SILL, L.M("mat_int_paint_green"), c, bevel=0.008)
    fl.box("win_shutter_batten", b + 0.62, -0.085, (WIN_SILL + WIN_TOP) / 2 + 0.36,
           1.05, 0.022, 0.070, L.M("mat_int_beam"), c, bevel=0.006)

    # --- the door, standing open on the square ------------------------------
    da, db = YB - DOOR_Y1, YB - DOOR_Y0
    L.opening_frame("doorframe2", fl, da, db, DOOR_TOP, c=c, mat="mat_int_beam")
    # STANDING FULLY OPEN, perpendicular to the wall.  A leaf swung back flat
    # against the outside face lies straight across its own opening from this
    # camera; at ninety degrees it is a thin edge beside the hole, and the way
    # out is unmistakable.
    L.box("door_leaf", (-0.62, DOOR_Y0 + 0.06, 1.05), (0.58, 0.026, 1.05),
          "mat_int_plank", c, bevel=0.008, tex_off=L.toff())
    for k in range(3):
        L.box("door_batten_%d" % k, (-0.62, DOOR_Y0 + 0.10, 0.36 + k * 0.66),
              (0.58, 0.020, 0.055), "mat_int_beam", c, bevel=0.006)
    L.cyl("door_handle", (-1.06, DOOR_Y0 + 0.02, 1.02), 0.016, 0.15, "mat_int_iron",
          c, axis="Y", verts=8, bevel=0)
    fl.box("door_threshold", (da + db) / 2, 0.04, 0.018, db - da + 0.10, 0.34, 0.036,
           L.M("mat_int_stone"), c, bevel=0.008)

    # --- what is out there: the square at dusk, and its lamp ----------------
    L.dusk_card("dusk_backdrop", (-1.85, 3.70, 1.55), (0.05, 3.40, 1.90), c="SHELL",
                top=(0.105, 0.132, 0.205), bottom=(0.020, 0.026, 0.044), strength=1.0)
    L.box("dusk_ground", (-0.95, 3.60, -0.03), (0.90, 3.30, 0.03), "mat_int_stone", c,
          bevel=0)
    L.cyl("dusk_lamppost", (-0.92, 5.85, 1.20), 0.042, 2.40, "mat_int_iron", c,
          verts=8, bevel=0.004)
    L.box("dusk_lamphead", (-0.92, 5.85, 2.50), (0.095, 0.095, 0.145),
          "mat_int_lampglass", c, bevel=0.010)
    # a stall's awning corner in the square, because it is Emberwake out there
    L.box("dusk_awning", (-1.35, 2.15, 2.15), (0.62, 0.90, 0.030), "mat_int_paint_red",
          c, rot=(0, deg(11), 0), bevel=0.008)


# ================================================================== lights ==

def build_lights(kit):
    mcx = (MO_X0 + MO_X1) / 2
    # THE OVEN.  A bake-oven's mouth is a slot, so its throw is narrower and
    # hotter than a hearth's -- it lays a bar of light across the platform and
    # up the hood, and almost nothing on the shop floor.
    # a bake-oven is a SLOT, so its throw is narrow -- and it is banked, not
    # roaring: tonight's last batch is already in.
    L.hearth_rig("oven", mcx - 0.22, OV_Y0 + 0.50, MO_Z0 - 0.24, (0, -1), energy=0.34,
                 mouth_spread=84)
    up = L.light("LGT_hood_wash", "AREA", (mcx, OV_Y0 - 0.34, MO_Z1 + 0.16), 138.0,
                 (1.0, 0.52, 0.22), shape="RECTANGLE", sx=1.40, sy=0.45, spread=96)
    L.aim(up, (mcx, OV_Y0 + 0.20, HOOD_TOP))

    # the working light: one big lantern over the bench, because you cannot
    # weigh flour by firelight
    L.hang_lantern(kit, "lantern_bench", (BX0 + BX1) / 2 - 0.62, (BY0 + BY1) / 2 - 0.15,
                   2.06, hang_from=CEIL - 0.26, energy=104.0)
    L.hang_lantern(kit, "lantern_door", 1.15, 2.20, 2.06, hang_from=CEIL - 0.26,
                   energy=64.0)

    # THE TWO COLD SHAFTS.  The bay window at working height and the clerestory
    # above it: two parallel bars of dusk cutting the flour haze, which is the
    # one image this room exists to make.
    w = L.light("LGT_bay", "AREA", (0.16, (WIN_Y0 + WIN_Y1) / 2, 1.62), 158.0,
                (0.54, 0.64, 0.90), shape="RECTANGLE", sx=1.55, sy=1.20, spread=92)
    L.aim(w, (3.60, (WIN_Y0 + WIN_Y1) / 2 - 0.90, 0.55))
    cl = L.light("LGT_clerestory", "AREA", (0.16, (WIN_Y0 + WIN_Y1) / 2,
                                            (CLER_Z0 + CLER_Z1) / 2), 118.0,
                 (0.50, 0.60, 0.88), shape="RECTANGLE", sx=1.50, sy=0.34, spread=80)
    L.aim(cl, (3.90, (WIN_Y0 + WIN_Y1) / 2 - 1.60, 0.60))
    L.light("LGT_square_lamp", "POINT", (-0.92, 5.85, 2.50), 128.0, (1.0, 0.66, 0.30),
            0.10)
    d = L.light("LGT_dusk_door", "AREA", (0.16, (DOOR_Y0 + DOOR_Y1) / 2, 1.20), 62.0,
                (0.52, 0.62, 0.86), shape="RECTANGLE", sx=1.10, sy=1.60, spread=140)
    L.aim(d, (3.00, (DOOR_Y0 + DOOR_Y1) / 2 - 1.10, 0.60))

    a = L.light("LGT_open_amb", "AREA", ((XL + XR) / 2, YF - 3.2, 2.85), 30.0,
                (0.40, 0.50, 0.70), shape="RECTANGLE", sx=8.0, sy=4.4, spread=170)
    L.aim(a, ((XL + XR) / 2, (YF + YB) / 2, 1.2))

    w2 = bpy.data.worlds.new("EMBBAKE_WORLD")
    w2.use_nodes = True
    bg = next(n for n in w2.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.058, 0.066, 0.090, 1.0)
    bg.inputs["Strength"].default_value = 0.18
    bpy.context.scene.world = w2

    # FLOUR IN THE AIR.  Denser than the inn's haze and paler: a bakehouse at
    # the end of a baking day is genuinely dusty, and it is what turns two
    # window shafts into two visible beams.
    L.fog_box("FOG_FLOUR", ((XL + XR_BACK) / 2 - 0.1, (YF + YB) / 2 + 0.3, 1.55),
              ((XR_BACK - XL) / 2 + 0.35, (YB - YF) / 2 - 0.35, 1.50),
              density=0.0042, color=(0.92, 0.86, 0.78), aniso=0.42)


# ================================================================== camera ==

# EYE LEVEL, LONG LENS, CLOSE.  v1 put the camera at z 3.89 -- above the
# ceiling -- and the near boards ate the top quarter of the frame in black.
# The fix is also the room's character: pitch 12 and a 28-degree lens puts you
# standing in the doorway of a working bakehouse, with the oven filling a
# seventh of the frame's width.  Against the inn's 40-degree wide-angle at
# pitch 13 these two rooms could not be mistaken for each other, which is the
# whole assignment.
CAM = dict(aim=(2.90, 4.00, 1.05), vh=4.05, pitch=12.0, az=24.0, fov=30.0)

FRAME_CHECKS = [
    ("oven mouth", ((MO_X0 + MO_X1) / 2, OV_Y0 - 0.02, (MO_Z0 + MO_Z1) / 2)),
    ("bay window", (0.06, (WIN_Y0 + WIN_Y1) / 2, 1.55)),
    ("door opening", (0.06, (DOOR_Y0 + DOOR_Y1) / 2, 1.05)),
    ("work bench", ((BX0 + BX1) / 2, (BY0 + BY1) / 2, 0.90)),
    ("cooling rack", (PL_X0 + 0.42, 5.30, PL_Z + 0.90)),
    ("hood", ((OV_X0 + OV_X1) / 2, OV_Y0 - 0.20, OV_TOP + 0.30)),
]


def build_cam():
    return L.build_camera("CAM_int_bakery", CAM["aim"], CAM["vh"], CAM["pitch"],
                          CAM["az"], CAM["fov"])


def build_pads():
    L.pad("walk_pad_door", 0.72, (DOOR_Y0 + DOOR_Y1) / 2, 0.82, 1.05)
    L.pad("walk_pad_counter", 0.88, (WIN_Y0 + WIN_Y1) / 2, 0.86, 1.30)
    L.pad("walk_pad_oven", (MO_X0 + MO_X1) / 2, PL_Y0 + 0.62, 1.30, 0.80, z=PL_Z)
    L.pad("walk_pad_bench", (BX0 + BX1) / 2, BY0 - 0.62, 1.70, 0.80)


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
    build_oven()
    build_bakehouse()
    build_shopfloor(kit)
    build_window_and_door()
    build_lights(kit)
    build_pads()
    cam = build_cam()
    if ref:
        L.place_kit(kit["REF_human_1p7"], "REF_scale_a", (2.60, 4.10, 0.0), c="CAM")
        L.place_kit(kit["REF_human_1p7"], "REF_scale_b", (1.20, 2.40, 0.0), c="CAM")
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
