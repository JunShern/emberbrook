"""density_sweep.py — how much foliage does a grown skeleton need to stop reading bare?

  Blender -b --python-exit-code 1 --python density_sweep.py -- <blend> <gn_obj> <crvscale>

Growing the skeleton grows the crown's VOLUME as k^3 while the generator keeps seeding
foliage at its authored density, so a grown tree reads thin. This measures the refill rather
than eyeballing it: for each density setting, the realised leaf triangle COUNT and the
canopy's bounding volume, reported as leaf triangles per cubic metre of crown — and the
median leaf triangle edge alongside, because a "refill" that quietly enlarges the cards
would be the original defect coming back in through the other door.

A WARNING WORTH KEEPING: these inputs are NOT normalised. island_tree_01 ships
density_multiplier = 106.3 against a socket DEFAULT of 0.5, so "set it to 3.2" reads like a
6x increase and is in fact a 33x cut. Always print the before value.
"""
import bpy, sys, os, json, statistics
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, GNOBJ, K = argv[0], argv[1], float(argv[2])
SETTINGS = [
    {},
    dict(density_multiplier=250.0),
    dict(density_multiplier=400.0),
    dict(density_multiplier=400.0, branch_density=2.4),
    dict(density_multiplier=650.0, branch_density=2.4),
]


def run(over):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    o = bpy.data.objects[GNOBJ]
    o.data.transform(Matrix.Diagonal((K, K, K, 1.0)))
    before = {}
    for m in o.modifiers:
        if m.type != 'NODES' or not m.node_group:
            continue
        for it in m.node_group.interface.items_tree:
            if getattr(it, 'item_type', '') != 'SOCKET' or it.in_out != 'INPUT':
                continue
            if it.name in over:
                before[it.name] = m[it.identifier]
                m[it.identifier] = over[it.name]
    o.update_tag()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    mats = [ms.material.name if ms.material else '' for ms in o.material_slots]
    P = [v.co for v in me.vertices]
    mn = [min(p[i] for p in P) for i in range(3)]
    mx = [max(p[i] for p in P) for i in range(3)]
    vol = max((mx[0] - mn[0]) * (mx[1] - mn[1]) * (mx[2] - mn[2]), 1e-6)
    lt = [t for t in me.loop_triangles if t.material_index >= len(mats)]
    step = max(1, len(lt) // 40000)
    edges = []
    for t in lt[::step]:
        a, b, c = (me.vertices[i].co for i in t.vertices)
        edges.append(max((b - a).length, (c - b).length, (a - c).length))
    r = dict(over=over, before=before, H=round(mx[2] - mn[2], 2),
             W=round(max(mx[0] - mn[0], mx[1] - mn[1]), 2), tris=len(me.loop_triangles),
             leaf_tris=len(lt), crown_vol=round(vol, 1),
             leaf_tris_per_m3=round(len(lt) / vol, 1),
             leaf_edge_mm=round(statistics.median(edges) * 1000, 2) if edges else None)
    ev.to_mesh_clear()
    return r


out = []
for s in SETTINGS:
    r = run(s)
    out.append(r)
    print(f"{str(s) or 'NATIVE':58} H{r['H']:6.2f} W{r['W']:6.2f} leaf_tris {r['leaf_tris']:9,} "
          f"per_m3 {r['leaf_tris_per_m3']:8.1f} edge {r['leaf_edge_mm']} mm  before={r['before']}",
          flush=True)
print(json.dumps(out))
