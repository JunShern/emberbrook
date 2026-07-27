#!/usr/bin/env python3
"""INTERIOR slicer — floor registration: the room measured from its floor mark.

The inversion of the prop convention: props STAND ON a magenta mark, a room
WRAPS AROUND one. The generated shell paints the walkable floor as one flat
magenta plane reaching exactly to the wall bases (variant A, the winner of
this round's variant test); the floor mark IS the room's registration:

  * SLOPE RECTIFICATION, COMPUTED: the model paints interiors at a steeper
    axonometric slope than 2:1 (the old bakery interior was hand-rescued
    with an eyeballed 0.873 x-squash). Here the floor mask's four edge
    slopes are regressed from the mask boundary; the correction to 2:1 is
    split evenly between an x-stretch and a y-squash (geometric mean, area
    preserving) and applied by resampling BEFORE the fit. Measured, not
    hand-tuned.
  * GRID: standard u-space parallelogram fit (u1 = x+2y, u2 = 2y-x) of the
    rectified floor mask -> grid origin, cellPx per axis, anchor.
  * WALL LINE = floor polygon edge: walls rise from the mark's edges, so
    the solid map derives from the fit — walkable = the 8x8 cells inside
    the polygon, solid = the wall ring outside it. Solidity by
    construction; an opaque-art-inside-polygon count PROVES the back walls
    never intrude over walkable floor.
  * DOOR: the model refused an abstract yellow cell on the magenta floor
    (4 attempts) but happily painted a YELLOW DOORMAT — outside the door,
    exterior side (a doormat's semantic home). The mat's centroid maps
    through the measured grid to the door's wall segment j; the interior
    doorstep = the walkable cell in front of that segment.
  * SPLIT BY MEASURED WALL PLANE: the near-right wall (i = 8 edge) is cut
    into its own layer, drawn over the character. The wall's painted base
    line is measured per column (bottom silhouette), its height from the
    opaque runs above the base; the cut keeps every opaque pixel inside
    the oblique band swept by the wall plane up to the measured height.
    Everything else is the back layer (floor rim + far walls), drawn
    under everything. Both layers share one crop, so they register.
  * The magenta floor keys to TRANSPARENT: the shipped shell is walls
    only; the real floor is the engine's f-plank ground supertile
    (decided + documented in interior-metrics.json). This is also what
    makes the split trivial to verify: floor art cannot leak into a wall
    layer because there is no floor art.

Also slices the interior props sheet (blocks9 convention, cyan background,
3x2 regions) with one interior finding mechanised: the model tends to stand
LARGE props beside/behind their mark instead of on it (markFill stays high
where an on-mark prop would hide its mark's centre). Detected per prop; such
props get a BASE-CONTACT anchor derived from the art's lowest opaque corner
+ the mark's measured cellPx instead of the mark-centre anchor.

Usage: python3 tools/slice_interior.py shell RAW.png [OUTDIR]
       python3 tools/slice_interior.py props RAW.png [OUTDIR]
Writes sprites + merges into <outdir>/interior-metrics.json.
"""
import sys, os, json, math
from PIL import Image

ROOM = (8, 8)
DECLARED_DOORSTEP = (7, 2)      # from tools/interior_template.py
PROPS = [  # name, col, row, footW, footH (must match interior_template.py)
    ('oven',      0, 0, 2, 2), ('counter', 1, 0, 2, 2), ('preptable', 2, 0, 2, 2),
    ('shelf',     0, 1, 1, 1), ('stool',   1, 1, 1, 1), ('sacks',     2, 1, 1, 1),
]
TW = 64

# ---- colour keys (bldg conventions) ---------------------------------------
def is_magenta(r, g, b):
    return r - g > 90 and b - g > 60

def near_magenta(r, g, b):
    return r - g > 50 and b - g > 32

def is_cyan(r, g, b):
    return g - r > 40 and b - r > 30 and g > 60 and b > 70 and b > g * 0.7

def near_cyan(r, g, b):
    return g - r > 25 and b - r > 18 and g > 50 and b > 55

def is_yellow(r, g, b):
    return r > 185 and g > 145 and b < 110 and r - b > 105 and g - b > 75


def mag_mask(px, w, h):
    m = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if is_magenta(*px[x, y]):
                m[y * w + x] = 1
    return m


