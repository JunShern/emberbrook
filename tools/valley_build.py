"""valley_build.py — build THE VALLEY region (chapters 1-2) in style F2.

  Blender -b --factory-startup -P tools/valley_build.py

The first real overworld region, replacing the 120 x 90u prototype tile.  It is
280 x 200u of terrain and it AUTHORS NOTHING about its own geography: every height,
every zone, the river, the road, the forests, the town anchors and the rim
treatments are read from

    public/world/world.json                  (spine, massifs, envelopes, graph)
    public/world/regions/valley.region.json  (the region's own refinement)

through tools/valley_map.py.  Edit the map, re-run this, get the same tile back.

REUSE.  The style is F2, unchanged: overworld3_lib's zone grid, zone-driven
tessellation and crag treatment, its four tree constructions and procedural
vegetation maps; overworld2_lib's tar boat, mooring basin and jetty;
overworld2_build's PBR material recipe; overworld_build's Prop accumulator, class
palette and dusk rig; overworld3_build's terrain material pass verbatim.  What is
new here is region CONTENT that the prototype had no equivalent of:

    * the two TOWN IMPRESSIONS (Emberbrook's plateau village, Dellhollow's
      gorge-straddling stepped clusters with its weir flight)
    * the two PORTAL markers
    * region PLANTING: the map's forest stamps, approach (a) in the stands and
      hybrid (c) breaking their edges, with the road held as a corridor
    * the VISTA RING, generated from the PARENT's coarse data
"""
import bpy
import bmesh
import json
import math
import os
import random
import sys
import time

import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valley_map as VM            # FIRST: re-points overworld_lib at the region
import overworld_lib as L
import overworld_build as B
import overworld2_lib as O2
import overworld2_build as B2
import overworld3_lib as O3
import overworld3_build as B3      # F2's material + vertex-colour passes

# The canyon rebuild puts more crag beside the gorge-rim climb than F2's tile ever
# had, and the 0.16u road notch no longer clears the terrain/ribbon sawtooth
# (verify measured a 0.088u pierce).  Deepen the worn corridor: invisible at this
# scale, and a canyon road WOULD be cut deeper into its shelf.
_rn_o3 = O3.road_notch
O3.road_notch = lambda F, x, y, depth=0.28: _rn_o3(F, x, y, depth)

ROOT = VM.ROOT
STYLE = "f2"                       # the TREATMENT is F2's, byte for byte
SUF = "valley"
OUT_BLEND = os.path.join(ROOT, "tools/blends/overworld-valley.blend")
BUNDLE = os.path.join(ROOT, "public/assets/scenes/ow-valley")

srgb = B.srgb
(GRASS, GRASS_HI, AUTUMN, ROCK, PEAK, SAND, DIRT, WATER, WALL, ROOF, WOOD, STONE,
 FOL_A, FOL_B, FOL_C, TRUNK, EMIT, BASE, METAL, MIST) = range(20)
TAR, CANVAS, ROPE, LEAF, TUFT, LAMP = range(20, 26)
LEAFM, LEAFC, BARK, MARK = O3.LEAFM, O3.LEAFC, O3.BARK, O3.MARK

HOUSE_RIDGE = VM.HOUSE_RIDGE       # 1.6u — the scale contract beside a 1.45u character
STATS = {}


def gh(F, zg, fr, x, y):
    """The BUILT ground height at one point (crag treatment included)."""
    return float(O3.height(F, zg, np.array([float(x)]), np.array([float(y)]), fr)[0])


def ghv(F, zg, fr, x, y):
    return O3.height(F, zg, np.asarray(x, float), np.asarray(y, float), fr)


