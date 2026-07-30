# cine_visprobe.py — CAN EACH CAMERA SEE ITS REGION? And if not, which angle can?
#
#   Blender -b tools/blends/dellhollow-master.blend -P tools/cine_visprobe.py -- [opts]
#     (no opts)              report visibility for every solved camera
#     --sweep a,b,c          for these cameras, grid-search yaw/pitch and print the best
#     --yaw 20,40,...        yaw candidates for the sweep (default 0..340 step 20)
#     --pitch 12,20,...      pitch candidates (default 10..60 step 8)
#
# WHY THIS EXISTS. The framing solver (tools/cine_solve.mjs) answers "does the region
# FIT in frame", which is geometry, and it can answer it in milliseconds. It cannot
# answer "is the region actually VISIBLE from there", which needs the town's 1900 objects
# and a ray-caster — and that is the question that killed the map's 13 draft cameras,
# every one of which was buried inside a cliff by a fixed standoff with nothing in the
# file to say so. Finding that out one 3.5-minute Cycles frame at a time is not a loop.
# This is the same probe cine_bake.py records as `visibleFrac`, run standalone and
# swept, so a buried shot is re-aimed in seconds and only then rendered.
#
# CPU ray-casts only: safe to run while a bake has the GPU.

import bpy, os, sys, json, math, time
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
S = json.load(open(os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def opt(name, dflt):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else dflt

SWEEP = [s for s in opt("--sweep", "").split(",") if s]
YAWS = [float(v) for v in opt("--yaw", ",".join(str(y) for y in range(0, 360, 20))).split(",")]
PITCHES = [float(v) for v in opt("--pitch", ",".join(str(p) for p in range(10, 64, 8))).split(",")]
D = S["defaults"]
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
CAMS = {c["id"]: c for c in S["cameras"]}

def seen_frac(pos, probes):
    """fraction of a region's character-head probes with clear line of sight"""
    o = Vector(pos)
    n = 0
    for p in probes:
        v = Vector(p) - o
        L = v.length
        if L < 1e-4: continue
        hit, *_ = sc.ray_cast(dg, o, v.normalized(), distance=L - 0.35)
        if not hit: n += 1
    return n / len(probes) if probes else 0.0

def fits(pos, aim, fov, aspect, pts, margin):
    """same frame test as cine_solve.mjs — so a swept angle is not accepted unless the
    region would still FIT there. Solver and sweep must agree or the sweep is useless."""
    f = (Vector(aim) - Vector(pos)).normalized()
    U = Vector((0, 0, 1))
    r = f.cross(U)
    if r.length < 1e-6: r = Vector((1, 0, 0))
    r.normalize()
    u = r.cross(f).normalized()
    if u.z < 0:
        r = -r
        u = r.cross(f).normalized()
    ty = math.tan(math.radians(fov) / 2)
    for p in pts:
        v = Vector(p) - Vector(pos)
        z = v.dot(f)
        if z <= 1e-6: return False
        if abs((v.dot(r) / z) / (ty * aspect)) > 1 - margin: return False
        if abs((v.dot(u) / z) / ty) > 1 - margin: return False
    return True

print("\n=== VISIBILITY AS SOLVED ===")
print("shot            probes  visible   verdict")
bad = []
for c in S["cameras"]:
    pr = c.get("probes", [])
    v = seen_frac(c["pos"], pr)
    verdict = "ok" if v >= 0.75 else ("THIN" if v >= 0.45 else "BURIED")
    if v < 0.75: bad.append((c["id"], v))
    print("%-15s %5d  %6.1f%%   %s" % (c["id"], len(pr), v * 100, verdict))
if bad:
    print("\nre-aim wanted: " + ", ".join("%s (%.0f%%)" % (i, v * 100) for i, v in bad))
    print("sweep them with:  --sweep " + ",".join(i for i, _ in bad))

# ---- the sweep ---------------------------------------------------------------
for cid in SWEEP:
    c = CAMS.get(cid)
    if not c: print("no such camera: " + cid); continue
    pr = c["probes"]
    aim = c["aim"]
    margin = 0.08
    aspect = D["aspect"]
    fov = c["fov"]
    print("\n=== SWEEP %s (%d probes, fov %g, aim %s) ===" % (cid, len(pr), fov, aim))
    rows = []
    t0 = time.time()
    for yaw in YAWS:
        for pitch in PITCHES:
            dirv = Vector((math.cos(math.radians(pitch)) * math.cos(math.radians(yaw)),
                           math.cos(math.radians(pitch)) * math.sin(math.radians(yaw)),
                           math.sin(math.radians(pitch))))
            # smallest standoff that still FITS the region at this angle
            dist = None
            lo, hi = 4.0, 8.0
            while hi < 200 and not fits(Vector(aim) + dirv * hi, aim, fov, aspect, pr, margin):
                hi *= 1.35
            if hi >= 200: continue
            for _ in range(26):
                mid = (lo + hi) / 2
                if fits(Vector(aim) + dirv * mid, aim, fov, aspect, pr, margin): hi = mid
                else: lo = mid
            dist = hi
            if dist > D["maxDist"] * 1.25: continue
            pos = Vector(aim) + dirv * dist
            v = seen_frac(pos, pr)
            rows.append((v, yaw, pitch, dist, tuple(round(x, 2) for x in pos)))
    rows.sort(reverse=True)
    print("  best angles (%.0fs, %d candidates fitted):" % (time.time() - t0, len(rows)))
    for v, yaw, pitch, dist, pos in rows[:12]:
        print("    yaw %6.1f  pitch %5.1f  dist %5.1f  visible %5.1f%%   pos %s"
              % (yaw, pitch, dist, v * 100, pos))
    if rows:
        v, yaw, pitch, dist, pos = rows[0]
        print("    -> suggested framing for '%s': {\"yaw\": %g, \"pitch\": %g}  (%.0f%% visible, %.1fm)"
              % (cid, yaw, pitch, v * 100, dist))
print("\ndone %.0fs" % (time.time() - 0))
