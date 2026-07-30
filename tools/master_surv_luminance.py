"""master_surv_luminance.py — did the survivability pass change the Blender render?

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_surv_luminance.py -- before
  Blender -b tools/blends/dellhollow-master.blend -P tools/master_surv_luminance.py -- after

Renders five frames and prints each one's MEAN LUMINANCE, so a before/after pair
of runs answers the pass's central promise in numbers: **the Blender render look
must not change**.  The gate is +-0.5% per frame.

EEVEE only, per the 2026-07-29 RENDER NORM (agent renders are self-verification,
not presentation; no Cycles beauty sets).

Frame choice — each one is here because a CURED material is IN it:
  arrival      the gate tier: `mat_gate_flag_*` bunting + gate foliage.  This is
               also the taste frame for the pennant verdict.
  continuity   the Boatyard v10 hero, the camera every district pass has quoted.
               The town's value anchor, thick with creepers and tufts.
  damface      Dam Five, the `mat_blackstone` family the brief says Lock Four must
               match — so this is the REFERENCE end of that comparison.
  lockfour     `lock_four_dam` itself: blackstone + `mat_darkfall`, the whole
               structure the runtime showed white.
  townbunting  `bunting_0`/`bunting_1`, the FOUR town `mat_flag_*` cloths the
               handed-down list did not mention (the brief knew only the gate's
               six).  Same taste question, four more cloths.

Both runs must render the SAME file from the SAME directory: relative texture
paths are resolved against the blend's own location, and a backup rendered out of
`backups/` renders missing-texture magenta and measures the rig instead of the
town (finding 119).  This script therefore always renders the LIVE master; the
"before" run simply happens before the cure is applied.  A magenta check runs
anyway, because a number that is measuring a broken rig looks perfectly healthy.
"""
import bpy, os, sys, math, io, contextlib, json
import numpy as np
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = ROOT + "/docs/qa/districts"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TAG = argv[0] if argv else "now"
SAMPLES = int(argv[1]) if len(argv) > 1 else 64

SHOTS = {
    # gate_lib.arrival — the game's first-ever frame of Dellhollow, and the frame
    # the pennant verdict is decided on
    "arrival":     dict(pos=(3.10, 13.80, 29.55), aim=(16.45, 4.40, 26.10), fov=46, fit='H'),
    # the v10 Boatyard hero, unchanged since the first accepted district
    "continuity":  dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35, fit='V'),
    # locksfoot_shots.damface — Dam Five's black dam, the blackstone reference
    "damface":     dict(pos=(112.0, 30.0, 6.0), aim=(88.0, 50.0, -1.2), fov=52, fit='H'),
    # Lock Four's dam, the structure that shipped entirely white.  Chosen from
    # three candidates: the first looked over the crest at the reservoir (subject
    # was a third of the frame) and the second sat inside the gorge cliff.  This
    # one puts the blackstone wall, its gate recesses and the lockhouse across the
    # middle band, which is what the crop then measures.
    "lockfour":    dict(pos=(34.0, 26.0, 13.0), aim=(9.0, 40.0, 4.0), fov=50, fit='H'),
    # the town bunting over the lane
    "townbunting": dict(pos=(32.0, 19.5, 10.5), aim=(22.0, 27.0, 6.2), fov=44, fit='H'),
}
# CROPS — the "accepted region" the +-0.5% gate is really about, as fractions of
# the frame (x0, x1, y0, y1).  A full-frame mean is diluted by sky and cliff; the
# crop is where the cured material actually is.
CROPS = {
    "arrival":     (0.30, 0.85, 0.25, 0.75),
    "continuity":  (0.15, 0.90, 0.30, 0.95),
    "damface":     (0.20, 0.80, 0.30, 0.90),
    "lockfour":    (0.15, 0.95, 0.35, 0.92),
    "townbunting": (0.25, 0.80, 0.20, 0.80),
}

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1024, 586
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = SAMPLES
try:
    sc.eevee.shadow_pool_size = '1024'
except Exception as e:
    print("shadow_pool_size NOT SET: %s" % e)
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = 0.35

# collision ribbons are not art: hide them so the number measures the town
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("walk_", "bar_")) and not o.hide_render:
        o.hide_render = True

print("blend: %s   tag=%s" % (bpy.data.filepath, TAG))
os.makedirs(OUT, exist_ok=True)
res = {}
for name, s in SHOTS.items():
    cd = bpy.data.cameras.new("lum_" + name)
    cd.lens_unit = 'FOV'
    cd.angle = math.radians(s["fov"])
    cd.sensor_fit = 'HORIZONTAL' if s.get("fit", 'H') == 'H' else 'VERTICAL'
    cd.clip_start, cd.clip_end = 0.05, 1200
    cam = bpy.data.objects.new("lum_" + name, cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(s["pos"])
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (Vector(s["aim"]) - Vector(s["pos"])).to_track_quat('-Z', 'Y')
    sc.camera = cam
    fp = os.path.join(OUT, "surv_%s_%s.png" % (TAG, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fp)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, im.channels)[:, :, :3]
    W = np.array([0.2126, 0.7152, 0.0722])
    lum_full = float((px * W).sum(axis=2).mean())
    x0, x1, y0, y1 = CROPS[name]
    sub = px[int(h * y0):int(h * y1), int(w * x0):int(w * x1)]
    lum_crop = float((sub * W).sum(axis=2).mean())
    r, g, b = px.reshape(-1, 3).mean(axis=0)
    magenta = (r > 0.25 and b > 0.25 and g < 0.6 * min(r, b))
    print("LUM %-8s %-12s full=%.5f  crop=%.5f  rgb=(%.3f, %.3f, %.3f)%s"
          % (TAG, name, lum_full, lum_crop, r, g, b,
             "   <-- MAGENTA: broken texture paths" if magenta else ""))
    res[name] = dict(full=lum_full, crop=lum_crop, rgb=[float(r), float(g), float(b)])
    bpy.data.images.remove(im)

jp = os.path.join(OUT, "surv_lum_%s.json" % TAG)
with open(jp, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote %s" % jp)

# if a sibling tag exists, print the delta table right here
other = "before" if TAG == "after" else "after"
op = os.path.join(OUT, "surv_lum_%s.json" % other)
if os.path.exists(op):
    prev = json.load(open(op))
    a, b_ = (prev, res) if TAG == "after" else (res, prev)
    print("\n" + "=" * 74)
    print("LUMINANCE DELTA  before -> after      (gate: +-0.5% on the crop)")
    print("=" * 74)
    worst = 0.0
    for n in SHOTS:
        if n not in a or n not in b_:
            continue
        for key in ("full", "crop"):
            d = 100.0 * (b_[n][key] - a[n][key]) / a[n][key] if a[n][key] else 0.0
            if key == "crop":
                worst = max(worst, abs(d))
            print("  %-12s %-5s %.5f -> %.5f   %+.3f%%%s"
                  % (n, key, a[n][key], b_[n][key], d,
                     "   FAIL" if key == "crop" and abs(d) > 0.5 else ""))
    print("-" * 74)
    print("worst crop delta: %+.3f%%  ->  %s" % (worst, "PASS" if worst <= 0.5 else "FAIL"))
    print("=" * 74)
