#!/usr/bin/env python3
"""festival slicer + measurer (copy of slice_blocks9.py).

Input: a generated sheet where each prop STANDS ON a flat pure-magenta
registration mark (its declared footprint) on a clean light-grey background.

For each of the 9 fixed regions:
  1. find the magenta mark (hue key + significant connected components)
  2. fit the mark's iso parallelogram in SHEARED coordinates
  3. extract the prop: flood-fill near-grey from the region border, key ALL
     magenta, bbox-crop, save keyed PNG
  4. flag overhang / base-spill, run base-containment

Writes <outdir>/<name>.png and <outdir>/festival-metrics.json.
Usage: python3 tools/festival_slice.py SHEET.png OUTDIR
"""
import sys, os, json, math
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base_containment import measure_base
from height_gate import load_specs, gate_from_spec, verdict_badge

PROPS = [  # name, col, row, footW, footH  (must match festival_template.py)
    ('brazier',    0, 0, 1, 1), ('applecrate', 1, 0, 1, 1), ('sign',    2, 0, 1, 1),
    ('haybale',    0, 1, 2, 2), ('firepit',    1, 1, 2, 2), ('logpile', 2, 1, 2, 2),
    ('pumpkincart', 0, 2, 2, 2), ('stall2',    1, 2, 2, 2), ('bigtree', 2, 2, 3, 3),
]

def is_magenta(r, g, b):
    return r - g > 90 and b - g > 60

def near_magenta(r, g, b):
    return r - g > 50 and b - g > 32

