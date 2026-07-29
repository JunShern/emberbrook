"""boatyard_lib.py — shared helpers for the del-boatyard district build.

Coordinate contract
-------------------
Town coords: x = along-gorge (downstream +x, upstream -x), y = out from the town
cliff (0) toward the river (~34 centre), z = height.  The boatyard parcel is
x 2..32, y 19..33.  Water: mid pool z 0.2 (x>14), upstream pool z 3.6 (x<14).

Probe coords (tools/blends/probe.blend): the accepted v11 boatyard was modelled
in a local frame where +y = upstream and +x = screen-right.  The map from probe
to town is a +90 deg rotation about Z:  probe(x, y) -> town(-y, x).
That mapping preserves screen layout: the probe camera looked +y (upstream) and
sat at -y; the town camera looks -x (upstream) and sits at +x, and probe
screen-right (+x) becomes town screen-right (+y).  So harvested probe geometry
keeps the exact lighting/facing relationships that were art-approved in v11.
"""

import bpy, bmesh, math, random, os, json
from mathutils import Vector, Matrix

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
PROBE_BLEND = REPO + "/tools/blends/probe.blend"
KITLIB_BLEND = REPO + "/tools/blends/kitlib.blend"
REGION = ((2.0, 32.0), (19.0, 33.0), (-2.0, 8.0))

# probe -> town rotation
R90 = Matrix.Rotation(math.pi / 2, 4, 'Z')
# translation applied to "atmosphere" donors (lights / haze / backdrops) so the
# probe yard centre lands on the town yard centre.
T_YARD = Vector((9.0, 26.5, -0.9))

WATER_MID = 0.2
WATER_UP = 3.6
CORRIDOR_MARGIN = 0.30
CORRIDOR_HEIGHT = 2.0

rng = random.Random(20260729)


# ---------------------------------------------------------------- collections
def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def link(ob, cname):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll(cname).objects.link(ob)
    return ob


# ---------------------------------------------------------------- mesh basics
def new_mesh(name, verts, faces, mat=None, cname="BY_BUILD", smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(mat)
    link(ob, cname)
    return ob


def join_meshes(obs, name, cname="BY_BUILD"):
    """Merge a list of objects into one (keeps all material slots)."""
    obs = [o for o in obs if o and o.type == 'MESH']
    if not obs:
        return None
    bm = bmesh.new()
    mats = []
    for o in obs:
        me = o.data
        idx_map = {}
        for i, ms in enumerate(me.materials):
            if ms is None:
                idx_map[i] = 0
                continue
            if ms.name not in [m.name for m in mats]:
                mats.append(ms)
            idx_map[i] = [m.name for m in mats].index(ms.name)
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)
        for f in tmp.faces:
            f.material_index = idx_map.get(f.material_index, 0)
        m2 = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(m2)
        tmp.free()
        bm.from_mesh(m2)
        bpy.data.meshes.remove(m2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    link(ob, cname)
    for o in obs:
        bpy.data.objects.remove(o, do_unlink=True)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat=None, cname="BY_BUILD"):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return new_mesh(name, v, f, mat, cname)


def obox(name, cx, cy, cz, sx, sy, sz, rz=0.0, mat=None, cname="BY_BUILD"):
    """Oriented box centred at (cx,cy,cz), rotated rz about Z."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    c, s = math.cos(rz), math.sin(rz)
    pts = []
    for dz in (-hz, hz):
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            pts.append((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return new_mesh(name, pts, f, mat, cname)


def beam(name, a, b, w, h, mat=None, cname="BY_BUILD", roll=0.0):
    """Rectangular-section beam from a to b (Vectors)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-6:
        return None
    up = Vector((0, 0, 1))
    if abs(d.normalized().dot(up)) > 0.98:
        up = Vector((1, 0, 0))
    xa = d.normalized()
    ya = xa.cross(up).normalized()
    za = ya.cross(xa).normalized()
    if roll:
        cr, sr = math.cos(roll), math.sin(roll)
        ya, za = ya * cr + za * sr, -ya * sr + za * cr
    v = []
    for t in (0.0, 1.0):
        p = a + d * t
        for sy, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v.append(p + ya * (sy * w / 2) + za * (sz * h / 2))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return new_mesh(name, v, f, mat, cname)


