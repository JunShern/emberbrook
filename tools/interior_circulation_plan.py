"""Per-room circulation plan: hero anchors, what counts as the room's bones, and
the sweep edit list.  Loaded by tools/interior_circulation.py.

FEATURES[room]    = [(label, x, y), ...]  points the player must be able to reach
PROTECT[room]     = extra name substrings that are STRUCTURE (never moved)
PROTECT_BOX[room] = [(objname, x0,x1,y0,y1,z0,z1)] triangles of a JOINED mesh that
                    are structure even though the mesh as a whole is sweepable
EDITS[room]       = ops: {op: move|delete|island, ...}

WARNING — the edit list is applied ONCE, to the art-gate-accepted blend, and it
is NOT idempotent: moves are deltas and island picks are keyed on the loose
part's CURRENT position, so running `--fix --save` twice on the same blend moves
everything twice. The committed blends already have it applied. Re-run only
against a `git checkout` of the accepted blend, or audit without `--fix`.
"""

FEATURES = {
    # the left-hand display table the player browses
    "item":   [("wares", -1.70, 0.60)],
    "weapon": [("wares", -1.70, 0.60)],
    "armor":  [("wares", -1.70, 0.60)],
    # taproom hearth and the stair to the rooms
    # the taproom hearth is fronted by its settle (you sit at it, you do not
    # walk into it) — the standing spot is off the settle's north end
    "inn":    [("hearth", -3.10, 0.78), ("stair", 3.90, 0.80)],
    # the range/oven wall the cook works at
    "cookhouse": [("range", -2.20, 1.45)],
    # hearth, dresser, the family table. NOT the garden door: it has no
    # walk_pad, the runtime cannot use it, and its corner barrel+crate are
    # against two walls — corner dressing, which the rule explicitly keeps.
    "cottage": [("hearth", 1.70, 3.60), ("dresser", 3.90, 5.70),
                ("table", 5.55, 4.55)],
}

_SHOP = ("dressing", "wares_", "window_bench", "corner_prop", "lantern_hooks",
         "backshelf", "shelf_goods", "hanging_goods")

PROTECT = {
    "item": _SHOP, "weapon": _SHOP, "armor": _SHOP,
    "inn": ("stairwell", "keyrack", "notice", "slate", "innsign", "wainscot",
            "foreground", "density", "hearth_fire", "hearth_dress"),
    "cookhouse": ("dining", "doorzone", "density", "foreground", "dryrack",
                  "panwall", "hearth_kit", "range_props", "dining_extra",
                  "steam", "wainscot"),
    # the cottage is 1088 discrete objects: its bones are named by wall/part
    "cottage": ("wb_", "wl_", "wr_", "wf_", "plaster", "wain", "stud", "rail",
                "joist", "ceilboard", "townleaf", "gardenleaf", "oilskin",
                "scarf", "herb", "chart", "lantern", "lamp_", "dresser", "dr_",
                "settle", "hearth", "fire_", "chimney", "mantel", "lshelf",
                "shelf", "table_", "chair_", "bench", "sink", "ext_", "balc_",
                "riverleaf", "mochi", "catbasket", "rug_", "sill", "casement",
                "glaz", "muntin", "door", "frame", "skirt", "cornice", "trim",
                # things that ARE on a surface or in place: the laid table, the
                # fireside stool, the log basket and woodpile against the hearth
                # wall, the kettle on its crane, the children's toys on the rug
                "ware_", "set_", "stool", "kettle", "basket", "woodstack",
                "slipper", "toy_", "doll", "prop_rope"),
}

PROTECT_BOX = {
    # the inn's `luggage` blob is half floor trunks (sweepable) and half coats
    # hooked on the walls (art above knee height — keep).
    "inn": [("luggage", -5.10, 5.10, 3.05, 3.60, 0.90, 2.20),   # back-wall coats
            ("luggage", -5.10, -4.55, -3.60, 3.60, 0.90, 2.20)],  # left-wall coats
}

