"""del-cottage-int -- the Keepers' Cottage interior, Dellhollow.

"The house over the locks."  Supper at dusk: the party comes in off the cliff
path and this room has to feel like the moment the cold stops.

FORMAT (project standard FF9 cutaway):
    floor + back wall + two side walls; the near wall and the ceiling exist but
    are camera-invisible, so they still bounce light and contain it while the
    camera looks straight into the room.  ONE fixed camera, perspective,
    vertical fov 35deg, 3/4 from slightly high.
SCALE: character 1.7u, door 2.1u, table top 0.75u, chair seat 0.45u.
AXES:  x 0..9 across the room, y 0..7 into it (back wall at y=7),
       z up.  Camera sits at -y, high, slightly +x of centre, so the LEFT wall
       (x=0) is the hero wall -- that is where the hearth goes.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/cottage_build.py -- \
      --render docs/qa/interiors/cottage-int_v1.png --samples 224
"""
import bpy, bmesh, math, os, random, re, sys, io, contextlib
from mathutils import Vector, Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cottage_materials as CM

try:
    import importlib
    importlib.reload(CM)
except Exception:
    pass

KITLIB = "/Users/junshernchan/projects/multiplayer-rpg/tools/blends/kitlib.blend"
OUTBLEND = "/Users/junshernchan/projects/multiplayer-rpg/tools/blends/interiors/cottage-int.blend"
R = random.Random(90210)

RW, RD = 9.0, 7.0          # room width (x), depth (y)
WALL_H = 3.66              # cottage room, open to the tie beams
WALL_T = 0.24
BEAM_Z = 2.40              # tie-beam centre
CEIL_Z = 3.58              # the (camera-invisible) lid that contains the light


# ------------------------------------------------------------------ helpers

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
    (c if isinstance(c, bpy.types.Collection) else coll(c)).objects.link(obj)
    if bevel and bevel > 0:
        m = obj.modifiers.new("bev", "BEVEL")
        m.width = bevel
        m.segments = seg
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(angle)
    return obj


def box(name, center, size, mat, c, rot=(0, 0, 0), bevel=0.008, tex_off=None):
    """Beveled cuboid.  tex_off shifts the mesh inside its own object space so
    box-projected materials start at a different phase (kills the repeat when
    many copies sit side by side)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    off = Vector(tex_off) if tex_off else Vector((0, 0, 0))
    bmesh.ops.create_cube(bm, size=2.0)     # verts at +/-1 => `size` is half-extent
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        v.co += off
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(center) - off
    ob.rotation_euler = Euler(rot)
    return _finish(ob, mat, c, bevel)


def cyl(name, center, r, h, mat, c, axis="Z", verts=20, rot=(0, 0, 0),
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
    ob.location = Vector(center) - off
    ob.rotation_euler = Euler(rot)
    return _finish(ob, mat, c, bevel)


def sphere(name, center, r, mat, c, segs=20, rings=12, scale=(1, 1, 1), rot=(0, 0, 0)):
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


def lathe(name, profile, center, mat, c, segments=28, rot=(0, 0, 0),
          thickness=0.0, smooth=True, bevel=0.0):
    """Spin a 2D profile [(radius, z), ...] around Z.  Open profiles + a
    solidify modifier give real bowl/cup/jug walls with a visible rim."""
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


def displace(obj, strength=0.012, scale=0.35, levels=0, coords="GLOBAL", seed=0):
    if levels:
        s = obj.modifiers.new("sub", "SUBSURF")
        s.subdivision_type = "SIMPLE"
        s.levels = levels
        s.render_levels = levels
    t = bpy.data.textures.new("dsp_%s_%d" % (obj.name, seed), type="CLOUDS")
    t.noise_scale = scale
    t.noise_depth = 3
    d = obj.modifiers.new("dsp", "DISPLACE")
    d.texture = t
    d.texture_coords = coords
    d.strength = strength
    d.mid_level = 0.5
    return obj


def plane(name, center, size, mat, c, rot=(0, 0, 0), levels=0, disp=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = center
    ob.rotation_euler = Euler(rot)
    _finish(ob, mat, c, 0)
    if levels:
        displace(ob, disp, 0.6, levels)
    return ob


def jit(a):
    return R.uniform(-a, a)


def toff():
    return (R.uniform(-3, 3), R.uniform(-3, 3), R.uniform(-3, 3))


def hide_from_camera(ob):
    ob.visible_camera = False
    return ob


# ------------------------------------------------------------------ kit

def append_kit(names):
    want = [n for n in names if bpy.data.objects.get(n) is None]
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


def place_kit(src, name, loc, rot=(0, 0, 0), c="PROPS", remap=True):
    o = src.copy()
    o.data = src.data.copy()
    o.name = name
    o.hide_render = False
    o.location = loc
    o.rotation_euler = Euler(rot)
    coll(c).objects.link(o)
    if remap:
        for slot in o.material_slots:
            if slot.material and slot.material.name in REMAP:
                slot.material = M(REMAP[slot.material.name])
    for ch in src.children:
        d = ch.copy()
        if ch.data:
            d.data = ch.data.copy()
        d.hide_render = False
        d.parent = o
        d.matrix_parent_inverse = src.matrix_world.inverted()
        coll(c).objects.link(d)
    return o


# ------------------------------------------------------------------ shell

def wall_xf(planeaxis, pos, inward):
    """Return f(u, v, z) -> world.  u runs along the wall, v is depth INTO the
    wall from its inner face (v>0 = behind the inner face)."""
    if planeaxis == "x":
        return lambda u, v, z: (pos - inward * v, u, z)
    return lambda u, v, z: (u, pos - inward * v, z)


def build_wall(tag, planeaxis, pos, inward, u0, u1, openings=(), c="SHELL"):
    """Wainscot + chair rail + plaster + exposed studs + top plate.

    openings: [(a, b, top)] spans of u to leave out (doors/windows)."""
    f = wall_xf(planeaxis, pos, inward)
    ax = 0 if planeaxis == "x" else 1          # world axis the wall runs along
    swap = (planeaxis == "x")

    def sz(du, dv, dz):
        return (dv / 2, du / 2, dz / 2) if swap else (du / 2, dv / 2, dz / 2)

    def spans(top_only_z=0.0):
        out = []
        cur = u0
        for a, b, t in sorted(openings):
            if t <= top_only_z:
                continue
            if a > cur:
                out.append((cur, a))
            cur = max(cur, b)
        if cur < u1:
            out.append((cur, u1))
        return out

    WAIN_TOP, RAIL_TOP, SKIRT = 1.02, 1.12, 0.14

    # --- plaster carcass (full height, sits behind everything) -------------
    for (a, b) in spans():
        w = b - a
        if w < 0.05:
            continue
        ob = box("%s_plaster_%.2f" % (tag, a), f((a + b) / 2, WALL_T / 2 + 0.02, WALL_H / 2),
                 sz(w, WALL_T + 0.04, WALL_H), "mat_int_plaster", c, bevel=0,
                 tex_off=toff())
        displace(ob, 0.016, 0.55, levels=4, seed=int(a * 10))
    # above the openings
    for (a, b, t) in openings:
        if t < WALL_H - 0.02:
            ob = box("%s_plaster_over_%.2f" % (tag, a),
                     f((a + b) / 2, WALL_T / 2 + 0.02, (t + WALL_H) / 2),
                     sz(b - a, WALL_T + 0.04, WALL_H - t), "mat_int_plaster", c,
                     bevel=0, tex_off=toff())
            displace(ob, 0.014, 0.5, levels=3, seed=int(b * 10))

    # --- painted wainscot boards ------------------------------------------
    for (a, b) in spans(WAIN_TOP):
        u = a + 0.01
        i = 0
        while u < b - 0.05:
            w = min(R.uniform(0.15, 0.235), b - 0.01 - u)
            if w < 0.05:
                break
            box("%s_wain_%02d_%.2f" % (tag, i, a), f(u + w / 2, -0.012 + jit(0.004),
                                                     SKIRT + (WAIN_TOP - SKIRT) / 2),
                sz(w - 0.008, 0.032, WAIN_TOP - SKIRT), "mat_int_paint_green", c,
                bevel=0.004, tex_off=toff())
            u += w
            i += 1
    # skirting + chair rail (oxblood trim)
    for (a, b) in spans(RAIL_TOP):
        box("%s_skirt_%.2f" % (tag, a), f((a + b) / 2, -0.026, SKIRT / 2),
            sz(b - a - 0.01, 0.055, SKIRT), "mat_int_paint_red", c, bevel=0.006,
            tex_off=toff())
        box("%s_rail_%.2f" % (tag, a), f((a + b) / 2, -0.030, (WAIN_TOP + RAIL_TOP) / 2),
            sz(b - a - 0.01, 0.062, RAIL_TOP - WAIN_TOP), "mat_int_paint_red", c,
            bevel=0.008, tex_off=toff())

    # --- exposed studs + top plate ----------------------------------------
    step = 1.12
    n = max(1, int(round((u1 - u0) / step)))
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / n
        if any(a - 0.14 < u < b + 0.14 for a, b, t in openings):
            continue
        box("%s_stud_%02d" % (tag, i), f(u, -0.022, (RAIL_TOP + WALL_H - 0.18) / 2),
            sz(0.115, 0.048, WALL_H - 0.18 - RAIL_TOP), "mat_int_beam", c,
            bevel=0.006, tex_off=toff())
    box("%s_plate" % tag, f((u0 + u1) / 2, -0.03, WALL_H - 0.10),
        sz(u1 - u0, 0.075, 0.20), "mat_int_beam", c, bevel=0.010, tex_off=toff())
    # mid rail across the panel, and diagonal braces where there is room
    for (a, b) in spans():
        if b - a < 0.7:
            continue
        box("%s_midrail_%.2f" % (tag, a), f((a + b) / 2, -0.026, 2.52),
            sz(b - a, 0.058, 0.125), "mat_int_beam", c, bevel=0.008, tex_off=toff())
        if b - a > 1.6:
            for sgn, uu in ((1, a + 0.62), (-1, b - 0.62)):
                ang = sgn * 0.62
                rot = (ang, 0, 0) if planeaxis == "x" else (0, -ang, 0)
                box("%s_brace_%.2f_%d" % (tag, a, sgn), f(uu, -0.018, 3.06),
                    sz(0.095, 0.038, 0.92), "mat_int_beam", c,
                    rot=rot, bevel=0.006, tex_off=toff())
        # a short spandrel post above the mid rail, off-centre
        box("%s_upstud_%.2f" % (tag, a), f((a + b) / 2, -0.022, 3.06),
            sz(0.10, 0.042, WALL_H - 0.18 - 2.62), "mat_int_beam", c, bevel=0.006,
            tex_off=toff())


def build_shell():
    c = coll("SHELL")
    # ---- floorboards (each its own object so the grain restarts per board)
    x = 0.0
    i = 0
    while x < RW - 0.02:
        w = min(R.uniform(0.155, 0.235), RW - x)
        y = -0.30
        while y < RD - 0.02:
            ln = min(R.uniform(2.1, 4.2), RD - y)
            if RD - (y + ln) < 0.6:
                ln = RD - y
            ob = box("walk_floorboard_%03d" % i,
                     (x + w / 2, y + ln / 2, -0.060 + jit(0.0035)),
                     (w / 2 - 0.004, ln / 2 - 0.004, 0.06),
                     "mat_int_floor", c, rot=(jit(0.0035), jit(0.002), 0),
                     bevel=0.005, tex_off=toff())
            i += 1
            y += ln
        x += w
    # joist shadow line under the boards so the gaps read black, not empty
    box("floor_void", (RW / 2, RD / 2, -0.17), (RW / 2 + 0.3, RD / 2 + 0.3, 0.06),
        "mat_int_ash", c, bevel=0)

    # ---- walls -----------------------------------------------------------
    # left wall (x=0): hearth breast occupies u(y) 2.05..5.35
    build_wall("wL", "x", 0.0, +1, -WALL_T, RD + WALL_T,
               openings=[(2.05, 5.35, WALL_H)])
    # right wall (x=9): small high window
    build_wall("wR", "x", RW, -1, -WALL_T, RD + WALL_T, openings=[])
    # back wall (y=7): town door + glazed river door
    build_wall("wB", "y", RD, -1, 0.0, RW,
               openings=[(1.30, 2.50, 2.24), (6.35, 8.20, 2.38)])

    # ---- camera-invisible near wall + ceiling: they light the room --------
    nw = box("shadow_nearwall", (RW / 2, -WALL_T / 2 - 0.02, WALL_H / 2),
             (RW / 2 + WALL_T, WALL_T / 2, WALL_H / 2), "mat_int_plaster", c, bevel=0)
    hide_from_camera(nw)
    ceil = box("shadow_ceiling", (RW / 2, RD / 2, CEIL_Z + 0.08),
               (RW / 2 + WALL_T, RD / 2 + WALL_T, 0.08), "mat_int_plank", c, bevel=0)
    hide_from_camera(ceil)
    # ceiling boards, visible only in the far half where they read as ceiling
    y = 0.0
    i = 0
    while y < RD:
        w = min(0.26, RD - y)
        box("ceilboard_%02d" % i, (RW / 2, y + w / 2, CEIL_Z - 0.03),
            (RW / 2 + 0.1, w / 2 - 0.004, 0.028), "mat_int_beam", c,
            bevel=0.004, tex_off=toff())
        y += w
        i += 1

    # ---- ceiling beams ---------------------------------------------------
    for k, yb in enumerate((0.75, 2.15, 3.55, 4.95, 6.35)):
        box("beam_%02d" % k, (RW / 2, yb, BEAM_Z), (RW / 2 + 0.12, 0.130, 0.140),
            "mat_int_beam", c, rot=(0, 0, jit(0.004)), bevel=0.014, tex_off=toff())
        # joists between the beams
        for j in range(1, 4):
            yj = yb + 1.40 * j / 4.0
            if yj > RD - 0.05:
                continue
            box("joist_%02d_%d" % (k, j), (RW / 2, yj, CEIL_Z - 0.12),
                (RW / 2 + 0.1, 0.045, 0.075), "mat_int_beam", c, bevel=0.006,
                tex_off=toff())
    # a longitudinal summer beam under the cross beams, built in segments so the
    # cutaway can drop the sections that would hang over the camera
    for k in range(4):
        y0 = RD * k / 4.0
        box("beam_summer_%d" % k, (RW / 2, y0 + RD / 8.0, BEAM_Z + 0.20),
            (0.115, RD / 8.0, 0.105), "mat_int_beam", c, bevel=0.012, tex_off=toff())
    # chunkier tie beams read as the "heavy timber" of the brief; nothing above
    # them is drawn (the camera sits over the ceiling plane).

def world_center(ob):
    """True world-space bbox centre.  NOT matrix_world.translation: box()/cyl()
    deliberately push the mesh off its own origin (tex_off) to shift the texture
    phase, so an object's origin can be metres away from where it is drawn."""
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return sum(pts, Vector()) / 8.0


