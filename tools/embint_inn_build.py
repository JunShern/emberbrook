#!/usr/bin/env python3
"""emb-inn-int -- THE EMBER HEARTH, Emberbrook's inn: the parlour.

CANON THIS ROOM SERVES
----------------------
STORY.md gives the inn one line and it is a floor plan: *"small -- two rooms
and a warm parlour; rarely a stranger in it."*  So the room is built as three
spaces you can see at once and not as one box:

  THE PARLOUR   the main space, ceiled under the guest rooms (two of them --
                the key board has exactly TWO hooks, and one of them is empty
                tonight because the stranger has already taken her key).
  THE INGLENOOK a stone bay projecting NORTH out of the back wall, its own low
                ceiling under the chimney breast, a settle down each cheek.
                This is the emotional set: Vesper lodges here on arrival night
                and this is the fire she comes back to after the Hush.
  THE SNUG      a step DOWN and through a post-and-beam opening to the west --
                the older half of the building, no ceiling, open to its own
                mono-pitch rafters.  Two rooms, visibly.

and a STAIR climbing the right-hand wall and disappearing through a real hole
in the parlour ceiling, because "two rooms" have to be somewhere.

WHY IT IS SHAPED LIKE THIS (the anti-box mandate, stated as geometry)
---------------------------------------------------------------------
The user's standing complaint about Dellhollow: *"all basically the same...
square rectangular boxes with a counter and maybe a table."*  Concretely, this
room breaks every one of the six things those six rooms share:

  1. ONE floor height          -> three here (parlour 0.00, snug -0.31, and the
                                  stair's own flight)
  2. FOUR axis-aligned walls   -> eleven wall segments including a projecting
                                  bay; built on `embint_lib.WallFrame`, which
                                  takes two points, not an axis
  3. a flat lid at ~3.0        -> boarded ceiling at 3.30 over the parlour, a
                                  2.05 stone soffit inside the nook, open
                                  rafters over the snug: three ceilings
  4. beams running ACROSS      -> beams run INTO the frame here and converge
  5. camera pitch ~24, fov 35  -> pitch 13, fov 40: eye height, not a survey.
                                  You are sitting in the parlour, not auditing
                                  it.
  6. a counter and a table     -> there is a counter, but the room's subject is
                                  a fire, and the counter is off-axis furniture

THE LIFE IN IT (a specific person's, on a specific night)
---------------------------------------------------------
Emberwake, an hour before the Kindling Hour.  The innkeep has gone up to the
square; the notice board out there reads *"...And a chair.  We are short of
chairs"* (chapter1.js), so the parlour's chairs are stacked on a hand-cart by
the door, half-loaded, waiting to be wheeled up.  The register lies open with
one new line in it after a long blank stretch.  The knitting is on the settle
with the needles still in it.  The stranger's satchel and map-tube lean where
she dropped them before going out to look at the flame.  Boots dry at the fire,
one fallen over.  Poppy's honeybuns sit under a cloth, because guests eat
first and that is LAW.

FORMAT: FF9 cutaway -- floor + back + both side walls, the near (front) wall
and the ceiling lid camera-invisible so they still bounce light.  ONE fixed
perspective camera.  SCALE: character 1.70, door 2.20, counter 1.05, table
0.75, seat 0.45.

Run headless (ALWAYS -b --python-exit-code 1):
    Blender -b --python-exit-code 1 -P tools/embint_inn_build.py -- \
        --out tools/blends/interiors/emb-inn-int.blend \
        --render docs/qa/interiors/emb-inn-int_v1.png --samples 224
"""
import bpy, math, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import embint_lib as L

CM = L.CM
OUTBLEND = "tools/blends/interiors/emb-inn-int.blend"
SEED = 20260801

# ============================================================== the plan ===
# Parlour x 0..10.2, y 0..7.1.  Camera stands front-RIGHT and looks north-west,
# so the HERO walls are the BACK (y=7.1) and the room's own depth; the right
# wall is the near-right repoussoir and carries the stair.
XL, XR = 0.00, 8.60
YF, YB = 0.00, 6.30
WH = 3.30                    # parlour wall height (to the plate)
CEIL = 3.30                  # underside of the guest-room floor
BEAM_Z = 3.14                # the beams that carry it, running INTO the frame
THICK = 0.24

# the inglenook: a stone bay projecting north out of the back wall
BX0, BX1 = 3.20, 5.30
BY1 = 7.75                   # fire wall
BAY_H = 2.05                 # the bressummer / nook soffit
FIRE_A, FIRE_B = 0.36, 1.74  # fire opening in the fire wall, measured in u
FIRE_TOP = 1.34

# back-wall openings, in world x
WIN_X0, WIN_X1 = 5.60, 6.30
DOOR_X0, DOOR_X1 = 6.60, 7.80
DOOR_TOP = 2.20

# the snug: one step down and west, through a post-and-beam opening
SX0, SY0, SY1 = -3.00, 3.60, 6.30
SNUG_Z = -0.31
SNUG_EAVE, SNUG_RIDGE = 2.45, 3.55

# reception, against the back wall
RC_X0, RC_X1 = 0.60, 2.55
RC_H = 1.05

# the stair, climbing the right wall northward.  The rise is set by HEADROOM,
# not by taste: the door pad stands south of the landing and the landing must
# clear a walking body, so 11 x 0.209 puts its underside at 2.27 m.
ST_Y0, ST_N, ST_RISE, ST_RUN = 1.00, 11, 0.209, 0.300
ST_W = 0.98
ST_TOP_Z = ST_N * ST_RISE            # 2.299
ST_Y1 = ST_Y0 + ST_N * ST_RUN        # 4.30

# the long table in the parlour
TX0, TX1, TY0, TY1, TH = 3.25, 6.15, 2.35, 3.55, 0.75


def deg(a):
    return math.radians(a)


# =============================================================== the shell ==

def build_floor():
    c = L.coll("SHELL")
    # PARLOUR.  Boards run east-west (dir_="x"), i.e. ACROSS the camera's line
    # of sight -- the opposite of the snug's, so the level change is legible
    # even in a grey render.  Three pale boards are replacements; that is what
    # a three-hundred-year-old parlour floor looks like.
    L.floor_planks("parl", (YF - 0.02, YB + 0.02), L.rects_yfn([(YF - 0.02, YB + 0.02,
                                                                XL - 0.02, XR + 0.02)]),
                   z=0.0, c=c, mat="mat_int_floor", mat_alt="mat_int_floor_pale",
                   alt=0.14, dir_="x")
    L.floor_void("floor_void_parl", XL, XR, YF, YB, 0.0, c=c)

    # SNUG: older, wider, darker boards running the other way, one step down.
    L.floor_planks("snug", (SX0 - 0.02, -0.30), L.rects_yfn([(SX0 - 0.02, -0.30,
                                                             SY0 - 0.02, SY1 + 0.02)]),
                   z=SNUG_Z, c=c, mat="mat_int_plank", mat_alt="mat_int_floor",
                   alt=0.22, dir_="y", w=(0.21, 0.30), run=(1.6, 3.0))
    L.floor_void("floor_void_snug", SX0, 0.0, SY0, SY1, SNUG_Z, c=c)
    # the step itself, walkable
    L.box("walk_step_snug_00", (-0.16, (SY0 + SY1) / 2 + 0.05, SNUG_Z / 2 - 0.020),
          (0.16, (SY1 - SY0) / 2 - 0.14, 0.038), "mat_int_wood", c, bevel=0.008,
          tex_off=L.toff())
    L.box("step_snug_riser", (0.02, (SY0 + SY1) / 2 + 0.05, SNUG_Z / 2 - 0.02),
          (0.028, (SY1 - SY0) / 2 - 0.14, abs(SNUG_Z) / 2), "mat_int_beam", c,
          bevel=0.004)
    # the threshold nosing on the parlour side: the thing a foot actually finds
    L.box("step_snug_nosing", (0.06, (SY0 + SY1) / 2 + 0.05, -0.026),
          (0.075, (SY1 - SY0) / 2 - 0.10, 0.026), "mat_int_wood", c, bevel=0.010,
          tex_off=L.toff())

    # HEARTHSTONE: the nook floor is one slab of stone, flush with the boards.
    L.prism("walk_floor_hearthstone",
            [(BX0 - 0.06, YB - 0.42), (BX1 + 0.06, YB - 0.42),
             (BX1 + 0.06, BY1 - 0.10), (BX0 - 0.06, BY1 - 0.10)],
            -0.055, 0.004, "mat_int_hearth", c, bevel=0.010)


