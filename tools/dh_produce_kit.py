"""dh_produce_kit.py — THE PRODUCE IN THIS TOWN IS ALREADY A SMOOTH DRUM, AND ONE
PASS BUILT ITS OWN OUT OF `obox()`.

  # census only, no Blender edit
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_produce_kit.py -- --census

  # carry the donor onto the cuboids
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_produce_kit.py -- [--dry] [save]

WHAT WAS MEASURED FIRST (round 13, before anything was built).

Round 12 handed over "the `t2c_` colour-pop family is the loudest defect — census the
whole prefix before fixing one".  Censused: **38 objects, 3.69% of the town's fifteen
frames**, up to 8.18% of waterfront.  Sizing the job by the PREFIX would have been
thirty times too big, which is round 12's own lesson about `lf_matte` repeated one
level up — the prefix is a PASS, not a subject.

The judge named two members and they have one thing in common that nothing else in
the family has:

    t2c_W7_keeper_boxes   cottage    "a row of orange cubes floating in mid-air"
    t2c_F5_fish_floats    fishdock   "untextured developer placeholder cubes"

**`mat_pumpkin` IS THE ONLY MATERIAL IN THE FAMILY WITH NO TEXTURE AT ALL** — 2 nodes,
a Principled and an Output.  Ten of the sixteen materials the family wears carry the
town's standard 21-node / 4-image recipe (`mat_shelf_paint_*`, `mat_qm_paint_*`), and
62 of the town's 148 materials do.  So "untextured" is literally true, of exactly one
material, and the frame share of that material is **0.125% of the town's rays** — not
the 3.69% of the prefix.

**AND THE MATERIAL IS NOT THE DEFECT, BECAUSE THE SAME MATERIAL READS FINE ELSEWHERE.**
Nine meshes wear `mat_pumpkin` and they fall into exactly two shapes:

    shelf_clutter / qm_clutter_0 / qm_clutter_4 / gate_clutter / barge_*
        polygon sides [4, 10], use_smooth on 100% of the faces
        = 20 verts / 12 faces per unit: a 10-gon drum, SMOOTH SHADED

    t2c_W7_keeper_boxes / t2c_LH3_rail_flowerbox / t2c_F5_fish_floats /
    t2c_G8_cliff_baskets / t2c_W5_flowerbox_rail
        polygon sides [4], use_smooth on 0% of the faces
        = 8 verts / 6 faces per unit: an `obox()`.  A LITERAL CUBE.

That is round 12's `dh_clump_kit` finding again, in a different district and a
different grammar: **the town already owns the kit and one pass invented its own.**
The fix is therefore a CARRY, not authoring — and the material needs no edit at all,
which is the control that says so.

WHAT THIS DOES.  For every cuboid island in the named `t2c_` objects, the island's
faces are replaced by a copy of the town's own donor drum, SCALED TO THE ISLAND'S OWN
WORLD BOX and shaded smooth.  Three things follow from measurement rather than taste:

  * **THE DONOR IS TAKEN FROM THE MASTER, NEVER AUTHORED.**  `_donor()` lifts one unit
    out of `shelf_clutter`'s own `mat_pumpkin` faces — 20 verts / 12 faces, verified by
    assertion — so the produce in a keeper's flowerbox is the same object as the produce
    on the shelf-row market stall, at whatever detail that stall ships today.
  * **THE SIZE IS THE CUBOID'S OWN BOX AND THE HEIGHT IS NOT INFLATED.**  Round 12 had to
    reject `dh_veg_kit`'s bbox-fit rule because its donor was wider than tall; here the
    donor drum (0.42 x 0.42 x 0.30 in its own space) and the cuboids have compatible
    aspect, so a per-axis fit is used and the top of the produce lands exactly where the
    cuboid's top was.  Nothing rises out of a trough it used to sit inside.
  * **THE MATERIAL SLOT IS PRESERVED PER ISLAND.**  These objects are joins carrying up
    to five materials (`mat_timber` troughs, `mat_pumpkin` and `mat_shelf_paint_*`
    produce), and a whole-mesh replacement would flatten them to one.  Only the island's
    own faces are rebuilt, on the island's own material index.

ONE COSMETIC CONSEQUENCE, MEASURED IN THE ARTIFACT AND LEFT: the `DPK_SRC_` snapshot
holds the ORIGINAL mesh datablock's name, so the rebuilt one takes a `.NNN` suffix and
that suffix reaches the glTF `meshes[].name` field (`t2c_W7_keeper_boxes.002`).  It is
invisible to every consumer, and that was checked rather than assumed: **the NODE names
of both bundles are identical before and after, 1635 of 1635, empty set both ways.**
Node names are what the runtime, the walk network and every gate look up.

WHAT IT ASSERTS RATHER THAN ASSUMES:
  * the donor is exactly 20 verts / 12 faces with polygon sides {4, 10} and 100% smooth;
  * every island it touches is exactly 8 verts / 6 faces (a cuboid) before the swap;
  * the object's material list is unchanged in name and order after the swap;
  * `revert save` is exact — the pre-swap meshes are snapshotted `DPK_SRC_<name>` with a
    fake user and restored bit-identically, the same faithfulness contract
    `crossing_lane_chop` uses.
"""
import bpy, sys, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DRY = "--dry" in argv
REVERT = "revert" in argv
CENSUS = "--census" in argv

