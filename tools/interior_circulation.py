#!/usr/bin/env python3
"""interior_circulation.py — the FLOOR-LEVEL clutter pass for the six interiors.

  Blender -b tools/blends/interiors/<room>-int.blend -P tools/interior_circulation.py \
          -- <roomkey> [--fix] [--save] [--json out.json]

WHY
---
Art-gate accepted rooms that are lovely to LOOK at can still be miserable to
WALK in: the runtime treats every visible floor-standing mesh as solid (raw
geometry, body half-width 0.30, step-up 0.63), so a basket beside the door mat
is a wall. The user's rule: *reduce clutter that literally blocks floorspace;
keep clutter on tables and places that aren't meant to be accessed.*

THE CIRCULATION ZONE
--------------------
  * a 1.2 m radius disc around every walk_pad_* (door, counter)
  * a 1.0 m wide lane joining the pads and the room's hero features (hearth,
    the shelves players read), routed by BFS through the IMMOVABLE geometry
    only — so the lane lands where the architecture says it should, not where
    today's clutter happens to leave a gap.

THE SIM (no browser)
--------------------
Samples the zone on a 0.15 m grid and puts the runtime's own body box at every
sample: an AABB of half-width 0.30 from floor+LO to floor+1.30, tested against
the real world-space triangles (exact tri-vs-AABB SAT, binned in a 2D hash).
Two heights are reported:
  hard  floor+0.65 .. floor+1.30   what the runtime actually refuses to enter
  full  floor+0.05 .. floor+1.30   a genuinely clear floor (a low crate you must
                                   climb is still friction, just not a wall)
Blocks are attributed to the object that owns the offending triangle, and split
into CLUTTER (movable) and STRUCTURE (hero furniture / walls we must not move).

THE FIX
-------
`--fix` applies the room's EDITS table below: whole-object moves/lifts/deletes
for the kit_* instances, and mesh-island surgery (move/delete loose parts) for
the joined dressing meshes, so the accepted composition above knee height is
untouched.  Idempotent-ish: island picks are keyed on position, so re-running a
fix that already ran finds nothing to do.
"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# ------------------------------------------------------------------ constants
BODY_R = 0.30          # runtime half-width
BODY_H = 1.30          # runtime collide height
STEP_UP = 0.63         # runtime step-up grace
LO_HARD = STEP_UP + 0.02
LO_FULL = 0.05
GRID = 0.15            # sample spacing for the zone metric
REACH_GRID = 0.10      # finer grid for the door->counter reachability walk: a
                       # 0.70 m gap for a 0.60 m body is real but a 0.15 grid
                       # can straddle it, so pinch points get their own pass
PAD_R = 1.2            # clear disc around a walk pad
LANE_W = 1.0           # lane width

SKIP_SUBSTR = ("fog", "shadow_ceiling", "steam_vol", "haze", "smoke", "steam_wisp")
SKIP_PREFIX = ("walk_", "REF_", "fx_", "bar_")


# ----------------------------------------------------------------- room table
# protected = the room's bones: never moved by this pass.  Anything matching
# these prefixes is STRUCTURE; everything else standing on the floor is clutter.
COMMON_PROTECT = (
    "wall", "kit_wall", "wainscot", "trim", "beam", "kit_beam", "ceil", "floor",
    "counter", "backshelf", "shelf_goods", "hearth", "range", "stair", "door",
    "window", "panwall", "dryrack", "hatch", "menuboard", "keyrack", "notice",
    "slate", "innsign", "lantern", "hanging", "hook", "prep", "bench", "table",
    "bed", "settle", "post", "sign", "rug", "step", "sill", "shelf",
)

ROOMS = {
    "cottage":   {"blend": "cottage-int.blend",   "key": "del-cottage-int"},
    "item":      {"blend": "item-int.blend",      "key": "del-item-int"},
    "inn":       {"blend": "inn-int.blend",       "key": "del-inn-int"},
    "weapon":    {"blend": "weapon-int.blend",    "key": "del-weapon-int"},
    "armor":     {"blend": "armor-int.blend",     "key": "del-armor-int"},
    "cookhouse": {"blend": "cookhouse-int.blend", "key": "del-cookhouse-int"},
}

# hero features the player must be able to reach, per room, as (label, x, y).
FEATURES = {}
# PROTECT[room] = extra name substrings that are this room's bones (added to COMMON)
PROTECT = {}
# PROTECT_BOX[room] = [(name, x0,x1,y0,y1,z0,z1)] — triangles of a JOINED mesh inside
# the box count as structure (wall coats inside a `luggage` blob, etc.)
PROTECT_BOX = {}
# EDITS[room] = list of ops.  See _apply_edits.
EDITS = {}


# ------------------------------------------------------------------- geometry
def world_tris(objs):
    """[(v0,v1,v2,objname)] in world space, from evaluated meshes."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for ob in objs:
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except Exception:
            continue
        mw = ob.matrix_world
        me.calc_loop_triangles()
        vs = [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles:
            a, b, c = t.vertices
            out.append((vs[a], vs[b], vs[c], ob.name))
        ev.to_mesh_clear()
    return out


class TriHash:
    """2D uniform bins over x/y; each bin holds triangle indices."""
    def __init__(self, tris, cell=0.5):
        self.tris, self.cell, self.bins = tris, cell, {}
        for i, (a, b, c, _n) in enumerate(tris):
            x0 = min(a.x, b.x, c.x); x1 = max(a.x, b.x, c.x)
            y0 = min(a.y, b.y, c.y); y1 = max(a.y, b.y, c.y)
            for ix in range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1):
                for iy in range(int(math.floor(y0 / cell)), int(math.floor(y1 / cell)) + 1):
                    self.bins.setdefault((ix, iy), []).append(i)

    def query(self, x0, x1, y0, y1):
        c, seen = self.cell, set()
        for ix in range(int(math.floor(x0 / c)), int(math.floor(x1 / c)) + 1):
            for iy in range(int(math.floor(y0 / c)), int(math.floor(y1 / c)) + 1):
                for i in self.bins.get((ix, iy), ()):
                    seen.add(i)
        return seen


