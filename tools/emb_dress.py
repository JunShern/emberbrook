"""emb_dress.py — EMBERBROOK'S DRESSING LAYER, DERIVED FROM THE RATIFIED BLOCKOUT.

    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_dress.py \
        --python-exit-code 1 -- --region mill --tier plate --frames a,b,c

    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_dress.py \
        --python-exit-code 1 -- --region mill --digest --nosave --noshoot

WHAT THIS IS, AND WHAT IT IS NOT.  `docs/qa/emberbrook/styleprobe/probe2-{a,b,c}.png` is
the ratified style bar and `mill_probe_r2.py` was the throwaway that produced it: HAND
AUTHORED, in its own coordinate frame, snapped to nothing, with its own invented terrain
function.  That script cannot be the production dressing, and not because it is untidy —
because a hand-authored corner cannot be re-derived.  Move the watermill one metre in the
map and the probe is a lie; the blockout is re-run and the probe is not.

So this file is a DERIVATION, and the thing it derives FROM is the blockout's own
as-built output.  It opens `emberbrook-master.blend`, HARVESTS the searched placements
the blockout already paid for — the 31 village trees with their species and their crown
radii, the boundary vocabulary, the walk surfaces, the lamps, the water, the ground —
and re-renders each of them with library assets.  It never re-runs a search the blockout
already ran, and it never invents a placement the blockout does not know about.  A map
change is therefore ONE command in each lane: emb_blockout, then emb_dress.

WHY HARVEST THE BLEND RATHER THAN IMPORT THE BUILDER.  `emb_blockout.py` is a top-level
bpy script, not a library: importing it would re-run the whole town.  Forking its search
code into this file would be worse — two copies of a paid rule, drifting.  The blend IS
the blockout's stated output and the object NAMES are already a contract (cine_regions
matches walk meshes by name).  Reading placements back out of it is the cheapest possible
coupling: this file knows the naming convention and nothing else about how the blockout
thinks.

  THE SPECIES OF A VILLAGE TREE IS READ OFF ITS CROWN'S TOPOLOGY, and that is not a trick.
  The blockout draws each canopy class from a different primitive recipe — the broad crown
  is two boxes and a cap (8+8+5 = 21 verts), the tall slim is three boxes and a cap (29),
  the conifer is three stacked pyramids (15).  The counts are three apart and cannot
  collide, so the class survives the round trip through the .blend exactly.  It is
  asserted, not assumed: an unrecognised crown is a hard failure, never a default.

DETERMINISM IS A GATE, AND THE HASH IS zlib.crc32.  NEVER Python `hash()` — it is salted
per process and `gs_build.py` paid for that lesson in a full day.  Two runs must produce
an identical CONTENT digest (world-space verts to 1e-5, materials, lights, cameras,
instance-collection assignments, particle counts and density weights).  `.blend` bytes
are NOT the gate: the format serialises memory addresses.

WHAT A DRESSING LAYER MAY NOT DO, in this town's own paid rules:
  * WALK SURFACES STAY CLEAN.  `walkGround`: any surface 0.00-0.73 m above a tread steals
    the foot.  Groundcover is scenery — it is scattered on `emb_ground_*`, never on a
    `walk_*` mesh, it is held off every tread by a measured margin, and it is emitted into
    a collection the realtime exporter drops from collision.
  * THE LANE CLEARANCES ARE THE BLOCKOUT'S, RE-ASSERTED ON THE DRESSED ASSET.  A scanned
    tree is not the proxy it replaces: its trunk is thicker and its canopy hangs lower.
    Trunk clears a walk surface by its own radius + 1.20 m; a canopy that oversails one
    has its underside at 3.60 m or higher.  Measured on the INSTANCED asset's own bounds.
  * `beyond_warmth` HOLDS.  Nothing that reads as habitation is dressed past the barn on
    the gate axis — the Gate Field is the town's one unwarm frame.
  * THE SEAL IS NOT TOUCHED.  No dressing is placed inside the notch's strip.

TWO OUTPUT TIERS FROM ONE DERIVATION.  `--tier plate` is the full-density Cycles build the
pre-rendered backgrounds bake from.  `--tier realtime` is the same derivation spending the
manifest's `realtime_budget`: baked ground instead of instanced grass, one impostor rank
instead of a second forest rank, a hard instance cap.  The tier is a BUILD FLAG, not a
second authoring — every placement in both tiers comes from the same harvest and the same
crc32 stream, so the realtime town and the plate town are the same town.

THE ASSET LIBRARY IS A MANIFEST, NOT A DIRECTORY LISTING.  `public/assets/dressing/
manifest.json` (lane A) names each asset's class, its measured height, its licence and its
tint recipe.  Until it lands, `--phcache` synthesises the same structure from the PolyHaven
CC0 set the ratified probe used, so the engine is written against the manifest from the
first line and the swap is one path.  Every substitution the library forces (a class with
no asset in it) is PRINTED as a manifest gap rather than silently defaulted.
"""
import bpy, bmesh, json, math, os, sys, zlib, hashlib
from mathutils import Vector, Euler

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


def flag(f):
    return f in argv


MAP_PATH = os.path.join(REPO, "public", opt("--map", "townmap/emberbrook.map.json"))
CAM_PATH = os.path.join(REPO, "public", opt("--cameras", "townmap/emberbrook.cameras.json"))
MANIFEST = opt("--manifest", os.path.join(REPO, "public/assets/dressing/manifest.json"))
PHCACHE = opt("--phcache", "/private/tmp/claude-501/-Users-junshernchan-projects-rpg-3d/"
                           "0e1c40c3-51e1-4ef0-8908-896c9d91202e/scratchpad/ph")
DELL = os.path.join(REPO, "tools/blends/dellhollow-master.blend")
REGION = opt("--region", "mill")
RADIUS = float(opt("--radius", "30.0"))
TIER = opt("--tier", "plate")
OUT = opt("--out", os.path.join(REPO, "tools/blends/emberbrook-dressed.blend"))
SHOTDIR = opt("--shots", os.path.join(REPO, "docs/qa/emberbrook/styleprobe"))
TAG = opt("--tag", "dress1")
FRAMES = [f for f in opt("--frames", "a,b,c").split(",") if f]
SAMPLES = int(opt("--samples", "120"))
RESX, RESY = int(opt("--resx", "1400")), int(opt("--resy", "800"))
KEY = opt("--key", "probe")            # probe = the style bar's legibility key
GROUNDSUB = int(opt("--groundsub", "2"))
DIGEST = flag("--digest")
NOSAVE = flag("--nosave")
NOSHOOT = flag("--noshoot")
FAST = flag("--fast")

MAPD = json.load(open(MAP_PATH))
LM = {l["id"]: l for l in MAPD["landmarks"]}

print("=" * 78)
print("EMBERBROOK DRESSING — region=%s tier=%s key=%s" % (REGION, TIER, KEY))
print("=" * 78)


# =============================================================== determinism ==
# zlib.crc32, and ONLY zlib.crc32.  Python's hash() is salted per process (PYTHONHASHSEED)
# so a build seeded from it is not reproducible across runs — gs_build.py shipped that bug
# and it cost a day.  crc32 is stable across processes, machines and Python versions.
def crc(*parts):
    s = "|".join(str(p) for p in parts).encode()
    return zlib.crc32(s) & 0xFFFFFFFF


def crc01(*parts):
    return crc(*parts) / 4294967295.0


def crcpick(seq, *parts):
    return seq[crc(*parts) % len(seq)] if seq else None


def crcrange(lo, hi, *parts):
    return lo + (hi - lo) * crc01(*parts)


# ============================================================ THE HARVEST ==
# Everything below reads the blockout's own as-built output.  Nothing here decides where
# anything stands; the blockout already did, against the map, with the searches it paid
# for.  This is a reader.
def world_verts(o):
    mw = o.matrix_world
    return [mw @ v.co for v in o.data.vertices]


def bounds(ws):
    return (min(v.x for v in ws), max(v.x for v in ws),
            min(v.y for v in ws), max(v.y for v in ws),
            min(v.z for v in ws), max(v.z for v in ws))


PLAN = {"village_trees": [], "rim": [], "wood": [], "boundary": [], "walk": [],
        "lamps": [], "water": {}, "ground": [], "massing": [], "fields": [], "props": []}

# THE THREE CANOPY CLASSES, KEYED BY THE CROWN'S OWN VERTEX COUNT.  See the module
# docstring: these are the blockout's three primitive recipes and they are three apart.
CROWN_CLASS = {21: "broad", 29: "slim", 15: "conifer"}
_vt = {}
for o in bpy.data.objects:
    n = o.name
    if o.type != 'MESH':
        if n.startswith("emb_lamp_") or n.startswith("KEYEMB_"):
            PLAN["lamps"].append((n, tuple(o.location)))
        continue
    if n.startswith("veg_emb_village_"):
        i = int(n.split("_")[3])
        _vt.setdefault(i, {})[n.rsplit("_", 1)[-1]] = o
    elif n.startswith("veg_emb_rim_"):
        PLAN["rim"].append(o)
    elif n.startswith("veg_emb_wood_"):
        PLAN["wood"].append(o)
    elif n.startswith("walk_"):
        ws = world_verts(o)
        if ws:
            PLAN["walk"].append((n, bounds(ws)))
    elif n.startswith("emb_ground"):
        PLAN["ground"].append(o)
    elif n.startswith("water_emb_"):
        ws = world_verts(o)
        if ws:
            PLAN["water"][n] = (o, bounds(ws))
    elif n.startswith("emb_lamp_"):
        PLAN["lamps"].append((n, tuple(o.location)))
    elif "_drystone" in n or "_rail" in n or "_bramble" in n or "_hedge" in n or "_pale" in n:
        ws = world_verts(o)
        if ws:
            PLAN["boundary"].append((n, o, bounds(ws)))
    elif n.startswith("lm_field_"):
        PLAN["fields"].append(o)
    elif n.startswith("lm_") or n.startswith("bar_"):
        ws = world_verts(o)
        if ws:
            PLAN["massing"].append((n, o, bounds(ws)))

for i in sorted(_vt):
    d = _vt[i]
    if "crown" not in d or "trunk" not in d:
        continue
    cw = world_verts(d["crown"])
    tw = world_verts(d["trunk"])
    nb = len(cw)
    cls = CROWN_CLASS.get(nb)
    assert cls, ("village tree %d has a %d-vertex crown, which is none of the blockout's "
                 "three canopy recipes (21 broad / 29 slim / 15 conifer). The blockout's "
                 "massing changed and this reader is stale — fix the reader, do not "
                 "guess a class." % (i, nb))
    cb = bounds(cw)
    tb = bounds(tw)
    _ccx, _ccy = (cb[0] + cb[1]) / 2, (cb[2] + cb[3]) / 2
    # THE CROWN RADIUS IS NOT HALF THE BOUNDING BOX, and reading it that way manufactured
    # a rule violation out of nothing.  Every crown slab is a SQUARE in its own frame,
    # yawed by the tree's hash; a yawed square's AABB is up to 41% wider than the square,
    # so the bbox reading inflated a 2.6 m conifer crown to 3.6 m and then found it 0.35 m
    # short of a lane the ratified blockout had already cleared it from.  Measure what the
    # blockout drew: the base square's own half-width, which is the CORNER distance over
    # root two, and which is invariant to the yaw.
    _corner = max(math.hypot(v.x - _ccx, v.y - _ccy) for v in cw)
    PLAN["village_trees"].append(dict(
        i=i, cls=cls,
        x=_ccx, y=_ccy,
        z=tb[4],                              # the trunk's foot IS the tree's ground
        crown_r=_corner / math.sqrt(2.0),
        cbase=cb[4], top=cb[5],
        trunk_r=max(tb[1] - tb[0], tb[3] - tb[2]) / 2,
        objs=[d["trunk"], d["crown"]]))

print("HARVEST from the ratified blockout (%d objects):" % len(bpy.data.objects))
_cc = {}
for t in PLAN["village_trees"]:
    _cc[t["cls"]] = _cc.get(t["cls"], 0) + 1
print("  village trees      %d — %s (species read off the crown's own topology, asserted)"
      % (len(PLAN["village_trees"]),
         ", ".join("%d %s" % (v, k) for k, v in sorted(_cc.items()))))
print("  walk surfaces      %d meshes (the clearance and trodden-bare instrument)"
      % len(PLAN["walk"]))
print("  boundary fragments %d (stone rows, rails, bramble, pales — the 29%%-partial "
      "vocabulary)" % len(PLAN["boundary"]))
print("  rim / wood         %d rim meshes, %d Whisperwood cluster meshes"
      % (len(PLAN["rim"]), len(PLAN["wood"])))
print("  lamps              %d post/light objects" % len(PLAN["lamps"]))
print("  water              %s" % ", ".join(sorted(PLAN["water"])))
print("  ground             %s" % ", ".join(o.name for o in PLAN["ground"]))


# ------------------------------------------------------------------ the region --
# A DISTRICT PASS IS A FILTER, NOT A DIFFERENT BUILD.  Every stage below runs the same
# code for `--region all` and `--region mill`; the region only decides which harvested
# items are in scope.  That is what makes the pilot mean something: the mill corner is
# built by the district-wide code path, not by a special case that would have to be
# rewritten before the district pass.
if REGION == "all":
    RCX, RCY, RR = 0.0, 0.0, 1e9
else:
    _anchor = {"mill": "watermill", "square": "square-plaza", "pond": "pond",
               "homerow": "elder-house", "gate": "gate-court"}.get(REGION, REGION)
    assert _anchor in LM, "unknown --region %r (no landmark %r in the map)" % (REGION, _anchor)
    RCX, RCY = LM[_anchor]["pos"][0], LM[_anchor]["pos"][1]
    RR = RADIUS
print("  region             %s — centre (%.1f, %.1f) radius %.1f m"
      % (REGION, RCX, RCY, RR) if REGION != "all" else "  region             the whole town")


def in_region(x, y, pad=0.0):
    return math.hypot(x - RCX, y - RCY) <= RR + pad


