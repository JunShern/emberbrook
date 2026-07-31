"""dressing_measure.py — MEASURE every candidate dressing asset. Never trust the file name.

  Blender -b --python-exit-code 1 --python dressing_measure.py -- <srcdir> <out.json>

PolyHaven vegetation blends are VARIANT SETS, not single objects: <id>_a.._e, each baked at
LOD0..LOD3, laid out APART in world space, and for the newer assets a geometry-nodes
GENERATOR object as well (whose evaluated output is the same plant as LOD0).  A merged
bounding box over that file therefore measures the LAYOUT, not the plant — which is how a
0.16 m dandelion measures 4.21 m wide.  Everything here is measured PER VARIANT, in the
variant's own local frame.

Reported per variant: height_m (Z extent), canopy_width_m (max horizontal extent),
z_min (how far the origin sits off the ground), tris/verts per LOD.
Reported per asset: leaf_card_m — the longest edge of the LEAF SOURCE cards the generator
instances, i.e. how big one alpha card actually is.  That is the number the hero-tree
defect is about: card * instance_scale is what the camera sees.
"""
import bpy, sys, os, json, re, statistics

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
LOD_RE = re.compile(r'_lod(\d)$', re.I)


def evaluated(obj, deps, world=True):
    ev = obj.evaluated_get(deps)
    try:
        me = ev.to_mesh()
    except Exception:
        return None
    if me is None or len(me.vertices) == 0:
        try:
            ev.to_mesh_clear()
        except Exception:
            pass
        return None
    me.calc_loop_triangles()
    M = obj.matrix_world
    pts = [(M @ v.co) if world else v.co for v in me.vertices]
    res = dict(verts=len(me.vertices), tris=len(me.loop_triangles),
               mn=[min(p[i] for p in pts) for i in range(3)],
               mx=[max(p[i] for p in pts) for i in range(3)])
    ev.to_mesh_clear()
    return res


def dims(r):
    return [r['mx'][i] - r['mn'][i] for i in range(3)]


def measure_blend(path, aid):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=path)
    deps = bpy.context.evaluated_depsgraph_get()

    leafcols = {c.name for c in bpy.data.collections
                if re.search(r'(leaves|leaf|needle)', c.name, re.I)}
    out = dict(id=aid, blend_bytes=os.path.getsize(path), variants={}, generators={},
               leaf_cards=[], materials=[], textures=[], notes=[])

    for o in bpy.data.objects:
        if o.type not in ('MESH', 'CURVE', 'SURFACE'):
            continue
        in_leafcol = any(o.name in bpy.data.collections[c].objects for c in leafcols)
        has_gn = any(m.type == 'NODES' and m.node_group for m in o.modifiers)
        # measure in the object's OWN frame (translation removed) so the file's layout
        # of variants cannot leak into the plant's size
        r = evaluated(o, deps, world=True)
        if r is None:
            continue
        d = dims(r)
        rec = dict(name=o.name, verts=r['verts'], tris=r['tris'],
                   height_m=round(d[2], 4), canopy_width_m=round(max(d[0], d[1]), 4),
                   footprint_x=round(d[0], 4), footprint_y=round(d[1], 4),
                   z_min=round(r['mn'][2], 4))
        if has_gn:
            out['generators'][o.name] = rec
            continue
        if in_leafcol:
            rec['longest'] = round(max(d), 4)
            out['leaf_cards'].append(rec)
            continue
        m = LOD_RE.search(o.name)
        lod = int(m.group(1)) if m else 0
        base = LOD_RE.sub('', o.name)
        v = out['variants'].setdefault(base, dict(lods={}))
        v['lods'][f'LOD{lod}'] = rec
        if lod == 0 or 'height_m' not in v:
            v['height_m'] = rec['height_m']
            v['canopy_width_m'] = rec['canopy_width_m']
            v['z_min'] = rec['z_min']

    if out['leaf_cards']:
        L = [c['longest'] for c in out['leaf_cards'] if c['tris'] > 4]
        if L:
            out['leaf_card_m'] = round(statistics.median(L), 4)
            out['leaf_card_min_m'] = round(min(L), 4)
            out['leaf_card_max_m'] = round(max(L), 4)

    H = [v['height_m'] for v in out['variants'].values()]
    if H:
        out['height_m'] = round(max(H), 3)          # the tallest variant is the asset's size
        out['height_range_m'] = [round(min(H), 3), round(max(H), 3)]
        out['canopy_width_m'] = round(max(v['canopy_width_m']
                                          for v in out['variants'].values()), 3)
        out['n_variants'] = len(out['variants'])
        lod0 = [v['lods'].get('LOD0') for v in out['variants'].values()]
        out['tris_lod0_max'] = max((r['tris'] for r in lod0 if r), default=0)
        lod1 = [v['lods'].get('LOD1') for v in out['variants'].values()]
        out['tris_lod1_max'] = max((r['tris'] for r in lod1 if r), default=0)
        out['lods_available'] = sorted({k for v in out['variants'].values() for k in v['lods']})
    if out['generators']:
        g = max(out['generators'].values(), key=lambda r: r['tris'])
        out['generator_height_m'] = g['height_m']
        out['generator_tris'] = g['tris']
        if not H:
            out['height_m'] = g['height_m']
            out['canopy_width_m'] = g['canopy_width_m']

    for m in bpy.data.materials:
        if m.users:
            out['materials'].append(m.name)
    seen = set()
    for im in bpy.data.images:
        if not im.users or im.name in seen:
            continue
        seen.add(im.name)
        fp = bpy.path.abspath(im.filepath) if im.filepath else ''
        out['textures'].append(dict(name=im.name, w=im.size[0], h=im.size[1],
                                    packed=bool(im.packed_file), file=os.path.basename(fp),
                                    bytes=os.path.getsize(fp) if fp and os.path.exists(fp) else 0))
    out['texture_bytes'] = sum(t['bytes'] for t in out['textures'])
    out['disk_bytes'] = out['blend_bytes'] + out['texture_bytes']
    return out


res = []
for aid in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, aid, aid + '.blend')
    if not os.path.exists(p):
        continue
    print('MEASURING', aid, flush=True)
    try:
        res.append(measure_blend(p, aid))
    except Exception as e:
        print('FAILED', aid, e, flush=True)
        res.append(dict(id=aid, error=str(e)))

with open(OUT, 'w') as f:
    json.dump(res, f, indent=1)
print('WROTE', OUT, len(res), 'assets')
