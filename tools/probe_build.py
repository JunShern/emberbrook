"""Dellhollow Boatyard quality probe.

One corner of the town built to the pilot-slice bar, to prove a RAW Cycles
render can carry presentation quality on its own.

Local axes: +Y is upstream (the camera looks up-gorge), +Z up, cliff on -X.
Composition: hulls loom in the near/mid ground, Lock Four's gates close the
background, cliff walls frame both sides, warm sun rakes down-gorge.
"""
import bpy, bmesh, math, random
from mathutils import Matrix, Vector, Euler, noise

KITLIB = "/Users/junshernchan/projects/multiplayer-rpg/tools/blends/kitlib.blend"
R = random.Random(4242)


# ------------------------------------------------------------------ helpers

def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def append_from_kit(names):
    """Append kit objects BY NAME -- this is the contract other agents rely on.

    Uses bpy.data.libraries.load rather than bpy.ops.wm.append: the operator
    needs a UI context and fails outright in a headless/MCP session.
    """
    want = [n for n in names if bpy.data.objects.get(n) is None]
    with bpy.data.libraries.load(KITLIB, link=False) as (src, dst):
        avail = [n for n in want if n in src.objects]
        missing = sorted(set(want) - set(avail))
        if missing:
            raise RuntimeError("not in kitlib: %s" % missing)
        dst.objects = avail
        # pull the WHOLE material library too -- an appended object only drags
        # in the materials it happens to use, and the probe needs the rest
        # (mat_water, mat_tar, mat_rock, ...) which no kit piece references.
        dst.materials = [m for m in src.materials
                         if bpy.data.materials.get(m) is None]
    got = {n: bpy.data.objects.get(n) for n in names}
    src_c = coll("KIT_SOURCE")
    for o in got.values():
        if o is not None and o.name not in src_c.objects:
            src_c.objects.link(o)
    # re-establish the lantern's child light (parenting is not implied by name)
    lamp, lit = got.get("kit_lantern_hanging"), got.get("kit_lantern_light")
    if lamp and lit:
        lit.parent = lamp
    bad = [n for n, o in got.items() if o is None]
    if bad:
        raise RuntimeError("kitlib append failed for: %s" % bad)
    return got


def M(name):
    return bpy.data.materials.get(name)


def place(src, loc, rot=(0, 0, 0), c=None, jitter=0.0):
    """Linked duplicate (shares mesh data) with optional random yaw/tilt."""
    o = src.copy()
    if jitter:
        rot = (rot[0] + R.uniform(-jitter, jitter),
               rot[1] + R.uniform(-jitter, jitter),
               rot[2] + R.uniform(-jitter, jitter))
    o.location = loc
    o.rotation_euler = rot
    (c or coll("PROBE")).objects.link(o)
    return o


def place_lantern(src, loc, c=None, energy=55.0):
    """The lantern's point light is a child object, so copy both."""
    o = place(src, loc, c=c)
    for ch in src.children:
        lc = ch.copy()
        lc.data = ch.data.copy()
        lc.data.energy = energy
        (c or coll("PROBE")).objects.link(lc)
        lc.parent = o
        lc.matrix_parent_inverse = o.matrix_world.inverted()
    return o


