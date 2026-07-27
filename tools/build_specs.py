#!/usr/bin/env python3
"""Build public/assets/iso/specs.json — the ASSET SPEC REGISTRY (intent).

One record per painted asset: what it IS, how big it should be, and the REAL
prompt to regenerate it with a future model. The slicers READ this (declared
footprints + door declarations live here now, not in per-script PROPS tables)
and WRITE their measurements into the *-metrics.json outcome files. Spec =
intent; metrics = outcome; the height gate compares the two.

Regeneration-with-a-better-model, end to end:
  1. read specs.json -> per asset: catalog, prompt, recipe, declaredFootprint,
     targetHeightCells, refs.
  2. the catalog's template generator (blocks9_template / festival_template /
     interior_template / bldg_template) draws the registration sheet from the
     declaredFootprints in specs.json — no hand table to drift.
  3. feed template + prompt (which now STATES the target height as a multiple
     of pad width) to the model.
  4. the slicer re-measures footprint (base_containment) AND height
     (height_gate) and writes both back to metrics; regeneration is accepted
     only when both gate PASS.

CANONICAL SIZE TABLE (metres; 1 cell = 0.5 m; cells = m/0.5). Documented per
asset in `notes`. Adjusted from the director's table with judgment where the
painted silhouette legitimately exceeds the "functional" height (a bench's
backrest, a stall's ridge vs its counter).
"""
import json, os

M = 0.5  # metres per cell

# id, catalog, footprint[w,h], heightM, mark/recipe, prompt-intent, notes
# heightM is the TOTAL painted silhouette height (ground to topmost paint).
A = []
def spec(id, catalog, foot, hM, shape, bg, tmpl, refs, prompt, notes, gen=None):
    A.append({
        'id': id, 'catalog': catalog,
        'declaredFootprint': foot,
        'targetHeightM': hM, 'targetHeightCells': round(hM / M, 2),
        'recipe': {'mark': shape, 'background': bg,
                   'templatePlaceholder': tmpl, 'refs': refs},
        'prompt': prompt,
        'generation': gen or {'model': 'gemini-2.5-flash-image',
                              'date': '2026-07-27', 'outputSize': [1024, 1024]},
        'notes': notes,
    })

# ---------- style preamble shared by every outdoor prop sheet region ----------
ISO = ('hand-painted semi-realistic isometric game art, true 2:1 dimetric '
       'projection, soft warm dusk lighting, cohesive autumn-festival palette, '
       'no cast shadow on the grey background, no text, no watermark')

def prop_prompt(name, desc, foot, cells, mult):
    return ('%s. Painted in its 3x3 sheet region STANDING ON the flat magenta '
            'registration pad (its %dx%d-cell footprint = %.1f m x %.1f m of '
            'ground); the base of the object covers the pad, nothing of the '
            'body spills past the pad edges at ground level. CRITICAL HEIGHT: '
            'the %s stands %.1f m tall — %s. %s.'
            % (desc, foot[0], foot[1], foot[0] * M, foot[1] * M, name,
               cells * M, mult, ISO))

# =========================== BLOCKS9 (9 outdoor props) ===========================
spec('barrel', 'blocks9', [1, 1], 0.9, '1x1 magenta pad', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('barrel', 'A single wooden ale barrel, iron hoops', [1, 1], 1.8,
                 'about 1.8x its pad width — a barrel reaches an adult to the waist'),
     'Waist-high barrel, 0.9 m. Was painted 0.36 m (REROLL).')
spec('crate', 'blocks9', [1, 1], 0.6, '1x1 magenta pad', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('crate', 'A wooden shipping crate, slatted sides', [1, 1], 1.2,
                 'about 1.2x its pad width — knee-to-thigh high'),
     'Knee-high crate, 0.6 m. Was 0.35 m (REROLL).')
