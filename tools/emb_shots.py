# emb_shots.py — review renders of Emberbrook, out of the live master.
#
#   Blender -b tools/blends/emberbrook-master.blend -P tools/emb_shots.py \
#       --python-exit-code 1 -- [--samples N] [--res WxH] [--only a,b]
#
# NOT the bake.  `tools/cine_bake.py --town emberbrook` renders the SHIPPED plates from
# the solved camera file and nothing here may be confused with it: these are contact
# renders for a review board, deliberately cheap, deliberately named after what they are
# looking at rather than after a camera id.
#
# Two grades are rendered for the hero shot and that is the point of this file tonight:
# Chapter One is EMBERWAKE EVENING, and the town's identity is a Heartlight and a ring of
# lamps lit from it — so "golden hour" and "dusk with the lamps carrying" are genuinely
# different towns, not two exposures of one.  The A/B goes on the morning board and the
# set is NOT committed to either until the user rules.

import bpy, os, sys, math, time, contextlib, io, json
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(REPO, "docs/qa/emberbrook")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


SAMPLES = int(opt("--samples", "48"))
W, H = [int(v) for v in opt("--res", "1600x914").split("x")]
ONLY = set(opt("--only", "").split(",")) if "--only" in argv else None
os.makedirs(OUT, exist_ok=True)

D = json.load(open(os.path.join(REPO, "public/townmap/emberbrook.map.json")))
LM = {l["id"]: l for l in D["landmarks"]}


def P(lid):
    return Vector(LM[lid]["pos"])


HL = P("heartlight")

# name, camera position, aim point, vertical fov, one-line intent
SHOTS = [
    ("town-wide", HL + Vector((26, -30, 30)), HL + Vector((2, 4, 0)), 40,
     "the whole valley: the village on its rise, the brook, the pond, the river east"),
    ("square-hero", HL + Vector((10.5, -9.0, 7.2)), HL + Vector((-1.2, 1.2, 1.5)), 40,
     "the postcard of home — the Heartlight centre frame, the inn and the shop flanking"),
    ("square-approach", Vector((30.4, 11.0, 4.6)), HL + Vector((0.0, -1.0, 0.8)), 34,
     "coming up the rise off the south road: the square reveals late, as the map's curl intends"),
    ("square-northwest", HL + Vector((-14.0, 10.5, 8.5)), HL + Vector((1.5, -1.0, 1.2)), 36,
     "from the home lane looking back across the plaza: bakery, bunting, the brook behind"),
    ("home-row", P("lake-home") + Vector((6.5, -8.5, 5.5)),
     P("hillside-cottage") + Vector((-1.0, 0.5, 1.2)), 38,
     "up the home lane: the keeper's cottage, Rowan's, Mara & Pip's, the brook behind"),
    ("hilltop-bench", P("home-lane-end") + Vector((-4.5, -3.5, 2.6)),
     P("heartlight") + Vector((0, 0, 1.6)), 40,
     "the bench with the whole village in view — the shot the implied-scale ruling is for"),
    ("gate-court", P("sigil-gate") + Vector((10.0, -14.0, 7.5)),
     P("sigil-gate") + Vector((0, -1.5, 1.2)), 36,
     "the sealed gate and its twin sigil plates — the one unwarm frame in the town"),
    ("confluence", P("brook-mouth") + Vector((-7.0, -9.0, 5.5)),
     P("brook-mouth") + Vector((1.5, 0.6, 0.3)), 36,
     "the brook slips into the river — the town's own name, made visible"),
    # ACROSS THE WATER, not from the town side.  Standing between the square and the
    # pond puts a cottage roof in the near half of every frame; standing on the far
    # shore puts the POND in it, which is what the map's own note asks for — "the
    # evening mirror for the Heartlight glow".
    ("pond-lane", P("pond") + Vector((6.0, -7.5, 4.6)),
     P("pond-jetty") + Vector((-0.5, 0.8, 0.6)), 38,
     "low along the shore: the jetty, the brook's mouth, the Heartlight's glow on the water"),
]

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"

prefs = bpy.context.preferences.addons.get('cycles')
if prefs:
    try:
        prefs.preferences.compute_device_type = 'METAL'
        prefs.preferences.get_devices()
        for d in prefs.preferences.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, CPU fallback:", e)

SUN = bpy.data.objects.get("EMB_sun")
WORLD_BG = sc.world.node_tree.nodes["Background"]


def grade(name):
    """THE TWO CANDIDATE HOURS, and they are different towns rather than two exposures.

    GOLDEN — the Dellhollow-ratified late-afternoon key (variant C, exposure +0.15).  It
    is what every existing baked plate in this project is lit by, so it is the safe
    answer and the one that makes Emberbrook look like it belongs beside Dellhollow.

    EMBERWAKE — Chapter One's own hour.  The sun is nearly down, the sky has gone blue,
    and the town's light is coming OUT of the Heartlight and the fifteen lamps lit from
    it.  It is the harder render and it is the one that says what this town IS: the rare
    survivor that still has a flame, on the night the flame is taken.
    """
    if name == "golden":
        SUN.data.energy = 3.6
        SUN.data.color = (1.0, 0.86, 0.68)
        SUN.rotation_euler = (math.radians(56), 0.0, math.radians(212))
        WORLD_BG.inputs[0].default_value = (0.30, 0.34, 0.42, 1)
        WORLD_BG.inputs[1].default_value = 1.15
        sc.view_settings.exposure = 0.15
    else:
        SUN.data.energy = 0.75                     # the last of it, raking
        SUN.data.color = (1.0, 0.62, 0.36)
        SUN.rotation_euler = (math.radians(80), 0.0, math.radians(226))
        WORLD_BG.inputs[0].default_value = (0.10, 0.13, 0.22, 1)
        WORLD_BG.inputs[1].default_value = 0.34
        sc.view_settings.exposure = 0.55


