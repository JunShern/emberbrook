"""shelf_build.py — the SHELF TIER (parcels `p-shelf-w` + `p-shelf-e`).

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/shelf_build.py -- save

Dellhollow's shop street: the Boatmen's Rest, the item and weapon shops, the
armor shop cantilevered over the gorge and the Shelf homes closing the row, on a
4 m ledge between the GATE tier's corbelled gallery 5 m above and the MARKET
tier 5 m below.

Built on the same BRANCH copy of the master as the Gate Approach, under the
parallel branch-district protocol: ADDITIVE ONLY.  Every object this script
makes is named `shelf_*` (foliage `veg_shelf_*`, lamps `KEYSH_*`) and lives in
the collection `SHELF_DISTRICT`.  The only permitted deletions are the `lm_`
blockout shells of this district's own five members, and every one of them is
recorded in `tools/blends/districts/shelf_branch_deletions.json` — which
ACCUMULATES and is never rewritten empty by a re-run (finding 131).

Nothing else in the file is moved, edited, renamed or hidden.  In particular the
GATE district's art is read but never touched: `gate_corbels`, `gate_ground`,
`gate_winch_rope` and `cargo_winch_foot` are this district's CEILING and its
keep-outs, measured off their own geometry.

Reading order of the district, which is also the order it is built:
  1  ground        the shelf's own rock mass west, a plate over the market east
  2  cliff veneer  continuing the gate's backdrop east of x=31.44
  3  paving        the street laid on the walk graph
  4  underworks    the stone that carries the gate stair and the market loop stair
  5  buildings     inn / item / weapon / armor / two homes, each on its own pad
  6  street        awnings, signs, stalls, the strung lanterns the map asks for
  7  bunting       vertex-coloured cloth (glTF survives vertex colours, not noise)
  8  lanterns      ordinary warm practicals (there are no Heartlights here)
  9  parapet       the gorge rail — "gorge air beyond the rail" is the map's note
 10  vegetation    creepers on the veneer, tufts and ferns in the joints
 11  clutter       the working life of a shop street
"""
import bpy, bmesh, math, os, random, sys, json
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          M, world_bbox, dist_poly2, point_in_poly, Corridor)
from shelf_lib import (Terrain, over_walk, ceiling, ceiling_over,
                       SX0, SX1, SY0, SY1, FLOOR, RIDGE_CAP, CLIMB_CAP, BASEZ,
                       MARKET_TOP, DECK_DROP, GROUND_DROP, PAVE_W,
                       CORRIDOR_H, TIER_Z, MASS_X, SEAM_X,
                       SHOTS, HERO, HERO_EYES, hero_dist, near_field)

SAVE = "save" in sys.argv
COLL = "SHELF_DISTRICT"
rng = random.Random(20260729)
LOG = []
DELETIONS = REPO + "/tools/blends/districts/shelf_branch_deletions.json"


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-32s %s" % (kind, what, why))


print("=" * 78)
print("SHELF TIER  —  parcels p-shelf-w + p-shelf-e")
print("=" * 78)

# ---------------------------------------------------------------- materials
MROCK, MIRON, MROPE = M("mat_rock"), M("mat_iron"), M("mat_rope")
MT, MTD, MDECK = M("mat_timber"), M("mat_timber_dark"), M("mat_deck")
MWALL, MWALLD = M("mat_wallwood"), M("mat_wallwood_dark")
MRED, MBLUE = M("mat_paint_red"), M("mat_paint_blue")
MSHINGLE, MGLASS = M("mat_shingle_mossy"), M("mat_lantern_glass")
MFRESH, MCANVAS = M("mat_freshwood"), M("mat_canvas")
MPUMPKIN = M("mat_pumpkin")


def derive(src, name, scale=None, tint=None, fac=0.85, mode='MULTIPLY'):
    """A new surface DERIVED from one of the town's textured materials.

    Findings 94/121: a flat Principled colour is not a dark surface, it is an
    UNTEXTURED one — next to the Boatyard's box-projected, AO-multiplied,
    moss-graded surfaces it reads as cream no matter how dark the number.
    Copying `mat_rock` and re-tinting through a MULTIPLY mix inherits the box
    projection, the AO multiply, the roughness map and the world-up moss layer.

    It is also the ONLY tinting form that survives glTF: an image texture
    multiplied by a constant is exactly baseColorTexture * baseColorFactor.
    """
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


# Re-tiled for the object's scale (finding 95): `mat_rock` is tuned for a 60 m
# cliff, so roughly one texture feature per metre.  A shopfront wants tighter
# still than the gate's carriageway did — the player walks under these eaves.
MGROUND = derive("mat_rock", "mat_shelf_ground", scale=1.15, tint=(0.44, 0.42, 0.33))
MPAVE = derive("mat_rock", "mat_shelf_paving", scale=1.85, tint=(0.49, 0.46, 0.41))
MSTONE = derive("mat_rock", "mat_shelf_stone", scale=1.95, tint=(0.56, 0.53, 0.48))
# The backdrop this street is READ AGAINST (finding 121): figure/ground is a
# surface problem before it is a light problem.  Same recipe and the same numbers
# as the gate's `mat_gate_cliff`, so the two veneers are one cliff across the
# seam at x=31.44 — but derived independently so this district carries no
# cross-district material dependency into the merge.
MCLIFF = derive("mat_rock", "mat_shelf_cliff", scale=1.05, tint=(0.34, 0.33, 0.36))
MSACK = derive("mat_timber", "mat_shelf_sack", scale=1.90, tint=(0.74, 0.63, 0.44))
# painted timber, per the finished districts.  Four boards a stop apart in VALUE,
# not four hues (finding 129, the same discipline as the bunting).
MPGREEN = derive("mat_wallwood", "mat_shelf_paint_green", scale=2.40, tint=(0.30, 0.40, 0.30))
MPOCHRE = derive("mat_wallwood", "mat_shelf_paint_ochre", scale=2.40, tint=(0.62, 0.47, 0.25))
MPTEAL = derive("mat_wallwood", "mat_shelf_paint_teal", scale=2.40, tint=(0.25, 0.39, 0.44))
MPRUST = derive("mat_wallwood", "mat_shelf_paint_rust", scale=2.40, tint=(0.52, 0.26, 0.19))
MPBONE = derive("mat_wallwood", "mat_shelf_paint_bone", scale=2.40, tint=(0.70, 0.66, 0.56))
PAINTS = [MPGREEN, MPOCHRE, MPTEAL, MPRUST, MPBONE]


def vcol_mat(name, rough=0.86, metal=0.0):
    """Principled, Base Color driven by the mesh's own `Col` attribute.

    THE GLTF-SURVIVAL GATE (2026-07-29) forbids a procedural node tree from
    reaching an exported material: 516/1587 townwalk prims export WHITE because
    the kit's ramps, ropes and bunting are noise/ramp trees that simply do not
    cross glTF.  `gate_build.cloth()` — a weave noise x a sun-fade multiplying a
    tint — is exactly that shape, and it renders beautifully in Blender and
    exports white.  So this district bakes the same variation into VERTEX
    COLOURS in Python and reads them with a Color Attribute node, which is
    glTF's COLOR_0 and survives byte-for-byte.  Same look, one gate passed.
    """
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "Col"
    nt.links.new(ca.outputs["Color"], b.inputs["Base Color"])
    return m


MCLOTH = vcol_mat("mat_shelf_cloth", rough=0.92)
MAWN = vcol_mat("mat_shelf_awning", rough=0.90)


def lamplit(name, rgb=(1.0, 0.455, 0.135), strength=2.6):
    """A window with someone behind it.

    Strength 2.1..3.4, not the 90 a 12 cm lantern globe wants: at window scale
    AgX creams anything hotter and the pane lands as a clipped white rectangle
    (finding 128).  FLAT strength, not the gate's noise-driven MapRange — glTF
    carries emissiveFactor and KHR_materials_emissive_strength, and carries
    nothing at all of a noise tree.  The unevenness comes from having four of
    these at four strengths rather than from a node.
    """
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.03, 0.02, 0.01, 1.0)
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


MWIN = [lamplit("mat_shelf_window_a", strength=2.15),
        lamplit("mat_shelf_window_b", strength=2.65),
        lamplit("mat_shelf_window_c", strength=3.05),
        lamplit("mat_shelf_window_d", strength=3.40)]
MWINDARK = derive("mat_wallwood", "mat_shelf_glass_dark", scale=3.0, tint=(0.10, 0.11, 0.12))

# ------------------------------------------------------------- collection(s)
coll(COLL)

killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("shelf_", "veg_shelf_", "KEYSH_")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
if killed:
    log("REBUILD", "%d shelf_/KEYSH_ objects cleared" % killed, "idempotent re-run")

# =========================================================================
# 0. DELETIONS — the blockout shells this district replaces
# =========================================================================
# Only p-shelf-w's and p-shelf-e's OWN members.  `lm_cookhouse_*` sits in the
# same x range and is the MARKET tier's; it is not touched.
DEL_PREFIX = ("lm_inn_", "lm_item-shop_", "lm_weapon-shop_",
              "lm_armor-shop_", "lm_shelf-homes_")
# The manifest ACCUMULATES (finding 131).  This script is idempotent, so its
# second run on its own saved output finds nothing left to delete — and a naive
# rewrite would publish an EMPTY list, which is the one file the merge custodian
# obeys literally.  Union by name; the log says how many were removed THIS run.
prev = {}
if os.path.exists(DELETIONS):
    try:
        prev = {d["name"]: d for d in json.load(open(DELETIONS)).get("deleted", [])}
    except Exception as e:
        print("!! could not read the existing deletions manifest:", e)
deleted = list(prev.values())
found = 0
for o in list(bpy.data.objects):
    if o.name.startswith(DEL_PREFIX):
        b = world_bbox(o)
        rec = {"name": o.name,
               "bbox_min": [round(v, 3) for v in (b[0], b[2], b[4])],
               "bbox_max": [round(v, 3) for v in (b[1], b[3], b[5])],
               "landmark": o.name.split("_")[1],
               "verts": len(o.data.vertices)}
        deleted = [d for d in deleted if d["name"] != o.name] + [rec]
        bpy.data.objects.remove(o, do_unlink=True)
        found += 1
manifest = {
    "district": "shelf-tier",
    "parcel": "p-shelf-w + p-shelf-e",
    "branch_blend": "tools/blends/dellhollow-master-gate-branch.blend",
    "rule": "ADDITIVE-ONLY except lm_ blockout shells of p-shelf-w's and "
            "p-shelf-e's own members. The merge custodian must delete exactly "
            "these object names from the live master before appending "
            "SHELF_DISTRICT. This file ACCUMULATES and is never rewritten empty "
            "by a rebuild (manifest finding 131).",
    "note": "All five members of the two shelf parcels (inn, item-shop, "
            "weapon-shop, armor-shop, shelf-homes) are replaced by built art, so "
            "both the _body and the _roof of each go. The _roof shells top out "
            "at z=23.55, 1.05 m above the parcels' nominal 22.5 ceiling; they are "
            "the roofs of bodies wholly inside the parcels and deleting a body "
            "without its roof would leave a slab floating over the street. "
            "Deleting them is also a QA WIN the merge inherits: on the branch's "
            "shelf region (x 17..56, y 0.5..14) lm_inn_roof was blocking 5 "
            "down-ray samples and lm_shelf-homes_body 4, both pre-existing master "
            "defects. lm_cookhouse_body/roof lies in the same x range but belongs "
            "to the MARKET tier (p-quay-mkt) and is NOT touched; nor is "
            "lm_notice-board, which blocks the remaining 2 samples in that region.",
    "deleted": sorted(deleted, key=lambda d: d["name"]),
}
os.makedirs(os.path.dirname(DELETIONS), exist_ok=True)
json.dump(manifest, open(DELETIONS, "w"), indent=1)
log("DELETE", "%d lm_ shells (%d removed this run)" % (len(deleted), found),
    "recorded in districts/shelf_branch_deletions.json")

