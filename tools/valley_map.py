"""valley_map.py — the VALLEY region's analytic field, DERIVED FROM THE MAP FILES.

  public/world/world.json                 (river spine, massifs, envelopes)
  public/world/regions/valley.region.json (elevation story, river, road, forests…)

This module is the bridge between the user-ratified geography hierarchy and the F2
overworld pipeline (tools/overworld{,2,3}_{lib,build}.py).  It does TWO things:

 1. it MONKEYPATCHES overworld_lib's tile constants and river functions so that
    every F2 system — the zone grid, the crag treatment, the tessellation, the
    planting, the mooring basin — operates on a 280 x 200u region instead of the
    prototype's 120 x 90u tile.  That is the whole reuse strategy: F2's systems
    are parameterised by `overworld_lib`, so re-pointing overworld_lib at real
    map data is cheaper AND truer than forking them.

 2. it builds ValleyField, a drop-in for overworld_lib.Field whose height field is
    an analytic reading of the region's elevation story:

        plateau   Emberbrook's highland mesa (h26); its SE lip is Ember Falls
        floor     four control heights, read as bank-above-water along the river,
                  so the whole region drains to the river and inherits its fall
        gorge     the spine 7-9 stretch: shoulders forced to rim height, channel
                  cut below it (this is why Dellhollow needs locks)
        rim       north/south ridges, the west forestwall, the east escarpment
        river     the refined 27-point course, carved with the PARENT's width
                  profile (3u at the falls -> 22u at the SE exit)
        road      graded to its own authored z, so map and terrain cannot disagree

No bpy: the field, the zone grid and the layout preview all run under plain
python3, which is what makes the cheap taste-gate preview possible.

COORDINATES.  world/region files use one world frame, [x, y] = east, north, over
[0, 280] x [0, 200].  Blender is centred: bx = wx - 140, by = wy - 100.  The
runtime is +x east / +z south: rx = bx, rz = -by.
"""
import json
import math
import os

import numpy as np

import overworld_lib as L

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
WORLD_P = os.path.join(ROOT, "public/world/world.json")
REGION_P = os.path.join(ROOT, "public/world/regions/valley.region.json")

WORLD = json.load(open(WORLD_P))
REGION = json.load(open(REGION_P))
REGION_ID = REGION["region"]
REG_META = [r for r in WORLD["regions"] if r["id"] == REGION_ID][0]

# ------------------------------------------------------------------ tile constants
# The TERRAIN tile is the massifs' extent (0..280 x 0..200); the PLAYABLE envelope
# is the region's own inset (10..270 x 10..195), so the rim treatments have 5-10u
# of land to stand on and the vista ring has somewhere to be beyond that.
TILE_W, TILE_H = 280.0, 200.0
CX, CY = TILE_W / 2.0, TILE_H / 2.0          # world coords of the blender origin
STEP = 1.6                                    # terrain facet pitch (F2 used 1.25 on
                                              # a tile 5.2x smaller in area)
ZONE_CELL = 1.25                              # the GAMEPLAY grid stays F2's pitch
ENVELOPE = REG_META["envelope"]

# patch overworld_lib's tile so every inherited system sizes itself to the region
L.TILE_X, L.TILE_Y, L.STEP = TILE_W, TILE_H, STEP
L.NX = int(round(TILE_W / STEP)) + 1
L.NY = int(round(TILE_H / STEP)) + 1

CHAR_H = L.CHAR_H                             # 1.45u — the scale contract
HOUSE_RIDGE = 1.6                             # ridge height of an impression house


def w2b(wx, wy):
    """world -> blender."""
    return np.asarray(wx, float) - CX, np.asarray(wy, float) - CY


def b2w(bx, by):
    return np.asarray(bx, float) + CX, np.asarray(by, float) + CY


def w2r(wx, wy):
    """world -> runtime (x, z)."""
    return np.asarray(wx, float) - CX, CY - np.asarray(wy, float)


def poly_b(pts):
    """A world polygon as a list of blender (x, y) tuples."""
    return [(float(p[0] - CX), float(p[1] - CY)) for p in pts]


def poly_r(pts):
    """A world polygon as a list of runtime (x, z) tuples."""
    return [(float(p[0] - CX), float(CY - p[1])) for p in pts]


def sstep(a, b, x):
    return L.sstep(a, b, x)


# ---------------------------------------------------------------------- polylines
def _resample(poly, spacing):
    d = np.linalg.norm(np.diff(poly[:, :2], axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)])
    ns = np.arange(0.0, s[-1], spacing)
    ns = np.concatenate([ns, [s[-1]]])
    out = np.column_stack([np.interp(ns, s, poly[:, k]) for k in range(poly.shape[1])])
    return out, ns


def _arclen(pts):
    d = np.linalg.norm(np.diff(np.asarray(pts, float)[:, :2], axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(d)])


def _chunked_nearest(px, py, cx, cy, block=96):
    """Nearest-point index over a long polyline without a 20M-element temporary.

    The prototype's field built one (NX, NY, 601) distance cube; at region scale
    that is 174 MB per array, so the same query is chunked over the centreline.
    """
    shp = np.shape(px)
    px = np.asarray(px, float).ravel()
    py = np.asarray(py, float).ravel()
    best_d = np.full(px.shape, 1e18)
    best_i = np.zeros(px.shape, np.int64)
    for k in range(0, len(cx), block):
        sx, sy = cx[k:k + block], cy[k:k + block]
        d2 = (px[:, None] - sx) ** 2 + (py[:, None] - sy) ** 2
        j = np.argmin(d2, axis=1)
        dv = d2[np.arange(len(px)), j]
        upd = dv < best_d
        best_d[upd] = dv[upd]
        best_i[upd] = j[upd] + k
    return np.sqrt(best_d).reshape(shp), best_i.reshape(shp)


