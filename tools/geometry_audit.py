"""geometry_audit.py — reusable geometry-coherence audit for a town district.

  Blender -b <blend> -P tools/geometry_audit.py -- [--region x0,x1,y0,y1]
                                                  [--json out.json] [--top N]
                                                  [--report-only]

Two checks, both aimed at the failure mode a viewer reads instantly as "computer
generated": objects that pass THROUGH each other, and objects that stand on
nothing.

1. INTERSECTIONS  (BVHTree.FromObject overlap + a vertex-inside test)
   For every pair of meshes whose world bounds overlap, the BVH overlap tells us
   the surfaces cross; the severity is then measured properly:
     inside_frac = fraction of the smaller object's vertices that lie INSIDE the
                   larger one (odd/even ray parity against its BVH)
     depth       = how far the deepest of those vertices is from the other's skin
   A shared face-touch (a beam sitting ON a deck, a barrel bedded in gravel) has
   inside_frac ~ 0 and depth ~ 0 and is NOT an offender.  A hull driven through a
   beam has a real fraction of its verts inside and centimetres-to-metres of depth.

2. STRAYS
   A prop with nothing under it and nothing beside it is floating.  Support is a
   downward ray from just under the object's lowest point; attachment is any other
   object's bounds within ATTACH of its own (brackets, hanging lanterns, bunting).
   Parented objects are attached by definition.

Exit code is non-zero when offenders are found (use --report-only to suppress),
so a district pass can run this as a QA gate.
"""
import bpy, sys, os, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# --------------------------------------------------------------------- config
INSIDE_FRAC = 0.08       # > this fraction of verts inside the other object
DEPTH = 0.10             # ... or deeper than this (metres) -> offender
COMPACT = 6.0            # bbox-interlock heuristic only applies below this size
SUPPORT_GAP = 0.75       # a downward ray this long must find something
ATTACH = 0.60            # ... or something within reach sideways/above (bracket, cliff)
WATER_Z = 3.65           # anything whose base is under a water surface is bedded, not floating
MAX_SAMPLE = 260         # verts sampled per object for the inside test

# scatter/vegetation: bushes growing through each other is how planting looks,
# and a rope/bunting chain is a chain.  Pairs where BOTH sides are soft are skipped.
VEG = ("creeper_", "rimclump_", "rimtree_", "tuft_", "seam_tuft", "farcrown",
       "farwallcrown", "wf_creeper_", "wf_rimclump_", "wf_tuft_", "wf_fern_",
       "gate_creeper_", "gate_rimclump_", "gate_rimtree", "gate_tuft_", "gate_fern_",
       "lf_rimclump_", "lf_fern_", "veg_")
FIRE = ("ember", "flame", "fire", "smoke", "spray", "foam", "haze", "fog")
CHAIN = ("seam_swag", "seam_handline", "bunting_")


def soft(n):
    """Vegetation and fire/atmosphere: interpenetration is how they are drawn."""
    return n.startswith(VEG) or any(t in n for t in FIRE)

# things that are not diegetic, are collision-only, or are the ground itself
SKIP_PREFIX = ("walk_", "bar_", "fx_", "cam", "CAM", "REF_")
GROUND = ("shelf_ground", "shelf_paving", "shelf_cliffface",
          "gate_ground", "gate_road", "gate_cliffface", "yard_ground", "seam_bank", "wf_ground", "riverbed",
          "water_pool", "water_mid",
          "water_upstream", "cliff_", "ridge_", "farcrown", "farwallcrown",
          "lock_four_dam", "dam_dam", "lf_ground", "lf_riverbed_tail",
          "lf_farbank_tail", "lf_lock_water", "lf_lock_floor", "lf_dam_boil")
