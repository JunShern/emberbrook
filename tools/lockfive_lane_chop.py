"""lockfive_lane_chop.py — THE RETIRED STAIR'S BODY LEAVES THE LANE (pain inventory #9).

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/lockfive_lane_chop.py -- [save] [revert]

WHY (BET 2, 2026-08-06).  r22 retired keepers-cottage__lock-five's WALK RECORDS (the
40-degree porch flight no body could climb; the map's `_steps_retired_2026-08-05` note
carries the whole argument) — but its ART stayed, deliberately, as scenery.  Its foot
did not stay scenery: `lg_ks_treads` (39 cells), `lg_ks_rail` (38) and `lg_ks_frame`
(6) stand in the body window over the lock-five -> north-landing lane (`--who` over
x 87.5..93.5, plan 25.6..28.8), and the westbound drive stalls at [90.38, -0.14, -27.57].
This is the ch2.dock -> landing walk.  A retired stair that still bars a LIVE lane is
not scenery, it is a wall wearing scenery's name.

WHAT THIS DOES.  Same operation, same guarantees as gate_stairwell_chop (the ratified
precedent): every LOOSE PART of the three lg_ks_* meshes that intersects the LANE'S
swept body corridor — each walk_e_lock-five__north-landing_* record's world bbox grown
GROW in plan, z from record top - 0.30 to top + HEADROOM — is removed WHOLE.  The
stair's upper body (the porch scenery the ruling kept) survives untouched; only what
reaches into the lane goes.  A truncated flight hanging above the dock also reads
"not a way" where the full flight read as an invitation — routes_derive marks exactly
that trap class `blocked` on ladders for the same reason.

WHAT IT REFUSES TO DO: touch any other object (town digest asserted unchanged), or
run without walk records (the corridor is derived from the CURRENT lane at run time).
lf_railings and the winch furniture also show cells in the band — they are locksfoot's
own live furniture, NOT the retired stair, and are deliberately out of scope: measure
them on their own ticket if the drive still stalls after this.

FAITHFULNESS: pre-chop meshes snapshotted LKC_SRC_<name> with a fake user;
`revert save` restores them bit-identical; digest over everything else must not move.
"""
import bpy, bmesh, sys, hashlib
from mathutils import Vector

SAVE = "save" in sys.argv
REVERT = "revert" in sys.argv
LANE = "walk_e_lock-five__north-landing_"
TARGETS = ["lg_ks_treads", "lg_ks_rail", "lg_ks_frame"]
SNAPP = "LKC_SRC_"
GROW = 0.45          # plan growth: body radius 0.42 + margin
HEADROOM = 2.40      # the body window's top over the lane floor, with margin


def town_digest(skip):
    h = hashlib.sha256()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != 'MESH' or o.name in skip:
            continue
        h.update(o.name.encode())
        h.update(str(len(o.data.vertices)).encode())
    return h.hexdigest()[:16]


SKIP = set(TARGETS) | {SNAPP + t for t in TARGETS}

if REVERT:
    for t in TARGETS:
        ob = bpy.data.objects.get(t)
        src = bpy.data.objects.get(SNAPP + t)
        assert ob is not None and src is not None, "no snapshot for %s" % t
        old = ob.data
        ob.data = src.data.copy()
        ob.data.name = t
        bpy.data.objects.remove(src, do_unlink=True)
        if old.users == 0:
            bpy.data.meshes.remove(old)
        print("REVERTED %s" % t)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED", bpy.data.filepath)
    sys.exit(0)

# ---- the corridor: every lane record's grown bbox ----------------------------
boxes = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(LANE):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        top = max(p.z for p in bb)
        boxes.append((min(p.x for p in bb) - GROW, max(p.x for p in bb) + GROW,
                      min(p.y for p in bb) - GROW, max(p.y for p in bb) + GROW,
                      top - 0.30, top + HEADROOM))
assert boxes, "no %s records found — wrong master?" % LANE
print("corridor: %d lane boxes" % len(boxes))


def in_corridor(p):
    for x0, x1, y0, y1, z0, z1 in boxes:
        if x0 <= p.x <= x1 and y0 <= p.y <= y1 and z0 <= p.z <= z1:
            return True
    return False


d0 = town_digest(SKIP)

for t in TARGETS:
    ob = bpy.data.objects.get(t)
    assert ob is not None, "no %s in this master" % t
    if bpy.data.objects.get(SNAPP + t) is None:
        src = bpy.data.objects.new(SNAPP + t, ob.data.copy())
        src.use_fake_user = True
        print("SNAPSHOT %s (%d verts, fake user)" % (SNAPP + t, len(src.data.vertices)))

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    mw = ob.matrix_world

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
    print("%s: %d loose parts, %d intersect the lane corridor -> removed whole"
          % (t, pid, len(hit)))
    if not hit:
        bm.free()
        print("%s: nothing in the corridor (idempotent no-op)" % t)
        continue
    assert len(hit) < pid, ("the corridor would take ALL of %s — wrong corridor, "
                            "refusing" % t)
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    print("%s: %d verts remain" % (t, len(ob.data.vertices)))

d1 = town_digest(SKIP)
assert d0 == d1, "town digest moved: %s -> %s — this pass touched something else" % (d0, d1)
print("FAITHFULNESS: town digest %s unchanged (everything but %s)" % (d0, ", ".join(TARGETS)))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
