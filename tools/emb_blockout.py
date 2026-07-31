"""emb_blockout.py — RAISE THE WHOLE OF EMBERBROOK, GRAY, FROM ITS OWN MAP.

    Blender -b -P tools/emb_blockout.py --python-exit-code 1
    Blender -b -P tools/emb_blockout.py --python-exit-code 1 -- --map <rel> --out <abs>
    Blender -b -P tools/emb_blockout.py --python-exit-code 1 -- --digest --nosave

WHAT THIS IS.  `tools/town_blockout.py` is Dellhollow's equivalent and this is its
Emberbrook sibling rather than its fork: same contract (a townmap JSON in, a
deterministic gray scene out), same walk-mesh NAMING — which is the whole point,
because `tools/cine_regions.mjs` proves coverage by matching mesh names against map
records (`walk_pad_<landmark>`, `walk_lm_<landmark>`, `walk_e_<from>__<to>_*`).  Rename
a mesh here and the camera gate silently stops seeing a district.

WHY NOT JUST REUSE town_blockout.py.  Because half of it is Dellhollow's GORGE — a
river spec with pools, a dam wall, waterwheels, two cliff slabs.  Emberbrook has no
gorge; it has a rise, a brook, a pond, a river vista and a ring of wood.  The shared
half (landmark massing by class, threshold pads, chaikin path ribbons) is reproduced
faithfully; the Dellhollow half is replaced with this town's own context.  Merging the
two into one parameterised generator is real work and NOT this pass's assignment — it
is filed in the DAYLOG, with the note that a THIRD town is the trigger, exactly as
`district_lib.py` was created on the third copy of a walk guard.

DETERMINISM IS A GATE.  Two runs must produce identical geometry.  So: no `random`, no
time, no dict order that isn't the JSON's own, and no `bpy.ops` mesh primitives (their
vertex order has moved between Blender versions) — every mesh here is an explicit
vertex list.  The one place variation is wanted (the wooded rim) uses an integer hash
of the object's own index.  `-- --digest` prints a vertex digest for the gate to diff.

FOUR RULES THIS FILE EXISTS TO OBEY, each one paid for by something that went wrong:

 1  GROUND IS NOT WALKABLE.  `docs/plans/town-legibility.md`: *the walkmesh IS the
    route — you cannot fall off the path in Alexandria*.  Dellhollow's floors were
    built for coverage and the user could walk off them into out-of-bounds.  Here
    `emb_ground_*` is scenery and collision; the ONLY walkable surfaces are the
    `walk_` pads, area floors and ribbons derived from the map's own records.

 2  A LANDMARK'S COORDINATE IS THE BUILDING, NOT THE DOORSTEP.  town_blockout puts the
    massing and the `walk_pad_` at the same point, so every house in the town stands on
    its own doorstep — a solid in a walk corridor (finding 93), a camera probe inside a
    wall, and a road that ends in a chimney.  Here the doorstep is DERIVED: pushed out
    from the centre along the mean direction of the edges that arrive there, past the
    building's own half-depth.  Roads run doorstep to doorstep.

 3  NOTHING SOLID STANDS ON WALKABLE FLOOR.  The map puts the inn, the item shop, the
    notice board, the well and the Heartlight *inside* `square-plaza`'s 7 m radius.  A
    plain disc would be a walk surface with five solids on it.  Area floors are
    therefore grids of cells with the footprints cut out, emitted as ONE mesh each.

 4  NO WATER UNDER A ROAD, AND NO ROAD UNDER WATER.  The pond's authored extent
    overlaps the jetty and the north-shore path; the map's own note says *"the lane
    skirts it"*, so water is cut against a rasterised footprint of every walk mesh in
    the town and the lane's shore becomes a real shore.  Where a road crosses the brook
    a stone culvert is founded under it and REPORTED — a ribbon hovering over a stream
    reads as art until somebody walks it.

 5  NO ROAD UNDER THE GRASS EITHER.  The rise is interpolated from the map's anchors and
    the walk network is laid at the map's authored z; nothing made them agree.  Measured
    over the village entrance: 605 of 960 walk samples had ground ABOVE the walk top,
    worst 0.66 m.  A district cannot fix that from above, so `ground_z` now carves a
    ROAD CUT the same way it carves the brook, and the ground mesh is therefore built
    LAST — after the pads, the ribbons and the area floors exist to carve against.

 6  A ROAD RIBBON STOPS AT ITS OWN MAP EDGE'S END.  Two edges meeting at a landmark
    share one derived doorstep, and that doorstep faces only one of them — so the OTHER
    edge used to run right past the landmark to reach it (`square-plaza__barn` overshot
    the tithe barn by 3.6 m into the gate court, while `barn__gate-court` lay wholly
    inside the court's rim and owned no mesh at all).  A camera boundary sits on that
    second edge.  The stretch is now HANDED OVER rather than deleted: the walk network
    is unchanged metre for metre and only its ownership moves.

 7  A PROP-CLASS PAD SIZES TO THE PROP.  A 3.0 m square doorstep is right in front of a
    house and wrong in front of a waystone, and a pad that sprawls into a neighbouring
    corridor leaves that corridor's seams nowhere to sit.  Prop pads are the prop's own
    footprint plus one step, oriented, and CAPPED at the landmark default so the rule
    can only ever shrink a pad.

 8  THE RIVER IS AN AUTHORED COURSE, NOT AN AXIS.  User redline 2026-08-01: a single
    straight line "does not meet the bar of realism".  `river.course` is a polyline of
    [x, y, bankWidth] with meanders and this file builds FROM it — the channel is carved
    along it, the water is skinned along it, the treeline opens where it crosses and the
    vista clusters are pushed off its banks.  Nothing here may reconstruct it from a
    centre-line x and a width; that generator is retired.  The brook is smoothed the same
    way (chaikin, deterministic) so it reads as a stream and not as a surveyed ditch.

 9  A CONSTANT IN METRES IS EITHER A FACT ABOUT A BODY OR A FACT ABOUT A TOWN, and the
    two behave differently when the map is rescaled.  A lane is 1.7 m wide, a brook is
    1.2 m wide, a doorstep is 1.2 x 0.9 m and a cell is 0.45 m BECAUSE OF THE PLAYER —
    those numbers do not move when the map's coordinates are doubled.  But the distance
    at which the interpolated rise gives way to the valley pan, and the number of trees
    it takes to close a horizon, are facts about the TOWN's size: the same literals that
    were right at 1x left 37% of the town's own bounding box sagging toward the pan and a
    treeline with 68 of its 150 trees culled.  Those are now DERIVED from the map's own
    anchor span (`TSPAN`), and evaluate to their old values on the 1x map.
"""
import bpy, json, math, os, sys, hashlib

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


MAP = os.path.join(REPO, "public", opt("--map", "townmap/emberbrook.map.json"))
OUT = opt("--out", os.path.join(REPO, "tools/blends/emberbrook-master.blend"))
DIGEST = "--digest" in argv
NOSAVE = "--nosave" in argv
D = json.load(open(MAP))

print("=" * 78)
print("EMBERBROOK BLOCKOUT — %s" % os.path.relpath(MAP, REPO))
print("=" * 78)

# =============================================================== scene reset ==
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


for n in ("EMB_CONTEXT", "EMB_WATER", "EMB_PATHS", "EMB_MASSING", "EMB_LIGHTS"):
    coll(n)