# --------------------------------------------------------------------- EDITS
# The three shops share one shell (same kit crate/barrel layout), so they share
# one sweep.  Door pad is at (-2.50, 2.28); counter pad at (2.10, -0.30); the
# only way from one to the other passes west of the counter's left end.
_SHOP_EDITS = [
    # the stack standing 0.2 m off the doorway — the single worst offender.
    # Slid east into the pocket between the door wall and the back shelving,
    # so the crate mass still reads in frame, just not across the threshold.
    {"op": "move", "obj": "kit_crate.004", "delta": [1.65, -0.32, 0],
     "why": "crate stack was touching the doorway"},
    {"op": "move", "obj": "kit_crate.005", "delta": [1.65, -0.32, 0],
     "why": "top of the doorway stack, follows .004"},
    # the stack sitting in the middle of the door->counter lane -> the front
    # prop row (a place the player has no reason to stand).
    {"op": "move", "obj": "kit_crate.001", "delta": [1.78, -4.12, 0],
     "why": "stack blocked the whole door->counter lane"},
    {"op": "move", "obj": "kit_crate.002", "delta": [1.78, -4.12, 0],
     "why": "top of the lane stack, follows .001"},
    {"op": "move", "obj": "kit_rope_coil.002", "delta": [1.78, -4.12, 0],
     "why": "rope coil rides on crate.002"},
    # sixth floor crate, wedged against the door jamb: the least valuable piece
    {"op": "delete", "obj": "kit_crate.003", "why": "crate wedged in the door jamb corner"},
    # barrel + its rope coil sat dead centre of the lane
    {"op": "move", "obj": "kit_barrel.001", "delta": [3.25, -2.97, 0],
     "why": "barrel stood in the door->counter lane"},
    {"op": "move", "obj": "kit_rope_coil.001", "delta": [3.25, -2.97, 0],
     "why": "rope coil rides on barrel.001"},
    # two barrels nibbling the counter-approach disc; the right-front corner
    # already carries three crates, a rope coil and a bucket.
    {"op": "delete", "obj": "kit_barrel.004", "why": "sixth barrel, in the counter approach"},
    {"op": "move", "obj": "kit_barrel.003", "delta": [-4.14, -1.14, 0],
     "why": "barrel reached into the counter-approach disc"},
    {"op": "move", "obj": "kit_rope_coil.003", "delta": [-4.14, -1.14, 0],
     "why": "rope coil rides on barrel.003"},
    # bucket standing in the counter approach -> back against the right wall
    {"op": "move", "obj": "kit_bucket.002", "delta": [0.40, -0.60, 0],
     "why": "bucket stood in the counter-approach disc"},
    # the produce bin at the counter's west end left only a 0.70 m gap against
    # the produce table — the single route from the door to the counter. Slid
    # 0.32 back along the counter line: the gap becomes a full metre.
    {"op": "island", "obj": "dressing", "box": [-0.70, 0.45, -0.05, 1.05, -0.05, 1.05],
     "action": "move", "delta": [-0.12, 0.32, 0],
     "why": "produce bin pinched the only door->counter route to 0.70 m"},
]

EDITS = {
    "item": list(_SHOP_EDITS),
    "weapon": list(_SHOP_EDITS),
    "armor": list(_SHOP_EDITS),

    "inn": [
        # barrel jammed into the back-left corner beside the door: the taproom
        # keeps barrel.002, two crates and a rope coil, and the door corner is
        # exactly the place clutter must not be.
        {"op": "delete", "obj": "kit_barrel.001", "why": "barrel boxed the door corner"},
        # the trunk/valise stack standing ON the door pad -> east along the back
        # wall to the coat hooks, which is where an inn's luggage belongs
        {"op": "island", "obj": "luggage", "box": [-4.80, -3.20, 1.90, 2.90, -0.15, 1.10],
         "action": "move", "delta": [3.00, 0.50, 0],
         "why": "trunk + travel cases stood on the door pad"},
        # water bucket sat in the middle of the hearth approach
        {"op": "move", "obj": "kit_bucket.001", "delta": [-1.23, 0.10, 0],
         "why": "bucket sat in the hearth approach"},
    ],

    # The cookhouse has almost no loose floor clutter — what crowds its pads is
    # furniture (the service hatch, the dining tables, the range, the right-wall
    # bench), and furniture is not this pass's to move. Two things are:
    "cookhouse": [
        # the right-wall bench overhung the door pad by 0.25 m, so from the spawn
        # you could not walk SOUTH — only west. Slid flush to the wall it is
        # against anyway (invisible in frame, the doorway walk opens).
        {"op": "island", "obj": "doorzone", "box": [3.20, 4.25, 1.30, 2.80, -0.10, 1.10],
         "action": "move", "delta": [0.22, 0, 0],
         "why": "wall bench overhung the door pad"},
        # a 0.30 m crock standing 0.45 m inside the threshold -> against the back
        # wall beside the prep bench
        {"op": "island", "obj": "doorzone", "box": [2.35, 2.90, 2.45, 2.80, -0.05, 0.35],
         "action": "move", "delta": [-0.55, 0.32, 0],
         "why": "crock stood in the doorway"},
    ],
    # The cottage floor is already open — its only real floor obstruction is the
    # bucket standing on the door pad. Everything else the sim flagged is either
    # ON the laid table (the rule's "clutter on surfaces is charm") or wall-side
    # dressing under 0.55 m that the runtime walks straight over.
    "cottage": [
        {"op": "move", "obj": "prop_bucket", "delta": [0.05, -0.75, 0],
         "why": "bucket stood on the door pad -> down beside the log basket"},
    ],
}
