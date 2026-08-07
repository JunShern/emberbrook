"""locksfoot_build.py — detail the Locksfoot district IN THE MASTER.

  Blender -b tools/blends/dellhollow-master.blend -P tools/locksfoot_build.py -- <phase> [save]

  phase: ground | deck | lock | dam | build | boats | dress | all

Parcel `p-lockfive`  x 65.4..91.5  y 21.5..34.5  z -1.5..5.5
Members: moorage, tenant-shack, lock-five, dam-crest-gate.

Jurisdiction (coordinator, 2026-07-29)
--------------------------------------
BUILD    the ground x 66..112 (bank, cliff, strand, the Keepers' Spur rock),
         the Tenant's shack, the Moorage, Lock Five's machinery, dam-five and
         the Dam Crest Gate.
DO NOT   build `p-lockhead` (jurisdiction unresolved), the Keepers' Cottage /
         `p-cottage`, anything in the Weave, or the tar-dark story boat (a
         SHARED library asset built separately — `lf_barge` stands in as a
         mooring placeholder at the Moorage).
The ground is still carried UNDER all of those: terracing a neighbour's walkway
is how a seam is made (manifest 55), not a claim on its parcel.

Dam ruling (user, 2026-07-29, map commit e3f59a0)
-------------------------------------------------
`dam-five` drop 1.8 -> 4.0; `pool-downstream` level -1.6 -> -3.8.  So the tail
water sits 4.0 m under the head, the kit's 4.4 m `lf_wheel_breast` reads at true
scale on the face, and the master's own water and river bed east of x=87 have to
be recut to match the map (they still carry the old -1.6).

Contract
--------
* `walk_*` / `bar_*` are canonical topology: never moved, never edited.  Covered
  ribbons get `hide_render = True` ONLY (manifest 51).
* Everything this pass makes is prefixed `lf_`.
* Props are placed through the walk Corridor, and anything near a walk goes
  through `over_walk()` (manifest 76) rather than being positioned by eye.
"""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (stable_hash, REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          M, world_bbox, reseat_slab, plank_fill, offset_poly, plane_z_fn,
                          point_in_poly, clip_halfplane, dist_poly2, Corridor, place)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PHASES = ["ground", "deck", "lock", "dam", "build", "boats", "dress"]
want = argv[0] if argv else "all"
DO = set(want.split(","))
if "all" in DO or not DO & set(PHASES):
    DO |= set(PHASES)
SAVE = "save" in argv
rng = random.Random(20260731)
COLL = "DIST_locksfoot"
KIT = REPO + "/tools/blends/districts/locksfoot-kit.blend"

# ---------------------------------------------------------------- constants
X0, X1 = 66.10, 112.10          # the ground this district owns (welds to wf_ground)
Y0, Y1 = 12.50, 34.10
ST = 0.40                       # wf_ground's own grid pitch, so the seam welds
DAM_X = 87.00
WATER_MID = 0.20                # pool-mid   (x < 87)
WATER_TAIL = -3.80              # pool-downstream, per the 2026-07-29 map ruling
BED_MID = -4.60
BED_TAIL = -7.60
POOL_THICK = 0.40               # the surface-slab depth water_pool-mid/-upstream use
STRAND = 2.30                   # the flat rock shelf a working waterfront needs
DECK_DROP = 0.055

LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-30s %s" % (kind, what, why))



def smoothstep(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3.0 - 2.0 * u)


def lerp_knots(x, knots):
    """Piecewise-linear through (x, value) knots, flat outside."""
    if x <= knots[0][0]:
        return knots[0][1]
    if x >= knots[-1][0]:
        return knots[-1][1]
    for i in range(len(knots) - 1):
        a, b = knots[i], knots[i + 1]
        if a[0] <= x <= b[0]:
            return a[1] + (b[1] - a[1]) * smoothstep((x - a[0]) / (b[0] - a[0]))
    return knots[-1][1]


# --------------------------------------------------------------- materials
MD, MT, MTD = M("mat_deck"), M("mat_timber"), M("mat_timber_dark")
MROCK, MWET, MIRON = M("mat_rock"), M("mat_wet"), M("mat_iron")
MROPE, MFRESH = M("mat_rope"), M("mat_freshwood")
MRED, MBLUE = M("mat_paint_red"), M("mat_paint_blue")
MDARKWOOD, MWALL = M("mat_wallwood_dark"), M("mat_wallwood")
MGLASS, MGRASS, MFERN = M("mat_lantern_glass"), M("mat_grass"), M("mat_fern")
MVINE, MCREEP = M("mat_vine"), M("mat_leaf_creeper")
MSHINGLE, MTAR = M("mat_shingle_mossy"), M("mat_tar")
MBLACK = M("mat_blackstone")          # Lock Four's own black — do not invent a second
MWATER = M("m_water")


def plain(name, rgb, rough=0.72, metal=0.0):
    """Create OR RE-TONE.  Returning an existing material untouched made this
    script silently non-idempotent for VALUES: `mat_boil` was knocked down twice
    in the source and the master kept the first number both times."""
    m = bpy.data.materials.get(name)
    if m and m.use_nodes and "Principled BSDF" in m.node_tree.nodes:
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1.0)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        return m
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


# The dam's own palette.  `mat_blackstone` already exists (Lock Four) and IS the
# black — these are its coursing, its wet nappe and its boil, nothing more.
MBLACKCAP = plain("mat_stone_black_cap", (0.0305, 0.0284, 0.0262), rough=0.80)
MNAPPE = plain("mat_nappe", (0.0110, 0.0245, 0.0272), rough=0.10)
# finding 86: the boil is the brightest thing in the BAY, never in the frame
MBOIL = plain("mat_boil", (0.132, 0.150, 0.143), rough=0.62)
MSTONEG = plain("mat_stone_grey", (0.0620, 0.0565, 0.0470), rough=0.82)

for c in (COLL, COLL + "_DECK", COLL + "_PROPS", COLL + "_VEG", COLL + "_DAM"):
    coll(c)

# idempotent: a re-run replaces this district, it does not stack a second one
killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("lf_", "veg_lf_")) and o.type == 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
# Finding 129, self-inflicted: removing the OBJECT orphans its light datablock,
# so the next run's practical is `lf_lantern_0_light.001` — which no longer ENDS
# with "_light", so the endswith() clean-up skipped it and eight rebuilds left
# 45 stacked 680 W point lamps where six belong.  Match the PREFIX and clear the
# datablocks too.
for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith("lf_"):
        bpy.data.objects.remove(o, do_unlink=True)
for _d in list(bpy.data.lights):
    if _d.name.startswith("lf_") and _d.users == 0:
        bpy.data.lights.remove(_d)
if killed:
    log("REBUILD", "%d lf_ objects cleared" % killed, "previous pass removed before rebuild")

# --------------------------------------------------------------- corridors
WALKS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
COR0 = Corridor(WALKS, margin=0.0)
COR = Corridor(WALKS, margin=0.30)
KEEP = Corridor(WALKS, margin=0.55)


def over_walk(x, y, z, pad=0.16):
    """True if a solid at (x,y,z) would stand in a walking line (manifest 76)."""
    for dx, dy in ((0, 0), (pad, 0), (-pad, 0), (0, pad), (0, -pad),
                   (pad * .7, pad * .7), (-pad * .7, pad * .7),
                   (pad * .7, -pad * .7), (-pad * .7, -pad * .7)):
        t = COR.top_at(x + dx, y + dy)
        if t is not None and t - 0.10 <= z <= t + 2.05:
            return True
    return False


OCCUPY = []          # (x, y, radius) of every prop this pass has already set down


def spot(x, y, r):
    """Reserve a footprint.  The walk Corridor keeps props out of the WALKING
    lines, but nothing kept them out of EACH OTHER: a 7 m lock coping carrying a
    winch, a capstan, three bollards and the loose cargo placed them all
    independently and the audit found 50 interpenetrations."""
    for ox, oy, orad in OCCUPY:
        if math.hypot(x - ox, y - oy) < (r + orad) * 0.92:
            return False
    OCCUPY.append((x, y, r))
    return True


def clear_box(x, y, z0, z1, pad=0.30):
    """`over_walk` for a TALL object: a 2.9 m winch or a 4 m tree only has to
    touch the corridor once.  Testing its base alone is what let a rim clump 19
    samples of the Lockhead walkway and a balance beam 11 of the boardwalk."""
    z = z0
    while z <= z1 + 0.01:
        if over_walk(x, y, z, pad=pad):
            return False
        z += 0.35
    return True


# ===========================================================================
# 1. GROUND
# ===========================================================================
def noise(x, y):
    return (math.sin(x * 1.27 + y * 0.81) * 0.50 + math.sin(x * 0.47 - y * 2.03) * 0.30 +
            math.sin(x * 3.61 + y * 2.87) * 0.12) * 0.15


# ---- the Waterfront's own height function, so the seam is a WELD ----------
def wf_toe(x):
    return 24.30 - 0.062 * (x - 40.0)


