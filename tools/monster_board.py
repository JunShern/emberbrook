#!/usr/bin/env python3
"""monster_board.py — stack two lineup frames into ONE before/after picture.

    node tools/monster_lineup.mjs --out docs/qa/battle-monsters/lineup-before.png --chars vesper,maren ...
    <make the change>
    node tools/monster_lineup.mjs --out docs/qa/battle-monsters/lineup-after.png  --chars vesper,maren ...
    python3 tools/monster_board.py docs/qa/battle-monsters/lineup-{before,after}.png \
        --out docs/qa/battle-monsters/lineup-before-after.png

Captions come from each frame's SIDECAR (`<name>.json`, written by monster_lineup),
so every label sits under the body it names even though perspective moves the
stations off their column centres. Long names alternate between two baselines --
two captions that overlap are a caption you cannot read, and this row is 8 wide.
"""
import argparse, json, os
from PIL import Image, ImageDraw, ImageFont

NOTE = {
    'brook-sprite':  'brook-sprite\n(ships as a built wisp)',
    'duskpad':       'duskpad\n(the reference)',
    'vesper':        'VESPER (ratified)',
    'maren':         'MAREN (ratified)',
    'lake':          'LAKE (ratified)',
}


def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Menlo.ttc',
              '/System/Library/Fonts/Menlo.ttc', '/Library/Fonts/Arial.ttf'):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('before'); ap.add_argument('after')
    ap.add_argument('--out', required=True)
    ap.add_argument('--top', default='BEFORE'); ap.add_argument('--bottom', default='AFTER')
    ap.add_argument('--crop', default='150,830', help='y0,y1 of the source frames worth keeping')
    a = ap.parse_args()
    y0, y1 = (int(v) for v in a.crop.split(','))
    b = Image.open(a.before).convert('RGB'); af = Image.open(a.after).convert('RGB')
    b = b.crop((0, y0, b.width, y1)); af = af.crop((0, y0, af.width, y1))
    meta = json.load(open(os.path.splitext(a.after)[0] + '.json'))
    W, H = b.size
    BAR = 64
    out = Image.new('RGB', (W, H * 2 + BAR * 2), (23, 20, 16))
    d = ImageDraw.Draw(out)
    F, FB = font(30), font(38)
    out.paste(b, (0, BAR)); out.paste(af, (0, BAR * 2 + H))
    d.text((24, 16), a.top, fill=(232, 220, 196), font=FB)
    d.text((24, BAR + H + 16), a.bottom, fill=(232, 220, 196), font=FB)
    for i, (k, v) in enumerate(meta.items()):
        if 'sx' not in v: continue
        txt = NOTE.get(k, k)
        stagger = 0 if i % 2 == 0 else 44
        for row in (BAR + H - 52 - stagger, BAR * 2 + 2 * H - 52 - stagger):
            bb = d.multiline_textbbox((0, 0), txt, font=F)
            d.multiline_text((int(v['sx'] * W) - (bb[2] - bb[0]) // 2, row - (bb[3] - bb[1])),
                             txt, fill=(255, 246, 224), font=F, align='center',
                             stroke_width=4, stroke_fill=(20, 18, 14))
    out = out.resize((W // 2, out.height // 2), Image.LANCZOS)
    out.save(a.out)
    print(a.out, out.size)


if __name__ == '__main__':
    main()