class Mesh:
    """Direct bmesh accumulator (same approach as the kit builder)."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, mat):
        names = [m.name for m in self.mats]
        if mat.name not in names:
            self.mats.append(mat)
            return len(self.mats) - 1
        return names.index(mat.name)

    def stamp(self, verts, mat, mtx):
        idx = self.mi(mat)
        verts = [v for v in verts if isinstance(v, bmesh.types.BMVert)]
        faces = {f for v in verts for f in v.link_faces}
        bmesh.ops.transform(self.bm, matrix=mtx, verts=verts)
        for f in faces:
            f.material_index = idx

    def box(self, center, half, mat, rot=(0, 0, 0), jitter=0.0):
        if jitter:
            rot = tuple(r + R.uniform(-jitter, jitter) for r in rot)
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        self.stamp(res["verts"], mat,
                   Matrix.Translation(center)
                   @ Euler(rot, "XYZ").to_matrix().to_4x4()
                   @ Matrix.Diagonal((half[0] * 2, half[1] * 2, half[2] * 2, 1.0)))

    def cyl(self, center, r, depth, mat, seg=14, rot=(0, 0, 0), r2=None):
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False,
                                    segments=seg, radius1=r,
                                    radius2=r if r2 is None else r2, depth=depth)
        self.stamp(res["verts"], mat,
                   Matrix.Translation(center) @ Euler(rot, "XYZ").to_matrix().to_4x4())

    def quad_strip(self, rows, mat):
        """rows: list of equal-length vertex-position lists -> lofted surface."""
        idx = self.mi(mat)
        vs = [[self.bm.verts.new(p) for p in row] for row in rows]
        for i in range(len(vs) - 1):
            for j in range(len(vs[0]) - 1):
                try:
                    f = self.bm.faces.new((vs[i][j], vs[i + 1][j],
                                           vs[i + 1][j + 1], vs[i][j + 1]))
                    f.material_index = idx
                except ValueError:
                    pass

    def finish(self, c, bevel=0.01, seg=2, shade_smooth=False):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=list(self.bm.verts), dist=1e-5)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        c.objects.link(ob)
        if bevel:
            md = ob.modifiers.new("bev", "BEVEL")
            md.width = bevel
            md.segments = seg
            md.limit_method = "ANGLE"
            md.angle_limit = math.radians(40)
        for p in me.polygons:
            p.use_smooth = shade_smooth
        return ob


# --------------------------------------------------------------------- hull

def hull_section(t, s, L, B, D, rocker):
    """Point on the hull surface.
    t in [-0.5,0.5] along length, s in [0,1] keel->sheer. Double-ended shape."""
    taper = max(0.0, 1.0 - (2 * t) ** 2) ** 0.55      # pointed stem and stern
    hw = B * taper
    keel_z = rocker * (2 * t) ** 2
    x = hw * math.sin(s * math.pi / 2)
    z = keel_z + D * (1 - math.cos(s * math.pi / 2))
    return x, t * L, z


def build_hull(name, c, L=7.6, B=1.15, D=1.35, rocker=0.55, strakes=7,
               stations=26, repaired=(3, 4)):
    """Clinker-built hull: each strake is its own lapped strip, alternately
    proud of its neighbour, so the planking steps the way real lapstrake does.
    A couple of strakes use fresh timber -- the visible repair."""
    m = Mesh(name)
    old, new = M("mat_deck"), M("mat_wallwood_dark")
    ts = [(-0.5 + i / (stations - 1)) for i in range(stations)]
    for k in range(strakes):
        s0, s1 = k / strakes, (k + 1) / strakes
        lip = 0.045 if k % 2 == 0 else 0.0        # the clinker step
        mat = new if k in repaired else old
        for side in (1, -1):
            rows = []
            for t in ts:
                row = []
                for s in (s0, s1):
                    x, y, z = hull_section(t, s, L, B, D, rocker)
                    nx = math.sin(s * math.pi / 2 + 0.35)
                    row.append((side * (x + lip * nx), y, z - lip * 0.15))
                rows.append(row)
            if side == -1:
                rows = [r[::-1] for r in rows]
            m.quad_strip(rows, mat)
    # keel, stem and stern posts
    m.box((0, 0, rocker * 0.12), (0.085, L * 0.47, 0.11), M("mat_timber"))
    for e in (-1, 1):
        m.box((0, e * L * 0.47, D * 0.42), (0.075, 0.16, D * 0.5), M("mat_timber"),
              rot=(e * 0.30, 0, 0))
    # gunwale rail
    for side in (1, -1):
        rows = []
        for t in ts:
            x, y, z = hull_section(t, 1.0, L, B, D, rocker)
            rows.append([(side * x, y, z), (side * (x + 0.07), y, z - 0.055)])
        m.quad_strip(rows, M("mat_timber"))
    return m.finish(c, bevel=0.006, shade_smooth=True)


def build_hull_frames(name, c, L=7.0, B=1.10, D=1.30, rocker=0.5, nribs=13):
    """The second hull: ribbed skeleton only -- keel, stem/stern, and bare frames."""
    m = Mesh(name)
    tb = M("mat_timber")
    m.box((0, 0, rocker * 0.12), (0.09, L * 0.47, 0.12), tb)
    for e in (-1, 1):
        m.box((0, e * L * 0.46, D * 0.45), (0.08, 0.15, D * 0.55), tb, rot=(e * 0.32, 0, 0))
    for i in range(nribs):
        t = -0.42 + 0.84 * i / (nribs - 1)
        for side in (1, -1):
            pts = []
            for j in range(9):
                s = j / 8
                x, y, z = hull_section(t, s, L, B, D, rocker)
                pts.append(Vector((side * x, y, z)))
            for a, b in zip(pts[:-1], pts[1:]):
                mid = (a + b) / 2
                d = b - a
                if d.length < 1e-4:
                    continue
                rot = d.to_track_quat("Z", "Y").to_euler()
                m.cyl(mid, 0.055, d.length * 1.15, tb, seg=6,
                      rot=(rot.x, rot.y, rot.z))
    # a couple of stringers running fore-aft over the frames
    for s in (0.45, 0.8):
        for side in (1, -1):
            rows = []
            for i in range(nribs):
                t = -0.42 + 0.84 * i / (nribs - 1)
                x, y, z = hull_section(t, s, L, B, D, rocker)
                rows.append([(side * x, y, z), (side * x, y, z - 0.09)])
            m.quad_strip(rows, tb)
    return m.finish(c, bevel=0.004, shade_smooth=True)


# ------------------------------------------------------------------ terrain

def build_cliff(name, c, origin, size, height, seed, facing=1, mat="mat_rock",
                ragged=0.0):
    """Displaced rock wall. Real relief, so it catches the raking sun."""
    m = Mesh(name)
    nx, ny = 26, 34
    rows = []
    for i in range(ny):
        v = i / (ny - 1)
        row = []
        y = origin[1] + (v - 0.5) * size
        # vary the crest height along the wall. Without this the displacement
        # only moves the face in and out and the skyline stays a dead-straight
        # horizontal edge, which reads as wallpaper rather than a ridge.
        hs = 1.0
        if ragged:
            hs = 1.0 - ragged * (0.5 + 0.5 * noise.noise(
                Vector((y * 0.055, seed * 3.7, 0.0))))
        for j in range(nx):
            u = j / (nx - 1)
            z = origin[2] + u * height * hs
            n1 = noise.noise(Vector((y * 0.11, z * 0.11, seed)))
            n2 = noise.noise(Vector((y * 0.38, z * 0.38, seed + 5))) * 0.35
            n3 = noise.noise(Vector((y * 1.1, z * 1.1, seed + 9))) * 0.12
            d = (n1 + n2 + n3) * 3.4
            # pull the base in so the wall leans out over the water
            d += (1.0 - u) * -1.6
            row.append((origin[0] + facing * d, y, z))
        rows.append(row)
    m.quad_strip(rows, M(mat))
    return m.finish(c, bevel=0, shade_smooth=True)


def build_water(name, c, center, size, z, flat=False):
    m = Mesh(name)
    if flat:
        # single quad: a box would present a vertical near face that catches the
        # sun and reads as a bright card wherever the gates don't occlude it
        hx, hy = size[0] / 2, size[1] / 2
        m.quad_strip([[(center[0] - hx, center[1] - hy, z),
                       (center[0] - hx, center[1] + hy, z)],
                      [(center[0] + hx, center[1] - hy, z),
                       (center[0] + hx, center[1] + hy, z)]], M("mat_water"))
    else:
        m.box((center[0], center[1], z - 1.0),
              (size[0] / 2, size[1] / 2, 1.0), M("mat_water"))
    return m.finish(c, bevel=0)


# ------------------------------------------------------------------- boatyard

def build_slipway(c):
    """Planked ramp descending into the water, with cross sleepers and rails."""
    m = Mesh(name := "slipway")
    dk, tb, wet = M("mat_deck"), M("mat_timber"), M("mat_wet")
    y0, z0 = -15.0, 3.1        # top of the ramp
    y1, z1 = 3.0, -0.5         # under the water
    n = 34
    for i in range(n):
        f0, f1 = i / n, (i + 1) / n
        ya, za = y0 + (y1 - y0) * f0, z0 + (z1 - z0) * f0
        yb, zb = y0 + (y1 - y0) * f1, z0 + (z1 - z0) * f1
        mat = wet if za < 1.4 else dk
        m.box(((ya + yb) / 2 * 0 + 0, (ya + yb) / 2, (za + zb) / 2),
              (4.2, abs(yb - ya) / 2 - 0.02, 0.075), mat, jitter=0.006)
    # cross sleepers the keel rides on
    for i in range(11):
        f = i / 10
        y = y0 + (y1 - y0) * f * 0.86
        z = z0 + (z1 - z0) * f * 0.86
        mat = wet if z < 1.4 else tb
        m.box((0, y, z + 0.13), (4.4, 0.16, 0.09), mat, jitter=0.01)
    return m.finish(c, bevel=0.01)


def build_deck_platform(c):
    """The yard's working deck around the slipway head, on stilts."""
    m = Mesh("yard_deck")
    dk, tb = M("mat_deck"), M("mat_timber")
    for (x0, x1, y0, y1) in [(-11.5, -4.2, -19.0, -6.0), (4.2, 12.0, -19.0, -6.0),
                             (-11.5, 12.0, -22.5, -19.0)]:
        nx = max(1, int((x1 - x0) / 0.26))
        for i in range(nx):
            x = x0 + (x1 - x0) * (i + 0.5) / nx
            m.box((x, (y0 + y1) / 2, 3.06), ((x1 - x0) / nx / 2 - 0.008,
                                             (y1 - y0) / 2, 0.07), dk, jitter=0.005)
        for yy in [y0 + 1.0, (y0 + y1) / 2, y1 - 1.0]:
            m.box(((x0 + x1) / 2, yy, 2.86), ((x1 - x0) / 2, 0.13, 0.16), tb)
    return m.finish(c, bevel=0.012)


