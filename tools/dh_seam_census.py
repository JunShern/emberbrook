"""dh_seam_census.py — WHERE DOES ONE OBJECT'S EDGE MEET ANOTHER'S, AND IS THAT EDGE
A STRAIGHT LINE?

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_seam_census.py -- seam --a 'cliff_town_' --b cliff_east_closure --grid 240
  Blender -b … -P tools/dh_seam_census.py -- sky --prefix cliff_town_ --grid 200
  Blender -b … -P tools/dh_seam_census.py -- box --shot gate --u0 .43 --u1 .52 --v0 0 --v1 .3

WHY IT EXISTS.  `scene_redteam`'s sharpest recurring complaint about this town is a
SILHOUETTE — "a sharp vertical seam", "cuts off abruptly in a straight vertical line" —
and until this there was no instrument that could say WHICH TWO OBJECTS make an edge, or
whether that edge is actually straight.  `plate_probe` names a region; `dh_pixel_census`
names the object at a pixel; neither can say "these 32 pixels are the boundary between A
and B, they span u 0.465..0.477, and they sit 6.5 px from a straight line".  It reuses
`dh_pixel_census`'s marcher, so `hide_render` objects are dropped and a render-only
volume card is passed through rather than reported as the thing making the pixel.

  `seam`  every pixel where a member of set A is horizontally adjacent to a member of
          set B: count, columns, the u span, the RMS residual from a best-fit straight
          line (in PLATE pixels, so it is comparable across grids), and the world x/y/z
          and camera distance of the A-side hit points — which is what says WHAT PART of
          A is doing the silhouetting.
  `sky`   the same question against the world background: for every column, the topmost
          pixel of the named prefix whose neighbour above is background.  ZERO columns
          means the object's top edge is not in that frame at all, however flat it is.
  `box`   an object census of an arbitrary (u, v) window plus a column/row run-length
          scan — for putting a judge's own bbox on the geometry.

WHAT IT MEASURED FIRST (round 5, 2026-08-08, and both halves matter).  The round-4
handover named `cliff_town_*`'s "top clamped perfectly flat at z = 37.0" as "a
dead-straight silhouette against the sky".  `sky` over all fifteen solved cameras: ZERO
silhouette columns anywhere, world background 0.00-0.03% of every frame — DELLHOLLOW IS
A CLOSED GORGE.  `seam` then put the real edge at u 0.465..0.477 on gate, which is the
judge's own bbox (0.466..0.478) to three decimals, with the wall side at y -2.5..-0.35 —
the builder's front clamp — 122-153 m out.  AND THE STRAIGHTNESS NUMBER IS WHAT REFUSED
THE OBVIOUS FIX: unflattening that clamp moved the residual 6.5 px -> 7.0 px, i.e. not at
all, because AT GRAZING INCIDENCE A SILHOUETTE IS THE ENVELOPE OF THE CRESTS OVER TENS OF
METRES AND AN ENVELOPE IS STRAIGHT HOWEVER THE CRESTS WANDER.

A NOTE ON THE STRAIGHTNESS FIGURE: it is a screen, not a verdict.  It is quantised by the
grid (a column is 2688/grid plate pixels) and a TILTED straight line has a wide u span and
a small residual, so read the two together — and then look at the plate.  The seam this
tool was written for went u span 32 -> 67 plate px with the residual unchanged, and the
picture is what said that was the fix landing.
"""
import os, sys, json, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import dh_pixel_census as C
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
MODE = argv[0] if argv else ""
PLATE_W, PLATE_H = 2688.0, 1536.0


def arg(f, d=None):
    return argv[argv.index(f) + 1] if f in argv else d


CAMS = {c["id"]: c for c in json.load(open(os.path.join(
    ROOT, "public/assets/scenes/del-cine/cine.json")))["cameras"]}
SC = bpy.context.scene
DG = bpy.context.evaluated_depsgraph_get()
VOL, SKIP = C._classify()


def cast(c, W, H, u0=0.0, u1=1.0, v0=0.0, v1=1.0):
    """-> names[H][W] (base object name or '<bg>'), pts[H][W] (world Vector or None)"""
    p = Vector(c["pos"]); f = (Vector(c["aim"]) - p).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
    ty = math.tan(math.radians(c["fov"]) / 2.0)
    ar = PLATE_W / PLATE_H
    names = [[None] * W for _ in range(H)]
    pts = [[None] * W for _ in range(H)]
    for iy in range(H):
        Y = (1.0 - 2.0 * (v0 + (v1 - v0) * (iy + 0.5) / H)) * ty
        for ix in range(W):
            X = (2.0 * (u0 + (u1 - u0) * (ix + 0.5) / W) - 1.0) * ty * ar
            dv = (f + X * r + Y * u).normalized()
            nm, _mat, dist, _taus, _cards = C._march(SC, DG, p, dv, VOL, SKIP)
            names[iy][ix] = (nm or "<bg>").split('.')[0]
            pts[iy][ix] = (p + dv * dist) if dist is not None else None
    return names, pts


