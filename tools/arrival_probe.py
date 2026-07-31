#!/usr/bin/env python3
"""arrival_probe.py — CAN THE SHOT SEE THE PLAYER AT THE MOMENT SHE ARRIVES?

    python3 tools/arrival_probe.py <shot> <x> <up> <-y> [--label ...]
    python3 tools/arrival_probe.py --scenegraph          # every door + cut arrival
    python3 tools/arrival_probe.py --scenegraph --shot shelf-west
    python3 tools/arrival_probe.py --town emberbrook --scenegraph

Coordinates are RUNTIME `[x, up, -y]`, exactly as `scenegraph.json` `spawn` and
`dellhollow.cameras.json` `arrivals` write them — so a number can be copied from
one file to the other and to this tool without ever being converted, which is the
whole of the Lock Five lesson (an arrival authored in map order sat 29 m in the
air and the checker had to catch it).

WHY A SEPARATE TOOL FROM shot_probe.py.  `shot_probe` asks how much of a WALK
EDGE a shot can see.  seam-canon §10.2's third sub-signal is a different and
sharper question — `composite.occludedFrac`, "arrives invisible" — and it is
about ONE point and ONE instant: the frame the player materialises in.  Four of
Dellhollow's sixteen arrivals are behind foreground geometry, and `cine_test` §B
passes all sixteen because ON SCREEN is not VISIBLE (§9.2).

METHOD.  Rasterise the character's own box — `charH` tall, 0.42 m wide, sampled
on a grid — project every sample through the shot's baked camera and compare with
the baked view-space depth at that pixel.  Reported as three numbers, because
they fail differently:

    drawnPx      samples that land on screen at all      (cine_test §B's question)
    visible%     samples the depth plate does not bury   (the real one)
    chest%       the same for the 0.9..1.4 m band        (what a player reads as
                                                          "I can see myself")

The 3x3 max on the depth read is shot_probe's: a one-pixel sliver of railing is
not an occluder, and without it a handrail in front of a shoulder reads as a
wall.  Only valid while the shipped plate matches the solved camera — the same
caveat, for the same reason.
"""
import json, sys, math
import numpy as np
from PIL import Image

ROOT = '/Users/junshernchan/projects/multiplayer-rpg/'
# THE TOWN. One flag picks the cinematic bundle; nothing else here knows a town's name,
# so a second town probes its arrivals with no edit (the house convention -- see
# tools/seam_test.mjs, cine_solve.mjs, cine_bake.py). Default stays Dellhollow, so every
# invocation already written keeps working byte for byte.
_a = sys.argv[1:]
TOWN = _a[_a.index('--town') + 1] if '--town' in _a else 'dellhollow'
SCENE = json.load(open(ROOT + 'public/townmap/%s.cameras.json' % TOWN))['sceneKey']
BUNDLE = 'public/assets/scenes/%s/' % SCENE
CINE = json.load(open(ROOT + BUNDLE + 'cine.json'))
CAM = {c['id']: c for c in CINE['cameras']}
CHARH = 1.7
CHARW = 0.42
_plates = {}


def plate(cid):
    if cid not in _plates:
        c = CAM[cid]
        d = c['depth']
        img = np.asarray(Image.open(ROOT + BUNDLE + c['art']['depth']).convert('RGB'),
                         dtype=np.float64)
        dep = d['near'] + (d['far'] - d['near']) * (
            img[:, :, 0] * 65536 + img[:, :, 1] * 256 + img[:, :, 2]) / 16777215.0
        pos, aim = np.array(c['pos'], float), np.array(c['aim'], float)
        f = aim - pos
        f /= np.linalg.norm(f)
        r = np.cross(f, [0, 0, 1.0])
        r = np.array([1.0, 0, 0]) if np.linalg.norm(r) < 1e-6 else r / np.linalg.norm(r)
        u = np.cross(r, f)
        u /= np.linalg.norm(u)
        if u[2] < 0:
            r = -r
            u = np.cross(r, f)
            u /= np.linalg.norm(u)
        ty = math.tan(math.radians(c['fov']) / 2)
        _plates[cid] = (dep, pos, f, r, u, ty * (d['width'] / d['height']), ty,
                        d['width'], d['height'])
    return _plates[cid]


def rt2map(p):
    """runtime [x, up, -y] -> the blend/cine world [x, y, z-up]."""
    return np.array([p[0], -p[2], p[1]], float)


def probe(cid, rt, nu=7, nv=13):
    """rt is a RUNTIME point standing on the ground."""
    dep, pos, f, r, u, tx, ty, W, H = plate(cid)
    base = rt2map(rt)
    drawn = vis = tot = 0
    cdrawn = cvis = 0
    for iu in range(nu):
        su = (iu / (nu - 1) - 0.5) * CHARW
        for iv in range(nv):
            h = 0.06 + (CHARH - 0.12) * iv / (nv - 1)
            chest = 0.90 <= h <= 1.40
            # the character's width is spread across the camera's own right vector,
            # so the box is measured as the shot sees it and not in world x
            p = base + r * su + np.array([0.0, 0.0, h])
            q = p - pos
            z = float(np.dot(q, f))
            tot += 1
            if z <= 1e-6:
                continue
            sx = float(np.dot(q, r)) / z / tx
            sy = float(np.dot(q, u)) / z / ty
            if abs(sx) > 1 or abs(sy) > 1:
                continue
            drawn += 1
            cdrawn += chest
            px = int(min(W - 1, max(0, (sx * 0.5 + 0.5) * W)))
            py = int(min(H - 1, max(0, (0.5 - sy * 0.5) * H)))
            zb = dep[max(0, py - 1):py + 2, max(0, px - 1):px + 2].max()
            if zb >= z - 0.35:
                vis += 1
                cvis += chest
    return dict(shot=cid, at=[round(v, 3) for v in rt], samples=tot, drawn=drawn,
                drawnPct=round(100 * drawn / tot, 1),
                visiblePct=round(100 * vis / tot, 1),
                chestPct=round(100 * cvis / cdrawn, 1) if cdrawn else 0.0)


def main():
    a = [x for x in sys.argv[1:] if x != '--town' and x != TOWN] if '--town' in sys.argv else sys.argv[1:]
    if a and a[0] == '--scenegraph':
        only = a[a.index('--shot') + 1] if '--shot' in a else None
        SG = json.load(open(ROOT + 'public/world/scenegraph.json'))
        rows = []
        for e in SG['edges']:
            cam = (e.get('cam') or {}).get('key')
            if not cam or cam not in CAM or not e.get('spawn'):
                continue
            if only and cam != only:
                continue
            rows.append((e['kind'], e['id'], cam, e['spawn']))
        print('%-5s %-10s %8s %9s %8s  %s' % ('kind', 'shot', 'drawnPx', 'visible%',
                                              'chest%', 'edge'))
        for kind, eid, cam, sp in sorted(rows):
            r = probe(cam, sp)
            flag = '  <-- ARRIVES INVISIBLE' if r['chestPct'] < 50 else ''
            print('%-5s %-10s %8d %8.1f%% %7.1f%%  %s%s'
                  % (kind, cam, r['drawn'], r['visiblePct'], r['chestPct'], eid, flag))
        return
    cid = a[0]
    rt = [float(a[1]), float(a[2]), float(a[3])]
    r = probe(cid, rt)
    print(json.dumps(r))


if __name__ == '__main__':
    main()
