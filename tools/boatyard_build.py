"""boatyard_build.py — build the del-boatyard district at TRUE TOWN COORDINATES.

Run headless:
  /Applications/Blender.app/Contents/MacOS/Blender -b \
      tools/blends/dellhollow-town.blend -P tools/boatyard_build.py

Starting from the town blockout guarantees the walk_* collision meshes are the
authored originals, bit for bit — nothing is re-authored, only pruned to the
parcel region and render-hidden.  Everything visible is built AROUND them.

Writes tools/blends/districts/boatyard.blend.
"""

import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
import importlib
import boatyard_lib as L
importlib.reload(L)
from boatyard_lib import (REPO, PROBE_BLEND, KITLIB_BLEND, REGION, R90, T_YARD,
                          WATER_MID, WATER_UP, coll, link, new_mesh, join_meshes,
                          box, obox, beam, cyl, offset_poly, point_in_poly,
                          plane_z_fn, plank_fill, harvest, M, world_bbox,
                          group_bbox, bake_group, move_group, anchor_group, place,
                          Corridor, clip_halfplane, dist_poly2)

OUT_BLEND = REPO + "/tools/blends/districts/boatyard.blend"
WALK_REF = REPO + "/tools/blends/districts/walk_reference.json"
rng = random.Random(4212)

# ===========================================================================
# 1. prune the town blockout down to the parcel region
# ===========================================================================
sc = bpy.context.scene
KEEP_CTX = set()   # the blockout far wall is replaced by a displaced, hazed one

walk_keep, lm_ref, dam_ref, ctx_keep, doomed = [], [], [], [], []
for ob in list(bpy.data.objects):
    if ob.type == 'MESH':
        b = world_bbox(ob)
        overlaps = (b[1] >= REGION[0][0] and b[0] <= REGION[0][1] and
                    b[3] >= REGION[1][0] and b[2] <= REGION[1][1])
        origin = ob.matrix_world.translation
        inbox = (REGION[0][0] <= origin.x <= REGION[0][1] and
                 REGION[1][0] <= origin.y <= REGION[1][1] and
                 REGION[2][0] <= origin.z <= REGION[2][1])
        if ob.name.startswith("walk_") and overlaps:
            walk_keep.append(ob)
            continue
        if ob.name.startswith("bar_") and overlaps:
            ctx_keep.append(ob)
            continue
        if ob.name.startswith("lm_") and inbox:
            lm_ref.append(ob)
            continue
        if ob.name.startswith("dam_dam-four"):
            dam_ref.append(ob)
            continue
        if ob.name in KEEP_CTX:
            ctx_keep.append(ob)
            continue
    doomed.append(ob)

for ob in doomed:
    bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    if not c.objects and not c.children:
        bpy.data.collections.remove(c)

print("REGION IMPORT: walk=%d  bar=%d  lm_ref=%d  dam_ref=%d" %
      (len(walk_keep), len([o for o in ctx_keep if o.name.startswith('bar_')]),
       len(lm_ref), len(dam_ref)))
for o in sorted(walk_keep, key=lambda o: o.name):
    print("   PRESERVED", o.name)

# --- record the exact authored walk geometry, for the QA assert -------------
ref = {}
for ob in walk_keep:
    ref[ob.name] = {
        "matrix": [list(r) for r in ob.matrix_world],
        "verts": [list(ob.matrix_world @ v.co) for v in ob.data.vertices],
    }
os.makedirs(os.path.dirname(WALK_REF), exist_ok=True)
json.dump(ref, open(WALK_REF, "w"))

WALK_COLL = coll("WALK_PRESERVED")
for ob in walk_keep:
    link(ob, "WALK_PRESERVED")
    ob.hide_render = True          # collision only; still exported to the GLB
REFC = coll("REF_MASSING")
for ob in lm_ref + dam_ref:
    link(ob, "REF_MASSING")

COR = Corridor(walk_keep)
COR0 = Corridor(walk_keep, margin=0.0)   # exact footprints, for burial tests
print("CORRIDOR: %d walk top faces" % len(COR.tops))


def free(x, y, z):
    return COR.free(x, y, z)


# ===========================================================================
# 2. harvest the accepted probe assets
# ===========================================================================
WANT = [
    # lighting / atmosphere
    "SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX",
    "v10_haze_mid", "v10_haze_far", "v10_haze_rim", "v10_far_town",
    "cliff_port", "cliff_stbd", "cliff_back", "cliff_back2",
    # hero geometry
    "hull_clinker", "hull_frames", "hull_blocks", "hull_shores",
    "boat_shed", "v10_shed_leanto", "v10_paintwork",
    "pitch_kettle", "kettle_fire", "v10_kettle_smoke", "v10_embers", "v10_gallows",
    "lock_four", "gate_spray",
    "v10_chandlery", "v10_netloft",
    "v10_barge_mid", "v10_barge_port", "v10_barge_stbd",
    "yard_clutter", "v10_foreclutter", "v10_redcrates", "v10_apron", "pilings",
    "v10_bunting", "lantern_posts",
    # kit props
    "kit_barrel", "kit_crate", "kit_rope_coil", "kit_bucket",
    "kit_railing_1m", "kit_railing_post", "kit_beam", "kit_stilt_trestle",
    "kit_lantern_hanging", "kit_lantern_light", "REF_human_1p7",
    # vegetation prototypes
    "v10_src_tree_a", "v10_src_tree_b", "v10_src_clump_a", "v10_src_clump_b",
    "v10_src_clump_far", "v10_src_creeper_a", "v10_src_creeper_b",
    "v10_src_tuft_grass", "v10_src_tuft_fern",
]
P = harvest(PROBE_BLEND, WANT, want_materials=True, want_world=True)
for ob in P.values():
    link(ob, "PROBE_SRC")
coll("PROBE_SRC").hide_render = True
coll("PROBE_SRC").hide_viewport = True

if bpy.data.worlds:
    w = None
    for cand in bpy.data.worlds:
        if cand.use_nodes and len(cand.node_tree.nodes) > 3:
            w = cand
    sc.world = w or bpy.data.worlds[0]
    print("WORLD:", sc.world.name, "nodes:", len(sc.world.node_tree.nodes) if sc.world.use_nodes else 0)


