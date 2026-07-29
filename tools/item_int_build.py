#!/usr/bin/env python3
"""Dellhollow ITEM SHOP interior (sceneKey del-item-int) -- chandlery skin.

This is the SHOP ARCHETYPE. The weapon and armor shops get built as skins over
the same layout, so the structure is deliberately parameterised:

    FF9 cutaway room, floor + back wall + two side walls, no near wall.
    ONE fixed perspective camera, vertical fov 35 deg, high 3/4 looking down.

    zone            where                       what changes per skin
    -------------   -------------------------   ---------------------------
    ENTRY           back wall, left bay          never (kit_wall_door)
    COUNTER         right half, y ~ 0.6..1.3     counter dressing only
    KEEP            behind counter, y 1.3..2.5   NPC stands here
    BACK WALL WARES shelving x 0.55..3.87        jars -> blades -> mail
    BROWSE          left half + right foreground crates -> racks -> stands
    HANGING         ceiling beams                lanterns stay, goods change

Naming contract for the engine: `walk_floor` is the walkable floor mesh,
`walk_pad_door` and `walk_pad_counter` are the interaction pads (hidden from
render -- they are metadata, not set dressing).

Run headless:
    Blender -b -P tools/item_int_build.py -- --out tools/blends/interiors/item-int.blend \
        --render docs/qa/interiors/item-int_v1.png --samples 224
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


pb = _mod("probe_build")          # Mesh / place / append_from_kit helpers
im = _mod("item_int_materials")        # interior material library
ru = _mod("render_util")

R = random.Random(20260729)

# ---------------------------------------------------------------- room shape
HW = 4.00          # half width  -> x in [-4, 4]
YB, YF = 3.00, -3.00   # back wall plane, open front edge
WH = 3.00          # wall height (matches the 3x3 kit panels)
CLAD = 0.126       # kit panel: cladding front face sits this far in front of origin
IX = HW - CLAD     # inner face of the side walls  (3.874)
IY = YB - CLAD     # inner face of the back wall   (2.874)

BEAM_Z = 2.860     # centre of the ceiling beams (tucked up under the plate:
BEAM_H = 0.075     # a lower beam becomes a black bar across the counter line)
BEAM_Y = (-1.70, 0.40, 2.20)
# (y, x0, x1) -- the front beam is a HALF beam carried on a post at x = -0.60
BEAMS = ((BEAM_Y[0], -HW, -1.15), (BEAM_Y[1], -HW, HW), (BEAM_Y[2], -HW, HW))

CTR_X0, CTR_X1 = 0.30, IX          # counter runs from the gap to the right wall
CTR_Y0, CTR_Y1 = 0.34, 1.08        # front face / back face
CTR_H = 1.05                       # counter height (project standard)

SHELF_X0, SHELF_X1 = 0.52, IX
SHELF_Y0, SHELF_Y1 = IY - 0.36, IY

DOOR_X = -2.50     # centre of the back-wall door bay
WIN_Y = 1.50       # centre of the left-wall window bay


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
    """probe_build.Mesh plus the primitives an interior needs: lathes for
    turned/coopered goods, strands for cordage, spheres for produce."""

    def sphere(self, center, r, mat, seg=14, rings=8, scale=(1, 1, 1), rot=(0, 0, 0)):
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

    def lathe(self, base, profile, mat, seg=16, aspect=(1.0, 1.0), lumpy=0.0,
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


def sagline(p0, p1, dz, n=12):
    """Parabolic sag between two points -- cordage, netting, bunting."""
    p0, p1 = Vector(p0), Vector(p1)
    out = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t)
        p.z -= dz * 4.0 * t * (1.0 - t)
        out.append(tuple(p))
    return out


# ------------------------------------------------------------------ the kit

KIT_NAMES = ["kit_wall_door", "kit_wall_window", "kit_wall_plain", "kit_barrel",
             "kit_crate", "kit_bucket", "kit_rope_coil", "kit_lantern_hanging",
             "kit_lantern_light", "kit_beam", "REF_human_1p7",
             "SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX"]

# kit exterior material -> interior equivalent. The kit's moss layer is driven
# by the world-up normal, which is right for a river town and wrong indoors.
RESKIN = {
    "mat_wallwood":      "mat_i_wall",       # cladding -> weathered interior timber
    "mat_timber":        "mat_i_green",      # framing  -> moss-green painted trim
    "mat_wallwood_dark": "mat_i_oxblood",    # door leaf / staves -> oxblood
    "mat_iron":          "mat_i_iron",
    "mat_glass_dark":    "mat_i_dusk",       # window panes -> dusk sky
    "mat_deck":          "mat_i_floor",
    "mat_rope":          "mat_rope",
}


def reskin(ob, extra=None):
    """Swap an appended kit object's materials for the interior palette."""
    table = dict(RESKIN)
    table.update(extra or {})
    me = ob.data
    for i, slot in enumerate(me.materials):
        if slot is None:
            continue
        new = table.get(slot.name)
        if new and bpy.data.materials.get(new):
            me.materials[i] = bpy.data.materials[new]
    return ob


# ------------------------------------------------------------------- shell

def build_floor(c):
    """`walk_floor`: real plank geometry, three de-correlated plank materials
    dealt out board by board. The gaps and the material rotation between them
    are what stop a 1k texture from tiling visibly across 8x6 units."""
    m = IMesh("walk_floor")
    mats = [M("mat_i_floor"), M("mat_i_floor_b"), M("mat_i_floor_c"),
            M("mat_i_floor_d"), M("mat_i_floor_e")]
    x = -HW - 0.05
    i = 0
    while x < HW + 0.05:
        w = R.uniform(0.215, 0.305)
        # a plank run is butt-jointed once or twice down its length
        cuts = sorted(R.uniform(YF + 0.9, YB - 0.9) for _ in range(R.choice([1, 1, 2])))
        edges = [YF - 0.08] + cuts + [YB + 0.08]
        for a, b in zip(edges[:-1], edges[1:]):
            mat = mats[(i + R.choice([0, 0, 1, 2, 3, 4])) % 5]
            m.box((x + w / 2, (a + b) / 2, -0.031),
                  (w / 2 - 0.008, (b - a) / 2 - 0.006, 0.031), mat,
                  rot=(R.uniform(-0.004, 0.004), 0, 0))
            i += 1
        x += w
    # sub-floor so no light leaks through the plank gaps
    m.box((0, 0, -0.10), (HW + 0.12, (YB - YF) / 2 + 0.12, 0.04), M("mat_i_beam"))
    ob = m.finish(c, bevel=0.006, seg=1)
    ob.name = "walk_floor"
    ob.data.name = "walk_floor"
    return ob


def build_wall_run(name, width, c):
    """A wall segment in the same local frame as the 3x3 kit panels: width
    along local X, height along Z, cladding front face at y = -0.126."""
    m = IMesh(name)
    clad = [M("mat_i_wall"), M("mat_i_wall_b")]
    frame = M("mat_i_green")
    # vertical cladding boards, each with a hair of random rotation
    x = -width / 2
    k = 0
    while x < width / 2 - 1e-3:
        w = min(R.uniform(0.185, 0.245), width / 2 - x)
        m.box((x + w / 2, -0.077, WH / 2), (w / 2 - 0.004, 0.049, WH / 2),
              clad[k % 2 if R.random() > 0.25 else R.randint(0, 1)],
              rot=(0, R.uniform(-0.0035, 0.0035), 0))
        x += w
        k += 1
    # stud frame behind the boards (matches the kit silhouette)
    m.box((0, 0.02, 0.07), (width / 2, 0.05, 0.07), frame)             # sill
    m.box((0, 0.02, WH - 0.08), (width / 2, 0.05, 0.08), frame)        # head
    m.box((0, 0.02, WH * 0.52), (width / 2, 0.042, 0.055), frame)      # mid rail
    for sx in (-1, 1):
        m.box((sx * (width / 2 - 0.07), 0.02, WH / 2), (0.07, 0.05, WH / 2), frame)
    n_std = max(1, int(width / 1.05))
    for i in range(1, n_std):
        m.box((-width / 2 + width * i / n_std, 0.02, WH / 2), (0.055, 0.045, WH / 2),
              frame)
    return m.finish(c, bevel=0.008)


