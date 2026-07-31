#!/usr/bin/env python3
"""emb-lake-int -- THE KEEPER'S COTTAGE.  The one interior the story needs.

CANON THIS ROOM SERVES, and it is quoted rather than invented
------------------------------------------------------------
`chapter1.js`, the hearth interaction, verbatim:

    "The hearth.  Grandmother's portrait watches from above the mantel --
     dusted daily, and the eyes still miss nothing."
    "Beneath it, an empty brass hook, worn bright.  The lighter's place,
     between rounds."

and, from the leaving-home cutscene:

    "(Her hand-lamp, off the hook by the door.  Tonight I'm not pretending
     it's for the light.)"
    "The last lamplighter of Emberbrook rose from his grandmother's table,
     and took down his grandmother's flame."

So this room contains, as GEOMETRY: a hearth; a mantel; a portrait over it; an
empty brass hook beneath the portrait; a second empty hook by the door; and
her table.  **Both hooks are empty**, because the scene the player walks into
is the one an hour after he left: he is out on the rounds carrying both.  That
is the whole emotional statement of the room and it costs two absences.

STORY.md §2 adds the trade: the lighter is a seed-ember that burns no fuel and
never goes out, the rounds run in fixed order from the pond lane inward, and
the keeper stands outside the kept -- he grieves the old way, alone.  Which is
why the room is *dusted daily* and nothing has been moved in a year: her chair
is still at the table, her boots are still by the door, and her bed under the
loft is still made.  The map adds herbs over the door and notes this was
Mochi's home until the year she died; the cat is gone and his saucer is not.

THE PLAN, AND WHY IT IS NOT A BOX
---------------------------------
  * OPEN TO THE ROOF.  No ceiling at all over two thirds of the room: rafters,
    purlins and the boarded underside of the slates climb from a 2.30 eave to
    a 4.20 ridge.  The hearth's stone breast goes up with them.
  * A LOFT under the west slope -- Lake's bed, a real deck at 2.05 with its
    joists showing, reached by a real ladder.  It is ART, not walk network: a
    loft you climb is a life upstairs, and there is nothing up there to play.
  * A CANTED ENTRY.  The south-east corner is cut off at 45 degrees and the
    door is in that cut, so the way out faces the camera square-on instead of
    edge-on -- seam canon indoors, solved in the plan rather than in the aim.
  * A BED ALCOVE under the loft: her bed, curtained, in the one part of the
    room the roof does not open over.  Low, dark and kept.

CAMERA PERSONALITY: the story camera.  The inn is wide and low (fov 40); the
bakery is a long working lens (fov 30); this is the TIGHTEST and quietest of
the three -- fov 26, pitch 10, aimed at the mantel so the hook sits within a
few degrees of frame centre.  Held breath, not a survey.

FORMAT: FF9 cutaway.  SCALE: character 1.70, door 2.05, table 0.75, mantel 1.55.

Run headless (ALWAYS -b --python-exit-code 1):
    Blender -b --python-exit-code 1 -P tools/embint_lake_build.py -- \
        --out tools/blends/interiors/emb-lake-int.blend \
        --render docs/qa/interiors/emb-lake-int_v1.png --samples 160
"""
import bpy, math, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import embint_lib as L

CM = L.CM
OUTBLEND = "tools/blends/interiors/emb-lake-int.blend"
SEED = 20260803

# ============================================================== the plan ===
XL, XR = 0.00, 7.20
YF, YB = 0.00, 5.60
CANT_X, CANT_Y = 5.90, 4.30       # the cut corner: (7.20,4.30) -> (5.90,5.60)
EAVE, RIDGE_Z, RIDGE_X = 2.30, 4.20, 3.60
THICK = 0.26

# the hearth, in the back wall
HX0, HX1 = 3.00, 5.20             # the breast
HY = YB - 0.55                    # it projects this far into the room
FO_X0, FO_X1 = 3.52, 4.72         # the fire opening
FO_TOP = 0.98
MANTEL_Z = 1.55
HOOK_Z = 1.80                     # the lighter's place, between rounds
PORT_Z0, PORT_Z1 = 2.08, 2.76     # grandmother

# the loft, under the west slope
LF_X1 = 2.60
# 2.14, not 2.05: the loft's trimmer beam hangs 0.29 below the deck and at
# 2.05 its underside sat at 1.76 -- eight centimetres inside a walking body's
# head.  The gate found it; nobody would have until they walked into it.
LF_Z = 2.14
LAD_X = 2.72

# the bed alcove under the loft
BED_Y0, BED_Y1 = 3.55, YB - 0.10

# the table
TX, TY, TH = 3.05, 2.35, 0.75

# the window in the east wall, and the door in the canted corner
WIN_Y0, WIN_Y1 = 1.15, 2.35
WIN_SILL, WIN_TOP = 0.98, 2.10
DOOR_U0, DOOR_U1 = 0.32, 1.52     # measured along the canted wall
DOOR_TOP = 2.05


def deg(a):
    return math.radians(a)


def cant_frame():
    return L.WallFrame((XR, CANT_Y), (CANT_X, YB), inward=(1, 1))


# =============================================================== the shell ==

