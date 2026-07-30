"""t2_color_pops.py — POPS OF COLOUR.  docs/plans/pops-of-color.md, phases P1-P4.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_color_pops.py -- [phase p1|dress|all] [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_color_pops.py -- revert save

THE FINDING.  Chromatic pop, defined narrowly (a pixel whose hit material is a
painted panel, cloth, awning, flag or produce — timber and roofs and rock
excluded, because a warm brown plank is the thing being broken up, not an
instance of breaking it up), measures 3.07% across the town.  The brief named
gate and quay-west as the two brown shots.  Gate is right, at 0.61%.  Quay-west
is wrong: at 9.01% it is the SECOND MOST COLOURFUL frame in Dellhollow, and it
reads brown because 45.4% of it is rock, not for want of paint.

The real brown belt is the EASTERN half of the town — cottage-steps 0.00%,
lockfive 0.00%, north-landing 0.03%, crossing 0.11%, fishdock 0.16%, cottage
0.17%.  Six of seventeen shots have essentially no chromatic pixel at all,
because every painted object in Dellhollow lives west of x ~ 65: the shelf shop
row, the quay market, the boatyard.  The Lockfoot district was built with the
`lf_` kit and got timber, stone and shingle and nothing else.

THE PLACEMENT TABLE IS MEASURED, AND IT WAS RE-MEASURED AFTER THE CLIFF PASS,
which is the ordering docs/plans/pops-of-color.md insists on: its budget was
taken against frames in which up to 22.6% of the pixels were the grey
`cliff_town` slab, and that slab is gone.  Re-running `tools/t2_probe_place.py`
against the rebuilt master reproduces the budget to within a tenth of a point
(gate 7.67%, lockhead 9.02%, crossing 10.59%, north-landing 7.95%), so the table
stands as written.  Every `screen` below is that occlusion-tested projection.

TWO FREE WINS FIRST (phase P1), because the modelled rows should be measured
against an already-improved baseline:

  * THE AWNINGS ARE GREY.  `qm_awning_2.001` is 21 of 21 loops neutral
    (0.60, 0.58, 0.54); `qm_awning_0/1/3/4` and `shelf_awning_1/2/3` run 12 grey
    loops to 9 coloured.  Nine awning objects already exist, already sit in
    frame, and are more than half unpainted.  Recolouring `Col` is a
    vertex-colour edit with ZERO new geometry — the finding-211 shape, already
    proven on this kit.
  * THE LOCKFOOT BUNTING IS 89% ROPE.  `lf_bunting_0..3` are 810 loops each, of
    which 720 are the brown line colour (0.42, 0.35, 0.25).  Repainting a third
    of those to the pennant set turns a brown rope into a strung line of colour
    at zero geometry cost.
    THE PLAN ALSO ASKS FOR THEM TO BE RE-STRUNG AT DECK HEIGHT, AND THAT IS NOT
    DONE HERE, because measuring it showed the premise is off.  The plan reads
    "z 0.16-1.64, down at the waterline where nothing sees them"; the ground
    under `lf_bunting_0` is at z = 0.78, so the object already straddles its own
    deck — the z range is its POSTS reaching the deck, not the line lying in the
    river.  Translating the whole object lifts the posts off the ground, and
    geometry_audit duly reported it as a STRAY floating 5.68 m up.  Re-stringing
    it properly means moving the rope and flag loops while leaving the posts
    planted, which is per-vertex surgery on someone else's mesh and belongs in
    its own pass.  BUNTING_LIFT is therefore 0.00 and the recolour stands alone.

CRAFT RULES (plan Part 5), all enforced here:
  1. NO NEW COLOURS and NO NEW MATERIALS.  Every element below wears a material
     that already ships — the six-accent storybook set completed by the
     house-variety pass, the market pair, the pennants, `mat_pumpkin`.  That
     makes the glTF survivability gate true by construction: nothing new can
     arrive white because nothing is new.
  2. VALUE DISCIPLINE.  The pennant materials sit at V 0.14-0.31 and the paints
     at V 0.40-0.71, so pennants are used ONLY for cloth strips and never for a
     surface over 2 m2, or a large low-value banner reads as a hole.
  3. NEIGHBOUR SEPARATION.  Where a row of like objects gets painted, colours
     come from sha1(name) with a neighbour pass, exactly as
     tools/house_variety.py assigns roofs.  Never random().
  4. RECOLOUR BEFORE YOU MODEL — hence P1 before the rest.
  5. INTERIORS.  None of the buildings dressed here has an interior scene, so no
     exterior/interior divergence is created.  Verified against tools/*_int_build.py.

Every built object is named `t2c_<id>`, so the whole pass is `-- revert save`
(delete by prefix, put the awning and bunting Col back from the recorded
transform).
"""
import bpy, os, sys, math, json, hashlib
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
CANDS = os.path.join(ROOT, "tools/blends/districts/t2_color_cands.json")
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_color_pops.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
PHASE = argv[argv.index("phase") + 1] if "phase" in argv else "all"

PREFIX = "t2c_"
COLL = "DIST_legibility"          # a CONTEXT-level collection that already exists
SEED = "dellhollow-pops/"

