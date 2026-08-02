"""gate_gorgewall_light.py — THE BLACK VOID IN THE GATE PLATE, NAMED AND LIT.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_gorgewall_light.py -- [save] [--variants base,haze,lit,both] \
      [--energy 3.0] [--out <dir>]

WHAT THE VOID IS.  The user: *"the giant gap in the cliff face is still there."*
The gate plate's top-left quadrant is a large, hard-edged, pure-black region
that reads as a hole punched in the world.  Named on the bake's own oracle
(tools/gate_gorge_census2.py, first-OPAQUE ray-cast at 448x256, hide_render
objects removed from the depsgraph first):

    cliff_east_closure   65.86% of the gate plate's TOP-LEFT QUADRANT
                         16.46% of the whole frame
                         x 140.5..154.1,  125-170 m from the camera
    plate luminance over that region:  median 7.7 / 255  (3%)

**It is not a hole, not a backface and not sky.**  It is the gorge closure wall
— present, correct, 2,205 verts, rebuilt by `t3_cliff_gorge.py` — receiving
essentially no light at 150 m and therefore rendering black against a lit near
cliff.  Commit 73f4916 measured that wall's SKY LEAK falling 1.84% -> 0.05%;
that is a true number about a different question and is not evidence here.

WHY A NEW SOURCE.  DAYLOG's Emberbrook night lane, measured: adjusting an
existing light has never moved a town in this repo; ADDING one always has.  So
this adds `KEY_gorgewall`, a sun **light-linked to `cliff_east_closure` alone**,
so no other surface in Dellhollow changes value.  A sun, not an area light,
because the wall is 60 m tall and 100 m long and irradiance must not fall off
across it.

AND `fx_haze_east`, WHICH WAS RETIRED ON A DIAGNOSIS THAT HAD ALREADY EXPIRED.
That card (x 124..130, a volume scatter at density 0.00917) has shipped
`hide_render = True` since the surgery bake — retired because it was mistaken
for the "salmon card", a diagnosis since corrected.  DAYLOG 2026-08-01
re-probed it at **lockfive**, found it contributed nothing there, and left it
off.  lockfive is not the frame that has the problem: at the GATE camera the
card stands in front of 57% of the top-left quadrant's rays.  Whether it helps
is a question about the gate plate and is answered here, on gate probes.

Renders one draft per variant (1008x576 / 28 spp, the shipped grade) so the
choice is made by LOOKING, and prints the measured luminance of the wall's own
screen region in each.  `save` writes only the chosen variant.
"""
import bpy, sys, os, math, json
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
WALL = "cliff_east_closure"
HAZE = "fx_haze_east"
LIGHT = "KEY_gorgewall"
LINKCOLL = "LNK_gorgewall"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


VARIANTS = opt("--variants", "base,haze,lit,both").split(",")
ENERGY = float(opt("--energy", "3.0"))
OUT = opt("--out", "/tmp")

sc = bpy.context.scene
wall = bpy.data.objects.get(WALL)
haze = bpy.data.objects.get(HAZE)
assert wall is not None, "no %s in this blend" % WALL


def make_light():
    old = bpy.data.objects.get(LIGHT)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    ld = bpy.data.lights.new(LIGHT, type='SUN')
    ld.energy = ENERGY
    ld.color = (1.0, 0.86, 0.68)      # the town's own late key, warmed
    ld.angle = math.radians(3.0)
    ob = bpy.data.objects.new(LIGHT, ld)
    sc.collection.objects.link(ob)
    # the wall is a plane at x ~ 147 facing WEST; light it from the town side,
    # raking down so its relief casts along itself instead of flattening
    ob.location = (60.0, 30.0, 60.0)
    ob.rotation_euler = (math.radians(62.0), 0.0, math.radians(-64.0))
    # LIGHT LINKING: this source may touch the far wall and nothing else, so no
    # other surface's value in any of the sixteen plates can move.
    coll = bpy.data.collections.get(LINKCOLL)
    if coll is None:
        coll = bpy.data.collections.new(LINKCOLL)
    ob.light_linking.receiver_collection = coll
    if wall.name not in coll.objects:
        coll.objects.link(wall)
    return ob


def probe(path):
    sol = json.load(open(REPO + "/public/townmap/dellhollow.cameras.solved.json"))
    c = [k for k in sol["cameras"] if k["id"] == "gate"][0]
    D = sol["defaults"]
    sc.view_settings.view_transform = D.get("view_transform", "AgX")
    sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
    sc.view_settings.exposure = D.get("exposure", 0.0)
    cam = bpy.data.objects.get("probe_gate")
    if cam is None:
        cd = bpy.data.cameras.new("probe_gate")
        cd.sensor_fit = 'VERTICAL'
        cd.angle_y = math.radians(c["fov"])
        cd.clip_start, cd.clip_end = c["clip"][0], c["clip"][1]
        cam = bpy.data.objects.new("probe_gate", cd)
        sc.collection.objects.link(cam)
        cam.location = Vector(c["pos"])
        cam.rotation_euler = (Vector(c["aim"]) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences
        cp.compute_device_type = 'METAL'
        cp.get_devices()
        for d in cp.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, CPU fallback:", e)
    sc.render.resolution_x, sc.render.resolution_y = 1008, 576
    sc.render.resolution_percentage = 100
    sc.cycles.samples = 28
    sc.cycles.use_denoising = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("PROBE %s" % path)


for v in VARIANTS:
    lit = v in ("lit", "both")
    hz = v in ("haze", "both")
    old = bpy.data.objects.get(LIGHT)
    if old and not lit:
        bpy.data.objects.remove(old, do_unlink=True)
    if lit:
        make_light()
    if haze:
        haze.hide_render = not hz
        # The card tops out at z = 26 and the wall it fronts reaches z = 32.5,
        # so the first haze probe came back with a hard horizontal seam across
        # the frame where the atmosphere simply stopped.  Raise its top over the
        # wall's own crest.  (Measured, not guessed: cliff_east_closure z max
        # 32.48.)
        if hz and float(opt("--hazetop", "0")) > 0:
            top = float(opt("--hazetop", "0"))
            for hv in haze.data.vertices:
                w = haze.matrix_world @ hv.co
                if w.z > 20.0:
                    w.z = top
                    hv.co = haze.matrix_world.inverted() @ w
            haze.data.update()
    print("\n=== VARIANT %s   light=%s(%.1f)  haze=%s ===" % (v, lit, ENERGY, hz))
    probe(os.path.join(OUT, "gorgewall_%s.png" % v))

if SAVE:
    # THE PROBE CAMERA MUST NOT SHIP.  It is a scene object like any other and
    # `sc.camera` points at it; saving with it in place would leave a stray
    # camera in the town's master and hand the next bake a different active
    # camera than the one it built.
    cam = bpy.data.objects.get("probe_gate")
    if cam:
        cd = cam.data
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.cameras.remove(cd)
    sc.camera = None
    # ship exactly what the last named variant configured
    bpy.ops.wm.save_mainfile()
    print("SAVED BLEND %s  (variant %s)" % (bpy.data.filepath, VARIANTS[-1]))
