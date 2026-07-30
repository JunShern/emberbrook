"""lg_shot.py — one EEVEE record frame of a named set of objects.

  Blender -b tools/blends/dellhollow-master.blend -P tools/lg_shot.py \
      --python-exit-code 1 -- <prefix,prefix> <out.png> <yaw> <pitch> <dist> [samples]

The town's record-shot norm (2026-07-29): agent renders are SELF-VERIFICATION;
2-3 shots go to `docs/qa/` for the human and nobody polishes a camera.  This is
deliberately NOT the pre-render pipeline — `tools/cine_bake.py` and
`public/townmap/dellhollow.cameras.json` own the real shots and their solved
frames.  This aims a camera at the bounding box of whatever you name, from the
shot's own yaw/pitch, so a build can be LOOKED AT without touching that pipeline.
Prints mean luminance so a before/after pair is a number as well as a picture.
Never saves the blend.
"""
import bpy, os, sys, math
import numpy as np
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import world_bbox

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREFIX = tuple(argv[0].split(","))
OUT = argv[1]
YAW = float(argv[2]) if len(argv) > 2 else 60.0
PITCH = float(argv[3]) if len(argv) > 3 else 24.0
DIST = float(argv[4]) if len(argv) > 4 else 24.0
SAMPLES = int(argv[5]) if len(argv) > 5 else 64

sel = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PREFIX)]
assert sel, "nothing matches %s" % (PREFIX,)
bb = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
for o in sel:
    b = world_bbox(o)
    bb = [min(bb[0], b[0]), max(bb[1], b[1]), min(bb[2], b[2]), max(bb[3], b[3]),
          min(bb[4], b[4]), max(bb[5], b[5])]
C = Vector(((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2, (bb[4] + bb[5]) / 2))
print("subject: %d objects, bounds x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f"
      % (len(sel), *bb))

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = SAMPLES
try:
    sc.eevee.shadow_pool_size = '1024'
except Exception as e:
    print("shadow_pool_size NOT SET:", e)
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = 0.35

cd = bpy.data.cameras.new("rec_cam")
cd.lens_unit = 'FOV'
cd.angle = math.radians(35.0)
cam = bpy.data.objects.new("rec_cam", cd)
sc.collection.objects.link(cam)
a, p = math.radians(YAW), math.radians(PITCH)
cam.location = C + Vector((math.cos(a) * math.cos(p), math.sin(a) * math.cos(p),
                           math.sin(p))) * DIST
d = (C - cam.location).normalized()
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
print("camera at (%.2f, %.2f, %.2f) looking at (%.2f, %.2f, %.2f), yaw %.0f pitch %.0f dist %.0f"
      % (*cam.location, *C, YAW, PITCH, DIST))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(OUT)
px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3]
lum = float((px * np.array([0.2126, 0.7152, 0.0722])).sum(axis=1).mean())
print("WROTE %s   mean luminance %.4f" % (OUT, lum))
