"""gate_build.py — the GATE APPROACH district (parcel `p-gate`).

!!! DO NOT RE-RUN AGAINST THE LIVE MASTER WITHOUT READING THIS (2026-07-30) !!!
This script's idempotent clear pass removes every gate_*/veg_gate_*/KEYG_* object
and rebuilds from scratch — which SILENTLY UNDOES the accepted legibility surgery
on veg_gate_rimclump_1/2/11/12 and veg_gate_rimtreeE_0 (per-leaf-card raises and
thins, commit 4ebeb92; spec in docs/qa/DAYLOG.md 2026-07-30). If a rebuild is ever
needed, run tools/ga_build.py AFTERWARDS — it restores the surgery from its
GA_SRC_* snapshots and recomputes. Related canon: a two-letter prefix is not
ownership — dry-run any clear pass against the live lamp/object inventory first.

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
import gate_lib
from gate_lib import (Terrain, over_walk, GX0, GX1, GY0, GY1, SHELF, PLATE_BOT,
                      BASEZ, SOLID_X, HIGH_Z, DECK_DROP, CORRIDOR_H,
                      SHOTS, HERO, HERO_EYES, NEAR_FRAC, NEAR_K,
                      hero_dist, near_field)

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
# The veneer behind the gate is the FIELD the gate is read against, and in v6 it
# was the same rock at the same value as the piers standing 4 m in front of it,
# so the arch had no silhouette from any western camera.  Figure/ground on a
# tier with a 20 m wall behind everything cannot come from the light rig — the
# card that lifts the arch's shadow side lifts the wall behind it by the same
# fraction.  It has to be built into the SURFACES: the backdrop is darkened and
# cooled a third, the dressed masonry stays warm and pale, and the arch reads.
MCLIFF = derive("mat_rock", "mat_gate_cliff", scale=1.05, tint=(0.34, 0.33, 0.36))


def cloth(name, rgb, back=1.55):
    """A pennant: diffuse front, translucent back, and a WEAVE.

    `mat_flag_*` from the kit is one flat diffuse colour mixed with one flat
    translucent colour.  At 20 m on a quay that is bunting; at 4 m from the lens
    of the town's front-door camera it is a coloured rectangle with no surface
    at all, which is what "raw kit quads" means.  Finding 95 one scale down: the
    gap the eye reads is a DETAIL gap.  So the colour is multiplied by a fine
    object-space noise (weave and sun-fade), and every value is pulled toward
    the painted-timber palette the rest of the town is made of.
    """
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.42
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Roughness"].default_value = 0.90
    tra = nt.nodes.new("ShaderNodeBsdfTranslucent")
    co = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")         # the weave
    nz.inputs["Scale"].default_value = 62.0
    nz.inputs["Detail"].default_value = 4.0
    nz2 = nt.nodes.new("ShaderNodeTexNoise")        # broad sun-fade / dirt
    nz2.inputs["Scale"].default_value = 5.5
    nz2.inputs["Detail"].default_value = 2.0
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'MULTIPLY_ADD'
    ad.inputs[1].default_value = 0.30
    ad.inputs[2].default_value = 0.56               # weave -> 0.56 .. 0.86
    ad2 = nt.nodes.new("ShaderNodeMath"); ad2.operation = 'MULTIPLY_ADD'
    ad2.inputs[1].default_value = 0.44
    ad2.inputs[2].default_value = 0.62              # fade  -> 0.62 .. 1.06
    ml = nt.nodes.new("ShaderNodeMath"); ml.operation = 'MULTIPLY'
    fr = nt.nodes.new("ShaderNodeMix"); fr.data_type = 'RGBA'; fr.blend_type = 'MULTIPLY'
    fr.inputs[0].default_value = 1.0
    fr.inputs[6].default_value = (*rgb, 1.0)
    bk = nt.nodes.new("ShaderNodeMix"); bk.data_type = 'RGBA'; bk.blend_type = 'MULTIPLY'
    bk.inputs[0].default_value = 1.0
    bk.inputs[6].default_value = (*[min(1.0, c * back) for c in rgb], 1.0)
    nt.links.new(co.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(co.outputs["Object"], nz2.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ad.inputs[0])
    nt.links.new(nz2.outputs["Fac"], ad2.inputs[0])
    nt.links.new(ad.outputs["Value"], ml.inputs[0])
    nt.links.new(ad2.outputs["Value"], ml.inputs[1])
    for mixn, sock in ((fr, dif.inputs["Color"]), (bk, tra.inputs["Color"])):
        nt.links.new(ml.outputs["Value"], mixn.inputs[7])
        nt.links.new(mixn.outputs[2], sock)
    nt.links.new(dif.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tra.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


# The kit's flag colours pulled ~35% toward their own luminance and re-seated on
# the painted-timber palette (`mat_paint_red`'s tint is 0.400/0.058/0.042,
# `mat_paint_blue`'s 0.070/0.195/0.330).  Six of them, not four, because the
# variation the eye wants at close range is VALUE variation, not more hues: two
# reds a stop apart, two blues, a weathered ochre and a bone-white, which is the
# same spread the Boatyard's bunting has.
MFLAG = [cloth("mat_gate_flag_red", (0.196, 0.064, 0.055)),
         cloth("mat_gate_flag_red2", (0.128, 0.050, 0.046)),
         cloth("mat_gate_flag_blue", (0.068, 0.123, 0.191)),
         cloth("mat_gate_flag_blue2", (0.047, 0.081, 0.128)),
         cloth("mat_gate_flag_ochre", (0.255, 0.175, 0.076)),
         cloth("mat_gate_flag_bone", (0.320, 0.295, 0.248))]


def lamplit(name, rgb=(1.0, 0.455, 0.135), lo=2.10, hi=3.40):
    """A window with someone behind it.

    The accepted Boatyard hero has exactly one of these and it is the thing the
    eye lands on.  Strength is 2-3.5, not the 90 a 12 cm lantern globe wants:
    at window scale AgX creams anything hotter and the pane lands as a clipped
    white rectangle with the hue burned out of it (boatyard `make_lockhouse_glass`).
    """
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1.0)
    co = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 21.0
    nz.inputs["Detail"].default_value = 3.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = lo
    mr.inputs["To Max"].default_value = hi
    nt.links.new(co.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], em.inputs["Strength"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


MWIN = lamplit("mat_gate_window")

# ------------------------------------------------------------- collection(s)
coll(COLL)

killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("gate_", "veg_gate_", "KEYG_")):
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
# The manifest ACCUMULATES.  This script is idempotent, so the second run on its
# own saved output finds nothing left to delete — and a naive rewrite would then
# publish an EMPTY deletions list, which is the one file the merge custodian
# obeys literally.  The shells would survive the merge standing inside the built
# art.  Re-running a build must never be able to un-record what the first run did.
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
log("DELETE", "%d lm_ shells (%d removed this run)" % (len(deleted), found),
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
    (2.90, 9.10, -0.25, 3.25),    # porters' shed
    (0.40, 5.10, 2.30, 5.45),      # tarpaulin lean-to
    (9.15, 14.00, -0.60, 4.90),    # gatehouse + chimney + pentice
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
# walk mesh out here — the map's walk graph stops at the `valley-road` pad — so
# the carriageway is carried on its own spine off the west edge of the parcel.
# THE SPINE AND ITS HEIGHT NOW LIVE IN gate_lib (2026-08-02, user redline #4):
# three tools lay geometry on it and it must not be edited in one of them alone.
ROAD_W = 1.42          # half-width added to a walk ribbon
GROUND_DROP = 0.36     # the carriageway slab's thickness


def road_at(x, y):
    """(top z, distance from the carriageway centre) or None."""
    z, d = walk_ref(x, y)
    if d < ROAD_W + 1.6:
        return z - DECK_DROP, d
    ds = gate_lib.spine_d(x, y)
    if ds < 2.55:
        return gate_lib.spine_top(x) - DECK_DROP, ds
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
    # THE SPINE IS A WALK SURFACE THE MAP DOES NOT CARRY, so it gets the walk
    # graph's own clamp (2026-08-02, user redline #4).  Without it `natural`'s
    # west-end bluff — 5.4 m of rock that used to be flattened, by luck, by the
    # Porters' Yard's 8 m walk disc — comes back up THROUGH the road the moment
    # that disc is deleted, and the last four metres of the entry road ramp 2.4 m
    # uphill on their way off the bottom of frame.
    ds = gate_lib.spine_d(x, y)
    if ds < 5.4:
        h = min(h, gate_lib.spine_top(x) - GROUND_DROP
                + max(0.0, ds - (ROAD_W + 0.50)) * 1.15)
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
CST = 0.42
# The veneer runs PAST the ground sheet's east end.  A sightline through the
# gate opening leaves at a very shallow angle to the cliff (roughly 1 in 4), so
# it crosses y=0.5 some 28 m downstream of the camera — past x=29.6, where in v6
# it found raw `cliff_town` again and put the blown white patch back in the one
# frame the whole exercise was for.  Where a veneer ENDS is set by the shallowest
# ray that can see behind it, not by where the ground it hides stops.  31.6 is
# the parcel's own eastern limit (p-gate is x 1.5..31.8).
CVX1 = 31.60
CX_N = int(round((CVX1 - GX0) / CST)) + 1
CZ0, CZ1 = 34.60, 0.0


def cliff_crest(x):
    # ABOVE cliff_town's own top edge (z=37.0) everywhere, or a band of the
    # blockout slab shows over the veneer's crest and the whole point is lost.
    return 40.20 + 1.50 * math.sin(x * 0.21 + 0.7) + 0.80 * math.sin(x * 0.63 - 1.9) \
        + 0.35 * math.sin(x * 1.47 + 3.1)


def cliff_front(x, z, zb):
    u = min(1.0, max(0.0, (z - zb) / max(cliff_crest(x) - zb, 1.0)))
    d = 0.10 + 0.86 * (1.0 - u) ** 1.05
    d += (math.sin(x * 0.83 + z * 0.55) * 0.40 + math.sin(x * 2.11 - z * 1.31) * 0.22
          + math.sin(x * 4.7 + z * 3.3) * 0.08) * 0.34
    # East of the winch the wall steps OUT into the gorge — a buttress that both
    # closes the shallow through-gate sightline and gives the tier's east end
    # something to end against.  It only exists above the gallery plate and it
    # stops 4 m short of the Item Shop's own footprint, which is at y 6.8..11.2.
    if x > 27.10:
        d += min(1.85, (x - 27.10) * 0.62) * min(1.0, max(0.0, (z - 24.60) / 2.0))
    if in_solid(x, 1.0) or in_solid(x, 0.4):
        d = min(d, 0.10)
    return max(0.04, d)


CV, CF = [], []
rows = []
for i in range(CX_N):
    x = GX0 + i * CST
    # The FOOT matters as much as the crest.  v6 seated it 1.6 m under the local
    # ground, which east of the promontory is a 0.40 m plate — so the veneer
    # stopped at z~22.4 and every ray that passed under the gallery found raw
    # `cliff_town` again (the pale wedge in `tollyard`, at 21.4..22.2 m up).
    # Floored at 19.0 it runs down past the Inn and Item-Shop roofs (23.55) into
    # ground that is never in shot, which costs 8 rows of quads and closes it.
    zb = min(ground_top(min(x, GX1), 0.55) - 1.60, 19.00)
    n = 30
    col = []
    for k in range(n + 1):
        z = zb + (cliff_crest(x) - zb) * (k / n) ** 0.92
        col.append((len(CV), z))
        CV.append((x, cliff_front(x, z, zb), z))
    for k in range(n + 1):
        z = col[k][1]
        CV.append((x, -0.60, z))
    rows.append((col, len(CV) - (n + 1)))
NN = 31
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
me.materials.append(MCLIFF)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
CLIFF = bpy.data.objects.new("gate_cliffface", me)
link(CLIFF, COLL)
log("BUILD", "gate_cliffface", "%d x %d veneer over cliff_town from x %.1f..%.1f (past "
    "the ground sheet, to close the shallow through-gate sightline), crest %.1f..%.1f m "
    "modulated (manifest 7), east buttress from x=27.1, pressed flat behind every "
    "building; mat_gate_cliff is a THIRD darker and cooler than the dressed masonry "
    "in front of it, which is where the arch's silhouette comes from"
    % (CX_N, NN, GX0, CVX1, min(cliff_crest(GX0 + i * CST) for i in range(CX_N)),
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
# roofs — one course builder, because a roof is not a stack of planks
# =========================================================================
def shingles(parts, cx, cy, eave_z, ridge_z, half_dep, width, mat=None,
             axis='y', courses=None, over=0.16, thick=0.075):
    """Lay overlapping shingle courses from the eaves up to the ridge.

    v1-v6 drew nine 0.42 m boards per pitch, which steps 0.21 m up and 0.30 m in
    per course: from any camera under the eaves that is a LUMBER STACK, and the
    gate tier has four of them crossing the top of its hero frame in one band.
    A shingled slope is many shallow courses with real overlap — here ~0.10 m of
    rise and 0.16 m of overlap per course — and it costs nothing but boxes.  The
    Boatyard's accepted roofs are the reference: you can count the tiles.
    """
    # The course count comes off the roof's DEPTH, not its height: what the eye
    # counts is the EXPOSURE, the strip of each course the one above leaves
    # showing.  At 0.21 m (what a height-driven count gave a shallow pitch) the
    # mossy shingle material paints one bright green stripe per course and the
    # roof reads as stacked boards again; at ~0.12 it reads as tiles.
    n = courses or max(8, int(round(half_dep / 0.12)))
    mat = mat if mat is not None else MSHINGLE
    # ... and each course is BROKEN ACROSS its length as well.  One 5 m box per
    # course is still a plank, just a shallower one: a shingle roof is small in
    # both directions, and it is the staggered vertical joints that say "tiles"
    # rather than "boards" from underneath.
    tiles = max(3, int(round(width / 0.70)))
    for k in range(n):
        u = k / float(n - 1)
        zz = eave_z + (ridge_z - eave_z) * u
        dep = half_dep * (1.0 - u)
        step = half_dep / float(n - 1)
        for s in (-1, 1):
            for t in range(tiles):
                stag = 0.5 if k % 2 else 0.0           # courses break on the half
                w = width / tiles
                off = (t + 0.5 + stag) * w - width / 2
                if abs(off) > width / 2:
                    continue
                jz = zz + (0.008 if (t + k) % 2 else -0.008)
                if axis == 'y':
                    parts.append(obox("rf", cx + off, cy + s * dep, jz, w * 0.94, step + over,
                                      thick, mat=mat, cname=COLL))
                else:
                    parts.append(obox("rf", cx + s * dep, cy + off, jz, step + over, w * 0.94,
                                      thick, mat=mat, cname=COLL))
    return parts


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
# A shingled cap over the beam keeps the rain off the joinery — and it is the
# thing that has to top the district.  The arch is the ONE object in a gate that
# has to be taller than the toll house beside it; in v6 the gatehouse ridge
# (28.80) and its chimney cap (29.39) matched the arch's 29.21, and the two of
# them plus the shed roof merged into one horizontal band of timber across the
# top of every arrival frame with nothing silhouetting against anything.  The
# cap is raised to a proper gablet on posts, the gatehouse is cut down (below),
# and the arch clears it by ~1.6 m.
CAPZ = TOPZ + 1.16
for sy in (-1, 1):
    for sx in (-1, 1):
        parts.append(obox("cp", GX + sx * 0.66, 4.00 + sy * 2.05, CAPZ - 0.42, 0.16, 0.16, 0.84,
                          mat=MGATE, cname=COLL))
shingles(parts, GX, 4.00, CAPZ, CAPZ + 0.92, 2.72, 2.10)
parts.append(beam("rg", (GX - 1.14, 4.00, CAPZ + 0.98), (GX + 1.14, 4.00, CAPZ + 0.98),
                  0.22, 0.18, MGATE, COLL))
for sy in (-1, 1):                        # barge boards, so the gablet has an edge
    parts.append(beam("bg", (GX, 4.00 + sy * 2.78, CAPZ - 0.04),
                      (GX, 4.00 + sy * 0.10, CAPZ + 0.96), 0.20, 0.14, MGATE, COLL))
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
# Body centre — cliff side, window onto the road.  v6 stood it at x=12.55, which
# is 1.2 m EAST of `walk_pad_gatehouse` (10.03..12.63, so centre 11.33) and 1.2 m
# nearer the arch than the map puts it.  From every western camera that 5.3 m
# lodge then stood shoulder to shoulder with a 1.9 m gate pier and won.  Seating
# it on its own pad is both truer to `dellhollow.map.json` and the separation the
# arrival frame needs — read the landmark's pad before placing the landmark
# (finding 93, the same lesson the winch taught, one axis over).
HX, HY = 11.55, 2.00
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
# The toll window: a shuttered hatch onto the road, with a sill shelf — and
# somebody behind it.  This is the only warm INTERIOR in the arrival frame and
# it does more work than any amount of lantern: the accepted Boatyard hero has
# exactly one lit pane and it is where the eye lands.  The lit glass sits just
# proud of the hatch board so the frame reads around it.
WY = HY + BD / 2
parts.append(obox("wh", HX + 0.55, WY + 0.02, zb + 1.70, 1.10, 0.16, 1.05, mat=MTD, cname=COLL))
parts.append(obox("wg", HX + 0.55, WY + 0.11, zb + 1.70, 0.92, 0.03, 0.86, mat=MWIN, cname=COLL))
for k in range(3):                                    # glazing bars over the pane
    parts.append(obox("wm", HX + 0.10 + k * 0.45, WY + 0.13, zb + 1.70, 0.05, 0.04, 0.88,
                      mat=MT, cname=COLL))
parts.append(obox("wm", HX + 0.55, WY + 0.13, zb + 1.70, 0.94, 0.04, 0.05, mat=MT, cname=COLL))
parts.append(obox("ws", HX + 0.55, WY + 0.24, zb + 1.14, 1.42, 0.52, 0.10, mat=MT, cname=COLL))
parts.append(obox("wu", HX + 0.55, WY + 0.36, zb + 2.42, 1.42, 0.60, 0.09, mat=MT, cname=COLL))
for sx in (-1, 1):
    parts.append(beam("wb", (HX + 0.55 + sx * 0.62, WY + 0.06, zb + 1.34),
                      (HX + 0.55 + sx * 0.62, WY + 0.60, zb + 2.40), 0.07, 0.07, MT, COLL))
# a door and two upper windows
parts.append(obox("dr", HX - 1.35, WY + 0.02, zb + 1.10, 1.02, 0.14, 2.10, mat=MGATE, cname=COLL))
parts.append(obox("uw", HX - 1.30, WY - 0.02, zb + 3.30, 0.80, 0.10, 0.60, mat=MTD, cname=COLL))
# a small pentice over the toll hatch: shelter for whoever is being charged
for k in range(7):
    u = k / 6.0
    parts.append(obox("pt", HX + 0.55, WY + 0.16 + u * 0.88, zb + 3.00 - u * 0.30, 2.00, 0.22, 0.055,
                      mat=MSHINGLE, cname=COLL))
for sx in (-1, 1):
    parts.append(beam("pb", (HX + 0.55 + sx * 0.86, WY + 0.06, zb + 2.55),
                      (HX + 0.55 + sx * 0.86, WY + 0.96, zb + 2.80), 0.08, 0.10, MT, COLL))
# Roof: mossy shingle, gable to the road — and DELIBERATELY subordinate.  A toll
# lodge that matches the arch it guards flattens the district's skyline into one
# band (see the arch's gablet above); the ridge comes down 0.72 m and the
# chimney 0.90 m so the arch is unambiguously the tallest thing on the tier.
EAVE = zb + 2.86
RIDGE = EAVE + 1.32
shingles(parts, HX, HY, EAVE, RIDGE, (BD + 1.22) / 2, BW + 0.86)
parts.append(beam("rg", (HX - (BW + 0.86) / 2, HY, RIDGE + 0.06),
                  (HX + (BW + 0.86) / 2, HY, RIDGE + 0.06), 0.24, 0.20, MT, COLL))
# chimney, on the CLIFF side of the ridge so it never stands against the sky in
# the arrival frame
parts.append(obox("ch", HX - 1.75, HY - 1.15, zb + 3.05, 0.78, 0.78, 2.80, mat=MSTONE, cname=COLL))
parts.append(obox("cc", HX - 1.75, HY - 1.15, zb + 4.52, 0.98, 0.98, 0.18, mat=MSTONE, cname=COLL))
# the toll board
parts.append(obox("tb", HX + 2.28, WY - 0.30, zb + 1.85, 0.05, 0.80, 0.98, mat=MTD, cname=COLL))
GATEHOUSE = register(join_meshes(parts, "gate_gatehouse", COLL), pad=0.45)

# the barrier: a counterweighted boom across the road, raised
parts = []
BX, BY = 15.05, 3.30
zb = ground_top(BX, BY)
parts.append(obox("pv", BX, BY, zb + 1.30, 0.34, 0.34, 2.60, mat=MGATE, cname=COLL))
piv = Vector((BX, BY, zb + 2.42))
# A raised boom stands UP, not out.  At the v6 angle (~23 deg above horizontal,
# 5.1 m of reach across the road) it was a 5 m diagonal raking straight across
# the gate opening in every western frame — the single strongest line in the
# composition, pointing at nothing.  Steepened to ~66 deg it reads as what it is,
# a barrier that has been lifted, and it leaves the arch's silhouette alone.
tip = Vector((BX - 0.38, BY + 1.75, zb + 4.85))
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
# Seating the toll house on its own pad moved it 1.0 m west, into the porters'
# shed's eave: the audit named the pair (gate_yard IN gate_gatehouse, 0.23 m).
# The shed slides the same distance rather than the lodge sliding back off its
# pad — the shed is the piece with no map position to be true to.
SX, SY = 6.05, 1.50
zb = ground_top(SX, SY)
parts.append(obox("sb", SX, SY, zb + 1.52, 5.40, 2.90, 3.04, mat=MWALL, cname=COLL))
for k in range(7):                                   # open front: posts only
    parts.append(obox("sp", SX - 2.70 + k * 5.40 / 6, SY + 1.52, zb + 1.52, 0.24, 0.24, 3.04, mat=MT, cname=COLL))
parts.append(obox("sl", SX, SY + 1.52, zb + 2.96, 5.60, 0.30, 0.26, mat=MT, cname=COLL))
for k in range(15):                      # a lean-to pitch, laid in real courses
    u = k / 14.0
    parts.append(obox("sr", SX, SY + 1.70 - u * 3.60, zb + 3.10 + u * 0.98, 5.80, 0.40, 0.06,
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
RUNS = [((GX - 0.20, YN + 0.35), (12.55, 3.60), 27.02, 27.24, 0.45),
        ((GX - 0.20, YS - 0.35), (12.95, 2.20), 26.72, 27.04, 0.40),
        ((9.60, 3.30), (5.20, 6.35), 26.98, 27.60, 0.60),
        ((GX + 0.25, 4.90), (25.10, 9.70), 26.80, 27.45, 0.75)]


def pennant(parts, c, run, drop, mat, phase):
    """One triangular pennant, hanging with a droop and a curl.

    A flat 0.05 x 0.34 x 0.42 box is a rectangle whether the camera is 20 m away
    or 3 m, and at 3 m it is unmistakably a kit quad.  Real bunting has a stiff
    top edge on the line, a taper to the point, a sag in the free corner and a
    curl where the cloth has rolled — four rows of vertices, no thickness, and
    the translucent side of `cloth()` does the rest.  The curl is per-pennant,
    signed by its phase, so a run never reads as N copies of one shape.
    """
    ax = Vector((run.x, run.y, 0)).normalized()
    side = Vector((-ax.y, ax.x, 0))                        # the cloth's own left
    top_w = 0.35 + 0.07 * math.sin(phase * 2.7)
    curl = 0.16 * math.sin(phase * 1.9) + 0.07 * math.sin(phase * 5.1)
    lean = 0.10 * math.sin(phase * 3.3)
    rows = 4
    V, F = [], []
    for r in range(rows + 1):
        u = r / float(rows)
        w = top_w * (1.0 - 0.78 * u)                        # taper to the point
        # the cloth hangs, twists off the vertical, and rolls one edge under
        off = side * (curl * math.sin(u * 2.4) + lean * u) + ax * (0.05 * u * u)
        z = -drop * (u + 0.10 * u * (1.0 - u))
        base = c + off + Vector((0, 0, z))
        V.append(base - side * (w / 2) * (1.0 - 0.35 * u))
        V.append(base + side * (w / 2) * (1.0 + 0.15 * u))
    for r in range(rows):
        i = r * 2
        F.append((i, i + 1, i + 3, i + 2))
    parts.append(new_mesh("fl", V, F, mat, COLL))
    return parts


nflag, nthin = 0, 0
for ri, (a, b, za, zb2, sag) in enumerate(RUNS):
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
                # Density is a function of DISTANCE TO THE LENS, not of the run.
                # Every second segment is right at 20 m and a picket fence at 3;
                # the near field gets a third of that, which reads as the same
                # bunting seen closer instead of as a wall of coloured paper.
                nf = near_field(c.x, c.y, c.z - 0.30, 0.45)
                step = 2 if nf > 0.62 else (3 if nf > 0.25 else 5)
                if k % step == 0 and not over_walk(COR, c.x, c.y, c.z - 0.46, pad=0.1):
                    if nf <= 0.02:
                        nthin += 1
                    else:
                        pennant(parts, c, p - prev, 0.34 + 0.10 * rng.random(),
                                MFLAG[(k + ri * 3) % len(MFLAG)], k * 1.31 + ri * 0.7)
                        nflag += 1
                elif k % step == 0:
                    nthin += 1
        prev = p
# masts for the two runs that have no building to tie to
for (mx, my) in ((5.20, 6.35), (25.10, 9.70)):
    z = ground_top(mx, my)
    if over_walk(COR, mx, my, z + 1.5, pad=0.24) or in_solid(mx, my):
        continue
    parts.append(obox("bm", mx, my, z + 2.15, 0.22, 0.22, 4.50, mat=MT, cname=COLL))
    parts.append(obox("bk", mx, my, z + 4.46, 0.36, 0.36, 0.14, mat=MT, cname=COLL))
BUNT = register(join_meshes(parts, "gate_bunting", COLL), pad=0.0)
log("BUILD", "gate_bunting", "%d runs, %d pennants (%d thinned out of the near field) "
    "— tapered, drooped and curled per flag, on six desaturated cloth materials "
    "pulled onto the painted-timber palette; every pennant Corridor-tested"
    % (len(RUNS), nflag, nthin))

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
# THE CLUSTER.  v6 hung the arch's two lanterns on the piers' TOWN face
# (GX + 1.24) — invisible from every frame the arriving player is ever in, which
# is the one direction a gate lamp exists for.  A gate at dusk is read by its
# lights before it is read by its stones: the arrival side now carries a pair on
# the piers, a pair hung from the lintel over the road, and the toll hatch's own
# lamp, so the threshold is a warm cluster at the end of a dark road.  Every one
# is a 680 W practical with a 14 m cutoff — the town standard, unchanged.
for yy in (YS - PIER / 2 - 0.35, YN + PIER / 2 + 0.35):
    for sx, tag in ((-1, "w"), (1, "e")):
        brackets.append(beam("br", (GX + sx * 0.62, yy, TOPZ - 2.05),
                             (GX + sx * 1.24, yy, TOPZ - 1.95), 0.06, 0.06, MIRON, COLL))
        lantern("gate_lantern_arch_%s%d" % (tag, len(LANTS)), GX + sx * 1.24, yy, TOPZ - 2.22)
# a hanging pair under the lintel, over the carriageway.  Soffit is at TOPZ+0.00
# and the road at ~24.06, so a lamp at TOPZ-1.20 still leaves >2.05 m of corridor
# — checked, not assumed (finding 99: bunting heights are absolute).
for yy in (3.05, 4.95):
    lz = TOPZ - 1.20
    if over_walk(COR, GX, yy, lz - CORRIDOR_H - 0.10, pad=0.14):
        continue
    brackets.append(cyl("hk", (GX, yy, TOPZ + 0.30), (GX, yy, lz + 0.20), 0.018, 5, MIRON, COLL))
    lantern("gate_lantern_hang_%d" % len(LANTS), GX, yy, lz)
# the toll window, the yard, the barrier and the winch
for i, (lx, ly, lz, bx, by) in enumerate((
        (HX + 1.55, HY + BD / 2 + 0.42, ground_top(HX, HY) + 2.90, HX + 1.55, HY + BD / 2 + 0.02),
        (HX - 2.28, HY + BD / 2 + 0.36, ground_top(HX, HY) + 2.74, HX - 2.10, HY + BD / 2 + 0.02),
        (SX, 3.45, ground_top(SX, 1.50) + 2.86, SX, 3.28),
        (2.75, 5.60, ground_top(2.75, 3.85) + 2.80, 2.75, 5.42),
        (BX, BY - 0.26, ground_top(BX, BY) + 2.44, BX, BY),
        (WX - 1.30, WY - 1.05, ground_top(WX, WY) + 2.90, WX - 1.30, WY - 0.30))):
    if over_walk(COR, lx, ly, lz - 0.30, pad=0.14):
        continue
    brackets.append(beam("br", (bx, by, lz + 0.46), (lx, ly, lz + 0.34), 0.055, 0.055, MIRON, COLL))
    lantern("gate_lantern_%d" % len(LANTS), lx, ly, lz)
join_meshes(brackets, "gate_lantern_brackets", COLL)
log("BUILD", "gate_lantern_* x%d" % len(LANTS),
    "warm 680 W practicals, 14 m cutoff — the town standard.  Four on the arch "
    "piers (both faces, the ARRIVAL side included), two hung from the lintel over "
    "the road, two on the toll house, two in the yard, one on the barrier, one at "
    "the winch: the gate is a lit threshold, not a dark opening")

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
        # THE NEAR FIELD.  A 1.35 m clump 3.8 m from the lens was 12% of the gate
        # frame and another was half of arrival; the placer had no idea, because
        # it was reasoning about a zone and the eye reasons about a frame.  Both
        # the keep-roll and the size ceiling come off the same number, so what
        # survives near a camera survives small (gate_lib.near_field).
        # `cull=False` for ground cover: a fern or a moss tuft never stands
        # between a lens and its subject in any meaningful sense — it is on the
        # floor.  It still gets the SIZE ceiling (a 1.8x tuft at the lens is a
        # hedge), but it is never removed, or the tier goes bald in exactly the
        # places the cameras are pointed.  Only the tall masses are thinned.
        b0 = world_bbox(src)
        ext = max(b0[1] - b0[0], b0[3] - b0[2], b0[5] - b0[4]) * s
        nf = near_field(px, py, pz + 0.45 * ext, ext)
        if cull and rng.random() > nf:
            continue
        s = min(s, lo + (hi - lo) * max(nf, 0.20 if not cull else 0.0))
        ob = src.copy()
        ob.data = src.data.copy()
        ob.name = "veg_gate_%s_%d" % (tag, i)
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
ng = clone("seam_tuft_0", "tuft", 110, (1.30, 29.2), None, 0.8, 1.8, mode="rim", cull=False)
ng += clone("seam_tuft_3", "tuft", 70, (1.20, 29.4), (0.0, 4.2), 0.8, 1.7, cull=False)
nf = clone("seam_tuft_1", "fern", 46, (1.20, 29.4), (0.0, 4.4), 0.8, 1.5, cull=False)
nf += clone("seam_tuft_37", "fern", 26, (13.4, 26.0), (6.2, 10.4), 0.8, 1.4, cull=False)
nc = clone("creeper_4", "creeper", 34, (1.60, 18.6), None, 0.7, 1.3, mode="face", zjit=-1.4,
           cull=False)
# a crown on the upper rim: "autumn trees crowning both rims" is the style note
crest = []
for i in range(22):
    px = GX0 + 0.8 + rng.random() * (GX1 - GX0 - 1.6)
    src = bpy.data.objects.get("rimclump_%d" % rng.randint(1, 12))
    if src is None:
        continue
    ob = src.copy(); ob.data = src.data.copy()
    ob.name = "veg_gate_rimclump_crest_%d" % i; ob.data.name = ob.name
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
log("BUILD", "veg_gate_rimclump_crest_* x%d" % len(crest),
    "autumn crowns seated ON the new crest, half-buried in it (manifest 71/78); the "
    "crest is 15 m above and behind every camera's near field, so it is EXEMPT from "
    "the near-field thinning — the crowns are the skyline, not clutter")
log("BUILD", "veg_gate_rimtree/rimclump/tuft/fern/creeper",
    "%d autumn crowns, %d clumps, %d tufts, %d ferns, %d creepers over the lip — "
    "everything Corridor-, carriageway- and near-field-tested" % (nt, nk, ng, nf, nc))

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
        # a joined multi-part mesh is audited by its BBOX corners (finding 97), so
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
        # the same near-field rule as the planting: a crate stack 3 m from the
        # lens is a wall, and the arrival frame had two of them holding down its
        # whole left third.  A stack is ~1.1 m over its longest side.
        if rng.random() > near_field(px, py, pz + 0.5, 1.10):
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
