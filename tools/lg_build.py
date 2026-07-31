"""lg_build.py — the LEGIBILITY PASS (bucket 1 / bucket 4), town custodian.

  Blender -b tools/blends/dellhollow-master.blend -P tools/lg_build.py \
      --python-exit-code 1 -- save

Work assigned by the coordinator off the legibility auditor's 17-shot audit
(`docs/qa/review/legibility-audit.html`, measured coordinates in
`docs/qa/review/probe/*.json`).  ADDITIVE ONLY: every object is `lg_*` and lives in
`DIST_legibility`.  No `walk_*`/`bar_*` mesh is touched — bucket 1 is VISIBLE
geometry only until the coordinator lands a versioned walk-QA re-baseline.

Sections, one per assignment:
  1  KEEPERS' STEPS (item 3, bucket 4).  The worst shot in the audit: "the
     eight-metre flight at cottage-steps is disconnected floating plank slabs;
     there is no stair in frame."

WHY THAT SHOT LOOKS LIKE THAT, measured before building anything: the walk
topology there is already a PROPER STAIR — 22 individual tread faces
(`walk_e_keepers-cottage__lock-five_l0_t00..l3_t03`, 0.14 m thick, ~0.37 m of rise
apart) and three landings — and every one of them is `hide_render = True`.  So the
collision is right, the art is absent, and the only things rendering in that frame
are the eight `bar_*_railA/B` boxes: four pairs of rails standing in mid-air with
no flight between them.  That is exactly what the audit saw.  This section lays the
flight the rails were always for: treads, risers, stringers, landings, legs founded
by ray-cast on `lf_ground`/`lf_planking`.

The machinery here (walk-face model, corridor guard, ray founding, clear-run beams)
is the same as `tools/lk_build.py`'s, deliberately compact.  IF A THIRD PLACE NEEDS
IT, FACTOR IT OUT into a shared district library rather than copying a third time —
that is a real debt and it is recorded in the report and the DAYLOG.
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (stable_hash, REPO, new_mesh, join_meshes, box, obox, beam, cyl, link, coll,
                          M, world_bbox, dist_poly2, point_in_poly, plane_z_fn, plank_fill)

SAVE = "save" in sys.argv
COLL = "DIST_legibility"
CORRIDOR_H = 2.05
DROP = 0.030                 # art this far under the walk plane (finding 90)
rng = random.Random(20260730)
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-26s %s" % (kind, what, why))


print("=" * 78)
print("LEGIBILITY PASS  —  bucket 1 / bucket 4, from the auditor's measurements")
print("=" * 78)

# ---------------------------------------------------------------- materials
# `derive()` by name returns the existing datablock, so the town's glTF-proven
# families cost nothing to reuse and nothing procedural reaches export.
def derive(src, name, scale=None, tint=None, fac=0.85, mode='MULTIPLY'):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials[src].copy()
    m.name = name
    m.use_fake_user = True
    nt = m.node_tree
    if scale:
        for n in nt.nodes:
            if n.type == 'MAPPING':
                n.inputs['Scale'].default_value = (scale, scale, scale)
    if tint:
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        sock = bsdf.inputs["Base Color"]
        if sock.is_linked:
            up = sock.links[0].from_socket
            nt.links.remove(sock.links[0])
            mx = nt.nodes.new('ShaderNodeMix')
            mx.data_type = 'RGBA'
            mx.blend_type = mode
            mx.inputs[0].default_value = fac
            mx.inputs[7].default_value = (*tint, 1.0)
            nt.links.new(up, mx.inputs[6])
            nt.links.new(mx.outputs[2], sock)
    return m


MDECKB = derive("mat_deck", "mat_qm_deck", scale=1.55, tint=(0.62, 0.55, 0.44))
MSTONE = derive("mat_rock", "mat_qm_stone", scale=2.05, tint=(0.50, 0.51, 0.56))
MTD, MIRON = M("mat_timber_dark"), M("mat_iron")

coll(COLL)
killed = 0
# THE LAMP NAMESPACE IS `KEYLG_`, AND THE FIRST DRAFT'S `KEYG_` WOULD HAVE DELETED
# THE GATE DISTRICT.  `KEYG_` is the GATE tier's own lamp prefix — 16 lights,
# including every lantern on the arch — and this idempotent clear pass would have
# removed all of them on the first run.  Caught by a dry run; the lesson is that a
# rebuild pass must own its prefix, and a two-letter prefix is not ownership.
for o in list(bpy.data.objects):
    if o.name.startswith(("lg_", "veg_lg_", "KEYLG_")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
for d in list(bpy.data.lights):
    if d.name.startswith("KEYLG_") and d.users == 0:
        bpy.data.lights.remove(d)
if killed:
    log("REBUILD", "%d objects cleared" % killed, "idempotent re-run")

# =========================================================================
# measurement — the same contract as lk_build.py
# =========================================================================
# THE GUARD'S REGION MUST COVER EVERY SECTION IN THIS FILE.  The first cut scoped
# it to the Keepers' Steps alone, so when section 2 started placing rail posts in
# the Weave — 30 metres west — `FACES` was empty there and `free_box()` cheerfully
# approved everything, which is a guard that answers "yes" instead of a guard.
REGION = (40.0, 100.0, 10.0, 34.0)


class Face:
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


# THE GUARD IS BUILT FROM `walk_` FACES ONLY, and that is not laziness.  The
# master's gate samples down-rays over `walk_` faces and merely ACCEPTS a hit on a
# `bar_` mesh as canonical; it never rays a `bar_` face.  So a bar_ rail imposes no
# constraint on new geometry — which matters here, because the visible rails this
# section builds stand exactly where the blockout rails are.
FACES = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith("walk_"):
        continue
    b = world_bbox(o)
    if b[1] < REGION[0] - 3 or b[0] > REGION[1] + 3 or b[3] < REGION[2] - 3 or b[2] > REGION[3] + 3:
        continue
    Mx = o.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    for p in o.data.polygons:
        if (N @ p.normal).normalized().z <= 0.5:
            continue
        FACES.append(Face([Mx @ o.data.vertices[i].co for i in p.vertices], o.name))


def eff_top(x, y):
    best = None
    for f in FACES:
        if point_in_poly(x, y, f.poly):
            z = f.at(x, y)
            if best is None or z > best:
                best = z
    return best


def free_box(x0, x1, y0, y1, z0, z1, pad=0.08, h=CORRIDOR_H):
    """A solid may overlap a walk polygon in plan only if it is wholly BELOW that
    face or more than `h` above it (finding 93 + the master's headroom check)."""
    sx = max(3, int((x1 - x0) / 0.22) + 1)
    sy = max(3, int((y1 - y0) / 0.22) + 1)
    pts = [(x0 + (x1 - x0) * i / (sx - 1.0), y0 + (y1 - y0) * j / (sy - 1.0))
           for i in range(sx) for j in range(sy)]
    for f in FACES:
        for q in f.poly:
            if x0 - pad <= q.x <= x1 + pad and y0 - pad <= q.y <= y1 + pad:
                t = f.at(q.x, q.y)
                e = eff_top(q.x, q.y)
                if not (e is not None and e > t + 0.05) and z1 > t - 0.03 and z0 < t + h:
                    return False
        for (x, y) in pts:
            px, py, d = nearest_on_poly(x, y, f.poly)
            if d > pad:
                continue
            t = f.at(px, py)
            e = eff_top(px, py)
            if e is not None and e > t + 0.05:
                continue
            if z1 > t - 0.03 and z0 < t + h:
                return False
    return True


def bvh_of(pred):
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


GBVH = bvh_of(lambda n: n.startswith(("lf_ground", "lf_planking", "lf_joists",
                                      "lf_lock_wall", "lf_gate_recess")))
KBVH = bvh_of(lambda n: n.startswith(("lf_ladder_iron", "e_lockhead__", "lf_clut",
                                      "lf_lantern", "lf_bollard", "lf_gate_upper",
                                      "lf_lock_gangbeam", "veg_")))


def gz(x, y, from_z=20.0):
    hit = GBVH.ray_cast(Vector((x, y, from_z)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else None


def clear_of(a, b, r=0.16):
    if KBVH is None:
        return True
    a, b = Vector(a), Vector(b)
    n = max(2, int((b - a).length / 0.22) + 1)
    for i in range(n + 1):
        loc = KBVH.find_nearest(a.lerp(b, i / float(n)), r)[0]
        if loc is not None:
            return False
    return True


npost = nrake = nfail = 0


def found(x, y, ztop, r=0.10, post_max=5.4, rake_max=3.2, cname=COLL):
    """Carry (x, y, ztop) down to real ground: post first, raking strut second,
    nothing third — and nothing is COUNTED, never faked."""
    global npost, nrake, nfail
    g = gz(x, y)
    if g is not None and 0.25 < ztop - g <= post_max and clear_of((x, y, g), (x, y, ztop)):
        npost += 1
        p = cyl("po", (x, y, g - 0.16), (x, y, ztop), r, 8, MTD, cname)
        return [p] if p else []
    for k in range(1, 14):
        s = 0.30 * k
        if s > rake_max:
            break
        for (dx, dy) in ((0, -s), (0, s), (-s, 0), (s, 0)):
            gg = gz(x + dx, y + dy)
            if gg is not None and gg >= ztop - s - 0.10 and gg < ztop - 0.20 \
                    and clear_of((x, y, ztop), (x + dx, y + dy, gg - 0.10)):
                nrake += 1
                p = cyl("ra", (x, y, ztop), (x + dx, y + dy, gg - 0.14), r * 0.9, 7,
                        MTD, cname)
                return [p] if p else []
    nfail += 1
    return []


# =========================================================================
# 1. THE KEEPERS' STEPS — the flight the rails were always for
# =========================================================================
# `walk_e_keepers-cottage__lock-five_*` is a real stair in collision: four flights
# of individual TREAD faces (l0 has 7, l1 5, l2 5, l3 4) and three landings, all
# render-hidden, dropping 7.90 -> 0.28 over 8 metres of fall between the Keepers'
# Cottage and Lock Five.  Nothing was ever built on it, so the shot shows four
# pairs of `bar_` rails in mid-air.  Everything below is placed off those faces'
# OWN planes; not one number here is authored.
STEP_PREFIX = "walk_e_keepers-cottage__lock-five_"
treads, landings = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(STEP_PREFIX):
        continue
    Mx = o.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    for p in o.data.polygons:
        if (N @ p.normal).normalized().z <= 0.5:
            continue
        poly = [Mx @ o.data.vertices[i].co for i in p.vertices]
        (landings if "landing" in o.name else treads).append((o.name, poly))
        break
treads.sort(key=lambda t: -sum(q.z for q in t[1]) / 4.0)
landings.sort(key=lambda t: -sum(q.z for q in t[1]) / 4.0)
log("READ", "%d treads, %d landings" % (len(treads), len(landings)),
    "z %.2f..%.2f — the flight exists in collision and was never built"
    % (min(q.z for _n, pl in treads for q in pl),
       max(q.z for _n, pl in treads for q in pl)))

tparts, fparts = [], []
ntread = nriser = 0
# flights, grouped by the ribbon leg in the name (l0..l3)
legs = {}
for nm, poly in treads:
    legs.setdefault(nm.split("_t")[0], []).append((nm, poly))

for legname, items in sorted(legs.items()):
    items.sort(key=lambda t: -sum(q.z for q in t[1]) / 4.0)
    # the flight's own direction, taken from its first and last tread
    c0 = sum(items[0][1], Vector((0, 0, 0))) / 4
    c1 = sum(items[-1][1], Vector((0, 0, 0))) / 4
    D = Vector((c1.x - c0.x, c1.y - c0.y, 0)).normalized()
    P = Vector((-D.y, D.x, 0))
    for k, (nm, poly) in enumerate(items):
        c = sum(poly, Vector((0, 0, 0))) / 4
        zfn = plane_z_fn(poly)
        ang = math.atan2(D.y, D.x)
        # THE TREAD IS THE WALK FACE, 30 mm down, in individual boards: the gate
        # rays each face at its own points, so a tread that covers its own face and
        # nothing else can never block a sample.
        V, F = plank_fill(poly, ang, w=0.26, gap=0.014, thick=0.14, drop=DROP,
                          zfn=zfn, seed=k * 5 + stable_hash(legname) % 97)
        if F:
            tparts.append(new_mesh("lg_ks_tread_%s_%02d" % (legname[-2:], k), V, F,
                                   MDECKB, COLL))
            ntread += 1
        # NO RISERS, AND THAT IS A MEASURED DECISION.  A riser closing the front of
        # each tread stands directly over the BACK of the tread below it, and these
        # treads overlap by only 0.05 m — so the lower face is not buried, the gate
        # rays it, and 16 samples came back blocked by the risers alone.  An
        # open-riser timber flight is what a waterside stair is anyway, and the
        # stringers under the treads are what give it its solidity in frame.
        hw = max(abs((q - c).dot(P)) for q in poly)
        ext = max(abs((q - c).dot(D)) for q in poly)
        nxt = items[k + 1][1] if k + 1 < len(items) else None
        low = (sum(nxt, Vector((0, 0, 0))) / 4).z if nxt else c.z - 0.38
        front = c + D * (ext - 0.03)
        top = zfn(front.x, front.y) - DROP - 0.14
        if top - low > 0.06 and free_box(min(front.x - hw, front.x + hw) - 0.05,
                                         max(front.x - hw, front.x + hw) + 0.05,
                                         min(front.y - hw, front.y + hw) - 0.05,
                                         max(front.y - hw, front.y + hw) + 0.05,
                                         low, top):
            rb = beam("ri", front + P * (hw - 0.06), front - P * (hw - 0.06),
                      0.05, top - low, MDECKB, COLL)
            if rb:
                rb.location.z += (low + top) / 2 - front.z
                fparts.append(rb)
                nriser += 1
    # two stringers under the flight, and a leg at each end of each
    for side in (+1, -1):
        hw = max(abs((q - (sum(pl, Vector((0, 0, 0))) / 4)).dot(P))
                 for _n, pl in items for q in pl)
        a = c0 + P * (side * (hw - 0.16))
        b = c1 + P * (side * (hw - 0.16))
        a.z = c0.z - 0.34
        b.z = c1.z - 0.34
        st = beam("st", a, b, 0.11, 0.30, MTD, COLL)
        if st:
            fparts.append(st)
        for q in (a, b):
            fparts += found(q.x, q.y, q.z - 0.12)

# the landings: a slab on each, with legs — they are where the flight turns, and
# they are what makes an 8 m fall read as a staircase rather than a ramp
nland = 0
for nm, poly in landings:
    zfn = plane_z_fn(poly)
    c = sum(poly, Vector((0, 0, 0))) / 4
    V, F = plank_fill(poly, math.pi / 4, w=0.28, gap=0.014, thick=0.16, drop=DROP,
                      zfn=zfn, seed=nland * 11 + 5)
    if F:
        tparts.append(new_mesh("lg_ks_landing_%d" % nland, V, F, MDECKB, COLL))
        nland += 1
    xs = [q.x for q in poly]
    ys = [q.y for q in poly]
    for (lx, ly) in ((min(xs) + 0.28, min(ys) + 0.28), (max(xs) - 0.28, min(ys) + 0.28),
                     (min(xs) + 0.28, max(ys) - 0.28), (max(xs) - 0.28, max(ys) - 0.28)):
        fparts += found(lx, ly, zfn(lx, ly) - 0.24, r=0.09)
    # a bearer frame under the slab so the legs have something to carry
    for (a, b) in (((min(xs) + 0.20, min(ys) + 0.28), (max(xs) - 0.20, min(ys) + 0.28)),
                   ((min(xs) + 0.20, max(ys) - 0.28), (max(xs) - 0.20, max(ys) - 0.28))):
        bm_ = beam("lb", (a[0], a[1], zfn(a[0], a[1]) - 0.26),
                   (b[0], b[1], zfn(b[0], b[1]) - 0.26), 0.10, 0.22, MTD, COLL)
        if bm_:
            fparts.append(bm_)

TREADS = join_meshes([p for p in tparts if p], "lg_ks_treads", COLL) if tparts else None
FRAME = join_meshes([p for p in fparts if p], "lg_ks_frame", COLL) if fparts else None
log("BUILD", "lg_ks_treads / lg_ks_frame",
    "%d tread runs + %d landings in individual boards, %d risers, stringers and "
    "%d posts + %d raking struts founded BY RAY on lf_ground/lf_planking (%d found "
    "nothing and were left unbuilt rather than floated)"
    % (ntread, nland, nriser, npost, nrake, nfail))

# =========================================================================
# 1b. THE RAILS THAT WERE THE "FLOATING PLANK SLABS"
# =========================================================================
# LOOK AT THE FIRST RECORD SHOT AND THE AUDIT'S SENTENCE STOPS BEING A METAPHOR:
# the four pale slabs hanging over the cliff in that frame are
# `bar_e_keepers-cottage__lock-five_l0..l3_railA/B` — eight 8-vertex blockout boxes,
# 2.4 m tall and 1.5 m long, standing on edge beside a flight that had no art.  They
# ARE the "disconnected floating plank slabs".  They are canonical topology so they
# may not be edited, but `hide_render` leaves them bit-identical (the 367/367 gate
# re-checks that every hidden one stays viewport-visible) and a real rail goes where
# each one stood: posts, a top rail, a midrail, following the box's own long axis.
BARS = [o for o in bpy.data.objects
        if o.type == 'MESH' and o.name.startswith("bar_e_keepers-cottage__lock-five")]
rparts = []
nrp = 0
for o in sorted(BARS, key=lambda o: o.name):
    b = world_bbox(o)
    if not o.hide_render:
        o.hide_render = True
        o.hide_viewport = False
    # the box's long axis in plan, and its two ends on that axis
    dx, dy = b[1] - b[0], b[3] - b[2]
    if dx >= dy:
        a0 = Vector((b[0] + 0.09, (b[2] + b[3]) / 2, b[4]))
        a1 = Vector((b[1] - 0.09, (b[2] + b[3]) / 2, b[4]))
    else:
        a0 = Vector(((b[0] + b[1]) / 2, b[2] + 0.09, b[4]))
        a1 = Vector(((b[0] + b[1]) / 2, b[3] - 0.09, b[4]))
    L = (a1 - a0).length
    n = max(2, int(L / 1.25) + 1)
    top = b[5] - 0.10                      # the blockout's own head height
    pts = []
    for k in range(n + 1):
        q = a0.lerp(a1, k / float(n))
        # the foot is the flight's own surface: a ray onto what this district just
        # built, so a post can never hang in the air beside its own stair
        hit = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),
                                         Vector((q.x, q.y, top + 0.2)),
                                         Vector((0, 0, -1)), distance=4.0)
        foot = hit[1].z if hit[0] else b[4]
        pts.append(Vector((q.x, q.y, foot)))
        rparts.append(obox("rp", q.x, q.y, (foot + top) / 2, 0.09, 0.09, top - foot,
                           mat=MTD, cname=COLL))
        nrp += 1
    for u, v in zip(pts, pts[1:]):
        for dz, w, h in ((0.0, 0.08, 0.07), (-0.42, 0.055, 0.05)):
            bm_ = beam("rl", Vector((u.x, u.y, top + dz)), Vector((v.x, v.y, top + dz)),
                       w, h, MTD, COLL)
            if bm_:
                rparts.append(bm_)
RAIL = join_meshes([p for p in rparts if p], "lg_ks_rail", COLL) if rparts else None
log("BUILD", "lg_ks_rail", "%d posts + top rail and midrail on the lines of %d "
    "blockout rails, which are now render-hidden (bit-identical, still "
    "viewport-visible so the GLB keeps their collision). Those eight boxes were "
    "the audit's 'disconnected floating plank slabs'." % (nrp, len(BARS)))

# =========================================================================
# 2. THE WEAVE RAILS — 19 measured unprotected drop edges
# =========================================================================
# `docs/qa/review/probe/weave.json`: the auditor's instrument walked the Weave's
# routes with a 2.5 m drop threshold and 0.9/1.4/2.0 m offsets and found 19 places
# where a player steps off into a 3.1..13.9 m fall — plus ONE BOTTOMLESS edge at
# runtime (59.69, 12.47, -18.14).  Bucket 1's rule from the plan: every drop edge
# is either railed or intentional, and nothing here is intentional (the ladder
# hatch at the lockhead is; a boardwalk edge over a 13.9 m fall is not).
#
# COORDINATE CONTRACT, and it is the one thing that will bite the next agent to
# read that file: the probe is RUNTIME space (x, y_up, z), the blend is
# (x, y_out, z_up), and they relate as  blend = (x, -z_runtime, y_runtime).
# Every conversion in this section is that one line.
WEAVE_PROBE = REPO + "/docs/qa/review/probe/weave.json"
wparts = []
nwp = nwskip = nwbr = 0
if os.path.exists(WEAVE_PROBE):
    drops = json.load(open(WEAVE_PROBE))["drops"]["list"]
    runs = {}
    for d in drops:
        key = (d["route"], d["side"])
        runs.setdefault(key, []).append(
            (Vector((d["edgeAt"][0], -d["edgeAt"][1], d["at"][1])),
             Vector((d["at"][0], -d["at"][2], d["at"][1])), d["fall"], d["bottomless"]))
    dg = bpy.context.evaluated_depsgraph_get()
    for (route, side), items in sorted(runs.items()):
        # order the run along the route so a rail chain follows the walk, not the
        # order the probe happened to emit
        items.sort(key=lambda t: (t[0].x, t[0].y))
        posts = []
        for (edge, at, fall, bottomless) in items:
            # the post stands INBOARD of the measured edge — the edge is where the
            # ground stops, and a post centred on it has half its section over air.
            toward = (at - edge)
            toward.z = 0
            if toward.length < 1e-6:
                continue
            toward.normalize()
            # INBOARD FIRST, THEN OUTBOARD ON A BRACKET.  These boardwalks are
            # narrow and walkable to their edge, so nine of nineteen posts had no
            # inboard room at all — the guard refused them, correctly.  A deck rail
            # in the real world is bolted to the OUTSIDE of the edge beam for
            # exactly that reason, and a bracket back to the deck is what carries it.
            deck_z = None
            hit0 = bpy.context.scene.ray_cast(dg, Vector((edge.x + toward.x * 0.30,
                                                          edge.y + toward.y * 0.30,
                                                          edge.z + 1.2)),
                                              Vector((0, 0, -1)), distance=2.4)
            if hit0[0]:
                deck_z = hit0[1].z
            placed, bracket = None, False
            for inb in (0.22, 0.34, 0.46):
                q = edge + toward * inb
                hit = bpy.context.scene.ray_cast(dg, Vector((q.x, q.y, edge.z + 1.2)),
                                                 Vector((0, 0, -1)), distance=2.4)
                if not hit[0]:
                    continue
                if not free_box(q.x - 0.08, q.x + 0.08, q.y - 0.08, q.y + 0.08,
                                hit[1].z - 0.10, hit[1].z + 1.06):
                    continue
                placed = Vector((q.x, q.y, hit[1].z))
                break
            if placed is None and deck_z is not None:
                for out in (0.10, 0.18, 0.26, 0.34, 0.44):
                    q = edge - toward * out
                    if free_box(q.x - 0.08, q.x + 0.08, q.y - 0.08, q.y + 0.08,
                                deck_z - 0.35, deck_z + 1.06):
                        placed = Vector((q.x, q.y, deck_z))
                        bracket = True
                        break
            if placed is None:
                nwskip += 1
                print("        UNRAILED edge (%.2f, %.2f) walkz %.2f fall %s  "
                      "deck under it: %s" % (edge.x, edge.y, edge.z, fall,
                                             "%.2f" % deck_z if deck_z is not None
                                             else "NONE — the ribbon has no art"))
                continue
            posts.append(placed)
            wparts.append(obox("wp", placed.x, placed.y, placed.z + 0.42, 0.10, 0.10,
                               1.28, mat=MTD, cname=COLL))
            nwp += 1
            if bracket:
                # ... and the bracket that carries it, back under the deck it hangs off
                b0 = Vector((placed.x, placed.y, placed.z - 0.30))
                b1 = Vector((placed.x + toward.x * 0.55, placed.y + toward.y * 0.55,
                             placed.z - 0.16))
                bm_ = beam("wb", b0, b1, 0.08, 0.12, MTD, COLL)
                if bm_:
                    wparts.append(bm_)
                nwbr += 1
        for u, v in zip(posts, posts[1:]):
            if (v - u).length > 3.4:      # do not span a gap the probe never measured
                continue
            for dz, w, h, mat in ((0.98, 0.085, 0.07, MTD), (0.54, 0.06, 0.05, MTD)):
                bm_ = beam("wr", u + Vector((0, 0, dz)), v + Vector((0, 0, dz)), w, h,
                           mat, COLL)
                if bm_:
                    wparts.append(bm_)
    RAILW = join_meshes([p for p in wparts if p], "lg_wv_rail", COLL) if wparts else None
    log("BUILD", "lg_wv_rail", "%d posts (%d of them OUTBOARD on brackets, because "
        "these boardwalks are walkable to their edge) covering %d of the auditor's "
        "%d measured drop edges; %d had neither inboard room nor a deck to bracket "
        "off and were left unbuilt rather than floated. Falls 3.1..13.9 m plus the "
        "bottomless edge at runtime (59.69, 12.47, -18.14)."
        % (nwp, nwbr, nwp, len(drops), nwskip))

# =========================================================================
# report
# =========================================================================
mine = [o for o in bpy.data.objects if o.name.startswith("lg_") and o.type == 'MESH']
if mine:
    bb = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
    nv = 0
    for o in mine:
        b = world_bbox(o)
        bb = [min(bb[0], b[0]), max(bb[1], b[1]), min(bb[2], b[2]), max(bb[3], b[3]),
              min(bb[4], b[4]), max(bb[5], b[5])]
        nv += len(o.data.vertices)
    print("\n" + "=" * 78)
    print("LEGIBILITY PASS — %d objects, %d verts, bounds x %.2f..%.2f y %.2f..%.2f "
          "z %.2f..%.2f" % (len(mine), nv, *bb))
    print("=" * 78)
    for o in sorted(mine, key=lambda o: o.name):
        b = world_bbox(o)
        print("  %-24s %6dv  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f"
              % (o.name, len(o.data.vertices), b[0], b[1], b[2], b[3], b[4], b[5]))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