# assemblies that are MODELLED as interpenetrating parts (joists into piles,
# planks over joists, stair stringers into treads...).  Pairs matching one of
# these on both sides are expected to overlap.
SAME_ASSEMBLY = [
    ("yard_planking", "yard_joists"), ("yard_planking", "yard_piles"),
    ("yard_joists", "yard_piles"), ("yard_planking", "yard_bollards"),
    ("yard_joists", "yard_bollards"), ("yard_railings", "yard_planking"),
    ("yard_railings", "yard_joists"), ("yard_railings", "yard_bollards"),
    ("bunting_", "bunting_masts"), ("lantern_", "lantern_brackets"),
    ("lantern_", "lantern_posts"),
    ("seam_kerb", "seam_bank"), ("seam_pile", "seam_bank"),
    ("seam_handline", "seam_railpost"), ("seam_swag", "seam_gatepost"),
    # a post is MEANT to pass through the deck it is driven through
    ("seam_gatepost", "yard_joists"), ("seam_gatepost", "yard_planking"),
    ("seam_railpost", "yard_joists"), ("seam_railpost", "yard_planking"),
    # --- Waterfront: the same deck assembly, one district east -------------
    ("wf_planking", "wf_joists"), ("wf_planking", "wf_piles"),
    ("wf_joists", "wf_piles"), ("wf_railings", "wf_planking"),
    ("wf_railings", "wf_joists"), ("wf_railings", "wf_piles"),
    ("wf_stair_treads", "wf_stair_stringers"), ("wf_stair_treads", "wf_planking"),
    ("wf_stair_stringers", "wf_planking"), ("wf_stair_stringers", "wf_stairmouth"),
    ("wf_stair_treads", "wf_stairmouth"), ("wf_stair_rail", "wf_stair_treads"),
    ("wf_stair_rail", "wf_stair_stringers"),
    ("wf_stage_", "wf_piles"), ("wf_stage_", "wf_joists"), ("wf_stage_", "wf_planking"),
    ("wf_stage_", "wf_clutter"), ("wf_stage_", "wf_fish_gear"),
    ("wf_stage_", "wf_fish_racks"), ("wf_stage_", "wf_lantern_brackets"),
    ("wf_stage_", "wf_winch_load"), ("wf_stage_", "wf_moorings"),
    ("wf_stage_", "wf_railings"),
    ("wf_pile_bracing", "wf_piles"), ("wf_pile_bracing", "wf_joists"),
    ("wf_pile_bracing", "wf_planking"), ("wf_pile_bracing", "wf_stage_"),
    # --- Locksfoot: the same deck assembly, one district further east ------
    ("lf_planking", "lf_joists"), ("lf_planking", "lf_piles"),
    ("lf_joists", "lf_piles"), ("lf_railings", "lf_planking"),
    ("lf_railings", "lf_joists"), ("lf_railings", "lf_piles"),
    ("lf_pile_bracing", "lf_piles"), ("lf_pile_bracing", "lf_joists"),
    ("lf_pile_bracing", "lf_planking"), ("lf_pile_bracing", "lf_stage_"),
    ("lf_stair_treads", "lf_stair_stringers"), ("lf_stair_treads", "lf_planking"),
    ("lf_stair_stringers", "lf_planking"), ("lf_stair_stringers", "lf_joists"),
    ("lf_stage_", "lf_piles"), ("lf_stage_", "lf_joists"), ("lf_stage_", "lf_planking"),
    ("lf_stage_", "lf_clut_"), ("lf_stage_", "lf_shack_piles"),
    ("lf_stage_", "lf_tenant_shack"), ("lf_stage_", "lf_railings"),
    ("lf_clut_", "lf_planking"), ("lf_clut_", "lf_joists"),
    ("lf_lantern_", "lf_planking"), ("lf_lantern_", "lf_joists"),
    ("lf_lantern_", "lf_railings"), ("lf_lantern_", "lf_stage_"),
    ("lf_tenant_shack", "lf_shack_piles"), ("lf_tenant_shack", "lf_ground"),
    ("lf_shack_piles", "lf_ground"), ("lf_piles", "lf_ground"),
    ("lf_mooring_post", "lf_stage_"), ("lf_mooring_post", "lf_planking"),
    ("lf_cleat", "lf_stage_"), ("lf_cleat", "lf_planking"),
    # the lock is ONE machine: walls, floor, coping, gates in their recesses,
    # winches bolted through the coping, sluices set INTO the wall.
    ("lf_lock_wallS", "lf_lock_floor"), ("lf_lock_wallN", "lf_lock_floor"),
    ("lf_lock_wallS", "lf_lock_water"), ("lf_lock_wallN", "lf_lock_water"),
    ("lf_lock_floor", "lf_lock_water"), ("lf_lock_wallS", "lf_gate_"),
    ("lf_lock_wallN", "lf_gate_"), ("lf_gate_recess", "lf_gate_"),
    ("lf_lock_wallS", "lf_gate_recess"), ("lf_lock_wallN", "lf_gate_recess"),
    ("lf_lock_wallS", "lf_sluice"), ("lf_lock_wallN", "lf_sluice"),
    ("lf_lock_wallS", "lf_gate_winch"), ("lf_lock_wallN", "lf_gate_winch"),
    ("lf_lock_wallS", "lf_capstan"), ("lf_lock_wallN", "lf_capstan"),
    ("lf_lock_wallS", "lf_bollard"), ("lf_lock_wallN", "lf_bollard"),
    ("lf_lock_wallS", "lf_clut_"), ("lf_lock_wallN", "lf_clut_"),
    ("lf_lock_wall", "lf_lock_gangbeam"), ("lf_lock_gangbeam", "lf_planking"),
    # the boardwalk is LAID OVER the lock's coping — that is how a coping and a
    # deck meet, and the cap is the thing it is laid on
    ("lf_lock_wall", "lf_planking"), ("lf_lock_wall", "lf_joists"),
    ("lf_lock_wall", "lf_railings"), ("lf_lock_wall", "lf_piles"),
    ("lf_lock_wallS", "lf_ground"), ("lf_lock_wallN", "lf_ground"),
    # the dam is a RUN OF REPEATS: bays touch their neighbours by design, the
    # wheels hang in bearings corbelled off the piers, the gate stands on the
    # crest, and the abutments are what the run lands on.
    ("lf_crest_bay", "lf_crest_bay"), ("lf_spill_bay", "lf_spill_bay"),
    ("lf_crest_bay", "lf_spill_bay"), ("lf_crest_bay", "lf_wheel_"),
    ("lf_spill_bay", "lf_wheel_"), ("lf_wheel_", "lf_wheel_"),
    ("lf_crest_bay", "lf_dam_abut"), ("lf_spill_bay", "lf_dam_abut"),
    ("lf_dam_abut", "lf_crest_gate"), ("lf_crest_bay", "lf_crest_gate"),
    ("lf_dam_abut", "lf_lock_wallN"), ("lf_dam_abut", "lf_ground"),
    ("lf_dam_abut", "lf_farbank_tail"), ("lf_spill_bay", "lf_dam_boil"),
    ("lf_bunting_", "lf_crest_bay"), ("lf_bunting_", "lf_spill_bay"),
    ("lf_barge_", "lf_barge_"), ("lf_barge_", "water_pool"),
    ("wf_lantern_", "wf_stairmouth"), ("wf_lantern_", "wf_fish_racks"),
    ("wf_lantern_", "wf_fish_gear"), ("wf_lantern_", "wf_stage_"),
    # the Boatyard seam's kerbs, piles and posts are MEANT to be driven through
    # the deck that now meets them — the same whitelist the yard already has
    ("seam_pile", "wf_planking"), ("seam_pile", "wf_joists"),
    ("seam_railpost", "wf_planking"), ("seam_railpost", "wf_joists"),
    ("seam_railpost", "wf_railings"), ("seam_gatepost", "wf_planking"),
    ("seam_gatepost", "wf_joists"), ("seam_kerb", "wf_planking"),
    ("seam_kerb", "wf_joists"), ("seam_rock", "wf_planking"),
    ("seam_bank", "wf_piles"),
    ("wf_fish_racks", "wf_fish_catch"), ("wf_fish_racks", "wf_fish_lines"),
    ("wf_fish_gear", "wf_fish_lines"), ("wf_fish_gear", "wf_fish_racks"),
    ("wf_winch_load", "wf_winch_tackle"), ("wf_winch_tackle", "cargo_winch_foot"),
    ("wf_lantern_", "wf_lantern_brackets"), ("wf_lantern_brackets", "wf_railings"),
    ("wf_lantern_brackets", "wf_stairmouth"), ("wf_lantern_brackets", "wf_planking"),
    ("wf_moorings", "wf_skiff"), ("wf_moorings", "wf_planking"),
    ("wf_clutter", "wf_planking"), ("wf_stairmouth", "wf_planking"),
    ("wf_stairmouth", "wf_joists"), ("wf_stairmouth", "wf_railings"),
    # --- the Weave: the same deck assembly again, one tier UP ---------------
    # (finding 79: a district that does not register its assemblies reports its
    #  own joists-into-piles as interpenetration offenders)
    ("wv_planking", "wv_joists"), ("wv_planking", "wv_piles"),
    ("wv_joists", "wv_piles"), ("wv_railings", "wv_planking"),
    ("wv_railings", "wv_joists"), ("wv_railings", "wv_piles"),
    ("wv_pile_bracing", "wv_piles"), ("wv_pile_bracing", "wv_joists"),
    ("wv_pile_bracing", "wv_planking"), ("wv_pile_bracing", "wv_hut_"),
    ("wv_stair_treads", "wv_planking"), ("wv_stair_treads", "wv_railings"),
    ("wv_stair_treads", "wv_joists"),
    # the piles are DRIVEN INTO the ground and stand in the water — that is what
    # a stilt district is, and both neighbours' ground meshes run under this tier
    ("wv_piles", "wf_ground"), ("wv_piles", "lf_ground"), ("wv_piles", "riverbed"),
    ("wv_piles", "water_pool"), ("wv_pile_bracing", "wf_ground"),
    ("wv_pile_bracing", "lf_ground"), ("wv_planking", "lf_ground"),
    ("wv_planking", "wf_ground"), ("wv_joists", "lf_ground"), ("wv_joists", "wf_ground"),
    # a hut is one object carrying its own posts, floor, walls, roof and veranda,
    # and it stands ON this district's decking and IN the rock
    ("wv_hut_", "wv_planking"), ("wv_hut_", "wv_joists"), ("wv_hut_", "wv_piles"),
    ("wv_hut_", "wv_railings"), ("wv_hut_", "wf_ground"), ("wv_hut_", "lf_ground"),
    ("wv_hut_", "riverbed"), ("wv_hut_", "water_pool"), ("wv_hut_", "wv_props"),
    ("wv_hut_", "wv_cloth_"), ("wv_hut_", "wv_clut_"), ("wv_hut_", "wv_stair_treads"),
    ("wv_hut_", "wv_pile_bracing"), ("wv_hut_", "wv_hut_"),
    # lines, cloth, lanterns and clutter hang off / stand on all of it
    ("wv_props", "wv_planking"), ("wv_props", "wv_joists"), ("wv_props", "wv_railings"),
    ("wv_props", "wv_cloth_"), ("wv_props", "wv_clut_"), ("wv_props", "wv_piles"),
    ("wv_cloth_", "wv_planking"), ("wv_cloth_", "wv_railings"),
    ("wv_cloth_", "wv_clut_"), ("wv_clut_", "wv_planking"), ("wv_clut_", "wv_railings"),
    ("wv_clut_", "wv_joists"), ("wv_cloth_", "wv_cloth_"),
    # the cottage is bedded in the Keepers' Spur buttress by design (its back is
    # cut into the rock — the same declaration lf_tenant_shack already has)
    ("wv_keeper_cottage", "lf_ground"), ("wv_keeper_cottage", "wv_planking"),
    ("wv_keeper_cottage", "wv_cottage_footings"), ("wv_keeper_cottage", "wv_props"),
    ("wv_keeper_cottage", "wv_railings"), ("wv_keeper_cottage", "wv_joists"),
    ("wv_cottage_footings", "lf_ground"),
    ("wv_fishdock_ladder", "wv_planking"), ("wv_fishdock_ladder", "wv_piles"),
    ("wv_fishdock_ladder", "wv_hut_"), ("wv_fishdock_ladder", "wv_railings"),
    # --- the North Landing pier -------------------------------------------
    ("nl_pier", "lf_riverbed_tail"), ("nl_pier", "lf_ground"),
    ("nl_pier", "water_pool"), ("nl_pier", "nl_dress_"), ("nl_pier", "nl_moor_"),
    ("nl_pier", "wv_railings"), ("nl_dress_", "nl_pier"), ("nl_dress_", "nl_dress_"),
    ("nl_moor_", "lf_riverbed_tail"), ("nl_moor_", "water_pool"),
]