# =========================================================================
# corridors + terrain
# =========================================================================
T = Terrain()
COR0, COR, KEEP = T.cor0, T.cor, T.keep
log("MODEL", "walk corridors", "%d tier/upper faces, %d lower faces (market + loop stair)"
    % (len(T.high), len(T.low)))


def free(x, y, z, pad=0.18):
    return not over_walk(COR, x, y, z, pad=pad)


# ---------------------------------------------------------------- the ground
_GT = {}


def ground_top(x, y):
    """The built sheet's own surface — the SAME number the mesh was made from, so
    a prop placer and the ground can never disagree about where the floor is."""
    k = (round(x, 3), round(y, 3))
    if k not in _GT:
        _GT[k] = T.node(x, y)[0]
    return _GT[k] if _GT[k] is not None else T.top(x, y)


def on_sheet(x, y):
    """True only where this district actually built ground (the sheet stops at
    the head of the market loop stair — see `Terrain.node`)."""
    if not T.has_ground(x, y):
        return False
    return T.node(x, y)[0] is not None


# The gate's rock promontory (gate_ground, solid to z=-8.35) already fills the
# west end of this parcel.  Rather than guess where it stops, ask it: a node
# whose own surface would be buried inside the promontory is simply not made.
GATEG = bpy.data.objects.get("gate_ground")
_GTOP = {}
_SC = bpy.context.scene
_DG = bpy.context.evaluated_depsgraph_get()


def gate_solid(x, y):
    """True where `gate_ground` already provides the surface at this level.

    The gate's rock promontory reaches into the west end of this parcel and
    plunges to z=-8.35.  Rather than guess where it stops (the number would go
    stale the moment the gate is rebuilt), ask its geometry: a node whose own
    surface would be buried inside the promontory is simply not made.
    """
    if GATEG is None:
        return False
    k = (round(x, 2), round(y, 2))
    if k in _GTOP:
        return _GTOP[k]
    hit, loc, nor, idx, ob, mat = _SC.ray_cast(_DG, Vector((x, y, FLOOR + 2.60)),
                                               Vector((0, 0, -1)), distance=5.0)
    v = bool(hit and ob is not None and ob.name == "gate_ground" and loc.z > FLOOR - 1.4)
    _GTOP[k] = v
    return v


ST = 0.32
NX = int(round((SX1 - SX0) / ST)) + 1
NY = int(round((SY1 - SY0) / ST)) + 1
NODE = {}
for i in range(NX):
    for j in range(NY):
        x, y = SX0 + i * ST, SY0 + j * ST
        if not T.has_ground(x, y):
            continue
        if gate_solid(x, y):
            continue
        t, b = T.node(x, y)
        if t is None:
            continue
        NODE[(i, j)] = (x, y, t, b)

V, F, MI = [], [], []
topi, boti = {}, {}
for k, (x, y, t, b) in NODE.items():
    topi[k] = len(V); V.append((x, y, t))
    boti[k] = len(V); V.append((x, y, b))


def cell(i, j):
    return all((i + a, j + c) in NODE for a, c in ((0, 0), (1, 0), (1, 1), (0, 1)))


for i in range(NX - 1):
    for j in range(NY - 1):
        if not cell(i, j):
            continue
        a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
        F.append((topi[a], topi[b], topi[c], topi[d]))
        zs = [NODE[k][2] for k in (a, b, c, d)]
        # the flat, walked part of the tier gets the turf/ground grade; the
        # falling faces stay bare rock (the moss layer is world-up driven)
        MI.append(1 if (max(zs) - min(zs) < 0.30 and min(zs) > 18.2) else 0)
        F.append((boti[d], boti[c], boti[b], boti[a])); MI.append(0)
        for (na, nb, oi, oj) in ((a, d, -1, 0), (b, c, 1, 0), (a, b, 0, -1), (d, c, 0, 1)):
            if cell(i + oi, j + oj):
                continue
            F.append((topi[na], topi[nb], boti[nb], boti[na])); MI.append(0)

me = bpy.data.meshes.new("shelf_ground")
me.from_pydata(V, [], F)
me.validate()
for m in (MROCK, MGROUND):
    me.materials.append(m)
for p, mi in zip(me.polygons, MI):
    p.material_index = mi
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
GROUND = bpy.data.objects.new("shelf_ground", me)
link(GROUND, COLL)
_zs = [n[2] for n in NODE.values()]
_bs = [n[3] for n in NODE.values()]
log("BUILD", "shelf_ground", "%d nodes, %d faces — solid rock mass west of x=%.1f "
    "(foot z=%.1f, the tier was floating), a plate east of it whose underside "
    "stays out of the MARKET's volume (min %.2f); surface z %.2f..%.2f"
    % (len(NODE), len(F), MASS_X, min(_bs), min(b for b in _bs if b > 10.0),
       min(_zs), max(_zs)))

# =========================================================================
# 2. THE CLIFF VENEER — continuing the gate's backdrop east
# =========================================================================
# `cliff_town` is ONE 170 x 6 x 46 m blockout box at y -6..0 and it is untouchable
# far-rim geometry.  The gate district put a rock VENEER in front of it and ran it
# to x=31.44; east of that the raw slab is bare again, and the gate's own
# transcript records a confirmed leak seen at (56.8, 0.0, 29.2).  That one is
# this parcel's (gate handover).  Findings 102/130 govern the shape:
#   * held ABOVE cliff_town's own top edge at z=37.0 everywhere, or a band of the
#     blockout shows over the crest and the whole exercise buys nothing;
#   * the FOOT matters as much as the crest — floored under the MARKET tier, not
#     under this one, or every ray passing beneath our plate finds the slab again;
#   * the east end is set by the shallowest ray that can see past it, not by
#     where our ground stops: `armor` looks back west along a 12 m street with the
#     cliff 6 m to its left, so the veneer runs 1.05 m past the parcel's own
#     eastern limit to close the gate's recorded leak.  It is additive, it is in
#     SHELF_DISTRICT, and the merge custodian is told about it in the manifest.
CST = 0.42
CVX0, CVX1 = 31.30, 57.60
CX_N = int(round((CVX1 - CVX0) / CST)) + 1
CFLOOR = 13.20


def cliff_crest(x):
    return 40.20 + 1.50 * math.sin(x * 0.21 + 0.7) + 0.80 * math.sin(x * 0.63 - 1.9) \
        + 0.35 * math.sin(x * 1.47 + 3.1)


BACKS = []      # filled in once the buildings know where their back walls are


def cliff_front(x, z):
    u = min(1.0, max(0.0, (z - CFLOOR) / max(cliff_crest(x) - CFLOOR, 1.0)))
    d = 0.10 + 0.80 * (1.0 - u) ** 1.05
    d += (math.sin(x * 0.83 + z * 0.55) * 0.40 + math.sin(x * 2.11 - z * 1.31) * 0.22
          + math.sin(x * 4.7 + z * 3.3) * 0.08) * 0.32
    for bx0, bx1 in BACKS:
        if bx0 <= x <= bx1:
            d = min(d, 0.10)
    return max(0.04, d)


def build_veneer():
    CV, CF = [], []
    rows = []
    n = 30
    for i in range(CX_N):
        x = CVX0 + i * CST
        col = []
        for k in range(n + 1):
            z = CFLOOR + (cliff_crest(x) - CFLOOR) * (k / n) ** 0.92
            col.append((len(CV), z))
            CV.append((x, cliff_front(x, z), z))
        for k in range(n + 1):
            CV.append((x, -0.60, col[k][1]))
        rows.append((col, len(CV) - (n + 1)))
    NN = n + 1
    for i in range(CX_N - 1):
        a0, b0 = rows[i][0][0][0], rows[i + 1][0][0][0]
        a1, b1 = rows[i][1], rows[i + 1][1]
        for k in range(NN - 1):
            CF.append((a0 + k, b0 + k, b0 + k + 1, a0 + k + 1))
            CF.append((a1 + k + 1, b1 + k + 1, b1 + k, a1 + k))
        CF.append((a0 + NN - 1, a1 + NN - 1, b1 + NN - 1, b0 + NN - 1))
        CF.append((b0, b1, a1, a0))
    for (a0, a1) in ((rows[0][0][0][0], rows[0][1]), (rows[-1][0][0][0], rows[-1][1])):
        for k in range(NN - 1):
            CF.append((a0 + k, a0 + k + 1, a1 + k + 1, a1 + k))
    me = bpy.data.meshes.new("shelf_cliffface")
    me.from_pydata(CV, [], CF)
    me.validate()
    me.materials.append(MCLIFF)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("shelf_cliffface", me)
    link(ob, COLL)
    return ob


# =========================================================================
# 3. PAVING — the street, laid on the walk graph
# =========================================================================
def walk_ref(x, y):
    """(effective shelf-level walk top, distance) — the STREET only, not the
    stairs above or below it, so the paving does not chase the gate stair up."""
    inside, best, bz = None, 1e9, None
    for raw, fn, zt, nm in T.high:
        if zt > FLOOR + 0.9:
            continue
        if point_in_poly(x, y, raw):
            v = fn(x, y)
            inside = v if inside is None else max(inside, v)
        d = dist_poly2(x, y, raw)
        if d < best:
            best, bz = d, T.plane_at(raw, fn, x, y, d)
    if inside is not None:
        return inside, 0.0
    return bz, best


def road_at(x, y):
    z, d = walk_ref(x, y)
    if z is None or d > PAVE_W + 1.4:
        return None
    return z - DECK_DROP, d


# =========================================================================
# roofs — one course builder, because a roof is not a stack of planks
# =========================================================================
def shingles(parts, cx, cy, eave_z, ridge_z, half_dep, width, mat=None,
             axis='y', courses=None, over=0.11, thick=0.055):
    """Overlapping shingle courses from the eaves up to the ridge (finding 125).

    The course count comes off the roof's DEPTH, not its height: what the eye
    counts is the EXPOSURE, the strip of each course the one above leaves
    showing.  ~0.12 m of exposure reads as tiles; 0.21 m reads as a lumber
    stack, and on a street where the player walks under the eaves that is very
    visible.  Courses break across their length on a half-tile stagger.
    """
    n = courses or max(9, int(round(half_dep / 0.105)))
    mat = mat if mat is not None else MSHINGLE
    tiles = max(3, int(round(width / 0.70)))
    for k in range(n):
        u = k / float(n - 1)
        zz = eave_z + (ridge_z - eave_z) * u
        dep = half_dep * (1.0 - u)
        step = half_dep / float(n - 1)
        for s in (-1, 1):
            for t in range(tiles):
                stag = 0.5 if k % 2 else 0.0
                w = width / tiles
                off = (t + 0.5 + stag) * w - width / 2
                if abs(off) > width / 2:
                    continue
                jz = zz + (0.008 if (t + k) % 2 else -0.008)
                if axis == 'y':
                    parts.append(obox("rf", cx + off, cy + s * dep, jz, w * 0.94,
                                      step + over, thick, mat=mat, cname=COLL))
                else:
                    parts.append(obox("rf", cx + s * dep, cy + off, jz, step + over,
                                      w * 0.94, thick, mat=mat, cname=COLL))
    return parts


