"""make_sheet.py — composite the rendered tiles into CONTACT SHEETS.

The 1 m grid drawn over each tile is not decoration and not eyeballed: the tile renderer
wrote px_per_m and the camera centre with the render, so every rule is placed by
arithmetic.  Read a plant's height straight off the rules.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

S = os.path.dirname(os.path.abspath(__file__))
TILES = os.path.join(S, 'tiles')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(S, 'sheets')
os.makedirs(OUT, exist_ok=True)

F = '/System/Library/Fonts/Supplemental/Arial.ttf'
FB = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f_title = ImageFont.truetype(FB, 30)
f_head = ImageFont.truetype(FB, 25)
f_body = ImageFont.truetype(F, 21)
f_small = ImageFont.truetype(F, 18)
f_tiny = ImageFont.truetype(F, 16)

TILE_W, CAP_H = 1280, 140
INK = (18, 20, 24)
MUTE = (95, 100, 110)
ACCENT = (150, 60, 20)


def load(aid):
    p = os.path.join(TILES, aid + '.json')
    if not os.path.exists(p):
        return None
    m = json.load(open(p))
    m['img'] = Image.open(m['file']).convert('RGB')
    return m


def annotate(m):
    """draw the metre grid + per-object labels onto one tile, then a caption strip"""
    im = m['img'].copy()
    W, H = im.size
    d = ImageDraw.Draw(im, 'RGBA')
    ppm = m['px_per_m']
    # camera centre maps to image centre; ground (z=0) is cam_z metres below it
    y0 = H / 2 + m['cam_z'] * ppm                       # pixel row of z = 0
    x0 = W / 2 - m['cam_x'] * ppm                       # pixel col of x = 0
    top = max(m['height_m'] or 0, 1.8) * 1.15
    step = 1.0 if top > 3 else (0.5 if top > 1.2 else 0.1)
    z = 0.0
    while z <= top + step:
        y = y0 - z * ppm
        if 0 <= y < H:
            major = abs(z / (step * 5) - round(z / (step * 5))) < 1e-6
            d.line([(0, y), (W, y)], fill=(255, 255, 255, 90 if major else 45),
                   width=2 if major else 1)
            if z > 0:
                lab = f'{z:g} m'
                d.text((8, y - 20), lab, font=f_tiny,
                       fill=(255, 255, 255, 235 if major else 150))
        z += step
    d.line([(0, y0), (W, y0)], fill=(255, 255, 255, 190), width=2)
    # per-object footers: name + measured height, under each object's own span
    for p in m['placed']:
        cx = x0 + (p['x0'] + p['x1']) / 2 * ppm
        txt = f"{p['h']:.2f} m"
        w = d.textlength(txt, font=f_small)
        d.rectangle([cx - w / 2 - 7, H - 34, cx + w / 2 + 7, H - 6], fill=(0, 0, 0, 150))
        d.text((cx - w / 2, H - 31), txt, font=f_small, fill=(255, 255, 255))
    d.text((x0 - 0.9 * ppm - 42, y0 - 1.80 * ppm - 26), '1.80 m', font=f_tiny,
           fill=(255, 235, 200, 255))

    cap = Image.new('RGB', (W, CAP_H), (247, 245, 241))
    dc = ImageDraw.Draw(cap)
    dc.text((16, 10), m['id'], font=f_head, fill=INK)
    tw = dc.textlength(m['id'], font=f_head)
    dc.text((26 + tw, 16), m['category'], font=f_body, fill=ACCENT)
    l2 = (f"tallest {m['height_m']:.2f} m   canopy {m['canopy_width_m']:.2f} m   "
          f"{m['n_variants'] or len(m['placed'])} variants   src {m['disk_mb']:.0f} MB")
    dc.text((16, 46), l2, font=f_body, fill=INK)
    lc = m.get('leaf_card_m')
    l3 = (f"leaf card {lc:.2f} m  ->  {lc * 2.6:.2f} m at round-2's 2.6x"
          if lc else 'no instanced leaf cards (mesh leaves)')
    dc.text((16, 76), l3, font=f_small, fill=ACCENT if lc else MUTE)
    shown = ' | '.join(f"{p['name']} {p['tris']:,}t" for p in m['placed'])
    while dc.textlength(shown, font=f_tiny) > W - 36 and ' | ' in shown:
        shown = shown.rsplit(' | ', 1)[0] + ' | ...'
        if shown.endswith('| ... | ...'):
            shown = shown.replace('| ... | ...', '| ...')
    dc.text((16, 106), shown, font=f_tiny, fill=MUTE)

    out = Image.new('RGB', (W, im.size[1] + CAP_H), (247, 245, 241))
    out.paste(im, (0, 0))
    out.paste(cap, (0, im.size[1]))
    return out


def sheet(name, ids, title, subtitle, cols=2, scale=0.5):
    tiles = [annotate(m) for m in (load(i) for i in ids) if m]
    if not tiles:
        return None
    tw, th = tiles[0].size
    tw, th = int(tw * scale), int(th * scale)
    rows = (len(tiles) + cols - 1) // cols
    pad, head = 14, 132
    W = cols * tw + pad * (cols + 1)
    H = head + rows * th + pad * (rows + 1)
    sh = Image.new('RGB', (W, H), (236, 233, 227))
    d = ImageDraw.Draw(sh)
    d.text((pad + 4, 18), title, font=f_title, fill=INK)
    # wrap the subtitle to the sheet width instead of letting it run off the edge
    words, line, y = subtitle.split(), '', 56
    for w in words:
        t = (line + ' ' + w).strip()
        if d.textlength(t, font=f_small) > W - 2 * pad - 8:
            d.text((pad + 4, y), line, font=f_small, fill=MUTE)
            y += 24
            line = w
        else:
            line = t
    d.text((pad + 4, y), line, font=f_small, fill=MUTE)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        sh.paste(t.resize((tw, th), Image.LANCZOS),
                 (pad + c * (tw + pad), head + pad + r * (th + pad)))
    p = os.path.join(OUT, name + '.png')
    sh.save(p)
    print('SHEET', p, sh.size, round(os.path.getsize(p) / 1e6, 2), 'MB')
    return p


GROUPS = [
    ('sheet-1-trees', ['jacaranda_tree', 'pine_tree_01', 'fir_tree_01', 'fir_sapling_medium',
                       'island_tree_01', 'tree_small_02', 'island_tree_02', 'island_tree_03'],
     'EMBERBROOK DRESSING INTAKE — CANDIDATE SHEET 1 of 3: TREES',
     'PolyHaven CC0 photoscans, rendered RAW (no autumn grade) under the ratified round-2 key. '
     'Every plant at TRUE SCALE beside a 1.80 m figure; grid rules are 1 m, placed by arithmetic from the ortho camera.'),
    ('sheet-2-shrubs', ['searsia_burchellii', 'searsia_lucida', 'shrub_01', 'shrub_03',
                        'fern_02', 'nettle_plant'],
     'CANDIDATE SHEET 2 of 3: SHRUBS / BANK PLANTING',
     'Same contract. Note the grid step changes with the subject: 1 m on the tall sheets, 0.5 m or 0.1 m here.'),
    ('sheet-3-groundcover', ['grass_medium_02', 'grass_medium_01', 'grass_bermuda_01',
                             'dandelion_01', 'weed_plant_02'],
     'CANDIDATE SHEET 3 of 3: GROUNDCOVER',
     'These are the hair-instanced clump sources. Measured heights are per single clump, not per scattered patch.'),
]

if __name__ == '__main__':
    for name, ids, title, sub in GROUPS:
        sheet(name, ids, title, sub)
