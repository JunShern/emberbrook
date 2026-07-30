"""lk_build.py — THE LOCKHEAD (parcel `p-lockhead`), Odessa's working post.

  Blender -b tools/blends/dellhollow-master.blend -P tools/lk_build.py \
      --python-exit-code 1 -- save

Dellhollow's east overlook: a timber jetty pinned to a cut bank 12 m above Lock
Five, where the senior lockkeeper works.  Built IN THE LIVE MASTER under serial
custody, ADDITIVE ONLY: every object is `lk_*` (foliage `veg_lk_*`, lamps
`KEYL_*`) in the `DIST_lockhead*` collections.  The only permitted deletion is
this parcel's own `lm_` blockout shell, recorded in
`tools/blends/districts/lockhead_deletions.json`, which ACCUMULATES and is never
rewritten empty by a re-run (finding 115).

--------------------------------------------------------------------------------
THIS FILE IS MEANT TO BE READ AS THE DISTRICT-CUSTODY TEMPLATE
--------------------------------------------------------------------------------
The order below is the order every district in this town has been built in, and
each step exists because skipping it produced a specific defect somewhere in the
master.  A new custodian can copy this file, change the parcel constants at the
top, and keep the guarantees:

  0   materials      derive()-by-name off the town's textured set: no procedural
                     node tree may reach glTF (the survival gate)
  0a  idempotence    clear this district's objects AND its orphan light
                     datablocks, so a re-run is a rebuild and lamp names never
                     drift (finding 115 corollary)
  0b  deletions      only this parcel's own `lm_` shells, into an accumulating
                     manifest
  0c  render-hide    this parcel's walk/bar ribbons.  `hide_render` leaves the
                     mesh BIT-IDENTICAL (the 367/367 gate) and viewport-visible
                     (the glTF exporter reads viewport visibility)
  1   measurement    the walk graph and the terrain are READ, never assumed:
                     every height in this file comes from a face plane or a ray
  2   surface        the route's own floor, laid 50 mm UNDER the walk top so the
                     master's down-ray still lands on canonical topology
                     (finding 90); setts where the ground is close, boards where
                     it flies
  3   substructure   what carries the boards — BELOW the walk plane, where the
                     QA's down-ray and headroom ray cannot see it
  4   descent        the exit route dressed as treads, or the player walks on
                     invisible floor
  5   bank           the cut-bank revetment: what makes the route read as a route
  6   rim            the rail at the drop (VISUAL ONLY — collision is the map's)
  7   station        the person who works here, and their tools
  8   clutter        the working life of the place
  9   light          ordinary warm practicals, solved wattage, measured spill
  10  vegetation     the same crossed-quad language as the neighbouring family

THE TWO RULES THAT GOVERN EVERY PLACEMENT IN A MASTER-BLEND DISTRICT
  * Nothing solid may stand ON a walk polygon or within CORRIDOR_H above one.
    That is finding 93 (`lm_notice-board` and `lm_lockhead` both stood dead
    centre of their own pads) and it is what `free_box()` below enforces.
  * A solid BELOW a walk plane is invisible to the gate — the down-ray starts
    0.90 m above the walk face and the headroom ray goes up — which is exactly
    why the whole substructure of this district lives under the boards.

WHAT WAS MEASURED HERE, AND WHY THE BUILD HAS THE SHAPE IT HAS
  With `walk_*`/`bar_*`/`lm_*` masked, the first surface under this parcel's
  route is: `lf_ground` 0.1..0.4 m below the SOUTH half of the approach (bedded),
  but 1.9..3.7 m below its NORTH half, 0.8..3.4 m below the pad's north half,
  and 1..2.5 m below the whole descending route to the Keepers' Cottage.  So the
  lockhead is a LEDGE for half its width and a CANTILEVER for the other half —
  which is also what the parcel camera's own note calls it ("Odessa's post on
  its jetty of deck") — and render-hiding the ribbons without laying structure
  under them would have swapped a gray ribbon for invisible floor over a 12 m
  drop.  See `docs/plans/lockhead-station-design.md` and `lockhead-prep.md`.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          M, world_bbox, dist_poly2, point_in_poly, plane_z_fn, plank_fill)

SAVE = "save" in sys.argv
COLL = "DIST_lockhead"
COLL_DECK = "DIST_lockhead_DECK"
COLL_PROPS = "DIST_lockhead_PROPS"
COLL_VEG = "DIST_lockhead_VEG"
DELETIONS = REPO + "/tools/blends/districts/lockhead_deletions.json"
rng = random.Random(20260730)

# ----------------------------------------------------------- parcel constants
# `public/townmap/dellhollow.map.json`, parcel `p-lockhead` (the map is the
# authority on bounds, class and staffing: class prop / kind post, staffedBy
# odessa — a STATION, not a dwelling, so nothing here is enterable).
PARCEL = (76.20, 85.20, 11.50, 20.50, 12.50, 17.50)
# The build region is wider than the parcel in x because this parcel's route
# ARRIVES from the market (x 75.15) and LEAVES to the Keepers' Cottage (x 86.1);
# the ribbons that cross the boundary are this custody's debt either way.
X0, X1, Y0, Y1 = 74.40, 86.80, 12.55, 18.60
FLOOR = 14.00                   # every pad/ribbon on this tier reads 13.92..14.07
DROP = 0.050                    # surface laid this far UNDER the walk top
MARG = 0.72                     # how far a laid surface reaches past a walk edge
LAP = 0.62                      # ground within this of the surface -> bedded (setts)
CORRIDOR_H = 2.05               # the headroom band the master's QA measures
BAND = (13.75, 14.15)           # a walk top in this band is the LEVEL route
GROUND_Y_MIN = 12.60            # `lf_ground` ends at y=12.50: VOID beyond it
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-26s %s" % (kind, what, why))


print("=" * 78)
print("THE LOCKHEAD  —  parcel p-lockhead   (Odessa's post, floor z = %.2f)" % FLOOR)
print("=" * 78)

# =========================================================================
# 0. MATERIALS — the quay-market family, by name
# =========================================================================
# `derive()` returns an EXISTING material when one of that name is already in the
# file, so reusing `mat_qm_*` costs no datablocks; the arguments only matter the
# first time a name is created.  `lockhead-prep.md` confirmed this is the right
# family: this parcel is the market's own east end and shares its timber, stone
# and paint.  Findings 95/105: a flat Principled colour is not a dark surface, it
# is an UNTEXTURED one — an image texture times a constant is the ONLY tinting
# form that survives glTF (baseColorTexture * baseColorFactor).
def derive(src, name, scale=None, tint=None, fac=0.85, mode='MULTIPLY'):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials[src].copy()
    m.name = name
    m.use_fake_user = True
    nt = m.node_tree
    if scale:
        for n in nt.nodes:
            if n.type == 'MAPPING':
                n.inputs['Scale'].default_value = (scale, scale, scale)
    if tint:
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        sock = bsdf.inputs["Base Color"]
        if sock.is_linked:
            up = sock.links[0].from_socket
            nt.links.remove(sock.links[0])
            mx = nt.nodes.new('ShaderNodeMix')
            mx.data_type = 'RGBA'
            mx.blend_type = mode
            mx.inputs[0].default_value = fac
            mx.inputs[7].default_value = (*tint, 1.0)
            nt.links.new(up, mx.inputs[6])
            nt.links.new(mx.outputs[2], sock)
    return m


def flat_emissive(name, rgb, strength, base=(0.05, 0.02, 0.01)):
    """A flat Principled emitter.  Flat because glTF carries `emissiveFactor` and
    nothing at all of a noise tree; the unevenness of a fire comes from having a
    few of these at a few strengths, never from a procedural ramp."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1.0)
    b.inputs["Roughness"].default_value = 0.65
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


MPAVE = derive("mat_rock", "mat_qm_paving", scale=1.90, tint=(0.46, 0.46, 0.49))
MSTONE = derive("mat_rock", "mat_qm_stone", scale=2.05, tint=(0.50, 0.51, 0.56))
MSTONED = derive("mat_rock", "mat_qm_stone_dark", scale=1.75, tint=(0.27, 0.28, 0.33))
MDECKB = derive("mat_deck", "mat_qm_deck", scale=1.55, tint=(0.62, 0.55, 0.44))
MSACK = derive("mat_timber", "mat_qm_sack", scale=1.90, tint=(0.74, 0.63, 0.44))
MRED = derive("mat_wallwood", "mat_qm_paint_red", scale=2.40, tint=(0.66, 0.19, 0.13))
MOCHRE = derive("mat_wallwood", "mat_qm_paint_ochre", scale=2.40, tint=(0.66, 0.49, 0.24))
MBONE = derive("mat_wallwood", "mat_qm_paint_bone", scale=2.40, tint=(0.78, 0.74, 0.62))
MGREEN = derive("mat_wallwood", "mat_qm_paint_green", scale=2.40, tint=(0.24, 0.44, 0.28))
# Two surfaces the family has no answer for.  Both are an image texture times a
# constant or a flat Principled, so both survive the round trip.
MSLATE = derive("mat_rock", "mat_lk_slate", scale=7.00, tint=(0.19, 0.20, 0.23))
MEMBER = flat_emissive("mat_lk_ember", (1.0, 0.34, 0.07), 5.5)

MIRON, MROPE = M("mat_iron"), M("mat_rope")
MT, MTD, MFRESH = M("mat_timber"), M("mat_timber_dark"), M("mat_freshwood")
MCANVAS, MGLASS = M("mat_canvas"), M("mat_lantern_glass")
MFERN, MGRASS = M("mat_fern"), M("mat_grass")

# =========================================================================
# 0a. IDEMPOTENCE — a re-run is a REBUILD
# =========================================================================
for c in (COLL, COLL_DECK, COLL_PROPS, COLL_VEG):
    coll(c)
killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("lk_", "veg_lk_", "KEYL_", "fx_lk_")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
# ... AND THE LIGHT DATABLOCKS THEY LEFT BEHIND.  Removing an object does not
# remove its data, so `bpy.data.lights.new("KEYL_lantern_0_light")` on the next
# run collides with the orphan and Blender hands back `..._light.001`.  The scene
# is unharmed but the LAMP NAMES stop being stable across runs, and a district
# whose script is its source of truth cannot have names that depend on how many
# times it has been run.
orphans = 0
for d in list(bpy.data.lights):
    if d.name.startswith("KEYL_") and d.users == 0:
        bpy.data.lights.remove(d)
        orphans += 1
if killed or orphans:
    log("REBUILD", "%d objects, %d orphan lights" % (killed, orphans),
        "cleared: idempotent re-run, and lamp names stay stable")

