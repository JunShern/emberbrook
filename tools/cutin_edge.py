#!/usr/bin/env python3
"""cutin_edge.py — THE EDGE-QUALITY INSTRUMENT for cut-in mattes.

    python3 tools/cutin_edge.py                       # every cutin*.png under characters/
    python3 tools/cutin_edge.py odessa hobb           # just these characters
    python3 tools/cutin_edge.py --json path.png ...   # machine-readable, arbitrary files
    python3 tools/cutin_edge.py --selftest            # prove the chroma gate red, 0.2 s

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

              AND IT IS BLIND TO HUE, WHICH IS WHAT `chroma_rim` IS FOR. See below.
  chroma_rim  THE THIRD GATE, and it exists because `halo` is a LUMINANCE
              difference: a rim of the WRONG HUE at the right brightness is
              invisible to it. That is not hypothetical. A bright chartreuse
              outline sat on the shipped cast for a day and a half — measured at
              79 of 112 plates, worst 3157 px on boatwright/cutin — with every
              one of them PASSING this file. The cause was in gen-cutin's band
              despill (it read a legitimately brighter edge pixel as magenta
              residue and subtracted magenta that was never there, driving R and
              B under G); that bug is fixed, and until this term existed nothing
              stopped the next one. A GATE THAT MEASURES BRIGHTNESS CANNOT SEE
              COLOUR.

              WHAT IT IS: the share of the figure's outer SHELL carrying a hue
              its own material 4-10 px in does not, on the KEY'S OWN AXIS. The
              hue is `anti = G - max(R,B)` — the key's complement, exactly what
              over-subtracting a magenta key leaves behind, and exactly the
              predicate the defect was first counted with. `key_rim` is the same
              measurement on `keys = min(R,B) - G`, gen-cutin's own `keyness()`:
              key colour that SURVIVED rather than key colour over-removed.

              THE SHELL-MINUS-CORE SHARE IS THE WHOLE TRICK, and two simpler
              forms were measured and rejected first. A per-pixel comparison
              against a LOCAL interior reference (the shape the despill fix
              itself uses) is defeated by texture: Maren's striped shirt puts a
              green stripe at the boundary and a stripe/cream average a few
              pixels in, so the honest paint reads as an excursion. A plain
              shell share is defeated by paint: child-girl's silhouette is a
              bundle of green reeds. Paint runs through BOTH bands and cancels;
              a rim exists in the shell and nowhere else.
  key_rim     the same number on the key's own hue. REPORTED, NOT GATED — see
              CHROMA_T's note. gen-cutin's `keyres` already refuses surviving key.
  rough       boundary length over the perimeter of a disc of the same area. Pure
              diagnostic, NOT gated: a character with flyaway hair is legitimately
              rougher than one in a hood, and a gate on this would be a gate on
              hairstyle.

THE GATE (grade_edges): edge_noise <= 0.12, halo <= +18 levels, ramp_px <= 3.5,
speckle <= 0.004, chroma_rim <= 0.0005. `pinhole`, `rough` and `key_rim` are
reported, not gated.
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

# THE HUE THRESHOLD, DERIVED AND NOT PICKED, and it is high on purpose.
# `anti = G - max(R,B)` is small and positive on a great deal of honest paint —
# olive cloth, blonde hair, sage wool, a bundle of green reeds — and enormous on
# the fringe, which is an interior colour with R and B arithmetically subtracted
# out of it and G left exactly where it was. Swept over the 51 plates whose
# defect is known PIXEL FOR PIXEL (the pre/post pair either side of the despill
# fix, so their difference IS the defect and nothing else) against the 106
# shipped plates that carry no rim, as shell-minus-core share:
#
#      T     weakest defect      worst clean        verdict
#     24        0.0056             0.0942           INVERTED
#     32        0.0041             0.0474           INVERTED
#     40        0.0022             0.0195           INVERTED
#     48        0.00127            0.00649          INVERTED
#     56        0.00123            0.00171          INVERTED
#     64        0.00088            0.00033          separated 2.7x
#     72        0.00088            0.00016          separated 5.5x
#     80        0.00055            0.00005          separated 11.7x
#
# Below 64 the honest green paint outscores the defect and NO BAR EXISTS AT ALL.
# 72 is where this stops: it is the highest threshold that still costs the
# weakest measured defect nothing (0.00088 at both 64 and 72), and at 80 the
# defect starts to fade faster than the paint does. 102 of the 106 clean plates
# read EXACTLY ZERO here and the worst reads three pixels — which is the shape of
# a real threshold, a level one population leaves entirely, not a tuned knee.
CHROMA_T = 72.0

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
    # THE CHROMA BAR, read off the gap between the two populations at CHROMA_T and
    # not chosen for a target pass rate. Worst clean plate 0.000159 — creel/cutin,
    # which is ONE PIXEL of a 6,270-pixel shell; weakest known defect 0.000876,
    # villager-woman/cutin-worried before the fix, ELEVEN pixels of 12,557. 0.0003
    # sits in that gap at 1.9x the clean ceiling and 2.9x under the weakest defect.
    # THE HONEST LIMIT: this is a share, so its granularity is one over the shell,
    # and on the smallest plate in the cast one pixel is already 0.00016 — the bar
    # is TWO pixels there and twelve on the largest. It is a bar on a rim, not on a
    # pixel, and a fringe worth seeing is hundreds.
    # WHAT IT COSTS TODAY, and every one of them was LOOKED AT at 1:1 over a night
    # value before the bar was written down: 14 shipped plates newly fail — Maren's
    # whole suite of 13 and weaponsmith/cutin — and all 14 carry a plainly visible
    # neon rim on hair or shoulder. They are the "20 left" the fix commit named as
    # unrepairable without studio art to re-mat from. NOTHING ELSE MOVES: the other
    # 106 shipped plates pass, 102 of them at exactly zero.
    # weaponsmith/cutin is the honest weak point at 0.000310 against the 0.0003
    # bar — his rim is real and thin, and a slightly milder version of it would
    # pass. The bar is not lowered to buy margin there: 0.0002 would start failing
    # child-girl's reeds, which are a picture and not a defect.
    'chroma_rim': 0.0003,
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


def grade_framing(m, base=None, own_framing=False):
    """metrics -> (bool pass, [reasons]). Waist-up, straight-cut, or it does not ship.

    `base` is the metrics dict of the character's own reference plate: the user's
    ruling is that the base image dictates the set's framing, so a mood is judged
    first against ITS OWN base (d_base), which is immune to the hair/hat bias that
    makes the absolute number character-dependent. The absolute band remains as the
    backstop, and is what judges the base plate itself.

    `own_framing` DROPS THE ABSOLUTE BAND ONLY, and it exists because the band
    encodes ONE contract — the cast's shared waist-up framing — while
    cutins.spec.json lets a character declare a different one. Mochi is the case:
    he is a cat, his spec asks for "the whole cat filling the frame", and his plate
    measured head_frac 0.162 against a 0.18 floor written for human proportion. That
    is the gate refusing a character for obeying its own instructions. Everything
    else still applies — the straight cut, the severed-gesture check, and (for
    moods) the drift from the character's own base, which is the part that actually
    keeps a SET consistent. A character with its own framing is still held to it;
    it is simply not held to somebody else's."""
    if m is None or m.get('head_frac') is None:
        return False, ['no silhouette to frame']
    lo, hi = (-1e9, 1e9) if own_framing else FRAME['head_frac']
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


