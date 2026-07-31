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
M_PLASTER = mat("emb_mat_plaster", (0.70, 0.64, 0.53, 1))
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
M_WINDOW = mat("emb_mat_window", (1.0, 0.80, 0.52, 1), rough=0.3,
               emit=((1.0, 0.72, 0.36, 1), 6.0))
M_GLASS = mat("emb_mat_lamp_glass", (1.0, 0.78, 0.44, 1), rough=0.2,
              emit=((1.0, 0.66, 0.30, 1), 24.0))
# THE ONE MAGICAL LIGHT IN THE TOWN.  Emberbrook is the rare survivor that still HAS a
# Heartlight and that is its identity (STORY.md §1).  Exactly one material in this file
# emits like this; a second anywhere in Emberbrook would be a canon bug.
M_HEART = mat("emb_mat_heartlight", (1.0, 0.78, 0.42, 1), rough=0.1,
              emit=((1.0, 0.66, 0.28, 1), 180.0))

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
BPOLY = resample([tuple(p) for p in BROOK["polyline"]], 0.6) if BROOK.get("polyline") else []
BW = BROOK.get("widthM", 1.2)
RCX = RIVER.get("centerX", None)
RWID = RIVER.get("width", 11)
RLVL = RIVER.get("level", -0.6)

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
PAD = 22.0
X0, X1 = min(XS) - PAD, max(XS) + PAD
Y0, Y1 = min(YS) - PAD, max(YS) + PAD
print("  town extent  x %.1f..%.1f  y %.1f..%.1f   (%d anchors, %d brook samples)"
      % (min(XS), max(XS), min(YS), max(YS), len(ANCH), len(BPOLY)))

# ============================================================ the valley floor ==
# The rise is INTERPOLATED from the map's own z values rather than sculpted, so the
# ground can never disagree with the walk network laid on top of it.  Then two channels
# are CARVED — the brook's and the river's — because a stream drawn on flat ground is a
# blue stripe, and a stream in a channel is a stream.
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
    t = max(0.0, min(1.0, (dmin - 9.0) / 16.0))
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
    # the brook's channel: a shallow V, 0.55 m deep and 3.2 m wide — deep enough to
    # hold water, shallow enough that the village stays ONE ground and not a ravine
    if BPOLY:
        d = brook_d(x, y)
        if d < 3.2:
            z -= 0.55 * (1.0 - d / 3.2) ** 1.6
    # the valley river east of town: a real channel, and the reason the eastern horizon
    # is water instead of void (the t2 vista lesson — never an unaudited sightline)
    if RCX is not None:
        d = abs(x - RCX)
        if d < RWID / 2 + 7.0:
            t = max(0.0, min(1.0, 1.0 - max(0.0, d - RWID / 2) / 7.0))
            z = z * (1 - t) + (RLVL - 1.1) * t
    return z


NX = int(round((X1 - X0) / GSTEP)) + 1
NY = int(round((Y1 - Y0) / GSTEP)) + 1
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
print("  emb_ground_valley      %d verts (%d x %d @ %.1f m)" % (len(gv), NX, NY, GSTEP))

# a skirt so no camera can see the underside or the world edge (t2 vista lesson)
box("emb_ground_far", (X0 + X1) / 2, (Y0 + Y1) / 2, PAN - 3.2,
    (X1 - X0) + 90.0, (Y1 - Y0) + 90.0, 1.2, M_GRASS, "EMB_CONTEXT")

