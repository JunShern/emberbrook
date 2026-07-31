"""Pick the SHOWCASE objects per asset from measured.json, and write the render spec.

A PolyHaven vegetation blend holds three kinds of object and only one of them is the plant:
  * the plant variants            <id>_a .. <id>_e        (+ _LOD0..3 bakes)
  * GENERATOR SOURCE parts        _twig_*, _branch_*, _leaves_*, _needle_*, leaf_UV,
                                  <id>_geometry*, *_geonodes_*   — consumed by the modifier
  * bare TRUNK objects            <id>_trunk*             — a real asset in its own right
                                                            (the probe's "bare autumn tree")
"""
import json, re, os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
M = {a['id']: a for a in json.load(open(os.path.join(SRC, 'measured.json')))}

SRC_PARTS = re.compile(
    r'(_twig|_branch|_leaves|_leaf|leaf_uv|_needle|_geometry|geonodes|_dead_branch|_root)',
    re.I)


def showcase(aid, n=4, want_trunk=False):
    a = M[aid]
    pool = []
    for name, v in a['variants'].items():
        if SRC_PARTS.search(name):
            continue
        is_trunk = bool(re.search(r'_trunk', name, re.I))
        if is_trunk != want_trunk:
            continue
        if 'LOD0' not in v['lods']:
            continue
        pool.append((name, v))
    # generators with no baked variants (nettle, some grasses): use the generator objects
    if not pool and not want_trunk:
        for name, g in a['generators'].items():
            if SRC_PARTS.search(name) or re.search(r'_LOD[123]$', name):
                continue
            pool.append((name, dict(height_m=g['height_m'], canopy_width_m=g['canopy_width_m'],
                                    z_min=g['z_min'], lods={'LOD0': g})))
    pool.sort(key=lambda kv: -kv[1]['height_m'])
    # spread across the size range rather than taking the n biggest clones
    if len(pool) > n:
        idx = [round(i * (len(pool) - 1) / (n - 1)) for i in range(n)]
        pool = [pool[i] for i in sorted(set(idx))]
    return pool


# category assignment is a PROPOSAL for the coordinator; measured height decides nothing
# on its own but it is what the proposal is argued from.
CATEGORY = {
    'pine_tree_01': 'treeline-conifer', 'fir_tree_01': 'treeline-conifer',
    'fir_sapling_medium': 'treeline-conifer',
    'jacaranda_tree': 'hero-tree?', 'tree_small_02': 'broadleaf-small',
    'island_tree_01': 'broadleaf-small', 'island_tree_02': 'broadleaf-small',
    'island_tree_03': 'broadleaf-small',
    'searsia_lucida': 'shrub', 'searsia_burchellii': 'shrub', 'shrub_01': 'shrub',
    'shrub_03': 'shrub', 'nettle_plant': 'shrub', 'fern_02': 'shrub',
    'weed_plant_02': 'groundcover', 'dandelion_01': 'groundcover',
    'grass_medium_01': 'groundcover', 'grass_medium_02': 'groundcover',
    'grass_bermuda_01': 'groundcover',
}

spec = []
for aid in sorted(M):
    a = M[aid]
    objs = showcase(aid)
    trunks = showcase(aid, n=2, want_trunk=True)
    if not objs:
        print('NO SHOWCASE', aid, file=sys.stderr)
        continue
    spec.append(dict(
        id=aid, blend=os.path.join(SRC, 'ph', aid, aid + '.blend'),
        category=CATEGORY.get(aid, '?'),
        objects=[dict(name=n + ('_LOD0' if 'LOD0' in v['lods'] and
                                v['lods']['LOD0']['name'].endswith('_LOD0') else ''),
                      height_m=v['height_m'], width_m=v['canopy_width_m'],
                      z_min=v['z_min'], tris=v['lods']['LOD0']['tris'])
                 for n, v in objs],
        trunks=[dict(name=v['lods']['LOD0']['name'], height_m=v['height_m'],
                     width_m=v['canopy_width_m'], z_min=v['z_min'],
                     tris=v['lods']['LOD0']['tris']) for n, v in trunks],
        leaf_card_m=a.get('leaf_card_m'),
        height_m=a.get('height_m'), canopy_width_m=a.get('canopy_width_m'),
        n_variants=a.get('n_variants'), disk_mb=round(a['disk_bytes'] / 1e6, 1),
    ))

# use the exact object names measured (LOD0 objects carry the _LOD0 suffix, some do not)
for s in spec:
    a = M[s['id']]
    for o in s['objects']:
        base = re.sub(r'_LOD0$', '', o['name'])
        v = a['variants'].get(base) or a['variants'].get(o['name'])
        if v and 'LOD0' in v['lods']:
            o['name'] = v['lods']['LOD0']['name']
        elif base in a['generators']:
            o['name'] = base
        elif o['name'] not in a['generators']:
            print('NAME UNRESOLVED', s['id'], o['name'], file=sys.stderr)

json.dump(spec, open(os.path.join(SRC, 'sheet_spec.json'), 'w'), indent=1)
for s in spec:
    print(f"{s['id']:20} {s['category']:18} {len(s['objects'])} objs "
          f"{[ (o['name'], round(o['height_m'],2)) for o in s['objects'] ]} "
          f"trunks {[t['name'] for t in s['trunks']]}")
