#!/usr/bin/env python3
"""valley_layout.py — the CHEAP top-down layout preview of the valley region.

  python3 tools/valley_layout.py

Writes docs/qa/overworld/valley_layout.png: hillshaded heightfield + zone tint +
the river (at its real width), the road, the portals, the landmarks, the town
anchors, the rim treatments and the vista ring.  Pure numpy + PIL — no Blender —
so the geography can be taste-gated in a second while the 3D build runs.

Everything in it is read from the map files through valley_map, so this image and
the built tile cannot disagree: if the layout is wrong, the fix is a map edit.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valley_map as VM                                        # noqa: E402
import overworld3_lib as O3                                    # noqa: E402

OUT = os.path.join(VM.ROOT, "docs/qa/overworld/valley_layout.png")
PPU = 4                      # pixels per world unit at final size
SS = 2                       # supersample factor for the vector overlay
W, H = int(VM.TILE_W * PPU), int(VM.TILE_H * PPU)

ZONE_RGB = {
    "meadow": (150, 176, 96), "forest": (58, 96, 56), "crag": (150, 136, 120),
    "road": (198, 173, 126), "water": (62, 118, 148),
}


def font(sz):
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    F = VM.ValleyField()
    zg = VM.ValleyZoneGrid(F)

    # ---- raster pass: hillshade x zone tint ---------------------------------
    wx = np.linspace(0.0, VM.TILE_W, W)
    wy = np.linspace(VM.TILE_H, 0.0, H)                 # image rows run north->south
    GX, GY = np.meshgrid(wx, wy)
    Hh = F.sample(GX - VM.CX, GY - VM.CY)
    # crag displacement is part of the built ground, so the preview shows it
    Hh = Hh + O3.crag_disp(F, zg, GX - VM.CX, GY - VM.CY, None)

    # hillshade off a SMOOTHED height: the crag treatment is sub-metre relief and at
    # 4 px/u it turns the whole tile into speckle, which hides the landform the
    # preview exists to show.  Detail comes back as a separate multiply below.
    Hs = Hh.copy()
    for _ in range(3):
        Hs = 0.2 * (np.roll(Hs, 1, 0) + np.roll(Hs, -1, 0)
                    + np.roll(Hs, 1, 1) + np.roll(Hs, -1, 1) + Hs)
    gy_, gx_ = np.gradient(Hs, VM.TILE_H / H, VM.TILE_W / W)
    # dusk key from the south-west at 40deg — the same light the tile is built for
    lx, ly, lz = -0.60, -0.55, 0.58
    nrm = np.stack([-gx_, gy_, np.ones_like(Hh)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    lam = np.clip(nrm[..., 0] * lx + nrm[..., 1] * ly + nrm[..., 2] * lz, 0.0, 1.0)
    shade = 0.42 + 0.78 * lam
    gyd, gxd = np.gradient(Hh - Hs, VM.TILE_H / H, VM.TILE_W / W)
    shade = shade * (1.0 - 0.16 * np.clip(gxd * 0.9 + gyd * 0.9, -1.2, 1.2))

    # zone tint, sampled per pixel
    col = np.zeros(Hh.shape + (3,))
    zi = np.zeros(Hh.shape, int)
    cc = np.clip(((GX - VM.CX) - zg.origin[0]) / zg.cell, 0, zg.cols - 1).astype(int)
    rr = np.clip(((VM.CY - GY) - zg.origin[1]) / zg.cell, 0, zg.rows - 1).astype(int)
    zi = zg.idx[cc, rr]
    pal = np.array([ZONE_RGB[n] for n in O3.ZONES], float)
    zc = pal[zi]
    # HYPSOMETRIC ramp under the zone tint.  Zone colour alone made the whole
    # region read as one green plain: the descent is the thing being taste-gated,
    # so absolute height has to be in the image, not only in the shading.
    stops = np.array([-6.0, 0.0, 4.0, 8.0, 12.0, 18.0, 24.0, 30.0, 40.0, 52.0])
    ramp = np.array([[38, 74, 92], [86, 126, 96], [126, 164, 96], [162, 182, 96],
                     [190, 186, 96], [204, 172, 96], [206, 150, 92], [190, 134, 104],
                     [166, 148, 140], [228, 226, 220]], float)
    hyp = np.stack([np.interp(Hs, stops, ramp[:, k]) for k in range(3)], -1)
    col = hyp * 0.56 + zc * 0.44
    # forest and water are the two zones a hypsometric ramp cannot express, so they
    # get an extra push — a stand has to be visible as a stand
    col = np.where((zi == O3.Z_FOREST)[..., None], col * 0.62 + zc * 0.30, col)
    col = col * shade[..., None]

    # CONTOURS are what actually makes a descent legible in one still: 4u minor,
    # 20u major, both widened where the ground is flat so a plain still reads.
    slope2 = np.hypot(gx_, gy_)
    for iv, k, w in ((4.0, 0.30, 1.5), (20.0, 0.62, 2.6)):
        band = np.abs(((Hs + 400.0) % iv) - iv / 2)
        cline = np.clip(1.0 - band / (w * (0.10 + slope2)), 0.0, 1.0)
        col = col * (1.0 - k * cline[..., None])

    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).resize(
        (W * SS, H * SS), Image.BILINEAR)
    d = ImageDraw.Draw(img, "RGBA")

    def P(wx_, wy_):
        return (wx_ * PPU * SS, (VM.TILE_H - wy_) * PPU * SS)

    # ---- envelope ----------------------------------------------------------
    env = [P(*p) for p in VM.ENVELOPE]
    d.line(env + [env[0]], fill=(255, 255, 255, 90), width=2 * SS)

    # ---- the river, drawn at its authored width ----------------------------
    tg = np.gradient(VM.RIV_XY, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    nr = np.column_stack([-tg[:, 1], tg[:, 0]])
    hwv = (VM.RIV_WIDTH * 0.5)[:, None]
    left = VM.RIV_XY + nr * hwv
    right = VM.RIV_XY - nr * hwv
    d.polygon([P(*p) for p in left[::3]] + [P(*p) for p in right[::-3]],
              fill=(74, 150, 186, 240), outline=(168, 214, 238, 255))
    d.line([P(*p) for p in VM.RIV_XY[::4]], fill=(206, 236, 252, 190), width=SS)

    # ---- the road (built line) + the authored line it came from ------------
    d.line([P(*p) for p in VM.ROAD_CTRL_W[:, :2]], fill=(120, 90, 60, 130), width=SS)
    d.line([P(*p) for p in VM.ROAD_XY[::2]], fill=(244, 224, 168, 255),
           width=max(2, int(VM.ROAD_WIDTH * PPU * SS)))

    # ---- forest stamps -----------------------------------------------------
    for st in VM.FORESTS:
        pts = [P(*p) for p in st["stamp"]]
        d.line(pts + [pts[0]], fill=(150, 220, 150, 110), width=SS)
    # ---- plateau blob + gorge crag stamp -----------------------------------
    pts = [P(*p) for p in VM.PLATEAU["blob"]]
    d.line(pts + [pts[0]], fill=(255, 210, 140, 130), width=SS)
    for st in VM.REGION.get("zoneOverrides", []):
        if "stamp" in st:
            pts = [P(*p) for p in st["stamp"]]
            d.line(pts + [pts[0]], fill=(235, 160, 90, 140), width=SS)

    # ---- the unauthorised span the map forces ------------------------------
    for (a, b) in VM.ROAD_SPANS:
        pa, pb = P(*VM.ROAD_XY[a]), P(*VM.ROAD_XY[b])
        d.line([pa, pb], fill=(255, 70, 70, 255), width=4 * SS)
        d.text((pa[0] - 40 * SS, pa[1] - 26 * SS), "UNLISTED CROSSING",
               fill=(255, 120, 120, 255), font=font(9 * SS))

    f1, f2 = font(11 * SS), font(9 * SS)

    def dot(wx_, wy_, label, rgb, r=4, dx=7, dy=-6):
        x, y = P(wx_, wy_)
        d.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS],
                  fill=rgb + (255,), outline=(20, 16, 12, 255), width=SS)
        if label:
            d.text((x + dx * SS, y + dy * SS), label, fill=(255, 248, 236, 255), font=f2,
                   stroke_width=2, stroke_fill=(20, 16, 12, 220))

    for a in VM.REGION["townAnchors"]:
        x, y = P(a["pos"][0], a["pos"][1])
        r = float(a["impressionRadius"]) * PPU * SS
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 232, 170, 190), width=SS)
        dot(a["pos"][0], a["pos"][1],
            "%s  h%g" % (a["town"].upper(), a["pos"][2]), (255, 206, 110), r=5)
    for pid, po in VM.PORTALS.items():
        dot(po["at"][0], po["at"][1], "portal %s" % pid, (255, 140, 90), r=4)
    x, y = P(*VM.ROAD_END_W)
    d.ellipse([x - 5 * SS, y - 5 * SS, x + 5 * SS, y + 5 * SS],
              outline=(255, 140, 90, 255), width=2 * SS)
    d.text((x + 7 * SS, y + 3 * SS), "gate as BUILT", fill=(255, 190, 150, 255), font=f2,
           stroke_width=2, stroke_fill=(20, 16, 12, 220))
    for lid in ("ember-falls", "dellhollow-moorage", "waystone", "boat-tar",
                "pass-hollowmere"):
        if lid in VM.LAND_W:
            p = VM.LAND_W[lid]
            dot(p[0], p[1], lid, (150, 210, 255), r=3)
    for f in VM.FLOOR:
        dot(f["at"][0], f["at"][1], "floor h%g" % f["height"], (200, 200, 200), r=2)

    # ---- rim labels --------------------------------------------------------
    rim = VM.REGION["rim"]
    for txt, (px_, py_) in (("N rim: %s (crest 40)" % rim["north"], (140, 191)),
                            ("S rim: %s (crest 36)" % rim["south"], (140, 6)),
                            ("W rim: %s" % rim["west"], (7, 100)),
                            ("E rim: %s" % rim["east"], (262, 100))):
        x, y = P(px_, py_)
        d.text((x, y), txt, fill=(240, 226, 200, 230), font=f2, anchor="mm",
               stroke_width=2, stroke_fill=(20, 16, 12, 200))

    # ---- title block -------------------------------------------------------
    cov = zg.coverage()
    lines = [
        "THE VALLEY — chapters 1-2   %.0f x %.0fu   layout from the map files"
        % (VM.TILE_W, VM.TILE_H),
        "river %.0fu, %.0f -> %.0fu wide, z %.0f -> %.0f    road %.0fu, z %.0f -> %.0f"
        % (VM.RIVER_LEN, VM.RIV_WIDTH[0], VM.RIV_WIDTH[-1], VM.RIV_Z[0], VM.RIV_Z[-1],
           VM.ROAD_S[-1], VM.ROAD_Z[0], VM.ROAD_Z[-1]),
        "zones  " + "  ".join("%s %.0f%%" % (k, v) for k, v in cov.items()),
        "terrain h %.0f .. %.0f   plateau 26   gorge rim 12, cut 14   contours 5u"
        % (F.H.min(), F.H.max()),
    ]
    d.rectangle([6 * SS, 6 * SS, 470 * SS, 62 * SS], fill=(18, 14, 11, 205))
    for i, t in enumerate(lines):
        d.text((14 * SS, (12 + i * 13) * SS), t, fill=(255, 240, 216, 255),
               font=f1 if i == 0 else f2)

    # legend
    lx0, ly0 = 6 * SS, (VM.TILE_H * PPU - 24) * SS
    d.rectangle([lx0, ly0 - 4 * SS, lx0 + 330 * SS, ly0 + 20 * SS],
                fill=(18, 14, 11, 205))
    for i, n in enumerate(O3.ZONES):
        x = lx0 + (8 + i * 64) * SS
        d.rectangle([x, ly0 + 3 * SS, x + 10 * SS, ly0 + 13 * SS],
                    fill=ZONE_RGB[n] + (255,))
        d.text((x + 14 * SS, ly0 + 2 * SS), n, fill=(240, 228, 206, 255), font=f2)

    img = img.resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print("WROTE %s  (%d x %d, %.0f kB)" % (OUT, W, H, os.path.getsize(OUT) / 1e3))
    print(VM.describe())
    print("zones: " + "  ".join("%s=%.1f%%" % (k, v) for k, v in cov.items()))


if __name__ == "__main__":
    main()
