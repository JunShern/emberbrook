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

# ROOT IS DERIVED FROM THIS FILE, NEVER TYPED.  It was hardcoded to the main
# checkout, so a build launched from a git WORKTREE read the worktree's builder and
# wrote its blend, its zones.json, its bundle and its QA record into the SHARED
# tree — an experiment in an isolated copy silently editing the shipped one.  A
# lane paid for that on 2026-08-03 and worked around it with an env override; the
# override is the symptom, this is the fix.  <repo>/tools/valley_map.py -> <repo>.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
#
# THE TILE IS READ FROM THE MAP, NEVER HARDCODED.  It used to be `280.0, 200.0`
# here while tools/scenegraph_derive.mjs derived its own from the massifs' extent
# (280 x 196) — so every ow-valley arrival the scene graph produced was 2u north
# of the ribbon it had been measured on, which is the whole of the three
# "arrival stands on walk network" reds.  world.json regions[].tile is now the
# single statement and both tools read it; a region without one raises rather
# than guessing, because guessing is what cost us the arrivals.
_TILE = REG_META.get("tile")
if not _TILE:
    raise SystemExit(
        "valley_map: world.json regions['%s'] has no 'tile' — the terrain tile and its "
        "origin must be STATED, not inferred (two tools inferred differently and the "
        "ow-valley arrivals landed 2u off the road)." % REGION_ID)
TILE_W, TILE_H = float(_TILE["size"][0]), float(_TILE["size"][1])
CX, CY = float(_TILE["origin"][0]), float(_TILE["origin"][1])   # world coords of the blender origin
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


def _boxblur(A, r=6, n=3):
    """Separable moving average, edge-clamped, via cumulative sums.

    Wide, cheap, and the only thing that removes the MEDIAL-AXIS CREASE: every
    quantity read off the river by NEAREST POINT (water level, bank profile, gorge
    factor) jumps where the nearest reach changes, and the jump is the river's own
    fall between those reaches.  Left sharp, it draws a 200u straight cliff down the
    middle of the meadow on both sides of every meander — which the zone grid then
    faithfully calls crag.
    """
    for _ in range(n):
        for ax in (0, 1):
            P = np.moveaxis(A, ax, 0)
            pad = np.concatenate([np.repeat(P[:1], r, 0), P, np.repeat(P[-1:], r, 0)], 0)
            c = np.cumsum(pad, axis=0)
            c = np.concatenate([np.zeros_like(c[:1]), c], 0)
            P = (c[2 * r + 1:] - c[:-(2 * r + 1)]) / (2 * r + 1)
            A = np.moveaxis(P, 0, ax)
    return A


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

# ---- the CANYON (schema v2) ---------------------------------------------------
# elevation.canyon replaces v1's gorge-only cut: an ASYMMETRIC trench along the
# whole spine.  benchSide names the traversable bank; the FAR wall (the other one)
# rises farWallRise above local water (unclimbable — the height gating canon),
# topped by the forested farPlateau (visible ch3 territory).
CANYON = REGION["elevation"].get("canyon")
if CANYON is None:
    raise SystemExit("valley_map: region schema v2 requires elevation.canyon")
CANYON_BENCH = [float(v) for v in CANYON["benchClearance"]]     # above local water
CANYON_RISE = [float(v) for v in CANYON["farWallRise"]]         # above local water
FARPLATEAU = CANYON.get("farPlateau", {})
WATER_ACCESS = [(float(w["at"][0]), float(w["at"][1])) for w in CANYON.get("waterAccess", [])]


# ---- WHICH BANK IS THE BENCH (resolved, never assumed) ------------------------
# This used to be hardcoded to the RIGHT bank, with "the Dellhollow master's
# chirality" as the reason.  That was only ever true while the river ran SOUTH-EAST:
# the 2026-08-01 world restamp turned it NORTH-EAST and the bench with it, and a
# hardcoded chirality carves the canyon the wrong way round while looking perfectly
# plausible.  So the side is now RESOLVED TWICE and the two answers must agree:
#   (a) from elevation.canyon.benchSide, a compass word, against the river's own
#       mean downstream heading — the region file's declared canon;
#   (b) from where the ROAD actually runs relative to the water — the built truth.
# Disagreement is a map bug, and it raises rather than picking one.
_COMPASS = {"N": (0.0, 1.0), "S": (0.0, -1.0), "E": (1.0, 0.0), "W": (-1.0, 0.0)}


def _compass_vec(word):
    """'W' -> (-1,0), 'NE' -> (.71,.71), 'NNE' -> (.45,.89).  Letters are summed,
    so any standard 1/2/3-point compass name resolves without a lookup table."""
    vx = vy = 0.0
    for ch in word.upper():
        if ch not in _COMPASS:
            raise SystemExit("valley_map: benchSide %r is not a compass word" % word)
        vx += _COMPASS[ch][0]
        vy += _COMPASS[ch][1]
    n = math.hypot(vx, vy)
    if n < 1e-9:
        raise SystemExit("valley_map: benchSide %r cancels out" % word)
    return vx / n, vy / n


def _mean_left_normal(xy):
    """Arc-length-weighted mean LEFT normal of a polyline (looking downstream)."""
    d = np.diff(xy, axis=0)
    seg = np.linalg.norm(d, axis=1)
    keep = seg > 1e-9
    d, seg = d[keep], seg[keep]
    nl = np.column_stack([-d[:, 1], d[:, 0]]) / seg[:, None]     # unit left normals
    v = (nl * seg[:, None]).sum(axis=0) / seg.sum()
    return float(v[0]), float(v[1])


def _road_offsets():
    """Signed offset (+ = LEFT bank) and distance to the water, per road control point."""
    road = np.array([[p[0], p[1]] for p in REGION["road"]["points"]], float)
    riv = SPINE[:, :2]
    off, dist = [], []
    for p in road:
        d = np.hypot(riv[:, 0] - p[0], riv[:, 1] - p[1])
        i = int(np.argmin(d))
        j = min(max(i, 1), len(riv) - 1)
        t = riv[j] - riv[j - 1]
        t /= max(np.hypot(*t), 1e-9)
        off.append(float((p[0] - riv[i][0]) * -t[1] + (p[1] - riv[i][1]) * t[0]))
        dist.append(float(d[i]))
    return road, np.array(off), np.array(dist)


CULVERT = REGION["road"].get("culvert")      # the ONE declared bank change, or None
CULVERT_XING = None                          # where the road actually crosses, measured


def _declared_side(side, key):
    """A compass word (or left/right) resolved against the river's own heading."""
    side = str(side).strip()
    if side.upper() in ("L", "LEFT"):
        return True
    if side.upper() in ("R", "RIGHT"):
        return False
    cx_, cy_ = _compass_vec(side)
    nlx, nly = _mean_left_normal(SPINE[:, :2])
    dot = nlx * cx_ + nly * cy_
    if abs(dot) < 0.25:
        raise SystemExit(
            "valley_map: %s %r is nearly parallel to the river's mean downstream heading "
            "(|dot| %.2f) — it does not name a bank. Give a compass word across the flow, "
            "or 'left'/'right'." % (key, side, dot))
    return dot > 0.0