def build_shell(c, kit):
    """Back wall (door bay + run), left wall (window bay + run), right wall."""
    obs = []

    door = kit["kit_wall_door"]
    door.location = (DOOR_X, YB, 0)
    reskin(door)
    obs.append(door)
    if door.name not in c.objects:
        c.objects.link(door)

    win = kit["kit_wall_window"]
    win.location = (-HW, WIN_Y, 0)
    win.rotation_euler = (0, 0, math.radians(90))
    reskin(win)
    obs.append(win)
    if win.name not in c.objects:
        c.objects.link(win)

    # back wall, right of the door bay: 5u
    w = build_wall_run("wall_back", 5.0, c)
    w.location = (1.5, YB, 0)
    obs.append(w)
    # left wall, front half: 3u
    w = build_wall_run("wall_left", 3.0, c)
    w.location = (-HW, -1.5, 0)
    w.rotation_euler = (0, 0, math.radians(90))
    obs.append(w)
    # right wall: full 6u
    w = build_wall_run("wall_right", 6.0, c)
    w.location = (HW, 0.0, 0)
    w.rotation_euler = (0, 0, math.radians(-90))
    obs.append(w)

    # ---- trim: the moss-green painted joinery that ties the palette -------
    t = IMesh("trim")
    g, gb, ox = M("mat_i_green"), M("mat_i_green_b"), M("mat_i_oxblood")
    # corner posts
    for (px, py) in ((-IX + 0.09, IY - 0.09), (IX - 0.09, IY - 0.09)):
        t.box((px, py, WH / 2), (0.09, 0.09, WH / 2), g)
    for px in (-IX + 0.09, IX - 0.09):
        t.box((px, YF + 0.10, WH / 2), (0.09, 0.09, WH / 2), gb)
    # top plate all round, and a matching wall plate the beams sit on
    t.box((0, IY - 0.075, WH - 0.10), (HW, 0.075, 0.10), g)
    for sx in (-1, 1):
        t.box((sx * (IX - 0.075), 0, WH - 0.10), (0.075, (YB - YF) / 2, 0.10), g)
    # skirting, broken at the door opening
    sk = 0.155
    for (x0, x1) in ((-IX, DOOR_X - 0.62), (DOOR_X + 0.62, IX)):
        t.box(((x0 + x1) / 2, IY - 0.035, sk / 2), ((x1 - x0) / 2, 0.035, sk / 2), gb)
    for sx in (-1, 1):
        t.box((sx * (IX - 0.035), (YB + YF) / 2, sk / 2),
              (0.035, (YB - YF) / 2, sk / 2), gb)
    # oxblood accent band above the skirting: the map's shop-front colour
    for (x0, x1) in ((-IX, DOOR_X - 0.62), (DOOR_X + 0.62, IX)):
        t.box(((x0 + x1) / 2, IY - 0.022, sk + 0.045), ((x1 - x0) / 2, 0.022, 0.045), ox)
    for sx in (-1, 1):
        t.box((sx * (IX - 0.022), (YB + YF) / 2, sk + 0.045),
              (0.022, (YB - YF) / 2, 0.045), ox)
    # a picture rail the hanging pegs live on
    for sx in (-1, 1):
        t.box((sx * (IX - 0.045), (YB + YF) / 2, 1.94), (0.045, (YB - YF) / 2, 0.048), g)
    obs.append(t.finish(c, bevel=0.008))

    # ---- ceiling beams ---------------------------------------------------
    # From a high 3/4 the camera sees the TOP of every beam, which nothing
    # lights, so a full-width beam is a black bar straight across the frame.
    # Two full beams live high in the frame (they read as ceiling); the front
    # one is a half beam over the browse aisle, carried on a floor post, so
    # the open floor and the counter stay unbarred.
    b = IMesh("beams")
    bm_, g = M("mat_i_beam"), M("mat_i_green")
    for (y, x0, x1) in BEAMS:
        b.box(((x0 + x1) / 2, y, BEAM_Z), ((x1 - x0) / 2, BEAM_H, BEAM_H), bm_,
              rot=(0, R.uniform(-0.004, 0.004), 0))
        for sx, bx in ((-1, x0), (1, x1)):
            if abs(bx) > HW - 0.2:            # corbel only where it meets a wall
                b.box((bx - sx * 0.16, y, BEAM_Z - 0.185), (0.16, 0.075, 0.09), bm_)
    for x in (-2.55, 1.35):
        b.box((x, 1.40, BEAM_Z + 0.120), (0.070, 1.48, 0.045), bm_)
    # the post carrying the half beam: also the vertical that breaks up the
    # empty middle distance and separates the browse aisle from the open floor
    py, px = BEAMS[0][0], BEAMS[0][2]
    b.box((px, py, (BEAM_Z - BEAM_H) / 2), (0.085, 0.085, (BEAM_Z - BEAM_H) / 2), bm_)
    b.box((px, py, 0.11), (0.115, 0.115, 0.11), g)                  # painted plinth
    for s in (-1, 1):
        b.strand([(px + s * 0.34, py, BEAM_Z - BEAM_H - 0.02),
                  (px, py, BEAM_Z - BEAM_H - 0.36)], 0.055, bm_, seg=6)
    b.cyl((px, py - 0.10, 1.62), 0.020, 0.16, M("mat_i_iron"), seg=8,
          rot=(math.pi / 2, 0, 0))                                  # a peg on the post
    obs.append(b.finish(c, bevel=0.01))
    return obs


# ----------------------------------------------------------------- counter

def build_counter(c):
    m = IMesh("counter")
    top, ox, g, bm_ = M("mat_i_counter"), M("mat_i_oxblood"), M("mat_i_green"), M("mat_i_beam")
    x0, x1, y0, y1 = CTR_X0, CTR_X1, CTR_Y0, CTR_Y1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # worn top slab with a front nosing that overhangs the panelling
    m.box((cx, cy - 0.035, CTR_H - 0.042), ((x1 - x0) / 2, (y1 - y0) / 2 + 0.035, 0.042), top)
    m.box((cx, y0 - 0.062, CTR_H - 0.10), ((x1 - x0) / 2, 0.032, 0.055), top)
    # panelled front: oxblood panels in green stiles and rails
    stiles = [x0 + 0.06, 1.22, 2.20, 3.16, x1 - 0.05]
    for sx in stiles:
        m.box((sx, y0 - 0.012, (CTR_H - 0.08) / 2), (0.062, 0.032, (CTR_H - 0.08) / 2), g)
    m.box((cx, y0 - 0.012, 0.075), ((x1 - x0) / 2, 0.032, 0.075), g)
    m.box((cx, y0 - 0.012, CTR_H - 0.145), ((x1 - x0) / 2, 0.032, 0.058), g)
    for a, b in zip(stiles[:-1], stiles[1:]):
        m.box(((a + b) / 2, y0 + 0.012, (CTR_H - 0.08) / 2),
              ((b - a) / 2 - 0.06, 0.028, (CTR_H - 0.08) / 2 - 0.12), ox)
    # carcass sides + back, and the shelf under the counter
    for sx in (x0 + 0.03, x1 - 0.03):
        m.box((sx, cy, (CTR_H - 0.08) / 2), (0.03, (y1 - y0) / 2, (CTR_H - 0.08) / 2), bm_)
    m.box((cx, y1 - 0.025, (CTR_H - 0.08) / 2), ((x1 - x0) / 2, 0.025, (CTR_H - 0.08) / 2), bm_)
    m.box((cx, cy, 0.46), ((x1 - x0) / 2 - 0.05, (y1 - y0) / 2 - 0.05, 0.018), bm_)
    # a bank of small drawers at the right end, brass pulls
    for i in range(3):
        z = 0.60 + i * 0.145
        m.box((3.53, y0 - 0.05, z), (0.30, 0.022, 0.062), M("mat_i_shelf"))
        m.cyl((3.53, y0 - 0.085, z), 0.019, 0.05, M("mat_i_brass"), seg=10,
              rot=(math.pi / 2, 0, 0))
    return m.finish(c, bevel=0.008)


def build_backshelves(c):
    """The wall of goods behind the shopkeep -- the shop's signature mass."""
    m = IMesh("backshelf")
    sh, shb, g, ox = M("mat_i_shelf"), M("mat_i_shelf_b"), M("mat_i_green"), M("mat_i_oxblood")
    x0, x1, y0, y1 = SHELF_X0, SHELF_X1, SHELF_Y0, SHELF_Y1
    cy, dy = (y0 + y1) / 2, (y1 - y0) / 2
    boards = [0.34, 0.82, 1.30, 1.78, 2.26]
    uprights = [x0 + 0.035, 1.62, 2.78, x1 - 0.035]
    for z in boards:
        m.box(((x0 + x1) / 2, cy, z), ((x1 - x0) / 2, dy, 0.021),
              sh if z in boards[::2] else shb)
        # a thin lip so nothing looks like it will slide off
        m.box(((x0 + x1) / 2, y0 + 0.012, z + 0.035), ((x1 - x0) / 2, 0.012, 0.024), g)
    for ux in uprights:
        m.box((ux, cy, 1.30), (0.035, dy, 1.30), shb)
        m.box((ux, y0 - 0.014, 1.30), (0.042, 0.014, 1.30), ox)
    # cornice + oxblood signboard over the top
    # return leg down the right wall (above the counter's end)
    ry0, ry1 = 1.15, y1
    rx0, rx1 = IX - 0.34, IX
    for z in boards:
        m.box(((rx0 + rx1) / 2, (ry0 + ry1) / 2, z), (0.17, (ry1 - ry0) / 2, 0.021),
              shb if z in boards[::2] else sh)
        m.box((rx1 - 0.012, (ry0 + ry1) / 2, z + 0.035), (0.012, (ry1 - ry0) / 2, 0.024), g)
    for uy in (ry0 + 0.035, 1.92):
        m.box(((rx0 + rx1) / 2, uy, 1.30), (0.17, 0.035, 1.30), shb)
        m.box((rx0 + 0.014, uy, 1.30), (0.014, 0.042, 1.30), ox)
    m.box(((rx0 + rx1) / 2, (ry0 + ry1) / 2 - 0.03, 2.62), (0.20, (ry1 - ry0) / 2, 0.03), sh)
    m.box(((x0 + x1) / 2, cy - 0.03, 2.62), ((x1 - x0) / 2 + 0.03, dy + 0.03, 0.03), sh)
    m.box(((x0 + x1) / 2, y1 - 0.045, 2.42), ((x1 - x0) / 2 - 0.04, 0.045, 0.155), ox)
    m.box(((x0 + x1) / 2, y1 - 0.062, 2.42), ((x1 - x0) / 2 - 0.02, 0.028, 0.185), g)
    return m.finish(c, bevel=0.006)


# ------------------------------------------------------------------- goods

def jar(m, x, y, z, h=0.28, r=0.085, mat=None, label=True, lid=True, seed=0):
    mat = mat or M("mat_i_ceramic")
    prof = [(0, 0), (r * 0.80, 0), (r * 0.97, h * 0.14), (r, h * 0.42),
            (r * 0.93, h * 0.70), (r * 0.66, h * 0.90), (r * 0.62, h * 0.96), (0, h)]
    m.lathe((x, y, z), prof, mat, seg=16, lumpy=0.02, seed=seed)
    if lid:
        m.cyl((x, y, z + h + 0.012), r * 0.70, 0.026, M("mat_i_canvas"), seg=14)
        m.strand(sagline((x - r * 0.72, y, z + h + 0.004),
                         (x + r * 0.72, y, z + h + 0.004), 0.004, 4),
                 0.006, M("mat_rope"), seg=5)
    if label:
        m.box((x, y - r * 0.99, z + h * 0.46), (r * 0.55, 0.004, h * 0.20),
              M("mat_i_label"), rot=(0, 0, 0))
        m.box((x, y - r * 1.02, z + h * 0.50), (r * 0.36, 0.003, h * 0.035),
              M("mat_i_iron"))


