"""make_manifest.py — the dressing library manifest. THE MANIFEST IS THE INTERFACE.

  python3 make_manifest.py <libdir> <verify.json> <measured.json> <out.json>

Written to the dressing-engine lane's contract (version 1, its class vocabulary, its file
layout). Every height/width/tri figure comes from `lib_verify.py`'s append-and-evaluate of
the SHIPPED file — not from the source scan, not from a note — so the manifest describes
what a builder will actually get.

TWO CONVENTIONS ADDED, both earned:
  `overrides`  Any generator input this library sets is recorded as {before, after}. These
               inputs are NOT normalised: island_tree_01 ships density_multiplier = 106.3
               against a socket default of 0.5, so "3.2" reads like a rise and is a 33x cut.
               A bare after-value in a manifest would hand that trap to the next reader.
  `up`         "+Z". Blender is Z-up and nothing is rotated at intake; the glTF exporter is
               what converts to +Y for anything that later ships in a GLB. A library rotated
               at intake is one every consumer has to un-rotate.
"""
import json, os, sys

LIB, VERIFY, MEASURED, OUT = sys.argv[1:5]
V = {r['id']: r for r in json.load(open(VERIFY))}
M = {a['id']: a for a in json.load(open(MEASURED))}

CLS = {
    'jacaranda_tree': 'canopy_broad', 'jacaranda_tree_trunk': 'canopy_broad',
    'island_tree_01': 'canopy_broad', 'island_tree_02': 'canopy_broad',
    'island_tree_03': 'canopy_broad', 'tree_small_02': 'canopy_broad',
    'fir_tree_01': 'conifer', 'fir_sapling_medium': 'conifer',
    'searsia_burchellii': 'shrub', 'searsia_lucida': 'bramble',
    'fern_02': 'fern',
    'shrub_01': 'weed', 'shrub_03': 'weed', 'nettle_plant': 'weed',
    'weed_plant_02': 'weed', 'dandelion_01': 'weed',
    'grass_medium_01': 'grass', 'grass_medium_02': 'grass', 'grass_bermuda_01': 'grass',
}
NOTE = {
    'jacaranda_tree': 'ACCENT HERO, 2-4 deliberate placements. Fully leafed 19.51 m '
                      'broadleaf; the round-2 note recorded it as a 10.36 m leafless tree, '
                      'which was its bare-trunk sibling object. Silhouette is subtropical '
                      'and the placement is reversible - call it "the spreading fine-leaf '
                      'tree" in board notes, not by species.',
    'jacaranda_tree_trunk': 'BARE tree, no foliage. The round-2 autumn accent at the '
                            'water edge. Same source blend as jacaranda_tree.',
    'fir_sapling_medium': 'MEASURED 8.84 m. The name says sapling; the tape does not.',
    'shrub_01': '0.39 m. Named shrub, measured understory - class is by measurement.',
    'shrub_03': '0.40 m. Named shrub, measured understory.',
    'searsia_lucida': 'The boundary duty: bramble spilling over the dry-stone row.',
    'island_tree_01': 'The hero-tree BASE: its generator scales by skeleton curve, which '
                      'grows the tree while instanced leaf cards stay native size.',
}
# what a builder is allowed to do with each: plates-only until an impostor pass exists
BUDGET = {'canopy_broad': 'plates-only', 'canopy_slim': 'plates-only',
          'conifer': 'plates-only', 'shrub': 'plates-only', 'bramble': 'plates-only',
          'fern': 'ship-in-GLB', 'weed': 'ship-in-GLB', 'grass': 'ship-in-GLB'}