def tri_box(a, b, c, bc, bh):
    """Akenine-Moller triangle / AABB overlap.  bc=box centre, bh=half extents."""
    v0 = a - bc; v1 = b - bc; v2 = c - bc
    # 3 box axes
    for i in range(3):
        lo = min(v0[i], v1[i], v2[i]); hi = max(v0[i], v1[i], v2[i])
        if lo > bh[i] or hi < -bh[i]:
            return False
    e = (v1 - v0, v2 - v1, v0 - v2)
    n = e[0].cross(e[1])
    # triangle plane
    r = bh[0] * abs(n.x) + bh[1] * abs(n.y) + bh[2] * abs(n.z)
    d = n.dot(v0)
    if d > r or d < -r:
        return False
    # 9 cross-product axes
    vs = (v0, v1, v2)
    for ei in e:
        for ax in range(3):
            if ax == 0:
                ax_v = Vector((0.0, -ei.z, ei.y))
            elif ax == 1:
                ax_v = Vector((ei.z, 0.0, -ei.x))
            else:
                ax_v = Vector((-ei.y, ei.x, 0.0))
            if ax_v.length_squared < 1e-12:
                continue
            p = [ax_v.dot(v) for v in vs]
            rr = (bh[0] * abs(ax_v.x) + bh[1] * abs(ax_v.y) + bh[2] * abs(ax_v.z))
            if min(p) > rr or max(p) < -rr:
                return False
    return True


# ---------------------------------------------------------------- scene split
def solid_objects():
    """Exactly the meshes interior_export.py leaves in the runtime GLB, minus the
    walk_ floors (which are floors, not walls)."""
    vl = set(bpy.context.view_layer.objects.keys())
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        n = o.name.lower()
        if (not o.visible_camera) or o.hide_render or o.hide_viewport:
            continue
        if o.name not in vl:
            continue          # view-layer-excluded (KIT_SOURCE rack) — stripped on export
        if any(n.startswith(p.lower()) for p in SKIP_PREFIX):
            continue
        if any(s in n for s in SKIP_SUBSTR):
            continue
        out.append(o)
    return out