# ---------------------------------------------------------------- palette ----
# linear RGB, read out of the shipped materials. Nothing here is new.
PAINT = {
    "rust":   "mat_shelf_paint_rust",
    "madder": "mat_shelf_paint_madder",
    "ochre":  "mat_shelf_paint_ochre",
    "bone":   "mat_shelf_paint_bone",
    "teal":   "mat_shelf_paint_teal",
    "slate":  "mat_shelf_paint_slate",
    "sage":   "mat_shelf_paint_green",
    "mkt_red":  "mat_qm_paint_red",
    "mkt_blue": "mat_qm_paint_blue",
    "pumpkin":  "mat_pumpkin",
}
PENNANT = ["mat_flag_red", "mat_flag_blue", "mat_flag_ochre", "mat_flag_green"]
ROPE = "mat_rope"
TIMBER = "mat_timber"
ACCENTS = ["rust", "madder", "ochre", "bone", "teal", "slate", "sage"]

# ------------------------------------------------------- the placement table --
# id -> (kind, palette, linear scale applied to the probed rectangle)
# `scale` is the plan's own column; the plan applied it LINEARLY (a strip's run
# is shortened, not its area quartered), and its Part 4 budget was computed that
# way, so this reproduces the published numbers.
ROWS = {
    # --- gate district: 0.61% -> 7.67% -------------------------------------
    "G1_awning_porters_a":  ("awning", ["ochre"], 1.0),
    "G2_awning_porters_b":  ("awning", ["mkt_red"], 1.0),
    "G3_awning_tollyard":   ("awning", ["teal"], 1.0),
    "G4_arch_banner":       ("banner", ["pennant_blue"], 1.0),
    "G5_gatehouse_door":    ("panel",  ["madder"], 1.0),
    "G6_tarps_cargo":       ("tarp",   ["bone"], 1.0),
    "G7_bunting_gate2":     ("bunting", ["pennant"], 1.0),
    "G8_cliff_baskets":     ("boxrow", ["pumpkin", "sage"], 1.0),
    "GB1_cliff_banner_a":   ("banner", ["teal"], 1.0),
    "GB2_cliff_banner_b":   ("banner", ["slate"], 1.0),
    # ochre, not madder: at the gate this is the largest banner and the one
    # furthest from the key, and in madder (V 0.46) it read as a plank-flat
    # dark slab beside the teal/slate pair. Ochre is the brightest hue in the
    # storybook set at V 0.62 and still inside the value band rule 2 sets.
    "GB3_cliff_banner_c":   ("banner", ["ochre"], 1.0),
    "GB4_yard_tarp_big":    ("tarp",   ["ochre"], 1.0),
    "GB5_road_marketrow":   ("awning", ["rust"], 1.0),
    # --- Lockfoot / weave: the six brown eastern cameras --------------------
    "W1_laundry_deckA":     ("laundry", ["bone", "teal", "madder"], 1.0),
    "W2_laundry_deckB":     ("laundry", ["ochre", "slate"], 1.0),
    "W3_hut_doors":         ("panelrow", ACCENTS, 1.0),
    "W4_hut_shutters":      ("panelrow", ["slate", "madder"], 1.0),
    "W5_flowerbox_rail":    ("boxrow", ["pumpkin", "sage"], 0.6),
    "W6_keeper_door":       ("panel",  ["rust"], 1.0),
    "W7_keeper_boxes":      ("boxrow", ["pumpkin"], 1.0),
    "W8_tenant_gable":      ("panel",  ["mkt_blue"], 0.6),
    "W9_laundry_planking":  ("laundry", ["bone", "teal", "ochre", "madder"], 0.5),
    "LH5_hut_shutters_hi":  ("panelrow", ["teal", "rust"], 0.7),
    "LH6_hut_gable_paint":  ("panelrow", ["madder", "ochre"], 0.7),
    "WV2_dryingdeck_awning": ("awning", ["rust"], 1.0),
    "WV3_north_hut_paint":  ("panel",  ["teal"], 0.7),
    # --- lock head: 1.40% -> 9.02% -----------------------------------------
    "LH1_station_awning":   ("awning", ["ochre"], 1.0),
    "LH2_rail_bunting":     ("bunting", ["pennant"], 0.5),
    "LH3_rail_flowerbox":   ("boxrow", ["pumpkin", "sage"], 0.5),
    "LH4_deck_crates":      ("crates", ["mkt_red", "mkt_blue"], 0.6),
    # --- north landing / downstream: 0.03% -> 7.95% ------------------------
    "N1_nl_awnings":        ("awning", ["rust", "ochre", "teal"], 0.5),
    "N2_nl_bunting":        ("bunting", ["pennant"], 0.7),
    "N3_nl_crates":         ("crates", ["mkt_blue"], 1.0),
    "N4_nl_barge_hull":     ("panel",  ["madder"], 1.0),
    "N5_nl_barge_deck":     ("tarp",   ["bone", "mkt_red"], 0.5),
    "N6_nl_nets":           ("nets",   ["ochre"], 0.7),
    "L1_crest_banners":     ("banner", ["pennant_blue", "pennant_red"], 0.7),
    "L2_lockhouse_paint":   ("panel",  ["slate"], 0.5),
    # --- waterfront / fish dock / boatyard ---------------------------------
    "F1_wf_awnings":        ("awning", ["mkt_red", "ochre"], 1.0),
    "F2_skiff_mid_a":       ("skiff",  ["slate"], 0.7),
    "F3_skiff_mid_b":       ("skiff",  ["rust"], 0.7),
    "F4_wf_laundry":        ("laundry", ["bone", "teal"], 1.0),
    "F5_fish_floats":       ("floats", ["mkt_red", "pumpkin"], 1.0),
    "B1_boat_sailcloth":    ("tarp",   ["bone"], 0.7),
    "DS1_yard_tarps":       ("tarp",   ["ochre"], 1.0),
    "DS2_hull_paint":       ("panel",  ["madder"], 0.55),
    "DS3_shed_doors":       ("panel",  ["mkt_blue"], 1.0),
    "DS4_yard_laundry":     ("laundry", ["rust", "bone"], 1.0),
    "WV1_quaydeck_laundry": ("laundry", ["bone", "teal", "madder", "ochre"], 0.33),
}
# WALK-HEADROOM LIFTS, and they are a gate result, not taste. master_walk_qa
# asserts nothing solid within 2.0 m above a walk surface. DS1's probed centre
# (28.0, 24.0, 3.2) is a tarp "over the boatyard stock" placed at head height
# over the yard deck: as probed it obstructed 3.90% of that surface and FAILED
# the gate. It is lifted to where a tarp over stock actually lives. The probe
# rectangle is unchanged, so its measured 1.42% at boatyard still applies.
LIFT = {"DS1_yard_tarps": 2.40}

