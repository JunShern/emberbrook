"""ls_reorigin.py — re-derive ONE map edge's walk records into the master.

    Blender -b tools/blends/dellhollow-master.blend -P tools/ls_reorigin.py \
        --python-exit-code 1 -- [save] [revert]

WHY THIS TOOL EXISTS. CLAUDE.md's doctrine is "a conflict fix is a landmark move or a
lane waypoint — ONE LINE OF MAP, ONE COMMAND TO RE-DERIVE. Never re-cut floors in a
district builder." The one line of map existed (c046f51). The one command did not.

`town_blockout.py` raises the WHOLE town from the map into `dellhollow-town.blend` and
WIPES the scene doing it; the master carries a night's district art on top of those
ribbons and cannot be regenerated that way. Every district builder in this repo is
therefore ADDITIVE and reads the walk network as given. So when the map's own walk
records change there has been nowhere for the change to land — which is why the loop
stairs' defect survived a rebuild, a re-aim, a bake and four gates.

This is that missing command, and it deliberately does NOT reimplement anything:
`town_blockout.py` regenerates the blockout from the stamped map, and this appends the
named records OUT of that blend into the master. The new ribbons are therefore
bit-identical to what a full blockout would have produced — there is no second
generator to drift.

WHAT IT MOVES, and nothing else:
  IN   walk_e_loop-landing__quay-deck_* (9 treads), bar_e_loop-landing__quay-deck_* (2)
  OUT  every *shelf-homes__quay-deck* record (14 treads, 2 landings, 4 blockout rails)
  NOT  lm_loop-landing_{postL,postR,lintel} — town_blockout gives a `portal` landmark
       posts-and-a-lintel placeholder massing. The master carries ZERO lm_ objects
       (measured: 0) because every one of them has been replaced by real art. Importing
       a stone gateway onto a timber stair landing would be a blockout artefact shipped
       as art, which is the `bar_`-rails-rendering mistake the crossing already taught.
  NOT  walk_pad_loop-landing — and this one was IMPORTED FIRST AND THEN MEASURED OUT,
       so the reasoning is recorded rather than assumed. town_blockout gives every
       structure/prop/portal landmark a 2.60 m threshold pad (its line 154), and all
       five of Dellhollow's other portals carry one. This one is REDUNDANT and HARMFUL:
       redundant because the fork platform already exists as the market flight's own
       `walk_e_shelf-homes__market-stalls_landing` (2.0 x 2.0 m at the same height, the
       mesh the new edge is re-origined onto), and harmful because the pad spans t
       0.348..0.586 of that market edge and swallowed the whole of its seam's slide
       window — seam_test went RED with "every seam position in t=[0.500,0.743]
       overlaps another path (walk_pad_loop-landing)", which seam-canon §5 ranks a
       FAILURE, not a warning: a player stepping onto the landing to take the QUAY
       branch would have been cut to quay-west for it. Authoring a @t split to dodge it
       was tried at six positions (0.82/0.84/0.86/0.88/0.90/0.93/0.97) and the window is
       squeezed from both ends — below t~0.73 the arrival clears only 0.47 m against a
       0.50 m floor, above t~0.78 the band lands on `walk_lm_quay-deck`. Empty
       intersection, exactly §5.1's arithmetic. A pad that buys no walkable ground and
       costs a seam is not worth an exception in the seam layer.
       THE PRICE, stated: the master no longer matches a full blockout for this record.
       That is two documented exceptions (this and lm_), and if a third appears the
       right answer is a rule in town_blockout — "no threshold pad where a landing mesh
       already covers the landmark" — not a third line in this tool.

IDEMPOTENT AND REVERTIBLE, on ls_build.py's own pattern: the outgoing objects are
snapshotted as LSR_SRC_* with a fake user before deletion, so `-- revert` puts them back
and a second run is a no-op. Peer settings (collection, hide_render, hide_viewport,
material) are COPIED FROM A SIBLING RIBBON rather than assumed, so the new records are
indistinguishable in kind from every other walk mesh in the master.

The stair art (ls_treads/ls_rail/ls_frame) is built to the OLD ribbons and is NOT
touched here — re-run tools/ls_build.py afterwards. This tool moves the walk network;
that one dresses it.
"""
import bpy, json, sys, os

