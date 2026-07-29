"""gate_shots.py — review renders for the Gate Approach district.

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/gate_shots.py -- \
      <version> [names|all] [samples] [EEVEE|CYCLES]

Writes docs/qa/districts/gate_v<version>_<name>.png at 1344x768 in the master's
own grade (AgX / Medium High Contrast / exposure +0.35).

The set is composed AROUND the district (manifest 57) — a walkable town is seen
from every side a player can stand on — but this district has one shot that
matters more than any other in Dellhollow: `arrival`, the frame the player gets
when they walk in off the overworld for the first time.  `continuity` reproduces
the Boatyard v10 hero camera exactly so the accepted district can be diffed for
value drift (manifest 53/67), and `fromgorge` is the shot that proves the new
ground: everything on this tier stands on a promontory that did not exist.

NOTE — the blockout walk ribbons.  The master render-hides `walk_*` meshes that a
district has decked over (manifest 51), but this district is on a BRANCH: a flag
set on a master-owned object would not survive the merge (which appends the
district collection, it does not re-append the master's own objects).  So the
gate tier's ribbons are still render-visible in the file, and this script hides
them FOR THE RENDER ONLY and never saves.  It is showing the merged result.
"""
import bpy, os, sys, math, io, contextlib
from mathutils import Vector

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

SHOTS = {
    # ---------------------------------------------------------------- the shot
    # ARRIVAL — the player walks in off the overworld road from up-gorge.  Yard
    # left and right, the toll house, and the Valley Gate closing the frame with
    # the gorge opening behind it.
    "arrival":   dict(pos=(2.20, 8.55, 26.20), aim=(16.90, 4.10, 25.15), fov=48, fit='H'),
    # the parcel's own draft camera: from inside the town looking back upstream at
    # the arch, arrival framed on rim rock
    "gate":      dict(pos=(24.20, 12.30, 28.40), aim=(16.30, 4.30, 25.60), fov=40, fit='V'),
    # standing in the gateway, looking into Dellhollow: the gallery, the winch and
    # the drop.  This is what the town IS, from its front door.
    "throughgate": dict(pos=(11.50, 4.30, 26.40), aim=(27.00, 6.20, 22.60), fov=50, fit='H'),
    # the toll house three-quarter, from the yard
    "tollyard":  dict(pos=(8.20, 8.60, 26.90), aim=(13.20, 2.90, 25.30), fov=44, fit='V'),
    # the Cargo Winch head from the gallery, with the rope going over
    "winch":     dict(pos=(22.40, 9.90, 26.70), aim=(28.30, 8.00, 24.20), fov=42, fit='V'),
    # the Porters' Yard from its gorge shoulder, bluff behind
    "yard":      dict(pos=(14.60, 15.80, 28.60), aim=(5.00, 6.00, 24.60), fov=46, fit='H'),
    # the promontory from out over the gorge: the tier has to STAND on something
    "fromgorge": dict(pos=(15.00, 33.00, 19.00), aim=(9.00, 6.00, 21.50), fov=48, fit='H'),
    # from the Boatyard's water, looking up at the gate tier — the town's silhouette
    "fromquay":  dict(pos=(42.00, 27.00, 15.00), aim=(16.00, 6.50, 24.20), fov=46, fit='H'),
    # the v10 Boatyard hero camera, unchanged — value continuity against
    # boatyard_v10.png / waterfront_v7_continuity.png
    "continuity": dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
}

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VER = argv[0] if argv else "1"
WHICH = argv[1].split(",") if len(argv) > 1 and argv[1] != "all" else list(SHOTS)
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
ENGINE = argv[3] if len(argv) > 3 else "EEVEE"

# --- render-only: hide the gate tier's blockout ribbons (see the note above)
hidden = 0
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(("walk_", "bar_")):
        continue
    vs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(v.x for v in vs) / 8
    cy = sum(v.y for v in vs) / 8
    cz = sum(v.z for v in vs) / 8
    if 0.0 <= cx <= 33.0 and -2.0 <= cy <= 13.5 and cz > 18.0 and not o.hide_render:
        o.hide_render = True
        hidden += 1
print("(render-only: %d gate-tier walk/bar ribbons hidden; this file is never saved)" % hidden)

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = 0.35
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
    # the gorge carries ~50 shadow-casting lamps; the default pool overflows and
    # drops shadows SILENTLY, which makes EEVEE unusable for value judgement
    # (manifest 70) — every real call here is made in Cycles.
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
    fp = os.path.join(OUT, "gate_v%s_%s.png" % (VER, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
