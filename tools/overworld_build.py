"""overworld_build.py — build tools/blends/overworld-proto.blend.

  Blender -b --factory-startup -P tools/overworld_build.py

One miniature FF9-style valley tile (120 x 90u) built ONCE, then copied into four
scenes and given four art treatments.  Everything a treatment does must survive a
glTF round-trip, so every style speaks only in things glTF carries:

    VERTEX COLOURS (FLOAT_COLOR, corner domain, linear) -> COLOR_0
    principled base params (roughness / metallic / emission / alpha)
    IMAGE TEXTURES with real UVs (style D only)

No procedural node trees reach the exported materials.  Style D's three-way terrain
blend is *baked* to a single image, then the node tree is thrown away.

Scenes: style_a (flat low-poly), style_b (painterly gradient), style_c (toy diorama),
        style_d (textured naturalistic-lite).  Objects are suffixed __a/__b/__c/__d;
        overworld_export.py strips the suffix so the runtime sees walk_road /
        water_river / etc.
"""
import bpy, bmesh, math, os, sys, random
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import overworld_lib as L

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TEXDIR = os.path.join(ROOT, "tools/textures/overworld")
OUT_BLEND = os.path.join(ROOT, "tools/blends/overworld-proto.blend")
STYLES = ("a", "b", "c", "d")

# ------------------------------------------------------------------ class table
# 0..6 are the terrain classes and MUST match the order of Field.w
(GRASS, GRASS_HI, AUTUMN, ROCK, PEAK, SAND, DIRT,
 WATER, WALL, ROOF, WOOD, STONE, FOL_A, FOL_B, FOL_C, TRUNK, EMIT, BASE, METAL, MIST) = range(20)
NCLS = 20

# which exported material each class lands in
GROUP = {WATER: "water", EMIT: "emit", MIST: "mist"}


def srgb(h):
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return np.array([f(r), f(g), f(b)])


# --------------------------------------------------------------------- palettes
# Deliberately the SAME class set for every style so the comparison isolates
# treatment.  Only the hues / values / material params change.
PAL = {
    # A — flat-shaded low-poly: vivid, confident, high chroma separation
    "a": {GRASS: "6f9a3a", GRASS_HI: "3f7350", AUTUMN: "cf8420", ROCK: "7c6f61",
          PEAK: "b3ada2", SAND: "c9ab63", DIRT: "9a6c3c", WATER: "1f8f96",
          WALL: "e0cfa8", ROOF: "b5442f", WOOD: "7a5330", STONE: "8d8578",
          FOL_A: "35704a", FOL_B: "d0862a", FOL_C: "b8452c", TRUNK: "5b3f28",
          EMIT: "ffb44a", BASE: "3a3630", METAL: "6d6a63", MIST: "ffd9ab"},
    # B — painterly gradient: lower chroma, pastel-leaning, big value range
    "b": {GRASS: "89a05c", GRASS_HI: "56737c", AUTUMN: "c69a56", ROCK: "645a63",
          PEAK: "9a94a0", SAND: "c8b287", DIRT: "9a7a5a", WATER: "5c9aa8",
          WALL: "e2d3b8", ROOF: "b0705e", WOOD: "836546", STONE: "8e8a86",
          FOL_A: "5e7a5c", FOL_B: "c69a58", FOL_C: "ae7259", TRUNK: "5f4c3c",
          EMIT: "ffd08a", BASE: "463f48", METAL: "84807a", MIST: "f4dcc0"},
    # C — toy diorama: clay tints, everything pulled toward one clay body
    "c": {GRASS: "8ea55b", GRASS_HI: "6f8a5a", AUTUMN: "c9903f", ROCK: "a2917f",
          PEAK: "c4bdb2", SAND: "d3bb85", DIRT: "a87f52", WATER: "4f9aa0",
          WALL: "e8d9b6", ROOF: "c0604a", WOOD: "9a6f43", STONE: "a89e90",
          FOL_A: "4f8258", FOL_B: "d09143", FOL_C: "c25a3c", TRUNK: "70503a",
          EMIT: "ffc169", BASE: "6b4a33", METAL: "8a867e", MIST: "f0dcc0"},
    # D — textured naturalistic-lite: real hues, but the CLASSES the texture blend
    #     multiplies against.  Anything that gets a texture in D is pre-brightened,
    #     because glTF can only do baseColorTexture * COLOR_0 (a plain multiply) and
    #     the Blender render has to predict exactly that.
    "d": {GRASS: "6d8442", GRASS_HI: "56704f", AUTUMN: "b4762c", ROCK: "7d7268",
          PEAK: "a49c92", SAND: "bda474", DIRT: "8a6440", WATER: "2f7a84",
          WALL: "d8c9a8", ROOF: "9c4a38", WOOD: "6f4e30", STONE: "8a837a",
          FOL_A: "3d6b45", FOL_B: "b57b28", FOL_C: "9c452c", TRUNK: "4f3a26",
          EMIT: "ffb44a", BASE: "3a352e", METAL: "6d6a63", MIST: "e8d8c0"},
}

PAL_LIN = {s: {c: srgb(h) for c, h in d.items()} for s, d in PAL.items()}