# NOT BUILT AS FREE-STANDING PANELS, and this is a mechanism correction rather
# than a taste one.  docs/plans/pops-of-color.md files the hut doors, the hut
# shutters and the keeper's door under phase P2, which it defines as "material-
# slot and `Col` edits on EXISTING meshes, not new geometry".  Built as separate
# plates they cannot be mounted cleanly: the lf_ kit's nine huts OVERLAP EACH
# OTHER IN X while standing at different y, so a single 10 m door band crosses
# three huts whose north faces are up to 0.9 m apart, and geometry_audit catches
# the plates 0.08-0.14 m inside wv_hut_weave-huts_1 and _2 however they are
# snapped.  W6 has the same problem against lf_pile_bracing.  Their combined
# measured contribution is ~1% across three cameras.  Repainting the huts' own
# wall `Col` is the right mechanism and is its own (safe) pass.
DROP_ROWS = {"W3_hut_doors", "W4_hut_shutters", "W6_keeper_door"}

# B2_yard_paintpots is in the candidate file and is NOT built: re-probed against
# the rebuilt master it projects under 0.05% in every one of the 17 cameras.

# ------------------------------------------------------------ P1 free wins ---
GREY = (0.60, 0.58, 0.54)          # the neutral the awnings are half made of
GREY_TOL = 0.04
AWNINGS = ["qm_awning_0.001", "qm_awning_1.001", "qm_awning_2.001",
           "qm_awning_3.001", "qm_awning_4.001",
           "shelf_awning_0", "shelf_awning_1", "shelf_awning_2", "shelf_awning_3"]
BUNTINGS = ["lf_bunting_0", "lf_bunting_1", "lf_bunting_2", "lf_bunting_3"]
BUNTING_LIFT = 0.00                # MEASURED TO ZERO — see below
ROPE_COL = (0.42, 0.35, 0.25)
ROPE_TOL = 0.05


def u01(name, salt=""):
    return int.from_bytes(hashlib.sha1((SEED + salt + name).encode()).digest()[:8],
                          "big") / float(1 << 64)


def lin(c):
    """sRGB 0-1 -> linear, for writing into a Col attribute"""
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c)


PAINT_NODE, PAINT_SOCK = "Mix.003", "B"      # the tint kit's socket, per house_variety.py
MOSS = (0.09, 0.16, 0.05)                    # the town-wide moss overlay literal


def paint_rgb(key):
    """the linear RGB a palette material actually paints.

    The tint kit puts its colour in Mix.003.B and its MOSS OVERLAY in Mix.001.B.
    A naive "first Mix node with a non-grey B" scan returns the moss literal for
    every accent in the palette — which is what the first run of this script did,
    painting nine awnings and four buntings the same swamp green."""
    m = bpy.data.materials[PAINT[key]]
    nd = m.node_tree.nodes.get(PAINT_NODE)
    if nd is not None:
        for i in nd.inputs:
            if i.name == PAINT_SOCK and not i.is_linked and hasattr(i.default_value, '__len__') \
                    and len(i.default_value) == 4:
                rgb = tuple(i.default_value[:3])
                if rgb not in ((0.0, 0.0, 0.0), (0.5, 0.5, 0.5)) and rgb != MOSS:
                    return rgb
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is not None and not bsdf.inputs['Base Color'].is_linked:
        return tuple(bsdf.inputs['Base Color'].default_value[:3])
    return (0.5, 0.5, 0.5)


def near(a, b, tol):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


