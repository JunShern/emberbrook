#!/usr/bin/env python3
"""gen-cutin.py — MAT THE PORTRAIT ART INTO CUT-IN PLATES.

    python3 tools/gen-cutin.py                 # every character with source art
    python3 tools/gen-cutin.py odessa maren    # just these
    python3 tools/gen-cutin.py --force         # re-mat art that already has a cutin
    python3 tools/gen-cutin.py --no-gate       # promote regardless of the edge metric
    python3 tools/gen-cutin.py --report        # write the QA contact sheets, mat nothing
    python3 tools/gen-cutin.py maren --picks rest=2,happy=1   # ship picked pose rolls

WHAT THIS IS FOR. The user ruled the modern cut-in grammar on 2026-08-01: the character
art rises OUT of the dialogue box with no frame and no background, chest-up, overlaid on
the scene. That needs an ALPHA CUTOUT and a CHEST-UP CROP.

TWO SOURCES, AND THE SECOND ONE IS THE PLAN NOW. This file first tried to SALVAGE the
cut-out from bust.png — 1024x1024 plates on warm toned paper with a radial glow behind
the figure, drawn to sit inside a frame. That works, and the salvage path below is a
genuinely careful piece of work, but the user looked at the result and ruled it the
wrong approach: "we should explicitly regenerate the images with the cut-in in mind...
very amenable to the background being masked out." The measurement agrees. On the 62
salvaged plates, tools/cutin_edge.py fails 43 — mostly on a +15 to +67 level bright
paper fringe, which is the toned paper surviving in the feather and reading as a glow
over a night street. No matte can be crisp against a background that has no edge in it.

So tools/gen-cutin-art.mjs now draws each portrait ON A FLAT KEY, and this file prefers
that art wherever it exists:

    studio/rest.png       ->  cutin.png          (chroma key — matte_key)
    studio/<mood>.png     ->  cutin-<mood>.png   (chroma key)
    bust.png              ->  cutin.png          (salvage — matte, the fallback)
    expr-<m>.png          ->  cutin-<m>.png      (salvage)

bust.png AND expr-*.png STAY, UNTOUCHED. The save menu, the shop plate and every other
.eb-port consumer still want a square framed thumbnail, and dialogue.js falls back to
exactly that for any speaker this tool could not mat. cutin.png is ADDITIVE.

THE ROLLOUT IS PER CHARACTER AND GATED. A regenerated plate replaces the shipped one
only when it passes tools/cutin_edge.py's gate; a plate that fails is discarded and the
character keeps today's file, so a bad roll can never regress a face that already works.
The new matte is written to a staging path, measured there, and promoted only on a pass
— which also means an interrupted run cannot leave half a cast swapped.

HOW THE SALVAGE MATTE WORKS, and why each step is there:

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
import shutil
import sys

import numpy as np
from PIL import Image, ImageFilter

from cutin_edge import (measure, grade_edges, grade_framing, line as edge_line,
                        HEAD as EDGE_HEAD)

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


# ------------------------------------------------- the matte, on a flat key
# Everything above is the salvage path and stays as the fallback. This is the path
# the regenerated art takes, and it is short for the reason the regeneration
# happened: when the background is one colour with a drawn edge against it, the
# matte is a distance and a threshold, and every clever step the salvage needs
# (step-wise flood, fitted quartic paper, seven-pixel soft band) exists only to
# cope with a background that has no edge in it.
KEY_RING = 10        # px of border the key colour's first estimate is read from
KEY_LO_MIN = 9.0     # RGB distance from the key surface at which alpha starts to rise
KEY_SPAN = 0.80      # ...share of the LOCAL character-to-key contrast that reaches 1.0
KEY_LOCAL = 10       # px radius that local contrast is measured over
KEY_BIAS = 0.07      # pulls the cut a hair inside the drawn outline
KEY_BAND = 2         # px either side of the cut the ramp may live in — the user's band
KEY_MAX_SIG = 9.0    # a "flat" key noisier than this at the ring is not a key
EXPECT_KEY = (255, 0, 255)   # the colour gen-cutin-art.mjs asks the model for
KEY_FIND_R = 165.0   # how far a RENDERED key may drift from it and still be the key.
                     # Measured, not guessed: across 138 plates the rendered magenta
                     # sits 114-138 from pure #FF00FF (Odessa 114, Poppy 135, the
                     # armorer 138), while the plates that IGNORED the key and came
                     # back on paper sit at 220-237. 165 separates them with room on
                     # both sides, and skin — the nearest real colour — is past 210.
KEY_BORDER_TOL = 45.0  # ...and how far the border may sit from the key before the
                       # plate is framed rather than keyed
KEY_RESIDUE_R = 40.0   # a surviving pixel this close to the key is background
KEY_RESIDUE_MAX = 0.0008  # ...and essentially none of them may survive. Not exactly
                       # zero: a handful of anti-aliased pixels on a magenta-adjacent
                       # trim can land inside the radius honestly. Sorrel's sticker
                       # read 0.68 against it.
KEY_SIGN_F = 0.35      # ...and this is the SAME RULE ON A BETTER AXIS. See keyness().


def keyness(rgb, key):
    """How much a pixel carries the KEY'S OWN CHANNEL SIGNATURE, in levels.

    RGB DISTANCE IS THE WRONG AXIS FOR BLOOMED KEY, and Maren's base is the
    measurement that says so (2026-08-02, the user's "her magenta cutout is quite
    messy"). Her residue sat 60-150 levels from the key — far outside
    KEY_RESIDUE_R's 40 — and fully OPAQUE 2-6 px inside the cut, so neither the
    residue rule nor the band despill could reach it. A scanline through the worst
    of it settles what it is: figure at distance ~200, a three-pixel spike at 88-93,
    figure again at ~190. Character on both sides of it — a strand gap the border
    flood cannot enter (flood_reach's min-pool only closes channels under 2 px) and
    whose trapped key has BLOOMED too far for a radius tuned to unbloomed key. The
    file's own header already predicted this failure ("bloomed key trapped in hair
    strand-gaps, 12 to 40 levels off pure"); the radius simply stops short of how
    far the bloom actually goes.

    Widening the RADIUS is the wrong repair: at 150 levels it would start eating
    real paint on a warm palette. The bloom's signature is not its distance but its
    CHANNEL ORDER — a magenta key holds R and B far above G, and no amount of
    blooming reorders the channels. So: the key's high channels minus its low ones,
    the weakest such pair, which is high only when EVERY key channel relationship
    holds. Skin and cream raise R and G together; a rose raises R and B unequally;
    only key colour raises the key's own channels together.

    MEASURED SEPARATION, keyness as a fraction of the key's own, over the deep
    interior (>=6 px inside the cut) of three plates chosen as the hard cases —
    Vesper (whose dusty-rose scarf is the cast's nearest miss to magenta), Maren
    (the defect), and Lake (whose RENDERED key drifted to #DA2A9D, the closest any
    plate's key gets to skin):

        paint tops out at   +0.05 (vesper, maren) / +0.10 (lake)
        then a flat tail of tens of pixels — the bloom ramp itself
        then a spike at     +0.95..+1.05 — trapped key, 3200-10800 px on Vesper

    The valley between +0.10 and +0.85 is empty on all three, so anything in the
    range is a choice about MARGIN, not about which pixels are key. It was swept
    (0.25/0.30/0.35/0.40/0.50) rather than picked, because the two characters pull
    in opposite directions and only the sweep shows where the knee is:

        Maren  happy-3 residue 127 px (0.50) -> 89 (0.40) -> 8 (0.35), then FLAT
               below 0.35. Her defect is entirely inside one step of the sweep.
        Lake   residue does not move at all across the whole range (37 -> 34 px);
               only his edge_noise does, climbing 0.073 -> 0.103 -> 0.126 on his
               worst plate (tender-1) as the threshold falls 0.50 -> 0.35 -> 0.25.
        Vesper flat on every number, at every setting.

    0.35 is where Maren's curve bottoms out and Lake's worst plate still holds
    0.103 against a 0.120 gate. His climb is an instrument artifact and the
    composite says so: his cut at 0.35 and his cut with the term OFF are
    indistinguishable at 1:1 over a night plate. Cutting a thin coherent run of
    bloom leaves soft pixels the sub-pixel blur refills to just under opaque, and
    edge_noise counts exactly those. Real, invisible, and the honest cost of
    removing something that IS visible.

    AND IT RESCUES PLATES, which is the part that settles it. Two of Lake's thirty
    pose rolls FAIL the edge gate outright without this term (sad-3 edge_noise
    0.446 / ramp 4.34, weary-3 0.320 / 4.10 / speckle 0.0080) because a broad
    bloom around the figure was being kept as character — 18k and 29k pixels of
    it. With the term on they read 0.068 and 0.090 and pass. The metric that
    looked like a cost on his clean plates is the same metric recording a real
    repair on his dirty ones.
    """
    key = np.asarray(key, float)
    hi = key >= 0.4 * key.max()          # magenta -> R,B; green -> G
    lo = ~hi
    if not hi.any() or not lo.any():     # a grey "key" has no signature to measure
        return np.zeros(rgb.shape[:2]), 1.0
    diffs = [rgb[..., h] - rgb[..., l] for h in np.flatnonzero(hi)
             for l in np.flatnonzero(lo)]
    kd = [key[h] - key[l] for h in np.flatnonzero(hi) for l in np.flatnonzero(lo)]
    return np.minimum.reduce(diffs), float(min(kd))


def local_max(a, r):
    """Max over a (2r+1) square. The alpha ramp's denominator — how far from the
    key the CHARACTER gets, here — has to be a local quantity."""
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1)), dtype=np.float64)


CRUMB_MAX_F = 0.0025   # a solid island smaller than this share of the figure is a crumb


def drop_crumbs(solid, frac=CRUMB_MAX_F):
    """Delete solid islands far too small to be the character.

    WHY, MEASURED (2026-08-02, Lake's re-roll). His ratified bust is drawn on toned
    paper with DARKENED CORNERS, and 9 of 13 rolls reproduced that darkening as a
    grey-tan smear bleeding a few pixels into the top-left corner of the key. It
    survives the matte as a detached island of 50-600 px — 0.0001-0.0006 of the
    figure, an order of magnitude under `speckle`'s 0.004 gate, so nothing refused
    it — and it lands ABOVE THE CROWN. `framing()` reads the head as the median row
    width over the figure's top 12%, and a crumb 60 rows above the hair fills that
    window with empty rows: head_frac collapsed from 0.26 to 0.05 and the plate was
    refused as "framed below the waist" on 7 straight rolls of a correctly framed
    portrait. Naming the corner in the prompt did not fix it (4 more rolls, same
    smear) — the same lesson this pipeline keeps paying for: prose does not reach
    what the reference image dictates.

    So it is removed where it is created rather than measured downstream. This is
    not a gate written around: the crumb is background that survived the key, it
    would have rendered as a dot floating beside the character's head in a dialogue
    box, and deleting it makes `speckle` read zero because the defect is GONE.

    THE THRESHOLD IS DELIBERATELY FAR BELOW ANYTHING REAL. 0.25% of the figure is a
    ~35x35 px blob on a 1024 plate; the smallest thing a portrait legitimately
    detaches — a flyaway lock, a gap-separated fingertip — is larger, and every
    crumb measured on this cast was under 0.06%. Islands are counted on the same
    1/2-scale max-pool `flood_reach` uses, so a strand one pixel wide still binds
    its own island to the body rather than being counted as loose."""
    ds = 2
    h, w = solid.shape
    hh, ww = h - h % ds, w - w % ds
    m = solid[:hh, :ww].reshape(hh // ds, ds, ww // ds, ds).max(axis=(1, 3))
    if not m.any():
        return solid
    rest = m.copy()
    keep = np.zeros_like(m)
    total = int(m.sum())
    biggest = 0
    while rest.any():
        ys, xs = np.nonzero(rest)
        cur = np.zeros_like(m)
        cur[ys[0], xs[0]] = True
        n = 1
        for _ in range(20000):
            nxt = cur.copy()
            nxt[1:, :] |= cur[:-1, :]
            nxt[:-1, :] |= cur[1:, :]
            nxt[:, 1:] |= cur[:, :-1]
            nxt[:, :-1] |= cur[:, 1:]
            cur = nxt & rest
            c = int(cur.sum())
            if c == n:
                break
            n = c
        rest = rest & ~cur
        if n > biggest:
            biggest = n
        if n > frac * total:
            keep |= cur
    if keep.sum() == total:
        return solid
    up = np.repeat(np.repeat(keep, ds, 0), ds, 1)
    out = np.zeros_like(solid)
    out[:up.shape[0], :up.shape[1]] = up
    # Rows/cols lost to the pooling remainder keep whatever they had; they are at
    # the far edge of the plate, which the crop throws away anyway.
    out[hh:, :] = solid[hh:, :]
    out[:, ww:] = solid[:, ww:]
    return out & solid


def matte_key(im):
    """RGB PIL image on a flat key -> (RGBA float array, diagnostics dict).

    THE KEY IS A FITTED SURFACE, NOT A COLOUR, and that is the whole lesson of this
    function. The border ring's median is only the FIRST estimate: the model draws a
    key that is flat at the corners and BLOOMS a little where it meets the figure,
    and against a single global colour those bloom pixels read as "not background",
    survive as a fully-opaque magenta rim, and put a glowing pink outline around the
    character over a night street. That was visible to the eye on Lake's second roll
    while every threshold in the file said the plate was clean. So the ring median
    only classifies a confident background; a quartic surface is then fitted over
    THOSE pixels and every distance below is measured against the surface. It is the
    salvage path's step 3 arriving at the same conclusion from the other direction —
    a background is a field, not a value — and it is cheap here because the field is
    nearly constant and the fit is interpolation over 40% of the frame.

    ALPHA IS A NORMALISED DISTANCE. A fixed upper threshold is wrong for the same
    reason: a pixel 57 levels from the key is nearly opaque against a pale collar and
    barely a quarter covered against a dark cape, because coverage is distance
    divided by HOW FAR THE CHARACTER IS FROM THE KEY THERE. That denominator is
    measured per pixel as a local maximum, which is what makes one ramp constant
    work for a whole cast.

    CONNECTIVITY DECIDES WHAT IS BACKGROUND, distance only decides how hard the
    edge is. A character may legitimately wear the key's colour — and on a magenta
    key, Vesper's dusty-rose scarf is the near miss — so a low-distance pixel is
    background ONLY if it is connected to the border. That single rule is what
    makes pinholes structurally impossible rather than merely rare."""
    rgb = np.asarray(im.convert('RGB'), dtype=np.float64)
    h, w, _ = rgb.shape

    # THE KEY IS FOUND BY COLOUR, AND THEN CHECKED AT THE BORDER. Reading it off the
    # border ring alone is what broke on Sorrel's `happy`: the model drew the portrait
    # as a STICKER — a magenta rectangle with a white outline, sitting on a white page
    # — so the ring was WHITE, the matte keyed white, and the magenta rectangle
    # survived as 81% of an opaque "figure". Every geometric metric passed it, because
    # a rectangle has excellent edges. Two rules close that hole. First, the key is
    # the median of the pixels near the colour the prompt ASKED for, which is a fact
    # this pipeline owns and does not have to infer. Second, that key must actually
    # reach the border: if it does not, the plate is framed, matted or inset, the
    # character may well extend past the key's own rectangle, and there is nothing
    # honest to do but refuse it and re-roll.
    keymass = np.sqrt(((rgb - np.array(EXPECT_KEY, float)) ** 2).sum(axis=-1)) < KEY_FIND_R
    if keymass.mean() < 0.05:
        return None, {'error': 'no key colour in the plate',
                      'keymass': round(float(keymass.mean()), 3)}
    key0 = np.median(rgb[keymass], axis=0)

    ring = np.zeros((h, w), bool)
    ring[:KEY_RING, :] = ring[-KEY_RING:, :] = True
    ring[:, :KEY_RING] = ring[:, -KEY_RING:] = True
    ringcol = np.median(rgb[ring], axis=0)
    if float(np.sqrt(((ringcol - key0) ** 2).sum())) > KEY_BORDER_TOL:
        return None, {'error': 'key does not reach the border (framed/sticker plate)',
                      'key': [round(float(c)) for c in key0],
                      'border': [round(float(c)) for c in ringcol]}
    sig0 = float(np.median(np.abs(rgb[ring] - key0)) * 1.4826)   # robust sigma
    if sig0 > KEY_MAX_SIG:
        return None, {'error': 'background is not a flat key',
                      'key': [round(float(c)) for c in key0], 'sigma': round(sig0, 1)}

    # 1. confident background: near the first estimate AND reachable from the border
    d0 = np.sqrt(((rgb - key0) ** 2).sum(axis=-1))
    bg = flood_reach(d0 < max(16.0, 4.0 * sig0))
    if bg.mean() < 0.04:
        return None, {'error': 'no background found', 'key': [round(float(c)) for c in key0],
                      'keyed': round(float(bg.mean()), 3)}

    # 2. the key SURFACE, fitted over that background only — interpolation, and the
    #    erode keeps the fit off the figure's anti-aliased edge.
    fit_mask = morph(bg, 3, False)
    if fit_mask.sum() < 5000:
        fit_mask = bg
    keyf, ksig = fit_paper(rgb, fit_mask)
    d = np.sqrt(((rgb - keyf) ** 2).sum(axis=-1))

    # 3. WHAT IS BACKGROUND is a connectivity question, decided ONCE, on a hard
    #    threshold against the fitted surface. Fitting the surface first is what
    #    makes a fixed threshold safe again: the bloom that defeated a single global
    #    key colour has been absorbed into the model, so what is left to threshold
    #    is genuinely flat. A patch of key colour the flood cannot reach is enclosed
    #    by the drawing and belongs to the character.
    lo = max(KEY_LO_MIN, 3.0 * ksig)
    # CONNECTIVITY, PLUS A STRICT COLOUR TEST, and the second half is not redundant.
    # flood_reach closes any channel narrower than its pooling step, which is the
    # forgiving direction for a gap between an arm and a torso and exactly the WRONG
    # one for HAIR: hair is made of narrow channels, the key shows through every one
    # of them, and closing them keeps the key. On the first full run that put visible
    # magenta blobs in Lake's, Maren's and Rowan's hair — plates the gate correctly
    # refused, and the reason it had to. So a pixel is also background if it is
    # simply THE KEY COLOUR, connected or not. Nothing in this cast can trip it:
    # the strict radius is a few levels of noise wide, and the nearest miss in the
    # whole town — Vesper's dusty-rose scarf — sits over a hundred levels away.
    # `strict` in the diagnostics reports how much was taken this way, so a future
    # character who really does wear the key shows up as a number, not a hole.
    #
    # MEASURED AGAINST key0, NOT THE FITTED SURFACE, and this cost a whole run to
    # learn. `keyf` is a quartic fitted over BACKGROUND pixels; inside the figure it
    # extrapolates, and a quartic extrapolating across a large interior swings far
    # enough to pass within 12 levels of real character colours. Using it here
    # punched holes through the middle of seven characters — weaponsmith lost 4% of
    # his own area — and every one survived a two-pixel erosion, so they were
    # punctures and not strand-gaps. This is the salvage path's own warning ("a
    # bulge that lives in the MIDDLE is extrapolation from the edge") arriving in a
    # new place. The ring median is a constant and cannot swing; the bloom it cannot
    # follow is what the fitted surface and the looser connectivity test are for.
    # THE STRICT RADIUS IS THE RESIDUE RADIUS, and that identity is the argument.
    # At 12 levels, bloomed key trapped in hair strand-gaps — 12 to 40 levels off
    # pure, enclosed so no flood reaches it — survived as figure and failed the
    # residue gate on 8 of 10 Vesper mood rolls (keyres 0.0012-0.0166, top-of-head
    # heat map), unfixable by re-rolling because every roll blooms somewhere. The
    # residue gate already rules that NO visible pixel may sit within KEY_RESIDUE_R
    # of the key, so classifying exactly those pixels as background cannot delete
    # anything a passing plate was allowed to keep. Still measured against key0,
    # the constant — the fitted surface stays banned here (see below: it once
    # punched holes in seven characters).
    # THE SIGNATURE TERM sits beside the radius rather than replacing it, because
    # the two catch different things: the radius catches unbloomed key wherever it
    # is, and keyness catches key that has bloomed past any radius a warm palette
    # would tolerate. Both are "this pixel is background", decided on colour alone,
    # and both are safe for the same reason — the character does not wear the key.
    kn, kn_key = keyness(rgb, key0)
    strict = (d0 < max(KEY_RESIDUE_R, 5.0 * sig0)) | (kn > KEY_SIGN_F * kn_key)
    bgm = flood_reach(d < max(18.0, 6.0 * ksig)) | strict
    if bgm.mean() < 0.04:
        return None, {'error': 'nothing keyed', 'keyed': round(float(bgm.mean()), 3)}
    solid = ~bgm
    solid = drop_crumbs(solid)

    # 4. THE RAMP LIVES IN THE BAND AND NOWHERE ELSE. Alpha is opaque inside the
    #    silhouette, zero outside it, and a normalised distance only in the few
    #    pixels either side of the cut. Letting the ramp apply everywhere — which
    #    the first version did — put partial alpha on 300,000 INTERIOR pixels of
    #    Odessa's coat, because a mid-tone patch sits well below the local maximum
    #    distance and the formula cannot tell "half covered" from "a different
    #    shade of brown". Coverage is only a meaningful question at an edge.
    #
    #    A consequence worth stating plainly, because it bears on how the gate
    #    should be read: edge_noise is now near zero on key-matted plates BY
    #    CONSTRUCTION. It keeps its full discriminating power over the salvage
    #    plates it was calibrated on, and it still catches a band that breaks, but
    #    a passing edge_noise on a regenerated plate is not evidence of anything by
    #    itself — `halo`, the QA composite and the eye are what judge those.
    edge = solid & ~morph(solid, 1, False)
    band = morph(edge, KEY_BAND, True)
    span = np.maximum(local_max(d, KEY_LOCAL) * KEY_SPAN, lo + 25.0)
    ramp = np.clip((d - lo) / (span - lo), 0.0, 1.0)
    a = np.where(band, ramp, solid.astype(np.float64))

    # A hair of erosion pulls the cut inside the drawn outline, so no pixel of the
    # key survives as a rim. The blur is sub-pixel: it softens the staircase on a
    # diagonal without widening the ramp past the 2 px the gate allows.
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float64) / 255.0
    a = np.clip((a - KEY_BIAS) / (1.0 - KEY_BIAS), 0.0, 1.0)

    # UN-PREMULTIPLY the key surface out of the semi-transparent band. Exact to the
    # pixel now that the background is a field: C_fg = (C - (1-a)*key)/a. The alpha
    # floor stops a 3%-opaque pixel from having its own rounding error multiplied
    # by thirty.
    soft = (a > 0.02) & (a < 0.985)
    out = rgb.copy()
    if soft.any():
        aa = a[soft][:, None]
        out[soft] = np.clip((rgb[soft] - (1.0 - aa) * keyf[soft]) / np.maximum(aa, 0.18), 0, 255)
    key = key0
    sig = ksig

    # BAND DESPILL, TOWARD THE LOCAL FIGURE COLOUR (2026-08-02; user flag on
    # Maren's picked base: "her magenta cutout is quite messy" — pink haze through
    # the wispy hair edges and around the headband, worst in the flyaway strands).
    # SCOPE IS THE WHOLE ARGUMENT. A GLOBAL despill stays refuted for solid pixels
    # (measured: clamping R and B to G traded a magenta cast for a red one, Lake
    # 32.2 -> 34.4, and the rim it chased was painted, not spilled). But the RAMP
    # BAND is different: the un-premultiply above divides by max(alpha, 0.18), so a
    # 5%-opaque wisp pixel keeps ~70% of the key it should have surrendered — real
    # residue, in exactly the pixels fine hair produces. Dark flyaway hair is the
    # worst case: the wisp is thinner than a pixel, the key shows through it, and
    # the leftover reads as pink haze over a night plate. The fix is the SAME
    # un-premultiply arithmetic run once more with a LOCAL reference: estimate each
    # band pixel's remaining key share from how far its two key channels (R and B,
    # for magenta) still sit above the nearby OPAQUE figure's own colour, and unmix
    # exactly that share of key0 back out. A wisp already the colour of the hair
    # beside it measures share zero and moves nowhere; the share is capped so the
    # division cannot explode on a pixel that is genuinely mostly key.
    if soft.any():
        sol = a >= 0.985
        if sol.any():
            def _boxf(arr, r=8):
                # separable box mean via cumsum — Pillow's BoxBlur refuses mode-F
                # images on this machine, and uint8 would quantise the weights.
                def run(a2, axis):
                    c = np.cumsum(a2, axis=axis, dtype=np.float64)
                    n = a2.shape[axis]
                    pad = np.zeros_like(a2)
                    hi = np.minimum(np.arange(n) + r, n - 1)
                    lo = np.arange(n) - r - 1
                    if axis == 0:
                        top = c[hi, :]
                        bot = np.where(lo[:, None] >= 0, c[np.maximum(lo, 0), :], 0.0)
                        return (top - bot) / (hi - np.maximum(lo, -1))[:, None]
                    top = c[:, hi]
                    bot = np.where(lo[None, :] >= 0, c[:, np.maximum(lo, 0)], 0.0)
                    return (top - bot) / (hi - np.maximum(lo, -1))[None, :]
                return run(run(arr.astype(np.float64), 0), 1)
            wgt = _boxf(sol.astype(np.float64))
            ref = np.dstack([_boxf(out[..., c] * sol) for c in range(3)])
            ref = ref / np.maximum(wgt, 1e-4)[..., None]
            have_ref = wgt > 0.02
            den = ((key[0] - ref[..., 0]) + (key[2] - ref[..., 2]))
            num = ((out[..., 0] - ref[..., 0]) + (out[..., 2] - ref[..., 2]))
            share = np.where((den > 60.0) & have_ref & soft,
                             np.clip(num / np.maximum(den, 1e-4), 0.0, 0.65), 0.0)
            sh = share[..., None]
            out = np.where(sh > 0.01,
                           np.clip((out - sh * np.array(key, float)) / (1.0 - sh), 0, 255),
                           out)

            # A SUB-PIXEL WISP'S COLOUR IS THE HAIR BESIDE IT, not whatever survives
            # dividing by its own alpha (2026-08-02, Maren's shipped `happy` at 1:1
            # over a night plate). Her flyaway strands are thinner than a pixel, so
            # every pixel along one is a genuine key/hair mix; the un-premultiply
            # divides by max(alpha, 0.18), and at alpha ~0.3 that is a 3.3x
            # amplification of every error in the key estimate. The result is
            # visible and it is TWO-COLOURED: the strand comes out magenta on the
            # side that kept too much key and NEON CHARTREUSE on the side that lost
            # too much, because subtracting more magenta than was there drives R and
            # B below G. 150 such pixels on that one plate, still readable as
            # coloured filaments after the downscale to CUTIN_MAX_PX.
            #
            # No better estimate of the key share exists for these pixels — but a
            # better estimate of the ANSWER does. The strand is hair; the opaque
            # figure a few pixels away is that same hair at full coverage; `ref` is
            # already that colour. So the un-premultiply is trusted in proportion to
            # the alpha it had to divide by, and the remainder is taken from the
            # neighbourhood. At alpha >= 0.68 nothing changes at all, which is where
            # every ordinary anti-aliased edge lives; the blend only bites on the
            # thin, low-alpha pixels whose arithmetic was never going to be reliable.
            # It is the same argument the salvage path makes for its fitted paper
            # model — an estimate from the picture beats an extrapolation — applied
            # to the figure instead of the background.
            w = np.clip((a - 0.18) / 0.50, 0.0, 1.0)[..., None]
            blend = soft & have_ref
            out = np.where(blend[..., None], w * out + (1.0 - w) * ref, out)

    # BEYOND THE BAND THERE IS STILL NO DESPILL STEP, and that remains a measured
    # decision rather than an omission. The global version was written — the classic
    # green-screen rule generalised from the measured key, clamping the key's two
    # strong channels down to its weak one — because the first bake-off plates
    # showed a coloured rim. It made the metric worse (Lake 32.2 -> 34.4) and it did
    # so for a good reason: subtracting an equal amount from R and B leaves a red
    # cast where it removed a magenta one, so it trades one wrong colour for
    # another. Then the rim was scanned pixel by pixel and turned out not to be key
    # spill at all — five opaque pixels of (218,177,144) around a grey cape, a PALE
    # RIM THE MODEL PAINTED, reproducing the reference plate's paper glow as a halo
    # on the figure rather than discarding it. No colour arithmetic fixes that; the
    # prompt has to stop it being drawn, and cutin_edge.py's `halo` is the gate that
    # refuses the plate when it is. The un-premultiply above is exact for a correct
    # alpha; the band despill exists only for the alpha floor's own residue.
    # KEY RESIDUE — the check that would have caught the sticker on its own, and the
    # only one here that does not care how TIDY the surviving background is. After
    # matting, essentially no visible pixel may still be the key colour. A geometric
    # metric cannot see this failure: Sorrel's sticker matted to an edge_noise of
    # 0.039 and a speckle of 0.0000 because a rectangle has excellent edges, and it
    # was 81% magenta. Reported here, gated in roll_character.
    vis = a > 0.02
    res = vis & (np.sqrt(((out - key0) ** 2).sum(axis=-1)) < KEY_RESIDUE_R)
    # ENCLOSED KEY ISLANDS ARE CUT, NOT JUST COUNTED (2026-08-01, pose-matrix
    # review): the model sometimes draws a closed shape — a laugh-puff over the
    # head, a gap ringed by hair — and fills it with the key. The border flood
    # can never reach inside a closed outline, so the key survives as an opaque
    # magenta patch. Any visible pixel still within KEY_RESIDUE_R of the key IS
    # background by the residue gate's own definition, so it is made transparent
    # here; keyres still reports the pre-cut fraction so the diagnostic keeps its
    # meaning as "how much the model tried to trap".
    a = np.where(res, 0.0, a)
    return np.dstack([out, a * 255.0]), {
        'key': [round(float(c)) for c in key], 'sigma': round(sig, 2),
        'keyres': round(float(res.sum() / max(1, int(vis.sum()))), 5),
        'coverage': round(float((a > 0.5).mean()), 3), 'src': 'key'}


def flood_reach(mask):
    """Everything in `mask` reachable from the image border, 4-connected. Runs on a
    1/DS-scale MIN-pool, so a channel narrower than DS px (a gap between an arm and
    a torso that the key does squeeze through) closes and the enclosed side stays
    with the character — the forgiving direction, since a false hole is a visible
    puncture and a false solid is a few pixels of background nobody can see."""
    ds = 2
    h, w = mask.shape
    hh, ww = h - h % ds, w - w % ds
    m = mask[:hh, :ww].reshape(hh // ds, ds, ww // ds, ds).min(axis=(1, 3))
    cur = np.zeros_like(m)
    cur[0, :] = m[0, :]
    cur[-1, :] = m[-1, :]
    cur[:, 0] = m[:, 0]
    cur[:, -1] = m[:, -1]
    n = int(cur.sum())
    for _ in range(20000):
        nxt = cur.copy()
        nxt[1:, :] |= cur[:-1, :]
        nxt[:-1, :] |= cur[1:, :]
        nxt[:, 1:] |= cur[:, :-1]
        nxt[:, :-1] |= cur[:, 1:]
        cur = nxt & m
        c = int(cur.sum())
        if c == n:
            break
        n = c
    up = np.repeat(np.repeat(cur, ds, 0), ds, 1)
    out = np.zeros_like(mask)
    out[:up.shape[0], :up.shape[1]] = up
    return out & mask


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


def silhouette_crop(a):
    """(l, t, r, b) around everything opaque, plus a small side margin.

    THE CROP THE STUDIO PLATES GET, and the reason it is this short next to
    chest_crop: those plates were DRAWN to the cut-in framing, so the composition
    is already the answer and re-deriving a waist line from shoulder widths would
    only be a chance to get it wrong. All that is left is to throw away the keyed
    border."""
    h, w = a.shape
    solid = a > 128
    rows, cols = solid.sum(axis=1), solid.sum(axis=0)
    if rows.max() < 8:
        return None
    ys = np.flatnonzero(rows >= 6)
    xs = np.flatnonzero(cols >= 6)
    if not len(ys) or not len(xs) or ys[-1] - ys[0] < 40:
        return None
    top, bot = int(ys[0]), int(ys[-1])

    # TRIM A FADING BOTTOM. The prompt tells the model the figure is cut off cleanly
    # by the frame and several plates do it anyway: the chest dissolves into the key
    # over the last few dozen rows, which mattes into a wide veil of partial alpha —
    # the single commonest defect in this batch, and the one that reads as a glow
    # under the dialogue box. Rows are dropped from the bottom while more than a
    # fifth of the figure's width in that row is semi-transparent. It costs nothing
    # to be generous here: CUTIN_SINK hides the bottom 55% of this crop behind the
    # window, so a row trimmed is a row the player was never going to see.
    soft = (a > 10) & (a <= 128)
    while bot > top + 40:
        span = int(solid[bot].sum()) + int(soft[bot].sum())
        if span and int(soft[bot].sum()) / span > 0.20:
            bot -= 1
        else:
            break

    # STRAIGHT CUT AT THE WAIST (user ruling 2026-08-01, Vesper review): the art
    # meets the dialogue box in a clean horizontal slice, not a rounded bust taper.
    # The prompt now asks for the slice, and this enforces it when the model tapers
    # anyway: rows are dropped from the bottom while they are narrower than 85% of
    # the lower torso's own width, so the final bottom row cuts opaque torso at
    # close to full width. Budget-capped at 12% of the figure — a taper deeper than
    # that is not a crop problem but a framing defect, and it is left standing for
    # cutin_edge.py's `bot_cut` gate to refuse with a named reason.
    # The trim threshold is 0.90, ABOVE the gate's 0.80, so a plate lands with
    # margin rather than on the line: at 0.85 four passing Vesper plates sat at
    # 0.87-0.90 against the gate's 0.80; at 0.90 the same art measures 0.92-0.94.
    # It is NOT a rescue for a real taper — Vesper's second `determined` (791 px
    # narrowing to 509 over the figure's last stretch) measured 0.75 under both
    # settings, because trimming also lifts the lower-quarter median the tail is
    # judged against. A taper that deep is the model's framing defect, and it stays
    # a named refusal. Every trimmed row is one CUTIN_SINK was going to hide anyway.
    rw = solid[top:bot + 1].sum(axis=1)
    torso = float(np.median(rw[int(len(rw) * 0.75):])) if len(rw) > 40 else 0.0
    floor_ = top + int((bot - top) * 0.88)
    while torso and bot > floor_ and solid[bot].sum() < 0.90 * torso:
        bot -= 1

    m = int(round(w * SIDE_MARGIN))
    band = solid[top:bot + 1]
    bx = np.flatnonzero(band.any(axis=0))
    if not len(bx):
        bx = xs
    # THREE TRANSPARENT ROWS STAY BELOW THE CUT (2026-08-02, measured on Rowan's
    # new-identity base). The band ramp legitimately leaves partial alpha in the
    # 2 px band around the WAIST CUT — a mid-distance palette (his rust vest) ramps
    # to ~0.86 where a dark coat clips to 1.0 — and a crop that ends exactly on the
    # last solid row amputates the boundary those pixels hug: cutin_edge's band is
    # built from boundaries it can SEE, so the same pixels read as off-band noise
    # (edge_noise 0.140 on a plate whose cut is clean; 0.000 with the rows kept).
    # Three invisible rows cost nothing — CUTIN_SINK hides the bottom 55% — and
    # they keep the instrument honest about a boundary that really is there.
    return (max(0, int(bx[0]) - m), max(0, top - int(round(h * 0.015))),
            min(w, int(bx[-1]) + 1 + m), min(h, bot + 4))


def make_cutin(src, dst, cid, key=False):
    im = Image.open(src)
    rgba, diag = (matte_key if key else matte)(im)
    if rgba is None:
        return None, diag
    box = silhouette_crop(rgba[..., 3]) if key else chest_crop(rgba[..., 3], cid)
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


def over_plate(art, plate, H=340):
    """One cut-in composited over a real baked background at display height."""
    art = art.resize((max(1, int(art.width * H / art.height)), H), Image.LANCZOS)
    W = art.width + 44
    if plate:
        sc = max(W / plate.width, H / plate.height)
        bgc = plate.resize((int(plate.width * sc) + 1, int(plate.height * sc) + 1), Image.LANCZOS)
        bgc = bgc.crop((0, bgc.height - H, W, bgc.height))
    else:
        bgc = Image.new('RGB', (W, H), (24, 26, 40))
    bgc = bgc.convert('RGBA')
    bgc.alpha_composite(art, (22, 0))
    return bgc.convert('RGB')


def report(ids):
    """THE BOARD, and it now shows every mood rather than one face per character.

    A neutral-only sheet was right when a character had a neutral and maybe three
    moods salvaged from art drawn for another purpose. After the emotive pass a
    character has up to eight plates that all have to be THE SAME PERSON, and the
    thing most worth looking at is a row of them side by side: identity drift is
    invisible in one plate and obvious in a row. Each plate carries its own metric
    line, so a number and the thing it describes are never in two different files."""
    os.makedirs(QA, exist_ok=True)
    for n in os.listdir(QA):
        if n.endswith('.png'):
            os.remove(os.path.join(QA, n))
    plate_path = busy_plate()
    plate = Image.open(plate_path).convert('RGB') if plate_path else None
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}

    body, nplate = [], 0
    for cid in ids:
        d = os.path.join(CHARS, cid)
        if not os.path.exists(os.path.join(d, 'cutin.png')):
            continue
        moods = [None] + sorted((man.get(cid) or {}).get('expr', []))
        src = 'studio' if os.path.isdir(os.path.join(d, 'studio')) else 'salvage'
        body.append('<h2>%s <span class=k>%s &middot; %d plate%s</span></h2><div class=row>'
                    % (cid, src, len(moods), '' if len(moods) == 1 else 's'))
        for mood in moods:
            p = os.path.join(d, cutin_name(mood))
            if not os.path.exists(p):
                continue
            fn = '%s%s.png' % (cid, '' if mood is None else '-' + mood)
            over_plate(Image.open(p).convert('RGBA'), plate).save(os.path.join(QA, fn))
            nplate += 1
            m = measure(p)
            good, why = grade_edges(m)
            body.append(
                '<figure><img src="%s"><figcaption><b>%s</b><br>'
                '<span class="%s">%s</span><br><span class=k>edge %.3f &middot; ramp %.2f'
                ' &middot; halo %+.1f &middot; speckle %.4f</span></figcaption></figure>'
                % (fn, mood or 'rest', 'ok' if good else 'bad',
                   'PASS' if good else 'FAIL ' + '; '.join(why),
                   m['edge_noise'], m['ramp_px'], m['halo'], m['speckle']))
        body.append('</div>')

    with open(os.path.join(QA, 'index.html'), 'w') as f:
        f.write(
            '<meta charset=utf-8><title>cut-in matte QA</title>'
            '<style>body{background:#11131c;color:#cbd;font:13px/1.5 system-ui;margin:18px}'
            'h1{font-size:19px}h2{font-size:15px;margin:22px 0 6px;'
            'border-top:1px solid #2a2d3c;padding-top:12px}'
            '.row{display:flex;flex-wrap:wrap;gap:10px}'
            'figure{margin:0}img{display:block;border:1px solid #333}'
            'figcaption{padding:4px 1px;font-size:11px}'
            '.k{color:#6a7085}.ok{color:#7fd18d}.bad{color:#e08a7a}'
            'p{max-width:76ch}</style>'
            '<h1>cut-in mattes, composited over a baked plate</h1>'
            '<p class=k>Every plate the runtime can show, over %s. A matte with a halo '
            'looks perfect on white and terrible on a night street, so this is the only '
            'honest place to judge one. Metrics are tools/cutin_edge.py; the gate is '
            'edge_noise&le;0.12, halo&le;+18, ramp&le;3.5&nbsp;px, speckle&le;0.004, '
            'pinhole&le;0.004. One row is one character &mdash; read it ACROSS for '
            'identity drift, which is invisible in a single plate and obvious in a row.'
            '</p>' % (plate_path or 'no plate found'))
        f.write(''.join(body))
    print('QA sheet: docs/qa/cutins/index.html  (%d plates)' % nplate)


# ------------------------------------------------------------- the rollout
STAGE = '.staged'


def studio_sources(cid):
    """[(mood_or_None, path)] of regenerated flat-key art for this character.

    ONLY NAMES THE SPEC KNOWS. studio/ accumulates working plates whose names are
    not moods — rest-cand1.png from a base pick, rest-clean2.png from a re-roll,
    rest-outpaint-fierce.png from a recipe trial — and the first version of this
    function took every png in the directory. Vesper's studio holds six such files
    today, so a plain run on her would have matted, gated and SHIPPED a portrait
    called cutin-rest-cand1.png that dialogue.js can never ask for and the manifest
    would advertise. A latent bug rather than a shipped one only because her suite
    was matted from the pose plates by hand. The spec is the list of moods that
    exist; anything else in studio/ is workings."""
    d = os.path.join(CHARS, cid, 'studio')
    if not os.path.isdir(d):
        return []
    known = spec_moods(cid)
    out = []
    for n in sorted(os.listdir(d)):
        if not n.endswith('.png'):
            continue
        mood = None if n == 'rest.png' else n[:-4]
        if mood is not None and known and mood not in known:
            continue
        out.append((mood, os.path.join(d, n)))
    return sorted(out, key=lambda t: (t[0] is not None, t[0] or ''))


def pose_sources(cid, picks):
    """[(mood_or_None, path)] for a set of USER-PICKED pose rolls.

    The pose matrix (tools/gen-cutin-poses.mjs) rolls three takes per expression
    into studio/poses/<mood>-<n>.png and puts them on a picker page; a pick is
    therefore a mood-to-roll-number map and nothing else. Shipping one is the same
    gated, atomic, floor-checked promotion every other source gets — which is the
    whole reason this returns a source list instead of copying files around."""
    d = os.path.join(CHARS, cid, 'studio', 'poses')
    out = []
    for mood, n in picks.items():
        p = os.path.join(d, '%s-%d.png' % (mood, n))
        if not os.path.exists(p):
            raise SystemExit('no such pose roll: ' + p)
        out.append((None if mood == 'rest' else mood, p))
    return sorted(out, key=lambda t: (t[0] is not None, t[0] or ''))


def salvage_sources(cid):
    """[(mood_or_None, path)] of the old bust/expression art — the fallback."""
    d = os.path.join(CHARS, cid)
    out = []
    if os.path.exists(os.path.join(d, 'bust.png')):
        out.append((None, os.path.join(d, 'bust.png')))
    for n in sorted(os.listdir(d)):
        if n.startswith('expr-') and n.endswith('.png'):
            out.append((n[5:-4], os.path.join(d, n)))
    return out


def cutin_name(mood):
    return 'cutin.png' if mood is None else 'cutin-%s.png' % mood


SPEC = os.path.join(ROOT, 'tools/characters/cutins.spec.json')
_SPEC = None


def spec_doc():
    """The whole emotional-coverage spec, cached."""
    global _SPEC
    if _SPEC is None:
        _SPEC = json.load(open(SPEC)) if os.path.exists(SPEC) else {'characters': {}}
    return _SPEC


def spec_entry(cid):
    """This character's row of the emotional-coverage spec, or None."""
    return spec_doc().get('characters', {}).get(cid)


def spec_moods(cid):
    """Every mood name this character is ENTITLED to, the tiered way.

    THE MERGE LIVES IN TWO LANGUAGES AND THEY HAD DRIFTED (2026-08-02, Lake's
    re-roll). cutins.spec.json states a character's moods in two halves: its own
    `moods` overrides, plus the shared `moodDefaults` grammar, which
    gen-cutin-art.mjs hands out by tier — the full set to `mainCharacters`, and to
    everyone else only the moods their dialogue actually uses. This file read the
    RAW `moods` block alone, so the defaults were invisible to it: Lake's studio
    held wry.png, thinking.png and annoyed.png, drawn by the JS from exactly this
    spec, and studio_sources() discarded all three as workings. The floor then
    refused the whole set for "would lose annoyed,thinking,wry" — a set that had
    every one of them on disk and passing. It never bit before only because his
    suite last shipped through --picks, which bypasses this filter entirely.

    So the tier rule is stated here in the same terms the JS states it, and
    `usedMoods` gets its second half too: a mood is "used" if a line asks for it OR
    the character already ships a plate of it."""
    ent = spec_entry(cid) or {}
    own = set(ent.get('moods') or {})
    doc = spec_doc()
    defaults = {k for k in (doc.get('moodDefaults') or {}) if k != '_doc'}
    if cid in set(doc.get('mainCharacters') or []):
        return own | defaults
    used = set(scripted_moods().get(cid, set()))
    d = os.path.join(CHARS, cid)
    if os.path.isdir(d):
        used |= {n[6:-4] for n in os.listdir(d)
                 if n.startswith('cutin-') and n.endswith('.png')}
    return own | (defaults & used)


def scripted_moods():
    """portrait id -> set of moods public/game/dialogue.json actually asks a line to
    wear. These are the moods with a CONSUMER; losing one is a scripted beat quietly
    demoting itself to the neutral plate."""
    path = os.path.join(ROOT, 'public/game/dialogue.json')
    if not os.path.exists(path):
        return {}
    D = json.load(open(path))
    sp = D.get('speakers', {})

    def pid_of(s):
        e = sp.get(s)
        return e.get('portrait', s) if e and 'portrait' in e else s

    out = {}
    for n in D.get('nodes', {}).values():
        for l in n.get('lines') or []:
            if isinstance(l, dict) and (l.get('expr') or n.get('expr')):
                p = pid_of(l.get('speaker') or n.get('speaker'))
                if p:
                    out.setdefault(p, set()).add(l.get('expr') or n.get('expr'))
        if n.get('expr') and n.get('speaker'):
            out.setdefault(pid_of(n['speaker']), set()).add(n['expr'])
    return out


def required_moods(cid, man, scripted):
    """The moods this character MUST still have afterwards.

    THE NO-REGRESSION RULE, and it is the reason the first full run had to be thrown
    away. That run replaced 26 of 28 characters and, in doing so, silently dropped
    maren's `awed` and `determined`, pip's and poppy's and rowan's `happy` — every
    one of them a mood a shipped line asks for by name. Each of those lines would
    still have drawn something, so nothing would have failed; the portrait would
    simply have stopped changing, which is precisely the invisible regression this
    lane exists to prevent. So the union of what the script asks for and what the
    character already ships is a FLOOR, and a set that cannot clear it is not an
    upgrade no matter how good its neutral looks."""
    return set(scripted.get(cid, set())) | set((man.get(cid) or {}).get('expr', []))


def roll_character(cid, man, gate=True, force=False, verbose=True, scripted=None,
                   srcs=None):
    """Mat one character and, if it earns it, swap the shipped plates for the new
    ones. Returns a row for the coverage table.

    ATOMIC PER CHARACTER, and that is the whole design. The obvious rule — promote
    each plate that passes — produces a character whose neutral is a regenerated
    studio portrait and whose 'worried' is still a salvaged bust, and those two
    plates do not share a framing, a crop or an edge. A player watching one
    conversation would see the face change SHAPE on a mood change, which is worse
    than either plate is on its own. So the REST plate is the whole decision: if it
    fails, nothing about this character moves and the old set stands untouched; if
    it passes, the character goes over to the studio set wholesale, and a mood that
    fails its own gate is simply dropped — dialogue.js falls back to the new
    neutral, which at least belongs to the same drawing."""
    d = os.path.join(CHARS, cid)
    if srcs is not None:                       # an explicit list (picked pose rolls)
        src_kind = 'picks'
    else:
        studio = studio_sources(cid)
        src_kind = 'studio' if studio else 'salvage'
        srcs = studio or salvage_sources(cid)
    if not srcs or srcs[0][0] is not None:
        return {'id': cid, 'action': 'skip', 'why': 'no neutral source art'}

    have = man.get(cid)
    if have and not force and src_kind == 'salvage':
        return {'id': cid, 'action': 'keep', 'why': 'already matted, no studio art'}

    stage = os.path.join(d, STAGE)
    os.makedirs(stage, exist_ok=True)
    rows, kept_moods, dropped = [], [], []
    neutral = None
    for mood, src in srcs:
        dst = os.path.join(stage, cutin_name(mood))
        cut, diag = make_cutin(src, dst, cid, key=(src_kind != 'salvage'))
        if cut is None:
            (dropped if mood else rows).append((mood, None, diag.get('error', 'matte failed')))
            if mood is None:
                shutil.rmtree(stage, ignore_errors=True)
                return {'id': cid, 'action': 'keep', 'src': src_kind,
                        'why': 'neutral: ' + str(diag.get('error', 'matte failed'))}
            continue
        m = measure(dst)
        good, why = grade_edges(m)
        # THE KEY-RESIDUE GATE, and it is deliberately a separate question from the
        # geometry. grade_edges asks "is this edge clean"; this asks "is the
        # background actually GONE". Sorrel's sticker answered the first question
        # beautifully and the second one not at all, and only the second one would
        # have stopped a pink rectangle reaching a dialogue box.
        kr = diag.get('keyres')
        if kr is not None and kr > KEY_RESIDUE_MAX:
            good = False
            why = list(why) + ['key residue %.4f > %.4f (background survived the matte)'
                               % (kr, KEY_RESIDUE_MAX)]
        # THE FRAMING GATE, third and independent. Edge quality asks "is the cut
        # clean", key residue asks "is the background gone", this asks "is this the
        # same picture as everyone else's". All three before a file touches a live
        # path — the user's ruling is that the drift IS the defect.
        # The neutral is graded on the absolute band (base=None: it IS the base);
        # every mood is then graded against the neutral's own metrics — the user's
        # ruling that the reference plate dictates the set's framing, made a gate.
        fok, fwhy = grade_framing(m, base=neutral,
                                  own_framing=bool((spec_entry(cid) or {}).get('framing')))
        if not fok:
            good = False
            why = list(why) + fwhy
        rows.append((mood, m, None if good else '; '.join(why)))
        if mood is None:
            if gate and not good:
                shutil.rmtree(stage, ignore_errors=True)
                return {'id': cid, 'action': 'keep', 'src': src_kind, 'metrics': m,
                        'why': 'neutral fails: ' + '; '.join(why)}
            neutral = m
        elif gate and not good:
            dropped.append(mood)
            os.remove(dst)
        else:
            kept_moods.append(mood)

    # THE FLOOR. Checked before anything is promoted, and checked against the moods
    # that SURVIVED the gate rather than the ones that were drawn.
    need = required_moods(cid, man, scripted or {})
    missing = sorted(need - set(kept_moods))
    if gate and missing:
        shutil.rmtree(stage, ignore_errors=True)
        return {'id': cid, 'action': 'keep', 'src': src_kind, 'metrics': neutral,
                'why': 'would lose ' + ','.join(missing),
                'regen': sorted(kept_moods)}

    # PROMOTE. Every old cutin*.png goes first, so a mood the new set does not have
    # cannot survive as a stale plate from the previous drawing.
    for n in os.listdir(d):
        if n == 'cutin.png' or (n.startswith('cutin-') and n.endswith('.png')):
            os.remove(os.path.join(d, n))
    for n in sorted(os.listdir(stage)):
        shutil.move(os.path.join(stage, n), os.path.join(d, n))
    shutil.rmtree(stage, ignore_errors=True)

    man[cid] = {'h': neutral['h'], 'w': neutral['w']}
    if kept_moods:
        man[cid]['expr'] = sorted(kept_moods)
    # `flip` travels from the spec into the manifest because the manifest is
    # regenerated on every run and a hand-edit there would not survive one. It tells
    # dialogue.js it may mirror this plate to face inward when the character is
    # anchored on the right; it is OFF unless somebody looked at that face and
    # decided its asymmetries survive a mirror (Lake's flame pin, Vesper's satchel
    # strap and Odessa's whistle cord are all canon and all one-sided).
    if (spec_entry(cid) or {}).get('flip'):
        man[cid]['flip'] = True
    row = {'id': cid, 'action': 'replace', 'src': src_kind, 'metrics': neutral,
           'moods': sorted(kept_moods), 'dropped': sorted(m for m in dropped if m),
           'rows': rows}
    if verbose:
        print(edge_line('%s/cutin' % cid, neutral))
        for mood, m, bad in rows:
            if mood is None:
                continue
            print('  ' + (edge_line('%s/cutin-%s' % (cid, mood), m) if m
                          else '%-28s   —  %s' % ('%s/cutin-%s' % (cid, mood), bad)))
    return row


# ---------------------------------------------------------------------- main
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    gate = '--no-gate' not in sys.argv
    only_report = '--report' in sys.argv

    # SHIP A SET OF PICKED POSE ROLLS:
    #     python3 tools/gen-cutin.py maren --picks rest=2,happy=1,awed=3
    # The picks ARE the authoring decision and nothing else is; everything after
    # them — matte, three gates, the no-regression floor, the atomic promotion,
    # the manifest — is the same path every other source takes. Re-runnable by
    # design: overriding one pick in the morning is one changed number and one
    # command, and a pick that would lose a scripted mood is still refused.
    if '--picks' in sys.argv:
        cid = args[0]
        raw = sys.argv[sys.argv.index('--picks') + 1]
        picks = {}
        for tok in raw.split(','):
            k, _, v = tok.partition('=')
            picks[k.strip()] = int(v)
        man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
        print(EDGE_HEAD)
        r = roll_character(cid, man, gate=gate, force=True, scripted=scripted_moods(),
                           srcs=pose_sources(cid, picks))
        with open(MANIFEST, 'w') as f:
            json.dump(man, f, indent=1, sort_keys=True)
        print('\n%s: %s  %s' % (cid, r['action'],
                                ','.join(r.get('moods', [])) or r.get('why', '')))
        if r.get('dropped'):
            print('  dropped: ' + ','.join(r['dropped']))
        return 0 if r['action'] == 'replace' else 1

    ids = args or sorted(d for d in os.listdir(CHARS)
                         if os.path.isdir(os.path.join(CHARS, d))
                         and (os.path.isfile(os.path.join(CHARS, d, 'bust.png'))
                              or os.path.isdir(os.path.join(CHARS, d, 'studio'))))
    if only_report:
        return report(ids)

    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    scripted = scripted_moods()
    print(EDGE_HEAD)
    table = []
    for cid in ids:
        table.append(roll_character(cid, man, gate=gate, force=force, scripted=scripted))

    with open(MANIFEST, 'w') as f:
        json.dump(man, f, indent=1, sort_keys=True)

    print('\n' + '-' * 78)
    print('%-16s %-9s %-8s %s' % ('character', 'action', 'source', 'moods'))
    rep = kep = 0
    for r in table:
        if r['action'] == 'replace':
            rep += 1
            note = ','.join(r['moods']) or '(neutral only)'
            if r['dropped']:
                note += '   dropped: ' + ','.join(r['dropped'])
        else:
            kep += 1
            note = r.get('why', '')
            if r.get('regen'):
                note += '   (regen passed: ' + ','.join(r['regen']) + ')'
        print('%-16s %-9s %-8s %s' % (r['id'], r['action'], r.get('src', '-'), note))
    print('\n%d replaced, %d kept · manifest: public/assets/characters/cutins.json (%d)'
          % (rep, kep, len(man)))


if __name__ == '__main__':
    sys.exit(main() or 0)