def cyl(name, a, b, r, seg=10, mat=None, cname="BY_BUILD", r2=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-6:
        return None
    r2 = r if r2 is None else r2
    xa = d.normalized()
    up = Vector((0, 0, 1)) if abs(xa.z) < 0.95 else Vector((1, 0, 0))
    ya = xa.cross(up).normalized()
    za = ya.cross(xa).normalized()
    v, f = [], []
    for i in range(seg):
        th = 2 * math.pi * i / seg
        v.append(a + ya * (math.cos(th) * r) + za * (math.sin(th) * r))
    for i in range(seg):
        th = 2 * math.pi * i / seg
        v.append(b + ya * (math.cos(th) * r2) + za * (math.sin(th) * r2))
    for i in range(seg):
        j = (i + 1) % seg
        f.append((i, j, seg + j, seg + i))
    f.append(tuple(range(seg - 1, -1, -1)))
    f.append(tuple(range(seg, seg * 2)))
    return new_mesh(name, v, f, mat, cname, smooth=True)


# ------------------------------------------------------------ polygon helpers
def poly_area2(pts):
    n = len(pts)
    return sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) / 2


def offset_poly(pts, m):
    """Outward miter-offset of a (convex-ish) polygon by m in XY. pts: Vectors."""
    n = len(pts)
    ccw = poly_area2([(p.x, p.y) for p in pts]) > 0
    P = list(pts) if ccw else list(pts)[::-1]
    out = []
    for i in range(len(P)):
        prev, cur, nxt = P[i - 1], P[i], P[(i + 1) % len(P)]
        e1 = Vector((cur.x - prev.x, cur.y - prev.y))
        e2 = Vector((nxt.x - cur.x, nxt.y - cur.y))
        if e1.length < 1e-9:
            e1 = e2
        if e2.length < 1e-9:
            e2 = e1
        n1 = Vector((e1.y, -e1.x)).normalized()
        n2 = Vector((e2.y, -e2.x)).normalized()
        b = n1 + n2
        if b.length < 1e-6:
            b = n1
        b.normalize()
        L = m / max(b.dot(n1), 0.35)
        out.append(Vector((cur.x + b.x * L, cur.y + b.y * L, cur.z)))
    return out if ccw else out[::-1]


def dist_poly2(x, y, pts):
    """XY distance from (x,y) to a polygon (0 inside)."""
    if point_in_poly(x, y, pts):
        return 0.0
    best = 1e9
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i].x, pts[i].y
        bx, by = pts[(i + 1) % n].x, pts[(i + 1) % n].y
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py = ax + t * dx, ay + t * dy
        best = min(best, math.hypot(x - px, y - py))
    return best


def point_in_poly(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i].x, pts[i].y
        x2, y2 = pts[(i + 1) % n].x, pts[(i + 1) % n].y
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def clip_halfplane(poly, nx, ny, d):
    """Keep the part of poly with nx*x + ny*y <= d.  poly: list of Vector."""
    if not poly:
        return []
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        da = nx * a.x + ny * a.y - d
        db = nx * b.x + ny * b.y - d
        if da <= 0:
            out.append(a)
        if (da <= 0) != (db <= 0):
            t = da / (da - db)
            out.append(a.lerp(b, t))
    return out


def plane_z_fn(pts):
    """Least-squares plane z = a*x + b*y + c through the polygon's points."""
    n = len(pts)
    sx = sum(p.x for p in pts); sy = sum(p.y for p in pts); sz = sum(p.z for p in pts)
    sxx = sum(p.x * p.x for p in pts); syy = sum(p.y * p.y for p in pts)
    sxy = sum(p.x * p.y for p in pts)
    sxz = sum(p.x * p.z for p in pts); syz = sum(p.y * p.z for p in pts)
    A = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, float(n)]]
    B = [sxz, syz, sz]
    # gaussian elimination 3x3
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(A[r][i]))
        if abs(A[piv][i]) < 1e-9:
            zc = sz / n
            return lambda x, y, zc=zc: zc
        A[i], A[piv] = A[piv], A[i]
        B[i], B[piv] = B[piv], B[i]
        for r in range(i + 1, 3):
            f = A[r][i] / A[i][i]
            for c in range(i, 3):
                A[r][c] -= f * A[i][c]
            B[r] -= f * B[i]
    x3 = [0, 0, 0]
    for i in (2, 1, 0):
        s = B[i] - sum(A[i][c] * x3[c] for c in range(i + 1, 3))
        x3[i] = s / A[i][i]
    a, b, c = x3
    return lambda X, Y: a * X + b * Y + c


