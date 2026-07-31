"""make_herosheet.py — the hero-tree / canopy_slim comparison sheets.

Two frames per candidate side by side: WIDE (silhouette, with the 1.80 m figure) and CLOSE
(7 m from the trunk — the only frame in which "leaf cards read large" can be settled).
probe2-c, the ratified bar, is pasted at the head of the sheet so the comparison is against
the frame the user actually approved and not against a memory of it.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

S = os.path.dirname(os.path.abspath(__file__))
HERO = os.path.join(S, 'hero')
OUT = os.path.join(S, 'sheets')
PROBE = '/Users/junshernchan/projects/multiplayer-rpg/docs/qa/emberbrook/styleprobe/probe2-c.png'
os.makedirs(OUT, exist_ok=True)

F = '/System/Library/Fonts/Supplemental/Arial.ttf'
FB = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f_title = ImageFont.truetype(FB, 32)
f_head = ImageFont.truetype(FB, 26)
f_body = ImageFont.truetype(F, 21)
f_small = ImageFont.truetype(F, 18)
INK, MUTE, ACCENT, GOOD = (18, 20, 24), (95, 100, 110), (150, 60, 20), (30, 95, 60)

CAND = {c['id']: c for c in json.load(open(os.path.join(HERO, 'candidates.json')))}
# leaf-card evidence from the probes (tools/dressing_slimprobe.py), median longest triangle
# edge of the realised leaf geometry — the card's size as the camera sees it
# leaf-card evidence, ALL FROM ONE INSTRUMENT (tools/dressing_slimprobe.py): median
# longest triangle edge of the realised leaf geometry = the card's size as the camera sees
# it, and median triangle aspect = the only one of the two that can see a stretch.
# K and L carry a RANGE because their density override was measured on the density sweep
# (tools/dressing_densitysweep.py) at k=3.0 rather than on this probe: native 9.93 mm,
# density_multiplier 250 -> 9.80 mm, and K/L sit at 170/190.
LEAFMM = {'A-control-2.6x': (26.17, 2.015), 'B-skeleton-2.5': (9.95, 2.086),
          'C-skeleton-3.0': (9.88, 2.060), 'K-skeleton-3.0-refilled': (9.85, 2.06),
          'F-slim-control': (18.61, 2.199), 'G-slim-skeleton': (9.87, 2.087),
          'H-slim-skeleton-tight': (9.84, 2.087), 'L-slim-skeleton-refilled': (9.85, 2.09)}
NATIVE_MM = 10.07


def tile(cid, w=760):
    a = os.path.join(HERO, cid + '-wide.png')
    b = os.path.join(HERO, cid + '-close.png')
    if not (os.path.exists(a) and os.path.exists(b)):
        return None
    ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
    h = int(ia.size[1] * w / ia.size[0])
    ia, ib = ia.resize((w, h), Image.LANCZOS), ib.resize((w, h), Image.LANCZOS)
    c = CAND.get(cid, {})
    CAP = 132
    out = Image.new('RGB', (w * 2 + 6, h + CAP), (247, 245, 241))
    out.paste(ia, (0, 0))
    out.paste(ib, (w + 6, 0))
    d = ImageDraw.Draw(out)
    d.text((10, h + 8), cid, font=f_head, fill=INK)
    tw = d.textlength(cid, font=f_head)
    d.text((22 + tw, h + 13), c.get('label', ''), font=f_body, fill=ACCENT)
    l2 = (f"measured  H {c.get('height_m', 0):.2f} m   crown {c.get('width_m', 0):.2f} m   "
          f"slenderness {c.get('slenderness', 0):.2f}   {c.get('tris', 0):,} tris")
    d.text((10, h + 44), l2, font=f_body, fill=INK)
    mm = LEAFMM.get(cid)
    if mm:
        delta = (mm[0] / NATIVE_MM - 1) * 100
        col = GOOD if abs(delta) < 15 else ACCENT
        approx = '~' if cid in ('K-skeleton-3.0-refilled', 'L-slim-skeleton-refilled') else ''
        l3 = (f"leaf card {approx}{mm[0]:.2f} mm median triangle edge vs {NATIVE_MM:.2f} mm "
              f"native ({delta:+.0f}%)   aspect {mm[1]:.2f}")
    else:
        lc = c.get('leaf_card_m')
        col = GOOD
        l3 = (f"leaf card {lc * 1000:.0f} mm — SET as a parameter, not inherited"
              if lc else 'leaf card: n/a')
    d.text((10, h + 74), l3, font=f_small, fill=col)
    d.text((10, h + 100), f"{c.get('asset', '')}   {c.get('spec', '')}"
           + (f"   gn {c.get('gn')}" if c.get('gn') else ''), font=f_small, fill=MUTE)
    d.text((14, 10), 'WIDE — silhouette, 1.80 m figure', font=f_small, fill=(255, 255, 255))
    d.text((w + 20, 10), 'CLOSE — 7 m, where the defect lives', font=f_small,
           fill=(255, 255, 255))
    return out


def sheet(name, ids, title, subtitle):
    tiles = [t for t in ((i, tile(i)) for i in ids) if t[1]]
    if not tiles:
        print('NO TILES', name)
        return
    tw, th = tiles[0][1].size
    pad, head = 14, 150
    bar_h = 300
    W = tw + pad * 2
    bar = Image.open(PROBE).convert('RGB')
    bw = W - pad * 2
    bar = bar.resize((bw, int(bar.size[1] * bw / bar.size[0])), Image.LANCZOS)
    bar_h = bar.size[1] + 44
    H = head + bar_h + len(tiles) * (th + pad) + pad
    sh = Image.new('RGB', (W, H), (236, 233, 227))
    d = ImageDraw.Draw(sh)
    d.text((pad + 4, 18), title, font=f_title, fill=INK)
    y = 58
    line = ''
    for word in subtitle.split():
        t = (line + ' ' + word).strip()
        if d.textlength(t, font=f_small) > W - 2 * pad - 8:
            d.text((pad + 4, y), line, font=f_small, fill=MUTE)
            y += 24
            line = word
        else:
            line = t
    d.text((pad + 4, y), line, font=f_small, fill=MUTE)
    d.text((pad + 4, head - 26), 'THE BAR — probe2-c, the ratified round-2 frame:',
           font=f_small, fill=ACCENT)
    sh.paste(bar, (pad, head))
    yy = head + bar_h
    for cid, t in tiles:
        sh.paste(t, (pad, yy))
        yy += th + pad
    p = os.path.join(OUT, name + '.png')
    sh.save(p)
    print('SHEET', p, sh.size, round(os.path.getsize(p) / 1e6, 2), 'MB')


if __name__ == '__main__':
    sheet('sheet-4-hero-tree',
          ['A-control-2.6x', 'B-skeleton-2.5', 'C-skeleton-3.0', 'K-skeleton-3.0-refilled',
           'D-jacaranda-native', 'E-jacaranda-0.7', 'I-sapling-oak'],
          'HERO BROADLEAF — CANDIDATES vs THE ROUND-2 CONTROL',
          'All candidates under probe2-c\'s own key (EMB_sun 3.0 W at elev 62/rot 212, warm bounce, '
          'MULTIPLE_SCATTERING sky at 0.30, AgX Medium High Contrast, exposure 0.10, 60 deg lens) and '
          'carrying the probe\'s own autumn regrade. The floor is a neutral matte, not the probe\'s dressed bank: '
          'the subject under test is the tree. A is the round-2 method and is included so the comparison has a control.')
    sheet('sheet-5-canopy-slim',
          ['F-slim-control', 'G-slim-skeleton', 'H-slim-skeleton-tight',
           'L-slim-skeleton-refilled', 'J-sapling-column'],
          'canopy_slim — THE POPLAR SILHOUETTE, CANDIDATES vs THE ROUND-2 STRETCH',
          'Same rig. F is what both probes did: a NON-UNIFORM OBJECT SCALE, which stretches every leaf card '
          'with the tree. The requirement is the poplar SILHOUETTE, not the birch species, so no white-bark '
          'source is needed. Slenderness (height / crown width) is the number to read.')