# =========================================================================
# 0b. DELETIONS — the blockout shell this district replaces
# =========================================================================
# `lm_lockhead` is a 0.80 m gray box standing DEAD CENTRE of `walk_pad_lockhead`,
# straddling `walk_e_lockhead__keepers-cottage_l0` and sitting on the ladder
# head.  It is the same finding-93 error as `lm_notice-board`: the pad is where
# the PLAYER stands, not where the landmark goes.  In the region gate it was 4
# headroom samples (1.65% of the surface).  Canon (user-ratified 2026-07-30):
# Odessa lives at the Keepers' Cottage; the lockhead is her working POST, not a
# hut — so the shell is replaced by a STATION, and there is no new building.
DEL_NAMES = ("lm_lockhead",)
prev = {}
if os.path.exists(DELETIONS):
    try:
        prev = {d["name"]: d for d in json.load(open(DELETIONS)).get("deleted", [])}
    except Exception as e:
        print("!! could not read the existing deletions manifest:", e)
deleted = list(prev.values())
found = 0
for o in list(bpy.data.objects):
    if o.name.startswith(DEL_NAMES):
        b = world_bbox(o)
        deleted = [d for d in deleted if d["name"] != o.name] + [{
            "name": o.name,
            "bbox_min": [round(v, 3) for v in (b[0], b[2], b[4])],
            "bbox_max": [round(v, 3) for v in (b[1], b[3], b[5])],
            "landmark": "lockhead", "verts": len(o.data.vertices)}]
        bpy.data.objects.remove(o, do_unlink=True)
        found += 1
os.makedirs(os.path.dirname(DELETIONS), exist_ok=True)
json.dump({
    "district": "the-lockhead",
    "parcel": "p-lockhead",
    "blend": "tools/blends/dellhollow-master.blend (LIVE master, serial custody)",
    "rule": "ADDITIVE-ONLY except lm_ blockout shells of p-lockhead's own members. "
            "This file ACCUMULATES and is never rewritten empty by a rebuild "
            "(manifest finding 115).",
    "note": "lm_lockhead stood dead centre of walk_pad_lockhead (finding 93) and "
            "cost the region gate 4 headroom samples. Canon 2026-07-30: Odessa is "
            "the senior lockkeeper, lives at the Keepers' Cottage with Maren, and "
            "the lockhead is her working POST (map: class prop / kind post / "
            "staffedBy odessa) — so it is replaced by a station and NOT by a "
            "building, which needs no map topology change.",
    "deleted": sorted(deleted, key=lambda d: d["name"]),
}, open(DELETIONS, "w"), indent=1)
log("DELETE", "%d lm_ shells (%d now)" % (len(deleted), found),
    "recorded in districts/lockhead_deletions.json")

# =========================================================================
# 0c. RENDER-HIDE this parcel's blockout ribbons
# =========================================================================
# The west-branch merge custodian render-hid 118 ribbons BY MAP PARCEL BOUNDS;
# p-lockhead was still gray then, so its own were never done and they RENDER —
# gray `m_wood` slabs where this district's boards belong.  `hide_render` is NOT
# a geometry edit: the mesh stays bit-identical for the 367/367 gate, and the
# gate re-checks that every hidden walk is still VIEWPORT-visible because that is
# what the glTF exporter reads.
#
# Two passes, because parcel bounds alone are not enough here: the approach
# ribbon's centre is in p-quay-mkt and the last descent step's centre is 70 mm
# east of the parcel edge, yet both are unambiguously this route's floor.
EXTRA_HIDE = ("walk_e_market-stalls__lockhead_l1", "walk_e_market-stalls__lockhead_l2",
              "walk_pad_lockhead",
              "walk_e_lockhead__keepers-cottage_l0", "walk_e_lockhead__keepers-cottage_l1",
              "walk_e_lockhead__keepers-cottage_l2", "walk_e_lockhead__keepers-cottage_l3",
              "walk_e_lockhead__keepers-cottage_l4", "walk_e_lockhead__keepers-cottage_l5")
hid = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(("walk_", "bar_")):
        continue
    b = world_bbox(o)
    c = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)
    inside = (PARCEL[0] <= c[0] <= PARCEL[1] and PARCEL[2] <= c[1] <= PARCEL[3]
              and PARCEL[4] <= c[2] <= PARCEL[5])
    if (inside or o.name in EXTRA_HIDE) and not o.hide_render:
        o.hide_render = True
        o.hide_viewport = False          # ... and it MUST stay viewport-visible
        hid.append(o.name)
log("HIDE", "%d walk_/bar_ ribbons" % len(hid),
    "by parcel bounds + the prep doc's list; geometry untouched, all still "
    "viewport-visible so the GLB keeps them")
for n in sorted(hid):
    print("             %s" % n)

# =========================================================================
# 1. MEASUREMENT — the walk graph and the terrain, READ not assumed
# =========================================================================
# A walk FACE (not object) is the unit, because the map's ribbons interleave: the
# pad stands up to 0.30 m over the first two steps of the descent, and the
# master's QA calls those samples BURIED and skips them.  Anything this build
# decides about a face has to use the same rule, or the surface either grows a
# hole in the middle of the pad (too strict) or caps a live flight (too loose).
class Face:
    __slots__ = ("poly", "fn", "zmin", "zmax", "name")

    def __init__(self, poly, name):
        self.poly = poly
        self.fn = plane_z_fn(poly)
        self.zmin = min(p.z for p in poly) - 0.02
        self.zmax = max(p.z for p in poly) + 0.02
        self.name = name

    def at(self, x, y):
        """The face's plane, CLAMPED to its own z range: a 1:2.5 flight
        extrapolated 0.7 m past its edge is 0.28 m of pure fiction."""
        return min(max(self.fn(x, y), self.zmin), self.zmax)


def nearest_on_poly(x, y, pts):
    """(px, py, d) — the closest point ON the polygon, and the distance to it."""
    if point_in_poly(x, y, pts):
        return x, y, 0.0
    best, bp = 1e9, (x, y)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b.x - a.x, b.y - a.y
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - a.x) * dx + (y - a.y) * dy) / L2))
        px, py = a.x + t * dx, a.y + t * dy
        d = math.hypot(x - px, y - py)
        if d < best:
            best, bp = d, (px, py)
    return bp[0], bp[1], best


FACES, LEVEL = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(("walk_", "bar_")):
        continue
    b = world_bbox(o)
    if b[1] < X0 - 2 or b[0] > X1 + 2 or b[3] < Y0 - 2 or b[2] > Y1 + 3:
        continue
    Mx = o.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    for p in o.data.polygons:
        if (N @ p.normal).normalized().z <= 0.5:
            continue
        f = Face([Mx @ o.data.vertices[i].co for i in p.vertices], o.name)
        FACES.append(f)
        if BAND[0] <= (f.zmin + f.zmax) / 2 <= BAND[1]:
            LEVEL.append(f)
log("READ", "%d walk faces" % len(FACES),
    "%d of them on the LEVEL route (top in %.2f..%.2f)" % (len(LEVEL), *BAND))


def eff_top(x, y):
    """The EFFECTIVE walk top over a point — the highest walk face covering it,
    which is the surface the master's QA actually rays against (finding 36)."""
    best = None
    for f in FACES:
        if point_in_poly(x, y, f.poly):
            z = f.at(x, y)
            if best is None or z > best:
                best = z
    return best


def free_box(x0, x1, y0, y1, z0, z1, pad=0.08, h=CORRIDOR_H):
    """May a SOLID occupy this box?  RULE (finding 93 + the master's headroom
    check): its footprint may overlap a walk polygon only if the box is entirely
    below that face (the down-ray starts 0.90 m above and never sees it) or
    entirely more than `h` above it.

    `pad` is 80 mm and that number was ARGUED WITH.  The gate samples only points
    INSIDE a walk polygon with a vertical ray, so 80 mm of clearance is all the
    gate needs and it is also all a prop needs not to clip the player's feet.
    The first cut used 0.20 and it refused Odessa's ENTIRE station: the free
    pocket south of `walk_pad_lockhead` is 0.65 m deep, and a 0.20 m cordon on a
    0.65 m pocket leaves 0.45 m, which fits nothing a person works at.  Anything
    that wants a real cordon (vegetation the player would brush through) asks for
    it explicitly."""
    sx = max(2, int((x1 - x0) / 0.25) + 1)
    sy = max(2, int((y1 - y0) / 0.25) + 1)
    pts = [(x0 + (x1 - x0) * i / (sx - 1.0), y0 + (y1 - y0) * j / (sy - 1.0))
           for i in range(sx) for j in range(sy)]
    for f in FACES:
        for (x, y) in pts:
            px, py, d = nearest_on_poly(x, y, f.poly)
            if d > pad:
                continue
            t = f.at(px, py)
            e = eff_top(px, py)
            if e is not None and e > t + 0.05:
                continue                      # buried face: the QA skips it too
            if z1 > t - 0.03 and z0 < t + h:
                return False
    return True


# ---------------------------------------------------------------- the terrain
def bvh_of(pred):
    verts, polys = [], []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not pred(o.name):
            continue
        Mx = o.matrix_world
        base = len(verts)
        verts.extend([Mx @ v.co for v in o.data.vertices])
        for p in o.data.polygons:
            polys.append([base + i for i in p.vertices])
    return BVHTree.FromPolygons(verts, polys, all_triangles=False) if polys else None


# What this district may FOUND on: the bank and the decks below it, and nothing
# else.  A pile driven on "whatever the ray hits" goes through a weaver's roof
# (finding 97), so the huts, the Weave's stairs, the map's iron ladder and every
# scatter object are keep-outs, not foundations.
GBVH = bvh_of(lambda n: n.startswith(("lf_ground", "lf_planking", "lf_joists")))
KBVH = bvh_of(lambda n: n.startswith(("wv_hut", "wv_stair", "wv_clut", "wv_props",
                                      "lf_clut", "lf_ladder_iron", "e_lockhead__",
                                      "veg_wv_", "veg_lf_")))
assert GBVH is not None, "no terrain to found on — is this the right blend?"


