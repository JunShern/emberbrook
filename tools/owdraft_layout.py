#!/usr/bin/env python3
"""owdraft_layout.py — the CHEAP top-down of the hanging-valley PROPOSAL.

  python3 tools/owdraft_layout.py

Writes docs/qa/overworld-draft/embercorridor_layout.png: hillshaded heightfield,
zone tint, the river at its real width, the road, the landmarks, contour lines
every 5u with the corridor's elevations called out — plus a LONG SECTION beneath
it, because the whole proposition is vertical and a plan view alone cannot argue
it.  Same discipline as tools/valley_layout.py: every number comes out of the
draft map file, so the picture and the built tile cannot disagree.

*** PROPOSAL. NOT CANON. ***
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import owdraft_lib as DL                                       # noqa: E402

D = DL.D
OUT = os.path.join(DL.QA, "embercorridor_layout.png")
PPU = 4
SS = 2
W, H = int(DL.TILE_W * PPU), int(DL.TILE_H * PPU)
PROF_H = 380
RIVL_H = 250
PAD_T = 96


def font(sz, bold=True):
    for p in (("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
               "/System/Library/Fonts/Supplemental/Arial.ttf"),
              "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def _blur(A, r, passes=2):
    """separable box blur — PIL cannot gaussian-blur an 'F' image"""
    k = 2 * r + 1
    B = A.astype(np.float64)
    for _ in range(passes):
        for ax in (0, 1):
            P = np.pad(B, [(r, r) if a == ax else (0, 0) for a in (0, 1)], mode="edge")
            c = np.cumsum(P, axis=ax)
            c = np.concatenate([np.zeros_like(np.take(c, [0], ax)), c], axis=ax)
            B = (np.take(c, range(k, c.shape[ax]), ax)
                 - np.take(c, range(0, c.shape[ax] - k), ax)) / k
    return B


def w2p(x, y, s=1):
    """world -> pixel inside the MAP panel (north up)"""
    return (x * PPU * s, (DL.TILE_H - y) * PPU * s)


def main():
    F = DL.DraftField()

    # ---------------------------------------------------------- raster: relief
    wx = np.linspace(0.0, DL.TILE_W, W)
    wy = np.linspace(DL.TILE_H, 0.0, H)
    GX, GY = np.meshgrid(wx, wy)
    Hh = F.height(GX, GY)

    # hillshade and slope come off a SMOOTHED height: sub-unit relief at 4 px/u is
    # speckle, and speckle hides the landform the map exists to show.
    Hs = _blur(Hh, 4)
    gy, gx = np.gradient(Hs, DL.TILE_H / H, DL.TILE_W / W)
    lx, ly, lz = -0.60, 0.60, 0.52
    nrm = 1.0 / np.sqrt(gx * gx + gy * gy + 1.0)
    shade = np.clip((-gx * lx + gy * ly + lz) * nrm * 1.62, 0.30, 1.42)

    # HYPSOMETRIC base — this is a geography map, so height is the primary colour
    ramp = [(-6, (36, 70, 84)), (2, (74, 116, 82)), (14, (108, 146, 78)),
            (24, (146, 168, 84)), (31, (176, 182, 96)), (38, (168, 150, 104)),
            (48, (146, 122, 100)), (58, (150, 138, 130)), (67, (196, 192, 190))]
    hs = np.array([r[0] for r in ramp], float)
    base = np.stack([np.interp(Hs, hs, [r[1][k] for r in ramp]) for k in range(3)], -1)

    zg, cell, cols, rows = DL.zone_grid(F, 1.25)
    zi = np.clip(((DL.TILE_H - GY) / cell).astype(int), 0, rows - 1)
    zj = np.clip((GX / cell).astype(int), 0, cols - 1)
    zt = zg[rows - 1 - zi, zj]

    def wash(mask, col, a):
        base[mask] = base[mask] * (1 - a) + np.array(col, float) * a

    wash(zt == 1, (42, 78, 48), 0.52)            # forest
    wash(zt == 5, (206, 176, 78), 0.46)          # farm — the valley IS farmed
    wash(np.hypot(gx, gy) > 0.85, (140, 128, 116), 0.34)   # crag, off smoothed slope

    rgb = np.clip(base * shade[..., None], 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb)

    # contours every 5u (25u heavier), drawn off the smoothed field
    ca = np.zeros((H, W), np.uint8)
    band = np.mod(Hs, 5.0)
    ca[(band < 0.30) | (band > 4.70)] = 52
    ca[(np.mod(Hs, 25.0) < 0.42) | (np.mod(Hs, 25.0) > 24.58)] = 122
    con = Image.fromarray(ca).filter(ImageFilter.GaussianBlur(0.5))
    img = Image.composite(Image.new("RGB", (W, H), (26, 24, 20)), img, con)

    # ------------------------------------------------------------- vector pass
    ov = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    def line(pts, col, wid):
        d.line([w2p(p[0], p[1], SS) for p in pts], fill=col, width=int(wid * SS),
               joint="curve")

    rp = D["river"]["points"]
    # river drawn at real width, tapering
    for i in range(len(rp) - 1):
        a, b = rp[i], rp[i + 1]
        wmid = (a[3] + b[3]) * 0.5
        d.line([w2p(a[0], a[1], SS), w2p(b[0], b[1], SS)],
               fill=(58, 120, 158, 255), width=max(2, int(wmid * PPU * SS)), joint="curve")
    line([(p[0], p[1]) for p in rp], (128, 196, 226, 235), 1.1)

    line([(p[0], p[1]) for p in F.roadpts], (26, 20, 14, 150), 3.4)
    line([(p[0], p[1]) for p in F.roadpts], (238, 216, 168, 255), 2.2)

    # the range crest — the load-bearing feature, so it gets drawn explicitly
    for r in D["ridges"]["list"]:
        hard = r["id"] == "gatewall-range"
        line([(p[0], p[1]) for p in r["points"]],
             (60, 44, 34, 235) if hard else (72, 62, 52, 130), 3.0 if hard else 1.6)
        if hard:
            for gxg, gyg, gr in r.get("gaps", []):
                px, py = w2p(gxg, gyg, SS)
                rr = gr * PPU * SS
                d.ellipse([px - rr, py - rr, px + rr, py + rr],
                          outline=(255, 214, 92, 255), width=int(2.4 * SS))

    for lm in D["landmarks"]:
        if lm["class"] != "town":
            continue
        px, py = w2p(lm["pos"][0], lm["pos"][1], SS)
        rr = lm["r"] * PPU * SS
        d.ellipse([px - rr, py - rr, px + rr, py + rr],
                  outline=(255, 248, 222, 210), width=int(1.6 * SS))

    ov = ov.resize((W, H), Image.LANCZOS)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    # --------------------------------------------------------------- the sheet
    sheet = Image.new("RGB", (W, PAD_T + H + PROF_H + RIVL_H), (17, 16, 15))
    sheet.paste(img, (0, PAD_T))
    s = ImageDraw.Draw(sheet)
    f28, f19, f16, f14 = font(30), font(20), font(17), font(15, False)

    s.text((22, 18), "THE EMBER CORRIDOR — hanging valley -> water gap -> gorge -> Dellhollow",
           font=f28, fill=(246, 238, 220))
    s.text((22, 56), "PROPOSAL DRAFT, NOT CANON — 300 x 240u, character = 1.45u.  "
                     "Downstream = NORTH (per both town maps).  Contours 5u / 25u.",
           font=f16, fill=(196, 168, 120))

    def label(x, y, txt, col=(255, 255, 255), at=None, anchor="l", fnt=f19, dot=True):
        """`at` is the label's own world position; a leader line joins it back to
        the feature, so text can go anywhere legible."""
        px, py = w2p(x, y)
        py += PAD_T
        lx, ly = (px + 14, py - 12) if at is None else (at[0] * PPU,
                                                        (DL.TILE_H - at[1]) * PPU + PAD_T)
        lines = txt.split("\n")
        tw = max(s.textbbox((0, 0), t, font=fnt)[2] for t in lines)
        th = len(lines) * (fnt.size + 4)
        if anchor == "r":
            lx -= tw
        s.line([px, py, lx + (tw / 2 if anchor == "l" else tw / 2), ly + th / 2],
               fill=(250, 244, 226, 200), width=2)
        s.rectangle([lx - 7, ly - 5, lx + tw + 7, ly + th + 3], fill=(12, 11, 10))
        s.multiline_text((lx, ly), txt, font=fnt, fill=col, spacing=4)
        if dot:
            s.ellipse([px - 5, py - 5, px + 5, py + 5], fill=col,
                      outline=(16, 14, 12), width=2)

    L = {lm["id"]: lm for lm in D["landmarks"]}
    label(*L["whisperwood-road"]["pos"][:2], at=(112, 18),
          txt="WHISPERWOOD ROAD  h33\nthe ONE way in — from the SOUTH, upstream",
          col=(232, 232, 226))
    label(*L["emberbrook"]["pos"][:2], at=(20, 78),
          txt="EMBERBROOK  h30\nthe hanging valley: farmed, warm,\ncradled behind the range",
          col=(255, 226, 150))
    label(*L["village-bridge"]["pos"][:2], at=(150, 74),
          txt="THE VILLAGE BRIDGE — the ONE crossing\nleave the village, cross, hug the east bank",
          col=(226, 200, 160), fnt=f16)
    label(*L["old-gate"]["pos"][:2], at=(150, 112),
          txt="THE OLD GATE = THE WATER GAP  h28\nthe range's ONE breach: road over, river under",
          col=(255, 214, 92))
    label(*L["ember-falls"]["pos"][:2], at=(6, 116),
          txt="EMBER FALLS\nh27.0 -> h18.5\nthe plunge off the lip",
          col=(150, 214, 240))
    label(*L["pocket-terrace"]["pos"][:2], at=(150, 150),
          txt="pocket terrace h15", col=(224, 224, 214), fnt=f16)
    label(*L["dellhollow"]["pos"][:2], at=(122, 206),
          txt="DELLHOLLOW   valley gate h12, pool h4\nthe same gorge, matured: locks, dams, wheels",
          col=(255, 226, 150))
    label(*L["dellhollow-moorage"]["pos"][:2], at=(214, 176),
          txt="THE MOORAGE h-4\nnavigable; Ch3 departs", col=(150, 214, 240), fnt=f16)

    def note(x, y, txt, col=(214, 196, 168), fnt=f16):
        s.multiline_text((x * PPU, (DL.TILE_H - y) * PPU + PAD_T), txt, font=fnt,
                         fill=col, spacing=3, stroke_width=3, stroke_fill=(16, 15, 14))

    note(8, 96, "THE GATEWALL RANGE\nunbroken, crest 54-63", (240, 214, 172), f19)
    note(196, 142, "the range runs on east —\nno other cut anywhere")
    note(56, 196, "far wall: forested plateau,\nseen but never trodden", (194, 206, 186))
    note(150, 132, "bench wall on the\ntraveller's RIGHT")
    note(30, 44, "WHISPERWOOD — wraps everything;\nother valleys implied, not drafted",
         (190, 206, 172))

    # ------------------------------------------------------------ long section
    py0 = PAD_T + H
    s.rectangle([0, py0, W, py0 + PROF_H], fill=(21, 20, 19))
    s.text((22, py0 + 14), "LONG SECTION along the corridor — the proposition is VERTICAL",
           font=f19, fill=(246, 238, 220))

    def arclen(pts):
        p = np.asarray([(q[0], q[1]) for q in pts], float)
        seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
        return np.concatenate([[0.0], np.cumsum(seg)])

    rs, rh = arclen(rp), np.array([p[2] for p in rp])
    ds = F.roadpts
    os_, oh = arclen(ds), np.array([p[2] for p in ds])
    total = max(rs[-1], os_[-1])
    x0, x1 = 92, W - 40
    y1, y0 = py0 + PROF_H - 46, py0 + 62
    hmin, hmax = -8.0, 38.0

    def px(sv):
        return x0 + (x1 - x0) * sv / total

    def pz(hv):
        return y1 - (y1 - y0) * (hv - hmin) / (hmax - hmin)

    for hv in range(-5, 36, 5):
        s.line([x0, pz(hv), x1, pz(hv)], fill=(46, 44, 42), width=1)
        s.text((x0 - 44, pz(hv) - 9), "h%+d" % hv, font=f14, fill=(140, 136, 130))

    # the ground either side of the river, as a section band
    gseg = np.linspace(0, rs[-1], 400)
    gx_ = np.interp(gseg, rs, [p[0] for p in rp])
    gy_ = np.interp(gseg, rs, [p[1] for p in rp])
    band = []
    for off in (-14.0, 14.0):
        hh = []
        for a, b in zip(gx_, gy_):
            hh.append(float(F.height(np.clip(a + off, 0, DL.TILE_W - .5), b)))
        band.append(np.array(hh))
    top = np.maximum(band[0], band[1])
    s.polygon([(px(a), pz(min(b, hmax))) for a, b in zip(gseg, top)]
              + [(px(gseg[-1]), y1), (px(gseg[0]), y1)], fill=(48, 44, 38))

    s.line([(px(a), pz(b)) for a, b in zip(os_, oh)], fill=(238, 216, 168), width=4)
    s.line([(px(a), pz(b)) for a, b in zip(rs, rh)], fill=(96, 178, 216), width=5)

    def vmark(sv, hv, txt, col, dy=-30):
        s.line([px(sv), pz(hv), px(sv), y1], fill=(90, 86, 80), width=1)
        s.text((px(sv) - 4, pz(hv) + dy), txt, font=f14, fill=col)

    vmark(rs[9], 28.2, "OLD GATE h28", (255, 214, 92), -34)
    vmark(rs[11], 18.5, "EMBER FALLS\n27.0 -> 18.5", (150, 214, 240), 8)
    vmark(rs[22], 4.2, "DELLHOLLOW pool h4", (255, 226, 150), -34)
    vmark(rs[25], -4.2, "MOORAGE h-4", (150, 214, 240), -34)
    s.text((px(rs[4]) - 30, pz(30.3) - 34), "EMBERBROOK h30", font=f14, fill=(255, 226, 150))

    s.text((x0, py0 + PROF_H - 34),
           "river (blue) 32.4 -> -5.0 = 37.4u fall  |  road (sand) 34.2 -> 12.0 = 22.2u  |  "
           "gate-to-Dellhollow river fall 24.0u over 96u of run  |  "
           "SHIPPED ow-valley for comparison: gate h24 -> Dellhollow h12 = 12u",
           font=f14, fill=(198, 174, 138))

    # ------------------------------------------------- the river's whole life
    ry0 = py0 + PROF_H
    s.rectangle([0, ry0, W, ry0 + RIVL_H], fill=(17, 16, 15))
    s.text((22, ry0 + 14), "THE RIVER DOES NOT STOP AT DELLHOLLOW — its whole course, schematic",
           font=f19, fill=(246, 238, 220))
    s.text((22, ry0 + 40),
           "Everything left of the bracket is DRAFTED at full scale on the tile above. "
           "Everything right of it is a SKETCH — not drafted, distances not to scale.",
           font=f14, fill=(150, 146, 138))

    stops = [
        (0.030, "Whisperwood\nheadwaters", 3.0, (198, 206, 186), 1),
        (0.115, "EMBERBROOK", 5.0, (255, 226, 150), -1),
        (0.170, "the village\nbridge", 5.4, (226, 200, 160), 1),
        (0.235, "THE OLD GATE\nEmber Falls", 4.6, (255, 214, 92), -1),
        (0.330, "the gorge", 7.0, (200, 200, 192), 1),
        (0.430, "DELLHOLLOW\nthe locks", 9.5, (255, 226, 150), -1),
        (0.495, "the Moorage\nCh3 departs by boat", 11.0, (150, 214, 240), 1),
        (0.610, "THE LONG REACH\nnorth through the deep wood", 14.0, (190, 200, 168), -1),
        (0.720, "Lanternstead (Ch3)", 17.0, (222, 214, 196), 1),
        (0.830, "the river broadens", 22.0, (170, 200, 214), -1),
        (0.925, "the estuary", 30.0, (150, 214, 240), 1),
    ]
    ax0, ax1 = 76, W - 232
    ay = ry0 + 150

    def rx(t):
        return ax0 + (ax1 - ax0) * t

    def ry(t):
        return ay + math.sin(t * 11.0) * 13.0 * (1.0 - t * 0.5)

    # the sea: the river runs INTO it, not up against a wall
    ox = W - 236
    s.rectangle([ox, ry0 + 62, W, ry0 + RIVL_H], fill=(27, 60, 78))
    for k in range(7):
        yy = ry0 + 78 + k * 24
        s.line([ox + 18 + (k % 2) * 20, yy, W - 18, yy], fill=(48, 94, 116), width=2)
    s.text((ox + 30, ry0 + 178), "THE OCEAN", font=f19, fill=(184, 220, 236),
           stroke_width=4, stroke_fill=(27, 60, 78))

    # the course as ONE polygon — a variable-width polyline renders as beads
    def halfw(t):
        return 1.6 + 8.0 * (t ** 1.8) + 34.0 * max(0.0, (t - 0.90) / 0.10) ** 1.6

    top = [(rx(i / 299.0), ry(i / 299.0) - halfw(i / 299.0)) for i in range(300)]
    bot = [(rx(i / 299.0), ry(i / 299.0) + halfw(i / 299.0)) for i in range(299, -1, -1)]
    s.polygon(top + bot, fill=(52, 112, 148))
    s.polygon([(ox, ry0 + 62), (ox + 26, ry0 + 62), (ox + 26, ry0 + RIVL_H),
               (ox, ry0 + RIVL_H)], fill=(36, 78, 100))

    for t, txt, _w, col, updown in stops:
        x, yy = rx(t), ry(t)
        s.ellipse([x - 5, yy - 5, x + 5, yy + 5], fill=col, outline=(16, 15, 14), width=2)
        n = len(txt.split("\n"))
        ty = yy - 26 - n * 18 if updown < 0 else yy + 24
        s.line([x, yy, x, ty + (n * 18 + 4 if updown < 0 else -4)],
               fill=(104, 100, 92), width=1)
        s.multiline_text((x - 2, ty), txt, font=f14, fill=col, spacing=3,
                         stroke_width=3, stroke_fill=(17, 16, 15))

    bx1 = rx(0.512)
    s.line([ax0 - 6, ry0 + RIVL_H - 26, bx1, ry0 + RIVL_H - 26], fill=(214, 190, 156), width=2)
    for xx in (ax0 - 6, bx1):
        s.line([xx, ry0 + RIVL_H - 32, xx, ry0 + RIVL_H - 20], fill=(214, 190, 156), width=2)
    s.text((ax0 + 6, ry0 + RIVL_H - 22), "DRAFTED — the 300 x 240u tile", font=f14,
           fill=(214, 190, 156))
    s.text((bx1 + 14, ry0 + RIVL_H - 22),
           "SKETCH — chapters of river still to design", font=f14, fill=(140, 136, 130))

    sheet.save(OUT)
    print("WROTE", OUT, sheet.size)


if __name__ == "__main__":
    main()