def clear_pos(pos, aim):
    """THE CAMERA MUST BE ABLE TO SEE ITS SUBJECT, and that is measured, not assumed.
    The first pass authored six positions by offset from a landmark and put four of them
    inside a tree crown — the hero frame of Festival Square rendered as a wall of green.
    So each camera backs off along its own view axis, and climbs, until the ray to the
    aim point is unobstructed.  This is cine_bake's visibility probe in miniature, and
    the lesson it encodes is seam-canon 9.3: measure WHY a thing is invisible before
    choosing the fix."""
    dg = bpy.context.evaluated_depsgraph_get()
    v = (Vector(pos) - Vector(aim))
    d0 = v.length
    for lift in (0.0, 1.5, 3.0, 5.0):
        for k in range(16):
            p = Vector(aim) + v.normalized() * (d0 + k * 1.6) + Vector((0, 0, lift))
            ray = Vector(aim) - p
            hit, _l, _n, _i, ob, _m = sc.ray_cast(dg, p, ray.normalized(),
                                                  distance=ray.length - 0.6)
            # ... AND THE CAMERA MUST NOT BE STANDING INSIDE SOMETHING.  An unobstructed
            # ray to the subject is not enough: a camera inside a tree crown has a clear
            # line out through the far side of the leaves and renders a wall of green
            # from the inside faces at the near clip.  Six axis probes settle it.
            enclosed = all(sc.ray_cast(dg, p, Vector(d), distance=1.4)[0] for d in
                           ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
            if not hit and not enclosed:
                if k or lift:
                    print("    %-18s backed off %.1f m, lifted %.1f m (was inside %s)"
                          % ("", k * 1.6, lift, "geometry"))
                return p
    return Vector(pos)


def shoot(name, pos, aim, fov, tag):
    pos = clear_pos(pos, aim)
    cd = bpy.data.cameras.new("shot_" + name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(fov)
    cd.clip_start, cd.clip_end = 0.05, 900
    cam = bpy.data.objects.new("shot_" + name, cd)
    sc.collection.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (Vector(aim) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    path = os.path.join(OUT, "%s.%s.png" % (name, tag))
    sc.render.filepath = path
    t = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print("  %-18s %-9s %5.1fs  ->  %s" % (name, tag, time.time() - t,
                                           os.path.relpath(path, REPO)))
    return path


print("=" * 78)
print("EMBERBROOK REVIEW RENDERS — %d samples, %dx%d" % (SAMPLES, W, H))
print("=" * 78)
made = []
for tag in ("golden", "emberwake"):
    grade(tag)
    for (name, pos, aim, fov, intent) in SHOTS:
        if ONLY and name not in ONLY:
            continue
        # the A/B is only worth paying for on the shots that carry the ruling; the rest
        # render once, in the grade the project already ships
        if tag == "emberwake" and name not in ("square-hero", "square-approach",
                                              "pond-lane", "confluence", "hilltop-bench"):
            continue
        made.append((name, tag, shoot(name, pos, aim, fov, tag), intent))

# a contact sheet the user can open in one click
rows = []
for name, tag, path, intent in made:
    rows.append(
        "<figure><img src='%s'><figcaption><b>%s</b> <span class='g'>%s</span><br>%s"
        "</figcaption></figure>" % (os.path.basename(path), name, tag, intent))
open(os.path.join(OUT, "index.html"), "w").write("""<!doctype html><meta charset=utf-8>
<title>Emberbrook — founding contact sheet</title>
<style>
body{background:#14120f;color:#e8dfd0;font:15px/1.55 -apple-system,Segoe UI,sans-serif;
     margin:0;padding:28px 32px}
h1{font-weight:600;letter-spacing:.02em;margin:0 0 4px}
p.sub{color:#9b8f7d;margin:0 0 26px;max-width:70ch}
figure{margin:0 0 30px}img{width:100%%;display:block;border:1px solid #302a22;border-radius:3px}
figcaption{color:#a99c88;padding:9px 2px 0;font-size:13.5px}
b{color:#e8dfd0;font-weight:600}
.g{color:#c98a3c;text-transform:uppercase;font-size:11px;letter-spacing:.09em;
   border:1px solid #4a3a22;padding:1px 6px;border-radius:9px;margin-left:6px}
</style>
<h1>Emberbrook &mdash; the founding</h1>
<p class=sub>Contact renders out of the live master, %s. Not the bake: these are review
frames, and the two grades on the square and the pond are the A/B the morning board has
to rule on &mdash; the project's ratified golden hour, against Chapter One's own
Emberwake evening, where the town's light comes out of the Heartlight and the fifteen
lamps lit from it.</p>
%s""" % (time.strftime("%Y-%m-%d %H:%M"), "\n".join(rows)))
print("\ncontact sheet -> docs/qa/emberbrook/index.html   (%d frames)" % len(made))
