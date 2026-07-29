"""Dellhollow modular kit geometry.

Human scale contract: character is 1.7u tall. Doors 2.1u, railings 1.0u,
stair rise 0.22u. Everything is built directly in bmesh at final world scale
(no object scaling) so the object-space box-projected materials keep correct
texel density. Names are the contract -- other agents append by name.
"""
import bpy, bmesh, math, random
from mathutils import Matrix, Vector, Euler

R = random.Random(20260729)


# ------------------------------------------------------------------ builder

class Part:
    """Accumulates geometry for one kit object, tracking material slots."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def _mi(self, mat):
        if mat is None:
            return 0
        if mat.name not in [m.name for m in self.mats]:
            self.mats.append(mat)
        return [m.name for m in self.mats].index(mat.name)

    def _stamp(self, verts, mat, mtx):
        """verts is the vert list returned by a bmesh primitive op; the faces of
        that primitive are exactly the faces linked to those verts."""
        idx = self._mi(mat)
        verts = [v for v in verts if isinstance(v, bmesh.types.BMVert)]
        faces = {f for v in verts for f in v.link_faces}
        bmesh.ops.transform(self.bm, matrix=mtx, verts=verts)
        for f in faces:
            f.material_index = idx

    def box(self, center, half, mat, rot=(0, 0, 0), jitter=0.0):
        """Axis box; jitter adds small random rotation so nothing is perfectly straight."""
        cx, cy, cz = center
        hx, hy, hz = half
        if jitter:
            rot = (rot[0] + R.uniform(-jitter, jitter),
                   rot[1] + R.uniform(-jitter, jitter),
                   rot[2] + R.uniform(-jitter, jitter))
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        mtx = (Matrix.Translation((cx, cy, cz))
               @ Euler(rot, "XYZ").to_matrix().to_4x4()
               @ Matrix.Diagonal((hx * 2, hy * 2, hz * 2, 1.0)))
        self._stamp(res["verts"], mat, mtx)

    def cyl(self, center, radius, depth, mat, segments=16, rot=(0, 0, 0), r2=None):
        r2 = radius if r2 is None else r2
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False,
                                    segments=segments, radius1=radius,
                                    radius2=r2, depth=depth)
        mtx = (Matrix.Translation(center)
               @ Euler(rot, "XYZ").to_matrix().to_4x4())
        self._stamp(res["verts"], mat, mtx)

    def torus(self, center, major, minor, mat, seg=20, ring=8, rot=(0, 0, 0)):
        tmp = bmesh.new()
        bmesh.ops.create_circle(tmp, cap_ends=False, segments=ring, radius=minor)
        bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
        bmesh.ops.translate(tmp, verts=tmp.verts, vec=(major, 0, 0))
        bmesh.ops.spin(tmp, geom=list(tmp.edges) + list(tmp.verts),
                       axis=(0, 0, 1), cent=(0, 0, 0), steps=seg,
                       angle=math.tau, use_merge=True)
        me = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(me)
        tmp.free()
        pre = set(self.bm.faces)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        new = [f for f in self.bm.faces if f not in pre]
        verts = list({v for f in new for v in f.verts})
        mtx = Matrix.Translation(center) @ Euler(rot, "XYZ").to_matrix().to_4x4()
        bmesh.ops.transform(self.bm, matrix=mtx, verts=verts)
        idx = self._mi(mat)
        for f in new:
            f.material_index = idx

    def finish(self, coll, bevel=0.012, segments=2, smooth=True):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=list(self.bm.verts), dist=1e-5)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        if bevel:
            md = ob.modifiers.new("bev", "BEVEL")
            md.width = bevel
            md.segments = segments
            md.limit_method = "ANGLE"
            md.angle_limit = math.radians(40)
            md.miter_outer = "MITER_ARC"
        if smooth:
            for p in me.polygons:
                p.use_smooth = False
        return ob


def M(name):
    return bpy.data.materials.get(name)


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


# ------------------------------------------------------------------- walls

def wall_frame(p, w=3.0, h=3.0, t=0.14, brace=True):
    """Timber frame: sill, head, corner posts, mid rail, diagonal brace."""
    tb = M("mat_timber")
    ht = t / 2
    inner = w / 2 - 0.18   # plates stop at the posts instead of running through
    p.box((0, 0, 0.075), (inner, ht, 0.075), tb)            # sill plate
    p.box((0, 0, h - 0.09), (inner, ht, 0.09), tb)          # head plate
    for sx in (-1, 1):                                       # full-height corner posts
        p.box((sx * (w / 2 - 0.09), 0, h / 2), (0.09, ht, h / 2), tb)
    p.box((0, 0, h * 0.52), (inner, ht * 0.8, 0.06), tb)     # mid rail
    if brace:
        L = math.hypot(w - 0.4, h - 0.4)
        # sits proud of the mid rail in Y so the crossing does not z-fight
        p.box((0, -ht * 0.9, h / 2), (L / 2, ht * 0.5, 0.055), tb,
              rot=(0, -math.atan2(h - 0.4, w - 0.4), 0))


def boards(p, w, h, t, mat, z0=0.0, bw=0.25, jitter=0.012):
    """Vertical cladding boards with gaps and slight misalignment."""
    n = max(1, int(round(w / bw)))
    step = w / n
    for i in range(n):
        x = -w / 2 + step * (i + 0.5)
        p.box((x, -t * 0.55, z0 + h / 2),
              (step / 2 - 0.008, t * 0.35, h / 2), mat,
              rot=(0, 0, 0), jitter=jitter)


def build_wall_plain(c):
    p = Part("kit_wall_plain")
    boards(p, 3.0, 3.0, 0.14, M("mat_wallwood"))
    wall_frame(p)
    return p.finish(c)


def build_wall_window(c):
    p = Part("kit_wall_window")
    w, h, t = 3.0, 3.0, 0.14
    wood = M("mat_wallwood")
    tb = M("mat_timber")
    # cladding in strips around a 1.1 x 1.2 opening centred at z=1.55
    ox, oz, ow, oh = 0.0, 1.55, 1.1, 1.2
    p.box((0, -t * 0.55, (oz - oh / 2) / 2), (w / 2, t * 0.35, (oz - oh / 2) / 2), wood)
    top0 = oz + oh / 2
    p.box((0, -t * 0.55, (top0 + h) / 2), (w / 2, t * 0.35, (h - top0) / 2), wood)
    side = (w / 2 - ow / 2) / 2
    for sx in (-1, 1):
        p.box((sx * (ow / 2 + side), -t * 0.55, oz), (side, t * 0.35, oh / 2), wood)
    wall_frame(p, brace=False)
    # window casing + 4-pane mullions + sill
    for sx in (-1, 1):
        p.box((sx * (ow / 2 + 0.05), -t * 0.6, oz), (0.05, 0.06, oh / 2 + 0.05), tb)
    p.box((0, -t * 0.6, oz + oh / 2 + 0.05), (ow / 2 + 0.1, 0.06, 0.05), tb)
    p.box((0, -t * 0.6, oz - oh / 2 - 0.06), (ow / 2 + 0.16, 0.10, 0.06), tb)  # sill
    p.box((0, -t * 0.58, oz), (0.032, 0.05, oh / 2), tb)      # vertical mullion
    p.box((0, -t * 0.58, oz), (ow / 2, 0.05, 0.032), tb)      # horizontal mullion
    p.box((0, -t * 0.45, oz), (ow / 2, 0.02, oh / 2), M("mat_glass_dark"))
    return p.finish(c)


def build_wall_door(c):
    p = Part("kit_wall_door")
    w, h, t = 3.0, 3.0, 0.14
    wood = M("mat_wallwood")
    tb = M("mat_timber")
    dw, dh = 1.0, 2.1
    side = (w / 2 - dw / 2) / 2
    for sx in (-1, 1):
        p.box((sx * (dw / 2 + side), -t * 0.55, dh / 2), (side, t * 0.35, dh / 2), wood)
    p.box((0, -t * 0.55, (dh + h) / 2), (w / 2, t * 0.35, (h - dh) / 2), wood)
    wall_frame(p, brace=False)
    for sx in (-1, 1):                                   # jambs
        p.box((sx * (dw / 2 + 0.06), -t * 0.62, dh / 2), (0.06, 0.07, dh / 2), tb)
    p.box((0, -t * 0.62, dh + 0.08), (dw / 2 + 0.14, 0.09, 0.08), tb)   # lintel
    # planked door leaf, hung very slightly off-square
    for i in range(5):
        x = -dw / 2 + dw / 5 * (i + 0.5)
        p.box((x, -t * 0.72, dh / 2), (dw / 10 - 0.006, 0.035, dh / 2 - 0.02),
              M("mat_wallwood_dark"), jitter=0.006)
    for zz in (0.35, dh - 0.35):                          # cross battens
        p.box((0, -t * 0.78, zz), (dw / 2 - 0.02, 0.022, 0.07), tb)
    p.box((0, -t * 0.78, dh / 2), (dw / 2 - 0.05, 0.02, 0.05), tb,
          rot=(0, -math.atan2(dh - 0.9, dw), 0))
    p.cyl((dw / 2 - 0.16, -t * 0.86, 1.05), 0.03, 0.10, M("mat_iron"),
          segments=8, rot=(math.pi / 2, 0, 0))
    return p.finish(c)


# ---------------------------------------------------------------- structure

def build_railing_post(c):
    p = Part("kit_railing_post")
    p.box((0, 0, 0.5), (0.06, 0.06, 0.5), M("mat_timber"))
    p.box((0, 0, 1.02), (0.075, 0.075, 0.025), M("mat_timber"))
    return p.finish(c)


def build_railing_1m(c):
    """1m span, 1.0u tall. Origin at left post, rail runs +X."""
    p = Part("kit_railing_1m")
    tb = M("mat_timber")
    for x in (0.0, 1.0):
        p.box((x, 0, 0.5), (0.06, 0.06, 0.5), tb, jitter=0.008)
    p.box((0.5, 0, 0.97), (0.55, 0.07, 0.05), tb, jitter=0.006)   # top rail
    p.box((0.5, 0, 0.52), (0.5, 0.045, 0.04), tb, jitter=0.01)    # mid rail
    return p.finish(c)


def build_stair_flight(c):
    """8 treads, rise 0.22 (<0.4 ok), run 0.30. Total 1.76 up, 2.4 along +X."""
    p = Part("kit_stair_flight")
    tb, dk = M("mat_timber"), M("mat_deck")
    rise, run, wide = 0.22, 0.30, 1.2
    n = 8
    for i in range(n):
        p.box((run * (i + 0.5), 0, rise * (i + 1) - 0.03),
              (run / 2 + 0.03, wide / 2, 0.035), dk, jitter=0.01)
    ang = math.atan2(rise * n, run * n)
    L = math.hypot(rise * n, run * n)
    for sy in (-1, 1):
        p.box((run * n / 2, sy * (wide / 2 + 0.06), rise * n / 2 - 0.13),
              (L / 2, 0.06, 0.14), tb, rot=(0, -ang, 0))
    return p.finish(c)


def build_stilt_trestle(c):
    """Cross-braced support tower, 4u tall, 1.3u square at base, origin at base centre."""
    p = Part("kit_stilt_trestle")
    tb = M("mat_timber")
    H, b, tp = 4.0, 0.65, 0.45
    legs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = sx * b, sy * b
            x1, y1 = sx * tp, sy * tp
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            lean = math.atan2(b - tp, H)
            p.box((mx, my, H / 2), (0.11, 0.11, H / 2 + 0.06), tb,
                  rot=(sy * lean, -sx * lean, 0), jitter=0.006)
            legs.append((x0, y0))
    for z, hw in ((H * 0.32, b * 0.86), (H * 0.68, b * 0.62)):
        for sx in (-1, 1):
            p.box((sx * hw, 0, z), (0.07, hw, 0.07), tb, jitter=0.01)
        for sy in (-1, 1):
            p.box((0, sy * hw, z), (hw, 0.07, 0.07), tb, jitter=0.01)
    # X bracing on all four faces
    for lo, hi in ((0.06, H * 0.32), (H * 0.32, H * 0.68), (H * 0.68, H - 0.1)):
        mz = (lo + hi) / 2
        dz = hi - lo
        for face in range(4):
            hw = b * (1.0 - 0.28 * (mz / H))
            L = math.hypot(hw * 2, dz)
            ang = math.atan2(dz, hw * 2)
            for s in (1, -1):
                if face < 2:
                    y = (1 if face == 0 else -1) * hw
                    p.box((0, y, mz), (L / 2, 0.045, 0.05), tb,
                          rot=(0, -s * ang, 0), jitter=0.008)
                else:
                    x = (1 if face == 2 else -1) * hw
                    p.box((x, 0, mz), (0.045, L / 2, 0.05), tb,
                          rot=(s * ang, 0, 0), jitter=0.008)
    p.box((0, 0, H + 0.02), (tp + 0.2, tp + 0.2, 0.09), tb)
    return p.finish(c)


def build_beam(c):
    p = Part("kit_beam")
    p.box((0, 0, 0), (1.5, 0.11, 0.11), M("mat_timber"))
    return p.finish(c)


def build_plank_deck(c):
    """2x2 deck tile, top surface at z=0, joists below."""
    p = Part("kit_plank_deck_2x2")
    dk, tb = M("mat_deck"), M("mat_timber")
    bw = 0.22
    n = int(round(2.0 / bw))
    step = 2.0 / n
    for i in range(n):
        y = -1.0 + step * (i + 0.5)
        p.box((0, y, -0.03), (1.0, step / 2 - 0.006, 0.03), dk,
              jitter=0.007)
    for x in (-0.8, 0.0, 0.8):
        p.box((x, 0, -0.14), (0.07, 1.0, 0.08), tb)
    return p.finish(c)


def build_roof_panel(c):
    """3 x 2.2 shingled slope, laid as overlapping courses (origin at eave centre)."""
    p = Part("kit_roof_panel")
    sh, tb = M("mat_shingle"), M("mat_timber")
    W, L = 3.0, 2.2
    p.box((0, L / 2, -0.06), (W / 2, L / 2, 0.05), tb)          # sheathing
    for r in range(9):                                          # shingle courses
        y = 0.02 + r * (L - 0.1) / 9
        p.box((0, y, 0.012 + r * 0.004), (W / 2 + 0.06, (L / 9) * 0.72, 0.022), sh,
              rot=(-0.04, 0, 0), jitter=0.006)
    for x in (-W / 2 + 0.15, 0.0, W / 2 - 0.15):                # rafter tails
        p.box((x, 0.02, -0.12), (0.06, 0.16, 0.06), tb)
    return p.finish(c)


# -------------------------------------------------------------------- props

def build_barrel(c):
    p = Part("kit_barrel")
    wd, ir = M("mat_wallwood_dark"), M("mat_iron")
    p.cyl((0, 0, 0.45), 0.30, 0.90, wd, segments=18)
    p.cyl((0, 0, 0.45), 0.335, 0.42, wd, segments=18)   # belly bulge
    for z in (0.12, 0.45, 0.78):
        rr = 0.345 if abs(z - 0.45) < 0.2 else 0.315
        p.cyl((0, 0, z), rr, 0.055, ir, segments=18)
    return p.finish(c, bevel=0.008)


def build_crate(c):
    p = Part("kit_crate")
    wd, tb = M("mat_wallwood_dark"), M("mat_timber")
    s = 0.34
    for i in range(3):                                  # slatted sides
        z = 0.06 + i * 0.235
        for ax in (0, 1):
            for sgn in (-1, 1):
                if ax == 0:
                    p.box((sgn * s, 0, z), (0.022, s, 0.10), wd, jitter=0.012)
                else:
                    p.box((0, sgn * s, z), (s, 0.022, 0.10), wd, jitter=0.012)
    for sx in (-1, 1):                                  # corner battens
        for sy in (-1, 1):
            p.box((sx * s, sy * s, 0.34), (0.035, 0.035, 0.34), tb)
    p.box((0, 0, 0.67), (s, s, 0.025), wd)
    return p.finish(c, bevel=0.006)


def build_lantern(c):
    """Hanging lantern: iron cage, emissive glass, real point light. ~0.45u tall."""
    p = Part("kit_lantern_hanging")
    ir, gl = M("mat_iron"), M("mat_lantern_glass")
    p.cyl((0, 0, -0.20), 0.085, 0.045, ir, segments=10)      # base
    p.cyl((0, 0, 0.0), 0.062, 0.30, gl, segments=10)         # glass body
    for a in range(4):                                        # cage uprights
        th = a * math.pi / 2 + math.pi / 4
        p.box((math.cos(th) * 0.072, math.sin(th) * 0.072, 0.0),
              (0.011, 0.011, 0.16), ir, rot=(0, 0, th))
    p.cyl((0, 0, 0.185), 0.10, 0.075, ir, segments=10, r2=0.03)   # conical cap
    p.cyl((0, 0, 0.245), 0.018, 0.05, ir, segments=8)
    p.torus((0, 0, 0.30), 0.045, 0.010, ir, seg=14, ring=6, rot=(math.pi / 2, 0, 0))
    ob = p.finish(c, bevel=0.004)
    lt = bpy.data.lights.new("kit_lantern_light", "POINT")
    lt.energy = 55.0
    lt.color = (1.0, 0.60, 0.28)
    lt.shadow_soft_size = 0.10
    lo = bpy.data.objects.new("kit_lantern_light", lt)
    lo.location = (0, 0, 0.0)
    c.objects.link(lo)
    lo.parent = ob
    return ob


def build_rope_coil(c):
    p = Part("kit_rope_coil")
    rp = M("mat_rope")
    for i in range(5):
        p.torus((R.uniform(-0.01, 0.01), R.uniform(-0.01, 0.01), 0.035 + i * 0.052),
                0.26 - i * 0.022, 0.026, rp, seg=22, ring=7,
                rot=(R.uniform(-0.05, 0.05), R.uniform(-0.05, 0.05), 0))
    return p.finish(c, bevel=0)


def build_bucket(c):
    p = Part("kit_bucket")
    wd, ir = M("mat_wallwood_dark"), M("mat_iron")
    p.cyl((0, 0, 0.16), 0.155, 0.32, wd, segments=14, r2=0.115)
    p.cyl((0, 0, 0.29), 0.163, 0.03, ir, segments=14)
    p.torus((0, 0, 0.30), 0.15, 0.010, ir, seg=16, ring=5, rot=(0, math.pi / 2, 0))
    return p.finish(c, bevel=0.005)


def build_ref_capsule(c):
    """1.7u scale reference -- the human-height sanity check."""
    p = Part("REF_human_1p7")
    m = M("mat_plaster")
    p.cyl((0, 0, 0.68), 0.17, 1.36, m, segments=14)   # body: 0.00 -> 1.36
    p.cyl((0, 0, 1.53), 0.13, 0.34, m, segments=12)   # head: 1.36 -> 1.70
    return p.finish(c, bevel=0.05)


# ------------------------------------------------------------------- lights

LIGHTING_RECIPE = """DELLHOLLOW SUNSET LIGHT RIG  (collection LIGHT_SUNSET)
=========================================================
Target mood: late-afternoon sun raking DOWN-GORGE, warm key vs cool shadow.
Reference: web/renders/dellhollow-slice/stylized.png

