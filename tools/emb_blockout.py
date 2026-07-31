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


# The mill's impoundment, set by the landmark pass and consulted by `ground_z` (which is
# defined below it and called long before): declared here so the name exists from the
# first call, empty until there is a mill to fill it.
MILLPOND = None
MILLPOND_R = 3.4


def brook_nearest(x, y):
    """(index of the closest brook sample, distance).  The mill, its wheel, its leat and
    the weir all SNAP to the stamped course — the map says so in as many words — so all
    four ask the course where it is and which way it is running rather than carrying
    authored angles that a re-stamped brook would silently invalidate."""
    if not BPOLY:
        return 0, 1e9
    k = min(range(len(BPOLY)),
            key=lambda n: (BPOLY[n][0] - x) ** 2 + (BPOLY[n][1] - y) ** 2)
    return k, math.hypot(BPOLY[k][0] - x, BPOLY[k][1] - y)


def brook_bearing(x, y):
    if not BPOLY or len(BPOLY) < 2:
        return 0.0
    k, _ = brook_nearest(x, y)
    a = BPOLY[max(0, k - 3)]
    b = BPOLY[min(len(BPOLY) - 1, k + 3)]
    return math.atan2(b[1] - a[1], b[0] - a[0])


def wheelset(name, cx, cy, cz, r, wid, rzn, m, cname, spokes=8):
    """An overshot wheel as a coarse cylinder on a HORIZONTAL axis — blockout massing,
    explicitly allowed to be coarse by the map's own quality ruling.  `rzn` is the
    direction of the axle in plan (square to the flow)."""
    ax_, ay_ = math.cos(rzn), math.sin(rzn)
    ux, uy = -ay_, ax_                                  # the wheel's own plane, in plan
    v, f = [], []
    for side in (-1, 1):
        ox, oy = ax_ * wid / 2 * side, ay_ * wid / 2 * side
        for k in range(spokes * 2):
            a = 2 * math.pi * k / (spokes * 2)
            v.append((cx + ox + ux * r * math.cos(a), cy + oy + uy * r * math.cos(a),
                      cz + r * math.sin(a)))
    n = spokes * 2
    for k in range(n):
        nn = (k + 1) % n
        f.append((k, nn, n + nn, n + k))                # the rim / the buckets
    return mesh(name, v, f, m, cname)


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
    # THE MILLPOND IS AN IMPOUNDMENT, WHICH MEANS A BASIN AND A DAM, and the first draft
    # of it was neither: the water surface was simply raised by the dam height and came
    # out as a 1.2 m slab of water lying on a hillside.  A pond that is held back has
    # ground DUG OUT under it and a bank ACROSS it, so both are built — the basin here,
    # the dam as massing beside the wheel.  `MILLPOND` is set during the landmark pass and
    # the ground mesh is raised last, so by the time this matters the value exists.
    if MILLPOND:
        _mx, _my, _ml = MILLPOND
        _dm = math.hypot(x - _mx, y - _my)
        if _dm < MILLPOND_R + 2.2:
            _t = max(0.0, min(1.0, (_dm - MILLPOND_R) / 2.2))
            z = min(z, (_ml - 0.95) * (1 - _t) + z * _t)
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
RIMFEET = []                    # the Whisperwood corridor below interlocks with these
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
        # THE LIVED-IN SET (map 2026-08-01).  Each of these is a footprint measured off
        # what the massing below actually builds, for the same reason the footbridge's
        # was: `foot_rect` is what cuts an area floor and what every clearance search
        # tests against, so a landmark default in place of a real size is a lie that
        # lands as a hole in the plaza or a lamp inside a wall.
        if "weir" in nm or "sluice" in nm:
            return (3.8, 1.5)                           # a sill across the brook
        if "dais" in nm:
            return (4.0, 3.0)
        if "bell" in nm:
            return (1.3, 1.0)
        if "den" in nm:
            return (2.3, 1.9)
        if "bench" in nm:
            return (2.2, 0.95)                          # a bench is shallow, not a shed
        return (2.0, 1.4)
    if kind == "tower":
        return (3.2, 3.2)                               # the dovecote: round, and tall
    if kind == "hut":
        return (3.4 * 1.14, 2.9 * 1.14)
    if kind == "openbarn":
        return (6.8 * 1.14, 4.8 * 1.14)
    if "mill" in nm:
        return (5.6 * 1.14, 4.6 * 1.14)                 # the wheel is built beside it
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