def apply_cutaway(keep_beams=(2, 4)):
    """FF9 cutaway.  Ceiling structure between the camera and the room is made
    camera-invisible but still casts shadow and bounces light, so the room stays
    a lit interior while the lens looks straight in.

    What survives is a chosen pair of tie beams: one crossing mid-frame (the
    supper lantern hangs from it) and one against the back wall.  Keeping all
    five turns the top of the frame into a cage; keeping none leaves the
    lantern chain hanging off nothing.
    """
    # matrix_world is lazily evaluated: without this the matrices of everything
    # just built are still identity, and world_center() silently returns the
    # tex_off jitter instead of the real position.
    bpy.context.view_layer.update()
    hidden = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        n = ob.name
        m = re.match(r"beam_(\d+)$", n)
        if m:
            drop = int(m.group(1)) not in keep_beams
        elif n.startswith(("ceilboard", "joist_", "beam_summer", "shadow_ceiling")):
            drop = True
        else:
            continue
        if drop:
            hide_from_camera(ob)
            hidden += 1
    print("CUTAWAY hid %d ceiling members from camera" % hidden)


def build_hearth():
    c = coll("HEARTH")
    y0, y1 = 2.05, 5.35                       # breast footprint along y
    D = 0.62                                   # projection into the room
    OPEN_Y0, OPEN_Y1, OPEN_Z = 3.10, 4.40, 1.08

    # rough stone piers, built as courses so nothing is a clean box
    for side, (a, b) in enumerate(((y0, OPEN_Y0), (OPEN_Y1, y1))):
        z = 0.0
        k = 0
        while z < 1.42:
            h = R.uniform(0.20, 0.30)
            d = D + jit(0.025)
            box("hearth_pier%d_%02d" % (side, k),
                (-WALL_T + (d + WALL_T) / 2 + jit(0.01), (a + b) / 2, z + h / 2),
                ((d + WALL_T) / 2, (b - a) / 2 - 0.004, h / 2 - 0.006),
                "mat_int_hearth", c, rot=(jit(0.008), jit(0.006), jit(0.01)),
                bevel=0.016, tex_off=toff())
            z += h
            k += 1
    # lintel
    box("hearth_lintel", (-WALL_T + (D + WALL_T) / 2, (OPEN_Y0 + OPEN_Y1) / 2, OPEN_Z + 0.13),
        ((D + WALL_T) / 2, (OPEN_Y1 - OPEN_Y0) / 2 + 0.34, 0.13),
        "mat_int_hearth", c, bevel=0.020, tex_off=toff())
    # firebox: back, cheeks, floor slab (sooty stone)
    box("hearth_back", (-WALL_T + 0.06, (OPEN_Y0 + OPEN_Y1) / 2, OPEN_Z / 2 + 0.1),
        (0.07, (OPEN_Y1 - OPEN_Y0) / 2, OPEN_Z / 2 + 0.1), "mat_int_hearth", c,
        bevel=0.01, tex_off=toff())
    box("hearth_slab", (0.20, (OPEN_Y0 + OPEN_Y1) / 2, 0.045),
        (0.40, (OPEN_Y1 - OPEN_Y0) / 2, 0.05), "mat_int_hearth", c, bevel=0.012,
        tex_off=toff())
    # corbelled hood tapering back to the wall, then the stack
    for k in range(4):
        t = k / 4.0
        w = (y1 - y0) / 2 * (1 - 0.30 * t)
        d = (D + WALL_T) * (1 - 0.55 * t)
        box("hearth_hood_%d" % k, (-WALL_T + d / 2, (y0 + y1) / 2, 1.52 + 0.24 * k + 0.12),
            (d / 2, w, 0.13), "mat_int_hearth", c, rot=(0, 0, jit(0.004)),
            bevel=0.014, tex_off=toff())
    box("hearth_stack", (-WALL_T + 0.30, (y0 + y1) / 2, 2.62),
        (0.30 + WALL_T / 2, (y1 - y0) / 2 * 0.68, 0.55), "mat_int_hearth", c,
        bevel=0.014, tex_off=toff())
    # ...and carries on up through the roof.  Built in courses so the silhouette
    # is not a clean extrusion.
    for k in range(7):
        w = (y1 - y0) / 2 * (0.64 - 0.012 * k)
        box("hearth_stack_%02d" % k,
            (-WALL_T + 0.26 + jit(0.012), (y0 + y1) / 2 + jit(0.02), 3.28 + 0.34 * k),
            (0.27 + WALL_T / 2, w, 0.175), "mat_int_hearth", c,
            rot=(jit(0.005), jit(0.004), jit(0.008)), bevel=0.016, tex_off=toff())
    box("hearth_stack_cap", (-WALL_T + 0.26, (y0 + y1) / 2, 5.72),
        (0.36 + WALL_T / 2, (y1 - y0) / 2 * 0.66, 0.075), "mat_int_stone", c,
        bevel=0.014, tex_off=toff())
    for sgn in (-1, 1):                      # chimney pots
        lathe("hearth_chimpot_%d" % sgn,
              [(0.0, 0.0), (0.115, 0.0), (0.115, 0.34), (0.100, 0.36)],
              (-WALL_T + 0.26, (y0 + y1) / 2 + sgn * 0.42, 5.79), M("mat_int_crock"),
              c, thickness=0.020)

    # hearthstone the players can stand on
    hs = box("walk_hearthstone", (0.42, (y0 + y1) / 2, 0.035),
             (0.62, (y1 - y0) / 2 - 0.05, 0.042), "mat_int_stone", c, bevel=0.014,
             tex_off=toff())
    displace(hs, 0.006, 0.4, levels=2)

    # mantel beam + its pegs
    box("hearth_mantel", (0.34, (y0 + y1) / 2, 1.62), (0.16, (y1 - y0) / 2 - 0.06, 0.075),
        "mat_int_beam", c, rot=(0, jit(0.004), 0), bevel=0.014, tex_off=toff())
    for yy in (2.35, 5.05):
        cyl("mantel_peg_%.0f" % (yy * 10), (0.49, yy, 1.62), 0.018, 0.09, "mat_int_wood",
            c, axis="X", verts=10)

    # ---- fire ------------------------------------------------------------
    # Read order matters: a bed of ash, charred logs crossed over it, embers
    # glowing in the gaps, then thin flame tongues.  The pot swings clear of the
    # flames so it does not read as a lump sitting in the middle of the fire.
    fy = (OPEN_Y0 + OPEN_Y1) / 2
    box("hearth_soot_back", (-WALL_T + 0.10, fy, OPEN_Z / 2 + 0.06),
        (0.035, (OPEN_Y1 - OPEN_Y0) / 2 - 0.02, OPEN_Z / 2 + 0.06), "mat_int_soot", c,
        bevel=0.006)
    for sgn in (-1, 1):
        box("hearth_soot_cheek_%d" % sgn, (0.10, fy + sgn * ((OPEN_Y1 - OPEN_Y0) / 2 - 0.02),
                                           OPEN_Z / 2 + 0.06),
            (0.30, 0.030, OPEN_Z / 2 + 0.06), "mat_int_soot", c, bevel=0.006)
    box("fire_back_plate", (-0.09, fy, 0.34), (0.022, 0.42, 0.34), "mat_int_iron", c,
        rot=(0, -0.06, 0), bevel=0.012)
    ash = sphere("fire_ashbed", (0.16, fy, 0.085), 0.36, M("mat_int_ash"), c,
                 scale=(0.62, 1.35, 0.13))
    displace(ash, 0.05, 0.22, levels=2)
    for k in range(5):                       # charred logs, crossed
        ang = R.uniform(-0.55, 0.55) + (0.9 if k % 2 else -0.9)
        cyl("fire_log_%d" % k,
            (0.15 + R.uniform(-0.07, 0.07), fy + R.uniform(-0.22, 0.22),
             0.115 + 0.055 * (k % 3)),
            R.uniform(0.045, 0.068), R.uniform(0.42, 0.60),
            "mat_embers" if k % 2 else "mat_int_charlog", c,
            axis="Y", verts=9, rot=(0, R.uniform(-0.16, 0.16), ang), bevel=0.008)
    emb = sphere("fire_emberbed", (0.15, fy, 0.105), 0.26, M("mat_embers"), c,
                 scale=(0.60, 1.22, 0.16))
    displace(emb, 0.030, 0.16, levels=2)
    for k in range(12):                      # flame tongues
        h = R.uniform(0.16, 0.46)
        xx = 0.15 + R.uniform(-0.10, 0.10)
        yy = fy + R.uniform(-0.34, 0.34)
        cyl("fire_flame_%d" % k, (xx, yy, 0.155 + h / 2),
            R.uniform(0.028, 0.055), h, "mat_fire", c, verts=10, taper=0.02,
            rot=(R.uniform(-0.22, 0.22), R.uniform(-0.20, 0.20), 0), bevel=0)
    for k in range(5):                       # loose embers on the hearthstone
        sphere("fire_spark_%d" % k, (0.44 + R.uniform(-0.10, 0.16),
                                     fy + R.uniform(-0.42, 0.42), 0.088),
               R.uniform(0.012, 0.022), M("mat_embers"), c, segs=8, rings=5)
    # andirons
    for s2 in (-1, 1):
        box("fire_andiron_%d" % s2, (0.16, fy + s2 * 0.32, 0.115), (0.22, 0.020, 0.020),
            "mat_int_iron", c, bevel=0.004)
        box("fire_andiron_up_%d" % s2, (-0.05, fy + s2 * 0.32, 0.175), (0.020, 0.020, 0.085),
            "mat_int_iron", c, bevel=0.004)

    # crane swung out of the flames, pot hanging over the near end of the fire
    PY_ = OPEN_Y1 - 0.32
    box("fire_crane_post", (0.28, OPEN_Y1 - 0.09, 0.62), (0.022, 0.022, 0.60),
        "mat_int_iron", c, bevel=0.004)
    box("fire_crane_arm", (0.30, OPEN_Y1 - 0.28, 1.13), (0.019, 0.24, 0.019),
        "mat_int_iron", c, bevel=0.004)
    for k in range(5):
        cyl("fire_potchain_%d" % k, (0.30, PY_, 1.09 - 0.048 * k), 0.014, 0.026,
            "mat_int_iron", c, axis="Y" if k % 2 else "X", verts=8, bevel=0.002)
    lathe("fire_pot", [(0.0, 0.0), (0.10, 0.004), (0.145, 0.070), (0.138, 0.185),
                       (0.116, 0.218), (0.126, 0.232)],
          (0.30, PY_, 0.60), M("mat_int_copper"), c, thickness=0.008, bevel=0.0)
    cyl("fire_pot_bail", (0.30, PY_, 0.845), 0.135, 0.010, "mat_int_iron", c,
        axis="Y", verts=16)

    # fireside kit
    box("hearth_poker", (0.72, 5.02, 0.44), (0.012, 0.012, 0.44), "mat_int_iron", c,
        rot=(0.10, 0.05, 0), bevel=0.003)
    box("hearth_tongs", (0.66, 4.92, 0.40), (0.014, 0.014, 0.40), "mat_int_iron", c,
        rot=(-0.06, 0.12, 0), bevel=0.003)


