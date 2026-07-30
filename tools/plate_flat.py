#!/usr/bin/env python3
"""plate_flat.py — find UNSHADED FLAT FILLS in baked backdrops.

    python3 tools/plate_flat.py [scene-key]        default del-cine

WHAT IT CATCHES. A backdrop card, a haze plane rendered without its volume, a material
with no shading, an emissive slab standing in for atmosphere: all of them land in the
plate as a region of literally constant colour. Real painted geometry never does -- even
a flat wall carries a light gradient, a shadow, or texture noise. So "a large connected
region whose colour variance is ~0" is a reliable, art-direction-agnostic signature of
something that is not really there.

WHY IT EXISTS. The 2026-07-30 water-facing pass turned five cameras OUTWARD along the
gorge for the first time in the town's life. The probe render of the Crossing's new
yaw-195 frame showed a hard-edged salmon rectangle (RGB 155,91,61, per-pixel std 0.41,
4.3% of frame, ndc x -0.72..-0.33 y 0.52..1.00) sitting over the water. Scanning all 17
SHIPPED plates for the same fill returned 0.00% on every one -- so the object was always
there and had simply never been in frame while every camera looked INTO the cliff.

That is the general hazard of a re-aim pass and the reason this is a tool and not a note:
a town's far field is built for the angles it has been shot from, and the first camera to
look somewhere new is the first to find what was never finished there.
"""
import sys, os, glob
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENE = sys.argv[1] if len(sys.argv) > 1 else 'del-cine'
# CALIBRATED, not chosen. At 0.2% this screen flagged 1 of 17 shipped plates: loop-stairs
# at 0.72%, which on inspection is a real pale panel with a cast shadow on it -- evenly
# lit geometry, not a card. The Crossing's actual card was 4.29%. 1% sits between them and
# keeps the screen worth a human's attention. This is a SCREEN: it produces candidates for
# eyes, never a verdict. Lower it when hunting, and expect large flat lit surfaces back.
MIN_FRAC = 0.01
BLOCK = 8                 # variance is measured over 8x8 blocks

def far_plane_fill(bg_path, depth_path, far):
    """The EXACT signature of a render-only volume that rendered as a card.

    cine_bake.py deletes fog/haze/steam_vol/smoke objects before the DEPTH pass, and
    encodes 'no surface hit' as the far plane. So a region that is a constant colour in
    the beauty plate AND reads exactly the far plane in the depth plate is, provably,
    something that shaded like a solid and has no geometry: a volume rendered without
    its volumetrics. No heuristics about tone or shape -- this is the mechanism itself.
    """
    bg = np.asarray(Image.open(bg_path).convert('RGB'), dtype=np.int16)
    dp = np.asarray(Image.open(depth_path).convert('RGB'), dtype=np.float64)
    dep = dp[:, :, 0]*65536 + dp[:, :, 1]*256 + dp[:, :, 2]
    nohit = dep >= 16777215*0.999
    H, W = nohit.shape
    small = np.asarray(Image.fromarray(bg.astype(np.uint8)).resize((W, H), Image.NEAREST),
                       dtype=np.int16)
    if not nohit.any():
        return 0.0, None, None
    # among no-hit pixels, the dominant colour and how flat it is
    px = small[nohit]
    c = np.median(px, axis=0)
    same = nohit & (np.abs(small - c).max(2) <= 3)
    frac = same.sum() / (H*W)
    if frac < 1e-6:
        return 0.0, None, None
    ys, xs = np.nonzero(same)
    ndc = (xs.min()/W*2-1, xs.max()/W*2-1, 1-ys.max()/H*2, 1-ys.min()/H*2)
    return frac, np.round(c, 0), ndc

def flat_regions(path):
    im = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)
    H, W, _ = im.shape
    h, w = H // BLOCK, W // BLOCK
    b = im[:h*BLOCK, :w*BLOCK].reshape(h, BLOCK, w, BLOCK, 3)
    var = b.std(axis=(1, 3)).max(axis=2)          # per-block colour spread
    mean = b.mean(axis=(1, 3))
    flat = var < 0.75                              # essentially constant
    if not flat.any():
        return 0.0, None, None, 0.0
    # largest connected run of flat blocks sharing one colour
    seen = np.zeros_like(flat); best = []
    for y in range(h):
        for x in range(w):
            if not flat[y, x] or seen[y, x]:
                continue
            c0 = mean[y, x]; stack = [(y, x)]; seen[y, x] = True; blob = []
            while stack:
                cy, cx = stack.pop(); blob.append((cy, cx))
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = cy+dy, cx+dx
                    if 0 <= ny < h and 0 <= nx < w and flat[ny, nx] and not seen[ny, nx] \
                       and np.abs(mean[ny, nx] - c0).max() <= 3:
                        seen[ny, nx] = True; stack.append((ny, nx))
            if len(blob) > len(best):
                best = blob; bc = c0
    if not best:
        return 0.0, None, None, 0.0
    P = np.array(best)
    frac = len(best) / (h * w)
    ys, xs = P[:, 0] * BLOCK, P[:, 1] * BLOCK
    ndc = (xs.min()/W*2-1, xs.max()/W*2-1, 1-ys.max()/H*2, 1-ys.min()/H*2)
    # RECTANGULARITY: what fraction of the blob's own bounding box it fills. A card is a
    # quad, so it fills its box; crushed shadow and blown highlight are organic and do not.
    bw = (P[:,1].max()-P[:,1].min()+1) * (P[:,0].max()-P[:,0].min()+1)
    rect = len(best) / bw if bw else 0.0
    return frac, np.round(bc, 0), ndc, rect

if __name__ == '__main__':
    pat = os.path.join(ROOT, 'public/assets/scenes', SCENE, 'cameras/*/bg.png')
    plates = sorted(glob.glob(pat))
    if not plates:
        sys.exit('no plates under ' + pat)
    import json
    cine = json.load(open(os.path.join(ROOT, 'public/assets/scenes', SCENE, 'cine.json')))
    FAR = {x['id']: x['depth']['far'] for x in cine['cameras'] if x.get('depth')}
    bad = 0
    print('%-15s %7s  %-16s %s' % ('plate', 'card%', 'colour', 'ndc bbox'))
    for p in plates:
        cid = os.path.basename(os.path.dirname(p))
        dpath = os.path.join(os.path.dirname(p), 'depth.png')
        if not os.path.exists(dpath) or cid not in FAR:
            print('%-15s   (no depth plate — skipped)' % cid); continue
        frac, c, ndc = far_plane_fill(p, dpath, FAR[cid])
        rect = 1.0
        # A flat region is only SUSPICIOUS if it is a mid-tone (not clipped black, not a
        # blown highlight -- both are legitimately constant) AND shaped like a quad.
        flag = frac >= MIN_FRAC
        bad += flag
        print('%-15s %6.2f%%  %-16s %s%s' % (
            cid, 100*frac,
            '' if c is None else 'RGB %d,%d,%d' % tuple(c),
            '' if ndc is None else 'x %.2f..%.2f y %.2f..%.2f' % ndc,
            '   <== VOLUME RENDERED AS A CARD' if flag else ''))
    print('\n%s — %d of %d plates carry a volume rendered as a card >= %.1f%% of frame'
          % ('FLAG' if bad else 'clean', bad, len(plates), 100*MIN_FRAC))
    sys.exit(1 if bad else 0)
