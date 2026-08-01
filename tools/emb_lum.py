"""emb_lum.py — THE STONE GATE'S RULER, made re-runnable.

    python3 tools/emb_lum.py <png> x0,y0,x1,y1 [<png> x0,y0,x1,y1 ...]

Prints mean/sd Rec.709 luminance (0.2126R + 0.7152G + 0.0722B) over each box of
each 8-bit PNG, plus the percentage against the FIRST box given, which is the
bar.  Boxes are pixel coords in the 1400x800 frame, x0,y0 top-left inclusive,
x1,y1 bottom-right exclusive.

IT ALSO PRINTS THE PEAK AND THE CLIPPED FRACTION, because the mean was not the
whole verdict and round 4 could not have seen that.  The bar's stone peaks at
181.3 with NOTHING above 200; round 4's gate frame peaked at 254.4 with 9.24% of
the box pinned there.  A blown patch is a surface with no material reading at
all, and it moves a mean far less than it wrecks a picture — so the redline
raised against it ("a hot white specular slab") looked like a separate,
cosmetic, roughness-shaped problem.  It was the same defect as the level.

WHY THIS FILE EXISTS AT ALL.  The dressing gate's stone verdict is a NUMBER, and
round 4 recorded one taken with an ad-hoc snippet that no later round could
re-run against a new frame without retyping it — and the round before that
recorded a closing number measured on the PREVIOUS round's render.  A ruler that
lives in the repo is the cheapest defence against both.

THE RATIFIED BOXES (1400x800 renders in docs/qa/emberbrook/styleprobe/):
    probe2-b.png  980,340,1180,560   THE BAR — the ratified probe's dressed stone
    dress*-b.png  470,400,620,545    the pit-and-plinth mass in the gate frame

AND A TRANSCRIPTION TO WATCH: round 4's DAYLOG entry lists these two boxes in the
REVERSE order to the two surfaces ("boxes 470,400-620,545 and 980,340-1180,560"),
which reads as the bar's box first.  Taken that way the same frames measure
26.8 / 43.4 / 42.4 and none of round 4's numbers reproduce.  The pairing above is
the one that returns 99.7 / 134.6 / 121.7 exactly, so it is the one that was used.
"""
import sys
import numpy as np
from PIL import Image

W = np.array([0.2126, 0.7152, 0.0722])


def measure(path, box):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
    x0, y0, x1, y1 = box
    c = a[y0:y1, x0:x1, :]
    lum = c @ W
    return (lum.mean(), lum.std(), lum.size, lum.max(),
            100.0 * float((lum > 200).mean()))


def main(argv):
    if len(argv) < 2 or len(argv) % 2:
        print(__doc__)
        return 2
    bar = None
    for i in range(0, len(argv), 2):
        path = argv[i]
        box = tuple(int(v) for v in argv[i + 1].split(","))
        m, sd, n, pk, hot = measure(path, box)
        if bar is None:
            bar = m
            rel = "THE BAR"
        else:
            rel = "%+.1f%% vs bar" % (100.0 * (m - bar) / bar)
        print("  %-40s %-20s L=%6.1f sd=%5.1f peak=%5.1f >200=%5.2f%% n=%6d  %s"
              % (path.split("/")[-1], "%d,%d-%d,%d" % box, m, sd, pk, hot, n, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
