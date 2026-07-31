"""slim_gn_probe.py — can the generator be grown into a COLUMNAR tree (birch/poplar/aspen)
without stretching the leaves?

  Blender -b --python-exit-code 1 --python slim_gn_probe.py -- <blend> <gn_object> \
      <sx,sy,sz> [<sx,sy,sz> ...]

THE DEFECT BEING TESTED. Both style probes faked the slim village trees by scaling a broad
scan 0.62/0.62/1.18 — a NON-UNIFORM OBJECT SCALE, which stretches every leaf card with the
tree and is exactly what reads wrong. This scales the SKELETON CURVE non-uniformly instead
and leaves the instanced leaf cards alone, so the question is whether the leaves stay
square and native while the crown becomes a column.

THE INSTRUMENT, and it needs one more number than the hero probe: a mean triangle AREA
cannot see a stretch (a card squashed in x and pulled in z can hold its area). So leaf
cards are measured as REALISED INSTANCES: the leaf-material faces are grouped into
connected islands and each island's bounding box is measured. Reported: median island
longest edge, and the median ASPECT (longest/shortest of the horizontal box) — a stretched
card shows up in the aspect even when the area holds.
"""
import bpy, sys, os, json, statistics
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, GNOBJ = argv[0], argv[1]
# 'obj:sx,sy,sz' scales the OBJECT (what both probes did — leaves stretch with the tree);
# a bare 'sx,sy,sz' scales the SKELETON CURVE (leaves are instanced afterwards, untouched)
SCALES = []
for a in (argv[2:] or ['1,1,1']):
    obj = a.startswith('obj:')
    SCALES.append((obj, tuple(float(v) for v in a.split(':')[-1].split(','))))
LEAF_HINT = ('leaf', 'leaves', 'needle')


def leaf_tris(me, mats, WM, sample=60000):
    """Leaf geometry measured TRIANGLE BY TRIANGLE.

    Instanced leaf cards come in with a material_index past the host object's own slots
    (that is how they showed up as '<oob>' in the hero probe), so "not one of my slots" is
    the reliable way to find them. Two numbers per triangle: its LONGEST EDGE, which is the
    card's size in metres, and its ASPECT (longest/shortest edge), which is the only one of
    the two that can see a STRETCH — a card squashed in x and pulled in z keeps its area.
    """
    me.calc_loop_triangles()
    own_leaf = {i for i, n in enumerate(mats) if any(h in n.lower() for h in LEAF_HINT)}
    tris = [t for t in me.loop_triangles
            if t.material_index >= len(mats) or t.material_index in own_leaf]
    if not tris:
        return []
    step = max(1, len(tris) // sample)
    out = []
    for t in tris[::step]:
        a, b, c = (WM @ me.vertices[i].co for i in t.vertices)
        e = sorted(((b - a).length, (c - b).length, (a - c).length))
        if e[0] < 1e-9:
            continue
        out.append(dict(longest=e[2], aspect=e[2] / e[0]))
    return out


out = []
for obj_level, sc in SCALES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    o = bpy.data.objects.get(GNOBJ)
    if sc != (1.0, 1.0, 1.0):
        if obj_level:
            o.scale = sc
        else:
            o.data.transform(Matrix.Diagonal((*sc, 1.0)))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mats = [ms.material.name if ms.material else '' for ms in o.material_slots]
    M = o.matrix_world
    P = [M @ v.co for v in me.vertices]
    zs = [p.z for p in P]
    xs = [p.x for p in P]
    ys = [p.y for p in P]
    H = max(zs) - min(zs)
    W = max(max(xs) - min(xs), max(ys) - min(ys))
    isl = leaf_tris(me, mats, M)
    r = dict(scale=sc, obj_level=obj_level, height=round(H, 3), width=round(W, 3),
             slenderness=round(H / max(W, 1e-6), 2), tris=len(me.polygons),
             n_leaf_tris_sampled=len(isl))
    if isl:
        r['leaf_tri_longedge_median_m'] = round(statistics.median(i['longest'] for i in isl), 5)
        r['leaf_tri_aspect_median'] = round(statistics.median(i['aspect'] for i in isl), 3)
    ev.to_mesh_clear()
    out.append(r)
    print(f"{'OBJ' if obj_level else 'CURVE'} {sc}: H={r['height']} W={r['width']} H/W={r['slenderness']} "
          f"faces={r['tris']:,} leaftris={r['n_leaf_tris_sampled']} "
          f"leaf_edge={r.get('leaf_tri_longedge_median_m')} "
          f"aspect={r.get('leaf_tri_aspect_median')}", flush=True)
print(json.dumps(out))
