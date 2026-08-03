#!/usr/bin/env python3
"""THE HEAD BOX: the per-character subject metric the cut-in layout scales on.

WHY THIS EXISTS. dialogue.js used to give every cut-in the SAME ELEMENT HEIGHT and
let the plate's aspect decide its width. That normalises the IMAGE, and the player
does not read images — they read SUBJECTS. Vesper's plate is a waist-up figure whose
head is ~31% of the plate; Mochi's is a close-up whose head is ~57% of it. At equal
element height the cat's face lands 1.8x the size of the human's and its silhouette
spans half the dialogue box: the user's bug, exactly.

WHAT IT MEASURES. Three horizontal lines per base plate, as fractions of the PLATE's
own height:
    crown  the top of the head          (from the ALPHA silhouette, then eye-checked)
    eye    the eye line                 (marked by eye)
    chin   the bottom of the jaw/muzzle (marked by eye)
`crown` is automatic because the crop is tight to the silhouette and on every plate in
this cast the topmost solid row IS the top of the head — `--sheets` renders the alpha
crown as a line so that claim is checked and not assumed. The other two need a face,
and there is no face detector here worth trusting on painted art at this cast size, so
they are HAND-MARKED ONCE from the ruler sheets this script draws and committed into
public/assets/characters/cutins.json. Twenty-nine numbers, read off an image, written
down: cheaper and more honest than a heuristic nobody can check.

WHY THE BASE PLATE CARRIES THE SET. tools/cutin_edge.py already gates every mood to
within 0.03 head_frac of its own neutral, so a character's moods share a framing by
construction and one head box per character is enough. `--verify` re-draws the marks
over every plate INCLUDING the moods, which is where that assumption gets checked.

    python3 tools/cutin_headbox.py --sheets     # ruler sheets to mark from
    python3 tools/cutin_headbox.py --verify     # marks drawn back over every plate
    python3 tools/cutin_headbox.py --report     # the resulting screen sizes, per character
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, 'public', 'assets', 'characters')
MANIFEST = os.path.join(CH, 'cutins.json')


def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def plate(pid, mood=None):
    return os.path.join(CH, pid, 'cutin' + ('-' + mood if mood else '') + '.png')


def crown_of(path):
    """Topmost solid row of the alpha, as a fraction of plate height."""
    a = np.asarray(Image.open(path).convert('RGBA'))[:, :, 3]
    rows = (a > 24).sum(axis=1)
    ys = np.flatnonzero(rows >= 6)
    if not len(ys):
        return 0.0
    return round(float(ys[0]) / a.shape[0], 4)


def sheets(pids, out, per=5, cell_h=560, zoom=1.0, step=5):
    """Ruler sheets: each plate at a known height with gridlines every `step`% of
    the PLATE's height. `zoom` keeps only the top fraction of the plate and spends
    the whole cell on it — the head is what is being marked, and at five-to-a-sheet
    a full waist-up figure puts the eye line inside two pixels of ruler."""
    os.makedirs(out, exist_ok=True)
    for i in range(0, len(pids), per):
        grp = pids[i:i + per]
        cells = []
        for pid in grp:
            im = Image.open(plate(pid)).convert('RGBA')
            full = im.height
            if zoom < 1.0:
                im = im.crop((0, 0, im.width, max(1, int(full * zoom))))
            s = cell_h / im.height
            im = im.resize((max(1, int(im.width * s)), cell_h), Image.LANCZOS)
            bg = Image.new('RGBA', (im.width + 74, cell_h + 30), (26, 30, 38, 255))
            bg.alpha_composite(im, (74, 15))
            d = ImageDraw.Draw(bg)
            top = int(100 * zoom) + 1
            for p in range(0, top, step):
                y = 15 + int(cell_h * (p / 100.0) / zoom)
                if y > cell_h + 15:
                    break
                major = (p % (step * 2) == 0)
                d.line([(74 if not major else 56, y), (bg.width, y)],
                       fill=(255, 90, 90, 170 if major else 70), width=1)
                if major:
                    d.text((6, y - 7), '%d' % p, fill=(255, 200, 200, 255))
            d.text((6, cell_h + 16), pid, fill=(255, 255, 255, 255))
            cells.append(bg)
        w = sum(c.width for c in cells)
        sheet = Image.new('RGBA', (w, cell_h + 30), (18, 20, 26, 255))
        x = 0
        for c in cells:
            sheet.alpha_composite(c, (x, 0))
            x += c.width
        p = os.path.join(out, 'sheet-%02d.png' % (i // per))
        sheet.convert('RGB').save(p)
        print('SAVED', p, '  ', ', '.join(grp))


def verify(man, out, cell_h=420):
    """Draw crown/eye/chin back over EVERY plate, base and moods, in rows."""
    os.makedirs(out, exist_ok=True)
    for pid in sorted(man):
        e = man[pid]
        hb = e.get('head')
        if not hb:
            continue
        cells = []
        for mood in [None] + list(e.get('expr') or []):
            p = plate(pid, mood)
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert('RGBA')
            s = cell_h / im.height
            im = im.resize((max(1, int(im.width * s)), cell_h), Image.LANCZOS)
            bg = Image.new('RGBA', (im.width + 8, cell_h + 22), (26, 30, 38, 255))
            bg.alpha_composite(im, (4, 0))
            d = ImageDraw.Draw(bg)
            # the mood's OWN alpha crown, plus the base plate's marked lines
            for frac, col in ((crown_of(p), (90, 200, 255, 220)),
                              (hb['eye'], (120, 255, 140, 220)),
                              (hb['chin'], (255, 210, 90, 220))):
                y = int(cell_h * frac)
                d.line([(0, y), (bg.width, y)], fill=col, width=2)
            d.text((5, cell_h + 6), mood or 'base', fill=(230, 230, 230, 255))
            cells.append(bg)
        if not cells:
            continue
        w = sum(c.width for c in cells)
        sheet = Image.new('RGBA', (w, cell_h + 22), (18, 20, 26, 255))
        x = 0
        for c in cells:
            sheet.alpha_composite(c, (x, 0))
            x += c.width
        p = os.path.join(out, '%s.png' % pid)
        sheet.convert('RGB').save(p)
        print('SAVED', p)


def report(man, target=118.0):
    """What each character's head box does to its drawn size, head-normalised."""
    rows = []
    for pid in sorted(man):
        e = man[pid]
        hb = e.get('head')
        if not hb:
            rows.append((pid, None))
            continue
        head = hb['chin'] - hb['crown']
        h = target / head
        rows.append((pid, (head, h, h * e['w'] / e['h'])))
    print('%-16s %6s %6s %7s %7s' % ('character', 'head', 'aspect', 'draw h', 'draw w'))
    for pid, r in rows:
        if r is None:
            print('%-16s   -- no head box --' % pid)
            continue
        head, h, w = r
        print('%-16s %6.3f %6.2f %7.0f %7.0f' % (pid, head, w / h, h, w))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sheets', metavar='DIR', nargs='?', const='auto')
    ap.add_argument('--verify', metavar='DIR', nargs='?', const='auto')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--crowns', action='store_true')
    ap.add_argument('--target', type=float, default=118.0)
    ap.add_argument('--zoom', type=float, default=1.0)
    ap.add_argument('--step', type=int, default=5)
    ap.add_argument('--per', type=int, default=5)
    a = ap.parse_args()
    man = load_manifest()
    pids = sorted(man)
    if a.crowns:
        for pid in pids:
            print('%-16s crown %.4f' % (pid, crown_of(plate(pid))))
    if a.sheets:
        sheets(pids, a.sheets if a.sheets != 'auto' else os.path.join(ROOT, 'docs/qa/cutins/headbox'), per=a.per, zoom=a.zoom, step=a.step)
    if a.verify:
        verify(man, a.verify if a.verify != 'auto' else os.path.join(ROOT, 'docs/qa/cutins/headbox/verify'))
    if a.report:
        report(man, a.target)
    return 0


if __name__ == '__main__':
    sys.exit(main())
