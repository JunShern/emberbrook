"""look_golden.py — DELLHOLLOW'S RATIFIED LIGHT: "late afternoon" (probe variant C).

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/look_golden.py
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 -P tools/look_golden.py -- save

WHAT THIS IS.  The town shipped under a dusk rig — a 5 W sun at (1.0, 0.545,
0.275), a 1.6 world, and a -0.52 exposure pulling the whole frame down.  Read as
a picture that is a sunset; read as a place a player walks around in for an hour
it is a town with the lights off, and it is the single biggest reason the
backdrops came back "brown".  Four rigs were rendered against the `gate` camera
(the probe strip) and the user picked C: the sun still golden, still raking, but
unmistakably DAYLIGHT — the hour before the light goes, not the hour after.

This script is the rig, written down.  It is not a one-off edit in a session that
is then lost: every number that makes Dellhollow's daylight lives here, it is
idempotent, and re-running it after any district build re-asserts the look.

    SUN_key      energy 5.0 -> 12.0
                 color (1.0, 0.545, 0.275) -> (1.0, 0.79, 0.56)
                 rotation_euler.x 1.1858 -> 0.93   (~53 deg elevation; Y and Z
                 are the district builds' azimuth and are NOT touched)
    World        Background.Strength 1.6 -> 2.1
    Grade        view exposure -0.52 -> +0.15   (AgX / Medium High Contrast stay)

THE EXPOSURE IS NOT OURS TO OWN.  cine_bake.py grades every backdrop from
`defaults.exposure` in townmap/dellhollow.cameras.json (through the solved file),
not from whatever the blend happens to carry — so an exposure set only here would
be silently discarded at bake time and the blend and the deliverable would
disagree.  So the number lives in the cameras file, this script READS it, and
asserts the two agree.  If you change one, the next run of this script fails
until you change the other.  That assertion is the whole point of the read.

The bounce/fill kit (CLIFF_BOUNCE*, FILL_bounce*, KEY_gorge*) is deliberately
untouched: those are per-district instruments balanced against each other, and
re-scaling 60 lights to chase a key change is how a lighting pass becomes a
re-lighting project.  If the fills read weak under the new key, that is a
separate, measured pass.
"""
import bpy, os, sys, json, math

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
CAMERAS = os.path.join(ROOT, "public/townmap/dellhollow.cameras.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = ("save" in argv) or ("--save" in argv)

# ----------------------------------------------------------------- the rig
GOLDEN = dict(
    sun_energy=12.0,
    sun_color=(1.0, 0.79, 0.56),
    sun_rot_x=0.93,
    world_strength=2.1,
    exposure=0.15,
    view_transform="AgX",
    look="AgX - Medium High Contrast",
)
EPS = 1e-4

sc = bpy.context.scene
report = []


def near(a, b):
    return abs(float(a) - float(b)) <= EPS


def setf(label, get, set_, want):
    have = get()
    if near(have, want):
        report.append(("=", label, have, want))
    else:
        set_(want)
        report.append(("*", label, have, want))


# --- the grade's single source of truth ----------------------------------------
cams = json.load(open(CAMERAS))
D = cams["defaults"]
assert near(D.get("exposure"), GOLDEN["exposure"]), (
    "GRADE DRIFT: townmap/dellhollow.cameras.json defaults.exposure is %r but the "
    "golden rig is %r.  cine_bake.py grades from the cameras file, so the blend "
    "alone cannot carry this. Set them both, then re-run "
    "`node tools/cine_solve.mjs` so the solved file follows."
    % (D.get("exposure"), GOLDEN["exposure"]))
assert D.get("view_transform") == GOLDEN["view_transform"], "view_transform drift"
assert D.get("look") == GOLDEN["look"], "look drift"

# --- SUN_key -------------------------------------------------------------------
sun = bpy.data.objects.get("SUN_key")
assert sun is not None and sun.type == 'LIGHT', "SUN_key missing from %s" % bpy.data.filepath
setf("SUN_key.energy", lambda: sun.data.energy,
     lambda v: setattr(sun.data, "energy", v), GOLDEN["sun_energy"])
for i, ch in enumerate("RGB"):
    setf("SUN_key.color.%s" % ch, lambda i=i: sun.data.color[i],
         lambda v, i=i: sun.data.color.__setitem__(i, v), GOLDEN["sun_color"][i])
setf("SUN_key.rotation_euler.x", lambda: sun.rotation_euler.x,
     lambda v: setattr(sun.rotation_euler, "x", v), GOLDEN["sun_rot_x"])
report.append((" ", "SUN_key elevation (deg)", "", round(math.degrees(GOLDEN["sun_rot_x"]), 1)))

# --- world ---------------------------------------------------------------------
bg = sc.world.node_tree.nodes.get("Background")
assert bg is not None, "world %r has no Background node" % sc.world.name
setf("World.Background.Strength", lambda: bg.inputs["Strength"].default_value,
     lambda v: setattr(bg.inputs["Strength"], "default_value", v), GOLDEN["world_strength"])

# --- grade ---------------------------------------------------------------------
setf("view_settings.exposure", lambda: sc.view_settings.exposure,
     lambda v: setattr(sc.view_settings, "exposure", v), GOLDEN["exposure"])
if sc.view_settings.view_transform != GOLDEN["view_transform"]:
    sc.view_settings.view_transform = GOLDEN["view_transform"]
if sc.view_settings.look != GOLDEN["look"]:
    sc.view_settings.look = GOLDEN["look"]

# --- report --------------------------------------------------------------------
print("=" * 78)
print("GOLDEN LOOK — late afternoon (probe variant C)")
print("=" * 78)
print("blend: %s" % bpy.data.filepath)
changed = 0
for mark, label, have, want in report:
    if mark == "*":
        changed += 1
    hv = ("%.4f" % have) if isinstance(have, float) else have
    wv = ("%.4f" % want) if isinstance(want, float) else want
    print("  %s %-30s %-10s -> %s" % (mark, label, hv, wv))
print("  view_transform=%s  look=%s" % (sc.view_settings.view_transform, sc.view_settings.look))
print("%d value(s) changed, %d already golden" % (changed, len(report) - changed - 1))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `-- save` to write the master)")
