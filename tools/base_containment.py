"""BASE-CONTAINMENT — does the painted art's GROUND-CONTACT BAND fit the
declared footprint? Shared by slice_blocks9.py and slice_interior.py.

The defect this catches (director-reported): a prop's art overflowing its
declared cells at ground level — the interior counter painted as 2x3 on a
2x2 mark, the oven slightly spilling its 2x2. Legitimate ELEVATED overhang
(tree canopy, stall awning) must NOT trip it.

Band definition (tuned, see notes):
  Every opaque pixel (x, y) is projected into cell space via the measured
  mark basis:  a = (dx + 2*dy)/cW,  b = (2*dy - dx)/cH  (dx,dy relative to
  the fitted back corner T). This projection assumes the pixel sits ON the
  ground plane; a pixel at true height h actually lands at
  (a0 - 2h/cW, b0 - 2h/cH) — elevation aliases toward the BACK (-a,-b),
  never the front. Two conditions, either admits a pixel into the band:

  * INTERIOR SLAB: (a, b) inside the declared footprint diamond (the
    pixel is within the mark's screen parallelogram) — this is the
    counter's "full base body": every front-face pixel up to where the
    body leaves the diamond, hPx ~ 0 by construction.
  * GROUND-CONTACT RIM: the pixel is within RIM px of its column's bottom
    silhouette, its column is GROUND-CONNECTED, and its minimum aliasing
    height
        hPx = max(max(0,-a)*cW, max(0,-b)*cH) / 2
    is <= 0.75*cellPx. (A pixel whose naive cell coords sit da behind the
    back edge is AT LEAST da*cW/2 px above the ground if its base point
    is inside the footprint — elevation shifts both naive axes by 2h/c.)

    GROUND-CONNECTED: a genuine base pixel behind the mark (the counter's
    attached back-right module) and a low elevated overhang (tree canopy
    droop, lamppost bracket) are per-pixel INDISTINGUISHABLE — both
    project behind the back edges. The discriminator is structure: an
    attached base module's bottom rim CONTINUES the ground staircase
    (iso-slope steps, ~0.5 px/column), while an overhang's underside
    JUMPS discontinuously where the body's ground contact ends. So
    bottom-silhouette columns are flood-connected: seeds = columns whose
    bottom point projects at/inside/in-front-of the mark plane (naive
    a, b >= -0.1 — zero aliasing ambiguity there), then adjacency
    propagates while |y_bottom(x) - y_bottom(x+1)| <= JUMP px. The
    tree's canopy droop (lowest point ~0.24 cell up), the lamppost's
    bracket (~0.3 cell up) and the stall's awning (>= 1.5 cells up) all
    sit across a silhouette jump from the base and are excluded; the
    counter's ground-level module rim walks straight out of the B corner
    and is kept. The hPx cap stays as a backstop against smoothly-
    descending overhangs (limits countable back overflow to 1.5 cells).

  Why not the plain band hPx in [-4, ~0.6*cellPx] over ALL pixels: a
  clamp-height proxy aliases the prop's own top-front edge into the back
  cells (a waist-high 2x2 box's top corner at h~1.3*cell projects to
  (-0.6,-0.6) with clamp-hPx ~ 0.6*cell — inside the naive band), which
  false-REDECLARED every box on the real sheets (lamppost -> 3x2, tree ->
  4x4). Requiring bottom-silhouette contact + ground connectivity for any
  pixel OUTSIDE the diamond removes exactly that aliasing; the -4px
  below-plane allowance is subsumed by the rim (silhouette bottoms sit
  wherever the paint ends, including below the mark's front corner).

Measured base = 1st/99th-percentile (a, b) extent over the band (robust to
stray pixels). Verdict:
  PASS      max protrusion <= 0.12 cell
  AUTOFIT   <= 0.4 cell -> renderFitScale = largest factor that pulls the
            base inside the declared cells when shrinking about the anchor
            (footprint centre); equals declared/measured for a centred
            oversized base, handles shifted bases too. Aspect kept.
  REDECLARE > 0.4 cell   -> smallest integer footprint containing the base
"""
import math

PASS_TOL = 0.12       # cells: contained
AUTOFIT_TOL = 0.40    # cells: shrink-to-fit ceiling
H_RIM_FRAC = 0.75     # of cellPx: backstop cap on rim back-aliasing height
SEED_TOL = 0.1        # cells: bottom point at/inside/front of the plane
PCT = 100             # 1st/99th percentile trim


