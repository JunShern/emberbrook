"""owdraft_build.py — BLOCKOUT of the hanging-valley PROPOSAL, as a parallel scene.

  Blender --python-exit-code 1 -b --factory-startup -P tools/owdraft_build.py

  *** PROPOSAL DRAFT. NOT CANON. ***
  Touches NOTHING shipped: it reads only docs/qa/overworld-draft/
  embercorridor-draft.region.json through tools/owdraft_lib.py, and writes only
  tools/blends/owdraft-embercorridor.blend and the ow-embercorridor-draft bundle.
  The ow-valley scene, its blend, its map inputs and valley_*.py are untouched.

Pattern borrowed from the ow-valley loop (map JSON -> analytic field -> deterministic
builder -> bundle -> renders), NOT its code: valley_map monkeypatches overworld_lib
against the RATIFIED map files, and the whole point of this draft is that it
disagrees with them.  What is here is blockout massing only — terrain, water with
the fall real, road ribbon, two town impressions, the gate in its notch, scale
capsules.  No dressing, no vegetation art, no cameras solved.  Cheap to discard.

Coordinates: draft world frame [0,300] x [0,240]; blender is centred, bx = wx-150,
by = wy-120, bz = h.  Runtime would be +x east / +z south: rx = bx, rz = -by.
"""
import bmesh
import bpy
import json
import math
import os
import random
import sys

import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import owdraft_lib as DL

D = DL.D
ROOT = DL.ROOT
OUT_BLEND = os.path.join(ROOT, "tools/blends/owdraft-embercorridor.blend")
SEED = DL.SEED
HOUSE_RIDGE = 1.6                    # the scale contract beside a 1.45u character


def b(x, y):
    """draft-world -> blender xy"""
    return (x - DL.CX, y - DL.CY)


# --------------------------------------------------------------------- materials
def srgb(c):
    return tuple((v / 255.0) ** 2.2 for v in c) + (1.0,)


MATS = {}


