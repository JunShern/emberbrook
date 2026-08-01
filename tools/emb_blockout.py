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


# AN ORIENTED RECTANGLE TEST, HOISTED HERE because it is the shared vocabulary of
# every footprint in this file — landmark massing, area-floor holes, infill plots and
# (since the seal) the gate's curtain walls and the range's own rock, which are derived
# before the treeline that has to refuse to grow in them.
def in_rect(px, py, rect, pad=0.0):
    cx, cy, hw, hd, rz = rect
    c, s_ = math.cos(-rz), math.sin(-rz)
    dx, dy = px - cx, py - cy
    return abs(dx * c - dy * s_) <= hw + pad and abs(dx * s_ + dy * c) <= hd + pad


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


# ================= THE SEAL — masonry, water, rock, and nothing walkable between ==
# USER TERRAIN RULING 2026-08-01 (map `sigil-gate`) AND THE STAMPED RIVER TAIL (map
# `river._doc`): the river carved the ONLY breach in the range, the Order gated it, and
# the tail now brings the channel hard against the gate's east side so GATE + WATER fill
# the notch together.  Round 2 built the bluffs and measured its own failure honestly —
# 9.5 m of dry ground between the masonry and the water, 32 m of open ground around the
# bottleneck.  This section is that measurement's answer, and every number in it is
# DERIVED, so a re-stamped tail re-cuts the seal instead of invalidating it:
#
#  *  THE PINCH LINE is the line through the gate SQUARE TO THE WAY THE GATE FACES OUT
#     OF THE VALLEY (the reverse of the lane that arrives at it).  Round 2 used the
#     town-CENTRE bearing instead — 23 degrees off the gate's own facing — which is why
#     its eastern chain stepped south-east back INTO the valley, why its refusals left a
#     hole beside the water, and why the two chains carried each other's names.
#  *  ACROSS THAT LINE, IN ORDER: living rock, the gate's west curtain wall, the gate,
#     its east curtain wall, the water, living rock.  Nothing else stands there and
#     nothing walkable survives between them.  Both facts are MEASURED at the end of the
#     run (THE SEAL, MEASURED) rather than asserted in this comment.
#  *  THE WALLS' LENGTHS ARE MEASURED, NOT AUTHORED.  Each runs from its own jamb until
#     it meets what it has to die into — living rock westward, the channel eastward.
#  *  THE WATER GOES UNDER THE GATE, NOT BESIDE IT (map `sigil-gate`, user refinement 2
#     with docs/qa/emberbrook/concepts/gate-final.png as the ratified reference): ONE
#     WIDE STRUCTURE spans the whole notch — twin arched doors over the road, and where
#     the channel crosses the same line the masonry continues as PLAIN COURSED WALL
#     carried on a LOW GRATE at the waterline.  "Arches are for humans."  So the seal
#     has no water gap in it at all: rock, wall, doors, wall, grate-under-wall, rock.
#  *  THE ROCK IS PINNED TO BOTH.  The west chain's inner face stands where the west
#     wall ends — searched outward until the rock stops eating a walkable area floor,
#     because a bluff standing on the gate court is round 2's Home Row defect again.
#     The east chain's inner face stands a toe INSIDE the water's far edge.
#  *  A MASS IS SQUARE TO THE PINCH AND ITS BIGGEST LUMP CARRIES NO JITTER, so the
#     rectangle the seal is measured and cut against is a face of the geometry itself
#     rather than an approximation of it.  The pile still reads as a pile: the two
#     smaller lumps and the cap keep their own offsets and yaw.
GATE_JAMBW, GATE_DEEP = 0.9, 1.1
GATE_HALF = 2.45                        # the sealed gate's masonry half-span (the lintel)
SEALED = [l for l in D["landmarks"]
          if l.get("class") == "portal" and l.get("state") == "sealed"]
BLUFFS = []                             # the rock, as `in_rect` rectangles
SEALMAS = []                            # the curtain walls, likewise
SEALCUT = []                            # both — what an area floor has to cut around
CHAIN = []
GATEFRAME = None
if SEALED:
    _gl = SEALED[0]
    GX, GY, GZ = _gl["pos"]
    _nbs = []
    for e in EDGES:
        if e["from"] == _gl["id"]:
            _nbs.append((e.get("waypoints") or [POS[e["to"]]])[0])
        elif e["to"] == _gl["id"]:
            _nbs.append((e.get("waypoints") or [POS[e["from"]]])[-1])
    _bx = sum(p[0] for p in _nbs) / len(_nbs) if _nbs else GX
    _by = sum(p[1] for p in _nbs) / len(_nbs) if _nbs else GY - 1.0
    _ol = math.hypot(GX - _bx, GY - _by) or 1.0
    OUTX, OUTY = (GX - _bx) / _ol, (GY - _by) / _ol     # out of the valley
    ACRX, ACRY = -OUTY, OUTX                            # across the pinch
    SEALRZ = math.atan2(ACRY, ACRX)
    GATEFRAME = (GX, GY, GZ)

    def _pt(a, b):
        """(across, out) in the pinch's own frame -> world."""
        return (GX + ACRX * a + OUTX * b, GY + ACRY * a + OUTY * b)

    def _wet(a, b):
        if not RCRS:
            return False
        _x, _y = _pt(a, b)
        _d, _w = river_at(_x, _y)
        return _d < _w / 2

    def _onmesh(a, b):
        _x, _y = _pt(a, b)
        return X0 + 1.0 < _x < X1 - 1.0 and Y0 + 1.0 < _y < Y1 - 1.0

    def _rect(a0, a1, b0, b1):
        _cx, _cy = _pt((a0 + a1) / 2, (b0 + b1) / 2)
        return (_cx, _cy, (a1 - a0) / 2, (b1 - b0) / 2, SEALRZ)

    # THE WALL IS 3.2 m THROUGH AND STANDS 0.4 m PROUD OF THE PINCH LINE, and neither
    # number is taste.  The gate court is an r10 disc centred 8 m inside the gate, so its
    # floor LAPS 1.8 m past the gate on both flanks — walk cells 1.3 m north of the line
    # the bottleneck is supposed to be.  A wall thinner than the lap leaves them standing.
    WALLD, WALLB, WALLTOE = 3.2, 0.4, 1.0
    WB0, WB1 = WALLB - WALLD / 2, WALLB + WALLD / 2

    # ---- WHICH FLANK THE CHANNEL IS ON IS DERIVED, NOT NAMED.  `across` is whichever
    #      perpendicular fell out of the gate's own facing — here it points WEST, so a
    #      block that hard-codes "east" searches the wrong half of the valley and finds
    #      no river at all (it did).  Ask the water instead: the flank that meets the
    #      channel is the CHANNEL flank and the other is the DRY flank, whatever the
    #      compass says and whichever side a future stamp puts the tail on.
    SIDEC, ACHAN = 0, 1e9
    if RCRS:
        for _sg in (-1, 1):
            _near = 1e9
            for _s in range(5):
                _b = WB0 + (WB1 - WB0) * _s / 4.0
                _a = GATE_HALF
                while _a < 120.0 and not _wet(_sg * _a, _b):
                    _a += 0.05
                _near = min(_near, _a)          # the SHORTEST dry reach founds the wall
            if _near < ACHAN:
                SIDEC, ACHAN = _sg, _near
        assert ACHAN < 119.0, ("the stamped river never crosses the pinch line: the gate "
                               "does not stand in the breach the water made")
    SIDED = -SIDEC if SIDEC else -1

    # ---- the channel flank's rock: a toe INSIDE the water's far edge, so stone and
    #      channel share a metre of the line and the grate's far end dies into rock.
    ACHAN_FAR = ACHAN
    if RCRS:
        _a = ACHAN
        while _a < 120.0 and (_wet(SIDEC * _a, WB0) or _wet(SIDEC * _a, WALLB)
                              or _wet(SIDEC * _a, WB1)):
            _a += 0.05
        ACHAN_FAR = _a
    AROCK_C = max(ACHAN + 0.5, ACHAN_FAR - WALLTOE)

    # ---- the dry flank's rock: SEARCHED outward from the jamb, the first offset at
    #      which the innermost mass clears every walkable area floor by a metre.  Round
    #      2's western chain lying along the top of Home Row is what this search exists
    #      to make impossible; the gate court is what it actually binds against here.
    AREADISC = [(l["pos"], l.get("extent", 3)) for l in D["landmarks"]
                if l.get("class") == "area" and l["id"] not in WATER_LM]

    def _clear_of_areas(a0, a1, b0, b1, m=1.0):
        for (_p, _r) in AREADISC:
            _pa = (_p[0] - GX) * ACRX + (_p[1] - GY) * ACRY
            _pb = (_p[0] - GX) * OUTX + (_p[1] - GY) * OUTY
            if math.hypot(max(a0 - _pa, 0.0, _pa - a1),
                          max(b0 - _pb, 0.0, _pb - b1)) < _r + m:
                return False
        return True

    # A MASS IS A PILE, NOT A TOWER (round 2's finding, kept): three offset lumps under a
    # broad cap.  It gets TALLER as it gets further from the gap, because that is what
    # makes a bluff read as a bluff — but the ramp plateaus at k=6, since the far end of
    # the chain is a map boundary and a 40 m spike on the horizon is a different mistake.
    BSTEP, NFACE, RAKE = 8.2, 3, 3.0

    FACEPROUD = 0.25

    def _mass(side, k):
        _bwd = 20.0 + 9.0 * h01(k, side + 3, 223)
        _bdp = 17.0 + 8.0 * h01(k, side + 5, 227)
        # THE FACE STANDS 0.25 m PROUD OF THE LINE, NEVER ON IT.  With the innermost
        # mass's south face laid exactly on b = 0, the rectangle test is a knife edge:
        # `in_rect` rotates by the pinch bearing, sin(-pi) is -1.2e-16 rather than 0, and
        # the 18 m lever arm from the mass's centre turns that into ~2e-15 of slop — so
        # BOTH chains' innermost masses read as absent from the very samples the seal is
        # measured on, and the probe reported an open notch through solid rock.  A face
        # that overlaps the line by a hand's breadth cannot be missed by arithmetic.
        _jit = FACEPROUD + (0.0 if k == 0 else 1.4 * h01(k, side + 9, 251))
        # THE FIRST THREE MASSES STAND ON THE PINCH LINE and the rest rake back out of
        # the valley, so the range pulls away from the village as it runs to the map's
        # edge instead of looming along the top of it.  The jitter is INTO the valley
        # only: a ragged rock face is wanted; a ragged rock face with a hole in it is the
        # thing this round exists to fix.
        return _bwd, _bdp, (0.0 if k < NFACE else (k - NFACE + 1) * RAKE) - _jit

    AROCK_D = GATE_HALF
    while AROCK_D < 40.0:
        _bwd, _bdp, _b0 = _mass(SIDED, 0)
        _alo, _ahi = sorted((SIDED * AROCK_D, SIDED * (AROCK_D + _bwd)))
        if _clear_of_areas(_alo, _ahi, _b0, _b0 + _bdp):
            break
        AROCK_D += 0.25

    for _side, _edge in ((SIDED, AROCK_D), (SIDEC, AROCK_C)):
        _k = 0
        while _k < 24:
            _bwd, _bdp, _b0 = _mass(_side, _k)
            _ain = _edge + _k * BSTEP
            if not _onmesh(_side * _ain, _b0 + _bdp / 2):
                break
            _alo, _ahi = sorted((_side * _ain, _side * (_ain + _bwd)))
            CHAIN.append((_side, _k, _ain, _bwd, _bdp, _b0))
            BLUFFS.append(_rect(_alo, _ahi, _b0, _b0 + _bdp))
            _k += 1

    # THE WALL TAKES A BITE INTO THE ROCK IT DIES INTO, and this is round 2b's knife edge
    # arriving from the other side.  Built flush, the curtain wall's outer end and the
    # innermost rock mass's inner face are the SAME coordinate, and the seal probe steps
    # the pinch line at 0.05 m: whenever that grid lands exactly on the join, `in_rect`
    # answers "outside" for both rectangles and the run reports 0.05 m of open ground
    # through solid masonry-into-cliff.  It held at HEAD only because the searched offset
    # happened to fall off the sampling grid; with the gate moved it landed on it and the
    # build failed.  A wall built INTO living rock overlaps the rock — that is what
    # "built wall-to-wall into living rock" means — so it does, by a hand's breadth.
    # BOTH ENDS OF EVERY RUN, not just the rock end: the doorway's jamb is a coincident
    # boundary too (the bay rect ends where the curtain wall begins), and the strip is
    # measured stepping OUT FROM the jamb, so that join sits on the very first sample.
    # It cost a build failure of exactly 0.05 m — one sample of "open ground" through the
    # gatepost — before the pattern was believed.
    WALLBITE = 0.30
    SEALMAS.append(_rect(*sorted((SIDED * (AROCK_D + WALLBITE),
                                  SIDED * (GATE_HALF - WALLBITE))), WB0, WB1))
    SEALMAS.append(_rect(*sorted((SIDEC * (GATE_HALF - WALLBITE),
                                  SIDEC * (AROCK_C + WALLBITE))), WB0, WB1))
    # THE GATE'S OWN BAY IS PART OF THE SEAL, and leaving it out is a hole exactly one
    # doorway wide.  `foot_rect` cuts an area floor to the gate's 4.6 x 1.6 massing, which
    # is thinner than the wall it now stands in — so the gate court's disc poked THROUGH
    # the doorway and left walk cells 1.9 m out the far side of the bottleneck.  The doors
    # are sealed; the floor under them is not floor until the story opens them.
    SEALMAS.append(_rect(-GATE_HALF, GATE_HALF, WB0, WB1))
    SEALCUT = SEALMAS + BLUFFS
    _cdir = "east" if (ACRX * SIDEC) > 0 else "west"
    print("  THE SEAL               the pinch line runs %.0f deg through the gate at "
          "(%.1f, %.1f); across it, rock to rock: %.2f m of wall | the %.2f m doorway | "
          "%.2f m of founded wall | %.2f m of wall over the grate | rock  (the channel "
          "is on the %s flank, derived)"
          % (math.degrees(SEALRZ) % 180.0, GX, GY, AROCK_D - GATE_HALF, 2 * GATE_HALF,
             ACHAN - GATE_HALF, AROCK_C - ACHAN, _cdir))
    print("    the dry flank's wall dies into rock %.2f m out — SEARCHED, the first "
          "offset at which the innermost mass clears every walkable area floor by 1.0 m"
          % AROCK_D)
    print("    the channel crosses the line %.2f..%.2f m out (%.2f m of water); the rock "
          "takes a %.2f m toe inside its far edge, so the LOW GRATE spans %.2f m under "
          "one unbroken run of coursed masonry — there is no gap in the barrier at all"
          % (ACHAN, ACHAN_FAR, ACHAN_FAR - ACHAN, WALLTOE, AROCK_C - ACHAN))


def in_bluff(x, y, m=0.0):
    for r in BLUFFS:
        if in_rect(x, y, r, m):
            return True
    return False


def in_seal(x, y, m=0.0):
    for r in SEALCUT:
        if in_rect(x, y, r, m):
            return True
    return False


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
ntree = noff = nwet = nrock = 0
RIMFEET = []                  # the Whisperwood corridor below interlocks with these
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
    if in_seal(x, y, -1.0):
        nrock += 1
        continue                        # the range is rock; the wood climbs it, at dressing
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
    # A GATE NOBODY FILLS IS NOT A GATE.  `RIMFEET` was declared here in round 2 and the
    # forest pass tests every candidate against it — but nothing ever appended to it, so
    # the check has been reading an empty list since the day it was written and printing
    # "0 refused on a rim tree" as if that were a result.  The wood has therefore been
    # free to grow inside the rim's own trunks for two rounds.  Filled (round 3).
    RIMFEET.append((x, y))
    ntree += 1