# =============================================================================
# WATER, ROAD, GREEN — the ribbons
# =============================================================================
def build_water(col, F):
    """The river surface, at the PARENT spine's width profile.

    The widening (3u at Ember Falls to 22u at the SE exit) is story-load-bearing:
    it is why a boat can leave from the Moorage and could not leave from anywhere
    upstream, so it is driven straight off world.json's own width column.
    """
    xy = VM.RIV_XY[::3]
    t = VM.RIV_T[::3]
    hw = VM.water_halfwidth(t) * 1.03
    wl = VM.water_level(t)
    tg = np.gradient(xy, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    nx, ny = -tg[:, 1], tg[:, 0]
    bx, by = xy[:, 0] - VM.CX, xy[:, 1] - VM.CY
    p = B.Prop("water_river")
    p.strip(WATER, list(zip(bx + nx * hw, by + ny * hw, wl)),
            list(zip(bx - nx * hw, by - ny * hw, wl)))
    ob = p.finish(col)
    STATS["river_width"] = (float(VM.RIV_WIDTH[0]), float(VM.RIV_WIDTH[-1]))
    return ob


def _ribbon(p, cls, xy, z, hw):
    tg = np.gradient(xy, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    nx, ny = -tg[:, 1], tg[:, 0]
    p.strip(cls, list(zip(xy[:, 0] + nx * hw, xy[:, 1] + ny * hw, z)),
            list(zip(xy[:, 0] - nx * hw, xy[:, 1] - ny * hw, z)))


def build_road(col, F):
    """walk_road — the visible road AND the walk network, on its authored z.

    The edge is deliberately SCRUFFY (user note: clean edges read as paving):
    the halfwidth wanders +-35% along the stations, independently per side."""
    xy = np.column_stack([F.road[:, 0], F.road[:, 1]])
    p = B.Prop("walk_road")
    s_ = F.road_s
    wob_l = 1.0 + 0.35 * np.sin(s_ * 0.61 + 0.9) * np.abs(np.sin(s_ * 0.173 + 2.2))
    wob_r = 1.0 + 0.35 * np.sin(s_ * 0.53 - 1.7) * np.abs(np.sin(s_ * 0.191 + 0.4))
    tg = np.gradient(xy, axis=0)
    tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
    nx, ny = -tg[:, 1], tg[:, 0]
    hw = VM.ROAD_WIDTH * 0.5
    z = F.road_h + 0.09
    p.strip(DIRT, list(zip(xy[:, 0] + nx * hw * wob_l, xy[:, 1] + ny * hw * wob_l, z)),
            list(zip(xy[:, 0] - nx * hw * wob_r, xy[:, 1] - ny * hw * wob_r, z)))
    return p.finish(col)


def build_causeway(col, F, zg, fr):
    """The span the map forces (see valley_map.CAUSEWAY).

    region.crossings.list is empty by ruling, but the region's road changes bank at
    the parent spine's second meander, so it must cross the water somewhere.  Rather
    than leave the ribbon hanging in mid-air over the channel, the build lays a low
    culverted causeway under it and flags it as the build's one unauthorised object.
    Delete-on-map-fix: valley_map.CAUSEWAY = False and this returns nothing.
    """
    if not VM.CAUSEWAY or not VM.ROAD_SPANS:
        return None
    p = B.Prop("walk_causeway")
    n = 0
    for (a, b) in VM.ROAD_SPANS:
        a, b = max(a - 3, 0), min(b + 3, len(F.road) - 1)
        xy = F.road[a:b + 1]
        z = F.road_h[a:b + 1]
        tg = np.gradient(xy, axis=0)
        tg /= np.maximum(np.linalg.norm(tg, axis=1)[:, None], 1e-9)
        nx, ny = -tg[:, 1], tg[:, 0]
        for side in (-1, 1):
            ex = xy[:, 0] + nx * side * 1.35
            ey = xy[:, 1] + ny * side * 1.35
            bed = ghv(F, zg, fr, ex, ey) - 0.3
            p.strip(STONE, list(zip(ex, ey, z + 0.06)), list(zip(ex, ey, bed)))
        # three culvert arches so the causeway is fill, not a dam
        for k in (0.30, 0.50, 0.70):
            i = int(k * (len(xy) - 1))
            cx_, cy_ = float(xy[i, 0]), float(xy[i, 1])
            dz = float(F._river_dist(np.array([cx_]), np.array([cy_]))[1][0])
            w = float(VM.water_level(np.array([dz]))[0])
            ang = math.atan2(float(tg[i, 1]), float(tg[i, 0]))
            p.cube(STONE, (cx_, cy_, w + 0.62), (0.9, 3.6, 0.34), rz=ang)
            n += 1
        # a CONTINUOUS kerb, not a row of posts.  With the road grade now embanking
        # the crossing, discrete posts read as cubes floating beside the ribbon.
        for side in (-1, 1):
            kx = xy[:, 0] + nx * side * 1.22
            ky = xy[:, 1] + ny * side * 1.22
            p.strip(STONE, list(zip(kx, ky, z + 0.34)), list(zip(kx, ky, z - 0.10)))
            kx2 = xy[:, 0] + nx * side * 1.02
            ky2 = xy[:, 1] + ny * side * 1.02
            p.strip(STONE, list(zip(kx, ky, z + 0.34)), list(zip(kx2, ky2, z + 0.30)))
    STATS["causeway_arches"] = n
    return p.finish(col)


# =============================================================================
# TOWN IMPRESSIONS — impressions, NOT the town models shrunk
# =============================================================================
def build_emberbrook(col, F, zg, fr):
    """Emberbrook: a clustered warm-lit village in a forest clearing on the plateau.

    An IMPRESSION at overworld scale: 14 houses whose ridges land at 1.6u beside a
    1.45u character, the Heartlight on its plinth at the centre (world canon: a
    Heartlight is rare and magical, and Emberbrook is the Heartlight town — the
    other lights here are ordinary lanterns), and a green for the spawn scan.
    """
    rng = random.Random(20260730)
    p = B.Prop("emberbrook")
    cx, cy = L.VILLAGE
    h0 = F.village_h
    ring = []
    for i in range(14):
        a = i * (2 * math.pi / 14) + 0.22
        r = 4.4 + (i % 3) * 2.0 + rng.uniform(0.0, 1.1)
        hx, hy = cx + math.cos(a) * r, cy + math.sin(a) * r
        gz = gh(F, zg, fr, hx, hy)
        fa = a + math.pi + rng.uniform(-0.28, 0.28)          # face the green
        w = 1.05 + rng.uniform(0, 0.34)
        d = 0.90 + rng.uniform(0, 0.24)
        bh = 0.96 + rng.uniform(0, 0.14)
        p.cube(WALL, (hx, hy, gz + bh / 2), (w, d, bh), rz=fa)
        p.prism(ROOF, (hx, hy, gz + bh), w * 1.20, d * 1.20,
                HOUSE_RIDGE - bh + rng.uniform(0.0, 0.10), rz=fa)
        p.cube(STONE, (hx + math.cos(fa + 1.6) * w * 0.30,
                       hy + math.sin(fa + 1.6) * w * 0.30, gz + bh + 0.42),
               (0.17, 0.17, 0.74), rz=fa)
        # ONE warm window per house facing the green: the "warm-lit" read at 34u
        p.cube(EMIT, (hx + math.cos(fa) * d * 0.56, hy + math.sin(fa) * d * 0.56,
                      gz + bh * 0.60), (0.30, 0.07, 0.24), rz=fa)
        ring.append((hx, hy))
    # ---- the Heartlight: plinth + a standing light, the town's whole identity ----
    for i in range(8):
        a = i * (2 * math.pi / 8)
        p.cube(STONE, (cx + math.cos(a) * 0.62, cy + math.sin(a) * 0.62, h0 + 0.16),
               (0.34, 0.28, 0.32), rz=a)
    p.cone(STONE, (cx, cy, h0 + 0.62), 0.34, 0.24, 1.0, seg=8)
    p.ico(EMIT, (cx, cy, h0 + 1.34), (0.36, 0.36, 0.44), subd=2)
    # ---- ordinary lanterns on posts + a low boundary fence ----
    for k in range(5):
        a = 0.5 + k * 1.15
        fx, fy = cx + math.cos(a) * 8.4, cy + math.sin(a) * 8.4
        gz = gh(F, zg, fr, fx, fy)
        p.cube(WOOD, (fx, fy, gz + 0.52), (0.12, 0.12, 1.04), rz=a)
        p.cube(EMIT, (fx, fy, gz + 1.12), (0.17, 0.17, 0.20), rz=a)
    for a in np.linspace(2.6, 5.4, 11):
        fx, fy = cx + math.cos(a) * 9.6, cy + math.sin(a) * 9.6
        gz = gh(F, zg, fr, fx, fy)
        p.cube(WOOD, (fx, fy, gz + 0.30), (0.11, 0.11, 0.60), rz=a)
    STATS["emberbrook_houses"] = 14
    return p.finish(col)


def build_emberbrook_green(col, F, zg, fr):
    """The green — a walk_ surface, so the spawn scan has somewhere sensible to land."""
    cx, cy = L.VILLAGE
    h0 = F.village_h + 0.07
    a = np.linspace(0, 2 * math.pi, 33)
    ring = [(cx + 3.4 * math.cos(t), cy + 3.4 * math.sin(t)) for t in a]
    p = B.Prop("walk_emberbrook_green")
    p.strip(GRASS, [(x, y, h0) for x, y in ring],
            [(cx + (x - cx) * 0.05, cy + (y - cy) * 0.05, h0) for x, y in ring])
    return p.finish(col)


def gorge_frame(F, wx, wy):
    """Local gorge frame at a world point: tangent, cross-normal, water level, halfwidth."""
    i = int(np.argmin(np.hypot(VM.RIV_XY[:, 0] - wx, VM.RIV_XY[:, 1] - wy)))
    i = max(1, min(len(VM.RIV_XY) - 2, i))
    tg = VM.RIV_XY[i + 1] - VM.RIV_XY[i - 1]
    tg = tg / np.linalg.norm(tg)
    nr = np.array([-tg[1], tg[0]])
    t = float(VM.RIV_T[i])
    return (np.array([VM.RIV_XY[i, 0] - VM.CX, VM.RIV_XY[i, 1] - VM.CY]), tg, nr,
            float(VM.water_level(np.array([t]))[0]),
            float(VM.water_halfwidth(np.array([t]))[0]), t)


def build_dellhollow(col, F, zg, fr):
    """Dellhollow: stepped clusters down BOTH gorge rim walls, weirs, wheels, gate.

    The town straddles the river in its gorge (world.json), so the impression is
    NOT a cluster on a shelf: it is two terraced strings of buildings facing each
    other across the notch, with the lock/weir flight visible on the water between
    them and the Valley Gate up on the rim where the road arrives.
    """
    rng = random.Random(20260731)
    p = B.Prop("dellhollow")
    aw = VM.DELLHOLLOW
    ctr, tg, nr, wl, hw, t = gorge_frame(F, aw[0], aw[1])
    rot = math.radians(float(VM.ANCHORS["dellhollow"]["rotationDeg"]))
    base_ang = math.atan2(float(tg[1]), float(tg[0]))
    n_house = 0
    for side in (-1, 1):
        for tier in range(3):
            lat = hw + 2.4 + tier * 4.4
            for stat in (-13.0, -7.0, -1.0, 5.0, 11.0):
                jx = rng.uniform(-1.1, 1.1)
                px = float(ctr[0] + tg[0] * (stat + jx) + nr[0] * side * lat)
                py = float(ctr[1] + tg[1] * (stat + jx) + nr[1] * side * lat)
                gz = gh(F, zg, fr, px, py)
                if gz < wl + 0.35:                  # that station is in the water
                    continue
                yaw = base_ang + rot + (0.0 if side > 0 else math.pi)
                w = 1.0 + rng.uniform(0, 0.30)
                d = 0.86 + rng.uniform(0, 0.22)
                bh = 0.92 + rng.uniform(0, 0.16)
                # A terrace pad + retaining wall is what makes a cluster read
                # STEPPED — but a pad placed at the CENTRE height cantilevers off a
                # gorge wall, which is what the first render showed.  The pad top is
                # the lowest of its own four corners, and the wall reaches from there
                # down to the ground beneath its outer edge.
                pw_, pd_ = w * 1.55, d * 1.55
                ca, sa = math.cos(yaw), math.sin(yaw)
                cor = [(px + ca * u * pw_ / 2 - sa * v * pd_ / 2,
                        py + sa * u * pw_ / 2 + ca * v * pd_ / 2)
                       for u in (-1, 1) for v in (-1, 1)]
                ch = [gh(F, zg, fr, a_, b_) for a_, b_ in cor]
                pad = min(ch) + 0.10
                p.cube(STONE, (px, py, pad - 0.20), (pw_, pd_, 0.44), rz=yaw)
                foot = min(ch) - 0.4
                ox = px - nr[0] * side * pd_ * 0.52
                oy = py - nr[1] * side * pd_ * 0.52
                foot = min(foot, gh(F, zg, fr, ox - nr[0] * side * 1.6,
                                    oy - nr[1] * side * 1.6))
                drop = max(0.6, min(5.0, pad - foot))
                p.cube(STONE, (ox, oy, pad - 0.42 - drop / 2), (pw_, 0.38, drop), rz=yaw)
                gz = pad
                p.cube(WALL, (px, py, gz + bh / 2), (w, d, bh), rz=yaw)
                p.prism(ROOF, (px, py, gz + bh), w * 1.20, d * 1.20,
                        HOUSE_RIDGE - bh + rng.uniform(0, 0.10), rz=yaw)
                p.cube(EMIT, (px + math.cos(yaw + math.pi / 2) * d * 0.56,
                              py + math.sin(yaw + math.pi / 2) * d * 0.56,
                              gz + bh * 0.58), (0.26, 0.07, 0.20), rz=yaw)
                n_house += 1
    # ---- THE WEIR FLIGHT: the reason the locks exist ------------------------
    n_weir = 0
    crest = None
    for k, stat in enumerate((-11.0, -1.0, 9.0)):
        cx_ = float(ctr[0] + tg[0] * stat)
        cy_ = float(ctr[1] + tg[1] * stat)
        _, wtg, wnr, wwl, whw, _ = gorge_frame(F, cx_ + VM.CX, cy_ + VM.CY)
        ang = math.atan2(float(wtg[1]), float(wtg[0])) + math.pi / 2
        span = whw * 2.0 + 1.4
        # SEGMENTED: one 2 x 15 x 3.4u block beside 1.6u houses reads as a monolith,
        # and the moorage camera stood right behind it.  Six courses with hashed
        # offsets read as built masonry at the same cost.
        nb = 6
        for bi in range(nb):
            u = (bi - (nb - 1) / 2.0) * (span / nb)
            hj = float(O3._hash01(bi, k * 17, 3))
            p.cube(STONE, (cx_ + float(wnr[0]) * u, cy_ + float(wnr[1]) * u,
                           wwl - 1.0 - 0.10 * hj),
                   (1.5 + 0.22 * hj, span / nb * 0.97, 2.9), rz=ang)
        p.cube(STONE, (cx_, cy_, wwl + 0.62), (2.1, span, 0.36), rz=ang)   # crest walk
        # a visible weir LINE downstream of the sill: white water reads as a drop
        p.cube(STONE, (cx_ - float(wtg[0]) * 1.6, cy_ - float(wtg[1]) * 1.6,
                       wwl - 0.28), (0.9, span * 0.88, 0.5), rz=ang)
        if crest is None:
            crest = (cx_, cy_, wwl + 0.90, ang, span)
        # ---- waterwheel HINTS on the abutment (2 of the 3 stations) ----------
        if k != 1:
            for side in (-1, 1):
                wx_ = cx_ + float(wnr[0]) * side * (whw + 1.4)
                wy_ = cy_ + float(wnr[1]) * side * (whw + 1.4)
                for j in range(9):
                    a = j * (2 * math.pi / 9)
                    p.cube(WOOD, (wx_ + math.cos(a) * 1.15 * float(wtg[0]),
                                  wy_ + math.cos(a) * 1.15 * float(wtg[1]),
                                  wwl + 0.15 + math.sin(a) * 1.15),
                           (0.40, 0.14, 0.40), rz=ang, rx=a)
                p.cone(WOOD, (wx_, wy_, wwl + 0.15), 1.22, 1.22, 0.20, seg=12, rz=ang)
                p.cone(METAL, (wx_, wy_, wwl + 0.15), 0.16, 0.16, 1.2, seg=8, rz=ang)
                # the mill it drives
                mx = wx_ + float(wnr[0]) * side * 2.4
                my = wy_ + float(wnr[1]) * side * 2.4
                mz = gh(F, zg, fr, mx, my)
                p.cube(WALL, (mx, my, max(mz, wwl) + 0.85), (1.7, 1.5, 1.7), rz=ang)
                p.prism(ROOF, (mx, my, max(mz, wwl) + 1.70), 2.0, 1.8, 0.95, rz=ang)
                n_weir += 1
    STATS["dellhollow_houses"] = n_house
    STATS["dellhollow_wheels"] = n_weir
    return p.finish(col), crest


def build_dam_crest(col, F, zg, fr, crest):
    """The dam crest — by the region's own ruling the ONLY span of this river."""
    if crest is None:
        return None
    cx_, cy_, z, ang, span = crest
    p = B.Prop("walk_dam_crest")
    dx, dy = math.cos(ang), math.sin(ang)
    n = 9
    ts = np.linspace(-span / 2, span / 2, n)
    xs = cx_ + dx * ts
    ys = cy_ + dy * ts
    _ribbon(p, STONE, np.column_stack([xs, ys]), np.full(n, z + 0.05), 1.05)
    return p.finish(col)


def build_canopy(col, F, zg, fr):
    """DEEP FOREST the FF7/FF9 way (user-directed, third iteration, the keeper):
    the geometry is only a GENTLE LUMPY SWELL; the treetop read lives in a
    PAINTED CANOPY TEXTURE (tools/textures/canopy_painted_{albedo,normal}.png —
    ~600 procedurally painted crowns with lit tops and dark gap shadows) draped
    over it at world scale, exactly like the PS1 world maps did it, and exactly
    F2's texture+normal language.  Walkable-under (veg_, no-stand, no-block);
    corridor carved WIDE so no canopy ever overhangs the road (user note);
    canopy interior mask keeps specimen trees to the edges."""
    made = []
    zg.canopy_int = np.zeros_like(zg.BX, dtype=bool)
    RD = np.hypot(zg.BX[..., None] - F.road[::4, 0], zg.BY[..., None] - F.road[::4, 1])
    ri = RD.argmin(-1) * 4
    rd = RD.min(-1)
    rs = F.road_s[np.clip(ri, 0, len(F.road_s) - 1)]
    UVREP = 24.0                       # world units per texture repeat (~crown 1.5u)
    for st in VM.FORESTS:
        if st.get("representation") != "canopy":
            continue
        mask = zg.stand[st["id"]].copy()
        cor = st.get("corridor")
        # WIDE corridor margin: the swell tapers over ~2 cells, so carve far
        # enough that not even the taper leans over the road (user note)
        if cor:
            w = float(cor.get("width", 6.0)) * 0.5 + 2.4
            s0, s1 = cor.get("alongRoad", [0, len(VM.ROAD_CTRL_W) - 1])
            sa = VM._arclen(VM.ROAD_CTRL_W[:, :2])
            lo, hi = float(sa[int(s0)]), float(sa[int(min(s1, len(sa) - 1))])
            mask &= ~((rd < w) & (rs >= lo - 4.0) & (rs <= hi + 8.0))
        else:
            mask &= ~(rd < 5.6)
        for c in st.get("clearings", []):
            cx_, cy_ = VM.w2b(c["at"][0], c["at"][1])
            mask &= (np.hypot(zg.BX - cx_, zg.BY - cy_) > float(c["r"]))
        if not mask.any():
            continue
        soft = O3._box(mask.astype(float), 3)
        keep = soft > 0.10
        edge = np.clip(soft * 1.45, 0.0, 1.0)
        zg.canopy_int |= soft > 0.55
        gh_ = F.sample(zg.BX, zg.BY)
        billow = (np.abs(O3.fbm(zg.BX, zg.BY, 0.11, seed=61, oct_=3))
                  + 0.5 * np.abs(O3.fbm(zg.BX, zg.BY, 0.31, seed=62, oct_=2)))
        top = gh_ + (1.5 + 1.6 * billow) * edge + 0.2
        ii, jj = np.nonzero(keep)
        vid = -np.ones(keep.shape, np.int64)
        vid[ii, jj] = np.arange(len(ii))
        verts = np.column_stack([zg.BX[ii, jj], zg.BY[ii, jj], top[ii, jj]])
        faces = []
        K = keep
        for a, b in zip(*np.nonzero(K[:-1, :-1] & K[1:, :-1] & K[:-1, 1:] & K[1:, 1:])):
            faces.append((int(vid[a, b]), int(vid[a + 1, b]),
                          int(vid[a + 1, b + 1]), int(vid[a, b + 1])))
        if not faces:
            continue
        me = bpy.data.meshes.new("veg_canopy_" + st["id"])
        me.from_pydata([tuple(v) for v in verts], [], faces)
        # UVs at world scale; COLOR_0 = subtle edge darkening only (texture does
        # the crowns; glTF multiplies baseColorTexture x COLOR_0)
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi = me.loops[li].vertex_index
                uvl.data[li].uv = (verts[vi, 0] / UVREP, verts[vi, 1] / UVREP)
        ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
        shade = (0.62 + 0.38 * edge[ii, jj])[:, None] * np.ones((1, 3))
        cols = np.concatenate([shade, np.ones((len(shade), 1))], axis=1)
        ca.data.foreach_set("color", cols.ravel())
        mat = bpy.data.materials.get("mat_valley_canopy_tex")
        if mat is None:
            mat = bpy.data.materials.new("mat_valley_canopy_tex")
            mat.use_nodes = True
            nt = mat.node_tree
            bsdf = nt.nodes["Principled BSDF"]
            ta = nt.nodes.new("ShaderNodeTexImage")
            ta.image = bpy.data.images.load(os.path.join(ROOT, "tools/textures/canopy_painted_albedo.png"))
            tn = nt.nodes.new("ShaderNodeTexImage")
            tn.image = bpy.data.images.load(os.path.join(ROOT, "tools/textures/canopy_painted_normal.png"))
            tn.image.colorspace_settings.name = "Non-Color"
            vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
            mixn = nt.nodes.new("ShaderNodeMix"); mixn.data_type = 'RGBA'
            mixn.blend_type = 'MULTIPLY'; mixn.inputs["Factor"].default_value = 1.0
            nt.links.new(ta.outputs["Color"], mixn.inputs["A"])
            nt.links.new(vc.outputs["Color"], mixn.inputs["B"])
            nt.links.new(mixn.outputs["Result"], bsdf.inputs["Base Color"])
            nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.9
            nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
            bsdf.inputs["Roughness"].default_value = 0.86
        me.materials.append(mat)
        ob = bpy.data.objects.new("veg_canopy_" + st["id"], me)
        col.objects.link(ob)
        for p_ in me.polygons:
            p_.use_smooth = True
        made.append(ob)
        STATS["canopy_" + st["id"]] = int(len(faces))
    return made


def build_portals(col, F, zg, fr):
    """A visible marker at each portal: a town gate, and a gate-arch impression.

    The Valley Gate marker stands at the road's BUILT endpoint, not at the region's
    authored [215, 65] — the clearance pass shows that coordinate standing in the
    channel.  Reported as a map-change request.
    """
    p = B.Prop("portal_markers")
    # ---- emberbrook-gate: a timber town gate across the road ----------------
    # the station ~11u out from the town centre: the first render put the gate frame
    # straddling two houses because station 4 is only 4u from the green
    vx, vy = L.VILLAGE
    dv = np.hypot(F.road[:, 0] - vx, F.road[:, 1] - vy)
    i = int(np.argmin(np.abs(dv - 11.0)))
    i = max(2, min(len(F.road) - 3, i))
    rx, ry, rz = float(F.road[i, 0]), float(F.road[i, 1]), float(F.road_h[i])
    tgv = F.road[i + 1] - F.road[i - 1]
    tgv = tgv / np.linalg.norm(tgv)
    ang = math.atan2(float(tgv[1]), float(tgv[0]))
    for side in (-1, 1):
        gx = rx - float(tgv[1]) * side * 1.75
        gy = ry + float(tgv[0]) * side * 1.75
        gz = gh(F, zg, fr, gx, gy)
        p.cube(WOOD, (gx, gy, gz + 1.35), (0.30, 0.30, 2.70), rz=ang)
        p.cube(EMIT, (gx, gy, gz + 2.55), (0.18, 0.18, 0.22), rz=ang)
    p.cube(WOOD, (rx, ry, rz + 2.62), (0.26, 4.0, 0.34), rz=ang)
    p.prism(ROOF, (rx, ry, rz + 2.80), 0.9, 4.3, 0.42, rz=ang + math.pi / 2)
    # ---- dellhollow-valley-gate: a stone gate arch on the gorge rim ---------
    ex, ey = float(F.road[-1, 0]), float(F.road[-1, 1])
    ez = float(F.road_h[-1])
    tge = F.road[-1] - F.road[-4]
    tge = tge / np.linalg.norm(tge)
    ang2 = math.atan2(float(tge[1]), float(tge[0]))
    for side in (-1, 1):
        gx = ex - float(tge[1]) * side * 2.05
        gy = ey + float(tge[0]) * side * 2.05
        gz = gh(F, zg, fr, gx, gy)
        p.cube(STONE, (gx, gy, gz + 1.85), (1.05, 1.05, 3.70), rz=ang2)
        p.cube(STONE, (gx, gy, gz + 3.85), (1.25, 1.25, 0.42), rz=ang2)
        # the curtain either side: the NOTCH in the rim the gate sits in
        for k in (1, 2, 3):
            wx_ = gx - float(tge[1]) * side * k * 1.35
            wy_ = gy + float(tge[0]) * side * k * 1.35
            wz = gh(F, zg, fr, wx_, wy_)
            p.cube(STONE, (wx_, wy_, wz + 1.15 - 0.15 * k), (1.4, 1.0, 2.4 - 0.3 * k),
                   rz=ang2)
    p.cube(STONE, (ex, ey, ez + 3.55), (0.62, 4.6, 0.62), rz=ang2)
    for side in (-1, 1):
        p.cube(EMIT, (ex - float(tge[1]) * side * 1.5, ey + float(tge[0]) * side * 1.5,
                      ez + 3.05), (0.18, 0.18, 0.22), rz=ang2)
    return p.finish(col)


def build_props(col, F, zg, fr):
    """The waystone at the treeline break, plus rock outcrops in the crag."""
    p = B.Prop("props_valley")
    # ---- the Whisperwood waystone (ch1 fiction) -----------------------------
    wx_, wy_ = VM.w2b(*VM.LAND_W["waystone"][:2])
    wx_, wy_ = float(wx_), float(wy_)
    # stand it just OFF the ribbon so the road stays clear
    d = F.road_frame_at(VM.LAND_W["waystone"][0], VM.LAND_W["waystone"][1])
    nx, ny = -d[3][1], d[3][0]
    wx_, wy_ = d[0] + nx * 2.2, d[1] + ny * 2.2
    gz = gh(F, zg, fr, wx_, wy_)
    ang = math.atan2(d[3][1], d[3][0])
    p.cube(STONE, (wx_, wy_, gz + 0.12), (1.5, 1.5, 0.30), rz=ang)
    p.cube(STONE, (wx_, wy_, gz + 1.02), (0.62, 0.34, 1.60), rz=ang + 0.12)
    p.cube(MARK, (wx_ + math.cos(ang + math.pi / 2) * 0.19,
                  wy_ + math.sin(ang + math.pi / 2) * 0.19, gz + 1.16),
           (0.34, 0.02, 0.46), rz=ang + 0.12)
    # ---- rock outcrops, biased into the crag zones -------------------------
    rng = random.Random(4242)
    n = 0
    tries = 0
    while n < 46 and tries < 40000:
        tries += 1
        bx = rng.uniform(-VM.TILE_W / 2 + 6, VM.TILE_W / 2 - 6)
        by = rng.uniform(-VM.TILE_H / 2 + 6, VM.TILE_H / 2 - 6)
        zt = zg.type_at_blender(bx, by)
        if zt != "crag":
            continue
        if float(F.road_dist(np.array([bx]), np.array([by]))[0]) < 3.0:
            continue
        # an outcrop on a near-vertical face hangs in the air (the first render had
        # boulders stuck to the plateau cliff like barnacles)
        if float(F.slope_at(np.array([bx]), np.array([by]))[0]) > 1.35:
            continue
        gz = gh(F, zg, fr, bx, by)
        s = rng.uniform(0.8, 2.4)
        before = set(p.bm.faces)
        # SUNK, and only where the ground is level enough to hold it: an outcrop set
        # on its own centre height hangs off a gorge wall like a barnacle
        ca = [gh(F, zg, fr, bx + dx_, by + dy_)
              for dx_, dy_ in ((-s, -s), (s, -s), (s, s), (-s, s))]
        if max(ca) - min(ca) > 1.7:
            continue
        p.ico(ROCK, (bx, by, min(ca) + s * 0.10), (s * 1.15, s * 0.86, s * 0.70),
              subd=1, rz=rng.uniform(0, 6.28))
        for f in p.bm.faces:
            if f not in before:
                for v in f.verts:
                    v.co += Vector((rng.uniform(-.13, .13), rng.uniform(-.13, .13),
                                    rng.uniform(-.10, .10))) * s
        n += 1
    STATS["outcrops"] = n
    return p.finish(col)


def build_moorage_spur(col, F, zg, fr, root):
    """A short bank path from the gorge floor out to the jetty root."""
    a = np.array([root[0], root[1]], float)
    ctr = fr["ctr"]
    tg = fr["tg"]
    b_ = a + tg * 9.0
    ts = np.linspace(0, 1, 14)
    pts = a[None, :] * (1 - ts[:, None]) + b_[None, :] * ts[:, None]
    z = ghv(F, zg, fr, pts[:, 0], pts[:, 1]) + 0.09
    p = B.Prop("walk_dockpath")
    _ribbon(p, DIRT, pts, z, 0.85)
    return p.finish(col)


# =============================================================================
# THE VISTA RING — generated from the PARENT's coarse data
# =============================================================================
def build_vista(col, F):
    """fx_ silhouette RANGES and the river continuing beyond the envelope.

    Read off world.json: each massif's crest sets the height of the range that
    carries on past the tile edge, and riverSpine's last point carries
    `continues: true`, so the water leaves the frame instead of stopping at it.

    Built as continuous ridge STRIPS, one per band per side.  The first pass used a
    cone per summit and every render came back with a picket fence of tents: a cone
    is a shape, and a mountain range is a CREST LINE.  A strip whose crest is hashed
    per station, with the bands overlapping in depth, is both cheaper and right.
    """
    p = B.Prop("fx_vista_ring")
    crest = {m["id"]: m.get("crest", 30.0) for m in VM.WORLD["massifs"]}
    HX, HY = VM.TILE_W / 2, VM.TILE_H / 2
    sides = (("northwall", 0, +1, HY, VM.TILE_W),
             ("southwall", 0, -1, HY, VM.TILE_W),
             ("westwall", 1, -1, HX, VM.TILE_H),
             ("northwall", 1, +1, HX, VM.TILE_H))          # east: over the escarpment
    # A LOW APRON first: without it the gap between the tile's cut edge and the
    # first range is a hole straight to the world background, and the vista shot
    # reads as a matte painting with the bottom torn off.
    for axis, sgn, edge, run in ((0, +1, HY, VM.TILE_W), (0, -1, HY, VM.TILE_H),
                                 (1, -1, HX, VM.TILE_H), (1, +1, HX, VM.TILE_H)):
        a0, a1 = edge - 2.0, edge + 640.0
        w = run / 2 + 660.0
        q = []
        for da in (a0, a1):
            for wu in (-w, w):
                q.append((wu, da * sgn) if axis == 0 else (da * sgn, wu))
        p.strip(ROCK, [(float(q[0][0]), float(q[0][1]), -11.0),
                       (float(q[1][0]), float(q[1][1]), -11.0)],
                [(float(q[2][0]), float(q[2][1]), -13.0),
                 (float(q[3][0]), float(q[3][1]), -13.0)])
    n = 0
    for si, (mid, axis, sgn, edge, run) in enumerate(sides):
        for band in range(3):
            dist = edge + 96.0 + band * 128.0
            top = crest[mid] * (1.15 + 0.55 * band)
            step = 26.0 + band * 14.0
            us = np.arange(-run / 2 - 260.0, run / 2 + 260.0 + step, step)
            crest_pts, near_pts, far_pts = [], [], []
            for k, u in enumerate(us):
                h1 = float(O3._hash01(int(k), band * 37 + si * 101, 5))
                h2 = float(O3._hash01(int(k) + 7, band * 53 + si * 211, 9))
                hgt = top * (0.55 + 0.50 * h1 * h1)
                # jitter the range's DEPTH as well as its height: overlapping crest
                # lines are what make three strips read as many ranges
                # depth jitter stays SMALL.  At +-2.2 steps the crest line zig-zagged
                # further in depth than it advanced along the range, and the "range"
                # became a self-overlapping mass that filled the whole vista frame.
                dd = dist + (h2 - 0.5) * step * 0.45
                foot = step * 0.85
                for lst, off, z in ((crest_pts, 0.0, -10.0 + hgt),
                                    (near_pts, -foot, -10.0), (far_pts, foot, -10.0)):
                    d2_ = (dd + off) * sgn
                    a = (u, d2_) if axis == 0 else (d2_, u)
                    lst.append((float(a[0]), float(a[1]), z))
                n += 1
            # a RIDGE WITH VOLUME: two faces meeting at the crest.  A single strip has
            # no thickness and from a high camera you look straight into its hollow
            # back — the overview render read it as torn cardboard.
            p.strip(ROCK, crest_pts, near_pts)
            p.strip(ROCK, far_pts, crest_pts)
    # ---- the spine continuing SE past the envelope -------------------------
    sp = VM.WORLD["riverSpine"]["points"]
    if sp[-1].get("continues"):
        ex, ey = sp[-1]["pos"][0], sp[-1]["pos"][1]
        pex, pey = sp[-2]["pos"][0], sp[-2]["pos"][1]
        d = np.array([ex - pex, ey - pey], float)
        d /= np.linalg.norm(d)
        m = 16
        ts = np.linspace(0.0, 150.0, m)
        xs = ex + d[0] * ts - VM.CX
        ys = ey + d[1] * ts - VM.CY
        w = np.linspace(float(sp[-1]["width"]), float(sp[-1]["width"]) * 1.7, m) * 0.5
        zs = np.linspace(float(sp[-1]["pos"][2]), float(sp[-1]["pos"][2]) - 7.0, m)
        nx, ny = -d[1], d[0]
        p.strip(WATER, list(zip(xs + nx * w, ys + ny * w, zs)),
                list(zip(xs - nx * w, ys - ny * w, zs)))
    STATS["vista_crest_stations"] = n
    return p.finish(col)


# =============================================================================
# PLANTING — the region's forest stamps, F2's trees
# =============================================================================
# The line-up answered the question (round 3): (a) chunky sculpted canopies are the
# field workhorse — real geometry that never breaks up or sorts wrong under the
# steep follow camera — and (c) the hybrid is what breaks a STAND EDGE, because its
# card fringe is only ever seen against the sky, which is the one thing a card is
# good at.  (b) and (d) stay in the prototype's line-up.
STAND_CFG = {
    # emberwood is the region's DENSE wood and the road's corridor runs through it,
    # so it is planted to its packing limit rather than to a round number
    "emberwood-core": dict(spacing=3.05, target=320, shrub=0.55),
    "valley-fringe": dict(spacing=4.4, target=60, shrub=0.40),
    "south-bank": dict(spacing=3.9, target=95, shrub=0.45),
    # rim.west = "forestwall": the wall itself is the stand
    "west-forestwall": dict(spacing=4.3, target=105, shrub=0.35),
}
MEADOW_CFG = dict(spacing=13.0, target=38, shrub=0.22)


def plant_region(col, F, zg, fr, suffix, seed=20260730):
    rng = np.random.RandomState(seed)
    V = O3.Veg("field")
    cell = 3.2
    grid = {}
    placed = []

    def free(x, y, sp):
        r = int(sp / cell) + 1
        c0, r0 = int(math.floor(x / cell)), int(math.floor(y / cell))
        for i in range(c0 - r, c0 + r + 1):
            for j in range(r0 - r, r0 + r + 1):
                for (ax, ay) in grid.get((i, j), ()):
                    if (x - ax) ** 2 + (y - ay) ** 2 < sp * sp:
                        return False
        return True

    def add(x, y, sp):
        grid.setdefault((int(math.floor(x / cell)), int(math.floor(y / cell))),
                        []).append((x, y))

    # keep-outs the map implies: settled ground, the moorage works, and the
    # TREELINE BREAK at the waystone (ch1 fiction: the road comes out of the wood
    # there, so the wood has to stop there)
    keepout = []
    for a in VM.REGION["townAnchors"]:
        bx, by = VM.w2b(a["pos"][0], a["pos"][1])
        keepout.append((float(bx), float(by), float(a["impressionRadius"]) * 0.92))
    mx, my = VM.w2b(*VM.LAND_W["dellhollow-moorage"][:2])
    keepout.append((float(mx), float(my), 13.0))
    wx_, wy_ = VM.w2b(*VM.LAND_W["waystone"][:2])
    keepout.append((float(wx_), float(wy_), 7.5))

    def candidates(mask):
        ii, jj = np.nonzero(mask)
        bx = zg.BX[ii, jj]
        by = zg.BY[ii, jj]
        o = rng.permutation(len(bx))
        return bx[o], by[o]

    def try_plant(bx, by, cfg, zone, edge_ok=True):
        n = 0
        sp = cfg["spacing"]
        for k in range(len(bx)):
            if n >= cfg["target"]:
                break
            x, y = float(bx[k]), float(by[k])
            x += float(rng.uniform(-0.5, 0.5))
            y += float(rng.uniform(-0.5, 0.5))
            if zg.type_at_blender(x, y) != zone:
                continue
            # THE ROAD MUST READ AS A CORRIDOR (H's lesson): in a stand the trees
            # come right up to the verge; in open meadow they stand well back, so
            # the corridor is a property of the wood and not of the whole tile.
            near = 2.45 if zone == "forest" else 5.5
            if float(F.road_dist(np.array([x]), np.array([y]))[0]) < near:
                continue
            dr, tr = F._river_dist(np.array([x]), np.array([y]))
            if float(dr[0]) - float(VM.water_halfwidth(tr)[0]) < 1.6:
                continue
            # 1.28, not the prototype's 0.85: the plateau skirt the emberwood grows
            # on runs 0.5-0.9, and a 0.85 cutoff left a bald band across the corridor
            if float(F.slope_at(np.array([x]), np.array([y]))[0]) > 1.28:
                continue
            if any((x - a) ** 2 + (y - b) ** 2 < r * r for a, b, r in keepout):
                continue
            # canopy interiors are the MASS's ground: specimen trees only at edges
            if getattr(zg, "canopy_int", None) is not None and \
                    bool(zg.wsample(zg.canopy_int.astype(float), x, y) > 0.5):
                continue
            if not free(x, y, sp):
                continue
            z = gh(F, zg, fr, x, y)
            fw = float(zg.wsample(zg.forest_w, x, y))
            interior = fw >= 0.72
            if zone == "meadow":
                key = "a"
            elif interior:
                key = "a" if rng.rand() < 0.80 else "c"
            else:
                key = "c" if rng.rand() < 0.74 else "a"
            s = float(rng.uniform(0.86, 1.26))
            O3.TREE_FN[key](V, x, y, z, s, float(rng.uniform(0, 6.283)), rng)
            if rng.rand() < cfg["shrub"]:
                a = rng.uniform(0, 6.283)
                dd = rng.uniform(1.3, 2.5)
                sx, sy = x + math.cos(a) * dd, y + math.sin(a) * dd
                # shrub (a) ALWAYS, whatever the tree is: the card-fringe shrubs
                # read as cabbages/agave in the foreground of the Emberbrook shot,
                # and understory is exactly where a card is seen flat from above
                O3.SHRUB_FN["a"](V, sx, sy, gh(F, zg, fr, sx, sy),
                                 float(rng.uniform(0.6, 1.0)),
                                 float(rng.uniform(0, 6.283)), rng)
            add(x, y, sp)
            placed.append((x, y, zone, key))
            n += 1
        return n

    byz = {}
    for sid, cfg in STAND_CFG.items():
        m = zg.stand.get(sid)
        if m is None or not m.any():
            continue
        bx, by = candidates(m)
        byz[sid] = try_plant(bx, by, cfg, "forest")
    mm = (zg.idx == O3.Z_MEADOW)
    bx, by = candidates(mm)
    byz["meadow-specimens"] = try_plant(bx, by, MEADOW_CFG, "meadow")

    n = V.n
    print("  planting: %d trees (a=%d c=%d), %d shrubs, %d cards, %d lobes"
          % (len(placed), n["a"], n["c"], n["shrub"], n["cards"], n["lobes"]))
    for k in sorted(byz):
        print("    %-18s %d" % (k, byz[k]))
    STATS["trees"] = len(placed)
    STATS["trees_by_stand"] = byz
    return V.finish(col, suffix), placed, byz


# =============================================================================
# CAMERAS
# =============================================================================
def add_cameras(sc, F, zg, fr, D, crest):
    cams = {}

    def cam(name, eye, aim, fov=42.0, fit="V"):
        nm = "cam_%s__%s" % (name, SUF)
        cd = bpy.data.cameras.new(nm)
        cd.sensor_fit = "VERTICAL" if fit == "V" else "HORIZONTAL"
        if fit == "V":
            cd.angle_y = math.radians(fov)
        else:
            cd.angle_x = math.radians(fov)
        cd.clip_start, cd.clip_end = 0.05, 2400.0
        ob = bpy.data.objects.new(nm, cd)
        sc.collection.objects.link(ob)
        ob.location = Vector(eye)
        ob.rotation_euler = (Vector(aim) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cams[name] = ob
        return ob

    # 1) LAYOUT — the whole region from the south, high enough to read the descent
    cam("overview", (-4.0, -212.0, 236.0), (10.0, 6.0, 4.0), fov=64.0, fit="H")
    # 2) EMBERBROOK — coming up the road to the town gate, character height + boom
    ex, ey, ez, etg = F.road_point(0.10)
    vx, vy = L.VILLAGE
    cam("emberbrook", (ex + etg[0] * 4.0 - etg[1] * 3.0,
                       ey + etg[1] * 4.0 + etg[0] * 3.0, ez + 9.0),
        (vx, vy, F.village_h + 1.2), fov=42.0)
    # 3) MIDVALLEY — the chase rig's own geometry (42deg, dist 34, pitch 0.61) on the
    #    open reach, so the shot predicts what the runtime camera actually shows
    mx, my, mz, mtg = F.road_point(0.55)
    d, pit = 34.0, 0.61
    cam("midvalley", (mx - mtg[0] * d * math.cos(pit), my - mtg[1] * d * math.cos(pit),
                      mz + 1.0 + d * math.sin(pit)), (mx, my, mz + 1.0), fov=42.0)
    # 4) GORGE — from the lit (south) side, across the notch at Dellhollow
    ax, ay = VM.w2b(*VM.DELLHOLLOW[:2])
    ctr, tg, nr, wl, hw, _ = gorge_frame(F, VM.DELLHOLLOW[0], VM.DELLHOLLOW[1])
    sgn = -1.0 if nr[1] > 0 else 1.0
    gx = float(ctr[0] + nr[0] * sgn * 30.0 - tg[0] * 12.0)
    gy = float(ctr[1] + nr[1] * sgn * 30.0 - tg[1] * 12.0)
    cam("gorge", (gx, gy, gh(F, zg, fr, gx, gy) + 15.0),
        (float(ctr[0]), float(ctr[1]), wl + 5.0), fov=46.0)
    # 5) MOORAGE — from the bank looking ALONG the water at the boat (finding 134)
    bx_, by_, bz_ = D["boat"]
    tx, ty = D["tg"]
    nx_, ny_ = D["nrm"]
    cx_, cy_ = D["ctr"]
    cam("moorage", (cx_ - tx * 15.0 + nx_ * 7.0, cy_ - ty * 15.0 + ny_ * 7.0,
                    D["wl"] + 7.5), (bx_ + tx * 1.0, by_ + ty * 1.0, bz_ + 0.5),
        fov=44.0)
    # 6) VISTA-RING — from inside the region looking out over the east escarpment at
    #    the ranges the PARENT map put there
    # stand INSIDE the region on the east escarpment and look out over its edge:
    # what this shot has to answer for is whether the world continues past the rim
    vx_, vy_ = VM.w2b(222.0, 100.0)
    cam("vistaring", (float(vx_), float(vy_), gh(F, zg, fr, vx_, vy_) + 13.0),
        (560.0, float(vy_) + 26.0, -34.0), fov=64.0, fit="H")
    return cams


# =============================================================================
def main():
    t_all = time.time()
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    print(VM.describe())
    t0 = time.time()
    F = VM.ValleyField()
    t_field = time.time() - t0
    print("field %dx%d  h %.1f..%.1f  emberbrook=%.2f gate=%.2f  (%.2fs)"
          % (L.NX, L.NY, F.H.min(), F.H.max(), F.village_h, F.clifftown_h, t_field))

    t0 = time.time()
    can_d, can_n = O3.canopy_maps()
    bark_d, bark_n = O3.bark_maps()
    atlas = O3.leafmass_atlas()
    veg_maps = dict(can_d=can_d, can_n=can_n, bark_d=bark_d, bark_n=bark_n, atlas=atlas)
    t_assets = time.time() - t0
    print("veg maps ready (%.1fs, one-off shared assets)" % t_assets)

    t_tile = time.time()
    sc = bpy.data.scenes[0]
    sc.name = "valley"
    col = sc.collection
    B.dusk_rig(sc, F, STYLE)
    # a second warm key in the gorge: Dellhollow's mills and windows are the only
    # light down there, and the dusk rig's single hearth is up on the plateau
    dl = bpy.data.lights.new("hearth_dellhollow", "POINT")
    dl.energy, dl.color, dl.shadow_soft_size = 420.0, (1.0, 0.66, 0.32), 1.2
    dob = bpy.data.objects.new("hearth_dellhollow", dl)
    dbx, dby = VM.w2b(*VM.DELLHOLLOW[:2])
    dob.location = (float(dbx), float(dby), 6.5)
    col.objects.link(dob)

    mats = {"matte": B.new_mat("ow_%s_matte" % STYLE, rough=0.9),
            "water": B.new_mat("ow_%s_water" % STYLE, rough=0.28, alpha=0.82, blend=True),
            "emit": B.new_mat("ow_%s_emit" % STYLE, rough=0.6, emit=srgb("ff9f38"),
                              emit_str=9.0),
            "mist": B.new_mat("ow_%s_mist" % STYLE, rough=1.0, alpha=0.2, blend=True)}
    for k in ("water", "mist"):
        mats[k].show_transparent_back = False
    group = dict(B.GROUP)

    # ---- the zone grid -----------------------------------------------------
    fr = VM.moorage_frame(F)
    t0 = time.time()
    zg = VM.ValleyZoneGrid(F, fr)
    t_zone = time.time() - t0
    cov = zg.coverage()
    print("zone grid %dx%d cell=%.2fu (%.2fs)  %s"
          % (zg.cols, zg.rows, zg.cell, t_zone,
             " ".join("%s=%.1f%%" % (k, v) for k, v in cov.items())))
    print("  thresholds %s  override cells %d" % (zg.thresh, zg.n_override))

    made = {}

    # ---- the dock + boat_tar, solved BEFORE the terrain (F2's order) --------
    cls = dict(hull=TAR, wood=WOOD, dark=TAR, canvas=CANVAS, rope=ROPE, lamp=LAMP)
    deck = B.Prop("walk_dock")
    dprops = B.Prop("dock_props")
    D = O2.build_dock(F, deck, dprops, cls, fr, boat_rig="mast")
    # corridors the crag treatment must not touch
    O3.FLAT_PATHS[:] = [(D["root"][0], D["root"][1], D["ctr"][0], D["ctr"][1], 4.0, 9.0)]
    for (a, b) in VM.ROAD_SPANS:
        O3.FLAT_PATHS.append((float(F.road[a, 0]), float(F.road[a, 1]),
                              float(F.road[b, 0]), float(F.road[b, 1]), 4.0, 9.0))

    # ---- terrain -----------------------------------------------------------
    t0 = time.time()
    ground, skirt, fcrag = O3.build_terrain(col, F, zg, fr)
    t_ter = time.time() - t0
    for ob, key in ((ground, "ground"), (skirt, "skirt")):
        ob.name = "%s__%s" % (ob.name, SUF)
        ob.data.name = ob.name
        made[key] = ob
    print("  terrain built in %.1fs" % t_ter)

    # ---- ribbons, towns, props --------------------------------------------
    made["water"] = build_water(col, F)
    made["road"] = build_road(col, F)
    cw = build_causeway(col, F, zg, fr)
    if cw is not None:
        made["causeway"] = cw
    made["green"] = build_emberbrook_green(col, F, zg, fr)
    made["emberbrook"] = build_emberbrook(col, F, zg, fr)
    dh, crest = build_dellhollow(col, F, zg, fr)
    made["dellhollow"] = dh
    dc = build_dam_crest(col, F, zg, fr, crest)
    if dc is not None:
        made["damcrest"] = dc
    made["portals"] = build_portals(col, F, zg, fr)
    for k_, ob_ in zip(("canopy_a", "canopy_b", "canopy_c"), build_canopy(col, F, zg, fr)):
        made[k_] = ob_                     # own vcol material; excluded from the class passes
    made["props"] = build_props(col, F, zg, fr)
    made["fx"] = build_vista(col, F)

    # ---- the moorage: basin water, jetty, boat, spur -----------------------
    do = deck.finish(col)
    do.name = do.data.name = "walk_dock"
    po = dprops.finish(col)
    po.name = po.data.name = "boat_tar"
    made["dock"], made["boat"] = do, po
    wp = B.Prop("water_pool")
    O2.pool_water(wp, WATER, fr)
    made["pool"] = wp.finish(col)
    made["dockpath"] = build_moorage_spur(col, F, zg, fr, D["root"])

    # ---- 1.45u scale references (renders only; stripped at export) ---------
    rp = B.Prop("ref_char")
    px, py, pz, _ = F.road_point(0.55)
    qx, qy = L.VILLAGE
    qz = F.village_h
    ex, ey = float(F.road[-1, 0]), float(F.road[-1, 1])
    ez = float(F.road_h[-1])
    for (ox, oy, oz) in ((px, py, pz), (qx + 4.4, qy, qz), (ex, ey, ez),
                         (D["head"][0], D["head"][1], D["deck_z"])):
        rp.cone(PEAK, (ox, oy, oz + 0.72), 0.26, 0.26, 1.05, seg=10)
        rp.ico(PEAK, (ox, oy, oz + 1.24), (0.26, 0.26, 0.26), subd=1)
        rp.ico(PEAK, (ox, oy, oz + 0.21), (0.26, 0.26, 0.21), subd=1)
    made["ref"] = rp.finish(col)

    # ---- trees -------------------------------------------------------------
    t0 = time.time()
    field, placed, byzone = plant_region(col, F, zg, fr, SUF)
    t_veg = time.time() - t0
    veg_keys = []
    for k, o in field.items():
        made["veg_" + k] = o
        veg_keys.append("veg_" + k)
    print("  planting took %.1fs" % t_veg)

    # ---- clearance safety net ---------------------------------------------
    for key in ("road", "green", "dockpath", "dock", "damcrest"):
        if key not in made:
            continue
        n = O3.conform_ribbon(made[key], F, zg, fr)
        if n:
            print("  conform %-10s lifted %d verts clear of the treated ground"
                  % (key, n))

    # ---- colours, shading, materials --------------------------------------
    PROPKEYS = ([k for k in ("skirt", "water", "road", "causeway", "green",
                             "emberbrook", "dellhollow", "damcrest", "portals",
                             "props", "fx", "dock", "boat", "pool", "dockpath",
                             "ref") if k in made] + veg_keys)
    for i, key in enumerate(PROPKEYS):
        jit = 0.10 if key.startswith("veg_") else 0.055
        made[key + "_cls"] = B.write_prop_colors(made[key], STYLE, True, jit, seed=41 + i)
    SOFT = {"water", "pool", "props", "green", "fx"} | set(veg_keys)
    for key in PROPKEYS:
        ob = made[key]
        v = key in SOFT
        ob.data.polygons.foreach_set("use_smooth", [v] * len(ob.data.polygons))
        ob.data.update()

    pm = B3.props_materials_f2(made, mats, group, veg_maps)
    UVKEYS = [k for k in ("emberbrook", "dellhollow", "portals", "props", "damcrest",
                          "causeway", "boat", "dock", "skirt", "fx") if k in made]
    UVKEYS += [k for k in veg_keys if not k.endswith("_cards")]
    for key in UVKEYS:
        scale = 1.35 if key.startswith("veg_") and "trunks" not in key else 1.0
        B3.vec_planar_uv(made[key], 1.0 / scale)
    gains = {g: m["vcol_gain"] for g, m in pm.items()}
    for key in UVKEYS:
        B3.apply_class_gains(made[key], made[key + "_cls"], group, gains)
    for key in PROPKEYS:
        ob = made[key]
        if ob.data.materials:
            continue
        B2.assign_slots2(ob, mats, made[key + "_cls"], group)
    B3.terrain_pbr_f2(made, F, zg, fcrag)

    # ---- the QA-only zone overlay -----------------------------------------
    ovl = O3.build_zone_overlay(col, F, zg, fr)
    ovl.name = ovl.data.name = "qa_zone_overlay__" + SUF
    om = B.new_mat("ow_%s_zoneovl" % STYLE, rough=1.0, alpha=0.62, blend=True)
    nt = om.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "Col"
    nt.links.new(ca.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    om.show_transparent_back = False
    ovl.data.materials.append(om)

    # ---- cameras + render conventions -------------------------------------
    cams = add_cameras(sc, F, zg, fr, D, crest)
    sc.camera = cams["overview"]
    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.resolution_percentage = 100
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
        sc.eevee.shadow_pool_size = 1024
    except Exception:
        pass

    t_tile = time.time() - t_tile

    # ---- zones.json + the build record ------------------------------------
    os.makedirs(BUNDLE, exist_ok=True)
    zp = os.path.join(BUNDLE, "zones.json")
    zg.write(zp)
    print("zones.json -> %s (%.1f kB)" % (zp, os.path.getsize(zp) / 1e3))

    tris = sum(sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
               for o in sc.objects if o.type == "MESH" and not o.name.startswith("qa_"))
    meshes = len([o for o in sc.objects if o.type == "MESH"])
    print("tile totals: %d meshes, %d tris (excl. QA overlay)" % (meshes, tris))

    qa = os.path.join(ROOT, "docs/qa/overworld")
    os.makedirs(qa, exist_ok=True)
    rec = dict(STATS)
    rec.update(dict(region=VM.REGION_ID, tile=[VM.TILE_W, VM.TILE_H], step=VM.STEP,
                    lattice=[L.NX, L.NY], build_s=round(t_tile, 2),
                    field_s=round(t_field, 2), zone_s=round(t_zone, 3),
                    terrain_s=round(t_ter, 2), veg_s=round(t_veg, 2),
                    veg_assets_oneoff_s=round(t_assets, 2), meshes=meshes, tris=tris,
                    zone_coverage_pct={k: round(v, 2) for k, v in cov.items()},
                    zone_cells=zg.cols * zg.rows,
                    road_pushed_stations=len(VM.ROAD_PUSH),
                    road_spans=[[int(a), int(b)] for a, b in VM.ROAD_SPANS],
                    h_range=[round(float(F.H.min()), 2), round(float(F.H.max()), 2)]))
    json.dump(rec, open(os.path.join(qa, "valley_build.json"), "w"), indent=1,
              sort_keys=True)

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("SAVED %s  (%.1fs total, %.1fs tile)" % (OUT_BLEND, time.time() - t_all, t_tile))


if __name__ == "__main__":
    main()
