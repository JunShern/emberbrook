"""waterfront_shots.py — review renders for the Waterfront district.

  Blender -b tools/blends/dellhollow-master.blend -P tools/waterfront_shots.py -- \
      <version> [names|all] [samples] [EEVEE|CYCLES]

Writes docs/qa/districts/waterfront_v<version>_<name>.png at 1344x768 in the
master's own grade (AgX / Medium High Contrast / exposure +0.35).

The camera set is deliberately AROUND the district (manifest finding 57): a
walkable town is seen from every side the player can stand on, so the set
dressing has to survive all of them, not one hero.  `continuity` reproduces the
Boatyard v10 hero camera exactly so the accepted art can be diffed, and
`damnorth` is the shot the river pass flagged as an unlit black mass.
"""
import bpy, os, sys, math, io, contextlib
from mathutils import Vector

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

SHOTS = {
    # down the boardwalk from the seam: stair mouth, long walk, fish dock beyond
    "boardwalk": dict(pos=(38.6, 32.4, 5.0), aim=(58.5, 27.4, 1.5), fov=40, fit='V'),
    # back west at the deep stairs' mouth — the discreet route, mapVisible:false
    "stairmouth": dict(pos=(50.5, 31.2, 4.2), aim=(42.6, 25.2, 2.6), fov=40, fit='V'),
    # the fish dock from the water
    "fishdock":  dict(pos=(50.6, 39.8, 6.6), aim=(60.2, 30.4, 1.6), fov=44, fit='V'),
    # the cargo winch foot, looking back into the yard (the district border)
    "winchfoot": dict(pos=(39.5, 31.0, 4.4), aim=(29.5, 23.8, 2.2), fov=42, fit='V'),
    # the whole stretch from mid-river: does the walk READ as a route?
    "fromriver": dict(pos=(47.0, 47.0, 10.5), aim=(46.0, 24.0, 3.0), fov=52, fit='H'),
    # ... and from upstream and above: the approach a player walking out of the
    "fromquay":  dict(pos=(31.5, 33.5, 12.5), aim=(46.5, 25.5, 1.4), fov=52, fit='H'),
    # the v10 hero camera, unchanged — continuity against boatyard_v10.png
    "continuity": dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
    # the extended Lock Four dam: black silhouette before the key chain
    "damnorth":  dict(pos=(30.0, 26.0, 9.0), aim=(16.0, 56.0, 3.0), fov=56, fit='H'),
    # the far rim / skyline: crowns on the crest instead of at its foot
    "farrim":    dict(pos=(44.0, 30.0, 16.0), aim=(26.0, 86.0, 44.0), fov=54, fit='H'),
}

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VER = argv[0] if argv else "1"
WHICH = argv[1].split(",") if len(argv) > 1 and argv[1] != "all" else list(SHOTS)
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
ENGINE = argv[3] if len(argv) > 3 else "EEVEE"

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
    # the gorge now carries ~40 shadow-casting lamps (key chain + practicals);
    # the default 16 MB shadow pool overflows and drops shadows silently.
    for attr, val in (("shadow_pool_size", '512'), ("light_threshold", 0.005)):
        try:
            setattr(sc.eevee, attr, val)
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
    fp = os.path.join(OUT, "waterfront_v%s_%s.png" % (VER, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