def is_structure(name, room=None):
    n = name.lower()
    pats = COMMON_PROTECT + tuple(PROTECT.get(room, ()))
    return any(p in n for p in pats)


def tri_structure(room, name, a, b, c):
    """Structure = the room's bones (never moved by this pass)."""
    if is_structure(name, room):
        return True
    cx = (a.x + b.x + c.x) / 3.0; cy = (a.y + b.y + c.y) / 3.0; cz = (a.z + b.z + c.z) / 3.0
    for nm, x0, x1, y0, y1, z0, z1 in PROTECT_BOX.get(room, ()):
        if nm == name and x0 <= cx <= x1 and y0 <= cy <= y1 and z0 <= cz <= z1:
            return True
    return False


def floor_bvh():
    verts, faces = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.lower().startswith('walk_'):
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        base = len(verts)
        mw = o.matrix_world
        verts += [mw @ v.co for v in me.vertices]
        faces += [tuple(base + i for i in t.vertices) for t in me.loop_triangles]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, faces, all_triangles=True) if faces else None


# ------------------------------------------------------------------ the audit
def pads():
    out = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.lower().startswith('walk_pad'):
            vs = [o.matrix_world @ Vector(c) for c in o.bound_box]
            out[o.name] = (sum(v.x for v in vs) / 8.0, sum(v.y for v in vs) / 8.0)
    return out


