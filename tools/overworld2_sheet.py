#!/usr/bin/env python3
"""overworld2_sheet.py — docs/qa/overworld/COMPARISON2.png.

  python3 tools/overworld2_sheet.py

Round-1 style D is the FIRST row on purpose: the user picked D, so the sheet has to
show what each variant did to it, not just four new looks side by side.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA = os.path.join(ROOT, "docs/qa/overworld")
SHOTS = ["chase", "vista", "village", "boat"]
ROWS = [
    ("d", "D  (round 1)", "the branch point — one baked 2048 terrain map, matte props"),
    ("e", "E  PAINTED NATURALISM", "dusk sun + AO baked INTO the albedo; terrain ships UNLIT"),
    ("f", "F  PBR MINIATURE", "no bake: tiled PolyHaven diffuse+normal+rough, 4 terrain slots"),
    ("g", "G  RELIEF MAP", "altitude/slope bands to snow, baked AO, tiled detail normal on UV1"),
    ("h", "H  LUSH CANOPY", "alpha-MASK foliage cards: canopies, hedgerows, meadow scatter"),
]
CW, CH = 484, 277
LAB = 262
PAD = 8


def font(sz, bold=False):
    for p in ("/System/Library/Fonts/SFNSDisplay.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


W = LAB + len(SHOTS) * (CW + PAD) + PAD
H = 104 + len(ROWS) * (CH + PAD) + PAD
sheet = Image.new("RGB", (W, H), (18, 15, 12))
d = ImageDraw.Draw(sheet)
f_title, f_head, f_lab, f_sub = font(29), font(18), font(19), font(13)

d.text((PAD + 6, 16), "OVERWORLD — round 2: four naturalistic branches off style D",
       font=f_title, fill=(235, 205, 160))
d.text((PAD + 6, 46), "one shared blockout · identical dusk key · EEVEE, Standard view "
       "transform (the runtime does no tone mapping) · chase cam = the runtime rig "
       "(42° vfov, dist 16, pitch 0.62)", font=f_sub, fill=(150, 130, 108))

for ci, sh in enumerate(SHOTS):
    x = LAB + ci * (CW + PAD)
    d.text((x + 4, 82), sh.upper(), font=f_head, fill=(190, 160, 120))

for ri, (st, name, note) in enumerate(ROWS):
    y = 104 + ri * (CH + PAD)
    d.text((PAD + 6, y + 6), name, font=f_lab, fill=(232, 196, 140))
    words, line, lines = note.split(), "", []
    for w in words:
        t = (line + " " + w).strip()
        if d.textlength(t, font=f_sub) > LAB - 22:
            lines.append(line)
            line = w
        else:
            line = t
    lines.append(line)
    for li, ln in enumerate(lines):
        d.text((PAD + 6, y + 34 + li * 17), ln, font=f_sub, fill=(146, 126, 104))
    for ci, sh in enumerate(SHOTS):
        x = LAB + ci * (CW + PAD)
        p = os.path.join(QA, "style_%s_%s.png" % (st, sh))
        if os.path.exists(p):
            im = Image.open(p).convert("RGB").resize((CW, CH), Image.LANCZOS)
            sheet.paste(im, (x, y))
        else:
            d.rectangle([x, y, x + CW, y + CH], fill=(30, 26, 22))
            d.text((x + 16, y + CH // 2 - 10),
                   "round 1 had no %s shot" % sh, font=f_sub, fill=(110, 95, 80))

out = os.path.join(QA, "COMPARISON2.png")
sheet.save(out)
print("wrote %s  (%d x %d)" % (out, W, H))
