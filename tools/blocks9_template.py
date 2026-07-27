#!/usr/bin/env python3
"""blocks9 REGISTRATION-MARK template.

Renders the layout reference fed to the image model: a 1024x1024 light-grey
sheet, 3x3 regions, one flat pure-magenta registration mark per region.
The mark IS the declared footprint (2:1 iso, cell = CELL px wide = 0.5 m).
The generated painting must keep these marks; the slicer then measures the
marks in the OUTPUT image, so the marks are the measurement by construction.

Usage: python3 tools/blocks9_template.py OUT.png
"""
import sys
from PIL import Image, ImageDraw

S = 1024              # sheet size
R = 3                 # 3x3 regions
CELL = 96             # px width of one 0.5 m cell diamond (2:1 -> 48 px tall)
BG = (216, 216, 216)  # flat light grey
LINE = (198, 198, 198)
MAG = (255, 0, 255)
PAD_BOTTOM = 34       # px from region bottom to mark's front corner

# name -> (col, row, footW, footH)   footW = cells along +i (down-right),
#                                    footH = cells along +j (down-left)
PROPS = {
    'barrel':   (0, 0, 1, 1),
    'crate':    (1, 0, 1, 1),
    'lamppost': (2, 0, 1, 1),
    'bench':    (0, 1, 2, 1),
    'planter':  (1, 1, 2, 1),
    'firewood': (2, 1, 2, 1),
    'stall':    (0, 2, 2, 2),
    'well':     (1, 2, 2, 2),
    'tree':     (2, 2, 2, 2),
}

def mark_corners(fw, fh, cell=CELL):
    """Parallelogram corners rel. to back corner T: T, R, B(front), L."""
    T = (0.0, 0.0)
    Rc = (fw * cell / 2.0, fw * cell / 4.0)
    B = ((fw - fh) * cell / 2.0, (fw + fh) * cell / 4.0)
    L = (-fh * cell / 2.0, fh * cell / 4.0)
    return [T, Rc, B, L]

def region_rect(col, row):
    x0 = round(col * S / R); x1 = round((col + 1) * S / R)
    y0 = round(row * S / R); y1 = round((row + 1) * S / R)
    return x0, y0, x1, y1

def placed_corners(name):
    """Mark corners in sheet coordinates for a prop."""
    col, row, fw, fh = PROPS[name]
    x0, y0, x1, y1 = region_rect(col, row)
    q = mark_corners(fw, fh)
    xs = [p[0] for p in q]; ys = [p[1] for p in q]
    cx = (x0 + x1) / 2.0 - (min(xs) + max(xs)) / 2.0   # centre bbox horizontally
    cy = y1 - PAD_BOTTOM - max(ys)                     # front corner above bottom pad
    return [(cx + px, cy + py) for px, py in q]

def main(out):
    im = Image.new('RGB', (S, S), BG)
    d = ImageDraw.Draw(im)
    for k in range(1, R):
        t = round(k * S / R)
        d.line([(t, 0), (t, S)], fill=LINE, width=2)
        d.line([(0, t), (S, t)], fill=LINE, width=2)
    SEAM = (225, 0, 225)   # darker magenta, still inside the slicer's key
    for name in PROPS:
        col, row, fw, fh = PROPS[name]
        T = placed_corners(name)[0]
        e1 = (CELL / 2.0, CELL / 4.0)     # +i edge
        e2 = (-CELL / 2.0, CELL / 4.0)    # +j edge
        pt = lambda a, b: (T[0] + a * e1[0] + b * e2[0], T[1] + a * e1[1] + b * e2[1])
        d.polygon(placed_corners(name), fill=MAG)
        # per-cell seams: make multi-cell structure legible to the model
        for a in range(1, fw):
            d.line([pt(a, 0), pt(a, fh)], fill=SEAM, width=2)
        for b in range(1, fh):
            d.line([pt(0, b), pt(fw, b)], fill=SEAM, width=2)
    im.save(out)
    print('wrote', out)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'blocks9-template.png')
