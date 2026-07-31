"""treeline_compare.py — is pine_tree_01 LOAD-BEARING for the Whisperwood treeline?

  Blender -b --python-exit-code 1 --python treeline_compare.py -- <outdir> [only ...]

THE QUESTION, from lane B's tri gate: pine_tree_01_LOD0 is 17.2 M tris — 68% of the whole
library — and its source is 777 MB, the biggest disk line in the intake. It is only worth
that if the treeline cannot be carried without it. Decided by rendering, not by tri count.

THE BAND IS THE SAME BAND IN ALL THREE VARIANTS: same seed, same 34 positions, same
per-tree rotations and scale jitter, so the only thing that differs between frames is WHICH
SPECIES stands at each station. Trees are placed at 26-72 m from a 1.8 m camera — the
distance the round-2 probe actually shows the treeline at — and they are instanced at LOD1,
because LOD1 is what a treeline at that distance would ever use. If LOD1 carries the band,
LOD0 never ships.
"""
import bpy, sys, os, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_rig as rig

S = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(S, 'ph')
argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
ONLY = set(argv[1:])
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(S, 'sapling_ext'))

# 34 stations, fixed once so every variant plants the same wood
random.seed(11)
STATIONS = []
for i in range(34):
    x = -46 + (i / 33.0) * 92 + random.uniform(-2.0, 2.0)
    y = 30.0 + random.uniform(0.0, 30.0)
    STATIONS.append((x, y, random.uniform(0, 6.283), random.uniform(0.82, 1.25)))


def load(aid, obj):
    blend = os.path.join(PH, aid, aid + '.blend')
    with bpy.data.libraries.load(blend, link=False) as (df, dt):
        if obj not in df.objects:
            raise SystemExit(f'{obj} not in {blend}')
        dt.objects = [obj]
    o = dt.objects[0]
    o.name = 'SRC_' + obj
    return o


def sapling_conifer(height=18.0):
    """a Sapling conifer, CC0-bark skinned — the 'can a generator carry it' arm"""
    import importlib
    m = importlib.import_module('sapling_ext')
    try:
        m.register()
    except Exception:
        pass
    p = os.path.join(S, 'sapling_ext', 'presets', 'douglas_fir.py')
    params = {}
    for line in open(p):
        line = line.strip()
        if not line.startswith('op.'):
            continue
        k, _, v = line[3:].partition('=')
        try:
            params[k.strip()] = eval(v.strip())
        except Exception:
            pass
    params.pop('bevel', None)
    params['scale'] = height
    params['showLeaves'] = True
    bpy.ops.curve.tree_add(**params)
    tree = bpy.data.objects.get('tree')
    leaves = bpy.data.objects.get('leaves')
    objs = [o for o in (tree, leaves) if o]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.object
    o.name = 'SRC_sapling_conifer'
    return o


VARIANTS = {
    'T1-pine-fir-mix': [('pine_tree_01', 'pine_tree_01_a_LOD1', 0.55),
                        ('fir_tree_01', 'fir_tree_01_a_LOD1', 1.0)],
    'T2-fir-only': [('fir_tree_01', 'fir_tree_01_a_LOD1', 0.5),
                    ('fir_tree_01', 'fir_tree_01_b_LOD1', 1.0)],
    'T3-fir-plus-sapling': [('SAPLING', None, 0.5),
                            ('fir_tree_01', 'fir_tree_01_a_LOD1', 1.0)],
}

meta = []
for vid, pool in VARIANTS.items():
    if ONLY and vid not in ONLY:
        continue
    sc = rig.scene()
    rig.ground()
    srcs = []
    for aid, obj, p in pool:
        src = sapling_conifer() if aid == 'SAPLING' else load(aid, obj)
        srcs.append((src, p, aid if aid == 'SAPLING' else obj))
    cols = []
    for src, p, label in srcs:
        c = bpy.data.collections.new('C_' + label)
        c.objects.link(src)
        try:
            sc.collection.objects.unlink(src)
        except Exception:
            pass
        cols.append((c, p, label))
    random.seed(11)
    counts = {}
    for (x, y, rz, s) in STATIONS:
        r = random.random()
        pick = next((c for c in cols if r < c[1]), cols[-1])
        e = bpy.data.objects.new(f'tl_{len(counts)}_{pick[2]}', None)
        e.instance_type = 'COLLECTION'
        e.instance_collection = pick[0]
        e.location = (x, y, 0)
        e.rotation_euler = (0, 0, rz)
        e.scale = (s, s, s)
        sc.collection.objects.link(e)
        counts[pick[2]] = counts.get(pick[2], 0) + 1
    rig.human(-3.0, 12.0)
    mn, mx, tris_src = rig.bbox([s[0] for s in srcs])
    rig.shoot(sc, OUT, vid, (0.0, -34.0, 1.80), (0.0, 40.0, 8.0), 40)
    meta.append(dict(id=vid, counts=counts, src_tris=tris_src, stations=len(STATIONS)))
    print('TREELINE', vid, counts, 'source tris', tris_src, flush=True)

p = os.path.join(OUT, 'treeline.json')
old = json.load(open(p)) if os.path.exists(p) else []
by = {m['id']: m for m in old}
by.update({m['id']: m for m in meta})
json.dump([by[k] for k in sorted(by)], open(p, 'w'), indent=1)
print('DONE')
