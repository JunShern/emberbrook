#!/usr/bin/env python3
"""Headless mask baker — Python port of public/js/bake-core.js (must stay in sync).
Bakes a 336x192 walkability bitmap from a flood image, using a per-scene
JSON config for corridors/segments and POIs.

Flood key is AUTO-DETECTED per maskraw:
  - legacy GREEN flood  -> v1 pipeline (strict threshold, close r=3, dilate 1)
  - MAGENTA flood       -> v2 pipeline (loose threshold — magenta is absent
    from the art so tolerance can be generous; close r=2; NO blanket dilate;
    gradient edge-snap against the painting's own edges)

Usage: python3 tools/bakemask.py SCENE_DIR [--threshold-only] [--out FILE]
  SCENE_DIR must contain maskraw.png and bake.json:
    { "corridors": [{"x":..,"y":..,"w":..,"h":..,"label":".."}],
      "segments":  [{"pts":[[x,y],...],"w":..,"label":".."}],   # polyline corridors
      "pois": [[x,y],...], "center": [x,y], "blockedRects": [...] }
Writes SCENE_DIR/mask.png and prints a report (mode, coverage, carves, and the
SLOP METRIC: walkable cells sitting on strong image edges, as % of the whole
grid — computed for the shipped mask.png (before) and the new bake (after); it
should drop. Grid-normalized on purpose: dividing by walkable-cell count
instead punishes tight masks (an old sloppy mask covering big FLAT surfaces —
water, lock walls — dilutes its own edge fraction).
  --threshold-only: experimental minimal bake — threshold on the 4px grid +
    authored corridors/segments/blockedRects, and NOTHING else.
  --out FILE: write the mask somewhere other than SCENE_DIR/mask.png.
"""
import sys, os, json, math
from PIL import Image

W, H, S = 336, 192, 4
FW, FH = 1344, 768

CFG = {
    'green':   {'min': 90, 'ratio': 1.25},          # v1 strict key (scene greens exist)
    'magenta': {'rgDiff': 50, 'bgDiff': 40},        # v2 loose key (magenta absent from art)
    'speckMax': 8,
    'bayFillR': 4,
    'v1': {'closeR': 3, 'dilateR': 1, 'snap': False},
    'v2': {'closeR': 2, 'dilateR': 0, 'snap': True},
    'snapScan': 3,      # edge-snap: look up to 3 cells out for a drawn edge
    'slopPct': 85,      # strong-edge threshold = p85 of per-cell mean sobel
}

def pass_(m, hit, r):
    out = bytearray(W * H)
    for y in range(H):
        for x in range(W):
            v = 0 if hit else 1
            done = False
            for dy in range(-r, r + 1):
                ny = y + dy
                if ny < 0 or ny >= H: continue
                base = ny * W
                for dx in range(-r, r + 1):
                    nx = x + dx
                    if 0 <= nx < W and m[base + nx] == (1 if hit else 0):
                        v = 1 if hit else 0; done = True; break
                if done: break
            out[y * W + x] = v
    return out

def components(m, val):
    comp = [-1] * (W * H)
    out = []
    for i in range(W * H):
        if m[i] != val or comp[i] != -1: continue
        q, cells = [i], []
        comp[i] = len(out)
        touches = False
        while q:
            c = q.pop(); cells.append(c)
            cx, cy = c % W, c // W
            if cx == 0 or cy == 0 or cx == W - 1 or cy == H - 1: touches = True
            for d in (-1, 1, -W, W):
                n = c + d
                if n < 0 or n >= W * H or abs((n % W) - cx) > 1: continue
                if m[n] == val and comp[n] == -1:
                    comp[n] = len(out); q.append(n)
        out.append((cells, touches))
    return out

# ---------- flood key ----------

def is_green(r, g, b):
    G = CFG['green']
    return g > G['min'] and g > r * G['ratio'] and g > b * G['ratio']

def is_magenta(r, g, b):
    M = CFG['magenta']
    return r - g > M['rgDiff'] and b - g > M['bgDiff']

def detect_key(px):
    """magenta wins if it hits more cells than green does (magenta never
    appears in the art, green does — moss/hull-paint/water)."""
    gn = sum(1 for r, g, b in px if is_green(r, g, b))
    mg = sum(1 for r, g, b in px if is_magenta(r, g, b))
    return 'magenta' if mg > gn else 'green'

# ---------- painting edges (sobel), for edge-snap + slop metric ----------

