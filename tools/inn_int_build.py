#!/usr/bin/env python3
"""Dellhollow INN common room -- "The Boatmen's Rest" (sceneKey del-inn-int).

Dellhollow is a lock-town in a gorge. When the locks go down, travellers are
stranded, and THIS is the room they are stranded in: the ground-floor common
room at dusk, where they wait, eat, dry their coats and grumble.

    FF9 cutaway: floor + back wall + two side walls, no near wall and no
    visible ceiling. Cutaway by camera VISIBILITY, not by deleting geometry.
    ONE fixed perspective camera, sensor_fit VERTICAL, vfov 35 deg, ~23.5 deg
    down. Room 10 x 7u -- the largest interior in the set, because it seats a
    crowd.

    wall          feature                       filler
    -----------   ---------------------------   ---------------------------
    LEFT   x=-5   HEARTH (live fire)            peg rail, coats, sticks,
                                                firewood, drying boots
    BACK   y=+3.5 DOOR (entry) / NOTICE BOARD   luggage mountain, coat pegs,
                  / RECEPTION COUNTER           key rack, inn sign
    RIGHT  x=+5   WINDOW (dusk) / STAIRCASE     under-stair luggage

    centre        the LONG SHARED TABLE -- benches, mugs, a card game in
                  progress, a candle. The sociable heart of the frame.

Scale contract: character 1.7u, door 2.1u, tables 0.75u, counter 1.05u.
Engine contract: `walk_floor` is the walkable mesh; `walk_pad_door` and
`walk_pad_counter` are interaction pads (hide_render -- metadata, not dressing).

Run headless:
    Blender -b -P tools/inn_int_build.py -- \
        --out tools/blends/interiors/inn-int.blend \
        --render docs/qa/interiors/inn-int_v1.png --samples 224
"""
import bpy, bmesh, math, os, random, sys, importlib.util
from mathutils import Matrix, Vector, Euler, noise

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TOOLS = os.path.join(ROOT, "tools")


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


pb = _mod("probe_build")            # Mesh / append_from_kit helpers
nm = _mod("inn_int_materials")      # this scene's material library
ru = _mod("render_util")

R = random.Random(70407)

# ---------------------------------------------------------------- room shape
HW = 5.00                 # half width -> x in [-5, 5]   (10u -- the big room)
YB, YF = 3.50, -3.50      # back wall plane / open front edge (7u deep)
WH = 3.00                 # wall height (matches the 3x3 kit panels)
CLAD = 0.126              # kit panel: cladding front face sits this far in
IX = HW - CLAD            # inner face of the side walls  (4.874)
IY = YB - CLAD            # inner face of the back wall   (3.374)

WAINS = 1.02              # top of the moss-green wainscot
RAIL_Z = 1.82             # peg rail height

BEAM_Z = 2.86             # ceiling beams tucked up under the plate: any lower
BEAM_H = 0.070            # and a beam becomes a black bar across the frame
# v1 shipped four FULL-WIDTH beams and they were four black bars straight
# across the picture, one of them sitting on the counter. In a 7u-deep room a
# beam at z=2.86 projects to a different frame height for every y, so the set
# sweeps the whole wall. Only the BACK beam may run full width -- up there it
# merges with the top plate and reads as ceiling. Everything forward of that is
# a stub against one wall, which reads as structure instead of as a bar.
BEAMS = ((-2.30, 2.55, HW), (-0.55, -HW, -1.90), (2.45, -HW, HW))
BEAM_POST = (2.55, -2.30)  # the post carrying the front-right stub

DOOR_X = -3.40            # centre of the back-wall door bay
# Window bay centre. At -1.35 the pane projected to u=0.98 -- hard against the
# right frame edge, where the one cool value note in the room is worth nothing.
# Moved back until it sits inside the crop, checked with world_to_camera_view.
WIN_Y = -0.70

CTR_X0, CTR_X1 = 0.70, 3.10        # reception counter
CTR_Y0, CTR_Y1 = 1.85, 2.60
CTR_H = 1.05                       # project standard

STR_X0, STR_X1 = 3.22, IX          # staircase bay, rising in +Y
STR_Y0 = 1.20
STR_RISE, STR_RUN, STR_N = 0.22, 0.30, 7

TBL_X0, TBL_X1 = -2.85, 2.35       # the long shared table
TBL_Y0, TBL_Y1 = -1.05, -0.15
TBL_H = 0.75

HRTH_Y0, HRTH_Y1 = -1.95, 1.05     # hearth breast on the left wall
HRTH_XF = -3.90                    # front face of the breast
OPEN_Y0, OPEN_Y1 = -1.52, 0.62     # fire opening
OPEN_Z = 1.22
MANTEL_Z = 1.30


def M(n):
    m = bpy.data.materials.get(n)
    if m is None:
        raise KeyError("material missing: %s" % n)
    return m


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


# ------------------------------------------------------------------ meshing

class IMesh(pb.Mesh):
    """probe_build.Mesh plus the primitives an inn needs: lathes for turned
    and coopered ware, strands for cordage and ironwork, spheres for produce,
    and hanging cloth for the coats that make the room feel occupied."""

    def sphere(self, center, r, mat, seg=12, rings=7, scale=(1, 1, 1), rot=(0, 0, 0)):
        try:
            res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg,
                                            v_segments=rings, radius=1.0)
        except TypeError:
            res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg,
                                            v_segments=rings, diameter=1.0)
        self.stamp(res["verts"], mat,
                   Matrix.Translation(center)
                   @ Euler(rot, "XYZ").to_matrix().to_4x4()
                   @ Matrix.Diagonal((r * scale[0], r * scale[1], r * scale[2], 1.0)))

    def lathe(self, base, profile, mat, seg=14, aspect=(1.0, 1.0), lumpy=0.0,
              seed=0.0, rot=0.0):
        """profile: [(radius, z), ...] bottom to top. Start/end at r=0 to cap."""
        rows = []
        for r, z in profile:
            row = []
            for k in range(seg + 1):
                a = rot + 2 * math.pi * k / seg
                rr = r
                if lumpy and r > 1e-4:
                    rr = r * (1.0 + lumpy * noise.noise(
                        Vector((math.cos(a) * 2.2, math.sin(a) * 2.2, z * 3.1 + seed))))
                row.append((base[0] + rr * aspect[0] * math.cos(a),
                            base[1] + rr * aspect[1] * math.sin(a),
                            base[2] + z))
            rows.append(row)
        self.quad_strip(rows, mat)

    def strand(self, pts, r, mat, seg=6, r2=None):
        for a, b in zip(pts[:-1], pts[1:]):
            a, b = Vector(a), Vector(b)
            d = b - a
            if d.length < 1e-5:
                continue
            e = d.to_track_quat("Z", "Y").to_euler()
            self.cyl(tuple((a + b) / 2), r, d.length * 1.04, mat, seg=seg,
                     rot=(e.x, e.y, e.z), r2=r2)

    def ring(self, center, r, tube, mat, axis="Z", seg=10):
        pts = []
        for k in range(seg + 1):
            a = 2 * math.pi * k / seg
            c, s = math.cos(a) * r, math.sin(a) * r
            if axis == "Z":
                pts.append((center[0] + c, center[1] + s, center[2]))
            elif axis == "X":
                pts.append((center[0], center[1] + c, center[2] + s))
            else:
                pts.append((center[0] + c, center[1], center[2] + s))
        self.strand(pts, tube, mat, seg=4)

    def cloth(self, top, u, nrm, w, h, mat, mat_top=None, taper=0.45,
              folds=4, bulge=0.075, seed=0.0, nu=9, nv=7):
        """A garment hanging off a peg: narrow at the shoulder, widening and
        rippling as it falls. Coats and oilskins on peg rails are the single
        cheapest way to say 'people are stuck here waiting'."""
        u = Vector(u).normalized()
        n = Vector(nrm).normalized()
        top = Vector(top)
        rows = []
        for i in range(nv + 1):
            t = i / nv
            ww = w * (taper + (1.0 - taper) * min(1.0, t * 1.7))
            row = []
            for j in range(nu + 1):
                s = (j / nu - 0.5) * ww
                ripple = math.sin(folds * math.pi * (j / nu) + seed) * bulge * (0.25 + t)
                drop = h * t + 0.045 * math.sin(2.4 * (j / nu) + seed) * t
                p = top + u * s + n * (ripple + 0.035) + Vector((0, 0, -drop))
                row.append(tuple(p))
            rows.append(row)
        self.quad_strip(rows, mat_top or mat)
        # a back face so the coat is not a one-sided sliver from the far side
        rows2 = []
        for i in range(nv + 1):
            t = i / nv
            ww = w * (taper + (1.0 - taper) * min(1.0, t * 1.7)) * 0.97
            row = []
            for j in range(nu + 1):
                s = (j / nu - 0.5) * ww
                ripple = math.sin(folds * math.pi * (j / nu) + seed) * bulge * 0.45 * (0.25 + t)
                drop = h * t + 0.045 * math.sin(2.4 * (j / nu) + seed) * t
                p = top + u * s + n * (ripple - 0.012) + Vector((0, 0, -drop))
                row.append(tuple(p))
            rows2.append(row)
        self.quad_strip(rows2, mat)


def sagline(p0, p1, dz, n=10):
    """Parabolic sag between two points -- cordage, chain, a washing line."""
    p0, p1 = Vector(p0), Vector(p1)
    out = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t)
        p.z -= dz * 4.0 * t * (1.0 - t)
        out.append(tuple(p))
    return out