assets = []
for aid in sorted(V):
    v = V[aid]
    m = M.get(aid.replace('_trunk', ''), {})
    a = dict(
        id=aid, cls=CLS.get(aid, 'weed'),
        file=f'veg/{aid}/{aid}.blend', collection=v['collection'],
        height_m=v['height_m'], canopy_width_m=v['canopy_width_m'],
        tris=v['tris'], objects=v['objects'], up='+Z', origin='ground',
        license='CC0', source='polyhaven',
        source_url=f'https://polyhaven.com/a/{aid.replace("_trunk", "")}',
        realtime_budget=BUDGET.get(CLS.get(aid, 'weed'), 'plates-only'),
        measured_by='tools/dressing_verify.py (append + evaluate of the shipped file)',
        bytes=v['bytes'],
    )
    if aid in NOTE:
        a['note'] = NOTE[aid]
    if m.get('leaf_card_m'):
        a['leaf_card_m'] = m['leaf_card_m']
    assets.append(a)

textures = [
    dict(id='leafy_grass', role='ground_turf', license='CC0', source='polyhaven',
         diffuse='tex/leafy_grass_Diffuse.jpg', normal='tex/leafy_grass_nor_gl.jpg',
         rough='tex/leafy_grass_Rough.jpg'),
    dict(id='brown_mud_leaves_01', role='ground_mud', license='CC0', source='polyhaven',
         diffuse='tex/brown_mud_leaves_01_Diffuse.jpg',
         normal='tex/brown_mud_leaves_01_nor_gl.jpg',
         rough='tex/brown_mud_leaves_01_Rough.jpg'),
]

# DERIVED assets: a base asset plus generator overrides. Declared here so the engine can
# see them coming; they are not files yet and carry "status": "pending".
derived = [
    dict(id='hero_broad_12m', cls='canopy_broad', status='pending', base='island_tree_01',
         skeleton_scale=[3.0, 3.0, 3.0],
         overrides={'density_multiplier': {'before': 106.3, 'after': 170.0},
                    'branch_density': {'before': 1.46, 'after': 2.4}},
         expect=dict(height_m=12.19, canopy_width_m=10.69, tris=12646379,
                     leaf_card_mm=9.85),
         note='PRIMARY temperate hero. Skeleton-curve scale, not object scale: leaf cards '
              'stay at native size (9.85 mm vs 10.07 mm native) where object-scaling to the '
              'same height gives 26.17 mm. KNOWN COST: the trunk carries a UNIQUE UNWRAP '
              'whose UV area is invariant under skeleton scale (0.652 at k=1 and k=3), so '
              'its texel density falls exactly 1/k - 520.0 -> 173.3 px/m at k=3. This '
              'CANNOT be countered by scaling the UV mapping (the unwrap would leave its '
              'own island); the only clean fix is a tileable triplanar bark, which trades '
              'the scan trunk for a generic one. Accepted at 3x per coordinator ruling.'),
    dict(id='slim_poplar_14m', cls='canopy_slim', status='pending', base='sapling_tree_gen',
         note='PRIMARY canopy_slim for the 15 village slims. Procedural (Sapling extension '
              'v0.3.7, GPL-3.0 - binds the add-on code, NOT the generated geometry, so no '
              'attribution), CC0 oak bark + CC0 single-leaf atlas. Measured 14.70 m, '
              'slenderness 2.94, 83,804 tris - 32x lighter than the skeleton-columnar '
              'alternative at a comparable silhouette.',
         expect=dict(height_m=14.703, canopy_width_m=5.004, tris=83804, leaf_card_m=0.10)),
    dict(id='slim_skeleton_12m', cls='canopy_slim', status='pending', base='island_tree_01',
         skeleton_scale=[0.6, 0.6, 3.0],
         overrides={'density_multiplier': {'before': 106.3, 'after': 190.0},
                    'branch_density': {'before': 1.46, 'after': 2.2}},
         expect=dict(height_m=11.691, canopy_width_m=3.529, tris=2655581,
                     leaf_card_mm=9.85),
         note='canopy_slim for NEAR-CAMERA placements only - scanned bark and leaves, but '
              '32x the cost of slim_poplar_14m. Same bark texel caveat as hero_broad_12m.'),
    dict(id='mid_broad_13m', cls='canopy_broad', status='pending', base='sapling_tree_gen',
         note='MID-GROUND filler past ~15 m: generic is fine at that distance. 13.29 m, '
              '428,702 tris, leaf size SET at 0.14 m rather than inherited.',
         expect=dict(height_m=13.29, canopy_width_m=13.315, tris=428702, leaf_card_m=0.14)),
]