# ============================================================== the wooded rim ==
# Emberbrook is a clearing in the Whisperwood; the rim is what closes every horizon.
# It is dressing (`veg_`) and it is deterministic (h01 of the tree's own index).
RIMN = 150
cx0, cy0 = (min(XS) + max(XS)) / 2, (min(YS) + max(YS)) / 2
rx, ry = (max(XS) - min(XS)) / 2 + 11.0, (max(YS) - min(YS)) / 2 + 11.0
ntree = 0
for k in range(RIMN):
    a = 2 * math.pi * k / RIMN
    band = 1.0 + 0.60 * h01(k, 11)
    x = cx0 + rx * band * math.cos(a)
    y = cy0 + ry * band * math.sin(a)
    if not (X0 + 2 < x < X1 - 2 and Y0 + 2 < y < Y1 - 2):
        continue
    if RCX is not None and abs(x - RCX) < RWID / 2 + 2.0:
        continue                                        # no trees standing in the river
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
print("  veg_emb_rim_*          %d trees" % ntree)

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
            return (3.4, 2.6)
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
    big = kind.startswith("shop") or kind == "building"
    bw, bd = (5.4, 4.6) if big else (4.4, 3.8)
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


APPR = {}
for l in D["landmarks"]:
    i = l["id"]
    vx = vy = 0.0
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
            vx += dx / d
            vy += dy / d
    d = math.hypot(vx, vy)
    APPR[i] = (vx / d, vy / d) if d > 1e-6 else (0.0, -1.0)

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
        back = abs(ax) * bw / 2 + abs(ay) * bd / 2 + 1.15
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
            box("walk_pad_" + i, x, y, z, 3.2, 2.2, 0.16, M_TIMBER, "EMB_PATHS", rz)
            for sgn in (-1, 1):
                tag = "AB"[(sgn + 1) // 2]
                ox, oy = -ay * sgn * 1.05, ax * sgn * 1.05
                box("bar_%s_rail%s" % (i, tag), x + ox, y + oy, z + 0.55,
                    3.2, 0.09, 0.10, M_TIMBER, "EMB_MASSING", rz)
                for k in (-1, 1):
                    box("bar_%s_post%s%d" % (i, tag, k + 1),
                        x + ox + ax * k * 1.35, y + oy + ay * k * 1.35, z + 0.30,
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
        bw, bd, bh = (5.4, 4.6, 4.6) if big else (4.4, 3.8, 3.2)
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
npad = nskip = 0
for l in D["landmarks"]:
    i = l["id"]
    if l.get("class", "structure") not in ("structure", "prop", "portal") or i in WATER_LM:
        continue
    if (l.get("kind") or "") in ("dock", "heartlight") or "bridge" in (l.get("name") or "").lower():
        continue                                        # deck IS the pad; the flame has none
    dx, dy, dz = DOOR[i]
    inside = in_area(dx, dy, -0.9)
    if inside:
        nskip += 1
        print("    pad %-18s SKIPPED — its doorstep stands on walk_lm_%s" % (i, inside))
        continue
    w = 2.6 if l.get("class") == "portal" else 3.0
    box("walk_pad_" + i, dx, dy, dz, w, w, 0.14, M_EARTH, "EMB_PATHS")
    npad += 1
print("  walk_pad_*             %d pads (%d skipped: already on an area floor)" % (npad, nskip))

# ================================================================== the paths ==
# Flat chaikin-smoothed ribbons, named `walk_e_<from>__<to>_l<i>` — the name IS the
# coverage contract (`cine_regions.mjs` matches meshes to map edges by it, which is what
# makes "every walkable metre has exactly one owner" checkable instead of hoped).  Edges
# run DOORSTEP to DOORSTEP, so a road stops at the step and never inside a wall.
nrib = 0
RIBSEGS = []
for e in EDGES:
    if e["from"] not in DOOR or e["to"] not in DOOR:
        print("  SKIP dangling edge %s__%s" % (e["from"], e["to"]))
        continue
    pts = [DOOR[e["from"]]] + [tuple(w) for w in e.get("waypoints", [])] + [DOOR[e["to"]]]
    nm = "e_%s__%s" % (e["from"], e["to"])
    t = e.get("type", "path")
    draw = chaikin(pts) if t in ("road", "path") else pts
    wdt = 2.4 if t == "road" else 1.7
    m = M_ROAD if t == "road" else M_EARTH
    for k in range(len(draw) - 1):
        ribbon("walk_%s_l%d" % (nm, k), draw[k], draw[k + 1], wdt, 0.14, m, "EMB_PATHS")
        RIBSEGS.append((draw[k], draw[k + 1], wdt))
        nrib += 1
print("  walk_e_*               %d ribbon segments over %d edges" % (nrib, len(EDGES)))

# ========================= the walk footprint, rasterised — RULE 4's instrument ==
# Water is cut against this, so the pond's authored disc becomes a pond whose shore the
# lane skirts (the map's own words) instead of a lane that runs through a pond.
OSTEP = 0.45
ONX = int((X1 - X0) / OSTEP) + 2
ONY = int((Y1 - Y0) / OSTEP) + 2
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


def occupied(x, y):
    i, j = int((x - X0) / OSTEP), int((y - Y0) / OSTEP)
    return 0 <= i < ONX and 0 <= j < ONY and OCC[j * ONX + i]


def corridor_clear(x, y, m=0.40):
    """Clear of every ribbon's own edge by `m`, measured against the segment rather
    than against the dilated raster.  The raster is right for water (generous is safe);
    it is wrong for a lamppost in a plaza, where 8 spurs radiate from one point and a
    0.40 m dilation of each blocked 77 of 111 candidate feet.  A lamppost's whole job is
    to stand at the edge of a road."""
    for (a, b, wdt) in RIBSEGS:
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
NO_LAMP = {"waystone", "sigil-gate", "forest-trailhead", "heartlight", "home-lane-end",
           "notice-board", "well", "brook-spring", "brook-mouth"}
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
print("    the round: " + " -> ".join(PLACED))

# ------------------------------------------------- area floors, with the holes --
CELL = 0.7
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
            # PAD = 0.28 + CELL/2.  A cell is kept or dropped by its CENTRE, so a
            # 0.28 pad leaves cells straddling a building's wall by up to half a cell,
            # and GateGrid samples inside those overhangs — which is exactly how 32
            # pieces of Festival Square's first real build came out standing on
            # walkable floor.  Half a cell is the honest margin.
            if any(in_rect(cx, cy, h, 0.63) for h in holes):
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
    print("    water_emb_brook       %3d cells, %.1f m wide, %.1f m of run" % (n, BW, run))
    nw += n

if RCX is not None:
    # ONE SLAB, not a cell field: the river is a VISTA the map says is "visible east of
    # town, NOT walkable", nothing walkable comes within 5 m of it, and 3 028 cells of
    # water nobody can reach is 24 000 vertices spent on a thing no camera resolves.
    box("water_emb_river", RCX, (Y0 + Y1) / 2, RLVL - 0.06, RWID, (Y1 - Y0) + 60.0, 0.12,
        M_WATER, "EMB_WATER")
    print("    water_emb_river       1 slab, centre x %.1f, %.1f m wide at z %.2f"
          % (RCX, RWID, RLVL))
print("  water_*                %d cells total" % nw)

# ------------------------------------------------------ culverts under the roads --
# Where a walk ribbon crosses the brook and no footbridge stands within 3 m, the road
# would hover over open water.  Found by measurement, founded in stone, and PRINTED —
# a floating road reads as art until somebody walks it.
ncul = 0
if BPOLY:
    seen = []
    for (a, b, wdt) in RIBSEGS:
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
            print("    CULVERT %d at (%.1f, %.1f) — road z %.2f over brook z %.2f"
                  % (ncul, x, y, z, bz))
            ncul += 1
print("  emb_culvert_*          %d road-over-brook crossings" % ncul)



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
    if not any(o.name.startswith("walk_e_%s__%s_l" % (e["from"], e["to"]))
               for o in bpy.data.objects):
        missing.append("walk_e_%s__%s_l*" % (e["from"], e["to"]))
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
