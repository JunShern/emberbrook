"""t2_occluder_census.py — WHICH OBJECT is standing in front of this walk edge?

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_occluder_census.py -- --edge valley-gate__inn --cams gate,shelf-west
      [--samples 40] [--json out.json]

WHY THIS EXISTS.  `tools/shot_probe.py` measures HOW MUCH of a walk edge a shot can
see, against the shipped baked depth.  It is the right instrument for "is this a
framing problem or an occlusion problem" (seam-canon §9.3) and it is useless for the
next question, which is the only one an art fix can act on: **WHICH OBJECT.**  A
percentage cannot be moved; an object can.

On 2026-07-30 the gate staircase was diagnosed three times from screenshots and three
camera attempts failed.  The census run below named the occluders in one pass, and
two of the four had ALREADY been flagged, independently, by `master_walk_qa` and
`geometry_audit` — the town's own standing gates were pointing at the answer.
**A ray-cast against the master is the oracle; a plate is a picture of its result.**

METHOD.  Sample the edge's polyline at `--samples`+1 stations, at FEET and at HEAD
(1.7 m).  Cast one ray from each camera's solved `pos` toward each station and tally
the first RENDER-VISIBLE hit.  Render-hidden collision meshes (`walk_`, `bar_`), fx
volumes and camera helpers are pulled out of the depsgraph first, exactly as
master_walk_qa finding 19 requires, or every ray stops on the invisible walk pad it
is aiming at.  A ray whose first hit is the station itself (within EPS of the target
distance) is CLEAR.

Reads the SOLVED cameras out of `public/assets/scenes/del-cine/cine.json`, so the
census answers for the shot that shipped, not for a camera somebody proposed.

READ-ONLY.  This script never saves the blend.
"""
import bpy, sys, os, json, math
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


EDGE = arg("--edge", "valley-gate__inn")
CAMS = (arg("--cams", "gate") or "").split(",")
NS = int(arg("--samples", "40"))
OUT = arg("--json")
CHARH = 1.7
EPS = 0.15                 # a hit this close to the station IS the station

CINE = json.load(open(ROOT + "/public/assets/scenes/del-cine/cine.json"))
MAP = json.load(open(ROOT + "/public/townmap/dellhollow.map.json"))
LM = {l["id"]: l for l in MAP["landmarks"]}
CAM = {c["id"]: c for c in CINE["cameras"]}

# not diegetic / collision-only / helpers: these must not stop a ray, because the
# renderer does not draw them either.
SKIP_PREFIX = ("walk_", "bar_", "fx_", "cam", "CAM", "REF_", "GA_SRC_", "KEY", "lm_")


def edge_stations(key, n):
    """The edge's polyline, resampled by arc length — shot_probe.py's own sampler."""
    fr, to = key.split("__")
    e = next(x for x in MAP["edges"] if x["from"] == fr and x["to"] == to)
    pts = [LM[fr]["pos"]] + (e.get("waypoints") or []) + [LM[to]["pos"]]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = cum[-1]
    out = []
    for i in range(n + 1):
        s = L * i / n
        j = max(0, min(len(pts) - 2, next((k for k in range(len(cum) - 1)
                                           if cum[k + 1] >= s), len(pts) - 2)))
        seg = cum[j + 1] - cum[j] or 1.0
        t = (s - cum[j]) / seg
        a, b = pts[j], pts[j + 1]
        out.append([a[i2] + (b[i2] - a[i2]) * t for i2 in range(3)])
    return out


# ---------------------------------------------------------------- depsgraph prep
hidden = []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if o.hide_render or o.name.startswith(SKIP_PREFIX):
        if not o.hide_viewport:
            o.hide_viewport = True
            hidden.append(o)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
print("census: %d render-hidden/helper meshes pulled out of the depsgraph" % len(hidden))

stations = edge_stations(EDGE, NS)
print("edge %s: %d stations x 2 heights" % (EDGE, len(stations)))

report = {"edge": EDGE, "samples": NS, "cams": {}}
for cid in CAMS:
    c = CAM.get(cid)
    if not c:
        print("  !! no such camera: %s" % cid)
        continue
    # cine.json world coords ARE Blender world coords (x, y, z-up).
    eye = Vector(c["pos"])
    tally, total = {}, 0
    for st in stations:
        base = Vector(st)
        # the walk line sits ON the surface; lift the feet station off it by a
        # hair so the ground it stands on is not its own occluder.
        for dz in (0.05, CHARH):
            tgt = Vector((base.x, base.y, base.z + dz))
            d = tgt - eye
            dist = d.length
            if dist < 1e-6:
                continue
            hit, loc, nrm, idx, obj, mat = bpy.context.scene.ray_cast(
                dg, eye, d.normalized(), distance=dist + 1.0)
            total += 1
            if not hit or (loc - eye).length >= dist - EPS:
                tally["CLEAR"] = tally.get("CLEAR", 0) + 1
            else:
                n = obj.name if obj else "?"
                tally[n] = tally.get(n, 0) + 1
    rows = sorted(tally.items(), key=lambda kv: -kv[1])
    print("\n%-12s  %d rays" % (cid, total))
    for n, k in rows:
        if k / total >= 0.01:
            print("    %5.1f%%  %4d  %s" % (100.0 * k / total, k, n))
    report["cams"][cid] = {"rays": total,
                           "clear_pct": round(100.0 * tally.get("CLEAR", 0) / total, 1),
                           "tally": {n: k for n, k in rows}}

for o in hidden:
    o.hide_viewport = False

if OUT:
    json.dump(report, open(OUT, "w"), indent=1)
    print("\nwrote %s" % OUT)