# ---- the river: refined course + the PARENT's width profile ------------------
RIV_CTRL = np.array(REGION["river"]["points"], float)            # (27, 3) world
SPINE = np.array([p["pos"] for p in WORLD["riverSpine"]["points"]], float)
SPINE_W = np.array([p["width"] for p in WORLD["riverSpine"]["points"]], float)

_rs = _arclen(RIV_CTRL)
_ss = _arclen(SPINE)
# The refined course and the coarse spine describe the SAME river, so normalised
# arc-length is the correspondence: width comes from the parent, meander from the
# child, and neither has to know about the other.
RIV_W_CTRL = np.interp(_rs / _rs[-1], _ss / _ss[-1], SPINE_W)

# a smooth centreline: Catmull-Rom through the authored points, then arc-length
# resampled at 0.5u so distance queries are accurate to a few centimetres
_sm = L.catmull([(p[0], p[1]) for p in RIV_CTRL], 26 * 24)
RIV_XY, RIV_S = _resample(_sm, 0.5)
RIV_T = RIV_S / RIV_S[-1]
# z and width ride the AUTHORED points' arc-length, mapped onto the smoothed course
_t_ctrl = _rs / _rs[-1]
RIV_Z = np.interp(RIV_T, _t_ctrl, RIV_CTRL[:, 2])
RIV_WIDTH = np.interp(RIV_T, _t_ctrl, RIV_W_CTRL)
RIVER_LEN = float(RIV_S[-1])

# the gorge stretch, read off the parent's spine indices
GORGE_I0, GORGE_I1 = REGION["elevation"]["gorge"]["alongSpine"]
GORGE_RIM = float(REGION["elevation"]["gorge"]["rimHeight"])
GORGE_CUT = float(REGION["elevation"]["gorge"]["cutDepth"])


def _t_at(wx, wy):
    """Downstream parameter of the river point nearest a world position."""
    i = int(np.argmin((RIV_XY[:, 0] - wx) ** 2 + (RIV_XY[:, 1] - wy) ** 2))
    return float(RIV_T[i])


T_GORGE0 = _t_at(*SPINE[GORGE_I0][:2])
T_GORGE1 = _t_at(*SPINE[GORGE_I1][:2])
# Ember Falls: the plateau lip sits just downstream of the river's source, and the
# authored z drops 24 -> 14 over the 32u that follow.  That reach IS the falls.
T_LIP = float(np.interp(11.0, RIV_S, RIV_T))
T_FALLS_END = float(np.interp(34.0, RIV_S, RIV_T))


def river_pts(n=601):
    """(t, x, y) in BLENDER coords — the signature overworld_lib's callers expect."""
    t = np.linspace(0.0, 1.0, n)
    x = np.interp(t, RIV_T, RIV_XY[:, 0]) - CX
    y = np.interp(t, RIV_T, RIV_XY[:, 1]) - CY
    return t, x, y


def water_level(t):
    return np.interp(np.asarray(t, float), RIV_T, RIV_Z)


def river_width(t):
    return np.interp(np.asarray(t, float), RIV_T, RIV_WIDTH)


def water_halfwidth(t):
    return river_width(t) * 0.5


def gorge_factor(t):
    """1 through Dellhollow's gorge, tapering downstream — the reason the locks
    exist AND the reason a boat can leave: the notch OPENS toward the SE exit."""
    t = np.asarray(t, float)
    up = sstep(T_GORGE0 - 0.075, T_GORGE0 - 0.005, t)
    down = 1.0 - 0.72 * sstep(T_GORGE0 + 0.02, 1.0, t)
    return np.clip(up * down, 0.0, 1.0)


# patch the module-level river API the inherited code calls
L.river_pts = river_pts
L.water_level = water_level
L.gorge_factor = gorge_factor
L.GORGE_T0, L.GORGE_T1 = T_GORGE0, 1.0
L.DAM_T = T_GORGE0                       # the weir flight AT Dellhollow: crag_disp
                                         # keeps this patch of ground exact
L.ROAD_CTRL = [(p[0] - CX, p[1] - CY) for p in REGION["road"]["points"]]

# ---- landmarks / anchors, in every frame we need -----------------------------
LAND_W = {l["id"]: l["pos"] for l in WORLD["landmarks"]}
LAND_W.update({l["id"]: l["pos"] for l in REGION["landmarks"]})
PORTALS = {p["id"]: p for p in REGION["road"]["portals"]}
ANCHORS = {a["town"]: a for a in REGION["townAnchors"]}
EMBERBROOK = ANCHORS["emberbrook"]["pos"]
DELLHOLLOW = ANCHORS["dellhollow"]["pos"]
GATE_W = PORTALS["dellhollow-valley-gate"]["at"]
TOWNGATE_W = PORTALS["emberbrook-gate"]["at"]

# The two guards F2's crag treatment keeps exact are named VILLAGE and CLIFFTOWN in
# overworld_lib.  Here VILLAGE is Emberbrook's plateau shelf; CLIFFTOWN is the
# VALLEY GATE APRON, deliberately NOT Dellhollow itself — Dellhollow's whole
# character is broken gorge rock, and suppressing crag at its anchor would flatten
# exactly the thing that makes the impression read.
L.VILLAGE = (EMBERBROOK[0] - CX, EMBERBROOK[1] - CY)
L.CLIFFTOWN = (GATE_W[0] - CX, GATE_W[1] - CY)

# ---- the road ---------------------------------------------------------------
ROAD_CTRL_W = np.array(REGION["road"]["points"], float)
ROAD_WIDTH = float(REGION["road"]["width"])
_rd_sm = L.catmull([(p[0], p[1]) for p in ROAD_CTRL_W], 14 * 22)
ROAD_RAW, _ = _resample(_rd_sm, 1.0)