# ---------------------------------------------------------------- bmesh helpers
class Prop:
    """A bmesh accumulator where every face carries an art class in an int layer."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.cl = self.bm.faces.layers.int.new("cls")

    def _tag(self, before, c):
        for f in self.bm.faces:
            if f not in before:
                f[self.cl] = c

    def cube(self, c, center, size, rz=0.0, rx=0.0):
        b = set(self.bm.faces)
        m = (Matrix.Translation(Vector(center)) @ Matrix.Rotation(rz, 4, "Z")
             @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal(Vector(size).to_4d()))
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._tag(b, c)

    def cone(self, c, center, r1, r2, depth, seg=7, rz=0.0):
        b = set(self.bm.faces)
        m = Matrix.Translation(Vector(center)) @ Matrix.Rotation(rz, 4, "Z")
        try:
            bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=r1, radius2=r2, depth=depth, matrix=m)
        except TypeError:
            bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  diameter1=r1 * 2, diameter2=r2 * 2, depth=depth, matrix=m)
        self._tag(b, c)

    def ico(self, c, center, scale, subd=1, rz=0.0):
        b = set(self.bm.faces)
        m = (Matrix.Translation(Vector(center)) @ Matrix.Rotation(rz, 4, "Z")
             @ Matrix.Diagonal(Vector(scale).to_4d()))
        try:
            bmesh.ops.create_icosphere(self.bm, subdivisions=subd, radius=1.0, matrix=m)
        except TypeError:
            bmesh.ops.create_icosphere(self.bm, subdivisions=subd, diameter=2.0, matrix=m)
        self._tag(b, c)

    def prism(self, c, center, w, d, h, rz=0.0):
        """Gable roof: a triangular prism ridged along local +Y."""
        b = set(self.bm.faces)
        pts = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
               (0, -d / 2, h), (0, d / 2, h)]
        m = Matrix.Translation(Vector(center)) @ Matrix.Rotation(rz, 4, "Z")
        vs = [self.bm.verts.new(m @ Vector(p)) for p in pts]
        for f in ((0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4), (0, 3, 2, 1)):
            self.bm.faces.new([vs[i] for i in f])
        self.bm.normal_update()
        self._tag(b, c)

    def strip(self, c, left, right, close=False):
        """Quad ribbon from two matching polylines of 3D points."""
        b = set(self.bm.faces)
        vl = [self.bm.verts.new(Vector(p)) for p in left]
        vr = [self.bm.verts.new(Vector(p)) for p in right]
        for i in range(len(vl) - 1):
            try:
                self.bm.faces.new((vl[i], vl[i + 1], vr[i + 1], vr[i]))
            except ValueError:
                pass
        self.bm.normal_update()
        self._tag(b, c)

    def finish(self, coll):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        return ob


def face_classes(me):
    a = me.attributes.get("cls")
    return np.array([v.value for v in a.data]) if a else np.zeros(len(me.polygons), int)


# ------------------------------------------------------------------ build world
def build_base(F, coll):
    rng = random.Random(20260729)
    objs = {}

    # ---- terrain -----------------------------------------------------------
    X, Y, H = F.MX, F.MY, F.H
    verts = np.stack([X.ravel(), Y.ravel(), H.ravel()], axis=-1)
    idx = np.arange(L.NX * L.NY).reshape(L.NX, L.NY)
    a, b, c, d = idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]
    # alternating diagonals: a herringbone triangulation, not a uniform grid
    ii, jj = np.meshgrid(np.arange(L.NX - 1), np.arange(L.NY - 1), indexing="ij")
    flip = ((ii + jj) % 2) == 0
    t1 = np.where(flip[..., None], np.stack([a, b, c], -1), np.stack([a, b, d], -1))
    t2 = np.where(flip[..., None], np.stack([a, c, d], -1), np.stack([b, c, d], -1))
    faces = np.concatenate([t1.reshape(-1, 3), t2.reshape(-1, 3)])
    me = bpy.data.meshes.new("ground_valley")
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    ground = bpy.data.objects.new("ground_valley", me)
    coll.objects.link(ground)
    objs["ground"] = ground

    # per-vertex class weights, carried to the styles as a float attribute set
    ground["ow_terrain"] = 1

    # ---- edge skirt: the tile is an abbreviated world; cap its rim ----------
    p = Prop("edge_skirt")
    bx = [(i, 0) for i in range(L.NX)] + [(L.NX - 1, j) for j in range(L.NY)] + \
         [(i, L.NY - 1) for i in range(L.NX - 1, -1, -1)] + [(0, j) for j in range(L.NY - 1, -1, -1)]
    top = [(X[i, j], Y[i, j], H[i, j]) for i, j in bx]
    bot = [(x, y, -7.0) for x, y, _ in top]
    p.strip(BASE, bot, top)
    objs["skirt"] = p.finish(coll)

    # ---- river surface -----------------------------------------------------
    rt, rx, ry = L.river_pts(361)
    hw = F.water_halfwidth(rt) * 1.03
    wl = L.water_level(rt)
    tg = np.gradient(np.column_stack([rx, ry]), axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    nx, ny = -tg[:, 1], tg[:, 0]
    p = Prop("water_river")
    p.strip(WATER, list(zip(rx + nx * hw, ry + ny * hw, wl)),
            list(zip(rx - nx * hw, ry - ny * hw, wl)))
    objs["water"] = p.finish(coll)

    # ---- road ribbon (this IS the visible road AND the walk network) --------
    rd, rh = F.road, F.road_h
    tg = np.gradient(rd, axis=0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    nx, ny = -tg[:, 1], tg[:, 0]
    HW = 1.0                                        # road width 2.0u
    p = Prop("walk_road")
    p.strip(DIRT, list(zip(rd[:, 0] + nx * HW, rd[:, 1] + ny * HW, rh + 0.09)),
            list(zip(rd[:, 0] - nx * HW, rd[:, 1] - ny * HW, rh + 0.09)))
    objs["road"] = p.finish(coll)

    # a small green in the village so the spawn scan lands somewhere sensible
    p = Prop("walk_village_green")
    vx, vy = L.VILLAGE
    ring = [(vx + 5.0 * math.cos(a), vy + 5.0 * math.sin(a)) for a in
            np.linspace(0, 2 * math.pi, 25)]
    p.strip(GRASS, [(x, y, F.village_h + 0.06) for x, y in ring],
            [(vx + (x - vx) * 0.04, vy + (y - vy) * 0.04, F.village_h + 0.06) for x, y in ring])
    objs["green"] = p.finish(coll)

    # ---- bridge ------------------------------------------------------------
    bi = F.bridge_i
    bx0, by0 = rd[bi]
    bz = float(rh[bi])
    t = tg[bi]
    n = (-t[1], t[0])
    p = Prop("walk_bridge")
    ang = math.atan2(t[1], t[0])
    for side in (-1, 1):
        for k in (-3.4, 3.4):                        # piers into the bank
            px, py = bx0 + t[0] * k + n[0] * side * 1.15, by0 + t[1] * k + n[1] * side * 1.15
            gz = float(F.sample(np.array([px]), np.array([py]))[0])
            p.cube(STONE, (px, py, (gz + bz) / 2), (0.55, 0.55, max(0.6, bz - gz)), rz=ang)
        # railings
        for k in np.linspace(-4.6, 4.6, 9):
            px, py = bx0 + t[0] * k + n[0] * side * 1.02, by0 + t[1] * k + n[1] * side * 1.02
            p.cube(WOOD, (px, py, bz + 0.34), (0.13, 0.13, 0.62), rz=ang)
        p.cube(WOOD, (bx0 + n[0] * side * 1.02, by0 + n[1] * side * 1.02, bz + 0.62),
               (9.6, 0.12, 0.14), rz=ang)
    objs["bridge"] = p.finish(coll)

    # ---- village: 8 tiny houses round a green, one warm hearth -------------
    p = Prop("village")
    vh = F.village_h
    # FF9 proportion contract: a 1.45u character stands ROOF-HEIGHT beside these.
    # Bodies are ~1.0u, ridge lands at ~1.55-1.75u.  Getting this wrong is the single
    # fastest way to lose the miniature-world read, so it is pinned here.
    for i in range(8):
        a = i * (2 * math.pi / 8) + 0.22
        r = 3.2 + rng.uniform(0.0, 1.15)
        hx, hy = vx + math.cos(a) * r, vy + math.sin(a) * r
        gz = float(F.sample(np.array([hx]), np.array([hy]))[0])
        fa = a + math.pi + rng.uniform(-0.25, 0.25)   # face the green
        w = 1.05 + rng.uniform(0, 0.30)
        d = 0.88 + rng.uniform(0, 0.22)
        bh = 0.92 + rng.uniform(0, 0.22)
        p.cube(WALL, (hx, hy, gz + bh / 2), (w, d, bh), rz=fa)
        p.prism(ROOF, (hx, hy, gz + bh), w * 1.18, d * 1.18, 0.58 + rng.uniform(0, 0.18), rz=fa)
        cx = hx + math.cos(fa + 1.6) * w * 0.3
        cy = hy + math.sin(fa + 1.6) * w * 0.3
        p.cube(STONE, (cx, cy, gz + bh + 0.44), (0.18, 0.18, 0.78), rz=fa)
    # hearth: stone ring + glowing coals (the coals are an EMISSIVE material)
    for i in range(9):
        a = i * (2 * math.pi / 9)
        p.cube(STONE, (vx + math.cos(a) * 0.52, vy + math.sin(a) * 0.52, vh + 0.13),
               (0.28, 0.24, 0.26), rz=a)
    p.ico(EMIT, (vx, vy, vh + 0.20), (0.46, 0.46, 0.20), subd=1)
    p.cube(WOOD, (vx, vy, vh + 0.34), (0.9, 0.13, 0.13), rz=0.5)
    p.cube(WOOD, (vx, vy, vh + 0.34), (0.9, 0.13, 0.13), rz=2.2)
    # a low fence hinting the village boundary
    for a in np.linspace(0.4, 2.5, 7):
        fx, fy = vx + math.cos(a) * 5.6, vy + math.sin(a) * 5.6
        gz = float(F.sample(np.array([fx]), np.array([fy]))[0])
        p.cube(WOOD, (fx, fy, gz + 0.32), (0.11, 0.11, 0.64), rz=a)
    objs["village"] = p.finish(coll)

    # ---- cliff-notch town marker ------------------------------------------
    p = Prop("clifftown")
    cx, cy = L.CLIFFTOWN
    ch = F.clifftown_h
    face = math.atan2(cy - 0, cx - 0) + math.pi          # look back into the valley
    for k, (dx, dy, tw, th) in enumerate(((-3.4, 1.6, 1.5, 4.6), (2.6, 2.8, 1.8, 5.6),
                                          (3.2, -3.2, 1.3, 3.8))):
        tx = cx + dx * math.cos(face) - dy * math.sin(face)
        ty = cy + dx * math.sin(face) + dy * math.cos(face)
        gz = float(F.sample(np.array([tx]), np.array([ty]))[0])
        p.cube(STONE, (tx, ty, gz + th / 2), (tw, tw, th), rz=face + 0.2 * k)
        p.cone(ROOF, (tx, ty, gz + th + 0.75), tw * 0.82, 0.05, 1.5, seg=6, rz=face)
    # gate arch straddling the road end
    for side in (-1, 1):
        gx = cx + math.cos(face + math.pi / 2) * side * 1.7 - math.cos(face) * 3.2
        gy = cy + math.sin(face + math.pi / 2) * side * 1.7 - math.sin(face) * 3.2
        gz = float(F.sample(np.array([gx]), np.array([gy]))[0])
        p.cube(STONE, (gx, gy, gz + 1.6), (0.7, 0.7, 3.2), rz=face)
    p.cube(WOOD, (cx - math.cos(face) * 3.2, cy - math.sin(face) * 3.2, ch + 3.4),
           (0.5, 4.2, 0.5), rz=face)
    # curtain wall
    for k in np.linspace(-6.5, 6.5, 12):
        wx = cx + math.cos(face + math.pi / 2) * k + math.cos(face) * 2.6
        wy = cy + math.sin(face + math.pi / 2) * k + math.sin(face) * 2.6
        gz = float(F.sample(np.array([wx]), np.array([wy]))[0])
        p.cube(STONE, (wx, wy, gz + 1.1), (1.3, 0.8, 2.2), rz=face)
    objs["clifftown"] = p.finish(coll)

    # ---- dam + waterwheel at the gorge head --------------------------------
    p = Prop("dam")
    di = int(np.argmin(np.abs(rt - L.DAM_T)))
    dx0, dy0 = float(rx[di]), float(ry[di])
    dtg = (float(tg[di][0]) if False else 0.0, 0.0)
    dt = np.array([rx[di + 1] - rx[di - 1], ry[di + 1] - ry[di - 1]])
    dt /= np.linalg.norm(dt)
    dn = np.array([-dt[1], dt[0]])
    dang = math.atan2(dt[1], dt[0])
    dwl = float(L.water_level(np.array([L.DAM_T - 0.01]))[0])
    p.cube(STONE, (dx0, dy0, dwl - 1.6), (2.2, 13.0, 6.4), rz=dang)
    p.cube(STONE, (dx0, dy0, dwl + 1.7), (2.9, 13.0, 0.55), rz=dang)     # dam crest walk
    # waterwheel on the north abutment
    wx = dx0 + dn[0] * 3.6 + dt[0] * 1.9
    wy = dy0 + dn[1] * 3.6 + dt[1] * 1.9
    for k in range(10):
        a = k * (2 * math.pi / 10)
        p.cube(WOOD, (wx + math.cos(a) * 1.35 * dt[0], wy + math.cos(a) * 1.35 * dt[1],
                      dwl - 0.4 + math.sin(a) * 1.35), (0.5, 0.16, 0.5), rz=dang, rx=a)
    p.cone(WOOD, (wx, wy, dwl - 0.4), 1.45, 1.45, 0.24, seg=12, rz=dang)
    p.cone(METAL, (wx, wy, dwl - 0.4), 0.22, 0.22, 1.4, seg=8, rz=dang)
    # mill house on the crest
    mx, my = dx0 + dn[0] * 5.6, dy0 + dn[1] * 5.6
    p.cube(WALL, (mx, my, dwl + 2.9), (2.3, 2.0, 1.9), rz=dang)
    p.prism(ROOF, (mx, my, dwl + 3.85), 2.7, 2.4, 1.15, rz=dang)
    objs["dam"] = p.finish(coll)

    # ---- trees: three archetypes, autumn scatter ---------------------------
    p = Prop("trees")
    placed = []
    tries = 0
    counts = [0, 0, 0]
    while len(placed) < 54 and tries < 40000:
        tries += 1
        tx = rng.uniform(-56, 56)
        ty = rng.uniform(-42, 42)
        if any((tx - a) ** 2 + (ty - b) ** 2 < 12.0 for a, b in placed):
            continue
        gz = float(F.sample(np.array([tx]), np.array([ty]))[0])
        wlv = float(L.water_level(np.array([F._river_dist([tx], [ty])[1][0]]))[0])
        if gz < wlv + 1.1 or gz > wlv + 26.0:
            continue
        if float(F.slope_at(np.array([tx]), np.array([ty]))[0]) > 0.85:
            continue
        if float(F.river_dist([tx], [ty])[0]) < 4.2:
            continue
        if float(F.road_dist([tx], [ty])[0]) < 3.0:
            continue
        if math.hypot(tx - vx, ty - vy) < 8.0 or math.hypot(tx - cx, ty - cy) < 9.0:
            continue
        placed.append((tx, ty))
        k = rng.random()
        rz = rng.uniform(0, 6.28)
        sc = rng.uniform(0.85, 1.2)
        if k < 0.36:                                   # conifer
            counts[0] += 1
            p.cone(TRUNK, (tx, ty, gz + 0.3 * sc), 0.11 * sc, 0.09 * sc, 0.6 * sc, seg=6, rz=rz)
            p.cone(FOL_A, (tx, ty, gz + 1.05 * sc), 0.78 * sc, 0.30 * sc, 1.35 * sc, seg=7, rz=rz)
            p.cone(FOL_A, (tx, ty, gz + 1.95 * sc), 0.52 * sc, 0.02 * sc, 1.15 * sc, seg=7, rz=rz + 0.4)
        elif k < 0.76:                                 # broadleaf blob
            counts[1] += 1
            p.cone(TRUNK, (tx, ty, gz + 0.45 * sc), 0.14 * sc, 0.10 * sc, 0.95 * sc, seg=6, rz=rz)
            p.ico(FOL_B, (tx, ty, gz + 1.55 * sc), (0.92 * sc, 0.92 * sc, 0.72 * sc), rz=rz)
            p.ico(FOL_B, (tx + 0.35 * sc, ty - 0.28 * sc, gz + 1.95 * sc),
                  (0.58 * sc, 0.58 * sc, 0.48 * sc), rz=rz + 1.1)
        else:                                          # slender autumn
            counts[2] += 1
            p.cone(TRUNK, (tx, ty, gz + 0.6 * sc), 0.09 * sc, 0.07 * sc, 1.25 * sc, seg=6, rz=rz)
            p.ico(FOL_C, (tx, ty, gz + 1.75 * sc), (0.50 * sc, 0.50 * sc, 0.90 * sc), rz=rz)
    objs["trees"] = p.finish(coll)
    print("TREES placed=%d  conifer=%d broadleaf=%d slender=%d" % (len(placed), *counts))

    # ---- rock outcrops -----------------------------------------------------
    p = Prop("rocks")
    n = 0
    tries = 0
    while n < 16 and tries < 20000:
        tries += 1
        tx, ty = rng.uniform(-55, 55), rng.uniform(-41, 41)
        sl = float(F.slope_at(np.array([tx]), np.array([ty]))[0])
        gz = float(F.sample(np.array([tx]), np.array([ty]))[0])
        wlv = float(L.water_level(np.array([F._river_dist([tx], [ty])[1][0]]))[0])
        if gz < wlv + 0.4:
            continue
        if sl < 0.35 and rng.random() < 0.75:
            continue
        if float(F.road_dist([tx], [ty])[0]) < 2.6:
            continue
        n += 1
        s = rng.uniform(0.7, 2.0)
        b = set(p.bm.faces)
        p.ico(ROCK, (tx, ty, gz + s * 0.35), (s * 1.1, s * 0.85, s * 0.72),
              subd=1, rz=rng.uniform(0, 6.28))
        for f in p.bm.faces:                            # jitter into a crag
            if f not in b:
                for v in f.verts:
                    v.co += Vector((rng.uniform(-.12, .12), rng.uniform(-.12, .12),
                                    rng.uniform(-.10, .10))) * s
    objs["rocks"] = p.finish(coll)

    # ---- 1.45u scale references (renders only; stripped at export) ---------
    # one on the road for the chase shot, one at the village edge so the FF9
    # "character is house-height" proportion is directly checkable
    px, py, pz, ptg = F.road_point(0.30)
    qx, qy, qz, _ = F.road_point(0.055)
    p = Prop("ref_char")
    for (ox, oy, oz) in ((px, py, pz), (qx, qy, qz)):
        p.cone(PEAK, (ox, oy, oz + 0.72), 0.26, 0.26, 1.05, seg=10)
        p.ico(PEAK, (ox, oy, oz + 1.24), (0.26, 0.26, 0.26), subd=1)
        p.ico(PEAK, (ox, oy, oz + 0.21), (0.26, 0.26, 0.21), subd=1)
    objs["ref"] = p.finish(coll)
    objs["_charpos"] = (px, py, pz, ptg)
    print("ROAD length %.1fu  chase-char at (%.1f, %.1f)  village-ref at (%.1f, %.1f)"
          % (F.road_s[-1], px, py, qx, qy))

    # ---- the road as a real curve datablock (documentation of the spline) --
    cu = bpy.data.curves.new("road_curve", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(rd) - 1)
    for i, (xx, yy) in enumerate(rd):
        sp.points[i].co = (xx, yy, rh[i] + 0.15, 1.0)
    coll.objects.link(bpy.data.objects.new("road_curve", cu))
    return objs


# ---------------------------------------------------------------- style helpers
def new_mat(name, base=(0.8, 0.8, 0.8), rough=0.85, metal=0.0, use_vcol=True,
            emit=None, emit_str=1.0, alpha=1.0, blend=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_str
    if use_vcol:
        ca = nt.nodes.new("ShaderNodeVertexColor")
        ca.layer_name = "Col"
        ca.location = (-320, 120)
        nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
        if blend:
            nt.links.new(ca.outputs["Alpha"], bsdf.inputs["Alpha"])
    if blend:
        m.surface_render_method = "BLENDED" if hasattr(m, "surface_render_method") else m.blend_method
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
        bsdf.inputs["Alpha"].default_value = alpha
    return m


def ensure_col(me):
    a = me.color_attributes.get("Col")
    if a is None:
        a = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
    me.color_attributes.active_color = a
    me.color_attributes.render_color_index = list(me.color_attributes).index(a)
    return a


def write_prop_colors(ob, style, hard, jitter, unify=None, unify_k=0.0, seed=1):
    """Colour a class-tagged prop mesh; also assigns material slots by class group."""
    me = ob.data
    cls = face_classes(me)
    pal = PAL_LIN[style]
    a = ensure_col(me)
    rng = np.random.RandomState(seed)
    fj = 1.0 + (rng.rand(len(cls)) - 0.5) * 2.0 * jitter
    cols = np.array([pal[int(c)] for c in cls]) * fj[:, None]
    if unify is not None and unify_k > 0:
        cols = cols * (1 - unify_k) + srgb(unify) * unify_k
    data = np.zeros((len(me.loops), 4))
    data[:, 3] = 1.0
    for pi, poly in enumerate(me.polygons):
        for li in poly.loop_indices:
            data[li, :3] = cols[pi]
    a.data.foreach_set("color", data.ravel())
    return cls


def assign_slots(ob, mats, cls):
    """mats: dict group->material. Sets slots + per-face material_index."""
    groups = sorted({GROUP.get(int(c), "matte") for c in cls})
    ob.data.materials.clear()
    for g in groups:
        ob.data.materials.append(mats[g])
    order = {g: i for i, g in enumerate(groups)}
    mi = np.array([order[GROUP.get(int(c), "matte")] for c in cls], dtype=np.int32)
    ob.data.polygons.foreach_set("material_index", mi)


def terrain_colors(ob, F, style, mode, seed=3, gradient=False, jitter=0.16):
    """Terrain colouring. mode: 'facet' (per-face argmax) or 'smooth' (per-vertex blend).
    gradient adds style B's valley-warm -> ridge-cool wash and altitude haze."""
    me = ob.data
    pal = PAL_LIN[style]
    P = np.array([pal[c] for c in range(7)])            # 7 terrain classes
    W = F.w.reshape(-1, 7)
    vcol = W @ P                                        # smooth blended vertex colour
    a = ensure_col(me)
    nv = L.NX * L.NY
    loops = np.zeros((len(me.loops), 4))
    loops[:, 3] = 1.0
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)

    sh = F.shade.ravel()
    if mode == "facet":
        rng = np.random.RandomState(seed)
        fverts = lv.reshape(-1, 3)                      # terrain is pure triangles
        fw = W[fverts].mean(axis=1)
        dom = np.argmax(fw, axis=1)
        fc = P[dom] * 0.60 + (fw @ P) * 0.40
        fc *= (1.0 + (rng.rand(len(fc)) - 0.5) * jitter)[:, None]
        fc *= sh[fverts].mean(axis=1)[:, None]
        loops[:, :3] = np.repeat(fc, 3, axis=0)
    else:
        c = vcol.copy()
        alt = (F.H - F.wl).ravel()
        if gradient:
            # valley floor warm -> ridge cool, plus a light altitude haze wash
            cool, warm = srgb("5d7391"), srgb("d8a760")
            k = L.sstep(1.0, 22.0, alt)[:, None]
            c = c * (1 - 0.26 * k) + cool * (0.26 * k)
            kw = (1.0 - L.sstep(0.0, 7.0, alt))[:, None]
            c = c * (1 - 0.26 * kw) + warm * (0.26 * kw)
            haze = L.sstep(20.0, 38.0, alt)[:, None] * 0.10
            c = c * (1 - haze) + srgb("d8c3a6") * haze
        c *= (1.0 + (sh - 1.0) * 0.6)[:, None]
        loops[:, :3] = c[lv]
    a.data.foreach_set("color", loops.ravel())
    return vcol


