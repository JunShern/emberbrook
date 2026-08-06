"""crossing_lane_chop.py — THE POSTCARD BRIDGE IS SEVERED BY ITS OWN DRESSING (BET 2).

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/crossing_lane_chop.py -- [save] [revert]

WHY (2026-08-06, measured on the shipped townwalk bundle).  The weave-huts__keepers-
cottage span — the route §9.1 of the pain inventory ruled "the only real one" from the
cottage down to the moorage — does not cross: `--pairs` weave<->cottage is no-path BOTH
ways, `--way` stalls at [74.65, 7.96, -22.9] and [83.49, 7.35, -22.9], and a 0.2 m fill
seeded mid-span holds an island of x 80.0..82.6 only.  `--at`/`--who` name the walls:
`t2c_W9_laundry_planking_2/_5` (pops-of-colour washing hanging into the 1.1 m slot
between the deck rails) and `t2c_W5_flowerbox_rail_1`.  The laundry was placed from a
screen-space probe rectangle that carried no idea of what was under it — the same
mechanism t2_color_pops.py itself convicts in its G3/GB5 hand-off note.  This severed
the town: with the ramp fixed, quay/shelf/cottage and weave/moorage were joined ONLY by
the (also shut) #7 foot.

WHAT THIS DOES.  lockfive_lane_chop's operation, verbatim: every LOOSE PART of the
target t2c_* meshes intersecting the lane's swept body corridor — each
walk_e_weave-huts__keepers-cottage_* record's world bbox grown GROW in plan, z from
record top - 0.30 to top + HEADROOM — is removed WHOLE.  Washing that hangs BESIDE the
corridor survives; only what reaches into it goes.  cx_rail and the bar_ blockout rails
are deliberately NOT targets: they are the span's own guard rails (generator-owned; the
junction-inset rule in town_blockout is their fix), and a chop with GROW 0.45 would
swallow the whole parapet since the rails stand inside the ribbon's own bbox.

RE-RUN CONTRACT: t2_color_pops.py re-installs the washing from its placement table, so
any re-run of that pass owes a re-run of this chop in the same window (the same shape as
t2_gate_awnings.py's own hand-off rule).

FAITHFULNESS: pre-chop meshes snapshotted CLC_SRC_<name> with a fake user;
`revert save` restores them bit-identical; digest over everything else must not move.
"""
import bpy, bmesh, sys, hashlib
from mathutils import Vector

SAVE = "save" in sys.argv
REVERT = "revert" in sys.argv
LANE = "walk_e_weave-huts__keepers-cottage_"
TARGET_PFX = ("t2c_W9_laundry_planking", "t2c_W5_flowerbox_rail")
SNAPP = "CLC_SRC_"
GROW = 0.45          # plan growth: body radius 0.42 + margin
HEADROOM = 2.40      # the body window's top over the lane floor, with margin

TARGETS = sorted(o.name for o in bpy.data.objects
                 if o.type == 'MESH' and o.name.startswith(TARGET_PFX)
                 and not o.name.startswith(SNAPP))


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

# ---- the corridor: the WALK SLOT of each lane record, in ITS OWN local space --
# NOT the grown world bbox lockfive_lane_chop uses: these legs run DIAGONAL, so a
# world bbox is a rectangle far wider than the ribbon, and the washing/flower rows
# are mounted ALONG the deck rails — a bbox corridor took EVERY part of both rows
# (measured on the first dry run: 12/12 and 10/10) where the engine's own census
# blamed three.  A leg_box is a unit cube under its matrix, so the slot test is
# exact in local coordinates: |y| within SLOT of the centreline (rail faces stand
# at 0.56; the body needs 0.42; dressing outside 0.55 narrows nothing), x within
# the leg + END_GROW, z from 0.30 under the walk top to HEADROOM over it.
SLOT = 0.55
END_GROW = 0.45
recs = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(LANE):
        dx, dy, dz = o.dimensions
        recs.append((o.matrix_world.inverted().copy(),
                     1 + 2 * END_GROW / max(dx, 1e-6),
                     2 * SLOT / max(dy, 1e-6),
                     1 - 2 * 0.30 / max(dz, 1e-6),
                     1 + 2 * HEADROOM / max(dz, 1e-6)))
assert recs, "no %s records found — wrong master?" % LANE
print("corridor: %d lane slots | targets: %s" % (len(recs), ", ".join(TARGETS)))


def in_corridor(p):
    for Mi, fx, fy, z0, z1 in recs:
        l = Mi @ p
        if abs(l.x) <= fx and abs(l.y) <= fy and z0 <= l.z <= z1:
            return True
    return False


d0 = town_digest(SKIP)

for t in TARGETS:
    ob = bpy.data.objects[t]
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

    print("%s: %d loose parts, %d intersect the lane corridor" % (t, pid, len(hit)))
    if not hit:
        bm.free()
        print("%s: nothing in the corridor (idempotent no-op)" % t)
        continue
    if bpy.data.objects.get(SNAPP + t) is None:
        src = bpy.data.objects.new(SNAPP + t, ob.data.copy())
        src.use_fake_user = True
        print("SNAPSHOT %s (%d verts, fake user)" % (SNAPP + t, len(src.data.vertices)))
    if len(hit) == pid:
        # the whole object hangs in the corridor: remove it outright rather than
        # leave a zero-vert husk (the row is decoration, not a guard)
        bpy.data.objects.remove(ob, do_unlink=True)
        bm.free()
        print("%s: EVERY part in the corridor -> object removed whole" % t)
        continue
    kill = [v for v in bm.verts if part[v.index] in hit]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    print("%s: %d verts remain" % (t, len(ob.data.vertices)))

d1 = town_digest(SKIP)
assert d0 == d1, "town digest moved: %s -> %s — this pass touched something else" % (d0, d1)
print("FAITHFULNESS: town digest %s unchanged (everything but the targets)" % d0)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
