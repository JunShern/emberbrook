#!/usr/bin/env python3
"""[village-base] Programmatic HSV derivation of the Emberbrook village-demo ground base
from the LIVE forest-B textures, so the village genuinely reads as "built on the same
ground as the forest".

Round-3 derivation (the version the director rejected) applied an unintended
saturation/value LIFT: the green push landed the grass +13.7% brighter (perceived
luminance) than the live forest floor, +12.5% saturation, +5.6% value. This tool
removes that lift.

GRASS  = tex-forestfloor (forest B) hue-rotated toward the approved forest-grass green,
         saturation held at the floor's own level (NO lift), and value pulled down so the
         grass's mean perceived luminance MATCHES the forest floor exactly. Same darkness
         family as forest B.
DIRT   = tex-forestpath darkened one step (~13% value), warmth preserved (hue held,
         saturation nudged so it reads as darker BROWN rather than pale sand).

Reads live textures read-only; writes only demo-candidate files. Does NOT touch any
live scene texture.
"""
import numpy as np
from PIL import Image
import os

ROOT = os.path.join(os.path.dirname(__file__), '..')
BLK = os.path.join(ROOT, 'public/assets/iso/blocks')
CAND = os.path.join(BLK, 'candidates')

FLOOR = os.path.join(BLK, 'tex-forestfloor.png')   # live forest-B floor (source, read-only)
PATH  = os.path.join(BLK, 'tex-forestpath.png')    # live forest-B path  (source, read-only)

GRASS_OUT = os.path.join(CAND, 'village-grass-forestB.png')
DIRT_OUT  = os.path.join(CAND, 'village-dirt-forestpathdark.png')

REL_LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)


def load(p):
    return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255.0


def rgb_to_hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
    v = mx
    s = np.where(mx > 1e-6, d / np.clip(mx, 1e-6, None), 0.0)
    h = np.zeros_like(mx)
    dd = np.clip(d, 1e-6, None)
    mask = d > 1e-6
    rc = ((g - b) / dd) % 6
    gc = (b - r) / dd + 2
    bc = (r - g) / dd + 4
    h = np.where(mx == r, rc, np.where(mx == g, gc, bc))
    h = np.where(mask, (h / 6.0) % 1.0, 0.0)
    return np.stack([h, s, v], -1)


def hsv_to_rgb(hsv):
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = np.floor(h * 6).astype(int)
    f = h * 6 - i
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    i = i % 6
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q])
    return np.clip(np.stack([r, g, b], -1), 0, 1)


def mean_lum(rgb):
    return float((rgb @ REL_LUM).mean())


# ---------- GRASS: green push off the floor, no lift, luminance matched ----------
floor = load(FLOOR)
floor_lum = mean_lum(floor)
fh = rgb_to_hsv(floor)

# Keep the approved green: floor median hue ~41deg -> grass ~79deg (delta +38deg).
# Constant shift preserves the floor's low-frequency hue mottling.
HUE_SHIFT_DEG = 38.0
gh = fh.copy()
gh[..., 0] = (gh[..., 0] + HUE_SHIFT_DEG / 360.0) % 1.0
# Saturation held at the floor's own level (NO lift). value untouched here.
grass = hsv_to_rgb(gh)

# Green rotation raises perceived luminance (G is the peak-luminance channel).
# Pull V down by a single factor so the grass's mean luminance == the floor's.
target = floor_lum
lo, hi = 0.4, 1.0
for _ in range(40):
    mid = (lo + hi) / 2
    gh2 = gh.copy(); gh2[..., 2] = np.clip(gh2[..., 2] * mid, 0, 1)
    if mean_lum(hsv_to_rgb(gh2)) > target:
        hi = mid
    else:
        lo = mid
VFAC = (lo + hi) / 2
gh[..., 2] = np.clip(gh[..., 2] * VFAC, 0, 1)
grass = hsv_to_rgb(gh)
Image.fromarray((grass * 255 + 0.5).astype(np.uint8)).save(GRASS_OUT)

gstat = rgb_to_hsv(grass)
print(f"GRASS  hueShift=+{HUE_SHIFT_DEG:.0f}deg  V*={VFAC:.3f}")
print(f"  floor: lum={floor_lum:.3f} S={fh[...,1].mean():.3f} V={fh[...,2].mean():.3f}")
print(f"  grass: lum={mean_lum(grass):.3f} S={gstat[...,1].mean():.3f} V={gstat[...,2].mean():.3f}"
      f"   (was lum=0.454 S=0.582 V=0.495 lifted)")

# ---------- DIRT: darken the forest path one step, keep warmth ----------
path = load(PATH)
ph = rgb_to_hsv(path)
DIRT_VFAC = 0.85           # 15% value darken (top of the 8-15% window; source path is very light)
DIRT_SFAC = 1.10           # saturation nudge so it reads darker BROWN, not pale grey sand
dh = ph.copy()
dh[..., 1] = np.clip(dh[..., 1] * DIRT_SFAC, 0, 1)
dh[..., 2] = np.clip(dh[..., 2] * DIRT_VFAC, 0, 1)
dirt = hsv_to_rgb(dh)
Image.fromarray((dirt * 255 + 0.5).astype(np.uint8)).save(DIRT_OUT)

dstat = rgb_to_hsv(dirt)
print(f"DIRT   V*={DIRT_VFAC:.2f} ({(1-DIRT_VFAC)*100:.0f}% darker)  S*={DIRT_SFAC:.2f}")
print(f"  path: lum={mean_lum(path):.3f} S={ph[...,1].mean():.3f} V={ph[...,2].mean():.3f}")
print(f"  dirt: lum={mean_lum(dirt):.3f} S={dstat[...,1].mean():.3f} V={dstat[...,2].mean():.3f}")