def hearth_mantel_clutter():
    c = coll("PROPS")
    # brass boat lamp
    lathe("lamp_boat_base", [(0.0, 0.0), (0.075, 0.0), (0.075, 0.03), (0.05, 0.055)],
          (0.34, 2.62, 1.70), M("mat_int_brass"), c, thickness=0.006)
    cyl("lamp_boat_glass", (0.34, 2.62, 1.83), 0.055, 0.17, "mat_int_lampglass", c,
        verts=16, bevel=0)
    lathe("lamp_boat_top", [(0.0, 0.10), (0.055, 0.055), (0.07, 0.0)],
          (0.34, 2.62, 1.92), M("mat_int_brass"), c, thickness=0.005)
    for k in range(4):
        box("lamp_boat_bar_%d" % k, (0.34 + 0.056 * math.cos(k * math.pi / 2),
                                     2.62 + 0.056 * math.sin(k * math.pi / 2), 1.83),
            (0.008, 0.008, 0.085), "mat_int_brass", c, bevel=0.002)
    # candlesticks
    for i, yy in enumerate((4.66, 4.86)):
        lathe("mantel_stick_%d" % i,
              [(0.0, 0.0), (0.045, 0.008), (0.018, 0.03), (0.014, 0.12),
               (0.032, 0.135), (0.020, 0.15)],
              (0.32, yy, 1.70), M("mat_int_brass"), c, thickness=0.005)
        h = R.uniform(0.08, 0.15)
        cyl("mantel_candle_%d" % i, (0.32, yy, 1.85 + h / 2), 0.013, h, "mat_int_wax",
            c, verts=12, bevel=0.003)
    # clay jar + a carved boat + a coil of cord
    lathe("mantel_jar", [(0.0, 0.0), (0.06, 0.0), (0.075, 0.06), (0.055, 0.15),
                         (0.065, 0.17)],
          (0.33, 3.30, 1.70), M("mat_int_crock_blue"), c, thickness=0.006)
    box("mantel_boat", (0.33, 3.85, 1.74), (0.05, 0.16, 0.035), "mat_int_wood", c,
        rot=(0, 0, 0.08), bevel=0.02, tex_off=toff())
    box("mantel_tin", (0.33, 4.25, 1.745), (0.045, 0.055, 0.045), "mat_int_iron", c,
        bevel=0.006)


# ------------------------------------------------------------------ doors

def planked_leaf(name, w, h, pivot, hinge_axis, mat, c, thick=0.05, angle=0.0,
                 battens=3):
    """A door leaf as separate boards + cross battens, hung from `pivot`."""
    parent = bpy.data.objects.new(name, None)
    coll(c).objects.link(parent)
    parent.location = pivot
    parent.rotation_euler = Euler((0, 0, angle * hinge_axis))
    n = max(3, int(round(w / 0.20)))
    bw = w / n
    for i in range(n):
        b = box("%s_bd%02d" % (name, i),
                (hinge_axis * (bw * (i + 0.5)), 0, h / 2),
                (bw / 2 - 0.004, thick / 2, h / 2), mat, c,
                rot=(0, 0, jit(0.002)), bevel=0.006, tex_off=toff())
        b.parent = parent
    for j in range(battens):
        z = 0.16 + (h - 0.32) * j / max(1, battens - 1)
        b = box("%s_bat%d" % (name, j), (hinge_axis * w / 2, -thick / 2 - 0.018, z),
                (w / 2 - 0.01, 0.020, 0.055), "mat_int_beam", c, bevel=0.006,
                tex_off=toff())
        b.parent = parent
    # iron strap hinges + ring latch
    for j in (0, battens - 1):
        z = 0.16 + (h - 0.32) * j / max(1, battens - 1)
        s = box("%s_strap%d" % (name, j), (hinge_axis * w * 0.32, -thick / 2 - 0.030, z),
                (w * 0.32, 0.010, 0.030), "mat_int_iron", c, bevel=0.004)
        s.parent = parent
    ring = cyl("%s_ring" % name, (hinge_axis * (w - 0.11), -thick / 2 - 0.03, h * 0.46),
               0.045, 0.012, "mat_int_iron", c, axis="Y", verts=16, bevel=0.003)
    ring.parent = parent
    return parent


def door_frame(name, planeaxis, pos, inward, a, b, top, mat, c, depth=0.16):
    f = wall_xf(planeaxis, pos, inward)
    swap = (planeaxis == "x")

    def sz(du, dv, dz):
        return (dv / 2, du / 2, dz / 2) if swap else (du / 2, dv / 2, dz / 2)
    for u in (a, b):
        box("%s_jamb_%.2f" % (name, u), f(u, WALL_T / 2 - 0.02, top / 2),
            sz(0.10, depth, top), mat, c, bevel=0.008, tex_off=toff())
    box("%s_head" % name, f((a + b) / 2, WALL_T / 2 - 0.02, top + 0.055),
        sz(b - a + 0.20, depth, 0.11), mat, c, bevel=0.008, tex_off=toff())


def build_town_door():
    c = coll("DOORS")
    a, b, top = 1.30, 2.50, 2.24
    door_frame("towndoor", "y", RD, -1, a, b, top, M("mat_int_paint_red"), c)
    planked_leaf("townleaf", 1.12, 2.10, (a + 0.04, RD - 0.06, 0.02), +1,
                 M("mat_int_plank"), c, angle=0.0)
    # threshold + the pad the game walks to
    box("towndoor_sill", ((a + b) / 2, RD - 0.02, 0.03), ((b - a) / 2, 0.13, 0.035),
        "mat_int_stone", c, bevel=0.010, tex_off=toff())
    p = box("walk_pad_door", ((a + b) / 2, RD - 0.62, 0.012), (0.62, 0.46, 0.014),
            "mat_int_floor", c, bevel=0.006, tex_off=toff())
    p.visible_shadow = False
    # boot scraper + a puddle-mat of straw
    box("door_scraper", (a - 0.28, RD - 0.24, 0.055), (0.09, 0.02, 0.055),
        "mat_int_iron", c, bevel=0.004)