# ---- ROAD/RIVER CLEARANCE ---------------------------------------------------
# THE ONE MAP CONFLICT THIS BUILD HAD TO RULE ON (reported, not edited).
#
# Emberbrook's road runs the river's RIGHT bank from [72,138] to [130,95]; the
# Valley Gate approach runs its LEFT bank from [160,75] to [215,65].  Between them
# is the parent spine's "second meander back west" (apex [138,82]), a hairpin whose
# neck the road cuts across — so the road changes bank, i.e. it CROSSES the river,
# while region.crossings.list is empty by ruling.  There is no route that avoids
# this without moving either the road's first half onto the left bank (~16u) or the
# apex itself (a parent-spine feature).  Both are the coordinator's call.
#
# What the build does, deterministically, from the map alone:
#   1. every road station standing IN the water is pushed radially to the nearest
#      dry bank (hw + 1.6), capped at 6u — this is a nudge, not a re-route, and it
#      is what stops the ribbon from being submerged along the gorge-rim climb;
#   2. whatever channel the road still spans after that is reported as a SPAN, and
#      the build lays a low culverted causeway there (CAUSEWAY=True) so the tile is
#      playable.  Set CAUSEWAY=False the moment the map grows a crossing or the
#      road is re-routed, and nothing else changes.
CLEAR = 1.6                      # dry bank the road keeps beside the water
CLEAR_CAP = 6.0                  # nudge, never re-route
CAUSEWAY = True                  # build the unauthorised span (see above)
ROAD_PUSH = []                   # [(station, world x, y, total push)] — reported


def _river_frame(xy):
    d, i = _chunked_nearest(xy[:, 0] - CX, xy[:, 1] - CY,
                            RIV_XY[:, 0] - CX, RIV_XY[:, 1] - CY)
    hw = water_halfwidth(RIV_T[i])
    return d, i, hw


def _seg_hits(xy):
    """Every plan intersection of the road with the river, as road station floats."""
    hits = []
    A, B = xy[:-1], xy[1:]
    for k in range(len(A)):
        p, r = A[k], B[k] - A[k]
        q = RIV_XY[:-1]
        s = RIV_XY[1:] - RIV_XY[:-1]
        den = r[0] * s[:, 1] - r[1] * s[:, 0]
        ok = np.abs(den) > 1e-9
        qp = q - p
        t = np.where(ok, (qp[:, 0] * s[:, 1] - qp[:, 1] * s[:, 0]) / np.where(ok, den, 1), -1)
        u = np.where(ok, (qp[:, 0] * r[1] - qp[:, 1] * r[0]) / np.where(ok, den, 1), -1)
        m = ok & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
        for tt in t[m]:
            hits.append(k + float(tt))
    return sorted(hits)


def _runs(mask):
    out, run = [], None
    for k in range(len(mask)):
        if mask[k] and run is None:
            run = k
        elif not mask[k] and run is not None:
            out.append((run, k - 1))
            run = None
    if run is not None:
        out.append((run, len(mask) - 1))
    return out


def road_clearance(xy, passes=2):
    """Clear the road of the water where that is possible, and REPORT where it is not.

    Per contiguous wet run, count the road/river plan intersections inside it:
      EVEN (usually 2) — the road dips into the channel and comes back out on the
        bank it started on.  An authoring accident: push the whole run to that bank.
      ODD (1)          — the road genuinely changes bank.  No lateral push can fix
        that; the run is reported as a SPAN and the build causeways it.
    """
    xy = xy.copy()
    tot = np.zeros(len(xy))
    spans = []
    for it in range(passes):
        d, i, hw = _river_frame(xy)
        need = hw + CLEAR
        hits = _seg_hits(xy)
        spans = []
        for (a, b) in _runs(d < need):
            n_hit = sum(1 for h in hits if a - 1 <= h <= b + 1)
            j1 = np.minimum(i[a:b + 1] + 1, len(RIV_XY) - 1)
            j0 = np.maximum(i[a:b + 1] - 1, 0)
            tg = RIV_XY[j1] - RIV_XY[j0]
            tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
            nr = np.column_stack([-tg[:, 1], tg[:, 0]])
            u = ((xy[a:b + 1] - RIV_XY[i[a:b + 1]]) * nr).sum(1)
            if n_hit % 2 == 1:
                spans.append((a, b))
                continue
            k0 = max(a - 1, 0)                     # the clean station in front
            side = np.sign(u[0]) if abs(u[0]) > 0.2 else 1.0
            if a > 0:
                du = xy[k0] - RIV_XY[i[k0]]
                side = np.sign(du[0] * nr[0, 0] + du[1] * nr[0, 1]) or side
            push = np.clip(need[a:b + 1] - u * side, 0.0, CLEAR_CAP)
            xy[a:b + 1] = xy[a:b + 1] + nr * (side * push)[:, None]
            tot[a:b + 1] += push
        # a 3-tap smooth so a push does not leave two kinks; spans are left alone
        kk = np.array([0.22, 0.56, 0.22])
        sm = xy.copy()
        for c in (0, 1):
            sm[:, c] = np.convolve(np.pad(xy[:, c], 1, mode="edge"), kk, mode="valid")
        keep = np.zeros(len(xy), bool)
        for (a, b) in spans:
            keep[max(a - 2, 0):b + 3] = True
        xy[~keep] = sm[~keep]
    d, i, hw = _river_frame(xy)
    for k in np.nonzero(tot > 0.05)[0]:
        ROAD_PUSH.append((int(k), float(xy[k, 0]), float(xy[k, 1]), float(tot[k])))
    return xy, tot, spans, float((d - hw).min())


