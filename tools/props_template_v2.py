#!/usr/bin/env python3
"""TEMPLATE V2 — spec-derived, placeholder-driven prop sheets.

Fixes the two director-confirmed defects of the equal-thirds 3x3 template:

  (1) REGION CEILING. The old sheet split into 9 equal squares (~341 px). A
      tall prop (lamppost = 6 height-cells, tree = 10, bigtree = 12) cannot
      be painted at true proportion inside a square — the model fattens and
      shortens it to fill the box. V2 sizes EACH region from the asset's
      targetHeightCells (+ headroom) and footprint, then shelf-packs the
      variable regions into the 1024 sheet. Tall props get tall regions.

  (2) STRIP-PAD POISONING. A 1x2 strip prop, drawn only as a flat magenta
      mark, was repainted by the model into a roughly SQUARE base — the
      surviving magenta measured cW!=cH (bench: 193 vs 96), axisErr 0.67,
      confidence 0, cellPx inflated to 144 and (since renderScale = TW/cellPx)
      the prop rendered at ~44%. V2 draws a GREY PLACEHOLDER BLOCK standing ON
      the machine-drawn pad, at the spec's footprint AND height. The model
      "completes over" the block (the proven interior recipe) instead of
      reconstructing the pad, so the elongated 1x2 footprint and the tall
      silhouette are both inherited from geometry, not prose.

Every region: cyan background, a magenta pad (1x1 diamond / true 2:1 1x2
strip / NxN, drawn programmatically), and a grey box standing on it whose
base insets ~18% (a magenta rim survives for the slicer to fit) and whose
height = targetHeightCells * cellPx / 2 (one height-cell = cellPx/2 px, the
engine's 2:1 unit).

Emits SHEET.png (fed to the model) and SHEET.regions.json (the region map the
v2 slicer consumes in place of the hardcoded 3x3 grid).

Usage: python3 tools/props_template_v2.py <blocks9|festival> OUT.png [MAP.json]
"""
import sys, os, json, math
from PIL import Image, ImageDraw

S = 1024
BG = (0, 200, 216)          # cyan surround (proven placeholder background)
LINE = (0, 168, 182)        # region border, a shade off the cyan
MAG = (255, 0, 255)
SEAM = (225, 0, 225)        # per-cell seam, still inside the slicer's magenta key
GREY_T, GREY_L, GREY_R = (178, 178, 178), (150, 150, 150), (128, 128, 128)

CELL_MIN, CELL_MAX = 64, 100     # painted cellPx floor (resolution) / ceiling
H_CAP = 470                      # region-height budget that sets tall-prop cellPx
MARGIN_TOP, PAD_BOTTOM = 26, 30  # px above box top / below pad front corner
SIDE_FRAC = 0.42                 # side margin per edge, in pad-widths (canopy room)
BASE_INSET = 0.74                # box base = footprint scaled about centre (rim shows)
GUTTER = 8                       # px between packed regions

# asset -> footprint order per catalog (must match the slicers' PROPS tables)
CATALOGS = {
    'blocks9': ['barrel', 'crate', 'lamppost', 'bench', 'planter', 'firewood',
                'stall', 'well', 'tree'],
    'festival': ['brazier', 'applecrate', 'sign', 'haybale', 'firepit',
                 'logpile', 'pumpkincart', 'stall2', 'bigtree'],
}


def load_specs():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'public/assets/iso/specs.json')
    with open(p) as f:
        return {a['id']: a for a in json.load(f).get('assets', [])}


def cell_for(th, fw, fh):
    """Largest painted cellPx (in [MIN,MAX]) whose region fits the height
    budget: region_h = cellPx*(th/2 + (fw+fh)/4) + margins <= H_CAP."""
    avail = H_CAP - MARGIN_TOP - PAD_BOTTOM
    denom = th / 2.0 + (fw + fh) / 4.0
    c = int(avail / denom) if denom > 0 else CELL_MAX
    return max(CELL_MIN, min(CELL_MAX, c))


def region_size(th, fw, fh, c):
    pad_w = (fw + fh) * c / 2.0
    pad_h = (fw + fh) * c / 4.0
    box_h = th * c / 2.0
    w = int(math.ceil(pad_w + 2 * SIDE_FRAC * c))
    h = int(math.ceil(box_h + pad_h + MARGIN_TOP + PAD_BOTTOM))
    return w, h


def shelf_pack(items):
    """items: list of dict with w,h. Shelf FFD (height-desc). Returns True and
    sets x0,y0 on each item if all fit in SxS, else False."""
    order = sorted(range(len(items)), key=lambda i: -items[i]['h'])
    x = y = shelf_h = 0
    for idx in order:
        it = items[idx]
        if x + it['w'] > S:                       # new shelf
            y += shelf_h + GUTTER
            x = shelf_h = 0
        if y + it['h'] > S:
            return False
        it['x0'], it['y0'] = x, y
        x += it['w'] + GUTTER
        shelf_h = max(shelf_h, it['h'])
    return True


