"""pilot_head_chop.py — lg_wv_rail LEAVES THE SEARCHED FLIGHT'S CORRIDOR (BET 2 it.6).

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/pilot_head_chop.py -- [save] [revert]

WHY (2026-08-06, measured).  Iteration 6 relocated quay-deck__pilot-cluster's hairpin
to the searched south line.  The legibility pass's weave railing `lg_wv_rail` (lg_build)
now crosses the flight's HEAD: `--at` names it blocking the landing/t00 cells at
[58.65..58.72, 13.35..13.47, -18.6..-18.7], and the DOWN drive wedges on l0_t01 unable
to enter the flight (UP threads east of the crossing and walks 9/9 — a directional
wall).  The ring search's art oracle DID hit this rail, and its head-zone filter then
excluded the hit as "fixed geometry common to all candidates" — a measured lesson: the
filter was drawn wider than the fixed geometry it meant to exclude, and it swallowed a
real wall.  lg_build CANNOT be re-run to fix this (its own header: it derives the
Keepers' Steps from walk records r22 retired, so a re-run DELETES that stair).

WHAT THIS DOES.  crossing_lane_chop's slot-test (local-space walk-slot corridor over
the flight's CURRENT records, treads/landings/apron), lockfive_lane_chop's loose-part
operation — but with ls_reorigin's GAP fallback: if a hit part is bigger than 3 m in
plan (the rail's continuous run, not a post), its VERTS inside the corridor are cut
instead of the whole part, leaving a gap the way ls_reorigin cut the market rail.
Digest over everything else asserted; PHC_SRC_ snapshot; revert restores bit-identical.
RE-RUN CONTRACT: none owed — lg_build is frozen by its own header's warning.
"""
import bpy, bmesh, sys, hashlib
from mathutils import Vector

SAVE = "save" in sys.argv
REVERT = "revert" in sys.argv
LANE = "walk_e_quay-deck__pilot-cluster_"
TARGETS = ["lg_wv_rail"]
SNAPP = "PHC_SRC_"
SLOT = 1.15          # flight half-width 1.0 + a rail's own thickness margin
END_GROW = 0.45
HEADROOM = 2.40
BIG_PART_PLAN = 3.0  # a part longer than this is the rail run: gap-cut, not removal


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

recs = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(LANE):
        dx, dy, dz = o.dimensions
        recs.append((o.matrix_world.inverted().copy(),
                     1 + 2 * END_GROW / max(dx, 1e-6),
                     2 * SLOT / max(dy, 1e-6) if dy < dx else 1 + 2 * 0.15 / max(dy, 1e-6),
                     1 - 2 * 0.30 / max(dz, 1e-6),
                     1 + 2 * HEADROOM / max(dz, 1e-6)))
assert recs, "no %s records found — wrong master?" % LANE
print("corridor: %d flight records" % len(recs))


def in_corridor(p):
    for Mi, fx, fy, z0, z1 in recs:
        l = Mi @ p
        if abs(l.x) <= fx and abs(l.y) <= fy and z0 <= l.z <= z1:
            return True
    return False


d0 = town_digest(SKIP)

for t in TARGETS:
    ob = bpy.data.objects.get(t)
    assert ob is not None, "no %s in this master" % t
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
    print("%s: %d loose parts, %d intersect the flight corridor" % (t, pid, len(hit)))
    if not hit:
        bm.free()
        print("%s: nothing in the corridor (idempotent no-op)" % t)
        continue
    if bpy.data.objects.get(SNAPP + t) is None:
        src = bpy.data.objects.new(SNAPP + t, ob.data.copy())
        src.use_fake_user = True
        print("SNAPSHOT %s (%d verts, fake user)" % (SNAPP + t, len(src.data.vertices)))

    # plan size of each hit part decides removal vs gap-cut
    ext = {}
    for v in bm.verts:
        p = part[v.index]
        if p not in hit:
            continue
        w = mw @ v.co
        e = ext.setdefault(p, [w.x, w.x, w.y, w.y])
        e[0] = min(e[0], w.x); e[1] = max(e[1], w.x)
        e[2] = min(e[2], w.y); e[3] = max(e[3], w.y)
    kill = []
    ncut = nrem = 0
    for v in bm.verts:
        p = part[v.index]
        if p not in hit:
            continue
        e = ext[p]
        big = max(e[1] - e[0], e[3] - e[2]) > BIG_PART_PLAN
        if big:
            if in_corridor(mw @ v.co):
                kill.append(v); ncut += 1
        else:
            kill.append(v); nrem += 1
    assert len(kill) < len(bm.verts), "the corridor would take ALL of %s — refusing" % t
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    print("%s: gap-cut %d verts from long runs, removed %d post verts; %d verts remain"
          % (t, ncut, nrem, len(ob.data.vertices)))

d1 = town_digest(SKIP)
assert d0 == d1, "town digest moved: %s -> %s — this pass touched something else" % (d0, d1)
print("FAITHFULNESS: town digest %s unchanged (everything but the targets)" % d0)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
