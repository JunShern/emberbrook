#!/usr/bin/env python3
"""iso_key — ONE keying implementation for every iso slicer.

The painted-iso sheets use two key colours: a CYAN background and a MAGENTA
registration-mark pad (buildings/interiors also embed a YELLOW door diamond).
The historical slicers each keyed by HARD hue thresholds — a pixel was either
100% art or 100% gone — which left two visible defects the director flagged:

  * TEAL / MAGENTA EDGE FRINGE — the 1-2px anti-aliased ramp where art meets
    the key colour is a blend (e.g. metal-rim + cyan-bg -> teal). Its hue
    sits just under the hard key threshold, so it shipped at FULL alpha as a
    coloured halo hugging every silhouette.
  * THE "BOX" — the magenta pad is an iso DIAMOND drawn under each prop. Its
    own anti-aliased perimeter is a dotted ring of magenta-blend pixels ON THE
    GROUND, outside the prop. They survived the key as a diamond of specks —
    "a box around most items".

This module replaces the binary cut with a feathered soft key:

  1. SOFT ALPHA  — alpha ramps (smoothstep) across the key-distance band, so
     edges feather over ~2px instead of stair-stepping.
  2. DESPILL     — inside the band the key tint is pulled out: magenta pixels
     have R,B dragged toward G; cyan pixels have G,B dragged toward R. Strength
     scales with key-ness, so a barely-tinted rim pixel keeps its art colour
     while a mostly-key pixel is fully neutralised. No pink/teal halo remains
     even where alpha is only partial.
  3. EDGE-BAND LIMIT — despill/soft-alpha touch ONLY pixels within `band` px of
     a keyed (transparent) pixel. Art that legitimately contains teal or pink
     (cottage timber panels, awning stripes, glass) sits in the interior, never
     in the band, so it is never recoloured. This is what keeps the despill
     from eating art.
  4. FEATHER     — a light neighbour-average pass on the alpha channel (mirrors
     the shipped character recipe in public/js/sprites2.js) smooths the ramp.
  5. SPECK DROP  — small isolated opaque components (the pad-diamond dots, seam
     slivers) are removed by connected-component area.
  6. RESIDUE CLEAR (assertion) — any SATURATED cyan/magenta pixel that somehow
     survived is cleared and COUNTED, so drift is always a visible number. This
     is the assertion previously inlined in slice_v2.py, folded in here.

Two entry points:
  * key_from_raw(...)  — full RGB sheet -> keyed RGBA (bldg / interior / v2).
  * clean_keyed(...)   — an already-keyed RGBA whose raw sheet is gone
                         (blocks9 / festival): despill the surviving opaque
                         fringe, drop the pad specks, in place, SAME canvas.
"""
import os

# --------------------------------------------------------------------------
# colour predicates — the HARD keys (a pixel that trips one is definitely the
# background or the mark). Kept conservative so painted art is never a core
# key; the feathering below handles everything between art and core.
# --------------------------------------------------------------------------

def is_magenta(r, g, b):
    return r - g > 90 and b - g > 60

def near_magenta(r, g, b):
    return r - g > 50 and b - g > 32

def is_cyan(r, g, b):
    # saturated-to-shaded cyan background: g and b well above r, b near g
    return g - r > 40 and b - r > 30 and g > 60 and b > 70 and b > g * 0.7

def near_cyan(r, g, b):
    return g - r > 25 and b - r > 18 and g > 50 and b > 55

