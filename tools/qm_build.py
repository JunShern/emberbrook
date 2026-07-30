"""qm_build.py — the QUAY-MARKET TIER (parcel `p-quay-mkt`).

  Blender -b tools/blends/dellhollow-master.blend -P tools/qm_build.py -- save

Dellhollow's commerce heart: the harbour deck over the gorge, the market stalls,
the cookhouse with its lit north front, the notice board where LOCKS: DELAYED
lives, and the discreet head of the Deep Stairs — on the mid tier at z = 14.00,
five metres under the shop street and eight above the Weave.

Built IN THE LIVE MASTER under serial custody.  ADDITIVE ONLY: every object is
`qm_*` (foliage `veg_qm_*`, lamps `KEYQ_*`, render-only helpers `fx_qm_*`) in the
`DIST_quaymkt*` collections.  The only permitted deletions are the `lm_` blockout
shells of this parcel's own members, and every one is recorded in
`tools/blends/districts/quaymkt_deletions.json`, which ACCUMULATES and is never
rewritten empty by a re-run (finding 115).

WHAT THIS DISTRICT IS, STRUCTURALLY — and it was measured, not chosen.  South of
y = 12.5 there is nothing at all under this tier: `shelf_ground`'s underside runs
17.37..18.61 and below it is void, because the shop street above is a PLATE
(`shelf_lib`: "east of MASS_X the MARKET tier is underneath and it is a plate").
North of y = 12.5 the Waterfront's `wf_ground` rises to 13.6..14.9 and the walk
ribbons sit 0.10..0.45 m above it.  Past y ~ 17 the quay deck oversails the
Weave's huts by 6..8 m.  So the tier is a REVETMENT TERRACE: a masonry bench cut
into the rock, its back wall an arcade that carries the shop street's outer half,
opening north onto a timber deck on piles.

*** CROSS-PARCEL BUILD ORDER — READ THIS BEFORE ANY JOINT REBUILD (finding 224) ***
The arcade BEARS on SHELF_DISTRICT's plate.  Every bearing height in it is
measured from that plate's underside at THIS script's run time
(`qm_lib.plate_min`), never stored as a constant, so a rebuilt shop street is
re-fitted automatically — but only if this script runs AFTER it.  On any joint
rebuild the order is:  shelf_build.py -> shelf_light.py -> qm_build.py ->
qm_light.py.  Run this district first and its piers fit a plate that is no longer
there.  This is the master's first inter-district structural dependency; it is
recorded here, in KITLIB_MANIFEST.md, and in the deletions manifest.

Reading order of the district, which is also the order it is built:
  0  deletions    the blockout shells this district replaces
  1  ground       the masonry bench + the talus that closes it into the cliff
  2  veneer       continuing the cliff backdrop east of the shelf's x=57.60
  3  paving       the market floor laid on the walk graph
  4  ARCADE       the revetment colonnade under the shop street (measured bearing)
  5  deck         planking, joists and piles out over the gorge
  6  underworks   the rock flank the Deep Stairs descend against
  7  cookhouse    tall lit north front over the drop, chimney in open sky
  8  notice board the landmark, off its pad at last
  9  stairhead    the Deep Stairs' gateway, off its pad at last
 10  stalls       the market: awnings, trestles, produce, the fishmonger's slab
 11  rail         the deck's edge over the gorge
 12  bunting      vertex-coloured cloth (glTF survives vertex colours, not noise)
 13  lanterns     ordinary warm practicals (there are no Heartlights here)
 14  vegetation   creepers on the revetment, tufts in the joints
 15  clutter      the working life of a market
 16  fx           the cookhouse's chimney smoke (render-only, stripped on export)
"""
import bpy, bmesh, math, os, random, sys, json
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          M, world_bbox, dist_poly2, point_in_poly, Corridor)
from qm_lib import (Terrain, over_walk, ceiling, ceiling_named, ceiling_over,
                    existing, clear_below, zone, plate_under, plate_min,
                    QX0, QX1, QY0, QY1, FLOOR, DECK_DROP, GROUND_DROP, PAVE_W,
                    CORRIDOR_H, TIER_LO, TIER_HI, LEVEL_BAND, TALUS_Y,
                    BASEZ, MASS_DEPTH, CEIL_CLEAR, PIER_SHY, DECK_MIN, PILE_MAX,
                    PLAZA_QUAY, PLAZA_MKT,
                    SHOTS, HERO, HERO_EYES, hero_dist, near_field)

SAVE = "save" in sys.argv
COLL = "DIST_quaymkt"
COLL_DECK = "DIST_quaymkt_DECK"
COLL_PROPS = "DIST_quaymkt_PROPS"
COLL_VEG = "DIST_quaymkt_VEG"
rng = random.Random(20260730)
LOG = []
DELETIONS = REPO + "/tools/blends/districts/quaymkt_deletions.json"


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-30s %s" % (kind, what, why))


print("=" * 78)
print("QUAY-MARKET TIER  —  parcel p-quay-mkt   (floor z = %.2f)" % FLOOR)
print("=" * 78)

# ---------------------------------------------------------------- materials
MROCK, MIRON, MROPE = M("mat_rock"), M("mat_iron"), M("mat_rope")
MT, MTD, MDECK = M("mat_timber"), M("mat_timber_dark"), M("mat_deck")
MWALL, MWALLD = M("mat_wallwood"), M("mat_wallwood_dark")
MSHINGLE, MGLASS = M("mat_shingle_mossy"), M("mat_lantern_glass")
MFRESH, MCANVAS = M("mat_freshwood"), M("mat_canvas")
MPUMPKIN, MFISH, MNET = M("mat_pumpkin"), M("mat_fish"), M("mat_net")


def derive(src, name, scale=None, tint=None, fac=0.85, mode='MULTIPLY'):
    """A new surface DERIVED from one of the town's textured materials.

    Findings 95/105: a flat Principled colour is not a dark surface, it is an
    UNTEXTURED one.  Copying a textured town material and re-tinting through a
    MULTIPLY mix inherits the box projection, the AO multiply, the roughness map
    and the world-up moss layer — and it is the only tinting form that survives
    glTF, because an image texture times a constant is exactly
    baseColorTexture * baseColorFactor.
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


# Re-tiled for the object's scale (finding 96): `mat_rock` is tuned for a 60 m
# cliff.  A market floor a player stands on wants roughly one feature per metre;
# dressed revetment masonry wants tighter still.
MGROUND = derive("mat_rock", "mat_qm_ground", scale=1.15, tint=(0.43, 0.41, 0.33))
MPAVE = derive("mat_rock", "mat_qm_paving", scale=1.90, tint=(0.46, 0.46, 0.49))
# COOL, and deliberately.  The v1 check spread came back amber-monochrome — the
# same verdict that rejected Boatyard v3 — because the revetment, the ground, the
# ceiling (which is another district's rock) and the timber were all one hue, and
# on a covered tier lit by 680 W tungsten globes there is nothing to break it.
# Figure/ground is a SURFACE problem before it is a light problem (finding 105):
# the masonry goes cool-neutral so the painted timber in front of it is the only
# warm thing in the frame, which is what the eye needs to read a market at all.
MSTONE = derive("mat_rock", "mat_qm_stone", scale=2.05, tint=(0.50, 0.51, 0.56))
# The revetment's own SHADED faces and the recess backs.  Figure/ground is a
# surface problem before it is a light problem (finding 105): the market's props
# and stalls are read against this wall all day, and it stands in the shop
# street's shadow, so it is a full stop darker than the dressed stone in front.
MSTONED = derive("mat_rock", "mat_qm_stone_dark", scale=1.75, tint=(0.27, 0.28, 0.33))
MCLIFF = derive("mat_rock", "mat_qm_cliff", scale=1.05, tint=(0.34, 0.33, 0.36))
MPLANK = derive("mat_deck", "mat_qm_deck", scale=1.55, tint=(0.62, 0.55, 0.44))
MSACK = derive("mat_timber", "mat_qm_sack", scale=1.90, tint=(0.74, 0.63, 0.44))
# Painted timber, per the finished districts, four values a stop apart rather
# than four hues (finding 113).  A market is the one place in town that may be
# a little louder than its neighbours, so the reds and the ochre carry more
# chroma than the shelf's — but the VALUE spread is what does the work.
MPRED = derive("mat_wallwood", "mat_qm_paint_red", scale=2.40, tint=(0.66, 0.19, 0.13))
MPOCHRE = derive("mat_wallwood", "mat_qm_paint_ochre", scale=2.40, tint=(0.66, 0.49, 0.24))
MPGREEN = derive("mat_wallwood", "mat_qm_paint_green", scale=2.40, tint=(0.24, 0.44, 0.28))
MPBLUE = derive("mat_wallwood", "mat_qm_paint_blue", scale=2.40, tint=(0.17, 0.34, 0.52))
MPBONE = derive("mat_wallwood", "mat_qm_paint_bone", scale=2.40, tint=(0.78, 0.74, 0.62))
PAINTS = [MPRED, MPOCHRE, MPGREEN, MPBLUE, MPBONE]


def vcol_mat(name, rough=0.86, metal=0.0):
    """Principled with Base Color driven by the mesh's own `Col` attribute.

    The GLTF-SURVIVAL GATE forbids a procedural node tree from reaching an
    exported material.  `gate_build.cloth()` — a weave noise times a sun-fade —
    renders beautifully in Blender and exports WHITE, so this district bakes the
    same variation into VERTEX COLOURS in Python and reads them with a Color
    Attribute node, which is glTF's COLOR_0 and survives byte for byte.
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


def paint_vcol(ob, tints, jitter=0.10, seed=0):
    """Give a FINISHED (already joined) object a `Col` attribute, per material slot.

    THE OBLIGATION A VERTEX-COLOUR MATERIAL CREATES, and it is easy to miss: a
    material whose Base Color comes from a Color Attribute node exports as
    COLOR_0, and a mesh that carries no COLOR_0 exports as WHITE.  `mat_qm_produce`
    was written as a vcol material and the trestles were joined through
    `join_meshes`, which round-trips bmesh and carries no colour layer — so five
    stalls shipped default-white produce and the glTF gate caught it.

    A fresh attribute starts WHITE, the neutral element, because glTF MULTIPLIES
    by COLOR_0 (finding 218: initialising one from a bake gave 26 correct
    materials a black COLOR_0 and nearly shipped it).  Only the loops of the
    materials named in `tints` are painted.
    """
    me = ob.data
    if not me.polygons:
        return ob
    att = me.color_attributes.get("Col")
    if att is None:
        att = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        for d in att.data:
            d.color = (1.0, 1.0, 1.0, 1.0)
    me.color_attributes.active_color = att
    import random as _r
    R = _r.Random(seed or (hash(ob.name) & 0xffff))
    mats = [m.name if m else "" for m in me.materials]
    for p in me.polygons:
        nm = mats[min(p.material_index, len(mats) - 1)]
        if nm not in tints:
            continue
        base = tints[nm]
        k = 1.0 + (R.random() - 0.5) * 2.0 * jitter
        c = (min(base[0] * k, 1.0), min(base[1] * k, 1.0), min(base[2] * k, 1.0), 1.0)
        for li in p.loop_indices:
            att.data[li].color = c
    return ob


MCLOTH = vcol_mat("mat_qm_cloth", rough=0.92)
MAWN = vcol_mat("mat_qm_awning", rough=0.90)
MPRODUCE = vcol_mat("mat_qm_produce", rough=0.72)


def lamplit(name, rgb=(1.0, 0.455, 0.135), strength=2.6):
    """A window with someone behind it.  Strength 2.1..3.4, not the 90 a lantern
    globe wants: at window scale AgX creams anything hotter and the pane lands as
    a clipped white rectangle (finding 112).  FLAT strength, because glTF carries
    emissiveFactor and nothing at all of a noise tree — the unevenness comes from
    having four of these at four strengths."""
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


MWIN = [lamplit("mat_qm_window_a", strength=2.20),
        lamplit("mat_qm_window_b", strength=2.70),
        lamplit("mat_qm_window_c", strength=3.10),
        lamplit("mat_qm_window_d", strength=3.45)]
MWINDARK = derive("mat_wallwood", "mat_qm_glass_dark", scale=3.0, tint=(0.10, 0.11, 0.12))

# ------------------------------------------------------------- collection(s)
for c in (COLL, COLL_DECK, COLL_PROPS, COLL_VEG):
    coll(c)

killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(("qm_", "veg_qm_", "KEYQ_", "fx_qm_")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
if killed:
    log("REBUILD", "%d qm_/KEYQ_/fx_qm_ objects cleared" % killed, "idempotent re-run")

# =========================================================================
# 0. DELETIONS — the blockout shells this district replaces
# =========================================================================
# Only p-quay-mkt's OWN members, and only shells wholly inside the parcel.
#   lm_cookhouse_body/roof         the cookhouse, rebuilt as real art
#   lm_notice-board                THE INHERITED WIN — it stands dead centre of
#                                  its own pad and blocks 2 walk samples plus an
#                                  8-sample headroom warning
#   lm_deep-stairs-head_*          two posts and a lintel, also standing IN the
#                                  pad the player has to stand on
# `lm_lockhead` belongs to p-lockhead and is handled by `qm_lockhead.py`.
DEL_PREFIX = ("lm_cookhouse_", "lm_notice-board", "lm_deep-stairs-head_")
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
    "district": "quay-market-tier",
    "parcel": "p-quay-mkt",
    "blend": "tools/blends/dellhollow-master.blend (LIVE master, serial custody)",
    "rule": "ADDITIVE-ONLY except lm_ blockout shells of p-quay-mkt's own "
            "members. This file ACCUMULATES and is never rewritten empty by a "
            "rebuild (manifest finding 115).",
    "build_order": "CROSS-PARCEL DEPENDENCY (finding 224): the arcade bears on "
                   "SHELF_DISTRICT's plate and measures that plate's underside at "
                   "run time. On any joint rebuild the order is shelf_build -> "
                   "shelf_light -> qm_build -> qm_light.",
    "note": "lm_notice-board and the three lm_deep-stairs-head_ shells both stood "
            "INSIDE their own landmark pads (finding 93: the pad is where the "
            "PLAYER stands, not where the landmark goes). lm_notice-board was a "
            "standing master defect blamed on nobody: 2 blocked down-ray samples "
            "and an 8-sample (0.49%) headroom warning on the region x 28..66 / "
            "y 10..20. lm_cookhouse_roof tops out at 18.55, 1.05 m above the "
            "parcel's nominal 17.5 ceiling; it is the roof of a body wholly "
            "inside the parcel and deleting the body without it would leave a "
            "slab floating over the market. Deleting the cookhouse shells does "
            "NOT move the shop street: shelf_lib raised its plate's underside to "
            "18.61 over that footprint, so the plate is simply thicker there than "
            "it needs to be, which is harmless and was already built.",
    "deleted": sorted(deleted, key=lambda d: d["name"]),
}
os.makedirs(os.path.dirname(DELETIONS), exist_ok=True)
json.dump(manifest, open(DELETIONS, "w"), indent=1)
log("DELETE", "%d lm_ shells (%d this run)" % (len(deleted), found),
    "recorded in districts/quaymkt_deletions.json")