def largest_component(w, h, mask):
    seen = bytearray(w * h)
    best = []
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
            if len(comp) > len(best):
                best = comp
    out = bytearray(w * h)
    for p in best:
        out[p] = 1
    return out, len(best)


def fit_line(pts):
    """least-squares y = m x + b over [(x,y)]; returns m, b."""
    n = len(pts)
    sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts); sxy = sum(p[0] * p[1] for p in pts)
    d = n * sxx - sx * sx
    if d == 0:
        return 0.0, sy / n
    m = (n * sxy - sx * sy) / d
    return m, (sy - m * sx) / n


def measure_slope(mask, w, h):
    """Regress the floor mask's four boundary edge slopes.
    Top boundary per column -> the two back-wall base edges (clean);
    bottom boundary -> the two open front edges (may carry a plinth
    remnant: a constant offset, which does not change slope)."""
    top, bot = {}, {}
    for x in range(w):
        ys = [y for y in range(h) if mask[y * w + x]]
        if ys:
            top[x] = min(ys)
            bot[x] = max(ys)
    tx = min(top, key=lambda x: top[x])          # back corner column
    bx = min(bot, key=lambda x: -bot[x])         # front corner column
    xs = sorted(top)
    x0, x1 = xs[0], xs[-1]
    pad = round((x1 - x0) * 0.08)
    seg = lambda d, a, b: [(x, d[x]) for x in d if a <= x <= b]
    edges = {}
    for name, d, a, b in [
            ('backLeft',   top, x0 + pad, tx - pad),
            ('backRight',  top, tx + pad, x1 - pad),
            ('frontLeft',  bot, x0 + pad, bx - pad),
            ('frontRight', bot, bx + pad, x1 - pad)]:
        pts = seg(d, a, b)
        if len(pts) > 20:
            m, _ = fit_line(pts)
            edges[name] = round(abs(m), 4)
    slope = sum(edges.values()) / len(edges)
    return round(slope, 4), edges


