#!/usr/bin/env python3
"""Throwaway iso compositor: places sliced Emberbrook blocks on a 2:1 grid.
Anchor model:
  cell (i,j) at elevation z -> screen anchor = the cell's TOP-PLANE diamond center:
    ax = ox + (i - j) * tileW/2
    ay = oy + (i + j) * tileH/2 - z * ZH
Kinds: 'top' anchored by top diamond center; 'base' blocks (house+deck) by
footprint; 'prop' by bottom-center standing on the plane; per-item dx/dy nudges.
Painter order: (zsort, i+j, layer)."""
import os, sys, json
from PIL import Image, ImageDraw, ImageEnhance

ROOT = '/Users/junshernchan/projects/multiplayer-rpg/public/assets/refs/iso-exploration'
BLK = os.path.join(ROOT, 'blocks')

RAW = {}
def load(name, tw, flip=False):
    key = (name, int(tw), flip)
    if key not in RAW:
        im = Image.open(os.path.join(BLK, name + '.png')).convert('RGBA')
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        s = tw / im.size[0]
        RAW[key] = im.resize((int(im.size[0]*s), int(im.size[1]*s)), Image.LANCZOS)
    return RAW[key]

# kind, target width at tileW=160 reference (scaled by tileW/160)
META = {
    'ground-plank':    ('top', 160), 'ground-stone': ('top', 160),
    'ground-grass':    ('top', 160), 'water':        ('top', 160),
    'ground-darkstone':('top', 160), 'deck-piles':   ('top', 160),
    'deck-rail1':      ('top', 160), 'deck-rail2':   ('top', 160),
    'house-red':       ('base', 300), 'house-teal':  ('base', 300),
    'house-red-stairs':('base', 300),
    'house-green':     ('prop', 210), 'market-stall':('prop', 150),
    'lantern-post':    ('prop', 46),  'barrel':      ('prop', 50),
    'crate':           ('prop', 60),  'chest':       ('prop', 66),
    'rope-coil':       ('prop', 66),  'crate-stack': ('prop', 62),
    'fish-rack':       ('prop', 128), 'stair':       ('prop', 106),
    'ramp':            ('prop', 130),
    'water-calm2':     ('top', 160), 'water-leaves': ('top', 160),
    'water-foam':      ('top', 160), 'dam-wall':     ('top', 160),
    'dam-fall':        ('top', 160), 'dam-fall-ladder': ('top', 160),
    'house-tall-teal': ('base', 300), 'house-tall-red': ('base', 300),
    'bunting':         ('base', 280),
}

def water_at(i, j, deck_cells, foam=True):
    """Pick a water variant: foam near deck edges, calm mix elsewhere."""
    if foam:
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (i + di, j + dj) in deck_cells:
                return 'water-foam'
    h = (i * 7 + j * 13) % 9
    return 'water' if h % 2 else 'water-calm2'

def render(placements, tileW, ox, oy, size, bg=(24, 20, 22)):
    tileH = tileW // 2
    ZH = tileW * 0.7765
    canvas = Image.new('RGB', size, bg)
    def key(p):
        name, i, j, z, kw = p
        return (kw.get('zsort', z), i + j, kw.get('layer', 0))
    for name, i, j, z, kw in sorted(placements, key=key):
        kind, tw = META[name]
        flip = name.startswith('water') and ((i * 3 + j) % 2 == 1)  # break repetition
        im = load(name, tw * tileW / 160.0, flip)
        w, h = im.size
        ax = ox + (i - j) * tileW / 2.0
        ay = oy + (i + j) * tileH / 2.0 - z * ZH
        if kind == 'top':
            px, py = ax - w / 2.0, ay - w / 4.0
        elif kind == 'base':
            t = 0.21 * w
            px, py = ax - w / 2.0, ay - h + t + w / 4.0
        else:  # prop
            px, py = ax - w / 2.0, ay - h + w / 8.0
        px += kw.get('dx', 0); py += kw.get('dy', 0)
        canvas.paste(im, (int(px), int(py)), im)
    return canvas

def P(name, i, j, z, **kw):
    return (name, i, j, z, kw)

def grade(im):
    """Cheap runtime-style lighting pass: warm amber wash from upper-left,
    cool dusk floor, gentle vignette. This is an engine-lighting stand-in,
    applied to the composed frame, not baked into blocks."""
    W, H = im.size
    ov = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(ov)
    for y in range(H):
        t = y / H
        # warm at top fading out, faint cool blue rising at bottom
        a_warm = int(46 * (1 - t) ** 1.5)
        d.line([(0, y), (W, y)], fill=(255, 176, 96, a_warm))
    im = Image.alpha_composite(im.convert('RGBA'), ov)
    ov2 = Image.new('RGBA', (W, H))
    d2 = ImageDraw.Draw(ov2)
    for y in range(H):
        t = y / H
        a_cool = int(34 * t ** 2)
        d2.line([(0, y), (W, y)], fill=(30, 40, 70, a_cool))
    im = Image.alpha_composite(im, ov2).convert('RGB')
    im = ImageEnhance.Color(im).enhance(1.06)
    im = ImageEnhance.Contrast(im).enhance(1.03)
    return im