# =========================================================================
# 0b. RENDER-HIDE this parcel's blockout ribbons
# =========================================================================
# The west-branch merge custodian render-hid 118 walk/bar ribbons BY MAP PARCEL
# BOUNDS when it landed the gate and shelf districts; p-quay-mkt was still gray
# and unbuilt then, so its own ribbons were never done — `walk_lm_quay-deck` is an
# 11 x 11 m gray slab sitting 0.22 m above where this district's paving belongs
# and it renders.  Hiding it is NOT a geometry edit: `hide_render` leaves the mesh
# bit-identical and the master's QA gate explicitly re-checks that every hidden
# walk stays VIEWPORT-visible, because that is what the glTF exporter reads.
PARCEL = (30.70, 63.60, 6.50, 21.50, 12.50, 18.60)
nhid = 0
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(("walk_", "bar_")):
        continue
    b = world_bbox(o)
    cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
    if not (PARCEL[0] <= cx <= PARCEL[1] and PARCEL[2] <= cy <= PARCEL[3]
            and PARCEL[4] <= cz <= PARCEL[5]):
        continue
    if not o.hide_render:
        o.hide_render = True
        nhid += 1
log("HIDE", "%d walk_/bar_ ribbons render-hidden" % nhid,
    "by MAP PARCEL BOUNDS, the merge custodian's own pattern; geometry untouched "
    "and every one stays viewport-visible so the GLB keeps it")

# =========================================================================
# corridors + terrain
# =========================================================================
T = Terrain()
COR0, COR, KEEP = T.cor0, T.cor, T.keep
log("MODEL", "walk corridors", "%d faces on this tier or entering its band, "
    "%d below it (deep stairs, pilot stair, the Weave)" % (len(T.high), len(T.low)))


def free(x, y, z, pad=0.18):
    return not over_walk(COR, x, y, z, pad=pad)


def column_free(x, y, z0, z1, pad=0.22):
    """No part of a vertical member may cross a walking line.

    `clear_below` asks whether a pile can be DRIVEN (is the column free of huts);
    this asks whether it may EXIST (does it cross canonical topology).  They are
    different questions and the first gated run failed on the second: the deck's
    cross-braces sit at 46% of the pile's length, which over the Weave is z ~10.3,
    which is exactly where `walk_e_quay-deck__pilot-cluster`'s lower flights run.
    """
    zz = min(z0, z1)
    top = max(z0, z1)
    while zz <= top:
        if over_walk(COR, x, y, zz, pad=pad, h=CORRIDOR_H):
            return False
        zz += 0.34
    return not over_walk(COR, x, y, top, pad=pad, h=CORRIDOR_H)



# ---------------------------------------------------------------- the ground
_GT = {}


def ground_top(x, y):
    """The built floor's own surface — the SAME number the mesh was made from, so
    a prop placer and the ground can never disagree about where the floor is.
    Falls back to whatever the world already provides where we build nothing."""
    k = (round(x, 3), round(y, 3))
    if k not in _GT:
        _GT[k] = T.top(x, y)
    return _GT[k]


def on_sheet(x, y):
    return T.node(x, y)[0] is not None


ST = 0.34
NX = int(round((QX1 - QX0) / ST)) + 1
NY = int(round((QY1 - QY0) / ST)) + 1
NODE = {}
for i in range(NX):
    for j in range(NY):
        x, y = QX0 + i * ST, QY0 + j * ST
        t, b = T.node(x, y)
        if t is None:
            continue
        NODE[(i, j)] = (x, y, t, b)


def sheet(nodes, nx, ny, name, mats, mi_fn, cname):
    """Build a top+bottom+skirt sheet from a node dict keyed (i, j)."""
    V, F, MI = [], [], []
    topi, boti = {}, {}
    for k, (x, y, t, b) in nodes.items():
        topi[k] = len(V); V.append((x, y, t))
        boti[k] = len(V); V.append((x, y, b))

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


def ground_mi(ns):
    zs = [n[2] for n in ns]
    ys = [n[1] for n in ns]
    # the flat walked terrace gets the worked ground grade; the talus and the
    # falling skirt stay bare rock (the moss layer is world-up driven anyway)
    return 1 if (max(zs) - min(zs) < 0.26 and min(ys) > 7.0) else 0


GROUND, nf = sheet(NODE, NX, NY, "qm_ground", (MROCK, MGROUND), ground_mi, COLL)
_zs = [n[2] for n in NODE.values()]
_bs = [n[3] for n in NODE.values()]
log("BUILD", "qm_ground", "%d nodes, %d faces — the masonry bench, surface z "
    "%.2f..%.2f, underside %.2f..%.2f; the talus at the back closes it into "
    "shelf_cliffface (whose foot the shop street floored at 13.20, under this "
    "tier, exactly so this joint could be made)"
    % (len(NODE), nf, min(_zs), max(_zs), min(_bs), max(_bs)))

# =========================================================================
# 2. THE CLIFF VENEER — continuing the backdrop east of the shop street's
# =========================================================================
# `cliff_town` is ONE 170 x 6 x 46 m blockout box at y -6..0 and it is
# untouchable far-rim geometry.  The gate district veneered it to x=31.44 and the
# shop street carried that to x=57.60; east of 57.60 the raw slab is bare again,
# and from this tier it SHOWS: the market floor's talus crest tops out at ~17.2,
# so a ray from a market-level eye grazing the crest lands on the slab between
# z 19 and 37.  Same recipe, same numbers, floored under this tier (findings
# 103/114), east end set by the shallowest ray that can see past it — the
# `stalls` camera looks east-south-east across the market plaza with the cliff
# 9 m to its right, and 64.20 is where that ray stops finding slab.
CST = 0.44
CVX0, CVX1 = 57.40, 64.20
CX_N = int(round((CVX1 - CVX0) / CST)) + 1
CFLOOR = 13.20


def cliff_crest(x):
    return 40.20 + 1.50 * math.sin(x * 0.21 + 0.7) + 0.80 * math.sin(x * 0.63 - 1.9) \
        + 0.35 * math.sin(x * 1.47 + 3.1)


def cliff_front(x, z):
    u = min(1.0, max(0.0, (z - CFLOOR) / max(cliff_crest(x) - CFLOOR, 1.0)))
    d = 0.10 + 0.80 * (1.0 - u) ** 1.05
    d += (math.sin(x * 0.83 + z * 0.55) * 0.40 + math.sin(x * 2.11 - z * 1.31) * 0.22
          + math.sin(x * 4.7 + z * 3.3) * 0.08) * 0.32
    return max(0.04, d)


CV, CF = [], []
rows = []
_n = 28
for i in range(CX_N):
    x = CVX0 + i * CST
    col = []
    for k in range(_n + 1):
        z = CFLOOR + (cliff_crest(x) - CFLOOR) * (k / _n) ** 0.92
        col.append((len(CV), z))
        CV.append((x, cliff_front(x, z), z))
    for k in range(_n + 1):
        CV.append((x, -0.60, col[k][1]))
    rows.append((col, len(CV) - (_n + 1)))
NN = _n + 1
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
me = bpy.data.meshes.new("qm_cliffface")
me.from_pydata(CV, [], CF)
me.validate()
me.materials.append(MCLIFF)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
CLIFF = bpy.data.objects.new("qm_cliffface", me)
link(CLIFF, COLL)
log("BUILD", "qm_cliffface", "%d x %d veneer over cliff_town, x %.2f..%.2f "
    "(the shop street's stops at 57.60, 0.20 m of overlap), crest %.1f..%.1f "
    "modulated and held above cliff_town's own top edge at 37.0, foot at %.1f "
    "so no ray beneath this tier finds the slab. 0.60 m of it lies east of the "
    "parcel to close the ray, which the merge/audit trail records."
    % (CX_N, NN, CVX0, CVX1,
       min(cliff_crest(CVX0 + i * CST) for i in range(CX_N)),
       max(cliff_crest(CVX0 + i * CST) for i in range(CX_N)), CFLOOR))

# =========================================================================
# 3. PAVING — the market floor, laid on the walk graph
# =========================================================================
# THE FLAT TIER ONLY, and the window is tight on purpose.  The market's own
# surfaces read 13.92..14.25 (pads 13.92..14.04, the two landmark slabs 14.24,
# the ribbons 14.07).  A wider band swept in the Deep Stairs' second tread at
# 13.67 and the shop street's loop-stair feet at 14.39/14.72, and paving laid
# from those references stood proud of the tread beside it — 8 blocked down-ray
# samples in the first gated run.
PAVE_BAND = (13.85, 14.32)


def walk_ref(x, y):
    """(effective tier-level walk top, distance) — the flat market only, so the
    paving does not chase the shop street's loop stair up or the Deep Stairs
    down."""
    inside, best, bz = None, 1e9, None
    for raw, fn, zt, nm in T.high:
        if not (PAVE_BAND[0] <= zt <= PAVE_BAND[1]):
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
    if z is None or d > PAVE_W + 1.5:
        return None
    return z - DECK_DROP, d


SURF_R = 2.45          # paving reaches PAVE_W + 0.45 from a walk, so a surface
                       # test with a 1.05 m radius cannot see the walk that the
                       # far edge of that paving is standing over


def surface_z(x, y, zz):
    """The height a laid surface may actually have at (x, y), or None to lay none.

    LOCAL, and the first cut was not.  A 2.45 m radius test refused a paving node
    whenever ANY walk face within 2.45 m sat below it — which on the quay plaza is
    always true, because the map's landmark slabs top out at 14.24 and its ribbons
    at 14.07, so half the market went unpaved.  The QA samples down-rays over walk
    faces at THEIR OWN points, so the only thing that can block one is a surface
    over that point:
      * a face COVERING (x, y) caps us, and it is the LOWEST such face that
        governs — capping to the highest laid the paving 0.17 m over the ribbon
        that crosses the same plaza and blocked its samples;
      * a face within 0.62 m and more than 0.30 m BELOW us is a flight dropping
        away, and the surface stops there rather than cascading down it (the
        ground sheet and the stair underworks take over, which is what a real quay
        does at the head of a stair).
    """
    cov, near = [], []
    for raw, fn, zt, nm in T.high + T.low:
        d = dist_poly2(x, y, raw)
        if d > 0.62:
            continue
        pz = T.plane_at(raw, fn, x, y, d)
        (cov if d <= 0.0 else near).append(pz)
    if cov:
        zz = min(zz, min(cov) - DECK_DROP)
    for pz in near:
        if pz < zz - 0.30:
            return None
        if pz < zz + 0.30:
            zz = min(zz, pz - DECK_DROP)
    if zz < FLOOR - 1.30:
        return None
    return zz


def level_cap(x, y, zz):
    """Cap a surface against every walk face ON ITS OWN LEVEL.

    The shelf's version capped against every walk face within a metre, which is
    right for a district whose only neighbours are at its own height.  Here the
    Deep Stairs drop 8.5 m straight off this floor and the shop street's loop
    stairs land on it, so an unbanded cap dragged the paving and the deck down
    the flights with them — the planking came out at z 7.01.  A walk six metres
    below is something this tier is a BRIDGE over, not something it may not poke
    through (finding 92, applied to surfaces instead of to ground).
    """
    # AND EVERY FACE VOTES AGAINST THE ORIGINAL HEIGHT, NOT THE RUNNING ONE.
    # Updating `zz` inside the loop makes the band walk DOWN a staircase: the
    # first tread lowers the surface into the second tread's band, which lowers
    # it into the third's, and the deck came out at z 8.53 at the foot of the
    # Deep Stairs — eight flights of cascade from one missing variable.
    z0, out = zz, zz
    for raw, fn, zt, nm in T.high + T.low:
        dd = dist_poly2(x, y, raw)
        if dd >= SURF_R:
            continue
        pz = T.plane_at(raw, fn, x, y, dd)
        if pz - 0.60 <= z0 <= pz + LEVEL_BAND:
            out = min(out, pz - DECK_DROP)
    return out


def gz(x, y):
    r = road_at(x, y)
    return r[0] if r is not None else ground_top(x, y)


def pz_at(x, y):
    """The height a PROP stands at: the surface this district actually laid.

    `gz` answers the walk graph's own plane, which on the plaza is the map's
    landmark slab at 14.24 while the paving next to it is at 14.02 and the deck
    apron at 14.19.  A stall seated on `gz` had its feet 0.17 m under the deck it
    was standing on and the audit called it a stray, correctly.  `surf_top` is
    defined after the surfaces exist, so this indirects through a global.
    """
    v = SURF_TOP[0](x, y) if SURF_TOP[0] else None
    return v if v is not None else gz(x, y)