# --- Gate Approach: the district's own assemblies (manifest 79) -------------
# A bracket is DRIVEN into whatever it hangs off, a gate leaf's hinges are inside
# its pier, a lantern sits inside its own cage bracket, and the corbels that
# carry the eastern gallery are let into it.
SAME_ASSEMBLY += [
    ("gate_lantern_", "gate_gatehouse"), ("gate_lantern_", "gate_arch"),
    ("gate_lantern_", "gate_barrier"), ("gate_lantern_", "gate_yard"),
    ("gate_lantern_", "gate_winch"), ("gate_lantern_", "gate_palisade"),
    ("gate_lantern_", "gate_lantern_brackets"),
    ("gate_lantern_brackets", "gate_gatehouse"), ("gate_lantern_brackets", "gate_arch"),
    ("gate_lantern_brackets", "gate_barrier"), ("gate_lantern_brackets", "gate_yard"),
    ("gate_lantern_brackets", "gate_winch"),
    ("gate_leaves", "gate_arch"), ("gate_leaves", "gate_palisade"),
    ("gate_palisade", "gate_arch"), ("gate_arch", "gate_parapet"),
    ("gate_corbels", "gate_parapet"), ("gate_corbels", "gate_yard"),
    ("gate_winch_rope", "gate_winch"), ("gate_winch_rope", "gate_parapet"),
    ("gate_clutter", "gate_yard"), ("gate_clutter", "gate_parapet"),
    ("gate_clutter", "gate_winch"), ("gate_clutter", "gate_palisade"),
    ("gate_bunting", "gate_arch"), ("gate_bunting", "gate_gatehouse"),
    ("gate_bunting", "gate_yard"), ("gate_bunting", "gate_palisade"),
    ("gate_barrier", "gate_parapet"), ("gate_barrier", "gate_gatehouse"),
]