def run_audit(room, verbose=True):
    objs = solid_objects()
    tris = world_tris(objs)
    th = TriHash(tris)
    fb = floor_bvh()

    P = pads()
    feats = FEATURES.get(room, [])
    anchors = list(P.values()) + [tuple(f[1:3]) for f in feats]
    names = list(P.keys()) + [f[0] for f in feats]

    # room bounds from the walk floor
    fx0 = fy0 = 1e9; fx1 = fy1 = -1e9
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.lower().startswith('walk_floor'):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                fx0 = min(fx0, w.x); fx1 = max(fx1, w.x)
                fy0 = min(fy0, w.y); fy1 = max(fy1, w.y)

    def floor_z(x, y):
        if fb is None:
            return 0.0
        hit = fb.ray_cast(Vector((x, y, 8.0)), Vector((0, 0, -1)), 20.0)
        return hit[0].z if hit and hit[0] else None

    # per-TRIANGLE structure flag: a joined dressing blob can be part wall-coat
    # (bones) and part floor trunk (clutter), so the split cannot be per-object.
    tstruct = [tri_structure(room, t[3], t[0], t[1], t[2]) for t in tris]

    def hits(x, y, fz, lo):
        """(clutter names, structure names) whose triangles intersect the body box."""
        bc = Vector((x, y, fz + (lo + BODY_H) / 2.0))
        bh = (BODY_R, BODY_R, (BODY_H - lo) / 2.0)
        clut, stru = set(), set()
        for i in th.query(x - BODY_R, x + BODY_R, y - BODY_R, y + BODY_R):
            a, b, c, nm = tris[i]
            if nm in (stru if tstruct[i] else clut):
                continue
            if tri_box(a, b, c, bc, bh):
                (stru if tstruct[i] else clut).add(nm)
        return clut, stru

    # --- free map over the whole floor (structure only) -> lane routing -------
    nx = int((fx1 - fx0) / GRID) + 1
    ny = int((fy1 - fy0) / GRID) + 1
    struct_tris = [i for i, t in enumerate(tris) if tstruct[i]]
    sh = TriHash([tris[i] for i in struct_tris]) if struct_tris else None
    stris = [tris[i] for i in struct_tris]

    def struct_free(x, y, fz):
        bc = Vector((x, y, fz + (LO_HARD + BODY_H) / 2.0))
        bh = (BODY_R, BODY_R, (BODY_H - LO_HARD) / 2.0)
        for i in sh.query(x - BODY_R, x + BODY_R, y - BODY_R, y + BODY_R):
            a, b, c, _n = stris[i]
            if tri_box(a, b, c, bc, bh):
                return False
        return True

    fz_map, free = {}, {}
    for ix in range(nx):
        for iy in range(ny):
            x = fx0 + ix * GRID; y = fy0 + iy * GRID
            fz = floor_z(x, y)
            fz_map[(ix, iy)] = fz
            free[(ix, iy)] = (fz is not None) and struct_free(x, y, fz)

    def cell(x, y):
        return (int(round((x - fx0) / GRID)), int(round((y - fy0) / GRID)))

    def nearest_free(c):
        if free.get(c):
            return c
        for rad in range(1, 14):
            best = None
            for dx in range(-rad, rad + 1):
                for dy in range(-rad, rad + 1):
                    if max(abs(dx), abs(dy)) != rad:
                        continue
                    q = (c[0] + dx, c[1] + dy)
                    if free.get(q):
                        d = dx * dx + dy * dy
                        if best is None or d < best[0]:
                            best = (d, q)
            if best:
                return best[1]
        return None

    def bfs_path(a, b):
        a = nearest_free(a); b = nearest_free(b)
        if not a or not b:
            return []
        prev = {a: None}; q = [a]
        while q:
            nq = []
            for c in q:
                if c == b:
                    p, out = c, []
                    while p:
                        out.append(p); p = prev[p]
                    return out[::-1]
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    n2 = (c[0] + d[0], c[1] + d[1])
                    if n2 in prev or not free.get(n2):
                        continue
                    prev[n2] = c; nq.append(n2)
            q = nq
        return []

    # --- build the zone ------------------------------------------------------
    zone = set()
    pad_r_cells = int(math.ceil(PAD_R / GRID))
    for (ax, ay) in anchors:
        c = cell(ax, ay)
        for dx in range(-pad_r_cells, pad_r_cells + 1):
            for dy in range(-pad_r_cells, pad_r_cells + 1):
                if (dx * dx + dy * dy) * GRID * GRID <= PAD_R * PAD_R:
                    q = (c[0] + dx, c[1] + dy)
                    if 0 <= q[0] < nx and 0 <= q[1] < ny and fz_map.get(q) is not None:
                        zone.add(q)
    lane_r = int(math.ceil((LANE_W / 2.0) / GRID))
    if anchors:
        a0 = anchors[0]
        for a in anchors[1:]:
            for c in bfs_path(cell(*a0), cell(*a)):
                for dx in range(-lane_r, lane_r + 1):
                    for dy in range(-lane_r, lane_r + 1):
                        if dx * dx + dy * dy <= lane_r * lane_r:
                            q = (c[0] + dx, c[1] + dy)
                            if 0 <= q[0] < nx and 0 <= q[1] < ny and fz_map.get(q) is not None:
                                zone.add(q)

    # --- sample --------------------------------------------------------------
    res = {"room": room, "zone_samples": len(zone), "anchors": dict(zip(names, anchors))}
    realfree = {}
    for tag, lo in (("hard", LO_HARD), ("full", LO_FULL)):
        blocked_struct = 0
        blocked_clutter = 0
        by_obj = {}
        pts = []
        for c in sorted(zone):
            x = fx0 + c[0] * GRID; y = fy0 + c[1] * GRID
            fz = fz_map[c]
            clut, stru = hits(x, y, fz, lo)
            if clut:
                blocked_clutter += 1
                for n in sorted(clut):
                    by_obj[n] = by_obj.get(n, 0) + 1
                pts.append([round(x, 2), round(y, 2), sorted(clut)[0]])
            elif stru:
                blocked_struct += 1
                for n in stru:
                    by_obj["[S]" + n] = by_obj.get("[S]" + n, 0) + 1
        res[tag] = {"clutter": blocked_clutter, "structure": blocked_struct,
                    "by_obj": dict(sorted(by_obj.items(), key=lambda kv: -kv[1])),
                    "pts": pts}

    # --- reachability: can a 0.30 body actually walk between the anchors? -----
    rnx = int((fx1 - fx0) / REACH_GRID) + 1
    rny = int((fy1 - fy0) / REACH_GRID) + 1
    for ix in range(rnx):
        for iy in range(rny):
            x = fx0 + ix * REACH_GRID; y = fy0 + iy * REACH_GRID
            fz = floor_z(x, y)
            if fz is None:
                realfree[(ix, iy)] = False
                continue
            clut, stru = hits(x, y, fz, LO_HARD)
            realfree[(ix, iy)] = not (clut or stru)

    def rcell(x, y):
        return (int(round((x - fx0) / REACH_GRID)), int(round((y - fy0) / REACH_GRID)))

    start = None
    for ax, ay in anchors:
        c = nearest_free_map(realfree, rcell(ax, ay), 4)
        if c:
            start = c; break
    reach = {}
    if start:
        seen = {start}; q = [start]
        while q:
            nq = []
            for c in q:
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n2 = (c[0] + d[0], c[1] + d[1])
                    if n2 not in seen and realfree.get(n2):
                        seen.add(n2); nq.append(n2)
            q = nq
        for n, (ax, ay) in zip(names, anchors):
            nf = nearest_free_map(realfree, rcell(ax, ay), 4)
            reach[n] = bool(nf and nf in seen)
    res["reach"] = reach
    res["free_cells"] = sum(1 for v in realfree.values() if v)

    if verbose:
        print("=== CIRC AUDIT %s  zone=%d samples (%.1f m2)" %
              (room, len(zone), len(zone) * GRID * GRID))
        print("    anchors:", ", ".join("%s(%.2f,%.2f)" % (n, a[0], a[1])
                                        for n, a in zip(names, anchors)))
        print("    reachable:", reach, " free floor cells:", res["free_cells"])
        for tag in ("hard", "full"):
            d = res[tag]
            print("    %-5s blocked: clutter=%-4d structure=%-4d" % (tag, d["clutter"], d["structure"]))
            for n, c in list(d["by_obj"].items())[:20]:
                print("        %-30s %d" % (n, c))
        if verbose == 2:
            for tag in ("hard", "full"):
                print("    %s offending points:" % tag)
                for p in res[tag]["pts"][:500]:
                    print("        (%6.2f,%6.2f) %s" % (p[0], p[1], p[2]))
    return res


