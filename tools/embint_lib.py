"""embint_lib.py — the Emberbrook INTERIORS library.  ANTI-BOX BY CONSTRUCTION.

WHY THIS FILE EXISTS
--------------------
Dellhollow's six interiors are a standing user dissatisfaction: *"all basically
the same... square rectangular boxes with a counter and maybe a table."*  They
are, and the reason is in the code, not in the art direction.  Every one of
them is built by a helper set whose wall primitive is `build_wall(planeaxis,
pos, ...)` — a wall that can only lie on world x or world y.  A toolkit that
can only draw four axis-aligned walls will only ever produce a box, however
much clutter is dealt onto the floor of it.  `tools/shop_props.py` states the
box as a *contract* (`HW`, `YB`, `YF`, `WH`) and three shops share it.

So the mandate ("Emberbrook's interiors must be CREATIVE, varied, and alive —
its own floor plan and its own camera personality per room") is a TOOLING
problem first.  This library's primitives are:

  * `WallFrame` — a wall segment between two arbitrary 2D points, with its own
    inward normal.  L-plans, wedges, canted bays, inglenook returns and
    stair walls are all just a list of these.  Nothing here knows what "the
    back wall" is.
  * `floor_planks` — a plank floor over an arbitrary rectilinear/trapezoid
    footprint, expressed as a per-column y-interval function.  An L-shaped
    room's boards run unbroken round the corner, because the interval function
    is the union, not two rectangles butted together.
  * `steps` / `platform` — split levels and lofts, so a room can have a floor
    at two heights.  Dellhollow has exactly one floor height per room.
  * `rafters` — a real roof pitch over the room, so the ceiling can be a shape
    instead of a lid.

WHAT IT DOES NOT REINVENT
-------------------------
Materials: `tools/cottage_materials.py` is a complete, gated INTERIOR material
library (no moss, soot/grime keyed to the hearth, limewash relief, painted
trim, fire/ember/lamp emissives).  It is imported as-is and never edited —
that lane's scars are worth more than a fresh set of my own.
The kit: `tools/blends/kitlib.blend` via `append_kit` (same contract as
`cottage_build.py`).
Bake: `tools/depth_bake.py` — the canon single-camera bundle exporter.

NAMING CANON (the runtime keys behaviour off the prefix)
--------------------------------------------------------
  walk_floor*      walkable surface, the walk network of the room
  walk_pad_door    THE door pad.  `tools/scenegraph_derive.mjs` reads this
                   name verbatim to place the interior side of the door edge;
                   spelling it anything else silently drops the room's exits.
  walk_pad_*       other interaction pads (counter, hearth, oven ...)
  bar_             DELIBERATELY UNUSED INDOORS, and this is a measured fact
                   rather than an omission: `depth_bake.py` builds the
                   collision GLB by deleting every mesh that is render-hidden
                   *unless its name starts with `walk_`*, so a hidden `bar_`
                   collider would be stripped out of the very bundle it exists
                   to serve, and a visible one would render.  Containment
                   indoors is the walk-floor polygon's own edge.
  veg_ / water_    n/a indoors.   lm_  none — nothing here is blockout.

DETERMINISM
-----------
One RNG stream, seeded per build, consumed in build order (`seed()`).  Never
`hash()` — Python salts string hashing per process, so `random.Random(hash(x))`
is a different stream on every run.  `tools/item_int_build.py:fill_shelf` does
exactly that; it is the reason this note exists.
"""
import bpy, bmesh, math, os, random, io, contextlib, sys
from mathutils import Vector, Euler, Matrix

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TOOLS = os.path.join(ROOT, "tools")
KITLIB = os.path.join(TOOLS, "blends/kitlib.blend")

sys.path.insert(0, TOOLS)
import cottage_materials as CM          # noqa: E402  (the interior material library)

R = random.Random(0)


def seed(n):
    """One deterministic stream per build, consumed in build order."""
    global R
    R = random.Random(n)
    return R


def jit(a):
    return R.uniform(-a, a)


def toff():
    """Push a mesh off its own origin so a BOX-projected material starts at a
    different phase.  Without it, twenty identical boards show one tile."""
    return (R.uniform(-3, 3), R.uniform(-3, 3), R.uniform(-3, 3))


# ---------------------------------------------------------------- primitives

def coll(name, parent=None):
    if isinstance(name, bpy.types.Collection):
        return name
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def M(name):
    m = bpy.data.materials.get(name)
    if m is None:
        raise KeyError("missing material " + name)
    return m


def _finish(obj, mat, c, bevel=0.008, seg=2, angle=40.0):
    if mat is not None:
        obj.data.materials.append(mat if isinstance(mat, bpy.types.Material) else M(mat))
    for cc in list(obj.users_collection):
        cc.objects.unlink(obj)
    coll(c).objects.link(obj)
    if bevel and bevel > 0:
        m = obj.modifiers.new("bev", "BEVEL")
        m.width = bevel
        m.segments = seg
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(angle)
    return obj