def plank_fill(poly, ang, w=0.30, gap=0.014, thick=0.10, jitter=0.014, drop=0.0,
               zfn=None, seed=0, keep=None):
    """Fill a convex polygon with individual plank boxes.

    poly : list of Vector (a top face outline, roughly planar)
    ang  : plank run direction in radians (XY)
    returns (verts, faces) of one merged mesh.
    """
    r = random.Random(seed)
    if zfn is None:
        zfn = plane_z_fn(poly)
    nx, ny = -math.sin(ang), math.cos(ang)          # across-plank axis
    ts = [p.x * nx + p.y * ny for p in poly]
    t0, t1 = min(ts) - 0.01, max(ts) + 0.01
    verts, faces = [], []
    t = t0
    k = 0
    while t < t1:
        te = t + w
        sub = clip_halfplane(poly, nx, ny, te - gap / 2)
        sub = clip_halfplane(sub, -nx, -ny, -(t + gap / 2))
        t = te
        k += 1
        if len(sub) < 3:
            continue
        cx = sum(p.x for p in sub) / len(sub)
        cy = sum(p.y for p in sub) / len(sub)
        if keep is not None:
            probes = [(cx, cy)] + [(q.x, q.y) for q in sub]
            for q in sub:
                probes.append(((q.x + cx) / 2, (q.y + cy) / 2))
            if not all(keep(px, py, zfn(px, py) - drop) for px, py in probes):
                continue
        dz = (r.random() - 0.5) * 2 * jitter - drop
        th = thick * (0.85 + 0.4 * r.random())
        base = len(verts)
        n = len(sub)
        for p in sub:
            verts.append((p.x, p.y, zfn(p.x, p.y) + dz))
        for p in sub:
            verts.append((p.x, p.y, zfn(p.x, p.y) + dz - th))
        faces.append(tuple(range(base, base + n)))
        faces.append(tuple(range(base + 2 * n - 1, base + n - 1, -1)))
        for i in range(n):
            j = (i + 1) % n
            faces.append((base + i, base + n + i, base + n + j, base + j))
    return verts, faces


# ---------------------------------------------------------------- harvesting
def harvest(path, objnames, want_materials=True, want_world=False):
    """Append named objects (+ all materials / world) from another blend."""
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        present = [n for n in objnames if n in src.objects]
        missing = [n for n in objnames if n not in src.objects]
        # NOTE: libraries.load rewrites the list object it is given in place, so
        # hand it a copy or `present` turns into a list of Objects.
        dst.objects = list(present)
        if want_materials:
            dst.materials = list(src.materials)
        if want_world:
            dst.worlds = list(src.worlds)
    got = {}
    for name, ob in zip(present, dst.objects):
        if ob is not None:
            got[name] = ob
    for name in present:
        if name not in got or got[name] is None:
            ob = bpy.data.objects.get(name)
            if ob is not None:
                got[name] = ob
    missing = missing + [n for n in present if n not in got]
    if missing:
        print("HARVEST MISSING from %s: %s" % (os.path.basename(path), missing))
    for m in bpy.data.materials:
        m.use_fake_user = True
    return got


def M(name):
    m = bpy.data.materials.get(name)
    if m is None:
        print("!! material missing:", name)
    return m


def reseat_slab(ob, ztop, thick):
    """Re-cut a water slab so its world TOP is exactly `ztop` and it is `thick` deep.

    A LEVEL from the map is a WORLD z, and a vertex coordinate is not: the town
    generator ships `water_pool-downstream` as a unit cube on an origin at z -1.8
    with a 0.2 z scale, so `v.co.z = level` puts the surface at
    `origin + 0.2 * level` — a metre high here — and any "split the mesh on its own
    mid-plane to stay idempotent" trick then re-splits the ALREADY-MOVED values and
    walks the slab further every run (this one had collapsed to a zero-thickness
    sheet at world -2.80 against a map level of -3.80).

    The cure is to stop straddling two spaces: keep the object's plan extent, drop
    it onto an IDENTITY transform and write world coordinates into the mesh, which
    is the form `water_pool-mid` and `lf_riverbed_tail` already have.  Absolute
    target, one space, idempotent from any starting state including a degenerate
    one — re-running is a no-op rather than another metre.
    """
    b = world_bbox(ob)
    x0, x1, y0, y1 = b[0], b[1], b[2], b[3]
    me = ob.data
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = ztop - thick if v.co.z < 0 else ztop
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob.matrix_basis.identity()
    return world_bbox(ob)


def world_bbox(ob):
    """Bounding box from live data — `ob.bound_box` / `ob.matrix_world` are only
    refreshed by a depsgraph evaluation, which never happens in a headless build."""
    Mx = ob.matrix_basis if ob.parent is None else ob.matrix_world
    if ob.type == 'MESH' and ob.data and len(ob.data.vertices):
        pts = [Mx @ v.co for v in ob.data.vertices]
    else:
        pts = [Mx @ Vector(c) for c in ob.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))