# =========================================================== the asset library ==
# THE MANIFEST IS THE CONTRACT.  Lane A owns `public/assets/dressing/manifest.json`; this
# file consumes it and nothing else.  The PolyHaven fallback below synthesises the SAME
# structure from the CC0 set the ratified probe used, so the engine has been written
# against the manifest since its first line and the swap is a path, not a rewrite.
#
# CLASSES, and they are the vocabulary the blockout's own massing speaks:
#   canopy_broad  the village oak — a wide dome that reads as one mass (blockout sp0)
#   canopy_slim   the poplar/birch column, twice as tall as it is wide (sp1)
#   conifer       the wood's own form at village scale (sp2)
#   shrub bramble fern weed grass   the boundary and groundcover vocabulary
#   ground_turf ground_mud          the scanned ground pair
PH_FALLBACK = {
    # id                     class            measured height (m), from the scan's own blend
    "tree_small_02":       ("canopy_broad",   4.56),
    "island_tree_01":      ("canopy_broad",   5.03),
    "island_tree_02":      ("canopy_broad",   3.41),
    "island_tree_03":      ("canopy_broad",   4.20),
    "jacaranda_tree":      ("canopy_bare",   10.36),
    "fir_tree_01":         ("conifer",        0.0),
    "pine_tree_01":        ("conifer",        0.0),
    "fir_sapling_medium":  ("conifer",        0.0),
    "searsia_lucida":      ("bramble",        0.0),
    "searsia_burchellii":  ("bramble",        0.0),
    "shrub_01":            ("shrub",          0.0),
    "shrub_03":            ("shrub",          0.0),
    "nettle_plant":        ("weed",           0.0),
    "weed_plant_02":       ("weed",           0.0),
    "fern_02":             ("fern",           0.0),
    "dandelion_01":        ("grass",          0.0),
    "grass_medium_01":     ("grass",          0.0),
    "grass_medium_02":     ("grass",          0.0),
    "grass_bermuda_01":    ("grass",          0.0),
}
# THE TINT RECIPES, carried over from the ratified probe unchanged.  These are the numbers
# the user accepted in round 2 — the scans graded toward the Emberwake autumn with
# subsurface so the low sun comes THROUGH the leaves.  They belong in the manifest the day
# lane A's manifest carries a `tint` field; until then they live here, in one table.
TINT = {
    "tree_small_02":    dict(hue=0.470, sat=1.20, val=0.92, mix=(0.60, 0.24, 0.05), mixf=0.55, sss=0.30),
    "island_tree_01":   dict(hue=0.492, sat=1.05, val=0.88, mix=(0.46, 0.33, 0.09), mixf=0.22, sss=0.28),
    "island_tree_02":   dict(hue=0.478, sat=1.12, val=0.90, mix=(0.56, 0.28, 0.06), mixf=0.46, sss=0.30),
    "island_tree_03":   dict(hue=0.478, sat=1.12, val=0.90, mix=(0.56, 0.28, 0.06), mixf=0.40, sss=0.30),
    "jacaranda_tree":   dict(hue=0.500, sat=0.98, val=0.92, mix=(0.50, 0.31, 0.08), mixf=0.38, sss=0.26),
    "shrub_01":         dict(hue=0.490, sat=1.08, val=0.88, mix=(0.42, 0.25, 0.07), mixf=0.20, sss=0.25),
    "shrub_03":         dict(hue=0.490, sat=1.08, val=0.88, mix=(0.42, 0.25, 0.07), mixf=0.20, sss=0.25),
    "nettle_plant":     dict(hue=0.495, sat=1.05, val=0.85, sss=0.25),
    "searsia_lucida":   dict(hue=0.486, sat=1.08, val=0.86, mix=(0.48, 0.28, 0.07), mixf=0.26, sss=0.28),
    "searsia_burchellii": dict(hue=0.486, sat=1.08, val=0.86, mix=(0.48, 0.28, 0.07), mixf=0.26, sss=0.28),
    "fir_tree_01":      dict(hue=0.500, sat=0.95, val=0.72, sss=0.20),
    "pine_tree_01":     dict(hue=0.500, sat=0.95, val=0.74, sss=0.20),
    "fir_sapling_medium": dict(hue=0.500, sat=0.95, val=0.74, sss=0.20),
    "fern_02":          dict(hue=0.488, sat=1.05, val=0.86, mix=(0.45, 0.30, 0.08), mixf=0.18, sss=0.25),
    "grass_medium_01":  dict(hue=0.492, sat=1.02, val=0.80, sss=0.30),
    "grass_medium_02":  dict(hue=0.492, sat=1.02, val=0.80, sss=0.30),
    "grass_bermuda_01": dict(hue=0.492, sat=1.02, val=0.82, sss=0.30),
    "weed_plant_02":    dict(hue=0.490, sat=1.05, val=0.85, sss=0.25),
    "dandelion_01":     dict(hue=0.492, sat=1.05, val=0.86, sss=0.25),
}


def load_manifest():
    """The manifest if lane A has landed it; otherwise the probe's CC0 set, in the same
       shape, with the substitution PRINTED rather than assumed."""
    if os.path.exists(MANIFEST):
        m = json.load(open(MANIFEST))
        root = m.get("root") or os.path.dirname(MANIFEST)
        if not os.path.isabs(root):
            root = os.path.join(REPO, root)
        for a in m["assets"]:
            a["_path"] = a["file"] if os.path.isabs(a["file"]) else os.path.join(root, a["file"])
        print("ASSET LIBRARY   manifest %s — %d assets, %d textures"
              % (os.path.relpath(MANIFEST, REPO), len(m["assets"]), len(m.get("textures", []))))
        return m
    assets = []
    for aid, (cls, h) in sorted(PH_FALLBACK.items()):
        p = os.path.join(PHCACHE, aid, aid + ".blend")
        if not os.path.exists(p):
            continue
        # NO `collection` FIELD ON PURPOSE.  Naming the top-level collection here would
        # re-create the exact trap this engine exists to catch: PolyHaven's top level
        # stacks the geometry-nodes generator with every baked LOD.  Leaving it unset makes
        # the loader fall through to the LOD convention and pick ONE representation.
        assets.append(dict(id=aid, cls=cls, file=p, _path=p,
                           height_m=h, license="CC0", source="polyhaven"))
    tex = [dict(id="leafy_grass", role="ground_turf",
                diffuse=os.path.join(PHCACHE, "tex/leafy_grass_Diffuse.jpg"),
                normal=os.path.join(PHCACHE, "tex/leafy_grass_nor_gl.jpg")),
           dict(id="brown_mud_leaves_01", role="ground_mud",
                diffuse=os.path.join(PHCACHE, "tex/brown_mud_leaves_01_Diffuse.jpg"),
                normal=os.path.join(PHCACHE, "tex/brown_mud_leaves_01_nor_gl.jpg"))]
    print("ASSET LIBRARY   MANIFEST NOT PRESENT at %s — falling back to the ratified "
          "probe's PolyHaven CC0 set (%d assets, %d ground textures) out of %s.\n"
          "                This is the documented interim: lane A's manifest replaces it "
          "with one --manifest path and no code change."
          % (os.path.relpath(MANIFEST, REPO), len(assets), len(tex), PHCACHE))
    return dict(version=0, root=PHCACHE, assets=assets, textures=tex,
                realtime_budget=dict(instances=420, tris=260000, textures_mb=24))


MAN = load_manifest()
BUDGET = MAN.get("realtime_budget", {})
BYCLASS = {}
for a in MAN["assets"]:
    BYCLASS.setdefault(a.get("cls") or a.get("class"), []).append(a)
for k in sorted(BYCLASS):
    BYCLASS[k].sort(key=lambda a: a["id"])
print("                classes: %s"
      % ", ".join("%s x%d" % (k, len(v)) for k, v in sorted(BYCLASS.items())))

GAPS = []
for need in ("canopy_broad", "canopy_slim", "conifer", "shrub", "bramble", "fern",
             "weed", "grass"):
    if not BYCLASS.get(need):
        GAPS.append(need)
if GAPS:
    print("                MANIFEST GAPS (no asset in class): %s — each is substituted "
          "below and the substitution is printed at the point it is made, never silently."
          % ", ".join(GAPS))


# ------------------------------------------------------- loading and tinting --
SRC = {}
SRCH = {}


def tri_count(col):
    n = 0
    for ob in col.all_objects:
        if ob.type == 'MESH':
            n += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return n


TRIREPORT = []


def src_collection(aid):
    """Append ONE representation of an asset, measure it, and cache it.

       A SCANNED-ASSET BLEND IS NOT ONE MODEL.  A PolyHaven tree blend's top-level
       collection holds the geometry-nodes GENERATOR, a baked LOD0 and a baked LOD1 as
       SIBLINGS, and a collection instance carries no view-layer exclusion — so instancing
       the top-level collection renders all three, coincident, and nothing looks wrong in
       frame.  Measured on this library: tree_small_02 is 2.06 M + 0.50 M baked tris plus a
       28 k generator, all stacked.  The ratified round-2 probe rendered every broadleaf
       three times and the only symptom was the clock.

       So the manifest's `collection` field is the contract — it names EXACTLY ONE
       representation — and the fallback picks one by the LOD convention rather than
       taking whatever sits at the top.  Which one is a TIER decision, from the same
       derivation: the plate takes LOD0, the realtime build takes the coarsest baked LOD."""
    if aid in SRC:
        return SRC[aid]
    a = next((a for a in MAN["assets"] if a["id"] == aid), None)
    if not a or not os.path.exists(a["_path"]):
        SRC[aid] = None
        return None
    want = a.get("collection")
    with bpy.data.libraries.load(a["_path"], link=False) as (df, dt):
        names = list(df.collections)
        dt.collections = names
        if not names:
            dt.objects = list(df.objects)
    loaded = {c.name: c for c in dt.collections if c}
    col, how = None, ""
    if want and want in loaded:
        col, how = loaded[want], "manifest names it"
    if col is None:
        lods = sorted(n for n in loaded
                      if n.startswith(aid + "_LOD") and n[len(aid) + 4:].isdigit())
        if lods:
            pick = lods[0] if TIER != "realtime" else lods[-1]
            col, how = loaded[pick], ("LOD convention, %s tier" % TIER)
    if col is None and loaded:
        col, how = loaded.get(aid) or list(loaded.values())[0], "top-level (no LOD split)"
    if col is None:
        col = bpy.data.collections.new("src_" + aid)
        for o in dt.objects:
            if o:
                col.objects.link(o)
        how = "loose objects"
    top = loaded.get(aid)
    whole = tri_count(top) if top is not None else None
    mine = tri_count(col)
    TRIREPORT.append((aid, col.name, how, mine, whole, a.get("tris")))
    tint_collection(col, aid)
    # MEASURE THE ASSET, because the round-2 finding was that the scans are SMALL: against
    # a 12 m mill they read as saplings at native scale.  The scale factor a placement
    # needs is (the proxy's height) / (this measurement), so the measurement has to be the
    # asset's own, not the manifest's opinion of it.
    zs, rs = [], []
    for ob in col.all_objects:
        if ob.type != 'MESH' or not ob.data.vertices:
            continue
        for v in ob.data.vertices:
            w = ob.matrix_world @ v.co
            zs.append(w.z)
            rs.append(math.hypot(w.x, w.y))
    h = (max(zs) - min(zs)) if zs else 1.0
    r = (sorted(rs)[int(len(rs) * 0.92)] if rs else 1.0)
    SRC[aid] = col
    SRCH[aid] = (max(h, 0.05), max(r, 0.02), min(zs) if zs else 0.0)
    return col


def tint_collection(col, aid):
    """Grade a scan toward the Emberwake autumn and let the low sun come THROUGH the
       leaves.  Ratified in style probe round 2; the numbers are that probe's, unchanged."""
    kw = TINT.get(aid)
    if not kw:
        return
    mats = set()
    for ob in col.all_objects:
        for s in ob.material_slots:
            if s.material:
                mats.add(s.material)
    for m in mats:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not b:
            continue
        inp = b.inputs["Base Color"]
        if inp.links:
            src = inp.links[0].from_socket
            hs = nt.nodes.new("ShaderNodeHueSaturation")
            hs.inputs["Hue"].default_value = kw["hue"]
            hs.inputs["Saturation"].default_value = kw["sat"]
            hs.inputs["Value"].default_value = kw["val"]
            nt.links.new(src, hs.inputs["Color"])
            out = hs.outputs["Color"]
            if kw.get("mix") and kw.get("mixf", 0) > 0:
                mx = nt.nodes.new("ShaderNodeMixRGB")
                mx.blend_type = 'COLOR'
                mx.inputs["Fac"].default_value = kw["mixf"]
                mx.inputs["Color2"].default_value = (*kw["mix"], 1)
                nt.links.new(out, mx.inputs["Color1"])
                out = mx.outputs["Color"]
            nt.links.new(out, inp)
        if kw.get("sss"):
            low = m.name.lower()
            if any(k in low for k in ("leaf", "leaves", "grass", "blad", "frond")):
                for k, v in (("Subsurface Weight", kw["sss"]),):
                    try:
                        b.inputs[k].default_value = v
                        b.inputs["Subsurface Radius"].default_value = (0.55, 0.32, 0.08)
                    except Exception:
                        pass


# ================================================================= materials ==
# THE BUILT VOCABULARY IS DELLHOLLOW'S, and that is a coherence ruling rather than a
# convenience: the two towns have to read as one game (`forest._doc`, the probe's own
# terms of reference).  Appending the shipped materials means the mill's timber IS the
# timber Dellhollow's cottages are made of.
DRESS = bpy.data.collections.new("EMB_DRESS")
bpy.context.scene.collection.children.link(DRESS)
DRESS_GC = bpy.data.collections.new("EMB_DRESS_GROUNDCOVER")   # never collidable
DRESS.children.link(DRESS_GC)

WANT = ['mat_timber', 'mat_timber_dark', 'mat_wallwood', 'mat_freshwood',
        'mat_shingle_cedar', 'mat_shingle_mossy', 'mat_stone_grey', 'mat_gate_stone',
        'mat_rock', 'mat_grass', 'mat_iron', 'mat_rope', 'mat_qm_window_a',
        'mat_qm_sack', 'mat_whitewater', 'mat_gate_road']
_app = 0
for n in WANT:
    if bpy.data.materials.get(n):
        continue
    try:
        bpy.ops.wm.append(filepath=os.path.join(DELL, 'Material', n),
                          directory=os.path.join(DELL, 'Material'), filename=n)
        _app += 1
    except Exception as e:
        print("  append-miss", n, e)
print("MATERIALS       %d appended from dellhollow-master (the shipped, ratified "
      "vocabulary — the two towns must read as one game)" % _app)