spec('lamppost', 'blocks9', [1, 1], 3.0, '1x1 magenta pad', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('lamppost', 'A wrought-iron street lamppost with a glass lantern head',
                 [1, 1], 6.0,
                 'SIX times its pad width — a tall street lamp, nearly twice an '
                 'adult\'s height, the lantern head high overhead'),
     'Tall street lamp, 3.0 m. Was 0.96 m — the headline defect (REROLL).')
spec('bench', 'blocks9', [1, 2], 0.85, '1x2 magenta strip', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('bench', 'A long wooden park bench with a backrest, seen along its length',
                 [1, 2], 1.7,
                 'about 1.7x its pad WIDTH tall to the top of the backrest '
                 '(seat 0.45 m, backrest to ~0.85 m)'),
     'Table gives seat 0.45 m; the painted silhouette includes the backrest, '
     'so TOTAL target = 0.85 m = 1.7 cells. Judgment adjust, documented.')
spec('planter', 'blocks9', [1, 2], 0.8, '1x2 magenta strip', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('planter', 'A long wooden trough planter spilling autumn flowers',
                 [1, 2], 1.6, 'about 1.6x its pad width tall including the blooms'),
     'Not in the director table; a knee-to-thigh flower trough ~0.8 m. Assigned.')
spec('firewood', 'blocks9', [1, 2], 0.8, '1x2 magenta strip', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('firewood', 'A low stacked row of split firewood logs', [1, 2], 1.6,
                 'about 1.6x its pad width tall — a waist-high stack'),
     'Stacked-log row ~0.8 m. Assigned (table lists festival logpile, not this).')
spec('stall', 'blocks9', [2, 2], 2.2, '2x2 magenta pad', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('stall', 'A market stall: a counter under a peaked cloth awning on posts',
                 [2, 2], 4.4,
                 'about 2.2x its pad width tall at the awning ridge — an adult '
                 'stands comfortably under it'),
     'Awning ridge 2.2 m per table. Was 1.7 m (REROLL/NOTE boundary).')
spec('well', 'blocks9', [2, 2], 2.2, '2x2 magenta pad', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('well', 'A round stone well with a shingled little roof on posts',
                 [2, 2], 4.4, 'about 2.2x its pad width tall including the roof'),
     'Well incl. roof 2.2 m per table. Was 1.5 m (REROLL).')
spec('tree', 'blocks9', [2, 2], 5.0, '2x2 magenta pad', 'flat light grey', False,
     ['blocks9-template.png'],
     prop_prompt('tree', 'A mature autumn tree, full canopy, trunk rising from the pad',
                 [2, 2], 10.0,
                 'about FIVE times its pad width tall — a real tree towers three '
                 'times an adult\'s height; the canopy may overhang the pad but '
                 'the trunk base sits on it'),
     'Tree 4.5-6 m -> target 5.0 m mid. Was 1.8 m — a shrub (REROLL).')

# =========================== FESTIVAL (9 outdoor props) ==========================
spec('brazier', 'festival', [1, 1], 1.2, '1x1 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('brazier', 'A standing iron fire brazier on legs, small flames',
                 [1, 1], 2.4, 'about 2.4x its pad width tall on its legs'),
     'Standing brazier ~1.2 m. Assigned.')
spec('applecrate', 'festival', [1, 1], 0.6, '1x1 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('applecrate', 'A wooden crate heaped with red apples', [1, 1], 1.2,
                 'about 1.2x its pad width — knee high'),
     'Crate of apples ~0.6 m (crate class).')
spec('sign', 'festival', [1, 1], 2.0, '1x1 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('sign', 'A tall wooden signpost with a hanging painted board', [1, 1], 4.0,
                 'about FOUR times its pad width tall — a signpost overhead height'),
     'Signpost ~2.0 m (door-height class). Assigned.')
spec('haybale', 'festival', [2, 2], 1.2, '2x2 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('haybale', 'A large round hay bale', [2, 2], 2.4,
                 'about 1.2x its pad width tall — thigh-to-chest high on an adult'),
     'Hay bale 1.2 m per table. Currently reads oversized in-scene (audit).')
