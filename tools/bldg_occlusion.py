#!/usr/bin/env python3
"""Occlusion test: Vesper vs a big-footprint building under the REAL sort.

Faithful replica of public/js/iso/engine.js:
  TW=64, TH=32                       sx=(x-y)*32, sy=(x+y)*16
  sortKey(prop) = i + j + (foot[0]+foot[1])/2
  char key      = x + y; char drawn before the first prop whose sortKey
                  exceeds it (strictly greater), else after all props
  char billboard: alpha-cropped frame scaled to CHAR_H=130, bottom-centre
                  at (sx, sy + 4)   [drawChar: py - CHAR_H + 4]
  building drawn like a 'free'-kind block with a measured anchor:
                  anchor pixel at the footprint centre, scale s = TW/cellPx
                  (one painted cell = one engine cell, by construction)

Per building, three composites: char clearly in FRONT of the facade,
char BESIDE THE DOOR (on the cell just outside the mark, in the door's
column), char BEHIND the building. Each is saved as a labeled PNG plus a
programmatic verdict (draw order + how much of the char the building
actually covers) in occl.json.

Usage: python3 tools/bldg_occlusion.py [OUTDIR]
"""
import os, sys, json
from PIL import Image, ImageDraw

TW, TH = 64, 32
CHAR_H = 130
ZOOM = 2

def sx(x, y): return (x - y) * (TW / 2)
def sy(x, y): return (x + y) * (TH / 2)

def load_vesper(root):
    sheet = Image.open(os.path.join(
        root, 'public/assets/characters/vesper/sheet.png')).convert('RGBA')
    CELL = 256
    f = sheet.crop((0, 0, CELL, CELL))          # 'down' frame 0, like the proto
    f = f.crop(f.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox())
    s = CHAR_H / f.height
    return f.resize((max(1, round(f.width * s)), CHAR_H), Image.LANCZOS)

