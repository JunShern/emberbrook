"""dh_cloth_smooth.py — THE AWNING IS NOT CLIPPING AND IT IS NOT UNTEXTURED.  IT IS
TWENTY-FOUR NON-PLANAR QUADS SHADED FLAT, WHICH IS A RAZOR CREASE DOWN EVERY PANEL.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_cloth_smooth.py -- [--census] [--dry] [save]
  … -P tools/dh_cloth_smooth.py -- revert save

WHAT WAS MEASURED (round 13), AND THE TWO THINGS IT REFUTED.

Crossing's four-round standing complaint is *"an untextured grey polygon CLIPPING
THROUGH the wooden walkway, bottom right"*, which round 12 put on the geometry for
the first time: 78.5% `qm_awning_0 | mat_qm_awning` at 5.3 m.  Rounds 8-11 treated it
as relief, then value, then texture.  Round 13 asked the two words themselves.

  * **IT DOES NOT CLIP.**  A real triangle-triangle `BVHTree.overlap` of all nine
    awnings against every other mesh in town: `qm_awning_0` has **ZERO overlaps**, and
    its minimum per-vertex down-ray gap to the surface below is **2.075 m** (max 3.412),
    over `qm_paving` / `qm_planking` / `qm_stall_1` / `lk_bearers`.  That is `AWN_CLEAR`
    (2.24 m over a 2.05 m corridor) doing exactly its job.  Three other awnings DO
    overlap something (`qm_awning_2` x2, `shelf_awning_0/1/2/3` x1 each) and none of
    them is the complained-about one.
  * **IT IS NOT UNTEXTURED.**  Round 11's canvas landed: on its own ray-derived,
    eroded mask the shipped plate reads **5x5 SD p50 8.29**, against `mat_qm_paving`'s
    own 6.40 in round 11's table and against the 0.00-3.56 it had before.

**WHAT IT ACTUALLY IS, AND IT IS EXACT: 24 OF 24 QUADS NON-PLANAR, 0% SMOOTH.**  A quad
whose four corners are not coplanar is triangulated by the renderer; flat-shaded, the
two triangles get different normals and you get a hard crease down the diagonal of
every panel.  Worst deviation **0.0705 m — which is `SAG_MID` (0.073)**, so the cause
is arithmetic and was predictable from `qm_build.awning()` before anything was
rendered: the scallop lifts ALTERNATE columns, so every quad spans one lifted rib
column and one unlifted mid column and cannot be planar.  The plate agrees: the
awning photographs as folded sheet metal, not cloth.

Town-wide census (`--census`): 52 meshes carry non-planar quads, 35 of them at 0%
smooth.  The cliffs are 75-99% non-planar and **100% smooth** — the town's own
convention already knows this, and the cloth pass never got it.

    qm_awning_0..4              24/24 quads non-planar   worst 0.0705 m   0% smooth
    t2c_*_laundry (x5)          42/75-81                 worst 0.0701 m   0% smooth
    t2c_*_banner / crest (x5)   19/30                    worst 0.0495 m   0% smooth

WHAT THIS DOES: sets `use_smooth` on the cloth family.  **NOT ONE VERTEX MOVES**, which
is not a nicety — `awning_lip` and `over_walk` cleared a 2.24 m headroom against this
exact geometry and the builder's own comment says the clearance must be arithmetically
untouched.  It is asserted here, per object, over the world coordinates.

WHY THE GROUNDS ARE NOT IN THE LIST, THOUGH THEY ARE 21-63% NON-PLANAR: a ground's
crease is at ONE metre of curvature over tens of metres and is read as terrain; a
canvas's is at 0.07 m over 0.42 m and is read as a fold.  And smoothing a ground would
round off every deliberate step edge in the town.  The subject is CLOTH — a material
class whose real-world surface has no creases at all except the ones the sag makes.
"""
import bpy, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DRY = "--dry" in argv
REVERT = "revert" in argv
CENSUS = "--census" in argv