def box(name, center, size, mat, c, rot=(0, 0, 0), bevel=0.008, tex_off=None):
    """Bevelled cuboid; `size` is the HALF-extent."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    off = Vector(tex_off) if tex_off else Vector((0, 0, 0))
    bmesh.ops.create_cube(bm, size=2.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        v.co += off
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = Euler(rot)
    ob.location = Vector(center) - (ob.rotation_euler.to_matrix() @ off)
    return _finish(ob, mat, c, bevel)


def cyl(name, center, r, h, mat, c, axis="Z", verts=16, rot=(0, 0, 0),
        bevel=0.004, taper=1.0, tex_off=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=r, radius2=r * taper, depth=h)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=Euler((0, math.pi / 2, 0)).to_matrix())
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=Euler((math.pi / 2, 0, 0)).to_matrix())
    off = Vector(tex_off) if tex_off else Vector((0, 0, 0))
    if tex_off:
        for v in bm.verts:
            v.co += off
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = Euler(rot)
    ob.location = Vector(center) - (ob.rotation_euler.to_matrix() @ off)
    return _finish(ob, mat, c, bevel)


def sphere(name, center, r, mat, c, segs=18, rings=11, scale=(1, 1, 1), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    for v in bm.verts:
        v.co.x *= scale[0]; v.co.y *= scale[1]; v.co.z *= scale[2]
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = center
    ob.rotation_euler = Euler(rot)
    return _finish(ob, mat, c, 0)


def lathe(name, profile, center, mat, c, segments=24, rot=(0, 0, 0),
          thickness=0.0, smooth=True, bevel=0.0):
    """Spin [(r, z), ...] about Z.  Open profile + solidify = a real vessel wall."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new((p[0], 0.0, p[1])) for p in profile]
    edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
    bmesh.ops.spin(bm, geom=verts + edges, axis=(0, 0, 1), cent=(0, 0, 0),
                   dvec=(0, 0, 0), angle=math.tau, steps=segments, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = smooth
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = center
    ob.rotation_euler = Euler(rot)
    if thickness:
        s = ob.modifiers.new("sol", "SOLIDIFY")
        s.thickness = thickness
        s.offset = -1.0
        s.use_rim = True
    return _finish(ob, mat, c, bevel)


def prism(name, poly, z0, z1, mat, c, bevel=0.0, smooth=False):
    """An extruded 2D polygon — the primitive an L-shaped anything needs.

    `poly` is [(x, y), ...] in order; winding is fixed automatically."""
    if _signed_area(poly) < 0:
        poly = list(reversed(poly))
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((p[0], p[1], z0)) for p in poly]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    up = [v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=up, vec=(0, 0, z1 - z0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for fa in bm.faces:
        fa.smooth = smooth
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return _finish(ob, mat, c, bevel)


def quad(name, corners, mat, c, smooth=False):
    """One four-cornered face in world space (rafter underside, canted glass)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in corners]
    f = bm.faces.new(vs)
    f.smooth = smooth
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return _finish(ob, mat, c, 0)


def displace(obj, strength=0.012, scale=0.35, levels=0, coords="GLOBAL", seed_=0):
    if levels:
        s = obj.modifiers.new("sub", "SUBSURF")
        s.subdivision_type = "SIMPLE"
        s.levels = levels
        s.render_levels = levels
    t = bpy.data.textures.new("dsp_%s_%d" % (obj.name, seed_), type="CLOUDS")
    t.noise_scale = scale
    t.noise_depth = 3
    d = obj.modifiers.new("dsp", "DISPLACE")
    d.texture = t
    d.texture_coords = coords
    d.strength = strength
    d.mid_level = 0.5
    return obj


def hide_from_camera(ob):
    """Still shadows, still bounces, never seen.  The FF9 cutaway is made of
    these — the room keeps its fourth wall and its lid for LIGHTING purposes
    while the lens looks straight in.  (Also: `depth_bake.py` deletes these
    before the collision export, so nothing invisible ends up solid.)"""
    ob.visible_camera = False
    return ob


def _signed_area(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2.0


# --------------------------------------------------------------- wall frames

class WallFrame:
    """A wall segment between two arbitrary plan points.

    Local coordinates, and they are the whole point of this class:
        u   along the wall from p0 to p1        (0 .. L)
        v   INTO the wall from its INNER face   (v > 0 is behind the plaster)
        z   world height

    Everything a wall carries — boards, studs, a chair rail, a window reveal —
    is authored in (u, v, z) and never in world x/y, so the same call builds a
    wall at 0 degrees, at 90, or at the 24-degree cant of a bakery's wedge.
    """

    def __init__(self, p0, p1, inward=None):
        self.p0 = Vector((p0[0], p0[1]))
        self.p1 = Vector((p1[0], p1[1]))
        d = self.p1 - self.p0
        self.L = d.length
        assert self.L > 1e-6, "degenerate wall segment"
        self.d = d / self.L
        # `inward` is the direction from the ROOM into the WALL.  Default is the
        # right-hand normal, i.e. walls listed anticlockwise round the room.
        n = Vector((self.d.y, -self.d.x))
        if inward is not None:
            iv = Vector((inward[0], inward[1])).normalized()
            if n.dot(iv) < 0:
                n = -n
        self.n = n
        self.yaw = math.atan2(self.d.y, self.d.x)

    def w(self, u, v=0.0, z=0.0):
        """(u, v, z) -> world (x, y, z)."""
        p = self.p0 + self.d * u + self.n * v
        return (p.x, p.y, z)

    def box(self, name, u, v, z, du, dv, dz, mat, c, bevel=0.008, tex=True,
            tilt=0.0):
        """A cuboid in wall-local space.  du/dv/dz are FULL extents."""
        return box(name, self.w(u, v, z), (du / 2, dv / 2, dz / 2), mat, c,
                   rot=(tilt, 0.0, self.yaw), bevel=bevel,
                   tex_off=toff() if tex else None)

    def cyl(self, name, u, v, z, r, h, mat, c, axis="Z", verts=12, bevel=0.003):
        rot = (0, 0, self.yaw)
        if axis == "V":                      # a peg sticking out of the wall
            rot = (0, math.pi / 2, self.yaw + math.pi / 2)
        elif axis == "U":                    # a rail running along the wall
            rot = (0, math.pi / 2, self.yaw)
        return cyl(name, self.w(u, v, z), r, h, mat, c, axis="Z", verts=verts,
                   rot=rot, bevel=bevel)


def wall_run(tag, frame, h, openings=(), c="SHELL", style="plaster",
             wain=None, wain_mat="mat_int_paint_green", trim_mat="mat_int_paint_red",
             board_mat="mat_int_plank", plaster_mat="mat_int_plaster",
             beam_mat="mat_int_beam", u0=None, u1=None, thick=0.22,
             studs=True, plate=True, plate_z=None, relief=True):
    """One wall of a room.  `openings` = [(a, b, top)] spans of u to leave out.

    style:
      "plaster"  limewash on lath between exposed studs (cottage / inn / bakery)
      "board"    vertical planking, framed (store, lean-to, loft gable)
      "stone"    coursed rubble (bakery oven wall, keeper's cottage hearth wall)
    """
    a0 = 0.0 if u0 is None else u0
    a1 = frame.L if u1 is None else u1
    SKIRT = 0.14
    WAIN_TOP = wain if wain else 0.0
    RAIL_TOP = WAIN_TOP + 0.10 if wain else 0.0
    plate_z = h - 0.10 if plate_z is None else plate_z

    def spans(above=0.0):
        out, cur = [], a0
        for (a, b, t) in sorted(openings):
            if t <= above:
                continue
            if a > cur:
                out.append((cur, a))
            cur = max(cur, b)
        if cur < a1:
            out.append((cur, a1))
        return out

    made = []
    # ---- carcass ---------------------------------------------------------
    for (a, b) in spans():
        w = b - a
        if w < 0.04:
            continue
        if style == "stone":
            z = 0.0
            k = 0
            while z < h - 0.02:
                ch = min(R.uniform(0.20, 0.31), h - z)
                ob = frame.box("%s_course_%02d_%.2f" % (tag, k, a), (a + b) / 2,
                               thick / 2 + 0.02 - R.uniform(0.0, 0.035), z + ch / 2,
                               w, thick + 0.04, ch - 0.012, "mat_int_stone", c,
                               bevel=0.012)
                displace(ob, 0.026, 0.22, levels=3, seed_=int(a * 10 + k))
                made.append(ob)
                z += ch
                k += 1
        elif style == "board":
            ob = frame.box("%s_sheath_%.2f" % (tag, a), (a + b) / 2, thick / 2 + 0.06,
                           h / 2, w, thick, h, plaster_mat, c, bevel=0)
            made.append(ob)
            u = a + 0.008
            i = 0
            while u < b - 0.04:
                bw = min(R.uniform(0.155, 0.245), b - 0.008 - u)
                if bw < 0.04:
                    break
                made.append(frame.box("%s_brd_%02d_%.2f" % (tag, i, a), u + bw / 2,
                                      0.026 + jit(0.004), h / 2, bw - 0.007, 0.052, h,
                                      board_mat, c, bevel=0.005))
                u += bw
                i += 1
        else:
            ob = frame.box("%s_plaster_%.2f" % (tag, a), (a + b) / 2, thick / 2 + 0.02,
                           h / 2, w, thick + 0.04, h, plaster_mat, c, bevel=0)
            if relief:
                displace(ob, 0.021, 0.30, levels=5, seed_=int(a * 10))
            made.append(ob)
    # over the openings
    for (a, b, t) in openings:
        if t < h - 0.02 and a1 - 0.01 > a and b > a0 + 0.01:
            ob = frame.box("%s_over_%.2f" % (tag, a), (a + b) / 2, thick / 2 + 0.02,
                           (t + h) / 2, b - a, thick + 0.04, h - t,
                           "mat_int_stone" if style == "stone" else plaster_mat, c,
                           bevel=0)
            if style == "plaster" and relief:
                displace(ob, 0.016, 0.30, levels=4, seed_=int(b * 10))
            made.append(ob)

    # ---- wainscot + trim -------------------------------------------------
    if wain:
        for (a, b) in spans(WAIN_TOP):
            u, i = a + 0.01, 0
            while u < b - 0.05:
                bw = min(R.uniform(0.15, 0.235), b - 0.01 - u)
                if bw < 0.05:
                    break
                made.append(frame.box("%s_wain_%02d_%.2f" % (tag, i, a), u + bw / 2,
                                      -0.012 + jit(0.004),
                                      SKIRT + (WAIN_TOP - SKIRT) / 2, bw - 0.008, 0.032,
                                      WAIN_TOP - SKIRT, wain_mat, c, bevel=0.004))
                u += bw
                i += 1
        for (a, b) in spans(RAIL_TOP):
            made.append(frame.box("%s_skirt_%.2f" % (tag, a), (a + b) / 2, -0.026,
                                  SKIRT / 2, b - a - 0.01, 0.055, SKIRT, trim_mat, c,
                                  bevel=0.006))
            made.append(frame.box("%s_rail_%.2f" % (tag, a), (a + b) / 2, -0.030,
                                  (WAIN_TOP + RAIL_TOP) / 2, b - a - 0.01, 0.062,
                                  RAIL_TOP - WAIN_TOP, trim_mat, c, bevel=0.008))

    # ---- studs + top plate ----------------------------------------------
    if studs and style != "stone":
        base = RAIL_TOP if wain else 0.0
        step = 1.06
        n = max(1, int(round((a1 - a0) / step)))
        for i in range(n + 1):
            u = a0 + (a1 - a0) * i / n
            if any(a - 0.14 < u < b + 0.14 for a, b, t in openings):
                continue
            made.append(frame.box("%s_stud_%02d" % (tag, i), u, -0.022,
                                  (base + plate_z - 0.08) / 2, 0.112, 0.048,
                                  plate_z - 0.08 - base, beam_mat, c, bevel=0.006))
    if plate:
        made.append(frame.box("%s_plate" % tag, (a0 + a1) / 2, -0.03, plate_z,
                              a1 - a0, 0.075, 0.20, beam_mat, c, bevel=0.010))
    return made


def opening_frame(tag, frame, a, b, top, c="SHELL", mat="mat_int_beam", depth=0.20,
                  sill=None):
    """Jambs + lintel (+ sill) round an opening.  The thing that turns a hole
    in a wall into a door or a window."""
    made = [
        frame.box("%s_jambL" % tag, a - 0.055, depth / 2 - 0.02, top / 2,
                  0.11, depth, top, mat, c, bevel=0.008),
        frame.box("%s_jambR" % tag, b + 0.055, depth / 2 - 0.02, top / 2,
                  0.11, depth, top, mat, c, bevel=0.008),
        frame.box("%s_lintel" % tag, (a + b) / 2, depth / 2 - 0.02, top + 0.075,
                  b - a + 0.24, depth, 0.15, mat, c, bevel=0.010),
    ]
    if sill is not None:
        made.append(frame.box("%s_sill" % tag, (a + b) / 2, depth / 2 - 0.10,
                              sill - 0.035, b - a + 0.30, depth + 0.16, 0.07,
                              mat, c, bevel=0.010))
    return made


# ---------------------------------------------------------------- the floor

def floor_planks(tag, xspan, yfn, z=0.0, c="SHELL", mat="mat_int_floor",
                 mat_alt=None, alt=0.16, dir_="y", thick=0.06, w=(0.155, 0.235),
                 run=(2.1, 4.2), name="walk_floorboard"):
    """Plank floor over an ARBITRARY rectilinear/trapezoid footprint.

    `yfn(x)` returns the list of (y0, y1) intervals the floor covers at that x.
    An L-shaped room is one call: the boards run unbroken round the corner
    because the interval function is the union of the arms, not two rectangles
    stopped against each other.  `dir_="x"` swaps the roles (boards running the
    other way), which is how a room gets a floor that is not the same floor as
    the room next door.

    Every board is its own object, named `walk_*`: the runtime's walk network
    IS the floor, so the room's walkable extent is exactly the shape drawn.
    """
    made = []
    a0, a1 = xspan
    a = a0
    i = 0
    swap = (dir_ == "x")
    while a < a1 - 1e-6:
        bw = min(R.uniform(*w), a1 - a)
        ac = a + bw / 2
        for (s0, s1) in yfn(ac):
            s = s0
            while s < s1 - 1e-6:
                ln = min(R.uniform(*run), s1 - s)
                if s1 - (s + ln) < 0.55:
                    ln = s1 - s
                cx, cy = (ac, s + ln / 2) if not swap else (s + ln / 2, ac)
                hx, hy = (bw / 2 - 0.004, ln / 2 - 0.004)
                if swap:
                    hx, hy = hy, hx
                made.append(box("%s_%s_%03d" % (name, tag, i), (cx, cy, z - thick / 2),
                                (hx, hy, thick / 2),
                                mat_alt if (mat_alt and R.random() < alt) else mat, c,
                                rot=(jit(0.0030), jit(0.0025), 0), bevel=0.005,
                                tex_off=toff()))
                i += 1
                s += ln
        a += bw
    return made


def rects_yfn(rects):
    """Build a `yfn` from axis-aligned rectangles [(x0, x1, y0, y1), ...].
    Overlapping arms are unioned, so an L or a T or a cross is one footprint."""
    def yfn(x):
        iv = sorted((y0, y1) for (x0, x1, y0, y1) in rects if x0 - 1e-9 <= x <= x1 + 1e-9)
        out = []
        for (a, b) in iv:
            if out and a <= out[-1][1] + 1e-9:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
        return out
    return yfn


def floor_void(name, x0, x1, y0, y1, z, c="SHELL", mat="mat_int_ash", pad=0.30):
    """A dark slab under the boards so the plank gaps read black, not empty."""
    return box(name, ((x0 + x1) / 2, (y0 + y1) / 2, z - 0.175),
               ((x1 - x0) / 2 + pad, (y1 - y0) / 2 + pad, 0.06), mat, c, bevel=0)


def steps(tag, frame_dir, x, y, n, rise, run, width, z_top, c="SHELL",
          mat="mat_int_plank", mat_side="mat_int_beam", walk=True, yaw=0.0):
    """A flight, built as `walk_` treads so the runtime can climb it.

    (x, y) is the centre of the TOP tread's outer edge; the flight descends in
    the -local-y direction.  Split levels are what stop a room being one plane;
    a plane is what makes a room a box."""
    made = []
    d = Vector((math.sin(yaw), -math.cos(yaw))) * frame_dir
    px = Vector((math.cos(yaw), math.sin(yaw)))
    pre = "walk_step" if walk else "step"
    for k in range(n):
        z = z_top - rise * k
        p = Vector((x, y)) + d * (run * (k + 0.5))
        made.append(box("%s_%s_%02d" % (pre, tag, k), (p.x, p.y, z - 0.035),
                        (width / 2, run / 2, 0.035), mat, c,
                        rot=(0, 0, yaw), bevel=0.008, tex_off=toff()))
        # riser: the shadow line that makes a step read as a step
        q = p + d * (run / 2)
        made.append(box("%s_%s_%02d_riser" % (pre.replace("walk_", ""), tag, k),
                        (q.x, q.y, z - rise / 2 - 0.06),
                        (width / 2 - 0.01, 0.022, rise / 2), mat_side, c,
                        rot=(0, 0, yaw), bevel=0.004, tex_off=toff()))
    return made


def platform(tag, poly, z, c="SHELL", mat="mat_int_plank", joist_mat="mat_int_beam",
             walk=False, joists=True, joist_dir="x"):
    """A raised deck: a loft, a stair landing, a shop's back platform.

    `walk=False` (the default) builds it as ART, not as walk network — a loft
    you reach by ladder is scenery, and putting a `walk_` mesh up there would
    hand the runtime a floor nobody can get to.  The ladder is the honest
    signal that there is a life upstairs; the walk network stays the ground."""
    made = []
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    pre = ("walk_%s_deck" % tag) if walk else ("%s_deck" % tag)
    # planked top
    if joist_dir == "x":
        a, b = min(ys), max(ys)
        u = a
        i = 0
        while u < b - 1e-6:
            bw = min(R.uniform(0.17, 0.245), b - u)
            made.append(box("%s_%03d" % (pre, i), ((min(xs) + max(xs)) / 2, u + bw / 2,
                                                   z - 0.028),
                            ((max(xs) - min(xs)) / 2, bw / 2 - 0.004, 0.028), mat, c,
                            rot=(0, 0, jit(0.002)), bevel=0.005, tex_off=toff()))
            u += bw
            i += 1
    else:
        a, b = min(xs), max(xs)
        u = a
        i = 0
        while u < b - 1e-6:
            bw = min(R.uniform(0.17, 0.245), b - u)
            made.append(box("%s_%03d" % (pre, i), (u + bw / 2, (min(ys) + max(ys)) / 2,
                                                   z - 0.028),
                            (bw / 2 - 0.004, (max(ys) - min(ys)) / 2, 0.028), mat, c,
                            rot=(0, 0, jit(0.002)), bevel=0.005, tex_off=toff()))
            u += bw
            i += 1
    if joists:
        # the UNDERSIDE is what the camera sees from below, and it is the whole
        # reason a loft beats a ceiling: structure, lit from underneath.
        if joist_dir == "x":
            n = max(2, int((max(ys) - min(ys)) / 0.42))
            for k in range(n + 1):
                y = min(ys) + (max(ys) - min(ys)) * k / n
                made.append(box("%s_joist_%02d" % (tag, k),
                                ((min(xs) + max(xs)) / 2, y, z - 0.115),
                                ((max(xs) - min(xs)) / 2, 0.048, 0.075), joist_mat, c,
                                bevel=0.006, tex_off=toff()))
        else:
            n = max(2, int((max(xs) - min(xs)) / 0.42))
            for k in range(n + 1):
                x = min(xs) + (max(xs) - min(xs)) * k / n
                made.append(box("%s_joist_%02d" % (tag, k),
                                (x, (min(ys) + max(ys)) / 2, z - 0.115),
                                (0.048, (max(ys) - min(ys)) / 2, 0.075), joist_mat, c,
                                bevel=0.006, tex_off=toff()))
    return made


def ladder(tag, x, y, z0, z1, yaw=0.0, lean=0.14, w=0.52, c="PROPS",
           mat="mat_int_wood"):
    """A loft ladder.  Rungs worn pale in the middle where feet land."""
    made = []
    H = z1 - z0
    d = Vector((math.cos(yaw), math.sin(yaw)))
    p = Vector((-d.y, d.x))                    # sideways
    for s in (-1, 1):
        b = Vector((x, y)) + p * (s * w / 2)
        made.append(box("%s_rail_%d" % (tag, s > 0),
                        (b.x + d.x * lean / 2, b.y + d.y * lean / 2, z0 + H / 2),
                        (0.038, 0.055, H / 2 + 0.10), mat, c,
                        rot=(math.atan2(lean, H) * -d.y, math.atan2(lean, H) * d.x,
                             yaw),
                        bevel=0.006, tex_off=toff()))
    n = max(3, int(H / 0.30))
    for k in range(1, n):
        t = k / float(n)
        b = Vector((x, y)) + d * (lean * t)
        made.append(cyl("%s_rung_%02d" % (tag, k), (b.x, b.y, z0 + H * t), 0.021,
                        w, "mat_int_wood" if k % 3 else "mat_int_bowlwood", c,
                        axis="X", verts=10, rot=(0, 0, yaw), bevel=0.003))
    return made


def rafters(tag, y0, y1, x0, x1, eave_z, ridge_z, c="SHELL", mat="mat_int_beam",
            board_mat="mat_int_plank", n=None, ridge_x=None, boards=True,
            hide_front=None, purlins=True):
    """A real roof pitch over the room: rafter pairs, purlins, and the boarded
    underside of the slates.

    This is the anti-box move that costs the least and reads the most.  A flat
    lid at 3.0 m is what every Dellhollow interior has; a ceiling that CLIMBS
    tells the player they are under a roof, in a house, in a village.

    `hide_front` — rafters forward of this y are made camera-invisible so the
    cutaway does not look through a cage (cottage-int v10's lesson, generalised).
    """
    made = []
    rx = (x0 + x1) / 2 if ridge_x is None else ridge_x
    n = n or max(3, int((y1 - y0) / 0.78))
    for k in range(n + 1):
        y = y0 + (y1 - y0) * k / n
        for (xa, xb) in ((x0, rx), (rx, x1)):
            if abs(xb - xa) < 0.05:
                continue
            L = math.hypot(xb - xa, ridge_z - eave_z)
            ang = math.atan2(ridge_z - eave_z, xb - xa)
            ob = box("%s_rafter_%02d_%s" % (tag, k, "a" if xa == x0 else "b"),
                     ((xa + xb) / 2, y, (eave_z + ridge_z) / 2),
                     (L / 2, 0.055, 0.085), mat, c, rot=(0, -ang, 0), bevel=0.008,
                     tex_off=toff())
            if hide_front is not None and y < hide_front:
                hide_from_camera(ob)
            made.append(ob)
    if boards:
        for (xa, xb) in ((x0, rx), (rx, x1)):
            if abs(xb - xa) < 0.05:
                continue
            L = math.hypot(xb - xa, ridge_z - eave_z)
            ang = math.atan2(ridge_z - eave_z, xb - xa)
            ob = box("%s_slateboard_%s" % (tag, "a" if xa == x0 else "b"),
                     ((xa + xb) / 2, (y0 + y1) / 2, (eave_z + ridge_z) / 2 + 0.10),
                     (L / 2, (y1 - y0) / 2, 0.030), board_mat, c, rot=(0, -ang, 0),
                     bevel=0, tex_off=toff())
            made.append(ob)
    if purlins:
        for t in (0.42, 0.80):
            for (xa, xb) in ((x0, rx), (rx, x1)):
                if abs(xb - xa) < 0.05:
                    continue
                px = xa + (xb - xa) * t
                pz = eave_z + (ridge_z - eave_z) * t
                made.append(box("%s_purlin_%s_%02d" % (tag, "a" if xa == x0 else "b",
                                                       int(t * 100)),
                                (px, (y0 + y1) / 2, pz - 0.075),
                                (0.065, (y1 - y0) / 2, 0.065), mat, c, bevel=0.006,
                                tex_off=toff()))
    # ridge piece
    made.append(box("%s_ridge" % tag, (rx, (y0 + y1) / 2, ridge_z + 0.03),
                    (0.075, (y1 - y0) / 2, 0.075), mat, c, bevel=0.008,
                    tex_off=toff()))
    return made


# ------------------------------------------------------------------- pads

def pad(name, cx, cy, w, d, z=0.0, yaw=0.0, c="PADS"):
    """Interaction / spawn metadata.  A real object so the exporter finds it,
    hidden from render because it is metadata, not dressing.

    `walk_pad_door` is READ BY NAME by tools/scenegraph_derive.mjs to build the
    interior side of the door edge and the spawn the player arrives on.  It is
    a contract, not a convention."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0,
                          matrix=Matrix.Translation((0, 0, 0))
                          @ Matrix.Diagonal((w, d, 0.02, 1.0)))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    coll(c).objects.link(ob)
    ob.location = (cx, cy, z + 0.02)
    ob.rotation_euler = Euler((0, 0, yaw))
    ob.hide_render = True
    ob.display_type = "WIRE"
    return ob


# -------------------------------------------------------------------- kit

def append_kit(names):
    want = [n for n in names if bpy.data.objects.get(n) is None]
    if want:
        with bpy.data.libraries.load(KITLIB, link=False) as (src, dst):
            avail = [n for n in want if n in src.objects]
            missing = sorted(set(want) - set(avail))
            if missing:
                raise RuntimeError("not in kitlib: %s" % missing)
            dst.objects = avail
    got = {}
    src_c = coll("KIT_SOURCE")
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None:
            raise RuntimeError("append failed: " + n)
        got[n] = o
        if o.name not in src_c.objects:
            src_c.objects.link(o)
        o.hide_render = True
    lamp, lit = got.get("kit_lantern_hanging"), got.get("kit_lantern_light")
    if lamp and lit:
        lit.parent = lamp
    return got


REMAP = {                       # outdoor kit material -> interior twin
    "mat_deck": "mat_int_plank",
    "mat_timber": "mat_int_beam",
    "mat_wallwood": "mat_int_paint_green",
    "mat_wallwood_dark": "mat_int_plank",
    "mat_plaster": "mat_int_plaster",
    "mat_mosswood": "mat_int_wood",
    "mat_iron": "mat_int_iron",
    "mat_metal": "mat_int_iron",
}


def place_kit(src, name, loc, rot=(0, 0, 0), c="PROPS", remap=True, extra=None):
    o = src.copy()
    o.data = src.data.copy()
    o.name = name
    o.hide_render = False
    o.location = loc
    o.rotation_euler = Euler(rot)
    coll(c).objects.link(o)
    table = dict(REMAP)
    table.update(extra or {})
    if remap:
        for slot in o.material_slots:
            if slot.material and slot.material.name in table:
                slot.material = M(table[slot.material.name])
    for ch in src.children:
        d = ch.copy()
        if ch.data:
            d.data = ch.data.copy()
        d.hide_render = False
        d.parent = o
        d.matrix_parent_inverse = src.matrix_world.inverted()
        coll(c).objects.link(d)
    return o


# ------------------------------------------------------------------ lights

def light(name, kind, loc, energy, color, size=0.25, c="LIGHTS", rot=(0, 0, 0),
          spread=None, shape=None, sx=1.0, sy=1.0, camera=False):
    ld = bpy.data.lights.new(name, type=kind)
    ld.energy = energy
    ld.color = color
    if kind == "POINT":
        ld.shadow_soft_size = size
    if kind == "SPOT":
        ld.shadow_soft_size = size
        ld.spot_size = math.radians(sx)
        ld.spot_blend = sy
    if kind == "AREA":
        ld.shape = shape or "RECTANGLE"
        ld.size = sx
        ld.size_y = sy
        if spread is not None:
            ld.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, ld)
    coll(c).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    ob.visible_camera = camera
    return ob


def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def hearth_rig(tag, x, y, z, face, energy=1.0, c="LIGHTS", mouth_spread=178):
    """The four-lamp fire rig, from cottage-int's hard-won note: a single point
    at the flames cannot both BE the fire and light the room — inverse square
    blows the firebox white before anything reaches the far wall.  So: a hot
    core, a high box light so the sooty back is not a hole, an AREA light in
    the PLANE OF THE OPENING throwing the pool out, and a second aimed HIGH.

    `face` is the unit direction the fire opening looks."""
    f = Vector((face[0], face[1], 0)).normalized()
    made = [
        light("LGT_%s_core" % tag, "POINT", (x, y, z + 0.28), 190.0 * energy,
              (1.0, 0.375, 0.090), 0.13, c=c),
        light("LGT_%s_box" % tag, "POINT", (x - f.x * 0.18, y - f.y * 0.18, z + 0.70),
              62.0 * energy, (1.0, 0.40, 0.11), 0.30, c=c),
    ]
    mouth = light("LGT_%s_mouth" % tag, "AREA",
                  (x + f.x * 0.30, y + f.y * 0.30, z + 0.70), 352.0 * energy,
                  (1.0, 0.435, 0.145), shape="RECTANGLE", sx=1.30, sy=1.10,
                  spread=mouth_spread, c=c)
    aim(mouth, (x + f.x * 4.0, y + f.y * 4.0, z + 0.62))
    made.append(mouth)
    up = light("LGT_%s_mouth_up" % tag, "AREA",
               (x + f.x * 0.36, y + f.y * 0.36, z + 0.86), 128.0 * energy,
               (1.0, 0.47, 0.17), shape="RECTANGLE", sx=1.20, sy=1.05, spread=150, c=c)
    aim(up, (x + f.x * 3.4, y + f.y * 3.4, z + 2.60))
    made.append(up)
    b = light("LGT_%s_bounce" % tag, "AREA",
              (x + f.x * 1.10, y + f.y * 1.10, z + 0.16), 68.0 * energy,
              (1.0, 0.52, 0.24), shape="RECTANGLE", sx=2.4, sy=2.0, spread=170, c=c)
    aim(b, (x + f.x * 3.0, y + f.y * 3.0, z + 1.5))
    made.append(b)
    return made


def hang_lantern(kit, name, x, y, z, hang_from, energy=90.0, c="PROPS",
                 chain_mat="mat_int_iron"):
    place_kit(kit["kit_lantern_hanging"], name, (x, y, z), c=c)
    n = max(1, int((hang_from - z - 0.16) / 0.055))
    for k in range(n):
        cyl("%s_chain_%02d" % (name, k), (x, y, z + 0.18 + 0.055 * k), 0.016, 0.030,
            chain_mat, coll(c), axis="Y" if k % 2 else "X", verts=8, bevel=0.002)
    cyl("%s_hook" % name, (x, y, hang_from - 0.02), 0.014, 0.09, chain_mat, coll(c),
        verts=8)
    light("LGT_%s" % name, "POINT", (x, y, z + 0.02), energy, (1.0, 0.60, 0.27), 0.09)


def roof_backing(name, x0, x1, y0, y1, z, c="SHELL", mat="mat_int_soot"):
    """A VISIBLE dark plane over the whole footprint, above every real ceiling.

    Not decoration and not a light trick: it is the fix for a measured defect.
    A cutaway room's ceiling is a set of boards, a hole for a stairwell and, in
    the next room along, open rafters -- and a camera pitched 13 degrees down
    still has its top rows looking 7 degrees UP.  Any ray that threads between
    those pieces leaves the scene and bakes as the depth map's FAR PLANE, which
    is exactly the signature `tools/plate_flat.py` exists to catch: the inn's
    first bundle came back "3.20% of frame, RGB 6,8,14, a volume rendered as a
    card" along its top edge.  With a backing plane every ray terminates on
    real geometry at a real distance, so the beauty plate and the depth plate
    agree everywhere, which is the whole contract of a pre-rendered scene.

    Dark and sooty because that is what a roof void over a lit room looks like.
    """
    ob = box(name, ((x0 + x1) / 2, (y0 + y1) / 2, z), ((x1 - x0) / 2, (y1 - y0) / 2,
                                                       0.06), mat, coll(c), bevel=0,
             tex_off=toff())
    ob.visible_shadow = False
    return ob


def dusk_card(name, center, half, rot=(0, 0, 0), top=(0.075, 0.105, 0.175),
              bottom=(0.014, 0.020, 0.034), strength=1.0, c="SHELL"):
    """The street outside a door or a window, as an emissive vertical gradient.

    NOT `mat_dusk_matte`: that one's ramp is keyed to OBJECT-space z over a
    fixed -3..5 range, so its warm band lands wherever the card happens to be
    scaled to — which on the first inn render put a blown warm rectangle in the
    doorway, exactly the flat unshaded fill `tools/plate_flat.py` exists to
    catch.  This one takes its two colours as arguments, so "how bright is the
    night outside" is a number in the room's own script.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (700, 0)
    em = nt.nodes.new("ShaderNodeEmission"); em.location = (480, 0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-800, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-620, 0)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-400, 0)
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (bottom[0], bottom[1], bottom[2], 1)
    cr.elements[1].position = 1.0
    cr.elements[1].color = (top[0], top[1], top[2], 1)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    # cloud breakup: a clean gradient is still a flat fill to the plate audit
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.location = (-620, -280)
    nz.inputs["Scale"].default_value = 2.6
    nz.inputs["Detail"].default_value = 7.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    mx.blend_type = "OVERLAY"; mx.location = (120, 0)
    for s in mx.inputs:
        if s.name == "Factor" and s.type == "VALUE":
            s.default_value = 0.26
    ins = [s for s in mx.inputs if s.type == "RGBA"]
    nt.links.new(ramp.outputs["Color"], ins[0])
    nt.links.new(nz.outputs["Color"], ins[1])
    nt.links.new([s for s in mx.outputs if s.type == "RGBA"][0], em.inputs["Color"])
    ob = box(name, center, half, mat, coll(c), rot=rot, bevel=0)
    ob.visible_shadow = False
    return ob


def fog_box(name, center, half, density=0.0030, color=(1.0, 0.62, 0.34),
            aniso=0.35, c="LIGHTS"):
    """BOUNDED volume only.  A world volume extinguishes everything (kit
    manifest bug 1) and a box that overhangs the shell turns the plate to soup
    (item-int's note).  Keep it strictly inside the walls."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    sc.inputs["Density"].default_value = density
    sc.inputs["Anisotropy"].default_value = aniso
    nt.links.new(sc.outputs["Volume"], out.inputs["Volume"])
    b = box(name, center, half, mat, coll(c), bevel=0)
    b.visible_shadow = False
    return b


# ------------------------------------------------------------------ camera

def build_camera(name, aim_at, vh, pitch, az, fov=35.0, roll=0.0, c="CAM",
                 shift=(0.0, 0.0)):
    """One fixed camera, framed by WHAT IT SEES rather than by a lens number.

    `vh` = the world height the frame covers at the aim point, so composition
    is authored in metres of room; `pitch` and `az` are where the camera stands
    relative to it.  Every interior in this set carries its OWN triple — the
    camera personality per room is the second half of the anti-box mandate,
    and Dellhollow's six rooms share one (pitch 24, az ~11, vfov 35).
    """
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = "VERTICAL"
    cd.angle_y = math.radians(fov)
    cd.clip_start = 0.08
    cd.clip_end = 400.0
    cd.shift_x, cd.shift_y = shift
    cam = bpy.data.objects.new(name, cd)
    coll(c).objects.link(cam)
    a = Vector(aim_at)
    dist = (vh / 2) / math.tan(math.radians(fov) / 2)
    azr, pr = math.radians(az), math.radians(pitch)
    d = Vector((math.sin(azr) * math.cos(pr), -math.cos(azr) * math.cos(pr),
                math.sin(pr)))
    cam.location = a + d * dist
    e = (a - cam.location).to_track_quat("-Z", "Y").to_euler()
    if roll:
        e.rotate_axis("Z", 0)
        cam.rotation_euler = e
        cam.rotation_mode = "XYZ"
        cam.rotation_euler = e
        # roll about the view axis
        q = (a - cam.location).to_track_quat("-Z", "Y")
        cam.rotation_euler = (q @ Euler((0, 0, math.radians(roll))).to_quaternion()
                              ).to_euler()
    else:
        cam.rotation_euler = e
    bpy.context.scene.camera = cam
    return cam


def in_frame(cam, pts):
    """Where world points land in NDC (0..1).  Used to CHECK a composition
    instead of guessing at it — 'the hearth is centre-frame' is a measurement."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    return [tuple(round(v, 3) for v in world_to_camera_view(sc, cam, Vector(p)))
            for p in pts]


# ------------------------------------------------------------------- render

def setup_render(samples=224, res=(1344, 768), exposure=0.72,
                 look="AgX - Punchy"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU setup skipped:", e)
        sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 16
    sc.cycles.diffuse_bounces = 6
    sc.cycles.glossy_bounces = 6
    sc.cycles.transmission_bounces = 8
    sc.cycles.volume_bounces = 2
    sc.cycles.sample_clamp_indirect = 8.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = look
    except Exception:
        pass
    sc.view_settings.exposure = exposure
    return sc


def render_to(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc = bpy.context.scene
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bpy.ops.render.render(write_still=True)
    print("RENDER ->", path)
    return path


def wipe():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def save(path):
    path = path if os.path.isabs(path) else os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("SAVED", path)
    return path


# ---------------------------------------------------------------- QA report

def qa_report(cam=None, checks=()):
    """Print the contract the room is judged on.  A build that cannot state
    its own floor height and door pad has not finished building."""
    bpy.context.view_layer.update()
    walk = [o for o in bpy.data.objects if o.name.startswith("walk_")]
    floors = [o for o in walk if "floorboard" in o.name or "_deck" in o.name
              or o.name.startswith("walk_step")]
    print("QA walk_ meshes: %d (floor %d)" % (len(walk), len(floors)))
    door = bpy.data.objects.get("walk_pad_door")
    print("QA walk_pad_door: %s%s" % (
        bool(door), "" if not door else " at (%.2f, %.2f, %.2f)" % tuple(door.location)))
    if floors:
        zs = [max((o.matrix_world @ Vector(c)).z for c in o.bound_box) for o in floors]
        print("QA floor top z: %.3f .. %.3f (character datum 0.000)" % (min(zs), max(zs)))
    print("QA meshes: %d  lights: %d  hidden-from-camera: %d" % (
        len([o for o in bpy.data.objects if o.type == "MESH"]),
        len([o for o in bpy.data.objects if o.type == "LIGHT"]),
        len([o for o in bpy.data.objects if o.type == "MESH" and not o.visible_camera])))
    if cam is not None and checks:
        for label, p in checks:
            u, v, d = in_frame(cam, [p])[0]
            print("QA frame  %-22s ndc (%.3f, %.3f)  depth %.2f m%s" % (
                label, u, v, d, "" if 0 <= u <= 1 and 0 <= v <= 1 else "   OFF-FRAME"))
    bad = CM.verify()
    if bad:
        print("MATERIAL WARNINGS:", bad)
    return len(walk)


def argopts(defaults):
    """Uniform CLI for every interior build script."""
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = dict(defaults)
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--") and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            k = a[2:].replace("-", "_")
            v = argv[i + 1]
            if k in out and isinstance(out[k], bool):
                out[k] = v not in ("0", "false", "False")
            elif k in out and isinstance(out[k], int) and not isinstance(out[k], bool):
                out[k] = int(v)
            elif k in out and isinstance(out[k], float):
                out[k] = float(v)
            else:
                out[k] = v
            i += 2
            continue
        if a.startswith("--"):
            out[a[2:].replace("-", "_")] = True
        i += 1
    return out
