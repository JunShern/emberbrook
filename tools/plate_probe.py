"""plate_probe.py — READ A SHIPPED PLATE IN WORLD SPACE.  No Blender, no browser.

  python3 tools/plate_probe.py ground [shot ...]
  python3 tools/plate_probe.py crushed <shot> [...]              # where the black is
  python3 tools/plate_probe.py box <shot> x0 x1 y0 y1 z0 z1      # close-read one prop
  python3 tools/plate_probe.py water <shot> [...]                # the shore profile

WHY IT EXISTS.  The world-building doctrine says "for dusk grades, measure GROUND
luminance on the region probes — the floor is what has to be read", and there was
no instrument that could.  `plate_flat` audits background leak, `nav_eval` asks an
LLM, `cine_visprobe` needs Blender.  Nothing read the SHIPPED PIXELS and could say
which of them are floor.

WHAT IT DOES.  It reconstructs a world XYZ for every pixel out of the bundle's own
two files — `cine.json`'s solved camera and the `rgb24-viewz` `depth.png` the bake
wrote — then derives a per-pixel surface normal from the world-position gradient.
That splits the frame into GROUND (up-facing), WALL and VOID (far plane), which is
what makes "the floor of this plate is crushed" a number instead of an impression.
Everything else here is that one reconstruction asked a different question.

THREE THINGS IT IS CAREFUL ABOUT, each of which was wrong once:
  * depth.png is DATA (`colorSpace = NoColorSpace` in the runtime, for the same
    reason).  It is resampled to the beauty plate's grid with NEAREST only — a
    filtered tap averages the packed bytes of two different depths, which is not
    a depth of anything.  bg is 2688x1536 and depth is 1344x768; they are not the
    same grid and treating them as one throws an IndexError, which is the polite
    version of this mistake.
  * A DEPTH DISCONTINUITY FAKES A GRAZING NORMAL.  The gradient across a silhouette
    edge is enormous, so any sample whose neighbour is more than 1.5 m away in world
    space is dropped rather than classified.  Without that guard every roofline in
    town reports as ground.
  * DARK IS NOT CRUSHED.  `crushed` asks for dark AND LOCALLY FLAT (L <= 24/255 with
    a 5x5 standard deviation <= 2), because a dark surface that still carries texture
    is a shadow and a dark surface that carries none is a hole.  They want different
    fixes and only the second is a defect.

AND THE THING IT CANNOT DO: it names a REGION, never an object.  A world box out of
`crushed` is the input to a Blender ray census, which is what actually says the
pixels are `lock_four_dam`/`mat_blackstone`.  Do not skip that step — round 3 has
now twice recorded a worklist item whose named object was the wrong one.

Camera convention matches the bake: Blender Z-up, `sensor_fit` VERTICAL so `fov` is
angle_y, aim via `to_track_quat('-Z','Y')`.

ENV: `PLATE_BUNDLE` points at a different bundle directory (one holding `cine.json`
and `cameras/<shot>/{bg,depth}.png`).  That is how the A/B is made honest — extract
the BEFORE plates straight out of `git show HEAD:...` into a scratch bundle and read
BOTH with this one instrument, instead of comparing live pixels against a downscaled,
re-compressed gallery jpg.  `UPCOS`, `DARK`, `FLAT` and `STEP_MAX` override the
thresholds; the defaults are the ones every number in the round-3 receipts used.
"""
import os, sys, json, math
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = os.environ.get("PLATE_BUNDLE",
                        os.path.join(ROOT, "public/assets/scenes/del-cine"))
CINE = json.load(open(os.path.join(BUNDLE, "cine.json")))
CAMS = {c["id"]: c for c in CINE["cameras"]}

UPCOS = float(os.environ.get("UPCOS", "0.80"))     # |n.z| for "this is floor"
DARK = float(os.environ.get("DARK", "24"))
FLAT = float(os.environ.get("FLAT", "2.0"))
STEP_MAX = float(os.environ.get("STEP_MAX", "1.5"))   # world metres per pixel pair


# ------------------------------------------------------------------ helpers ---
def _basis(pos, aim):
    f = np.array(aim, float) - np.array(pos, float)
    f /= np.linalg.norm(f)
    up = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(f, up))) > 0.9999:
        up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up); r /= np.linalg.norm(r)
    return r, np.cross(r, f), f


def load(shot):
    """-> (cam, bg[H,W,3], viewdepth[H,W], void[H,W], world[H,W,3])"""
    c = CAMS[shot]
    bgi = Image.open(os.path.join(BUNDLE, "cameras", shot, "bg.png")).convert("RGB")
    dpi = Image.open(os.path.join(BUNDLE, "cameras", shot, "depth.png")).convert("RGB")
    if dpi.size != bgi.size:
        dpi = dpi.resize(bgi.size, Image.NEAREST)      # NEAREST only — see docstring
    bg = np.asarray(bgi).astype(np.float32)
    dp = np.asarray(dpi).astype(np.float64)
    n = dp[..., 0] * 65536 + dp[..., 1] * 256 + dp[..., 2]
    near, far = c["depth"]["near"], c["depth"]["far"]
    d = near + (far - near) * n / 16777215.0
    void = n >= 16777215 - 0.5
    H, W = d.shape
    ty = math.tan(math.radians(c["fov"]) / 2.0)
    ys = (1.0 - 2.0 * ((np.arange(H) + 0.5) / H)) * ty
    xs = (2.0 * ((np.arange(W) + 0.5) / W) - 1.0) * ty * (W / H)
    X, Y = np.meshgrid(xs, ys)
    r, u, f = _basis(c["pos"], c["aim"])
    P = (np.array(c["pos"], float)[None, None, :]
         + d[..., None] * (f[None, None, :] + X[..., None] * r[None, None, :]
                           + Y[..., None] * u[None, None, :]))
    return c, bg, d, void, P


