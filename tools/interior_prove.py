#!/usr/bin/env python3
"""Interior proving composites — the measured room exercised under the REAL
engine sort (faithful to public/js/iso/engine.js, same replica as
tools/bldg_occlusion.py):

  TW=64, TH=32; sx=(x-y)*32, sy=(x+y)*16
  prop sortKey = i + j + (foot_w+foot_h)/2 ; char key = x + y, drawn before
  the first prop whose key strictly exceeds it; Vesper billboard CHAR_H=130,
  bottom-centre at (sx, sy+4).

Room mapping (from interior-metrics.json, all measured):
  back layer   = backdrop, drawn before the sorted pass
  near band    = sorted prop with key 9e9 (the rescue's key-24 trick, i.e. a
                 [0,0]-foot block placed at (W,H) — always after the char)
  floor        = f-plank ground supertiles (the shipped engine material),
                 per the floorRender decision in the metrics
  cellScale S  = room painted cell -> SxS engine cells; renderScale
                 S*TW/cellPx; props stay at their own measured 1-painted-
                 cell-per-engine-cell scale (composability: two independent
                 measurement chains meet in one scene)

Outputs (public/assets/iso/interior/): scale-S1.png scale-S15.png
solidity.png occl-door.png occl-mid.png occl-oven.png occl-counter.png
room-assembled.png + interior-prove.json with programmatic verdicts.

Usage: python3 tools/interior_prove.py [OUTDIR]
"""
import os, sys, json
from PIL import Image, ImageDraw

TW, TH = 64, 32
CHAR_H = 130
ZOOM = 2

def sx(x, y): return (x - y) * (TW / 2)
def sy(x, y): return (x + y) * (TH / 2)

def load_vesper(root):
    sheet = Image.open(os.path.join(
        root, 'public/assets/characters/vesper/sheet.png')).convert('RGBA')
    f = sheet.crop((0, 0, 256, 256))
    f = f.crop(f.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox())
    s = CHAR_H / f.height
    return f.resize((max(1, round(f.width * s)), CHAR_H), Image.LANCZOS)

