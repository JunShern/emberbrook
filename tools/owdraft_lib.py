#!/usr/bin/env python3
"""owdraft_lib.py — the analytic field for the HANGING-VALLEY PROPOSAL DRAFT.

  *** PROPOSAL. NOT CANON. Nothing here is read by any shipped scene. ***

Reads docs/qa/overworld-draft/embercorridor-draft.region.json and nothing else.
It deliberately does NOT import valley_map / overworld_lib: those monkeypatch the
shipped pipeline against the RATIFIED map files, and this draft exists precisely
to disagree with them.  Same doctrine though — the map file is the authority, the
builder authors no geography — so a taste change is a JSON edit and a re-run.

The field is river-relative, which is what makes the proposition expressible:

    terrace(p) = waterH(s) + clear(s) + rise(s) * ramp(d / riseDist(s))

where s is the nearest point along the ONE river polyline and d the distance to
it.  In the hanging valley clear~1.2 and rise runs out over 55u (gentle farmland);
below the notch clear climbs 4 -> 16 and rise runs out over 9 -> 24u (gorge).  The
land therefore falls because THE WATER falls, which is the whole claim under test.
Mountain arms are laid on top as ridge polylines with per-vertex crests; the
gatewall range carries exactly one gap, and that gap is the water gap.

No bpy: the layout preview, the Blender build and the exporter all sample the same
grid, so the picture and the tile cannot disagree.
"""
import json
import os

import numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
DRAFT_P = os.path.join(ROOT, "docs/qa/overworld-draft/embercorridor-draft.region.json")
QA = os.path.join(ROOT, "docs/qa/overworld-draft")
SEED = 20260731                      # deterministic: the same tile every run

D = json.load(open(DRAFT_P))
TILE_W, TILE_H = D["tile"]
CX, CY = TILE_W / 2.0, TILE_H / 2.0          # world coords of the blender origin
STEP = D["step"]
GSTEP = D["gridStep"]
CHAR_H = D["charHeight"]
KEY = D["sceneKey"]


# --------------------------------------------------------------- polyline helper
class Poly:
    """A polyline carrying per-vertex attributes, resampled to a fine spacing.

    query(x, y) -> (distance, attributes interpolated at the nearest sample)
    A resampled point cloud beats exact segment projection here: the courses are
    already dense, and a KD-free chunked argmin over ~600 samples is both simple
    and fast enough for the 300x240 grid."""

    def __init__(self, pts, attrs, spacing=0.4):
        pts = np.asarray(pts, float)
        attrs = np.asarray(attrs, float)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        self.length = float(cum[-1])
        n = max(2, int(round(self.length / spacing)) + 1)
        t = np.linspace(0.0, self.length, n)
        self.P = np.stack([np.interp(t, cum, pts[:, 0]),
                           np.interp(t, cum, pts[:, 1])], axis=1)
        self.A = np.stack([np.interp(t, cum, attrs[:, k])
                           for k in range(attrs.shape[1])], axis=1)
        self.s = t

    def query(self, x, y, chunk=40000):
        x = np.asarray(x, float).ravel()
        y = np.asarray(y, float).ravel()
        dist = np.empty(x.size)
        idx = np.empty(x.size, dtype=np.int64)
        for i in range(0, x.size, chunk):
            j = slice(i, min(i + chunk, x.size))
            dx = x[j][:, None] - self.P[None, :, 0]
            dy = y[j][:, None] - self.P[None, :, 1]
            d2 = dx * dx + dy * dy
            k = np.argmin(d2, axis=1)
            idx[j] = k
            dist[j] = np.sqrt(d2[np.arange(k.size), k])
        return dist, self.A[idx], self.s[idx]


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _vnoise(x, y, freq, seed):
    """Deterministic value noise, bilinear on an integer lattice."""
    gx, gy = x * freq, y * freq
    x0, y0 = np.floor(gx).astype(np.int64), np.floor(gy).astype(np.int64)
    fx, fy = gx - x0, gy - y0

    def h(i, j):
        n = (i * 374761393 + j * 668265263 + seed * 2654435761) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFFFF) / 0xFFFFFF - 0.5

    u, v = smoothstep(fx), smoothstep(fy)
    a = h(x0, y0) * (1 - u) + h(x0 + 1, y0) * u
    b = h(x0, y0 + 1) * (1 - u) + h(x0 + 1, y0 + 1) * u
    return a * (1 - v) + b * v