def build_shed(c, origin=(8.4, -11.0, 3.1)):
    """Boatwright's shed: timber walls, shingle roof, lean-to, tool clutter."""
    m = Mesh("boat_shed")
    ww, tb, sh = M("mat_wallwood"), M("mat_timber"), M("mat_shingle")
    ox, oy, oz = origin
    W, Dp, H = 5.0, 6.4, 3.2
    # cladding
    for (ax, sgn) in [(0, 1), (0, -1)]:
        nb = int(Dp / 0.28)
        for i in range(nb):
            y = oy - Dp / 2 + Dp * (i + 0.5) / nb
            m.box((ox + sgn * W / 2, y, oz + H / 2),
                  (0.06, Dp / nb / 2 - 0.008, H / 2), ww, jitter=0.01)
    nb = int(W / 0.28)
    for i in range(nb):
        x = ox - W / 2 + W * (i + 0.5) / nb
        m.box((x, oy - Dp / 2, oz + H / 2), (W / nb / 2 - 0.008, 0.06, H / 2),
              ww, jitter=0.01)
        m.box((x, oy + Dp / 2, oz + H * 0.32), (W / nb / 2 - 0.008, 0.06, H * 0.32),
              ww, jitter=0.01)   # rear wall, open above for the doorway
    # corner posts + plates
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((ox + sx * W / 2, oy + sy * Dp / 2, oz + H / 2),
                  (0.11, 0.11, H / 2), tb)
    for sy in (-1, 1):
        m.box((ox, oy + sy * Dp / 2, oz + H), (W / 2, 0.1, 0.11), tb)
    # gable roof, shingled in courses
    pitch = 1.5
    for side in (1, -1):
        L = math.hypot(W / 2 + 0.35, pitch)
        ang = math.atan2(pitch, W / 2 + 0.35)
        cx = ox + side * (W / 4 + 0.18)
        cz = oz + H + pitch / 2
        m.box((cx, oy, cz), (L / 2, Dp / 2 + 0.4, 0.06), tb, rot=(0, -side * ang, 0))
        rows = 7
        for r in range(rows):
            f = (r + 0.5) / rows
            px = ox + side * (W / 2 + 0.35) * (1 - f)
            pz = oz + H + pitch * f
            m.box((px, oy, pz + 0.05), ((L / rows) * 0.62, Dp / 2 + 0.45, 0.028), sh,
                  rot=(0, -side * ang, 0), jitter=0.005)
    m.box((ox, oy, oz + H + pitch + 0.03), (0.13, Dp / 2 + 0.45, 0.09), tb)  # ridge
    # lean-to work bench on the slipway side
    m.box((ox - W / 2 - 0.9, oy - 1.2, oz + 0.95), (0.85, 1.5, 0.06), M("mat_deck"))
    for sy in (-1, 1):
        m.box((ox - W / 2 - 1.6, oy - 1.2 + sy * 1.35, oz + 0.47),
              (0.07, 0.07, 0.47), tb)
    # tool clutter: leaning planks and spars
    for i in range(7):
        m.box((ox - W / 2 - 0.35 + R.uniform(-0.1, 0.1), oy + R.uniform(-2.4, 2.4),
               oz + 1.25), (0.05, 0.13, 1.3), M("mat_deck"),
              rot=(0, R.uniform(0.10, 0.22), R.uniform(-0.1, 0.1)))
    return m.finish(c, bevel=0.012)


