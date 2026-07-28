#!/usr/bin/env python3
# [groundv2] Key the flat-magenta background off the deck-edge sprites and trim
# to the opaque bounding box. Output -> public/assets/iso/dellhollow/<id>.png
# (transparent, engine-placed by the deck-platform system).
import sys, glob, os
import numpy as np
from PIL import Image

RAW = 'public/assets/iso/dellhollow/raw'
OUT = 'public/assets/iso/dellhollow'

def key(p):
    im = Image.open(p).convert('RGBA')
    a = np.asarray(im).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # magenta signature: high R, high B, low G
    mag = (r > 120) & (b > 120) & (g < 110) & (r - g > 40) & (b - g > 40)
    out = np.asarray(im).copy()
    out[mag, 3] = 0
    # feather a 2px alpha erosion at the key boundary to kill the magenta halo
    alpha = out[..., 3].astype(np.float32) / 255.0
    # simple 1-ring erosion
    er = alpha.copy()
    er[1:, :] = np.minimum(er[1:, :], alpha[:-1, :])
    er[:-1, :] = np.minimum(er[:-1, :], alpha[1:, :])
    er[:, 1:] = np.minimum(er[:, 1:], alpha[:, :-1])
    er[:, :-1] = np.minimum(er[:, :-1], alpha[:, 1:])
    out[..., 3] = (er * 255).astype(np.uint8)
    # de-spill: neutralize residual magenta on semi-transparent fringe pixels
    rgb = out[..., :3].astype(np.int16)
    spill = (out[..., 3] > 0) & (out[..., 3] < 255) & (rgb[..., 0] > rgb[..., 1]) & (rgb[..., 2] > rgb[..., 1])
    gg = rgb[..., 1]
    out[spill, 0] = np.minimum(out[spill, 0], gg[spill] + 12)
    out[spill, 2] = np.minimum(out[spill, 2], gg[spill] + 12)
    # trim to opaque bbox
    ys, xs = np.where(out[..., 3] > 8)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        out = out[y0:y1, x0:x1]
    outp = os.path.join(OUT, os.path.basename(p))
    Image.fromarray(out).save(outp)
    print('keyed', outp, out.shape)

if __name__ == '__main__':
    filt = sys.argv[1] if len(sys.argv) > 1 else ''
    for p in sorted(glob.glob(os.path.join(RAW, f'*{filt}*.png'))):
        key(p)