def build_walls():
    c = "SHELL"
    made = {}
    # ---- BACK WALL, in two runs either side of the nook mouth -------------
    # u runs east->west from the right corner, so `u = XR - x`.
    fb = L.WallFrame((XR, YB), (XL, YB), inward=(0, 1))
    made["back"] = L.wall_run(
        "wBack", fb, WH, c=c, style="plaster", wain=1.02, thick=THICK,
        openings=[(XR - DOOR_X1, XR - DOOR_X0, DOOR_TOP),
                  (XR - WIN_X1, XR - WIN_X0, 2.05),
                  (XR - BX1, XR - BX0, BAY_H)])
    L.opening_frame("doorframe", fb, XR - DOOR_X1, XR - DOOR_X0, DOOR_TOP, c=c)
    L.opening_frame("winframe", fb, XR - WIN_X1, XR - WIN_X0, 2.05, c=c, sill=1.05)

    # ---- RIGHT WALL: the near repoussoir; the stair runs up it ------------
    fr = L.WallFrame((XR, YF), (XR, YB), inward=(1, 0))
    made["right"] = L.wall_run("wRight", fr, WH, c=c, style="plaster", wain=1.02,
                               thick=THICK)

    # ---- LEFT WALL: only the front half exists; north of y=4.2 the room
    #      opens into the snug, which is the whole point of the plan.
    fl = L.WallFrame((XL, SY0), (XL, YF), inward=(-1, 0))
    made["left"] = L.wall_run("wLeft", fl, WH, c=c, style="plaster", wain=1.02,
                              thick=THICK)

    # ---- THE INGLENOOK: three stone walls, low ----------------------------
    fe = L.WallFrame((BX1, YB - 0.10), (BX1, BY1), inward=(1, 0))
    L.wall_run("wNookE", fe, BAY_H, c=c, style="stone", thick=0.30, studs=False,
               plate=False)
    fw = L.WallFrame((BX0, BY1), (BX0, YB - 0.10), inward=(-1, 0))
    L.wall_run("wNookW", fw, BAY_H, c=c, style="stone", thick=0.30, studs=False,
               plate=False)
    ff = L.WallFrame((BX1, BY1), (BX0, BY1), inward=(0, 1))
    L.wall_run("wFire", ff, BAY_H, c=c, style="stone", thick=0.34, studs=False,
               plate=False, openings=[(FIRE_A, FIRE_B, FIRE_TOP)])
    made["fire_frame"] = ff

    # ---- THE SNUG: south wall, west wall, back wall ----------------------
    fs = L.WallFrame((SX0, SY0), (0.0, SY0), inward=(0, -1))
    L.wall_run("wSnugS", fs, SNUG_RIDGE, c=c, style="board", thick=0.20,
               plate_z=SNUG_RIDGE - 0.12, board_mat="mat_int_plank")
    fsw = L.WallFrame((SX0, SY1), (SX0, SY0), inward=(-1, 0))
    L.wall_run("wSnugW", fsw, SNUG_EAVE, c=c, style="board", thick=0.20,
               plate_z=SNUG_EAVE - 0.10, board_mat="mat_int_plank")
    fsb = L.WallFrame((0.0, SY1), (SX0, SY1), inward=(0, 1))
    # the kitchen doorway: a warm slot at the far end.  You never go in; the
    # light coming out of it is the reason the snug is not a dead end.
    L.wall_run("wSnugB", fsb, SNUG_RIDGE, c=c, style="board", thick=0.20,
               plate_z=SNUG_RIDGE - 0.12, board_mat="mat_int_plank",
               openings=[(1.05, 2.05, 2.05)])
    L.opening_frame("kitchframe", fsb, 1.05, 2.05, 2.05, c=c)
    made["kitchen_frame"] = fsb

    # ---- the camera-invisible near wall: it lights the room ---------------
    nw = L.box("shadow_nearwall", ((XL + XR) / 2, YF - THICK / 2 - 0.02, WH / 2),
               ((XR - XL) / 2 + THICK, THICK / 2, WH / 2), "mat_int_plaster",
               L.coll("SHELL"), bevel=0)
    L.hide_from_camera(nw)
    nw2 = L.box("shadow_nearwall_snug", ((SX0 + 0) / 2, SY0 - 0.30, 1.4),
                (abs(SX0) / 2, 0.10, 1.4), "mat_int_plaster", L.coll("SHELL"), bevel=0)
    L.hide_from_camera(nw2)
    return made