def build_pitch_kettle(c, loc=(-3.2, -13.4, 3.1)):
    """Iron kettle of tar over a stone hearth, with a lit fire underneath."""
    m = Mesh("pitch_kettle")
    ir, tar, rk = M("mat_iron"), M("mat_tar"), M("mat_rock")
    x, y, z = loc
    for i in range(9):                                   # hearth stones
        a = i / 9 * math.tau
        m.box((x + math.cos(a) * 0.62, y + math.sin(a) * 0.62, z + 0.13),
              (0.19, 0.19, 0.15), rk, rot=(0, 0, a), jitter=0.25)
    m.cyl((x, y, z + 0.62), 0.62, 0.66, ir, seg=18, r2=0.52)   # kettle
    m.cyl((x, y, z + 0.90), 0.66, 0.09, ir, seg=18)            # rim
    m.cyl((x, y, z + 0.905), 0.55, 0.03, tar, seg=18)          # tar surface
    for sx in (-1, 1):                                          # trivet legs
        for sy in (-1, 1):
            m.box((x + sx * 0.42, y + sy * 0.42, z + 0.16), (0.045, 0.045, 0.16), ir)
    ob = m.finish(c, bevel=0.01)

    # embers + smoke
    fire = bpy.data.lights.new("kettle_fire", "POINT")
    fire.energy = 42.0
    fire.color = (1.0, 0.42, 0.13)
    fire.shadow_soft_size = 0.25
    fo = bpy.data.objects.new("kettle_fire", fire)
    fo.location = (x, y, z + 0.30)
    c.objects.link(fo)

    sm = Mesh("kettle_smoke")
    sm.box((x, y, z + 3.0), (1.5, 1.5, 2.4), M("mat_smoke"))
    so = sm.finish(c, bevel=0)
    so.visible_shadow = False
    return ob