# ======================================= background roofs, in ONE generator ==
# A "cluster of roofs somebody lives in but nobody walks to" is now needed in TWO places
# — the `dressing` vistas OUTSIDE the playable edge (implied-scale technique 1) and the
# INFILL between the lanes (the densification ruling, 2026-08-01) — so it is one function
# rather than two copies that drift.  `district_lib.py` was created on the third copy of
# a walk guard; this is the second copy of a roof cluster and it is being merged now.
#
# EVERYTHING ABOUT A CLUSTER IS DERIVED FROM ITS SALT, so the same seed always builds the
# same hamlet and the digest gate keeps meaning what it says.
def roof_cluster(name, x, y, salt, nroof=5, spread=(3.0, 5.5), cname="EMB_CONTEXT",
                 avoid_river=True, scale=1.0, reject=None):
    """Returns the list of (x, y, ridge_z) of the roofs it actually built."""
    out = []
    for k in range(nroof):
        a = 2 * math.pi * h01(salt, k, 3) + k * 1.1
        rr = spread[0] + spread[1] * h01(salt, k, 7)
        vx, vy = x + rr * math.cos(a), y + rr * math.sin(a)
        # NO COTTAGE STANDS IN THE RIVER.  The cluster's own centre is a chosen point and
        # clears the water; a roof thrown 8.5 m off it need not, and at 2x the riverside
        # cottages' spread reaches 2.6 m past the west bank.  A roof that lands in the
        # channel is pushed straight back out to the bank + 2.5 m along the course's own
        # normal — deterministic, and it keeps the cluster's shape.
        if avoid_river and RCRS:
            _d, _hw = river_at(vx, vy)
            _want = _hw / 2 + 2.5
            if _d < _want:
                _ox, _oy = vx - x, vy - y
                _oL = math.hypot(_ox, _oy) or 1.0
                _sgn = -1.0 if _d < 1e-6 else 1.0
                vx -= _sgn * _ox / _oL * (_want - _d)
                vy -= _sgn * _oy / _oL * (_want - _d)
                print("    vista %-18s roof %d pushed %.1f m clear of the river bank"
                      % (name, k, _want - _d))
        bw = (3.6 + 2.2 * h01(salt, k, 11)) * scale
        bd = bw * (0.72 + 0.3 * h01(salt, k, 13))
        # A ROOF THAT WOULD STAND ON A LANE IS DROPPED, NOT MOVED.  Infill passes a
        # `reject` predicate (the walk-clearance test); moving the roof to satisfy it
        # would walk the cluster into the NEXT lane, which is how the first infill draft
        # put four background cottages across Home Row.  A cluster is allowed to come out
        # smaller than it asked for, and the count is reported.
        if reject is not None and reject(vx, vy, max(bw, bd) / 2):
            continue
        vz = ground_z(vx, vy)
        bh = (2.8 + 1.6 * h01(salt, k, 17)) * (0.85 + 0.15 * scale)
        vrz = h01(salt, k, 19) * math.pi
        box("%s_%d_body" % (name, k), vx, vy, vz + bh / 2, bw, bd, bh,
            M_PLASTER, cname, vrz)
        rh = 1.5 + 0.5 * h01(salt, k, 23)
        gable("%s_%d_roof" % (name, k), vx, vy, vz + bh, bw * 1.16, bd * 1.16, rh,
              M_THATCH if (h32(salt, k, 29) % 3) else M_TILE, cname, vrz)
        box("%s_%d_chim" % (name, k), vx + bw * 0.3, vy + bd * 0.28, vz + bh + 1.2,
            0.55, 0.55, 1.9, M_STONE, cname, vrz)
        # two lit windows per roof: the cheapest possible "somebody lives there"
        for wk in (-1, 1):
            box("%s_%d_win%d" % (name, k, (wk + 1) // 2),
                vx + math.cos(vrz) * wk * bw * 0.28 - math.sin(vrz) * (bd / 2 + 0.02),
                vy + math.sin(vrz) * wk * bw * 0.28 + math.cos(vrz) * (bd / 2 + 0.02),
                vz + bh * 0.62, 0.7, 0.06, 0.8, M_WINDOW, cname, vrz)
        out.append((vx, vy, vz + bh + rh))
    return out


# ================================================================== landmarks ==
# `lm_` prefixed and NON-SOLID by contract: a district builder that lands later deletes
# the `lm_` objects it replaces and nothing else in the town has to know it happened.
# EVERY WALK TOP FACE IS AT THE AUTHORED z — pads, area floors and ribbons alike — so
# where two overlap they are coplanar and `eff_top` has nothing to choose between.  (The
# first draft put them at z+0.06, z and z-0.02 and manufactured a 60 mm lip around every
# doorstep in the town.)
BRIDGES = []
LAMPABLE = []
VISTAROOFS = []
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
        VISTAROOFS.extend(roof_cluster("lm_" + i, x, y, len(i), 5))
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
        elif "weir" in nm:
            # A SILL ACROSS THE WATER AND A SLUICE YOU CAN SEE THE WINCH OF.  Its axis is
            # taken from the BROOK, not from the approach: a weir is square to the flow or
            # it is not a weir, and the flow is whatever course the map is carrying today.
            wrz = brook_bearing(x, y) + math.pi / 2
            box("lm_%s_sill" % i, x, y, z - 0.10, 3.6, 0.55, 0.90, M_STONE, "EMB_MASSING", wrz)
            for sgn in (-1, 1):
                box("lm_%s_cheek%d" % (i, (sgn + 1) // 2),
                    x + math.cos(wrz) * sgn * 1.85, y + math.sin(wrz) * sgn * 1.85,
                    z + 0.30, 0.6, 1.1, 1.1, M_STONE, "EMB_MASSING", wrz)
                box("lm_%s_post%d" % (i, (sgn + 1) // 2),
                    x + math.cos(wrz) * sgn * 1.55, y + math.sin(wrz) * sgn * 1.55,
                    z + 1.05, 0.16, 0.16, 1.5, M_TIMBER, "EMB_MASSING", wrz)
            box("lm_%s_winch" % i, x, y, z + 1.72, 3.3, 0.22, 0.22, M_TIMBER, "EMB_MASSING", wrz)
            box("lm_%s_gate" % i, x, y, z + 0.62, 2.4, 0.10, 1.0, M_TIMBER, "EMB_MASSING", wrz)
        elif "dais" in nm:
            # low, and DELIBERATELY low: it stands 2.8 m from the Heartlight's own steps
            # and anything taller would be massing in front of the thing the whole town
            # is composed around.
            box("lm_%s_deck" % i, x, y, z + 0.22, 3.8, 2.8, 0.44, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_step" % i, x + ax * 1.62, y + ay * 1.62, z + 0.08, 3.0, 0.55, 0.18,
                M_TIMBER, "EMB_MASSING", rz)
            for sgn in (-1, 1):
                box("lm_%s_newel%d" % (i, (sgn + 1) // 2),
                    x - ay * sgn * 1.75, y + ax * sgn * 1.75, z + 0.72, 0.16, 0.16, 1.0,
                    M_TIMBER, "EMB_MASSING", rz)
        elif "bell" in nm:
            for sgn in (-1, 1):
                box("lm_%s_post%d" % (i, (sgn + 1) // 2), x - ay * sgn * 0.45,
                    y + ax * sgn * 0.45, z + 1.20, 0.15, 0.15, 2.4, M_TIMBER, "EMB_MASSING", rz)
            box("lm_%s_head" % i, x, y, z + 2.45, 1.25, 0.18, 0.18, M_TIMBER, "EMB_MASSING", rz)
            pyramid("lm_%s_bell" % i, x, y, z + 2.32, 0.62, 0.62, -0.62, M_IRON, "EMB_MASSING", rz)
        elif "den" in nm:
            # planks leaned into a lean-to, a crate, a plank floor.  It is a child's fort,
            # so nothing here is square to anything.
            for k in range(4):
                box("lm_%s_plank%d" % (i, k), x - 0.55 + k * 0.36, y, z + 0.62,
                    0.24, 1.7, 0.07, M_TIMBER, "EMB_MASSING", rz + 0.42 + 0.06 * k)
            box("lm_%s_crate" % i, x + 0.85, y - 0.55, z + 0.28, 0.62, 0.62, 0.56,
                M_TIMBER, "EMB_MASSING", rz + 0.7)
            box("lm_%s_floor" % i, x, y, z + 0.05, 2.0, 1.5, 0.10, M_TIMBER, "EMB_MASSING", rz)
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
    elif kind == "tower":
        # THE DOVECOTE — the map asks the Gate Field for "a vertical accent that is not
        # the gate", so it is round, tall for its footprint, and capped.
        disc("lm_%s_shaft" % i, x, y, z + 4.1, 1.5, 4.1, M_PLASTER, "EMB_MASSING", seg=16)
        disc("lm_%s_plinth" % i, x, y, z + 0.42, 1.75, 0.42, M_STONE, "EMB_MASSING", seg=16)
        disc("lm_%s_band" % i, x, y, z + 3.5, 1.68, 0.3, M_TIMBER, "EMB_MASSING", seg=16)
        pyramid("lm_%s_cap" % i, x, y, z + 4.1, 3.5, 3.5, 1.7, M_TILE, "EMB_MASSING")
        box("lm_%s_door" % i, x + ax * 1.5, y + ay * 1.5, z + 0.95, 0.9, 0.16, 1.9,
            M_TIMBER, "EMB_MASSING", rz)
    elif kind == "openbarn":
        # THE CIDER PRESS BARN — open-sided by definition: posts, a plate, a big roof and
        # one gable end.  Building it as a closed box would hide the only thing in it.
        bw, bd, bh = 6.8, 4.8, 3.1
        for sx_ in (-1, 1):
            for sy_ in (-1, 1):
                box("lm_%s_post%d%d" % (i, (sx_ + 1) // 2, (sy_ + 1) // 2),
                    x + (math.cos(rz) * sx_ * bw / 2 - math.sin(rz) * sy_ * bd / 2),
                    y + (math.sin(rz) * sx_ * bw / 2 + math.cos(rz) * sy_ * bd / 2),
                    z + bh / 2, 0.26, 0.26, bh, M_TIMBER, "EMB_MASSING", rz)
        box("lm_%s_plate" % i, x, y, z + bh + 0.12, bw + 0.3, bd + 0.3, 0.24,
            M_TIMBER, "EMB_MASSING", rz)
        box("lm_%s_gableend" % i, x - ax * bd / 2, y - ay * bd / 2, z + bh / 2,
            bw * 0.98, 0.22, bh, M_TIMBER, "EMB_MASSING", rz)
        gable("lm_%s_roof" % i, x, y, z + bh + 0.24, bw * 1.16, bd * 1.20, 1.5,
              M_THATCH, "EMB_MASSING", rz)
        box("lm_%s_press" % i, x, y, z + 0.55, 1.5, 1.5, 1.1, M_TIMBER, "EMB_MASSING", rz)
    elif kind == "hut":
        # the spring house and the smokehouse: one small stone room, one steep roof
        bw, bd, bh = 3.4, 2.9, 2.35
        box("lm_%s_body" % i, x, y, z + bh / 2, bw, bd, bh, M_STONE, "EMB_MASSING", rz)
        gable("lm_%s_roof" % i, x, y, z + bh, bw * 1.16, bd * 1.16, 1.35,
              M_SLATE if "smoke" in nm else M_THATCH, "EMB_MASSING", rz)
        box("lm_%s_door" % i, x + ax * (bd / 2 + 0.03), y + ay * (bd / 2 + 0.03),
            z + 0.85, 0.85, 0.14, 1.7, M_TIMBER, "EMB_MASSING", rz)
        if "smoke" in nm:                               # Finn's: the racks and the skiff
            box("lm_%s_flue" % i, x, y, z + bh + 1.5, 0.45, 0.45, 1.5, M_STONE,
                "EMB_MASSING", rz)
            for k in range(3):
                box("lm_%s_rack%d" % (i, k), x - ay * (2.4 + k * 0.9) - ax * 1.2,
                    y + ax * (2.4 + k * 0.9) - ay * 1.2, z + 0.75, 2.0, 0.10, 1.5,
                    M_TIMBER, "EMB_MASSING", rz)
    elif "mill" in nm:
        # THE WATERMILL, and everything about it is derived from the stamped brook: the
        # wheel hangs on the bank the mill stands on, its axle is square to the flow, and
        # the leat runs from upstream to the wheel's own crown.  An overshot wheel needs
        # the water delivered ABOVE it, so the leat is a raised launder rather than a
        # ditch — that is the whole reason the mill wants a reach with fall.
        bw, bd, bh = 5.6, 4.6, 5.2
        box("lm_%s_base" % i, x, y, z + 0.7, bw, bd, 1.4, M_STONE, "EMB_MASSING", rz)
        box("lm_%s_body" % i, x, y, z + 1.4 + (bh - 1.4) / 2, bw * 0.97, bd * 0.97,
            bh - 1.4, M_TIMBER, "EMB_MASSING", rz)
        gable("lm_%s_roof" % i, x, y, z + bh, bw * 1.14, bd * 1.14, 1.9, M_TILE,
              "EMB_MASSING", rz)
        box("lm_%s_door" % i, x + ax * (bd / 2 + 0.03), y + ay * (bd / 2 + 0.03),
            z + 1.05, 1.2, 0.16, 2.1, M_TIMBER, "EMB_MASSING", rz)
        bk, bdist = brook_nearest(x, y)
        if BPOLY:
            brg = brook_bearing(x, y)
            bx_, by_, bz_ = BPOLY[bk]
            # the wheel stands ON the water, half-way between the mill wall and the
            # channel's centre, with its axle square to the flow
            wx = (x + bx_) / 2.0
            wy = (y + by_) / 2.0
            # THE WHEEL IS SIZED BY THE HEAD THE BROOK ACTUALLY HAS, and this is the one
            # place the mill's romance meets a valley 108 m across with 2.4 m of fall in
            # its whole brook.  An overshot wheel's diameter cannot exceed the drop from
            # the leat's crown to its tailrace: dam + the natural fall the leat bypasses.
            # An authored radius would have produced a wheel standing in the bed or
            # hanging in the air; this one is MEASURED and PRINTED.  The first pass
            # measured 1.55 m of wheel on a 1.20 m dam and REPORTED it rather than
            # inflating it; the user's ruling on that report was option (b) — a 2.00 m
            # dam and the bigger impoundment that goes with it, picturesque over strict
            # hydrology, with breastshot and the small wheel recorded as alternates.  The
            # head is still printed every run, which is the point: the ruling was made on
            # a number and it stays checkable against one.
            MILL_DAM = 2.00
            uk0 = max(0, bk - 16)
            head = (BPOLY[uk0][2] + MILL_DAM) - bz_
            WR = max(0.55, min(1.85, head / 2.0))
            wz = bz_ + WR - 0.35
            wheelset("lm_%s_wheel" % i, wx, wy, wz, WR, 0.9, brg + math.pi / 2,
                     M_TIMBER, "EMB_MASSING")
            box("lm_%s_axle" % i, wx, wy, wz, 2.4, 0.22, 0.22, M_TIMBER, "EMB_MASSING",
                brg + math.pi / 2)
            # THE LEAT: a launder on trestles, running from the millpond to the crown
            ux_, uy_, uz_ = BPOLY[uk0]
            nseg = 5
            for k in range(nseg):
                t0, t1 = k / float(nseg), (k + 1) / float(nseg)
                px0, py0 = ux_ + (wx - ux_) * t0, uy_ + (wy - uy_) * t0
                px1, py1 = ux_ + (wx - ux_) * t1, uy_ + (wy - uy_) * t1
                lz = (uz_ + MILL_DAM) + (wz + WR - (uz_ + MILL_DAM)) * (t0 + t1) / 2.0
                ribbon("lm_%s_leat%d" % (i, k), (px0, py0, lz), (px1, py1, lz),
                       1.0, 0.35, M_TIMBER, "EMB_MASSING")
                tz = ground_z(px1, py1)
                if lz - tz > 0.6:
                    box("lm_%s_trestle%d" % (i, k), px1, py1, (lz + tz) / 2,
                        0.9, 0.20, lz - tz, M_TIMBER, "EMB_MASSING", brg)
            MILLPOND = (ux_, uy_, uz_ + MILL_DAM)
            # THE IMPOUNDMENT IS A RING, NOT A WALL, and the arithmetic of the user's own
            # ruling is why.  A 2.00 m dam holds the pond 2.00 m ABOVE the brook it stands
            # on, and the ground beside a brook on a gentle rise is not 2 m higher — so a
            # single wall across the channel leaves water standing in the air on three
            # sides.  What a hillside corn mill actually has is a POUND: a tank dug into
            # the slope uphill and EMBANKED on the rest, with the dam proper (the wide
            # one, carrying the head gate) across the downstream lip.  `ground_z` carves
            # the basin; this is the bank that holds it, and it is only built where the
            # natural ground is too low to do the job itself.
            _dbrg = brook_bearing(ux_, uy_)
            _dlvl = uz_ + MILL_DAM
            _nbank = 0
            for _bk in range(14):
                _ba_ = 2 * math.pi * _bk / 14
                _bx_ = ux_ + (MILLPOND_R + 0.85) * math.cos(_ba_)
                _by_ = uy_ + (MILLPOND_R + 0.85) * math.sin(_ba_)
                if abs(((_ba_ - _dbrg + math.pi) % (2 * math.pi)) - math.pi) < 0.55:
                    continue                            # the DAM stands on this arc
                _bg_ = ground_z(_bx_, _by_)
                if _bg_ >= _dlvl + 0.15:
                    continue                            # the slope already holds it here
                box("lm_%s_bank%02d" % (i, _bk), _bx_, _by_,
                    (_bg_ - 0.4 + _dlvl + 0.35) / 2, 2.6, 1.5,
                    (_dlvl + 0.35) - (_bg_ - 0.4), M_EARTH, "EMB_MASSING",
                    _ba_ + math.pi / 2)
                _nbank += 1
            _ddx, _ddy = math.cos(_dbrg), math.sin(_dbrg)
            _dgz = ground_z(ux_ + _ddx * (MILLPOND_R + 0.85),
                            uy_ + _ddy * (MILLPOND_R + 0.85))
            box("lm_%s_dam" % i, ux_ + _ddx * (MILLPOND_R + 0.85),
                uy_ + _ddy * (MILLPOND_R + 0.85), (_dgz - 0.6 + _dlvl + 0.45) / 2,
                8.0, 2.4, (_dlvl + 0.45) - (_dgz - 0.6), M_STONE, "EMB_MASSING",
                _dbrg + math.pi / 2)
            box("lm_%s_headgate" % i, ux_ + _ddx * (MILLPOND_R + 0.85),
                uy_ + _ddy * (MILLPOND_R + 0.85), _dlvl + 1.05,
                1.5, 0.26, 1.2, M_TIMBER, "EMB_MASSING", _dbrg + math.pi / 2)
            print("    millpond:  a banked POUND — water held at z %.2f by %d embankment "
                  "sections plus the dam across the lip; %.2f m of it stands above the "
                  "natural ground, which is what a 2.00 m head costs on a slope this "
                  "gentle" % (_dlvl, _nbank, _dlvl - _dgz))
            print("    watermill: HEAD %.2f m (%.2f m of natural fall over the leat's "
                  "%.1f m + a %.2f m dam) -> an OVERSHOT wheel %.2f m across, on the "
                  "brook at (%.1f, %.1f); the mill wall stands %.1f m off the water"
                  % (head, head - MILL_DAM, math.hypot(wx - ux_, wy - uy_), MILL_DAM,
                     WR * 2, bx_, by_, bdist))
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
#
# THE ROLL IS FOURTEEN AND THAT IS NOW ASSERTED.  Two round-2 redlines each tried to grow
# it and neither is a lamp decision: the WHISPERWOOD district is outside the warmth by
# construction (the arch is the first lamplight the player ever sees — that reveal is the
# whole point of the opening), and the ten lived-in landmarks are OUTBUILDINGS, not homes,
# which is what §2's "a lamppost near every home" actually says.  Left alone, the arrival
# clearing and the mill and the dovecote and the dais and the rest took the round from 14
# to 22.  So: the woodroad district hosts no lamp at all, the new set is denied by name,
# and the COUNT is asserted — a future map that means to change the roll will fail this
# build and get to say so out loud.
NO_LAMP_DISTRICT = {"woodroad"}
NO_LAMP = {"waystone", "sigil-gate", "forest-trailhead", "heartlight", "home-lane-end",
           "notice-board", "well", "brook-spring", "brook-mouth", "gate-court",
           # the lived-in set, 2026-08-01: sheds, stores, a mill and a bell are not homes
           "watermill", "spring-house", "pond-weir", "cider-press", "dovecote",
           "festival-dais", "village-bell", "pips-den", "smokehouse",
           "grandmothers-bench"}
LAMP_ROLL = 14                                          # map `lamps._doc`, user-ruled
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
    if l.get("district") in NO_LAMP_DISTRICT:
        continue                                        # the wood is outside the warmth
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
    # THE RING WIDENED, and the ten lived-in landmarks are why.  Finn's smokehouse now
    # stands 2.5 m off the jetty's own deck and Lake's FIRST stop — "low ground first,
    # POND LANE, where the moths come off the water" — was refused for want of 1.0 m of
    # search.  The round is canon and a refusal in it is not a build outcome to accept
    # quietly, so the ring reaches further before it gives up; the radius each lamp
    # actually needed is printed, because a lamp 3.9 m from its host is a fact about the
    # map's density that the district pass will want.
    for r in (1.9, 2.4, 2.9, 1.5, 3.4, 3.9):
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
            best = (lx, ly, g, r)
            break
        if best:
            break
    if best is None:
        nrefused += 1
        print("    lamp REFUSED for %-18s no foot out of the walk corridor" % hid)
        continue
    lx, ly, lz, lr = best
    if lr > 2.9:
        print("    lamp %-18s foot found only at %.1f m — its host is crowded" % (hid, lr))
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
assert nlamp == LAMP_ROLL, (
    "Lake's round is map canon at %d lamps and this build made %d (%s). A lamp added or "
    "lost is a MAP decision — see `lamps._doc` and NO_LAMP above — not a build outcome."
    % (LAMP_ROLL, nlamp, ", ".join(PLACED)))

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
AREACUT = {}
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
    v, f, ncell, nbrookcut, nsteep = [], [], 0, 0, 0
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
                nbrookcut += 1                          # the brook is not floor
                continue
            # AN AREA FLOOR STOPS WHERE A LANE CLIMBS OFF IT, and this is rule 6 arriving
            # from a new direction.  An area's floor is FLAT at the map's authored z; the
            # lanes leaving it are laid at the map's z too and CLIMB.  At the founding
            # scale the plaza was r7 and the barn lane was 0.1 m above it where they
            # overlapped, which nothing could see.  At r14 the same lane is 0.45 m above
            # the plaza's outermost ring, the ground is carved down to the LANE (it is the
            # nearest walk surface), and 97 of the plaza's own cells ended up under 0.35 m
            # of grass — walk faces that render as a bank.  The stretch belongs to the
            # lane, which already carries it, so the FLOOR gives it up: a cell under a
            # ribbon more than 0.18 m above the area's own z is not emitted.  The walk
            # network is unchanged metre for metre; only its owner moves.
            _steep = False
            for (ra_, rb_, rw_, _rk) in RIBSEGS:
                if seg_dist2(cx, cy, ra_[0], ra_[1], rb_[0], rb_[1]) > (rw_ / 2 + 0.25) ** 2:
                    continue
                if max(ra_[2], rb_[2]) - z > 0.18:
                    _steep = True
                    break
            if _steep:
                nsteep += 1
                continue
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
    # THE BROOK'S BILL, PER AREA, because the brook course's own constraints are written
    # in this currency ("cuts no cells from the r14 plaza") and a proposal has to be
    # checkable rather than argued.
    AREACUT[i] = nbrookcut
    print("    walk_lm_%-16s %3d cells @ %.1f m, %d footprints cut%s%s"
          % (i, ncell, CELL, len(holes),
             ", %d MORE cut by the brook" % nbrookcut if nbrookcut else "",
             ", %d handed to a lane climbing off it" % nsteep if nsteep else ""))
print("  walk_lm_*              %d area floors" % narea)

rebuild_occ()
rebuild_wcut()

# =============================== HOW FAR IS THE NEAREST WALK SURFACE? (GateGrid) ==
# Both of the passes below — the infill hamlets and the forest — are governed by ONE
# question asked hundreds of thousands of times: how far is this point from anything the
# player can stand on?  `walk_probe` cannot answer it (it is capped at CUT_REACH, 3 m,
# because the road cut only reaches that far), so the OCC raster gets a chamfer distance
# transform and every solid this file plants is gated on it.
#
# IT IS DELIBERATELY CONSERVATIVE.  OCC is stamped with a 0.40-0.45 m dilation around
# every walk quad, so a distance measured FROM it under-reports the true clearance by
# about that much; the chamfer's own ~2% overestimate on diagonals is an order of
# magnitude smaller.  A gate that errs toward refusing is the right sign of error — this
# is the rule that keeps a crown out of a lane, and DAYLOG finding 93 is what it costs to
# get it wrong.
def build_wdist():
    INF = 1e6
    d = [0.0 if OCC[k] else INF for k in range(ONX * ONY)]
    ao, bo = OSTEP, OSTEP * 1.4142135623730951
    for j in range(ONY):
        base = j * ONX
        for i in range(ONX):
            k = base + i
            if d[k] == 0.0:
                continue
            best = d[k]
            if i > 0:
                best = min(best, d[k - 1] + ao)
            if j > 0:
                best = min(best, d[k - ONX] + ao)
                if i > 0:
                    best = min(best, d[k - ONX - 1] + bo)
                if i < ONX - 1:
                    best = min(best, d[k - ONX + 1] + bo)
            d[k] = best
    for j in range(ONY - 1, -1, -1):
        base = j * ONX
        for i in range(ONX - 1, -1, -1):
            k = base + i
            if d[k] == 0.0:
                continue
            best = d[k]
            if i < ONX - 1:
                best = min(best, d[k + 1] + ao)
            if j < ONY - 1:
                best = min(best, d[k + ONX] + ao)
                if i < ONX - 1:
                    best = min(best, d[k + ONX + 1] + bo)
                if i > 0:
                    best = min(best, d[k + ONX - 1] + bo)
            d[k] = best
    return d


WDIST = build_wdist()


def wdist(x, y):
    i, j = int((x - X0) / OSTEP), int((y - Y0) / OSTEP)
    if not (0 <= i < ONX and 0 <= j < ONY):
        return 1e6
    return WDIST[j * ONX + i]


# every piece of standing water, as one predicate — the infill and the forest both need
# it and neither may put a cottage or a spruce in the pond
def in_water(x, y, m=0.0):
    for wid in WATER_LM:
        wx, wy, _wz = LM[wid]["pos"]
        if math.hypot(x - wx, y - wy) <= LM[wid].get("extent", 5) + m:
            return True
    if BPOLY and brook_d(x, y) < BW / 2 + 1.2 + m:
        return True
    if RCRS:
        dd, hh = river_at(x, y)
        if dd < hh / 2 + 3.0 + m:
            return True
    return False


def lm_blocked(x, y, m):
    """Inside any REAL landmark's massing footprint (plus a margin)."""
    for o in D["landmarks"]:
        if o.get("class") in ("area", "dressing") or bodysize(o)[0] <= 0:
            continue
        if math.hypot(o["pos"][0] - x, o["pos"][1] - y) > 12.0 + m:
            continue
        if in_rect(x, y, foot_rect(o), m):
            return True
    return False


# districts, by warmth.  The gradient the densification ruling asks for is stated in the
# map's own vocabulary — "thickest around Festival Square and Home Row, thinning toward
# the Gate Field and the wood" — so it is read off the districts rather than off a list
# of coordinates that a map redline would silently invalidate.
WARM_D = {"square", "homerow", "lanes"}
COLD_D = {"gatefield"}
WOOD_D = {"woodroad"}
WARMPTS = [tuple(l["pos"]) for l in D["landmarks"] if l.get("district") in WARM_D]
COLDPTS = [tuple(l["pos"]) for l in D["landmarks"] if l.get("district") in COLD_D]
WOODLM = [l for l in D["landmarks"] if l.get("district") in WOOD_D]
# THE GATEWAY IS DERIVED, NOT NAMED.  The arrival road climbs to whichever portal the
# map connects it to; hard-coding `road-gate` here would mean a map that moves the
# arrival somewhere else silently builds its wood in the wrong place.
WOOD_IDS = {l["id"] for l in WOODLM}
GATEWAY = sorted({b for e in EDGES for a, b in ((e["from"], e["to"]), (e["to"], e["from"]))
                  if a in WOOD_IDS and b not in WOOD_IDS
                  and LM.get(b, {}).get("class") == "portal"})
GATEPOS = [tuple(LM[g]["pos"]) for g in GATEWAY]
WOOD_Y1 = (max(p[1] for p in GATEPOS) + 2.0) if GATEPOS else (min(YS) + 10.0)
# the arrival road AS DRAWN — chaikin-smoothed and rim-trimmed, the same polyline the
# ribbons were built from, because that is the line the trees have to press against and
# the line the reveal probe has to walk.
WSPINE = [resample(LANEDRAW[k], 1.5) for k in sorted(LANEDRAW)
          if k.split("__")[0] in WOOD_IDS and k.split("__")[1] in WOOD_IDS]


def d_to(pts, x, y):
    return min((math.hypot(x - p[0], y - p[1]) for p in pts), default=1e9)


# ================== INFILL — the village between its own lanes, HOUSEHOLD BY HOUSEHOLD ==
# USER RULING 2026-08-01 (map `impliedScale._doc`): at 2x the village interior read sparse
# — "houses on a lawn" — so implied-scale technique 1, which had only ever been applied
# OUTSIDE the playable edge, is extended INSIDE it.  Non-enterable, never walkable,
# `lm_infill_*` so the district pass that lands later deletes them like any other
# placeholder massing.
#
# AND THEN THE REFINEMENT THAT THIS FILE IS NOW BUILT AROUND.  The first implementation
# read the ruling as "more roofs" and seeded HAMLETS — 3 to 5 cottages inside one 7 m
# hedge ring, roofs 3-4 m apart.  The user saw it in a live snapshot and named it exactly:
# unrealistic clutter, cottages packed wall to wall.  The correction is not fewer roofs,
# it is a different unit.  A village cottage is a HOUSEHOLD:
#
#   its own garden plot, hedged or fenced, with a gap you get in by
#   a fruit tree or two standing in that plot
#   a shed or a woodpile against the boundary
#   and A WAY TO REACH IT — nobody builds a house you cannot walk to.  The track is
#   non-walkable geometry (the walk network stays exactly as tight as the parcels) but it
#   is VISIBLE, and it either joins a real lane or narrows away into an implied one.
#
# So: one cottage per seed, 6-12 m apart and VARIED, and the forest fills the space
# between the garden plots instead of another roof.  Density is life per household, not
# roofs per square metre.  The 2+-roofs-visible target still stands and is still measured
# — it is met by depth and arrangement now rather than by packing.
#
# THREE THINGS THAT WENT WRONG AND ARE NOW RULES:
#  a  SEEDED BY SEARCH, NOT AUTHORED — gated on `wdist` (no household ever leans on a
#     lane), on the water, on the real landmarks' footprints, and on a per-seed separation
#     drawn from the seed's own hash.  Deterministic order, deterministic hash.
#  b  A PIECE THAT FAILS THE GATE IS DROPPED, NOT NUDGED.  The first draft pushed
#     offending roofs outward and walked four of them across Home Row, because "outward"
#     from one lane is "into" the next.
#  c  A CLOSED LANE MUST LEAD SOMEWHERE.  Implied-scale technique 2 says a lane visibly
#     continues and is closed at the threshold; the ruling adds that what it continues INTO
#     has to be visible.  The two closed lanes get their households FIRST, strung along the
#     stub's own bearing, before the grid can claim the ground.
INFILL_SEEDS = []
INFILL_ROOFS = []
INFILL_XY = []
INFILL_RECTS = []                       # every cottage built so far, as an oriented rect
INFILL_CLEAR = 4.6                      # a household's centre, this far off any walk surface


def infill_ok(x, y, clear, sep):
    if not (X0 + 6 < x < X1 - 6 and Y0 + 6 < y < Y1 - 6):
        return False
    if wdist(x, y) < clear or in_water(x, y, 1.5) or lm_blocked(x, y, 3.2):
        return False
    for (px, py, _w, psep) in INFILL_SEEDS:
        if math.hypot(x - px, y - py) < max(sep, psep):
            return False
    return True


def seed_sep(x, y):
    """6-12 m, varied — the ruling's own range, drawn from the position's own hash so the
    spacing is irregular the way a village's is and identical between runs."""
    # THE FLOOR IS 7.5, NOT THE RULING'S 6.5, and the reason is measured: a cottage's
    # roof oversails its walls by 16%, so two 5.9 m cottages 6.5 m apart have roofs that
    # share 0.4 m of volume — six pairs did, and a shared roof volume is the defect the
    # bakery was moved 1.5 m for in the founding round.  7.5-12.0 m is still the village
    # spacing the refinement asked for and it is the range that can actually be built.
    return 7.5 + 4.5 * h01(int(x * 8), int(y * 8), 149)


# (c) the closed lanes first — the stub runs away from the town centre for 1.2 + 6*1.7 m
for l in D["landmarks"]:
    if l.get("class") != "prop" or "closed" not in (l.get("name") or "").lower():
        continue
    x, y, _z = l["pos"]
    ox, oy = x - cx_town, y - cy_town
    dn = math.hypot(ox, oy) or 1.0
    ox, oy = ox / dn, oy / dn
    nput = 0
    for reach in (13.0, 17.5, 22.0, 26.5):
        for swing in (0.0, -0.34, 0.34, -0.66, 0.66):
            ca, sa = math.cos(swing), math.sin(swing)
            dx_, dy_ = ox * ca - oy * sa, ox * sa + oy * ca
            sx, sy = x + dx_ * reach, y + dy_ * reach
            if infill_ok(sx, sy, INFILL_CLEAR, seed_sep(sx, sy)):
                INFILL_SEEDS.append((sx, sy, "closed:" + l["id"], seed_sep(sx, sy)))
                nput += 1
                break
        if nput >= 3:
            break
    if not nput:
        print("    infill: no household foot at the end of %s's stub" % l["id"])

# (a) then the grid, in the map's own warmth gradient
ISTEP = 3.4
ia0, ia1 = int(math.floor((min(XS) - 16) / ISTEP)), int(math.ceil((max(XS) + 16) / ISTEP))
ja0, ja1 = int(math.floor((min(YS) - 6) / ISTEP)), int(math.ceil((max(YS) + 16) / ISTEP))
for jj in range(ja0, ja1 + 1):
    for ii in range(ia0, ia1 + 1):
        sx = ii * ISTEP + (h01(ii, jj, 5) - 0.5) * 2.6
        sy = jj * ISTEP + (h01(ii, jj, 9) - 0.5) * 2.6
        if sy <= WOOD_Y1 + 8.0:
            continue                    # THE WOODROAD STAYS EMPTY — the wood is the wood
        p = 1.0 if d_to(WARMPTS, sx, sy) < 16.0 else \
            max(0.38, 1.0 - (d_to(WARMPTS, sx, sy) - 16.0) / 46.0)
        p *= min(1.0, 0.32 + d_to(COLDPTS, sx, sy) / 24.0)
        if h01(ii, jj, 13) > p:
            continue
        if infill_ok(sx, sy, INFILL_CLEAR, seed_sep(sx, sy)):
            INFILL_SEEDS.append((sx, sy, "grid", seed_sep(sx, sy)))

# every lane point a track can plausibly join, sampled once
TRACKPTS = []
for _k, _d in LANEDRAW.items():
    TRACKPTS.extend([(q[0], q[1], q[2]) for q in resample(_d, 2.0)])

ninf = ninfroof = ntrack = nfade = 0
for (sx, sy, why, _sep) in INFILL_SEEDS:
    salt = h32(int(sx * 16), int(sy * 16), 77)

    def _rej(vx, vy, half):
        # A HOUSEHOLD'S OWN FURNITURE MUST CLEAR ITS NEIGHBOUR'S HOUSE.  The first pass
        # gated hedges, palings and fruit trees against the walk network, the water and
        # the REAL landmarks — and against nothing else — so with cottages 6-12 m apart
        # one household's paling fence came out inside the next one's parlour, and a fruit
        # tree grew through a vista cottage.  Everything a household builds now tests the
        # cottages already standing, the implied-scale clusters, and the mill's pound.
        if (wdist(vx, vy) < half + 1.6 or in_water(vx, vy, 1.0)
                or lm_blocked(vx, vy, half + 1.0)
                or any(math.hypot(vx - f[0], vy - f[1]) < half + 2.2 for f in LAMPFEET)
                or any(math.hypot(vx - r[0], vy - r[1]) < half + 3.2 for r in VISTAROOFS)):
            return True
        if MILLPOND and math.hypot(vx - MILLPOND[0], vy - MILLPOND[1]) < MILLPOND_R + 3.6:
            return True
        return any(in_rect(vx, vy, r, half + 0.35) for r in INFILL_RECTS)

    # ---- the cottage -------------------------------------------------------------
    bw = 4.0 + 1.9 * h01(salt, 0, 11)
    bd = bw * (0.74 + 0.26 * h01(salt, 0, 13))
    if _rej(sx, sy, max(bw, bd) / 2):
        continue
    gz = ground_z(sx, sy)
    bh = 2.7 + 1.3 * h01(salt, 0, 17)
    crz = h01(salt, 0, 19) * math.pi
    tag = "lm_infill_%02d" % ninf
    box(tag + "_body", sx, sy, gz + bh / 2, bw, bd, bh, M_PLASTER, "EMB_MASSING", crz)
    rh = 1.5 + 0.5 * h01(salt, 0, 23)
    gable(tag + "_roof", sx, sy, gz + bh, bw * 1.16, bd * 1.16, rh,
          M_THATCH if (h32(salt, 0, 29) % 3) else M_TILE, "EMB_MASSING", crz)
    box(tag + "_chim", sx + math.cos(crz) * bw * 0.3, sy + math.sin(crz) * bw * 0.3,
        gz + bh + 1.2, 0.55, 0.55, 1.9, M_STONE, "EMB_MASSING", crz)
    for wk in (-1, 1):
        box(tag + "_win%d" % ((wk + 1) // 2),
            sx + math.cos(crz) * wk * bw * 0.28 - math.sin(crz) * (bd / 2 + 0.02),
            sy + math.sin(crz) * wk * bw * 0.28 + math.cos(crz) * (bd / 2 + 0.02),
            gz + bh * 0.62, 0.7, 0.06, 0.8, M_WINDOW, "EMB_MASSING", crz)
    INFILL_ROOFS.append((sx, sy, gz + bh + rh))
    INFILL_XY.append((sx, sy))
    INFILL_RECTS.append((sx, sy, bw * 1.16 / 2, bd * 1.16 / 2, crz))
    ninfroof += 1

    # ---- which way the household faces: toward the nearest real lane ---------------
    near = min(TRACKPTS, key=lambda q: (q[0] - sx) ** 2 + (q[1] - sy) ** 2) \
        if TRACKPTS else None
    if near:
        gate_a = math.atan2(near[1] - sy, near[0] - sx)
        gate_d = math.hypot(near[0] - sx, near[1] - sy)
    else:
        gate_a, gate_d = h01(salt, 0, 31) * 6.283, 99.0

    # ---- the garden plot: a hedge or a paling fence, with a gap at the gate ---------
    plot = 4.6 + 2.4 * h01(salt, 0, 37)
    fence = (h32(salt, 0, 41) % 3) == 0
    nseg = 16
    nh = 0
    for k in range(nseg):
        a = 2 * math.pi * k / nseg + h01(salt, 0, 43) * 0.9
        da = abs(((a - gate_a + math.pi) % (2 * math.pi)) - math.pi)
        if da < 0.42:
            continue                                    # the way in
        hx, hy = sx + plot * math.cos(a), sy + plot * math.sin(a)
        if _rej(hx, hy, 0.9):
            continue
        if fence:
            box("%s_pale%02d" % (tag, k), hx, hy, ground_z(hx, hy) + 0.52,
                1.9, 0.10, 1.04, M_TIMBER, "EMB_MASSING", a + math.pi / 2)
        else:
            box("%s_hedge%02d" % (tag, k), hx, hy, ground_z(hx, hy) + 0.46,
                1.9, 0.80, 0.92, M_LEAF_G, "EMB_MASSING", a + math.pi / 2)
        nh += 1

    # ---- a fruit tree or two, standing IN the plot ---------------------------------
    for t_ in range(1 + (h32(salt, 0, 47) % 2)):
        ta = gate_a + math.pi + (h01(salt, t_, 53) - 0.5) * 2.2
        tr_ = plot * (0.52 + 0.30 * h01(salt, t_, 59))
        tx, ty = sx + tr_ * math.cos(ta), sy + tr_ * math.sin(ta)
        if _rej(tx, ty, 1.7) or math.hypot(tx - sx, ty - sy) < max(bw, bd) / 2 + 1.6:
            continue
        tz = ground_z(tx, ty)
        th = 3.4 + 1.2 * h01(salt, t_, 61)
        box("%s_fruit%d_trunk" % (tag, t_), tx, ty, tz + th * 0.30, 0.22, 0.22, th * 0.60,
            M_TIMBER, "EMB_MASSING")
        pyramid("%s_fruit%d_crown" % (tag, t_), tx, ty, tz + th * 0.52, 3.0, 3.0, 2.2,
                M_LEAF_A if (h32(salt, t_, 67) % 2) else M_LEAF_G, "EMB_MASSING",
                h01(salt, t_, 71) * 1.57)

    # ---- a shed OR a woodpile, against the boundary --------------------------------
    oa = gate_a + (2.0 if (h32(salt, 0, 73) % 2) else -2.0)
    ox_, oy_ = sx + (plot - 1.9) * math.cos(oa), sy + (plot - 1.9) * math.sin(oa)
    if not _rej(ox_, oy_, 1.8):
        oz = ground_z(ox_, oy_)
        if (h32(salt, 0, 79) % 2):
            box(tag + "_shed", ox_, oy_, oz + 0.95, 2.7, 2.0, 1.9, M_TIMBER,
                "EMB_MASSING", oa)
            gable(tag + "_shedroof", ox_, oy_, oz + 1.9, 3.0, 2.3, 0.8, M_THATCH,
                  "EMB_MASSING", oa)
        else:
            for w_ in range(3):
                box("%s_woodpile%d" % (tag, w_), ox_, oy_, oz + 0.28 + w_ * 0.45,
                    2.2 - w_ * 0.3, 0.9, 0.44, M_TIMBER, "EMB_MASSING", oa)

    # ---- AND A WAY TO REACH IT.  Non-walkable, but visible, and it goes somewhere. ---
    # It joins the nearest lane when there is one within reach; otherwise it runs out
    # into the implied village and NARROWS AWAY rather than stopping dead, which is the
    # only honest thing a blockout can say about a road it cannot show the end of.
    gx0 = sx + (plot + 0.4) * math.cos(gate_a)
    gy0 = sy + (plot + 0.4) * math.sin(gate_a)
    if gate_d <= plot + 20.0 and near:
        tx1, ty1, joined = near[0], near[1], True
    else:
        tx1 = gx0 + 11.0 * math.cos(gate_a)
        ty1 = gy0 + 11.0 * math.sin(gate_a)
        joined = False
    nsg = 6
    for k in range(nsg):
        t0, t1 = k / float(nsg), (k + 1) / float(nsg)
        p0 = (gx0 + (tx1 - gx0) * t0, gy0 + (ty1 - gy0) * t0)
        p1 = (gx0 + (tx1 - gx0) * t1, gy0 + (ty1 - gy0) * t1)
        if occupied(p1[0], p1[1]) and joined:
            break                                       # it has reached the lane
        if in_water(p1[0], p1[1], 0.4):
            break                                       # a cart track is not a ford
        # AND IT DOES NOT RUN THROUGH THE NEIGHBOUR'S GARDEN.  A track laid straight at
        # the nearest lane crossed whatever stood between — eleven of them went through
        # somebody else's hedge and seven through a cottage wall.  A track that cannot
        # reach the lane without trespassing simply stops at the boundary, which is what
        # a track that joins an implied one looks like anyway.
        if any(in_rect(p1[0], p1[1], r_, 1.1) for r_ in INFILL_RECTS) or \
                any(math.hypot(p1[0] - q_[0], p1[1] - q_[1]) < 5.4
                    for q_ in INFILL_XY[:-1]):
            break
        wdt_ = 1.25 * (1.0 if joined else max(0.15, 1.0 - t1))   # fading = narrowing
        ribbon("%s_track%d" % (tag, k),
               (p0[0], p0[1], ground_z(*p0) + 0.06),
               (p1[0], p1[1], ground_z(*p1) + 0.06), wdt_, 0.10, M_EARTH, "EMB_MASSING")
    ntrack += 1 if joined else 0
    nfade += 0 if joined else 1
    ninf += 1
print("  lm_infill_*            %d HOUSEHOLDS (%d roofs), each with a garden plot, a "
      "fruit tree, a shed or woodpile and a track: %d tracks join a real lane, %d fade "
      "into the implied village" % (ninf, ninfroof, ntrack, nfade))

# ============================== THE BLUFFS — the valley has an END, not an edge ==
# USER TERRAIN RULING 2026-08-01 (map, `sigil-gate` note): the Old Gate is the BOTTLENECK
# between the valley and two mountain cliff bluffs — masonry built wall-to-wall into
# living rock, no way around it, the water leaving through the same pinch, and the
# shadowed gorge beyond IS the road to Dellhollow.  Coarse gray massing only: the dressed
# cliffs follow whichever of the three committed concepts the user picks.
#
# EVERYTHING HERE IS DERIVED FROM THE SEALED PORTAL, so the notch is wherever the map
# says the gate is, and the funnel's axis is the direction the gate faces out of the
# valley.  Two masses converge on it, each stepping outward and UPWARD — a bluff reads as
# a bluff because it gets taller as it gets further from the gap, not because it is tall.
SEALED = [l for l in D["landmarks"]
          if l.get("class") == "portal" and l.get("state") == "sealed"]
BLUFFS = []
if SEALED:
    _g = SEALED[0]["pos"]
    _nx, _ny = _g[0] - cx_town, _g[1] - cy_town
    _nl = math.hypot(_nx, _ny) or 1.0
    _nx, _ny = _nx / _nl, _ny / _nl                     # out of the valley
    _px, _py = -_ny, _nx                                # across the pinch
    NOTCH = 9.0                                         # half the gap AT the gate
    nblu = 0
    for side in (-1, 1):
        for k in range(7):
            # the face steps out across the pinch and back along the valley: converging
            # THE FUNNEL OPENS NORTHWARD, and the first draft's did not.  Stepping the
            # masses straight out across the pinch laid the western chain along the top of
            # Home Row, where they rendered as blank grey slabs looming over the village
            # instead of as a valley closing behind it.  Both chains now move OUT and
            # FORWARD together, so what the town sees is two shoulders of rock converging
            # on the gate and the gorge beyond it — the ruling's own picture.
            off = NOTCH + k * 8.2
            back = 3.0 + k * 8.0
            bx = _g[0] + _px * off * side + _nx * back
            by = _g[1] + _py * off * side + _ny * back
            # THE RIVER KEEPS ITS SLOT.  A bluff dropped on the water would dam the valley
            # and hide the one vista the east horizon has; the mass stops at the bank and
            # the gap it leaves is REPORTED, because a bottleneck the river walks around
            # is not a bottleneck.
            if RCRS:
                _rd, _rw = river_at(bx, by)
                if _rd < _rw / 2 + 7.0:
                    continue
            if wdist(bx, by) < 7.0:
                continue                                # never over the court or a lane
            # A CRAG IS A PILE, NOT A TOWER.  One tall box with a spike on it renders as a
            # grey skyscraper (it did).  Three offset lumps of decreasing size under a
            # broad low cap read as rock at 80 m, which is the only distance this is ever
            # seen from, and cost nothing.
            bh = 6.0 + 2.6 * k + 3.5 * h01(k, side + 2, 211)
            bwd = 20.0 + 9.0 * h01(k, side + 3, 223)
            bdp = 17.0 + 8.0 * h01(k, side + 5, 227)
            brz = math.atan2(_py, _px) + (h01(k, side + 7, 229) - 0.5) * 0.7
            gz_ = ground_z(bx, by)
            tagb = "emb_bluff_%s%d" % ("WE"[(side + 1) // 2], k)
            for l_ in range(3):
                f_ = 1.0 - 0.24 * l_
                jx = (h01(k, side + l_, 239) - 0.5) * bwd * 0.20
                jy = (h01(k, side + l_, 241) - 0.5) * bdp * 0.20
                box("%s_mass%d" % (tagb, l_), bx + jx, by + jy,
                    gz_ - 1.5 + (bh * f_) / 2 + l_ * bh * 0.22,
                    bwd * f_, bdp * f_, bh * f_, M_STONE, "EMB_CONTEXT",
                    brz + (h01(k, side + l_, 243) - 0.5) * 0.6)
            pyramid("%s_cap" % tagb, bx, by, gz_ - 1.5 + bh * 0.96,
                    bwd * 0.66, bdp * 0.66, 3.0 + 3.0 * h01(k, side + 11, 233),
                    M_STONE, "EMB_CONTEXT", brz)
            BLUFFS.append((bx, by, bwd / 2, bdp / 2, brz))
            nblu += 1
    print("  emb_bluff_*            %d rock masses converging on the Old Gate: the notch "
          "is %.1f m of gap either side of (%.1f, %.1f), the valley closes behind them"
          % (nblu, NOTCH, _g[0], _g[1]))
    if RCRS:
        _rd, _rw = river_at(_g[0], _g[1])
        print("    the river leaves the valley %.1f m east of the gate (its own bank is "
              "%.1f m from the masonry) — the pinch is NOT sealed by the stamped course; "
              "an amended tail is proposed in the report" % (_rd, _rd - _rw / 2))


def in_bluff(x, y, m=0.0):
    for r in BLUFFS:
        if in_rect(x, y, r, m):
            return True
    return False


# ================================ THE FOREST — the village's container ==
# USER RULING 2026-08-01 (map `forest._doc`): *the forest is the village's CONTAINER, not
# a rim decoration.*  Thicken it hard — it presses in around and between the outer
# houses, runs along the main paths' outer sides, closes every horizon, and swallows the
# space beyond the infill hamlets.  Composition target: the village is clearings and
# lanes carved OUT of forest, not buildings placed ON a lawn.
#
# AND THE SAME RULING FIXES THE TREE ITSELF AS A PLACEHOLDER.  Quality is a dressing-stage
# bar with a taste probe in front of it; nothing here may spend effort on beautiful trees.
# What IS this pass's job is DENSITY and PLACEMENT, and those are measured:
#
#  1  GATEGRID, THE PAID RULE.  A crown clears every walk surface by its OWN radius plus
#     1.0 m.  The radius is drawn from the tree's own hash BEFORE the gate is tested, so a
#     big crown needs more room than a small one and no tree is ever trimmed to fit.
#     Asserted after the fact against the ribbons themselves, not against the raster.
#  2  THE WHISPERWOOD ARRIVAL IS THE DENSE CASE.  South of the arch the map has a road
#     and nothing else; the rim ellipse runs 47 m further out than that road, so with the
#     rim alone the game's opening scene is a lane across an open field.  There, p = 1:
#     the wood is continuous and the road is a gap in it.  It THINS at the gateway (the
#     map's own words: "the last stretch: the wood thins, the arch and the first lamplight
#     appear"), so the reveal has somewhere to happen.
#  3  INSIDE THE VILLAGE IT IS STANDS, NOT WOOD.  A forest at woodroad density between the
#     square and Home Row would delete the town.  Village-side probability rises with
#     clearance from the walk network AND with distance outside the town's own anchor box,
#     so the trees press in from the edges and thicken into the rim, and the middle stays
#     the middle.
#
# BATCHED, and that is an engineering decision with a number behind it: ~1 800 trees as
# three objects each is 5 400 objects in a GLB the runtime loads for the free-roam scene.
# Emitted as merged meshes per material per batch it is ~70, and geometry_audit gets one
# soft object per batch instead of five thousand stray checks.
def _box_geo(acc, cx, cy, cz, sx, sy, sz, rz=0.0):
    v, f = acc
    b = len(v)
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    c, s_ = math.cos(rz), math.sin(rz)
    for dz in (-hz, hz):
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            v.append((cx + dx * c - dy * s_, cy + dx * s_ + dy * c, cz + dz))
    for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        f.append(tuple(b + n for n in q))


def _pyr_geo(acc, cx, cy, cz, sx, sy, h, rz=0.0):
    v, f = acc
    b = len(v)
    hx, hy = sx / 2.0, sy / 2.0
    c, s_ = math.cos(rz), math.sin(rz)
    for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        v.append((cx + dx * c - dy * s_, cy + dx * s_ + dy * c, cz))
    v.append((cx, cy, cz + h))
    for q in ((0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)):
        f.append(tuple(b + n for n in q))


ANCHX0, ANCHX1 = min(XS), max(XS)
ANCHY0, ANCHY1 = min(YS), max(YS)


def out_of_town(x, y):
    """How far outside the town's own anchor box a point lies (0 inside)."""
    return math.hypot(max(0.0, max(ANCHX0 - x, x - ANCHX1)),
                      max(0.0, max(ANCHY0 - y, y - ANCHY1)))


def forest_p(x, y, wd):
    if y <= WOOD_Y1 + 12.0:
        # THE WHISPERWOOD, and its northern edge is NOT the arch.  Two numbers here were
        # wrong and the reveal probe caught both.  (1) The wood used to stop at the
        # gateway's own latitude, leaving the ground between the arch and the orchard
        # nearly bare — and the ray from the arrival clearing to the tithe barn, 96 m
        # away, went straight through that window: the whole village was visible from the
        # game's first frame.  The wood wraps PAST the arch and dies against the village's
        # own lanes and floors, which the `wd` gate below already protects.  (2) The
        # thinning disc for the reveal was 8 m of nothing and 14 m of ramp — a 44 m-wide
        # hole punched in the treeline exactly where the sight line leaves.  A village
        # arch is 3.4 m wide; 5 m of clearance shows it whole, and the wood closes to
        # either side of the road instead of retreating from the whole neighbourhood.
        dg = d_to(GATEPOS, x, y) if GATEPOS else 1e9
        if dg < 5.0:
            return 0.0
        return min(1.0, (dg - 5.0) / 9.0)
    # A HAMLET HAS A CLEARING AROUND IT, and this factor is the whole reason the second
    # composition ruling can coexist with the first.  Without it the forest grows in
    # exactly the band the infill occupies — trees taller than the roofs, 20 m from the
    # lane — and the roof-count probe fell to a median of ONE against a target of two,
    # while the wood looked fine.  The village side is therefore: lane, then hamlet, then
    # wood; the trees take everything BEYOND the hamlets, which is what "swallows the
    # space beyond the infill clusters" says.
    # THE FOREST FILLS BETWEEN THE GARDEN PLOTS — the refinement's own words.  A
    # household's plot is 4.6-7.0 m of radius, so the trees start just outside it and
    # thicken over the next few metres: what lies between two cottages is wood, not
    # another cottage.  (The first version held them 11 m off a HAMLET, which left the
    # gaps as lawn.)
    ds = d_to(INFILL_XY, x, y)
    if ds < 8.2:
        return 0.0
    p = max(0.0, min(1.0, (wd - 6.0) / 8.0)) * min(1.0, (ds - 8.2) / 3.5)
    return p * min(1.0, 0.30 + out_of_town(x, y) / 12.0)


FSTEP = 2.75
BATCH = 90
_bt, _ba, _bg = ([], []), ([], []), ([], [])
nbatch = nwood = 0
FEET = []


def flush_forest(force=False):
    global _bt, _ba, _bg, nbatch
    if not force and len(FEET) % BATCH:
        return
    if _bt[0]:
        mesh("veg_emb_wood_%02d_trunks" % nbatch, _bt[0], _bt[1], M_TIMBER, "EMB_CONTEXT")
    if _ba[0]:
        mesh("veg_emb_wood_%02d_crownA" % nbatch, _ba[0], _ba[1], M_LEAF_A, "EMB_CONTEXT")
    if _bg[0]:
        mesh("veg_emb_wood_%02d_crownG" % nbatch, _bg[0], _bg[1], M_LEAF_G, "EMB_CONTEXT")
    _bt, _ba, _bg = ([], []), ([], []), ([], [])
    nbatch += 1


fi0, fi1 = int(math.floor((X0 + 3) / FSTEP)), int(math.ceil((X1 - 3) / FSTEP))
fj0, fj1 = int(math.floor((Y0 + 3) / FSTEP)), int(math.ceil((Y1 - 3) / FSTEP))
nrej_gate = nrej_water = nrej_lm = nrej_rim = nrej_rock = 0
for fj in range(fj0, fj1 + 1):
    for fi in range(fi0, fi1 + 1):
        x = fi * FSTEP + (h01(fi, fj, 3) - 0.5) * 1.9
        y = fj * FSTEP + (h01(fi, fj, 7) - 0.5) * 1.9
        if not (X0 + 2 < x < X1 - 2 and Y0 + 2 < y < Y1 - 2):
            continue
        # the crown's radius is drawn FIRST: the gate is a fact about THIS tree
        crown = 2.0 + 1.1 * h01(fi, fj, 53)
        wd = wdist(x, y)
        p = forest_p(x, y, wd)
        if p <= 0.0 or h01(fi, fj, 71) > p:
            continue
        if wd < crown + 1.0:
            nrej_gate += 1
            continue
        if in_water(x, y, crown * 0.5):
            nrej_water += 1
            continue
        if lm_blocked(x, y, crown + 0.8) or \
                any(math.hypot(x - r[0], y - r[1]) < crown + 3.4 for r in INFILL_ROOFS) or \
                any(math.hypot(x - r[0], y - r[1]) < crown + 3.4 for r in VISTAROOFS) or \
                any(math.hypot(x - f[0], y - f[1]) < crown + 1.4 for f in LAMPFEET):
            nrej_lm += 1
            continue
        if any(math.hypot(x - f[0], y - f[1]) < 1.9 for f in RIMFEET):
            nrej_rim += 1
            continue
        if in_bluff(x, y, -1.5):
            nrej_rock += 1          # the wood CLIMBS the bluffs; it does not grow in them
            continue
        z = ground_z(x, y)
        ht = 6.0 + 4.2 * h01(fi, fj, 23)
        tr = 0.26 + 0.13 * h01(fi, fj, 31)
        # THE WHISPERWOOD'S CANOPY COMES DOWN TO THE GROUND, and this is a MEASUREMENT
        # rather than a mood.  The first build of the arrival gave every tree a bare
        # trunk to 62% of its height, and the reveal probe found a village roof visible
        # from the FAR END of the road — a sight line at 3.6 m of elevation slipping
        # between 0.3 m trunks under a canopy that starts at 4 m.  A wood you can see the
        # next parish through is not a container.  So in the wood sector the crowns start
        # at 30% and there are three of them: the ray has to go through foliage, which is
        # what "trees pressing close" has to MEAN if the opening is to work.  Village-side
        # stands keep the high canopy — the lanes still have to read.
        deep = y <= WOOD_Y1
        _box_geo(_bt, x, y, z + ht * 0.34, tr, tr, ht * 0.72)
        leafg = (h32(fi, fj, 47) % 5) < 2
        base = 0.18 if deep else 0.62
        for c_ in range(3 if deep else 2):
            rr = (crown + 0.35 * c_) * (1.0 - 0.19 * c_)
            _pyr_geo(_bg if leafg else _ba, x, y, z + ht * base + c_ * 1.7,
                     rr * 2, rr * 2, 2.6 + 1.2 * h01(fi, fj, 61 + c_ % 2),
                     h01(fi, fj, 71 + c_ % 2) * 1.57)
        # UNDERSTORY, and it is the difference between a wood and a colonnade.  The first
        # render of the opening frame showed the village arch and two cottage roofs down a
        # corridor of BARE TRUNKS: a canopy that starts at 3 m occludes nothing at a
        # walker's eye, and a walker's eye is the only height the arrival is ever seen
        # from.  So in the wood sector most trees carry a low clump at the foot, thrown
        # off the trunk so the mass sits BETWEEN the stems rather than around them.  Scrub
        # massing, not a plant — quality is the dressing pass's bar, density is this one's.
        if deep and (h32(fi, fj, 83) % 4):
            _ua = h01(fi, fj, 89) * 6.283
            _ur = 0.9 + 1.1 * h01(fi, fj, 97)
            _uw = 1.5 + 1.3 * h01(fi, fj, 101)
            _pyr_geo(_bg if (h32(fi, fj, 103) % 3) else _ba,
                     x + _ur * math.cos(_ua), y + _ur * math.sin(_ua), z - 0.20,
                     _uw * 2, _uw * 2, 1.7 + 1.2 * h01(fi, fj, 107),
                     h01(fi, fj, 109) * 1.57)
        FEET.append((x, y, crown))
        nwood += 1
        flush_forest()
flush_forest(True)
print("  veg_emb_wood_*         %d trees in %d batched meshes (%.1f m grid; refused: "
      "%d by the lane gate, %d in water, %d on massing, %d on a rim tree)"
      % (nwood, nbatch, FSTEP, nrej_gate, nrej_water, nrej_lm, nrej_rim))

# GATEGRID, ASSERTED AGAINST THE RIBBONS THEMSELVES rather than against the raster the
# placement used.  A crown that overhangs a lane is the one defect this pass can cause
# that a screenshot will not show and a player will walk into.
worst_gap, worst_at = 1e9, None
for (fx, fy, crown) in FEET:
    for (a, b, wdt, _k) in RIBSEGS:
        gap = math.sqrt(seg_dist2(fx, fy, a[0], a[1], b[0], b[1])) - wdt / 2 - crown
        if gap < worst_gap:
            worst_gap, worst_at = gap, (fx, fy)
if FEET:
    print("  forest lane clearance  tightest crown clears its lane's edge by %.2f m at "
          "(%.1f, %.1f) — the rule is 1.00 m" % (worst_gap, *worst_at))
    assert worst_gap >= 1.0, ("a forest crown overhangs a lane at (%.1f, %.1f): %.2f m"
                              % (worst_at[0], worst_at[1], worst_gap))

build_ground()          # LAST, so the road cut sees the whole walkable town


# ====================================================================== water ==
# All three bodies are `water_` — never walkable, always cut against the walk footprint.
WCELL = 0.55


# RULE 4, EXTENDED: NO WATER UNDER A BUILDING EITHER.  The pond's extent doubled to 12 m
# in the round-2 redline and its disc now reaches over ground that the map has since put
# Finn's smokehouse, the weir and the brook mouth on; the founding rule cut water against
# WALK surfaces only, so the jetty stayed dry and the smokehouse rendered standing in the
# pond.  A solid gets its own dry footprint for the same reason a road does.  WHICH
# landmarks needed it is PRINTED — a building that only stays out of the water because
# the builder cut a hole for it is a map question, not a fix.
WET_MASSING = []


def dry_footprint(x, y):
    for o in D["landmarks"]:
        if o.get("class") in ("area", "dressing") or bodysize(o)[0] <= 0:
            continue
        if math.hypot(o["pos"][0] - x, o["pos"][1] - y) > 9.0:
            continue
        if in_rect(x, y, foot_rect(o), 0.35):
            if o["id"] not in WET_MASSING:
                WET_MASSING.append(o["id"])
            return True
    for (rx_, ry_, _rz) in INFILL_ROOFS:
        if math.hypot(rx_ - x, ry_ - y) < 3.6:
            return True
    return False


def water_field(name, inside_fn, level_fn, x0, x1, y0, y1, cut=True):
    v, f, n = [], [], 0
    for a in range(int(math.floor(x0 / WCELL)), int(math.ceil(x1 / WCELL))):
        for b in range(int(math.floor(y0 / WCELL)), int(math.ceil(y1 / WCELL))):
            cx, cy = (a + 0.5) * WCELL, (b + 0.5) * WCELL
            if not inside_fn(cx, cy) or (cut and occupied(cx, cy)):
                continue
            if cut and dry_footprint(cx, cy):
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

if MILLPOND:
    # THE MILLPOND is the head the overshot wheel runs on: the brook widened and held
    # back where the leat is drawn off.  It is small on purpose — this is a village
    # corn mill on a brook, not a reservoir — and it is cut against the walk footprint
    # like the pond, so the mill lane keeps its bank.
    _mx, _my, _mz = MILLPOND
    _mr = MILLPOND_R
    _n = water_field("water_emb_millpond",
                     lambda x, y: math.hypot(x - _mx, y - _my) <= _mr,
                     lambda x, y: _mz - 0.10, _mx - _mr - 1, _mx + _mr + 1,
                     _my - _mr - 1, _my + _mr + 1)
    print("    water_emb_millpond    %3d cells, r %.1f at z %.2f (the head the wheel "
          "runs on; the basin under it is carved and the dam is massing)"
          % (_n, _mr, _mz - 0.10))
    nw += _n

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
# A JETTY IS SUPPOSED TO OVERHANG THE WATER — that is what a jetty IS — so the rule for a
# dock is not "keep it dry", it is "keep its ROOT on the bank".  The coordinator ruled this
# explicitly when the pond came back to r9: assert the landward end, do not relocate the
# deck.  Measured on the pad's own vertices: the two corners nearest the shore must be
# outside every water extent, and how far the far end reaches over the water is PRINTED,
# because "the jetty is 3 m out over the pond" is a fact the lighting pass will want.
for _d in [l for l in D["landmarks"] if (l.get("kind") or "") == "dock"]:
    _ob = bpy.data.objects.get("walk_pad_" + _d["id"])
    if not _ob:
        continue
    _cs = [(v.co.x, v.co.y) for v in _ob.data.vertices[:4]]
    _wd = []
    for wid in WATER_LM:
        _wx, _wy, _ = LM[wid]["pos"]
        _wr = LM[wid].get("extent", 5)
        _wd.append([_wr - math.hypot(c[0] - _wx, c[1] - _wy) for c in _cs])
    _over = max(max(r) for r in _wd) if _wd else -9.9
    _dry = min(min(r) for r in _wd) if _wd else 9.9
    print("  %-22s deck reaches %.2f m out over the water; its landward corner stands "
          "%.2f m inland of the shore" % (_d["id"], _over, -_dry))
    assert _dry < 0.0, ("%s's whole walk pad is inside a water extent — a jetty may "
                        "overhang the water but it must be rooted on the bank" % _d["id"])

if WET_MASSING:
    print("    NOTE  %s stand INSIDE an authored water extent — the water is cut around "
          "them so nothing renders in the pond, but a building that needs a hole cut in "
          "a pond to stand dry is a MAP question (the extent, or the position)"
          % ", ".join(sorted(WET_MASSING)))

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
            # A HOME LANE GETS A SMALL BRIDGE, NOT A CULVERT, and that is the map's own
            # word: `brook._doc` says each home-lane crossing is "a small bridge".  A
            # culvert is a road detail — you do not know you crossed anything — and the
            # brook course was proposed on the promise that Home Row crosses its water in
            # plain sight, once, on planks.  Everything else (the north lane, the shore
            # path) still gets stone, because that IS what those are.
            home = any(LM.get(n, {}).get("district") == "homerow"
                       for n in ekey.split("__"))
            brg = brook_bearing(x, y)
            if home:
                ux_, uy_ = math.cos(brg), math.sin(brg)
                box("walk_pad_footbridge_%02d" % ncul, x, y, z, wdt + 1.4, 2.2, 0.16,
                    M_TIMBER, "EMB_PATHS", math.atan2(b[1] - a[1], b[0] - a[0]))
                for si, sgn in enumerate((-1, 1)):
                    box("bar_footbridge_%02d_rail%d" % (ncul, si),
                        x + ux_ * sgn * 1.05, y + uy_ * sgn * 1.05, z + 0.52,
                        wdt + 1.4, 0.09, 0.10, M_TIMBER, "EMB_MASSING",
                        math.atan2(b[1] - a[1], b[0] - a[0]))
                    box("emb_footbridge_%02d_abut%d" % (ncul, si),
                        x + ux_ * sgn * 1.45, y + uy_ * sgn * 1.45,
                        (z - 0.30 + bz - 0.5) / 2, wdt + 1.4, 0.7,
                        max(0.4, (z - 0.30) - (bz - 0.5)), M_STONE, "EMB_CONTEXT",
                        math.atan2(b[1] - a[1], b[0] - a[0]))
                print("    FOOTBRIDGE %d at (%.1f, %.1f) on %-30s HOME LANE — planks and "
                      "rails, road z %.2f over brook z %.2f" % (ncul, x, y, ekey, z, bz))
            else:
                box("emb_culvert_%02d_deck" % ncul, x, y, z - 0.21, wdt + 0.9, 2.6, 0.30,
                    M_STONE, "EMB_CONTEXT")
                for si, sgn in enumerate((-1, 1)):
                    hgt = max(0.4, (z - 0.36) - (bz - 0.6))
                    box("emb_culvert_%02d_abut%d" % (ncul, si), x, y + sgn * 1.15,
                        (z - 0.36 + bz - 0.6) / 2, wdt + 0.9, 0.5, hgt, M_STONE,
                        "EMB_CONTEXT")
                print("    CULVERT %d at (%.1f, %.1f) on %-32s road z %.2f over brook "
                      "z %.2f" % (ncul, x, y, ekey, z, bz))
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

# ================================ THE BROOK'S BILL, IN THE CONSTRAINTS' OWN TERMS ==
# `brook._doc` states the course's constraints as countable facts — each home lane
# crosses AT MOST ONCE, the r14 plaza loses NO cells, the crossing of Pond Lane is AT the
# footbridge — and a course proposal that cannot be checked against them is an opinion.
# This is the instrument.  It counts crossings against the RIBBONS AS DRAWN (chaikin,
# rim-trimmed, reclaimed), not against the map's straight lines between landmarks, because
# the drawn lane is the one a bridge has to stand on.
def _seg_cross(p, q, r, s):
    def _cr(ox, oy, ax_, ay_, bx_, by_):
        return (ax_ - ox) * (by_ - oy) - (bx_ - ox) * (ay_ - oy)
    d1 = _cr(r[0], r[1], s[0], s[1], p[0], p[1])
    d2 = _cr(r[0], r[1], s[0], s[1], q[0], q[1])
    d3 = _cr(p[0], p[1], q[0], q[1], r[0], r[1])
    d4 = _cr(p[0], p[1], q[0], q[1], s[0], s[1])
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


if BPOLY:
    HOMED = {l["id"] for l in D["landmarks"] if l.get("district") == "homerow"}
    XINGS = {}
    for _key, _draw in LANEDRAW.items():
        pts = []
        for a, b in zip(_draw, _draw[1:]):
            for c, dd in zip(BPOLY, BPOLY[1:]):
                if _seg_cross(a, b, c, dd):
                    if all(math.hypot(a[0] - px, a[1] - py) > 2.5 for (px, py) in pts):
                        pts.append((a[0], a[1]))
        if pts:
            XINGS[_key] = pts
    print("  brook x lanes          %d lanes cross the brook" % len(XINGS))
    _bad = []
    for _key in sorted(XINGS):
        pts = XINGS[_key]
        a_id, b_id = _key.split("__")
        home = a_id in HOMED or b_id in HOMED
        bridged = sum(1 for (px, py) in pts
                      if any(math.hypot(px - bx_, py - by_) < 3.5
                             for (bx_, by_, _bz) in BRIDGES))
        print("      %-38s %d crossing(s)%s, %d at a bridge  %s"
              % (_key, len(pts), " [HOME LANE]" if home else "", bridged,
                 " ".join("(%.1f, %.1f)" % p for p in pts)))
        if home and len(pts) > 1:
            _bad.append(_key)
    if _bad:
        print("    BROOK CONSTRAINT UNMET — a home lane may cross the brook AT MOST ONCE "
              "(`brook._doc`): %s" % ", ".join(_bad))
    _pl = [(k, v) for k, v in AREACUT.items() if v]
    if _pl:
        for (k, v) in sorted(_pl):
            print("    BROOK CONSTRAINT — the brook cut %d cells out of walk_lm_%s "
                  "(`brook._doc`: it must cut NONE from the r%s plaza)"
                  % (v, k, AREA_R.get(k, "?")))
    # WHERE THE FALL IS, which is the mill's whole site requirement: an overshot wheel
    # wants head, and the map hands the builder the mill's position on condition that it
    # snaps to a reach that has some.
    _best, _bat = 0.0, None
    for _k in range(0, max(1, len(BPOLY) - 30), 5):
        _a, _b = BPOLY[_k], BPOLY[_k + 30]
        _run = sum(math.hypot(q[0] - p[0], q[1] - p[1])
                   for p, q in zip(BPOLY[_k:_k + 30], BPOLY[_k + 1:_k + 31]))
        if _run > 1e-6 and (_a[2] - _b[2]) / _run > _best:
            _best, _bat = (_a[2] - _b[2]) / _run, (_a, _b, _run)
    if _bat:
        print("  brook steepest reach   %.3f m/m — %.2f m of fall over %.1f m, from "
              "(%.1f, %.1f) to (%.1f, %.1f)"
              % (_best, _bat[0][2] - _bat[1][2], _bat[2], _bat[0][0], _bat[0][1],
                 _bat[1][0], _bat[1][1]))



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

# TWO LANDMARKS STANDING IN EACH OTHER, reported by measurement.  Ten lived-in landmarks
# arrived in one map commit into a town that was already placed, and the blockout is the
# first thing that knows how big any of them is (`bodysize` is here, not in the map).  A
# roof volume shared between two buildings is a map line, never a builder fudge — the
# bakery was moved 1.5 m for exactly this in the founding round — so it is NAMED here.
_ov = []
_lms = [o for o in D["landmarks"] if o.get("class") not in ("area", "dressing")
        and bodysize(o)[0] > 0]
for _a in range(len(_lms)):
    for _b in range(_a + 1, len(_lms)):
        A, B = _lms[_a], _lms[_b]
        if math.hypot(A["pos"][0] - B["pos"][0], A["pos"][1] - B["pos"][1]) > 12.0:
            continue
        # SEPARATING AXIS, so the answer is a DEPTH and not a yes.  The first version of
        # this instrument answered yes/no and reported five "conflicts", of which two were
        # two buildings standing in one place and three were oriented corners grazing by
        # centimetres — one line of output for a defect and for a bench that stands close
        # to a cottage, which is a report that makes its reader do the measuring.
        ra, rb = foot_rect(A), foot_rect(B)
        pen = 1e9
        for (_cx, _cy, _hw, _hd, _rz) in (ra, rb):
            for (axx, axy) in ((math.cos(_rz), math.sin(_rz)),
                               (-math.sin(_rz), math.cos(_rz))):
                ext = []
                for (px_, py_, phw, phd, prz) in (ra, rb):
                    e = abs(math.cos(prz) * axx + math.sin(prz) * axy) * phw + \
                        abs(-math.sin(prz) * axx + math.cos(prz) * axy) * phd
                    ext.append((px_ * axx + py_ * axy, e))
                sep = abs(ext[0][0] - ext[1][0]) - (ext[0][1] + ext[1][1])
                pen = min(pen, -sep)
        if pen > 0.0:
            _ov.append((A["id"], B["id"], pen,
                        math.hypot(A["pos"][0] - B["pos"][0], A["pos"][1] - B["pos"][1])))
_hard = [o for o in _ov if o[2] >= 0.35]
if _hard:
    print("  MAP CONFLICT — %d pair(s) of landmark footprints genuinely overlap "
          "(a map move, never a builder fudge):" % len(_hard))
    for (a_, b_, p_, d_) in sorted(_hard, key=lambda o: -o[2]):
        print("      %-20s x %-20s overlap %.2f m  (centres %.2f m apart)"
              % (a_, b_, p_, d_))
else:
    print("  no two landmark footprints genuinely overlap")
for (a_, b_, p_, d_) in sorted([o for o in _ov if o[2] < 0.35], key=lambda o: -o[2]):
    print("      grazing  %-18s x %-18s corners overlap %.2f m — noted, not a defect"
          % (a_, b_, p_))

# a parcel member that no longer names a real landmark: a rename that missed a reference
for p in D.get("parcels", []):
    for mid in p.get("members", []):
        if mid not in LM:
            print("  MAP WARN  parcel %s names member '%s', which is not a landmark"
                  % (p["id"], mid))

# =============================================== TWO PROBES, BECAUSE TWO RULINGS ==
# Both round-2 composition rulings are stated as things the PLAYER sees, and neither can be
# settled off a screenshot of a gray town: "the village is invisible until the arch", and
# "from any playable lane, 2+ non-playable roofs visible in most directions".  So both are
# RAY-CAST, out of the same depsgraph the bake uses, and the numbers go in the report.
# Nothing here builds anything — a probe that changed the scene would change the digest and
# stop being a probe.
from mathutils import Vector as Vec                      # noqa: E402  (probe-only)

bpy.context.view_layer.update()
_dg = bpy.context.evaluated_depsgraph_get()
_sc = bpy.context.scene
EYE = 1.62


def _sees(px, py, pz, tx, ty, tz, margin=0.45):
    d = Vec((tx - px, ty - py, tz - pz))
    L = d.length
    if L < 1e-6:
        return True
    return not _sc.ray_cast(_dg, Vec((px, py, pz)), d.normalized(), distance=L - margin)[0]


def _surface_pts(o):
    """THREE AIM POINTS ON A SOLID, AND NONE OF THEM ON ITS RIDGE.  The arrival probe's
    first version aimed at the bbox centre 0.35 m under the top — which, on a GABLE, is
    inside the roof's own wedge: the ray entered its own target's skin ~0.6 m out, the
    stop margin was 0.45, and every roof in the town reported itself occluded.  The probe
    said the village was invisible from the wood road while the render of that exact frame
    showed three roofs.  A visibility oracle that fails closed is the most dangerous kind
    of instrument there is, because a pass looks like a pass.  Aim at the eaves corners
    and the shoulder instead, and stop the ray well short."""
    pts = [o.matrix_world @ Vec(c) for c in o.bound_box]
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
    y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
    z1 = max(p.z for p in pts)
    z0 = min(p.z for p in pts)
    zs = z0 + (z1 - z0) * 0.62
    return [((x0 + x1) / 2, (y0 + y1) / 2, zs),
            (x0 + (x1 - x0) * 0.18, y0 + (y1 - y0) * 0.18, zs),
            (x0 + (x1 - x0) * 0.82, y0 + (y1 - y0) * 0.82, zs)]


# BOTH PROBES AIM AT GEOMETRY THAT EXISTS, and the first draft of them did not — it aimed
# at `landmark.pos.z + 5.4`, a height picked to clear a roof.  For the Heartlight, whose
# whole massing is 3 m tall, that put the target in EMPTY AIR ABOVE THE FLAME, the ray
# reached it unobstructed, and the arrival probe reported the village visible from the far
# end of the wood road when what was visible was nothing at all.  A visibility oracle that
# can see through the thing it is asking about is worse than no oracle: it is a number
# that reads like evidence.  So targets are read off BUILT OBJECTS' world bounds.
def _targets(pred, drop=0.35):
    """[(x, y, z_top - drop, key)] for every built object the predicate accepts."""
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not pred(o.name):
            continue
        pts = [o.matrix_world @ Vec(c) for c in o.bound_box]
        out.append((sum(p.x for p in pts) / 8.0, sum(p.y for p in pts) / 8.0,
                    max(p.z for p in pts) - drop, o.name))
    return out


# ---- PROBE 1: WHEN DOES EMBERBROOK APPEAR? ----------------------------------------
# Sampled along the arrival road at a walker's eye height, asking three questions per step:
# can I see the arch, a village roof, the Heartlight.  A roof visible from the clearing end
# is a FOREST failure with a number on it, not a taste question.
if WSPINE and GATEPOS:
    _road = []
    for poly in WSPINE:
        _road.extend(resample(poly, 2.0))
    _road.sort(key=lambda p: -d_to(GATEPOS, p[0], p[1]))
    # EVERY built village solid, INCLUDING the infill households — the first version of
    # this filter kept only y > WOOD_Y1 + 4 and so excused exactly the roofs nearest the
    # arch, which are the ones the ruling is about.
    _vill = [(o.name, _surface_pts(o)) for o in bpy.data.objects
             if o.type == 'MESH' and o.name.startswith("lm_")
             and o.name.endswith(("_roof", "_body", "_shedroof"))
             and not any(o.name.startswith("lm_%s_" % g) for g in GATEWAY)
             and (o.matrix_world @ Vec(o.bound_box[0])).y > WOOD_Y1 - 2.0]
    _hl = [p for o in bpy.data.objects if o.name.startswith("lm_heartlight_flame")
           for p in _surface_pts(o)]
    _arch = [p for o in bpy.data.objects
             if any(o.name == "lm_%s_lintel" % g for g in GATEWAY)
             for p in _surface_pts(o)]
    _fhl = _froof = _farch = None
    _who = None
    _vcount = []
    for p in _road:
        dg_, ez = d_to(GATEPOS, p[0], p[1]), p[2] + EYE
        if _farch is None and any(_sees(p[0], p[1], ez, *a, margin=0.9) for a in _arch):
            _farch = dg_
        # HOW MANY of the village's solids have a sight line, not merely whether ONE
        # does.  "A ray exists" and "the village is revealed" are different claims and the
        # first is a far weaker one: through 1 700 scattered trees there is nearly always
        # some needle between two trunks.  The count is what tells the reviewer whether
        # the opening frame shows a town or shows a gap.
        nvis = 0
        for (vn, vps) in _vill:
            if any(_sees(p[0], p[1], ez, *t, margin=0.9) for t in vps):
                nvis += 1
                if _froof is None:
                    _froof, _who = dg_, vn
        _vcount.append((dg_, nvis))
        if _fhl is None and any(_sees(p[0], p[1], ez, *h, margin=0.9) for h in _hl):
            _fhl = dg_
    print("  THE ARRIVAL, MEASURED   %d samples over %.1f m of wood road, eye at %.2f m, "
          "against %d built village solids:"
          % (len(_road), max(d_to(GATEPOS, p[0], p[1]) for p in _road), EYE, len(_vill)))
    for _lbl, _v, _x in (("the arch itself", _farch, ""),
                         ("the first village solid", _froof, " (%s)" % _who),
                         ("the Heartlight's flame", _fhl, "")):
        print("      %-24s first shows %s%s"
              % (_lbl, ("%5.1f m from the arch" % _v) if _v is not None
                 else "NEVER on this road", _x if _v is not None else ""))
    if _vcount:
        print("      village solids with a sight line, by distance from the arch:")
        print("        " + "  ".join("%.0fm:%d" % (d_, n_) for (d_, n_) in _vcount[::2]))
        print("      (of %d built village solids. One needle through 1 700 trees is not a "
              "reveal; the shape of this row is the answer.)" % len(_vill))

# ---- PROBE 2: BACKGROUND ROOFS FROM THE PLAYABLE LANES ----------------------------
# The densification ruling's own working target, counted rather than eyeballed: standing on
# a lane, how many roofs you can never walk to are in sight, and in how many of eight
# compass sectors.  Vista clusters count (same technique); the infill is what this round
# added and is reported separately.  The wood road is excluded on purpose — it HAS no
# village, and averaging it in would hide the answer for the lanes that do.
# A ROOF IS VISIBLE IF ANY OF IT IS, and the first draft tested one point — the apex —
# which counted a roof hidden when its own ridge end was in plain sight.  Three points per
# roof, and the RANGE matters too: "look around and see other people's roofs" is a
# statement about the roofs near you, so 35 m is the measure and the 60 m figure is
# reported beside it rather than instead of it.
_bgo = [o for o in bpy.data.objects
        if o.type == 'MESH' and o.name.endswith("_roof")
        and (o.name.startswith("lm_infill_")
             or any(o.name.startswith("lm_%s_" % v["id"]) for v in D["landmarks"]
                    if v.get("class") == "dressing"))]
_bgi = []
for o in _bgo:
    pts = [o.matrix_world @ Vec(c) for c in o.bound_box]
    cx_, cy_ = sum(p.x for p in pts) / 8.0, sum(p.y for p in pts) / 8.0
    zt = max(p.z for p in pts)
    _bgi.append([(cx_, cy_, zt - 0.30),
                 ((cx_ + max(p.x for p in pts)) / 2, (cy_ + max(p.y for p in pts)) / 2,
                  zt - 0.55),
                 ((cx_ + min(p.x for p in pts)) / 2, (cy_ + min(p.y for p in pts)) / 2,
                  zt - 0.55)])
if _bgi and LANEDRAW:
    _samples = []
    for _key, _draw in LANEDRAW.items():
        a_, b_ = _key.split("__")
        if a_ in WOOD_IDS and b_ in WOOD_IDS:
            continue
        for p in resample(_draw, 5.0):
            _samples.append((_key, p))
    _near, _far, _sectors, _worst = [], [], [], (99, ("-", 0.0, 0.0))
    for (_key, p) in _samples:
        ez = p[2] + EYE
        n35 = n60 = 0
        secs = set()
        for tri in _bgi:
            d_ = math.hypot(tri[0][0] - p[0], tri[0][1] - p[1])
            if d_ > 60.0:
                continue
            if not any(_sees(p[0], p[1], ez, t[0], t[1], t[2]) for t in tri):
                continue
            n60 += 1
            if d_ <= 35.0:
                n35 += 1
                secs.add(int((math.atan2(tri[0][1] - p[1], tri[0][0] - p[0]) + math.pi)
                             / (math.pi / 4)))
        _near.append(n35)
        _far.append(n60)
        _sectors.append(len(secs))
        if n35 < _worst[0]:
            _worst = (n35, (_key, p[0], p[1]))
    _cs, _fs, _ss = sorted(_near), sorted(_far), sorted(_sectors)
    _ok = sum(1 for c in _near if c >= 2) / float(len(_near))
    print("  BACKGROUND ROOFS        %d lane samples against %d unreachable roofs "
          "(%d infill + %d vista):" % (len(_samples), len(_bgi), len(INFILL_ROOFS),
                                       len(VISTAROOFS)))
    print("      within 35 m, in sight     median %d, worst %d, best %d"
          % (_cs[len(_cs) // 2], _cs[0], _cs[-1]))
    print("      within 60 m, in sight     median %d, best %d" % (_fs[len(_fs) // 2], _fs[-1]))
    print("      compass sectors with one  median %d of 8, worst %d"
          % (_ss[len(_ss) // 2], _ss[0]))
    print("      meeting the ruling's 2+ target: %.0f%% of lane samples "
          "(emptiest: %s at (%.1f, %.1f), %d roofs)"
          % (100 * _ok, _worst[1][0], _worst[1][1], _worst[1][2], _worst[0]))

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