def _resolve_bench_left():
    global CULVERT_XING
    side = str(CANYON.get("benchSide", "")).strip()
    declared = _declared_side(side, "benchSide")
    # (b) the built truth: which side of the water does the road actually run on?
    # Only stations NEAR the channel get a vote — a road reach that is 50u from the
    # water (or upstream of the source, as the v2 map had) is not on a bank at all,
    # and letting it vote by magnitude is how one far station outshouts ten near ones.
    # One vote each, majority wins.
    road, off, dist = _road_offsets()
    near = dist < 25.0
    if int(near.sum()) < 4:
        print("valley_map: WARNING — only %d road stations run within 25u of the water; "
              "benchSide %r taken on trust." % (int(near.sum()), side))
        return declared
    # ---- THE ROAD IS ALLOWED TO CHANGE BANK EXACTLY WHERE THE MAP SAYS IT DOES ----
    # It used to be allowed to change bank ANYWHERE and merely printed a NOTE about it,
    # which is how a hairpin that swapped 3 of 14 stations lived in a shipped map for as
    # long as the map existed.  Now: no `road.culvert` means no bank change at all, and a
    # culvert means the change happens THERE, once, with each reach internally consistent.
    # The bench is resolved on the reach BELOW the culvert, because that is the reach
    # `benchSide` is a statement about.
    culv = REGION["road"].get("culvert")
    if culv is not None:
        i0, i1 = (int(v) for v in culv["roadStations"])
        above = np.arange(len(off)) <= i0
        below = np.arange(len(off)) >= i1
        for nm, m in (("above", above & near), ("below", below & near)):
            s_ = np.sign(off[m])
            if len(s_) and not (s_ == s_[0]).all():
                raise SystemExit(
                    "valley_map: the road changes bank INSIDE the %s-culvert reach "
                    "(offsets %s). road.culvert names ONE bank change; this map has more."
                    % (nm, np.round(off[m], 2).tolist()))
        a_side = float(np.sign(off[above & near].mean()))
        b_side = float(np.sign(off[below & near].mean()))
        if a_side == b_side:
            raise SystemExit(
                "valley_map: road.culvert '%s' declares a bank change the road does not "
                "make — both reaches run on the %s bank."
                % (culv.get("id"), "LEFT" if a_side > 0 else "RIGHT"))
        # and it has to be a change AT THE CULVERT: the segment between the two named
        # stations must actually cross the channel, close to the declared point.
        p0, p1 = road[i0], road[i1]
        r = p1 - p0
        q0, q1 = RIV_XY[:-1], RIV_XY[1:]
        s_ = q1 - q0
        den = r[0] * s_[:, 1] - r[1] * s_[:, 0]
        okd = np.abs(den) > 1e-9
        qp = q0 - p0
        tt = np.where(okd, (qp[:, 0] * s_[:, 1] - qp[:, 1] * s_[:, 0]) / np.where(okd, den, 1), -1)
        uu = np.where(okd, (qp[:, 0] * r[1] - qp[:, 1] * r[0]) / np.where(okd, den, 1), -1)
        m_ = okd & (tt >= 0) & (tt <= 1) & (uu >= 0) & (uu <= 1)
        if not m_.any():
            raise SystemExit(
                "valley_map: road.culvert '%s' names stations %d..%d, and that segment does "
                "not cross the channel at all." % (culv.get("id"), i0, i1))
        xg = p0 + r * float(tt[m_][0])
        dcl = float(np.hypot(*(xg - np.array(culv["at"], float))))
        if dcl > 4.0:
            raise SystemExit(
                "valley_map: road.culvert '%s' says the road crosses at %s; it crosses at "
                "[%.2f, %.2f], %.2fu away." % (culv.get("id"), culv["at"], xg[0], xg[1], dcl))
        CULVERT_XING = (float(xg[0]), float(xg[1]), dcl)
        built = b_side > 0
        nl, nr = int((off[near] > 0).sum()), int((off[near] <= 0).sum())
        # ---- AND THE CANYON CHANGES HANDS WHERE THE ROAD DOES ------------------
        # benchSide is a statement about the reach BELOW the culvert.  The reach
        # above it is Emberbrook's and has its own word, because the canyon's
        # asymmetry is not a global constant: run one side down the whole spine and
        # the far wall's 18-26u rise lands on the WHISPERWOOD side of the gate,
        # which measured an 11u ridge through the highland 20u west of the village
        # (y=48, x=70: 25.7 -> 36.7).  A geography that changes hands has to say so
        # twice, and each word is checked against its own reach of road.
        aw = CANYON.get("benchSideAboveCulvert")
        if aw is None:
            raise SystemExit(
                "valley_map: road.culvert declares a bank change but "
                "elevation.canyon.benchSideAboveCulvert is missing — the canyon's "
                "asymmetry above the crossing is then unstated, and the build would "
                "carry the downstream side up past Emberbrook.")
        ad = _declared_side(aw, "benchSideAboveCulvert")
        if ad != (a_side > 0):
            raise SystemExit(
                "valley_map: benchSideAboveCulvert %r says the %s bank; the road's own "
                "above-culvert reach runs on the %s bank."
                % (aw, "LEFT" if ad else "RIGHT", "LEFT" if a_side > 0 else "RIGHT"))
        globals()["BENCH_LEFT_ABOVE"] = ad
        print("valley_map: road.culvert '%s' — bank change declared at %s; the %d near-water "
              "stations above it are %s (benchSideAboveCulvert %r), the %d below are %s "
              "(benchSide %r)"
              % (culv.get("id"), culv.get("at"), int((above & near).sum()),
                 "LEFT" if a_side > 0 else "RIGHT", aw, int((below & near).sum()),
                 "LEFT" if b_side > 0 else "RIGHT", side))
    else:
        nl, nr = int((off[near] > 0).sum()), int((off[near] <= 0).sum())
        built = nl > nr
        if nl and nr:
            raise SystemExit(
                "valley_map: the road changes bank (%d left / %d right within 25u of the "
                "water) and NOTHING IN THE MAP SAYS IT MAY. Declare road.culvert (or a "
                "crossing) or fix the road." % (nl, nr))
    if built != declared:
        raise SystemExit(
            "valley_map: THE MAP CONTRADICTS ITSELF ON WHICH BANK THE BENCH IS.\n"
            "  elevation.canyon.benchSide %r says the %s bank looking downstream;\n"
            "  the road's bench reach runs on the %s bank (%d of %d stations within 25u "
            "of the water are left of it, %d right).\n"
            "  Fix the map, not this file: the road, the bench and the towns are one bank."
            % (side, "LEFT" if declared else "RIGHT", "LEFT" if built else "RIGHT",
               nl, nl + nr, nr))
    return declared