def soffit(parts, cx, cy, z, sx, sy, mat=None):
    """Under-boarding closing the roof from below.

    A shingle roof seen from UNDER its eaves is a stack of tile ends, and on a
    3 m street that is most of what the player looks at (finding 125 is about the
    top surface; this is its other half).  Real roofs are boarded underneath, and
    one box per building buys the whole street a clean soffit line."""
    parts.append(obox("sf", cx, cy, z, sx, sy, 0.06,
                      mat=mat if mat is not None else MTD, cname=COLL))


def monopitch(parts, x0, x1, y0, y1, z_lo, z_hi, mat=None, over=0.10, thick=0.055):
    """A shed roof falling from y0 (high) to y1 (low), in real courses."""
    mat = mat if mat is not None else MSHINGLE
    dep = abs(y1 - y0)
    n = max(6, int(round(dep / 0.11)))
    tiles = max(3, int(round((x1 - x0) / 0.70)))
    for k in range(n):
        u = (k + 0.5) / n
        yy = y0 + (y1 - y0) * u
        zz = z_hi + (z_lo - z_hi) * u
        for t in range(tiles):
            stag = 0.5 if k % 2 else 0.0
            w = (x1 - x0) / tiles
            xx = x0 + (t + 0.5 + stag) * w
            if xx > x1:
                continue
            parts.append(obox("rf", xx, yy, zz + (0.008 if (t + k) % 2 else -0.008),
                              w * 0.94, dep / n + over, thick, mat=mat, cname=COLL))
    return parts


# =========================================================================
# 5. THE BUILDINGS
# =========================================================================
# Every one is seated against its OWN landmark pad and the pad is left clear:
# the pad is where the PLAYER stands, not where the building goes (finding 92),
# and reading the pad before placing the landmark — in x as well as z — was the
# single largest compositional improvement of the gate pass (finding 127).
#
# The Inn is the district's subject: it is the first thing seen coming down the
# gate stair and it carries the tallest ridge.  Everything else is DELIBERATELY
# subordinate (finding 126) — but with only 4.10 m between the floor and the
# gallery, subordination cannot be bought with height, so the differentiation is
# ridge DIRECTION (X vs Y), awning depth and jetty:
#
#   inn          x 23.95..28.45  ridge along X  23.05   deep bracketed porch
#   item-shop    x 30.30..35.00  ridge along Y  22.60   gable + 1.30 m awning
#   weapon-shop  x 35.00..39.90  ridge along X  22.75   forge pentice + chimney
#   armor-shop   x 42.30..46.80  ridge along Y  22.85   jettied over the gorge
#   home A       x 47.90..51.90  ridge along X  22.25
#   home B       x 46.90..50.60  ridge along Y  22.45
#   home C       x 51.40..54.40  ridge along X  22.15
#
# and every ridge is then CAPPED by `ceiling_over()`, which reads the gate's own
# corbels and plate rather than trusting any number in this comment.
CEIL_CLEAR = 0.30
CAPPED = []


def cap(name, x0, x1, y0, y1, want):
    c = ceiling_over(x0 - 0.25, x1 + 0.25, y0 - 0.25, y1 + 0.25)
    z = min(want, RIDGE_CAP, c - CEIL_CLEAR)
    CAPPED.append((name, want, c, z))
    return z


def gz(x, y):
    r = road_at(x, y)
    return r[0] if r is not None else ground_top(x, y)


def plinth(parts, x0, x1, y0, y1, zb, h=0.26, over=0.16, mat=None):
    parts.append(obox("pl", (x0 + x1) / 2, (y0 + y1) / 2, zb + h / 2,
                      x1 - x0 + over, y1 - y0 + over, h,
                      mat=mat if mat is not None else MSTONE, cname=COLL))


def framed_wall(parts, x0, x1, y0, y1, zb, zt, mat, frame=MT, nposts=0, sill=True):
    """A painted boarded wall with its exposed frame — the town's own idiom."""
    parts.append(obox("wl", (x0 + x1) / 2, (y0 + y1) / 2, (zb + zt) / 2,
                      x1 - x0, y1 - y0, zt - zb, mat=mat, cname=COLL))
    if nposts:
        L = max(x1 - x0, y1 - y0)
        along_x = (x1 - x0) >= (y1 - y0)
        for k in range(nposts):
            u = (k + 0.5) / nposts
            if along_x:
                parts.append(obox("fr", x0 + L * u, (y0 + y1) / 2, (zb + zt) / 2,
                                  0.15, (y1 - y0) + 0.05, zt - zb, mat=frame, cname=COLL))
            else:
                parts.append(obox("fr", (x0 + x1) / 2, y0 + L * u, (zb + zt) / 2,
                                  (x1 - x0) + 0.05, 0.15, zt - zb, mat=frame, cname=COLL))
    if sill:
        parts.append(obox("sl", (x0 + x1) / 2, (y0 + y1) / 2, zt,
                          x1 - x0 + 0.16, y1 - y0 + 0.16, 0.11, mat=frame, cname=COLL))


WINCOUNT = [0]


def window(parts, cx, cy, cz, w, h, face, lit=True, mat_frame=MT):
    """A window, lit or shuttered.  `face` is 'y+', 'y-', 'x+' or 'x-'."""
    nx = 0.10
    sx, sy = (w, nx) if face[0] == 'y' else (nx, w)
    sgn = 1.0 if face[1] == '+' else -1.0
    off = 0.06 * sgn
    ox, oy = (0.0, off) if face[0] == 'y' else (off, 0.0)
    mg = MWIN[WINCOUNT[0] % len(MWIN)] if lit else MWINDARK
    WINCOUNT[0] += 1
    parts.append(obox("wf", cx, cy, cz, sx + 0.20, sy + 0.20, h + 0.20,
                      mat=MTD, cname=COLL))
    parts.append(obox("wg", cx + ox, cy + oy, cz, sx * 0.90, sy * 0.90, h * 0.88,
                      mat=mg, cname=COLL))
    # glazing bars, so a lit pane is a WINDOW and not a glowing rectangle
    for k in (-1, 1):
        if face[0] == 'y':
            parts.append(obox("wm", cx + k * w * 0.22, cy + oy * 1.5, cz,
                              0.045, 0.05, h * 0.88, mat=mat_frame, cname=COLL))
        else:
            parts.append(obox("wm", cx + ox * 1.5, cy + k * w * 0.22, cz,
                              0.05, 0.045, h * 0.88, mat=mat_frame, cname=COLL))
    parts.append(obox("wb", cx + ox * 1.5, cy + oy * 1.5, cz,
                      sx * 0.90, sy * 0.90, 0.045, mat=mat_frame, cname=COLL))
    parts.append(obox("ws", cx + ox * 3.0, cy + oy * 3.0, cz - h * 0.56,
                      sx + 0.30 if face[0] == 'y' else sx + 0.34,
                      sy + 0.34 if face[0] == 'y' else sy + 0.30, 0.08,
                      mat=mat_frame, cname=COLL))


def doorway(parts, cx, cy, cz, w, h, face, mat=MTD):
    nx = 0.14
    sx, sy = (w, nx) if face[0] == 'y' else (nx, w)
    parts.append(obox("dr", cx, cy, cz + h / 2, sx, sy, h, mat=mat, cname=COLL))
    parts.append(obox("dj", cx, cy, cz + h + 0.09, sx + 0.24, sy + 0.10, 0.16,
                      mat=MT, cname=COLL))


def hangsign(parts, cx, cy, cz, face, paint, w=0.86, h=0.62, arm=0.62):
    """A shop sign on an iron arm — this is a shop STREET and the signs are half
    of what says so."""
    sgn = 1.0 if face[1] == '+' else -1.0
    if face[0] == 'y':
        parts.append(beam("sa", (cx, cy, cz + 0.42), (cx, cy + sgn * arm, cz + 0.42),
                          0.055, 0.055, MIRON, COLL))
        parts.append(cyl("sh", (cx, cy + sgn * arm * 0.88, cz + 0.40),
                         (cx, cy + sgn * arm * 0.88, cz + h / 2), 0.022, 6, MIRON, COLL))
        parts.append(obox("sg", cx, cy + sgn * arm * 0.88, cz, w, 0.06, h,
                          mat=paint, cname=COLL))
        parts.append(obox("sgf", cx, cy + sgn * arm * 0.88, cz, w + 0.10, 0.035, h + 0.10,
                          mat=MTD, cname=COLL))
    else:
        parts.append(beam("sa", (cx, cy, cz + 0.42), (cx + sgn * arm, cy, cz + 0.42),
                          0.055, 0.055, MIRON, COLL))
        parts.append(cyl("sh", (cx + sgn * arm * 0.88, cy, cz + 0.40),
                         (cx + sgn * arm * 0.88, cy, cz + h / 2), 0.022, 6, MIRON, COLL))
        parts.append(obox("sg", cx + sgn * arm * 0.88, cy, cz, 0.06, w, h,
                          mat=paint, cname=COLL))
        parts.append(obox("sgf", cx + sgn * arm * 0.88, cy, cz, 0.035, w + 0.10, h + 0.10,
                          mat=MTD, cname=COLL))


AWNINGS = []


def awning(x0, x1, y_wall, y_out, z_wall, z_out, rgb_a, rgb_b, nstripe=None):
    """A striped canvas awning, its stripes baked into VERTEX COLOURS.

    A stripe is the obvious job for a texture or a procedural checker, and both
    are exactly what the glTF-survival gate forbids (a checker node exports as
    nothing at all).  Vertex colours are COLOR_0 and survive, so the stripes are
    made of geometry: one quad pair per stripe, coloured in Python.

    ONE OBJECT PER AWNING, not one object for the street.  The first cut
    accumulated all four into a single mesh spanning x 30.9..44.9, and the
    geometry audit called the whole thing a stray — its five footprint probes
    are taken on the BBOX, and four awnings 10 m apart leave three of those
    probes hanging in mid-air over the street.  Finding 96, read the other way:
    a joined multi-part mesh's bounding box is not its footprint.
    """
    n = nstripe or max(4, int(round((x1 - x0) / 0.42)))
    V, F, C = [], [], []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        V.append((x, y_wall, z_wall))
        V.append((x, (y_wall + y_out) / 2, (z_wall + z_out) / 2 + 0.055))
        V.append((x, y_out, z_out))
        C += [rgb_a, rgb_a, rgb_a]
    for k in range(n):
        c = rgb_a if k % 2 == 0 else rgb_b
        for r in (0, 1):
            i0 = k * 3 + r
            F.append((i0, i0 + 3, i0 + 4, i0 + 1))
        for r in range(3):
            C[k * 3 + r] = c
            C[(k + 1) * 3 + r] = c
    me = bpy.data.meshes.new("shelf_awning_%d" % len(AWNINGS))
    me.from_pydata(V, [], F)
    me.validate()
    me.materials.append(MAWN)
    ca = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for i, c in enumerate(C):
        ca.data[i].color = (c[0], c[1], c[2], 1.0)
    ob = bpy.data.objects.new(me.name, me)
    link(ob, COLL)
    AWNINGS.append(ob)
    return ob