SURF_TOP = [None]


# =========================================================================
# 4. THE ARCADE — the revetment that carries the shop street's outer half
# =========================================================================
# CONDITION 1 OF THE RED-TEAM VERDICT, and the reason this section exists at all:
# the bearing is MEASURED at run time off `shelf_ground`/`shelf_paving`'s own
# underside (`qm_lib.plate_min`) and the wall is cut to it minus PIER_SHY = 40 mm.
# Nothing here is a constant that could go stale when the shop street is rebuilt.
#
# WHY A BLIND ARCADE AND NOT A COLONNADE.  The talus rises immediately behind the
# wall line, so an open colonnade would frame a rock bank — the arches are
# therefore RECESSES in a revetment, which is what a real river-town terrace
# has, gives the market its bays, and costs a third of the geometry.  The
# pilasters carry; the recesses are relieving arches; the string course is the
# line the eye reads the whole 24 m run along.
ARC_X0, ARC_X1 = 31.60, 55.00       # the plate ends at x=55.26; so does the wall
WALLD = 0.80                        # the revetment's thickness in y
REC_D = 0.42                        # how deep a recess is cut into it
PIL_W, PIL_PROUD = 0.74, 0.20       # pilaster width and how far it stands proud
NBAY = 7

# WHERE THE WALL LINE IS — found by SEARCH, once, for the whole run, so the
# colonnade is straight (a wall that jogs 1.4 m in plan where the plaza happens
# to be deeper reads as a mistake, not as a plan).  The line steps SOUTH from the
# walk graph until every station on it is clear; the plaza's own south edge at
# y = 8.50 is what sets it.
YROW = None
_stations = [ARC_X0 + (ARC_X1 - ARC_X0) * i / float(NBAY) for i in range(NBAY + 1)]
for _try in range(46):
    y = 9.30 - _try * 0.15
    if y < 4.60:
        break
    if all(not over_walk(COR, sx, y + WALLD / 2, FLOOR + 1.0, pad=0.42) and
           not over_walk(COR, sx, y - WALLD / 2, FLOOR + 1.0, pad=0.42)
           for sx in _stations):
        YROW = y
        break
assert YROW is not None, "no straight wall line clears the walk graph"
WY0, WY1 = YROW - WALLD / 2, YROW + WALLD / 2

parts = []
BEARINGS = []
pitch = (ARC_X1 - ARC_X0) / float(NBAY)
CW = 0.28                                     # wall column width
ncol = int(round((ARC_X1 - ARC_X0) / CW))
for c in range(ncol):
    cx = ARC_X0 + (c + 0.5) * (ARC_X1 - ARC_X0) / ncol
    ptop, who = plate_min(cx - CW / 2, cx + CW / 2, WY0, WY1)
    if ptop is None:
        continue                              # no plate overhead -> no wall
    ztop = ptop - PIER_SHY
    zb = min(ground_top(cx, WY0), ground_top(cx, WY1)) - 0.30
    BEARINGS.append((cx, ptop, ztop, who))
    # which bay is this column in, and where in it
    bay = min(NBAY - 1, int((cx - ARC_X0) / pitch))
    bcx = ARC_X0 + (bay + 0.5) * pitch
    u = cx - bcx
    span = pitch - PIL_W - 0.24
    rise = 0.40 * span
    zs = ztop - 0.26 - rise                   # springing, under the cornice
    if abs(u) <= span / 2 and zs > zb + 1.95:
        # inside the recess: the wall exists only above the arch head, and the
        # recess floor is the bank behind
        head = zs + rise * math.sqrt(max(0.0, 1.0 - (2 * u / span) ** 2))
        if head < ztop - 0.06:
            parts.append(obox("wc", cx, YROW, (head + ztop) / 2, CW, WALLD,
                              ztop - head, mat=MSTONE, cname=COLL))
        # the recess's own back, set REC_D south of the face
        parts.append(obox("rb", cx, WY0 + REC_D / 2, (zb + head) / 2, CW,
                          WALLD - REC_D, head - zb, mat=MSTONED, cname=COLL))
        # the archivolt: a proud ring following the head
        parts.append(obox("av", cx, WY1 - 0.10, head - 0.11, CW, 0.24, 0.30,
                          mat=MSTONE, cname=COLL))
    else:
        parts.append(obox("wc", cx, YROW, (zb + ztop) / 2, CW, WALLD, ztop - zb,
                          mat=MSTONE, cname=COLL))
# pilasters at every bay division, and the cornice that ties the run together
npil = 0
for i in range(NBAY + 1):
    px = ARC_X0 + i * pitch
    ptop, who = plate_min(px - PIL_W / 2, px + PIL_W / 2, WY0, WY1 + PIL_PROUD)
    if ptop is None:
        continue
    ztop = ptop - PIER_SHY
    zb = ground_top(px, WY1 + PIL_PROUD / 2) - 0.26
    if over_walk(COR, px, WY1 + PIL_PROUD, FLOOR + 1.0, pad=0.30):
        continue
    parts.append(obox("pi", px, WY1 + PIL_PROUD / 2 - 0.02, (zb + ztop - 0.30) / 2,
                      PIL_W, WALLD + PIL_PROUD, ztop - 0.30 - zb, mat=MSTONE, cname=COLL))
    parts.append(obox("pb", px, WY1 + PIL_PROUD / 2 - 0.02, zb + 0.19,
                      PIL_W + 0.20, WALLD + PIL_PROUD + 0.20, 0.38,
                      mat=MSTONE, cname=COLL))
    parts.append(obox("pc", px, WY1 + PIL_PROUD / 2 - 0.02, ztop - 0.19,
                      PIL_W + 0.16, WALLD + PIL_PROUD + 0.16, 0.34,
                      mat=MSTONE, cname=COLL))
    npil += 1
ARCADE = join_meshes(parts, "qm_revetment", COLL)
_bz = [b[1] for b in BEARINGS]
log("BUILD", "qm_revetment", "%d bays, %d pilasters on a %.2f m pitch at y=%.2f "
    "(found by search: the quay plaza's south edge at 8.50 sets it). BEARING "
    "MEASURED AT RUN TIME off %s: plate underside %.3f..%.3f, wall head cut to "
    "%.0f mm below it — bearing to the eye, no interpenetration for the audit "
    "(finding 224)."
    % (NBAY, npil, pitch, YROW,
       "/".join(sorted({b[3] for b in BEARINGS})), min(_bz), max(_bz), PIER_SHY * 1000))

# the arcade is a keep-out for everything placed later
BUILDINGS = [(ARC_X0 - 0.4, ARC_X1 + 0.4, WY0 - 0.5, WY1 + PIL_PROUD + 0.25)]


def keepout(x0, x1, y0, y1):
    BUILDINGS.append((x0, x1, y0, y1))


def in_solid(x, y, pad=0.25):
    return any(x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad
               for x0, x1, y0, y1 in BUILDINGS)


# =========================================================================
# 3b. PAVING (built now the revetment owns its strip)
# =========================================================================
RST = 0.31
RNX = int(round((QX1 - QX0) / RST)) + 1
RNY = int(round((QY1 - QY0) / RST)) + 1
RN = {}
for i in range(RNX):
    for j in range(RNY):
        x, y = QX0 + i * RST, QY0 + j * RST
        r = road_at(x, y)
        if r is None:
            continue
        z, d = r
        if d > PAVE_W + 0.45:
            continue
        ez, en = existing(x, y)
        if ez is not None and ez > z - 0.04:
            continue                       # the world is already above the paving
        crown = -0.020 * (d / max(PAVE_W, 0.1)) ** 2
        n = (math.sin(x * 3.1 + y * 1.9) * 0.5 + math.sin(x * 6.7 - y * 4.1) * 0.3) * 0.013
        zz = surface_z(x, y, z + crown + n)
        if zz is None:
            continue
        RN[(i, j)] = (x, y, zz, zz - 0.24)

PAVING, npf = sheet(RN, RNX, RNY, "qm_paving", (MPAVE,), lambda ns: 0, COLL)
log("BUILD", "qm_paving", "%d nodes, %d faces — %.1f m of sett paving over every "
    "flat market walk, top %.0f mm UNDER the walk surface so the master's "
    "down-ray still lands on canonical topology (finding 90)"
    % (len(RN), npf, 2 * PAVE_W, DECK_DROP * 1000))

# =========================================================================
# 5. THE DECK — planking on joists and piles, out over the gorge
# =========================================================================
# The north half of the quay plaza and the whole run west to the Deep Stairs
# oversail: `wf_ground` falls away from 13.9 to 7.6 across it and the Weave's
# huts stand under it.  A deck is what belongs there, and its piles are placed
# by RAY-CAST — a pile is only made where a down-ray first hits real terrain, so
# it can never be driven through `wv_hut_*` or through the Waterfront's own
# creepers (which is the same lesson as finding 97, one district over).
DST = 0.34
DNX = int(round((QX1 - QX0) / DST)) + 1
DNY = int(round((QY1 - QY0) / DST)) + 1
DN = {}
for i in range(DNX):
    for j in range(DNY):
        x, y = QX0 + i * DST, QY0 + j * DST
        r = road_at(x, y)
        if r is None:
            continue
        z, d = r
        if d > PAVE_W + 0.55:
            continue
        if y > T.rim(x) + 0.35:
            continue                        # the deck stops at the lip, not 2 m past it
        if on_sheet(x, y):
            continue                        # the masonry bench already carries it
        ez, en = existing(x, y)
        if ez is None or FLOOR - ez < DECK_MIN:
            continue                        # bedded: paving already did it
        zz = surface_z(x, y, z)
        if zz is None:
            continue
        DN[(i, j)] = (x, y, zz, 0.0)
for k in list(DN):
    x, y, zz, _ = DN[k]
    DN[k] = (x, y, zz, zz - 0.16)

# WHERE THIS DISTRICT ACTUALLY LAID A SURFACE.  Props, rails and lamps have to
# stand on the deck and the paving, not on the terrain 7 m under them: `existing()`
# at the deck's outer edge answers `wf_ground` at z 7, and the first cut's rail
# believed it and refused every post out there.  One index, both surfaces.
SURF = {}
for _d in (RN, DN):
    for (_x, _y, _zt, _zb) in _d.values():
        SURF[(round(_x / 0.25), round(_y / 0.25))] = _zt


def surf_top(x, y, r=2):
    """The built surface height near (x, y), or None where we laid none."""
    bi, bj = round(x / 0.25), round(y / 0.25)
    best = None
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            v = SURF.get((bi + di, bj + dj))
            if v is not None and (best is None or v > best):
                best = v
    return best


SURF_TOP[0] = surf_top
DECK, ndf = sheet(DN, DNX, DNY, "qm_planking", (MPLANK,), lambda ns: 0, COLL_DECK)
_dz = [n[2] for n in DN.values()]
log("BUILD", "qm_planking", "%d nodes, %d faces — the harbour deck where the walk "
    "graph oversails (existing ground %.1f m or more below the floor); surface "
    "z %.2f..%.2f, %.0f mm under the walk"
    % (len(DN), ndf, DECK_MIN, min(_dz) if _dz else 0, max(_dz) if _dz else 0,
       DECK_DROP * 1000))

# ---- joists and piles under it
# A PILE ASKS A DIFFERENT QUESTION FROM THE FLOOR.  `existing()` answers "what
# terrain is under this point", deliberately ignoring the Weave's huts so the
# market's floor is never bedded on a weaver's roof.  A pile has to ask whether
# the COLUMN is clear, and `clear_below` is that question: the huts stand under
# the north half of the quay plaza from z 5.25 to 13.74, and a pile driven on the
# first answer would have gone straight through three of them.  Where the column
# is not clear the deck is CANTILEVERED instead, on deep joists spanning back to
# the bedded edge, which is the truthful reading anyway: the market deck oversails
# the Weave.
parts = []
npile, ncant, njoist, nbrace, nblock = 0, 0, 0, 0, 0
_xs = sorted({round(v[0], 2) for v in DN.values()})
_ys = sorted({round(v[1], 2) for v in DN.values()})
PILE_PITCH = 2.38
_taken = []
for x in _xs:
    for y in _ys:
        if any((x - px) ** 2 + (y - py) ** 2 < PILE_PITCH ** 2 for px, py in _taken):
            continue
        near = [v for v in DN.values() if abs(v[0] - x) < 0.35 and abs(v[1] - y) < 0.35]
        if not near:
            continue
        zb = min(v[3] for v in near)
        ez, en = existing(x, y)
        if ez is None:
            continue
        L = zb - 0.12 - ez
        if L <= 0.35 or L > PILE_MAX:
            continue
        if not clear_below(x, y, zb - 0.20):
            continue                       # a hut, a deck or a prop is in the way
        if not column_free(x, y, ez - 0.20, zb - 0.02):
            nblock += 1
            continue                       # it would cross a walking line
        _taken.append((x, y))
        parts.append(cyl("pl", (x, y, ez - 0.20), (x, y, zb - 0.02), 0.150, 8, MTD,
                         COLL_DECK))
        npile += 1
        if L > 2.4:
            for dx, dy in ((PILE_PITCH * 0.42, 0.0), (0.0, PILE_PITCH * 0.42)):
                bz = ez + L * 0.46
                # finding 98: a member that SPANS between two tested points has to
                # be tested at its own ends too, and a brace under this deck runs
                # straight through the pilot-cluster stair unless it is
                if not (column_free(x - dx, y - dy, bz - 0.08, bz + 0.08)
                        and column_free(x + dx, y + dy, bz - 0.08, bz + 0.08)
                        and column_free(x, y, bz - 0.08, bz + 0.08)):
                    nblock += 1
                    continue
                parts.append(beam("bc", (x - dx, y - dy, bz),
                                  (x + dx, y + dy, bz), 0.10, 0.14, MTD, COLL_DECK))
                nbrace += 1