def composite(name, m, sprite, char, cx, cy, label, out_png):
    fw, fh = m['declared']
    s = TW / m['cellPx']
    bw, bh = round(sprite.width * s), round(sprite.height * s)
    b = sprite.resize((bw, bh), Image.LANCZOS)
    ax, ay = m['anchorSprite'][0] * s, m['anchorSprite'][1] * s
    # building anchor at footprint centre (building placed at i=j=0)
    bx, by = sx(fw / 2, fh / 2) - ax, sy(fw / 2, fh / 2) - ay

    # canvas extents over building + char + a ring of ground
    px, py = sx(cx, cy), sy(cx, cy)
    x0 = min(bx, px - char.width / 2, sx(0, fh + 2)) - 24
    x1 = max(bx + bw, px + char.width / 2, sx(fw + 2, 0)) + 24
    y0 = min(by, py - CHAR_H) - 24
    y1 = max(by + bh, py + 8, sy(fw + 2, fh + 2)) + 24
    W, H = round((x1 - x0) * ZOOM), round((y1 - y0) * ZOOM) + 22 * ZOOM
    im = Image.new('RGBA', (W, H), (23, 18, 14, 255))
    d = ImageDraw.Draw(im)
    tr = lambda x, y: ((x - x0) * ZOOM, (y - y0) * ZOOM + 22 * ZOOM)

    # faint grid + red footprint + yellow door cell (context, then engine draw)
    def cell_poly(a, b_, a2, b2):
        return [tr(sx(a, b_), sy(a, b_)), tr(sx(a2, b_), sy(a2, b_)),
                tr(sx(a2, b2), sy(a2, b2)), tr(sx(a, b2), sy(a, b2))]
    for a in range(-2, fw + 3):
        for b_ in range(-2, fh + 3):
            d.polygon(cell_poly(a, b_, a + 1, b_ + 1), outline=(240, 230, 210, 36))
    d.polygon(cell_poly(0, 0, fw, fh), outline=(255, 80, 64, 220), width=2)
    dc = (m.get('door') or {}).get('cell')
    if dc:
        d.polygon(cell_poly(dc[0], dc[1], dc[0] + 1, dc[1] + 1),
                  outline=(255, 212, 0, 235), width=2)

    # contact shadow (engine's ground-decal pass, simplified ellipse)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    ccx, ccy = tr(sx(fw / 2, fh / 2), sy(fw / 2, fh / 2))
    rx = (fw + fh) * (TW / 4) * 0.78 * ZOOM
    sd.ellipse([ccx - rx, ccy - rx / 2, ccx + rx, ccy + rx / 2],
               fill=(22, 11, 18, 60))
    im.alpha_composite(sh)

    # THE SORT (engine.js render(), verbatim logic)
    sort_key = 0 + 0 + (fw + fh) / 2.0
    ck = cx + cy
    char_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cpx, cpy = tr(px, py)
    char_layer.alpha_composite(
        char, (round(cpx - char.width * ZOOM / 2 / 1), 0))  # placed below
    # (paste with zoom: rescale char by ZOOM)
    char_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    cz = char.resize((char.width * ZOOM, CHAR_H * ZOOM), Image.LANCZOS)
    char_layer.alpha_composite(
        cz, (round(cpx - cz.width / 2), round(cpy - (CHAR_H - 4) * ZOOM)))
    bldg_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bz = b.resize((bw * ZOOM, bh * ZOOM), Image.LANCZOS)
    bldg_layer.alpha_composite(bz, (round(tr(bx, by)[0]), round(tr(bx, by)[1])))

    char_first = ck < sort_key
    order = [char_layer, bldg_layer] if char_first else [bldg_layer, char_layer]
    for layer in order:
        im.alpha_composite(layer)

    # verdict: how much of the char does the building silhouette cover,
    # and does the draw order hide it
    ca = char_layer.getchannel('A').load()
    ba = bldg_layer.getchannel('A').load()
    tot = ovl = 0
    for yy in range(0, H, 2):
        for xx in range(0, W, 2):
            if ca[xx, yy] > 128:
                tot += 1
                if ba[xx, yy] > 128:
                    ovl += 1
    frac = ovl / tot if tot else 0.0

    d = ImageDraw.Draw(im)
    txt = '%s - %s   char(%.1f,%.1f) key %.1f %s bldg key %.1f -> char %s' % (
        name, label, cx, cy, ck, '<' if char_first else '>=', sort_key,
        'BEHIND' if char_first else 'IN FRONT')
    d.rectangle([0, 0, W, 20 * ZOOM], fill=(12, 9, 7, 255))
    d.text((8, 6), txt, fill=(242, 228, 196, 255))
    im.convert('RGB').save(out_png)
    return {'charPos': [cx, cy], 'charKey': round(ck, 2),
            'bldgKey': round(sort_key, 2),
            'charDrawn': 'before (behind bldg)' if char_first else 'after (in front)',
            'charCoveredFrac': round(frac, 3), 'img': os.path.basename(out_png)}

