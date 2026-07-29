#!/usr/bin/env python3
"""Dellhollow SHOP interior builder -- one room, three skins.

This file builds the FF9 cutaway shop: floor, shell, counter carcass, shelving
carcass, beams, light rig, camera, walk pads. It is the SHOP ARCHETYPE, first
proven as the item shop (`docs/qa/interiors/item-int_v6.png`, accepted) and
then generalised so the weapon and armour shops are the same room with a
different skin rather than three hand-built scenes.

    zone            where                       what a skin changes
    -------------   -------------------------   ---------------------------
    ENTRY           back wall, left bay          never (kit_wall_door)
    COUNTER         right half, y ~ 0.6..1.3     counter_props
    KEEP            behind counter, y 1.3..2.5   NPC stands here
    BACK WALL WARES shelving x 0.55..3.87        shelf_item_pool
    BROWSE          left half + right foreground island_dressing / left_stock
    HANGING         ceiling beams                hanging_pool
    CORNER          left front                   corner_prop

Nothing in this file knows what a shop sells. The goods, the practicals'
energies and the paint are tables in `tools/shop_skins.py`, built from the
prop vocabulary in `tools/shop_props.py`. Adding a fourth shop is adding a
dict there; it should never mean editing this file.

Naming contract for the engine: `walk_floor` is the walkable floor mesh,
`walk_pad_door` and `walk_pad_counter` are the interaction pads (hidden from
render -- they are metadata, not set dressing).

Run headless:
    Blender -b -P tools/item_int_build.py -- --skin item \
        --out tools/blends/interiors/item-int.blend \
        --render docs/qa/interiors/item-int_v6.png --samples 224
"""
import bpy, bmesh, math, os, random, sys, importlib.util
from mathutils import Matrix, Vector, Euler

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TOOLS = os.path.join(ROOT, "tools")


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sp = _mod("shop_props")           # room contract + prop vocabulary
sk = _mod("shop_skins")           # the three skins, as data
pb = sp.pb                        # Mesh / place / append_from_kit helpers
im = _mod("item_int_materials")   # interior material library
ru = _mod("render_util")

R = sp.R                          # ONE rng stream, consumed in build order
IMesh, sagline, M, coll = sp.IMesh, sp.sagline, sp.M, sp.coll

# room contract -- see shop_props for the commentary on each number
HW, YB, YF, WH = sp.HW, sp.YB, sp.YF, sp.WH
IX, IY = sp.IX, sp.IY
BEAM_Z, BEAM_H, BEAM_Y, BEAMS, BZ = sp.BEAM_Z, sp.BEAM_H, sp.BEAM_Y, sp.BEAMS, sp.BZ
CTR_X0, CTR_X1, CTR_Y0, CTR_Y1, CTR_H, CTR_YC = (
    sp.CTR_X0, sp.CTR_X1, sp.CTR_Y0, sp.CTR_Y1, sp.CTR_H, sp.CTR_YC)
SHELF_X0, SHELF_X1, SHELF_Y0, SHELF_Y1 = (
    sp.SHELF_X0, sp.SHELF_X1, sp.SHELF_Y0, sp.SHELF_Y1)
SHELF_BOARDS = sp.SHELF_BOARDS
ISL_X0, ISL_X1, ISL_Y0, ISL_Y1, ISL_H = (
    sp.ISL_X0, sp.ISL_X1, sp.ISL_Y0, sp.ISL_Y1, sp.ISL_H)
DOOR_X, WIN_Y = sp.DOOR_X, sp.WIN_Y


# ------------------------------------------------------------------ palette
# A skin names its joinery colours; everything structural asks for them by
# ROLE, never by material name, so re-painting a shop is a three-line table
# change and cannot miss a piece.

PAL = {}


def P(role):
    return M(PAL.get(role, role))


# ------------------------------------------------------------- table runner

def emit(m, entries, origin=(0.0, 0.0, 0.0)):
    """Run a skin table. `at` is an offset from `origin`; any `*_name` kwarg is
    resolved to a material, so the tables stay free of bpy objects (they are
    imported before any material exists)."""
    ox, oy, oz = origin
    for fn, at, kw in entries:
        kw = dict(kw)
        for k in [k for k in kw if k.endswith("_name")]:
            kw[k[:-5]] = M(kw.pop(k))
        fn(m, ox + at[0], oy + at[1], oz + at[2], **kw)


