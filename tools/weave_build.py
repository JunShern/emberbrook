"""weave_build.py — detail the WEAVE (mid tier) IN THE MASTER.

  Blender -b tools/blends/dellhollow-master.blend -P tools/weave_build.py -- <phase> [save]

  phase: deck | huts | cottage | ladder | dress | landing | all   (comma-separated)

JURISDICTION (coordinator, 2026-07-29)
--------------------------------------
p-westweave  x 43.7..52.7   Westweave cluster (weave-north)
p-weave      x 54.6..76.0   pilot cluster (ADOPT the pilot slice), weave huts,
                            drying decks
p-cottage    x 88.1..97.1   the Keepers' Cottage (kit asset, appended read-only)
ALSO, by explicit assignment from the Locksfoot handover: the undecked
weave-owned ribbons hanging over the Moorage —
`walk_e_weave-huts__moorage_l0/l1` and `walk_lm_drying-decks` — flagged as the
single biggest visual gap in the region.
ALSO, by user extension mid-pass: p-northlanding x 101.2..110.2, the North
Landing pier (prefix `nl_`, so it stays separable from the tier).

NOT MINE and untouched: p-lockhead, p-quay-mkt, p-lockfive, p-waterfront,
p-boatyard, and the gate branch.  `p-crossing` (the plank bridge, x 71.5..92.5)
is an unassigned TRANSIT parcel whose two ends are both mine — see the note at
the bridge, where the scope call is made explicitly.

CONTRACT
--------
* `walk_*` / `bar_*` are canonical topology: never moved, never edited.  A
  ribbon this pass decks over gets `hide_render = True` and nothing else
  (manifest 51) — `hide_viewport` would drop it from the glTF and the runtime
  would lose its collision.
* Everything built here is `wv_` (`nl_` at the North Landing), foliage is
  `veg_wv_` / `veg_nl_` (the runtime no-stand prefix), in `DIST_weave*`.
* MATERIALS: kit materials only, and every object goes through
  `weave_lib.finish()` so it carries `Col` + `UVMap`.  Nothing procedural may
  reach an exported object — see weave_lib's header for why.
* Props go through the walk Corridor, tall things through `clear_box`
  (finding 113), and everything through one shared occupancy list (finding 114).
"""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          world_bbox, plank_fill, offset_poly, plane_z_fn, point_in_poly,
                          clip_halfplane, Corridor, place)
from weave_lib import MAT, PAL, finish, audit_gltf_safe

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PHASES = ["deck", "huts", "cottage", "ladder", "dress", "landing"]
want = argv[0] if argv and not argv[0] == "save" else "all"
DO = set(want.split(","))
if "all" in DO or not DO & set(PHASES):
    DO |= set(PHASES)
SAVE = "save" in argv
rng = random.Random(20260801)
COLL = "DIST_weave"
KIT = REPO + "/tools/blends/districts/locksfoot-kit.blend"

WATER_MID = 0.20
WATER_TAIL = -2.80          # the SAVED value; the map says -3.80 — see the report
DECK_DROP = 0.085           # the district's deck sits under the walk top
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-34s %s" % (kind, what, why))


for c in (COLL, COLL + "_DECK", COLL + "_BUILD", COLL + "_PROPS", COLL + "_VEG"):
    coll(c)

# ------------------------------------------------------------------ materials
MMATTE, MDECK, MSTONE = MAT("lf_matte"), MAT("lf_deck"), MAT("lf_stone")
MSHINGLE, MIRON, MGLASS = MAT("lf_shingle"), MAT("lf_iron"), MAT("lf_glass")

# The default tint table: what each kit slot means when this district uses it.
T = {"lf_matte": PAL["timber"], "lf_deck": PAL["deck"], "lf_stone": PAL["stonegrey"],
     "lf_shingle": PAL["shingle"], "lf_iron": PAL["iron"], "lf_glass": PAL["glass"]}


def T_(**kw):
    """A tint table with overrides, e.g. T_(lf_matte=PAL['oxblood'])."""
    d = dict(T)
    d.update({k: v for k, v in kw.items()})
    return d


# ------------------------------------------------------------------ clean-up
# finding 117: match the PREFIX, and clear the orphaned DATA too.  A suffix match
# ("_light", "_body") is what let eight rebuilds stack 45 practicals.
killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("wv_", "nl_", "veg_wv_", "veg_nl_", "WVKITSRC_")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
for me in list(bpy.data.meshes):
    if me.name.startswith(("wv_", "nl_", "veg_wv_", "veg_nl_", "WVKITSRC_")) and me.users == 0:
        bpy.data.meshes.remove(me)
if killed:
    log("REBUILD", "%d wv_/nl_ objects cleared" % killed, "previous pass removed first")

# ------------------------------------------------------------------ corridors
WALKS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
BARS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("bar_")]
COR0 = Corridor(WALKS, margin=0.0)
COR = Corridor(WALKS, margin=0.30)
# `bar_*` rails ARE canonical topology (the map owns them) and master_walk_qa
# casts a down-ray over every one of their top faces too.  Leaving them out of
# the corridor is what let a hut roof sit 0.40 m above a stair rail and the
# cottage clip the Lockhead path's guard.  A rail's band is shallower than a
# walk's, though: the QA's ray starts 0.90 m above the surface, so only that
# 0.90 m has to be kept clear over a rail top, not the full 2.05 m corridor.
CORB = Corridor(BARS, margin=0.26) if BARS else None
CORRIDOR_H = 2.05
BAR_H = 0.95


_OW = {}


def over_walk(x, y, z, pad=0.16):
    k = (round(x, 2), round(y, 2), round(z, 2), pad)
    if k in _OW:
        return _OW[k]
    r = False
    for dx, dy in ((0, 0), (pad, 0), (-pad, 0), (0, pad), (0, -pad),
                   (pad * .7, pad * .7), (-pad * .7, pad * .7),
                   (pad * .7, -pad * .7), (-pad * .7, -pad * .7)):
        t = COR.top_at(x + dx, y + dy)
        if t is not None and t - 0.10 <= z <= t + CORRIDOR_H:
            r = True
            break
        if CORB is not None:
            tb = CORB.top_at(x + dx, y + dy)
            if tb is not None and tb - 0.10 <= z <= tb + BAR_H:
                r = True
                break
    _OW[k] = r
    return r


_CB = {}


def clear_box(x, y, z0, z1, pad=0.30):
    """finding 113: a tall object only has to touch the corridor once."""
    k = (round(x, 2), round(y, 2), round(z0, 2), round(z1, 2), pad)
    if k in _CB:
        return _CB[k]
    z = z0
    r = True
    while z <= z1 + 0.01:
        if over_walk(x, y, z, pad=pad):
            r = False
            break
        z += 0.35
    _CB[k] = r
    return r


def free_of_walk(x, y, z, band=0.60):
    """No walk surface within `band` metres of z, either way.

    `below_walk` answers "may a plank be laid here", and it tolerates a plank up
    to 0.16 m under a walk because that is how a district's decking meets its own
    ribbon.  For an APRON — planking OUTBOARD of the ribbon — and for a pile head
    or a rail post, that tolerance is wrong: laid 0.05 m under a walk at the same
    level, the apron comes out 0.01-0.05 m ABOVE it once the plank jitter is added
    and the walk's own down-ray lands on the apron.  That is 8 of the North
    Landing's samples and 2 more at the drying decks.  Outboard structure must
    either miss the walk entirely or clear it by a real margin.
    """
    t = COR0.top_at(x, y)
    return t is None or abs(t - z) > band


def ceiling_over(x, y, z, reach=14.0):
    """The lowest walk surface ABOVE a point — what a roof ridge has to duck.

    `walk_lm_quay-deck` runs at z 14.24 directly over Westweave, whose own parcel
    intent is "tucked under the quay's shadow ... stilts overhead".  A two-storey
    hut on a 10.25 floor puts its ridge at 15.8, straight up through the Quay, and
    nothing in the Corridor test catches it: that test asks whether a point is in
    a walking line, never what is above it.
    """
    lo = None
    for dx, dy in ((0, 0), (1.0, 0), (-1.0, 0), (0, 1.0), (0, -1.0)):
        t = COR0.top_at(x + dx, y + dy)
        if t is not None and t > z + 0.5 and (lo is None or t < lo):
            lo = t
    return lo if lo is None or lo < z + reach else None


OCCUPY = []


def spot(x, y, r):
    """finding 114: the Corridor keeps props out of walks, not out of EACH OTHER."""
    for ox, oy, orad in OCCUPY:
        if math.hypot(x - ox, y - oy) < (r + orad) * 0.92:
            return False
    OCCUPY.append((x, y, r))
    return True


# --------------------------------------------------------------------- ground
_DG = bpy.context.evaluated_depsgraph_get()
_SC = bpy.context.scene
_GCACHE = {}
GROUNDY = ("wf_ground", "lf_ground", "riverbed", "lf_riverbed_tail", "seam_bank",
           "yard_ground", "lf_farbank", "cliff_")


def ground_z(x, y, top=40.0):
    """The real ground under a point, found by RAY (finding 103), not assumed."""
    k = (round(x, 2), round(y, 2))
    if k in _GCACHE:
        return _GCACHE[k]
    org = Vector((x, y, top))
    d = Vector((0, 0, -1))
    z = -8.0
    for _ in range(40):
        hit, loc, n, i, ob, mw = _SC.ray_cast(_DG, org, d, distance=90)
        if not hit:
            break
        if ob.name.startswith(GROUNDY) or "ground" in ob.name or "riverbed" in ob.name:
            z = loc.z
            break
        org = loc + d * 0.02
    _GCACHE[k] = z
    return z


def water_z(x):
    return WATER_MID if x < 87.0 else WATER_TAIL


def first_solid_below(x, y, z0):
    """The first EXISTING solid under a point — ground, or a neighbour's deck.

    A stilt driven to `ground_z` is right in an empty gorge and wrong in a stacked
    town: at the weave huts, Locksfoot's `lf_stage_shack` deck sits at z 1.87 and
    a gallery post aimed at the rock 4 m lower drove straight through it (the
    audit's only interpenetration offender).  A post stops on the first thing it
    meets, which is also how a real post is built.
    """
    org = Vector((x, y, z0 - 0.05))
    d = Vector((0, 0, -1))
    for _ in range(30):
        hit, loc, n, i, ob, mw = _SC.ray_cast(_DG, org, d, distance=60)
        if not hit:
            return None
        if not ob.name.startswith(("walk_", "bar_", "wv_", "nl_", "veg_", "fx_")):
            return loc.z
        org = loc + d * 0.02
    return None


# ===========================================================================
# the kit, appended read-only  (manifest 4/31, and finding 119 for the donors)
# ===========================================================================
_KIT = {}


def kit_load(names):
    todo = [n for n in names if n not in _KIT]
    if not todo:
        return
    before = set(bpy.data.objects.keys())
    with bpy.data.libraries.load(KIT, link=False) as (src, dst):
        dst.objects = list([n for n in todo if n in src.objects])
        dst.materials = list([m for m in src.materials if m.startswith("lf_")])
    got = [o for o in bpy.data.objects if o.name not in before]
    hold = coll("WV_KITSRC")
    hold.hide_render = True
    for o in got:
        base = o.name.split(".")[0]
        if base in todo and base not in _KIT:
            _KIT[base] = o
            o.name = "WVKITSRC_" + base          # finding 119: donors stand at (0,0,0)
            if o.data:
                o.data.name = "WVKITSRC_" + base
        for c in list(o.users_collection):
            c.objects.unlink(o)
        hold.objects.link(o)
    # scope the texture remap to the maps the kit ships (finding 118)
    for im in list(bpy.data.images):
        b = os.path.basename(im.filepath) if im.filepath else ""
        if b not in ("weathered_planks_Diffuse.jpg", "old_stone_wall_02_Diffuse.jpg",
                     "red_slate_roof_tiles_01_Diffuse.jpg"):
            continue
        cand = os.path.join(REPO, "tools", "textures", b)
        if os.path.exists(cand):
            im.filepath = cand
        first = bpy.data.images.get(b)
        if first is not None and im is not first:
            im.user_remap(first)
            bpy.data.images.remove(im)
    # ...and to the MATERIALS, which is the leak that put 2000 datablocks in the
    # master before tools/master_mat_dedup.py caught it
    for m in list(bpy.data.materials):
        if m.name.startswith("lf_") and "." in m.name:
            canon = bpy.data.materials.get(m.name.split(".")[0])
            if canon is not None and canon is not m:
                m.user_remap(canon)
                bpy.data.materials.remove(m)
    for m in bpy.data.materials:
        m.use_fake_user = True