BENCH_LEFT_ABOVE = None                     # set by _resolve_bench_left when a culvert exists
BENCH_LEFT = _resolve_bench_left()                              # bench on the left bank?
if BENCH_LEFT_ABOVE is None:
    BENCH_LEFT_ABOVE = BENCH_LEFT
print("valley_map: benchSide %r -> bench on the %s bank below the crossing, %s above "
      "(road agrees on both reaches)"
      % (CANYON.get("benchSide"), "LEFT" if BENCH_LEFT else "RIGHT",
         "LEFT" if BENCH_LEFT_ABOVE else "RIGHT"))
# the downstream parameter at which the corridor changes hands: the culvert itself
T_HANDOVER = None
if CULVERT is not None:
    _cj = int(np.argmin((RIV_XY[:, 0] - CULVERT["at"][0]) ** 2
                        + (RIV_XY[:, 1] - CULVERT["at"][1]) ** 2))
    T_HANDOVER = float(RIV_T[_cj])

# Dellhollow's deep notch: derived from the canyon + the town anchor (v1 read an
# explicit elevation.gorge block; v2 folds it into the canyon and the anchor).
_dell = [a for a in REGION["townAnchors"] if a["town"] == "dellhollow"][0]
_di = int(np.argmin(np.hypot(SPINE[:, 0] - _dell["pos"][0], SPINE[:, 1] - _dell["pos"][1])))
GORGE_I0, GORGE_I1 = max(_di - 1, 0), min(_di + 1, len(SPINE) - 1)
# THE RIM IS WHERE THE GATE STANDS, NOT WHERE THE CENTROID LANDS.  This read the
# town ANCHOR's z with the comment "the rim the gate stands on" — two different
# dots, and they agreed only by accident: the anchor used to sit 4.9u from the
# road's end, inside the Valley Gate apron shelf that the build pins to the road's
# own z, so its 12.0 was never tested against the ground.  The chirality flip moved
# the anchor 14.5u out of that apron and the same 12.0 measured 6.10 in the field —
# which would have quietly halved the gorge's depth if the cut had gone on reading
# it.  The Valley Gate portal IS the rim, by definition and by its own map note.
GORGE_RIM = float(
    [p for p in REGION["road"]["portals"] if p["id"] == "dellhollow-valley-gate"][0]["at"][2])
GORGE_CUT = GORGE_RIM - float(SPINE[_di][2]) + 3.0              # rim down past the water


def _t_at(wx, wy):
    """Downstream parameter of the river point nearest a world position."""
    i = int(np.argmin((RIV_XY[:, 0] - wx) ** 2 + (RIV_XY[:, 1] - wy) ** 2))
    return float(RIV_T[i])


T_GORGE0 = _t_at(*SPINE[GORGE_I0][:2])
T_GORGE1 = _t_at(*SPINE[GORGE_I1][:2])
# ---- EMBER FALLS: the lip is the SILL, and the sill is a crossing, not a constant
# This was `np.interp(11.0, RIV_S, RIV_T)` — eleven units of arc length FROM THE
# RIVER'S START.  That was true exactly while the river's source WAS the falls.  The
# 2026-08-01 restamp moved the source to the Whisperwood springs 50u upstream of the
# gate, and the constant went on pointing 11u below the SPRINGS: the Whisperwood
# plateau was being cut off in the middle of its own headwaters while the gorge head
# kept plateau weight.  It printed itself every run ("falls lip t=0.044, arc 11u")
# and nobody read it, which is the same lesson as the scene-graph warnings.
#
# Derived instead, from geography that moves when the map moves: the LIP is where the
# channel clears the gatewall's outer face — the sill at the wall's foot, which is the
# same crossing that seated ember-falls — and the plateau is fully gone by the foot of
# the plunge, the first authored river point below the falls.
def _wall_crossing(blob, edge, xy):
    """t where a polyline crosses the (infinite) line through blob[edge] -> blob[edge+1]."""
    a = np.array(blob[edge], float)
    b = np.array(blob[(edge + 1) % len(blob)], float)
    d = b - a
    s = (xy[:, 0] - a[0]) * d[1] - (xy[:, 1] - a[1]) * d[0]     # signed side, per sample
    sign = np.sign(s)
    hits = np.nonzero(np.diff(sign) != 0)[0]
    return None if not len(hits) else float(RIV_T[hits[-1]])


_LM0 = {l["id"]: l["pos"] for l in WORLD["landmarks"]}
_gw = [m for m in WORLD["massifs"] if m["id"] == "gatewall"]
_fp = _LM0.get("ember-falls")
_falls_t = None if _fp is None else float(
    RIV_T[int(np.argmin(np.hypot(RIV_XY[:, 0] - _fp[0], RIV_XY[:, 1] - _fp[1])))])
T_LIP = _wall_crossing(_gw[0]["blob"], 2, RIV_XY) if _gw else None
if T_LIP is None or _falls_t is None or T_LIP >= _falls_t:
    raise SystemExit(
        "valley_map: cannot derive the falls lip — the river must cross the gatewall's "
        "outer face UPSTREAM of the ember-falls landmark (lip t=%s, falls t=%s). The "
        "sill is what makes a hanging valley hang; it is not a constant."
        % (T_LIP, _falls_t))
# the plateau is fully gone by the FOOT of the plunge: the authored river point below
# the falls, so the fade is the plunge's own length rather than a chosen number.
_ctrl_s = _arclen(RIV_CTRL[:, :2])
_fi = int(np.argmin(np.hypot(RIV_CTRL[:, 0] - _fp[0], RIV_CTRL[:, 1] - _fp[1])))
T_FALLS_END = float(np.interp(_ctrl_s[min(_fi + 1, len(RIV_CTRL) - 1)], RIV_S, RIV_T))
if T_FALLS_END <= T_LIP:
    raise SystemExit("valley_map: falls foot t=%.4f is not below the lip t=%.4f"
                     % (T_FALLS_END, T_LIP))


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


def bank_offset(wx, wy):
    """(signed offset from the channel centreline, channel half-width) at a WORLD point.

    Positive is the LEFT bank looking downstream.  This exists because "which bank"
    kept being answered from a single local frame taken somewhere else: Dellhollow's
    impression took its lateral offsets from the ANCHOR's frame and walked across a
    river that turns 36 degrees inside the cluster's own 24u of stations.  Measured
    by vertex, a third of the town was still standing on the far wall after the side
    itself had been fixed.  Ask per point, not per town."""
    j = int(np.argmin((RIV_XY[:, 0] - wx) ** 2 + (RIV_XY[:, 1] - wy) ** 2))
    tg = RIV_XY[min(j + 1, len(RIV_XY) - 1)] - RIV_XY[max(j - 1, 0)]
    tg = tg / max(float(np.hypot(*tg)), 1e-9)
    off = float((wx - RIV_XY[j, 0]) * -tg[1] + (wy - RIV_XY[j, 1]) * tg[0])
    return off, float(water_halfwidth(np.array([RIV_T[j]]))[0])