def bevel_mesh(me, offset=0.055, segs=2):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                    offset=offset, offset_type="OFFSET", segments=segs, profile=0.5,
                    affect="EDGES", clamp_overlap=True, miter_outer="SHARP")
    bm.to_mesh(me)
    bm.free()


def box_uv(ob, scale=1.0):
    """Manual cube projection — no ops, headless-safe, exports as real UVs."""
    me = ob.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        u_i, v_i = ((1, 2), (0, 2), (0, 1))[ax]
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co[u_i] * scale, co[v_i] * scale)


def planar_uv_terrain(ob):
    me = ob.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co[0] + L.TILE_X / 2) / L.TILE_X,
                              (co[1] + L.TILE_Y / 2) / L.TILE_Y)


def ribbon_uv(ob, along=0.35, across=1.0):
    """Length-wise UVs for the road ribbon (strip mesh: quads in order)."""
    me = ob.data
    uv = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for pi, poly in enumerate(me.polygons):
        for k, li in enumerate(poly.loop_indices):
            u = (pi + (1 if k in (1, 2) else 0)) * along
            v = (0.0 if k in (0, 1) else across)
            uv.data[li].uv = (u, v)


def tex_node(nt, path, noncolor=False):
    n = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(path, check_existing=True)
    n.image = img
    if noncolor:
        img.colorspace_settings.name = "Non-Color"
    return n