def gz(x, y, from_z=34.0):
    """Terrain top under (x, y), or None."""
    hit = GBVH.ray_cast(Vector((x, y, from_z)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else None


def clear_of(a, b, r=0.17, bvh=None):
    """Is the segment a->b clear of the keep-out soup?  Sampled, because a bbox
    test on `lf_ladder_iron` (6 x 11 x 12 m for a 0.4 m ladder) would veto the
    whole north-east quadrant of the pad."""
    bvh = bvh or KBVH
    if bvh is None:
        return True
    a, b = Vector(a), Vector(b)
    n = max(2, int((b - a).length / 0.22) + 1)
    for i in range(n + 1):
        p = a.lerp(b, i / float(n))
        loc, nor, idx, d = bvh.find_nearest(p, r)
        if loc is not None:
            return False
    return True


# =========================================================================
# 2. THE SURFACE — the route's own floor
# =========================================================================
# ONE sheet, TWO materials, and deliberately not two objects: the setts and the
# boards meet along a line the terrain draws (wherever the bank falls more than
# LAP under the walk), and two sheets built from two node dicts would leave a
# 0.30 m gap at that line, because a cell needs all four of its corners.
def route_ref(x, y):
    """(plane z of the nearest LEVEL walk face, distance to it)."""
    bz, best = None, 1e9
    for f in LEVEL:
        px, py, d = nearest_on_poly(x, y, f.poly)
        if d < best:
            best, bz = d, f.at(px, py)
    return bz, best


def lay(x, y):
    """The height a laid surface may have at (x, y), or None to lay none."""
    z, d = route_ref(x, y)
    if z is None or d > MARG:
        return None
    zz = z - DROP
    for f in FACES:
        px, py, dd = nearest_on_poly(x, y, f.poly)
        if dd > 0.55:
            continue
        t = f.at(px, py)
        e = eff_top(px, py)
        if e is not None and e > t + 0.05:
            continue                     # buried under a higher walk: ignore it
        # A live face more than 0.22 m BELOW us is a flight dropping away.  The
        # surface stops at the head of it rather than cascading down it, and the
        # dressed treads of section 4 take over — capping instead would drag the
        # whole sheet down the stair (the quay market lost its deck to z 8.53
        # that way).
        if t < zz - 0.22:
            return None
        zz = min(zz, t - DROP)
    return zz


ST = 0.30
NX = int(round((X1 - X0) / ST)) + 1
NY = int(round((Y1 - Y0) / ST)) + 1
NODE = {}
npave = ndeck = nburied = nladder = 0
for i in range(NX):
    for j in range(NY):
        x, y = X0 + i * ST, Y0 + j * ST
        if y < GROUND_Y_MIN:
            continue                     # lf_ground ends at 12.50: void beyond
        zz = lay(x, y)
        if zz is None:
            continue
        g = gz(x, y)
        if g is not None and g > zz - 0.04:
            nburied += 1
            continue                     # the bank is already above the paving
        kind = 1 if (g is not None and zz - g <= LAP) else 2
        zb = (g - 0.22) if kind == 1 else (zz - 0.16)
        # THE LADDER COMES THROUGH THE DECK.  `e_lockhead__lock-five_rung00` tops
        # out at 14.13, 0.14 m over this surface, and the iron stiles behind it
        # pass through the slab's own 0.16 m for about 0.3 m of their length.  A
        # deck has a slot where its ladder comes up; this is that slot, and it is
        # 2 cells wide.
        if not clear_of((x, y, zb), (x, y, zz), r=0.13):
            nladder += 1
            continue
        NODE[(i, j)] = (x, y, zz, zb, kind)
        npave += kind == 1
        ndeck += kind == 2


# 2b. THE WORKING TERRACE — and it exists because a MEASUREMENT killed the plan.
# The design note called x 82.5..84.5 at y ~ 15.0 a flat shelf at pad level, read
# off a single row of ground samples.  It is not a shelf: the bank falls 1.2 m per
# metre of y through it exactly as it does everywhere else here (14.54 at y 14.5,
# 13.94 at 15.0, 13.33 at 15.5), and `flat_enough()` refused every prop the station
# tried to stand on it.  So the station gets a LEVEL LEDGE, laid where the terrain
# already passes through pad level and retained on its north edge by the revetment
# that section 5 puts there anyway — which is how you get a working platform on a
# bank in the real world, and it is the same masonry-bench move the quay market
# makes one district west.
TERRACE = (82.15, 84.40, 14.55, 15.50)
TERRACE_Z = 13.98
nterr = 0
for i in range(NX):
    for j in range(NY):
        x, y = X0 + i * ST, Y0 + j * ST
        if (i, j) in NODE or not (TERRACE[0] <= x <= TERRACE[1]
                                  and TERRACE[2] <= y <= TERRACE[3]):
            continue
        g = gz(x, y)
        if g is None or not (TERRACE_Z - 0.44 <= g <= TERRACE_Z + 0.16):
            continue
        zb = min(g, TERRACE_Z) - 0.28
        if not free_box(x - 0.16, x + 0.16, y - 0.16, y + 0.16, zb, TERRACE_Z):
            continue
        NODE[(i, j)] = (x, y, TERRACE_Z, zb, 1)
        nterr += 1
log("BUILD", "terrace nodes x%d" % nterr, "a level ledge at z %.2f laid where the "
    "bank itself passes through pad level (x %.2f..%.2f, y %.2f..%.2f) — Odessa's "
    "working corner, retained on its north edge by the revetment"
    % (TERRACE_Z, TERRACE[0], TERRACE[1], TERRACE[2], TERRACE[3]))


def sheet(nodes, nx, ny, name, mats, mi_fn, cname):
    """top + bottom + skirt from a node dict keyed (i, j).  The town's standard
    ground/surface builder (shelf -> quay market -> here)."""
    V, F, MI = [], [], []
    topi, boti = {}, {}
    for k, nd in nodes.items():
        topi[k] = len(V); V.append((nd[0], nd[1], nd[2]))
        boti[k] = len(V); V.append((nd[0], nd[1], nd[3]))

    def cell(i, j):
        return all((i + a, j + c) in nodes for a, c in ((0, 0), (1, 0), (1, 1), (0, 1)))

    for i in range(nx - 1):
        for j in range(ny - 1):
            if not cell(i, j):
                continue
            a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
            F.append((topi[a], topi[b], topi[c], topi[d]))
            MI.append(mi_fn([nodes[k] for k in (a, b, c, d)]))
            F.append((boti[d], boti[c], boti[b], boti[a])); MI.append(0)
            for (na, nb, oi, oj) in ((a, d, -1, 0), (b, c, 1, 0), (a, b, 0, -1), (d, c, 0, 1)):
                if cell(i + oi, j + oj):
                    continue
                F.append((topi[na], topi[nb], boti[nb], boti[na])); MI.append(0)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F)
    me.validate()
    for m in mats:
        me.materials.append(m)
    for p, mi in zip(me.polygons, MI):
        p.material_index = min(mi, len(mats) - 1)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    link(ob, cname)
    return ob, len(F)


SURFACE, nsf = sheet(NODE, NX, NY, "lk_surface", (MTD, MPAVE, MDECKB),
                     lambda ns: 2 if any(n[4] == 2 for n in ns) else 1, COLL_DECK)
_zs = [n[2] for n in NODE.values()]
log("BUILD", "lk_surface", "%d nodes / %d faces, top z %.2f..%.2f, %.0f mm under "
    "the walk top so the master's down-ray still lands on canonical topology "
    "(finding 90). %d sett nodes where the bank is within %.2f m, %d BOARD nodes "
    "where it flies; %d nodes refused because the bank is already above the "
    "paving, %d for the ladder's slot."
    % (len(NODE), nsf, min(_zs), max(_zs), DROP * 1000, npave, LAP, ndeck,
       nburied, nladder))

# WHERE THIS DISTRICT ACTUALLY LAID A SURFACE.  Props, rails and lamps stand on
# the boards, not on the terrain 3 m under them — `gz()` at the deck's outer edge
# answers `lf_ground` at z 8.4 and a rail that believed it would refuse every
# post out there (the quay market lost its first rail exactly so).
SURF = {}
for nd in NODE.values():
    SURF[(round(nd[0] / 0.25), round(nd[1] / 0.25))] = (nd[2], nd[4])


def surf_top(x, y, r=2):
    bi, bj = round(x / 0.25), round(y / 0.25)
    best = None
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            v = SURF.get((bi + di, bj + dj))
            if v is not None and (best is None or v[0] > best):
                best = v[0]
    return best


def surf_kind(x, y, r=1):
    """1 = setts on ground (bedded paving or the terrace), 2 = boards over the
    drop.  Only the boards have a rail to stay inboard of."""
    bi, bj = round(x / 0.25), round(y / 0.25)
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            v = SURF.get((bi + di, bj + dj))
            if v is not None:
                return v[1]
    return None


def stand_z(x, y):
    """The height a prop's feet sit at: this district's own surface if it laid
    one here, else the terrain."""
    v = surf_top(x, y, r=1)
    return v if v is not None else gz(x, y)


# =========================================================================
# 3. SUBSTRUCTURE — what carries the boards, all of it BELOW the walk plane
# =========================================================================
def beam_run(tag, a, b, w, h, mat, cname, step=0.30):
    """A beam broken into its CLEAR stretches.  A single beam from a to b would
    be simpler and would drive itself through the map's iron ladder; a keep-out
    test that vetoes the whole beam would leave the deck unsupported.  Real
    joisting is trimmed around an opening, which is what this is."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    if L < 0.35:
        return []
    n = max(1, int(L / step))
    runs, cur = [], None
    for i in range(n):
        p = a.lerp(b, i / float(n))
        q = a.lerp(b, (i + 1) / float(n))
        if clear_of(p, q, r=max(w, h) * 0.5 + 0.09):
            cur = [p, q] if cur is None else [cur[0], q]
        elif cur is not None:
            runs.append(cur); cur = None
    if cur is not None:
        runs.append(cur)
    out = []
    for (p, q) in runs:
        if (q - p).length >= 0.35:
            bm_ = beam(tag, p, q, w, h, mat, cname)
            if bm_:
                out.append(bm_)
    return out


# BEARERS.  Where the bank is within reach a POST is driven; where it is not, the
# member RAKES back south into the rock — which is both the only structure that
# can land (the bank falls 3 m per metre north of the pad) and the truthful
# reading of a jetty pinned to a cut bank.  Every landing is a ray, never a
# constant, so a rebuilt bank re-fits this deck automatically.
npost = nrake = nfail = 0
POST_MAX, RAKE_MAX = 5.20, 4.20


def found(x, y, ztop, r=0.115):
    """Carry (x, y, ztop) down to the rock.  Post first, rake second, nothing
    third — and 'nothing' is logged, never faked."""
    global npost, nrake, nfail
    g = gz(x, y)
    if g is not None and 0.30 < ztop - g <= POST_MAX and clear_of((x, y, g), (x, y, ztop)):
        p = cyl("po", (x, y, g - 0.18), (x, y, ztop), r, 8, MTD, COLL_DECK)
        npost += 1
        return [p] if p else []
    s = 0.35
    while s <= RAKE_MAX:
        yy, zz = y - s, ztop - s
        gg = gz(x, yy)
        if gg is not None and gg >= zz - 0.10 and clear_of((x, y, ztop), (x, yy, gg - 0.10)):
            p = cyl("ra", (x, y, ztop), (x, yy, gg - 0.16), r * 0.92, 7, MTD, COLL_DECK)
            nrake += 1
            return [p] if p else []
        s += 0.30
    nfail += 1
    return []


DECKN = {k: v for k, v in NODE.items() if v[4] == 2}
parts_j, parts_b = [], []
njoist = 0
# JOISTS RUN NORTH-SOUTH, one every third column (0.90 m), because that is the
# direction the load has to go: the flying half of this deck bears on the cut
# bank at its south end and on posts or rakers at its north.  The first cut ran
# them east-west along the lip and, because the decked band is a DIAGONAL (the
# approach ribbon runs ENE), a single global row selection left whole columns of
# boards over nothing.
for i in sorted({i for (i, j) in DECKN}):
    if i % 3:
        continue
    js = sorted(j for (ii, j) in DECKN if ii == i)
    runs, s = [], None
    for k, j in enumerate(js):
        if s is None:
            s = j
        if k + 1 == len(js) or js[k + 1] != j + 1:
            runs.append((s, j)); s = None
    for (j0, j1) in runs:
        if j1 - j0 < 1:
            continue
        x = DECKN[(i, j0)][0]
        zt = min(DECKN[(i, j)][3] for j in range(j0, j1 + 1)) - 0.02
        # 0.35 m of extra bearing at the south end, into the bedded ground the
        # setts are laid on — a joist has to LAND on something.
        parts_j += beam_run("jo", (x, DECKN[(i, j0)][1] - 0.35, zt - 0.11),
                            (x, DECKN[(i, j1)][1] + 0.12, zt - 0.11),
                            0.10, 0.22, MTD, COLL_DECK)
        njoist += 1
        for j in (j1, (j0 + j1) // 2):
            nd = DECKN.get((i, j))
            if nd is not None:
                parts_b += found(nd[0], nd[1], nd[3] - 0.06)

JOISTS = join_meshes([p for p in parts_j if p], "lk_joists", COLL_DECK)
BEARERS = join_meshes([p for p in parts_b if p], "lk_bearers", COLL_DECK)
log("BUILD", "lk_joists / lk_bearers", "%d joist runs on a 0.90 m pitch, %d posts "
    "and %d raking struts founded BY RAY on lf_ground/lf_planking (%d stations "
    "found nothing in %.1f m and were left unbuilt rather than floated); the whole "
    "substructure is below the walk plane, where the gate's down-ray cannot see it"
    % (njoist, npost, nrake, nfail, RAKE_MAX))

# =========================================================================
# 4. THE DESCENT — the exit route to the Keepers' Cottage, dressed
# =========================================================================
# `..._l0..l5` fall 14.07 -> 11.92 over 5.5 m and hang 1..2.5 m over bare bank.
# They are the parcel's EXIT, they were about to be render-hidden, and a hidden
# ribbon with nothing under it is invisible floor over a drop — the legibility
# programme's bucket 1 defect, authored.  So they get treads.
DESCENT = ["walk_e_lockhead__keepers-cottage_l%d" % i for i in range(6)]
TREAD_OUT = 0.42               # how far the treads oversail the ribbon, river side
parts_t, parts_s = [], []
ntread = nleg = 0
laid_cells = set(NODE.keys())


def already_laid(x, y, z, band=0.30):
    """The flat sheet got here first AT THIS HEIGHT: do not lay a tread over it
    (two surfaces in the same place is an intersection offender, and it is also
    just wrong).  The height test matters — the first cut asked only 'is there a
    sheet near in plan', and because the sheet's edge runs right along the head of
    the flight it swallowed three flights whose treads are 0.3..0.7 m BELOW it."""
    s = surf_top(x, y, r=1)
    return s is not None and abs(s - z) < band


ribs = []
for nm in DESCENT:
    o = bpy.data.objects.get(nm)
    if o is None:
        continue
    Mx = o.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    for p in o.data.polygons:
        if (N @ p.normal).normalized().z > 0.5:
            ribs.append((nm, [Mx @ o.data.vertices[i].co for i in p.vertices]))
            break
for k, (nm, poly) in enumerate(ribs):
    c = sum(poly, Vector((0, 0, 0))) / len(poly)
    nxt = sum(ribs[k + 1][1], Vector((0, 0, 0))) / 4 if k + 1 < len(ribs) else None
    prv = sum(ribs[k - 1][1], Vector((0, 0, 0))) / 4 if k else None
    D = ((nxt - c) if nxt is not None else (c - prv))
    D = Vector((D.x, D.y, 0)).normalized()
    P = Vector((-D.y, D.x, 0))                        # +P is the river (north) side
    ang = math.atan2(D.y, D.x)
    zfn = plane_z_fn(poly)
    # THE TREADS RUN `TREAD_OUT` WIDER THAN THE RIBBON on the river side, and that
    # is structure, not decoration: the map's flights are walkable to their very
    # edge, so a rail post beside the treads would stand on nothing (a stray) and a
    # post on the treads is a blocked gate sample.  The flat deck solves the same
    # problem by reaching 0.72 m past its own walk edges; this is that margin,
    # sized to a flight instead of to a plaza.  Without it the whole descent rail
    # came out empty — 4 posts refused, 0 built.
    poly = [(q + P * TREAD_OUT) if (q - c).dot(P) > 0.01 else q for q in poly]
    zfn = plane_z_fn(poly)
    V, F = plank_fill(poly, ang + math.pi / 2, w=0.29, gap=0.016, thick=0.11,
                      drop=DROP, zfn=zfn, seed=k * 7 + 3,
                      keep=lambda px, py, pz: not already_laid(px, py, pz))
    if F:
        ob = new_mesh("lk_tread_%d" % k, V, F, MDECKB, COLL_DECK)
        parts_t.append(ob)
        ntread += 1
    else:
        continue
    # stringers along the flight, a riser board closing its uphill edge, and a leg
    # at the downhill end of each stringer.  HALF-WIDTH IS MEASURED off the
    # ribbon, not assumed: these quads are 1.6..1.9 m across and a 0.58 m offset
    # (the first cut) puts the stringer INSIDE the walk polygon, where the guard
    # correctly refuses the rail that stands on it.
    ts = [(q - c).dot(D) for q in poly]
    hw = max(abs((q - c).dot(P)) for q in poly)
    for side in (+1, -1):
        # the RIVER-side stringer sits close under the widened edge (the boards may
        # cantilever a little, not a lot); the bank-side one is set well in.
        inset = 0.30 if side > 0 else 0.26
        a = c + D * min(ts) + P * (side * (hw - inset))
        b = c + D * max(ts) + P * (side * (hw - inset))
        for q in (a, b):
            q.z = zfn(q.x, q.y) - 0.26
        st = beam("st", a, b, 0.09, 0.22, MTD, COLL_DECK)
        if st:
            parts_s.append(st)
        foot = b if (nxt is not None) else a
        if not already_laid(foot.x, foot.y, foot.z):
            got = found(foot.x, foot.y, foot.z - 0.06, r=0.095)
            parts_s += got
            nleg += len(got)
    up = c + D * min(ts)
    # ... and the riser hangs BELOW the tread plane (centre dropped by half its
    # depth): a riser whose top stands 0.16 m over the flight above it is a
    # blocked gate sample, which is the whole reason section 1 exists.
    up.z = zfn(up.x, up.y) - DROP - 0.23
    rb = beam("ri", up + P * (hw - 0.20), up - P * (hw - 0.20), 0.05, 0.42, MDECKB,
              COLL_DECK)
    if rb:
        parts_s.append(rb)
TREADS = join_meshes([p for p in parts_t if p], "lk_boardwalk", COLL_DECK) if parts_t else None
BWFRAME = join_meshes([p for p in parts_s if p], "lk_boardwalk_frame", COLL_DECK) if parts_s else None
log("BUILD", "lk_boardwalk", "%d flights of individual boards over ..._l0..l5 "
    "(the ones the flat sheet did not already carry), on %d stringer legs — the "
    "exit route now READS as a route instead of being a hidden ribbon over a "
    "1..2.5 m drop" % (ntread, nleg))

# =========================================================================
# 5. THE BANK — the cut-bank revetment, and the route's south edge
# =========================================================================
# `lf_ground` rises to 15.54 at (80, 13) and 16.9 at (84, 12.5): the bank stands
# 0.3..2.4 m above the route within a metre of it.  Left as raw slope it reads as
# an accident; cut and faced, it gives the route a hard south edge (bucket 2:
# ground language that distinguishes ROUTE from scenery floor), and it is what
# Odessa's board, hooks and lamp hang on.
def walk_south_edge(x):
    """The y at which this route's own floor STARTS at this x — measured by
    walking a line north until it is inside a walk polygon.  The first cut
    anchored the wall to the southernmost LAID node instead, and where the bank
    has already cut the paving's south margin away that node is INSIDE the walk
    polygon, so the guard refused the wall and 9 metres of revetment silently did
    not get built."""
    y = GROUND_Y_MIN
    while y <= Y1:
        if eff_top(x, y) is not None:
            return y
        y += 0.05
    return None


WALL = {}                      # round(x, 1) -> (face y, top z): what things hang on
wall = []
nwall = ncop = nwskip = 0
x = 74.80
while x <= 84.60:
    ys = walk_south_edge(x)
    if ys is None:
        x += 0.28
        continue
    zs = surf_top(x, ys + 0.35, r=2) or eff_top(x, ys + 0.10) or 14.0
    # step SOUTH until the wall clears the walk graph — the same search the quay
    # market's arcade used to find its wall line, done per column because this
    # route bends and a straight line would jog into it.
    yw, ok = ys - 0.14, False
    while yw > GROUND_Y_MIN and ys - yw < 1.05:
        gb = gz(x, yw - 0.95)
        top = zs + 0.16 if (gb is None or gb < zs + 0.30) else min(gb + 0.06, zs + 2.45)
        base = min(zs - 0.60, (gz(x, yw) or zs) - 0.40)
        if top - base >= 0.22 and free_box(x - 0.15, x + 0.15, yw - 0.22, yw + 0.19,
                                           base, top):
            ok = True
            break
        yw -= 0.08
    if not ok:
        nwskip += 1
        x += 0.28
        continue
    # coursing, not colour: the family's stone at two values a stop apart
    m = MSTONE if (int(x * 3.4) % 3) else MSTONED
    wall.append(obox("wc", x, yw, (base + top) / 2, 0.29, 0.36, top - base, mat=m,
                     cname=COLL))
    nwall += 1
    # A RETURN WHERE THE WALL STEPS.  East of the pad the route's south edge jumps
    # ~0.9 m south (the pad ends at x 82.03 and the descent's own ribbon takes
    # over), and a revetment that jogs without a return reads as a mistake rather
    # than as a plan.  The step is where Odessa's bench is, so the return is the
    # thing that makes the bench look built.
    if WALL:
        pk = max(WALL)
        py_, pt_ = WALL[pk]
        if x - pk < 0.45 and abs(py_ - yw) > 0.35:
            wall.append(obox("wr", (x + pk) / 2 - 0.02, (py_ + yw) / 2,
                             (base + min(top, pt_)) / 2, 0.30, abs(py_ - yw) + 0.30,
                             min(top, pt_) - base, mat=MSTONE, cname=COLL))
    WALL[round(x, 1)] = (yw, top)
    if top > zs + 0.34:                  # a coping, and a buttress every 2 m
        wall.append(obox("cp", x, yw + 0.02, top - 0.06, 0.29, 0.48, 0.14,
                         mat=MSTONE, cname=COLL))
        ncop += 1
        if abs((x * 100) % 200) < 28:
            wall.append(obox("bt", x, yw + 0.10, (base + top - 0.30) / 2, 0.40, 0.52,
                             top - 0.30 - base, mat=MSTONE, cname=COLL))
    x += 0.28
BANK = join_meshes([p for p in wall if p], "lk_bankface", COLL)
_wt = [v[1] for v in WALL.values()]
log("BUILD", "lk_bankface", "%d courses + %d coping stones (%d columns had no room), "
    "top z %.2f..%.2f — found per column by stepping south off the walk graph's own "
    "edge until it clears, so the wall follows the route where the route bends"
    % (nwall, ncop, nwskip, min(_wt) if _wt else 0, max(_wt) if _wt else 0))


def wall_at(x):
    """(face y, top z) of the revetment nearest this x — what a board, a hook, a
    shelf or a lamp bracket is actually fixed to."""
    if not WALL:
        return None
    k = min(WALL, key=lambda kx: abs(kx - x))
    return WALL[k] if abs(k - x) < 0.9 else None

# =========================================================================
# 6. THE RIM — the rail at the drop.  VISUAL ONLY.
# =========================================================================
# Collision is the map's and the map's alone (architecture canon 2026-07-29):
# these are new `lk_rail_*` visuals with no `bar_`/`walk_` prefix, placed OUTSIDE
# every walk polygon.  What they do is legibility work: north of this route the
# ground falls 3 m per metre into a 12 m plunge, and the ladder head becomes the
# one legible way over the edge instead of one of many ways off it.
# EVERYTHING PLACED FROM HERE ON REGISTERS ITS FOOTPRINT.  The corridor guard
# answers "may this stand here at all"; it says nothing about whether something of
# this district's own is already standing there, and the first gated run put a lamp
# post through a chain coil, a rail post through a crate and the work lamp through
# the desk it was lighting — 4 intersection offenders, all of them mine.
OCC = []


def spot_clear(x, y, r):
    return all((x - ox) ** 2 + (y - oy) ** 2 >= (r + orr) ** 2 for ox, oy, orr in OCC)


# ... and a 3D companion, because a plan circle is the wrong tool for anything
# BRACKETED: the work lamp hangs 0.6 m over the desk it lights, so in plan it is
# inside the desk and in space it is nowhere near it — while the same lamp at the
# same height WAS inside the chart board 0.4 m west of it (the last offender the
# geometry audit held out for).  Only a real box test can tell those apart.
MYBB = []


def remember(parts):
    for q in parts:
        if q:
            MYBB.append(world_bbox(q))


def box_free3(x0, x1, y0, y1, z0, z1, pad=0.02):
    for b in MYBB:
        if (x1 > b[0] - pad and x0 < b[1] + pad and y1 > b[2] - pad and y0 < b[3] + pad
                and z1 > b[4] - pad and z0 < b[5] + pad):
            return False
    return True


def occupy(x, y, r):
    OCC.append((x, y, r))


RAIL_X1 = 82.70
# WHERE THE MAP'S IRON LADDER CROSSES THE LIP, interpolated off its own rungs:
# rung04 centres at (81.53, 17.55) and rung05 at (81.73, 17.94), so at the deck's
# outer edge (y ~ 17.8) the ladder is at x ~ 81.66.  The opening is 1.0 m wide.
LADDER_GAP = (81.15, 82.15)
edge = []
for i in range(NX):
    js = [j for (ii, j) in NODE if ii == i]
    if not js:
        continue
    nd = NODE[(i, max(js))]
    if nd[0] > RAIL_X1:
        continue
    edge.append(Vector((nd[0], nd[1] - 0.15, nd[2])))
rail, chain = [], []
nrpost, nrskip = 0, 0
print("      (outer edge: %d points, x %.2f..%.2f, y %.2f..%.2f)"
      % (len(edge), min(p.x for p in edge), max(p.x for p in edge),
         min(p.y for p in edge), max(p.y for p in edge)) if edge else "      (no edge)")


def rail_chain(pts, maxgap=1.15, maxdz=0.45):
    """Posts every ~1.35 m with a top rail, a midrail and a kickboard between
    them; the chain BREAKS where the edge jumps, because a rail that leaps a gap
    reads as a fence someone dropped.

    `maxgap` IS A PARAMETER because the two edges this is called on are sampled
    at different pitches: the deck's outer edge comes off a 0.30 m node grid,
    while the descent gives two points per flight, 1.2..1.5 m apart.  With the
    grid's threshold every descent run was a single point and the whole flight
    rail silently came out empty."""
    global nrpost, nrskip
    out, run = [], []
    for p in pts:
        if run and ((p - run[-1]).length > maxgap or abs(p.z - run[-1].z) > maxdz):
            out.append(run); run = []
        run.append(p)
    if run:
        out.append(run)
    posts = []
    for seg in out:
        if len(seg) < 2:
            continue
        acc, keep = 0.0, [seg[0]]
        for a, b in zip(seg, seg[1:]):
            acc += (b - a).length
            if acc >= 1.35:
                keep.append(b); acc = 0.0
        if (keep[-1] - seg[-1]).length > 0.5:
            keep.append(seg[-1])
        kept = []
        for p in keep:
            if LADDER_GAP[0] < p.x < LADDER_GAP[1]:
                continue                        # the ladder head: the rail opens
            # A post the guard refuses is NUDGED OUTBOARD before it is abandoned.
            # These ribbons are diagonal quads: a post set a fixed 0.15 m in from
            # the surface's own edge is well clear of the pad and 0.02 m inside the
            # approach.  It may only move as far as there is still deck under it.
            n = 0
            while n < 4 and not free_box(p.x - 0.07, p.x + 0.07, p.y - 0.07,
                                         p.y + 0.07, p.z - 0.10, p.z + 1.06):
                if surf_top(p.x, p.y + 0.10, r=1) is None:
                    break
                p = p + Vector((0, 0.07, 0))
                n += 1
            if not free_box(p.x - 0.07, p.x + 0.07, p.y - 0.07, p.y + 0.07,
                            p.z - 0.10, p.z + 1.06):
                nrskip += 1
                continue
            rail.append(obox("rp", p.x, p.y, p.z + 0.36, 0.10, 0.10, 1.36, mat=MTD,
                             cname=COLL))
            occupy(p.x, p.y, 0.20)
            nrpost += 1
            kept.append(p)
        for a, b in zip(kept, kept[1:]):
            if (b - a).length > 2.4:
                continue
            if min(a.x, b.x) < LADDER_GAP[1] and max(a.x, b.x) > LADDER_GAP[0]:
                continue                        # never span the ladder opening
            for dz, w, h, mat in ((1.00, 0.09, 0.07, MTD), (0.56, 0.06, 0.05, MTD),
                                  (0.12, 0.04, 0.20, MDECKB)):
                bm_ = beam("rl", a + Vector((0, 0, dz)), b + Vector((0, 0, dz)), w, h,
                           mat, COLL)
                if bm_:
                    rail.append(bm_)
        posts += kept
    return posts


LIP = rail_chain(edge)
# ... and the same treatment along the descent's river side, which is the exit the
# player is meant to take: the outer edge of each flight, offset off its MEASURED
# half-width so the posts stand beside the treads and not on them.
dedge = []
for k, (nm, poly) in enumerate(ribs):
    if k < 2:
        continue           # l0/l1 lie INSIDE walk_pad_lockhead: the lip rail has them
    c = sum(poly, Vector((0, 0, 0))) / len(poly)
    nxt = sum(ribs[k + 1][1], Vector((0, 0, 0))) / 4 if k + 1 < len(ribs) else None
    prv = sum(ribs[k - 1][1], Vector((0, 0, 0))) / 4 if k else None
    D = Vector((*(((nxt - c) if nxt is not None else (c - prv)).xy), 0)).normalized()
    P = Vector((-D.y, D.x, 0))
    zfn = plane_z_fn(poly)
    ts = [(q - c).dot(D) for q in poly]
    hw = max(abs((q - c).dot(P)) for q in poly)
    for t in (min(ts) + 0.25, max(ts) - 0.25):
        # PUSHED OUT UNTIL IT IS ACTUALLY CLEAR, not by a computed constant.  `hw`
        # is the corner projection of a quad whose own axis is not exactly the
        # centre-to-centre direction, and consecutive flights overlap where they
        # meet, so `hw + a bit` lands 0.05 m INSIDE a ribbon about half the time —
        # which is how the first cut refused every descent post it drew.
        q = None
        for step in range(6):
            cand = c + D * t + P * (hw + 0.16 + 0.06 * step)
            # 0.24 m of CENTRE clearance, because the guard tests the post's
            # CORNERS: a centre 0.13 m clear puts the corner of a 0.14 m post
            # exactly on the polygon edge, and the guard refused all three posts
            # this loop had just carefully pushed out (round 5).
            if all(dist_poly2(cand.x, cand.y, f.poly) >= 0.24 for f in FACES):
                q = cand
                break
        if q is None:
            continue
        q.z = zfn(q.x, q.y) - DROP
        dedge.append(q)
rail_chain(dedge, maxgap=2.10, maxdz=0.80)
# THE LADDER HEAD'S GRAB FRAME — the one place the rail is meant to open, and the
# reason the opening reads as a way down instead of as a hole in the fence.  The
# stanchions are pinned to the two edge points either side of the gap, because
# those are the points that certainly have deck under them.
gap_posts = [p for p in LIP if abs(p.x - LADDER_GAP[0]) < 0.9
             or abs(p.x - LADDER_GAP[1]) < 0.9]
for p in gap_posts:
    if not free_box(p.x - 0.08, p.x + 0.08, p.y - 0.08, p.y + 0.08, p.z - 0.1, p.z + 1.25):
        continue
    st = cyl("gs", (p.x, p.y, p.z - 0.12), (p.x, p.y, p.z + 1.20), 0.045, 8, MIRON, COLL)
    if st:
        rail.append(st)
    hb = cyl("gh", (p.x, p.y, p.z + 1.16), (p.x, p.y - 0.50, p.z + 1.06), 0.038, 7,
             MIRON, COLL)
    if hb:
        rail.append(hb)
RAIL = join_meshes([p for p in rail if p], "lk_rail", COLL)
log("BUILD", "lk_rail", "%d posts + rails/kickboard along the whole north lip and "
    "the descent's river side (%d stations refused by the corridor guard), with the "
    "ladder head left OPEN at x %.2f..%.2f and grabbed by iron stanchions. VISUAL "
    "ONLY: no bar_/walk_ prefix, nothing over a walk polygon, collision remains "
    "the map's" % (nrpost, nrskip, LADDER_GAP[0], LADDER_GAP[1]))

# =========================================================================
# 7. ODESSA'S STATION — a place a real person works all day
# =========================================================================
# NOT a hut and NOT enterable (canon 2026-07-30, and `lockhead-prep.md` option
# 2): the deck IS her station, so the furniture rings the pad instead of standing
# on it, the mast stands on the bank BEHIND a revetment where no player could
# mistake it for somewhere to go, and no map topology changes at all.
st = []
skipped = []


def put(parts, box_, label):
    """Everything in this section goes through here: measured feet, guarded
    footprint, and a LOG line when a piece cannot be placed — a district that
    silently drops its own props is a district nobody can review."""
    if free_box(*box_):
        st.extend([p for p in parts if p])
        # the registered circle is sized off the SHORT side: a 1.4 x 0.6 m desk
        # whose circle is half its long side reserves the whole bench and the
        # working corner comes out bare.
        occupy((box_[0] + box_[1]) / 2, (box_[2] + box_[3]) / 2,
               0.42 * min(box_[1] - box_[0], box_[3] - box_[2]) + 0.06)
        remember(parts)
        return True
    skipped.append(label)
    return False


# --- the bell: how the lockhead talks to Lock Five, 12 m below -------------
# IN THE ONE POCKET THAT EXISTS AT PAD LEVEL: `walk_pad_lockhead` starts at
# y = 14.70 and the market approach ribbon ends at x = 80.90, so x 80.95..82.05 /
# y 14.02..14.62 is free ground at 13.82..14.40 — 1.10 x 0.60 m.  The A-frame is
# 0.44 m deep BECAUSE that is what fits; the first cut drew it 0.60 deep, the
# guard refused it, and a station with no bell in it is not a station.
bxx, byy = 81.30, 14.30
bz = stand_z(bxx, byy) or 13.9
if put([cyl("bl", (bxx - 0.34, byy - 0.14, bz), (bxx - 0.05, byy, bz + 1.62), 0.048, 7, MTD, COLL_PROPS),
        cyl("bl", (bxx + 0.34, byy - 0.14, bz), (bxx + 0.05, byy, bz + 1.62), 0.048, 7, MTD, COLL_PROPS),
        cyl("bl", (bxx - 0.34, byy + 0.16, bz), (bxx - 0.05, byy + 0.06, bz + 1.60), 0.042, 7, MTD, COLL_PROPS),
        cyl("bl", (bxx + 0.34, byy + 0.16, bz), (bxx + 0.05, byy + 0.06, bz + 1.60), 0.042, 7, MTD, COLL_PROPS),
        beam("bh", (bxx - 0.30, byy + 0.02, bz + 1.60), (bxx + 0.30, byy + 0.02, bz + 1.60), 0.07, 0.07, MTD, COLL_PROPS),
        cyl("bb", (bxx, byy + 0.02, bz + 1.50), (bxx, byy + 0.02, bz + 1.16), 0.085, 10, MIRON, COLL_PROPS, r2=0.20),
        cyl("bp", (bxx, byy + 0.02, bz + 1.20), (bxx, byy + 0.02, bz + 1.06), 0.030, 6, MIRON, COLL_PROPS),
        cyl("bn", (bxx + 0.02, byy + 0.02, bz + 1.10), (bxx + 0.06, byy - 0.01, bz + 0.55), 0.014, 5, MROPE, COLL_PROPS)],
       (bxx - 0.42, bxx + 0.42, byy - 0.22, byy + 0.24, bz - 0.05, bz + 1.70), "bell frame"):
    log("BUILD", "lk bell frame", "at (%.2f, %.2f) on z %.2f, lanyard to hand height"
        % (bxx, byy, bz))

# --- the working bench: the desk, the ledger, the stool, the chart board ----
# THE BENCH IS MEASURED, NOT CHOSEN.  `lf_ground` reads 13.93..13.95 across
# x 82.5..84.5 at y ~ 15.0 and 14.55 at y 14.5 — a flat shelf at PAD LEVEL, one
# step down from the pad's south-east corner, immediately south of where the
# descent to the cottage begins.  That elbow is exactly the transition the
# legibility audit says players cannot find, so that is where the person is.
BENCH = (82.35, 84.30, 14.86, 15.40)
bcx = (BENCH[0] + BENCH[1]) / 2
bcy = (BENCH[2] + BENCH[3]) / 2
w_ = wall_at(bcx)
cby = (w_[0] if w_ else 14.0)
wtop = (w_[1] if w_ else (gz(bcx, cby - 0.95) or 14.9))
dx, dy = 83.35, bcy + 0.04
dz = stand_z(dx, dy) or 13.95
put([obox("dt", dx, dy, dz + 0.80, 1.30, 0.56, 0.08, rz=0.10, mat=MDECKB, cname=COLL_PROPS),
     obox("dr", dx, dy - 0.22, dz + 0.68, 1.22, 0.10, 0.16, rz=0.10, mat=MTD, cname=COLL_PROPS)]
    + [cyl("dl", (dx + sx * 0.56, dy + sy * 0.22, dz), (dx + sx * 0.56, dy + sy * 0.22, dz + 0.78),
           0.038, 6, MTD, COLL_PROPS) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    + [obox("lg", dx - 0.28, dy + 0.04, dz + 0.87, 0.30, 0.22, 0.06, rz=0.22, mat=MBONE, cname=COLL_PROPS),
       cyl("ro", (dx + 0.30, dy - 0.08, dz + 0.87), (dx + 0.54, dy + 0.04, dz + 0.87), 0.035, 7, MSACK, COLL_PROPS),
       cyl("ro", (dx + 0.28, dy + 0.06, dz + 0.86), (dx + 0.52, dy + 0.14, dz + 0.88), 0.030, 7, MSACK, COLL_PROPS)],
    (dx - 0.70, dx + 0.70, dy - 0.32, dy + 0.32, dz - 0.05, dz + 0.92), "the lock ledger desk")
# the chart board on its own easel, facing back along the deck: the board a
# lockkeeper writes the day's levels on, and the first thing the camera reads
ebx, eby = 82.82, BENCH[2] + 0.12
ebz = stand_z(ebx, eby) or 13.95
put([obox("cf", ebx, eby + 0.10, ebz + 1.26, 1.14, 0.09, 0.86, rz=-0.42, mat=MOCHRE, cname=COLL_PROPS),
     obox("cs", ebx, eby + 0.15, ebz + 1.26, 0.98, 0.04, 0.70, rz=-0.42, mat=MSLATE, cname=COLL_PROPS),
     obox("cl", ebx, eby + 0.13, ebz + 1.72, 1.18, 0.16, 0.09, rz=-0.42, mat=MOCHRE, cname=COLL_PROPS),
     cyl("ce", (ebx - 0.34, eby + 0.06, ebz), (ebx - 0.26, eby + 0.16, ebz + 0.86), 0.040, 6, MTD, COLL_PROPS),
     cyl("ce", (ebx + 0.34, eby + 0.06, ebz), (ebx + 0.26, eby + 0.16, ebz + 0.86), 0.040, 6, MTD, COLL_PROPS),
     cyl("ce", (ebx, eby + 0.34, ebz), (ebx, eby + 0.18, ebz + 0.84), 0.038, 6, MTD, COLL_PROPS)],
    (ebx - 0.62, ebx + 0.62, eby - 0.10, eby + 0.40, ebz - 0.05, ebz + 1.78), "chart board")
sx_, sy_ = 82.55, BENCH[3] - 0.14
sz_ = stand_z(sx_, sy_) or 13.95
put([cyl("sp", (sx_, sy_, sz_ + 0.44), (sx_, sy_, sz_ + 0.50), 0.17, 10, MTD, COLL_PROPS)]
    + [cyl("sl", (sx_ + math.cos(a) * 0.13, sy_ + math.sin(a) * 0.13, sz_),
           (sx_ + math.cos(a) * 0.07, sy_ + math.sin(a) * 0.07, sz_ + 0.45), 0.026, 5, MTD, COLL_PROPS)
       for a in (0.4, 2.5, 4.6)],
    (sx_ - 0.20, sx_ + 0.20, sy_ - 0.20, sy_ + 0.20, sz_ - 0.05, sz_ + 0.54), "stool")
# THE GEAR POST: the oilskin on its hooks and the gauge glasses on a shelf.
# These were drawn on the revetment first and that was WRONG, not merely refused:
# the wall's north face sits within 0.05 m of the walk edge (the search puts it as
# close to the route as it can), so anything hung on it overhangs the floor the
# gate rays down through, and a coat over a walkway is a blocked sample.  A post
# at the bench's east end carries them both, and a lockkeeper's coat, hooks and
# gauge glasses on one post is a truer picture of a working station anyway.
gpx, gpy = BENCH[1] - 0.12, bcy - 0.06
gpz = stand_z(gpx, gpy) or 13.95
put([cyl("gp", (gpx, gpy, gpz - 0.10), (gpx, gpy, gpz + 1.94), 0.065, 7, MTD, COLL_PROPS),
     cyl("hk", (gpx, gpy, gpz + 1.72), (gpx - 0.20, gpy - 0.04, gpz + 1.74), 0.024, 5, MIRON, COLL_PROPS),
     cyl("hk", (gpx, gpy, gpz + 1.66), (gpx + 0.18, gpy + 0.06, gpz + 1.68), 0.024, 5, MIRON, COLL_PROPS),
     obox("os", gpx - 0.22, gpy - 0.06, gpz + 1.32, 0.42, 0.20, 0.76, rz=0.10, mat=MCANVAS, cname=COLL_PROPS),
     obox("os", gpx - 0.22, gpy - 0.06, gpz + 1.68, 0.30, 0.16, 0.14, mat=MCANVAS, cname=COLL_PROPS),
     obox("gs", gpx + 0.02, gpy + 0.16, gpz + 1.02, 0.44, 0.26, 0.05, mat=MDECKB, cname=COLL_PROPS)]
    + [cyl("gg", (gpx + dxx, gpy + 0.16, gpz + 1.05), (gpx + dxx, gpy + 0.16, gpz + 1.26),
           0.033, 8, MGLASS, COLL_PROPS) for dxx in (-0.13, 0.02, 0.15)],
    (gpx - 0.46, gpx + 0.26, gpy - 0.20, gpy + 0.32, gpz - 0.12, gpz + 1.98), "gear post")
GEARPOST = (gpx, gpy, gpz)
# --- the brazier: the one warm thing on a windy deck -----------------------
brx, bry = 83.90, BENCH[2] + 0.22
brz = stand_z(brx, bry) or 13.9
put([cyl("bz", (brx, bry, brz + 0.42), (brx, bry, brz + 0.66), 0.27, 12, MIRON, COLL_PROPS, r2=0.30),
     cyl("be", (brx, bry, brz + 0.60), (brx, bry, brz + 0.64), 0.24, 12, MEMBER, COLL_PROPS)]
    + [cyl("bg", (brx + math.cos(a) * 0.20, bry + math.sin(a) * 0.20, brz),
           (brx + math.cos(a) * 0.12, bry + math.sin(a) * 0.12, brz + 0.44), 0.030, 5, MIRON, COLL_PROPS)
       for a in (0.5, 2.6, 4.7)],
    (brx - 0.32, brx + 0.32, bry - 0.32, bry + 0.32, brz - 0.05, brz + 0.70), "brazier")
STATION = join_meshes([p for p in st if p], "lk_station", COLL_PROPS)
log("BUILD", "lk_station", "chart board, lock desk + ledger, stool, gauge shelf, "
    "oilskin on hooks, bell frame, brazier — all off the pad, all on measured "
    "ground, nothing enterable%s"
    % ("" if not skipped else "  (SKIPPED, footprint not free: %s)" % ", ".join(skipped)))

# --- the signal mast, on the bank shelf 1.5 m above the deck ---------------
# THE ONE DELIBERATELY UNREACHABLE THING HERE, and that is the design: a raised
# post a player can see and never reach is the floating-building defect wearing a
# hat UNLESS it is obviously not a place — a mast behind a revetment is not a
# place, it is an instrument.  It also gives the parcel camera (yaw 60, pitch 26,
# "from high over the basin") the vertical it is composed for.
mx, my = 81.88, 13.18
mg = gz(mx, my) or 15.5
mast = []
if free_box(mx - 0.20, mx + 0.20, my - 0.20, my + 0.20, mg - 0.2, mg + 4.4):
    # The plinth is BURIED, not bedded: the bank here runs at about 45 degrees
    # (16.12 at y 12.5 down to 14.39 at y 14.0), so a 0.26 m block laid on the
    # surface floats on its downhill corner.  0.95 m of it, most of it in the
    # ground, is a plinth cut into a slope.
    mast += [cyl("ms", (mx, my, mg - 0.30), (mx, my, mg + 4.30), 0.115, 10, MTD, COLL, r2=0.075),
             obox("mb", mx, my, mg - 0.24, 0.66, 0.72, 0.95, mat=MSTONE, cname=COLL),
             beam("my", (mx - 0.78, my, mg + 3.34), (mx + 0.78, my, mg + 3.34), 0.07, 0.07, MTD, COLL),
             obox("md", mx - 0.62, my + 0.06, mg + 2.92, 0.42, 0.05, 0.42, rz=0.0, mat=MRED, cname=COLL),
             obox("md", mx + 0.60, my + 0.06, mg + 2.92, 0.40, 0.05, 0.28, rz=0.0, mat=MBONE, cname=COLL),
             cyl("mh", (mx + 0.03, my + 0.02, mg + 4.24), (mx + 0.62, my + 0.05, mg + 3.06), 0.014, 5, MROPE, COLL),
             cyl("mh", (mx - 0.03, my + 0.02, mg + 4.20), (mx - 0.14, my + 0.24, mg + 0.86), 0.014, 5, MROPE, COLL),
             obox("mc", mx - 0.16, my + 0.28, mg + 0.80, 0.10, 0.22, 0.10, mat=MIRON, cname=COLL)]
    MAST = join_meshes([p for p in mast if p], "lk_mast", COLL)
    log("BUILD", "lk_mast", "signal mast at (%.2f, %.2f), foot z %.2f (1.5 m above "
        "the deck, BEHIND the revetment — an instrument, not a place), 4.3 m to the "
        "truck, yard + two day-marks + halyard to a cleat" % (mx, my, mg))
else:
    log("SKIP", "lk_mast", "footprint not free — the bank shelf is not clear")

# =========================================================================
# 8. CLUTTER — the working life of a lock station
# =========================================================================
# Lock machinery spares, because the thing this post overlooks is a machine:
# a spare paddle, a bundle of iron bar, chain, rope, a bucket, crates.
clut = []
nclut, nclut_skip = 0, 0


def flat_enough(x, y, r=0.35, tol=0.20):
    """Is the ground here flat enough to stand a crate on?  THE BANK IS NOT A
    SHELF: it runs at 45 degrees (1.15 m of fall per metre of y), and the first
    cut put six crates and a barrel up it, each of them floating on one corner
    and buried on the other.  Anything laid on this district's own surface is
    flat by construction; anything laid on terrain has to ask."""
    zs = [gz(x + dx, y + dy) for dx, dy in
          ((-r, -r), (r, -r), (r, r), (-r, r), (0, 0))]
    zs = [z for z in zs if z is not None]
    return len(zs) == 5 and (max(zs) - min(zs)) <= tol


# The footprint of each kind, so the SEARCH can test the guard instead of the
# guard vetoing whatever the search happened to like: (half-x, half-y, height).
# The first cut searched for flat, free ground and only then built the box and
# asked the guard — 13 of 15 props were refused after the fact, with no retry.
SIZE = {"crate": (0.38, 0.34, 0.50), "barrel": (0.28, 0.28, 0.84),
        "coil": (0.33, 0.33, 0.26), "chain": (0.29, 0.29, 0.20),
        "paddle": (0.38, 0.18, 1.70), "bars": (0.58, 0.22, 0.32),
        "bucket": (0.18, 0.18, 0.32)}


def prop(kind, x, y, rz=0.0, s=1.0, seek=1.25):
    """Place one prop, SEARCHING outward for a spot that is flat enough to stand
    on, has a surface under it, AND whose footprint the corridor guard accepts —
    all three tested together.  The ones that never find a spot are counted."""
    global nclut, nclut_skip
    hx, hy, hz = SIZE[kind]
    hx, hy, hz = hx * s, hy * s, hz * s
    spot = None
    r = 0.0
    while r <= seek and spot is None:
        for i in range(1 if r < 0.01 else 12):
            a = 2 * math.pi * i / 12.0
            xx, yy = x + math.cos(a) * r, y + math.sin(a) * r
            on_deck = surf_top(xx, yy, r=1) is not None
            if not on_deck and not flat_enough(xx, yy):
                continue
            # INBOARD OF THE RAIL, always.  The search is free to move a prop and
            # the first cut used that freedom to put a crate at y 18.06 — outboard
            # of the rail line, on the 0.15 m of board that overhangs the void.
            # INBOARD OF THE RAIL BY A CLEAR MARGIN.  The band between the walk
            # edge and the rail is only ~0.5 m wide, and a prop tucked into it ends
            # up inside the kickboard: 0.55 m of clearance keeps gear on the deck
            # proper, which is also where a working deck actually keeps it.
            if on_deck and surf_kind(xx, yy) == 2 \
                    and surf_top(xx, yy + hy + 0.55, r=1) is None:
                continue
            z = stand_z(xx, yy)
            if z is None:
                continue
            if not free_box(xx - hx, xx + hx, yy - hy, yy + hy, z - 0.05, z + hz):
                continue
            if not spot_clear(xx, yy, max(hx, hy) + 0.10):
                continue
            spot = (xx, yy, z)
            break
        r += 0.18
    if spot is None:
        nclut_skip += 1
        return
    x, y, z = spot
    occupy(x, y, max(hx, hy) + 0.06)
    P = []
    if kind == "crate":
        h = 0.44 * s
        P = [obox("cr", x, y, z + h / 2, 0.62 * s, 0.52 * s, h, rz=rz, mat=MDECKB, cname=COLL_PROPS),
             obox("cb", x, y, z + h - 0.03, 0.66 * s, 0.56 * s, 0.05, rz=rz, mat=MTD, cname=COLL_PROPS)]
    elif kind == "barrel":
        P = [cyl("ba", (x, y, z), (x, y, z + 0.78 * s), 0.24 * s, 12, MTD, COLL_PROPS),
             cyl("bh", (x, y, z + 0.18), (x, y, z + 0.24), 0.255 * s, 12, MIRON, COLL_PROPS),
             cyl("bh", (x, y, z + 0.56), (x, y, z + 0.62), 0.255 * s, 12, MIRON, COLL_PROPS)]
    elif kind == "coil":
        P = [cyl("co", (x, y, z + 0.04), (x, y, z + 0.10), 0.30 * s, 14, MROPE, COLL_PROPS),
             cyl("co", (x, y, z + 0.10), (x, y, z + 0.16), 0.24 * s, 14, MROPE, COLL_PROPS),
             cyl("co", (x, y, z + 0.16), (x, y, z + 0.21), 0.17 * s, 12, MROPE, COLL_PROPS)]
    elif kind == "chain":
        P = [cyl("ch", (x, y, z + 0.03), (x, y, z + 0.09), 0.26 * s, 12, MIRON, COLL_PROPS),
             cyl("ch", (x, y, z + 0.09), (x, y, z + 0.15), 0.19 * s, 12, MIRON, COLL_PROPS)]
    elif kind == "paddle":
        # a spare lock paddle, leaning: the machine's own spare part
        P = [obox("pd", x, y, z + 0.62, 0.60, 0.09, 1.24, rz=rz, mat=MDECKB, cname=COLL_PROPS),
             cyl("ps", (x, y + 0.05, z + 1.18), (x, y + 0.05, z + 1.62), 0.045, 7, MIRON, COLL_PROPS)]
    elif kind == "bars":
        P = [cyl("ib", (x - 0.5, y + 0.05 * k, z + 0.06 + 0.055 * k), (x + 0.5, y + 0.05 * k, z + 0.06 + 0.055 * k),
                 0.032, 6, MIRON, COLL_PROPS) for k in range(4)]
    elif kind == "bucket":
        P = [cyl("bu", (x, y, z), (x, y, z + 0.26), 0.13, 10, MIRON, COLL_PROPS, r2=0.15),
             cyl("bb", (x - 0.13, y, z + 0.24), (x + 0.13, y, z + 0.24), 0.012, 5, MIRON, COLL_PROPS)]
    if not P:
        return
    clut.extend([p for p in P if p])
    remember(P)
    nclut += 1


# WHERE, and it is the laid surface's own margins plus the measured bench — not
# the bank, which is a 45-degree slope and holds nothing.  The margin band between
# the walk edge and the rail is where a working deck keeps its gear, and the bench
# at the elbow is Odessa's own corner.
for (kind, x, y, rz) in [
        # the terrace / the station elbow
        ("crate", 83.85, 15.20, 0.30), ("bucket", 82.60, 15.10, 0.0),
        ("bars", 84.15, 14.98, 0.0), ("paddle", 82.30, 15.24, 0.35),
        # the deck itself, clear of the rail: the gear a lock station keeps to hand
        ("coil", 80.95, 17.10, 0.0), ("chain", 79.95, 17.05, 0.0),
        ("crate", 79.55, 16.55, -0.22), ("coil", 77.35, 15.85, 0.0),
        ("barrel", 78.30, 16.05, 0.0),
        # the south margin, against the revetment, along the approach
        ("crate", 76.55, 14.10, 0.18), ("barrel", 75.60, 14.20, 0.0),
        ("bucket", 79.85, 14.35, 0.0), ("crate", 80.60, 14.35, -0.30),
        ("coil", 82.15, 14.85, 0.0), ("crate", 77.30, 14.15, 0.40),
        # ... and more of it, because the user's own note on this district was that
        # it is "a big empty district": the sweep from the Weave huts to the
        # cottage is 11 m of route and it has to look worked in, not swept.
        ("coil", 78.20, 14.35, 0.0), ("bars", 79.10, 14.32, 0.0),
        ("barrel", 80.10, 16.85, 0.0), ("crate", 75.90, 15.65, -0.15),
        ("bucket", 77.05, 15.90, 0.0), ("coil", 83.05, 14.80, 0.0)]:
    prop(kind, x, y, rz)
CLUT = join_meshes([p for p in clut if p], "lk_clut", COLL_PROPS) if clut else None
log("BUILD", "lk_clut", "%d props placed, %d refused by the corridor guard "
    "(crates, barrels, rope and chain coils, a spare lock paddle, a bundle of "
    "iron bar, buckets)" % (nclut, nclut_skip))

# =========================================================================
# 9. LIGHT — ordinary warm practicals, solved wattage
# =========================================================================
# 680 W / 14 m cutoff is the town standard, unchanged across six districts.
# There are no Heartlights in Dellhollow (world canon: Heartlights are rare and
# magical; a working post has lanterns).
LAMPS = []


def lantern(name, x, y, z, energy=680.0):
    p = [obox("gl", x, y, z, 0.155, 0.155, 0.26, mat=MGLASS, cname=COLL),
         obox("cp", x, y, z + 0.17, 0.21, 0.21, 0.055, mat=MIRON, cname=COLL),
         obox("bs", x, y, z - 0.16, 0.19, 0.19, 0.04, mat=MIRON, cname=COLL)]
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p.append(obox("cg", x + sx * 0.072, y + sy * 0.072, z, 0.024, 0.024, 0.34,
                      mat=MIRON, cname=COLL))
    ob = join_meshes([q for q in p if q], name, COLL)
    li = bpy.data.lights.new(name.replace("lk_", "KEYL_") + "_light", 'POINT')
    li.energy = energy
    li.color = (1.0, 0.58, 0.24)
    li.shadow_soft_size = 0.10
    li.use_custom_distance = True
    li.cutoff_distance = 14.0
    li.shadow_maximum_resolution = 0.01
    lo = bpy.data.objects.new(li.name, li)
    lo.location = (x, y, z + 0.02)
    link(lo, COLL)
    LAMPS.append((li.name, x, y, z + 0.02, energy))
    return ob


lampparts = []
# (1) THE LADDER HEAD, on a post standing on the boards beside the rail opening —
#     the one place a player has to be able to find in the dark, because it is the
#     only legitimate way over the edge.  Its position is taken from the rail's own
#     posts (they are the points that certainly have deck under them), not guessed:
#     the first cut named a coordinate 0.16 m past the deck's east edge and the
#     lamp silently did not get built.
#     It stands BESIDE that post, not on it: the first gated run put the lamp post
#     exactly where a rail post already was and drove its bracket through a chain
#     coil as well — 2 of the run's 4 intersection offenders.
lamp_post = None
for p in sorted(LIP, key=lambda p: abs(p.x - (LADDER_GAP[0] - 0.35))):
    for off in (-0.42, 0.42, -0.62, 0.62):
        q = p + Vector((off, 0, 0))
        if surf_top(q.x, q.y, r=1) is None:
            continue
        if free_box(q.x - 0.14, q.x + 0.14, q.y - 0.14, q.y + 0.14, q.z - 0.10, q.z + 2.45) \
                and spot_clear(q.x, q.y, 0.34):
            lamp_post = q
            break
    if lamp_post is not None:
        break
if lamp_post is not None:
    lx, ly, lz = lamp_post.x, lamp_post.y, lamp_post.z
    occupy(lx, ly, 0.30)
    lampparts.append(cyl("lp", (lx, ly, lz - 0.15), (lx, ly, lz + 2.26), 0.055, 8, MIRON, COLL))
    lampparts.append(cyl("la", (lx, ly, lz + 2.22), (lx, ly - 0.30, lz + 2.18), 0.040, 6, MIRON, COLL))
    lantern("lk_lantern_0", lx, ly - 0.30, lz + 1.94)
# (2) Odessa's own work lamp, bracketed off the revetment over the bench, and off
#     its SOUTH face: east of the pad the wall follows the descent's ribbon, so the
#     bench lies BEHIND the wall and a bracket on the north face would hang over
#     the flight the player walks down.  480 W, not 680: the ledger is 1.1 m away
#     and a full globe measures 53 W/m2 there, which is a wash — this lamp exists
#     to read a chart by.
#     IT HANGS ON THE GEAR POST, off the hook beside the gauge shelf, and not on a
#     bracket off the revetment.  Two rounds of the geometry audit argued this one
#     out: on the wall at desk height the globe was inside the desk, raised 0.4 m it
#     was inside the chart board, and searched along the wall it could not find 0.5
#     m of clear air anywhere over a bench that is 0.6 m deep and fully furnished.
#     A lockkeeper's lamp hangs where her coat and her gauges hang.
gp = globals().get("GEARPOST")
if gp:
    gpx, gpy, gpz = gp
    lx1, ly1, lz1 = gpx + 0.28, gpy + 0.10, gpz + 1.58
    # (no 3D self-test on this one: the globe is MEANT to touch the hook it hangs
    #  from, which is why the town registers lantern-to-bracket as one assembly)
    if free_box(lx1 - 0.13, lx1 + 0.13, ly1 - 0.13, ly1 + 0.13, lz1 - 0.20, lz1 + 0.24):
        lampparts.append(cyl("lb", (gpx, gpy + 0.02, gpz + 1.80),
                             (lx1, ly1, lz1 + 0.22), 0.030, 6, MIRON, COLL))
        lantern("lk_lantern_1", lx1, ly1, lz1, energy=480.0)
if lampparts:
    join_meshes([p for p in lampparts if p], "lk_lantern_brackets", COLL)


def irr(E, P, Q):
    """Point-lamp irradiance, W/m2, the number the town's lighting norm is
    written in (spill is MEASURED, never eyeballed)."""
    d2 = max((Vector(P) - Vector(Q)).length_squared, 0.04)
    return E / (4.0 * math.pi * d2)


PROBES = [("pad centre", (80.73, 16.00, 14.60)), ("the desk", (82.44, 14.60, 14.85)),
          ("ladder head", (81.55, 17.40, 14.30)), ("approach mid", (77.50, 15.20, 14.60)),
          ("descent foot", (85.30, 17.60, 12.40)), ("mast truck", (81.88, 13.18, 19.80))]
log("LIGHT", "%d practicals" % len(LAMPS), "680 W warm (1.0, 0.58, 0.24), 14 m "
    "cutoff — the town standard; no Heartlights (world canon)")
print("\n  LAMP INVENTORY — p-lockhead")
for (nm, x, y, z, E) in LAMPS:
    print("    %-26s %6.1f W  at (%.2f, %.2f, %.2f)  cutoff 14.0 m" % (nm, E, x, y, z))
print("  MEASURED SPILL (sum of this district's own lamps, W/m2)")
for label, P in PROBES:
    tot = sum(irr(E, (x, y, z), P) for (_n, x, y, z, E) in LAMPS)
    print("    %-14s %8.2f W/m2   at (%.2f, %.2f, %.2f)" % (label, tot, *P))

# =========================================================================
# 10. VEGETATION — the same language as the family next door
# =========================================================================
# `veg_lf_fern_*` is 8 verts: two crossed quads, `mat_fern`/`mat_grass`.  Same
# here, because a district that invents its own foliage grammar reads as a
# different game from the district beside it.  Guarded like everything else: a
# tuft standing in a walk corridor blocks a gate sample as surely as a wall does.
nveg = 0
for k in range(40):
    x = 75.0 + rng.random() * 10.2
    y = GROUND_Y_MIN + 0.10 + rng.random() * 1.70      # the bank face, mostly
    joint = rng.random() < 0.30
    if joint:                                          # ... and a few in the joints
        y = 13.8 + rng.random() * 3.6
    s = 0.42 + rng.random() * 0.55
    h = 0.30 + rng.random() * 0.42
    # THE FOOT IS THE LOWEST CORNER, not the centre: on a 45-degree bank a 0.9 m
    # clump seated on its centre floats 0.35 m at its downhill edge.
    gs = [gz(x + dx, y + dy) for dx, dy in
          ((-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2), (-s / 2, s / 2))]
    gs = [g for g in gs if g is not None]
    if not gs:
        continue
    g = min(gs)
    # A joint tuft belongs in a JOINT — beside the route, not scattered 7 m down
    # the cliff face where the first cut put three of them.
    if joint:
        s_ = surf_top(x, y, r=3)
        if s_ is None or abs(s_ - g) > 0.55:
            continue
    if not free_box(x - s / 2, x + s / 2, y - s / 2, y + s / 2, g - 0.05, g + h, pad=0.26):
        continue
    a = rng.random() * math.pi
    V, F = [], []
    for t in (a, a + math.pi / 2):
        dx, dy = math.cos(t) * s / 2, math.sin(t) * s / 2
        b = len(V)
        V += [(x - dx, y - dy, g - 0.06), (x + dx, y + dy, g - 0.06),
              (x + dx, y + dy, g + h), (x - dx, y - dy, g + h)]
        F.append((b, b + 1, b + 2, b + 3))
    new_mesh("veg_lk_tuft_%d" % k, V, F, MFERN if k % 2 else MGRASS, COLL_VEG)
    nveg += 1
log("BUILD", "veg_lk_tuft_* x%d" % nveg, "crossed quads on mat_fern/mat_grass, the "
    "veg_lf_* family's own grammar; guarded out of every walk corridor")

# =========================================================================
# report
# =========================================================================
mine = [o for o in bpy.data.objects
        if o.name.startswith(("lk_", "veg_lk_")) and o.type == 'MESH']
if mine:
    bb = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
    nv = 0
    for o in mine:
        b = world_bbox(o)
        bb = [min(bb[0], b[0]), max(bb[1], b[1]), min(bb[2], b[2]), max(bb[3], b[3]),
              min(bb[4], b[4]), max(bb[5], b[5])]
        nv += len(o.data.vertices)
    print("\n" + "=" * 78)
    print("THE LOCKHEAD — %d objects, %d verts, bounds x %.2f..%.2f y %.2f..%.2f "
          "z %.2f..%.2f" % (len(mine), nv, *bb))
    print("=" * 78)
    for o in sorted(mine, key=lambda o: o.name):
        b = world_bbox(o)
        print("  %-24s %6dv  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f"
              % (o.name, len(o.data.vertices), b[0], b[1], b[2], b[3], b[4], b[5]))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
