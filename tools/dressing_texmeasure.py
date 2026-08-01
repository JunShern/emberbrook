"""dressing_texmeasure.py — THE LIBRARY'S TEXTURE RULER, made re-runnable.

    python3 tools/dressing_texmeasure.py [<manifest.json>] [--id <substr>]
    python3 tools/dressing_texmeasure.py --files a_Diffuse.jpg b_Diffuse.jpg

Prints, per `textures` entry of the dressing manifest, the LINEAR albedo of its diffuse
map: mean RGB, Rec.709 luminance, the spatial sd of that luminance, and R/B.

WHY THIS FILE EXISTS, and it is the same lesson `tools/emb_lum.py` was written to record.
The masonry intake round chose between twenty CC0 wall scans on a number — "which of these
is dark enough to land the pilot's stone at the bar with the town lamps burning" — and that
number was first taken with an ad-hoc snippet that no later round could re-run against a new
candidate without retyping it.  A library that records a measurement without shipping its
instrument is a library whose next reader has to guess what was measured.

WHAT IS BEING MEASURED, exactly, because "albedo" is ambiguous and the ambiguity is the trap.
An 8-bit PNG/JPEG diffuse map is sRGB-ENCODED.  Averaging its bytes and dividing by 255
gives a number ~1.6x too high on a dark stone, because the encoding is concave.  Blender
loads the map through the sRGB colour space and hands the shader LINEAR values, so the
number that predicts a render is the mean of the LINEARISED pixels — which is what this
prints.  The bare 8-bit mean is printed alongside, in brackets, purely so a reader who
measured the other way can see both and tell which one they have.

THE COMPARISON THAT MADE IT ACTIONABLE, recorded here so the next round does not re-derive
it: `emb_dress.py` drives its procedural masonry from probe2's own flat colours, linear
(0.262, 0.246, 0.223) rubble = luminance 0.2477.  Round 5's measured albedo curve on the
gate frame WITH the town lamps at 1.0 lands the bar (L=99.7) at albedo scale 0.435, i.e. an
effective linear luminance of 0.108.  So "dark enough" had a number before any texture was
downloaded, and the screen was a sort, not an opinion.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = np.array([0.2126, 0.7152, 0.0722])


def srgb_to_linear(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def measure(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
    lin = srgb_to_linear(a)
    rgb = lin.reshape(-1, 3).mean(0)
    lum = lin @ W
    return rgb, float(lum.mean()), float(lum.std()), float(a.reshape(-1, 3).mean(0) @ W)


def row(label, path):
    if not os.path.exists(path):
        print("  %-26s TEX-MISS %s" % (label, path))
        return
    rgb, lm, sd, raw = measure(path)
    print("  %-26s lin %.3f/%.3f/%.3f  lum=%.4f  sd=%.4f  R/B=%.2f   [8-bit mean %.3f]"
          % (label, rgb[0], rgb[1], rgb[2], lm, sd, rgb[0] / max(rgb[2], 1e-9), raw))


def main(argv):
    if "--files" in argv:
        for p in argv[argv.index("--files") + 1:]:
            row(os.path.basename(p), p)
        return 0
    want = argv[argv.index("--id") + 1] if "--id" in argv else ""
    pos = [a for a in argv if not a.startswith("-")]
    mf = pos[0] if pos else os.path.join(REPO, "public/assets/dressing/manifest.json")
    m = json.load(open(mf))
    root = m.get("root") or os.path.dirname(mf)
    if not os.path.isabs(root):
        root = os.path.join(REPO, root)
    print("LINEAR ALBEDO of every diffuse map in %s" % os.path.relpath(mf, REPO))
    print("  (the shader-side number; the bar's own procedural stone is lum 0.2477 and the "
          "\n   pilot's measured target with the town lamps on is 0.108 — see the docstring)")
    for t in m.get("textures", []):
        if want and want not in t.get("id", ""):
            continue
        d = t.get("diffuse")
        if not d:
            continue
        row("%s [%s]" % (t["id"], t.get("role", "?")),
            d if os.path.isabs(d) else os.path.join(root, d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