def normals(P, void):
    dx = np.zeros_like(P); dy = np.zeros_like(P)
    dx[:, 1:-1, :] = P[:, 2:, :] - P[:, :-2, :]
    dy[1:-1, :, :] = P[2:, :, :] - P[:-2, :, :]
    N = np.cross(dx, dy)
    ln = np.linalg.norm(N, axis=2); ln[ln == 0] = 1
    N = N / ln[..., None]
    step = np.maximum(np.linalg.norm(dx, axis=2), np.linalg.norm(dy, axis=2))
    return N, (void | (step > STEP_MAX))


def lum(bg):
    return 0.2126 * bg[..., 0] + 0.7152 * bg[..., 1] + 0.0722 * bg[..., 2]


def local_sd(a, k=2):
    """5x5 standard deviation via integral images (no scipy in this repo)."""
    def box(x):
        p = np.pad(x, k, mode="edge")
        c = np.cumsum(np.cumsum(p, 0), 1)
        c = np.pad(c, ((1, 0), (1, 0)))
        n = 2 * k + 1; H, W = x.shape
        s = c[n:n + H, n:n + W] - c[0:H, n:n + W] - c[n:n + H, 0:W] + c[0:H, 0:W]
        return s / (n * n)
    m = box(a); m2 = box(a * a)
    return np.sqrt(np.maximum(m2 - m * m, 0))


# -------------------------------------------------------------------- modes ---
def cmd_ground(shots):
    print("%-14s %6s %6s | %10s %6s %6s %6s %6s | %8s %6s"
          % ("shot", "void%", "gnd%", "GROUND p05", "p25", "p50", "<=12%", "<=24%",
             "WALL p50", "<=24%"))
    for shot in shots:
        c, bg, d, void, P = load(shot)
        N, bad = normals(P, void)
        L = lum(bg)
        up = (np.abs(N[..., 2]) >= UPCOS) & (~bad)
        wall = (~up) & (~bad) & (~void)
        g = L[up] if up.sum() > 50 else np.zeros(1)
        w = L[wall] if wall.sum() > 50 else np.zeros(1)
        print("%-14s %6.2f %6.2f | %10.1f %6.1f %6.1f %6.2f %6.2f | %8.1f %6.2f"
              % (shot, 100 * void.mean(), 100 * up.mean(),
                 np.percentile(g, 5), np.percentile(g, 25), np.percentile(g, 50),
                 100 * (g <= 12).mean(), 100 * (g <= 24).mean(),
                 np.percentile(w, 50), 100 * (w <= 24).mean()))


