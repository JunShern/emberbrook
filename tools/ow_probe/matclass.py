"""matclass.py — R14's extension of r13's material classifier to WALLS and ROOFS.

WHY IT EXISTS.  R13 measured GRASS and STONE, matched the references on both, and
the fourteenth blind critic still said "every house wall is the SAME tan, and the
roofs are only a few percent different in value from the walls".  HOUSES WERE NEVER
A MEASURED CLASS.  No statistic about grass can constrain a roof.

WHAT THE CLASS BOUNDARY HAD TO BE, and why it is not r13's kind of rule.  R13 could
separate grass from stone by colour because they ARE different colours.  Wall and
roof are not separable by colour here — that is the defect itself — so a colour rule
would define the answer into existence.  The boundary is instead:

  * DECLARED wall boxes and roof boxes per image, dumped as an overlay
    (scratchpad/r14/mc-<label>-roi.png) so a reader can look at what was counted;
  * inside them, r13's OWN pixel rules used as EXCLUSIONS ONLY — vegetation, water
    and sky are dropped, and nothing positive is assumed about wall or roof;
  * a second, UNSUPERVISED reading over whole-building boxes: 2-means on the built
    pixels, labelled by IMAGE Y (the higher cluster is the roof).  It is an UPPER
    BOUND on the separation present in the picture — it finds the best two-way
    division that exists — so if it comes back near 1.0 no relabelling would have
    found a roof that reads darker than its wall.

Lit/shade within a class is r13's split verbatim: that class's own luminance
quartiles, so the columns compare across images.

HUE IS REPORTED WITH A WARM-COOL AXIS BESIDE IT.  The reference's stone runs sat
0.05-0.10 and an HSV hue at that chroma is noise (the windmill wall swings 224 to
302 degrees between its own quartiles).  `R-B` in sRGB is stable at any chroma and
says the one thing the round is about: positive is warm, negative is cool.

  python3 tools/ow_probe/matclass.py                 # the reference
  python3 tools/ow_probe/matclass.py <plate.png>...  # our meadow plates
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "scratchpad", "r14")
os.makedirs(OUT, exist_ok=True)

L709 = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

REF = os.path.join(ROOT, "public/assets/refs/reimagine_ff9_overworld_3.jpg")

# Declared regions.  ('roof'|'wall') = a surface box; 'bldg' = a whole building,
# fed to the unsupervised split.  The boxes are the only judgement in the file.
REG_REF = [
    ("roof", 258, 78, 336, 152),      # windmill: the slate cap, clear of the sails
    ("roof", 262, 140, 352, 186),
    ("wall", 300, 300, 470, 560),     # windmill: the pale stone tower
    ("bldg", 250, 65, 505, 625),      # windmill entire
    ("bldg", 495, 395, 730, 700),     # the two stone huts
]
# our meadow plate, 1400 x 733
REG_OURS = [
    ("roof", 185, 420, 450, 540), ("wall", 300, 565, 450, 690),    # left foreground
    ("roof", 605, 218, 752, 300), ("wall", 615, 308, 742, 392),    # centre
    ("roof", 1020, 215, 1205, 330), ("wall", 1030, 338, 1120, 418),  # right
    ("bldg", 150, 395, 480, 705), ("bldg", 585, 205, 765, 405),
    ("bldg", 640, 85, 800, 215), ("bldg", 1005, 145, 1230, 425),
    ("bldg", 1225, 165, 1400, 470),
]


def built_mask(im):
    """r13's own rules used as EXCLUSIONS: what survives vegetation, water and sky
    is built surface.  No positive colour rule for either class."""
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    chroma = im.max(2) - im.min(2)
    L = L709(im)
    veg = (g >= r) & (g >= b) & (chroma > 0.05)
    # THE WATER RULE HAD TO BE LOOSENED AND THIS IS THE ROUND'S FIRST FINDING.
    # r13's `b is the max channel and chroma > 0.08` is a fine rule for a river in
    # OUR frames, where nothing else is blue.  Run it on the reference it DELETES
    # THE SLATE AND MOST OF THE STONE TOWER — the reference's built surfaces are
    # cool, which is the very fact the round is chasing.  A classifier whose
    # exclusions are written against our own art cannot measure art we do not have.
    # Real water here is high-chroma cyan (g above r as well as b), so ask for that.
    #
    # AND THE SAME BUG CAME BACK ON OUR OWN FRAME THE MOMENT THE SLATE BECAME SLATE
    # (r14 second pass).  The loosened rule was still only a CHROMA threshold, so it
    # deleted 36% of the roof boxes' pixels out of the 2d4db1 plate — 63223 pixels
    # counted with the rule off, 40450 with it on — and the pixels it took were the
    # bluest ones, which biased the very number the round is about: roof HSV sat read
    # 0.165 with the rule and 0.309 without.  It was ALREADY biasing the 374c81 plate
    # the pass before (0.076 with, 0.114 without), so the "5.9x under the reference"
    # figure in 13cd671 was partly the instrument.  A CLASSIFIER THAT DELETES THE
    # CLASS IT IS MEASURING REPORTS THE ABSENCE IT CAUSED.
    #
    # The fix is the axis, not the threshold.  Our river is CYAN — g sits almost on
    # top of b — while slate is BLUE, g much nearer r than b.  `cy` is where g falls
    # on the r->b span: 1.0 is pure cyan, 0.0 is pure blue.  Measured: our river runs
    # 0.75-1.0, our roof 0.17, the reference's slate 0.27, the reference's stone
    # tower 0.32.  0.55 separates them with room on both sides.
    cy = (g - r) / np.maximum(b - r, 1e-6)
    water = (b >= r) & (b >= g) & (g >= r) & (chroma > 0.20) & (cy > 0.55)
    return ~veg & ~water & (L > 0.03) & (L < 0.86)


def line(nm, px):
    m = px.mean(0)
    h, s, _ = colorsys.rgb_to_hsv(*m)
    l = L709(px)
    lo, hi = np.percentile(l, 25), np.percentile(l, 75)
    sh, li = px[l <= lo], px[l >= hi]
    ms, mlt = sh.mean(0), li.mean(0)
    hs = colorsys.rgb_to_hsv(*ms)[0] * 360.0
    hl = colorsys.rgb_to_hsv(*mlt)[0] * 360.0
    La, Ls, Ll = float(L709(m)), float(l[l <= lo].mean()), float(l[l >= hi].mean())
    print("  %-4s n=%7d  MEAN rgb %5.3f %5.3f %5.3f  L %.3f  hue %5.1f  sat %.3f  R-B %+.3f"
          % (nm, len(px), *m, La, h * 360.0, s, m[0] - m[2]))
    print("       SHADE L %.3f hue %5.1f R-B %+.3f | LIT L %.3f hue %5.1f R-B %+.3f"
          "  ->  shade/lit L %.2f  dhue %+6.1f  d(R-B) %+.3f"
          % (Ls, hs, ms[0] - ms[2], Ll, hl, mlt[0] - mlt[2], Ls / max(Ll, 1e-6),
             ((hs - hl + 540) % 360) - 180, (ms[0] - ms[2]) - (mlt[0] - mlt[2])))
    return La, m


def kmeans2(x, c0, c1, iters=40):
    c = np.array([c0, c1], float)
    a = None
    for _ in range(iters):
        a = ((x[:, None, :] - c[None, :, :]) ** 2).sum(-1).argmin(1)
        for k in (0, 1):
            if (a == k).any():
                c[k] = x[a == k].mean(0)
    return a


def report(path, boxes, label):
    im = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    ov = (im * 255).astype(np.uint8).copy()
    bank = {"roof": [], "wall": []}
    kroof, kwall, per = [], [], []
    for (kind, x0, y0, x1, y1) in boxes:
        sub = im[y0:y1, x0:x1]
        m = built_mask(sub)
        if m.sum() < 400:
            continue
        px = sub[m]
        idx = np.argwhere(m)
        if kind in bank:
            bank[kind].append(px)
            ov[y0:y1, x0:x1][idx[:, 0], idx[:, 1]] = ((255, 0, 200) if kind == "roof"
                                                      else (0, 220, 255))
            continue
        l = L709(px)
        a = kmeans2(px, px[l <= np.percentile(l, 20)].mean(0),
                    px[l >= np.percentile(l, 80)].mean(0))
        ry = 0 if idx[a == 0, 0].mean() < idx[a == 1, 0].mean() else 1
        if (a == ry).sum() < 200 or (a != ry).sum() < 200:
            continue
        kroof.append(px[a == ry])
        kwall.append(px[a != ry])
        per.append((float(L709(px[a != ry].mean(0))), float(L709(px[a == ry].mean(0)))))
    Image.fromarray(ov).save(os.path.join(OUT, "mc-%s-roi.png" % label))
    print("== %s  (%s)" % (label, os.path.basename(path)))
    if bank["roof"] and bank["wall"]:
        print("  -- DECLARED boxes")
        Lw, mw = line("wall", np.concatenate(bank["wall"]))
        Lr, mr = line("roof", np.concatenate(bank["roof"]))
        print("  ROOF/WALL value ratio %.3f   (target band 0.45-0.65)" % (Lr / Lw))
        print("  ROOF-WALL warm-cool  %+.3f  (negative = the roof is COOLER)"
              % ((mr[0] - mr[2]) - (mw[0] - mw[2])))
    if kroof:
        print("  -- UNSUPERVISED 2-means over whole buildings (upper bound)")
        Lw, mw = line("wall", np.concatenate(kwall))
        Lr, mr = line("roof", np.concatenate(kroof))
        print("  ROOF/WALL value ratio %.3f" % (Lr / Lw))
        print("  ROOF-WALL warm-cool  %+.3f" % ((mr[0] - mr[2]) - (mw[0] - mw[2])))
        wl = np.array([p[0] for p in per])
        print("  WALL value across %d buildings: min %.3f max %.3f  spread %.1f%%  sd %.3f"
              % (len(wl), wl.min(), wl.max(),
                 100 * (wl.max() / max(wl.min(), 1e-6) - 1), wl.std()))


if __name__ == "__main__":
    args = sys.argv[1:] or [REF]
    for a in args:
        report(a, REG_REF if "reimagine" in a else REG_OURS,
               "ref3" if "reimagine" in a else os.path.basename(a).replace(".png", ""))