# ------------------------------------------------------------------------- field
class DraftField:
    def __init__(self):
        rp = D["river"]["points"]
        self.river = Poly([(p[0], p[1]) for p in rp],
                          [(p[2], p[3], p[4], p[5], p[6]) for p in rp])
        self.road = None                    # pass 2 — the bench is read off the land
        self.ridges = []
        for r in D["ridges"]["list"]:
            self.ridges.append((
                Poly([(p[0], p[1]) for p in r["points"]], [(p[2],) for p in r["points"]]),
                float(r["halfWidth"]),
                np.asarray(r.get("gaps", []), float).reshape(-1, 3)))
        self.channelDepth = float(D["river"]["channelDepth"])

        # one shared 0.5u lattice; everything else bilinearly samples it
        self.nx = int(round(TILE_W / GSTEP)) + 1
        self.ny = int(round(TILE_H / GSTEP)) + 1
        self.gx = np.linspace(0.0, TILE_W, self.nx)
        self.gy = np.linspace(0.0, TILE_H, self.ny)
        GX, GY = np.meshgrid(self.gx, self.gy)          # [ny, nx]
        self._build(GX, GY)

    # -- the analytic stack ---------------------------------------------------
    def _build(self, GX, GY):
        sh = GX.shape
        x, y = GX.ravel(), GY.ravel()

        rd, ra, _ = self.river.query(x, y)
        wh, ww, clear, rise, riseD = (ra[:, 0], ra[:, 1], ra[:, 2], ra[:, 3], ra[:, 4])

        bank = wh + clear
        d0 = ww * 0.5 + 1.5                              # the flat bank strip
        ramp = smoothstep((rd - d0) / np.maximum(riseD, 1e-3))
        terrace = bank + rise * ramp
        # past the shoulder the land must KEEP climbing, gently.  A terrace that
        # goes dead flat is determined only by which river vertex is nearest, and
        # that shows up in the hillshade as radiating facets.
        ff = D.get("farField", {})
        terrace = terrace + np.minimum(
            np.maximum(rd - (d0 + riseD), 0.0) * float(ff.get("slope", 0.10)),
            float(ff.get("cap", 9.0)))

        # OUTER HILLS: the Whisperwood is hill country, not a plain.  Applied to the
        # TERRACE, before the arms, so a ridge is always higher than its own
        # surroundings — added afterwards it cut hard-edged blades through them.
        hm = smoothstep((rd - float(ff.get("hillsFrom", 55.0)))
                        / float(ff.get("hillsOver", 45.0)))
        hn = (_vnoise(x, y, 1 / 46.0, SEED + 101)
              + 0.55 * _vnoise(x, y, 1 / 23.0, SEED + 103))
        terrace = terrace + np.maximum(hn, -0.15) * hm * float(ff.get("hillsAmp", 15.0))

        # ridges sit ON the terrace: take the strongest, never stack
        add = np.zeros_like(terrace)
        for poly, hw, gaps in self.ridges:
            dd, aa, _ = poly.query(x, y)
            prof = 0.5 * (1.0 + np.cos(np.pi * np.clip(dd / hw, 0.0, 1.0)))
            for gxg, gyg, gr in gaps:
                dg = np.hypot(x - gxg, y - gyg)
                prof = prof * smoothstep(dg / gr)
            add = np.maximum(add, np.maximum(aa[:, 0] - terrace, 0.0) * prof)
        h = terrace + add

        # relief: strong on the arms, gentle on the farmed valley floor
        # NOTE: the fine octave is deliberately small.  At blockout the gorge walls
        # are near-vertical, and a 3u-wavelength octave on a vertical face renders
        # as corduroy, not as rock — measured in the first round of renders.
        relief = np.clip(add / 12.0, 0.0, 1.0) * 1.5 + 0.85
        n = (_vnoise(x, y, 1 / 17.0, SEED) * 1.0
             + _vnoise(x, y, 1 / 7.0, SEED + 7) * 0.30
             + _vnoise(x, y, 1 / 3.1, SEED + 31) * 0.07)
        h = h + n * relief * 2.2

        # the channel is carved LAST so noise can never dam the river
        cut = smoothstep((ww * 0.5 + 1.2 - rd) / 1.6)
        h = h * (1 - cut) + (wh - self.channelDepth) * cut

        self.H0 = h.reshape(sh)                 # UNGRADED land — the road reads this
        self.WH = wh.reshape(sh)
        self.WD = rd.reshape(sh)
        self.WW = ww.reshape(sh)
        self.TER = terrace.reshape(sh)
        self.ADD = add.reshape(sh)

        # ---- pass 2: lay the bench, CARVE its shelf, then grade the road corridor
        self.roadpts = self._solve_road()
        self.road = Poly([(p[0], p[1]) for p in self.roadpts],
                         [(p[2],) for p in self.roadpts])
        dr, ar, _ = self.road.query(x, y)
        rh = ar[:, 0]

        sp = D["road"].get("shelf")
        if sp:
            hw = float(sp["halfWidth"])
            up = smoothstep((hw + float(sp["backRun"]) - dr) / float(sp["backRun"]))
            dn = smoothstep((hw + float(sp["outerRun"]) - dr) / float(sp["outerRun"]))
            blend = np.where(h > rh, up, dn)
            blend = np.where(dr < hw, 1.0, blend)
            h = h * (1 - blend) + rh * blend

        w = float(D["road"]["width"])
        g = smoothstep((w * 1.9 - dr) / (w * 1.3))
        h = h * (1 - g) + (rh - 0.14) * g
        self.H = h.reshape(sh)
        self.RD = dr.reshape(sh)

    def _solve_road(self):
        """Above the gate: the map's authored valley course.  Below it: the bench,
        resampled off the river so the switchbacks are curves rather than corners.
        The height is authored because MEASUREMENT SAID SO — see road._doc: the
        natural gorge profile has no ledge at these offsets, so one is carved."""
        pts = [(p[0], p[1], p[2]) for p in D["road"]["points"]]
        bench = D["road"].get("bench")
        if not bench:
            return pts

        rp = D["river"]["points"]
        P = np.array([(p[0], p[1]) for p in rp], float)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        bs = np.array([b[0] for b in bench], float)
        bo = np.array([b[1] for b in bench], float)
        bz = np.array([b[2] for b in bench], float)
        s = np.linspace(bs[0], bs[-1], int((bs[-1] - bs[0]) / 1.0) + 1)
        off = np.interp(s, bs, bo)
        hh = np.interp(s, bs, bz)
        cx_ = np.interp(s, cum, P[:, 0])
        cy_ = np.interp(s, cum, P[:, 1])
        eps = 0.4
        tx = np.interp(s + eps, cum, P[:, 0]) - np.interp(s - eps, cum, P[:, 0])
        ty = np.interp(s + eps, cum, P[:, 1]) - np.interp(s - eps, cum, P[:, 1])
        tl = np.hypot(tx, ty)
        rx, ry = ty / tl, -tx / tl              # RIGHT of the flow direction
        bx = np.clip(cx_ + rx * off, 1.0, TILE_W - 1.0)
        by = np.clip(cy_ + ry * off, 1.0, TILE_H - 1.0)
        # a road is smooth; the offset schedule's corners are not
        k = 7
        for arr in (bx, by):
            arr[:] = np.convolve(np.pad(arr, k // 2, mode="edge"),
                                 np.ones(k) / k, mode="valid")
        return pts + [(float(a), float(c), float(e))
                      for a, c, e in zip(bx[1:], by[1:], hh[1:])]

    # -- sampling -------------------------------------------------------------
    def _bilinear(self, G, x, y):
        fx = np.clip(np.asarray(x, float) / GSTEP, 0, self.nx - 1.001)
        fy = np.clip(np.asarray(y, float) / GSTEP, 0, self.ny - 1.001)
        x0, y0 = fx.astype(np.int64), fy.astype(np.int64)
        tx, ty = fx - x0, fy - y0
        a = G[y0, x0] * (1 - tx) + G[y0, x0 + 1] * tx
        b = G[y0 + 1, x0] * (1 - tx) + G[y0 + 1, x0 + 1] * tx
        return a * (1 - ty) + b * ty

    def height(self, x, y):
        return self._bilinear(self.H, x, y)

    def water(self, x, y):
        return self._bilinear(self.WH, x, y)

    def riverdist(self, x, y):
        return self._bilinear(self.WD, x, y)

    def riverwidth(self, x, y):
        return self._bilinear(self.WW, x, y)

    def roaddist(self, x, y):
        return self._bilinear(self.RD, x, y)


# ------------------------------------------------------------------------ zones
def polymask(poly, X, Y):
    """even-odd point-in-polygon, vectorised"""
    P = np.asarray(poly, float)
    inside = np.zeros(X.shape, bool)
    n = len(P)
    for i in range(n):
        x1, y1 = P[i]
        x2, y2 = P[(i + 1) % n]
        cond = ((y1 > Y) != (y2 > Y))
        with np.errstate(divide="ignore", invalid="ignore"):
            xin = (x2 - x1) * (Y - y1) / np.where(y2 == y1, 1e-9, y2 - y1) + x1
        inside ^= cond & (X < xin)
    return inside


ZONES = ["meadow", "forest", "crag", "road", "water", "farm"]
ZONE_RGB = {"meadow": (150, 176, 96), "forest": (58, 96, 56), "crag": (150, 136, 120),
            "road": (198, 173, 126), "water": (62, 118, 148), "farm": (196, 178, 92)}


def zone_grid(F, cell=1.25):
    """Same taxonomy as the shipped zones.json plus a draft-only 'farm' type — the
    hanging valley being FARMED rather than wooded is half the proposition."""
    cols = int(TILE_W / cell)
    rows = int(TILE_H / cell)
    X, Y = np.meshgrid((np.arange(cols) + 0.5) * cell, (np.arange(rows) + 0.5) * cell)
    h = F.height(X, Y)
    z = np.zeros(X.shape, np.int8)                      # meadow

    for f in D["forests"]:
        z[polymask(f["stamp"], X, Y)] = 1
    for s in D["farmland"]["stamps"]:
        z[polymask(s["poly"], X, Y)] = 5

    gy, gx = np.gradient(h, cell)
    slope = np.hypot(gx, gy)
    z[slope > np.percentile(slope, 84)] = 2                 # crag beats forest/farm

    # water and road overrule everything
    z[F.roaddist(X, Y) < 1.9] = 3
    z[F.riverdist(X, Y) < F.riverwidth(X, Y) * 0.5] = 4
    return z, cell, cols, rows


if __name__ == "__main__":
    F = DraftField()
    print("tile %gx%g  grid %dx%d  h %.1f .. %.1f"
          % (TILE_W, TILE_H, F.nx, F.ny, F.H.min(), F.H.max()))
    for lm in D["landmarks"]:
        x, y, z = lm["pos"]
        print("  %-20s map z=%6.2f   built h=%6.2f   dz=%+.2f"
              % (lm["id"], z, F.height(x, y), F.height(x, y) - z))