ROAD_XY, ROAD_PUSH_U, ROAD_SPANS, ROAD_SLACK = road_clearance(ROAD_RAW)
ROAD_S = _arclen(ROAD_XY)
# the BUILT endpoints: the authored portals, after the clearance nudge.  The Valley
# Gate portal marker is placed here, not at its authored [215,65] (which the
# clearance shows standing in the channel) — reported as a map-change request.
ROAD_START_W = (float(ROAD_XY[0, 0]), float(ROAD_XY[0, 1]))
ROAD_END_W = (float(ROAD_XY[-1, 0]), float(ROAD_XY[-1, 1]))
_road_tc = _arclen(ROAD_CTRL_W)
ROAD_Z = np.interp(ROAD_S / ROAD_S[-1], _road_tc / _road_tc[-1], ROAD_CTRL_W[:, 2])
# a light smoothing pass: the authored z is a 15-point polyline and the graded
# terrain reads its second derivative as a kink at every control point
_k = np.ones(7) / 7.0
for _ in range(3):
    ROAD_Z = np.convolve(np.pad(ROAD_Z, 3, mode="edge"), _k, mode="valid")

# ---- forests ----------------------------------------------------------------
FORESTS = REGION["forests"]

# ---- floor control, read as bank-height-above-water -------------------------
FLOOR = REGION["elevation"]["floor"]
PLATEAU = REGION["elevation"]["plateau"]


def _poly_dist(px, py, poly):
    """Signed-ish distance to a polygon: 0 inside, +distance outside."""
    poly = np.asarray(poly, float)
    n = len(poly)
    inside = np.zeros(np.shape(px), bool)
    dmin = np.full(np.shape(px), 1e9)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        hit = ((y0 > py) != (y1 > py)) & (px < (x1 - x0) * (py - y0) / (y1 - y0 + 1e-12) + x0)
        inside ^= hit
        dx, dy = x1 - x0, y1 - y0
        t = np.clip(((px - x0) * dx + (py - y0) * dy) / max(dx * dx + dy * dy, 1e-9), 0.0, 1.0)
        dmin = np.minimum(dmin, np.hypot(px - (x0 + t * dx), py - (y0 + t * dy)))
    return np.where(inside, 0.0, dmin), inside