def bottle(m, x, y, z, h=0.30, r=0.052, mat=None, seed=0):
    mat = mat or M("mat_i_glass_brown")
    prof = [(0, 0), (r * 0.9, 0), (r, h * 0.10), (r * 0.97, h * 0.46),
            (r * 0.55, h * 0.62), (r * 0.32, h * 0.72), (r * 0.30, h * 0.94),
            (r * 0.36, h * 0.97), (0, h)]
    m.lathe((x, y, z), prof, mat, seg=14, seed=seed)
    m.cyl((x, y, z + h * 0.96), r * 0.30, 0.03, M("mat_i_wax"), seg=10)


def tin(m, x, y, z, h=0.115, r=0.062, mat=None):
    mat = mat or M("mat_i_rust")
    m.lathe((x, y, z), [(0, 0), (r, 0), (r, h * 0.92), (r * 0.94, h), (0, h)],
            mat, seg=14)
    m.cyl((x, y, z + h + 0.006), r * 0.98, 0.012, M("mat_i_iron"), seg=14)


def candle_bundle(m, x, y, z, n=7, h=0.26, seed=0):
    w = M("mat_i_wax")
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = 0.030 if i else 0.0
        m.cyl((x + rr * math.cos(a), y + rr * math.sin(a), z + h / 2),
              0.0135, h * R.uniform(0.9, 1.05), w, seg=8)
        m.strand([(x + rr * math.cos(a), y + rr * math.sin(a), z + h),
                  (x + rr * math.cos(a), y + rr * math.sin(a), z + h + 0.018)],
                 0.0028, M("mat_i_iron"), seg=4)
    m.strand(sagline((x - 0.05, y - 0.045, z + h * 0.55),
                     (x + 0.05, y - 0.045, z + h * 0.55), 0.006, 4),
             0.007, M("mat_rope"), seg=5)


def rolled_chart(m, x, y, z, h=0.34, lean=0.10):
    m.cyl((x, y, z + h / 2), 0.030, h, M("mat_i_paper"), seg=10,
          rot=(0, lean, 0))
    m.strand([(x, y - 0.033, z + h * 0.55), (x, y + 0.033, z + h * 0.55)],
             0.005, M("mat_rope"), seg=5)


def bowl_stack(m, x, y, z, n=3, r=0.085):
    for i in range(n):
        zz = z + i * 0.042
        m.lathe((x, y, zz), [(r * 0.45, 0), (r * 0.52, 0.006), (r, 0.048),
                             (r * 0.96, 0.052), (r * 0.44, 0.012)],
                M("mat_i_ceramic_b") if i % 2 else M("mat_i_ceramic"), seg=14)


def sack(m, x, y, z, h=0.40, r=0.20, seed=0.0, mat=None, tilt=0.0):
    mat = mat or M("mat_i_burlap")
    prof = [(0, 0), (r * 0.85, 0.01), (r, h * 0.22), (r * 0.97, h * 0.52),
            (r * 0.72, h * 0.74), (r * 0.34, h * 0.86), (r * 0.20, h * 0.92),
            (r * 0.26, h * 0.97), (0, h)]
    m.lathe((x, y, z), prof, mat, seg=14, lumpy=0.085, seed=seed)
    m.strand(sagline((x - r * 0.24, y, z + h * 0.885),
                     (x + r * 0.24, y, z + h * 0.885), 0.01, 5),
             0.009, M("mat_rope"), seg=6)


def small_crate(m, x, y, z, w=0.26, d=0.24, h=0.19, rz=0.0, mat=None):
    mat = mat or M("mat_i_crate")
    tb = M("mat_i_beam")
    ca, sa = math.cos(rz), math.sin(rz)
    def P(lx, ly, lz):
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca, z + lz)
    for sy in (-1, 1):
        m.box(P(0, sy * (d / 2 - 0.012), h / 2), (w / 2, 0.012, h / 2), mat, rot=(0, 0, rz))
    for sx in (-1, 1):
        m.box(P(sx * (w / 2 - 0.012), 0, h / 2), (0.012, d / 2, h / 2), mat, rot=(0, 0, rz))
    m.box(P(0, 0, 0.012), (w / 2, d / 2, 0.012), mat, rot=(0, 0, rz))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box(P(sx * (w / 2 - 0.016), sy * (d / 2 - 0.016), h / 2),
                  (0.018, 0.018, h / 2), tb, rot=(0, 0, rz))


def coil_flat(m, x, y, z, r=0.13, n=4):
    rp = M("mat_rope")
    for i in range(n):
        rr = r - i * 0.021
        pts = [(x + rr * math.cos(2 * math.pi * k / 18),
                y + rr * math.sin(2 * math.pi * k / 18), z + 0.018 * i + 0.011)
               for k in range(19)]
        m.strand(pts, 0.0115, rp, seg=5)


# --------------------------------------------------------- shelf stuffing

def fill_shelf(m, x0, x1, yf, yb, z, hmax, seed=0, kind="chandlery"):
    """Walk the board left to right dropping goods with small gaps. Sometimes
    a back row goes in first so the shelf has depth, sometimes items stack."""
    rr = random.Random(hash((round(x0, 3), round(z, 3), seed)) & 0xffffffff)
    yc = (yf + yb) / 2
    x = x0 + 0.06
    while x < x1 - 0.10:
        pick = rr.random()
        if pick < 0.20:
            h = min(0.30, hmax - 0.04)
            jar(m, x + 0.095, yc + rr.uniform(-0.02, 0.02), z, h=h,
                r=rr.uniform(0.078, 0.095),
                mat=rr.choice([M("mat_i_ceramic"), M("mat_i_ceramic_b"),
                               M("mat_i_ceramic_ox"), M("mat_i_ceramic_gn"),
                               M("mat_i_ceramic_bl")]),
                seed=rr.random() * 9, lid=rr.random() < 0.7)
            x += 0.20
        elif pick < 0.36:
            n = rr.randint(2, 3)
            for i in range(n):
                bottle(m, x + 0.055 + i * 0.108, yc + rr.uniform(-0.03, 0.03), z,
                       h=min(0.31, hmax - 0.03), seed=rr.random() * 9,
                       mat=rr.choice([M("mat_i_glass_brown"), M("mat_i_glass_green"),
                                      M("mat_i_glass"), M("mat_i_glass_brown")]))
            x += 0.10 + n * 0.108
        elif pick < 0.52:
            n = rr.randint(2, 3)
            for i in range(n):
                tin(m, x + 0.075, yc + rr.uniform(-0.03, 0.03), z + i * 0.122,
                    mat=rr.choice([M("mat_i_rust"), M("mat_i_copper"), M("mat_i_iron")]))
            if rr.random() < 0.5:
                tin(m, x + 0.20, yc + rr.uniform(-0.03, 0.03), z)
                x += 0.13
            x += 0.17
        elif pick < 0.64:
            candle_bundle(m, x + 0.075, yc, z, n=rr.randint(5, 8),
                          h=min(0.27, hmax - 0.05), seed=rr.random() * 9)
            x += 0.17
        elif pick < 0.74:
            small_crate(m, x + 0.14, yc, z, w=0.26, d=min(0.24, yb - yf - 0.02),
                        h=min(0.20, hmax - 0.03), rz=rr.uniform(-0.06, 0.06),
                        mat=rr.choice([M("mat_i_crate"), M("mat_i_crate_b")]))
            x += 0.30
        elif pick < 0.82:
            for i in range(rr.randint(2, 3)):
                rolled_chart(m, x + 0.05 + i * 0.062, yc + rr.uniform(-0.02, 0.02), z,
                             h=min(0.33, hmax - 0.03), lean=rr.uniform(-0.13, 0.13))
            x += 0.22
        elif pick < 0.90:
            bowl_stack(m, x + 0.10, yc, z, n=rr.randint(2, 4))
            x += 0.23
        else:
            coil_flat(m, x + 0.13, yc, z, r=min(0.125, (yb - yf) / 2 - 0.01),
                      n=rr.randint(2, 3))
            x += 0.29
        x += rr.uniform(0.005, 0.045)


def build_shelf_goods(c):
    m = IMesh("shelf_goods")
    boards = [0.34, 0.82, 1.30, 1.78, 2.26]
    for i, z in enumerate(boards):
        top = z + 0.021
        fill_shelf(m, SHELF_X0 + 0.05, 1.585, SHELF_Y0 + 0.03, SHELF_Y1 - 0.02,
                   top, 0.44, seed=i * 3 + 1)
        fill_shelf(m, 1.66, 2.745, SHELF_Y0 + 0.03, SHELF_Y1 - 0.02,
                   top, 0.44, seed=i * 3 + 2)
        fill_shelf(m, 2.82, SHELF_X1 - 0.05, SHELF_Y0 + 0.03, SHELF_Y1 - 0.02,
                   top, 0.44, seed=i * 3 + 3)
    for i, z in enumerate([0.34, 0.82, 1.30, 1.78, 2.26]):
        fill_shelf(m, 1.20, 1.86, IX - 0.31, IX - 0.03, z + 0.021, 0.44, seed=70 + i)
        fill_shelf(m, 1.98, 2.78, IX - 0.31, IX - 0.03, z + 0.021, 0.44, seed=80 + i)
    return m.finish(c, bevel=0.004, seg=1)


# ------------------------------------------------------------ counter props

def _point(name, loc, energy, color, radius=0.04):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = energy
    d.color = color
    d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d)
    coll("INT_LIGHT").objects.link(o)
    o.location = loc
    return o


