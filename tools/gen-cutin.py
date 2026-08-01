#!/usr/bin/env python3
"""gen-cutin.py — MAT THE BUSTS INTO CUT-IN PORTRAITS.

    python3 tools/gen-cutin.py                 # every character with a bust.png
    python3 tools/gen-cutin.py odessa maren    # just these
    python3 tools/gen-cutin.py --force         # re-mat art that already has a cutin
    python3 tools/gen-cutin.py --report        # write the QA contact sheets, mat nothing

WHAT THIS IS FOR. The busts are 1024x1024 colour-pencil plates on warm toned paper,
drawn to sit INSIDE a portrait frame. The user ruled the modern cut-in grammar instead
(2026-08-01): the character art rises OUT of the dialogue box with no frame and no
background, chest-up, overlaid on the scene. That needs two things the bust is not:
an ALPHA CUTOUT, and a CHEST-UP CROP. Both are derivable from the art we already paid
for, so this file derives them — regeneration is the fallback, not the plan.

    public/assets/characters/<id>/bust.png      ->  cutin.png
    public/assets/characters/<id>/expr-<m>.png  ->  cutin-<m>.png

bust.png STAYS. The save menu, the shop plate and every other .eb-port consumer still
want a square framed thumbnail, and dialogue.js falls back to exactly that for any
speaker this tool could not mat. cutin.png is ADDITIVE.

HOW THE MATTE WORKS, and why each step is there:

 1. THERE IS NO KEY COLOUR TO FIND, and two measurements say so. These plates carry a
    broad radial gradient behind the figure, and the paper both DARKENS and SATURATES
    across it — Hobb's runs (216,175,127) at the corners and (180,130,89) in the middle,
    a chromaticity drift of 0.034, which is wider than any usable threshold. A quadratic
    surface fitted from the border ring cannot help either: a bulge that lives in the
    MIDDLE is extrapolation from the edge, and that version keyed Hobb at 64% opaque —
    the entire glow read as character. So this tool never asks "is this pixel the
    background colour". It asks whether a pixel matches THE NEIGHBOUR IT WAS REACHED
    FROM, and grows the background out from the border one step at a time (flood_local).
    A step-wise test has no global reference to be wrong about: it follows a gradient of
    any shape for as long as the gradient stays smooth, and stops where the picture
    actually steps.

 2. THE HARD BARRIER IS LINEWORK, MEASURED AS LOCAL RANGE (max minus min in a 3x3).
    Smooth paper has almost none; a pencil edge has plenty. The flood runs at quarter
    scale with the colour MEAN-pooled — which removes the paper's grain, so the step
    tolerances measure the picture rather than the medium — and the barrier MAX-pooled,
    so a one-pixel line still blocks at full strength. Connectivity is then what saves
    the half of this cast who wear the paper's own colour: Hobb's coat and the
    villager's tunic are tan and smooth, but they are ENCLOSED, and a flood cannot
    reach them.

 3. THE PAPER MODEL IS FITTED AFTERWARDS, FROM THE BACKGROUND WE FOUND. Once the
    segmentation is in hand, a per-channel QUARTIC surface over the pixels actually
    classified as paper reproduces the glow and the vignette accurately — it is
    interpolation now, not extrapolation. That model is what the soft edge and the
    colour decontamination are measured against.

 4. THE EDGE IS FEATHERED AND DECONTAMINATED. A soft matte leaves paper-coloured
    fringe in the semi-transparent pixels, which over a dark night scene reads as a
    glowing outline. Un-premultiplying the fitted paper out of those pixels
    (C_fg = (C - (1-a)*bg) / a) removes it, and a sub-pixel blur plus a small alpha
    bias pulls the cut a hair inside the linework.

 5. THE CROP RUNS TO THE WAIST, AND THE BOX HIDES THE REST. The user asked for
    chest-up framing, but the framing the player sees is the crop MINUS whatever the
    dialogue box covers, and the box covers the bottom third. So the cut is made at the
    waist and the visible portrait is chest-up — which is also the forgiving direction
    to be wrong in, because a bottom edge that is never seen cannot be seen to be wrong.
    The unit is SHOULDER WIDTH (see chest_crop): row-count alone cannot find a head on
    a character whose hair is as wide as her shoulders.

VERIFY OVER A BUSY SCREENSHOT, NEVER OVER FLAT COLOUR. A matte with a paper halo looks
perfect on white and terrible on a night street; --report composites every cut-in over
a real baked plate at docs/qa/cutins/index.html for exactly that reason.

Writes public/assets/characters/cutins.json — the runtime manifest dialogue.js reads to
know, without a probe, which speakers have cut-in art and which fall back to the
thumbnail.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, 'public/assets/characters')
MANIFEST = os.path.join(CHARS, 'cutins.json')
QA = os.path.join(ROOT, 'docs/qa/cutins')

RING = 14           # px of border the paper's own statistics are read from
GR_MIN = 16.0       # local-range floor, in levels — the barrier the flood cannot cross
DS = 4              # the flood runs at 1/DS scale; 4 px of paper drift per step
CEPS = 0.0065       # chromaticity a single flood step may drift
LEPS = 7.0          # luminance levels a single flood step may drift
LO_SIG, HI_SIG = 2.2, 5.5
LO_MIN, HI_MIN = 7.0, 20.0
BAND = 7            # px of erode/dilate around the segmentation, where alpha is soft
WAIST_PER_SHOULDER = 1.30   # shoulder-widths from the crown down to the waist
CUT_MIN_F, CUT_MAX_F = 0.45, 0.82   # ...clamped to this share of the figure's height
SIDE_MARGIN = 0.035
MIN_H = 600         # the runtime gate: a cut-in shorter than this is upscaled

# Framing overrides, each earned by looking at the QA sheet: the crop as a share
# of the figure's own height, for silhouettes the shoulder rule cannot read.
OVERRIDE = {
    'mochi': 1.0,      # a cat — no shoulder line to find, keep the whole animal
    'boat': 1.0,       # not a person at all
    'postcrow': 1.0,
}


# ----------------------------------------------------------------- the matte
def poly_basis(h, w, deg):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    x = (xx / w) - .5
    y = (yy / h) - .5
    terms = [x ** i * y ** j for d in range(deg + 1) for i in range(d + 1)
             for j in [d - i]]
    return np.stack(terms, axis=-1)


def fit_paper(rgb, mask, deg=4):
    """Per-channel polynomial surface fitted over `mask` (the pixels believed to be
    paper). Interpolation, not extrapolation — see the header, step 3."""
    h, w, _ = rgb.shape
    basis = poly_basis(h, w, deg)
    idx = np.flatnonzero(mask.ravel())
    if len(idx) > 120000:                            # subsample: the fit is smooth
        idx = idx[:: len(idx) // 120000 + 1]
    A = basis.reshape(-1, basis.shape[-1])[idx]
    model = np.empty_like(rgb)
    resid = []
    for c in range(3):
        col = rgb[..., c].ravel()[idx]
        coef, *_ = np.linalg.lstsq(A, col, rcond=None)
        model[..., c] = basis @ coef
        resid.append(col - (A @ coef))
    return model, float(np.std(np.stack(resid)))


def local_range(gray):
    """max - min over a 3x3 — the paper has almost none, linework has plenty."""
    im = Image.fromarray(gray.astype(np.uint8))
    hi = np.asarray(im.filter(ImageFilter.MaxFilter(3)), dtype=np.float64)
    lo = np.asarray(im.filter(ImageFilter.MinFilter(3)), dtype=np.float64)
    return hi - lo


def morph(mask, px, grow):
    """Erode (grow=False) or dilate (grow=True) a boolean mask by `px`."""
    k = 2 * px + 1
    im = Image.fromarray((mask * 255).astype(np.uint8))
    f = ImageFilter.MaxFilter(k) if grow else ImageFilter.MinFilter(k)
    return np.asarray(im.filter(f)) > 127


def flood_local(cand, chrom, gray, ceps, leps, iters=400):
    """Grow the background out from the border ONE STEP AT A TIME, admitting a
    pixel only if it matches the neighbour that reached it.

    A global key cannot work on these plates. Hobb's paper runs (216,175,127) at
    the corners and (180,130,89) in the middle: as it darkens it also SATURATES,
    so its chromaticity drifts 0.034 — further than the whole threshold budget —
    and any single reference colour either keeps the vignette or eats the coat.
    A step-wise flood has no global reference to be wrong about. It follows a
    gradient of any shape as far as the gradient stays smooth, and stops where
    the picture actually steps: at the silhouette. `cand` (low local range) is the
    hard barrier — linework — and ceps/leps are how much drift one step may carry.
    """
    h, w = cand.shape
    reach = np.zeros((h, w), bool)
    reach[0, :] = cand[0, :]
    reach[-1, :] = cand[-1, :]
    reach[:, 0] = cand[:, 0]
    reach[:, -1] = cand[:, -1]
    if not reach.any():
        return reach

    def step(arr, dy, dx):
        """arr shifted so that out[p] holds arr[p + (dy,dx)] (the neighbour)."""
        o = np.zeros_like(arr)
        ys = slice(max(0, dy), h + min(0, dy))
        yd = slice(max(0, -dy), h + min(0, -dy))
        xs = slice(max(0, dx), w + min(0, dx))
        xd = slice(max(0, -dx), w + min(0, -dx))
        o[yd, xd] = arr[ys, xs]
        return o

    for _ in range(iters):
        grew = False
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = step(reach, dy, dx)
            if not nb.any():
                continue
            dc = np.abs(chrom - step(chrom, dy, dx)).sum(axis=-1)
            dl = np.abs(gray - step(gray, dy, dx))
            new = nb & cand & (dc < ceps) & (dl < leps) & ~reach
            if new.any():
                reach |= new
                grew = True
        if not grew:
            break
    return reach


def box_down(a, n):
    """Mean-pool a 2-D or 3-D array by n. Averaging kills the paper grain, which
    is what lets the step tolerances be tight."""
    h, w = a.shape[:2]
    h -= h % n
    w -= w % n
    a = a[:h, :w]
    sh = (h // n, n, w // n, n) + a.shape[2:]
    return a.reshape(sh).mean(axis=(1, 3))


def max_down(a, n):
    """Max-pool — used on the barrier so a one-pixel line still blocks."""
    h, w = a.shape
    h -= h % n
    w -= w % n
    return a[:h, :w].reshape(h // n, n, w // n, n).max(axis=(1, 3))


def matte(im):
    """RGB PIL image -> (RGBA float array, diagnostics dict)."""
    rgb = np.asarray(im.convert('RGB'), dtype=np.float64)
    h, w, _ = rgb.shape
    gray = rgb.mean(axis=-1)

    # --- 1. paper-likeness: hue, not brightness, plus smoothness ---------
    tot = rgb.sum(axis=-1) + 1e-6
    chrom = np.stack([rgb[..., 0] / tot, rgb[..., 1] / tot], axis=-1)
    gr = local_range(gray)

    ring = np.zeros((h, w), bool)
    ring[:RING, :] = ring[-RING:, :] = True
    ring[:, :RING] = ring[:, -RING:] = True
    # The art runs off the edge on some plates (Odessa's hair, Pip's stick), so
    # the ring's own statistics are read at percentiles, not means.
    gr_hi = max(GR_MIN, float(np.percentile(gr[ring], 97)) * 1.5)

    # The flood runs at 1/DS scale. Mean-pooling the colour removes the paper's
    # grain (the tolerances below are then measuring the picture, not the medium);
    # max-pooling the local range keeps every line as a barrier at full strength.
    cs = box_down(chrom, DS)
    gs = box_down(gray, DS)
    bar = max_down(gr, DS) < gr_hi
    reach = flood_local(bar, cs, gs, CEPS, LEPS)
    outside = np.repeat(np.repeat(reach, DS, 0), DS, 1)
    if outside.shape != (h, w):                      # non-multiple sizes
        outside = np.asarray(Image.fromarray(outside.astype(np.uint8) * 255)
                             .resize((w, h), Image.NEAREST)) > 127
    if outside.mean() < 0.06:                        # nothing keyed — refuse rather than lie
        return None, {'error': 'no background found', 'gr_hi': round(gr_hi, 1),
                      'keyed': round(float(outside.mean()), 3)}

    # --- 2. the paper surface, fitted from the paper we just found -------
    fit_mask = morph(outside, 3, False)              # keep the fit off the silhouette
    if fit_mask.sum() < 5000:
        fit_mask = outside
    paper, sig = fit_paper(rgb, fit_mask)

    # --- 3. soft alpha, in a band around the segmentation ----------------
    delta = np.sqrt(((rgb - paper) ** 2).sum(axis=-1) / 3.0)
    lo = max(LO_MIN, LO_SIG * sig)
    hi = max(HI_MIN, HI_SIG * sig, lo + 6.0)
    ramp = np.clip((delta - lo) / (hi - lo), 0.0, 1.0)

    solid = ~outside
    a = np.where(morph(solid, BAND, False), 1.0,
                 np.where(morph(solid, BAND, True), ramp, 0.0))

    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float64) / 255.0
    a = np.clip((a - 0.10) / 0.86, 0.0, 1.0)

    # --- 4. colour decontamination on the semi-transparent band ----------
    soft = (a > 0.02) & (a < 0.985)
    out = rgb.copy()
    if soft.any():
        aa = a[soft][:, None]
        out[soft] = np.clip((rgb[soft] - (1.0 - aa) * paper[soft]) / np.maximum(aa, 0.08), 0, 255)

    return np.dstack([out, a * 255.0]), {
        'sigma': round(sig, 2), 'gr_hi': round(gr_hi, 1),
        'coverage': round(float((a > 0.5).mean()), 3)}


# ------------------------------------------------------------------ the crop
def chest_crop(a, cid):
    """Alpha (HxW, 0..255 float) -> (l, t, r, b) chest-up box, or None."""
    h, w = a.shape
    solid = a > 128
    rows = solid.sum(axis=1)
    cols = solid.sum(axis=0)
    if rows.max() < 8:
        return None
    ys = np.flatnonzero(rows >= 6)
    top, bot = int(ys[0]), int(ys[-1])
    figh = bot - top
    if figh < 40:
        return None

    ov = OVERRIDE.get(cid)
    if ov is not None:
        cut = top + int(round(figh * ov))
    else:
        # SHOULDER WIDTH IS THE UNIT. Row-count alone cannot find a head — Maren's
        # hair is as wide at the crown as her shoulders are, so "first row at 62%
        # of maximum" put the cut through her chin. The widest row of the upper
        # figure IS the shoulder line's width, and human proportion ties it to
        # vertical distance: shoulders span about 1.9 head-heights, crown to waist
        # about 2.5, so ~1.30 shoulder-widths below the crown is the waist. The
        # clamp catches the two silhouettes that break the proportion — Hobb, whose
        # arms are out and reads 0.9 x figure-height wide, and any plate framed
        # closer or wider than the cast's norm.
        wsh = int(rows[top:top + max(8, int(figh * 0.6))].max())
        cut = top + int(round(WAIST_PER_SHOULDER * wsh))
    cut = int(np.clip(cut, top + int(figh * CUT_MIN_F), top + int(figh * CUT_MAX_F)))
    cut = int(min(cut, bot))

    band = solid[top:cut + 1]
    xs = np.flatnonzero(band.any(axis=0))
    if not len(xs):
        xs = np.flatnonzero(cols > 0)
    m = int(round(w * SIDE_MARGIN))
    l = max(0, int(xs[0]) - m)
    r = min(w, int(xs[-1]) + 1 + m)
    t = max(0, top - int(round(h * 0.02)))
    return l, t, r, cut + 1


def make_cutin(src, dst, cid):
    im = Image.open(src)
    rgba, diag = matte(im)
    if rgba is None:
        return None, diag
    box = chest_crop(rgba[..., 3], cid)
    if box is None:
        return None, dict(diag, error='no silhouette')
    l, t, r, b = box
    cut = Image.fromarray(rgba.astype(np.uint8), 'RGBA').crop((l, t, r, b))
    if cut.height < MIN_H:
        s = MIN_H / cut.height
        cut = cut.resize((max(1, int(round(cut.width * s))), MIN_H), Image.LANCZOS)
    # A fully transparent pixel still carries RGB nobody will ever see, and the
    # matte leaves a different unseen colour in every one of them — noise, which
    # is the one thing PNG cannot compress. Flattening the invisible half of the
    # image to black takes ~36% off the file (Hobb: 1729 KB -> 1105 KB) and
    # changes not one visible pixel. Partial alpha is left alone: its colour is
    # the decontaminated edge and it is very much on screen.
    px = np.asarray(cut).copy()
    gone = px[..., 3] == 0
    px[gone, 0] = px[gone, 1] = px[gone, 2] = 0
    cut = Image.fromarray(px, 'RGBA')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    cut.save(dst, optimize=True, compress_level=9)
    return cut, dict(diag, w=cut.width, h=cut.height, box=[l, t, r, b])


# ------------------------------------------------------------------ QA sheet
def busy_plate():
    """A real baked background to composite over — a matte is only honest against
    the scene it will actually be drawn on."""
    for rel in ('public/world/scenes', 'public/assets/scenes', 'public/world'):
        base = os.path.join(ROOT, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, _, names in os.walk(base):
            for n in sorted(names):
                if n == 'bg.png' or n.endswith('_bg.png'):
                    return os.path.join(dirpath, n)
    return None


def report(ids):
    os.makedirs(QA, exist_ok=True)
    plate_path = busy_plate()
    plate = Image.open(plate_path).convert('RGB') if plate_path else None
    rows = []
    for cid in ids:
        p = os.path.join(CHARS, cid, 'cutin.png')
        if not os.path.exists(p):
            continue
        art = Image.open(p).convert('RGBA')
        H = 420
        art = art.resize((max(1, int(art.width * H / art.height)), H), Image.LANCZOS)
        W = art.width + 60
        if plate:
            sc = max(W / plate.width, H / plate.height)
            bgc = plate.resize((int(plate.width * sc) + 1, int(plate.height * sc) + 1), Image.LANCZOS)
            bgc = bgc.crop((0, bgc.height - H, W, bgc.height))
        else:
            bgc = Image.new('RGB', (W, H), (24, 26, 40))
        bgc = bgc.convert('RGBA')
        bgc.alpha_composite(art, (30, 0))
        out = os.path.join(QA, cid + '.png')
        bgc.convert('RGB').save(out)
        rows.append((cid, os.path.basename(out)))
    with open(os.path.join(QA, 'index.html'), 'w') as f:
        f.write('<meta charset=utf-8><title>cut-in matte QA</title>'
                '<style>body{background:#11131c;color:#cbd;font:13px system-ui;margin:18px}'
                'figure{display:inline-block;margin:0 10px 14px 0}img{display:block;border:1px solid #333}'
                'figcaption{padding:3px 1px}</style>'
                '<h1>cut-in mattes over a baked plate</h1><p>plate: %s</p>' % (plate_path or 'none'))
        for cid, fn in rows:
            f.write('<figure><img src="%s"><figcaption>%s</figcaption></figure>' % (fn, cid))
    print('QA sheet: docs/qa/cutins/index.html  (%d)' % len(rows))


# ---------------------------------------------------------------------- main
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    only_report = '--report' in sys.argv

    ids = args or sorted(d for d in os.listdir(CHARS)
                         if os.path.isfile(os.path.join(CHARS, d, 'bust.png')))
    if only_report:
        return report(ids)

    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    for cid in ids:
        d = os.path.join(CHARS, cid)
        src = os.path.join(d, 'bust.png')
        if not os.path.exists(src):
            print('%-16s SKIP  no bust.png' % cid)
            continue
        dst = os.path.join(d, 'cutin.png')
        if os.path.exists(dst) and not force:
            print('%-16s keep' % cid)
            continue
        cut, diag = make_cutin(src, dst, cid)
        if cut is None:
            print('%-16s FAIL  %s' % (cid, diag))
            man.pop(cid, None)
            continue
        exprs = []
        for n in sorted(os.listdir(d)):
            if not (n.startswith('expr-') and n.endswith('.png')):
                continue
            mood = n[5:-4]
            e, _ = make_cutin(os.path.join(d, n), os.path.join(d, 'cutin-%s.png' % mood), cid)
            if e is not None:
                exprs.append(mood)
        man[cid] = {'h': cut.height, 'w': cut.width}
        if exprs:
            man[cid]['expr'] = exprs
        print('%-16s %4dx%-4d cover %.3f sigma %.2f  %s' %
              (cid, cut.width, cut.height, diag['coverage'], diag['sigma'],
               ('expr: ' + ','.join(exprs)) if exprs else ''))

    with open(MANIFEST, 'w') as f:
        json.dump(man, f, indent=1, sort_keys=True)
    print('\nmanifest: public/assets/characters/cutins.json  (%d cut-ins)' % len(man))


if __name__ == '__main__':
    main()