class ValleyField:
    """The region's analytic field — a drop-in for overworld_lib.Field."""

    def __init__(self):
        xs = np.linspace(-TILE_W / 2, TILE_W / 2, L.NX)
        ys = np.linspace(-TILE_H / 2, TILE_H / 2, L.NY)
        self.xs, self.ys = xs, ys
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        self.X, self.Y = X, Y
        WX, WY = X + CX, Y + CY                          # world coords per vertex

        # ---- river distance / downstream parameter -------------------------
        self.river = np.column_stack([RIV_XY[:, 0] - CX, RIV_XY[:, 1] - CY])
        self.rt = RIV_T
        dr, ri = _chunked_nearest(X, Y, self.river[:, 0], self.river[:, 1])
        self.dr, self.ridx_river = dr, ri
        self.tr = RIV_T[ri]
        self.wl = water_level(self.tr)
        self.hw = water_halfwidth(self.tr)
        g = gorge_factor(self.tr)
        self.gorge = g

        # ---- AMBIENT FLOOR: bank height above the local water --------------
        # Every floor control point is converted to "how far above its own river
        # is it" — so the four numbers in the region file become a downstream
        # profile instead of four bumps, and the NW->SE descent is inherited from
        # the river's fall by construction.  Two of the four controls sit inside
        # the river's own channel, so the profile is then CALIBRATED (below): the
        # region's floor heights are honoured as the height of the FLOOR BESIDE
        # the channel, which is the only reading of "valley floor" that is not
        # simply a contradiction with the river's own z.
        tc, ac = [0.0], [1.4]
        for f in FLOOR:
            fx, fy = float(f["at"][0]), float(f["at"][1])
            t = _t_at(fx, fy)
            d = float(np.hypot(RIV_XY[:, 0] - fx, RIV_XY[:, 1] - fy).min())
            a = float(f["height"]) - float(water_level(t)) - 0.075 * min(d, 45.0)
            tc.append(t)
            ac.append(max(a, 0.85))
        tc.append(1.0)
        ac.append(ac[-1])
        self.floor_t = np.array(tc)

        dev = (1.85 * np.sin(WX * 0.0405) * np.cos(WY * 0.0525)
               + 1.15 * np.sin(WX * 0.083 + 1.3) * np.sin(WY * 0.071 + 0.6)
               + 0.58 * np.sin(WX * 0.152 + 2.1) * np.cos(WY * 0.131)
               + 0.30 * np.sin(WX * 0.262 + 0.4) * np.sin(WY * 0.229 + 1.7))
        # Rolling relief is DAMPED near the channel.  The region's floor sits only
        # 1-2u above its own river, so undamped +-3.9u relief put whole reaches of
        # the valley floor BELOW the water line — which then read as swamp to the
        # zone grid and erased the valley-fringe stand.  Floodplains are flat and
        # uplands roll; this is that, and it costs one factor.
        dev = dev * (0.18 + 0.82 * sstep(2.0, 18.0, dr))
        self.dev = dev

        # ---- everything that does not depend on the floor profile -----------
        pd, _ = _poly_dist(WX, WY, PLATEAU["blob"])
        # 14u of falloff, not 9: the mesa is 14u above the floor, and a 9u skirt is
        # a 57deg cliff — which the zone grid then calls crag and refuses to plant,
        # leaving a bald band straight across the emberwood the road runs through.
        pw = (1.0 - sstep(0.0, 14.0, pd))
        # UNION with Emberbrook's own anchor disc.  The region's plateau blob does
        # not contain the [50,160] anchor (it is 12.3u outside the blob's NW edge)
        # even though the anchor's own h is 26 = the plateau height and the world
        # file calls Emberbrook a "high forested plateau" town.  Without the union
        # the town becomes a separate 26u knoll with a dip behind it.  Reported as
        # a map-change request: extend the blob's NW edge past the anchor.
        ar = float(ANCHORS["emberbrook"]["impressionRadius"])
        pw = np.maximum(pw, 1.0 - sstep(ar + 4.0, ar + 20.0,
                                        np.hypot(WX - EMBERBROOK[0], WY - EMBERBROOK[1])))
        # the mesa stops where the river leaves it: iso-lines of the downstream
        # parameter are the only edge that can cross a river without a seam
        pw = pw * (1.0 - sstep(T_LIP, T_FALLS_END, self.tr))
        self.plateau_w = pw
        ph = float(PLATEAU["height"]) + 0.42 * dev

        crest = {m["id"]: m.get("crest", 30.0) for m in WORLD["massifs"]}
        amp = (1.0 + 0.16 * np.sin(WX * 0.093 + 0.7) * np.cos(WY * 0.121 + 1.4)
               + 0.10 * np.sin(WX * 0.215) * np.sin(WY * 0.183))
        R_n = crest["northwall"] * sstep(163.0, 196.0, WY) * amp
        R_s = crest["southwall"] * sstep(21.0, -2.0, WY) * amp
        R_w = crest["westwall"] * sstep(23.0, -3.0, WX) * amp
        # Hollowmere Pass (sealed, world-level): a notch in the forest wall, so the
        # future attachment point is VISIBLE without being walkable yet
        hm = [e for e in REG_META.get("exits", []) if e["id"] == "pass-hollowmere"]
        if hm:
            hy = float(hm[0]["at"][1])
            R_w = R_w * (1.0 - 0.55 * np.exp(-((WY - hy) / 11.0) ** 2))
        self.rim = np.maximum.reduce([R_n, R_s, R_w])
        esc = sstep(263.0, 280.0, WX) * (1.0 - 0.85 * (1.0 - sstep(9.0, 22.0, dr)))
        Rg = self.wl + (GORGE_CUT - 3.0) * g
        self.gorge_rim = Rg
        gw = g * (1.0 - sstep(15.0, 33.0, dr))
        Wc = self.hw + 6.0 + 10.0 * g            # lateral run of the bank profile
        bank = 3.0 + 9.0 * g
        q = np.clip(dr / Wc, 0.0, 1.0)
        bed = self.wl - (0.55 + 0.045 * river_width(self.tr) + 1.3 * g)
        self.bed = bed
        prof = bed + (self.wl + bank - bed) * sstep(0.0, 1.0, q)
        chan = sstep(0.0, 1.0, 1.0 - q)

        self.road = ROAD_XY - np.array([CX, CY])
        self.road_s = ROAD_S
        self.road_h = ROAD_Z.copy()
        drd, ridx = _chunked_nearest(X, Y, self.road[:, 0], self.road[:, 1])
        self.drd, self.ridx = drd, ridx
        wroad = ((1.0 - sstep(2.8, 8.0, drd))
                 * sstep(0.05, 1.6, dr - self.hw))      # never fills the channel
        shelves = []
        for (wx_, wy_, h_, r0, r1) in (
                (EMBERBROOK[0], EMBERBROOK[1], float(EMBERBROOK[2]), 8.0, 15.0),
                (ROAD_END_W[0], ROAD_END_W[1], float(ROAD_Z[-1]), 4.5, 10.5)):
            # gated on channel distance: a levelled apron that reached into the
            # gorge would BURY the river under the Valley Gate
            shelves.append(((1.0 - sstep(r0, r1, np.hypot(WX - wx_, WY - wy_)))
                            * sstep(0.4, 3.0, dr - self.hw), h_))

        def assemble(a_prof, with_built=True):
            bank_a = np.interp(self.tr, self.floor_t, a_prof)
            H = self.wl + bank_a + dev + 0.075 * np.minimum(dr, 45.0)
            H = H * (1.0 - pw) + ph * pw                       # plateau mesa
            rw = sstep(0.0, 6.5, self.rim - H)
            H = H * (1.0 - rw) + self.rim * rw                 # ridges / forest wall
            H = H - np.clip(H + 5.0, 0.0, 26.0) * esc          # east escarpment
            H = np.where(Rg > H, H + (Rg - H) * gw, H)         # gorge shoulders
            H = H * (1.0 - chan) + prof * chan                 # the river channel
            if not with_built:
                return H
            H = H * (1.0 - wroad) + self.road_h[ridx] * wroad  # the road grade
            for w_, h_ in shelves:
                H = H * (1.0 - w_) + h_ * w_
            return H

        # ---- CALIBRATION so the region's floor heights land -----------------
        # Probed on the NATURAL field only (no road grade, no settlement shelves):
        # calibrating against them would chase the road's own authored z and
        # diverge, and "valley floor" means the land, not the works on it.
        probes = []
        for f in FLOOR:
            fx, fy = float(f["at"][0]), float(f["at"][1])
            t = _t_at(fx, fy)
            i = int(np.argmin(np.abs(RIV_T - t)))
            tg = RIV_XY[min(i + 1, len(RIV_XY) - 1)] - RIV_XY[max(i - 1, 0)]
            nr = np.array([-tg[1], tg[0]]) / max(np.linalg.norm(tg), 1e-9)
            side = np.sign(np.dot(nr, np.array([fx, fy]) - RIV_XY[i])) or 1.0
            off = max(float(water_halfwidth(t)) + 5.5,
                      float(np.hypot(fx - RIV_XY[i, 0], fy - RIV_XY[i, 1])))
            probes.append((RIV_XY[i, 0] + nr[0] * side * off - CX,
                           RIV_XY[i, 1] + nr[1] * side * off - CY, float(f["height"])))
        self.floor_probes = probes
        a_prof = np.array(ac)
        for _ in range(6):
            self.H = assemble(a_prof, with_built=False)
            err = np.zeros(len(a_prof))
            for k, (px, py, want) in enumerate(probes):
                got = float(self.sample(np.array([px]), np.array([py]))[0])
                err[k + 1] = np.clip(want - got, -6.0, 6.0)
            err[0] = err[1] * 0.35
            err[-1] = err[-2]
            a_prof = np.clip(a_prof + err * 0.7, 1.1, 12.0)
        self.floor_a = a_prof
        self.H_natural = assemble(a_prof, with_built=False)
        self.H = assemble(a_prof)
        self.village_h = float(self.sample(np.array([L.VILLAGE[0]]), np.array([L.VILLAGE[1]]))[0])
        self.clifftown_h = float(self.sample(np.array([L.CLIFFTOWN[0]]), np.array([L.CLIFFTOWN[1]]))[0])

        # ---- analysis masks (round 1's recipe, region-scaled) --------------
        H = self.H
        gx, gy = np.gradient(H, STEP, STEP)
        self.slope = np.sqrt(gx * gx + gy * gy)
        self.nz = 1.0 / np.sqrt(1.0 + self.slope ** 2)
        alt = H - self.wl
        self.alt = alt

        rock = sstep(0.55, 1.35, self.slope)
        peak = sstep(19.0, 32.0, alt) * (0.35 + 0.65 * rock)
        sand = (1.0 - rock) * (1.0 - sstep(0.6, 4.0, dr - self.hw)) * sstep(-1.4, 0.4, alt)
        dirt = (1.0 - sstep(0.95, 2.4, drd)) * sstep(0.6, 2.6, dr - self.hw)
        patch = 0.5 + 0.5 * (np.sin(WX * 0.081 + 1.3) * np.sin(WY * 0.096 - 0.4)
                             + 0.55 * np.sin(WX * 0.23 - 0.8) * np.sin(WY * 0.20 + 2.2)
                             + 0.32 * np.sin(WX * 0.48 + 0.3) * np.sin(WY * 0.42 - 1.1))
        autumn = np.clip(patch - 0.52, 0.0, 1.0) * 2.2 * (1.0 - rock) * (1.0 - sstep(10.0, 19.0, alt))
        ghi = sstep(7.0, 17.0, alt) * (1.0 - rock)
        base = np.clip(1.0 - rock - peak - sand - dirt - autumn - ghi, 0.0, 1.0)
        w = np.stack([base, ghi, autumn, rock, peak, sand, dirt], axis=-1)
        for _ in range(2):
            k = np.zeros_like(w)
            for dx_, dy_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                k += np.roll(np.roll(w, dx_, 0), dy_, 1)
            w = k / 5.0
        w = np.maximum(w, 0.0)
        self.w = w / np.maximum(w.sum(-1, keepdims=True), 1e-6)

        self.shade = (1.0 + 0.12 * np.sin(WX * 0.42 + 0.4) * np.sin(WY * 0.38 - 1.2)
                      + 0.08 * np.sin(WX * 0.85 - 2.0) * np.sin(WY * 0.75 + 0.7))

        rng = np.random.RandomState(7)
        mask = np.zeros_like(X)
        mask[1:-1, 1:-1] = 1.0
        self.MX = X + (rng.rand(*X.shape) - 0.5) * 0.72 * STEP * mask
        self.MY = Y + (rng.rand(*X.shape) - 0.5) * 0.72 * STEP * mask

    # ------------------------------------------------------------------ sampling
    def sample(self, x, y):
        fx = np.clip((np.asarray(x, float) + TILE_W / 2) / STEP, 0, L.NX - 1.001)
        fy = np.clip((np.asarray(y, float) + TILE_H / 2) / STEP, 0, L.NY - 1.001)
        i0, j0 = fx.astype(int), fy.astype(int)
        tx, ty = fx - i0, fy - j0
        H = self.H
        return (H[i0, j0] * (1 - tx) * (1 - ty) + H[i0 + 1, j0] * tx * (1 - ty) +
                H[i0, j0 + 1] * (1 - tx) * ty + H[i0 + 1, j0 + 1] * tx * ty)

    def slope_at(self, x, y):
        fx = np.clip((np.asarray(x, float) + TILE_W / 2) / STEP, 0, L.NX - 1.001)
        fy = np.clip((np.asarray(y, float) + TILE_H / 2) / STEP, 0, L.NY - 1.001)
        return self.slope[fx.astype(int), fy.astype(int)]

    def _river_dist(self, x, y):
        d, i = _chunked_nearest(np.asarray(x, float).ravel(), np.asarray(y, float).ravel(),
                                self.river[:, 0], self.river[:, 1])
        return d, RIV_T[i]

    def river_dist(self, x, y):
        return self._river_dist(x, y)[0]

    def road_dist(self, x, y):
        d, _ = _chunked_nearest(np.asarray(x, float).ravel(), np.asarray(y, float).ravel(),
                                self.road[:, 0], self.road[:, 1])
        return d

    def water_halfwidth(self, t):
        return water_halfwidth(t)

    def road_point(self, s):
        i = int(np.clip(s, 0, 1) * (len(self.road) - 1))
        i = max(1, min(len(self.road) - 2, i))
        p = self.road[i]
        tg = self.road[i + 1] - self.road[i - 1]
        tg = tg / np.linalg.norm(tg)
        return float(p[0]), float(p[1]), float(self.road_h[i]), (float(tg[0]), float(tg[1]))

    def road_frame_at(self, wx, wy):
        """Nearest road station to a world point: (blender x, y, h, unit tangent)."""
        i = int(np.argmin((self.road[:, 0] - (wx - CX)) ** 2 + (self.road[:, 1] - (wy - CY)) ** 2))
        i = max(1, min(len(self.road) - 2, i))
        tg = self.road[i + 1] - self.road[i - 1]
        tg = tg / np.linalg.norm(tg)
        return (float(self.road[i, 0]), float(self.road[i, 1]), float(self.road_h[i]),
                (float(tg[0]), float(tg[1])))