def build_counter_props(c):
    m = IMesh("counter_props")
    z = CTR_H
    yc = (CTR_Y0 + CTR_Y1) / 2
    # --- the ledger, open, with a quill and an inkpot ---------------------
    lx, ly = 0.92, yc + 0.02
    m.box((lx, ly, z + 0.022), (0.20, 0.145, 0.022), M("mat_i_leather"),
          rot=(0, 0, 0.13))
    for sx in (-1, 1):
        m.box((lx + sx * 0.098 * math.cos(0.13), ly + sx * 0.098 * math.sin(0.13),
               z + 0.052), (0.098, 0.135, 0.014), M("mat_i_paper"),
              rot=(0, sx * 0.05, 0.13))
    m.box((lx, ly, z + 0.048), (0.016, 0.14, 0.026), M("mat_i_leather"), rot=(0, 0, 0.13))
    m.lathe((lx + 0.30, ly - 0.06, z), [(0, 0), (0.036, 0), (0.040, 0.03),
                                        (0.030, 0.055), (0.020, 0.062), (0, 0.066)],
            M("mat_i_ceramic_b"), seg=12)
    m.strand([(lx + 0.30, ly - 0.06, z + 0.05), (lx + 0.36, ly + 0.02, z + 0.20)],
             0.005, M("mat_i_paper"), seg=5, r2=0.001)
    # --- balance scale ----------------------------------------------------
    sx0, sy0 = 2.30, yc + 0.03
    m.lathe((sx0, sy0, z), [(0, 0), (0.085, 0), (0.090, 0.016), (0.048, 0.026),
                            (0.020, 0.034), (0, 0.036)], M("mat_i_beam"), seg=14)
    m.cyl((sx0, sy0, z + 0.20), 0.014, 0.34, M("mat_i_brass"), seg=10)
    m.box((sx0, sy0, z + 0.375), (0.175, 0.011, 0.011), M("mat_i_brass"), rot=(0.045, 0, 0))
    for s in (-1, 1):
        px = sx0 + s * 0.172
        pz = z + 0.375 + s * 0.008
        for k in range(3):
            a = 2 * math.pi * k / 3
            m.strand([(px, pz * 0 + sy0, pz),
                      (px + 0.052 * math.cos(a), sy0 + 0.052 * math.sin(a), pz - 0.105)],
                     0.0022, M("mat_i_brass"), seg=4)
        m.lathe((px, sy0, pz - 0.115), [(0, 0), (0.030, 0.004), (0.058, 0.016),
                                        (0.058, 0.019), (0.028, 0.008), (0, 0.005)],
                M("mat_i_brass"), seg=14)
    for i, rr in enumerate((0.030, 0.026, 0.022)):
        m.lathe((sx0 - 0.30 + i * 0.072, sy0 - 0.08, z),
                [(0, 0), (rr, 0), (rr * 0.92, 0.042), (rr * 0.45, 0.048), (0, 0.052)],
                M("mat_i_iron"), seg=12)
    # --- brass oil lamp ---------------------------------------------------
    ox_, oy = 3.42, yc + 0.06
    m.lathe((ox_, oy, z), [(0, 0), (0.075, 0), (0.080, 0.014), (0.040, 0.030),
                           (0.036, 0.052), (0.062, 0.075), (0.066, 0.115),
                           (0.050, 0.140), (0.048, 0.150), (0, 0.152)],
            M("mat_i_brass"), seg=16)
    m.lathe((ox_, oy, z + 0.150), [(0.048, 0), (0.058, 0.012), (0.062, 0.11),
                                   (0.050, 0.155)], M("mat_i_lampglass"), seg=16)
    m.lathe((ox_, oy, z + 0.300), [(0.052, 0), (0.058, 0.010), (0.030, 0.038),
                                   (0.014, 0.050), (0, 0.054)], M("mat_i_brass"), seg=14)
    m.lathe((ox_, oy, z + 0.185), [(0, 0), (0.012, 0.008), (0.008, 0.055), (0, 0.070)],
            M("mat_i_flame"), seg=10)
    _point("LAMP_counter", (ox_, oy, z + 0.225), 230.0, (1.0, 0.60, 0.26), radius=0.05)
    # --- everyday counter clutter ----------------------------------------
    coil_flat(m, 1.52, yc + 0.10, z, r=0.095, n=3)
    tin(m, 1.83, yc - 0.10, z, h=0.09, r=0.052, mat=M("mat_i_copper"))
    m.lathe((2.86, yc - 0.11, z), [(0, 0), (0.058, 0.004), (0.075, 0.020),
                                   (0.074, 0.024), (0.056, 0.010), (0, 0.006)],
            M("mat_i_brass"), seg=14)
    for i in range(7):
        m.cyl((2.86 + R.uniform(-0.035, 0.035), yc - 0.11 + R.uniform(-0.035, 0.035),
               z + 0.024 + i * 0.004), 0.012, 0.004, M("mat_i_brass"), seg=8)
    clx, cly = 0.62, yc + 0.04
    m.lathe((clx, cly, z), [(0, 0), (0.070, 0), (0.074, 0.014), (0.058, 0.028),
                            (0.052, 0.040)], M("mat_i_iron"), seg=12)
    m.lathe((clx, cly, z + 0.040), [(0.050, 0), (0.056, 0.010), (0.058, 0.135),
                                    (0.048, 0.170)], M("mat_i_lampglass"), seg=12)
    m.lathe((clx, cly, z + 0.210), [(0.052, 0), (0.056, 0.010), (0.028, 0.036),
                                    (0, 0.050)], M("mat_i_iron"), seg=12)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        m.strand([(clx + 0.054 * math.cos(a), cly + 0.054 * math.sin(a), z + 0.040),
                  (clx + 0.054 * math.cos(a), cly + 0.054 * math.sin(a), z + 0.210)],
                 0.005, M("mat_i_iron"), seg=3)
    m.lathe((clx, cly, z + 0.070), [(0, 0), (0.011, 0.006), (0.007, 0.042), (0, 0.054)],
            M("mat_i_flame"), seg=8)
    _point("LAMP_counter_l", (clx, cly, z + 0.115), 55.0, (1.0, 0.62, 0.28), radius=0.04)
    small_crate(m, 0.98, yc - 0.05, z, w=0.20, d=0.18, h=0.13, rz=0.22,
                mat=M("mat_i_crate_b"))
    for i in range(3):
        m.sphere((0.98 + R.uniform(-0.05, 0.05), yc - 0.05 + R.uniform(-0.04, 0.04),
                  z + 0.145), 0.043, M("mat_i_apple") if i else M("mat_i_apple_g"),
                 seg=12, rings=8)
    # under-counter shelf: stacked ledgers and a spare lantern glass
    for i in range(3):
        m.box((0.75, yc + 0.02, 0.50 + i * 0.036), (0.19, 0.135, 0.018),
              M("mat_i_leather") if i % 2 else M("mat_i_paper"),
              rot=(0, 0, R.uniform(-0.09, 0.09)))
    return m.finish(c, bevel=0.004, seg=1)


# -------------------------------------------------------------- browse zone

def build_oar_stand(c):
    """The corner barrel of oars, poles and boat hooks: the chandlery's
    tallest silhouette and the frame's left-hand repoussoir."""
    m = IMesh("oar_stand")
    bx, by = -3.05, -2.05
    stv, ir = M("mat_i_oxblood"), M("mat_i_iron")
    # coopered barrel, staves individually placed
    n = 18
    rb, hb = 0.40, 0.78
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = rb * (1.0 + 0.055 * math.sin(math.pi * 0.5))
        m.box((bx + rr * math.cos(a), by + rr * math.sin(a), hb / 2),
              (0.075, 0.024, hb / 2), stv, rot=(0, 0, a + math.pi / 2),
              jitter=0.012)
    for hz in (0.07, 0.40, 0.71):
        m.lathe((bx, by, hz), [(rb * 1.02, 0), (rb * 1.06, 0.012),
                               (rb * 1.06, 0.052), (rb * 1.02, 0.064)], ir, seg=20)
    poles = [(-0.17, -0.10, 2.44, 0.055, "oar"), (0.02, -0.16, 2.62, 0.052, "oar"),
             (0.17, -0.02, 2.28, 0.048, "pole"), (-0.05, 0.14, 2.72, 0.050, "oar"),
             (0.13, 0.18, 2.16, 0.044, "hook"), (-0.19, 0.08, 2.36, 0.046, "pole"),
             (0.00, 0.00, 2.55, 0.050, "pole")]
    wood = [M("mat_i_beam"), M("mat_i_shelf"), M("mat_i_counter")]
    for i, (dx, dy, ln, r, kind) in enumerate(poles):
        lean_x = R.uniform(-0.10, 0.10)
        lean_y = R.uniform(-0.08, 0.08)
        base = Vector((bx + dx, by + dy, 0.30))
        tipv = base + Vector((math.sin(lean_x) * ln, math.sin(lean_y) * ln,
                              math.cos(lean_x) * ln))
        w = wood[i % 3]
        m.strand([tuple(base), tuple(tipv)], r, w, seg=9, r2=r * 0.82)
        if kind == "oar":
            d = (tipv - base).normalized()
            bl0 = tipv - d * 0.62
            e = d.to_track_quat("Z", "Y").to_euler()
            m.box(tuple((bl0 + tipv) / 2), (0.098, 0.016, 0.31), w,
                  rot=(e.x, e.y, e.z + R.uniform(0, 3.1)))
        elif kind == "hook":
            d = (tipv - base).normalized()
            m.strand([tuple(tipv - d * 0.10), tuple(tipv + Vector((0.10, 0.03, 0.04)))],
                     0.020, ir, seg=6)
        else:
            m.cyl(tuple(tipv - (tipv - base).normalized() * 0.05), r * 1.18, 0.09, ir,
                  seg=10, rot=(lean_y, lean_x, 0))
    return m.finish(c, bevel=0.006)