def river_frame_at_arc(s):
    """(point, tangent, left-normal, water level, half-width) at an ARC LENGTH.

    The companion to bank_offset: anything laid out ALONG the river must step along
    the river's own curve, not along one frame's tangent.  Dellhollow's cluster spans
    24u of a reach that turns 36 degrees, so a straight tangent from the anchor threw
    a third of the town across the water and a per-point bank guard then refused it —
    correct, and it cost the town half its mass.  Step on the curve and nothing has
    to be refused."""
    s = float(np.clip(s, 0.0, RIV_S[-1]))
    j = int(np.clip(np.searchsorted(RIV_S, s), 1, len(RIV_S) - 2))
    tg = RIV_XY[j + 1] - RIV_XY[j - 1]
    tg = tg / max(float(np.hypot(*tg)), 1e-9)
    t = float(RIV_T[j])
    return (RIV_XY[j].copy(), tg, np.array([-tg[1], tg[0]]),
            float(water_level(np.array([t]))[0]),
            float(water_halfwidth(np.array([t]))[0]), t)


def river_arc_at(wx, wy):
    """Arc length of the river point nearest a world position."""
    return float(RIV_S[int(np.argmin((RIV_XY[:, 0] - wx) ** 2 + (RIV_XY[:, 1] - wy) ** 2))])


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
# THE MAP CONFLICT THIS BLOCK WAS WRITTEN FOR IS GONE.  v2 had the road change bank
# across a hairpin's neck while region.crossings.list was empty by ruling, and the
# build reported that as a span and causewayed it.  The 2026-08-01 world restamp
# ends it: the road is authored as a constant offset on ONE bank — the village's,
# the Old Gate's, Dellhollow's — and the only span in the world is Dellhollow's dam
# crest.  So a detected span is now a MAP BUG, and so is a large push count.
#
# What the build still does, deterministically, from the map alone:
#   1. every road station standing IN the water is pushed radially to the nearest
#      dry bank (hw + 1.6), capped at 6u — a nudge, not a re-route, and what stops
#      the ribbon from being submerged along the gorge-rim climb.  On a right-handed
#      map this should be a handful of stations at most: a DOZEN of them is the
#      signature of the canyon being carved on the wrong bank (see _resolve_bench_left).
#   2. whatever channel the road still spans after that is reported as a SPAN.
CLEAR = 1.6                      # dry bank the road keeps beside the water
CLEAR_CAP = 6.0                  # nudge, never re-route
CAUSEWAY = False                 # the road never crosses; any detected span is a MAP BUG.
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


def _culvert_mask(xy):
    """Road stations standing on the CULVERTED reach — where there is no open water.

    The clearance pass exists to keep the ribbon out of the river.  At the gate court
    the river is UNDER STONE for road.culvert.lengthU, so those stations are not in the
    water, they are on the paving; pushing them out would undo the crossing the user
    ratified and would then report it as a span.  The mask is derived from the map's own
    culvert block in the RIVER's frame (along the flow, and across it), never from a
    radius around a typed point."""
    if CULVERT is None:
        return np.zeros(len(xy), bool)
    c = np.array(CULVERT["at"], float)
    j = int(np.argmin((RIV_XY[:, 0] - c[0]) ** 2 + (RIV_XY[:, 1] - c[1]) ** 2))
    tg = RIV_XY[min(j + 1, len(RIV_XY) - 1)] - RIV_XY[max(j - 1, 0)]
    tg = tg / max(float(np.hypot(*tg)), 1e-9)
    nl = np.array([-tg[1], tg[0]])
    d = xy - c
    along = d @ tg
    across = d @ nl
    half = float(CULVERT["lengthU"]) / 2.0 + 0.75
    # across: only as far as the deck has to reach, i.e. the notch either side of the
    # channel.  Beyond that the road is on real ground and the clearance rule applies.
    reach = float(water_halfwidth(np.array([RIV_T[j]]))[0]) * 4.0
    return (np.abs(along) <= half) & (np.abs(across) <= reach)


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
        culv = _culvert_mask(xy)
        d = np.where(culv, 1e9, d)          # under the court there is no open water
        need = hw + CLEAR
        hits = [h for h in _seg_hits(xy)
                if not culv[int(np.clip(round(h), 0, len(culv) - 1))]]
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
    culv = _culvert_mask(xy)
    for k in np.nonzero(tot > 0.05)[0]:
        ROAD_PUSH.append((int(k), float(xy[k, 0]), float(xy[k, 1]), float(tot[k])))
    slack = (d - hw)[~culv]
    return xy, tot, spans, float(slack.min()), culv


ROAD_XY, ROAD_PUSH_U, ROAD_SPANS, ROAD_SLACK, ROAD_CULV = road_clearance(ROAD_RAW)
if CULVERT is not None:
    print("valley_map: culvert '%s' covers %d road stations (%.1fu of ribbon); the road "
          "crosses the channel at [%.2f, %.2f], %.2fu from the declared point"
          % (CULVERT.get("id"), int(ROAD_CULV.sum()), float(ROAD_CULV.sum()),
             CULVERT_XING[0], CULVERT_XING[1], CULVERT_XING[2]))
ROAD_S = _arclen(ROAD_XY)
# the BUILT endpoints: the authored portals, after the clearance nudge.  The Valley
# Gate portal marker is placed here, not at its authored [215,65] (which the
# clearance shows standing in the channel) — reported as a map-change request.
ROAD_START_W = (float(ROAD_XY[0, 0]), float(ROAD_XY[0, 1]))
ROAD_END_W = (float(ROAD_XY[-1, 0]), float(ROAD_XY[-1, 1]))
# re-point the crag guard at the gate apron as BUILT (the authored [215,65] stands
# in the channel, and guarding there would flatten water instead of a terrace)
L.CLIFFTOWN = (ROAD_END_W[0] - CX, ROAD_END_W[1] - CY)
_road_tc = _arclen(ROAD_CTRL_W)
ROAD_Z = np.interp(ROAD_S / ROAD_S[-1], _road_tc / _road_tc[-1], ROAD_CTRL_W[:, 2])
# a light smoothing pass: the authored z is a 15-point polyline and the graded
# terrain reads its second derivative as a kink at every control point
_k = np.ones(7) / 7.0
for _ in range(3):
    ROAD_Z = np.convolve(np.pad(ROAD_Z, 3, mode="edge"), _k, mode="valid")

