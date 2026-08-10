"""r13_awning.py — DOES THE AWNING INTERSECT, FLOAT, OR ABUT?

Round 12 named crossing's four-round standing complaint on the geometry for the
first time: 78.5% `qm_awning_0 | mat_qm_awning` at 5.3 m, described as "an
untextured grey polygon CLIPPING THROUGH the wooden walkway".  Rounds 8-11 read
that as relief, then value, then texture.  This asks the word itself.

Three tests, all on the shipped master:
  1. BVHTree.overlap of every awning against every other mesh in the town —
     a REAL triangle-triangle intersection, not a bbox test.  A bbox overlap is
     not clipping; a triangle overlap is.
  2. per-vertex DOWN-RAY to the nearest surface under it, with the object named:
     a floating sheet has a gap everywhere, an abutting one has a gap at its
     supported end and not at the other.
  3. the SILHOUETTE question the picture actually asks: the awning's own
     thickness.  A ruled sheet with zero thickness seen from above IS a polygon.
"""
import bpy, sys, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "/tmp/r13_awning.json"
PFX = argv[argv.index("--pfx") + 1] if "--pfx" in argv else "qm_awning,shelf_awning"
PFX = tuple(PFX.split(","))

dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene

targets = [o for o in bpy.data.objects
           if o.type == 'MESH' and not o.hide_render
           and any(o.name.startswith(p) for p in PFX)]
print("targets: %d  %s" % (len(targets), [o.name for o in targets]))

others = [o for o in bpy.data.objects
          if o.type == 'MESH' and not o.hide_render and o not in targets
          and len(o.data.vertices)]


def bvh(o):
    m = o.matrix_world
    vs = [m @ v.co for v in o.data.vertices]
    ps = [tuple(p.vertices) for p in o.data.polygons]
    return BVHTree.FromPolygons(vs, ps, all_triangles=False)


res = {}
for t in targets:
    m = t.matrix_world
    ws = [m @ v.co for v in t.data.vertices]
    xs = [v.x for v in ws]; ys = [v.y for v in ws]; zs = [v.z for v in ws]
    bb = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    tb = bvh(t)
    hits = []
    for o in others:
        ob = o.bound_box
        om = o.matrix_world
        oc = [om @ Vector(c) for c in ob]
        ox = [v.x for v in oc]; oy = [v.y for v in oc]; oz = [v.z for v in oc]
        if (min(ox) > bb[1] or max(ox) < bb[0] or min(oy) > bb[3] or max(oy) < bb[2]
                or min(oz) > bb[5] or max(oz) < bb[4]):
            continue                                # bbox miss: cannot overlap
        ov = tb.overlap(bvh(o))
        if ov:
            hits.append({"obj": o.name,
                         "mat": (o.data.materials[0].name if o.data.materials
                                 and o.data.materials[0] else None),
                         "tri_pairs": len(ov)})
    # per-vertex down-ray, self excluded by nudging the origin below the vertex
    gaps = []
    for v in ws:
        ok, loc, nor, idx, obj, _ = sc.ray_cast(dg, v + Vector((0, 0, -0.002)),
                                                Vector((0, 0, -1)), distance=60.0)
        gaps.append({"z": round(v.z, 4),
                     "gap": (round(v.z - loc.z, 4) if ok else None),
                     "under": (obj.name if ok else None)})
    g = [q["gap"] for q in gaps if q["gap"] is not None]
    res[t.name] = {
        "bbox": [round(x, 3) for x in bb],
        "dims": [round(bb[1] - bb[0], 3), round(bb[3] - bb[2], 3), round(bb[5] - bb[4], 3)],
        "verts": len(ws), "faces": len(t.data.polygons),
        "mat": (t.data.materials[0].name if t.data.materials else None),
        "overlaps": hits,
        "gap_min": (round(min(g), 4) if g else None),
        "gap_max": (round(max(g), 4) if g else None),
        "gap_n": len(g), "gap_none": len(gaps) - len(g),
        "under_names": sorted(set(q["under"] for q in gaps if q["under"])),
        "gaps": gaps,
    }
    print("%-22s dims %.2f x %.2f x %.2f  overlaps %d  gap %s..%s  under %s"
          % (t.name, res[t.name]["dims"][0], res[t.name]["dims"][1],
             res[t.name]["dims"][2], len(hits),
             res[t.name]["gap_min"], res[t.name]["gap_max"],
             ",".join(res[t.name]["under_names"][:4])))
    for h in hits:
        print("    OVERLAP %s (%s) %d tri pairs" % (h["obj"], h["mat"], h["tri_pairs"]))

json.dump(res, open(OUT, "w"), indent=0)
print("SAVED %s" % OUT)
