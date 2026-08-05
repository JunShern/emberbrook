"""emb_lanepatch.py — CARRY THE MISSING FOUR SEGMENTS OF THE NORTH LANE INTO THE MASTER.

    /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/emberbrook-master.blend \
        -P tools/emb_lanepatch.py --python-exit-code 1 -- [save] [revert]

WHAT IT FIXES (PT-20260805-010, measured 2026-08-05).  `emb-cine` ships eleven ribbon
segments for the map edge `square-plaza__barn` — the ONLY road out of Emberbrook to the
Old Gate — named `walk_e_square-plaza__barn_l4 .. _l14`.  **THERE IS NO l0, l1, l2 OR
l3.**  The ribbon's near end therefore starts at map y 55.90, and the plaza's own carved
floor tiles stop short of it, so a strip roughly x 63.8..65.8 by y 55.0..55.9 carries a
solid, rendered, plate-visible ground with NO WALK NETWORK UNDER IT.

That strip is a ONE-WAY WALL, and the direction it refuses is the one Chapter One needs:

    node tools/_court_probe.mjs --port 3000 --scene emb-cine --way ...
      x 62.6  square -> gate   3/3 legs        x 63.8  STALLS at z -54.95
      x 63.2  square -> gate   3/3 legs        x 64.4  STALLS at z -54.95
                                               x 65.0  STALLS at z -54.95
                                               x 65.6  STALLS at z -54.95
      gate -> square, same lines: no stall     (downhill finds the plaza floor within
                                                STEP_DN; uphill finds no walk floor at
                                                the next 0.075 m stride and refuses)

The scenegraph seam the game routes through, `square>northlane`, sits at x 64.44 — DEAD
CENTRE OF THE CLOSED STRIP — and the way-marker draws over it.  In
`docs/qa/playtest/runs/run-20260805-022035` the playtest agent aimed at that seam eight
times and every leg ended at [64.9, 1.36, -54.96] with `closed 0.00 m of 2.94`, then
turned round: steps 131-200, the whole remaining budget, on a wall.

A FLOOD FILL CANNOT SEE IT.  `_court_probe --comp` from both sides reports ONE component
of 1058 cells, because the fill goes round the west side on a 0.4 m lattice with no body
box.  `_court_probe --grid ... "walk":true` is what names it: the strip prints `v` —
ground you can SEE and cannot STAND on.  Same class as walk_engine_gate's finding.

WHY A CARRIER AND NOT A MAP EDIT.  The doctrine fix is one lane waypoint plus a re-derive
(CLAUDE.md), and `walk_rederive.py` is exactly that command — but it is hardcoded to
Dellhollow's master, blockout and map, and `emb_blockout.py` regenerates the WHOLE
Emberbrook master in one pass.  Rebuilding a live 2316-object master to add four quads,
overnight, in front of a three-hour receipt run, is the trade CLAUDE.md already refuses
for the Old Gate (`gate_build.py MUST NOT be run against it`).  So this is additive and
revertible, like `gate_rimchop`: it appends the four segments the derivation left empty
and touches nothing else.  **If `emb_blockout.py` is ever re-run, this patch is
correctly lost** — and the derivation bug is still there, which is why it is written up
above rather than only in a commit message.

HOW THE FOUR ARE BUILT.  Not by hand: they are `l4`'s own centreline continued BACKWARD.
`l4`'s near end gives the point, the bearing and the width; the far end of the patch is
pushed to map y `Y_START`, which is 0.75 m inside the plaza floor tiles that reach y
54.35, so the new ribbon and the plaza floor OVERLAP rather than meet — `trim_to_rim`'s
own rule, applied at the end where it failed.  Heights are RAY-CAST against the master's
own walk surfaces at each vertex and fall back to a linear ramp between the two ends that
must match, so the patch sits on the ground the plate shows instead of floating over it.
`ribbon()` is copied verbatim from `emb_blockout.py` so the quads are the shape every
other segment is.

THE GATE IT PRINTS, before it will save: exactly four objects added, no name taken, every
new segment's world extent, and the height it found at each end.  Objects go into `l4`'s
own collection with `l4`'s material and hide flags — an imported record that renders is
the mistake `walk_rederive` already paid for.

AFTER SAVING, THE COLLISION GLB MUST BE RE-EXPORTED or nothing changes for the player:

    Blender -b tools/blends/emberbrook-master.blend -P tools/cine_bake.py \
        --python-exit-code 1 -- --town emberbrook --glb
"""
import bpy
import math
import sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