def straightness(cols, rows, W):
    """RMS residual of the seam from a best-fit line u = m*v + b, in PLATE pixels."""
    if len(cols) < 4:
        return None
    mx = sum(rows) / len(rows); my = sum(cols) / len(cols)
    sxx = sum((a - mx) ** 2 for a in rows) or 1e-9
    m = sum((a - mx) * (b - my) for a, b in zip(rows, cols)) / sxx
    b0 = my - m * mx
    rr = [b - (m * a + b0) for a, b in zip(rows, cols)]
    return math.sqrt(sum(v * v for v in rr) / len(rr)) * PLATE_W / W


def match(name, spec):
    return any(name == s or (s.endswith("_") and name.startswith(s)) for s in spec)


if MODE == "seam":
    A = (arg("--a") or "cliff_town_").split(",")
    B = (arg("--b") or "cliff_east_closure").split(",")
    G = int(arg("--grid", "240")); W, H = G, int(G * 9 / 16)
    shots = (arg("--shots") or ",".join(CAMS)).split(",")
    print("A=%s  B=%s  grid=%dx%d" % (",".join(A), ",".join(B), W, H))
    print("%-14s %6s %5s %9s %14s  %s" % ("shot", "seam", "cols", "straight", "u span", "world, A side"))
    for sid in shots:
        c = CAMS[sid]
        names, pts = cast(c, W, H)
        cols, rows, wp = [], [], []
        for iy in range(H):
            for ix in range(W - 1):
                l, r = names[iy][ix], names[iy][ix + 1]
                if match(l, A) and match(r, B):
                    cols.append(ix); rows.append(iy); wp.append(pts[iy][ix])
                elif match(l, B) and match(r, A):
                    cols.append(ix); rows.append(iy); wp.append(pts[iy][ix + 1])
        if not cols:
            print("%-14s %6d %5s %9s %14s" % (sid, 0, "-", "-", "-"))
            continue
        s = straightness(cols, rows, W)
        wp = [p for p in wp if p is not None]
        w = "-"
        if wp:
            eye = Vector(c["pos"])
            w = ("x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f  %.0f..%.0f m"
                 % (min(p.x for p in wp), max(p.x for p in wp),
                    min(p.y for p in wp), max(p.y for p in wp),
                    min(p.z for p in wp), max(p.z for p in wp),
                    min((p - eye).length for p in wp), max((p - eye).length for p in wp)))
        print("%-14s %6d %5d %6s px %6.3f-%.3f  %s"
              % (sid, len(cols), len(set(cols)), ("%.1f" % s) if s else "-",
                 (min(cols) + 0.5) / W, (max(cols) + 0.5) / W, w))

elif MODE == "sky":
    P = (arg("--prefix") or "cliff_town_").split(",")
    G = int(arg("--grid", "200")); W, H = G, int(G * 9 / 16)
    shots = (arg("--shots") or ",".join(CAMS)).split(",")
    print("prefix=%s  grid=%dx%d   (a column counts when a prefix pixel's neighbour ABOVE "
          "is the world background)" % (",".join(P), W, H))
    print("%-14s %8s %9s %9s   %s" % ("shot", "obj%", "bg%", "sil cols", "top-edge world z"))
    for sid in shots:
        c = CAMS[sid]
        names, pts = cast(c, W, H)
        n = W * H
        nobj = sum(1 for row in names for v in row if match(v, P))
        nbg = sum(1 for row in names for v in row if v == "<bg>")
        zs = []
        for ix in range(W):
            for iy in range(1, H):
                if match(names[iy][ix], P) and names[iy - 1][ix] == "<bg>":
                    if pts[iy][ix] is not None:
                        zs.append(pts[iy][ix].z)
                    break
        print("%-14s %7.2f%% %8.2f%% %9d   %s"
              % (sid, 100.0 * nobj / n, 100.0 * nbg / n, len(zs),
                 ("z %.2f..%.2f" % (min(zs), max(zs))) if zs else "-"))

elif MODE == "box":
    sid = arg("--shot", "gate")
    G = int(arg("--grid", "150"))
    u0, u1 = float(arg("--u0", "0")), float(arg("--u1", "1"))
    v0, v1 = float(arg("--v0", "0")), float(arg("--v1", "1"))
    c = CAMS[sid]
    W = G
    H = max(1, int(G * (v1 - v0) * PLATE_H / ((u1 - u0) * PLATE_W)))
    names, _ = cast(c, W, H, u0, u1, v0, v1)
    from collections import Counter
    cnt = Counter(v for row in names for v in row)
    n = W * H
    print("BOX %s u %.3f..%.3f v %.3f..%.3f  %dx%d = %d rays" % (sid, u0, u1, v0, v1, W, H, n))
    for k, v in cnt.most_common(14):
        print("   %-28s %6.2f%%  (%d)" % (k, 100.0 * v / n, v))
    iy = H // 2
    print("\nrow scan at v=%.4f:" % (v0 + (v1 - v0) * (iy + 0.5) / H))
    runs = []
    for ix in range(W):
        v = names[iy][ix]
        if not runs or runs[-1][0] != v:
            runs.append([v, ix, ix])
        runs[-1][2] = ix
    for a, i0, i1 in runs:
        print("   %-28s u %.4f .. %.4f" % (a, u0 + (u1 - u0) * (i0 + 0.5) / W,
                                           u0 + (u1 - u0) * (i1 + 0.5) / W))

else:
    raise SystemExit("modes: seam | sky | box   (see the docstring)")