# --- an extra material: the black stone of the river dams -------------------
def make_blackstone():
    m = bpy.data.materials.new("mat_blackstone")
    m.use_fake_user = True
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 2.4
    n1.inputs["Detail"].default_value = 8.0; n1.inputs["Roughness"].default_value = 0.62
    n2 = nt.nodes.new("ShaderNodeTexVoronoi"); n2.inputs["Scale"].default_value = 1.15
    n2.feature = 'DISTANCE_TO_EDGE'
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    # v3/v4 sat at 0.028-0.105 and still resolved to a mid-grey wall, because the
    # key rakes this face head-on.  Near-black masonry has to be near-black in
    # albedo AND barely specular, or the sun just polishes it back to grey.
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.0115, 0.0130, 0.0165, 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (0.043, 0.045, 0.050, 1)
    mixc = nt.nodes.new("ShaderNodeMixRGB"); mixc.blend_type = 'MULTIPLY'
    mixc.inputs["Fac"].default_value = 0.55
    # wet band near the waterline (world Z)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    wet = nt.nodes.new("ShaderNodeMapRange")
    wet.inputs["From Min"].default_value = 0.15; wet.inputs["From Max"].default_value = 1.5
    wet.inputs["To Min"].default_value = 1.0; wet.inputs["To Max"].default_value = 0.0
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs["From Min"].default_value = 0.0; rough.inputs["From Max"].default_value = 1.0
    # a 0.16 gloss floor gave the whole dam a broad sheen of reflected sky — the
    # real reason it read pale.  Keep a damp sheen only near the waterline.
    rough.inputs["To Min"].default_value = 0.93; rough.inputs["To Max"].default_value = 0.54
    bsdf.inputs["Specular IOR Level"].default_value = 0.20
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.55
    nt.links.new(coord.outputs["Object"], n1.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(n2.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mixc.inputs["Color1"])
    nt.links.new(n1.outputs["Color"], mixc.inputs["Color2"])
    nt.links.new(mixc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(n2.outputs["Distance"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def make_whitewater():
    """FOAM ONLY.  v3 hung this material on full-height sheets across every gate
    bay, so the pale water — not the black masonry — became the wall that closes
    the shot (it read as poured concrete).  v4 uses it strictly as the spill
    crest, the plunge boil and thin highlight rims, and it is darkened a stop so
    even those accents sit under the AgX shoulder instead of clipping."""
    m = bpy.data.materials.new("mat_whitewater")
    m.use_fake_user = True
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.40, 0.435, 0.45, 1)
    bsdf.inputs["Roughness"].default_value = 0.52
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.80, 0.82, 0.86, 1)
    em.inputs["Strength"].default_value = 0.06
    coord = nt.nodes.new("ShaderNodeTexCoord")
    # fine, aerated foam.  At scale 11 / bump 0.7 this mottled into something
    # that read as speckled white granite on the thin rims rather than water.
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 34.0
    nz.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22
    nt.links.new(coord.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(nz.outputs["Fac"], mix.inputs["Fac"])
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


def make_darkfall():
    """The sheet of water actually standing in each gate bay: a dark, glassy,
    river-green fall.  Only its vertical streaks catch the rim, so the bays stay
    part of the black mass instead of punching pale holes in it."""
    m = bpy.data.materials.new("mat_darkfall")
    m.use_fake_user = True
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.72          # mostly glossy = wet sheet
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (0.016, 0.042, 0.044, 1)
    gloss = nt.nodes.new("ShaderNodeBsdfGlossy")
    gloss.inputs["Color"].default_value = (0.24, 0.30, 0.31, 1)
    gloss.inputs["Roughness"].default_value = 0.22
    coord = nt.nodes.new("ShaderNodeTexCoord")
    # stretch the noise vertically so it streaks the way falling water does
    mapn = nt.nodes.new("ShaderNodeMapping")
    mapn.inputs["Scale"].default_value = (7.0, 7.0, 0.55)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nz.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.55
    nt.links.new(coord.outputs["Object"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], diff.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], gloss.inputs["Normal"])
    nt.links.new(diff.outputs["BSDF"], mix.inputs[1])
    nt.links.new(gloss.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


# the lock-house window pane spans this world-Z band (see GAL_Z / the lock house
# below) — the emission gradient is keyed to it, so keep the two in step.
LH_WIN_Z0, LH_WIN_Z1 = 6.45, 7.30


def make_lockhouse_glass():
    """Warm amber lamplight in a real window.

    v3 hung mat_lantern_glass (pure emission, strength 90) on a 1.5 x 1.0 m
    pane.  That is the right number for a 12 cm lantern globe, but at window
    scale AgX creams it: the hue burns out of it and it lands as a clipped white
    rectangle in the upper middle of frame.  Emission has to sit UNDER the AgX
    shoulder to keep its colour, so this runs at 1.9-3.6 with a gradient (the
    lamp is on the sill, so the pane is hotter low) and a little old-glass
    unevenness across it."""
    m = bpy.data.materials.new("mat_lockhouse_glass")
    m.use_fake_user = True
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.455, 0.135, 1)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    grad = nt.nodes.new("ShaderNodeMapRange")       # hotter at the sill
    grad.inputs["From Min"].default_value = LH_WIN_Z1
    grad.inputs["From Max"].default_value = LH_WIN_Z0
    grad.inputs["To Min"].default_value = 6.80
    grad.inputs["To Max"].default_value = 10.50
    nz = nt.nodes.new("ShaderNodeTexNoise")         # wobbly hand-drawn glass
    nz.inputs["Scale"].default_value = 24.0
    nz.inputs["Detail"].default_value = 3.0
    mad = nt.nodes.new("ShaderNodeMath")
    mad.operation = 'MULTIPLY_ADD'
    mad.inputs[1].default_value = 0.34              # noise -> 0.83 .. 1.17
    mad.inputs[2].default_value = 0.83
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = 'MULTIPLY'
    nt.links.new(coord.outputs["Generated"], nz.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], grad.inputs["Value"])
    nt.links.new(nz.outputs["Fac"], mad.inputs[0])
    nt.links.new(grad.outputs["Result"], mul.inputs[0])
    nt.links.new(mad.outputs["Value"], mul.inputs[1])
    nt.links.new(mul.outputs["Value"], em.inputs["Strength"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def darken(src, name, mul, tint=(1.0, 1.0, 1.0), inplace=False):
    """Copy an image-based material and drop its albedo a stop or so.

    With inplace=True it retunes the material itself rather than deriving a copy.

    Used to build the value structure by hand: v3 lit every timber surface to
    the same midtone, so the frame read as uniform timber soup with no focal
    diagonal.  Darkening the under-structure and the mid-ground in the MATERIAL
    (rather than only in the light rig) keeps the slipway/hull diagonal reading
    as the lightest path through the shot no matter how the lamps move."""
    m = src if inplace else src.copy()
    if not inplace:
        m.name = name
    m.use_fake_user = True
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        return m
    bc = bsdf.inputs["Base Color"]
    dark = nt.nodes.new("ShaderNodeMixRGB")
    dark.blend_type = 'MULTIPLY'
    dark.inputs["Fac"].default_value = 1.0
    dark.inputs["Color2"].default_value = (mul * tint[0], mul * tint[1], mul * tint[2], 1)
    if bc.is_linked:
        srclink = bc.links[0].from_socket
        nt.links.new(srclink, dark.inputs["Color1"])
    else:
        dark.inputs["Color1"].default_value = bc.default_value
    nt.links.new(dark.outputs["Color"], bc)
    return m


def demoss_sides(mat):
    """Kill the white grid between roof shingles.

    The seams were never mortar or a UV artifact: mat_shingle* mixes its moss
    tint by face normal Z, so the 34 mm vertical riser at every course step got
    NO moss and showed the bare, very pale shingle albedo — a bright lattice
    across the roof.  Giving side-facing normals a healthy share of the moss mix
    (the sides weather too) removes the lattice without touching the geometry."""
    for n in mat.node_tree.nodes:
        if n.type != 'VALTORGB':
            continue
        e = n.color_ramp.elements
        if len(e) == 2 and abs(e[0].position - 0.25) < 1e-6 and abs(e[1].position - 0.85) < 1e-6:
            e[0].color = (0.62, 0.62, 0.62, 1)      # was pure black = no moss
            e[0].position = 0.10
            return True
    return False


MAT_STONE = make_blackstone()
MAT_WW = make_whitewater()
MAT_FALL = make_darkfall()
MAT_LHGLASS = make_lockhouse_glass()
MD, MT = M("mat_deck"), M("mat_timber")
MW, MWD = M("mat_wallwood"), M("mat_wallwood_dark")
MRED, MBLUE = M("mat_paint_red"), M("mat_paint_blue")
MSH, MSHM = M("mat_shingle"), M("mat_shingle_mossy")
MROCK, MROCKF = M("mat_rock"), M("mat_rock_far")
MWATER, MWET = M("mat_water"), M("mat_wet")
MIRON, MROPE, MTAR = M("mat_iron"), M("mat_rope"), M("mat_tar")
MSPRAY, MSMOKE = M("mat_spray"), M("mat_smoke")
MFRESH = M("mat_freshwood")

# --- value structure: darker timbers for the under-structure and the gates ---
# Slightly cool as well as dark: the shadow side of this shot is meant to read
# blue-grey against the warm lantern pools, and neutral-brown shadows were a
# large part of why v3 came out amber-monochrome.
MT_DARK = darken(MT, "mat_timber_dark", 0.38, (1.03, 1.00, 0.96))
MD_DARK = darken(MD, "mat_deck_dark", 0.50, (1.03, 1.00, 0.96))
MGATE = darken(MT, "mat_gate_timber", 0.24, (0.94, 0.96, 1.02))

# kill the shingle seams at the source (see demoss_sides)
for _sm in (MSHM, MSH):
    print("DEMOSS %-20s -> %s" % (_sm.name, demoss_sides(_sm)))
# ...and drop the roofs out of the highlight range: at 0.52 mean luma the mossy
# roof was the brightest large mass in the frame and competed with the focal
# diagonal for the eye (the reference sits its equivalent roof around 0.41).
darken(MSHM, None, 0.84, inplace=True)
darken(MSH, None, 0.88, inplace=True)

# The river was 88% glossy, so every water surface just mirrored the pale sky
# and read grey.  Letting more of the teal body through is what makes the water
# register as water in the dusk split (probe_v11 reads distinctly green-blue).
for _n in MWATER.node_tree.nodes:
    if _n.type == 'MIX_SHADER' and not _n.inputs["Fac"].is_linked:
        _n.inputs["Fac"].default_value = 0.60
    elif _n.type == 'BSDF_DIFFUSE':
        _n.inputs["Color"].default_value = (0.019, 0.132, 0.138, 1)
    elif _n.type == 'BSDF_GLOSSY':
        _n.inputs["Color"].default_value = (0.30, 0.40, 0.42, 1)


# ===========================================================================
# 3. terrain + water
# ===========================================================================
def gh_base(x, y):
    """The working hard: a gravel/mud shelf that runs the length of the yard and
    shelves into the mid pool at the north, backed by talus up to the cliff."""
    ykn = 30.6 if x <= 11.0 else (30.3 if x >= 15.0 else 30.6 - 0.3 * (x - 11.0) / 4.0)
    b = 3.15 - 0.030 * (x - 8.0)
    h = b - 0.10 * max(0.0, y - 24.0) - 1.35 * max(0.0, y - ykn)
    h += 2.60 * max(0.0, 21.4 - y) ** 1.30
    return h


# the launching slipway is cut down through the hard into the river
SLIP_X0, SLIP_X1 = 16.9, 21.8
SLIP_Y0, SLIP_Y1 = 31.5, 38.0
SLIP_Z0, SLIP_Z1 = 1.86, -1.45


def slip_z(y):
    t = max(0.0, min(1.0, (y - SLIP_Y0) / (SLIP_Y1 - SLIP_Y0)))
    return SLIP_Z0 + (SLIP_Z1 - SLIP_Z0) * t


def ground_z(x, y):
    n = (math.sin(x * 1.31 + y * 0.77) * 0.5 + math.sin(x * 0.43 - y * 2.11) * 0.32 +
         math.sin(x * 3.7 + y * 2.9) * 0.13)
    h = gh_base(x, y) + n * 0.13
    # every walk top face terraces the hard down to just below itself
    for poly, fn, raw, nm in COR.tops:
        d = dist_poly2(x, y, raw)
        if d < 3.2:
            h = min(h, fn(x, y) - 0.42 + d * 1.15)
    # slipway cut
    if y > SLIP_Y0 - 1.0:
        lat = max(0.0, max(SLIP_X0 - x, x - SLIP_X1))
        if lat < 2.2:
            h = min(h, slip_z(y) - 0.42 + lat * 1.05)
    return h


def build_ground():
    x0, x1, y0, y1, st = 0.5, 35.0, 17.4, 36.5, 0.40
    nx = int((x1 - x0) / st) + 1
    ny = int((y1 - y0) / st) + 1
    verts, faces = [], []
    for i in range(nx):
        for j in range(ny):
            x = x0 + i * st
            y = y0 + j * st
            verts.append((x, y, ground_z(x, y)))
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            faces.append((a, a + ny, a + ny + 1, a + 1))
    return new_mesh("yard_ground", verts, faces, MROCK, "BY_TERRAIN")


build_ground()

# water — replace the blockout slabs with tuned planes
new_mesh("water_mid", [(13.95, 18.0, WATER_MID), (94.0, 18.0, WATER_MID),
                       (94.0, 45.0, WATER_MID), (13.95, 45.0, WATER_MID)],
         [(0, 1, 2, 3)], MWATER, "BY_TERRAIN")
new_mesh("water_upstream", [(-70.0, 30.35, WATER_UP), (14.05, 30.35, WATER_UP),
                            (14.05, 48.0, WATER_UP), (-70.0, 48.0, WATER_UP)],
         [(0, 1, 2, 3)], MWATER, "BY_TERRAIN")
# river bed far side so the water never shows sky through it
box("riverbed", -70, 94, 18.0, 46.0, -4.2, -3.9, MROCK, "BY_TERRAIN")

# ---- the town cliff face closing the left of frame ------------------------
cliff = place(P["cliff_port"], (18.0, 16.4, -2.0), rz=0.0, mode="cxy_minz",
              name="cliff_town_face", cname="BY_TERRAIN")
cb = world_bbox(cliff)
print("cliff face bb:", ["%.1f" % v for v in cb])
cliff.data.materials.clear()
cliff.data.materials.append(MROCK)

# the far gorge wall across the river — hazed backdrop (map: farWallY 58)
farw = place(P["cliff_stbd"], (10.0, 57.5, -13.0), rz=0.0, mode="cxy_minz",
             name="cliff_far_wall", cname="BY_TERRAIN")
farw.data.materials.clear(); farw.data.materials.append(MROCKF)
print("far wall bb", ["%.1f" % v for v in world_bbox(farw)])

# distant upstream valley wall + hazed ridges
back = place(P["cliff_back"], (-88.0, 30.0, -8.0), rz=0.0, mode="cxy_minz",
             name="ridge_upstream", cname="BY_TERRAIN")
back.data.materials.clear(); back.data.materials.append(MROCKF)
back2 = place(P["cliff_back2"], (-52.0, 31.0, -7.0), rz=0.0, mode="cxy_minz",
              name="ridge_upstream_mid", cname="BY_TERRAIN")
back2.data.materials.clear(); back2.data.materials.append(MROCKF)
fartown = place(P["v10_far_town"], (-46.0, 30.0, 7.0), rz=0.0, mode="cxy_minz",
                name="far_town_silhouette", cname="BY_TERRAIN")


# ===========================================================================
# 4. planking laid to the walk ribbons  (the playable surface)
# ===========================================================================
DECK_DROP = 0.055
PLANK_ANG = {
    "walk_lm_slipway": math.radians(90),
    "walk_pad_boatwright-shed": math.radians(0),
    "walk_pad_drydock-frames": math.radians(0),
    "walk_pad_lockfour-overlook": math.radians(0),
    "walk_pad_winch-foot": math.radians(90),
}


def ribbon_angle(pts):
    """Planks run ACROSS a walkway: perpendicular to its long axis."""
    best, ang = 0.0, 0.0
    n = len(pts)
    for i in range(n):
        for j in range(i + 1, n):
            d = (pts[j] - pts[i]).to_2d()
            if d.length > best:
                best, ang = d.length, math.atan2(d.y, d.x)
    return ang + math.pi / 2


def _joist_ok(px, py, pz):
    t = COR0.top_at(px, py)
    if t is not None and pz > t - 0.02:
        return False
    return not COR.blocked((px, py, pz))


deck_parts, joist_parts, pile_parts = [], [], []
for ob in walk_keep:
    Mx = ob.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    for pi, p in enumerate(ob.data.polygons):
        if (N @ p.normal).normalized().z <= 0.5:
            continue
        raw = [Mx @ ob.data.vertices[i].co for i in p.vertices]
        # skip faces buried under a higher walk mesh (they are dead geometry)
        cxy = (sum(v.x for v in raw) / len(raw), sum(v.y for v in raw) / len(raw))
        czz = sum(v.z for v in raw) / len(raw)
        top = COR.top_at(*cxy)
        if top is not None and top > czz + 0.15:
            continue
        poly = offset_poly(raw, 0.52)
        zfn = plane_z_fn(raw)
        ang = PLANK_ANG.get(ob.name, ribbon_angle(raw))
        def _keep(px, py, pz, _c=COR0, _f=COR):
            t = _c.top_at(px, py)
            if t is not None and pz > t - 0.02:
                return False
            return not _f.blocked((px, py, pz))

        v, f = plank_fill(poly, ang, w=0.29, gap=0.016, thick=0.11,
                          jitter=0.013, drop=DECK_DROP, zfn=zfn,
                          seed=hash(ob.name) & 0xffff, keep=_keep)
        deck_parts.append(new_mesh("deck_%s_%d" % (ob.name[5:], pi), v, f, MD, "BY_DECK"))

        # joists under the planking, and piles down to the ground / river bed
        xs = [q.x for q in poly]; ys = [q.y for q in poly]
        ax0, ax1, ay0, ay1 = min(xs), max(xs), min(ys), max(ys)
        long_x = (ax1 - ax0) >= (ay1 - ay0)
        step = 0.95
        if long_x:
            u = ax0 + 0.35
            while u <= ax1 - 0.3:
                seg = clip_halfplane(clip_halfplane(poly, 1, 0, u + 0.09), -1, 0, -(u - 0.09))
                if len(seg) >= 3:
                    yy = [q.y for q in seg]
                    probe = [(u, min(yy) + 0.05), (u, (min(yy) + max(yy)) / 2), (u, max(yy) - 0.05)]
                    if all(_joist_ok(a, b, zfn(a, b) - 0.19) for a, b in probe):
                        joist_parts.append(beam("jo", (u, min(yy), zfn(u, min(yy)) - 0.28),
                                                (u, max(yy), zfn(u, max(yy)) - 0.28),
                                                0.13, 0.18, MT_DARK, "BY_DECK"))
                u += step
        else:
            u = ay0 + 0.35
            while u <= ay1 - 0.3:
                seg = clip_halfplane(clip_halfplane(poly, 0, 1, u + 0.09), 0, -1, -(u - 0.09))
                if len(seg) >= 3:
                    xx = [q.x for q in seg]
                    probe = [(min(xx) + 0.05, u), ((min(xx) + max(xx)) / 2, u), (max(xx) - 0.05, u)]
                    if all(_joist_ok(a, b, zfn(a, b) - 0.19) for a, b in probe):
                        joist_parts.append(beam("jo", (min(xx), u, zfn(min(xx), u) - 0.28),
                                                (max(xx), u, zfn(max(xx), u) - 0.28),
                                                0.13, 0.18, MT_DARK, "BY_DECK"))
                u += step

        # piles on a grid inside the face
        gx = ax0 + 0.55
        while gx < ax1 - 0.4:
            gy = ay0 + 0.55
            while gy < ay1 - 0.4:
                if point_in_poly(gx, gy, poly):
                    if not _joist_ok(gx, gy, zfn(gx, gy) - 0.30):
                        gy += 1.55
                        continue
                    ztop = zfn(gx, gy) - 0.30
                    zbot = ground_z(gx, gy) - 0.35
                    if ztop - zbot > 0.95:
                        pile_parts.append(cyl("pl", (gx, gy, zbot), (gx, gy, ztop),
                                              0.135 + rng.random() * 0.04, 7,
                                              MWET if zbot < WATER_MID else MT_DARK, "BY_DECK"))
                gy += 1.55
            gx += 1.55

join_meshes(deck_parts, "yard_planking", "BY_DECK")
join_meshes(joist_parts, "yard_joists", "BY_DECK")
join_meshes(pile_parts, "yard_piles", "BY_DECK")
print("DECK: planking laid over %d walk top faces" % len(walk_keep))


# ===========================================================================
# 5. free-standing staging (non-walkable dressing decks)
# ===========================================================================
def staging(name, x0, x1, y0, y1, z, ang=math.radians(90), skirt=True):
    poly = [Vector((x0, y0, z)), Vector((x1, y0, z)), Vector((x1, y1, z)), Vector((x0, y1, z))]
    v, f = plank_fill(poly, ang, w=0.30, gap=0.016, thick=0.12, jitter=0.014,
                      drop=0.0, zfn=lambda X, Y: z, seed=hash(name) & 0xffff)
    parts = [new_mesh(name, v, f, MD, "BY_DECK")]
    for u in [x0 + 0.5 + i * 1.6 for i in range(int((x1 - x0 - 0.8) / 1.6) + 1)]:
        parts.append(beam("jo", (u, y0, z - 0.22), (u, y1, z - 0.22), 0.14, 0.22, MT, "BY_DECK"))
        for w in [y0 + 0.6 + i * 1.7 for i in range(int((y1 - y0 - 1.0) / 1.7) + 1)]:
            zb = min(ground_z(u, w), WATER_MID) - 0.5
            parts.append(cyl("pl", (u, w, zb), (u, w, z - 0.28),
                             0.15, 8, MWET, "BY_DECK"))
    return join_meshes(parts, name, "BY_DECK")


# ===========================================================================
# 6. Lock Four — black stone dam, gates, spillway, spray
# ===========================================================================
LOCK = []
DAMX0, DAMX1 = 12.35, 15.85
# south abutment: the boardwalk climbs over it, so the stone only rises to
# just under the walk ribbon and the bank carries the path.
# The abutment has to stay UNDER the drydock pad and the boardwalk that climb
# over it, so it only rises to full height south of the walk graph.
LOCK.append(box("dam4_abutment", DAMX0, DAMX1, 19.0, 22.90, -1.6, 3.30, MAT_STONE, "BY_LOCK"))
LOCK.append(box("dam4_abutment_ramp", DAMX0, DAMX1, 22.90, 30.15, -1.6, 2.08, MAT_STONE, "BY_LOCK"))
LOCK.append(box("dam4_abutment_n", DAMX0, DAMX1, 30.15, 30.75, -1.6, 4.35, MAT_STONE, "BY_LOCK"))
# main weir out into the river
LOCK.append(box("dam4_weir", DAMX0, DAMX1, 30.75, 44.0, -1.6, 4.35, MAT_STONE, "BY_LOCK"))
LOCK.append(box("dam4_crest", DAMX0 - 0.28, DAMX1 + 0.28, 30.15, 44.0, 4.35, 4.62, MAT_STONE, "BY_LOCK"))
# the cap was mat_rock — a pale grey that read as poured concrete against the
# black masonry.  The whole mass is one stone now.
LOCK.append(box("dam4_cap", DAMX0 - 0.36, DAMX1 + 0.36, 30.15, 44.0, 4.62, 4.80, MAT_STONE, "BY_LOCK"))
# crest parapet on the downstream lip
LOCK.append(box("dam4_parapet", DAMX1 + 0.02, DAMX1 + 0.28, 30.6, 44.0, 4.62, 5.35, MAT_STONE, "BY_LOCK"))
# the quay wall that retains the upper pool along the lock terrace
LOCK.append(box("lock4_quaywall", 1.0, DAMX0, 30.75, 31.35, 1.0, 4.05, MAT_STONE, "BY_LOCK"))
LOCK.append(box("lock4_quaycap", 0.9, DAMX0, 30.68, 31.45, 4.05, 4.22, MAT_STONE, "BY_LOCK"))

# --- spill gates ------------------------------------------------------------
# v3 filled each bay with a full-height sheet of mat_whitewater.  Three 1.8 x
# 4.3 m pale rectangles is what made Lock Four read as a bank of concrete
# panels: the water, not the masonry, was the wall closing the shot.  v4 closes
# the gates instead — dark timber leaves banded in iron, set into the black
# stone — and water is reduced to what it should be: a dark glassy fall over
# each leaf, a thin FOAM line where it tips, and a boil at the foot.
GATE_Y = (32.6, 36.0, 39.4)
GATE_HW = 1.15          # bay half-width (slot centre to slot centre)
for i, gy in enumerate(GATE_Y):
    LOCK.append(box("dam4_gateslot%d" % i, DAMX0 - 0.32, DAMX1 + 0.32, gy - GATE_HW, gy - 0.95,
                    2.4, 5.9, MAT_STONE, "BY_LOCK"))
    LOCK.append(box("dam4_gateslot%db" % i, DAMX0 - 0.32, DAMX1 + 0.32, gy + 0.95, gy + GATE_HW,
                    2.4, 5.9, MAT_STONE, "BY_LOCK"))
    LOCK.append(box("dam4_gatelintel%d" % i, DAMX0 - 0.32, DAMX1 + 0.32, gy - GATE_HW, gy + GATE_HW,
                    5.5, 5.9, MAT_STONE, "BY_LOCK"))
    # the closed timber leaf, on the DOWNSTREAM face where the camera can see it
    LOCK.append(box("dam4_gateleaf%d" % i, DAMX1 - 0.34, DAMX1 + 0.30, gy - 0.92, gy + 0.92,
                    0.55, 3.95, MGATE, "BY_LOCK"))
    # iron banding across the leaf, proud of the boards
    for zb in (1.02, 1.90, 2.78, 3.64):
        LOCK.append(beam("dam4_gateband%d" % i, (DAMX1 + 0.30, gy - 0.94, zb),
                         (DAMX1 + 0.30, gy + 0.94, zb), 0.13, 0.11, MIRON, "BY_LOCK"))
    # vertical stiles + the hanging strap-hinges, clear of the spill so the
    # ironwork stays readable either side of the falling sheet
    for sy in (gy - 0.66, gy + 0.66):
        LOCK.append(beam("dam4_gatestile%d" % i, (DAMX1 + 0.34, sy, 0.58),
                         (DAMX1 + 0.34, sy, 3.92), 0.12, 0.13, MGATE, "BY_LOCK"))
    for sy in (gy - 0.86, gy + 0.86):
        LOCK.append(beam("dam4_gatehinge%d" % i, (DAMX1 + 0.36, sy, 0.58),
                         (DAMX1 + 0.36, sy, 3.92), 0.10, 0.09, MIRON, "BY_LOCK"))
    # winding gear over the slot
    LOCK.append(beam("dam4_wind%d" % i, (DAMX0 + 0.55, gy - 1.3, 5.95),
                     (DAMX0 + 0.55, gy + 1.3, 5.95), 0.16, 0.16, MT, "BY_LOCK"))
    LOCK.append(cyl("dam4_windwheel%d" % i, (DAMX0 + 0.30, gy, 6.25), (DAMX0 + 0.80, gy, 6.25),
                    0.42, 12, MIRON, "BY_LOCK"))
    # the fall itself: dark, glassy, streaked — NOT a pale panel — and only as
    # wide as the worn centre of the leaf, so the banded timber shows either side
    LOCK.append(box("dam4_fall%d" % i, DAMX1 + 0.30, DAMX1 + 0.58, gy - 0.44, gy + 0.44,
                    0.42, 4.02, MAT_FALL, "BY_LOCK"))
    # the only white in the bay: the foam line where the sheet tips over the
    # leaf, and the boil where it lands
    LOCK.append(box("dam4_crestfoam%d" % i, DAMX1 - 0.02, DAMX1 + 0.62, gy - 0.52, gy + 0.52,
                    3.90, 4.16, MAT_WW, "BY_LOCK"))
    LOCK.append(box("dam4_plunge%d" % i, DAMX1 + 0.20, DAMX1 + 1.55, gy - 1.10, gy + 1.10,
                    0.18, 0.58, MAT_WW, "BY_LOCK"))

# battered piers + string courses on the downstream face
for k in range(9):
    py = 30.6 + k * 1.55
    LOCK.append(new_mesh("dam4_pier%d" % k,
                         [(DAMX1, py, -1.2), (DAMX1 + 0.62, py, -1.2),
                          (DAMX1 + 0.62, py + 0.72, -1.2), (DAMX1, py + 0.72, -1.2),
                          (DAMX1, py + 0.10, 4.30), (DAMX1 + 0.26, py + 0.10, 4.30),
                          (DAMX1 + 0.26, py + 0.62, 4.30), (DAMX1, py + 0.62, 4.30)],
                         [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                          (2, 3, 7, 6), (3, 0, 4, 7)], MAT_STONE, "BY_LOCK"))
# string courses, broken around the gate bays so they read as masonry coursing
# rather than a band ruled straight across the timber gates
_segs, _y = [], 30.15
for _gy in GATE_Y:
    if _gy - GATE_HW > _y:
        _segs.append((_y, _gy - GATE_HW))
    _y = _gy + GATE_HW
_segs.append((_y, 44.0))
for zc in (1.15, 2.55, 3.75):
    for ya, yb in _segs:
        LOCK.append(box("dam4_course", DAMX1, DAMX1 + 0.20, ya, yb, zc, zc + 0.26,
                        MAT_STONE, "BY_LOCK"))

# NO nappe between the gates.  v3 ran a 0.87 m pale band the full length of the
# weir; thinning it to a rim still left a continuous white ledge ruled straight
# across the dam — the brightest element on the mass that is supposed to be the
# darkest thing in frame.  It was never motivated either: the leaves spill at
# 3.95 and the solid crest stands at 4.35, so every drop goes through the three
# bays.  The white in this wall is now exactly the foam at those three spills
# and the boil at the foot, which is what the art direction asked for.
# lantern posts marking the crest walkway
for k in range(5):
    ly = 31.4 + k * 2.9
    LOCK.append(beam("dam4_crestpost", (DAMX0 - 0.10, ly, 4.62), (DAMX0 - 0.10, ly, 6.30),
                     0.16, 0.16, MT, "BY_LOCK"))
# --- crest gallery: a timber gantry deck the length of the weir, with the
#     lock house over the middle gate.  This is what actually closes the shot.
GAL_Z = 5.35
for k in range(10):
    gy = 30.9 + k * 1.42
    LOCK.append(beam("gal_pier", (DAMX0 + 0.30, gy, 4.35), (DAMX0 + 0.30, gy, GAL_Z),
                     0.24, 0.24, MT, "BY_LOCK"))
    LOCK.append(beam("gal_pier2", (DAMX1 - 0.30, gy, 4.35), (DAMX1 - 0.30, gy, GAL_Z),
                     0.24, 0.24, MT, "BY_LOCK"))
LOCK.append(box("gal_deck", DAMX0 - 0.25, DAMX1 + 0.25, 30.6, 44.0, GAL_Z, GAL_Z + 0.16, MD, "BY_LOCK"))
for k in range(19):
    gy = 30.8 + k * 0.72
    LOCK.append(beam("gal_post", (DAMX1 + 0.20, gy, GAL_Z + 0.16), (DAMX1 + 0.20, gy, GAL_Z + 1.06),
                     0.11, 0.11, MT, "BY_LOCK"))
for hz in (1.00, 0.55):
    LOCK.append(beam("gal_rail", (DAMX1 + 0.20, 30.6, GAL_Z + hz), (DAMX1 + 0.20, 44.0, GAL_Z + hz),
                     0.09, 0.12, MT, "BY_LOCK"))
    LOCK.append(beam("gal_railw", (DAMX0 - 0.20, 30.6, GAL_Z + hz), (DAMX0 - 0.20, 44.0, GAL_Z + hz),
                     0.09, 0.12, MT, "BY_LOCK"))
# the lock house
LHY0, LHY1 = 31.4, 35.2
LOCK.append(box("lh_wall_e", DAMX1 - 0.18, DAMX1 + 0.22, LHY0, LHY1, GAL_Z + 0.16, GAL_Z + 2.55, MWD, "BY_LOCK"))
LOCK.append(box("lh_wall_w", DAMX0 - 0.22, DAMX0 + 0.18, LHY0, LHY1, GAL_Z + 0.16, GAL_Z + 2.55, MW, "BY_LOCK"))
LOCK.append(box("lh_wall_s", DAMX0 - 0.22, DAMX1 + 0.22, LHY0, LHY0 + 0.32, GAL_Z + 0.16, GAL_Z + 2.55, MW, "BY_LOCK"))
LOCK.append(box("lh_wall_n", DAMX0 - 0.22, DAMX1 + 0.22, LHY1 - 0.32, LHY1, GAL_Z + 0.16, GAL_Z + 2.55, MW, "BY_LOCK"))
# --- the lock-house window --------------------------------------------------
# In v3 this was a bare 1.5 x 1.0 m slab of mat_lantern_glass (emission 90) and
# it blew to a clipped white rectangle dominating the upper middle of frame.
# Now: a smaller pane in mat_lockhouse_glass (emission 1.9-3.6, amber, keyed to
# LH_WIN_Z0/Z1), set back behind a timber frame and divided into six lights, so
# it reads as a lit window rather than a hole cut in the picture.
WY0, WY1 = LHY0 + 1.25, LHY0 + 2.45
assert abs((GAL_Z + 1.10) - LH_WIN_Z0) < 1e-6 and abs((GAL_Z + 1.95) - LH_WIN_Z1) < 1e-6, \
    "lock-house window Z must match LH_WIN_Z0/Z1 that drive the emission gradient"
# The pane must sit PROUD of lh_wall_e, whose outer face is DAMX1 + 0.22 — the
# first pass put the glass at +0.14..+0.21, i.e. buried inside the wall, and the
# window went black.  Everything here is ordered outward from that face.
LH_WALL_X = DAMX1 + 0.22
LOCK.append(box("lh_win", LH_WALL_X - 0.03, LH_WALL_X + 0.05, WY0, WY1, LH_WIN_Z0, LH_WIN_Z1,
                MAT_LHGLASS, "BY_LOCK"))
# mullions + transom stand in front of the glass: two bars and one = six lights
for _k in (1, 2):
    _my = WY0 + (WY1 - WY0) * _k / 3.0
    LOCK.append(beam("lh_win_mullion", (LH_WALL_X + 0.09, _my, LH_WIN_Z0),
                     (LH_WALL_X + 0.09, _my, LH_WIN_Z1), 0.07, 0.05, MT, "BY_LOCK"))
LOCK.append(beam("lh_win_transom", (LH_WALL_X + 0.09, WY0, (LH_WIN_Z0 + LH_WIN_Z1) / 2.0),
                 (LH_WALL_X + 0.09, WY1, (LH_WIN_Z0 + LH_WIN_Z1) / 2.0), 0.05, 0.045, MT, "BY_LOCK"))
# reveal: jambs, head and sill, standing proud again so the pane sits in a frame
for _wy in (WY0 - 0.09, WY1 + 0.09):
    LOCK.append(beam("lh_win_jamb", (LH_WALL_X + 0.10, _wy, LH_WIN_Z0 - 0.12),
                     (LH_WALL_X + 0.10, _wy, LH_WIN_Z1 + 0.12), 0.17, 0.13, MT, "BY_LOCK"))
LOCK.append(beam("lh_win_head", (LH_WALL_X + 0.10, WY0 - 0.17, LH_WIN_Z1 + 0.09),
                 (LH_WALL_X + 0.10, WY1 + 0.17, LH_WIN_Z1 + 0.09), 0.20, 0.14, MT, "BY_LOCK"))
LOCK.append(beam("lh_win_sill", (LH_WALL_X + 0.13, WY0 - 0.21, LH_WIN_Z0 - 0.09),
                 (LH_WALL_X + 0.13, WY1 + 0.21, LH_WIN_Z0 - 0.09), 0.26, 0.12, MT, "BY_LOCK"))
for k in range(9):
    ry = LHY0 - 0.35 + k * 0.55
    LOCK.append(beam("lh_raft", (DAMX0 - 0.55, ry, GAL_Z + 2.55), (14.1, ry, GAL_Z + 3.45),
                     0.10, 0.14, MT, "BY_LOCK"))
    LOCK.append(beam("lh_raft2", (DAMX1 + 0.55, ry, GAL_Z + 2.55), (14.1, ry, GAL_Z + 3.45),
                     0.10, 0.14, MT, "BY_LOCK"))
for k in range(7):
    ry = LHY0 - 0.35 + k * 0.72
    for side in (0, 1):
        x0r = (DAMX0 - 0.62) if side == 0 else 14.1
        x1r = 14.15 if side == 0 else (DAMX1 + 0.62)
        za = GAL_Z + 2.50 if side == 0 else GAL_Z + 3.42
        zb = GAL_Z + 3.42 if side == 0 else GAL_Z + 2.50
        LOCK.append(new_mesh("lh_shingle",
                             [(x0r, ry, za), (x1r, ry, zb), (x1r, ry + 0.80, zb), (x0r, ry + 0.80, za),
                              (x0r, ry, za - 0.06), (x1r, ry, zb - 0.06),
                              (x1r, ry + 0.80, zb - 0.06), (x0r, ry + 0.80, za - 0.06)],
                             [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                              (2, 3, 7, 6), (3, 0, 4, 7)], MSHM, "BY_LOCK"))

join_meshes(LOCK, "lock_four_dam", "BY_LOCK")

# spray at the foot of the dam (harvested probe volume, re-scaled to the weir)
spray = place(P["gate_spray"], (17.6, 36.5, -0.25), rz=0.0, mode="cxy_minz",
              name="dam4_spray", cname="BY_LOCK")
sb = world_bbox(spray)
print("spray bb", ["%.1f" % v for v in sb])

# foam pad on the water below the weir
new_mesh("dam4_foam", [(17.5, 30.6, 0.24), (22.4, 30.6, 0.24), (22.4, 44.0, 0.24), (17.5, 44.0, 0.24)],
         [(0, 1, 2, 3)], M("mat_spray"), "BY_LOCK")
# a narrow plunge-pool lip so the black wall reads against white water — a
# waterline, not the 1 m slab of white v3 laid along the whole foot of the dam
new_mesh("dam4_lip", [(15.85, 30.6, 0.30), (16.50, 30.6, 0.30),
                      (16.50, 44.0, 0.30), (15.85, 44.0, 0.30)],
         [(0, 1, 2, 3)], MAT_WW, "BY_LOCK")

# lock-four winding house / gate gantry over the boardwalk (all above z 4.6)
G = []
for gx, gy in ((12.6, 22.95), (15.6, 22.95), (12.6, 30.25), (15.6, 30.25)):
    G.append(beam("g_post", (gx, gy, 2.6), (gx, gy, 6.5), 0.24, 0.24, MT, "BY_LOCK"))
G.append(beam("g_bm", (12.6, 22.95, 6.5), (12.6, 30.25, 6.5), 0.22, 0.30, MT, "BY_LOCK"))
G.append(beam("g_bm", (15.6, 22.95, 6.5), (15.6, 30.25, 6.5), 0.22, 0.30, MT, "BY_LOCK"))
G.append(beam("g_bm", (12.6, 22.95, 6.62), (15.6, 22.95, 6.62), 0.22, 0.30, MT, "BY_LOCK"))
G.append(beam("g_bm", (12.6, 30.25, 6.62), (15.6, 30.25, 6.62), 0.22, 0.30, MT, "BY_LOCK"))
for k in range(4):
    yy = 22.95 + k * 2.433
    G.append(beam("g_rft", (12.35, yy, 6.78), (15.85, yy, 6.78), 0.10, 0.16, MT, "BY_LOCK"))
G.append(cyl("g_drum", (12.9, 28.3, 6.15), (15.3, 28.3, 6.15), 0.34, 12, MIRON, "BY_LOCK"))
for br in ((12.6, 22.95), (15.6, 22.95), (12.6, 30.25), (15.6, 30.25)):
    G.append(beam("g_brace", (br[0], br[1], 5.4), (br[0], br[1] - (0.9 if br[1] < 28 else -0.9), 6.45),
                  0.13, 0.13, MT, "BY_LOCK"))
join_meshes(G, "lock_four_gantry", "BY_LOCK")


# ===========================================================================
# 7. hulls
# ===========================================================================
# --- hero: clinker hull chocked up on the hard, right of frame -------------
hero = bake_group([P["hull_clinker"], P["hull_shores"]],
                  rz=0.0, prefix="hero_", cname="BY_HULLS")
anchor_group(hero, hero[0], (27.9, 29.40, ground_z(27.9, 29.40) + 0.60), "cxy_minz")
hb = world_bbox(hero[0])
print("hero hull bb", ["%.2f" % v for v in hb])
CH = []
for u in (25.0, 27.0, 29.0, 31.0):
    CH.append(box("chock", u - 0.55, u + 0.55, 28.85, 29.95,
                  ground_z(u, 29.4) - 0.15, hb[4] + 0.10, MT, "BY_HULLS"))
join_meshes(CH, "hero_hull_chocks", "BY_HULLS")
PAINT = []
for i, (cx, cy, col) in enumerate(((25.6, 27.05, MRED), (26.5, 27.15, MBLUE),
                                   (30.6, 27.35, MRED), (21.9, 32.35, MBLUE),
                                   (33.1, 27.9, MW))):
    gz = ground_z(cx, cy)
    if not free(cx, cy, gz + 0.5):
        continue
    o = place(P["kit_crate"], (cx, cy, gz), rz=rng.random() * 6.28,
              name="paintcrate_%d" % i, cname="BY_PROPS")
    o.data.materials.clear()
    o.data.materials.append(col)


# --- ribbed skeleton hull straddling the drydock pad -----------------------
frames = bake_group([P["hull_frames"]], rz=math.radians(0),
                    scale=(1.20, 1.55, 1.05), prefix="dry_", cname="BY_HULLS")
anchor_group(frames, frames[0], (14.0, 25.0, 5.22), "cxy_minz")
fb = world_bbox(frames[0])
print("frames bb", ["%.2f" % v for v in fb])
# the stocks that carry it — posts only where the corridor allows
kb = []
for (ux, uy) in ((11.3, 22.4), (11.3, 27.12), (16.7, 22.4), (16.7, 27.12),
                 (14.0, 22.4), (14.0, 27.12)):
    if free(ux, uy, 3.4) and free(ux, uy, 4.6):
        kb.append(beam("stock_post", (ux, uy, ground_z(ux, uy) - 0.2), (ux, uy, 5.34),
                       0.30, 0.30, MT, "BY_HULLS"))
for uy in (22.4, 27.12):
    kb.append(beam("stock_cap", (10.9, uy, 5.22), (17.1, uy, 5.22), 0.26, 0.30, MT, "BY_HULLS"))
for ux in (11.3, 14.0, 16.7):
    kb.append(beam("stock_tie", (ux, 22.4, 5.22), (ux, 27.12, 5.22), 0.22, 0.26, MT, "BY_HULLS"))
    kb.append(beam("stock_brace", (ux, 22.4, 5.05), (ux, 22.4, 2.20), 0.14, 0.14, MT, "BY_HULLS"))
    kb.append(beam("stock_brace", (ux, 27.12, 5.05), (ux, 27.12, 2.20), 0.14, 0.14, MT, "BY_HULLS"))
join_meshes(kb, "drydock_stocks", "BY_HULLS")

# --- the launching slipway running down into the river ---------------------
SL = []
sx0, sx1 = SLIP_X0, SLIP_X1
for k in range(16):
    y = SLIP_Y0 + k * (SLIP_Y1 - SLIP_Y0) / 15
    y2 = y + (SLIP_Y1 - SLIP_Y0) / 15 + 0.02
    SL.append(new_mesh("sl_slab",
                       [(sx0, y, slip_z(y) - 0.40), (sx1, y, slip_z(y) - 0.40),
                        (sx1, y2, slip_z(y2) - 0.40), (sx0, y2, slip_z(y2) - 0.40),
                        (sx0, y, slip_z(y)), (sx1, y, slip_z(y)),
                        (sx1, y2, slip_z(y2)), (sx0, y2, slip_z(y2))],
                       [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                        (2, 3, 7, 6), (3, 0, 4, 7)],
                       MAT_STONE if y > 33.0 else MROCK, "BY_HULLS"))
for u in (17.7, 21.0):
    SL.append(beam("sl_way", (u, SLIP_Y0 - 0.2, SLIP_Z0 + 0.22), (u, SLIP_Y1, SLIP_Z1 + 0.20),
                   0.36, 0.28, MWET, "BY_HULLS"))
for k in range(11):
    y = SLIP_Y0 - 0.1 + k * 0.72
    SL.append(beam("sl_slp", (sx0 + 0.2, y, slip_z(y) + 0.07), (sx1 - 0.2, y, slip_z(y) + 0.07),
                   0.22, 0.15, MWET, "BY_HULLS"))
join_meshes(SL, "slipway_ramp", "BY_HULLS")

# a second, smaller hull half-launched on the slip
small = bake_group([P["hull_clinker"]], rz=math.radians(90), scale=(0.62, 0.62, 0.62),
                   prefix="slip_", cname="BY_HULLS")
anchor_group(small, small[0], (19.4, 34.2, slip_z(34.2) + 0.30), "cxy_minz")
print("slip hull bb", ["%.2f" % v for v in world_bbox(small[0])])


# ===========================================================================
# 8. the boatwright's shed  (roof over the walk pad, walls only where legal)
# ===========================================================================
S = []
SHED_S, SHED_N = 21.55, 25.95          # south wall line / north eave line
SHED_W, SHED_E = 22.15, 27.75
ZS_TOP, ZN_TOP = 6.50, 4.72            # monopitch: high at the south wall


def shed_roof_z(y):
    return ZS_TOP + (ZN_TOP - ZS_TOP) * (y - SHED_S + 0.5) / (SHED_N - SHED_S + 1.0)


# south wall (painted board), on the bank behind the yard
S.append(box("sh_wall_s", SHED_W, SHED_E, SHED_S, SHED_S + 0.22, 1.55, ZS_TOP, MW, "BY_SHED"))
for k in range(9):
    u = SHED_W + 0.28 + k * 0.66
    S.append(beam("sh_stud", (u, SHED_S + 0.11, 1.55), (u, SHED_S + 0.11, ZS_TOP), 0.15, 0.30, MT, "BY_SHED"))
S.append(beam("sh_sill", (SHED_W, SHED_S + 0.11, 1.9), (SHED_E, SHED_S + 0.11, 1.9), 0.34, 0.26, MT, "BY_SHED"))
S.append(beam("sh_plate", (SHED_W - 0.2, SHED_S + 0.11, ZS_TOP - 0.16),
              (SHED_E + 0.2, SHED_S + 0.11, ZS_TOP - 0.16), 0.30, 0.28, MT, "BY_SHED"))
# short east return wall (stops clear of the winch path)
S.append(box("sh_wall_e", SHED_E - 0.22, SHED_E, SHED_S, 23.45, 1.7, 6.05, MWD, "BY_SHED"))
# west return, tight against the bank
S.append(box("sh_wall_w", SHED_W, SHED_W + 0.22, SHED_S, 22.85, 1.8, 6.4, MW, "BY_SHED"))

# posts: only where the corridor allows
post_xy = []
for cand in [(SHED_W + 0.1, SHED_S + 0.1), (SHED_E - 0.1, SHED_S + 0.1),
             (SHED_W + 0.1, 22.75), (SHED_E - 0.1, 22.9),
             (SHED_E - 0.1, SHED_N), (SHED_W + 0.1, SHED_N),
             (24.9, SHED_N), (SHED_E - 0.1, 24.9)]:
    z = 3.2
    if free(cand[0], cand[1], z) and free(cand[0], cand[1], z + 1.2):
        post_xy.append(cand)
    else:
        nb = COR.find_free(cand[0], cand[1], z, radius=1.6)
        if nb:
            post_xy.append(nb)
print("SHED posts kept:", ["(%.2f,%.2f)" % p for p in post_xy])
for (px, py) in post_xy:
    S.append(beam("sh_post", (px, py, ground_z(px, py) - 0.2), (px, py, shed_roof_z(py) - 0.18),
                  0.26, 0.26, MT, "BY_SHED"))

# rafters + roof plane (everything above the 2 m corridor headroom)
for k in range(11):
    u = SHED_W - 0.25 + k * 0.60
    S.append(beam("sh_raft", (u, SHED_S - 0.5, shed_roof_z(SHED_S - 0.5)),
                  (u, SHED_N + 0.65, shed_roof_z(SHED_N + 0.65)), 0.13, 0.22, MT, "BY_SHED"))
S.append(beam("sh_purlin", (SHED_W - 0.3, SHED_N + 0.6, shed_roof_z(SHED_N + 0.6) - 0.2),
              (SHED_E + 0.3, SHED_N + 0.6, shed_roof_z(SHED_N + 0.6) - 0.2), 0.24, 0.32, MT, "BY_SHED"))
# shingle courses (overlapped, sheathed in the SAME material — manifest item 13)
# The white lattice on this roof in v3 came from two places: a 35 mm side gap
# that showed bare sheathing, and a 34 mm riser at every course step whose
# vertical normal got no moss (see demoss_sides).  Tiles now butt at 12 mm and
# step 22 mm, and the risers are tinted, so the courses read as texture.
ny = int((SHED_N + 0.75 - (SHED_S - 0.55)) / 0.285) + 1
nx_s = int((SHED_E + 0.35 - (SHED_W - 0.35)) / 0.31) + 1
for k in range(ny):
    y = SHED_S - 0.55 + k * 0.285
    z = shed_roof_z(y)
    off = 0.155 if k % 2 else 0.0
    for m in range(nx_s):
        xs = SHED_W - 0.35 + m * 0.31 + off
        if xs > SHED_E + 0.35:
            continue
        jz = (rng.random() - 0.5) * 0.010
        S.append(box("shc", xs, min(xs + 0.298, SHED_E + 0.35), y, y + 0.44,
                     z + 0.008 + jz, z + 0.030 + jz, MSHM, "BY_SHED"))
zA, zB = shed_roof_z(SHED_S - 0.55), shed_roof_z(SHED_N + 0.75)
S.append(new_mesh("sh_sheath",
                  [(SHED_W - 0.35, SHED_S - 0.55, zA), (SHED_E + 0.35, SHED_S - 0.55, zA),
                   (SHED_E + 0.35, SHED_N + 0.75, zB), (SHED_W - 0.35, SHED_N + 0.75, zB),
                   (SHED_W - 0.35, SHED_S - 0.55, zA - 0.09), (SHED_E + 0.35, SHED_S - 0.55, zA - 0.09),
                   (SHED_E + 0.35, SHED_N + 0.75, zB - 0.09), (SHED_W - 0.35, SHED_N + 0.75, zB - 0.09)],
                  [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
                  MSHM, "BY_SHED"))
join_meshes(S, "boatwright_shed", "BY_SHED")

# workbench + tool clutter under the shed roof, hugging the south wall
W = []
W.append(box("wb_top", 22.6, 26.9, 21.85, 22.62, 2.28, 2.40, MFRESH, "BY_SHED"))
for u in (22.85, 24.75, 26.6):
    W.append(beam("wb_leg", (u, 22.0, ground_z(u, 22.0) - 0.1), (u, 22.0, 2.28), 0.14, 0.14, MT, "BY_SHED"))
    W.append(beam("wb_leg", (u, 22.5, ground_z(u, 22.5) - 0.1), (u, 22.5, 2.28), 0.14, 0.14, MT, "BY_SHED"))
for k in range(7):
    u = 22.8 + k * 0.62
    W.append(beam("wb_plank", (u, 21.9, 2.44), (u + 0.4, 21.9, 2.62), 0.09, 0.22, MFRESH, "BY_SHED"))
# saw-horses + strakes stacked against the wall
for k, u in enumerate((23.2, 25.5)):
    for dx in (-0.5, 0.5):
        W.append(beam("sw_leg", (u + dx, 22.75, ground_z(u + dx, 22.75)), (u, 22.75, 2.05), 0.10, 0.10, MT, "BY_SHED"))
        W.append(beam("sw_leg", (u + dx, 23.25, ground_z(u + dx, 23.25)), (u, 23.25, 2.05), 0.10, 0.10, MT, "BY_SHED"))
    W.append(beam("sw_top", (u - 0.7, 22.75, 2.08), (u + 0.7, 23.25, 2.08), 0.16, 0.14, MT, "BY_SHED"))
for k in range(5):
    W.append(beam("strake", (22.4 + rng.random() * 0.4, 22.9 + k * 0.06, 2.12 + k * 0.09),
                  (26.6 + rng.random() * 0.5, 23.1 + k * 0.06, 2.16 + k * 0.09),
                  0.30, 0.055, MFRESH, "BY_SHED"))
# forge brazier under the shed roof — the warm accent the left third needs
BZ = []
bzx, bzy = 26.85, 22.35
bz = ground_z(bzx, bzy)
BZ.append(cyl("bz_pot", (bzx, bzy, bz + 0.55), (bzx, bzy, bz + 1.05), 0.42, 12, MIRON, "BY_SHED"))
for a in range(3):
    th = a * 2.09
    BZ.append(beam("bz_leg", (bzx + math.cos(th) * 0.34, bzy + math.sin(th) * 0.34, bz),
                   (bzx, bzy, bz + 0.62), 0.09, 0.09, MIRON, "BY_SHED"))
BZ.append(cyl("bz_coal", (bzx, bzy, bz + 0.94), (bzx, bzy, bz + 1.06), 0.34, 12, M("mat_embers"), "BY_SHED"))
join_meshes(BZ, "shed_brazier", "BY_SHED")
bzl = bpy.data.lights.new("shed_brazier_light", 'POINT')
bzl.energy, bzl.color, bzl.shadow_soft_size = 130.0, (1.0, 0.52, 0.20), 0.35
bzo = bpy.data.objects.new("shed_brazier_light", bzl)
link(bzo, "BY_LIGHT")
bzo.location = (bzx, bzy, bz + 1.25)

join_meshes(W, "shed_bench_clutter", "BY_SHED")


# ===========================================================================
# 9. pitch kettle + smoke  (north of the slipway pad, clear of the corridor)
# ===========================================================================
KX, KY = 24.15, 31.75
kettle = bake_group([P["pitch_kettle"], P["v10_embers"], P["v10_gallows"], P["v10_kettle_smoke"]],
                    rz=0.0, prefix="k_", cname="BY_KETTLE")
anchor_group(kettle, kettle[0], (KX, KY, ground_z(KX, KY) + 0.04), "cxy_minz")
print("kettle bb", ["%.2f" % v for v in world_bbox(kettle[0])])
kfire = place(P["kettle_fire"], (KX - 0.10, KY - 0.55, ground_z(KX, KY) + 0.55), name="kettle_fire", cname="BY_KETTLE")
smoke = place(P["v10_kettle_smoke"], (KX + 0.1, KY + 0.2, ground_z(KX, KY) + 1.25), mode="cxy_minz",
              name="kettle_smoke_plume", cname="BY_KETTLE")
smoke.scale = (1.0, 1.0, 1.0)
# tar barrels and a pitch mop beside it
for i, (bx, by) in enumerate(((23.0, 32.2), (23.6, 32.6), (25.6, 31.2))):
    place(P["kit_barrel"], (bx, by, ground_z(bx, by)), rz=rng.random() * 3,
          name="tar_barrel%d" % i, cname="BY_KETTLE")


# ===========================================================================
# 10. cargo winch (foot) + the cableway up to the gate tier
# ===========================================================================
V = []
WFX, WFY = 30.0, 24.0
for dx, dy in ((-1.55, -1.5), (1.55, -1.5), (-1.55, 1.5), (1.55, 1.5)):
    px, py = WFX + dx, WFY + dy
    if not free(px, py, 1.4):
        nb = COR.find_free(px, py, 1.4, radius=1.5)
        if nb:
            px, py = nb
    V.append(beam("wn_post", (px, py, ground_z(px, py) - 0.2), (px, py, 5.6), 0.30, 0.30, MT, "BY_WINCH"))
V.append(beam("wn_head", (WFX - 1.75, WFY - 1.5, 5.6), (WFX + 1.75, WFY - 1.5, 5.6), 0.26, 0.34, MT, "BY_WINCH"))
V.append(beam("wn_head", (WFX - 1.75, WFY + 1.5, 5.6), (WFX + 1.75, WFY + 1.5, 5.6), 0.26, 0.34, MT, "BY_WINCH"))
V.append(beam("wn_head", (WFX, WFY - 1.7, 5.85), (WFX, WFY + 1.7, 5.85), 0.26, 0.34, MT, "BY_WINCH"))
V.append(cyl("wn_drum", (WFX - 0.9, WFY, 5.35), (WFX + 0.9, WFY, 5.35), 0.46, 14, MT, "BY_WINCH"))
V.append(cyl("wn_sheave", (WFX - 0.16, WFY - 1.5, 6.05), (WFX + 0.16, WFY - 1.5, 6.05), 0.42, 14, MIRON, "BY_WINCH"))
# the cable running up the cliff to the gate-tier winch head
V.append(cyl("wn_cable", (WFX - 0.2, WFY - 1.5, 6.0), (28.7, 10.0, 25.0), 0.055, 6, MIRON, "BY_WINCH"))
V.append(cyl("wn_cable2", (WFX + 0.2, WFY - 1.5, 5.9), (29.1, 10.0, 24.6), 0.045, 6, MIRON, "BY_WINCH"))
# a laden pallet hanging on the cable, caught in the light
V.append(box("wn_load", 29.3, 30.7, 21.2, 22.4, 4.4, 5.0, MT, "BY_WINCH"))
V.append(cyl("wn_bridle", (30.0, 21.8, 5.0), (29.85, 21.35, 6.35), 0.04, 5, MIRON, "BY_WINCH"))
join_meshes(V, "cargo_winch_foot", "BY_WINCH")


# ===========================================================================
# 11. railings, bollards, ladders, clutter
# ===========================================================================
def railing_run(name, pts, h=0.94, step=1.80, mat=None, parts=None):
    mat = mat or MT
    parts = parts if parts is not None else []
    total = 0.0
    segs = []
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        segs.append((a, b, (b - a).length))
        total += (b - a).length
    n = max(2, int(total / step) + 1)
    for i in range(n + 1):
        d = total * i / n
        acc = 0.0
        for a, b, ln in segs:
            if acc + ln >= d or (a, b, ln) is segs[-1]:
                t = min(1.0, (d - acc) / max(ln, 1e-6))
                p = a.lerp(b, t)
                parts.append(beam(name + "_post", (p.x, p.y, p.z - 0.28), (p.x, p.y, p.z + h),
                                  0.105, 0.105, mat, "BY_RAIL"))
                break
            acc += ln
    for a, b, ln in segs:
        for hz in (h, h * 0.52):
            parts.append(beam(name + "_rail", (a.x, a.y, a.z + hz), (b.x, b.y, b.z + hz),
                              0.09, 0.13, mat, "BY_RAIL"))
    return parts


RA = []
# boardwalk to the overlook — railing on both sides, 0.32 outside the ribbon
railing_run("bw_n", [(15.49, 29.25, 2.53), (12.84, 29.84, 2.96), (8.84, 30.78, 3.76)], parts=RA)
railing_run("bw_s", [(12.50, 27.16, 2.96), (8.50, 27.12, 3.76)], parts=RA)
# overlook parapet rail on the quay cap
railing_run("ov_n", [(6.4, 30.90, 3.76), (11.6, 30.90, 3.76)], parts=RA)
railing_run("ov_w", [(6.4, 30.90, 3.76), (6.4, 27.3, 3.76)], parts=RA)
# slipway pad's outboard arc (over the water)
arc = []
for k in range(7):
    a = math.radians(46 + k * 15)
    arc.append((19.33 + math.cos(a) * 4.85, 27.0 + math.sin(a) * 4.85, 2.18))
railing_run("slip_arc", arc, parts=RA)
# staging edges
join_meshes(RA, "yard_railings", "BY_RAIL")

# bollards / cleats / mooring posts along the water edge
BO = []
for (bx, by) in ((20.3, 31.6), (22.6, 31.6), (24.6, 31.7), (27.4, 31.5), (30.6, 31.5),
                 (16.6, 31.1), (32.4, 29.0)):
    if free(bx, by, 2.4):
        gz = ground_z(bx, by)
        BO.append(cyl("bollard", (bx, by, gz - 0.25), (bx, by, gz + 0.62), 0.15, 8, MT, "BY_PROPS"))
        BO.append(cyl("bollard_cap", (bx, by, gz + 0.62), (bx, by, gz + 0.76), 0.20, 8, MIRON, "BY_PROPS"))
join_meshes(BO, "yard_bollards", "BY_PROPS")

# working clutter harvested from the accepted probe (barrels, ropes, crates, tools)
CLUT = [
    ("yard_clutter", (17.4, 20.3), 0.0),
    ("v10_foreclutter", (33.4, 30.4), 0.0),
    ("v10_redcrates", (22.4, 32.1), math.radians(90)),
    ("v10_apron", (11.0, 20.6), 0.0),
]
for nm, (tx, ty), rz in CLUT:
    if nm in P:
        place(P[nm], (tx, ty, ground_z(tx, ty)), rz=rz, name="by_" + nm, cname="BY_PROPS")

props = []
for i in range(44):
    kind = rng.choice(["kit_barrel", "kit_crate", "kit_rope_coil", "kit_bucket"])
    for _ in range(24):
        px = 13.5 + rng.random() * 20.0
        py = 20.2 + rng.random() * 13.0
        base = ground_z(px, py)
        if base < WATER_MID + 0.15:
            continue
        if not free(px, py, base + 0.5):
            continue
        props.append(place(P[kind], (px, py, base), rz=rng.random() * 6.28,
                           name="prop_%s_%d" % (kind[4:], i), cname="BY_PROPS"))
        break
print("PROPS scattered:", len(props))

FG = []
# a stack of freshly sawn boards on trestles, near-right on the hard
sx, sy = 33.2, 29.8
gz0 = ground_z(sx, sy)
for dx in (-1.5, 1.5):
    for dy in (-0.55, 0.55):
        FG.append(beam("fg_tr", (sx + dx + dy * 0.35, sy + dy, gz0 - 0.1),
                       (sx + dx, sy + dy * 0.2, gz0 + 0.62), 0.11, 0.11, MT, "BY_PROPS"))
    FG.append(beam("fg_trtop", (sx + dx, sy - 0.75, gz0 + 0.66), (sx + dx, sy + 0.75, gz0 + 0.66),
                   0.16, 0.13, MT, "BY_PROPS"))
for k in range(7):
    FG.append(beam("fg_board", (sx - 2.4 + rng.random() * 0.3, sy - 0.55 + (k % 4) * 0.30,
                                gz0 + 0.72 + (k // 4) * 0.075),
                   (sx + 2.5 + rng.random() * 0.3, sy - 0.5 + (k % 4) * 0.30,
                    gz0 + 0.74 + (k // 4) * 0.075), 0.26, 0.06, MFRESH, "BY_PROPS"))
# a spar leaning against the shed
FG.append(beam("fg_spar", (28.9, 21.8, ground_z(28.9, 21.8)), (27.4, 23.6, 4.4), 0.17, 0.17, MT, "BY_PROPS"))
FG.append(beam("fg_spar2", (29.3, 22.3, ground_z(29.3, 22.3)), (27.7, 23.9, 4.1), 0.14, 0.14, MT, "BY_PROPS"))
join_meshes(FG, "foreground_timber", "BY_PROPS")


# ===========================================================================
# 12. lanterns, bunting, painted colour
# ===========================================================================
LP = []
lantern_spots = [(22.6, 21.95, 4.85), (26.9, 21.95, 4.85), (24.4, 22.35, 5.15),
                 (13.1, 26.75, 5.55), (15.1, 29.85, 5.55),
                 (16.30, 31.60, 6.35), (16.30, 40.80, 6.35), (16.30, 36.20, 6.35),
                 (31.4, 25.90, 5.30), (23.6, 32.30, 3.05), (9.6, 30.05, 6.05)]
for i, (lx, ly, lz) in enumerate(lantern_spots):
    nb = (lx, ly)
    if not free(lx, ly, lz - 0.9):
        pass  # hanging lanterns are above head height by construction
    lan = place(P["kit_lantern_hanging"], (lx, ly, lz), mode="cxy_maxz",
                name="lantern_%d" % i, cname="BY_LIGHT")
    li = P["kit_lantern_light"].copy()
    li.data = P["kit_lantern_light"].data.copy()
    li.name = "lantern_light_%d" % i
    li.location = (lx, ly, lz - 0.22)
    link(li, "BY_LIGHT")
    # the bracket it hangs from
    LP.append(beam("lan_arm", (lx, ly, lz + 0.30), (lx, ly, lz + 0.62), 0.07, 0.07, MIRON, "BY_LIGHT"))
join_meshes(LP, "lantern_brackets", "BY_LIGHT")

# bunting strung across the yard (well above the 2 m corridor headroom)
for i, bx in enumerate((20.4, 24.2)):
    b = place(P["v10_bunting"], (bx, 26.4 + (i % 2) * 0.6, 6.15 - i * 0.15), rz=0.0,
              mode="cxy_cz", name="bunting_%d" % i, cname="BY_LIGHT")
# bunting masts, only where the corridor allows
BM = []
for (mx, my) in ((20.6, 21.6), (24.5, 21.6),
                 (20.4, 31.6), (24.4, 31.9)):
    if free(mx, my, 3.0):
        BM.append(beam("mast", (mx, my, ground_z(mx, my) - 0.3), (mx, my, 6.9), 0.19, 0.19, MT, "BY_LIGHT"))
join_meshes(BM, "bunting_masts", "BY_LIGHT")



# a splash of painted timber variety on the shed gable + hull topsides
place(P["v10_paintwork"], (24.8, 20.55, 6.05), rz=math.radians(90), mode="cxy_cz",
      name="shed_paintwork", cname="BY_SHED")


# ===========================================================================
# 13. vegetation
# ===========================================================================
VEG = []


def scatter(proto, spots, rzr=6.28, sc=(1.0, 1.0, 1.0), cname="BY_VEG", tag="v"):
    for i, (x, y, z) in enumerate(spots):
        s = sc if isinstance(sc, tuple) else (sc, sc, sc)
        j = 0.82 + rng.random() * 0.5
        o = place(proto, (x, y, z), rz=rng.random() * rzr,
                  scale=(s[0] * j, s[1] * j, s[2] * j), mode="cxy_minz",
                  name="%s_%d" % (tag, i), cname=cname)
    return


# creepers hanging down the cliff face on the left of frame
creep = []
for k in range(26):
    cx = 2.0 + rng.random() * 30.0
    cz = 4.2 + rng.random() * 7.5
    creep.append((cx, 19.55 + rng.random() * 0.55, cz))
for i, (cx, cy, cz) in enumerate(creep):
    proto = P["v10_src_creeper_a"] if i % 2 == 0 else P["v10_src_creeper_b"]
    place(proto, (cx, cy, cz), rz=math.radians(180) + (rng.random() - 0.5) * 0.6,
          scale=0.8 + rng.random() * 0.6, mode="cxy_maxz",
          name="creeper_%d" % i, cname="BY_VEG")
# canopy clumps on the cliff shoulder above
for i in range(15):
    cx = 1.0 + rng.random() * 25.0
    place(P["v10_src_clump_a"] if i % 2 else P["v10_src_clump_b"],
          (cx, 18.9 + rng.random() * 1.1, 9.5 + rng.random() * 5.0),
          rz=rng.random() * 6.28, scale=1.1 + rng.random() * 0.8, mode="cxy_cz",
          name="rimclump_%d" % i, cname="BY_VEG")
# a couple of real trees where they read
for i, (tx, ty, tz) in enumerate(((9.0, 19.2, 11.6), (24.0, 19.0, 13.4))):
    place(P["v10_src_tree_b"], (tx, ty, tz), rz=rng.random() * 6.28,
          scale=1.25, mode="cxy_minz", name="rimtree_%d" % i, cname="BY_VEG")
# far autumn crowns along the upstream ridge
for i in range(22):
    rx = -122.0 + rng.random() * 78.0
    place(P["v10_src_clump_far"], (rx, 26.0 + rng.random() * 16.0, 12.0 + rng.random() * 7.0),
          rz=rng.random() * 6.28, scale=2.2 + rng.random() * 1.6, mode="cxy_cz",
          name="farcrown_%d" % i, cname="BY_VEG")
# autumn crowns along the far gorge wall across the river
for i in range(18):
    rx = -14.0 + rng.random() * 52.0
    place(P["v10_src_clump_far"], (rx, 55.0 + rng.random() * 4.0, 15.4 + rng.random() * 2.4),
          rz=rng.random() * 6.28, scale=1.6 + rng.random() * 1.2, mode="cxy_cz",
          name="farwallcrown_%d" % i, cname="BY_VEG")
# ferns / grass along the deck edges and the bank
for i in range(46):
    for _ in range(20):
        gx = 3.0 + rng.random() * 29.0
        gy = 19.4 + rng.random() * 13.0
        gz = ground_z(gx, gy)
        if gz < WATER_MID + 0.10:
            continue
        base = gz
        if not free(gx, gy, base + 0.4):
            continue
        place(P["v10_src_tuft_fern"] if i % 2 else P["v10_src_tuft_grass"],
              (gx, gy, base), rz=rng.random() * 6.28, scale=0.9 + rng.random() * 0.7,
              mode="cxy_minz", name="tuft_%d" % i, cname="BY_VEG")
        break


# ===========================================================================
# 14. moored barge with pumpkins in the calm upper pool
# ===========================================================================
for i, (nm, tx, ty, rz) in enumerate((("v10_barge_mid", 5.0, 33.2, math.radians(4)),
                                      ("v10_barge_port", -3.5, 35.4, math.radians(12)))):
    if nm in P:
        place(P[nm], (tx, ty, WATER_UP - 0.28), rz=rz, mode="cxy_minz",
              name="barge_%d" % i, cname="BY_PROPS")
# a working barge below the dam too
place(P["v10_barge_stbd"], (19.4, 40.0, WATER_MID - 0.28), rz=math.radians(-8),
      mode="cxy_minz", name="barge_mid_pool", cname="BY_PROPS")

# a chandlery + net loft further downstream, holding the right-hand skyline
place(P["v10_chandlery"], (4.6, 22.4, 2.60), rz=math.radians(90),
      name="lockside_chandlery", cname="BY_STRUCT")
place(P["v10_netloft"], (11.5, 19.8, 3.30), rz=math.radians(180),
      name="bank_netloft", cname="BY_STRUCT")

# a figure for scale, on the boardwalk (rendered — it is the boatwright)
place(P["REF_human_1p7"], (18.6, 21.3, ground_z(18.6, 21.3)), name="REF_human_scale", cname="BY_PROPS")


# ===========================================================================
# 15. lighting, fog, haze, camera
# ===========================================================================
LIGHT_RIG = {
    # name: (position, aim)   -- see NOTE below
    "SUN_key":     ((52.0, 41.0, 17.5), (18.0, 27.0, 2.6)),
    "FILL_bounce": ((30.0, 42.0, 3.8), (22.0, 27.5, 2.2)),
    "RIM_gorge":   ((-4.0, 30.0, 8.0), (20.0, 27.5, 3.6)),
}
# NOTE (deviation from the probe rig, and why): mapping the probe rig through
# R90 puts the key over the camera's LEFT shoulder — which in true town coords
# is the town cliff (y < 19, ~28 u tall, 6 u away).  It shadows the entire yard:
# clearing it needs 77 deg of elevation, i.e. noon.  The key therefore mirrors
# to the river side (screen-right), keeping the probe's 22 deg elevation and
# 3/4 relationship to the camera; a warm CLIFF_BOUNCE area replaces the light
# the cliff would really throw back, so camera-facing planes still model.
for nm, (pos, aimp) in LIGHT_RIG.items():
    src = P[nm]
    ob = src.copy()
    ob.data = src.data.copy()
    ob.name = nm
    link(ob, "BY_LIGHT")
    ob.location = Vector(pos)
    ob.rotation_euler = (Vector(aimp) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    print("LIGHT %-12s at (%.1f, %.1f, %.1f)  elev %.1f deg" %
          (nm, pos[0], pos[1], pos[2],
           math.degrees(math.asin((pos[2] - aimp[2]) /
                                  max((Vector(pos) - Vector(aimp)).length, 1e-6)))))

# ---------------------------------------------------------------------------
# THE DUSK SPLIT.  v3 ran an all-warm rig — a 9.0 amber sun, a 780 W amber
# gorge rim and a 260 W amber cliff bounce against a single 185 W cool fill —
# so every plane in the shot resolved to the same orange and the picture came
# out amber-monochrome.  probe_v11's warm/cool contrast comes from the balance,
# not the intensity: warm light only where the sun and the lanterns actually
# reach, and a cool blue-grey sky wash carrying every shadow.
for ob in bpy.data.objects:
    if ob.type != 'LIGHT' or ob.hide_render:
        continue
    if ob.name.startswith("SUN_key"):
        # The key had to be mirrored to the river side (see the NOTE above), which
        # means it FRONT-lights the whole yard.  At 9.0 it was a floodlight: every
        # surface the camera could see came back at the same midtone, which is what
        # "uniform timber soup" actually was.  At dusk the sun is a low grazing
        # rake and the practicals carry the scene, so it drops most of a stop.
        ob.data.energy = 5.0
        ob.data.color = (1.0, 0.545, 0.275)
    elif ob.name.startswith("RIM_gorge"):
        ob.data.energy = 700.0                   # backlights the dam: silhouette, not wash
        ob.data.color = (1.0, 0.535, 0.265)
    elif ob.name.startswith("FILL_bounce"):
        # this one faces UPSTREAM, so every watt lands on the downstream face of
        # Lock Four.  At 430 it was single-handedly painting the dam grey.
        ob.data.energy = 185.0
        ob.data.color = (0.285, 0.370, 0.620)

# the warm cliff bounce is the single biggest reason v3 read as timber soup: at
# 260 W it lit every camera-facing plane to the same midtone.  It survives only
# to keep the right-hand structures from going flat.
cb_d = bpy.data.lights.new("CLIFF_BOUNCE", 'AREA')
cb_d.shape = 'RECTANGLE'
cb_d.size, cb_d.size_y = 14.0, 7.0
cb_d.energy = 120.0
cb_d.color = (1.0, 0.66, 0.42)
cbo = bpy.data.objects.new("CLIFF_BOUNCE", cb_d)
link(cbo, "BY_LIGHT")
cbo.location = Vector((28.0, 18.6, 8.2))
cbo.rotation_euler = (Vector((21.0, 28.0, 3.0)) - cbo.location).to_track_quat('-Z', 'Y').to_euler()

# SKY_wash — a wide, cool, top-down source standing in for the open dusk sky.
# This is what puts blue-grey into the shadow side and splits the palette.
sw_d = bpy.data.lights.new("SKY_wash", 'AREA')
sw_d.shape = 'RECTANGLE'
sw_d.size, sw_d.size_y = 46.0, 34.0
# 900 W of this lifted every shadow in the frame to the same value and washed
# the colour out — a cool wash has to TINT the shadows, not fill them.
sw_d.energy = 250.0
# blue-GREY, not blue: a saturated blue wash pushed the shadow/highlight hue
# split to +0.115 against the reference's +0.063 — cool shadows, not blue ones.
sw_d.color = (0.50, 0.515, 0.625)
swo = bpy.data.objects.new("SKY_wash", sw_d)
link(swo, "BY_LIGHT")
swo.location = Vector((24.0, 30.0, 26.0))
swo.rotation_euler = (Vector((21.0, 30.0, 2.0)) - swo.location).to_track_quat('-Z', 'Y').to_euler()

# KEY_slip — the focal diagonal.  The slipway hard and the hull standing on it
# run from the lower middle of frame up to the lock; v3 gave them no more light
# than the surrounding timber, so the eye had nothing to follow.  A single
# raking spot makes that run the lightest path through the picture.
ks_d = bpy.data.lights.new("KEY_slip", 'SPOT')
ks_d.energy = 5400.0
ks_d.color = (1.0, 0.795, 0.565)
ks_d.spot_size = math.radians(48.0)
ks_d.spot_blend = 0.62
ks_d.shadow_soft_size = 1.8
kso = bpy.data.objects.new("KEY_slip", ks_d)
link(kso, "BY_LIGHT")
# placed off the key axis and high, so the cone rakes the slipway hard, the hull
# standing on it AND the hero hull's camera-facing flank — one continuous light
# path from the lower middle of frame up to the lock.
kso.location = Vector((44.0, 36.0, 16.0))
kso.rotation_euler = (Vector((23.0, 30.5, 2.6)) - kso.location).to_track_quat('-Z', 'Y').to_euler()

# lantern pools stay warm, but 11 x 300 W was itself a wash — pull them back so
# each one reads as a local pool instead of general amber ambience
_nlan = 0
for ob in bpy.data.objects:
    if ob.type == 'LIGHT' and ob.name.startswith("lantern_light_") and not ob.hide_render:
        ob.data.energy = 680.0
        ob.data.shadow_soft_size = 0.13
        _nlan += 1
print("LANTERNS retuned:", _nlan)

# deepen the sky gradient behind the rim and cool the ambient it contributes
_w = sc.world
if _w and _w.use_nodes:
    for n in _w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            n.inputs["Strength"].default_value = 1.60
        elif n.type == 'VALTORGB' and len(n.color_ramp.elements) >= 5:
            e = n.color_ramp.elements
            e[0].color = (0.135, 0.052, 0.030, 1)     # hot band right on the horizon
            e[1].color = (0.62, 0.215, 0.062, 1)
            e[2].color = (0.255, 0.118, 0.140, 1)
            e[3].color = (0.098, 0.084, 0.152, 1)     # deep violet-blue mid sky
            e[4].color = (0.030, 0.034, 0.078, 1)     # near-night at the zenith
            print("WORLD ramp deepened (%d stops)" % len(e))

fog = place(P["FOG_BOX"], (-10.0, 26.0, 14.0), mode="cxy_cz", name="FOG_BOX", cname="BY_LIGHT")
print("FOG_BOX bb", ["%.0f" % v for v in world_bbox(fog)])
for nm, tx in (("v10_haze_mid", -35.0), ("v10_haze_far", -62.0), ("v10_haze_rim", -100.0)):
    place(P[nm], (tx, 28.0, 8.0), mode="cxy_cz", name=nm, cname="BY_LIGHT")

# camera — low along the yard looking UPSTREAM, Lock Four closing the view.
AIM = Vector((14.4, 30.40, 3.40))
CAMPOS = Vector((37.6, 25.40, 8.50))
cd = bpy.data.cameras.new("cam_boatyard")
cd.type = 'PERSP'
cd.sensor_fit = 'VERTICAL'
cd.angle_y = math.radians(35.0)
cd.clip_start = 0.05
cd.clip_end = 600.0
cam = bpy.data.objects.new("cam_boatyard", cd)
link(cam, "BY_CAM")
cam.location = CAMPOS
cam.rotation_euler = (AIM - CAMPOS).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
d = (CAMPOS - AIM)
print("CAMERA dist=%.2f  yaw=%.1f  pitch=%.1f  vh=%.1f" %
      (d.length, math.degrees(math.atan2(d.y, d.x)),
       math.degrees(math.asin(d.z / d.length)),
       2 * d.length * math.tan(math.radians(17.5))))

# ---- automatic corridor sweep: anything scattered that ended up inside a
#      walk corridor is deleted outright (playability beats dressing) ---------
SWEEP = Corridor(walk_keep)
culled = []
for ob in list(bpy.data.objects):
    if ob.type != 'MESH' or ob.name.startswith("walk_"):
        continue
    if not ob.name.startswith(("prop_", "tuft_", "tar_barrel", "creeper_", "lantern_",
                               "rimclump_", "by_", "barge_", "REF_human")):
        continue
    Mx = ob.matrix_basis
    if any(SWEEP.blocked(Mx @ v.co) for v in ob.data.vertices):
        culled.append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)
print("CORRIDOR SWEEP culled %d scattered objects: %s" % (len(culled), culled))

# ---- drop the massing references now that everything is replaced ----------
for ob in list(coll("REF_MASSING").objects):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.collections.remove(coll("REF_MASSING"))

# ---- render settings ------------------------------------------------------
sc.render.engine = "CYCLES"
sc.cycles.samples = 224
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8
sc.cycles.volume_bounces = 2
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.view_settings.view_transform = "AgX"
# match the grade of the quality reference (docs/qa/dellhollow-rebuild/probe_v11):
# High Contrast was crushing the shadow separation and over-saturating the key,
# which fed the amber-monochrome read.  Keep this in step with boatyard_render.py.
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = -0.52

os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("SAVED", OUT_BLEND)
print("OBJECTS", len(bpy.data.objects))
