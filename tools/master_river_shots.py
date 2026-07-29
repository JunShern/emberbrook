"""master_river_shots.py — review renders for the 3x river widening.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_river_shots.py -- \
      [names] [samples] [ENGINE]

Writes docs/qa/districts/river-wide_<name>.png at 1344x768 in the master's own
grade (AgX / Medium High Contrast / exposure +0.35).  `hero` reproduces the
Boatyard v10 camera exactly (tools/boatyard_build.py CAMPOS/AIM, 35 deg vertical)
so the Lock Four extension can be diffed against docs/qa/districts/boatyard_v10.png.
"""
import bpy, os, sys, math, io, contextlib
from mathutils import Vector

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

SHOTS = {
    # the whole town + the 48-wide gorge: does it still compose / stay enclosed?
    "overview":  dict(pos=(134.0, -26.0, 120.0), aim=(44.0, 46.0, 4.0), fov=50, fit='H'),
    # where the accepted art stops and the extension starts: bay 3 (y=39.4, built)
    # next to bay 4 (y=46, cloned) — the join that has to be invisible
    "bayjoin":   dict(pos=(25.0, 34.0, 7.5), aim=(15.5, 52.0, 3.2), fov=48, fit='H'),
    # Lock Four from inside the gorge, downstream of the weir: the accepted gate
    # bays near the town, then the extension running away to the far abutment
    "lockfour":  dict(pos=(30.0, 26.0, 9.0), aim=(16.0, 56.0, 3.0), fov=56, fit='H'),
    # the v10 hero camera, unchanged — continuity check against boatyard_v10.png
    "hero":      dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
    # Lock Five: the blockout dam re-spanned, 3 wheels across the full width
    "lockfive":  dict(pos=(108.0, 2.0, 20.0), aim=(88.0, 50.0, 0.0), fov=56, fit='H'),
    # the near bank the Waterfront district inherits, with the new far side behind
    "nearbank":  dict(pos=(40.0, 14.0, 22.0), aim=(62.0, 60.0, 2.0), fov=58, fit='H'),
}

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = argv[0].split(",") if argv and argv[0] != "all" else list(SHOTS)
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
ENGINE = argv[2] if len(argv) > 2 else "EEVEE"

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
if ENGINE == "CYCLES":
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU setup skipped:", e); sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.volume_bounces = 2
    sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
else:
    sc.render.engine = "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass

for name in WHICH:
    s = SHOTS[name]
    cd = bpy.data.cameras.new("cam_" + name)
    cd.sensor_fit = 'VERTICAL' if s["fit"] == 'V' else 'HORIZONTAL'
    if s["fit"] == 'V':
        cd.angle_y = math.radians(s["fov"])
    else:
        cd.angle_x = math.radians(s["fov"])
    cd.clip_start, cd.clip_end = 0.05, 1200
    cam = bpy.data.objects.new("cam_" + name, cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(s["pos"])
    cam.rotation_euler = (Vector(s["aim"]) - Vector(s["pos"])).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    fp = os.path.join(OUT, "river-wide_%s.png" % name)
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