def build_lock_gates(c, y=27.0, top_z=3.6):
    """Lock Four: tall timber gates upstream, water standing higher behind them."""
    m = Mesh("lock_four")
    tb, ir = M("mat_timber"), M("mat_iron")
    for side in (-1, 1):
        cx = side * 3.1
        for i in range(9):                              # vertical gate planks
            xx = cx + (i - 4) * 0.66 * 1.0
            if abs(xx) < 0.35:
                continue
            m.box((xx, y, top_z / 2 + 1.3), (0.31, 0.14, top_z / 2 + 1.3), tb,
                  jitter=0.006)
        for zz in (1.1, 3.0, 4.6):                      # iron straps
            m.box((cx, y - 0.16, zz), (2.95, 0.05, 0.13), ir)
        m.box((cx, y - 0.2, 3.0), (2.9, 0.06, 0.11), ir,
              rot=(0, math.radians(-18) * side, 0))
    # masonry abutments either side
    for side in (-1, 1):
        m.box((side * 8.4, y, 3.2), (2.6, 1.3, 3.2), M("mat_rock"))
    # sill / walkway across the top
    m.box((0, y, 5.05), (9.0, 0.55, 0.16), M("mat_deck"))
    return m.finish(c, bevel=0.012)


def build_boardwalk_rail(c):
    """Railing along the front edge of the yard deck, framing the low camera."""
    kit = bpy.data.objects["kit_railing_1m"]
    made = []
    # run the rails up both edges of the slipway so they act as leading lines
    # driving the eye from the foreground into the hulls and the lock gates
    for side in (-1, 1):
        for i in range(12):
            y = -19.0 + i * 1.0
            made.append(place(kit, (side * 4.35, y, 3.12),
                              rot=(0, 0, math.pi / 2), c=c, jitter=0.02))
    # short return along the very front edge, outboard of the slipway
    for i in range(6):
        made.append(place(kit, (-11.0 + i * 1.0, -19.2, 3.12), c=c, jitter=0.02))
    for i in range(6):
        made.append(place(kit, (5.4 + i * 1.0, -19.2, 3.12), c=c, jitter=0.02))
    return made


# --------------------------------------------------------------------- extra