def mat(name, rgba, rough=0.9, emit=None, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    if emit is not None:
        b.inputs["Emission Color"].default_value = emit[0]
        b.inputs["Emission Strength"].default_value = emit[1]
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    return m


# The blockout palette IS the look brief in gray form: warm autumn village, timber over
# stone, thatch and shingle, cobble — and greens MIXED INTO the autumn (look canon; a
# uniformly orange town reads as a filter, not a season).
M_GRASS = mat("emb_mat_grass", (0.24, 0.30, 0.16, 1))
M_EARTH = mat("emb_mat_earth", (0.40, 0.32, 0.23, 1))
M_ROAD = mat("emb_mat_road", (0.46, 0.39, 0.29, 1))
M_COBBLE = mat("emb_mat_cobble", (0.44, 0.40, 0.36, 1))
M_STONE = mat("emb_mat_stone", (0.47, 0.45, 0.42, 1))
M_TIMBER = mat("emb_mat_timber", (0.34, 0.24, 0.16, 1))
M_PLASTER = mat("emb_mat_plaster", (0.55, 0.49, 0.40, 1))
M_THATCH = mat("emb_mat_thatch", (0.55, 0.45, 0.26, 1))
M_SLATE = mat("emb_mat_slate", (0.24, 0.24, 0.28, 1))
M_TILE = mat("emb_mat_tile", (0.42, 0.24, 0.18, 1))
M_WATER = mat("emb_mat_water", (0.13, 0.22, 0.26, 1), rough=0.06, alpha=0.70)
M_LEAF_A = mat("emb_mat_leaf_autumn", (0.52, 0.22, 0.09, 1))
M_LEAF_G = mat("emb_mat_leaf_green", (0.20, 0.28, 0.13, 1))
M_IRON = mat("emb_mat_iron", (0.08, 0.08, 0.09, 1), rough=0.5)
# An ORDINARY warm window, and the distinction matters: `impliedScale` asks for lit
# windows out past the playable edge so the town reads inhabited, and STORY.md says the
# lamps carry the Heartlight's warmth OUT to the doors.  So windows and lampposts glow
# — modestly.  Only the Heartlight itself is magical, and only it is 30x brighter.
M_WINDOW = mat("emb_mat_window", (0.90, 0.72, 0.46, 1), rough=0.3,
               emit=((1.0, 0.72, 0.36, 1), 2.6))
M_GLASS = mat("emb_mat_lamp_glass", (1.0, 0.78, 0.44, 1), rough=0.2,
              emit=((1.0, 0.66, 0.30, 1), 7.0))
# THE ONE MAGICAL LIGHT IN THE TOWN.  Emberbrook is the rare survivor that still HAS a
# Heartlight and that is its identity (STORY.md §1).  Exactly one material in this file
# emits like this; a second anywhere in Emberbrook would be a canon bug.
# 26, not 180.  The Heartlight has to be the brightest thing in every frame that holds
# it, and at 180 it was simply WHITE — a clipped hole with no crystal in it, which is
# the opposite of what "treat with reverence in every shot" asks for.  Brightness is
# carried by the 5200 W point light beside it; the surface only has to glow.
M_HEART = mat("emb_mat_heartlight", (1.0, 0.78, 0.42, 1), rough=0.1,
              emit=((1.0, 0.60, 0.24, 1), 26.0))

MESHES = []


def mesh(name, verts, faces, m, cname):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    me.update()
    if m:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    coll(cname).objects.link(ob)
    MESHES.append(ob)
    return ob


def box(name, cx, cy, cz, sx, sy, sz, m, cname, rz=0.0):
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    c, s = math.cos(rz), math.sin(rz)
    v = []
    for dz in (-hz, hz):
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            v.append((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh(name, v, f, m, cname)


def disc(name, cx, cy, cz, r, thick, m, cname, seg=24):
    v, f = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v.append((cx + r * math.cos(a), cy + r * math.sin(a), cz))
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v.append((cx + r * math.cos(a), cy + r * math.sin(a), cz - thick))
    f.append(tuple(range(seg - 1, -1, -1)))
    f.append(tuple(range(seg, 2 * seg)))
    for k in range(seg):
        n = (k + 1) % seg
        f.append((k, n, seg + n, seg + k))
    return mesh(name, v, f, m, cname)


def pyramid(name, cx, cy, cz, sx, sy, h, m, cname, rz=0.0):
    hx, hy = sx / 2.0, sy / 2.0
    c, s = math.cos(rz), math.sin(rz)
    v = []
    for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        v.append((cx + dx * c - dy * s, cy + dx * s + dy * c, cz))
    v.append((cx, cy, cz + h))
    f = [(0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    return mesh(name, v, f, m, cname)


def gable(name, cx, cy, cz, sx, sy, h, m, cname, rz=0.0):
    """A ridged roof, not a cone.  A four-sided cone reads as a tent from every angle
    this town's cameras use; a ridge reads as a house at 40 m, which is where they
    stand."""
    hx, hy = sx / 2.0, sy / 2.0
    c, s = math.cos(rz), math.sin(rz)

    def P(dx, dy, dz):
        return (cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz)

    v = [P(-hx, -hy, 0), P(hx, -hy, 0), P(hx, hy, 0), P(-hx, hy, 0),
         P(-hx * 0.92, 0, h), P(hx * 0.92, 0, h)]
    f = [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)]
    return mesh(name, v, f, m, cname)


def ribbon(name, a, b, wdt, hgt, m, cname):
    """One flat segment of a walk surface: top face at the authored z, skirt below."""
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
    return mesh(name, v, f, m, cname)


def chaikin(pts, n=2):
    for _ in range(n):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]
            out.append(tuple(p[k] * 0.75 + q[k] * 0.25 for k in range(3)))
            out.append(tuple(p[k] * 0.25 + q[k] * 0.75 for k in range(3)))
        out.append(pts[-1])
        pts = out
    return pts


def resample(poly, step):
    """A polyline at fixed spacing, carrying z — the brook is authored as a sparse
    polyline and needs dense samples both to carve the channel and to skin the water."""
    out = [poly[0]]
    for a, b in zip(poly, poly[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / step)))
        for k in range(1, n + 1):
            t = k / float(n)
            out.append(tuple(a[j] + (b[j] - a[j]) * t for j in range(3)))
    return out


def seg_dist2(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2


def h32(*ints):
    """The ONLY source of variation in this file.  `random` (even seeded) is a promise
    about a library version; this is arithmetic."""
    h = 2166136261
    for i in ints:
        h = ((h ^ (int(i) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


def h01(*ints):
    return h32(*ints) / 4294967295.0


# =========================================================== the map, indexed ==
LM = {l["id"]: l for l in D["landmarks"]}
POS = {i: tuple(l["pos"]) for i, l in LM.items()}
EDGES = D["edges"]
WATER_LM = {i for i, l in LM.items() if l.get("kind") == "water"}

BROOK = D.get("brook") or {}
RIVER = D.get("river") or {}
BW = BROOK.get("widthM", 1.2)
RLVL = RIVER.get("level", -0.6)

# ------------------------------------------------------------- the river's course --
# RULE 8.  `river.course` is the authored polyline — [x, y, bankWidth] per point, south
# to north, meandering.  Everything the river is in this file comes off this curve.
#
# IT RUNS OFF THE MAP AT BOTH ENDS.  A river that begins and ends inside the valley is a
# long pond; the course is extrapolated along its own end tangents far enough to leave
# the ground mesh, so the water enters the frame from downstream-of-nowhere and leaves
# toward Dellhollow, which is the story the map's `flow` note is telling.
#
# THEN SMOOTHED THE WAY THE LANES ARE.  Eight authored points make eight straight reaches
# and seven corners; two rounds of chaikin turn the corners into bends without moving the
# course off what was authored (chaikin is a corner cut, not a fit), and the resample
# gives the carve and the water skin the same samples to work from.
RCOURSE = [tuple(p) for p in RIVER.get("course", [])]
RCRS = []
if len(RCOURSE) >= 2:
    def _run_on(a, b, d):
        vx, vy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(vx, vy) or 1.0
        return (b[0] + vx / L * d, b[1] + vy / L * d, b[2])

    # FOUR ROUNDS OF CHAIKIN, NOT THE LANES' TWO, and the extra two are paid for by a
    # measurement rather than by taste.  The water is skinned as a strip offset half the
    # bank width either side of the course, and a strip FOLDS — the inner bank crosses
    # itself into a bow tie — wherever the course's radius of curvature is smaller than
    # that half width.  At two rounds the bend below the north end came out at radius
    # 4.4 m against a 6.3 m half width (ratio 0.69) and rendered as a lobe of water lying
    # over its own bank.  Four rounds take the tightest bend to ratio 2.0 and change the
    # course's sinuosity by 0.001 — the meanders the user asked for are all still there.
    RCRS = resample(chaikin([_run_on(RCOURSE[1], RCOURSE[0], 26.0)] + RCOURSE
                            + [_run_on(RCOURSE[-2], RCOURSE[-1], 26.0)], 4), 1.5)
    _worst, _at = 1e9, None
    for _k in range(1, len(RCRS) - 1):
        _a, _b, _c = RCRS[_k - 1], RCRS[_k], RCRS[_k + 1]
        _ar = abs((_b[0] - _a[0]) * (_c[1] - _a[1]) - (_c[0] - _a[0]) * (_b[1] - _a[1])) / 2
        if _ar < 1e-9:
            continue
        _rad = (math.hypot(_b[0] - _a[0], _b[1] - _a[1])
                * math.hypot(_c[0] - _b[0], _c[1] - _b[1])
                * math.hypot(_c[0] - _a[0], _c[1] - _a[1])) / (4 * _ar)
        if _rad / (_b[2] / 2) < _worst:
            _worst, _at = _rad / (_b[2] / 2), (_b[0], _b[1])
    print("  river course   tightest bend has radius %.2f x its own half width at "
          "(%.1f, %.1f) — the water strip cannot fold above 1.0" % (_worst, *_at))
    assert _worst > 1.05, ("the authored river course bends tighter than its own banks at "
                           "(%.1f, %.1f): the water would cross itself" % _at)


def river_at(x, y):
    """(distance to the course, bank width there).  One question, four askers: the
    channel carve, the water skin, the treeline's opening and the vista clusters."""
    best, bw = 1e9, 11.0
    for a, b in zip(RCRS, RCRS[1:]):
        d2 = seg_dist2(x, y, a[0], a[1], b[0], b[1])
        if d2 < best:
            best, bw = d2, (a[2] + b[2]) * 0.5
    return (math.sqrt(best) if best < 1e9 else 1e9), bw


# ------------------------------------------------------------------- the brook, ditto --
# THE BROOK REACHES THE RIVER, because the town is named for the meeting.  The map
# authors a `confluence` point; the river's own west bank may lie past it (at 2x it lies
# 7.5 m past it), so the channel is carried on along its last bearing until it is IN the
# water — and the distance is MEASURED and PRINTED rather than assumed, because "the
# brook ends 7 m short of the river" is exactly the kind of thing a wide shot shows and
# a build log should have said first.
_bpts = [tuple(p) for p in BROOK.get("polyline", [])]
if _bpts and BROOK.get("confluence"):
    _bpts.append(tuple(BROOK["confluence"]))
    if RCRS:
        _a, _b = _bpts[-2], _bpts[-1]
        _vx, _vy = _b[0] - _a[0], _b[1] - _a[1]
        _L = math.hypot(_vx, _vy) or 1.0
        _d, _hw = river_at(_b[0], _b[1])
        _short = _d - _hw / 2.0
        if _short > 0.05:
            _bpts.append((_b[0] + _vx / _L * (_short + 1.5),
                          _b[1] + _vy / _L * (_short + 1.5), RLVL))
        print("  brook->river   the authored confluence (%.1f, %.1f) is %.1f m short of "
              "the west bank; channel carried on %.1f m to meet the water"
              % (_b[0], _b[1], _short, max(0.0, _short + 1.5)))
BPOLY = resample(chaikin(_bpts, 2), 0.6) if len(_bpts) >= 2 else []

# every point the town is pinned to, in map order (the ground is interpolated from it)
ANCH = [tuple(l["pos"]) for l in D["landmarks"]]
for e in EDGES:
    for w in e.get("waypoints", []):
        ANCH.append(tuple(w))
for p in BPOLY[::4]:
    ANCH.append(p)
if BROOK.get("confluence"):
    ANCH.append(tuple(BROOK["confluence"]))

XS = [p[0] for p in ANCH]
YS = [p[1] for p in ANCH]
# THE GROUND HAS TO REACH PAST THE TREELINE THAT CLOSES IT.  `PAD` was 22 m against a
# wooded rim whose band ends 28 m out, so the mesh-bound check silently culled the outer
# third of the ring — 59 trees at 2x, 59 at 1x, and a treeline with holes in it is the
# one thing this ring exists to prevent.  The pad is now the band's own depth plus a
# margin, which is a fact about the rim rather than a number that happened to fit.
RIMIN, RIMBAND = 11.0, 17.0                             # the wooded rim's band, see below
PAD = RIMIN + RIMBAND + 5.0
X0, X1 = min(XS) - PAD, max(XS) + PAD
Y0, Y1 = min(YS) - PAD, max(YS) + PAD
# THE GROUND MUST CONTAIN THE WATER IT CARRIES.  The meandering course swings further
# east than any landmark does (16 m further, at 2x), so a ground mesh sized to the
# landmarks alone would end in mid-river.  Only the AUTHORED span counts here — the
# run-on tails are meant to leave the mesh.
for (_rx, _ry, _rw) in RCOURSE:
    X0, X1 = min(X0, _rx - _rw / 2 - 10.0), max(X1, _rx + _rw / 2 + 10.0)
    Y0, Y1 = min(Y0, _ry - 10.0), max(Y1, _ry + 10.0)

# RULE 9.  The town's own span, which is what the two size-of-town constants below are
# measured in.  At 1x this is 45.0 and they evaluate to the 9.0 / 16.0 they were tuned to.
TSPAN = ((max(XS) - min(XS)) + (max(YS) - min(YS))) / 2.0
FALL_START = 0.2000 * TSPAN         # ... beyond this from any anchor the rise gives way
FALL_LEN = 0.3556 * TSPAN           # ... over this distance, to the valley pan
print("  town extent  x %.1f..%.1f  y %.1f..%.1f   (%d anchors, %d brook samples, "
      "%d river samples)" % (min(XS), max(XS), min(YS), max(YS), len(ANCH), len(BPOLY),
                             len(RCRS)))
print("  town span %.1f m  ->  the rise holds to %.1f m from an anchor, then falls to "
      "the pan over %.1f m" % (TSPAN, FALL_START, FALL_LEN))

# ================================== the walk footprint, rasterised — two fields ==
# ONE grid, two answers, and both are needed before the ground can be built.
#   OCC  (below, filled after the ribbons)  — IS there walk surface here?  Water is cut
#        against it, so the pond's authored disc becomes a pond whose shore the lane
#        skirts (the map's own words) instead of a lane that runs through a pond.
#   WCUT — HOW HIGH is the walk surface here?  The ground is carved down to it (see
#        `road_cut`).  The declarations live up here, before `ground_z`, because
#        `ground_z` consults WCUT and Python resolves that at call time only if the name
#        exists; the fields themselves stay empty until there is a walk network to fill
#        them from, and an empty field carves nothing.
OSTEP = 0.45
ONX = int((X1 - X0) / OSTEP) + 2
ONY = int((Y1 - Y0) / OSTEP) + 2
NOZ = -1e9
WCUT = [NOZ] * (ONX * ONY)


def stamp_walk_z(pts, ztop):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    i0 = max(0, int((min(xs) - X0) / OSTEP))
    i1 = min(ONX - 1, int((max(xs) - X0) / OSTEP))
    j0 = max(0, int((min(ys) - Y0) / OSTEP))
    j1 = min(ONY - 1, int((max(ys) - Y0) / OSTEP))
    for j in range(j0, j1 + 1):
        for i in range(i0, i1 + 1):
            k = j * ONX + i
            if ztop > WCUT[k]:
                WCUT[k] = ztop


def rebuild_wcut():
    """The height of every walk surface built SO FAR.  Called twice, like `rebuild_occ`:
    once after the ribbons (so the lamps are seated on carved ground) and once after the
    area floors (so the ground mesh itself is carved against the whole walkable town)."""
    for k in range(len(WCUT)):
        WCUT[k] = NOZ
    for o in MESHES:
        if not o.name.startswith("walk_"):
            continue
        vs = o.data.vertices
        if o.name.startswith("walk_lm_"):
            for c in range(0, len(vs), 8):
                stamp_walk_z([(vs[c + k2].co.x, vs[c + k2].co.y) for k2 in range(4)],
                             max(vs[c + k2].co.z for k2 in range(8)))
        elif len(vs) >= 8:
            stamp_walk_z([(vs[k2].co.x, vs[k2].co.y) for k2 in range(4)],
                         max(v.co.z for v in vs))


# CUT_FULL is carved flat; CUT_BLEND eases back to the natural rise.  2.1 m of full cut
# either side of a 2.4 m ribbon centreline is wider than the ground grid's own 1.5 m
# step, which is the point: every grid EDGE that crosses a road has BOTH ends inside the
# cut, so the interpolated surface between them cannot arch back over the road.
CUT_DROP = 0.12
CUT_FULL = 1.40
CUT_BLEND = 1.60
CUT_REACH = CUT_FULL + CUT_BLEND


def walk_probe(x, y):
    """Distance to the nearest walk surface within CUT_REACH, and its top z."""
    i0 = max(0, int((x - CUT_REACH - X0) / OSTEP))
    i1 = min(ONX - 1, int((x + CUT_REACH - X0) / OSTEP))
    j0 = max(0, int((y - CUT_REACH - Y0) / OSTEP))
    j1 = min(ONY - 1, int((y + CUT_REACH - Y0) / OSTEP))
    bd, bz = 1e9, None
    for j in range(j0, j1 + 1):
        cy = Y0 + (j + 0.5) * OSTEP
        for i in range(i0, i1 + 1):
            z = WCUT[j * ONX + i]
            if z == NOZ:
                continue
            cx = X0 + (i + 0.5) * OSTEP
            d = math.hypot(x - cx, y - cy)
            if d < bd:
                bd, bz = d, z
    return bd, bz


# ============================================================ the valley floor ==
# The rise is INTERPOLATED from the map's own z values rather than sculpted, so the
# ground can never disagree with the walk network laid on top of it.  Then THREE things
# are CARVED — the brook's channel, the river's, and the ROADS — because a stream drawn
# on flat ground is a blue stripe, and a road drawn UNDER the ground is not a road.
GSTEP = 1.5
PAN = min(p[2] for p in ANCH if p[2] > -0.4) - 1.4


def surface_z(x, y):
    num = den = 0.0
    for (ax, ay, az) in ANCH:
        d2 = (x - ax) ** 2 + (y - ay) ** 2
        if d2 < 1e-6:
            return az
        w = 1.0 / (d2 * d2)
        num += w * az
        den += w
    z = num / den
    dmin = min(math.hypot(x - ax, y - ay) for (ax, ay, _z) in ANCH)
    # RULE 9.  These two distances are facts about the TOWN's size, not about a body, so
    # they are derived from its span.  As literal 9.0 / 16.0 they were right for a 50 x 40
    # town and wrong for a 100 x 80 one: measured on the 2x map, 37% of the town's own
    # bounding box was being pulled toward the valley pan (10% at 1x) and points inside it
    # reached the pan outright — a village with craters between its lanes.
    t = max(0.0, min(1.0, (dmin - FALL_START) / FALL_LEN))
    return z * (1 - t) + (PAN - 1.6 * t) * t


def brook_d(x, y):
    best = 1e9
    for a, b in zip(BPOLY, BPOLY[1:]):
        d2 = seg_dist2(x, y, a[0], a[1], b[0], b[1])
        if d2 < best:
            best = d2
    return math.sqrt(best) if best < 1e9 else 1e9


def ground_z(x, y):
    z = surface_z(x, y)
    # THE VALLEY RIVER, CARVED ALONG ITS AUTHORED COURSE (rule 8) — a real channel with a
    # cross-section, and the reason the eastern horizon is water instead of void (the t2
    # vista lesson: never an unaudited sightline).
    #
    # THE PROFILE IS THE POINT, and the first draft of it was wrong in a way only the
    # arithmetic shows.  A symmetric blend from the bank outward (the axis-strip version's
    # linear ramp over 7 m) leaves the ground BELOW the water surface for ~4 m past the
    # water's own edge — a dry trench inside the river, which reads as a hole beside the
    # water rather than as a bank.  So: inside the bank width it is a wetted channel,
    # shoaling from a thalweg 1.25 m under the surface to 0.25 m under it at the bank;
    # outside, the bank leaves the water within a metre and then eases into the valley.
    if RCRS:
        d, hw = river_at(x, y)
        half = hw / 2.0
        if d <= half:
            z = (RLVL - 1.25) + 1.00 * (d / max(half, 1e-6)) ** 2.2
        elif d < half + 9.0:
            s = ((d - half) / 9.0) ** 0.55
            z = (RLVL - 0.25) * (1 - s) + z * s
    # THE BROOK'S CHANNEL IS CUT AFTER THE RIVER'S, and the order is the whole of the
    # confluence.  A shallow V, 0.55 m deep and 3.2 m wide — deep enough to hold water,
    # shallow enough that the village stays ONE ground and not a ravine.  Cut BEFORE the
    # river (which it was), the last 15 m of it were simply overwritten by the river's
    # bank profile, and the stream's own water — which keeps the z the map authored for
    # it — was left standing on top of the bank: an aqueduct into the river, rendered.
    if BPOLY:
        d = brook_d(x, y)
        if d < 3.2:
            z -= 0.55 * (1.0 - d / 3.2) ** 1.6
    # THE ROAD IS CARVED THE SAME WAY THE BROOK IS, and for the same reason.  The rise is
    # interpolated from the map's anchors, the walk network is laid at the map's authored
    # z, and the two do not have to agree: measured over the village entrance, 605 of 960
    # walk samples had this surface ABOVE the walk top, worst 0.66 m — more than half of
    # that parcel's road buried under its own grass.  A district cannot fix that from
    # above (a skin that rises over a walk face fails master_walk_qa's coverage ray), so
    # it is fixed HERE, where the ground is made.  The cut only ever LOWERS: ground that
    # is already below the road is left alone, which is what a bank beside a lane is.
    d, wt = walk_probe(x, y)
    if wt is not None:
        target = wt - CUT_DROP
        if z > target:
            t = 0.0 if d <= CUT_FULL else min(1.0, (d - CUT_FULL) / CUT_BLEND)
            z += (target - z) * (1.0 - t)
    return z


NX = int(round((X1 - X0) / GSTEP)) + 1
NY = int(round((Y1 - Y0) / GSTEP)) + 1


def build_ground():
    """THE GROUND IS BUILT LAST, and that ordering is the whole of the road cut.
    `ground_z` carves against WCUT, and WCUT is empty until the pads, the ribbons and
    the area floors exist — so the mesh has to be raised after them, not before.  Every
    OTHER consumer of `ground_z` is unaffected by the move: the rim and the vista
    clusters stand 11 m or more outside the walk network (the cut is zero there), the
    lane stubs run away from town past the closed threshold, and the lamps — which DO
    stand within 0.40 m of a road edge — are seated after the first `rebuild_wcut()`
    and therefore on the carved surface, which is the point."""
    gv, gf = [], []
    for j in range(NY):
        for i in range(NX):
            x, y = X0 + i * GSTEP, Y0 + j * GSTEP
            gv.append((x, y, ground_z(x, y)))
    for j in range(NY - 1):
        for i in range(NX - 1):
            a = j * NX + i
            gf.append((a, a + 1, a + NX + 1, a + NX))
    mesh("emb_ground_valley", gv, gf, M_GRASS, "EMB_CONTEXT")
    # a skirt so no camera can see the underside or the world edge (t2 vista lesson)
    box("emb_ground_far", (X0 + X1) / 2, (Y0 + Y1) / 2, PAN - 3.2,
        (X1 - X0) + 90.0, (Y1 - Y0) + 90.0, 1.2, M_GRASS, "EMB_CONTEXT")
    print("  emb_ground_valley      %d verts (%d x %d @ %.1f m)"
          % (len(gv), NX, NY, GSTEP))


# ============================================================== the wooded rim ==
# Emberbrook is a clearing in the Whisperwood; the rim is what closes every horizon.
# It is dressing (`veg_`) and it is deterministic (h01 of the tree's own index).
#
# RULE 9, TWICE OVER.  Both of this ring's numbers used to be facts about a 1x town
# wearing the clothes of facts about a forest.  (a) The band was a FRACTION of the
# ellipse's own radius, so at 2x it threw trees 41 m outside the anchors — past the
# ground mesh's edge, where the bound check culled 68 of the 150 and left the treeline
# full of holes.  A treeline's depth is a fact about trees: 11 to 28 m of wood outside
# the town, at any town size.  (b) 150 trees closed a 265 m perimeter at 1x (one every
# 1.76 m); the same 150 over a 406 m perimeter is a colonnade.  The COUNT is derived
# from the perimeter at that spacing, so the wood is as thick as it was and there is
# simply more of it.
cx0, cy0 = (min(XS) + max(XS)) / 2, (min(YS) + max(YS)) / 2
rx, ry = (max(XS) - min(XS)) / 2, (max(YS) - min(YS)) / 2
_ma, _mb = rx + RIMIN + RIMBAND / 2, ry + RIMIN + RIMBAND / 2   # the band's mean ellipse
_per = math.pi * (3 * (_ma + _mb) - math.sqrt((3 * _ma + _mb) * (_ma + 3 * _mb)))
RIMN = int(round(_per / 1.76))
ntree = noff = nwet = 0
for k in range(RIMN):
    a = 2 * math.pi * k / RIMN
    off = RIMIN + RIMBAND * h01(k, 11)
    x = cx0 + (rx + off) * math.cos(a)
    y = cy0 + (ry + off) * math.sin(a)
    if not (X0 + 2 < x < X1 - 2 and Y0 + 2 < y < Y1 - 2):
        noff += 1                                       # must stay ZERO: see PAD, above
        continue
    if RCRS:
        _d, _hw = river_at(x, y)
        if _d < _hw / 2 + 2.0:
            nwet += 1
            continue                                    # the wood opens where the water is
    z = ground_z(x, y)
    ht = 5.4 + 3.4 * h01(k, 23)
    tr = 0.28 + 0.10 * h01(k, 31)
    box("veg_emb_rim_%03d_trunk" % k, x, y, z + ht * 0.34, tr, tr, ht * 0.72, M_TIMBER, "EMB_CONTEXT")
    leaf = M_LEAF_G if (h32(k, 47) % 5) < 2 else M_LEAF_A
    for c_ in range(2):
        rr = (2.0 + 1.1 * h01(k, 53 + c_)) * (1.0 - 0.22 * c_)
        pyramid("veg_emb_rim_%03d_crown%d" % (k, c_), x, y, z + ht * 0.62 + c_ * 1.5,
                rr * 2, rr * 2, 2.6 + 1.2 * h01(k, 61 + c_), leaf, "EMB_CONTEXT",
                rz=h01(k, 71 + c_) * 1.57)
    ntree += 1
print("  veg_emb_rim_*          %d trees of %d over %.0f m of perimeter (%.2f m apart; "
      "%d stood in the river and the wood opens there, %d fell off the ground mesh)"
      % (ntree, RIMN, _per, _per / max(ntree, 1), nwet, noff))
assert noff == 0, ("%d rim trees fell outside the ground mesh — PAD no longer covers the "
                   "rim band" % noff)

# ================================================================== doorsteps ==
# A landmark's map coordinate is the BUILDING.  The doorstep is DERIVED — pushed out
# along the mean direction of the edges that arrive there, past the building's own
# half-depth.  Nothing about the map moves: the map says where the inn IS, and this
# says where you stand to knock.
AREAS = [(l["id"], l["pos"], l.get("extent", 3)) for l in D["landmarks"]
         if l.get("class") == "area" and l["id"] not in WATER_LM]


def in_area(x, y, pad=0.0):
    for (aid, (ax, ay, _az), r) in AREAS:
        if math.hypot(x - ax, y - ay) <= r + pad:
            return aid
    return None


def bodysize(l):
    """The plan footprint of a landmark's massing — ONE place, so the doorstep, the
    area cut-out and the massing itself cannot disagree about how big a house is."""
    cls = l.get("class", "structure")
    kind = l.get("kind") or ""
    nm = (l.get("name") or "").lower()
    if cls in ("area", "dressing"):
        return (0.0, 0.0)
    if cls == "portal":
        return (2.4, 1.8) if kind == "trailhead" else (4.6, 1.6)
    if cls == "prop":
        if "bridge" in nm:
            # A PROP'S FOOTPRINT IS THE PROP, NOT A LANDMARK DEFAULT.  This read (3.4,
            # 2.6) — a slab wider than the lane it carries — and because a footbridge's
            # DECK *is* `walk_pad_brook-bridge`, that number laid a 3.6 x 3.9 m walk
            # surface 0.26 m off the Pond Lane corridor, so no seam on that lane had a
            # band free of a foreign path.  A plank footbridge is what the name says:
            # long enough to span the 1.2 m brook with ~0.44 m of bearing on each bank
            # (2.6, across the approach) and one plank-and-rail wide (1.4, along it).
            return (2.6, 1.4)
        if "spring" in nm or "mouth" in nm:
            return (2.6, 2.6)
        if "well" in nm:
            return (2.5, 2.5)                           # a well is round and you draw
        if "board" in nm:                               # water from every side of it
            return (2.2, 1.6)
        return (2.0, 1.4)
    if kind == "heartlight":
        return (2.4, 2.4)
    if kind == "dock":
        return (1.9, 4.7)
    # SIZED FOR THE MAP'S OWN DENSITY.  The first draft used 5.4 x 4.6 for a shop or a
    # house; the map puts Home Row's three cottages 3-5 m apart, so with a 1.14 roof
    # oversail there was no room left between them for the doorsteps their own lanes
    # arrive at — five pads refused in a row.  A 4.8 m frontage is still a proper
    # village house and it gives every lane its threshold back.
    big = kind.startswith("shop") or kind == "building"
    bw, bd = (4.8, 4.0) if big else (3.9, 3.3)
    return (bw * 1.14, bd * 1.14)                       # the roof oversails the walls


def foot_rect(l):
    """A landmark's massing footprint as an ORIENTED rectangle.  It replaced a
    circumscribed circle, and the circle was not a rounding error: the inn and the item
    shop stand 5.8-6.4 m from the plaza's 7 m centre, so cutting them out as r 4.34
    discs took 154 m2 of Festival Square down to 31 — a plaza too small for the crowd
    the Kindling Hour puts on it (`impliedScale`, technique 3).  The rectangle gives
    back 2.4x the floor and cuts exactly what is actually standing there."""
    bw, bd = bodysize(l)
    x, y, _z = l["pos"]
    return (x, y, bw / 2, bd / 2, math.atan2(APPR[l["id"]][1], APPR[l["id"]][0]) + math.pi / 2)


def in_rect(px, py, rect, pad=0.0):
    cx, cy, hw, hd, rz = rect
    c, s_ = math.cos(-rz), math.sin(-rz)
    dx, dy = px - cx, py - cy
    return abs(dx * c - dy * s_) <= hw + pad and abs(dx * s_ + dy * c) <= hd + pad


# THE APPROACH IS ONE EDGE, NOT THE MEAN OF ALL OF THEM.  Averaging unit directions is
# right for a building on a straight street and catastrophic on a junction: Mara & Pip's
# cottage sits where three lanes meet, the three unit vectors very nearly cancelled, and
# the mean pointed WEST — putting the derived doorstep 4.9 m into the neighbour's garden
# and turning the cottage's front door away from the only road that reaches it.  A house
# faces the road it is ON.  So: prefer `road` edges over `path`, and among the preferred
# set take the one whose neighbour is furthest, which is the through-route rather than a
# spur.  Ties resolve by the map's own edge order, so it stays deterministic.
APPR = {}
for l in D["landmarks"]:
    i = l["id"]
    cands = []
    for e in EDGES:
        if e["from"] == i:
            nb = (e.get("waypoints") or [POS[e["to"]]])[0]
        elif e["to"] == i:
            nb = (e.get("waypoints") or [POS[e["from"]]])[-1]
        else:
            continue
        dx, dy = nb[0] - POS[i][0], nb[1] - POS[i][1]
        d = math.hypot(dx, dy)
        if d > 1e-6:
            cands.append((0 if e.get("type") == "road" else 1, -d, dx / d, dy / d))
    if cands:
        cands.sort(key=lambda c: (c[0], c[1]))
        APPR[i] = (cands[0][2], cands[0][3])
    else:
        APPR[i] = (0.0, -1.0)

DOOR = {}
for l in D["landmarks"]:
    i, (x, y, z) = l["id"], l["pos"]
    cls = l.get("class", "structure")
    kind = l.get("kind") or ""
    nm = (l.get("name") or "").lower()
    if cls in ("area", "dressing") or i in WATER_LM or kind == "dock" or "bridge" in nm:
        DOOR[i] = (x, y, z)                             # you stand ON these
        continue
    ax, ay = APPR[i]
    bw, bd = bodysize(l)
    if cls == "portal":
        back = (bd / 2 + 1.3) if l.get("state") == "sealed" else 0.0
    else:
        # `rz` is derived FROM the approach, so in the building's own frame the approach
        # runs along its DEPTH axis and the boundary is exactly bd/2.  The first draft
        # used |ax|*bw/2 + |ay|*bd/2, which double-counts on a diagonal and put every
        # corner-approached doorstep 1.5-2 m too far out into the road.
        back = bd / 2 + 1.15
    DOOR[i] = (x + ax * back, y + ay * back, z)

# ================================================================== landmarks ==
# `lm_` prefixed and NON-SOLID by contract: a district builder that lands later deletes
# the `lm_` objects it replaces and nothing else in the town has to know it happened.
# EVERY WALK TOP FACE IS AT THE AUTHORED z — pads, area floors and ribbons alike — so
# where two overlap they are coplanar and `eff_top` has nothing to choose between.  (The
# first draft put them at z+0.06, z and z-0.02 and manufactured a 60 mm lip around every
# doorstep in the town.)
BRIDGES = []
LAMPABLE = []
cx_town = sum(p[0] for p in ANCH) / len(ANCH)
cy_town = sum(p[1] for p in ANCH) / len(ANCH)
nlm = 0
for l in D["landmarks"]:
    i, (x, y, z) = l["id"], l["pos"]
    cls = l.get("class", "structure")
    kind = l.get("kind") or ""
    nm = (l.get("name") or "").lower()
    if i in WATER_LM or cls == "area":
        continue
    rz = math.atan2(APPR[i][1], APPR[i][0]) + math.pi / 2
    ax, ay = APPR[i]
    if cls == "dressing":
        # IMPLIED SCALE, technique 1: non-walkable massing beyond every playable edge,
        # composed into the frames.  A vista is a CLUSTER, not a building — five or six
        # roofs at descending sizes with chimneys and lit windows, so the eye reads
        # "more town over there" and never finds a wall.  The player can never reach
        # one; that is the whole point of the technique.
        if "river" in nm or "downstream" in nm:
            continue                                    # the water IS the vista
        nroof = 5
        for k in range(nroof):
            a = 2 * math.pi * h01(i.encode() and len(i), k, 3) + k * 1.1
            rr = 3.0 + 5.5 * h01(len(i), k, 7)
            vx, vy = x + rr * math.cos(a), y + rr * math.sin(a)
            # NO COTTAGE STANDS IN THE RIVER.  The cluster's own centre is a map point and
            # clears the water; a roof thrown 8.5 m off it need not, and at 2x the
            # riverside cottages' spread reaches 2.6 m past the west bank.  A roof that
            # lands in the channel is pushed straight back out to the bank + 2.5 m along
            # the course's own normal — deterministic, and it keeps the cluster's shape.
            if RCRS:
                _d, _hw = river_at(vx, vy)
                _want = _hw / 2 + 2.5
                if _d < _want:
                    _ox, _oy = vx - x, vy - y
                    _oL = math.hypot(_ox, _oy) or 1.0
                    _sgn = -1.0 if _d < 1e-6 else 1.0
                    vx -= _sgn * _ox / _oL * (_want - _d)
                    vy -= _sgn * _oy / _oL * (_want - _d)
                    print("    vista %-18s roof %d pushed %.1f m clear of the river bank"
                          % (i, k, _want - _d))
            vz = ground_z(vx, vy)
            bw = 3.6 + 2.2 * h01(len(i), k, 11)
            bd = bw * (0.72 + 0.3 * h01(len(i), k, 13))
            bh = 2.8 + 1.6 * h01(len(i), k, 17)
            vrz = h01(len(i), k, 19) * math.pi
            box("lm_%s_%d_body" % (i, k), vx, vy, vz + bh / 2, bw, bd, bh,
                M_PLASTER, "EMB_CONTEXT", vrz)
            gable("lm_%s_%d_roof" % (i, k), vx, vy, vz + bh, bw * 1.16, bd * 1.16,
                  1.5 + 0.5 * h01(len(i), k, 23),
                  M_THATCH if (h32(len(i), k, 29) % 3) else M_TILE, "EMB_CONTEXT", vrz)
            box("lm_%s_%d_chim" % (i, k), vx + bw * 0.3, vy + bd * 0.28, vz + bh + 1.2,
                0.55, 0.55, 1.9, M_STONE, "EMB_CONTEXT", vrz)
            # two lit windows per roof: the cheapest possible "somebody lives there"
            for wk in (-1, 1):
                box("lm_%s_%d_win%d" % (i, k, (wk + 1) // 2),
                    vx + math.cos(vrz) * wk * bw * 0.28 - math.sin(vrz) * (bd / 2 + 0.02),
                    vy + math.sin(vrz) * wk * bw * 0.28 + math.cos(vrz) * (bd / 2 + 0.02),
                    vz + bh * 0.62, 0.7, 0.06, 0.8, M_WINDOW, "EMB_CONTEXT", vrz)
        nlm += 1
        continue
    if cls == "prop" and "closed" in nm:
        # IMPLIED SCALE, technique 2: a lane that visibly CONTINUES and is closed at the
        # threshold.  The stub is `emb_` (scenery, NOT walkable, so the walk network
        # stays exactly as tight as the parcels) and the closure is `bar_` — festival
        # carts and stacked barrels a player can see through and cannot pass.  Never an
        # invisible wall: the user ruled on that specifically.
        ox, oy = x - cx_town, y - cy_town
        d = math.hypot(ox, oy) or 1.0
        ox, oy = ox / d, oy / d
        for k in range(7):                              # the lane, running away
            sx, sy = x + ox * (1.2 + k * 1.7), y + oy * (1.2 + k * 1.7)
            box("emb_lanestub_%s_%d" % (i, k), sx, sy, ground_z(sx, sy) + 0.05,
                2.2, 1.8, 0.10, M_ROAD, "EMB_CONTEXT", math.atan2(oy, ox))
        crz = math.atan2(oy, ox) + math.pi / 2
        box("bar_%s_cart_bed" % i, x, y, z + 0.62, 2.6, 1.3, 0.35, M_TIMBER, "EMB_MASSING", crz)
        box("bar_%s_cart_rail" % i, x, y, z + 0.95, 2.6, 0.12, 0.40, M_TIMBER, "EMB_MASSING", crz)
        for wk in (-1, 1):
            disc("bar_%s_cart_wheel%d" % (i, (wk + 1) // 2),
                 x - oy * wk * 0.72, y + ox * wk * 0.72, z + 0.44, 0.44, 0.12,
                 M_TIMBER, "EMB_MASSING", seg=12)
        for k in range(3):
            bxp = x + (-oy) * (1.55 + 0.62 * (k % 2)) * (1 if k < 2 else -1)
            byp = y + (ox) * (1.55 + 0.62 * (k % 2)) * (1 if k < 2 else -1)
            disc("bar_%s_barrel%d" % (i, k), bxp, byp, z + 0.42 + 0.42 * (k // 2),
                 0.36, 0.84, M_TIMBER, "EMB_MASSING", seg=10)
        nlm += 1
        continue
    if cls == "portal":
        if kind == "trailhead":
            box("lm_%s_stileA" % i, x - 0.9, y, z + 0.55, 0.22, 1.5, 1.1, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_stileB" % i, x + 0.9, y, z + 0.55, 0.22, 1.5, 1.1, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_step" % i, x, y, z + 0.42, 1.9, 0.5, 0.16, M_TIMBER, "EMB_MASSING", rz)
        elif l.get("state") == "sealed":                # the sealed gate: stone, mossy
            box("lm_%s_jambL" % i, x - 1.9, y, z + 1.7, 0.9, 1.1, 3.4, M_STONE, "EMB_MASSING", rz)
            box("lm_%s_jambR" % i, x + 1.9, y, z + 1.7, 0.9, 1.1, 3.4, M_STONE, "EMB_MASSING", rz)
            box("lm_%s_lintel" % i, x, y, z + 3.7, 4.9, 1.1, 0.7, M_STONE, "EMB_MASSING", rz)
            box("lm_%s_doors" % i, x, y, z + 1.5, 2.9, 0.28, 3.0, M_TIMBER, "EMB_MASSING", rz)
            # the twin sigil plates set in the ground before the doors (Ch1 set-piece)
            for sgn, tag in ((-1, "L"), (1, "R")):
                disc("lm_%s_plate%s" % (i, tag),
                     x + sgn * 2.2 * math.cos(rz) + ax * 3.0,
                     y + sgn * 2.2 * math.sin(rz) + ay * 3.0,
                     z + 0.04, 0.95, 0.10, M_STONE, "EMB_MASSING", seg=16)
        else:                                           # the village arch: timber, warm
            box("lm_%s_postL" % i, x - 1.7, y, z + 1.5, 0.34, 0.34, 3.0, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_postR" % i, x + 1.7, y, z + 1.5, 0.34, 0.34, 3.0, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_lintel" % i, x, y, z + 3.1, 4.1, 0.42, 0.34, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_brace" % i, x, y, z + 2.75, 3.4, 0.20, 0.20, M_TIMBER, "EMB_MASSING", rz)
    elif cls == "prop":
        if "bridge" in nm:
            # A PLANK-AND-RAIL FOOTBRIDGE.  Its deck IS its walk pad, and its rails are
            # `bar_` — a collider that is never a floor, which is exactly what a rail is
            # and exactly the case district_lib's GateGrid exists to let stand.
            # THE DECK AND ITS RAILS COME OUT OF ONE NUMBER, `bodysize`.  They used to be
            # three independent literals (3.2 x 2.2 deck, rails at 1.05, posts at 1.35)
            # and they disagreed: `(-ay, ax)` is the SPAN axis and `(ax, ay)` the width,
            # so the rails were offset along the span (both of them down the deck's own
            # centreline, overhanging each end) and the posts across it, 0.25 m out in
            # the air.  That is DAYLOG finding (e) — the reversed lateral basis — living
            # on in one more place.  Now: `span` is local x, `wid` is local y, and the
            # rails sit on the deck's own edges because they are measured from it.
            span, wid = bodysize(l)
            ux, uy = -ay, ax                                # along the deck (the span)
            vx, vy = -ax, -ay                               # across it (the width)
            box("walk_pad_" + i, x, y, z, span, wid, 0.16, M_TIMBER, "EMB_PATHS", rz)
            for sgn in (-1, 1):
                tag = "AB"[(sgn + 1) // 2]
                orl = (wid / 2 - 0.05) * sgn
                ox, oy = vx * orl, vy * orl
                box("bar_%s_rail%s" % (i, tag), x + ox, y + oy, z + 0.55,
                    span, 0.09, 0.10, M_TIMBER, "EMB_MASSING", rz)
                for k in (-1, 1):
                    opz = (span / 2 - 0.30) * k
                    box("bar_%s_post%s%d" % (i, tag, k + 1),
                        x + ox + ux * opz, y + oy + uy * opz, z + 0.30,
                        0.11, 0.11, 0.62, M_TIMBER, "EMB_MASSING", rz)
            BRIDGES.append((x, y, z))
        elif "spring" in nm:
            for k in range(5):
                a = 2 * math.pi * k / 5 + 0.4
                box("lm_%s_stone%d" % (i, k), x + 1.1 * math.cos(a), y + 1.1 * math.sin(a),
                    z + 0.18, 0.7, 0.6, 0.36, M_STONE, "EMB_MASSING", a)
        elif "mouth" in nm:
            for k in range(4):
                box("lm_%s_bank%d" % (i, k), x - 1.2 + k * 0.9, y + (k % 2) * 1.3 - 0.6,
                    z + 0.14, 0.8, 0.7, 0.28, M_STONE, "EMB_MASSING", h01(k, 5) * 1.5)
        elif "board" in nm:
            box("lm_%s_postL" % i, x - 0.7, y, z + 0.6, 0.14, 0.14, 1.2, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_postR" % i, x + 0.7, y, z + 0.6, 0.14, 0.14, 1.2, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_face" % i, x, y, z + 1.05, 1.7, 0.10, 1.0, M_TIMBER, "EMB_MASSING", rz)
        elif "bench" in nm:
            box("lm_%s_seat" % i, x, y, z + 0.44, 1.9, 0.44, 0.10, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_legA" % i, x - 0.75, y, z + 0.20, 0.12, 0.40, 0.40, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_legB" % i, x + 0.75, y, z + 0.20, 0.12, 0.40, 0.40, M_TIMBER, "EMB_MASSING", rz)
        elif "well" in nm:
            disc("lm_%s_ring" % i, x, y, z + 0.62, 1.0, 0.62, M_STONE, "EMB_MASSING", seg=16)
            box("lm_%s_frameA" % i, x - 0.85, y, z + 1.5, 0.14, 0.14, 1.8, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_frameB" % i, x + 0.85, y, z + 1.5, 0.14, 0.14, 1.8, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_beam" % i, x, y, z + 2.35, 2.0, 0.16, 0.16, M_TIMBER, "EMB_MASSING", rz)
        else:                                           # the waystone and its kin
            box("lm_%s_base" % i, x, y, z + 0.12, 1.1, 0.9, 0.24, M_STONE, "EMB_MASSING", rz)
            box("lm_" + i, x, y, z + 0.95, 0.78, 0.52, 1.5, M_STONE, "EMB_MASSING", rz)
    elif kind == "heartlight":
        # THE ONE.  Pedestal + flame-crystal, and it EMITS: no camera in this town is
        # ever composed without knowing where the light comes from.  STORY.md §2 — this
        # is the reservoir every lamppost in the village is lit FROM, and the only
        # magical light source Emberbrook has.
        disc("lm_%s_plinth" % i, x, y, z + 0.95, 1.15, 0.95, M_STONE, "EMB_MASSING", seg=16)
        box("lm_%s_cap" % i, x, y, z + 1.05, 2.0, 2.0, 0.20, M_STONE, "EMB_MASSING")
        pyramid("lm_%s_flame" % i, x, y, z + 1.18, 0.5, 0.5, 1.15, M_HEART, "EMB_MASSING")
        li = bpy.data.lights.new("KEYEMB_heartlight", 'POINT')
        li.energy = 5200.0
        li.color = (1.0, 0.63, 0.28)
        li.shadow_soft_size = 0.45
        lo = bpy.data.objects.new(li.name, li)
        lo.location = (x, y, z + 1.9)
        coll("EMB_LIGHTS").objects.link(lo)
    elif kind == "dock":
        box("walk_pad_" + i, x, y, z, 1.7, 4.6, 0.16, M_TIMBER, "EMB_PATHS", rz)
        for k in range(3):
            box("lm_%s_pile%d" % (i, k), x - ax * (1.6 - k * 1.6), y - ay * (1.6 - k * 1.6),
                z - 0.7, 0.22, 0.22, 1.5, M_TIMBER, "EMB_MASSING", rz)
    else:                                               # a house
        big = kind.startswith("shop") or kind == "building"
        bw, bd, bh = (4.8, 4.0, 4.6) if big else (3.9, 3.3, 3.2)
        box("lm_%s_base" % i, x, y, z + 0.55, bw, bd, 1.1, M_STONE, "EMB_MASSING", rz)
        box("lm_%s_body" % i, x, y, z + 1.1 + (bh - 1.1) / 2, bw * 0.97, bd * 0.97,
            bh - 1.1, M_PLASTER, "EMB_MASSING", rz)
        roof = M_SLATE if kind == "shop-inn" else (M_TILE if big else M_THATCH)
        gable("lm_%s_roof" % i, x, y, z + bh, bw * 1.14, bd * 1.14, 1.7, roof, "EMB_MASSING", rz)
        box("lm_%s_door" % i, x + ax * (bd / 2 + 0.03), y + ay * (bd / 2 + 0.03),
            z + 1.05, 1.1, 0.16, 2.1, M_TIMBER, "EMB_MASSING", rz)
        box("lm_%s_chimney" % i, x - ax * bw * 0.30, y - ay * bd * 0.30, z + bh + 1.1,
            0.6, 0.6, 2.0, M_STONE, "EMB_MASSING", rz)
    nlm += 1
print("  lm_* massing           %d landmarks" % nlm)


# --------------------------------------------------- threshold pads (walk_pad_) --
# A pad is the doorstep.  It is NOT built where the doorstep already stands on an area's
# floor — the plaza IS the inn's doorstep, and a second coplanar slab there would only
# give `eff_top` something to pick between.
#
# EXCEPT THAT AN ENTERABLE LANDMARK KEEPS ITS PAD (rule 8), and this is the THIRD time
# the swallow rule has been caught deleting walkable IDENTITY rather than redundant walk
# surface — after the camera boundary that landed on the previous edge's mesh (rule 6)
# and the doorstep that faced the next edge instead of its own.  `walk_pad_<id>` is not
# only floor: `scenegraph_derive` reads it BY NAME to seat a door's trigger and to land
# the spawn you return to, and `slice_test` proves both against the exported GLB.  With
# the plaza carrying the floor, item-shop, inn and bakery had no named geometry at their
# doors at all, and two return spawns landed in the holes the plaza's floor is cut with.
#
# IT IS A THRESHOLD, NOT A FORECOURT, and the size is measured rather than chosen.  The
# structure default is 3.0 m; centred on a doorstep 3.43 m out into a 14 m plaza that
# lands on what the map itself put there — the Heartlight's steps first touch 0.63 m from
# the item-shop's doorstep, the notice board's posts at 0.62, the shop's own trays at
# 0.77, the well's lip 1.09 m from the bakery's — and it took Festival Square's walk gate
# from 0 offenders to 11.  So it is 0.80 m square, ORIENTED to the door, and emitted
# WITHOUT THE RING SEARCH — that search exists to lift a doorstep out of a NEIGHBOUR'S
# WALL, these three stand on open plaza, and running it would reassign DOOR[] and move
# every ribbon in the town.
#
# IT IS CENTRED ON THE DOORSTEP, `DOOR[]`, and stays there.  I first chased it 0.53 m
# inboard to catch the return spawn, and that was me building around a BUG in somebody
# else's file rather than reporting it: `scenegraph_derive` was seating each door's
# TRIGGER at the landmark's CENTRE — inside the walls — and taking only the pad's HEIGHT,
# so the spawn, measured from the trigger, came out 2.9 m from the centre while the
# doorstep is at `bd/2 + 1.15` = 3.43 m.  The two numbers were never a contract, they
# were a defect and its symptom; the final-leg custodian has fixed the derive (trigger on
# the doorstep, proven byte-identical on Dellhollow) and RULED that a spawn landing off
# the network gets a derive-side street search.  So this pad does NOT stretch toward the
# plaza to catch a spawn point — it is a threshold, the trigger sits on it, and the spawn
# is measured from there.
#
# THE SIZE IS 1.2 m ALONG THE WALL FACE x 0.9 m DEEP, ruled, and it is a threshold rather
# than a forecourt for an arithmetic reason worth writing down: the return spawn is
# DEFINED as the trigger plus 2.90 m, and the trigger sits on this pad, so a pad that
# covered its own spawn would have to be 5.80 m deep — which is the 3.0 m default's
# problem an order of magnitude worse, and the 3.0 m default already took Festival
# Square's walk gate from 0 offenders to 11.  No size and no centre closes that loop;
# re-centring only carries the trigger along and pushes the spawn out again.  Whether
# there is floor 2.90 m past the door is the derive's question, not this file's.
#
# MEASURING THE ROOM COST A WRONG INSTRUMENT FIRST, and it was the same wrong instrument
# as DAYLOG (d): I took each threshold's clearance as the nearest VERTEX of the
# surrounding furniture and got 0.49 m where the true answer was zero — a box's corners
# can be far away while its FACE lies over the pad.  Point-in-shape, never
# nearest-vertex; at 1.4 m deep the item-shop's threshold reached `emb_sq_heart_step`
# and at 0.9 m it does not.
DOORSTEP_W, DOORSTEP_D = 1.20, 0.90
npad = nskip = nkept = 0
for l in D["landmarks"]:
    i = l["id"]
    if l.get("class", "structure") not in ("structure", "prop", "portal") or i in WATER_LM:
        continue
    if (l.get("kind") or "") in ("dock", "heartlight") or "bridge" in (l.get("name") or "").lower():
        continue                                        # deck IS the pad; the flame has none
    dx, dy, dz = DOOR[i]
    inside = in_area(dx, dy, -0.9)
    if inside and not l.get("enterable"):
        nskip += 1
        print("    pad %-18s SKIPPED — its doorstep stands on walk_lm_%s" % (i, inside))
        continue
    if inside:
        # the area's floor is still the walk surface here; what this adds is a NAME at
        # the door, coplanar with it, so `eff_top` still has nothing to choose between.
        drz = math.atan2(APPR[i][1], APPR[i][0]) + math.pi / 2
        box("walk_pad_" + i, dx, dy, dz, DOORSTEP_W, DOORSTEP_D, 0.14, M_EARTH,
            "EMB_PATHS", drz)
        nkept += 1
        print("    pad %-18s THRESHOLD on walk_lm_%-14s %.2f x %.2f m on the doorstep "
              "(%.2f, %.2f), %.2f m out — ENTERABLE, and its door's trigger sits here"
              % (i, inside, DOORSTEP_W, DOORSTEP_D, dx, dy,
                 math.hypot(dx - l["pos"][0], dy - l["pos"][1])))
        continue
    # A PROP-CLASS PAD SIZES TO THE PROP.  The landmark default is a 3.0 m square, which
    # is right for a doorstep in front of a house and wrong for a waystone: it hands the
    # cameras 9 m2 of walk surface where a marker stone stands, and a pad that sprawls
    # into a neighbouring corridor leaves that corridor's seams nowhere to sit (this is
    # Dellhollow's boatwright pad, arriving in a second town).  So a prop's pad is the
    # PROP's own plan footprint plus one step of margin, oriented the way the prop is —
    # and CAPPED at the landmark default, so that no prop pad can grow because of it.
    pw = ph = 2.6 if l.get("class") == "portal" else 3.0
    prz = 0.0
    if l.get("class") == "prop":
        bw_, bd_ = bodysize(l)
        pw, ph = min(bw_ + 0.60, pw), min(bd_ + 0.60, ph)
        prz = math.atan2(APPR[i][1], APPR[i][0]) + math.pi / 2
    # A DOORSTEP MUST NOT LAND IN THE NEIGHBOUR'S WALL.  Mara & Pip's cottage sits 3.8 m
    # from Poppy's bakery, so its derived pad overlapped the bakery's own footprint —
    # a walk surface tucked under a building, which is finding 93 arriving from the
    # other direction.  The pad walks out along its own approach axis until it is clear,
    # and a pad that cannot get clear is refused and counted rather than buried.
    # A DOORSTEP MUST NOT LAND IN THE NEIGHBOUR'S WALL.  Mara & Pip's cottage sits a few
    # metres from Poppy's bakery and Lake's from Rowan's, so a derived doorstep can land
    # inside a neighbour's footprint — a walk surface tucked under a building, which is
    # finding 93 arriving from the other direction.  Walking straight OUT along the
    # approach does not always help (it can walk further into the same neighbour), so the
    # foot is SEARCHED: the nearest clear point to the map's own doorstep, over a ring of
    # sixteen directions.  A landmark with no clear doorstep at all is refused and
    # counted, never buried.
    others = [foot_rect(o) for o in D["landmarks"]
              if o["id"] != i and o.get("class") not in ("area", "dressing")
              and bodysize(o)[0] > 0
              and math.hypot(o["pos"][0] - dx, o["pos"][1] - dy) < 11.0]
    found = None
    for rad in [0.0] + [0.30 + 0.30 * k for k in range(8)]:
        for a_ in range(16 if rad > 0 else 1):
            th = 2 * math.pi * a_ / 16
            px, py = dx + rad * math.cos(th), dy + rad * math.sin(th)
            if any(in_rect(px, py, r2, 0.40) for r2 in others):
                continue
            if BPOLY and brook_d(px, py) < BW / 2 + 0.4:
                continue
            found = (px, py, rad)
            break
        if found:
            break
    if found is None:
        print("    pad %-18s REFUSED — no clear doorstep within 2.4 m of the map point" % i)
        continue
    if found[2] > 0.0:
        print("    pad %-18s moved %.2f m: the map point lands in a neighbour's wall"
              % (i, found[2]))
    dx, dy = found[0], found[1]
    DOOR[i] = (dx, dy, dz)
    box("walk_pad_" + i, dx, dy, dz, pw, ph, 0.14, M_EARTH, "EMB_PATHS", prz)
    DOOR[i] = (dx, dy, dz)
    npad += 1
    print("    pad %-18s %-8s %.2f x %.2f m" % (i, l.get("class", "structure"), pw, ph))
print("  walk_pad_*             %d pads (%d enterable thresholds on an area floor, "
      "%d skipped: already on an area floor)" % (npad + nkept, nkept, nskip))

# ================================================================== the paths ==
# Flat chaikin-smoothed ribbons, named `walk_e_<from>__<to>_l<i>` — the name IS the
# coverage contract (`cine_regions.mjs` matches meshes to map edges by it, which is what
# makes "every walkable metre has exactly one owner" checkable instead of hoped).  Edges
# run DOORSTEP to DOORSTEP, so a road stops at the step and never inside a wall.
# AN EDGE THAT ENDS AT AN AREA STOPS AT THE AREA'S RIM, and this is the rule that
# rescued Festival Square.  `DOOR[<area>]` is the area's CENTRE, so every one of the
# eight edges touching `square-plaza` began its ribbon at (32, 22) — which is exactly
# where the Heartlight's pedestal stands.  Measured with master_walk_qa's own two rays:
# the pedestal, the well, the bakery, the inn and the item shop were all standing on
# road, and all five looked like building-placement faults until the ray named the floor
# underneath.  The area's own walkable floor carries the player from its rim to its
# middle; a road drawn across it is a second, thinner copy of a surface that is already
# there, threaded under whatever the district builds in the centre.
AREA_R = {l["id"]: l.get("extent", 3) for l in D["landmarks"]
          if l.get("class") == "area" and l["id"] not in WATER_LM}


def trim_to_rim(end_id, p, nb):
    r = AREA_R.get(end_id)
    if r is None:
        return p, 0.0
    dx, dy = nb[0] - p[0], nb[1] - p[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return p, 0.0
    # 0.6 short of the rim, so the ribbon and the area floor OVERLAP rather than meet
    t = min(max(0.0, r - 0.6), L)
    return (p[0] + dx / L * t, p[1] + dy / L * t, p[2] + (nb[2] - p[2]) * (t / L)), t


# A ROAD RIBBON STOPS AT ITS OWN MAP EDGE'S END, and the tithe barn is what taught it.
# Both of the barn's edges run to the SAME derived doorstep, and that doorstep faces the
# gate court — so `square-plaza__barn` did not stop at the barn, it carried on 3.6 m PAST
# it (segments l11..l14, the last reaching (36.8, 36.6)) to meet the court's flagstones,
# while `barn__gate-court` — whose whole polyline then lay inside the court's rim — was
# swallowed and owned no mesh at all.  The northlane<->gatefield camera boundary sits on
# `barn__gate-court`; it was landing on the PREVIOUS edge's ribbon.  b214b90 already
# ruled on this from the camera side ("a camera boundary belongs on a WALKABLE edge, not
# on one that happens to own a mesh"), and this is the geometry side of the same ruling:
# the stretch between a landmark and a doorstep that faces the NEXT edge belongs to that
# next edge, and it is handed over rather than deleted, so the walk network is unchanged
# metre for metre and only its OWNERSHIP moves.
#
# THE SWALLOWED-SPUR BEHAVIOUR IS UNCHANGED for everything else.  A spur — an edge with a
# leaf at one end, like the seven that radiate from the plaza's centre — is still
# swallowed by the area floor it lies in, because the plaza IS its walk surface.  Only a
# THROUGH edge (both ends carry other edges: it is a link in the town's route graph, and
# therefore a place a camera boundary can fall) tries to reclaim what was drawn past it,
# and an edge with nothing to reclaim is still swallowed and is now SAID so distinctly.
DEG = {}
for e in EDGES:
    for endk in ("from", "to"):
        DEG[e[endk]] = DEG.get(e[endk], 0) + 1


def span_of(d):
    return sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(d, d[1:]))


PLAN = []
for e in EDGES:
    if e["from"] not in DOOR or e["to"] not in DOOR:
        print("  SKIP dangling edge %s__%s" % (e["from"], e["to"]))
        continue
    pts = [DOOR[e["from"]]] + [tuple(w) for w in e.get("waypoints", [])] + [DOOR[e["to"]]]
    a2, ta = trim_to_rim(e["from"], pts[0], pts[1])
    b2, tb = trim_to_rim(e["to"], pts[-1], pts[-2])
    pts[0], pts[-1] = a2, b2
    t = e.get("type", "path")
    PLAN.append({"e": e, "key": "%s__%s" % (e["from"], e["to"]), "type": t,
                 "draw": chaikin(pts) if t in ("road", "path") else pts})

for p in PLAN:
    if span_of(p["draw"]) >= 1.2:
        continue
    e = p["e"]
    if DEG[e["from"]] < 2 or DEG[e["to"]] < 2:
        continue                            # a spur: the area's own floor IS its surface
    for Y in [n for n in (e["from"], e["to"]) if n not in AREA_R]:
        donor = at_start = None
        for q in PLAN:
            if q is p or Y not in (q["e"]["from"], q["e"]["to"]):
                continue
            if span_of(q["draw"]) < 1.2:
                continue
            donor, at_start = q, (q["e"]["from"] == Y)
            break
        if donor is None:
            continue
        d = donor["draw"]
        # the hand-over point is the polyline's own closest approach to the landmark:
        # that IS "the end of the map edge", and cutting at a vertex keeps both runs
        # made of whole segments.
        k = min(range(len(d)),
                key=lambda n: (d[n][0] - POS[Y][0]) ** 2 + (d[n][1] - POS[Y][1]) ** 2)
        if at_start:
            if k <= 0:
                continue
            tail, donor["draw"] = list(reversed(d[:k + 1])), d[k:]
        else:
            if k >= len(d) - 1:
                continue
            tail, donor["draw"] = d[k:], d[:k + 1]
        # THE RECLAIMED STRETCH REPLACES THE STUB, it is not appended to it.  What was
        # left of this edge after the rim trim is a sub-metre stub lying INSIDE the area
        # floor, which is exactly the thing the swallow rule exists to delete — and
        # keeping it cost 55 extra walk samples under the tithe barn's base plinth
        # (gatefield 2 offenders -> 3) for 0.46 m of ribbon the court's own floor already
        # carries.  So the edge's mesh is the stretch it legitimately owns, from the
        # landmark to the rim, and not one quad more.
        p["draw"] = tail
        print("    edge %-40s RECLAIMED %.2f m %s had drawn past %s"
              % (p["key"], span_of(tail), donor["key"], Y))
        if span_of(p["draw"]) >= 1.2:
            break

nrib = 0
nswallow = 0
SWALLOWED = set()
RIBSEGS = []
RUNS = {}
LANEDRAW = {}
for p in PLAN:
    e, draw = p["e"], p["draw"]
    span = span_of(draw)
    if span < 1.2:
        # the whole edge lies inside an area: the area's floor IS its walk surface, and
        # a 0.6 m ribbon threaded under the district's own hero prop is only a defect
        SWALLOWED.add(p["key"])
        nswallow += 1
        through = DEG[e["from"]] >= 2 and DEG[e["to"]] >= 2
        print("    edge %-40s SWALLOWED by an area floor (%.2f m left after trim)%s"
              % (p["key"], span,
                 " — THROUGH edge, nothing to reclaim" if through else ""))
        continue
    nm = "e_" + p["key"]
    RUNS[p["key"]] = span                               # for the lane-incident work-list
    LANEDRAW[p["key"]] = draw
    wdt = 2.4 if p["type"] == "road" else 1.7
    m = M_ROAD if p["type"] == "road" else M_EARTH
    for k in range(len(draw) - 1):
        ribbon("walk_%s_l%d" % (nm, k), draw[k], draw[k + 1], wdt, 0.14, m, "EMB_PATHS")
        RIBSEGS.append((draw[k], draw[k + 1], wdt, p["key"]))
        nrib += 1
print("  walk_e_*               %d ribbon segments over %d edges (%d swallowed by an "
      "area floor)" % (nrib, len(EDGES) - nswallow, nswallow))

# ========================= the walk footprint, rasterised — RULE 4's instrument ==
# The grid, OSTEP and the height field WCUT are declared up beside `ground_z`, which
# needs them; this is where the OCCUPANCY half of it gets filled.
OCC = bytearray(ONX * ONY)


def stamp_quad(pts, pad):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    i0 = max(0, int((min(xs) - pad - X0) / OSTEP))
    i1 = min(ONX - 1, int((max(xs) + pad - X0) / OSTEP))
    j0 = max(0, int((min(ys) - pad - Y0) / OSTEP))
    j1 = min(ONY - 1, int((max(ys) + pad - Y0) / OSTEP))
    for j in range(j0, j1 + 1):
        for i in range(i0, i1 + 1):
            OCC[j * ONX + i] = 1


def rebuild_occ():
    """Rasterise every walk surface built SO FAR.  Called twice, and the two calls
    answer different questions: before the lamps, OCC is the CORRIDOR (ribbons and
    pads) — because a lamppost standing in a square is right and a lamppost standing in
    a lane is a bollard; after the area floors, OCC is the whole walkable town, which
    is what the water has to be cut against."""
    for k in range(len(OCC)):
        OCC[k] = 0
    for o in MESHES:
        if not o.name.startswith("walk_"):
            continue
        if o.name.startswith("walk_lm_"):
            # an area floor is hundreds of cells; stamping its bbox would erase a pond.
            # Stamp each CELL's own footprint — what the player can actually stand on.
            vs = o.data.vertices
            for c in range(0, len(vs), 8):
                stamp_quad([(vs[c + k2].co.x, vs[c + k2].co.y) for k2 in range(4)], 0.45)
        else:
            stamp_quad([(v.co.x, v.co.y) for v in o.data.vertices], 0.40)


rebuild_occ()
rebuild_wcut()          # the lamps below stand ON the carved ground, not beside it


def occupied(x, y):
    i, j = int((x - X0) / OSTEP), int((y - Y0) / OSTEP)
    return 0 <= i < ONX and 0 <= j < ONY and OCC[j * ONX + i]


def corridor_clear(x, y, m=0.40):
    """Clear of every ribbon's own edge by `m`, measured against the segment rather
    than against the dilated raster.  The raster is right for water (generous is safe);
    it is wrong for a lamppost in a plaza, where 8 spurs radiate from one point and a
    0.40 m dilation of each blocked 77 of 111 candidate feet.  A lamppost's whole job is
    to stand at the edge of a road."""
    for (a, b, wdt, _k) in RIBSEGS:
        if seg_dist2(x, y, a[0], a[1], b[0], b[1]) < (wdt / 2 + m) ** 2:
            return False
    return True


# ============================================== LAKE'S ROUNDS — the lamp ring ==
# STORY.md §2 and the map's own `lamps` block: *a lamppost near every home*, and the
# lamplighter's dusk round runs in a FIXED order — low ground first (the pond lane,
# where the moths come off the water), then inward, ENDING on the lamps nearest the
# Heartlight: "closing the ring" before full dark.
#
# So the lamps are not dressing and they are not placed by eye.  Each one is numbered
# with its position in the round, and the numbering IS the order the map states: the
# square's own lamps are always last, everything else is sorted low-ground-first and
# then furthest-first.  A later evening-ambience pass can light them in name order and
# it will be staging the canon without having to know any of this.
#
# NOTE FOR THE LIGHTING PASS: Lake carries the brass LIGHTER — a seed-ember — on the
# round.  The Heartlight never leaves its pedestal.  So the travelling light source is
# small and warm and moves; the big one stays put and gets brighter as the sky drops.
# NOBODY'S WARMTH REACHES THE OLD GATE, and that is a rule with teeth rather than a
# mood: `emberbrook-town.md` §1 says the gate court gets no lamp at all, and it is the
# one unwarm frame in a town whose whole identity is that its Heartlight survived.  The
# court was getting lamp 07 anyway — `emb_gate_build` asserts only that IT builds no
# light (`KEYGT_`), which cannot see a lamp the blockout put there first — and the
# gatefield shot came out a lit courtyard with a dark gate standing in it.  CHECKED
# AGAINST SHIPPED CANON BEFORE REMOVING, because shipped canon outranks the plan:
# `public/js/chapter1.js`'s `gate` scene carries no `lamps` array at all (lamp1 is on the
# lane, lamp2/lamp3 and one already-lit post are in the square — three lamps, none here),
# so nothing in the shipped chapter stages a light at the court.  The round is 14 stops.
NO_LAMP = {"waystone", "sigil-gate", "forest-trailhead", "heartlight", "home-lane-end",
           "notice-board", "well", "brook-spring", "brook-mouth", "gate-court"}
HL = next((tuple(l["pos"]) for l in D["landmarks"]
           if (l.get("kind") or "") == "heartlight"), (cx_town, cy_town, 0.0))
SQ = next((l for l in D["landmarks"] if l["id"] == "square-plaza"), None)
SQR = (SQ.get("extent", 7) if SQ else 7)

LAMPFEET = []
hosts = []
for l in D["landmarks"]:
    i = l["id"]
    cls = l.get("class", "structure")
    nm = (l.get("name") or "").lower()
    if i in NO_LAMP or cls == "dressing" or i in WATER_LM or "closed" in nm:
        continue
    if cls not in ("structure", "prop", "portal", "area"):
        continue
    if cls == "area" and l.get("kind") == "plaza" and i != "square-plaza":
        pass
    elif cls == "area" and i == "square-plaza":
        continue                                        # its own two lamps are added below
    dx, dy, dz = DOOR[i]
    near_sq = math.hypot(dx - HL[0], dy - HL[1]) < SQR + 3.0
    hosts.append((1 if near_sq else 0, dz, -math.hypot(dx - HL[0], dy - HL[1]), i, dx, dy, dz))

# THE SQUARE CLOSES THE RING (the map's word).  Its two lamps are SEARCHED along the
# plaza rim rather than authored at fixed angles: the first draft put one on the brook,
# which the foot search correctly refused, and a refused lamp in the square is the one
# refusal this town cannot afford — the last two lamps of the round are the beat the
# whole round exists for.
if SQ:
    picked = []
    DBG = {"occ": 0, "brook": 0, "near": 0, "foot": 0, "lamp": 0}
    for k, a0 in enumerate((math.radians(115), math.radians(295))):
        for rr, step in [(rr, st) for rr in (SQR - 1.5, SQR - 2.6, SQR - 3.6)
                         for st in range(37)]:
            a = a0 + math.radians(((step + 1) // 2) * 10 * (1 if step % 2 else -1))
            lx = HL[0] + rr * math.cos(a)
            ly = HL[1] + rr * math.sin(a)
            if not corridor_clear(lx, ly):
                DBG["occ"] += 1
                continue
            if BPOLY and brook_d(lx, ly) < BW / 2 + 1.0:
                DBG["brook"] += 1
                continue
            if math.hypot(lx - HL[0], ly - HL[1]) < 2.6:
                DBG["near"] += 1
                continue                                # not inside the Heartlight's own step
            if BPOLY and brook_d(lx, ly) < BW / 2 + 1.0:
                DBG["brook"] += 1
                continue
            if any(math.hypot(lx - px, ly - py) < 3.5 for (px, py) in picked):
                DBG["near"] += 1
                continue
            if any(in_rect(lx, ly, foot_rect(o), 0.45) for o in D["landmarks"]
                   if o.get("class") in ("structure", "prop") and bodysize(o)[0] > 0
                   and math.hypot(o["pos"][0] - HL[0], o["pos"][1] - HL[1]) < SQR + 4):
                DBG["foot"] += 1
                continue
            if any(math.hypot(lx - f[0], ly - f[1]) < 2.5 for f in LAMPFEET):
                DBG["lamp"] += 1
                continue
            picked.append((lx, ly))
            hosts.append((2, HL[2], -0.0 - k, "square-ring%d" % k, lx, ly, HL[2]))
            break
        else:
            print("    square-ring%d: no free rim foot (occ %d, brook %d, near %d, "
                  "foot %d, lamp %d of %d tried)"
                  % (k, DBG["occ"], DBG["brook"], DBG["near"], DBG["foot"], DBG["lamp"],
                     sum(DBG.values())))

hosts.sort(key=lambda h: (h[0], h[1], h[2], h[3]))

nlamp = nrefused = 0
PLACED = []
for (ring, _z, _d, hid, dx, dy, dz) in hosts:
    # THE FOOT IS SEARCHED, NEVER AUTHORED (ga_build's rule): a ring of candidates
    # around the doorstep, each required to stand OUT of the walk corridor and to have
    # ground under it.  Nothing is floated; a host with no free foot is COUNTED.
    best = None
    for r in (1.9, 2.4, 2.9, 1.5):
        for k in range(16):
            a = 2 * math.pi * k / 16
            lx, ly = dx + r * math.cos(a), dy + r * math.sin(a)
            if occupied(lx, ly):
                continue
            g = ground_z(lx, ly)
            if abs(g - dz) > 1.3:
                continue
            if BPOLY and brook_d(lx, ly) < BW / 2 + 0.6:
                continue
            # ... and clear of every WALL.  The first draft checked the walk corridor,
            # the ground and the brook and not the buildings, so the item shop's lamp
            # was founded 0.3 m inside its own shopfront.
            if any(in_rect(lx, ly, foot_rect(o), 0.30) for o in D["landmarks"]
                   if o.get("class") not in ("area", "dressing") and bodysize(o)[0] > 0
                   and math.hypot(o["pos"][0] - lx, o["pos"][1] - ly) < 9.0):
                continue
            best = (lx, ly, g)
            break
        if best:
            break
    if best is None:
        nrefused += 1
        print("    lamp REFUSED for %-18s no foot out of the walk corridor" % hid)
        continue
    lx, ly, lz = best
    PLACED.append(hid)
    tag = "emb_lamp_%02d_%s" % (nlamp, hid)
    box(tag + "_post", lx, ly, lz + 1.30, 0.13, 0.13, 2.60, M_IRON, "EMB_MASSING")
    box(tag + "_glass", lx, ly, lz + 2.72, 0.30, 0.30, 0.34, M_GLASS, "EMB_MASSING")
    box(tag + "_cap", lx, ly, lz + 2.95, 0.40, 0.40, 0.10, M_IRON, "EMB_MASSING")
    li = bpy.data.lights.new("KEYEMB_lamp_%02d_%s" % (nlamp, hid), 'POINT')
    li.energy = 680.0                                   # the town standard, seven districts old
    li.color = (1.0, 0.58, 0.24)                        # ordinary warm; NOT a Heartlight
    li.shadow_soft_size = 0.10
    li.use_custom_distance = True
    li.cutoff_distance = 14.0
    lo = bpy.data.objects.new(li.name, li)
    lo.location = (lx, ly, lz + 2.74)
    coll("EMB_LIGHTS").objects.link(lo)
    LAMPFEET.append((lx, ly, 0.34, 0.34, 0.0))
    nlamp += 1
print("  emb_lamp_*             %d lampposts in round order (%d refused), 680 W each"
      % (nlamp, nrefused))
print("    the round: " + " -> ".join("%02d %s" % (n, h) for n, h in enumerate(PLACED)))
print("    posts are emb_lamp_NN_<host>_*; the LIGHTS are KEYEMB_lamp_NN_<host>")

# =================================== LANE INCIDENTS — REVIEW AIDS, NOT DRESSING ==
# The map's `laneIncident` block (user ruling 2026-08-01): with distances doubled, a lane
# needs mid-lane incident to pace the walk — a handcart, a woodpile, a fence gate — 1-2
# per lane over ~15 m, SEARCHED off the lane edge, thinning toward the unwarm Gate Field.
#
# THE REAL PASS IS THE DISTRICT DRESSING LAYER, AFTER RATIFICATION, and these are not it.
# They are grey blocks at the right size in the right places, put here for ONE reason:
# the user is being asked to judge PACING off this blockout, and a lane cannot be judged
# for pacing when it is empty by construction.  `lm_` prefixed like all massing, so the
# district builder that lands later deletes them the way it deletes any other placeholder,
# and named `lm_incident_*` so it is impossible to mistake one for a finished prop.
GATEFIELD = {l["id"] for l in D["landmarks"] if l.get("district") == "gatefield"}
nincident = 0
for _span, _key in sorted(((v, k) for k, v in RUNS.items() if v >= 15.0), reverse=True):
    a_id, b_id = _key.split("__")
    want = 2 if _span >= 20.0 else 1
    if a_id in GATEFIELD or b_id in GATEFIELD:
        want -= 1                                       # the unwarm end thins to nothing
    draw = LANEDRAW[_key]
    for w in range(want):
        # the spot: a fraction along the lane's own polyline, by arc length
        target = _span * (w + 1) / (want + 1.0)
        acc, px, py, pz, tx, ty = 0.0, draw[0][0], draw[0][1], draw[0][2], 1.0, 0.0
        for p_, q_ in zip(draw, draw[1:]):
            L_ = math.hypot(q_[0] - p_[0], q_[1] - p_[1])
            if acc + L_ >= target and L_ > 1e-6:
                u = (target - acc) / L_
                px, py = p_[0] + (q_[0] - p_[0]) * u, p_[1] + (q_[1] - p_[1]) * u
                pz = p_[2] + (q_[2] - p_[2]) * u
                tx, ty = (q_[0] - p_[0]) / L_, (q_[1] - p_[1]) / L_
                break
            acc += L_
        kind = ("handcart", "woodpile")[(nincident + len(_key)) % 2]
        bw_, bd_, bh_ = (1.85, 0.95, 0.85) if kind == "handcart" else (1.55, 0.85, 0.75)
        # SEARCHED OFF THE LANE EDGE, never on walk surface: both verges, stepping out.
        found = None
        for off in (1.7, 2.2, 2.8, 3.4):
            for sgn in (-1, 1):
                lx, ly = px - ty * off * sgn, py + tx * off * sgn
                if occupied(lx, ly) or not corridor_clear(lx, ly, 0.55):
                    continue
                if BPOLY and brook_d(lx, ly) < BW / 2 + 1.0:
                    continue
                if any(in_rect(lx, ly, foot_rect(o), 0.45) for o in D["landmarks"]
                       if o.get("class") not in ("area", "dressing") and bodysize(o)[0] > 0
                       and math.hypot(o["pos"][0] - lx, o["pos"][1] - ly) < 9.0):
                    continue
                if any(math.hypot(lx - f[0], ly - f[1]) < 1.6 for f in LAMPFEET):
                    continue
                g = ground_z(lx, ly)
                if abs(g - pz) > 1.0:
                    continue
                found = (lx, ly, g)
                break
            if found:
                break
        if found is None:
            print("    incident REFUSED on %s at %.1f m — no clear verge" % (_key, target))
            continue
        lx, ly, lz = found
        box("lm_incident_%02d_%s_%s" % (nincident, _key, kind), lx, ly, lz + bh_ / 2,
            bw_, bd_, bh_, M_TIMBER, "EMB_MASSING", math.atan2(ty, tx))
        print("    lm_incident_%02d  %-9s on %-34s %.1f m along, %.1f m off the lane"
              % (nincident, kind, _key, target, math.hypot(lx - px, ly - py)))
        nincident += 1
print("  lm_incident_*          %d REVIEW-AID blocks on lanes >= 15 m (map `laneIncident`;"
      " the real dressing is the district pass, post-ratification)" % nincident)

# ------------------------------------------------- area floors, with the holes --
# 0.45 m, not 0.70.  A cell is kept or dropped by its CENTRE, so the cut's margin has
# to be half a cell — and at 0.70 that margin (0.63) took Festival Square's walkable
# floor down to 24 m2, which is not a square a Kindling Hour crowd can stand in
# (`impliedScale`, technique 3).  Halving the cell halves the margin and follows every
# footprint's real edge; the plaza is one mesh either way, so the cost is vertices in a
# file that has them to spare.
CELL = 0.45
narea = 0
for l in D["landmarks"]:
    if l.get("class") != "area" or l["id"] in WATER_LM:
        continue
    i, (x, y, z) = l["id"], l["pos"]
    r = l.get("extent", 3)
    holes = []
    for o in D["landmarks"]:
        if o["id"] == i or o.get("class") in ("area", "dressing"):
            continue
        ox, oy, _oz = o["pos"]
        if math.hypot(ox - x, oy - y) > r + 6:
            continue
        hw, hd = bodysize(o)
        if hw <= 0 or "bridge" in (o.get("name") or "").lower():
            continue                                    # a bridge deck IS floor
        holes.append(foot_rect(o))
    holes += [f for f in LAMPFEET
              if math.hypot(f[0] - x, f[1] - y) <= r + 1]
    n = int(math.ceil(r / CELL))
    v, f, ncell = [], [], 0
    for a in range(-n, n):
        for b in range(-n, n):
            cx, cy = x + (a + 0.5) * CELL, y + (b + 0.5) * CELL
            if math.hypot(cx - x, cy - y) > r - CELL * 0.5:
                continue
            # PAD = 0.28 + CELL/2.  A cell is kept or dropped by its CENTRE, so a bare
            # 0.28 pad leaves cells straddling a building's wall by up to half a cell,
            # and GateGrid samples inside those overhangs — which is exactly how 32
            # pieces of Festival Square's first real build came out standing on
            # walkable floor.  Half a cell is the honest margin.
            if any(in_rect(cx, cy, h, 0.28 + CELL / 2) for h in holes):
                continue
            if BPOLY and brook_d(cx, cy) < BW / 2 + 0.5:
                continue                                # the brook is not floor
            base = len(v)
            for dz in (0.0, -0.14):
                for dx, dy in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
                    v.append((cx + dx * CELL, cy + dy * CELL, z + dz))
            f += [(base, base + 3, base + 2, base + 1), (base + 4, base + 5, base + 6, base + 7),
                  (base, base + 1, base + 5, base + 4), (base + 1, base + 2, base + 6, base + 5),
                  (base + 2, base + 3, base + 7, base + 6), (base + 3, base, base + 4, base + 7)]
            ncell += 1
    assert ncell, "area '%s' has no walkable cell after cutting %d footprints" % (i, len(holes))
    mesh("walk_lm_" + i, v, f, M_COBBLE if l.get("kind") == "plaza" else M_EARTH, "EMB_PATHS")
    narea += 1
    print("    walk_lm_%-16s %3d cells @ %.1f m, %d footprints cut" % (i, ncell, CELL, len(holes)))
print("  walk_lm_*              %d area floors" % narea)

rebuild_occ()
rebuild_wcut()
build_ground()          # LAST, so the road cut sees the whole walkable town


# ====================================================================== water ==
# All three bodies are `water_` — never walkable, always cut against the walk footprint.
WCELL = 0.55


def water_field(name, inside_fn, level_fn, x0, x1, y0, y1, cut=True):
    v, f, n = [], [], 0
    for a in range(int(math.floor(x0 / WCELL)), int(math.ceil(x1 / WCELL))):
        for b in range(int(math.floor(y0 / WCELL)), int(math.ceil(y1 / WCELL))):
            cx, cy = (a + 0.5) * WCELL, (b + 0.5) * WCELL
            if not inside_fn(cx, cy) or (cut and occupied(cx, cy)):
                continue
            z = level_fn(cx, cy)
            base = len(v)
            for dz in (0.0, -0.12):
                for dx, dy in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
                    v.append((cx + dx * WCELL, cy + dy * WCELL, z + dz))
            f += [(base, base + 3, base + 2, base + 1), (base + 4, base + 5, base + 6, base + 7),
                  (base, base + 1, base + 5, base + 4), (base + 1, base + 2, base + 6, base + 5),
                  (base + 2, base + 3, base + 7, base + 6), (base + 3, base, base + 4, base + 7)]
            n += 1
    if n:
        mesh(name, v, f, M_WATER, "EMB_WATER")
    return n


nw = 0
for wid in sorted(WATER_LM):
    l = LM[wid]
    px, py, pz = l["pos"]
    r = l.get("extent", 5)
    n = water_field("water_emb_" + wid,
                    lambda x, y, px=px, py=py, r=r: math.hypot(x - px, y - py) <= r,
                    lambda x, y, pz=pz: pz, px - r - 1, px + r + 1, py - r - 1, py + r + 1)
    print("    water_emb_%-13s %3d cells, r %.1f at z %.2f" % (wid, n, r, pz))
    nw += n
    bv, bf = [], []
    for ring in range(4):
        rr = r * (1.0 - ring / 4.0)
        dz = -0.18 - 1.6 * (ring / 3.0) ** 1.5
        for k in range(32):
            a = 2 * math.pi * k / 32
            bv.append((px + rr * math.cos(a), py + rr * math.sin(a), pz + dz))
    for ring in range(3):
        for k in range(32):
            nn = (k + 1) % 32
            bf.append((ring * 32 + k, ring * 32 + nn, (ring + 1) * 32 + nn, (ring + 1) * 32 + k))
    mesh("emb_pondbed_" + wid, bv, bf, M_EARTH, "EMB_CONTEXT")

if BPOLY:
    def brook_level(x, y):
        best, bz = 1e9, BPOLY[0][2]
        for p in BPOLY:
            d = (x - p[0]) ** 2 + (y - p[1]) ** 2
            if d < best:
                best, bz = d, p[2]
        return bz

    bx = [p[0] for p in BPOLY]
    by = [p[1] for p in BPOLY]
    # THE BROOK IGNORES THE WALK FOOTPRINT, and that is the opposite of the pond's
    # rule for a reason: a watercourse is CONTINUOUS or it is not a watercourse, and
    # where a road crosses it the culverts below carry the road OVER the water rather
    # than deleting the water.  Cutting the brook against the roads first (measured)
    # left 50 of 150 cells and a stream that vanished three times between its spring
    # and the pond.
    n = water_field("water_emb_brook", lambda x, y: brook_d(x, y) <= BW / 2, brook_level,
                    min(bx) - 2, max(bx) + 2, min(by) - 2, max(by) + 2, cut=False)
    run = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(BPOLY, BPOLY[1:]))
    chord = math.hypot(BPOLY[-1][0] - BPOLY[0][0], BPOLY[-1][1] - BPOLY[0][1])
    # HOW FAR THE STREAM EVER GETS FROM A RULED LINE, which is the honest measure of
    # "reads as a stream" and the one the review board needs: chaikin can round the
    # corners the map authored, it cannot invent a meander the map did not.
    swing = max(math.sqrt(seg_dist2(p[0], p[1], BPOLY[0][0], BPOLY[0][1],
                                    BPOLY[-1][0], BPOLY[-1][1])) for p in BPOLY)
    print("    water_emb_brook       %3d cells, %.1f m wide, %.1f m of run over a %.1f m "
          "chord (sinuosity %.3f, chaikin-smoothed; widest swing off the chord %.1f m), "
          "falling %.2f m"
          % (n, BW, run, chord, run / max(chord, 1e-6), swing, BPOLY[0][2] - BPOLY[-1][2]))
    nw += n

if RCRS:
    # A RIBBON SKINNED ALONG THE COURSE — no longer a slab on an axis (rule 8), and still
    # not a cell field: the river is a VISTA the map says is "vista only, never walkable",
    # nothing walkable comes within 20 m of it, and 3 000 cells of water nobody can reach
    # is 24 000 vertices spent on a thing no camera resolves.  Two vertices per course
    # sample, offset along the segment normal by the bank width the map authored THERE,
    # so every meander is in the water itself and the channel narrows and widens the way
    # the course says it does.
    rv, rf = [], []
    for k, (px, py, pw) in enumerate(RCRS):
        if k == 0:
            tx, ty = RCRS[1][0] - px, RCRS[1][1] - py
        elif k == len(RCRS) - 1:
            tx, ty = px - RCRS[-2][0], py - RCRS[-2][1]
        else:                                           # the central difference: a normal
            tx = RCRS[k + 1][0] - RCRS[k - 1][0]        # that turns with the bend instead
            ty = RCRS[k + 1][1] - RCRS[k - 1][1]        # of stepping at every vertex
        tl = math.hypot(tx, ty) or 1.0
        nx_, ny_ = -ty / tl * pw / 2.0, tx / tl * pw / 2.0
        rv.append((px + nx_, py + ny_, RLVL))
        rv.append((px - nx_, py - ny_, RLVL))
    for k in range(len(RCRS) - 1):
        rf.append((2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1))
    mesh("water_emb_river", rv, rf, M_WATER, "EMB_WATER")
    _run = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(RCRS, RCRS[1:]))
    _chord = math.hypot(RCRS[-1][0] - RCRS[0][0], RCRS[-1][1] - RCRS[0][1])
    _ws = [p[2] for p in RCRS]
    print("    water_emb_river     %4d quads along the course: %.1f m of run over a "
          "%.1f m chord (sinuosity %.2f), %.1f-%.1f m between banks at z %.2f"
          % (len(rf), _run, _chord, _run / max(_chord, 1e-6), min(_ws), max(_ws), RLVL))
print("  water_*                %d cells total" % nw)

# ------------------------------------------------------ culverts under the roads --
# Where a walk ribbon crosses the brook and no footbridge stands within 3 m, the road
# would hover over open water.  Found by measurement, founded in stone, and PRINTED —
# a floating road reads as art until somebody walks it.
ncul = 0
CULV = []
if BPOLY:
    seen = []
    for (a, b, wdt, ekey) in RIBSEGS:
        for k in range(9):
            t = k / 8.0
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            z = a[2] + (b[2] - a[2]) * t
            if brook_d(x, y) > BW / 2 + 0.35:
                continue
            if any(math.hypot(x - bx_, y - by_) < 3.0 for (bx_, by_, _bz) in BRIDGES):
                continue
            if any(math.hypot(x - sx, y - sy) < 2.4 for (sx, sy) in seen):
                continue
            seen.append((x, y))
            near = [p[2] for p in BPOLY if math.hypot(p[0] - x, p[1] - y) < 2.5]
            bz = min(near) if near else z - 0.5
            box("emb_culvert_%02d_deck" % ncul, x, y, z - 0.21, wdt + 0.9, 2.6, 0.30,
                M_STONE, "EMB_CONTEXT")
            for si, sgn in enumerate((-1, 1)):
                hgt = max(0.4, (z - 0.36) - (bz - 0.6))
                box("emb_culvert_%02d_abut%d" % (ncul, si), x, y + sgn * 1.15,
                    (z - 0.36 + bz - 0.6) / 2, wdt + 0.9, 0.5, hgt, M_STONE, "EMB_CONTEXT")
            print("    CULVERT %d at (%.1f, %.1f) on %-32s road z %.2f over brook z %.2f"
                  % (ncul, x, y, ekey, z, bz))
            CULV.append(ekey)
            ncul += 1
print("  emb_culvert_*          %d road-over-brook crossings" % ncul)
# A LANE THAT NEEDS THREE CULVERTS IS NOT CROSSING THE BROOK, IT IS RUNNING DOWN IT — and
# that is a MAP fact, not a build fact, so it is named here for the review board rather
# than papered over with more stone.
for _k in sorted(set(CULV)):
    if CULV.count(_k) >= 3:
        print("    NOTE  %s founds %d culverts — the lane runs ALONGSIDE the brook rather "
              "than across it (a map question: one bridge, or the lane nudged off the "
              "water)" % (_k, CULV.count(_k)))



# ================================================================ sun + world ==
sun = bpy.data.lights.new("EMB_sun", 'SUN')
sun.energy = 3.6
sun.color = (1.0, 0.86, 0.68)
sun.angle = math.radians(1.6)
so = bpy.data.objects.new("EMB_sun", sun)
# golden late afternoon out of the south-west, where the shipped Chapter One backdrops
# put it: long shadows across the square, the buildings' fronts warm
so.rotation_euler = (math.radians(56), 0.0, math.radians(212))
coll("EMB_LIGHTS").objects.link(so)

w = bpy.data.worlds.get("EMB_world") or bpy.data.worlds.new("EMB_world")
bpy.context.scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.30, 0.34, 0.42, 1)
bg.inputs[1].default_value = 1.15

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"

# ====================================================================== audit ==
print("-" * 78)


def pfx(p):
    return [o for o in bpy.data.objects if o.name.startswith(p)]


print("  walk_ %d   bar_ %d   veg_ %d   water_ %d   lm_ %d   emb_ %d   total %d"
      % (len(pfx("walk_")), len(pfx("bar_")), len(pfx("veg_")), len(pfx("water_")),
         len(pfx("lm_")), len(pfx("emb_")), len(bpy.data.objects)))
print("  vertices %d" % sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))

# THE RIVER IS A VISTA, and that is now MEASURED rather than asserted in a comment.  The
# map's words are "vista only, never walkable"; the instrument is the distance from the
# nearest walk vertex in the town to the water's own edge.
if RCRS:
    worstd, worstn = 1e9, "-"
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith("walk_"):
            continue
        for v in o.data.vertices:
            wv = o.matrix_world @ v.co
            dd, hh = river_at(wv.x, wv.y)
            if dd - hh / 2 < worstd:
                worstd, worstn = dd - hh / 2, o.name
    print("  river clearance        nearest walk surface is %.1f m from the water's edge "
          "(%s)" % (worstd, worstn))
    assert worstd > 3.0, "a walk surface reaches the river bank: %s at %.2f m" % (worstn, worstd)

# LANE LENGTHS, for the lane-incident work-list (map `laneIncident`, user 2026-08-01).
# Nothing is placed here — the incidents are the district pass's dressing layer — but the
# blockout is where the runs are known, so it says which lanes are long enough to need
# pacing and how far apart Lake's lamps ended up along them.
LONG = sorted(((v, k) for k, v in RUNS.items() if v >= 15.0), reverse=True)
print("  lanes >= 15 m          %d of %d (the laneIncident work-list for the district pass)"
      % (len(LONG), len(RUNS)))
for (v, k) in LONG:
    print("      %6.1f m  %s" % (v, k))
if len(LAMPFEET) > 1:
    gaps = sorted(min(math.hypot(a[0] - b[0], a[1] - b[1])
                      for b in LAMPFEET if b is not a) for a in LAMPFEET)
    print("  lamp spacing           nearest-neighbour %.1f m median, %.1f m worst "
          "(%d lamps, map canon)" % (gaps[len(gaps) // 2], gaps[-1], len(LAMPFEET)))

# COVERAGE, asserted HERE so a missing mesh is a build failure and not a camera mystery
# three tools downstream: cine_regions proves ownership BY NAME, so a landmark or edge
# with no named geometry is a silent hole in the coverage proof.
missing = []
for l in D["landmarks"]:
    i = l["id"]
    cls = l.get("class", "structure")
    if cls == "dressing":
        continue
    if i in WATER_LM:
        if not any(o.name == "water_emb_" + i for o in bpy.data.objects):
            missing.append("water_emb_" + i)
    elif cls == "area":
        if not any(o.name == "walk_lm_" + i for o in bpy.data.objects):
            missing.append("walk_lm_" + i)
    elif (l.get("kind") or "") == "heartlight":
        if not any(o.name.startswith("lm_%s_" % i) for o in bpy.data.objects):
            missing.append("lm_%s_*" % i)
    else:
        dx, dy, _dz = DOOR[i]
        if not any(o.name == "walk_pad_" + i for o in bpy.data.objects) \
                and not in_area(dx, dy, -0.9):
            missing.append("walk_pad_" + i)
for e in EDGES:
    k = "%s__%s" % (e["from"], e["to"])
    if k in SWALLOWED:
        continue                                        # its floor is the area's, counted above
    if not any(o.name.startswith("walk_e_%s_l" % k) for o in bpy.data.objects):
        missing.append("walk_e_%s_l*" % k)
assert not missing, "NO GEOMETRY for: %s" % missing
print("  COVERAGE OK — every landmark and every edge has named geometry")

# a parcel member that no longer names a real landmark: a rename that missed a reference
for p in D.get("parcels", []):
    for mid in p.get("members", []):
        if mid not in LM:
            print("  MAP WARN  parcel %s names member '%s', which is not a landmark"
                  % (p["id"], mid))

if DIGEST:
    h = hashlib.sha256()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        h.update(o.name.encode())
        if o.type == 'MESH':
            for v in o.data.vertices:
                h.update(("%.4f,%.4f,%.4f;" % (v.co.x, v.co.y, v.co.z)).encode())
        else:
            h.update(("%.4f,%.4f,%.4f;" % tuple(o.location)).encode())
    print("DIGEST %s" % h.hexdigest())

if not NOSAVE:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print("SAVED %s" % OUT)
