"""district_lib.py — the walk-contract machinery a district build needs, ONCE.

RECORDED DEBT, DISCHARGED FOR NEW WORK.  `tools/lk_build.py` grew a walk-face
model, a corridor guard and a ray-founding helper; `tools/lg_build.py` copied them
verbatim and said so in its own docstring, and the coordinator's risk log made it
canon on 2026-07-30: "lg_build duplicates lk_build machinery — factor a shared
district library BEFORE a third copy."  This is the third place that needs it, so
this is the library.  `tools/ga_build.py` uses it and holds no copy of its own.

NOT MIGRATED IN THIS PASS, deliberately: `lk_build.py` and `lg_build.py` still
carry their own copies.  Their output is already IN the master and both are
accepted districts; swapping the guard under them is a change whose only honest
proof is a full re-run plus a re-gate of two districts, which is not this pass's
assignment.  The migration target now exists and the next builder to touch either
file should import from here and delete the copy.

WHAT THE GUARD IS FOR (finding 93 + the master's own headroom check): a solid may
overlap a walk polygon in plan only if it is wholly BELOW that face, or more than
CORRIDOR_H above it.  Anything else stands in the corridor a player walks down.

THE GUARD IS BUILT FROM `walk_` FACES ONLY, and that is not laziness: the master's
gate rays down over `walk_` faces and merely ACCEPTS a hit on a `bar_` mesh as
canonical — it never rays a `bar_` face.  A `bar_` blockout therefore imposes no
constraint on new geometry.

A GUARD MUST COVER EVERY PLACE ITS CALLER BUILDS.  lg_build shipped with its
region scoped to one section, so 30 m away `FACES` was empty and `free_box()`
cheerfully approved everything — a guard that answers "yes" is not a guard.
`WalkGuard.__init__` therefore takes the region explicitly and `free_box()` raises
if it is asked about a point outside the region it was built for.
"""
import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from boatyard_lib import point_in_poly, plane_z_fn, world_bbox

CORRIDOR_H = 2.05


class Face:
    """One upward-facing polygon of one `walk_` mesh, in world space."""
    __slots__ = ("poly", "fn", "zmin", "zmax", "name")

    def __init__(self, poly, name):
        self.poly = poly
        self.fn = plane_z_fn(poly)
        self.zmin = min(p.z for p in poly) - 0.02
        self.zmax = max(p.z for p in poly) + 0.02
        self.name = name

    def at(self, x, y):
        return min(max(self.fn(x, y), self.zmin), self.zmax)


def nearest_on_poly(x, y, pts):
    if point_in_poly(x, y, pts):
        return x, y, 0.0
    best, bp = 1e9, (x, y)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b.x - a.x, b.y - a.y
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - a.x) * dx + (y - a.y) * dy) / L2))
        px, py = a.x + t * dx, a.y + t * dy
        d = math.hypot(x - px, y - py)
        if d < best:
            best, bp = d, (px, py)
    return bp[0], bp[1], best


class WalkGuard:
    def __init__(self, region, corridor_h=CORRIDOR_H):
        self.region = region
        self.h = corridor_h
        self.faces = []
        for o in bpy.data.objects:
            if o.type != 'MESH' or not o.name.startswith("walk_"):
                continue
            b = world_bbox(o)
            if b[1] < region[0] - 3 or b[0] > region[1] + 3 \
                    or b[3] < region[2] - 3 or b[2] > region[3] + 3:
                continue
            Mx = o.matrix_world
            N = Mx.to_3x3().inverted().transposed()
            for p in o.data.polygons:
                if (N @ p.normal).normalized().z <= 0.5:
                    continue
                self.faces.append(Face([Mx @ o.data.vertices[i].co for i in p.vertices],
                                       o.name))

    def eff_top(self, x, y):
        """The HIGHEST walk face over (x, y): a face buried under another one is not
        the surface anybody walks on (manifest finding 36)."""
        best = None
        for f in self.faces:
            if point_in_poly(x, y, f.poly):
                z = f.at(x, y)
                if best is None or z > best:
                    best = z
        return best

    def free_box(self, x0, x1, y0, y1, z0, z1, pad=0.08):
        r = self.region
        assert r[0] - 3 <= x0 and x1 <= r[1] + 3 and r[2] - 3 <= y0 and y1 <= r[3] + 3, \
            ("free_box asked about (%.2f..%.2f, %.2f..%.2f), outside the region "
             "%s this guard was built for — widen the region or the guard is "
             "answering yes about faces it never loaded" % (x0, x1, y0, y1, r))
        sx = max(3, int((x1 - x0) / 0.22) + 1)
        sy = max(3, int((y1 - y0) / 0.22) + 1)
        pts = [(x0 + (x1 - x0) * i / (sx - 1.0), y0 + (y1 - y0) * j / (sy - 1.0))
               for i in range(sx) for j in range(sy)]
        for f in self.faces:
            for q in f.poly:
                if x0 - pad <= q.x <= x1 + pad and y0 - pad <= q.y <= y1 + pad:
                    t = f.at(q.x, q.y)
                    e = self.eff_top(q.x, q.y)
                    if not (e is not None and e > t + 0.05) and z1 > t - 0.03 and z0 < t + self.h:
                        return False
            for (x, y) in pts:
                px, py, d = nearest_on_poly(x, y, f.poly)
                if d > pad:
                    continue
                t = f.at(px, py)
                e = self.eff_top(px, py)
                if e is not None and e > t + 0.05:
                    continue
                if z1 > t - 0.03 and z0 < t + self.h:
                    return False
        return True


def bvh_of(pred):
    """A BVH over every mesh whose NAME passes `pred`, in world space."""
    verts, polys = [], []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not pred(o.name):
            continue
        Mx = o.matrix_world
        base = len(verts)
        verts.extend([Mx @ v.co for v in o.data.vertices])
        for p in o.data.polygons:
            polys.append([base + i for i in p.vertices])
    return BVHTree.FromPolygons(verts, polys, all_triangles=False) if polys else None


def ground_z(bvh, x, y, from_z=40.0, depth=60.0):
    """Where real ground is under (x, y), or None.  Nothing is ever FOUNDED on a
    guess: a station that finds nothing is left unbuilt and counted."""
    if bvh is None:
        return None
    hit = bvh.ray_cast(Vector((x, y, from_z)), Vector((0, 0, -1)), depth)
    return hit[0].z if hit[0] is not None else None


def clear_between(bvh, a, b, r=0.16):
    """True when a straight member from a to b runs through nothing solid."""
    if bvh is None:
        return True
    a, b = Vector(a), Vector(b)
    n = max(2, int((b - a).length / 0.22) + 1)
    for i in range(n + 1):
        if bvh.find_nearest(a.lerp(b, i / float(n)), r)[0] is not None:
            return False
    return True
