#!/usr/bin/env python3
"""The three Dellhollow shop SKINS, as data.

`tools/item_int_build.py` builds one room. It knows about walls, the counter
carcass, the shelving carcass, the beams, the light rig and the camera -- the
things that are the same in every shop because they are the same building and
the same fixed camera. It knows nothing about jars, blades or mail.

Everything that makes a room a particular shop is a table here:

    shelf_item_pool   weighted goods dealt onto the back-wall shelving
    counter_props     what sits on the counter (and which practicals it lights)
    island_dressing   what the browse trestle in the aisle carries
    hanging_pool      what hangs from the ceiling beams
    corner_prop       the tall silhouette in the left corner

plus the supporting tables (wall rack, floor stock, features, trade sign,
bench, lanterns, palette, light) that follow the same shape.

An entry is `E(fn, at, **kw)`: a function from `shop_props`, a position, and
its arguments. The builder walks the list and calls them. Adding a fourth shop
is adding a dict; it should never mean touching the builder.

Positions are ABSOLUTE world coordinates except where a table's docstring says
otherwise (counter_props and island_dressing are relative to their surface, so
that moving the counter moves its clutter).
"""
import math
import importlib.util, os

TOOLS = os.path.dirname(os.path.abspath(__file__))


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sp = _mod("shop_props")
M, R = sp.M, sp.R
IX, IY, BZ, BEAM_Y, DOOR_X, WIN_Y = sp.IX, sp.IY, sp.BZ, sp.BEAM_Y, sp.DOOR_X, sp.WIN_Y
POST_X, CORNER = sp.POST_X, sp.CORNER


def E(what, at=(0.0, 0.0, 0.0), **kw):
    """One table row: what, where, how.

    The first parameter is `what`, not `fn`, so that a row can pass a nested
    `fn=` of its own (a peg hanger takes the prop it carries as `fn`).
    """
    return (what, at, kw)


# =====================================================================
# SHELF POOLS
#
# A pool entry is (weight, fn). `fill_shelf` draws one number per slot and
# walks the cumulative weights, so a pool is order-sensitive but easy to read.
# The fn signature is fn(m, x, yc, z, hmax, rr) -> how far to advance x.
# `rr` is the shelf's own Random so a shelf is reproducible independent of
# what else got built first.
# =====================================================================

# ---------------------------------------------------------------- chandlery

def _p_jar(m, x, yc, z, hmax, rr):
    sp.jar(m, x + 0.095, yc + rr.uniform(-0.02, 0.02), z, h=min(0.30, hmax - 0.04),
           r=rr.uniform(0.078, 0.095),
           mat=rr.choice([M("mat_i_ceramic"), M("mat_i_ceramic_b"),
                          M("mat_i_ceramic_ox"), M("mat_i_ceramic_gn"),
                          M("mat_i_ceramic_bl")]),
           seed=rr.random() * 9, lid=rr.random() < 0.7)
    return 0.20


def _p_bottles(m, x, yc, z, hmax, rr):
    n = rr.randint(2, 3)
    for i in range(n):
        sp.bottle(m, x + 0.055 + i * 0.108, yc + rr.uniform(-0.03, 0.03), z,
                  h=min(0.31, hmax - 0.03), seed=rr.random() * 9,
                  mat=rr.choice([M("mat_i_glass_brown"), M("mat_i_glass_green"),
                                 M("mat_i_glass"), M("mat_i_glass_brown")]))
    return 0.10 + n * 0.108


def _p_tins(m, x, yc, z, hmax, rr):
    adv = 0.0
    for i in range(rr.randint(2, 3)):
        sp.tin(m, x + 0.075, yc + rr.uniform(-0.03, 0.03), z + i * 0.122,
               mat=rr.choice([M("mat_i_rust"), M("mat_i_copper"), M("mat_i_iron")]))
    if rr.random() < 0.5:
        sp.tin(m, x + 0.20, yc + rr.uniform(-0.03, 0.03), z)
        adv += 0.13
    return adv + 0.17


def _p_candles(m, x, yc, z, hmax, rr):
    sp.candle_bundle(m, x + 0.075, yc, z, n=rr.randint(5, 8),
                     h=min(0.27, hmax - 0.05), seed=rr.random() * 9)
    return 0.17


def _p_crate(m, x, yc, z, hmax, rr):
    sp.small_crate(m, x + 0.14, yc, z, w=0.26, d=0.24, h=min(0.20, hmax - 0.03),
                   rz=rr.uniform(-0.06, 0.06),
                   mat=rr.choice([M("mat_i_crate"), M("mat_i_crate_b")]))
    return 0.30


def _p_charts(m, x, yc, z, hmax, rr):
    for i in range(rr.randint(2, 3)):
        sp.rolled_chart(m, x + 0.05 + i * 0.062, yc + rr.uniform(-0.02, 0.02), z,
                        h=min(0.33, hmax - 0.03), lean=rr.uniform(-0.13, 0.13))
    return 0.22