def wf_h(x, y):
    b = 1.06 - 0.010 * (x - 40.0)
    d = wf_toe(x) - y
    if d <= 0.0:
        h = b - 2.30 * (-d) ** 1.06
    elif d < STRAND:
        h = b + 0.115 * d
    else:
        u = min((d - STRAND) / 7.0, 1.0)
        h = b + 0.115 * STRAND + 13.40 * smoothstep(u)
        if d - STRAND > 7.0:
            h += 0.34 * (d - STRAND - 7.0)
    h += noise(x, y)
    t = smoothstep((x - 40.10) / 2.20)
    return BED_MID + (h - BED_MID) * t


# ---- Locksfoot's own -----------------------------------------------------
def water_z(x):
    """Two pools, one dam.  The face itself is the step."""
    return WATER_MID if x < DAM_X else WATER_TAIL


def bed_z(x):
    return BED_MID + (BED_TAIL - BED_MID) * smoothstep((x - 85.5) / 4.5)


# The shoreline.  It has to follow the town rather than a straight line: the
# moorage and the lock stand OUT over the pool, but the Keepers' Spur carries a
# cottage 8 m up, so the rock has to come back OUT under it.
TOE = [(66.0, 22.69), (72.0, 22.45), (78.0, 22.60), (84.0, 23.60),
       (88.5, 25.00), (93.0, 25.45), (99.0, 25.30), (106.0, 24.60), (112.0, 24.20)]


def toe(x):
    return lerp_knots(x, TOE)


# the bank's own top just inland of the water: one pool step, taken across the
# dam's own footprint because the dam IS what holds the two levels apart.
def bank_z(x):
    up = 0.80 - 0.010 * (x - 66.0)
    dn = -3.20 - 0.008 * (x - 88.5)
    return up + (dn - up) * smoothstep((x - 85.5) / 3.0)


# the shoulder the strand climbs to before the landforms take over
TOP = [(66.0, 14.0), (71.0, 12.6), (76.0, 12.4), (82.0, 12.0), (88.0, 8.0),
       (94.0, 6.2), (100.0, 6.0), (112.0, 5.6)]
RUN = [(66.0, 7.0), (74.0, 6.6), (82.0, 6.0), (88.0, 4.4), (94.0, 3.2),
       (104.0, 4.4), (112.0, 5.0)]


def bump(x, y, cx, cy, amp, rx, ry):
    """A landform, not a translation: a smooth rock mass with its own footprint."""
    u = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
    if u >= 1.0:
        return 0.0
    return amp * smoothstep(1.0 - math.sqrt(u))


def lf_h(x, y):
    b = bank_z(x)
    d = toe(x) - y
    if d <= 0.0:                                   # river side of the shoreline
        h = b - 2.30 * (-d) ** 1.06
    elif d < STRAND:                               # the strand (manifest 72)
        h = b + 0.115 * d
    else:
        t, r = lerp_knots(x, TOP), lerp_knots(x, RUN)
        u = min((d - STRAND) / r, 1.0)
        h = b + 0.115 * STRAND + (t - b - 0.115 * STRAND) * smoothstep(u)
        if d - STRAND > r:
            h += 0.34 * (d - STRAND - r)
    # --- landforms.  Both are the reason a landmark stands where it stands.
    # the Lockhead promontory: Odessa's post is 14 m over the basin
    h += bump(x, y, 80.5, 12.0, 5.4, 12.0, 9.0)
    # the Keepers' Spur: a rock buttress that carries the cottage over the drop.
    # It has to reach the SOUTH-WEST corner of walk_pad_keepers-cottage (91.3,
    # 20.7) or the pad hangs on nothing; the pad's river edge is meant to.
    h += bump(x, y, 93.6, 19.4, 10.8, 8.6, 8.0)
    # ... and its downstream shoulder, so the spur is a spur and not a pillar
    h += bump(x, y, 99.5, 20.4, 3.4, 7.4, 6.4)
    # the town wall climbing away behind everything (cliff_town starts at y<=0)
    if y < 15.0:
        h += 1.55 * (15.0 - y)
    h += noise(x, y)
    return h


def raw_h(x, y):
    """wf_ground's own function at the seam, blending into Locksfoot's over 4 m
    (manifest 55: carry the ground under the neighbour, do not decorate a join)."""
    t = smoothstep((x - X0) / 4.0)
    if t <= 0.0:
        return wf_h(x, y)
    if t >= 1.0:
        return lf_h(x, y)
    return wf_h(x, y) * (1.0 - t) + lf_h(x, y) * t


TOPS = [(poly, fn, raw, nm) for poly, fn, raw, nm in COR0.tops]


def clamp_walks(x, y, h):
    """Terrace the ground under every walkway (manifest 38/55).  Only ever cuts."""
    for poly, fn, raw, nm in TOPS:
        d = dist_poly2(x, y, raw)
        if d < 3.6:
            h = min(h, fn(x, y) - 0.45 + d * 1.15)
    return h


def ground_z(x, y):
    return max(clamp_walks(x, y, raw_h(x, y)), bed_z(x))


if "ground" in DO:
    NX = int(round((X1 - X0) / ST)) + 1
    NY = int(round((Y1 - Y0) / ST)) + 1
    V, F = [], []
    for i in range(NX):
        for j in range(NY):
            V.append((X0 + i * ST, Y0 + j * ST, ground_z(X0 + i * ST, Y0 + j * ST)))
    for i in range(NX - 1):
        for j in range(NY - 1):
            a = i * NY + j
            F.append((a, a + NY, a + NY + 1, a + 1))
    new_mesh("lf_ground", V, F, MROCK, COLL)
    log("BUILD", "lf_ground", "%d x %d grid, x %.1f..%.1f y %.1f..%.1f — bank, strand "
        "and cliff welded to wf_ground at x=%.1f, terraced under every walkway"
        % (NX, NY, X0, X1, Y0, Y1, X0))

    # ---- the two pools and the bed the map ruling moved -------------------
    # pool-downstream drops 1.6 -> 3.8 m, so the bed under it (top -3.90) would
    # leave 10 cm of water.  Cut the shared bed at the dam and give the tail its
    # own, deeper one rather than dragging the whole town's bed down.
    rb = bpy.data.objects["riverbed"]
    for v in rb.data.vertices:
        if v.co.x > DAM_X:
            v.co.x = DAM_X
    log("EDIT", "riverbed", "east end 94.0 -> %.1f: the shared bed stops at the dam" % DAM_X)
    box("lf_riverbed_tail", DAM_X, 131.0, 18.0, 78.0, BED_TAIL, BED_TAIL + 0.30,
        MROCK, COLL)
    log("BUILD", "lf_riverbed_tail", "x %.0f..131 at z %.1f — the tail pool needs a bed "
        "under its new -3.8 surface" % (DAM_X, BED_TAIL))

    pd = bpy.data.objects["water_pool-downstream"]
    b0 = world_bbox(pd)
    reseat_slab(pd, WATER_TAIL, POOL_THICK)
    b1 = world_bbox(pd)
    log("EDIT", "water_pool-downstream", "world surface %.2f -> %.2f, slab %.2f..%.2f "
        "(map e3f59a0: dam-five drop 1.8 -> 4.0).  Reseated onto an IDENTITY transform "
        "in world coords, like water_pool-mid: this object shipped with origin z -1.8 "
        "and a 0.2 z scale, and the old code wrote the world level straight into "
        "`v.co.z`" % (b0[5], b1[5], b1[4], b1[5]))


# ===========================================================================
# diagnostics — every walk face in the region against the ground under it
# ===========================================================================
def ground_report():
    print("\n  ground vs. every walk mesh in the region (gap = walk_top - ground):")
    rows = []
    for ob in WALKS:
        b = world_bbox(ob)
        if b[1] < X0 - 0.5 or b[0] > X1:
            continue
        Mx = ob.matrix_world
        N = Mx.to_3x3().inverted().transposed()
        gaps = []
        for p in ob.data.polygons:
            if (N @ p.normal).normalized().z <= 0.5:
                raw = [Mx @ ob.data.vertices[i].co for i in p.vertices]
                cx = sum(v.x for v in raw) / len(raw)
                cy = sum(v.y for v in raw) / len(raw)
                cz = sum(v.z for v in raw) / len(raw)
                if X0 <= cx <= X1 and Y0 <= cy <= Y1:
                    gaps.append(cz - ground_z(cx, cy))
        if gaps:
            rows.append((min(gaps), max(gaps), ob.name))
    rows.sort()
    for lo, hi, nm in rows:
        flag = "  <-- BURIED" if lo < 0.30 else ("  (on piles)" if lo > 3.0 else "")
        print("    %-52s %6.2f .. %6.2f%s" % (nm, lo, hi, flag))
    bad = [r for r in rows if r[0] < 0.30]
    print("    %d walk meshes sampled, %d with less than 0.30 m of air under them"
          % (len(rows), len(bad)))
# ===========================================================================
# KIT — appended read-only from tools/blends/districts/locksfoot-kit.blend
# ===========================================================================
# `bpy.ops.wm.append` fails headless (manifest 4), and `libraries.load` rewrites
# the list it is given in place, so it gets a COPY (manifest 31).
_KIT_SRC = {}


