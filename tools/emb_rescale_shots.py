# emb_rescale_shots.py — REVIEW frames for the 2x-scale + meandering-river blockout.
#
#   Blender -b tools/blends/emberbrook-master.blend -P tools/emb_rescale_shots.py \
#       --python-exit-code 1 -- [--samples N] [--res WxH] [--only a,b]
#
# WHY THIS IS NOT `emb_shots.py`.  That file is the FOUNDING contact sheet and every one
# of its cameras is an offset in metres from a landmark — offsets measured against the 1x
# map, which after the scale redline frame a third of what they used to.  Rather than
# quietly re-tune the sheet the morning board already ruled on (its grade A/B is still
# the live ruling), this is a separate, smaller set with ONE job: let the user judge the
# rescale AT BLOCKOUT LEVEL.  Every camera here is derived from the map's own extents and
# landmark positions, so it re-aims itself if the map is rescaled again.
#
# ONE GRADE, deliberately: the project's ratified golden hour.  A dusk A/B is a lighting
# question and this board is about distance, mass and water.

import bpy, os, sys, math, time, contextlib, io, json
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


OUT = opt("--out", os.path.join(REPO, "docs/qa/emberbrook/rescale"))
SAMPLES = int(opt("--samples", "64"))
W, H = [int(v) for v in opt("--res", "1600x914").split("x")]
ONLY = set(opt("--only", "").split(",")) if "--only" in argv else None
os.makedirs(OUT, exist_ok=True)

D = json.load(open(os.path.join(REPO, "public/townmap/emberbrook.map.json")))
LM = {l["id"]: l for l in D["landmarks"]}


def P(lid):
    return Vector(LM[lid]["pos"])