def build(catalog, subset=None):
    specs = load_specs()
    names = subset if subset else CATALOGS[catalog]
    # size every region, shrinking global cellPx if the pack overflows
    shrink = 1.0
    for _ in range(12):
        items = []
        for name in names:
            sp = specs[name]
            fw, fh = sp['declaredFootprint']
            th = sp['targetHeightCells']
            c = max(CELL_MIN, int(cell_for(th, fw, fh) * shrink))
            w, h = region_size(th, fw, fh, c)
            items.append({'name': name, 'fw': fw, 'fh': fh, 'th': th,
                          'cellPx': c, 'w': w, 'h': h})
        if shelf_pack(items):
            break
        shrink *= 0.92
    else:
        raise SystemExit('could not pack %s even after shrink' % catalog)
    return items


def draw_region(d, it):
    c = it['cellPx']
    fw, fh, th = it['fw'], it['fh'], it['th']
    e1 = (c / 2.0, c / 4.0)      # +i edge (down-right)
    e2 = (-c / 2.0, c / 4.0)     # +j edge (down-left)
    # pad corners relative to back corner T
    corners = {'T': (0, 0), 'R': (fw * e1[0], fw * e1[1]),
               'B': (fw * e1[0] + fh * e2[0], fw * e1[1] + fh * e2[1]),
               'L': (fh * e2[0], fh * e2[1])}
    xs = [p[0] for p in corners.values()]
    ys = [p[1] for p in corners.values()]
    box_h = th * c / 2.0
    # place: centre pad in region width; front corner PAD_BOTTOM above region base
    Tx = it['x0'] + it['w'] / 2.0 - (min(xs) + max(xs)) / 2.0
    Ty = it['y0'] + it['h'] - PAD_BOTTOM - max(ys)
    P = lambda a, b: (Tx + a * e1[0] + b * e2[0], Ty + a * e1[1] + b * e2[1])

    # ---- magenta pad (programmatic footprint geometry) ----
    d.polygon([P(0, 0), P(fw, 0), P(fw, fh), P(0, fh)], fill=MAG)
    for a in range(1, fw):
        d.line([P(a, 0), P(a, fh)], fill=SEAM, width=2)
    for b in range(1, fh):
        d.line([P(0, b), P(fw, b)], fill=SEAM, width=2)

    # ---- grey placeholder box standing on the pad ----
    lo, hi = (1 - BASE_INSET) / 2.0, 1 - (1 - BASE_INSET) / 2.0
    base = {'T': P(fw * lo, fh * lo), 'R': P(fw * hi, fh * lo),
            'B': P(fw * hi, fh * hi), 'L': P(fw * lo, fh * hi)}
    up = lambda xy: (xy[0], xy[1] - box_h)
    d.polygon([up(base['T']), up(base['R']), up(base['B']), up(base['L'])],
              fill=GREY_T)                                   # top face
    d.polygon([up(base['L']), up(base['B']), base['B'], base['L']],
              fill=GREY_L)                                   # left face
    d.polygon([up(base['B']), up(base['R']), base['R'], base['B']],
              fill=GREY_R)                                   # right face

    anchor = ((corners['T'][0] + corners['B'][0]) / 2.0 + Tx,
              (corners['T'][1] + corners['B'][1]) / 2.0 + Ty)
    return {'padCornersSheet': {k: [round(Tx + v[0], 1), round(Ty + v[1], 1)]
                                for k, v in corners.items()},
            'anchorSheet': [round(anchor[0], 1), round(anchor[1], 1)],
            'boxTopY': round(Ty + min(ys) - box_h, 1)}


def main(catalog, out, mapout, subset=None):
    items = build(catalog, subset)
    im = Image.new('RGB', (S, S), BG)
    d = ImageDraw.Draw(im)
    regions = []
    for it in items:
        # region border
        d.rectangle([it['x0'], it['y0'], it['x0'] + it['w'], it['y0'] + it['h']],
                    outline=LINE, width=2)
        info = draw_region(d, it)
        regions.append({'name': it['name'], 'declared': [it['fw'], it['fh']],
                        'targetHeightCells': it['th'], 'cellPxDrawn': it['cellPx'],
                        'region': [it['x0'], it['y0'], it['w'], it['h']],
                        **info})
    im.save(out)
    with open(mapout, 'w') as f:
        json.dump({'catalog': catalog, 'sheet': os.path.basename(out),
                   'sheetSize': S, 'regions': regions}, f, indent=1)
    print('wrote', out, '+', mapout)
    for r in regions:
        x0, y0, w, h = r['region']
        print('  %-11s cell %3dpx  region %dx%d  th %.1f' %
              (r['name'], r['cellPxDrawn'], w, h, r['targetHeightCells']))


if __name__ == '__main__':
    cat = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else cat + '-template-v2.png'
    mapout = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(out)[0] + '.regions.json'
    subset = sys.argv[4].split(',') if len(sys.argv) > 4 else None
    main(cat, out, mapout, subset)
