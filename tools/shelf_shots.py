"""shelf_shots.py — review renders for the Gate Approach district.

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/shelf_shots.py -- \
      <version> [names|all] [samples] [EEVEE|CYCLES]

Writes docs/qa/districts/shelf_v<version>_<name>.png at 1344x768 in the master's
own grade (AgX / Medium High Contrast / exposure +0.35).

Per the 2026-07-29 RENDER NORM these are SELF-VERIFICATION, not presentation:
EEVEE, small, and never polished beyond "subject visible".  `continuity`
reproduces the Boatyard v10 hero camera exactly so the accepted district can be
diffed for value drift (manifest 53/67), and `gorge` is the shot that proves the
new ground — everything on this tier was floating over a 24 m hole.

NOTE — the blockout walk ribbons.  The master render-hides `walk_*` meshes that a
district has decked over (manifest 51), but this district is on a BRANCH: a flag
set on a master-owned object would not survive the merge (which appends the
district collection, it does not re-append the master's own objects).  So the
gate tier's ribbons are still render-visible in the file, and this script hides
them FOR THE RENDER ONLY and never saves.  It is showing the merged result.
"""
import bpy, os, sys, math, io, contextlib
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
# The camera list lives in `gate_lib` because the BUILD needs it too: near-field
# density and prop size are decided against the eye positions (gate_lib.near_field),
# so a camera moved here and left stale there would silently invalidate the
# thinning that frame was thinned for.
from shelf_lib import SHOTS

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

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
    if 0.0 <= cx <= 60.0 and -2.0 <= cy <= 20.0 and cz > 13.0 and not o.hide_render:
        o.hide_render = True
        hidden += 1
print("(render-only: %d shelf/gate/market walk-bar ribbons hidden; this file is never saved)" % hidden)

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
    # the gorge carries ~50 shadow-casting lamps; the pool overflows and drops
    # shadows SILENTLY, which makes EEVEE unusable for value judgement
    # (manifest 70) — every real call here is made in Cycles.
    #
    # AND THE FIX FOR THAT WAS ITSELF SILENT.  A previous pass set this to '4096'
    # inside a bare `except Exception: pass`.  In Blender 5.1 shadow_pool_size is
    # an ENUM whose largest member is '1024', so the assignment raised, the except
    # swallowed it, and the pool stayed at the '512' it started on — a fix for a
    # silent failure that failed silently.  Set to the real ceiling, and if a
    # setting will not take, SAY SO: a QA script that hides its own broken knob is
    # worse than one that never had it.
    for attr, val in (("shadow_pool_size", '1024'), ("light_threshold", 0.005)):
        try:
            setattr(sc.eevee, attr, val)
        except Exception as e:
            print("  !! EEVEE %s = %r REFUSED: %s" % (attr, val, e))
    print("  EEVEE shadow_pool_size=%s light_threshold=%.4f  — 1024 is this "
          "build's maximum and this tier still overflows it (the render log says "
          "'Shadow buffer full'), so these frames prove SUBJECT VISIBLE and "
          "nothing about value.  Record shots: CYCLES."
          % (sc.eevee.shadow_pool_size, sc.eevee.light_threshold))

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
    fp = os.path.join(OUT, "shelf_v%s_%s.png" % (VER, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
