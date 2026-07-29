"""overworld_lib.py — shared geometry field + helpers for the overworld art-direction proto.

The whole prototype rests on ONE analytic height field (a miniature FF9-style valley
tile, 120 x 90 units) so that all four art treatments sit on IDENTICAL terrain and the
comparison is about treatment, not about luck of the blockout.

Nothing here touches materials — see overworld_build.py for the four styles.
"""
import math
import numpy as np

# ---------------------------------------------------------------- tile constants
TILE_X, TILE_Y = 120.0, 90.0           # miniature valley: 120 wide, 90 deep
STEP = 1.25                            # terrain grid pitch (facet size for style A)
NX = int(TILE_X / STEP) + 1            # 97
NY = int(TILE_Y / STEP) + 1            # 73

VILLAGE = (-30.0, 20.0)                # cozy village cluster (8 tiny houses + hearth)
CLIFFTOWN = (43.0, -29.0)              # cliff-notch town marker
CHAR_H = 1.45                          # runtime character height — the scale contract

# river centreline control (t in 0..1 runs west -> east across the whole tile)
GORGE_T0, GORGE_T1 = 0.72, 0.98        # the gorge notch cut through the east rim
DAM_T = 0.735                          # dam / waterwheel sits at the gorge head

# water level down the river's length: a gentle fall, then the dam's 4.5u spillway drop
_WL_T = np.array([0.00, 0.30, 0.55, 0.700, 0.730, 0.745, 0.800, 1.00])
_WL_H = np.array([5.80, 5.00, 4.40, 4.000, 3.900, -0.60, -1.600, -3.00])

# winding road: village -> river bridge -> cliff-notch town.  Deliberately never
# straight for more than ~6u so the follow-camera always has something to turn around.
ROAD_CTRL = [(-30.0, 20.0), (-25.5, 15.0), (-18.0, 11.6), (-10.5, 13.8), (-3.0, 11.4),
             (3.5, 8.6), (9.0, 6.4), (14.0, 3.4), (18.5, -1.2), (23.0, -6.4),
             (27.5, -11.8), (33.5, -17.6), (38.5, -23.4), (43.0, -29.0)]


def sstep(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def catmull(ctrl, n):
    """Resample a control polyline as a Catmull-Rom spline -> n points."""
    p = np.array(ctrl, dtype=float)
    p = np.vstack([p[0] + (p[0] - p[1]), p, p[-1] + (p[-1] - p[-2])])
    segs = len(p) - 3
    out = []
    for i in range(segs):
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        for k in range(n // segs):
            t = k / (n // segs)
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t +
                              (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)


def resample(poly, spacing):
    """Arc-length resample a polyline at a fixed spacing; returns pts + cumulative s."""
    d = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)])
    total = s[-1]
    ns = np.arange(0.0, total, spacing)
    ns = np.concatenate([ns, [total]])
    out = np.column_stack([np.interp(ns, s, poly[:, 0]), np.interp(ns, s, poly[:, 1])])
    return out, ns


def river_pts(n=601):
    t = np.linspace(0.0, 1.0, n)
    x = -64.0 + 128.0 * t
    y = 14.0 * np.sin(2.6 * t + 0.2) + 8.0 * np.sin(7.0 * t + 0.9) - 6.0
    return t, x, y


def water_level(t):
    return np.interp(t, _WL_T, _WL_H)


def gorge_factor(t):
    """1 inside the gorge notch, 0 in the open valley."""
    return sstep(GORGE_T0, GORGE_T0 + 0.05, t) * (1.0 - sstep(GORGE_T1, 1.02, t))