def build_wares_left(c, kit):
    """Browsable stock down the left side: open crates, sacks, barrels."""
    m = IMesh("wares_left")
    made = []

    # open crate of apples, lid propped against it
    cx, cy = -2.42, -0.62
    w, d, h = 0.62, 0.54, 0.44
    for sy in (-1, 1):
        m.box((cx, cy + sy * (d / 2), h / 2), (w / 2, 0.018, h / 2), M("mat_i_crate"),
              rot=(0, 0, 0.10))
    for sx in (-1, 1):
        m.box((cx + sx * (w / 2) * math.cos(0.10), cy + sx * (w / 2) * math.sin(0.10),
               h / 2), (0.018, d / 2, h / 2), M("mat_i_crate"), rot=(0, 0, 0.10))
    m.box((cx, cy, 0.02), (w / 2, d / 2, 0.02), M("mat_i_crate"), rot=(0, 0, 0.10))
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.box((cx + sx * 0.28, cy + sy * 0.24, h / 2), (0.026, 0.026, h / 2),
                  M("mat_i_beam"), rot=(0, 0, 0.10))
    m.box((cx - 0.02, cy - 0.40, 0.30), (w / 2, 0.022, 0.28), M("mat_i_crate_b"),
          rot=(0.30, 0, 0.10))
    m.box((cx - 0.02, cy - 0.42, 0.30), (0.055, 0.018, 0.30), M("mat_i_oxblood"),
          rot=(0.30, 0, 0.10))
    # straw + apples heaped to the rim
    for i in range(34):
        a = R.uniform(0, 2 * math.pi)
        rr = R.uniform(0, 0.235)
        m.sphere((cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.86,
                  0.36 + R.uniform(0, 0.09) - rr * 0.20), R.uniform(0.040, 0.052),
                 M("mat_i_apple") if R.random() < 0.72 else M("mat_i_apple_g"),
                 seg=12, rings=8, rot=(R.uniform(0, 3), 0, R.uniform(0, 3)))

    # open provisions barrel with sacks and roots
    bx, by = -3.32, 0.60
    n, rb, hb = 18, 0.36, 0.72
    for i in range(n):
        a = 2 * math.pi * i / n
        m.box((bx + rb * math.cos(a), by + rb * math.sin(a), hb / 2),
              (0.068, 0.022, hb / 2), M("mat_i_crate"), rot=(0, 0, a + math.pi / 2),
              jitter=0.012)
    for hz in (0.06, 0.62):
        m.lathe((bx, by, hz), [(rb * 1.03, 0), (rb * 1.07, 0.012), (rb * 1.07, 0.048),
                               (rb * 1.03, 0.058)], M("mat_i_iron"), seg=20)
    for i in range(9):
        a = R.uniform(0, 6.28)
        rr = R.uniform(0, 0.21)
        m.lathe((bx + rr * math.cos(a), by + rr * math.sin(a), 0.55 + R.uniform(0, 0.06)),
                [(0, 0), (0.05, 0.02), (0.062, 0.07), (0.038, 0.12), (0, 0.14)],
                M("mat_i_ceramic_b"), seg=10, lumpy=0.14, seed=i * 2.1,
                aspect=(1.0, 0.78), rot=R.uniform(0, 3))

    # sacks slumped against the left wall
    for i, (sx, sy, hh, rrad) in enumerate(((-3.55, 1.62, 0.44, 0.215),
                                            (-3.30, 1.95, 0.40, 0.195),
                                            (-3.62, -1.05, 0.42, 0.205))):
        sack(m, sx, sy, 0.0, h=hh, r=rrad, seed=i * 3.3,
             mat=M("mat_i_burlap") if i != 1 else M("mat_i_canvas"))
    made.append(m.finish(c, bevel=0.006, seg=1))

    # kit crates and barrels, reskinned for the interior palette
    ck, bk = kit["kit_crate"], kit["kit_barrel"]
    reskin(ck, {"mat_wallwood_dark": "mat_i_crate", "mat_timber": "mat_i_beam"})
    reskin(bk, {"mat_wallwood_dark": "mat_i_oxblood"})
    for (x, y, z, rz) in ((-1.42, 1.62, 0.043, 0.24), (-1.36, 1.55, 0.735, -0.42),
                          (-3.46, 2.46, 0.043, 0.16), (-1.68, 2.34, 0.043, -0.30),
                          (-1.64, 2.30, 0.735, 0.52)):
        made.append(pb.place(ck, (x, y, z), rot=(0, 0, rz), c=c, jitter=0.02))
    for (x, y, rz) in ((-1.86, 0.52, 0.4), (-3.30, -1.72, 1.1)):
        made.append(pb.place(bk, (x, y, 0.0), rot=(0, 0, rz), c=c, jitter=0.02))
    rc = kit["kit_rope_coil"]
    for (x, y, z) in ((-1.86, 0.52, 0.90), (-1.36, 1.55, 1.43)):
        made.append(pb.place(rc, (x, y, z), c=c, jitter=0.15))
    return made


def build_wares_right(c, kit):
    """Right foreground: a peg rack of cordage and buckets over stacked stock.
    This is the repoussoir on the camera's right; the weapon shop swaps the
    contents for a rack of hafted weapons without touching the geometry."""
    m = IMesh("wares_right")
    made = []
    g, bm_, ir = M("mat_i_green"), M("mat_i_beam"), M("mat_i_iron")
    # peg rail on the right wall, front half
    m.box((IX - 0.045, -1.62, 1.72), (0.045, 1.05, 0.055), g)
    pegs = [-2.52, -2.16, -1.80, -1.44, -1.08, -0.72]
    for i, py in enumerate(pegs):
        m.cyl((IX - 0.14, py, 1.76), 0.022, 0.20, bm_, seg=8, rot=(0, math.pi / 2, 0))
    # hanging coils and buckets on the pegs
    for i, py in enumerate(pegs):
        if i % 2 == 0:
            for k in range(3):
                rr = 0.20 - k * 0.032
                pts = [(IX - 0.20 - 0.012 * k + rr * math.sin(2 * math.pi * t / 16) * 0.28,
                        py + rr * math.cos(2 * math.pi * t / 16),
                        1.74 - rr + rr * (1 - math.cos(2 * math.pi * t / 16)) * 0.0)
                       for t in range(17)]
                pts = [(px, pyy, 1.74 - rr * (1 - math.cos(2 * math.pi * t / 16)))
                       for t, (px, pyy, _) in enumerate(pts)]
                m.strand(pts, 0.0135, M("mat_rope"), seg=5)
        else:
            m.strand([(IX - 0.16, py, 1.74), (IX - 0.30, py, 1.50)], 0.010,
                     M("mat_rope"), seg=4)
            m.lathe((IX - 0.30, py, 1.10), [(0, 0), (0.10, 0.0), (0.115, 0.03),
                                            (0.145, 0.28), (0.150, 0.30), (0, 0.30)],
                    M("mat_i_crate_b"), seg=14)
            m.lathe((IX - 0.30, py, 1.36), [(0.146, 0), (0.152, 0.012),
                                            (0.152, 0.040), (0.146, 0.050)], ir, seg=14)
    m.box((IX - 0.17, -1.62, 2.12), (0.17, 1.12, 0.022), M("mat_i_shelf"))
    for by in (-2.64, -0.58):
        m.box((IX - 0.17, by, 1.95), (0.17, 0.030, 0.19), bm_)
    for i in range(5):
        m.box((IX - 0.20, -2.44 + i * 0.44, 1.96), (0.11, 0.055, 0.13), bm_,
              rot=(0, math.radians(-38), 0))
    for i, by in enumerate((-2.46, -2.02, -1.58, -1.14, -0.70)):
        if i % 2:
            small_crate(m, IX - 0.19, by, 2.142, w=0.30, d=0.34, h=0.22,
                        rz=math.radians(90), mat=M("mat_i_crate_b"))
        else:
            coil_flat(m, IX - 0.19, by, 2.142, r=0.14, n=3)
    made.append(m.finish(c, bevel=0.006, seg=1))

    ck, bk, bu = kit["kit_crate"], kit["kit_barrel"], kit["kit_bucket"]
    reskin(bu, {"mat_wallwood_dark": "mat_i_crate_b"})
    for (x, y, z, rz) in ((3.50, -2.42, 0.043, -0.18), (3.44, -2.36, 0.735, 0.34),
                          (2.72, -2.58, 0.043, 0.44)):
        made.append(pb.place(ck, (x, y, z), rot=(0, 0, rz), c=c, jitter=0.02))
    for (x, y, rz) in ((3.46, -1.28, 2.6), (2.86, -1.86, 0.7)):
        made.append(pb.place(bk, (x, y, 0.0), rot=(0, 0, rz), c=c, jitter=0.02))
    for (x, y, z) in ((2.72, -2.58, 0.79), (3.10, -1.14, 0.0)):
        made.append(pb.place(bu, (x, y, z), c=c, jitter=0.10))
    made.append(pb.place(kit["kit_rope_coil"], (3.46, -1.28, 0.905), c=c, jitter=0.2))
    return made