def build_floor():
    c = L.coll("SHELL")

    def yfn(y):
        # the cut corner takes a triangle off the east end of the back rows
        if y <= CANT_Y:
            return [(XL - 0.02, XR + 0.02)]
        t = (y - CANT_Y) / (YB - CANT_Y)
        return [(XL - 0.02, XR - (XR - CANT_X) * t + 0.02)]

    L.floor_planks("lake", (YF - 0.02, YB + 0.02), yfn, z=0.0, c=c,
                   mat="mat_int_floor", mat_alt="mat_int_floor_pale", alt=0.12,
                   dir_="x", w=(0.165, 0.235), run=(2.0, 3.8))
    L.floor_void("floor_void_lake", XL, XR, YF, YB, 0.0, c=c)

    # the hearthstone: one slab, and the only part of the floor she never
    # scrubbed pale, because it has had a fire on it for two hundred years
    L.prism("walk_floor_hearthstone",
            [(HX0 - 0.10, HY - 0.62), (HX1 + 0.10, HY - 0.62),
             (HX1 + 0.10, HY + 0.02), (HX0 - 0.10, HY + 0.02)],
            -0.055, 0.004, "mat_int_hearth", c, bevel=0.010)
    # the rug in front of it -- the one colour in a room of browns
    rug = L.box("rug", (3.95, 3.35, 0.008), (1.15, 0.78, 0.008), "mat_int_rug_border", c,
                rot=(0, 0, deg(4)), bevel=0.006)
    L.displace(rug, 0.010, 0.40, levels=3, seed_=2)
    L.box("rug_border", (3.95, 3.35, 0.006), (1.24, 0.87, 0.006),
          "mat_int_rug", c, rot=(0, 0, deg(4)), bevel=0.006)


def build_walls():
    c = "SHELL"
    # back wall (y = YB), running east->west from the cut corner
    fb = L.WallFrame((CANT_X, YB), (XL, YB), inward=(0, 1))
    L.wall_run("wBack", fb, EAVE + 0.30, c=c, style="plaster", wain=0.98, thick=THICK)
    # the gable triangle above it, in stone-coursed rubble like the breast
    for k in range(7):
        z0 = EAVE + 0.30 + k * 0.30
        halfspan = max(0.10, (XR - XL) / 2 * (1 - (z0 - EAVE) / (RIDGE_Z - EAVE)))
        L.box("gable_back_%02d" % k, (RIDGE_X, YB - 0.05, z0 + 0.15),
              (halfspan, 0.10, 0.15), "mat_int_plaster", c, bevel=0.006,
              tex_off=L.toff())

    # east wall (x = XR) up to the cut corner: the window onto the lane
    fe = L.WallFrame((XR, YF), (XR, CANT_Y), inward=(1, 0))
    L.wall_run("wEast", fe, EAVE + 0.30, c=c, style="plaster", wain=0.98, thick=THICK,
               openings=[(WIN_Y0, WIN_Y1, WIN_TOP)])
    L.opening_frame("winframe", fe, WIN_Y0, WIN_Y1, WIN_TOP, c=c, sill=WIN_SILL)

    # THE CANTED CORNER: the door wall, facing south-east
    fc = cant_frame()
    L.wall_run("wCant", fc, EAVE + 0.30, c=c, style="plaster", wain=0.98, thick=THICK,
               openings=[(DOOR_U0, DOOR_U1, DOOR_TOP)])
    L.opening_frame("doorframe", fc, DOOR_U0, DOOR_U1, DOOR_TOP, c=c)

    # west wall (x = XL): the low one, under the loft's eave
    fw = L.WallFrame((XL, YB), (XL, YF), inward=(-1, 0))
    L.wall_run("wWest", fw, EAVE, c=c, style="board", thick=0.20,
               board_mat="mat_int_plank", plate_z=EAVE - 0.10)

    nw = L.box("shadow_nearwall", ((XL + XR) / 2, YF - THICK / 2 - 0.02, EAVE / 2),
               ((XR - XL) / 2 + THICK, THICK / 2, EAVE / 2), "mat_int_plaster",
               L.coll("SHELL"), bevel=0)
    L.hide_from_camera(nw)
    return fb, fe, fc, fw


def build_roof():
    """OPEN TO THE RIDGE.  This is the room's one big move and it costs eleven
    rafters: a cottage with its roof showing cannot be mistaken for a shop with
    a lid on."""
    c = L.coll("SHELL")
    L.rafters("roof", YF - 0.10, YB + 0.10, XL - 0.15, XR + 0.15, EAVE, RIDGE_Z,
              c=c, ridge_x=RIDGE_X, n=8, hide_front=-0.30, purlins=True)
    L.roof_backing("roofvoid", XL - 0.5, XR + 0.5, YF - 0.5, YB + 0.5, 4.55, c=c)
    # a collar tie across the two slopes: the horizontal that stops the roof
    # reading as an open tent
    for y in (1.60, 3.90):
        L.box("collar_%.1f" % y, (RIDGE_X, y, 3.28), ((XR - XL) / 2 - 0.90, 0.075,
                                                      0.085),
              "mat_int_beam", c, bevel=0.010, tex_off=L.toff())


def build_loft():
    c = L.coll("SHELL")
    L.platform("loft", [(XL - 0.05, YF + 0.55), (LF_X1, YB - 0.02)], LF_Z, c=c,
               mat="mat_int_plank", walk=False, joists=True, joist_dir="x")
    # the trimmer beam at the open edge, carried on a post: the loft has to be
    # HELD UP by something the eye can see or it reads as a shelf
    L.box("loft_trimmer", (LF_X1, (YF + 0.55 + YB) / 2, LF_Z - 0.145),
          (0.100, (YB - YF - 0.55) / 2, 0.145), "mat_int_beam", c, bevel=0.012,
          tex_off=L.toff())
    L.box("loft_post", (LF_X1, YF + 0.72, (LF_Z - 0.29) / 2 + 0.02),
          (0.095, 0.095, (LF_Z - 0.29) / 2), "mat_int_beam", c, bevel=0.010,
          tex_off=L.toff())
    L.box("loft_post_b", (LF_X1, 3.42, (LF_Z - 0.29) / 2 + 0.02),
          (0.095, 0.095, (LF_Z - 0.29) / 2), "mat_int_beam", c, bevel=0.010,
          tex_off=L.toff())
    # a low rail along the open edge, and the ladder
    L.box("loft_rail", (LF_X1 - 0.04, (YF + 0.90 + 3.30) / 2, LF_Z + 0.42),
          (0.038, (3.30 - YF - 0.90) / 2, 0.038), "mat_int_wood", c, bevel=0.010)
    for yy in (YF + 0.92, 3.28):
        L.box("loft_rail_post_%.2f" % yy, (LF_X1 - 0.04, yy, LF_Z + 0.22),
              (0.042, 0.042, 0.22), "mat_int_wood", c, bevel=0.008)
    L.ladder("ladder", LAD_X, 1.55, 0.0, LF_Z + 0.16, yaw=deg(180), lean=0.24,
             w=0.50, c="SHELL")

    # WHAT IS UP THERE: a made bed, a blanket folded the way a man folds it,
    # one book.  You see it edge-on and that is enough -- somebody lives here.
    p = L.coll("PROPS")
    L.box("loft_mattress", (1.15, 3.95, LF_Z + 0.10), (0.78, 0.98, 0.10),
          "mat_int_linen", p, bevel=0.030)
    bl = L.box("loft_blanket", (1.15, 4.35, LF_Z + 0.215), (0.80, 0.62, 0.030),
               "mat_int_felt", p, rot=(0, 0, deg(2)), bevel=0.020)
    L.displace(bl, 0.018, 0.35, levels=2, seed_=4)
    L.box("loft_pillow", (1.15, 3.10, LF_Z + 0.235), (0.36, 0.20, 0.085),
          "mat_int_linen", p, rot=(0, 0, deg(-6)), bevel=0.040)
    L.box("loft_book", (2.05, 3.05, LF_Z + 0.032), (0.11, 0.15, 0.032),
          "mat_int_oilskin", p, rot=(0, 0, deg(14)), bevel=0.006)
    L.box("loft_chest", (0.55, 1.55, LF_Z + 0.22), (0.34, 0.46, 0.22),
          "mat_int_plank", p, bevel=0.012, tex_off=L.toff())