def ufit(mask, w, h, trim=300):
    pts = [(p % w, p // w) for p in range(w * h) if mask[p]]
    u1s = sorted(x + 2 * y for x, y in pts)
    u2s = sorted(2 * y - x for x, y in pts)
    t = max(1, len(pts) // trim)
    return u1s[t], u1s[-1 - t], u2s[t], u2s[-1 - t], len(pts)


def uv(u1, u2):
    return ((u1 - u2) / 2.0, (u1 + u2) / 4.0)


# ---------------------------------------------------------------------------
def slice_shell(raw_path, outdir):
    fw, fh = ROOM
    im = Image.open(raw_path).convert('RGB')
    w, h = im.size
    px = im.load()
    rec = {'declared': list(ROOM), 'declaredDoorstep': list(DECLARED_DOORSTEP),
           'raw': os.path.basename(raw_path), 'rawSize': [w, h]}

    # ---- 1. floor mask on the RAW image; measure painted slope ------------
    mag = mag_mask(px, w, h)
    mag, n = largest_component(w, h, mag)
    rec['floorMarkPx'] = n
    if n < 20000:
        rec['error'] = 'floor mark missing (%d px)' % n
        return rec
    slope, edge_slopes = measure_slope(mag, w, h)
    rec['paintedSlope'] = slope
    rec['paintedSlopePerEdge'] = edge_slopes

    # ---- 2. rectify to 2:1, split between x-stretch and y-squash ----------
    # slope' = slope * ky / kx ; want 0.5 with kx*? distortion split evenly:
    # kx = sqrt(slope/0.5), ky = 1/kx  ->  slope * ky / kx = slope / kx^2 = 0.5
    k = math.sqrt(slope / 0.5)
    rec['rectify'] = {'slopeMeasured': slope, 'targetSlope': 0.5,
                      'xStretch': round(k, 4), 'ySquash': round(1 / k, 4),
                      'equivalentSingleAxisX': round(slope / 0.5, 4)}
    rw, rh = round(w * k), round(h / k)
    rim = im.resize((rw, rh), Image.LANCZOS)
    rpx = rim.load()

    # ---- 3. u-space fit of the rectified floor mask -----------------------
    rmag = mag_mask(rpx, rw, rh)
    rmag, rn = largest_component(rw, rh, rmag)
    u1a, u1b, u2a, u2b, _ = ufit(rmag, rw, rh)
    T, R = uv(u1a, u2a), uv(u1b, u2a)
    B, L = uv(u1b, u2b), uv(u1a, u2b)
    cW = (u1b - u1a) / fw
    cH = (u2b - u2a) / fh
    cell = (cW + cH) / 2
    axis_err = abs(cW - cH) / cell
    anchor = ((T[0] + B[0]) / 2, (T[1] + B[1]) / 2)
    conf = max(0.0, 1.0 - min(1, axis_err * 1.5))
    rec.update({
        'rectSize': [rw, rh],
        'fit': {'T': T, 'R': R, 'B': B, 'L': L},
        'cellPx': round(cell, 1),
        'cellPxPerAxis': [round(cW, 1), round(cH, 1)],
        'measured': [round((u1b - u1a) / cell, 2), round((u2b - u2a) / cell, 2)],
        'anchorRect': [round(anchor[0], 1), round(anchor[1], 1)],
        'axisErr': round(axis_err, 3),
        'confidence': round(conf, 2),
    })
    e1 = (cW / 2.0, cW / 4.0)
    e2 = (-cH / 2.0, cH / 4.0)
    ox = T[0]
    oy = T[1]
    def cellf(x, y):                       # pixel -> cell floats (a, b)
        a = ((x - ox) + 2 * (y - oy)) / cW
        b = (2 * (y - oy) - (x - ox)) / cH
        return a, b
    def pt(a, b):
        return (ox + a * e1[0] + b * e2[0], oy + a * e1[1] + b * e2[1])

    # ---- 4. per-cell magenta coverage (verification grid) -----------------
    cov = {}
    NS = 7
    for a in range(-2, fw + 2):
        for b in range(-2, fh + 2):
            hit = tot = 0
            for i in range(NS):
                for j in range(NS):
                    x, y = pt(a + (i + .5) / NS, b + (j + .5) / NS)
                    xi, yi = int(x), int(y)
                    if 0 <= xi < rw and 0 <= yi < rh:
                        tot += 1
                        if rmag[yi * rw + xi]:
                            hit += 1
            cov['%d,%d' % (a, b)] = round(hit / tot, 2) if tot else 0.0
    walk_cov = [cov['%d,%d' % (a, b)] for a in range(fw) for b in range(fh)]
    ring = [cov['%d,%d' % (a, b)] for a in range(-1, fw + 1)
            for b in range(-1, fh + 1) if not (0 <= a < fw and 0 <= b < fh)]
    rec['cellCoverage'] = {
        'walkableMean': round(sum(walk_cov) / len(walk_cov), 3),
        'walkableCellsSeen': sum(1 for c in walk_cov if c >= 0.5),
        'walkableCellsOccluded': sum(1 for c in walk_cov if c < 0.5),
        'ringMax': max(ring), 'ringMean': round(sum(ring) / len(ring), 3),
        'grid': cov,
    }

    # ---- 5. wall-base alignment: fitted edges vs mask boundary ------------
    align = {}
    def edge_offsets(fixed_axis, fixed_u, lo, hi, use_min):
        offs = []
        for p in range(rw * rh):
            if not rmag[p]:
                continue
            x, y = p % rw, p // rw
            u1, u2 = x + 2 * y, 2 * y - x
            var = u2 if fixed_axis == 'u1' else u1
            if not (lo <= var <= hi):
                continue
            offs.append((var, u1 if fixed_axis == 'u1' else u2))
        if not offs:
            return None
        # bin the varying coordinate, take the extreme of the fixed one
        bins = {}
        for v, u in offs:
            key = int(v // 8)
            if key not in bins:
                bins[key] = u
            else:
                bins[key] = min(bins[key], u) if use_min else max(bins[key], u)
        errs = [(u - fixed_u) / 2.0 for u in bins.values()]
        # bins where the floor boundary is far from the fitted edge are
        # OCCLUDED (the near wall hides the floor there), not misaligned —
        # measure alignment only where the edge is actually visible
        vis = [e for e in errs if abs(e) < cell * 0.5]
        if not vis:
            return {'meanPx': None, 'bins': len(errs), 'visibleBins': 0}
        return {'meanPx': round(sum(abs(e) for e in vis) / len(vis), 1),
                'maxPx': round(max(abs(e) for e in vis), 1),
                'bins': len(errs), 'visibleBins': len(vis),
                'occludedBins': len(errs) - len(vis)}
    m1 = cW * 0.5
    align['backRightBase'] = edge_offsets('u2', u2a, u1a + m1, u1b - m1, True)
    align['backLeftBase'] = edge_offsets('u1', u1a, u2a + m1, u2b - m1, True)
    rec['wallBaseAlignment'] = align

    # ---- 6. door: the yellow doormat --------------------------------------
    yel = bytearray(rw * rh)
    for y in range(rh):
        for x in range(rw):
            if is_yellow(*rpx[x, y]):
                yel[y * rw + x] = 1
    yel, yn = largest_component(rw, rh, yel)
    if yn > 800:
        cx = sum(p % rw for p in range(rw * rh) if yel[p]) / yn
        cy = sum(p // rw for p in range(rw * rh) if yel[p]) / yn
        a, b = cellf(cx, cy)
        dj = max(0, min(fh - 1, int(math.floor(b))))
        rec['door'] = {
            'yellowPx': yn, 'matCentroidRect': [round(cx, 1), round(cy, 1)],
            'matCellFloat': [round(a, 2), round(b, 2)],
            'matSide': 'exterior' if a > fw else 'interior',
            'doorWallSegment': [fw, dj],
            'interiorDoorstep': [fw - 1, dj],
            'matchesDeclared': [fw - 1, dj] == list(DECLARED_DOORSTEP),
        }
    else:
        rec['door'] = {'yellowPx': yn, 'interiorDoorstep': list(DECLARED_DOORSTEP),
                       'matSide': None, 'fallback': 'declared cell (mat not found)'}

    # ---- 7. key the shell: cyan bg, magenta floor, yellow mat -> alpha ----
    rgba = Image.new('RGBA', (rw, rh))
    out = rgba.load()
    for y in range(rh):
        for x in range(rw):
            r, g, b = rpx[x, y]
            if is_cyan(r, g, b) or is_magenta(r, g, b) or yel[y * rw + x]:
                out[x, y] = (0, 0, 0, 0)
            elif near_magenta(r, g, b):
                t2 = min(1.0, ((r - g) + (b - g) - 82) / 60.0)
                out[x, y] = (int(g + (r - g) * .35), g,
                             int(g + (b - g) * .35), int(255 * (1 - t2 * .85)))
            elif near_cyan(r, g, b):
                s = (g - r) + (b - r)
                t2 = min(1.0, max(0.0, (s - 43) / 45.0))
                out[x, y] = (r, int(r + (g - r) * .45), int(r + (b - r) * .45),
                             int(255 * (1 - t2 * .9)))
            else:
                out[x, y] = (r, g, b, 255)

    # drop small isolated islands (mark-seam / mat-fringe specks)
    A = rgba.getchannel('A').load()
    op = bytearray(rw * rh)
    for y in range(rh):
        for x in range(rw):
            if A[x, y] > 20:
                op[y * rw + x] = 1
    seen = bytearray(rw * rh)
    dropped = 0
    for start in range(rw * rh):
        if op[start] and not seen[start]:
            comp, stack = [], [start]
            seen[start] = 1
            while stack:
                p = stack.pop()
                comp.append(p)
                x, y = p % rw, p // rw
                for q in (p - 1 if x else -1, p + 1 if x < rw - 1 else -1,
                          p - rw if y else -1, p + rw if y < rh - 1 else -1):
                    if q >= 0 and op[q] and not seen[q]:
                        seen[q] = 1
                        stack.append(q)
            if len(comp) < 1500:
                dropped += len(comp)
                for p in comp:
                    out[p % rw, p // rw] = (0, 0, 0, 0)
                    op[p] = 0
    rec['speckPxRemoved'] = dropped

    # ---- 8. measure the near wall's painted base line + height ------------
    # WALL COLUMNS: image columns whose bottom-most opaque pixel sits near
    # the fitted floor edge R->B (the wall line by construction) AND whose
    # opaque run above it is at least 0.6 cells tall — a real wall, not the
    # thin painted floor rim along the open front edges.
    def floor_edge_y(x):                    # fitted R->B edge, extended
        j = (R[0] - x) / (cH / 2.0)
        return R[1] + j * (cH / 4.0)
    wall_cols = {}
    for x in range(int(B[0]), rw):
        col = [y for y in range(rh) if op[y * rw + x]]
        if not col:
            continue
        bot = max(col)
        if abs(bot - floor_edge_y(x)) > cell * 0.6:
            continue
        run_top = bot
        while run_top > 0 and op[(run_top - 1) * rw + x]:
            run_top -= 1
        if bot - run_top >= cell * 0.6:
            wall_cols[x] = (bot, bot - run_top)
    if wall_cols:
        base_pts = [(x, v[0]) for x, v in wall_cols.items()]
        bm, bb = fit_line(base_pts)
        offs = [abs(py - floor_edge_y(px_)) for px_, py in base_pts]
        heights = sorted(v[1] for v in wall_cols.values())
        # columns where the near wall visually abuts the back-right wall
        # have MERGED opaque runs (no keyed floor between them), inflated by
        # the back wall's height. The CLEAN columns (left end of the wall,
        # and beyond the floor's R corner) measure the true wall height:
        # p20 finds the clean cluster, and the cut uses the tallest clean
        # run (the wall's top rail) so merged columns cut at the rail line
        p20 = heights[len(heights) // 5]
        clean = [h_ for h_ in heights if h_ <= p20 * 1.3]
        h_wall = clean[len(clean) // 2]
        h_cut = clean[-1]
        xw0, xw1 = min(wall_cols), max(wall_cols)
        rec['nearWall'] = {
            'baseSlopeMeasured': round(-bm, 4),
            'baseOffsetMeanPx': round(sum(offs) / len(offs), 1),
            'baseOffsetMaxPx': round(max(offs), 1),
            'heightPx': h_wall,
            'heightCells': round(h_wall / (cell / 2.0), 2),
            'heightCutPx': h_cut,
            'heightPercentiles': {'p20': heights[len(heights) // 5],
                                  'p50': heights[len(heights) // 2],
                                  'p80': heights[len(heights) * 4 // 5]},
            'columnSpan': [xw0, xw1],
            'spanCellsAlongWall': [round((R[0] - xw1) / (cH / 2.0), 2),
                                   round((R[0] - xw0) / (cH / 2.0), 2)],
            'columnsMeasured': len(wall_cols),
        }
    else:
        bm, bb = None, None
        h_wall = h_cut = round(cell * 2.2)
        xw0, xw1 = rw, -1
        rec['nearWall'] = {'error': 'no wall base silhouette found',
                           'heightPx': h_wall}

    # ---- 9. split: near-wall band cut at the measured wall plane ----------
    # near band = opaque pixels within the wall's column span, at or below
    # the measured base line raised by the measured wall height (a pad
    # covers the top rail trim + the end posts)
    PAD_TOP = 16
    PAD_XL, PAD_XR = 26, 8      # left pad covers the wall's end post, whose
                                # columns' bottom-most pixel is the floor rim
    # per-column cut height: where the near wall's opaque run is separated
    # from the back walls by keyed floor, the run's own top IS the cut (the
    # measured silhouette); where the runs merge, cap at the measured height
    # pass 1: columns with a CLEAN wall run (bottom near the base line,
    # height in the plausible wall range) cut at their own silhouette top
    near_top = {}
    if bm is not None:
        gaps = []
        span = range(max(0, xw0 - PAD_XL), min(rw, xw1 + PAD_XR + 1))
        for x in span:
            base = bm * x + bb
            y0_ = min(rh - 1, max(0, int(round(base)) - 2))
            if not op[y0_ * rw + x]:
                continue
            yb = y0_
            while yb < rh - 1 and op[(yb + 1) * rw + x]:
                yb += 1
            yt = y0_
            while yt > 0 and op[(yt - 1) * rw + x]:
                yt -= 1
            if cell * 0.6 <= (yb - yt) <= h_cut * 1.2:
                near_top[x] = yt - 2
                gaps.append(base - near_top[x])
        # pass 2: door columns (bottom strip detached from the door by the
        # keyed mat fringe) and merged columns get the rail line carried
        # over from the good columns: base minus the p80 measured height
        gaps.sort()
        h_fill = gaps[int(len(gaps) * 0.8)] if gaps else h_cut + PAD_TOP
        rec['nearWall']['railHeightFillPx'] = round(h_fill, 1)
        for x in span:
            if x not in near_top:
                near_top[x] = bm * x + bb - h_fill - 4
    back = Image.new('RGBA', (rw, rh), (0, 0, 0, 0))
    near = Image.new('RGBA', (rw, rh), (0, 0, 0, 0))
    bo, no_ = back.load(), near.load()
    near_px = back_px = art_in_poly_back = art_in_poly_near = 0
    M = 0.08                                # boundary margin for solidity count
    for y in range(rh):
        for x in range(rw):
            p = y * rw + x
            if not op[p]:
                continue
            r, g, b, al = out[x, y]
            a_, b_ = cellf(x, y)
            in_poly = M <= a_ <= fw - M and M <= b_ <= fh - M
            is_near = x in near_top and y >= near_top[x]
            if is_near:
                no_[x, y] = (r, g, b, al)
                near_px += 1
                if in_poly:
                    art_in_poly_near += 1
            else:
                bo[x, y] = (r, g, b, al)
                back_px += 1
                if in_poly:
                    art_in_poly_back += 1
    rec['split'] = {
        'nearBandPx': near_px, 'backPx': back_px,
        # THE solidity number: back-layer art over walkable floor cells
        # (boundary rim excluded by an 0.08-cell margin). The old interior
        # failed exactly this — walkable cells under painted walls.
        'backArtInsideFloorPolygonPx': art_in_poly_back,
        'nearArtInsideFloorPolygonPx': art_in_poly_near,
        'insideMarginCells': M,
    }

    # ---- 10. shared crop, save layers + combined shell --------------------
    shell = Image.alpha_composite(back, near)
    bbox = shell.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    cx0, cy0 = bbox[0], bbox[1]
    for img, name in [(back, 'bakint2-back'), (near, 'bakint2-near'),
                      (shell, 'bakint2-shell')]:
        img.crop(bbox).save(os.path.join(outdir, name + '.png'))
    rec['sprites'] = {'back': 'bakint2-back.png', 'near': 'bakint2-near.png',
                      'shell': 'bakint2-shell.png'}
    rec['crop'] = list(bbox)
    rec['anchorSprite'] = [round(anchor[0] - cx0, 1), round(anchor[1] - cy0, 1)]
    rec['fitSprite'] = {k: [round(v[0] - cx0, 1), round(v[1] - cy0, 1)]
                        for k, v in rec['fit'].items()}

    # ---- 11. cyan pockets in the shipped layers ---------------------------
    sp = shell.crop(bbox).load()
    sw, sh_ = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pocket = 0
    for y in range(sh_):
        for x in range(sw):
            r, g, b, a2 = sp[x, y]
            if a2 >= 200 and near_cyan(r, g, b):
                pocket += 1
    rec['cyanPocketCheck'] = {'opaqueNearCyan': pocket, 'pass': pocket == 0}

    # ---- 12. cellScale candidates + floor decision ------------------------
    rec['floorRender'] = ('engine ground supertile f-plank (magenta floor keys '
                         'to transparent; shell ships walls only)')
    rec['cellScale'] = {}
    for S in (1, 1.5, 2):
        per = cell / S
        rec['cellScale'][str(S)] = {
            'S': S, 'engineFoot': [round(fw * S), round(fh * S)],
            'renderScale': round(S * TW / cell, 4),
            'texelHeadroom': round(per / TW, 3),
            'resolutionFloor': {'cellPxPerEngineCell': round(per, 2),
                                'floorPx': TW, 'pass': per >= TW,
                                'upscaleFactor': round(max(1.0, TW / per), 3)},
        }
    return rec


# ---------------------------------------------------------------------------
def slice_props(raw_path, outdir):
    im = Image.open(raw_path).convert('RGB')
    W, H = im.size
    px = im.load()
    recs = {}
    for name, col, row, fw, fh in PROPS:
        x0, y0 = round(col * W / 3), round(row * H / 2)
        x1, y1 = round((col + 1) * W / 3), round((row + 1) * H / 2)
        w, h = x1 - x0, y1 - y0
        mag = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                if is_magenta(*px[x0 + x, y0 + y]):
                    mag[y * w + x] = 1
        comp, n = largest_component(w, h, mag)
        rec = {'declared': [fw, fh], 'region': [x0, y0, w, h], 'markPx': n}
        recs[name] = rec
        if n < 200:
            rec['fit'] = None
            rec['confidence'] = 0.0
            rec['error'] = 'mark missing'
            continue
        u1a, u1b, u2a, u2b, _ = ufit(comp, w, h)
        T, R = uv(u1a, u2a), uv(u1b, u2a)
        B, L = uv(u1b, u2b), uv(u1a, u2b)
        cW, cH = (u1b - u1a) / fw, (u2b - u2a) / fh
        cell = (cW + cH) / 2
        axis_err = abs(cW - cH) / cell
        area = (u1b - u1a) * (u2b - u2a) / 4.0
        fill = n / area if area > 0 else 0
        anchor = ((T[0] + B[0]) / 2, (T[1] + B[1]) / 2)
        conf = max(0.0, 1.0 - min(1, axis_err * 1.5))
        rec.update({
            'fit': {'T': T, 'R': R, 'B': B, 'L': L},
            'cellPx': round(cell, 1),
            'cellPxPerAxis': [round(cW, 1), round(cH, 1)],
            'measured': [round((u1b - u1a) / cell, 2), round((u2b - u2a) / cell, 2)],
            'axisErr': round(axis_err, 3), 'markFill': round(fill, 2),
            'confidence': round(conf, 2),
        })

        # ---- extract sprite: global cyan hue key + magenta key ------------
        rgba = Image.new('RGBA', (w, h))
        out = rgba.load()
        for y in range(h):
            for x in range(w):
                r, g, b = px[x0 + x, y0 + y]
                if is_cyan(r, g, b) or is_magenta(r, g, b):
                    out[x, y] = (0, 0, 0, 0)
                elif near_magenta(r, g, b):
                    t2 = min(1.0, ((r - g) + (b - g) - 82) / 60.0)
                    out[x, y] = (int(g + (r - g) * .35), g,
                                 int(g + (b - g) * .35), int(255 * (1 - t2 * .85)))
                elif near_cyan(r, g, b):
                    s = (g - r) + (b - r)
                    t2 = min(1.0, max(0.0, (s - 43) / 45.0))
                    out[x, y] = (r, int(r + (g - r) * .45),
                                 int(r + (b - r) * .45),
                                 int(255 * (1 - t2 * .9)))
                else:
                    out[x, y] = (r, g, b, 255)
        A = rgba.getchannel('A').point(lambda v: 255 if v > 20 else 0)
        bbox = A.getbbox()
        sprite = rgba.crop(bbox)
        sprite.save(os.path.join(outdir, name + '.png'))
        rec['sprite'] = name + '.png'
        rec['crop'] = list(bbox)
        rec['anchorMark'] = [round(anchor[0] - bbox[0], 1),
                             round(anchor[1] - bbox[1], 1)]
        rec['fitSprite'] = {k: [round(v[0] - bbox[0], 1), round(v[1] - bbox[1], 1)]
                            for k, v in rec['fit'].items()}

        # ---- beside-the-mark detection + base-contact anchor --------------
        # an ON-mark prop HIDES its mark's centre. So sample the magenta
        # coverage of the mark's central half: ~0 for a prop standing on the
        # mark, ~1 when the model stood the prop beside/behind it (the
        # interior sheets' systematic defect for larger props). Overall
        # markFill cannot separate the two when the mark is much larger
        # than the prop's base (stool on an oversized mark).
        e1p = (cW / 2.0, cW / 4.0)
        e2p = (-cH / 2.0, cH / 4.0)
        chit = ctot = 0
        NSC = 9
        for i in range(NSC):
            for j in range(NSC):
                a_ = fw * (0.25 + 0.5 * (i + .5) / NSC)
                b_ = fh * (0.25 + 0.5 * (j + .5) / NSC)
                sxp = T[0] + a_ * e1p[0] + b_ * e2p[0]
                syp = T[1] + a_ * e1p[1] + b_ * e2p[1]
                xi, yi = int(sxp), int(syp)
                if 0 <= xi < w and 0 <= yi < h:
                    ctot += 1
                    if comp[yi * w + xi]:
                        chit += 1
        center_fill = chit / ctot if ctot else 0.0
        rec['markCenterFill'] = round(center_fill, 2)
        sp = sprite.load()
        sw, sh_ = sprite.size
        ys_bot = sh_ - 1
        rows = []
        for y in range(sh_ - 1, max(-1, sh_ - 9), -1):
            xs = [x for x in range(sw) if sp[x, y][3] > 128]
            if xs:
                rows += [(x, y) for x in xs]
        if rows:
            fx = sum(p[0] for p in rows) / len(rows)
            fy = max(p[1] for p in rows)
            # anchor = footprint centre from the front corner + cellPx
            ax = fx + (fh - fw) * cell / 4.0
            ay = fy - (fw + fh) * cell / 4.0
            rec['anchorBaseContact'] = [round(ax, 1), round(ay, 1)]
        beside = center_fill > 0.5
        rec['besideMark'] = beside
        rec['anchorMode'] = 'baseContact' if beside else 'mark'
        rec['anchorSprite'] = (rec.get('anchorBaseContact') or rec['anchorMark']) \
            if beside else rec['anchorMark']
    return recs


def main():
    mode, raw = sys.argv[1], sys.argv[2]
    outdir = sys.argv[3] if len(sys.argv) > 3 else 'public/assets/iso/interior'
    os.makedirs(outdir, exist_ok=True)
    mpath = os.path.join(outdir, 'interior-metrics.json')
    metrics = {}
    if os.path.exists(mpath):
        with open(mpath) as f:
            metrics = json.load(f)
    if mode == 'shell':
        rec = slice_shell(raw, outdir)
        metrics['room'] = rec
        if 'error' in rec:
            print('SHELL:', rec['error'])
        else:
            print('shell: slope %.3f -> rectify x%.3f/y%.3f  cell %spx (%s/%s)  '
                  'conf %.2f  measured %s' %
                  (rec['paintedSlope'], rec['rectify']['xStretch'],
                   rec['rectify']['ySquash'], rec['cellPx'],
                   *rec['cellPxPerAxis'], rec['confidence'], rec['measured']))
            d = rec['door']
            print('  door: mat %s px at cell %s (%s) -> wall seg %s, doorstep %s (%s)'
                  % (d.get('yellowPx'), d.get('matCellFloat'), d.get('matSide'),
                     d.get('doorWallSegment'), d.get('interiorDoorstep'),
                     'MATCHES declared' if d.get('matchesDeclared') else
                     'declared was %s' % (DECLARED_DOORSTEP,)))
            nw = rec['nearWall']
            print('  near wall: base offset mean %s px (max %s), height %s px '
                  '= %s cells, %s columns' %
                  (nw.get('baseOffsetMeanPx'), nw.get('baseOffsetMaxPx'),
                   nw.get('heightPx'), nw.get('heightCells'),
                   nw.get('columnsMeasured')))
            s = rec['split']
            print('  split: near %d px, back %d px; back art inside floor '
                  'polygon: %d px  <- solidity by construction' %
                  (s['nearBandPx'], s['backPx'],
                   s['backArtInsideFloorPolygonPx']))
            print('  coverage: walkable mean %.2f (%d seen / %d occluded by '
                  'near wall), ring max %.2f' %
                  (rec['cellCoverage']['walkableMean'],
                   rec['cellCoverage']['walkableCellsSeen'],
                   rec['cellCoverage']['walkableCellsOccluded'],
                   rec['cellCoverage']['ringMax']))
            print('  cyan pockets: %d -> %s' %
                  (rec['cyanPocketCheck']['opaqueNearCyan'],
                   'PASS' if rec['cyanPocketCheck']['pass'] else 'FAIL'))
            for S, cs in rec['cellScale'].items():
                rf = cs['resolutionFloor']
                print('  S=%s: engine %s, renderScale %s, %s px/engine-cell %s'
                      % (S, cs['engineFoot'], cs['renderScale'],
                         rf['cellPxPerEngineCell'],
                         'PASS' if rf['pass'] else
                         'UPSCALE x%s' % rf['upscaleFactor']))
    elif mode == 'props':
        recs = slice_props(raw, outdir)
        metrics['props'] = recs
        metrics['propsRaw'] = os.path.basename(raw)
        for name, rec in recs.items():
            if not rec.get('fit'):
                print('%-10s MARK MISSING' % name)
                continue
            print('%-10s conf %.2f  cell %spx (%s/%s)  fill %.2f  centre %.2f  '
                  '%s  anchor %s'
                  % (name, rec['confidence'], rec['cellPx'],
                     *rec['cellPxPerAxis'], rec['markFill'],
                     rec['markCenterFill'],
                     'BESIDE-MARK -> baseContact' if rec['besideMark']
                     else 'on-mark', rec['anchorSprite']))
    else:
        print('usage: slice_interior.py shell|props RAW.png [OUTDIR]')
        sys.exit(1)
    with open(mpath, 'w') as f:
        json.dump(metrics, f, indent=1)


if __name__ == '__main__':
    main()