BUILDINGS = []          # (name, x0, x1, y0, y1) keep-out footprints


def keepout(name, x0, x1, y0, y1, back=False):
    BUILDINGS.append((x0, x1, y0, y1))
    if back:
        # only a CLIFF-side building backs onto the veneer, and only those press
        # it flat: pressing it behind a gorge-side shop would flatten 5 m of rock
        # relief for nothing (finding 102 says press behind every building — it
        # means every building that is actually in front of it).
        BACKS.append((x0 - 0.30, x1 + 0.30))


def in_solid(x, y):
    return any(x0 - 0.25 <= x <= x1 + 0.25 and y0 - 0.25 <= y <= y1 + 0.25
               for x0, x1, y0, y1 in BUILDINGS)


# ------------------------------------------------------------------ THE INN
# WHY IT IS NOT ON ITS PAD.  `walk_pad_inn` is x 20.70..23.30, and the whole of
# x 17.5..24.5 / y 2.0..5.0 above it is the gate stair coming down — three
# flights, two landings, and `bar_e_valley-gate__inn_l2_railA` standing to
# z=21.18 at x 23.64..24.51.  `walk_e_valley-gate__inn_landing.001` (x 22.5..24.5,
# top 20.40) also owns a 2.05 m corridor to z=22.45, so nothing may be built or
# even oversailed there below that height.  The inn therefore begins at x=24.80,
# 1.5 m east of its pad, and faces the pad with its west GABLE: a player walking
# down the stair arrives on the pad looking straight at the inn's end wall, its
# door and its sign.  That is truer to the frame than standing the building in
# the stair would have been.  (Findings 92/127, one axis over again.)
IX0, IX1, IY0, IY1 = 25.30, 29.40, 1.90, 4.65
zb = min(gz(IX0 + 0.4, IY1), gz(IX1 - 0.4, IY1)) - 0.10
RIDGE_INN = cap("inn", IX0, IX1, IY0, IY1 + 0.55, 23.05)
EAVE_INN = RIDGE_INN - 1.42
parts = []
plinth(parts, IX0, IX1, IY0, IY1, zb - 0.20, h=0.34)
framed_wall(parts, IX0, IX1, IY0, IY1, zb + 0.14, EAVE_INN - 0.18, MPGREEN, nposts=6)
# the taproom's front: three windows onto the street, two of them lit
for k, wx in enumerate((25.60, 26.90, 28.20)):
    window(parts, wx, IY1 + 0.02, zb + 1.42, 0.86, 1.00, 'y+', lit=(k != 1))
for wx in (26.20, 27.90):
    window(parts, wx, IY1 + 0.02, EAVE_INN - 0.62, 0.62, 0.54, 'y+', lit=True)
doorway(parts, IX0 + 0.02, 3.80, zb + 0.14, 1.05, 2.05, 'x-')
window(parts, IX0 + 0.02, 2.45, zb + 1.50, 0.70, 0.86, 'x-', lit=True)
# the ridge runs along X so the GABLE faces the gate stair.  Every other roof on
# this street turns the other way — with 4.10 m between the floor and the gate's
# gallery there is no height left to differentiate with, so the differentiation
# is DIRECTION (finding 126, adapted to a ceiling).
soffit(parts, (IX0 + IX1) / 2, (IY0 + IY1) / 2, EAVE_INN - 0.05,
       IX1 - IX0 + 0.75, IY1 - IY0 + 0.90)
shingles(parts, (IX0 + IX1) / 2, (IY0 + IY1) / 2, EAVE_INN, RIDGE_INN,
         (IY1 - IY0 + 0.90) / 2, IX1 - IX0 + 0.75)
parts.append(beam("rg", (IX0 - 0.38, (IY0 + IY1) / 2, RIDGE_INN + 0.06),
                  (IX1 + 0.38, (IY0 + IY1) / 2, RIDGE_INN + 0.06), 0.22, 0.19, MT, COLL))
for sy in (-1, 1):                     # barge boards, so the gable has an edge
    parts.append(beam("bg", (IX0 - 0.30, (IY0 + IY1) / 2 + sy * (IY1 - IY0 + 0.90) / 2,
                            EAVE_INN - 0.02),
                      (IX0 - 0.30, (IY0 + IY1) / 2, RIDGE_INN + 0.02), 0.20, 0.13, MT, COLL))
# the gable's boarded head, with the inn's own loft light
framed_wall(parts, IX0, IX0 + 0.16, IY0 + 0.35, IY1 - 0.35, EAVE_INN - 0.20,
            EAVE_INN + 0.82, MPBONE, nposts=3, sill=False)
window(parts, IX0 - 0.05, 3.28, EAVE_INN + 0.38, 0.60, 0.52, 'x-', lit=True)
# THE GALLERY.  The deepest oversail on the street — 1.45 m of covered walk in
# front of the taproom — hung on brackets rather than posts, because the ground
# it would need is the street itself.  Its underside is at EAVE-0.30 and the
# walk it covers has its 2.05 m corridor topping out at 21.05, so it is checked,
# not assumed (finding 98: heights here are ABSOLUTE).
GALZ = max(EAVE_INN - 0.30, 21.36)
for bx in (IX0 + 0.55, (IX0 + IX1) / 2, IX1 - 0.55):
    parts.append(beam("gb", (bx, IY1 - 0.04, GALZ + 0.10), (bx, IY1 + 1.45, GALZ + 0.06),
                      0.13, 0.16, MT, COLL))
    # A knee brace springing from the wall at GALZ-0.86 crosses the street's own
    # walk at z=20.89 — 0.16 m INSIDE the 2.05 m corridor, and the master's gate
    # named all five samples.  So the bracket stops short of the walk edge
    # entirely and the oversail is carried the way a real long jetty is: on iron
    # tie-rods back to the eave, which live above the roof line.
    parts.append(beam("gk", (bx, IY1 - 0.04, GALZ - 0.62), (bx, IY1 + 0.32, GALZ + 0.02),
                      0.10, 0.12, MT, COLL))
    parts.append(cyl("gt", (bx, IY1 + 1.40, GALZ + 0.30), (bx, IY1 + 0.05, EAVE_INN + 0.52),
                     0.028, 6, MIRON, COLL))
monopitch(parts, IX0 + 0.20, IX1 - 0.20, IY1 + 0.02, IY1 + 1.50, GALZ + 0.10, GALZ + 0.38)
parts.append(beam("gf", (IX0 + 0.10, IY1 + 1.45, GALZ + 0.08),
                  (IX1 - 0.10, IY1 + 1.45, GALZ + 0.08), 0.16, 0.20, MT, COLL))
# the sign, high on the gable so it clears the stair's corridor entirely
hangsign(parts, IX0 - 0.06, 3.55, EAVE_INN + 0.10, 'x-', MPRUST, w=1.05, h=0.72, arm=0.46)
INN = join_meshes(parts, "shelf_inn", COLL)
keepout("inn", IX0, IX1, IY0, IY1 + 1.55, back=True)

# ------------------------------------------------------------- THE ITEM SHOP
QX0, QX1, QY0, QY1 = 30.30, 35.00, 1.90, 5.85
zb = min(gz(QX0 + 0.4, QY1), gz(QX1 - 0.4, QY1)) - 0.10
RIDGE_ITEM = cap("item-shop", QX0, QX1, QY0, QY1 + 0.60, 22.60)
EAVE_ITEM = RIDGE_ITEM - 1.30
parts = []
plinth(parts, QX0, QX1, QY0, QY1, zb - 0.20, h=0.30)
framed_wall(parts, QX0, QX1, QY0, QY1, zb + 0.10, EAVE_ITEM - 0.20, MPTEAL, nposts=5)
# the ridge runs along Y, so the GABLE faces the street: a chandlery front
soffit(parts, (QX0 + QX1) / 2, (QY0 + QY1) / 2, EAVE_ITEM - 0.05,
       QX1 - QX0 + 0.80, QY1 - QY0 + 0.70)
shingles(parts, (QX0 + QX1) / 2, (QY0 + QY1) / 2, EAVE_ITEM, RIDGE_ITEM,
         (QX1 - QX0 + 0.80) / 2, QY1 - QY0 + 0.70, axis='x')
parts.append(beam("rg", ((QX0 + QX1) / 2, QY0 - 0.35, RIDGE_ITEM + 0.06),
                  ((QX0 + QX1) / 2, QY1 + 0.35, RIDGE_ITEM + 0.06), 0.21, 0.18, MT, COLL))
framed_wall(parts, QX0 + 0.40, QX1 - 0.40, QY1 - 0.16, QY1, EAVE_ITEM - 0.22,
            EAVE_ITEM + 0.74, MPBONE, nposts=3, sill=False)
window(parts, (QX0 + QX1) / 2, QY1 + 0.02, EAVE_ITEM + 0.34, 0.72, 0.56, 'y+', lit=True)
# the shopfront: a wide stall window, the door, and a 1.30 m striped awning
doorway(parts, QX0 + 1.05, QY1 + 0.02, zb + 0.10, 1.02, 2.05, 'y+')
parts.append(obox("sf", (QX0 + QX1) / 2 + 0.75, QY1 - 0.03, zb + 1.52, 2.30, 0.14, 1.24,
                  mat=MTD, cname=COLL))
parts.append(obox("sg", (QX0 + QX1) / 2 + 0.75, QY1 + 0.06, zb + 1.52, 2.10, 0.03, 1.06,
                  mat=MWIN[1], cname=COLL))
for k in range(4):
    parts.append(obox("sm", QX0 + 2.10 + k * 0.62, QY1 + 0.09, zb + 1.52, 0.05, 0.05, 1.08,
                      mat=MT, cname=COLL))
parts.append(obox("st", (QX0 + QX1) / 2 + 0.75, QY1 + 0.24, zb + 0.84, 2.46, 0.52, 0.10,
                  mat=MT, cname=COLL))
awning(QX0 + 0.55, QX1 - 0.30, QY1 + 0.05, QY1 + 1.30,
       min(zb + 2.52, EAVE_ITEM - 0.18), zb + 2.14,
       (0.196, 0.064, 0.055), (0.320, 0.295, 0.248))
for ax in (QX0 + 0.60, QX1 - 0.35):
    parts.append(beam("ab", (ax, QY1 + 0.06, min(zb + 2.52, EAVE_ITEM - 0.18)),
                      (ax, QY1 + 1.30, zb + 2.14), 0.07, 0.09, MT, COLL))
hangsign(parts, QX1 - 0.40, QY1 + 0.06, zb + 2.98, 'y+', MPOCHRE, w=0.90, h=0.64, arm=0.70)
ITEM = join_meshes(parts, "shelf_item_shop", COLL)
keepout("item-shop", QX0, QX1, QY0, QY1 + 1.40, back=True)