def _p_bowls(m, x, yc, z, hmax, rr):
    sp.bowl_stack(m, x + 0.10, yc, z, n=rr.randint(2, 4))
    return 0.23


def _p_coil(m, x, yc, z, hmax, rr):
    sp.coil_flat(m, x + 0.13, yc, z, r=0.125, n=rr.randint(2, 3))
    return 0.29


CHANDLERY_SHELF = [
    (0.20, _p_jar), (0.16, _p_bottles), (0.16, _p_tins), (0.12, _p_candles),
    (0.10, _p_crate), (0.08, _p_charts), (0.08, _p_bowls), (0.10, _p_coil),
]


# ------------------------------------------------------------------- weapons

def _w_daggers(m, x, yc, z, hmax, rr):
    """A block of daggers stood point-up. Small bright verticals, close
    together -- the shelf equivalent of a pin cushion."""
    n = rr.randint(3, 5)
    m.box((x + 0.11, yc, z + 0.022), (0.10, 0.075, 0.022), M("mat_i_beam"))
    for i in range(n):
        sp.dagger(m, x + 0.045 + i * 0.045, yc + rr.uniform(-0.03, 0.03), z + 0.044,
                  ln=rr.uniform(0.24, 0.32),
                  blade=rr.choice([M("mat_i_steel"), M("mat_i_steel_bright"),
                                   M("mat_i_steel_b")]))
    return 0.07 + n * 0.045


def _w_axeheads(m, x, yc, z, hmax, rr):
    """Loose axe heads in an open crate -- heavy, dull, stacked on their sides
    so the bit edges all point one way and catch the same highlight."""
    sp.small_crate(m, x + 0.15, yc, z, w=0.28, d=0.24, h=0.15,
                   rz=rr.uniform(-0.06, 0.06), mat=M("mat_i_crate_b"))
    for i in range(rr.randint(2, 4)):
        m.plate((x + 0.15 + rr.uniform(-0.07, 0.07), yc + rr.uniform(-0.05, 0.05),
                 z + 0.17 + i * 0.030), 0.19, 0.10, 0.028,
                M("mat_i_steel_b") if i % 2 else M("mat_i_iron"),
                rot=(1.57, rr.uniform(0, 3.1), rr.uniform(0, 3.1)), taper=1.7)
    return 0.26


def _w_quiver(m, x, yc, z, hmax, rr):
    sp.quiver(m, x + 0.10, yc, z, ln=min(0.44, hmax - 0.06),
              rot=(0, rr.uniform(-0.06, 0.06), rr.uniform(0, 3.1)), n=7)
    return 0.21


def _w_oilbottles(m, x, yc, z, hmax, rr):
    n = rr.randint(2, 3)
    for i in range(n):
        sp.bottle(m, x + 0.055 + i * 0.108, yc + rr.uniform(-0.03, 0.03), z,
                  h=min(0.31, hmax - 0.03), seed=rr.random() * 9,
                  mat=rr.choice([M("mat_i_glass_brown"), M("mat_i_glass_green"),
                                 M("mat_i_glass_brown"), M("mat_i_glass")]))
    return 0.10 + n * 0.108


def _w_whetstones(m, x, yc, z, hmax, rr):
    for i in range(rr.randint(2, 3)):
        sp.whetstone(m, x + 0.10, yc + rr.uniform(-0.04, 0.04), z + i * 0.048,
                     rot=rr.uniform(-0.3, 0.3))
    sp.oil_rag(m, x + 0.10, yc + 0.05, z, r=0.075, seed=rr.random() * 5)
    return 0.26


def _w_bladeflat(m, x, yc, z, hmax, rr):
    """A blade laid flat across the shelf on two chocks -- a horizontal, which
    a shelf of standing goods badly needs."""
    for s in (-1, 1):
        m.box((x + 0.20 + s * 0.16, yc, z + 0.020), (0.030, 0.055, 0.020),
              M("mat_i_beam"))
    sp.sword(m, x + 0.20, yc, z + 0.048, ln=rr.uniform(0.62, 0.76),
             rot=(0, math.pi / 2, 0),
             blade=rr.choice([M("mat_i_steel"), M("mat_i_steel_bright")]))
    return 0.40


def _w_helmrow(m, x, yc, z, hmax, rr):
    sp.helm(m, x + 0.11, yc, z + 0.02, r=0.088,
            rot=(0, 0, rr.uniform(0, 3.1)),
            mat=M("mat_i_steel_b") if rr.random() < 0.5 else M("mat_i_steel"),
            kind="nasal")
    return 0.21


