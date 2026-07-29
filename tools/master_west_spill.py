"""master_west_spill.py — decompose the merged master's drift on an ACCEPTED frame.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_west_spill.py -- [samples]

Finding 163: continuity needs an A/B CONTROL RENDER, not a stale baseline.  This
takes that one step further, because a MERGE is where two branch districts meet for
the first time: each measured its own spill onto the accepted art alone, so neither
number covers the pair.  Same camera, same engine, same samples, five configs:

  merged          the master as it now stands
  no_west         both district collections hide_render'd  -> must reproduce the
                  pre-merge number, which is what proves the rig rather than the art
  no_west_lights  every KEYG_/KEYSH_ lamp off, geometry left in -> separates "new
                  light reaching accepted art" from "new geometry in frame"
  no_gate_lights  the gate tier's 16 lamps off
  no_shelf_lights the shelf tier's 16 lamps off

The camera is the Boatyard v10 hero — the frame every district pass has quoted.
Nothing is saved.
"""
import bpy, os, sys, math, io, contextlib
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(argv[0]) if argv else 48
OUT = "/private/tmp/spill"
os.makedirs(OUT, exist_ok=True)

# the Boatyard v10 hero, identical to weave_luminance.SHOTS["continuity"]
POS, AIM, FOV = (37.6, 25.4, 8.5), (14.4, 30.4, 3.4), 35

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 672, 384
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
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
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True

cd = bpy.data.cameras.new("spill_cam")
cd.lens_unit = 'FOV'
cd.angle = math.radians(FOV)
cam = bpy.data.objects.new("spill_cam", cd)
sc.collection.objects.link(cam)
cam.location = Vector(POS)
cam.rotation_mode = 'QUATERNION'
cam.rotation_quaternion = (Vector(AIM) - Vector(POS)).to_track_quat('-Z', 'Y')
sc.camera = cam

GATE = [o for o in bpy.data.collections["GATE_DISTRICT"].all_objects]
SHELF = [o for o in bpy.data.collections["SHELF_DISTRICT"].all_objects]
GLIGHT = [o for o in GATE if o.type == 'LIGHT']
SLIGHT = [o for o in SHELF if o.type == 'LIGHT']
print("gate: %d objects (%d lamps) | shelf: %d objects (%d lamps)"
      % (len(GATE), len(GLIGHT), len(SHELF), len(SLIGHT)))

CONFIGS = [("merged", []),
           ("no_west", GATE + SHELF),
           ("no_west_lights", GLIGHT + SLIGHT),
           ("no_gate_lights", GLIGHT),
           ("no_shelf_lights", SLIGHT)]

results = {}
for name, off in CONFIGS:
    for o in GATE + SHELF:
        o.hide_render = False
    for o in off:
        o.hide_render = True
    fp = os.path.join(OUT, "spill_%s.png" % name)
    sc.render.filepath = fp
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bpy.ops.render.render(write_still=True)
    px = np.asarray(bpy.data.images.load(fp).pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
    lum = float((px * np.array([0.2126, 0.7152, 0.0722])).sum(axis=1).mean())
    results[name] = lum
    print("  %-16s hid %3d objects   mean luminance %.5f" % (name, len(off), lum))

base = results["no_west"]
print("\n  A/B against the CONTROL (both districts hidden = the pre-merge frame):")
for name in ("merged", "no_west_lights", "no_gate_lights", "no_shelf_lights"):
    print("    %-16s %+.3f%%" % (name, (results[name] - base) / base * 100))
print("\n  attribution of the merged drift:")
m, nl = results["merged"], results["no_west_lights"]
print("    new LIGHT reaching the accepted frame : %+.3f%%" % ((m - nl) / base * 100))
print("    new GEOMETRY in / shadowing the frame : %+.3f%%" % ((nl - base) / base * 100))
print("    gate lamps alone                      : %+.3f%%"
      % ((m - results["no_gate_lights"]) / base * 100))
print("    shelf lamps alone                     : %+.3f%%"
      % ((m - results["no_shelf_lights"]) / base * 100))
for o in GATE + SHELF:
    o.hide_render = False
print("(nothing saved)")
