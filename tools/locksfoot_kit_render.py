"""locksfoot_kit_render.py — taste-check renders of the Locksfoot prep kit.

  Blender -b tools/blends/districts/locksfoot-kit.blend -P tools/locksfoot_kit_render.py

READ-ONLY on the kit blend (manifest 63: `-b file.blend -P script.py` never saves
unless the script says so, and this one never does).  Every assembly is INSTANCED
into a throwaway stage scene, lit with the district rig's discipline (a warm 3/4 key
from over the camera's shoulder at ~22 deg, a cool river bounce, a warm rim), and
shot through render_util's AgX conventions.

EEVEE, per the brief.  Note the standing caveat (manifest 70): EEVEE's shadow budget
makes it unrepeatable past ~40 lamps, so it is fine for a 6-lamp kit stage and NOT
fine for a value judgement inside the master — those stay in Cycles.

Writes docs/qa/districts/locksfoot_kit_<shot>.png
"""
import bpy, math, os, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
import render_util as RU

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
QA = os.path.join(ROOT, "docs/qa/districts")
SRC = {o.name: o for o in bpy.data.objects}
ONLY = None
if "--" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--") + 1:]) or None

STAGE = bpy.data.collections.new("STAGE")


def put(src, loc=(0, 0, 0), rz=0.0, rx=0.0, name=None):
    o = SRC[src].copy()
    o.data = SRC[src].data          # linked duplicate: one mesh, many placements
    o.name = name or (src + "_i")
    o.location = loc
    o.rotation_euler = (rx, 0.0, rz)
    STAGE.objects.link(o)
    return o