ROOT = "/Users/junshernchan/projects/multiplayer-rpg/"
MASTER = ROOT + "tools/blends/dellhollow-master.blend"
BLOCKOUT = ROOT + "tools/blends/dellhollow-town.blend"
MAP = json.load(open(ROOT + "public/townmap/dellhollow.map.json"))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

NEW_EDGE = "loop-landing__quay-deck"
OLD_EDGE = "shelf-homes__quay-deck"
NEW_PAD = "walk_pad_loop-landing"
SNAP = "LSR_SRC_"

# ---- the map is the authority: refuse to run against a map that disagrees ---------
edge_ids = {"%s__%s" % (e["from"], e["to"]) for e in MAP["edges"]}
lm_ids = {l["id"] for l in MAP["landmarks"]}
assert NEW_EDGE in edge_ids, "map has no edge %s — stamp it first" % NEW_EDGE
assert OLD_EDGE not in edge_ids, "map STILL has %s — this tool would orphan it" % OLD_EDGE
assert "loop-landing" in lm_ids, "map has no loop-landing landmark"
print("MAP OK — %s present, %s withdrawn" % (NEW_EDGE, OLD_EDGE))


def snapshot_name(n):
    return SNAP + n


def do_revert():
    """RESTORE MEANS RE-LINK, NOT JUST RENAME — learned the hard way on the first run.

    The first version renamed the snapshots back and cleared `use_fake_user`, but never
    re-linked them to a collection. An object in no collection with no fake user has
    ZERO users, so Blender garbage-collected all twenty on the next save: the tool
    reported a successful revert and then silently destroyed exactly the thing it exists
    to protect. The withdraw step now records each object's collections on the object
    itself, and nothing loses its fake user until it is back in one.
    """
    back = 0
    for o in list(bpy.data.objects):
        if not o.name.startswith(SNAP):
            continue
        o.name = o.name[len(SNAP):]
        names = list(o.get("lsr_colls", []))
        linked = False
        for cn in names:
            coll = bpy.data.collections.get(cn)
            if coll and o.name not in coll.objects:
                coll.objects.link(o); linked = True
        if not linked:                       # its collection is gone: park it in the scene
            bpy.context.scene.collection.objects.link(o)
        if "lsr_colls" in o:
            del o["lsr_colls"]
        o.use_fake_user = False              # safe ONLY now that it has a real user
        back += 1
    dead = [o for o in bpy.data.objects if NEW_EDGE in o.name or o.name == NEW_PAD]
    for o in dead:
        bpy.data.objects.remove(o, do_unlink=True)
    print("REVERTED — %d snapshots restored AND re-linked, %d re-derived objects removed"
          % (back, len(dead)))
    if back == 0:
        print("  NOTE: no snapshots found. If a previous run's snapshots were lost, the")
        print("  master is git-tracked: `git checkout tools/blends/dellhollow-master.blend`.")
    return back, len(dead)


if REVERT:
    do_revert()
    if SAVE:
        bpy.ops.wm.save_as_mainfile(filepath=MASTER)
        print("SAVED", MASTER)
    sys.exit(0)

# ---- 0. a sibling to copy peer settings from -------------------------------------
sib = bpy.data.objects.get("walk_e_shelf-homes__market-stalls_l0_t00")
assert sib is not None, "no sibling ribbon to copy peer settings from"
sib_colls = [c.name for c in sib.users_collection]
sib_mats = [m.name if m else None for m in sib.data.materials]
print("PEER SETTINGS from %s: collections=%s hide_render=%s hide_viewport=%s mats=%s"
      % (sib.name, sib_colls, sib.hide_render, sib.hide_viewport, sib_mats))