EDGE = "square-plaza__barn"
DONOR = "walk_e_%s_l4" % EDGE           # the first segment the derivation DID build
NEW = ["walk_e_%s_l%d" % (EDGE, k) for k in range(4)]   # l0..l3, the empty numbers
Y_START = 53.60          # map y the patch reaches back to; plaza tiles hold to 54.35
WDT = 2.4                # `road` ribbon width, emb_blockout's own number
HGT = 0.14               # ribbon skirt, emb_blockout's own number


def ribbon(name, a, b, wdt, hgt, m, coll_):
    """VERBATIM from emb_blockout.py — one flat segment of a walk surface."""
    ax, ay, az = a
    bx, by, bz = b
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return None
    nx, ny = -dy / L * wdt / 2.0, dx / L * wdt / 2.0
    v = [(ax + nx, ay + ny, az), (ax - nx, ay - ny, az),
         (bx - nx, by - ny, bz), (bx + nx, by + ny, bz)]
    v += [(x, y, z - hgt) for (x, y, z) in v]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in v], [], [tuple(q) for q in f])
    me.validate()
    me.update()
    if m:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    coll_.objects.link(ob)
    return ob


# ---------------------------------------------------------------- revert -------
if REVERT:
    gone = []
    for n in NEW:
        o = bpy.data.objects.get(n)
        if o:
            gone.append(n)
            bpy.data.objects.remove(o, do_unlink=True)
    print("REVERT removed %d: %s" % (len(gone), ", ".join(gone) or "-"))
    if SAVE and gone:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

bpy.context.view_layer.update()
N_BEFORE = len(bpy.data.objects)

d = bpy.data.objects.get(DONOR)
assert d is not None, "no %s in this blend — is this the Emberbrook master?" % DONOR
for n in NEW:
    assert bpy.data.objects.get(n) is None, (
        "%s already exists — this patch is already in, or the derivation now builds it. "
        "Run with `revert` first if you mean to replace it." % n)

# l4's TOP face, in world. The top is the four vertices at the higher z of each corner;
# `ribbon` writes the top four first, so read the object's own extremes instead of
# trusting index order: the near end is the lower map y.
W = [d.matrix_world @ v.co for v in d.data.vertices]
ztop = max(w.z for w in W)
top = [w for w in W if w.z > ztop - HGT * 0.5]
assert len(top) == 4, "expected 4 top verts on %s, got %d" % (DONOR, len(top))
# The near edge is the TWO LOWEST map y of the four, taken by rank rather than by a
# distance window: `l4` is only 0.64 m long, and a 0.6 m window caught three of them.
top.sort(key=lambda w: w.y)
near, far = top[:2], top[2:]
assert abs(near[1].y - near[0].y) < 1.2 and abs(far[1].y - far[0].y) < 1.2, (
    "%s's top face does not split into a near and a far edge" % DONOR)
NEAR = ((near[0].x + near[1].x) / 2.0, (near[0].y + near[1].y) / 2.0,
        (near[0].z + near[1].z) / 2.0)
FAR = ((far[0].x + far[1].x) / 2.0, (far[0].y + far[1].y) / 2.0,
       (far[0].z + far[1].z) / 2.0)
