#!/usr/bin/env python3
"""Headless mask baker — Python port of public/js/bake-core.js (must stay in sync).
Bakes a 336x192 walkability bitmap from a green-flood image, using a per-scene
JSON config for corridors and POIs.

Usage: python3 tools/bakemask.py SCENE_DIR
  SCENE_DIR must contain maskraw.png and bake.json:
    { "corridors": [{"x":..,"y":..,"w":..,"h":..,"label":".."}],
      "pois": [[x,y],...], "center": [x,y] }
Writes SCENE_DIR/mask.png and prints a report (carved corridors, coverage).
"""
import sys, os, json
from PIL import Image

W, H, S = 336, 192, 4

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

def bake(scene_dir):
    cfg = json.load(open(os.path.join(scene_dir, 'bake.json')))
    raw = Image.open(os.path.join(scene_dir, 'maskraw.png')).convert('RGB').resize((W, H))
    px = list(raw.getdata())
    m = bytearray(W * H)
    for i, (r, g, b) in enumerate(px):
        m[i] = 1 if (g > 90 and g > r * 1.25 and g > b * 1.25) else 0
    # close (r=3)
    m = pass_(m, True, 3); m = pass_(m, False, 3)
    # heal interior specks (<8 cells)
    for cells, touches in components(m, 0):
        if not touches and len(cells) < 8:
            for c in cells: m[c] = 1
    # bay-fill (close blocked r=4)
    m = pass_(m, False, 4); m = pass_(m, True, 4)
    # corridors
    for c in cfg.get('corridors', []):
        for y in range(c['y'] // S, -(-(c['y'] + c['h']) // S)):
            for x in range(c['x'] // S, -(-(c['x'] + c['w']) // S)):
                if 0 <= x < W and 0 <= y < H: m[y * W + x] = 1
    # dilate walkable 1 + despeck
    m = pass_(m, True, 1)
    for cells, touches in components(m, 0):
        if not touches and len(cells) < 8:
            for c in cells: m[c] = 1
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
    carved = 0
    for px2, py2 in cfg.get('pois', []):
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
    out.convert('RGB').save(os.path.join(scene_dir, 'mask.png'))
    cov = sum(m) * 100 // (W * H)
    print(f'baked {scene_dir}/mask.png  coverage={cov}%  carved={carved}')
    # sanity: every POI walkable?
    bad = [(x, y) for x, y in cfg.get('pois', []) if not m[(y // S) * W + (x // S)]]
    if bad: print('WARNING: POIs still blocked:', bad)
    return carved

if __name__ == '__main__':
    bake(sys.argv[1])