# ---- TRIBUTARIES: the river's growth, made legible --------------------------
# Found, not typed (region.tributaries._doc records the instrument).  Each is a
# polyline from its head to its mouth with the natural field's own z; the carve
# below turns it into a groove the water can sit in, and valley_build lays the
# waterline on top.  z is forced monotonically descending and the mouth is pulled
# down to the MAIN channel's water level, so a tributary can never run uphill or
# hang above the river it joins.
TRIBS = []
for _t in REGION.get("tributaries", {}).get("list", []):
    _p = np.array(_t["points"], float)
    _xy, _s = _resample(_p, 0.5)
    _z = np.interp(_s, _arclen(_p), _p[:, 2])
    _z = np.minimum.accumulate(_z)
    _mo = _t["points"][-1]
    _j = int(np.argmin((RIV_XY[:, 0] - _mo[0]) ** 2 + (RIV_XY[:, 1] - _mo[1]) ** 2))
    _wl = float(water_level(np.array([RIV_T[_j]]))[0])
    # the last 20% of the run drops to the main channel's water
    _f = np.clip((_s - _s[-1] * 0.80) / max(_s[-1] * 0.20, 1e-6), 0.0, 1.0)
    _z = _z * (1.0 - _f) + np.minimum(_z, _wl) * _f
    TRIBS.append(dict(id=_t["id"], xy=_xy, s=_s, z=_z, w=float(_t.get("width", 1.6)),
                      mouth_wl=_wl, drop=float(_z[0] - _z[-1])))
