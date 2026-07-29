"""weave_shots.py — self-verification renders for the Weave (mid tier).

  Blender -b tools/blends/dellhollow-master.blend -P tools/weave_shots.py -- \
      <version> [names|all] [samples] [EEVEE|CYCLES]

Writes docs/qa/districts/weave_v<version>_<name>.png at 1344x768 in the master's
own grade.

RENDER NORM (user, 2026-07-29): these are the agent's only visual sense, not
presentation.  Six angles per version, EEVEE, and the cameras are DISPOSABLE
scaffolding — framed to "subject visible" and never polished.  The real game
cameras are authored later from the map's own camera hints.

Two of the six are continuity frames on ACCEPTED art, and both are chosen for
what is IN them rather than for who owns them (finding 118).  `wfcontinuity`
looks WEST along the Waterfront boardwalk, away from the Weave, so it measures
the disturbance to the accepted district rather than the new district's own
massing.  `lfcontinuity` does the same for Locksfoot.  This district is the
first to stand BETWEEN a light rig and the art it was solved against, so the
occlusion cost is real and has to be looked at, not argued about.
"""
import bpy, os, sys, math, io, contextlib
from mathutils import Vector

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

SHOTS = {
    # p-weave's own camera note: "from the cliff shoulder out over the stilt
    # clusters — the pilot slice's proven drama angle"
    "weave":       dict(pos=(80.0, 40.0, 18.0), aim=(58.0, 22.0, 9.5), fov=48, fit='H'),
    # p-westweave: "tucked under the quay's shadow — stilts overhead"
    "westweave":   dict(pos=(58.0, 33.0, 9.0), aim=(46.5, 20.5, 10.8), fov=44, fit='V'),
    # the drying decks + the Moorage ribbons: the Locksfoot handover's flagged gap
    "dryingdecks": dict(pos=(60.0, 38.0, 6.5), aim=(70.0, 25.5, 6.0), fov=48, fit='H'),
    # the plank bridge and the cottage beyond — the postcard walk
    "bridge":      dict(pos=(70.0, 34.0, 14.0), aim=(92.0, 22.5, 8.4), fov=44, fit='V'),
    # p-cottage's own camera: "intimate from over the basin, balcony over the drop"
    "cottage":     dict(pos=(86.5, 32.0, 3.0), aim=(93.0, 21.5, 8.6), fov=44, fit='V'),
    # p-northlanding: the last pier, and how high it now stands over the pool
    "landing":     dict(pos=(112.0, 34.0, 3.0), aim=(105.5, 27.0, -0.4), fov=48, fit='H'),
    # the whole tier from mid-river: does the stilt forest READ as one thing?
    "fromriver":   dict(pos=(62.0, 58.0, 20.0), aim=(80.0, 24.0, 7.0), fov=56, fit='H'),
    # --- continuity on ACCEPTED art, cameras unchanged --------------------
    # the Boatyard v10 hero, byte-for-byte the same camera every pass has used
    "continuity":  dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
    # WEST-looking Waterfront: its own content, none of the Weave (finding 118)
    "wfcontinuity": dict(pos=(58.6, 32.4, 5.0), aim=(38.5, 27.4, 1.5), fov=40, fit='V'),
    # WEST-looking Locksfoot: the moorage and the dam, not the tier above them
    "lfcontinuity": dict(pos=(95.0, 33.0, 4.0), aim=(78.0, 27.0, 1.0), fov=44, fit='V'),
}

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VER = argv[0] if argv else "1"
WHICH = argv[1].split(",") if len(argv) > 1 and argv[1] != "all" else list(SHOTS)
SAMPLES = int(argv[2]) if len(argv) > 2 else 48
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
    sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
else:
    sc.render.engine = "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass
    # the gorge now carries ~110 shadow-casting lamps; the default pool overflows
    # and drops shadows SILENTLY, which makes the frame non-repeatable (finding 70)
    for attr, val in (("shadow_pool_size", '512'), ("light_threshold", 0.005)):
        try:
            setattr(sc.eevee, attr, val)
        except Exception:
            pass

# The blockout ribbons this district decked are render-hidden in the file, but
# the ones OUTSIDE it are not, and a review frame full of gray tape is a frame
# every judgement is made wrongly on (finding 90, from the in-master side).
# Hide them for the render only; this script NEVER saves.
hidden = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("walk_", "bar_")) and not o.hide_render:
        o.hide_render = True
        hidden.append(o)
print("ribbons hidden for rendering only (not saved): %d" % len(hidden))

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
    fp = os.path.join(OUT, "weave_v%s_%s.png" % (VER, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