def group_bbox(obs):
    bs = [world_bbox(o) for o in obs if o.type == 'MESH']
    return (min(b[0] for b in bs), max(b[1] for b in bs),
            min(b[2] for b in bs), max(b[3] for b in bs),
            min(b[4] for b in bs), max(b[5] for b in bs))


def bake_group(srcs, rz=0.0, scale=(1.0, 1.0, 1.0), mirror_y=False, prefix="by_",
               cname="BY_BUILD"):
    """Copy probe objects and bake  S_town * Rz(90+rz) * (object transform)  into
    their mesh data, leaving an identity object transform so `ob.location` then
    positions the whole group rigidly.  Scale is expressed in TOWN axes.

    Object copies (not fresh objects) so BEVEL modifiers survive; `matrix_basis`
    rather than `matrix_world` so nothing depends on a depsgraph evaluation
    (there is none in a headless build)."""
    S = Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
    if mirror_y:
        S = S @ Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))
    Mr = S @ Matrix.Rotation(math.pi / 2 + rz, 4, 'Z')
    out = []
    for s in srcs:
        ob = s.copy()
        ob.data = s.data.copy() if s.data else None
        ob.name = prefix + s.name
        if ob.data:
            ob.data.name = prefix + s.name
        W = Mr @ s.matrix_basis
        if s.type == 'MESH':
            ob.data.transform(W)
            if mirror_y:
                ob.data.flip_normals()
            ob.matrix_basis = Matrix.Identity(4)
            ob.location = (0.0, 0.0, 0.0)
            ob.rotation_euler = (0.0, 0.0, 0.0)
            ob.scale = (1.0, 1.0, 1.0)
        else:
            ob.matrix_basis = W
        link(ob, cname)
        out.append(ob)
    return out


def move_group(obs, delta):
    d = Vector(delta)
    for o in obs:
        o.location = o.location + d


def anchor_group(obs, ref, target, mode="cxy_minz"):
    """Translate the whole group so that `ref`'s bbox anchor lands on target."""
    b = world_bbox(ref)
    cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
    if mode == "cxy_minz":
        cur = Vector((cx, cy, b[4]))
    elif mode == "cxy_cz":
        cur = Vector((cx, cy, (b[4] + b[5]) / 2))
    elif mode == "cxy_maxz":
        cur = Vector((cx, cy, b[5]))
    else:
        raise ValueError(mode)
    move_group(obs, Vector(target) - cur)


def place(src, target, rz=0.0, scale=1.0, mode="cxy_minz", name=None,
          cname="BY_BUILD", mirror_y=False):
    sc = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    obs = bake_group([src], rz=rz, scale=sc, mirror_y=mirror_y, prefix="", cname=cname)
    ob = obs[0]
    if name:
        ob.name = name
        if ob.data:
            ob.data.name = name
    if ob.type == 'MESH':
        anchor_group([ob], ob, target, mode)
    else:
        ob.location = Vector(target)
    return ob


# ------------------------------------------------------------- walk corridors
class Corridor:
    """Walkable-corridor model built from the preserved walk_* meshes."""

    def __init__(self, walk_objs, margin=CORRIDOR_MARGIN, height=CORRIDOR_HEIGHT):
        self.height = height
        self.tops = []      # (expanded_poly, plane_fn, raw_poly)
        for ob in walk_objs:
            Mx = ob.matrix_world
            N = Mx.to_3x3().inverted().transposed()
            for p in ob.data.polygons:
                if (N @ p.normal).normalized().z > 0.5:
                    raw = [Mx @ ob.data.vertices[i].co for i in p.vertices]
                    self.tops.append((offset_poly(raw, margin), plane_z_fn(raw), raw, ob.name))

    def top_at(self, x, y):
        best = None
        for poly, fn, raw, nm in self.tops:
            if point_in_poly(x, y, poly):
                z = fn(x, y)
                if best is None or z > best:
                    best = z
        return best

    def blocked(self, p):
        """True if point p sits in a walk corridor (between the effective walk
        surface and +height above it)."""
        t = self.top_at(p[0], p[1])
        if t is None:
            return False
        return t - 0.01 <= p[2] <= t + self.height

    def free(self, x, y, z=None):
        t = self.top_at(x, y)
        if t is None:
            return True
        if z is None:
            return False
        return not (t - 0.01 <= z <= t + self.height)

    def find_free(self, x, y, z, radius=2.4, step=0.2):
        """Nudge (x,y) outward until it is out of every corridor."""
        if self.free(x, y, z):
            return (x, y)
        r = step
        while r <= radius:
            for i in range(24):
                a = 2 * math.pi * i / 24
                nx, ny = x + math.cos(a) * r, y + math.sin(a) * r
                if self.free(nx, ny, z):
                    return (nx, ny)
            r += step
        return None