HL = P("heartlight")
XS = [l["pos"][0] for l in D["landmarks"]]
YS = [l["pos"][1] for l in D["landmarks"]]
CTR = Vector(((min(XS) + max(XS)) / 2, (min(YS) + max(YS)) / 2, 1.2))
SPAN = max(max(XS) - min(XS), max(YS) - min(YS))         # the town's own size, in metres
RC = D["river"]["course"]
RMID = Vector((RC[len(RC) // 2][0], RC[len(RC) // 2][1], D["river"]["level"]))

# name, camera position, aim point, vertical fov, one-line intent
SHOTS = [
    # THE WHOLE VALLEY, and the stand-off is a multiple of the town's own span rather
    # than a literal, so this frame holds whatever scale the map is next authored at.
    ("town-aerial", CTR + Vector((-0.42 * SPAN, -0.92 * SPAN, 0.80 * SPAN)),
     CTR + Vector((6, 2, 0)), 40,
     "the whole town from the south-west at 2x: lane runs, the rise, the brook through "
     "the middle, the river closing the east"),
    ("river-meanders", Vector((RMID.x + 0.46 * SPAN, RMID.y - 0.62 * SPAN, 0.46 * SPAN)),
     Vector((RMID.x - 6, RMID.y + 14, 0.0)), 38,
     "the river's own bends, town beyond: the redline frame — an authored course with "
     "meanders, vista only, never walkable"),
    # HIGH AND BACK, DELIBERATELY.  The obvious eye-level framing from the square's own
    # corner puts the item shop across half the frame — at 1x it stood ON the plaza rim
    # and read as one side of a room; at 2x it is 11 m clear of the floor and simply
    # blocks.  The question this frame has to answer is how much EMPTY plaza there is,
    # and that is a question only a frame containing the whole square can answer.
    ("square", HL + Vector((2.0, -36.0, 24.0)), HL + Vector((0.0, 2.0, 1.0)), 38,
     "Festival Square at 2x: the plaza's 7 m extent did NOT scale with the map, so the "
     "inn, the shop and the bakery now stand 11-12 m clear of its rim"),
    # THE ONE FRAME AT A PLAYER'S OWN HEIGHT, and it is the arrival: through the village
    # arch, up the gate road, the waystone on the verge and the orchard beyond it.  This
    # is where "the town reads too small" was felt, so it is where it has to be re-judged.
    ("orchard-approach", Vector((58.5, 11.0, 1.75)), Vector((43.0, 23.0, 1.2)), 46,
     "EYE LEVEL on the gate road inside the arch: the waystone on the verge and the "
     "orchard beyond it — a player's-height read on the new distances"),
    ("home-lane", Vector((63.0, 40.0, 19.0)), Vector((33.5, 60.0, 2.4)), 40,
     "down Home Row: Lake's, Rowan's, Mara & Pip's — and the brook running ALONGSIDE the "
     "lane, which is where the six culverts in a row come from"),
    ("confluence", Vector((95.0, 43.0, 7.5)), Vector((108.0, 54.0, -0.3)), 40,
     "the brook slips into the river past the pond — the town's own name, and the join "
     "the blockout now carries all the way to the water"),
    # ---------------------------------------------------------------- ROUND 2 ----
    # THE FOUR NEW FRAMES, and the first two are the ones the round exists for.  Every
    # position is derived from a landmark the map actually carries, so a re-stamped
    # arrival re-aims them; the eye-level pair sit ON the road at a walker's height
    # because the question they answer — does the wood close around you — is not a
    # question an aerial can be asked.
    ("arrival-clearing", P("arrival-clearing") + Vector((-1.4, -5.0, 1.55)),
     P("waystone") + Vector((0.8, 2.0, 0.9)), 46,
     "THE GAME'S FIRST FRAME, at eye level: the arrival clearing looking north up the "
     "Whisperwood road. No lamp, no village, no roof — the wood is the whole horizon and "
     "the road is the only way out of it"),
    ("waystone-road", P("waystone") + Vector((-1.9, -6.6, 1.62)),
     P("waystone") + Vector((2.6, 9.5, 1.5)), 44,
     "the Waystone on the quiet climbing road, where Mochi hires himself to Vesper — the "
     "wood still pressing both verges, the arch and its lamp another 20 m north"),
    ("wood-aerial", P("arrival-clearing")
     + Vector((-0.30 * SPAN, -0.44 * SPAN, 0.60 * SPAN)),
     CTR + Vector((-2, -14, 0)), 42,
     "the whole approach from the south: the arrival corridor cut through the Whisperwood, "
     "the village in its clearing beyond, and how much forest now contains it"),
    # FROM ACROSS THE BROOK, not from the village side: the mill's own neighbours stand
    # between it and the town, and the first framing backed straight into one of them.
    ("watermill", P("watermill") + Vector((8.5, 10.0, 5.6)),
     P("watermill") + Vector((0.8, 2.6, 1.4)), 40,
     "the watermill on the brook's upper run: overshot wheel, the leat on its trestles, "
     "and the banked millpond that holds the 2.0 m of head the wheel turns on. "
     "<b>USER TASTE ITEM:</b> a 2.00 m dam on a valley that falls 2.4 m in total means "
     "the pound stands ~1.9 m PROUD of the natural ground behind its embankment. That is "
     "hydrology, not a modelling slip &mdash; it ships as built for your judgment: keep "
     "the hillside mill pound, or drop to the 1.55 m wheel the valley gives for free"),
    # ------------------------------------------------------- MINI-ROUND 2b ----
    # THE FRAME THE ROUND EXISTS FOR, and it stands ON the court at a walker's height
    # because "can I see a way round" is not a question an aerial can be asked — from
    # above, every bottleneck looks sealed.  Both ends of the pinch have to be IN it:
    # the doors, the channel beside them, and the rock closing on both.
    ("gatefield-seal", P("sigil-gate") + Vector((3.0, -21.0, 1.62)),
     P("sigil-gate") + Vector((5.0, 1.0, 1.4)), 52,
     "THE SEALED PINCH at eye level from the gate court: the Old Gate as ONE structure "
     "spanning the notch &mdash; twin doors over the road, the curtain wall carrying on "
     "east across the channel on its low grate, and the two rock chains closing on both "
     "ends of it. Nothing walkable survives between the masonry and the water"),
    ("gatefield-seal-aerial", P("sigil-gate") + Vector((-26.0, -46.0, 34.0)),
     P("sigil-gate") + Vector((6.0, 2.0, 0.0)), 42,
     "the same pinch from above and behind the village: the valley now has an END rather "
     "than an edge. The chains stand ON the pinch line for three masses and then rake "
     "back out of the valley, so the range pulls away from Home Row instead of looming "
     "along the top of it"),
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
sc.view_settings.exposure = 0.15                         # the ratified golden-hour grade

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


def clear_pos(pos, aim):
    """THE CAMERA MUST BE ABLE TO SEE ITS SUBJECT (emb_shots.py's probe, same lesson):
    back off along the view axis and climb until the ray to the aim point is clear AND
    the camera is not standing inside anything — a camera inside a tree crown has a
    clean line out through the far leaves and renders a wall of green from the inside."""
    dg = bpy.context.evaluated_depsgraph_get()
    v = (Vector(pos) - Vector(aim))
    d0 = v.length
    for lift in (0.0, 1.5, 3.0, 5.0, 8.0):
        for k in range(16):
            p = Vector(aim) + v.normalized() * (d0 + k * 2.2) + Vector((0, 0, lift))
            if p.z < 0.6:
                continue
            ray = Vector(aim) - p
            hit, _l, _n, _i, _o, _m = sc.ray_cast(dg, p, ray.normalized(),
                                                  distance=ray.length - 0.6)
            # 0.90 m, NOT 1.40.  The enclosure probe exists to catch a camera standing
            # INSIDE a tree crown; at 1.4 m it also catches a camera standing on a 2.4 m
            # forest road with scrub on both verges, which is the one place the arrival
            # frames have to stand.  Round 2's understory evicted the Waystone camera 5 m
            # into the air and it rendered the stone from above, through the canopy.  A
            # camera with 0.9 m of clearance on all six axes is not inside anything.
            enclosed = all(sc.ray_cast(dg, p, Vector(d), distance=0.90)[0] for d in
                           ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
            if not hit and not enclosed:
                if k or lift:
                    print("      (backed off %.1f m, lifted %.1f m to clear geometry)"
                          % (k * 2.2, lift))
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
    path = os.path.join(OUT, "%s.png" % name)
    sc.render.filepath = path
    t = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print("  %-18s %5.1fs  from (%.1f, %.1f, %.1f)  ->  %s"
          % (name, time.time() - t, pos.x, pos.y, pos.z, os.path.relpath(path, REPO)))
    return path


print("=" * 78)
print("EMBERBROOK RESCALE REVIEW — %d samples, %dx%d, town span %.0f m"
      % (SAMPLES, W, H, SPAN))
print("=" * 78)
made = []
for (name, pos, aim, fov, intent) in SHOTS:
    if ONLY and name not in ONLY:
        continue
    made.append((name, shoot(name, pos, aim, fov, "golden"), intent))

rows = []
for name, path, intent in made:
    rows.append("<figure><img src='%s'><figcaption><b>%s</b><br>%s</figcaption></figure>"
                % (os.path.basename(path), name, intent))
open(os.path.join(OUT, "index.html"), "w").write("""<!doctype html><meta charset=utf-8>
<title>Emberbrook &mdash; blockout round 2</title>
<style>
body{background:#14120f;color:#e8dfd0;font:15px/1.55 -apple-system,Segoe UI,sans-serif;
     margin:0;padding:28px 32px}
h1{font-weight:600;letter-spacing:.02em;margin:0 0 4px}
p.sub{color:#9b8f7d;margin:0 0 10px;max-width:76ch}
ul.q{color:#c8b89e;max-width:76ch;margin:0 0 26px;padding-left:20px}
ul.q li{margin:4px 0}
figure{margin:0 0 30px}img{width:100%%;display:block;border:1px solid #302a22;border-radius:3px}
figcaption{color:#a99c88;padding:9px 2px 0;font-size:13.5px}
b{color:#e8dfd0;font-weight:600}
</style>
<h1>Emberbrook &mdash; blockout, round 2 + the sealed notch (2b)</h1>
<p class=sub>Gray review frames out of the live master, %s. This round folded in every
ratified redline: area extents doubled, the well off the lane, the <b>Whisperwood
arrival</b> (a clearing deep in the wood, the Waystone on a quiet climbing road, no lamp
until the arch), a <b>stamped wandering brook</b> at sinuosity 1.17 that crosses no home
lane, the <b>ten lived-in landmarks</b> including the watermill, <b>infill households</b>
between the lanes, a <b>forest that contains the village</b> rather than ringing it, and
coarse <b>bluff massing</b> funnelling to the Old Gate. <b>MINI-ROUND 2b</b> then made the
bottleneck absolute against your stamped river tail and your final gate reference: the Old
Gate is now ONE structure spanning the whole notch &mdash; doors over the road, coursed
wall carrying on across the channel on a low grate &mdash; with the rock chains re-snapped
to both of its ends. Measured: <b>0.00 m</b> of walkable ground between the masonry and
the water, <b>0.00 m</b> between the masonry and the rock, and a flood fill from the court
reaches <b>0 m&sup2;</b> of the gorge behind the gate. Nothing downstream has been re-run
&mdash; no districts, no cameras, no bakes. Tree and cliff QUALITY is a dressing-stage bar
with a taste probe in front of it; what is being judged here is density, mass, distance and
composition.</p>
<ul class=q>
<li>The first two frames are the game's opening. Does the wood read as a container?</li>
<li>Infill is now one HOUSEHOLD per cottage &mdash; garden plot, fruit tree, shed or
woodpile, and a track that goes somewhere. Is the spacing village-true?</li>
<li><b>The last two frames are the round's own question.</b> Does the notch read as
absolute &mdash; no way round, on foot or by eye? The cliffs are still massing only,
pending the dressing pass against your gate reference.</li>
<li>The village lost 21 infill households this round, every one of them standing NORTH of
the gate in ground the terrain ruling makes a mountain range. Roofs-in-sight from the
lanes fell from 84% to 73% of samples meeting the 2+ target. Correct, but visible: say if
the north horizon now wants the density put back INSIDE the valley.</li>
<li>The <b>watermill</b> frame carries a taste item in its caption &mdash; the mill pound
stands ~1.9 m proud. It ships as built for your call.</li>
</ul>
%s""" % (time.strftime("%%Y-%%m-%%d %%H:%%M"), "\n".join(rows)))
print("\ncontact sheet -> %s   (%d frames)"
      % (os.path.relpath(os.path.join(OUT, "index.html"), REPO), len(made)))