bar_sib = bpy.data.objects.get("bar_e_shelf-homes__market-stalls_l0_railA")
bar_colls = [c.name for c in bar_sib.users_collection] if bar_sib else sib_colls
bar_hr = bar_sib.hide_render if bar_sib else True

# ---- 1. is this already done? (idempotence) --------------------------------------
already = [o.name for o in bpy.data.objects if NEW_EDGE in o.name or o.name == NEW_PAD]
if already:
    print("ALREADY RE-ORIGINED — %d objects present; nothing to do." % len(already))
    sys.exit(0)

# ---- 2. append the new records out of the freshly-derived blockout ----------------
with bpy.data.libraries.load(BLOCKOUT, link=False) as (src, dst):
    want = [n for n in src.objects
            if (NEW_EDGE in n and (n.startswith("walk_e_") or n.startswith("bar_e_")))]
    # EXPLICITLY NOT lm_* — see the module docstring.
    dropped = sorted(n for n in src.objects if "loop-landing" in n and n not in want)
    # `dst.objects` is mutated IN PLACE by the loader (names -> Objects on block exit),
    # and it is the same list object as `want`. Keep the names separately.
    wanted_names = sorted(want)
    dst.objects = want
print("APPENDED %d records: %s" % (len(wanted_names), wanted_names))
print("DELIBERATELY LEFT IN THE BLOCKOUT: %s" % dropped)
assert wanted_names, "the blockout carries no %s records — re-run town_blockout.py" % NEW_EDGE

for o in dst.objects:
    if o is None:
        continue
    is_bar = o.name.startswith("bar_")
    for cn in (bar_colls if is_bar else sib_colls):
        coll = bpy.data.collections.get(cn) or bpy.context.scene.collection
        if o.name not in coll.objects:
            coll.objects.link(o)
    o.hide_render = bar_hr if is_bar else sib.hide_render
    o.hide_viewport = sib.hide_viewport
    if not is_bar and sib.data.materials:
        o.data.materials.clear()
        for mn in sib_mats:
            o.data.materials.append(bpy.data.materials.get(mn) if mn else None)

# ---- 3. snapshot + withdraw the old edge's records --------------------------------
old = [o for o in bpy.data.objects if OLD_EDGE in o.name and not o.name.startswith(SNAP)]
for o in old:
    o.name = snapshot_name(o.name)
    o["lsr_colls"] = [c.name for c in o.users_collection]   # so revert can re-LINK, not
    o.use_fake_user = True                                  # merely rename (see do_revert)
    for c in list(o.users_collection):
        c.objects.unlink(o)
print("WITHDREW %d old records (snapshotted %s*, fake-user, revertible)" % (len(old), SNAP))

# ---- 3b. A HANDRAIL MAY NOT FENCE OFF A WAY ON -----------------------------------
# Found by walking the finished stair in the shipped game with the body box on, which is
# the only instrument that could have found it: every offline probe said the new flight
# was perfect, and the live walker stopped dead after two steps with 0.30 m of clear lane
# against a 0.60 m body.
#
# The cause is a straight consequence of re-origining an edge to leave MID-FLIGHT.
# `town_blockout` draws a `bar_` rail down each side of every stairs edge, and it draws
# it per-edge, knowing nothing about anything else that leaves. Before the stamp nothing
# left the market flight's south side here, so a continuous rail was correct. Now the
# quay branch leaves through it, and `bar_e_shelf-homes__market-stalls_l0_railB` runs
# straight across the new flight's top tread — with `ls_build` then dressing that same
# line in visible timber, because it builds rails ON the blockout lines.
#
# bar_ meshes are invisible but they are NOT non-solid: play3d.html's `noStand` list is
# water_/lm_/veg_ only, so a bar_ is in `collide` and blocks the body exactly like a
# wall. An invisible wall across a staircase is the worst version of this defect.
#
# So the rail gets a GAP, not a deletion — the rest of it is still what stops a player
# walking off the market flight's south side. Faces are cut only inside the new flight's
# own first-tread footprint (grown by a body radius) and only up to head height above it.
# The whole object is snapshotted first, so this is revertible like everything else here.
import bmesh
from mathutils import Vector as _V