def build_ceiling():
    """Three ceilings, and the stairwell hole that proves there is an upstairs."""
    c = L.coll("SHELL")
    HOLE = (7.30, XR, 4.05, 5.35)          # the stairwell opening, in x/y

    def in_hole(x0, x1, y0, y1):
        return not (x1 < HOLE[0] or x0 > HOLE[1] or y1 < HOLE[2] or y0 > HOLE[3])

    # the lid: camera-invisible, but it is what stops the parlour reading as an
    # outdoor set with furniture in it.
    lid = L.box("shadow_ceiling", ((XL + XR) / 2, (YF + YB) / 2, CEIL + 0.16),
                ((XR - XL) / 2 + THICK, (YB - YF) / 2 + THICK, 0.08),
                "mat_int_plank", c, bevel=0)
    L.hide_from_camera(lid)
    # the roof void behind everything: see embint_lib.roof_backing for the
    # measurement that put it here
    L.roof_backing("roofvoid", SX0 - 0.4, XR + 0.4, YF - 0.4, BY1 + 0.4, 3.72, c=c)

    # boards, laid east-west, skipping the stairwell
    y = YF
    i = 0
    while y < YB - 1e-6:
        w = min(0.255, YB - y)
        x0, x1 = XL - 0.06, XR + 0.06
        segs = [(x0, x1)]
        if in_hole(x0, x1, y, y + w):
            segs = [(x0, HOLE[0])]
        for (a, b) in segs:
            if b - a < 0.05:
                continue
            ob = L.box("ceilboard_%02d" % i, ((a + b) / 2, y + w / 2, CEIL - 0.03),
                       ((b - a) / 2, w / 2 - 0.004, 0.028), "mat_int_beam", c,
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

    # BEAMS RUNNING INTO THE FRAME.  Dellhollow's interiors all run their beams
    # across the picture and every one of them notes in its own source that the
    # result is "a black bar across the frame".  Run them the other way and the
    # same timber becomes perspective: three lines converging on the back wall.
    for k, bx in enumerate((1.90, 4.55, 7.30)):
        n = 4
        for s in range(n):
            y0 = YF + (YB - YF) * s / n
            y1 = YF + (YB - YF) * (s + 1) / n
            if bx > HOLE[0] and y1 > HOLE[2]:
                continue
            ob = L.box("beam_%d_%d" % (k, s), (bx, (y0 + y1) / 2, BEAM_Z),
                       (0.105, (y1 - y0) / 2, 0.115), "mat_int_beam", c,
                       bevel=0.012, tex_off=L.toff())
            if (y0 + y1) / 2 < -0.20:
                L.hide_from_camera(ob)
    # joists riding on top, thin and high: they read as ceiling, not as bars
    yj, i = 0.30, 0
    while yj < YB - 0.05:
        segs = [(XL - 0.05, XR + 0.05)]
        if in_hole(XL, XR, yj - 0.04, yj + 0.04):
            segs = [(XL - 0.05, HOLE[0])]
        for (a, b) in segs:
            ob = L.box("joist_%02d" % i, ((a + b) / 2, yj, CEIL - 0.10),
                       ((b - a) / 2, 0.042, 0.070), "mat_int_beam", c, bevel=0.006,
                       tex_off=L.toff())
            if yj < -0.20:
                L.hide_from_camera(ob)
        yj += 0.36
        i += 1
    # trimmer round the stairwell -- the edge you would grab at the top
    L.box("stairwell_trim_s", ((HOLE[0] + HOLE[1]) / 2, HOLE[2], CEIL - 0.11),
          ((HOLE[1] - HOLE[0]) / 2, 0.075, 0.115), "mat_int_beam", c, bevel=0.010,
          tex_off=L.toff())
    L.box("stairwell_trim_w", (HOLE[0], (HOLE[2] + HOLE[3]) / 2, CEIL - 0.11),
          (0.075, (HOLE[3] - HOLE[2]) / 2, 0.115), "mat_int_beam", c, bevel=0.010,
          tex_off=L.toff())
    # the underside of the flight that continues above the hole: you see the
    # treads of the NEXT flight through the ceiling, which is the whole trick
    for k in range(5):
        L.box("upflight_%02d" % k, (7.95, HOLE[2] + 0.34 + k * 0.30,
                                    CEIL + 0.12 + k * 0.19),
              (0.80, 0.150, 0.030), "mat_int_plank", c, bevel=0.006, tex_off=L.toff())

    # THE NOOK'S OWN CEILING, at 2.05: stone soffit under the chimney
    L.box("nook_soffit", ((BX0 + BX1) / 2, (YB + BY1) / 2, BAY_H + 0.06),
          ((BX1 - BX0) / 2 + 0.20, (BY1 - YB) / 2 + 0.18, 0.06), "mat_int_soot", c,
          bevel=0)
    # the breast: the stone mass over the mouth, rising into the ceiling
    L.box("nook_breast", ((BX0 + BX1) / 2, YB + 0.16, (BAY_H + CEIL) / 2 + 0.02),
          ((BX1 - BX0) / 2 + 0.22, 0.22, (CEIL - BAY_H) / 2), "mat_int_stone", c,
          bevel=0.014, tex_off=L.toff())
    # and the bressummer across the mouth: the single heaviest timber in the room
    L.box("bressummer", ((BX0 + BX1) / 2, YB - 0.02, BAY_H - 0.075),
          ((BX1 - BX0) / 2 + 0.28, 0.135, 0.155), "mat_int_beam", c, bevel=0.016,
          tex_off=L.toff())

    # THE SNUG: no ceiling at all -- open to its own mono-pitch roof, so the
    # opening in the left wall shows a space that keeps going UP.  One glance
    # says "older building, added on to".
    L.rafters("snug", SY0 - 0.10, SY1 + 0.10, SX0 - 0.10, 0.10, SNUG_EAVE,
              SNUG_RIDGE, c=c, ridge_x=0.10, n=7, purlins=True)


def build_opening_snug():
    """The post-and-beam where a wall used to be.  A room that opens into
    another room needs a THRESHOLD or the two just smear together."""
    c = L.coll("SHELL")
    L.box("snugpost", (0.13, SY0 + 0.13, 1.62), (0.115, 0.115, 1.62), "mat_int_beam",
          c, bevel=0.012, tex_off=L.toff())
    L.box("snugpost_plinth", (0.13, SY0 + 0.13, 0.10), (0.145, 0.145, 0.10),
          "mat_int_paint_red", c, bevel=0.010)
    L.box("snugbeam", (0.10, (SY0 + SY1) / 2 + 0.10, 3.24 - 0.10),
          (0.115, (SY1 - SY0) / 2 + 0.10, 0.155), "mat_int_beam", c, bevel=0.014,
          tex_off=L.toff())
    # a brace from post to beam: the diagonal that says "carpentry"
    L.box("snugbrace", (0.13, SY0 + 0.60, 2.72), (0.075, 0.42, 0.075),
          "mat_int_beam", c, rot=(deg(42), 0, 0), bevel=0.008, tex_off=L.toff())


# ============================================================ the inglenook ==

def build_fire(fire_frame):
    c = L.coll("HEARTH")
    ff = fire_frame
    fx = (BX0 + BX1) / 2
    fy = BY1 - 0.16
    # firebox: sooted stone back and cheeks, set into the wall opening
    L.box("firebox_back", (fx, BY1 - 0.05, FIRE_TOP / 2), (0.70, 0.10, FIRE_TOP / 2),
          "mat_int_soot", c, bevel=0)
    for s in (-1, 1):
        L.box("firebox_cheek_%d" % (s > 0), (fx + s * 0.695, fy + 0.02, FIRE_TOP / 2),
              (0.055, 0.16, FIRE_TOP / 2), "mat_int_soot", c, bevel=0)
    L.box("firebox_lintel", (fx, fy + 0.02, FIRE_TOP + 0.055), (0.75, 0.17, 0.055),
          "mat_int_iron", c, bevel=0.008)
    # the fire itself: logs, embers, flame.  Banked for the evening, not roaring
    # -- the innkeep is up at the square and will be back.
    for k, (ox, oy, oz, rz) in enumerate(((-0.16, 0.02, 0.10, 0.22),
                                          (0.12, -0.05, 0.11, -0.35),
                                          (-0.02, 0.06, 0.22, 0.10))):
        L.cyl("firelog_%d" % k, (fx + ox, fy + oy, oz), 0.075, 0.62,
              "mat_int_charlog", c, axis="X", verts=10, rot=(0, 0, rz), bevel=0.006)
    L.prism("fire_embers", [(fx - 0.42, fy - 0.22), (fx + 0.42, fy - 0.22),
                            (fx + 0.42, fy + 0.20), (fx - 0.42, fy + 0.20)],
            0.005, 0.055, "mat_embers", c)
    for k, (ox, h, r) in enumerate(((-0.14, 0.34, 0.085), (0.05, 0.46, 0.10),
                                    (0.19, 0.28, 0.070))):
        L.lathe("flame_%d" % k, [(0.0, 0.0), (r, 0.06), (r * 0.72, h * 0.55),
                                 (0.0, h)],
                (fx + ox, fy + L.jit(0.05), 0.10), L.M("mat_fire"), c, segments=12)
    L.sphere("fire_ash", (fx, fy - 0.02, 0.03), 0.30, "mat_int_ash", c,
             scale=(1.5, 0.9, 0.14))
    # the crane and the kettle: the inn's supper, swung off the fire
    L.cyl("crane_post", (fx + 0.60, fy + 0.10, 0.62), 0.024, 1.20, "mat_int_iron", c,
          verts=10)
    L.cyl("crane_arm", (fx + 0.24, fy + 0.02, 1.16), 0.020, 0.74, "mat_int_iron", c,
          axis="X", verts=8)
    L.cyl("crane_chain", (fx - 0.06, fy + 0.0, 0.98), 0.010, 0.30, "mat_int_iron", c,
          verts=6)
    L.lathe("kettle", [(0.0, 0.0), (0.13, 0.03), (0.155, 0.13), (0.115, 0.24),
                       (0.075, 0.27), (0.075, 0.30)],
            (fx - 0.06, fy, 0.60), L.M("mat_int_iron"), c, segments=18, thickness=0.008)
    L.cyl("kettle_bail", (fx - 0.06, fy, 0.83), 0.008, 0.24, "mat_int_iron", c,
          axis="X", verts=6)

    # ---- the nook's furniture: a settle down each cheek -------------------
    # A SETTLE, not a screen.  v1 gave each one a 0.92 m slab back in pale
    # plank and, lit from the fire, the pair read as two lightboxes flanking
    # the flames -- the worst thing in that frame.  A real inglenook settle is
    # a low box seat with a SHORT panelled back and a solid arm at the open
    # end, in the same dark oak as everything else people sit on.
    for s, x in ((-1, BX0 + 0.30), (1, BX1 - 0.30)):
        tag = "settle_%s" % ("e" if s > 0 else "w")
        yc = (YB + BY1) / 2 - 0.19
        L.box(tag + "_seat", (x, yc, 0.435), (0.255, 0.46, 0.040), "mat_int_wood", c,
              bevel=0.012, tex_off=L.toff())
        L.box(tag + "_back", (x - s * 0.235, yc, 0.720), (0.032, 0.46, 0.285),
              "mat_int_beam", c, bevel=0.008, tex_off=L.toff())
        L.box(tag + "_caprail", (x - s * 0.235, yc, 1.017), (0.048, 0.475, 0.032),
              "mat_int_beam", c, bevel=0.010, tex_off=L.toff())
        L.box(tag + "_arm", (x, yc - 0.48, 0.635), (0.235, 0.042, 0.030),
              "mat_int_beam", c, bevel=0.010, tex_off=L.toff())
        L.cyl(tag + "_armpost", (x + s * 0.185, yc - 0.48, 0.535), 0.030, 0.20,
              "mat_int_wood", c, verts=8, bevel=0.004)
        L.box(tag + "_base", (x, yc, 0.205), (0.225, 0.45, 0.205),
              "mat_int_paint_red", c, bevel=0.008, tex_off=L.toff())
        L.box(tag + "_cushion", (x, yc + 0.05, 0.478), (0.215, 0.28, 0.035),
              "mat_int_felt", c, bevel=0.028)
    # the knitting, needles still in it, on the west settle -- the innkeep meant
    # to be back before now
    L.box("knitting", (BX0 + 0.36, YB + 0.22, 0.50), (0.15, 0.13, 0.045),
          "mat_int_felt", c, bevel=0.030)
    for k, a in enumerate((0.30, -0.22)):
        L.cyl("knit_needle_%d" % k, (BX0 + 0.36, YB + 0.22, 0.545), 0.007, 0.30,
              "mat_int_bowlwood", c, axis="X", verts=6, rot=(0, 0, a), bevel=0)
    L.sphere("wool_ball", (BX0 + 0.30, YB + 0.10, 0.075), 0.075, "mat_int_felt", c)
    # boots drying, one on its side: nobody arranges boots
    for k, (bx, by, rz, tip) in enumerate(((BX1 - 0.30, YB + 0.30, 0.30, 0.0),
                                           (BX1 - 0.52, YB + 0.22, -0.5, 1.45))):
        L.box("boot_%d" % k, (bx, by, 0.11 if tip == 0 else 0.075),
              (0.055, 0.115, 0.11), "mat_int_oilskin", c,
              rot=(tip, 0, rz), bevel=0.030)
        L.box("boot_%d_leg" % k, (bx, by - 0.02, 0.30 if tip == 0 else 0.075),
              (0.052, 0.052, 0.12), "mat_int_oilskin", c, rot=(tip, 0, rz),
              bevel=0.020)
    # firewood, stacked end-on in the east cheek
    for k in range(11):
        L.cyl("nook_log_%02d" % k, (BX1 - 0.16 + L.jit(0.02),
                                    BY1 - 0.34 + L.jit(0.03),
                                    0.075 + (k // 4) * 0.135),
              0.062, 0.36, "mat_int_bowlwood" if k % 3 else "mat_int_charlog", c,
              axis="X", verts=8, rot=(0, 0, L.jit(0.06)), bevel=0.004)


def build_mantel():
    """The nook has no mantel shelf -- it has a BRESSUMMER, and things get put
    on it anyway.  A row of objects at 1.94 is the room's reading line."""
    c = L.coll("HEARTH")
    z = BAY_H - 0.02
    L.box("mantel_shelf", ((BX0 + BX1) / 2, YB - 0.16, z), ((BX1 - BX0) / 2, 0.13,
                                                            0.030),
          "mat_int_wood", c, bevel=0.010, tex_off=L.toff())
    # a pair of candlesticks, one burned right down and never replaced
    for k, (ox, h) in enumerate(((-0.72, 0.20), (0.68, 0.035))):
        L.lathe("mantel_stick_%d" % k, [(0.0, 0.0), (0.045, 0.012), (0.018, 0.05),
                                        (0.022, 0.10), (0.030, 0.115)],
                ((BX0 + BX1) / 2 + ox, YB - 0.16, z + 0.03), L.M("mat_int_brass"), c,
                segments=14)
        L.cyl("mantel_candle_%d" % k, ((BX0 + BX1) / 2 + ox, YB - 0.16,
                                       z + 0.145 + h / 2),
              0.017, h, "mat_int_wax", c, verts=10, bevel=0.003)
    # the tinder box and a stub of chalk (the chairs tally, see the hand-cart)
    L.box("mantel_tinderbox", ((BX0 + BX1) / 2 - 0.28, YB - 0.18, z + 0.055),
          (0.085, 0.055, 0.055), "mat_int_iron", c, bevel=0.008)
    L.cyl("mantel_chalk", ((BX0 + BX1) / 2 + 0.14, YB - 0.13, z + 0.042), 0.011,
          0.055, "mat_int_crock", c, axis="X", verts=6, rot=(0, 0, 0.4), bevel=0)
    # a jug of something warm, lid off, put down and forgotten
    L.lathe("mantel_jug", [(0.0, 0.0), (0.055, 0.01), (0.070, 0.09), (0.045, 0.155),
                           (0.050, 0.175)],
            ((BX0 + BX1) / 2 + 0.32, YB - 0.17, z + 0.03), L.M("mat_int_crock_blue"),
            c, segments=16, thickness=0.005)


# =============================================================== reception ==

def build_reception():
    """Two hooks on the key board.  One key on it.  That is the entire
    characterisation of an inn that *"rarely has a stranger in it"*, and it is
    cheaper than any amount of dressing."""
    c = L.coll("PROPS")
    x0, x1 = RC_X0, RC_X1
    y0, y1 = YB - 0.72, YB - 0.06
    cx = (x0 + x1) / 2
    L.box("rc_top", (cx, (y0 + y1) / 2 - 0.03, RC_H - 0.035),
          ((x1 - x0) / 2 + 0.04, (y1 - y0) / 2 + 0.05, 0.035), "mat_int_wood", c,
          bevel=0.012, tex_off=L.toff())
    L.box("rc_front", (cx, y0 + 0.03, (RC_H - 0.08) / 2),
          ((x1 - x0) / 2, 0.032, (RC_H - 0.08) / 2), "mat_int_paint_green", c,
          bevel=0.008, tex_off=L.toff())
    for sx in (x0 + 0.055, cx, x1 - 0.055):
        L.box("rc_stile_%.2f" % sx, (sx, y0 + 0.012, (RC_H - 0.08) / 2),
              (0.062, 0.040, (RC_H - 0.08) / 2), "mat_int_paint_red", c, bevel=0.008)
    L.box("rc_shelf", (cx, (y0 + y1) / 2, 0.44), ((x1 - x0) / 2 - 0.05, 0.28, 0.018),
          "mat_int_plank", c, bevel=0.006, tex_off=L.toff())

    # the register on its slope desk, open, with ONE new line after a long gap
    L.box("reg_desk", (x0 + 0.62, y1 - 0.22, RC_H + 0.075), (0.30, 0.22, 0.075),
          "mat_int_wood", c, rot=(deg(-11), 0, 0), bevel=0.010, tex_off=L.toff())
    L.box("register", (x0 + 0.62, y1 - 0.245, RC_H + 0.165), (0.24, 0.175, 0.022),
          "mat_int_paper", c, rot=(deg(-11), 0, 0), bevel=0.004)
    L.box("register_spine", (x0 + 0.62, y1 - 0.245, RC_H + 0.152), (0.245, 0.180,
                                                                    0.014),
          "mat_int_oilskin", c, rot=(deg(-11), 0, 0), bevel=0.006)
    L.box("register_ribbon", (x0 + 0.70, y1 - 0.33, RC_H + 0.186), (0.012, 0.10,
                                                                    0.002),
          "mat_int_paint_red", c, rot=(deg(-11), 0, 0), bevel=0)
    L.lathe("inkwell", [(0.0, 0.0), (0.032, 0.005), (0.036, 0.045), (0.022, 0.058),
                        (0.026, 0.065)],
            (x0 + 1.02, y1 - 0.20, RC_H), L.M("mat_int_glassjug"), c, segments=14)
    L.cyl("pen", (x0 + 1.14, y1 - 0.30, RC_H + 0.03), 0.006, 0.20, "mat_int_bowlwood",
          c, axis="X", verts=6, rot=(0, deg(16), deg(28)), bevel=0)
    # the little brass bell nobody has had to ring in months
    L.lathe("desk_bell", [(0.0, 0.075), (0.055, 0.055), (0.062, 0.0)],
            (x1 - 0.28, y1 - 0.26, RC_H), L.M("mat_int_brass"), c, segments=16,
            thickness=0.004)
    L.sphere("desk_bell_knob", (x1 - 0.28, y1 - 0.26, RC_H + 0.092), 0.016,
             "mat_int_brass", c)

    # THE KEY BOARD.  Two hooks.  One key.
    bx = cx + 0.10
    L.box("keyboard", (bx, YB - 0.135, 1.80), (0.44, 0.030, 0.34),
          "mat_int_paint_green", c, bevel=0.008, tex_off=L.toff())
    L.box("keyboard_frame", (bx, YB - 0.125, 1.80), (0.485, 0.022, 0.385),
          "mat_int_paint_red", c, bevel=0.010)
    for k, ox in enumerate((-0.20, 0.20)):
        L.cyl("key_hook_%d" % k, (bx + ox, YB - 0.185, 1.88), 0.010, 0.085,
              "mat_int_brass", c, axis="Y", verts=8, bevel=0)
    # ROOM ONE's key hangs.  ROOM TWO's hook is bare: the stranger has it.
    L.cyl("key_1_ring", (bx - 0.20, YB - 0.215, 1.815), 0.038, 0.009,
          "mat_int_brass", c, axis="Y", verts=14, bevel=0)
    L.box("key_1_shank", (bx - 0.20, YB - 0.215, 1.715), (0.008, 0.008, 0.062),
          "mat_int_brass", c, bevel=0)
    L.box("key_1_bit", (bx - 0.172, YB - 0.215, 1.665), (0.030, 0.008, 0.022),
          "mat_int_brass", c, bevel=0)
    # a numbered tag on each hook so the empty one is legibly a MISSING key
    for k, ox in enumerate((-0.20, 0.20)):
        L.box("key_tag_%d" % k, (bx + ox, YB - 0.152, 2.02), (0.042, 0.004, 0.046),
              "mat_int_paper", c, bevel=0.004)


# =================================================================== stair ==

def build_stair():
    """It climbs the near-right wall and goes through the ceiling.  A stair is
    the cheapest possible statement that a building has an upstairs, and its
    soffit is the one long diagonal in a room otherwise made of horizontals."""
    c = L.coll("SHELL")
    x_in = XR - THICK / 2 - 0.02                 # inner face of the right wall
    for k in range(ST_N):
        y = ST_Y0 + ST_RUN * (k + 0.5)
        z = ST_RISE * (k + 1)
        L.box("stair_tread_%02d" % k, (x_in - ST_W / 2, y, z - 0.028),
              (ST_W / 2, ST_RUN / 2 + 0.022, 0.028), "mat_int_plank", c,
              bevel=0.008, tex_off=L.toff())
        L.box("stair_riser_%02d" % k, (x_in - ST_W / 2, y - ST_RUN / 2 - 0.014,
                                       z - ST_RISE / 2 - 0.03),
              (ST_W / 2 - 0.012, 0.020, ST_RISE / 2 - 0.02), "mat_int_plank", c,
              bevel=0.004)
    # landing at the top, then out through the ceiling
    L.box("stair_landing", (x_in - ST_W / 2, ST_Y1 + 0.44, ST_TOP_Z - 0.028),
          (ST_W / 2, 0.44, 0.028), "mat_int_plank", c, bevel=0.008, tex_off=L.toff())
    # the raking string, and the soffit under it: THE diagonal
    ang = math.atan2(ST_RISE, ST_RUN)
    Ls = math.hypot(ST_N * ST_RUN, ST_N * ST_RISE)
    L.box("stair_string", (x_in - ST_W - 0.055, ST_Y0 + ST_N * ST_RUN / 2,
                           ST_TOP_Z / 2 - 0.06),
          (0.055, Ls / 2, 0.170), "mat_int_beam", c, rot=(-ang, 0, 0), bevel=0.010,
          tex_off=L.toff())
    nx = x_in - ST_W - 0.055                     # the outboard (string) line
    L.box("stair_soffit", (x_in - ST_W / 2, ST_Y0 + ST_N * ST_RUN / 2,
                           ST_TOP_Z / 2 - 0.14),
          (ST_W / 2, Ls / 2, 0.028), "mat_int_plaster", c, rot=(-ang, 0, 0), bevel=0)
    # newel + turned balusters + handrail
    L.box("stair_newel", (nx, ST_Y0 - 0.06, 0.58), (0.075, 0.075, 0.58),
          "mat_int_wood", c, bevel=0.010, tex_off=L.toff())
    L.lathe("stair_newel_cap", [(0.0, 0.10), (0.062, 0.055), (0.085, 0.0)],
            (nx, ST_Y0 - 0.06, 1.16), L.M("mat_int_wood"), c, segments=14)
    for k in range(ST_N):
        y = ST_Y0 + ST_RUN * (k + 0.5)
        z = ST_RISE * (k + 1)
        L.lathe("baluster_%02d" % k,
                [(0.0, 0.0), (0.038, 0.02), (0.026, 0.16), (0.042, 0.28),
                 (0.024, 0.42), (0.030, 0.74), (0.030, 0.80)],
                (nx, y, z), L.M("mat_int_wood"), c, segments=10)
    L.box("stair_handrail", (nx, ST_Y0 + ST_N * ST_RUN / 2, ST_TOP_Z / 2 + 0.82),
          (0.055, Ls / 2, 0.048), "mat_int_wood", c, rot=(-ang, 0, 0), bevel=0.014,
          tex_off=L.toff())

    # THE SPANDREL: the stair is boxed in underneath, which is what every real
    # inn does with that wedge of space -- and it is also the fix the walk gate
    # asked for.  Left open, the floor under the flight is reachable with 1.72 m
    # of headroom at one end and 0.21 m at the other; boxed in, the low wedge is
    # simply not floor, and the parlour gets a cupboard door instead of a trap.
    for k in range(ST_N + 2):
        y = ST_Y0 + 0.15 + k * 0.30
        h = max(0.30, ST_RISE * ((y - ST_Y0) / ST_RUN) - 0.14)
        L.box("stair_spandrel_%02d" % k, (nx - 0.045, y, h / 2), (0.035, 0.155, h / 2),
              "mat_int_plaster", c, bevel=0.004, tex_off=L.toff())
    # the cupboard door in it: two planks, a strap hinge and a wooden turn-button
    L.box("understair_door", (nx - 0.085, ST_Y0 + 0.95, 0.62), (0.030, 0.40, 0.62),
          "mat_int_paint_green", c, bevel=0.008, tex_off=L.toff())
    L.box("understair_door_batten", (nx - 0.115, ST_Y0 + 0.95, 0.95),
          (0.014, 0.40, 0.055), "mat_int_beam", c, bevel=0.006)
    L.cyl("understair_turn", (nx - 0.125, ST_Y0 + 0.58, 0.72), 0.022, 0.11,
          "mat_int_wood", c, axis="X", verts=8, bevel=0.004)

    # what the inn keeps AGAINST the spandrel, out in the parlour where you can
    # trip over it, because that is where things actually end up
    p = L.coll("PROPS")
    L.box("understair_chest", (nx - 0.44, ST_Y0 + 2.05, 0.24), (0.32, 0.42, 0.24),
          "mat_int_plank", p, rot=(0, 0, deg(-6)), bevel=0.012, tex_off=L.toff())
    L.box("understair_chest_lid", (nx - 0.44, ST_Y0 + 2.05, 0.495),
          (0.33, 0.43, 0.035), "mat_int_oilskin", p, rot=(0, 0, deg(-6)), bevel=0.010)
    for k, (dy, h) in enumerate(((0.30, 0.42), (0.62, 0.30), (0.95, 0.36))):
        L.cyl("understair_broom_%d" % k, (nx - 0.26, ST_Y0 + 2.95 + dy * 0.2,
                                          0.62 + h * 0.1),
              0.020, 1.24, "mat_int_bowlwood", p, verts=8,
              rot=(deg(9 + k * 3), 0, deg(k * 22)), bevel=0)
    # the peg rail on the wall over the chest: coats, and one empty peg
    fr = L.WallFrame((XR, YF), (XR, YB), inward=(1, 0))
    fr.box("stairpegrail", ST_Y0 + 0.60, -0.045, 1.62, 1.30, 0.045, 0.075,
           L.M("mat_int_paint_red"), p, bevel=0.008)
    for k, u in enumerate((ST_Y0 + 0.16, ST_Y0 + 0.56, ST_Y0 + 0.96)):
        fr.cyl("stairpeg_%d" % k, u, -0.12, 1.66, 0.020, 0.17, L.M("mat_int_wood"), p,
               axis="V", verts=8)


# ================================================= door, window, the outside ==

def build_door():
    """The exit reads: seam canon applies indoors.  It is a 1.20 x 2.20 opening
    in the back wall, standing OPEN on a dusk-lit street, with the square's own
    lamp visible past the jamb -- so the player never has to hunt for the way
    out, and the room is connected to the night the chapter happens on."""
    c = L.coll("SHELL")
    fb = L.WallFrame((XR, YB), (XL, YB), inward=(0, 1))
    a, b = XR - DOOR_X1, XR - DOOR_X0
    # the leaf, hung open into the room
    hinge = (DOOR_X0 + 0.03, YB + 0.10)
    ang = deg(78)                        # standing open in the street
    dxy = (math.cos(ang), math.sin(ang))
    lc = (hinge[0] + dxy[0] * 0.55, hinge[1] + dxy[1] * 0.55)
    L.box("door_leaf", (lc[0], lc[1], 1.07), (0.55, 0.026, 1.07), "mat_int_plank", c,
          rot=(0, 0, ang), bevel=0.008, tex_off=L.toff())
    for k in range(3):
        L.box("door_batten_%d" % k,
              (lc[0] - dxy[1] * 0.035, lc[1] + dxy[0] * 0.035, 0.38 + k * 0.68),
              (0.55, 0.020, 0.055), "mat_int_beam", c, rot=(0, 0, ang), bevel=0.006)
    L.cyl("door_handle", (lc[0] + dxy[0] * 0.42 - dxy[1] * 0.05,
                          lc[1] + dxy[1] * 0.42 + dxy[0] * 0.05, 1.02),
          0.016, 0.16, "mat_int_iron", c, axis="X", verts=8, rot=(0, 0, ang + deg(90)),
          bevel=0)
    # threshold + the doormat that has taken thirty years of boots
    fb.box("door_threshold", (a + b) / 2, 0.04, 0.018, b - a + 0.10, 0.34, 0.036,
           L.M("mat_int_stone"), c, bevel=0.008)
    fb.box("door_mat", (a + b) / 2, -0.28, 0.014, b - a - 0.10, 0.42, 0.028,
           L.M("mat_int_rug_border"), c, bevel=0.006)
    # what you see through it: the street, a lamppost, a neighbour's roofline.
    # A matte, not geometry -- the town is another lane's blend.
    L.dusk_card("dusk_backdrop", ((DOOR_X0 + DOOR_X1) / 2 - 0.40, YB + 2.90, 1.50),
                (2.60, 0.05, 1.70), c="SHELL",
                top=(0.062, 0.086, 0.148), bottom=(0.011, 0.016, 0.028),
                strength=1.0)
    L.box("dusk_roofline", ((DOOR_X0 + DOOR_X1) / 2 - 0.95, YB + 2.55, 2.42),
          (1.05, 0.04, 0.58), "mat_int_soot", c, rot=(0, deg(13), 0), bevel=0)
    L.cyl("dusk_lamppost", (DOOR_X0 + 0.18, YB + 1.70, 1.20), 0.042, 2.40,
          "mat_int_iron", c, verts=8, bevel=0.004)
    L.box("dusk_lamphead", (DOOR_X0 + 0.18, YB + 1.70, 2.50), (0.095, 0.095, 0.145),
          "mat_int_lampglass", c, bevel=0.010)
    L.box("dusk_ground", ((DOOR_X0 + DOOR_X1) / 2, YB + 1.60, -0.03),
          (2.60, 1.62, 0.03), "mat_int_stone", c, bevel=0)


def build_window():
    c = L.coll("SHELL")
    fb = L.WallFrame((XR, YB), (XL, YB), inward=(0, 1))
    a, b = XR - WIN_X1, XR - WIN_X0
    fb.box("win_glass", (a + b) / 2, 0.10, 1.55, b - a - 0.06, 0.014, 0.94,
           L.M("mat_glass_dusk"), c, bevel=0)
    for k in range(3):
        fb.box("win_mullion_%d" % k, a + (b - a) * (k + 1) / 4.0, 0.06, 1.55,
               0.032, 0.055, 0.94, L.M("mat_int_paint_green"), c, bevel=0.004)
    fb.box("win_transom", (a + b) / 2, 0.06, 1.55, b - a - 0.02, 0.055, 0.032,
           L.M("mat_int_paint_green"), c, bevel=0.004)
    # the sill: where a jug of cut branches has been standing long enough to
    # leave a ring
    fb.box("win_sill_in", (a + b) / 2, -0.13, 1.04, b - a + 0.22, 0.24, 0.045,
           L.M("mat_int_wood"), c, bevel=0.010)
    # what stands on the sill is a stub of candle in a dish and a folded cloth:
    # small, warm, and not competing with the fire for the eye
    L.lathe("sill_dish", [(0.0, 0.0), (0.075, 0.008), (0.082, 0.026), (0.072, 0.030)],
            (WIN_X0 + 0.22, YB - 0.17, 1.085), L.M("mat_int_crock"), L.coll("PROPS"),
            segments=16, thickness=0.004)
    L.cyl("sill_candle", (WIN_X0 + 0.22, YB - 0.17, 1.155), 0.017, 0.11,
          "mat_int_wax", L.coll("PROPS"), verts=10, bevel=0.003)
    L.box("sill_cloth", (WIN_X1 - 0.22, YB - 0.16, 1.098), (0.115, 0.075, 0.020),
          "mat_int_linen", L.coll("PROPS"), rot=(0, 0, deg(11)), bevel=0.014)


# ============================================================== the parlour ==

def build_table_and_life(kit):
    """The room on THIS night: chairs going up to the square, a stranger's kit
    dropped by the fire, and Poppy's honeybuns under a cloth."""
    c = L.coll("PROPS")
    cx, cy = (TX0 + TX1) / 2, (TY0 + TY1) / 2
    L.box("table_top", (cx, cy, TH - 0.030), ((TX1 - TX0) / 2, (TY1 - TY0) / 2, 0.030),
          "mat_int_wood", c, bevel=0.012, tex_off=L.toff())
    L.box("table_rail_n", (cx, TY1 - 0.10, TH - 0.115), ((TX1 - TX0) / 2 - 0.12, 0.045,
                                                         0.055),
          "mat_int_beam", c, bevel=0.006, tex_off=L.toff())
    L.box("table_rail_s", (cx, TY0 + 0.10, TH - 0.115), ((TX1 - TX0) / 2 - 0.12, 0.045,
                                                         0.055),
          "mat_int_beam", c, bevel=0.006, tex_off=L.toff())
    for (lx, ly) in ((TX0 + 0.16, TY0 + 0.16), (TX1 - 0.16, TY0 + 0.16),
                     (TX0 + 0.16, TY1 - 0.16), (TX1 - 0.16, TY1 - 0.16)):
        L.lathe("table_leg_%.2f_%.2f" % (lx, ly),
                [(0.0, 0.0), (0.055, 0.02), (0.045, 0.20), (0.062, 0.34),
                 (0.040, 0.52), (0.048, TH - 0.06), (0.052, TH - 0.06)],
                (lx, ly, 0.0), L.M("mat_int_wood"), c, segments=12)

    # THE HAND-CART OF CHAIRS.  The notice board in the square says the village
    # is short of chairs; this is where they went.  Half-loaded, because the
    # innkeep is coming back for the rest.
    ccx, ccy = 1.95, 2.15
    for k in range(4):
        _chair("stack_chair_%d" % k, ccx + L.jit(0.035), ccy + L.jit(0.035),
               k * 0.115, deg(28) + L.jit(0.13), c)
    # the rope that will lash them into the cart, coiled on the top seat
    L.lathe("stack_rope", [(0.055, 0.0), (0.085, 0.012), (0.085, 0.030),
                           (0.055, 0.042)],
            (ccx + 0.02, ccy + 0.03, 0.945), L.M("mat_int_bowlwood"), c, segments=18)
    # a lantern set down on the floor beside them, still lit: somebody is
    # coming back for the second load
    L.place_kit(kit["kit_lantern_hanging"], "lantern_floor", (ccx + 0.62,
                                                              ccy - 0.42, 0.20),
                c="PROPS")
    _chair("chair_floor", 3.55, 0.95, 0.0, deg(52), c)
    _chair("chair_fire", 2.85, 5.10, 0.0, deg(-118), c)     # pulled up to the nook
    # two stools left behind, because nobody carts stools
    for k, (sx, sy) in enumerate(((1.20, 2.60), (5.55, 4.35))):
        L.lathe("stool_%d" % k, [(0.0, 0.0), (0.17, 0.0), (0.17, 0.03), (0.0, 0.03)],
                (sx, sy, 0.45), L.M("mat_int_wood"), c, segments=14)
        for j in range(3):
            aa = deg(120 * j + 25)
            L.cyl("stool_%d_leg_%d" % (k, j), (sx + 0.11 * math.cos(aa),
                                               sy + 0.11 * math.sin(aa), 0.225),
                  0.019, 0.46, "mat_int_wood", c, verts=8,
                  rot=(deg(7) * math.sin(aa), -deg(7) * math.cos(aa), 0), bevel=0.004)

    # THE STRANGER'S KIT, dropped by the settle: satchel, map tube, wet cloak.
    # Vesper walked in an hour ago and went straight back out to the square.
    L.box("satchel", (BX0 + 0.34, YB + 0.30, 0.17), (0.19, 0.13, 0.17),
          "mat_int_oilskin", c, rot=(deg(6), 0, deg(28)), bevel=0.045)
    L.box("satchel_flap", (BX0 + 0.34, YB + 0.20, 0.28), (0.19, 0.045, 0.11),
          "mat_int_oilskin", c, rot=(deg(-16), 0, deg(28)), bevel=0.030)
    L.cyl("satchel_strap", (BX0 + 0.34, YB + 0.30, 0.30), 0.016, 0.42,
          "mat_int_oilskin", c, axis="X", verts=8, rot=(0, deg(62), deg(28)),
          bevel=0)
    L.cyl("maptube", (BX0 + 0.14, YB + 0.10, 0.34), 0.055, 0.72, "mat_int_bowlwood",
          c, verts=14, rot=(deg(74), 0, deg(-18)), bevel=0.008)
    L.cyl("maptube_cap", (BX0 + 0.14 + 0.33 * math.sin(deg(-18)) * math.sin(deg(74)),
                          YB + 0.10 - 0.33 * math.cos(deg(-18)) * math.sin(deg(74)),
                          0.34 + 0.33 * math.cos(deg(74))),
          0.060, 0.075, "mat_int_brass", c, verts=14, rot=(deg(74), 0, deg(-18)),
          bevel=0.006)

    # POPPY'S HONEYBUNS, under a cloth on the table.  Guests eat first: LAW.
    for k, (ox, oy) in enumerate(((-0.10, 0.0), (0.10, 0.03), (0.0, -0.14),
                                  (0.19, -0.10), (-0.19, -0.09))):
        L.sphere("honeybun_%d" % k, (cx - 0.95 + ox, cy + 0.18 + oy, TH + 0.045),
                 0.062, "mat_int_bread", c, scale=(1.0, 1.0, 0.68))
    L.lathe("bun_plate", [(0.0, 0.0), (0.24, 0.006), (0.255, 0.030), (0.24, 0.034)],
            (cx - 0.95, cy + 0.18, TH), L.M("mat_int_crock"), c, segments=20,
            thickness=0.004)
    cl = L.box("bun_cloth", (cx - 0.95, cy + 0.14, TH + 0.10), (0.30, 0.30, 0.014),
               "mat_int_linen", c, rot=(deg(4), deg(-3), deg(12)), bevel=0.020)
    L.displace(cl, 0.028, 0.22, levels=3, seed_=7)
    # supper things at the far end: one place laid, because one guest
    L.lathe("bowl_1", [(0.0, 0.0), (0.10, 0.045), (0.115, 0.075), (0.10, 0.078)],
            (cx + 1.02, cy + 0.10, TH), L.M("mat_int_crock_blue"), c, segments=18,
            thickness=0.005)
    L.lathe("cup_1", [(0.0, 0.0), (0.043, 0.004), (0.046, 0.085), (0.040, 0.088)],
            (cx + 1.32, cy - 0.14, TH), L.M("mat_int_crock"), c, segments=16,
            thickness=0.004)
    L.box("spoon_1", (cx + 1.16, cy - 0.02, TH + 0.008), (0.075, 0.012, 0.006),
          "mat_int_bowlwood", c, rot=(0, 0, deg(24)), bevel=0.004)
    # a stack of bowls waiting for a crowd that is up at the square, and the
    # big jug beside them: the table of an inn that is expecting people back
    for k in range(4):
        L.lathe("bowl_stack_%d" % k, [(0.0, 0.0), (0.105, 0.040), (0.118, 0.062),
                                      (0.106, 0.066)],
                (cx - 0.34, cy - 0.30, TH + k * 0.034),
                L.M("mat_int_crock" if k % 2 else "mat_int_crock_blue"), c,
                segments=18, thickness=0.005)
    L.lathe("table_jug", [(0.0, 0.0), (0.075, 0.014), (0.098, 0.115), (0.058, 0.245),
                          (0.064, 0.275)],
            (cx + 0.62, cy - 0.34, TH), L.M("mat_int_crock"), c, segments=18,
            thickness=0.006)
    L.cyl("table_jug_handle", (cx + 0.70, cy - 0.34, TH + 0.185), 0.010, 0.14,
          "mat_int_crock", c, verts=8, rot=(0, deg(28), 0), bevel=0)
    # somebody's tally of who has taken a chair, chalked on a slate
    L.box("chair_slate", (cx - 0.70, cy - 0.42, TH + 0.012), (0.16, 0.115, 0.012),
          "mat_int_soot", c, rot=(0, 0, deg(-13)), bevel=0.006)
    # the candle that is actually lit, and a spill jar of tapers
    L.lathe("table_stick", [(0.0, 0.0), (0.055, 0.010), (0.020, 0.045),
                            (0.026, 0.10), (0.034, 0.115)],
            (cx + 0.30, cy + 0.22, TH), L.M("mat_int_brass"), c, segments=14)
    L.cyl("table_candle", (cx + 0.30, cy + 0.22, TH + 0.245), 0.017, 0.26,
          "mat_int_wax", c, verts=10, bevel=0.003)
    L.lathe("table_flame", [(0.0, 0.0), (0.014, 0.012), (0.008, 0.045), (0.0, 0.062)],
            (cx + 0.30, cy + 0.22, TH + 0.375), L.M("mat_int_flame_small"), c,
            segments=8)

    # THE RUG: the room's one pop of saturated colour, and the mark on the floor
    # that says "this is where people sit".  Laid crooked, because it always is.
    rug = L.box("rug", (4.25, 5.20, 0.008), (1.30, 0.72, 0.008), "mat_int_rug", c,
                rot=(0, 0, deg(-7)), bevel=0.006)
    L.displace(rug, 0.010, 0.40, levels=3, seed_=3)
    L.box("rug_border", (4.25, 5.20, 0.006), (1.39, 0.81, 0.006), "mat_int_rug_border",
          c, rot=(0, 0, deg(-7)), bevel=0.006)

    # a bench along the near side of the table, so its near edge is not one bare
    # plank silhouette across the bottom of the frame
    L.box("table_bench", ((TX0 + TX1) / 2 - 0.12, TY0 - 0.42, 0.435),
          ((TX1 - TX0) / 2 - 0.22, 0.155, 0.032), "mat_int_wood", c, bevel=0.010,
          tex_off=L.toff())
    for lx in ((TX0 + TX1) / 2 - 1.12, (TX0 + TX1) / 2 + 0.86):
        L.box("table_bench_leg_%.2f" % lx, (lx, TY0 - 0.42, 0.205),
              (0.032, 0.135, 0.205), "mat_int_wood", c, bevel=0.008, tex_off=L.toff())

    # kit props: a barrel of small beer by the reception, a crate of Emberwake
    # bunting half-unpacked in the snug, and a rope coil under the stair
    L.place_kit(kit["kit_barrel"], "barrel_beer", (RC_X1 + 0.32, YB - 1.05, 0.0),
                rot=(0, 0, deg(20)), c="PROPS")
    L.place_kit(kit["kit_crate"], "crate_bunting", (-2.55, 6.02, SNUG_Z + 0.375),
                rot=(0, 0, deg(-14)), c="PROPS")
    L.place_kit(kit["kit_rope_coil"], "rope_understair", (XR - 1.62, ST_Y0 + 3.35,
                                                          0.0), c="PROPS")
    L.place_kit(kit["kit_bucket"], "bucket_hearth", (BX1 + 0.02, YB - 0.60, 0.0),
                rot=(0, 0, deg(-30)), c="PROPS")


def _chair(name, x, y, z, rz, c, flat=False):
    """A ladder-back chair.  `flat` lays it on its side on the cart."""
    tilt = deg(90) if flat else 0.0
    L.box(name + "_seat", (x, y, z + (0.03 if flat else 0.45)),
          (0.21, 0.21, 0.022), "mat_int_wood", c, rot=(tilt, 0, rz), bevel=0.008,
          tex_off=L.toff())
    for k in range(3):
        L.box(name + "_slat_%d" % k,
              (x - (0.19 if flat else 0.0) * math.cos(rz),
               y - (0.19 if flat else 0.0) * math.sin(rz),
               z + (0.20 + k * 0.10 if flat else 0.62 + k * 0.14)),
              (0.19, 0.018, 0.035), "mat_int_wood", c, rot=(tilt, 0, rz),
              bevel=0.006, tex_off=L.toff())
    if not flat:
        for (sx, sy) in ((-0.185, -0.185), (0.185, -0.185), (-0.185, 0.185),
                         (0.185, 0.185)):
            px = x + sx * math.cos(rz) - sy * math.sin(rz)
            py = y + sx * math.sin(rz) + sy * math.cos(rz)
            back = sy > 0
            L.cyl(name + "_leg_%.2f_%.2f" % (sx, sy), (px, py,
                                                       (0.90 if back else 0.225)),
                  0.019, (1.80 if back else 0.45), "mat_int_wood", c, verts=8,
                  bevel=0.004)


def build_snug(kit):
    """The second room.  One lamp, one long table, the festival being packed."""
    c = L.coll("PROPS")
    z = SNUG_Z
    tx, ty = -1.72, 5.45
    L.box("snugtable_top", (tx, ty, z + 0.75 - 0.028), (0.55, 0.66, 0.028),
          "mat_int_plank", c, bevel=0.010, tex_off=L.toff())
    for (lx, ly) in ((tx - 0.44, ty - 0.54), (tx + 0.44, ty - 0.54),
                     (tx - 0.44, ty + 0.54), (tx + 0.44, ty + 0.54)):
        L.box("snugtable_leg_%.2f_%.2f" % (lx, ly), (lx, ly, z + 0.36),
              (0.045, 0.045, 0.36), "mat_int_wood", c, bevel=0.006, tex_off=L.toff())
    # bunting spilling out of the crate and over the table: Emberwake is tonight
    for k in range(9):
        L.box("bunting_%02d" % k, (tx - 0.38 + k * 0.095, ty + 0.36 + L.jit(0.05),
                                   z + 0.78 + L.jit(0.015)),
              (0.045, 0.055, 0.006),
              "mat_int_paint_red" if k % 3 == 0 else
              ("mat_int_paint_green" if k % 3 == 1 else "mat_int_linen"), c,
              rot=(0, 0, L.jit(0.5)), bevel=0.004)
    # a bench, and the innkeep's ledger of who lent what to the festival
    # the bench goes on the table's WEST side, out of the through-route from
    # the parlour: a room you cannot cross is not a second room, it is scenery
    L.box("snugbench", (tx - 0.86, ty, z + 0.42), (0.16, 0.62, 0.030),
          "mat_int_wood", c, bevel=0.008, tex_off=L.toff())
    for ly in (ty - 0.48, ty + 0.48):
        L.box("snugbench_leg_%.2f" % ly, (tx - 0.86, ly, z + 0.20),
              (0.14, 0.030, 0.20), "mat_int_wood", c, bevel=0.006)
    L.box("snug_ledger", (tx + 0.26, ty - 0.28, z + 0.765), (0.13, 0.17, 0.020),
          "mat_int_paper", c, rot=(0, 0, deg(9)), bevel=0.004)
    # the shelf of tankards nobody has needed all year
    L.box("snugshelf", (SX0 + 0.20, ty + 0.10, z + 1.72), (0.15, 0.85, 0.028),
          "mat_int_plank", c, bevel=0.006, tex_off=L.toff())
    for k in range(6):
        L.lathe("tankard_%d" % k, [(0.0, 0.0), (0.048, 0.005), (0.052, 0.115),
                                   (0.046, 0.120)],
                (SX0 + 0.20, ty - 0.62 + k * 0.26, z + 1.748),
                L.M("mat_int_crock" if k % 2 else "mat_int_copper"), c, segments=14,
                thickness=0.004)


# ================================================================== lights ==

def build_lights(kit):
    fx, fy = (BX0 + BX1) / 2, BY1 - 0.20
    # a narrower mouth throw: at 178 the fire washed its own stone cheeks and
    # the two settle backs white before any of it reached the floor
    L.hearth_rig("fire", fx, fy, 0.02, (0, -1), energy=1.05, mouth_spread=124)
    # the nook is a stone box: without a bounce off its own cheeks the settles
    # go black two feet from the fire
    b = L.light("LGT_nook_bounce", "AREA", (fx, YB + 0.55, 1.35), 46.0,
                (1.0, 0.55, 0.26), shape="RECTANGLE", sx=1.9, sy=1.3, spread=160)
    L.aim(b, (fx, YB - 2.2, 0.9))

    # two hanging lanterns, ordinary flame.  The HIERARCHY is deliberate: the
    # fire is the brightest thing in the room, the reception lantern second,
    # the table third, the snug fourth.  A room where everything is equally lit
    # has no subject.
    L.hang_lantern(kit, "lantern_reception", RC_X0 + 1.00, YB - 0.95, 2.06,
                   hang_from=BEAM_Z - 0.12, energy=158.0)
    L.hang_lantern(kit, "lantern_table", (TX0 + TX1) / 2 - 0.30, (TY0 + TY1) / 2 + 0.10,
                   2.10, hang_from=BEAM_Z - 0.12, energy=92.0)
    L.light("LGT_table_candle", "POINT",
            ((TX0 + TX1) / 2 + 0.30, (TY0 + TY1) / 2 + 0.22, TH + 0.40), 9.0,
            (1.0, 0.63, 0.25), 0.035)

    # the snug: one bracket lamp, deliberately dimmer, so distance reads as
    # distance and the eye goes to the fire first
    L.place_kit(kit["kit_lantern_hanging"], "lantern_snug", (SX0 + 0.36, 4.55,
                                                             SNUG_Z + 2.06),
                c="PROPS")
    L.light("LGT_snug", "POINT", (SX0 + 0.40, 4.55, SNUG_Z + 2.10), 54.0,
            (1.0, 0.60, 0.27), 0.09)
    # the kitchen doorway: a warm slot at the end of the snug
    k = L.light("LGT_kitchen", "AREA", (-1.45, SY1 - 0.16, SNUG_Z + 1.05), 78.0,
                (1.0, 0.56, 0.24), shape="RECTANGLE", sx=0.90, sy=1.60, spread=120)
    L.aim(k, (-1.20, SY1 - 3.0, SNUG_Z + 0.9))

    # THE DOORWAY: dusk outside, plus the square's own lamp.  This is the one
    # cool note in the room and it is what makes the firelight read as warm.
    d = L.light("LGT_dusk_door", "AREA",
                ((DOOR_X0 + DOOR_X1) / 2, YB + 0.30, 1.35), 88.0, (0.52, 0.62, 0.86),
                shape="RECTANGLE", sx=1.10, sy=1.90, spread=150)
    L.aim(d, ((DOOR_X0 + DOOR_X1) / 2 - 2.0, YB - 3.4, 0.9))
    L.light("LGT_square_lamp", "POINT", (DOOR_X0 + 0.18, YB + 1.70, 2.50), 74.0,
            (1.0, 0.66, 0.30), 0.10)
    w = L.light("LGT_dusk_win", "AREA", ((WIN_X0 + WIN_X1) / 2, YB - 0.12, 1.55),
                26.0, (0.55, 0.64, 0.88), shape="RECTANGLE", sx=0.72, sy=0.90,
                spread=150)
    L.aim(w, ((WIN_X0 + WIN_X1) / 2 - 1.6, YB - 3.2, 0.9))

    # the lantern set down beside the stacked chairs -- the second warm pool in
    # the foreground, and the reason the left third of the frame is not a hole
    L.light("LGT_floor_lantern", "POINT", (2.57, 1.73, 0.24), 64.0,
            (1.0, 0.60, 0.27), 0.09)

    # THE STAIR needs its own light or the whole right third is a black mass:
    # a bracket candle on the right wall at the foot of the flight, which is
    # also exactly where an inn would put one.
    L.box("stair_sconce_plate", (XR - 0.14, ST_Y0 + 1.05, 1.62), (0.035, 0.075, 0.10),
          "mat_int_iron", L.coll("PROPS"), bevel=0.006)
    L.cyl("stair_sconce_arm", (XR - 0.30, ST_Y0 + 1.05, 1.66), 0.014, 0.34,
          "mat_int_iron", L.coll("PROPS"), axis="X", verts=8)
    L.lathe("stair_sconce_pan", [(0.0, 0.0), (0.060, 0.010), (0.055, 0.026)],
            (XR - 0.46, ST_Y0 + 1.05, 1.66), L.M("mat_int_iron"), L.coll("PROPS"),
            segments=14)
    L.cyl("stair_sconce_candle", (XR - 0.46, ST_Y0 + 1.05, 1.77), 0.017, 0.19,
          "mat_int_wax", L.coll("PROPS"), verts=10, bevel=0.003)
    L.lathe("stair_sconce_flame", [(0.0, 0.0), (0.014, 0.012), (0.008, 0.045),
                                   (0.0, 0.062)],
            (XR - 0.46, ST_Y0 + 1.05, 1.875), L.M("mat_int_flame_small"),
            L.coll("PROPS"), segments=8)
    L.light("LGT_stair_sconce", "POINT", (XR - 0.46, ST_Y0 + 1.05, 1.90), 82.0,
            (1.0, 0.62, 0.28), 0.05)
    # and a wide, weak rake down the right wall so the balusters have a ground
    # to be silhouetted against instead of dissolving into black
    rw = L.light("LGT_stairwash", "AREA", (XR - 1.35, ST_Y0 + 1.90, 2.62), 96.0,
                 (1.0, 0.70, 0.45), shape="RECTANGLE", sx=1.10, sy=3.40, spread=150)
    L.aim(rw, (XR - 0.55, ST_Y0 + 2.10, 0.95))

    # a weak warm uplight under the ceiling: without it the joists over the far
    # half go to pure black and the top of the frame is a bar again
    up = L.light("LGT_ceiling_bounce", "AREA", (4.10, 3.40, 2.30), 62.0,
                 (1.0, 0.72, 0.46), shape="RECTANGLE", sx=6.0, sy=4.4, spread=150)
    L.aim(up, (4.10, 4.60, 3.40))

    # a very low cool wash standing in for the missing fourth wall, so nothing
    # in the foreground goes to pure black
    a = L.light("LGT_open_amb", "AREA", ((XL + XR) / 2, YF - 3.4, 2.90), 34.0,
                (0.40, 0.50, 0.70), shape="RECTANGLE", sx=9.0, sy=5.0, spread=170)
    L.aim(a, ((XL + XR) / 2, (YF + YB) / 2, 1.2))

    # world: near black.  Every photon in this room comes from a flame.
    w = bpy.data.worlds.new("EMBINN_WORLD")
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.055, 0.062, 0.085, 1.0)
    bg.inputs["Strength"].default_value = 0.16
    bpy.context.scene.world = w

    # bounded haze so the lantern pools and the fire get halos
    L.fog_box("FOG_ROOM", ((XL + XR) / 2 + 0.2, (YF + YB) / 2 + 0.5, 1.60),
              ((XR - XL) / 2 - 0.25, (YB - YF) / 2 + 0.6, 1.55), density=0.0030)


# ================================================================== camera ==

# The camera personality of THIS room, and it is not the personality of any
# other room in the set: LOW (pitch 13 against Dellhollow's 24), WIDE (40 deg
# against 35), and standing INSIDE the room's headroom at z 3.05 rather than
# looking down into an open box.  You are a person in the doorway of a parlour,
# not a surveyor over a model of one.
CAM = dict(aim=(4.35, 4.35, 1.26), vh=5.60, pitch=13.0, az=24.0, fov=40.0)

# What MUST be inside the frame, asserted by tools/embint_verify.py.  The door
# is on this list because seam canon applies indoors: an exit the player cannot
# see is not an exit, whatever the scene graph says.
FRAME_CHECKS = [
    ("fire mouth", (4.45, 7.57, 0.55)),
    ("door opening", (7.60, 6.28, 1.05)),
    ("key board", (1.90, 6.16, 1.80)),
    ("snug opening", (0.10, 4.95, 1.40)),
    ("reception counter", (1.80, 5.70, 1.05)),
    ("stair, mid flight", (7.98, 2.80, 1.30)),
]


def build_cam():
    return L.build_camera("CAM_int_inn", CAM["aim"], CAM["vh"], CAM["pitch"],
                          CAM["az"], CAM["fov"])


def build_pads():
    """walk_pad_door is read BY NAME by scenegraph_derive; the others are the
    interaction marks the runtime offers prompts on."""
    L.pad("walk_pad_door", (DOOR_X0 + DOOR_X1) / 2, YB - 0.78, 1.15, 0.80)
    L.pad("walk_pad_counter", (RC_X0 + RC_X1) / 2, YB - 1.24, 1.80, 0.86)
    L.pad("walk_pad_hearth", (BX0 + BX1) / 2, YB - 0.55, 1.50, 0.90)
    L.pad("walk_pad_snug", -1.10, 4.25, 0.90, 0.70, z=SNUG_Z)


# ==================================================================== main ==

def build(ref=False):
    L.wipe()
    L.seed(SEED)
    CM.make_all()
    kit = L.append_kit(["kit_barrel", "kit_crate", "kit_bucket", "kit_rope_coil",
                        "kit_lantern_hanging", "kit_lantern_light", "REF_human_1p7"])
    build_floor()
    walls = build_walls()
    build_ceiling()
    build_opening_snug()
    build_fire(walls["fire_frame"])
    build_mantel()
    build_reception()
    build_stair()
    build_door()
    build_window()
    build_table_and_life(kit)
    build_snug(kit)
    build_lights(kit)
    build_pads()
    cam = build_cam()
    if ref:
        L.place_kit(kit["REF_human_1p7"], "REF_scale_a", (6.30, 5.20, 0.0), c="CAM")
        L.place_kit(kit["REF_human_1p7"], "REF_scale_b", (2.60, 1.90, 0.0), c="CAM")
    L.qa_report(cam, [
        ("fire mouth", ((BX0 + BX1) / 2, BY1 - 0.18, 0.55)),
        ("door centre", ((DOOR_X0 + DOOR_X1) / 2, YB - 0.02, 1.05)),
        ("key board", ((RC_X0 + RC_X1) / 2 + 0.10, YB - 0.14, 1.86)),
        ("snug opening", (0.10, 4.95, 1.40)),
        ("stair newel", (XR - 0.24 - ST_W, ST_Y0 - 0.06, 1.10)),
        ("stairwell hole", (7.95, 4.70, CEIL)),
    ])
    return cam


def main():
    o = L.argopts(dict(out=OUTBLEND, render="", samples=224, exposure=0.74,
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