# --- Shelf tier: the shop street's own assemblies (manifest 79) --------------
# Every building is ONE joined object carrying its plinth, walls, roof, gallery
# and sign, and it is bedded in the tier it stands on and in the veneer it backs
# onto.  The stair underworks are masonry BUILT UNDER canonical treads and let
# into the ground.  Signs, awnings, bunting and lanterns hang off the buildings.
_SH_B = ("shelf_inn", "shelf_item_shop", "shelf_weapon_shop", "shelf_armor_shop",
         "shelf_home_a", "shelf_home_b", "shelf_home_c", "shelf_stalls")
_SH_G = ("shelf_ground", "shelf_paving", "shelf_cliffface", "shelf_stair_underworks")
_SH_D = ("shelf_awning", "shelf_bunting", "shelf_bunting_lines", "shelf_lantern_",
         "shelf_lantern_brackets", "shelf_parapet", "shelf_clutter")
SAME_ASSEMBLY += [(a, b) for a in _SH_B for b in _SH_G]
SAME_ASSEMBLY += [(a, b) for a in _SH_B for b in _SH_B]
SAME_ASSEMBLY += [(a, b) for a in _SH_D for b in _SH_B]
SAME_ASSEMBLY += [(a, b) for a in _SH_D for b in _SH_G]
SAME_ASSEMBLY += [(a, b) for a in _SH_D for b in _SH_D]
SAME_ASSEMBLY += [(a, b) for a in _SH_G for b in _SH_G]
# the shelf's ground meets the gate's promontory and its veneer meets the gate's
# veneer at x=31.44 — two districts, one cliff, by design
SAME_ASSEMBLY += [("shelf_ground", "gate_ground"), ("shelf_cliffface", "gate_cliffface"),
                  ("shelf_cliffface", "gate_ground"), ("shelf_ground", "gate_corbels"),
                  ("shelf_stair_underworks", "gate_ground"),
                  ("shelf_ground", "cliff_town"), ("shelf_cliffface", "cliff_town")]


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    cfg = {"region": None, "json": None, "top": 40, "report_only": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--region":
            cfg["region"] = [float(v) for v in argv[i + 1].split(",")]; i += 2
        elif a == "--json":
            cfg["json"] = argv[i + 1]; i += 2
        elif a == "--top":
            cfg["top"] = int(argv[i + 1]); i += 2
        elif a == "--report-only":
            cfg["report_only"] = True; i += 1
        else:
            i += 1
    return cfg


def is_ground(n):
    return n.startswith(GROUND) or any(g in n for g in GROUND)


def same_assembly(a, b):
    for p, q in SAME_ASSEMBLY:
        if (a.startswith(p) and b.startswith(q)) or (a.startswith(q) and b.startswith(p)):
            return True
    return False


def _under_water(b):
    """True when the object's base sits below one of the town's water surfaces."""
    for z in (0.20, 3.60):
        if b[4] < z - 0.05:
            return True
    return False


def wbb(ob):
    vs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs),
            max(v.y for v in vs), min(v.z for v in vs), max(v.z for v in vs))