def kit_load(names):
    todo = [n for n in names if n not in _KIT_SRC]
    if not todo:
        return
    before = set(bpy.data.objects.keys())
    with bpy.data.libraries.load(KIT, link=False) as (src, dst):
        dst.objects = list([n for n in todo if n in src.objects])
        dst.materials = list([m for m in src.materials if m.startswith("lf_")])
    got = [o for o in bpy.data.objects if o.name not in before]
    hold = coll("LF_KITSRC")
    hold.hide_render = True
    for o in got:
        base = o.name.split(".")[0]
        if base in todo and base not in _KIT_SRC:
            _KIT_SRC[base] = o
            # RENAME the source out of the way.  Left as `lf_crest_gate`, the
            # appended donor owns the name and every placed copy becomes
            # `lf_crest_gate.001` — which is what the QA reported, and what a
            # handover would then have to explain.
            o.name = "KITSRC_" + base
            if o.data:
                o.data.name = "KITSRC_" + base
        for c in list(o.users_collection):
            c.objects.unlink(o)
        hold.objects.link(o)
    # The kit's textures are relative to tools/blends/districts/ (manifest 63) and
    # would resolve to nothing from the master.  Re-point ONLY the maps the kit
    # ships — the first version walked every image in the file, which would have
    # rewritten the whole town's texture paths on the way past.
    KIT_MAPS = ("weathered_planks_Diffuse.jpg", "old_stone_wall_02_Diffuse.jpg",
                "red_slate_roof_tiles_01_Diffuse.jpg")
    for im in list(bpy.data.images):
        base = os.path.basename(im.filepath) if im.filepath else ""
        if base not in KIT_MAPS:
            continue
        cand = os.path.join(REPO, "tools", "textures", base)
        if os.path.exists(cand):
            im.filepath = cand
        # every append makes a fresh datablock; without this the master collects
        # old_stone_wall_02_Diffuse.jpg.001 ... .0NN, one per rebuild
        first = bpy.data.images.get(base)
        if first is not None and im is not first:
            im.user_remap(first)
            bpy.data.images.remove(im)
    # ... and the same is true of the MATERIALS, which finding 130 missed because
    # a material datablock is invisible in a render and `use_fake_user` keeps it
    # from ever being purged.  `kit_load` is called once per group of assemblies
    # and each call asks for all eight `lf_*` materials, so the master collected
    # lf_deck.001 ... lf_deck.268 — 2000 unused copies — and every placed
    # assembly pointed at its own private set.  Remap onto the canonical name.
    for m in list(bpy.data.materials):
        if not m.name.startswith("lf_") or "." not in m.name:
            continue
        canon = bpy.data.materials.get(m.name.split(".")[0])
        if canon is not None and canon is not m:
            m.user_remap(canon)
            bpy.data.materials.remove(m)
    for m in bpy.data.materials:
        m.use_fake_user = True


def kp(name, target, rz=0.0, cname=None, oname=None, mode="cxy_minz", scale=1.0):
    """Place a kit assembly in TOWN axes.

    `place()` bakes Rz(90 deg + rz) because it was written to carry probe-frame
    geometry into the town; the Locksfoot kit is already authored in town axes,
    so town-identity is rz = -90 deg.
    """
    kit_load([name])
    src = _KIT_SRC.get(name)
    if src is None:
        log("MISS", name, "not in the kit")
        return None
    ob = place(src, target, rz=rz - math.pi / 2, scale=scale, mode=mode,
               name=oname or ("lf_%s_%d" % (name[3:], len(bpy.data.objects))),
               cname=cname or COLL)
    return ob


def remap(ob, table):
    """Re-point a kit object's material SLOTS by NAME.

    The kit speaks a glTF-safe language (image x vertex colour) and its
    `lf_stone` is a warm grey — right for a keeper's cottage, wrong for the one
    thing in this town that has to out-dark everything else.  Manifest 82: key
    off the material NAME, never the slot index.
    """
    if ob is None or ob.type != 'MESH':
        return
    for i, ms in enumerate(ob.data.materials):
        if ms is not None and ms.name in table and table[ms.name] is not None:
            ob.data.materials[i] = table[ms.name]


# ref 6b: BLACK stone.  `mat_blackstone` is Lock Four's own value and the plan
# is explicit that this town gets one black, not two.
# `mat_deck` is the town's PALE walking plank and it made the spill bays' raised
# gate leaves read as sheets of card hanging on a black wall — the manifest-40
# failure wearing a different hat.  A dam's timber is dark, wet and structural.
DAM_MATS = {"lf_stone": MBLACK, "lf_matte": MBLACKCAP, "lf_water": MNAPPE,
            "lf_foam": MBOIL, "lf_iron": MIRON, "lf_deck": MTD,
            "lf_shingle": MBLACKCAP, "lf_glass": MGLASS}
# a wheel is wet timber and iron, and it stands against the black
WHEEL_MATS = {"lf_deck": MTD, "lf_matte": MTD, "lf_stone": MBLACK,
              "lf_iron": MIRON, "lf_shingle": MWET}
GATE_MATS = {"lf_stone": MBLACK, "lf_matte": MBLACKCAP, "lf_deck": MTD,
             "lf_iron": MIRON}


def kill(names, why):
    gone = []
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o:
            gone.append(nm)
            bpy.data.objects.remove(o, do_unlink=True)
    if gone:
        log("REPLACE", "%d blockout meshes" % len(gone), "%s: %s" % (why, ", ".join(gone[:4])))
    return gone


# ===========================================================================
# 2. DECKING over the walk ribbons the district owns
# ===========================================================================
FLAT_NAMES = [
    "walk_e_tenant-shack__fish-dock_l0", "walk_pad_tenant-shack",
    "walk_e_moorage__tenant-shack_l0", "walk_lm_moorage",
    "walk_e_moorage__lock-five_l0", "walk_e_moorage__lock-five_l1",
    "walk_pad_lock-five", "walk_pad_dam-crest-gate",
    "walk_e_lock-five__north-landing_l0",
    "walk_e_weave-huts__moorage_landing.002",
    "walk_e_keepers-cottage__lock-five_landing.001",
    "walk_e_keepers-cottage__lock-five_landing.002",
] + ["walk_e_lockhead__keepers-cottage_l%d" % k for k in range(6, 19)]
# the switchbacks: Locksfoot decks the LOWER legs (the Weave and the cottage own
# the upper ones), so the break is always AT a landing, never mid-flight.
STAIR_NAMES = [o.name for o in WALKS
               if (("weave-huts__moorage_l2_t" in o.name or
                    "weave-huts__moorage_l3_t" in o.name or
                    "keepers-cottage__lock-five_l2_t" in o.name or
                    "keepers-cottage__lock-five_l3_t" in o.name))]
PLANK_ANG = {"walk_lm_moorage": math.radians(90),
             "walk_pad_lock-five": math.radians(90),
             "walk_pad_dam-crest-gate": math.radians(90),
             "walk_pad_tenant-shack": math.radians(0)}


def ribbon_angle(pts):
    best, ang = 0.0, 0.0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = (pts[j] - pts[i]).to_2d()
            if d.length > best:
                best, ang = d.length, math.atan2(d.y, d.x)
    return ang + math.pi / 2


def below_walk(px, py, pz):
    t = COR0.top_at(px, py)
    if t is not None and pz > t - 0.02:
        return False
    return not COR.blocked((px, py, pz))