def edge_cells(scene_im):
    """Per-grid-cell MEAN of L1 sobel magnitude over the full-res painting,
    plus the strong-edge threshold (p'slopPct' of all cells)."""
    im = scene_im.convert('RGB').resize((FW, FH))
    px = im.tobytes()
    lum = bytearray(FW * FH)
    for i in range(FW * FH):
        lum[i] = (px[i*3] * 77 + px[i*3+1] * 151 + px[i*3+2] * 28) >> 8
    csum = [0] * (W * H)
    for y in range(1, FH - 1):
        r0 = (y - 1) * FW; r1 = y * FW; r2 = (y + 1) * FW
        crow = (y >> 2) * W
        for x in range(1, FW - 1):
            a = lum[r0+x-1]; b = lum[r0+x]; c = lum[r0+x+1]
            d = lum[r1+x-1];                f = lum[r1+x+1]
            g = lum[r2+x-1]; h = lum[r2+x]; i2 = lum[r2+x+1]
            gx = (c + 2*f + i2) - (a + 2*d + g)
            gy = (g + 2*h + i2) - (a + 2*b + c)
            csum[crow + (x >> 2)] += abs(gx) + abs(gy)
    E = [s // 16 for s in csum]
    srt = sorted(E)
    T = srt[min(len(srt) - 1, len(srt) * CFG['slopPct'] // 100)]
    return E, T

def slop(m, E, T):
    """Walkable cells on strong edges, as % of the WHOLE grid (see module doc
    for why not % of walkable)."""
    hits = sum(1 for i in range(W * H) if m[i] and E[i] >= T)
    return hits * 100.0 / (W * H)

def edge_snap(m, E, T):
    """Expansion-only boundary snap: where the mask stops short of the drawn
    boundary, walk outward up to snapScan cells; if a strong-edge cell is
    found, fill the low-gradient cells between (never the edge cell itself).
    Cannot disconnect anything (only adds cells)."""
    R = CFG['snapScan']
    add = []
    for y in range(H):
        for x in range(W):
            i = y * W + x
            if not m[i]: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or m[ny * W + nx]: continue
                fill = []
                for k in range(1, R + 1):
                    px2, py2 = x + dx * k, y + dy * k
                    if not (0 <= px2 < W and 0 <= py2 < H): fill = []; break
                    j = py2 * W + px2
                    if m[j]: fill = []; break
                    if E[j] >= T: break          # drawn edge: fill up to it
                    fill.append(j)
                else:
                    fill = []                    # no edge within reach: no fill
                add.extend(fill)
    n = 0
    for j in add:
        if not m[j]: m[j] = 1; n += 1
    return n

# ---------- authored geometry ----------

def stamp_rect(m, r, val):
    for y in range(r['y'] // S, -(-(r['y'] + r['h']) // S)):
        for x in range(r['x'] // S, -(-(r['x'] + r['w']) // S)):
            if 0 <= x < W and 0 <= y < H: m[y * W + x] = val

def stamp_segment(m, seg):
    """Polyline corridor: cells whose center lies within w/2 of the path."""
    hw = seg['w'] / 2.0
    pts = seg['pts']
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        x0 = int((min(x1, x2) - hw) // S); x3 = int((max(x1, x2) + hw) // S) + 1
        y0 = int((min(y1, y2) - hw) // S); y3 = int((max(y1, y2) + hw) // S) + 1
        vx, vy = x2 - x1, y2 - y1
        L2 = vx * vx + vy * vy
        for gy in range(max(0, y0), min(H, y3)):
            cy = gy * S + S / 2.0
            for gx in range(max(0, x0), min(W, x3)):
                cx = gx * S + S / 2.0
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((cx - x1) * vx + (cy - y1) * vy) / L2))
                dx, dy = cx - (x1 + vx * t), cy - (y1 + vy * t)
                if dx * dx + dy * dy <= hw * hw: m[gy * W + gx] = 1

# ---------- bake ----------

def load_scene_image(scene_dir):
    for cand in ('festival.png', 'main.png', 'gray.png'):
        p = os.path.join(scene_dir, cand)
        if os.path.exists(p): return Image.open(p)
    return None

def bake(scene_dir, threshold_only=False, out_path=None):
    cfg = json.load(open(os.path.join(scene_dir, 'bake.json')))
    raw = Image.open(os.path.join(scene_dir, 'maskraw.png')).convert('RGB').resize((W, H))
    px = list(raw.getdata())

    key = detect_key(px)
    V = CFG['v2'] if key == 'magenta' else CFG['v1']
    test = is_magenta if key == 'magenta' else is_green
    m = bytearray(W * H)
    for i, (r, g, b) in enumerate(px):
        m[i] = 1 if test(r, g, b) else 0

    scene_im = load_scene_image(scene_dir)
    E = T = None
    if scene_im is not None:
        E, T = edge_cells(scene_im)

    # shipped mask (for the before/after slop report)
    slop_before = None
    shipped = os.path.join(scene_dir, 'mask.png')
    if E is not None and os.path.exists(shipped):
        sm = Image.open(shipped).convert('L').resize((W, H), Image.NEAREST)
        slop_before = slop([1 if v > 127 else 0 for v in sm.getdata()], E, T)

    if not threshold_only:
        # close (v1 r=3, v2 r=2)
        m = pass_(m, True, V['closeR']); m = pass_(m, False, V['closeR'])
        # heal interior specks (<8 cells)
        for cells, touches in components(m, 0):
            if not touches and len(cells) < CFG['speckMax']:
                for c in cells: m[c] = 1
        # bay-fill (close blocked r=4)
        m = pass_(m, False, CFG['bayFillR']); m = pass_(m, True, CFG['bayFillR'])
    # authored corridors: legacy rects + polyline segments
    for c in cfg.get('corridors', []): stamp_rect(m, c, 1)
    for s in cfg.get('segments', []): stamp_segment(m, s)
    snapped = 0
    if not threshold_only:
        # v1: blanket dilate 1; v2: none (boundary fidelity)
        if V['dilateR']: m = pass_(m, True, V['dilateR'])
        for cells, touches in components(m, 0):
            if not touches and len(cells) < CFG['speckMax']:
                for c in cells: m[c] = 1
        # v2: edge-snap the boundary out to the painting's own drawn edges
        if V['snap'] and E is not None:
            snapped = edge_snap(m, E, T)
    # clearance carve
    CLR = 2
    cx0, cy0 = cfg.get('center', [672, 620])
    ccx, ccy = cx0 // S, cy0 // S
    def clear_map():
        cl = bytearray(W * H)
        for y in range(CLR, H - CLR):
            for x in range(CLR, W - CLR):
                ok = 1
                for dy in range(-CLR, CLR + 1):
                    base = (y + dy) * W
                    for dx in range(-CLR, CLR + 1):
                        if not m[base + x + dx]: ok = 0; break
                    if not ok: break
                cl[y * W + x] = ok
        return cl
    def reach_clear():
        cl = clear_map()
        seen = bytearray(W * H)
        q = []
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                i2 = (ccy + dy) * W + ccx + dx
                if 0 <= i2 < W * H and cl[i2] and not seen[i2]:
                    seen[i2] = 1; q.append(i2)
        while q:
            c = q.pop(); qx = c % W
            for d in (-1, 1, -W, W):
                n = c + d
                if n < 0 or n >= W * H or abs((n % W) - qx) > 1: continue
                if cl[n] and not seen[n]: seen[n] = 1; q.append(n)
        return seen
    # authored blocked rects (e.g. tall props that must not be walked behind)
    for r in cfg.get('blockedRects', []): stamp_rect(m, r, 0)
    carved = 0
    for px2, py2 in (cfg.get('pois', []) if not threshold_only else []):
        seen = reach_clear()
        gx, gy = px2 // S, py2 // S
        ok = any(0 <= gx+dx < W and 0 <= gy+dy < H and seen[(gy+dy)*W + gx+dx]
                 for dy in range(-3, 4) for dx in range(-3, 4))
        if ok: continue
        steps = max(abs(ccx - gx), abs(ccy - gy), 1)
        for t in range(steps + 1):
            x = round(gx + (ccx - gx) * t / steps)
            y = round(gy + (ccy - gy) * t / steps)
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H: m[ny * W + nx] = 1
        carved += 1
    out = Image.new('L', (W, H))
    out.putdata([255 if v else 0 for v in m])
    dest = out_path or os.path.join(scene_dir, 'mask.png')
    out.convert('RGB').save(dest)
    cov = sum(m) * 100 // (W * H)
    mode = 'threshold-only' if threshold_only else ('v2-magenta' if key == 'magenta' else 'v1-green')
    nseg = len(cfg.get('segments', []))
    nrect = len(cfg.get('corridors', []))
    print(f'baked {dest}  mode={mode}  coverage={cov}%  carved={carved}'
          f'  corridors={nrect} rects + {nseg} segments'
          + (f'  snapped={snapped} cells' if snapped else ''))
    if E is not None:
        after = slop(m, E, T)
        bef = f'{slop_before:.1f}%' if slop_before is not None else 'n/a'
        print(f'slop (walkable cells on strong edges, p{CFG["slopPct"]} T={T}): '
              f'before(shipped)={bef}  after={after:.1f}%')
    # sanity: every POI walkable?
    bad = [(x, y) for x, y in cfg.get('pois', []) if not m[(y // S) * W + (x // S)]]
    if bad: print('WARNING: POIs still blocked:', bad)
    return carved

if __name__ == '__main__':
    argv = sys.argv[1:]
    thr = '--threshold-only' in argv
    outp = None
    if '--out' in argv:
        outp = argv[argv.index('--out') + 1]
    pos = [a for i, a in enumerate(argv)
           if not a.startswith('--') and (i == 0 or argv[i - 1] != '--out')]
    bake(pos[0], threshold_only=thr, out_path=outp)