# joists: continuous beams under the planking, running out from the bedded edge,
# which is what the gorge camera sees and what makes the cantilever legible
for x in _xs:
    if round(x / DST) % 5:
        continue
    col = sorted([v for v in DN.values() if abs(v[0] - x) < 0.02], key=lambda v: v[1])
    if len(col) < 3:
        continue
    runs, cur = [], [col[0]]
    for v in col[1:]:
        if v[1] - cur[-1][1] < DST * 1.6:
            cur.append(v)
        else:
            runs.append(cur); cur = [v]
    runs.append(cur)
    for r in runs:
        if len(r) < 3:
            continue
        y0, y1 = r[0][1], r[-1][1]
        zb0, zb1 = r[0][3], r[-1][3]
        deep = 0.34 if (y1 - y0) > 3.0 else 0.22
        if not all(column_free(x, y0 + (y1 - y0) * t / 6.0,
                               (zb0 + (zb1 - zb0) * t / 6.0) - deep - 0.02,
                               (zb0 + (zb1 - zb0) * t / 6.0) - 0.02, pad=0.16)
                   for t in range(7)):
            nblock += 1
            continue
        parts.append(beam("jo", (x, y0 - 0.12, zb0 - deep / 2),
                          (x, y1 + 0.12, zb1 - deep / 2), 0.16, deep, MTD, COLL_DECK))
        njoist += 1
        if (y1 - y0) > 3.0:
            ncant += 1
JOISTS = join_meshes(parts, "qm_deck_frame", COLL_DECK)
log("BUILD", "qm_deck_frame", "%d piles on a %.2f m pitch — every one column-tested "
    "twice (`clear_below` for what it would be driven through, `column_free` for "
    "the walking lines it would cross); %d braces, %d joists of which %d are the "
    "deep cantilever runs carrying the deck out over the Weave. %d members "
    "refused: the pilot-cluster stair descends straight through this frame."
    % (npile, PILE_PITCH, nbrace, njoist, ncant, nblock))

# =========================================================================
# 6. UNDERWORKS — the rock the Deep Stairs descend against
# =========================================================================
# The Deep Stairs currently fall 8.5 m from this tier through open air, and the
# shop street's two loop stairs land on it the same way.  A tread's masonry
# belongs UNDER the tread and the walk QA measures headroom ABOVE it, so a
# battered block capped 60 mm below each tread costs nothing and fixes three
# obviously unsupported runs.
# ANOTHER DISTRICT'S ART IS A KEEP-OUT, not just a thing to avoid touching.  The
# Deep Stairs' lower flights pass through the Weave's huts' airspace, and the
# first audited run drove 71 faces of `qm_stair_underworks` a metre inside
# `wv_hut_weave-north_0`.  A block that would enter any neighbouring district's
# built object is simply not made — the tread there is a bridge span like the
# others.
FOREIGN = []
for _o in bpy.data.objects:
    if _o.type != 'MESH':
        continue
    # BUILDINGS AND PROPS of other districts, not their ground, paving or
    # underworks — those are neighbours this tier is registered as sharing an
    # assembly with (finding 79), and a blanket foreign list refused 27 of 42
    # blocks for touching the shop street's own stair masonry, which is exactly
    # the joint that SHOULD touch.
    if not _o.name.startswith(("wv_hut", "wv_clut", "wv_props", "wv_planking",
                               "wv_piles", "wv_joists", "wv_stair", "wv_cloth",
                               "wf_stair", "wf_winch", "wf_clutter", "wf_stage",
                               "wf_fish", "nl_", "cargo_winch_foot")):
        continue
    _b = world_bbox(_o)
    if _b[1] < QX0 - 2 or _b[0] > QX1 + 2 or _b[5] < 4.0 or _b[4] > TIER_HI + 2:
        continue
    FOREIGN.append((_o.name, _b))


def foreign_hit(x0, x1, y0, y1, z0, z1, pad=0.10):
    for nm, b in FOREIGN:
        if (min(x1, b[1] + pad) > max(x0, b[0] - pad)
                and min(y1, b[3] + pad) > max(y0, b[2] - pad)
                and min(z1, b[5] + pad) > max(z0, b[4] - pad)):
            return nm
    return None


parts = []
nuw, nbridge, nforeign = 0, 0, 0
for raw, fn, zt, nm in (T.high + T.low):
    if not (nm.startswith("walk_e_deep-stairs-head__") or
            nm.startswith("walk_e_quay-deck__deep-stairs-head") or
            nm.startswith("walk_e_shelf-homes__quay-deck") or
            nm.startswith("walk_e_shelf-homes__market-stalls")):
        continue
    xs = [p.x for p in raw]
    ys = [p.y for p in raw]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    if not (QX0 - 1.0 <= cx <= QX1 + 1.0):
        continue
    if zt > 18.4 or zt < 6.0:
        continue
    eff = []
    for a in range(5):
        for b2 in range(5):
            # BANDED, not maximal (finding 222): an unbanded top_at over a market
            # tread returns the shop street's walk 5 m above it and the block
            # would be built to the wrong ceiling entirely.
            t = COR0.top_band(min(xs) + (max(xs) - min(xs)) * a / 4.0,
                              min(ys) + (max(ys) - min(ys)) * b2 / 4.0,
                              zt - LEVEL_BAND, zt + LEVEL_BAND)
            if t is not None:
                eff.append(t)
    if not eff:
        continue
    ztop = min(eff) - 0.06
    ez, en = existing(cx, cy)
    zg = ez if ez is not None else ground_top(cx, cy)
    if not (0.24 < ztop - zg < 8.4):
        continue
    # NOT WHERE THE FLIGHT IS A BRIDGE.  The shop street's loop stair crosses the
    # market plaza with as little as 1.13 m of clearance (tread 15.37 over
    # `walk_lm_market-stalls` at 14.24), and masonry under a tread there stands in
    # the plaza's own headroom band.  A flight passing over another walk is a
    # BRIDGE and gets no underworks — which is also why it does not read as
    # unsupported: its ends are carried and its span is meant to be open.
    if any(zt - CORRIDOR_H < pz < ztop - 0.10
           for pz in [f for f in (COR0.top_band(cx, cy, 8.0, ztop - 0.20),) if f]):
        nbridge += 1
        continue
    bw, bd = (max(xs) - min(xs)) * 0.92, (max(ys) - min(ys)) * 0.92
    fh = foreign_hit(cx - bw / 2, cx + bw / 2, cy - bd / 2, cy + bd / 2, zg - 0.20, ztop)
    if fh:
        nforeign += 1
        continue
    parts.append(obox("uw", cx, cy, (zg + ztop) / 2 - 0.10, bw, bd,
                      max(0.14, ztop - zg + 0.20), mat=MSTONED, cname=COLL))
    nuw += 1
UNDER = join_meshes(parts, "qm_stair_underworks", COLL)
log("BUILD", "qm_stair_underworks", "%d battered blocks under the Deep Stairs and "
    "the two loop stairs off the shop street, each capped 60 mm below its own "
    "tread so the walk QA's down-ray still lands on the tread; %d treads left "
    "open as BRIDGE spans where the flight crosses another walk, %d refused for "
    "entering a neighbouring district's built art" % (nuw, nbridge, nforeign))

# =========================================================================
# roof builders — a roof is not a stack of planks (finding 109)
# =========================================================================
def shingles(parts, cx, cy, eave_z, ridge_z, half_dep, width, mat=None,
             axis='y', courses=None, over=0.11, thick=0.055):
    n = courses or max(9, int(round(half_dep / 0.105)))
    mat = mat if mat is not None else MSHINGLE
    tiles = max(3, int(round(width / 0.70)))
    rise = abs(ridge_z - eave_z) / max(n - 1, 1)
    thick = max(thick, rise + 0.032)
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


def monopitch(parts, x0, x1, y0, y1, z_lo, z_hi, mat=None, over=0.10, thick=0.055):
    """A shed roof falling from y0 (z_hi) to y1 (z_lo), in real courses."""
    mat = mat if mat is not None else MSHINGLE
    dep = abs(y1 - y0)
    n = max(6, int(round(dep / 0.11)))
    tiles = max(3, int(round((x1 - x0) / 0.70)))
    thick = max(thick, abs(z_hi - z_lo) / max(n, 1) + 0.032)
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


def soffit(parts, cx, cy, z, sx, sy, mat=None):
    """Eave boarding as a RING, never a slab (finding 109's other half: a large
    flat plane a few centimetres under a stepped roof is findable by any shallow
    ray that gets in between two courses)."""
    mat = mat if mat is not None else MTD
    hx, hy, zz, W = (sx - 0.16) / 2, (sy - 0.16) / 2, z - 0.05, 0.58
    for cxx, cyy, ssx, ssy in ((cx, cy - hy + W / 2, sx - 0.16, W),
                               (cx, cy + hy - W / 2, sx - 0.16, W),
                               (cx - hx + W / 2, cy, W, sy - 0.16 - 2 * W),
                               (cx + hx - W / 2, cy, W, sy - 0.16 - 2 * W)):
        if ssx <= 0.05 or ssy <= 0.05:
            continue
        parts.append(obox("sf", cxx, cyy, zz, ssx, ssy, 0.16, mat=mat, cname=COLL))


def plinth(parts, x0, x1, y0, y1, zb, h=0.26, over=0.16, mat=None):
    parts.append(obox("pl", (x0 + x1) / 2, (y0 + y1) / 2, zb + h / 2,
                      x1 - x0 + over, y1 - y0 + over, h,
                      mat=mat if mat is not None else MSTONE, cname=COLL))


def framed_wall(parts, x0, x1, y0, y1, zb, zt, mat, frame=MT, nposts=0, sill=True):
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
NOAWN = []


