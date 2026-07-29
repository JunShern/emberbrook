"""boatyard_render.py — render the district shot.

  Blender -b tools/blends/districts/boatyard.blend -P tools/boatyard_render.py -- v1 [samples] [engine]
"""
import bpy, os, sys, io, contextlib, math

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["v1"]
tag = argv[0]
samples = int(argv[1]) if len(argv) > 1 else 224
engine = argv[2] if len(argv) > 2 else "CYCLES"

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - High Contrast"
sc.view_settings.exposure = -0.20

if engine == "CYCLES":
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU setup skipped:", e)
        sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.volume_bounces = 2
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
else:
    sc.render.engine = "BLENDER_EEVEE"

cam = bpy.data.objects.get("cam_boatyard")
assert cam, "no cam_boatyard"
sc.camera = cam
path = os.path.join(OUT, "boatyard_%s.png" % tag)
sc.render.filepath = path
sc.render.image_settings.file_format = "PNG"
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    bpy.ops.render.render(write_still=True)
print("RENDER OK ->", path)