def is_greyish(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    return mx - mn < 16 and mx > 140

def is_yellow(r, g, b):
    return r > 185 and g > 145 and b < 120 and r - b > 105 and g - b > 75


# --------------------------------------------------------------------------
# continuous key-ness — how magenta / cyan a pixel is, in channel units.
# A blend of art + key lands mid-band; pure art is <= 0.
# --------------------------------------------------------------------------

def mag_key(r, g, b):
    return min(r - g, b - g)          # both R and B above G

def cyan_key(r, g, b):
    return min(g - r, b - r)          # both G and B above R


def _smooth(t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return t * t * (3 - 2 * t)        # smoothstep


# feather / despill band edges (channel units on mag_key / cyan_key).
# LO = art side (below this, untouched); HI = core side (above this the hard
# predicate already fired). Despill runs from LO_D (a touch below LO) so even
# the faintest tinted rim de-spills.
MAG_LO_D, MAG_LO, MAG_HI = 14, 24, 82
CYAN_LO_D, CYAN_LO, CYAN_HI = 12, 20, 70
DESPILL = 0.92                        # max fraction of key tint pulled out
INTERIOR_RESIDUE_PX = 500             # near-key components below this = residue


def despill_pixel(r, g, b, a=255, do_mag=True, do_cyan=True, aggressive=False):
    """Soft-key one pixel: pull the requested key tint(s) toward the neutral
    (art) channel and ramp alpha with key-ness. Returns (r,g,b,a). do_mag /
    do_cyan gate which key is pulled — the caller decides scope (magenta is
    always residue so it runs globally; cyan is scoped to fringe/cracks so
    green foliage and teal panels survive). A pixel with no key tint (or with
    its key not requested) comes back unchanged.

    aggressive: for pixels the caller KNOWS are silhouette fringe (edge band),
    the despill floor is raised so even a weakly-tinted fringe pixel is pulled
    substantially toward neutral — otherwise leaf-edge blends that sit just
    over the near_ threshold survive as faint teal/pink freckles. Never used on
    interior pixels, so art is unaffected."""
    mk = mag_key(r, g, b)
    ck = cyan_key(r, g, b)
    out_a = a
    R, G, B = float(r), float(g), float(b)
    floor = 0.60 if aggressive else 0.0

    if do_mag and mk > MAG_LO_D:
        # despill: drag R and B down toward G
        fr = max(floor, _smooth((mk - MAG_LO_D) / (MAG_HI - MAG_LO_D)))
        d = DESPILL * fr
        R = G + (R - G) * (1 - d)
        B = G + (B - G) * (1 - d)
        # alpha ramp starts at LO (art side) -> HI (fully keyed)
        fa = _smooth((mk - MAG_LO) / (MAG_HI - MAG_LO))
        out_a = min(out_a, a * (1 - fa))

    if do_cyan and ck > CYAN_LO_D:
        # recompute cyan-ness on the (possibly magenta-despilled) colour so we
        # don't double-count; drag G and B down toward R
        ck2 = min(G - R, B - R)
        if ck2 > CYAN_LO_D:
            fr = max(floor, _smooth((ck2 - CYAN_LO_D) / (CYAN_HI - CYAN_LO_D)))
            d = DESPILL * fr
            G = R + (G - R) * (1 - d)
            B = R + (B - R) * (1 - d)
        fa = _smooth((ck - CYAN_LO) / (CYAN_HI - CYAN_LO))
        out_a = min(out_a, a * (1 - fa))

    return (int(round(R)), int(round(G)), int(round(B)), int(round(out_a)))


# --------------------------------------------------------------------------
# whole-sprite passes — operate on a PIL RGBA .load() pixel access + (w,h).
# --------------------------------------------------------------------------

def _alpha_bytes(px, w, h):
    a = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            a[row + x] = px[x, y][3]
    return a


def feather_alpha(px, w, h, thresh=8):
    """Neighbour-average smoothing of the alpha channel (mirror of the
    character recipe in sprites2.js). Only rewrites where the local average
    differs from the pixel by > thresh, so flat interiors and hard cores are
    untouched — it just rounds the ramp."""
    a0 = _alpha_bytes(px, w, h)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = y * w + x
            if not a0[i]:
                continue          # never paint silhouette onto empty canvas
            avg = (a0[i] * 4 + a0[i - 1] + a0[i + 1]
                   + a0[i - w] + a0[i + w]) / 8.0
            if abs(avg - a0[i]) > thresh:
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, int(round(avg)))


def drop_specks(px, w, h, min_px, alpha_th=8):
    """Remove opaque islands smaller than min_px (the pad-diamond dots, seam
    slivers, and the faint feather-bleed pixels the alpha pass leaves in empty
    canvas). alpha_th is intentionally low (below the slicers' bbox threshold
    of 20) so a stray feathered pixel is a droppable island, not a bbox-
    inflating survivor. Returns pixels dropped. 4-connected on alpha > alpha_th."""
    mask = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            if px[x, y][3] > alpha_th:
                mask[row + x] = 1
    seen = bytearray(w * h)
    dropped = 0
    for start in range(w * h):
        if mask[start] and not seen[start]:
            comp, stack = [], [start]
            seen[start] = 1
            while stack:
                p = stack.pop()
                comp.append(p)
                x, y = p % w, p // w
                for q in (p - 1 if x else -1, p + 1 if x < w - 1 else -1,
                          p - w if y else -1, p + w if y < h - 1 else -1):
                    if q >= 0 and mask[q] and not seen[q]:
                        seen[q] = 1
                        stack.append(q)
            if len(comp) < min_px:
                dropped += len(comp)
                for p in comp:
                    px[p % w, p // w] = (0, 0, 0, 0)
    return dropped


def _sat_cyan(r, g, b):
    # bright saturated cyan only — never a shaded teal timber/glass art pixel
    return b > 150 and g > 140 and r < 110 and b - r > 60 and g - r > 45

def _sat_magenta(r, g, b):
    return r > 130 and b > 100 and r - g > 60 and b - g > 40


def clear_residue(px, w, h, alpha_th=0):
    """Assertion pass: clear any SATURATED cyan/magenta pixel still opaque and
    return the count. Thresholds are the conservative ones from slice_v2.py so
    shaded teal/pink ART is never touched — only true key survivors."""
    residue = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > alpha_th and (_sat_cyan(r, g, b) or _sat_magenta(r, g, b)):
                px[x, y] = (r, g, b, 0)
                residue += 1
    return residue


def _small_cyan_components(px, w, h, max_px, alpha_th=24):
    """Flag opaque near_cyan pixels that belong to a SMALL connected component
    of near_cyan pixels. These are cyan residue that bled through interior
    cracks (slat gaps, seams) — thin, so a small area. A LARGE near_cyan
    component is painted art (teal glass panel, green foliage) and is left
    alone: this is the interior counterpart of the edge-band limit, and it is
    CYAN-ONLY because near_cyan overlaps legitimate greens while near_magenta
    never overlaps art (which is why magenta despill runs globally)."""
    mask = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > alpha_th and near_cyan(r, g, b):
                mask[row + x] = 1
    seen = bytearray(w * h)
    flag = bytearray(w * h)
    for start in range(w * h):
        if mask[start] and not seen[start]:
            comp, stack = [], [start]
            seen[start] = 1
            while stack:
                p = stack.pop()
                comp.append(p)
                x, y = p % w, p // w
                for q in (p - 1 if x else -1, p + 1 if x < w - 1 else -1,
                          p - w if y else -1, p + w if y < h - 1 else -1):
                    if q >= 0 and mask[q] and not seen[q]:
                        seen[q] = 1
                        stack.append(q)
            if len(comp) < max_px:
                for p in comp:
                    flag[p] = 1
    return flag


def _edge_band(px, w, h, band, alpha_th=24):
    """Return a bytearray flagging opaque pixels within `band` px of a
    transparent pixel (the fringe). Interior art is left un-flagged so despill
    never recolours it. Uses a two-pass chamfer-ish dilation of the hole set."""
    # distance-to-hole via BFS rings from transparent pixels
    INF = 255
    dist = bytearray([INF]) * (w * h)
    stack = []
    for y in range(h):
        row = y * w
        for x in range(w):
            if px[x, y][3] <= alpha_th:
                dist[row + x] = 0
                stack.append(row + x)
    head = 0
    while head < len(stack):
        p = stack[head]
        head += 1
        d = dist[p]
        if d >= band:
            continue
        x, y = p % w, p // w
        for q in (p - 1 if x else -1, p + 1 if x < w - 1 else -1,
                  p - w if y else -1, p + w if y < h - 1 else -1):
            if q >= 0 and dist[q] > d + 1:
                dist[q] = d + 1
                stack.append(q)
    flag = bytearray(w * h)
    for i in range(w * h):
        if 0 < dist[i] <= band:
            flag[i] = 1
    return flag


def _apply_despill(px, w, h, band, interior_max_px=INTERIOR_RESIDUE_PX):
    """Despill fringe pixels. MAGENTA despill is GLOBAL — a near_magenta pixel
    is always mark residue (the pad rim, the interior magenta-floor edge line),
    never art (maroon awnings have too little blue to qualify). CYAN despill is
    SCOPED to the edge band and small interior cyan components, so large green
    foliage / teal panels (which trip near_cyan) survive untouched. Edge-band
    pixels additionally get the sub-threshold magenta feather. Returns count."""
    edge = _edge_band(px, w, h, band)
    small_cyan = _small_cyan_components(px, w, h, interior_max_px)
    changed = 0
    for y in range(h):
        row = y * w
        for x in range(w):
            i = row + x
            r, g, b, a = px[x, y]
            if not a:
                continue
            do_mag = near_magenta(r, g, b) or edge[i]
            do_cyan = edge[i] or small_cyan[i]
            if not (do_mag or do_cyan):
                continue
            nr, ng, nb, na = despill_pixel(r, g, b, a,
                                           do_mag=do_mag, do_cyan=do_cyan,
                                           aggressive=bool(edge[i]))
            if (nr, ng, nb, na) != (r, g, b, a):
                px[x, y] = (nr, ng, nb, na)
                changed += 1
    return changed


# --------------------------------------------------------------------------
# ENTRY POINT A — key a freshly-painted RGB sheet (raw available).
# --------------------------------------------------------------------------

def key_from_raw(px, x0, y0, w, h, *, bg='cyan_global',
                 in_mark=None, extra_key=None, band=2, speck_px=48):
    """Key region (x0,y0,w,h) of an RGB sheet (`px` = img.load()).

    bg:
      'cyan_global'  — every cyan pixel keyed by hue anywhere (enclosed
                       pockets cannot survive). For saturated-cyan sheets.
      'grey_flood'   — flood near-grey from the region border only.
      'grey_or_cyan_flood' — flood grey OR cyan from the border.
    in_mark(x,y) -> bool : optional; a yellow pixel inside the mark is keyed
                           (door diamond), yellow art outside is kept.
    extra_key    : optional bytearray(w*h); 1 = force this pixel transparent
                   (e.g. a pre-computed yellow door-mat mask).
    Returns (rgba_image, stats). rgba is UNCROPPED (region-sized); caller
    bboxes/crops as before so anchors are unaffected.
    """
    from PIL import Image
    rgba = Image.new('RGBA', (w, h))
    out = rgba.load()

    # 1. background mask
    bgm = bytearray(w * h)
    if bg == 'cyan_global':
        for y in range(h):
            row = y * w
            for x in range(w):
                r, g, b = px[x0 + x, y0 + y]
                if is_cyan(r, g, b):
                    bgm[row + x] = 1
    else:
        want_cyan = (bg == 'grey_or_cyan_flood')
        def isbg(r, g, b):
            return is_greyish(r, g, b) or (want_cyan and is_cyan(r, g, b))
        stack = []
        for x in range(w):
            stack += [x, (h - 1) * w + x]
        for y in range(h):
            stack += [y * w, y * w + w - 1]
        seed = []
        for p in stack:
            r, g, b = px[x0 + p % w, y0 + p // w]
            if isbg(r, g, b):
                bgm[p] = 1
                seed.append(p)
        while seed:
            p = seed.pop()
            x, y = p % w, p // w
            for q in (p - 1 if x else -1, p + 1 if x < w - 1 else -1,
                      p - w if y else -1, p + w if y < h - 1 else -1):
                if q >= 0 and not bgm[q]:
                    r, g, b = px[x0 + q % w, y0 + q // w]
                    if isbg(r, g, b):
                        bgm[q] = 1
                        seed.append(q)

    # 2. per-pixel key: core keys -> transparent, else copy art (despill in a
    #    second pass, limited to the edge band).
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b = px[x0 + x, y0 + y]
            if (bgm[row + x] or is_magenta(r, g, b) or is_cyan(r, g, b)
                    or (extra_key is not None and extra_key[row + x])
                    or (in_mark is not None and is_yellow(r, g, b)
                        and in_mark(x, y))):
                out[x, y] = (0, 0, 0, 0)
            else:
                out[x, y] = (r, g, b, 255)

    # 3. despill the fringe (edge band + small interior crack residue); art
    #    interior and large teal/pink art regions untouched
    _apply_despill(out, w, h, band)

    # 4. feather, speck-drop, residue assertion
    feather_alpha(out, w, h)
    dropped = drop_specks(out, w, h, speck_px)
    residue = clear_residue(out, w, h)
    return rgba, {'speckPxRemoved': dropped, 'keyResiduePxCleared': residue}


# --------------------------------------------------------------------------
# ENTRY POINT B — clean an already-keyed sprite in place (raw sheet gone).
# Preserves the canvas size exactly, so crop/anchor metrics are unchanged.
# --------------------------------------------------------------------------

def clean_keyed(rgba, *, band=2, speck_px=40):
    """Despill the surviving opaque fringe of an already-keyed RGBA sprite,
    feather it, drop pad-diamond specks, clear saturated residue. In place,
    same dimensions. Returns stats."""
    w, h = rgba.size
    px = rgba.load()
    despilled = _apply_despill(px, w, h, band)
    feather_alpha(px, w, h)
    dropped = drop_specks(px, w, h, speck_px)
    residue = clear_residue(px, w, h)
    return {'edgePxDespilled': despilled,
            'speckPxRemoved': dropped,
            'keyResiduePxCleared': residue}
