"""rungread.py — read a dose ladder inside the subject's OWN ray-derived mask.

The mask comes from `objmap` (geometry, not light), so it is THE SAME PIXELS on
every rung — the property that makes the A/B honest.  Reported: the subject's
luminance, the fraction still crushed, and the WHOLE-FRAME p95 / blown fraction,
because a fill card that lifts its subject by milking the rest of the frame is
not a fix (round 12's sky lesson).
"""
import sys, os, json
import numpy as np
from PIL import Image

S = os.path.dirname(os.path.abspath(__file__))
om = json.load(open(os.path.join(S, "objmap.json")))
SUB = "qm_stair_underworks"
dirs = sys.argv[1:]

for shot in ("deep-stairs", "waterfront"):
    c = om["cams"][shot]; W, H = c["W"], c["H"]
    g = np.zeros((H, W), bool)
    for i, o in enumerate(c["obj"]):
        if o == SUB:
            g[i // W, i % W] = True
    if not g.any():
        continue
    e = g.copy()
    e[1:, :] &= g[:-1, :]; e[:-1, :] &= g[1:, :]
    e[:, 1:] &= g[:, :-1]; e[:, :-1] &= g[:, 1:]
    g = e
    print("\n=== %s: %s mask %d rays ===" % (shot, SUB, int(g.sum())))
    print("%-26s %7s %7s %7s %8s | %8s %8s" % ("arm", "L p05", "L p50", "L p95",
                                               "L<=8 %", "frame p95", "blown %"))
    for d in dirs:
        p = os.path.join(d, "cameras", shot, "bg.png")
        if not os.path.exists(p):
            continue
        bg = np.asarray(Image.open(p).convert("RGB"), np.float32)
        PH, PW = bg.shape[:2]
        L = 0.2126 * bg[..., 0] + 0.7152 * bg[..., 1] + 0.0722 * bg[..., 2]
        yi = (np.arange(PH) * H // PH).clip(0, H - 1)
        xi = (np.arange(PW) * W // PW).clip(0, W - 1)
        M = g[yi][:, xi]
        print("%-26s %7.1f %7.1f %7.1f %8.1f | %8.1f %8.3f"
              % (os.path.basename(d), np.percentile(L[M], 5), np.percentile(L[M], 50),
                 np.percentile(L[M], 95), 100.0 * (L[M] <= 8).mean(),
                 np.percentile(L, 95), 100.0 * (L >= 254).mean()))