def _w_bowstring(m, x, yc, z, hmax, rr):
    sp.coil_flat(m, x + 0.11, yc, z, r=0.095, n=rr.randint(2, 3))
    sp.tin(m, x + 0.11, yc, z + 0.075, h=0.085, r=0.048, mat=M("mat_i_copper"))
    return 0.25


WEAPON_SHELF = [
    (0.18, _w_daggers), (0.14, _w_axeheads), (0.12, _w_quiver),
    (0.12, _w_oilbottles), (0.12, _w_whetstones), (0.14, _w_bladeflat),
    (0.10, _w_helmrow), (0.08, _w_bowstring),
]


# -------------------------------------------------------------------- armour

def _a_helms(m, x, yc, z, hmax, rr):
    n = rr.randint(1, 2)
    kinds = ["nasal", "great", "crest", "nasal"]
    for i in range(n):
        sp.helm(m, x + 0.115 + i * 0.225, yc + rr.uniform(-0.02, 0.02), z + 0.015,
                r=rr.uniform(0.098, 0.118), rot=(0, 0, rr.uniform(-0.5, 0.5)),
                mat=rr.choice([M("mat_i_steel"), M("mat_i_steel_bright"),
                               M("mat_i_steel_b")]),
                kind=kinds[rr.randrange(4)])
    return 0.10 + n * 0.225


def _a_buckler(m, x, yc, z, hmax, rr):
    """A shield stood on edge, leaning on the shelf back. A disc on edge is
    the single most readable thing that can sit on a shelf in a dark room."""
    sp.shield_round(m, x + 0.16, yc + 0.05, z + 0.16, r=rr.uniform(0.145, 0.175),
                    rot=(math.radians(78), 0, rr.uniform(0, 3.1)),
                    face=rr.choice([M("mat_i_oxblood"), M("mat_i_steelblue_b"),
                                    M("mat_i_beam"), M("mat_i_steel_b")]),
                    rim=M("mat_i_steel_b"), boss=True)
    return 0.36


def _a_mailfold(m, x, yc, z, hmax, rr):
    """Mail folded on the shelf, not hung: a low soft mass between the hard
    shapes, so the shelf has a rest in it."""
    for i in range(rr.randint(2, 3)):
        m.lathe((x + 0.13, yc + rr.uniform(-0.02, 0.02), z + i * 0.052),
                [(0, 0), (0.075, 0.006), (0.108, 0.028), (0.098, 0.048),
                 (0.050, 0.055), (0, 0.056)], M("mat_i_mail"), seg=12,
                aspect=(1.0, 0.72), lumpy=0.12, seed=rr.random() * 6,
                rot=rr.uniform(0, 3))
    return 0.29


def _a_gauntlets(m, x, yc, z, hmax, rr):
    for i in range(2):
        sp.gauntlet(m, x + 0.075 + i * 0.085, yc + rr.uniform(-0.03, 0.03), z + 0.02,
                    rot=(0, 0, rr.uniform(-0.4, 0.4)), ln=0.19,
                    mat=M("mat_i_steel") if i else M("mat_i_steel_b"))
    return 0.25


def _a_rolls(m, x, yc, z, hmax, rr):
    sp.leather_roll(m, x + 0.17, yc, z, ln=0.30, r=0.056,
                    rot=(0, 0, rr.uniform(-0.2, 0.2)), n=rr.randint(1, 2),
                    mat=rr.choice([M("mat_i_leather"), M("mat_i_leather_b"),
                                   M("mat_i_leather_r")]))
    return 0.34


def _a_rivets(m, x, yc, z, hmax, rr):
    sp.parts_bin(m, x + 0.15, yc, z, w=0.13, d=0.10, n=rr.randint(6, 10),
                 kind="rivet" if rr.random() < 0.6 else "plate")
    return 0.32


def _a_oil(m, x, yc, z, hmax, rr):
    n = rr.randint(2, 3)
    for i in range(n):
        sp.bottle(m, x + 0.055 + i * 0.108, yc + rr.uniform(-0.03, 0.03), z,
                  h=min(0.29, hmax - 0.03), seed=rr.random() * 9,
                  mat=rr.choice([M("mat_i_glass_brown"), M("mat_i_glass"),
                                 M("mat_i_glass_green")]))
    return 0.10 + n * 0.108


def _a_greaves(m, x, yc, z, hmax, rr):
    for i in range(2):
        m.arc_lathe((x + 0.075 + i * 0.075, yc + rr.uniform(-0.03, 0.03), z),
                    [(0.056, 0), (0.062, 0.13), (0.052, 0.27), (0.044, 0.35)],
                    M("mat_i_steel") if i else M("mat_i_steel_b"), seg=12,
                    a0=-2.5, a1=0.6, rot=rr.uniform(-0.4, 0.4), aspect=(1.0, 0.78))
    return 0.25