def nearest_free_map(fm, c, rad_max):
    for rad in range(0, rad_max + 1):
        for dx in range(-rad, rad + 1):
            for dy in range(-rad, rad + 1):
                if max(abs(dx), abs(dy)) != rad:
                    continue
                q = (c[0] + dx, c[1] + dy)
                if fm.get(q):
                    return q
    return None


# -------------------------------------------------------------------- editing
def _obj(n):
    return bpy.data.objects.get(n)


def _islands(ob):
    """[(indices, bbox_world)] loose parts of ob, in world space."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen = set(); out = []
    mw = ob.matrix_world
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; grp = []
        seen.add(v.index)
        while stack:
            u = stack.pop(); grp.append(u.index)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index); stack.append(w)
        ws = [mw @ bm.verts[i].co for i in grp]
        bb = (min(p.x for p in ws), max(p.x for p in ws),
              min(p.y for p in ws), max(p.y for p in ws),
              min(p.z for p in ws), max(p.z for p in ws))
        out.append((grp, bb))
    bm.free()
    return out


def _apply_edits(room):
    """ops:
       {op:move,   obj:NAME, delta:[dx,dy,dz]}            whole object
       {op:delete, obj:NAME}
       {op:island, obj:NAME, box:[x0,x1,y0,y1,z0,z1], action:move|delete,
                   delta:[dx,dy,dz]}   loose parts whose bbox CENTRE is in box
    """
    log = {"moved": 0, "lifted": 0, "deleted": 0, "islands_moved": 0,
           "islands_deleted": 0, "detail": []}
    for op in EDITS.get(room, []):
        kind = op["op"]
        ob = _obj(op["obj"])
        if ob is None:
            log["detail"].append("MISSING %s" % op["obj"]); continue
        if kind == "delete":
            log["deleted"] += 1
            log["detail"].append("delete %s (%s)" % (ob.name, op.get("why", "")))
            bpy.data.objects.remove(ob, do_unlink=True)
        elif kind == "move":
            d = Vector(op["delta"])
            ob.location = ob.location + d
            if abs(d.z) > 0.05:
                log["lifted"] += 1
            else:
                log["moved"] += 1
            log["detail"].append("%s %s by (%.2f,%.2f,%.2f) (%s)" %
                                 ("lift" if abs(d.z) > 0.05 else "move", ob.name,
                                  d.x, d.y, d.z, op.get("why", "")))
        elif kind == "island":
            x0, x1, y0, y1, z0, z1 = op["box"]
            isl = _islands(ob)
            pick = []
            for grp, bb in isl:
                cx = (bb[0] + bb[1]) / 2.0; cy = (bb[2] + bb[3]) / 2.0
                if x0 <= cx <= x1 and y0 <= cy <= y1 and z0 <= bb[4] and bb[4] <= z1:
                    pick.append((grp, bb))
            if not pick:
                log["detail"].append("island %s in %s: none found" % (op["action"], ob.name))
                continue
            bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
            idx = set()
            for grp, _bb in pick:
                idx |= set(grp)
            if op["action"] == "delete":
                bmesh.ops.delete(bm, geom=[bm.verts[i] for i in idx], context='VERTS')
                log["islands_deleted"] += len(pick)
            else:
                mwi = ob.matrix_world.inverted()
                d = mwi.to_3x3() @ Vector(op["delta"])
                for i in idx:
                    bm.verts[i].co = bm.verts[i].co + d
                log["islands_moved"] += len(pick)
            bm.to_mesh(ob.data); bm.free(); ob.data.update()
            log["detail"].append("island %s x%d in %s (%s)" %
                                 (op["action"], len(pick), ob.name, op.get("why", "")))
    return log


# ----------------------------------------------------------------------- main
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    room = argv[0]
    do_fix = "--fix" in argv
    do_save = "--save" in argv
    jpath = argv[argv.index("--json") + 1] if "--json" in argv else None
    quiet = "--quiet" in argv
    verb = 0 if quiet else (2 if "--points" in argv else 1)

    before = run_audit(room, verbose=verb)
    out = {"before": before}
    if do_fix:
        log = _apply_edits(room)
        print("--- EDITS", json.dumps({k: v for k, v in log.items() if k != "detail"}))
        for d in log["detail"]:
            print("    ", d)
        after = run_audit(room, verbose=verb)
        out["after"] = after
        out["log"] = log
        print("=== %s  hard %d -> %d | full %d -> %d (clutter blocks in zone)" %
              (room, before["hard"]["clutter"], after["hard"]["clutter"],
               before["full"]["clutter"], after["full"]["clutter"]))
        if do_save:
            bpy.ops.wm.save_mainfile()
            print("SAVED", bpy.data.filepath)
    if jpath:
        with open(jpath, "w") as f:
            json.dump(out, f, indent=1)


# EDITS / FEATURES live in a sidecar so the table can be iterated without
# touching the harness.
_side = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interior_circulation_plan.py")
if os.path.exists(_side):
    _g = {}
    exec(compile(open(_side).read(), _side, "exec"), _g)
    FEATURES.update(_g.get("FEATURES", {}))
    PROTECT.update(_g.get("PROTECT", {}))
    PROTECT_BOX.update(_g.get("PROTECT_BOX", {}))
    EDITS.update(_g.get("EDITS", {}))

if __name__ == "__main__":
    main()