def is_greyish(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    return mx - mn < 16 and mx > 140

def mark_components(w, h, mask):
    """mask: bytearray of 0/1 -> (merged bytearray, size). Keeps every
    connected component >= 20% of the largest; tiny blobs are dropped."""
    seen = bytearray(w * h)
    comps = []
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
            comps.append(comp)
    if not comps:
        return bytearray(w * h), 0
    big = max(len(c) for c in comps)
    out = bytearray(w * h)
    n = 0
    for c in comps:
        if len(c) >= big * 0.2:
            n += len(c)
            for p in c:
                out[p] = 1
    return out, n

def edge_coverage(comp, w, h, p0, p1, tol=3):
    """Fraction of sample points along segment p0-p1 with magenta within tol px."""
    n, hit = 24, 0
    for k in range(n + 1):
        x = p0[0] + (p1[0] - p0[0]) * k / n
        y = p0[1] + (p1[1] - p0[1]) * k / n
        found = False
        for dy in range(-tol, tol + 1):
            for dx in range(-tol, tol + 1):
                xi, yi = int(x + dx), int(y + dy)
                if 0 <= xi < w and 0 <= yi < h and comp[yi * w + xi]:
                    found = True
                    break
            if found:
                break
        hit += found
    return hit / (n + 1)

def slice_sheet(sheet_path, outdir):
    im = Image.open(sheet_path).convert('RGB')
    S = im.size[0]
    assert im.size == (S, S), 'expected square sheet'
    px = im.load()
    metrics = {}
    os.makedirs(outdir, exist_ok=True)
    SPECS = load_specs()          # spec = intent (declared footprint + height target)

    for name, col, row, fw, fh in PROPS:
        sp = SPECS.get(name)
        if sp and sp.get('declaredFootprint'):
            fw, fh = sp['declaredFootprint']
        x0, y0 = round(col * S / 3), round(row * S / 3)
        x1, y1 = round((col + 1) * S / 3), round((row + 1) * S / 3)
        w, h = x1 - x0, y1 - y0

        # ---- 1. magenta mask, largest component ----
        mag = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                r, g, b = px[x0 + x, y0 + y]
                if is_magenta(r, g, b):
                    mag[y * w + x] = 1
        comp, n = mark_components(w, h, mag)
        rec = {'declared': [fw, fh], 'region': [x0, y0, w, h], 'markPx': n}
        metrics[name] = rec
        if n < 200:
            rec['fit'] = None
            rec['confidence'] = 0.0
            rec['error'] = 'mark missing (%d magenta px)' % n
            continue

        # ---- 2. fit parallelogram in sheared iso coordinates ----
        pts = [(p % w, p // w) for p in range(w * h) if comp[p]]
        u1s = sorted(x + 2 * y for x, y in pts)
        u2s = sorted(2 * y - x for x, y in pts)
        t = max(1, len(pts) // 300)          # ~0.3% trim against strays
        u1a, u1b = u1s[t], u1s[-1 - t]
        u2a, u2b = u2s[t], u2s[-1 - t]
        uv = lambda u1, u2: ((u1 - u2) / 2.0, (u1 + u2) / 4.0)
        T, R = uv(u1a, u2a), uv(u1b, u2a)
        B, L = uv(u1b, u2b), uv(u1a, u2b)
        cov = min(edge_coverage(comp, w, h, L, B), edge_coverage(comp, w, h, B, R))
        cW = (u1b - u1a) / fw
        cH = (u2b - u2a) / fh
        cell = (cW + cH) / 2
        axis_err = abs(cW - cH) / cell
        fw_meas = (u1b - u1a) / cell
        fh_meas = (u2b - u2a) / cell
        area = (u1b - u1a) * (u2b - u2a) / 4.0   # parallelogram area in px^2
        fill = n / area if area > 0 else 0
        anchor = ((T[0] + B[0]) / 2, (T[1] + B[1]) / 2)
        mx = sum(p[0] for p in pts) / n
        my = sum(p[1] for p in pts) / n
        sxx = sum((p[0] - mx) ** 2 for p in pts) / n
        syy = sum((p[1] - my) ** 2 for p in pts) / n
        sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
        axis_deg = math.degrees(0.5 * math.atan2(2 * sxy, sxx - syy))
        conf = max(0.0, 1.0
                   - min(1, axis_err * 1.5)        # wrong mark shape
                   - max(0, 0.9 - cov)             # weak front edges
                   - max(0, (0.35 - fill) * 2))    # mark mostly hidden
        rec.update({
            'fit': {'T': T, 'R': R, 'B': B, 'L': L},
            'cellPx': round(cell, 1),
            'cellPxPerAxis': [round(cW, 1), round(cH, 1)],
            'measured': [round(fw_meas, 2), round(fh_meas, 2)],
            'anchorSheet': [round(anchor[0] + x0, 1), round(anchor[1] + y0, 1)],
            'axisErr': round(axis_err, 3),
            'markAxisDeg': round(axis_deg, 1),
            'markFill': round(fill, 2),
            'frontEdgeCov': round(cov, 2),
            'confidence': round(conf, 2),
        })

        # ---- 3. extract prop: background flood + magenta key ----
        rgba = Image.new('RGBA', (w, h))
        out = rgba.load()
        bg = bytearray(w * h)          # 1 = background (flood from border)
        stack = []
        for x in range(w):
            stack += [x, (h - 1) * w + x]
        for y in range(h):
            stack += [y * w, y * w + w - 1]
        for p in stack:
            r, g, b = px[x0 + p % w, y0 + p // w]
            bg[p] = 1 if is_greyish(r, g, b) else 0
        stack = [p for p in stack if bg[p]]
        while stack:
            p = stack.pop()
            x, y = p % w, p // w
            for q in (p - 1 if x else -1, p + 1 if x < w - 1 else -1,
                      p - w if y else -1, p + w if y < h - 1 else -1):
                if q >= 0 and not bg[q]:
                    r, g, b = px[x0 + q % w, y0 + q // w]
                    if is_greyish(r, g, b):
                        bg[q] = 1
                        stack.append(q)
        for y in range(h):
            for x in range(w):
                r, g, b = px[x0 + x, y0 + y]
                p = y * w + x
                if bg[p] or is_magenta(r, g, b):
                    out[x, y] = (0, 0, 0, 0)
                elif near_magenta(r, g, b):   # de-spill soft magenta fringe
                    t = min(1.0, ((r - g) + (b - g) - 82) / 60.0)
                    out[x, y] = (int(g + (r - g) * .35), g,
                                 int(g + (b - g) * .35), int(255 * (1 - t * .85)))
                else:
                    out[x, y] = (r, g, b, 255)

        bbox = rgba.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
        sprite = rgba.crop(bbox)
        sprite.save(os.path.join(outdir, name + '.png'))
        cx0, cy0 = bbox[0], bbox[1]
        rec['sprite'] = name + '.png'
        rec['crop'] = list(bbox)       # rel. to region
        rec['anchorSprite'] = [round(anchor[0] - cx0, 1), round(anchor[1] - cy0, 1)]
        rec['fitSprite'] = {k: [round(v[0] - cx0, 1), round(v[1] - cy0, 1)]
                            for k, v in rec['fit'].items()}

        # ---- 4. overhang / base-spill ----
        rec['overhang'] = {
            'left': round(max(0.0, L[0] - bbox[0]), 1),
            'right': round(max(0.0, bbox[2] - 1 - R[0]), 1),
            'baseSpillPx': round(max(0.0, bbox[3] - 1 - B[1]), 1),
        }

        # ---- 5. BASE-CONTAINMENT: ground-contact band vs declared cells ----
        op = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                if out[x, y][3] > 128:
                    op[y * w + x] = 1
        bc = measure_base(op, w, h, T, cW, cH, fw, fh)
        if bc:
            bc['quadSprite'] = {k: [round(v[0] - cx0, 1), round(v[1] - cy0, 1)]
                                for k, v in bc.pop('quad').items()}
            rec['baseContainment'] = bc
            if bc['verdict'] == 'AUTOFIT':
                rec['renderFitScale'] = bc['renderFitScale']
            elif bc['verdict'] == 'REDECLARE':
                rd = bc['redeclare']
                if rd['to'] != rec['declared']:
                    bc['autoRedeclared'] = True
                    rec['declaredOriginal'] = rec['declared']
                    rec['declared'] = list(rd['to'])
                    ax, ay = rd['anchorPx']
                    rec['anchorSheet'] = [round(ax + x0, 1), round(ay + y0, 1)]
                    rec['anchorSprite'] = [round(ax - cx0, 1),
                                           round(ay - cy0, 1)]

        # ---- 6. HEIGHT GATE ----
        hf = gate_from_spec(sp, rec['anchorSprite'][1], rec['cellPx'], S=1.0,
                            fit_scale=rec.get('renderFitScale', 1.0),
                            measured_base=(bc or {}).get('measuredBase'),
                            declared=rec['declared'])
        if hf:
            rec['heightFit'] = hf

    with open(os.path.join(outdir, 'festival-metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=1)
    for name, rec in metrics.items():
        if not rec.get('fit'):
            print('%-11s MARK MISSING/DEFORMED  %s' % (name, rec.get('error', '')))
            continue
        bc = rec.get('baseContainment') or {}
        print('%-11s conf %.2f  cell %spx (%s/%s)  declared %s  measured %s  '
              'anchor %s  overhang L%s R%s  spill %spx'
              % (name, rec['confidence'], rec['cellPx'], *rec['cellPxPerAxis'],
                 rec['declared'], rec['measured'], rec['anchorSprite'],
                 rec['overhang']['left'], rec['overhang']['right'],
                 rec['overhang']['baseSpillPx']))
        if bc:
            print('            base %sx%s cells  prot %s (max %s)  -> %s%s'
                  % (*bc['measuredBase'], bc['protrusion'],
                     bc['maxProtrusion'], bc['verdict'],
                     ' x%s' % bc.get('renderFitScale', '')
                     if bc['verdict'] == 'AUTOFIT' else
                     ' -> %s' % bc['redeclare']['to']
                     if bc['verdict'] == 'REDECLARE' else ''))
        hf = rec.get('heightFit')
        if hf:
            print('            height %.2f/%.2f cells (%.0f%%)  -> %s%s'
                  % (hf['measuredHeightCells'], hf['targetHeightCells'],
                     hf['ratio'] * 100, verdict_badge(hf['verdict']),
                     ' hFit x%s' % hf['heightFitScale']
                     if hf.get('heightFitScale') else ''))
    return metrics

if __name__ == '__main__':
    slice_sheet(sys.argv[1], sys.argv[2] if len(sys.argv) > 2
                else 'public/assets/iso/festival')