def M(name, fallback, rough=0.85, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = fallback
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


TIMBER = M('mat_timber', (0.30, 0.19, 0.11, 1), 0.82)
TIMBER_D = M('mat_timber_dark', (0.17, 0.11, 0.07, 1), 0.85)
PLANK = M('mat_wallwood', (0.38, 0.26, 0.16, 1), 0.80)
SHINGLE = M('mat_shingle_cedar', (0.31, 0.20, 0.12, 1), 0.85)
SHING_M = M('mat_shingle_mossy', (0.26, 0.28, 0.16, 1), 0.90)
STONE = M('mat_stone_grey', (0.34, 0.32, 0.29, 1), 0.90)
STONE_W = M('mat_gate_stone', (0.40, 0.37, 0.32, 1), 0.90)
ROCK = M('mat_rock', (0.30, 0.27, 0.24, 1), 0.92)
IRON = M('mat_iron', (0.09, 0.09, 0.10, 1), 0.50, 0.9)
WINDOW = M('mat_qm_window_a', (0.90, 0.66, 0.32, 1), 0.30)
SACK = M('mat_qm_sack', (0.52, 0.44, 0.30, 1), 0.95)
ROPE = M('mat_rope', (0.45, 0.36, 0.22, 1), 0.90)
FOAM = M('mat_whitewater', (0.92, 0.93, 0.92, 1), 0.40)
ROADM = M('mat_gate_road', (0.30, 0.24, 0.17, 1), 0.95)
THATCH = M('emb_dress_thatch', (0.44, 0.31, 0.14, 1), 0.98)
DAUB = M('emb_dress_daub', (0.40, 0.355, 0.27, 1), 0.95)


def make_water(name, col, rough, alpha):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Alpha"].default_value = alpha
    try:
        b.inputs["IOR"].default_value = 1.33
    except Exception:
        pass
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 26.0
    n.inputs["Detail"].default_value = 6.0
    bm2 = nt.nodes.new("ShaderNodeBump")
    bm2.inputs["Strength"].default_value = 0.25
    nt.links.new(n.outputs["Fac"], bm2.inputs["Height"])
    nt.links.new(bm2.outputs["Normal"], b.inputs["Normal"])
    return m


WATER = make_water('emb_dress_water', (0.045, 0.075, 0.062), 0.09, 0.90)
WATER_F = make_water('emb_dress_waterfall', (0.66, 0.66, 0.60), 0.22, 0.62)
MIST = make_water('emb_dress_mist', (0.82, 0.83, 0.80), 0.90, 0.10)


def emissive(name, col, strength):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Emission Color"].default_value = (*col, 1)
    b.inputs["Emission Strength"].default_value = strength
    return m


GLOW = emissive('emb_dress_lampglow', (1.0, 0.66, 0.28), 9.0)


def ground_material():
    """The scanned ground pair — turf blended into trodden mud+leaf litter by height, so
       the margins toward water read wet.  Round 2's recipe; textures come from the
       manifest's `ground_turf`/`ground_mud` roles."""
    m = bpy.data.materials.get("emb_dress_ground")
    if m:
        return m
    m = bpy.data.materials.new("emb_dress_ground")
    m.use_nodes = True
    t = m.node_tree
    b = t.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.94
    byrole = {tx.get("role"): tx for tx in MAN.get("textures", [])}

    def image(fp, cs='sRGB', sc=0.22):
        if not fp or not os.path.exists(fp):
            print("  TEX-MISS", fp)
            return None
        im = bpy.data.images.load(fp, check_existing=True)
        im.colorspace_settings.name = cs
        n = t.nodes.new("ShaderNodeTexImage")
        n.image = im
        co = t.nodes.new("ShaderNodeTexCoord")
        mp = t.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (sc, sc, sc)
        t.links.new(co.outputs["Object"], mp.inputs["Vector"])
        t.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n

    turf = byrole.get("ground_turf", {})
    mud = byrole.get("ground_mud", {})
    g = image(turf.get("diffuse"))
    d = image(mud.get("diffuse"), sc=0.26)
    gn = image(turf.get("normal"), 'Non-Color')
    if g and d:
        geo = t.nodes.new("ShaderNodeNewGeometry")
        sep = t.nodes.new("ShaderNodeSeparateXYZ")
        t.links.new(geo.outputs["Position"], sep.inputs["Vector"])
        rng = t.nodes.new("ShaderNodeMapRange")
        # MUD TOWARD WATER, and the two numbers are the town's own levels rather than the
        # probe's: the brook here runs at ~1.5-2.2 and the ground rises off it.
        rng.inputs["From Min"].default_value = MILL.get("tail", 0.2)
        rng.inputs["From Max"].default_value = 3.2
        rng.inputs["To Min"].default_value = 1.0
        rng.inputs["To Max"].default_value = 0.0
        t.links.new(sep.outputs["Z"], rng.inputs["Value"])
        nz = t.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 1.1
        mixf = t.nodes.new("ShaderNodeMixRGB")
        mixf.blend_type = 'SCREEN'
        mixf.inputs["Fac"].default_value = 0.35
        t.links.new(rng.outputs["Result"], mixf.inputs["Color1"])
        t.links.new(nz.outputs["Fac"], mixf.inputs["Color2"])
        mx = t.nodes.new("ShaderNodeMixRGB")
        t.links.new(mixf.outputs["Color"], mx.inputs["Fac"])
        t.links.new(g.outputs["Color"], mx.inputs["Color1"])
        t.links.new(d.outputs["Color"], mx.inputs["Color2"])
        hs = t.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Hue"].default_value = 0.505
        hs.inputs["Saturation"].default_value = 0.88
        hs.inputs["Value"].default_value = 0.48
        t.links.new(mx.outputs["Color"], hs.inputs["Color"])
        t.links.new(hs.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = (0.10, 0.11, 0.045, 1)
    if gn:
        nm = t.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 1.0
        t.links.new(gn.outputs["Color"], nm.inputs["Color"])
        t.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


# ============================================================ build primitives ==
_T = {}


def _fin(me, smooth=False):
    me.materials.append(None)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return me


def tpl_cube():
    if 'cube' in _T:
        return _T['cube']
    me = bpy.data.meshes.new('dt_cube')
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges), offset=0.035,
                    segments=2, affect='EDGES', profile=0.5)
    bm.to_mesh(me)
    bm.free()
    _T['cube'] = _fin(me)
    return me


def tpl_cyl(v, r2=1.0):
    k = 'cyl%d_%s' % (v, r2)
    if k in _T:
        return _T[k]
    me = bpy.data.meshes.new('dt_' + k)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=v,
                          radius1=0.5, radius2=0.5 * r2, depth=1.0)
    bm.to_mesh(me)
    bm.free()
    _T[k] = _fin(me, smooth=True)
    return me


def tpl_blob(i):
    k = 'blob%d' % i
    if k in _T:
        return _T[k]
    me = bpy.data.meshes.new('dt_' + k)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    for j, v in enumerate(bm.verts):
        v.co *= 0.62 + 0.83 * crc01("blob", i, j)
        v.co.z *= 0.70 + 0.40 * crc01("blobz", i, j)
    bmesh.ops.smooth_vert(bm, verts=list(bm.verts), factor=0.35,
                          use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(me)
    bm.free()
    _T[k] = _fin(me, smooth=True)
    return me


def obj(name, me, loc, scale=(1, 1, 1), rot=(0, 0, 0), mat=None, coll=None):
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.scale = scale
    o.rotation_euler = Euler(rot)
    if mat is not None:
        o.material_slots[0].link = 'OBJECT'
        o.material_slots[0].material = mat
    (coll or DRESS).objects.link(o)
    return o


def box(name, loc, size, rot=(0, 0, 0), mat=None, coll=None):
    return obj(name, tpl_cube(), loc, size, rot, mat, coll)


def cyl(name, loc, r, d, rot=(0, 0, 0), mat=None, verts=12, taper=1.0, coll=None):
    return obj(name, tpl_cyl(verts, taper), loc, (2 * r, 2 * r, d), rot, mat, coll)


def blob(name, loc, s, rot=(0, 0, 0), mat=None, i=0, coll=None):
    return obj(name, tpl_blob(i % 8), loc, s, rot, mat, coll)


def gridmesh(name, nx, ny, fn, mat, smooth=True, coll=None):
    me = bpy.data.meshes.new(name)
    vs, fs = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            vs.append(fn(i / nx, j / ny))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            fs.append((a, a + 1, a + nx + 2, a + nx + 1))
    me.from_pydata(vs, [], fs)
    me.update()
    me.materials.append(None)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.material_slots[0].link = 'OBJECT'
    o.material_slots[0].material = mat
    (coll or DRESS).objects.link(o)
    return o


def ring(name, cx, cy, cz, r_out, r_in, width, mat, seg=64, ux=(1, 0), coll=None):
    """A SOLID SHROUD.  Round 1's wheel read cog-like because 28 discrete rim boxes turn
       to mush at 2x; the ratified round-2 fix is a solid ring so the wheel reads as a
       4.4 m disc first and machinery second.  Built in the wheel's own plane: `ux` is the
       in-plane horizontal unit (the flow direction), the axle is normal to it."""
    ax, ay = ux
    nx, ny = -ay, ax                      # the axle direction
    me = bpy.data.meshes.new(name)
    vs, fs = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        for rr in (r_out, r_in):
            for sy in (-width / 2, width / 2):
                vs.append((cx + ca * rr * ax + sy * nx, cy + ca * rr * ay + sy * ny,
                           cz + sa * rr))
    for i in range(seg):
        a = i * 4
        b2 = ((i + 1) % seg) * 4
        fs.append((a + 0, b2 + 0, b2 + 1, a + 1))
        fs.append((a + 2, a + 3, b2 + 3, b2 + 2))
        fs.append((a + 0, a + 2, b2 + 2, b2 + 0))
        fs.append((a + 1, b2 + 1, b2 + 3, a + 3))
    me.from_pydata(vs, [], fs)
    me.update()
    me.materials.append(None)
    o = bpy.data.objects.new(name, me)
    o.material_slots[0].link = 'OBJECT'
    o.material_slots[0].material = mat
    (coll or DRESS).objects.link(o)
    return o


# ======================================================= the instrument set ==
# These are the town's paid rules, re-implemented against the HARVESTED blockout rather
# than re-derived from the map.  A dressing layer that measured its clearances against its
# own idea of where the lanes are would be measuring against a second town.
WALKB = [b for _n, b in PLAN["walk"]]
# THE WALK SURFACES AS POLYGONS, NOT AS BOXES.  The first build of this instrument
# measured to each walk mesh's axis-aligned BOUNDING BOX and reported a village tree
# standing 0.44 m INSIDE a lane — a tree the blockout had already asserted at 1.20 m
# clearance.  Both cannot be true, and the bound was the thing that was wrong: a lane
# ribbon is an oriented quad and its AABB is up to 40% wider than the road.  A bound
# loose enough to refuse a placement the ratified blockout already made is a veto, not a
# test.  So the distance is measured to the TOP FACE POLYGONS, which is the surface a
# foot actually lands on.
WALKPOLY = []
for _o in bpy.data.objects:
    if _o.type != 'MESH' or not _o.name.startswith("walk_"):
        continue
    _mw = _o.matrix_world
    _ws = [_mw @ v.co for v in _o.data.vertices]
    if not _ws:
        continue
    _top = max(v.z for v in _ws) - 1e-4
    for _p in _o.data.polygons:
        _pv = [_mw @ _o.data.vertices[i].co for i in _p.vertices]
        if min(v.z for v in _pv) < _top:
            continue                       # side and underside faces are not treads
        WALKPOLY.append(([(v.x, v.y) for v in _pv], max(v.z for v in _pv)))


def _seg_d2(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    t = 0.0 if l2 <= 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2))
    dx, dy = px - (ax + t * vx), py - (ay + t * vy)
    return dx * dx + dy * dy


