"""mask.py — read a shipped plate through an EXACT ray-derived object/material mask.

  python3 mask.py <objmap.json> <shot> <sel> [--mat M] [--bundle DIR] [--erode N]

`sel` matches the OBJECT name (substring); `--mat` additionally requires the
material, which is how "the produce on this crate" is said without also taking
the crate.  The mask is the objmap's own 240x135 marched grid upsampled NEAREST
to the plate and ERODED by `--erode` grid cells, so no silhouette pixel of the
neighbour leaks in — the round-11 lesson that a silhouette edge fakes every
local statistic.

Prints L percentiles, the local 5x5 SD (the "is it flat" number rounds 8-11
used), and the FACET number this round adds: the fraction of the mask whose
5x5 SD is exactly 0.00, which is what a flat-shaded planar facet looks like
and a smooth-shaded curved one cannot.
"""
import sys, json, os
import numpy as np
from PIL import Image


def local_sd(a, k=2):
    H, W = a.shape
    out = np.zeros_like(a)
    p = np.pad(a, k, mode='edge')
    acc = np.zeros_like(a); acc2 = np.zeros_like(a); n = 0
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            v = p[k + dy:k + dy + H, k + dx:k + dx + W]
            acc += v; acc2 += v * v; n += 1
    m = acc / n
    return np.sqrt(np.maximum(acc2 / n - m * m, 0))


om = json.load(open(sys.argv[1]))
shot = sys.argv[2]
sel = sys.argv[3]
a = sys.argv[4:]
mat = a[a.index("--mat") + 1] if "--mat" in a else None
bundle = a[a.index("--bundle") + 1] if "--bundle" in a else "public/assets/scenes/del-cine"
er = int(a[a.index("--erode") + 1]) if "--erode" in a else 1

c = om["cams"][shot]
W, H = c["W"], c["H"]
g = np.zeros((H, W), bool)
for i, (o, m) in enumerate(zip(c["obj"], c["mat"])):
    if sel in o and (mat is None or m == mat):
        g[i // W, i % W] = True
if not g.any():
    print("NO RAYS"); sys.exit(1)
raw = int(g.sum())
for _ in range(er):
    e = g.copy()
    e[1:, :] &= g[:-1, :]; e[:-1, :] &= g[1:, :]
    e[:, 1:] &= g[:, :-1]; e[:, :-1] &= g[:, 1:]
    g = e
if not g.any():
    print("%s @ %s: %d rays, ERODED TO NOTHING (subject thinner than %d grid cells)"
          % (sel, shot, raw, er)); sys.exit(0)

bg = np.asarray(Image.open(os.path.join(bundle, "cameras", shot, "bg.png"))
                .convert("RGB"), np.float32)
PH, PW = bg.shape[:2]
L = 0.2126 * bg[..., 0] + 0.7152 * bg[..., 1] + 0.0722 * bg[..., 2]
sd = local_sd(L)
yi = (np.arange(PH) * H // PH).clip(0, H - 1)
xi = (np.arange(PW) * W // PW).clip(0, W - 1)
M = g[yi][:, xi]
n = int(M.sum())
print("%s%s @ %s: %d rays raw, %d after erode-%d  -> %d plate px (%.3f%% of frame)"
      % (sel, (" | " + mat) if mat else "", shot, raw, int(g.sum()), er, n, 100.0 * n / (PH * PW)))
print("  L p05 %.1f p50 %.1f p95 %.1f  mean %.1f  sd %.1f"
      % (np.percentile(L[M], 5), np.percentile(L[M], 50), np.percentile(L[M], 95),
         L[M].mean(), L[M].std()))
print("  5x5 SD p50 %.2f p90 %.2f   FLAT(sd==0.00) %.1f%%   flat(<=2) %.1f%%"
      % (np.percentile(sd[M], 50), np.percentile(sd[M], 90),
         100.0 * (sd[M] < 0.005).mean(), 100.0 * (sd[M] <= 2).mean()))
mx = bg.max(2); mn = bg.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
print("  RGB %.1f,%.1f,%.1f  sat %.3f"
      % (bg[..., 0][M].mean(), bg[..., 1][M].mean(), bg[..., 2][M].mean(), sat[M].mean()))