# ------------------------------------------------------------------ style build
def dusk_rig(sc, F, style):
    """The dusk key + world, IDENTICAL in every style of every round.

    Round 2 (overworld2_build.py) calls this same function, which is the only way
    to guarantee the comparison stays about treatment across both rounds."""
    col = sc.collection
    # dusk key from the south-west at 40deg: high enough that the rim does not throw
    # a 40u shadow across the village, low enough to model the hills
    sun = bpy.data.lights.new("sun_" + style, "SUN")
    sun.energy = 3.6
    sun.color = (1.0, 0.79, 0.56)
    sun.angle = math.radians(3.0)
    so = bpy.data.objects.new("sun_" + style, sun)
    so.rotation_euler = (math.radians(50.0), 0.0, math.radians(20.0))
    col.objects.link(so)
    fill = bpy.data.lights.new("fill_" + style, "SUN")
    fill.energy = 0.95
    fill.color = (0.60, 0.71, 0.96)
    fo = bpy.data.objects.new("fill_" + style, fill)
    fo.rotation_euler = (math.radians(58.0), 0.0, math.radians(205.0))
    col.objects.link(fo)
    hearth = bpy.data.lights.new("hearth_" + style, "POINT")
    hearth.energy = 260.0
    hearth.color = (1.0, 0.65, 0.30)
    hearth.shadow_soft_size = 0.5
    ho = bpy.data.objects.new("hearth_" + style, hearth)
    ho.location = (L.VILLAGE[0], L.VILLAGE[1], F.village_h + 0.7)
    col.objects.link(ho)

    w = bpy.data.worlds.new("world_" + style)
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.55
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "LINEAR"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.34
    ramp.color_ramp.elements[0].color = (*srgb("f0b070"), 1)     # warm dusk horizon
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*srgb("6d86b0"), 1)     # cool zenith
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    sc.world = w
    return sc


