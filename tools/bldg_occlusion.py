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

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'public/assets/iso/bldg')
