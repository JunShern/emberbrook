"""hero_gn_probe.py — can the PolyHaven generator grow a VILLAGE-SIZE tree without
growing its leaves?

  Blender -b --python-exit-code 1 --python hero_gn_probe.py -- <blend> <gn_object>

THE DEFECT BEING TESTED. Round 2 reached 9-13 m broadleaves by instancing a 4.6 m scan at
2.4-2.9x, which multiplies the LEAF CARD by the same factor: a 0.32 m spray card becomes
0.83 m and reads wrong in close-up. The scanned trees ship as geometry-nodes GENERATORS
whose leaf geometry is INSTANCED from a separate collection, so the question is whether the
skeleton can be scaled while the instances stay at native size.

THE INSTRUMENT. For each candidate scale k the generator is evaluated and the realised mesh
measured per material: total height, and MEAN TRIANGLE AREA of the faces carrying the leaf
material. Mean leaf-triangle area is the leaf card's size in the only units that matter to
the camera. If height scales with k while mean leaf-triangle area holds, the fix is real;
if both scale, the generator is just a scale factor by another name.
"""
import bpy, sys, os, json
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, GNOBJ = argv[0], argv[1]
SCALES = [float(x) for x in (argv[2:] or ['1.0', '2.0', '3.0'])]


def tri_area(me, tri):
    a, b, c = (me.vertices[i].co for i in tri.vertices)
    return (b - a).cross(c - a).length / 2.0


def measure(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    mats = [ms.material.name if ms.material else '<none>' for ms in o.material_slots]
    by = {}
    zs = [v.co.z for v in me.vertices]
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    for t in me.loop_triangles:
        n = mats[t.material_index] if t.material_index < len(mats) else '<oob>'
        d = by.setdefault(n, dict(n=0, area=0.0))
        d['n'] += 1
        d['area'] += tri_area(me, t)
    res = dict(height=round(max(zs) - min(zs), 3),
               width=round(max(max(xs) - min(xs), max(ys) - min(ys)), 3),
               tris=len(me.loop_triangles), per_material={})
    for n, d in by.items():
        res['per_material'][n] = dict(tris=d['n'], total_area=round(d['area'], 3),
                                      mean_tri_area=round(d['area'] / max(d['n'], 1), 7),
                                      mean_tri_edge_mm=round(
                                          (d['area'] / max(d['n'], 1) * 2) ** 0.5 * 1000, 2))
    ev.to_mesh_clear()
    return res


out = []
for k in SCALES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    o = bpy.data.objects.get(GNOBJ)
    if o is None:
        print('NO OBJECT', GNOBJ, [x.name for x in bpy.data.objects])
        sys.exit(1)
    if k != 1.0:
        # scale the SKELETON ITSELF (the curve's control points), not the object
        o.data.transform(Matrix.Scale(k, 4))
        try:
            for sp in o.data.splines:
                for p in sp.points:
                    p.radius = p.radius          # radii are relative; left alone on purpose
        except Exception:
            pass
    r = measure(o)
    r['k'] = k
    out.append(r)
    print(f"k={k}: H={r['height']} W={r['width']} tris={r['tris']:,}")
    for n, d in sorted(r['per_material'].items()):
        print(f"    {n:34} tris {d['tris']:9,} mean_tri_area {d['mean_tri_area']:.7f} m2 "
              f"(~{d['mean_tri_edge_mm']:.1f} mm edge)  total {d['total_area']:.2f} m2")
print(json.dumps(out))
