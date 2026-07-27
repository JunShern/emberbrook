#!/usr/bin/env python3
"""BUILDING registration-mark templates — one building per sheet.

Conventions this round establishes (on top of the blocks9 round):
  * background is SATURATED CYAN (#00C8D8), not grey — the slicer keys the
    background by HUE globally, so enclosed pockets (sky seen through a
    window, gaps under a sign) can never survive; magenta stays exclusive
    to registration marks.
  * DOOR MARK: a YELLOW (#FFD400) diamond embedded in the magenta mark at
    the door's cell — the slicer detects it and records the door cell
    relative to the anchor (trigger-cell placement by construction).
  * NO GROUND in the art: the building ends at its foundation line,
    standing on the mark. The engine draws contact shadows.

Renders one 1024x1024 template per building: flat cyan sheet, one magenta
mark parallelogram (the declared footprint, 2:1 iso, CELL px per cell)
with per-cell seams, yellow diamond at the door cell.

Usage: python3 tools/bldg_template.py OUTDIR
       -> OUTDIR/template-<name>.png
"""
import sys, os
from PIL import Image, ImageDraw

S = 1024
CELL = 128            # px width of one 0.5 m cell diamond (2:1 -> 64 px tall)
CYAN = (0, 200, 216)  # saturated cyan background — hue-keyed by the slicer
MAG = (255, 0, 255)
SEAM = (225, 0, 225)  # darker magenta, still inside the slicer's magenta key
YELLOW = (255, 212, 0)
PAD_BOTTOM = 48       # px from sheet bottom to the mark's front corner

# name -> (footW, footH, (doorI, doorJ))   footW = cells along +i
# (down-right), footH = cells along +j (down-left); door cell 0-indexed
# from the back corner, all doors on the lower-left face (j = footH-1).
BLDGS = {
    # bakery re-declared 3x3 (2026-07-27): the model failed the 4x3 mark in
    # both attempts (squared it / shattered it into outline chunks) — same
    # elongation refusal the blocks9 round measured on 2x1 strips, now
    # confirmed at building scale. 'bakery4x3' keeps the failed declaration
    # measurable as evidence; square-ish is the proven working proportion.
    'bakery':    (3, 3, (1, 2)),
    'bakery4x3': (4, 3, (2, 2)),
    'cottage':   (3, 3, (0, 2)),
    'guildhall': (4, 4, (1, 3)),
}

def render(name, fw, fh, door, out):
    im = Image.new('RGB', (S, S), CYAN)
    d = ImageDraw.Draw(im)
    e1 = (CELL / 2.0, CELL / 4.0)     # +i edge
    e2 = (-CELL / 2.0, CELL / 4.0)    # +j edge
    # back corner T: mark bbox centred horizontally, front corner above pad
    w2 = (fw + fh) * CELL / 2.0
    Tx = S / 2.0 - (fw * e1[0] + fh * e2[0]) / 2.0 - (min(0, fw * e1[0]) + min(0, fh * e2[0])) \
         + 0  # simplify below
    # bbox: x from -fh*CELL/2 to fw*CELL/2 rel. T
    Tx = S / 2.0 - (fw * CELL / 2.0 - fh * CELL / 2.0) / 2.0
    Ty = S - PAD_BOTTOM - (fw + fh) * CELL / 4.0
    pt = lambda a, b: (Tx + a * e1[0] + b * e2[0], Ty + a * e1[1] + b * e2[1])
    d.polygon([pt(0, 0), pt(fw, 0), pt(fw, fh), pt(0, fh)], fill=MAG)
    for a in range(1, fw):
        d.line([pt(a, 0), pt(a, fh)], fill=SEAM, width=2)
    for b in range(1, fh):
        d.line([pt(0, b), pt(fw, b)], fill=SEAM, width=2)
    # yellow door diamond, inset so magenta stays around it (embedded)
    di, dj = door
    cx = (di + 0.5, dj + 0.5)
    k = 0.82
    q = [(cx[0] - k / 2, cx[1] - k / 2), (cx[0] + k / 2, cx[1] - k / 2),
         (cx[0] + k / 2, cx[1] + k / 2), (cx[0] - k / 2, cx[1] + k / 2)]
    d.polygon([pt(a, b) for a, b in q], fill=YELLOW)
    im.save(out)
    print('wrote', out, '  mark %dx%d cells, door cell (%d,%d)' % (fw, fh, di, dj))

def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, (fw, fh, door) in BLDGS.items():
        render(name, fw, fh, door, os.path.join(outdir, 'template-%s.png' % name))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'public/assets/iso/bldg')