if "deck" in DO:
    deck, joists, piles, stairs, bracing = [], [], [], [], []
    PILE_POS = []
    for nm in FLAT_NAMES + STAIR_NAMES:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        is_stair = nm in STAIR_NAMES
        Mx = ob.matrix_world
        N = Mx.to_3x3().inverted().transposed()
        for pi, p in enumerate(ob.data.polygons):
            if (N @ p.normal).normalized().z <= 0.5:
                continue
            raw = [Mx @ ob.data.vertices[i].co for i in p.vertices]
            cx = sum(v.x for v in raw) / len(raw)
            cy = sum(v.y for v in raw) / len(raw)
            cz = sum(v.z for v in raw) / len(raw)
            top = COR0.top_at(cx, cy)
            if top is not None and top > cz + 0.15:
                continue                              # buried face (manifest 36)
            # stairs are INSET, flat decking is generous (manifest 74)
            poly = offset_poly(raw, -0.045 if is_stair else 0.38)
            zfn = plane_z_fn(raw)
            ang = PLANK_ANG.get(nm, ribbon_angle(raw))
            v, f = plank_fill(poly, ang, w=0.26 if is_stair else 0.29, gap=0.014,
                              thick=0.09 if is_stair else 0.11, jitter=0.010,
                              drop=DECK_DROP, zfn=zfn, seed=(stable_hash(nm) + pi) & 0xffff,
                              keep=None if is_stair else
                              (lambda px, py, pz: below_walk(px, py, pz)))
            tgt = stairs if is_stair else deck
            tgt.append(new_mesh("lf_d_%d" % len(tgt), v, f, MD, COLL + "_DECK"))
            if is_stair:
                continue
            xs = [q.x for q in poly]
            ys = [q.y for q in poly]
            ax0, ax1, ay0, ay1 = min(xs), max(xs), min(ys), max(ys)
            long_x = (ax1 - ax0) >= (ay1 - ay0)
            u = (ax0 if long_x else ay0) + 0.4
            lim = (ax1 if long_x else ay1) - 0.35
            while u <= lim:
                if long_x:
                    seg = clip_halfplane(clip_halfplane(poly, 1, 0, u + 0.09), -1, 0, -(u - 0.09))
                else:
                    seg = clip_halfplane(clip_halfplane(poly, 0, 1, u + 0.09), 0, -1, -(u - 0.09))
                if len(seg) >= 3:
                    w = [q.y for q in seg] if long_x else [q.x for q in seg]
                    a0, a1 = min(w), max(w)
                    pa = (u, a0) if long_x else (a0, u)
                    pb = (u, a1) if long_x else (a1, u)
                    mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                    if all(below_walk(q[0], q[1], zfn(q[0], q[1]) - 0.19) for q in (pa, pb, mid)):
                        joists.append(beam("jo", (pa[0], pa[1], zfn(*pa) - 0.28),
                                           (pb[0], pb[1], zfn(*pb) - 0.28), 0.13, 0.18,
                                           MTD, COLL + "_DECK"))
                u += 0.95
            gx = ax0 + 0.6
            while gx < ax1 - 0.4:
                gy = ay0 + 0.6
                while gy < ay1 - 0.4:
                    if point_in_poly(gx, gy, poly) and below_walk(gx, gy, zfn(gx, gy) - 0.30):
                        zt = zfn(gx, gy) - 0.30
                        wz = water_z(gx)
                        zb = min(ground_z(gx, gy), wz - 0.1) - 0.40
                        if zt - zb > 0.9:
                            piles.append(cyl("pl", (gx, gy, zb), (gx, gy, zt),
                                             0.135 + rng.random() * 0.045, 7,
                                             MWET if zb < wz else MTD, COLL + "_DECK"))
                            PILE_POS.append((gx, gy, zb, zt))
                    gy += 1.55
                gx += 1.55

    # cross bracing between neighbouring piles: a forest of bare poles reads as
    # scaffolding, a braced one reads as built (the Waterfront's own trick)
    for i, (x1, y1, zb1, zt1) in enumerate(PILE_POS):
        for x2, y2, zb2, zt2 in PILE_POS[i + 1:]:
            d = math.hypot(x2 - x1, y2 - y1)
            if 1.2 < d < 2.4:
                zt = min(zt1, zt2) - 0.55
                zb = max(min(zb1, zb2) + 0.55, zt - 2.6)
                if zt - zb > 0.5:
                    bracing.append(beam("br", (x1, y1, zb), (x2, y2, zt), 0.09, 0.13,
                                        MTD, COLL + "_DECK"))
                    bracing.append(beam("br", (x1, y1, zt), (x2, y2, zb), 0.09, 0.13,
                                        MTD, COLL + "_DECK"))

    join_meshes(deck, "lf_planking", COLL + "_DECK")
    join_meshes(joists, "lf_joists", COLL + "_DECK")
    join_meshes(piles, "lf_piles", COLL + "_DECK")
    join_meshes(bracing, "lf_pile_bracing", COLL + "_DECK")
    log("BUILD", "lf_planking / joists / piles",
        "%d flat ribbons decked, %d piles driven to the bed, %d braces"
        % (len(FLAT_NAMES), len(piles), len(bracing)))

    # ---- treads + one stringer per FLIGHT (manifest 74) -------------------
    strp = []
    flights = {}
    for nm in STAIR_NAMES:
        key = nm.rsplit("_t", 1)[0]
        b = world_bbox(bpy.data.objects[nm])
        flights.setdefault(key, []).append(
            (Vector(((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, b[4])), b))
    for key, treads in flights.items():
        if len(treads) < 2:
            continue
        treads.sort(key=lambda t: -t[0].z)
        a, b0 = treads[0][0], treads[-1][0]
        run = Vector((b0.x - a.x, b0.y - a.y, 0.0))
        if run.length < 0.2:
            continue
        ax = run.normalized()
        pp = Vector((-ax.y, ax.x, 0.0))
        hw = 0.0
        for c, bb in treads:
            for cx2, cy2 in ((bb[0], bb[2]), (bb[1], bb[2]), (bb[1], bb[3]), (bb[0], bb[3])):
                hw = max(hw, abs((cx2 - c.x) * pp.x + (cy2 - c.y) * pp.y))
        hw += 0.13

        def clear_end(p, d):
            for k in range(26):
                q = p + d * (0.10 * k)
                t = COR.top_at(q.x, q.y)
                if t is None or q.z < t - 0.10:
                    return q
            return p + d * 2.6

        def blocked_at(q):
            return (over_walk(q.x, q.y, q.z + 0.20, pad=0.24) or
                    over_walk(q.x, q.y, q.z + 0.58, pad=0.24))

        for sgn in (1, -1):
            p0 = clear_end(a + pp * (hw * sgn) - ax * 0.40 + Vector((0, 0, -0.16)), ax)
            p1 = clear_end(b0 + pp * (hw * sgn) + ax * 0.40 + Vector((0, 0, -0.16)), -ax)
            for _ in range(24):
                n = 12
                bad = [k for k in range(n + 1) if blocked_at(p0.lerp(p1, k / n))]
                if not bad or (p1 - p0).length < 0.9:
                    break
                if sum(bad) / len(bad) < n / 2:
                    p0 = p0.lerp(p1, 0.10)
                else:
                    p1 = p1.lerp(p0, 0.10)
            if (p1 - p0).length < 0.9 or any(blocked_at(p0.lerp(p1, k / 12)) for k in range(13)):
                continue
            strp.append(beam("st", p0, p1, 0.11, 0.40, MTD, COLL + "_DECK"))
    join_meshes(stairs, "lf_stair_treads", COLL + "_DECK")
    join_meshes(strp, "lf_stair_stringers", COLL + "_DECK")
    log("BUILD", "lf_stair_treads / stringers",
        "%d treads on the lower legs of both switchbacks, %d stringers"
        % (len(STAIR_NAMES), len(strp)))

    # ---- guards, placed by SEARCH (manifest 76) ---------------------------
    def rail_run(pts, h=1.02):
        parts = []
        for x, y, z in pts:
            parts.append(obox("rp", x, y, z - 0.30 + (h + 0.32) / 2, 0.11, 0.11, h + 0.32,
                              rz=rng.random() * 0.2, mat=MT, cname=COLL + "_DECK"))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 3.4:
                continue
            for dz, sec in ((h, (0.09, 0.10)), (h * 0.55, (0.07, 0.07))):
                parts.append(beam("rr", (a[0], a[1], a[2] + dz), (b[0], b[1], b[2] + dz),
                                  sec[0], sec[1], MT, COLL + "_DECK"))
        return parts

    def outer_edge(x, ylo, yhi, out=0.30):
        """The deck point `out` metres OUTBOARD of the walk's river lip at x."""
        y = yhi
        z = None
        while y > ylo:
            z = COR0.top_at(x, y)
            if z is not None:
                break
            y -= 0.04
        if z is None:
            return None
        py = y + out
        while py < y + 1.2 and COR.top_at(x, py) is not None:
            py += 0.04
        # A GUARD THAT COULD NOT GET OUTBOARD MUST NOT BE BUILT (2026-08-07, measured).
        # This walk gives up at 1.2 m and, before this line, PLANTED THE POST ANYWAY —
        # so the log line below ("none in a walking line") was a claim the code did not
        # make true.  It came due when the searched moorage flight's hairpin landing
        # moved out over the water inside this band: `_court_probe --who` named
        # `lf_railings` on 7 cells at x 69.3..69.7, z -29.7..-30.3, and the climb up the
        # flight STALLED there (23/23 down, 11/23 up) while the fill still called it one
        # component.  Same family as lay_stair_rails' dropped stub: a guard standing in
        # a walking line is worse than a missing guard.
        if COR.top_at(x, py) is not None:
            return None
        return (x, py, z)

    rails = []
    for x0r, x1r, ylo, yhi, stp in ((66.4, 71.6, 24.0, 29.0, 1.70),
                                    (72.6, 80.4, 24.0, 31.4, 1.70),
                                    (81.0, 85.4, 25.0, 29.2, 1.60),
                                    (88.6, 97.4, 25.0, 29.2, 1.70)):
        pts = []
        x = x0r
        while x <= x1r:
            e = outer_edge(x, ylo, yhi)
            if e:
                pts.append(e)
            x += stp
        rails += rail_run(pts)
    join_meshes(rails, "lf_railings", COLL + "_DECK")
    log("BUILD", "lf_railings", "guards along the river lip of the boardwalk, the moorage "
        "and the tail-race walk — every post set outboard by search, none in a walking line")

    # ---- ribbons that now carry real decking stop rendering (manifest 51) --
    hid = 0
    for nm in FLAT_NAMES + STAIR_NAMES:
        o = bpy.data.objects.get(nm)
        if o is not None and not o.hide_render:
            o.hide_render = True
            hid += 1
    log("HIDE", "%d walk ribbons render-hidden" % hid,
        "hide_render only — hide_viewport would drop them from the glTF and the "
        "runtime would lose its collision")


# ===========================================================================
# 3. LOCK FIVE — a working lock, not scenery
# ===========================================================================
CH_Y0, CH_Y1 = 26.20, 29.80          # the chamber between the walls
CH_X0, CH_X1 = 83.40, 90.40
COPE_Z = 0.55                        # coping, 0.35 over the head pool
CH_FLOOR = -2.10
CH_WATER = -1.40                     # mid-cycle: the chamber is emptying
y_s, y_n = CH_Y0, CH_Y1              # overwritten by the wall search below

if "lock" in DO:
    kill(["lm_lock-five_wallS", "lm_lock-five_wallN", "lm_lock-five_gateA",
          "lm_lock-five_gateB"], "Lock Five blockout replaced with real masonry")
    parts = []

    def chamber_wall(name, ya, yb, inner):
        """Coped masonry with a string course, founded on the bed.

        The blockout walls stood 0.21 m from `walk_e_moorage__lock-five_l1` and
        cost 6 blocked + 17 headroom samples.  The rebuild pulls the inner face
        back until `over_walk` lets go, so the same wall costs nothing.
        """
        # Search OUTWARD (toward the wall's own back face `ya`), and probe at the
        # coping's real height.  Probing 0.4 m higher than the stone actually is
        # made `walk_pad_dam-crest-gate` — which the north wall correctly stands
        # UNDER — read as an obstruction and ate the whole chamber.
        step = 0.06 if ya > inner else -0.06
        y_in = inner
        for _ in range(14):
            if not any(over_walk(x, y_in, COPE_Z, pad=0.10)
                       for x in (CH_X0 + 0.4, (CH_X0 + CH_X1) / 2, CH_X1 - 0.4)):
                break
            y_in += step
        a, b = min(ya, y_in), max(ya, y_in)
        parts.append(box(name, CH_X0, CH_X1, a, b, -4.20, COPE_Z - 0.16, MSTONEG,
                         COLL + "_PROPS"))
        parts.append(box(name + "_cap", CH_X0 - 0.10, CH_X1 + 0.10, a - 0.09, b + 0.09,
                         COPE_Z - 0.16, COPE_Z, MBLACKCAP, COLL + "_PROPS"))
        # a string course, or a 4.75 m wall is one flat mass with no form
        parts.append(box(name + "_sc", CH_X0 - 0.06, CH_X1 + 0.06, a - 0.05, b + 0.05,
                         -1.62, -1.44, MBLACKCAP, COLL + "_PROPS"))
        # the wet band the chamber leaves when it empties
        parts.append(box(name + "_wet", CH_X0 + 0.02, CH_X1 - 0.02,
                         (b - 0.03) if inner > (ya + yb) / 2 else (a - 0.01),
                         (b + 0.01) if inner > (ya + yb) / 2 else (a + 0.03),
                         CH_FLOOR, CH_WATER + 0.55, MWET, COLL + "_PROPS"))
        return y_in

    y_s = chamber_wall("lf_lock_wallS", 24.60, 26.20, 26.20)
    y_n = chamber_wall("lf_lock_wallN", 31.40, 29.80, 29.80)
    log("BUILD", "lf_lock_wallS / wallN", "coped masonry to the bed, inner faces set by "
        "search at y=%.2f / %.2f (blockout: 26.20 / 29.80)" % (y_s, y_n))

    # ---- the pool has to STOP at the chamber ------------------------------
    # `walk_pad_lock-five` sits at z -0.08 and `pool-mid` is a solid slab to
    # z +0.20, so the lock pad is UNDER the pool surface and its down-rays hit
    # water.  That is not decoration: a chamber is cut off from its pool by its
    # own gates, so the pool gets a notch and the chamber keeps its own lower,
    # mid-cycle water.  Worth 22 blocked samples.
    pm = bpy.data.objects["water_pool-mid"]
    pb = world_bbox(pm)
    HX0 = CH_X0 + 0.70
    slab = [box("wpm_a", pb[0], HX0, pb[2], pb[3], pb[4], pb[5], MWATER, COLL + "_PROPS"),
            box("wpm_b", HX0, pb[1], y_n, pb[3], pb[4], pb[5], MWATER, COLL + "_PROPS")]
    bpy.data.objects.remove(pm, do_unlink=True)
    join_meshes(slab, "water_pool-mid", COLL + "_PROPS")
    log("EDIT", "water_pool-mid", "notched x %.2f..%.2f y %.2f..%.2f — the pool no longer "
        "stands over the lock chamber or its walk pad" % (HX0, pb[1], pb[2], y_n))
    # THIS PASS DESTROYS THE WATER-TRANSPARENCY TRANCHE, AND IT IS SILENT ABOUT IT
    # (2026-08-07, measured).  The notch above REBUILDS `water_pool-mid` out of two fresh
    # boxes and the chamber's `lf_lock_water` below is a fresh box too — so both come back
    # as 8- and 16-vertex slabs with NO `Col` attribute, which is exactly the state
    # docs/plans/water-transparency.md exists to remove.  Measured across one re-run:
    # water_pool-mid 8648 -> 16 verts, water_pool-downstream 4290 -> 8, lf_lock_water
    # 90 -> 8.  Nothing failed; the gates were green; the RIVER SIMPLY WAS NOT IN THE
    # PLATES any more (the fishdock plate went from 21.1% water-coloured pixels to ~0 and
    # its moored boat sat on dry bed).  Same shape as the emb_dress/emb_decimate rule in
    # CLAUDE.md: A PASS THAT REBUILDS A DRESSED DATABLOCK OWES THAT DRESSING'S RE-RUN IN
    # THE SAME WINDOW.  The order is fixed and t2_water_shader's own header states it:
    #     t2_water_bed.py -- save        (the bathymetry IS the deliverable)
    #     t2_water_shader.py -- save     (never before the bed)
    log("OWED", "t2 water chain", "this pass rebuilt water_pool-mid and lf_lock_water as "
        "flat slabs — RUN tools/t2_water_bed.py THEN tools/t2_water_shader.py (in that "
        "order, both with `save`) BEFORE any export or bake, or the river ships opaque "
        "and the plates lose it entirely")

    # floor + the water standing in it
    parts.append(box("lf_lock_floor", CH_X0, CH_X1, y_s, y_n, CH_FLOOR - 0.35, CH_FLOOR,
                     MSTONEG, COLL + "_PROPS"))
    box("lf_lock_water", CH_X0 + 0.05, CH_X1 - 0.05, y_s + 0.05, y_n - 0.05,
        CH_WATER - 0.30, CH_WATER, MWATER, COLL + "_PROPS")

    # ---- two mitre gate pairs -------------------------------------------
    # The kit's smallest leaf is 2.60 m and the chamber is 3.60 m wide, so the
    # mitre is deep (46 deg off the wall rather than the canal-standard 20).
    # That is the honest way to use the kit: SCALING a kit object breaks its
    # texel-density contract, and a deep mitre on a 7 m lock still reads.
    # THE GATES CANNOT STAND MITRED, AND THE TOPOLOGY IS WHY.
    # `walk_e_moorage__lock-five_l1` (x 81.4..86.2) and
    # `walk_e_lock-five__north-landing_l0` (x 87.8..97.9) run at z ~0 straight
    # THROUGH both gate heads, and `walk_pad_lock-five` takes 2.60 m of a 3.60 m
    # chamber.  A closed leaf is 3.74 m tall, so anything mitred across the
    # chamber stands in the walking line: the first attempt cost 24 blocked
    # samples.  Locks recess their leaves into the wall when they are OPEN, and
    # an OPEN lock is also the correct state for a district whose story is a boat
    # being brought through.  So each leaf lies ALONG its wall, in its recess,
    # proud only by what the 0.30 m QA margin leaves free — and it is placed only
    # if `clear_box` agrees.
    made_g = 0
    for hx, tag in ((CH_X0 + 1.55, "upper"), (CH_X1 - 1.55, "lower")):
        for sgn, wy in ((1, y_s - 0.42), (-1, y_n + 0.42)):
            rz = -math.pi / 2 if sgn > 0 else math.pi / 2
            if not all(clear_box(hx + dx, wy, CH_FLOOR + 0.2, CH_FLOOR + 3.9, pad=0.34)
                       for dx in (-1.2, 0.0, 1.2)):
                continue
            kp("lf_gate_leaf_low", (hx, wy, CH_FLOOR + 0.10), rz=rz, mode="cxy_minz",
               oname="lf_gate_%s_%s" % (tag, "S" if sgn > 0 else "N"),
               cname=COLL + "_PROPS")
            made_g += 1
            # a recess in the wall for the leaf to lie in, so it reads as housed
            box("lf_gate_recess_%s_%s" % (tag, "S" if sgn > 0 else "N"),
                hx - 1.45, hx + 1.45, wy - 0.46 * sgn, wy + 0.46 * sgn,
                CH_FLOOR, COPE_Z - 0.20, MSTONEG, COLL + "_PROPS")
    log("BUILD", "lf_gate_* x%d" % made_g, "the leaves lie OPEN in wall recesses, not "
        "mitred across the chamber: the boardwalk runs through both gate heads at z~0 "
        "and a 3.74 m closed leaf there cost 24 blocked samples")

    # ---- winches, sluices, capstan, bollards on the coping ---------------
    made_m = 0
    for hx in (CH_X0 + 0.70, CH_X1 - 0.70):
        for yy in (y_s - 0.80, y_n + 0.80):
            if clear_box(hx, yy, COPE_Z, COPE_Z + 2.90, pad=0.78) and spot(hx, yy, 0.80):
                kp("lf_gate_winch", (hx, yy, COPE_Z), cname=COLL + "_PROPS")
                made_m += 1
        for yy in (y_s + 0.04, y_n - 0.04):
            sx = hx + (1.85 if hx < (CH_X0 + CH_X1) / 2 else -1.85)
            if spot(sx, yy, 0.55):
                kp("lf_sluice_paddle", (sx, yy, COPE_Z - 2.60), cname=COLL + "_PROPS")
    for px, py in ((CH_X0 + 2.2, y_s - 0.85), (CH_X1 - 2.4, y_n + 0.85)):
        if clear_box(px, py, COPE_Z, COPE_Z + 1.15, pad=0.95) and spot(px, py, 1.05):
            kp("lf_capstan", (px, py, COPE_Z), cname=COLL + "_PROPS")
            made_m += 1
    for px in (CH_X0 + 1.4, CH_X0 + 3.6, CH_X1 - 1.6):
        for py in (y_s - 0.85, y_n + 0.85):
            if clear_box(px, py, COPE_Z, COPE_Z + 1.70, pad=0.42) and spot(px, py, 0.34):
                kp("lf_bollard", (px, py, COPE_Z), cname=COLL + "_PROPS")
                made_m += 1
    log("BUILD", "lock machinery", "%d winches / capstans / bollards on the coping + 4 "
        "sluice paddles set into the chamber walls, all filtered through over_walk()" % made_m)

    # ---- a gangway over the chamber where the walk pad already is --------
    # `walk_pad_lock-five` is canon and it sits MID-CHAMBER, so the only honest
    # reading is the keeper's gang bridge across the lock.  Beams land on both
    # copings; the deck itself is the planking pass's.
    for gy in (y_s + 0.25, y_n - 0.25):
        beam("lf_lock_gangbeam_%d" % int(gy), (85.35, gy, -0.34), (88.55, gy, -0.34),
             0.20, 0.30, MTD, COLL + "_PROPS")
    log("BUILD", "lf_lock_gangbeam x2", "the keeper's gang bridge that carries "
        "walk_pad_lock-five across the chamber")

    # ---- Odessa's ladder gets an iron stringer instead of a slab ---------
    kill(["e_lockhead__lock-five_rail"], "the ladder's blockout rail was one 8-vertex "
         "diagonal slab through the cliff")
    rungs = sorted([o for o in bpy.data.objects
                    if o.name.startswith("e_lockhead__lock-five_rung")],
                   key=lambda o: -world_bbox(o)[4])
    pts = [Vector(((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2))
           for b in (world_bbox(o) for o in rungs)]
    lad = []
    for sgn in (1, -1):
        prev = None
        for p in pts:
            q = p + Vector((0.30 * sgn, -0.12 * sgn, 0.0))
            if prev is not None:
                mid = (prev + q) / 2.0
                if not over_walk(mid.x, mid.y, mid.z, pad=0.16):
                    lad.append(beam("ld", prev, q, 0.05, 0.09, MIRON, COLL + "_PROPS"))
            prev = q
    # a cage where it passes the coping, which is where a fall would matter
    for p in pts:
        if p.z < 4.6:
            continue
        if p.z > 9.0:
            continue
        for sgn in (1, -1):
            if over_walk(p.x + 0.46 * sgn, p.y - 0.18 * sgn, p.z, pad=0.16):
                continue
            lad.append(beam("lc", p + Vector((0.30 * sgn, -0.12 * sgn, 0.0)),
                            p + Vector((0.62 * sgn, -0.24 * sgn, 0.0)), 0.05, 0.05,
                            MIRON, COLL + "_PROPS"))
    join_meshes(lad, "lf_ladder_iron", COLL + "_PROPS")
    log("BUILD", "lf_ladder_iron", "%d rungs given two iron stringers and a cage at the "
        "cliff break — the rungs themselves are untouched blockout topology" % len(pts))


# ===========================================================================
# 4. STRUCTURES — the Tenant's shack and the Moorage staging
# ===========================================================================
def staging(name, x0, x1, y0, y1, z, ang=math.radians(90), skirt=True, mat=None):
    poly = [Vector((x0, y0, z)), Vector((x1, y0, z)), Vector((x1, y1, z)), Vector((x0, y1, z))]
    v, f = plank_fill(poly, ang, w=0.30, gap=0.016, thick=0.12, jitter=0.014, drop=0.0,
                      zfn=lambda X, Y: z, seed=stable_hash(name) & 0xffff)
    parts = [new_mesh(name, v, f, mat or MD, COLL + "_DECK")]
    n = max(1, int((x1 - x0 - 0.8) / 1.5))
    for k in range(n + 1):
        u = x0 + 0.45 + k * (x1 - x0 - 0.9) / max(n, 1)
        parts.append(beam("jo", (u, y0, z - 0.22), (u, y1, z - 0.22), 0.13, 0.20, MT,
                          COLL + "_DECK"))
        if not skirt:
            continue
        m = max(1, int((y1 - y0 - 0.8) / 1.6))
        for q in range(m + 1):
            w = y0 + 0.42 + q * (y1 - y0 - 0.85) / max(m, 1)
            wz = water_z(u)
            zb = min(ground_z(u, w), wz - 0.1) - 0.45
            if z - 0.3 - zb > 0.8:
                parts.append(cyl("pl", (u, w, zb), (u, w, z - 0.28),
                                 0.13 + rng.random() * 0.04, 7,
                                 MWET if zb < wz else MTD, COLL + "_DECK"))
    return join_meshes(parts, name, COLL + "_DECK")


if "build" in DO:
    kill(["lm_tenant-shack_body", "lm_tenant-shack_roof"],
         "the tenant's shack blockout stood ON walk_pad_tenant-shack (5 blocked samples)")
    # The kit shack is 5.07 x 5.04 m and the pad runs y 24.70..27.30, so the
    # building goes INLAND of its own pad and opens onto it — a blockout that
    # swallows its landmark's standing pad is what cost the baseline its samples.
    sh = kp("lf_tenant_shack", (69.90, 22.55, 1.30), rz=math.pi,
            oname="lf_tenant_shack", cname=COLL)
    b = world_bbox(sh)
    log("BUILD", "lf_tenant_shack", "kit oxblood shack at x %.2f..%.2f y %.2f..%.2f "
        "z %.2f..%.2f — inland of walk_pad_tenant-shack, porch onto it"
        % (b[0], b[1], b[2], b[3], b[4], b[5]))
    # it stands over the strand AND over the water, so it needs real legs
    legs = []
    for lx in (b[0] + 0.5, (b[0] + b[1]) / 2, b[1] - 0.5):
        for ly in (b[2] + 0.5, (b[2] + b[3]) / 2, b[3] - 0.5):
            wz = water_z(lx)
            zb = min(ground_z(lx, ly), wz - 0.1) - 0.45
            if b[4] - zb > 0.7 and not over_walk(lx, ly, b[4] - 0.2, pad=0.16):
                legs.append(cyl("lg", (lx, ly, zb), (lx, ly, b[4] + 0.10), 0.15, 7,
                                MWET if zb < wz else MTD, COLL))
    join_meshes(legs, "lf_shack_piles", COLL)
    # a lean-to store, because the blockout shell was bigger than the kit prop
    staging("lf_stage_shack", b[0] + 0.30, b[0] + 3.90, 19.30, 20.90, 1.86,
            ang=math.radians(0))
    log("BUILD", "lf_shack_piles / lf_stage_shack", "%d legs to the strand and the bed, "
        "plus the drying stage the plan asked for where the blockout was bigger than "
        "the kit prop" % len(legs))

    # ---- the Moorage: a working landing, not just a disc ------------------
    # `walk_lm_moorage` is a FILLED disc (manifest 35), so everything the moorage
    # WORKS with has to stand off it — on staging outside the corridor.
    staging("lf_stage_moorage", 72.60, 79.60, 31.30, 33.30, 1.02, ang=math.radians(0))
    staging("lf_stage_moorage_w", 70.90, 72.60, 26.20, 29.40, 1.06, ang=math.radians(90))
    mp = 0
    for px, py in ((72.9, 32.0), (76.1, 32.0), (79.3, 32.0), (73.6, 33.1), (78.6, 33.1)):
        if spot(px, py, 0.36):
            kp("lf_mooring_post", (px, py, 1.02), cname=COLL + "_PROPS")
            mp += 1
    for px, py in ((73.4, 31.5), (76.1, 31.5), (78.8, 31.5)):
        if spot(px, py, 0.30):
            kp("lf_cleat", (px, py, 1.14), rz=math.pi / 2, cname=COLL + "_PROPS")
    log("BUILD", "lf_stage_moorage*", "the moorage's landing stage on the river lip and a "
        "west store bench, %d mooring posts + 3 cleats, all outside the filled disc" % mp)


# ===========================================================================
# 5. DAM FIVE — the hero.  Black stone, three true-scale wheels, closed crest.
# ===========================================================================
BAY_PITCH = 3.90
BAY_ORIGIN_Z = 0.78                  # the kit crest deck sits +0.12 -> z 0.90
DAM_Y0 = 31.40                       # the lock's north wall
N_BAYS = 11
WHEEL_BAYS = (0, 4, 8)

if "dam" in DO:
    kill(["dam_dam-five_wall", "dam_dam-five_crest", "dam_dam-five_foam",
          "dam_dam-five_wheel0", "dam_dam-five_wheel1", "dam_dam-five_wheel2",
          "lm_dam-crest-gate_postL", "lm_dam-crest-gate_postR",
          "lm_dam-crest-gate_lintel"],
         "the dam-five blockout (95 blocked + 69 headroom samples of the baseline) "
         "replaced with a run of kit bays")

    crest_ys, spill_ys = [], []
    for k in range(N_BAYS):
        y0 = DAM_Y0 + k * BAY_PITCH
        if k % 2 == 0:
            remap(kp("lf_crest_bay", (86.00, y0 + BAY_PITCH / 2, BAY_ORIGIN_Z - 5.20),
                     oname="lf_crest_bay_%02d" % k, cname=COLL + "_DAM"), DAM_MATS)
            crest_ys.append(y0 + BAY_PITCH / 2)
        else:
            remap(kp("lf_spill_bay", (86.00, y0 + BAY_PITCH / 2, BAY_ORIGIN_Z - 5.20),
                     oname="lf_spill_bay_%02d" % k, cname=COLL + "_DAM"), DAM_MATS)
            spill_ys.append(y0 + BAY_PITCH / 2)
    log("BUILD", "dam-five: %d bays" % N_BAYS, "%d crest piers + %d spill bays alternating "
        "at %.2f m pitch from y=%.1f to y=%.1f — a run of REPEATS (manifest 61), not %d "
        "modelled bays" % (len(crest_ys), len(spill_ys), BAY_PITCH, DAM_Y0,
                           DAM_Y0 + N_BAYS * BAY_PITCH, N_BAYS))

    # ---- the three wheels, at TRUE scale against the ruling's 4.0 m head ---
    # head 0.20, tail -3.80.  A 4.4 m breast wheel centred at z -1.55 takes water
    # just under the crest and clears the tail bed — which is the whole reason
    # the user deepened the drop.
    WHEEL_Z = -1.55
    wn = 0
    for k in WHEEL_BAYS:
        wy = DAM_Y0 + k * BAY_PITCH + BAY_PITCH / 2
        remap(kp("lf_wheel_breast", (90.00, wy, WHEEL_Z), rz=math.pi / 2, mode="cxy_cz",
                 oname="lf_wheel_%d" % wn, cname=COLL + "_DAM"), WHEEL_MATS)
        for sgn in (1, -1):
            remap(kp("lf_wheel_bearing", (90.00, wy + 1.55 * sgn, WHEEL_Z + 0.30),
                     rz=math.pi / 2 if sgn > 0 else -math.pi / 2, mode="cxy_maxz",
                     oname="lf_wheel_%d_brg%d" % (wn, 0 if sgn > 0 else 1),
                     cname=COLL + "_DAM"), WHEEL_MATS)
        wn += 1
    log("BUILD", "lf_wheel_0..2 + 6 bearings", "4.4 m lf_wheel_breast on piers %s, axle "
        "z %.2f: the wheel spans z %.2f..%.2f against a head of %.1f and a tail of %.1f — "
        "true scale, per the user's 1.8 -> 4.0 drop ruling"
        % (WHEEL_BAYS, WHEEL_Z, WHEEL_Z - 2.26, WHEEL_Z + 2.26, WATER_MID, WATER_TAIL))

    # ---- the tail race the new drop exposes -------------------------------
    # finding 86: the boil BREAKS the surface, it is not a slab laid on it.
    boils = []
    for wy in spill_ys:
        for i in range(4):
            bx = 89.4 + i * 0.85 + rng.random() * 0.25
            by = wy - 1.35 + i * 0.9
            w = 0.75 + rng.random() * 0.5
            boils.append(obox("bo", bx, by, WATER_TAIL - 0.10, w, w * 1.5,
                              0.30 + rng.random() * 0.16, rz=rng.random() * 0.8,
                              mat=MBOIL, cname=COLL + "_DAM"))
    join_meshes(boils, "lf_dam_boil", COLL + "_DAM")
    log("BUILD", "lf_dam_boil", "%d low wedges breaking the tail surface under the spill "
        "bays — tops barely proud, knocked off white so the boil is the brightest thing "
        "in the BAY and not in the frame" % len(boils))

    # ---- abutment + the toe of the far bank at the LOCAL pool level -------
    # manifest 60: two pools either side of this dam, so the toe has two lips.
    box("lf_dam_abut_s", 84.00, 89.20, 29.80, DAM_Y0 + 0.20, -4.60, BAY_ORIGIN_Z + 0.12,
        MBLACK, COLL + "_DAM")
    box("lf_dam_abut_n", 84.00, 89.20, DAM_Y0 + N_BAYS * BAY_PITCH - 0.20, 76.00,
        -4.60, BAY_ORIGIN_Z + 0.12, MBLACK, COLL + "_DAM")
    box("lf_farbank_tail", 89.20, 131.00, 71.00, 79.00, BED_TAIL, -1.10,
        MROCK, COLL + "_DAM")
    log("BUILD", "lf_dam_abut_s/n + lf_farbank_tail", "the dam lands on black abutments at "
        "both banks, and the far bank keeps a toe below the tail pool's NEW -3.80 lip "
        "(manifest 60: moving a waterline leaves a hole)")

    # ---- the closed crest gate -------------------------------------------
    remap(kp("lf_crest_gate", (87.00, 30.30, 0.90), oname="lf_crest_gate",
             cname=COLL + "_DAM"), GATE_MATS)
    log("BUILD", "lf_crest_gate", "closed, chained, 'not kept' board — the map's crossing "
        "is state:closed and says no detail beyond the gate")


# ===========================================================================
# 6. BOATS
# ===========================================================================
if "boats" in DO:
    # The tar-dark story boat is a SHARED library asset built separately; the
    # kit barge stands in at the Moorage so the berth is not empty and the
    # composition is already correct when the real hull arrives.
    bg = kp("lf_barge", (76.10, 34.60, WATER_MID + 0.10), rz=math.pi / 2,
            oname="lf_barge_moorage", cname=COLL + "_PROPS")
    log("PLACE", "lf_barge_moorage", "MOORING PLACEHOLDER for the tar-dark story boat "
        "(ruled a shared library asset) — floor above the water plane, manifest 77")
    for i, (bx, by) in enumerate(((80.60, 37.80), (72.20, 38.60))):
        kp("lf_barge", (bx, by, WATER_MID + 0.10), rz=math.pi / 2 + 0.22 * (1 - 2 * i),
           oname="lf_barge_pool_%d" % i, cname=COLL + "_PROPS")
        kp("lf_cargo_stack", (bx + 1.1 * (1 - 2 * i), by + 0.1, WATER_MID + 0.68),
           rz=0.4 * i, oname="lf_barge_load_%d" % i, cname=COLL + "_PROPS")
    log("PLACE", "lf_barge_pool_0/1", "flat cargo hulls with pumpkin/crate loads in the "
        "calm pool above the dam — the map's own motif")


# ===========================================================================
# 7. DRESSING
# ===========================================================================
if "dress" in DO:
    # ---- bunting.  RULING: it anchors to the dam's own crest posts, not the
    # far wall (a 48 m swag would need a mast on pure backdrop).
    PARAPET_Z = BAY_ORIGIN_Z + 0.86
    sw = 0
    for k in (0, 2, 4, 6):
        y0 = DAM_Y0 + k * BAY_PITCH + BAY_PITCH / 2
        kp("lf_bunting_swag", (86.10, y0, PARAPET_Z), rz=math.pi / 2,
           mode="cxy_maxz", oname="lf_bunting_%d" % sw, cname=COLL + "_PROPS")
        sw += 1
    log("BUILD", "lf_bunting_0..%d" % (sw - 1), "%d nine-metre swags along the crest, "
        "anchored crest post to crest post (coordinator ruling) rather than to the far "
        "wall" % sw)

    # ---- ordinary warm hanging lanterns.  World canon: Heartlights do NOT
    # exist in Dellhollow; these are lamps on posts and they are lit.
    LANTERNS = [(67.60, 27.40), (71.80, 26.10), (75.30, 31.60), (79.40, 31.60),
                (83.10, 26.00), (85.20, 30.10), (89.60, 26.00), (93.40, 26.30),
                (97.20, 26.10)]
    def deck_below(x, y, zmax=4.0):
        """The district's OWN deck at (x, y).

        `Corridor.top_at` returns the HIGHEST walk face, which out here is
        regularly the Weave's elevated walkway 6 m overhead — the first pass
        stood a lantern post on `walk_lm_drying-decks` and the audit called it a
        stray hanging 4.88 m over the ground, correctly."""
        best = None
        for poly, fn, raw, nm in COR0.tops:
            if point_in_poly(x, y, poly):
                z = fn(x, y)
                if z <= zmax and (best is None or z > best):
                    best = z
        return best

    lit = 0
    for lx, ly in LANTERNS:
        gz = deck_below(lx, ly)
        base = gz if gz is not None else ground_z(lx, ly)
        pos = COR.find_free(lx, ly, base + 1.0, radius=2.0)
        if pos is None:
            continue
        px, py = pos
        if not spot(px, py, 0.55):
            continue
        kp("lf_lantern_post", (px, py, base - 0.05), rz=rng.random() * 3.1,
           oname="lf_lantern_%d" % lit, cname=COLL + "_PROPS")
        d = bpy.data.lights.new("lf_lantern_%d_light" % lit, 'POINT')
        d.energy, d.shadow_soft_size = 680.0, 0.10
        d.color = (1.0, 0.72, 0.42)
        d.use_custom_distance, d.cutoff_distance = True, 14.0
        ob = bpy.data.objects.new(d.name, d)
        ob.location = (px + 0.28, py, base + 2.10)
        link(ob, COLL + "_PROPS")
        lit += 1
    log("BUILD", "lf_lantern_0..%d" % (lit - 1), "%d ordinary warm post lanterns along the "
        "route (world canon: Heartlights do not exist in Dellhollow), each with a 680 W "
        "practical on the town's own value" % lit)

    # ---- rope, cargo and cleats on every deck, placed by Corridor search ---
    # A working surface is a KNOWN rectangle at a KNOWN height, and the strand is
    # a band of ground near the waterline.  Sampling "anywhere, then step off the
    # walk" placed 0 of 396: beside a boardwalk on piles there IS no ground, so
    # every candidate failed the ground test.  Same lesson as manifest 72, one
    # level up — give the placer a surface, not a search space.
    SURFACES = [(72.60, 79.60, 31.30, 33.30, 1.02),      # the moorage landing stage
                (70.90, 72.60, 26.20, 29.40, 1.06),      # its west store bench
                (67.66, 71.26, 19.30, 20.90, 1.86),      # the shack's drying stage
                (CH_X0 + 0.3, CH_X1 - 0.3, 24.75, y_s - 0.15, COPE_Z),   # south coping
                (CH_X0 + 0.3, CH_X1 - 0.3, y_n + 0.15, 31.25, COPE_Z)]   # north coping
    CLUT = [("lf_rope_coil", 9), ("lf_barrel", 8), ("lf_crate", 8), ("lf_cargo_stack", 4)]
    placed = tries = onstrand = 0
    for nm, n in CLUT:
        got = 0
        for _ in range(n * 40):
            if got >= n:
                break
            tries += 1
            if rng.random() < 0.62:
                sx0, sx1, sy0, sy1, sz = SURFACES[rng.randrange(len(SURFACES))]
                if sx1 - sx0 < 0.6 or sy1 - sy0 < 0.6:
                    continue
                px = sx0 + 0.30 + rng.random() * max(0.01, sx1 - sx0 - 0.60)
                py = sy0 + 0.30 + rng.random() * max(0.01, sy1 - sy0 - 0.60)
                pz = sz
            else:
                px = X0 + rng.random() * 32.0
                py = 18.0 + rng.random() * 8.0
                pz = ground_z(px, py)
                wz = water_z(px)
                sl = max(abs(ground_z(px + 0.4, py) - pz),
                         abs(ground_z(px, py + 0.4) - pz)) / 0.4
                if sl > 0.40 or pz < wz + 0.10 or pz > wz + 2.30:
                    continue
                onstrand += 1
            if not clear_box(px, py, pz, pz + 1.45, pad=0.62):
                continue
            if not spot(px, py, 1.35 if nm == "lf_cargo_stack" else 0.62):
                continue
            kp(nm, (px, py, pz - 0.03), rz=rng.random() * 6.28,
               oname="lf_clut_%d" % placed, cname=COLL + "_PROPS")
            placed += 1
            got += 1
    log("BUILD", "lf_clut_* x%d" % placed, "rope coils, barrels, crates and cargo stacks "
        "(%d of them on the strand, the rest on the staging and the lock coping), every "
        "one filtered out of the walking lines by over_walk (%d probes)" % (onstrand, tries))

    # ---- autumn planting on the rim, seated on the CREST function (f.71) ---
    veg = 0
    for _ in range(420):
        x = X0 + rng.random() * (X1 - X0 - 1.0)
        y = 13.0 + rng.random() * 8.0
        z = ground_z(x, y)
        # slope test: nothing stands on a 40 degree bank (manifest 72)
        s = max(abs(ground_z(x + 0.5, y) - z), abs(ground_z(x, y + 0.5) - z)) / 0.5
        if s > 0.55 or z < 3.0:
            continue
        r = 0.9 + rng.random() * 1.5
        h = 1.6 + rng.random() * 2.4
        if not clear_box(x, y, z, z + h * 1.35, pad=r + 0.40):
            continue
        parts = []
        MLEAF = M("mat_leaf_autumn")
        for k in range(3):
            zc = z + h * (0.42 + 0.24 * k)
            rr = r * (1.02 - 0.22 * k)
            dx, dy = (rng.random() - .5) * r * 0.5, (rng.random() - .5) * r * 0.5
            parts.append(cyl("cl", (x + dx, y + dy, zc - h * 0.20),
                             (x + dx * 1.4, y + dy * 1.4, zc + h * 0.24),
                             rr, 9, MLEAF, COLL + "_VEG", r2=rr * 0.55))
        parts.append(cyl("tr", (x, y, z - 0.2), (x, y, z + h * 0.52), 0.14, 6, MTD,
                         COLL + "_VEG"))
        join_meshes(parts, "veg_lf_rimclump_%d" % veg, COLL + "_VEG")
        veg += 1
        if veg >= 46:
            break
    # ferns and tufts on the strand, which is the reason the strand exists
    tuft = 0
    for _ in range(600):
        x = X0 + rng.random() * (X1 - X0 - 1.0)
        y = 18.0 + rng.random() * 8.0
        z = ground_z(x, y)
        s = max(abs(ground_z(x + 0.4, y) - z), abs(ground_z(x, y + 0.4) - z)) / 0.4
        if s > 0.42 or z < water_z(x) + 0.15 or z > water_z(x) + 2.6:
            continue
        r = 0.30 + rng.random() * 0.42
        if not clear_box(x, y, z, z + r * 1.4, pad=r + 0.35):
            continue
        obox("veg_lf_fern_%d" % tuft, x, y, z + r * 0.55, r * 2.0, r * 1.7, r * 1.2,
             rz=rng.random() * 3.0, mat=MFERN if tuft % 2 else MGRASS, cname=COLL + "_VEG")
        tuft += 1
        if tuft >= 78:
            break
    # runtime canon (commit 5e2d7fc): `veg_` is the NO-STAND prefix — without it
    # a tree canopy is climbable terrain.  `lf_` alone is standable.
    log("BUILD", "veg_lf_rimclump_* x%d, veg_lf_fern_* x%d" % (veg, tuft),
        "autumn canopy masses on the rim and planting on the 2.3 m strand — with the "
        "slope test, the strand is what lets anything stand at all (manifest 72)")


# The donors are a pile of kit geometry standing at the world ORIGIN — which is
# inside the Boatyard.  `hide_render` keeps them out of a render but not out of a
# glTF export, so they are removed once the last kp() has copied from them.
n_src = 0
for o in list(bpy.data.objects):
    if o.name.startswith("KITSRC_"):
        bpy.data.objects.remove(o, do_unlink=True)
        n_src += 1
c = bpy.data.collections.get("LF_KITSRC")
if c is not None:
    bpy.data.collections.remove(c)
if n_src:
    log("CLEAN", "%d kit donors removed" % n_src,
        "appended read-only from the kit, copied from, then deleted — nothing of "
        "the kit library itself is left standing at the origin")

if "ground" in DO:
    ground_report()

print("\n" + "=" * 78)
print("LOCKSFOOT BUILD (%s): %d log lines" % (",".join(sorted(DO)), len(LOG)))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