def build_river_door():
    """Glazed door to the balcony over the locks -- one leaf ajar so real dusk
    light lands on the floor."""
    c = coll("DOORS")
    a, b, top = 6.35, 8.20, 2.38
    door_frame("riverdoor", "y", RD, -1, a, b, top, M("mat_int_paint_green"), c,
               depth=0.18)
    box("riverdoor_sill", ((a + b) / 2, RD + 0.02, 0.045), ((b - a) / 2 + 0.06, 0.16, 0.05),
        "mat_int_stone", c, bevel=0.012, tex_off=toff())
    w = (b - a) / 2 - 0.05

    def glazed_leaf(name, pivot, hinge, angle):
        parent = bpy.data.objects.new(name, None)
        coll(c).objects.link(parent)
        parent.location = pivot
        parent.rotation_euler = Euler((0, 0, angle * hinge))
        H = 2.22
        frame = [((hinge * 0.035, 0, H / 2), (0.035, 0.028, H / 2)),
                 ((hinge * (w - 0.035), 0, H / 2), (0.035, 0.028, H / 2)),
                 ((hinge * w / 2, 0, 0.030), (w / 2, 0.028, 0.030)),
                 ((hinge * w / 2, 0, H - 0.035), (w / 2, 0.028, 0.035)),
                 ((hinge * w / 2, 0, 0.44), (w / 2, 0.030, 0.045))]
        for i, (lc, ls) in enumerate(frame):
            o = box("%s_f%d" % (name, i), lc, ls, "mat_int_paint_green", c,
                    bevel=0.006, tex_off=toff())
            o.parent = parent
        # lower panel
        o = box("%s_panel" % name, (hinge * w / 2, 0, 0.24), (w / 2 - 0.04, 0.020, 0.20),
                "mat_int_paint_green", c, bevel=0.008, tex_off=toff())
        o.parent = parent
        # glazing bars: 2 x 3 panes
        gz0, gz1 = 0.50, H - 0.08
        for i in range(1, 2):
            o = box("%s_mull%d" % (name, i), (hinge * w * i / 2, 0, (gz0 + gz1) / 2),
                    (0.018, 0.022, (gz1 - gz0) / 2), "mat_int_paint_green", c,
                    bevel=0.004, tex_off=toff())
            o.parent = parent
        for j in range(1, 3):
            z = gz0 + (gz1 - gz0) * j / 3
            o = box("%s_tran%d" % (name, j), (hinge * w / 2, 0, z),
                    (w / 2 - 0.03, 0.022, 0.016), "mat_int_paint_green", c,
                    bevel=0.004, tex_off=toff())
            o.parent = parent
        g = box("%s_glass" % name, (hinge * w / 2, 0, (gz0 + gz1) / 2),
                (w / 2 - 0.035, 0.006, (gz1 - gz0) / 2), "mat_glass_dusk", c, bevel=0)
        g.parent = parent
        h = cyl("%s_handle" % name, (hinge * (w - 0.10), -0.055, 1.05), 0.014, 0.10,
                "mat_int_brass", c, axis="Y", verts=12)
        h.parent = parent
        return parent

    glazed_leaf("riverleaf_R", (b - 0.05, RD - 0.04, 0.075), -1, 0.0)
    glazed_leaf("riverleaf_L", (a + 0.05, RD - 0.04, 0.075), +1, -0.62)

    # ---- what is beyond: balcony deck, rail, and the dusk matte -----------
    o = coll("BEYOND")
    x = 5.4
    i = 0
    while x < 9.6:
        w2 = R.uniform(0.17, 0.24)
        box("balc_plank_%02d" % i, (x + w2 / 2, RD + 1.15, -0.02 + jit(0.004)),
            (w2 / 2 - 0.005, 1.05, 0.04), "mat_int_plank", o, bevel=0.005,
            tex_off=toff())
        x += w2
        i += 1
    box("balc_beam", (7.4, RD + 2.15, -0.12), (2.2, 0.10, 0.10), "mat_int_beam", o,
        bevel=0.01, tex_off=toff())
    # The balcony is roofed -- the cottage eave carries over it.  Without this the
    # camera looks over the back wall straight into the sky matte and blows out.
    # The pitch and start height matter: the camera looks over the back wall, so
    # the soffit has to be high enough at the wall and steep enough to close off
    # the sky before the frame edge.
    for k in range(11):
        y = RD + 0.08 + k * 0.40
        z = 4.16 - 0.190 * k
        box("balc_eave_%02d" % k, (5.4, y, z), (5.8, 0.215, 0.030), "mat_int_beam", o,
            rot=(-0.443, 0, 0), bevel=0.005, tex_off=toff())
    for s in (0, 1):
        box("balc_eavebeam_%d" % s, (1.9 + s * 6.9, RD + 2.2, 3.36), (0.10, 2.4, 0.11),
            "mat_int_beam", o, rot=(-0.443, 0, 0), bevel=0.01, tex_off=toff())
    box("balc_fascia", (5.4, RD + 4.25, 2.30), (5.8, 0.055, 0.13), "mat_int_paint_green",
        o, bevel=0.008, tex_off=toff())


def build_exterior_roof():
    """Two slopes on the outside of the side walls.  Purely an occluder: without
    them the camera looks past the wall tops into open sky at the frame corners."""
    o = coll("BEYOND")
    for sgn, x0 in ((-1, -WALL_T), (1, RW + WALL_T)):
        for k in range(7):
            d = 0.28 + k * 0.42
            box("ext_roof_%d_%d" % (sgn > 0, k),
                (x0 + sgn * d, RD / 2 - 0.2, WALL_H + 0.10 - 0.235 * k),
                (0.235, RD / 2 + 2.2, 0.030), "mat_int_beam", o,
                rot=(0, sgn * 0.51, 0), bevel=0.005, tex_off=toff())
        box("ext_verge_%d" % (sgn > 0), (x0 + sgn * 1.55, RD / 2 - 0.2, WALL_H - 0.62),
            (0.09, RD / 2 + 2.2, 0.10), "mat_int_paint_red", o, bevel=0.008,
            tex_off=toff())


def build_dusk_backdrop():
    """No exterior is modelled -- just a lit matte and two silhouette planes so
    the glass has something with depth behind it."""
    o = coll("BEYOND")
    plane("dusk_matte", (8.2, RD + 15.0, 1.0), (11.0, 18.0), M("mat_dusk_matte"), o,
          rot=(math.pi / 2, 0, 0))
    for i, (yy, xx, s, dark) in enumerate(((9.4, 4.2, 6.0, 0.026), (11.8, 10.8, 7.0, 0.045))):
        p = plane("dusk_cliff_%d" % i, (xx, yy, 1.2), (s, 8.0),
                  CM.simple("mat_dusk_cliff_%d" % i, (dark, dark * 1.05, dark * 1.15),
                            rough=0.9), o, rot=(math.pi / 2, 0, 0))
        displace(p, 0.9, 0.35, levels=4, seed=i)


def build_window_right():
    """A small high window on the right wall: a cold rake of gorge light that
    crosses the room the other way from the fire."""
    c = coll("DOORS")
    y0, y1, z0, z1 = 1.45, 2.45, 1.62, 2.42
    # cut the plaster by inserting a frame box and a glazed sash
    box("winR_sill", (RW - 0.02, (y0 + y1) / 2, z0), (0.16, (y1 - y0) / 2 + 0.09, 0.045),
        "mat_int_stone", c, bevel=0.010, tex_off=toff())
    for yy in (y0, y1):
        box("winR_jamb_%.1f" % yy, (RW + 0.02, yy, (z0 + z1) / 2), (0.14, 0.055,
            (z1 - z0) / 2), "mat_int_paint_green", c, bevel=0.006, tex_off=toff())
    box("winR_head", (RW + 0.02, (y0 + y1) / 2, z1), (0.14, (y1 - y0) / 2 + 0.055, 0.05),
        "mat_int_paint_green", c, bevel=0.006, tex_off=toff())
    box("winR_glass", (RW + 0.06, (y0 + y1) / 2, (z0 + z1) / 2),
        (0.006, (y1 - y0) / 2, (z1 - z0) / 2 - 0.02), "mat_glass_dusk", c, bevel=0)
    for j in range(1, 3):
        box("winR_bar%d" % j, (RW + 0.05, y0 + (y1 - y0) * j / 3, (z0 + z1) / 2),
            (0.020, 0.014, (z1 - z0) / 2 - 0.02), "mat_int_paint_green", c, bevel=0.003)
    box("winR_mull", (RW + 0.05, (y0 + y1) / 2, (z0 + z1) / 2 + 0.02),
        (0.020, (y1 - y0) / 2, 0.014), "mat_int_paint_green", c, bevel=0.003)