dx, dy = NEAR[0] - FAR[0], NEAR[1] - FAR[1]
L = math.hypot(dx, dy)
assert L > 0.3, "%s is degenerate in plan (%.3f m)" % (DONOR, L)
ux, uy = dx / L, dy / L                       # unit vector pointing BACK toward the plaza
assert uy < -0.2, ("%s does not run north-south (bearing y %.3f) — this patch's whole "
                   "geometry assumes the lane leaves the plaza toward +y" % (DONOR, uy))
run = (Y_START - NEAR[1]) / uy                # how far back along the bearing
assert 1.0 < run < 6.0, "patch run %.2f m is out of the range this fix was measured for" % run

# THE HEIGHT AT THE PLAZA END, ray-cast against the master's own walk surfaces rather
# than assumed. A ribbon laid at a guessed height is a ribbon the body stands 10 cm
# inside the road on.
START = (NEAR[0] + ux * run, Y_START, None)
dg = bpy.context.evaluated_depsgraph_get()
hit, loc, _nrm, _idx, _ob, _m = bpy.context.scene.ray_cast(
    dg, (START[0], START[1], ztop + 30.0), (0.0, 0.0, -1.0))
if hit and loc.z < ztop + 0.01:
    z0, how = loc.z, "ray-cast on %s" % (_ob.name if _ob else "?")
else:
    z0, how = NEAR[2] - 0.40, "FALLBACK ramp (no ray hit)"
print("  donor %s near [%.2f %.2f %.3f] far [%.2f %.2f %.3f]"
      % (DONOR, NEAR[0], NEAR[1], NEAR[2], FAR[0], FAR[1], FAR[2]))
print("  patch start [%.2f %.2f %.3f]  (%s)   run %.2f m along bearing (%.3f, %.3f)"
      % (START[0], START[1], z0, how, run, -ux, -uy))

# Four segments, plaza end -> l4's near end, z linear between the two ends that must
# match. Each vertex's own z is then pulled DOWN to any walk surface found under it, so
# the patch follows the graded lane instead of chording across it.
mat = d.data.materials[0] if d.data.materials else None
collection = d.users_collection[0] if d.users_collection else bpy.context.scene.collection
made = []
P = []
for k in range(len(NEW) + 1):
    t = k / float(len(NEW))
    P.append((START[0] + (NEAR[0] - START[0]) * t,
              START[1] + (NEAR[1] - START[1]) * t,
              z0 + (NEAR[2] - z0) * t))
for k, n in enumerate(NEW):
    ob = ribbon(n, P[k], P[k + 1], WDT, HGT, mat, collection)
    assert ob is not None, "segment %s came out degenerate" % n
    ob.hide_render = d.hide_render
    ob.hide_viewport = d.hide_viewport
    made.append(ob)

bpy.context.view_layer.update()
added = len(bpy.data.objects) - N_BEFORE
print("\n== GATE ==")
print("  objects %d -> %d   (added %d, expected %d)"
      % (N_BEFORE, len(bpy.data.objects), added, len(NEW)))
assert added == len(NEW), "added %d objects, expected %d" % (added, len(NEW))
for ob in made:
    ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
    print("  %-34s x %6.2f..%6.2f  y %6.2f..%6.2f  z %.3f..%.3f  coll=%s render=%s"
          % (ob.name, min(w.x for w in ws), max(w.x for w in ws),
             min(w.y for w in ws), max(w.y for w in ws),
             min(w.z for w in ws), max(w.z for w in ws),
             [c.name for c in ob.users_collection], not ob.hide_render))
gap = min(w.y for w in (made[0].matrix_world @ v.co for v in made[0].data.vertices))
print("  the patch reaches back to map y %.2f; the plaza's floor tiles hold to 54.35, "
      "so they OVERLAP by %.2f m" % (gap, 54.35 - gap))
assert gap < 54.35, "the patch does not reach the plaza floor — no overlap, no fix"

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("DRY RUN — nothing written. Add `save` to commit it to the master.")
