#!/usr/bin/env python3
"""shot_probe.py — measure, against the SHIPPED baked depth maps, how much of a given
walk edge each camera can actually SEE.

    python3 tools/shot_probe.py <edge>  [shot ...]
    python3 tools/shot_probe.py valley-gate__inn gate shelf-west

WHY. "The boatyard shot is almost completely occluded by this one roof" and "the gate
staircase is visible from NEITHER the gate nor the west shelf" are both OCCLUSION
reports, and no offline tool could answer them: cine_solve knows whether a region is
IN FRAME, which is a different question from whether you can SEE it. The gate stair
measured 100% on-screen in both shots and 12.2% / 25.6% VISIBLE -- so exit-seam framing,
which puts seams in frame, could not have fixed it, and we would have re-baked and still
been wrong.

This is public/js/route_overlay.js ROUTES.probe() done offline against the shipped
plates, so the answer costs seconds instead of a bake. It is only valid while the shipped
plate still matches the solved camera (cine_test asserts exactly that in its CHAIN
section): after a re-solve that moves a camera, re-bake before trusting it.

This is tools/route_overlay.js ROUTES.probe() done offline: project each sample of the
flight (feet and head) through the baked camera, decode the baked view-space depth at
that pixel, and compare. If the surface the camera rendered is nearer than the sample,
something is in the way.

Only valid while the shipped plate matches the solved camera. gate and shelf-west moved
6 mm in the surgery re-solve, so their tranche-2 depth maps are still authoritative.
"""
import json, sys, math
import numpy as np
from PIL import Image

ROOT = '/Users/junshernchan/projects/multiplayer-rpg/'
CINE = json.load(open(ROOT + 'public/assets/scenes/del-cine/cine.json'))
MAP = json.load(open(ROOT + 'public/townmap/dellhollow.map.json'))
LM = {l['id']: l for l in MAP['landmarks']}
CAM = {c['id']: c for c in CINE['cameras']}
CHARH = 1.7

def edge_pts(key, n=40):
    fr, to = key.split('__')
    e = next(x for x in MAP['edges'] if x['from'] == fr and x['to'] == to)
    pts = [LM[fr]['pos']] + (e.get('waypoints') or []) + [LM[to]['pos']]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0]-a[0], b[1]-a[1]))
    L = cum[-1]
    out = []
    for i in range(n + 1):
        s = L * i / n
        for j in range(len(cum) - 1):
            if s <= cum[j+1] or j == len(cum) - 2:
                seg = cum[j+1] - cum[j]
                f = 0 if seg < 1e-9 else (s - cum[j]) / seg
                a, b = pts[j], pts[j+1]
                out.append([a[k] + (b[k]-a[k]) * f for k in range(3)])
                break
    return out, L

def basis(pos, aim):
    f = np.array(aim, float) - np.array(pos, float); f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0])
    r = np.array([1.0, 0, 0]) if np.linalg.norm(r) < 1e-6 else r / np.linalg.norm(r)
    u = np.cross(r, f); u /= np.linalg.norm(u)
    if u[2] < 0: r, u = -r, np.cross(-r, f) / np.linalg.norm(np.cross(-r, f))
    return f, r, u

def probe(cid, key, n=40):
    c = CAM[cid]
    pos, aim, fov = np.array(c['pos'], float), np.array(c['aim'], float), c['fov']
    d = c['depth']; near, far, W, H = d['near'], d['far'], d['width'], d['height']
    img = np.asarray(Image.open(ROOT + 'public/assets/scenes/del-cine/' + c['art']['depth']).convert('RGB'), dtype=np.float64)
    dep = near + (far - near) * (img[:, :, 0]*65536 + img[:, :, 1]*256 + img[:, :, 2]) / 16777215.0
    f, r, u = basis(pos, aim)
    ty = math.tan(math.radians(fov) / 2); tx = ty * 1.75
    pts, L = edge_pts(key, n)
    onscreen = vis = 0; tot = 0; runs = []; cur = 0
    for p in pts:
        for h in (0.35, CHARH):                       # ankle-ish and head
            q = np.array([p[0], p[1], p[2] + h]) - pos
            z = float(np.dot(q, f))
            tot += 1
            if z <= 1e-6: continue
            sx = float(np.dot(q, r)) / z / tx
            sy = float(np.dot(q, u)) / z / ty
            if abs(sx) > 1 or abs(sy) > 1: continue
            onscreen += 1
            px = int(min(W-1, max(0, (sx*0.5+0.5)*W)))
            py = int(min(H-1, max(0, (0.5-sy*0.5)*H)))
            # 3x3 min: a 1-px sliver of railing should not read as full occlusion
            zb = dep[max(0,py-1):py+2, max(0,px-1):px+2].max()
            if zb >= z - 0.35: vis += 1
    return dict(shot=cid, edge=key, samples=tot, onScreenPct=round(100*onscreen/tot, 1),
                visiblePct=round(100*vis/tot, 1), lenM=round(L, 2))

if __name__ == '__main__':
    edge = sys.argv[1] if len(sys.argv) > 1 else 'valley-gate__inn'
    shots = sys.argv[2:] or ['gate', 'shelf-west']
    print(f'{"shot":<14}{"edge":<28}{"on-screen%":>11}{"VISIBLE%":>10}')
    for s in shots:
        r = probe(s, edge)
        print(f'{r["shot"]:<14}{r["edge"]:<28}{r["onScreenPct"]:>11}{r["visiblePct"]:>10}')
