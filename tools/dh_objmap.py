"""dh_objmap.py — ONE BLENDER PASS, THEN EVERY LATER QUESTION IS OFFLINE.

  # 1. dump: object + material + camera distance at every pixel of every solved camera
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_objmap.py -- dump --grid 240 --out /tmp/objmap.json

  # 2. read (NO Blender): what is inside a judge's bbox, on the geometry
  python3 tools/dh_objmap.py box /tmp/objmap.json lockfive 0,0.45,0.27,0.56

  # 3. read (NO Blender): an A/B of two plate trees over a NAMED SUBSET of the pixels
  python3 tools/dh_objmap.py ab /tmp/objmap.json <dirA> <dirB> --objects m_water --min 55

WHY IT EXISTS.  `dh_pixel_census` answers ONE question per Blender launch, and a round
that has to put five judge bboxes on the geometry, size a subject town-wide, and then
measure a before/after on exactly those pixels was spending four minutes of Blender per
question.  This dumps the whole map ONCE (15 cameras at 240x135 = 486,000 marched rays,
~4 min) and every question after that is numpy.  Round 7 answered eight of them off one
pass.  It reuses `dh_pixel_census`'s marcher, so `hide_render` objects are dropped and a
render-only volume card is passed THROUGH rather than reported as the thing making the
pixel — the two lies about the frame that census already paid for.

AND THE PROPERTY THAT MAKES THE A/B HONEST: the mask is RAY-DERIVED, not plate-derived,
so it is THE SAME PIXELS ON BOTH SIDES.  A mask recomputed from each plate (e.g. "the
crushed region") moves when the plate moves, which is exactly when you are measuring —
round 4 had to hand-carry a world-space box between two bundles to avoid this.  Here
"the water past 55 m" is one set of pixel indices and both renders are read through it.

  `--min` / `--max` bound CAMERA DISTANCE, which is how "the far water" is said in a
  language the plate cannot argue with.  `--objects` matches an object OR a material
  name, because the useful subject is sometimes one mesh and sometimes one material
  spread over many (`mat_rock_far` / `mat_silhouette`, the greybox far field).
"""
import os, sys, json, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
MODE = argv[0] if argv else ""


def arg(f, d=None):
    return argv[argv.index(f) + 1] if f in argv else d


def dump():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import dh_pixel_census as C
    import bpy
    from mathutils import Vector
    grid = int(arg("--grid", "240"))
    out = arg("--out", "/tmp/dh_objmap.json")
    cams = {c["id"]: c for c in json.load(open(os.path.join(
        ROOT, "public/assets/scenes/del-cine/cine.json")))["cameras"]}
    shots = (arg("--shots") or ",".join(cams)).split(",")
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    vol, skip = C._classify()
    res = {"grid": grid, "cams": {}}
    for sid in shots:
        c = cams[sid]
        p = Vector(c["pos"]); f = (Vector(c["aim"]) - p).normalized()
        r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
        ty = math.tan(math.radians(c["fov"]) / 2.0)
        W = grid; H = int(grid * 9 / 16)
        obj = []; mat = []; dist = []
        for iy in range(H):
            Y = (1.0 - 2.0 * ((iy + 0.5) / H)) * ty
            for ix in range(W):
                X = (2.0 * ((ix + 0.5) / W) - 1.0) * ty * (W / H)
                nm, mt, d, _, _ = C._march(sc, dg, p, (f + X * r + Y * u).normalized(),
                                           vol, skip)
                obj.append(nm or "<bg>"); mat.append(mt or "-")
                dist.append(round(d, 2) if d else -1.0)
        res["cams"][sid] = {"W": W, "H": H, "obj": obj, "mat": mat, "dist": dist}
        print("MAPPED %s %dx%d" % (sid, W, H))
    json.dump(res, open(out, "w"))
    print("SAVED %s" % out)


def _grid(objmap, sid):
    import numpy as np
    c = objmap["cams"][sid]
    H, W = c["H"], c["W"]
    return (np.array(c["obj"]).reshape(H, W), np.array(c["mat"]).reshape(H, W),
            np.array(c["dist"]).reshape(H, W))


def _resample(a, H, W):
    import numpy as np
    gh, gw = a.shape
    yy = ((np.arange(H) + 0.5) / H * gh).astype(int)
    xx = ((np.arange(W) + 0.5) / W * gw).astype(int)
    return a[np.ix_(yy, xx)]


def box():
    import numpy as np
    from collections import Counter
    objmap = json.load(open(argv[1]))
    sid = argv[2]
    u0, v0, u1, v1 = [float(x) for x in argv[3].split(",")]
    obj, mat, dist = _grid(objmap, sid)
    H, W = obj.shape
    m = np.zeros((H, W), bool)
    m[int(v0 * H):int(v1 * H), int(u0 * W):int(u1 * W)] = True
    n = max(1, int(m.sum()))
    print("%s  u %.3f..%.3f v %.3f..%.3f — %.2f%% of frame, distance p50 %.1f m"
          % (sid, u0, u1, v0, v1, 100 * m.mean(), float(np.median(dist[m]))))
    for (o, mt), v in Counter(zip(obj[m].tolist(), mat[m].tolist())).most_common(6):
        sel = m & (obj == o) & (mat == mt)
        print("   %5.1f%%  %-28s %-24s %6.1f m" % (100.0 * v / n, o, mt,
                                                   float(np.median(dist[sel]))))


def ab():
    import numpy as np
    from PIL import Image
    objmap = json.load(open(argv[1]))
    dirs = [argv[2], argv[3]]
    want = set((arg("--objects") or "").split(",")) - {""}
    dmin = float(arg("--min", "0")); dmax = float(arg("--max", "1e9"))

    def lum(a):
        return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

    def sd5(L, k=2):
        from numpy.lib.stride_tricks import sliding_window_view
        w = sliding_window_view(np.pad(L, k, mode='edge'), (2 * k + 1, 2 * k + 1))
        return w.std(axis=(-1, -2))

    print("%-14s %-20s %7s %7s %7s %7s %7s %8s"
          % ("shot", "tree", "%frame", "p05", "p50", "p95", "sd5", "crush%"))
    for d in dirs:
        cd = os.path.join(d, "cameras") if os.path.isdir(os.path.join(d, "cameras")) else d
        for sid in sorted(os.listdir(cd)):
            fp = os.path.join(cd, sid, "bg.png")
            if not os.path.exists(fp) or sid not in objmap["cams"]:
                continue
            obj, mat, dist = _grid(objmap, sid)
            L = lum(np.asarray(Image.open(fp).convert("RGB"), dtype=np.float32))
            H, W = L.shape
            o = _resample(obj, H, W); mt = _resample(mat, H, W)
            dd = _resample(dist, H, W)
            m = (np.isin(o, list(want)) | np.isin(mt, list(want))) if want else (dd > 0)
            m &= (dd >= dmin) & (dd < dmax)
            if m.sum() < 200:
                continue
            s = sd5(L)
            print("%-14s %-20s %7.2f %7.1f %7.1f %7.1f %7.2f %8.1f"
                  % (sid, os.path.basename(d), 100 * m.mean(),
                     np.percentile(L[m], 5), np.percentile(L[m], 50),
                     np.percentile(L[m], 95), float(np.median(s[m])),
                     100.0 * ((L <= 24) & (s <= 2.0) & m).sum() / m.sum()))


if __name__ == "__main__":
    if MODE == "dump":
        dump()
    elif MODE == "box":
        box()
    elif MODE == "ab":
        ab()
    else:
        raise SystemExit(__doc__)
