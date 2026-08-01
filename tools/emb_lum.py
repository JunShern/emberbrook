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

AND IT PRINTS `clip` — the share of pixels with ANY CHANNEL at 254+ — added for the
fixture round, whose bar is "zero clipped pixels on the glass".  `>200` is a brightness
bar and stays exactly what it was (every published ratio against it is unchanged); `clip`
is a dynamic-range one, and it is measured per channel because a warm emitter pins R long
before its luminance gets near 255.

WHY THIS FILE EXISTS AT ALL.  The dressing gate's stone verdict is a NUMBER, and
round 4 recorded one taken with an ad-hoc snippet that no later round could
re-run against a new frame without retyping it — and the round before that
recorded a closing number measured on the PREVIOUS round's render.  A ruler that
lives in the repo is the cheapest defence against both.

THE FIXTURE BOXES (1400x800, the board's own pinned cameras — town.cameras.json).  Each
one is DERIVED, not eyeballed: every world vertex of the named object projected through
the pinned camera, pixel AABB, 6 px margin.  A box picked by eye off a bright patch is
how round 6 measured 460 clipped pixels of sun glare and called them a lamp.
    <cam>-district-entrance  524,265,572,312   emb_lamp_00_road-gate_glass, the only lamp
                                               in that frame, at 42.7 m
    <cam>-district-square    655,395,745,545   the Heartlight's flame: the blockout
                                               pyramid's own box (664,409-736,530) widened
                                               to the dressed shell stack, which is 1.24x
                                               wider and 1.20x taller than the pyramid it
                                               replaced
AND THE LEVEL IS DISTANCE-INVARIANT, which is why one lamp settles all fourteen: an
emissive surface's radiance does not fall off with range, so a lantern at 6 m and one at
43 m clip at the same emission strength.  What range changes is how many pixels it is,
not how bright each one is.

THE RATIFIED BOXES (1400x800 renders in docs/qa/emberbrook/styleprobe/):
    probe2-b.png  980,340,1180,560   THE BAR (stone) — the ratified probe's dressed stone
    dress*-b.png  470,400,620,545    the pit-and-plinth mass in the gate frame
    dress*-b.png  395,555,530,600    the pilot's ground — the lane slab
    probe2-b.png  720,100,855,180    THE BAR (ground) — the far bank, AND SEE BELOW

AND THE GROUND BAR'S BOX IS A RECONSTRUCTION, WHICH IS SAID OUT LOUD BECAUSE THE ROUND
THAT WROTE THE NUMBER DOWN IS THE SAME ROUND THAT WROTE THIS FILE.  Round 5 recorded
"the bar's own far bank at L=43.2" and every ratio in its ground table against it, and
recorded NO COORDINATES for it — the identical failure to the transposed stone boxes it
had just corrected, committed in the same entry.  Round 6 recovered a box by sweeping
probe2-b for one that returns the published value: 720,100-855,180 gives L=43.52 sd=9.76,
within 0.3 of 43.2, on the flat trodden bank behind the wheel, and it is the only
low-variance candidate that close.  It is NOT proven to be the original box, so the
PUBLISHED CONSTANT 43.2 stays the bar for every ratio; this box is here so the next round
has something to re-run instead of another sentence.  The pilot-side box was recorded and
is exact.

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
    # CLIPPED IS NOT THE SAME QUESTION AS HOT, and the fixture round is why this column
    # exists.  `>200` is a BRIGHTNESS bar — it is what round 4's blown gate patch was
    # caught by, and every published ratio against it stands unchanged.  A FIXTURE bar is
    # a dynamic-range one: "zero clipped pixels on the glass" means no pixel has a CHANNEL
    # at the top of the 8-bit range, because a pinned channel has thrown away the form
    # that makes an emitter read as a body of light instead of a white rectangle.
    #   PER CHANNEL, NOT ON LUMINANCE, and that is the whole point of a second column: a
    # saturated ember-orange pins R at 255 while its luminance is still near 150, so a
    # luminance peak can read 'fine' on a fixture that is already clipping in the channel
    # the fixture is made of.
    clip = 100.0 * float((c.max(axis=2) >= 254).mean())
    return (lum.mean(), lum.std(), lum.size, lum.max(),
            100.0 * float((lum > 200).mean()), clip)


def main(argv):
    if len(argv) < 2 or len(argv) % 2:
        print(__doc__)
        return 2
    bar = None
    for i in range(0, len(argv), 2):
        path = argv[i]
        box = tuple(int(v) for v in argv[i + 1].split(","))
        m, sd, n, pk, hot, clip = measure(path, box)
        if bar is None:
            bar = m
            rel = "THE BAR"
        else:
            rel = "%+.1f%% vs bar" % (100.0 * (m - bar) / bar)
        print("  %-46s %-20s L=%6.1f sd=%5.1f peak=%5.1f >200=%5.2f%% clip=%5.2f%% "
              "n=%6d  %s"
              % (path.split("/")[-1], "%d,%d-%d,%d" % box, m, sd, pk, hot, clip, n, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
