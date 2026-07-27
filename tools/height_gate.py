"""HEIGHT GATE — does the painted art stand at the RIGHT HEIGHT for what it is?

Companion to base_containment.py. base_containment answers "does the ground
band fit the declared FOOTPRINT?"; this answers "is the sprite the right number
of cells TALL?". Footprint is normalized by the registration mark; height is
whatever composition the model chose per sheet region, so nothing verified it
until now (director defect 2026-07-27: giant character, tiny lampposts, squat
props — every asset painted to its own private vertical scale).

THE ENGINE'S HEIGHT UNIT (derived, then confirmed against the live proto and
against interior nearWall.heightCells which already used it):
  * ground cell = TW x TH = 64 x 32 screen px (2:1 dimetric), 0.5 m.
  * one CELL of world HEIGHT (0.5 m) projects to TW/2 = 32 screen px. This is
    the standard iso-cube vertical edge (= half the tile width). A building's
    ridge measured this way lands at ~5 m, a person pinned to 3.4 cells reads
    1.7 m against it — coherent; the pre-fix character at 130 px measured
    4.06 cells = 2.03 m, a giant, exactly the reported defect.

MEASUREMENT: measure the sprite's opaque extent ABOVE its ground line, in the
SPRITE's own painted px (pxAbove = groundLineY - topOpaqueY; the slicer crops
tight so topOpaqueY = 0 and pxAbove = anchorSprite_y). Convert to engine cells
through the asset's ACTUAL render scale, so props (native 1x), buildings
(cellScale S), and the interior shell (S=1.5) all reduce to one number:

    renderScale        = S * TW / cellPx * fitScale        (fitScale = renderFitScale or 1)
    engineHeightPx     = pxAbove * renderScale
    measuredHeightCells = engineHeightPx / (TW/2)
                        = 2 * S * fitScale * pxAbove / cellPx

VERDICT vs the canonical targetHeightCells (specs.json, meters/0.5):
    ratio = measured / target
    PASS        |ratio-1| <= 0.15
    SCALE-NOTE  |ratio-1| <= 0.30  -> record heightFitScale = target/measured
                IF applying it keeps the footprint containable (see coupling).
    REROLL      else — painted proportion is wrong; regenerate with the height
                stated in the prompt ("the lamppost stands three metres — six
                times its pad width").

FOOTPRINT-HEIGHT COUPLING (the load-bearing subtlety): a billboard sprite
scales height and footprint TOGETHER. You cannot rescale height alone. So
heightFitScale = target/measured is only LEGAL when the base has enough slack
to absorb the SAME scale without protruding past AUTOFIT tolerance. Scaling
about the anchor (footprint centre) multiplies each base half-extent by k;
the base stays containable while, per side, measuredBase*k <= declared + 2*TOL.
We compute the largest legal k from the measured base and gate heightFitScale
against it. If the needed k exceeds it, height cannot be reconciled without
breaking the footprint -> REROLL even inside the SCALE-NOTE band.
"""

TW = 64                       # engine screen px per ground cell (width)
HEIGHT_CELL_PX = TW / 2       # 32 px == one 0.5 m cell of world height
PASS_TOL = 0.15               # +-15% of target -> PASS
NOTE_TOL = 0.30               # +-30% -> SCALE-NOTE (reconcilable if footprint has slack)
AUTOFIT_TOL = 0.40            # cells: base-containment shrink ceiling (matches base_containment)


def _legal_height_fit(k, measured_base, declared):
    """Largest uniform scale <= k that keeps the base containable, else None.
    Scaling about the footprint centre multiplies each measured base half-
    extent; the base stays inside declared+2*AUTOFIT_TOL while
    measuredBase*scale <= declared + 2*AUTOFIT_TOL per axis."""
    if not measured_base or not declared:
        return k                      # no base info: assume footprint not limiting
    kmax = min((declared[a] + 2 * AUTOFIT_TOL) / measured_base[a]
               for a in range(2) if measured_base[a] > 0)
    return k if k <= kmax else None


def measure_height(px_above, cell_px, target_cells, S=1.0, fit_scale=1.0,
                   measured_base=None, declared=None):
    """Returns the heightFit record: measured cells, ratio, verdict, and (when
    a SCALE-NOTE is reconcilable) heightFitScale. px_above/cell_px in the
    sprite's painted px; S/fit_scale the asset's render convention."""
    if not cell_px or not target_cells:
        return None
    render_scale = S * TW / cell_px * fit_scale
    measured = px_above * render_scale / HEIGHT_CELL_PX      # == 2*S*fit*px/cell
    ratio = measured / target_cells
    rec = {
        'measuredHeightCells': round(measured, 2),
        'measuredHeightM': round(measured * 0.5, 2),
        'targetHeightCells': round(target_cells, 2),
        'ratio': round(ratio, 3),
        'pxAbove': round(px_above, 1),
        'renderScale': round(render_scale, 4),
    }
    off = abs(ratio - 1.0)
    if off <= PASS_TOL:
        rec['verdict'] = 'PASS'
    elif off <= NOTE_TOL:
        k = target_cells / measured                          # uniform scale to hit target
        legal = _legal_height_fit(k, measured_base, declared)
        if legal is not None:
            rec['verdict'] = 'SCALE-NOTE'
            rec['heightFitScale'] = round(k, 3)
            rec['footprintCoupling'] = 'ok: base has slack for x%.3f' % k
        else:
            rec['verdict'] = 'REROLL'
            rec['footprintCoupling'] = (
                'blocked: x%.3f would push base past footprint+AUTOFIT; '
                'height cannot be fixed by scaling -> regenerate' % k)
    else:
        rec['verdict'] = 'REROLL'
    return rec


def verdict_badge(v):
    return {'PASS': 'PASS', 'SCALE-NOTE': 'NOTE', 'REROLL': 'REROLL'}.get(v, '?')


# ---- spec registry access (spec = intent; the slicers read targets/footprints
# from here and write measurements back to the metrics outcome files) ----
def load_specs(root=None):
    """Return {id: specRecord} from public/assets/iso/specs.json, or {} if
    absent (slicers stay runnable standalone)."""
    import json, os
    if root is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, 'public/assets/iso/specs.json')
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        data = json.load(f)
    return {a['id']: a for a in data.get('assets', [])}


def gate_from_spec(spec, px_above, cell_px, S=1.0, fit_scale=1.0,
                   measured_base=None, declared=None):
    """Convenience: run measure_height against a spec's targetHeightCells."""
    if not spec:
        return None
    t = spec.get('targetHeightCells')
    if not t:
        return None
    return measure_height(px_above, cell_px, t, S=S, fit_scale=fit_scale,
                          measured_base=measured_base, declared=declared)