def cmd_crushed(shots, minpx=1500):
    from collections import deque
    for shot in shots:
        c, bg, d, void, P = load(shot)
        N, bad = normals(P, void)
        L = lum(bg)
        m = (L <= DARK) & (local_sd(L) <= FLAT) & (~void)
        H, W = L.shape
        ms = m[::2, ::2]                       # label at half res; report full-res
        seen = np.zeros(ms.shape, bool)
        print("== %s  %dx%d  crushed %.2f%%" % (shot, W, H, 100 * m.mean()))
        regs = []
        for y0, x0 in np.argwhere(ms):
            if seen[y0, x0]:
                continue
            q = deque([(y0, x0)]); seen[y0, x0] = True; cells = []
            while q:
                y, x = q.popleft(); cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < ms.shape[0] and 0 <= xx < ms.shape[1] \
                       and ms[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; q.append((yy, xx))
            if len(cells) * 4 >= minpx:
                regs.append(cells)
        regs.sort(key=len, reverse=True)
        for cells in regs[:8]:
            ys = np.array([y * 2 for y, x in cells]); xs = np.array([x * 2 for y, x in cells])
            pw = P[ys, xs]; nn = N[ys, xs]
            print("   n=%6d (%5.2f%%) u=%.3f v=%.3f  world x[%7.2f,%7.2f] y[%7.2f,%7.2f]"
                  " z[%6.2f,%6.2f]  up=%.2f  L %5.1f+-%4.1f  dist %5.1f"
                  % (len(cells) * 4, 400.0 * len(cells) / L.size, xs.mean() / W, ys.mean() / H,
                     pw[:, 0].min(), pw[:, 0].max(), pw[:, 1].min(), pw[:, 1].max(),
                     pw[:, 2].min(), pw[:, 2].max(),
                     float((np.abs(nn[:, 2]) >= UPCOS).mean()),
                     L[ys, xs].mean(), L[ys, xs].std(), d[ys, xs].mean()))


def cmd_box(shot, box):
    c, bg, d, void, P = load(shot)
    N, bad = normals(P, void)
    L = lum(bg); sd = local_sd(L)
    mx = bg.max(2); mn = bg.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    m = ((~void) & (P[..., 0] >= box[0]) & (P[..., 0] <= box[1])
         & (P[..., 1] >= box[2]) & (P[..., 1] <= box[3])
         & (P[..., 2] >= box[4]) & (P[..., 2] <= box[5]))
    H, W = L.shape
    print("%s: %d px (%.3f%% of frame, %dx%d)" % (shot, int(m.sum()), 100 * m.mean(), W, H))
    if m.sum() < 20:
        return
    ys, xs = np.nonzero(m)
    print("  screen u %.3f..%.3f  v %.3f..%.3f  (%dx%d px)   dist %.1f m"
          % (xs.min() / W, xs.max() / W, ys.min() / H, ys.max() / H,
             xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, d[m].mean()))
    print("  L p05 %.1f p50 %.1f p95 %.1f mean %.1f sd %.1f"
          % (np.percentile(L[m], 5), np.percentile(L[m], 50), np.percentile(L[m], 95),
             L[m].mean(), L[m].std()))
    print("  LOCAL detail (5x5 sd): p50 %.2f p90 %.2f   flat(<=2)%% %.1f"
          % (np.percentile(sd[m], 50), np.percentile(sd[m], 90), 100 * (sd[m] <= 2).mean()))
    print("  sat %.3f  RGB %.1f,%.1f,%.1f  up-facing %.1f%%"
          % (sat[m].mean(), bg[..., 0][m].mean(), bg[..., 1][m].mean(), bg[..., 2][m].mean(),
             100 * float((np.abs(N[..., 2]) >= UPCOS)[m].mean())))


def cmd_water(shots):
    """Luminance as a function of DISTANCE FROM SHORE, in metres, on the water.

    A wet-shore contact band would show as a brighter ring inside ~0.5 m.  A pure
    depth-alpha shore shows the opposite: darker at the edge, because shallow water
    is transparent and what it reveals is unlit bed.  Both are legible here and they
    are different claims — "knife-sharp waterline" and "no foam" are not the same
    defect and this is what tells them apart."""
    from collections import deque
    sheets = json.load(open(os.path.join(ROOT, "tools/blends/districts/t2_water_shader.json")))
    ZS = [v["surface_z"] for v in sheets["sheets"].values()]
    for shot in shots:
        c, bg, d, void, P = load(shot)
        N, bad = normals(P, void)
        L = lum(bg)
        mx = bg.max(2); mn = bg.min(2)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
        up = (np.abs(N[..., 2]) >= UPCOS) & (~bad)
        water = np.zeros(L.shape, bool)
        for z in ZS:
            water |= up & (np.abs(P[..., 2] - z) <= 0.12)
        if water.sum() < 2000:
            print("== %s: water pixels %d — too few" % (shot, int(water.sum())))
            continue
        H, W = L.shape
        mpp = np.zeros(L.shape)
        mpp[:, 1:-1] = np.linalg.norm(P[:, 2:, :2] - P[:, :-2, :2], axis=2) / 2
        dist = np.full((H, W), 1e9)
        e = np.zeros((H, W), bool)
        nb = ~water
        e[1:-1, 1:-1] = water[1:-1, 1:-1] & (nb[:-2, 1:-1] | nb[2:, 1:-1]
                                             | nb[1:-1, :-2] | nb[1:-1, 2:])
        q = deque()
        for y, x in zip(*np.nonzero(e)):
            dist[y, x] = 0.0; q.append((y, x))
        while q:
            y, x = q.popleft(); dv = dist[y, x]
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and water[yy, xx]:
                    nd = dv + (mpp[yy, xx] if mpp[yy, xx] > 0 else 0.02)
                    if nd < dist[yy, xx] - 1e-9:
                        dist[yy, xx] = nd; q.append((yy, xx))
        print("== %s  water %.2f%% of frame, shore edge %d px"
              % (shot, 100 * water.mean(), int(e.sum())))
        for a, b in ((0, .15), (.15, .3), (.3, .5), (.5, .8), (.8, 1.2), (1.2, 2), (2, 4), (4, 1e9)):
            m = water & (dist >= a) & (dist < b)
            if m.sum() < 30:
                continue
            print("   %5.2f-%5.2f m  n=%7d  L %6.1f +-%5.1f  sat %.3f"
                  % (a, min(b, 99), int(m.sum()), L[m].mean(), L[m].std(), sat[m].mean()))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    mode, rest = a[0], a[1:]
    if mode == "ground":
        cmd_ground(rest or sorted(CAMS))
    elif mode == "crushed":
        cmd_crushed(rest or sorted(CAMS))
    elif mode == "box":
        cmd_box(rest[0], [float(v) for v in rest[1:7]])
    elif mode == "water":
        cmd_water(rest or sorted(CAMS))
    else:
        print(__doc__); sys.exit(2)