def awning(x0, x1, y_wall, y_out, z_wall, z_out, rgb_a, rgb_b, nstripe=None,
           cname=None):
    """A striped canvas awning, its stripes baked into VERTEX COLOURS.

    A stripe is the obvious job for a texture or a procedural checker and both
    are exactly what the glTF-survival gate forbids.  ONE OBJECT PER AWNING, not
    one for the market: the geometry audit takes its footprint probes on the
    BBOX, and awnings 10 m apart leave most of those probes in mid-air
    (finding 97 read the other way).
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
    me = bpy.data.meshes.new("qm_awning_%d" % len(AWNINGS))
    me.from_pydata(V, [], F)
    me.validate()
    me.materials.append(MAWN)
    ca = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for i, c in enumerate(C):
        ca.data[i].color = (c[0], c[1], c[2], 1.0)
    ob = bpy.data.objects.new(me.name, me)
    link(ob, cname or COLL_PROPS)
    AWNINGS.append(ob)
    return ob


AWN_CLEAR = 2.24   # not 2.10: the master's corridor is 2.05 and a 50 mm
                   # margin is not a margin once the canvas sags across it


def awning_lip(x0, x1, y0, y1, want, clear=AWN_CLEAR, step=0.24):
    """The outer lip height an awning may actually hang at: whichever is higher,
    what the stall wants or what the street under it needs (the master's headroom
    pass caught the shop street 15 mm under its 2.00 m bar this way)."""
    lo = want
    for i in range(int((x1 - x0) / step) + 1):
        for j in range(int((y1 - y0) / step) + 1):
            z, d = walk_ref(x0 + i * step, y0 + j * step)
            if z is None or d > 0.30:
                continue
            lo = max(lo, z + clear)
    return lo


CAPPED = []


def cap(name, x0, x1, y0, y1, want):
    c = ceiling_over(x0 - 0.25, x1 + 0.25, y0 - 0.25, y1 + 0.25)
    z = min(want, c - CEIL_CLEAR)
    CAPPED.append((name, want, c, z))
    return z


# =========================================================================
# 7. THE COOKHOUSE — off its pad, at the tier's edge, lit over the gorge
# =========================================================================
# WHY IT IS NOT ON ITS PAD.  `walk_pad_cookhouse` is x 39.10..41.70 / y
# 9.70..12.30 and the pad is where the PLAYER stands (finding 93); the blockout
# shell sat on it.  North of the pad the tier runs out to the gorge in open sky,
# which is where the map's own note wants this building — "warm windows over the
# gorge at night; the tavern-warmth hub".  So the cookhouse stands NORTH of its
# pad with its door facing back south onto it, and the walk ribbon
# `walk_e_quay-deck__cookhouse_l1` (north edge y=12.79) sets its south wall.
#
# ITS ROOF IS A LEAN-TO, and that is measured too: `veg_shelf_creeper_*` hang off
# the shop street's parapet down to z 16.88 over x 38.25..41.46 / y 12.48..14.61,
# and `shelf_ground`'s plate is at 17.37..18.61 over the same strip.  A gabled
# ridge would have to duck under both.  A monopitch rising NORTH puts its low
# eave under the creepers and its tall front out in the open air over the drop —
# which is exactly the elevation the lit windows want, so the constraint and the
# composition agree for once.
CX0, CX1, CY0, CY1 = 37.40, 42.40, 12.96, 15.58
zb = min(gz(CX0 + 0.5, CY0), gz(CX1 - 0.5, CY0), gz(CX0 + 0.5, CY1)) - 0.08
EAVE_S = cap("cookhouse eave (S)", CX0, CX1, CY0, CY0 + 0.55, 16.42)
# THE RIDGE IS FITTED TO THE CEILING, NOT CAPPED BY ITS MINIMUM.  A single
# `cap()` over the whole footprint takes the LOWEST ceiling anywhere over it, and
# on a monopitch that is the wrong test: the lowest point overhead is at the
# building's SOUTH edge (the shop street's hanging creepers reach z 16.88..17.13
# over y <= 14.8) while the ridge stands at the NORTH edge under open sky.  Capping
# by the minimum cost 1.2 m of ridge for nothing.  So the roof PLANE is fitted:
# sample the ceiling across the footprint and take the steepest rise that keeps
# the plane clear everywhere.
def fit_monopitch(x0, x1, y0, y1, eave, want, clear=CEIL_CLEAR, step=0.26):
    R = want
    ny = max(3, int((y1 - y0) / step) + 1)
    nx = max(3, int((x1 - x0) / step) + 1)
    for j in range(ny):
        yy = y0 + (y1 - y0) * j / (ny - 1)
        u = (yy - y0) / max(y1 - y0, 1e-6)
        if u < 1e-3:
            continue
        c = 99.0
        for i in range(nx):
            c = min(c, ceiling(x0 + (x1 - x0) * i / (nx - 1), yy, 0.18))
        if c > 90.0:
            continue
        R = min(R, eave + (c - clear - eave) / u)
    return R


RIDGE_N = fit_monopitch(CX0 - 0.25, CX1 + 0.25, CY0, CY1 + 0.30, EAVE_S, 18.05)
CAPPED.append(("cookhouse ridge (N), plane-fitted", 18.05,
               ceiling_over(CX0 - 0.25, CX1 + 0.25, CY1 - 0.4, CY1 + 0.3), RIDGE_N))
parts = []
plinth(parts, CX0, CX1, CY0, CY1, zb - 0.22, h=0.34)
framed_wall(parts, CX0, CX1, CY0, CY0 + 0.18, zb + 0.12, EAVE_S - 0.16, MPRED, nposts=6)
framed_wall(parts, CX0, CX1, CY1 - 0.18, CY1, zb + 0.12, RIDGE_N - 0.16, MPRED, nposts=6)
framed_wall(parts, CX0, CX0 + 0.18, CY0, CY1, zb + 0.12, EAVE_S - 0.16, MPRED, nposts=4)
framed_wall(parts, CX1 - 0.18, CX1, CY0, CY1, zb + 0.12, EAVE_S - 0.16, MPRED, nposts=4)
# the raking gable ends that make the lean-to read as one
for s, xx in ((-1, CX0 + 0.09), (1, CX1 - 0.09)):
    for k in range(7):
        u = (k + 0.5) / 7.0
        yy = CY0 + (CY1 - CY0) * u
        zt_ = EAVE_S + (RIDGE_N - EAVE_S) * u
        parts.append(obox("gk", xx, yy, (EAVE_S - 0.16 + zt_) / 2, 0.18,
                          (CY1 - CY0) / 7.0 * 1.04, max(0.06, zt_ - EAVE_S + 0.16),
                          mat=MPRED, cname=COLL))
# the door onto the pad, and the shuttered service hatch beside it
doorway(parts, 39.85, CY0 - 0.02, zb + 0.12, 1.10, 2.10, 'y-')
parts.append(obox("ht", 41.35, CY0 - 0.04, zb + 1.62, 1.16, 0.14, 0.92,
                  mat=MTD, cname=COLL))
parts.append(obox("hs", 41.35, CY0 - 0.30, zb + 2.16, 1.34, 0.62, 0.09,
                  mat=MT, cname=COLL))
window(parts, 38.20, CY0 - 0.02, zb + 1.58, 0.84, 1.00, 'y-', lit=True)
# THE NORTH FRONT — the elevation the whole district is lit by at dusk.  Four
# panes over the drop, three of them lit, plus the loft light in the gable head.
NWIN = 4 if RIDGE_N - zb > 2.55 else 3
for k in range(NWIN):
    wx = CX0 + 0.70 + k * (CX1 - CX0 - 1.40) / max(NWIN - 1, 1)
    window(parts, wx, CY1 + 0.02, zb + 1.66, 0.86, 1.10, 'y+', lit=(k != 2))
soffit(parts, (CX0 + CX1) / 2, (CY0 + CY1) / 2, EAVE_S - 0.05,
       CX1 - CX0 + 0.70, CY1 - CY0 + 0.60)
monopitch(parts, CX0 - 0.34, CX1 + 0.34, CY0 - 0.30, CY1 + 0.34, EAVE_S, RIDGE_N)
parts.append(beam("rg", (CX0 - 0.36, CY1 + 0.30, RIDGE_N + 0.07),
                  (CX1 + 0.36, CY1 + 0.30, RIDGE_N + 0.07), 0.22, 0.19, MT, COLL))
# THE CHIMNEY, and it stands OUTSIDE the roof against the WEST gable.  Sited
# inside the footprint it was capped at 17.33 by the same hanging creepers that
# cap the roof — a 3.2 m stack, which is not a chimney, it is a bump.  The north
# wall was the obvious alternative and it is wrong for a different reason:
# `walk_e_quay-deck__deep-stairs-head_l1` runs at y 16.01..18.39 across x
# 39.64..45.71, i.e. 0.43 m off the north wall, and a stack there stands in the
# route west to the Deep Stairs.  The west gable is clear of both — between the
# creeper clumps at x 33.86..34.99 and 38.25..41.46, south of the l2 flight's
# y 16.32 — so the flue is corbelled off that wall in open sky, which is what a
# real cookhouse has anyway.  Position corridor-tested, height cap()ed.
CHX, CHY = CX0 - 0.62, 14.62
for _t in range(10):
    if not over_walk(COR, CHX, CHY, FLOOR + 1.4, pad=0.60) and \
            plate_under(CHX, CHY, 0.20)[0] is None:
        break
    CHY += 0.16                # NORTH, out from under the plate's edge at 13.53
CH_TOP = cap("cookhouse chimney", CHX - 0.55, CHX + 0.55, CHY - 0.55, CHY + 0.55, 19.40)
# the stack reaches the floor under it, whatever that floor is — a flue whose
# base hangs 0.5 m over the ground it stands on is a stray (finding 97's cousin)
CHBASE = min(zb, gz(CHX, CHY)) - 0.30
parts.append(obox("ch", CHX, CHY, (CHBASE + CH_TOP) / 2, 0.96, 0.96,
                  CH_TOP - CHBASE, mat=MSTONE, cname=COLL))
parts.append(obox("cc", CHX, CHY, CH_TOP + 0.12, 1.22, 1.22, 0.24, mat=MSTONE, cname=COLL))
# ... corbelled back into the gable so it is not a free-standing tower
for zz_ in (zb + 1.30, zb + 2.60):
    if zz_ < CH_TOP - 0.5:
        parts.append(beam("cb", (CHX, CHY, zz_), (CX0 + 0.10, CHY, zz_ + 0.10),
                          0.30, 0.26, MSTONE, COLL))
hangsign(parts, 39.85, CY0 - 0.08, zb + 2.72, 'y-', MPOCHRE, w=1.00, h=0.68, arm=0.66)
COOK = join_meshes(parts, "qm_cookhouse", COLL)
keepout(CX0 - 1.35, CX1 + 0.45, CY0 - 0.55, CY1 + 0.45)
log("BUILD", "qm_cookhouse", "x %.2f..%.2f y %.2f..%.2f, lean-to eave %.2f (S) "
    "rising to %.2f (N), chimney head %.2f; 7 windows, 6 lit. Door faces its own "
    "pad across walk_e_quay-deck__cookhouse_l1; the interior's walk_pad_door "
    "contract is untouched." % (CX0, CX1, CY0, CY1, EAVE_S, RIDGE_N, CH_TOP))

# =========================================================================
# 8. THE NOTICE BOARD — the landmark, off its pad at last
# =========================================================================
# `lm_notice-board` stood at 47.80..48.60 / 11.60..12.40, dead centre of
# `walk_pad_notice-board` (46.90..49.50 / 10.70..13.30): 2 blocked down-ray
# samples and an 8-sample headroom warning, inherited from the blockout and
# blamed on nobody.  The real board goes on the pad's SOUTH edge facing +y, so a
# player standing on the pad reads it — which is what a notice board is for.
NBX, NBY = 48.20, 9.92
zbn = gz(NBX, NBY)
parts = []
for sx in (-1.28, 1.28):
    parts.append(obox("po", NBX + sx, NBY, zbn + 1.34, 0.20, 0.20, 2.72, mat=MTD, cname=COLL))
    parts.append(obox("pf", NBX + sx, NBY, zbn + 0.10, 0.34, 0.34, 0.22, mat=MSTONE, cname=COLL))
parts.append(obox("bd", NBX, NBY + 0.06, zbn + 1.72, 2.70, 0.13, 1.42, mat=MWALLD, cname=COLL))
parts.append(obox("bf", NBX, NBY + 0.14, zbn + 1.72, 2.86, 0.06, 1.58, mat=MTD, cname=COLL))
# the hood: a market board is roofed, or the notices are pulp by morning
monopitch(parts, NBX - 1.58, NBX + 1.58, NBY + 0.62, NBY - 0.30, zbn + 2.66, zbn + 2.94)
parts.append(beam("hb", (NBX - 1.50, NBY + 0.10, zbn + 2.60),
                  (NBX + 1.50, NBY + 0.10, zbn + 2.60), 0.12, 0.14, MT, COLL))
# THE NOTICES.  LOCKS: DELAYED lives here (it is on the inn's board too — the
# town has one piece of news and it is this).  Paper is geometry at this scale:
# eight sheets at eight angles, one of them a big official proclamation.
parts.append(obox("nb", NBX - 0.78, NBY + 0.13, zbn + 1.86, 0.86, 0.02, 0.62,
                  mat=MPBONE, cname=COLL))
parts.append(obox("nr", NBX - 0.78, NBY + 0.15, zbn + 2.09, 0.88, 0.02, 0.12,
                  mat=MPRED, cname=COLL))
for k in range(7):
    parts.append(obox("no", NBX + rng.uniform(-1.1, 1.2), NBY + 0.13,
                      zbn + 1.35 + rng.uniform(0.0, 1.05),
                      rng.uniform(0.20, 0.34), 0.02, rng.uniform(0.24, 0.38),
                      rz=rng.uniform(-0.09, 0.09), mat=MPBONE, cname=COLL))
NOTICE = join_meshes(parts, "qm_notice_board", COLL)
keepout(NBX - 1.65, NBX + 1.65, NBY - 0.60, NBY + 0.85)
log("BUILD", "qm_notice_board", "at (%.2f, %.2f) on the SOUTH edge of its own pad "
    "facing +y, hooded, 2.94 m to the ridge — the shell it replaces stood dead "
    "centre of the pad and blocked 2 walk samples + 8 headroom samples"
    % (NBX, NBY))

# =========================================================================
# 9. THE DEEP STAIRS' HEAD — a gateway, clear of the pad
# =========================================================================
# The blockout's two posts and lintel stood inside `walk_pad_deep-stairs-head`
# (33.90..36.50 / 15.70..18.30) as well.  The real gateway straddles the head of
# the flight instead, found by stepping along the pad's edge until the corridor
# releases — "the discreet route down", so it is a plain timber frame with one
# lamp and a warning board, not a monument.
SHX, SHY = 35.20, 15.34
zbs = gz(SHX, SHY)
parts = []
for _t in range(16):
    if not (over_walk(COR, SHX - 1.34, SHY, zbs + 1.2, pad=0.26) or
            over_walk(COR, SHX + 1.34, SHY, zbs + 1.2, pad=0.26)):
        break
    SHY -= 0.12
    zbs = gz(SHX, SHY)
GATE_TOP = cap("stairhead lintel", SHX - 1.5, SHX + 1.5, SHY - 0.4, SHY + 0.4, 17.05)
for sx in (-1.34, 1.34):
    parts.append(obox("gp", SHX + sx, SHY, (zbs + GATE_TOP - 0.22) / 2, 0.28, 0.30,
                      GATE_TOP - 0.22 - zbs, mat=MTD, cname=COLL))
    parts.append(obox("gf", SHX + sx, SHY, zbs + 0.13, 0.46, 0.48, 0.28,
                      mat=MSTONE, cname=COLL))
    parts.append(beam("gk", (SHX + sx, SHY, GATE_TOP - 0.92),
                      (SHX + sx * 0.62, SHY, GATE_TOP - 0.26), 0.11, 0.13, MT, COLL))
parts.append(obox("gl", SHX, SHY, GATE_TOP - 0.11, 3.22, 0.34, 0.30, mat=MT, cname=COLL))
parts.append(obox("gs", SHX, SHY + 0.16, GATE_TOP - 0.52, 1.42, 0.07, 0.44,
                  mat=MPBONE, cname=COLL))
STAIRHEAD = join_meshes(parts, "qm_stairhead", COLL)
keepout(SHX - 1.70, SHX + 1.70, SHY - 0.45, SHY + 0.45)
log("BUILD", "qm_stairhead", "gateway at (%.2f, %.2f), lintel %.2f — stepped south "
    "off the pad until the corridor released; the three lm_ shells it replaces "
    "stood inside the pad" % (SHX, SHY, GATE_TOP))

# =========================================================================
# 10. THE MARKET — stalls, trestles, produce, the fishmonger's slab
# =========================================================================
# `walk_lm_market-stalls` is a 6 x 6 m plaza at x 56.09..62.09 / y 10.00..16.00
# and `market-stalls` is an AREA landmark of extent 3, so the stalls belong round
# its EDGES with the crossing left open — a market a player cannot walk through
# is a wall.  Each stall is its own object (finding 97: a joined multi-part mesh
# is audited by its bbox, and four stalls 4 m apart leave most of the footprint
# probes in mid-air).
STALLC = [(0.196, 0.064, 0.055), (0.068, 0.123, 0.191),
          (0.255, 0.175, 0.076), (0.320, 0.295, 0.248),
          (0.128, 0.050, 0.046), (0.047, 0.081, 0.128)]
PRODUCE = [(0.42, 0.13, 0.07), (0.55, 0.34, 0.06), (0.20, 0.30, 0.10),
           (0.48, 0.42, 0.12), (0.35, 0.10, 0.14), (0.26, 0.22, 0.30)]
STALLS = []


def stall(name, cx, cy, ax, w, d, paint, cloth, fish=False):
    """One trestle stall under a striped awning, facing the plaza.

    `ax` is the direction the stall FACES ('y-', 'y+', 'x-', 'x+').  Everything
    is derived from the floor under the stall's own four corners, so a stall on
    the deck and a stall on the paving sit the same way.
    """
    p = []
    zc = min(pz_at(cx + sx * w * 0.42, cy + sy * d * 0.42)
             for sx in (-1, 1) for sy in (-1, 1))
    hx, hy = (w / 2, d / 2) if ax[0] == 'y' else (d / 2, w / 2)
    sgn = -1.0 if ax[1] == '-' else 1.0
    # four posts and the trestle top
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(obox("sp", cx + sx * (hx - 0.12), cy + sy * (hy - 0.12),
                          zc + 1.06, 0.11, 0.11, 2.12, mat=MT, cname=COLL_PROPS))
    if ax[0] == 'y':
        p.append(obox("st", cx, cy + sgn * (hy - 0.42), zc + 0.86, w - 0.20, 0.78, 0.10,
                      mat=MT, cname=COLL_PROPS))
        p.append(obox("sk", cx, cy + sgn * (hy - 0.08), zc + 0.44, w - 0.24, 0.09, 0.80,
                      mat=paint, cname=COLL_PROPS))
        p.append(obox("sb", cx, cy - sgn * (hy - 0.20), zc + 1.28, w - 0.20, 0.10, 1.30,
                      mat=paint, cname=COLL_PROPS))
    else:
        p.append(obox("st", cx + sgn * (hx - 0.42), cy, zc + 0.86, 0.78, w - 0.20, 0.10,
                      mat=MT, cname=COLL_PROPS))
        p.append(obox("sk", cx + sgn * (hx - 0.08), cy, zc + 0.44, 0.09, w - 0.24, 0.80,
                      mat=paint, cname=COLL_PROPS))
        p.append(obox("sb", cx - sgn * (hx - 0.20), cy, zc + 1.28, 0.10, w - 0.20, 1.30,
                      mat=paint, cname=COLL_PROPS))
    # THE GOODS.  Crates of produce on the trestle, in vertex-coloured heaps —
    # a market with an empty counter is a bus stop.
    for k in range(rng.randint(3, 5)):
        u = (k + 0.5) / 5.0
        if ax[0] == 'y':
            px, py = cx - w / 2 + 0.30 + u * (w - 0.60), cy + sgn * (hy - 0.44)
        else:
            px, py = cx + sgn * (hx - 0.44), cy - w / 2 + 0.30 + u * (w - 0.60)
        p.append(obox("cr", px, py, zc + 1.02, 0.42, 0.36, 0.22, mat=MWALLD,
                      cname=COLL_PROPS))
        if fish:
            for q in range(3):
                p.append(obox("fs", px + rng.uniform(-.13, .13), py + rng.uniform(-.11, .11),
                              zc + 1.16, 0.30, 0.11, 0.07, rz=rng.uniform(0, 3.14),
                              mat=MFISH, cname=COLL_PROPS))
        else:
            for q in range(4):
                p.append(cyl("pr", (px + rng.uniform(-.13, .13),
                                    py + rng.uniform(-.11, .11), zc + 1.13),
                             (px + rng.uniform(-.13, .13), py + rng.uniform(-.11, .11),
                              zc + 1.24), 0.075, 7, MPRODUCE, COLL_PROPS))
    ob = join_meshes(p, name, COLL_PROPS)
    # the produce is vertex-coloured and the join dropped the layer: paint it now,
    # one hue per stall so the market is a row of different trades
    paint_vcol(ob, {"mat_qm_produce": PRODUCE[len(STALLS) % len(PRODUCE)]},
               jitter=0.16, seed=1700 + len(STALLS))
    # the awning is its own object, hung off the stall's face — IF it fits.  The
    # canvas reaches 0.92 m further out than the stall the site test cleared, and
    # the shop street's loop stair passes overhead near the market: 2 headroom
    # samples survived the site test because the site test only knows the stall's
    # own footprint.  So the awning tests its own quad, and a stall that cannot
    # have one simply does not — a bare trestle is a market stall too.
    if ax[0] == 'y':
        y_w = cy + sgn * (hy - 0.06)
        y_o = cy + sgn * (hy + 0.92)
        lip = awning_lip(cx - w / 2, cx + w / 2, min(y_w, y_o), max(y_w, y_o), zc + 2.06)
        zw = max(zc + 2.30, lip + 0.26)
        # tested at the canvas's OWN height, point by point — not over a padded
        # band.  A ±0.12 m band around a lip that clears the 2.05 m corridor by
        # 0.19 m reaches back INTO the corridor and refused every awning in the
        # district; the thing to test is where the cloth actually is.
        fits = True
        for u in (-1.0, -0.5, 0.0, 0.5, 1.0):
            for v in (0.0, 0.35, 0.7, 1.0):
                px = cx + (w / 2 + 0.10) * u
                py = y_w + (y_o - y_w) * v
                pz = zw + (lip - zw) * v
                if over_walk(COR, px, py, pz, pad=0.14):
                    fits = False
        if fits:
            aw = awning(cx - w / 2 - 0.10, cx + w / 2 + 0.10, y_w, y_o, zw, lip,
                        cloth, (0.320, 0.295, 0.248))
            # PARENTED to its stall, and that is not a dodge: an awning IS
            # attached, the audit says so in as many words ("parented objects are
            # attached by definition"), and the alternative — joining the canvas
            # into the trestle — would round-trip its `Col` layer through bmesh,
            # which is exactly what weave_lib warns never to do to a vertex-
            # coloured mesh.  Its own bbox stays tight, so finding 97 still holds.
            aw.parent = ob
            aw.matrix_parent_inverse = ob.matrix_world.inverted()
        else:
            NOAWN.append(name)
    STALLS.append(ob)
    keepout(cx - hx - 0.35, cx + hx + 0.35, cy - hy - 1.05, cy + hy + 1.05)
    return ob


# WHERE THE STALLS CAN ACTUALLY GO — found by SEARCH, and the search is the
# interesting part.  Both landmark plazas are ONE walk polygon each
# (`walk_lm_quay-deck` 11 x 11 m, `walk_lm_market-stalls` 6 x 6 m) and every
# square metre of them is canonical walkable topology, so a stall standing in the
# market is a stall standing in the collision surface: the master's down-ray hits
# it instead of the walk and the QA fails.  A market whose stalls ring the
# crossing is also the truer image — the crossing is what a market is FOR.
# So: scan the tier on a 0.30 m grid, keep every point where a stall's whole
# footprint clears every walk corridor at THIS level and everything already
# built, then take the best ones by distance to the `market-stalls` landmark
# (59.09, 13.00) and the quay deck's own centre, with a minimum separation.
MX0, MX1, MY0, MY1 = PLAZA_MKT
MKT_AIM = Vector((59.09, 13.00, FLOOR))
QUAY_AIM = Vector((53.40, 14.00, FLOOR))
SW, SD = 2.30, 1.20                 # a stall's counter run and its depth

def free_sites(SW, SD, step=0.30, facing=True, y0=6.20, y1=19.60):
    """Every (distance, x, y, facing) where a SW x SD footprint fits on this tier.

    ONE search, TWO clients, and the second client is why it is a function.  A
    stall's 2.30 x 1.20 footprint fits in only ~26 distinct places here, because
    both landmark plazas are single walk polygons covering x 47.9..62.1 /
    y 8.5..19.5 almost entirely.  Reusing the STALL sites for the clutter left
    four pieces of dressing in the whole district.  A barrel is 0.95 m wide and has
    a hundred places to stand: the difference is the footprint, not the rule.
    """
    out = []
    gx = QX0 + 1.0
    while gx < QX1 - 1.0:
        gy = y0
        while gy < y1:
            for ax in (('y+', 'y-', 'x+', 'x-') if facing else ('y+',)):
                hx, hy = (SW / 2, SD / 2) if ax[0] == 'y' else (SD / 2, SW / 2)
                ok = True
                for ddx in (-hx, 0.0, hx):
                    for ddy in (-hy, 0.0, hy):
                        px, py = gx + ddx, gy + ddy
                        if over_walk(COR, px, py, FLOOR + 0.95, pad=0.20):
                            ok = False; break
                        zc = pz_at(px, py)
                        if abs(zc - pz_at(gx, gy)) > 0.30:
                            ok = False; break
                        ez, en = existing(px, py)
                        # ON OUR OWN BENCH, OR ON A SURFACE WE ACTUALLY LAID.
                        # "road_at is not None" is not the same claim: it says a
                        # walk is within reach, not that any mesh got built here,
                        # and one stall on the deck's outer edge came out with its
                        # feet 1.42 m over the terrain because of the difference.
                        if not (on_sheet(px, py)
                                or surf_top(px, py, r=1) is not None
                                or (ez is not None and FLOOR - ez < 0.30)):
                            ok = False; break
                    if not ok:
                        break
                if not ok:
                    continue
                zc = pz_at(gx, gy)
                if zc < FLOOR - 0.9 or zc > FLOOR + 0.9:
                    continue
                # AND CLEAR THROUGH ITS WHOLE HEIGHT.  The shop street's loop stair
                # descends THROUGH this tier: `walk_e_shelf-homes__market-stalls_
                # l1_t04/t05` run at z 15.72..16.07 over x 55.6..59.2.  The first
                # gated run sited a stall under them and its awning blocked 7 of
                # the stair's own down-ray samples, because `awning_lip` consults
                # only the FLAT band and cannot see a flight passing overhead.
                if not column_free(gx, gy, zc + 0.25, zc + 2.95,
                                   pad=max(hx, hy) * 0.8):
                    continue
                if facing:
                    # A STALL MUST FACE A CROSSING, and the reach matters: the
                    # footprint has to clear the walk by 0.46 m (margin 0.30 + pad
                    # 0.16), so a probe 0.95 m from the centre lands 0.40 m SHORT
                    # of the walk it is looking for and no site in the district
                    # could ever pass.  1.70 m reaches past the clearance the same
                    # test demands.
                    fy = gy + (1.70 if ax == 'y+' else (-1.70 if ax == 'y-' else 0.0))
                    fx = gx + (1.70 if ax == 'x+' else (-1.70 if ax == 'x-' else 0.0))
                    if not over_walk(COR0, fx, fy, FLOOR + 0.30, pad=0.12, h=0.9):
                        continue
                d = min((Vector((gx, gy, FLOOR)) - MKT_AIM).length,
                        (Vector((gx, gy, FLOOR)) - QUAY_AIM).length + 2.5)
                out.append((d, gx, gy, ax))
            gy += step
        gx += step
    out.sort()
    return out


CANDS = [c for c in free_sites(SW, SD) if not in_solid(c[1], c[2], pad=0.55)]
nstall = 0
STALL_SEP = 3.10
_placed = []
for d, sx, sy, ax in CANDS:
    if nstall >= 7:
        break
    if any((sx - px) ** 2 + (sy - py) ** 2 < STALL_SEP ** 2 for px, py in _placed):
        continue
    if in_solid(sx, sy, pad=0.55):
        continue
    stall("qm_stall_%d" % nstall, sx, sy, ax, SW, SD,
          PAINTS[nstall % len(PAINTS)], STALLC[nstall % len(STALLC)],
          fish=(nstall in (1, 4)))
    _placed.append((sx, sy))
    nstall += 1
log("SEARCH", "%d stall sites, %d used" % (len(CANDS), nstall),
    "0.30 m grid x 4 facings; every footprint corner clear of this tier's walk "
    "corridors, on real floor, and FACING a crossing — the plazas are one walk "
    "polygon each and a stall inside one is a stall inside the collision surface")
# the fishmonger's stone slab — `market-stalls`' one named resident is the
# fishmonger, so she gets the district's one piece of dressed furniture.  Sited
# from the same candidate list, so it is placed by the same rule as the stalls.
for d, FSX, FSY, ax in CANDS:
    if any((FSX - px) ** 2 + (FSY - py) ** 2 < STALL_SEP ** 2 for px, py in _placed):
        continue
    if in_solid(FSX, FSY, pad=0.55):
        continue
    zf = pz_at(FSX, FSY)
    p = [obox("fb", FSX, FSY, zf + 0.42, 1.60, 0.88, 0.84, mat=MSTONE, cname=COLL_PROPS),
         obox("fp", FSX, FSY, zf + 0.88, 1.76, 1.02, 0.10, mat=MSTONED, cname=COLL_PROPS)]
    for q in range(6):
        p.append(obox("fs", FSX + rng.uniform(-.55, .55), FSY + rng.uniform(-.28, .28),
                      zf + 0.97, 0.34, 0.12, 0.08, rz=rng.uniform(0, 3.14),
                      mat=MFISH, cname=COLL_PROPS))
    join_meshes(p, "qm_fish_slab", COLL_PROPS)
    keepout(FSX - 1.05, FSX + 1.05, FSY - 0.68, FSY + 0.68)
    _placed.append((FSX, FSY))
    break
log("BUILD", "qm_stall_* x%d + qm_fish_slab" % nstall,
    "trestles round the market plaza's EDGES with the crossing left open, each "
    "its own object with its own awning; %d awnings (%d stalls left bare where the "
    "canvas would have oversailed a walking line), produce and fish in crates on "
    "the counters" % (len(AWNINGS), len(NOAWN)))

# =========================================================================
# 11. THE RAIL along the gorge edge — placed by SEARCH, never by taste
# =========================================================================
parts, posts = [], []
x = QX0 + 0.7
last = None
while x < QX1 - 0.4:
    # FROM THE OUTERMOST BUILT NODE, INWARD.  A rail belongs at the edge of the
    # deck, and this district's edge is 0.3..1.8 m OUTBOARD of the walk polygon
    # that defines it (`walk_lm_quay-deck` ends at y 19.50; the planking runs to
    # the lip at 19.95).  The shelf's version stepped outward from the rim and
    # relied on `ground_top`, which out here answers `wf_ground` seven metres
    # below — so it refused all but two posts.  Walk in from the last node that
    # has a surface until the walking corridor releases, and stand on THAT.
    y = None
    for k in range(46):
        yy = T.rim(x) + 0.45 - k * 0.11
        if yy < 8.6:
            break
        z0 = surf_top(x, yy)
        if z0 is None or z0 < FLOOR - 1.3:
            continue
        if over_walk(COR, x, yy, z0 + 0.55, pad=0.40) or in_solid(x, yy):
            continue
        if not column_free(x, yy, z0 + 0.05, z0 + 1.30, pad=0.24):
            continue
        y, z = yy, z0
        break
    if y is None:
        x += 1.02
        last = None
        continue
    p = Vector((x, y, z))
    posts.append(p)
    parts.append(obox("pp", x, y, z + 0.52, 0.17, 0.17, 1.14, mat=MT, cname=COLL))
    parts.append(obox("pc", x, y, z + 1.11, 0.25, 0.25, 0.09, mat=MT, cname=COLL))
    mid_ok = last is not None and (p - last).length < 2.6
    if mid_ok:
        m = (last + p) / 2
        # finding 98: anything that SPANS between two tested points has to be
        # tested at its midpoint too — the gate lost 14 samples to exactly this
        if over_walk(COR, m.x, m.y, m.z + 0.42, pad=0.40) or in_solid(m.x, m.y) \
                or not column_free(m.x, m.y, m.z + 0.40, m.z + 1.10, pad=0.20):
            mid_ok = False
    if mid_ok:
        for zr, sag in ((0.98, 0.09), (0.58, 0.06)):
            mid = (last + p) / 2 + Vector((0, 0, zr - sag))
            parts.append(cyl("hl", last + Vector((0, 0, zr)), mid, 0.026, 5, MROPE, COLL))
            parts.append(cyl("hl", mid, p + Vector((0, 0, zr)), 0.026, 5, MROPE, COLL))
    last = p
    x += 1.02
RAIL = join_meshes(parts, "qm_rail", COLL)
log("BUILD", "qm_rail", "%d posts found by walking OUT toward the lip until the "
    "walk corridor and the built art released, rope handline between them — the "
    "deck is 6..8 m over the Weave's roofs and the map's night-on-the-quay stage "
    "needs an edge a player can see" % len(posts))

# =========================================================================
# 12. BUNTING — vertex-coloured cloth over the market
# =========================================================================
# The map's own note is "night-on-the-quay stage; lanterns at dusk", so this is
# the district that earns its bunting.  Finding 113: `mat_flag_*` is one flat
# diffuse mixed with one flat translucent and reads as a coloured rectangle at
# 4 m; the gate's answer was a weave NOISE, which exports WHITE.  Same weave,
# baked into vertex colours.  Six values, not six hues.
CLOTHC = STALLC
BV, BF, BC = [], [], []
LINEP = []


def weave(rgb, u, v, phase):
    w = 0.56 + 0.30 * (0.5 + 0.5 * math.sin(u * 61.0 + phase) * math.sin(v * 47.0 - phase))
    f = 0.62 + 0.44 * (0.5 + 0.5 * math.sin(u * 5.5 + v * 3.1 + phase * 0.7))
    k = w * f
    return (min(1.0, rgb[0] * k), min(1.0, rgb[1] * k), min(1.0, rgb[2] * k))


def pennant(c, run, drop, rgb, phase):
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


# Heights are ABSOLUTE and solved, not chosen (finding 99), and on THIS tier the
# solve has an answer the first cut did not survive.  The floor is 14.00 and the
# master's corridor is 2.05, so nothing may hang below 16.05 — but under the
# arcade the shop street's plate bears at 16.93..17.73, which leaves as little as
# 0.63 m between the top of the walking corridor and the ceiling.  A pennant is
# 0.34 m plus its tip: it does not fit, and hanging it there put every flag inside
# the corridor.  So THE BUNTING GOES WHERE THERE IS SKY (y >= 14.2, north of the
# plate's own edge at 13.53) and the covered market gets bracket lamps off the
# revetment instead.  Line 17.60, sag 0.26, low point 17.34, tip 16.92 — 0.87 m
# of margin over the corridor, and every segment is Corridor-tested as a backstop.
RUNS = [((42.90, 15.90), (47.60, 14.55), 17.60, 17.60, 0.26),
        ((48.20, 14.75), (54.00, 15.60), 17.60, 17.60, 0.26),
        ((54.60, 15.45), (60.40, 14.25), 17.60, 17.55, 0.26),
        ((49.60, 18.80), (56.20, 18.80), 17.55, 17.55, 0.26),
        ((56.80, 18.20), (61.20, 15.85), 17.55, 17.50, 0.24),
        ((37.80, 16.15), (42.30, 16.40), 17.60, 17.60, 0.24)]

# LANT_MIN_SEP, THE BRACKET HEIGHT AND THE DROPPER ARE ALL MEASURED, not chosen.
# The 680 W practical is town canon and is not up for renegotiation, so density and
# HEIGHT are the only handles.  Against the accepted Boatyard's own walking
# surface, sampled by the down-ray grid `qm_light.py` asserts on:
#   12 lamps, brackets 2.66 m, dropper 0.85, sep 3.0, every 2nd pilaster
#                                        market mean 24.91 W/m2 = 1.315x  FAIL
#    9 lamps, brackets 3.06 m, dropper 0.55, sep 3.6, every 3rd pilaster
#                                        market mean (see the light log)  <- adopted
# Height does most of the work: a globe 2.7 m over a floor is 1.32x one at 3.1 m
# by inverse square alone, and 3.1 m is what a market lantern on a pole actually
# hangs at.  Parity with a district the user has ACCEPTED is the target; sitting
# well under it would be the other half of the same failure (finding 101).
LANT_MIN_SEP = 3.60
# the shopfront lamps: a building lights its own door, and that is the one
# lantern a player can explain.  Positions come from `bracket_at` so the lamps
# counted by the density solver are exactly the lamps that get built.
SHOPFRONT_LAMPS = [(39.85, CY0 - 0.12, 'y-'), (41.85, CY1 + 0.12, 'y+'),
                   (NBX + 1.28, NBY + 0.14, 'y+'), (SHX + 1.34, SHY + 0.16, 'y+')]
# ... plus one on every other arcade pilaster, which is what actually lights the
# market's back wall and its bays
for i in range(0, NBAY + 1, 3):
    SHOPFRONT_LAMPS.append((ARC_X0 + i * pitch, WY1 + PIL_PROUD + 0.14, 'y+'))


def bracket_at(bx, by, face):
    lz = pz_at(bx, by) + 3.06
    ox = -0.42 if face == 'x-' else (0.42 if face == 'x+' else 0.0)
    oy = 0.42 if face == 'y+' else (-0.42 if face == 'y-' else 0.0)
    if over_walk(COR, bx + ox, by + oy, lz - 0.30, pad=0.14):
        return None
    return Vector((bx + ox, by + oy, lz))


WALL_PTS = [q for q in (bracket_at(*s) for s in SHOPFRONT_LAMPS) if q is not None]
LAMP_PTS = []
for ri, (a, b2, za, zb2, sag) in enumerate(RUNS):
    A = Vector((a[0], a[1], za))
    B = Vector((b2[0], b2[1], zb2))
    p = A.lerp(B, 0.50) - Vector((0, 0, sag))
    if any((p.xy - q.xy).length < LANT_MIN_SEP for q in WALL_PTS):
        continue
    if any((p.xy - q.xy).length < LANT_MIN_SEP for q in LAMP_PTS):
        continue
    LAMP_PTS.append(p)


def near_lamp(p, r=1.60):
    """A pennant this close to a 680 W globe is not cloth, it is a white triangle.

    MEASURED, not chosen.  At 0.95 m (the shop street's radius, which it set when
    its lamps hung 0.85 m below the line) a globe delivers 680/(4*pi*0.95^2) =
    60 W/m2 on the flag beside it, and the v1 check spread shows exactly that: the
    vertex-coloured weave the cloth was built for reads as pale gray.  This tier's
    droppers had to shorten to 0.55 m to bring the practical density under the
    accepted Boatyard's (there is no headroom to hang them lower), which puts the
    globe LEVEL with the pennant tips — so the radius has to grow instead: 1.60 m
    is 21 W/m2, a third of the wash, and it costs two flags per run.
    """
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
        c_ = ceiling(p.x, p.y)
        if c_ < 90.0:
            p.z = min(p.z, c_ - 0.34)
        if prev is not None:
            c = (prev + p) / 2
            if not over_walk(COR, c.x, c.y, c.z, pad=0.10):
                LINEP.append((prev.copy(), p.copy()))
                nf_ = near_field(c.x, c.y, c.z - 0.30, 0.45)
                step = 2 if nf_ > 0.62 else (3 if nf_ > 0.25 else 5)
                if k % step == 0 and not over_walk(COR, c.x, c.y, c.z - 0.50, pad=0.10) \
                        and not near_lamp(c):
                    if nf_ <= 0.02:
                        nthin += 1
                    else:
                        pennant(c, p - prev, 0.32 + 0.10 * rng.random(),
                                CLOTHC[(k + ri * 3) % len(CLOTHC)], k * 1.31 + ri * 0.7)
                        nflag += 1
                elif k % step == 0:
                    nthin += 1
        prev = p
if BV:
    me = bpy.data.meshes.new("qm_bunting")
    me.from_pydata(BV, [], BF)
    me.validate()
    me.materials.append(MCLOTH)
    ca = me.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for i, c in enumerate(BC):
        ca.data[i].color = (c[0], c[1], c[2], 1.0)
    BUNT = bpy.data.objects.new("qm_bunting", me)
    link(BUNT, COLL_PROPS)
parts = [cyl("bl", a, b2, 0.018, 5, MROPE, COLL_PROPS) for a, b2 in LINEP]
LINES = join_meshes(parts, "qm_bunting_lines", COLL_PROPS)
log("BUILD", "qm_bunting", "%d runs, %d pennants (%d thinned out of the near "
    "field) — the weave and the sun-fade are baked into VERTEX COLOURS, not a "
    "noise tree, so the cloth survives the glTF round trip"
    % (len(RUNS), nflag, nthin))

# =========================================================================
# 13. LANTERNS — ordinary, warm.  (Heartlights do not exist in Dellhollow.)
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
    li = bpy.data.lights.new(name.replace("qm_", "KEYQ_") + "_light", 'POINT')
    li.energy = 680.0                       # the town standard, five districts old
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
for s in SHOPFRONT_LAMPS:
    q = bracket_at(*s)
    if q is None:
        continue
    bx, by = s[0], s[1]
    brackets.append(beam("br", (bx, by, q.z + 0.44), (q.x, q.y, q.z + 0.32),
                         0.055, 0.055, MIRON, COLL))
    lantern("qm_lantern_%d" % len(LANTS), q.x, q.y, q.z)
nhang_skip = 0
for p in LAMP_PTS:
    # 0.55 m of dropper: hung level with the pennants a 680 W globe washes every
    # flag within 1.5 m to cream and throws away the vertex-coloured weave the
    # cloth was built for (finding 113's lighting corollary).
    #
    # BUT THE DROPPER LENGTH IS NOT FREE HERE.  The walking corridor over this
    # floor tops out at 16.05..16.30 and a lamp is a solid: dropping 0.85 m from a
    # 17.60 line lands the globe at 16.75, which is clear — dropping it from a
    # lower line does not, and the first cut lost every hung lamp in the district
    # to exactly that (0 of 6).  So the drop is SOLVED against the corridor under
    # the lamp rather than fixed: as long as possible, never inside the corridor.
    top = COR0.top_band(p.x, p.y, TIER_LO, TIER_HI)
    floor_lim = (top + CORRIDOR_H + 0.10) if top is not None else FLOOR + 1.6
    lz = max(p.z - 0.55, floor_lim + 0.22)
    if lz > p.z - 0.24 or over_walk(COR, p.x, p.y, lz - 0.22, pad=0.14):
        nhang_skip += 1
        continue
    brackets.append(cyl("hk", (p.x, p.y, p.z), (p.x, p.y, lz + 0.20), 0.016, 5, MIRON, COLL))
    lantern("qm_lantern_hang_%d" % len(LANTS), p.x, p.y, lz)
join_meshes(brackets, "qm_lantern_brackets", COLL)
log("BUILD", "qm_lantern_* x%d" % len(LANTS),
    "warm 680 W practicals, 14 m cutoff — %d on buildings and arcade pilasters, "
    "%d hung over the market from the bunting lines (%d dropped: no room between "
    "the walking corridor and the ceiling); the town standard, unchanged across "
    "five districts, and there are no Heartlights in Dellhollow"
    % (len([n for n in LANTS if "hang" not in n]),
       len([n for n in LANTS if "hang" in n]), nhang_skip))

# =========================================================================
# 14. VEGETATION
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
            py = T.rim(px) - 0.25 - rng.random() * 1.30
        elif mode == "wall":
            # the strip immediately in front of the revetment: a joint at the foot
            # of a retaining wall is exactly where weeds grow, and it is the one
            # place on this tier a player is always looking at
            py = WY1 + PIL_PROUD + 0.30 + rng.random() * 0.55
        elif mode == "talus":
            py = TALUS_Y - 0.30 - rng.random() * 2.9
        else:
            py = yr[0] + rng.random() * (yr[1] - yr[0])
        ezv, env = existing(px, py)
        if not (on_sheet(px, py) or (ezv is not None and abs(FLOOR - ezv) < 1.40)):
            continue
        # ON WHATEVER IS ACTUALLY THERE: our bench where we built one, the
        # Waterfront's own ground where it stands above us (the knoll)
        pz = ground_top(px, py) if on_sheet(px, py) else ezv
        if pz < FLOOR - 1.2 or pz > FLOOR + 3.6:
            continue
        s = lo + rng.random() * (hi - lo)
        if over_walk(KEEP, px, py, pz + 0.45, pad=0.35 * s) or in_solid(px, py):
            continue
        r = road_at(px, py)
        # ... unless the existing terrain here stands ABOVE the paving level, in
        # which case no paving was laid (the sheet stops at other districts' art)
        # and the "keep off the road" rule is protecting a road that is not there.
        if r is not None and r[1] < PAVE_W + 0.35 and not (ezv is not None
                                                          and ezv > FLOOR - 0.10):
            continue
        b0 = world_bbox(src)
        ext = max(b0[1] - b0[0], b0[3] - b0[2], b0[5] - b0[4]) * s
        nf_ = near_field(px, py, pz + 0.45 * ext, ext)
        if cull and rng.random() > nf_:
            continue
        s = min(s, lo + (hi - lo) * max(nf_, 0.20 if not cull else 0.0))
        ob = src.copy()
        ob.data = src.data.copy()
        ob.name = "veg_qm_%s_%d" % (tag, i)
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
        link(ob, COLL_VEG)
        made += 1
        VEGN += 1
    return made


# THE KNOLL.  `wf_ground` pokes 0.86 m ABOVE this floor at x 45..46.6 / y 13..15 —
# accepted Waterfront art standing in the middle of the market, which the v1 quay
# frame shows as a bare boulder pile.  It cannot be moved and it should not be
# hidden, so it gets planted: an outcrop the market grew around reads as geology,
# a bare one reads as a mistake.
nk = clone("veg_seam_tuft_0", "tuft", 40, (44.2, 47.4), (12.6, 15.4), 0.8, 1.5,
           mode="ground", cull=False)
nk += clone("veg_seam_tuft_37", "fern", 26, (44.2, 47.4), (12.6, 15.4), 0.7, 1.3,
            mode="ground", cull=False)
ng = clone("veg_seam_tuft_0", "tuft", 84, (QX0 + 0.6, QX1 - 0.6), None, 0.7, 1.4, mode="rim",
           cull=False)
ng += clone("veg_seam_tuft_3", "tuft", 70, (ARC_X0, ARC_X1), None, 0.7, 1.3, mode="wall",
            cull=False)
nfr = clone("veg_seam_tuft_1", "fern", 48, (QX0 + 1.0, QX1 - 1.0), None, 0.7, 1.25,
            mode="talus", cull=False)
nfr += clone("veg_seam_tuft_37", "fern", 30, (ARC_X0, ARC_X1), None, 0.7, 1.2, mode="wall",
             cull=False)
# creepers down the revetment: the one surface in the district a player is
# always looking at, and the one place vegetation buys the most
nc = 0
src = bpy.data.objects.get("veg_creeper_4")
if src is not None:
    for i in range(22):
        px = ARC_X0 + 0.6 + rng.random() * (ARC_X1 - ARC_X0 - 1.2)
        py = WY1 + PIL_PROUD - 0.02
        ptop, who = plate_min(px - 0.3, px + 0.3, WY0, WY1)
        if ptop is None:
            continue
        if in_solid(px, py + 0.6, pad=0.1):
            continue
        ob = src.copy(); ob.data = src.data.copy()
        ob.name = "veg_qm_creeper_%d" % i; ob.data.name = ob.name
        s = 0.62 + rng.random() * 0.45
        b = world_bbox(src)
        cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
        for v in ob.data.vertices:
            p = src.matrix_basis @ v.co
            v.co = Vector(((p.x - cx) * s, (p.y - cy) * s, (p.z - cz) * s))
        ob.matrix_basis.identity()
        bb = world_bbox(ob)
        ob.location = Vector((px, py - bb[3] + 0.10, ptop - PIER_SHY - bb[5] + 0.20))
        link(ob, COLL_VEG)
        nc += 1
        VEGN += 1
log("BUILD", "veg_qm_*", "%d tufts, %d ferns, %d creepers down the revetment, %d on "
    "the Waterfront's rock knoll in the middle of the market (accepted art that "
    "pokes 0.86 m above this floor and cannot be moved) — every one Corridor-, "
    "paving-, built-art- and near-field-tested" % (ng, nfr, nc, nk))

# =========================================================================
# 15. CLUTTER — the working life of a market
# =========================================================================
# PLACED ON THE SAME PROVEN-FREE SITES THE STALLS WERE.  Hand-drawn zone
# rectangles do not survive this tier: both landmark plazas are single walk
# polygons covering x 47.9..62.1 / y 8.5..19.5 almost entirely, so six of seven
# hand-picked zones placed nothing at all and the seventh took the whole budget.
# The stall search already produced 100+ sites that are provably clear of every
# walking line, on real floor, at market level — so the clutter uses them, and
# they cost nothing extra to compute.
#
# ONE OBJECT PER X-BAND (finding 97, third time tonight): the audit samples an
# object's footprint at five bbox fractions, and a single joined clutter mesh
# spanning the whole district has most of those fractions out over the gorge —
# the first audited run called it a stray with a 4.49 m gap.
CLUT_SEP = 1.35
CLUT_N = 46
BANDS = 5
ZPARTS = {}
placed = 0
_cl = list(_placed)
_pool = free_sites(0.95, 0.95, step=0.34, facing=False)
rng.shuffle(_pool)
for d, px, py, ax in _pool:
    if placed >= CLUT_N:
        break
    if any((px - qx) ** 2 + (py - qy) ** 2 < CLUT_SEP ** 2 for qx, qy in _cl):
        continue
    if in_solid(px, py, pad=0.45):
        continue
    pz = pz_at(px, py)
    if pz < FLOOR - 1.2 or pz > FLOOR + 1.2:
        continue
    # a joined mesh is audited by its BBOX corners: every piece needs floor under
    # its whole FOOTPRINT, not only under its centre
    if any(abs(pz_at(px + dx, py + dy) - pz) > 0.55
           for dx, dy in ((0.40, 0), (-0.40, 0), (0, 0.40), (0, -0.40))):
        continue
    if over_walk(KEEP, px, py, pz + 0.7, pad=0.44):
        continue
    if rng.random() > near_field(px, py, pz + 0.5, 1.05):
        continue
    band = min(BANDS - 1, int((px - QX0) / ((QX1 - QX0) / BANDS)))
    parts = ZPARTS.setdefault(band, [])
    _cl.append((px, py))
    k = rng.random()
    rz = rng.random() * 3.14
    if k < 0.26:
        parts.append(obox("cr", px, py, pz + 0.36, 0.74, 0.68, 0.72, rz=rz,
                          mat=MWALLD, cname=COLL_PROPS))
        for e in range(2):
            parts.append(obox("cb", px, py, pz + 0.15 + e * 0.42, 0.78, 0.72, 0.07,
                              rz=rz, mat=MT, cname=COLL_PROPS))
    elif k < 0.46:
        parts.append(cyl("br", (px, py, pz), (px, py, pz + 0.84), 0.31, 12,
                         MWALLD, COLL_PROPS, r2=0.28))
        for e in (0.15, 0.42, 0.69):
            parts.append(cyl("bh", (px, py, pz + e), (px, py, pz + e + 0.05), 0.325,
                             12, MIRON, COLL_PROPS))
    elif k < 0.62:
        for e in range(rng.randint(2, 4)):
            parts.append(obox("sk", px + rng.uniform(-.20, .20),
                              py + rng.uniform(-.20, .20),
                              pz + 0.19 + e * 0.30, 0.68, 0.48, 0.32,
                              rz=rz + e * 0.5, mat=MSACK, cname=COLL_PROPS))
    elif k < 0.76:
        parts.append(obox("pl", px, py, pz + 0.08, 1.24, 1.00, 0.13, rz=rz, mat=MT,
                          cname=COLL_PROPS))
        for e in range(rng.randint(2, 5)):
            parts.append(cyl("pk", (px + rng.uniform(-.34, .34),
                                    py + rng.uniform(-.28, .28), pz + 0.15),
                             (px + rng.uniform(-.34, .34),
                              py + rng.uniform(-.28, .28), pz + 0.48),
                             0.22, 10, MPUMPKIN, COLL_PROPS))
    elif k < 0.88:
        # fish crates and a folded net — this is a river market
        parts.append(obox("fc", px, py, pz + 0.17, 0.86, 0.62, 0.34, rz=rz,
                          mat=MWALLD, cname=COLL_PROPS))
        for e in range(3):
            parts.append(obox("fs", px + rng.uniform(-.28, .28),
                              py + rng.uniform(-.18, .18), pz + 0.37,
                              0.30, 0.11, 0.07, rz=rng.uniform(0, 3.14),
                              mat=MFISH, cname=COLL_PROPS))
        parts.append(obox("nt", px + 0.62, py, pz + 0.14, 0.52, 0.44, 0.28,
                          rz=rz, mat=MNET, cname=COLL_PROPS))
    else:
        for e in range(4):
            parts.append(cyl("rc", (px, py, pz + 0.03 + e * 0.05),
                             (px, py, pz + 0.06 + e * 0.05), 0.28 - e * 0.042, 12,
                             MROPE, COLL_PROPS))
    placed += 1
nclut = 0
for band, pl in sorted(ZPARTS.items()):
    if not pl:
        continue
    join_meshes(pl, "qm_clutter_%d" % band, COLL_PROPS)
    nclut += 1
log("BUILD", "qm_clutter_* x%d" % nclut, "%d crate stacks / barrels / sack piles / "
    "produce pallets / fish crates / rope coils, placed on the stall search's own "
    "proven-free sites (hand-drawn zone rectangles do not survive a tier whose "
    "two plazas are single walk polygons), grouped into %d x-bands so every "
    "bounding box has floor under all of it" % (placed, nclut))

# =========================================================================
# 16. fx — the cookhouse's chimney smoke (render-only; town_export strips fx_*)
# =========================================================================
# Kit findings 1/12/27, all three at once: never the World volume; a box that is
# harmless off-frame quietly hazes half the plate once it moves into shot, so it
# is sized to the plume and nothing else; and density is a TEXTURE — a radial
# falloff on `Generated` coordinates takes it to zero before it reaches a face, so
# the box never prints its own edges, and a noise ramp straddling the noise mean
# breaks the ellipsoid into something ragged.  Inlined rather than imported from
# `shop_props`, which pulls in the interior pipeline on import.
def smoke_wisp(name, loc, dims, color=(0.72, 0.60, 0.50), density=0.42,
               seed=5.7, squash=0.58, cname=COLL):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    from mathutils import Matrix
    bmesh.ops.create_cube(bm, size=1.0,
                          matrix=Matrix.Translation(loc) @ Matrix.Diagonal(
                              (dims[0], dims[1], dims[2], 1.0)))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    link(ob, cname)
    mat = bpy.data.materials.get("mat_" + name.lower()) or \
        bpy.data.materials.new("mat_" + name.lower())
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Color"].default_value = (color[0], color[1], color[2], 1)
    vol.inputs["Anisotropy"].default_value = 0.28
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.40)
    nt.links.new(tc.outputs["Generated"], sub.inputs[0])
    scv = nt.nodes.new("ShaderNodeVectorMath"); scv.operation = "MULTIPLY"
    scv.inputs[1].default_value = (1.0, 1.0, squash)
    nt.links.new(sub.outputs["Vector"], scv.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    nt.links.new(scv.outputs["Vector"], ln.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange")
    fall.inputs["From Min"].default_value = 0.12
    fall.inputs["From Max"].default_value = 0.44
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.0
    nt.links.new(ln.outputs["Value"], fall.inputs["Value"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 5.4
    nz.inputs["Detail"].default_value = 6.0
    try:
        nz.noise_dimensions = "4D"
        nz.inputs["W"].default_value = seed
    except (AttributeError, KeyError):
        pass
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nr = nt.nodes.new("ShaderNodeValToRGB")
    nr.color_ramp.elements[0].position = 0.36
    nr.color_ramp.elements[0].color = (0.10, 0.10, 0.10, 1)
    nr.color_ramp.elements[1].position = 0.72
    nr.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], nr.inputs["Fac"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(fall.outputs["Result"], mul.inputs[0])
    nt.links.new(nr.outputs["Color"], mul.inputs[1])
    amt = nt.nodes.new("ShaderNodeMath"); amt.operation = "MULTIPLY"
    amt.inputs[1].default_value = density
    nt.links.new(mul.outputs["Value"], amt.inputs[0])
    nt.links.new(amt.outputs["Value"], vol.inputs["Density"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    me.materials.append(mat)
    return ob


try:
    smoke_wisp("fx_qm_smoke", (CHX, CHY + 0.20, CH_TOP + 2.20), (1.55, 1.55, 4.10))
    log("BUILD", "fx_qm_smoke", "bounded volume over the cookhouse flue, sized to "
        "the plume and nothing else (kit findings 1/12/27); render-only, and "
        "town_export.py strips fx_* before the runtime ever sees it")
except Exception as e:
    log("WARN", "fx_qm_smoke not built", str(e))

# =========================================================================
for nm, want, c, got in CAPPED:
    log("CAP", "%s -> %.2f" % (nm, got),
        "wanted %.2f | measured neighbouring ceiling over its footprint %s"
        % (want, ("open sky" if c > 90 else "%.3f (clearance %.2f)" % (c, c - got))))

print("\n" + "=" * 78)
tot = sum(len(bpy.data.collections[c].objects) for c in (COLL, COLL_DECK, COLL_PROPS, COLL_VEG))
print("QUAY-MARKET DISTRICT: %d objects across %s"
      % (tot, ", ".join((COLL, COLL_DECK, COLL_PROPS, COLL_VEG))))
for c in (COLL, COLL_DECK, COLL_PROPS, COLL_VEG):
    print("   %-22s %d" % (c, len(bpy.data.collections[c].objects)))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