spec('firepit', 'festival', [2, 2], 1.0, '2x2 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('firepit', 'A ring of stones around a campfire with rising flames',
                 [2, 2], 2.0, 'the flames rise about 1.0 m — 1x its pad width'),
     'Firepit flames ~1.0 m per table.')
spec('logpile', 'festival', [2, 2], 1.0, '2x2 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('logpile', 'A stacked pile of cut logs', [2, 2], 2.0,
                 'about 1.0 m tall — 1x its pad width'),
     'Log pile ~1.0 m. Assigned.')
spec('pumpkincart', 'festival', [2, 2], 1.6, '2x2 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('pumpkincart', 'A wooden handcart heaped with pumpkins', [2, 2], 3.2,
                 'about 1.6x its pad width tall to the cart handle'),
     'Handcart of pumpkins ~1.6 m. Assigned.')
spec('stall2', 'festival', [2, 2], 2.2, '2x2 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('stall2', 'A festival market stall with a striped awning on posts',
                 [2, 2], 4.4, 'about 2.2x its pad width tall at the awning ridge'),
     'Festival stall 2.2 m (stall class).')
spec('bigtree', 'festival', [3, 3], 6.0, '3x3 magenta pad', 'flat light grey', False,
     ['festival-template.png'],
     prop_prompt('bigtree', 'A huge ancient festival tree, sprawling canopy', [3, 3], 12.0,
                 'about FOUR times its pad width tall — a giant tree, canopy '
                 'overhanging, trunk base on the pad'),
     'Big tree ~6 m (upper tree range). Assigned.')

# =========================== BUILDINGS (3 facades) ==============================
# Buildings render at cellScale S=2. Prefer RESCALE over regen; see notes.
def bldg_prompt(name, desc, foot, door, ridgeM):
    return ('%s. Painted STANDING ON its %dx%d-cell magenta ground pad, a yellow '
            'door mark at pad cell %s. Eaves at ~3.2 m, roof RIDGE at %.1f m — '
            'the facade rises about %.0f cells (measure height in half-pad-widths: '
            'ridge ~= %.0f). Door is a 2.0 m opening. %s.'
            % (desc, foot[0], foot[1], door, ridgeM, ridgeM / M, ridgeM / M, ISO))

spec('bakery', 'bldg', [3, 3], 5.0, '3x3 magenta pad + yellow door', 'flat light grey', False,
     ['template-bakery4x3.png'],
     bldg_prompt('bakery', 'A cozy two-storey timber-framed village bakery, warm '
                 'lit windows, red awning', [3, 3], [1, 2], 5.0),
     'Eaves 3.2 m, ridge 5-6 m. Measured ridge ~5.0 m — PASS; no regen. door 2.0 m.')
spec('cottage', 'bldg', [3, 3], 5.0, '3x3 magenta pad + yellow door', 'flat light grey', False,
     ['template-cottage.png'],
     bldg_prompt('cottage', 'A rustic village cottage, steep shingled roof, '
                 'timber frame', [3, 3], [0, 2], 5.0),
     'Ridge 5-6 m. Measured in audit; rescale cellScale if off, do not regen.')
spec('guildhall', 'bldg', [4, 4], 8.0, '4x4 magenta pad + yellow door', 'flat light grey', False,
     ['template-guildhall.png'],
     bldg_prompt('guildhall', 'A grand two-storey stone-and-timber guildhall, '
                 'tall gabled roof', [4, 4], [1, 3], 8.0),
     'Two-storey ridge ~8 m. Measured in audit; rescale over regen.')

# =========================== INTERIOR (shell + 6 props) =========================
spec('int-room', 'interior', [8, 8], 2.7, 'green floor grid + yellow door mat',
     'painted room shell', False, ['template-bakint-a.png'],
     'The bakery interior shell: back and side walls of a warm timber bakery, an '
     '8x8-cell plank floor (4 m x 4 m), a doorway on the right wall. Walls stand '
     '2.7 m = about 5.4 half-cells; keep the 2:1 floor grid true. ' + ISO,
     'Interior walls 2.7 m per table. NOTE: shell currently renders at S=1.5, '
     'inflating walls to ~3.7 m; audit flags S=1.0 as the coherent choice.')