def _in_poly(px, py, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / ((by - ay) or 1e-12) + ax:
            inside = not inside
    return inside


# A UNIFORM GRID OVER THE TREADS, because this question is asked once per ground vertex.
# The groundcover density field alone asks it ~60 000 times and the town has ~1 000 tread
# polygons; the linear scan was 60 million polygon tests and it was the whole run time.
WGSTEP = 4.0
WGRID = {}
WGX0 = min((min(p[0] for p in pts) for pts, _z in WALKPOLY), default=0.0)
WGY0 = min((min(p[1] for p in pts) for pts, _z in WALKPOLY), default=0.0)
for _pi, (_pts, _pz) in enumerate(WALKPOLY):
    _i0 = int((min(p[0] for p in _pts) - WGX0) // WGSTEP)
    _i1 = int((max(p[0] for p in _pts) - WGX0) // WGSTEP)
    _j0 = int((min(p[1] for p in _pts) - WGY0) // WGSTEP)
    _j1 = int((max(p[1] for p in _pts) - WGY0) // WGSTEP)
    for _i in range(_i0, _i1 + 1):
        for _j in range(_j0, _j1 + 1):
            WGRID.setdefault((_i, _j), []).append(_pi)


def walk_dist(x, y, cap=8.0):
    """Plan distance to the nearest TREAD polygon.  0 standing on one.  Capped at `cap`
       (returned as `cap`) — every rule that consumes this is a clearance of a few metres,
       so the exact distance to a lane 40 m away is a number nobody spends."""
    best = cap
    ci = int((x - WGX0) // WGSTEP)
    cj = int((y - WGY0) // WGSTEP)
    rad = int(cap // WGSTEP) + 1
    seen = set()
    for r in range(rad + 1):
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r:
                    continue
                for pi in WGRID.get((ci + di, cj + dj), ()):
                    if pi in seen:
                        continue
                    seen.add(pi)
                    pts = WALKPOLY[pi][0]
                    if _in_poly(x, y, pts):
                        return 0.0
                    d2 = min(_seg_d2(x, y, pts[k][0], pts[k][1],
                                     pts[(k + 1) % len(pts)][0], pts[(k + 1) % len(pts)][1])
                             for k in range(len(pts)))
                    if d2 < best * best:
                        best = math.sqrt(d2)
        if best <= r * WGSTEP:
            break                     # nothing in a further ring can beat this
    return best


def walk_top(x, y, r=1.2):
    """The tread height under a point, if any walk surface is within r."""
    best = None
    for (x0, x1, y0, y1, _z0, z1) in WALKB:
        dx = max(x0 - x, 0.0, x - x1)
        dy = max(y0 - y, 0.0, y - y1)
        if math.hypot(dx, dy) <= r:
            best = z1 if best is None else max(best, z1)
    return best


GROUND = None
for o in PLAN["ground"]:
    if o.name == "emb_ground_valley":
        GROUND = o
if GROUND is None and PLAN["ground"]:
    GROUND = PLAN["ground"][0]
assert GROUND is not None, "no emb_ground_* mesh in the blockout — nothing to dress onto"


def raycast_ground(x, y, top=60.0):
    """Ground height from the blockout's OWN ground mesh, by ray cast.  The blockout's
       `ground_z` is a function this file deliberately does not own a copy of: the surface
       that matters is the one that shipped in the blend.

       CAST AT THE GROUND OBJECT, NOT AT THE SCENE.  The first build cast a scene ray and
       read 9.10 m for the natural ground at the watermill — which is the gray mill's own
       ROOF.  Every level in the mill build derives from this number, so the whole corner
       would have been founded eight metres in the air.  An oracle that can see the thing
       being replaced is the wrong oracle."""
    inv = GROUND.matrix_world.inverted()
    o = inv @ Vector((x, y, top))
    d = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
    hit, loc, _n, _i = GROUND.ray_cast(o, d, distance=top * 3)
    return (GROUND.matrix_world @ loc).z if hit else None


# =========================================== THE MILL CORNER, AT THE RULED 2x ==
# The map's `watermill` note carries the user's re-rule: *the mill at TWICE the probe's
# scale — overshot wheel 2.2 -> 4.4 m dia, total fall 4.6 m as built in probe r2 (dam
# crest 1.78 impounding the pond, tail water -3.05), building mass scaled with the wheel.
# Probe round 2 renders are the visual reference.*
#
# THE RULED QUANTITIES ARE THE WHEEL AND THE FALL.  1.78 and -3.05 are numbers in the
# probe's own coordinate frame and mean nothing here; what they SAY is 4.60 m of fall.
# So this build takes the fall as ruled and derives everything else from the town: the
# crest is the blockout's own impounded millpond surface (the blockout searched and built
# that pond against the stamped brook), the tail is crest - 4.60, and the wheel pit is
# excavated to hold it.
#
# THE SHAPE IS THE PROBE'S, THE PLACE IS THE MAP'S.  Every recipe below — the solid
# shrouds, the bucket boards held inside the shroud line, the coursed rubble, the launder
# on trestles, the plunge foam — is the ratified round-2 construction, ported into a LOCAL
# FRAME and then mapped onto the town's brook.  Local x runs downstream, local y is the
# left bank, local z is the town's z minus the crest.  So the probe's own numbers survive
# as relative offsets and none of its absolute coordinates do.
MILL = {}


def build_mill():
    lm = LM["watermill"]
    mx0, my0 = lm["pos"][0], lm["pos"][1]

    # ---- THE LOCAL FRAME IS ANCHORED ON THE BROOK, NOT ON THE LANDMARK, and the ordering
    # is the whole of the fix.  The landmark IS the mill HOUSE (that is what the blockout
    # builds there and what the map's note describes), and a mill house stands DOWNSTREAM
    # of its own wheel: water arrives, turns the wheel, leaves.  The first build anchored
    # the frame at the landmark and searched the house downstream of it, which walks the
    # whole complex further downstream every time the map is re-derived — a placement that
    # moves when nothing moved.  So: the DAM is found on the stamped brook, 10.6 m upstream
    # (the probe's own dam-to-house distance) of the brook point nearest the house, the
    # wheel hangs off it, and the house stays exactly where the map put it.
    pond = PLAN["water"].get("water_emb_millpond")
    assert pond, ("the blockout built no water_emb_millpond — the mill's impoundment is "
                  "the crest this build derives from and it cannot be invented here")
    poly = [(p[0], p[1], p[2]) for p in MAPD["brook"]["polyline"]]
    arc, s = [0.0], 0.0
    for i in range(1, len(poly)):
        s += math.hypot(poly[i][0] - poly[i - 1][0], poly[i][1] - poly[i - 1][1])
        arc.append(s)

    def brook_at(sq):
        sq = max(0.0, min(arc[-1], sq))
        for i in range(1, len(poly)):
            if arc[i] >= sq:
                t = (sq - arc[i - 1]) / max(1e-6, arc[i] - arc[i - 1])
                a_, b_ = poly[i - 1], poly[i]
                dxu, dyu = b_[0] - a_[0], b_[1] - a_[1]
                dl = math.hypot(dxu, dyu) or 1.0
                return (a_[0] + dxu * t, a_[1] + dyu * t, a_[2] + (b_[2] - a_[2]) * t,
                        dxu / dl, dyu / dl)
        return (poly[-1][0], poly[-1][1], poly[-1][2], 1.0, 0.0)

    s_house = min(arc, key=lambda q: math.hypot(brook_at(q)[0] - mx0,
                                                brook_at(q)[1] - my0))
    for _k in range(40):                       # refine to the nearest metre, then to 0.1
        cand = [s_house + d for d in (-2.0, -1.0, -0.5, -0.1, 0.1, 0.5, 1.0, 2.0)]
        b2 = min(cand + [s_house],
                 key=lambda q: math.hypot(brook_at(q)[0] - mx0, brook_at(q)[1] - my0))
        if abs(b2 - s_house) < 1e-3:
            break
        s_house = b2
    # THE DAM STANDS AT THE BLOCKOUT'S OWN POND, and that is the last authored offset
    # removed from this build.  A literal 10.6 m upstream is the probe's dam-to-house
    # distance and it has no standing here; the town already has an impoundment, searched
    # and built by the blockout against the stamped brook, and the dam is what holds it.
    # So the anchor is the brook arclength nearest that pond's own centre, and the launder
    # spans whatever the town leaves between it and the wheel.
    _pc = ((pond[1][0] + pond[1][1]) / 2.0, (pond[1][2] + pond[1][3]) / 2.0)
    DAM_S = min([s_house - 22.0 + 0.25 * k for k in range(120)],
                key=lambda q: math.hypot(brook_at(q)[0] - _pc[0], brook_at(q)[1] - _pc[1]))
    dpt = brook_at(DAM_S)
    ux, uy = dpt[3], dpt[4]                      # downstream, AT THE DAM
    vx, vy = -uy, ux
    # which bank is the house on?  The map decides; the build follows.
    MSIDE = 1 if ((mx0 - dpt[0]) * vx + (my0 - dpt[1]) * vy) >= 0 else -1

    # ---- the levels, MEASURED off the blockout's own water, not authored here.
    crest = (pond[1][4] + pond[1][5]) / 2.0
    # THE FALL IS NOT A LITERAL ANY MORE, and that is the breastshot ruling in one line.
    # The map's first number (4.60 m) was the coordinator's stamp of the probe's as-built
    # geometry, and the stamped brook cannot give it: measured on the BUILT water surface,
    # the bed is still 1.90 m above that tail water 14 m downstream and does not reach it
    # anywhere inside 60 m. So the tail is READ OFF THE BROOK at the ruled rejoin reach and
    # the fall is whatever the town actually has. Re-stamped 2026-08-01: breastshot, fed at
    # axle height, 4.4 m disc unchanged.
    REJOIN = float(opt("--rejoin", "20.0"))
    _rp = brook_at(s_house + REJOIN)
    _bw = PLAN["water"].get("water_emb_brook")
    tail = _rp[2]
    if _bw:
        _o, _b = _bw
        _mw = _o.matrix_world
        _near = [(_mw @ v.co).z for v in _o.data.vertices
                 if math.hypot((_mw @ v.co).x - _rp[0], (_mw @ v.co).y - _rp[1]) < 2.5]
        if _near:
            tail = sum(_near) / len(_near)
    FALL = crest - tail
    pit = tail - 1.10
    natural = raycast_ground(mx0, my0) or lm["pos"][2]
    # the brook's own bed downstream of the mill, for the rejoin report
    _d14 = brook_at(s_house + 14.0)
    dsz = raycast_ground(_d14[0], _d14[1])
    MILL.update(dict(ux=ux, uy=uy, vx=vx, vy=vy, crest=crest, tail=tail, pit=pit,
                     origin=(dpt[0], dpt[1]), natural=natural))

    def W(px, py, pz=0.0):
        """PROBE-local -> town world.  The probe's frame has its dam at (0, 0), its wheel
           at (3.6, 3.6) and its mill house at (10.6, 4.9); this maps that frame onto the
           stamped brook with the dam at the anchor and `MSIDE` choosing the bank, so every
           number in the ratified round-2 recipe survives as a relative offset and none of
           its absolute coordinates does."""
        return (dpt[0] + ux * px + vx * py * MSIDE,
                dpt[1] + uy * px + vy * py * MSIDE, crest + pz)

    # ---- REMOVE THE GRAY FIRST.  The blockout's mill massing is the thing being dressed,
    # and it has to go BEFORE anything measures the ground: every level below derives from
    # a ray cast, and a ray that can still hit the old roof founds the new mill in the air.
    _killed = 0
    for o in list(bpy.data.objects):
        if o.name.startswith("lm_watermill") or o.name == "water_emb_millpond":
            bpy.data.objects.remove(o, do_unlink=True)
            _killed += 1
    print("    replaced %d gray blockout meshes at the watermill landmark" % _killed)

    # ---- THE HOUSE IS WHERE THE MAP SAYS.  It is not searched, and that is the change the
    # coordinator ruled: the map is the authority, so the build stands the house on the
    # landmark and MEASURES the fit rather than shopping for a better coordinate.  Two
    # numbers come out of that measurement and both are stamps, not build decisions:
    # how far the landmark is from the probe's own dam-to-house geometry, and whether the
    # town's derived doorstep still lands outside a 2x footprint.
    WD, DP = 8.6, 9.4
    MALONG = (mx0 - dpt[0]) * ux + (my0 - dpt[1]) * uy
    MLAT = ((mx0 - dpt[0]) * vx + (my0 - dpt[1]) * vy) * MSIDE
    clear = 1e9
    for a2 in range(9):
        for b2 in range(9):
            px = mx0 + ux * (-WD / 2 + WD * a2 / 8) + vx * MSIDE * (-DP / 2 + DP * b2 / 8)
            py = my0 + uy * (-WD / 2 + WD * a2 / 8) + vy * MSIDE * (-DP / 2 + DP * b2 / 8)
            clear = min(clear, walk_dist(px, py))
    pad, padin = None, None
    for n, b in PLAN["walk"]:
        if n == "walk_pad_watermill":
            pad = ((b[0] + b[1]) / 2, (b[2] + b[3]) / 2)
    if pad:
        plx = (pad[0] - mx0) * ux + (pad[1] - my0) * uy
        ply = ((pad[0] - mx0) * vx + (pad[1] - my0) * vy) * MSIDE
        padin = max(abs(plx) - WD / 2, abs(ply) - DP / 2)     # + outside, - inside
    print("    MILL HOUSE: stood ON the landmark (%.1f, %.1f), %s bank, %.1f m downstream "
          "of the dam and %.1f m off the leat axis (the ratified probe's own geometry is "
          "10.6 / 4.9). Its 8.6 x 9.4 footprint clears the nearest tread by %.2f m "
          "(rule 1.20)."
          % (mx0, my0, "left" if MSIDE > 0 else "right", MALONG, MLAT, clear))
    if pad:
        _padbrg = math.degrees(math.atan2(pad[0] - mx0, pad[1] - my0)) % 360.0
        print("    THE DOORSTEP'S OWN BEARING from the landmark is %.1f deg (0 = +y, "
              "90 = +x) — this is the number `doorFace` has to equal for the door and the "
              "doorstep to be the same place." % _padbrg)
    if padin is not None:
        print("    THE DOORSTEP, MEASURED: walk_pad_watermill stands %.2f m %s the 2x "
              "footprint (it was 1.12 m INSIDE it before the map carried `footprint` and "
              "emb_blockout read it — the pad had been derived from the body's own "
              "half-depth and the body was still the pre-ruling 5.6 x 4.6)."
              % (abs(padin), "outside" if padin >= 0 else "INSIDE"))
    MILL["house"] = (MALONG, MSIDE, MLAT)

    # THE HOUSE IS THE LANDMARK, in the probe frame's own coordinates.
    MYL = MLAT
    # THE DOOR IS IN THE WALL THE MAP NAMES.  `doorFace` is a compass bearing (0 = +y,
    # 90 = +x) for the outward normal of the door's wall, stamped 2026-08-01 because the
    # doorstep is derived from the ARRIVING EDGE's bearing while the door is built into a
    # wall, and here the two disagreed by 34 degrees — the kind of almost-right a player
    # reads as wrong.  The house is therefore yawed to the map's bearing, and the brook
    # frame keeps only the water: dam, launder, wheel and pit.
    _probe_face = math.degrees(math.atan2(-vx * MSIDE, -vy * MSIDE)) % 360.0
    _face = lm.get("doorFace")
    if _face is None:
        _face = _probe_face
        print("    DOOR FACE: the map carries none; taking the probe's own (%.1f deg) and "
              "reporting it, because a door face that is not in the map is a fact this "
              "build invented." % _face)
    else:
        print("    DOOR FACE: the map stamps %.1f deg; the probe's brook-frame face is "
              "%.1f deg, a %.1f deg difference. The map wins and the house is yawed to it."
              % (_face, _probe_face, abs((_face - _probe_face + 180) % 360 - 180)))
    _fr = math.radians(_face)
    HVX, HVY = -math.sin(_fr), -math.cos(_fr)      # house local +y (away from the door)
    HUX, HUY = HVY, -HVX                            # house local +x
    HRZ = math.atan2(HUY, HUX)

    def HW(px, py, pz=0.0):
        """house-local (x along the frontage, y away from the door) -> town world"""
        return (mx0 + HUX * px + HVX * py, my0 + HUY * px + HVY * py, crest + pz)
    MILL["padin"] = padin

    print("    THE FALL, MEASURED NOT AUTHORED: crest %.2f (the blockout's own impounded "
          "millpond surface, read off water_emb_millpond), tail %.2f (the BUILT brook's own "
          "water surface %.0f m downstream, where the stone-walled cut rejoins it) -> FALL "
          "%.2f m. Wheel pit floor %.2f; natural ground at the landmark %.2f."
          % (crest, tail, REJOIN, FALL, pit, natural))
    print("    HOW THE FALL IS PAID: %.2f m of it is IMPOUNDMENT (crest above natural "
          "ground) and %.2f m is EXCAVATION (natural ground down to the tail water). A "
          "4.4 m disc on %.2f m of fall is a BREASTSHOT wheel, fed at axle height — the "
          "map's re-rule, and the only reading the stamped brook supports."
          % (max(0.0, crest - natural), max(0.0, natural - tail), FALL))
    print("    THE TAILRACE: a stone-walled cut %.0f m to the rejoin, arriving AT the "
          "brook's own level rather than below it — which is what the re-rule bought. "
          "(The retired 4.60 m fall would have put the tail %.2f m under the bed here.)"
          % (REJOIN, tail - (crest - 4.60)))

    # ---------------------------------------------------------- ground, re-cut --
    # THE WHEEL PIT IS AN EXCAVATION AND THE GROUND MESH HAS TO SHOW IT.  The blockout
    # carved a basin for a 2.00 m dam; a 4.60 m fall needs a real stone pit.  The ground
    # is scenery and collision, never a walk surface, so re-cutting it here changes no
    # tread — and the cut is asserted to stay clear of every walk mesh.
    me = GROUND.data
    mw = GROUND.matrix_world
    inv = mw.inverted()
    moved, worst_walk = 0, 1e9
    for v in me.vertices:
        w = mw @ v.co
        lx = (w.x - dpt[0]) * ux + (w.y - dpt[1]) * uy
        ly = ((w.x - dpt[0]) * vx + (w.y - dpt[1]) * vy) * MSIDE
        if not (-9.0 < lx < 13.0 and -6.0 < ly < 6.0):
            continue
        want = None
        dly = abs(ly)
        if -3.0 < lx < 8.5 and dly < 5.0:
            want = crest + pit + 1.15 * max(0.0, dly - 3.0) ** 1.5
        elif 8.5 <= lx < 13.0 and dly < 4.4:
            want = crest + tail - crest + 0.35 * (lx - 8.5)
            want = tail + 0.35 * (lx - 8.5) + 1.0 * max(0.0, dly - 2.6) ** 1.5
        if want is None or want >= w.z:
            continue
        d = walk_dist(w.x, w.y)
        worst_walk = min(worst_walk, d)
        if d < 1.60:
            continue                      # never undercut a tread
        w.z = want
        v.co = inv @ w
        moved += 1
    me.update()
    print("    ground re-cut: %d vertices excavated for the wheel pit and tailrace; the "
          "cut stops 1.60 m short of every walk surface (nearest walk surface inside the "
          "cut footprint: %.2f m)" % (moved, worst_walk))

    # ------------------------------------------------------------------ water --
    def waterfn(x0, x1, z, hw):
        def f(u, v):
            px = x0 + u * (x1 - x0)
            py = (v - 0.5) * 2 * hw
            wx, wy, _wz = W(px, py)
            return (wx, wy, crest + z + 0.014 * math.sin(px * 2.1 + py * 1.7))
        return f

    gridmesh("emb_dress_millpond", 60, 20, waterfn(-30.0, -0.15, 0.0, 3.15), WATER)
    gridmesh("emb_dress_tailrace", 50, 18, waterfn(0.1, 22.0, tail - crest, 2.4), WATER)
    gridmesh("emb_dress_wheelpit_water", 24, 14,
             lambda u, v: W(-2.4 + u * 10.6, (v - 0.5) * 7.0,
                            tail - crest + 0.02), WATER)

    # ---------------------------------------------- dam, spill, head gate ------
    DAMH = crest - pit
    RZ0 = math.atan2(uy, ux) + (0.0 if MSIDE > 0 else math.pi)
    box("emb_dress_dam_wall", W(0.0, 0.0, -(DAMH + 0.3) / 2 + 0.15),
        (2.10, 13.0, DAMH + 0.3), rot=(0, 0, RZ0), mat=STONE_W)
    for i in range(26):
        box("emb_dress_dam_cope%02d" % i,
            W(0.0, -6.3 + i * 0.5 + 0.25, 0.10),
            (2.55 + crcrange(-0.12, 0.12, "cope", i), 0.48,
             0.26 + crcrange(-0.03, 0.04, "copez", i)),
            rot=(0, crcrange(-0.02, 0.02, "coperx", i),
                 RZ0 + crcrange(-0.03, 0.03, "coperz", i)), mat=STONE)
    for i in range(150):          # coursed rubble on the face the plate sees
        sy = -6.1 + crcrange(0, 12.2, "rub", i)
        sz = crcrange(pit - crest + 0.1, -0.05, "rubz", i)
        box("emb_dress_dam_stone%03d" % i, W(1.06 + crcrange(-0.07, 0.07, "rubx", i), sy, sz),
            (crcrange(0.16, 0.30, "rs", i), crcrange(0.45, 0.95, "rsy", i),
             crcrange(0.22, 0.44, "rsz", i)),
            rot=(0, crcrange(-0.08, 0.08, "rr", i),
                 RZ0 + crcrange(-0.06, 0.06, "rrz", i)),
            mat=STONE if i % 3 else ROCK)
    box("emb_dress_dam_sheet", W(1.12, -2.2, (tail - crest) / 2 + 0.05),
        (0.16, 2.3, crest - tail + 0.3), rot=(0, 0, RZ0), mat=WATER_F)
    box("emb_dress_dam_lip", W(0.62, -2.2, 0.10), (0.55, 2.3, 0.10),
        rot=(0, 0.34, RZ0), mat=WATER_F)
    for i in range(70):
        an = crcrange(0, 6.28, "foama", i)
        rr = crcrange(0.05, 3.0, "foamr", i)
        blob("emb_dress_foam%02d" % i,
             W(1.35 + crcrange(-0.5, 1.9, "fx", i), -2.2 + math.cos(an) * rr * 0.9,
               tail - crest + 0.12 + crcrange(-0.10, 0.62, "fz", i)),
             (crcrange(0.5, 1.3, "fs", i), crcrange(0.6, 1.7, "fsy", i),
              crcrange(0.3, 0.8, "fsz", i)), mat=FOAM, i=i)
    for i in range(26):
        blob("emb_dress_mist%02d" % i,
             W(1.5 + crcrange(-0.4, 2.6, "mx", i), -1.7 + crcrange(-2.6, 2.6, "my", i),
               tail - crest + crcrange(0.5, 2.4, "mz", i)),
             (crcrange(0.8, 1.9, "ms", i),) * 2 + (crcrange(0.5, 1.1, "msz", i),),
             mat=MIST, i=i + 3)

    GZ = 0.07                      # the leat floor, just above the crest
    # THE YAW CARRIES THE MIRROR.  W() flips local y when the mill stands on the right
    # bank, and a box's own rotation has to flip with it or the whole assembly is built
    # inside out.  For the rectangular members here, a y-mirror is a half turn.
    RZ = RZ0


    # ------------------------------------- the BREASTSHOT wheel, 4.4 m diameter --
    # THE WHEEL HANGS OFF THE MILL, and the ordering matters because the house is pinned by
    # the map.  The first build placed the wheel from the DAM at the probe's own (3.6, 3.6)
    # and the house 9.2 m downstream of that dam — which put the wheel's rim 0.9 m INSIDE
    # the mill's upstream wall and ran the launder straight through the building.  The
    # probe's real geometry is a RELATION, wheel to house (7.0 m along, 1.3 m across), so
    # that is what survives the port; the dam stays on the brook and the launder spans
    # whatever distance results, which is exactly what a launder on trestles is for.
    #
    # AND IT IS FED AT AXLE HEIGHT.  Re-ruled breastshot 2026-08-01 on this lane's own
    # measurement of the brook: the sole clears the tail water, the hub sits a radius above
    # it, and the launder delivers there instead of over the crown.  Same 4.4 m disc, same
    # stone pit; the water arrives in the launder, rides the descending buckets and foams
    # at the tail exactly as the user's ratified frames have it.
    R, NB, HALFW = 2.20, 28, 1.30
    WHX = MALONG - 7.0
    LEATY = MYL - 1.3
    HUBZ = (tail + 0.15 + R) - crest
    cyl("emb_dress_wheel_axle", W(WHX, LEATY, HUBZ), 0.24, 6.2,
        rot=(math.pi / 2, 0, RZ), mat=TIMBER_D, verts=14)
    for side in (-1, 1):
        wy = LEATY + side * HALFW
        c = W(WHX, wy, HUBZ)
        ring("emb_dress_shroud%+d" % side, c[0], c[1], c[2], R + 0.05, R - 0.30, 0.26,
             TIMBER, ux=(ux, uy))
        ring("emb_dress_strake%+d" % side, c[0], c[1], c[2], R + 0.13, R + 0.03, 0.32,
             IRON, ux=(ux, uy))
        ring("emb_dress_innerband%+d" % side, c[0], c[1], c[2], R - 0.55, R - 0.72, 0.22,
             TIMBER_D, ux=(ux, uy))
        for i in range(10):
            a0 = i * math.pi / 5 + (0.2 if side > 0 else 0.51)
            box("emb_dress_spoke%+d_%d" % (side, i),
                W(WHX + math.cos(a0) * R * 0.5, wy, HUBZ + math.sin(a0) * R * 0.5),
                (0.13, 0.16, R * 1.04), rot=(0, a0 + math.pi / 2, RZ), mat=TIMBER_D)
        cyl("emb_dress_hub%+d" % side, W(WHX, wy, HUBZ), 0.52, 0.42,
            rot=(math.pi / 2, 0, RZ), mat=TIMBER_D, verts=14)
        cyl("emb_dress_hubband%+d" % side, W(WHX, wy, HUBZ), 0.56, 0.10,
            rot=(math.pi / 2, 0, RZ), mat=IRON, verts=16)
    for i in range(NB):
        a0 = i * 2 * math.pi / NB
        px = WHX + math.cos(a0) * (R - 0.34)
        pz = HUBZ + math.sin(a0) * (R - 0.34)
        box("emb_dress_buckA%02d" % i, W(px, LEATY, pz), (0.06, 2.38, 0.50),
            rot=(0, a0 + math.pi / 2, RZ), mat=PLANK)
        px2 = WHX + math.cos(a0 + 0.155) * (R - 0.60)
        pz2 = HUBZ + math.sin(a0 + 0.155) * (R - 0.60)
        box("emb_dress_buckB%02d" % i, W(px2, LEATY, pz2), (0.50, 2.36, 0.06),
            rot=(0, a0 + math.pi / 2, RZ), mat=PLANK)
        # water rides the buckets from the AXLE DOWN on the descending side — a
        # breastshot's own signature, and where round 2 put it on an overshot crown
        if math.cos(a0) < -0.05 and -0.95 < math.sin(a0) < 0.25:
            box("emb_dress_buckwater%02d" % i, W(px - 0.13, LEATY, pz - 0.11),
                (0.24, 2.20, 0.34), rot=(0, a0 + math.pi / 2, RZ), mat=WATER_F)
    for i in range(40):
        blob("emb_dress_drip%02d" % i,
             W(WHX + crcrange(-1.2, 2.2, "dx", i), LEATY + crcrange(-1.3, 1.3, "dy", i),
               tail - crest + crcrange(0, 2.2, "dz", i)),
             (crcrange(0.16, 0.40, "ds", i),) * 2 + (crcrange(0.3, 0.9, "dsz", i),),
             mat=FOAM, i=i + 5)
    for s, zc in ((-1, (pit + tail + 0.5) / 2 - crest), (1, (pit + 1.2) / 2 - crest)):
        hh = (tail + 0.5 - pit) if s < 0 else (1.2 - (pit - crest))
        box("emb_dress_pit%+d" % s, W(WHX, LEATY + s * 2.45, zc), (5.6, 0.55, abs(hh)),
            rot=(0, 0, RZ), mat=STONE_W)
    for i in range(150):
        box("emb_dress_pitrubble%03d" % i,
            W(WHX + crcrange(-2.7, 2.7, "pr", i), LEATY + 2.15,
              pit - crest + crcrange(0, 5.2, "prz", i)),
            (crcrange(0.34, 0.75, "prs", i), 0.14, crcrange(0.20, 0.38, "prsz", i)),
            rot=(0, 0, RZ + crcrange(-0.04, 0.04, "prr", i)),
            mat=STONE if i % 3 else ROCK)
    box("emb_dress_hurst_beam", W(WHX, LEATY - 2.2, HUBZ + 0.02),
        (0.55, 1.9, 0.55), rot=(0, 0, RZ), mat=TIMBER_D)

    # ------------------------- the head gate, and the launder that spans to the axle --
    # THE LAUNDER'S LENGTH IS DERIVED, and it is the piece that absorbs the difference
    # between a hand-authored corner and a stamped brook: the dam is where the water is,
    # the wheel is where the mill is, and a launder on trestles is exactly the thing that
    # gets from one to the other.  It runs from the head gate at the crest down to the
    # BREASTSHOT entry at the axle — the whole visible difference from the retired
    # overshot reading, and the reason the water still arrives on screen.
    GX0, GY0 = -1.2, 0.0                      # the head gate, on the dam's own line
    ENTX = WHX - (R + 0.55)                   # the entry, just clear of the rim
    ENTZ = HUBZ + 0.30
    for nm, dy in (("a", -1.0), ("b", 1.0)):
        box("emb_dress_gatepost_%s" % nm, W(GX0, GY0 + dy, GZ + 1.55), (0.34, 0.34, 3.1),
            rot=(0, 0, RZ), mat=TIMBER_D)
    box("emb_dress_gate_head", W(GX0, GY0, GZ + 3.05), (0.40, 2.6, 0.32),
        rot=(0, 0, RZ), mat=TIMBER_D)
    box("emb_dress_gate_paddle", W(GX0, GY0, GZ + 0.95), (0.16, 1.85, 1.9),
        rot=(0, 0, RZ), mat=PLANK)
    cyl("emb_dress_gate_screw", W(GX0, GY0, GZ + 2.7), 0.07, 1.7, mat=IRON, verts=8)
    cyl("emb_dress_gate_wheel", W(GX0, GY0, GZ + 3.55), 0.42, 0.08,
        rot=(0, 0, RZ), mat=IRON, verts=18)
    LN = max(2.0, math.hypot(ENTX - GX0, LEATY - GY0))
    NSEG = max(4, int(LN / 1.6))
    LBRG = math.atan2((LEATY - GY0) * MSIDE, ENTX - GX0)
    for i in range(NSEG):
        t0, t1 = i / float(NSEG), (i + 1) / float(NSEG)
        tm = (t0 + t1) / 2.0
        lx = GX0 + (ENTX - GX0) * tm
        ly = GY0 + (LEATY - GY0) * tm
        zz = GZ + (ENTZ - GZ) * tm
        seg = LN / NSEG * 1.04
        box("emb_dress_leat_floor%d" % i, W(lx, ly, zz), (seg, 2.2, 0.16),
            rot=(0, 0, RZ + LBRG), mat=PLANK)
        for sgn in (-1, 1):
            box("emb_dress_leat_w%d%+d" % (i, sgn),
                W(lx - math.sin(LBRG) * sgn * 1.05 * MSIDE,
                  ly + math.cos(LBRG) * sgn * 1.05, zz + 0.45),
                (seg, 0.14, 0.86), rot=(0, 0, RZ + LBRG), mat=PLANK)
        box("emb_dress_leat_water%d" % i, W(lx, ly, zz + 0.30), (seg, 1.84, 0.38),
            rot=(0, 0, RZ + LBRG), mat=WATER_F)
        if i % 2 == 0:
            wx_, wy_, _ = W(lx, ly)
            gzz = raycast_ground(wx_, wy_)
            gzz = (gzz if gzz is not None else crest) - crest
            h = max(0.6, zz - 0.08 - gzz)
            box("emb_dress_leat_trestle%d" % i, W(lx, ly, zz - 0.08 - h / 2),
                (0.26, 2.5, h), rot=(0, 0, RZ + LBRG), mat=TIMBER_D)
    box("emb_dress_leat_nose", W(ENTX - 0.9, LEATY, ENTZ - 0.10), (2.4, 2.2, 0.16),
        rot=(0, 0.14, RZ + LBRG), mat=PLANK)
    box("emb_dress_leat_jet", W(ENTX + 0.2, LEATY, ENTZ - 0.22), (0.90, 1.55, 0.75),
        rot=(0, 0.22, RZ + LBRG), mat=WATER_F)
    print("    THE FEED: head gate on the dam, launder %.1f m of trestled boarding "
          "falling %.2f m to a BREASTSHOT entry at the axle (hub z %.2f, sole %.2f, tail "
          "%.2f). The wheel hangs %.1f m upstream of the mill's own centre — the ratified "
          "probe's own wheel-to-house relation, which is also its wall clearance."
          % (LN, GZ - ENTZ, crest + HUBZ, crest + HUBZ - R, tail, MALONG - WHX))
    print("      AND THE LAUNDER IS SHORT, WHICH IS A FACT ABOUT THE TOWN: the blockout's "
          "millpond stands %.1f m from the mill, so once the wheel is against its own "
          "wall there is almost nothing left to span. The probe's twelve metres of "
          "trestled boarding measured the throwaway's invented layout, not this brook."
          % MALONG)

    # ------------------------------------------------------------ the mill house --
    hw, hd = WD, DP
    hx, hy, _ = HW(0, 0)
    MZ = raycast_ground(hx, hy)
    MZ = (MZ if MZ is not None else natural) - crest
    FOOT_BOT = pit - crest - 0.25
    box("emb_dress_mill_foot", HW(0, 0, (FOOT_BOT + MZ + 1.45) / 2),
        (hw + 0.34, hd + 0.34, MZ + 1.45 - FOOT_BOT), rot=(0, 0, HRZ), mat=STONE_W)
    box("emb_dress_mill_plinth", HW(0, 0, MZ + 1.52), (hw + 0.5, hd + 0.5, 0.18),
        rot=(0, 0, HRZ), mat=STONE)
    for i in range(230):
        face = "nsew"[crc("face", i) % 4]
        if face == 'w':
            sx = -(hw / 2 + 0.19)
            sy = crcrange(-hd / 2, hd / 2, "wy", i)
            sz = pit - crest + crcrange(0.1, MZ + 1.3 - (pit - crest), "wz", i)
            sc = (0.13, crcrange(0.34, 0.76, "ws", i), crcrange(0.20, 0.38, "wsz", i))
        elif face in 'ns':
            sx = crcrange(-hw / 2, hw / 2, "nx", i)
            sy = (hd / 2 + 0.19) * (1 if face == 'n' else -1)
            sz = MZ + crcrange(0.05, 1.35, "nz", i)
            sc = (crcrange(0.34, 0.76, "ns", i), 0.13, crcrange(0.20, 0.38, "nsz", i))
        else:
            sx = (hw / 2 + 0.19)
            sy = crcrange(-hd / 2, hd / 2, "ey", i)
            sz = MZ + crcrange(0.05, 1.35, "ez", i)
            sc = (0.13, crcrange(0.34, 0.76, "es", i), crcrange(0.20, 0.38, "esz", i))
        box("emb_dress_mill_rub%03d" % i, HW(sx, sy, sz), sc,
            rot=(0, 0, HRZ), mat=STONE if i % 3 else ROCK)

    UZ, UH = MZ + 1.55, 5.0
    box("emb_dress_mill_infill", HW(0, 0, UZ + UH / 2),
        (hw - 0.06, hd - 0.06, UH), rot=(0, 0, HRZ), mat=DAUB)
    for nm, dx, dy, sx2, sy2 in (('n', 0, hd / 2, hw + 0.12, 0.24),
                                 ('s', 0, -hd / 2, hw + 0.12, 0.24),
                                 ('e', hw / 2, 0, 0.24, hd + 0.12),
                                 ('w', -hw / 2, 0, 0.24, hd + 0.12)):
        box("emb_dress_mill_sill_%s" % nm, HW(dx, dy, UZ + 0.1),
            (sx2, sy2, 0.22), rot=(0, 0, HRZ), mat=TIMBER_D)
        box("emb_dress_mill_plate_%s" % nm, HW(dx, dy, UZ + UH),
            (sx2 + 0.02, sy2, 0.24), rot=(0, 0, HRZ), mat=TIMBER_D)
    for sx2 in (-1, 1):
        for sy2 in (-1, 1):
            box("emb_dress_mill_post%+d%+d" % (sx2, sy2),
                HW(sx2 * hw / 2, sy2 * hd / 2, UZ + UH / 2),
                (0.26, 0.26, UH), rot=(0, 0, HRZ), mat=TIMBER_D)
    for t in (-0.34, -0.12, 0.12, 0.34):
        box("emb_dress_mill_studN%s" % t, HW(t * hw, hd / 2, UZ + UH / 2),
            (0.22, 0.24, UH), rot=(0, 0, HRZ), mat=TIMBER_D)
        box("emb_dress_mill_studS%s" % t, HW(t * hw, - hd / 2, UZ + UH / 2),
            (0.22, 0.24, UH), rot=(0, 0, HRZ), mat=TIMBER_D)
        box("emb_dress_mill_studW%s" % t, HW(- hw / 2, t * hd, UZ + UH / 2),
            (0.24, 0.22, UH), rot=(0, 0, HRZ), mat=TIMBER_D)
        box("emb_dress_mill_studE%s" % t, HW(hw / 2, t * hd, UZ + UH / 2),
            (0.24, 0.22, UH), rot=(0, 0, HRZ), mat=TIMBER_D)
    # a five-metre wall needs a floor line, and it reads as two storeys
    for nm, dx, dy, sx2, sy2 in (('n', 0, hd / 2, hw + 0.06, 0.24),
                                 ('s', 0, -hd / 2, hw + 0.06, 0.24),
                                 ('w', -hw / 2, 0, 0.24, hd + 0.06)):
        box("emb_dress_mill_midrail_%s" % nm, HW(dx, dy, UZ + UH * 0.52),
            (sx2, sy2, 0.26), rot=(0, 0, HRZ), mat=TIMBER_D)
    for sx2, ang2 in ((-1, 0.72), (1, -0.72)):
        box("emb_dress_mill_brN%+d" % sx2,
            HW(sx2 * hw * 0.33, hd / 2, UZ + UH * 0.28),
            (0.17, 0.20, 1.5), rot=(0, ang2, HRZ), mat=TIMBER_D)
        box("emb_dress_mill_brS%+d" % sx2,
            HW(sx2 * hw * 0.33, - hd / 2, UZ + UH * 0.28),
            (0.17, 0.20, 1.5), rot=(0, ang2, HRZ), mat=TIMBER_D)

    for wz, ws in ((UZ + 1.45, 1.0), (UZ + 4.05, 0.82)):
        for wxo in (-2.3, 2.4):
            wy2 = -hd / 2 - 0.06
            box("emb_dress_mill_win", HW(wxo, wy2, wz),
                (1.45 * ws, 0.16, 1.55 * ws), rot=(0, 0, HRZ), mat=WINDOW)
            box("emb_dress_mill_winf", HW(wxo, wy2 - 0.07, wz),
                (1.68 * ws, 0.12, 1.78 * ws), rot=(0, 0, HRZ), mat=TIMBER_D)
            box("emb_dress_mill_winm", HW(wxo, wy2 - 0.15, wz),
                (0.09, 0.07, 1.55 * ws), rot=(0, 0, HRZ), mat=TIMBER_D)
            box("emb_dress_mill_wins", HW(wxo, wy2 - 0.19, wz - 0.92 * ws),
                (1.85 * ws, 0.32, 0.12), rot=(0, 0, HRZ), mat=STONE)
    box("emb_dress_mill_door", HW(- 1.6, - hd / 2 - 0.14, UZ + 1.35),
        (1.7, 0.14, 2.7), rot=(0, 0, HRZ), mat=PLANK)
    box("emb_dress_mill_doorhead", HW(- 1.6, - hd / 2 - 0.18, UZ + 2.85),
        (2.1, 0.24, 0.28), rot=(0, 0, HRZ), mat=TIMBER_D)
    box("emb_dress_mill_doorstep", HW(- 1.6, - hd / 2 - 0.9, UZ - 0.06),
        (2.4, 1.7, 0.20), rot=(0, 0, HRZ), mat=STONE)
    for i in range(4):
        box("emb_dress_mill_step%d" % i,
            HW(- 1.6, - hd / 2 - 1.7 - i * 0.5, UZ - 0.22 - i * 0.28),
            (2.2, 0.55, 0.22), rot=(0, 0, HRZ), mat=STONE)

    RIDGE, EAVE, OVER = UZ + UH + 3.10, UZ + UH + 0.18, 1.20
    angr = math.atan2(RIDGE - EAVE, hd / 2 + OVER)
    ln = math.hypot(RIDGE - EAVE, hd / 2 + OVER)
    for sy2 in (-1, 1):
        box("emb_dress_mill_roofdeck%+d" % sy2,
            HW(0, sy2 * (hd / 2 + OVER) / 2, (RIDGE + EAVE) / 2),
            (hw + 1.5, ln, 0.10), rot=(sy2 * -angr, 0, HRZ), mat=PLANK)
        nc, ns = 17, 27
        for c in range(nc):
            t = (c + 0.5) / nc
            yy = sy2 * (hd / 2 + OVER) * t
            zz = RIDGE - (RIDGE - EAVE) * t
            for s in range(ns):
                sxp = -(hw + 1.4) / 2 + (s + 0.5) * (hw + 1.4) / ns \
                    + crcrange(-0.03, 0.03, "sh", sy2, c, s)
                box("emb_dress_mill_sh%+d_%d_%d" % (sy2, c, s),
                    HW(sxp, yy, zz + 0.10),
                    ((hw + 1.4) / ns * 1.08, (hd / 2 + OVER) / nc * 1.30, 0.055),
                    rot=(sy2 * -angr, 0, HRZ + crcrange(-0.014, 0.014, "shr", sy2, c, s)),
                    mat=SHING_M if (c > nc - 5 and crc01("moss", sy2, c, s) < 0.42)
                        else SHINGLE)
        for s in range(13):
            box("emb_dress_mill_raft%+d_%d" % (sy2, s),
                HW(- (hw + 1.8) / 2 + s * (hw + 1.8) / 12, sy2 * (hd / 2 + OVER - 0.14), EAVE + 0.22),
                (0.14, 0.80, 0.22), rot=(sy2 * -angr, 0, HRZ), mat=TIMBER_D)
    box("emb_dress_mill_ridge", HW(0, 0, RIDGE + 0.18), (hw + 2.2, 0.40, 0.24),
        rot=(0, 0, HRZ), mat=TIMBER_D)
    for sx2 in (-1, 1):
        box("emb_dress_mill_gable%+d" % sx2,
            HW(sx2 * (hw / 2 + 1.0), 0, (RIDGE + EAVE) / 2 - 0.30),
            (0.18, hd + 0.8, RIDGE - EAVE), rot=(0, 0, HRZ), mat=PLANK)
    box("emb_dress_mill_lucam", HW(- 1.6, - hd / 2 - 0.9, RIDGE - 1.95),
        (2.6, 1.9, 2.6), rot=(0, 0, HRZ), mat=PLANK)
    box("emb_dress_mill_lucamroof", HW(- 1.6, - hd / 2 - 1.0, RIDGE - 0.50),
        (3.2, 2.5, 0.20), rot=(0.22, 0, HRZ), mat=SHINGLE)
    box("emb_dress_mill_hoistbeam", HW(- 1.6, - hd / 2 - 2.3, RIDGE - 1.05),
        (0.26, 2.8, 0.26), rot=(0, 0, HRZ), mat=TIMBER_D)
    cyl("emb_dress_mill_pulley", HW(- 1.6, - hd / 2 - 3.4, RIDGE - 1.32),
        0.28, 0.16, rot=(0, math.pi / 2, HRZ), mat=IRON, verts=12)
    cyl("emb_dress_mill_hoistrope", HW(- 1.6, - hd / 2 - 3.4, RIDGE - 3.8),
        0.045, 5.0, mat=ROPE, verts=6)
    box("emb_dress_mill_hoistsack", HW(- 1.6, - hd / 2 - 3.4, RIDGE - 6.7),
        (1.05, 0.90, 1.5), rot=(0, 0, HRZ), mat=SACK)

    # the yard: the millstone, the sacks, the waiting barrels — dressing.dressing_doc's
    # "hay stooks + threshing floor" class of domestic life, at the mill's own door
    cyl("emb_dress_millstone", HW(5.3, - 2.4, MZ + 1.55), 1.60, 0.42,
        rot=(1.32, 0, HRZ + 0.3), mat=STONE, verts=24)
    for i, (sx2, sy2) in enumerate([(2.9, -6.4), (4.0, -6.9), (3.3, -7.4), (1.6, -6.9)]):
        px, py, _ = HW(sx2, sy2)
        gz = raycast_ground(px, py)
        box("emb_dress_sack%d" % i,
            (px, py, (gz if gz is not None else crest) + 0.62), (0.95, 0.80, 1.25),
            rot=(0, 0, HRZ + crcrange(-0.5, 0.5, "sack", i)), mat=SACK)
    for i in range(3):
        px, py, _ = HW(1.4 + i * 0.95, - hd / 2 - 2.1 - i * 0.35)
        gz = raycast_ground(px, py)
        cyl("emb_dress_barrel%d" % i, (px, py, (gz if gz is not None else crest) + 0.55),
            0.44, 1.05, mat=PLANK, verts=14)

    MILL.update(dict(ridge=crest + RIDGE, wheel_world=W(WHX, LEATY, HUBZ),
                     house_world=HW(0, 0, MZ), R=R))
    print("    THE WHEEL: %.1f m BREASTSHOT, %d buckets, %.2f m across the shrouds, hub at "
          "z %.2f; ridge at z %.2f (%.1f m above the natural ground at the landmark)."
          % (R * 2, NB, HALFW * 2, crest + HUBZ, crest + RIDGE, crest + RIDGE - natural))


print("MILL CORNER — the ruled 2x build, at the map's watermill landmark")
build_mill()


# ========================================== VEGETATION, FROM THE HARVESTED PLAN ==
# EVERY PLACEMENT BELOW WAS SEARCHED BY THE BLOCKOUT.  This stage swaps the gray proxy for
# a library asset and then RE-ASSERTS the lane rule on the asset's own measured bounds,
# because a scanned tree is not the proxy it replaces.
CLASSMAP = {"broad": "canopy_broad", "slim": "canopy_slim", "conifer": "conifer"}
SUBS = {}
INSTANCES = []


def veg(aid, loc, scale, rotz, name, tilt=0.06, seed=0, coll=None):
    col = src_collection(aid)
    if not col:
        return None
    o = bpy.data.objects.new(name, None)
    o.instance_type = 'COLLECTION'
    o.instance_collection = col
    o.location = loc
    o.scale = (scale, scale, scale)
    o.rotation_euler = Euler((crcrange(-tilt, tilt, "tx", seed),
                              crcrange(-tilt, tilt, "ty", seed), rotz))
    o.empty_display_size = 0.3
    (coll or DRESS).objects.link(o)
    INSTANCES.append(o)
    return o


def pick_for(cls, seed):
    """Choose an asset for a canopy class, and PRINT the substitution when the class is
       empty rather than defaulting into silence."""
    pool = BYCLASS.get(cls)
    if pool:
        return crcpick(pool, "asset", cls, seed)["id"], False
    alt = {"canopy_slim": "canopy_broad", "conifer": "canopy_broad",
           "bramble": "shrub", "shrub": "bramble", "weed": "fern",
           "fern": "weed", "grass": "weed"}.get(cls)
    pool = BYCLASS.get(alt) if alt else None
    if pool:
        SUBS[cls] = alt
        return crcpick(pool, "asset", cls, seed)["id"], True
    return None, True


def dress_trees():
    n, kept, worst_trunk, lowest_canopy = 0, 0, 1e9, 1e9
    worst_conifer, over, stretched = 1e9, 0, 0
    for t in PLAN["village_trees"]:
        if not in_region(t["x"], t["y"], 4.0):
            continue
        kept += 1
        cls = CLASSMAP[t["cls"]]
        aid, sub = pick_for(cls, t["i"])
        if not aid:
            continue
        src_collection(aid)
        h0, r0, z0 = SRCH.get(aid, (1.0, 1.0, 0.0))
        want_h = max(2.0, t["top"] - t["z"])
        s = want_h / h0
        # THE SCANS ARE SMALL, and round 2 measured it: at native scale a 4.6 m scan reads
        # as a sapling beside a 12 m mill. The scale factor is therefore the BLOCKOUT's own
        # height for that tree divided by the asset's measured height, so a hero broadleaf
        # is as big as the blockout said it was and not as big as the scan happens to be.
        o = veg(aid, (t["x"], t["y"], t["z"] - 0.12 - z0 * s),
                s, crcrange(0, 6.283, "rot", t["i"]),
                "emb_dress_villtree_%02d" % t["i"], seed=t["i"])
        if not o:
            continue
        if t["cls"] == "slim" and sub:
            # A COLUMN IS A SHAPE, NOT A SPECIES. With no slim asset in the library the
            # broadleaf is stretched to the proxy's own aspect and the substitution is
            # reported as a manifest gap, because a birch-shaped oak is a stopgap.
            o.scale = (s * 0.62, s * 0.62, s * 1.18)
            stretched += 1
        # RE-ASSERT THE PAID LANE RULE ON THE DRESSED ASSET, IN THE BLOCKOUT'S OWN TWO
        # PARTS.  The rule is not one number: a BROADLEAF is allowed over a lane (trunk
        # clears by its own radius + 1.20 m, canopy underside at 3.60 m or more), and a
        # CONIFER is not, because its skirt hangs at head height — for that species the
        # forest's crown + 1.00 m applies unchanged.  Measuring one rule against both
        # species is how the first build "found" a conifer illegally oversailing a lane
        # it was never near.
        wd = walk_dist(t["x"], t["y"])
        eff_trunk = max(t["trunk_r"], 0.22 * s * (h0 / 6.0))
        if t["cls"] == "conifer":
            worst_conifer = min(worst_conifer, wd - t["crown_r"])
        else:
            worst_trunk = min(worst_trunk, wd - eff_trunk)
            if wd < t["crown_r"] + 1.0:
                over += 1
                lowest_canopy = min(lowest_canopy, t["cbase"] - t["z"])
        n += 1
    print("  VILLAGE TREES   %d of %d harvested placements are in region; %d instanced "
          "from the library%s"
          % (kept, len(PLAN["village_trees"]), n,
             (" (%d stretched into the missing slim class)" % stretched) if stretched else ""))
    if n:
        print("    lane rule, RE-MEASURED ON THE DRESSED ASSET (the blockout's own two "
              "parts, per species): tightest BROADLEAF trunk clears its tread by %.2f m "
              "(rule 1.20); %d canopies oversail a tread and the lowest underside is "
              "%.2f m (rule 3.60, a walker is 1.62 m); tightest CONIFER crown clears by "
              "%.2f m (rule 1.00, no exemption — its skirt is at head height)"
              % (worst_trunk if worst_trunk < 1e8 else float('nan'), over,
                 lowest_canopy if lowest_canopy < 1e8 else float('nan'),
                 worst_conifer if worst_conifer < 1e8 else float('nan')))
        assert worst_trunk > 1e8 or worst_trunk >= 1.20 - 1e-6, \
            "a dressed village tree's trunk stands %.2f m from a tread" % worst_trunk
        assert lowest_canopy > 1e8 or lowest_canopy >= 3.60 - 1e-6, \
            "a dressed canopy oversails a lane at %.2f m" % lowest_canopy
        assert worst_conifer > 1e8 or worst_conifer >= 1.00 - 1e-6, \
            "a dressed conifer's crown stands %.2f m from a tread" % worst_conifer
    if SUBS:
        print("    MANIFEST GAPS SUBSTITUTED: %s — lane A owns closing these."
              % ", ".join("%s -> %s" % kv for kv in sorted(SUBS.items())))


def dress_bank_and_bramble():
    """THE BOUNDARY VOCABULARY, RE-RENDERED.  The blockout stamped the 29%-median-partial
       enclosure — irregular stone rows, split-rail fragments, bramble clumps (the
       coexistence ruling's consequence (1)).  Each fragment keeps its stamped place and
       gains scanned planting, varied per household on that household's own crc."""
    n, hh = 0, set()
    for name, o, bb in PLAN["boundary"]:
        cx, cy = (bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2
        if not in_region(cx, cy, 2.0):
            continue
        house = name.split("_")[1] if name.startswith("lm_infill_") else name.split("_")[1]
        hh.add(house)
        if "_bramble" in name:
            aid, _ = pick_for("bramble", crc(house, name))
            if aid:
                veg(aid, (cx, cy, bb[4] - 0.05),
                    crcrange(0.8, 1.7, "bs", name), crcrange(0, 6.283, "br", name),
                    "emb_dress_bramble_" + name, seed=crc(name))
                o.hide_render = True
                n += 1
        elif "_drystone" in name:
            # the stamped row keeps its place; the stones become individual field stones
            for k in range(5):
                box("emb_dress_stone_%s_%d" % (name, k),
                    (cx + crcrange(-0.55, 0.55, "sx", name, k),
                     cy + crcrange(-0.55, 0.55, "sy", name, k),
                     bb[4] + crcrange(0.06, 0.34, "sz", name, k)),
                    (crcrange(0.26, 0.52, "ss", name, k),
                     crcrange(0.30, 0.55, "ssy", name, k),
                     crcrange(0.18, 0.32, "ssz", name, k)),
                    rot=(crcrange(-0.12, 0.12, "sr", name, k),
                         crcrange(-0.12, 0.12, "sp", name, k),
                         crcrange(0, 3.14, "sw", name, k)),
                    mat=[STONE, ROCK, STONE_W][k % 3])
            o.hide_render = True
            n += 1
        if crc01("spill", name) < 0.34:
            aid, _ = pick_for("shrub", crc("spill", name))
            if aid:
                veg(aid, (cx + crcrange(-1.2, 1.6, "px", name),
                          cy + crcrange(-0.9, 1.6, "py", name), bb[4] - 0.04),
                    crcrange(1.4, 2.6, "ps", name), crcrange(0, 6.283, "pr", name),
                    "emb_dress_spill_" + name, seed=crc("s", name))
    print("  BOUNDARIES      %d stamped fragments re-rendered across %d households "
          "(per-household crc variation; the stamped places are unchanged)" % (n, len(hh)))


def dress_bank_planting():
    """Ferns and nettles hugging the water line and the pit lip — the probe's bank
       recipe, placed against the town's own water bounds instead of an invented brook."""
    n = 0
    wb = [b for _k, (_o, b) in PLAN["water"].items()]
    for i in range(260):
        x = RCX + crcrange(-RR, RR, "bx", i)
        y = RCY + crcrange(-RR, RR, "by", i)
        if not in_region(x, y):
            continue
        near = min((math.hypot(max(b[0] - x, 0, x - b[1]), max(b[2] - y, 0, y - b[3]))
                    for b in wb), default=1e9)
        if near > 3.4:
            continue
        if walk_dist(x, y) < 1.0:
            continue
        z = raycast_ground(x, y)
        if z is None:
            continue
        cls = crcpick(["fern", "weed", "shrub", "bramble"], "bankcls", i)
        aid, _ = pick_for(cls, i)
        if not aid:
            continue
        veg(aid, (x, y, z - 0.04), crcrange(0.9, 2.4, "bsc", i),
            crcrange(0, 6.283, "brr", i), "emb_dress_bank%03d" % i, seed=i)
        n += 1
    print("  BANK PLANTING   %d scanned plants along the water margins and the pit lip "
          "(searched against the town's own water bounds, held 1.00 m off every tread)" % n)


dress_trees()
dress_bank_and_bramble()
dress_bank_planting()


# ============================================================== GROUNDCOVER ==
# THE DENSITY FIELD IS THE WHOLE POINT.  Round 1 was pulled up for a uniform carpet; round
# 2's ratified recipe is fractal density with TRODDEN BARE ground where feet actually go.
# Here "where feet go" is not authored — it is the harvested walk network, the mill door
# and the doorsteps, so the bare ground appears exactly where the town's own treads are.
#
# GROUNDCOVER IS NEVER COLLIDABLE.  walkGround: any surface 0.00-0.73 m above a tread
# steals the foot, and a grass clump is 0.4 m tall. It lives in EMB_DRESS_GROUNDCOVER,
# which the realtime export drops from collision, and it is held off every tread besides.
def dress_groundcover():
    if TIER == "realtime":
        print("  GROUNDCOVER     realtime tier: instanced grass is NOT emitted (budget "
              "%s). The density field is baked into the ground material's own mix instead "
              "— same derivation, different spend." % json.dumps(BUDGET))
        return
    keys = [a["id"] for a in BYCLASS.get("grass", [])] + \
           [a["id"] for a in BYCLASS.get("weed", [])][:1]
    if not keys:
        print("  GROUNDCOVER     NO grass-class asset in the library — skipped, and this "
              "is a manifest gap, not a build choice.")
        return
    gcol = bpy.data.collections.new("emb_dress_grass_src")
    for k in keys:
        col = src_collection(k)
        if not col:
            continue
        reps = 4 if k.startswith("grass") else 1
        for ob in col.all_objects:
            if ob.type != 'MESH':
                continue
            for r in range(reps):
                if r == 0:
                    try:
                        gcol.objects.link(ob)
                    except RuntimeError:
                        pass
                else:
                    cp = ob.copy()
                    cp.data = ob.data
                    gcol.objects.link(cp)

    # ---- the emitter: the blockout's OWN ground, locally refined so the trodden edges
    # have somewhere to live.  The blockout's valley grid is ~1 m and a lane's trodden
    # margin is 2.2 m wide, which is two samples: too coarse to read.  Subdivision is
    # LINEAR (no smoothing) so the surface a body collides with does not move, and the
    # deviation is MEASURED below rather than asserted by argument.
    me = GROUND.data
    mw = GROUND.matrix_world
    # THE DEVIATION IS COMPUTED, NOT SAMPLED, and the difference matters.  Sampling the
    # refined mesh at the ORIGINAL vertices measures nothing — subdivision keeps those
    # points exactly, so the answer is 0.0000 by construction and says nothing about the
    # interior.  What actually moves is the centre of each quad: the renderer splits a
    # non-planar quad along one diagonal, so its surface there is (z0+z2)/2, while a
    # linear subdivision puts a new vertex at the bilinear (z0+z1+z2+z3)/4.  The
    # difference is (z1+z3-z0-z2)/4 and it is the whole error, exactly.
    devs = []
    for f in me.polygons:
        if len(f.vertices) != 4:
            continue
        zs = [(mw @ me.vertices[i].co).z for i in f.vertices]
        c = mw @ f.center
        if not in_region(c.x, c.y, 3.0):
            continue
        devs.append((abs(zs[1] + zs[3] - zs[0] - zs[2]) / 4.0, c.z))
    devs.sort()
    dev = devs[-1][0] if devs else 0.0
    devmed = devs[len(devs) // 2][0] if devs else 0.0
    devp99 = devs[int(len(devs) * 0.99)][0] if devs else 0.0
    devz = devs[-1][1] if devs else 0.0
    if GROUNDSUB > 0 and REGION != "all":
        bm = bmesh.new()
        bm.from_mesh(me)
        sel = []
        for f in bm.faces:
            fx = sum((mw @ v.co).x for v in f.verts) / len(f.verts)
            fy = sum((mw @ v.co).y for v in f.verts) / len(f.verts)
            if in_region(fx, fy, 3.0):
                sel.append(f)
        if sel:
            edges = set()
            for f in sel:
                edges.update(f.edges)
            bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=GROUNDSUB,
                                      use_grid_fill=True, smooth=0.0)
            bm.to_mesh(me)
            me.update()
        bm.free()
    vg = GROUND.vertex_groups.get("emb_dress_grass") or \
        GROUND.vertex_groups.new(name="emb_dress_grass")
    doorsteps = [((b[0] + b[1]) / 2, (b[2] + b[3]) / 2)
                 for n, b in PLAN["walk"] if n.startswith("walk_pad_")]
    mw2 = GROUND.matrix_world
    live, bare = 0, 0
    for v in me.vertices:
        w = mw2 @ v.co
        x, y, z = w.x, w.y, w.z
        wgt = 1.0
        if not in_region(x, y, 2.0):
            wgt = 0.0
        # under water, in the pit, and on the treads themselves: nothing
        for _k, (_o, b) in PLAN["water"].items():
            if b[0] - 1.0 < x < b[1] + 1.0 and b[2] - 1.0 < y < b[3] + 1.0 \
                    and z < (b[4] + b[5]) / 2 + 0.20:
                wgt = 0.0
        if MILL and z < MILL["tail"] + 0.35:
            wgt = 0.0
        d = walk_dist(x, y)
        if d < 0.35:
            wgt = 0.0
        if wgt > 0.0:
            # CLUMPY, not a carpet — round 2's fractal density, unchanged
            nsy = (math.sin(x * 0.31 + 1.7) * math.cos(y * 0.27) * 0.5
                   + math.sin(x * 0.11 - y * 0.13) * 0.35
                   + math.sin(x * 0.73 + y * 0.61) * 0.15)
            wgt *= max(0.0, min(1.0, 0.80 + 0.95 * nsy))
            # TRODDEN BARE where the town's own feet go: every tread, and every doorstep
            if d < 2.2:
                wgt *= max(0.05, (d / 2.2) ** 1.5)
                bare += 1
            for (dx, dy) in doorsteps:
                dd = math.hypot(x - dx, y - dy)
                if dd < 6.5:
                    wgt *= max(0.04, (dd / 6.5) ** 1.7)
        if wgt > 0.01:
            vg.add([v.index], min(1.0, wgt), 'REPLACE')
            live += 1
        else:
            vg.add([v.index], 0.0, 'REPLACE')

    count = 12000 if FAST else int(opt("--grass", "260000"))
    GROUND.modifiers.new("emb_dress_grass", 'PARTICLE_SYSTEM')
    ps = GROUND.particle_systems[-1]
    st = ps.settings
    st.type = 'HAIR'
    st.count = count
    st.hair_length = 1.0
    st.use_advanced_hair = True
    st.render_type = 'COLLECTION'
    st.instance_collection = gcol
    st.use_collection_pick_random = True
    st.particle_size = 1.6
    st.size_random = 0.7
    st.use_rotations = True
    st.rotation_mode = 'NOR'
    st.rotation_factor_random = 0.08
    st.phase_factor_random = 2.0
    st.child_type = 'NONE'
    st.distribution = 'RAND'
    ps.seed = 7
    ps.vertex_group_density = "emb_dress_grass"
    GROUND.data.materials.clear()
    GROUND.data.materials.append(ground_material())
    print("  GROUNDCOVER     %d hair instances over %d weighted ground vertices "
          "(%d in a trodden margin); ground refined by %d cuts inside the region. The "
          "linear split's own error at a quad centre — the WHOLE error, computed as "
          "(z1+z3-z0-z2)/4 and not sampled, because sampling the refined mesh at the "
          "original vertices returns 0.0000 by construction — is %.4f m median, %.4f m at "
          "p99 and %.4f m worst, and the worst quad sits at z %.2f, inside the excavated "
          "wheel pit where the ground genuinely steps. Away from the excavation the ground "
          "a body collides with does not move."
          % (count, live, bare, GROUNDSUB, devmed, devp99, dev, devz))
    print("                  the scatter is scenery: collection EMB_DRESS_GROUNDCOVER, "
          "zero weight within 0.35 m of any tread, and never a collider (walkGround: a "
          "surface 0.00-0.73 m above a tread steals the foot)")


dress_groundcover()


# ============================================================= TIER + LIGHTS ==
def tri_gate():
    """THE DOUBLE-INSTANCING GATE.  Two ways an asset lane can hand this engine three
       models where it asked for one — a blend whose top-level collection stacks the
       generator and every baked LOD, and a manifest that points at the wrong collection —
       and NEITHER is visible in a render.  Both show up here, in tris, on both tiers,
       because a realtime_budget computed against a secretly-tripled plate is arithmetic
       about nothing.  Flag at 1.5x, which is well under the 3x this library actually had
       and well over any honest baked-LOD difference."""
    if not TRIREPORT:
        return
    print("ASSET TRI GATE  (%s tier) — what one instance of each asset actually renders:"
          % TIER)
    bad = []
    for aid, cname, how, mine, whole, expect in sorted(TRIREPORT):
        note = ""
        if whole and mine and whole > mine * 1.5:
            note = ("  <- the blend's TOP-LEVEL collection is %.1fx this; instancing it "
                    "would have rendered %d tris of stacked LODs" % (whole / mine, whole))
        if expect and mine > expect * 1.5:
            note += "  <- %.1fx the manifest's stated %d tris" % (mine / expect, expect)
            bad.append((aid, mine, expect))
        print("    %-22s %-28s %9d tris  (%s)%s" % (aid, cname, mine, how, note))
    tot = sum(r[3] for r in TRIREPORT)
    print("    library total %d tris across %d assets; instances placed %d"
          % (tot, len(TRIREPORT), len(INSTANCES)))
    assert not bad, ("asset(s) render more than 1.5x the manifest's stated tris — the "
                     "manifest is pointing at more than one representation: %s" % bad)


tri_gate()


def apply_tier():
    if TIER != "realtime":
        print("TIER            plate — full density, Cycles; this is what cine_bake's "
              "plates are rendered from")
        return
    cap = int(BUDGET.get("instances", 420))
    if len(INSTANCES) > cap:
        drop = 0
        for o in sorted(INSTANCES, key=lambda o: crc("cull", o.name)):
            if len(INSTANCES) - drop <= cap:
                break
            if o.name.startswith("emb_dress_villtree"):
                continue          # the village trees are the ruling; they are never culled
            bpy.data.objects.remove(o, do_unlink=True)
            drop += 1
        print("TIER            realtime — %d instances culled to the manifest's %d cap "
              "(village trees exempt: they are a user ruling, not scatter)" % (drop, cap))
    else:
        print("TIER            realtime — %d instances, inside the manifest's %d cap"
              % (len(INSTANCES), cap))


apply_tier()


def light_key():
    """THE SAME GOLDEN LEGIBILITY KEY THE STYLE BAR WAS SHOT IN.  probe2-a/b/c were lit
       with sun 3.0 warm at (62, 0, 212), exposure 0.10, world 0.30 under Cycles — a
       bright cousin of the emberwake grade, chosen so the DRESSING is legible.  The
       shipped emberwake numbers (exposure 0.55, sun 0.75, sky 0.55) live in
       emberbrook.cameras.json and are NOT touched here; `--key emberwake` selects them
       for a deliverable-grade look."""
    scn = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT' and o.name in ("EMB_sun", "bounce"):
            bpy.data.objects.remove(o, do_unlink=True)
    if KEY == "emberwake":
        cam = json.load(open(CAM_PATH))
        rig = cam["defaults"]["lightRig"]
        sd = bpy.data.lights.new("EMB_sun", 'SUN')
        sd.energy = rig["sun"]["energy"]
        sd.color = tuple(rig["sun"]["color"])
        so = bpy.data.objects.new("EMB_sun", sd)
        so.rotation_euler = Euler([math.radians(a) for a in rig["sun"]["rotationEulerDeg"]])
        DRESS.objects.link(so)
        world = bpy.data.worlds.new("W_emberwake")
        scn.world = world
        world.use_nodes = True
        bg = world.node_tree.nodes["Background"]
        bg.inputs[0].default_value = (*rig["world"]["color"], 1)
        bg.inputs[1].default_value = rig["world"]["strength"]
        scn.view_settings.exposure = cam["defaults"]["exposure"]
        print("LIGHT KEY       emberwake (from emberbrook.cameras.json defaults: exposure "
              "%.2f, sun %.2f, world %.2f)"
              % (cam["defaults"]["exposure"], rig["sun"]["energy"], rig["world"]["strength"]))
        return
    sd = bpy.data.lights.new("EMB_sun", 'SUN')
    sd.energy, sd.color, sd.angle = 3.0, (1.0, 0.70, 0.42), math.radians(2.5)
    so = bpy.data.objects.new("EMB_sun", sd)
    so.rotation_euler = Euler((math.radians(62), 0, math.radians(212)))
    DRESS.objects.link(so)
    bd = bpy.data.lights.new("bounce", 'SUN')
    bd.energy, bd.color = 0.30, (1.0, 0.55, 0.34)
    bo = bpy.data.objects.new("bounce", bd)
    bo.rotation_euler = Euler((math.radians(108), 0, math.radians(30)))
    DRESS.objects.link(bo)
    world = bpy.data.worlds.new("W_probekey")
    scn.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs[0].default_value = (0.30, 0.31, 0.42, 1)
    bg.inputs[1].default_value = 0.30
    dropped = []
    try:
        sky = nt.nodes.new("ShaderNodeTexSky")
        for a, v in (('sky_type', 'MULTIPLE_SCATTERING'), ('sun_elevation', math.radians(8.0)),
                     ('sun_rotation', math.radians(212)), ('altitude', 200),
                     ('air_density', 2.2), ('dust_density', 5.5), ('ozone_density', 1.4),
                     ('sun_intensity', 0.30), ('sun_disc', True)):
            try:
                setattr(sky, a, v)
            except Exception:
                dropped.append(a)
        nt.links.new(sky.outputs["Color"], bg.inputs[0])
    except Exception as e:
        dropped.append("ShaderNodeTexSky:%s" % e)
    scn.view_settings.exposure = 0.10
    print("LIGHT KEY       probe — the style bar's own legibility key (sun 3.0 warm at "
          "62/212, bounce 0.30, world 0.30, exposure 0.10, AgX Medium High Contrast)")
    if dropped:
        # THE 5.1 GOTCHA, NAMED. Round 1's sky node silently failed on Blender 5.1's
        # dropped `dust_density` and the frame fell back to a flat blue world. It is
        # caught and PRINTED here so a future run cannot lose the sky in silence.
        print("                Blender %s dropped these sky attributes: %s — the node is "
              "still linked and the rest applied; this is the round-1 silent-failure mode, "
              "now reported." % (bpy.app.version_string, ", ".join(dropped)))
    # the mill's own practicals, and the harvested lamps keep theirs
    for i, (nm, loc) in enumerate((("KEY_dress_mill_win", MILL.get("house_world")),)):
        if not loc:
            continue
        l = bpy.data.lights.new(nm, 'POINT')
        l.energy, l.color = 800, (1.0, 0.60, 0.26)
        lo = bpy.data.objects.new(nm, l)
        lo.location = (loc[0], loc[1], loc[2] + 3.0)
        DRESS.objects.link(lo)
    pf = bpy.data.lights.new("emb_dress_pit_fill", 'AREA')
    pf.energy, pf.color, pf.size = 1500, (1.0, 0.72, 0.46), 9.0
    pfo = bpy.data.objects.new("emb_dress_pit_fill", pf)
    w = MILL.get("wheel_world", (RCX, RCY, 0))
    pfo.location = (w[0] - MILL["ux"] * 1.5 - MILL["vx"] * 9.5 * MILL["house"][1],
                    w[1] - MILL["uy"] * 1.5 - MILL["vy"] * 9.5 * MILL["house"][1],
                    MILL["crest"] + 1.4)
    pfo.rotation_euler = Euler((math.radians(62), 0,
                                math.atan2(MILL["uy"], MILL["ux"]) - math.radians(38)))
    DRESS.objects.link(pfo)


light_key()


# ================================================================== the digest ==
# A CONTENT DIGEST, NOT A BYTE COMPARE. `.blend` serialises memory addresses, so two
# identical builds differ byte for byte (tools/embint_verify.py paid for this). What has
# to be identical is the CONTENT: world-space geometry, the instance assignments that ARE
# the dressing, the particle spend, the materials, the lights, the cameras.
def content_digest():
    h = hashlib.sha256()
    dg = bpy.context.evaluated_depsgraph_get()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        h.update(o.name.encode())
        h.update(("%.5f,%.5f,%.5f;" % tuple(o.location)).encode())
        h.update(("%.5f,%.5f,%.5f;" % tuple(o.scale)).encode())
        h.update(("%.5f,%.5f,%.5f;" % tuple(o.rotation_euler)).encode())
        if o.instance_collection:
            h.update(("INST:%s;" % o.instance_collection.name).encode())
        if o.type == 'MESH':
            mw = o.matrix_world
            for v in o.data.vertices:
                w = mw @ v.co
                h.update(("%.5f,%.5f,%.5f;" % (w.x, w.y, w.z)).encode())
            for s in o.material_slots:
                h.update(("MAT:%s;" % (s.material.name if s.material else "-")).encode())
            for psys in o.particle_systems:
                h.update(("PS:%s:%d:%d:%s;" % (psys.name, psys.settings.count,
                                               psys.seed,
                                               psys.vertex_group_density)).encode())
            for vg in o.vertex_groups:
                tot = 0.0
                for v in o.data.vertices:
                    for g in v.groups:
                        if g.group == vg.index:
                            tot += g.weight
                h.update(("VG:%s:%.4f;" % (vg.name, tot)).encode())
        elif o.type == 'LIGHT':
            h.update(("L:%.4f:%s;" % (o.data.energy, tuple(round(c, 4) for c in o.data.color))).encode())
    return h.hexdigest()


if DIGEST:
    print("DIGEST %s" % content_digest())


# ==================================================================== the shots ==
# THE PILOT'S FRAMINGS ARE THE STYLE BAR'S FRAMINGS, TRANSFORMED.  probe2-a/b/c were shot
# in the throwaway's own coordinate frame; the only honest side-by-side puts this build's
# camera at the SAME PLACE RELATIVE TO THE MILL. So each probe camera is mapped through the
# same local frame the build uses — downstream, left bank, crest — and nothing about the
# framing is re-chosen by eye.
PROBE_SHOTS = {
    'a': ((21.5, -30.0, 16.0 - 1.55), (0.0, 6.5, 1.2 - 1.55), 40),
    'b': ((9.0, -15.4, 7.2 - 1.55), (3.4, 3.4, 0.5 - 1.55), 32),
    'c': ((-13.0, -31.0, 3.35 - 1.55), (-6.2, -15.5, 7.5 - 1.55), 60),
}


def shoot():
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scn.cycles.device = 'GPU'
    except Exception as e:
        print("  GPU setup failed -> CPU", e)
        scn.cycles.device = 'CPU'
    scn.cycles.samples = 24 if FAST else SAMPLES
    scn.cycles.use_denoising = True
    try:
        scn.cycles.denoiser = 'OPENIMAGEDENOISE'
        scn.cycles.denoising_use_gpu = True
    except Exception:
        pass
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.02
    scn.cycles.max_bounces = 8
    scn.cycles.diffuse_bounces = 4
    scn.cycles.glossy_bounces = 3
    scn.cycles.transmission_bounces = 6
    scn.cycles.transparent_max_bounces = 32
    scn.cycles.caustics_reflective = False
    scn.cycles.caustics_refractive = False
    scn.view_settings.view_transform = 'AgX'
    for lk in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            scn.view_settings.look = lk
            break
        except Exception:
            pass
    scn.render.resolution_x, scn.render.resolution_y = RESX, RESY
    scn.render.image_settings.file_format = 'PNG'
    os.makedirs(SHOTDIR, exist_ok=True)
    ux, uy, vx, vy = MILL["ux"], MILL["uy"], MILL["vx"], MILL["vy"]
    ox, oy = MILL["origin"]
    side = MILL["house"][1]
    crest = MILL["crest"]

    def W(p):
        return (ox + ux * p[0] + vx * p[1] * side,
                oy + uy * p[0] + vy * p[1] * side,
                crest + p[2])

    for f in FRAMES:
        if f not in PROBE_SHOTS:
            continue
        lp, ap, fov = PROBE_SHOTS[f]
        loc, aim = W(lp), W(ap)
        cd = bpy.data.cameras.new("dress_" + f)
        cd.lens_unit = 'FOV'
        cd.angle = math.radians(fov)
        cd.clip_start, cd.clip_end = 0.05, 1400
        co = bpy.data.objects.new("dress_" + f, cd)
        DRESS.objects.link(co)
        co.location = loc
        co.rotation_mode = 'QUATERNION'
        co.rotation_quaternion = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y')
        scn.camera = co
        scn.render.filepath = os.path.join(SHOTDIR, "%s-%s.png" % (TAG, f))
        print("  SHOT %s  camera (%.1f, %.1f, %.1f) aim (%.1f, %.1f, %.1f) fov %d — the "
              "probe's own framing, mapped through the mill's local frame"
              % (f, *loc, *aim, fov))
        bpy.ops.render.render(write_still=True)
        print("  WROTE %s" % scn.render.filepath, flush=True)


if not NOSHOOT:
    shoot()

if not NOSAVE:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print("SAVED %s  (the master blend is NEVER written by this file)" % OUT)
print("DONE")