def make_scene(style, base_objs, F):
    sc = bpy.data.scenes.new("style_" + style)
    col = sc.collection
    pal = PAL_LIN[style]
    dusk_rig(sc, F, style)

    # ---- style material set ------------------------------------------------
    if style == "a":
        mats = {"matte": new_mat("ow_a_matte", rough=0.88),
                "water": new_mat("ow_a_water", rough=0.24, alpha=0.86, blend=True),
                "emit": new_mat("ow_a_emit", rough=0.6, emit=srgb("ff9f38"), emit_str=9.0),
                "mist": new_mat("ow_a_mist", rough=1.0, alpha=0.25, blend=True)}
    elif style == "b":
        mats = {"matte": new_mat("ow_b_matte", rough=1.0),
                "water": new_mat("ow_b_water", rough=0.34, alpha=0.72, blend=True),
                "emit": new_mat("ow_b_emit", rough=0.9, emit=srgb("ffc27a"), emit_str=7.0),
                "mist": new_mat("ow_b_mist", rough=1.0, alpha=1.0, blend=True)}
    elif style == "c":
        # props are satin clay; the GROUND is deliberately duller — at 0.34 the sun
        # sparkles off individual terrain facets and the tile reads as tinfoil
        mats = {"matte": new_mat("ow_c_clay", rough=0.30),
                "ground": new_mat("ow_c_clay_ground", rough=0.58),
                "water": new_mat("ow_c_water", rough=0.10, metal=0.0, alpha=0.92, blend=True),
                "emit": new_mat("ow_c_emit", rough=0.4, emit=srgb("ffb055"), emit_str=8.0),
                "mist": new_mat("ow_c_mist", rough=1.0, alpha=0.2, blend=True)}
    else:
        mats = {"matte": new_mat("ow_d_matte", rough=0.92),
                "water": new_mat("ow_d_water", rough=0.30, alpha=0.80, blend=True),
                "emit": new_mat("ow_d_emit", rough=0.6, emit=srgb("ff9f38"), emit_str=9.0),
                "mist": new_mat("ow_d_mist", rough=1.0, alpha=0.2, blend=True)}
    mats.setdefault("ground", mats["matte"])

    smooth = style == "b"
    facet = "smooth" if style in ("b", "d") else "facet"

    # ---- copy + treat every base object -----------------------------------
    made = {}
    for key, ob in base_objs.items():
        if key.startswith("_"):
            continue
        d = ob.copy()
        d.data = ob.data.copy()
        d.name = "%s__%s" % (ob.name, style)
        d.data.name = d.name
        col.objects.link(d)
        made[key] = d

    ground = made["ground"]
    terrain_colors(ground, F, style, facet, gradient=(style == "b"),
                   jitter={"a": 0.16, "c": 0.07}.get(style, 0.0))
    ground.data.materials.clear()
    ground.data.materials.append(mats["ground"])

    # style C: chunky bevels on the crafted props (NOT the terrain)
    if style == "c":
        for key in ("village", "clifftown", "dam", "bridge", "rocks", "trees"):
            bevel_mesh(made[key].data, offset=0.075, segs=2)

    unify, uk = (None, 0.0)
    if style == "c":
        unify, uk = "cbb08a", 0.24                      # everything shares one clay body
    for i, key in enumerate(("skirt", "water", "road", "green", "bridge", "village",
                             "clifftown", "dam", "trees", "rocks", "ref")):
        ob = made[key]
        jit = {"a": 0.09, "b": 0.03, "c": 0.05, "d": 0.06}[style]
        cls = write_prop_colors(ob, style, facet == "facet", jit,
                                unify=(unify if key not in ("water", "ref") else None),
                                unify_k=uk, seed=17 + i)
        assign_slots(ob, mats, cls)

    # ---- shading -----------------------------------------------------------
    # A and C are hard-facet by definition.  B goes soft everywhere except the built
    # things (a smooth-shaded cottage stops reading as a cottage).  D smooths the
    # natural world so its textures carry the detail instead of the silhouette.
    SOFT = {"a": set(), "c": set(),
            "b": {"ground", "water", "trees", "rocks", "green"},
            "d": {"ground", "water", "trees", "rocks", "green"}}[style]
    for key, ob in made.items():
        v = key in SOFT
        ob.data.polygons.foreach_set("use_smooth", [v] * len(ob.data.polygons))
        ob.data.update()

    # ---- style B: exportable fog bands (vertex-alpha planes) ---------------
    if style == "b":
        p = Prop("water_mistband__b_src")
        for bi, (z, al, sx) in enumerate(((7.0, 0.13, 1.0), (11.5, 0.09, 0.94), (16.5, 0.06, 0.88))):
            nx_, ny_ = 26, 20
            xs = np.linspace(-62 * sx, 62 * sx, nx_)
            ys = np.linspace(-47 * sx, 47 * sx, ny_)
            base = len(p.bm.verts)
            vs = [[p.bm.verts.new((x, y, z + 0.7 * math.sin(x * 0.06 + bi) * math.cos(y * 0.05)))
                   for y in ys] for x in xs]
            b = set(p.bm.faces)
            for i in range(nx_ - 1):
                for j in range(ny_ - 1):
                    p.bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            p._tag(b, MIST)
        mo = p.finish(col)
        mo.name = "water_mistband__b"
        mo.data.name = mo.name
        me = mo.data
        a = ensure_col(me)
        cols = np.zeros((len(me.loops), 4))
        mc = PAL_LIN["b"][MIST]
        for li, lp in enumerate(me.loops):
            co = me.vertices[lp.vertex_index].co
            e = max(abs(co[0]) / 62.0, abs(co[1]) / 47.0)
            band = 0.13 if co[2] < 9 else (0.09 if co[2] < 14 else 0.06)
            cols[li, :3] = mc
            cols[li, 3] = band * float(1.0 - L.sstep(0.55, 1.0, e)) * \
                float(0.55 + 0.45 * math.sin(co[0] * 0.05 + co[1] * 0.03))
        a.data.foreach_set("color", cols.ravel())
        me.materials.clear()
        me.materials.append(mats["mist"])
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))

    # ---- style C: the model base — a visible plinth at the tile rim --------
    if style == "c":
        p = Prop("base_plinth")
        for (sx, sy, z, h) in ((124.0, 94.0, -12.6, 1.2), (127.5, 97.5, -13.9, 1.6)):
            p.cube(BASE, (0, 0, z), (sx, sy, h))
        po = p.finish(col)
        po.name = "base_plinth__c"
        po.data.name = po.name
        bevel_mesh(po.data, offset=0.35, segs=2)
        cls = write_prop_colors(po, "c", True, 0.03, seed=99)
        assign_slots(po, mats, cls)
        made["plinth"] = po
        # re-tint the skirt to the base colour so the tile reads as a cast model
        sk = made["skirt"]
        cls = write_prop_colors(sk, "c", True, 0.02, seed=98)
        assign_slots(sk, mats, cls)

    # ---- style D: textures ------------------------------------------------
    if style == "d":
        build_style_d(made, mats, F, sc)

    # ---- cameras (identical transforms in every scene) --------------------
    px, py, pz, tg = base_objs["_charpos"]
    add_cameras(sc, F, (px, py, pz), tg, style)
    sc.render.resolution_x, sc.render.resolution_y = 1344, 768
    sc.render.resolution_percentage = 100
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"     # match the runtime: no tonemap
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    return sc, made