# ------------------------------------------------------------- the mooring basin
def moorage_frame(F):
    """The Moorage, as the round-2 basin frame (ctr/tg/nrm/wl/t).

    Reuses O2's basin/jetty/boat machinery verbatim by handing it a frame at the
    region's own landmark instead of the prototype's village bank.  The basin digs
    into the DELLHOLLOW side of the channel — the town's boats moor below its locks.
    """
    mx, my = LAND_W["dellhollow-moorage"][:2]
    i = int(np.argmin(np.hypot(RIV_XY[:, 0] - mx, RIV_XY[:, 1] - my)))
    i = max(1, min(len(RIV_XY) - 2, i))
    t = float(RIV_T[i])
    tg = np.array([RIV_XY[i + 1, 0] - RIV_XY[i - 1, 0], RIV_XY[i + 1, 1] - RIV_XY[i - 1, 1]])
    tg /= np.linalg.norm(tg)
    nrm = np.array([-tg[1], tg[0]])
    ctr = np.array([RIV_XY[i, 0] - CX, RIV_XY[i, 1] - CY])
    if np.dot(nrm, np.array([DELLHOLLOW[0] - CX, DELLHOLLOW[1] - CY]) - ctr) < 0:
        nrm = -nrm
    return dict(ctr=ctr, tg=tg, nrm=nrm, wl=float(water_level(np.array([t]))[0]), t=t)