if TRIBS:
    print("valley_map: %d tributaries — %s"
          % (len(TRIBS), "; ".join("%s %.1fu falling %.1fu to water %.2f"
                                   % (t["id"], t["s"][-1], t["drop"], t["mouth_wl"])
                                   for t in TRIBS)))

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
        # the SMOOTHED river reference the ambient land is built on (see _boxblur).
        # The channel carve keeps the sharp values: within its own half-width the
        # nearest reach is never ambiguous, so there is no crease to remove there.
        self.wl_s = _boxblur(self.wl, 6, 3)
        self.g_s = _boxblur(g, 6, 3)

        # ---- WHICH BANK (canyon asymmetry) ----------------------------------
        # signed offset from the channel along the LEFT normal of the nearest
        # reach: sideL=1 on the LEFT bank looking downstream, 0 on the right.
        # sideB is then the BENCH-side field and sideF the FAR-WALL side, keyed
        # off BENCH_LEFT — resolved from elevation.canyon.benchSide and checked
        # against the road, never assumed (see _resolve_bench_left).  Soft 10u
        # transition, and the whole effect is faded out beyond ~46u of the
        # channel so meander medial axes (where the nearest reach jumps) never
        # see it — the v1 crease lesson applied to the side field.
        TGN = np.gradient(RIV_XY, axis=0)
        TGN /= np.maximum(np.linalg.norm(TGN, axis=1, keepdims=True), 1e-9)
        NL = np.column_stack([-TGN[:, 1], TGN[:, 0]])            # left normals
        s_signed = ((X + CX) - RIV_XY[ri, 0]) * NL[ri, 0] + ((Y + CY) - RIV_XY[ri, 1]) * NL[ri, 1]
        self.sideL = _boxblur(sstep(-5.0, 5.0, s_signed), 3, 2)
        _below = self.sideL if BENCH_LEFT else 1.0 - self.sideL
        _above = self.sideL if BENCH_LEFT_ABOVE else 1.0 - self.sideL
        if BENCH_LEFT_ABOVE == BENCH_LEFT or T_HANDOVER is None:
            self.sideB = _below
        else:
            # THE HANDOVER. The corridor changes bank at the gate and the canyon with
            # it, so the bench field is the upstream one above T_HANDOVER and the
            # downstream one below it.  The blend is deliberately SHORT and sits on
            # the reach the gate wall stands in — the one place in the region where a
            # cross-channel seam is not only invisible but built.
            hw_ = sstep(T_HANDOVER - 0.030, T_HANDOVER + 0.008, self.tr)
            self.sideB = _above * (1.0 - hw_) + _below * hw_
            self.handover_w = hw_
        self.sideF = 1.0 - self.sideB                                 # the far wall
        # canyon profiles ride the downstream parameter
        self.bench_t = np.interp(self.tr, [0.0, 1.0], CANYON_BENCH)
        self.rise_t = np.interp(self.tr, [0.0, 1.0], CANYON_RISE)
        # waterAccess: the bench is allowed down to the water ONLY here (Moorage)
        wa = np.zeros_like(X)
        for (ax, ay) in WATER_ACCESS:
            wa = np.maximum(wa, 1.0 - sstep(6.0, 13.0, np.hypot(WX - ax, WY - ay)))
        self.bench_t = self.bench_t * (1.0 - 0.88 * wa)
        self.wa = wa                                   # shelf wall also yields here

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
        # A ridge whose foot is a straight line and whose crest is a constant is a
        # WALL.  Both are folded: the foot meanders (+-11u) and the crest breathes
        # (+-26%), at wavelengths long enough to read as landform from the vista and
        # short enough to break the silhouette from inside the valley.
        amp = (1.0 + 0.20 * np.sin(WX * 0.058 + 0.7) * np.cos(WY * 0.041 + 1.4)
               + 0.13 * np.sin(WX * 0.121 + 2.2) + 0.07 * np.sin(WX * 0.263 - 0.6))
        ampw = (1.0 + 0.20 * np.sin(WY * 0.052 - 1.1) + 0.12 * np.sin(WY * 0.115 + 2.7))
        fold_n = 11.0 * np.sin(WX * 0.037 + 0.4) + 5.0 * np.sin(WX * 0.089 - 1.7)
        fold_s = 9.0 * np.sin(WX * 0.043 - 2.1) + 4.5 * np.sin(WX * 0.101 + 0.9)
        fold_w = 10.0 * np.sin(WY * 0.040 + 1.5) + 4.0 * np.sin(WY * 0.094 - 0.8)
        # THE RIM'S FOOT IS THE MASSIF'S OWN EDGE, not a number typed beside it.
        # northwall's foot was hardcoded at y=160 while its blob starts at y=168:
        # eight units of valley floor eaten by a ridge the map does not put there,
        # and it lands exactly on the Moorage and the head of the Long Reach (the
        # Moorage measured 7.2u ABOVE its own water on a bank that should be a
        # landing).  Each foot is now read from the massif that names it; the crest
        # keeps its 1u lip past the far edge so the ridge tops out inside the tile.
        _blob = {m["id"]: np.array(m["blob"], float) for m in WORLD["massifs"]}
        n_foot, n_full = float(_blob["northwall"][:, 1].min()), float(_blob["northwall"][:, 1].max()) + 1.0
        s_foot, s_full = float(_blob["southwall"][:, 1].max()), float(_blob["southwall"][:, 1].min()) - 4.0
        w_foot, w_full = float(_blob["westwall"][:, 0].max()), float(_blob["westwall"][:, 0].min()) - 5.0
        self.rim_feet = dict(north=(n_foot, n_full), south=(s_foot, s_full), west=(w_foot, w_full))
        # A RIDGE ALSO ENDS WHERE ITS BLOB ENDS.  northwall's blob stops at x=210 and
        # says so in its own note ("the rim runs out at x~210, where the gorge's own
        # walls take the river on to the Long Reach"), but the term was a function of
        # WY alone and ran the ridge clean across the tile — which is why the Long
        # Reach floor control at [226,186] wants 9.0 and measured 17.58 with its floor
        # profile already pinned at the minimum.  The prose was right and the geometry
        # never read it.
        def _run_out(v, lo, hi):
            return sstep(lo - 12.0, lo + 8.0, v) * (1.0 - sstep(hi - 8.0, hi + 12.0, v))
        n_run = _run_out(WX, float(_blob["northwall"][:, 0].min()), float(_blob["northwall"][:, 0].max()))
        w_run = _run_out(WY, float(_blob["westwall"][:, 1].min()), float(_blob["westwall"][:, 1].max()))
        R_n = crest["northwall"] * sstep(n_foot, n_full, WY + fold_n) * amp * n_run
        R_s = crest["southwall"] * sstep(s_foot, s_full, WY + fold_s) * amp
        R_w = crest["westwall"] * sstep(w_foot, w_full, WX + fold_w) * ampw * w_run
        # Hollowmere Pass (sealed, world-level): a notch in the forest wall, so the
        # future attachment point is VISIBLE without being walkable yet
        hm = [e for e in REG_META.get("exits", []) if e["id"] == "pass-hollowmere"]
        if hm:
            hx, hy = float(hm[0]["at"][0]), float(hm[0]["at"][1])
            # THE NOTCH GOES IN THE RIM THE MAP PUTS THE PASS IN, not the one a comment
            # remembers.  This read `R_s` with the comment "v2: the sealed pass moved to
            # the SOUTH rim (the reachable bank)" while world.json had the exit at
            # [146,190] — the NORTH rim — since the restamp.  So the south ridge carried a
            # 55% notch at x=146 that nothing uses, and the north rim that actually holds
            # the pass stood full height across it.  A notch in the wrong ridge is invisible
            # in every render that does not happen to look at both.
            _rims = {"northwall": ("N", R_n), "southwall": ("S", R_s), "westwall": ("W", R_w)}
            _pick, _pd = None, 1e9
            for _mid, (_tag, _term) in _rims.items():
                _d, _in = _poly_dist(np.array([hx]), np.array([hy]), _blob[_mid])
                if float(_d[0]) < _pd:
                    _pick, _pd = _mid, float(_d[0])
            _notch = 1.0 - 0.55 * np.exp(
                -(((WX if _pick != "westwall" else WY)
                   - (hx if _pick != "westwall" else hy)) / 11.0) ** 2)
            if _pick == "northwall":
                R_n = R_n * _notch
            elif _pick == "southwall":
                R_s = R_s * _notch
            else:
                R_w = R_w * _notch
            print("valley_map: Hollowmere Pass notch cut in %s (%.1fu from its blob), at %s"
                  % (_pick, _pd, hm[0]["at"]))
        # THE WATER ACCESS IS A BREACH, and it has to breach everything in its way.
        # `wa` used to relax the bench profile and the shelf wall only, so at the
        # Moorage — the ONE bench-side descent to water in the region, the reason a
        # boat can leave in Ch2 — the north rim went on standing where the landing
        # had to be and the map's h=0.0 measured -4.29 in the field.  A descent that
        # only some of the terrain agrees to is not a descent.
        # A RIM CANNOT STAND IN THE RIVER.  northwall's blob reaches x=210 and its
        # own note says "the rim runs out at x~210, where the gorge's own walls take
        # the river on to the Long Reach" — but the ridge term knew nothing about the
        # channel, so at the Moorage the river's own LEFT EDGE (y~170 at x~200) lay
        # inside the ridge's footprint and the region's one boat landing measured 3.4u
        # above its water.  The east escarpment two lines below has always backed off
        # within 22u of the channel; the rims now do the same, which is the map's note
        # made into geometry instead of prose.
        self.rim = (np.maximum.reduce([R_n, R_s, R_w])
                    * (1.0 - 0.85 * (1.0 - sstep(9.0, 22.0, dr)))
                    * (1.0 - 0.85 * wa))

        # ---- BLOB RIDGES (schema v2): gatewall + any interior massif ---------
        # Axis-aligned walls above are the tile's frame; blob massifs are the
        # STORY walls.  The gatewall seals the Whisperwood bowl; the OLD GATE is
        # its only cut — carved where the ROAD passes through it, so map and
        # terrain cannot disagree about where the breach is.
        self._blob_ridges_pending = [m for m in WORLD["massifs"]
                                     if m["kind"] == "ridge"
                                     and m["id"] not in ("northwall", "southwall", "westwall")]
        self._ridge_amp = amp
        esc = sstep(263.0, 280.0, WX) * (1.0 - 0.85 * (1.0 - sstep(9.0, 22.0, dr)))
        Rg = self.wl_s + (GORGE_CUT - 3.0) * self.g_s
        self.gorge_rim = Rg
        # ...and the gorge SHOULDER yields at the breach too.  With only the bench and
        # the rim relaxed, the Moorage still measured +2.86 against its map height of
        # 0.0, because the shoulder term was holding 6.5u of gorge wall exactly where
        # the boat has to be. The Moorage is the one place in the region where the
        # gorge is supposed to be open to the water; Ch2 ends by rowing out of it.
        gw = self.g_s * (1.0 - sstep(15.0, 33.0, dr)) * (1.0 - 0.92 * wa)
        Wc = self.hw + 6.0 + 10.0 * g            # lateral run of the bank profile
        bank = 3.0 + 9.0 * g
        q = np.clip(dr / Wc, 0.0, 1.0)
        # DEPTH scales with width: at 18-22u wide and 1.5u deep the bright rock bed
        # showed straight through the 0.82-alpha water and the whole river read as
        # milk.  A navigable river also has to look navigable.
        bed = self.wl - (0.95 + 0.085 * river_width(self.tr) + 1.4 * g)
        self.bed = bed
        prof = bed + (self.wl + bank - bed) * sstep(0.0, 1.0, q)
        chan = sstep(0.0, 1.0, 1.0 - q)
        # A SECOND, NARROW carve applied after the works.  The wide profile is what
        # shapes the valley and the gorge walls (20u of lateral run inside the
        # notch), but it also reached 20u past the water and dragged the Valley Gate
        # apron 4u down into the gorge.  So the wide profile shapes the LAND, the
        # works are laid on it, and this narrow pass guarantees the CHANNEL.
        q2 = np.clip(dr / (self.hw + 1.8), 0.0, 1.0)
        prof2 = bed + (self.wl + 0.9 - bed) * sstep(0.0, 1.0, q2)
        chan2 = sstep(0.0, 1.0, 1.0 - q2)

        self.road = ROAD_XY - np.array([CX, CY])
        self.road_s = ROAD_S
        self.road_h = ROAD_Z.copy()
        drd, ridx = _chunked_nearest(X, Y, self.road[:, 0], self.road[:, 1])
        self.drd, self.ridx = drd, ridx
        # THE ROAD'S APRON IS NARROW ON THE GATE COURT.  Everywhere else the grade
        # blends the ground to the ribbon over 2.8..8.0u, which is what makes a road
        # read as cut into its shelf.  On the culvert it would also cut 8u out of the
        # gate wall's own east abutment — the rock the wall has to bite into — and the
        # seal probe measured exactly that (2.25u of open ground, 131 leaked cells).
        # A gate court is masonry laid BETWEEN rock, not a graded verge, so the apron
        # there is the ribbon's own width plus a metre.
        r0 = np.where(ROAD_CULV, 1.2, 2.8)
        r1 = np.where(ROAD_CULV, 3.0, 8.0)
        wroad = 1.0 - sstep(r0[ridx], r1[ridx], drd)
        self.road_apron = (r0, r1)

        # blob ridges need the road distance for the Old Gate cut, so they land here
        for m in self._blob_ridges_pending:
            bd, _ = _poly_dist(WX, WY, m["blob"])
            w_blob = 1.0 - sstep(0.0, 14.0, bd)
            Rb = float(m.get("crest", 30.0)) * w_blob * self._ridge_amp
            if m["id"] == "gatewall":
                # THE OLD GATE: THE BREACH IS THE NOTCH, AND THE NOTCH IS SIZED BY THE
                # PINCH RATIO.  This was `sstep(3.5, 9.0, drd)` — a 9u yield either
                # side of the ROAD and nothing about the water at all.  Measured on the
                # pinch line it left living rock at -3u and +14u: a 17u gap for a 4.5u
                # channel, where the town's own notch is 19.6 m rock-to-rock against a
                # 6.95 m grate = 2.82 grate-widths.  Carried as a RATIO (metres would
                # ask for 6.3u, which cannot even hold the ratified channel), the notch
                # wants ~13.5u, and the gate structure spans all of it:
                #     rock | curtain 1.58 | doorway 1.41 | founded 1.02 | grate 2.00 | rock
                #     (half-widths; the same numbers the seat was derived from)
                # The wall yields where the ROAD passes and where the WATER passes, and
                # nowhere else — which is what "the river cut it, the Order gated it"
                # means in geometry rather than in prose.
                # THE "212-CELL BYPASS" WAS MY OWN PROBE, NOT THE TERRAIN, and the
                # ridge floor I wrote to close it is deliberately NOT here.  The seal
                # probe counted any cell downstream of the pinch line IN THE RIVER'S
                # FRAME, and this massif runs diagonally across that frame, so cells
                # still on the highland side — riding the band's own inner edge, 20 to
                # 30u west of the channel — scored as escapes.  Fixed to ask the real
                # question (out past the gatewall's OUTER face) the count is 0, and it
                # is 0 WITH THE FLOOR REMOVED TOO: measured both ways, one build apart.
                # So the floor bought nothing, and a change with no evidence behind it
                # does not get to stay just because it was already written.  The crest
                # does sag to 25.7..29.1 inside its band; the fill proves that ground
                # connects to the highland, which is where it belongs, and not to the
                # valley.
                # ...and the NOTCH follows the same rule: a wide yield along the road
                # is right where the road threads the wall, and wrong on the court,
                # where it would open the very ground the wall's east end stands in.
                _c0 = np.where(ROAD_CULV, 1.2, 2.6)
                _c1 = np.where(ROAD_CULV, 2.4, 4.6)
                Rb = Rb * np.minimum(sstep(_c0[ridx], _c1[ridx], drd),
                                     sstep(self.hw, self.hw + 1.2, dr))
            self.rim = np.maximum(self.rim, Rb)
        shelves = []
        for (wx_, wy_, h_, r0, r1) in (
                (EMBERBROOK[0], EMBERBROOK[1], float(EMBERBROOK[2]), 8.0, 15.0),
                (ROAD_END_W[0], ROAD_END_W[1], float(ROAD_Z[-1]), 4.5, 10.5)):
            shelves.append((1.0 - sstep(r0, r1, np.hypot(WX - wx_, WY - wy_)), h_))

        # ---- tributary distance fields (one per found ravine) ----------------
        self.trib = []
        for _t in TRIBS:
            _dt, _ti = _chunked_nearest(X, Y, _t["xy"][:, 0] - CX, _t["xy"][:, 1] - CY)
            self.trib.append((_dt, _t["z"][_ti], _t["w"]))

        self._dbg = dict(pw=pw, ph=ph, rim=self.rim, esc=esc, Rg=Rg, gw=gw,
                         chan=chan, prof=prof, chan2=chan2, prof2=prof2, q=q,
                         bed=bed, Wc=Wc, bank=bank, dev=dev)

        def assemble(a_prof, with_built=True):
            bank_a = _boxblur(np.interp(self.tr, self.floor_t, a_prof), 6, 3)
            # NB: a saturating exponential, not np.minimum(dr, 45).  The clamp has a
            # hard gradient break exactly 45u from the channel, and the zone grid's
            # slope percentile read that break as a 200u-long straight escarpment
            # running the whole length of the valley on both banks.
            # wl_s, NOT wl: the ambient land is referenced to the SMOOTHED water
            # level.  Read sharp it steps by the river's whole fall between two
            # reaches wherever the nearest reach changes, so every meander grows a
            # 100u straight cliff down its medial axis (which the zone grid then
            # faithfully calls crag).  The channel carve keeps the sharp value.
            H = self.wl_s + bank_a + dev + 3.4 * (1.0 - np.exp(-dr / 26.0))
            H = H * (1.0 - pw) + ph * pw                       # plateau mesa
            rw = sstep(0.0, 6.5, self.rim - H)
            H = H * (1.0 - rw) + self.rim * rw                 # ridges / forest wall
            # ---- THE CANYON (schema v2): asymmetric trench ------------------
            # FAR side (sideF): the far wall climbs farWallRise above local water
            # over a short run past the channel — unclimbable by height, the
            # canon's only legitimate hard gate.  BENCH side (sideB): the bench
            # flattens toward benchClearance above water, which is what makes
            # the road's shelf read as THE way through.  Influence fades by 46u
            # so meander medial axes never see the side flip.
            cw = 1.0 - sstep(30.0, 46.0, dr)
            FW = self.wl_s + self.rise_t + 0.55 * dev
            fw = self.sideF * cw * sstep(self.hw + 1.5, self.hw + 8.5, dr)
            H = H * (1.0 - fw) + np.maximum(H, FW) * fw
            BW = self.wl_s + self.bench_t + 0.35 * dev
            bw = self.sideB * cw * (1.0 - sstep(self.hw + 2.0, self.hw + 15.0, dr)) \
                 * sstep(0.0, 2.0, dr - self.hw) * 0.85
            # the bench never rises above the wall rule: blend, don't max
            H = H * (1.0 - bw) + BW * bw
            # ---- THE SHELF (canyon.shelf, user: a RESTRICTED ridge walk) -----
            # Behind the road (away from the river) the mountain rises again, so
            # the traversable ground is a narrow ledge between the canyon lip and
            # a back wall — restriction by height, never by fences.  Applies only
            # along the valley stretch (after the Old Gate), so the Whisperwood
            # bowl keeps its own shape.
            SH = CANYON.get("shelf")
            if SH:
                shw = float(SH.get("width", 9.0))
                brise = float(SH.get("backRise", 12.0))
                og = PORTALS.get("old-gate")
                if og is not None:
                    _ob = w2b(og["at"][0], og["at"][1])
                    _oi = int(np.argmin(np.hypot(self.road[:, 0] - _ob[0], self.road[:, 1] - _ob[1])))
                    og_s = float(self.road_s[_oi])
                else:
                    og_s = 0.0
                # THE SHELF SPINE: the road, plus an authored OVERRUN past the
                # last portal so the ledge outlives its destinations and pinches
                # out against the rim — terrain, not a corridor (user note)
                ov = SH.get("overrun")
                if ov:
                    ext = np.array([[pp[0] - CX, pp[1] - CY] for pp in ov["points"]], float)
                    spine_xy = np.vstack([self.road, ext])
                else:
                    spine_xy = self.road
                spine_s = np.concatenate([[0.0], np.cumsum(
                    np.linalg.norm(np.diff(spine_xy, axis=0), axis=1))])
                drd_sh, ridx_sh = _chunked_nearest(X, Y, spine_xy[:, 0], spine_xy[:, 1])
                rs_sh = spine_s[ridx_sh]
                if ov:
                    tap = float(ov.get("taper", 12.0))
                    end_close = sstep(spine_s[-1] - tap, spine_s[-1], rs_sh)
                else:
                    end_close = 0.0
                after_gate = sstep(og_s + 6.0, og_s + 18.0, rs_sh)
                # POCKETS: authored widenings so the ledge is not one uniform
                # width — the wall bows outward locally (user note)
                shw_l = np.full_like(drd, shw)
                for pk in SH.get("pockets", []):
                    px_, py_ = pk["at"][0], pk["at"][1]
                    g_ = np.exp(-((WX - px_) ** 2 + (WY - py_) ** 2) / (2.0 * float(pk.get("r", 12.0)) ** 2))
                    shw_l = shw_l + float(pk.get("extraWidth", 10.0)) * g_
                # the overrun pinches: ledge width -> 0 at the spine's far end
                shw_l = shw_l * (1.0 - end_close) + 0.4 * end_close
                # STEEP onset: wall, not slope — the hand AWAY FROM THE WATER should
                # touch rock (user note: no roamable skirt beside the path).  Which
                # hand that is follows benchSide: with the bench on the left bank the
                # rock is on the player's left and the river on the right.
                wallw = (sstep(shw_l, shw_l + 4.0, drd_sh) * self.sideB
                         * after_gate * sstep(2.0, 6.0, dr - self.hw)
                         * (1.0 - self.wa))            # the Moorage descent stays open
                BACK = self.wl_s + brise * (0.78 + 0.22 * sstep(shw_l, shw_l + 12.0, drd_sh)) + 0.6 * dev
                H = H * (1.0 - wallw) + np.maximum(H, BACK) * wallw
            # ---- TRIBUTARY GROOVES: a waterline needs somewhere to sit -------
            # np.minimum, never a blend: a found ravine may only CUT.  If it could
            # fill it would build a ridge wherever the trace crossed ground lower
            # than the traced cell, which is exactly the artefact a hand-drawn
            # stream leaves behind.
            for (_dt, _zt, _wt) in self.trib:
                q_ = np.clip(_dt / (_wt * 3.0), 0.0, 1.0)
                pr_ = (_zt - 0.55) + (_zt + 1.70 - (_zt - 0.55)) * sstep(0.0, 1.0, q_)
                w_ = sstep(0.0, 1.0, 1.0 - q_)
                H = np.minimum(H, H * (1.0 - w_) + pr_ * w_)
            H = H - np.clip(H + 5.0, 0.0, 26.0) * esc          # east escarpment
            H = np.where(Rg > H, H + (Rg - H) * gw, H)         # gorge shoulders
            H = H * (1.0 - chan) + prof * chan                 # valley + gorge walls
            if not with_built:
                return H
            # shelves BEFORE the road grade: in v2 the road passes THROUGH the
            # Emberbrook shelf while descending to the Old Gate, and a shelf
            # applied last pinned the clearing back to h=26 over the graded road
            # (a 0.41u pierce at station 38).  The town shapes the ground; the
            # road cuts through whatever the ground is.
            for w_, h_ in shelves:
                H = H * (1.0 - w_) + h_ * w_
            H = H * (1.0 - wroad) + self.road_h[ridx] * wroad  # the road grade
            # works may embank right up to the waterline; none of them can fill it
            return H * (1.0 - chan2) + prof2 * chan2

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
            a_prof = np.clip(a_prof + err * 0.7, 0.55, 12.0)
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
        alt = H - self.wl_s
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
    out.append("falls: lip (sill, gatewall outer face) t=%.3f arc %.0fu -> foot t=%.3f arc %.0fu; gorge t=%.3f..%.3f, rim %.0f cut %.0f"
               % (T_LIP, T_LIP * RIVER_LEN, T_FALLS_END, T_FALLS_END * RIVER_LEN,
                  T_GORGE0, T_GORGE1, GORGE_RIM, GORGE_CUT))
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
        # rim.west = "forestwall": the region says its west rim is a wall of wood,
        # and no forest stamp covers it, so the treatment is read directly.  A
        # derived stand, flagged in findings — not an invented one.
        if REGION["rim"].get("west") == "forestwall":
            WXc = self.BX + CX
            fwall = ((WXc < 34.0) & (~crag) & (~wet) & (SL < 1.35) & (DCH > 1.2)
                     & (O3.fbm(self.BX, self.BY, 0.05, seed=911, oct_=4) > 0.36))
            dens = np.maximum(dens, fwall * 0.8)
            self.stand["west-forestwall"] = fwall
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