# ------------------------------------------------------------------ the kit

KIT_NAMES = ["kit_wall_door", "kit_wall_window", "kit_wall_plain", "kit_barrel",
             "kit_crate", "kit_bucket", "kit_rope_coil", "kit_lantern_hanging",
             "kit_lantern_light", "kit_beam", "REF_human_1p7",
             "SUN_key", "FILL_bounce", "RIM_gorge", "FOG_BOX"]

# kit exterior material -> interior material or palette ROLE. The kit's moss
# layer is driven by the world-up normal, which is right for a river town and
# wrong indoors.
RESKIN = {
    "mat_wallwood":      "mat_i_wall",       # cladding -> weathered interior timber
    "mat_timber":        "trim",             # framing  -> the shop's painted trim
    "mat_wallwood_dark": "accent",           # door leaf / staves -> the accent
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
        if new is None:
            continue
        new = PAL.get(new, new)
        if bpy.data.materials.get(new):
            me.materials[i] = bpy.data.materials[new]
    return ob


# ------------------------------------------------------------------- shell

def build_floor(c):
    """`walk_floor`: real plank geometry, five de-correlated plank materials
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
    fr = P("trim")
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
    m.box((0, 0.02, 0.07), (width / 2, 0.05, 0.07), fr)             # sill
    m.box((0, 0.02, WH - 0.08), (width / 2, 0.05, 0.08), fr)        # head
    m.box((0, 0.02, WH * 0.52), (width / 2, 0.042, 0.055), fr)      # mid rail
    for sx in (-1, 1):
        m.box((sx * (width / 2 - 0.07), 0.02, WH / 2), (0.07, 0.05, WH / 2), fr)
    n_std = max(1, int(width / 1.05))
    for i in range(1, n_std):
        m.box((-width / 2 + width * i / n_std, 0.02, WH / 2), (0.055, 0.045, WH / 2),
              fr)
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

    # ---- trim: the painted joinery that ties the palette ------------------
    t = IMesh("trim")
    g, gb, ox = P("trim"), P("trim_b"), P("accent")
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
    skb = 0.155
    for (x0, x1) in ((-IX, DOOR_X - 0.62), (DOOR_X + 0.62, IX)):
        t.box(((x0 + x1) / 2, IY - 0.035, skb / 2), ((x1 - x0) / 2, 0.035, skb / 2), gb)
    for sx in (-1, 1):
        t.box((sx * (IX - 0.035), (YB + YF) / 2, skb / 2),
              (0.035, (YB - YF) / 2, skb / 2), gb)
    # accent band above the skirting: the map's shop-front colour
    for (x0, x1) in ((-IX, DOOR_X - 0.62), (DOOR_X + 0.62, IX)):
        t.box(((x0 + x1) / 2, IY - 0.022, skb + 0.045), ((x1 - x0) / 2, 0.022, 0.045), ox)
    for sx in (-1, 1):
        t.box((sx * (IX - 0.022), (YB + YF) / 2, skb + 0.045),
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
    bm_ = M("mat_i_beam")
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
    top, ox, g, bm_ = M("mat_i_counter"), P("accent"), P("trim"), M("mat_i_beam")
    x0, x1, y0, y1 = CTR_X0, CTR_X1, CTR_Y0, CTR_Y1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # worn top slab with a front nosing that overhangs the panelling
    m.box((cx, cy - 0.035, CTR_H - 0.042), ((x1 - x0) / 2, (y1 - y0) / 2 + 0.035, 0.042), top)
    m.box((cx, y0 - 0.062, CTR_H - 0.10), ((x1 - x0) / 2, 0.032, 0.055), top)
    # panelled front: accent panels in painted stiles and rails
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
    sh, shb, g, ox = M("mat_i_shelf"), M("mat_i_shelf_b"), P("trim"), P("accent")
    x0, x1, y0, y1 = SHELF_X0, SHELF_X1, SHELF_Y0, SHELF_Y1
    cy, dy = (y0 + y1) / 2, (y1 - y0) / 2
    boards = list(SHELF_BOARDS)
    uprights = [x0 + 0.035, 1.62, 2.78, x1 - 0.035]
    for z in boards:
        m.box(((x0 + x1) / 2, cy, z), ((x1 - x0) / 2, dy, 0.021),
              sh if z in boards[::2] else shb)
        # a thin lip so nothing looks like it will slide off
        m.box(((x0 + x1) / 2, y0 + 0.012, z + 0.035), ((x1 - x0) / 2, 0.012, 0.024), g)
    for ux in uprights:
        m.box((ux, cy, 1.30), (0.035, dy, 1.30), shb)
        m.box((ux, y0 - 0.014, 1.30), (0.042, 0.014, 1.30), ox)
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
    # cornice + accent signboard over the top
    m.box(((rx0 + rx1) / 2, (ry0 + ry1) / 2 - 0.03, 2.62), (0.20, (ry1 - ry0) / 2, 0.03), sh)
    m.box(((x0 + x1) / 2, cy - 0.03, 2.62), ((x1 - x0) / 2 + 0.03, dy + 0.03, 0.03), sh)
    m.box(((x0 + x1) / 2, y1 - 0.045, 2.42), ((x1 - x0) / 2 - 0.04, 0.045, 0.155), ox)
    m.box(((x0 + x1) / 2, y1 - 0.062, 2.42), ((x1 - x0) / 2 - 0.02, 0.028, 0.185), g)
    return m.finish(c, bevel=0.006)


# --------------------------------------------------------- shelf stuffing

def fill_shelf(m, pool, x0, x1, yf, yb, z, hmax, seed=0):
    """Walk the board left to right dealing from the skin's weighted pool,
    leaving small gaps.

    One `rr.random()` per slot, drawn from the shelf's OWN Random, so a board
    always gets the same goods no matter what else the scene built first --
    which is what lets a skin be swapped without reshuffling the whole room.
    """
    rr = random.Random(hash((round(x0, 3), round(z, 3), seed)) & 0xffffffff)
    yc = (yf + yb) / 2
    total = sum(w for w, _ in pool)
    x = x0 + 0.06
    while x < x1 - 0.10:
        pick = rr.random() * total
        acc = 0.0
        fn = pool[-1][1]
        for w, f in pool:
            acc += w
            if pick < acc:
                fn = f
                break
        x += fn(m, x, yc, z, hmax, rr)
        x += rr.uniform(0.005, 0.045)


def build_shelf_goods(c, skin):
    m = IMesh("shelf_goods")
    pool = skin["shelf_item_pool"]
    for i, z in enumerate(SHELF_BOARDS):
        top = z + 0.021
        fill_shelf(m, pool, SHELF_X0 + 0.05, 1.585, SHELF_Y0 + 0.03, SHELF_Y1 - 0.02,
                   top, 0.44, seed=i * 3 + 1)
        fill_shelf(m, pool, 1.66, 2.745, SHELF_Y0 + 0.03, SHELF_Y1 - 0.02,
                   top, 0.44, seed=i * 3 + 2)
        fill_shelf(m, pool, 2.82, SHELF_X1 - 0.05, SHELF_Y0 + 0.03, SHELF_Y1 - 0.02,
                   top, 0.44, seed=i * 3 + 3)
    for i, z in enumerate(SHELF_BOARDS):
        fill_shelf(m, pool, 1.20, 1.86, IX - 0.31, IX - 0.03, z + 0.021, 0.44, seed=70 + i)
        fill_shelf(m, pool, 1.98, 2.78, IX - 0.31, IX - 0.03, z + 0.021, 0.44, seed=80 + i)
    return m.finish(c, bevel=0.004, seg=1)


# ------------------------------------------------------------ counter props

def build_counter_props(c, skin):
    """Positions in the table are relative to (0, counter centre-line, counter
    top), so moving the counter moves its clutter with it."""
    m = IMesh("counter_props")
    emit(m, skin["counter_props"], origin=(0.0, CTR_YC, CTR_H))
    return m.finish(c, bevel=0.004, seg=1)


# -------------------------------------------------------------- browse zone

def build_corner(c, skin):
    """The tall silhouette in the left front corner: oars, polearms or a
    dressed armour stand. Whatever it is, it is the frame's left-hand
    repoussoir and the only thing that breaks the beam line down there."""
    m = IMesh("corner_prop")
    emit(m, [skin["corner_prop"]])
    return m.finish(c, bevel=0.006)


def build_wares_left(c, kit, skin):
    """Browsable stock down the left side, plus the kit crates and barrels the
    town shares. The kit pieces are linked duplicates -- one mesh, many uses."""
    m = IMesh("wares_left")
    made = []
    emit(m, skin["left_stock"])
    made.append(m.finish(c, bevel=0.006, seg=1))

    ck, bk = kit["kit_crate"], kit["kit_barrel"]
    reskin(ck, {"mat_wallwood_dark": "mat_i_crate", "mat_timber": "mat_i_beam"})
    reskin(bk, {"mat_wallwood_dark": "stave"})
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


def build_wares_right(c, kit, skin):
    """Right foreground: the wall rack over stacked stock. This is the
    repoussoir on the camera's right; a skin swaps the rack's contents without
    touching the geometry it hangs on."""
    m = IMesh("wares_right")
    made = []
    emit(m, skin["wall_rack"])
    for i, by in enumerate((-2.46, -2.02, -1.58, -1.14, -0.70)):
        if i % 2:
            sp.small_crate(m, IX - 0.19, by, 2.142, w=0.30, d=0.34, h=0.22,
                           rz=math.radians(90), mat=M("mat_i_crate_b"))
        else:
            sp.coil_flat(m, IX - 0.19, by, 2.142, r=0.14, n=3)
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


def build_dressing(c, kit, skin):
    """The stuff that turns a stocked room into a shop somebody works in: the
    dresser in the dead bay, the left peg rail, the browse island, the skin's
    feature props, the trade sign, notices, and litter on the floor."""
    m = IMesh("dressing")
    made = []

    # --- narrow dresser in the bay between the door and the main shelving --
    dx0, dx1 = -1.28, 0.28
    dy0, dy1 = IY - 0.34, IY
    sp.dresser(m, dx0, dx1, dy0, dy1, trim=P("trim"), accent=P("accent"))
    for i, z in enumerate((0.44, 0.92, 1.40, 1.88)):
        fill_shelf(m, skin["shelf_item_pool"], dx0 + 0.05, dx1 - 0.05,
                   dy0 + 0.03, dy1 - 0.02, z, 0.44, seed=40 + i)

    # --- peg rail on the LEFT wall, front half (mirrors the right-hand rail)
    m.box((-IX + 0.045, -1.55, 1.58), (0.045, 1.10, 0.055), P("trim"))
    for py in (-2.42, -2.02, -1.62, -1.22, -0.82):
        m.cyl((-IX + 0.14, py, 1.62), 0.022, 0.20, M("mat_i_beam"), seg=8,
              rot=(0, math.pi / 2, 0))
    emit(m, skin["left_pegs"])

    # --- the skin's feature props, trade sign and wall bills --------------
    emit(m, skin["features"])
    emit(m, [skin["trade_sign"]])
    sp.notices(m, -3.62, IY, 1.66)

    # --- browse island ----------------------------------------------------
    sp.trestle(m, ISL_X0, ISL_X1, ISL_Y0, ISL_Y1, h=ISL_H,
               trim=P("trim"), accent=P("accent"))
    emit(m, skin["island_dressing"], origin=(ISL_X0, ISL_Y0, ISL_H + 0.024))

    # --- straw, sawdust wisps and floor spill -----------------------------
    lit = dict(skin["litter"])
    for k in [k for k in lit if k.endswith("_name")]:
        lit[k[:-5]] = M(lit.pop(k))
    sp.floor_litter(m, -IX + 0.1, IX - 0.1, YF + 0.2, IY - 0.1, **lit)
    made.append(m.finish(c, bevel=0.004, seg=1))

    # --- foreground floor stock, kept clear of the door/counter lane ------
    ck, bk = kit["kit_crate"], kit["kit_barrel"]
    made.append(pb.place(ck, (-1.72, -2.55, 0.043), rot=(0, 0, -0.35), c=c, jitter=0.02))
    made.append(pb.place(bk, (-2.28, -2.62, 0.0), rot=(0, 0, 1.9), c=c, jitter=0.02))
    for (x, y, z) in ((-1.72, -2.55, 0.70), (3.02, -2.15, 0.0)):
        made.append(pb.place(kit["kit_rope_coil"], (x, y, z), c=c, jitter=0.25))
    return made


def build_window_bench(c, skin):
    """Low bench under the dusk window -- keeps the left wall from going dead
    and gives the light shaft something to land on."""
    m = IMesh("window_bench")
    sp.window_bench(m, -IX + 0.24, WIN_Y, trim=P("trim"))
    emit(m, skin["bench_props"])
    return m.finish(c, bevel=0.006, seg=1)


# ---------------------------------------------------------------- hanging

def build_hanging(c, kit, skin):
    """Goods slung from the ceiling beams, then the lanterns that are the
    room's warm pools. Ordinary flame, no magic."""
    m = IMesh("hanging_goods")
    made = []
    emit(m, skin["hanging_pool"])
    made.append(m.finish(c, bevel=0.004, seg=1))

    lamp = kit["kit_lantern_hanging"]
    reskin(lamp, {"mat_lantern_glass": "mat_i_lampglass"})
    hooks = IMesh("lantern_hooks")
    # COUNTER KEY: the lantern over the counter runs a full stop hotter than
    # the room ambient (and the browse-side lanterns were pulled back to
    # match) so the buy/sell spot is unambiguously the brightest thing in
    # frame. The hierarchy is counter > back-shelf wares > browse aisle >
    # corners, and it belongs to the ARCHETYPE: every skin keeps it.
    for (lx, ly, energy, drop) in skin["lanterns"]:
        hooks.strand([(lx, ly, BZ), (lx, ly, BZ - drop)], 0.007, M("mat_i_iron"), seg=4)
        o = pb.place_lantern(lamp, (lx, ly, BZ - drop - 0.352), c=c, energy=energy)
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

def setup_light(c, dusk=130.0, world=0.20, fog=0.0125, fill=46.0, sky=82.0,
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


def build(skin="item", ref=False, **light_kw):
    global PAL
    s = sk.SKINS[skin]
    PAL = dict(s["palette"])

    wipe()
    sp.R.seed(20260729)               # one deterministic stream per build
    im.make_all()
    kit = pb.append_from_kit(KIT_NAMES)
    vl = bpy.context.view_layer.layer_collection.children.get("KIT_SOURCE")
    if vl:
        vl.exclude = True

    c = coll(s["collection"])
    build_floor(c)
    build_shell(c, kit)
    build_counter(c)
    build_backshelves(c)
    build_shelf_goods(c, s)
    build_counter_props(c, s)
    build_corner(c, s)
    build_wares_left(c, kit, s)
    build_wares_right(c, kit, s)
    build_window_bench(c, s)
    build_dressing(c, kit, s)
    build_hanging(c, kit, s)
    build_shadow_ceiling(c)
    build_pads(c)

    lk = dict(s.get("light", {}))
    lk.update(light_kw)
    setup_light(c, **lk)
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

    lk = {}
    for flag, key in (("--dusk", "dusk"), ("--world", "world"), ("--fog", "fog"),
                      ("--fill", "fill"), ("--sky", "sky"), ("--winfill", "winfill")):
        v = opt(flag, None, float)
        if v is not None:
            lk[key] = v

    build(skin=opt("--skin", "item"), ref="--ref" in argv, **lk)

    if opt("--pitch") or opt("--yaw") or opt("--dist"):
        setup_camera(pitch=opt("--pitch", 24.5, float),
                     yaw=opt("--yaw", 1.5, float),
                     dist=opt("--dist", 10.30, float))

    # Configure the render BEFORE saving, so the .blend ships with the shipping
    # recipe baked in (Cycles / 224 + denoise / 1344x768 / AgX + exposure) and
    # not with Blender's EEVEE 1920x1080 defaults.
    if opt("--engine", "cycles") == "eevee":
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
