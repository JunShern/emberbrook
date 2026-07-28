#!/usr/bin/env python3
# [groundpicker] Post-process raw ground candidates -> 512x512 seamless tiles.
# Resize 1024->512, then make seamlessly tileable by blending a half-offset copy
# in a smoothstep band near the edges (center stays crisp; outer edges wrap
# continuously). Good for the low-frequency painterly ground we generate.
import sys, glob, os
import numpy as np
from PIL import Image

RAW = 'public/assets/iso/blocks/candidates/raw'
OUT = 'public/assets/iso/blocks/candidates'

def tileable(a, edge=0.55):
    H, W = a.shape[:2]
    af = a.astype(np.float32)
    b = np.roll(np.roll(af, H // 2, 0), W // 2, 1)
    ny = np.abs(np.linspace(-1, 1, H))[:, None]
    nx = np.abs(np.linspace(-1, 1, W))[None, :]
    d = np.maximum(ny, nx)
    t = np.clip((d - edge) / (1 - edge), 0, 1)
    w = (t * t * (3 - 2 * t))[..., None]
    out = af * (1 - w) + b * w
    return np.clip(out, 0, 255).astype(np.uint8)

def process(p):
    im = Image.open(p).convert('RGB')
    im = im.resize((512, 512), Image.LANCZOS)
    a = np.asarray(im)
    a = tileable(a)
    outp = os.path.join(OUT, os.path.basename(p))
    Image.fromarray(a).save(outp)
    kb = os.path.getsize(outp) // 1024
    print('wrote', outp, f'{kb}KB')

if __name__ == '__main__':
    filt = sys.argv[1] if len(sys.argv) > 1 else ''
    files = sorted(glob.glob(os.path.join(RAW, f'*{filt}*.png')))
    for p in files:
        process(p)
    print(f'processed {len(files)} files')