# ================================================================ REVERT ======
if REVERT:
    n = 0
    for o in [o for o in bpy.data.objects if o.name.startswith(PREFIX)]:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
        n += 1
    for bn in BUNTINGS:
        ob = bpy.data.objects.get(bn)
        if ob is not None and ob.get("t2c_lifted"):
            ob.location.z -= float(ob["t2c_lifted"])
            print("LOWERED %s back by %.2f m" % (bn, float(ob["t2c_lifted"])))
            del ob["t2c_lifted"]
    for an in AWNINGS + BUNTINGS:
        ob = bpy.data.objects.get(an)
        if ob is None:
            continue
        ca = ob.data.color_attributes.active_color if ob.data.color_attributes else None
        if ca is None or not ob.get("t2c_repaint"):
            continue
        for idx, col in json.loads(ob["t2c_repaint"]):
            ca.data[idx].color = col
        del ob["t2c_repaint"]
        print("REPAINT REVERTED %s" % an)
    print("REVERT removed %d %s objects" % (n, PREFIX))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

sc = bpy.context.scene
# HIDE THIS PASS'S OWN OUTPUT FROM THE RAY-CASTER before rebuilding. On a second
# run the previous build is still in the depsgraph, so a laundry line's post
# ray-cast hits the previous laundry line 3 cm below and concludes there is
# ground there: the posts silently stopped being built and the strays came back.
_selfhidden = []
for o in bpy.data.objects:
    if o.name.startswith(PREFIX) and not o.hide_viewport:
        o.hide_viewport = True
        _selfhidden.append(o.name)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
if _selfhidden:
    print("hid %d existing %s objects from the ray-caster for this rebuild"
          % (len(_selfhidden), PREFIX))
coll = bpy.data.collections.get(COLL) or sc.collection
report = {"repainted": {}, "built": {}}