ARMOUR_SHELF = [
    (0.20, _a_helms), (0.16, _a_buckler), (0.12, _a_mailfold),
    (0.12, _a_gauntlets), (0.12, _a_rolls), (0.10, _a_rivets),
    (0.09, _a_oil), (0.09, _a_greaves),
]


# =====================================================================
# THE SKINS
# =====================================================================

ITEM = {
    "key": "del-item-int",
    "collection": "ITEM_INT",

    # painted joinery. The shell geometry is identical between shops; the
    # paint is not, and it is doing most of the work of making them read as
    # three different businesses on the same street.
    "palette": {
        "trim": "mat_i_green", "trim_b": "mat_i_green_b",
        "accent": "mat_i_oxblood", "accent_b": "mat_i_oxblood",
        "stave": "mat_i_oxblood",
    },

    "shelf_item_pool": CHANDLERY_SHELF,

    # relative to (0, counter centre-line, counter top)
    "counter_props": [
        E(sp.ledger,          (0.92, 0.02, 0.0)),
        E(sp.balance_scale,   (2.30, 0.03, 0.0)),
        E(sp.oil_lamp,        (3.42, 0.06, 0.0), energy=400.0),
        E(sp.coil_flat,       (1.52, 0.10, 0.0), r=0.095, n=3),
        E(sp.tin,             (1.83, -0.10, 0.0), h=0.09, r=0.052,
          mat_name="mat_i_copper"),
        E(sp.coin_dish,       (2.86, -0.11, 0.0), n=7),
        E(sp.candle_lantern,  (0.62, 0.04, 0.0), energy=85.0),
        E(sp.fruit_box,       (0.98, -0.05, 0.0), n=3),
        E(sp.book_stack,      (0.75, 0.02, -0.55), n=3),
    ],

    # relative to the trestle's near-left corner, on its top
    "island_dressing": [
        E(sp.small_crate, (0.34, 0.44, 0.0), w=0.44, d=0.40, h=0.24, rz=0.12,
          mat_name="mat_i_crate_b"),
        E(sp.apple_heap,  (0.34, 0.44, 0.215), n=11, r=0.15),
        E(sp.sack,        (0.86, 0.30, 0.0), h=0.30, r=0.150, seed=7.1),
        E(sp.tin_stack,   (1.02, 0.60, 0.0), n=3),
        E(sp.jar,         (1.28, 0.20, 0.0), h=0.24, r=0.076,
          mat_name="mat_i_ceramic_ox", seed=3.3),
        E(sp.coil_flat,   (1.28, 0.62, 0.0), r=0.105, n=3),
        E(sp.bowl_stack,  (0.84, 0.62, 0.0), n=4),
    ],

    "hanging_pool": [
        E(sp.dried_fish_line, (0.30, BEAM_Y[1] - 0.32, BZ - 0.16), x1=3.30, n=9),
        E(sp.hung_coils,      (3.42, BEAM_Y[0] + 0.02, BZ), r=0.26, n=4),
        E(sp.hung_coils,      (-0.62, BEAM_Y[2] - 0.05, BZ), r=0.22, n=3),
        E(sp.hung_coils,      (1.05, BEAM_Y[0] + 0.03, BZ), r=0.21, n=3),
        E(sp.block_tackle,    (2.30, BEAM_Y[2] + 0.05, BZ)),
        E(sp.herb_bunch,      (-1.55, BEAM_Y[2] + 0.02, BZ)),
        E(sp.herb_bunch,      (-3.25, BEAM_Y[1] - 0.04, BZ)),
    ],

    "corner_prop": E(sp.oar_stand, (CORNER[0], CORNER[1], 0.0)),

    # the right-hand repoussoir rail, and the left-wall peg rail
    "wall_rack": [
        E(sp.cordage_peg_rack, (IX, -2.70, 1.62), y1=-0.54, face=1.0, pegs=6),
    ],

    # the left-wall peg rail, and the big hank on the aisle post. v5 hung the
    # nets off the front BEAM as long parallel strands and it read as a bead
    # curtain; a net a chandler is not using is bundled on a peg, and a bundle
    # has a silhouette.
    "left_pegs": [
        E(sp.peg_hook_pot, (-IX + 0.16, -2.42, 1.60), r=0.105, h=0.26,
          mat_name="mat_i_crate_b"),
        E(sp.net_hank,     (-IX + 0.26, -2.02, 1.60), drop=0.72, span=0.28,
          depth=0.19, n=26, seed=3.4, face=1.0, floats=2, mat_name="mat_i_net_d"),
        E(sp.peg_hook_pot, (-IX + 0.16, -1.62, 1.60), r=0.105, h=0.26,
          mat_name="mat_i_copper"),
        E(sp.net_hank,     (-IX + 0.26, -1.22, 1.60), drop=0.66, span=0.28,
          depth=0.19, n=26, seed=5.4, face=1.0, floats=1, mat_name="mat_i_net"),
        E(sp.peg_hook_pot, (-IX + 0.16, -0.82, 1.60), r=0.105, h=0.26,
          mat_name="mat_i_copper"),
        E(sp.net_hank,     (POST_X, BEAM_Y[0] - 0.17, 1.585), drop=0.70, span=0.30,
          depth=0.205, n=32, seed=1.7, face=-1.0, floats=3, mat_name="mat_i_net"),
    ],

    "left_stock": [
        E(sp.apple_crate_open,   (-2.42, -0.62, 0.0), n=34, fill="apple"),
        E(sp.provisions_barrel,  (-3.32, 0.60, 0.0), n=9, fill="root"),
        E(sp.sack, (-3.55, 1.62, 0.0), h=0.44, r=0.215, seed=0.0),
        E(sp.sack, (-3.30, 1.95, 0.0), h=0.40, r=0.195, seed=3.3,
          mat_name="mat_i_canvas"),
        E(sp.sack, (-3.62, -1.05, 0.0), h=0.42, r=0.205, seed=6.6),
    ],

    "features": [
        E(sp.tapped_barrel, (-0.06, 0.66, 0.62)),
        E(sp.coir_mat,      (DOOR_X, 2.10, 0.006)),
        E(sp.stool,         (1.72, 2.06, 0.0)),
        E(sp.broom,         (DOOR_X + 0.80, IY - 0.16, 0.02)),
        E(sp.price_board,   (-0.50, IY, 2.44)),
        E(sp.hawser,        (1.08, -1.92, 0.036)),
    ],

    "trade_sign": E(sp.crossed_sign, (DOOR_X, IY, 0.0), kind="oars"),

    "bench_props": [
        E(sp.measure_set, (-IX + 0.24, WIN_Y, 0.622)),
        E(sp.pot_row,     (-IX + 0.24, WIN_Y, 0.16), n=4),
    ],

    "litter": {"n": 190, "hot": (1.9, -0.2), "spread": 2.2, "base": 0.30},

    # (x, y, energy, drop). The COUNTER lantern is the key and runs a full stop
    # over the room ambient -- that hierarchy is the shop archetype's, not this
    # shop's, so every skin keeps it.
    "lanterns": [
        (-2.20, BEAM_Y[0] - 0.02, 440.0, 0.30),
        (2.55, BEAM_Y[1] + 0.02, 1180.0, 0.58),
        (-0.55, BEAM_Y[2] + 0.02, 400.0, 0.30),
        (3.20, BEAM_Y[0] + 0.04, 300.0, 0.30),
        (-0.34, BEAM_Y[1] + 0.02, 305.0, 0.74),
    ],

    "light": {},
}