def punch_window_hole():
    """The right wall is built as solid plaster; carve the window with a boolean
    so the light actually gets in."""
    wall = [o for o in bpy.data.objects if o.name.startswith("wR_plaster")]
    cutter = box("winR_cutter", (RW, 1.95, 2.02), (0.5, 0.50, 0.40), None,
                 coll("SHELL"), bevel=0)
    cutter.hide_render = True
    cutter.hide_viewport = True
    for w in wall:
        m = w.modifiers.new("winhole", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.object = cutter
        m.solver = "EXACT"


# ------------------------------------------------------------------ table

TX, TY = 5.55, 3.15                 # table centre
TW, TD, TH = 2.35, 1.10, 0.75


def build_table():
    c = coll("FURNITURE")
    # top: five boards, slight cup, ends cleated
    n = 5
    bw = TD / n
    for i in range(n):
        box("table_board_%d" % i,
            (TX, TY - TD / 2 + bw * (i + 0.5), TH - 0.025 + jit(0.002)),
            (TW / 2, bw / 2 - 0.004, 0.026), "mat_int_wood", c,
            rot=(jit(0.0025), 0, 0), bevel=0.007, tex_off=toff())
    for s in (-1, 1):
        box("table_cleat_%d" % s, (TX + s * (TW / 2 - 0.045), TY, TH - 0.075),
            (0.045, TD / 2 - 0.01, 0.028), "mat_int_wood", c, bevel=0.006,
            tex_off=toff())
    # trestle ends
    for s in (-1, 1):
        x = TX + s * (TW / 2 - 0.34)
        box("table_foot_%d" % s, (x, TY, 0.045), (0.055, TD / 2 - 0.06, 0.045),
            "mat_int_wood", c, bevel=0.008, tex_off=toff())
        for t in (-1, 1):
            box("table_leg_%d%d" % (s, t), (x, TY + t * (TD / 2 - 0.17), 0.37),
                (0.048, 0.048, 0.33), "mat_int_wood", c, rot=(t * 0.045, 0, 0),
                bevel=0.007, tex_off=toff())
        box("table_head_%d" % s, (x, TY, TH - 0.10), (0.05, TD / 2 - 0.12, 0.038),
            "mat_int_wood", c, bevel=0.006, tex_off=toff())
    box("table_stretcher", (TX, TY, 0.30), (TW / 2 - 0.32, 0.045, 0.05),
        "mat_int_wood", c, bevel=0.006, tex_off=toff())

    # linen runner down the middle, rumpled
    run = plane("table_runner", (TX - 0.05, TY, TH + 0.003), (1.75, 0.50),
                M("mat_int_linen"), c, levels=5, disp=0.010)
    for s in (-1, 1):                      # the overhang at both ends
        plane("table_runner_fall_%d" % s, (TX - 0.05 + s * 0.875, TY, TH - 0.055),
              (0.11, 0.50), M("mat_int_linen"), c, rot=(0, math.pi / 2, 0),
              levels=4, disp=0.006)


def place_setting(i, x, y, facing):
    """One place: bowl, spoon, cup, a hunk of bread on the board's side."""
    c = coll("TABLEWARE")
    z = TH + 0.003
    ang = facing
    mat = "mat_int_crock" if i % 2 else "mat_int_crock_blue"
    lathe("set_bowl_%d" % i, [(0.0, 0.0), (0.045, 0.0), (0.085, 0.030), (0.105, 0.062),
                              (0.108, 0.070)],
          (x, y, z), M(mat), c, thickness=0.006, rot=(0, 0, R.uniform(0, 3)))
    if i % 3 != 2:
        lathe("set_stew_%d" % i, [(0.0, 0.052), (0.088, 0.055)],
              (x, y, z), M("mat_int_stew"), c, thickness=0.0, smooth=False)
    # spoon: handle + a shallow scoop
    hx, hy = x + 0.16 * math.cos(ang), y + 0.16 * math.sin(ang)
    box("set_spoon_%d" % i, (hx, hy, z + 0.008), (0.075, 0.011, 0.006),
        "mat_int_bowlwood", c, rot=(0, 0, ang + R.uniform(-0.3, 0.3)), bevel=0.004)
    sphere("set_spoonbowl_%d" % i,
           (hx + 0.085 * math.cos(ang), hy + 0.085 * math.sin(ang), z + 0.010),
           0.032, M("mat_int_bowlwood"), c, scale=(1.0, 0.66, 0.30))
    # cup
    cx, cy = x + 0.20 * math.cos(ang + 1.1), y + 0.20 * math.sin(ang + 1.1)
    lathe("set_cup_%d" % i, [(0.0, 0.0), (0.036, 0.0), (0.041, 0.035), (0.044, 0.085)],
          (cx, cy, z), M("mat_int_crock" if i % 2 == 0 else "mat_int_crock_blue"),
          c, thickness=0.005)


def build_tableware():
    c = coll("TABLEWARE")
    z = TH + 0.003
    # five places -- three on the camera side, two on the far side
    seats = [(TX - 0.78, TY - 0.34, math.pi / 2), (TX + 0.02, TY - 0.36, math.pi / 2),
             (TX + 0.82, TY - 0.33, math.pi / 2),
             (TX - 0.42, TY + 0.35, -math.pi / 2), (TX + 0.46, TY + 0.36, -math.pi / 2)]
    for i, (x, y, f) in enumerate(seats):
        place_setting(i, x, y, f)

    # the centre of the table: tureen, bread board, jug, candle, butter, salt
    lathe("ware_tureen", [(0.0, 0.0), (0.10, 0.0), (0.165, 0.055), (0.155, 0.155),
                          (0.175, 0.175)],
          (TX - 0.30, TY + 0.03, z), M("mat_int_crock"), c, thickness=0.008)
    lathe("ware_tureen_stew", [(0.0, 0.155), (0.150, 0.158)],
          (TX - 0.30, TY + 0.03, z), M("mat_int_stew"), c, thickness=0.0, smooth=False)
    lathe("ware_ladle_cup", [(0.0, 0.0), (0.045, 0.02), (0.048, 0.045)],
          (TX - 0.30, TY + 0.03, z + 0.19), M("mat_int_iron"), c, thickness=0.004,
          rot=(0.5, 0, 0.4))
    box("ware_ladle_handle", (TX - 0.16, TY + 0.14, z + 0.28), (0.012, 0.012, 0.14),
        "mat_int_iron", c, rot=(0.55, 0, 0.4), bevel=0.003)

    bx, by = TX + 0.62, TY + 0.06
    box("ware_breadboard", (bx, by, z + 0.012), (0.22, 0.15, 0.012), "mat_int_bowlwood",
        c, rot=(0, 0, 0.22), bevel=0.010, tex_off=toff())
    loaf = sphere("ware_loaf", (bx - 0.03, by + 0.01, z + 0.065), 0.115,
                  M("mat_int_bread"), c, scale=(1.25, 0.85, 0.55), rot=(0, 0, 0.22))
    displace(loaf, 0.022, 0.18, levels=1)
    for k in range(3):
        sl = box("ware_slice_%d" % k, (bx + 0.14 + 0.045 * k, by - 0.10 + 0.02 * k,
                                       z + 0.028),
                 (0.021, 0.085, 0.028), "mat_int_bread", c,
                 rot=(0, R.uniform(-0.25, 0.25), 0.22 + jit(0.3)), bevel=0.008)
    box("ware_knife", (bx + 0.06, by - 0.17, z + 0.020), (0.10, 0.014, 0.006),
        "mat_int_iron", c, rot=(0, 0, 0.5), bevel=0.003)
    box("ware_knife_h", (bx - 0.11, by - 0.24, z + 0.020), (0.045, 0.016, 0.010),
        "mat_int_wood", c, rot=(0, 0, 0.5), bevel=0.005)

    # jug of ale
    lathe("ware_jug", [(0.0, 0.0), (0.075, 0.0), (0.098, 0.055), (0.088, 0.155),
                       (0.052, 0.215), (0.058, 0.245), (0.050, 0.255)],
          (TX - 0.86, TY + 0.10, z), M("mat_int_crock_blue"), c, thickness=0.007)
    cyl("ware_jug_handle", (TX - 0.95, TY + 0.10, z + 0.165), 0.055, 0.014,
        "mat_int_crock_blue", c, axis="Y", verts=14)
    # candle in a dish -- the second warm source on the table
    lathe("ware_candledish", [(0.0, 0.0), (0.075, 0.004), (0.082, 0.022), (0.062, 0.026)],
          (TX + 1.02, TY + 0.14, z), M("mat_int_brass"), c, thickness=0.005)
    cyl("ware_candle", (TX + 1.02, TY + 0.14, z + 0.115), 0.017, 0.19, "mat_int_wax", c,
        verts=14, bevel=0.004)
    cyl("ware_candleflame", (TX + 1.02, TY + 0.14, z + 0.228), 0.011, 0.038,
        "mat_int_flame_small", c, verts=10, taper=0.05, bevel=0)
    # butter crock + salt
    lathe("ware_butter", [(0.0, 0.0), (0.055, 0.0), (0.058, 0.045), (0.062, 0.05)],
          (TX + 0.20, TY + 0.34, z), M("mat_int_crock"), c, thickness=0.005)
    lathe("ware_salt", [(0.0, 0.0), (0.035, 0.0), (0.038, 0.030)],
          (TX + 0.36, TY + 0.30, z), M("mat_int_crock"), c, thickness=0.004)
    # an onion and a couple of apples, because a supper table is never tidy
    for k, (ox, oy, s, mt) in enumerate(((TX + 1.02, TY - 0.24, 0.048, "mat_int_bread"),
                                         (TX + 0.92, TY - 0.32, 0.045, "mat_int_bread"),
                                         (TX - 1.02, TY - 0.22, 0.052, "mat_int_crock"))):
        sphere("ware_fruit_%d" % k, (ox, oy, z + s * 0.82), s, M(mt), c,
               scale=(1.0, 1.0, 0.85))


def chair(name, loc, rot, c=None):
    c = c or coll("FURNITURE")
    parent = bpy.data.objects.new(name, None)
    coll(c).objects.link(parent)
    parent.location = loc
    parent.rotation_euler = Euler((0, 0, rot))
    SEAT = 0.45
    parts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            back = (sy > 0)
            hz = 0.90 if back else SEAT
            parts.append(box("%s_leg%d%d" % (name, sx, sy),
                             (sx * 0.185, sy * 0.175, hz / 2),
                             (0.028, 0.028, hz / 2), "mat_int_wood", c,
                             rot=(sy * (0.05 if back else 0.03), -sx * 0.03, 0),
                             bevel=0.005, tex_off=toff()))
    parts.append(box("%s_seat" % name, (0, 0, SEAT), (0.205, 0.195, 0.020),
                     "mat_int_wood", c, bevel=0.008, tex_off=toff()))
    for j, z in enumerate((0.62, 0.74, 0.855)):
        parts.append(box("%s_slat%d" % (name, j), (0, 0.20, z), (0.175, 0.014, 0.035),
                         "mat_int_wood", c, bevel=0.006, tex_off=toff()))
    for sx in (-1, 1):
        parts.append(box("%s_rung%d" % (name, sx), (sx * 0.185, 0, 0.20),
                         (0.014, 0.175, 0.014), "mat_int_wood", c, bevel=0.004))
    parts.append(box("%s_rungf" % name, (0, -0.175, 0.22), (0.185, 0.014, 0.014),
                     "mat_int_wood", c, bevel=0.004))
    for p in parts:
        p.parent = parent
    return parent


def build_seating():
    c = coll("FURNITURE")
    chair("chair_a", (TX - 0.78, TY - 0.86, 0.0), math.pi + 0.06)
    chair("chair_b", (TX + 0.06, TY - 0.90, 0.0), math.pi - 0.10)
    chair("chair_c", (TX + 0.92, TY - 0.80, 0.0), math.pi + 0.28)
    chair("chair_d", (TX + 1.52, TY + 0.10, 0.0), -math.pi / 2 + 0.05)
    # bench on the far side
    bench = bpy.data.objects.new("bench_far", None)
    coll(c).objects.link(bench)
    bench.location = (TX + 0.02, TY + 0.92, 0.0)
    bench.rotation_euler = Euler((0, 0, 0.02))
    for i in range(3):
        b = box("bench_top_%d" % i, (0, -0.09 + 0.09 * i, 0.44), (0.90, 0.043, 0.020),
                "mat_int_wood", c, bevel=0.006, tex_off=toff())
        b.parent = bench
    for s in (-1, 1):
        for p in (box("bench_leg_%d" % s, (s * 0.72, 0, 0.215), (0.035, 0.115, 0.215),
                      "mat_int_wood", c, rot=(0, s * 0.04, 0), bevel=0.006,
                      tex_off=toff()),
                  box("bench_foot_%d" % s, (s * 0.72, 0, 0.022), (0.055, 0.145, 0.022),
                      "mat_int_wood", c, bevel=0.006, tex_off=toff())):
            p.parent = bench
    b = box("bench_rail", (0, 0, 0.28), (0.62, 0.030, 0.030), "mat_int_wood", c,
            bevel=0.005)
    b.parent = bench
    # a stool tucked at the head, and a coat thrown over one chair back
    for i, z in enumerate((0.0,)):
        lathe("stool_top", [(0.0, 0.42), (0.17, 0.42), (0.175, 0.40)],
              (TX - 1.52, TY + 0.02, 0.0), M("mat_int_wood"), c, thickness=0.03,
              smooth=False)
        for k in range(3):
            a = k * math.tau / 3 + 0.4
            box("stool_leg_%d" % k, (TX - 1.52 + 0.12 * math.cos(a),
                                     TY + 0.02 + 0.12 * math.sin(a), 0.20),
                (0.020, 0.020, 0.20), "mat_int_wood", c,
                rot=(0.10 * math.sin(a), -0.10 * math.cos(a), 0), bevel=0.004)


# ------------------------------------------------------------------ clutter

def build_settle():
    """High-backed fireside settle in the near corner: foreground mass for the
    composition, and the obvious place to drop a wet coat after the cliff path."""
    c = coll("FURNITURE")
    parent = bpy.data.objects.new("settle", None)
    coll(c).objects.link(parent)
    parent.location = (0.56, 1.22, 0.0)
    parent.rotation_euler = Euler((0, 0, math.pi / 2 + 0.04))
    L = 0.78                      # half length
    parts = []
    for i in range(4):            # seat boards
        parts.append(box("settle_seat_%d" % i, (0, -0.24 + 0.16 * i, 0.44),
                         (L, 0.078, 0.020), "mat_int_wood", c, bevel=0.006,
                         tex_off=toff()))
    for i in range(5):            # back boards
        parts.append(box("settle_back_%d" % i, (0, 0.26, 0.52 + 0.115 * i),
                         (L, 0.020, 0.056), "mat_int_paint_red", c, bevel=0.005,
                         tex_off=toff()))
    parts.append(box("settle_cap", (0, 0.255, 1.075), (L + 0.03, 0.055, 0.035),
                     "mat_int_wood", c, bevel=0.008, tex_off=toff()))
    for s2 in (-1, 1):            # solid ends
        parts.append(box("settle_end_%d" % s2, (s2 * (L - 0.02), 0.02, 0.53),
                         (0.028, 0.30, 0.53), "mat_int_paint_red", c, bevel=0.008,
                         tex_off=toff()))
    parts.append(box("settle_rail", (0, -0.28, 0.16), (L - 0.06, 0.030, 0.030),
                     "mat_int_wood", c, bevel=0.005))
    for p2 in parts:
        p2.parent = parent
    # cushion + a blanket thrown over the back
    cu = plane("settle_cushion", (0.56, 1.22, 0.475), (0.56, 1.42), M("mat_int_rug"),
               c, rot=(0, 0, math.pi / 2 + 0.04), levels=5, disp=0.022)
    sol = cu.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.055
    sol.offset = 0.0
    bl = plane("settle_blanket", (0.40, 1.62, 0.86), (0.44, 0.78), M("mat_int_rug"),
               c, rot=(0.06, math.pi / 2 - 0.10, 1.60), levels=5, disp=0.030)
    sol = bl.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.020


def build_dresser():
    """Crockery dresser on the back wall, between the two doors."""
    c = coll("FURNITURE")
    x0, x1 = 3.05, 4.75
    yb = RD - 0.26
    cx = (x0 + x1) / 2
    box("dresser_carcass", (cx, yb, 0.44), ((x1 - x0) / 2, 0.24, 0.44),
        "mat_int_paint_green", c, bevel=0.010, tex_off=toff())
    box("dresser_top", (cx, yb - 0.02, 0.90), ((x1 - x0) / 2 + 0.04, 0.27, 0.025),
        "mat_int_wood", c, bevel=0.008, tex_off=toff())
    for s in (-1, 1):
        box("dresser_side_%d" % s, (cx + s * ((x1 - x0) / 2 - 0.02), yb + 0.06, 1.52),
            (0.022, 0.18, 0.60), "mat_int_paint_green", c, bevel=0.006, tex_off=toff())
    box("dresser_back", (cx, yb + 0.22, 1.52), ((x1 - x0) / 2, 0.012, 0.60),
        "mat_int_paint_green", c, bevel=0.004, tex_off=toff())
    box("dresser_cornice", (cx, yb + 0.04, 2.14), ((x1 - x0) / 2 + 0.05, 0.21, 0.035),
        "mat_int_paint_red", c, bevel=0.008, tex_off=toff())
    shelves = (1.16, 1.56, 1.96)
    for i, z in enumerate(shelves):
        box("dresser_shelf_%d" % i, (cx, yb + 0.06, z), ((x1 - x0) / 2 - 0.03, 0.17, 0.014),
            "mat_int_wood", c, bevel=0.005, tex_off=toff())
    # cupboard doors below
    for s in (-1, 1):
        box("dresser_door_%d" % s, (cx + s * 0.40, yb - 0.245, 0.46), (0.38, 0.014, 0.36),
            "mat_int_paint_green", c, bevel=0.008, tex_off=toff())
        cyl("dresser_knob_%d" % s, (cx + s * 0.10, yb - 0.27, 0.46), 0.018, 0.03,
            "mat_int_brass", c, axis="Y", verts=10)
    # crockery: plates stood on edge, bowls stacked, jugs and cups on hooks
    cw = coll("TABLEWARE")
    for i, z in enumerate(shelves):
        n = 5
        for k in range(n):
            x = x0 + 0.20 + (x1 - x0 - 0.40) * k / (n - 1)
            kind = (i + k) % 3
            m = "mat_int_crock" if (i + k) % 2 else "mat_int_crock_blue"
            if kind == 0:      # plate on edge, leaning on the back
                lathe("dr_plate_%d%d" % (i, k), [(0.0, 0.0), (0.09, 0.006), (0.115, 0.028)],
                      (x, yb + 0.19, z + 0.13), M(m), cw, thickness=0.006,
                      rot=(math.pi / 2 - 0.16, 0, R.uniform(-0.15, 0.15)))
            elif kind == 1:    # stack of bowls
                for s2 in range(R.randint(2, 3)):
                    lathe("dr_bowl_%d%d_%d" % (i, k, s2),
                          [(0.0, 0.0), (0.040, 0.0), (0.075, 0.028), (0.090, 0.055)],
                          (x + jit(0.01), yb + 0.05, z + 0.012 + 0.035 * s2), M(m), cw,
                          thickness=0.005, rot=(0, 0, R.uniform(0, 3)))
            else:              # jug
                lathe("dr_jug_%d%d" % (i, k),
                      [(0.0, 0.0), (0.052, 0.0), (0.068, 0.045), (0.058, 0.115),
                       (0.036, 0.155), (0.042, 0.175)],
                      (x, yb + 0.05, z + 0.012), M(m), cw, thickness=0.005)
        # cups hanging from the shelf edge
        if i < 2:
            for k in range(4):
                x = x0 + 0.30 + (x1 - x0 - 0.60) * k / 3
                lathe("dr_cup_%d%d" % (i, k),
                      [(0.0, 0.0), (0.032, 0.0), (0.037, 0.030), (0.040, 0.070)],
                      (x, yb - 0.08, z - 0.088), M("mat_int_crock"), cw, thickness=0.004,
                      rot=(0, 0, R.uniform(0, 3)))
                cyl("dr_hook_%d%d" % (i, k), (x, yb - 0.08, z - 0.012), 0.012, 0.008,
                    "mat_int_iron", cw, axis="Z", verts=8)
    # dresser top: a big bowl, a lamp, the day's ledger
    lathe("dr_bigbowl", [(0.0, 0.0), (0.07, 0.0), (0.16, 0.045), (0.185, 0.095)],
          (cx - 0.48, yb - 0.03, 0.915), M("mat_int_crock_blue"), cw, thickness=0.008)
    box("dr_ledger", (cx + 0.44, yb - 0.04, 0.935), (0.11, 0.075, 0.018),
        "mat_int_paper", cw, rot=(0, 0, 0.3), bevel=0.004)
    box("dr_ledger_cover", (cx + 0.44, yb - 0.04, 0.955), (0.115, 0.08, 0.006),
        "mat_int_oilskin", cw, rot=(0, 0, 0.3), bevel=0.004)


def cloth_hang(name, loc, w, h, mat, c, rot=0.0, fold=0.05):
    """A coat/oilskin hanging off a peg: a plane, rumpled and thickened."""
    o = plane(name, loc, (w, h), mat, c, rot=(math.pi / 2, 0, rot), levels=5,
              disp=fold)
    s = o.modifiers.new("sol", "SOLIDIFY")
    s.thickness = 0.012
    s.offset = 0
    return o


def build_clutter(kit):
    c = coll("PROPS")
    # --- oilskins on hooks, left wall by the back corner --------------------
    box("hook_rail", (0.78, RD - 0.10, 1.86), (0.60, 0.030, 0.055), "mat_int_beam", c,
        bevel=0.006, tex_off=toff())
    for i, x in enumerate((0.34, 0.78, 1.20)):
        cyl("hook_%d" % i, (x, RD - 0.16, 1.80), 0.013, 0.13, "mat_int_iron", c,
            axis="Y", verts=8)
        if i < 2:
            cloth_hang("oilskin_%d" % i, (x, RD - 0.30 - 0.03 * i, 1.26), 0.40, 1.00,
                       M("mat_int_oilskin"), c, rot=jit(0.06))
            box("oilskin_shoulder_%d" % i, (x, RD - 0.31 - 0.03 * i, 1.70),
                (0.19, 0.075, 0.055), "mat_int_oilskin", c, rot=(0, jit(0.05), 0),
                bevel=0.035)
            cloth_hang("oilskin_hem_%d" % i, (x, RD - 0.36 - 0.03 * i, 0.90), 0.50, 0.34,
                       M("mat_int_oilskin"), c, rot=jit(0.08), fold=0.08)
        else:
            cloth_hang("scarf_%d" % i, (x, RD - 0.28, 1.44), 0.24, 0.70,
                       M("mat_int_rug"), c, rot=jit(0.1), fold=0.03)
    # a sou'wester hat on the last hook
    lathe("oilskin_hat", [(0.0, 0.10), (0.075, 0.095), (0.10, 0.03), (0.155, 0.0)],
          (1.20, RD - 0.30, 1.72), M("mat_int_oilskin"), c, thickness=0.010,
          rot=(0.25, 0.1, 0))

    # --- tide / lock chart on the back wall --------------------------------
    CY = 6.15                       # left wall, between the hearth and the corner
    ch = plane("chart_paper", (0.055, CY, 1.86), (0.66, 0.92), M("mat_int_paper"),
               c, rot=(math.pi / 2, 0, math.pi / 2 + 0.02), levels=4, disp=0.012)
    for k in range(7):
        z = 1.86 - 0.26 + 0.082 * k
        box("chart_line_%d" % k, (0.075, CY + jit(0.02), z),
            (0.002, R.uniform(0.11, 0.29), 0.004), "mat_int_ink", c, bevel=0)
    for k in range(4):
        box("chart_step_%d" % k, (0.075, CY - 0.22 + 0.145 * k, 1.66 + 0.058 * k),
            (0.002, 0.068, 0.006), "mat_int_ink", c, bevel=0)
    for sy in (-1, 1):
        for sz in (-1, 1):
            cyl("chart_pin_%d%d" % (sy, sz), (0.09, CY + sy * 0.30, 1.86 + sz * 0.42),
                0.010, 0.03, "mat_int_iron", c, axis="X", verts=8)

    # --- log basket + split logs beside the hearth -------------------------
    bx, by = 0.92, 5.30
    for k in range(11):
        a = k * math.tau / 11
        cyl("basket_stave_%d" % k, (bx + 0.30 * math.cos(a), by + 0.30 * math.sin(a), 0.20),
            0.026, 0.40, "mat_int_bowlwood", c, verts=7,
            rot=(0.06 * math.sin(a), -0.06 * math.cos(a), 0), bevel=0.003)
    for k, z in enumerate((0.07, 0.22, 0.375)):
        cyl("basket_band_%d" % k, (bx, by, z), 0.325, 0.038, "mat_int_bowlwood", c,
            verts=26, bevel=0.006)
    for k in range(9):
        cyl("basket_log_%d" % k,
            (bx + R.uniform(-0.16, 0.16), by + R.uniform(-0.16, 0.16),
             0.20 + R.uniform(0.0, 0.26)),
            R.uniform(0.035, 0.062), R.uniform(0.30, 0.44), "mat_int_bowlwood", c,
            verts=8, axis="X",
            rot=(0, R.uniform(-0.3, 0.3), R.uniform(0, 3.1)), bevel=0.006)
    for k in range(3):                     # a few spilled on the floor
        cyl("floor_log_%d" % k, (bx + R.uniform(0.35, 0.62), by + R.uniform(-0.35, 0.3),
                                 0.05),
            R.uniform(0.04, 0.055), R.uniform(0.30, 0.40), "mat_int_bowlwood", c,
            verts=8, axis="X", rot=(0, 0, R.uniform(0, 3.1)), bevel=0.006)

    # --- left wall, above the settle: shelf of odds and a peg rail ----------
    box("lshelf", (0.30, 1.30, 1.42), (0.19, 0.78, 0.020), "mat_int_wood", c,
        bevel=0.006, tex_off=toff())
    for yy in (0.62, 1.98):
        box("lshelf_brk_%.1f" % yy, (0.20, yy, 1.31), (0.11, 0.024, 0.11),
            "mat_int_beam", c, rot=(0.7, 0, 0), bevel=0.004)
    cw0 = coll("TABLEWARE")
    for k, yy in enumerate((0.72, 1.02, 1.34, 1.66, 1.94)):
        m = "mat_int_crock" if k % 2 else "mat_int_crock_blue"
        lathe("lshelf_pot_%d" % k, [(0.0, 0.0), (0.050, 0.0), (0.062, 0.045),
                                    (0.046, 0.115), (0.054, 0.132)],
              (0.30 + jit(0.02), yy, 1.445), M(m), cw0, thickness=0.005,
              rot=(0, 0, R.uniform(0, 3)))
    box("lpeg_rail", (0.12, 1.30, 2.02), (0.035, 0.80, 0.045), "mat_int_beam", c,
        bevel=0.005, tex_off=toff())
    for k, yy in enumerate((0.68, 1.10, 1.52, 1.94)):
        cyl("lpeg_%d" % k, (0.24, yy, 2.02), 0.014, 0.16, "mat_int_wood", c, axis="X",
            verts=8)
    # a saw and a coil of light line hung on the pegs
    box("lwall_saw", (0.30, 0.68, 1.72), (0.012, 0.10, 0.30), "mat_int_iron", c,
        rot=(0, 0.05, 0), bevel=0.004)
    cyl("lwall_coil", (0.30, 1.52, 1.86), 0.13, 0.055, "mat_rope"
        if bpy.data.materials.get("mat_rope") else "mat_int_bowlwood", c, axis="X",
        verts=20)

    # --- right wall: work bench with keeper gear ---------------------------
    bx0, bx1 = RW - 0.62, RW - 0.04
    box("bench_work_top", ((bx0 + bx1) / 2, 3.35, 0.86), ((bx1 - bx0) / 2, 0.95, 0.030),
        "mat_int_wood", c, bevel=0.008, tex_off=toff())
    for yy in (2.50, 4.18):
        box("bench_work_leg_%.0f" % yy, (RW - 0.30, yy, 0.43), (0.045, 0.045, 0.43),
            "mat_int_wood", c, bevel=0.006, tex_off=toff())
        box("bench_work_brace_%.0f" % yy, (RW - 0.30, yy, 0.20), (0.032, 0.55, 0.026),
            "mat_int_wood", c, bevel=0.005, tex_off=toff())
    # shelf above it, with more crockery and tins
    box("shelf_right", (RW - 0.42, 3.35, 1.52), (0.20, 0.92, 0.022), "mat_int_wood", c,
        bevel=0.006, tex_off=toff())
    for s in (-1, 1):
        box("shelf_right_brk_%d" % s, (RW - 0.30, 3.35 + s * 0.78, 1.40),
            (0.10, 0.024, 0.10), "mat_int_beam", c, rot=(0, 0.7, 0), bevel=0.004)
    cw = coll("TABLEWARE")
    for k in range(5):
        y = 2.70 + 0.32 * k
        m = "mat_int_crock" if k % 2 else "mat_int_crock_blue"
        lathe("shelf_pot_%d" % k, [(0.0, 0.0), (0.055, 0.0), (0.070, 0.05),
                                   (0.052, 0.13), (0.060, 0.15)],
              (RW - 0.42 + jit(0.03), y, 1.545), M(m), cw, thickness=0.005,
              rot=(0, 0, R.uniform(0, 3)))
    # lock tools on the bench: a wrench, a tin of grease, a lantern
    box("tool_wrench", (RW - 0.36, 2.72, 0.895), (0.14, 0.028, 0.012), "mat_int_iron", c,
        rot=(0, 0, 0.6), bevel=0.005)
    lathe("tool_greasetin", [(0.0, 0.0), (0.065, 0.0), (0.068, 0.075)],
          (RW - 0.30, 3.02, 0.876), M("mat_int_iron"), c, thickness=0.005)
    box("tool_rag", (RW - 0.34, 4.02, 0.885), (0.10, 0.11, 0.014), "mat_int_linen", c,
        rot=(0, 0, 0.4), bevel=0.010)

    # --- rug under the table ------------------------------------------------
    # Built as field + border + fringe: a single displaced plane reads as a
    # doormat, and the border is what makes the eye call it a rug.
    RX, RY, RA = TX - 0.32, TY - 0.18, 0.035
    FW, FD = 2.86, 2.02                       # field
    BW = 0.20                                 # border width
    sh = coll("SHELL")

    def rugpart(name, cx, cy, w, d, mat, z=0.010):
        o = plane(name, (cx, cy, z), (w, d), M(mat), sh, rot=(0, 0, RA),
                  levels=5, disp=0.009)
        sol = o.modifiers.new("sol", "SOLIDIFY")
        sol.thickness = 0.011
        sol.offset = 1.0
        return o

    ca, sa = math.cos(RA), math.sin(RA)

    def R2(dx, dy):
        return (RX + dx * ca - dy * sa, RY + dx * sa + dy * ca)

    rugpart("walk_rug", *R2(0, 0), FW, FD, "mat_int_rug")
    for sgn in (-1, 1):
        x, y = R2(sgn * (FW / 2 + BW / 2), 0)
        rugpart("walk_rug_bordX_%d" % sgn, x, y, BW, FD + 2 * BW, "mat_int_rug_border",
                z=0.0104)
        x, y = R2(0, sgn * (FD / 2 + BW / 2))
        rugpart("walk_rug_bordY_%d" % sgn, x, y, FW, BW, "mat_int_rug_border", z=0.0104)
    for sgn in (-1, 1):                       # inner stripe
        x, y = R2(sgn * (FW / 2 - 0.16), 0)
        rugpart("walk_rug_stripe_%d" % sgn, x, y, 0.075, FD - 0.30, "mat_int_rug_border",
                z=0.0125)
    for sgn in (-1, 1):                       # fringe
        for k in range(34):
            dx = sgn * (FW / 2 + BW + 0.045)
            dy = -FD / 2 - BW + 0.03 + (FD + 2 * BW - 0.06) * k / 33.0
            x, y = R2(dx, dy)
            cyl("rug_fringe_%d_%02d" % (sgn, k), (x, y, 0.008), 0.006, 0.085,
                "mat_int_rug_border", sh, axis="X", verts=5,
                rot=(0, 0, RA + jit(0.10)), bevel=0)

    # --- hanging things under the beams -------------------------------------
    for i, (x, y) in enumerate(((2.15, 3.55), (2.55, 3.55), (6.9, 2.15))):
        for k in range(7):
            cyl("herb_%d_%d" % (i, k), (x + jit(0.035), y + jit(0.035), BEAM_Z - 0.28),
                0.008, R.uniform(0.22, 0.34), "mat_int_bowlwood", c, verts=6,
                rot=(jit(0.12), jit(0.12), 0), bevel=0)
        cyl("herb_tie_%d" % i, (x, y, BEAM_Z - 0.10), 0.028, 0.05, "mat_int_rope"
            if bpy.data.materials.get("mat_rope") is None else "mat_rope", c, verts=10)
    # onion string
    for k in range(6):
        sphere("onion_%d" % k, (7.35, 5.15, BEAM_Z - 0.16 - 0.10 * k), 0.055,
               M("mat_int_bread"), c, scale=(1.0, 1.0, 0.9))

    # --- kit props ----------------------------------------------------------
    place_kit(kit["kit_rope_coil"], "prop_rope_coil_a", (RW - 0.52, 4.72, 0.90),
              rot=(0, 0, 0.6))
    place_kit(kit["kit_rope_coil"], "prop_rope_coil_b", (RW - 0.72, 1.35, 0.02),
              rot=(0.02, 0, 1.9))
    place_kit(kit["kit_bucket"], "prop_bucket", (1.28, 6.22, 0.0), rot=(0, 0, 0.7))
    place_kit(kit["kit_crate"], "prop_crate", (RW - 0.56, 5.65, 0.0), rot=(0, 0, -0.22))
    place_kit(kit["kit_barrel"], "prop_barrel", (RW - 0.60, 6.45, 0.0), rot=(0, 0, 0.5))
    for i in range(3):
        place_kit(kit["kit_railing_1m"], "balc_rail_%d" % i,
                  (6.1 + i * 1.0, RD + 2.05, 0.0), c="BEYOND", remap=True)


# ------------------------------------------------------------------ lights

def light(name, kind, loc, energy, color, size=0.25, c="LIGHTS", rot=(0, 0, 0),
          spread=None, shape=None, sx=1.0, sy=1.0):
    ld = bpy.data.lights.new(name, type=kind)
    ld.energy = energy
    ld.color = color
    if kind == "POINT":
        ld.shadow_soft_size = size
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
    return ob


def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def hang_lantern(kit, name, x, y, z, hang_from=BEAM_Z - 0.14, energy=70.0):
    """Kit lantern on a real chain up to a beam, plus its own warm point."""
    place_kit(kit["kit_lantern_hanging"], name, (x, y, z), c="PROPS")
    n = max(1, int((hang_from - z - 0.16) / 0.055))
    for k in range(n):
        cyl("%s_chain_%02d" % (name, k), (x, y, z + 0.18 + 0.055 * k), 0.016, 0.030,
            "mat_int_iron", coll("PROPS"), axis="Y" if k % 2 else "X", verts=8,
            bevel=0.002)
    cyl("%s_hook" % name, (x, y, hang_from - 0.02), 0.014, 0.09, "mat_int_iron",
        coll("PROPS"), verts=8)
    light("LGT_%s" % name, "POINT", (x, y, z + 0.02), energy, (1.0, 0.60, 0.27), 0.09)


def build_lights(kit):
    fy = 3.72
    # hearth: a hot core, a soft bloom, and a low bounce off the hearthstone
    # A single point light at the flames cannot both model the fire and light the
    # room: inverse square means whatever reaches the far wall has already blown
    # the firebox out to white.  So the flames get a small local light, and the
    # room is lit by an area light sitting IN THE PLANE OF THE OPENING, facing
    # out -- it throws the warm pool across the floor without touching the
    # sooty interior behind it.
    light("LGT_fire_core", "POINT", (0.20, fy, 0.26), 88.0, (1.0, 0.375, 0.090), 0.13)
    mouth = light("LGT_fire_mouth", "AREA", (0.66, fy, 0.66), 235.0,
                  (1.0, 0.435, 0.145), shape="RECTANGLE", sx=1.25, sy=1.05, spread=178)
    aim(mouth, (4.6, fy - 0.9, 0.9))
    light("LGT_fire_spill", "POINT", (1.15, fy - 0.30, 0.24), 55.0, (1.0, 0.44, 0.16), 0.55)
    # what the firelight throws back off the hearthstone and the near floor
    b = light("LGT_fire_bounce", "AREA", (1.55, fy - 0.10, 0.16), 42.0,
              (1.0, 0.52, 0.24), shape="RECTANGLE", sx=2.4, sy=2.0, spread=170)
    aim(b, (3.6, 3.2, 1.5))

    # table lantern + a second by the town door, both hung off the beams
    hang_lantern(kit, "lantern_table", TX - 0.05, 3.55, 1.80, energy=165.0)
    hang_lantern(kit, "lantern_door", 2.72, RD - 0.48, 2.05, hang_from=BEAM_Z - 0.14,
                 energy=58.0)
    light("LGT_candle", "POINT", (TX + 1.02, TY + 0.14, TH + 0.24), 9.0,
          (1.0, 0.63, 0.25), 0.035)
    c = coll("PROPS")
    lathe("benchlamp_base", [(0.0, 0.0), (0.070, 0.0), (0.072, 0.028), (0.050, 0.050)],
          (RW - 0.40, 3.92, 0.888), M("mat_int_brass"), c, thickness=0.005)
    cyl("benchlamp_glass", (RW - 0.40, 3.92, 1.005), 0.052, 0.145, "mat_int_lampglass",
        c, verts=16, bevel=0)
    lathe("benchlamp_top", [(0.0, 0.085), (0.052, 0.045), (0.066, 0.0)],
          (RW - 0.40, 3.92, 1.078), M("mat_int_brass"), c, thickness=0.005)
    light("LGT_benchlamp", "POINT", (RW - 0.40, 3.92, 1.00), 42.0, (1.0, 0.62, 0.28),
          0.05)

    # dusk through the ajar river door
    d = light("LGT_dusk_door", "AREA", (7.25, RD + 0.55, 1.35), 210.0,
              (0.36, 0.55, 1.0), shape="RECTANGLE", sx=1.65, sy=2.10, spread=110)
    aim(d, (5.6, 2.6, 0.35))
    d2 = light("LGT_dusk_glass", "AREA", (7.3, RD + 0.42, 1.30), 42.0,
               (0.30, 0.48, 1.0), shape="RECTANGLE", sx=1.6, sy=2.0, spread=150)
    aim(d2, (6.6, 3.5, 0.9))
    # dusk through the right-hand window
    w = light("LGT_dusk_window", "AREA", (RW + 0.35, 1.95, 2.05), 68.0,
              (0.34, 0.52, 1.0), shape="RECTANGLE", sx=0.95, sy=0.80, spread=120)
    aim(w, (6.4, 3.2, 0.35))

    # the barest ambient so the near-camera floor is not pure black; warm, low
    f = light("LGT_fill_room", "AREA", (4.6, -1.4, 2.6), 30.0, (1.0, 0.74, 0.50),
              shape="RECTANGLE", sx=7.0, sy=3.4, spread=150)
    aim(f, (4.6, 3.4, 0.6))
    # kick under the beams so the ceiling timbers are not lost
    # The tie beams sit between the lens and the room, so an unlit underside
    # reads as a black bar across the frame.  This uplight is what turns them
    # back into timber.
    k = light("LGT_beam_kick", "AREA", (4.4, 3.1, 1.55), 62.0, (1.0, 0.63, 0.31),
              shape="RECTANGLE", sx=4.6, sy=3.4, spread=150)
    aim(k, (4.4, 3.5, 2.6))
    k2 = light("LGT_beam_kick_L", "AREA", (1.55, 3.5, 1.30), 34.0, (1.0, 0.55, 0.24),
               shape="RECTANGLE", sx=2.2, sy=2.6, spread=150)
    aim(k2, (1.55, 3.6, 2.6))

    # world: near-black with a cold cast, so any opening reads as dusk
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.020, 0.035, 0.070, 1.0)
    bg.inputs[1].default_value = 0.35