# ----------------------------------------------------------- THE WEAPON SHOP
WX0, WX1, WY0, WY1 = 35.00, 39.90, 8.65, 12.30
zb = min(gz(WX0 + 0.4, WY0), gz(WX1 - 0.4, WY0)) - 0.10
RIDGE_WEAP = cap("weapon-shop", WX0, WX1, WY0 - 0.60, WY1, 22.75)
EAVE_WEAP = RIDGE_WEAP - 1.34
parts = []
plinth(parts, WX0, WX1, WY0, WY1, zb - 0.20, h=0.32)
framed_wall(parts, WX0, WX1, WY0, WY1, zb + 0.12, EAVE_WEAP - 0.20, MPRUST, nposts=6)
soffit(parts, (WX0 + WX1) / 2, (WY0 + WY1) / 2, EAVE_WEAP - 0.05,
       WX1 - WX0 + 0.70, WY1 - WY0 + 0.85)
shingles(parts, (WX0 + WX1) / 2, (WY0 + WY1) / 2, EAVE_WEAP, RIDGE_WEAP,
         (WY1 - WY0 + 0.85) / 2, WX1 - WX0 + 0.70)
parts.append(beam("rg", (WX0 - 0.34, (WY0 + WY1) / 2, RIDGE_WEAP + 0.06),
                  (WX1 + 0.34, (WY0 + WY1) / 2, RIDGE_WEAP + 0.06), 0.22, 0.19, MT, COLL))
# the forge front, facing the street (-y)
doorway(parts, WX0 + 1.15, WY0 - 0.02, zb + 0.12, 1.10, 2.10, 'y-')
for k, wx in enumerate((37.05, 38.35, 39.35)):
    window(parts, wx, WY0 - 0.02, zb + 1.48, 0.82, 0.98, 'y-', lit=(k != 2))
window(parts, 36.10, WY0 - 0.02, EAVE_WEAP - 0.58, 0.60, 0.52, 'y-', lit=True)
# the forge's own pentice — shallow, so the inn's porch stays the deepest thing
for k in range(6):
    u = k / 5.0
    parts.append(obox("pt", (WX0 + WX1) / 2 + 0.30, WY0 - 0.14 - u * 0.78,
                      zb + 2.72 - u * 0.24, 3.60, 0.22, 0.055, mat=MSHINGLE, cname=COLL))
for ax in (WX0 + 1.90, WX1 - 1.10):
    parts.append(beam("pb", (ax, WY0 - 0.04, zb + 2.20), (ax, WY0 - 0.92, zb + 2.50),
                      0.08, 0.10, MT, COLL))
# chimney on the CLIFF side of the ridge, so it never stands against the sky in
# the `shops` frame, and 0.05 m under the inn's ridge so the inn still wins
parts.append(obox("ch", WX0 + 0.95, WY1 - 0.95, zb + 2.60, 0.82, 0.82, 3.00,
                  mat=MSTONE, cname=COLL))
parts.append(obox("cc", WX0 + 0.95, WY1 - 0.95, min(RIDGE_INN - 0.06, zb + 4.16),
                  1.02, 1.02, 0.18, mat=MSTONE, cname=COLL))
hangsign(parts, WX0 + 2.60, WY0 - 0.06, zb + 2.90, 'y-', MPTEAL, w=0.92, h=0.66, arm=0.68)
WEAP = join_meshes(parts, "shelf_weapon_shop", COLL)
keepout("weapon-shop", WX0, WX1, WY0 - 1.05, WY1)

# ------------------------------------------------------------ THE ARMOR SHOP
# "the armor shop over the gorge" — the map's own words.  Its pad is gorge-side
# (y 7.70..10.30), so the shop stands NORTH of the street and its back half
# oversails the lip on brackets.  That cantilever, not height, is its drama.
AX0, AX1, AY0, AY1 = 42.30, 46.80, 10.75, 13.85
zb = min(gz(AX0 + 0.4, AY0), gz(AX1 - 0.4, AY0)) - 0.10
RIDGE_ARM = cap("armor-shop", AX0, AX1, AY0 - 0.60, AY1, 22.85)
EAVE_ARM = RIDGE_ARM - 1.26
parts = []
plinth(parts, AX0, AX1, AY0, AY0 + 1.75, zb - 0.20, h=0.32)
framed_wall(parts, AX0, AX1, AY0, AY1, zb + 0.12, EAVE_ARM - 0.20, MPOCHRE, nposts=5)
soffit(parts, (AX0 + AX1) / 2, (AY0 + AY1) / 2, EAVE_ARM - 0.05,
       AX1 - AX0 + 0.80, AY1 - AY0 + 0.70)
shingles(parts, (AX0 + AX1) / 2, (AY0 + AY1) / 2, EAVE_ARM, RIDGE_ARM,
         (AX1 - AX0 + 0.80) / 2, AY1 - AY0 + 0.70, axis='x')
parts.append(beam("rg", ((AX0 + AX1) / 2, AY0 - 0.35, RIDGE_ARM + 0.06),
                  ((AX0 + AX1) / 2, AY1 + 0.35, RIDGE_ARM + 0.06), 0.21, 0.18, MT, COLL))
framed_wall(parts, AX0 + 0.40, AX1 - 0.40, AY0, AY0 + 0.16, EAVE_ARM - 0.22,
            EAVE_ARM + 0.70, MPBONE, nposts=3, sill=False)
doorway(parts, AX0 + 1.20, AY0 - 0.02, zb + 0.12, 1.08, 2.08, 'y-')
for k, wx in enumerate((44.30, 45.60)):
    window(parts, wx, AY0 - 0.02, zb + 1.50, 0.88, 1.00, 'y-', lit=(k == 0))
window(parts, (AX0 + AX1) / 2, AY0 - 0.02, EAVE_ARM + 0.30, 0.68, 0.52, 'y-', lit=True)
# THE CANTILEVER: raking brackets off the rock carrying the oversailing half,
# and a jettied upper band that puts the whole north wall out over the drop.
for k in range(5):
    bx = AX0 + 0.35 + k * (AX1 - AX0 - 0.70) / 4.0
    parts.append(beam("cb", (bx, AY0 + 1.55, zb - 0.05), (bx, AY1 - 0.10, zb - 0.04),
                      0.24, 0.30, MT, COLL))
    parts.append(beam("ck", (bx, AY0 + 1.35, zb - 0.12), (bx, AY0 + 2.95, zb - 1.55),
                      0.18, 0.22, MT, COLL))
parts.append(obox("fl", (AX0 + AX1) / 2, (AY0 + AY1) / 2 + 0.30, zb - 0.02,
                  AX1 - AX0 + 0.20, AY1 - AY0 - 0.40, 0.16, mat=MDECK, cname=COLL))
parts.append(obox("jt", (AX0 + AX1) / 2, AY1 + 0.14, zb + 2.30,
                  AX1 - AX0 + 0.44, 0.36, 0.30, mat=MT, cname=COLL))
window(parts, (AX0 + AX1) / 2 - 1.10, AY1 + 0.02, zb + 1.70, 0.90, 1.02, 'y+', lit=True)
hangsign(parts, AX0 + 2.75, AY0 - 0.06, zb + 2.86, 'y-', MPRUST, w=0.94, h=0.66, arm=0.70)
ARMOR = join_meshes(parts, "shelf_armor_shop", COLL)
keepout("armor-shop", AX0, AX1, AY0 - 1.05, AY1)

# ------------------------------------------------------------- SHELF HOMES
# "the Shelf homes" is plural and it closes the row: three dwellings, two of them
# gorge-side over the drop and one backed into the cliff, with ridges deliberately
# lower and shorter than every shop west of them.
def home(name, x0, x1, y0, y1, want, axis, paint, door_face, lit=(True, False)):
    zb_ = min(gz(x0 + 0.4, y0 if door_face == 'y-' else y1),
              gz(x1 - 0.4, y0 if door_face == 'y-' else y1)) - 0.10
    ridge = cap(name, x0, x1, y0 - 0.5, y1 + 0.5, want)
    eave = ridge - 1.16
    p = []
    plinth(p, x0, x1, y0, y1, zb_ - 0.20, h=0.28)
    framed_wall(p, x0, x1, y0, y1, zb_ + 0.10, eave - 0.18, paint, nposts=4)
    if axis == 'x':
        soffit(p, (x0 + x1) / 2, (y0 + y1) / 2, eave - 0.05,
               x1 - x0 + 0.62, y1 - y0 + 0.76)
        shingles(p, (x0 + x1) / 2, (y0 + y1) / 2, eave, ridge,
                 (y1 - y0 + 0.76) / 2, x1 - x0 + 0.62)
        p.append(beam("rg", (x0 - 0.30, (y0 + y1) / 2, ridge + 0.05),
                      (x1 + 0.30, (y0 + y1) / 2, ridge + 0.05), 0.19, 0.16, MT, COLL))
    else:
        soffit(p, (x0 + x1) / 2, (y0 + y1) / 2, eave - 0.05,
               x1 - x0 + 0.76, y1 - y0 + 0.62)
        shingles(p, (x0 + x1) / 2, (y0 + y1) / 2, eave, ridge,
                 (x1 - x0 + 0.76) / 2, y1 - y0 + 0.62, axis='x')
        p.append(beam("rg", ((x0 + x1) / 2, y0 - 0.30, ridge + 0.05),
                      ((x0 + x1) / 2, y1 + 0.30, ridge + 0.05), 0.19, 0.16, MT, COLL))
    fy = y0 - 0.02 if door_face == 'y-' else y1 + 0.02
    doorway(p, x0 + 0.95, fy, zb_ + 0.10, 0.98, 2.02, door_face)
    for k, wx in enumerate((x0 + 2.20, x1 - 0.75)):
        if wx <= x0 + 1.6:
            continue
        window(p, wx, fy, zb_ + 1.44, 0.78, 0.94, door_face, lit=lit[k % len(lit)])
    window(p, x0 + 1.55, fy, eave - 0.52, 0.56, 0.48, door_face, lit=True)
    # a hood over the door, and a chimney against the cliff-facing gable
    for k in range(4):
        u = k / 3.0
        sgn = -1.0 if door_face == 'y-' else 1.0
        p.append(obox("hd", x0 + 0.95, fy + sgn * (0.10 + u * 0.52),
                      zb_ + 2.44 - u * 0.16, 1.60, 0.18, 0.05, mat=MSHINGLE, cname=COLL))
    p.append(obox("ch", x1 - 0.55, (y0 + y1) / 2, zb_ + 2.30, 0.64, 0.64, 2.60,
                  mat=MSTONE, cname=COLL))
    p.append(obox("cc", x1 - 0.55, (y0 + y1) / 2, min(ridge - 0.10, zb_ + 3.66),
                  0.82, 0.82, 0.16, mat=MSTONE, cname=COLL))
    ob = join_meshes(p, "shelf_" + name.replace("-", "_"), COLL)
    keepout(name, x0, x1, y0 - 0.85, y1 + 0.85, back=(door_face == "y+"))
    return ob