WEAPON = dict(ITEM)
WEAPON.update({
    "key": "del-weapon-int",
    "collection": "WEAPON_INT",

    # deeper oxblood: a room of grey steel needs a darker, browner ground than
    # the chandlery's, or the trim shouts over the goods
    "palette": {
        "trim": "mat_i_green", "trim_b": "mat_i_green_b",
        "accent": "mat_i_oxblood_d", "accent_b": "mat_i_oxblood_d",
        "stave": "mat_i_oxblood_d",
    },

    "shelf_item_pool": WEAPON_SHELF,

    "counter_props": [
        E(sp.ledger,         (0.92, 0.02, 0.0)),
        E(sp.whetstone,      (2.24, 0.06, 0.0), rot=0.22),
        E(sp.oil_lamp,       (3.42, 0.06, 0.0), energy=400.0),
        E(sp.oil_rag,        (1.52, 0.10, 0.0), r=0.105, seed=2.2),
        E(sp.bottle,         (1.83, -0.10, 0.0), h=0.22, r=0.045,
          mat_name="mat_i_glass_brown", seed=1.1),
        E(sp.coin_dish,      (2.86, -0.11, 0.0), n=7),
        E(sp.candle_lantern, (0.62, 0.04, 0.0), energy=85.0),
        # the job in progress: a blade half-wrapped in oiled cloth, lying
        # across the counter right under the key. It is the brightest object
        # in the room and it is exactly where the player clicks.
        E(sp.wrapped_blade,  (2.62, -0.02, 0.045), ln=0.84, rot=(0, 1.5708, 0.10)),
        E(sp.parts_bin,      (1.06, -0.06, 0.0), w=0.13, d=0.10, n=8, kind="plate"),
        E(sp.leather_roll,   (2.02, -0.12, 0.0), ln=0.28, r=0.050, n=2,
          rot=(0, 0, 0.35)),
        E(sp.helm_block,     (3.06, 0.06, 0.0), r=0.105, kind="nasal"),
        E(sp.book_stack,     (0.75, 0.02, -0.55), n=3),
    ],

    "island_dressing": [
        E(sp.small_crate, (0.34, 0.44, 0.0), w=0.44, d=0.40, h=0.24, rz=0.12,
          mat_name="mat_i_crate_b"),
        E(sp.blade_fan,   (0.34, 0.44, 0.215), n=5),
        E(sp.axe_row,     (0.86, 0.34, 0.0), n=3),
        E(sp.tin_stack,   (1.02, 0.60, 0.0), n=3),
        E(sp.quiver,      (1.30, 0.22, 0.0), ln=0.46, rot=(0.16, 0, 1.1)),
        E(sp.whetstone,   (1.26, 0.62, 0.0), rot=0.5),
        E(sp.leather_roll, (0.84, 0.62, 0.0), ln=0.30, r=0.052, n=2),
    ],

    "hanging_pool": [
        E(sp.blade_hang_row,  (1.98, BEAM_Y[1] - 0.30, BZ), span=2.85, n=5, drop=0.14),
        E(sp.hung_arms_row,   (-2.28, BEAM_Y[2] - 0.10, BZ), span=1.60, n=3,
          drop=0.18, kind="bow"),
        E(sp.hung_coils,      (3.42, BEAM_Y[0] + 0.02, BZ), r=0.26, n=4),
        E(sp.herb_bunch,      (-0.62, BEAM_Y[2] - 0.05, BZ), n=9),
        E(sp.block_tackle,    (1.05, BEAM_Y[0] + 0.03, BZ)),
    ],

    "corner_prop": E(sp.polearm_barrel, (CORNER[0], CORNER[1], 0.0)),

    "wall_rack": [
        E(sp.weapon_peg_rack, (IX, -2.70, 1.62), y1=-0.54, face=1.0, pegs=6),
    ],

    "left_pegs": [
        E(sp.peg_hang, (-IX + 0.16, -2.42, 1.60), fn=sp.sword, side=1.0, drop=0.12,
          ln=0.86, rot=(0, math.pi, 0)),
        E(sp.peg_hang, (-IX + 0.16, -2.02, 1.60), fn=sp.quiver, side=1.0, drop=0.62,
          ln=0.50, rot=(0.14, 0, 0.6)),
        E(sp.peg_hang, (-IX + 0.16, -1.62, 1.60), fn=sp.axe, side=1.0, drop=0.12,
          ln=0.70, rot=(0, math.pi, 0.4)),
        E(sp.peg_hook_pot, (-IX + 0.16, -1.22, 1.60), r=0.105, h=0.26,
          mat_name="mat_i_crate_b"),
        E(sp.peg_hang, (-IX + 0.16, -0.82, 1.60), fn=sp.bow, side=1.0, drop=0.66,
          ln=1.10, rot=(0, 0, 0)),
        # the post peg carries a bundle of raw hafts rather than a net
        E(sp.net_hank, (POST_X, BEAM_Y[0] - 0.17, 1.585), drop=0.62, span=0.24,
          depth=0.17, n=22, seed=1.7, face=-1.0, floats=0, mat_name="mat_i_leather"),
    ],

    "left_stock": [
        E(sp.apple_crate_open,  (-2.42, -0.62, 0.0), n=14, fill="billet"),
        E(sp.provisions_barrel, (-3.32, 0.60, 0.0), n=7, fill="hilt"),
        E(sp.sack, (-3.55, 1.62, 0.0), h=0.44, r=0.215, seed=0.0),
        E(sp.sack, (-3.30, 1.95, 0.0), h=0.40, r=0.195, seed=3.3,
          mat_name="mat_i_canvas"),
        E(sp.sack, (-3.62, -1.05, 0.0), h=0.42, r=0.205, seed=6.6),
    ],

    "features": [
        # the grindstone stands where the chandlery taps its oil barrel: the
        # one prop that states the premise, in the same spot
        E(sp.grindstone,  (-0.10, 0.74, 0.0), rot=math.radians(74), r=0.30),
        # a SHOP-corner forge, not a smithy: it exists to add a second warm
        # pool opposite the counter and to say a smith works behind the till
        E(sp.forge_nook,  (1.00, 1.95, 0.0), rot=math.radians(9), energy=430.0),
        E(sp.coir_mat,    (DOOR_X, 2.10, 0.006)),
        E(sp.stool,       (2.62, 2.02, 0.0)),
        E(sp.broom,       (DOOR_X + 0.80, IY - 0.16, 0.02)),
        E(sp.price_board, (-0.50, IY, 2.44)),
        E(sp.hawser,      (1.08, -1.92, 0.036), k=4, r0=0.40),
        E(sp.floor_lantern, (-2.32, -1.58, 0.0), h=0.94, energy=140.0,
          name="LAMP_rack"),
    ],

    "trade_sign": E(sp.crossed_sign, (DOOR_X, IY, 0.0), kind="swords"),

    "bench_props": [
        E(sp.whetstone,  (-IX + 0.24, WIN_Y - 0.30, 0.622), rot=0.3),
        E(sp.oil_rag,    (-IX + 0.22, WIN_Y + 0.06, 0.622), r=0.10, seed=4.4),
        E(sp.tin_stack,  (-IX + 0.26, WIN_Y + 0.36, 0.622), n=3),
        E(sp.pot_row,    (-IX + 0.24, WIN_Y, 0.16), n=3),
    ],

    # swarf and quench-water splash gather at the grindstone as well as the
    # counter, so the litter has two hot spots
    "litter": {"n": 210, "hot": (0.6, 0.2), "spread": 3.0, "base": 0.26,
               "mat_name": "mat_i_straw"},

    "lanterns": [
        (-2.20, BEAM_Y[0] - 0.02, 420.0, 0.30),
        (2.55, BEAM_Y[1] + 0.02, 1180.0, 0.58),
        (-0.55, BEAM_Y[2] + 0.02, 380.0, 0.30),
        (3.20, BEAM_Y[0] + 0.04, 300.0, 0.30),
        (-0.34, BEAM_Y[1] + 0.02, 290.0, 0.74),
    ],

    "light": {},
})