SUN  "SUN_key"
  type SUN, energy 4.2, angle 2.5 deg (soft-ish edge, not a hard CG shadow)
  colour  1.00 / 0.68 / 0.40   (~2900K -- deep golden hour)
  rotation: elevation 11 deg above horizon, pointing along the gorge axis so
  it rakes across facades and throws LONG shadows across the decking. A low
  sun is what separates this from flat midday CG.

WORLD  warm gradient sky (no HDRI needed)
  Sky-ish vertical ramp via Texture Coordinate(Generated).Z -> ColorRamp:
    z=0.00  (0.42, 0.20, 0.10)  warm dust at the gorge floor
    z=0.45  (0.55, 0.36, 0.22)  haze band
    z=1.00  (0.30, 0.34, 0.44)  cool upper sky -- the complement that makes
                                the warm key read as warm
  strength 1.1

FILL  "FILL_bounce"  AREA, 9x9, energy 90
  placed opposite the key and BELOW/beside, tinted cool teal (0.35,0.55,0.65)
  to fake bounce off the river. Keeps shadows readable instead of black.

RIM  "RIM_gorge"  AREA, 6x6, energy 130, warm (1.0,0.72,0.45)
  behind subject, low -- separates silhouettes from the misty background.

PRACTICALS  each kit_lantern_hanging carries its own POINT light,
  55W, colour (1.0,0.60,0.28), soft size 0.10. These are the warm accents.

