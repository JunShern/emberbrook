#!/usr/bin/env python3
"""Dellhollow COOKHOUSE -- the quay eatery (sceneKey `del-cookhouse-int`).

Dellhollow is a lock-town in a gorge. The cookhouse is the open kitchen on the
quay where the cook feeds dock hands and stranded travellers, and its windows
are the warm ones the whole gorge sees at dusk. Distinct from the inn: this is
where FOOD happens -- steam, sizzle, fish.

    FF9 cutaway: floor + back wall + two side walls, no near wall and no
    visible ceiling. Cutaway by camera VISIBILITY, not by deleting geometry.
    ONE fixed perspective camera, sensor_fit VERTICAL, vfov 35 deg, ~24 deg
    down, ~6.5u of vertical framing. Room 9 x 6.5u.

    wall          feature                        filler
    -----------   ----------------------------   --------------------------
    LEFT   x=-4.5 COOKING HEARTH (live fire),    fire irons, wood pile,
                  crane + cauldron, spit         hanging pots
    BACK   y=+3.25 BRICK RANGE + BREAD OVEN,     pan wall (copper), braided
                  PREP BENCH (fish filleting),   onions + garlic, DOOR
    RIGHT  x=+4.5 WINDOW (dusk) + window bench   crates, eel barrel

    centre        the SERVING HATCH -- the counter players order at, framed
                  by a post-and-lintel with the chalk menu board hung off it.
    front         the dining side: two tables mid-meal, stools, clutter.

Scale contract: character 1.7u, door 2.1u, counters 1.05u, tables 0.75u.
Engine contract: `walk_floor` is the walkable mesh; `walk_pad_door` and
`walk_pad_counter` are interaction pads (hide_render -- metadata, not
dressing).

Run headless:
    Blender -b -P tools/cookhouse_int_build.py -- \
        --out tools/blends/interiors/cookhouse-int.blend \
        --render docs/qa/interiors/cookhouse-int_v1.png --samples 224
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


pb = _mod("probe_build")                 # Mesh / append_from_kit helpers
km = _mod("cookhouse_int_materials")     # this scene's material library
ru = _mod("render_util")

R = random.Random(51823)

# ---------------------------------------------------------------- room shape
HW = 4.50                 # half width -> x in [-4.5, 4.5]        (9u)
YB, YF = 3.25, -3.25      # back wall plane / open front edge     (6.5u)
WH = 3.00                 # wall height (matches the 3x3 kit panels)
CLAD = 0.126              # kit panel: cladding front face sits this far in
IX = HW - CLAD            # inner face of the side walls  (4.374)
IY = YB - CLAD            # inner face of the back wall   (3.124)

WAINS = 1.02              # top of the moss-green wainscot
RAIL_Z = 1.86             # peg / utensil rail height

BEAM_Z = 2.84
BEAM_H = 0.068
# Only the REARMOST beam may run full width -- up there it merges with the top
# plate and reads as ceiling. Everything forward of that is a stub against one
# wall, which reads as structure instead of as a black bar across the picture.
BEAMS = ((2.62, -HW, HW), (0.35, -HW, -1.55), (-1.62, 1.95, HW))
BEAM_POST = (2.05, -1.62)

DOOR_X = 3.00             # centre of the back-wall door bay (bay 1.50..4.50)
WIN_Y = -0.55             # window bay centre on the right wall

# --- the masonry range in the back-left corner ---------------------------
RNG_X0, RNG_X1 = -3.42, -1.15     # brick range + bread oven mass
RNG_YF = 2.25                      # its front face
RNG_H = 1.05                       # range top (project counter height)
OVEN_X0, OVEN_X1 = -2.45, -1.20    # the domed bread oven above the base
OVEN_MZ = 1.42                     # oven mouth centre
OVEN_TOP = 2.05

# --- the cooking hearth on the left wall ---------------------------------
HRTH_Y0, HRTH_Y1 = 0.10, 3.25      # breast extent along the left wall
HRTH_XF = -3.42                    # front face of the breast
OPEN_Y0, OPEN_Y1 = 0.30, 2.60      # fire opening
OPEN_Z = 1.54
MANTEL_Z = 1.58
FIRE_X = -3.70                     # kit lesson 20: the fire sits FORWARD in
FIRE_Y = 1.85                      # the box, where the camera can see its bed

# --- the prep bench on the back wall -------------------------------------
PRP_X0, PRP_X1 = -0.95, 1.85
PRP_Y0, PRP_Y1 = 2.35, IY
PRP_H = 1.14

# --- the serving hatch: second value leader ------------------------------
HAT_X0, HAT_X1 = -0.55, 2.30
HAT_Y0, HAT_Y1 = 0.85, 1.60
HAT_H = 1.05
HAT_LINTEL = 2.44

TBL_H = 0.75
STOOL_H = 0.46
BENCH_H = 0.46


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

class KMesh(pb.Mesh):
    """probe_build.Mesh plus the primitives a kitchen needs: lathes for
    coopered and thrown ware, strands for eels and ironwork and pot chains,
    spheres for produce, cards for fins and leaves, and hanging cloth."""

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

    def cone(self, base, r, h, mat, seg=8, rot=(0, 0, 0), r2=0.0):
        self.cyl((base[0], base[1], base[2] + h / 2), r, h, mat, seg=seg,
                 rot=rot, r2=r2)

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

    def arch(self, center, w, h, depth, mat, axis="y", seg=9, thick=0.0):
        """A masonry arch VOID surround: the reveal of an opening, drawn as a
        ring of little blocks so the oven mouth and the log arch read as brick
        rather than as a rectangle punched in a slab."""
        cx, cy, cz = center
        r = w / 2
        for k in range(seg + 1):
            a = math.pi * k / seg
            px, pz = r * math.cos(a), (h - r) + r * math.sin(a)
            if pz < 0:
                continue
            if axis == "y":
                self.box((cx + px, cy, cz + pz), (w / (2.2 * seg), depth, 0.055),
                         mat, rot=(0, -a + math.pi / 2, 0))
            else:
                self.box((cx, cy + px, cz + pz), (depth, w / (2.2 * seg), 0.055),
                         mat, rot=(a - math.pi / 2, 0, 0))

    def card(self, center, u, v, w, h, mat, curl=0.0, nu=5, nv=4, seed=0.0):
        """A double-sided ripply rectangle: fins, leaves, hanging cloth tags."""
        u, v = Vector(u).normalized(), Vector(v).normalized()
        n = u.cross(v).normalized()
        c = Vector(center)
        rows = []
        for i in range(nv + 1):
            t = i / nv - 0.5
            row = []
            for j in range(nu + 1):
                s = j / nu - 0.5
                bulge = curl * (0.25 - s * s) + 0.35 * curl * math.sin(3.1 * t + seed)
                row.append(tuple(c + u * (s * w) + v * (t * h) + n * bulge))
            rows.append(row)
        self.quad_strip(rows, mat)

    def cloth(self, top, u, nrm, w, h, mat, taper=0.45, folds=4, bulge=0.075,
              seed=0.0, nu=9, nv=7):
        u = Vector(u).normalized()
        n = Vector(nrm).normalized()
        top = Vector(top)
        for side, off in ((1.0, 0.035), (0.97, -0.012)):
            rows = []
            for i in range(nv + 1):
                t = i / nv
                ww = w * (taper + (1.0 - taper) * min(1.0, t * 1.7)) * side
                row = []
                for j in range(nu + 1):
                    s = (j / nu - 0.5) * ww
                    ripple = math.sin(folds * math.pi * (j / nu) + seed) * bulge * (0.25 + t)
                    drop = h * t + 0.045 * math.sin(2.4 * (j / nu) + seed) * t
                    row.append(tuple(top + u * s + n * (ripple + off)
                                     + Vector((0, 0, -drop))))
                rows.append(row)
            self.quad_strip(rows, mat)


def sagline(p0, p1, dz, n=10):
    """Parabolic sag between two points -- cordage, chain, a herb line."""
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
    """A real text datablock. The menu board is the one place in this room
    where the STORY is literally written down, so it gets legible type."""
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
# by the world-up normal: right for a river town, wrong inside a kitchen.
RESKIN = {
    "mat_wallwood":      "mat_k_wall",
    "mat_timber":        "mat_k_green",
    "mat_wallwood_dark": "mat_k_oxblood",
    "mat_iron":          "mat_k_iron",
    "mat_glass_dark":    "mat_k_dusk",
    "mat_deck":          "mat_k_floor",
    "mat_lantern_glass": "mat_k_lampglass",
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

def in_flag(x, y):
    """The FLAGGED zone. A plank floor at a live cooking hearth is a building
    that has already burned down, so the whole working end of the kitchen --
    hearth apron, range front, and the strip the cook walks between them -- is
    laid in stone. It also gives the fire a cool grey surface to pool on
    instead of yet more brown timber."""
    if x < -1.05 and y > 0.30:
        return True
    if x < 0.10 and y > 1.95:                     # in front of the prep bench
        return True
    return False


def build_floor(c):
    """`walk_floor`: real plank geometry with five de-correlated materials
    dealt out board by board, plus a laid stone apron over the working end.
    The gaps plus the material rotation between them are what stop a 1k
    texture tiling visibly across 9 x 6.5 units."""
    m = KMesh("walk_floor")
    mats = [M("mat_k_floor"), M("mat_k_floor_b"), M("mat_k_floor_c"),
            M("mat_k_floor_d"), M("mat_k_floor_e")]
    x = -HW - 0.05
    i = 0
    while x < HW + 0.05:
        w = R.uniform(0.215, 0.305)
        cuts = sorted(R.uniform(YF + 0.9, YB - 0.9) for _ in range(R.choice([1, 1, 2])))
        edges = [YF - 0.08] + cuts + [YB + 0.08]
        for a, b in zip(edges[:-1], edges[1:]):
            # the greasy lane the cook has walked ten thousand times
            lane = -3.1 < x + w / 2 < 1.4 and 0.2 < (a + b) / 2 < 2.6
            mat = mats[3] if (lane and R.random() < 0.42) else \
                mats[(i + R.choice([0, 0, 1, 2, 4])) % 5]
            m.box((x + w / 2, (a + b) / 2, -0.031),
                  (w / 2 - 0.008, (b - a) / 2 - 0.006, 0.031), mat,
                  rot=(R.uniform(-0.004, 0.004), 0, 0))
            i += 1
        x += w

    # laid stone over the working end, sitting just proud of the boards
    fa, fb = M("mat_k_flag"), M("mat_k_flag_b")
    y = 0.18
    row = 0
    while y < YB + 0.30:
        d = R.uniform(0.42, 0.58)
        x = -HW - 0.10 + (0.22 if row % 2 else 0.0)
        while x < 0.45:
            w = R.uniform(0.40, 0.62)
            if in_flag(x + w / 2, y + d / 2):
                m.box((x + w / 2, y + d / 2, 0.004),
                      (w / 2 - 0.014, d / 2 - 0.014, 0.026),
                      fa if (row + int(x)) % 3 else fb,
                      rot=(R.uniform(-0.006, 0.006), R.uniform(-0.006, 0.006), 0))
            x += w
        y += d
        row += 1

    # sub-floor: no light leaks through the plank gaps
    m.box((0, 0, -0.10), (HW + 0.12, (YB - YF) / 2 + 0.12, 0.04), M("mat_k_beam"))
    ob = m.finish(c, bevel=0.006, seg=1)
    ob.name = "walk_floor"
    ob.data.name = "walk_floor"
    return ob


def build_wall_run(name, width, c):
    """A wall segment in the same local frame as the 3x3 kit panels: width
    along local X, height along Z, cladding front face at y = -0.126."""
    m = KMesh(name)
    clad = [M("mat_k_wall"), M("mat_k_wall_b")]
    frame = M("mat_k_green")
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

    # back wall left of the door bay (door bay spans 1.50 .. 4.50)
    w = build_wall_run("wall_back", 6.00, c)
    w.location = (-1.50, YB, 0)
    obs.append(w)
    # left wall: full depth
    w = build_wall_run("wall_left", 6.50, c)
    w.location = (-HW, 0.0, 0)
    w.rotation_euler = (0, 0, math.radians(90))
    obs.append(w)
    # right wall in two runs either side of the window bay (-2.05 .. 0.95)
    w = build_wall_run("wall_right_f", 1.20, c)
    w.location = (HW, -2.65, 0)
    w.rotation_euler = (0, 0, math.radians(-90))
    obs.append(w)
    w = build_wall_run("wall_right_b", 2.30, c)
    w.location = (HW, 2.10, 0)
    w.rotation_euler = (0, 0, math.radians(-90))
    obs.append(w)

    # ---- moss-green wainscot: the palette move that ties the room together --
    t = KMesh("wainscot")
    g, gb, gc = M("mat_k_green"), M("mat_k_green_b"), M("mat_k_green_c")
    ox = M("mat_k_oxblood")

    def panelled(x0, x1, y, axis, depth, mat_a, mat_b):
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

    # back wall: only the stretch right of the range and left of the door bay
    # is visible timber -- the masonry and the prep bench cover the rest
    for (x0, x1) in ((-1.10, 1.42),):
        panelled(x0, x1, IY - 0.035, "x", 0.035, g, gb)
    panelled(1.62, IX, IY - 0.035, "x", 0.035, gb, g)
    # left wall in front of the hearth breast
    panelled(YF, HRTH_Y0 - 0.10, -IX + 0.035, "y", 0.035, gb, g)
    # right wall, broken at the window bay
    panelled(YF, -2.10, IX - 0.035, "y", 0.035, g, gb)
    panelled(1.00, IY, IX - 0.035, "y", 0.035, gb, g)

    # oxblood accent band just above the capping rail -- the map's trim colour
    for (x0, x1) in ((-1.10, 1.42), (1.62, IX)):
        t.box(((x0 + x1) / 2, IY - 0.022, WAINS + 0.125),
              ((x1 - x0) / 2, 0.022, 0.038), ox)
    t.box((-IX + 0.022, (YF + HRTH_Y0 - 0.10) / 2, WAINS + 0.125),
          (0.022, (HRTH_Y0 - 0.10 - YF) / 2, 0.038), ox)
    for (y0, y1) in ((YF, -2.10), (1.00, IY)):
        t.box((IX - 0.022, (y0 + y1) / 2, WAINS + 0.125),
              (0.022, (y1 - y0) / 2, 0.038), ox)

    # corner posts + top plate the beams land on
    for (px, py, mm) in ((-IX + 0.09, IY - 0.09, g), (IX - 0.09, IY - 0.09, g),
                         (-IX + 0.09, YF + 0.10, gb), (IX - 0.09, YF + 0.10, gb)):
        t.box((px, py, WH / 2), (0.09, 0.09, WH / 2), mm)
    t.box((0, IY - 0.075, WH - 0.10), (HW, 0.075, 0.10), g)
    for sx in (-1, 1):
        t.box((sx * (IX - 0.075), 0, WH - 0.10), (0.075, (YB - YF) / 2, 0.10), g)

    # utensil / peg rails
    t.box((-IX + 0.055, -1.35, RAIL_Z), (0.055, 0.72, 0.055), gc)
    t.box((2.05, IY - 0.055, RAIL_Z + 0.10), (0.42, 0.055, 0.055), gc)
    obs.append(t.finish(c, bevel=0.008))

    # ---- ceiling beams ---------------------------------------------------
    b = KMesh("beams")
    bm_, bb = M("mat_k_beam"), M("mat_k_beam_b")
    for (y, x0, x1) in BEAMS:
        b.box(((x0 + x1) / 2, y, BEAM_Z), ((x1 - x0) / 2, BEAM_H, BEAM_H),
              bm_ if abs(y) > 1.0 else bb, rot=(0, R.uniform(-0.004, 0.004), 0))
        for sx, bx in ((-1, x0), (1, x1)):
            if abs(bx) > HW - 0.2:
                b.box((bx - sx * 0.16, y, BEAM_Z - 0.185), (0.16, 0.075, 0.09), bm_)
    # purlins run in Y, so they project as DIAGONALS rather than as horizontal
    # bars -- which is why they may cross the frame where the beams may not
    for x in (-2.95, -0.30, 2.55):
        b.box((x, 1.35, BEAM_Z + 0.115), (0.062, 1.32, 0.042), bb)
    px, py = BEAM_POST
    b.box((px, py, (BEAM_Z - BEAM_H) / 2), (0.085, 0.085, (BEAM_Z - BEAM_H) / 2), bm_)
    b.box((px, py, 0.11), (0.115, 0.115, 0.11), M("mat_k_green"))
    for s in (-1, 1):
        b.strand([(px + s * 0.32, py, BEAM_Z - BEAM_H - 0.02),
                  (px, py, BEAM_Z - BEAM_H - 0.34)], 0.055, bm_, seg=6)
    obs.append(b.finish(c, bevel=0.01))
    return obs


# ------------------------------------------------------------------- hearth

def flames(m, cx, cy, base_z, rx, ry, n=26, hmin=0.16, hmax=0.55, seed=0):
    """A low RAGGED MASS of flame, not a bouquet of tidy cones.

    Kit lesson 21: stacked emissive cones ADD, so 3-5 of them lie along any one
    view ray and their emission sums; the per-cone strength is tuned for the
    mass (see mat_k_fire), and the mass is kept LOW and WIDE so it reads as a
    cooking fire someone is actually working over rather than as a bonfire.
    """
    fm = M("mat_k_fire")
    rr = random.Random(seed)
    for i in range(n):
        a = rr.uniform(0, 2 * math.pi)
        t = math.sqrt(rr.random())
        x = cx + math.cos(a) * rx * t
        y = cy + math.sin(a) * ry * t
        h = hmax - (hmax - hmin) * t * rr.uniform(0.6, 1.15)
        r = rr.uniform(0.030, 0.062) * (1.25 - 0.5 * t)
        lean = rr.uniform(-0.16, 0.16)
        # two-segment flame: a fat root and a thin licking tip, so the
        # silhouette is ragged instead of triangular
        m.cyl((x, y, base_z + h * 0.28), r, h * 0.56, fm, seg=5,
              rot=(lean * 0.4, lean, rr.uniform(0, 3)), r2=r * 0.52)
        m.cyl((x + lean * 0.10, y + lean * 0.06, base_z + h * 0.74), r * 0.50,
              h * 0.50, fm, seg=5,
              rot=(lean * 0.9, lean * 1.4, rr.uniform(0, 3)), r2=0.004)


def emberbed(m, cx, cy, base_z, rx, ry, n=34, seed=0):
    """The hot bed the flames stand on. Without it the flames read as floating
    paper triangles (kit lesson 20)."""
    e1, e2 = M("mat_k_ember"), M("mat_k_ember_b")
    ash = M("mat_k_soot")
    rr = random.Random(seed)
    for i in range(n):
        a = rr.uniform(0, 2 * math.pi)
        t = math.sqrt(rr.random())
        x, y = cx + math.cos(a) * rx * t, cy + math.sin(a) * ry * t
        r = rr.uniform(0.028, 0.058)
        m.sphere((x, y, base_z + r * 0.35), r,
                 e1 if t < 0.55 else (e2 if t < 0.85 else ash),
                 seg=6, rings=4, scale=(1.0, 1.0, 0.52))


def build_hearth(c):
    """THE VALUE LEADER. A river-stone cooking hearth: a wide low fire on a
    raised bed, an iron crane swinging a cauldron over it, a spit, and the fire
    irons and split wood a cook keeps within reach."""
    m = KMesh("hearth")
    st, stb = M("mat_k_stone"), M("mat_k_stone_b")
    soot, sootb = M("mat_k_soot"), M("mat_k_soot_b")
    bm_, ir = M("mat_k_beam"), M("mat_k_iron")

    yc = (OPEN_Y0 + OPEN_Y1) / 2
    hy0, hy1 = HRTH_Y0, HRTH_Y1

    # ---- the breast, built as courses so it is masonry and not a slab -----
    z = 0.0
    row = 0
    while z < MANTEL_Z + 0.02:
        hgt = R.uniform(0.13, 0.20)
        y = hy0 - 0.05
        k = 0
        while y < hy1 + 0.05:
            w = R.uniform(0.26, 0.44)
            # leave the fire opening void
            if not (OPEN_Y0 - 0.02 < y + w / 2 < OPEN_Y1 + 0.02 and z < OPEN_Z):
                d = R.uniform(0.0, 0.022)
                m.box((HRTH_XF - 0.54 + d * 0.5, y + w / 2, z + hgt / 2),
                      (0.54 - d * 0.5, w / 2 - 0.012, hgt / 2 - 0.010),
                      st if (row + k) % 3 else stb,
                      rot=(R.uniform(-0.006, 0.006), 0, 0))
            y += w
            k += 1
        z += hgt
        row += 1

    # cheeks either side of the opening get an extra half-depth pier so the
    # opening has a REVEAL. Kept shallow: kit lesson 20 -- a deep pier eats the
    # ember bed and all that reaches the lens is mid-flame.
    for oy in (OPEN_Y0, OPEN_Y1):
        s = -1 if oy == OPEN_Y0 else 1
        m.box((HRTH_XF - 0.09, oy - s * 0.075, OPEN_Z / 2),
              (0.09, 0.075, OPEN_Z / 2), stb)

    # sooted firebox: back, cheeks and throat. GENUINELY DARK -- it is the
    # blackness behind the fire, not the fire's own brightness, that makes the
    # flames the brightest thing in frame under AgX.
    m.box((-HW + 0.07, yc, OPEN_Z / 2 + 0.10),
          (0.07, (OPEN_Y1 - OPEN_Y0) / 2, OPEN_Z / 2 + 0.10), sootb)
    for oy in (OPEN_Y0, OPEN_Y1):
        s = 1 if oy == OPEN_Y0 else -1
        m.box((HRTH_XF - 0.60, oy + s * 0.045, OPEN_Z / 2 + 0.08),
              (0.50, 0.045, OPEN_Z / 2 + 0.08), soot)
    # sloping throat above the opening, drawing back to the flue
    m.box((HRTH_XF - 0.60, yc, OPEN_Z + 0.10), (0.50, (OPEN_Y1 - OPEN_Y0) / 2, 0.05),
          sootb, rot=(0, 0.30, 0))
    # raised fire bed (stone hob) -- the fire is not on the floor
    m.box((HRTH_XF - 0.52, yc, 0.075), (0.50, (OPEN_Y1 - OPEN_Y0) / 2 - 0.03, 0.075),
          stb)

    # ---- lintel + mantel -------------------------------------------------
    m.box((HRTH_XF - 0.28, yc, OPEN_Z + 0.075),
          (0.30, (OPEN_Y1 - OPEN_Y0) / 2 + 0.14, 0.075), bm_)   # oak bressumer
    m.box((HRTH_XF - 0.30, yc, MANTEL_Z),
          (0.36, (OPEN_Y1 - OPEN_Y0) / 2 + 0.26, 0.055), bm_)   # mantel shelf
    for k in range(6):                                          # iron straps
        yy = OPEN_Y0 + (OPEN_Y1 - OPEN_Y0) * (k + 0.5) / 6
        m.box((HRTH_XF - 0.03, yy, OPEN_Z + 0.075), (0.020, 0.030, 0.078), ir)

    # ---- chimney breast tapering up to the beams -------------------------
    z = MANTEL_Z + 0.06
    row = 0
    while z < WH - 0.05:
        hgt = R.uniform(0.14, 0.20)
        t = (z - MANTEL_Z) / (WH - MANTEL_Z)
        yy0 = OPEN_Y0 - 0.30 + 0.34 * t
        yy1 = OPEN_Y1 + 0.30 - 0.34 * t
        y = yy0
        k = 0
        while y < yy1:
            w = min(R.uniform(0.26, 0.44), yy1 - y)
            depth = 0.50 - 0.16 * t
            m.box((HRTH_XF + 0.02 - depth, y + w / 2, z + hgt / 2),
                  (depth, w / 2 - 0.012, hgt / 2 - 0.010),
                  st if (row + k) % 3 else stb,
                  rot=(R.uniform(-0.006, 0.006), 0, 0))
            y += w
            k += 1
        z += hgt
        row += 1

    ob = m.finish(c, bevel=0.010, seg=1)

    # ---- the fire itself, as its own object so the emission is isolated ---
    f = KMesh("hearth_fire")
    # v1's fire was a small bright scribble in a big grey hole and the brick
    # range beat it outright. A COOKING fire is wide and low -- it fills the
    # width of the bed so the whole opening glows, rather than standing up in
    # the middle of it like a campfire.
    emberbed(f, FIRE_X, FIRE_Y, 0.155, 0.34, 0.72, n=54, seed=7)
    flames(f, FIRE_X, FIRE_Y, 0.185, 0.30, 0.66, n=44, hmin=0.13, hmax=0.44, seed=11)
    # burning logs laid across the bed, half consumed
    for (yy, ln, rr_) in ((1.42, 0.52, 0.055), (1.86, 0.60, 0.062), (2.24, 0.44, 0.048)):
        f.cyl((FIRE_X + R.uniform(-0.05, 0.05), yy, 0.20), rr_, ln,
              M("mat_k_soot"), seg=7, rot=(math.pi / 2, 0, R.uniform(-0.12, 0.12)))
    fire_ob = f.finish(c, bevel=0.004, seg=1)

    return ob, fire_ob


def build_hearth_kit(c, kit):
    """Everything that makes it a COOKING fire rather than a parlour fire:
    the crane, the cauldron over the flames, the spit with supper on it, the
    fire irons, the trivet, the split wood."""
    m = KMesh("hearth_kit")
    ir, irb = M("mat_k_iron"), M("mat_k_iron_b")
    cu, cub = M("mat_k_copper"), M("mat_k_copper_b")
    bm_ = M("mat_k_beam")
    yc = (OPEN_Y0 + OPEN_Y1) / 2

    # ---- the crane: an iron arm hinged on the back cheek, swung OUT into
    # the opening so the cauldron hangs over the fire and the camera sees the
    # whole assembly instead of the pintle
    piv = (HRTH_XF - 0.14, OPEN_Y1 - 0.10, 0.0)
    m.cyl((piv[0], piv[1], (OPEN_Z - 0.10) / 2), 0.030, OPEN_Z - 0.10, ir, seg=8)
    arm_end = (FIRE_X - 0.02, FIRE_Y + 0.10, OPEN_Z - 0.20)
    m.strand([(piv[0], piv[1], OPEN_Z - 0.20), arm_end], 0.026, ir, seg=6)
    m.strand([(piv[0], piv[1], OPEN_Z - 0.62),
              (arm_end[0] * 0.5 + piv[0] * 0.5, arm_end[1] * 0.5 + piv[1] * 0.5,
               OPEN_Z - 0.22)], 0.019, ir, seg=6)      # diagonal brace

    # pot hook + chain
    hook_top = (arm_end[0], arm_end[1], arm_end[2] - 0.02)
    m.strand([hook_top, (arm_end[0], arm_end[1], 0.86)], 0.014, ir, seg=6)
    for k in range(4):                                  # ratchet teeth
        m.box((arm_end[0] + 0.028, arm_end[1], 0.98 + k * 0.075),
              (0.026, 0.010, 0.010), ir)

    # THE CAULDRON: bellied, sooted outside, a bright copper rim
    cz = 0.62
    m.lathe((arm_end[0], arm_end[1], cz),
            [(0.0, 0.0), (0.145, 0.015), (0.215, 0.085), (0.232, 0.175),
             (0.205, 0.245), (0.196, 0.262), (0.206, 0.268)],
            M("mat_k_soot"), seg=16, lumpy=0.03, seed=3.1)
    m.ring((arm_end[0], arm_end[1], cz + 0.262), 0.202, 0.014, cub)
    m.ring((arm_end[0], arm_end[1], cz + 0.30), 0.21, 0.013, ir, axis="Y", seg=9)
    # what is in it
    m.cyl((arm_end[0], arm_end[1], cz + 0.238), 0.188, 0.012, M("mat_k_broth"), seg=16)
    # legs
    for k in range(3):
        a = k * 2.094 + 0.4
        m.strand([(arm_end[0] + 0.15 * math.cos(a), arm_end[1] + 0.15 * math.sin(a), cz + 0.03),
                  (arm_end[0] + 0.18 * math.cos(a), arm_end[1] + 0.18 * math.sin(a), cz - 0.09)],
                 0.017, ir, seg=5)

    # ---- the SPIT: fire dogs either side, a square bar across the opening,
    # a fish and a fowl threaded on it, dripping into a pan
    # SPIT HEIGHT is a visibility decision, not a taste one. At z=0.46 the
    # spitted meat sat exactly on the camera's sightline into the firebox --
    # the ray_cast probe hit the roasting fish instead of the ember bed from
    # three of three angles, and the fire lost its glowing base. Raised to
    # 0.68 the sightline passes UNDER the spit, and the meat now silhouettes
    # against the flames instead of hiding them, which is the better picture
    # anyway. The meat is also kept in the FAR half so the near half of the
    # bed is completely open to the lens.
    SPIT_Z = 0.68
    for oy in (OPEN_Y0 + 0.22, OPEN_Y1 - 0.22):
        m.box((HRTH_XF - 0.30, oy, 0.16), (0.26, 0.030, 0.026), ir)     # foot
        m.box((HRTH_XF - 0.16, oy, SPIT_Z / 2 + 0.07),
              (0.030, 0.030, SPIT_Z / 2 - 0.03), ir)                    # upright
        for k in range(3):
            m.box((HRTH_XF - 0.16, oy, SPIT_Z - 0.20 + k * 0.085),
                  (0.048, 0.032, 0.012), ir)
    m.box((HRTH_XF - 0.16, yc, SPIT_Z),
          (0.022, (OPEN_Y1 - OPEN_Y0) / 2 + 0.16, 0.022), ir, rot=(0, 0, 0.02))
    m.box((HRTH_XF - 0.16, OPEN_Y0 - 0.34, SPIT_Z), (0.020, 0.11, 0.020), ir)
    m.box((HRTH_XF - 0.16, OPEN_Y0 - 0.44, SPIT_Z - 0.06), (0.018, 0.018, 0.075), bm_)
    # a fish and a bird threaded on the spit, both in the far half
    m.sphere((HRTH_XF - 0.16, yc + 0.42, SPIT_Z), 0.110, M("mat_k_fishskin"),
             seg=10, rings=6, scale=(0.55, 1.55, 0.85))
    m.sphere((HRTH_XF - 0.16, yc + 0.90, SPIT_Z + 0.01), 0.118, M("mat_k_bread"),
             seg=10, rings=6, scale=(0.72, 1.25, 0.88))
    # dripping pan under the spit
    # ... and its dripping pan, kept SMALL and pushed to the near cheek: the
    # first pass laid a 0.5u dish straight over the ember bed and the fire lost
    # its glowing base (kit lesson 20 again, by a different route).
    m.lathe((HRTH_XF - 0.24, OPEN_Y0 + 0.42, 0.155),
            [(0.0, 0.0), (0.12, 0.006), (0.145, 0.042), (0.150, 0.048)],
            M("mat_k_iron_b"), seg=12, aspect=(0.70, 1.30))

    # ---- fire irons leaning on the cheek + a trivet ----------------------
    for k, (dy, ln, tip) in enumerate(((-0.10, 1.05, 0.016), (0.02, 0.98, 0.020),
                                       (0.14, 1.12, 0.014))):
        bx = HRTH_XF - 0.02
        m.strand([(bx + 0.14, OPEN_Y0 - 0.42 + dy, 0.02),
                  (bx - 0.10, OPEN_Y0 - 0.34 + dy, ln)], tip, irb, seg=6)
    m.ring((HRTH_XF - 0.34, OPEN_Y0 - 0.46, 0.24), 0.13, 0.014, ir)
    for k in range(3):
        a = k * 2.094
        m.strand([(HRTH_XF - 0.34 + 0.12 * math.cos(a), OPEN_Y0 - 0.46 + 0.12 * math.sin(a), 0.24),
                  (HRTH_XF - 0.34 + 0.13 * math.cos(a), OPEN_Y0 - 0.46 + 0.13 * math.sin(a), 0.005)],
                 0.012, ir, seg=4)

    # ---- split wood stacked against the breast, end-on -------------------
    for row in range(4):
        for k in range(7):
            if row == 3 and k > 4:
                continue
            x = HRTH_XF + 0.14 + R.uniform(-0.02, 0.02)
            y = OPEN_Y1 + 0.24 + k * 0.115 + (0.055 if row % 2 else 0)
            if y > IY - 0.10:
                continue
            z = 0.055 + row * 0.105
            m.cyl((x, y, z), R.uniform(0.046, 0.060), R.uniform(0.34, 0.46),
                  bm_ if k % 2 else M("mat_k_shelf"), seg=7,
                  rot=(0, math.pi / 2, R.uniform(-0.05, 0.05)))
    # kindling basket
    m.lathe((HRTH_XF - 0.05, OPEN_Y0 - 0.86, 0.0),
            [(0.0, 0.0), (0.17, 0.01), (0.20, 0.14), (0.225, 0.28), (0.218, 0.30)],
            M("mat_k_straw"), seg=13, lumpy=0.05, seed=1.7)
    for k in range(9):
        a = R.uniform(0, 6.28)
        m.strand([(HRTH_XF - 0.05 + 0.10 * math.cos(a), OPEN_Y0 - 0.86 + 0.10 * math.sin(a), 0.24),
                  (HRTH_XF - 0.05 + 0.19 * math.cos(a), OPEN_Y0 - 0.86 + 0.19 * math.sin(a),
                   0.30 + R.uniform(0.04, 0.20))], 0.011, bm_, seg=4)

    # ---- the mantel shelf: the cook's own line of ware -------------------
    shelf_z = MANTEL_Z + 0.055
    mz = shelf_z
    pots = [(0.22, 0.105, "mat_k_crock"), (0.62, 0.088, "mat_k_ceramic_gn"),
            (0.92, 0.115, "mat_k_ceramic_ox"), (1.30, 0.078, "mat_k_ceramic_cr"),
            (1.66, 0.098, "mat_k_crock"), (2.02, 0.082, "mat_k_ceramic_bl")]
    for (dy, r, mm) in pots:
        yy = OPEN_Y0 - 0.20 + dy
        h = r * R.uniform(1.5, 2.2)
        m.lathe((HRTH_XF - 0.30, yy, mz),
                [(0.0, 0.0), (r * 0.78, 0.008), (r, h * 0.35), (r * 0.94, h * 0.80),
                 (r * 0.70, h), (r * 0.74, h + 0.012)],
                M(mm), seg=12, lumpy=0.03, seed=dy * 3)
    # a big salt box and a rushlight holder
    m.box((HRTH_XF - 0.30, OPEN_Y1 + 0.18, mz + 0.10), (0.11, 0.10, 0.10),
          M("mat_k_shelf"))
    m.box((HRTH_XF - 0.30, OPEN_Y1 + 0.18, mz + 0.215), (0.115, 0.105, 0.016),
          M("mat_k_shelf_b"), rot=(0.16, 0, 0))
    return m.finish(c, bevel=0.006, seg=1)


# -------------------------------------------------------- range + bread oven

def build_range(c):
    """The brick range and the domed BREAD OVEN in the back-left corner.

    Fired brick, not river stone: two masonry masses meeting in one corner
    will read as a single undifferentiated lump unless they differ in colour
    and in course size, so the hearth is big grey rubble and this is small red
    brick. The oven mouth is a second, smaller warm aperture -- it gives the
    kitchen end two glows at different heights, which is what stops the value
    leader being one flat blob.
    """
    m = KMesh("range")
    br, brb = M("mat_k_brick"), M("mat_k_brick_b")
    st = M("mat_k_stone_b")
    soot, ir = M("mat_k_soot"), M("mat_k_iron")

    ARCH_X, ARCH_W, ARCH_Z = -3.00, 0.66, 0.34    # log store / ash arch
    OV_CX = (OVEN_X0 + OVEN_X1) / 2

    # ---- brick base, laid in courses with the two voids left out ---------
    z = 0.0
    row = 0
    while z < RNG_H - 0.05:
        hgt = R.uniform(0.085, 0.115)
        x = RNG_X0 - 0.02
        k = 0
        while x < RNG_X1 + 0.02:
            w = R.uniform(0.19, 0.27)
            cx = x + w / 2
            void = (abs(cx - ARCH_X) < ARCH_W / 2 + 0.02 and z < ARCH_Z + 0.30)
            if not void:
                m.box((cx, (RNG_YF + IY) / 2 + 0.02, z + hgt / 2),
                      (w / 2 - 0.010, (IY - RNG_YF) / 2, hgt / 2 - 0.008),
                      br if (row + k) % 3 else brb,
                      rot=(0, R.uniform(-0.005, 0.005), 0))
            x += w
            k += 1
        z += hgt
        row += 1
    m.arch((ARCH_X, RNG_YF - 0.01, 0.0), ARCH_W, ARCH_Z + 0.30, 0.055,
           st, axis="y", seg=8)
    # sooted ash pit BEHIND the arch. It has to start behind the coals: the
    # first pass centred it on them and the whole fire was inside a solid box.
    m.box((ARCH_X, RNG_YF + 0.60, 0.24), (ARCH_W / 2, 0.30, 0.26), soot)

    # ---- range TOP: a heavy iron plate over the left half ----------------
    m.box(((RNG_X0 + OVEN_X0) / 2 - 0.02, (RNG_YF + IY) / 2 + 0.02, RNG_H - 0.028),
          ((OVEN_X0 - RNG_X0) / 2 + 0.04, (IY - RNG_YF) / 2 + 0.03, 0.028),
          M("mat_k_iron_b"))
    # a brick lip round it so the plate is set INTO the masonry
    for sx in (RNG_X0 - 0.01, OVEN_X0 + 0.06):
        m.box((sx, (RNG_YF + IY) / 2 + 0.02, RNG_H - 0.012),
              (0.055, (IY - RNG_YF) / 2 + 0.03, 0.042), brb)
    m.box(((RNG_X0 + OVEN_X0) / 2, RNG_YF - 0.015, RNG_H - 0.012),
          ((OVEN_X0 - RNG_X0) / 2 + 0.06, 0.042, 0.042), br)
    # two pot holes in the plate, with rings
    for hx in (-3.14, -2.72):
        m.ring((hx, RNG_YF + 0.44, RNG_H + 0.004), 0.145, 0.014, ir)
        m.ring((hx, RNG_YF + 0.44, RNG_H + 0.004), 0.105, 0.012, ir)

    # ---- the domed BREAD OVEN sitting on the base ------------------------
    ov_w = (OVEN_X1 - OVEN_X0) / 2
    z = RNG_H - 0.03
    row = 0
    while z < OVEN_TOP:
        hgt = R.uniform(0.085, 0.115)
        t = (z - RNG_H) / (OVEN_TOP - RNG_H)
        # a dome: the courses corbel in as they rise
        shrink = 0.16 * t * t + 0.10 * t
        x = OVEN_X0 + shrink - 0.02
        k = 0
        while x < OVEN_X1 - shrink + 0.02:
            w = min(R.uniform(0.17, 0.24), OVEN_X1 - shrink + 0.02 - x)
            cx = x + w / 2
            mouth = (abs(cx - OV_CX) < 0.34 and
                     OVEN_MZ - 0.30 < z + hgt / 2 < OVEN_MZ + 0.30)
            if not mouth:
                d = (IY - RNG_YF) / 2 - shrink * 0.55
                m.box((cx, (RNG_YF + IY) / 2 + shrink * 0.55 + 0.02, z + hgt / 2),
                      (w / 2 - 0.010, d, hgt / 2 - 0.008),
                      br if (row + k) % 3 else brb,
                      rot=(0, R.uniform(-0.005, 0.005), 0))
            x += w
            k += 1
        z += hgt
        row += 1
    # the mouth: a stone arch with a sooted throat behind it
    m.arch((OV_CX, RNG_YF - 0.02, OVEN_MZ - 0.28), 0.62, 0.56, 0.06, st,
           axis="y", seg=9)
    m.box((OV_CX, RNG_YF + 0.72, OVEN_MZ), (0.34, 0.26, 0.30), soot)
    m.box((OV_CX, RNG_YF + 0.06, OVEN_MZ - 0.30), (0.34, 0.10, 0.022), st)   # sill

    # flue: a brick stack off the dome crown, up past the beams
    m.box((OV_CX + 0.12, IY - 0.30, (OVEN_TOP + WH) / 2),
          (0.24, 0.24, (WH - OVEN_TOP) / 2 + 0.06), brb)

    ob = m.finish(c, bevel=0.008, seg=1)

    # ---- what is IN the oven and ON the range (separate, emissive) -------
    f = KMesh("range_fire")
    emberbed(f, ARCH_X, RNG_YF + 0.22, 0.045, 0.24, 0.12, n=16, seed=21)
    flames(f, ARCH_X, RNG_YF + 0.22, 0.065, 0.16, 0.08, n=9, hmin=0.06,
           hmax=0.19, seed=23)
    # the oven floor glowing, with loaves baking on it
    fo = M("mat_k_fire_oven")
    f.box((OV_CX, RNG_YF + 0.30, OVEN_MZ - 0.26), (0.28, 0.22, 0.012), fo)
    emberbed(f, OV_CX + 0.20, RNG_YF + 0.26, OVEN_MZ - 0.25, 0.09, 0.09,
             n=10, seed=27)
    for k, dx in enumerate((-0.16, 0.06)):
        f.sphere((OV_CX + dx, RNG_YF + 0.34, OVEN_MZ - 0.185), 0.075,
                 M("mat_k_dough"), seg=9, rings=5, scale=(0.95, 0.66, 0.50))
    return ob, f.finish(c, bevel=0.004, seg=1)


def build_range_props(c):
    """Pots working on the range top, the peel, the loaves, the flour."""
    m = KMesh("range_props")
    ir = M("mat_k_iron")
    OV_CX = (OVEN_X0 + OVEN_X1) / 2

    # a big stew pot on the back hole -- this is what the steam rises from
    px, py = -3.14, RNG_YF + 0.44
    m.lathe((px, py, RNG_H - 0.02),
            [(0.0, 0.0), (0.135, 0.012), (0.185, 0.075), (0.196, 0.180),
             (0.182, 0.245), (0.176, 0.258)],
            M("mat_k_soot"), seg=15, lumpy=0.025, seed=5.2)
    m.ring((px, py, RNG_H + 0.238), 0.180, 0.013, M("mat_k_copper_b"))
    # lid, pushed askew and half off -- steam has to come from SOMEWHERE
    m.lathe((px + 0.055, py - 0.02, RNG_H + 0.240),
            [(0.170, 0.0), (0.150, 0.030), (0.075, 0.052), (0.022, 0.058),
             (0.020, 0.075), (0.0, 0.078)],
            M("mat_k_iron_b"), seg=14, rot=0.2)
    m.cyl((px + 0.10, py + 0.30, RNG_H + 0.24), 0.170, 0.014,
          M("mat_k_broth"), seg=15)

    # a copper pan sizzling on the front hole
    qx, qy = -2.72, RNG_YF + 0.44
    m.lathe((qx, qy, RNG_H - 0.01),
            [(0.0, 0.0), (0.115, 0.006), (0.165, 0.050), (0.172, 0.082),
             (0.170, 0.090)],
            M("mat_k_copper_c"), seg=15)
    m.cyl((qx, qy, RNG_H + 0.056), 0.150, 0.010, M("mat_k_broth_b"), seg=14)
    # fish frying in it
    for k, (dx, dy) in enumerate(((-0.05, 0.03), (0.04, -0.04), (0.01, 0.07))):
        m.sphere((qx + dx, qy + dy, RNG_H + 0.070), 0.062, M("mat_k_fishflesh"),
                 seg=9, rings=5, scale=(0.55, 1.5, 0.26),
                 rot=(0, 0, R.uniform(-0.6, 0.6)))
    m.strand([(qx + 0.16, qy - 0.05, RNG_H + 0.075),
              (qx + 0.60, qy - 0.30, RNG_H + 0.115)], 0.016, ir, seg=5)  # handle

    # the PEEL leaning against the oven -- the long-handled bread shovel
    m.box((OVEN_X1 + 0.16, RNG_YF - 0.26, 0.98), (0.135, 0.012, 0.175),
          M("mat_k_shelf"), rot=(0.20, 0, 0))
    m.strand([(OVEN_X1 + 0.16, RNG_YF - 0.30, 1.14),
              (OVEN_X1 + 0.22, RNG_YF - 0.52, 2.02)], 0.020, M("mat_k_beam"), seg=6)

    # loaves cooling on the oven sill and on a rack
    for k, dx in enumerate((-0.20, 0.02, 0.24)):
        m.sphere((OV_CX + dx, RNG_YF + 0.02, OVEN_MZ - 0.235), 0.088,
                 M("mat_k_bread"), seg=10, rings=6, scale=(0.85, 0.70, 0.52),
                 rot=(0, 0, R.uniform(-0.4, 0.4)))
    # a rack of loaves on the range brick lip
    for k in range(4):
        m.sphere((OVEN_X0 - 0.10 - k * 0.005, RNG_YF + 0.20 + k * 0.02,
                  RNG_H + 0.075 + k * 0.085), 0.082, M("mat_k_bread"),
                 seg=9, rings=5, scale=(0.90, 0.66, 0.48),
                 rot=(0, R.uniform(-0.1, 0.1), R.uniform(-0.5, 0.5)))

    # flour sack slumped against the range
    m.lathe((RNG_X1 + 0.24, RNG_YF - 0.20, 0.0),
            [(0.0, 0.0), (0.19, 0.02), (0.215, 0.14), (0.20, 0.30),
             (0.135, 0.42), (0.105, 0.46), (0.0, 0.48)],
            M("mat_k_sack"), seg=13, lumpy=0.10, seed=8.3)
    m.box((RNG_X1 + 0.36, RNG_YF - 0.36, 0.015), (0.20, 0.16, 0.004),
          M("mat_k_dough"), rot=(0, 0, 0.3))     # spilled flour
    return m.finish(c, bevel=0.006, seg=1)


# ---------------------------------------------------------------- prep bench

def fish(m, loc, L, rot=0.0, skin="mat_k_fishskin", tilt=0.0, belly=None):
    """A whole fish: a laterally-flattened body, a wedge head, a forked tail
    and a dorsal card. Kit lesson 25 -- a small prop must be HORIZONTAL to read
    in a side-lit room, so every fish in this scene lies on its side."""
    x, y, z = loc
    sk = M(skin)
    bl = M(belly or "mat_k_fishskin_b")
    e = (0, tilt, rot)
    c, s = math.cos(rot), math.sin(rot)
    m.sphere((x, y, z), L * 0.5, sk, seg=11, rings=6,
             scale=(0.30, 1.0, 0.42), rot=e)
    m.sphere((x - s * L * 0.02, y + c * L * 0.02, z - L * 0.055), L * 0.44, bl,
             seg=10, rings=5, scale=(0.26, 0.88, 0.24), rot=e)      # pale belly
    # head wedge
    hx, hy = x + s * L * 0.44, y - c * L * 0.44
    m.sphere((hx, hy, z + L * 0.015), L * 0.17, sk, seg=9, rings=5,
             scale=(0.72, 1.05, 0.95), rot=e)
    m.sphere((hx + s * L * 0.10 + c * L * 0.055, hy - c * L * 0.10 + s * L * 0.055,
              z + L * 0.055), L * 0.030, M("mat_k_pewter"), seg=6, rings=4)
    # tail + dorsal
    tx, ty = x - s * L * 0.54, y + c * L * 0.54
    m.card((tx, ty, z), (c, s, 0), (0, 0, 1), L * 0.24, L * 0.34, sk,
           curl=L * 0.05, seed=x)
    m.card((x - s * L * 0.05, y + c * L * 0.05, z + L * 0.14), (c, s, 0),
           (0, 0, 1), L * 0.46, L * 0.13, bl, curl=L * 0.03, seed=y)


def build_prep(c):
    """The PREP BENCH: scrubbed pale wood, a fish half filleted on the block,
    the knife that is doing it laid across the board, and the working debris
    that says somebody stepped away thirty seconds ago."""
    m = KMesh("prep")
    pw, sh = M("mat_k_prep"), M("mat_k_shelf")
    g, ox = M("mat_k_green"), M("mat_k_oxblood")
    ir, stl = M("mat_k_iron"), M("mat_k_steel")
    cx = (PRP_X0 + PRP_X1) / 2
    cy = (PRP_Y0 + PRP_Y1) / 2

    # carcase: a painted base with a thick scrubbed top
    m.box((cx, cy, (PRP_H - 0.06) / 2), ((PRP_X1 - PRP_X0) / 2 - 0.03,
          (PRP_Y1 - PRP_Y0) / 2 - 0.02, (PRP_H - 0.06) / 2), g)
    for px in (PRP_X0 + 0.06, PRP_X1 - 0.06, cx):
        m.box((px, PRP_Y0 - 0.005, (PRP_H - 0.06) / 2),
              (0.045, 0.030, (PRP_H - 0.06) / 2), M("mat_k_green_c"))
    m.box((cx, PRP_Y0 - 0.010, PRP_H - 0.10), ((PRP_X1 - PRP_X0) / 2, 0.025, 0.038), ox)
    m.box((cx, cy, PRP_H - 0.028), ((PRP_X1 - PRP_X0) / 2, (PRP_Y1 - PRP_Y0) / 2,
          0.030), pw)

    # open shelf underneath with crocks and a stack of trenchers
    m.box((cx, cy + 0.02, 0.36), ((PRP_X1 - PRP_X0) / 2 - 0.06,
          (PRP_Y1 - PRP_Y0) / 2 - 0.04, 0.018), sh)
    for k, (dx, r, mm) in enumerate(((-1.02, 0.10, "mat_k_crock"),
                                     (-0.74, 0.085, "mat_k_ceramic_b"),
                                     (0.86, 0.105, "mat_k_ceramic_gn"),
                                     (1.16, 0.09, "mat_k_crock"))):
        m.lathe((cx + dx, cy + 0.03, 0.378),
                [(0.0, 0.0), (r * 0.8, 0.008), (r, 0.10), (r * 0.86, 0.18),
                 (r * 0.72, 0.205)], M(mm), seg=11, lumpy=0.03, seed=dx)
    for k in range(6):                                   # stacked trenchers
        m.lathe((cx + 0.18, cy + 0.05, 0.380 + k * 0.021),
                [(0.0, 0.0), (0.115, 0.004), (0.128, 0.016), (0.10, 0.019)],
                M("mat_k_shelf_b"), seg=12, rot=k * 0.3)
    for k in range(3):                                   # baskets
        m.lathe((cx - 0.30 + k * 0.26, cy - 0.02, 0.378),
                [(0.0, 0.0), (0.10, 0.01), (0.125, 0.14), (0.118, 0.155)],
                M("mat_k_straw"), seg=11, lumpy=0.06, seed=k * 2.2)

    # ---- THE CHOPPING BLOCK: raised, so the fish on it clears the hatch --
    bx, by, bz = -0.28, cy - 0.03, PRP_H + 0.002
    m.box((bx, by, bz + 0.048), (0.46, 0.31, 0.048), M("mat_k_shelf"),
          rot=(0, 0, 0.03))
    m.box((bx, by, bz + 0.094), (0.44, 0.29, 0.004), M("mat_k_prep"))
    # the fish being filleted: the body, one fillet lifted off, guts aside
    # A BIG fish. At L=0.62 on a low block this was a 20px smudge behind the
    # hatch counter; it is one of the two props that tell you what this room
    # IS, so it is oversized on purpose and the block is raised to bring it
    # clear of the hatch top in projection.
    fish(m, (bx - 0.08, by + 0.02, bz + 0.150), 0.82, rot=0.30,
         skin="mat_k_fishskin")
    m.sphere((bx + 0.30, by - 0.12, bz + 0.116), 0.25, M("mat_k_fishflesh"),
             seg=10, rings=5, scale=(0.34, 1.05, 0.125), rot=(0, 0, -0.5))
    m.sphere((bx + 0.36, by + 0.16, bz + 0.110), 0.21, M("mat_k_fishflesh_b"),
             seg=10, rings=5, scale=(0.32, 0.95, 0.11), rot=(0, 0, 0.9))
    for k in range(5):                                   # trimmings
        m.sphere((bx + R.uniform(-0.32, 0.32), by + R.uniform(-0.20, 0.20),
                  bz + 0.106), R.uniform(0.020, 0.038), M("mat_k_fishskin_b"),
                 seg=6, rings=4, scale=(1.0, 1.4, 0.35))
    # the filleting knife, laid across the board where it was put down
    m.box((bx + 0.02, by - 0.24, bz + 0.104), (0.125, 0.017, 0.004), stl,
          rot=(0, 0, -0.22))
    m.box((bx + 0.19, by - 0.27, bz + 0.108), (0.058, 0.019, 0.015),
          M("mat_k_leather"), rot=(0, 0, -0.22))

    # ---- knife block + steel, at the right-hand end ----------------------
    kx = PRP_X1 - 0.42
    m.box((kx, cy + 0.06, PRP_H + 0.086), (0.085, 0.10, 0.086), M("mat_k_beam"),
          rot=(0.13, 0, 0.1))
    for k in range(5):
        m.box((kx - 0.055 + k * 0.028, cy + 0.02, PRP_H + 0.235 + k * 0.012),
              (0.009, 0.075, 0.075), stl, rot=(0.13, 0, 0.1))
        m.box((kx - 0.055 + k * 0.028, cy - 0.04, PRP_H + 0.345 + k * 0.016),
              (0.013, 0.016, 0.042), M("mat_k_leather_b"), rot=(0.13, 0, 0.1))
    m.strand([(kx + 0.20, cy + 0.14, PRP_H + 0.02), (kx + 0.26, cy - 0.14, PRP_H + 0.03)],
             0.010, stl, seg=4)                          # sharpening steel

    # ---- a gutting tub, a salt crock, a pile of onions and roots ---------
    tx = PRP_X0 + 0.36
    m.lathe((tx, cy + 0.02, PRP_H + 0.002),
            [(0.0, 0.0), (0.145, 0.006), (0.175, 0.075), (0.185, 0.135),
             (0.178, 0.148)], M("mat_k_iron_b"), seg=14)
    m.cyl((tx, cy + 0.02, PRP_H + 0.120), 0.165, 0.010, M("mat_k_water"), seg=14)
    for k in range(4):
        m.sphere((tx + R.uniform(-0.09, 0.09), cy + 0.02 + R.uniform(-0.09, 0.09),
                  PRP_H + 0.126), R.uniform(0.028, 0.045), M("mat_k_fishskin"),
                 seg=7, rings=4, scale=(0.6, 1.4, 0.5), rot=(0, 0, R.uniform(0, 3)))
    # salt crock with its wooden lid off
    m.lathe((PRP_X0 + 0.72, cy + 0.14, PRP_H + 0.002),
            [(0.0, 0.0), (0.075, 0.008), (0.095, 0.075), (0.088, 0.135),
             (0.092, 0.142)], M("mat_k_crock"), seg=11)
    m.lathe((PRP_X0 + 0.86, cy - 0.14, PRP_H + 0.006),
            [(0.095, 0.0), (0.090, 0.014), (0.028, 0.020), (0.026, 0.040),
             (0.0, 0.042)], M("mat_k_shelf_b"), seg=11, rot=0.4)
    # heaped veg at the far right of the bench
    vx = PRP_X1 - 0.10
    for k in range(9):
        a = R.uniform(0, 6.28)
        rr = R.uniform(0.0, 0.14)
        m.sphere((vx + math.cos(a) * rr, cy - 0.02 + math.sin(a) * rr,
                  PRP_H + 0.045 + (0.05 if k > 5 else 0.0)),
                 R.uniform(0.042, 0.062),
                 M("mat_k_onion" if k % 3 else "mat_k_onion_b"),
                 seg=8, rings=5, scale=(1.0, 1.0, 0.92))
    for k in range(4):                                    # carrots
        m.cyl((vx - 0.26 + k * 0.045, cy + 0.16, PRP_H + 0.048), 0.026, 0.22,
              M("mat_k_carrot"), seg=7,
              rot=(math.pi / 2, 0, R.uniform(-0.5, 0.5)), r2=0.008)
    return m.finish(c, bevel=0.005, seg=1)


def build_panwall(c):
    """The COPPER PAN WALL over the prep bench, plus braided onions and
    garlic. This is the kitchen's jewellery: a rail of bright hammered metal
    that catches the fire and the hatch key and gives the back wall a band of
    high value exactly where the eye travels between the two glows."""
    m = KMesh("panwall")
    ir = M("mat_k_iron")
    rail_z = 2.06
    x0, x1 = PRP_X0 + 0.05, PRP_X1 - 0.05

    # the rail on its brackets
    m.cyl(((x0 + x1) / 2, IY - 0.13, rail_z), 0.018, x1 - x0, ir, seg=8,
          rot=(0, math.pi / 2, 0))
    for bx in (x0 + 0.10, (x0 + x1) / 2, x1 - 0.10):
        m.strand([(bx, IY - 0.02, rail_z + 0.02), (bx, IY - 0.13, rail_z)],
                 0.014, ir, seg=4)
        m.strand([(bx, IY - 0.02, rail_z + 0.24), (bx, IY - 0.13, rail_z + 0.01)],
                 0.011, ir, seg=4)

    pans = [(-0.78, 0.155, 0.055, "mat_k_copper", 0.30),
            (-0.44, 0.125, 0.048, "mat_k_copper_b", 0.24),
            (-0.10, 0.190, 0.070, "mat_k_copper_c", 0.36),
            (0.28, 0.140, 0.052, "mat_k_copper", 0.26),
            (0.62, 0.108, 0.062, "mat_k_tin", 0.22),
            (0.96, 0.172, 0.058, "mat_k_copper_b", 0.32),
            (1.30, 0.130, 0.045, "mat_k_copper_c", 0.24)]
    for (dx, r, depth, mm, drop) in pans:
        px = (x0 + x1) / 2 + dx
        if not (x0 < px < x1):
            continue
        pz = rail_z - drop
        # hook
        m.strand([(px, IY - 0.13, rail_z - 0.015), (px, IY - 0.12, pz + 0.03)],
                 0.008, ir, seg=4)
        # the pan hangs FACE-ON to the room: a disc plus a shallow rim, which
        # is the only orientation that shows the camera a big lit surface
        m.lathe((px, IY - 0.115, pz), [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.012),
                                       (r, depth), (r * 0.94, depth)],
                M(mm), seg=16, aspect=(1.0, 0.22), rot=0.0)
        m.card((px, IY - 0.105, pz), (1, 0, 0), (0, 0, 1), r * 1.86, r * 1.86,
               M(mm), curl=0.014, nu=8, nv=8, seed=dx)
        m.strand([(px, IY - 0.10, pz - r * 0.9), (px + 0.02, IY - 0.10, pz - r * 1.6)],
                 0.013, ir, seg=4)                            # handle

    # ladles, skimmers and a flesh-fork on the second row of hooks
    for k, (dx, ln) in enumerate(((-0.98, 0.34), (1.52, 0.30), (1.70, 0.38))):
        px = (x0 + x1) / 2 + dx
        m.strand([(px, IY - 0.11, rail_z - 0.03), (px, IY - 0.10, rail_z - ln)],
                 0.010, ir, seg=5)
        m.lathe((px, IY - 0.10, rail_z - ln - 0.03),
                [(0.0, 0.0), (0.055, 0.012), (0.062, 0.045), (0.058, 0.050)],
                M("mat_k_iron_b"), seg=10, aspect=(1.0, 0.5))

    # ---- BRAIDED ONIONS + GARLIC hanging at the left end of the rail -----
    for bi, (bx, mm, nb, rad) in enumerate((
            (x0 + 0.02, "mat_k_onion", 11, 0.055),
            (x0 + 0.19, "mat_k_garlic", 13, 0.040),
            (x1 - 0.06, "mat_k_onion_b", 9, 0.052))):
        top = rail_z - 0.02
        m.strand([(bx, IY - 0.13, rail_z), (bx, IY - 0.11, top - 0.10)],
                 0.012, M("mat_k_straw"), seg=4)
        for k in range(nb):
            t = k / max(1, nb - 1)
            a = k * 2.4
            r = rad * (0.55 + 0.45 * math.sin(math.pi * min(1.0, t * 1.4)))
            m.sphere((bx + math.cos(a) * rad * 0.55,
                      IY - 0.11 + math.sin(a) * 0.030,
                      top - 0.13 - t * 0.52), r, M(mm), seg=8, rings=5,
                     scale=(1.0, 0.9, 1.05))
        m.strand([(bx, IY - 0.11, top - 0.12), (bx, IY - 0.10, top - 0.68)],
                 0.010, M("mat_k_straw"), seg=5)
    return m.finish(c, bevel=0.005, seg=1)


# -------------------------------------------------------------- the hatch

def build_hatch(c):
    """THE SERVING HATCH -- second in the value hierarchy, and the thing the
    players actually interact with.

    A post-and-lintel frames it. That frame is doing real compositional work:
    it separates kitchen from dining as a PLANE the eye reads through rather
    than as a wall, it gives the middle of the frame a vertical to hang the
    menu board and two lanterns off, and it stops the back half of the room
    dissolving into one continuous field of brown clutter.
    """
    m = KMesh("hatch")
    ct, g, gb = M("mat_k_counter"), M("mat_k_green"), M("mat_k_green_b")
    ox, sh = M("mat_k_oxblood"), M("mat_k_shelf")
    ir, bm_ = M("mat_k_iron"), M("mat_k_beam")
    cx, cy = (HAT_X0 + HAT_X1) / 2, (HAT_Y0 + HAT_Y1) / 2
    hx, hy = (HAT_X1 - HAT_X0) / 2, (HAT_Y1 - HAT_Y0) / 2

    # ---- the counter itself ----------------------------------------------
    m.box((cx, cy, (HAT_H - 0.07) / 2), (hx - 0.04, hy - 0.03, (HAT_H - 0.07) / 2), g)
    # panelled front facing the diners
    n = 5
    for i in range(n + 1):
        m.box((HAT_X0 + (HAT_X1 - HAT_X0) * i / n, HAT_Y0 - 0.015, (HAT_H - 0.07) / 2),
              (0.048, 0.030, (HAT_H - 0.07) / 2), gb)
    m.box((cx, HAT_Y0 - 0.018, 0.075), (hx, 0.032, 0.075), gb)
    m.box((cx, HAT_Y0 - 0.020, HAT_H - 0.155), (hx, 0.030, 0.042), ox)
    # thick worn top with a nosing that overhangs the front
    m.box((cx, cy - 0.02, HAT_H - 0.035), (hx + 0.045, hy + 0.055, 0.035), ct)
    m.box((cx, HAT_Y0 - 0.075, HAT_H - 0.055), (hx + 0.045, 0.022, 0.020), ct)
    # a brass edge strip where a thousand bowls have been slid across
    m.box((cx, HAT_Y0 - 0.055, HAT_H - 0.005), (hx + 0.030, 0.030, 0.006),
          M("mat_k_brass"))
    # under-counter shelf with stacked bowls and a keg
    m.box((cx, cy + 0.02, 0.38), (hx - 0.08, hy - 0.05, 0.018), sh)
    for k in range(7):
        m.lathe((HAT_X0 + 0.34, cy, 0.398 + k * 0.030),
                [(0.0, 0.0), (0.085, 0.006), (0.098, 0.028), (0.082, 0.032)],
                M("mat_k_ceramic_cr" if k % 2 else "mat_k_ceramic"), seg=12,
                rot=k * 0.4)
    for k in range(6):
        m.lathe((HAT_X0 + 0.62, cy + 0.04, 0.398 + k * 0.026),
                [(0.0, 0.0), (0.080, 0.005), (0.090, 0.024), (0.076, 0.027)],
                M("mat_k_ceramic_b"), seg=12, rot=k * 0.5)

    # ---- the post-and-lintel frame ---------------------------------------
    for px in (HAT_X0 - 0.02, HAT_X1 + 0.02):
        m.box((px, HAT_Y1 - 0.06, (HAT_LINTEL - 0.06) / 2),
              (0.075, 0.075, (HAT_LINTEL - 0.06) / 2), bm_)
        m.box((px, HAT_Y1 - 0.06, 0.10), (0.10, 0.10, 0.10), M("mat_k_green_c"))
        m.box((px, HAT_Y1 - 0.06, HAT_LINTEL - 0.30), (0.098, 0.098, 0.045), gb)
    m.box((cx, HAT_Y1 - 0.06, HAT_LINTEL - 0.02),
          (hx + 0.10, 0.070, 0.070), bm_)
    m.box((cx, HAT_Y1 - 0.06, HAT_LINTEL + 0.062),
          (hx + 0.12, 0.085, 0.020), M("mat_k_green_c"))
    for s, px in ((1, HAT_X0 - 0.02), (-1, HAT_X1 + 0.02)):
        m.strand([(px + s * 0.30, HAT_Y1 - 0.06, HAT_LINTEL - 0.10),
                  (px, HAT_Y1 - 0.06, HAT_LINTEL - 0.40)], 0.048, bm_, seg=6)

    # ---- what is ON the counter -----------------------------------------
    # the soup kettle the cook ladles from: the one the steam comes off
    kx, ky = HAT_X0 + 0.52, cy + 0.02
    m.lathe((kx, ky, HAT_H - 0.002),
            [(0.0, 0.0), (0.145, 0.010), (0.196, 0.075), (0.205, 0.185),
             (0.192, 0.250), (0.186, 0.262)],
            M("mat_k_copper_b"), seg=15, lumpy=0.02, seed=4.4)
    m.ring((kx, ky, HAT_H + 0.242), 0.190, 0.013, M("mat_k_copper_c"))
    m.cyl((kx, ky, HAT_H + 0.238), 0.180, 0.010, M("mat_k_broth"), seg=15)
    m.ring((kx, ky, HAT_H + 0.30), 0.20, 0.012, ir, axis="Y", seg=9)
    # the ladle stood in it
    m.strand([(kx + 0.06, ky + 0.02, HAT_H + 0.22),
              (kx + 0.20, ky - 0.10, HAT_H + 0.46)], 0.013, ir, seg=5)
    m.lathe((kx + 0.02, ky + 0.06, HAT_H + 0.20),
            [(0.0, 0.0), (0.048, 0.010), (0.055, 0.038), (0.052, 0.042)],
            M("mat_k_iron_b"), seg=10)

    # bowls waiting to go out, one already filled
    for k, (dx, dy, fill) in enumerate(((0.92, 0.06, True), (1.16, -0.06, True),
                                        (1.42, 0.08, False))):
        bx, by = HAT_X0 + dx, cy + dy
        m.lathe((bx, by, HAT_H - 0.002),
                [(0.0, 0.0), (0.075, 0.006), (0.105, 0.050), (0.112, 0.072),
                 (0.104, 0.078)], M("mat_k_ceramic_cr"), seg=13)
        if fill:
            m.cyl((bx, by, HAT_H + 0.062), 0.098, 0.010, M("mat_k_broth_b"), seg=12)
            for j in range(3):
                m.sphere((bx + R.uniform(-0.05, 0.05), by + R.uniform(-0.05, 0.05),
                          HAT_H + 0.070), R.uniform(0.014, 0.022),
                         M("mat_k_carrot" if j % 2 else "mat_k_cabbage"),
                         seg=6, rings=4)
        m.box((bx + 0.11, by - 0.09, HAT_H + 0.008), (0.055, 0.010, 0.004),
              M("mat_k_shelf_b"), rot=(0, 0, R.uniform(-0.4, 0.4)))   # spoon
    # a stack of wooden trenchers and a loaf on a board
    for k in range(5):
        m.lathe((HAT_X1 - 0.30, cy + 0.10, HAT_H + 0.001 + k * 0.020),
                [(0.0, 0.0), (0.100, 0.004), (0.113, 0.015), (0.090, 0.018)],
                M("mat_k_shelf_b"), seg=12, rot=k * 0.35)
    m.box((HAT_X1 - 0.62, cy - 0.14, HAT_H + 0.010), (0.16, 0.10, 0.010),
          M("mat_k_shelf"), rot=(0, 0, 0.12))
    m.sphere((HAT_X1 - 0.64, cy - 0.14, HAT_H + 0.062), 0.10, M("mat_k_bread"),
             seg=10, rings=6, scale=(0.95, 0.62, 0.52), rot=(0, 0, 0.12))
    m.box((HAT_X1 - 0.46, cy - 0.20, HAT_H + 0.026), (0.075, 0.012, 0.003),
          M("mat_k_steel"), rot=(0, 0, -0.3))
    # a hand bell and a tally stick, because somebody has to be called
    # (the stools on the DINERS' side are placed in build_dining)
    m.lathe((HAT_X1 - 0.10, cy + 0.16, HAT_H + 0.002),
            [(0.062, 0.0), (0.058, 0.030), (0.040, 0.070), (0.016, 0.084),
             (0.014, 0.108), (0.0, 0.112)], M("mat_k_brass"), seg=12)
    m.box((HAT_X0 + 0.16, HAT_Y0 + 0.10, HAT_H + 0.006), (0.012, 0.14, 0.006),
          M("mat_k_shelf"), rot=(0, 0, 0.4))
    return m.finish(c, bevel=0.006, seg=1)


def build_menuboard(c):
    """The chalk menu, hung off the hatch lintel where a diner would read it.

    It hangs at the RIGHT end of the lintel, clear of the fish on the prep
    block behind: both are in the middle band of the frame, and overlapping
    them would waste the room's two most legible props on each other.
    """
    m = KMesh("menuboard")
    fr, sl = M("mat_k_oxblood_b"), M("mat_k_slate")
    ir = M("mat_k_iron")
    bx, by = 1.72, HAT_Y1 - 0.16
    top, w, h = HAT_LINTEL - 0.10, 0.46, 0.62
    czb = top - 0.10 - h / 2
    for s in (-1, 1):
        m.strand([(bx + s * (w - 0.05), HAT_Y1 - 0.06, HAT_LINTEL - 0.06),
                  (bx + s * (w - 0.07), by, czb + h / 2)], 0.009, ir, seg=5)
    m.box((bx, by + 0.020, czb), (w, 0.018, h), fr, rot=(0.05, 0, 0))
    m.box((bx, by - 0.004, czb + 0.02), (w - 0.06, 0.010, h - 0.075), sl,
          rot=(0.05, 0, 0))
    # a ledge for the chalk, and the chalk
    m.box((bx, by - 0.020, czb - h + 0.055), (w - 0.02, 0.026, 0.018), fr,
          rot=(0.05, 0, 0))
    m.cyl((bx + 0.22, by - 0.038, czb - h + 0.082), 0.012, 0.055, M("mat_k_chalk"),
          seg=7, rot=(0, math.pi / 2, 0.2))
    ob = m.finish(c, bevel=0.005, seg=1)

    ch = M("mat_k_chalk")
    rot = (math.pi / 2 - 0.05, 0, 0)
    textob("menu_l1", "EEL STEW", 0.140, ch, (bx, by - 0.020, czb + 0.31),
           rot, c, extrude=0.004, spacing=0.94)
    textob("menu_l2", "WHAT ELSE?", 0.092, ch, (bx, by - 0.020, czb + 0.14),
           rot, c, extrude=0.004, spacing=0.94)
    textob("menu_l3", "bread  ~  ale", 0.070, ch, (bx, by - 0.020, czb - 0.06),
           rot, c, extrude=0.003, spacing=0.94)
    textob("menu_l4", "no credit", 0.056, ch, (bx, by - 0.020, czb - 0.22),
           rot, c, extrude=0.003, spacing=0.94)
    return ob


def build_dryrack(c):
    """Herb bundles and more braids drying overhead in the kitchen's heat.

    A rack rather than a beam: two thin poles carrying a curtain of small
    ragged shapes. It fills the dead band between the top of the range and the
    ceiling -- which in the first sketch was the emptiest part of the frame --
    without adding another horizontal bar.
    """
    m = KMesh("dryrack")
    bm_, ir = M("mat_k_beam"), M("mat_k_iron")
    x0, x1 = -3.05, 0.30
    for py, pz in ((2.06, 2.36), (2.42, 2.36)):
        m.cyl(((x0 + x1) / 2, py, pz), 0.026, x1 - x0, bm_, seg=8,
              rot=(0, math.pi / 2, 0))
    for hx in (x0 + 0.18, (x0 + x1) / 2, x1 - 0.18):
        for py in (2.06, 2.42):
            m.strand([(hx, py, BEAM_Z - 0.04), (hx, py, 2.36)], 0.010, ir, seg=4)

    herbs = ["mat_k_herb", "mat_k_herb_b", "mat_k_cabbage"]
    n = 17
    for k in range(n):
        t = (k + 0.5) / n
        hx = x0 + 0.12 + (x1 - x0 - 0.24) * t
        py = 2.06 if k % 2 else 2.42
        drop = R.uniform(0.24, 0.52)
        mm = M(herbs[k % 3])
        m.strand([(hx, py, 2.34), (hx, py, 2.34 - 0.05)], 0.008, M("mat_k_straw"), seg=3)
        for j in range(7):
            a = R.uniform(0, 6.28)
            sp = R.uniform(0.02, 0.062)
            m.strand([(hx, py, 2.29),
                      (hx + math.cos(a) * sp, py + math.sin(a) * sp * 0.6,
                       2.29 - drop * R.uniform(0.7, 1.0))],
                     R.uniform(0.012, 0.022), mm, seg=4, r2=0.006)
    # two more onion braids at the ends, longer, to break the even rhythm
    for bx, mm in ((x0 + 0.05, "mat_k_onion"), (x1 - 0.05, "mat_k_garlic")):
        m.strand([(bx, 2.24, 2.36), (bx, 2.24, 2.20)], 0.011, M("mat_k_straw"), seg=3)
        for k in range(12):
            t = k / 11
            a = k * 2.5
            m.sphere((bx + math.cos(a) * 0.048, 2.24 + math.sin(a) * 0.034,
                      2.16 - t * 0.62), R.uniform(0.036, 0.052) *
                     (0.6 + 0.4 * math.sin(math.pi * min(1.0, t * 1.5))),
                     M(mm), seg=8, rings=5)
    return m.finish(c, bevel=0.005, seg=1)


# ------------------------------------------------------------- dining side

def stool(m, x, y, mat, h=STOOL_H, r=0.145, rot=0.0):
    m.lathe((x, y, h - 0.045), [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.020),
                                (r, 0.045), (0.0, 0.045)], mat, seg=12, rot=rot)
    for k in range(3):
        a = rot + k * 2.094
        m.strand([(x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62, h - 0.045),
                  (x + math.cos(a) * r * 0.98, y + math.sin(a) * r * 0.98, 0.0)],
                 0.021, mat, seg=5)
    m.ring((x, y, h * 0.36), r * 0.80, 0.014, mat, seg=8)


def table(m, cx, cy, w, d, mat_top, mat_leg, h=TBL_H, rz=0.0):
    c, s = math.cos(rz), math.sin(rz)
    m.box((cx, cy, h - 0.028), (w / 2, d / 2, 0.028), mat_top, rot=(0, 0, rz))
    m.box((cx, cy, h - 0.086), (w / 2 - 0.10, d / 2 - 0.08, 0.032), mat_leg,
          rot=(0, 0, rz))
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx = (w / 2 - 0.12) * sx
            ly = (d / 2 - 0.10) * sy
            m.box((cx + lx * c - ly * s, cy + lx * s + ly * c, (h - 0.12) / 2),
                  (0.040, 0.040, (h - 0.12) / 2), mat_leg, rot=(0, 0, rz))
    for sy in (-1, 1):
        ly = (d / 2 - 0.10) * sy
        m.box((cx - ly * s, cy + ly * c, 0.155), (w / 2 - 0.12, 0.024, 0.024),
              mat_leg, rot=(0, 0, rz))


def meal(m, cx, cy, z, n=2, seed=0):
    """A meal MID-EATING. Bowls with stew still in them, a spoon left in one,
    a hunk of bread torn not cut, mugs, crumbs. The story is that these people
    got up when the fire needed feeding and will be back."""
    rr = random.Random(seed)
    bowls = M("mat_k_ceramic_cr"), M("mat_k_ceramic"), M("mat_k_ceramic_b")
    for k in range(n):
        a = 2 * math.pi * k / n + rr.uniform(-0.4, 0.4)
        bx = cx + math.cos(a) * rr.uniform(0.20, 0.30)
        by = cy + math.sin(a) * rr.uniform(0.14, 0.22)
        m.lathe((bx, by, z), [(0.0, 0.0), (0.070, 0.006), (0.100, 0.048),
                              (0.107, 0.068), (0.099, 0.074)],
                bowls[k % 3], seg=13, lumpy=0.02, seed=k)
        m.cyl((bx, by, z + 0.058), 0.092, 0.010, M("mat_k_broth_b"), seg=12)
        for j in range(2):
            m.sphere((bx + rr.uniform(-0.045, 0.045), by + rr.uniform(-0.045, 0.045),
                      z + 0.066), rr.uniform(0.012, 0.020),
                     M("mat_k_carrot" if j else "mat_k_cabbage"), seg=6, rings=4)
        # a spoon left standing in the bowl
        m.strand([(bx + 0.02, by + 0.03, z + 0.055),
                  (bx + 0.12, by + 0.13, z + 0.135)], 0.009, M("mat_k_shelf_b"), seg=4)
        # mug
        mx = bx + math.cos(a) * 0.20
        my = by + math.sin(a) * 0.16
        m.lathe((mx, my, z), [(0.0, 0.0), (0.045, 0.004), (0.050, 0.030),
                              (0.049, 0.100), (0.045, 0.104)],
                M("mat_k_crock" if k % 2 else "mat_k_ceramic_gn"), seg=11)
        m.cyl((mx, my, z + 0.088), 0.042, 0.008, M("mat_k_broth"), seg=10)
        m.ring((mx + 0.055, my, z + 0.062), 0.032, 0.009, M("mat_k_crock"), axis="X")
    # torn bread + crumbs in the middle
    m.box((cx, cy, z + 0.008), (0.135, 0.095, 0.008), M("mat_k_shelf"), rot=(0, 0, 0.2))
    m.sphere((cx - 0.02, cy + 0.01, z + 0.058), 0.085, M("mat_k_bread"),
             seg=9, rings=5, scale=(0.90, 0.60, 0.55), rot=(0, 0, 0.2))
    m.sphere((cx + 0.12, cy - 0.07, z + 0.036), 0.045, M("mat_k_bread"),
             seg=7, rings=4, scale=(1.0, 0.7, 0.6), rot=(0, 0, -0.5))
    for k in range(5):
        m.sphere((cx + rr.uniform(-0.28, 0.28), cy + rr.uniform(-0.20, 0.20),
                  z + 0.008), rr.uniform(0.007, 0.013), M("mat_k_bread"),
                 seg=5, rings=3)
    # a candle stub in a dish
    m.lathe((cx + 0.30, cy + 0.22, z), [(0.0, 0.0), (0.055, 0.004), (0.062, 0.014),
                                        (0.050, 0.017)], M("mat_k_pewter"), seg=11)
    m.cyl((cx + 0.30, cy + 0.22, z + 0.058), 0.017, 0.082, M("mat_k_wax"), seg=8,
          r2=0.014)
    m.cone((cx + 0.30, cy + 0.22, z + 0.100), 0.013, 0.048, M("mat_k_candleflame"),
           seg=6)


def build_dining(c, kit):
    """The dining side: two small tables mid-meal, stools, and the bench under
    the window. Deliberately fewer, bigger shapes than the kitchen -- the
    density gradient from cluttered kitchen to sparse dining side is what makes
    the room read as two rooms in one frame."""
    m = KMesh("dining")
    tt, tb = M("mat_k_table"), M("mat_k_table_b")
    lg, lgb = M("mat_k_beam"), M("mat_k_shelf")
    g, ox = M("mat_k_green"), M("mat_k_oxblood")

    # --- table A, front left ---------------------------------------------
    ax, ay = -2.20, -1.05
    table(m, ax, ay, 1.24, 0.86, tt, lg, rz=0.06)
    meal(m, ax, ay, TBL_H + 0.002, n=2, seed=3)
    stool(m, ax - 0.86, ay + 0.10, lgb, rot=0.3)
    stool(m, ax + 0.82, ay - 0.16, lg, rot=1.1)
    stool(m, ax + 0.08, ay - 0.72, lgb, rot=0.7)
    # a coat over the back of the far stool, and a cap on the table
    m.cloth((ax - 0.86, ay + 0.10, STOOL_H + 0.02), (1, 0, 0), (0, -1, 0),
            0.34, 0.42, M("mat_k_leather"), taper=0.7, folds=3, seed=1.2)

    # --- table B, front right ---------------------------------------------
    bx2, by2 = 1.32, -1.62
    table(m, bx2, by2, 1.12, 0.80, tb, lg, rz=-0.10)
    meal(m, bx2, by2, TBL_H + 0.002, n=2, seed=9)
    stool(m, bx2 - 0.78, by2 - 0.10, lg, rot=0.9)
    stool(m, bx2 + 0.74, by2 + 0.14, lgb, rot=0.2)
    # a dog-eared pack and a hat under the table -- somebody is sitting here
    m.lathe((bx2 - 0.42, by2 + 0.40, 0.0), [(0.0, 0.0), (0.16, 0.02), (0.185, 0.13),
                                            (0.150, 0.26), (0.115, 0.30), (0.0, 0.32)],
            M("mat_k_canvas"), seg=12, lumpy=0.09, seed=2.4)

    # --- the WINDOW BENCH -------------------------------------------------
    by0, by1 = -1.70, 0.55
    bxx = IX - 0.26
    m.box((bxx, (by0 + by1) / 2, BENCH_H - 0.026), (0.24, (by1 - by0) / 2, 0.026), tt)
    m.box((bxx + 0.20, (by0 + by1) / 2, BENCH_H + 0.20), (0.030, (by1 - by0) / 2, 0.20), g)
    for yy in (by0 + 0.16, (by0 + by1) / 2, by1 - 0.16):
        m.box((bxx, yy, (BENCH_H - 0.06) / 2), (0.20, 0.038, (BENCH_H - 0.06) / 2), g)
    m.box((bxx, (by0 + by1) / 2, 0.14), (0.16, (by1 - by0) / 2 - 0.10, 0.022), g)
    m.box((bxx - 0.22, (by0 + by1) / 2, BENCH_H - 0.075), (0.024, (by1 - by0) / 2, 0.028), ox)
    # cushions and a folded blanket
    for k, yy in enumerate((by0 + 0.40, by1 - 0.55)):
        m.lathe((bxx - 0.02, yy, BENCH_H), [(0.0, 0.0), (0.17, 0.012), (0.19, 0.055),
                                            (0.15, 0.082), (0.0, 0.090)],
                M("mat_k_linen" if k else "mat_k_rug"), seg=12,
                aspect=(1.05, 1.45), lumpy=0.06, seed=k * 3.3)
    # a bowl and a mug abandoned on the bench, plus a coil of line
    m.lathe((bxx - 0.03, by1 - 0.10, BENCH_H + 0.001),
            [(0.0, 0.0), (0.070, 0.006), (0.098, 0.046), (0.104, 0.066),
             (0.096, 0.072)], M("mat_k_ceramic"), seg=13)
    m.cyl((bxx - 0.03, by1 - 0.10, BENCH_H + 0.058), 0.088, 0.008,
          M("mat_k_broth_b"), seg=12)

    # --- the CENTRE. v1 left a bare plank field roughly a fifth of the frame
    # wide between the hatch and the front edge -- a dead stage in the most
    # valuable part of the picture. It is filled with things that belong on a
    # cookhouse floor and still leave the two-player lane (x 0.15..1.45) open.
    # A rush mat first: one big soft-edged shape does more to break a plank
    # field than six small props, and it catches the window light.
    # A PLAITED mat, woven in strips. The first pass used one round lathe and
    # it read as a dark oval stain on the boards rather than as an object; a
    # rectangle of visible plaiting, paler than the floor, reads instantly.
    mx0, mx1, my0, my1 = -1.42, 0.42, -2.32, -1.34
    m.box(((mx0 + mx1) / 2, (my0 + my1) / 2, 0.006),
          ((mx1 - mx0) / 2, (my1 - my0) / 2, 0.006), M("mat_k_straw"),
          rot=(0, 0, 0.05))
    yy = my0 + 0.05
    k = 0
    while yy < my1:
        w = R.uniform(0.075, 0.115)
        m.box(((mx0 + mx1) / 2, yy + w / 2, 0.013),
              ((mx1 - mx0) / 2 - 0.02, w / 2 - 0.010, 0.006),
              M("mat_k_straw" if k % 2 else "mat_k_burlap"), rot=(0, 0, 0.05))
        yy += w
        k += 1
    for sx in (mx0 + 0.04, mx1 - 0.04):        # bound edges
        m.box((sx, (my0 + my1) / 2, 0.014), (0.035, (my1 - my0) / 2, 0.008),
              M("mat_k_burlap"), rot=(0, 0, 0.05))
    # a water butt with its dipper -- every kitchen has one and it is a tall
    # dark cylinder, which is exactly the silhouette this zone was missing
    wx, wy = -1.05, -2.76
    m.lathe((wx, wy, 0.0), [(0.0, 0.0), (0.30, 0.0), (0.315, 0.04), (0.335, 0.36),
                            (0.325, 0.66), (0.312, 0.70), (0.302, 0.705)],
            M("mat_k_crate"), seg=18, lumpy=0.018, seed=9.4)
    for bz in (0.07, 0.38, 0.66):
        m.ring((wx, wy, bz), 0.322 if bz == 0.38 else 0.300, 0.016, M("mat_k_iron"))
    m.cyl((wx, wy, 0.655), 0.298, 0.014, M("mat_k_water"), seg=17)
    m.lathe((wx - 0.09, wy + 0.10, 0.66), [(0.0, 0.0), (0.070, 0.005),
                                           (0.082, 0.055), (0.076, 0.062)],
            M("mat_k_shelf_b"), seg=11)
    m.strand([(wx - 0.09, wy + 0.10, 0.70), (wx - 0.24, wy + 0.30, 0.98)],
             0.014, M("mat_k_shelf"), seg=5)
    m.lathe((wx + 0.36, wy - 0.20, 0.0), [(0.0, 0.0), (0.135, 0.0), (0.155, 0.24),
                                          (0.148, 0.26)], M("mat_k_crate_b"), seg=13)
    m.ring((wx + 0.36, wy - 0.20, 0.21), 0.152, 0.011, M("mat_k_iron"))
    # spilled straw and sawdust down the lane. The lane must stay walkable,
    # so this is all flat: it breaks a bare plank field without putting a
    # single thing in the players' way.
    for k in range(46):
        sx = R.uniform(0.10, 2.35)
        sy = R.uniform(-3.20, -1.55)
        a = R.uniform(0, 6.28)
        ln = R.uniform(0.06, 0.20)
        m.strand([(sx, sy, 0.006),
                  (sx + math.cos(a) * ln, sy + math.sin(a) * ln * 0.7, 0.006)],
                 R.uniform(0.006, 0.011), M("mat_k_straw"), seg=3)
    for k in range(9):
        m.sphere((R.uniform(0.25, 2.20), R.uniform(-3.10, -1.70), 0.012),
                 R.uniform(0.020, 0.038), M("mat_k_shelf_b"), seg=6, rings=4,
                 scale=(1.0, 0.8, 0.35), rot=(0, 0, R.uniform(0, 3)))
    # a dropped sack and an upset basket at the very bottom edge, cropped by
    # the frame on purpose so the foreground has something in the near plane
    m.lathe((1.62, -3.06, 0.0), [(0.0, 0.0), (0.24, 0.02), (0.270, 0.16),
                                 (0.230, 0.36), (0.150, 0.50), (0.0, 0.54)],
            M("mat_k_sack"), seg=13, lumpy=0.10, seed=11.2)
    m.lathe((2.28, -2.92, 0.0), [(0.0, 0.0), (0.185, 0.01), (0.215, 0.15),
                                 (0.240, 0.30), (0.232, 0.315)],
            M("mat_k_straw"), seg=13, lumpy=0.07, seed=12.4)
    for k in range(7):
        a = R.uniform(0, 6.28)
        m.sphere((2.28 + math.cos(a) * R.uniform(0, 0.16),
                  -2.92 + math.sin(a) * R.uniform(0, 0.16),
                  0.30 + R.uniform(0, 0.05)), R.uniform(0.048, 0.066),
                 M("mat_k_onion" if k % 2 else "mat_k_carrot"), seg=8, rings=5)

    # a stool pulled out of the way and a dropped cloth
    stool(m, 0.30, -1.28, M("mat_k_shelf"), rot=0.6)
    m.cloth((0.26, -1.42, 0.44), (1, 0, 0), (0, -1, 0), 0.30, 0.30,
            M("mat_k_apron"), taper=0.8, folds=3, seed=7.2)
    # split firewood ricked against the hatch, right where the cook drops it
    for row in range(3):
        for k in range(5 - row):
            m.cyl((1.72 + k * 0.115 + row * 0.055, HAT_Y0 - 0.42,
                   0.055 + row * 0.100), R.uniform(0.046, 0.058),
                  R.uniform(0.32, 0.42), M("mat_k_beam") if k % 2 else M("mat_k_shelf"),
                  seg=7, rot=(math.pi / 2, 0, R.uniform(-0.06, 0.06)))

    # --- a little side table by the window with the day's catch tally -----
    m.box((IX - 0.30, by0 - 0.72, 0.60), (0.22, 0.28, 0.022), tb)
    for sx in (-1, 1):
        m.box((IX - 0.30 + sx * 0.16, by0 - 0.72, 0.30), (0.032, 0.24, 0.30), lg)
    m.lathe((IX - 0.34, by0 - 0.72, 0.622),
            [(0.0, 0.0), (0.058, 0.005), (0.066, 0.038), (0.062, 0.115),
             (0.058, 0.120)], M("mat_k_crock"), seg=11)
    return m.finish(c, bevel=0.006, seg=1)


# ------------------------------------------------------- door / delivery end

def build_doorzone(c, kit):
    """The delivery end by the oxblood door: the day's fish still in its
    crates, the BARREL OF EELS, ice-straw, and the wet gear of whoever carried
    them up from the quay."""
    m = KMesh("doorzone")
    cr, crb = M("mat_k_crate"), M("mat_k_crate_b")
    st = M("mat_k_straw")

    # --- fish crates stacked against the right-hand back corner ----------
    crates = [(3.72, 1.72, 0.0, 0.10, True), (3.74, 2.34, 0.0, -0.08, True),
              (3.70, 2.02, 0.40, 0.22, True), (4.10, 1.34, 0.0, 0.30, False)]
    for (cx, cy, cz, rz, open_) in crates:
        w, d, h = 0.36, 0.28, 0.20
        for sx in (-1, 1):
            m.box((cx + sx * w * math.cos(rz), cy + sx * w * math.sin(rz), cz + h),
                  (0.022, d, h), cr, rot=(0, 0, rz))
        for sy in (-1, 1):
            m.box((cx - sy * d * math.sin(rz), cy + sy * d * math.cos(rz), cz + h),
                  (w, 0.022, h), crb, rot=(0, 0, rz))
        m.box((cx, cy, cz + 0.02), (w, d, 0.02), cr, rot=(0, 0, rz))
        if open_:
            # straw bedding + the catch, heaped so it breaks the box line
            m.box((cx, cy, cz + 0.16), (w - 0.03, d - 0.03, 0.05), st, rot=(0, 0, rz))
            for k in range(6):
                fish(m, (cx + R.uniform(-0.24, 0.24), cy + R.uniform(-0.16, 0.16),
                         cz + 0.235 + R.uniform(0, 0.05)), R.uniform(0.26, 0.40),
                     rot=rz + R.uniform(-0.7, 0.7), tilt=R.uniform(-0.2, 0.2),
                     skin="mat_k_fishskin" if k % 2 else "mat_k_fishskin_b")
        else:
            m.box((cx, cy, cz + 0.30), (w, d, 0.022), crb, rot=(0, 0, rz))
            m.lathe((cx - 0.10, cy, cz + 0.32), [(0.0, 0.0), (0.14, 0.01),
                                                 (0.165, 0.12), (0.155, 0.135)],
                    st, seg=11, lumpy=0.07, seed=1.1)

    # --- THE BARREL OF EELS ----------------------------------------------
    ex, ey = 4.02, 0.72
    stv = M("mat_k_crate")
    m.lathe((ex, ey, 0.0),
            [(0.0, 0.0), (0.245, 0.0), (0.255, 0.02), (0.290, 0.24),
             (0.296, 0.42), (0.272, 0.62), (0.262, 0.66), (0.252, 0.665)],
            stv, seg=18, lumpy=0.020, seed=6.1)
    for bz in (0.06, 0.33, 0.60):
        m.ring((ex, ey, bz), 0.292 if bz == 0.33 else 0.262, 0.017, M("mat_k_iron"))
    # brine, then the eels: strands looping through it. Kit lesson: the whole
    # prop works on the coat highlight running along each back -- without it a
    # barrel of black eels is a black hole, which the brief forbids outright.
    m.cyl((ex, ey, 0.615), 0.258, 0.014, M("mat_k_water"), seg=16)
    eel = M("mat_k_eel")
    for k in range(9):
        a0 = R.uniform(0, 6.28)
        rad = R.uniform(0.08, 0.20)
        pts = []
        for j in range(9):
            a = a0 + j * R.uniform(0.55, 0.95)
            rr_ = rad * (0.75 + 0.35 * math.sin(j * 1.3 + k))
            pts.append((ex + math.cos(a) * rr_, ey + math.sin(a) * rr_,
                        0.618 + 0.020 * math.sin(j * 1.9 + k * 0.7)))
        m.strand(pts, R.uniform(0.020, 0.030), eel, seg=5)
    # one eel escaping over the rim -- the joke the menu board sets up
    m.strand([(ex + 0.10, ey - 0.20, 0.640), (ex + 0.20, ey - 0.30, 0.655),
              (ex + 0.28, ey - 0.36, 0.600), (ex + 0.31, ey - 0.42, 0.480),
              (ex + 0.28, ey - 0.50, 0.360), (ex + 0.22, ey - 0.60, 0.300)],
             0.026, eel, seg=6, r2=0.010)

    # --- a lidded brine tub, a sack of salt, and a bundle of nets --------
    m.lathe((3.34, 0.44, 0.0), [(0.0, 0.0), (0.20, 0.0), (0.225, 0.20),
                                (0.212, 0.38), (0.205, 0.40)],
            crb, seg=15, lumpy=0.02, seed=2.9)
    m.lathe((3.34, 0.44, 0.40), [(0.215, 0.0), (0.205, 0.018), (0.06, 0.026),
                                 (0.055, 0.052), (0.0, 0.056)],
            M("mat_k_shelf"), seg=13)
    m.lathe((4.14, 2.86, 0.0), [(0.0, 0.0), (0.18, 0.02), (0.205, 0.16),
                                (0.175, 0.34), (0.120, 0.44), (0.0, 0.46)],
            M("mat_k_sack"), seg=12, lumpy=0.10, seed=4.7)
    # wet oilskin and a hat on the door pegs
    m.box((2.06, IY - 0.05, RAIL_Z + 0.10), (0.030, 0.030, 0.030), M("mat_k_iron"))
    m.cloth((2.06, IY - 0.10, RAIL_Z + 0.06), (1, 0, 0), (0, -1, 0), 0.40, 0.74,
            M("mat_k_leather_b"), taper=0.52, folds=4, seed=0.6)
    m.cloth((2.38, IY - 0.10, RAIL_Z + 0.02), (1, 0, 0), (0, -1, 0), 0.30, 0.50,
            M("mat_k_canvas_b"), taper=0.6, folds=3, seed=2.1)
    # a boot pair drying by the door
    for k, dx in enumerate((-0.10, 0.06)):
        m.lathe((2.62 + dx, 2.62, 0.0), [(0.0, 0.0), (0.075, 0.005), (0.080, 0.10),
                                         (0.072, 0.26), (0.068, 0.30)],
                M("mat_k_leather_b"), seg=10, aspect=(1.0, 0.85))
        m.box((2.62 + dx, 2.50, 0.035), (0.072, 0.10, 0.035), M("mat_k_leather_b"))
    return m.finish(c, bevel=0.005, seg=1)


# ------------------------------------------------------------- foreground

def build_foreground(c, kit):
    """The bottom fifth of the frame is the most valuable real estate in a
    pre-rendered background and the easiest to leave as a dead brown apron.
    Big simple silhouettes, close to the lens, lit from behind by the room."""
    m = KMesh("foreground")
    cr, crb = M("mat_k_crate"), M("mat_k_crate_b")
    sh, bm_ = M("mat_k_shelf"), M("mat_k_beam")

    # --- the scullery corner, front left: a scrubbing tub on a trestle ----
    tx, ty = -3.55, -2.05
    for sx in (-1, 1):
        m.box((tx + sx * 0.42, ty, 0.30), (0.045, 0.24, 0.30), bm_,
              rot=(0, sx * 0.05, 0))
        m.box((tx + sx * 0.42, ty, 0.16), (0.075, 0.26, 0.020), bm_)
    m.box((tx, ty, 0.615), (0.52, 0.30, 0.022), bm_)
    m.lathe((tx, ty, 0.62), [(0.0, 0.0), (0.30, 0.0), (0.335, 0.16),
                             (0.352, 0.30), (0.342, 0.315)],
            crb, seg=17, lumpy=0.02, seed=3.7)
    for bz in (0.70, 0.90):
        m.ring((tx, ty, bz), 0.345 if bz > 0.8 else 0.322, 0.014, M("mat_k_iron"))
    m.cyl((tx, ty, 0.885), 0.330, 0.014, M("mat_k_water"), seg=16)
    for k in range(5):                        # crocks soaking in it
        a = R.uniform(0, 6.28)
        rr_ = R.uniform(0.05, 0.19)
        m.lathe((tx + math.cos(a) * rr_, ty + math.sin(a) * rr_, 0.80),
                [(0.0, 0.0), (0.070, 0.006), (0.092, 0.055), (0.086, 0.100)],
                M("mat_k_ceramic_b" if k % 2 else "mat_k_crock"), seg=10,
                rot=R.uniform(0, 1))
    # brush, cloth over the rim, and a bucket underneath
    m.box((tx + 0.20, ty - 0.30, 0.93), (0.085, 0.045, 0.030), sh, rot=(0.3, 0, 0.3))
    m.cloth((tx - 0.26, ty - 0.24, 0.92), (0.7, -0.7, 0), (0.7, 0.7, 0), 0.30, 0.40,
            M("mat_k_apron"), taper=0.75, folds=3, seed=5.5)
    m.lathe((tx + 0.52, ty - 0.44, 0.0), [(0.0, 0.0), (0.135, 0.0), (0.158, 0.24),
                                          (0.150, 0.26)], crb, seg=13)
    m.ring((tx + 0.52, ty - 0.44, 0.20), 0.156, 0.011, M("mat_k_iron"))

    # --- the front-right: stacked empties, a barrel, a broom -------------
    for (cx, cy, cz, rz) in ((2.90, -2.60, 0.0, 0.18), (2.86, -2.56, 0.42, -0.22),
                             (3.46, -2.20, 0.0, -0.10)):
        w, d, h = 0.34, 0.27, 0.20
        for sx in (-1, 1):
            m.box((cx + sx * w * math.cos(rz), cy + sx * w * math.sin(rz), cz + h),
                  (0.022, d, h), cr, rot=(0, 0, rz))
        for sy in (-1, 1):
            m.box((cx - sy * d * math.sin(rz), cy + sy * d * math.cos(rz), cz + h),
                  (w, 0.022, h), crb, rot=(0, 0, rz))
        m.box((cx, cy, cz + 0.02), (w, d, 0.02), cr, rot=(0, 0, rz))
        m.box((cx, cy, cz + 0.38), (w, d, 0.020), crb, rot=(0, 0, rz))
    # a stack of empty trenchers and a pot on the top crate
    for k in range(6):
        m.lathe((2.86, -2.56, 0.82 + k * 0.021),
                [(0.0, 0.0), (0.105, 0.004), (0.118, 0.016), (0.094, 0.019)],
                M("mat_k_shelf_b"), seg=12, rot=k * 0.4)
    m.lathe((3.46, -2.20, 0.40), [(0.0, 0.0), (0.115, 0.008), (0.150, 0.065),
                                  (0.158, 0.150), (0.146, 0.205), (0.150, 0.212)],
            M("mat_k_soot"), seg=14, lumpy=0.03, seed=7.7)

    # a broom leaning where the wall meets the floor
    m.strand([(3.94, -2.92, 0.02), (3.62, -2.66, 1.42)], 0.020, bm_, seg=6)
    m.lathe((3.96, -2.94, 0.0), [(0.0, 0.0), (0.075, 0.0), (0.085, 0.18),
                                 (0.055, 0.22)], M("mat_k_straw"), seg=10,
            lumpy=0.14, seed=9.1)

    # --- a sack of meal and a heap of roots front-centre-left ------------
    m.lathe((-1.62, -2.72, 0.0), [(0.0, 0.0), (0.22, 0.02), (0.255, 0.18),
                                  (0.225, 0.40), (0.150, 0.54), (0.0, 0.58)],
            M("mat_k_sack"), seg=13, lumpy=0.09, seed=6.6)
    m.lathe((-1.14, -2.86, 0.0), [(0.0, 0.0), (0.20, 0.02), (0.225, 0.15),
                                  (0.180, 0.32), (0.0, 0.38)],
            M("mat_k_burlap"), seg=12, lumpy=0.11, seed=8.8)
    for k in range(11):
        a = R.uniform(0, 6.28)
        rr_ = R.uniform(0.0, 0.26)
        m.sphere((-1.14 + math.cos(a) * rr_, -2.86 + math.sin(a) * rr_ * 0.7,
                  0.36 + R.uniform(0.0, 0.06)), R.uniform(0.048, 0.070),
                 M("mat_k_onion" if k % 3 else "mat_k_onion_b"), seg=8, rings=5)

    # --- the cat, asleep on the warm flags where the fire reaches --------
    # Kit lesson 25: a small prop must be HORIZONTAL to read in a side-lit
    # room. A cat curled on her side gets raked by the firelight and
    # head-body-tail is unmistakable at 25px.
    cxx, cyy = -2.55, 0.62
    fur = M("mat_k_leather")
    m.sphere((cxx, cyy, 0.085), 0.145, fur, seg=11, rings=7,
             scale=(1.25, 0.92, 0.62), rot=(0, 0, 0.5))
    m.sphere((cxx + 0.16, cyy + 0.10, 0.105), 0.072, fur, seg=9, rings=6,
             scale=(1.0, 0.95, 0.92))
    for s in (-1, 1):
        m.cone((cxx + 0.19, cyy + 0.10 + s * 0.045, 0.155), 0.026, 0.048, fur, seg=5)
    m.strand([(cxx - 0.15, cyy - 0.06, 0.055), (cxx - 0.28, cyy + 0.02, 0.045),
              (cxx - 0.34, cyy + 0.14, 0.060)], 0.024, fur, seg=5, r2=0.014)
    return m.finish(c, bevel=0.005, seg=1)


def build_hanging(c, kit):
    """Lanterns and the last of the overhead clutter. Ordinary warm lanterns
    only -- no magical flames anywhere in Dellhollow."""
    obs = []
    lam = kit["kit_lantern_hanging"]
    # two off the hatch lintel: these light the counter the players use
    obs.append(place_lantern(lam, (HAT_X0 + 0.30, HAT_Y1 - 0.06, HAT_LINTEL - 0.30),
                             c, energy=40.0))
    obs.append(place_lantern(lam, (HAT_X1 - 0.34, HAT_Y1 - 0.06, HAT_LINTEL - 0.30),
                             c, energy=36.0))
    # one over each dining table, hung off the beams
    obs.append(place_lantern(lam, (-2.20, 0.28, BEAM_Z - 0.44), c, energy=32.0))
    obs.append(place_lantern(lam, (2.95, -1.62, BEAM_Z - 0.40), c, energy=30.0))
    # one by the door so the entrance is not a hole
    obs.append(place_lantern(lam, (2.20, IY - 0.22, 2.30), c, energy=26.0))

    m = KMesh("hanging")
    ir, bm_ = M("mat_k_iron"), M("mat_k_beam")
    # chains up to the beams so the lanterns are not floating
    for (lx, ly, lz, tz) in ((-2.20, 0.28, BEAM_Z - 0.44, BEAM_Z - 0.04),
                             (2.95, -1.62, BEAM_Z - 0.40, BEAM_Z - 0.04),
                             (2.20, IY - 0.22, 2.30, WH - 0.16)):
        m.strand([(lx, ly, lz + 0.20), (lx, ly, tz)], 0.010, ir, seg=4)
    # a pot rack over the hearth end: three pots on a bracket off the chimney
    for k, (dy, r, mm) in enumerate(((0.35, 0.115, "mat_k_copper"),
                                     (0.78, 0.145, "mat_k_soot"),
                                     (1.18, 0.098, "mat_k_copper_b"))):
        yy = OPEN_Y0 - 0.62 + dy
        m.strand([(HRTH_XF - 0.22, yy, MANTEL_Z + 0.62),
                  (HRTH_XF - 0.22, yy, MANTEL_Z + 0.40)], 0.009, ir, seg=4)
        m.lathe((HRTH_XF - 0.22, yy, MANTEL_Z + 0.20),
                [(0.0, 0.0), (r * 0.8, 0.010), (r, 0.075), (r * 0.92, 0.175),
                 (r * 0.88, 0.185)], M(mm), seg=13)
    m.cyl((HRTH_XF - 0.22, OPEN_Y0 - 0.10, MANTEL_Z + 0.63), 0.016, 1.10, ir,
          seg=8, rot=(math.pi / 2, 0, 0))
    for yy in (OPEN_Y0 - 0.58, OPEN_Y0 + 0.42):
        m.strand([(HRTH_XF + 0.02, yy, MANTEL_Z + 0.74),
                  (HRTH_XF - 0.22, yy, MANTEL_Z + 0.63)], 0.012, ir, seg=4)

    # a bunch of dried fish strung up over the prep end -- cheap, and it says
    # 'this kitchen preserves what the river gives it'
    for k in range(6):
        sx = 2.28 + k * 0.075
        m.strand([(sx, IY - 0.16, 2.30), (sx, IY - 0.14, 2.30 - 0.06)], 0.007,
                 M("mat_k_straw"), seg=3)
        fish(m, (sx, IY - 0.14, 2.30 - 0.30), 0.30, rot=1.5708, tilt=1.4,
             skin="mat_k_fishskin_b")
    obs.append(m.finish(c, bevel=0.005, seg=1))
    return obs


# ------------------------------------------------------------ density pass

def build_density(c, kit):
    """The zones the first two versions left as bare painted board.

    Measured off the render rather than guessed at: the wall above the
    wainscot on the LEFT (between the hearth breast and the front corner) and
    on the BACK wall between the menu board and the door were the two largest
    unbroken fields of one value in the frame, and a cookhouse of all rooms
    has no excuse for empty wall -- every vertical surface in a working
    kitchen ends up carrying something.
    """
    m = KMesh("density")
    sh, shb = M("mat_k_shelf"), M("mat_k_shelf_b")
    g, gc = M("mat_k_green"), M("mat_k_green_c")
    ir, ox = M("mat_k_iron"), M("mat_k_oxblood")

    # ---- LEFT WALL, forward of the hearth: a plate rack and a smoking line
    # The frame crops the left wall forward of about y = -2.2, and the sun
    # shaft lands low and forward, so a rack of pale dishes placed by taste
    # ended up half out of frame and blown white at the very edge -- the
    # brightest thing in the picture, in the least useful place. Checked with
    # world_to_camera_view and moved back into the hearth's warm falloff.
    sy0, sy1 = -2.15, 0.02
    for sz in (1.42, 1.96):
        m.box((-IX + 0.10, (sy0 + sy1) / 2, sz), (0.10, (sy1 - sy0) / 2, 0.020), sh)
        m.box((-IX + 0.02, (sy0 + sy1) / 2, sz + 0.058),
              (0.022, (sy1 - sy0) / 2, 0.058), gc)          # back batten
        for by in (sy0 + 0.18, (sy0 + sy1) / 2, sy1 - 0.18):
            m.strand([(-IX + 0.02, by, sz + 0.12), (-IX + 0.19, by, sz - 0.01)],
                     0.015, sh, seg=4)
    # dishes stood on edge in the rack, and crocks lying on the lower shelf
    yy = sy0 + 0.14
    k = 0
    while yy < sy1 - 0.10:
        r = R.uniform(0.085, 0.125)
        m.card((-IX + 0.13, yy, 1.96 + r + 0.020), (0, 1, 0), (0, 0, 1),
               r * 1.9, r * 1.9,
               M("mat_k_ceramic_cr" if k % 3 else "mat_k_ceramic_gn"),
               curl=0.012, nu=8, nv=8, seed=yy)
        yy += r * 1.9 + R.uniform(0.02, 0.05)
        k += 1
    for k, dy in enumerate((0.30, 0.72, 1.18, 1.66, 2.06)):
        r = R.uniform(0.075, 0.105)
        m.lathe((-IX + 0.13, sy0 + dy, 1.442),
                [(0.0, 0.0), (r * 0.8, 0.008), (r, 0.075), (r * 0.88, 0.150),
                 (r * 0.72, 0.175), (r * 0.76, 0.185)],
                M(["mat_k_crock", "mat_k_ceramic_ox", "mat_k_ceramic_b",
                   "mat_k_ceramic_bl", "mat_k_crock"][k]),
                seg=11, lumpy=0.03, seed=dy)
    # a line of split fish smoking under the shelf, and a besom
    for k in range(7):
        fy = sy0 + 0.22 + k * 0.32
        if fy > sy1 - 0.12:
            break
        m.strand([(-IX + 0.09, fy, 1.40), (-IX + 0.10, fy, 1.34)], 0.007,
                 M("mat_k_straw"), seg=3)
        fish(m, (-IX + 0.16, fy, 1.08), 0.34, rot=1.5708, tilt=1.45,
             skin="mat_k_fishskin_b")
    m.strand([(-IX + 0.14, sy0 - 0.30, 0.02), (-IX + 0.34, sy0 - 0.18, 1.32)],
             0.019, M("mat_k_beam"), seg=6)
    m.lathe((-IX + 0.14, sy0 - 0.31, 0.0), [(0.0, 0.0), (0.070, 0.0),
                                            (0.082, 0.20), (0.050, 0.25)],
            M("mat_k_straw"), seg=10, lumpy=0.15, seed=3.3)

    # ---- BACK WALL between the menu board and the door -------------------
    bx0, bx1 = 2.10, 2.62
    m.box(((bx0 + bx1) / 2, IY - 0.11, 1.34), ((bx1 - bx0) / 2, 0.11, 0.020), sh)
    m.box(((bx0 + bx1) / 2, IY - 0.03, 1.40), ((bx1 - bx0) / 2, 0.028, 0.075), gc)
    for k, (dx, r, mm) in enumerate(((0.10, 0.082, "mat_k_crock"),
                                     (0.28, 0.068, "mat_k_ceramic_gn"),
                                     (0.44, 0.090, "mat_k_ceramic_ox"))):
        m.lathe((bx0 + dx, IY - 0.11, 1.362),
                [(0.0, 0.0), (r * 0.8, 0.008), (r, 0.070), (r * 0.86, 0.140),
                 (r * 0.70, 0.162)], M(mm), seg=11, lumpy=0.03, seed=dx * 5)
    # a hook rail with a flesh fork, a skimmer, a whisk of twigs and an apron
    m.cyl(((bx0 + bx1) / 2, IY - 0.09, 2.02), 0.015, bx1 - bx0, ir, seg=8,
          rot=(0, math.pi / 2, 0))
    for k, (dx, ln) in enumerate(((0.08, 0.34), (0.24, 0.28), (0.40, 0.40))):
        m.strand([(bx0 + dx, IY - 0.09, 2.00), (bx0 + dx, IY - 0.08, 2.00 - ln)],
                 0.010, ir, seg=5)
        if k == 2:
            for j in range(6):
                a = R.uniform(0, 6.28)
                m.strand([(bx0 + dx, IY - 0.08, 2.00 - ln),
                          (bx0 + dx + math.cos(a) * 0.045, IY - 0.08 + math.sin(a) * 0.02,
                           2.00 - ln - R.uniform(0.06, 0.13))], 0.008,
                         M("mat_k_straw"), seg=3)
        else:
            m.lathe((bx0 + dx, IY - 0.08, 2.00 - ln - 0.03),
                    [(0.0, 0.0), (0.050, 0.010), (0.058, 0.038), (0.055, 0.042)],
                    M("mat_k_iron_b"), seg=10, aspect=(1.0, 0.45))
    # the cook's spare apron on a peg -- the palest cloth in the room
    m.box((2.86, IY - 0.05, 2.06), (0.028, 0.028, 0.028), ir)
    m.cloth((2.86, IY - 0.10, 2.02), (1, 0, 0), (0, -1, 0), 0.36, 0.62,
            M("mat_k_apron"), taper=0.62, folds=4, seed=3.9)

    # ---- above the hatch lintel: a stub shelf carrying big crocks --------
    m.box((0.55, HAT_Y1 - 0.02, HAT_LINTEL + 0.14), (0.70, 0.145, 0.022), shb)
    for k, (dx, r, mm) in enumerate(((-0.44, 0.095, "mat_k_crock"),
                                     (-0.14, 0.115, "mat_k_ceramic_b"),
                                     (0.22, 0.082, "mat_k_ceramic_ox"),
                                     (0.50, 0.105, "mat_k_crock"))):
        m.lathe((0.55 + dx, HAT_Y1 - 0.02, HAT_LINTEL + 0.162),
                [(0.0, 0.0), (r * 0.78, 0.008), (r, 0.085), (r * 0.90, 0.165),
                 (r * 0.72, 0.195), (r * 0.76, 0.205)],
                M(mm), seg=11, lumpy=0.03, seed=dx * 7)

    # ---- the front-left corner was the darkest tile in the audit ---------
    m.lathe((-IX + 0.40, -2.95, 0.0), [(0.0, 0.0), (0.235, 0.0), (0.250, 0.04),
                                       (0.268, 0.30), (0.258, 0.54), (0.248, 0.56)],
            M("mat_k_crate"), seg=16, lumpy=0.018, seed=5.8)
    for bz in (0.06, 0.30, 0.52):
        m.ring((-IX + 0.40, -2.95, bz), 0.256, 0.014, ir)
    m.lathe((-IX + 0.40, -2.95, 0.545), [(0.250, 0.0), (0.240, 0.018),
                                         (0.06, 0.026), (0.055, 0.050), (0.0, 0.054)],
            sh, seg=13)
    for k in range(5):
        m.lathe((-IX + 0.42, -2.62, 0.60 + k * 0.021),
                [(0.0, 0.0), (0.100, 0.004), (0.112, 0.015), (0.090, 0.018)],
                shb, seg=12, rot=k * 0.4)
    return m.finish(c, bevel=0.005, seg=1)


# ---------------------------------------------------------------- steam

STEAM_SPOTS = [
    # (x, y, base_z, radius, height, seed)  -- one per working pot
    (-3.14, RNG_YF + 0.44, 1.32, 0.20, 0.86, 1),          # range stew pot
    (-3.70, 1.85 + 0.10, 0.90, 0.17, 0.62, 2),            # the cauldron
    (0.07, (HAT_Y0 + HAT_Y1) / 2 + 0.02, 1.32, 0.16, 0.60, 3),   # hatch kettle
]


def build_steam(c):
    """Steam over the pots -- the single most cookhouse-specific note in the
    whole frame, and the easiest one to ruin.

    Two parts. (1) WISP GEOMETRY: soft translucent shells that catch the warm
    light and give the steam a readable silhouette. (2) A tiny bounded VOLUME
    per pot. The manifest rule is that the interior fog box contains nothing
    but the room; a steam volume is a second, much smaller box, and kit lesson
    12 is that a smoke box which is harmless off-frame will quietly haze six
    of ten frame rows once it moves into shot -- so these are sized to the
    plume and nothing else, and the ray map in qa() checks them.
    """
    m = KMesh("steam_wisps")
    s1, s2 = M("mat_k_steam"), M("mat_k_steam_b")
    for (sx, sy, sz, r, h, seed) in STEAM_SPOTS:
        rr = random.Random(seed * 31)
        for k in range(5):
            t = k / 4
            drift = 0.16 * t
            m.sphere((sx + rr.uniform(-0.05, 0.05) + drift * 0.6,
                      sy + rr.uniform(-0.05, 0.05) - drift * 0.3,
                      sz + h * (0.16 + 0.78 * t)),
                     r * (0.38 + 0.58 * t), s1 if k % 2 else s2,
                     seg=11, rings=7,
                     scale=(1.0, 0.92, 0.62 + 0.25 * t),
                     rot=(0, 0, rr.uniform(0, 3)))
    ob = m.finish(c, bevel=0, seg=1, shade_smooth=True)
    ob.visible_shadow = False          # steam must not print a shadow anywhere

    vols = []
    for i, (sx, sy, sz, r, h, seed) in enumerate(STEAM_SPOTS):
        me = bpy.data.meshes.new("STEAM_VOL_%d" % i)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0,
                              matrix=Matrix.Translation((sx + 0.06, sy - 0.03,
                                                         sz + h * 0.46))
                              @ Matrix.Diagonal((r * 1.7, r * 1.6, h * 0.84, 1.0)))
        bm.to_mesh(me)
        bm.free()
        vob = bpy.data.objects.new("STEAM_VOL_%d" % i, me)
        c.objects.link(vob)
        mat = bpy.data.materials.get("mat_k_steamvol_%d" % i) or \
            bpy.data.materials.new("mat_k_steamvol_%d" % i)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vol = nt.nodes.new("ShaderNodeVolumeScatter"); vol.location = (-200, 0)
        # v1 ran 0.42 here. Even at a box only 0.6u across that is a solid
        # milky slab, and the three of them printed hard-edged rectangles over
        # the hatch, the pan wall and the range -- kit lesson 12, verbatim.
        # Steam has to be a HINT that catches the warm keys, not a surface.
        vol.inputs["Density"].default_value = 0.16
        # scatter colour saturated towards the light it is scattering (kit
        # lesson 22): near-white steam laid a milky veil over the whole
        # kitchen end on the first pass
        vol.inputs["Color"].default_value = (1.0, 0.82, 0.62, 1)
        vol.inputs["Anisotropy"].default_value = 0.30
        nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
        mat.use_fake_user = True
        me.materials.append(mat)
        vob.visible_shadow = False
        vols.append(vob)
    return ob, vols


# -------------------------------------------------------------------- pads

def build_shadow_ceiling(c):
    """A roof the camera cannot see.

    The cutaway has no ceiling and no near wall, so any directional light
    floods the room from above and from the front, and nothing overhead
    bounces the lantern light back down. A plane with visible_camera off fixes
    both: the window becomes the sun's only aperture, and the room finally gets
    a top bounce. It is NOT set dressing -- it never renders.
    """
    m = KMesh("shadow_ceiling")
    m.box((0, 0.10, 3.06), (HW + 0.15, (YB + 2.95) / 2, 0.05), M("mat_k_beam"))
    ob = m.finish(c, bevel=0)
    ob.visible_camera = False
    return ob


def build_pads(c):
    """Interaction metadata, not set dressing: real objects so the exporter can
    find them, hidden from the beauty render. `walk_pad_counter` sits in FRONT
    of the serving hatch, which is where a player stands to order."""
    out = []
    for name, (cx, cy, w, d) in {
            "walk_pad_door": (DOOR_X, 2.58, 1.30, 0.90),
            "walk_pad_counter": (0.88, 0.42, 2.40, 0.80)}.items():
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

def setup_light(c, dusk=118.0, world=0.22, fog=0.0068, fill=36.0, sky=64.0,
                winfill=58.0, fire=215.0, firecore=5.5, oven=28.0,
                hatchkey=58.0, beamup=32.0, prepkey=44.0, fgfill=58.0):
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

    # ---- the window: the room's one aperture -----------------------------
    # A room with no roof and no near wall lets a sun in from everywhere, which
    # is why the camera-invisible shadow ceiling exists. An AREA lamp outside
    # the pane spills onto the wall's outer face; a window SHAFT needs parallel
    # rays, i.e. a SUN.
    #
    # NOTE kit_wall_window inherits the frame's MID RAIL, a 0.12 timber running
    # across the glass at z 1.50-1.62. Aim through the UPPER light of the sash.
    #
    # Aim: across the room at the dining side and the front of the hearth
    # breast, where it lands as a window-shaped patch with the sash bars
    # printed across it and rakes table A on the way. A shaft landing on the
    # floor at dusk elevation arrives at grazing incidence and reads as almost
    # nothing; surfaces FACING the window take it square.
    sun = bpy.data.objects["SUN_key"]
    sun.hide_render = False
    sun.location = (HW + 1.50, WIN_Y - 0.05, 2.10)
    ru.aim(sun, (-IX + 0.55, WIN_Y + 0.15, 0.55))
    sun.data.energy = dusk
    sun.data.color = (1.0, 0.57, 0.35)
    sun.data.angle = math.radians(1.6)

    # soft fill hugging the inside of the pane: the sky (rather than the sun)
    # coming through the opening, and the light that models the window reveal
    win = bpy.data.objects["FILL_bounce"]
    win.name = "DUSK_window"
    win.location = (IX - 0.05, WIN_Y, 1.55)
    win.rotation_euler = (0, math.radians(-90), 0)
    win.data.energy = winfill
    win.data.size = 1.25
    win.data.color = (0.84, 0.63, 0.56)
    win.data.shape = "SQUARE"
    win.visible_camera = False

    # a very low cool fill from the open (cutaway) side, so foreground props
    # keep a readable dark side instead of going to pure black
    amb = bpy.data.objects["RIM_gorge"]
    amb.name = "AMB_open"
    amb.location = (0.0, -6.6, 3.6)
    amb.rotation_euler = (math.radians(62), 0, 0)
    amb.data.energy = fill
    amb.data.size = 9.5
    amb.data.color = (0.38, 0.48, 0.66)

    # cool overhead wash standing in for the light through the missing roof
    top = bpy.data.lights.new("SKY_top", "AREA")
    top.energy, top.size, top.color = sky, 8.5, (0.40, 0.50, 0.70)
    tob = bpy.data.objects.new("SKY_top", top)
    lc.objects.link(tob)
    tob.location = (0.0, -0.2, 2.94)          # just under the shadow ceiling

    # UPLIGHT FOR THE BEAMS. From a high 3/4 camera every beam shows the eye
    # its underside and its camera-facing cheek, and SKY_top sits ABOVE them,
    # so nothing in a physical rig ever touches those faces. A cheat with no
    # source in the room, and the right call: composition beats authenticity.
    up = bpy.data.lights.new("BEAM_up", "AREA")
    up.energy, up.size, up.color = beamup, 7.5, (0.90, 0.74, 0.56)
    uob = bpy.data.objects.new("BEAM_up", up)
    lc.objects.link(uob)
    uob.location = (0.0, 0.40, 2.22)
    uob.rotation_euler = (math.pi, 0, 0)      # -Z normal flipped to face +Z
    uob.visible_camera = False

    # THE HATCH is second in the value hierarchy and would otherwise sit in the
    # shadow of its own lintel. A dedicated soft key, camera-invisible.
    hk = bpy.data.lights.new("HATCH_key", "AREA")
    hk.energy, hk.color = hatchkey, (1.0, 0.71, 0.42)
    hk.shape = "RECTANGLE"
    hk.size, hk.size_y = 3.00, 1.20
    hob = bpy.data.objects.new("HATCH_key", hk)
    lc.objects.link(hob)
    hob.location = ((HAT_X0 + HAT_X1) / 2, (HAT_Y0 + HAT_Y1) / 2 - 0.10, 2.28)
    hob.rotation_euler = (math.radians(12), 0, 0)
    hob.visible_camera = False

    # the prep bench: the fish is the one clean bright note in the room and it
    # sits deep in the back wall's shadow. Small, tight, camera-invisible.
    pk = bpy.data.lights.new("PREP_key", "AREA")
    pk.energy, pk.color = prepkey, (1.0, 0.76, 0.50)
    pk.shape, pk.size, pk.size_y = "RECTANGLE", 2.40, 0.90
    pob = bpy.data.objects.new("PREP_key", pk)
    lc.objects.link(pob)
    pob.location = ((PRP_X0 + PRP_X1) / 2, PRP_Y0 - 0.30, 2.46)
    pob.rotation_euler = (math.radians(26), 0, 0)
    pob.visible_camera = False

    # ---- the hearth fire -------------------------------------------------
    # Kit lesson 14: a light INSIDE enclosed geometry lights nothing. The
    # firebox is a stone box, so the practical that lights the ROOM sits in the
    # OPENING plane facing out, and only a weak core light sits in the flames
    # to model the logs and the back of the box.
    core = bpy.data.lights.new("FIRE_core", "POINT")
    core.energy, core.color, core.shadow_soft_size = firecore, (1.0, 0.36, 0.11), 0.16
    cob = bpy.data.objects.new("FIRE_core", core)
    lc.objects.link(cob)
    cob.location = (FIRE_X, FIRE_Y, 0.40)

    mouth = bpy.data.lights.new("FIRE_mouth", "AREA")
    mouth.energy, mouth.color = fire, (1.0, 0.44, 0.15)
    mouth.shape = "RECTANGLE"
    mouth.size, mouth.size_y = 2.10, 1.18        # size runs local X = world Y
    mob = bpy.data.objects.new("FIRE_mouth", mouth)
    lc.objects.link(mob)
    mob.location = (HRTH_XF + 0.04, (OPEN_Y0 + OPEN_Y1) / 2, 0.62)
    mob.rotation_euler = (0, math.radians(-90), 0)     # -Z normal -> +X
    mob.visible_camera = False

    # a small warm lift on the hearth apron and the cat, which lie in the
    # mouth light's own shadow
    ap = bpy.data.lights.new("FIRE_apron", "POINT")
    ap.energy, ap.color, ap.shadow_soft_size = 22.0, (1.0, 0.50, 0.21), 0.45
    aob = bpy.data.objects.new("FIRE_apron", ap)
    lc.objects.link(aob)
    aob.location = (-2.72, 1.05, 0.92)

    # ---- the bread oven: the SECOND aperture -----------------------------
    om = bpy.data.lights.new("OVEN_mouth", "AREA")
    om.energy, om.color = oven, (1.0, 0.44, 0.16)
    om.shape, om.size, om.size_y = "RECTANGLE", 0.62, 0.50
    omb = bpy.data.objects.new("OVEN_mouth", om)
    lc.objects.link(omb)
    omb.location = ((OVEN_X0 + OVEN_X1) / 2, RNG_YF - 0.03, OVEN_MZ)
    omb.rotation_euler = (math.radians(90), 0, 0)     # -Z normal -> -Y
    omb.visible_camera = False
    # and the little ash-arch fire under the range top
    ar = bpy.data.lights.new("RANGE_arch", "AREA")
    ar.energy, ar.color = 26.0, (1.0, 0.40, 0.13)
    ar.shape, ar.size, ar.size_y = "RECTANGLE", 0.60, 0.42
    arb = bpy.data.objects.new("RANGE_arch", ar)
    lc.objects.link(arb)
    arb.location = (-3.00, RNG_YF - 0.03, 0.34)
    arb.rotation_euler = (math.radians(90), 0, 0)
    arb.visible_camera = False

    # the window end. The bench, the crates and the eel barrel all sit in the
    # lee of the beam post and came back muddy; this is the light that makes
    # the right third of the frame a place rather than a shadow.
    wk = bpy.data.lights.new("WIN_key", "AREA")
    wk.energy, wk.color = 34.0, (1.0, 0.72, 0.46)
    wk.shape, wk.size, wk.size_y = "RECTANGLE", 1.60, 3.20
    wkob = bpy.data.objects.new("WIN_key", wk)
    lc.objects.link(wkob)
    wkob.location = (IX - 0.55, -0.35, 2.60)
    wkob.rotation_euler = (0, math.radians(18), 0)
    wkob.visible_camera = False

    # FOREGROUND FILL. The bottom fifth of the frame is where a cutaway
    # interior goes dead. Broad, weak, warm and camera-invisible.
    fg = bpy.data.lights.new("FG_fill", "AREA")
    fg.energy, fg.color, fg.size = fgfill, (1.0, 0.76, 0.52), 8.2
    fgob = bpy.data.objects.new("FG_fill", fg)
    lc.objects.link(fgob)
    fgob.location = (0.55, -2.45, 2.70)
    fgob.rotation_euler = (math.radians(16), 0, 0)
    fgob.visible_camera = False

    # bounded fog: haze inside the room only, so the lantern pools get halos.
    # A world volume would extinguish everything (kit manifest, bug 1), and the
    # box must contain NOTHING but the room (bug 2, in reverse) or the sun
    # outside lights the volume and the whole plate goes to soup.
    fb = bpy.data.objects["FOG_BOX"]
    fb.name = "FOG_ROOM"
    fb.location = (0.0, 0.0, 1.46)
    fb.scale = (4.34 / 80.0, 3.10 / 80.0, 1.44 / 30.0)
    vn = fb.data.materials[0].node_tree.nodes["Volume Scatter"]
    vn.inputs["Density"].default_value = fog
    vn.inputs["Color"].default_value = (0.64, 0.52, 0.42, 1)
    return win, amb, fb


def setup_camera(pitch=24.0, yaw=0.0, dist=10.30, target=(0.0, 0.45, 1.20),
                 vfov=35.0):
    """One fixed camera: perspective, VERTICAL fov 35 deg (Blender fits the
    sensor to the LONG edge by default, which would give 35 deg horizontally),
    high 3/4 looking down into the cutaway. At dist 10.3 the vertical framing
    is 2*d*tan(17.5) = 6.5u, which is the project standard."""
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

FEATS = {
    "hearth mantel":  (HRTH_XF - 0.30, (OPEN_Y0 + OPEN_Y1) / 2, MANTEL_Z),
    "fire bed":       (FIRE_X, FIRE_Y, 0.30),
    "cauldron":       (FIRE_X - 0.02, FIRE_Y + 0.10, 0.90),
    "spit":           (HRTH_XF - 0.16, (OPEN_Y0 + OPEN_Y1) / 2, 0.46),
    "oven mouth":     ((OVEN_X0 + OVEN_X1) / 2, RNG_YF, OVEN_MZ),
    "oven crown":     ((OVEN_X0 + OVEN_X1) / 2, RNG_YF + 0.4, OVEN_TOP),
    "range pot":      (-3.14, RNG_YF + 0.44, RNG_H + 0.25),
    "prep fish":      (-0.36, (PRP_Y0 + PRP_Y1) / 2, PRP_H + 0.15),
    "knife block":    (PRP_X1 - 0.42, (PRP_Y0 + PRP_Y1) / 2, PRP_H + 0.30),
    "pan wall":       ((PRP_X0 + PRP_X1) / 2, IY - 0.11, 1.85),
    "onion braid":    (PRP_X0 + 0.07, IY - 0.11, 1.70),
    "hatch top L":    (HAT_X0, HAT_Y0, HAT_H),
    "hatch top R":    (HAT_X1, HAT_Y0, HAT_H),
    "hatch kettle":   (HAT_X0 + 0.52, (HAT_Y0 + HAT_Y1) / 2, HAT_H + 0.25),
    "hatch lintel":   ((HAT_X0 + HAT_X1) / 2, HAT_Y1, HAT_LINTEL),
    "menu board":     (1.72, HAT_Y1 - 0.16, HAT_LINTEL - 0.72),
    "dry rack":       (-1.40, 2.24, 2.20),
    "door":           (DOOR_X, IY, 1.05),
    "window":         (IX, WIN_Y, 1.55),
    "eel barrel":     (4.02, 0.72, 0.62),
    "fish crates":    (3.72, 2.02, 0.60),
    "table A":        (-2.20, -1.05, TBL_H),
    "table B":        (1.32, -1.62, TBL_H),
    "window bench":   (IX - 0.26, -0.60, BENCH_H),
    "cat":            (-2.55, 0.62, 0.10),
    "wash tub":       (-3.55, -2.05, 0.90),
    "fg crates":      (2.90, -2.60, 0.40),
    "back wall top":  (0.0, IY, WH),
    "floor front-L":  (-HW, YF, 0.0),
    "floor front-R":  (HW, YF, 0.0),
}


def qa():
    """Place by projection, not by eyeball (kit lesson 16). Reports whether the
    features are in frame, and ray-maps the frame so a stray volume or a black
    hole shows up in seconds rather than after a four-minute render."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    print("\n--- FRAME CHECK (u,v in 0..1 means in frame) ---")
    for k, p in FEATS.items():
        u = world_to_camera_view(sc, cam, Vector(p))
        ok = "in " if (0.0 <= u.x <= 1.0 and 0.0 <= u.y <= 1.0) else "OUT"
        print("  %-16s %s  u=%6.3f v=%6.3f  d=%5.2f" % (k, ok, u.x, u.y, u.z))

    print("\n--- RAY MAP (what the frame actually hits) ---")
    # FOG_ROOM, the steam volumes and shadow_ceiling are real meshes that every
    # ray hits first and that the camera never sees, so the map steps THROUGH
    # them -- otherwise it reports the fog box twelve times a row.
    skip = {"FOG_ROOM", "shadow_ceiling"}
    skip |= {o.name for o in bpy.data.objects
             if o.name.startswith("STEAM_VOL") or o.name.startswith("walk_pad")}
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
            for _ in range(14):
                hit, loc, nrm, idx, obj, mw = sc.ray_cast(dg, o, d)
                if not hit:
                    break
                if obj.name not in skip:
                    name = obj.name[:9]
                    break
                o = loc + d * 0.01
            line.append(name.ljust(10))
        print("   " + "".join(line))

    # ---- can the camera SEE the ember bed? (kit lesson 20) ---------------
    # ray_cast must skip everything the camera cannot see, or the answer is
    # always "blocked by FOG_ROOM" and tells you nothing.
    hidden = []
    for o in bpy.data.objects:
        if o.type == "MESH" and (o.name in skip or not o.visible_camera):
            if not o.hide_viewport:
                o.hide_viewport = True
                hidden.append(o)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    print("\n--- FIRE VISIBILITY (must hit hearth_fire / range_fire) ---")
    probes = {
        "ember bed near":  (FIRE_X, FIRE_Y - 0.42, 0.20),
        "ember bed mid":   (FIRE_X, FIRE_Y, 0.20),
        "ember bed far":   (FIRE_X, FIRE_Y + 0.42, 0.20),
        "flame tips":      (FIRE_X, FIRE_Y, 0.62),
        "oven ember":      ((OVEN_X0 + OVEN_X1) / 2 + 0.20, RNG_YF + 0.30,
                            OVEN_MZ - 0.22),
        "range arch fire": (-3.00, RNG_YF + 0.34, 0.12),
    }
    for k, p in probes.items():
        d = (Vector(p) - org)
        dist = d.length
        d.normalize()
        hit, loc, nrm, idx, obj, mw = sc.ray_cast(dg, org + d * 0.02, d)
        seen = obj.name if hit else "(nothing)"
        gap = (loc - Vector(p)).length if hit else 999
        where = ("at %.2f %.2f %.2f" % (loc.x, loc.y, loc.z)) if hit else ""
        print("  %-16s -> %-14s gap=%.3f %-22s %s" %
              (k, seen[:14], gap, where, "OK" if gap < 0.26 else "BLOCKED"))
    for o in hidden:
        o.hide_viewport = False
    bpy.context.view_layer.update()
    print()


