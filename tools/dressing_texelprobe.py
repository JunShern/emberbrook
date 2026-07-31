"""texel_probe.py — does growing the skeleton actually stretch the bark?

  Blender -b --python-exit-code 1 --python texel_probe.py -- <blend> <gn_obj> <k> [<k>...]

The coordinator asked for the bark stretch to be COUNTERED and the texel density printed
before and after. Before countering anything, the stretch has to be measured, because the
premise is not obvious: all three of this asset's materials read UV coordinates, and if the
generator lays UVs down PROPORTIONALLY TO ARC LENGTH then a grown skeleton gets grown UVs
and there is no stretch to counter at all.

TEXEL DENSITY, per material, in pixels per metre:
    density = sqrt( sum(uv_area) * texW * texH / sum(area_m2) )
UV area is computed on the evaluated mesh's active UV layer, 3D area on the same triangles,
so the ratio is the real one the renderer samples at. A material whose density is flat
across k needs no counter-scale; one whose density falls as 1/k is stretched exactly by k.
"""
import bpy, sys, json
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, GNOBJ = argv[0], argv[1]
KS = [float(x) for x in (argv[2:] or ['1.0', '3.0'])]


def tri_area(a, b, c):
    return (b - a).cross(c - a).length / 2.0


def uv_area(a, b, c):
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2.0


def texsize(mat):
    if not mat or not mat.use_nodes:
        return (1024, 1024)
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and n.image.size[0]:
            return tuple(n.image.size)
    return (1024, 1024)


out = []
for k in KS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    o = bpy.data.objects[GNOBJ]
    if k != 1.0:
        o.data.transform(Matrix.Diagonal((k, k, k, 1.0)))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    uvl = me.uv_layers.active
    mats = [ms.material for ms in o.material_slots]
    acc = {}
    for t in me.loop_triangles:
        mi = t.material_index
        name = (mats[mi].name if mi < len(mats) and mats[mi] else f'<instanced:{mi}>')
        d = acc.setdefault(name, dict(a3=0.0, auv=0.0, n=0))
        vs = [me.vertices[i].co for i in t.vertices]
        d['a3'] += tri_area(*vs)
        d['n'] += 1
        if uvl:
            uvs = [uvl.data[li].uv for li in t.loops]
            d['auv'] += uv_area(*uvs)
    row = dict(k=k, materials={})
    for name, d in sorted(acc.items()):
        m = next((x for x in mats if x and x.name == name), None)
        W, H = texsize(m)
        dens = ((d['auv'] * W * H / d['a3']) ** 0.5) if d['a3'] > 0 and d['auv'] > 0 else 0.0
        row['materials'][name] = dict(tris=d['n'], area_m2=round(d['a3'], 3),
                                      uv_area=round(d['auv'], 4), tex=[W, H],
                                      px_per_m=round(dens, 1))
    ev.to_mesh_clear()
    out.append(row)
    print(f'k={k}')
    for name, d in row['materials'].items():
        print(f"   {name:38} {d['tris']:9,} tris  area {d['area_m2']:9.2f} m2  "
              f"uv {d['uv_area']:8.3f}  {d['tex'][0]}px  ->  {d['px_per_m']:8.1f} px/m")
if len(out) > 1:
    print('\nRATIO vs k=1 (1.00 = no stretch; 1/k = stretched exactly by k):')
    base = out[0]['materials']
    for row in out[1:]:
        for name, d in row['materials'].items():
            b = base.get(name)
            if b and b['px_per_m']:
                print(f"   k={row['k']}  {name:38} {d['px_per_m'] / b['px_per_m']:.3f}")
print(json.dumps(out))