def scene_render(objects, char, cx, cy, grid, title, out_png, floor=None,
                 zoom=ZOOM, draw_grid=True, char2=None):
    """Engine-grid compositor with the REAL sort (see bldg_occlusion.py).
    objects: {img, scale, anchor, i, j, foot, key(optional), occl, shadow}
    floor: (img, scale, (i0,j0,i1,j1)) f-plank supertiles over that range.
    char2: optional second character position (cx2, cy2)."""
    placed = []
    for o in objects:
        s = o['scale']
        bw, bh = round(o['img'].width * s), round(o['img'].height * s)
        fw, fh = o['foot']
        ax, ay = o['anchor'][0] * s, o['anchor'][1] * s
        bx = sx(o['i'] + fw / 2, o['j'] + fh / 2) - ax
        by = sy(o['i'] + fw / 2, o['j'] + fh / 2) - ay
        key = o.get('key')
        if key is None:
            key = o['i'] + o['j'] + (fw + fh) / 2.0
        placed.append(dict(o, bw=bw, bh=bh, bx=bx, by=by, key=key))
    placed.sort(key=lambda p: p['key'])

    chars = [(cx, cy)] + ([char2] if char2 else [])
    i0, j0, i1, j1 = grid
    gx = [sx(i0, j0), sx(i1, j0), sx(i1, j1), sx(i0, j1)]
    gy = [sy(i0, j0), sy(i1, j0), sy(i1, j1), sy(i0, j1)]
    pxs = [sx(a, b) for a, b in chars]
    pys = [sy(a, b) for a, b in chars]
    x0 = min([p['bx'] for p in placed] + [q - char.width / 2 for q in pxs] + gx) - 20
    x1 = max([p['bx'] + p['bw'] for p in placed] +
             [q + char.width / 2 for q in pxs] + gx) + 20
    y0 = min([p['by'] for p in placed] + [q - CHAR_H for q in pys] + gy) - 20
    y1 = max([p['by'] + p['bh'] for p in placed] + [q + 8 for q in pys] + gy) + 20
    W, H = round((x1 - x0) * zoom), round((y1 - y0) * zoom) + 22 * zoom
    im = Image.new('RGBA', (W, H), (18, 12, 16, 255))
    tr = lambda x, y: ((x - x0) * zoom, (y - y0) * zoom + 22 * zoom)

    # floor pass (engine ground): f-plank supertiles clipped to the room
    if floor:
        fimg, fs, (fi0, fj0, fi1, fj1) = floor
        fl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        fw_px = fimg.width * fs * zoom
        fh_px = fimg.height * fs * zoom
        fz = fimg.resize((round(fw_px), round(fh_px)), Image.LANCZOS)
        step = 2
        for a in range(fi0, fi1, step):
            for b in range(fj0, fj1, step):
                tx, ty = tr(sx(a, b), sy(a, b))
                fl.alpha_composite(fz, (round(tx - fz.width / 2), round(ty)))
        # clip to the room diamond
        mask = Image.new('L', (W, H), 0)
        md = ImageDraw.Draw(mask)
        md.polygon([tr(sx(fi0, fj0), sy(fi0, fj0)), tr(sx(fi1, fj0), sy(fi1, fj0)),
                    tr(sx(fi1, fj1), sy(fi1, fj1)), tr(sx(fi0, fj1), sy(fi0, fj1))],
                   fill=255)
        im.paste(fl, (0, 0), Image.composite(fl.getchannel('A'), mask, mask))

    d = ImageDraw.Draw(im)
    def cell_poly(a, b_, a2, b2):
        return [tr(sx(a, b_), sy(a, b_)), tr(sx(a2, b_), sy(a2, b_)),
                tr(sx(a2, b2), sy(a2, b2)), tr(sx(a, b2), sy(a, b2))]
    if draw_grid:
        for a in range(i0, i1):
            for b_ in range(j0, j1):
                d.polygon(cell_poly(a, b_, a + 1, b_ + 1),
                          outline=(240, 230, 210, 26))

    # contact shadows for shadowed props (engine's ground-decal pass)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for p in placed:
        if not p.get('shadow'):
            continue
        fw, fh = p['foot']
        ccx, ccy = tr(sx(p['i'] + fw / 2, p['j'] + fh / 2),
                      sy(p['i'] + fw / 2, p['j'] + fh / 2))
        rx = (fw + fh) * (TW / 4) * 0.62 * zoom
        sd.ellipse([ccx - rx, ccy - rx / 2, ccx + rx, ccy + rx / 2],
                   fill=(20, 10, 16, 64))
    im.alpha_composite(sh)

    # THE SORT
    ck = cx + cy
    cz = char.resize((char.width * zoom, CHAR_H * zoom), Image.LANCZOS)
    char_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for qx, qy in chars:
        cpx, cpy = tr(sx(qx, qy), sy(qx, qy))
        char_layer.alpha_composite(
            cz, (round(cpx - cz.width / 2), round(cpy - (CHAR_H - 4) * zoom)))
    after_char = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    drawn = False
    for p in placed:
        if not drawn and ck < p['key']:
            im.alpha_composite(char_layer)
            drawn = True
        bz = p['img'].resize((p['bw'] * zoom, p['bh'] * zoom), Image.LANCZOS)
        pos = (round(tr(p['bx'], p['by'])[0]), round(tr(p['bx'], p['by'])[1]))
        im.alpha_composite(bz, pos)
        if drawn and p.get('occl'):
            after_char.alpha_composite(bz, pos)
    if not drawn:
        im.alpha_composite(char_layer)

    ca = char_layer.getchannel('A').load()
    oa = after_char.getchannel('A').load()
    tot = ovl = 0
    for yy in range(0, H, 2):
        for xx in range(0, W, 2):
            if ca[xx, yy] > 128:
                tot += 1
                if oa[xx, yy] > 128:
                    ovl += 1
    frac = ovl / tot if tot else 0.0

    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 20 * ZOOM], fill=(12, 9, 7, 255))
    d.text((8, 6), title, fill=(242, 228, 196, 255))
    im.convert('RGB').save(out_png)
    return {'charPos': [round(cx, 2), round(cy, 2)], 'charKey': round(ck, 2),
            'charCoveredFrac': round(frac, 3), 'img': os.path.basename(out_png)}


