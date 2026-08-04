#!/usr/bin/env python3
"""canopyhist.py — VALUE AND HUE of a leaf mass, ours against the references'.

  python3 tools/ow_probe/canopyhist.py                    # atlas vs the ref crops
  python3 tools/ow_probe/canopyhist.py --img a.png --img b.png

THE CLAIM THIS INSTRUMENT EXISTS TO TEST (blind critic, round T1): the reference's
shrub/tree masses hold a NARROW VALUE RANGE over a WIDE HUE RANGE — yellow-green
through blue-green at roughly constant luminance — and ours hold near-black cores
against blown chartreuse highlights.  That is a statement about two distributions
and it is measurable directly off the art, with no build and no browser.

WHAT IS COMPARED, AND THE ONE CAVEAT.  `leafclump_atlas.png` is albedo WITH THE
LIGHT BAKED IN (foliage_atlas.py's own docstring), so it is the same kind of thing
as a pixel of a rendered reference frame: a lit leaf.  It is not the same thing as
a shipped pixel, because the runtime multiplies by COLOR_0 and by its own key —
a card that reads correct here can still read wrong in frame, which is why the
plate is the verdict and this is only the ruler.  Alpha < 0.5 is excluded: the
cutout's transparent half is not art.

Hue spread is CHROMA-WEIGHTED and circular (the same treatment framespread.py
uses on whole frames), because an unweighted hue mean over near-grey pixels is
noise dressed as a number.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ATLAS = os.path.join(ROOT, "tools/textures/overworld/leafclump_atlas.png")
REF = os.path.join(ROOT, "public/assets/refs/reimagine_ff9_overworld_1.jpg")
# canopy/shrub crops of ref 1, chosen by eye off a contact sheet and clear of the
# HUD.  (l, t, r, b) in the 1920x1080 frame.
REF_BOXES = {
    "ref-cave-shrub": (780, 380, 910, 500),
    "ref-east-shrub": (1480, 440, 1660, 580),
    "ref-ridge-scrub": (1370, 470, 1560, 620),
}


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def stats(rgb, name, alpha=None):
    """rgb float 0..1 sRGB, shape (...,3).  Returns a dict, prints a row."""
    a = rgb.reshape(-1, 3)
    if alpha is not None:
        a = a[alpha.reshape(-1) > 0.5]
    if not len(a):
        return None
    lin = srgb_to_lin(a)
    L = lin @ np.array([0.2126, 0.7152, 0.0722])
    # perceptual value: sRGB-ish luma, which is what "value range" means to an eye
    V = a @ np.array([0.2126, 0.7152, 0.0722])
    mx, mn = a.max(1), a.min(1)
    chroma = mx - mn
    sat = chroma / np.maximum(mx, 1e-6)
    # circular hue, chroma-weighted
    r, g, b = a[:, 0], a[:, 1], a[:, 2]
    hue = np.zeros(len(a))
    m = chroma > 1e-6
    imax = a.argmax(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        h = np.where(imax == 0, ((g - b) / np.maximum(chroma, 1e-9)) % 6.0,
                     np.where(imax == 1, (b - r) / np.maximum(chroma, 1e-9) + 2.0,
                              (r - g) / np.maximum(chroma, 1e-9) + 4.0))
    hue[m] = (h[m] * 60.0) % 360.0
    w = chroma
    ang = np.deg2rad(hue)
    C = float((w * np.cos(ang)).sum()), float((w * np.sin(ang)).sum())
    W = float(w.sum()) or 1.0
    R = (C[0] ** 2 + C[1] ** 2) ** 0.5 / W       # 1 = one hue, 0 = all hues
    hmean = np.rad2deg(np.arctan2(C[1], C[0])) % 360.0
    # chroma-weighted hue IQR, measured about the mean on the circle
    d = (hue - hmean + 180.0) % 360.0 - 180.0
    o = np.argsort(d)
    cw = np.cumsum(w[o]) / W
    q = lambda p: float(d[o][np.searchsorted(cw, p)]) if len(o) else 0.0
    p = np.percentile(V, [2, 5, 25, 50, 75, 95, 98])
    out = dict(name=name, n=len(a), V05=p[1], V25=p[2], V50=p[3], V75=p[4],
               V95=p[5], rng=p[5] - p[1], iqr=p[4] - p[2],
               dark=float((V < 0.06).mean()), blown=float((V > 0.72).mean()),
               sat=float(np.median(sat)), hueR=R, hue=hmean,
               hspread=q(0.75) - q(0.25), L50=float(np.median(L)))
    print("  %-18s n=%-8d V05 %.3f  V50 %.3f  V95 %.3f  rng %.3f  IQR %.3f | "
          "<.06 %5.1f%%  >.72 %5.1f%% | hue %5.1f  R %.3f  hIQR %5.1f  sat %.3f"
          % (name, out["n"], out["V05"], out["V50"], out["V95"], out["rng"],
             out["iqr"], 100 * out["dark"], 100 * out["blown"], out["hue"],
             out["hueR"], out["hspread"], out["sat"]))
    return out


def atlas_stats(path=ATLAS, label=None):
    im = np.asarray(Image.open(path).convert("RGBA"), np.float32) / 255.0
    return stats(im[..., :3], label or os.path.basename(path), im[..., 3])


def ref_stats():
    im = np.asarray(Image.open(REF).convert("RGB"), np.float32) / 255.0
    out = []
    for k, (l, t, r, b) in REF_BOXES.items():
        out.append(stats(im[t:b, l:r], k))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", action="append", default=[])
    ap.add_argument("--atlas", default=ATLAS)
    a = ap.parse_args()
    print("REFERENCE (reimagine_ff9_overworld_1.jpg canopy crops)")
    ref_stats()
    print("OURS")
    if os.path.exists(a.atlas):
        atlas_stats(a.atlas)
    for p in a.img:
        if p.lower().endswith(".png"):
            atlas_stats(p)
        else:
            im = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255.0
            stats(im, os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
