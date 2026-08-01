#!/usr/bin/env python3
"""cutin_edge.py — THE EDGE-QUALITY INSTRUMENT for cut-in mattes.

    python3 tools/cutin_edge.py                       # every cutin*.png under characters/
    python3 tools/cutin_edge.py odessa hobb           # just these characters
    python3 tools/cutin_edge.py --json path.png ...   # machine-readable, arbitrary files

WHY THIS FILE EXISTS. dialogue_test.mjs §2b already proves a cut-in is an 8-bit RGBA
PNG whose alpha does work (not all-clear, not all-opaque). That gate cannot tell a
crisp silhouette from a mushy one: a matte with a seven-pixel feather, a speckled
halo and paper-coloured fringe passes it exactly as cleanly as a razor cut. The user
looked at the salvage mattes on 2026-08-01 and saw the difference the gate could not,
and ruled the art be REGENERATED for the matte. A ruling about edges needs an
instrument that measures edges, so that "the new plate is better" is a number and not
a taste, and so that per-character rollout has something to be gated on.

WHAT IS MEASURED, and why each number is the one it is:

  edge_noise  THE PRIMARY. Of every pixel with intermediate alpha, the fraction
              lying FURTHER THAN 2 PX from the alpha=0.5 boundary. A matte cut on a
              flat key needs one pixel of feather to stop aliasing, so its soft
              pixels all hug the boundary and this runs near zero. Soft alpha found
              far from any boundary is not anti-aliasing — it is a partially-keyed
              background (a halo, a glow, a gradient the key could not follow), and
              a halo is precisely what reads as a glowing outline over a night
              street. The 2 px band is the user's own wording of the gate.
  ramp_px     soft pixels per boundary pixel — the mean thickness of the alpha ramp,
              in pixels. Reported because it is the honest confound to read
              edge_noise against: a wide-but-tidy feather and a noisy speckled one
              can share an edge_noise, never a ramp_px.
  speckle     solid pixels NOT connected to the main figure, as a share of the
              figure. Detached crumbs of background that survived the key.
  pinhole     enclosed transparent components inside the figure, same share.
              DIAGNOSTIC, NOT GATED — and it was gated at first, wrongly, which is
              worth recording. It was meant to catch the key eating a piece of the
              character. What it actually catches on correctly-keyed art is the gap
              under an akimbo arm and the holes in a loose curl of hair: background
              that IS enclosed by the silhouette and SHOULD be transparent. It read
              4.2% on the weaponsmith and 1.0% on Vesper, whose plates are both
              pristine on inspection, and it read ~0 on the salvage mattes only
              because those filled every such gap in solid — the metric was
              rewarding the bug. A key that truly ate a character shows up in
              `coverage` and on the QA board.
  halo        THE OTHER GATE: how much brighter the figure's outer 3 px are than its
              own material 4-10 px in, in luminance levels. Signed, gated ONE-SIDED.
              A silhouette normally ends in linework, so a clean plate is near zero
              or negative, and a POSITIVE number means a pale ring around the
              character — which is the defect the user actually saw. It catches two
              different causes with one measurement: the salvage matte's toned paper
              surviving in the feather (Odessa +30.9, Lake +52.4), and a regenerated
              plate on which the model PAINTED a bright rim onto the figure instead
              of discarding the reference's glow (Lake's first studio roll, +28.6 —
              a five-pixel opaque band of (218,177,144) around a grey cape).
              Negative is not gated: dark linework is how these portraits are drawn.

              WHAT IT IS MEASURED ON MATTERS, and two earlier drafts are worth
              recording as wrong. Measured over the SEMI-TRANSPARENT BAND ONLY, it
              misses a painted rim entirely — that rim is fully opaque and never
              enters the band. Measured as a CHROMATICITY distance, it blows up on
              dark linework, where dividing by a small sum makes noise look like
              colour, and it ranked a clean plate worse than a filthy one. The
              shell-versus-core form is stable because both samples are the same
              kind of thing: material of the drawing, a few pixels apart.
  rough       boundary length over the perimeter of a disc of the same area. Pure
              diagnostic, NOT gated: a character with flyaway hair is legitimately
              rougher than one in a hood, and a gate on this would be a gate on
              hairstyle.

THE GATE (grade_edges): edge_noise <= 0.12, halo <= +18 levels, ramp_px <= 3.5,
speckle <= 0.004. `pinhole` and `rough` are reported, not gated.
The thresholds were set by measuring the salvage
mattes FIRST (see docs/qa/DAYLOG.md, cut-in regeneration) so that "pass" means
measurably better than the incumbent it would replace, rather than merely not
catastrophic — 43 of the 62 incumbents fail it, and the ones that pass are the ones
that looked right on the QA board.

NO SCIPY HERE. Connected components come from a shift-and-intersect flood in numpy —
the repo has numpy and Pillow and nothing else, and adding a dependency to count blobs
would be a poor trade. The flood runs at HALF SCALE on a max-pooled mask, which is a
measured decision and not a shortcut: PIL's MaxFilter(9) at full resolution took over
four minutes on the 62 incumbent plates and never finished, while max-pooling by two
keeps every crumb two pixels or wider (max-pool cannot erase a set pixel) and brings
the whole cast in under a minute. Sub-two-pixel specks are therefore NOT counted, and
that is the honest limit of this number.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = os.path.join(ROOT, 'public/assets/characters')

BAND_PX = 2          # the user's band: soft alpha is allowed within 2 px of the cut
SOFT_LO = 0.04       # below this a pixel is transparent, not "intermediate"
SOFT_HI = 0.96       # above this it is opaque
SHELL = 3            # px of the figure's outer edge the halo is read from
CORE_IN, CORE_OUT = 4, 10   # ...and the band of its own material it is read against

# The gate. Set from the incumbent salvage mattes' own measurements — a pass has to
# mean BETTER THAN WHAT IT REPLACES, not merely "has an alpha channel".
GATE = {
    'edge_noise': 0.12,
    # One-sided: a PALE ring is the defect, dark linework is not. +18 rather than the
    # +12 first tried, and the extra six levels were bought by looking: Odessa's clean
    # regenerated plate reads +14.1 because her silhouette really is pale — grey hair
    # and a cream gansey around a dark oilskin core — and the composite over a night
    # plate shows no ring at all. +18 still refuses every defect this lane has seen:
    # her own salvage plate (+30.9), Lake's (+52.4), and the roll where the model
    # painted a rim onto the figure (+28.6).
    'halo': 18.0,
    'ramp_px': 3.5,   # BAND_PX either side of the cut, plus the sub-pixel blur
    'speckle': 0.004,
    # no 'pinhole': see the header. An enclosed transparent region is usually the
    # picture being right, not the matte being wrong.
}


def _morph(mask, px, grow):
    """Erode (grow=False) or dilate (grow=True) a boolean mask by `px`."""
    if px <= 0:
        return mask
    k = 2 * px + 1
    im = Image.fromarray((mask * 255).astype(np.uint8))
    f = ImageFilter.MaxFilter(k) if grow else ImageFilter.MinFilter(k)
    return np.asarray(im.filter(f)) > 127


def _spread(m):
    """One step of 4-connected dilation, in numpy. Four slice-assignments beat any
    filter kernel at radius 1, and radius 1 is all a flood ever needs."""
    o = m.copy()
    o[1:, :] |= m[:-1, :]
    o[:-1, :] |= m[1:, :]
    o[:, 1:] |= m[:, :-1]
    o[:, :-1] |= m[:, 1:]
    return o


def _flood(seed, mask):
    """Everything in `mask` reachable from `seed`, 4-connected. One pixel per
    round, so the round count is the figure's geodesic diameter; at half scale
    that is a few hundred rounds of four slice-ORs, which is milliseconds."""
    cur = seed & mask
    n = int(cur.sum())
    for _ in range(20000):
        cur = _spread(cur) & mask
        m = int(cur.sum())
        if m == n:
            return cur
        n = m
    return cur


def _pool_max(m, ds):
    """Max-pool a boolean mask by `ds`. Max-pooling cannot erase a set pixel, so
    every crumb `ds` px or wider survives into the flood — which is what makes
    half-scale component counting a bounded approximation rather than a guess."""
    h, w = m.shape
    h -= h % ds
    w -= w % ds
    return m[:h, :w].reshape(h // ds, ds, w // ds, ds).max(axis=(1, 3))


def _pool_min(m, ds):
    h, w = m.shape
    h -= h % ds
    w -= w % ds
    return m[:h, :w].reshape(h // ds, ds, w // ds, ds).min(axis=(1, 3))


DS = 2                # the scale the component floods run at


def _detached(solid):
    """Share of solid pixels NOT connected to the main figure — background crumbs
    the key left behind. Seeded from the deepest interior pixel rather than from a
    centroid, because a centroid can land in the gap between an arm and a torso."""
    n = int(solid.sum())
    if n == 0:
        return 0.0
    s = _pool_max(solid, DS)
    if not s.any():
        return 0.0
    deep = s
    for px in (5, 3, 1):
        e = _morph(s, px, False)
        if e.any():
            deep = e
            break
    ys, xs = np.nonzero(deep)
    seed = np.zeros_like(s)
    seed[ys[len(ys) // 2], xs[len(xs) // 2]] = True
    main = _flood(seed, s)
    tot = int(s.sum())
    return float((tot - main.sum()) / tot) if tot else 0.0


def _pinholes(solid):
    """Share of the figure's area taken by transparent components fully enclosed
    by it — the key eating pieces out of the character. Min-pooled, so only holes
    at least DS px across are counted (the conservative direction: a hole has to
    be real to be charged)."""
    n = int(solid.sum())
    if n == 0:
        return 0.0
    s = _pool_min(solid, DS)
    empty = ~s
    if not empty.any():
        return 0.0
    border = np.zeros_like(empty)
    border[0, :] = border[-1, :] = True
    border[:, 0] = border[:, -1] = True
    outside = _flood(border & empty, empty)
    holes = int((empty & ~outside).sum())
    return float(holes / max(1, int(s.sum())))


# ------------------------------------------------------------------ framing
# THE FRAMING GATE. User ruling (2026-08-01), after browsing the gallery: every
# cut-in is framed the SAME — waist-up, crown near the top, head about a third of the
# image — and the drift the set had (shoulders-up beside waist-up beside everything
# between) IS the defect. "The gate is what makes 62+ images consistent, not care."
# CALIBRATED ON VESPER, who the rollout order names the template the rest of the cast
# is judged against. Her nine regenerated waist-up plates land at 0.208-0.241 — a
# spread of 0.033 across a laugh, a flinch and a folded-arm deadpan, which is the
# consistency the ruling is asking for. The band is that cluster with room either
# side. For contrast, the SHIPPED set it replaces runs 0.110 (Pip) to 0.394 (Odessa):
# a spread of 0.28, three times the whole tolerance, and that spread is precisely the
# drift the user named when they said a portrait system only reads as a system when
# every character sits in the frame the same way.
# RECALIBRATED 2026-08-01, second Vesper pass. Three measured facts moved the band:
# (1) the statistic ("first row 1.6x head width") is biased DOWN and only down by
# anything wide near the head — Vesper's mane read 0.208-0.241 at her HAIR line,
# Finn's hat brim read 0.129, while the same true waist-up framing on narrow slicked
# hair reads at the anatomical shoulders (Lake 0.442, Poppy 0.464, both verified
# waist-up by eye through gen-cutin.py's own matte). (2) A genuine bust reads 0.55+
# (Mara 0.661, verified head-and-shoulders by eye), and no hair morphology can push
# a tight plate DOWN into the band — the ceiling keeps full power at 0.50. (3) The
# user re-ruled the frame after rejecting the first Vesper suite: uniform waist-up
# with a STRAIGHT HORIZONTAL bottom cut, and the reference plate dictates the set's
# framing. So moods are graded against their own BASE plate (d_base), the absolute
# band is the backstop for the base itself, and `bot_cut` witnesses the straight
# frame-cut waist (a frame-sliced torso keeps its width to the last row; a bust
# taper or a pair of legs does not).
# SECOND RECALIBRATION, same day, measured on the new Vesper suite: the shoulder
# statistic is not gateable at all. Across nine plates whose framing is uniform by
# the strongest witness available (head span 234-254 px on identical 1024 canvases,
# +-4%, and the eye agrees), `shoulder` swung 0.228 -> 0.502 with hair volume and
# hand placement. It stays REPORTED for the QA board and its own history, but the
# gate now rides `head_frac` (head span / figure height), which held 0.245-0.267 on
# those same nine plates, reads 0.248-0.258 on verified waist-up Lake/Poppy, and
# 0.328 on Mara's true head-and-shoulders bust — the failure the band exists for.
# LIMIT, measured and accepted: on the REJECTED first suite, head_frac cannot
# separate the plate the user called chest-up (sad, 0.290) from its own neutral
# (0.291) — subtle within-set drift stays a QA-board-by-eye judgement; the gates
# catch the gross failures (bust base, no straight cut, severed hands, drift from
# the base beyond 0.03).
FRAME = {'head_frac': (0.18, 0.30), 'd_base': 0.03, 'bot_cut': 0.80}
# A raised hand may come close to the frame but must not be CUT by it: a hand
# cropped at the wrist mid-gesture reads as an error at cut-in scale, where the
# silhouette is read before the face. Only the left and right edges are checked —
# the bottom is the waist line by construction and the crop guarantees the top.
EDGE_TOUCH_MAX = 0.004


def framing(solid):
    """Where the body sits in the frame, from the alpha silhouette alone.

    ONE MEASUREMENT CARRIES THE GATE, chosen to be one a silhouette can actually
    answer without face detection. `shoulder` is how far down the figure the shoulder
    line falls as a fraction of the figure's own height. It is scale-free and it
    separates the three framings by human proportion: crown-to-shoulders is about
    1.25 head-heights, so a WAIST-UP figure (~3 heads of body in frame) puts its
    shoulders around 0.42 of the way down, a chest-up crop (~2.2 heads) around 0.57,
    and a head-and-shoulders close-up higher still.

    The shoulder line is the first row at least 72% as wide as the figure's widest —
    a threshold rather than a peak, because arms and props own the widest row and the
    question here is where the body stops being a head. The test is VERTICAL on
    purpose: a wide hairstyle inflates the head's own width, but it also moves the
    widest row it is measured against, so the ratio survives it.

    `headroom`, `centre` and `fig_frac` are reported for the QA board and NOT gated:
    gen-cutin.py's crop sets all three, so gating them would be checking that file
    against itself rather than checking the art.
    """
    rows = solid.sum(axis=1)
    ys = np.flatnonzero(rows >= 6)
    if len(ys) < 40:
        return None
    top, bot = int(ys[0]), int(ys[-1])
    fig = bot - top
    if fig < 40:
        return None
    # THE SHOULDER LINE IS FOUND AGAINST THE HEAD, NOT AGAINST THE WIDEST ROW, and
    # the first version got this wrong in a way the gesture ruling exposed. Measuring
    # "the first row at least 72% as wide as the widest" works only while the widest
    # row IS the shoulders; once a character throws both arms open the widest row is
    # the arms, the threshold rises with them, and the shoulder line appears to slide
    # down the body. Vesper's `happy` read 0.605 — "framed too tight" — on a plate
    # framed exactly like her `sad` at 0.355. The head is the narrow column at the
    # top of any of these silhouettes, so its own width is the stable unit, and the
    # shoulders are where the body first exceeds it by half again.
    band = rows[top:bot + 1]
    head_w = float(np.median(band[:max(4, int(fig * 0.12))]))
    wide = np.flatnonzero(band >= 1.6 * head_w)
    sh = int(wide[0]) if len(wide) else 0
    cols = solid.sum(axis=0)
    xs = np.flatnonzero(cols >= 6)
    cx = (float(xs[0] + xs[-1]) / 2.0 / solid.shape[1]) if len(xs) else 0.5
    side = (int(solid[:, 0].sum()) + int(solid[:, -1].sum())) / float(2 * solid.shape[0])
    # THE STRAIGHT-CUT WITNESS. The user's ruling is that the art meets the dialogue
    # box in a straight horizontal slice through the torso. If it does, the figure's
    # last rows are as wide as the lower torso above them; a rounded bust taper, a
    # fade, or legs below a three-quarter crop all leave the bottom rows narrow.
    tail = band[-max(4, int(fig * 0.02)):]
    lower = band[int(len(band) * 0.75):]
    bot_cut = float(np.median(tail)) / max(1.0, float(np.median(lower)))
    return {'shoulder': round(sh / fig, 3), 'headroom': round(top / solid.shape[0], 3),
            'centre': round(cx, 3), 'fig_frac': round(fig / solid.shape[0], 3),
            'edge_touch': round(side, 4), 'bot_cut': round(bot_cut, 3),
            'head_frac': round(head_w / fig, 3)}


def grade_framing(m, base=None):
    """metrics -> (bool pass, [reasons]). Waist-up, straight-cut, or it does not ship.

    `base` is the metrics dict of the character's own reference plate: the user's
    ruling is that the base image dictates the set's framing, so a mood is judged
    first against ITS OWN base (d_base), which is immune to the hair/hat bias that
    makes the absolute number character-dependent. The absolute band remains as the
    backstop, and is what judges the base plate itself."""
    if m is None or m.get('head_frac') is None:
        return False, ['no silhouette to frame']
    lo, hi = FRAME['head_frac']
    v = m['head_frac']
    bad = []
    if v > hi:
        bad.append('head_frac %.3f > %.2f — head too large for the figure '
                   '(chest-up or closer)' % (v, hi))
    elif v < lo:
        bad.append('head_frac %.3f < %.2f — head too small for the figure '
                   '(framed below the waist)' % (v, lo))
    if base is not None and base.get('head_frac') is not None:
        d = abs(v - base['head_frac'])
        if d > FRAME['d_base']:
            bad.append('head_frac %.3f drifts %.3f from the base plate (> %.2f) — '
                       'not the framing the reference dictates' % (v, d, FRAME['d_base']))
    if m.get('bot_cut', 1.0) < FRAME['bot_cut']:
        bad.append('bottom rows %.2f of lower-torso width (< %.2f) — no straight '
                   'waist cut' % (m.get('bot_cut', 0.0), FRAME['bot_cut']))
    # The horizontal extent is deliberately NOT bounded: the user ruled the waist-up
    # frame exists to be USED, so a thrown-open arm is the picture working, not a
    # fault. What is bounded is the arm being SEVERED by the frame.
    if m.get('edge_touch', 0) > EDGE_TOUCH_MAX:
        bad.append('gesture cropped at the frame edge (edge_touch %.4f > %.4f)'
                   % (m['edge_touch'], EDGE_TOUCH_MAX))
    return (not bad), bad


def _halo(lum, solid):
    """Luminance of the figure's outer shell minus that of its own core band.

    Both samples are material of the drawing a few pixels apart, which is what
    makes this stable where a soft-band measurement is not: the shell is where a
    pale ring lives whether that ring is semi-transparent (leftover background) or
    fully opaque (a rim the model painted), and the core is the same character
    rendered the same way with no edge effect on it."""
    shell = solid & ~_morph(solid, SHELL, False)
    core = _morph(solid, CORE_IN, False) & ~_morph(solid, CORE_OUT, False)
    if not shell.any() or not core.any():
        return 0.0
    return float(lum[shell].mean() - lum[core].mean())


def measure(path_or_img):
    """RGBA image (path or PIL) -> the metrics dict. `None` for anything with no
    usable silhouette, which is itself a failure the caller reports."""
    im = (Image.open(path_or_img) if isinstance(path_or_img, str) else path_or_img)
    im = im.convert('RGBA')
    arr = np.asarray(im, dtype=np.float64)
    a = arr[..., 3] / 255.0
    solid = a >= 0.5
    if solid.sum() < 64:
        return None

    # The cut itself: solid pixels with a non-solid 4-neighbour, one pixel wide.
    boundary = solid & ~_morph(solid, 1, False)
    nb = int(boundary.sum())
    if nb == 0:
        return None
    band = _morph(boundary, BAND_PX, True)

    soft = (a > SOFT_LO) & (a < SOFT_HI)
    ns = int(soft.sum())
    edge_noise = float((soft & ~band).sum() / ns) if ns else 0.0

    speckle = _detached(solid)
    pinhole = _pinholes(solid)
    halo = _halo(arr[..., :3].mean(axis=-1), solid)
    fr = framing(solid) or {}

    area = float(solid.sum())
    rough = nb / (2.0 * np.sqrt(np.pi * area))

    return {
        'w': im.width, 'h': im.height,
        'edge_noise': round(edge_noise, 4),
        'ramp_px': round(ns / nb, 2),
        'halo': round(halo, 1),
        'speckle': round(speckle, 5),
        'pinhole': round(pinhole, 5),
        'rough': round(float(rough), 2),
        'coverage': round(area / (im.width * im.height), 3),
        **fr,
    }


def grade_edges(m):
    """metrics -> (bool pass, [reasons it failed])."""
    if m is None:
        return False, ['no silhouette']
    bad = []
    if m['edge_noise'] > GATE['edge_noise']:
        bad.append('edge_noise %.3f > %.3f' % (m['edge_noise'], GATE['edge_noise']))
    if m['halo'] > GATE['halo']:
        bad.append('halo +%.1f > +%.0f' % (m['halo'], GATE['halo']))
    if m['ramp_px'] > GATE['ramp_px']:
        bad.append('ramp %.2f > %.1f px' % (m['ramp_px'], GATE['ramp_px']))
    if m['speckle'] > GATE['speckle']:
        bad.append('speckle %.4f > %.4f' % (m['speckle'], GATE['speckle']))
    return (not bad), bad


HEAD = ('%-28s %6s %6s %7s %8s %8s %6s %6s  %s' %
        ('plate', 'edge', 'ramp', 'halo', 'speckle', 'pinhole', 'rough', 'cover', 'verdict'))


def line(label, m):
    if m is None:
        return '%-28s   —  no silhouette' % label
    good, bad = grade_edges(m)
    return ('%-28s %6.3f %6.2f %+7.1f %8.4f %8.4f %6.2f %6.3f  %s' %
            (label, m['edge_noise'], m['ramp_px'], m['halo'], m['speckle'],
             m['pinhole'], m['rough'], m['coverage'],
             'PASS' if good else 'FAIL ' + '; '.join(bad)))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    as_json = '--json' in sys.argv

    files = []
    if args and all(a.endswith('.png') for a in args):
        files = [(os.path.basename(a), a) for a in args]
    else:
        ids = args or sorted(os.listdir(CHARS))
        for cid in ids:
            d = os.path.join(CHARS, cid)
            if not os.path.isdir(d):
                continue
            for n in sorted(os.listdir(d)):
                if n == 'cutin.png' or (n.startswith('cutin-') and n.endswith('.png')):
                    files.append((cid + '/' + n[:-4], os.path.join(d, n)))

    out = {}
    if not as_json:
        print(HEAD)
    for label, p in files:
        m = measure(p)
        out[label] = m
        if not as_json:
            print(line(label, m))
    if as_json:
        print(json.dumps(out, indent=1, sort_keys=True))
    else:
        ms = [m for m in out.values() if m]
        if ms:
            print('\n%d plates · median edge_noise %.3f · %d pass, %d fail' % (
                len(ms), float(np.median([m['edge_noise'] for m in ms])),
                sum(1 for m in ms if grade_edges(m)[0]),
                sum(1 for m in ms if not grade_edges(m)[0])))


if __name__ == '__main__':
    main()