def build_hearth():
    """The subject of the room, and of the chapter."""
    c = L.coll("HEARTH")
    cx = (HX0 + HX1) / 2
    # the breast: coursed stone from the floor to the rafters
    z = 0.0
    k = 0
    while z < RIDGE_Z - 0.60:
        h = min(0.235, RIDGE_Z - 0.60 - z)
        # it tapers above the mantel, the way a chimney does
        # the taper starts ABOVE the portrait, not at the mantel.  v1 began it
        # at 1.55 and by z=1.70 the breast face had walked 20 mm north of the
        # brass hook and 50 mm north of grandmother -- the two objects this
        # room exists for were buried inside the chimney.  A chimney does
        # gather in; it does not do it through its own mantelpiece.
        TAPER_Z = PORT_Z1 + 0.18
        t = max(0.0, (z - TAPER_Z) / (RIDGE_Z - 0.60 - TAPER_Z))
        half = (HX1 - HX0) / 2 * (1 - t) + 0.42 * t
        dep = 0.55 * (1 - t) + 0.30 * t
        spans = ([(cx - half, cx + half)] if (z > FO_TOP - 0.02 or z + h < 0.02)
                 else [(cx - half, FO_X0), (FO_X1, cx + half)])
        for (sx0, sx1) in spans:
            if sx1 - sx0 < 0.04:
                continue
            ob = L.box("breast_%02d_%.2f" % (k, sx0), ((sx0 + sx1) / 2,
                                                       YB - dep / 2, z + h / 2),
                       ((sx1 - sx0) / 2, dep / 2, h / 2 - 0.006), "mat_int_stone", c,
                       bevel=0.010, tex_off=L.toff())
            L.displace(ob, 0.014, 0.28, levels=2, seed_=k)
        z += h
        k += 1
    # the firebox: sooted, with a heavy timber lintel over the opening
    L.box("firebox_back", (cx, YB - 0.10, FO_TOP / 2), ((FO_X1 - FO_X0) / 2, 0.10,
                                                        FO_TOP / 2),
          "mat_int_soot", c, bevel=0)
    for s in (-1, 1):
        L.box("firebox_cheek_%d" % (s > 0), (cx + s * ((FO_X1 - FO_X0) / 2 - 0.03),
                                             YB - 0.32, FO_TOP / 2),
              (0.030, 0.24, FO_TOP / 2), "mat_int_soot", c, bevel=0)
    L.box("firebox_crown", (cx, YB - 0.32, FO_TOP - 0.03), ((FO_X1 - FO_X0) / 2, 0.24,
                                                            0.030),
          "mat_int_soot", c, bevel=0)
    L.box("fire_lintel", (cx, HY + 0.04, FO_TOP + 0.10), ((FO_X1 - FO_X0) / 2 + 0.26,
                                                          0.14, 0.10),
          "mat_int_beam", c, bevel=0.014, tex_off=L.toff())

    # THE FIRE: low and banked.  He went out at dusk and he will be back; a
    # blaze in an empty house is a different story than the one this is.
    fy = YB - 0.24
    for k, (ox, oy, oz, rz) in enumerate(((-0.14, 0.02, 0.09, 0.20),
                                          (0.10, -0.04, 0.10, -0.30),
                                          (-0.01, 0.05, 0.19, 0.08))):
        L.cyl("firelog_%d" % k, (cx + ox, fy + oy, oz), 0.068, 0.54, "mat_int_charlog",
              c, axis="X", verts=10, rot=(0, 0, rz), bevel=0.006)
    L.prism("fire_embers", [(cx - 0.38, fy - 0.20), (cx + 0.38, fy - 0.20),
                            (cx + 0.38, fy + 0.18), (cx - 0.38, fy + 0.18)],
            0.005, 0.050, "mat_embers", c)
    for k, (ox, h, r) in enumerate(((-0.26, 0.20, 0.052), (-0.16, 0.30, 0.066),
                                    (-0.06, 0.38, 0.076), (0.05, 0.30, 0.066),
                                    (0.16, 0.20, 0.050), (0.25, 0.13, 0.038))):
        L.lathe("flame_%d" % k, [(0.0, 0.0), (r, 0.05), (r * 0.7, h * 0.55), (0.0, h)],
                (cx + ox, fy + L.jit(0.04), 0.09), L.M("mat_fire"), c, segments=10)
    L.sphere("fire_ash", (cx, fy - 0.02, 0.03), 0.26, "mat_int_ash", c,
             scale=(1.6, 0.9, 0.14))
    # the crane and the cold kettle swung off the fire
    L.cyl("crane_post", (FO_X1 - 0.06, YB - 0.30, 0.60), 0.022, 1.16, "mat_int_iron", c,
          verts=10)
    L.cyl("crane_arm", (cx + 0.16, YB - 0.28, 1.14), 0.019, 0.62, "mat_int_iron", c,
          axis="X", verts=8)
    L.lathe("kettle", [(0.0, 0.0), (0.12, 0.03), (0.145, 0.12), (0.105, 0.22),
                       (0.070, 0.25), (0.070, 0.28)],
            (cx - 0.06, YB - 0.28, 0.62), L.M("mat_int_iron"), c, segments=18,
            thickness=0.008)

    # ---- THE MANTEL, and the two things on the wall above it --------------
    L.box("mantel", (cx, HY - 0.08, MANTEL_Z), ((HX1 - HX0) / 2 + 0.05, 0.15, 0.045),
          "mat_int_wood", c, bevel=0.014, tex_off=L.toff())
    L.box("mantel_corbel_a", (HX0 + 0.20, HY - 0.02, MANTEL_Z - 0.14), (0.075, 0.10,
                                                                        0.10),
          "mat_int_wood", c, bevel=0.010)
    L.box("mantel_corbel_b", (HX1 - 0.20, HY - 0.02, MANTEL_Z - 0.14), (0.075, 0.10,
                                                                        0.10),
          "mat_int_wood", c, bevel=0.010)

    # ===================================================================
    # THE EMPTY BRASS HOOK.  "The lighter's place, between rounds."
    # It is empty because he is out on the rounds carrying it, which is the
    # only fact about this room the player needs to feel.  Everything else
    # here is context for a hook with nothing on it.
    # It is deliberately over-scaled and over-lit for its size: at nine metres
    # a true-scale hook is four pixels, and a detail nobody can see is a detail
    # that is not in the scene.
    # ===================================================================
    # the wrought back-plate, the arm, and a bold J-curl.  At ten metres a
    # true-scale hook is four pixels; this one is built at about 1.4x and given
    # its own small spot, because the room's subject is a thing that is NOT
    # there and an absence has to be legible or it is only darkness.
    L.box("hook_plate", (cx, YB - 0.575, HOOK_Z), (0.055, 0.028, 0.145),
          "mat_int_iron", c, bevel=0.010)
    L.sphere("hook_boss_a", (cx, YB - 0.600, HOOK_Z + 0.115), 0.026, "mat_int_iron",
             c, segs=10, rings=6, scale=(1.0, 0.5, 1.0))
    L.sphere("hook_boss_b", (cx, YB - 0.600, HOOK_Z - 0.115), 0.026, "mat_int_iron",
             c, segs=10, rings=6, scale=(1.0, 0.5, 1.0))
    L.cyl("hook_stem", (cx, YB - 0.680, HOOK_Z + 0.045), 0.020, 0.20, "mat_int_brass",
          c, axis="Y", verts=12, bevel=0)
    for k in range(9):                      # the curl of the hook
        a = deg(-100) + deg(250) * (k / 8.0)
        L.cyl("hook_curl_%d" % k, (cx + 0.074 * math.cos(a), YB - 0.780,
                                   HOOK_Z - 0.030 + 0.074 * math.sin(a)),
              0.019, 0.036, "mat_int_brass", c, axis="Y", verts=10, bevel=0)
    L.sphere("hook_tip", (cx + 0.074 * math.cos(deg(150)), YB - 0.780,
                          HOOK_Z - 0.030 + 0.074 * math.sin(deg(150))), 0.026,
             "mat_int_brass", c, segs=10, rings=6)
    # THE WORN RING.  Three hundred years of dusks, and one year of a boy
    # taking it down and putting it back: the plaster round the hook is
    # polished pale in a circle the exact size of the lighter's body.
    L.cyl("hook_wear", (cx, YB - 0.558, HOOK_Z - 0.055), 0.155, 0.008,
          "mat_int_floor_pale", c, axis="Y", verts=24, bevel=0)

    # ---- GRANDMOTHER, above it ---------------------------------------------
    L.box("portrait_canvas", (cx, YB - 0.565, (PORT_Z0 + PORT_Z1) / 2), (0.24, 0.018,
                                                                        (PORT_Z1 - PORT_Z0) / 2),
          "mat_int_oilskin", c, bevel=0.004)
    L.box("portrait_frame", (cx, YB - 0.545, (PORT_Z0 + PORT_Z1) / 2), (0.285, 0.030,
                                                                       (PORT_Z1 - PORT_Z0) / 2 + 0.045),
          "mat_int_brass", c, bevel=0.010)
    L.box("portrait_frame_in", (cx, YB - 0.560, (PORT_Z0 + PORT_Z1) / 2),
          (0.245, 0.026, (PORT_Z1 - PORT_Z0) / 2 + 0.008), "mat_int_wood", c,
          bevel=0.006)
    # the sitter: a pale collar and face-shape, no features.  At this distance a
    # painted face is a smudge either way, and a smudge that reads as a person
    # looking out of the frame is the whole point of the line about the eyes.
    L.sphere("portrait_head", (cx, YB - 0.580, PORT_Z1 - 0.20), 0.075,
             "mat_int_linen", c, scale=(0.85, 0.22, 1.05))
    L.box("portrait_shoulders", (cx, YB - 0.580, PORT_Z1 - 0.40), (0.135, 0.014,
                                                                   0.095),
          "mat_int_felt", c, bevel=0.030)
    L.box("portrait_collar", (cx, YB - 0.582, PORT_Z1 - 0.315), (0.070, 0.012, 0.030),
          "mat_int_linen", c, bevel=0.014)

    # ---- ON the mantel: the trade, and one thing that is not the trade -----
    L.lathe("oil_can", [(0.0, 0.0), (0.055, 0.008), (0.062, 0.10), (0.030, 0.145),
                        (0.034, 0.16)],
            (HX0 + 0.28, HY - 0.08, MANTEL_Z + 0.045), L.M("mat_int_copper"), c,
            segments=14, thickness=0.005)
    L.cyl("oil_spout", (HX0 + 0.40, HY - 0.13, MANTEL_Z + 0.17), 0.010, 0.16,
          "mat_int_copper", c, axis="X", verts=8, rot=(0, deg(28), deg(-16)), bevel=0)
    L.box("wick_tin", (HX0 + 0.66, HY - 0.09, MANTEL_Z + 0.085), (0.085, 0.060, 0.040),
          "mat_int_iron", c, rot=(0, 0, deg(7)), bevel=0.008)
    for k in range(5):
        L.cyl("taper_%d" % k, (HX1 - 0.34 + L.jit(0.02), HY - 0.10, MANTEL_Z + 0.14),
              0.007, 0.19, "mat_int_wax", c, verts=6,
              rot=(L.jit(0.10), L.jit(0.10), 0), bevel=0)
    L.lathe("taper_jar", [(0.0, 0.0), (0.055, 0.006), (0.058, 0.11), (0.052, 0.114)],
            (HX1 - 0.34, HY - 0.10, MANTEL_Z + 0.045), L.M("mat_int_crock_blue"), c,
            segments=14, thickness=0.004)
    # a pebble.  Not the trade.  Somebody picked it up on a walk and it stayed.
    L.sphere("mantel_pebble", (HX1 - 0.06, HY - 0.10, MANTEL_Z + 0.068), 0.026,
             "mat_int_stone", c, scale=(1.2, 0.9, 0.7))

    # ---- THE ROUNDS, chalked on the breast where his hand can reach --------
    # STORY.md: low ground first (the pond lane), then inward, ending at the
    # lamps nearest the Heartlight -- "closing the ring" before full dark.
    for k in range(6):
        L.box("rounds_mark_%d" % k, (HX1 - 0.16, YB - 0.655, 1.06 - k * 0.085),
              (0.075 if k % 2 else 0.055, 0.005, 0.008), "mat_int_wax", c,
              rot=(0, 0, 0), bevel=0)

    # ---- MOCHI'S OLD SPOTS -------------------------------------------------
    # He left the year she died (map note).  What is left is a saucer with a
    # year of dust in it that nobody has been able to put away.
    L.lathe("cat_saucer", [(0.0, 0.0), (0.085, 0.008), (0.092, 0.026), (0.080, 0.030)],
            (HX1 + 0.30, HY - 0.34, 0.004), L.M("mat_int_crock"), c, segments=16,
            thickness=0.004)
    L.cyl("cat_saucer_dust", (HX1 + 0.30, HY - 0.34, 0.020), 0.070, 0.006,
          "mat_int_ash", c, verts=16, bevel=0)