def flat(name, rgb, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


MGROUND = flat("stage_ground", (0.030, 0.023, 0.016))
MWATER = flat("stage_water", (0.013, 0.048, 0.048), rough=0.09)
MDECK = flat("stage_deck", (0.052, 0.036, 0.021))


def slab(name, x0, x1, y0, y1, z, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    STAGE.objects.link(o)
    return o


def wall(name, verts, mat=MGROUND):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    STAGE.objects.link(bpy.data.objects.new(name, me))


def plank_deck(name, x0, x1, y0, y1, z, pw=0.30, gap=0.014, t=0.10):
    """A real plank deck for the stage, so a quay does not read as a card."""
    vs, fs, s = [], [], y0
    while s < y1 - 1e-4:
        w = min(pw, y1 - s)
        b = len(vs)
        for (xa, ya) in ((x0, s), (x1, s), (x1, s + w - gap), (x0, s + w - gap)):
            vs.append((xa, ya, z))
        for (xa, ya) in ((x0, s), (x1, s), (x1, s + w - gap), (x0, s + w - gap)):
            vs.append((xa, ya, z - t))
        fs += [(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4),
               (b + 4, b + 5, b + 1, b), (b + 5, b + 6, b + 2, b + 1),
               (b + 6, b + 7, b + 3, b + 2), (b + 7, b + 4, b, b + 3)]
        s += w
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.materials.append(MDECK)
    STAGE.objects.link(bpy.data.objects.new(name, me))


def clear():
    for o in list(STAGE.objects):
        bpy.data.objects.remove(o, do_unlink=True)


# --------------------------------------------------------------------- light
def rig(key_from, target, level=1.0, sky=1.0):
    """The district rig in miniature: a 3/4 key from over the camera's shoulder at
    ~22 deg (probe finding 5/11), a cool area bounce off the river so the shadows
    are not black, and a warm rim to lift the silhouettes off the background."""
    lamps = []

    def lamp(name, kind, loc, aim, energy, colour, size=6.0, spot=None):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = colour
        if kind == "AREA":
            ld.size = size
        if kind == "SUN":
            ld.angle = math.radians(2.6)
        if spot:
            ld.spot_size, ld.spot_blend = spot, 1.0
        o = bpy.data.objects.new(name, ld)
        o.location = loc
        RU.aim(o, aim)
        STAGE.objects.link(o)
        lamps.append(o)
        return o

    lamp("SUN_key", "SUN", key_from, target, 5.8 * level, (1.0, 0.73, 0.48))
    lamp("FILL_river", "AREA", (target[0] + 10, target[1] - 15, target[2] + 5), target,
         1750 * level * sky, (0.46, 0.66, 0.80), size=20)
    lamp("RIM_warm", "AREA", (target[0] - 14, target[1] + 13, target[2] + 10), target,
         980 * level, (1.0, 0.76, 0.50), size=12)
    lamp("AMB_low", "AREA", (target[0], target[1], target[2] + 17), target,
         1150 * level * sky, (0.62, 0.60, 0.74), size=30)
    return lamps


def world():
    """A banded sky, not a flat wall.  Manifest 10: a ColorRamp's first stop paints
    the WHOLE lower hemisphere, so the ember goes in a thin band at the elevation
    the camera sees and everything below it stays dark."""
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs[1].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs[0])
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.00, (0.040, 0.030, 0.030, 1)     # the ground half
    e[1].position, e[1].color = 0.498, (0.150, 0.090, 0.060, 1)
    for pos, col in ((0.512, (1.40, 0.72, 0.32, 1)),               # the ember band
                     (0.560, (0.90, 0.44, 0.20, 1)),
                     (0.640, (0.34, 0.21, 0.16, 1)),
                     (0.780, (0.090, 0.085, 0.110, 1)),
                     (1.00, (0.024, 0.030, 0.058, 1))):            # deep blue zenith
        el = ramp.color_ramp.elements.new(pos)
        el.color = col


def shoot(name, cam_loc, look, lens=35.0, exposure=0.30):
    RU.setup_eevee(res=(1344, 768))
    sc = bpy.context.scene
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = exposure
    if hasattr(sc, "eevee"):
        for a, v in (("taa_render_samples", 96), ("use_raytracing", True),
                     ("use_shadows", True), ("use_volumetric_lights", False)):
            if hasattr(sc.eevee, a):
                setattr(sc.eevee, a, v)
    cam = RU.make_camera("cam_" + name, cam_loc, look, lens=lens, coll=STAGE)
    sc.camera = cam
    p = os.path.join(QA, "locksfoot_kit_%s.png" % name)
    RU.render_to(p)
    print("  ->", p)


# ===========================================================================
def shot_lock():
    """Lock machinery at the chamber: a mitred pair of gates hung on their heel
    posts, the winding gear and a sluice paddle on the quay, a capstan for warping
    the barge in, and the spare low leaf leaning where a lock keeper would keep it."""
    clear()
    world()
    CW, FLOOR, UP, DN = 3.05, -3.40, -0.70, -2.55
    plank_deck("quayS", -24, 20, -16, -CW, 0.0)
    plank_deck("quayN", -24, 20, CW, 16, 0.0)
    slab("floor", -24, 20, -CW, CW, FLOOR, MGROUND)
    for sy in (-1, 1):
        wall("chamber%d" % sy, [(-24, sy * CW, FLOOR), (20, sy * CW, FLOOR),
                                (20, sy * CW, 0.0), (-24, sy * CW, 0.0)])
    slab("w_up", -24, 1.30, -CW, CW, UP, MWATER)
    slab("w_dn", 1.30, 20, -CW, CW, DN, MWATER)
    # the mitre pair, closing UPSTREAM (-X) as a mitre gate must
    put("lf_gate_leaf", (1.30, -CW, FLOOR), rz=math.radians(20))
    put("lf_gate_leaf", (1.30, CW, FLOOR), rz=math.radians(160))
    put("lf_gate_winch", (2.95, -CW - 0.62, 0.0), rz=math.radians(-96))
    put("lf_gate_winch", (2.95, CW + 0.62, 0.0), rz=math.radians(96))
    put("lf_sluice_paddle", (-1.20, -CW + 0.02, FLOOR + 0.10), rz=math.radians(-90))
    put("lf_capstan", (6.2, -CW - 1.35, 0.0))
    put("lf_bollard", (9.2, -CW - 0.75, 0.0))
    put("lf_bollard", (-2.6, -CW - 0.80, 0.0))
    put("lf_rope_coil", (7.6, -CW - 1.95, 0.0))
    put("lf_lantern_post", (4.4, -CW - 0.58, 0.0), rz=math.radians(120))
    put("lf_lantern_post", (-3.4, CW + 0.58, 0.0), rz=math.radians(-60))
    put("lf_gate_leaf_low", (-9.6, -CW - 3.35, 0.0), rz=math.radians(-6), rx=math.radians(-74))
    put("lf_crate", (-4.4, -CW - 1.95, 0.0), rz=math.radians(14))
    put("lf_barrel", (-3.3, -CW - 2.45, 0.0))
    put("lf_cargo_stack", (11.2, -CW - 1.60, 0.0), rz=math.radians(-40))
    put("lf_barge", (10.4, 0.10, DN), rz=math.radians(184))
    put("REF_human_1p7", (6.9, -CW - 0.70, 0.0), rz=math.radians(210))
    put("lf_bunting_swag", (-1.2, -CW - 0.20, 3.30), rz=math.radians(2))
    rig((27, -23, 12), (2.0, -0.5, -0.6), level=1.05, sky=1.10)
    shoot("lock", (16.2, -1.30, 0.95), (1.9, 0.15, -0.75), lens=34, exposure=0.45)


def shot_wheels():
    """The three wheel variants + the pillow block they run in."""
    clear()
    world()
    slab("ground", -14, 14, -12, 12, 0.0, MGROUND)
    slab("water", -14, 14, -12, 12, 0.55, MWATER)
    for nm, x, z in (("lf_wheel_breast_wide", -5.4, 2.90),
                     ("lf_wheel_breast", 0.4, 2.55),
                     ("lf_wheel_undershot", 5.1, 1.85)):
        put(nm, (x, 0, z), rz=math.radians(90))
        put("lf_wheel_bearing", (x, -1.10 if "wide" in nm else -0.95, z), rz=math.radians(90))
        put("lf_wheel_bearing", (x, 1.10 if "wide" in nm else 0.95, z), rz=math.radians(90))
    put("REF_human_1p7", (8.6, -1.2, 0.0), rz=math.radians(170))
    put("lf_barrel", (-8.6, -1.0, 0.0))
    rig((-12, -20, 13), (0.0, 0.0, 2.4), level=1.05)
    shoot("wheels", (2.0, -16.5, 4.4), (0.0, 0.4, 2.4), lens=42)


def shot_dam():
    """Lock Five in mock-up: crest bays cloned along the crest (manifest 61), three
    spill bays, three breastshot wheels on the black face, the closed crest gate."""
    clear()
    world()
    LEN, DROP = 3.90, 1.80
    n = 7                                   # pier / bay / pier / bay ... like ref 6b
    slab("ground", -60, 60, -40, n * LEN + 40, -5.6, MGROUND)
    slab("head", -60, -1.75, -40, n * LEN + 40, -0.24, MWATER)
    slab("tail", 1.75, 60, -40, n * LEN + 40, -DROP, MWATER)
    for i in range(n):
        if i % 2:
            put("lf_spill_bay", (0, i * LEN + LEN / 2, 0.0), name="spill%d" % i)
        else:
            put("lf_crest_bay", (0, i * LEN, 0.0), name="bay%d" % i)
            if i < 6:                       # a wheel hung on each interior pier
                wy = i * LEN + LEN / 2
                put("lf_wheel_breast", (4.15, wy, -0.45), rz=math.radians(90),
                    name="wheel%d" % i)
                for sy in (-1.02, 1.02):
                    put("lf_wheel_bearing", (4.15, wy + sy, -0.45), rz=math.radians(90),
                        name="bear%d%.0f" % (i, sy))
    put("lf_crest_gate", (0.10, (n - 0.55) * LEN, 0.12), rz=math.radians(90))
    for i in (0, 2, 4):
        put("lf_lantern_post", (-1.34, i * LEN + 1.1, 0.12), rz=math.radians(-90))
    put("lf_cargo_stack", (0.10, 2.0 * LEN + 1.6, 0.12), rz=math.radians(24))
    put("lf_barrel", (0.35, 4.0 * LEN + 0.8, 0.12))
    put("lf_crate", (-0.40, 4.0 * LEN + 1.7, 0.12), rz=math.radians(-18))
    put("lf_bunting_swag", (-1.15, 1.15 * LEN, 3.10), rz=math.radians(90))
    put("REF_human_1p7", (-0.35, 2.0 * LEN + 0.4, 0.12), rz=math.radians(150))
    put("lf_barge", (-7.4, 5.1 * LEN, -0.24), rz=math.radians(96))
    put("lf_cargo_stack", (-7.9, 5.4 * LEN, 0.30), rz=math.radians(96))
    rig((26, -14, 14), (2.0, n * LEN / 2, -0.6), level=1.05, sky=1.15)
    shoot("dam", (22.0, 3.6, 5.4), (0.6, n * LEN * 0.52, -0.75), lens=40, exposure=0.40)


def shot_cottage():
    """Keepers' Cottage from over the basin — the balcony where supper is served,
    its lantern-lit underside (what Locksfoot sees from below), and the tenant's
    shack in oxblood beside it."""
    clear()
    world()
    slab("ground", -34, 34, -26, 6.2, 0.0, MGROUND)
    slab("water", -34, 34, 6.2, 46, -6.6, MWATER)
    for v in ([(-34, 6.2, 0.0), (34, 6.2, 0.0), (34, 6.2, -6.8), (-34, 6.2, -6.8)],):
        wall("spurface", v)
    put("lf_keeper_cottage", (-1.6, 1.05, 0.0))
    put("lf_tenant_shack", (-10.4, -1.2, 0.0), rz=math.radians(28))
    put("lf_lantern_post", (4.4, 3.4, 0.0), rz=math.radians(190))
    put("lf_bunting_swag", (3.2, 5.4, 4.5), rz=math.radians(196))
    put("lf_barrel", (5.2, 1.3, 0.0))
    put("lf_crate", (5.9, 2.2, 0.0), rz=math.radians(18))
    put("lf_rope_coil", (-6.4, 4.4, 0.0))
    put("lf_bollard", (-7.4, 5.2, 0.0))
    put("REF_human_1p7", (2.6, 4.3, 0.0), rz=math.radians(150))
    rig((-20, 24, 13), (0.0, 1.0, 2.0), level=1.0)
    shoot("cottage", (9.6, 14.6, 5.4), (-1.5, 2.2, 1.9), lens=38, exposure=0.22)


def shot_clutter():
    """The dockside set: barge at a moorage, bollards, cargo, lanterns."""
    clear()
    world()
    slab("water", -24, 24, -24, 8, 0.0, MWATER)
    plank_deck("deck", -12, 12, 1.6, 9, 1.15)
    put("lf_barge", (-2.6, -2.3, 0.0), rz=math.radians(6))
    put("lf_barge", (5.6, -4.6, 0.0), rz=math.radians(-9))
    put("lf_cargo_stack", (-3.4, -2.2, 0.52), rz=math.radians(12))
    put("lf_cargo_stack", (5.0, -4.5, 0.52), rz=math.radians(-40))
    for x in (-6.4, -1.0, 4.2, 8.4):
        put("lf_mooring_post", (x, 0.4, 1.15))
    for x, y in ((-7.6, 2.3), (0.6, 2.2), (7.2, 2.4)):
        put("lf_bollard", (x, y, 1.15))
    put("lf_cleat", (-3.2, 2.05, 1.15), rz=math.radians(90))
    put("lf_cleat", (3.4, 2.05, 1.15), rz=math.radians(90))
    put("lf_barrel", (-5.2, 3.3, 1.15))
    put("lf_barrel", (-4.5, 3.9, 1.15))
    put("lf_crate", (1.9, 3.6, 1.15), rz=math.radians(22))
    put("lf_rope_coil", (-1.8, 3.2, 1.15))
    put("lf_capstan", (6.0, 4.2, 1.15))
    put("lf_lantern_post", (-8.8, 3.0, 1.15), rz=math.radians(-70))
    put("lf_lantern_post", (3.0, 3.0, 1.15), rz=math.radians(-100))
    put("lf_bunting_swag", (-8.8, 3.4, 3.4))
    put("lf_tenant_shack", (9.4, 6.4, 1.15), rz=math.radians(-16))
    put("REF_human_1p7", (0.2, 3.9, 1.15), rz=math.radians(-165))
    rig((-14, -20, 11), (0.0, 0.0, 1.4), level=1.0, sky=1.1)
    shoot("clutter", (7.0, -14.6, 4.6), (-1.0, 0.6, 1.4), lens=40)


def shot_crest():
    """Along the dam crest at walking height: the closed crossing gate that bars the
    far shore, the lantern run, bunting, cargo staged on the crest — the walk the
    map promises and the beat the chapter needs (`dam-crest-gate`, state=closed)."""
    clear()
    world()
    LEN, DROP, n = 3.90, 1.80, 8
    slab("ground", -60, 60, -40, n * LEN + 40, -5.6, MGROUND)
    slab("head", -60, -1.75, -40, n * LEN + 40, -0.24, MWATER)
    slab("tail", 1.75, 60, -40, n * LEN + 40, -DROP, MWATER)
    for i in range(n):
        if i % 2:
            put("lf_spill_bay", (0, i * LEN + LEN / 2, 0.0), name="spill%d" % i)
        else:
            put("lf_crest_bay", (0, i * LEN, 0.0), name="bay%d" % i)
    put("lf_crest_gate", (0.05, 2.55 * LEN, 0.12), rz=math.radians(90))
    for i in range(4):
        put("lf_lantern_post", (-1.32, 0.55 * LEN + i * 1.35 * LEN, 0.12), rz=math.radians(-90))
    put("lf_cargo_stack", (0.42, 0.75 * LEN, 0.12), rz=math.radians(70))
    put("lf_barrel", (0.55, 2.6 * LEN, 0.12))
    put("lf_crate", (-0.55, 3.4 * LEN, 0.12), rz=math.radians(20))
    put("lf_rope_coil", (0.55, 4.3 * LEN, 0.12))
    put("lf_bunting_swag", (-1.15, 0.55 * LEN, 3.05), rz=math.radians(90))
    put("lf_bunting_swag", (-1.15, 3.05 * LEN, 3.05), rz=math.radians(90))
    put("REF_human_1p7", (-0.62, 1.85 * LEN, 0.12), rz=math.radians(178))
    rig((-15, -4, 11), (0.0, 2.6 * LEN, 1.0), level=1.0, sky=1.1)
    shoot("crest", (0.30, -2.4, 1.62), (-0.15, 4.2 * LEN, 1.25), lens=34, exposure=0.40)


SHOTS = {"lock": shot_lock, "wheels": shot_wheels, "dam": shot_dam,
         "crest": shot_crest, "cottage": shot_cottage, "clutter": shot_clutter}

bpy.context.scene.collection.children.link(STAGE)
for k in bpy.data.collections:
    if k.name.startswith("LF_"):
        k.hide_render = True                # the library copies stay out of frame

for k, fn in SHOTS.items():
    if ONLY and k not in ONLY:
        continue
    print("SHOT", k)
    fn()
print("done — regenerate the gallery with: python3 tools/make_qa_index.py")