def build_dressing(c, kit):
    """The stuff that turns a stocked room into a shop somebody works in:
    a dresser in the dead bay beside the door, pegs on the left wall, a stool
    behind the counter, straw and spillage on the floor."""
    m = IMesh("dressing")
    made = []
    sh, shb = M("mat_i_shelf"), M("mat_i_shelf_b")
    g, ox, bm_, ir = M("mat_i_green"), M("mat_i_oxblood"), M("mat_i_beam"), M("mat_i_iron")

    # --- narrow dresser in the bay between the door and the main shelving --
    dx0, dx1 = -1.28, 0.28
    dy0, dy1 = IY - 0.34, IY
    for z in (0.42, 0.90, 1.38, 1.86):
        m.box(((dx0 + dx1) / 2, (dy0 + dy1) / 2, z), ((dx1 - dx0) / 2, 0.17, 0.020),
              sh if z in (0.42, 1.38) else shb)
        m.box(((dx0 + dx1) / 2, dy0 + 0.012, z + 0.032), ((dx1 - dx0) / 2, 0.012, 0.022), g)
    for ux in (dx0 + 0.032, dx1 - 0.032):
        m.box((ux, (dy0 + dy1) / 2, 1.10), (0.032, 0.17, 1.10), shb)
    m.box(((dx0 + dx1) / 2, dy1 - 0.04, 2.02), ((dx1 - dx0) / 2 + 0.03, 0.04, 0.10), ox)
    for i, z in enumerate((0.44, 0.92, 1.40, 1.88)):
        fill_shelf(m, dx0 + 0.05, dx1 - 0.05, dy0 + 0.03, dy1 - 0.02, z, 0.44,
                   seed=40 + i)

    # --- peg rail on the LEFT wall, front half (mirrors the right-hand rail)
    m.box((-IX + 0.045, -1.55, 1.58), (0.045, 1.10, 0.055), g)
    for i, py in enumerate((-2.42, -2.02, -1.62, -1.22, -0.82)):
        m.cyl((-IX + 0.14, py, 1.62), 0.022, 0.20, bm_, seg=8, rot=(0, math.pi / 2, 0))
        if i % 2:
            for k in range(3):
                rr = 0.19 - k * 0.030
                pts = [(-IX + 0.20 + 0.012 * k + rr * math.sin(2 * math.pi * t / 16) * 0.30,
                        py + rr * math.cos(2 * math.pi * t / 16),
                        1.60 - rr * (1 - math.cos(2 * math.pi * t / 16)))
                       for t in range(17)]
                m.strand(pts, 0.0135, M("mat_rope"), seg=5)
        else:
            m.strand([(-IX + 0.16, py, 1.60), (-IX + 0.30, py, 1.40)], 0.010,
                     M("mat_rope"), seg=4)
            m.lathe((-IX + 0.30, py, 1.06), [(0, 0), (0.075, 0.0), (0.085, 0.02),
                                             (0.105, 0.24), (0.108, 0.26), (0, 0.26)],
                    M("mat_i_copper") if i else M("mat_i_crate_b"), seg=14)

    # --- tapped oil barrel on a cradle: the chandlery premise, in one prop --
    obx, oby, obz = -0.06, 0.66, 0.62
    bh, br = 0.66, 0.315
    for i in range(18):
        a = 2 * math.pi * i / 18
        m.box((obx, oby + br * math.cos(a), obz + br * math.sin(a)),
              (bh / 2, 0.060, 0.023), ox, rot=(a + math.pi / 2, 0, 0), jitter=0.010)
    for hx in (-bh / 2 + 0.10, 0.0, bh / 2 - 0.10):
        for i in range(20):
            a = 2 * math.pi * i / 20
            m.box((obx + hx, oby + br * 1.05 * math.cos(a), obz + br * 1.05 * math.sin(a)),
                  (0.028, 0.052, 0.012), ir, rot=(a + math.pi / 2, 0, 0))
    for hx in (-bh / 2 - 0.012, bh / 2 + 0.012):
        m.cyl((obx + hx, oby, obz), br * 0.97, 0.026, M("mat_i_crate"), seg=20,
              rot=(0, math.pi / 2, 0))
    for s_ in (-1, 1):                                        # cradle
        m.box((obx + s_ * 0.36, oby, 0.145), (0.052, 0.30, 0.145), bm_)
        for e_ in (-1, 1):
            m.box((obx + s_ * 0.36, oby + e_ * 0.215, 0.375), (0.048, 0.075, 0.105),
                  bm_, rot=(math.radians(-24) * e_, 0, 0))
    m.box((obx, oby, 0.042), (0.44, 0.30, 0.042), g)
    m.cyl((obx, oby - br - 0.055, 0.50), 0.023, 0.14, M("mat_i_brass"), seg=10,
          rot=(math.pi / 2, 0, 0))                            # spigot
    m.cyl((obx, oby - br - 0.105, 0.545), 0.011, 0.075, M("mat_i_brass"), seg=8)
    m.lathe((obx, oby - br - 0.15, 0.0), [(0, 0), (0.10, 0.0), (0.115, 0.03),
                                          (0.145, 0.26), (0.150, 0.28), (0, 0.28)],
            M("mat_i_crate_b"), seg=14)                       # catch bucket
    m.lathe((obx, oby - br - 0.15, 0.23), [(0.146, 0), (0.152, 0.012),
                                           (0.152, 0.040), (0.146, 0.050)], ir, seg=14)
    m.box((obx, oby - br - 0.010, 0.90), (0.23, 0.013, 0.095), ox)
    m.box((obx, oby - br - 0.022, 0.90), (0.19, 0.008, 0.062), M("mat_i_label"))

    # --- a coir mat inside the door, marking the entry pad ----------------
    for i in range(22):
        yy = 2.10 + 0.028 * i
        m.strand([(DOOR_X - 0.52, yy, 0.006), (DOOR_X + 0.52, yy, 0.006)],
                 0.011, M("mat_i_net"), seg=4)
    for i in range(9):
        xx = DOOR_X - 0.50 + 0.125 * i
        m.strand([(xx, 2.09, 0.010), (xx, 2.70, 0.010)], 0.010, M("mat_i_net"), seg=4)

    # --- notices nailed up beside the door --------------------------------
    for (nx, nz, nw, nh, rr_) in ((-3.62, 1.66, 0.095, 0.125, 0.05),
                                  (-3.36, 1.52, 0.075, 0.095, -0.09),
                                  (-3.58, 1.28, 0.082, 0.065, 0.03)):
        m.box((nx, IY - 0.010, nz), (nw, 0.010, nh), M("mat_i_paper"), rot=(0, rr_, 0))
        for k in range(3):
            m.box((nx + R.uniform(-nw * 0.5, nw * 0.5), IY - 0.021,
                   nz + (k - 1) * nh * 0.5), (nw * R.uniform(0.3, 0.6), 0.003, 0.005),
                  M("mat_i_iron"))

    # --- a stool the shopkeep never sits on, behind the counter -----------
    sx, sy = 1.72, 2.06
    m.lathe((sx, sy, 0.56), [(0, 0), (0.19, 0.0), (0.20, 0.018), (0.19, 0.030),
                             (0, 0.032)], sh, seg=16)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        m.strand([(sx + 0.145 * math.cos(a), sy + 0.145 * math.sin(a), 0.0),
                  (sx + 0.085 * math.cos(a), sy + 0.085 * math.sin(a), 0.56)],
                 0.026, bm_, seg=6)
    # a ledger and a mug abandoned on it
    m.box((sx, sy, 0.60), (0.14, 0.10, 0.016), M("mat_i_leather"), rot=(0, 0, 0.4))

    # --- broom leaning by the door ---------------------------------------
    bxx, byy = DOOR_X + 0.80, IY - 0.16
    top = Vector((bxx + 0.16, byy - 0.42, 1.62))
    bot = Vector((bxx, byy - 0.02, 0.02))
    m.strand([tuple(bot), tuple(top)], 0.019, bm_, seg=8)
    d = (top - bot).normalized()
    for k in range(16):
        a = 2 * math.pi * k / 16
        m.strand([tuple(bot + d * 0.30),
                  (bot.x + 0.10 * math.cos(a), bot.y + 0.10 * math.sin(a), 0.01)],
                 0.010, M("mat_i_net"), seg=4, r2=0.004)

    # --- chalked price board over the dresser -----------------------------
    m.box((-0.50, IY - 0.025, 2.44), (0.44, 0.025, 0.30), ox)
    m.box((-0.50, IY - 0.055, 2.44), (0.38, 0.012, 0.245), M("mat_tar"))
    for i in range(6):
        m.box((-0.50 + R.uniform(-0.26, 0.26), IY - 0.070,
               2.30 + i * 0.075), (R.uniform(0.05, 0.17), 0.004, 0.009),
              M("mat_i_label"))

    # --- crossed oars over the door: the chandler's trade sign ------------
    for s_ in (-1, 1):
        m.strand([(DOOR_X - s_ * 0.92, IY - 0.075, 2.21),
                  (DOOR_X + s_ * 0.92, IY - 0.075, 2.84)], 0.029, bm_, seg=6)
        m.box((DOOR_X + s_ * 0.735, IY - 0.104, 2.74), (0.115, 0.019, 0.30), sh,
              rot=(0, math.radians(20) * s_, 0))
    m.box((DOOR_X, IY - 0.048, 2.53), (0.070, 0.048, 0.070), g)

    # --- browse island: a trestle of open stock in the middle of the aisle.
    # The weapon shop swaps the trestle top for a blade rack, same footprint.
    tx0, tx1, ty0, ty1, th = -2.10, -0.62, -1.20, -0.38, 0.76
    tcx, tcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    m.box((tcx, tcy, th), ((tx1 - tx0) / 2, (ty1 - ty0) / 2, 0.024), M("mat_i_counter"))
    for ex in (tx0 + 0.16, tx1 - 0.16):
        for ey in (ty0 + 0.12, ty1 - 0.12):
            m.strand([(ex, ey, 0.0), (ex, ey, th - 0.024)], 0.030, bm_, seg=6)
        m.box((ex, tcy, 0.30), (0.030, (ty1 - ty0) / 2 - 0.10, 0.026), g)
    m.box((tcx, tcy, 0.34), ((tx1 - tx0) / 2 - 0.14, 0.026, 0.024), bm_)
    m.box((tcx, ty0 + 0.02, 0.90), ((tx1 - tx0) / 2 - 0.06, 0.018, 0.085), ox)
    small_crate(m, tx0 + 0.34, tcy + 0.03, th + 0.024, w=0.44, d=0.40, h=0.24,
                rz=0.12, mat=M("mat_i_crate_b"))
    for i in range(11):
        a = R.uniform(0, 6.28)
        rr = R.uniform(0, 0.15)
        m.sphere((tx0 + 0.34 + rr * math.cos(a), tcy + 0.03 + rr * math.sin(a),
                  th + 0.215 + R.uniform(0, 0.05)), R.uniform(0.042, 0.052),
                 M("mat_i_apple_g") if i % 3 else M("mat_i_apple"), seg=12, rings=8)
    sack(m, tx0 + 0.86, ty0 + 0.30, th + 0.024, h=0.30, r=0.150, seed=7.1)
    for i in range(3):
        tin(m, tx1 - 0.46, ty1 - 0.22, th + 0.024 + i * 0.122,
            mat=M("mat_i_rust") if i % 2 else M("mat_i_copper"))
    jar(m, tx1 - 0.20, ty0 + 0.20, th + 0.024, h=0.24, r=0.076,
        mat=M("mat_i_ceramic_ox"), seed=3.3)
    coil_flat(m, tx1 - 0.20, ty1 - 0.20, th + 0.024, r=0.105, n=3)
    bowl_stack(m, tx0 + 0.84, ty1 - 0.20, th + 0.024, n=4)

    # --- straw, sawdust wisps and floor spill ----------------------------
    straw = M("mat_i_straw")
    for i in range(190):
        x = R.uniform(-IX + 0.1, IX - 0.1)
        y = R.uniform(YF + 0.2, IY - 0.1)
        # denser where goods are handled: the aisle mouth and the counter front
        if R.random() > 0.30 + 0.70 * math.exp(-((x - 1.9) ** 2 + (y + 0.2) ** 2) / 2.2):
            continue
        a = R.uniform(0, math.pi)
        ln = R.uniform(0.05, 0.155)
        m.strand([(x, y, 0.004),
                  (x + ln * math.cos(a), y + ln * math.sin(a), 0.004)],
                 0.0040, straw, seg=3)
    made.append(m.finish(c, bevel=0.004, seg=1))

    hw_ = IMesh("hawser")
    hx, hy = 1.08, -1.92
    for k in range(5):
        rr = 0.44 - k * 0.075
        pts = [(hx + rr * math.cos(2 * math.pi * t / 26),
                hy + rr * math.sin(2 * math.pi * t / 26) * 0.92,
                0.036 + k * 0.062) for t in range(27)]
        hw_.strand(pts, 0.034, M("mat_rope"), seg=6)
    hw_.strand(sagline((hx + 0.44, hy, 0.036), (hx + 0.95, hy - 0.42, 0.034), 0.02, 6),
               0.034, M("mat_rope"), seg=6)
    made.append(hw_.finish(c, bevel=0.006, seg=1))

    # --- foreground floor stock, kept clear of the door/counter lane ------
    ck, bk = kit["kit_crate"], kit["kit_barrel"]
    for (x, y, z, rz) in ((-1.72, -2.55, 0.043, -0.35),):
        made.append(pb.place(ck, (x, y, z), rot=(0, 0, rz), c=c, jitter=0.02))
    made.append(pb.place(bk, (-2.28, -2.62, 0.0), rot=(0, 0, 1.9), c=c, jitter=0.02))
    for (x, y, z) in ((-1.72, -2.55, 0.70), (3.02, -2.15, 0.0)):
        made.append(pb.place(kit["kit_rope_coil"], (x, y, z), c=c, jitter=0.25))
    return made