spec('i-counter', 'interior', [3, 2], 1.0, 'template placeholder on 3x2 pad',
     'flat light grey', True, ['template-intprops.png'],
     'A bakery front counter/display case, REPLACING the grey placeholder block '
     'standing on the pad exactly as it stands. Counter surface at 1.0 m = about '
     '2 half-cells tall. ' + ISO,
     'Counter 1.0 m per table. Painted ~1.6 m native — reads tall vs a 1.7 m cook.')
spec('i-oven', 'interior', [2, 2], 2.2, 'template placeholder on 2x2 pad',
     'flat light grey', True, ['template-intprops.png'],
     'A big brick baking oven with an iron door, REPLACING the placeholder. '
     'Oven ~2.2 m tall = about 4.4 half-cells. ' + ISO,
     'Oven 2.2 m per table.')
spec('i-preptable', 'interior', [2, 2], 0.9, 'template placeholder on 2x2 pad',
     'flat light grey', True, ['template-intprops.png'],
     'A wooden prep table dusted with flour, REPLACING the placeholder. Table '
     'top ~0.9 m = about 1.8 half-cells. ' + ISO,
     'Prep table 0.9 m per table.')
spec('i-shelf', 'interior', [1, 1], 1.8, 'template placeholder on 1x1 pad',
     'flat light grey', True, ['template-intprops.png'],
     'A tall bread shelf/rack stacked with loaves, REPLACING the placeholder. '
     'Shelf ~1.8 m = about 3.6 half-cells. ' + ISO,
     'Shelf 1.8 m per table.')
spec('i-stool', 'interior', [1, 1], 0.5, 'template placeholder on 1x1 pad',
     'flat light grey', True, ['template-intprops.png'],
     'A small round wooden stool, REPLACING the placeholder. Stool ~0.5 m = '
     'about 1 half-cell. ' + ISO,
     'Stool 0.5 m per table.')
spec('i-sacks', 'interior', [1, 1], 0.8, 'template placeholder on 1x1 pad',
     'flat light grey', True, ['template-intprops.png'],
     'A cluster of plump flour sacks, REPLACING the placeholder. Sacks ~0.8 m = '
     'about 1.6 half-cells. ' + ISO,
     'Flour sacks 0.8 m per table.')

# =========================== GROUND TEXTURES ===================================
for gid, gdesc in [('tex-grass', 'seamless autumn grass'),
                   ('tex-dirt', 'seamless packed dirt'),
                   ('tex-cobble', 'seamless cobblestone'),
                   ('f-plank', 'seamless wooden plank floor')]:
    A.append({
        'id': gid, 'catalog': 'ground', 'declaredFootprint': [2, 2],
        'targetHeightM': 0.0, 'targetHeightCells': 0.0,
        'recipe': {'mark': 'none (flat tileable texture, pre-squashed 2:1)',
                   'background': 'n/a', 'templatePlaceholder': False, 'refs': []},
        'prompt': ('A seamless, tileable top-down %s texture for isometric '
                   'ground, even lighting, no seams, no props, no text.' % gdesc),
        'generation': {'model': 'gemini-2.5-flash-image', 'date': '2026-07-27',
                       'outputSize': [512, 512]},
        'notes': 'Flat ground material, height gate N/A (targetHeightCells=0).',
    })

