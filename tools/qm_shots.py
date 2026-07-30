"""qm_shots.py — review renders for the QUAY-MARKET tier.

  Blender -b tools/blends/dellhollow-master.blend -P tools/qm_shots.py -- \
      <version> [names|all] [samples] [EEVEE|CYCLES]

Writes docs/qa/districts/quaymkt_v<version>_<name>.png at 1344x768 in the master's
own grade (AgX / Medium High Contrast / exposure +0.35).

Per the 2026-07-29 RENDER NORM these are SELF-VERIFICATION, not presentation:
EEVEE, small, and never polished beyond "subject visible".  `continuity`
reproduces the Boatyard v10 hero camera exactly so the accepted district can be
diffed for value drift (manifest 53/67), and `gorge` is the shot that proves the
new ground — everything on this tier was floating over a 24 m hole.

NOTE — the blockout walk ribbons.  Unlike the branch districts, this one is in the
LIVE master, so `qm_build.py` sets `hide_render` on its own parcel's ribbons for
real (by map parcel bounds, the merge custodian's pattern) and saves it.  This
script therefore hides NOTHING and shows the file as it ships.  If a gray slab
appears in a frame, it is a ribbon the build missed and it is a bug, not a render
artefact — which is exactly why the hiding was moved into the build.
"""
import bpy, os, sys, math, io, contextlib
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
# The camera list lives in `gate_lib` because the BUILD needs it too: near-field
# density and prop size are decided against the eye positions (gate_lib.near_field),
# so a camera moved here and left stale there would silently invalidate the
# thinning that frame was thinned for.
from qm_lib import SHOTS

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VER = argv[0] if argv else "1"
WHICH = argv[1].split(",") if len(argv) > 1 and argv[1] != "all" else list(SHOTS)
SAMPLES = int(argv[2]) if len(argv) > 2 else 64
ENGINE = argv[3] if len(argv) > 3 else "EEVEE"

# The build already hid this parcel's ribbons and saved it.  Report how many are
# still render-visible inside the parcel, so a missed one shows up as a NUMBER in
# the log rather than as a gray slab someone has to notice in a frame.
vis = [o.name for o in bpy.data.objects
       if o.type == 'MESH' and o.name.startswith(("walk_", "bar_")) and not o.hide_render
       and 30.7 <= sum((o.matrix_world @ Vector(c)).x for c in o.bound_box) / 8 <= 63.6
       and 6.5 <= sum((o.matrix_world @ Vector(c)).y for c in o.bound_box) / 8 <= 21.5
       and 12.5 <= sum((o.matrix_world @ Vector(c)).z for c in o.bound_box) / 8 <= 18.6]
print("(ribbons still render-visible inside p-quay-mkt: %d %s)"
      % (len(vis), vis[:6]))

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
    # the gorge carries ~60 shadow-casting lamps now; the pool overflows and drops
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
    fp = os.path.join(OUT, "quaymkt_v%s_%s.png" % (VER, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
