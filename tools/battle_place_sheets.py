#!/usr/bin/env python3
"""battle_place_sheets.py — CONTACT SHEETS FOR THE SORT, and nothing else.

The placement study's method depends on the sort being made from PICTURES
BEFORE any metric is read (see tools/battle_place.mjs's header). So this script
deliberately prints NO measurement: it lays the captured sites out in labelled
grids so a human (or me) can look at twelve places at a time and put each one in
a pile. The numbers live in sites.json and are not opened until sort.json exists.

  python3 tools/battle_place_sheets.py                 # sheets from docs/qa/battle-placement/sites
  python3 tools/battle_place_sheets.py --cols 4 --rows 3
"""
import argparse, json, os, sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('--dir', default='docs/qa/battle-placement/sites')
ap.add_argument('--out', default='docs/qa/battle-placement/sheets')
ap.add_argument('--cols', type=int, default=4)
ap.add_argument('--rows', type=int, default=3)
ap.add_argument('--cw', type=int, default=460)
ap.add_argument('--suffix', default='')       # '' = the round shot, '-decide' = the dwell shot
a = ap.parse_args()

src = os.path.join(ROOT, a.dir)
out = os.path.join(ROOT, a.out)
os.makedirs(out, exist_ok=True)

names = sorted(f for f in os.listdir(src)
               if f.endswith('.png') and (f.endswith('-decide.png') if a.suffix else not f.endswith('-decide.png')))
if not names:
    sys.exit('no shots in ' + src)

per = a.cols * a.rows
ch = int(a.cw * 9 / 16)
LAB = 20
made = []
for s in range(0, len(names), per):
    chunk = names[s:s + per]
    W = a.cols * a.cw
    H = a.rows * (ch + LAB)
    sheet = Image.new('RGB', (W, H), (16, 16, 18))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(chunk):
        r, c = divmod(i, a.cols)
        im = Image.open(os.path.join(src, n)).convert('RGB').resize((a.cw, ch), Image.LANCZOS)
        x, y = c * a.cw, r * (ch + LAB)
        sheet.paste(im, (x, y + LAB))
        d.rectangle([x, y, x + a.cw - 1, y + LAB - 1], fill=(30, 30, 34))
        d.text((x + 6, y + 5), n.replace('.png', ''), fill=(235, 235, 235))
        d.rectangle([x, y + LAB, x + a.cw - 1, y + LAB + ch - 1], outline=(60, 60, 66))
    f = os.path.join(out, 'sheet%02d%s.png' % (s // per, a.suffix))
    sheet.save(f)
    made.append(f)
    print(f, len(chunk))
print('%d sheets, %d shots' % (len(made), len(names)))
