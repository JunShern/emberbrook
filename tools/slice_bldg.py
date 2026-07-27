#!/usr/bin/env python3
"""BUILDING slicer + measurer — registration marks at building scale.

Extends the blocks9 convention (tools/slice_blocks9.py) for one-building
images with this round's new conventions:

  * SATURATED-CYAN background, keyed GLOBALLY BY HUE — not a border flood.
    Every cyan / near-cyan pixel goes transparent no matter where it sits,
    so enclosed pockets (sky seen through a window, the gap under a sign)
    cannot survive by construction. An automated check then asserts that
    ZERO opaque near-cyan pixels remain in the shipped sprite.
  * DOOR MARK: a yellow (#FFD400) diamond embedded in the magenta mark at
    the door's cell. Detected inside the fitted mark parallelogram (so
    yellow art — bread signs, lit windows — can never be mistaken for it)
    and recorded as a cell index relative to the mark's back corner and
    as an offset from the anchor: trigger placement by construction.
  * Mark fit identical in spirit to blocks9: parallelogram fitted in
    sheared iso coordinates u1 = x + 2y, u2 = 2y - x; the mark IS the
    measurement (anchor / ground line / footprint / cell size).

Writes <outdir>/<name>.png (keyed sprite) and merges a record into
<outdir>/bldg-metrics.json.

Usage: python3 tools/slice_bldg.py NAME RAW.png [OUTDIR]
       NAME in bldg_template.BLDGS (bakery | cottage | guildhall)
"""
import sys, os, json, math
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bldg_template import BLDGS

# ---- colour keys -----------------------------------------------------------
def is_magenta(r, g, b):
    return r - g > 90 and b - g > 60

def near_magenta(r, g, b):
    return r - g > 50 and b - g > 32

def is_cyan(r, g, b):
    # saturated-to-shaded cyan: green and blue well above red, blue near green
    return g - r > 40 and b - r > 30 and g > 60 and b > 70 and b > g * 0.7

def near_cyan(r, g, b):
    return g - r > 25 and b - r > 18 and g > 50 and b > 55

def is_yellow(r, g, b):
    return r > 185 and g > 145 and b < 120 and r - b > 105 and g - b > 75

def edge_coverage(mask, w, h, p0, p1, tol=3):
    n, hit = 24, 0
    for k in range(n + 1):
        x = p0[0] + (p1[0] - p0[0]) * k / n
        y = p0[1] + (p1[1] - p0[1]) * k / n
        found = False
        for dy in range(-tol, tol + 1):
            for dx in range(-tol, tol + 1):
                xi, yi = int(x + dx), int(y + dy)
                if 0 <= xi < w and 0 <= yi < h and mask[yi * w + xi]:
                    found = True
                    break
            if found:
                break
        hit += found
    return hit / (n + 1)