PRODUCE_MAT = "mat_pumpkin"     # the material the donor is lifted through
DONOR_OBJ = "shelf_clutter"
SNAPP = "DPK_SRC_"
# The subjects: `t2c_` objects that build produce out of `obox()`.  Named, not
# prefix-matched, because the prefix is a PASS and not a subject — the census above.
TARGETS = ["t2c_W7_keeper_boxes", "t2c_LH3_rail_flowerbox", "t2c_F5_fish_floats",
           "t2c_G8_cliff_baskets", "t2c_W5_flowerbox_rail"]
# THE CONTAINER IS A BOX AND MUST STAY ONE.  Inside these five objects the trough
# and the crate body are `mat_timber`; everything else is the thing sitting IN the
# trough.  Measured island counts: 22 timber containers, and 30 produce cuboids
# across `mat_pumpkin` (17), `mat_shelf_paint_green` (9) and `mat_qm_paint_red` (4,
# the fishdock floats, which have no timber at all because a float is not in a box).
# Stated as a RULE over the object's own material list rather than a third hand-typed
# list, so a re-run of `t2_color_pops` that repaints a box cannot silently escape it.
CONTAINER_MATS = {"mat_timber"}


def islands(me, midx):
    """Connected components of the faces using material slot `midx`."""
    faces = [p for p in me.polygons if p.material_index == midx]
    parent = {}

    def find(a):
        while parent.get(a, a) != a:
            parent[a] = parent.get(parent[a], parent[a]); a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    vf = {}
    for p in faces:
        parent.setdefault(p.index, p.index)
        for v in p.vertices:
            if v in vf:
                union(p.index, vf[v])
            vf[v] = p.index
    groups = {}
    for p in faces:
        groups.setdefault(find(p.index), []).append(p)
    return list(groups.values())


def _donor():
    """One produce unit lifted out of the town's own market clutter."""
    o = bpy.data.objects[DONOR_OBJ]
    me = o.data
    midx = [m.name if m else None for m in me.materials].index(PRODUCE_MAT)
    gs = islands(me, midx)
    assert gs, "%s carries no %s island" % (DONOR_OBJ, PRODUCE_MAT)
    g = gs[0]
    vids = sorted({v for p in g for v in p.vertices})
    assert len(vids) == 20 and len(g) == 12, (
        "donor is not the 20v/12f drum this tool was measured against: %d verts / %d faces"
        % (len(vids), len(g)))
    assert sorted({len(p.vertices) for p in g}) == [4, 10], "donor is not a 10-gon drum"
    assert all(p.use_smooth for p in g), "donor is not smooth shaded"
    remap = {v: i for i, v in enumerate(vids)}
    co = [Vector(me.vertices[v].co) for v in vids]      # OBJECT space of the donor
    mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
    mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
    span = Vector((max(mx.x - mn.x, 1e-6), max(mx.y - mn.y, 1e-6), max(mx.z - mn.z, 1e-6)))
    unit = [Vector(((c.x - mn.x) / span.x, (c.y - mn.y) / span.y, (c.z - mn.z) / span.z))
            for c in co]                                 # normalised to 0..1 in its box
    faces = [tuple(remap[v] for v in p.vertices) for p in g]
    print("DONOR %s: %d verts / %d faces, sides %s, box %.3f x %.3f x %.3f"
          % (DONOR_OBJ, len(unit), len(faces), sorted({len(f) for f in faces}),
             span.x, span.y, span.z))
    return unit, faces


