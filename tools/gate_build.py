"""gate_build.py — the GATE APPROACH district (parcel `p-gate`).

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/gate_build.py -- save

Built on a BRANCH copy of the master under the parallel branch-district protocol:
ADDITIVE ONLY.  Every object this script makes is named `gate_*` (lamps `KEYG_*`)
and lives in the collection `GATE_DISTRICT`.  The only permitted deletions are
`lm_` blockout shells of p-gate's own members, and every one of them is recorded
in `tools/blends/districts/gate_branch_deletions.json`.

Nothing else in the file is moved, edited, renamed or hidden — in particular the
walk_/bar_ meshes keep even their `hide_render` flags, because a branch merges by
appending THIS collection, so a flag set on a master object would not survive it
anyway (the merge custodian applies the manifest-51 render-hiding after the
merge, town-wide, in one pass).

Reading order of the district, which is also the order it is built:
  1  ground        the rock promontory the gate stands on + the eastern gallery
  2  road          packed-earth carriageway laid on the walk graph
  3  arch          THE Valley Gate: the player's first frame of Dellhollow
  4  gatehouse     the toll house and its barrier
  5  yard          Porters' Yard: pallets, mule lines, the staging clutter
  6  winch         Cargo Winch head, and its rope down to the quay's winch foot
  7  parapet       the guard along the rim, placed by search, never by taste
  8  bunting       the festival motif, carried up from the quay
  9  lanterns      ordinary warm practicals (there are no Heartlights here)
 10  vegetation    autumn crowns on the rim, tufts and creepers on the rock
 11  clutter       the working life of a gate: crates, barrels, sacks, rope
"""
import bpy, bmesh, math, os, random, sys, json
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          M, world_bbox, offset_poly, plane_z_fn, point_in_poly,
                          dist_poly2, Corridor)
from gate_lib import (Terrain, over_walk, GX0, GX1, GY0, GY1, SHELF, PLATE_BOT,
                      BASEZ, SOLID_X, HIGH_Z, DECK_DROP, CORRIDOR_H)

SAVE = "save" in sys.argv
COLL = "GATE_DISTRICT"
rng = random.Random(20260801)
LOG = []
DELETIONS = REPO + "/tools/blends/districts/gate_branch_deletions.json"


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-32s %s" % (kind, what, why))


print("=" * 78)
print("GATE APPROACH DISTRICT  —  parcel p-gate")
print("=" * 78)

# ---------------------------------------------------------------- materials
MROCK, MIRON, MROPE = M("mat_rock"), M("mat_iron"), M("mat_rope")
MT, MTD, MDECK = M("mat_timber"), M("mat_timber_dark"), M("mat_deck")
MWALL, MWALLD = M("mat_wallwood"), M("mat_wallwood_dark")
MRED, MBLUE = M("mat_paint_red"), M("mat_paint_blue")
MSHINGLE, MGLASS = M("mat_shingle_mossy"), M("mat_lantern_glass")
MGATE, MFRESH = M("mat_gate_timber"), M("mat_freshwood")
MCANVAS, MNET = M("mat_canvas"), M("mat_net")
MPUMPKIN, MTAR = M("mat_pumpkin"), M("mat_tar")
MFLAG = [M("mat_flag_red"), M("mat_flag_green"), M("mat_flag_blue"), M("mat_flag_ochre")]


def plain(name, rgb, rough=0.80, metal=0.0):
    m = bpy.data.materials.get(name)
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