def kit_place(name, at, rz=0.0, cname=None, oname=None, mode="cxy_minz", scale=1.0):
    """Copy a kit assembly to a town position.  The kit is authored in town axes."""
    kit_load([name])
    src = _KIT[name]
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = oname or ("wv_" + name[3:] if name.startswith("lf_") else "wv_" + name)
    ob.data.name = ob.name
    c, s = math.cos(rz), math.sin(rz)
    for v in ob.data.vertices:
        p = src.matrix_basis @ v.co
        p = Vector((p.x * scale, p.y * scale, p.z * scale))
        v.co = Vector((p.x * c - p.y * s, p.x * s + p.y * c, p.z))
    ob.matrix_basis.identity()
    b = world_bbox(ob)
    cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
    if mode == "cxy_minz":
        ob.location = Vector((at[0] - cx, at[1] - cy, at[2] - b[4]))
    elif mode == "origin":
        ob.location = Vector(at)
    else:
        ob.location = Vector((at[0] - cx, at[1] - cy, at[2] - (b[4] + b[5]) / 2))
    link(ob, cname or (COLL + "_PROPS"))
    return ob


MADE = []           # everything this pass finishes, for the glTF audit


def done(ob, tints=None, jitter=0.06):
    if ob is None:
        return None
    finish(ob, tints or T, jitter=jitter)
    MADE.append(ob)
    return ob


# ===========================================================================
# 1. DECK — the ribbons this tier owns, and the stilt forest under them
# ===========================================================================
# The tier's own ribbons, plus the two the Locksfoot handover assigned by name.
# Everything already decked by the Waterfront or Locksfoot (hide_render == True)
# is skipped by construction — decking it twice is how you get z-fighting.
FLAT = [
    # -- p-westweave / p-weave: the plank walks between the clusters
    "walk_pad_weave-north", "walk_pad_pilot-cluster", "walk_pad_weave-huts",
    "walk_e_pilot-cluster__weave-north_l0", "walk_e_pilot-cluster__weave-north_l1",
    "walk_e_pilot-cluster__weave-huts_l0", "walk_e_pilot-cluster__weave-huts_l1",
    "walk_e_pilot-cluster__weave-huts_l2",
    "walk_e_weave-huts__drying-decks_l0", "walk_e_weave-huts__drying-decks_l1",
    "walk_lm_drying-decks",
    # -- the quay stair's landings (its treads are handled as stairs below)
    "walk_e_quay-deck__pilot-cluster_landing",
    "walk_e_quay-deck__pilot-cluster_landing.001",
    "walk_e_quay-deck__pilot-cluster_landing.002",
    # -- the Moorage ribbons: the Locksfoot handover's flagged gap
    "walk_e_weave-huts__moorage_landing", "walk_e_weave-huts__moorage_landing.001",
    # -- p-cottage
    "walk_pad_keepers-cottage", "walk_e_keepers-cottage__lock-five_landing",
    # -- the bridge (p-crossing, see the scope note)
    "walk_e_weave-huts__keepers-cottage_l0", "walk_e_weave-huts__keepers-cottage_l1",
    "walk_e_weave-huts__keepers-cottage_l2",
    # -- p-northlanding
    "walk_lm_north-landing", "walk_e_lock-five__north-landing_l1",
]
STAIRS = (["walk_e_quay-deck__pilot-cluster_l0_t00"]
          + ["walk_e_quay-deck__pilot-cluster_l1_t%02d" % i for i in range(6)]
          + ["walk_e_quay-deck__pilot-cluster_l2_t%02d" % i for i in range(5)]
          + ["walk_e_quay-deck__pilot-cluster_l3_t%02d" % i for i in range(3)]
          + ["walk_e_weave-huts__moorage_l0_t%02d" % i for i in range(6)]
          + ["walk_e_weave-huts__moorage_l1_t%02d" % i for i in range(6)]
          + ["walk_e_keepers-cottage__lock-five_l0_t%02d" % i for i in range(7)]
          + ["walk_e_keepers-cottage__lock-five_l1_t%02d" % i for i in range(5)])
# This pass OWNS the ribbons named above, so a previous run's `hide_render` is
# un-set before the list is built.  (Filtering on the flag instead made the
# second run deck nothing while the clear-out removed the first run's planks —
# 62 invisible, undecked ribbons.  Idempotency has to survive the flags a pass
# sets on objects it does not own.)
for _nm in FLAT + STAIRS:
    _o = bpy.data.objects.get(_nm)
    if _o is not None:
        _o.hide_render = False
FLAT = [n for n in FLAT if bpy.data.objects.get(n)]
STAIRS = [n for n in STAIRS if bpy.data.objects.get(n)]

PLANK_ANG = {}


def ribbon_angle(raw):
    xs = [v.x for v in raw]
    ys = [v.y for v in raw]
    return 0.0 if (max(xs) - min(xs)) >= (max(ys) - min(ys)) else math.pi / 2


def below_walk(px, py, pz):
    """A plank may only be laid where it is not under someone else's walk...

    ...and not OVER one either.  A flat ribbon's decking is generous (+0.36 m), so
    at the head of a flight it overhangs the tread below, and that tread's own
    down-ray then lands on the plank.  The ribbon this plank belongs to sits
    DECK_DROP above it; anything walkable in the metre beneath is someone else's
    surface.
    """
    t = COR0.top_at(px, py)
    if t is not None and t > pz + 0.16:
        return False
    if t is not None and pz - 1.05 < t < pz - 0.02:
        return False
    return not COR.blocked((px, py, pz))