def _shell_core(solid):
    """The two samples every rim measurement in this file is made between: the
    figure's outer SHELL, and a band of its own material a few pixels in.

    Computed once and handed to both `_halo` and `_chroma_rim` — they ask
    different questions (how bright is the rim / what colour is it) of exactly the
    same two populations, and the three erosions are the expensive part."""
    return (solid & ~_morph(solid, SHELL, False),
            _morph(solid, CORE_IN, False) & ~_morph(solid, CORE_OUT, False))


def _halo(lum, shell, core):
    """Luminance of the figure's outer shell minus that of its own core band.

    Both samples are material of the drawing a few pixels apart, which is what
    makes this stable where a soft-band measurement is not: the shell is where a
    pale ring lives whether that ring is semi-transparent (leftover background) or
    fully opaque (a rim the model painted), and the core is the same character
    rendered the same way with no edge effect on it."""
    if not shell.any() or not core.any():
        return 0.0
    return float(lum[shell].mean() - lum[core].mean())


def _chroma_rim(rgb, shell, core):
    """(chroma_rim, key_rim) — the share of the outer shell carrying a hue off
    the KEY'S OWN AXIS that the figure's own material 4-10 px in does not.

    THE AXIS IS THE PIPELINE'S, NOT A COLOUR SPACE'S. gen-cutin keys on magenta
    and identifies it by CHANNEL ORDER rather than distance (`keyness()`: the
    key's high channels minus its low ones, weakest pair, = min(R,B) - G for
    magenta). A despill that subtracts more key than was present drives R and B
    under G and leaves the mirror image of that signature, G - max(R,B) — which
    is precisely the predicate the chartreuse outbreak was first counted with
    (3157 px on boatwright/cutin). So both hues are read on the key's own axis
    and neither is a generic saturation: a teal coat, a scarlet vest and warm
    skin all sit off it, which is why Vesper's sage wool and child-girl's green
    reeds are invisible here while an 11-pixel fringe is not.

    THE SUBTRACTION IS WHAT MAKES PAINT SAFE. A share measured on the shell alone
    fails on any character whose SILHOUETTE is the green thing — child-girl is
    holding a bundle of reeds, and they are the outline. A per-pixel comparison
    against a local interior reference (the shape gen-cutin's own despill fix
    uses) fails the other way, on texture: Maren's striped shirt puts a green
    stripe at the boundary and a stripe/cream average a few pixels in. Paint runs
    through BOTH bands and cancels. A rim is in the shell and nowhere else.

    `key_rim` is the same number for key colour that SURVIVED, and it is REPORTED
    AND NOT GATED, on evidence rather than caution: Vesper owns the top ten of the
    whole cast on it (0.013-0.040) and what fires is the magenta edge along her
    auburn hair strands, which I could not tell from bloomed key by eye and have
    no labelled positive set to settle. Gating it would refuse the character the
    framing gate is calibrated on, for something that may be her own art. The
    direction is not unguarded: gen-cutin's `keyres` already refuses any visible
    pixel still within KEY_RESIDUE_R of the key, which is this failure at source.
    """
    if not shell.any() or not core.any():
        return 0.0, 0.0
    anti = rgb[..., 1] - np.maximum(rgb[..., 0], rgb[..., 2])
    keyc = np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]

    def rim(f):
        return (float((f[shell] > CHROMA_T).mean())
                - float((f[core] > CHROMA_T).mean()))
    return rim(anti), rim(keyc)


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
    shell, core = _shell_core(solid)
    halo = _halo(arr[..., :3].mean(axis=-1), shell, core)
    chroma_rim, key_rim = _chroma_rim(arr[..., :3], shell, core)
    fr = framing(solid) or {}

    area = float(solid.sum())
    rough = nb / (2.0 * np.sqrt(np.pi * area))

    return {
        'w': im.width, 'h': im.height,
        'edge_noise': round(edge_noise, 4),
        'ramp_px': round(ns / nb, 2),
        'halo': round(halo, 1),
        'chroma_rim': round(chroma_rim, 6),
        'key_rim': round(key_rim, 6),
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
    # THE HUE THE BRIGHTNESS GATE ABOVE CANNOT SEE. `.get` rather than `[]` so a
    # metrics dict recorded before this term existed still grades.
    if m.get('chroma_rim', 0.0) > GATE['chroma_rim']:
        bad.append('chroma_rim %.5f > %.5f — key-complement fringe around the '
                   'silhouette (halo cannot see a hue)'
                   % (m['chroma_rim'], GATE['chroma_rim']))
    if m['ramp_px'] > GATE['ramp_px']:
        bad.append('ramp %.2f > %.1f px' % (m['ramp_px'], GATE['ramp_px']))
    if m['speckle'] > GATE['speckle']:
        bad.append('speckle %.4f > %.4f' % (m['speckle'], GATE['speckle']))
    return (not bad), bad


HEAD = ('%-28s %6s %6s %7s %8s %8s %8s %8s %6s %6s  %s' %
        ('plate', 'edge', 'ramp', 'halo', 'chroma', 'keyrim', 'speckle', 'pinhole',
         'rough', 'cover', 'verdict'))


def line(label, m):
    if m is None:
        return '%-28s   —  no silhouette' % label
    good, bad = grade_edges(m)
    return ('%-28s %6.3f %6.2f %+7.1f %8.5f %8.5f %8.4f %8.4f %6.2f %6.3f  %s' %
            (label, m['edge_noise'], m['ramp_px'], m['halo'],
             m.get('chroma_rim', 0.0), m.get('key_rim', 0.0), m['speckle'],
             m['pinhole'], m['rough'], m['coverage'],
             'PASS' if good else 'FAIL ' + '; '.join(bad)))


def selftest():
    """PROVE THE CHROMA TERM RED BEFORE ANYONE TRUSTS IT GREEN, on two synthetic
    plates that differ in exactly one thing.

    Both are the same warm figure on a transparent field. The second has its outer
    two pixels put through the arithmetic the shipped defect actually was: the old
    band despill's over-subtraction, C' = (C - s*key)/(1-s) with the magenta key
    and s = 0.40. That takes (180,140,110) to (130,233,13) — R and B driven under
    G, which is the chartreuse.

    The assertion that matters is not that the new term fires. It is that
    EVERY OTHER TERM IN THIS FILE PASSES THE FRINGED PLATE, including `halo`,
    whose sign even goes the safe way (the fringe is DARKER than the material it
    rings, so a one-sided pale-ring gate is not merely blind, it is reassured).
    That is the defect this gate was written for, reproducible in 0.2 s with no
    art on disk."""
    ok = True

    def plate(fringe):
        n, r = 300, 110
        yy, xx = np.mgrid[0:n, 0:n]
        disc = ((yy - n / 2) ** 2 + (xx - n / 2) ** 2) <= r * r
        a = np.where(disc, 255, 0).astype(np.uint8)
        rgb = np.zeros((n, n, 3), np.float64)
        rgb[disc] = (180, 140, 110)
        if fringe:
            ring = disc & ~_morph(disc, 2, False)
            s, key = 0.40, np.array((255.0, 0.0, 255.0))
            rgb[ring] = np.clip((np.array((180.0, 140.0, 110.0)) - s * key)
                                / (1.0 - s), 0, 255)
        return Image.fromarray(
            np.dstack([rgb.astype(np.uint8), a]).astype(np.uint8), 'RGBA')

    clean = measure(plate(False))
    dirty = measure(plate(True))
    print('clean  ' + line('synthetic/clean', clean))
    print('fringe ' + line('synthetic/fringed', dirty))

    def want(cond, msg):
        nonlocal ok
        print(('  ok   ' if cond else '  FAIL ') + msg)
        ok = ok and cond

    want(dirty['chroma_rim'] > GATE['chroma_rim'],
         'chroma_rim fires on the fringe (%.5f > %.5f)'
         % (dirty['chroma_rim'], GATE['chroma_rim']))
    want(clean['chroma_rim'] <= GATE['chroma_rim'],
         'chroma_rim silent on the clean plate (%.5f)' % clean['chroma_rim'])
    want(not grade_edges(dirty)[0], 'the gate REFUSES the fringed plate')
    want(grade_edges(clean)[0], 'the gate passes the clean plate')
    # ...and the whole reason this term had to be written:
    want(dirty['halo'] <= GATE['halo'],
         'halo passes the fringed plate (%+.1f <= +%.0f) — brightness cannot see '
         'colour' % (dirty['halo'], GATE['halo']))
    prev = dict(dirty)
    prev.pop('chroma_rim')
    want(grade_edges(prev)[0],
         'and every OTHER term passes it too (the pre-2026-08-09 gate was green)')
    print('SELFTEST ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    as_json = '--json' in sys.argv
    if '--selftest' in sys.argv:
        sys.exit(selftest())

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