# ---------------- Scene A: Dellhollow corner ----------------
def scene_a():
    pl = []
    lower = {(i, j) for j in range(3, 6) for i in range(0, 8)}
    upper = {(i, j) for j in range(0, 3) for i in range(1, 7)}
    deck_shadow = lower | upper                # cells with deck above water
    for j in range(-1, 9):                     # water everywhere below, z=0
        for i in range(-2, 10):
            if (i, j) in deck_shadow:
                pl.append(P('water-calm2', i, j, 0))
            else:
                pl.append(P(water_at(i, j, deck_shadow), i, j, 0))
    # dark stone dam spine along the right, two stories, waterfalls into the pool
    for j in range(-1, 7):
        base = 'dam-fall' if j in (5, 6) else 'dam-wall'
        pl.append(P(base, 8, j, 1))
        top = 'dam-fall-ladder' if j == 3 else 'dam-wall'
        pl.append(P(top, 8, j, 2))
        pl.append(P('ground-darkstone', 8, j, 3))   # walkable dam top
    for (i, j) in sorted(lower):               # lower platform z=1
        if j == 5:
            pl.append(P('deck-piles', i, j, 1))
        else:
            pl.append(P('ground-plank', i, j, 1))
    for (i, j) in sorted(upper):               # upper platform z=2
        if j == 2 or i == 6:
            pl.append(P('deck-piles', i, j, 2))
        else:
            pl.append(P('ground-plank', i, j, 2))
    # tall scaffold houses drawn after all z=2 blocks so their bases aren't clipped
    pl.append(P('house-tall-red', 2, 0, 2, zsort=2.05))
    pl.append(P('house-tall-teal', 5, 0, 2, zsort=2.06))
    pl.append(P('bunting', 3, 0, 2, zsort=2.04, dx=30))
    pl.append(P('stair', 4, 3, 1, zsort=2.1, dy=-6))
    pl.append(P('market-stall', 1, 4, 1, zsort=1.06))
    pl.append(P('crate-stack', 0, 3, 1, layer=1))
    pl.append(P('barrel', 2, 4, 1, layer=1, dx=-24))
    pl.append(P('crate', 0, 4, 1, layer=1))
    pl.append(P('lantern-post', 6, 3, 1, layer=1))
    pl.append(P('fish-rack', 6, 4, 1, zsort=1.07))
    pl.append(P('rope-coil', 3, 4, 1, layer=1))
    pl.append(P('barrel', 1, 1, 2, zsort=2.07))
    pl.append(P('lantern-post', 4, 0, 2, zsort=2.07))
    return grade(render(pl, 160, 640, 300, (1344, 768)))

# ---------------- Scene B: fishing jetty from walkfirst spec ----------------
def point_in_poly(x, y, pts):
    inside = False
    n = len(pts)
    for k in range(n):
        x1, y1 = pts[k]; x2, y2 = pts[(k + 1) % n]
        if (y1 > y) != (y2 > y):
            xt = x1 + (y - y1) / (y2 - y1) * (x2 - x1)
            if x < xt:
                inside = not inside
    return inside

def scene_b():
    spec = json.load(open('/Users/junshernchan/projects/multiplayer-rpg/public/assets/refs/walkfirst/jetty-spec.json'))
    CS = 64  # spec-space cell size -> 21x12 grid
    Z = {'shore boardwalk': 1, 'main jetty deck': 1, 'upper ramp': 1,
         'smokehouse platform': 2, 'east gangway': 2,
         'lower walkway': 1, 'fishing platform': 1}
    cols, rows = 1344 // CS, 768 // CS
    cells = {}
    offs = [(0.5, 0.5), (0.2, 0.5), (0.8, 0.5), (0.5, 0.2), (0.5, 0.8)]
    for poly in spec['walkable']:
        z = Z[poly['label']]
        for j in range(rows):
            for i in range(cols):
                if any(point_in_poly((i + ox) * CS, (j + oy) * CS, poly['points'])
                       for ox, oy in offs):
                    if cells.get((i, j), 0) < z:
                        cells[(i, j)] = z
    pl = []
    deck = set(cells)
    for j in range(rows):
        for i in range(cols):
            pl.append(P(water_at(i, j, deck, foam=False) if (i, j) not in deck
                        else 'water-calm2', i, j, 0))
    for (i, j), z in cells.items():
        below = cells.get((i, j + 1), 0)
        right = cells.get((i + 1, j), 0)
        front = below < z or right < z
        pl.append(P('deck-piles' if front else 'ground-plank', i, j, z))
    # stair from upper-ramp deck (z=1) up to the smokehouse platform (z=2)
    pl.append(P('stair', 13, 5, 1, zsort=2.1, dy=-4))
    pl.append(P('house-red', 14, 3, 2, zsort=2.05))    # smokehouse (958,268)
    pl.append(P('chest', 8, 8, 1, layer=1))            # chest on main jetty
    pl.append(P('fish-rack', 17, 10, 1, zsort=1.06))   # fish rack (1130,656)
    pl.append(P('lantern-post', 8, 7, 1, layer=1, dx=30))  # net crane spot
    pl.append(P('rope-coil', 3, 8, 1, layer=1))
    pl.append(P('barrel', 16, 4, 2, zsort=2.06))
    pl.append(P('crate', 4, 9, 1, layer=1))
    pl.append(P('barrel', 12, 9, 1, layer=1))
    big = render(pl, 104, 720, 200, (2000, 1150))
    big = grade(big.convert('RGB'))
    return big.resize((1344, int(1150 * 1344 / 2000)), Image.LANCZOS)

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if which in ('a', 'both'):
        scene_a().save(os.path.join(ROOT, 'composed-dellhollow-corner.png'))
        print('scene a done')
    if which in ('b', 'both'):
        scene_b().save(os.path.join(ROOT, 'composed-jetty.png'))
        print('scene b done')