def bb_overlap(a, b, pad=0.0):
    for i in (0, 2, 4):
        if min(a[i + 1], b[i + 1]) - max(a[i], b[i]) < -pad:
            return False
    return True


def main():
    cfg = parse()
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    R = cfg["region"]

    obs = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.name.startswith(SKIP_PREFIX):
            continue
        if ob.hide_viewport or not len(ob.data.vertices):
            continue
        b = wbb(ob)
        cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
        if R and not (R[0] <= cx <= R[1] and R[2] <= cy <= R[3]):
            continue
        obs.append((ob, b))
    print("=" * 78)
    print("GEOMETRY AUDIT — %d meshes%s" % (len(obs), (" in region %s" % R) if R else ""))
    print("=" * 78)

    bvhs = {}

    def bvh(ob):
        if ob.name not in bvhs:
            bvhs[ob.name] = BVHTree.FromObject(ob, dg)
        return bvhs[ob.name]

    def inside_frac(small, big):
        """fraction of `small`'s verts inside `big`, and the deepest such vertex."""
        B = bvh(big)
        Mx = small.matrix_world
        vs = small.data.vertices
        step = max(1, len(vs) // MAX_SAMPLE)
        n = ins = 0
        deep = 0.0
        for i in range(0, len(vs), step):
            p = Mx @ vs[i].co
            n += 1
            # ray parity: count surface crossings straight up
            hits = 0
            o = p.copy()
            for _ in range(12):
                r = B.ray_cast(o, Vector((0, 0, 1)), 1e4)
                if r[0] is None:
                    break
                hits += 1
                o = r[0] + Vector((0, 0, 1e-4))
            if hits % 2 == 1:
                ins += 1
                nr = B.find_nearest(p)
                if nr[0] is not None:
                    deep = max(deep, (nr[0] - p).length)
        return (ins / max(n, 1)), deep

    # -------------------------------------------------------- 1. intersections
    pairs = []
    checked = 0
    for i in range(len(obs)):
        oa, ba = obs[i]
        for j in range(i + 1, len(obs)):
            ob_, bb_ = obs[j]
            if not bb_overlap(ba, bb_):
                continue
            na, nb = oa.name, ob_.name
            if is_ground(na) or is_ground(nb):
                continue
            if oa.parent is ob_ or ob_.parent is oa or same_assembly(na, nb):
                continue
            if soft(na) or soft(nb):
                continue
            if na.startswith(CHAIN) and nb.startswith(CHAIN):
                continue
            checked += 1
            try:
                ov = bvh(oa).overlap(bvh(ob_))
            except Exception:
                continue
            if not ov:
                continue
            small, big = (oa, ob_) if len(oa.data.vertices) <= len(ob_.data.vertices) else (ob_, oa)
            f, d = inside_frac(small, big)
            # non-manifold art (leaf cards, open shells) defeats the parity test,
            # so also measure how deeply the two solids' bounds interlock: the
            # SMALLEST of the three overlap extents is ~0 for a face-touch and
            # metres for a beam driven through a roof.
            pen = min(min(ba[k + 1], bb_[k + 1]) - max(ba[k], bb_[k]) for k in (0, 2, 4))
            # the bbox heuristic is only meaningful for compact objects: two joined
            # multi-part meshes that span the whole yard always "interlock" by bbox.
            diag = max(math.dist((ba[0], ba[2], ba[4]), (ba[1], ba[3], ba[5])),
                       math.dist((bb_[0], bb_[2], bb_[4]), (bb_[1], bb_[3], bb_[5])))
            if f > INSIDE_FRAC or d > DEPTH or (len(ov) >= 24 and pen > 0.22 and diag < COMPACT):
                pairs.append({"a": small.name, "b": big.name, "inside_frac": round(f, 3),
                              "depth": round(d, 3), "faces": len(ov), "pen": round(pen, 2),
                              "a_loc": [round(v, 2) for v in small.matrix_world.translation],
                              "b_loc": [round(v, 2) for v in big.matrix_world.translation]})
    pairs.sort(key=lambda p: -(p["inside_frac"] * 2 + p["depth"] + p["pen"] * 0.25))
    print("\n[1] INTERSECTIONS  (%d bbox-overlapping pairs tested, %d offenders)"
          % (checked, len(pairs)))
    print("    (inside_frac > %.3f or depth > %.2f m counts; a face-touch does not)"
          % (INSIDE_FRAC, DEPTH))
    for p in pairs[:cfg["top"]]:
        print("    %-28s IN %-28s frac=%.3f depth=%.2f pen=%.2f faces=%d at (%.1f,%.1f,%.1f)"
              % (p["a"], p["b"], p["inside_frac"], p["depth"], p["pen"], p["faces"], *p["a_loc"]))
    if len(pairs) > cfg["top"]:
        print("    ... %d more" % (len(pairs) - cfg["top"]))

    # ------------------------------------------------------------- 2. strays
    allb = [(o, b) for o, b in obs]
    strays = []
    for ob, b in obs:
        if is_ground(ob.name) or ob.parent is not None:
            continue
        # sample the footprint, not just the centroid: a joined multi-part mesh
        # can be perfectly supported at its centre and cantilevered into the air
        # at one end (that is exactly how composite leftovers read).
        fx = [0.5, 0.18, 0.82, 0.18, 0.82]
        fy = [0.5, 0.18, 0.18, 0.82, 0.82]
        # a thing is "held" if something is under it (support) OR beside/above it
        # within reach (a bracket, a cliff face, a mast) — creepers hang on rock,
        # lanterns hang off brackets, and neither is a stray.
        DIRS = [((0, 0, -1), SUPPORT_GAP), ((1, 0, 0), ATTACH), ((-1, 0, 0), ATTACH),
                ((0, 1, 0), ATTACH), ((0, -1, 0), ATTACH), ((0, 0, 1), ATTACH)]
        unsup, on = 0, {}
        for u, v in zip(fx, fy):
            cx = b[0] + (b[1] - b[0]) * u
            cy = b[2] + (b[3] - b[2]) * v
            held = None
            for dvec, dist in DIRS:
                o = Vector((cx, cy, b[4] - 0.02)) if dvec[2] < 0 else \
                    Vector((cx, cy, b[4] + min(0.25, (b[5] - b[4]) * 0.5)))
                for _ in range(4):
                    hit, loc, nor, idx, hob, mat = sc.ray_cast(dg, o, Vector(dvec), distance=dist)
                    if not hit:
                        break
                    if hob is not ob:
                        held = hob.name
                        break
                    o = loc + Vector(dvec) * 0.01
                if held:
                    break
            if held:
                on[held] = on.get(held, 0) + 1
            else:
                unsup += 1
        if unsup < len(fx):
            continue
        # rays can slip past a thin hanger or a rock face a hand's width away;
        # fall back on a true surface-distance test against everything nearby.
        touch = None
        for o2, b2 in allb:
            if o2 is ob or not bb_overlap(b, b2, pad=0.40):
                continue
            try:
                loc, nor, idx, dd = bvh(o2).find_nearest(
                    Vector(((b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2)), 0.60)
            except Exception:
                continue
            if loc is not None:
                touch = o2.name
                break
        if touch:
            continue
        if b[4] < WATER_Z and _under_water(b):
            continue
        # how far IS it above the next thing down?  (a 0.8 m gap is a placement
        # slip; a 6 m gap is an object that belongs somewhere else entirely)
        cx = (b[0] + b[1]) / 2
        cy = (b[2] + b[3]) / 2
        gap = None
        hit, loc, nor, idx, hob, mat = sc.ray_cast(dg, Vector((cx, cy, b[4] - 0.03)),
                                                   Vector((0, 0, -1)), distance=40)
        if hit and hob is not ob:
            gap = round(b[4] - loc.z, 2)
        strays.append({"name": ob.name, "bbox_min_z": round(b[4], 2), "unsupported": unsup,
                       "of": len(fx), "rests_on": sorted(on), "gap": gap,
                       "loc": [round(v, 2) for v in ob.matrix_world.translation]})
    print("\n[2] STRAYS  (nothing within %.2f m below, nothing within %.2f m beside)"
          % (SUPPORT_GAP, ATTACH))
    for s in strays[:cfg["top"]]:
        print("    %-30s at (%6.1f,%6.1f) bottom z=%6.2f  gap to ground below: %s"
              % (s["name"], s["loc"][0], s["loc"][1], s["bbox_min_z"],
                 ("%.2f m" % s["gap"]) if s["gap"] is not None else "nothing within 40 m"))
    if not strays:
        print("    -> everything is supported or attached.")

    out = {"intersections": pairs, "strays": strays, "n_meshes": len(obs)}
    if cfg["json"]:
        json.dump(out, open(cfg["json"], "w"), indent=1)
        print("\nwrote", cfg["json"])
    print("\n" + "=" * 78)
    bad = len(pairs) + len(strays)
    print("GEOMETRY AUDIT: %d intersection offenders, %d strays" % (len(pairs), len(strays)))
    print("=" * 78)
    if bad and not cfg["report_only"]:
        sys.exit(1)


main()