# THE DEPSGRAPH AGAIN — a just-appended object's matrix_world is identity until the view
# layer is updated, so the first version of this block measured the new tread as a UNIT
# CUBE at the origin, matched no rail, and printed "NO RAIL CROSSED THE FORK" while the
# rail was still standing across the stair. Same trap as the extent report in §4, one
# step earlier and with no assert to catch it. Update first, measure second.
bpy.context.view_layer.update()

BODY_R, BODY_H, STEP_UP = 0.30, 1.30, 0.63
head = bpy.data.objects.get("walk_e_%s_l0_t00" % NEW_EDGE)
gapped = []
if head is not None:
    hv = [head.matrix_world @ v.co for v in head.data.vertices]
    hx0, hx1 = min(v.x for v in hv) - BODY_R, max(v.x for v in hv) + BODY_R
    hy0, hy1 = min(v.y for v in hv) - BODY_R, max(v.y for v in hv) + BODY_R
    hz = max(v.z for v in hv)
    zlo, zhi = hz + STEP_UP * 0.5, hz + BODY_H + 0.6      # the body's own column
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or not o.name.startswith("bar_e_"):
            continue
        if NEW_EDGE in o.name:                            # the branch's own rails stay
            continue
        M = o.matrix_world
        doomed = []
        for p in o.data.polygons:
            c = M @ p.center
            if hx0 <= c.x <= hx1 and hy0 <= c.y <= hy1 and zlo <= c.z <= zhi:
                doomed.append(p.index)
        if not doomed:
            continue
        snap = o.copy(); snap.data = o.data.copy()
        snap.name = SNAP + o.name; snap.use_fake_user = True
        snap["lsr_colls"] = [c.name for c in o.users_collection]
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        kill = [f for f in bm.faces if f.index in set(doomed)]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        bm.to_mesh(o.data); bm.free(); o.data.update()
        gapped.append((o.name, len(doomed)))
if gapped:
    print("RAIL GAPS CUT so the fork is not fenced off (snapshotted %s*, revertible):" % SNAP)
    for n, k in gapped:
        print("   %-46s %d faces inside the fork's body column" % (n, k))
else:
    print("NO RAIL CROSSED THE FORK — nothing cut.")

# ---- 4. state the result in the terms the gate is written in ----------------------
from mathutils import Vector
# `bound_box` is depsgraph-derived and reads as a UNIT CUBE on a just-appended object
# until the view layer is updated. The first run of this tool printed -1..1 for all
# twelve records, which looks exactly like "the transforms did not come across" —
# so the extents below are measured from evaluated MESH VERTICES, not from bound_box,
# and the assert makes a silent unit-cube import impossible to ship.
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def ext(o):
    ev = o.evaluated_get(dg)
    vs = [o.matrix_world @ v.co for v in ev.data.vertices]
    return ([round(min(v[i] for v in vs), 2) for i in range(3)],
            [round(max(v[i] for v in vs), 2) for i in range(3)])
print("\nTHE NEW FLIGHT, as built:")
span_max = 0.0
for n in sorted(o.name for o in bpy.data.objects if NEW_EDGE in o.name or o.name == NEW_PAD):
    o = bpy.data.objects[n]
    lo, hi = ext(o)
    span_max = max(span_max, abs(lo[0]), abs(hi[0]))
    print("  %-46s x %6.2f..%6.2f  y %6.2f..%6.2f  z %6.2f..%6.2f"
          % (n, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
assert span_max > 10.0, ("appended records are sitting at the origin — the transforms "
                         "did not come across; do NOT save this master")

walks = len([o for o in bpy.data.objects if o.name.startswith("walk_")])
print("\nwalk_ meshes in the master: %d" % walks)
if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=MASTER)
    print("SAVED", MASTER)
else:
    print("DRY RUN — pass `-- save` to write the master.")