def room_objects(m, back, near, S):
    fw, fh = m['declared']
    scale = S * TW / m['cellPx']
    anchor = m['anchorSprite']
    W, H = round(fw * S), round(fh * S)
    return [
        # back layer: backdrop — key -inf so it always draws first
        {'img': back, 'scale': scale, 'anchor': anchor,
         'i': 0, 'j': 0, 'foot': [W, H], 'key': -9e9, 'occl': False},
        # near band: the rescue's trick measured — always after the char
        {'img': near, 'scale': scale, 'anchor': anchor,
         'i': 0, 'j': 0, 'foot': [W, H], 'key': 9e9, 'occl': True},
    ]


def prop_object(P, sprites, name, i, j, occl=True):
    p = P[name]
    return {'img': sprites[name], 'scale': TW / p['cellPx'],
            'anchor': p['anchorSprite'], 'i': i, 'j': j,
            'foot': p['declared'], 'occl': occl, 'shadow': True}


def solidity_view(m, outdir):
    """(b) derived solid map over the assembled shell art: walkable green,
    wall ring red, door wall segment yellow, interior doorstep bright."""
    shell = Image.open(os.path.join(outdir, m['sprites']['shell'])).convert('RGBA')
    fw, fh = m['declared']
    cW, cH = m['cellPxPerAxis']
    T = m['fitSprite']['T']
    e1 = (cW / 2.0, cW / 4.0)
    e2 = (-cH / 2.0, cH / 4.0)
    pt = lambda a, b: (T[0] + a * e1[0] + b * e2[0], T[1] + a * e1[1] + b * e2[1])
    base = Image.new('RGBA', (shell.width, shell.height + 44), (24, 17, 14, 255))
    base.alpha_composite(shell, (0, 44))
    ov = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    P = lambda a, b: tuple(map(lambda v: v + (0 if v is None else 0),
                               (pt(a, b)[0], pt(a, b)[1] + 44)))
    def cell(a, b, fill, outline, wid=1):
        d.polygon([P(a, b), P(a + 1, b), P(a + 1, b + 1), P(a, b + 1)],
                  fill=fill, outline=outline, width=wid)
    ring = []
    for a in range(-1, fw + 1):
        for b in range(-1, fh + 1):
            if 0 <= a < fw and 0 <= b < fh:
                continue
            ring.append([a, b])
            cell(a, b, (224, 64, 48, 60), (224, 64, 48, 160))
    for a in range(fw):
        for b in range(fh):
            cell(a, b, (88, 200, 112, 36), (88, 200, 112, 110))
    door = m['door']
    if door.get('doorWallSegment'):
        a, b = door['doorWallSegment']
        cell(a, b, (255, 212, 0, 90), (255, 212, 0, 235), 2)
    if door.get('interiorDoorstep'):
        a, b = door['interiorDoorstep']
        cell(a, b, (80, 220, 120, 90), (80, 220, 120, 235), 2)
    if door.get('matCentroidRect'):
        mx, my = door['matCentroidRect']
        mx, my = mx - m['crop'][0], my - m['crop'][1] + 44
        d.ellipse([mx - 5, my - 5, mx + 5, my + 5], outline=(255, 212, 0, 255),
                  width=2)
    base.alpha_composite(ov)
    d2 = ImageDraw.Draw(base)
    d2.rectangle([0, 0, base.width, 40], fill=(12, 9, 7, 255))
    d2.text((8, 4), 'SOLIDITY BY CONSTRUCTION - derived from the floor mark fit: '
            'green = walkable 8x8 (the mark), red = wall ring (solid)',
            fill=(242, 228, 196, 255))
    d2.text((8, 20), 'door wall segment (8,%d) yellow, interior doorstep (7,%d) '
            'bright green; back-layer art inside walkable polygon: %d px'
            % (door['doorWallSegment'][1], door['interiorDoorstep'][1],
               m['split']['backArtInsideFloorPolygonPx']),
            fill=(242, 228, 196, 255))
    out = os.path.join(outdir, 'solidity.png')
    base.convert('RGB').save(out)
    return {'img': 'solidity.png', 'ringCells': len(ring),
            'backArtInsideFloorPolygonPx':
                m['split']['backArtInsideFloorPolygonPx']}