def audit_black(path):
    """Report the darkest tiles of the render. The brief's hard rule is 'no
    black region larger than a fist' -- this measures it instead of guessing.

    Reads the saved PNG, not "Render Result": in background mode the result
    datablock's pixels come back all zeros.
    """
    img = bpy.data.images.load(path)
    px = list(img.pixels)
    w, h = img.size
    gw, gh = 16, 9
    print("\n--- LUMA GRID x100 (printed top row = top of frame) ---")
    worst = []
    for gy in range(gh - 1, -1, -1):
        row = []
        for gx in range(gw):
            tot = n = 0
            for yy in range(gy * h // gh, (gy + 1) * h // gh, 4):
                for xx in range(gx * w // gw, (gx + 1) * w // gw, 4):
                    i = (yy * w + xx) * 4
                    tot += 0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2]
                    n += 1
            v = int(100 * tot / max(1, n))
            row.append("%4d" % v)
            worst.append((v, gx, gy))
        print("   " + "".join(row))
    worst.sort()
    dark = [t for t in worst if t[0] < 6 and t[2] < gh - 1]
    print("   tiles under 6/100 (excluding the top row, which is the void): %d"
          % len(dark), dark[:8])
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
    km.make_all()
    kit = pb.append_from_kit(KIT_NAMES)
    vl = bpy.context.view_layer.layer_collection.children.get("KIT_SOURCE")
    if vl:
        vl.exclude = True

    c = coll("COOKHOUSE_INT")
    build_floor(c)
    build_shell(c, kit)
    build_hearth(c)
    build_hearth_kit(c, kit)
    build_range(c)
    build_range_props(c)
    build_prep(c)
    build_panwall(c)
    build_hatch(c)
    build_menuboard(c)
    build_dryrack(c)
    build_dining(c, kit)
    build_doorzone(c, kit)
    build_foreground(c, kit)
    build_hanging(c, kit)
    build_density(c, kit)
    build_steam(c)
    build_shadow_ceiling(c)
    build_pads(c)

    setup_light(c, **light_kw)
    setup_camera()

    r = kit["REF_human_1p7"]
    r.location = (0.88, 0.10, 0.0)          # standing at the serving hatch
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
          dusk=opt("--dusk", 118.0, float),
          world=opt("--world", 0.22, float),
          fog=opt("--fog", 0.0068, float),
          fill=opt("--fill", 36.0, float),
          sky=opt("--sky", 64.0, float),
          winfill=opt("--winfill", 58.0, float),
          fire=opt("--fire", 215.0, float),
          firecore=opt("--firecore", 5.5, float),
          oven=opt("--oven", 28.0, float),
          hatchkey=opt("--hatchkey", 58.0, float),
          prepkey=opt("--prepkey", 44.0, float),
          beamup=opt("--beamup", 32.0, float),
          fgfill=opt("--fgfill", 58.0, float))

    if opt("--pitch") or opt("--yaw") or opt("--dist"):
        setup_camera(pitch=opt("--pitch", 24.0, float),
                     yaw=opt("--yaw", 0.0, float),
                     dist=opt("--dist", 10.30, float))

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
