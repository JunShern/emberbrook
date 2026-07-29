"""master_weld_fixes.py — geometry-coherence fixes for the Boatyard region.

Applied by `master_weld.py -- fixes`.  Every entry here was found by
tools/geometry_audit.py, and the fix is written so the audit re-run proves it.

Rules followed:
  * walk_/bar_ meshes are never touched;
  * where two diegetic objects interpenetrate, the LESS load-bearing one gives way
    (a quay bollard yields to a mast that carries the yard's bunting);
  * a floating prop is attached to the thing it should hang from, not deleted,
    when its position is clearly deliberate (the lantern spacing marks the route).
"""
import bpy, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

MASTS = "bunting_masts"
BOLLARDS = "yard_bollards"


def _bvh(ob, dg):
    return BVHTree.FromObject(ob, dg)


def _wbb(ob):
    vs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs),
            max(v.y for v in vs), min(v.z for v in vs), max(v.z for v in vs))


def fix_mast_through_bollard(log):
    """A bunting mast is driven straight through a quay bollard (0.36 m deep).

    The mast is structural — it carries the bunting runs across the yard — so the
    bollard is the one that yields.  Both live inside joined multi-part meshes, so
    the fix is vertex surgery: drop the one bollard the mast stands in.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    masts = bpy.data.objects.get(MASTS)
    boll = bpy.data.objects.get(BOLLARDS)
    if not (masts and boll):
        return
    for _pass in range(4):
        dg = bpy.context.evaluated_depsgraph_get()
        ov = _bvh(masts, dg).overlap(_bvh(boll, dg))
        if not ov:
            break
        Mb = boll.matrix_world
        pts = [Mb @ boll.data.polygons[fb].center for _, fb in ov]
        # cluster the clashing faces in XY: one cluster = one bollard
        clusters = []
        for p in pts:
            for c in clusters:
                if math.hypot(p.x - c[0], p.y - c[1]) < 0.9:
                    break
            else:
                clusters.append((p.x, p.y))
        bm = bmesh.new()
        bm.from_mesh(boll.data)
        n0 = len(bm.verts)
        doomed = [v for v in bm.verts
                  if any(math.hypot((Mb @ v.co).x - cx, (Mb @ v.co).y - cy) < 0.95
                         for cx, cy in clusters)]
        if not doomed:
            break
        bmesh.ops.delete(bm, geom=doomed, context='VERTS')
        bm.to_mesh(boll.data)
        bm.free()
        boll.data.update()
        bpy.context.view_layer.update()
        log("FIX", "yard_bollards", "bollard(s) at %s removed — a bunting mast stood inside "
            "them; %d of %d verts dropped"
            % (", ".join("(%.1f,%.1f)" % c for c in clusters), len(doomed), n0))


HANGER_CANDIDATES = ("lantern_brackets", "lock_four_gantry", "boatwright_shed",
                     "cargo_winch_foot", "bunting_masts", "yard_railings",
                     "lockside_chandlery", "bank_netloft", "shed_paintwork",
                     "lock_four_dam", "yard_planking")


def fix_floating_lanterns(log):
    """Lanterns hanging on nothing get an iron hanger to the structure beside them.

    Their placement is deliberate (they space out along the walk route and are the
    yard's night practicals), so they are attached rather than moved or deleted.
    """
    # idempotent: clear any hangers a previous run made before re-measuring
    for o in list(bpy.data.objects):
        if "_hanger" in o.name:
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    iron = bpy.data.materials.get("mat_iron")
    cands = [(bpy.data.objects[n], _bvh(bpy.data.objects[n], dg))
             for n in HANGER_CANDIDATES if bpy.data.objects.get(n)]
    made = 0
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        if ob.type != 'MESH' or not ob.name.startswith("lantern_") or ob.name == "lantern_brackets":
            continue
        b = _wbb(ob)
        cx, cy, ztop = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, b[5]
        held = False
        for dvec, dist in (((0, 0, -1), 0.75), ((0, 0, 1), 0.60), ((1, 0, 0), 0.60),
                           ((-1, 0, 0), 0.60), ((0, 1, 0), 0.60), ((0, -1, 0), 0.60)):
            org = Vector((cx, cy, b[4] - 0.02)) if dvec[2] < 0 else Vector((cx, cy, ztop - 0.02))
            hit, loc, nor, idx, hob, mat = sc.ray_cast(dg, org, Vector(dvec), distance=dist)
            if hit and hob is not ob:
                held = True
                break
        if held:
            continue
        top = Vector((cx, cy, ztop))
        best, bestd, bestname = None, 1e9, None
        for cob, cb in cands:
            loc, nor, idx, d = cb.find_nearest(top, 3.2)
            if loc is not None and d < bestd:
                best, bestd, bestname = loc.copy(), d, cob.name
        if best is None:
            log("FIX", ob.name, "floating with nothing within 3.2 m — left in place, flagged")
            continue
        seg = 6
        verts, faces = [], []
        for k in range(seg + 1):
            f = k / seg
            p = top.lerp(best, f)
            for a in range(4):
                th = a * math.pi / 2 + math.pi / 4
                verts.append((p.x + 0.022 * math.cos(th), p.y + 0.022 * math.sin(th), p.z))
        for k in range(seg):
            for a in range(4):
                i0 = k * 4 + a
                i1 = k * 4 + (a + 1) % 4
                faces.append((i0, i1, i1 + 4, i0 + 4))
        me = bpy.data.meshes.new(ob.name + "_hanger")
        me.from_pydata(verts, [], faces)
        me.validate()
        if iron:
            me.materials.append(iron)
        h = bpy.data.objects.new(ob.name + "_hanger", me)
        for c in ob.users_collection:
            c.objects.link(h)
            break
        made += 1
        log("FIX", ob.name + "_hanger", "iron hanger %.2f m to %s — the lantern was hanging "
            "on nothing" % (bestd, bestname))
    if not made:
        log("FIX", "lanterns", "no floating lanterns found")


def apply(log):
    fix_mast_through_bollard(log)
    fix_floating_lanterns(log)
