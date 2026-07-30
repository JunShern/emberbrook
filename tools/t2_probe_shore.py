"""t2_probe_shore.py — READ ONLY.  Which metres of shoreline does each camera
actually SEE, and how steep is the bank there?  Produces the bed work list.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_probe_shore.py -- --out /tmp/shore.json

THE BATHYMETRY SCOPING GATE for docs/plans/water-transparency.md.  Every wet cell
with a dry 4-neighbour is a shoreline cell; each is classified by bank rise (over
1 m in one 0.5 m step = a wall, not a bank) and projected + occlusion-ray-cast
into all 17 cameras.  The output is metres of shoreline per camera split into
"wall" and "gentle bank", which is what scoped the shelf work to 49 m in three
places (lockfive 27.5 m, boatyard 15.5 m, cottage-steps 6.5 m) instead of the
whole river: a shelf is only worth building where a camera can see a gentle bank.

CPU ray-casts only.  NEVER saves.
"""
import bpy, os, sys, json, math, collections as C
from mathutils import Vector
REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(n, d): return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d
S = json.load(open(os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")))
ASPECT = S["defaults"]["aspect"]
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()

WOBJ = [o for o in sc.objects if o.type == 'MESH'
        and any(s.material and s.material.name == 'm_water' for s in o.material_slots)]
WN = set(o.name for o in WOBJ)

def stack(x, y, z0):
    out = []; p = Vector((x, y, z0)); d = Vector((0, 0, -1))
    for _ in range(8):
        hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, p, d, distance=400.0)
        if not hit: break
        out.append((ob.name, loc.z)); p = loc + d * 0.002
    return out

def basis(pos, aim):
    f = (Vector(aim) - Vector(pos)).normalized()
    r = f.cross(Vector((0, 0, 1)))
    if r.length < 1e-6: r = Vector((1, 0, 0))
    r.normalize(); u = r.cross(f).normalized()
    if u.z < 0: r = -r; u = r.cross(f).normalized()
    return f, r, u

CAMS = []
for c in S["cameras"]:
    f, r, u = basis(c["pos"], c["aim"])
    CAMS.append((c["id"], Vector(c["pos"]), f, r, u, math.tan(math.radians(c["fov"]) / 2)))

STEP = 0.5
rows = []
for o in WOBJ:
    bb = [o.matrix_world @ Vector(cc) for cc in o.bound_box]
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
    y0, y1 = min(v.y for v in bb), max(v.y for v in bb)
    wz = max(v.z for v in bb)
    nx = int((x1 - x0) / STEP) + 2; ny = int((y1 - y0) / STEP) + 2
    wet = {}
    for j in range(ny):
        for i in range(nx):
            xx = x0 - STEP + i * STEP; yy = y0 - STEP + j * STEP
            st = stack(xx, yy, wz + 6.0)
            wi = next((k for k, (n, z) in enumerate(st) if n in WN), None)
            if wi is None:
                wet[(i, j)] = (0, st[0][1] if st else None, None, None)
            else:
                bed = next(((n, z) for (n, z) in st[wi + 1:] if n not in WN), None)
                wet[(i, j)] = (1, None, bed[1] if bed else None, bed[0] if bed else None)
    # shoreline = wet cell with a dry 4-neighbour
    for (i, j), v in wet.items():
        if not v[0]: continue
        drynb = [wet.get((i + di, j + dj)) for di, dj in ((1,0),(-1,0),(0,1),(0,-1))]
        dry = [d for d in drynb if d and not d[0] and d[1] is not None]
        if not dry: continue
        xx = x0 - STEP + i * STEP; yy = y0 - STEP + j * STEP
        bankrise = max(d[1] for d in dry) - wz
        depth = (wz - v[2]) if v[2] is not None else None
        p = Vector((xx, yy, wz))
        seen = []
        for cid, pos, f, r, u, ty in CAMS:
            vv = p - pos; z = vv.dot(f)
            if z <= 0.2: continue
            if abs((vv.dot(r) / z) / (ty * ASPECT)) > 1 or abs((vv.dot(u) / z) / ty) > 1: continue
            d = p - pos
            hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, pos, d.normalized(), distance=d.length - 0.3)
            if not hit: seen.append((cid, round(z, 1)))
        rows.append({"pool": o.name, "x": round(xx, 2), "y": round(yy, 2), "surf": round(wz, 2),
                     "bankrise": round(bankrise, 2), "depth": round(depth, 2) if depth is not None else None,
                     "bedobj": v[3], "seen": seen})

json.dump(rows, open(opt("--out", "/tmp/shore.json"), "w"))
print("shoreline cells:", len(rows))
per = C.Counter()
steep = C.Counter()
for r in rows:
    for cid, dd in r["seen"]:
        per[cid] += 1
        if r["bankrise"] > 1.0: steep[cid] += 1
print("%-15s %10s %10s %10s" % ("camera", "shore_m", "of which wall", "gentle bank m"))
for cid, n in per.most_common():
    print("%-15s %9.1f %10.1f %10.1f" % (cid, n * STEP, steep[cid] * STEP, (n - steep[cid]) * STEP))