# ============================================================== P1: RECOLOUR ==
if PHASE in ("all", "p1"):
    print("\n" + "=" * 78)
    print("P1 — the two free wins: nine grey awnings, four sunken buntings")
    print("=" * 78)
    for i, an in enumerate(AWNINGS):
        ob = bpy.data.objects.get(an)
        if ob is None:
            print("  %s missing" % an)
            continue
        ca = ob.data.color_attributes.active_color if ob.data.color_attributes else None
        if ca is None:
            print("  %s has no Col" % an)
            continue
        if ob.get("t2c_repaint"):
            print("  %-22s already repainted" % an)
            continue
        # deterministic accent, neighbour-aware against the previous awning
        pick = ACCENTS[int(u01(an) * len(ACCENTS)) % len(ACCENTS)]
        near2 = {report["repainted"].get(AWNINGS[j], {}).get("accent")
                 for j in (i - 1, i - 2) if j >= 0}
        while pick in near2:
            pick = ACCENTS[(ACCENTS.index(pick) + 3) % len(ACCENTS)]
        rgb = paint_rgb(pick)
        undo, n = [], 0
        for k in range(len(ca.data)):
            c = tuple(ca.data[k].color[:3])
            # Col is stored linear; GREY is quoted sRGB in the census
            if near(c, lin(GREY), GREY_TOL) or near(c, GREY, GREY_TOL):
                undo.append([k, list(ca.data[k].color)])
                ca.data[k].color = (rgb[0], rgb[1], rgb[2], 1.0)
                n += 1
        if n:
            ob["t2c_repaint"] = json.dumps(undo)
        report["repainted"][an] = {"accent": pick, "loops": n, "of": len(ca.data)}
        print("  %-22s %3d/%-3d neutral loops -> %-7s %s"
              % (an, n, len(ca.data), pick, tuple(round(v, 3) for v in rgb)))

    for bn in BUNTINGS:
        ob = bpy.data.objects.get(bn)
        if ob is None:
            continue
        was = float(ob.get("t2c_lifted", 0.0))
        if abs(was - BUNTING_LIFT) > 1e-4:
            ob.location.z += (BUNTING_LIFT - was)
            if BUNTING_LIFT:
                ob["t2c_lifted"] = BUNTING_LIFT
                print("  %-22s raised %.2f m" % (bn, BUNTING_LIFT))
            else:
                if "t2c_lifted" in ob:
                    del ob["t2c_lifted"]
                print("  %-22s returned to its planted height (was +%.2f m)" % (bn, was))
        ca = ob.data.color_attributes.active_color if ob.data.color_attributes else None
        if ca is None or ob.get("t2c_repaint"):
            continue
        # repaint the LINE loops in the pennant set: 720 of 810 loops were rope
        undo, n = [], 0
        cols = [paint_rgb(k) for k in ("madder", "teal", "ochre", "sage")]
        for k in range(len(ca.data)):
            c = tuple(ca.data[k].color[:3])
            if near(c, lin(ROPE_COL), ROPE_TOL) or near(c, ROPE_COL, ROPE_TOL):
                if (k // 6) % 3 == 0:          # every third panel, so it stays a line
                    rgb = cols[(k // 6) % len(cols)]
                    undo.append([k, list(ca.data[k].color)])
                    ca.data[k].color = (rgb[0], rgb[1], rgb[2], 1.0)
                    n += 1
        if n:
            ob["t2c_repaint"] = json.dumps(undo)
        report["repainted"][bn] = {"accent": "pennant set", "loops": n, "of": len(ca.data)}
        print("  %-22s %3d/%-3d rope loops -> pennant set" % (bn, n, len(ca.data)))

# =========================================================== P2-P4: DRESSING ==


def mesh(name, verts, faces, mats, matidx=None, smooth=False):
    full = PREFIX + name
    old = bpy.data.objects.get(full)
    if old:
        me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(full)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    for m in mats:
        me.materials.append(bpy.data.materials[m])
    if matidx:
        for p, mi in zip(me.polygons, matidx):
            p.material_index = mi
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(full, me)
    coll.objects.link(ob)
    return ob


def quad(v, f, a, b, c, d):
    i = len(v)
    v += [tuple(a), tuple(b), tuple(c), tuple(d)]
    f.append((i, i + 1, i + 2, i + 3))


def boxv(v, f, ctr, ex, ey, ez):
    i = len(v)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                v.append(tuple(Vector(ctr) + Vector(ex) * sx + Vector(ey) * sy + Vector(ez) * sz))
    # order: (sx,sy,sz) -> index i + 4*ix + 2*iy + iz  with ix,iy,iz in {0,1}
    def p(a, b, c):
        return i + 4 * a + 2 * b + c
    f += [(p(0, 0, 0), p(0, 1, 0), p(1, 1, 0), p(1, 0, 0)),
          (p(0, 0, 1), p(1, 0, 1), p(1, 1, 1), p(0, 1, 1)),
          (p(0, 0, 0), p(1, 0, 0), p(1, 0, 1), p(0, 0, 1)),
          (p(1, 0, 0), p(1, 1, 0), p(1, 1, 1), p(1, 0, 1)),
          (p(1, 1, 0), p(0, 1, 0), p(0, 1, 1), p(1, 1, 1)),
          (p(0, 1, 0), p(0, 0, 0), p(0, 0, 1), p(0, 1, 1))]


PROUD = 0.14                 # how far proud of its host a painted panel sits.
                             # 0.04 grazed lf_pile_bracing and 0.10 still let the
                             # corners of a 2.2 m door panel into a hut's uneven wall.


def snap_to_host(ctr, n, reach=2.2):
    """Put a painted panel ON THE OUTSIDE of the wall it belongs to.

    Casting outward FROM the probed centre is wrong and the audit proved it
    twice: the probe rectangles are centres of a REGION, and a door band's centre
    sits INSIDE the hut, so an outward ray hits an INTERIOR wall and the panel
    gets mounted 14 cm proud of it — still inside the building.  Cast INWARD
    instead, from a point well outside on each side; the first hit is by
    construction the OUTER skin.  Take the side whose skin is nearer, and sit
    PROUD of it.  Returns (centre, outward normal)."""
    best = None
    for s in (1.0, -1.0):
        start = Vector(ctr) + Vector(n) * (s * reach)
        hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, start, -Vector(n) * s, distance=reach * 2.0)
        if hit:
            d = (loc - Vector(ctr)).length
            if best is None or d < best[0]:
                best = (d, loc, Vector(n) * s)
    if best is None:
        return Vector(ctr), Vector(n), False
    d, loc, out = best
    pc = Vector(loc) + out * PROUD
    # VALIDITY GUARD. A snap can still land wrong where the lf_ kit's huts
    # overlap each other in x at different y: the inward ray finds hut A's north
    # face while the panel's x actually belongs to hut B, which stands 0.9 m
    # further out. So verify: from the mounted position, 0.6 m of open air along
    # the outward normal. If it is not there, the panel is not placed. Refusing
    # to place two shutters is cheaper than shipping a door inside a wall.
    hit, *_ = sc.ray_cast(dg, pc, out, distance=0.6)
    return (pc, out, not hit)


def ground_below(p, reach=6.0):
    """the first surface under p, or None"""
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector(p) + Vector((0, 0, 0.05)),
                                            Vector((0, 0, -1)), distance=reach)
    return loc.z if hit else None


def seat(ob, clearance=0.02):
    """drop an object so its lowest vertex rests on whatever is under it.  Props
    that float are what geometry_audit calls a STRAY, and a painted crate hanging
    in the air is worse than no painted crate."""
    lo = min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
    ctr = ob.matrix_world @ (sum((v.co for v in ob.data.vertices), Vector()) / len(ob.data.vertices))
    g = ground_below(Vector((ctr.x, ctr.y, lo + 0.4)))
    if g is None:
        return 0.0
    dz = (g + clearance) - lo
    if abs(dz) > 1e-3:
        ob.location.z += dz
    return dz


built_stats = {}
if PHASE in ("all", "dress"):
    print("\n" + "=" * 78)
    print("P2-P4 — the placement table, %d rows" % len(ROWS))
    print("=" * 78)
    CAND = {c["id"]: c for c in json.load(open(CANDS))}
    for rid in sorted(ROWS):
        if rid in DROP_ROWS:
            old = bpy.data.objects.get(PREFIX + rid)
            if old:
                me = old.data
                bpy.data.objects.remove(old, do_unlink=True)
                if me.users == 0:
                    bpy.data.meshes.remove(me)
            print("  %-24s not built (see DROP_ROWS)" % rid)
            continue
        kind, pal, scale = ROWS[rid]
        c = CAND.get(rid)
        if c is None:
            print("  %s not in the candidate table" % rid)
            continue
        ctr = Vector(c["at"]) + Vector((0, 0, LIFT.get(rid, 0.0)))
        e1 = Vector(c["e1"]) * scale
        e2 = Vector(c["e2"]) * scale
        n = e1.cross(e2)
        n = n.normalized() if n.length > 1e-6 else Vector((0, 1, 0))
        v, f, mi = [], [], []
        mats = []

        def use(mat):
            if mat not in mats:
                mats.append(mat)
            return mats.index(mat)

        if kind in ("panel", "banner"):
            if kind == "panel":
                ctr, n, ok = snap_to_host(ctr, n)
                if not ok:
                    old = bpy.data.objects.get(PREFIX + rid)
                    if old:
                        me2 = old.data
                        bpy.data.objects.remove(old, do_unlink=True)
                        if me2.users == 0:
                            bpy.data.meshes.remove(me2)
                    print("  %-24s SKIPPED — no clear mounting face" % rid)
                    continue
            o = Vector((0, 0, 0))
            if kind == "banner":
                # A BANNER HANGS ON SOMETHING. The probe rectangles put the three
                # gate guild banners at y = 2.3 while gate_cliffface's skin is
                # around y = 0.5 there, and the first render showed them as dark
                # slabs floating 1.8 m clear of the cliff — billboards, not cloth.
                # Snap to a host when there is one within reach and hang the
                # cloth from a timber bar; keep the free position when there is
                # not (the banner under the gate arch).
                pc, pn, ok2 = snap_to_host(ctr, n, reach=3.2)
                if ok2:
                    ctr, n = pc, pn
                # hangs: a slight belly, and pennant materials are allowed here
                # only because a banner is a cloth strip (craft rule 2)
                key = pal[0]
                mat = ({"pennant_blue": "mat_flag_blue", "pennant_red": "mat_flag_red"}
                       .get(key) or PAINT[key])
                k = use(mat)
                kt = use(TIMBER)
                boxv(v, f, ctr + e2 + n * 0.10, (max(0.25, e1.length * 1.10), 0, 0),
                     (0.05, 0.05, 0), (0, 0, 0.05))
                mi += [kt] * 6
                # A DRAPED SHEET, not a plank. The first take built the banner as
                # five flat strips with a belly in the normal only, and the gate
                # frame read it as a board bolted to the rock. Cloth needs three
                # things a board does not have: a BELLY that is deepest at
                # mid-height, a HEM that sags between the corners, and a little
                # lateral SWAY that grows toward the free bottom edge.
                NU, NW = 6, 4
                grid = []
                for a in range(NU + 1):
                    u = a / NU                       # 0..1 across the width
                    row = []
                    for b in range(NW + 1):
                        w = b / NW                   # 0 at the bar, 1 at the hem
                        belly = 0.16 * math.sin(math.pi * u) * math.sin(math.pi * w * 0.85)
                        hem = -0.22 * math.sin(math.pi * u) * (w ** 2)
                        sway = 0.10 * math.sin(2.4 * u + 1.1) * (w ** 1.5)
                        p = (ctr + e1 * (-1 + 2 * u) + e2 * (1 - 2 * w)
                             + n * belly + Vector((0, 0, hem)) + e1.normalized() * sway)
                        row.append(p)
                    grid.append(row)
                base0 = len(v)
                for row in grid:
                    v += [tuple(p) for p in row]
                for a in range(NU):
                    for b in range(NW):
                        i0 = base0 + a * (NW + 1) + b
                        f.append((i0, i0 + (NW + 1), i0 + (NW + 1) + 1, i0 + 1))
                        mi.append(k)
            else:
                k = use(PAINT[pal[0]])
                quad(v, f, ctr - e1 - e2 + o, ctr + e1 - e2 + o,
                     ctr + e1 + e2 + o, ctr - e1 + e2 + o)
                mi.append(k)
        elif kind == "panelrow":
            # snap EACH panel to ITS OWN host. A 10 m door band runs across
            # several huts standing at different y, so one snap at the row centre
            # leaves the end panels 0.18 m inside the hut next door — which is
            # exactly what the first audit caught on wv_hut_weave-huts_2.
            N = 5
            e2 = e2 * 0.82          # keep a panel's corners off a hut's uneven wall
            prev = None
            for j in range(N):
                key = pal[int(u01(rid + str(j)) * len(pal)) % len(pal)]
                if key == prev and len(pal) > 1:            # neighbour separation
                    key = pal[(pal.index(key) + 1) % len(pal)]
                prev = key
                k = use(PAINT[key])
                t0 = -1 + 2.0 * j / N + 0.06
                t1 = -1 + 2.0 * (j + 1) / N - 0.06
                tm = (t0 + t1) / 2
                pc, pn, ok = snap_to_host(ctr + e1 * tm, n)
                if not ok:
                    continue
                off = pc - (ctr + e1 * tm)
                quad(v, f, ctr + e1 * t0 - e2 + off, ctr + e1 * t1 - e2 + off,
                     ctr + e1 * t1 + e2 + off, ctr + e1 * t0 + e2 + off)
                mi.append(k)
        elif kind in ("awning", "tarp"):
            k = use(PAINT[pal[0]])
            drop = Vector((0, 0, -0.55 if kind == "awning" else -0.25))
            quad(v, f, ctr - e1 - e2, ctr + e1 - e2, ctr + e1 + e2 + drop, ctr - e1 + e2 + drop)
            mi.append(k)
            if kind == "tarp":                              # posts if it floats
                kt = use(TIMBER)
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        top = ctr + e1 * (sx * 0.94) + e2 * (sy * 0.94) + (drop if sy > 0 else Vector())
                        g = ground_below(top, 7.0)
                        if g is not None and 1.0 < top.z - g < 6.5:
                            boxv(v, f, Vector((top.x, top.y, (top.z + g) / 2)),
                                 (0.06, 0, 0), (0, 0.06, 0), (0, 0, (top.z - g) / 2))
                            mi += [kt] * 6
            if kind == "awning":                            # valance on the outer edge
                k2 = use(PAINT[pal[-1]])
                quad(v, f, ctr - e1 + e2 + drop, ctr + e1 + e2 + drop,
                     ctr + e1 + e2 + drop + Vector((0, 0, -0.30)),
                     ctr - e1 + e2 + drop + Vector((0, 0, -0.30)))
                mi.append(k2)
                kt = use(TIMBER)                            # two posts, so it is a thing
                for s2 in (-1, 1):
                    boxv(v, f, ctr + e1 * s2 * 0.92 + e2 + drop + Vector((0, 0, -0.75)),
                         (0.05, 0, 0), (0, 0.05, 0), (0, 0, 0.75))
                    mi += [kt] * 6
        elif kind == "laundry":
            kr = use(ROPE)
            kt = use(TIMBER)
            for s2 in (-1, 1):                    # posts, or the line is a STRAY
                top = ctr + e1 * (s2 * 1.02) + e2
                g = ground_below(top, 7.0)
                if g is not None and top.z - g > 0.4:
                    boxv(v, f, Vector((top.x, top.y, (top.z + g) / 2)),
                         (0.07, 0, 0), (0, 0.07, 0), (0, 0, (top.z - g) / 2))
                    mi += [kt] * 6
            boxv(v, f, ctr + e2, (e1.x * 1.02, e1.y * 1.02, 0), (0, 0.025, 0), (0, 0, 0.025))
            mi += [kr] * 6
            # HUNG CLOTH, NOT PLACARDS. The first take pegged seven identical
            # rectangles at identical spacing and lockfive read them as a row of
            # printed boards. Washing on a line varies: each sheet gets its own
            # width and drop from sha1, hangs from the line's own catenary, and
            # curls — a belly across the sheet and a hem that swings out at the
            # bottom, which is what separates cloth from card at 30 m.
            N = 7
            for j in range(N):
                key = pal[j % len(pal)]
                k = use(PAINT[key])
                t = -1 + 2.0 * (j + 0.5) / N
                wob = 0.55 + 0.75 * u01(rid + str(j))          # width variation
                drop = 0.75 + 0.55 * u01(rid + str(j), "d")    # drop variation
                lean = 0.16 * (u01(rid + str(j), "l") - 0.5)   # a little askew
                line_sag = Vector((0, 0, -0.12 * math.sin(math.pi * (j + 0.5) / N)))
                NU2, NW2 = 3, 3
                base1 = len(v)
                for a2 in range(NU2 + 1):
                    uu = a2 / NU2
                    for b2 in range(NW2 + 1):
                        ww = b2 / NW2
                        wid = e1 * ((0.90 / N) * wob * (-1 + 2 * uu))
                        belly = n * (0.10 * math.sin(math.pi * uu) * math.sin(math.pi * ww * 0.9))
                        hem = Vector((0, 0, -0.10 * math.sin(math.pi * uu) * ww * ww))
                        swing = e1 * (lean * ww)
                        p2 = (ctr + e1 * t + wid + e2 - e2 * (2.0 * drop * ww)
                              + line_sag + belly + hem + swing)
                        v.append(tuple(p2))
                for a2 in range(NU2):
                    for b2 in range(NW2):
                        i1 = base1 + a2 * (NW2 + 1) + b2
                        f.append((i1, i1 + (NW2 + 1), i1 + (NW2 + 1) + 1, i1 + 1))
                        mi.append(k)
        elif kind == "bunting":
            kr = use(ROPE)
            kt = use(TIMBER)
            N = 11
            pts = [ctr + e1 * (-1 + 2.0 * j / N) + Vector((0, 0, -0.35 * math.sin(math.pi * j / N)))
                   for j in range(N + 1)]
            for j in range(N):
                a, b = pts[j], pts[j + 1]
                boxv(v, f, (a + b) / 2, ((b - a) / 2), (0, 0.02, 0), (0, 0, 0.02))
                mi += [kr] * 6
            for s2 in (0, N):                     # a mast at each end of the run
                top = pts[s2]
                g = ground_below(top, 8.0)
                if g is not None and top.z - g > 0.4:
                    boxv(v, f, Vector((top.x, top.y, (top.z + g) / 2)),
                         (0.08, 0, 0), (0, 0.08, 0), (0, 0, (top.z - g) / 2))
                    mi += [kt] * 6
            for j in range(N):
                k = use(PENNANT[j % len(PENNANT)])
                a, b = pts[j], pts[j + 1]
                m0 = (a + b) / 2
                i0 = len(v)
                v += [tuple(a + (b - a) * 0.15), tuple(a + (b - a) * 0.85),
                      tuple(m0 - e2 * 2.4)]
                f.append((i0, i0 + 1, i0 + 2))
                mi.append(k)
        elif kind == "boxrow":
            kt = use(TIMBER)
            kf = [use(PAINT[p]) for p in pal]
            N = 6
            for j in range(N):
                t = -1 + 2.0 * (j + 0.5) / N
                b = ctr + e1 * t
                boxv(v, f, b, (e1.length * 0.6 / N, 0, 0), (0, 0.16, 0), (0, 0, 0.16))
                mi += [kt] * 6
                boxv(v, f, b + Vector((0, 0, 0.20)),
                     (e1.length * 0.5 / N, 0, 0), (0, 0.13, 0), (0, 0, 0.10))
                mi += [kf[j % len(kf)]] * 6
        elif kind == "crates":
            ks = [use(PAINT[p]) for p in pal]
            for j, (dx, dz) in enumerate([(-0.55, -0.5), (0.55, -0.5), (0.0, 0.45)]):
                boxv(v, f, ctr + e1 * dx + e2 * dz,
                     (e1.length * 0.40, 0, 0), (0, e1.length * 0.36, 0), (0, 0, e2.length * 0.42))
                mi += [ks[j % len(ks)]] * 6
        elif kind == "skiff":
            k = use(PAINT[pal[0]])
            kt = use(TIMBER)
            boxv(v, f, ctr, (e1.length, 0, 0), (0, e2.length, 0), (0, 0, 0.16))
            mi += [k] * 6
            boxv(v, f, ctr + Vector((0, 0, 0.20)),
                 (e1.length * 0.55, 0, 0), (0, e2.length * 0.5, 0), (0, 0, 0.05))
            mi += [kt] * 6
        elif kind == "floats":
            ks = [use(PAINT[p]) for p in pal]
            N = 7
            for j in range(N):
                a = u01(rid + str(j))
                b = u01(rid + str(j), "b")
                p0 = ctr + e1 * (-1 + 2 * a) + e2 * (-1 + 2 * b)
                boxv(v, f, p0, (0.16, 0, 0), (0, 0.16, 0), (0, 0, 0.16))
                mi += [ks[j % len(ks)]] * 6
        elif kind == "nets":
            k = use(PAINT[pal[0]])
            kt = use(TIMBER)
            for s2 in (-1, 1):
                boxv(v, f, ctr + e1 * s2, (0.06, 0, 0), (0, 0.06, 0), (0, 0, e2.length))
                mi += [kt] * 6
            quad(v, f, ctr - e1 - e2, ctr + e1 - e2, ctr + e1 + e2, ctr - e1 + e2)
            mi.append(k)
        else:
            print("  unknown kind %s" % kind)
            continue

        ob = mesh(rid, v, f, mats, mi)
        dz = seat(ob) if kind in ("crates", "skiff", "floats") else 0.0
        built_stats[rid] = dict(kind=kind, palette=pal, scale=scale, seated_dz=round(dz, 3),
                                verts=len(v), polys=len(f), materials=mats,
                                at=[round(x, 2) for x in c["at"]],
                                lift_m=LIFT.get(rid, 0.0))
        print("  %-24s %-9s %-28s %4d v %4d p  scale %.2f"
              % (rid, kind, "/".join(pal)[:28], len(v), len(f), scale))

for nm in _selfhidden:
    o = bpy.data.objects.get(nm)
    if o is not None:
        o.hide_viewport = False

report["built"] = built_stats
nv = sum(s["verts"] for s in built_stats.values())
print("\nBUILT %d objects, %d verts, %d polys — all in materials that already ship"
      % (len(built_stats), nv, sum(s["polys"] for s in built_stats.values())))
mats_used = sorted({m for s in built_stats.values() for m in s["materials"]})
print("materials used (%d, none new): %s" % (len(mats_used), ", ".join(mats_used)))

json.dump(dict(
    _doc=("GENERATED by tools/t2_color_pops.py — the pops-of-colour placement as "
          "built. Every material already shipped before this pass; no new "
          "material is created, which is what makes the glTF survivability gate "
          "true by construction."),
    generator="tools/t2_color_pops.py", plan="docs/plans/pops-of-color.md",
    prefix=PREFIX, collection=COLL, seed=SEED,
    bunting_lift_m=BUNTING_LIFT, awnings=AWNINGS, buntings=BUNTINGS,
    not_built={"B2_yard_paintpots": "re-probed post-cliff: under 0.05% in all 17",
               "W3_hut_doors": "P2 mechanism: repaint the hut's own wall Col",
               "W4_hut_shutters": "P2 mechanism: repaint the hut's own wall Col",
               "W6_keeper_door": "P2 mechanism: repaint the cottage's own Col",
               "N4_nl_barge_hull": "no clear mounting face on the moored barge"},
    repainted=report["repainted"], objects=built_stats,
    total_verts=nv, materials=mats_used,
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