def textob(name, body, size, mat, loc, rot, c, extrude=0.006, align="CENTER",
           spacing=1.0):
    """A real text datablock. The lock-schedule slate and the inn sign are the
    two places in this room where the STORY is literally written down, so they
    get legible type rather than squiggle geometry."""
    cu = bpy.data.curves.new(name, type="FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.space_character = spacing
    ob = bpy.data.objects.new(name, cu)
    ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = rot
    c.objects.link(ob)
    return ob


# ------------------------------------------------------------------ the kit

KIT_NAMES = ["kit_wall_door", "kit_wall_window", "kit_wall_plain", "kit_barrel",
             "kit_crate", "kit_bucket", "kit_rope_coil", "kit_lantern_hanging",
             "kit_lantern_light", "kit_beam", "REF_human_1p7",
             "SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX"]

# kit exterior material -> interior equivalent. The kit's moss layer is driven
# by the world-up normal: right for a river town, wrong inside an inn.
RESKIN = {
    "mat_wallwood":      "mat_n_wall",
    "mat_timber":        "mat_n_green",
    "mat_wallwood_dark": "mat_n_oxblood",
    "mat_iron":          "mat_n_iron",
    "mat_glass_dark":    "mat_n_dusk",
    "mat_deck":          "mat_n_floor",
    "mat_lantern_glass": "mat_n_lampglass",
}


def reskin(ob, extra=None):
    table = dict(RESKIN)
    table.update(extra or {})
    for i, slot in enumerate(ob.data.materials):
        if slot is None:
            continue
        new = table.get(slot.name)
        if new and bpy.data.materials.get(new):
            ob.data.materials[i] = bpy.data.materials[new]
    return ob


def place(src, loc, rot=(0, 0, 0), c=None, extra=None):
    ob = src.copy()
    ob.data = src.data.copy()
    ob.location = loc
    ob.rotation_euler = rot
    (c or bpy.context.scene.collection).objects.link(ob)
    reskin(ob, extra)
    return ob


def place_lantern(src, loc, c, energy=48.0, warm=(1.0, 0.60, 0.28)):
    """Copy the kit lantern AND its child point light. Appending brings the
    light with it, but a plain copy() does not re-parent the child."""
    lamp = place(src, loc, c=c)
    lit_src = bpy.data.objects.get("kit_lantern_light")
    if lit_src is None:
        return lamp
    lit = lit_src.copy()
    lit.data = lit_src.data.copy()
    lit.data.energy = energy
    lit.data.color = warm
    lit.data.shadow_soft_size = 0.05
    c.objects.link(lit)
    lit.parent = lamp
    lit.matrix_parent_inverse = Matrix.Identity(4)
    return lamp


# ------------------------------------------------------------------- shell

def build_floor(c):
    """`walk_floor`: real plank geometry with three de-correlated materials
    dealt out board by board. The gaps plus the material rotation between them
    are what stop a 1k texture tiling visibly across 10 x 7 units."""
    m = IMesh("walk_floor")
    mats = [M("mat_n_floor"), M("mat_n_floor_b"), M("mat_n_floor_c"),
            M("mat_n_floor_d"), M("mat_n_floor_e")]
    x = -HW - 0.05
    i = 0
    while x < HW + 0.05:
        w = R.uniform(0.215, 0.305)
        cuts = sorted(R.uniform(YF + 0.9, YB - 0.9) for _ in range(R.choice([1, 1, 2])))
        edges = [YF - 0.08] + cuts + [YB + 0.08]
        for a, b in zip(edges[:-1], edges[1:]):
            mat = mats[(i + R.choice([0, 0, 1, 2, 3, 4])) % 5]
            m.box((x + w / 2, (a + b) / 2, -0.031),
                  (w / 2 - 0.008, (b - a) / 2 - 0.006, 0.031), mat,
                  rot=(R.uniform(-0.004, 0.004), 0, 0))
            i += 1
        x += w
    # sub-floor: no light leaks through the plank gaps
    m.box((0, 0, -0.10), (HW + 0.12, (YB - YF) / 2 + 0.12, 0.04), M("mat_n_beam"))
    ob = m.finish(c, bevel=0.006, seg=1)
    ob.name = "walk_floor"
    ob.data.name = "walk_floor"
    return ob


def build_wall_run(name, width, c):
    """A wall segment in the same local frame as the 3x3 kit panels: width
    along local X, height along Z, cladding front face at y = -0.126."""
    m = IMesh(name)
    clad = [M("mat_n_wall"), M("mat_n_wall_b")]
    frame = M("mat_n_green")
    x = -width / 2
    k = 0
    while x < width / 2 - 1e-3:
        w = min(R.uniform(0.185, 0.245), width / 2 - x)
        m.box((x + w / 2, -0.077, WH / 2), (w / 2 - 0.004, 0.049, WH / 2),
              clad[k % 2 if R.random() > 0.25 else R.randint(0, 1)],
              rot=(0, R.uniform(-0.0035, 0.0035), 0))
        x += w
        k += 1
    m.box((0, 0.02, 0.07), (width / 2, 0.05, 0.07), frame)              # sill
    m.box((0, 0.02, WH - 0.08), (width / 2, 0.05, 0.08), frame)         # head
    m.box((0, 0.02, WH * 0.52), (width / 2, 0.042, 0.055), frame)       # mid rail
    for sx in (-1, 1):
        m.box((sx * (width / 2 - 0.07), 0.02, WH / 2), (0.07, 0.05, WH / 2), frame)
    n_std = max(1, int(width / 1.05))
    for i in range(1, n_std):
        m.box((-width / 2 + width * i / n_std, 0.02, WH / 2),
              (0.055, 0.045, WH / 2), frame)
    return m.finish(c, bevel=0.008)


def build_shell(c, kit):
    obs = []

    door = kit["kit_wall_door"]
    door.location = (DOOR_X, YB, 0)
    reskin(door)
    obs.append(door)
    if door.name not in c.objects:
        c.objects.link(door)

    win = kit["kit_wall_window"]
    win.location = (HW, WIN_Y, 0)
    win.rotation_euler = (0, 0, math.radians(-90))
    reskin(win)
    obs.append(win)
    if win.name not in c.objects:
        c.objects.link(win)

    # back wall right of the door bay (door bay spans -4.90 .. -1.90)
    w = build_wall_run("wall_back", 6.90, c)
    w.location = (1.55, YB, 0)
    obs.append(w)
    # left wall: full depth
    w = build_wall_run("wall_left", 7.00, c)
    w.location = (-HW, 0.0, 0)
    w.rotation_euler = (0, 0, math.radians(90))
    obs.append(w)
    # right wall in two runs either side of the window bay (-2.20 .. 0.80)
    w = build_wall_run("wall_right_f", 1.30, c)
    w.location = (HW, -2.85, 0)
    w.rotation_euler = (0, 0, math.radians(-90))
    obs.append(w)
    w = build_wall_run("wall_right_b", 2.70, c)
    w.location = (HW, 2.15, 0)
    w.rotation_euler = (0, 0, math.radians(-90))
    obs.append(w)

    # ---- moss-green wainscot: the palette move that ties the room together --
    t = IMesh("wainscot")
    g, gb, gc = M("mat_n_green"), M("mat_n_green_b"), M("mat_n_green_c")
    ox = M("mat_n_oxblood")

    def panelled(x0, x1, y, axis, depth, mat_a, mat_b):
        """A run of framed panels: recessed field, proud stiles, capping rail."""
        span = x1 - x0
        if span <= 0.05:
            return
        n = max(1, int(round(span / 0.62)))
        for i in range(n + 1):
            p = x0 + span * i / n
            if axis == "x":
                t.box((p, y, WAINS * 0.5), (0.045, depth * 1.5, WAINS * 0.5), mat_b)
            else:
                t.box((y, p, WAINS * 0.5), (depth * 1.5, 0.045, WAINS * 0.5), mat_b)
        if axis == "x":
            t.box(((x0 + x1) / 2, y, WAINS * 0.5), (span / 2, depth, WAINS * 0.5), mat_a)
            t.box(((x0 + x1) / 2, y, 0.075), (span / 2, depth * 1.6, 0.075), mat_b)
            t.box(((x0 + x1) / 2, y, WAINS + 0.045),
                  (span / 2, depth * 2.1, 0.045), gc)              # capping rail
        else:
            t.box((y, (x0 + x1) / 2, WAINS * 0.5), (depth, span / 2, WAINS * 0.5), mat_a)
            t.box((y, (x0 + x1) / 2, 0.075), (depth * 1.6, span / 2, 0.075), mat_b)
            t.box((y, (x0 + x1) / 2, WAINS + 0.045),
                  (depth * 2.1, span / 2, 0.045), gc)

    # back wall, broken at the door opening
    for (x0, x1) in ((-IX, DOOR_X - 0.62), (DOOR_X + 0.62, IX)):
        panelled(x0, x1, IY - 0.035, "x", 0.035, g, gb)
    # left wall, broken at the hearth breast
    for (y0, y1) in ((YF, HRTH_Y0 - 0.10), (HRTH_Y1 + 0.10, YB)):
        panelled(y0, y1, -IX + 0.035, "y", 0.035, gb, g)
    # right wall, broken at the stair
    panelled(YF, STR_Y0 - 0.05, IX - 0.035, "y", 0.035, g, gb)

    # oxblood accent band just above the capping rail -- the map's trim colour
    for (x0, x1) in ((-IX, DOOR_X - 0.62), (DOOR_X + 0.62, IX)):
        t.box(((x0 + x1) / 2, IY - 0.022, WAINS + 0.125),
              ((x1 - x0) / 2, 0.022, 0.038), ox)
    for (y0, y1) in ((YF, HRTH_Y0 - 0.10), (HRTH_Y1 + 0.10, YB)):
        t.box((-IX + 0.022, (y0 + y1) / 2, WAINS + 0.125),
              (0.022, (y1 - y0) / 2, 0.038), ox)
    t.box((IX - 0.022, (YF + STR_Y0) / 2, WAINS + 0.125),
          (0.022, (STR_Y0 - YF) / 2, 0.038), ox)

    # corner posts + top plate the beams land on
    for (px, py, mm) in ((-IX + 0.09, IY - 0.09, g), (IX - 0.09, IY - 0.09, g),
                         (-IX + 0.09, YF + 0.10, gb), (IX - 0.09, YF + 0.10, gb)):
        t.box((px, py, WH / 2), (0.09, 0.09, WH / 2), mm)
    t.box((0, IY - 0.075, WH - 0.10), (HW, 0.075, 0.10), g)
    for sx in (-1, 1):
        t.box((sx * (IX - 0.075), 0, WH - 0.10), (0.075, (YB - YF) / 2, 0.10), g)

    # peg rails (the pegs themselves get their coats in build_travellers).
    # The left rail sits BEHIND the hearth, not in front of it: the front-left
    # corner falls outside the camera crop, and coats are too good a storytelling
    # prop to hang where the frame cuts them off.
    t.box((-IX + 0.055, 1.72, RAIL_Z), (0.055, 0.60, 0.055), gc)
    t.box((-2.38, IY - 0.055, RAIL_Z), (0.50, 0.055, 0.055), gc)
    obs.append(t.finish(c, bevel=0.008))

    # ---- ceiling beams ---------------------------------------------------
    # From a high 3/4 the camera sees the TOP of every beam and nothing lights
    # it, so a full-width beam is a black bar straight across the frame. They
    # are tucked high, kept slim, and SKY_top sits above them to graze the
    # tops. The front beam is split and carried on a post so the foreground
    # and the long table stay unbarred.
    b = IMesh("beams")
    bm_, bb, g = M("mat_n_beam"), M("mat_n_beam_b"), M("mat_n_green")
    for (y, x0, x1) in BEAMS:
        b.box(((x0 + x1) / 2, y, BEAM_Z), ((x1 - x0) / 2, BEAM_H, BEAM_H),
              bm_ if abs(y) > 1.0 else bb, rot=(0, R.uniform(-0.004, 0.004), 0))
        for sx, bx in ((-1, x0), (1, x1)):
            if abs(bx) > HW - 0.2:
                b.box((bx - sx * 0.16, y, BEAM_Z - 0.185), (0.16, 0.075, 0.09), bm_)
    # purlins tying the cross beams. These run in Y, so they project as
    # DIAGONALS rather than as horizontal bars -- which is why they are allowed
    # to cross the frame where the beams are not.
    for x in (-3.25, -0.55, 2.15):
        b.box((x, 1.30, BEAM_Z + 0.115), (0.062, 1.35, 0.042), bb)
    px, py = BEAM_POST
    b.box((px, py, (BEAM_Z - BEAM_H) / 2), (0.085, 0.085, (BEAM_Z - BEAM_H) / 2), bm_)
    b.box((px, py, 0.11), (0.115, 0.115, 0.11), g)                 # painted plinth
    for s in (-1, 1):
        b.strand([(px + s * 0.34, py, BEAM_Z - BEAM_H - 0.02),
                  (px, py, BEAM_Z - BEAM_H - 0.36)], 0.055, bm_, seg=6)
    b.cyl((px - 0.10, py, 1.66), 0.020, 0.16, M("mat_n_iron"), seg=8,
          rot=(0, math.pi / 2, 0))
    obs.append(b.finish(c, bevel=0.01))
    return obs


# ------------------------------------------------------------------- hearth

def build_hearth(c):
    """The value leader. A river-stone breast with a live fire, a heavy timber
    mantel, and everything a soaked traveller would prop in front of it."""
    m = IMesh("hearth")
    st, stb, soot = M("mat_n_stone"), M("mat_n_stone_b"), M("mat_n_soot")
    bm_, ir = M("mat_n_beam"), M("mat_n_iron")

    xb, xf = -IX, HRTH_XF
    # jambs either side of the opening, floor to mantel
    for (y0, y1) in ((HRTH_Y0, OPEN_Y0), (OPEN_Y1, HRTH_Y1)):
        m.box(((xb + xf) / 2, (y0 + y1) / 2, MANTEL_Z / 2),
              ((xf - xb) / 2, (y1 - y0) / 2, MANTEL_Z / 2),
              st if y0 < 0 else stb)
    # lintel over the opening
    m.box(((xb + xf) / 2, (OPEN_Y0 + OPEN_Y1) / 2, (OPEN_Z + MANTEL_Z) / 2),
          ((xf - xb) / 2, (OPEN_Y1 - OPEN_Y0) / 2, (MANTEL_Z - OPEN_Z) / 2), stb)
    # Firebox. A fireplace on the LEFT wall is seen almost edge-on by a camera
    # sitting at x=0, so a deep box with parallel cheeks shows the viewer one
    # sliver of soot and hides the fire behind its own jamb. Real fireplaces
    # splay their cheeks for draught; here the splay is doing camera work, and
    # the box is kept shallow so the burning logs stay visible from the side.
    m.box((-4.42, (OPEN_Y0 + OPEN_Y1) / 2, OPEN_Z / 2),
          (0.075, (OPEN_Y1 - OPEN_Y0) / 2 - 0.14, OPEN_Z / 2), soot)
    for (y, sp) in ((OPEN_Y0, 0.30), (OPEN_Y1, -0.30)):
        m.box((-4.18, y - math.copysign(0.075, sp), OPEN_Z / 2),
              (0.26, 0.03, OPEN_Z / 2), soot, rot=(0, 0, sp))
    m.box((-4.18, (OPEN_Y0 + OPEN_Y1) / 2, OPEN_Z - 0.02),
          (0.26, (OPEN_Y1 - OPEN_Y0) / 2, 0.03), soot)

    # the hood above the mantel, tapering back into the wall
    rows = []
    for i in range(5):
        t = i / 4
        xfr = xf + (-4.62 - xf) * t
        yy = (HRTH_Y1 - 0.10) + (0.62 - (HRTH_Y1 - 0.10)) * t
        y0 = (HRTH_Y0 + 0.10) + (-1.02 - (HRTH_Y0 + 0.10)) * t
        z = MANTEL_Z + 0.10 + (2.35 - MANTEL_Z - 0.10) * t
        rows.append([(xb, y0, z), (xfr, y0, z), (xfr, yy, z), (xb, yy, z)])
    for a, b_ in zip(rows[:-1], rows[1:]):
        m.quad_strip([[a[0], a[1], a[2], a[3]], [b_[0], b_[1], b_[2], b_[3]]], stb)
    # chimney stack from the hood to the ceiling
    m.box(((xb + -4.62) / 2, (-1.02 + 0.62) / 2, (2.35 + WH) / 2),
          ((-4.62 - xb) / 2, (0.62 + 1.02) / 2, (WH - 2.35) / 2), st)

    # mantel: a heavy adzed timber, the shelf every inn puts its clutter on
    m.box((-4.44, (HRTH_Y0 + HRTH_Y1) / 2 - 0.02, MANTEL_Z - 0.055),
          (0.50, (HRTH_Y1 - HRTH_Y0) / 2 + 0.09, 0.075), bm_,
          rot=(0, R.uniform(-0.004, 0.004), 0))
    for y in (HRTH_Y0 + 0.16, HRTH_Y1 - 0.16):          # corbels under it
        m.box((-4.62, y, MANTEL_Z - 0.18), (0.24, 0.055, 0.055), bm_)

    # hearth apron on the floor -- flagstones, worn pale where boots stand
    for i in range(4):
        y0 = HRTH_Y0 + 0.10 + i * 0.66
        m.box((-3.83, y0 + 0.31, 0.026), (0.30, 0.31, 0.026),
              st if i % 2 else stb, rot=(0, 0, R.uniform(-0.01, 0.01)))

    # andirons + logs + ember bed
    for y in (OPEN_Y0 + 0.26, OPEN_Y1 - 0.26):
        m.strand([(-4.38, y, 0.08), (-3.96, y, 0.08)], 0.022, ir, seg=6)
        m.strand([(-3.96, y, 0.05), (-3.96, y, 0.30)], 0.024, ir, seg=6)
        m.ring((-3.96, y, 0.33), 0.045, 0.016, ir, axis="X", seg=8)
    logs = [((-4.20, -0.62, 0.13), 0.085, 0.95, 0.10),
            ((-4.14, -0.22, 0.12), 0.075, 0.86, -0.14),
            ((-4.22, 0.04, 0.27), 0.070, 0.78, 0.22),
            ((-4.10, -0.42, 0.30), 0.062, 0.70, -0.08)]
    for (p, r, ln, tilt) in logs:
        m.cyl(p, r, ln, soot, seg=9, rot=(math.pi / 2, tilt, 0), r2=r * 0.88)
    for i in range(22):
        m.sphere((-4.20 + R.uniform(-0.18, 0.24), R.uniform(-1.05, 0.25),
                  0.032 + R.uniform(0, 0.05)), R.uniform(0.018, 0.040),
                 M("mat_n_ember"), seg=6, rings=4)
    # v12: the art gate asked the hearth for more PRESENCE. The bed is widened
    # across the full opening and given bigger coals, on a PRIVATE rng so the
    # shared stream -- and therefore every prop built after this one -- keeps
    # its v11 placement exactly. Growing the bed's AREA (not the emission) is
    # what buys glow without pushing the fire into the AgX shoulder.
    RE = random.Random(9114)
    for i in range(20):
        m.sphere((-4.22 + RE.uniform(-0.16, 0.30), RE.uniform(-1.34, 0.46),
                  0.030 + RE.uniform(0, 0.055)), RE.uniform(0.030, 0.058),
                 M("mat_n_ember"), seg=6, rings=4)
    ob = m.finish(c, bevel=0.008)

    # flames as a separate object so the fire material's object-Z ramp (root
    # dark orange -> tip pale yellow) is measured from the floor, not from the
    # hearth object's origin
    f = IMesh("hearth_fire")
    fm = M("mat_n_fire")
    # Cones read as traffic cones. A lumpy lathe with a teardrop profile reads
    # as fire, and the lumpiness is what stops nine of them looking like nine
    # copies of one object.
    # Tall modelled flames read as cardboard arrowheads at background scale --
    # v6/v7 proved it twice. What reads as fire is a LOW, dense, ragged mass
    # sitting in the logs with a hot ember bed under it; the storytelling is
    # done by the glow it throws on the stone, not by the silhouette.
    for i in range(11):
        bx = -4.16 + R.uniform(-0.18, 0.24)
        by = R.uniform(-1.10, 0.28)
        sc_ = R.uniform(0.60, 1.05)
        f.lathe((bx, by, 0.09),
                [(0.0, 0.0), (0.062 * sc_, 0.02), (0.078 * sc_, 0.07),
                 (0.060 * sc_, 0.14), (0.034 * sc_, 0.21), (0.014 * sc_, 0.27),
                 (0.0, 0.31 * sc_)], fm, seg=11, lumpy=0.55, seed=i * 3.7,
                rot=R.uniform(0, 3.0))
    for i in range(11):                                  # low licking flames
        f.lathe((-4.16 + R.uniform(-0.24, 0.30), R.uniform(-1.12, 0.30), 0.04),
                [(0.0, 0.0), (0.058, 0.015), (0.070, 0.05), (0.040, 0.10),
                 (0.0, 0.14)], fm, seg=9, lumpy=0.50, seed=40 + i * 2.1)
    # v12: a slightly larger fire MASS. Kit finding 21 -- stacked emissive cones
    # ADD, so piling more flames into the middle of the bed clips the stack to
    # white through AgX and the fire goes back to flat paper. The extra mass is
    # therefore spent at the two ENDS of the opening (y beyond the v11 spread),
    # where it widens the silhouette without deepening the stack on any one view
    # ray. Private rng again, so the shared stream is untouched.
    RF = random.Random(4471)
    for i in range(7):
        end = -1.40 + RF.uniform(0.0, 0.34) if i % 2 else 0.24 + RF.uniform(0.0, 0.34)
        sc_ = RF.uniform(0.70, 1.12)
        f.lathe((-4.18 + RF.uniform(-0.14, 0.26), end, 0.08),
                [(0.0, 0.0), (0.062 * sc_, 0.02), (0.080 * sc_, 0.07),
                 (0.058 * sc_, 0.15), (0.032 * sc_, 0.22), (0.012 * sc_, 0.28),
                 (0.0, 0.33 * sc_)], fm, seg=11, lumpy=0.55, seed=80 + i * 3.1,
                rot=RF.uniform(0, 3.0))
    for i in range(6):
        end = -1.42 + RF.uniform(0.0, 0.40) if i % 2 else 0.22 + RF.uniform(0.0, 0.40)
        f.lathe((-4.16 + RF.uniform(-0.22, 0.30), end, 0.04),
                [(0.0, 0.0), (0.058, 0.015), (0.072, 0.05), (0.042, 0.10),
                 (0.0, 0.15)], fm, seg=9, lumpy=0.50, seed=120 + i * 2.3)
    fob = f.finish(c, bevel=0, shade_smooth=True)
    fob.visible_shadow = False
    return ob, fob


def build_hearth_dressing(c, kit):
    """Boots drying, firewood, a drying rack, the mantel clutter. This is the
    zone that has to say 'a dozen wet strangers have been here all day'."""
    m = IMesh("hearth_dress")
    lt, ltb = M("mat_n_leather"), M("mat_n_leather_b")
    bm_, ir, g = M("mat_n_beam"), M("mat_n_iron"), M("mat_n_green")
    ox, cer, brs = M("mat_n_oxblood"), M("mat_n_ceramic"), M("mat_n_brass")

    def boot(x, y, rz, tilt=0.0, mat=lt, h=0.32):
        e = (0, tilt, rz)
        m.box((x, y, h * 0.5), (0.055, 0.070, h * 0.5), mat, rot=e)     # leg
        m.box((x + 0.055 * math.cos(rz), y + 0.055 * math.sin(rz), 0.048),
              (0.105, 0.072, 0.048), mat, rot=(0, 0, rz))               # foot
        m.box((x + 0.055 * math.cos(rz), y + 0.055 * math.sin(rz), 0.012),
              (0.112, 0.076, 0.014), ltb, rot=(0, 0, rz))               # sole

    # pairs steaming on the apron, plus one tipped over
    boot(-3.86, -1.42, 0.30); boot(-3.80, -1.20, 0.42)
    boot(-3.90, -0.62, -0.25, mat=ltb); boot(-3.86, -0.40, -0.12, mat=ltb)
    m.box((-3.78, 0.30, 0.062), (0.11, 0.062, 0.062), lt, rot=(1.35, 0, 0.6))
    m.box((-3.72, 0.52, 0.055), (0.10, 0.058, 0.055), lt, rot=(0, 1.45, 0.2))

    # firewood stacked against the wall behind the breast
    for i in range(11):
        row, col = i // 4, i % 4
        m.cyl((-4.66 + R.uniform(-0.02, 0.02), 1.32 + col * 0.135,
               0.075 + row * 0.145), R.uniform(0.058, 0.072), 0.60,
              M("mat_n_beam_b"), seg=8,
              rot=(0, math.pi / 2, R.uniform(-0.05, 0.05)))
    for i in range(4):                                   # a few fallen
        m.cyl((-4.20 + R.uniform(-0.1, 0.1), 1.30 + i * 0.16, 0.062), 0.060,
              0.52, bm_, seg=8, rot=(0, math.pi / 2, R.uniform(-0.25, 0.25)))

    # fire irons in a stand
    m.cyl((-3.62, 0.78, 0.035), 0.085, 0.07, ir, seg=10)
    for i, (lean, ln) in enumerate(((0.06, 1.02), (0.13, 0.95), (-0.05, 0.88))):
        a = -0.5 + i * 0.5
        m.strand([(-3.62, 0.78, 0.05),
                  (-3.62 + math.sin(lean) * ln * math.cos(a),
                   0.78 + math.sin(lean) * ln * math.sin(a), 0.05 + ln)],
                 0.014, ir, seg=6)
    m.ring((-3.62 + 0.02, 0.78 - 0.05, 1.05), 0.048, 0.013, ir, axis="Y", seg=8)

    # a drying rack with a shirt and a blanket over it -- pure "stranded"
    ry = -2.48                       # clear of the fire opening in frame
    for sx in (-0.30, 0.30):
        m.strand([(-3.30 + sx * 0.10, ry + sx, 0.0),
                  (-3.46, ry + sx * 0.25, 1.00)], 0.024, bm_, seg=6)
        m.strand([(-3.62 + sx * 0.10, ry + sx, 0.0),
                  (-3.46, ry + sx * 0.25, 1.00)], 0.024, bm_, seg=6)
    m.strand([(-3.46, ry - 0.30, 0.99), (-3.46, ry + 0.30, 0.99)], 0.020, bm_, seg=6)
    m.cloth((-3.46, ry, 0.98), (0, 1, 0), (1, 0, 0), 0.58, 0.62,
            M("mat_n_linen"), folds=3, bulge=0.06, seed=1.1, taper=0.85)
    m.cloth((-3.42, ry, 0.82), (0, 1, 0), (-1, 0, 0), 0.50, 0.46,
            M("mat_n_wool"), folds=3, bulge=0.05, seed=2.3, taper=0.9)

    # mantel clutter: a jug, two candlesticks, a pipe, a tally board
    m.lathe((-4.44, -1.42, MANTEL_Z + 0.02),
            [(0.0, 0), (0.062, 0.012), (0.072, 0.09), (0.050, 0.16),
             (0.058, 0.19), (0.0, 0.20)], cer, seg=12, lumpy=0.05)
    for (y, h) in ((-1.02, 0.13), (0.60, 0.16)):
        m.lathe((-4.44, y, MANTEL_Z + 0.02),
                [(0.0, 0), (0.048, 0.008), (0.020, 0.03), (0.018, h),
                 (0.030, h + 0.012), (0.0, h + 0.014)], brs, seg=10)
        m.cyl((-4.44, y, MANTEL_Z + 0.02 + h + 0.05), 0.014, 0.075,
              M("mat_n_wax"), seg=8)
    m.box((-4.40, 0.14, MANTEL_Z + 0.075), (0.020, 0.15, 0.075), M("mat_n_slate"),
          rot=(0, 0.06, 0))
    m.box((-4.46, -0.62, MANTEL_Z + 0.03), (0.075, 0.10, 0.028), M("mat_n_paper"),
          rot=(0, 0, 0.3))
    obs = [m.finish(c, bevel=0.006)]

    # the settle: a high-backed bench pulled up to the fire
    s = IMesh("hearth_settle")
    for y in (-1.32, 0.28):
        s.box((-3.30, y, 0.215), (0.16, 0.055, 0.215), M("mat_n_oxblood_b"))
        s.box((-2.92, y, 0.215), (0.055, 0.055, 0.215), M("mat_n_oxblood_b"))
    s.box((-3.16, -0.52, 0.455), (0.34, 0.86, 0.035), M("mat_n_table_b"))
    # v2: an oxblood back board caught the fire AND the dusk shaft and became
    # the brightest, pinkest object on the left. Green sits back and lets the
    # fire behind it lead.
    s.box((-2.86, -0.52, 0.80), (0.045, 0.86, 0.35), M("mat_n_green_b"))
    for y in (-1.34, 0.30):
        s.box((-2.88, y, 0.80), (0.055, 0.055, 0.35), M("mat_n_green_b"))
    s.cloth((-2.90, -0.52, 0.68), (0, 1, 0), (-1, 0, 0), 0.62, 0.34,
            M("mat_n_wool_b"), folds=3, bulge=0.05, seed=4.2, taper=0.92)
    obs.append(s.finish(c, bevel=0.008))

    # a bucket and a stack of split kindling by the settle
    obs.append(place(kit["kit_bucket"], (-3.40, 1.32, 0.0), rot=(0, 0, 0.5), c=c))
    return obs


# ----------------------------------------------------------------- counter

def build_counter(c):
    """The innkeep's reception desk: painted panelled front, worn timber top,
    a bell, an open ledger, and the key rack on the wall behind."""
    m = IMesh("counter")
    top, ox, oxb = M("mat_n_counter"), M("mat_n_oxblood"), M("mat_n_oxblood_b")
    g, gb, bm_ = M("mat_n_green"), M("mat_n_green_b"), M("mat_n_beam")
    x0, x1, y0, y1 = CTR_X0, CTR_X1, CTR_Y0, CTR_Y1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    # carcass
    m.box((cx, cy, (CTR_H - 0.10) / 2), ((x1 - x0) / 2 - 0.02,
          (y1 - y0) / 2 - 0.03, (CTR_H - 0.10) / 2), oxb)
    # panelled front face
    n = 4
    for i in range(n):
        px = x0 + (x1 - x0) * (i + 0.5) / n
        m.box((px, y0 - 0.022, (CTR_H - 0.08) / 2),
              ((x1 - x0) / n / 2 - 0.055, 0.022, (CTR_H - 0.30) / 2), ox)
    for i in range(n + 1):
        px = x0 + (x1 - x0) * i / n
        m.box((px, y0 - 0.028, (CTR_H - 0.08) / 2), (0.045, 0.028, (CTR_H - 0.08) / 2), g)
    m.box((cx, y0 - 0.030, 0.085), ((x1 - x0) / 2, 0.030, 0.085), gb)      # plinth
    m.box((cx, y0 - 0.030, CTR_H - 0.145), ((x1 - x0) / 2, 0.030, 0.048), g)
    # top with a nosing that overhangs the front -- catches the lantern
    m.box((cx, cy - 0.035, CTR_H - 0.030), ((x1 - x0) / 2 + 0.055,
          (y1 - y0) / 2 + 0.055, 0.030), top, rot=(0, R.uniform(-0.003, 0.003), 0))
    m.box((cx, y0 - 0.085, CTR_H - 0.075), ((x1 - x0) / 2 + 0.055, 0.030, 0.030), top)
    # a flap at the left end, propped open: the way the innkeep gets out
    m.box((x0 - 0.135, y1 - 0.30, CTR_H - 0.030), (0.135, 0.30, 0.026), top,
          rot=(0, 0, 0.04))
    # working shelf behind, and a stool
    m.box((cx + 0.10, y1 + 0.22, 0.52), ((x1 - x0) / 2 - 0.25, 0.14, 0.022), M("mat_n_shelf"))
    for (sx, sy) in ((x0 + 0.42, y1 + 0.22), (x1 - 0.42, y1 + 0.22)):
        m.box((sx, sy, 0.26), (0.030, 0.030, 0.26), bm_)
    m.cyl((x1 - 0.30, y1 + 0.42, 0.40), 0.135, 0.035, M("mat_n_table_b"), seg=12)
    for a in range(3):
        ang = a * 2.094 + 0.4
        m.strand([(x1 - 0.30 + 0.10 * math.cos(ang), y1 + 0.42 + 0.10 * math.sin(ang), 0.0),
                  (x1 - 0.30 + 0.055 * math.cos(ang), y1 + 0.42 + 0.055 * math.sin(ang), 0.39)],
                 0.020, bm_, seg=6)
    return m.finish(c, bevel=0.008)


def build_keyrack(c):
    """Numbered pegs on the wall behind the counter. The gaps matter: keys
    still hanging are empty rooms, missing keys are the rooms already taken by
    people who got stuck here yesterday."""
    m = IMesh("keyrack")
    sh, g, ir = M("mat_n_shelf"), M("mat_n_green"), M("mat_n_iron")
    brs = M("mat_n_brass")
    # v2 put the rack at x 0.95..3.02 and the hanging-mug shelf at 1.26..2.70 --
    # the shelf sat 0.13 in FRONT of the rack and hid its bottom row entirely.
    # They now own separate stretches of wall.
    x0, x1, z0, z1 = 1.52, 3.06, 1.44, 2.26
    y = IY - 0.030
    # A dark field behind pale hardware: v3 had a brown board, green frame and
    # green pegs all at one value and the rack read as a blank cabinet.
    m.box(((x0 + x1) / 2, y, (z0 + z1) / 2), ((x1 - x0) / 2, 0.030,
          (z1 - z0) / 2), M("mat_n_oxblood_b"))                   # backboard
    for (a, b_, hz) in ((x0, x1, z0), (x0, x1, z1)):              # frame rails
        m.box(((a + b_) / 2, y - 0.020, hz), ((b_ - a) / 2 + 0.035, 0.022, 0.038), g)
    for xx in (x0, x1):
        m.box((xx, y - 0.020, (z0 + z1) / 2), (0.035, 0.022, (z1 - z0) / 2 + 0.038), g)

    ncol, nrow = 6, 2
    taken = {1, 4, 5, 7, 8, 10}                          # rooms already let
    for r in range(nrow):
        zz = z0 + 0.26 + r * 0.44
        m.box(((x0 + x1) / 2, y - 0.018, zz - 0.075),
              ((x1 - x0) / 2 - 0.04, 0.020, 0.016), g)            # peg rail
        for i in range(ncol):
            px = x0 + 0.16 + (x1 - x0 - 0.32) * i / (ncol - 1)
            m.cyl((px, y - 0.055, zz), 0.011, 0.075, brs, seg=6, rot=(math.pi / 2, 0, 0))
            m.sphere((px, y - 0.090, zz), 0.017, brs, seg=7, rings=5)
            m.box((px, y - 0.014, zz - 0.055), (0.022, 0.014, 0.015),
                  M("mat_n_chalk"))                               # number plate
            k = r * ncol + i
            if k in taken:
                continue
            m.ring((px, y - 0.070, zz - 0.045), 0.032, 0.008, brs, axis="Y", seg=8)
            m.strand([(px, y - 0.070, zz - 0.074), (px, y - 0.070, zz - 0.160)],
                     0.009, brs, seg=5)
            m.box((px + 0.016, y - 0.070, zz - 0.155), (0.016, 0.007, 0.015), brs)
    return m.finish(c, bevel=0.005)


def build_counter_props(c):
    """Bell, ledger, inkpot, candle, tally, a mug the innkeep never finished."""
    m = IMesh("counter_props")
    brs, cer, pap = M("mat_n_brass"), M("mat_n_ceramic"), M("mat_n_paper")
    ir, wax, pew = M("mat_n_iron"), M("mat_n_wax"), M("mat_n_pewter")
    z = CTR_H
    cy = (CTR_Y0 + CTR_Y1) / 2

    # the bell: a brass dome on a turned base with a plunger
    bx, by = CTR_X0 + 0.34, CTR_Y0 + 0.20
    m.lathe((bx, by, z), [(0.0, 0), (0.075, 0.008), (0.070, 0.022), (0.0, 0.024)],
            M("mat_n_table_b"), seg=14)
    m.lathe((bx, by, z + 0.024),
            [(0.0, 0.0), (0.062, 0.005), (0.064, 0.030), (0.052, 0.058),
             (0.028, 0.078), (0.012, 0.086), (0.0, 0.088)], brs, seg=14)
    m.cyl((bx, by, z + 0.104), 0.008, 0.030, brs, seg=8)
    m.sphere((bx, by, z + 0.124), 0.016, brs, seg=8, rings=6)

    # the open ledger: two leaves with a spine and a ribbon
    lx, ly = CTR_X0 + 0.98, cy - 0.055
    for s in (-1, 1):
        m.box((lx + s * 0.115, ly, z + 0.020), (0.115, 0.145, 0.014), pap,
              rot=(0, -s * 0.045, 0.02))
    m.box((lx, ly, z + 0.016), (0.022, 0.150, 0.020), M("mat_n_leather"))
    for s in (-1, 1):                                   # ruled lines
        for i in range(6):
            m.box((lx + s * 0.115, ly - 0.10 + i * 0.042, z + 0.034),
                  (0.088, 0.0035, 0.0015), M("mat_n_iron"), rot=(0, -s * 0.045, 0.02))
    m.strand([(lx, ly - 0.14, z + 0.030), (lx + 0.06, ly - 0.24, z + 0.004)],
             0.006, M("mat_n_oxblood"), seg=5)
    # inkpot + quill
    m.lathe((lx + 0.30, ly + 0.12, z), [(0.0, 0), (0.034, 0.006), (0.036, 0.048),
            (0.020, 0.056), (0.0, 0.058)], M("mat_n_glass_brown"), seg=10)
    m.strand([(lx + 0.30, ly + 0.12, z + 0.05), (lx + 0.40, ly + 0.22, z + 0.24)],
             0.006, M("mat_n_linen"), seg=5, r2=0.002)
    # a stub candle in a dish -- the innkeep's own light
    cxx, cyy = CTR_X1 - 0.30, CTR_Y0 + 0.22
    m.lathe((cxx, cyy, z), [(0.0, 0), (0.070, 0.006), (0.062, 0.016), (0.024, 0.020),
            (0.0, 0.022)], pew, seg=12)
    m.cyl((cxx, cyy, z + 0.075), 0.020, 0.115, wax, seg=10, r2=0.018)
    m.cyl((cxx, cyy, z + 0.136), 0.0035, 0.014, ir, seg=6)
    m.cyl((cxx, cyy, z + 0.158), 0.016, 0.042, M("mat_n_candleflame"), seg=8, r2=0.002)
    # a pewter mug, a coin stack, a folded chit
    m.lathe((CTR_X0 + 1.62, CTR_Y0 + 0.17, z),
            [(0.0, 0), (0.048, 0.006), (0.052, 0.10), (0.048, 0.105), (0.0, 0.107)],
            pew, seg=12)
    m.ring((CTR_X0 + 1.62 + 0.056, CTR_Y0 + 0.17, z + 0.055), 0.034, 0.008, pew,
           axis="X", seg=8)
    for i in range(5):
        m.cyl((CTR_X0 + 1.30, CTR_Y0 + 0.40, z + 0.006 + i * 0.007), 0.021, 0.007,
              brs, seg=10, rot=(0, 0, R.uniform(0, 1)))
    m.box((CTR_X1 - 0.72, cy + 0.10, z + 0.004), (0.070, 0.050, 0.004), pap,
          rot=(0, 0, 0.5))
    # a ring of spare keys dumped on the top
    m.ring((CTR_X0 + 0.62, cy + 0.16, z + 0.008), 0.038, 0.007, ir, axis="Z", seg=10)
    for a in (0.4, 1.9, 3.3):
        m.box((CTR_X0 + 0.62 + 0.055 * math.cos(a), cy + 0.16 + 0.055 * math.sin(a),
               z + 0.008), (0.030, 0.008, 0.004), ir, rot=(0, 0, a))
    ob = m.finish(c, bevel=0.004)

    lit = bpy.data.lights.new("CTR_candle", "POINT")
    lit.energy, lit.color, lit.shadow_soft_size = 5.0, (1.0, 0.66, 0.30), 0.03
    lo = bpy.data.objects.new("CTR_candle", lit)
    c.objects.link(lo)
    lo.location = (cxx, cyy, z + 0.165)
    return ob


def build_innsign(c):
    """A painted board over the key rack. FF9 backgrounds always tell you where
    you are in the picture itself."""
    m = IMesh("innsign")
    m.box((1.98, IY - 0.045, 2.52), (1.14, 0.045, 0.185), M("mat_n_green_b"))
    m.box((1.98, IY - 0.070, 2.52), (1.10, 0.022, 0.150), M("mat_n_oxblood"))
    for sx in (-1, 1):
        m.box((1.98 + sx * 1.14, IY - 0.070, 2.52), (0.035, 0.035, 0.195),
              M("mat_n_green"))
    ob = m.finish(c, bevel=0.005)
    textob("sign_text", "THE BOATMEN'S REST", 0.086, M("mat_n_chalk"),
           (1.98, IY - 0.094, 2.525), (math.radians(90), 0, 0), c, extrude=0.005)
    return ob


# ------------------------------------------------------------- notice board

def build_notice(c):
    """The lock schedule. This is the plot of the room: the locks are down and
    nobody is going anywhere, and it is written on the wall in chalk."""
    m = IMesh("notice")
    sh, g, ox = M("mat_n_shelf_b"), M("mat_n_green"), M("mat_n_oxblood")
    pap, ir = M("mat_n_notice"), M("mat_n_iron")
    x0, x1, z0, z1 = -1.62, 0.02, 1.16, 2.28
    y = IY - 0.028
    m.box(((x0 + x1) / 2, y, (z0 + z1) / 2), ((x1 - x0) / 2, 0.028,
          (z1 - z0) / 2), sh)
    for (a, b_, hz) in ((x0, x1, z0), (x0, x1, z1)):
        m.box(((a + b_) / 2, y - 0.020, hz), ((b_ - a) / 2 + 0.032, 0.022, 0.034), g)
    for xx in (x0, x1):
        m.box((xx, y - 0.020, (z0 + z1) / 2), (0.032, 0.022, (z1 - z0) / 2 + 0.034), ox)

    # pinned papers, curling, overlapping, at angles
    for i in range(11):
        px = R.uniform(x0 + 0.14, x1 - 0.14)
        pz = R.uniform(z0 + 0.14, z1 - 0.26)
        w, h = R.uniform(0.075, 0.145), R.uniform(0.085, 0.165)
        rz = R.uniform(-0.20, 0.20)
        m.box((px, y - 0.033 - i * 0.0012, pz), (w, 0.004, h), pap, rot=(0, rz, 0))
        for k in range(int(h / 0.028)):                 # writing
            m.box((px, y - 0.040 - i * 0.0012, pz + h - 0.028 - k * 0.028),
                  (w * R.uniform(0.45, 0.85), 0.0015, 0.0035),
                  M("mat_n_iron"), rot=(0, rz, 0))
        m.cyl((px + w * 0.7, y - 0.046, pz + h * 0.8), 0.006, 0.020, ir, seg=6,
              rot=(math.pi / 2, 0, 0))
    ob = m.finish(c, bevel=0.004)

    # the slate: LOCKS DELAYED, hung on the board by a cord
    s = IMesh("slate")
    s.box((-0.80, y - 0.052, 1.56), (0.40, 0.020, 0.28), M("mat_n_slate"))
    for sx in (-1, 1):
        s.box((-0.80 + sx * 0.40, y - 0.056, 1.56), (0.030, 0.026, 0.30),
              M("mat_n_beam"))
    for sz in (-1, 1):
        s.box((-0.80, y - 0.056, 1.56 + sz * 0.28), (0.43, 0.026, 0.030),
              M("mat_n_beam"))
    s.strand(sagline((-1.14, y - 0.048, 1.86), (-0.46, y - 0.048, 1.86), 0.05),
             0.005, M("mat_n_canvas"), seg=4)
    obs = [ob, s.finish(c, bevel=0.004)]
    textob("slate_text", "LOCKS:\nDELAYED", 0.108, M("mat_n_chalk"),
           (-0.80, y - 0.078, 1.565), (math.radians(90), 0, 0), c, extrude=0.004)
    return obs


# ------------------------------------------------------------------- stair

def build_stair(c):
    """Rises along the right wall in +Y and passes through a framed head in the
    back wall. Only the bottom flight is in frame; the rest is implied by the
    dark stairwell above the top tread -- which is not a flat black hole,
    because two more treads and the landing rail catch the lantern."""
    m = IMesh("stair")
    # Seen from a camera at x=0 this flight is heavily foreshortened and v2 lost
    # it entirely. The fix is not geometry, it is CONTRAST: pale painted risers
    # alternating with dark timber treads make a band pattern the eye reads as
    # "staircase" instantly, at any size, however oblique the angle.
    tr, ris = M("mat_n_table"), M("mat_n_green_c")
    g, gb, bm_ = M("mat_n_green"), M("mat_n_green_b"), M("mat_n_beam")
    x0, x1 = STR_X0, STR_X1
    cx = (x0 + x1) / 2

    tops = []
    for i in range(STR_N):
        y = STR_Y0 + i * STR_RUN
        z = (i + 1) * STR_RISE
        m.box((cx, y + STR_RUN / 2, z - 0.022), ((x1 - x0) / 2, STR_RUN / 2 + 0.022,
              0.022), tr, rot=(0, R.uniform(-0.003, 0.003), 0))     # tread
        m.box((cx, y - 0.020, z - STR_RISE / 2 - 0.02),
              ((x1 - x0) / 2, 0.020, STR_RISE / 2), ris)            # riser
        tops.append((y + STR_RUN / 2, z))
    ytop = STR_Y0 + STR_N * STR_RUN
    ztop = STR_N * STR_RISE
    m.box((cx, (ytop + IY) / 2, ztop - 0.022), ((x1 - x0) / 2,
          (IY - ytop) / 2, 0.022), tr)                              # landing
    # two more treads beyond the wall line, glimpsed through the head
    for i in range(2):
        m.box((cx, IY + 0.14 + i * STR_RUN, ztop + (i + 1) * STR_RISE - 0.022),
              ((x1 - x0) / 2, STR_RUN / 2, 0.022), tr)

    # closed stringer on the open side + the wall stringer
    rows_o, rows_i = [], []
    for (y, z) in [(STR_Y0, 0.0)] + tops + [(IY, ztop)]:
        rows_o.append([(x0 - 0.045, y, 0.0), (x0 - 0.045, y, z + 0.02)])
        rows_i.append([(x1 + 0.02, y, 0.0), (x1 + 0.02, y, z + 0.02)])
    m.quad_strip(rows_o, M("mat_n_oxblood_b"))
    m.quad_strip(rows_i, gb)
    m.box((x0 - 0.045, (STR_Y0 + IY) / 2, 0.0), (0.045, (IY - STR_Y0) / 2, 0.012), gb)
    # riser skirt so the underside is solid, not a see-through gap
    m.box((cx, (STR_Y0 + IY) / 2, 0.36), ((x1 - x0) / 2, (IY - STR_Y0) / 2, 0.36),
          M("mat_n_shelf_b"))

    # newel post + handrail + balusters
    nx, ny = x0 - 0.045, STR_Y0 - 0.02
    m.box((nx, ny, 0.50), (0.070, 0.070, 0.50), g)
    m.box((nx, ny, 1.03), (0.085, 0.085, 0.045), g)
    m.sphere((nx, ny, 1.12), 0.070, g, seg=10, rings=7)
    hr0 = (nx, ny, 1.00)
    hr1 = (nx, ytop + 0.10, ztop + 0.92)
    m.strand([hr0, hr1], 0.028, M("mat_n_beam"), seg=8)
    for i in range(STR_N):
        t = (i + 0.5) / STR_N
        by = ny + (hr1[1] - ny) * t
        bz = (hr1[2] - hr0[2]) * t + hr0[2]
        m.box((nx, by, (bz - 0.05) / 2 + STR_RISE * i * 0.0),
              (0.022, 0.022, (bz - 0.05) / 2), gb)
    m.box((nx, ytop + 0.14, ztop + 0.50), (0.062, 0.062, 0.50), g)

    # the head: a framed opening in the back wall, dark beyond
    ox0, ox1 = x0 + 0.10, x1 - 0.02
    m.box(((ox0 + ox1) / 2, IY - 0.02, ztop + 1.36), ((ox1 - ox0) / 2 + 0.06,
          0.045, 0.055), g)                                        # head lintel
    m.box((ox0 - 0.06, IY - 0.02, ztop + 0.68), (0.055, 0.045, 0.68), g)
    ob = m.finish(c, bevel=0.008)

    # The stairwell recess: a box the camera looks INTO, closed at the far end.
    # v1 built it 1.30 half-height so it rose to z=3.54 and stuck up over the
    # back wall as a brightly lit crate sitting on the roofline. It must stay
    # entirely below WH and shallow enough that the sun outside never sees it.
    r = IMesh("stairwell")
    rm = M("mat_n_beam_b")
    r.box((cx, IY + 0.46, ztop + 0.60), ((x1 - x0) / 2 + 0.08, 0.46, 0.68), rm)
    rob = r.finish(c, bevel=0)
    # flip it inside out so we see the interior faces, not the outside of a box
    rob.data.flip_normals() if hasattr(rob.data, "flip_normals") else None
    me = rob.data
    for p in me.polygons:
        p.flip()
    me.update()
    return [ob, rob]


# -------------------------------------------------------------- long table

def mug(m, x, y, z, mat, ale=None, rz=0.0, h=0.11, r=0.048, tipped=False):
    if tipped:
        m.cyl((x, y, z + r), r, h, mat, seg=10, rot=(math.pi / 2, 0, rz))
        return
    m.lathe((x, y, z), [(0.0, 0), (r, 0.006), (r * 1.06, h * 0.55), (r, h),
                        (r * 0.90, h), (r * 0.86, 0.010), (0.0, 0.008)],
            mat, seg=12)
    m.ring((x + math.cos(rz) * (r + 0.012), y + math.sin(rz) * (r + 0.012),
            z + h * 0.55), 0.030, 0.008, mat, axis="X" if abs(math.cos(rz)) > 0.5 else "Y",
           seg=8)
    if ale is not None:
        m.cyl((x, y, z + h * 0.80), r * 0.86, 0.006, ale, seg=12)


def build_long_table(c):
    """The sociable heart: one long shared table, benches both sides, and a
    card game that stopped mid-hand when somebody said the locks were shut."""
    m = IMesh("long_table")
    top, topb = M("mat_n_table"), M("mat_n_table_b")
    bm_, g, ox = M("mat_n_beam"), M("mat_n_green"), M("mat_n_oxblood_b")
    x0, x1, y0, y1 = TBL_X0, TBL_X1, TBL_Y0, TBL_Y1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    # plank top, boards laid individually so the joints read
    nb = 5
    for i in range(nb):
        yy = y0 + (y1 - y0) * (i + 0.5) / nb
        m.box((cx, yy, TBL_H - 0.024), ((x1 - x0) / 2, (y1 - y0) / nb / 2 - 0.005,
              0.024), top if i % 2 else topb, rot=(R.uniform(-0.003, 0.003), 0, 0))
    m.box((cx, cy, TBL_H - 0.056), ((x1 - x0) / 2 - 0.05, (y1 - y0) / 2 - 0.02,
          0.010), bm_)                                             # under-rail
    for sx in (-1, 1):                                             # breadboard ends
        m.box((cx + sx * ((x1 - x0) / 2 + 0.030), cy, TBL_H - 0.024),
              (0.030, (y1 - y0) / 2, 0.026), topb)

    # three trestles, painted green like the rest of the joinery
    for tx in (x0 + 0.62, cx, x1 - 0.62):
        m.box((tx, cy, 0.055), (0.075, (y1 - y0) / 2 + 0.02, 0.055), g)   # foot
        m.box((tx, cy, (TBL_H - 0.10) / 2), (0.060, 0.075, (TBL_H - 0.10) / 2), g)
        m.box((tx, cy, TBL_H - 0.095), (0.075, (y1 - y0) / 2 - 0.06, 0.045), g)
    m.box((cx, cy, 0.30), ((x1 - x0) / 2 - 0.55, 0.045, 0.045), bm_)  # stretcher

    # benches, each pushed askew by a few degrees
    def bench(by, ang, seat_mat):
        ca, sa = math.cos(ang), math.sin(ang)

        def P(dx):
            return (cx + dx * ca, by + dx * sa)
        px, py = P(0.0)
        m.box((px, py, 0.435), ((x1 - x0) / 2 - 0.12, 0.145, 0.028), topb,
              rot=(0, 0, ang))
        for dx in (x0 + 0.50 - cx, 0.0, x1 - 0.50 - cx):
            lx, ly = P(dx)
            m.box((lx, ly, 0.205), (0.055, 0.125, 0.205), seat_mat, rot=(0, 0, ang))
        m.box((px, py, 0.155), ((x1 - x0) / 2 - 0.35, 0.030, 0.030), bm_,
              rot=(0, 0, ang))

    bench(y0 - 0.56, 0.048, ox)
    bench(y1 + 0.55, -0.014, M("mat_n_blue"))
    return m.finish(c, bevel=0.007)


def build_table_props(c):
    """Mugs, a jug, a stew bowl, a candle, and a hand of cards face-down with
    the pot still on the table. Density here is what sells 'a crowd was just
    sitting where the player is standing'."""
    m = IMesh("table_props")
    pew, cer = M("mat_n_pewter"), M("mat_n_ceramic")
    cerb, cerox = M("mat_n_ceramic_b"), M("mat_n_ceramic_ox")
    cergn, cerbl = M("mat_n_ceramic_gn"), M("mat_n_ceramic_bl")
    ale, aled = M("mat_n_ale"), M("mat_n_ale_dark")
    brs, wax, ir = M("mat_n_brass"), M("mat_n_wax"), M("mat_n_iron")
    card, pap = M("mat_n_card"), M("mat_n_paper")
    z = TBL_H

    mugs = [(-2.42, -0.78, pew, ale, 0.4), (-2.05, -0.36, cerb, ale, 2.1),
            (-1.42, -0.80, pew, aled, 1.2), (-0.72, -0.30, cergn, ale, 3.0),
            (0.28, -0.82, pew, ale, 0.2), (0.92, -0.34, cerox, aled, 2.6),
            (1.62, -0.76, cerbl, ale, 1.7), (2.02, -0.30, pew, None, 0.9)]
    for (x, y, mt, al, rz) in mugs:
        mug(m, x, y, z, mt, ale=al, rz=rz)
    mug(m, -0.18, -0.88, z, pew, rz=0.9, tipped=True)          # one knocked over
    for i in range(7):                                          # the spill
        m.cyl((-0.06 + i * 0.035, -0.86 + R.uniform(-0.03, 0.03), z + 0.002),
              R.uniform(0.020, 0.045), 0.003, aled, seg=8)

    # a big jug and a stew bowl with a spoon
    m.lathe((-1.05, -0.58, z), [(0.0, 0), (0.085, 0.010), (0.105, 0.085),
            (0.092, 0.155), (0.058, 0.195), (0.066, 0.215), (0.0, 0.218)],
            cer, seg=14, lumpy=0.04)
    m.ring((-1.05 + 0.108, -0.58, z + 0.125), 0.052, 0.011, cer, axis="X", seg=8)
    m.lathe((0.52, -0.60, z), [(0.0, 0), (0.055, 0.004), (0.115, 0.055),
            (0.118, 0.062), (0.106, 0.058), (0.048, 0.010), (0.0, 0.012)],
            cerb, seg=14)
    m.cyl((0.52, -0.60, z + 0.048), 0.098, 0.006, M("mat_n_ale_dark"), seg=12)
    m.strand([(0.52, -0.60, z + 0.052), (0.66, -0.50, z + 0.11)], 0.008, pew, seg=5)
    # a board with bread and cheese
    m.box((1.32, -0.58, z + 0.010), (0.145, 0.105, 0.010), M("mat_n_shelf"), rot=(0, 0, 0.2))
    for i in range(3):
        m.sphere((1.26 + i * 0.075, -0.58 + R.uniform(-0.03, 0.03), z + 0.042),
                 0.048, M("mat_n_straw"), seg=9, rings=6, scale=(1.2, 0.85, 0.75))
    m.box((1.44, -0.66, z + 0.038), (0.055, 0.048, 0.028), M("mat_n_wax"), rot=(0, 0, 0.4))

    # the candle in the middle of the table
    cxx, cyy = -0.35, -0.60
    m.lathe((cxx, cyy, z), [(0.0, 0), (0.085, 0.006), (0.078, 0.018), (0.030, 0.024),
            (0.0, 0.026)], brs, seg=12)
    m.cyl((cxx, cyy, z + 0.115), 0.022, 0.180, wax, seg=10, r2=0.020)
    for i in range(4):                                          # wax runs
        a = R.uniform(0, 6.28)
        m.cyl((cxx + 0.021 * math.cos(a), cyy + 0.021 * math.sin(a), z + 0.10),
              0.006, R.uniform(0.05, 0.11), wax, seg=6)
    m.cyl((cxx, cyy, z + 0.212), 0.0035, 0.016, ir, seg=6)
    m.cyl((cxx, cyy, z + 0.238), 0.017, 0.046, M("mat_n_candleflame"), seg=8, r2=0.002)

    # the card game, abandoned mid-hand
    for i in range(5):                                          # a fanned hand
        a = -0.45 + i * 0.22
        m.box((-1.92 + i * 0.028, -0.52 + i * 0.012, z + 0.003 + i * 0.001),
              (0.032, 0.046, 0.0016), card, rot=(0, 0, a))
    for i in range(4):                                          # face-down pile
        m.box((-1.55, -0.72, z + 0.003 + i * 0.0018), (0.032, 0.046, 0.0016),
              card, rot=(0, 0, R.uniform(-0.12, 0.12)))
    for (px, py, a) in ((-1.18, -0.44, 0.6), (-1.02, -0.62, -0.3), (-0.86, -0.40, 1.2),
                        (0.10, -0.44, 0.2), (0.26, -0.70, -0.8)):
        m.box((px, py, z + 0.0035), (0.032, 0.046, 0.0016), card, rot=(0, 0, a))
    for i in range(9):                                          # the pot
        m.cyl((-1.30 + R.uniform(-0.06, 0.06), -0.58 + R.uniform(-0.05, 0.05),
               z + 0.004 + R.uniform(0, 0.004)), 0.019, 0.005, brs, seg=10,
              rot=(0, 0, R.uniform(0, 1)))
    # a dice cup and two dice
    m.lathe((-0.72, -0.86, z), [(0.0, 0), (0.042, 0.004), (0.048, 0.085), (0.0, 0.086)],
            M("mat_n_leather"), seg=10)
    for i in range(2):
        m.box((-0.55 + i * 0.055, -0.90 + i * 0.03, z + 0.014), (0.014, 0.014, 0.014),
              M("mat_n_ceramic_cr"), rot=(0.3 * i, 0.2, R.uniform(0, 1)))

    # The RIGHT half of the table was bare in v3 -- a long empty slab through
    # the middle of the frame. A second party's end of the table: a stew pot,
    # plates, a lantern set down, a letter being read.
    m.lathe((1.86, -0.62, z), [(0.0, 0), (0.098, 0.008), (0.135, 0.075),
            (0.128, 0.135), (0.108, 0.155), (0.0, 0.158)], M("mat_n_iron"), seg=14)
    m.ring((1.86, -0.62, z + 0.150), 0.112, 0.010, M("mat_n_iron"), axis="Z", seg=14)
    for s_ in (-1, 1):
        m.ring((1.86 + s_ * 0.138, -0.62, z + 0.115), 0.030, 0.009,
               M("mat_n_iron"), axis="Y", seg=8)
    for i in range(4):                                       # a stack of plates
        m.lathe((2.20, -0.34, z + i * 0.016),
                [(0.0, 0), (0.052, 0.002), (0.098, 0.014), (0.094, 0.016),
                 (0.044, 0.005), (0.0, 0.006)], M("mat_n_ceramic_cr"), seg=12)
    m.box((1.32, -0.30, z + 0.005), (0.078, 0.055, 0.005), M("mat_n_paper"),
          rot=(0, 0, -0.55))                                  # a letter
    m.box((1.48, -0.24, z + 0.004), (0.062, 0.044, 0.004), M("mat_n_notice"),
          rot=(0, 0, 0.9))
    m.lathe((0.66, -0.24, z), [(0.0, 0), (0.062, 0.006), (0.058, 0.020),
            (0.026, 0.026), (0.0, 0.028)], M("mat_n_brass"), seg=12)
    m.cyl((0.66, -0.24, z + 0.085), 0.019, 0.145, M("mat_n_wax"), seg=10, r2=0.017)
    m.cyl((0.66, -0.24, z + 0.178), 0.015, 0.040, M("mat_n_candleflame"),
          seg=8, r2=0.002)
    # a coat slung over the end of the front bench
    m.cloth((-2.30, -1.60, 0.455), (1, 0, 0), (0, -1, 0), 0.44, 0.40,
            M("mat_n_oilskin_b"), folds=3, bulge=0.06, seed=9.4, taper=0.95, nv=5)

    # somebody's hat and gloves dumped on the back bench, a pipe on the table
    m.lathe((1.90, 0.42, 0.463), [(0.0, 0), (0.175, 0.004), (0.170, 0.012),
            (0.095, 0.016), (0.098, 0.075), (0.088, 0.090), (0.0, 0.092)],
            M("mat_n_canvas_b"), seg=12)
    m.strand([(-2.15, -0.30, z + 0.008), (-1.98, -0.24, z + 0.008)], 0.008, bm := ir, seg=5)
    m.lathe((-1.96, -0.235, z + 0.004), [(0.0, 0), (0.022, 0.002), (0.024, 0.030),
            (0.0, 0.031)], M("mat_n_ceramic_b"), seg=8)
    ob = m.finish(c, bevel=0.004)

    lit = bpy.data.lights.new("TBL_candle", "POINT")
    lit.energy, lit.color, lit.shadow_soft_size = 7.0, (1.0, 0.68, 0.32), 0.035
    lo = bpy.data.objects.new("TBL_candle", lit)
    c.objects.link(lo)
    lo.location = (cxx, cyy, z + 0.245)
    return ob


# ------------------------------------------------------------- small tables

def build_small_tables(c, kit):
    obs = []
    m = IMesh("small_tables")
    top, topb = M("mat_n_table"), M("mat_n_table_b")
    g, ox, blu = M("mat_n_green"), M("mat_n_oxblood_b"), M("mat_n_blue")
    bm_, pew, cer = M("mat_n_beam"), M("mat_n_pewter"), M("mat_n_ceramic")

    def stool(x, y, r=0.145, h=0.44, mat=None, rz=0.0):
        m.cyl((x, y, h - 0.018), r, 0.036, topb, seg=12, rot=(0, 0, rz))
        for a in range(3):
            ang = rz + a * 2.094
            m.strand([(x + (r - 0.03) * math.cos(ang) * 1.25,
                       y + (r - 0.03) * math.sin(ang) * 1.25, 0.0),
                      (x + (r - 0.06) * math.cos(ang), y + (r - 0.06) * math.sin(ang),
                       h - 0.03)], 0.021, mat or g, seg=6)

    def sq_table(x, y, w, d, rz, ma, mb):
        m.box((x, y, TBL_H - 0.022), (w, d, 0.022), ma, rot=(0, 0, rz))
        m.box((x, y, TBL_H - 0.062), (w - 0.05, d - 0.05, 0.020), bm_, rot=(0, 0, rz))
        for (sx, sy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            lx = x + (sx * (w - 0.065)) * math.cos(rz) - (sy * (d - 0.065)) * math.sin(rz)
            ly = y + (sx * (w - 0.065)) * math.sin(rz) + (sy * (d - 0.065)) * math.cos(rz)
            m.box((lx, ly, (TBL_H - 0.04) / 2), (0.038, 0.038, (TBL_H - 0.04) / 2),
                  mb, rot=(0, 0, rz))

    # --- right front, under the window: two travellers waiting it out -------
    sq_table(3.24, -1.78, 0.46, 0.46, 0.18, top, ox)
    stool(3.22, -2.48, rz=0.4, mat=ox)
    stool(2.56, -1.55, rz=1.1, mat=g)
    mug(m, 3.10, -1.66, TBL_H, pew, ale=M("mat_n_ale"), rz=1.6)
    mug(m, 3.40, -1.92, TBL_H, M("mat_n_ceramic_bl"), ale=M("mat_n_ale_dark"), rz=4.2)
    m.lathe((3.42, -1.58, TBL_H), [(0.0, 0), (0.048, 0.004), (0.098, 0.048),
            (0.092, 0.052), (0.040, 0.008), (0.0, 0.010)], cer, seg=12)
    m.box((3.06, -1.98, TBL_H + 0.006), (0.090, 0.062, 0.006), M("mat_n_paper"),
          rot=(0, 0, 0.35))
    # a lantern set on the table, and a pack leaning on the stool
    m.box((2.56, -1.55, 0.50), (0.16, 0.13, 0.20), M("mat_n_canvas_b"), rot=(0.2, 0, 0.9))

    # --- left front, by the hearth: one man, a bottle, a pipe ---------------
    sq_table(-2.72, -2.42, 0.42, 0.42, -0.22, topb, blu)
    stool(-2.05, -2.55, rz=0.7, mat=blu)
    stool(-3.00, -3.02, rz=1.4, mat=g)
    mug(m, -2.62, -2.30, TBL_H, pew, ale=M("mat_n_ale"), rz=2.2)
    m.lathe((-2.86, -2.52, TBL_H), [(0.0, 0), (0.038, 0.006), (0.042, 0.10),
            (0.020, 0.155), (0.019, 0.205), (0.026, 0.212), (0.0, 0.214)],
            M("mat_n_glass_green"), seg=12)
    m.box((-2.58, -2.58, TBL_H + 0.005), (0.075, 0.055, 0.005), M("mat_n_paper"),
          rot=(0, 0, -0.4))
    obs.append(m.finish(c, bevel=0.006))
    return obs


# ------------------------------------------------------------- the stranded

def build_travellers(c, kit):
    """Luggage, coats, sticks, bedrolls. The brief in one word: EVERYWHERE.
    Anything that says people arrived, could not leave, and put their things
    down wherever there was room."""
    obs = []
    m = IMesh("luggage")
    lt, ltb = M("mat_n_leather"), M("mat_n_leather_b")
    cv, cvb, sack = M("mat_n_canvas"), M("mat_n_canvas_b"), M("mat_n_sack")
    ir, bm_, ox = M("mat_n_iron"), M("mat_n_beam"), M("mat_n_oxblood_b")
    g, blu, bur = M("mat_n_green_b"), M("mat_n_blue"), M("mat_n_burlap")

    def trunk(x, y, z, w, d, h, rz, body, lid=None, bands=3):
        m.box((x, y, z + h * 0.42), (w, d, h * 0.42), body, rot=(0, 0, rz))
        m.box((x, y, z + h * 0.90), (w * 1.02, d * 1.02, h * 0.10),
              lid or body, rot=(0, 0, rz))
        for i in range(bands):
            bx = -w + 2 * w * (i + 0.5) / bands
            m.box((x + bx * math.cos(rz), y + bx * math.sin(rz), z + h * 0.5),
                  (0.018, d * 1.03, h * 0.52), ir, rot=(0, 0, rz))
        for (sx, sy) in ((-1, -1), (-1, 1), (1, -1), (1, 1)):     # corner irons
            cxx = x + (sx * w) * math.cos(rz) - (sy * d) * math.sin(rz)
            cyy = y + (sx * w) * math.sin(rz) + (sy * d) * math.cos(rz)
            m.box((cxx, cyy, z + h * 0.90), (0.030, 0.030, h * 0.12), ir, rot=(0, 0, rz))
        m.box((x - (d + 0.012) * math.sin(rz), y + (d + 0.012) * math.cos(rz),
               z + h * 0.72), (w * 0.16, 0.014, h * 0.10), ir, rot=(0, 0, rz))

    def duffel(x, y, z, ln, r, rz, mat, tilt=0.0):
        m.lathe((x, y, z + r), [(0.0, -ln / 2), (r * 0.55, -ln / 2 + 0.02),
                (r, -ln / 2 + 0.10), (r * 1.04, 0), (r, ln / 2 - 0.10),
                (r * 0.55, ln / 2 - 0.02), (0.0, ln / 2)], mat, seg=12,
                aspect=(1.0, 1.0), lumpy=0.06, rot=rz)
        # lying down: rotate by building along Y then trusting the lathe axis is Z,
        # so instead lay it out as a capsule of boxes
    def bedroll(x, y, z, ln, r, rz, mat):
        e = (math.pi / 2, 0, rz)
        m.cyl((x, y, z + r), r, ln, mat, seg=12, rot=(0, math.pi / 2, rz), r2=r * 0.96)
        for s in (-1, 1):
            m.ring((x + s * (ln / 2 - 0.02) * math.cos(rz),
                    y + s * (ln / 2 - 0.02) * math.sin(rz), z + r), r * 0.7, 0.012,
                   M("mat_n_canvas"), axis="X" if abs(math.cos(rz)) > 0.5 else "Y", seg=8)
        m.strand([(x - 0.10 * math.sin(rz), y + 0.10 * math.cos(rz), z + r * 1.9),
                  (x + 0.10 * math.sin(rz), y - 0.10 * math.cos(rz), z + r * 0.1)],
                 0.012, M("mat_n_leather"), seg=5)

    def sackbag(x, y, z, h, r, seed, mat, tilt=0.0):
        m.lathe((x, y, z), [(0.0, 0), (r * 0.9, 0.02), (r, h * 0.35),
                (r * 0.92, h * 0.62), (r * 0.55, h * 0.85), (r * 0.30, h),
                (r * 0.34, h + 0.04), (0.0, h + 0.05)], mat, seg=12,
                lumpy=0.10, seed=seed)
        m.strand(sagline((x - r * 0.32, y, z + h * 0.86), (x + r * 0.32, y, z + h * 0.86),
                 0.01), 0.010, M("mat_n_canvas"), seg=4)

    # ---- the mountain by the door -----------------------------------------
    trunk(-4.34, 2.52, 0.0, 0.34, 0.24, 0.44, 0.10, ox, lid=bm_)
    trunk(-4.30, 2.48, 0.44, 0.28, 0.20, 0.32, -0.22, blu, lid=bm_, bands=2)
    trunk(-2.52, 2.96, 0.0, 0.38, 0.26, 0.40, -0.35, g, lid=bm_)
    trunk(-2.30, 2.24, 0.0, 0.26, 0.20, 0.30, 0.55, ox, lid=bm_, bands=2)
    bedroll(-3.86, 2.18, 0.0, 0.72, 0.115, 0.25, cvb)
    bedroll(-3.60, 2.34, 0.23, 0.66, 0.105, -0.15, cv)
    sackbag(-2.86, 2.66, 0.0, 0.42, 0.20, 1.1, sack)
    sackbag(-2.62, 2.44, 0.0, 0.34, 0.17, 3.3, bur)
    sackbag(-4.62, 1.98, 0.0, 0.38, 0.19, 5.2, cvb)
    # a leather satchel and a hatbox on the pile
    m.box((-4.30, 2.48, 0.92), (0.20, 0.13, 0.10), lt, rot=(0, 0.06, 0.3))
    m.strand([(-4.46, 2.40, 1.00), (-4.12, 2.58, 1.00)], 0.014, ltb, seg=5)
    m.lathe((-2.52, 2.96, 0.40), [(0.0, 0), (0.155, 0.008), (0.160, 0.135),
            (0.150, 0.145), (0.0, 0.150)], cvb, seg=12)
    # walking sticks in a stand by the door
    m.lathe((-1.78, 3.02, 0.0), [(0.0, 0), (0.135, 0.010), (0.140, 0.34),
            (0.126, 0.35), (0.0, 0.352)], M("mat_n_copper"), seg=12)
    for i in range(6):
        a = i * 1.05
        lean = R.uniform(0.06, 0.16)
        ln = R.uniform(0.95, 1.30)
        m.strand([(-1.78 + 0.05 * math.cos(a), 3.02 + 0.05 * math.sin(a), 0.03),
                  (-1.78 + math.sin(lean) * ln * math.cos(a) + 0.05 * math.cos(a),
                   3.02 + math.sin(lean) * ln * math.sin(a) + 0.05 * math.sin(a),
                   0.03 + ln)], R.uniform(0.014, 0.020),
                 bm_ if i % 2 else M("mat_n_beam_b"), seg=6)
    # a boot scraper and a puddle-stained mat at the threshold
    m.box((DOOR_X + 0.72, 3.16, 0.055), (0.075, 0.020, 0.055), ir)
    m.box((DOOR_X + 0.72, 3.16, 0.100), (0.090, 0.010, 0.012), ir)
    m.box((DOOR_X, 2.86, 0.010), (0.44, 0.26, 0.010), M("mat_n_rug"), rot=(0, 0, 0.04))

    # ---- under and beside the stair ---------------------------------------
    trunk(2.86, 1.62, 0.0, 0.30, 0.22, 0.36, 0.42, blu, lid=bm_, bands=2)
    sackbag(2.90, 2.10, 0.0, 0.36, 0.18, 7.7, sack)
    bedroll(2.72, 1.10, 0.0, 0.62, 0.100, 1.35, cv)
    # a crate being used as a table by the window bench
    m.box((4.44, -2.86, 0.20), (0.24, 0.22, 0.20), M("mat_n_crate"), rot=(0, 0, 0.2))
    sackbag(4.30, -0.30, 0.0, 0.34, 0.17, 9.1, bur)

    # ---- coats and oilskins on the peg rails ------------------------------
    oil, oilb = M("mat_n_oilskin"), M("mat_n_oilskin_b")
    wool, woolb = M("mat_n_wool"), M("mat_n_wool_b")
    # back wall rail (x -2.88 .. -1.88), garments hang toward -Y
    for (px, w, h, mat, sd) in ((-2.74, 0.30, 0.72, oil, 0.3),
                                (-2.40, 0.28, 0.64, wool, 1.7),
                                (-2.05, 0.26, 0.70, oilb, 3.1)):
        m.cyl((px, IY - 0.075, RAIL_Z + 0.02), 0.014, 0.075, M("mat_n_green_c"),
              seg=6, rot=(math.pi / 2, 0, 0))
        m.sphere((px, IY - 0.108, RAIL_Z + 0.02), 0.020, M("mat_n_green_c"), seg=7, rings=5)
        m.cloth((px, IY - 0.115, RAIL_Z - 0.01), (1, 0, 0), (0, -1, 0), w, h,
                mat, folds=4, bulge=0.07, seed=sd)
    # a hat on the end peg
    m.lathe((-1.92, IY - 0.135, RAIL_Z - 0.02),
            [(0.0, 0), (0.155, 0.006), (0.150, 0.016), (0.090, 0.020),
             (0.092, 0.090), (0.082, 0.100), (0.0, 0.102)], cvb, seg=12)
    # left wall rail (y 1.12 .. 2.32), garments hang toward +X
    for (py, w, h, mat, sd) in ((1.22, 0.30, 0.76, oilb, 5.5),
                                (1.66, 0.28, 0.66, woolb, 2.2),
                                (2.10, 0.30, 0.72, oil, 4.4)):
        m.cyl((-IX + 0.075, py, RAIL_Z + 0.02), 0.014, 0.075, M("mat_n_green_c"),
              seg=6, rot=(0, math.pi / 2, 0))
        m.sphere((-IX + 0.108, py, RAIL_Z + 0.02), 0.020, M("mat_n_green_c"), seg=7, rings=5)
        m.cloth((-IX + 0.115, py, RAIL_Z - 0.01), (0, 1, 0), (1, 0, 0), w, h,
                mat, folds=4, bulge=0.07, seed=sd)
    obs.append(m.finish(c, bevel=0.006))

    # kit barrels and a crate, reskinned
    obs.append(place(kit["kit_barrel"], (-4.48, 3.06, 0.0), rot=(0, 0, 0.3), c=c))
    obs.append(place(kit["kit_barrel"], (0.26, 2.92, 0.0), rot=(0, 0, 1.1), c=c))
    obs.append(place(kit["kit_crate"], (4.30, 2.62, 0.0), rot=(0, 0, -0.25), c=c))
    obs.append(place(kit["kit_rope_coil"], (4.52, -3.02, 0.0), c=c))
    return obs


# ------------------------------------------------------------- foreground

def build_foreground(c, kit):
    """v1's bottom quarter was bare plank floor -- dead space in the most
    valuable real estate in the frame. The fill has to respect the walkable
    lane, so it is a flat rug down the middle and mass at the edges, plus the
    detail that tells the whole story in one prop: people are sleeping on the
    common-room floor, because there are no rooms left."""
    obs = []
    m = IMesh("foreground")
    cv, cvb = M("mat_n_canvas"), M("mat_n_canvas_b")
    wool, woolb = M("mat_n_wool"), M("mat_n_wool_b")
    lt, ir, bm_ = M("mat_n_leather"), M("mat_n_iron"), M("mat_n_beam")
    g, ox = M("mat_n_green"), M("mat_n_oxblood_b")

    # A worn rug: flat, so it dresses the lane without blocking it. v3 laid it
    # as ONE dark box and it read as a hole cut in the floor -- the single worst
    # black region in the frame. Woven stripes of alternating value fix it: the
    # eye reads pattern as a surface and reads flat black as absence.
    rug_a, rug_b = M("mat_n_rug"), M("mat_n_burlap")
    rx0, rx1, ry0, ry1 = -2.20, 2.40, -2.86, -1.46
    nst = 9
    for i in range(nst):
        y0 = ry0 + (ry1 - ry0) * i / nst
        y1 = ry0 + (ry1 - ry0) * (i + 1) / nst
        m.box(((rx0 + rx1) / 2, (y0 + y1) / 2, 0.007),
              ((rx1 - rx0) / 2, (y1 - y0) / 2, 0.007),
              rug_a if i % 2 else rug_b, rot=(0, 0, 0.010))
    for yy in (ry0, ry1):                                  # bound edges
        m.box(((rx0 + rx1) / 2, yy, 0.010), ((rx1 - rx0) / 2, 0.055, 0.010),
              M("mat_n_oxblood_b"), rot=(0, 0, 0.010))
    for sx in (rx0, rx1):                                  # rolled/frayed ends
        m.cyl((sx, (ry0 + ry1) / 2, 0.014), 0.016, (ry1 - ry0), rug_b,
              seg=8, rot=(math.pi / 2, 0, 0))

    # a bedroll made up on the floor by the hearth side, blanket thrown back,
    # a pack for a pillow: the inn is full
    bx, by, rz = -1.72, -2.86, 0.24
    m.box((bx, by, 0.035), (0.86, 0.34, 0.035), cvb, rot=(0, 0, rz))
    m.cloth((bx + 0.30, by + 0.34, 0.145), (1, 0, 0), (0, -1, 0), 1.05, 0.62,
            wool, folds=3, bulge=0.05, seed=8.1, taper=0.95, nv=5)
    m.lathe((bx - 0.66, by + 0.02, 0.0), [(0.0, 0), (0.16, 0.03), (0.175, 0.13),
            (0.10, 0.20), (0.0, 0.215)], M("mat_n_sack"), seg=12, lumpy=0.10, seed=3.3)
    m.box((bx + 0.74, by - 0.16, 0.055), (0.115, 0.075, 0.055), lt, rot=(0, 0, rz - 0.4))
    m.box((bx + 0.74, by - 0.30, 0.052), (0.110, 0.070, 0.052), lt, rot=(0, 0, rz + 0.3))

    # an overturned stool -- somebody stood up fast when the news came in
    sx_, sy_ = 1.92, -2.92
    m.cyl((sx_, sy_, 0.145), 0.145, 0.036, M("mat_n_table_b"), seg=12,
          rot=(math.pi / 2, 0, 0.5))
    for a in range(3):
        ang = a * 2.094 + 0.5
        m.strand([(sx_ + 0.02 * math.cos(ang), sy_ - 0.02, 0.145),
                  (sx_ + 0.34 * math.cos(ang) + 0.06, sy_ + 0.30,
                   0.145 + 0.30 * math.sin(ang))], 0.021, g, seg=6)

    # mass at the right edge: crate stack, a barrel-top table, a dropped mug
    m.box((3.98, -2.62, 0.20), (0.26, 0.24, 0.20), M("mat_n_blue"), rot=(0, 0, 0.16))
    m.box((3.94, -2.58, 0.55), (0.21, 0.19, 0.155), M("mat_n_crate_b"), rot=(0, 0, -0.30))
    m.lathe((4.36, -1.62, 0.0), [(0.0, 0), (0.165, 0.02), (0.185, 0.30),
            (0.170, 0.52), (0.150, 0.56), (0.0, 0.565)], ox, seg=14, lumpy=0.03)
    for hz in (0.10, 0.30, 0.50):
        m.ring((4.36, -1.62, hz), 0.183, 0.014, ir, axis="Z", seg=14)
    mug(m, 0.72, -2.42, 0.010, M("mat_n_pewter"), rz=1.1, tipped=True)

    # mass at the left edge: a bucket, a broom, a coil of line
    m.lathe((-3.62, -3.02, 0.0), [(0.0, 0), (0.115, 0.012), (0.135, 0.24),
            (0.120, 0.245), (0.0, 0.248)], M("mat_n_rust"), seg=12)
    m.strand([(-3.86, -2.86, 0.02), (-3.60, -2.62, 1.28)], 0.018, bm_, seg=6)
    m.box((-3.85, -2.84, 0.10), (0.075, 0.060, 0.090), M("mat_n_straw"), rot=(0.2, 0, 0.3))
    obs.append(m.finish(c, bevel=0.006))
    obs.append(place(kit["kit_crate"], (-4.28, -1.86, 0.0), rot=(0, 0, 0.22), c=c))
    return obs



# ------------------------------------------------------------- density pass

def build_density(c, kit):
    """v8 read thinner than the accepted archetype: three parallel empty bench
    slabs through the middle and wide bare floor either side of them. The lane
    has to stay walkable for two players, so the floor gets FLAT texture
    (rushes, as any real inn floor had) and the mass goes at the lane edges and
    on top of the benches."""
    obs = []
    m = IMesh("density")
    straw = M("mat_n_straw")
    cv, cvb, sack = M("mat_n_canvas"), M("mat_n_canvas_b"), M("mat_n_sack")
    lt, ir, bm_ = M("mat_n_leather"), M("mat_n_iron"), M("mat_n_beam")
    wool, oil = M("mat_n_wool"), M("mat_n_oilskin")

    # ---- floor rushes: flat, walkable, and they kill the bare-plank look ---
    BLOCK = [(-4.90, -2.90, HRTH_Y0, HRTH_Y1),        # hearth apron
             (CTR_X0 - 0.2, IX, CTR_Y0 - 0.2, IY),    # behind the counter
             (STR_X0 - 0.1, IX, STR_Y0 - 0.1, IY)]    # the stair

    def blocked(x, y):
        return any(a <= x <= b and cc <= y <= d for (a, b, cc, d) in BLOCK)

    n = 0
    while n < 340:
        x = R.uniform(-4.30, 4.55)
        y = R.uniform(-3.25, 3.10)
        if blocked(x, y):
            continue
        m.box((x, y, 0.006), (R.uniform(0.030, 0.075), 0.006, 0.0035), straw,
              rot=(0, R.uniform(-0.05, 0.05), R.uniform(0, 3.14)))
        n += 1
    for (cx, cy) in ((-1.30, -1.30), (2.60, 0.90), (0.20, 1.70), (3.60, -0.90)):
        for _ in range(26):                            # swept-up drifts
            a, r = R.uniform(0, 6.28), R.uniform(0, 0.34)
            m.box((cx + r * math.cos(a), cy + r * math.sin(a), 0.010),
                  (R.uniform(0.035, 0.080), 0.007, 0.005), straw,
                  rot=(0, 0, R.uniform(0, 3.14)))

    # ---- things left on the benches ---------------------------------------
    bz = 0.435
    m.lathe((-1.05, -1.60, bz), [(0.0, 0), (0.145, 0.03), (0.160, 0.16),
            (0.100, 0.24), (0.0, 0.26)], sack, seg=12, lumpy=0.10, seed=6.1)
    m.cloth((1.28, -1.60, bz + 0.10), (1, 0, 0), (0, -1, 0), 0.46, 0.42,
            wool, folds=3, bulge=0.06, seed=11.2, taper=0.95, nv=5)
    m.box((0.42, 0.40, bz + 0.075), (0.19, 0.13, 0.075), lt, rot=(0, 0, 0.22))
    m.strand([(0.24, 0.40, bz + 0.14), (0.60, 0.40, bz + 0.14)], 0.012, lt, seg=5)
    m.cloth((-1.72, 0.40, bz + 0.12), (1, 0, 0), (0, 1, 0), 0.50, 0.44,
            oil, folds=3, bulge=0.06, seed=13.7, taper=0.95, nv=5)

    # ---- mass at the right edge of the lane, between table and stair ------
    m.box((3.98, -0.34, 0.22), (0.28, 0.25, 0.22), M("mat_n_crate"), rot=(0, 0, 0.18))
    m.box((3.92, -0.30, 0.60), (0.23, 0.20, 0.16), M("mat_n_crate_b"), rot=(0, 0, -0.34))
    m.lathe((4.42, 0.18, 0.0), [(0.0, 0), (0.15, 0.02), (0.175, 0.26),
            (0.152, 0.46), (0.0, 0.465)], M("mat_n_oxblood_b"), seg=14, lumpy=0.03)
    for hz in (0.09, 0.27, 0.43):
        m.ring((4.42, 0.18, hz), 0.174, 0.013, ir, axis="Z", seg=14)
    m.lathe((3.52, 0.28, 0.0), [(0.0, 0), (0.19, 0.03), (0.205, 0.30),
            (0.130, 0.46), (0.075, 0.52), (0.0, 0.53)], sack, seg=12,
            lumpy=0.09, seed=17.3)
    m.lathe((4.06, 0.62, 0.0), [(0.0, 0), (0.16, 0.03), (0.170, 0.24),
            (0.105, 0.37), (0.0, 0.39)], cvb, seg=12, lumpy=0.10, seed=21.1)

    # ---- a bench under the window with a traveller's kit on it ------------
    m.box((4.44, -1.30, 0.425), (0.20, 0.52, 0.030), M("mat_n_table_b"))
    for byy in (-1.72, -0.88):
        m.box((4.44, byy, 0.200), (0.16, 0.045, 0.200), M("mat_n_blue"))
    m.lathe((4.44, -1.10, 0.455), [(0.0, 0), (0.115, 0.02), (0.125, 0.16),
            (0.075, 0.25), (0.0, 0.265)], cv, seg=12, lumpy=0.10, seed=27.7)
    m.box((4.44, -1.62, 0.485), (0.135, 0.095, 0.030), M("mat_n_paper"),
          rot=(0, 0, 0.25))

    # ---- bottom-left: a barrow-load of somebody's goods, and a lantern ----
    m.box((-3.92, -1.62, 0.19), (0.24, 0.20, 0.19), M("mat_n_oxblood"), rot=(0, 0, -0.2))
    m.lathe((-3.34, -1.44, 0.0), [(0.0, 0), (0.16, 0.03), (0.172, 0.22),
            (0.105, 0.35), (0.0, 0.37)], sack, seg=12, lumpy=0.10, seed=31.9)
    obs.append(m.finish(c, bevel=0.005))
    return obs


# ---------------------------------------------------------------- hanging

def build_hanging(c, kit):
    """Ordinary warm hanging lanterns (NO magical flames) plus an iron ring
    over the long table. Also the things that hang because there is nowhere
    left to put them: mugs, a wet cloak, herbs."""
    obs = []
    lamp = kit["kit_lantern_hanging"]
    m = IMesh("hanging")
    ir, bm_ = M("mat_n_iron"), M("mat_n_beam")

    spots = [((1.90, 2.05, 2.28), 46.0),        # over the counter
             ((-3.40, 2.42, 2.34), 40.0),       # over the door
             ((3.30, 0.55, 2.26), 34.0),        # at the stair foot
             ((3.24, -1.78, 2.30), 34.0),       # over the small table
             ((-2.72, -2.42, 2.34), 30.0)]      # over the far small table
    for (loc, e) in spots:
        # chain up to the nearest beam
        m.strand([(loc[0], loc[1], loc[2] + 0.10), (loc[0], loc[1], BEAM_Z - 0.02)],
                 0.010, ir, seg=4)
        obs.append(place_lantern(lamp, loc, c, energy=e))

    # the iron ring over the long table: five candles, one feature light
    rx, ry, rz = -0.35, -0.60, 2.16
    m.ring((rx, ry, rz), 0.42, 0.020, ir, axis="Z", seg=16)
    m.ring((rx, ry, rz + 0.03), 0.30, 0.014, ir, axis="Z", seg=14)
    for a in range(3):
        ang = a * 2.094 + 0.5
        m.strand([(rx + 0.42 * math.cos(ang), ry + 0.42 * math.sin(ang), rz),
                  (rx, ry, rz + 0.62)], 0.008, ir, seg=5)
    m.strand([(rx, ry, rz + 0.62), (rx, ry, BEAM_Z - 0.02)], 0.011, ir, seg=4)
    for a in range(5):
        ang = a * 1.2566 + 0.3
        cxx = rx + 0.42 * math.cos(ang)
        cyy = ry + 0.42 * math.sin(ang)
        m.lathe((cxx, cyy, rz + 0.012), [(0.0, 0), (0.048, 0.004), (0.042, 0.012),
                (0.018, 0.016), (0.0, 0.018)], ir, seg=8)
        m.cyl((cxx, cyy, rz + 0.082), 0.018, 0.128, M("mat_n_wax"), seg=8, r2=0.016)
        m.cyl((cxx, cyy, rz + 0.154), 0.014, 0.038, M("mat_n_candleflame"), seg=8, r2=0.002)
    lit = bpy.data.lights.new("RING_candles", "POINT")
    lit.energy, lit.color, lit.shadow_soft_size = 34.0, (1.0, 0.66, 0.30), 0.30
    lo = bpy.data.objects.new("RING_candles", lit)
    c.objects.link(lo)
    lo.location = (rx, ry, rz + 0.13)

    # mugs hung on hooks under a shelf behind the counter
    m.box((1.10, IY - 0.16, 1.30), (0.38, 0.14, 0.018), M("mat_n_shelf"))
    for sx in (-0.30, 0.30):
        m.box((1.10 + sx, IY - 0.16, 1.22), (0.030, 0.14, 0.075), M("mat_n_green"))
    for i in range(4):
        hx = 0.84 + i * 0.175
        m.strand([(hx, IY - 0.20, 1.28), (hx, IY - 0.20, 1.21)], 0.006, ir, seg=4)
        mug(m, hx, IY - 0.20, 1.09, M("mat_n_pewter") if i % 2 else M("mat_n_ceramic_b"),
            rz=1.57, h=0.10, r=0.042)
    # a couple of jugs and a lamp on the shelf
    for (jx, jm) in ((0.86, M("mat_n_ceramic_gn")), (1.34, M("mat_n_ceramic_ox"))):
        m.lathe((jx, IY - 0.16, 1.318), [(0.0, 0), (0.052, 0.006), (0.062, 0.055),
                (0.052, 0.095), (0.032, 0.118), (0.036, 0.128), (0.0, 0.130)],
                jm, seg=12)

    # A plate rack over the coat pegs. The room was reading as one long brown
    # chord; painted crockery is where the town palette's blue and oxblood get
    # to sing at small scale without repainting the joinery.
    m.box((-2.38, IY - 0.12, 2.16), (0.56, 0.115, 0.020), M("mat_n_shelf"))
    for sx in (-0.52, 0.52):
        m.box((-2.38 + sx, IY - 0.12, 2.10), (0.028, 0.115, 0.062), M("mat_n_green"))
    m.box((-2.38, IY - 0.055, 2.26), (0.56, 0.022, 0.085), M("mat_n_green_c"))
    plates = [M("mat_n_ceramic_bl"), M("mat_n_ceramic_ox"), M("mat_n_ceramic_cr"),
              M("mat_n_ceramic_gn"), M("mat_n_ceramic_bl"), M("mat_n_ceramic_ox")]
    for i, pm in enumerate(plates):                     # plates stood on edge
        px = -2.82 + i * 0.175
        m.lathe((px, IY - 0.085, 2.18), [(0.0, 0), (0.052, 0.004), (0.098, 0.016),
                (0.092, 0.019), (0.044, 0.007), (0.0, 0.008)], pm, seg=12,
                aspect=(1.0, 0.22), rot=0.0)
    for (jx, jm, jh) in ((-2.86, M("mat_n_ceramic_ox"), 0.115),
                         (-1.94, M("mat_n_ceramic_gn"), 0.135)):
        m.lathe((jx, IY - 0.15, 2.18), [(0.0, 0), (0.042, 0.005), (0.050, 0.045),
                (0.040, 0.080), (0.024, jh), (0.028, jh + 0.010), (0.0, jh + 0.012)],
                jm, seg=10)

    # strings of onions by the counter -- the innkeep's own larder, hung where
    # there is nowhere else left to hang anything
    for (ox_, oy_) in ((0.42, IY - 0.22), (0.60, IY - 0.26)):
        m.strand([(ox_, oy_, 2.30), (ox_, oy_, 1.86)], 0.008, M("mat_n_straw"), seg=4)
        for k in range(6):
            a = k * 1.05
            m.sphere((ox_ + 0.036 * math.cos(a), oy_ + 0.036 * math.sin(a),
                      1.90 + k * 0.055), 0.040, M("mat_n_label"), seg=8, rings=6,
                     scale=(1.0, 1.0, 0.82))

    # a wet cloak thrown over the front beam, and herb bunches by the hearth
    m.cloth((-2.72, BEAMS[1][0], BEAM_Z - 0.08), (1, 0, 0), (0, -1, 0), 0.52, 0.68,
            M("mat_n_wool_b"), folds=3, bulge=0.09, seed=6.6, taper=0.85)
    for (hx, hy, hl) in ((-4.28, 1.12, 0.30), (-4.20, 1.30, 0.26)):
        m.strand([(hx, hy, 2.30), (hx, hy, 2.30 - 0.06)], 0.006, ir, seg=4)
        for k in range(7):
            a = k * 0.9
            m.strand([(hx, hy, 2.24),
                      (hx + 0.035 * math.cos(a), hy + 0.035 * math.sin(a), 2.24 - hl)],
                     0.009, M("mat_n_straw"), seg=5)
    obs.append(m.finish(c, bevel=0.006))
    return obs


# -------------------------------------------------------------------- pads

def build_shadow_ceiling(c):
    """A roof the camera cannot see.

    The cutaway has no ceiling and no near wall, so any directional light
    floods the room from above and from the front, and nothing overhead
    bounces the lantern light back down. A plane with visible_camera off fixes
    both: the window becomes the sun's only aperture, and the room finally gets
    a top bounce. It is NOT set dressing -- it never renders.
    """
    m = IMesh("shadow_ceiling")
    m.box((0, 0.10, 3.06), (HW + 0.15, (YB + 2.95) / 2, 0.05), M("mat_n_beam"))
    ob = m.finish(c, bevel=0)
    ob.visible_camera = False
    return ob


def build_pads(c):
    """Interaction metadata, not set dressing: real objects so the exporter can
    find them, hidden from the beauty render."""
    out = []
    for name, (cx, cy, w, d) in {
            "walk_pad_door": (DOOR_X, 2.72, 1.30, 0.90),
            "walk_pad_counter": (1.90, 1.35, 2.10, 0.90)}.items():
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0,
                              matrix=Matrix.Translation((cx, cy, 0.03))
                              @ Matrix.Diagonal((w, d, 0.02, 1.0)))
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        c.objects.link(ob)
        ob.hide_render = True
        ob.display_type = "WIRE"
        out.append(ob)
    return out


# ------------------------------------------------------- lighting + camera

def setup_light(c, dusk=120.0, world=0.22, fog=0.0072, fill=38.0, sky=68.0,
                winfill=54.0, fire=200.0, firecore=4.4, ctrkey=52.0,
                beamup=32.0, stubup=30.0):
    lc = coll("INT_LIGHT")
    for n in ("SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX"):
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        lc.objects.link(o)

    kb = _mod("kit_build")
    kb.setup_world(density=0.0)              # bounded FOG_BOX only, never world
    nt = bpy.context.scene.world.node_tree
    ramp = next(n for n in nt.nodes if n.type == "VALTORGB").color_ramp
    ramp.elements[0].color = (0.09, 0.085, 0.10, 1)
    ramp.elements[1].color = (0.10, 0.12, 0.16, 1)
    ramp.elements[2].color = (0.12, 0.17, 0.28, 1)      # cool dusk outside
    next(n for n in nt.nodes if n.type == "BACKGROUND").inputs["Strength"] \
        .default_value = world

    # A low sun down the gorge, admitted ONLY by the window.
    #
    # A room with no roof and no near wall lets a sun in from everywhere, which
    # is why the camera-invisible shadow ceiling exists: it makes the window
    # the sole aperture. An AREA lamp outside the pane was tried on the sibling
    # scene and spilled onto the wall's outer face; a window shaft needs
    # PARALLEL rays, i.e. a SUN.
    #
    # NOTE kit_wall_window inherits the frame's MID RAIL, a 0.12 timber running
    # across the glass at z 1.50-1.62. Aim through the UPPER light of the sash.
    #
    # Aim: at dusk elevation a shaft landing on the floor or a tabletop arrives
    # at grazing incidence and reads as almost nothing. The surfaces facing the
    # window take it square, so it is aimed across the room at the LEFT wall --
    # specifically at the hearth breast and the wainscot beside it, where it
    # lands as a window-shaped patch with the sash bars printed across it, and
    # rakes the settle on the way. Path verified by ray cast, not by eye.
    sun = bpy.data.objects["SUN_key"]
    sun.hide_render = False
    sun.location = (HW + 1.50, WIN_Y - 0.10, 2.05)
    ru.aim(sun, (-IX, WIN_Y - 0.35, 1.28))
    sun.data.energy = dusk
    sun.data.color = (1.0, 0.58, 0.36)
    sun.data.angle = math.radians(1.6)

    # soft fill hugging the inside of the pane: the sky (rather than the sun)
    # coming through the opening, and the light that models the window reveal
    win = bpy.data.objects["FILL_bounce"]
    win.name = "DUSK_window"
    win.location = (IX - 0.05, WIN_Y, 1.55)
    win.rotation_euler = (0, math.radians(-90), 0)
    win.data.energy = winfill
    win.data.size = 1.20
    win.data.color = (0.84, 0.64, 0.58)
    win.data.shape = "SQUARE"
    win.visible_camera = False

    # a very low cool fill from the open (cutaway) side, so foreground props
    # keep a readable dark side instead of going to pure black
    amb = bpy.data.objects["RIM_gorge"]
    amb.name = "AMB_open"
    amb.location = (0.0, -7.0, 3.8)
    amb.rotation_euler = (math.radians(62), 0, 0)
    amb.data.energy = fill
    amb.data.size = 10.0
    amb.data.color = (0.38, 0.48, 0.66)

    # cool overhead wash standing in for the light through the missing roof.
    # Without it every beam top and shelf top is pure black, and a row of black
    # bars is all the eye sees.
    top = bpy.data.lights.new("SKY_top", "AREA")
    top.energy = sky
    top.size = 9.0
    top.color = (0.40, 0.50, 0.70)
    tob = bpy.data.objects.new("SKY_top", top)
    lc.objects.link(tob)
    tob.location = (0.0, -0.2, 2.94)          # just under the shadow ceiling
    tob.rotation_euler = (0, 0, 0)

    # UPLIGHT FOR THE BEAMS. From a high 3/4 camera every beam shows the eye its
    # underside and its camera-facing cheek, and SKY_top sits ABOVE them, so
    # nothing in a physical lighting rig ever touches those faces -- v1's beams
    # were pure black. This is a cheat with no source in the room, and it is the
    # right call: composition beats authenticity. It also lifts the upper wall
    # and bounces off the shadow ceiling, which softens the whole ceiling zone.
    up = bpy.data.lights.new("BEAM_up", "AREA")
    up.energy, up.size, up.color = beamup, 7.5, (0.90, 0.74, 0.56)
    uob = bpy.data.objects.new("BEAM_up", up)
    lc.objects.link(uob)
    uob.location = (0.0, 0.30, 2.24)
    uob.rotation_euler = (math.pi, 0, 0)      # -Z normal flipped to face +Z
    uob.visible_camera = False

    # v12: BEAM_up sits directly under the room's centre, so it reaches the
    # beams' UNDERSIDES but arrives nearly parallel to their camera-facing (-Y)
    # cheeks -- which is the face the 3/4 camera actually sees, and the reason
    # the two front stubs still read as black bars at v11. Two small uplights,
    # one per stub, sit FORWARD of their beam and tilt their normal back toward
    # +Y, so the light rakes the cheek as well as the soffit. Camera-invisible
    # and facing up, so they touch nothing below them.
    for nm_, (bx, by, size) in (("BEAM_up_L", (-3.45, -1.30, 3.4)),
                                ("BEAM_up_R", (3.78, -3.05, 2.8))):
        s = bpy.data.lights.new(nm_, "AREA")
        s.energy, s.size, s.color = stubup, size, (0.94, 0.74, 0.52)
        sob_ = bpy.data.objects.new(nm_, s)
        lc.objects.link(sob_)
        sob_.location = (bx, by, 2.30)
        sob_.rotation_euler = (math.pi - math.radians(30), 0, 0)
        sob_.visible_camera = False

    # The counter is the second value leader and in v1 it was nearly black. A
    # dedicated soft key over it, camera-invisible, buys the stop of separation
    # the value hierarchy asks for without touching anything else in the room.
    ck = bpy.data.lights.new("CTR_key", "AREA")
    ck.energy, ck.color = ctrkey, (1.0, 0.72, 0.44)
    ck.shape = "RECTANGLE"
    ck.size, ck.size_y = 2.60, 1.30
    ckob = bpy.data.objects.new("CTR_key", ck)
    lc.objects.link(ckob)
    ckob.location = ((CTR_X0 + CTR_X1) / 2, (CTR_Y0 + CTR_Y1) / 2 + 0.10, 2.40)
    ckob.rotation_euler = (0, 0, 0)
    ckob.visible_camera = False

    # ---- the fire -------------------------------------------------------
    # Kit lesson 14: a light INSIDE enclosed geometry lights nothing. The
    # firebox is a stone box, so the practical that lights the ROOM sits in the
    # OPENING plane facing out, and only a weak core light sits in the flames
    # to model the logs and the back of the box.
    core = bpy.data.lights.new("FIRE_core", "POINT")
    core.energy, core.color, core.shadow_soft_size = firecore, (1.0, 0.36, 0.11), 0.16
    cob = bpy.data.objects.new("FIRE_core", core)
    lc.objects.link(cob)
    cob.location = (-4.02, -0.42, 0.40)

    mouth = bpy.data.lights.new("FIRE_mouth", "AREA")
    mouth.energy, mouth.color = fire, (1.0, 0.47, 0.18)
    mouth.shape = "RECTANGLE"
    mouth.size, mouth.size_y = 1.55, 0.95
    mob = bpy.data.objects.new("FIRE_mouth", mouth)
    lc.objects.link(mob)
    mob.location = (HRTH_XF + 0.04, (OPEN_Y0 + OPEN_Y1) / 2, 0.60)
    mob.rotation_euler = (0, math.radians(-90), 0)     # -Z normal -> +X
    mob.visible_camera = False

    # a small warm lift on the apron and the drying boots, which sit in the
    # mouth light's own shadow
    ap = bpy.data.lights.new("FIRE_apron", "POINT")
    ap.energy, ap.color, ap.shadow_soft_size = 27.0, (1.0, 0.50, 0.21), 0.45
    aob = bpy.data.objects.new("FIRE_apron", ap)
    lc.objects.link(aob)
    aob.location = (-3.02, -0.45, 0.96)

    # a warm glow in the stairwell so the head of the stair is a dark WARM
    # recess with treads in it, not a black rectangle, plus a rake down the
    # flight itself -- v2's stair was legible only to someone who already knew
    # it was there
    sw = bpy.data.lights.new("STAIR_glow", "POINT")
    sw.energy, sw.color, sw.shadow_soft_size = 26.0, (1.0, 0.62, 0.30), 0.20
    sob = bpy.data.objects.new("STAIR_glow", sw)
    lc.objects.link(sob)
    sob.location = ((STR_X0 + STR_X1) / 2, IY + 0.30, STR_N * STR_RISE + 0.70)

    st2 = bpy.data.lights.new("STAIR_rake", "AREA")
    st2.energy, st2.color = 30.0, (1.0, 0.70, 0.40)
    st2.shape, st2.size, st2.size_y = "RECTANGLE", 1.90, 1.30
    s2ob = bpy.data.objects.new("STAIR_rake", st2)
    lc.objects.link(s2ob)
    s2ob.location = ((STR_X0 + STR_X1) / 2, STR_Y0 + 1.05, 2.55)
    s2ob.visible_camera = False

    # FOREGROUND FILL. The luma audit put a band across the bottom fifth of v2
    # at 3-14/100 -- a dark strip far wider than a fist, straight through the
    # most valuable part of the frame. Broad, weak, warm and camera-invisible:
    # it lifts the near floor and the front bench without flattening the hearth.
    fg = bpy.data.lights.new("FG_fill", "AREA")
    fg.energy, fg.color, fg.size = 52.0, (1.0, 0.76, 0.52), 7.0
    fgob = bpy.data.objects.new("FG_fill", fg)
    lc.objects.link(fgob)
    fgob.location = (0.0, -2.30, 2.70)
    fgob.rotation_euler = (math.radians(16), 0, 0)
    fgob.visible_camera = False

    # bounded fog: haze inside the room only, so the lantern pools get halos.
    # A world volume would extinguish everything (kit manifest, bug 1), and the
    # box must contain NOTHING but the room (bug 2, in reverse) or the sun
    # outside lights the volume and the whole plate goes to soup.
    fb = bpy.data.objects["FOG_BOX"]
    fb.name = "FOG_ROOM"
    fb.location = (0.0, 0.0, 1.46)
    fb.scale = (4.82 / 80.0, 3.32 / 80.0, 1.44 / 30.0)
    vn = fb.data.materials[0].node_tree.nodes["Volume Scatter"]
    vn.inputs["Density"].default_value = fog
    vn.inputs["Color"].default_value = (0.62, 0.54, 0.46, 1)
    return win, amb, fb


def setup_camera(pitch=23.5, yaw=0.0, dist=11.00, target=(0.0, 0.55, 1.22),
                 vfov=35.0):
    """One fixed camera: perspective, VERTICAL fov 35 deg (Blender fits the
    sensor to the LONG edge by default, which would give 35 deg horizontally),
    high 3/4 looking down into the cutaway."""
    p, y = math.radians(pitch), math.radians(yaw)
    d = Vector((math.cos(p) * math.sin(y), math.cos(p) * math.cos(y), -math.sin(p)))
    loc = Vector(target) - d * dist
    cam = bpy.data.objects.get("CAM_int") or ru.make_camera("CAM_int", loc, target)
    cam.location = loc
    ru.aim(cam, target)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.sensor_height = 24.0
    cam.data.lens = (24.0 / 2.0) / math.tan(math.radians(vfov) / 2.0)
    cam.data.clip_start = 0.15
    cam.data.clip_end = 80.0
    bpy.context.scene.camera = cam
    return cam


# ---------------------------------------------------------------------- QA

def qa():
    """Place by projection, not by eyeball (kit lesson 16). Reports whether the
    features are in frame, and ray-maps the frame so a stray volume or a black
    hole shows up in seconds rather than after a 4-minute render."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    print("\n--- FRAME CHECK (u,v in 0..1 means in frame) ---")
    feats = {
        "hearth mantel":   (HRTH_XF - 0.2, -0.45, MANTEL_Z),
        "fire":            (-4.46, -0.42, 0.35),
        "counter L":       (CTR_X0, CTR_Y0, CTR_H),
        "counter R":       (CTR_X1, CTR_Y0, CTR_H),
        "key rack":        (1.98, IY, 1.85),
        "inn sign":        (1.98, IY, 2.52),
        "notice slate":    (-0.80, IY, 1.56),
        "door":            (DOOR_X, IY, 1.05),
        "window":          (IX, WIN_Y, 1.55),
        "stair foot":      (STR_X0, STR_Y0, 0.10),
        "stair head":      ((STR_X0 + STR_X1) / 2, IY, STR_N * STR_RISE),
        "table L":         (TBL_X0, TBL_Y0, TBL_H),
        "table R":         (TBL_X1, TBL_Y0, TBL_H),
        "luggage door":    (-4.34, 2.52, 0.44),
        "peg coats L":     (-IX, 1.66, RAIL_Z),
        "peg coats B":     (-2.40, IY, RAIL_Z),
        "front-L table":   (-2.72, -2.42, TBL_H),
        "front-R table":   (3.24, -1.78, TBL_H),
        "back wall top":   (0.0, IY, WH),
        "floor front-L":   (-HW, YF, 0.0),
        "floor front-R":   (HW, YF, 0.0),
    }
    for k, p in feats.items():
        u = world_to_camera_view(sc, cam, Vector(p))
        ok = "in " if (0.0 <= u.x <= 1.0 and 0.0 <= u.y <= 1.0) else "OUT"
        print("  %-16s %s  u=%6.3f v=%6.3f  d=%5.2f" % (k, ok, u.x, u.y, u.z))

    print("\n--- RAY MAP (what the frame actually hits) ---")
    # FOG_ROOM and shadow_ceiling are real meshes that every ray hits first and
    # that the camera never sees, so the map steps THROUGH them -- otherwise it
    # reports the fog box twelve times a row and tells you nothing.
    skip = {"FOG_ROOM", "shadow_ceiling"}
    org = cam.matrix_world.translation
    fr = [cam.matrix_world @ v for v in cam.data.view_frame(scene=sc)]
    tr, br, bl, tl = fr[0], fr[1], fr[2], fr[3]
    rows, cols = 8, 12
    for r in range(rows):
        fy = (r + 0.5) / rows
        line = []
        for cc in range(cols):
            fx = (cc + 0.5) / cols
            tgt = tl.lerp(tr, fx).lerp(bl.lerp(br, fx), fy)
            d = (tgt - org).normalized()
            o = org.copy()
            name = "---"
            for _ in range(12):
                hit, loc, nrm, idx, obj, mw = sc.ray_cast(dg, o, d)
                if not hit:
                    break
                if obj.name not in skip:
                    name = obj.name[:9]
                    break
                o = loc + d * 0.01
            line.append(name.ljust(10))
        print("   " + "".join(line))
    print()


def audit_black(path):
    """Report the darkest tiles of the render. The brief's hard rule is 'no
    black region larger than a fist' -- this measures it instead of guessing.

    Reads the saved PNG, not "Render Result": in background mode the result
    datablock's pixels come back all zeros, which had this reporting a
    perfectly black frame for a picture that plainly was not.
    """
    img = bpy.data.images.load(path)
    px = list(img.pixels)
    w, h = img.size
    gw, gh = 16, 9
    print("\n--- LUMA GRID x100 (printed top row = top of frame) ---")
    for gy in range(gh - 1, -1, -1):
        row = []
        for gx in range(gw):
            tot = n = 0
            for yy in range(gy * h // gh, (gy + 1) * h // gh, 4):
                for xx in range(gx * w // gw, (gx + 1) * w // gw, 4):
                    i = (yy * w + xx) * 4
                    tot += 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2]
                    n += 1
            row.append("%4d" % int(100 * tot / max(1, n)))
        print("   " + "".join(row))
    print()


# -------------------------------------------------------------------- main

def wipe():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for cu in list(bpy.data.curves):
        bpy.data.curves.remove(cu)
    for cc in list(bpy.data.collections):
        bpy.data.collections.remove(cc)


def build(ref=False, **light_kw):
    wipe()
    nm.make_all()
    kit = pb.append_from_kit(KIT_NAMES)
    vl = bpy.context.view_layer.layer_collection.children.get("KIT_SOURCE")
    if vl:
        vl.exclude = True

    c = coll("INN_INT")
    build_floor(c)
    build_shell(c, kit)
    build_hearth(c)
    build_hearth_dressing(c, kit)
    build_counter(c)
    build_keyrack(c)
    build_counter_props(c)
    build_innsign(c)
    build_notice(c)
    build_stair(c)
    build_long_table(c)
    build_table_props(c)
    build_small_tables(c, kit)
    build_travellers(c, kit)
    build_foreground(c, kit)
    build_density(c, kit)
    build_hanging(c, kit)
    build_shadow_ceiling(c)
    build_pads(c)

    setup_light(c, **light_kw)
    setup_camera()

    r = kit["REF_human_1p7"]
    r.location = (1.90, 1.30, 0.0)
    if r.name not in c.objects:
        c.objects.link(r)
    r.hide_render = not ref
    bpy.context.view_layer.update()
    return c


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(flag, default=None, cast=str):
        if flag in argv:
            return cast(argv[argv.index(flag) + 1])
        return default

    build(ref="--ref" in argv,
          dusk=opt("--dusk", 120.0, float),
          world=opt("--world", 0.22, float),
          fog=opt("--fog", 0.0072, float),
          fill=opt("--fill", 38.0, float),
          sky=opt("--sky", 68.0, float),
          winfill=opt("--winfill", 54.0, float),
          fire=opt("--fire", 200.0, float),
          firecore=opt("--firecore", 4.4, float),
          ctrkey=opt("--ctrkey", 52.0, float),
          beamup=opt("--beamup", 32.0, float),
          stubup=opt("--stubup", 30.0, float))

    if opt("--pitch") or opt("--yaw") or opt("--dist"):
        setup_camera(pitch=opt("--pitch", 23.5, float),
                     yaw=opt("--yaw", 0.0, float),
                     dist=opt("--dist", 11.00, float))

    # Configure the render BEFORE saving, so the .blend ships with the shipping
    # recipe baked in (Cycles / 224 + denoise / 1344x768 / AgX) and not with
    # Blender's EEVEE 1920x1080 defaults.
    if opt("--engine", "cycles") == "eevee":
        ru.setup_eevee()
    else:
        ru.setup_cycles(samples=opt("--samples", 224, int),
                        exposure=opt("--exposure", 0.70, float))

    if "--qa" in argv:
        qa()

    out = opt("--out")
    if out:
        out = out if os.path.isabs(out) else os.path.join(ROOT, out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out)
        print("SAVED", out)

    img = opt("--render")
    if img:
        img = img if os.path.isabs(img) else os.path.join(ROOT, img)
        ru.render_to(img)
        print("RENDERED", img)
        if "--audit" in argv:
            audit_black(img)

    tri = sum(len(o.data.polygons) for o in bpy.data.objects
              if o.type == "MESH" and not o.hide_render)
    print("FACES", tri)


if __name__ == "__main__":
    main()