def main(outdir):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(outdir, 'bldg-metrics.json')) as f:
        M = json.load(f)
    char = load_vesper(root)
    occl = {}
    for name in ['bakery', 'cottage', 'guildhall']:
        m = M[name]
        fw, fh = m['declared']
        sprite = Image.open(os.path.join(outdir, m['sprite'])).convert('RGBA')
        dc = (m.get('door') or {}).get('cell') or [fw // 2, fh - 1]
        cases = [
            ('front',  fw * 0.45, fh + 0.7, 'in front of facade'),
            ('door',   dc[0] + 0.5, fh + 0.5, 'beside the door'),
            ('behind', fw * 0.5, -0.7, 'behind the building'),
        ]
        occl[name] = {}
        for key, cx, cy, label in cases:
            out_png = os.path.join(outdir, 'occl-%s-%s.png' % (name, key))
            occl[name][key] = composite(name, m, sprite, char, cx, cy, label, out_png)
            r = occl[name][key]
            print('%-9s %-6s char key %-5s bldg key %-4s drawn %-22s covered %.0f%%'
                  % (name, key, r['charKey'], r['bldgKey'], r['charDrawn'],
                     r['charCoveredFrac'] * 100))
    with open(os.path.join(outdir, 'occl.json'), 'w') as f:
        json.dump(occl, f, indent=1)

# ============================================================
# PART TWO — CELLSCALE round: composites at ENGINE scale.
# Each building rendered with its measured cellScale (S=2): one
# painted cell spans S engine cells on screen (renderScale =
# S*TW/cellPx), engine footprint = painted x S, same anchor
# pixel, sortKey fed the ENGINE footprint. Vesper unchanged at
# CHAR_H=130 (~2.5 engine cells). Produces per building a
# scale-sanity shot at the doorstep, the three-position
# occlusion trio, and one combined ensemble with native-1x
# blocks9 props. Verdicts in occl2.json.
# ============================================================

def scene_render(objects, char, cx, cy, grid, title, out_png, zoom=ZOOM):
    """Generic engine-grid compositor with the REAL sort.

    objects: list of dicts {img, scale, anchor(ax,ay sprite px), i, j,
             foot(engine cells), door(list of engine cells)|None,
             doorstep(list)|None, occl(bool: count coverage of char)}
    char at (cx, cy) engine cells. grid = (i0, j0, i1, j1) cell range drawn.
    Returns {charKey, layers:[(name,key)...], charDrawn, charCoveredFrac}.
    """
    placed = []
    for o in objects:
        s = o['scale']
        bw, bh = round(o['img'].width * s), round(o['img'].height * s)
        fw, fh = o['foot']
        ax, ay = o['anchor'][0] * s, o['anchor'][1] * s
        bx = sx(o['i'] + fw / 2, o['j'] + fh / 2) - ax
        by = sy(o['i'] + fw / 2, o['j'] + fh / 2) - ay
        key = o['i'] + o['j'] + (fw + fh) / 2.0
        placed.append(dict(o, bw=bw, bh=bh, bx=bx, by=by, key=key))
    placed.sort(key=lambda p: p['key'])

    px, py = sx(cx, cy), sy(cx, cy)
    i0, j0, i1, j1 = grid
    gx = [sx(i0, j0), sx(i1, j0), sx(i1, j1), sx(i0, j1)]
    gy = [sy(i0, j0), sy(i1, j0), sy(i1, j1), sy(i0, j1)]
    x0 = min([p['bx'] for p in placed] + [px - char.width / 2] + gx) - 24
    x1 = max([p['bx'] + p['bw'] for p in placed] + [px + char.width / 2] + gx) + 24
    y0 = min([p['by'] for p in placed] + [py - CHAR_H] + gy) - 24
    y1 = max([p['by'] + p['bh'] for p in placed] + [py + 8] + gy) + 24
    W, H = round((x1 - x0) * zoom), round((y1 - y0) * zoom) + 22 * zoom
    im = Image.new('RGBA', (W, H), (23, 18, 14, 255))
    d = ImageDraw.Draw(im)
    tr = lambda x, y: ((x - x0) * zoom, (y - y0) * zoom + 22 * zoom)

    def cell_poly(a, b_, a2, b2):
        return [tr(sx(a, b_), sy(a, b_)), tr(sx(a2, b_), sy(a2, b_)),
                tr(sx(a2, b2), sy(a2, b2)), tr(sx(a, b2), sy(a, b2))]
    for a in range(i0, i1):
        for b_ in range(j0, j1):
            d.polygon(cell_poly(a, b_, a + 1, b_ + 1), outline=(240, 230, 210, 36))
    for p in placed:
        fw, fh = p['foot']
        d.polygon(cell_poly(p['i'], p['j'], p['i'] + fw, p['j'] + fh),
                  outline=(255, 80, 64, 220), width=2)
        for c in p.get('door') or []:
            d.polygon(cell_poly(c[0] + p['i'], c[1] + p['j'],
                                c[0] + p['i'] + 1, c[1] + p['j'] + 1),
                      outline=(255, 212, 0, 235), width=2)
        for c in p.get('doorstep') or []:
            d.polygon(cell_poly(c[0] + p['i'], c[1] + p['j'],
                                c[0] + p['i'] + 1, c[1] + p['j'] + 1),
                      outline=(80, 220, 120, 235), width=2)

    # contact shadows (engine's ground-decal pass, simplified ellipses)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for p in placed:
        fw, fh = p['foot']
        ccx, ccy = tr(sx(p['i'] + fw / 2, p['j'] + fh / 2),
                      sy(p['i'] + fw / 2, p['j'] + fh / 2))
        rx = (fw + fh) * (TW / 4) * 0.78 * zoom
        sd.ellipse([ccx - rx, ccy - rx / 2, ccx + rx, ccy + rx / 2],
                   fill=(22, 11, 18, 60))
    im.alpha_composite(sh)

    # THE SORT (engine.js render(): char drawn before the first prop whose
    # sortKey strictly exceeds the char key, else after all props)
    ck = cx + cy
    cz = char.resize((char.width * zoom, CHAR_H * zoom), Image.LANCZOS)
    cpx, cpy = tr(px, py)
    char_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    char_layer.alpha_composite(
        cz, (round(cpx - cz.width / 2), round(cpy - (CHAR_H - 4) * zoom)))
    after_char = Image.new('RGBA', (W, H), (0, 0, 0, 0))  # occluders of the char
    drawn = False
    for p in placed:
        if not drawn and ck < p['key']:
            im.alpha_composite(char_layer)
            drawn = True
        bz = p['img'].resize((p['bw'] * zoom, p['bh'] * zoom), Image.LANCZOS)
        pos = (round(tr(p['bx'], p['by'])[0]), round(tr(p['bx'], p['by'])[1]))
        im.alpha_composite(bz, pos)
        if drawn and p.get('occl'):
            after_char.alpha_composite(bz, pos)
    if not drawn:
        im.alpha_composite(char_layer)

    # coverage: how much of the char the layers drawn AFTER it cover
    ca = char_layer.getchannel('A').load()
    oa = after_char.getchannel('A').load()
    tot = ovl = 0
    for yy in range(0, H, 2):
        for xx in range(0, W, 2):
            if ca[xx, yy] > 128:
                tot += 1
                if oa[xx, yy] > 128:
                    ovl += 1
    frac = ovl / tot if tot else 0.0

    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 20 * zoom], fill=(12, 9, 7, 255))
    d.text((8, 6), title, fill=(242, 228, 196, 255))
    im.convert('RGB').save(out_png)
    behind_any = any(ck < p['key'] for p in placed if p.get('occl'))
    return {'charPos': [round(cx, 2), round(cy, 2)], 'charKey': round(ck, 2),
            'charDrawn': 'before (behind)' if behind_any else 'after (in front)',
            'charCoveredFrac': round(frac, 3), 'img': os.path.basename(out_png)}