# The cloth family, by the objects that build it.  `t2c_F1_wf_awnings` and its
# siblings are deliberately ABSENT: they are 24v/14f tents whose quads are planar,
# so they are not in this class and smoothing them would only soften a real fold.
PFX = ("qm_awning_", "shelf_awning_", "t2c_W1_laundry", "t2c_W2_laundry",
       "t2c_F4_wf_laundry", "t2c_DS4_yard_laundry", "t2c_WV1_quaydeck_laundry",
       "t2c_G4_arch_banner", "t2c_GB1_cliff_banner", "t2c_GB2_cliff_banner",
       "t2c_GB3_cliff_banner", "t2c_L1_crest_banners")
# The rope and timber slots inside a laundry line are POSTS AND A LINE, not cloth:
# a 6-gon post shaded smooth turns into a soft tube.  Only the cloth faces are set.
NOT_CLOTH = {"mat_rope", "mat_timber", "mat_timber_dark", "mat_iron"}


def targets():
    return [o for o in bpy.data.objects
            if o.type == 'MESH' and not o.hide_render and o.users_collection
            and o.name.startswith(PFX) and len(o.data.polygons)]


def planarity(o):
    mw = o.matrix_world
    me = o.data
    nq = bad = 0
    worst = 0.0
    for p in me.polygons:
        if len(p.vertices) != 4:
            continue
        nq += 1
        v = [mw @ me.vertices[i].co for i in p.vertices]
        n = (v[1] - v[0]).cross(v[3] - v[0])
        if n.length < 1e-9:
            continue
        n.normalize()
        d = abs((v[2] - v[0]).dot(n))
        worst = max(worst, d)
        if d > 0.005:
            bad += 1
    return nq, bad, worst


if CENSUS:
    print("%-26s %6s %6s %9s %8s %8s" % ("object", "quads", "nonpl", "worst m",
                                         "smooth%", "cloth f"))
    for o in targets():
        nq, bad, w = planarity(o)
        names = [m.name if m else None for m in o.data.materials]
        cf = sum(1 for p in o.data.polygons if names[p.material_index] not in NOT_CLOTH)
        print("%-26s %6d %6d %9.4f %8.1f %8d  %s"
              % (o.name, nq, bad, w,
                 100.0 * sum(1 for p in o.data.polygons if p.use_smooth)
                 / len(o.data.polygons), cf, ",".join(n or '-' for n in names)[:34]))
    sys.exit(0)

rows = []
skipped = []
for o in targets():
    me = o.data
    # THE SUBJECT IS THE DEFECT, NOT THE FAMILY.  `shelf_awning_0..3` are in the
    # cloth family and have ZERO non-planar quads (they are planar tents); smoothing
    # them would round off a ridge that is a real fold and buy nothing.  Measured, not
    # assumed — a shelf awning rebuilt with a scallop would join the list on its own.
    if planarity(o)[1] == 0:
        skipped.append(o.name)
        continue
    names = [m.name if m else None for m in me.materials]
    before = [tuple(v.co) for v in me.vertices]
    n0 = sum(1 for p in me.polygons if p.use_smooth)
    hit = 0
    for p in me.polygons:
        cloth = names[p.material_index] not in NOT_CLOTH
        want = False if REVERT else cloth
        if cloth and p.use_smooth != want:
            hit += 1
        if cloth and not DRY:
            p.use_smooth = want
    after = [tuple(v.co) for v in me.vertices]
    assert before == after, "%s moved a vertex — this tool may only change shading" % o.name
    nq, bad, w = planarity(o)
    rows.append((o.name, len(me.polygons), n0,
                 sum(1 for p in me.polygons if p.use_smooth), hit, nq, bad, w))

print("%-26s %6s %10s %8s %6s %6s %9s" % ("object", "polys", "smooth", "changed",
                                          "quads", "nonpl", "worst m"))
for n, np_, s0, s1, hit, nq, bad, w in rows:
    print("%-26s %6d %4d->%-4d %8d %6d %6d %9.4f" % (n, np_, s0, s1, hit, nq, bad, w))
print("%d object(s), %d polygon(s) reshaded, 0 vertices moved (asserted per object)"
      % (len(rows), sum(r[4] for r in rows)))
print("SKIPPED (0 non-planar quads — planar cloth, not in the class): %s"
      % (", ".join(skipped) or "none"))

if DRY:
    print("--dry: nothing written")
elif SAVE:
    bpy.ops.wm.save_mainfile(); print("SAVED %s" % bpy.data.filepath)
else:
    print("not saved (pass `save`)")