def measure_base(op, w, h, T, cW, cH, fw, fh):
    """op: bytearray(w*h) opaque flags in region coords; T = fitted back
    corner (region coords); cW/cH = measured cell px per axis; (fw, fh) =
    declared footprint. Returns the baseContainment record (verdict +
    remedy) or None if the band is empty."""
    cell = (cW + cH) / 2.0
    RIM = max(4, round(cell * 0.08))
    HRIM = H_RIM_FRAC * cell
    JUMP = max(4, round(cell * 0.04))
    Tx, Ty = T[0], T[1]
    bot = {}
    for p in range(w * h):
        if op[p]:
            x, y = p % w, p // w
            if y > bot.get(x, -1):
                bot[x] = y

    def cellf(x, y):
        dx, dy = x - Tx, y - Ty
        return (dx + 2 * dy) / cW, (2 * dy - dx) / cH

    # ground-connectivity of bottom-silhouette columns: seed where the
    # bottom point projects at/inside/in-front-of the mark plane, then
    # propagate along columns while the silhouette stays continuous
    gc = {}
    for x, y in bot.items():
        a, b = cellf(x, y)
        gc[x] = a >= -SEED_TOL and b >= -SEED_TOL
    cols = sorted(bot)
    for _ in range(2):
        for seq in (cols, cols[::-1]):
            prev = None
            for x in seq:
                if prev is not None and abs(x - prev) == 1 and gc[prev] \
                        and abs(bot[x] - bot[prev]) <= JUMP:
                    gc[x] = True
                prev = x

    a_vals, b_vals = [], []
    n_slab = n_rim = 0
    for p in range(w * h):
        if not op[p]:
            continue
        x, y = p % w, p // w
        a, b = cellf(x, y)
        in_slab = -0.05 <= a <= fw + 0.05 and -0.05 <= b <= fh + 0.05
        in_rim = False
        if not in_slab and gc[x] and y >= bot[x] - RIM:
            hpx = max(max(0.0, -a) * cW, max(0.0, -b) * cH) / 2.0
            in_rim = hpx <= HRIM
        if in_slab or in_rim:
            a_vals.append(a)
            b_vals.append(b)
            n_slab += in_slab
            n_rim += in_rim
    if not a_vals:
        return None
    a_vals.sort()
    b_vals.sort()
    n = len(a_vals)
    t = min(n - 1, max(1, n // PCT))
    aLo, aHi = a_vals[t], a_vals[-1 - t]
    bLo, bHi = b_vals[t], b_vals[-1 - t]
    prot = {
        'backLeft': max(0.0, -aLo), 'frontRight': max(0.0, aHi - fw),
        'backRight': max(0.0, -bLo), 'frontLeft': max(0.0, bHi - fh),
    }
    max_prot = max(prot.values())
    pt = lambda a, b: [round(Tx + a * cW / 2 - b * cH / 2, 1),
                       round(Ty + a * cW / 4 + b * cH / 4, 1)]
    rec = {
        'measuredBase': [round(aHi - aLo, 2), round(bHi - bLo, 2)],
        'baseCellRange': [[round(aLo, 2), round(aHi, 2)],
                          [round(bLo, 2), round(bHi, 2)]],
        'protrusion': {k: round(v, 2) for k, v in prot.items()},
        'maxProtrusion': round(max_prot, 2),
        'bandPx': n, 'slabPx': n_slab, 'rimPx': n_rim,
        'band': {'rimPx': RIM, 'hRimCells': H_RIM_FRAC,
                 'percentile': [1, 99],
                 'note': 'slab = footprint diamond interior; rim = bottom-'
                         'silhouette contact with min aliasing height '
                         '<= %.2f cell' % H_RIM_FRAC},
        # measured base quad in REGION px (caller shifts by crop for sprite)
        'quad': {'T': pt(aLo, bLo), 'R': pt(aHi, bLo),
                 'B': pt(aHi, bHi), 'L': pt(aLo, bHi)},
    }
    if max_prot <= PASS_TOL:
        rec['verdict'] = 'PASS'
    elif max_prot <= AUTOFIT_TOL:
        rec['verdict'] = 'AUTOFIT'
        # largest s that pulls the whole base inside the declared cells
        # when shrinking about the anchor (footprint centre): each side v
        # maps to centre + (v - centre)*s; equals declared/measured for a
        # centred oversized base, also handles shifted bases
        ca, cb = fw / 2.0, fh / 2.0
        s = min(
            ca / (ca - aLo) if aLo < 0 else 1.0,
            ca / (aHi - ca) if aHi > fw else 1.0,
            cb / (cb - bLo) if bLo < 0 else 1.0,
            cb / (bHi - cb) if bHi > fh else 1.0)
        rec['renderFitScale'] = round(s, 3)
    else:
        rec['verdict'] = 'REDECLARE'
        a0 = math.floor(aLo + PASS_TOL)
        a1 = max(a0 + 1, math.ceil(aHi - PASS_TOL))
        b0 = math.floor(bLo + PASS_TOL)
        b1 = max(b0 + 1, math.ceil(bHi - PASS_TOL))
        rec['redeclare'] = {
            'from': [fw, fh], 'to': [a1 - a0, b1 - b0],
            'cellRange': [[a0, a1], [b0, b1]],
            # new anchor = new footprint centre, REGION px
            'anchorPx': [round(Tx + ((a0 + a1) * cW - (b0 + b1) * cH) / 4, 1),
                         round(Ty + ((a0 + a1) * cW + (b0 + b1) * cH) / 8, 1)],
        }
    return rec