print("  veg_emb_rim_*          %d trees of %d over %.0f m of perimeter (%.2f m apart; "
      "%d stood in the river and the wood opens there, %d stood in the range's own rock, "
      "%d fell off the ground mesh)"
      % (ntree, RIMN, _per, _per / max(ntree, 1), nwet, nrock, noff))
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
        # THE MAP CARRIES THE MILL'S BODY (stamp 2026-08-01, on the dressing lane's
        # measurement).  This is the number the DOORSTEP is derived from, so it is the
        # one that has to move when the building does — the 2x re-rule left it at the
        # old literal and put the mill's own pad 1.12 m inside the dressed footprint.
        _fp = l.get("footprint")
        if _fp:
            return (_fp[0] * 1.14, _fp[1] * 1.14)
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
                 avoid_river=True, scale=1.0, reject=None, wscale=1.0, hscale=1.0):
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
        # THE IMPLIED TIER READS SMALLER, WHICH IS THE WHOLE TECHNIQUE.  `wscale`/`hscale`
        # are separate from `scale` because `scale` also feeds the height blend below and
        # a further tier has to shrink in BOTH dimensions, not one and a bit.  Defaulted to
        # 1.0 so the infill clusters are untouched; only the vistas pass them.
        bw = (3.6 + 2.2 * h01(salt, k, 11)) * scale * wscale
        bd = bw * (0.72 + 0.3 * h01(salt, k, 13))
        # A ROOF THAT WOULD STAND ON A LANE IS DROPPED, NOT MOVED.  Infill passes a
        # `reject` predicate (the walk-clearance test); moving the roof to satisfy it
        # would walk the cluster into the NEXT lane, which is how the first infill draft
        # put four background cottages across Home Row.  A cluster is allowed to come out
        # smaller than it asked for, and the count is reported.
        if reject is not None and reject(vx, vy, max(bw, bd) / 2):
            continue
        vz = ground_z(vx, vy)
        bh = (2.8 + 1.6 * h01(salt, k, 17)) * (0.85 + 0.15 * scale) * hscale
        vrz = h01(salt, k, 19) * math.pi
        box("%s_%d_body" % (name, k), vx, vy, vz + bh / 2, bw, bd, bh,
            M_PLASTER, cname, vrz)
        rh = (1.5 + 0.5 * h01(salt, k, 23)) * hscale
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
        # A SUBSTRING MATCH ON A DISPLAY NAME IS NOT A CLASS TEST, and this one cost the
        # town a whole mapped landmark in silence.  The guard exists for `river-vista` and
        # `downstream-vista`, where the water IS the vista and a roof cluster would be
        # wrong.  It matched on the lowercased NAME, and `east-cottages` is called
        # "Riverside cottages (vista)" — so a cottage cluster whose name merely mentions
        # the river was skipped, and the blockout emitted NOTHING for a landmark the map
        # carries. It was invisible because a vista that is not built looks exactly like a
        # vista that is far away. The test is the landmark's own ID.
        if i in ("river-vista", "downstream-vista"):
            continue                                    # the water IS the vista
        # THE FURTHER TIER MUST READ SMALLER THAN THE VILLAGE, WHICH IS ITS ENTIRE JOB.
        # Coordinator's ruling 2026-08-01: a further tier says "more town beyond your
        # reach", so it has to read SMALLER, never larger, and the depth cue is roof COUNT
        # and OVERLAP rather than volume.  Measured PER ROOF (the matched unit — the first
        # measurement compared a five-roof CLUSTER's bounds to a single house's and made
        # them look 2.5x too big): as built, a vista roof is 0.92x a real house across and
        # 1.03x its ridge, i.e. indistinguishable in size from a house the player can walk
        # to. The ruled band is 0.55-0.70x across and 0.75-0.85x ridge, so the tier takes
        # 0.67x width and 0.78x height to land mid-band at 0.62x / 0.80x, and four roofs on
        # a tighter spread so they OVERLAP into one settlement instead of standing apart.
        VISTAROOFS.extend(roof_cluster("lm_" + i, x, y, len(i), 4, spread=(1.6, 3.0),
                                       wscale=0.67, hscale=0.78))
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
            # THE JAMB'S OUTER FACE IS `GATE_HALF`, not a literal 0.1 m inside it.  The
            # curtain walls that seal the pinch butt against exactly this plane, and a
            # wall that overlaps its jamb is a geometry_audit intersection while a wall
            # 0.1 m off it is a crack in the one barrier the map calls absolute.
            for sgn, tag in ((-1, "L"), (1, "R")):
                box("lm_%s_jamb%s" % (i, tag), x + sgn * (GATE_HALF - GATE_JAMBW / 2), y,
                    z + 1.7, GATE_JAMBW, GATE_DEEP, 3.4, M_STONE, "EMB_MASSING", rz)
            box("lm_%s_lintel" % i, x, y, z + 3.7, 2 * GATE_HALF, GATE_DEEP, 0.7,
                M_STONE, "EMB_MASSING", rz)
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
        # THE BODY IS THE MAP'S, NOT A LITERAL.  The user's 2x re-rule doubled this mill
        # and nothing about it reached this branch, so the doorstep — derived from the
        # body's own half-depth — went on being derived for a 5.6 x 4.6 building that no
        # longer exists, and landed 1.12 m INSIDE the dressed footprint (measured by the
        # dressing lane, stamped 2026-08-01). `footprint` is [W, D, wall height]; the old
        # literals are the fallback for a landmark that does not carry one.
        bw, bd, bh = l.get("footprint", (5.6, 4.6, 5.2))
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
           # THE CH1 STAMPS THAT LANDED AFTER THIS SET WAS WRITTEN, and the assert below
           # is what found them: with the plates and the stall in, the build made 17 lamps
           # against a roll the map fixes at 14 and REFUSED TO SAVE — so the committed
           # master has not been rebuildable from its own builder since those stamps
           # landed, and nothing noticed because nobody had re-run it.
           #   NEITHER OF THESE IS A NEW DECISION.  `sigil-plate-w/e` stand IN the gate
           # court, and the map's own `lamps._doc` already rules that the gate court gets
           # NO lamp ("nobody's warmth reaches the Old Gate"; the Gate Field is the town's
           # one unwarm frame) -- a lamp on a sigil plate would light the exact frame canon
           # says must stay dark.  `poppy-stall` is a market stall inside Festival Square,
           # which already carries the ring-closers 12 and 13; a stall does not get its own
           # lamppost, and the roll count is map canon at fourteen either way.
           "sigil-plate-w", "sigil-plate-e", "poppy-stall",
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

# ================= THE SECLUDED APPROACH — where the town stops and the wood begins ==
# USER SECLUSION RULING 2026-08-01 (map `sigil-gate`): the Old Gate is too close to the
# town centre and moves to genuine seclusion, reached by *a quiet, wooded, incident-free
# stretch between the town's last warmth (the barn/dovecote area) and the court, designed
# as a MEASURED environment shift: village roofs fall out of sight past a threshold, lamp
# warmth ends at the barn, the forest closes in, then the sealed gate.*
#
# THE CORRIDOR IS DERIVED FROM THE MAP, NOT NAMED, so a re-stamped gate moves the whole
# environment shift with it and nothing here has to be re-tuned:
#   the SEALED portal          -> the map's own `state: sealed`
#   its COURT                  -> the area landmark the portal has an edge to
#   the WARM END               -> the last landmark on the lane chain back from that court
#                                 that HOSTS A LAMP.  Lake's round is map canon at
#                                 fourteen and does not grow (`lamps._doc`), so "where the
#                                 warmth ends" is a fact the build already knows: it is
#                                 wherever the roll's most gate-ward stop happens to be.
#   the APPROACH               -> the drawn lane between the two, trimmed by the warm
#                                 end's own apron so the barnyard is still the barnyard
# Inside it: NO households, NO lane incidents, and the forest at WHISPERWOOD density with
# its understory — the same treatment the arrival road gets, for the same reason (a
# canopy that starts at 4 m occludes nothing at a walker's eye, and a walker's eye is the
# only height this stretch is ever seen from).
SECL = []                               # the approach as a polyline, warm end -> court
SECL_EDGES = set()                      # the lane keys it is made of
SECL_R = 18.0                           # how wide the quiet stretch reads, either side
SECL_APRON = 9.0                        # the barnyard's own ground, left out of it
SECL_WARM = None
SECL_COURT = None
if SEALED:
    _sg = SEALED[0]["id"]
    for e in EDGES:
        for _a, _b in ((e["from"], e["to"]), (e["to"], e["from"])):
            if _a == _sg and LM.get(_b, {}).get("class") == "area":
                SECL_COURT = _b
    if SECL_COURT:
        _adj = {}
        for e in EDGES:
            _adj.setdefault(e["from"], []).append(e["to"])
            _adj.setdefault(e["to"], []).append(e["from"])
        _seen, _q = {SECL_COURT: [SECL_COURT]}, [SECL_COURT]
        _lamphosts = set(PLACED)
        while _q:
            _n = _q.pop(0)
            if _n in _lamphosts:
                SECL_WARM = _n
                break
            for _m in sorted(_adj.get(_n, [])):
                if _m not in _seen and _m != _sg:
                    _seen[_m] = _seen[_n] + [_m]
                    _q.append(_m)
        if SECL_WARM:
            _path = _seen[SECL_WARM][::-1]              # warm end -> ... -> the court
            _pts = []
            for _i in range(len(_path) - 1):
                _k = "%s__%s" % (_path[_i], _path[_i + 1])
                _kr = "%s__%s" % (_path[_i + 1], _path[_i])
                _d = LANEDRAW.get(_k) or LANEDRAW.get(_kr)
                if not _d:
                    continue
                SECL_EDGES.add(_k if _k in LANEDRAW else _kr)
                _dd = list(_d)
                if math.hypot(_dd[0][0] - POS[_path[_i]][0],
                              _dd[0][1] - POS[_path[_i]][1]) > \
                   math.hypot(_dd[-1][0] - POS[_path[_i]][0],
                              _dd[-1][1] - POS[_path[_i]][1]):
                    _dd.reverse()
                _pts.extend(_dd if not _pts else _dd[1:])
            # trim the warm end's own apron off the front: the ground around the barn is
            # still the town's, and the shift starts where the town stops.
            _run = 0.0
            for _i in range(1, len(_pts)):
                _run += math.hypot(_pts[_i][0] - _pts[_i - 1][0],
                                   _pts[_i][1] - _pts[_i - 1][1])
                if _run >= SECL_APRON:
                    SECL = _pts[_i - 1:]
                    break
            SECL_LEN = 0.0
            for _i in range(1, len(SECL)):
                SECL_LEN += math.hypot(SECL[_i][0] - SECL[_i - 1][0],
                                       SECL[_i][1] - SECL[_i - 1][1])
            print("  THE APPROACH           the town's last warmth is lamp %02d at %s; "
                  "from %.1f m past it the quiet stretch runs %.1f m of wooded road to "
                  "%s — no households, no incidents, no lamps, the wood at Whisperwood "
                  "density %.0f m either side"
                  % (PLACED.index(SECL_WARM), SECL_WARM, SECL_APRON, SECL_LEN,
                     SECL_COURT, SECL_R))


def beyond_warmth(x, y):
    """Is (x, y) further out of the valley than the quiet approach's own start?

    NOBODY LIVES PAST THE LAST LAMP, AND NOBODY FARMS THERE EITHER.  This rule is the
    one the seclusion round could not have guessed it needed, and the probe found it:
    moving the gate north drags the town's anchor box up the approach with it, the infill
    grid seeds to that box plus 16 m, and the first candidate build put TWENTY-SEVEN new
    households in the wilderness either side of the secluded road — far enough off the
    lane to clear the 18 m corridor, close enough that fourteen of their roofs were in
    sight from the gate court.  The environment shift was built and then suburbanised in
    the same run.  So the village ENDS where its approach begins, measured along the
    gate's own out-of-the-valley axis: past that line the ground is wood, and the only
    thing standing on it is the road.
    """
    if not SECL or GATEFRAME is None:
        return False
    return (x - SECL[0][0]) * OUTX + (y - SECL[0][1]) * OUTY > 0.0


def in_approach(x, y, m=0.0):
    """Inside the quiet wooded stretch between the town's last warmth and the court."""
    if not SECL:
        return False
    for _a, _b in zip(SECL, SECL[1:]):
        if seg_dist2(x, y, _a[0], _a[1], _b[0], _b[1]) < (SECL_R + m) ** 2:
            return True
    return False


def approach_d(x, y):
    """Distance to the approach's own line (1e9 when there is no approach)."""
    if not SECL:
        return 1e9
    return math.sqrt(min(seg_dist2(x, y, a[0], a[1], b[0], b[1])
                         for a, b in zip(SECL, SECL[1:])))


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
nincident_quiet = 0
for _span, _key in sorted(((v, k) for k, v in RUNS.items() if v >= 15.0), reverse=True):
    a_id, b_id = _key.split("__")
    want = 2 if _span >= 20.0 else 1
    if a_id in GATEFIELD or b_id in GATEFIELD:
        want -= 1                                       # the unwarm end thins to nothing
    if _key in SECL_EDGES:
        # AND THE QUIET STRETCH THINS TO NOTHING AT ALL.  The seclusion ruling asks for
        # "NO incidents" on the approach, and the gatefield's own -1 is not enough once
        # the road is long: a 55 m lane asks for two, gets one for being unwarm, and one
        # handcart is exactly the domestic life this stretch exists to be free of.
        want = 0
        nincident_quiet += 1
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
if nincident_quiet:
    print("    %d lane(s) of the quiet approach were denied their incidents by the "
          "seclusion ruling" % nincident_quiet)
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
    # THE SEAL CUTS FLOOR LIKE ANY OTHER SOLID.  The gate court is an r10 disc centred
    # 8 m inside the gate, so its own floor LAPS 1.8 m past the gate on both flanks —
    # walk cells standing north of the pinch line, beside the one barrier the map calls
    # absolute.  The curtain walls and the rock are derived before this loop precisely so
    # that they can be holes in it.
    holes += [f for f in SEALCUT
              if math.hypot(f[0] - x, f[1] - y) <= r + f[2] + f[3] + 1]
    n = int(math.ceil(r / CELL))
    v, f, ncell, nbrookcut, nsteep, nbank = [], [], 0, 0, 0, 0
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
            # AN AREA FLOOR MAY NOT REACH THE RIVER BANK.  The map's words are "vista
            # only, never walkable" and the build already asserts 3.0 m of clearance from
            # every walk VERTEX — but it asserted it for the first time this round, because
            # until the tail was stamped the offender was a landmark pad that failed first
            # and masked the floor behind it.  The gate court's r10 east rim stands 2.21 m
            # off the stamped channel: a plaza whose far cells are the river's own bank.
            # The extent is the map's; where its cells may LIE is the build's.
            if RCRS:
                _rd, _rw = river_at(cx, cy)
                if _rd - _rw / 2 < 3.5:
                    nbank += 1
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
    print("    walk_lm_%-16s %3d cells @ %.1f m, %d footprints cut%s%s%s"
          % (i, ncell, CELL, len(holes),
             ", %d MORE cut by the brook" % nbrookcut if nbrookcut else "",
             ", %d handed to a lane climbing off it" % nsteep if nsteep else "",
             ", %d given back to the river bank" % nbank if nbank else ""))
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


# THE CAMERAS, WHICH ARE THE OTHER THING A TREE OR A ROOF CAN RUIN.  The six shots in
# `emberbrook.cameras.json` each own landmarks and edges; the shot exists to show its
# PRINCIPAL SUBJECT (the Heartlight from the square, the sealed gate from the court, the
# arch from the road) from the routes it owns.  So the sight line from every owned edge's
# ends to that subject is a corridor no village tree and no square-ring roof may stand in.
# Read from the cameras file rather than hard-coded here: a re-authored shot moves the
# corridors with it.  This is the ownership data, NOT `emberbrook.cameras.solved.json` —
# the solved file still carries 1x positions and would aim these corridors at a town that
# no longer exists.