# =========================== CHARACTER =========================================
A.append({
    'id': 'vesper', 'catalog': 'character', 'declaredFootprint': [1, 1],
    'targetHeightM': 1.7, 'targetHeightCells': 3.4,
    'recipe': {'mark': 'none (transparent 4x4 sprite sheet on magenta)',
               'background': 'flat magenta #FF00FF',
               'templatePlaceholder': False,
               'refs': ['bust.png']},
    'prompt': 'See tools/characters/vesper.json (desc + sheetHint) driven '
              'through tools/gen-character.mjs T.sheet: slightly-chibi ~3-heads '
              'field sprite, 4x4 walk-cycle grid on flat magenta. Engine PINS '
              'the drawn height to 3.4 cells (1.7 m = 108.8 px), NOT the sheet.',
    'generation': {'model': 'gemini-2.5-flash-image', 'date': '2026-07-20',
                   'outputSize': [1024, 1024]},
    'notes': 'Person 1.7 m = 3.4 cells. Engine CHAR_H pins the RENDER height to '
             '3.4*32=108.8 px regardless of sheet proportions; pre-fix CHAR_H=130 '
             'rendered 4.06 cells = 2.03 m (the giant).',
})

OUT = {
    'sizeTable': {
        'cellMeters': 0.5, 'heightCellPx': 32,
        'note': 'cells = metres / 0.5. One cell of world HEIGHT renders at '
                'TW/2 = 32 engine px (2:1 dimetric). targetHeightCells is the '
                'TOTAL painted silhouette height. See tools/height_gate.py.',
        'canonical_m': {
            'person': 1.7, 'door': 2.0, 'lamppost': 3.0, 'stall_ridge': 2.2,
            'market_awning': 2.4, 'bench_seat': 0.45, 'barrel': 0.9, 'crate': 0.6,
            'well_incl_roof': 2.2, 'tree': '4.5-6', 'haybale': 1.2,
            'firepit_flames': 1.0, 'building_eaves': 3.2, 'building_ridge': '5-6',
            'two_story_ridge': 8.0, 'interior_walls': 2.7, 'counter': 1.0,
            'oven': 2.2, 'prep_table': 0.9, 'shelf': 1.8, 'stool': 0.5,
            'flour_sacks': 0.8,
        },
    },
    'assets': A,
}

# ---- TEMPLATE V2 regeneration stamp (2026-07-27) --------------------------
# Assets regenerated through the placeholder-driven, spec-sized Template V2
# (tools/props_template_v2.py + slice_v2.py): each region sized from
# targetHeightCells, a grey placeholder block standing on a machine-drawn pad,
# the model completing over it. Fixes the region-ceiling (tall props painted
# short) and strip-pad poisoning (1x2 base collapsed to square, cellPx
# inflated -> rendered tiny). Kept-old assets (v1 grey template still better):
# blocks9 crate/stall/well, festival haybale.
V2_STAMP = {
    'barrel': 'PASS 109%', 'lamppost': 'PASS 85% (was REROLL 0.38 — headline defect fixed)',
    'bench': 'PASS 89% (strip poisoning fixed: axisErr 0.67->~0.2, conf 0.0->0.70)',
    'planter': 'SCALE-NOTE 79% (footprint de-poisoned)',
    'firewood': 'SCALE-NOTE 76% (was REROLL)', 'tree': 'SCALE-NOTE 128% (was REROLL 0.48)',
    'sign': 'PASS 103% (was REROLL 0.31)', 'pumpkincart': 'PASS 109% (was REROLL 0.61)',
    'firepit': 'PASS 104%', 'brazier': 'SCALE-NOTE 80% (was REROLL 0.43)',
    'logpile': 'SCALE-NOTE 122%', 'applecrate': 'PASS 108% (was REROLL 0.45)',
    'stall2': 'SCALE-NOTE 72%', 'bigtree': 'SCALE-NOTE 84% (was REROLL 0.36)',
}
for a in A:
    if a['id'] in V2_STAMP:
        a['recipe']['templatePlaceholder'] = True
        a['recipe']['refs'] = ['template-v2.png']
        a['generation'] = {'model': 'gemini-2.5-flash-image', 'date': '2026-07-27',
                           'outputSize': [1024, 1024], 'template': 'v2',
                           'recipe': 'placeholder-over-pad'}
        a['notes'] = a['notes'] + ' | V2 regen: ' + V2_STAMP[a['id']]

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'public/assets/iso/specs.json')
with open(path, 'w') as f:
    json.dump(OUT, f, indent=1)
print('wrote', path, '-', len(A), 'asset specs')
