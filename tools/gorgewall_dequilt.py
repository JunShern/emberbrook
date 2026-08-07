"""gorgewall_dequilt.py — THE EAST CLOSURE WALL: DE-QUILT THE TILE, THEN LIGHT IT.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gorgewall_dequilt.py -- [save] [--scale 0.06] [--energy 3.0] \
      [--probe gate,lockfive] [--out <dir>]

WHY THIS EXISTS.  Red-team 20260806-2: lockfive frame-edge FAILING — "the top-left
background is a flat, featureless dark void" — plus gate/weave WEAK of the same
shape.  Render-faithful census: `cliff_east_closure` owns 464/2304 rays of the
lockfive frame (20%), 369 of gate, 308 of crossing, 180 of weave.  The wall is
present and unlit (the gate lane's own 2026-08-02 finding).

THE HISTORY THIS OBEYS (DAYLOG 2026-08-02, cliff-completion lane): lighting the
wall was probed then and REJECTED — a 3 W sun exposed `mat_rock_gorgewall`'s
3.33 m tile as a quilted repeat across a 100 m wall.  The haze card was the
shipped fix; measured, it reaches the gate frame (9.21%) and lockfive at 0.07% —
lockfive's void is exactly the frame the haze cannot touch.  So the rejection's
ROOT CAUSE is treated, not re-argued: the quilt.

WHAT IT DOES.
 1. `mat_rock_gorgewall`'s Mapping scale 0.30 -> --scale (default 0.06, i.e. a
    ~17 m period — the wall's own sibling `mat_rock_farwall`, the four-texture
    parent it was copied from, ships 0.05 and has never quilted).  Same textures,
    same tree, one knob.
 2. Recreates `KEY_gorgewall` exactly as tools/gate_gorgewall_light.py designed
    it: a sun (uniform irradiance over a 60 x 100 m face), LIGHT-LINKED to
    `cliff_east_closure` alone so no other surface in any plate can move.
 3. Probes the named cameras at 1008x576 / 28 spp with the shipped grade and
    prints the median luminance of each frame's top-left quadrant — the region
    both verdicts complain about — so the energy is picked by looking WITH a
    number attached, not assumed.

`save` ships steps 1+2 (no probe cameras are saved — the probe camera is removed
before save, the gate lane's own rule).
"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
WALL = "cliff_east_closure"
MAT = "mat_rock_gorgewall"
LIGHT = "KEY_gorgewall"
LINKCOLL = "LNK_gorgewall"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


SCALE = float(opt("--scale", "0.06"))
ENERGY = float(opt("--energy", "3.0"))
PROBES = [p for p in opt("--probe", "").split(",") if p]
OUT = opt("--out", "/tmp")

sc = bpy.context.scene
wall = bpy.data.objects.get(WALL)
assert wall is not None, "no %s in this blend" % WALL

# ---- 1. de-quilt
m = bpy.data.materials.get(MAT)
assert m is not None, "no %s" % MAT
mapping = next(n for n in m.node_tree.nodes if n.type == 'MAPPING')
before = tuple(mapping.inputs['Scale'].default_value)
mapping.inputs['Scale'].default_value = (SCALE, SCALE, SCALE)
print("%s Mapping scale %s -> %s  (tile period %.1f m -> %.1f m)"
      % (MAT, tuple(round(v, 3) for v in before), (SCALE,) * 3,
         1.0 / before[0], 1.0 / SCALE))

# ---- 2. the linked sun (gate_gorgewall_light.py's own design)
old = bpy.data.objects.get(LIGHT)
if old:
    bpy.data.objects.remove(old, do_unlink=True)
ld = bpy.data.lights.new(LIGHT, type='SUN')
ld.energy = ENERGY
ld.color = (1.0, 0.86, 0.68)
ld.angle = math.radians(3.0)
ob = bpy.data.objects.new(LIGHT, ld)
sc.collection.objects.link(ob)
ob.location = (60.0, 30.0, 60.0)
ob.rotation_euler = (math.radians(62.0), 0.0, math.radians(-64.0))
coll = bpy.data.collections.get(LINKCOLL)
if coll is None:
    coll = bpy.data.collections.new(LINKCOLL)
ob.light_linking.receiver_collection = coll
if wall.name not in coll.objects:
    coll.objects.link(wall)
print("%s sun %.1f W light-linked to %s alone" % (LIGHT, ENERGY, WALL))

# ---- 3. probes
def probe(cid, path):
    sol = json.load(open(REPO + "/public/townmap/dellhollow.cameras.solved.json"))
    c = [k for k in sol["cameras"] if k["id"] == cid][0]
    D = sol["defaults"]
    sc.view_settings.view_transform = D.get("view_transform", "AgX")
    sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
    sc.view_settings.exposure = D.get("exposure", 0.0)
    name = "probe_" + cid
    cam = bpy.data.objects.get(name)
    if cam is None:
        cd = bpy.data.cameras.new(name)
        cd.sensor_fit = 'VERTICAL'
        cd.angle_y = math.radians(c["fov"])
        cd.clip_start, cd.clip_end = c["clip"][0], c["clip"][1]
        cam = bpy.data.objects.new(name, cd)
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
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)
    tl = px[h // 2:, : w // 2, :3]        # image rows start at bottom: top-left = upper half rows
    lum = 0.2126 * tl[..., 0] + 0.7152 * tl[..., 1] + 0.0722 * tl[..., 2]
    print("PROBE %-10s %s  top-left quadrant median L %.1f/255" % (cid, path, float(np.median(lum)) * 255))
    bpy.data.images.remove(img)


for cid in PROBES:
    probe(cid, os.path.join(OUT, "gorgewall_dq_%s_s%s_e%s.png" % (cid, SCALE, ENERGY)))

if SAVE:
    for o in list(bpy.data.objects):
        if o.name.startswith("probe_") and o.type == 'CAMERA':
            cd = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.cameras.remove(cd)
    sc.camera = None
    bpy.ops.wm.save_mainfile()
    print("SAVED BLEND %s  (scale %.3f, energy %.1f)" % (bpy.data.filepath, SCALE, ENERGY))