def cam_clear(x, y, m):
    """Is (x, y) at least `m` off every camera's line to its own principal subject?"""
    return not any(math.sqrt(seg_dist2(x, y, c[0][0], c[0][1], c[1][0], c[1][1])) < m
                   for c in CAMLINES)
CAMLINES = []
try:
    _CAMD = json.load(open(os.path.join(REPO, "public/townmap/emberbrook.cameras.json")))
except Exception:
    _CAMD = {"cameras": []}
for _cam in _CAMD.get("cameras", []):
    _own = _cam.get("owns") or {}
    _cands = [i for i in _own.get("landmarks", []) if i in LM]
    if not _cands:
        continue
    _subj = None
    for _pri in (lambda l: l.get("kind") == "heartlight",
                 lambda l: l.get("class") == "portal",
                 lambda l: l.get("class") == "area",
                 lambda l: True):
        _hit = [i for i in _cands if _pri(LM[i])]
        if _hit:
            _subj = _hit[0]
            break
    # THE @RANGE IS PART OF THE OWNERSHIP AND IGNORING IT MAKES THE CORRIDOR A VETO.
    # `square-plaza__barn@0..0.573` means the square camera owns the first 57% of that
    # lane, not the barn — and the first version of this block took the far LANDMARK as
    # the viewpoint, so the square's corridors ran 24 m out to the tithe barn and swept
    # the whole annulus the ring pass has to build in (153 candidate house positions
    # refused, 4 houses placed).  A camera cannot be blocked on ground it does not own.
    _ends = set()
    for _es in _own.get("edges", []):
        _eid = _es.split("@")[0]
        _rng = _es.split("@")[1] if "@" in _es else "0..1"
        _a, _b = _eid.split("__")
        if _a not in LM or _b not in LM:
            continue
        try:
            _t0, _t1 = [float(v) for v in _rng.split("..")]
        except ValueError:
            _t0, _t1 = 0.0, 1.0
        for _t in (_t0, _t1):
            _p = (POS[_a][0] + (POS[_b][0] - POS[_a][0]) * _t,
                  POS[_a][1] + (POS[_b][1] - POS[_a][1]) * _t,
                  POS[_a][2] + (POS[_b][2] - POS[_a][2]) * _t)
            if math.hypot(_p[0] - POS[_subj][0], _p[1] - POS[_subj][1]) > 2.0:
                _ends.add((round(_p[0], 3), round(_p[1], 3), round(_p[2], 3)))
    for _end in sorted(_ends):
        CAMLINES.append((_end, POS[_subj], _cam.get("id", "?")))

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
INFILL_PLOTS = []                       # (x, y, plot radius) — a household's CLAIMED ground
INFILL_TRACKS = []                      # (p0, p1, width) — the way TO a house is claimed too
INFILL_FRUIT = []                       # the fruit trees already standing in the plots
INFILL_RECTS = []                       # every cottage built so far, as an oriented rect
INFILL_SEALED = []                      # seeds refused because they lay past the pinch
INFILL_QUIET = []                       # ... and because they lay on the quiet approach
INFILL_CLEAR = 4.6                      # a household's centre, this far off any walk surface
BOUND_FRAC = []                         # how much of each plot's perimeter is bounded at all
BOUND_KIND = [0, 0, 0]                  # dry-stone rows / rail fragments / bramble clumps
NOBOUND_FIX = [0]                       # plots whose drawn runs were ALL rejected


def infill_ok(x, y, clear, sep):
    if not (X0 + 6 < x < X1 - 6 and Y0 + 6 < y < Y1 - 6):
        return False
    if wdist(x, y) < clear or in_water(x, y, 1.5) or lm_blocked(x, y, 3.2):
        return False
    # NOBODY LIVES PAST THE PINCH.  The seed grid runs to the anchor box plus 16 m, which
    # at 2x reaches 24 m NORTH of the Old Gate — outside the valley the gate closes, in
    # ground that is now the range's own rock.  The seal is a wall to the infill for the
    # same reason it is a wall to the player, and the count it costs is REPORTED, because
    # "the village got smaller" is exactly the kind of change that must not arrive
    # silently inside a terrain round.
    if in_seal(x, y, 2.0):
        INFILL_SEALED.append((x, y))
        return False
    # NOBODY LIVES ON THE QUIET STRETCH.  The seclusion ruling's own words — "NO
    # households" — and it has to be a gate rather than a hope: the infill grid runs to
    # the anchor box plus 16 m, and moving the gate north extends that box straight up
    # the approach, so without this the environment shift would be built and then
    # populated in the same run.
    if in_approach(x, y) or beyond_warmth(x, y):
        INFILL_QUIET.append((x, y))
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

# (d) THE SQUARE'S OWN RING, AND IT GETS THE GROUND BEFORE THE GRID DOES.
# USER RULING 2026-08-01 (map `coexistence._doc` (3)): *more buildings and trees closing
# the ring around Festival Square so it reads as its own space.*  The grid pass cannot
# deliver that, and the reason is arithmetic rather than luck: its probability field is
# a warmth gradient, it seeds on a 3.4 m lattice, and the ring that would close the
# square is a 19-25 m annulus whose inner edge is set by the plaza's own r14 floor plus
# the 4.6 m every household stands off a walk surface.  The grid drops seeds into that
# annulus at the same rate as anywhere else and the square stayed a field with a
# Heartlight in it — SEVEN of sixteen compass sectors ending in a roof or a canopy.
#
# So the annulus is swept DELIBERATELY, sector by sector, and three things about how:
#  *  IT IS A SEARCH, NOT A PLACEMENT.  Each sector tries radii outward and bearings
#     either side, takes the first offset that passes the same `infill_ok` gate every
#     other household passes, and gives up if none does.  Nothing is nudged.
#  *  TWO PER SECTOR, because one cottage at 20 m subtends about 15 degrees and a sector
#     is 22.5 — one roof leaves the sector's shoulders open, which is what the probe
#     measures and what the eye sees.
#  *  IT MAY NOT STAND IN A CAMERA'S WAY.  A tree on a sight line is a nuisance; a
#     five-metre roof on the line from the arch road to the Heartlight is the shot.  The
#     ring seeds are the one infill class gated on `cam_clear`, and the count refused is
#     printed rather than swallowed.
SQ_RING = 0
SQ_CAMREF = 0
_sq = LM.get("square-plaza")
if _sq:
    _sqx, _sqy, _sqz = _sq["pos"]
    _sqe = _sq.get("extent", 14)
    for _s in range(16):
        _put = 0
        for _rad in (_sqe + 5.0, _sqe + 7.4, _sqe + 9.8, _sqe + 12.2):
            for _sw in (0.0, -0.13, 0.13, -0.26, 0.26):
                _ba = 2 * math.pi * _s / 16 + _sw
                sx = _sqx + _rad * math.cos(_ba)
                sy = _sqy + _rad * math.sin(_ba)
                if not cam_clear(sx, sy, 4.0):
                    SQ_CAMREF += 1
                    continue
                if infill_ok(sx, sy, INFILL_CLEAR, seed_sep(sx, sy)):
                    INFILL_SEEDS.append((sx, sy, "square-ring", seed_sep(sx, sy)))
                    SQ_RING += 1
                    _put += 1
                    break
            if _put >= 3:
                break
    print("    infill: %d households SEARCHED onto Festival Square's own 19-26 m ring to "
          "close it into a room (%d candidate offsets refused for standing on a camera's "
          "line to its own subject)" % (SQ_RING, SQ_CAMREF))

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

    # ---- the garden plot: A WILDERNESS BOUNDARY, AND ONLY PART OF ONE ---------------
    # USER RULING 2026-08-01 (map `coexistence._doc` (1) — the town-model review, which
    # SUPERSEDES the round-2 refinement's styling where they conflict): the trimmed hedge
    # ring around every household is SUBURBAN vocabulary, and this is a village that has
    # stood itself up inside a forest.  Two changes, and the second is the one that does
    # the work:
    #
    #  (a) THE VOCABULARY.  Irregular dry-stone rows, split-rail and paling FRAGMENTS,
    #      bramble clumps.  Drawn per RUN rather than per household, because a real plot
    #      is stone where somebody cleared stone, rail where somebody had timber, and
    #      bramble where nobody did anything at all — one household can carry all three.
    #  (b) PARTIAL ENCLOSURE.  The old ring built 15 of its 16 segments: a plot fenced
    #      all the way round with one gate in it.  A claimed plot in a forest village is
    #      not fenced, it is BOUNDED IN PLACES — 2 or 3 runs of boundary covering a
    #      minority of the perimeter, the rest simply the ground the wood is on.  The
    #      fraction each household closes is drawn from its own hash and REPORTED as a
    #      distribution, because "partial" is a number and not an adjective.
    #
    # THE ROUND-3 LESSON HOLDS INSIDE A RUN: a boundary is a LINE, NOT A ROW OF DASHES.
    # Segments inside a run overlap on purpose (1.85 m of stone at ~1.45 m centres), and
    # the irregularity is radial and rotational jitter, never a gap.  Bramble is the one
    # exception and it is deliberate: a bramble clump IS a gappy thing, so it drops every
    # third segment and wanders further off the line.
    plot = 4.6 + 2.4 * h01(salt, 0, 37)
    INFILL_PLOTS.append((sx, sy, plot))
    nseg = 24
    nrun = 2 + (h32(salt, 0, 41) % 2)
    _runs = []
    for r_ in range(nrun):
        _ra = 2 * math.pi * (r_ + 0.10 + 0.80 * h01(salt, r_, 151)) / nrun
        _rs = 0.80 + 1.20 * h01(salt, r_, 157)          # 46..115 deg of arc
        _runs.append((_ra, _rs, h32(salt, r_, 163) % 3))
    nh = 0
    nseg_built = 0
    for _try in range(2):
      if _try and nseg_built >= 3:
        break
      if _try:
        # A PLOT THAT BOUNDS NOTHING IS NOT A CLAIMED PLOT, and "partial" cannot be
        # allowed to decay into "absent".  Three segments is the floor: one stone lying
        # on its own is litter, a 5 m run of it is somebody's boundary.  When the drawn
        # runs were rejected — a neighbour's wall, a lane, the water — one run is laid
        # on the arc BEHIND the house (opposite the way in, the side least likely to be
        # the reason the others failed) at the tightest margin the gate will accept.
        # Counted and reported: a rule that fires silently is a rule nobody can review.
        _runs = [(gate_a + math.pi - 0.55, 1.10, h32(salt, 0, 163) % 2)]
        NOBOUND_FIX[0] += 1
      for k in range(nseg):
        a = 2 * math.pi * k / nseg + h01(salt, 0, 43) * 0.9
        da = abs(((a - gate_a + math.pi) % (2 * math.pi)) - math.pi)
        if da < 0.42:
            continue                                    # the way in
        kind = None
        for (_ra, _rs, _rk) in _runs:
            if ((a - _ra) % (2 * math.pi)) <= _rs:
                kind = _rk
                break
        if kind is None:
            continue                                    # PARTIAL: nobody bounded this arc
        # the line wanders; it does not break.  radial wobble first, so the reject test
        # is asked about the stone that is actually laid.
        wob = (h01(salt, k, 167) - 0.5) * (1.0 if kind == 2 else 0.5)
        yaw = a + math.pi / 2 + (h01(salt, k, 173) - 0.5) * (0.7 if kind else 0.36)
        hx = sx + (plot + wob) * math.cos(a)
        hy = sy + (plot + wob) * math.sin(a)
        if _rej(hx, hy, 0.55 if _try else 1.0):
            continue
        gz_ = ground_z(hx, hy)
        if kind == 0:                                   # AN IRREGULAR DRY-STONE ROW
            _sh = 0.44 + 0.26 * h01(salt, k, 179)
            box("%s_drystone%02d" % (tag, k), hx, hy, gz_ + _sh / 2,
                1.85, 0.52 + 0.22 * h01(salt, k, 181), _sh, M_STONE, "EMB_MASSING", yaw)
        elif kind == 1:                                 # SPLIT RAIL / PALING FRAGMENT
            box("%s_rail%02dp" % (tag, k), hx, hy, gz_ + 0.52,
                0.16, 0.16, 1.04, M_TIMBER, "EMB_MASSING", yaw)
            for _rr in range(2):
                box("%s_rail%02d%d" % (tag, k, _rr), hx, hy, gz_ + 0.44 + _rr * 0.38,
                    1.85, 0.09, 0.13, M_TIMBER, "EMB_MASSING", yaw)
        else:                                           # A BRAMBLE CLUMP
            if (h32(salt, k, 191) % 3) == 0:
                continue                                # brambles clump; they do not run
            _bw = 1.3 + 0.9 * h01(salt, k, 193)
            _bh = 0.60 + 0.45 * h01(salt, k, 197)
            pyramid("%s_bramble%02d" % (tag, k), hx, hy, gz_ - 0.10, _bw, _bw * 0.85,
                    _bh + 0.10, M_LEAF_G, "EMB_MASSING", yaw)
        nh += 1
        nseg_built += 1
    BOUND_FRAC.append(nseg_built / float(nseg))
    for (_ra, _rs, _rk) in _runs:
        BOUND_KIND[_rk] += 1

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
        INFILL_FRUIT.append((tx, ty))

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
        INFILL_TRACKS.append((p0, p1, wdt_))
    ntrack += 1 if joined else 0
    nfade += 0 if joined else 1
    ninf += 1
if INFILL_QUIET:
    print("    infill: %d candidate seeds stood ON OR PAST THE QUIET APPROACH and are "
          "refused — the village ends where its approach begins (`beyond_warmth`), and "
          "the stretch to the gate court carries no household by ruling"
          % len(INFILL_QUIET))
if INFILL_SEALED:
    _iy = [(_p[0] - GX) * OUTX + (_p[1] - GY) * OUTY for _p in INFILL_SEALED]
    print("    infill: %d candidate seeds stood PAST THE PINCH (%.1f to %.1f m out of the "
          "valley) and are refused — the seed grid runs to the anchor box plus 16 m, and "
          "at 2x that is 24 m beyond the Old Gate"
          % (len(INFILL_SEALED), min(_iy), max(_iy)))
print("  lm_infill_*            %d HOUSEHOLDS (%d roofs), each with a garden plot, a "
      "fruit tree, a shed or woodpile and a track: %d tracks join a real lane, %d fade "
      "into the implied village" % (ninf, ninfroof, ntrack, nfade))
