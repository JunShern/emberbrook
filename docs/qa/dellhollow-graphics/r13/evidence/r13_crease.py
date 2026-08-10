"""r13_crease.py — WHICH SURFACES IN THIS TOWN ARE FLAT-SHADED NON-PLANAR QUADS?

A quad whose four corners are not coplanar is TRIANGULATED by the renderer, and if
it is also FLAT shaded the two triangles get different normals: a razor crease down
the diagonal of every panel.  That is what crossing's awning photographs as, and no
texture, value or relief edit can touch it.

Per mesh: the fraction of quads that are non-planar by more than `--tol` metres, and
the fraction of polygons shaded smooth.  A mesh that is >0% non-planar AND 0% smooth
is in the class.
"""
import bpy, sys, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "/tmp/r13_crease.json"
TOL = float(argv[argv.index("--tol") + 1]) if "--tol" in argv else 0.005

res = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render or not o.users_collection:
        continue
    me = o.data
    if not len(me.polygons):
        continue
    mw = o.matrix_world
    nq = 0; bad = 0; worst = 0.0; sm = 0
    for p in me.polygons:
        if p.use_smooth:
            sm += 1
        if len(p.vertices) != 4:
            continue
        nq += 1
        v = [mw @ me.vertices[i].co for i in p.vertices]
        n = (v[1] - v[0]).cross(v[3] - v[0])
        if n.length < 1e-9:
            continue
        n.normalize()
        dev = abs((v[2] - v[0]).dot(n))
        if dev > worst:
            worst = dev
        if dev > TOL:
            bad += 1
    if nq and bad:
        res[o.name] = {"quads": nq, "nonplanar": bad, "frac": bad / nq,
                       "worst_m": round(worst, 4), "polys": len(me.polygons),
                       "smooth": sm, "smooth_frac": sm / len(me.polygons),
                       "mat": [m.name if m else None for m in me.materials]}

json.dump(res, open(OUT, "w"), indent=0)
rows = sorted(res.items(), key=lambda kv: -kv[1]["nonplanar"])
print("NON-PLANAR QUAD MESHES (tol %.3f m): %d of the town's meshes" % (TOL, len(res)))
print("%-34s %6s %6s %6s %8s %8s" % ("object", "quads", "nonpl", "frac", "worst m", "smooth%"))
for k, v in rows[:40]:
    print("%-34s %6d %6d %6.2f %8.3f %8.1f  %s"
          % (k, v["quads"], v["nonplanar"], v["frac"], v["worst_m"],
             100 * v["smooth_frac"], ",".join(m or '-' for m in v["mat"])[:28]))
print("SAVED %s" % OUT)
