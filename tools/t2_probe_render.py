"""t2_probe_render.py — a TASTE-GATE frame from the live master, built exactly the
way cine_bake.py builds one, at probe sample counts.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_probe_render.py -- --cams lockhead --samples 48 \
                                     --hide cliff_town --tag tierA

WHY THIS EXISTS.  The tranche-2 plans all gate on taste, not on numbers: replacing
3-23% of ten frames changes ten compositions at once, and the mitigation
cliff-completion.md names is "build tier A first, bake lockhead alone (the 22.64%
worst case), and put that single frame through a taste gate before building
B/C/D".  Running `cine_bake.py` for that would re-bake a SHIPPED plate against a
half-built master.  This renders the same camera to docs/qa/districts/ instead,
so the shipped backdrops are never touched and the coordinator's single end-of-
tranche bake stays the only thing that writes them.

IDENTICAL to cine_bake.py where it matters, and the identity is the point — a
probe shot under a different camera or a different grade is not evidence about
the shot:
  * camera:  sensor_fit VERTICAL, angle_y = fov, clip from the solved file,
             -Z track to `aim` with Y up — build_cam(), copied
  * grade:   view_transform / look / exposure from the solved file's defaults
  * engine:  Cycles, GPU (Metal), denoised
Only `samples` and `res` differ, and both are printed.

--hide takes object names to exclude from the render AND from the depsgraph, for
the one case this pass needs it: tier A is built BEHIND the `cliff_town`
placeholder's y = 0 face, so the master stays sound (no sky leak) while the
taste gate is out — but the placeholder has to come off for the frame to show
what was built.  Hiding it here rather than deleting it in the blend is what lets
the committed master be correct at every point in the tranche.

Writes docs/qa/districts/<tag>_<camera>.png.  Never saves the blend.
"""
import bpy, os, sys, json, math, time
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
SOLVED = os.path.join(ROOT, "public/townmap/dellhollow.cameras.solved.json")
OUTDIR = os.path.join(ROOT, "docs/qa/districts")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d):
    return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d


CAMS = [c for c in opt("--cams", "").split(",") if c]
SAMPLES = int(opt("--samples", "48"))
RES = opt("--res", "1792x1024")
TAG = opt("--tag", "probe")
HIDE = [h for h in opt("--hide", "").split(",") if h]
BW, BH = [int(v) for v in RES.split("x")]

S = json.load(open(SOLVED))
D = S["defaults"]
BY_ID = {c["id"]: c for c in S["cameras"]}
assert CAMS, "pass --cams id[,id...]"
missing = [c for c in CAMS if c not in BY_ID]
assert not missing, "unknown camera ids: %s" % missing

sc = bpy.context.scene
os.makedirs(OUTDIR, exist_ok=True)

# --- GPU, as cine_bake sets it -------------------------------------------------
prefs = bpy.context.preferences.addons.get('cycles')
if prefs:
    cp = prefs.preferences
    try:
        cp.compute_device_type = 'METAL'
        cp.get_devices()
        for d in cp.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, CPU fallback:", e)

# --- the grade: one place, from the data ---------------------------------------
sc.view_settings.view_transform = D.get("view_transform", "AgX")
sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
sc.view_settings.exposure = D.get("exposure", 0.0)
print("GRADE  %s / %s / exposure %+.2f" % (sc.view_settings.view_transform,
                                           sc.view_settings.look, sc.view_settings.exposure))

hidden = []
for n in HIDE:
    o = bpy.data.objects.get(n)
    if o is None:
        print("  --hide: no object named %s" % n)
        continue
    o.hide_render = True
    o.hide_viewport = True
    hidden.append(n)
if hidden:
    print("HIDDEN for this render only (the blend is not saved): %s" % ", ".join(hidden))


def build_cam(c):
    """cine_bake.py::build_cam, verbatim — the ONLY place a camera is created."""
    name = "cine_" + c["id"]
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(c["fov"])
    cd.clip_start, cd.clip_end = c["clip"][0], c["clip"][1]
    ob = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(ob)
    ob.location = Vector(c["pos"])
    ob.rotation_euler = (Vector(c["aim"]) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob


sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = BW, BH
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'

for cid in CAMS:
    c = BY_ID[cid]
    cam = build_cam(c)
    sc.camera = cam
    path = os.path.join(OUTDIR, "%s_%s.png" % (TAG, cid))
    sc.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("PROBE %-15s %dx%d  %d samples  %.0fs  -> %s"
          % (cid, BW, BH, SAMPLES, time.time() - t0, os.path.relpath(path, ROOT)))
    sys.stdout.flush()

print("\nNOT SAVED — this script never writes the blend.")