def slice_building(name, raw_path, outdir):
    fw, fh, (ddi, ddj) = BLDGS[name]
    im = Image.open(raw_path).convert('RGB')
    w, h = im.size
    px = im.load()
    os.makedirs(outdir, exist_ok=True)
    rec = {'declared': [fw, fh], 'declaredDoor': [ddi, ddj],
           'raw': os.path.basename(raw_path), 'rawSize': [w, h]}

    # ---- 1. magenta mark mask (whole image; magenta is exclusive to marks)
    mag = bytearray(w * h)
    n = 0
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if is_magenta(r, g, b):
                mag[y * w + x] = 1
                n += 1
    rec['markPx'] = n
    if n < 2000:
        rec['fit'] = None
        rec['confidence'] = 0.0
        rec['error'] = 'mark missing (%d magenta px)' % n
        return rec

    # ---- 2. fit parallelogram in sheared iso coordinates -------------------
    pts = [(p % w, p // w) for p in range(w * h) if mag[p]]
    u1s = sorted(x + 2 * y for x, y in pts)
    u2s = sorted(2 * y - x for x, y in pts)
    t = max(1, len(pts) // 300)
    u1a, u1b = u1s[t], u1s[-1 - t]
    u2a, u2b = u2s[t], u2s[-1 - t]
    uv = lambda u1, u2: ((u1 - u2) / 2.0, (u1 + u2) / 4.0)
    T, R = uv(u1a, u2a), uv(u1b, u2a)
    B, L = uv(u1b, u2b), uv(u1a, u2b)
    cov = min(edge_coverage(mag, w, h, L, B), edge_coverage(mag, w, h, B, R))
    cW = (u1b - u1a) / fw
    cH = (u2b - u2a) / fh
    cell = (cW + cH) / 2
    axis_err = abs(cW - cH) / cell
    area = (u1b - u1a) * (u2b - u2a) / 4.0
    fill = n / area if area > 0 else 0
    anchor = ((T[0] + B[0]) / 2, (T[1] + B[1]) / 2)
    conf = max(0.0, 1.0
               - min(1, axis_err * 1.5)
               - max(0, 0.9 - cov)
               # buildings legitimately cover most of the mark: only flag
               # when almost no magenta was visible to fit from
               - max(0, (0.10 - fill) * 5))
    rec.update({
        'fit': {'T': T, 'R': R, 'B': B, 'L': L},
        'cellPx': round(cell, 1),
        'cellPxPerAxis': [round(cW, 1), round(cH, 1)],
        'measured': [round((u1b - u1a) / cell, 2), round((u2b - u2a) / cell, 2)],
        'anchorRaw': [round(anchor[0], 1), round(anchor[1], 1)],
        'axisErr': round(axis_err, 3),
        'markFill': round(fill, 2),
        'frontEdgeCov': round(cov, 2),
        'confidence': round(conf, 2),
    })

    # ---- 3. door diamond: yellow inside the fitted mark (± half a cell) ----
    m1, m2 = cW * 0.5, cH * 0.5
    ys_px = []
    sx_ = sy_ = 0.0
    for y in range(h):
        for x in range(w):
            u1, u2 = x + 2 * y, 2 * y - x
            if u1a - m1 <= u1 <= u1b + m1 and u2a - m2 <= u2 <= u2b + m2:
                r, g, b = px[x, y]
                if is_yellow(r, g, b):
                    ys_px.append(y * w + x)
                    sx_ += x; sy_ += y
    if len(ys_px) >= 80:
        cx, cy = sx_ / len(ys_px), sy_ / len(ys_px)
        a = (cx + 2 * cy - u1a) / cW      # cell coords along +i
        bq = (2 * cy - cx - u2a) / cH     # cell coords along +j
        di, dj = int(math.floor(a)), int(math.floor(bq))
        # The door lives in a WALL: snap the detected cell to the nearest
        # front-perimeter cell of the footprint (interior detections are
        # centroid-flooring noise; a door cannot be inside the building).
        # Front edges are the two viewer-facing ones: i == fw-1 and j == fh-1.
        di = max(0, min(fw - 1, di))
        dj = max(0, min(fh - 1, dj))
        if di != fw - 1 and dj != fh - 1:
            # snap to whichever front edge the raw centroid sits closest to
            if (fw - 1) - a <= (fh - 1) - bq:
                di = fw - 1
            else:
                dj = fh - 1
        # The DOORSTEP is the walkable cell one step OUTSIDE the door's
        # front edge — the cell a player stands on to trigger entry.
        step_i, step_j = (di + 1, dj) if di == fw - 1 else (di, dj + 1)
        rec['door'] = {
            'yellowPx': len(ys_px),
            'centroidRaw': [round(cx, 1), round(cy, 1)],
            'cellFloat': [round(a, 2), round(bq, 2)],
            'cell': [di, dj],
            'doorstep': [step_i, step_j],   # outside the footprint by construction
            'matchesDeclared': [di, dj] == [ddi, ddj],
            # offset of the door cell's centre from the anchor, in cells —
            # what a scene needs to place the trigger next to the door
            'cellOffsetFromAnchor': [round(di + 0.5 - fw / 2, 2),
                                     round(dj + 0.5 - fh / 2, 2)],
        }
    else:
        rec['door'] = {'yellowPx': len(ys_px), 'cell': None,
                       'error': 'door diamond not found in mark'}

    # ---- 4. extract sprite: GLOBAL hue key (cyan bg, magenta + yellow mark)
    rgba = Image.new('RGBA', (w, h))
    out = rgba.load()
    in_mark = lambda x, y: (u1a - m1 <= x + 2 * y <= u1b + m1 and
                            u2a - m2 <= 2 * y - x <= u2b + m2)
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if is_cyan(r, g, b) or is_magenta(r, g, b):
                out[x, y] = (0, 0, 0, 0)
            elif is_yellow(r, g, b) and in_mark(x, y):
                out[x, y] = (0, 0, 0, 0)          # doormat is mark, not art
            elif near_magenta(r, g, b):
                t2 = min(1.0, ((r - g) + (b - g) - 82) / 60.0)
                out[x, y] = (int(g + (r - g) * .35), g,
                             int(g + (b - g) * .35), int(255 * (1 - t2 * .85)))
            elif near_cyan(r, g, b):
                # de-spill: pull green/blue toward red, fade with cyan-ness
                s = (g - r) + (b - r)
                t2 = min(1.0, max(0.0, (s - 43) / 45.0))
                out[x, y] = (r, int(r + (g - r) * .45), int(r + (b - r) * .45),
                             int(255 * (1 - t2 * .9)))
            else:
                out[x, y] = (r, g, b, 255)

    # cleanup: drop small isolated opaque islands (anti-aliased slivers of
    # the mark's seam lines and outline survive both hue keys as sparse
    # magenta-cyan blend specks; the building itself is one big component,
    # with sign/lantern connected through their brackets)
    A = rgba.getchannel('A').load()
    mask = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if A[x, y] > 20:
                mask[y * w + x] = 1
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
            if len(comp) < 1500:
                dropped += len(comp)
                for p in comp:
                    out[p % w, p // w] = (0, 0, 0, 0)
    rec['speckPxRemoved'] = dropped

    bbox = rgba.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    sprite = rgba.crop(bbox)
    sprite.save(os.path.join(outdir, name + '.png'))
    cx0, cy0 = bbox[0], bbox[1]
    rec['sprite'] = name + '.png'
    rec['crop'] = list(bbox)
    rec['anchorSprite'] = [round(anchor[0] - cx0, 1), round(anchor[1] - cy0, 1)]
    rec['fitSprite'] = {k: [round(v[0] - cx0, 1), round(v[1] - cy0, 1)]
                        for k, v in rec['fit'].items()}

    # ---- 5. cyan-pocket check: NO opaque near-cyan pixel may survive -------
    sp = sprite.load()
    sw, sh = sprite.size
    pocket = 0
    worst = None
    for y in range(sh):
        for x in range(sw):
            r, g, b, a = sp[x, y]
            if a >= 200 and near_cyan(r, g, b):
                pocket += 1
                worst = [x, y, r, g, b]
    rec['cyanPocketCheck'] = {'opaqueNearCyan': pocket,
                              'pass': pocket == 0, 'worst': worst}

    # ---- 6. overhang / base spill / solid cells ----------------------------
    rec['overhang'] = {
        'left': round(max(0.0, (L[0] - cx0) - 0), 1),
        'right': round(max(0.0, (bbox[2] - 1 - cx0) - (R[0] - cx0)), 1),
        'baseSpillPx': round(max(0.0, (bbox[3] - 1 - cy0) - (B[1] - cy0)), 1),
    }
    rec['solid'] = [[a, b] for b in range(fh) for a in range(fw)]
    return rec

def main():
    name, raw = sys.argv[1], sys.argv[2]
    outdir = sys.argv[3] if len(sys.argv) > 3 else 'public/assets/iso/bldg'
    rec = slice_building(name, raw, outdir)
    mpath = os.path.join(outdir, 'bldg-metrics.json')
    metrics = {}
    if os.path.exists(mpath):
        with open(mpath) as f:
            metrics = json.load(f)
    metrics[name] = rec
    with open(mpath, 'w') as f:
        json.dump(metrics, f, indent=1)
    if not rec.get('fit'):
        print('%s: MARK MISSING — %s' % (name, rec.get('error')))
        return
    d = rec['door']
    print('%-9s conf %.2f  cell %spx (%s/%s)  declared %s  measured %s' %
          (name, rec['confidence'], rec['cellPx'], *rec['cellPxPerAxis'],
           rec['declared'], rec['measured']))
    print('  door: declared %s  measured %s  (%s, %d yellow px)' %
          (rec['declaredDoor'], d.get('cell'),
           'MATCH' if d.get('matchesDeclared') else 'CHECK', d['yellowPx']))
    print('  cyan pockets: %d opaque near-cyan px -> %s' %
          (rec['cyanPocketCheck']['opaqueNearCyan'],
           'PASS' if rec['cyanPocketCheck']['pass'] else 'FAIL ' +
           str(rec['cyanPocketCheck']['worst'])))
    print('  overhang L%s R%s  baseSpill %spx  anchorSprite %s' %
          (rec['overhang']['left'], rec['overhang']['right'],
           rec['overhang']['baseSpillPx'], rec['anchorSprite']))

if __name__ == '__main__':
    main()
