#!/usr/bin/env python3
"""Sprite utilities: magenta keying, frame extraction, sheet packing.
Mirrors the browser-side recipe (sprites2.js) so agents can run the whole
sprite pipeline headlessly.

Usage:
  python3 tools/sprites.py key IN.png OUT.png            # key magenta -> transparent, bbox crop
  python3 tools/sprites.py split IN.png OUTDIR [n]       # split a strip into frames by alpha projection
  python3 tools/sprites.py pack OUT.png ROWSPEC...       # pack frames into a 256px-cell sheet
      ROWSPEC = row:file1,file2,...   (each file keyed+cropped, bottom-aligned in its cell)
Example:
  python3 tools/sprites.py pack sheet.png 0:down1.png,down2.png 1:up1.png 2:r1.png,r2.png,r3.png
"""
import sys, os
from PIL import Image

def key_magenta(im):
    im = im.convert('RGBA')
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            rg, bg = r - g, b - g
            if rg > 90 and bg > 60:
                px[x, y] = (0, 0, 0, 0)
            elif rg > 50 and bg > 32:
                t = min(1.0, ((rg + bg) - 82) / 60.0)
                px[x, y] = (int(g + rg * 0.35), g, int(g + bg * 0.35), int(255 * (1 - t * 0.85)))
    return im

def bbox_crop(im, alpha_th=24):
    a = im.getchannel('A')
    bbox = a.point(lambda v: 255 if v > alpha_th else 0).getbbox()
    return im.crop(bbox) if bbox else im

def split_frames(im, want=None, alpha_th=24):
    """Split a keyed strip into frames via column alpha projection."""
    a = im.getchannel('A')
    w, h = im.size
    data = list(a.getdata())
    col = [0] * w
    for y in range(0, h, 2):
        row = data[y * w:(y + 1) * w]
        for x in range(w):
            if row[x] > alpha_th:
                col[x] += 1
    th = h * 0.012
    runs, start = [], None
    for x in range(w + 1):
        on = x < w and col[x] > th
        if on and start is None: start = x
        if not on and start is not None:
            if x - start > 6: runs.append((start, x))
            start = None
    if want:
        runs = sorted(sorted(runs, key=lambda r: r[0] - r[1])[:want])
    return [bbox_crop(im.crop((x0, 0, x1, h))) for x0, x1 in runs]

def pack(out_path, rowspecs, cell=256):
    rows = []
    for spec in rowspecs:
        rown, files = spec.split(':', 1)
        frames = []
        for f in files.split(','):
            im = key_magenta(Image.open(f))
            frames.append(bbox_crop(im))
        rows.append((int(rown), frames))
    ncols = max(len(fr) for _, fr in rows)
    nrows = max(r for r, _ in rows) + 1
    sheet = Image.new('RGBA', (cell * ncols, cell * nrows), (0, 0, 0, 0))
    for rown, frames in rows:
        for i, fr in enumerate(frames):
            s = min((cell - 12) / fr.height, (cell - 12) / fr.width)
            fw, fh = max(1, int(fr.width * s)), max(1, int(fr.height * s))
            fr2 = fr.resize((fw, fh), Image.LANCZOS)
            sheet.alpha_composite(fr2, (i * cell + (cell - fw) // 2, rown * cell + cell - fh - 2))
    sheet.save(out_path)
    print(f'packed {out_path}: {ncols}x{nrows} cells of {cell}')

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'key':
        key_magenta(Image.open(sys.argv[2])).save(sys.argv[3]); print('keyed', sys.argv[3])
    elif cmd == 'split':
        outdir = sys.argv[3]; os.makedirs(outdir, exist_ok=True)
        want = int(sys.argv[4]) if len(sys.argv) > 4 else None
        frames = split_frames(key_magenta(Image.open(sys.argv[2])), want)
        for i, fr in enumerate(frames):
            fr.save(os.path.join(outdir, f'f{i+1}.png'))
        print(f'split {len(frames)} frames -> {outdir}')
    elif cmd == 'pack':
        pack(sys.argv[2], sys.argv[3:])
    else:
        print(__doc__); sys.exit(1)
