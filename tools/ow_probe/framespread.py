#!/usr/bin/env python3
"""framespread.py — HOW WIDE IS THIS PICTURE, in value and in hue.

WHY THIS EXISTS, and it is the whole lesson of gauntlet round 13 -> 14.  R13
matched the FFIX-reimagined overworld references on their L05 and on their share
of pixels under L 0.10, and shipped a frame the fourteenth blind critic called
"plainly the flatter of the two ... one undifferentiated putty-coloured mass".
Both of those statistics describe only the BOTTOM of a histogram.  A statistic is
a constraint on a DISTRIBUTION and says nothing about the RELATIONSHIPS inside
the frame, which is where craft lives.

Measured with this tool, the disagreement resolves and it is not where anyone
looked (r13 plates against the two daylight references):

    frame            5-95 range   IQR    local SD   circular R   hue SD   sectors
    ref 1              0.523     0.219    0.0434      0.631       55.0      3
    ref 3              0.442     0.152    0.0367      0.493       68.1      4
    r13 meadow         0.559     0.259    0.0393      0.872       29.9      3

BY EVERY VALUE STATISTIC THE FRAME IS NOT FLAT.  Its range is WIDER than either
reference, its interquartile spread wider, its 9x9 local contrast between the
two.  What it has no spread in is HUE: circular R 0.872 against 0.63 and 0.49,
and its three loudest hue sectors are R 0-30, O 30-60 and Y 60-90 -- THREE
ADJACENT SECTORS, 95% of the frame's chroma inside one 90-degree arc.  The
references' third sector is cyan-blue at 19-21% of the frame.  That is "the
entire frame lives in a narrow band of warm beige-green" as a number.

So the value ladder is here to be REFUSED as evidence of flatness, and the hue
spread is here because it is the number that agrees with the eye.  Neither one is
a verdict: NUMBERS ARE FOR ITERATION, THE PICTURE IS THE VERDICT (user ruling).
Open the plate.

    python3 tools/ow_probe/framespread.py <img> [<img> ...]

HUD masking is automatic: a path containing "reimagine" is treated as one of the
reference screenshots and its party panel, quest banner and minimap are cut out;
anything else is treated as one of our plates and only the sky band is dropped.
Companion to scratchpad-era refhue.py/ourhue.py, which measure per-MATERIAL
lit-vs-shade hue -- this one measures the whole frame.
"""
import sys
import numpy as np
from PIL import Image


def mask_for(path, H, W):
    m = np.ones((H, W), bool)
    if 'reimagine' in path:
        m[:int(0.22 * H), :] = False
        m[int(0.55 * H):, :int(0.26 * W)] = False
        m[:int(0.40 * H), int(0.82 * W):] = False
        m[int(0.85 * H):, int(0.90 * W):] = False
        m[int(0.92 * H):, :] = False
    else:
        m[:int(0.10 * H), :] = False
    return m


SECT = ['R 0-30', 'O 30-60', 'Y 60-90', 'YG 90-120', 'G 120-150', 'GC 150-180',
        'C 180-210', 'CB 210-240', 'B 240-270', 'V 270-300', 'M 300-330', 'MR 330-360']


def value_ladder(L, m):
    """The percentile ladder plus a 9x9 LOCAL contrast.

    The local term matters on its own: a frame with a wide histogram and no local
    structure is a gradient, not a picture.  Computed with a summed-area table so
    it is O(N) rather than an 81x gather.
    """
    l = L[m]
    q = np.percentile(l, [5, 25, 50, 75, 95])
    k, pad = 9, 4
    Lp = np.pad(L, pad, mode='edge')
    cs = np.pad(np.cumsum(np.cumsum(Lp, 0), 1), ((1, 0), (1, 0)))
    cs2 = np.pad(np.cumsum(np.cumsum(Lp * Lp, 0), 1), ((1, 0), (1, 0)))
    box = lambda c: (c[k:, k:] + c[:-k, :-k] - c[k:, :-k] - c[:-k, k:]) / (k * k)
    mu, mu2 = box(cs), box(cs2)
    loc = np.sqrt(np.maximum(0.0, mu2 - mu * mu))[m]
    return q, 100.0 * (l < 0.10).mean(), np.median(loc), np.percentile(loc, 90)


def hue_spread(im, m):
    """Chroma-weighted CIRCULAR spread of hue, and the 30-degree sector shares.

    Near-neutral pixels are excluded (chroma > 0.08): a grey pixel has no hue and
    including it would let a desaturation pass read as a hue-spread improvement.
    Circular R near 1.0 means every coloured pixel in the frame is the SAME hue.
    """
    mx, mn = im.max(2), im.min(2)
    sel = m & ((mx - mn) > 0.08)
    if sel.sum() < 500:
        return None
    px, c = im[sel], (mx - mn)[sel]
    mxs, mns = px.max(1), px.min(1)
    d = np.maximum(mxs - mns, 1e-6)
    hue = np.where(mxs == px[:, 0], ((px[:, 1] - px[:, 2]) / d) % 6.0,
          np.where(mxs == px[:, 1], (px[:, 2] - px[:, 0]) / d + 2.0,
                                    (px[:, 0] - px[:, 1]) / d + 4.0)) * 60.0
    a = np.radians(hue)
    Cb, Sb = np.average(np.cos(a), weights=c), np.average(np.sin(a), weights=c)
    R = float(np.hypot(Cb, Sb))
    sd = float(np.degrees(np.sqrt(max(0.0, -2.0 * np.log(max(R, 1e-9))))))
    share = np.bincount(np.clip((hue // 30).astype(int), 0, 11), weights=c, minlength=12)
    share = 100.0 * share / share.sum()
    return R, sd, share, 100.0 * sel.sum() / m.sum()


def run(path):
    im = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0
    H, W, _ = im.shape
    m = mask_for(path, H, W)
    L = 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
    q, under, locmed, locp90 = value_ladder(L, m)
    print('== %s' % path.split('/')[-1])
    print('   VALUE  L05 %.3f  L25 %.3f  L50 %.3f  L75 %.3f  L95 %.3f | IQR %.3f  '
          '5-95 %.3f  under0.10 %5.2f%% | localSD med %.4f p90 %.4f'
          % (*q, q[3] - q[1], q[4] - q[0], under, locmed, locp90))
    h = hue_spread(im, m)
    if h is None:
        print('   HUE    too few coloured pixels')
        return
    R, sd, share, cov = h
    top = np.argsort(share)[::-1][:3]
    print('   HUE    coloured %5.1f%% | circular R %.3f  SD %5.1f deg | sectors>=8%%: %d'
          ' | top3 %s' % (cov, R, sd, int((share >= 8.0).sum()),
                          '  '.join('%s %.0f%%' % (SECT[i], share[i]) for i in top)))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    for p in sys.argv[1:]:
        run(p)