def extra_materials():
    """Probe-only materials: wet timber near the waterline, and smoke."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "km", "/Users/junshernchan/projects/multiplayer-rpg/tools/kit_materials.py")
    km = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(km)

    # wet planks: same texture as the deck but darker and far glossier
    wet = km.make_tex_mat("mat_deck", scale=1.0, moss=0.7,
                          moss_color=(0.055, 0.09, 0.045),
                          rough_lo=0.06, rough_hi=0.30, darken=0.35,
                          normal_strength=1.3)
    wet.name = "mat_wet"

    # rebuild mat_deck (make_tex_mat reused the datablock we just renamed)
    km.make_tex_mat("mat_deck", scale=1.0, moss=0.55, rough_lo=0.55,
                    darken=0.62, normal_strength=1.2)

    far = km.make_tex_mat("mat_rock", scale=0.05, moss=0.25, rough_lo=0.7,
                          darken=0.36, tint=(0.40, 0.41, 0.47), tint_fac=0.7,
                          normal_strength=0.35)
    far.name = "mat_rock_far"
    km.make_tex_mat("mat_rock", scale=0.17, moss=0.45, rough_lo=0.55,
                    darken=0.72, normal_strength=1.3)

    sp = bpy.data.materials.get("mat_spray") or bpy.data.materials.new("mat_spray")
    sp.use_nodes = True
    spt = sp.node_tree
    spt.nodes.clear()
    spo = spt.nodes.new("ShaderNodeOutputMaterial")
    spv = spt.nodes.new("ShaderNodeVolumeScatter"); spv.location = (-200, 0)
    spv.inputs["Color"].default_value = (0.78, 0.85, 0.88, 1)
    spv.inputs["Density"].default_value = 0.011
    spt.links.new(spv.outputs["Volume"], spo.inputs["Volume"])

    sm = bpy.data.materials.get("mat_smoke") or bpy.data.materials.new("mat_smoke")
    sm.use_nodes = True
    nt = sm.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled"); pv.location = (-200, 0)
    pv.inputs["Color"].default_value = (0.09, 0.08, 0.075, 1)
    pv.inputs["Density"].default_value = 0.0
    nt.links.new(pv.outputs["Volume"], out.inputs["Volume"])
    # noise-driven density so the plume has structure and fades upward
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1100, -200)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.location = (-900, -200)
    nz.inputs["Scale"].default_value = 1.7
    nz.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-900, 120)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    fall = nt.nodes.new("ShaderNodeMapRange"); fall.location = (-700, 120)
    fall.inputs["From Min"].default_value = 0.15
    fall.inputs["From Max"].default_value = 1.0
    fall.inputs["To Min"].default_value = 1.0
    fall.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], fall.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    mul.location = (-480, 0)
    nt.links.new(nz.outputs["Fac"], mul.inputs[0])
    nt.links.new(fall.outputs["Result"], mul.inputs[1])
    amt = nt.nodes.new("ShaderNodeMath"); amt.operation = "MULTIPLY"
    amt.location = (-330, 0); amt.inputs[1].default_value = 0.55
    nt.links.new(mul.outputs["Value"], amt.inputs[0])
    nt.links.new(amt.outputs["Value"], pv.inputs["Density"])
    return wet, sm


def build_foreground_clutter(c, kit):
    """The near deck was reading as an empty plank field across the bottom of
    frame. A working yard has stuff underfoot -- this gives the eye something
    to land on before it travels into the scene."""
    m = Mesh("yard_clutter")
    dk, tb = M("mat_deck"), M("mat_timber")
    # stack of sawn planks, slightly splayed
    for i in range(7):
        m.box((-2.9 + R.uniform(-0.04, 0.04), -15.4, 2.72 + i * 0.075),
              (0.30, 1.45, 0.036), dk, rot=(0, 0, R.uniform(-0.03, 0.03)))
    for i in range(4):
        m.box((-2.4 + R.uniform(-0.06, 0.06), -15.1, 3.25 + i * 0.075),
              (0.26, 1.15, 0.036), dk, rot=(0, 0, R.uniform(-0.05, 0.05)))
    # trestle the planks are being sawn on
    for yy in (-16.6, -14.2):
        m.box((2.7, yy, 2.98), (0.55, 0.07, 0.07), tb)
        for sx in (-1, 1):
            m.box((2.7 + sx * 0.45, yy, 2.75), (0.05, 0.05, 0.26), tb,
                  rot=(0, sx * 0.22, 0))
    m.box((2.72, -15.4, 3.08), (0.42, 1.3, 0.045), dk, rot=(0.01, 0.0, 0.02))
    # discarded offcuts and a leaning oar
    for i in range(6):
        m.box((R.uniform(-3.6, 3.4), R.uniform(-17.6, -13.0), 2.72),
              (R.uniform(0.06, 0.14), R.uniform(0.22, 0.5), 0.026), dk,
              rot=(0, 0, R.uniform(0, 3.1)))
    m.box((-4.05, -12.6, 3.85), (0.045, 0.045, 1.15), tb, rot=(0.30, 0, 0.1))
    m.box((-4.13, -12.28, 4.92), (0.075, 0.015, 0.34), dk, rot=(0.30, 0, 0.1))
    ob = m.finish(c, bevel=0.008)

    place(kit["kit_rope_coil"], (-1.55, -16.9, 2.74), c=c, jitter=0.12)
    place(kit["kit_barrel"], (3.35, -17.4, 2.74), rot=(0, 0, 0.7), c=c, jitter=0.05)
    place(kit["kit_bucket"], (1.6, -14.2, 2.74), c=c, jitter=0.1)
    place(kit["kit_crate"], (-3.5, -17.9, 2.74), rot=(0, 0, 0.35), c=c, jitter=0.04)
    # bottom-right of frame was empty deck -- give it working clutter too
    place(kit["kit_barrel"], (5.2, -18.6, 3.14), rot=(0, 0, 1.2), c=c, jitter=0.05)
    place(kit["kit_crate"], (7.0, -19.4, 3.14), rot=(0, 0, 0.6), c=c, jitter=0.04)
    place(kit["kit_rope_coil"], (4.6, -17.2, 3.14), c=c, jitter=0.12)
    place(kit["kit_bucket"], (8.1, -17.6, 3.14), c=c, jitter=0.1)
    return ob


def build_pilings(c):
    """Mooring pilings marching up-gorge.

    The midground between the hulls and the gates was a large flat sheet of
    empty water. A receding line of pilings fills it, gives the eye leading
    lines into the background, and reinforces the depth layering."""
    m = Mesh("pilings")
    tb, wet = M("mat_timber"), M("mat_wet")
    spec = [(-6.6, 1.5, 3.3), (-6.2, 6.0, 3.0), (-5.6, 11.0, 2.7),
            (7.4, 0.5, 3.5), (7.9, 5.5, 3.2), (8.3, 11.5, 2.9),
            (9.0, 18.0, 2.6), (-5.0, 17.0, 2.4)]
    for (x, y, h) in spec:
        lean = R.uniform(-0.05, 0.05)
        m.cyl((x, y, 0.2 + h / 2), 0.20, h, tb, seg=10,
              rot=(lean, R.uniform(-0.05, 0.05), 0))
        m.cyl((x, y, 0.45), 0.225, 1.1, wet, seg=10)      # wet, weedy at the waterline
        m.box((x, y, 0.2 + h + 0.04), (0.26, 0.26, 0.06), tb, jitter=0.05)
    # a couple of cross-braced pairs
    for (x, y) in [(-6.4, 3.6), (7.65, 3.0)]:
        m.box((x, y, 2.3), (0.09, 2.3, 0.09), tb, jitter=0.03)
    ob = m.finish(c, bevel=0.01)
    return ob


def build_gate_spray(c, y=27.0):
    """Mist at the foot of Lock Four -- sells the 'staircase of water' and gives
    the far plane something luminous to separate the gates from the cliffs."""
    m = Mesh("gate_spray")
    m.box((0, y - 1.8, 2.0), (9.0, 1.8, 2.2), M("mat_spray"))
    ob = m.finish(c, bevel=0)
    ob.visible_shadow = False
    return ob


# ------------------------------------------------------------------ assembly

KIT_NAMES = ["kit_barrel", "kit_crate", "kit_rope_coil", "kit_bucket",
             "kit_lantern_hanging", "kit_lantern_light",
             "kit_railing_1m", "kit_railing_post",
             "kit_beam", "kit_stilt_trestle", "REF_human_1p7",
             "SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX"]


def build_lantern_posts(c, spots):
    m = Mesh("lantern_posts")
    tb = M("mat_timber")
    for (x, y, z) in spots:
        m.box((x, y, z + 1.6), (0.095, 0.095, 1.6), tb, jitter=0.01)
        m.box((x + 0.42, y, z + 3.05), (0.42, 0.06, 0.06), tb)
        m.box((x + 0.14, y, z + 2.78), (0.28, 0.05, 0.05), tb,
              rot=(0, math.radians(42), 0))
    return m.finish(c, bevel=0.008)


def scatter_props(c, kit):
    ref = []
    barrels = [(-5.4, -15.6, 3.13, 0.4), (-6.3, -16.4, 3.13, 1.1),
               (5.6, -14.2, 3.13, 0.2), (6.5, -15.0, 3.13, 2.0),
               (-5.9, -10.2, 3.13, 0.8), (6.1, -9.4, 3.13, 1.4)]
    for x, y, z, rz in barrels:
        ref.append(place(kit["kit_barrel"], (x, y, z), rot=(0, 0, rz), c=c, jitter=0.05))
    crates = [(-6.6, -18.2, 3.13, 0.5), (-6.2, -18.4, 3.87, 0.9),
              (5.5, -17.6, 3.13, 0.25), (7.4, -11.6, 3.13, 1.3)]
    for x, y, z, rz in crates:
        ref.append(place(kit["kit_crate"], (x, y, z), rot=(0, 0, rz), c=c, jitter=0.04))
    for x, y, z in [(-5.0, -13.1, 3.14), (5.0, -12.0, 3.14), (-7.5, -14.6, 3.14),
                    (6.9, -17.2, 3.14)]:
        ref.append(place(kit["kit_rope_coil"], (x, y, z), c=c, jitter=0.1))
    for x, y, z in [(-5.6, -17.9, 3.14), (5.9, -12.6, 3.14)]:
        ref.append(place(kit["kit_bucket"], (x, y, z), c=c, jitter=0.08))
    return ref


def build_scene():
    c = coll("PROBE")
    kit = append_from_kit(KIT_NAMES)
    extra_materials()
    # staging collection holds the pristine originals; exclude from the render
    vl = bpy.context.view_layer.layer_collection.children.get("KIT_SOURCE")
    if vl:
        vl.exclude = True

    # --- terrain / water -------------------------------------------------
    build_water("water_lower", c, (0, -8, 0), (240, 200), 0.2)
    build_water("water_upper", c, (0, 90, 0), (240, 124), 3.6, flat=True)
    build_cliff("cliff_port", c, (-13.0, -2.0, -2.0), 62, 30, 1.7, facing=1)
    build_cliff("cliff_stbd", c, (17.5, -2.0, -2.0), 62, 30, 8.3, facing=-1)
    # two ragged ridge lines at different depths -> aerial perspective, with
    # real sky visible in the notches between crests
    build_cliff("cliff_back", c, (0.0, 0.0, -6.0), 170, 36, 3.1, facing=1,
                mat="mat_rock_far", ragged=0.45)
    bcl = bpy.data.objects["cliff_back"]
    bcl.rotation_euler = (0, 0, math.radians(90))
    bcl.location = (14, 132, 0)
    build_cliff("cliff_back2", c, (0.0, 0.0, -6.0), 140, 28, 6.7, facing=1,
                mat="mat_rock_far", ragged=0.55)
    b2 = bpy.data.objects["cliff_back2"]
    b2.rotation_euler = (0, 0, math.radians(90))
    b2.location = (-24, 88, 0)

    # --- the yard --------------------------------------------------------
    build_slipway(c)
    build_deck_platform(c)
    build_shed(c)
    build_pitch_kettle(c, loc=(-6.4, -12.6, 3.13))
    build_lock_gates(c, y=27.0)
    build_boardwalk_rail(c)

    # stilts holding the deck over the water
    for x, y in [(-10.0, -8.0), (-10.0, -16.0), (10.0, -8.0), (10.0, -16.0),
                 (-6.0, -21.0), (6.0, -21.0), (12.0, -20.0)]:
        place(kit["kit_stilt_trestle"], (x, y, -1.0), c=c, jitter=0.02)

    # --- hulls -----------------------------------------------------------
    ramp_ang = math.atan2(3.6, 18.0)
    hull = build_hull("hull_clinker", c)
    hull.location = (0.9, -9.5, 2.18)
    hull.rotation_euler = (-ramp_ang, 0.06, 0.035)

    frames = build_hull_frames("hull_frames", c)
    # second hull down at the water's edge, mid-haul -- gives a third depth layer
    frames.location = (-2.5, -1.6, 0.72)
    frames.rotation_euler = (-ramp_ang, 0.04, 0.16)
    blocks = Mesh("hull_blocks")
    for yy in (-2.4, -0.4, 1.9):
        blocks.box((-2.5 + yy * 0.16, -1.6 + yy, 0.42 - yy * 0.2), (0.85, 0.2, 0.22),
                   M("mat_timber"), jitter=0.03)
    blocks.finish(c, bevel=0.01)

    # shores propping the clinker hull against the ramp
    sh = Mesh("hull_shores")
    for sx in (-1, 1):
        for yy in (-1.9, 1.4):
            sh.box((sx * 2.15, -9.5 + yy, 2.62), (0.08, 0.08, 1.15),
                   M("mat_timber"), rot=(0, sx * 0.55, 0), jitter=0.04)
    sh.finish(c, bevel=0.01)

    # --- props and practicals -------------------------------------------
    scatter_props(c, kit)
    build_foreground_clutter(c, kit)
    build_gate_spray(c)
    build_pilings(c)
    posts = [(-4.9, -17.4, 3.13), (4.9, -14.4, 3.13), (-5.1, -8.6, 3.13)]
    build_lantern_posts(c, posts)
    for (x, y, z) in posts:
        place_lantern(kit["kit_lantern_hanging"], (x + 0.42, y, z + 2.92),
                      c=c, energy=150)
    # lanterns under the shed eave
    for y in (-13.6, -8.6):
        place_lantern(kit["kit_lantern_hanging"], (5.55, y, 5.85), c=c, energy=130)

    # 1.7u scale reference, kept to a corner of frame
    r = kit["REF_human_1p7"]
    r.location = (6.4, -16.2, 3.13)
    if r.name not in c.objects:
        c.objects.link(r)
    return c


def setup_light(sun_energy=7.5, fog_density=0.0048):
    # The rig was appended into the excluded KIT_SOURCE staging collection --
    # move it into a rendered collection or nothing gets lit.
    lc = coll("PROBE_LIGHT")
    for n in ("SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX"):
        o = bpy.data.objects[n]
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        lc.objects.link(o)

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "kb", "/Users/junshernchan/projects/multiplayer-rpg/tools/kit_build.py")
    kb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kb)
    kb.setup_world(density=0.0)
    # cooler, deeper sky: the warm key only reads as warm against a cool sky,
    # and v1 went sepia because sky, fog and sun were all the same orange.
    nt = bpy.context.scene.world.node_tree
    ramp = next(n for n in nt.nodes if n.type == "VALTORGB").color_ramp
    ramp.elements[0].color = (0.30, 0.17, 0.11, 1)
    ramp.elements[1].color = (0.34, 0.28, 0.26, 1)
    ramp.elements[2].color = (0.13, 0.18, 0.30, 1)
    next(n for n in nt.nodes if n.type == "BACKGROUND").inputs["Strength"] \
        .default_value = 1.05

    sun = bpy.data.objects["SUN_key"]
    sun.location = (-22, -34, 16)
    # 3/4 key from over the camera's LEFT SHOULDER, 21 deg up. v1/v2 lit from
    # up-gorge (behind the subject), so every camera-facing plane was in shadow
    # and the frame read as a flat silhouette. Keying from behind-left instead
    # puts warm light on the hull flank and decks and throws long raking
    # shadows across the planking -- which is what models form.
    sun.rotation_euler = (math.radians(68.9), 0, math.radians(-26.8))
    sun.data.energy = sun_energy
    sun.data.color = (1.0, 0.66, 0.36)
    sun.data.angle = math.radians(2.2)

    fill = bpy.data.objects["FILL_bounce"]
    fill.location = (-15, -24, 4.0)
    fill.rotation_euler = (math.radians(78), 0, math.radians(-112))
    fill.data.energy = 190
    fill.data.size = 18.0
    fill.data.color = (0.30, 0.52, 0.66)          # cool bounce off the river

    rim = bpy.data.objects["RIM_gorge"]
    rim.location = (2, 13, 7.0)
    rim.rotation_euler = (math.radians(96), 0, math.radians(180))
    rim.data.energy = 900
    rim.data.size = 12.0
    rim.data.color = (1.0, 0.72, 0.42)

    fog = bpy.data.objects["FOG_BOX"]
    fog.location = (0, 40, 14)
    # The default 160u box spans y -66..94, which left the far ridges (y=88 and
    # y=132) OUTSIDE the fog entirely -- they rendered crisp and bright and read
    # as cardboard cutouts. Stretch the box so it actually contains them.
    fog.scale = (2.4, 2.8, 1.7)
    # near-neutral haze. A warm fog at v1 density flattened the whole frame into
    # orange soup and destroyed the depth cue it was supposed to create.
    volnode = fog.data.materials[0].node_tree.nodes["Volume Scatter"]
    volnode.inputs["Density"].default_value = fog_density
    volnode.inputs["Color"].default_value = (0.60, 0.55, 0.52, 1)
    return sun, fill, rim, fog