def build_style_d(made, mats, F, sc):
    """Bake a 3-way terrain blend to one image; box-project real textures elsewhere."""
    ground = made["ground"]
    planar_uv_terrain(ground)

    # masks (rock / dirt / sand) ride in a temporary colour attribute the bake reads;
    # "Col" already holds the smooth class-blend palette, and the bake multiplies the
    # two so the terrain keeps the art-directed hue and gains real surface detail
    me = ground.data
    mk = me.color_attributes.new("masks", "FLOAT_COLOR", "CORNER")
    W = F.w.reshape(-1, 7)
    m = np.stack([W[:, ROCK] + W[:, PEAK], W[:, DIRT], W[:, SAND]], -1)
    lv = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    d = np.ones((len(me.loops), 4))
    d[:, :3] = m[lv]
    mk.data.foreach_set("color", d.ravel())

    bakemat = bpy.data.materials.new("ow_d_terrain_bake")
    bakemat.use_nodes = True
    nt = bakemat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "UVMap"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (26.0, 20.0, 1.0)   # ~4.6u per texture tile
    nt.links.new(uvn.outputs["UV"], mp.inputs["Vector"])
    g = tex_node(nt, os.path.join(TEXDIR, "withered_grass_diff_1k.jpg"))
    g2 = tex_node(nt, os.path.join(TEXDIR, "leafy_grass_diff_1k.jpg"))
    r = tex_node(nt, os.path.join(TEXDIR, "rock_face_03_Diffuse.jpg")
                 if os.path.exists(os.path.join(TEXDIR, "rock_face_03_Diffuse.jpg"))
                 else os.path.join(ROOT, "tools/textures/rock_face_03_Diffuse.jpg"))
    dpath = tex_node(nt, os.path.join(TEXDIR, "stony_dirt_path_diff_1k.jpg"))
    for n in (g, g2, r, dpath):
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        n.extension = "REPEAT"
    mp2 = nt.nodes.new("ShaderNodeMapping")
    mp2.inputs["Scale"].default_value = (9.0, 7.0, 1.0)
    nt.links.new(uvn.outputs["UV"], mp2.inputs["Vector"])
    nt.links.new(mp2.outputs["Vector"], g2.inputs["Vector"])

    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "masks"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(ca.outputs["Color"], sep.inputs["Color"])

    def mix(a_out, b_out, fac_out=None, fac=0.5):
        n = nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        s = lambda nm, t: [x for x in n.inputs if x.name == nm and x.type == t][0]
        nt.links.new(a_out, s("A", "RGBA"))
        nt.links.new(b_out, s("B", "RGBA"))
        if fac_out:
            nt.links.new(fac_out, s("Factor", "VALUE"))
        else:
            s("Factor", "VALUE").default_value = fac
        return n.outputs["Result"]

    # base grass: two grasses broken up by a large-scale noise for autumn patchiness
    noi = nt.nodes.new("ShaderNodeTexNoise")
    noi.inputs["Scale"].default_value = 5.0
    nt.links.new(uvn.outputs["UV"], noi.inputs["Vector"])
    col = mix(g.outputs["Color"], g2.outputs["Color"], noi.outputs["Fac"])
    col = mix(col, r.outputs["Color"], sep.outputs[0])          # rock on slopes
    col = mix(col, dpath.outputs["Color"], sep.outputs[1])      # dirt on the road

    # STYLISED application, not photoreal: the photo supplies DETAIL (its luminance,
    # remapped around 1.0) and a little of its hue; the art-directed class palette
    # supplies the COLOUR.  Straight photo albedo turns the whole tile into one
    # muddy straw sheet — this keeps the same read as the other three styles.
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(col, bw.inputs["Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.06
    mr.inputs["From Max"].default_value = 0.62
    mr.inputs["To Min"].default_value = 0.66
    mr.inputs["To Max"].default_value = 1.42
    mr.clamp = True
    nt.links.new(bw.outputs["Val"], mr.inputs["Value"])
    cav = nt.nodes.new("ShaderNodeVertexColor")
    cav.layer_name = "Col"
    tinted = mix(cav.outputs["Color"], col, fac=0.20)           # a touch of real hue
    detail = nt.nodes.new("ShaderNodeMix")
    detail.data_type = "RGBA"
    detail.blend_type = "MULTIPLY"
    sd = lambda nm, t: [x for x in detail.inputs if x.name == nm and x.type == t][0]
    sd("Factor", "VALUE").default_value = 1.0
    nt.links.new(tinted, sd("A", "RGBA"))
    nt.links.new(mr.outputs["Result"], sd("B", "RGBA"))
    nt.links.new(detail.outputs["Result"], bsdf.inputs["Base Color"])

    img = bpy.data.images.new("ow_d_terrain", 2048, 2048)
    img.filepath_raw = os.path.join(TEXDIR, "ow_d_terrain.png")
    bake_target = nt.nodes.new("ShaderNodeTexImage")
    bake_target.image = img
    nt.nodes.active = bake_target

    me.materials.clear()
    me.materials.append(bakemat)

    prev_scene = bpy.context.window.scene if bpy.context.window else None
    if bpy.context.window:
        bpy.context.window.scene = sc
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 4
    sc.cycles.device = "CPU"
    sc.render.bake.use_pass_direct = False
    sc.render.bake.use_pass_indirect = False
    sc.render.bake.use_pass_color = True
    sc.render.bake.margin = 24
    for o in sc.objects:
        o.select_set(False)
    ground.select_set(True)
    bpy.context.view_layer.objects.active = ground
    print("BAKE start (2048, terrain diffuse colour)…")
    bpy.ops.object.bake(type="DIFFUSE")
    img.save()
    print("BAKE done ->", img.filepath_raw)
    sc.render.engine = "BLENDER_EEVEE"
    if prev_scene and bpy.context.window:
        bpy.context.window.scene = prev_scene

    # final exportable material: one image texture, nothing procedural
    tm = bpy.data.materials.new("ow_d_terrain")
    tm.use_nodes = True
    ntt = tm.node_tree
    ntt.nodes.clear()
    o2 = ntt.nodes.new("ShaderNodeOutputMaterial")
    b2 = ntt.nodes.new("ShaderNodeBsdfPrincipled")
    b2.inputs["Roughness"].default_value = 0.92
    ntt.links.new(b2.outputs["BSDF"], o2.inputs["Surface"])
    ti = ntt.nodes.new("ShaderNodeTexImage")
    ti.image = img
    uvm = ntt.nodes.new("ShaderNodeUVMap")
    uvm.uv_map = "UVMap"
    ntt.links.new(uvm.outputs["UV"], ti.inputs["Vector"])
    ntt.links.new(ti.outputs["Color"], b2.inputs["Base Color"])
    me.materials.clear()
    me.materials.append(tm)
    me.color_attributes.remove(me.color_attributes["masks"])
    if "Col" in me.color_attributes:
        me.color_attributes.remove(me.color_attributes["Col"])   # texture carries it now

    # road + village green: these are ground ribbons sitting 0.09u above the terrain
    # at the SAME xy, so they take planar UVs into the SAME baked map.  The dirt path
    # is already baked into it under the road, so the ribbon lines up perfectly and
    # costs zero extra texture memory (a second tiled road texture read as a dark
    # gravel strip pasted on top of the grass).
    # The green disc takes the map straight.  The road needs a darkening tint on top:
    # texture-matched alone it vanishes into the terrain, and an overworld road that
    # you cannot read from the follow camera is not a road.
    green = made["green"]
    planar_uv_terrain(green)
    green.data.materials.clear()
    green.data.materials.append(tm)
    green.data.polygons.foreach_set("material_index", [0] * len(green.data.polygons))
    if "Col" in green.data.color_attributes:
        green.data.color_attributes.remove(green.data.color_attributes["Col"])

    road = made["road"]
    planar_uv_terrain(road)
    rm = bpy.data.materials.new("ow_d_road")
    rm.use_nodes = True
    n2 = rm.node_tree
    n2.nodes.clear()
    o3 = n2.nodes.new("ShaderNodeOutputMaterial")
    b3 = n2.nodes.new("ShaderNodeBsdfPrincipled")
    b3.inputs["Roughness"].default_value = 0.95
    n2.links.new(b3.outputs["BSDF"], o3.inputs["Surface"])
    t3 = n2.nodes.new("ShaderNodeTexImage")
    t3.image = img
    u3 = n2.nodes.new("ShaderNodeUVMap")
    u3.uv_map = "UVMap"
    n2.links.new(u3.outputs["UV"], t3.inputs["Vector"])
    cav2 = n2.nodes.new("ShaderNodeVertexColor")
    cav2.layer_name = "Col"
    mx2 = n2.nodes.new("ShaderNodeMix")
    mx2.data_type = "RGBA"
    mx2.blend_type = "MULTIPLY"
    s2 = lambda nm, t: [x for x in mx2.inputs if x.name == nm and x.type == t][0]
    s2("Factor", "VALUE").default_value = 1.0
    n2.links.new(t3.outputs["Color"], s2("A", "RGBA"))
    n2.links.new(cav2.outputs["Color"], s2("B", "RGBA"))
    n2.links.new(mx2.outputs["Result"], b3.inputs["Base Color"])
    ca = road.data.color_attributes["Col"]
    d = np.zeros(len(ca.data) * 4)
    d = d.reshape(-1, 4)
    d[:, :3] = srgb("c39a70")
    d[:, 3] = 1.0
    ca.data.foreach_set("color", d.ravel())
    road.data.materials.clear()
    road.data.materials.append(rm)
    road.data.polygons.foreach_set("material_index", [0] * len(road.data.polygons))

    # rocks: real rock texture via box projection (keeps vertex colours off)
    rock = made["rocks"]
    box_uv(rock, scale=0.42)
    km = bpy.data.materials.new("ow_d_rock")
    km.use_nodes = True
    n4 = km.node_tree
    n4.nodes.clear()
    o4 = n4.nodes.new("ShaderNodeOutputMaterial")
    b4 = n4.nodes.new("ShaderNodeBsdfPrincipled")
    b4.inputs["Roughness"].default_value = 0.9
    n4.links.new(b4.outputs["BSDF"], o4.inputs["Surface"])
    rp = os.path.join(ROOT, "tools/textures/rock_face_03_Diffuse.jpg")
    t4 = tex_node(n4, rp)
    u4 = n4.nodes.new("ShaderNodeUVMap")
    u4.uv_map = "UVMap"
    n4.links.new(u4.outputs["UV"], t4.inputs["Vector"])
    n4.links.new(t4.outputs["Color"], b4.inputs["Base Color"])
    rock.data.materials.clear()
    rock.data.materials.append(km)
    if "Col" in rock.data.color_attributes:
        rock.data.color_attributes.remove(rock.data.color_attributes["Col"])

    # village + clifftown walls: plaster / planks, box projected
    for key, tex, sc_ in (("village", "clay_plaster_Diffuse.jpg", 0.6),
                          ("clifftown", "rock_face_03_Diffuse.jpg", 0.35)):
        ob = made[key]
        box_uv(ob, scale=sc_)
        mm = bpy.data.materials.new("ow_d_" + key)
        mm.use_nodes = True
        n5 = mm.node_tree
        n5.nodes.clear()
        o5 = n5.nodes.new("ShaderNodeOutputMaterial")
        b5 = n5.nodes.new("ShaderNodeBsdfPrincipled")
        b5.inputs["Roughness"].default_value = 0.9
        n5.links.new(b5.outputs["BSDF"], o5.inputs["Surface"])
        t5 = tex_node(n5, os.path.join(ROOT, "tools/textures", tex))
        u5 = n5.nodes.new("ShaderNodeUVMap")
        u5.uv_map = "UVMap"
        n5.links.new(u5.outputs["UV"], t5.inputs["Vector"])
        # multiply the texture by the class vertex colour so roofs stay red etc.
        cav = n5.nodes.new("ShaderNodeVertexColor")
        cav.layer_name = "Col"
        mixn = n5.nodes.new("ShaderNodeMix")
        mixn.data_type = "RGBA"
        mixn.blend_type = "MULTIPLY"
        sk = lambda nm, t: [x for x in mixn.inputs if x.name == nm and x.type == t][0]
        sk("Factor", "VALUE").default_value = 1.0
        n5.links.new(t5.outputs["Color"], sk("A", "RGBA"))
        n5.links.new(cav.outputs["Color"], sk("B", "RGBA"))
        n5.links.new(mixn.outputs["Result"], b5.inputs["Base Color"])
        # NOTE: this multiply is a node tree — glTF cannot carry it, but the exporter
        # writes baseColorTexture * COLOR_0, which is exactly the same maths. Verified
        # by overworld_verify.py.
        # A multiply always DARKENS, so the class colours have to be pre-divided by
        # the map's own mean luminance or every textured prop comes out muddy.
        px = np.array(t5.image.pixels[:]).reshape(-1, 4)[:, :3]
        gain = float(np.clip(0.42 / max(px.mean(), 0.03), 1.0, 3.0))
        ca = ob.data.color_attributes["Col"]
        d = np.zeros(len(ca.data) * 4)
        ca.data.foreach_get("color", d)
        d = d.reshape(-1, 4)
        d[:, :3] = np.clip(d[:, :3] * gain, 0.0, 1.0)
        ca.data.foreach_set("color", d.ravel())
        print("  D %s: texture mean=%.3f -> vertex-colour gain x%.2f" % (key, px.mean(), gain))
        ob.data.materials.clear()
        ob.data.materials.append(mm)
        ob.data.polygons.foreach_set("material_index", [0] * len(ob.data.polygons))
        # hearth coals must stay emissive
        if key == "village":
            ob.data.materials.append(mats["emit"])
            cls = face_classes(ob.data)
            mi = np.where(cls == EMIT, 1, 0).astype(np.int32)
            ob.data.polygons.foreach_set("material_index", mi)


def add_cameras(sc, F, charpos, tg, style):
    px, py, pz = charpos
    cams = {}

    # 1) chase cam — the runtime's own rig: 42deg vertical FOV, dist 16, pitch 0.62rad
    d, pitch = 16.0, 0.62
    tx, ty, tz = px, py, pz + 1.0
    cx = tx - tg[0] * d * math.cos(pitch)
    cy = ty - tg[1] * d * math.cos(pitch)
    cz = tz + d * math.sin(pitch)
    cams["chase"] = ((cx, cy, cz), (tx, ty, tz), 42.0, "V")

    # 2) vista — the whole tile from the lit (south-west) side, high enough that the
    #    tile's cut edge is a thin band rather than a wall
    cams["vista"] = ((-34.0, -124.0, 112.0), (6.0, 6.0, 4.0), 56.0, "H")

    # 3) village approach at ground level, coming up the road
    vx, vy = L.VILLAGE
    ax, ay, az, atg = F.road_point(0.185)
    cams["village"] = ((ax + atg[0] * 1.0 - atg[1] * 2.6, ay + atg[1] * 1.0 + atg[0] * 2.6,
                        az + 2.9), (vx, vy, F.village_h + 0.8), 42.0, "V")

    for name, (pos, aim, fov, fit) in cams.items():
        nm = "cam_%s__%s" % (name, style)
        cd = bpy.data.cameras.new(nm)
        cd.sensor_fit = "VERTICAL" if fit == "V" else "HORIZONTAL"
        if fit == "V":
            cd.angle_y = math.radians(fov)
        else:
            cd.angle_x = math.radians(fov)
        cd.clip_start, cd.clip_end = 0.05, 900.0
        ob = bpy.data.objects.new(nm, cd)
        sc.collection.objects.link(ob)
        ob.location = Vector(pos)
        ob.rotation_euler = (Vector(aim) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        if name == "chase":
            sc.camera = ob
    return cams


# ------------------------------------------------------------------------ main
def main():
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    print("building field…")
    F = L.Field()
    print("  terrain %dx%d  village_h=%.2f  clifftown_h=%.2f  bridge@%s"
          % (L.NX, L.NY, F.village_h, F.clifftown_h, F.road[F.bridge_i].round(1)))

    base_sc = bpy.data.scenes[0]
    base_sc.name = "BASE"
    base_col = bpy.data.collections.new("base_geo")
    base_sc.collection.children.link(base_col)
    objs = build_base(F, base_col)

    tot = 0
    for k, o in objs.items():
        if not k.startswith("_") and o.type == "MESH":
            n = sum(len(p.vertices) - 2 for p in o.data.polygons)
            tot += n
            print("  %-12s %6d tris" % (o.name, n))
    print("BASE TOTAL %d tris" % tot)

    for s in STYLES:
        print("style %s…" % s)
        make_scene(s, objs, F)

    # keep the base geometry out of every style scene (it is the master copy)
    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("SAVED", OUT_BLEND)


# round 2 (overworld2_build.py) IMPORTS this module for the shared field, the Prop
# accumulator and build_base(), so the two rounds cannot drift apart.  Guarding main()
# is what makes that legal — under `Blender -P` __name__ is "__main__", so the round-1
# build still runs exactly as before.
if __name__ == "__main__":
    main()
