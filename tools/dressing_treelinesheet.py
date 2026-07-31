"""make_treelinesheet.py — the pine_tree_01 verdict sheet.

Same band, same 34 stations, same seed in all three frames; only the species standing at
each station changes. The tri and disk figures under each frame are what the choice actually
costs.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

S = os.path.dirname(os.path.abspath(__file__))
HERO = os.path.join(S, 'hero')
OUT = os.path.join(S, 'sheets')
os.makedirs(OUT, exist_ok=True)
F = '/System/Library/Fonts/Supplemental/Arial.ttf'
FB = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f_title = ImageFont.truetype(FB, 32)
f_head = ImageFont.truetype(FB, 26)
f_body = ImageFont.truetype(F, 21)
f_small = ImageFont.truetype(F, 18)
INK, MUTE, ACCENT = (18, 20, 24), (95, 100, 110), (150, 60, 20)

TL = {t['id']: t for t in json.load(open(os.path.join(HERO, 'treeline.json')))}
NOTE = {
    'T1-pine-fir-mix': ('ROUND-2 AS BUILT: pine_tree_01 + fir_tree_01',
                        'pine source 777 MB - the biggest disk line in the intake. '
                        'pine LOD0 17.2 M tris = 68% of the whole library; LOD1 827 k.'),
    'T2-fir-only': ('WITHOUT PINE: fir_tree_01 variants a + b only',
                    'fir source 426 MB. If this band reads, 777 MB and the library\'s '
                    'largest mesh never ship.'),
    'T3-fir-plus-sapling': ('WITHOUT PINE: fir_tree_01 + a Sapling-generated conifer',
                            'Sapling conifer is procedural: no source download, no '
                            'attribution, size set as a parameter.'),
}


def build():
    # T3 (the Sapling-conifer arm) is DELIBERATELY NOT ON THIS SHEET. It rendered with
    # invisible trunks: the preset parse silently produced an empty parameter dict and the
    # curve was left unbevelled, so each 'tree' was a zero-width curve carrying a thin cloud
    # of leaves. A frame that shows something other than what it claims to show is worse
    # than no frame, and the arm also needs a CC0 NEEDLE atlas we do not hold locally.
    ids = [i for i in ('T1-pine-fir-mix', 'T2-fir-only')
           if os.path.exists(os.path.join(HERO, i + '.png'))]
    if not ids:
        print('no treeline frames')
        return
    ims = [Image.open(os.path.join(HERO, i + '.png')).convert('RGB') for i in ids]
    w = 1500
    ims = [im.resize((w, int(im.size[1] * w / im.size[0])), Image.LANCZOS) for im in ims]
    th = ims[0].size[1]
    CAP = 116
    pad, head = 14, 150
    W = w + pad * 2
    H = head + len(ims) * (th + CAP + pad) + pad
    sh = Image.new('RGB', (W, H), (236, 233, 227))
    d = ImageDraw.Draw(sh)
    d.text((pad + 4, 18), 'THE WHISPERWOOD TREELINE — IS pine_tree_01 LOAD-BEARING?',
           font=f_title, fill=INK)
    sub = ('TWO arms, not three: the Sapling-conifer arm is withheld — it rendered with invisible '
           'trunks (unbevelled curves from a failed preset parse) and needs a CC0 needle atlas we do '
           'not hold. The same 34 stations, the same seed, the same rotations and scale jitter in all three '
           'frames: only the species at each station changes. Instanced at LOD1, which is what a '
           'band at 26-72 m would ever use — if LOD1 carries it, LOD0 never ships. Camera 1.80 m, '
           '40 deg, probe2-c\'s key.')
    y = 58
    line = ''
    for word in sub.split():
        t = (line + ' ' + word).strip()
        if d.textlength(t, font=f_small) > W - 2 * pad - 8:
            d.text((pad + 4, y), line, font=f_small, fill=MUTE)
            y += 24
            line = word
        else:
            line = t
    d.text((pad + 4, y), line, font=f_small, fill=MUTE)
    yy = head
    for i, im in zip(ids, ims):
        sh.paste(im, (pad, yy))
        yy += th
        t = TL.get(i, {})
        d.text((pad + 6, yy + 8), i, font=f_head, fill=INK)
        tw = d.textlength(i, font=f_head)
        d.text((pad + 18 + tw, yy + 13), NOTE[i][0], font=f_body, fill=ACCENT)
        counts = ', '.join(f'{k} x{v}' for k, v in sorted(t.get('counts', {}).items()))
        d.text((pad + 6, yy + 44), counts, font=f_small, fill=INK)
        d.text((pad + 6, yy + 70), NOTE[i][1], font=f_small, fill=MUTE)
        yy += CAP + pad
    p = os.path.join(OUT, 'sheet-6-treeline.png')
    sh.save(p)
    print('SHEET', p, sh.size, round(os.path.getsize(p) / 1e6, 2), 'MB')


if __name__ == '__main__':
    build()
