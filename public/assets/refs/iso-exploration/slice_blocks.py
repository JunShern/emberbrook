#!/usr/bin/env python3
"""Slice iso block sheets into keyed PNGs.
Cell-based: known grid layout per sheet; within each cell, key the magenta
family (incl. darker magenta drop shadows), keep the largest connected
component, bbox-crop, save RGBA."""
import sys, os
from collections import deque
from PIL import Image

ROOT = '/Users/junshernchan/projects/multiplayer-rpg/public/assets/refs/iso-exploration'
OUT = os.path.join(ROOT, 'blocks')
os.makedirs(OUT, exist_ok=True)

SHEETS = [
    ('sheet-a-raw.png', 3, 3, ['ground-plank', 'ground-stone', 'ground-grass',
                               'water', 'deck-piles', 'ground-darkstone',
                               'house-red', 'house-red-stairs', 'house-teal']),
    ('sheet-b-raw.png', 3, 3, ['house-green', 'market-stall', 'lantern-post',
                               'barrel', 'crate', 'chest',
                               'rope-coil', 'crate-stack', 'fish-rack']),
    ('sheet-c-raw.png', 2, 2, ['stair', 'ramp', 'deck-rail2', 'deck-rail1']),
    ('sheet-d-raw.png', 3, 3, ['water-calm2', 'water-leaves', 'water-foam',
                               'dam-wall', 'dam-fall-ladder', 'dam-fall',
                               'house-tall-teal', 'house-tall-red', 'bunting']),
]
if len(sys.argv) > 1:
    SHEETS = [s for s in SHEETS if s[0].startswith(sys.argv[1])]

def is_bg(r, g, b):
    # magenta family: strong pink incl. shadow-darkened magenta
    return (r - g) > 45 and (b - g) > 18 and r > 70

def is_soft(r, g, b):
    return (r - g) > 30 and (b - g) > 10 and r > 60

for fname, cols, rows, names in SHEETS:
    im = Image.open(os.path.join(ROOT, fname)).convert('RGB')
    W, H = im.size
    cw, ch = W // cols, H // rows
    idx = 0
    for r in range(rows):
        for c in range(cols):
            name = names[idx]; idx += 1
            inset = 6
            cell = im.crop((c*cw+inset, r*ch+inset, (c+1)*cw-inset, (r+1)*ch-inset))
            w, h = cell.size
            px = cell.load()
            # build opacity mask
            mask = [[0]*w for _ in range(h)]
            for y in range(h):
                for x in range(w):
                    rr, gg, bb = px[x, y]
                    if is_bg(rr, gg, bb):
                        mask[y][x] = 0
                    elif is_soft(rr, gg, bb):
                        mask[y][x] = 1   # soft edge
                    else:
                        mask[y][x] = 2
            # largest CC of mask>0 (also drops white grid-line fragments if any)
            seen = [[False]*w for _ in range(h)]
            best = []
            for y0 in range(h):
                for x0 in range(w):
                    if mask[y0][x0] > 0 and not seen[y0][x0]:
                        comp = []
                        q = deque([(x0, y0)]); seen[y0][x0] = True
                        while q:
                            x, y = q.popleft(); comp.append((x, y))
                            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                                nx, ny = x+dx, y+dy
                                if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] > 0 and not seen[ny][nx]:
                                    seen[ny][nx] = True; q.append((nx, ny))
                        if len(comp) > len(best):
                            best = comp
                    else:
                        seen[y0][x0] = True
            keep = set(best)
            out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            opx = out.load()
            minx, miny, maxx, maxy = w, h, 0, 0
            for (x, y) in best:
                rr, gg, bb = px[x, y]
                a = 255 if mask[y][x] == 2 else 140
                if mask[y][x] == 1:
                    # desaturate magenta fringe toward neutral
                    rr = int(gg + (rr-gg)*0.3); bb = int(gg + (bb-gg)*0.3)
                opx[x, y] = (rr, gg, bb, a)
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
            if not best:
                print('EMPTY', fname, name); continue
            out = out.crop((minx, miny, maxx+1, maxy+1))
            out.save(os.path.join(OUT, name + '.png'))
            print(f'{name}: {out.size[0]}x{out.size[1]} ({len(best)} px)')