def build_window_bench(c, kit):
    """Low bench under the dusk window -- keeps the left wall from going dead
    and gives the light shaft something to land on."""
    m = IMesh("window_bench")
    bm_, g = M("mat_i_beam"), M("mat_i_green")
    x = -IX + 0.24
    m.box((x, WIN_Y, 0.60), (0.24, 0.62, 0.022), M("mat_i_shelf"))
    for sy in (-1, 1):
        m.box((x, WIN_Y + sy * 0.56, 0.30), (0.20, 0.035, 0.30), g)
    m.box((x, WIN_Y, 0.14), (0.20, 0.56, 0.020), M("mat_i_shelf_b"))
    # a copper measure, a funnel, a stack of tins on the bench
    m.lathe((x, WIN_Y - 0.30, 0.622), [(0, 0), (0.085, 0), (0.092, 0.02),
                                       (0.086, 0.20), (0.070, 0.225), (0, 0.228)],
            M("mat_i_copper"), seg=14)
    m.lathe((x + 0.02, WIN_Y + 0.02, 0.622), [(0, 0), (0.022, 0), (0.024, 0.12),
                                              (0.115, 0.24), (0.118, 0.25), (0, 0.25)],
            M("mat_i_copper"), seg=14)
    for i in range(3):
        tin(m, x - 0.02, WIN_Y + 0.34, 0.622 + i * 0.122,
            mat=M("mat_i_rust") if i % 2 else M("mat_i_copper"))
    for i in range(4):
        m.lathe((x + R.uniform(-0.08, 0.08), WIN_Y + R.uniform(-0.45, 0.45), 0.16),
                [(0, 0), (0.055, 0.01), (0.062, 0.16), (0.048, 0.19), (0, 0.20)],
                M("mat_i_ceramic_gn") if i % 2 else M("mat_i_ceramic_ox"), seg=12)
    return m.finish(c, bevel=0.006, seg=1)


# ---------------------------------------------------------------- hanging

def build_hanging(c, kit):
    """Goods slung from the ceiling beams: the FF9 chandlery signature."""
    m = IMesh("hanging_goods")
    made = []
    rp, ir = M("mat_rope"), M("mat_i_iron")
    bz = BEAM_Z - BEAM_H          # underside of the beams

    # --- fishing nets bundled on the front beam ---------------------------
    # Two dead ends before this: long irregular catenaries read as cobweb, and
    # a taut regular grid read as a white ladder hanging in mid air. A net in a
    # chandlery is STORED, not set: gathered at the beam and falling in folds.
    # Folds also mean no long straight highlight for the lantern to catch.
    def nethank(cx, cy, span, ztop, drop, n=26, seed=0.0, mat=None):
        mat = mat or M("mat_i_net_d")
        rr = random.Random(int(seed * 977) & 0xffff)
        cols = []
        for i in range(n):
            t = i / (n - 1)
            gx = cx + (t - 0.5) * span
            fold = math.sin(t * math.pi * 3.4 + seed)           # the hanging folds
            dz = drop * (0.55 + 0.45 * abs(math.sin(t * math.pi * 1.7 + seed * 0.7)))
            pts = sagline((gx, cy + 0.02 * fold, ztop),
                          (gx + 0.10 * fold + rr.uniform(-0.03, 0.03),
                           cy - 0.30 - 0.13 * fold, ztop - dz),
                          0.10 + 0.05 * abs(fold), 7)
            m.strand(pts, 0.0075, mat, seg=4)
            cols.append(pts)
        # cross ties every few strands, following the folds -> reads as mesh
        for lvl in range(1, 7):
            f = lvl / 7.0
            row = []
            for pts in cols:
                k = min(len(pts) - 1, int(f * (len(pts) - 1)))
                row.append(pts[k])
            for a, b in zip(row[:-1], row[1:]):
                m.strand([a, (((a[0] + b[0]) / 2), (a[1] + b[1]) / 2 - 0.02,
                              (a[2] + b[2]) / 2 - 0.035), b], 0.0068, mat, seg=3)
        # head rope along the beam, and a couple of cork floats caught in it
        m.strand(sagline((cx - span / 2, cy + 0.02, ztop + 0.01),
                         (cx + span / 2, cy + 0.02, ztop + 0.01), 0.02, 6),
                 0.016, rp, seg=4)
        for k in range(3):
            m.lathe((cx + (k - 1) * span * 0.28, cy - 0.26,
                     ztop - drop * (0.42 + 0.16 * k)),
                    [(0, 0), (0.052, 0.028), (0.058, 0.058), (0, 0.082)],
                    M("mat_i_crate_b"), seg=10)

    nethank(-1.82, BEAM_Y[0] + 0.03, 1.34, bz - 0.03, 0.92, n=28, seed=1.7)
    nethank(-3.22, BEAM_Y[0] + 0.03, 0.62, bz - 0.05, 0.66, n=14, seed=4.1,
            mat=M("mat_i_net"))

    # --- a line of dried fish under the second beam -----------------------
    fy = BEAM_Y[1] - 0.32
    line = sagline((0.30, fy, bz - 0.16), (3.30, fy, bz - 0.16), 0.14, 14)
    m.strand(line, 0.008, rp, seg=5)
    for i in range(9):
        t = (i + 0.5) / 9.0
        k = int(t * 14)
        px, py, pz = line[k]
        ln = R.uniform(0.30, 0.40)
        tilt = R.uniform(-0.12, 0.12)
        m.lathe((px, py, pz - ln), [(0, 0), (0.020, ln * 0.10), (0.042, ln * 0.38),
                                    (0.046, ln * 0.55), (0.030, ln * 0.82),
                                    (0.011, ln * 0.95), (0, ln)],
                M("mat_i_fish"), seg=10, aspect=(1.0, 0.42), rot=tilt)
        m.box((px, py, pz - ln + 0.012), (0.055, 0.006, 0.030), M("mat_i_fish"),
              rot=(0, 0.5, tilt))
        m.strand([(px, py, pz), (px, py, pz - 0.04)], 0.0035, rp, seg=3)

    # --- coiled lines and a spare block-and-tackle hung from beams --------
    for (hx, hy, rr, n) in ((3.42, BEAM_Y[0] + 0.02, 0.26, 4),
                            (-0.62, BEAM_Y[2] - 0.05, 0.22, 3),
                            (1.05, BEAM_Y[0] + 0.03, 0.21, 3)):
        m.strand([(hx, hy, bz), (hx, hy, bz - 0.16)], 0.010, rp, seg=4)
        for k in range(n):
            r2 = rr - k * 0.030
            top = bz - 0.16 - k * 0.055
            pts = [(hx + r2 * math.sin(2 * math.pi * t / 18) * 0.34,
                    hy + r2 * math.cos(2 * math.pi * t / 18),
                    top - r2 * (1 - math.cos(2 * math.pi * t / 18)))
                   for t in range(19)]
            m.strand(pts, 0.0135, rp, seg=5)
    # block and tackle
    tx, ty = 2.30, BEAM_Y[2] + 0.05
    m.strand([(tx, ty, bz), (tx, ty, bz - 0.22)], 0.008, rp, seg=4)
    m.box((tx, ty, bz - 0.30), (0.045, 0.035, 0.075), M("mat_i_beam"))
    m.cyl((tx, ty, bz - 0.30), 0.030, 0.078, ir, seg=12, rot=(0, math.pi / 2, 0))
    # bunches of dried herbs / oakum near the door
    for (hx, hy) in ((-1.55, BEAM_Y[2] + 0.02), (-3.25, BEAM_Y[1] - 0.04)):
        m.strand([(hx, hy, bz), (hx, hy, bz - 0.14)], 0.007, rp, seg=3)
        for k in range(11):
            a = 2 * math.pi * k / 11
            m.strand([(hx, hy, bz - 0.14),
                      (hx + 0.075 * math.cos(a), hy + 0.075 * math.sin(a), bz - 0.44)],
                     0.010, M("mat_i_net"), seg=5, r2=0.003)
    made.append(m.finish(c, bevel=0.004, seg=1))

    # --- lanterns: the warm pools. Ordinary flame, no magic. --------------
    lamp = kit["kit_lantern_hanging"]
    reskin(lamp, {"mat_lantern_glass": "mat_i_lampglass"})
    hooks = IMesh("lantern_hooks")
    for (lx, ly, energy, drop) in ((-2.20, BEAM_Y[0] - 0.02, 520.0, 0.30),
                                   (2.55, BEAM_Y[1] + 0.02, 700.0, 0.58),
                                   (-0.55, BEAM_Y[2] + 0.02, 470.0, 0.30),
                                   (3.20, BEAM_Y[0] + 0.04, 330.0, 0.30),
                                   (-0.34, BEAM_Y[1] + 0.02, 360.0, 0.74)):
        hooks.strand([(lx, ly, bz), (lx, ly, bz - drop)], 0.007, ir, seg=4)
        o = pb.place_lantern(lamp, (lx, ly, bz - drop - 0.352), c=c, energy=energy)
        made.append(o)
    made.append(hooks.finish(c, bevel=0.004))
    return made