HOME_A = home("home-a", 47.90, 51.90, 10.70, 13.55, 22.25, 'x', MPGREEN, 'y-',
              lit=(True, False))
HOME_B = home("home-b", 46.90, 50.60, 1.90, 5.05, 22.45, 'y', MPBONE, 'y+',
              lit=(False, True))
HOME_C = home("home-c", 51.40, 54.40, 1.90, 4.70, 22.15, 'x', MPTEAL, 'y+',
              lit=(True, True))

for nm, want, c, got in CAPPED:
    log("CAP", "%s ridge %.2f" % (nm, got),
        "wanted %.2f | measured gate ceiling over its footprint %s"
        % (want, ("open sky" if c > 90 else "%.3f (clearance %.2f)" % (c, c - got))))

# ------------------------------------------------ the market approach stalls
# The cliff side between the weapon shop and the armor shop is the run the map
# calls "the market approach".  Low lean-to stalls, deliberately 1.2 m under
# every ridge on the street, so they read as furniture and not as buildings.
parts = []
nst = 0
for k in range(4):
    sx0 = 39.90 + k * 1.72
    sx1 = sx0 + 1.42
    if sx1 > 46.30:
        break
    zbs = gz((sx0 + sx1) / 2, 3.30)
    for ax in (sx0 + 0.10, sx1 - 0.10):
        parts.append(obox("sp", ax, 3.55, zbs + 1.10, 0.14, 0.14, 2.20, mat=MT, cname=COLL))
        parts.append(obox("sp", ax, 1.95, zbs + 1.24, 0.14, 0.14, 2.48, mat=MT, cname=COLL))
    parts.append(obox("sc", (sx0 + sx1) / 2, 2.75, zbs + 0.86, sx1 - sx0, 1.24, 0.11,
                      mat=MT, cname=COLL))
    monopitch(parts, sx0 - 0.14, sx1 + 0.14, 1.90, 3.68, zbs + 2.18, zbs + 2.50)
    awning(sx0 - 0.10, sx1 + 0.10, 3.62, 4.42, zbs + 2.16, zbs + 1.92,
           (0.068, 0.123, 0.191) if k % 2 else (0.255, 0.175, 0.076),
           (0.320, 0.295, 0.248))
    nst += 1
STALLS = join_meshes(parts, "shelf_stalls", COLL)
for k in range(nst):
    keepout("stall%d" % k, 39.90 + k * 1.72 - 0.2, 39.90 + k * 1.72 + 1.62, 1.85, 4.50,
            back=True)

# =========================================================================
# 3b. PAVING (built now that the buildings own their footprints)
# =========================================================================
RST = 0.25
RNX = int(round((SX1 - SX0) / RST)) + 1
RNY = int(round((SY1 - SY0) / RST)) + 1
RN = {}
for i in range(RNX):
    for j in range(RNY):
        x, y = SX0 + i * RST, SY0 + j * RST
        r = road_at(x, y)
        if r is None:
            continue
        z, d = r
        if d > PAVE_W + 0.40:
            continue
        if not on_sheet(x, y) or gate_solid(x, y):
            continue
        crown = -0.022 * (d / max(PAVE_W, 0.1)) ** 2
        n = (math.sin(x * 3.1 + y * 1.9) * 0.5 + math.sin(x * 6.7 - y * 4.1) * 0.3) * 0.014
        zz = z + crown + n
        # Cap against EVERY walk face within reach, not only the shelf-level
        # band: the loop stair to the market drops below TIER_Z halfway down, so
        # its lower treads live in `T.low` — and paving laid from the nearest
        # HIGH tread stood 0.3 m proud of the low one right beside it (16 blocked
        # down-ray samples).  A paving slab is capped by whatever walk is nearest,
        # whichever list it happens to be in.
        for raw, fn, zt, nm in T.high + T.low:
            dd = dist_poly2(x, y, raw)
            if dd < 1.00:
                zz = min(zz, T.plane_at(raw, fn, x, y, dd) - DECK_DROP)
        RN[(i, j)] = (x, y, zz)

RV, RF = [], []
rt, rb = {}, {}
for k, (x, y, z) in RN.items():
    rt[k] = len(RV); RV.append((x, y, z))
    rb[k] = len(RV); RV.append((x, y, z - 0.22))


def rcell(i, j):
    return all((i + a, j + c) in RN for a, c in ((0, 0), (1, 0), (1, 1), (0, 1)))


for i in range(RNX - 1):
    for j in range(RNY - 1):
        if not rcell(i, j):
            continue
        a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
        RF.append((rt[a], rt[b], rt[c], rt[d]))
        RF.append((rb[d], rb[c], rb[b], rb[a]))
        for (na, nb, oi, oj) in ((a, d, -1, 0), (b, c, 1, 0), (a, b, 0, -1), (d, c, 0, 1)):
            if not rcell(i + oi, j + oj):
                RF.append((rt[na], rt[nb], rb[nb], rb[na]))
me = bpy.data.meshes.new("shelf_paving")
me.from_pydata(RV, [], RF)
me.validate()
me.materials.append(MPAVE)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
PAVING = bpy.data.objects.new("shelf_paving", me)
link(PAVING, COLL)
log("BUILD", "shelf_paving", "%d nodes — %.1f m of sett paving on every shelf-level "
    "walk ribbon, top %.0f mm UNDER the walk surface so the master's down-ray still "
    "lands on canonical topology (finding 89)" % (len(RN), 2 * PAVE_W, DECK_DROP * 1000))

# =========================================================================
# 4. UNDERWORKS — the stone that carries the two stairs
# =========================================================================
# Both stairs on this tier are currently FLOATING: the gate stair drops 5 m from
# the valley gate through open air onto the street, and the loop stair drops 5 m
# from the shelf-homes to the market.  A tread's masonry belongs UNDER the tread,
# and the walk QA measures headroom ABOVE it, so a battered wall capped 60 mm
# below each tread costs nothing and fixes two obviously unsupported runs.
parts = []
nw = 0
for raw, fn, zt, nm in (T.high + T.low):
    if not (nm.startswith("walk_e_valley-gate__inn") or
            nm.startswith("walk_e_shelf-homes__quay-deck") or
            nm.startswith("walk_e_shelf-homes__market-stalls")):
        continue
    xs = [p.x for p in raw]
    ys = [p.y for p in raw]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    if not on_sheet(cx, cy) or gate_solid(cx, cy):
        continue
    # A tread's masonry is capped by the LOWEST walk surface anywhere over its
    # own footprint, not by its own underside.  These flights overlap heavily in
    # plan (l2_t00 spans x 22.65..24.10 while l2_t01, 0.35 m lower, spans
    # 22.41..23.85), so a block sized to one tread and capped under that tread
    # stands 0.15 m PROUD of its neighbour and blocks the neighbour's down-ray.
    eff = []
    for a in range(5):
        for b2 in range(5):
            t = COR0.top_at(min(xs) + (max(xs) - min(xs)) * a / 4.0,
                            min(ys) + (max(ys) - min(ys)) * b2 / 4.0)
            if t is not None:
                eff.append(t)
    if not eff:
        continue
    ztop = min(eff) - 0.06
    zg = ground_top(cx, cy)
    if not (0.22 < ztop - zg < 7.0):
        continue
    parts.append(obox("uw", cx, cy, (zg + ztop) / 2 - 0.10,
                      (max(xs) - min(xs)) * 0.92, (max(ys) - min(ys)) * 0.92,
                      max(0.12, ztop - zg + 0.20), mat=MSTONE, cname=COLL))
    nw += 1
UNDER = join_meshes(parts, "shelf_stair_underworks", COLL)
log("BUILD", "shelf_stair_underworks", "%d battered blocks under the gate stair and "
    "the market loop stair, each capped 60 mm below its own tread so the walk QA's "
    "down-ray still lands on the tread" % nw)

# =========================================================================
# 6/7. BUNTING — vertex-coloured cloth, strung over the street
# =========================================================================
# The map's own note for this street is "lanterns strung overhead", so this is a
# lot of close-range cloth and it matters here more than it did at the gate.
# Finding 129: `mat_flag_*` is one flat diffuse mixed with one flat translucent —
# a coloured rectangle at 4 m.  The gate's answer was a weave NOISE; this
# district's answer is the same weave BAKED INTO VERTEX COLOURS, because a noise
# tree exports white (the glTF-survival gate).  Six values, not six hues.
CLOTHC = [(0.196, 0.064, 0.055), (0.128, 0.050, 0.046),
          (0.068, 0.123, 0.191), (0.047, 0.081, 0.128),
          (0.255, 0.175, 0.076), (0.320, 0.295, 0.248)]
BV, BF, BC = [], [], []
LINEP = []


def weave(rgb, u, v, phase):
    """The weave and the broad sun-fade, evaluated per vertex in Python."""
    w = 0.56 + 0.30 * (0.5 + 0.5 * math.sin(u * 61.0 + phase) * math.sin(v * 47.0 - phase))
    f = 0.62 + 0.44 * (0.5 + 0.5 * math.sin(u * 5.5 + v * 3.1 + phase * 0.7))
    k = w * f
    return (min(1.0, rgb[0] * k), min(1.0, rgb[1] * k), min(1.0, rgb[2] * k))


def pennant(c, run, drop, rgb, phase):
    """One triangular pennant: stiff top edge on the line, taper to the point, a
    per-pennant curl signed by its phase so a run is not N copies of one shape."""
    ax = Vector((run.x, run.y, 0)).normalized()
    side = Vector((-ax.y, ax.x, 0))
    top_w = 0.35 + 0.07 * math.sin(phase * 2.7)
    curl = 0.16 * math.sin(phase * 1.9) + 0.07 * math.sin(phase * 5.1)
    lean = 0.10 * math.sin(phase * 3.3)
    rows = 4
    b = len(BV)
    for r in range(rows + 1):
        u = r / float(rows)
        w = top_w * (1.0 - 0.78 * u)
        off = side * (curl * math.sin(u * 2.4) + lean * u) + ax * (0.05 * u * u)
        z = -drop * (u + 0.10 * u * (1.0 - u))
        base = c + off + Vector((0, 0, z))
        for s, sc_ in ((-1, 1.0 - 0.35 * u), (1, 1.0 + 0.15 * u)):
            p = base + side * (s * w / 2 * sc_)
            BV.append((p.x, p.y, p.z))
            BC.append(weave(rgb, u, 0.5 + 0.5 * s, phase))
    for r in range(rows):
        i = b + r * 2
        BF.append((i, i + 1, i + 3, i + 2))


# Heights are ABSOLUTE and solved, not chosen (finding 98).  The street's walk
# surface is 19.00 and the master's corridor is 2.05, so nothing may hang below
# 21.05 — and the thing that hangs lowest is not the line, it is the PENNANT's
# point 0.50 m under it.  A first cut strung the runs at 21.20..21.35 with a
# 0.42 m sag, which put every pennant tip inside the corridor and the Corridor
# backstop threw 78 of 90 segments away: 12 flags for the whole street.  Solved:
# line 22.70, sag 0.28, low point 22.42, tip 21.92 — 0.87 m of margin, which
# is also what an 0.85 m lantern dropper needs to hang clear of the same band.
RUNS = [((25.30, 5.00), (30.10, 8.30), 22.70, 22.70, 0.28),
        ((30.60, 8.60), (36.40, 5.70), 22.70, 22.70, 0.28),
        ((37.90, 5.95), (43.50, 9.05), 22.70, 22.75, 0.28),
        ((44.60, 9.20), (50.60, 8.95), 22.75, 22.70, 0.28),
        ((42.60, 10.45), (46.60, 10.45), 22.65, 22.65, 0.24)]