# ------------------------------------------------------------------- diagnostics
def describe():
    out = []
    out.append("region %s  tile %.0f x %.0fu  lattice %d x %d @ %.2fu"
               % (REGION_ID, TILE_W, TILE_H, L.NX, L.NY, STEP))
    out.append("river %.1fu long, %d authored pts, width %.1f -> %.1fu, z %.1f -> %.1f"
               % (RIVER_LEN, len(RIV_CTRL), RIV_WIDTH[0], RIV_WIDTH[-1], RIV_Z[0], RIV_Z[-1]))
    out.append("road  %.1fu long, %d authored pts, z %.1f -> %.1f"
               % (ROAD_S[-1], len(ROAD_CTRL_W), ROAD_Z[0], ROAD_Z[-1]))
    out.append("falls lip t=%.3f (arc %.0fu), gorge t=%.3f..%.3f, rim %.0f cut %.0f"
               % (T_LIP, T_LIP * RIVER_LEN, T_GORGE0, T_GORGE1, GORGE_RIM, GORGE_CUT))
    return "\n".join(out)


if __name__ == "__main__":
    print(describe())
    F = ValleyField()
    print("H range %.1f .. %.1f" % (F.H.min(), F.H.max()))
    print("floor profile a = %s" % np.round(F.floor_a, 2))
    for nm, p in (("emberbrook", EMBERBROOK), ("ember-falls", LAND_W["ember-falls"]),
                  ("dellhollow", DELLHOLLOW), ("moorage", LAND_W["dellhollow-moorage"]),
                  ("waystone", LAND_W["waystone"]), ("valley-gate", GATE_W)):
        bx, by = w2b(p[0], p[1])
        h = float(F.sample(np.array([bx]), np.array([by]))[0])
        d = float(F.river_dist(np.array([bx]), np.array([by]))[0])
        print("  %-14s map h=%6.1f   field h=%6.2f   (%+.2f)  %.1fu from the channel"
              % (nm, p[2], h, h - p[2], d))
    print("floor controls:")
    for f, (px, py, want) in zip(FLOOR, F.floor_probes):
        bx, by = w2b(f["at"][0], f["at"][1])
        h = float(F.sample(np.array([bx]), np.array([by]))[0])
        hb = float(F.sample(np.array([px]), np.array([py]))[0])
        print("    at %-11s want %5.1f   at the point %6.2f   floor beside the channel %6.2f"
              % (f["at"], want, h, hb))
    print("road/river clearance: %d stations pushed, max %.1fu, final min slack %.2fu"
          % (len(ROAD_PUSH), max([p[3] for p in ROAD_PUSH] or [0]), ROAD_SLACK))
    for a, b in ROAD_SPANS:
        print("    SPAN stations %d..%d  world(%.1f,%.1f)..(%.1f,%.1f)  %.1fu long"
              % (a, b, ROAD_XY[a, 0], ROAD_XY[a, 1], ROAD_XY[b, 0], ROAD_XY[b, 1],
                 ROAD_S[b] - ROAD_S[a]))
    for k, x_, y_, u in ROAD_PUSH[::6]:
        print("    station %3d world(%6.1f,%6.1f) pushed %.1fu" % (k, x_, y_, u))
    # the descent, sampled along the road: does the fall read as monotone?
    print("road profile (blender x, y -> terrain h):")
    for s in np.linspace(0, 1, 11):
        rx, ry, rh, _ = F.road_point(float(s))
        gh = float(F.sample(np.array([rx]), np.array([ry]))[0])
        print("    s=%.1f world(%6.1f,%6.1f) road_h=%5.1f terrain=%5.1f  dr=%5.1f"
              % (s, rx + CX, ry + CY, rh, gh, float(F.river_dist(np.array([rx]), np.array([ry]))[0])))