if "deck" in DO:
    deck, joists, piles, treads, strings, bracing = [], [], [], [], [], []
    PILE_POS = []
    for nm in FLAT + STAIRS:
        ob = bpy.data.objects[nm]
        is_stair = nm in STAIRS
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
                continue                                   # buried face (manifest 36)
            poly = offset_poly(raw, -0.045 if is_stair else 0.36)
            zfn = plane_z_fn(raw)
            ang = PLANK_ANG.get(nm, ribbon_angle(raw))
            v, f = plank_fill(poly, ang, w=0.24 if is_stair else 0.27, gap=0.014,
                              thick=0.09 if is_stair else 0.11, jitter=0.011,
                              drop=DECK_DROP, zfn=zfn, seed=(hash(nm) + pi) & 0xffff,
                              keep=None if is_stair else
                              (lambda px, py, pz: below_walk(px, py, pz)))
            tgt = treads if is_stair else deck
            tgt.append(new_mesh("wv_d%d" % len(tgt), v, f, MDECK, COLL + "_DECK"))
            if is_stair:
                continue
            xs = [q.x for q in poly]
            ys = [q.y for q in poly]
            ax0, ax1, ay0, ay1 = min(xs), max(xs), min(ys), max(ys)
            long_x = (ax1 - ax0) >= (ay1 - ay0)
            u = (ax0 if long_x else ay0) + 0.4
            lim = (ax1 if long_x else ay1) - 0.35
            while u <= lim:                                 # joists
                if long_x:
                    seg = clip_halfplane(clip_halfplane(poly, 1, 0, u + 0.09), -1, 0, -(u - 0.09))
                else:
                    seg = clip_halfplane(clip_halfplane(poly, 0, 1, u + 0.09), 0, -1, -(u - 0.09))
                if len(seg) >= 3:
                    w = [q.y for q in seg] if long_x else [q.x for q in seg]
                    pa = (u, min(w)) if long_x else (min(w), u)
                    pb = (u, max(w)) if long_x else (max(w), u)
                    mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                    if all(below_walk(q[0], q[1], zfn(q[0], q[1]) - 0.19)
                           for q in (pa, pb, mid)):
                        joists.append(beam("jo", (pa[0], pa[1], zfn(*pa) - 0.28),
                                           (pb[0], pb[1], zfn(*pb) - 0.28), 0.13, 0.18,
                                           MDECK, COLL + "_DECK"))
                u += 0.95
            gx = ax0 + 0.6                                  # piles
            while gx < ax1 - 0.4:
                gy = ay0 + 0.6
                while gy < ay1 - 0.4:
                    if point_in_poly(gx, gy, poly) and below_walk(gx, gy, zfn(gx, gy) - 0.30):
                        zt = zfn(gx, gy) - 0.30
                        wz = water_z(gx)
                        zb = min(ground_z(gx, gy), wz - 0.1) - 0.40
                        # a pile descends THROUGH whatever is below it: the
                        # weave-huts ribbons stand 1 m over the drying decks and
                        # their piles came down inside that disc
                        if zt - zb > 0.9 and free_of_walk(gx, gy, zt, band=0.55) is not False \
                                and not any(over_walk(gx, gy, zt - k * 0.5, pad=0.14)
                                            for k in range(1, int((zt - zb) / 0.5) + 1)):
                            piles.append(cyl("pl", (gx, gy, zb), (gx, gy, zt),
                                             0.150 + rng.random() * 0.055, 7,
                                             MDECK, COLL + "_DECK"))
                            PILE_POS.append((gx, gy, zb, zt))
                    gy += 1.25
                gx += 1.25

    # A 10 m stilt is a POLE; a braced one is a building.  The Weave's whole
    # silhouette from the Waterfront is this lattice, so it gets two bands of
    # bracing rather than the Waterfront's one — the reach is three times longer.
    for i, (x1, y1, zb1, zt1) in enumerate(PILE_POS):
        for x2, y2, zb2, zt2 in PILE_POS[i + 1:]:
            d = math.hypot(x2 - x1, y2 - y1)
            if not (1.1 < d < 2.3):
                continue
            span = min(zt1, zt2) - max(zb1, zb2)
            bands = 2 if span > 5.5 else 1
            for k in range(bands):
                zt = min(zt1, zt2) - 0.55 - k * (span / bands)
                zb = max(zt - min(2.8, span / bands), max(zb1, zb2) + 0.35)
                if zt - zb > 0.5:
                    bracing.append(beam("br", (x1, y1, zb), (x2, y2, zt), 0.09, 0.13,
                                        MDECK, COLL + "_DECK"))
                    bracing.append(beam("br", (x1, y1, zt), (x2, y2, zb), 0.09, 0.13,
                                        MDECK, COLL + "_DECK"))

    # ---- APRONS.  A filled landmark disc is corridor all the way to its rim
    #      (manifest 35), so a district that only decks the ribbon has nowhere to
    #      put a barrel: every point of its own decking is inside a walking line.
    #      The drying decks and the North Landing are both working platforms that
    #      would really be bigger than their standing pad, so each gets a planked
    #      annulus outboard of the walk.  That band is what carries the dressing.
    def apron(cx, cy, r0, r1, z, tag, nseg=40, nrad=4):
        made = []
        for k in range(nseg):
            t0, t1 = 2 * math.pi * k / nseg, 2 * math.pi * (k + 1) / nseg
            for j in range(nrad):
                a = r0 + (r1 - r0) * j / nrad
                b = r0 + (r1 - r0) * (j + 1) / nrad
                q = [(cx + math.cos(t) * rr, cy + math.sin(t) * rr)
                     for t, rr in ((t0, a), (t1, a), (t1, b), (t0, b))]
                mid = (sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4)
                if not all(free_of_walk(px, py, z) for px, py in q + [mid]):
                    continue
                if ground_z(mid[0], mid[1]) > z - 0.35:
                    continue                       # it is standing on rock, not air
                made.append(new_mesh("ap", [(x, y, z - 0.13) for x, y in q]
                                     + [(x, y, z - 0.02) for x, y in q],
                                     [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                                      (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
                                     MDECK, COLL + "_DECK"))
        # the apron needs its own legs or it is a floating skirt
        for k in range(10):
            th = 2 * math.pi * k / 10 + 0.15
            px, py = cx + math.cos(th) * (r1 - 0.25), cy + math.sin(th) * (r1 - 0.25)
            if not free_of_walk(px, py, z) or not clear_box(px, py, z - 0.30, z, pad=0.16):
                continue
            zb = min(ground_z(px, py), water_z(px) - 0.1) - 0.35
            if z - zb > 0.9:
                made.append(cyl("al", (px, py, zb), (px, py, z - 0.16), 0.15, 7,
                                MDECK, COLL + "_DECK"))
        return made

    dd = bpy.data.objects.get("walk_lm_drying-decks")
    if dd is not None:
        bb = world_bbox(dd)
        deck += apron((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2,
                      (bb[1] - bb[0]) / 2 - 0.15, (bb[1] - bb[0]) / 2 + 1.55,
                      bb[5] - DECK_DROP, "drying")

    done(join_meshes(deck, "wv_planking", COLL + "_DECK"), T_(lf_deck=PAL["deck"]))
    done(join_meshes(joists, "wv_joists", COLL + "_DECK"), T_(lf_deck=PAL["timberdk"]))
    done(join_meshes(piles, "wv_piles", COLL + "_DECK"), T_(lf_deck=PAL["timber"]), jitter=0.10)
    done(join_meshes(bracing, "wv_pile_bracing", COLL + "_DECK"), T_(lf_deck=PAL["timberdk"]))
    done(join_meshes(treads, "wv_stair_treads", COLL + "_DECK"), T_(lf_deck=PAL["deck"]))
    log("BUILD", "wv_planking / joists / piles / bracing",
        "%d flat ribbons decked, %d stair treads, %d piles driven to the ground or "
        "the bed, %d braces" % (len(FLAT), len(STAIRS), len(piles), len(bracing)))

    # ---- guards on the gorge lip, placed by SEARCH (finding 76) -----------
    def rail_run(pts, h=1.02):
        parts = []
        pts = [p for p in pts if clear_box(p[0], p[1], p[2] - 0.10, p[2] + h, pad=0.14)]
        for x, y, z in pts:
            parts.append(obox("rp", x, y, z - 0.30 + (h + 0.32) / 2, 0.11, 0.11, h + 0.32,
                              rz=rng.random() * 0.2, mat=MDECK, cname=COLL + "_DECK"))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if math.hypot(b[0] - a[0], b[1] - a[1]) > 3.2:
                continue
            # finding 97: anything that SPANS between two tested points has to be
            # tested at its midpoint too
            mx, my, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2
            if not clear_box(mx, my, mz - 0.10, mz + h, pad=0.14):
                continue
            for dz, sec in ((h, (0.09, 0.10)), (h * 0.55, (0.07, 0.07))):
                parts.append(beam("rr", (a[0], a[1], a[2] + dz), (b[0], b[1], b[2] + dz),
                                  sec[0], sec[1], MDECK, COLL + "_DECK"))
        return parts

    def outer_edge(x, ylo, yhi, out=0.30):
        y, z = yhi, None
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
        return (x, py, z)

    rails = []
    for x0r, x1r, ylo, yhi, stp in ((44.0, 52.4, 18.0, 23.5, 1.65),
                                    (54.6, 63.6, 19.5, 25.0, 1.65),
                                    (64.0, 69.0, 22.0, 27.0, 1.55),
                                    (67.4, 75.0, 22.0, 28.0, 1.60),
                                    (72.2, 91.6, 21.5, 24.2, 1.90),
                                    (101.6, 110.0, 24.5, 30.4, 1.70)):
        pts = []
        x = x0r
        while x <= x1r:
            e = outer_edge(x, ylo, yhi)
            if e:
                pts.append(e)
            x += stp
        rails += rail_run(pts)
    done(join_meshes(rails, "wv_railings", COLL + "_DECK"), T_(lf_deck=PAL["timber"]))
    log("BUILD", "wv_railings", "guards along the gorge lip of every deck this tier "
        "owns — each post set outboard by search, none in a walking line")

    hid = 0
    for nm in FLAT + STAIRS:
        o = bpy.data.objects.get(nm)
        if o is not None and not o.hide_render:
            o.hide_render = True
            hid += 1
    log("HIDE", "%d walk ribbons render-hidden" % hid,
        "hide_render only — hide_viewport drops them from the glTF and the runtime "
        "loses its collision (manifest 51)")


# ===========================================================================
# 2. HOUSES — architecture that STRADDLES THE CLIFF
# ===========================================================================
# ART DIRECTION (user, 2026-07-29, reviewing v1 live in townwalk): the first
# pass read as "houses floating in mid-air on forests of stilts", and the user
# called it ugly.  The correction is structural, not cosmetic:
#   * house mass moves CLIFFWARD (toward low y), onto the terrain;
#   * foundations are cut into the rock — a masonry undercroft that follows the
#     real ground, so the weight visibly rests on something;
#   * buildings step DOWN the fall in half-levels instead of sitting on one plate;
#   * stilts survive only as an accent under the river-facing edge;
#   * river-facing space becomes a light GALLERY / drying deck, not a dwelling
#     hanging in air;
#   * form grew to meet the terrain: offset floor plates, ridges that step and
#     change direction, lean-to additions, party walls shared with the rock.
#
# The terrain makes this possible and the numbers are worth recording, because
# they are why the first pass went wrong.  Measured (`ground_z` on a 1 m grid,
# x 43..78): the cliff falls ~2.5 m per metre of y between y=17 and y=19 and then
# flattens to z~1.0 out at y>=21.  Every walk_pad_* in this tier sits on that
# FLAT part — 6 to 8 m above the rock — while the rock reaches the pad's own
# height only 2 to 7 m inland:
#     walk_pad_weave-north   z 10.25 at y 18.7..21.3   rock hits 10.25 at y~16.5
#     walk_pad_pilot-cluster z  9.00 at y 20.7..23.3   rock hits  9.00 at y~16.4
#     walk_pad_weave-huts    z  7.83 at y 22.7..25.3   rock hits  7.83 at y~16.3
# So a house AT its pad has to float, and a house 3-7 m inland of its pad sits on
# rock — with a gallery spanning the difference.  That is the whole design.
HOUSE_MIN_Y = 15.4          # do not push mass further into the cliff than this

# Neighbouring districts' STRUCTURES, declared as explicit rectangles.  A house
# whose plan overlaps one of these cannot be fixed by adjusting how deep its
# undercroft goes — that only made the masonry WRAP Locksfoot's tenant-shack
# stage instead of passing through it.  Measured off the saved file, not guessed
# (manifest 96: one rectangle per structure, never a joined mesh's bounding box).
NEIGHBOUR_KEEPOUT = [
    (67.5, 71.4, 19.1, 21.1),      # lf_stage_shack  (+ lf_shack_piles under it)
    (70.8, 72.7, 26.1, 29.5),      # lf_stage_moorage_w
    (72.5, 79.7, 31.2, 33.4),      # lf_stage_moorage
]


def hits_keepout(x0, x1, y0, y1):
    for kx0, kx1, ky0, ky1 in NEIGHBOUR_KEEPOUT:
        if x1 > kx0 and x0 < kx1 and y1 > ky0 and y0 < ky1:
            return True
    return False


def rock_seat(x, floor, y_hi, y_lo=HOUSE_MIN_Y, drop=1.6):
    """March inland from `y_hi` to the y where the rock is `drop` under `floor`.

    This is the contour the back of a house sits on.  Returns None if the rock
    never comes up — which would mean the site really is a void and the steer
    cannot be honoured there.
    """
    y = y_hi
    while y > y_lo:
        if ground_z(x, y) >= floor - drop:
            return y
        y -= 0.25
    return None


GALLERY_AT = []          # (x0, x1, y, z) of every gallery, for the dressing


def cliff_house(name, ax0, floor, pad, wall_col, seed=0, width=4.2, xlim=None):
    """One Weave house: undercroft in the rock, stepped half-levels, a gallery.

    `pad` is the walk pad this dwelling must still serve; the gallery reaches
    back to it, which is the steer's hard constraint.  When the seat directly
    inland of `ax0` is occupied, the house SLIDES ALONG THE CONTOUR rather than
    out over the void — the tier's walk network crosses the inland space in
    several places (the Quay's switchback, the inter-cluster plank walks) and
    stepping sideways keeps the mass on rock, which is the whole steer.
    """
    for _dx in (0.0, 0.8, -0.8, 1.6, -1.6, 2.4, -2.4, 3.2, -3.2):
        ax = ax0 + _dx
        if xlim and not (xlim[0] - 0.4 <= ax <= xlim[1] + 0.4):
            continue
        ob = _cliff_house_at(name, ax, floor, pad, wall_col, seed, width)
        if ob is not None:
            if _dx:
                print("      (%s slid %+.1f m along the contour to find rock)"
                      % (name, _dx))
            return ob
    print("      !! %s: no seat on the rock anywhere along its contour — SKIPPED"
          % name)
    return None


def _cliff_house_at(name, ax, floor, pad, wall_col, seed=0, width=4.2):
    R = random.Random(seed)
    P = []
    W = width
    hw = W / 2.0

    def gmin(x0, x1, y0, y1, n=3):
        return min(ground_z(x0 + (x1 - x0) * i / (n - 1.0), y0 + (y1 - y0) * j / (n - 1.0))
                   for i in range(n) for j in range(n))

    # ---- 1. where the rock is ------------------------------------------------
    y_back = rock_seat(ax, floor, pad[1] - 0.6)
    if y_back is None:
        return None
    y_back = max(y_back - 0.9, HOUSE_MIN_Y)      # bury the back wall IN the rock

    # ---- 2. the volumes, stepping down the fall -----------------------------
    # depth and half-level drop vary per house so a cluster is not a repeat
    d0 = 3.0 + R.random() * 0.9
    d1 = 2.4 + R.random() * 0.9
    step = 0.95 + R.random() * 0.55
    vols = [dict(y0=y_back, y1=y_back + d0, z=floor, w=W,
                 xo=0.0, ridge='x', h=2.45 + R.random() * 0.35),
            dict(y0=y_back + d0 - 0.35, y1=y_back + d0 - 0.35 + d1,
                 z=floor - step, w=W * (0.80 + R.random() * 0.16),
                 xo=(R.random() - 0.5) * 1.5, ridge='y', h=2.25 + R.random() * 0.3)]
    # a lean-to on one gable of the upper block, lower ridge, its own direction
    lean = R.random() < 0.75
    lsgn = R.choice((-1, 1))

    def fit(x0, x1, y0, y1, zf, top, y0_max, min_d=1.50, min_w=2.20):
        """Pull a volume back off the walking lines instead of abandoning it.

        The tier's walk network runs along y 20..23 — exactly where a house's
        second half-level wants to be — so a volume tested all-or-nothing is
        rejected every time, which is what made the first run of this builder
        skip all nine houses.  March the river edge back, then the inland edge
        forward, then narrow, and only give up when there is genuinely nothing.
        """
        def bad(px, py):
            return not clear_box(px, py, zf - 0.1, top, pad=0.18)
        for _ in range(30):
            xs = (x0 + 0.15, (x0 + x1) / 2, x1 - 0.15)
            ym = (y0 + y1) / 2
            ys = (y0 + 0.15, ym, y1 - 0.15)
            hi = any(bad(px, py) for px in xs for py in ys if py > ym)
            lo = any(bad(px, py) for px in xs for py in ys if py <= ym)
            wide = any(bad(px, py) for px in (x0 + 0.15, x1 - 0.15) for py in ys)
            if not hi and not lo:
                return x0, x1, y0, y1
            if y1 - y0 <= min_d and x1 - x0 <= min_w:
                return None
            if hi and y1 - y0 > min_d:
                y1 -= 0.25
            elif lo and y1 - y0 > min_d and y0 < y0_max:
                # ...but only a little.  Unbounded, this branch marched the whole
                # volume RIVER-WARD off its rock seat — 3.4 m out into the void for
                # weave-north_0 — which is the exact opposite of the steer.  A
                # blocked inland half means the house belongs somewhere else ALONG
                # THE CONTOUR, and the caller slides it in x instead.
                y0 += 0.25
            elif wide and x1 - x0 > min_w:
                x0 += 0.20
                x1 -= 0.20
            else:
                return None
        return None

    made_any = False
    for vi, v in enumerate(vols):
        zf = v["z"]
        rise = 0.95 + R.random() * 0.35
        h = v["h"]
        # DUCK THE WALK OVERHEAD.  The pilot cluster's inland space is where the
        # Quay's switchback stair comes down (`walk_e_quay-deck__pilot-cluster`
        # descends z 14.1 -> 9.9 across y 16.6..21.6), and the Quay's own deck
        # runs at z 14.24 over Westweave.  Tested at full height every volume
        # under them failed and the builder skipped eight of nine houses; the
        # right answer is a LOWER house, not no house — a dwelling tucked under
        # the stair is exactly what "scaffold residential" means here.
        ceil = ceiling_over(ax + v["xo"], (v["y0"] + v["y1"]) / 2, zf)
        if ceil is not None:
            avail = ceil - 0.50 - zf
            if avail < 2.9:
                rise = max(0.55, avail * 0.28)      # a shallower pitch, not no roof
            h = min(h, avail - rise)
        if h < 1.75:
            continue
        v["h"] = h
        v["rise"] = rise
        fitted = fit(ax + v["xo"] - v["w"] / 2, ax + v["xo"] + v["w"] / 2,
                     v["y0"], v["y1"], zf, zf + h + rise + 0.18,
                     y0_max=y_back + 0.9)
        if fitted is None:
            continue
        x0, x1, y0, y1 = fitted
        if hits_keepout(x0, x1, y0, y1):
            continue
        v["y1"] = y1
        v["w"] = x1 - x0
        v["xo"] = (x0 + x1) / 2 - ax
        made_any = True
        # ---- UNDERCROFT: masonry from the real ground up to the floor.  This is
        #      the whole point of the rework — what the eye reads as "resting on
        #      the terrain" is a continuous wall that meets the rock, not poles.
        gz = gmin(x0, x1, y0, y1)
        # An undercroft is a building's foundation, not a pile: where part of the
        # footprint overhangs, `gmin` returns the RIVERBED and the wall grew 17 m
        # tall.  Cap it at a believable 5 m of masonry and let the overhang be
        # carried by the corbels the plinth course already reads as.
        base = max(min(gz - 0.55, zf - 0.35), zf - 5.0)
        if zf - base > 0.35:
            P.append(box("uc", x0 + 0.10, x1 - 0.10, y0 + 0.10, y1 - 0.10,
                         base, zf - 0.22, MSTONE, COLL + "_BUILD"))
            # a battered plinth course, so the undercroft reads as built stone
            P.append(box("ucp", x0 - 0.16, x1 + 0.16, y0 - 0.16, y1 + 0.16,
                         base, base + 0.55 + R.random() * 0.5, MSTONE, COLL + "_BUILD"))
        # ---- floor plate
        P.append(box("fl", x0, x1, y0, y1, zf - 0.24, zf, MDECK, COLL + "_BUILD"))
        # ---- walls
        for a, b in ((( x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                     ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            P.append(beam("w", (a[0], a[1], zf + h / 2), (b[0], b[1], zf + h / 2),
                          h, 0.14, MDECK, COLL + "_BUILD", roll=math.pi / 2))
        for cxx, cyy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            P.append(obox("st", cxx, cyy, zf + h / 2, 0.18, 0.18, h, mat=MDECK,
                          cname=COLL + "_BUILD"))
        # ---- roof: a KICKED gable (two pitches), ridge along x or y per volume
        ov = 0.46
        rise = v["rise"]
        ze, zt = zf + h - 0.05, zf + h + rise
        zk = ze + rise * 0.42                       # the kick, 60% of the way out
        rv, rf = [], []

        def panel(pa, pb, pc, pd, za, zb):
            i = len(rv)
            rv.extend([(pa[0], pa[1], za), (pb[0], pb[1], za),
                       (pc[0], pc[1], zb), (pd[0], pd[1], zb),
                       (pa[0], pa[1], za - 0.13), (pb[0], pb[1], za - 0.13),
                       (pc[0], pc[1], zb - 0.13), (pd[0], pd[1], zb - 0.13)])
            rf.extend([(i, i + 1, i + 2, i + 3), (i + 4, i + 7, i + 6, i + 5),
                       (i, i + 4, i + 5, i + 1), (i + 3, i + 2, i + 6, i + 7)])

        if v["ridge"] == 'x':
            ymid = (y0 + y1) / 2
            for sgn in (-1, 1):
                ye = (y0 - ov) if sgn < 0 else (y1 + ov)
                yk = ymid + sgn * (y1 - y0) * 0.30
                panel((x0 - ov, ye), (x1 + ov, ye), (x1 + ov, yk), (x0 - ov, yk), ze, zk)
                panel((x0 - ov, yk), (x1 + ov, yk), (x1 + ov, ymid), (x0 - ov, ymid), zk, zt)
        else:
            xmid = (x0 + x1) / 2
            for sgn in (-1, 1):
                xe = (x0 - ov) if sgn < 0 else (x1 + ov)
                xk = xmid + sgn * (x1 - x0) * 0.30
                panel((xe, y0 - ov), (xe, y1 + ov), (xk, y1 + ov), (xk, y0 - ov), ze, zk)
                panel((xk, y0 - ov), (xk, y1 + ov), (xmid, y1 + ov), (xmid, y0 - ov), zk, zt)
        P.append(new_mesh("rf", rv, rf, MSHINGLE, COLL + "_BUILD"))
        # ---- windows: warm panes on the river face
        for k in range(2 if v["w"] > 3.6 else 1):
            wx = x0 + (k + 0.5) * (x1 - x0) / (2 if v["w"] > 3.6 else 1)
            P.append(obox("wn", wx, y1 - 0.02, zf + h * 0.55, 0.86, 0.12, 0.78,
                          mat=MGLASS, cname=COLL + "_BUILD"))
            P.append(obox("wf", wx, y1 - 0.02, zf + h * 0.55, 1.02, 0.07, 0.94,
                          mat=MDECK, cname=COLL + "_BUILD"))
        # ---- lean-to on the upper block's gable: a shed roof, its own direction
        if vi == 0 and lean:
            lx0 = x1 if lsgn > 0 else x0 - 1.55
            lx1 = x1 + 1.55 if lsgn > 0 else x0
            lz = zf - 0.30
            lgz = gmin(lx0, lx1, y0 + 0.3, y1 - 0.3)
            if clear_box((lx0 + lx1) / 2, (y0 + y1) / 2, lz, lz + 2.4, pad=0.18):
                _sup = first_solid_below((lx0 + lx1) / 2, (y0 + y1) / 2, lz)
                lbase = max(lgz - 0.5, lz - 4.2)     # ground_z returns -8.0 when
                if _sup is not None and _sup > lbase:
                    lbase = _sup - 0.10
                if lz - lbase > 0.35:                 # it finds nothing at all
                    P.append(box("lu", lx0 + 0.08, lx1 - 0.08, y0 + 0.35, y1 - 0.15,
                                 lbase, lz - 0.20, MSTONE, COLL + "_BUILD"))
                P.append(box("lf", lx0, lx1, y0 + 0.3, y1 - 0.1, lz - 0.22, lz,
                             MDECK, COLL + "_BUILD"))
                for a, b in (((lx0, y0 + 0.3), (lx1, y0 + 0.3)),
                             ((lx1, y0 + 0.3), (lx1, y1 - 0.1)),
                             ((lx1, y1 - 0.1), (lx0, y1 - 0.1)),
                             ((lx0, y1 - 0.1), (lx0, y0 + 0.3))):
                    P.append(beam("lw", (a[0], a[1], lz + 0.95), (b[0], b[1], lz + 0.95),
                                  1.9, 0.12, MDECK, COLL + "_BUILD", roll=math.pi / 2))
                i = 0
                sv = [(lx0 - 0.3, y0 + 0.1, lz + 1.85), (lx1 + 0.3, y0 + 0.1, lz + 2.45),
                      (lx1 + 0.3, y1 + 0.25, lz + 2.45), (lx0 - 0.3, y1 + 0.25, lz + 1.85)]
                if lsgn < 0:
                    sv = [(p[0], p[1], (lz + 2.45) if i in (0, 3) else (lz + 1.85))
                          for i, p in enumerate(sv)]
                P.append(new_mesh("ls", sv + [(p[0], p[1], p[2] - 0.12) for p in sv],
                                  [(0, 1, 2, 3), (7, 6, 5, 4), (4, 5, 1, 0),
                                   (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)],
                                  MSHINGLE, COLL + "_BUILD"))

    if not made_any:
        for q in P:
            if q:
                bpy.data.objects.remove(q, do_unlink=True)
        return None

    # ---- 3. THE GALLERY: light, open, river-facing, and it reaches the pad ---
    v = vols[-1]
    # the gallery deck sits FLUSH under the walk top, like every other deck in
    # this district, and stops 1.5 m short of the pad's near edge so that neither
    # its posts nor its roof ever enters the pad's 2.05 m corridor.  The pad's own
    # decking (laid by the deck phase) carries the last step, which is what makes
    # the entry read as continuous while the QA still lands on canonical topology.
    gz_f = pad[2] - DECK_DROP
    gx0, gx1 = ax + v["xo"] - v["w"] / 2 + 0.1, ax + v["xo"] + v["w"] / 2 - 0.1
    gy0 = v["y1"] - 0.2
    gy1 = min(pad[1] - 1.5, gy0 + 5.0)
    # the WHOLE gallery footprint, not just its post line: tested at the posts
    # only, the deck and its shed roof still reached over
    # `walk_e_pilot-cluster__weave-huts_l1` and took a sample there.
    while gy1 > gy0 + 0.9 and not all(
            clear_box(px, py, gz_f - 0.2, gz_f + 2.65, pad=0.16)
            for px in (gx0 + 0.2, (gx0 + gx1) / 2, gx1 - 0.2)
            for py in (gy0 + 0.2, (gy0 + gy1) / 2, gy1 - 0.25)):
        gy1 -= 0.25
    if gy1 - gy0 <= 0.9:
        # no room for a gallery: a bracketed canopy + drying rail on the river
        # wall, which is what a house whose door opens straight onto the deck
        # would really have
        zc = v["z"] + v["h"] - 0.35
        # The canopy projects 0.55 m past the wall and was the ONE piece of a
        # house never corridor-tested: at weave-huts the inter-cluster plank walk
        # runs within half a metre of the river wall, and the canopy hung 0.1-0.75
        # m over it.  March it in, and drop it rather than shorten it below a
        # believable 0.25 m eave.
        cy_ = gy0 + 0.55
        while cy_ > gy0 + 0.24 and not all(
                clear_box(px, cy_, zc - 0.45, zc + 0.55, pad=0.14)
                for px in (gx0 - 0.25, (gx0 + gx1) / 2, gx1 + 0.25)):
            cy_ -= 0.10
        if cy_ > gy0 + 0.24:
            P.append(beam("cn", (gx0 - 0.3, cy_, zc + 0.30),
                          (gx1 + 0.3, cy_, zc + 0.30), 0.9, 0.10, MSHINGLE,
                          COLL + "_BUILD", roll=math.pi / 2))
            for px in (gx0 + 0.1, (gx0 + gx1) / 2, gx1 - 0.1):
                P.append(beam("cb", (px, gy0 - 0.05, zc - 0.35),
                              (px, cy_, zc + 0.26), 0.08, 0.10, MDECK,
                              COLL + "_BUILD"))
            P.append(beam("dr", (gx0 + 0.2, cy_ - 0.10, zc - 0.10),
                          (gx1 - 0.2, cy_ - 0.10, zc - 0.10), 0.05, 0.05, MDECK,
                          COLL + "_BUILD"))
            GALLERY_AT.append((gx0, gx1, cy_ - 0.10, zc - 0.10))
        else:
            # no room for an eave at all: the drying rail goes ON the wall, which
            # still gives the laundry somewhere to hang
            GALLERY_AT.append((gx0, gx1, gy0 - 0.15, zc - 0.10))
    if gy1 - gy0 > 0.9:
        P.append(new_mesh("gd", [(gx0, gy0, gz_f - 0.14), (gx1, gy0, gz_f - 0.14),
                                 (gx1, gy1, gz_f - 0.14), (gx0, gy1, gz_f - 0.14),
                                 (gx0, gy0, gz_f), (gx1, gy0, gz_f),
                                 (gx1, gy1, gz_f), (gx0, gy1, gz_f)],
                          [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                           (2, 3, 7, 6), (3, 0, 4, 7)], MDECK, COLL + "_BUILD"))
        # THE STILTS — and this is now all of them: two posts under the gallery's
        # outboard corners, an accent under a structure whose weight is on rock
        for px in (gx0 + 0.25, gx1 - 0.25):
            sup = first_solid_below(px, gy1 - 0.3, gz_f)
            g = ground_z(px, gy1 - 0.3)
            zb = max(min(g, water_z(px) - 0.1) - 0.35, gz_f - 6.5)
            if sup is not None and sup > zb:
                zb = sup - 0.12           # it lands ON the deck below, not through it
            if gz_f - zb > 0.8:
                P.append(cyl("gp", (px, gy1 - 0.3, zb), (px, gy1 - 0.3, gz_f - 0.12),
                             0.16, 8, MDECK, COLL + "_BUILD"))
                P.append(beam("gb", (px, gy1 - 0.3, gz_f - 2.2),
                              (px, gy0 + 0.2, gz_f - 0.4), 0.11, 0.15, MDECK,
                              COLL + "_BUILD"))
        # posts + a shed roof over the gallery: this is the drying deck
        rh = 2.35                       # underside clears the 2.05 m corridor
        for px in (gx0 + 0.18, (gx0 + gx1) / 2, gx1 - 0.18):
            P.append(obox("gq", px, gy1 - 0.25, gz_f + rh / 2, 0.13, 0.13, rh,
                          mat=MDECK, cname=COLL + "_BUILD"))
        sv = [(gx0 - 0.35, gy0 - 0.1, gz_f + rh + 0.55), (gx1 + 0.35, gy0 - 0.1, gz_f + rh + 0.55),
              (gx1 + 0.35, gy1 + 0.4, gz_f + rh), (gx0 - 0.35, gy1 + 0.4, gz_f + rh)]
        P.append(new_mesh("gs", sv + [(p[0], p[1], p[2] - 0.12) for p in sv],
                          [(0, 1, 2, 3), (7, 6, 5, 4), (4, 5, 1, 0), (5, 6, 2, 1),
                           (6, 7, 3, 2), (7, 4, 0, 3)], MSHINGLE, COLL + "_BUILD"))
        # its rail, and the drying rail that makes it a weaver's gallery
        P.append(beam("gr", (gx0, gy1 - 0.2, gz_f + 0.95), (gx1, gy1 - 0.2, gz_f + 0.95),
                      0.08, 0.09, MDECK, COLL + "_BUILD"))
        P.append(beam("gr2", (gx0, gy1 - 0.2, gz_f + 0.50), (gx1, gy1 - 0.2, gz_f + 0.50),
                      0.06, 0.07, MDECK, COLL + "_BUILD"))
        P.append(beam("dr", (gx0 + 0.2, gy1 - 0.55, gz_f + rh - 0.35),
                      (gx1 - 0.2, gy1 - 0.55, gz_f + rh - 0.35), 0.05, 0.05, MDECK,
                      COLL + "_BUILD"))
        GALLERY_AT.append((gx0, gx1, gy1 - 0.45, gz_f + rh - 0.35))
        # a woven reed screen closing one end — the district's own motif
        se = gx0 if R.random() < 0.5 else gx1
        P.append(beam("sc", (se, gy0 + 0.2, gz_f + 1.1), (se, gy1 - 0.4, gz_f + 1.1),
                      1.9, 0.05, MDECK, COLL + "_BUILD", roll=math.pi / 2))

    ob = join_meshes([p for p in P if p], name, COLL + "_BUILD")
    return done(ob, T_(lf_deck=wall_col, lf_shingle=PAL["shingle"],
                       lf_stone=PAL["rockwall"]), jitter=0.10)

CLUSTERS = {
    # Each cluster is anchored on its own walk_pad_* — the pad is the hard
    # constraint (every dwelling must still meet its door pad) and the houses are
    # laid along the rock contour beside it, three abreast, each reaching back to
    # the deck with its own gallery.  `x` is the house's own centre line; the
    # inland seat is found from the terrain, never assumed.
    "weave-north": dict(shells=["lm_weave-north_0", "lm_weave-north_1", "lm_weave-north_2",
                                "lm_weave-north_0_roof", "lm_weave-north_1_roof",
                                "lm_weave-north_2_roof"],
                        floor=10.25, pad=(48.20, 20.00, 10.25), xlim=(43.7, 52.7),
                        xs=[44.9, 48.4, 51.7], widths=[4.0, 4.6, 3.7],
                        walls=[PAL["fadeblue"], PAL["oxblood"], PAL["cream"]]),
    "pilot-cluster": dict(shells=["lm_pilot-cluster_0", "lm_pilot-cluster_1",
                                  "lm_pilot-cluster_2", "lm_pilot-cluster_0_roof",
                                  "lm_pilot-cluster_1_roof", "lm_pilot-cluster_2_roof"],
                          floor=9.00, pad=(59.09, 22.00, 9.00), xlim=(54.6, 66.0),
                          # the Quay's switchback comes down at x 57.3..61.0, so
                          # the row straddles it: two houses either side and a
                          # smaller one tucked beneath its high end
                          xs=[55.2, 58.2, 62.8], widths=[4.1, 3.3, 4.4],
                          walls=[PAL["oxblood"], PAL["mossgreen"], PAL["ochre"]]),
    "weave-huts": dict(shells=["lm_weave-huts_0", "lm_weave-huts_1", "lm_weave-huts_2",
                               "lm_weave-huts_0_roof", "lm_weave-huts_1_roof",
                               "lm_weave-huts_2_roof"],
                       floor=7.83, pad=(71.45, 24.00, 7.83), xlim=(66.2, 76.0),
                       xs=[67.9, 71.4, 74.8], widths=[4.1, 4.7, 3.9],
                       walls=[PAL["mossgreen"], PAL["cream"], PAL["fadeblue"]]),
}
HUT_AT = []
ONLY = None
for a in argv:
    if a.startswith("cluster="):
        ONLY = a.split("=", 1)[1]

if "huts" in DO:
    gone = []
    for tag, spec in CLUSTERS.items():
        if ONLY and tag != ONLY:
            continue
        for nm in spec["shells"]:
            o = bpy.data.objects.get(nm)
            if o is not None:
                assert not nm.startswith(("walk_", "bar_")), "refusing to touch topology"
                bpy.data.objects.remove(o, do_unlink=True)
                gone.append(nm)
    log("DELETE", "%d lm_ blockout shells" % len(gone),
        "the stilt clusters' placeholder massing.  These are the objects that owned "
        "62 of the tier's 93 blocked walk samples, because a blockout is placed AT "
        "the landmark coordinate and the landmark coordinate is the standing pad "
        "(finding 92).")
    made = skipped = 0
    for tag, spec in CLUSTERS.items():
        if ONLY and tag != ONLY:
            continue
        for i, (hx, wdt, wall) in enumerate(zip(spec["xs"], spec["widths"],
                                                spec["walls"])):
            nm = "wv_hut_%s_%d" % (tag, i)
            fl = spec["floor"] + (i - 1) * 0.35        # the row itself steps
            ob = cliff_house(nm, hx, fl, spec["pad"], wall,
                             seed=hash(nm) & 0xffff, width=wdt,
                             xlim=spec["xlim"])
            if ob is None:
                skipped += 1
                continue
            b_ = world_bbox(ob)
            print("      %-26s x %5.1f..%5.1f  y %5.1f..%5.1f  z %5.2f..%5.2f"
                  % (nm, b_[0], b_[1], b_[2], b_[3], b_[4], b_[5]))
            HUT_AT.append((hx, spec["pad"][1], fl, wdt, wdt, 0.0, tag))
            made += 1
    log("BUILD", "wv_hut_* x%d" % made,
        "houses that STRADDLE THE CLIFF (user steer, 2026-07-29): each is a masonry "
        "undercroft cut into the rock carrying two offset half-levels that step down "
        "the fall, a lean-to on one gable with its own lower ridge, kicked two-pitch "
        "roofs whose ridges change direction between volumes, and a light open "
        "GALLERY on the river face that reaches back to the walk pad.  The only "
        "stilts left in the district's dwellings are the two posts under each "
        "gallery's outboard corners.  %d skipped where every volume stood in a "
        "walking line." % skipped)


# ===========================================================================
# 3. THE KEEPERS' COTTAGE — the kit asset, adapted
# ===========================================================================
if "cottage" in DO:
    for nm in ("lm_keepers-cottage_body", "lm_keepers-cottage_roof"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    log("DELETE", "lm_keepers-cottage_body/_roof",
        "8 blocked samples + 1 of the region's 4 strays (its roof overlapped its own "
        "body, so the support ray started inside it)")

    # The kit cottage is authored in town axes with the BALCONY on +y (its
    # `lf_deck` faces run y 2.50..4.89 at z ~0) and the body on -y — which is
    # exactly the map's "balcony platform on the river side overlooking the locks".
    # Siting it is the whole problem: `walk_pad_keepers-cottage` (2.6 x 2.6 at
    # y 20.7..23.3) sits in the middle of a 9 m parcel, the Lockhead path descends
    # across the west half at z 8.6..9.4 — ABOVE the cottage's own floor, so the
    # body cannot go there at all — and the basin steps leave from the east.
    # The resolution is that the BALCONY IS THE PAD'S DECKING: a balcony is a
    # walkable platform, it lands 55 mm under the walk top like every other deck
    # in this district, the down-ray still hits canonical topology, and the player
    # standing on the pad is standing on the cottage's balcony, which is where the
    # map says supper is served.  Only the BODY has to clear the corridor.
    FLOOR = 7.83
    BODY_Y0, BODY_Y1 = -3.40, 2.50       # the kit's own body extent in local y
    BODY_HX, ROOF = 3.75, 4.86

    # The site has three hard constraints that pull against each other, so it is
    # SEARCHED rather than judged: (a) the body may not stand in a walking line,
    # (b) the Keepers' Spur buttress rises to z 14.8 at x 93..97 / y 15..17, so a
    # body pushed inland to clear the path gets its roof buried in Locksfoot's own
    # rock, and (c) the parcel is only 9 m wide.  Scoring all three and taking the
    # minimum found a seat no amount of eyeballing did.
    BAL_Y1 = 4.96                        # the balcony's outer edge, in local y

    def score_seat(gx, gy, nu=7, nv=5):
        viol = burial = outp = rail = 0
        for iu in range(nu):
            px = gx + (iu / (nu - 1.0) - 0.5) * 2 * BODY_HX
            for iv in range(nv):
                py = gy + BODY_Y0 + iv * (BODY_Y1 - BODY_Y0) / (nv - 1.0)
                if not clear_box(px, py, FLOOR - 0.1, FLOOR + ROOF + 0.2, pad=0.20):
                    viol += 1
                if ground_z(px, py) > FLOOR + ROOF - 0.4:
                    burial += 1
                if not (88.1 <= px <= 97.1):
                    outp += 1
        # ...and the BALCONY'S OWN BALUSTRADE, which is the part the first version
        # forgot.  The balcony DECK may lie under a walk — that is the whole idea,
        # it is the pad's decking — but its perimeter rail is a metre of solid
        # timber standing on whatever is beneath it, and it took 12 of the pad's
        # samples.  Test the three rail lines.
        for t in range(5):
            f = t / 4.0
            for px, py in ((gx - BODY_HX + 0.1, gy + BODY_Y1 + f * (BAL_Y1 - BODY_Y1)),
                           (gx + BODY_HX - 0.1, gy + BODY_Y1 + f * (BAL_Y1 - BODY_Y1)),
                           (gx + (f - 0.5) * 2 * BODY_HX, gy + BAL_Y1 - 0.1)):
                if not clear_box(px, py, FLOOR, FLOOR + 1.2, pad=0.16):
                    rail += 1
        n = nu * nv
        # Burial is CHEAP: the back of a cliff cottage cut into the Keepers' Spur
        # buttress is the look the map asks for ("cottage against the cliff").
        # Standing in a walking line and standing outside the parcel are not.
        # Weighted equally, the search bought a seat 21 samples out of parcel to
        # save a few buried-roof samples.
        return ((viol + rail) * 14.0 / n * 35 + outp * 9.0 / n * 35
                + burial * 1.2 / n * 35 + math.hypot(gx - 92.61, gy - 20.0) * 0.30,
                viol + rail, burial, outp)

    best, bestscore = None, 1e9
    for gx in [89.0 + 0.60 * i for i in range(11)]:          # coarse
        for gy in [14.4 + 0.60 * i for i in range(12)]:
            s0 = score_seat(gx, gy, nu=5, nv=4)
            if s0[0] < bestscore:
                bestscore, best = s0[0], (gx, gy)
    bx, by = best
    bestscore = 1e9
    for gx in [bx - 0.6 + 0.20 * i for i in range(7)]:       # refine
        for gy in [by - 0.6 + 0.20 * i for i in range(7)]:
            s0 = score_seat(gx, gy, nu=9, nv=7)
            if s0[0] < bestscore:
                bestscore, best = s0[0], (gx, gy, s0[1], s0[2], s0[3])
    cx, cy, viol, burial, outp = best
    ob = kit_place("lf_keeper_cottage", (cx, cy, FLOOR), rz=0.0,
                   cname=COLL + "_BUILD", oname="wv_keeper_cottage", mode="origin")
    ob.location = Vector((cx, cy, FLOOR))
    b = world_bbox(ob)
    log("BUILD", "wv_keeper_cottage",
        "kit asset appended read-only, seated by scored search at (%.2f, %.2f) "
        "floor %.2f: body x %.1f..%.1f, balcony out to y %.2f over the basin, roof "
        "%.1f.  Score = %d corridor samples / %d buried-roof samples / %d out of "
        "parcel, of 49 each.  The balcony IS the pad's decking — a balcony is a "
        "walkable platform, it lands under the walk top like every other deck here, "
        "and the player standing on walk_pad_keepers-cottage is standing where the "
        "map says supper is served."
        % (cx, cy, FLOOR, b[0], b[1], b[3], b[5], viol, burial, outp))
    MADE.append(ob)          # already carries Col + UVMap from the kit

    # the balcony's own posts land on falling ground, so give them a footing
    fo = []
    for px in (b[0] + 0.75, (b[0] + b[1]) / 2, b[1] - 0.75):
        gz = ground_z(px, b[3] - 0.5)
        if FLOOR - 1.7 - gz > 0.4:
            fo.append(cyl("cf", (px, b[3] - 0.55, gz - 0.3), (px, b[3] - 0.55, FLOOR - 1.55),
                          0.17, 8, MDECK, COLL + "_BUILD"))
    done(join_meshes(fo, "wv_cottage_footings", COLL + "_BUILD"), T_(lf_deck=PAL["timber"]))

    # the under-balcony lantern the map asks for is IN the kit; what the balcony
    # needs from this pass is the rock-side stair rail and a supper-table lantern
    # bracket, both of which the dress phase hangs.


# ===========================================================================
# 4. THE FISH-DOCK LADDER — blockout art standing in its own walkway
# ===========================================================================
if "ladder" in DO:
    old = [o for o in bpy.data.objects
           if o.name.startswith("e_weave-huts__fish-dock_")]
    # 10 blocked + 4 headroom samples, all of them the blockout's own ladder
    # standing ON the walk it represents.  Same class as the lm_ shells: it is
    # PATHS-collection placeholder art for a map edge inside this parcel, not
    # canonical topology (no walk_/bar_ name), so it is this district's to replace.
    zs = []
    for o in old:
        b = world_bbox(o)
        zs.append((b[0], b[1], b[2], b[3], b[4], b[5]))
        bpy.data.objects.remove(o, do_unlink=True)
    if not zs:
        # RECORDED extent of the blockout ladder (measured before it was deleted).
        # Deriving the replacement from the thing it replaces made the pass
        # non-idempotent: on a second run the blockout was already gone and the
        # ladder simply vanished from the district without a word.
        zs = [(58.99, 71.55, 23.75, 28.25, 0.95, 7.98)]
    log("DELETE", "%d e_weave-huts__fish-dock_ blockout parts" % len(old),
        "the placeholder ladder + its rail, standing in the walking line it is "
        "supposed to represent")
    if zs:
        x0 = min(z[0] for z in zs); x1 = max(z[1] for z in zs)
        y0 = min(z[2] for z in zs); y1 = max(z[3] for z in zs)
        z0 = min(z[4] for z in zs); z1 = max(z[5] for z in zs)
        # rebuild it OUTBOARD of the run, hung off the hut piles, so the rungs are
        # beside the climbing line rather than in it (finding 92's shape)
        A = Vector((x1, y0, z1)); B = Vector((x0, y1, z0))
        d = (B - A)
        n = Vector((-d.y, d.x, 0)).normalized()
        parts = []
        L = d.length
        # finding 97 again: the RUNGS were filtered and the STRINGERS were not, so
        # the two stringers ran the full 15 m from the huts' pad to the fish dock
        # and picked up 4 samples at each end.  Walk both ends in until the whole
        # run is clear, exactly as the Waterfront does for a stair stringer (74).
        def walk_in(t0, t1):
            for _ in range(30):
                if t1 - t0 < 0.12:
                    break
                bad0 = any(over_walk(*(A + d * (t0 + (t1 - t0) * f / 8))[:2],
                                     (A + d * (t0 + (t1 - t0) * f / 8)).z + 0.02, pad=0.16)
                           for f in range(3))
                bad1 = any(over_walk(*(A + d * (t1 - (t1 - t0) * f / 8))[:2],
                                     (A + d * (t1 - (t1 - t0) * f / 8)).z + 0.02, pad=0.16)
                           for f in range(3))
                if not bad0 and not bad1:
                    break
                if bad0:
                    t0 += 0.035
                if bad1:
                    t1 -= 0.035
            return t0, t1

        t0, t1 = walk_in(0.0, 1.0)
        P0, P1 = A + d * t0, A + d * t1
        for side in (-1, 1):
            off = n * (0.46 * side)
            parts.append(beam("lr", P0 + off, P1 + off, 0.10, 0.13, MDECK, COLL + "_DECK"))
        k = 0
        while k * 0.33 < L * (t1 - t0):
            p = P0 + (P1 - P0) * ((k * 0.33) / max(L * (t1 - t0), 1e-6))
            if not over_walk(p.x, p.y, p.z + 0.02, pad=0.10):
                parts.append(beam("lg", p - n * 0.44, p + n * 0.44, 0.07, 0.05, MDECK,
                                  COLL + "_DECK"))
            k += 1
        done(join_meshes(parts, "wv_fishdock_ladder", COLL + "_DECK"),
             T_(lf_deck=PAL["timber"]))
        log("BUILD", "wv_fishdock_ladder",
            "stringers set 0.46 m outboard on both sides, BOTH ENDS walked in until "
            "the whole run is clear (finding 97 — the rungs were filtered and the "
            "stringers were not), every rung Corridor-tested before it is laid: the "
            "climb is unchanged, the walking line is clear")


# ===========================================================================
# 5. DRESS — a weavers' tier: drying lines, dye pots, screens, nets, lanterns
# ===========================================================================
bpy.context.view_layer.update()
_DG = bpy.context.evaluated_depsgraph_get()


def deck_top(x, y, z0=17.0):
    """The top of the DISTRICT'S OWN decking — never a walk ribbon.

    The first version returned `COR0.top_at`, the walk surface, and every prop in
    the pass was then rejected by its own Corridor test: a barrel standing ON a
    walk is over_walk by definition, so the dye pots, the clutter, the racks and
    the whole North Landing dressing came out at ZERO and the log said "x0" four
    times.  What a prop actually stands on is this district's planking, its
    aprons and its hut verandas, and those are exactly the surfaces that exist
    OUTSIDE the walking line.  Ray-cast for them.
    """
    org = Vector((x, y, z0))
    d = Vector((0, 0, -1))
    for _ in range(24):
        hit, loc, n, i, ob, mw = _SC.ray_cast(_DG, org, d, distance=44)
        if not hit:
            return None
        if ob.name.startswith(("wv_", "nl_")) and n.z > 0.45:
            return loc.z
        if ob.name.startswith(("walk_", "bar_")):
            return None            # we are over a walking line: not a prop seat
        org = loc + d * 0.02
    return None


def swag(name, a, b, sag, w, mat, cname, seg=9, col=None):
    """A hanging line.  A rope is a CHAIN — modelled, not faked with a box."""
    a, b = Vector(a), Vector(b)
    pts = []
    for i in range(seg + 1):
        t = i / seg
        p = a.lerp(b, t)
        p.z -= sag * math.sin(math.pi * t)
        pts.append(p)
    parts = []
    for i in range(seg):
        parts.append(beam("sw", pts[i], pts[i + 1], w, w, mat, cname))
    return parts, pts


if "dress" in DO:
    props, cloth, veg = [], [], []
    kit_load(["lf_barrel", "lf_crate", "lf_cargo_stack", "lf_rope_coil", "lf_bollard",
              "lf_cleat", "lf_lantern_post", "lf_mooring_post", "lf_bunting_swag"])

    # ---- lantern meshes, one per KEYW_lantern_ bulb the light rig installed.
    #      Built FROM the lamps rather than from a second hard-coded list, so the
    #      glass can never end up somewhere the light is not (the two lists drifting
    #      apart is the same failure mode as finding 117, one level up).
    nl = 0
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or not o.name.startswith("KEYW_lantern_"):
            continue
        x, y, z = o.location
        p = []
        p.append(cyl("lb", (x, y, z + 0.30), (x, y, z + 0.46), 0.11, 8, MIRON, COLL + "_PROPS"))
        p.append(obox("lg", x, y, z, 0.20, 0.20, 0.30, mat=MGLASS, cname=COLL + "_PROPS"))
        p.append(cyl("lc", (x, y, z - 0.20), (x, y, z - 0.16), 0.13, 8, MIRON, COLL + "_PROPS"))
        p.append(cyl("lh", (x, y, z + 0.46), (x, y, z + 0.86), 0.018, 6, MIRON, COLL + "_PROPS"))
        props += p
        nl += 1

    # ---- DRYING LINES: the district's whole reason for its name.
    #      Runs are strung between hut posts and deck rails; each carries cloth
    #      panels, and every run is height-tested along its length (finding 98:
    #      the sag is per run, and 1.55 m of sag on an 8 m line is 1.2 m of
    #      headroom where the corridor wants 2.0).
    # The runs are derived FROM the galleries the houses actually built, never
    # from a hard-coded list: the house pass moved every dwelling 3-7 m inland
    # onto the rock, and a hard-coded line would still be strung across the void
    # where the old stilt huts used to float.  Two kinds — along each gallery's
    # own drying rail, and between neighbouring galleries in a cluster.
    LINES = []
    for (gx0, gx1, gy, gz) in GALLERY_AT:
        LINES.append(((gx0 + 0.25, gy, gz), (gx1 - 0.25, gy, gz)))
    G = sorted(GALLERY_AT)
    for a, b in zip(G, G[1:]):
        if abs(b[0] - a[1]) < 4.6:
            LINES.append(((a[1] - 0.2, a[2], a[3] - 0.15),
                          (b[0] + 0.2, b[2], b[3] - 0.15)))
    ncloth = 0
    nrun = 0
    for a, b in LINES:
        L = (Vector(b) - Vector(a)).length
        if L < 0.8:
            continue
        sag = min(0.20 + 0.040 * L, 0.55)        # per run, not one global number
        parts, pts = swag("dl", a, b, sag, 0.028, MDECK, COLL + "_PROPS")
        # finding 98: the sag is per run, and the low point has to clear whatever
        # walk is under it by the full 2.0 m corridor
        if any((COR0.top_at(q.x, q.y) is not None and q.z - COR0.top_at(q.x, q.y) < 2.05)
               for q in pts):
            for q in parts:
                bpy.data.objects.remove(q, do_unlink=True)
            continue
        props += parts
        nrun += 1
        for k in range(1, len(pts) - 1):
            if rng.random() > 0.78:
                continue
            q = pts[k]
            wdt = 0.34 + rng.random() * 0.30
            hgt = 0.55 + rng.random() * 0.60
            t = COR0.top_at(q.x, q.y)
            if t is not None:
                # size the panel to the headroom that EXISTS rather than dropping
                # the station: every run passes over a deck somewhere, and the
                # first version therefore hung zero panels in a district whose
                # entire identity is its laundry
                hgt = min(hgt, q.z - t - 2.05 - 0.03)
            if hgt < 0.28:
                continue
            c = obox("cl", q.x, q.y, q.z - hgt / 2 - 0.03, wdt, 0.035, hgt,
                     rz=rng.random() * 0.4, mat=MMATTE, cname=COLL + "_PROPS")
            cloth.append((c, rng.choice([PAL["cloth_r"], PAL["cloth_b"], PAL["cloth_y"],
                                         PAL["cloth_w"], PAL["cloth_g"], PAL["dye_indigo"],
                                         PAL["dye_madder"], PAL["dye_weld"]])))
            ncloth += 1
    log("BUILD", "wv_drying_lines / wv_cloth",
        "%d of %d runs strung between the galleries, carrying %d panels — the sag is "
        "solved PER RUN, and a panel is SIZED to the headroom that exists rather "
        "than dropped (finding 98)" % (nrun, len(LINES), ncloth))

    # ---- DYE POTS: three vats, the colours the cloth on the lines is dyed with
    ndye = 0
    for (px, py, col) in ((49.0, 22.4, PAL["dye_indigo"]), (60.2, 24.6, PAL["dye_madder"]),
                          (69.9, 26.4, PAL["dye_weld"]), (72.4, 23.0, PAL["dye_indigo"])):
        t = deck_top(px, py)
        if t is None or not clear_box(px, py, t, t + 1.3, pad=0.22) or not spot(px, py, 0.75):
            continue
        v = cyl("dv", (px, py, t + 0.02), (px, py, t + 0.62), 0.46, 12, MIRON,
                COLL + "_PROPS", r2=0.52)
        props.append(v)
        liq = cyl("dq", (px, py, t + 0.50), (px, py, t + 0.54), 0.47, 12, MMATTE,
                  COLL + "_PROPS")
        cloth.append((liq, col))
        for k in range(3):                      # the stones it stands on
            props.append(obox("dh", px + math.cos(k * 2.1) * 0.52, py + math.sin(k * 2.1) * 0.52,
                              t + 0.10, 0.22, 0.20, 0.20, rz=rng.random() * 3,
                              mat=MSTONE, cname=COLL + "_PROPS"))
        ndye += 1
    log("BUILD", "wv_dyepots x%d" % ndye,
        "indigo, madder and weld — a weavers' tier is defined by what it dyes with, "
        "and the vats are the only saturated colour in the district")

    # ---- NETS + fish racks on the drying decks (the map calls them out by name)
    nrack = 0
    for px, py in ((63.4, 25.2), (65.0, 26.6), (66.6, 24.4), (67.4, 26.2)):
        t = deck_top(px, py)
        if t is None or not clear_box(px, py, t, t + 2.0, pad=0.22) or not spot(px, py, 0.85):
            continue
        for sgn in (-1, 1):
            props.append(obox("rp", px + sgn * 0.62, py, t + 0.85, 0.11, 0.11, 1.70,
                              mat=MDECK, cname=COLL + "_PROPS"))
        props.append(beam("rb", (px - 0.62, py, t + 1.66), (px + 0.62, py, t + 1.66),
                          0.08, 0.08, MDECK, COLL + "_PROPS"))
        n = obox("nt", px, py, t + 1.10, 1.16, 0.06, 1.05, mat=MMATTE, cname=COLL + "_PROPS")
        cloth.append((n, PAL["net"]))
        nrack += 1

    # ---- everyday clutter from the kit, on the decks, through the occupancy list
    nclut = 0
    for _ in range(150):
        px = rng.uniform(44.0, 96.0)
        py = rng.uniform(18.0, 28.0)
        t = deck_top(px, py)
        if t is None or t < 5.0:
            continue
        if not clear_box(px, py, t, t + 1.2, pad=0.26) or not spot(px, py, 0.62):
            continue
        if not free_of_walk(px, py, t, band=0.75):
            continue
        nm = rng.choice(["lf_barrel", "lf_crate", "lf_crate", "lf_rope_coil",
                         "lf_cargo_stack", "lf_bollard"])
        o = kit_place(nm, (px, py, t + 0.02), rz=rng.random() * 6.28,
                      cname=COLL + "_PROPS",
                      oname="wv_clut_%d" % nclut, scale=0.88 + rng.random() * 0.3)
        MADE.append(o)
        nclut += 1
        if nclut >= 46:
            break
    log("BUILD", "wv_clut_* x%d / racks x%d" % (nclut, nrack),
        "kit barrels, crates, cargo and rope on the decks — one shared occupancy list, "
        "so nothing interpenetrates anything else (finding 114)")

    # ---- BUNTING between the clusters (the map's first motif)
    nb = 0
    # Strung ACROSS the gaps between clusters, high, over the falling ground where
    # nothing walks beneath — the map's first motif ("bunting strung across the
    # gorge and between houses") and the thing that ties three separate clusters
    # into one district when read from the Waterfront below.
    BUNT = [((53.6, 19.2, 13.1), (56.4, 19.0, 12.4)),
            ((65.2, 19.4, 11.4), (68.4, 19.6, 10.9)),
            ((74.4, 21.0, 10.6), (79.0, 22.4, 10.1)),
            ((84.0, 22.4, 10.1), (89.4, 22.6, 10.3)),
            ((47.0, 17.6, 13.3), (50.6, 17.4, 13.3)),
            ((70.2, 17.2, 11.6), (74.0, 17.4, 11.8))]
    for a, b in BUNT:
        L = (Vector(b) - Vector(a)).length
        parts, pts = swag("bt", a, b, min(0.22 + 0.05 * L, 0.70), 0.024, MDECK,
                          COLL + "_PROPS")
        if any((COR0.top_at(p.x, p.y) is not None and p.z - COR0.top_at(p.x, p.y) < 2.2)
               for p in pts):
            for q in parts:
                bpy.data.objects.remove(q, do_unlink=True)
            continue
        props += parts
        for k in range(1, len(pts) - 1):
            p = pts[k]
            f = obox("pn", p.x, p.y, p.z - 0.17, 0.20, 0.02, 0.30,
                     rz=rng.random() * 0.5, mat=MMATTE, cname=COLL + "_PROPS")
            cloth.append((f, rng.choice([PAL["cloth_r"], PAL["cloth_g"], PAL["cloth_b"],
                                         PAL["cloth_y"]])))
        nb += 1
    log("BUILD", "wv_bunting x%d runs" % nb, "the map's first motif, strung across the tier")

    done(join_meshes(props, "wv_props", COLL + "_PROPS"), T_(lf_deck=PAL["timber"]))
    # cloth is joined per COLOUR so each panel keeps its own dye
    bycol = {}
    for ob, col in cloth:
        bycol.setdefault(tuple(round(c, 4) for c in col), []).append(ob)
    for i, (col, obs) in enumerate(sorted(bycol.items())):
        done(join_meshes(obs, "wv_cloth_%d" % i, COLL + "_PROPS"),
             T_(lf_matte=col), jitter=0.10)
    log("BUILD", "wv_cloth_* x%d" % len(bycol),
        "one object per dye, so a panel's colour is its vertex colour and survives "
        "the glTF round trip as COLOR_0")

    # ---- FOLIAGE on the rock between the stilts — veg_ so it is never standable
    nv = 0
    for _ in range(320):
        px = rng.uniform(43.0, 97.0)
        py = rng.uniform(15.5, 26.0)
        gz = ground_z(px, py)
        if gz < water_z(px) + 0.15 or gz > 13.0:
            continue
        if not clear_box(px, py, gz, gz + 1.4, pad=0.30) or not spot(px, py, 0.55):
            continue
        h = 0.55 + rng.random() * 0.85
        w = 0.42 + rng.random() * 0.55
        # tapered drums, not boxes (finding 115): three of them read as mass
        parts = []
        for k in range(3):
            ax = px + (rng.random() - 0.5) * w * 0.7
            ay = py + (rng.random() - 0.5) * w * 0.7
            hh = h * (0.62 + rng.random() * 0.5)
            parts.append(cyl("vg", (ax, ay, gz - 0.05), (ax, ay, gz + hh),
                             w * 0.5, 9, MMATTE, COLL + "_VEG", r2=w * 0.16))
        col = rng.choice([PAL["leaf"], PAL["leaf"], PAL["mosswood"], PAL["leafdry"],
                          PAL["leafturn"]])
        done(join_meshes(parts, "veg_wv_clump_%d" % nv, COLL + "_VEG"),
             T_(lf_matte=col), jitter=0.13)
        nv += 1
        if nv >= 74:
            break
    log("BUILD", "veg_wv_clump_* x%d" % nv,
        "tapered drums on the rock between the stilts, autumn-graded by VERTEX "
        "COLOUR rather than a noise+ramp node tree — foliage was the largest single "
        "group in the 516 white primitives")


# ===========================================================================
# 6. NORTH LANDING — the last pier  (user extension, prefix nl_)
# ===========================================================================
if "landing" in DO:
    kit_load(["lf_bollard", "lf_cleat", "lf_mooring_post", "lf_lantern_post",
              "lf_barrel", "lf_crate", "lf_cargo_stack", "lf_rope_coil"])
    P = []
    LM = bpy.data.objects["walk_lm_north-landing"]
    b = world_bbox(LM)
    DECK_Z = b[5]                      # -0.75, fixed by canonical topology
    BED = -7.30
    WATER = WATER_TAIL                 # -2.80 in the SAVED file (see the report)
    cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
    R = (b[1] - b[0]) / 2

    # ---- piles: the landing's whole point is that the pool dropped under it.
    #      4.5 m of pile stands in the water and 2.05 m in the air; showing that
    #      length IS the brief ("embrace the height with visible pile length").
    heads = []
    for ring, rr, n in ((0, R * 0.55, 6), (1, R * 0.92, 12)):
        for k in range(n):
            th = 2 * math.pi * k / n + ring * 0.26
            px, py = cx + math.cos(th) * rr, cy + math.sin(th) * rr
            zt = DECK_Z - 0.34
            P.append(cyl("np", (px, py, BED - 0.30), (px, py, zt),
                         0.19 + rng.random() * 0.05, 8, MDECK, COLL + "_DECK"))
            heads.append((px, py, zt))
    for i, (x1, y1, z1) in enumerate(heads):        # two bands of bracing
        for x2, y2, z2 in heads[i + 1:]:
            d = math.hypot(x2 - x1, y2 - y1)
            if not (1.3 < d < 3.0):
                continue
            for band in (0, 1):
                zt = z1 - 0.5 - band * 2.4
                zb = max(zt - 2.2, BED + 0.5)
                if zt - zb > 0.6:
                    P.append(beam("nb", (x1, y1, zb), (x2, y2, zt), 0.10, 0.14, MDECK,
                                  COLL + "_DECK"))
                    P.append(beam("nb", (x1, y1, zt), (x2, y2, zb), 0.10, 0.14, MDECK,
                                  COLL + "_DECK"))
    # ---- the working apron: a pier is bigger than the disc a player stands on
    for k in range(44):
        t0, t1 = 2 * math.pi * k / 44, 2 * math.pi * (k + 1) / 44
        for j in range(4):
            a = R - 0.15 + 1.70 * j / 4
            b = R - 0.15 + 1.70 * (j + 1) / 4
            q = [(cx + math.cos(t) * rr, cy + math.sin(t) * rr)
                 for t, rr in ((t0, a), (t1, a), (t1, b), (t0, b))]
            mid = (sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4)
            if not all(free_of_walk(px, py, DECK_Z - 0.06) for px, py in q + [mid]):
                continue
            P.append(new_mesh("na", [(x, y, DECK_Z - 0.16) for x, y in q]
                              + [(x, y, DECK_Z - 0.05) for x, y in q],
                              [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                               (2, 3, 7, 6), (3, 0, 4, 7)], MDECK, COLL + "_DECK"))

    # ---- edge coping: a dock's rubbing strake, all the way round
    ring = []
    for k in range(33):
        th = 2 * math.pi * k / 32
        ring.append((cx + math.cos(th) * (R + 1.55), cy + math.sin(th) * (R + 1.55),
                     DECK_Z - 0.10))
    for k in range(32):
        a, b = ring[k], ring[k + 1]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if not all(free_of_walk(q[0], q[1], DECK_Z - 0.10)
                   for q in (a, b, mid)):
            continue                # it ran over the lock-five approach lane
        P.append(beam("nc", a, b, 0.17, 0.26, MDECK, COLL + "_DECK"))
    # ---- a landing STAGE: the low platform a boat is actually boarded from
    sy = cy + R - 0.2
    st = []
    stz = WATER + 0.55
    for k in range(4):
        px = cx - 1.65 + k * 1.10
        st.append((px, sy + 1.15, stz))
        P.append(cyl("ns", (px, sy + 1.15, BED - 0.2), (px, sy + 1.15, stz),
                     0.15, 7, MDECK, COLL + "_DECK"))
    P.append(new_mesh("nst", [(cx - 2.0, sy + 0.55, stz), (cx + 2.0, sy + 0.55, stz),
                              (cx + 2.0, sy + 1.75, stz), (cx - 2.0, sy + 1.75, stz),
                              (cx - 2.0, sy + 0.55, stz - 0.14), (cx + 2.0, sy + 0.55, stz - 0.14),
                              (cx + 2.0, sy + 1.75, stz - 0.14), (cx - 2.0, sy + 1.75, stz - 0.14)],
                      [(0, 1, 2, 3), (7, 6, 5, 4), (4, 5, 1, 0), (5, 6, 2, 1),
                       (6, 7, 3, 2), (7, 4, 0, 3)], MDECK, COLL + "_DECK"))
    # ...and the ladder down to it, hung OUTBOARD of the deck edge
    lx = cx + 1.9
    for sgn in (-1, 1):
        P.append(beam("nl", (lx + sgn * 0.30, sy + 0.42, DECK_Z + 0.10),
                      (lx + sgn * 0.30, sy + 0.42, stz), 0.09, 0.11, MDECK, COLL + "_DECK"))
    z = stz + 0.32
    while z < DECK_Z:
        P.append(beam("nr", (lx - 0.32, sy + 0.42, z), (lx + 0.32, sy + 0.42, z),
                      0.06, 0.05, MDECK, COLL + "_DECK"))
        z += 0.34
    done(join_meshes(P, "nl_pier", COLL + "_DECK"), T_(lf_deck=PAL["timber"]), jitter=0.08)
    log("BUILD", "nl_pier",
        "%d piles from the tail bed at %.1f to the deck at %.2f — %.2f m of them "
        "standing in the water and %.2f m in the air; ring coping, a boarding stage "
        "at %.2f (0.55 m over the pool) and a ladder down to it, hung outboard of "
        "the deck edge" % (len(heads), BED, DECK_Z, WATER - BED, DECK_Z - WATER, stz))

    # ---- mooring dressing on the APRON, all Corridor- and occupancy-filtered
    bpy.context.view_layer.update()
    _DG = bpy.context.evaluated_depsgraph_get()
    n = 0
    for k in range(30):
        th = 2 * math.pi * k / 30 + 0.2
        rr = R + 0.35 + (k % 3) * 0.45
        px, py = cx + math.cos(th) * rr, cy + math.sin(th) * rr
        t = deck_top(px, py)
        if t is None or not clear_box(px, py, t, t + 1.3, pad=0.24) or not spot(px, py, 0.58):
            continue
        if not free_of_walk(px, py, t, band=0.75):
            continue                # the apron passes near the lock-five lane here
        nm = rng.choice(["lf_bollard", "lf_cleat", "lf_barrel", "lf_crate",
                         "lf_rope_coil", "lf_cargo_stack", "lf_lantern_post"])
        o = kit_place(nm, (px, py, t + 0.02), rz=th + math.pi / 2, cname=COLL + "_PROPS",
                      oname="nl_dress_%d" % n, scale=0.92 + rng.random() * 0.22)
        MADE.append(o)
        n += 1
    # mooring posts stand OUTBOARD, in the water, where a boat's line reaches them
    for k, th in enumerate((0.5, 1.5, 2.6, 4.2)):
        px, py = cx + math.cos(th) * (R + 0.85), cy + math.sin(th) * (R + 0.85)
        o = kit_place("lf_mooring_post", (px, py, WATER - 1.4), rz=0.0,
                      cname=COLL + "_PROPS", oname="nl_moor_%d" % k, mode="cxy_minz")
        MADE.append(o)
    log("BUILD", "nl_dress_* x%d + nl_moor_* x4" % n,
        "kit bollards, cleats, rope and cargo on the deck; four mooring posts set "
        "outboard in the pool where a boat's line actually reaches them")

    # ---- foliage on the strand behind the landing
    nv = 0
    for _ in range(300):
        px = rng.uniform(99.5, 111.5)
        py = rng.uniform(21.0, 25.5)
        gz = ground_z(px, py)
        if gz < WATER + 0.2 or gz > 6.0:
            continue
        if not clear_box(px, py, gz, gz + 1.2, pad=0.30) or not spot(px, py, 0.6):
            continue
        h = 0.5 + rng.random() * 0.7
        w = 0.45 + rng.random() * 0.5
        parts = [cyl("vg", (px + (rng.random() - .5) * w * .7, py + (rng.random() - .5) * w * .7,
                            gz - 0.05),
                     (px + (rng.random() - .5) * w * .7, py + (rng.random() - .5) * w * .7,
                      gz + h * (0.6 + rng.random() * 0.5)), w * 0.5, 9, MMATTE,
                     COLL + "_VEG", r2=w * 0.16) for _ in range(3)]
        done(join_meshes(parts, "veg_nl_clump_%d" % nv, COLL + "_VEG"),
             T_(lf_matte=rng.choice([PAL["leaf"], PAL["mosswood"], PAL["leafdry"]])),
             jitter=0.13)
        nv += 1
        if nv >= 30:
            break
    log("BUILD", "veg_nl_clump_* x%d" % nv, "on the strand behind the pier")


# ===========================================================================
# 7. donors out, inventory, glTF gate
# ===========================================================================
# finding 119: `libraries.load` parks the donors at (0,0,0), which is inside the
# Boatyard, and `hide_render` does not stop a glTF export.
ndon = 0
for o in list(bpy.data.objects):
    if o.name.startswith("WVKITSRC_"):
        bpy.data.objects.remove(o, do_unlink=True)
        ndon += 1
c = bpy.data.collections.get("WV_KITSRC")
if c is not None:
    bpy.data.collections.remove(c)
if ndon:
    log("CLEAN", "%d kit donors deleted" % ndon, "they stand at the world origin, "
        "which is inside the Boatyard, and hide_render does not stop a glTF export")

print("\n--- inventory of the SAVED state (finding 117: count the file) -------")
from collections import Counter
grp = Counter()
for o in bpy.data.objects:
    for p in ("wv_hut_", "wv_clut_", "wv_cloth_", "veg_wv_", "veg_nl_", "nl_dress_",
              "nl_moor_", "wv_", "nl_"):
        if o.name.startswith(p):
            grp[p] += 1
            break
for k in sorted(grp):
    print("    %-16s %4d" % (k + "*", grp[k]))
print("    %-16s %4d" % ("TOTAL", sum(grp.values())))
print("    %-16s %4d" % ("objects in file", len(bpy.data.objects)))
print("    %-16s %4d" % ("materials", len(bpy.data.materials)))

bad = audit_gltf_safe([o for o in bpy.data.objects
                       if o.name.startswith(("wv_", "nl_", "veg_wv_", "veg_nl_"))])
print("\n--- glTF SAFETY (the 516-white-primitives gate) ----------------------")
if bad:
    for n, why in bad[:20]:
        print("    !! %-30s %s" % (n, why))
    raise SystemExit("%d objects would export white or untextured" % len(bad))
print("    all %d objects carry Col + UVMap and an exporter-writable material"
      % sum(1 for o in bpy.data.objects
            if o.name.startswith(("wv_", "nl_", "veg_wv_", "veg_nl_")) and o.type == 'MESH'))

print("\n" + "=" * 78)
print("WEAVE BUILD: %d log lines, phases %s" % (len(LOG), sorted(DO & set(PHASES))))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
