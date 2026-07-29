"""locksfoot_shots.py — review renders for the Locksfoot district.

  Blender -b tools/blends/dellhollow-master.blend -P tools/locksfoot_shots.py -- \
      <version> [names|all] [samples] [EEVEE|CYCLES]

Writes docs/qa/districts/locksfoot_v<version>_<name>.png at 1344x768 in the
master's own grade (AgX / Medium High Contrast / exposure +0.35).

The set is composed FOR THE ROUND (manifest 57): a walkable district is seen
from every side a player can stand on.  `continuity` reproduces the Boatyard v10
hero camera unchanged so the accepted art can be diffed frame to frame — it is
the number that says "one town" — and `wfcontinuity` does the same job for the
Waterfront, because this pass is the first to change the sky over an accepted
district and the claim has to be measured, not asserted.
"""
import bpy, os, sys, math, io, contextlib
from mathutils import Vector

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

SHOTS = {
    # p-lockfive's own camera: low in the gorge looking downstream at the dam
    "lockbasin":  dict(pos=(66.5, 31.0, 7.8), aim=(90.0, 28.5, -0.4), fov=46, fit='V'),
    # the hero: the black dam, its three wheels and the tail race, from below
    "damface":    dict(pos=(112.0, 30.0, 6.0), aim=(88.0, 50.0, -1.2), fov=52, fit='H'),
    # along the crest walk to the closed gate and the far shore beyond
    "crestwalk":  dict(pos=(86.6, 68.0, 3.4), aim=(86.9, 30.0, 0.7), fov=38, fit='V'),
    # the moorage, its barge and the tenant's shack behind
    "moorage":    dict(pos=(85.0, 40.0, 6.0), aim=(70.5, 25.4, 2.2), fov=46, fit='V'),
    # up at the Keepers' Spur from the basin — the "house over the locks" line
    "cottagespur": dict(pos=(86.0, 31.0, 1.2), aim=(93.6, 21.6, 7.6), fov=44, fit='V'),
    # the goodbye framing: from the last pier looking back up at the dam
    "northlanding": dict(pos=(108.5, 27.5, 1.0), aim=(88.0, 31.0, 0.6), fov=50, fit='H'),
    # p-crossing's vignette: straight down at the basin from the plank bridge
    "fromcrossing": dict(pos=(82.0, 22.8, 9.6), aim=(88.0, 28.0, -1.0), fov=52, fit='H'),
    # the whole district from mid-river: does the walk READ as a route?
    "fromriver":  dict(pos=(70.0, 56.0, 15.0), aim=(88.0, 26.0, 1.0), fov=56, fit='H'),
    # the tenant's shack and the district's west seam with the Waterfront
    "westseam":   dict(pos=(63.0, 33.0, 5.0), aim=(76.0, 25.0, 2.0), fov=44, fit='V'),
    # --- continuity: accepted art, unchanged cameras ------------------------
    "continuity": dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
    "wfcontinuity": dict(pos=(38.6, 32.4, 5.0), aim=(58.5, 27.4, 1.5), fov=40, fit='V'),
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
        print("GPU setup skipped:", e)
        sc.cycles.device = "CPU"
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
    # the gorge now carries ~70 shadow-casting lamps; the default pool overflows
    # and drops shadows SILENTLY, which makes the frame non-repeatable (f.70)
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
    fp = os.path.join(OUT, "locksfoot_v%s_%s.png" % (VER, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