def mat(name, rgb, rough=0.85, metal=0.0, alpha=1.0, emit=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(rgb)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = srgb(rgb)
        bsdf.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    MATS[name] = m
    return m


def vcol_mat(name):
    """terrain material: vertex colour straight into base colour, so the blockout
    carries its own legend (farm gold / forest green / crag grey / meadow)."""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.92
    a = nt.nodes.new("ShaderNodeVertexColor")
    a.layer_name = "Col"
    a.location = (-320, 200)
    nt.links.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    MATS[name] = m
    return m


def newobj(name, me, coll=None):
    o = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


# ----------------------------------------------------------------------- terrain
def build_terrain(F, sc):
    step = DL.STEP
    nx = int(round(DL.TILE_W / step)) + 1
    ny = int(round(DL.TILE_H / step)) + 1
    wx = np.linspace(0.0, DL.TILE_W, nx)
    wy = np.linspace(0.0, DL.TILE_H, ny)
    GX, GY = np.meshgrid(wx, wy)
    H = F.height(GX, GY)

    verts = np.stack([(GX - DL.CX).ravel(), (GY - DL.CY).ravel(), H.ravel()], -1)
    idx = np.arange(nx * ny).reshape(ny, nx)
    a = idx[:-1, :-1].ravel()
    c = idx[:-1, 1:].ravel()
    d = idx[1:, 1:].ravel()
    e = idx[1:, :-1].ravel()
    faces = np.stack([a, c, d, e], -1)

    me = bpy.data.meshes.new("terrain__draft")
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.validate()

    # vertex colour from the zone grid + a height wash
    zg, cell, cols, rows = DL.zone_grid(F, 1.25)
    ci = np.clip((GY.ravel() / cell).astype(int), 0, rows - 1)
    cj = np.clip((GX.ravel() / cell).astype(int), 0, cols - 1)
    zt = zg[ci, cj]
    col = np.zeros((verts.shape[0], 4))
    col[:, 3] = 1.0
    palette = {0: (150, 176, 96), 1: (52, 88, 52), 2: (146, 132, 118),
               3: (198, 173, 126), 4: (58, 110, 138), 5: (198, 174, 84)}
    for k, rgb in palette.items():
        m = zt == k
        if m.any():
            col[m, :3] = [(v / 255.0) ** 2.2 for v in rgb]
    # high ground pales towards rock, so the arms read as arms
    hv = np.clip((H.ravel() - 34.0) / 30.0, 0, 1)[:, None]
    col[:, :3] = col[:, :3] * (1 - hv * 0.72) + np.array([0.42, 0.39, 0.37]) * hv * 0.72

    # SKIRT: drop the tile's rim to a base plane, so the draft reads as ground and
    # not as a floating slab (the shipped tiles get this from their vista ring).
    base_z = float(H.min()) - 26.0
    rim = (list(idx[0, :]) + list(idx[:, -1]) + list(idx[-1, ::-1]) + list(idx[::-1, 0]))
    me2 = bpy.data.meshes.new("terrain_skirt__draft")
    sv, sf = [], []
    for a_, b_ in zip(rim, rim[1:]):
        base = len(sv)
        sv += [verts[a_].tolist(), verts[b_].tolist(),
               [verts[b_][0], verts[b_][1], base_z], [verts[a_][0], verts[a_][1], base_z]]
        sf.append((base, base + 1, base + 2, base + 3))
    me2.from_pydata(sv, [], sf)
    me2.validate()
    me2.materials.append(mat("m_skirt__draft", (104, 92, 84), rough=0.95))
    newobj("terrain_skirt__draft", me2)

    lay = me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    lay.data.foreach_set("color", col.ravel())
    me.materials.append(vcol_mat("m_terrain__draft"))
    me.shade_smooth()
    o = newobj("terrain__draft", me)
    return o, H


def build_water(F, sc):
    """The river as a ribbon at its own falling water level, plus a vertical sheet
    at every step > 1.2u — the FALL is the thing being proposed, so it is real
    geometry, not a texture."""
    rp = D["river"]["points"]
    P = np.array([(p[0], p[1]) for p in rp], float)
    Wd = np.array([p[3] for p in rp], float)
    Hh = np.array([p[2] for p in rp], float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = int(cum[-1] / 0.8)
    t = np.linspace(0, cum[-1], n)
    sx = np.interp(t, cum, P[:, 0])
    sy = np.interp(t, cum, P[:, 1])
    sw = np.interp(t, cum, Wd)
    sh = np.interp(t, cum, Hh)

    dx = np.gradient(sx)
    dy = np.gradient(sy)
    ln = np.hypot(dx, dy)
    nx_, ny_ = -dy / ln, dx / ln

    verts, faces = [], []
    for i in range(n):
        hw = sw[i] * 0.5
        for s in (-1, 1):
            X, Y = b(sx[i] + nx_[i] * hw * s, sy[i] + ny_[i] * hw * s)
            verts.append((X, Y, sh[i]))
    for i in range(n - 1):
        a0, a1 = 2 * i, 2 * i + 1
        faces.append((a0, a1, a1 + 2, a0 + 2))
    # the falling faces: wherever the level steps down, close it with a curtain
    for i in range(n - 1):
        if sh[i] - sh[i + 1] > 0.12:
            a0, a1 = 2 * i, 2 * i + 1
            faces.append((a0, a0 + 2, a1 + 2, a1))

    me = bpy.data.meshes.new("water_river__draft")
    me.from_pydata(verts, [], faces)
    me.validate()
    me.materials.append(mat("m_water__draft", (66, 128, 156), rough=0.14, alpha=0.86))
    me.shade_smooth()
    return newobj("water_river__draft", me)


def build_road(F, sc):
    rp = F.roadpts                      # the SOLVED course, not the authored one
    P = np.array([(p[0], p[1]) for p in rp], float)
    Z = np.array([p[2] for p in rp], float)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = int(cum[-1] / 0.7)
    t = np.linspace(0, cum[-1], n)
    sx, sy, sz = (np.interp(t, cum, P[:, 0]), np.interp(t, cum, P[:, 1]),
                  np.interp(t, cum, Z))
    dx, dy = np.gradient(sx), np.gradient(sy)
    ln = np.hypot(dx, dy)
    nx_, ny_ = -dy / ln, dx / ln
    hw = float(D["road"]["width"]) * 0.5
    verts, faces = [], []
    for i in range(n):
        for s in (-1, 1):
            X, Y = b(sx[i] + nx_[i] * hw * s, sy[i] + ny_[i] * hw * s)
            verts.append((X, Y, sz[i] + 0.06))
    for i in range(n - 1):
        faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    me = bpy.data.meshes.new("walk_road__draft")
    me.from_pydata(verts, [], faces)
    me.validate()
    me.materials.append(mat("m_road__draft", (206, 182, 138), rough=0.95))
    return newobj("walk_road__draft", me)


# ------------------------------------------------------------------- prop helper
class Prop:
    """accumulate boxes/prisms into ONE mesh per class — the same trick the shipped
    builders use to keep an overworld tile to a few dozen objects."""

    def __init__(self, name, material):
        self.name, self.mat = name, material
        self.v, self.f = [], []

    def box(self, cx, cy, cz, sx, sy, sz, rot=0.0):
        c, s = math.cos(rot), math.sin(rot)
        base = len(self.v)
        for ux, uy, uz in ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0),
                           (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            X, Y = ux * sx * .5, uy * sy * .5
            self.v.append((cx + X * c - Y * s, cy + X * s + Y * c, cz + uz * sz))
        for q in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
                  (2, 6, 7, 3), (3, 7, 4, 0)):
            self.f.append(tuple(base + i for i in q))

    def gable(self, cx, cy, cz, sx, sy, wall, ridge, rot=0.0):
        self.box(cx, cy, cz, sx, sy, wall, rot)
        c, s = math.cos(rot), math.sin(rot)
        base = len(self.v)
        pts = [(-sx / 2, -sy / 2, wall), (sx / 2, -sy / 2, wall),
               (sx / 2, sy / 2, wall), (-sx / 2, sy / 2, wall),
               (0, -sy / 2, wall + ridge), (0, sy / 2, wall + ridge)]
        for X, Y, Z in pts:
            self.v.append((cx + X * c - Y * s, cy + X * s + Y * c, cz + Z))
        for q in ((0, 1, 4), (2, 3, 5), (0, 4, 5, 3), (1, 2, 5, 4)):
            self.f.append(tuple(base + i for i in q))

    def emit(self):
        if not self.v:
            return None
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.validate()
        me.materials.append(self.mat)
        return newobj(self.name, me)


# ------------------------------------------------------------------ town massing
def build_emberbrook(F):
    lm = [l for l in D["landmarks"] if l["id"] == "emberbrook"][0]
    cx, cy, _ = lm["pos"]
    r = lm["r"]
    rng = random.Random(SEED + 11)
    walls = Prop("lm_emberbrook_walls__draft", mat("m_wall__draft", (222, 208, 180)))
    roofs = Prop("lm_emberbrook_roofs__draft", mat("m_roof__draft", (172, 98, 66)))
    fields = Prop("lm_emberbrook_fields__draft", mat("m_field__draft", (196, 172, 82)))
    lamps = Prop("lm_emberbrook_light__draft",
                 mat("m_emit__draft", (255, 206, 128), emit=6.0))

    placed = []
    for _ in range(240):
        if len(placed) >= 46:
            break
        a = rng.uniform(0, math.tau)
        d = r * math.sqrt(rng.uniform(0.02, 1.0))
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        if F.riverdist(x, y) < 5.0 or F.roaddist(x, y) < 1.6:
            continue
        if any((x - p[0]) ** 2 + (y - p[1]) ** 2 < 9.0 for p in placed):
            continue
        placed.append((x, y))
        z = float(F.height(x, y))
        w, dp = rng.uniform(1.5, 2.4), rng.uniform(1.9, 3.0)
        rot = rng.uniform(0, math.tau)
        X, Y = b(x, y)
        walls.box(X, Y, z, w, dp, HOUSE_RIDGE * 0.62, rot)
        roofs.gable(X, Y, z + HOUSE_RIDGE * 0.62, w * 1.16, dp * 1.16, 0.01,
                    HOUSE_RIDGE * 0.5, rot)
    # the Heartlight: the one warm point the village is built around
    hx, hy = cx + 1.5, cy + 1.0
    HX, HY = b(hx, hy)
    lamps.box(HX, HY, float(F.height(hx, hy)) + 1.1, 0.7, 0.7, 0.9)

    # field strips — the hanging valley is FARMED, and that has to be visible
    for st in D["farmland"]["stamps"]:
        poly = np.array(st["poly"], float)
        x0, y0 = poly.min(0)
        x1, y1 = poly.max(0)
        for gx in np.arange(x0, x1, 5.5):
            for gy in np.arange(y0, y1, 7.0):
                px, py = gx + 2.6, gy + 3.2
                if not DL.polymask(poly, np.array([[px]]), np.array([[py]]))[0, 0]:
                    continue
                if F.riverdist(px, py) < 4.0 or F.roaddist(px, py) < 2.2:
                    continue
                X, Y = b(px, py)
                fields.box(X, Y, float(F.height(px, py)) - 0.05, 4.6, 6.0, 0.18,
                           rng.uniform(0, 0.5))
    return [o for o in (walls.emit(), roofs.emit(), fields.emit(), lamps.emit()) if o]


def build_dellhollow(F):
    lm = [l for l in D["landmarks"] if l["id"] == "dellhollow"][0]
    cx, cy, _ = lm["pos"]
    rng = random.Random(SEED + 23)
    walls = Prop("lm_dellhollow_walls__draft", mat("m_dwall__draft", (198, 190, 178)))
    roofs = Prop("lm_dellhollow_roofs__draft", mat("m_droof__draft", (128, 84, 62)))
    stone = Prop("lm_dellhollow_works__draft", mat("m_stone__draft", (96, 92, 88)))
    lamps = Prop("lm_dellhollow_light__draft",
                 mat("m_emit__draft", (255, 206, 128), emit=6.0))

    # stepped clusters clinging to the RIGHT bank between the rim road and the water
    placed = []
    for _ in range(600):
        if len(placed) >= 40:
            break
        x = cx + rng.uniform(-17, 15)
        y = cy + rng.uniform(-13, 13)
        dr = float(F.riverdist(x, y))
        if not (4.0 < dr < 20.0):
            continue
        z = float(F.height(x, y))
        if not (0.5 < z < 15.0):
            continue
        if any((x - p[0]) ** 2 + (y - p[1]) ** 2 < 6.0 for p in placed):
            continue
        placed.append((x, y))
        w, dp = rng.uniform(1.6, 2.6), rng.uniform(2.0, 3.2)
        rot = rng.uniform(0, math.tau)
        X, Y = b(x, y)
        walls.box(X, Y, z, w, dp, HOUSE_RIDGE * 0.9, rot)
        roofs.gable(X, Y, z + HOUSE_RIDGE * 0.9, w * 1.16, dp * 1.16, 0.01,
                    HOUSE_RIDGE * 0.5, rot)
        if rng.random() < 0.45:
            lamps.box(X, Y + dp * 0.8, z + 1.4, 0.28, 0.28, 0.32)

    # the locks: dams across the channel at the two river steps the town exists for
    rp = D["river"]["points"]
    for i in range(len(rp) - 1):
        drop = rp[i][2] - rp[i + 1][2]
        if drop < 2.0 or rp[i][1] < cy - 22 or rp[i][1] > cy + 22:
            continue
        ax, ay = rp[i][0], rp[i][1]
        bx2, by2 = rp[i + 1][0], rp[i + 1][1]
        mx, my = (ax + bx2) / 2, (ay + by2) / 2
        ang = math.atan2(by2 - ay, bx2 - ax)
        X, Y = b(mx, my)
        stone.box(X, Y, rp[i + 1][2] - 0.6, 2.4, rp[i][3] + 6.0, drop + 1.2, ang)
        for k in (-1, 0, 1):                       # the breast wheels on its face
            stone.box(X + math.cos(ang) * 1.6, Y + math.sin(ang) * 1.6 + k * 3.0,
                      rp[i + 1][2] + 0.2, 1.0, 1.0, 1.6, ang)
    return [o for o in (walls.emit(), roofs.emit(), stone.emit(), lamps.emit()) if o]


def build_gate(F):
    """The Old Gate spanning the notch. Follows the CURRENT map ruling
    (public/townmap/emberbrook.map.json, sigil-gate, refinement 2, 2026-08-01):
    ONE wide structure across the whole pinch, the river running directly parallel
    to the road and passing UNDER it — but the water passage is NOT an arch,
    "arches are for humans". A low culvert grate sits at water level only, with
    plain coursed masonry above it; only the road's doorway is arched.
    Massing at overworld impression scale; the concept art is the design."""
    lm = [l for l in D["landmarks"] if l["id"] == "old-gate"][0]
    gx, gy, gz = lm["pos"]
    stone = Prop("lm_oldgate__draft", mat("m_gatestone__draft", (176, 164, 146)))
    bars = Prop("lm_oldgate_grate__draft", mat("m_bars__draft", (52, 48, 44)))

    rp = D["river"]["points"]
    i = min(range(len(rp)), key=lambda k: (rp[k][0] - gx) ** 2 + (rp[k][1] - gy) ** 2)
    fdx = rp[min(i + 1, len(rp) - 1)][0] - rp[max(i - 1, 0)][0]
    fdy = rp[min(i + 1, len(rp) - 1)][1] - rp[max(i - 1, 0)][1]
    fl = math.hypot(fdx, fdy) or 1.0
    ax, ay = fdy / fl, -fdx / fl              # the wall's axis = RIGHT of the flow
    ang = math.atan2(ay, ax)
    X0, Y0 = b(gx, gy)
    wz = float(F.water(gx, gy))
    top = gz + 3.4
    chan = rp[i][3] * 0.5 + 0.4               # the water passage's half width

    def seg(u0, u1, z0, z1, prop=stone):
        c = (u0 + u1) * 0.5
        prop.box(X0 + ax * c, Y0 + ay * c, z0, abs(u1 - u0), 2.0, z1 - z0, ang)

    door0, door1 = chan + 1.4, chan + 4.6     # the road's doorway, beside the water
    seg(-8.0, -chan, wz - 3.0, top)           # wall, far side
    seg(chan, door0, wz - 3.0, top)           # pier between water and road
    seg(door1, 8.0, wz - 3.0, top)            # wall, near side
    seg(-chan, chan, wz + 1.1, top)           # PLAIN MASONRY over the water passage
    seg(door0, door1, gz + 2.2, top)          # lintel over the road doorway
    # the grate: low, at water level only, slightly taller than the waterline
    n = max(3, int(chan * 2 / 0.55))
    for k in range(n):
        u = -chan + (k + 0.5) * (2 * chan / n)
        bars.box(X0 + ax * u, Y0 + ay * u, wz - 0.9, 0.20, 1.9, 2.0, ang)
    return [o for o in (stone.emit(), bars.emit()) if o]


def build_bridge(F):
    """The village bridge — the ONE crossing. Placed where the map puts it, sized to
    the channel it actually spans rather than to taste: deck across the wetted width
    plus an abutment on each bank."""
    lm = [l for l in D["landmarks"] if l["id"] == "village-bridge"]
    if not lm:
        return []
    bx, by, bz = lm[0]["pos"]
    deck = Prop("lm_village_bridge__draft", mat("m_deckwood__draft", (128, 96, 66)))
    piers = Prop("lm_bridge_piers__draft", mat("m_pier__draft", (168, 160, 146)))

    # the deck follows the ROAD, not the river's perpendicular: the first version
    # squared the deck to the flow and the carriageway crossed it at an angle.
    rd = F.roadpts
    i = min(range(len(rd)), key=lambda k: (rd[k][0] - bx) ** 2 + (rd[k][1] - by) ** 2)
    bx, by = rd[i][0], rd[i][1]
    bz = rd[i][2]
    a0, a1 = rd[max(i - 2, 0)], rd[min(i + 2, len(rd) - 1)]
    ang = math.atan2(a1[1] - a0[1], a1[0] - a0[0])
    w = float(F.riverwidth(bx, by))
    wz = float(F.water(bx, by))
    X, Y = b(bx, by)
    span = w + 4.6
    deck.box(X, Y, bz - 0.34, span, 2.9, 0.36, ang)
    for s_ in (-1, 1):                             # parapets
        deck.box(X + math.cos(ang + math.pi / 2) * 1.15 * s_,
                 Y + math.sin(ang + math.pi / 2) * 1.15 * s_,
                 bz + 0.04, span, 0.26, 0.42, ang)
    for s_ in (-1, 1):                             # abutments, on the banks
        u = (w * 0.5 + 1.3) * s_
        piers.box(X + math.cos(ang) * u, Y + math.sin(ang) * u,
                  wz - 1.4, 2.0, 3.0, bz - wz + 1.1, ang)
    return [o for o in (deck.emit(), piers.emit()) if o]


def build_canopy(F):
    """Whisperwood as canopy MASS (the shipped region's representation), scattered
    on the forest stamps and batched — legibility of 'the wood wraps everything'."""
    rng = random.Random(SEED + 41)
    bm = bmesh.new()
    unit = bmesh.new()
    bmesh.ops.create_icosphere(unit, subdivisions=1, radius=1.0)
    ulist = [v.co.copy() for v in unit.verts]
    ufaces = [[unit.verts[:].index(v) for v in f.verts] for f in unit.faces]
    unit.free()

    # USER RULING (this round): no bare collar between the village and the wood — the
    # trees run right up to the settled edge and take every unclaimed acre.  So the
    # canopy is a COMPLEMENT: it fills the stamps except where something else has a
    # claim (fields, the village itself, the lanes, the water), rather than being a
    # shape that politely stops short.
    farm = [np.array(st["poly"], float) for st in D["farmland"]["stamps"]]
    towns = [(l["pos"][0], l["pos"][1], l["r"]) for l in D["landmarks"]
             if l["class"] == "town"]

    def claimed(x, y):
        if F.roaddist(x, y) < 3.2:
            return True
        if F.riverdist(x, y) < F.riverwidth(x, y) * 0.5 + 1.5:
            return True
        for tx, ty, tr in towns:
            if (x - tx) ** 2 + (y - ty) ** 2 < (tr * 0.94) ** 2:
                return True
        for poly in farm:
            if DL.polymask(poly, np.array([[x]]), np.array([[y]]))[0, 0]:
                return True
        return False

    verts, faces = [], []
    for st in D["forests"]:
        poly = np.array(st["stamp"], float)
        x0, y0 = poly.min(0)
        x1, y1 = poly.max(0)
        area = (x1 - x0) * (y1 - y0)
        for _ in range(int(area * 0.30)):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if not DL.polymask(poly, np.array([[x]]), np.array([[y]]))[0, 0]:
                continue
            if claimed(x, y):
                continue
            z = float(F.height(x, y))
            # WHERE THE WOOD STOPS needs a reason. Density falls off to a treeline,
            # and a noise term ragged-edges the stamp so its boundary never reads as
            # the straight line it actually is.
            tl = D.get("treeline", {})
            t0, t1 = float(tl.get("from", 40.0)), float(tl.get("to", 53.0))
            keep = 1.0 - max(0.0, min(1.0, (z - t0) / (t1 - t0)))
            keep *= 0.55 + float(tl.get("edgeNoise", 0.85)) * (
                DL._vnoise(np.array([x]), np.array([y]), 1 / 9.0, DL.SEED + 61)[0] + 0.5)
            if rng.random() > keep:
                continue
            r = rng.uniform(1.3, 2.4)
            X, Y = b(x, y)
            base = len(verts)
            for co in ulist:
                verts.append((X + co.x * r, Y + co.y * r, z + r * 0.72 + co.z * r * 0.72))
            for f in ufaces:
                faces.append(tuple(base + i for i in f))
    bm.free()
    me = bpy.data.meshes.new("veg_canopy__draft")
    me.from_pydata(verts, [], faces)
    me.validate()
    me.materials.append(mat("m_canopy__draft", (46, 84, 48), rough=0.95))
    me.shade_smooth()
    return newobj("veg_canopy__draft", me)


def build_refchars(F):
    """1.45u capsules at the three places the argument is about — the only honest
    way to read an overworld's vertical."""
    p = Prop("ref_char__draft", mat("m_ref__draft", (240, 240, 250), emit=0.8))
    for lid in ("emberbrook", "old-gate", "dellhollow", "pocket-terrace"):
        lm = [l for l in D["landmarks"] if l["id"] == lid][0]
        x, y = lm["pos"][0], lm["pos"][1]
        X, Y = b(x, y)
        p.box(X + 2.0, Y, float(F.height(x + 2.0, y)), 0.5, 0.5, DL.CHAR_H)
    return [o for o in (p.emit(),) if o]


# ------------------------------------------------------------------------ camera
def add_camera(name, pos, target, lens, sc, F=None, snap=False, lift=0.0):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start, cam.clip_end = 0.5, 2000.0
    o = bpy.data.objects.new(name, cam)
    sc.collection.objects.link(o)
    px, py = b(pos[0], pos[1])
    tx, ty = b(target[0], target[1])
    pz = (float(F.height(pos[0], pos[1])) + 1.5 + lift) if (snap and F) else pos[2]
    P = Vector((px, py, pz))
    T = Vector((tx, ty, target[2]))
    o.location = P
    o.rotation_euler = (T - P).to_track_quat("-Z", "Y").to_euler()
    return o


def main():
    t0 = __import__("time").time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.name = "embercorridor"
    sc.unit_settings.system = "METRIC"

    F = DL.DraftField()
    terrain, H = build_terrain(F, sc)
    build_water(F, sc)
    build_road(F, sc)
    build_emberbrook(F)
    build_dellhollow(F)
    build_gate(F)
    build_bridge(F)
    build_canopy(F)
    build_refchars(F)

    # ---- light: a low warm sun, the look pillar's golden hour, plus enough sky to
    # read the gorge floor (a geography draft that is too dark to judge is no draft)
    sun_d = bpy.data.lights.new("sun__draft", type="SUN")
    sun_d.energy = 4.6
    sun_d.angle = math.radians(2.0)
    sun_d.color = (1.0, 0.86, 0.68)
    sun = bpy.data.objects.new("sun__draft", sun_d)
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(52), 0.0, math.radians(-24))

    world = bpy.data.worlds.new("w__draft")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = srgb((124, 148, 176))
    bg.inputs[1].default_value = 1.15
    sc.world = world

    for nm, c in D["cameras"].items():
        if nm.startswith("_"):
            continue
        add_camera("cam_%s__draft" % nm, c["pos"], c["target"], c["lens"], sc,
                   F=F, snap=c.get("snapToGround", False),
                   lift=float(c.get("lift", 0.0)))
    cams = [o for o in sc.objects if o.name.startswith("cam_")]
    sc.camera = sc.objects.get("cam_aerial__draft") or (cams[0] if cams else None)

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    nv = sum(len(o.data.vertices) for o in sc.objects if o.type == "MESH")
    print("BUILT %s  objects=%d verts=%d  h %.1f..%.1f  (%.1fs)"
          % (OUT_BLEND, len(sc.objects), nv, H.min(), H.max(),
             __import__("time").time() - t0))


main()