# ------------------------------------------------------------------- pads

def build_shadow_ceiling(c):
    """A roof the camera cannot see.

    The cutaway has no ceiling and no near wall, so any directional light
    floods the room from above and from the front, and there is nothing for
    the lantern light to bounce off overhead. A plane with visible_camera off
    fixes both: the window becomes the sun's only aperture, and the room
    finally gets a top bounce. It is NOT set dressing -- it never renders.
    """
    m = IMesh("shadow_ceiling")
    m.box((0, 0.08, 3.06), (HW + 0.15, (YB + 2.95) / 2, 0.05), M("mat_i_beam"))
    ob = m.finish(c, bevel=0)
    ob.visible_camera = False
    return ob


def build_pads(c):
    """Interaction metadata, not set dressing: real objects in the blend so the
    exporter can find them, hidden from the beauty render."""
    out = []
    for name, (cx, cy, w, d) in {
            "walk_pad_door": (DOOR_X, 2.28, 1.20, 0.95),
            "walk_pad_counter": (2.10, -0.30, 1.70, 1.00)}.items():
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

def setup_light(c, dusk=130.0, world=0.22, fog=0.0125, fill=50.0, sky=90.0,
                winfill=95.0):
    lc = coll("INT_LIGHT")
    for n in ("SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX"):
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        lc.objects.link(o)

    kb = _mod("kit_build")
    kb.setup_world(density=0.0)                 # bounded FOG_BOX only, never world
    nt = bpy.context.scene.world.node_tree
    ramp = next(n for n in nt.nodes if n.type == "VALTORGB").color_ramp
    ramp.elements[0].color = (0.10, 0.09, 0.10, 1)
    ramp.elements[1].color = (0.11, 0.13, 0.17, 1)
    ramp.elements[2].color = (0.13, 0.18, 0.29, 1)   # cool dusk outside
    next(n for n in nt.nodes if n.type == "BACKGROUND").inputs["Strength"] \
        .default_value = world

    # A low sun down the gorge, admitted ONLY by the window.
    #
    # Getting here took three tries. An AREA lamp outside the pane spilled most
    # of its output onto the wall's outer face (visible in frame as a light
    # leak) and what did get through was too diffuse to read as a shaft. What a
    # window shaft needs is parallel rays, i.e. a SUN -- but a room with no
    # roof and no near wall lets a sun in from everywhere. Hence the
    # camera-invisible shadow ceiling built above: it makes the window the only
    # aperture the sun can use, and as a bonus it bounces the lantern light
    # back down, which no amount of extra lamps was doing.
    #
    # Direction is chosen so the patch lands on the counter approach, and so it
    # clears the stock in the aisle. Checked with a ray cast, not by eye.
    sun = bpy.data.objects["SUN_key"]
    sun.hide_render = False
    # NOTE kit_wall_window inherits wall_frame's MID RAIL, a 0.12 timber that
    # runs straight across the opening at z 1.50-1.62 -- i.e. across the middle
    # of the glass. Aim through the lower light of the sash, not the centre.
    #
    # Aim: at a shallow dusk elevation, a shaft that lands on the FLOOR or on
    # the counter TOP arrives at ~6 deg grazing incidence and reads as almost
    # nothing however hard the lamp is driven. The surfaces facing the window
    # take the beam nearly square, so the shaft is aimed at the RIGHT WALL:
    # a window-shaped patch at eye height, with the sash bars and the hanging
    # lantern printed across it. Path verified by ray cast, not by eye.
    sun.location = (-HW - 1.34, WIN_Y + 0.74, 2.15)
    ru.aim(sun, (IX, -1.20, 1.50))
    sun.data.energy = dusk
    sun.data.color = (1.0, 0.60, 0.38)
    sun.data.angle = math.radians(1.4)

    # a soft fill hugging the inside of the pane: models the sky (rather than
    # the sun) coming through the opening, and lights the window reveal
    win = bpy.data.objects["FILL_bounce"]
    win.name = "DUSK_window"
    win.location = (-IX + 0.05, WIN_Y, 1.55)
    win.rotation_euler = (0, math.radians(90), 0)
    win.data.energy = winfill
    win.data.size = 1.15
    win.data.color = (0.86, 0.66, 0.60)
    win.data.shape = "SQUARE"
    win.visible_camera = False

    # a very low cool fill from the open (cutaway) side so foreground props
    # keep a readable dark side instead of going to pure black
    amb = bpy.data.objects["RIM_gorge"]
    amb.name = "AMB_open"
    amb.location = (0.0, -6.4, 3.6)
    amb.rotation_euler = (math.radians(64), 0, 0)
    amb.data.energy = fill
    amb.data.size = 9.0
    amb.data.color = (0.40, 0.50, 0.68)

    # a cool overhead wash standing in for the light that would come through
    # the missing 4th wall / roof. Without it every beam top and shelf top is
    # pure black, and four black bars is all the eye sees.
    top = bpy.data.lights.new("SKY_top", "AREA")
    top.energy = sky
    top.size = 8.0
    top.color = (0.42, 0.52, 0.72)
    tob = bpy.data.objects.new("SKY_top", top)
    lc.objects.link(tob)
    tob.location = (0.0, -0.4, 2.94)     # just under the shadow ceiling
    tob.rotation_euler = (0, 0, 0)

    # bounded fog: haze inside the room only, so the lantern pools get halos.
    # A world volume would extinguish everything (kit manifest, bug 1).
    fb = bpy.data.objects["FOG_BOX"]
    fb.name = "FOG_ROOM"
    # STRICTLY inside the walls. With the box overhanging the shell, the
    # unobstructed sun outside lit all that volume and the whole plate went to
    # pink soup -- the interior sibling of the probe's "fog box must contain
    # the far geometry" note, in reverse: it must not contain anything else.
    fb.location = (0.0, -0.05, 1.46)
    fb.scale = (3.80 / 80.0, 2.86 / 80.0, 1.44 / 30.0)
    vn = fb.data.materials[0].node_tree.nodes["Volume Scatter"]
    vn.inputs["Density"].default_value = fog
    vn.inputs["Color"].default_value = (0.62, 0.55, 0.47, 1)
    return win, amb, fb


def setup_camera(pitch=24.5, yaw=1.5, dist=10.30, target=(0.05, 1.05, 1.18),
                 vfov=35.0):
    """One fixed camera: perspective, VERTICAL fov 35 deg (Blender fits the
    sensor to the long edge by default, which would give 35 deg horizontally),
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


# -------------------------------------------------------------------- main

def wipe():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for cc in list(bpy.data.collections):
        bpy.data.collections.remove(cc)


def build(ref=False, **light_kw):
    wipe()
    im.make_all()
    kit = pb.append_from_kit(KIT_NAMES)
    vl = bpy.context.view_layer.layer_collection.children.get("KIT_SOURCE")
    if vl:
        vl.exclude = True

    c = coll("ITEM_INT")
    build_floor(c)
    build_shell(c, kit)
    build_counter(c)
    build_backshelves(c)
    build_shelf_goods(c)
    build_counter_props(c)
    build_oar_stand(c)
    build_wares_left(c, kit)
    build_wares_right(c, kit)
    build_window_bench(c, kit)
    build_dressing(c, kit)
    build_hanging(c, kit)
    build_shadow_ceiling(c)
    build_pads(c)

    setup_light(c, **light_kw)
    setup_camera()

    r = kit["REF_human_1p7"]
    r.location = (2.10, -0.30, 0.0)
    if r.name not in c.objects:
        c.objects.link(r)
    r.hide_render = not ref
    return c


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    def opt(flag, default=None, cast=str):
        if flag in argv:
            return cast(argv[argv.index(flag) + 1])
        return default

    build(ref="--ref" in argv,
          dusk=opt("--dusk", 130.0, float),
          world=opt("--world", 0.22, float),
          fog=opt("--fog", 0.0125, float),
          fill=opt("--fill", 50.0, float),
          sky=opt("--sky", 90.0, float),
          winfill=opt("--winfill", 95.0, float))

    if opt("--pitch") or opt("--yaw") or opt("--dist"):
        setup_camera(pitch=opt("--pitch", 24.5, float),
                     yaw=opt("--yaw", 1.5, float),
                     dist=opt("--dist", 10.30, float))

    # Configure the render BEFORE saving, so the .blend ships with the shipping
    # recipe baked in (Cycles / 224 + denoise / 1344x768 / AgX + exposure) and
    # not with Blender's EEVEE 1920x1080 defaults.
    eng = opt("--engine", "cycles")
    if eng == "eevee":
        ru.setup_eevee()
    else:
        ru.setup_cycles(samples=opt("--samples", 224, int),
                        exposure=opt("--exposure", 0.70, float))

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

    tri = sum(len(o.data.polygons) for o in bpy.data.objects
              if o.type == "MESH" and not o.hide_render)
    print("FACES", tri)


if __name__ == "__main__":
    main()