# derived assets that have BEEN BUILT AND PASSED THE GATE get their measured values and
# status 'shipped'; the rest stay 'pending' with their expected values
DV = os.path.join(os.path.dirname(OUT) or '.', 'verify_derived.json')
if os.path.exists(DV):
    got = {r['id']: r for r in json.load(open(DV))}
    for d in derived:
        r = got.get(d['id'])
        if not r or r.get('fails'):
            continue
        d['status'] = 'shipped'
        d['file'] = f"veg/{d['id']}/{d['id']}.blend"
        d['collection'] = r['collection']
        d['height_m'] = r['height_m']
        d['canopy_width_m'] = r['canopy_width_m']
        d['tris'] = r['tris']
        d['objects'] = r['objects']
        d['bytes'] = r['bytes']
        d['up'] = '+Z'
        d['origin'] = 'ground'
        d['realtime_budget'] = 'plates-only'
        d['measured_by'] = 'tools/dressing_verify.py (append + evaluate of the shipped file)'
        d['license'] = ('CC0' if d.get('base') != 'sapling_tree_gen' else
                        'CC0 assets; generated geometry unencumbered (Sapling add-on is '
                        'GPL-3.0, which binds its code and not its output)')

man = dict(
    version=1,
    root='public/assets/dressing',
    generated_by='tools/dressing_manifest.py',
    up='+Z',
    realtime_budget={'instances': 420, 'tris': 260000, 'textures_mb': 24},
    conventions=dict(
        overrides='Any generator input the library sets is recorded as {before, after}. '
                  'These inputs are NOT normalised - island_tree_01 ships '
                  'density_multiplier 106.3 against a socket default of 0.5 - so a bare '
                  'after-value would hand the next reader a 33x trap.',
        up='+Z (Blender). Nothing is rotated at intake; glTF export converts to +Y.',
        origin='Every object is seated at (x centre, y centre, z min) = (0,0,0). The source '
               'files lay variants out apart, which is what made a 0.16 m dandelion measure '
               '4.21 m wide.',
        resolution='PER-CLASS, set by what a camera can resolve, and the next asset follows '
                   'it without asking: generator assets ship the generator and NONE of the '
                   'baked LODs; trees and shrubs get 1k maps and LOD0+LOD1; understory and '
                   'groundcover get 512 maps and LOD1 only, because a 1k map on a 0.15 m '
                   'weed is texels nobody sees. Alpha maps stay PNG at every size (JPEG '
                   'haloes a cutout edge); everything else is JPEG q92.',
        representation='Assets with a geometry-nodes generator ship the GENERATOR, not the '
                       'baked LODs: the source blends hold generator + LOD0 + LOD1 as '
                       'siblings in one collection, and instancing that collection renders '
                       'the same plant three times over.',
    ),
    dropped=[dict(id='pine_tree_01', reason='Not load-bearing for the Whisperwood treeline '
                                            'on a same-station same-seed comparison at LOD1 '
                                            '(docs/qa/emberbrook/dressing/sheet-6-treeline.jpg). '
                                            'Removing it drops 777 MB of source and a '
                                            '17.2 M-tri LOD0, 68% of the library.')],
    assets=assets,
    derived=derived,
    textures=textures,
)
json.dump(man, open(OUT, 'w'), indent=1)
print(f'{OUT}: {len(assets)} assets, {len(derived)} derived (pending), '
      f'{len(textures)} textures, '
      f"{sum(a['bytes'] for a in assets)/1e6:.1f} MB of blends")
by = {}
for a in assets:
    by[a['cls']] = by.get(a['cls'], 0) + 1
print('by class:', by)