if BOUND_FRAC:
    _bf = sorted(BOUND_FRAC)
    print("    boundaries             WILDERNESS VOCABULARY, PARTIAL BY RULE (map "
          "`coexistence._doc`): %d dry-stone runs, %d split-rail/paling fragments, %d "
          "bramble clumps over %d households — each plot bounds %.0f%% of its own "
          "perimeter (median; %.0f%% least, %.0f%% most), against the trimmed ring's 94%%"
          % (BOUND_KIND[0], BOUND_KIND[1], BOUND_KIND[2], len(_bf),
             100 * _bf[len(_bf) // 2], 100 * _bf[0], 100 * _bf[-1]))
    print("      %d plots had every drawn run rejected (a neighbour, a lane, the water) "
          "and got one fallback run behind the house — a partial boundary may not decay "
          "into no boundary" % NOBOUND_FIX[0])

# ============= THE SEAL, RAISED — the curtain walls and the range, from the rects ==
# The geometry is DERIVED ABOVE (see THE SEAL), before the area floors, because the
# floors have to cut around it: the gate court is an r10 disc whose north rim laps past
# the gate, and a bottleneck with walk cells beside it is not a bottleneck.  Nothing is
# decided here — this raises what was measured, and only the heights and the pile's own
# jitter are new.
if GATEFRAME:
    WALLTOP = GZ + 4.20                 # the head of the wall, level with the gate's own
    GRATETOP = RLVL + 0.85              # "slightly taller than the waterline", user ref
    nwall = 0

    def _side_tag(a):
        """W or E from where the run actually LANDS, not from the sign of an offset in a
        frame whose across-axis is whichever perpendicular fell out of the gate's facing.
        Round 2 named its chains off that sign and shipped them swapped."""
        return "W" if _pt(a, 0.0)[0] < GX else "E"

    def _wallrun(tag, ax0, ax1, base):
        global nwall
        _a0, _a1 = sorted((ax0, ax1))
        if _a1 - _a0 < 0.35:
            return                      # rock already stands against the jamb
        _wx, _wy = _pt((_a0 + _a1) / 2, WALLB)
        box("emb_gatewall_%s" % tag, _wx, _wy, (base + WALLTOP) / 2,
            _a1 - _a0, WALLD, WALLTOP - base, M_STONE, "EMB_MASSING", SEALRZ)
        box("emb_gatewall_%s_cope" % tag, _wx, _wy, WALLTOP + 0.22,
            _a1 - _a0, WALLD + 0.34, 0.44, M_STONE, "EMB_MASSING", SEALRZ)
        nwall += 1

    def _founded(ax0, ax1):
        """THE WALL IS FOUNDED, NOT PLACED: its base is the LOWEST ground under its own
        run (the gorge falls away past the pinch), so it can never hang in the air on
        the downhill side."""
        _a0, _a1 = sorted((ax0, ax1))
        return min(ground_z(*_pt(_a0 + (_a1 - _a0) * _t / 8.0, _bb))
                   for _t in range(9) for _bb in (WB0, WALLB, WB1)) - 1.4

    _wallrun(_side_tag(SIDED * AROCK_D), SIDED * AROCK_D, SIDED * GATE_HALF,
             _founded(SIDED * AROCK_D, SIDED * GATE_HALF))
    _wallrun(_side_tag(SIDEC * ACHAN), SIDEC * GATE_HALF, SIDEC * ACHAN,
             _founded(SIDEC * GATE_HALF, SIDEC * ACHAN))
    # THE WATER PASSES UNDER THE GATE.  Over the channel the same wall continues as plain
    # coursed masonry standing on a LOW GRATE at the waterline — the user's refinement 2,
    # against docs/qa/emberbrook/concepts/gate-final.png: arches are for humans, the water
    # gets a culvert grate slightly taller than the water and stone above it.  At blockout
    # the grate is one coarse band; its bars are the dressing pass's.
    if AROCK_C - ACHAN > 0.35:
        _wallrun(_side_tag(SIDEC * ACHAN) + "grate", SIDEC * ACHAN, SIDEC * AROCK_C,
                 GRATETOP)
        _gx, _gy = _pt(SIDEC * (ACHAN + AROCK_C) / 2, WALLB)
        box("emb_gategrate", _gx, _gy, (RLVL - 1.30 + GRATETOP) / 2,
            AROCK_C - ACHAN, WALLD * 0.55, GRATETOP - (RLVL - 1.30),
            M_STONE, "EMB_MASSING", SEALRZ)
    nblu = 0
    for (_side, _k, _ain, _bwd, _bdp, _b0) in CHAIN:
        _ac = _side * (_ain + _bwd / 2)
        _bc = _b0 + _bdp / 2
        _bx, _by = _pt(_ac, _bc)
        _gz = ground_z(_bx, _by)
        # THE ROCK MUST OUT-TOP THE MASONRY, and round 2's height rule could not know
        # that because there was no masonry yet.  `6.0 + 2.6k` is measured from the mass's
        # OWN ground, and the ground past the pinch falls away toward the valley pan — so
        # the innermost crags came out topping at z 2.5-6.0 against a wall whose head is
        # at 7.3, and the first render of the sealed notch showed a curtain wall standing
        # PROUD of the cliffs it is supposed to be built into.  The floor is now the
        # wall's own head plus a clearance that climbs with the chain, so "wall-to-wall
        # into living rock" is a fact about the geometry rather than a line in the map.
        _bh = max(6.0 + 2.6 * min(_k, 6) + 3.5 * h01(_k, _side + 2, 211),
                  (GZ + 4.20 + 4.0 + 2.2 * min(_k, 6)) - (_gz - 1.5))
        _tag = "emb_bluff_%s%d" % (_side_tag(_ac), _k)
        for _l in range(3):
            _f = 1.0 - 0.24 * _l
            # LUMP 0 CARRIES NO JITTER, in position or in yaw: it IS the rectangle the
            # seal was measured and the floors were cut against.  The two smaller lumps
            # (0.76 and 0.52 of it) and the cap keep theirs and stay inside its skin.
            _jx = 0.0 if _l == 0 else (h01(_k, _side + _l, 239) - 0.5) * _bwd * 0.20
            _jy = 0.0 if _l == 0 else (h01(_k, _side + _l, 241) - 0.5) * _bdp * 0.20
            _yaw = SEALRZ + (0.0 if _l == 0
                             else (h01(_k, _side + _l, 243) - 0.5) * 0.6)
            _lx, _ly = _pt(_ac + _jx, _bc + _jy)
            box("%s_mass%d" % (_tag, _l), _lx, _ly,
                _gz - 1.5 + (_bh * _f) / 2 + _l * _bh * 0.22,
                _bwd * _f, _bdp * _f, _bh * _f, M_STONE, "EMB_CONTEXT", _yaw)
        pyramid("%s_cap" % _tag, _bx, _by, _gz - 1.5 + _bh * 0.96,
                _bwd * 0.66, _bdp * 0.66, 3.0 + 3.0 * h01(_k, _side + 11, 233),
                M_STONE, "EMB_CONTEXT", SEALRZ + (h01(_k, _side + 7, 229) - 0.5) * 0.5)
        nblu += 1
    print("  emb_gatewall_*         %d runs of curtain wall + emb_gategrate: ONE structure "
          "rock to rock, the doors over the road and the river running UNDER it through "
          "a grate %.2f m proud of the water" % (nwall, GRATETOP - RLVL))
    print("  emb_bluff_*            %d rock masses in two chains (%d on the dry flank, "
          "%d beyond the channel), the first %d of each standing ON the pinch line and "
          "the rest raking back out of the valley %.1f m a step; both chains run to the "
          "ground mesh's own edge"
          % (nblu, sum(1 for c in CHAIN if c[0] == SIDED),
             sum(1 for c in CHAIN if c[0] == SIDEC), NFACE, RAKE))


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


# ============ THE VILLAGE TREES — the wood, continuing THROUGH the village ==
# USER RULING 2026-08-01 (map `coexistence._doc` (2)): *large individual trees scattered
# AMONG the houses and over the lanes — several species shapes and sizes, so the wood
# visibly continues through the village.*  These are NOT the forest: the forest is a mass
# with a probability field and it stops where the village begins (`forest_p` holds it
# 8.2 m off every household and 6 m off every lane).  A village tree is an INDIVIDUAL,
# searched onto ground the forest is forbidden, and it is allowed the one thing the forest
# is not — to stand beside a lane and put its canopy over it.
#
# THE PAID LANE RULE, RESTATED RATHER THAN WAIVED.  The forest's rule is "a crown clears
# every walk surface by its own radius plus 1.0 m", and it exists so that nothing hangs in
# a walker's face or narrows a lane.  A village tree over a lane cannot obey the letter of
# it and still be over the lane, so it obeys what the rule is FOR, in two parts that are
# both asserted at the end of the pass:
#     the TRUNK clears every walk surface by its own radius + 1.20 m
#     the CANOPY's underside stands at least 3.60 m up wherever it oversails one
# — so the lane keeps its full width at a body's height, nothing is in frame at eye level
# that a walker could touch, and the tree still arches over the road.  A CONIFER carries
# its skirt at head height and therefore gets NO exemption: for that species the forest's
# own crown+1.0 m rule applies unchanged, which is why the conifers stand off the lanes
# and the broadleaves stand on them.
#
VILLTREES = []                                  # (x, y, crown radius, canopy base z)
# THREE MASSING SHAPES, and the ruling's own words are the specification: "broadleaf
# crowns + slimmer forms alongside the forest conifers".  Sizes and silhouettes are
# deliberately far apart — at blockout the only thing a tree communicates is its
# SILHOUETTE, so two species that differ by 15% differ by nothing.
#   0  BROAD CROWN   a village oak: short heavy bole, a wide blocky dome that reads as
#                    one mass from any bearing, canopy high enough to walk under
#   1  TALL SLIM     a poplar or a birch: a column, twice as tall as it is wide
#   2  CONIFER       the wood's own form at village scale — a skirted cone, and the one
#                    that keeps the forest's crown+1.0 m rule
VSPEC = ("broad crown", "tall slim", "conifer")
VSTEP = 3.0
_vgrid = [(int(math.floor((ANCHX0 - 10) / VSTEP)), int(math.ceil((ANCHX1 + 10) / VSTEP))),
          (int(math.floor((ANCHY0 - 10) / VSTEP)), int(math.ceil((ANCHY1 + 10) / VSTEP)))]
_vn = [0, 0, 0]
_vrej = {"lane": 0, "water": 0, "massing": 0, "camera": 0, "crowded": 0, "rock": 0}
_vworst_trunk, _vworst_at = 1e9, None
_vover, _voverz, _vovercl = 0, [], []
# ONE PLANTING FUNCTION, TWO SEARCHES.  The gates below are the whole of the rule and
# they must be identical wherever a tree is proposed from, so they live in one place and
# both searches call it.  `sd` is the tree's own hash seed: species and size come off it,
# so a tree proposed on a verge and a tree proposed on the grid are drawn the same way.
def vplant(x, y, sp, sd):
    global _vover, _vworst_trunk, _vworst_at
    if not (X0 + 4 < x < X1 - 4 and Y0 + 4 < y < Y1 - 4):
        return False
    if y <= WOOD_Y1 + 8.0:
        return False                 # the Whisperwood road is the wood's, not the village's
    if out_of_town(x, y) > 9.0:
        return False                 # beyond the anchors it is the forest's ground
    if in_approach(x, y) or beyond_warmth(x, y):
        return False                 # past the village's end it is WOOD, not village trees
    # THE SPECIES AND ITS SIZE ARE DRAWN BEFORE THE GATE IS TESTED, exactly as the forest
    # draws its crown radius first: the gate is then a fact about THIS tree rather than
    # about an average one, and a big crown has to find room a small one would not need.
    u = h01(sd, 0, 227)
    if sp == 0:
        ht, trr, crown = 11.0 + 4.0 * u, 0.42 + 0.20 * u, 4.2 + 1.8 * u
        cbase = 4.4 + 0.8 * h01(sd, 0, 229)
    elif sp == 1:
        ht, trr, crown = 14.0 + 4.0 * u, 0.30 + 0.12 * u, 1.9 + 0.8 * u
        cbase = 4.8 + 1.6 * h01(sd, 0, 229)
    else:
        ht, trr, crown = 9.0 + 4.0 * u, 0.30 + 0.15 * u, 2.6 + 1.0 * u
        cbase = 2.4 + 0.8 * h01(sd, 0, 229)
    need = (crown + 1.0) if sp == 2 else (trr + 1.20)
    wd = wdist(x, y)
    if wd < need:
        _vrej["lane"] += 1
        return False
    if in_water(x, y, crown * 0.4):
        _vrej["water"] += 1
        return False
    if in_seal(x, y, 1.0) or in_bluff(x, y, 1.0):
        _vrej["rock"] += 1
        return False
    if lm_blocked(x, y, crown * 0.55 + 0.8) \
            or any(in_rect(x, y, r_, crown * 0.55 + 0.8) for r_ in INFILL_RECTS) \
            or any(math.hypot(x - r[0], y - r[1]) < crown * 0.55 + 3.4
                   for r in VISTAROOFS) \
            or any(math.hypot(x - f[0], y - f[1]) < crown * 0.55 + 1.6
                   for f in LAMPFEET) \
            or any(math.hypot(x - p[0], y - p[1]) < p[2] * 0.55 for p in INFILL_PLOTS) \
            or any(math.hypot(x - f[0], y - f[1]) < crown * 0.5 + 2.2
                   for f in INFILL_FRUIT):
        # A GARDEN IS NOT A NO-TREE ZONE — that was the first version of this gate and it
        # held every broad crown 6-9 m off a household centre, which is further than the
        # households stand apart: the ruling's trees were pushed out of exactly the
        # ground the ruling is about.  What a village tree must not do is stand in the
        # middle of somebody's vegetable plot or grow through the fruit tree that is
        # already there, so the gate is the plot's INNER half and the fruit trees.
        _vrej["massing"] += 1
        return False
    if any(math.sqrt(seg_dist2(x, y, _c[0][0], _c[0][1], _c[1][0], _c[1][1]))
           < crown * 0.6 + 0.8 for _c in CAMLINES):
        _vrej["camera"] += 1
        return False
    if any(math.hypot(x - t[0], y - t[1]) < crown + t[2] + 0.2 for t in VILLTREES):
        _vrej["crowded"] += 1
        return False
    z = ground_z(x, y)
    tag = "veg_emb_village_%02d" % len(VILLTREES)
    _tk, _cw = ([], []), ([], [])
    # THE BOLE REACHES INTO THE CANOPY, and that is a geometry_audit finding rather than
    # a drawing preference.  Built to 1.04 x the canopy base, the trunk's top stood 0.18 m
    # above the crown's underside — and the stray test starts its lateral rays 0.25 m up
    # from a mesh's own floor, so every broadleaf crown reported itself unsupported: a
    # canopy floating over a pole that ended just below it.  Twelve new strays of a class
    # this town had never had.  A metre of overlap is what a tree actually looks like.
    _box_geo(_tk, x, y, z + (cbase + 1.0) * 0.5, trr * 2, trr * 2, cbase + 1.0)
    if sp == 0:                                     # the broad dome: two slabs + a cap
        for c_ in range(2):
            _box_geo(_cw, x, y, z + cbase + 1.1 + c_ * 1.9,
                     crown * 2 * (1.0 - 0.14 * c_), crown * 2 * (1.0 - 0.14 * c_),
                     2.2, h01(sd, c_, 233) * 1.57)
        _pyr_geo(_cw, x, y, z + cbase + 3.9, crown * 1.5, crown * 1.5,
                 max(1.6, ht - cbase - 3.9), h01(sd, 0, 239) * 1.57)
    elif sp == 1:                                   # the column
        for c_ in range(3):
            _box_geo(_cw, x, y, z + cbase + 1.6 + c_ * 3.0,
                     crown * 2 * (1.0 - 0.10 * c_), crown * 2 * (1.0 - 0.10 * c_),
                     3.2, h01(sd, c_, 233) * 1.57)
        _pyr_geo(_cw, x, y, z + cbase + 9.4, crown * 1.7, crown * 1.7,
                 max(1.4, ht - cbase - 9.4), h01(sd, 0, 239) * 1.57)
    else:                                           # the skirted cone
        for c_ in range(3):
            rr = crown * (1.0 - 0.22 * c_)
            _pyr_geo(_cw, x, y, z + cbase + c_ * (ht - cbase) * 0.26,
                     rr * 2, rr * 2, (ht - cbase) * 0.52, h01(sd, c_, 233) * 1.57)
    mesh(tag + "_trunk", _tk[0], _tk[1], M_TIMBER, "EMB_CONTEXT")
    mesh(tag + "_crown", _cw[0], _cw[1],
         M_LEAF_A if (h32(sd, 0, 241) % 3) == 0 else M_LEAF_G, "EMB_CONTEXT")
    VILLTREES.append((x, y, crown, cbase, sp, z))
    _vn[sp] += 1
    if wd - trr < _vworst_trunk:
        _vworst_trunk, _vworst_at = wd - trr, (x, y)
    if wd < crown + 1.0:
        _vover += 1                                 # this one's canopy is over a lane
        _vovercl.append(cbase)
    return True


# ---- SEARCH 0: THE SQUARE'S RING, which gets the ground before either of the others.
# The third consequence of the coexistence ruling is "more buildings AND TREES closing the
# ring around Festival Square", and the two halves do different jobs: a roof closes a
# sector at eye level, a broad crown closes the top of the frame from ground a house could
# never stand on (a tree needs 1.2 m off a lane where a household needs 4.6).  So the same
# annulus the ring households searched is swept again for trees, sector by sector, before
# the general searches can spend the ground on anything else.
_sqring = 0
if LM.get("square-plaza"):
    _sqp = LM["square-plaza"]
    _sqr0 = _sqp.get("extent", 14) + 4.0
    for _s in range(16):
        _hit = 0
        for _rad in (_sqr0, _sqr0 + 2.2, _sqr0 + 4.4, _sqr0 + 6.6, _sqr0 + 8.8):
            for _sw in (0.0, -0.16, 0.16, -0.32, 0.32, -0.46, 0.46):
                _ba = 2 * math.pi * _s / 16 + _sw
                _sd = h32(_s, int(_rad * 4), 269)
                # A CONIFER CLOSES THE SECTOR A STANDING EYE SEES; A BROAD CROWN CLOSES
                # THE FRAME ABOVE IT.  Which is offered first alternates on the sector's
                # own hash so the ring does not read as one planted species, and BOTH are
                # offered at every candidate: this annulus is the hardest ground in the
                # village to stand anything on (the plaza's own floor, six lanes leaving
                # it, the brook, the pond and four camera corridors all cross it), so a
                # sector that refuses a cone may still take a crown.
                for _sp in ((2, 0) if (h32(_s, 0, 271) % 2) else (0, 2)):
                    if vplant(_sqp["pos"][0] + _rad * math.cos(_ba),
                              _sqp["pos"][1] + _rad * math.sin(_ba), _sp, _sd):
                        _sqring += 1
                        _hit += 1
                        break
                if _hit >= 2:
                    break
            if _hit >= 2:
                break

# ---- SEARCH 1: THE VERGES.  The ruling says trees OVER THE LANES, and a grid scan
# delivers that only by luck: at a 3 m step, the band where a broadleaf's trunk clears
# the walk surface by 1.2 m and its crown still reaches the road is a metre or two wide,
# and the first build of this pass put exactly TWO trees over a lane out of 28.  So the
# verges are searched directly — walk each village lane, and every few metres try both
# sides at increasing offset, taking the FIRST that passes.  Conifers are excluded here
# by construction: their skirt is at head height and they keep the forest's full rule.
_vergen = 0
for _lk in sorted(LANEDRAW):
    _a2, _b2 = _lk.split("__")
    if _a2 in WOOD_IDS and _b2 in WOOD_IDS:
        continue
    _lp = resample(LANEDRAW[_lk], 3.0)
    for _li in range(1, len(_lp) - 1):
        _sd = h32(int(_lp[_li][0] * 8), int(_lp[_li][1] * 8), 251)
        if h01(_sd, 0, 253) > 0.58:
            continue

        _dx = _lp[_li + 1][0] - _lp[_li - 1][0]
        _dy = _lp[_li + 1][1] - _lp[_li - 1][1]
        _dl = math.hypot(_dx, _dy) or 1.0
        _nx, _ny = -_dy / _dl, _dx / _dl
        _sp = 0 if (h32(_sd, 0, 257) % 3) else 1
        _done = False
        for _side in ((1, -1) if (h32(_sd, 0, 259) % 2) else (-1, 1)):
            for _off in (3.0, 4.0, 5.0, 6.2, 7.6):
                if vplant(_lp[_li][0] + _nx * _side * _off,
                          _lp[_li][1] + _ny * _side * _off, _sp, _sd):
                    _vergen += 1
                    _done = True
                    break
            if _done:
                break

# ---- SEARCH 2: THE GROUND BETWEEN THE HOUSES, biggest species first.  With one pass
# over the grid accepting whatever species the cell's own hash drew, the broad crowns —
# which need three times the room of a birch — arrived to find the ground already taken
# by slimmer trees that had been luckier in the scan order: 15 tall slim, 6 conifers and
# TWO broad crowns, against a ruling that asks for a broadleaf canopy among the houses.
# Three passes, biggest first; the species per cell is still the cell's own hash.
for _vpass in (0, 2, 1):
  for _vj in range(_vgrid[1][0], _vgrid[1][1] + 1):
    for _vi in range(_vgrid[0][0], _vgrid[0][1] + 1):
        if h01(_vi, _vj, 217) > 0.88:
            continue                    # scattered, not planted in rows
        if h32(_vi, _vj, 223) % 3 != _vpass:
            continue
        _vx = _vi * VSTEP + (h01(_vi, _vj, 211) - 0.5) * 2.2
        _vy = _vj * VSTEP + (h01(_vi, _vj, 213) - 0.5) * 2.2
        # THE CONIFER KEEPS TO THE VILLAGE'S OUTER GROUND, and that is a measurement, not
        # a preference.  It is the one species whose skirt hangs at head height, so it is
        # also the one that hides the village FROM ITSELF: with conifers scattered through
        # the middle on the same terms as the broadleaves, the densification ruling's own
        # number — lane samples with 2+ background roofs in sight — fell from 75% to 62%
        # and Home Row to 46%, while the square's enclosure and the interleaving figures
        # did not move at all.  Held to the cool edges (>24 m from the warm districts'
        # landmarks, the same gradient the infill uses) it costs 66% instead, keeps all
        # three canopy shapes in the village, and puts the cones where the wood is
        # arriving anyway.  Where closing a view IS the job — the square's own ring, above
        # — the conifer is still offered first.
        if _vpass == 2 and d_to(WARMPTS, _vx, _vy) < 24.0:
            continue
        vplant(_vx, _vy, _vpass, h32(_vi, _vj, 263))
print("  veg_emb_village_*      %d VILLAGE TREES among the houses (%d broad crowns, %d "
      "tall slim, %d conifers) — refused: %d by the lane rule, %d in water, %d on "
      "massing or a garden plot, %d on a camera's sight line to its own subject, %d too "
      "close to another village tree, %d in the range's rock; %d were searched onto "
      "FESTIVAL SQUARE'S OWN RING to close it into a room, %d onto a LANE VERGE, the "
      "rest onto the ground between the houses"
      % (len(VILLTREES), _vn[0], _vn[1], _vn[2], _vrej["lane"], _vrej["water"],
         _vrej["massing"], _vrej["camera"], _vrej["crowded"], _vrej["rock"], _sqring,
         _vergen))

if VILLTREES:
    _cb = sorted(_vovercl)
    print("    over the lanes         %d of them stand close enough that their canopy "
          "OVERSAILS a walk surface — the forest's crown+1.0 m rule would have refused "
          "every one of those. The tightest TRUNK clears its lane by %.2f m at "
          "(%.1f, %.1f) against the 1.20 m rule; the lowest of those oversailing "
          "canopies has its underside %.2f m off its own ground, and a walker is 1.62 m"
          % (_vover, _vworst_trunk, _vworst_at[0], _vworst_at[1],
             _cb[0] if _cb else 0.0))
    assert _vworst_trunk >= 1.20, ("a village tree's trunk stands %.2f m from a walk "
                                   "surface at (%.1f, %.1f)"
                                   % (_vworst_trunk, *_vworst_at))
    assert not _cb or _cb[0] >= 3.60, ("a village canopy hangs at %.2f m over a lane"
                                       % _cb[0])
    # IS IT INTERLEAVED, OR IS IT ORNAMENTAL?  The ruling refuses to be settled by a
    # count — "nature interleaved, not ornamental" is a statement about what the ground
    # between the houses looks like — so it is asked as two distances, both measured on
    # the LANES, which is where the player is.  A tree 40 m away in a field is a tree in
    # a field; a canopy 6 m off the lane you are walking is the wood continuing through
    # the village.
    _lsamp = []
    for _k, _d in LANEDRAW.items():
        _a2, _b2 = _k.split("__")
        if _a2 in WOOD_IDS and _b2 in WOOD_IDS:
            continue
        _lsamp.extend(resample(_d, 3.0))
    if _lsamp:
        _near = sorted(min(math.hypot(p[0] - t[0], p[1] - t[1]) - t[2]
                           for t in VILLTREES) for p in _lsamp)
        _cnt = sorted(sum(1 for t in VILLTREES
                          if math.hypot(p[0] - t[0], p[1] - t[1]) <= 25.0)
                      for p in _lsamp)
        print("    interleaved or ornamental?  over %d village-lane samples: the nearest "
              "village canopy EDGE is %.1f m away (median), %.1f m at best and %.1f m at "
              "worst; %.0f%% of lane samples have one within 8 m and %.0f%% within 15 m; "
              "%d village trees within 25 m (median)"
              % (len(_lsamp), _near[len(_near) // 2], _near[0], _near[-1],
                 100.0 * sum(1 for d in _near if d <= 8.0) / len(_near),
                 100.0 * sum(1 for d in _near if d <= 15.0) / len(_near),
                 _cnt[len(_cnt) // 2]))


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
    # THE QUIET APPROACH IS WHISPERWOOD, NOT VILLAGE EDGE.  Village-side probability is
    # 0.30 at the anchor box and rises with distance outside it — which is right for the
    # ground between the lanes and wrong for the stretch the seclusion ruling is about,
    # because moving the gate north drags the anchor box up the approach with it and the
    # corridor would come out at village density: a lane across a thin coppice.  Inside
    # the corridor the wood is continuous and the road is a gap in it, exactly as it is
    # on the arrival road, tapering back to village density over the last 6 m of the band.
    # AND IT IS THE ARRIVAL'S FORMULA, NOT A MILDER ONE.  The first version multiplied
    # the corridor's density by the village-side clearance ramp (wd - 4)/4, which holds
    # the first trunk 8 m off the walk surface — a 16 m-wide avenue through a wood, and
    # the seclusion probe measured exactly what an avenue does: village solids in sight
    # from the approach went 15 at the warm end, down to 5 in the middle, and back UP to
    # 21 at the court, because oblique rays run the length of the clear verge.  On the
    # Whisperwood road the density is 1.0 and the ONLY thing holding a tree off the lane
    # is the crown gate (crown + 1.0 m), which is a fact about a body rather than a
    # composition choice.  The approach gets the same deal.
    _ad = approach_d(x, y)
    if _ad < SECL_R:
        return min(1.0, max(0.0, (SECL_R - _ad) / 6.0))
    if beyond_warmth(x, y):
        return 0.85                 # past the village's own end the valley is wood
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
nrej_gate = nrej_water = nrej_lm = nrej_rim = nrej_rock = nrej_vill = 0
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
        # A VILLAGE TREE IS AN INDIVIDUAL AND THE WOOD MAY NOT SWALLOW IT.  The same gate
        # the rim got in round 3, for the same reason: the pass that runs second has to
        # be told about the pass that ran first, or the ruling's "large individual trees"
        # end up standing inside a thicket that reads as one mass.
        if any(math.hypot(x - t[0], y - t[1]) < crown + t[2] + 0.2 for t in VILLTREES):
            nrej_vill += 1
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
        deep = y <= WOOD_Y1 or approach_d(x, y) < SECL_R or beyond_warmth(x, y)
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
      "%d by the lane gate, %d in water, %d on massing, %d on a rim tree, %d inside a "
      "village tree's own crown)"
      % (nwood, nbatch, FSTEP, nrej_gate, nrej_water, nrej_lm, nrej_rim, nrej_vill))

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

# ================================ NO UNCLAIMED ACRE — the field parcels ==
# USER RULING 2026-08-01 (map `forest._doc`, FARMLAND): *cleared land is welcome IF it is
# visibly CLAIMED for farming — the objection was never to open ground, it was to
# unclaimed emptiness between village and treeline.  Every acre is either forest or WORKED
# land: field strips with boundaries (hedges/stone rows/fences) ... reading as somebody's
# livelihood.  No ambiguous green voids.*
#
# THE RULING IS A PREDICATE BEFORE IT IS GEOMETRY, and that ordering is the whole design.
# "Worked land" cannot be judged from a screenshot of a gray town, so this pass opens by
# ASKING THE GROUND: sweep the valley at 1.5 m and call a cell UNCLAIMED when it is more
# than CLAIM (8 m) from every claimant the ruling recognises — forest, lane or floor,
# water, a household's plot, a real landmark, the range's own rock.  That number is
# printed BEFORE anything is built and again AFTER, and the target is zero.  A pass that
# only prints the after-number is a pass that cannot be wrong.
#
# THE PARCELS RUN WITH THE VALLEY, NOT WITH THE SCREEN.  The strip grid is laid in the
# frame of the line from the arrival portal to the Old Gate — the valley's own spine,
# derived from the map like everything else here, so a redline that moves either portal
# re-lays the fields instead of leaving them at a stale bearing.  Strips are 16 m along
# that spine by 9 m across: the long, narrow parcels of a valley farmed lengthwise.
#
# A BOUNDARY IS THE POINT, AND IT IS GATED PER SEGMENT.  What makes ground read as worked
# is the LINE round it, so each parcel draws its own boundary in one material — hedge,
# dry-stone row, or paling — and each segment is tested on its own against the lanes, the
# water, the trees, the households and the masonry.  A parcel whose neighbour is already a
# parcel does not draw the shared edge twice: a doubled hedge is a defect you only see in
# the audit.  Inside, crop ridges (or autumn stubble) run the length of the strip, broken
# wherever anything stands in the way, because a ridge that runs through a tree is worse
# than no ridge at all.
CLAIM = 8.0                             # the ruling's own reach, in metres
FIELD_RECTS = []                        # every parcel built, as an oriented rect

# the forest, as a distance field — the same chamfer WDIST uses, because "how far is the
# nearest tree" is asked ~40 000 times below and 1 900 hypots a sample is not a probe.
_TSEED = bytearray(ONX * ONY)
for (_fx, _fy, _fc) in FEET:
    _i, _j = int((_fx - X0) / OSTEP), int((_fy - Y0) / OSTEP)
    if 0 <= _i < ONX and 0 <= _j < ONY:
        _TSEED[_j * ONX + _i] = 1
for (_fx, _fy) in RIMFEET:
    _i, _j = int((_fx - X0) / OSTEP), int((_fy - Y0) / OSTEP)
    if 0 <= _i < ONX and 0 <= _j < ONY:
        _TSEED[_j * ONX + _i] = 1


def _chamfer(seed):
    INF = 1e6
    d = [0.0 if seed[k] else INF for k in range(ONX * ONY)]
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


TDIST = _chamfer(_TSEED)


def tdist(x, y):
    i, j = int((x - X0) / OSTEP), int((y - Y0) / OSTEP)
    if not (0 <= i < ONX and 0 <= j < ONY):
        return 1e6
    return TDIST[j * ONX + i]


def in_valley(x, y):
    """BETWEEN THE VILLAGE AND THE TREELINE — the ruling's own boundary, and it is a real
    one.  Inside the ground mesh, inside the wooded rim's INNER edge (past that you are in
    the wood, and a hedge out there would be a field in a forest), and on the village's
    side of the pinch: nobody farms the gorge behind a sealed gate."""
    if not (X0 + 3 < x < X1 - 3 and Y0 + 3 < y < Y1 - 3):
        return False
    if ((x - cx0) / (rx + RIMIN)) ** 2 + ((y - cy0) / (ry + RIMIN)) ** 2 > 1.0:
        return False
    if GATEFRAME and ((x - GX) * OUTX + (y - GY) * OUTY) > -1.0:
        return False
    # NOR DOES ANYBODY FARM THE SECLUDED APPROACH.  The farmland ruling's own words are
    # "every acre BETWEEN THE VILLAGE AND THE WOOD", and past the village's own end the
    # ground is not between them — it IS the wood.  A field strip with a hedge and a hay
    # stook laid along the quiet stretch would be somebody's livelihood standing exactly
    # where the seclusion ruling says there is nobody.
    if beyond_warmth(x, y) or in_approach(x, y):
        return False
    return True


def claimed_by(x, y, with_fields=True):
    """WHO claims this ground — the ruling's own list, in the order that answers most
    cheaply.  None means an ambiguous green void, which is the thing being counted."""
    if wdist(x, y) <= CLAIM:
        return "lane or floor"
    if tdist(x, y) <= CLAIM:
        return "forest"
    if in_water(x, y, CLAIM):
        return "water"
    for (px, py, pr) in INFILL_PLOTS:
        if math.hypot(x - px, y - py) <= pr + CLAIM:
            return "household"
    if lm_blocked(x, y, CLAIM) or in_seal(x, y, CLAIM):
        return "landmark or rock"
    if with_fields:
        for r in FIELD_RECTS:
            if in_rect(x, y, r, CLAIM):
                return "field parcel"
    return None


def sweep_unclaimed(with_fields):
    """The whole valley at 1.5 m, TWO questions per sample and they are not the same one.
      (1) UNCLAIMED — more than 8 m from every claimant.  The ruling's own test, and its
          target is zero.
      (2) BARE — nothing stands on this ground at all: no lane, no floor, no crown, no
          plot, no water, no masonry.  This is what the EYE calls a green void, and it is
          the number that decides where a field goes.  A cell 7 m from one tree passes
          test (1) and still renders as lawn, so a pass that only counted (1) would build
          one parcel and call the valley farmed.  It nearly did."""
    _un, _bare, _tot, _pts = 0, set(), 0, []
    _j = 0
    _y = Y0 + 3.0
    while _y < Y1 - 3.0:
        _i = 0
        _x = X0 + 3.0
        while _x < X1 - 3.0:
            if in_valley(_x, _y):
                _tot += 1
                if claimed_by(_x, _y, with_fields) is None:
                    _un += 1
                    _pts.append((_x, _y))
                if _fopen(_x, _y, 0.5) and not (with_fields and
                                                any(in_rect(_x, _y, r, 0.0)
                                                    for r in FIELD_RECTS)):
                    _bare.add((_i, _j))
            _i += 1
            _x += 1.5
        _j += 1
        _y += 1.5
    return _un, _bare, _tot, _pts


def bare_patches(cells):
    """THE NUMBER THAT ACTUALLY ANSWERS THE RULING, and the total area is not it.  900 m2
    of bare ground spread as two hundred slivers between hedges, tracks and cottages is
    TEXTURE; the same 900 m2 in one rectangle is the green void the user objected to.  The
    bare samples are 4-connected at 1.5 m and the answer is the size of the BIGGEST patch
    and how many are large enough to read as one (>= 40 m2, about a quarter of a strip)."""
    seen, out = set(), []
    for c in cells:
        if c in seen:
            continue
        stack, comp = [c], 0
        seen.add(c)
        while stack:
            (_i, _j) = stack.pop()
            comp += 1
            for (_di, _dj) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                _n = (_i + _di, _j + _dj)
                if _n in cells and _n not in seen:
                    seen.add(_n)
                    stack.append(_n)
        out.append(comp * 2.25)
    return sorted(out, reverse=True)

# the valley's spine, DERIVED: the arrival portal to the Old Gate
if GATEPOS and GATEFRAME:
    FANG = math.atan2(GY - GATEPOS[0][1], GX - GATEPOS[0][0])
else:
    FANG = math.pi / 2
FUX, FUY = math.cos(FANG), math.sin(FANG)               # along the valley
FVX, FVY = -FUY, FUX                                    # across it
FPU, FPV = 16.0, 9.0                                    # a strip: long with the valley


def _fpt(u, v):
    return (cx0 + FUX * u + FVX * v, cy0 + FUY * u + FVY * v)


def _fopen(x, y, half):
    """Can a piece of farm boundary or crop stand here?  Everything a parcel builds is
    tested with this — a field is the one thing in this file that fills the gaps BETWEEN
    the others, so it has to clear every one of them."""
    if not in_valley(x, y):
        return False
    if wdist(x, y) < half + 1.2 or in_water(x, y, 0.8):
        return False
    if lm_blocked(x, y, half + 0.6) or in_seal(x, y, 0.6):
        return False
    if tdist(x, y) < half + 2.4:                        # a crown's own room
        return False
    for (px, py, pr) in INFILL_PLOTS:
        if math.hypot(x - px, y - py) < pr + half + 0.9:
            return False
    if any(in_rect(x, y, r, half + 0.5) for r in INFILL_RECTS):
        return False
    # AND NOT ACROSS THE WAY TO SOMEBODY'S DOOR.  The first build of this pass laid four
    # boundary segments and crop ridges over infill CART TRACKS — 1.2 cm to 4.5 cm of
    # penetration, so shallow that only geometry_audit could see it, and a hedge across a
    # household's own track is exactly the kind of thing that reads as computer-generated.
    # The tracks are not walk surfaces, so `wdist` cannot see them; they are their own list.
    for (_ta, _tb, _tw) in INFILL_TRACKS:
        if seg_dist2(x, y, _ta[0], _ta[1], _tb[0], _tb[1]) < (_tw / 2 + half + 0.15) ** 2:
            return False
    if any(math.hypot(x - r[0], y - r[1]) < half + 3.4 for r in VISTAROOFS):
        return False
    if any(math.hypot(x - f[0], y - f[1]) < half + 1.6 for f in LAMPFEET):
        return False
    if MILLPOND and math.hypot(x - MILLPOND[0], y - MILLPOND[1]) < MILLPOND_R + half + 1.6:
        return False
    return True


UNCLAIMED_BEFORE, BARE_BEFORE, SWEPT, UNPTS = sweep_unclaimed(False)
print("  THE ACRES, BEFORE      %d valley samples at 1.5 m between the village and the "
      "treeline (%d m2):" % (SWEPT, int(SWEPT * 2.25)))
print("      UNCLAIMED (>%.0f m from forest, lane, floor, water, household, landmark)  "
      "%d samples, %d m2" % (CLAIM, UNCLAIMED_BEFORE, int(UNCLAIMED_BEFORE * 2.25)))
_PB = bare_patches(BARE_BEFORE)
print("      BARE (nothing standing on it at all — what the eye calls a green void)  "
      "%d samples, %d m2 (%.0f%% of the valley floor) in %d patches, biggest %.0f m2, "
      "%d of them >= 40 m2"
      % (len(BARE_BEFORE), int(len(BARE_BEFORE) * 2.25),
         100.0 * len(BARE_BEFORE) / max(SWEPT, 1), len(_PB), _PB[0] if _PB else 0.0,
         sum(1 for v in _PB if v >= 40.0)))

# PASS 1 — WHICH CELLS ARE PARCELS.  A cell becomes a parcel when it contains ground the
# sweep called unclaimed AND enough open ground to be worth a boundary.  Deciding the
# whole set first is what lets a shared edge be drawn once.
_ur = int(math.ceil((abs(X1 - X0) + abs(Y1 - Y0)) / FPU)) + 2
_vr = int(math.ceil((abs(X1 - X0) + abs(Y1 - Y0)) / FPV)) + 2
FCELLS = {}
for _iu in range(-_ur, _ur + 1):
    for _iv in range(-_vr, _vr + 1):
        _cu, _cv = (_iu + 0.5) * FPU, (_iv + 0.5) * FPV
        _cx, _cy = _fpt(_cu, _cv)
        if not in_valley(_cx, _cy):
            continue
        _nop = _nun = _ns = 0
        _du = -FPU / 2 + 1.0
        while _du < FPU / 2:
            _dv = -FPV / 2 + 1.0
            while _dv < FPV / 2:
                _sx, _sy = _fpt(_cu + _du, _cv + _dv)
                _ns += 1
                if _fopen(_sx, _sy, 0.5):
                    _nop += 1
                    if claimed_by(_sx, _sy, False) is None:
                        _nun += 1
                _dv += 1.5
            _du += 1.5
        # THE TRIGGER IS BARE GROUND, NOT THE 8 m TEST.  A strip that is a third open is
        # a strip somebody would have ploughed; requiring an >8 m void in it built ONE
        # parcel in the whole valley and left every lawn between the households bare.
        if _ns and (_nop / float(_ns) >= 0.22 or _nop >= 6 or (_nun >= 1 and _nop >= 3)):
            FCELLS[(_iu, _iv)] = (_cu, _cv, _cx, _cy)

# PASS 2 — RAISE THEM.  A parcel that builds NOTHING (every segment and every ridge
# refused by something standing in the strip) must not be counted and must not go in
# FIELD_RECTS: the after-sweep tests ground against those rects, so an empty parcel would
# claim its acre in the report and show the player bare grass.  Two of the first eighteen
# were exactly that.
nfield = nbound = nridge = nempty = 0
for (_iu, _iv) in sorted(FCELLS):
    _cu, _cv, _cx, _cy = FCELLS[(_iu, _iv)]
    _made = []
    tag = "lm_field_%02d" % nfield
    salt = h32(_iu, _iv, 181)
    kind = salt % 3                                     # 0 hedge, 1 dry-stone, 2 paling
    # the four edges, the two "low" ones always and the two "high" ones only where the
    # neighbour is not a parcel — one boundary between two fields, never two
    edges = [(-FPV / 2, 1), (-FPU / 2, 0)]
    if (_iu, _iv + 1) not in FCELLS:
        edges.append((FPV / 2, 1))
    if (_iu + 1, _iv) not in FCELLS:
        edges.append((FPU / 2, 0))
    for (_off, _along) in edges:
        _L = FPU if _along else FPV
        _n = int(_L / 2.5)
        for _k in range(_n):
            _t = -_L / 2 + _L * (_k + 0.5) / _n
            _u, _v = (_cu + _t, _cv + _off) if _along else (_cu + _off, _cv + _t)
            _bx, _by = _fpt(_u, _v)
            if not _fopen(_bx, _by, 1.1):
                continue
            _bz = ground_z(_bx, _by)
            _rz = FANG if _along else FANG + math.pi / 2
            if kind == 0:
                _made.append((box, ("%s_hedge%02d", _bx, _by, _bz + 0.44,
                                    2.9, 0.75, 0.88, M_LEAF_G, _rz), 1))
            elif kind == 1:
                _made.append((box, ("%s_drystone%02d", _bx, _by, _bz + 0.31,
                                    2.9, 0.50, 0.62, M_STONE, _rz), 1))
            else:
                _made.append((box, ("%s_pale%02d", _bx, _by, _bz + 0.50,
                                    2.9, 0.10, 1.00, M_TIMBER, _rz), 1))
    # A BOUNDARY IS A LINE, NOT A ROW OF DASHES.  The segments are 2.9 m long at 2.5 m
    # centres, so a run of them OVERLAPS by 40 cm and reads as one wall; the first build
    # laid 2.2 m segments at 2.4 m and the review frame showed a field boundary as a
    # dotted line of loose stones.  The overlap is why `_drystone` and `_ridge` joined
    # geometry_audit's SOFT_PART, exactly as `_hedge` and `_pale` did in round 2.
    # THE CROP, AS RIDGES.  Three runs the length of the strip at 0.22 m — enough to read
    # as ploughed ground in a plan or a wide shot, and broken wherever anything stands in
    # the way.  Stubble (thatch) or green rows, by the parcel's own hash: the map's autumn.
    _cropm = M_THATCH if (salt % 5) < 2 else M_LEAF_G
    for _r in range(3):
        _v = _cv + (_r - 1) * (FPV / 4.0)
        _du = -FPU / 2 + 1.6
        while _du < FPU / 2 - 1.2:
            _rx, _ry = _fpt(_cu + _du, _v)
            if _fopen(_rx, _ry, 1.4):
                _made.append((box, ("%s_ridge%02d", _rx, _ry, ground_z(_rx, _ry) + 0.11,
                                    3.0, 1.1, 0.22, _cropm, FANG), 2))
            _du += 3.2
    # a hay stook on every third parcel, standing where the ridges leave room
    if (salt % 3) == 0:
        _sx, _sy = _fpt(_cu + FPU / 2 - 2.6, _cv + FPV / 2 - 2.2)
        if _fopen(_sx, _sy, 1.5):
            _made.append((pyramid, ("%s_stook", _sx, _sy, ground_z(_sx, _sy),
                                    2.0, 2.0, 2.2, M_THATCH,
                                    h01(salt, 0, 191) * 1.57), 3))
    if len(_made) < 2:
        nempty += 1                     # nothing could stand here: not a parcel, not a claim
        continue
    for (_fn, _ar, _cls) in _made:
        if _cls == 1:
            _nm, _px, _py, _pz, _sx2, _sy2, _sz2, _mm, _rz2 = _ar
            box(_nm % (tag, nbound % 100), _px, _py, _pz, _sx2, _sy2, _sz2, _mm,
                "EMB_MASSING", _rz2)
            nbound += 1
        elif _cls == 2:
            _nm, _px, _py, _pz, _sx2, _sy2, _sz2, _mm, _rz2 = _ar
            box(_nm % (tag, nridge % 100), _px, _py, _pz, _sx2, _sy2, _sz2, _mm,
                "EMB_MASSING", _rz2)
            nridge += 1
        else:
            _nm, _px, _py, _pz, _sx2, _sy2, _hh, _mm, _rz2 = _ar
            pyramid(_nm % tag, _px, _py, _pz, _sx2, _sy2, _hh, _mm, "EMB_MASSING", _rz2)
    FIELD_RECTS.append((_cx, _cy, FPU / 2, FPV / 2, FANG))
    nfield += 1

print("  lm_field_*             %d WORKED PARCELS over the open ground (%.0f x %.0f m "
      "strips on the valley's own spine, %.0f deg): %d boundary segments (hedge / "
      "dry-stone / paling, one per shared edge) and %d crop ridges; %d candidate strips "
      "built nothing (something stood in every metre of them) and are NOT counted as "
      "claimed" % (nfield, FPU, FPV, math.degrees(FANG) % 180.0, nbound, nridge, nempty))
UNCLAIMED_AFTER, BARE_AFTER, _sw2, UNPTS2 = sweep_unclaimed(True)
print("  THE ACRES, AFTER       UNCLAIMED %d samples (%d m2) — the ruling's target is 0"
      % (UNCLAIMED_AFTER, int(UNCLAIMED_AFTER * 2.25)))
_PA = bare_patches(BARE_AFTER)
print("      BARE ground left OUTSIDE every field parcel  %d m2 (was %d m2) in %d patches, "
      "biggest %.0f m2 (was %.0f m2), %d of them >= 40 m2 (was %d) — %.0f%% of the bare "
      "ground is now inside a worked parcel"
      % (int(len(BARE_AFTER) * 2.25), int(len(BARE_BEFORE) * 2.25), len(_PA),
         _PA[0] if _PA else 0.0, _PB[0] if _PB else 0.0,
         sum(1 for v in _PA if v >= 40.0), sum(1 for v in _PB if v >= 40.0),
         100.0 * (1.0 - len(BARE_AFTER) / float(max(len(BARE_BEFORE), 1)))))
if UNPTS2:
    print("      still unclaimed, worst: " + "; ".join("(%.0f, %.0f)" % p for p in UNPTS2[:6]))

# ------------------- DOES THE FOREST REACH THE VILLAGE EDGE? (container ruling) -------
# The round-2 ruling says the wood is the village's CONTAINER — it *presses in around and
# between the outer houses* — and the round-2 report asserted that it did without ever
# measuring it at the boundary.  So: 36 rays out of the town's own centre.  On each, the
# LAST walk surface crossed is the village edge in that direction and the FIRST tree past
# it is the wood; the gap between the two is the number the ruling is about.  Where a ray
# leaves over the river the wood is SUPPOSED to open, so those rays are counted apart
# rather than averaged in — and whatever fills a gap is named, because after the farmland
# pass "8 m of worked field" and "8 m of nothing" are different answers.
_edge_gaps, _edge_open, _river_rays, _built_gaps, _bare_m = [], [], 0, [], 0.0
for _k in range(36):
    _a = 2 * math.pi * _k / 36.0
    _cs, _sn = math.cos(_a), math.sin(_a)
    _rmax = 0.0
    _r = 1.0
    _rw = _rb = None
    while _r < 200.0:
        _px, _py = cx0 + _r * _cs, cy0 + _r * _sn
        if not (X0 + 2 < _px < X1 - 2 and Y0 + 2 < _py < Y1 - 2):
            break
        _rmax = _r
        if occupied(_px, _py):
            _rw = _r
        # the outermost thing anybody BUILT on this bearing — a household's plot, a
        # landmark, a field's own boundary.  "The wood presses in around the outer houses"
        # is a statement about that edge, not about the last walk surface.
        if (any(math.hypot(_px - _p[0], _py - _p[1]) <= _p[2] + 1.0 for _p in INFILL_PLOTS)
                or lm_blocked(_px, _py, 1.0)
                or any(in_rect(_px, _py, _fr, 0.0) for _fr in FIELD_RECTS)):
            _rb = _r
        _r += 0.5
    if _rw is None:
        continue
    if _rb is not None and _rb > _rw:
        _rw_built = _rb
    else:
        _rw_built = _rw
    # A TREE IS REACHED WHEN THE RAY ENTERS ITS CROWN, not when it hits the trunk.  The
    # first version tested `tdist <= 1.0` — within a metre of a stem — and a ray can slip
    # between 2.75 m-spaced trunks for tens of metres, so it reported 34 m of "gap" on
    # bearings that run through standing wood.  Crowns are 2.0-3.1 m of radius; 3.0 m is
    # the honest threshold and it is the same number the forest's own gate uses.
    _r, _rt = _rw, None
    while _r < _rmax:
        _px, _py = cx0 + _r * _cs, cy0 + _r * _sn
        if tdist(_px, _py) <= 3.0:
            _rt = _r
            break
        _r += 0.5
    if _rt is None:
        _edge_open.append(("no wood on this bearing", math.degrees(_a), _rmax - _rw))
        continue
    _mx, _my = cx0 + (_rw + _rt) / 2 * _cs, cy0 + (_rw + _rt) / 2 * _sn
    _who = claimed_by(_mx, _my, True)
    if in_water(_mx, _my, 0.0):
        _river_rays += 1
    _rr = _rw
    while _rr < _rt:
        if _fopen(cx0 + _rr * _cs, cy0 + _rr * _sn, 0.5):
            _bare_m += 0.5
        _rr += 0.5
    _edge_gaps.append((_rt - _rw, math.degrees(_a), _who))
    _built_gaps.append(max(0.0, _rt - _rw_built))
if _edge_gaps:
    _g = sorted(g[0] for g in _edge_gaps)
    _gb = sorted(_built_gaps)
    _worst = max(_edge_gaps)
    _tot_gap = sum(g[0] for g in _edge_gaps)
    print("  THE VILLAGE EDGE       %d bearings out of the town's centre; on each, the "
          "last walk surface, the outermost thing anybody built, and the first tree crown:"
          % len(_edge_gaps))
    print("      last WALK surface  -> the wood   median %.1f m, worst %.1f m at %.0f deg "
          "(the ground between is claimed by: %s)"
          % (_g[len(_g) // 2], _worst[0], _worst[1], _worst[2]))
    print("      outermost BUILT thing -> the wood   median %.1f m, worst %.1f m — this "
          "is the container ruling's own number: the wood presses in around the outer "
          "houses" % (_gb[len(_gb) // 2], _gb[-1]))
    print("      of %.0f m of ray between the walk edge and the wood, %.0f m is BARE "
          "ground (%.0f%%); %d bearings leave over the water, where the wood is meant to "
          "open; %d bearings' gap is UNCLAIMED"
          % (_tot_gap, _bare_m, 100.0 * _bare_m / max(_tot_gap, 1.0), _river_rays,
             sum(1 for g in _edge_gaps if g[2] is None)))
    if _edge_open:
        print("      bearings with NO wood beyond the village at all: %d — %s"
              % (len(_edge_open), "; ".join("%.0f deg" % o[1] for o in _edge_open)))

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
WET_BY = {}                     # landmark id -> {water mesh name: cells cut for it}
CURWATER = "?"                  # which body `water_field` is rasterising right now


def dry_footprint(x, y):
    for o in D["landmarks"]:
        if o.get("class") in ("area", "dressing") or bodysize(o)[0] <= 0:
            continue
        if math.hypot(o["pos"][0] - x, o["pos"][1] - y) > 9.0:
            continue
        if in_rect(x, y, foot_rect(o), 0.35):
            if o["id"] not in WET_MASSING:
                WET_MASSING.append(o["id"])
            # WHICH water it was is the whole question, and only this loop knows: by the
            # time the report runs, these cells have been CUT and counting them off the
            # built mesh finds nothing (it did).  Attribute at cut time.
            WET_BY.setdefault(o["id"], {})
            WET_BY[o["id"]][CURWATER] = WET_BY[o["id"]].get(CURWATER, 0) + 1
            return True
    for (rx_, ry_, _rz) in INFILL_ROOFS:
        if math.hypot(rx_ - x, ry_ - y) < 3.6:
            return True
    return False


def water_field(name, inside_fn, level_fn, x0, x1, y0, y1, cut=True):
    global CURWATER
    CURWATER = name.replace("water_emb_", "")
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
    print("    NOTE  %s have water cells inside their own footprint — the water is cut "
          "around them so nothing renders standing in a pond, but WHICH water it is "
          "decides whether that is a map question at all (see below)"
          % ", ".join(sorted(WET_MASSING)))

    # ROUND 2 LEFT THIS AS A QUESTION WITH NO NUMBER ON IT, which is why it is still open:
    # "a building stands in the water" is an observation, and what the coordinator needs to
    # stamp is a MAP LINE.  So the overlap is measured against the footprint the build
    # actually raises (not the landmark's point), and both of the only two fixes are
    # costed in metres: move the landmark, or shrink the extent.  Whichever the
    # coordinator picks, the number is here to check it against.
    def _rect_dist(px, py, rect):
        _cx, _cy, _hw, _hd, _rz = rect
        _c, _s = math.cos(-_rz), math.sin(-_rz)
        _dx, _dy = px - _cx, py - _cy
        _lx = abs(_dx * _c - _dy * _s) - _hw
        _ly = abs(_dx * _s + _dy * _c) - _hd
        return math.hypot(max(_lx, 0.0), max(_ly, 0.0))

    # AND WHICH WATER IT IS, BECAUSE ROUND 2's NOTE CONFLATED FOUR DIFFERENT THINGS.
    # "Stands inside an authored water extent" is only true of the disc-shaped ones the
    # MAP authors.  The brook is a course this file smooths, the millpond is an
    # impoundment this file DERIVES from the wheel ruling, and a watermill standing in
    # its own leat is not a defect — it is a watermill.  Only an authored extent can be
    # answered with "move the landmark or shrink the extent"; the rest get their own
    # sentence, so the coordinator is never asked to stamp a fix for a non-problem.
    # The attribution is COUNTED off the built water meshes, not inferred from a
    # centre-to-centre distance, because that is the same guess that produced the note.
    for _wid in sorted(WET_MASSING):
        _o = LM[_wid]
        _fr = foot_rect(_o)
        for (_src, _n) in sorted(WET_BY.get(_wid, {}).items(), key=lambda kv: -kv[1]):
            if _src in WATER_LM:
                _wl = LM[_src]
                _wr = _wl.get("extent", 5)
                _d = _rect_dist(_wl["pos"][0], _wl["pos"][1], _fr)
                print("      %-11s x %-9s AUTHORED EXTENT — %d cells cut out of a "
                      "%.1f x %.1f m footprint at (%.2f, %.2f); the rim reaches %.2f m "
                      "INTO it (nearest face %.2f m from the extent's centre, r%.1f)"
                      % (_wid, _src, _n, _fr[2] * 2, _fr[3] * 2, _o["pos"][0],
                         _o["pos"][1], _wr - _d, _d, _wr))
                _ax, _ay = _o["pos"][0] - _wl["pos"][0], _o["pos"][1] - _wl["pos"][1]
                _al = math.hypot(_ax, _ay) or 1.0
                _need = _wr + 0.5 - _d
                print("        MAP LINE A  move %s %.2f m out along its own bearing from "
                      "%s -> (%.2f, %.2f), leaving 0.50 m of dry shore"
                      % (_wid, _need, _src, _o["pos"][0] + _ax / _al * _need,
                         _o["pos"][1] + _ay / _al * _need))
                print("        MAP LINE B  shrink %s's extent %.2f m, r%.1f -> r%.2f, and "
                      "leave %s where the builder searched it"
                      % (_src, _wr - (_d - 0.5), _wr, _d - 0.5, _wid))
            elif _src == "brook":
                print("      %-11s x brook     NOT AN AUTHORED EXTENT — %d cells of the "
                      "smoothed brook course fell in its footprint, and this landmark "
                      "SNAPS to that course by canon. A mill or a weir that does not "
                      "touch its own water is the defect; nothing to stamp."
                      % (_wid, _n))
            elif _src == "millpond":
                print("      %-11s x millpond  NOT AUTHORED AT ALL — %d cells of the "
                      "impoundment this build DERIVES (r%.2f, the head the 2.00 m dam "
                      "ruling buys). The pound is the mill's own; nothing to stamp."
                      % (_wid, _n, MILLPOND_R))
            else:
                print("      %-11s x %-9s %d cells cut from its footprint"
                      % (_wid, _src, _n))

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

# ------------------------------------------------------- THE SEAL, MEASURED --------
# Round 2 reported the bottleneck's failure in the only currency that matters — "32 m of
# walkable ground around the pinch" — and then had no instrument that could say when it
# was fixed.  Three now, in increasing strictness, because a seal that only holds ON the
# line is not a seal:
#
#  1  THE STRIP.  Metres of the pinch line that are neither masonry, nor rock, nor water,
#     nor off the ground mesh — reported per flank, because the number this round exists
#     to drive to zero is the one BETWEEN THE MASONRY AND THE WATER.
#  2  THE WALK NETWORK.  The furthest any walk vertex in the town reaches out of the
#     valley.  It must be SOUTH of the pinch line: the court's own r10 floor lapped
#     1.3 m past the gate before the curtain walls cut it.
#  3  THE FLOOD FILL, which is the only one that can catch a way ROUND.  Open ground is
#     4-connected at 0.5 m; the fill starts on the gate court and may not reach a single
#     cell past the pinch line.  A chain that seals the line and stops 40 m short of the
#     map's edge fails this and passes the other two.
if GATEFRAME:
    _reach = max((_c[2] + _c[3] for _c in CHAIN), default=40.0)

    def _blocked(a, b):
        _x, _y = _pt(a, b)
        for _r in SEALMAS:
            if in_rect(_x, _y, _r):
                return True
        for _r in BLUFFS:
            if in_rect(_x, _y, _r):
                return True
        if not _onmesh(a, b):
            return True                                 # the world ends; you cannot walk off it
        return _wet(a, b)

    _SS = 0.05
    _openm = [0.0, 0.0]
    _widest = 0.0
    _run = 0.0
    _runs = []
    _a = -_reach
    while _a <= _reach:
        if _blocked(_a, 0.0):
            if _run > 0.5:
                _e0, _e1 = sorted((abs(_a - _run), abs(_a)))
                _runs.append(("east" if _a < 0 else "west", _e0, _e1))
            _widest = max(_widest, _run)
            _run = 0.0
        else:
            _openm[0 if _a < 0 else 1] += _SS
            _run += _SS
        _a += _SS
    # the round's own number: dry, un-rocked ground between the gate's masonry and what
    # it is sealed against, one flank at a time
    _flank = {}
    for _sgn, _nm in ((1, "east (to the water)"), (-1, "west (to the rock)")):
        _m, _a = 0.0, GATE_HALF
        while _a < _reach and not _blocked(_sgn * _a, 0.0):
            _m += _SS
            _a += _SS
        _flank[_nm] = _m
    print("  THE SEAL, MEASURED")
    print("    [1] walkable strip between the masonry and the water   %.2f m"
          % _flank["east (to the water)"])
    print("        walkable strip between the masonry and the rock    %.2f m"
          % _flank["west (to the rock)"])
    print("        open ground anywhere on the pinch line, over its whole %.0f m run: "
          "%.2f m west + %.2f m east, widest single gap %.2f m"
          % (2 * _reach, _openm[0], _openm[1], _widest))
    assert _flank["east (to the water)"] < 0.01 and _flank["west (to the rock)"] < 0.01, (
        "the pinch is not sealed: %.2f m east of the masonry, %.2f m west"
        % (_flank["east (to the water)"], _flank["west (to the rock)"]))
    # THE LINE IS NOT THE GATE, AND SAYING SO IS THE POINT.  The chains stand on the
    # pinch line for their first three masses and then RAKE back out of the valley, so
    # the line itself reopens 40-odd metres out — into ground that the raked band above
    # it still closes.  A straight wall from map edge to map edge would zero this number
    # and would be the "blank grey slab" round 2 was told off for.  What must be zero is
    # the strip beside the masonry (asserted above) and the ability to WALK round it
    # (asserted below); this run-list is the diagnostic in between.
    if _runs:
        print("        the line reopens outside the chains' first three masses: %s"
              % "; ".join("%s %.0f-%.0f m out" % _r for _r in _runs))

    _wb, _wbn = -1e9, "-"
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith("walk_"):
            continue
        for v in o.data.vertices:
            wv = o.matrix_world @ v.co
            _p = (wv.x - GX) * OUTX + (wv.y - GY) * OUTY
            if _p > _wb:
                _wb, _wbn = _p, o.name
    print("    [2] the walk network stops %.2f m SHORT of the pinch line (%s)"
          % (-_wb, _wbn))
    assert _wb < 0.0, "a walk surface (%s) stands %.2f m past the pinch line" % (_wbn, _wb)

    _FS = 0.5
    _a0, _a1 = -_reach - 4.0, _reach + 4.0
    _b0, _b1 = -26.0, 44.0
    _NA = int((_a1 - _a0) / _FS) + 1
    _NB = int((_b1 - _b0) / _FS) + 1
    _open = bytearray(_NA * _NB)
    for _j in range(_NB):
        for _i in range(_NA):
            if not _blocked(_a0 + _i * _FS, _b0 + _j * _FS):
                _open[_j * _NA + _i] = 1
    _si = int((0.0 - _a0) / _FS)
    _sj = int(((POS["gate-court"][1] - GY) * OUTY
               + (POS["gate-court"][0] - GX) * OUTX - _b0) / _FS)
    assert _open[_sj * _NA + _si], ("the flood fill's own seed (the gate court) is "
                                    "blocked — the probe would pass by measuring nothing")
    _seen = bytearray(_NA * _NB)
    _stack = [(_si, _sj)]
    _seen[_sj * _NA + _si] = 1
    _nreach = _past = _gorge = 0
    _maxb = -1e9
    # THE GORGE IS WHAT MUST BE UNREACHABLE, not "any ground past the line", and the
    # difference is the whole shape of the range.  The chains stand on the pinch line for
    # three masses and then rake back out of the valley, which leaves a rocky CUL-DE-SAC
    # behind their shoulders at the far end — ground north of the line that the valley can
    # walk into and cannot walk out of.  That is a broken shoulder, not a bypass.  The
    # ruling's own words are "no way around it", so the assertion is on the road the gate
    # exists to close: the gorge floor directly behind the structure, out to 20 m.
    _GA = max(AROCK_D, AROCK_C) + 12.0
    while _stack:
        _i, _j = _stack.pop()
        _nreach += 1
        _bb = _b0 + _j * _FS
        _aa = _a0 + _i * _FS
        if _bb > 0.0:
            _past += 1
            _maxb = max(_maxb, _bb)
            if abs(_aa) <= _GA and WB1 + 1.0 <= _bb <= WB1 + 21.0:
                _gorge += 1
        for _di, _dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _ni, _nj = _i + _di, _j + _dj
            if 0 <= _ni < _NA and 0 <= _nj < _NB:
                _k = _nj * _NA + _ni
                if _open[_k] and not _seen[_k]:
                    _seen[_k] = 1
                    _stack.append((_ni, _nj))
    print("    [3] flood fill from the gate court over %d m2 of open ground: %d m2 of "
          "the GORGE behind the gate is reachable (must be 0)"
          % (int(_nreach * _FS * _FS), int(_gorge * _FS * _FS)))
    if _past:
        print("        %d m2 of dead-end ground behind the range's raked shoulders IS "
              "reachable, furthest %.1f m past the line — a cul-de-sac in the rock, not "
              "a bypass; it carries no walk surface" % (int(_past * _FS * _FS), _maxb))
    assert _gorge == 0, ("%d m2 of the gorge behind the Old Gate is reachable from the "
                         "gate court — there is a way ROUND it" % int(_gorge * _FS * _FS))

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
    # THE NORTH HORIZON, ASKED SEPARATELY.  Mini-round 2b evicted 21 infill households
    # that stood past the pinch, and the town-wide 2+ rate fell 84% -> 73% — but a
    # town-wide average cannot say WHERE it thinned, and the households that went were all
    # at one end.  So every sample is tagged with its lane's own districts and the Gate
    # Field's lanes (the barn, the court, the washline green) get their own number.  If
    # the north reads thin it is a redline about the gatefield, not about the town.
    _bydist = {}
    _samples = [(k, p) for (k, p) in _samples]
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
        _a2, _b2 = _key.split("__")
        for _dd in {LM.get(_a2, {}).get("district", "?"),
                    LM.get(_b2, {}).get("district", "?")}:
            _bydist.setdefault(_dd, []).append(n35)
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
    print("      BY DISTRICT (a town-wide average cannot say where it thinned):")
    for _dd in sorted(_bydist, key=lambda k: -len(_bydist[k])):
        _vv = sorted(_bydist[_dd])
        print("        %-10s %3d samples   median %d within 35 m   %3.0f%% meet 2+"
              % (_dd, len(_vv), _vv[len(_vv) // 2],
                 100.0 * sum(1 for c in _vv if c >= 2) / len(_vv)))
    _nh = _bydist.get("gatefield", [])
    if _nh:
        _nhs = sorted(_nh)
        print("      THE NORTH HORIZON (the Gate Field's own lanes — barn, court, "
              "washline green): %d samples, median %d roofs within 35 m, %.0f%% meet 2+"
              % (len(_nhs), _nhs[len(_nhs) // 2],
                 100.0 * sum(1 for c in _nhs if c >= 2) / len(_nhs)))

# ---- PROBE 4: DOES THE TOWN FALL OUT OF SIGHT ON THE WAY TO THE GATE? --------------
# The seclusion ruling is a sequence of PLAYER EXPERIENCES — warmth ends, roofs go, the
# wood closes, then the gate — and only the second of those can be settled with a ray.
# So it is: walk the approach from the town's last warmth to the court at a walker's eye
# and count how many of the village's own solids still have a sight line, step by step.
# The number the ruling asks for is THE THRESHOLD: the distance from the warm end past
# which the count is zero and STAYS zero.  A count that touches zero and comes back is a
# gap between two trees, not a threshold, so the search runs from the far end backwards.
#
# THE SAME THREE TRAPS THE ARRIVAL PROBE FELL INTO ARE AVOIDED THE SAME WAY (round 2):
# targets come off built objects' world bounds and never off a landmark's z + a guess;
# three aim points per solid at the eaves and the shoulder, never the ridge; and the
# village list excludes NOTHING that stands in the village, including the barn and the
# dovecote whose own roofs are the last thing that ought to disappear.
if SECL and len(SECL) > 1:
    _apts = resample(SECL, 2.0)
    # WHAT COUNTS AS "THE VILLAGE" HERE WAS WRONG, AND THE FRAME CAUGHT IT — round 2's
    # lesson arriving a third time, and the most expensive kind: a probe that fails
    # CLOSED.  The first version excluded every landmark in the `gatefield` DISTRICT,
    # which is not the gate — it is the gate AND the tithe barn AND the dovecote AND the
    # closed back lane.  So the report printed "the barn and the dovecote are IN this
    # count" while the code had excluded them by name, the profile read 0 at the
    # threshold, and the review render of that exact spot showed the barn, the dovecote
    # and two roofs past them.  A number that disagrees with its own frame is the number
    # that is wrong.  The exclusion is now DERIVED and means what it says: only things
    # standing on the GATE's side of the approach's start — the gate, its court, the
    # stile, the downstream vista — are excluded, because those are what you are walking
    # TOWARD.  Everything the town built is in.
    _town = [(o.name, _surface_pts(o)) for o in bpy.data.objects
             if o.type == 'MESH' and o.name.startswith("lm_")
             and o.name.endswith(("_roof", "_body", "_shedroof"))
             and not beyond_warmth((o.matrix_world @ Vec(o.bound_box[0])).x,
                                   (o.matrix_world @ Vec(o.bound_box[0])).y)]
    # THE BARNYARD IS NOT THE VILLAGE.  The barn and the dovecote are the town's last
    # warmth by the ruling's own words, so their roofs being in sight as you walk away
    # from them is the shift WORKING, not failing; counted in with the rest they hold the
    # first 15 m of the profile at 5-7 and hide the shape of everything after it.  Both
    # counts are kept: everything built, and everything more than 25 m from the warm end,
    # which is what "village roofs" means here.
    _wx, _wy, _wz = POS[SECL_WARM]
    _far = [(n_, p_) for (n_, p_) in _town
            if math.hypot(p_[0][0] - _wx, p_[0][1] - _wy) > 25.0]
    _prof = []
    _run = 0.0
    for _i, _p in enumerate(_apts):
        if _i:
            _run += math.hypot(_p[0] - _apts[_i - 1][0], _p[1] - _apts[_i - 1][1])
        _ez = _p[2] + EYE
        _n = _nf = 0
        _who = None
        for (_vn2, _vps) in _town:
            if any(_sees(_p[0], _p[1], _ez, *_t, margin=0.9) for _t in _vps):
                _n += 1
                if math.hypot(_vps[0][0] - _wx, _vps[0][1] - _wy) > 25.0:
                    _nf += 1
                if _who is None:
                    _who = _vn2
        _prof.append((_run, _n, _who, _nf))
    # TWO THRESHOLDS, BECAUSE ONE NEEDLE IS NOT A VIEW.  Round 2's arrival probe earned
    # this the hard way in the other direction: through 1 700 scattered trees there is
    # nearly always SOME ray between two trunks, so a strict "count is zero and stays
    # zero" line is reset by a single roof sliver at 86 m and reports 2 m of seclusion on
    # a stretch that is empty for 25.  Both are printed: the strict line, and the line
    # past which no more than one solid is ever in sight at once.  The share of the
    # approach standing at zero is the number that describes the walk.
    def _last_above(n, ix):
        for _k in range(len(_prof) - 1, -1, -1):
            if _prof[_k][ix] > n:
                return _prof[_k][0] if _k + 1 < len(_prof) else None
        return 0.0
    _thr = _last_above(0, 3)
    _first0 = next((_r[0] for _r in _prof if _r[3] == 0), None)
    _after = [_r for _r in _prof if _first0 is not None and _r[0] >= _first0]
    _zero = 100.0 * sum(1 for _r in _after if _r[3] == 0) / max(1, len(_after))
    _peak = max((_r[3] for _r in _after), default=0)
    print("  THE SECLUSION, MEASURED  %d samples over %.1f m of quiet approach from %s "
          "to %s, eye at %.2f m, against %d built village solids (only the gate, its "
          "court, the stile and the downstream vista are excluded, because those are what "
          "you walk TOWARD — the barn and the dovecote are IN, and their roofs are the "
          "last that ought to go):"
          % (len(_apts), _prof[-1][0] if _prof else 0.0, SECL_WARM, SECL_COURT, EYE,
             len(_town)))
    print("      village solids in sight, by metres from the warm end "
          "(all / more than 25 m from the warm end):")
    print("        " + "  ".join("%.0fm:%d/%d" % (_r[0], _r[1], _r[3]) for _r in _prof))
    _tot = _prof[-1][0] if _prof else 0.0
    if _first0 is None:
        print("      THE VILLAGE NEVER FALLS OUT OF SIGHT on this approach — its roofs "
              "are in view the whole way to the court")
    else:
        print("      THE THRESHOLD            the village (beyond the barnyard) goes out "
              "of sight %.1f m past the warm end, and over the %.1f m of approach beyond "
              "that point %.0f%% of samples see NOTHING of it; the most ever visible "
              "again at once is %d solid(s)"
              % (_first0, _tot - _first0, _zero, _peak))
        print("      THE STRICT LINE          zero and STAYS zero from %s — the last "
              "thing to go is %s, a sliver down an 86 m diagonal"
              % ("%.1f m" % _thr if _thr is not None else "NEVER",
                 ([_r[2] for _r in _prof if _r[3] > 0] or ["-"])[-1]))
    if SECL_WARM and SECL_COURT:
        print("      THE SECLUSION DISTANCE   the Old Gate stands %.1f m from Festival "
              "Square and %.1f m from the last lamp (%s), %.1f m of it by road"
              % (math.hypot(GX - POS["square-plaza"][0], GY - POS["square-plaza"][1]),
                 math.hypot(GX - POS[SECL_WARM][0], GY - POS[SECL_WARM][1]),
                 SECL_WARM, _tot + SECL_APRON + 8.0))

# ---- PROBE 3: IS FESTIVAL SQUARE A ROOM? ------------------------------------------
# USER RULING 2026-08-01 (map `coexistence._doc` (3)): *the square is a CONTAINED ROOM —
# more buildings and trees closing the ring around it so it reads as its own space.*  A
# room is a thing you measure by looking OUT of it, so: stand on the plaza and sweep the
# horizon, asking of each bearing what the eye lands on and how far away.
#
# THREE DECISIONS THIS PROBE MAKES, each of which could have been made the flattering way:
#  *  IT STARTS 4.0 m OUT, NOT AT THE CENTRE.  `square-plaza` and `heartlight` share a
#     coordinate, so a ray cast from the plaza's own centre begins INSIDE the Heartlight's
#     plinth and returns a hit on its own backface at ~1 m — sixteen sectors of "closed",
#     by the flame in the middle of the room.  The ray starts clear of the plinth and the
#     distance is reported FROM THE CENTRE, which is what the ruling's ~25 m means.
#  *  GROUND DOES NOT CLOSE A SECTOR.  A horizontal ray at eye height on a village that
#     sits on a rise runs into the rise itself, and a bank of grass is not a wall of the
#     room the ruling is asking for.  Hits are classified by what they land on and the
#     ROOFLINE-OR-CANOPY number is the one reported first; the ground figure is printed
#     beside it so the two can never be confused.
#  *  A SECTOR IS THREE RAYS, NOT ONE.  One ray per sector finds the gap between two
#     cottages and calls a closed side open, or threads a doorway and calls an open side
#     closed.  16 sectors x 3 rays at 7.5 deg; a sector closes when the MAJORITY of its
#     rays land on built mass or canopy inside the range.
if LM.get("square-plaza") and bpy.data.objects:
    _sqx, _sqy, _sqz = POS["square-plaza"]
    _SQR, _NSEC = 25.0, 16
    _start, _ez = 4.0, _sqz + EYE
    # THE FAN, AND WHY IT IS NOT ONE HORIZONTAL RAY.  The first version of this probe cast
    # level rays only, and it was wrong in a way that would have driven the geometry: a
    # broad crown's canopy starts 4.4-5.2 m up, the ground 20 m out stands 1-2 m above the
    # plaza, so its underside is 4-5 m ABOVE a standing eye — a level ray runs clean
    # underneath it and reports the sector open while the tree fills the top half of the
    # frame.  "Ends in a roofline or canopy" is a statement about the FRAME, so each
    # bearing is asked at three elevations from the eye (level, +9, +18 deg: at 25 m that
    # is a head, a first floor and a ridge line) and the eye-level answer is reported
    # separately underneath, because the two say different true things.
    _ELEV = (0.0, 0.157, 0.314)
    _BEAR = (-0.33, 0.0, 0.33)
    _closed = _eyeclosed = _groundonly = 0
    _open = []
    _dists = []
    for _s in range(_NSEC):
        _hit = _eyehit = _gh = 0
        for _bi, _bo in enumerate(_BEAR):
            _bear = 2 * math.pi * (_s + _bo) / _NSEC
            _dx, _dy = math.cos(_bear), math.sin(_bear)
            _o = Vec((_sqx + _dx * _start, _sqy + _dy * _start, _ez))
            for _ei, _el in enumerate(_ELEV):
                _d = Vec((_dx, _dy, math.tan(_el))).normalized()
                _ok, _loc, _n, _i, _obj, _m = _sc.ray_cast(
                    _dg, _o, _d, distance=(_SQR - _start) / math.cos(_el))
                if not _ok:
                    continue
                _nm = _obj.name if _obj else ""
                if _nm.startswith(("emb_ground", "walk_", "bar_")):
                    _gh += 1
                    continue
                _hit += 1
                if _ei == 0:
                    _eyehit += 1
                _dists.append(_start + math.hypot(_loc.x - _o.x, _loc.y - _o.y))
        if _hit >= 4:                       # 4 of the sector's 9 rays end on something built
            _closed += 1
            if _eyehit >= 2:
                _eyeclosed += 1
        elif _hit + _gh >= 4:
            _groundonly += 1
            _open.append(int(round(360.0 * _s / _NSEC)))
        else:
            _open.append(int(round(360.0 * _s / _NSEC)))
    _dists.sort()
    print("  THE SQUARE AS A ROOM    %d compass sectors swept from the plaza's centre "
          "(%.0f m range; %d bearings x %d elevations a sector, eye at %.2f m, cast from "
          "%.1f m out so the Heartlight's own plinth cannot close the room):"
          % (_NSEC, _SQR, len(_BEAR), len(_ELEV), EYE, _start))
    print("      sectors ending in a ROOFLINE OR CANOPY   %d of %d (%.0f%%)"
          % (_closed, _NSEC, 100.0 * _closed / _NSEC))
    print("        of those, closed AT EYE LEVEL too      %d (the rest close the upper "
          "frame with a high canopy a standing eye can see under — both are true and "
          "they are different facts)" % _eyeclosed)
    print("      sectors ending only in RISING GROUND     %d (a bank of grass is not a "
          "wall of the room)" % _groundonly)
    print("      sectors still OPEN at %.0f m               %d%s"
          % (_SQR, _NSEC - _closed,
             ("  — bearings %s deg" % ", ".join(str(b) for b in _open)) if _open else ""))
    if _dists:
        print("      where the eye lands, when it lands     median %.1f m, nearest "
              "%.1f m, furthest %.1f m"
              % (_dists[len(_dists) // 2], _dists[0], _dists[-1]))

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