ARMOUR = dict(ITEM)
ARMOUR.update({
    "key": "del-armor-int",
    "collection": "ARMOR_INT",

    # steel-blue-grey joinery. Cold trim is not decoration here: polished steel
    # is a mirror, so the colour of the room is the colour of the armour. A
    # cool ground makes every warm practical read as a highlight ON the metal.
    "palette": {
        "trim": "mat_i_steelblue", "trim_b": "mat_i_steelblue_b",
        "accent": "mat_i_oxblood", "accent_b": "mat_i_steelblue_b",
        "stave": "mat_i_steelblue_b",
    },

    "shelf_item_pool": ARMOUR_SHELF,

    "counter_props": [
        E(sp.ledger,         (0.92, 0.02, 0.0)),
        E(sp.leather_roll,   (2.18, 0.05, 0.0), ln=0.34, r=0.060, n=2, rot=(0, 0, 0.2)),
        E(sp.oil_lamp,       (3.42, 0.06, 0.0), energy=400.0),
        E(sp.buckle_tray,    (1.52, 0.08, 0.0), w=0.16, d=0.12, rot=0.18, n=14),
        E(sp.parts_bin,      (1.84, -0.10, 0.0), w=0.12, d=0.10, n=9, kind="rivet"),
        E(sp.coin_dish,      (2.86, -0.11, 0.0), n=7),
        E(sp.candle_lantern, (0.62, 0.04, 0.0), energy=85.0),
        # a helm on a block under the key: a curved mirror right at the
        # transaction point, so the counter reads even before the goods do
        E(sp.helm_block,     (2.60, 0.00, 0.0), r=0.125),
        E(sp.gauntlet,       (1.14, -0.06, 0.0), ln=0.18, rot=(0, 0, 0.5)),
        E(sp.book_stack,     (0.75, 0.02, -0.55), n=3),
    ],

    "island_dressing": [
        E(sp.small_crate,  (0.34, 0.44, 0.0), w=0.44, d=0.40, h=0.24, rz=0.12,
          mat_name="mat_i_crate_b"),
        E(sp.helm_heap,    (0.34, 0.44, 0.215), n=5),
        E(sp.shield_lean,  (0.90, 0.24, 0.0), r=0.26),
        E(sp.leather_roll, (1.04, 0.60, 0.0), ln=0.32, r=0.058, n=3),
        E(sp.buckle_tray,  (1.30, 0.22, 0.0), w=0.14, d=0.11, rot=0.4, n=12),
        E(sp.gauntlet,     (0.80, 0.62, 0.0), ln=0.20, rot=(0, 0, 1.1)),
    ],

    "hanging_pool": [
        E(sp.hung_mail_row, (1.98, BEAM_Y[1] - 0.30, BZ), span=2.80, n=5, drop=0.16),
        E(sp.hung_coils,    (-1.55, BEAM_Y[2] + 0.02, BZ), r=0.20, n=3),
        E(sp.hung_mail_row, (-2.28, BEAM_Y[2] - 0.10, BZ), span=1.60, n=3, drop=0.18),
        E(sp.hung_coils,    (3.42, BEAM_Y[0] + 0.02, BZ), r=0.24, n=3),
        E(sp.herb_bunch,    (-0.62, BEAM_Y[2] - 0.05, BZ), n=9),
        E(sp.block_tackle,  (1.05, BEAM_Y[0] + 0.03, BZ)),
    ],

    "corner_prop": E(sp.armor_stand, (CORNER[0], CORNER[1] + 0.10, 0.0),
                     rot=math.radians(28), h=1.70),

    "wall_rack": [
        E(sp.armour_peg_rack, (IX, -2.70, 1.62), y1=-0.54, face=1.0, pegs=6),
    ],

    "left_pegs": [
        E(sp.peg_hang, (-IX + 0.16, -2.42, 1.60), fn=sp.shield_round, side=1.0,
          drop=0.30, r=0.27, rot=(0, math.pi / 2, 0), face_name="mat_i_oxblood"),
        E(sp.peg_hang, (-IX + 0.16, -2.02, 1.60), fn=sp.mail_shirt, side=1.0,
          drop=0.10, ln=0.60, rot=(0, 0, 0)),
        E(sp.peg_hang, (-IX + 0.16, -1.62, 1.60), fn=sp.helm, side=1.0, drop=0.22,
          r=0.115, kind="great"),
        E(sp.peg_hook_pot, (-IX + 0.16, -1.22, 1.60), r=0.105, h=0.26,
          mat_name="mat_i_crate_b"),
        E(sp.peg_hang, (-IX + 0.16, -0.82, 1.60), fn=sp.shield_round, side=1.0,
          drop=0.30, r=0.25, rot=(0, math.pi / 2, 0), face_name="mat_i_steelblue_b"),
        E(sp.net_hank, (POST_X, BEAM_Y[0] - 0.17, 1.585), drop=0.66, span=0.26,
          depth=0.19, n=26, seed=1.7, face=-1.0, floats=0, mat_name="mat_i_mail"),
    ],

    "left_stock": [
        E(sp.apple_crate_open,  (-2.42, -0.62, 0.0), n=9, fill="buckler"),
        E(sp.provisions_barrel, (-3.32, 0.60, 0.0), n=8, fill="helm"),
        E(sp.sack, (-3.55, 1.62, 0.0), h=0.44, r=0.215, seed=0.0),
        E(sp.sack, (-3.30, 1.95, 0.0), h=0.40, r=0.195, seed=3.3,
          mat_name="mat_i_canvas"),
        E(sp.sack, (-3.62, -1.05, 0.0), h=0.42, r=0.205, seed=6.6),
    ],

    "features": [
        # a second, half-dressed stand where the chandlery taps its barrel:
        # armour in progress rather than armour finished
        E(sp.armor_stand, (-0.10, 0.74, 0.0), rot=math.radians(-24), h=1.46,
          full=False),
        E(sp.polish_bench, (2.78, 2.06, 0.0), rot=math.radians(-8)),
        E(sp.floor_lantern, (-2.36, -1.52, 0.0), h=0.94, energy=155.0,
          name="LAMP_stand"),
        E(sp.floor_lantern, (-0.46, -0.52, 0.0), h=0.88, energy=115.0,
          name="LAMP_aisle"),
        E(sp.coir_mat,     (DOOR_X, 2.10, 0.006)),
        E(sp.stool,        (1.36, 2.02, 0.0)),
        E(sp.broom,        (DOOR_X + 0.80, IY - 0.16, 0.02)),
        E(sp.price_board,  (-0.50, IY, 2.44)),
        E(sp.hawser,       (1.08, -1.92, 0.036), k=4, r0=0.40),
    ],

    "trade_sign": E(sp.crossed_sign, (DOOR_X, IY, 0.0), kind="shield"),

    "bench_props": [
        E(sp.leather_roll, (-IX + 0.24, WIN_Y - 0.30, 0.622), ln=0.28, r=0.052, n=2),
        E(sp.buckle_tray,  (-IX + 0.22, WIN_Y + 0.06, 0.622), w=0.13, d=0.10,
          rot=1.4, n=10),
        E(sp.helm,         (-IX + 0.24, WIN_Y + 0.38, 0.640), r=0.105,
          kind="great"),
        E(sp.pot_row,      (-IX + 0.24, WIN_Y, 0.16), n=3),
    ],

    "litter": {"n": 170, "hot": (1.9, -0.2), "spread": 2.4, "base": 0.26},

    "lanterns": [
        (-2.20, BEAM_Y[0] - 0.02, 470.0, 0.30),
        (2.55, BEAM_Y[1] + 0.02, 1180.0, 0.58),
        (-0.55, BEAM_Y[2] + 0.02, 430.0, 0.30),
        (3.20, BEAM_Y[0] + 0.04, 330.0, 0.30),
        (-0.34, BEAM_Y[1] + 0.02, 330.0, 0.74),
    ],

    # dark metal in a dark room disappears. The shadow ceiling is carrying the
    # bounce, so it gets more to carry: a hotter sky wash, a warmer/stronger
    # window fill for rim separation, and slightly thicker haze so the lantern
    # pools halo around the polished pieces.
    "light": {"sky": 98.0, "fill": 54.0, "winfill": 122.0, "world": 0.21,
              "fog": 0.0110},
})


SKINS = {"item": ITEM, "weapon": WEAPON, "armor": ARMOUR, "armour": ARMOUR}