# =========================================================================
# WHICH PRACTICALS THE STREET GETS  —  solved against an accepted district
# =========================================================================
# The 680 W practical is town canon: the same lamp lights four districts and it
# is not up for renegotiation here, so DENSITY is the only handle.  The order of
# solving matters.  The shopfront lamps are FIXED — a shop lights its own door,
# and that is the one lantern a player can explain — so they go first, and the
# strung lamps are then hung only where no shopfront lamp already lights that
# stretch.  On a 3 m street a strung lamp 1.7 m from a bracket lamp is not
# atmosphere, it is one pool of light paid for twice.
#
# LANT_MIN_SEP is MEASURED, not chosen.  Against the accepted Boatyard's own
# walking surface, sampled by the same down-ray grid `shelf_light.py` asserts on:
#     4 strung (no rule)       shelf mean 22.42 W/m2 = 1.25x the Boatyard's 17.91
#     3 strung (sep 2.6 m)                 20.32       1.14x
#     2 strung (sep 3.0 m)                 17.90       1.00x   <- adopted
# 3.0 m drops exactly the two redundant lamps — the mid-street one is 2.29 m from
# the item shop's bracket and the east one 1.67 m from home-b's — and keeps the
# two that hang over genuinely unlit stretches (3.66 m and 3.91 m clear).  Parity
# with a district the user has already accepted is the target; sitting well UNDER
# it would be the other half of the same failure (finding 100).
LANT_MIN_SEP = 3.00
SHOPFRONT_LAMPS = [(IX0 - 0.30, 3.35, 'x-'), (QX0 + 1.05, QY1 + 0.10, 'y+'),
                   (WX0 + 1.15, WY0 - 0.10, 'y-'), (AX0 + 1.20, AY0 - 0.10, 'y-'),
                   (48.85, 10.60, 'y-'), (47.85, 5.15, 'y+'), (52.35, 4.80, 'y+')]


def bracket_at(bx, by, face):
    """Where a shopfront bracket's lamp actually ends up, or None if the corridor
    refuses the bracket.  Shared by the density solver below and the builder
    further down, so the two can never disagree about where the lamps are."""
    lz = gz(bx, by) + 2.62
    ox = -0.42 if face == 'x-' else 0.0
    oy = 0.42 if face == 'y+' else (-0.42 if face == 'y-' else 0.0)
    if over_walk(COR, bx + ox, by + oy, lz - 0.30, pad=0.14):
        return None
    return Vector((bx + ox, by + oy, lz))


WALL_PTS = [q for q in (bracket_at(*s) for s in SHOPFRONT_LAMPS) if q is not None]
LAMP_PTS = []
for ri, (a, b2, za, zb2, sag) in enumerate(RUNS[:4]):
    A = Vector((a[0], a[1], za))
    B = Vector((b2[0], b2[1], zb2))
    p = A.lerp(B, 0.50) - Vector((0, 0, sag * math.sin(math.pi * 0.50)))
    if any((p.xy - q.xy).length < LANT_MIN_SEP for q in WALL_PTS):
        continue
    LAMP_PTS.append(p)


def near_lamp(p, r=0.95):
    return any((p - q).length < r for q in LAMP_PTS)


nflag, nthin = 0, 0
for ri, (a, b2, za, zb2, sag) in enumerate(RUNS):
    A = Vector((a[0], a[1], za))
    B = Vector((b2[0], b2[1], zb2))
    n = 18
    prev = None
    for k in range(n + 1):
        t = k / n
        p = A.lerp(B, t) - Vector((0, 0, sag * math.sin(math.pi * t)))
        if prev is not None:
            c = (prev + p) / 2
            # Bunting heights are ABSOLUTE and its sag is per run (finding 98):
            # every segment is Corridor-tested as a backstop, and the pennant's
            # own tip is tested 0.46 m lower.
            if not over_walk(COR, c.x, c.y, c.z, pad=0.10):
                LINEP.append((prev.copy(), p.copy()))
                nf = near_field(c.x, c.y, c.z - 0.30, 0.45)
                step = 2 if nf > 0.62 else (3 if nf > 0.25 else 5)
                if k % step == 0 and not over_walk(COR, c.x, c.y, c.z - 0.50, pad=0.10) \
                        and not near_lamp(c):
                    if nf <= 0.02:
                        nthin += 1
                    else:
                        pennant(c, p - prev, 0.34 + 0.10 * rng.random(),
                                CLOTHC[(k + ri * 3) % len(CLOTHC)], k * 1.31 + ri * 0.7)
                        nflag += 1
                elif k % step == 0:
                    nthin += 1
        prev = p
if BV:
    me = bpy.data.meshes.new("shelf_bunting")
    me.from_pydata(BV, [], BF)
    me.validate()
    me.materials.append(MCLOTH)
    ca = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for i, c in enumerate(BC):
        ca.data[i].color = (c[0], c[1], c[2], 1.0)
    BUNT = bpy.data.objects.new("shelf_bunting", me)
    link(BUNT, COLL)
parts = [cyl("bl", a, b2, 0.018, 5, MROPE, COLL) for a, b2 in LINEP]
LINES = join_meshes(parts, "shelf_bunting_lines", COLL)
log("BUILD", "shelf_bunting / shelf_awnings",
    "%d runs, %d pennants (%d thinned out of the near field), %d awnings — "
    "the weave and the sun-fade are baked into VERTEX COLOURS, not a noise tree, "
    "so the cloth survives the glTF round trip (GLTF-SURVIVAL GATE)"
    % (len(RUNS), nflag, nthin, len(AWNINGS)))

# =========================================================================
# 8. LANTERNS — ordinary, warm.  (Heartlights do not exist in Dellhollow.)
# =========================================================================
LANTS = []


def lantern(name, x, y, z):
    p = [obox("gl", x, y, z, 0.155, 0.155, 0.26, mat=MGLASS, cname=COLL),
         obox("cp", x, y, z + 0.17, 0.21, 0.21, 0.055, mat=MIRON, cname=COLL),
         obox("bs", x, y, z - 0.16, 0.19, 0.19, 0.04, mat=MIRON, cname=COLL)]
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p.append(obox("cg", x + sx * 0.072, y + sy * 0.072, z, 0.024, 0.024, 0.34,
                      mat=MIRON, cname=COLL))
    ob = join_meshes(p, name, COLL)
    li = bpy.data.lights.new(name.replace("shelf_", "KEYSH_") + "_light", 'POINT')
    li.energy = 680.0                       # the town standard, three districts old
    li.color = (1.0, 0.58, 0.24)
    li.shadow_soft_size = 0.10
    li.use_custom_distance = True
    li.cutoff_distance = 14.0
    li.shadow_maximum_resolution = 0.01
    lo = bpy.data.objects.new(li.name, li)
    lo.location = (x, y, z + 0.02)
    link(lo, COLL)
    LANTS.append(li.name)
    return ob


brackets = []
# on the buildings, over their own doors — the shopfront lamps.  Positions come
# from `bracket_at`, the same function the density solver used, so the lamps that
# were counted are exactly the lamps that get built.
for s in SHOPFRONT_LAMPS:
    q = bracket_at(*s)
    if q is None:
        continue
    bx, by = s[0], s[1]
    brackets.append(beam("br", (bx, by, q.z + 0.44), (q.x, q.y, q.z + 0.32),
                         0.055, 0.055, MIRON, COLL))
    lantern("shelf_lantern_%d" % len(LANTS), q.x, q.y, q.z)
# and the STRUNG lanterns the map asks for, hung on the bunting lines over the
# street — at the run midpoints LANT_MIN_SEP left standing, which is where the
# shopfronts are NOT already lighting the street.  `shelf_light.py` asserts the
# resulting walking-surface mean against the accepted Boatyard's.
for p in LAMP_PTS:
    # 0.85 m of dropper, not 0.46.  A 680 W practical is ~54 W/m2 at one metre:
    # hung level with the pennants it washed every flag within 1.5 m to cream and
    # threw away the entire vertex-coloured weave the cloth was built for.
    # Finding 129 has a lighting corollary — a DETAIL surface only reads if
    # something is not blowing it out.
    lz = p.z - 0.85
    # the test is the lamp's own BASE against the corridor ceiling, not a point
    # 2 m under it — the first cut tested (lz - CORRIDOR_H) and was asking
    # whether the street's floor was clear, which it never is.
    if over_walk(COR, p.x, p.y, lz - 0.22, pad=0.14):
        continue
    brackets.append(cyl("hk", (p.x, p.y, p.z), (p.x, p.y, lz + 0.20), 0.016, 5, MIRON, COLL))
    lantern("shelf_lantern_hang_%d" % len(LANTS), p.x, p.y, lz)
join_meshes(brackets, "shelf_lantern_brackets", COLL)
log("BUILD", "shelf_lantern_* x%d" % len(LANTS),
    "warm 680 W practicals, 14 m cutoff, %d on shopfronts and %d hung from the "
    "bunting lines over the street — the town standard, unchanged across four "
    "districts; there are no Heartlights in Dellhollow"
    % (len([n for n in LANTS if "hang" not in n]), len([n for n in LANTS if "hang" in n])))

# =========================================================================
# 9. PARAPET along the gorge rim — placed by SEARCH, never by taste
# =========================================================================
parts, posts = [], []
x = SX0 + 0.6
last = None
while x < SX1 - 0.4:
    yr = T.rim(x)
    y = yr - 0.45
    z = ground_top(x, y)
    tries = 0
    # OUTWARD, toward the lip.  A first cut stepped inward (y -= 0.12) and so
    # marched the post TOWARD the street it was trying to get clear of; the one
    # place the street runs right up to the rim (the loop-stair head at x~52) it
    # put a post inside the walk corridor.
    while (over_walk(COR, x, y, z + 0.55, pad=0.42) or in_solid(x, y)) and tries < 22:
        y += 0.11
        z = ground_top(x, y)
        tries += 1
    if tries >= 26 or not on_sheet(x, y) or T.winch_keepout(x, y):
        x += 0.98
        last = None
        continue
    p = Vector((x, y, z))
    posts.append(p)
    parts.append(obox("pp", x, y, z + 0.50, 0.18, 0.18, 1.12, mat=MT, cname=COLL))
    parts.append(obox("pc", x, y, z + 1.09, 0.26, 0.26, 0.09, mat=MT, cname=COLL))
    mid_ok = last is not None and (p - last).length < 2.5
    if mid_ok:
        m = (last + p) / 2
        # finding 97: anything that SPANS between two tested points has to be
        # tested at its midpoint too — the gate lost 14 samples to exactly this.
        if over_walk(COR, m.x, m.y, ground_top(m.x, m.y) + 0.42, pad=0.42) or in_solid(m.x, m.y):
            mid_ok = False
    if mid_ok:
        for zr, sag in ((0.96, 0.09), (0.56, 0.06)):
            mid = (last + p) / 2 + Vector((0, 0, zr - sag))
            parts.append(cyl("hl", last + Vector((0, 0, zr)), mid, 0.026, 5, MROPE, COLL))
            parts.append(cyl("hl", mid, p + Vector((0, 0, zr)), 0.026, 5, MROPE, COLL))
        c = (last + p) / 2
        parts.append(obox("kb", c.x, c.y, c.z + 0.19, (p - last).length + 0.22, 0.38, 0.42,
                          rz=math.atan2(p.y - last.y, p.x - last.x), mat=MSTONE, cname=COLL))
    last = p
    x += 0.98