def derive(src, name, scale=None, tint=None, fac=0.85, mode='MULTIPLY'):
    """A new surface DERIVED from one of the town's textured materials.

    v1 of this district gave its ground, its road and its masonry flat
    Principled colours at 0.09..0.13 albedo, on the theory that the number was
    what mattered.  It is not: next to the Boatyard's box-projected, AO-multiplied,
    moss-graded surfaces a flat colour reads as untextured cream no matter how
    dark the number is (manifest 53 from the other side — the value gap the eye
    actually sees is a DETAIL gap).  Copying `mat_rock` and re-tinting it keeps
    the box projection, the AO multiply, the roughness map and — the thing that
    does the most work here — the moss layer driven by the world-up normal, which
    grasses the flat tier and leaves the cliff faces bare for free.
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


MROAD = derive("mat_rock", "mat_gate_road", scale=0.92, tint=(0.42, 0.33, 0.25))
MTURF = derive("mat_rock", "mat_gate_turf", scale=0.52, tint=(0.40, 0.41, 0.29))
MSTONE = derive("mat_rock", "mat_gate_stone", scale=1.60, tint=(0.55, 0.52, 0.47))
MSACK = derive("mat_timber", "mat_gate_sack", scale=1.90, tint=(0.74, 0.63, 0.44))
MPOOL = plain("mat_gate_troughwater", (0.021, 0.040, 0.044), rough=0.12)

# ------------------------------------------------------------- collection(s)
coll(COLL)

killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("gate_", "KEYG_")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
if killed:
    log("REBUILD", "%d gate_/KEYG_ objects cleared" % killed, "idempotent re-run")

# =========================================================================
# 0. DELETIONS — the blockout shells this district replaces
# =========================================================================
# Only p-gate's OWN members, and only shells that lie inside the parcel.  The
# Porters' Yard's shell is `walk_lm_porters-yard`, a WALK mesh: canonical
# topology, untouchable, so the yard is built AROUND its own pad.
DEL_PREFIX = ("lm_valley-gate", "lm_gatehouse", "lm_winch-head")
deleted = []
for o in list(bpy.data.objects):
    if o.name.startswith(DEL_PREFIX):
        b = world_bbox(o)
        deleted.append({"name": o.name,
                        "bbox_min": [round(v, 3) for v in (b[0], b[2], b[4])],
                        "bbox_max": [round(v, 3) for v in (b[1], b[3], b[5])],
                        "landmark": o.name.split("_")[1],
                        "verts": len(o.data.vertices)})
        bpy.data.objects.remove(o, do_unlink=True)
manifest = {
    "district": "gate-approach",
    "parcel": "p-gate",
    "branch_blend": "tools/blends/dellhollow-master-gate-branch.blend",
    "rule": "ADDITIVE-ONLY except lm_ blockout shells of p-gate's own members. "
            "The merge custodian must delete exactly these object names from the "
            "live master before appending GATE_DISTRICT.",
    "note": "lm_valley-gate_*, lm_gatehouse_* and lm_winch-head_* are the shells of "
            "three of p-gate's four members and are replaced by built art. "
            "lm_gatehouse_roof's apex reaches z=28.55, 1.05 m above the parcel's "
            "nominal 27.5 ceiling; it is the roof of a body that is wholly inside "
            "the parcel, and deleting the body without it would leave a slab "
            "floating over the toll yard. The fourth member, porters-yard, has no "
            "lm_ shell at all - its blockout is walk_lm_porters-yard, a canonical "
            "walk mesh, which is NOT touched. Nothing outside p-gate is deleted; "
            "lm_inn_* and lm_item-shop_* stand and are built around.",
    "deleted": sorted(deleted, key=lambda d: d["name"]),
}
os.makedirs(os.path.dirname(DELETIONS), exist_ok=True)
json.dump(manifest, open(DELETIONS, "w"), indent=1)
log("DELETE", "%d lm_ blockout shells" % len(deleted),
    "recorded in districts/gate_branch_deletions.json: %s"
    % ", ".join(d["name"] for d in sorted(deleted, key=lambda d: d["name"])))

# =========================================================================
# corridors + terrain
# =========================================================================
T = Terrain()
COR0, COR, KEEP = T.cor0, T.cor, T.keep
log("MODEL", "walk corridors", "%d tier faces, %d lower faces (%d within the 2 m "
    "band under the gallery)" % (len(T.high), len(T.low), len(T.hot)))


def free(x, y, z, pad=0.18):
    return not over_walk(COR, x, y, z, pad=pad)


# Footprints nothing loose may stand in.  Declared EXPLICITLY, one rectangle per
# structure: every structure here is a joined multi-part mesh, and a joined mesh's
# bounding box is not its footprint (the yard's cart alone stretched the yard's
# bbox across 9 m of open ground and the keep-out swallowed the whole district).
SOLIDS = [
    (3.90, 9.80, -0.25, 3.25),    # porters' shed
    (0.40, 5.10, 2.30, 5.45),      # tarpaulin lean-to
    (10.15, 14.95, 0.00, 4.85),    # gatehouse + chimney + pentice
    (14.60, 15.75, 2.85, 9.00),    # toll barrier
    (15.80, 17.55, 0.80, 7.20),    # the arch's piers
    (16.05, 17.20, -0.60, 10.70),  # palisade wings + leaves
    (25.45, 29.25, 3.70, 6.40),    # winch derrick
    (10.60, 14.70, 9.55, 10.60),   # mule line + trough
    (18.40, 21.10, 7.55, 9.90),    # the waiting cart
]


def in_solid(x, y):
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in SOLIDS)


def register(ob, pad=0.0):
    return ob


def walk_ref(x, y):
    """(effective walk top, distance) for the gate-tier walk graph."""
    inside = None
    for raw, fn, zt, nm in T.high:
        if point_in_poly(x, y, raw):
            v = fn(x, y)
            inside = v if inside is None else max(inside, v)
    if inside is not None:
        return inside, 0.0
    best, bz = 1e9, None
    for raw, fn, zt, nm in T.high:
        d = dist_poly2(x, y, raw)
        if d < best:
            best, bz = d, T.plane_at(raw, fn, x, y, d)
    return bz, best


# the western approach: the road the player actually arrives on.  There is no
# walk mesh out here — the map's exit is the arch itself — so the carriageway is
# carried on its own spine until it goes round the bluff and off the parcel.
SPINE = [Vector((1.30, 6.05, 0)), Vector((3.20, 6.85, 0)), Vector((5.10, 7.65, 0))]
ROAD_W = 1.42          # half-width added to a walk ribbon
GROUND_DROP = 0.36     # the carriageway slab's thickness


def spine_d(x, y):
    best = 1e9
    for i in range(len(SPINE) - 1):
        a, b = SPINE[i], SPINE[i + 1]
        ab = Vector((b.x - a.x, b.y - a.y))
        L2 = ab.length_squared
        t = max(0.0, min(1.0, ((x - a.x) * ab.x + (y - a.y) * ab.y) / L2))
        best = min(best, math.hypot(x - (a.x + t * ab.x), y - (a.y + t * ab.y)))
    return best


def road_at(x, y):
    """(top z, distance from the carriageway centre) or None."""
    z, d = walk_ref(x, y)
    if d < ROAD_W + 1.6:
        return z - DECK_DROP, d
    ds = spine_d(x, y)
    if ds < 2.55:
        return T.natural(x, y) - 0.30, ds
    return None


def road_blocked(x, y, ztop):
    """A carriageway slab may not overhang a walk that is close below it."""
    for raw, fn, zt, nm in T.low:
        if zt >= ztop - 0.10 or zt < ztop - GROUND_DROP - CORRIDOR_H:
            continue
        if dist_poly2(x, y, raw) < 0.02:
            top = COR0.top_at(x, y)
            if top is not None and top > zt + 0.05:
                continue                      # buried under a higher walk
            return True
    return False


# =========================================================================
# 1. GROUND
# =========================================================================
def ground_top(x, y):
    h = T.natural(x, y)
    for raw, fn, zt, nm in T.high:
        d = dist_poly2(x, y, raw)
        if d < 5.4:
            h = min(h, T.plane_at(raw, fn, x, y, d) - GROUND_DROP
                    + max(0.0, d - (ROAD_W + 0.50)) * 1.15)
    for raw, fn, zt, nm in T.low:
        if x > SOLID_X:
            break                                # the gallery plate never terraces
        d = dist_poly2(x, y, raw)
        if d >= 2.2:
            continue
        top = COR0.top_at(x, y)
        if top is not None and top > zt + 0.05:
            continue
        lo = zt + d * 1.15 - GROUND_DROP
        if lo < h < zt + CORRIDOR_H + d * 0.6:
            h = lo
    over = y - T.rim(x)
    if over > 0.0 and x <= SOLID_X + 0.80:
        h -= 30.0 * (over ** 1.30)
    return max(h, BASEZ)


ST = 0.34
NX = int(round((GX1 - GX0) / ST)) + 1
NY = int(round((GY1 - GY0) / ST)) + 1
NODE = {}
for i in range(NX):
    for j in range(NY):
        x, y = GX0 + i * ST, GY0 + j * ST
        if not T.has_ground(x, y):
            continue
        t = ground_top(x, y)
        NODE[(i, j)] = (x, y, t, T.bottom(x, y, t))

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
        rise = max(zs) - min(zs)
        MI.append(1 if (rise < 0.34 and min(zs) > 21.0) else 0)
        F.append((boti[d], boti[c], boti[b], boti[a])); MI.append(0)
        # the skirt, wherever the sheet stops
        for (na, nb, oi, oj) in ((a, d, -1, 0), (b, c, 1, 0), (a, b, 0, -1), (d, c, 0, 1)):
            if cell(i + oi, j + oj):
                continue
            F.append((topi[na], topi[nb], boti[nb], boti[na])); MI.append(0)

me = bpy.data.meshes.new("gate_ground")
me.from_pydata(V, [], F)
me.validate()
for m in (MROCK, MTURF):
    me.materials.append(m)
for p, mi in zip(me.polygons, MI):
    p.material_index = mi
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
GROUND = bpy.data.objects.new("gate_ground", me)
link(GROUND, COLL)
log("BUILD", "gate_ground", "%d nodes, %d faces — solid rock promontory west of "
    "x=%.1f (foot at z=%.0f), a %.2f m gallery plate east of it whose underside "
    "clears the Inn/Item-Shop roofs" % (len(NODE), len(F), SOLID_X, BASEZ,
                                        SHELF - PLATE_BOT))

# =========================================================================
# 1b. THE CLIFF FACE BEHIND THE TIER
# =========================================================================
# `cliff_town` is the town's backdrop: ONE 170 x 6 x 46 m box at y -6..0 with a
# blockout material.  Every other district looks at it from water level, edge-on
# or in shadow.  The gate tier is 24 m up and its road runs 4..9 m in FRONT of
# it, and the sun travels toward -y — so it hits that slab square on and the
# player's first frame of Dellhollow has a blown white wall behind the gate.
# (Ray-cast to be sure: the pale field in gate_v1..v5 `arrival` is `cliff_town`
# at 28 m, not the sky.)  cliff_town is untouchable far-rim geometry, so the fix
# is a VENEER standing in front of it, inside the parcel: real rock texture, a
# modulated crest instead of a straight skyline (manifest 7), pressed flat to
# 0.10 m wherever a building backs onto it so nothing is disturbed.
CST = 0.38
CX_N = int(round((GX1 - GX0) / CST)) + 1
CZ0, CZ1 = 34.60, 0.0


def cliff_crest(x):
    return 33.10 + 2.30 * math.sin(x * 0.21 + 0.7) + 1.15 * math.sin(x * 0.63 - 1.9) \
        + 0.55 * math.sin(x * 1.47 + 3.1)


def cliff_front(x, z, zb):
    u = min(1.0, max(0.0, (z - zb) / max(cliff_crest(x) - zb, 1.0)))
    d = 0.10 + 0.72 * (1.0 - u) ** 1.25
    d += (math.sin(x * 0.83 + z * 0.55) * 0.40 + math.sin(x * 2.11 - z * 1.31) * 0.22
          + math.sin(x * 4.7 + z * 3.3) * 0.08) * 0.34
    if in_solid(x, 1.0) or in_solid(x, 0.4):
        d = min(d, 0.10)
    return max(0.04, d)


CV, CF = [], []
rows = []
for i in range(CX_N):
    x = GX0 + i * CST
    zb = ground_top(x, 0.55) - 1.60
    n = 26
    col = []
    for k in range(n + 1):
        z = zb + (cliff_crest(x) - zb) * (k / n) ** 0.92
        col.append((len(CV), z))
        CV.append((x, cliff_front(x, z, zb), z))
    for k in range(n + 1):
        z = col[k][1]
        CV.append((x, -0.60, z))
    rows.append((col, len(CV) - (n + 1)))
NN = 27
for i in range(CX_N - 1):
    a0 = rows[i][0][0][0]
    b0 = rows[i + 1][0][0][0]
    a1 = rows[i][1]
    b1 = rows[i + 1][1]
    for k in range(NN - 1):
        CF.append((a0 + k, b0 + k, b0 + k + 1, a0 + k + 1))          # front
        CF.append((a1 + k + 1, b1 + k + 1, b1 + k, a1 + k))          # back
    CF.append((a0 + NN - 1, a1 + NN - 1, b1 + NN - 1, b0 + NN - 1))  # crest
    CF.append((b0, b1, a1, a0))                                      # foot
for (a0, a1) in ((rows[0][0][0][0], rows[0][1]), (rows[-1][0][0][0], rows[-1][1])):
    for k in range(NN - 1):
        CF.append((a0 + k, a0 + k + 1, a1 + k + 1, a1 + k))
me = bpy.data.meshes.new("gate_cliffface")
me.from_pydata(CV, [], CF)
me.validate()
me.materials.append(MROCK)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
CLIFF = bpy.data.objects.new("gate_cliffface", me)
link(CLIFF, COLL)
log("BUILD", "gate_cliffface", "%d x %d veneer over cliff_town from x %.1f..%.1f, crest "
    "%.1f..%.1f m modulated (manifest 7), pressed flat behind every building — the "
    "pale slab the arrival frame was looking at"
    % (CX_N, NN, GX0, GX1, min(cliff_crest(GX0 + i * CST) for i in range(CX_N)),
       max(cliff_crest(GX0 + i * CST) for i in range(CX_N))))

# =========================================================================
# 2. ROAD — the carriageway, laid on the walk graph
# =========================================================================
RST = 0.26
RNX = int(round((GX1 - GX0) / RST)) + 1
RNY = int(round((GY1 - GY0) / RST)) + 1
RN = {}
for i in range(RNX):
    for j in range(RNY):
        x, y = GX0 + i * RST, GY0 + j * RST
        r = road_at(x, y)
        if r is None:
            continue
        z, d = r
        if d > ROAD_W + 0.45:
            continue
        if road_blocked(x, y, z):
            continue
        # the carriageway crowns very slightly and is rutted where the carts run
        crown = -0.030 * (d / max(ROAD_W, 0.1)) ** 2
        rut = -0.026 * math.exp(-((d - 0.62) / 0.26) ** 2) - 0.026 * math.exp(-((d - 1.10) / 0.26) ** 2)
        n = (math.sin(x * 2.9 + y * 1.7) * 0.5 + math.sin(x * 6.1 - y * 4.3) * 0.3) * 0.018
        zz = z + crown + rut + n
        for raw, fn, zt, nm in T.high:
            dd = dist_poly2(x, y, raw)
            if dd < 0.95:
                zz = min(zz, T.plane_at(raw, fn, x, y, dd) - DECK_DROP)
        RN[(i, j)] = (x, y, zz)

RV, RF = [], []
rt, rb = {}, {}
for k, (x, y, z) in RN.items():
    rt[k] = len(RV); RV.append((x, y, z))
    rb[k] = len(RV); RV.append((x, y, z - GROUND_DROP))


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

me = bpy.data.meshes.new("gate_road")
me.from_pydata(RV, [], RF)
me.validate()
me.materials.append(MROAD)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
ROAD = bpy.data.objects.new("gate_road", me)
link(ROAD, COLL)
log("BUILD", "gate_road", "%d nodes — %.1f m carriageway on every gate-tier walk "
    "ribbon plus the western approach spine, crowned and rutted, top %.0f mm under "
    "the walk surface so the master's down-ray still lands on canonical topology"
    % (len(RN), 2 * ROAD_W, DECK_DROP * 1000))

# =========================================================================
# 3. THE VALLEY GATE
# =========================================================================
GX = 16.67                        # the gate line
PIER = 1.16                       # pier section
YS, YN = 2.30, 5.70               # inner faces of the two piers (corridor +0.30)
parts = []


def gz(x, y):
    r = road_at(x, y)
    return (r[0] if r else ground_top(x, y))


for side, y0 in (("s", YS - PIER), ("n", YN)):
    yc = y0 + PIER / 2
    zb = gz(GX, yc) - 0.30
    # battered base, shaft, cap: a stone pier with a timber head
    parts.append(obox("p", GX, yc, zb + 0.52, PIER + 0.46, PIER + 0.46, 1.04, mat=MSTONE, cname=COLL))
    parts.append(obox("p", GX, yc, zb + 1.04 + 1.30, PIER, PIER, 2.60, mat=MSTONE, cname=COLL))
    parts.append(obox("p", GX, yc, zb + 3.79, PIER + 0.34, PIER + 0.34, 0.34, mat=MSTONE, cname=COLL))
    # a string course and a corbel band, not scattered quoins
    parts.append(obox("sc", GX, yc, zb + 2.28, PIER + 0.14, PIER + 0.14, 0.16, mat=MSTONE, cname=COLL))
    for sx in (-1, 1):
        parts.append(obox("cb", GX + sx * (PIER / 2 + 0.11), yc, zb + 3.42, 0.24, PIER - 0.22, 0.26,
                          mat=MSTONE, cname=COLL))
TOPZ = gz(GX, 4.0) - 0.30 + 3.96          # top of the pier caps
# the lintel: a boxed timber beam across the road, and its truss
parts.append(beam("l", (GX, YS - PIER, TOPZ + 0.36), (GX, YN + PIER, TOPZ + 0.36),
                  0.62, 0.72, MGATE, COLL))
for sx in (-1, 1):
    parts.append(beam("l", (GX + sx * 0.50, YS - PIER + 0.2, TOPZ + 0.92),
                      (GX + sx * 0.50, YN + PIER - 0.2, TOPZ + 0.92), 0.20, 0.24, MGATE, COLL))
for k in range(7):
    yy = YS - 0.5 + k * (YN - YS + 1.0) / 6.0
    parts.append(beam("s", (GX - 0.50, yy, TOPZ + 0.74), (GX + 0.50, yy, TOPZ + 0.74), 0.13, 0.13, MGATE, COLL))
# Knee braces springing from the piers into the beam — the "arch" read.  They
# spring at TOPZ-0.72, NOT at the pier's foot: a brace that reaches down into the
# opening eats the walk corridor's 2.0 m headroom over the gate pad, and the
# master's gate names the exact samples (manifest 76, the same lesson).
for sy, y0 in ((1, YS), (-1, YN)):
    for k in range(4):
        t0, t1 = k / 4.0, (k + 1) / 4.0

        def bp(t, sy=sy, y0=y0):
            return (GX, y0 + sy * 1.58 * t, TOPZ - 1.24 * (1 - t) ** 1.6)
        parts.append(beam("b", bp(t0), bp(t1), 0.46, 0.40, MGATE, COLL))
        parts.append(beam("b2", (GX - 0.60, bp(t0)[1], bp(t0)[2] - 0.10),
                          (GX - 0.60, bp(t1)[1], bp(t1)[2] - 0.10), 0.16, 0.22, MGATE, COLL))
        parts.append(beam("b2", (GX + 0.60, bp(t0)[1], bp(t0)[2] - 0.10),
                          (GX + 0.60, bp(t1)[1], bp(t1)[2] - 0.10), 0.16, 0.22, MGATE, COLL))
# the name board hung under the beam (clear of the 2 m corridor by 0.5 m)
parts.append(obox("ks", GX, 4.00, TOPZ + 0.10, 0.86, 0.62, 0.62, mat=MSTONE, cname=COLL))
# the name board, hung on the beam's town face so it is legible on the way OUT
BOARD = TOPZ + 0.50
parts.append(obox("nb", GX - 0.42, 4.00, BOARD, 0.10, 2.40, 0.66, mat=MTD, cname=COLL))
parts.append(obox("nf", GX - 0.47, 4.00, BOARD, 0.05, 2.56, 0.10, mat=MT, cname=COLL))
# a shingled cap over the beam keeps the rain off the joinery
for k in range(6):
    u = k / 5.0
    dep = ((YN + PIER + 0.5) - (YS - PIER - 0.5)) / 2 * (1 - u * 0.72)
    for sy in (-1, 1):
        parts.append(obox("rf", GX, 4.00 + sy * dep, TOPZ + 1.02 + u * 0.42, 1.90, 0.42, 0.09,
                          mat=MSHINGLE, cname=COLL))
parts.append(beam("rg", (GX - 0.95, 4.00, TOPZ + 1.48), (GX + 0.95, 4.00, TOPZ + 1.48), 0.20, 0.16, MGATE, COLL))
ARCH = register(join_meshes(parts, "gate_arch", COLL), pad=0.30)

# the leaves, standing open against the piers — an open gate is the invitation
parts = []
for tag, ya, yb in (("s", YS - 0.06, 0.10), ("n", YN + 0.06, 7.90)):
    zb = gz(GX, (ya + yb) / 2) - 0.06
    yc, L = (ya + yb) / 2, abs(yb - ya)
    parts.append(obox("lf", GX - 0.38, yc, zb + 1.62, 0.15, L, 3.10, mat=MGATE, cname=COLL))
    for r in range(3):
        parts.append(obox("bt", GX - 0.46, yc, zb + 0.46 + r * 1.10, 0.06, L - 0.14, 0.17,
                          mat=MIRON, cname=COLL))
    parts.append(obox("hg", GX - 0.30, ya, zb + 2.30, 0.34, 0.22, 0.14, mat=MIRON, cname=COLL))
    parts.append(obox("hg", GX - 0.30, ya, zb + 0.80, 0.34, 0.22, 0.14, mat=MIRON, cname=COLL))
GATE_LEAF = join_meshes(parts, "gate_leaves", COLL)

# the palisade wings: the arch is only a gate if there is a wall either side
parts = []
WING = [("s", YS - PIER, -0.45, -1), ("n", YN + PIER, 10.55, 1)]
for tag, y0, y1, sgn in WING:
    n = max(2, int(abs(y1 - y0) / 0.42))
    for k in range(n + 1):
        yy = y0 + (y1 - y0) * k / n
        if abs(yy - y0) < 0.05:
            continue
        zb = gz(GX, yy)
        h = 3.05 + 0.28 * math.sin(k * 1.7) - 0.35 * max(0.0, (abs(yy - y0) - 3.0) / 4.0)
        parts.append(obox("pl", GX, yy, zb + h / 2 - 0.35, 0.30, 0.34, h, mat=MGATE, cname=COLL))
        parts.append(obox("pt", GX, yy, zb + h - 0.35 + 0.16, 0.22, 0.24, 0.32, mat=MGATE, cname=COLL))
    for zr in (1.05, 2.35):
        parts.append(beam("rl", (GX - 0.24, y0, gz(GX, y0) + zr), (GX - 0.24, y1, gz(GX, y1) + zr),
                          0.16, 0.20, MGATE, COLL))
    # buttress posts on the town side, every 2.2 m
    k = 0.9
    while k < abs(y1 - y0):
        yy = y0 + sgn * k
        zb = gz(GX, yy)
        parts.append(beam("bp", (GX - 0.22, yy, zb + 2.55), (GX - 1.35, yy, zb - 0.10), 0.20, 0.24, MT, COLL))
        k += 2.2
PALI = register(join_meshes(parts, "gate_palisade", COLL), pad=0.30)
log("BUILD", "gate_arch / gate_leaves / gate_palisade",
    "stone piers + boxed timber lintel at z=%.2f (soffit %.2f m over the road, "
    "corridor needs 2.05), leaves standing open, palisade wings running to the "
    "cliff and out to the rim so the arch is the only way in" % (TOPZ, TOPZ - 24.06))

# =========================================================================
# 4. GATEHOUSE (toll)
# =========================================================================
HX, HY = 12.55, 2.00              # body centre — cliff side, window onto the road
parts = []
zb = ground_top(HX, HY)
BW, BD = 4.16, 3.40
# stone lodge: one generous storey with a loft in the gable.  The parcel's
# nominal ceiling is 27.5 and the road is at 24.06, so a two-storey toll house
# cannot exist here; this keeps the same envelope as the shell it replaces
# (lm_gatehouse_roof topped out at 28.55).
parts.append(obox("g", HX, HY, zb + 1.42, BW, BD, 2.84, mat=MSTONE, cname=COLL))
parts.append(obox("pl", HX, HY, zb + 0.11, BW + 0.36, BD + 0.36, 0.42, mat=MSTONE, cname=COLL))
parts.append(obox("bd", HX, HY, zb + 2.90, BW + 0.26, BD + 0.26, 0.22, mat=MT, cname=COLL))
# a painted boarded gable over the stone, with its exposed frame
parts.append(obox("u", HX, HY, zb + 3.42, BW - 0.10, BD - 0.10, 0.86, mat=MWALLD, cname=COLL))
for k in range(6):
    parts.append(obox("fr", HX - BW / 2 + 0.34 + k * (BW - 0.68) / 5.0, HY + (BD - 0.10) / 2,
                      zb + 3.42, 0.17, 0.09, 0.84, mat=MT, cname=COLL))
# the toll window: a shuttered hatch onto the road, with a sill shelf
WY = HY + BD / 2
parts.append(obox("wh", HX + 0.55, WY + 0.02, zb + 1.70, 1.10, 0.16, 1.05, mat=MTD, cname=COLL))
parts.append(obox("ws", HX + 0.55, WY + 0.24, zb + 1.14, 1.42, 0.52, 0.10, mat=MT, cname=COLL))
parts.append(obox("wu", HX + 0.55, WY + 0.36, zb + 2.42, 1.42, 0.60, 0.09, mat=MT, cname=COLL))
for sx in (-1, 1):
    parts.append(beam("wb", (HX + 0.55 + sx * 0.62, WY + 0.06, zb + 1.34),
                      (HX + 0.55 + sx * 0.62, WY + 0.60, zb + 2.40), 0.07, 0.07, MT, COLL))
# a door and two upper windows
parts.append(obox("dr", HX - 1.35, WY + 0.02, zb + 1.10, 1.02, 0.14, 2.10, mat=MGATE, cname=COLL))
parts.append(obox("uw", HX - 1.30, WY - 0.02, zb + 3.44, 0.80, 0.10, 0.66, mat=MTD, cname=COLL))
# a small pentice over the toll hatch: shelter for whoever is being charged
for k in range(4):
    u = k / 3.0
    parts.append(obox("pt", HX + 0.55, WY + 0.16 + u * 0.86, zb + 3.05 - u * 0.30, 2.00, 0.34, 0.08,
                      mat=MSHINGLE, cname=COLL))
for sx in (-1, 1):
    parts.append(beam("pb", (HX + 0.55 + sx * 0.86, WY + 0.06, zb + 2.55),
                      (HX + 0.55 + sx * 0.86, WY + 0.96, zb + 2.80), 0.08, 0.10, MT, COLL))
# roof: mossy shingle, gable to the road
EAVE = zb + 3.02
RIDGE = EAVE + 1.68
for k in range(9):
    u = k / 8.0
    zz = EAVE + (RIDGE - EAVE) * u
    dep = (BD + 1.40) * (1 - u) / 2
    for sy in (-1, 1):
        parts.append(obox("rf", HX, HY + sy * dep, zz, BW + 1.05, 0.42, 0.11, mat=MSHINGLE, cname=COLL))
parts.append(beam("rg", (HX - (BW + 1.05) / 2, HY, RIDGE + 0.06),
                  (HX + (BW + 1.05) / 2, HY, RIDGE + 0.06), 0.24, 0.20, MT, COLL))
# chimney
parts.append(obox("ch", HX - 1.75, HY - 0.95, zb + 3.30, 0.82, 0.82, 3.30, mat=MSTONE, cname=COLL))
parts.append(obox("cc", HX - 1.75, HY - 0.95, zb + 5.02, 1.02, 1.02, 0.20, mat=MSTONE, cname=COLL))
# the toll board
parts.append(obox("tb", HX + 2.28, WY - 0.30, zb + 1.85, 0.05, 0.80, 0.98, mat=MTD, cname=COLL))
GATEHOUSE = register(join_meshes(parts, "gate_gatehouse", COLL), pad=0.45)

# the barrier: a counterweighted boom across the road, raised
parts = []
BX, BY = 15.05, 3.30
zb = ground_top(BX, BY)
parts.append(obox("pv", BX, BY, zb + 1.30, 0.34, 0.34, 2.60, mat=MGATE, cname=COLL))
piv = Vector((BX, BY, zb + 2.42))
tip = Vector((BX - 0.95, BY + 5.10, zb + 4.60))
parts.append(beam("bm", piv, tip, 0.16, 0.20, MGATE, COLL))
for k in range(4):
    t = 0.22 + k * 0.24
    p = piv.lerp(tip, t)
    parts.append(obox("st", p.x, p.y, p.z, 0.19, 0.30, 0.10, mat=MRED, cname=COLL))
cw = piv + (piv - tip) * 0.30
parts.append(beam("cb", piv, cw, 0.14, 0.16, MGATE, COLL))
parts.append(obox("cw", cw.x, cw.y, cw.z, 0.44, 0.44, 0.40, mat=MIRON, cname=COLL))
BARRIER = register(join_meshes(parts, "gate_barrier", COLL), pad=0.25)
log("BUILD", "gate_gatehouse / gate_barrier",
    "stone ground floor + jettied painted upper storey with the toll hatch onto "
    "the road; boom raised and counterweighted, pivot at (%.1f, %.1f)" % (BX, BY))

# =========================================================================
# 5. PORTERS' YARD
# =========================================================================
parts = []
# the porters' shed, back against the cliff, open to the yard
SX, SY = 6.85, 1.50
zb = ground_top(SX, SY)
parts.append(obox("sb", SX, SY, zb + 1.52, 5.40, 2.90, 3.04, mat=MWALL, cname=COLL))
for k in range(7):                                   # open front: posts only
    parts.append(obox("sp", SX - 2.70 + k * 5.40 / 6, SY + 1.52, zb + 1.52, 0.24, 0.24, 3.04, mat=MT, cname=COLL))
parts.append(obox("sl", SX, SY + 1.52, zb + 2.96, 5.60, 0.30, 0.26, mat=MT, cname=COLL))
for k in range(8):
    u = k / 7.0
    parts.append(obox("sr", SX, SY + 1.70 - u * 3.60, zb + 3.14 + u * 0.98, 5.80, 0.54, 0.10,
                      mat=MSHINGLE, cname=COLL))
SHED = list(parts)
parts = []


def clear(px, py, dz=0.7, pad=0.24):
    """Nothing the yard stands may reach into the yard PAD's walking corridor.

    `walk_lm_porters-yard` is a filled 8 x 8 m landmark disc (manifest 35), and
    the first pass tested only the mule-line POSTS: the rails between them and
    the water trough were placed unconditionally and put 14 samples of the yard's
    own pad under solid timber.  Every part goes through here now."""
    if not T.has_ground(px, py):
        return False
    return not over_walk(COR, px, py, ground_top(px, py) + dz, pad=pad, h=CORRIDOR_H + 0.4)


# mule lines along the cliff apron, east of the shed — never on the pad
for (bx, by, n, ang) in ((10.95, 9.85, 4, 0.12), (17.85, 9.55, 3, 0.10)):
    pts = []
    for k in range(n):
        px, py = bx + math.cos(ang) * k * 1.20, by + math.sin(ang) * k * 1.20
        if not clear(px, py):
            continue
        z = ground_top(px, py)
        parts.append(obox("hp", px, py, z + 0.62, 0.18, 0.18, 1.30, mat=MT, cname=COLL))
        pts.append(Vector((px, py, z + 1.10)))
    for k in range(len(pts) - 1):
        m = (pts[k] + pts[k + 1]) / 2
        if clear(m.x, m.y, dz=1.1):
            parts.append(beam("hr", pts[k], pts[k + 1], 0.13, 0.11, MT, COLL))
if clear(10.75, 10.25, dz=0.5, pad=1.2):
    tz = ground_top(10.75, 10.25)
    parts.append(obox("tr", 10.75, 10.25, tz + 0.34, 2.10, 0.86, 0.68, mat=MT, cname=COLL))
    parts.append(obox("tw", 10.75, 10.25, tz + 0.60, 1.92, 0.70, 0.10, mat=MPOOL, cname=COLL))

# the tarpaulin lean-to where pallets wait out the rain
LX, LY = 2.75, 3.85
zb = ground_top(LX, LY)
if clear(LX, LY, dz=1.4, pad=2.4):
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(obox("lp", LX + sx * 2.10, LY + sy * 1.35, zb + 1.35 + (0.22 if sy > 0 else 0),
                              0.20, 0.20, 2.70 + (0.44 if sy > 0 else 0), mat=MT, cname=COLL))
    for k in range(7):
        u = k / 6.0
        parts.append(obox("lt", LX, LY - 1.40 + u * 2.80, zb + 2.62 + u * 0.42, 4.70, 0.50, 0.07,
                          mat=MCANVAS, cname=COLL))

# a two-wheeled mule cart, shafts down, waiting outside the yard's own disc
CX, CY = 19.75, 8.70
if clear(CX, CY, dz=1.0, pad=1.9):
    zb = ground_top(CX, CY)
    parts.append(obox("cb", CX, CY, zb + 1.02, 2.60, 1.55, 0.62, rz=0.5, mat=MT, cname=COLL))
    for k in range(7):
        parts.append(obox("cs", CX - 1.15 + k * 0.38, CY, zb + 1.42, 0.10, 1.60, 0.52, rz=0.5,
                          mat=MT, cname=COLL))
    for sy in (-1, 1):
        c = Vector((CX + math.sin(0.5) * sy * 0.86, CY - math.cos(0.5) * sy * 0.86, zb + 0.78))
        parts.append(cyl("cw", c - Vector((math.cos(0.5) * 0.08, math.sin(0.5) * 0.08, 0)),
                         c + Vector((math.cos(0.5) * 0.08, math.sin(0.5) * 0.08, 0)),
                         0.78, 14, MT, COLL))
    for sy in (-1, 1):
        parts.append(beam("sh", (CX + 1.20 + sy * 0.05, CY + sy * 0.55, zb + 0.92),
                          (CX + 3.10, CY + sy * 0.62, zb + 0.16), 0.09, 0.09, MT, COLL))
YARD = register(join_meshes(SHED + parts, "gate_yard", COLL), pad=0.30)
log("BUILD", "gate_yard", "porters' shed against the cliff, two mule lines with "
    "trough, tarpaulin lean-to, and a cart with its shafts down — all outside the "
    "yard pad's own walking disc")

# =========================================================================
# 6. CARGO WINCH HEAD
# =========================================================================
# The Waterfront already carries its hoist rope up to the head; read the exact
# terminus off `cargo_winch_foot` rather than assuming it, and hang the sheave
# just clear of it.  That object is ACCEPTED ART — it is never touched.
foot = bpy.data.objects.get("cargo_winch_foot")
ROPE_TOP = Vector((28.70, 10.04, 25.03))
if foot:
    P = [foot.matrix_world @ v.co for v in foot.data.vertices]
    hi = max(P, key=lambda p: p.z)
    ROPE_TOP = Vector((sum(p.x for p in P if p.z > hi.z - 0.25) / max(1, len([p for p in P if p.z > hi.z - 0.25])),
                       sum(p.y for p in P if p.z > hi.z - 0.25) / max(1, len([p for p in P if p.z > hi.z - 0.25])),
                       hi.z))
WX, WY = 27.30, 5.05               # the machine stands SOUTH of its own pad
parts = []
zb = ground_top(WX, WY)
SHEAVE = Vector((ROPE_TOP.x, ROPE_TOP.y, ROPE_TOP.z + 0.42))
# `walk_pad_winch-head` (x 26.03..28.63, y 6.7..9.3) is where the player STANDS to
# work the winch, so the machine may not stand on it and nothing may hang in its
# 2 m corridor.  The first pass put the drum in the middle of the pad: 32 blocked
# down-ray samples and 36 headroom samples, the largest single failure of the
# build.  So the derrick is a mast pair south of the pad with the boom carried
# OVER the corridor at 27.4 m and the sheave block hung outside it.
MASTZ = zb + 4.10
for sx in (-1, 1):
    parts.append(beam("mt", (WX + sx * 1.30, WY, zb - 0.25), (WX + sx * 1.30, WY, MASTZ), 0.30, 0.30, MT, COLL))
    parts.append(beam("st", (WX + sx * 1.30, WY, MASTZ - 0.60), (WX + sx * 2.55, WY - 1.30, zb - 0.10),
                      0.18, 0.20, MT, COLL))
parts.append(beam("hd", (WX - 1.45, WY, MASTZ), (WX + 1.45, WY, MASTZ), 0.30, 0.34, MT, COLL))
parts.append(beam("br", (WX - 1.30, WY, MASTZ - 1.05), (WX + 1.30, WY, MASTZ - 0.10), 0.16, 0.18, MT, COLL))
BOOMT = Vector((SHEAVE.x, SHEAVE.y + 0.30, SHEAVE.z + 1.55))
for sx in (-1, 1):
    parts.append(beam("bm", (WX + sx * 1.30, WY, MASTZ - 0.16), (BOOMT.x + sx * 0.22, BOOMT.y, BOOMT.z),
                      0.22, 0.26, MT, COLL))
parts.append(beam("bt", (BOOMT.x - 0.22, BOOMT.y, BOOMT.z), (BOOMT.x + 0.22, BOOMT.y, BOOMT.z), 0.20, 0.22, MT, COLL))
# hanging block, on a stirrup, outside the pad's corridor
parts.append(cyl("hb", (SHEAVE.x - 0.13, SHEAVE.y, SHEAVE.z), (SHEAVE.x + 0.13, SHEAVE.y, SHEAVE.z),
                 0.32, 14, MIRON, COLL))
for sx in (-1, 1):
    parts.append(beam("sr", (SHEAVE.x + sx * 0.16, SHEAVE.y, SHEAVE.z), (BOOMT.x + sx * 0.16, BOOMT.y, BOOMT.z - 0.08),
                      0.05, 0.05, MIRON, COLL))
# the drum, its gearing and the crank the porters turn — at the mast feet
DRUM = Vector((WX, WY - 0.55, zb + 0.95))
parts.append(cyl("dr", DRUM - Vector((1.05, 0, 0)), DRUM + Vector((1.05, 0, 0)), 0.48, 16, MT, COLL))
for sx in (-1, 1):
    parts.append(cyl("df", DRUM + Vector((sx * 1.06, 0, 0)), DRUM + Vector((sx * 1.14, 0, 0)), 0.60, 16, MIRON, COLL))
parts.append(cyl("gw", DRUM + Vector((1.18, 0, 0)), DRUM + Vector((1.30, 0, 0)), 0.86, 20, MIRON, COLL))
for k in range(16):
    a = 2 * math.pi * k / 16
    parts.append(obox("gt", DRUM.x + 1.24, DRUM.y + math.cos(a) * 0.92, DRUM.z + math.sin(a) * 0.92,
                      0.10, 0.13, 0.13, mat=MIRON, cname=COLL))
parts.append(beam("cr", (DRUM.x + 1.38, DRUM.y, DRUM.z), (DRUM.x + 1.38, DRUM.y - 0.62, DRUM.z), 0.09, 0.09, MIRON, COLL))
parts.append(beam("ch", (DRUM.x + 1.38, DRUM.y - 0.62, DRUM.z), (DRUM.x + 1.84, DRUM.y - 0.62, DRUM.z), 0.07, 0.07, MT, COLL))
parts.append(beam("pw", (DRUM.x - 1.28, DRUM.y - 0.55, DRUM.z + 0.72), (DRUM.x - 1.28, DRUM.y + 0.10, DRUM.z + 0.28),
                  0.09, 0.13, MIRON, COLL))
parts.append(obox("bd", WX, WY - 0.55, zb - 0.06, 3.30, 1.80, 0.30, mat=MT, cname=COLL))
# a pallet hanging in the sling, just under the lip: it explains the machine
SL = Vector((SHEAVE.x, SHEAVE.y + 0.05, SHEAVE.z - 3.30))
parts.append(obox("pa", SL.x, SL.y, SL.z, 1.30, 1.10, 0.16, mat=MT, cname=COLL))
for k in range(3):
    parts.append(obox("pc", SL.x - 0.32 + (k % 2) * 0.62, SL.y - 0.20 + (k // 2) * 0.46,
                      SL.z + 0.44, 0.60, 0.58, 0.62, rz=0.2 * k, mat=MWALLD, cname=COLL))
for sx in (-1, 1):
    for sy in (-1, 1):
        parts.append(cyl("sr", (SL.x + sx * 0.58, SL.y + sy * 0.48, SL.z + 0.02),
                         (SHEAVE.x, SHEAVE.y, SHEAVE.z - 0.28), 0.026, 5, MROPE, COLL))
WINCH = register(join_meshes(parts, "gate_winch", COLL), pad=0.30)

# the hauling rope: drum -> sheave, and a second, slack line running down toward
# the quay's winch FOOT.  Explicitly a NEW object; the Waterfront's own rope and
# machine are untouched.
rp = []
rp.append(cyl("r0", (DRUM.x - 0.20, DRUM.y, DRUM.z + 0.48), (BOOMT.x, BOOMT.y, BOOMT.z - 0.14), 0.045, 6, MROPE, COLL))
rp.append(cyl("r0b", (BOOMT.x, BOOMT.y, BOOMT.z - 0.14), (SHEAVE.x, SHEAVE.y, SHEAVE.z + 0.28), 0.045, 6, MROPE, COLL))
FOOTP = Vector((30.00, 23.60, 2.20))
prev = Vector((SHEAVE.x + 0.30, SHEAVE.y + 0.24, SHEAVE.z - 0.10))
N = 9
for k in range(1, N + 1):
    t = k / N
    p = prev.lerp(FOOTP, 0) if False else Vector((
        SHEAVE.x + 0.30 + (FOOTP.x - SHEAVE.x - 0.30) * t,
        SHEAVE.y + 0.24 + (FOOTP.y - SHEAVE.y - 0.24) * t,
        (SHEAVE.z - 0.10) + (FOOTP.z - SHEAVE.z + 0.10) * t - 1.35 * math.sin(math.pi * t)))
    rp.append(cyl("r%d" % k, prev, p, 0.038, 5, MROPE, COLL))
    prev = p
ROPEOBJ = join_meshes(rp, "gate_winch_rope", COLL)
log("BUILD", "gate_winch / gate_winch_rope",
    "mast pair + drum, gearing and pawl SOUTH of the pad at (%.1f, %.1f); boom "
    "Waterfront's OWN rope terminus (%.2f, %.2f, %.2f) read off cargo_winch_foot, "
    "carried over the pad corridor, sheave block hung %.2f m clear of it; new slack line to the quay"
    % (WX, WY, ROPE_TOP.x, ROPE_TOP.y, ROPE_TOP.z, SHEAVE.z - 0.34 - ROPE_TOP.z))

# =========================================================================
# 7. PARAPET along the rim — placed by SEARCH (manifest 76)
# =========================================================================
parts, posts = [], []
x = 2.10
last = None
while x < 29.4:
    yr = T.rim(x)
    # walk outward from the lip until the walk corridor lets go
    y = yr - 0.55
    z = ground_top(x, y)
    tries = 0
    while over_walk(COR, x, y, z + 0.55, pad=0.24) and tries < 26:
        y += 0.12
        z = ground_top(x, y)
        tries += 1
    if tries >= 26 or not T.has_ground(x, y):
        x += 0.95
        last = None
        continue
    # the winch needs an open lip: cargo goes over the edge there
    if 25.9 < x < 29.2:
        x += 0.95
        last = None
        continue
    p = Vector((x, y, z))
    posts.append(p)
    parts.append(obox("pp", x, y, z + 0.52, 0.19, 0.19, 1.16, mat=MT, cname=COLL))
    parts.append(obox("pc", x, y, z + 1.13, 0.27, 0.27, 0.09, mat=MT, cname=COLL))
    if last is not None and (p - last).length < 2.4:
        for zr, sag in ((1.00, 0.10), (0.58, 0.06)):
            mid = (last + p) / 2 + Vector((0, 0, zr - sag))
            parts.append(cyl("hl", last + Vector((0, 0, zr)), mid, 0.028, 5, MROPE, COLL))
            parts.append(cyl("hl", mid, p + Vector((0, 0, zr)), 0.028, 5, MROPE, COLL))
        # a low drystone kerb between the posts stops the eye at the drop
        c = (last + p) / 2
        parts.append(obox("kb", c.x, c.y, c.z + 0.20, (p - last).length + 0.24, 0.40, 0.44,
                          rz=math.atan2(p.y - last.y, p.x - last.x), mat=MSTONE, cname=COLL))
    last = p
    x += 0.95
PARAPET = join_meshes(parts, "gate_parapet", COLL)
log("BUILD", "gate_parapet", "%d posts found by walking outward from the lip until "
    "the walk corridor released, rope handline + drystone kerb between them; the "
    "winch lip x 25.9..29.2 is deliberately left open for cargo" % len(posts))

# =========================================================================
# 8. BUNTING — the town's motif, met at the door
# =========================================================================
parts = []
# Heights are ABSOLUTE, and the sag is per run: a 1.55 m sag on an 8 m span put
# the low point of the eastern run at z=25.3 over a road at 24.06 — 1.2 m of
# headroom where the master's gate wants 2.0.  Every segment is Corridor-tested
# as a backstop.
RUNS = [((GX - 0.20, YN + 0.35), (13.40, 3.55), 27.02, 27.32, 0.45),
        ((GX - 0.20, YS - 0.35), (13.90, 2.20), 26.72, 27.12, 0.40),
        ((10.55, 3.30), (5.20, 6.35), 27.05, 27.60, 0.60),
        ((GX + 0.25, 4.90), (25.10, 9.70), 26.80, 27.45, 0.75)]
for (a, b, za, zb2, sag) in RUNS:
    A = Vector((a[0], a[1], za))
    B = Vector((b[0], b[1], zb2))
    n = 16
    prev = None
    for k in range(n + 1):
        t = k / n
        p = A.lerp(B, t) - Vector((0, 0, sag * math.sin(math.pi * t)))
        if prev is not None:
            c = (prev + p) / 2
            if not over_walk(COR, c.x, c.y, c.z, pad=0.1):
                parts.append(cyl("bl", prev, p, 0.020, 5, MROPE, COLL))
                if k % 2 == 0 and not over_walk(COR, c.x, c.y, c.z - 0.46, pad=0.1):
                    parts.append(obox("fl", c.x, c.y, c.z - 0.24, 0.05, 0.34, 0.42,
                                      rz=rng.random() * 0.5, mat=MFLAG[k % 4], cname=COLL))
        prev = p
# masts for the two runs that have no building to tie to
for (mx, my) in ((5.20, 6.35), (25.10, 9.70)):
    z = ground_top(mx, my)
    if over_walk(COR, mx, my, z + 1.5, pad=0.24) or in_solid(mx, my):
        continue
    parts.append(obox("bm", mx, my, z + 2.15, 0.22, 0.22, 4.50, mat=MT, cname=COLL))
    parts.append(obox("bk", mx, my, z + 4.46, 0.36, 0.36, 0.14, mat=MT, cname=COLL))
BUNT = register(join_meshes(parts, "gate_bunting", COLL), pad=0.0)
log("BUILD", "gate_bunting", "%d runs — arch to gatehouse, arch to the yard, and "
    "one carried east over the gallery; every pennant Corridor-tested" % len(RUNS))

# =========================================================================
# 9. LANTERNS — ordinary, warm.  (Heartlights do not exist in Dellhollow.)
# =========================================================================
LANTS = []


def lantern(name, x, y, z):
    parts = [obox("gl", x, y, z, 0.155, 0.155, 0.26, mat=MGLASS, cname=COLL),
             obox("cp", x, y, z + 0.17, 0.21, 0.21, 0.055, mat=MIRON, cname=COLL),
             obox("bs", x, y, z - 0.16, 0.19, 0.19, 0.04, mat=MIRON, cname=COLL)]
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        parts.append(obox("cg", x + sx * 0.072, y + sy * 0.072, z, 0.024, 0.024, 0.34,
                          mat=MIRON, cname=COLL))
    ob = join_meshes(parts, name, COLL)
    li = bpy.data.lights.new(name.replace("gate_", "KEYG_") + "_light", 'POINT')
    li.energy = 680.0
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
# the two on the arch piers are the ones the player sees first
for yy in (YS - PIER / 2 - 0.35, YN + PIER / 2 + 0.35):
    brackets.append(beam("br", (GX + 0.62, yy, TOPZ - 2.05), (GX + 1.24, yy, TOPZ - 1.95), 0.06, 0.06, MIRON, COLL))
    lantern("gate_lantern_arch_%d" % len(LANTS), GX + 1.24, yy, TOPZ - 2.22)
# the toll window, the yard, the barrier and the winch
for i, (lx, ly, lz, bx, by) in enumerate((
        (HX + 1.55, HY + BD / 2 + 0.42, ground_top(HX, HY) + 2.90, HX + 1.55, HY + BD / 2 + 0.02),
        (6.85, 3.45, ground_top(6.85, 1.50) + 2.86, 6.85, 3.28),
        (2.75, 5.60, ground_top(2.75, 3.85) + 2.80, 2.75, 5.42),
        (BX, BY - 0.26, ground_top(BX, BY) + 2.44, BX, BY),
        (WX - 1.30, WY - 1.05, ground_top(WX, WY) + 2.90, WX - 1.30, WY - 0.30))):
    if over_walk(COR, lx, ly, lz - 0.30, pad=0.14):
        continue
    brackets.append(beam("br", (bx, by, lz + 0.46), (lx, ly, lz + 0.34), 0.055, 0.055, MIRON, COLL))
    lantern("gate_lantern_%d" % len(LANTS), lx, ly, lz)
join_meshes(brackets, "gate_lantern_brackets", COLL)
log("BUILD", "gate_lantern_* x%d" % len(LANTS),
    "warm 680 W practicals with a 14 m cutoff — the town standard; two on the arch "
    "piers, one at the toll hatch, two in the yard, one on the barrier, one at the winch")

# =========================================================================
# 10. VEGETATION
# =========================================================================
VEGN = 0


def clone(src_name, tag, n, xr, yr, lo, hi, mode="ground", zjit=0.0):
    global VEGN
    src = bpy.data.objects.get(src_name)
    if src is None:
        return 0
    made = 0
    for i in range(n):
        px = xr[0] + rng.random() * (xr[1] - xr[0])
        if mode == "rim":
            py = T.rim(px) - 0.15 - rng.random() * 1.25
        elif mode == "face":
            py = T.rim(px) + 0.25 + rng.random() * 0.75
        else:
            py = yr[0] + rng.random() * (yr[1] - yr[0])
        if not T.has_ground(px, py):
            continue
        pz = ground_top(px, py)
        if pz < 12.0:
            continue
        s = lo + rng.random() * (hi - lo)
        if over_walk(KEEP, px, py, pz + 0.45, pad=0.35 * s) or in_solid(px, py):
            continue
        r = road_at(px, py)
        if r is not None and r[1] < ROAD_W + 0.55:
            continue
        ob = src.copy()
        ob.data = src.data.copy()
        ob.name = "gate_%s_%d" % (tag, i)
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


nt = clone("rimtree_0", "rimtree", 10, (1.25, 4.60), (0.1, 2.6), 0.80, 1.20)
nt += clone("rimtree_1", "rimtree", 10, (1.25, 4.40), (8.6, 12.2), 0.56, 0.84)
nt += clone("rimtree_0", "rimtreeE", 4, (13.40, 15.60), (8.2, 10.2), 0.40, 0.58)
nk = clone("rimclump_3", "rimclump", 30, (1.30, 26.0), None, 0.7, 1.35, mode="rim")
nk += clone("rimclump_7", "rimclump", 16, (1.20, 4.70), (0.1, 5.2), 0.6, 1.1)
ng = clone("seam_tuft_0", "tuft", 110, (1.30, 29.2), None, 0.8, 1.8, mode="rim")
ng += clone("seam_tuft_3", "tuft", 70, (1.20, 29.4), (0.0, 4.2), 0.8, 1.7)
nf = clone("seam_tuft_1", "fern", 46, (1.20, 29.4), (0.0, 4.4), 0.8, 1.5)
nf += clone("seam_tuft_37", "fern", 26, (13.4, 26.0), (6.2, 10.4), 0.8, 1.4)
nc = clone("creeper_4", "creeper", 34, (1.60, 18.6), None, 0.7, 1.3, mode="face", zjit=-1.4)
# a crown on the upper rim: "autumn trees crowning both rims" is the style note
crest = []
for i in range(22):
    px = GX0 + 0.8 + rng.random() * (GX1 - GX0 - 1.6)
    src = bpy.data.objects.get("rimclump_%d" % rng.randint(1, 12))
    if src is None:
        continue
    ob = src.copy(); ob.data = src.data.copy()
    ob.name = "gate_rimclump_crest_%d" % i; ob.data.name = ob.name
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
log("BUILD", "gate_rimclump_crest_* x%d" % len(crest),
    "autumn crowns seated ON the new crest, half-buried in it (manifest 71/78)")
log("BUILD", "gate_rimtree/rimclump/tuft/fern/creeper",
    "%d autumn crowns, %d clumps, %d tufts, %d ferns, %d creepers over the lip — "
    "everything Corridor- and carriageway-tested" % (nt, nk, ng, nf, nc))

# =========================================================================
# 11. CLUTTER — the working life of a gate
# =========================================================================
parts = []
placed = 0
ZONES = [
    # (x0, x1, y0, y1, n, kinds)
    (4.30, 10.10, 3.05, 5.50, 34, "yard"),       # the shed's apron, onto the yard
    (1.20, 4.70, 0.20, 5.30, 14, "yard"),        # the bluff notch under the lean-to
    (5.40, 12.60, 10.10, 12.35, 16, "yard"),     # the yard's gorge shoulder
    (13.30, 15.60, 0.30, 2.20, 8, "toll"),       # between the barrier and the arch
    (13.40, 15.65, 6.60, 10.50, 10, "toll"),     # inside the palisade
    (18.60, 26.00, 6.20, 9.70, 30, "road"),      # the gallery shoulder
    (23.90, 25.85, 4.40, 9.40, 10, "winch"),     # the winch's staging, west of the pad
    (28.85, 29.50, 4.00, 9.40, 6, "winch"),      # ... and east of it
]
for (x0, x1, y0, y1, n, kind) in ZONES:
    for i in range(n * 4):
        if placed >= sum(z[4] for z in ZONES):
            break
        px = x0 + rng.random() * (x1 - x0)
        py = y0 + rng.random() * (y1 - y0)
        if not T.has_ground(px, py):
            continue
        pz = ground_top(px, py)
        # a joined multi-part mesh is audited by its BBOX corners (finding 96), so
        # one piece cantilevered over the lip makes the whole `gate_clutter` object
        # a stray.  Every piece has to have ground under its whole FOOTPRINT.
        if pz < 23.30:
            continue
        if any(not T.has_ground(px + dx, py + dy) or abs(ground_top(px + dx, py + dy) - pz) > 0.85
               for dx, dy in ((0.45, 0), (-0.45, 0), (0, 0.45), (0, -0.45))):
            continue
        if over_walk(KEEP, px, py, pz + 0.7, pad=0.55) or in_solid(px, py):
            continue
        r = road_at(px, py)
        if r is not None and r[1] < ROAD_W + 0.42:
            continue
        k = rng.random()
        rz = rng.random() * 3.14
        if k < 0.30:
            parts.append(obox("cr", px, py, pz + 0.38, 0.78, 0.72, 0.76, rz=rz, mat=MWALLD, cname=COLL))
            for e in range(2):
                parts.append(obox("cb", px, py, pz + 0.16 + e * 0.44, 0.82, 0.76, 0.07, rz=rz, mat=MT, cname=COLL))
            if rng.random() < 0.45:
                parts.append(obox("cr", px + 0.12, py - 0.08, pz + 1.06, 0.66, 0.62, 0.60,
                                  rz=rz + 0.4, mat=MWALL, cname=COLL))
        elif k < 0.52:
            parts.append(cyl("br", (px, py, pz), (px, py, pz + 0.88), 0.33, 12, MWALLD, COLL, r2=0.30))
            for e in (0.16, 0.44, 0.72):
                parts.append(cyl("bh", (px, py, pz + e), (px, py, pz + e + 0.055), 0.345, 12, MIRON, COLL))
        elif k < 0.70:
            for e in range(rng.randint(2, 4)):
                parts.append(obox("sk", px + rng.uniform(-.22, .22), py + rng.uniform(-.22, .22),
                                  pz + 0.20 + e * 0.32, 0.72, 0.50, 0.34,
                                  rz=rz + e * 0.5, mat=MSACK, cname=COLL))
        elif k < 0.84:
            parts.append(obox("pl", px, py, pz + 0.09, 1.32, 1.06, 0.14, rz=rz, mat=MT, cname=COLL))
            for e in range(rng.randint(2, 5)):
                parts.append(cyl("pk", (px + rng.uniform(-.36, .36), py + rng.uniform(-.30, .30), pz + 0.16),
                                 (px + rng.uniform(-.36, .36), py + rng.uniform(-.30, .30), pz + 0.52),
                                 0.24, 10, MPUMPKIN, COLL))
        else:
            for e in range(4):
                parts.append(cyl("rc", (px, py, pz + 0.03 + e * 0.055), (px, py, pz + 0.06 + e * 0.055),
                                 0.30 - e * 0.045, 12, MROPE, COLL))
        placed += 1
CLUTTER = join_meshes(parts, "gate_clutter", COLL)
log("BUILD", "gate_clutter", "%d crate stacks / barrels / sack piles / pumpkin "
    "pallets / rope coils, every one clear of the walking lines and the carriageway"
    % placed)

# =========================================================================
# corbels under the eastern gallery — it must read as BUILT from below
# =========================================================================
parts = []
x = 19.20
while x < 29.4:
    yr = T.rim(x)
    if T.has_ground(x, yr - 0.30) and ground_top(x, yr - 0.30) > 23.0 and not in_solid(x, yr - 1.0):
        zt = ground_top(x, yr - 0.30)
        parts.append(beam("cb", (x, yr - 0.05, zt - 0.42), (x, yr - 1.95, zt - 2.35), 0.24, 0.30, MT, COLL))
        parts.append(obox("cp", x, yr - 0.55, zt - 0.52, 0.30, 1.30, 0.22, mat=MT, cname=COLL))
    ylo = T.ylo(x)
    if T.has_ground(x, ylo + 0.30) and ground_top(x, ylo + 0.30) > 23.0 and not in_solid(x, ylo + 1.0):
        zt = ground_top(x, ylo + 0.30)
        parts.append(beam("cb", (x, ylo + 0.05, zt - 0.42), (x, ylo + 1.85, zt - 2.20), 0.22, 0.28, MT, COLL))
    x += 1.55
CORB = join_meshes(parts, "gate_corbels", COLL)
log("BUILD", "gate_corbels", "raking struts under both lips of the eastern gallery "
    "plate, so a 0.4 m shelf over the Inn's roofs reads as carpentry, not as a slab")

# =========================================================================
print("\n" + "=" * 78)
print("GATE DISTRICT: %d objects in %s" % (len(bpy.data.collections[COLL].objects), COLL))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