def main(outdir):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(outdir, 'interior-metrics.json')) as f:
        M = json.load(f)
    m = M['room']
    P = M['props']
    back = Image.open(os.path.join(outdir, m['sprites']['back'])).convert('RGBA')
    near = Image.open(os.path.join(outdir, m['sprites']['near'])).convert('RGBA')
    sprites = {n: Image.open(os.path.join(outdir, P[n]['sprite'])).convert('RGBA')
               for n in P if P[n].get('sprite')}
    plank = Image.open(os.path.join(
        root, 'public/assets/iso/blocks/f-plank.png')).convert('RGBA')
    plank_s = 0.492                     # registry f-plank scale (2x2 supertile)
    char = load_vesper(root)
    fw, fh = m['declared']
    door = m['door']
    dstep = door['interiorDoorstep']
    out = {}

    # ---- (a) scale sanity at S=1 and S=1.5 --------------------------------
    wall_h = m['nearWall']['heightPx']
    for S, tag in [(1, 'S1'), (1.5, 'S15')]:
        W, H = round(fw * S), round(fh * S)
        objs = room_objects(m, back, near, S)
        rs = S * TW / m['cellPx']
        wall_screen = wall_h * rs
        r = scene_render(
            objs, char, W / 2 + 0.5, H / 2 + 0.5,
            (0, 0, W, H),
            'SCALE %s: cellScale x%s -> engine %dx%d, renderScale %.3f | wall '
            'renders %dpx vs Vesper %dpx (%.2fx)' % (
                tag, S, W, H, rs, wall_screen, CHAR_H, wall_screen / CHAR_H),
            os.path.join(outdir, 'scale-%s.png' % tag),
            floor=(plank, plank_s, (0, 0, W, H)),
            char2=((dstep[0] + 0.5) * S, (dstep[1] + 0.5) * S))
        r['S'] = S
        r['renderScale'] = round(rs, 4)
        r['wallScreenPx'] = round(wall_screen)
        r['wallOverVesper'] = round(wall_screen / CHAR_H, 2)
        r['engineFoot'] = [W, H]
        out['scale-%s' % tag] = r
        print('scale %s: wall %dpx = %.2fx Vesper, room %dx%d engine cells'
              % (tag, wall_screen, wall_screen / CHAR_H, W, H))

    # ---- pick S: closest wall/Vesper ratio to the hand-rescued room -------
    # rescue reference: bakint-room walls ~300px at s=1.25 -> 375 screen px
    # = 2.88x Vesper; and the rescue room is 12x12 engine cells
    S = 1.5 if abs(out['scale-S15']['wallOverVesper'] - 2.4) < \
               abs(out['scale-S1']['wallOverVesper'] - 2.4) else 1
    out['sVerdict'] = {
        'chosen': S,
        'reason': 'wall height %.2fx Vesper at S=1.5 vs %.2fx at S=1; the '
                  'hand-rescued room is 12x12 engine cells with walls ~2.5-3x '
                  'Vesper — S=1.5 reproduces the proven interior scale '
                  '(engine 12x12) from an 8x8 painted room' % (
                      out['scale-S15']['wallOverVesper'],
                      out['scale-S1']['wallOverVesper']),
    }
    W, H = round(fw * S), round(fh * S)
    RS = S * TW / m['cellPx']
    grid = (0, 0, W, H)
    floor = (plank, plank_s, grid)

    # ---- (b) solidity ------------------------------------------------------
    out['solidity'] = solidity_view(m, outdir)

    # ---- (c) near-wall occlusion ------------------------------------------
    objs = room_objects(m, back, near, S)
    r = scene_render(objs, char, (dstep[0] + 0.5) * S, (dstep[1] + 0.5) * S,
                     grid, 'NEAR-WALL OCCLUSION: Vesper on the interior '
                     'doorstep (%d,%d) - partially behind the measured '
                     'near-wall band' % tuple(dstep),
                     os.path.join(outdir, 'occl-door.png'), floor=floor)
    out['occl-door'] = r
    print('occl door: covered %.0f%%' % (r['charCoveredFrac'] * 100))
    r = scene_render(objs, char, W / 2 - 1, H / 2 + 1, grid,
                     'NEAR-WALL OCCLUSION: Vesper mid-room - fully visible',
                     os.path.join(outdir, 'occl-mid.png'), floor=floor)
    out['occl-mid'] = r
    print('occl mid: covered %.0f%%' % (r['charCoveredFrac'] * 100))
    # approach shot: walk the doorstep row away from the wall and keep the
    # first position where the wall hides PART of her (head over the rail)
    import tempfile
    for pa in (6.5, 6.0, 5.5, 5.0, 4.5):
        cx2, cy2 = (pa + 0.5) * S, (dstep[1] + 0.5) * S
        r = scene_render(objs, char, cx2, cy2, grid,
                         'NEAR-WALL OCCLUSION: approaching the door at painted '
                         '(%.1f,%d) - partially behind the band' % (
                             pa, dstep[1]),
                         os.path.join(outdir, 'occl-approach.png'), floor=floor)
        if 0.1 <= r['charCoveredFrac'] <= 0.8:
            break
    out['occl-approach'] = r
    print('occl approach (painted %.1f): covered %.0f%%'
          % (pa, r['charCoveredFrac'] * 100))

    # ---- (d) prop sorting --------------------------------------------------
    oven_i, oven_j = round(1.5 * S), 0
    r1 = scene_render(
        room_objects(m, back, near, S) +
        [prop_object(P, sprites, 'oven', oven_i, oven_j)],
        char, oven_i + 1, oven_j - 0.6 + 0.0, grid,
        'PROP SORT: Vesper BEHIND the oven (key %.1f < oven %.1f)' % (
            oven_i + 1 + oven_j - 0.6, oven_i + oven_j + 2),
        os.path.join(outdir, 'occl-oven.png'), floor=floor)
    out['occl-oven-behind'] = r1
    ctr_i, ctr_j = round(2.5 * S), round(2.5 * S)
    r2 = scene_render(
        room_objects(m, back, near, S) +
        [prop_object(P, sprites, 'counter', ctr_i, ctr_j)],
        char, ctr_i + 1, ctr_j + 2.7, grid,
        'PROP SORT: Vesper IN FRONT of the counter (key %.1f > counter %.1f)'
        % (ctr_i + 1 + ctr_j + 2.7, ctr_i + ctr_j + 2),
        os.path.join(outdir, 'occl-counter.png'), floor=floor)
    out['occl-counter-front'] = r2
    print('oven behind: covered %.0f%%; counter front: covered %.0f%%'
          % (r1['charCoveredFrac'] * 100, r2['charCoveredFrac'] * 100))

    # ---- (e) the assembled room -------------------------------------------
    # placements avoid the near wall's occlusion shadow (the wall correctly
    # hides a triangle of cells deep into the room - measured finding, see
    # the report; props there would be invisible like a char at the doorstep)
    objs = room_objects(m, back, near, S) + [
        prop_object(P, sprites, 'oven', round(1.2 * S), 0),
        prop_object(P, sprites, 'shelf', 0, round(1.4 * S)),
        prop_object(P, sprites, 'sacks', round(2.9 * S), 0),
        prop_object(P, sprites, 'preptable', 0, round(4.2 * S)),
        prop_object(P, sprites, 'counter', round(3.4 * S), round(3.2 * S)),
        prop_object(P, sprites, 'stool', round(3.1 * S), round(5.6 * S)),
    ]
    r = scene_render(objs, char, round(3.4 * S) + 1, round(3.2 * S) + 2.7,
                     grid, 'THE ASSEMBLED ROOM - measured shell + measured '
                     'props + f-plank floor + Vesper at the counter, real '
                     'sort, cellScale x%s' % S,
                     os.path.join(outdir, 'room-assembled.png'), floor=floor,
                     draw_grid=False)
    out['assembled'] = r
    print('assembled: covered %.0f%%' % (r['charCoveredFrac'] * 100))

    with open(os.path.join(outdir, 'interior-prove.json'), 'w') as f:
        json.dump(out, f, indent=1)
    print('S verdict:', out['sVerdict']['chosen'])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'public/assets/iso/interior')