PARAPET = join_meshes(parts, "shelf_parapet", COLL)
log("BUILD", "shelf_parapet", "%d posts found by walking OUT toward the lip until the "
    "walk corridor and the buildings released, rope handline + drystone kerb between "
    "them — the p-shelf-w camera note asks for 'gorge air beyond the rail'" % len(posts))

# =========================================================================
# the veneer, now that the buildings have registered their backs
# =========================================================================
CLIFF = build_veneer()
log("BUILD", "shelf_cliffface", "%d x 31 veneer over cliff_town from x %.2f..%.2f "
    "(the gate's stops at 31.44), crest %.1f..%.1f m modulated and held above "
    "cliff_town's own top edge at 37.0, foot at %.1f so no ray under our plate "
    "finds the slab, pressed to 0.10 m behind %d buildings"
    % (CX_N, CVX0, CVX1,
       min(cliff_crest(CVX0 + i * CST) for i in range(CX_N)),
       max(cliff_crest(CVX0 + i * CST) for i in range(CX_N)), CFLOOR, len(BACKS)))

# =========================================================================
# 10. VEGETATION
# =========================================================================
VEGN = 0


def clone(src_name, tag, n, xr, yr, lo, hi, mode="ground", zjit=0.0, cull=True):
    global VEGN
    src = bpy.data.objects.get(src_name)
    if src is None:
        return 0
    made = 0
    for i in range(n):
        px = xr[0] + rng.random() * (xr[1] - xr[0])
        if mode == "rim":
            py = T.rim(px) - 0.12 - rng.random() * 1.15
        elif mode == "face":
            py = T.rim(px) + 0.20 + rng.random() * 0.70
        elif mode == "cliff":
            py = 1.05 + rng.random() * 0.85
        else:
            py = yr[0] + rng.random() * (yr[1] - yr[0])
        if not on_sheet(px, py) or gate_solid(px, py):
            continue
        pz = ground_top(px, py)
        if pz < 15.0:
            continue
        s = lo + rng.random() * (hi - lo)
        if over_walk(KEEP, px, py, pz + 0.45, pad=0.35 * s) or in_solid(px, py):
            continue
        r = road_at(px, py)
        if r is not None and r[1] < PAVE_W + 0.45:
            continue
        b0 = world_bbox(src)
        ext = max(b0[1] - b0[0], b0[3] - b0[2], b0[5] - b0[4]) * s
        # findings 122/123: cull the masses, only SIZE-cap the ground cover — a
        # fern on the floor never stands between a lens and its subject, and
        # culling it makes the tier go bald exactly where the cameras point.
        nf = near_field(px, py, pz + 0.45 * ext, ext)
        if cull and rng.random() > nf:
            continue
        s = min(s, lo + (hi - lo) * max(nf, 0.20 if not cull else 0.0))
        ob = src.copy()
        ob.data = src.data.copy()
        ob.name = "veg_shelf_%s_%d" % (tag, i)
        ob.data.name = ob.name
        b = world_bbox(src)
        cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
        rot = 0.0 if tag == "creeper" else rng.random() * 6.28
        c, sn = math.cos(rot), math.sin(rot)
        for v in ob.data.vertices:
            p = src.matrix_basis @ v.co
            q = Vector(((p.x - cx) * s, (p.y - cy) * s, (p.z - cz) * s))
            v.co = Vector((q.x * c - q.y * sn, q.x * sn + q.y * c, q.z))
        ob.matrix_basis.identity()
        bb = world_bbox(ob)
        ob.location = Vector((px, py, pz - bb[4] - 0.06 + zjit))
        link(ob, COLL)
        made += 1
        VEGN += 1
    return made


ng = clone("seam_tuft_0", "tuft", 96, (SX0 + 0.5, SX1 - 0.5), None, 0.7, 1.5,
           mode="rim", cull=False)
ng += clone("seam_tuft_3", "tuft", 64, (SX0 + 0.5, SX1 - 0.5), None, 0.7, 1.4,
            mode="cliff", cull=False)
nf = clone("seam_tuft_1", "fern", 42, (SX0 + 0.5, SX1 - 0.5), None, 0.7, 1.3,
           mode="cliff", cull=False)
nf += clone("seam_tuft_37", "fern", 30, (SX0 + 0.5, SX1 - 0.5), None, 0.7, 1.3,
            mode="rim", cull=False)
nc = clone("creeper_4", "creeper", 18, (SX0 + 1.0, SX1 - 1.0), None, 0.6, 0.95,
           mode="face", zjit=-0.75, cull=False)
nc += clone("creeper_4", "creeper", 26, (CVX0 + 0.5, CVX1 - 3.0), None, 0.7, 1.15,
            mode="cliff", zjit=0.35, cull=False)
nk = clone("rimclump_3", "rimclump", 20, (SX0 + 1.0, SX1 - 1.0), None, 0.6, 1.0, mode="rim")
# autumn crowns seated ON the new crest — the skyline, and 18 m above and behind
# every camera's near field, so they are EXEMPT from the thinning (finding 71/78)
crest = []
for i in range(20):
    px = CVX0 + 0.8 + rng.random() * (CVX1 - CVX0 - 1.6)
    src = bpy.data.objects.get("rimclump_%d" % rng.randint(1, 12))
    if src is None:
        continue
    ob = src.copy(); ob.data = src.data.copy()
    ob.name = "veg_shelf_rimclump_crest_%d" % i; ob.data.name = ob.name
    sc_ = 0.85 + rng.random() * 0.9
    b = world_bbox(src)
    cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
    for v in ob.data.vertices:
        q = src.matrix_basis @ v.co
        v.co = Vector(((q.x - cx) * sc_, (q.y - cy) * sc_, (q.z - cz) * sc_))
    ob.matrix_basis.identity()
    bb = world_bbox(ob)
    ob.location = Vector((px, -0.10 + rng.random() * 0.55,
                          cliff_crest(px) - bb[4] - (bb[5] - bb[4]) * 0.40))
    link(ob, COLL)
    crest.append(ob)
log("BUILD", "veg_shelf_*", "%d tufts, %d ferns, %d creepers, %d clumps on the rim, "
    "%d autumn crowns on the new crest — everything Corridor-, paving-, building- "
    "and near-field-tested" % (ng, nf, nc, nk, len(crest)))

# =========================================================================
# 11. CLUTTER — the working life of a shop street
# =========================================================================
parts = []
placed = 0
ZONES = [
    (24.40, 29.60, 6.30, 7.60, 14, "inn"),
    (30.40, 35.40, 6.10, 7.30, 12, "shop"),
    (35.40, 39.90, 7.10, 8.30, 10, "forge"),
    (40.10, 46.20, 4.90, 7.30, 16, "market"),
    (42.40, 46.60, 9.70, 10.50, 6, "armor"),
    (47.20, 52.60, 5.20, 7.30, 14, "homes"),
    (19.60, 24.40, 6.60, 9.20, 10, "stair"),
    (51.20, 55.00, 5.20, 7.20, 8, "east"),
    (33.00, 39.60, 9.40, 11.60, 10, "rail"),
]
for (x0, x1, y0, y1, n, kind) in ZONES:
    for i in range(n * 5):
        if placed >= sum(z[4] for z in ZONES):
            break
        px = x0 + rng.random() * (x1 - x0)
        py = y0 + rng.random() * (y1 - y0)
        if not on_sheet(px, py) or gate_solid(px, py):
            continue
        pz = ground_top(px, py)
        if pz < 18.4:
            continue
        # a joined multi-part mesh is audited by its BBOX corners (finding 96), so
        # one piece cantilevered over the lip makes the whole object a stray:
        # every piece needs ground under its whole FOOTPRINT.
        if any(not on_sheet(px + dx, py + dy) or
               abs(ground_top(px + dx, py + dy) - pz) > 0.80
               for dx, dy in ((0.40, 0), (-0.40, 0), (0, 0.40), (0, -0.40))):
            continue
        if over_walk(KEEP, px, py, pz + 0.7, pad=0.44) or in_solid(px, py):
            continue
        r = road_at(px, py)
        if r is not None and r[1] < PAVE_W + 0.30:
            continue
        if rng.random() > near_field(px, py, pz + 0.5, 1.05):
            continue
        k = rng.random()
        rz = rng.random() * 3.14
        if k < 0.28:
            parts.append(obox("cr", px, py, pz + 0.36, 0.74, 0.68, 0.72, rz=rz,
                              mat=MWALLD, cname=COLL))
            for e in range(2):
                parts.append(obox("cb", px, py, pz + 0.15 + e * 0.42, 0.78, 0.72, 0.07,
                                  rz=rz, mat=MT, cname=COLL))
        elif k < 0.50:
            parts.append(cyl("br", (px, py, pz), (px, py, pz + 0.84), 0.31, 12,
                             MWALLD, COLL, r2=0.28))
            for e in (0.15, 0.42, 0.69):
                parts.append(cyl("bh", (px, py, pz + e), (px, py, pz + e + 0.05), 0.325,
                                 12, MIRON, COLL))
        elif k < 0.68:
            for e in range(rng.randint(2, 4)):
                parts.append(obox("sk", px + rng.uniform(-.20, .20), py + rng.uniform(-.20, .20),
                                  pz + 0.19 + e * 0.30, 0.68, 0.48, 0.32,
                                  rz=rz + e * 0.5, mat=MSACK, cname=COLL))
        elif k < 0.84:
            parts.append(obox("pl", px, py, pz + 0.08, 1.24, 1.00, 0.13, rz=rz, mat=MT, cname=COLL))
            for e in range(rng.randint(2, 5)):
                parts.append(cyl("pk", (px + rng.uniform(-.34, .34), py + rng.uniform(-.28, .28), pz + 0.15),
                                 (px + rng.uniform(-.34, .34), py + rng.uniform(-.28, .28), pz + 0.48),
                                 0.22, 10, MPUMPKIN, COLL))
        else:
            for e in range(4):
                parts.append(cyl("rc", (px, py, pz + 0.03 + e * 0.05),
                                 (px, py, pz + 0.06 + e * 0.05), 0.28 - e * 0.042, 12,
                                 MROPE, COLL))
        placed += 1
CLUTTER = join_meshes(parts, "shelf_clutter", COLL)
log("BUILD", "shelf_clutter", "%d crate stacks / barrels / sack piles / pumpkin pallets "
    "/ rope coils, every one clear of the walking lines, the paving and the shopfronts"
    % placed)

# =========================================================================
print("\n" + "=" * 78)
print("SHELF DISTRICT: %d objects in %s" % (len(bpy.data.collections[COLL].objects), COLL))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