# =============================================================================
# THE ZONE GRID — F2's, with the region's AUTHORED forests and overrides
# =============================================================================
# Imported down here on purpose: overworld3_lib reads overworld_lib's tile
# constants, and everything above this line is what re-points them at the region.
import overworld3_lib as O3                                     # noqa: E402

Z_MEADOW, Z_FOREST, Z_CRAG, Z_ROAD, Z_WATER = range(5)


def region_overrides():
    """The region file's zoneOverrides, in the grid's runtime frame.

    `{"type": "road", "alongRoad": true}` needs no stamp: the derived road mask IS
    the road polyline buffered to 1.9u, so that override is satisfied by
    construction and is asserted rather than applied.

    The two SETTLEMENT stamps are not in the region file.  F2 established the rule
    (settled ground is safe ground — the encounter table must not roll a wolf in
    the village green) and the region gives every anchor an impressionRadius, so
    they are derived from it.  Requested as an explicit addition to zoneOverrides.
    """
    out = []
    for st in REGION.get("zoneOverrides", []):
        if st.get("alongRoad"):
            continue
        if "stamp" in st:
            out.append(dict(type=st["type"], polygon=poly_r(st["stamp"]),
                            why=st.get("note", "region zoneOverride")))
    for a in REGION["townAnchors"]:
        rx, rz = w2r(a["pos"][0], a["pos"][1])
        r = float(a["impressionRadius"]) * 0.62
        out.append(dict(type="road", ellipse=(float(rx), float(rz), r, r, 0.0),
                        why="%s: settled ground is safe ground" % a["town"]))
    return out


class ValleyZoneGrid(O3.ZoneGrid):
    """F2's zone grid, with two region-level differences.

    FOREST comes from the region's authored stamps and densities instead of the
    prototype's value-noise percentile — but the *breakup* is still coherent noise,
    so a 0.55-density stand thins at its own edges rather than ending at a polygon
    boundary.  And the OVERRIDES come from the region file.
    """

    def __init__(self, F, fr=None, cell=ZONE_CELL):
        O3.ZoneGrid.__init__(self, F, fr, cell=cell, overrides=[])
        Z = self.idx
        SL = O3._grid_sample(F.slope, self.BX, self.BY)
        ALT = F.sample(self.BX, self.BY) - O3._grid_sample(F.wl, self.BX, self.BY)
        # dry-bank distance, not height above water: at region scale the valley
        # floor is only 1-2u above its own river, and the prototype's ALT > 1.0
        # guard erased 87% of the valley-fringe stand
        DCH = (O3._grid_sample(F.dr, self.BX, self.BY)
               - F.water_halfwidth(O3._grid_sample(F.tr, self.BX, self.BY)))
        crag = Z == Z_CRAG
        wet = (Z == Z_WATER) | (Z == Z_ROAD)

        dens = np.zeros(Z.shape)
        self.stand = {}
        for k, st in enumerate(FORESTS):
            m = self._stamp_mask(dict(polygon=poly_r(st["stamp"])))
            d = float(st.get("density", 1.0))
            plantable = (m & (~crag) & (~wet) & (SL < 1.20)
                         & (DCH > 1.2) & (ALT > 0.15))
            nz = O3.fbm(self.BX, self.BY, 0.042, seed=17 + 37 * k, oct_=4)
            # density thins the PLANTABLE ground, not the raw stamp: the stamp
            # already loses its channel and its crag, and thinning twice is how a
            # 0.55-density stand ends up at 0.25
            if plantable.any() and d < 0.999:
                thr = float(np.percentile(nz[plantable], 100.0 * (1.0 - d)))
            else:
                thr = -1.0
            keep = plantable & (nz > thr)
            dens = np.maximum(dens, keep * d)
            self.stand[st["id"]] = keep
        forest = dens > 0.0
        Z[Z == Z_FOREST] = Z_MEADOW            # drop the prototype's noise forest
        Z[forest & (Z == Z_MEADOW)] = Z_FOREST
        self.forest_dens = dens

        self.overrides = region_overrides()
        self.n_override = 0
        for st in self.overrides:
            m = self._stamp_mask(st)
            if st["type"] != "water":
                # an authored stamp never dries the river out: the gorge-rim crag
                # stamp covers the channel it is the rim OF, and a settlement's
                # safe ground is ground
                m = m & (Z != Z_WATER)
            self.n_override += int(m.sum())
            Z[m] = O3.ZONES.index(st["type"])
        self.idx = Z

        # the continuous weights the terrain treatment and the planting read
        self.crag_w = O3._box((Z == Z_CRAG).astype(float), 2)
        self.forest_w = O3._box((Z == Z_FOREST).astype(float), 1)
        veto = ((Z == Z_ROAD) | (Z == Z_WATER)).astype(float)
        self.crag_w *= (1.0 - O3._box(veto, 2))
        self.crag_w = np.clip(self.crag_w, 0.0, 1.0)
        self.thresh["forest"] = "region stamps"

    def to_dict(self):
        d = O3.ZoneGrid.to_dict(self)
        d["region"] = REGION_ID
        d["_doc"] = list(d["_doc"]) + [
            "REGION BUILD: this grid is derived from public/world/world.json + "
            "public/world/regions/valley.region.json by tools/valley_build.py. "
            "forest = the region's forest stamps x their density (coherent-noise "
            "breakup); the road override is satisfied by derivation; the crag "
            "override is the region's gorge-rim stamp; the two settlement stamps "
            "come from townAnchors.impressionRadius (settled = safe).",
        ]
        return d