def bldg_object(m, sprite, i, j, occl=True):
    cs = m['cellScale']
    return {'img': sprite, 'scale': cs['renderScale'],
            'anchor': m['anchorSprite'], 'i': i, 'j': j,
            'foot': cs['engineFoot'], 'door': cs.get('engineDoorCells'),
            'doorstep': cs.get('engineDoorstep'), 'occl': occl}

def main_cellscale(outdir):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(outdir, 'bldg-metrics.json')) as f:
        M = json.load(f)
    char = load_vesper(root)
    out = {}

    for name in ['bakery', 'cottage', 'guildhall']:
        m = M[name]
        cs = m['cellScale']
        efw, efh = cs['engineFoot']
        sprite = Image.open(os.path.join(outdir, m['sprite'])).convert('RGBA')
        step = cs['engineDoorstep']
        dsx = sum(c[0] for c in step) / len(step) + 0.5
        dsy = step[0][1] + 0.5
        obj = [bldg_object(m, sprite, 0, 0)]
        grid = (-2, -2, efw + 2, efh + 2)
        key = efw / 2 + efh / 2

        # (a) scale sanity: Vesper ON the engine doorstep
        r = scene_render(obj, char, dsx, dsy, grid,
                         '%s - SCALE SANITY: Vesper on the %d-cell engine doorstep '
                         '(cellScale x%d, renderScale %.3f)' % (
                             name, len(step), cs['S'], cs['renderScale']),
                         os.path.join(outdir, 'scale-%s.png' % name))
        out[name] = {'scale': r}

        # (b) occlusion trio at engine scale
        cases = [('front', efw * 0.45, efh + 0.7, 'in front of facade'),
                 ('door', dsx, dsy, 'at the doorstep'),
                 ('behind', efw * 0.5, -0.7, 'behind the building')]
        for k, cx, cy, label in cases:
            r = scene_render(obj, char, cx, cy, grid,
                             '%s - %s   char(%.1f,%.1f) key %.1f vs bldg key %.1f' % (
                                 name, label, cx, cy, cx + cy, key),
                             os.path.join(outdir, 'occl2-%s-%s.png' % (name, k)))
            out[name][k] = r
            print('%-9s %-6s char key %-5s bldg key %-4s drawn %-16s covered %.0f%%'
                  % (name, k, r['charKey'], key, r['charDrawn'],
                     r['charCoveredFrac'] * 100))

    # (c) ensemble: three buildings + native-1x blocks9 props + Vesper
    with open(os.path.join(root, 'public/assets/iso/blocks9/'
                                 'blocks9-metrics.json')) as f:
        B9 = json.load(f)
    def prop_object(pname, i, j):
        p = B9[pname]
        img = Image.open(os.path.join(root, 'public/assets/iso/blocks9/',
                                      p['sprite'])).convert('RGBA')
        return {'img': img, 'scale': TW / p['cellPx'], 'anchor': p['anchorSprite'],
                'i': i, 'j': j, 'foot': p['declared'], 'occl': True}
    bak, cot, gld = [Image.open(os.path.join(outdir, M[n]['sprite'])).convert('RGBA')
                     for n in ['bakery', 'cottage', 'guildhall']]
    objs = [
        bldg_object(M['cottage'], cot, 0, 0),
        bldg_object(M['guildhall'], gld, 14, 0),
        bldg_object(M['bakery'], bak, 6, 10),
        prop_object('tree', 10, 2),
        prop_object('bench', 15, 10),
        prop_object('barrel', 13, 12),
    ]
    # Vesper on the bakery doorstep (bakery placed at 6,10)
    st = M['bakery']['cellScale']['engineDoorstep']
    vx = 6 + sum(c[0] for c in st) / len(st) + 0.5
    vy = 10 + st[0][1] + 0.5
    r = scene_render(objs, char, vx, vy, (-2, -2, 24, 18),
                     'ENSEMBLE - 3 buildings at cellScale x2 + blocks9 props at '
                     'native 1x + Vesper (real sort, one grid)',
                     os.path.join(outdir, 'ensemble.png'))
    out['ensemble'] = r
    print('ensemble  char key %s drawn %s covered %.0f%%'
          % (r['charKey'], r['charDrawn'], r['charCoveredFrac'] * 100))

    with open(os.path.join(outdir, 'occl2.json'), 'w') as f:
        json.dump(out, f, indent=1)

if __name__ == '__main__':
    _out = sys.argv[1] if len(sys.argv) > 1 else 'public/assets/iso/bldg'
    main(_out)
    main_cellscale(_out)