ATMOSPHERE  (this is the single biggest gap between raw and stylized)
  World volume scatter, density 0.0022, warm colour (0.62,0.50,0.40),
  anisotropy 0.35. Gives aerial perspective: far cliffs desaturate into haze,
  lantern light gets visible bloom, depth reads instantly.

FILM  Filmic/AgX view transform, exposure ~0.0, contrast Medium High.
"""


def build_light_rig():
    c = coll("LIGHT_SUNSET")
    sun = bpy.data.lights.new("SUN_key", "SUN")
    sun.energy = 4.2
    sun.color = (1.0, 0.68, 0.40)
    sun.angle = math.radians(2.5)
    so = bpy.data.objects.new("SUN_key", sun)
    so.location = (18, 40, 16)
    so.rotation_euler = (math.radians(79), 0, math.radians(196))
    c.objects.link(so)

    fill = bpy.data.lights.new("FILL_bounce", "AREA")
    fill.energy = 90
    fill.size = 9.0
    fill.color = (0.35, 0.55, 0.65)
    fo = bpy.data.objects.new("FILL_bounce", fill)
    fo.location = (-8, -6, 3.0)
    fo.rotation_euler = (math.radians(65), 0, math.radians(-55))
    c.objects.link(fo)

    rim = bpy.data.lights.new("RIM_gorge", "AREA")
    rim.energy = 130
    rim.size = 6.0
    rim.color = (1.0, 0.72, 0.45)
    ro = bpy.data.objects.new("RIM_gorge", rim)
    ro.location = (10, 26, 7)
    ro.rotation_euler = (math.radians(72), 0, math.radians(150))
    c.objects.link(ro)

    txt = bpy.data.texts.get("LIGHTING_NOTES") or bpy.data.texts.new("LIGHTING_NOTES")
    txt.clear()
    txt.write(LIGHTING_RECIPE)
    return c


def make_fog_box(name="FOG_BOX", center=(0, 0, 10), size=(160, 160, 60),
                 density=0.004, color=(0.62, 0.50, 0.40)):
    """Bounded atmospheric haze.

    NB: do NOT put volume scatter on the World. A world volume is infinite, so
    sun and sky light (which arrive from infinite distance) get fully
    extinguished -- the sky renders black and the sun stops lighting anything.
    A finite box gives the same aerial perspective and keeps lighting intact.
    """
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((*size, 1.0)), verts=bm.verts)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    coll("LIGHT_SUNSET").objects.link(ob)

    mat = bpy.data.materials.get("mat_fog") or bpy.data.materials.new("mat_fog")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumeScatter"); vol.location = (-200, 0)
    vol.inputs["Color"].default_value = (*color, 1.0)
    vol.inputs["Density"].default_value = density
    vol.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    me.materials.append(mat)
    ob.visible_shadow = False
    return ob


def setup_world(density=0.0):
    w = bpy.data.worlds.get("DellhollowSunset") or bpy.data.worlds.new("DellhollowSunset")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (500, 0)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (280, 100)
    bg.inputs["Strength"].default_value = 1.1
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-500, 100)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-320, 100)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-120, 100)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.42, 0.20, 0.10, 1)
    e = cr.elements.new(0.45); e.color = (0.55, 0.36, 0.22, 1)
    cr.elements[2].position = 1.0
    cr.elements[2].color = (0.30, 0.34, 0.44, 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    if density > 0:
        vol = nt.nodes.new("ShaderNodeVolumeScatter"); vol.location = (280, -180)
        vol.inputs["Color"].default_value = (0.62, 0.50, 0.40, 1)
        vol.inputs["Density"].default_value = density
        vol.inputs["Anisotropy"].default_value = 0.35
        nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return w


def build_all():
    cw, cs, cp = coll("KIT_WALLS"), coll("KIT_STRUCT"), coll("KIT_PROPS")
    made = []
    made += [build_wall_plain(cw), build_wall_window(cw), build_wall_door(cw)]
    made += [build_railing_post(cs), build_railing_1m(cs), build_stair_flight(cs),
             build_stilt_trestle(cs), build_beam(cs), build_plank_deck(cs),
             build_roof_panel(cs)]
    made += [build_barrel(cp), build_crate(cp), build_lantern(cp),
             build_rope_coil(cp), build_bucket(cp), build_ref_capsule(cp)]
    build_light_rig()
    setup_world()
    make_fog_box()
    return made