def build_fog():
    """BOUNDED volume only -- a world volume extinguishes everything (see
    KITLIB_MANIFEST).  This box holds the room and the balcony beyond it."""
    mat = bpy.data.materials.get("mat_int_fog") or bpy.data.materials.new("mat_int_fog")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (1.0, 0.86, 0.70, 1.0)
    sc.inputs["Density"].default_value = 0.0075
    sc.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(sc.outputs["Volume"], out.inputs["Volume"])
    b = box("FOG_BOX_INT", (5.20, RD / 2 + 1.2, 2.1),
            (4.35, RD / 2 + 2.6, 2.35), mat, coll("LIGHTS"), bevel=0)
    b.visible_shadow = False
    return b


# ------------------------------------------------------------------ camera

CAM = dict(aim=(4.58, 3.38, 1.24), vh=6.50, pitch=24.0, az=11.5, fov=35.0)


def build_camera():
    cd = bpy.data.cameras.new("CAM_cottage_int")
    cd.sensor_fit = "VERTICAL"
    cd.angle_y = math.radians(CAM["fov"])
    cd.clip_end = 400.0
    cam = bpy.data.objects.new("CAM_cottage_int", cd)
    coll("CAM").objects.link(cam)
    aimpt = Vector(CAM["aim"])
    vh = CAM["vh"]                               # world units framed vertically
    dist = (vh / 2) / math.tan(math.radians(CAM["fov"]) / 2)
    az, pitch = math.radians(CAM["az"]), math.radians(CAM["pitch"])
    d = Vector((math.sin(az) * math.cos(pitch), -math.cos(az) * math.cos(pitch),
                math.sin(pitch)))
    cam.location = aimpt + d * dist
    cam.rotation_euler = (aimpt - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def setup_render(samples=224, res=(1344, 768), exposure=0.58):
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
        sc.view_settings.look = "AgX - Medium High Contrast"
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


# ------------------------------------------------------------------ main

def wipe():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def build(ref_human=False):
    wipe()
    CM.make_all()
    kit = append_kit(["kit_rope_coil", "kit_bucket", "kit_crate", "kit_barrel",
                      "kit_lantern_hanging", "kit_lantern_light", "kit_railing_1m",
                      "REF_human_1p7"])
    build_shell()
    build_hearth()
    hearth_mantel_clutter()
    build_town_door()
    build_river_door()
    build_window_right()
    punch_window_hole()
    build_dusk_backdrop()
    build_exterior_roof()
    build_table()
    build_tableware()
    build_seating()
    build_dresser()
    build_settle()
    build_clutter(kit)
    build_lights(kit)
    apply_cutaway()
    build_fog()
    build_camera()
    if ref_human:
        place_kit(kit["REF_human_1p7"], "REF_scale_a", (3.30, 1.85, 0.0), c="CAM")
        place_kit(kit["REF_human_1p7"], "REF_scale_b", (TX + 1.10, TY - 1.30, 0.0),
                  c="CAM")
    qa_report()
    bad = CM.verify()
    if bad:
        print("MATERIAL WARNINGS:", bad)
    n = len([o for o in bpy.data.objects if o.type == "MESH"])
    print("BUILD OK: %d meshes, %d lights" % (
        n, len([o for o in bpy.data.objects if o.type == "LIGHT"])))


def qa_report():
    """Print the things the scene contract is judged on."""
    bpy.context.view_layer.update()
    def bb(name):
        o = bpy.data.objects.get(name)
        if not o:
            return None
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return (min(p.z for p in pts), max(p.z for p in pts))
    walk = sorted({o.name.split("_")[1] for o in bpy.data.objects
                   if o.name.startswith("walk_")})
    nwalk = len([o for o in bpy.data.objects if o.name.startswith("walk_")])
    floor = [o for o in bpy.data.objects if o.name.startswith("walk_floorboard")]
    ftop = max(max((o.matrix_world @ Vector(c)).z for c in o.bound_box) for o in floor)
    print("QA walk_ objects: %d in groups %s" % (nwalk, walk))
    print("QA walk_pad_door present: %s" % bool(bpy.data.objects.get("walk_pad_door")))
    print("QA floor top z = %.3f (character datum should be 0.000)" % ftop)
    print("QA town door leaf height = 2.10, opening top z = 2.24")
    print("QA table top z = %.3f  chair seat z = 0.450" % TH)
    print("QA hidden-from-camera meshes: %d" % len([o for o in bpy.data.objects
                                                    if o.type == "MESH" and not o.visible_camera]))
    print("QA camera %s" % CAM)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = None
    samples = 224
    res = (1344, 768)
    ref = False
    save = True
    exposure = 0.58
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--render":
            out = argv[i + 1]; i += 1
        elif a == "--samples":
            samples = int(argv[i + 1]); i += 1
        elif a == "--exposure":
            exposure = float(argv[i + 1]); i += 1
        elif a == "--res":
            res = tuple(int(v) for v in argv[i + 1].split("x")); i += 1
        elif a == "--cam":
            for kv in argv[i + 1].split(","):
                k, v = kv.split("=")
                CAM[k] = float(v) if k != "aim" else CAM["aim"]
            i += 1
        elif a == "--aim":
            CAM["aim"] = tuple(float(v) for v in argv[i + 1].split(",")); i += 1
        elif a == "--ref":
            ref = True
        elif a == "--nosave":
            save = False
        i += 1
    build(ref_human=ref)
    setup_render(samples=samples, res=res, exposure=exposure)
    if save:
        os.makedirs(os.path.dirname(OUTBLEND), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=OUTBLEND)
        print("SAVED", OUTBLEND)
    if out:
        render_to(out)


if __name__ == "__main__":
    main()