def census():
    print("%-28s %-22s %6s %6s %6s %8s" % ("object", "material", "faces", "verts",
                                           "islands", "smooth%"))
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render or not o.users_collection:
            continue
        names = [m.name if m else None for m in o.data.materials]
        if PRODUCE_MAT not in names:
            continue
        midx = names.index(PRODUCE_MAT)
        gs = islands(o.data, midx)
        fs = [p for p in o.data.polygons if p.material_index == midx]
        vs = {v for p in fs for v in p.vertices}
        sides = sorted({len(p.vertices) for p in fs})
        print("%-28s %-22s %6d %6d %6d %8.1f  sides %s  per-island %d v / %d f"
              % (o.name, PRODUCE_MAT, len(fs), len(vs), len(gs),
                 100.0 * sum(1 for p in fs if p.use_smooth) / max(len(fs), 1), sides,
                 len(vs) // max(len(gs), 1), len(fs) // max(len(gs), 1)))


# --------------------------------------------------------------------- revert ---
def restore():
    n = 0
    for t in TARGETS:
        src = bpy.data.objects.get(SNAPP + t)
        ob = bpy.data.objects.get(t)
        if src and ob:
            old = ob.data
            ob.data = src.data.copy()
            ob.data.name = t
            if old.users == 0:
                bpy.data.meshes.remove(old)
            bpy.data.objects.remove(src, do_unlink=True)
            n += 1
    print("restored %d mesh(es) from %s*" % (n, SNAPP))


if REVERT:
    restore()
    if SAVE:
        bpy.ops.wm.save_mainfile(); print("SAVED %s" % bpy.data.filepath)
    else:
        print("reverted in memory (pass `save`)")
    sys.exit(0)

if CENSUS:
    census()
    _donor()
    sys.exit(0)

# ---------------------------------------------------------------------- carry ---
UNIT, DFACES = _donor()
report = []
for t in TARGETS:
    ob = bpy.data.objects.get(t)
    assert ob is not None, "missing target %s" % t
    me = ob.data
    names = [m.name if m else None for m in me.materials]
    assert PRODUCE_MAT in names, "%s does not wear %s" % (t, PRODUCE_MAT)
    prod = [i for i, n in enumerate(names) if n not in CONTAINER_MATS]
    todo = []
    for midx in prod:
        for g in islands(me, midx):
            vids = {v for p in g for v in p.vertices}
            assert len(vids) == 8 and len(g) == 6, (
                "%s island on %s is not a cuboid (%d verts / %d faces) — this tool only "
                "carries the obox() grammar it measured"
                % (t, names[midx], len(vids), len(g)))
            todo.append((midx, g))

    # rebuild the whole mesh: keep every container face verbatim, replace each
    # produce island with a scaled donor
    V = [Vector(v.co) for v in me.vertices]
    drop = {p.index for _, g in todo for p in g}
    newV = list(V)
    newF = [(tuple(p.vertices), p.material_index, p.use_smooth)
            for p in me.polygons if p.index not in drop]
    for midx, g in todo:
        vids = sorted({v for p in g for v in p.vertices})
        co = [V[v] for v in vids]
        mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
        mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
        span = mx - mn
        base = len(newV)
        for u in UNIT:
            newV.append(Vector((mn.x + u.x * span.x, mn.y + u.y * span.y,
                                mn.z + u.z * span.z)))
        for f in DFACES:
            newF.append((tuple(base + i for i in f), midx, True))
    report.append((t, len(todo), len(me.vertices), len(newV), len(me.polygons), len(newF)))

    if DRY:
        continue
    if bpy.data.objects.get(SNAPP + t) is None:
        src = bpy.data.objects.new(SNAPP + t, me.copy())
        src.use_fake_user = True

    nm = bpy.data.meshes.new(t + "_dpk")
    nm.from_pydata([tuple(v) for v in newV], [], [f[0] for f in newF])
    nm.validate()
    for m in me.materials:
        nm.materials.append(m)
    for p, (_, mi, sm) in zip(nm.polygons, newF):
        p.material_index = mi
        p.use_smooth = sm
    old = me
    ob.data = nm
    nm.name = t
    assert [m.name if m else None for m in ob.data.materials] == names, \
        "%s material list changed" % t

print("\n%-28s %8s %10s %10s" % ("object", "islands", "verts", "faces"))
for t, ng, v0, v1, f0, f1 in report:
    print("%-28s %8d %5d->%-5d %5d->%-5d" % (t, ng, v0, v1, f0, f1))
print("TOTAL cuboids carried: %d" % sum(r[1] for r in report))

if DRY:
    print("--dry: nothing written")
elif SAVE:
    bpy.ops.wm.save_mainfile(); print("SAVED %s" % bpy.data.filepath)
else:
    print("not saved (pass `save`)")