def build_room(kit):
    """Her table, her chair, her boots, her bed.  Kept."""
    c = L.coll("PROPS")
    # --- THE TABLE ---------------------------------------------------------
    L.box("table_top", (TX, TY, TH - 0.030), (0.86, 0.60, 0.030), "mat_int_floor_pale",
          c, bevel=0.012, tex_off=L.toff())
    L.box("table_rail", (TX, TY - 0.46, TH - 0.115), (0.74, 0.040, 0.055),
          "mat_int_beam", c, bevel=0.006, tex_off=L.toff())
    for (lx, ly) in ((TX - 0.72, TY - 0.46), (TX + 0.72, TY - 0.46),
                     (TX - 0.72, TY + 0.46), (TX + 0.72, TY + 0.46)):
        L.lathe("table_leg_%.2f_%.2f" % (lx, ly),
                [(0.0, 0.0), (0.052, 0.02), (0.042, 0.20), (0.058, 0.33),
                 (0.038, 0.50), (0.046, TH - 0.06), (0.050, TH - 0.06)],
                (lx, ly, 0.0), L.M("mat_int_wood"), c, segments=12)

    # TWO CHAIRS.  One is pulled out and lived in; the other has not moved in a
    # year and has a folded shawl over its back.
    _chair("chair_lake", TX - 0.10, TY - 0.86, deg(6), c, used=True)
    _chair("chair_gran", TX + 0.05, TY + 0.88, deg(184), c, used=False)
    sh = L.box("gran_shawl", (TX + 0.05, TY + 1.06, 0.86), (0.24, 0.045, 0.20),
               "mat_int_felt", c, rot=(deg(4), 0, deg(184)), bevel=0.030)
    L.displace(sh, 0.020, 0.30, levels=2, seed_=6)

    # ON the table: one bowl washed and turned over, one cup the same way, and
    # the whetstone he sharpens the wick-scissors on.  Nothing is out.
    L.lathe("bowl_up", [(0.0, 0.0), (0.115, 0.006), (0.118, 0.014), (0.100, 0.070),
                        (0.0, 0.078)],
            (TX - 0.34, TY + 0.10, TH), L.M("mat_int_crock"), c, segments=18,
            thickness=0.005)
    L.lathe("cup_up", [(0.0, 0.0), (0.046, 0.004), (0.048, 0.010), (0.040, 0.088),
                       (0.0, 0.092)],
            (TX + 0.24, TY - 0.14, TH), L.M("mat_int_crock_blue"), c, segments=16,
            thickness=0.004)
    L.box("whetstone", (TX + 0.52, TY + 0.16, TH + 0.014), (0.085, 0.038, 0.014),
          "mat_int_stone", c, rot=(0, 0, deg(-12)), bevel=0.006)
    L.box("scissors", (TX + 0.50, TY + 0.02, TH + 0.008), (0.075, 0.014, 0.008),
          "mat_int_iron", c, rot=(0, 0, deg(28)), bevel=0.004)

    # --- HER BED, under the loft, still made --------------------------------
    bx = 1.35
    L.box("bed_frame", (bx, (BED_Y0 + BED_Y1) / 2, 0.24), (0.72, (BED_Y1 - BED_Y0) / 2,
                                                           0.24),
          "mat_int_wood", c, bevel=0.012, tex_off=L.toff())
    L.box("bed_mattress", (bx, (BED_Y0 + BED_Y1) / 2, 0.55), (0.70, (BED_Y1 - BED_Y0) / 2
                                                              - 0.03, 0.09),
          "mat_int_linen", c, bevel=0.030)
    bq = L.box("bed_quilt", (bx, (BED_Y0 + BED_Y1) / 2 + 0.10, 0.655),
               (0.72, (BED_Y1 - BED_Y0) / 2 - 0.14, 0.030), "mat_int_rug", c,
               bevel=0.020)
    L.displace(bq, 0.014, 0.40, levels=2, seed_=7)
    L.box("bed_pillow", (bx, BED_Y1 - 0.34, 0.70), (0.42, 0.20, 0.085), "mat_int_linen",
          c, rot=(0, 0, deg(3)), bevel=0.040)
    L.box("bed_head", (bx, BED_Y1 - 0.02, 0.72), (0.72, 0.040, 0.48), "mat_int_wood", c,
          bevel=0.012, tex_off=L.toff())
    # the curtain, half drawn: the alcove is kept, not sealed
    cur = L.box("bed_curtain", (bx + 0.60, (BED_Y0 + BED_Y1) / 2 - 0.30, 1.02),
                (0.045, 0.42, 1.02), "mat_int_felt", c, rot=(0, 0, deg(-8)),
                bevel=0.030)
    L.displace(cur, 0.030, 0.24, levels=3, seed_=8)
    L.cyl("bed_curtain_rail", (bx + 0.30, (BED_Y0 + BED_Y1) / 2, LF_Z - 0.22), 0.016,
          1.10, "mat_int_iron", c, axis="Y", verts=8)

    # --- the dresser on the west wall, and everything a keeper's house keeps -
    L.box("dresser_carcass", (0.42, 1.65, 0.44), (0.30, 0.62, 0.44), "mat_int_wood", c,
          bevel=0.010, tex_off=L.toff())
    L.box("dresser_top", (0.44, 1.65, 0.90), (0.33, 0.66, 0.024), "mat_int_wood", c,
          bevel=0.010, tex_off=L.toff())
    for k, z in enumerate((1.22, 1.58, 1.94)):
        L.box("dresser_shelf_%d" % k, (0.34, 1.65, z), (0.22, 0.62, 0.020),
              "mat_int_plank", c, bevel=0.006, tex_off=L.toff())
        for j in range(4):
            L.lathe("dresser_crock_%d_%d" % (k, j),
                    [(0.0, 0.0), (0.062, 0.008), (0.068, 0.09), (0.050, 0.14),
                     (0.055, 0.152)],
                    (0.34, 1.65 - 0.44 + j * 0.29, z + 0.020),
                    L.M("mat_int_crock" if (j + k) % 2 else "mat_int_crock_blue"), c,
                    segments=14, thickness=0.005)

    # --- the door end: HER BOOTS, the herbs, and the SECOND empty hook -------
    fc = cant_frame()
    # herbs over the door (the map's own note), on a string across the head
    for k in range(6):
        u = DOOR_U0 + 0.16 + k * 0.19
        p = fc.w(u, -0.09, DOOR_TOP + 0.16)
        for j in range(5):
            L.cyl("herb_%d_%d" % (k, j), (p[0] + L.jit(0.02), p[1] + L.jit(0.02),
                                          p[2] - 0.11 + L.jit(0.02)),
                  0.006, 0.22, "mat_int_felt", c, verts=5,
                  rot=(L.jit(0.16), L.jit(0.16), 0), bevel=0)
        L.cyl("herb_tie_%d" % k, (p[0], p[1], p[2]), 0.012, 0.035, "mat_int_bowlwood",
              c, verts=8, bevel=0)
    fc.box("herb_string", (DOOR_U0 + DOOR_U1) / 2, -0.10, DOOR_TOP + 0.17,
           DOOR_U1 - DOOR_U0 + 0.10, 0.010, 0.010, L.M("mat_int_bowlwood"), c, bevel=0)

    # THE SECOND EMPTY HOOK.  "Her hand-lamp, off the hook by the door."
    fc.box("lamphook_plate", DOOR_U1 + 0.34, -0.038, 1.62, 0.10, 0.038, 0.12,
           L.M("mat_int_iron"), c, bevel=0.008)
    fc.cyl("lamphook_peg", DOOR_U1 + 0.34, -0.13, 1.64, 0.016, 0.17,
           L.M("mat_int_iron"), c, axis="V", verts=8)
    fc.cyl("lamphook_wear", DOOR_U1 + 0.34, -0.026, 1.52, 0.075, 0.008,
           L.M("mat_int_floor_pale"), c, axis="V", verts=18)

    # her boots, exactly where she left them, side by side, which is the tell:
    # nobody wears them, so nobody has knocked them over
    pb = fc.w(DOOR_U1 + 0.62, -0.28, 0.0)
    for k, off in enumerate((-0.10, 0.10)):
        L.box("gran_boot_%d" % k, (pb[0] + off * 0.9, pb[1] + off * 0.4, 0.11),
              (0.055, 0.115, 0.11), "mat_int_oilskin", c, rot=(0, 0, deg(-32)),
              bevel=0.030)
        L.box("gran_boot_%d_leg" % k, (pb[0] + off * 0.9, pb[1] + off * 0.4 - 0.02,
                                       0.30),
              (0.050, 0.050, 0.12), "mat_int_oilskin", c, rot=(0, 0, deg(-32)),
              bevel=0.020)

    # the height marks scratched on the door jamb: a boy, measured every year,
    # and then not
    for k in range(7):
        fc.box("height_%d" % k, DOOR_U0 - 0.10, -0.020, 0.72 + k * 0.115, 0.010,
               0.012, 0.006, L.M("mat_int_ink"), c, bevel=0)

    # the wood basket and the water pail: a house that heats itself
    L.place_kit(kit["kit_crate"], "wood_basket", (HX0 - 0.58, HY - 0.16, 0.0),
                rot=(0, 0, deg(-16)), c="PROPS")
    for k in range(9):
        L.cyl("split_log_%d" % k, (HX0 - 0.58 + L.jit(0.14), HY - 0.16 + L.jit(0.12),
                                   0.42 + (k // 4) * 0.10),
              0.058, 0.40, "mat_int_bowlwood" if k % 3 else "mat_int_charlog", c,
              axis="X", verts=8, rot=(0, 0, L.jit(0.4)), bevel=0.004)
    L.place_kit(kit["kit_bucket"], "water_pail", (0.98, 0.70, 0.0), rot=(0, 0, deg(24)),
                c="PROPS")


def _chair(name, x, y, rz, c, used=True):
    L.box(name + "_seat", (x, y, 0.45), (0.21, 0.21, 0.022), "mat_int_wood", c,
          rot=(0, 0, rz), bevel=0.008, tex_off=L.toff())
    for k in range(3):
        L.box(name + "_slat_%d" % k, (x - 0.19 * math.sin(rz), y + 0.19 * math.cos(rz),
                                      0.64 + k * 0.145),
              (0.19, 0.018, 0.033), "mat_int_wood", c, rot=(0, 0, rz), bevel=0.006,
              tex_off=L.toff())
    for (sx, sy) in ((-0.185, -0.185), (0.185, -0.185), (-0.185, 0.185),
                     (0.185, 0.185)):
        px = x + sx * math.cos(rz) - sy * math.sin(rz)
        py = y + sx * math.sin(rz) + sy * math.cos(rz)
        back = sy > 0
        L.cyl(name + "_leg_%.2f_%.2f" % (sx, sy), (px, py, 0.92 if back else 0.225),
              0.019, 1.84 if back else 0.45, "mat_int_wood", c, verts=8, bevel=0.004)
    if used:
        # the cushion with the hollow worn into it, and the frayed arm the cat
        # used for twelve years
        cu = L.box(name + "_cushion", (x, y, 0.478), (0.185, 0.185, 0.030),
                   "mat_int_felt", c, rot=(0, 0, rz), bevel=0.026)
        L.displace(cu, 0.014, 0.35, levels=2, seed_=9)


def build_openings():
    c = L.coll("SHELL")
    fc = cant_frame()
    fe = L.WallFrame((XR, YF), (XR, CANT_Y), inward=(1, 0))
    # the door, standing open on the lane: he went out and did not lock it,
    # because nobody in Emberbrook locks anything
    dn = fc.n
    lc = fc.w((DOOR_U0 + DOOR_U1) / 2, 0.0, 0.0)
    hinge = fc.w(DOOR_U0 + 0.03, 0.10, 0.0)
    L.box("door_leaf", (hinge[0] + dn.x * 0.60 - fc.d.x * 0.02,
                        hinge[1] + dn.y * 0.60 - fc.d.y * 0.02, 1.02),
          (0.026, 0.60, 1.02), "mat_int_plank", c,
          rot=(0, 0, fc.yaw + deg(90)), bevel=0.008, tex_off=L.toff())
    for k in range(3):
        L.box("door_batten_%d" % k, (hinge[0] + dn.x * 0.60 + fc.d.x * 0.02,
                                     hinge[1] + dn.y * 0.60 + fc.d.y * 0.02,
                                     0.34 + k * 0.66),
              (0.020, 0.60, 0.055), "mat_int_beam", c, rot=(0, 0, fc.yaw + deg(90)),
              bevel=0.006)
    fc.box("door_threshold", (DOOR_U0 + DOOR_U1) / 2, 0.04, 0.018,
           DOOR_U1 - DOOR_U0 + 0.10, 0.34, 0.036, L.M("mat_int_stone"), c, bevel=0.008)

    # the window, small and deep-set the way a cottage window is
    fe.box("win_glass", (WIN_Y0 + WIN_Y1) / 2, 0.13, (WIN_SILL + WIN_TOP) / 2,
           WIN_Y1 - WIN_Y0 - 0.06, 0.014, WIN_TOP - WIN_SILL - 0.06,
           L.M("mat_glass_dusk"), c, bevel=0)
    for k in range(2):
        fe.box("win_mullion_%d" % k, WIN_Y0 + (WIN_Y1 - WIN_Y0) * (k + 1) / 3.0, 0.08,
               (WIN_SILL + WIN_TOP) / 2, 0.036, 0.060, WIN_TOP - WIN_SILL,
               L.M("mat_int_paint_green"), c, bevel=0.004)
    fe.box("win_transom", (WIN_Y0 + WIN_Y1) / 2, 0.08, (WIN_SILL + WIN_TOP) / 2,
           WIN_Y1 - WIN_Y0, 0.060, 0.036, L.M("mat_int_paint_green"), c, bevel=0.004)
    fe.box("win_sill_in", (WIN_Y0 + WIN_Y1) / 2, -0.12, WIN_SILL - 0.03,
           WIN_Y1 - WIN_Y0 + 0.20, 0.24, 0.050, L.M("mat_int_wood"), c, bevel=0.010)

    # the valley at dusk, seen through both: this is the hour of the rounds
    L.dusk_card("dusk_lane", (8.70, 2.60, 1.50), (0.05, 2.60, 1.85), c="SHELL",
                top=(0.086, 0.110, 0.180), bottom=(0.014, 0.020, 0.034), strength=1.0)
    L.dusk_card("dusk_door", (7.55, 6.60, 1.50), (2.30, 0.05, 1.85), c="SHELL",
                top=(0.086, 0.110, 0.180), bottom=(0.014, 0.020, 0.034), strength=1.0)
    L.box("dusk_ground", (8.10, 4.20, -0.03), (1.60, 3.30, 0.03), "mat_int_stone", c,
          bevel=0)
    # THE LAMPPOST outside the door -- the nearest lamp on his own round, and
    # the thing that tells you what this house is for.
    L.cyl("dusk_lamppost", (7.55, 5.85, 1.25), 0.045, 2.50, "mat_int_iron", c, verts=8,
          bevel=0.004)
    L.box("dusk_lamphead", (7.55, 5.85, 2.58), (0.10, 0.10, 0.155), "mat_int_lampglass",
          c, bevel=0.010)


# ================================================================== lights ==

def build_lights(kit):
    cx = (HX0 + HX1) / 2
    fy = YB - 0.26
    # a LOW fire: he banked it before he went out.  Half the energy of the inn's
    # parlour hearth, because the inn is full of people and this house is not.
    L.hearth_rig("fire", cx, fy, -0.06, (0, -1), energy=0.52, mouth_spread=126)

    # THE HOOK'S OWN LIGHT.  Unapologetic: a small warm spot on the mantel wall
    # so the empty brass hook and the portrait above it are the brightest small
    # thing in the frame.  The room's subject is a thing that is NOT there, and
    # an absence has to be lit or it is just darkness.
    sp = L.light("LGT_hook", "SPOT", (cx + 0.55, YB - 1.65, 2.20), 88.0,
                 (1.0, 0.72, 0.42), size=0.12, sx=46.0, sy=0.62)
    L.aim(sp, (cx, YB - 0.60, 1.98))

    # one hanging lamp over the table, and the dresser's own small pool
    L.hang_lantern(kit, "lantern_table", TX + 0.10, TY - 0.10, 1.96,
                   hang_from=3.20, energy=104.0)
    L.light("LGT_dresser", "POINT", (0.62, 1.65, 1.42), 34.0, (1.0, 0.62, 0.30), 0.10)

    # the loft, lit from below by the table lamp only: a dark shelf with a bed
    # on it, which is how a loft looks
    L.light("LGT_loft", "AREA", (1.55, 3.20, LF_Z + 0.55), 22.0, (1.0, 0.66, 0.34),
            shape="RECTANGLE", sx=1.6, sy=1.6, spread=150)

    # dusk through the window and the open door: the cold that makes the fire
    # warm, and the only blue in the picture
    w = L.light("LGT_dusk_win", "AREA", (XR - 0.14, (WIN_Y0 + WIN_Y1) / 2, 1.55), 54.0,
                (0.52, 0.62, 0.88), shape="RECTANGLE", sx=1.05, sy=0.95, spread=130)
    L.aim(w, (XR - 3.2, (WIN_Y0 + WIN_Y1) / 2 - 0.6, 0.70))
    fc = cant_frame()
    dp = fc.w((DOOR_U0 + DOOR_U1) / 2, -0.20, 1.20)
    d = L.light("LGT_dusk_door", "AREA", dp, 78.0, (0.52, 0.62, 0.86),
                shape="RECTANGLE", sx=1.10, sy=1.80, spread=140)
    L.aim(d, (dp[0] - 2.4, dp[1] - 2.4, 0.70))
    L.light("LGT_lane_lamp", "POINT", (7.55, 5.85, 2.58), 128.0, (1.0, 0.66, 0.30),
            0.10)

    a = L.light("LGT_open_amb", "AREA", ((XL + XR) / 2, YF - 3.2, 2.60), 30.0,
                (0.40, 0.50, 0.70), shape="RECTANGLE", sx=8.4, sy=4.4, spread=170)
    L.aim(a, ((XL + XR) / 2, (YF + YB) / 2, 1.1))

    w2 = bpy.data.worlds.new("EMBLAKE_WORLD")
    w2.use_nodes = True
    bg = next(n for n in w2.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.050, 0.058, 0.082, 1.0)
    bg.inputs["Strength"].default_value = 0.15
    bpy.context.scene.world = w2
    L.fog_box("FOG_ROOM", ((XL + XR) / 2, (YF + YB) / 2 + 0.2, 1.45),
              ((XR - XL) / 2 - 0.30, (YB - YF) / 2 - 0.10, 1.40), density=0.0030)


# ================================================================== camera ==

CAM = dict(aim=(4.05, 3.70, 1.32), vh=4.00, pitch=10.0, az=14.0, fov=26.0)

FRAME_CHECKS = [
    ("the empty hook", ((HX0 + HX1) / 2, YB - 0.66, 1.80)),
    ("the portrait", ((HX0 + HX1) / 2, YB - 0.58, 2.42)),
    ("fire opening", ((HX0 + HX1) / 2, YB - 0.30, 0.55)),
    ("door opening", (6.55, 4.95, 1.05)),
    ("her table", (3.05, 2.35, 0.75)),
    ("the loft edge", (2.60, 3.00, 2.05)),
    ("her bed", (1.35, 4.30, 0.65)),
]


def build_cam():
    return L.build_camera("CAM_int_lake", CAM["aim"], CAM["vh"], CAM["pitch"],
                          CAM["az"], CAM["fov"])


def build_pads():
    L.pad("walk_pad_door", 6.05, 4.42, 0.90, 0.90)
    L.pad("walk_pad_hearth", (HX0 + HX1) / 2, HY - 0.92, 1.50, 0.80)
    L.pad("walk_pad_table", TX + 0.32, TY - 1.05, 1.40, 0.72)
    L.pad("walk_pad_bed", 2.62, 4.30, 0.72, 1.10)


# ==================================================================== main ==

def build(ref=False):
    L.wipe()
    L.seed(SEED)
    CM.make_all()
    kit = L.append_kit(["kit_crate", "kit_bucket", "kit_barrel", "kit_rope_coil",
                        "kit_lantern_hanging", "kit_lantern_light", "REF_human_1p7"])
    build_floor()
    build_walls()
    build_roof()
    build_loft()
    build_hearth()
    build_room(kit)
    build_openings()
    build_lights(kit)
    build_pads()
    cam = build_cam()
    if ref:
        L.place_kit(kit["REF_human_1p7"], "REF_scale_a", (4.10, 3.10, 0.0), c="CAM")
        L.place_kit(kit["REF_human_1p7"], "REF_scale_b", (5.85, 3.90, 0.0), c="CAM")
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
