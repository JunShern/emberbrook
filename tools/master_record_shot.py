"""master_record_shot.py — one record frame from a named district camera.

  Blender -b <blend> -P tools/master_record_shot.py -- <lib.SHOT> <out.png> [samples]

e.g.  -- gate_lib.arrival docs/qa/districts/merge_arrival_after.png 96

EEVEE, per the 2026-07-29 render norm (agent renders are self-verification; the
record set is 2-3 shots).  Deliberately does NOT touch `hide_render` on anything:
the point of a merge record shot is to show the master EXACTLY as it now stands,
including whether the manifest-51 ribbon hiding actually landed.  Prints the mean
luminance so a before/after pair is a number as well as a picture.  Never saves.
"""
import bpy, os, sys, math, io, contextlib
import numpy as np
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = argv[0]
OUTPNG = argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 96

libname, shotname = WHICH.split(".")
lib = __import__(libname)
shot = lib.SHOTS[shotname]

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.engine = "BLENDER_EEVEE"   # Blender 5.x renamed EEVEE Next back to this
sc.eevee.taa_render_samples = SAMPLES
# finding 174: this property is an ENUM whose largest member is '1024'.  Set the
# real ceiling and SAY what was got, instead of swallowing the failure.
try:
    sc.eevee.shadow_pool_size = '1024'
    print("shadow_pool_size = %s" % sc.eevee.shadow_pool_size)
except Exception as e:
    print("shadow_pool_size NOT SET: %s" % e)
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = 0.35

cd = bpy.data.cameras.new("rec_" + shotname)
cd.lens_unit = 'FOV'
cd.angle = math.radians(shot["fov"])
cd.sensor_fit = 'HORIZONTAL' if shot.get("fit", 'H') == 'H' else 'VERTICAL'
cam = bpy.data.objects.new("rec_" + shotname, cd)
sc.collection.objects.link(cam)
cam.location = Vector(shot["pos"])
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (Vector(shot["aim"]) - Vector(shot["pos"])).to_track_quat('-Z', 'Y')
sc.camera = cam

nvis = sum(1 for o in bpy.data.objects
           if o.name.startswith(("walk_", "bar_")) and not o.hide_render)
print("blend: %s" % bpy.data.filepath)
print("walk/bar ribbons still RENDER-VISIBLE town-wide: %d" % nvis)

os.makedirs(os.path.dirname(OUTPNG), exist_ok=True)
sc.render.filepath = OUTPNG
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    bpy.ops.render.render(write_still=True)
px = np.asarray(bpy.data.images.load(OUTPNG).pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
lum = float((px * np.array([0.2126, 0.7152, 0.0722])).sum(axis=1).mean())
r, g, b = px.mean(axis=0)
print("RECORD %-10s %s  mean=%.4f  rgb=(%.3f, %.3f, %.3f)"
      % (shotname, os.path.basename(OUTPNG), lum, r, g, b))