class Field:
    """The shared terrain field: heights plus every per-vertex mask the styles need."""

    def __init__(self):
        xs = np.linspace(-TILE_X / 2, TILE_X / 2, NX)
        ys = np.linspace(-TILE_Y / 2, TILE_Y / 2, NY)
        self.xs, self.ys = xs, ys
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        self.X, self.Y = X, Y

        # ---- river: distance + downstream parameter for every grid point
        rt, rx, ry = river_pts()
        self.river = np.column_stack([rx, ry])
        self.rt = rt
        d2 = (X[..., None] - rx) ** 2 + (Y[..., None] - ry) ** 2
        idx = np.argmin(d2, axis=-1)
        self.dr = np.sqrt(np.take_along_axis(d2, idx[..., None], -1)[..., 0])
        self.tr = rt[idx]
        self.wl = water_level(self.tr)
        g = gorge_factor(self.tr)
        self.gorge = g

        # ---- rolling hills, referenced to the local water level so the whole tile
        #      drains toward the river and inherits the river's downstream fall
        dev = (2.4 * np.sin(X * 0.052) * np.cos(Y * 0.068)
               + 1.6 * np.sin(X * 0.105 + 1.3) * np.sin(Y * 0.088 + 0.6)
               + 0.8 * np.sin(X * 0.190 + 2.1) * np.cos(Y * 0.163)
               + 0.45 * np.sin(X * 0.330 + 0.4) * np.sin(Y * 0.290 + 1.7))
        H = self.wl + 6.5 + dev + 0.09 * np.minimum(self.dr, 45.0)

        # ---- mountain rim enclosing the tile, gated open where the river passes
        ex, ey = np.abs(X) / (TILE_X / 2), np.abs(Y) / (TILE_Y / 2)
        e = (ex ** 10 + ey ** 10) ** 0.1
        amp = 16.5 + 6.0 * np.sin(X * 0.11 + 0.7) * np.cos(Y * 0.15 + 1.4) \
            + 4.0 * np.sin(X * 0.26) * np.sin(Y * 0.22)
        rim = sstep(0.58, 1.0, e) * np.maximum(amp, 7.0)
        gate = 1.0 - 0.93 * np.clip(1.0 - (self.dr - 4.0) / 11.0, 0.0, 1.0)
        self.rim = rim * gate
        H = H + self.rim

        # ---- river valley: bed, banks, and a narrow deep notch in the gorge
        W = 11.0 - 5.0 * g
        bank = 4.5 + 11.0 * g
        q = np.clip(self.dr / W, 0.0, 1.0)
        bed = self.wl - 0.7 - 0.5 * g
        prof = bed + (self.wl + bank - bed) * sstep(0.0, 1.0, q)
        s = sstep(0.0, 1.0, 1.0 - q)
        H = H * (1.0 - s) + prof * s
        self.H = H
        self.valley_w, self.bank_h = W, bank

        # ---- road corridor: graded, lifted clear of the water at the bridge
        road = catmull(ROAD_CTRL, 260)
        self.road, self.road_s = resample(road, 1.0)
        rh = self.sample(self.road[:, 0], self.road[:, 1])
        # bridge: force the profile above the local water line near the crossing
        rdr, rtt = self._river_dist(self.road[:, 0], self.road[:, 1])
        near = rdr < 11.0
        rh[near] = np.maximum(rh[near], water_level(rtt[near]) + 2.9)
        k = np.ones(11) / 11.0
        for _ in range(4):
            rh = np.convolve(np.pad(rh, 5, mode="edge"), k, mode="valid")
        self.road_h = rh
        self.bridge_i = int(np.argmin(rdr))

        d2r = (X[..., None] - self.road[:, 0]) ** 2 + (Y[..., None] - self.road[:, 1]) ** 2
        ridx = np.argmin(d2r, axis=-1)
        self.drd = np.sqrt(np.take_along_axis(d2r, ridx[..., None], -1)[..., 0])
        self.ridx = ridx
        wroad = (1.0 - sstep(2.6, 7.5, self.drd)) * sstep(2.4, 5.2, self.dr)
        H = H * (1.0 - wroad) + rh[ridx] * wroad
        self.H = H

        # ---- village shelf + cliff-notch terrace (sampled AFTER the road grade so
        #      the road ends and the terraces agree by construction)
        for (cx, cy), (r0, r1), drop in ((VILLAGE, (6.5, 14.0), 0.0),
                                         (CLIFFTOWN, (5.5, 11.5), 1.5)):
            dv = np.hypot(X - cx, Y - cy)
            w = 1.0 - sstep(r0, r1, dv)
            h0 = float(self.sample(np.array([cx]), np.array([cy]))[0]) - drop
            H = H * (1.0 - w) + h0 * w
            self.H = H
        self.village_h = float(self.sample(*[np.array([v]) for v in VILLAGE])[0])
        self.clifftown_h = float(self.sample(*[np.array([v]) for v in CLIFFTOWN])[0])

        # ---- per-vertex analysis masks used by every style's palette
        gx, gy = np.gradient(H, STEP, STEP)
        self.slope = np.sqrt(gx * gx + gy * gy)
        nz = 1.0 / np.sqrt(1.0 + self.slope ** 2)
        self.nz = nz
        alt = H - self.wl                              # height above the local river
        self.alt = alt

        rock = sstep(0.55, 1.35, self.slope)
        peak = sstep(17.0, 28.0, alt) * (0.35 + 0.65 * rock)
        sand = (1.0 - rock) * (1.0 - sstep(1.2, 5.0, self.dr - 0.0)) * sstep(-1.4, 0.4, alt)
        dirt = (1.0 - sstep(0.95, 2.1, self.drd)) * sstep(2.2, 4.4, self.dr)
        # three octaves: big autumn stands read from the vista, ~10u breakup keeps the
        # chase camera (16u out) from ever filling the frame with one flat colour
        patch = 0.5 + 0.5 * (np.sin(X * 0.105 + 1.3) * np.sin(Y * 0.125 - 0.4)
                             + 0.55 * np.sin(X * 0.30 - 0.8) * np.sin(Y * 0.26 + 2.2)
                             + 0.32 * np.sin(X * 0.62 + 0.3) * np.sin(Y * 0.55 - 1.1))
        autumn = np.clip(patch - 0.52, 0.0, 1.0) * 2.2 * (1.0 - rock) * (1.0 - sstep(9.0, 17.0, alt))
        ghi = sstep(6.0, 15.0, alt) * (1.0 - rock)
        base = np.clip(1.0 - rock - peak - sand - dirt - autumn - ghi, 0.0, 1.0)
        w = np.stack([base, ghi, autumn, rock, peak, sand, dirt], axis=-1)
        # a couple of box-filter passes: without this the per-face argmax used by the
        # faceted styles flips class between neighbouring facets and reads as noise
        for _ in range(2):
            k = np.zeros_like(w)
            for dx_, dy_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                k += np.roll(np.roll(w, dx_, 0), dy_, 1)
            w = k / 5.0
        w = np.maximum(w, 0.0)
        self.w = w / np.maximum(w.sum(-1, keepdims=True), 1e-6)

        # a gentle multiplicative shading field: close-range surface life that costs
        # nothing (it rides in the same vertex colours) and works in every style
        self.shade = (1.0 + 0.12 * np.sin(X * 0.52 + 0.4) * np.sin(Y * 0.47 - 1.2)
                      + 0.08 * np.sin(X * 1.05 - 2.0) * np.sin(Y * 0.93 + 0.7))

        # mesh-space jitter: breaks the perfect grid so facets read as terrain,
        # not as a chessboard.  Boundary stays exact so the edge skirt still welds.
        rng = np.random.RandomState(7)
        mask = np.zeros_like(X)
        mask[1:-1, 1:-1] = 1.0
        self.MX = X + (rng.rand(*X.shape) - 0.5) * 0.72 * STEP * mask
        self.MY = Y + (rng.rand(*X.shape) - 0.5) * 0.72 * STEP * mask

    # ------------------------------------------------------------------ sampling
    def sample(self, x, y):
        """Bilinear height lookup (accepts arrays)."""
        fx = np.clip((np.asarray(x, float) + TILE_X / 2) / STEP, 0, NX - 1.001)
        fy = np.clip((np.asarray(y, float) + TILE_Y / 2) / STEP, 0, NY - 1.001)
        i0, j0 = fx.astype(int), fy.astype(int)
        tx, ty = fx - i0, fy - j0
        H = self.H
        return (H[i0, j0] * (1 - tx) * (1 - ty) + H[i0 + 1, j0] * tx * (1 - ty) +
                H[i0, j0 + 1] * (1 - tx) * ty + H[i0 + 1, j0 + 1] * tx * ty)

    def slope_at(self, x, y):
        fx = np.clip((np.asarray(x, float) + TILE_X / 2) / STEP, 0, NX - 1.001)
        fy = np.clip((np.asarray(y, float) + TILE_Y / 2) / STEP, 0, NY - 1.001)
        return self.slope[fx.astype(int), fy.astype(int)]

    def _river_dist(self, x, y):
        rx, ry = self.river[:, 0], self.river[:, 1]
        d2 = (np.asarray(x, float)[:, None] - rx) ** 2 + (np.asarray(y, float)[:, None] - ry) ** 2
        i = np.argmin(d2, axis=-1)
        return np.sqrt(d2[np.arange(len(i)), i]), self.rt[i]

    def river_dist(self, x, y):
        return self._river_dist(x, y)[0]

    def road_dist(self, x, y):
        rx, ry = self.road[:, 0], self.road[:, 1]
        d2 = (np.asarray(x, float)[:, None] - rx) ** 2 + (np.asarray(y, float)[:, None] - ry) ** 2
        return np.sqrt(d2.min(axis=-1))

    def water_halfwidth(self, t):
        """Where the valley profile crosses the water line — the river's visible width."""
        t = np.asarray(t, float)
        g = gorge_factor(t)
        W, bank = 11.0 - 5.0 * g, 4.5 + 11.0 * g
        wl = water_level(t)
        bed = wl - 0.7 - 0.5 * g
        k = (wl - bed) / (wl + bank - bed)
        qq = np.linspace(0.0, 1.0, 400)
        return np.interp(k, sstep(0.0, 1.0, qq), qq) * W

    def road_point(self, s):
        """Point + unit tangent at arc-length fraction s in 0..1 along the road."""
        i = int(np.clip(s, 0, 1) * (len(self.road) - 1))
        i = max(1, min(len(self.road) - 2, i))
        p = self.road[i]
        tg = self.road[i + 1] - self.road[i - 1]
        tg = tg / np.linalg.norm(tg)
        return float(p[0]), float(p[1]), float(self.road_h[i]), (float(tg[0]), float(tg[1]))
