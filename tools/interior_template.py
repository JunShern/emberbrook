#!/usr/bin/env python3
"""INTERIOR templates — floor registration, the inversion of prop registration.

Props/buildings STAND ON a magenta mark; a room shell WRAPS AROUND one:
the FLOOR is the mark. Two shell variants are rendered to test which the
image model executes more reliably:

  A (template-bakint-a.png)  the whole walkable floor is one flat MAGENTA
     plane reaching exactly to the wall bases. The floor mark IS the room's
     registration (grid origin, cellPx per axis -> rectification, wall line
     = floor polygon edge). The real floor is engine-rendered (f-plank
     ground supertile), so the keyed shell ships WALLS ONLY — which also
     makes the near-wall band cut trivial (any art inside the floor polygon
     is the near wall, since the floor keyed to transparent).
  B (template-bakint-b.png)  the floor is painted art; only a magenta
     BORDER band runs along the wall bases / room perimeter. Same u1/u2
     extremes -> same fit, but the shell keeps its painted floor and the
     near-wall cut loses the transparent-floor separation.

Both: 8x8 painted cells, CELL px/cell (2:1), cyan surround, three walls
(back-left, back-right, near-right with the exit door), near-left side
OPEN. A YELLOW diamond sits on floor cell (7,2) — the interior doorstep:
the walkable cell in front of the exit door in the near-right wall.

Also renders template-intprops.png: the interior props sheet (3x2 regions,
blocks9 convention at interior scale, cyan background this time).

Usage: python3 tools/interior_template.py [OUTDIR]
"""
import os, sys
from PIL import Image, ImageDraw

S = 1024
CELL = 100            # px width of one 0.5 m cell diamond (2:1 -> 50 px tall)
ROOM = (8, 8)         # declared painted cells
DOOR = (7, 2)         # doorstep cell: in front of the near-right wall (i=8 edge)
CYAN = (0, 200, 216)
MAG = (255, 0, 255)
SEAM = (225, 0, 225)  # darker magenta, still inside the slicer's magenta key
YELLOW = (255, 212, 0)
FLOOR_B = (172, 122, 78)   # variant B: neutral warm tone the model repaints
TY = 300              # back corner y on the sheet (leaves headroom for walls)

E1 = (CELL / 2.0, CELL / 4.0)     # +i edge (down-right)
E2 = (-CELL / 2.0, CELL / 4.0)    # +j edge (down-left)

def pt(a, b, T=(S / 2.0, TY)):
    return (T[0] + a * E1[0] + b * E2[0], T[1] + a * E1[1] + b * E2[1])

def diamond(d, ci, cj, k=0.82, fill=YELLOW):
    q = [(ci + 0.5 - k / 2, cj + 0.5 - k / 2), (ci + 0.5 + k / 2, cj + 0.5 - k / 2),
         (ci + 0.5 + k / 2, cj + 0.5 + k / 2), (ci + 0.5 - k / 2, cj + 0.5 + k / 2)]
    d.polygon([pt(a, b) for a, b in q], fill=fill)

def shell_a(out):
    fw, fh = ROOM
    im = Image.new('RGB', (S, S), CYAN)
    d = ImageDraw.Draw(im)
    d.polygon([pt(0, 0), pt(fw, 0), pt(fw, fh), pt(0, fh)], fill=MAG)
    for a in range(1, fw):
        d.line([pt(a, 0), pt(a, fh)], fill=SEAM, width=2)
    for b in range(1, fh):
        d.line([pt(0, b), pt(fw, b)], fill=SEAM, width=2)
    diamond(d, *DOOR)
    im.save(out)
    print('wrote', out, ' %dx%d cells @ %dpx, doorstep %s' % (fw, fh, CELL, DOOR))

def shell_b(out):
    fw, fh = ROOM
    BAND = 0.35        # border band width in cells
    im = Image.new('RGB', (S, S), CYAN)
    d = ImageDraw.Draw(im)
    d.polygon([pt(0, 0), pt(fw, 0), pt(fw, fh), pt(0, fh)], fill=MAG)
    d.polygon([pt(BAND, BAND), pt(fw - BAND, BAND),
               pt(fw - BAND, fh - BAND), pt(BAND, fh - BAND)], fill=FLOOR_B)
    diamond(d, *DOOR)
    im.save(out)
    print('wrote', out, ' border band %.2f cells' % BAND)

# ---- interior props sheet: 3x2 regions, marks on cyan ----------------------
PCELL = 110
PAD_BOTTOM = 70
# name -> (col, row, footW, footH). Square-ish only: the 2x1 strip refusal is
# a proven model defect (blocks9 + bldg rounds), so shelf ships 1x1.
PROPS = {
    'oven':      (0, 0, 2, 2),
    'counter':   (1, 0, 2, 2),
    'preptable': (2, 0, 2, 2),
    'shelf':     (0, 1, 1, 1),
    'stool':     (1, 1, 1, 1),
    'sacks':     (2, 1, 1, 1),
}
COLS, ROWS = 3, 2

def props_sheet(out):
    im = Image.new('RGB', (S, S), CYAN)
    d = ImageDraw.Draw(im)
    LINE = (0, 178, 194)
    for k in range(1, COLS):
        d.line([(round(k * S / COLS), 0), (round(k * S / COLS), S)], fill=LINE, width=2)
    d.line([(0, S // ROWS), (S, S // ROWS)], fill=LINE, width=2)
    e1 = (PCELL / 2.0, PCELL / 4.0)
    e2 = (-PCELL / 2.0, PCELL / 4.0)
    for name, (col, row, fw, fh) in PROPS.items():
        x0, x1 = round(col * S / COLS), round((col + 1) * S / COLS)
        y1 = round((row + 1) * S / ROWS)
        q = [(0, 0), (fw, 0), (fw, fh), (0, fh)]
        xs = [a * e1[0] + b * e2[0] for a, b in q]
        ys = [a * e1[1] + b * e2[1] for a, b in q]
        Tx = (x0 + x1) / 2.0 - (min(xs) + max(xs)) / 2.0
        Ty_ = y1 - PAD_BOTTOM - max(ys)
        p = lambda a, b: (Tx + a * e1[0] + b * e2[0], Ty_ + a * e1[1] + b * e2[1])
        d.polygon([p(a, b) for a, b in q], fill=MAG)
        for a in range(1, fw):
            d.line([p(a, 0), p(a, fh)], fill=SEAM, width=2)
        for b in range(1, fh):
            d.line([p(0, b), p(fw, b)], fill=SEAM, width=2)
    im.save(out)
    print('wrote', out)

def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    shell_a(os.path.join(outdir, 'template-bakint-a.png'))
    shell_b(os.path.join(outdir, 'template-bakint-b.png'))
    props_sheet(os.path.join(outdir, 'template-intprops.png'))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'public/assets/iso/interior')
