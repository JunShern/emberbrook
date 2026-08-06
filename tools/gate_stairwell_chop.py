"""gate_stairwell_chop.py — THE STAIRWELL: the gallery's corbel run skips the ONE DESCENT.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_stairwell_chop.py -- [save] [revert]

WHY (BET 2, 2026-08-06).  The gate->shelf descent was rebuilt as ONE straight 2.2 u
flight (map edge valley-gate->inn, no waypoints; see the edge's own notes).  The gate
tier east of the arch is a CORBELLED GALLERY oversailing the shelf street — that is
the district's design (shelf_build measures it as the street's CEILING) — so the
flight necessarily passes through the gallery's edge band on its way down.  The
gallery SLAB is fine: from tread t08 down the flight runs under it with 2.69..4.60 m
of measured headroom (an arcade, not a crawl).  What is NOT fine is `gate_corbels`,
the bracket run under the slab edge: its stones reach down to z 21.22 and stand in
the body window across the flight at x 19..22 — `_court_probe --who` named it on
26 cells and both `--way` drives stalled on it (down at [20.29, 22.53], up at
[21.19, 22.15]).  A stone bracket at head height mid-flight is the whole finding.

WHAT THIS DOES.  A stairwell notch, the way a real corbelled gallery meets a real
stair: the bracket RUN SKIPS the stairwell.  Every LOOSE PART of `gate_corbels`
that intersects the flight's swept body corridor — each tread's world bbox grown
GROW in plan, z from tread top - 0.30 to tread top + HEADROOM — is removed WHOLE.
Deleting whole brackets rather than booleaning them keeps every surviving stone a
stone; a sliced corbel reads as damage, a skipped bay reads as a stairwell.

WHAT IT REFUSES TO DO: touch any other object, or any part of the run outside the
corridor.  The corridor is derived from the CURRENT walk records at run time, so a
future flight move re-derives the notch by re-running this after walk_rederive —
same carrier discipline as gate_rimchop/gate_roadchop (gate_build stays unrunnable).

FAITHFULNESS: the rest of the town is digested (name + world-vert count) before and
after and asserted UNCHANGED; the pre-chop mesh is snapshotted GSC_SRC_gate_corbels
with a fake user, so `revert save` restores it bit-identical.
"""
import bpy, bmesh, sys, hashlib
from mathutils import Vector

SAVE = "save" in sys.argv
REVERT = "revert" in sys.argv
FLIGHT = "walk_e_valley-gate__inn_"
TARGET = "gate_corbels"
SNAP = "GSC_SRC_" + TARGET
GROW = 0.45          # plan growth: body radius 0.42 + margin
HEADROOM = 2.40      # the body window's top over a tread, with margin


def town_digest(skip):
    h = hashlib.sha256()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != 'MESH' or o.name in skip:
            continue
        h.update(o.name.encode())
        h.update(str(len(o.data.vertices)).encode())
    return h.hexdigest()[:16]


ob = bpy.data.objects.get(TARGET)
assert ob is not None, "no %s in this master" % TARGET

if REVERT:
    src = bpy.data.objects.get(SNAP)
    assert src is not None, "no snapshot %s to revert to" % SNAP
    old = ob.data
    ob.data = src.data.copy()
    ob.data.name = TARGET
    bpy.data.objects.remove(src, do_unlink=True)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    print("REVERTED %s from %s" % (TARGET, SNAP))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED", bpy.data.filepath)
    sys.exit(0)

# ---- the corridor: every flight tread's grown bbox ---------------------------
boxes = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(FLIGHT) and o.name.split("_")[-1].startswith("t"):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        top = max(p.z for p in bb)
        boxes.append((min(p.x for p in bb) - GROW, max(p.x for p in bb) + GROW,
                      min(p.y for p in bb) - GROW, max(p.y for p in bb) + GROW,
                      top - 0.30, top + HEADROOM))
assert boxes, "no %s treads found — run walk_rederive first" % FLIGHT
print("corridor: %d tread boxes" % len(boxes))


def in_corridor(p):
    for x0, x1, y0, y1, z0, z1 in boxes:
        if x0 <= p.x <= x1 and y0 <= p.y <= y1 and z0 <= p.z <= z1:
            return True
    return False


d0 = town_digest({TARGET, SNAP})

# snapshot (idempotent: keep the FIRST snapshot, it is the shipped state)
if bpy.data.objects.get(SNAP) is None:
    src = bpy.data.objects.new(SNAP, ob.data.copy())
    src.use_fake_user = True
    print("SNAPSHOT %s (%d verts, fake user, linked to no collection)"
          % (SNAP, len(src.data.vertices)))

bm = bmesh.new()
bm.from_mesh(ob.data)
bm.verts.ensure_lookup_table()
mw = ob.matrix_world

# label loose parts by flood fill over edges
part = {}
pid = 0
for v in bm.verts:
    if v.index in part:
        continue
    stack = [v]
    while stack:
        u = stack.pop()
        if u.index in part:
            continue
        part[u.index] = pid
        for e in u.link_edges:
            w = e.other_vert(u)
            if w.index not in part:
                stack.append(w)
    pid += 1

hit = set()
for v in bm.verts:
    if in_corridor(mw @ v.co):
        hit.add(part[v.index])

kill = [v for v in bm.verts if part[v.index] in hit]
nparts = pid
print("%s: %d loose parts, %d intersect the flight corridor -> removed whole"
      % (TARGET, nparts, len(hit)))
assert hit, "nothing intersects — either already chopped (idempotent no-op) or wrong corridor"
assert len(hit) < nparts, "the corridor would take the WHOLE corbel run — wrong corridor, refusing"
bmesh.ops.delete(bm, geom=kill, context='VERTS')
bm.to_mesh(ob.data)
bm.free()
print("%s: %d verts remain" % (TARGET, len(ob.data.vertices)))

d1 = town_digest({TARGET, SNAP})
assert d0 == d1, "town digest moved: %s -> %s — this pass touched something else" % (d0, d1)
print("FAITHFULNESS: town digest %s unchanged (everything but %s)" % (d0, TARGET))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
