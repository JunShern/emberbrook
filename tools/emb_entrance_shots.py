"""emb_entrance_shots.py — contact renders for the Village Entrance parcel.

    Blender -b tools/blends/emberbrook-entrance-wip.blend -P tools/emb_entrance_shots.py \
        --python-exit-code 1 -- [--samples 96] [--out docs/qa/districts] [--only arrival]

THREE FRAMES, and they are chosen rather than pointed: this parcel has to read from BOTH
ENDS of the same road (it is the scene the player arrives into and the scene the map's
own camera note looks back down), plus the one thing neither end can show — the river.

  arrival   the player's first-ever view of the game world: up the south road at dusk,
            the arch lit, the village warm behind it.  `chapter1.js` Act I walks in here.
  archback  the map's own `p-entrance` camera note: "from inside the village looking back
            down the road through the arch — orchard rows framing, valley beyond".
  waystone  the marker's carved face, its moss and the cat-sized shelf on its plinth —
            the staging for Mochi's hiring (STORY.md, and the map's note on this stone).
  riverlook standing ON the road at the waystone and looking EAST, which is the only
            direction that holds the water: the river Vesper has followed for weeks,
            glimpsed through the gap this build keeps open in the riverside screen.
            The other three frames cannot contain it — the water is 27 m east and the
            arch is due south — and that is a fact about the map, not a framing failure.

This script NEVER saves the blend.  It only sets a camera, renders, and exits.
"""
import bpy, sys, os, math

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from render_util import setup_cycles, make_camera

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag, d):
    return argv[argv.index(flag) + 1] if flag in argv else d


SAMPLES = int(opt("--samples", "96"))
OUT = os.path.join(REPO, opt("--out", "docs/qa/districts"))
ONLY = opt("--only", None)
EXPO = float(opt("--exposure", "0.0"))
os.makedirs(OUT, exist_ok=True)

# THE ARCHBACK CAMERA MOVED ONCE, AND THE REASON IS WORTH KEEPING: its first station at
# (29.6, 12.7, 3.55) put the lens INSIDE a bunting swag — 3.5 m is exactly the height the
# festival strings hang at along this road.  A camera on this parcel either stands under
# the swags (eye height, 1.7 m) or over them (4.5 m+); 3.5 m is the one band that is
# guaranteed to be full of cloth.
SHOTS = [
    # id,        camera position,          look at,             lens
    ("arrival",  (34.90, -5.10, 2.30),     (29.40, 8.60, 2.00), 34.0),
    ("archback", (31.80, 13.60, 4.40),     (28.60, 3.20, 1.00), 28.0),
    ("waystone", (30.60, 6.30, 2.00),      (26.00, 8.10, 1.35), 28.0),
    ("riverlook", (27.00, 9.60, 2.20),     (45.00, 6.20, -0.20), 35.0),
]

sc = setup_cycles(samples=SAMPLES, res=(1344, 768), exposure=EXPO)
for (sid, loc, at, lens) in SHOTS:
    if ONLY and sid != ONLY:
        continue
    cam = make_camera("EN_CAM_" + sid, loc, at, lens=lens)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, "entrance_%s.png" % sid)
    print("RENDER %-9s from (%.1f, %.1f, %.1f) -> (%.1f, %.1f, %.1f)  %.0f mm"
          % ((sid,) + loc + at + (lens,)))
    bpy.ops.render.render(write_still=True)
    print("  wrote %s" % sc.render.filepath)
    bpy.data.objects.remove(cam, do_unlink=True)
print("done — %d frames at %d samples" % (len(SHOTS) if not ONLY else 1, SAMPLES))
