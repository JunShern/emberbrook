"""emb_lane_build.py — POND LANE, Emberbrook's second real district.

    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_lane_build.py \
        --python-exit-code 1 -- [save] [--digest]

The quiet one.  `p-lane` is the pond, its jetty, the washline green and the brook's
mouth — the map's own note calls it *"the evening mirror for the Heartlight glow"*, and
`chapter1.js` puts Finn on it, preferring fish to festivals, on the night the fish start
swimming in one slow circle.  It is also the FIRST leg of Lake's dusk round: STORY.md §2
and the map's `lamps` block send him to the low ground first, *"where moths rise off the
water at dusk"*, before he works inward and closes the ring at the Heartlight.

CONTRACT, identical to `tools/emb_square_build.py` and stated again because the pattern
is the point:

  * this pass owns `emb_ln_`, `bar_emb_ln_`, `veg_emb_ln_` and `KEYLN_`, plus the
    `lm_<member>_*` massing it replaces.  It never touches `emb_lamp_*` (the blockout's
    lamp ring is map canon and stages Lake's rounds), `emb_ground_*`, `water_*`, or any
    `walk_`/`bar_` the blockout built;
  * it does NOT rebuild the walk network.  Coverage is proved by mesh NAME against the
    map, and the blockout already emits those names with every footprint cut out;
  * every solid is gated with `district_lib.GateGrid` — master_walk_qa's own sampling
    contract — and a refusal is COUNTED and printed, never silently dropped;
  * membership is the UNION of the parcel's `members` array and every landmark whose own
    `district` field names this district.  The square pass learned that one the
    expensive way: Poppy's bakery was added to the map as a `square` landmark without
    being added to `p-square.members`, and a real bakery got built inside a gray one.

MEMBERSHIP NOTE, deliberate: `brook-bridge` and `brook-mouth` are built here even though
the parcel's array does not name them, because the map gives them `district: lanes` and
because the footbridge is the thing Pond Lane STEPS OVER.  The bridge's deck is already
a `walk_pad_` from the blockout (a deck IS its pad) and its rails are already `bar_`;
this pass only dresses them.
"""
import bpy, json, math, os, sys, hashlib
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from district_lib import GateGrid, WalkGuard

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DIGEST = "--digest" in argv

D = json.load(open(os.path.join(REPO, "public/townmap/emberbrook.map.json")))
LM = {l["id"]: l for l in D["landmarks"]}
PARCEL = next(p for p in D["parcels"] if p["id"] == "p-lane")
DISTRICT = "lanes"
# ... plus two the map files under another district and this parcel plainly contains.
# Stated as an explicit list rather than inferred, so the deviation is visible: the
# footbridge is the thing Pond Lane steps over and the brook's mouth is the confluence
# the lane ends at.  Both are dressed here; if the map ever re-districts them the union
# below simply stops adding them and nothing breaks.
EXTRA = [i for i in ("brook-bridge", "brook-mouth") if i in LM]
MEMBERS = sorted({m for m in PARCEL["members"] if m in LM} |
                 {l["id"] for l in D["landmarks"] if l.get("district") == DISTRICT} |
                 set(EXTRA))
B = PARCEL["bounds"]
REGION = (B["min"][0] - 3, B["max"][0] + 3, B["min"][1] - 3, B["max"][1] + 3)
MINE = ("emb_ln_", "bar_emb_ln_", "veg_emb_ln_", "KEYLN_")
COLL = "EMB_LANE"

BROOK = (D.get("brook") or {})
BPOLY = [tuple(p) for p in BROOK.get("polyline", [])]

print("=" * 78)
print("POND LANE — Emberbrook's second real district")
print("=" * 78)
print("  parcel %s  members: %s" % (PARCEL["id"], ", ".join(MEMBERS)))
print("  region x %.1f..%.1f  y %.1f..%.1f" % REGION)


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def M(name):
    m = bpy.data.materials.get(name)
    assert m is not None, "material %r missing — run tools/emb_blockout.py first" % name
    return m


MAT = {k: M("emb_mat_" + k) for k in
       ("grass", "earth", "road", "stone", "timber", "plaster", "thatch", "water",
        "leaf_autumn", "leaf_green", "iron", "window", "lamp_glass")}
for k in ("awn_blue", "awn_red", "awn_cream", "awn_green", "straw"):
    m = bpy.data.materials.get("emb_mat_" + k)
    if m:
        MAT[k] = m


def newmat(name, rgba, rough=0.85):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    return m


MAT["reed"] = newmat("emb_mat_reed", (0.34, 0.36, 0.19, 1))
MAT["linen"] = newmat("emb_mat_linen", (0.80, 0.78, 0.71, 1))
MAT["tarred"] = newmat("emb_mat_tarred", (0.16, 0.14, 0.13, 1), rough=0.6)

# ------------------------------------------------------------------- clearing --
removed = gone = 0
for o in list(bpy.data.objects):
    if o.name.startswith(MINE):
        bpy.data.objects.remove(o, do_unlink=True)
        removed += 1
for o in list(bpy.data.objects):
    for mid in MEMBERS:
        if o.name == "lm_" + mid or o.name.startswith("lm_%s_" % mid):
            bpy.data.objects.remove(o, do_unlink=True)
            gone += 1
            break
for d in list(bpy.data.meshes):
    if d.users == 0:
        bpy.data.meshes.remove(d)
print("  cleared %d of my own, retired %d blockout massing objects" % (removed, gone))
coll(COLL)

NEW = []


def mesh(name, verts, faces, m):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    me.update()
    if m:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    coll(COLL).objects.link(ob)
    NEW.append(ob)
    return ob


def box(name, cx, cy, cz, sx, sy, sz, m, rz=0.0):
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    c, s = math.cos(rz), math.sin(rz)
    v = []
    for dz in (-hz, hz):
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            v.append((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh(name, v, f, m)


def cyl(name, cx, cy, cz, r, h, m, seg=10, r2=None):
    r2 = r if r2 is None else r2
    v, f = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v.append((cx + r * math.cos(a), cy + r * math.sin(a), cz - h / 2))
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v.append((cx + r2 * math.cos(a), cy + r2 * math.sin(a), cz + h / 2))
    f.append(tuple(range(seg - 1, -1, -1)))
    f.append(tuple(range(seg, 2 * seg)))
    for k in range(seg):
        n = (k + 1) % seg
        f.append((k, n, seg + n, seg + k))
    return mesh(name, v, f, m)


def quad(name, a, b, c, d, m):
    return mesh(name, [a, b, c, d], [(0, 1, 2, 3)], m)


def h32(*ints):
    h = 2166136261
    for i in ints:
        h = ((h ^ (int(i) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h


def h01(*ints):
    return h32(*ints) / 4294967295.0


def appr_of(lid):
    px, py, _pz = LM[lid]["pos"]
    cands = []
    for e in D["edges"]:
        if e["from"] == lid:
            nb = (e.get("waypoints") or [LM[e["to"]]["pos"]])[0]
        elif e["to"] == lid:
            nb = (e.get("waypoints") or [LM[e["from"]]["pos"]])[-1]
        else:
            continue
        dx, dy = nb[0] - px, nb[1] - py
        d = math.hypot(dx, dy)
        if d > 1e-6:
            cands.append((0 if e.get("type") == "road" else 1, -d, dx / d, dy / d))
    if not cands:
        return (0.0, -1.0)
    cands.sort(key=lambda c: (c[0], c[1]))
    return (cands[0][2], cands[0][3])


def brook_d(x, y):
    best = 1e9
    for a, b in zip(BPOLY, BPOLY[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        best = min(best, (x - a[0] - t * dx) ** 2 + (y - a[1] - t * dy) ** 2)
    return math.sqrt(best) if best < 1e9 else 1e9


GUARD = WalkGuard(REGION)
GATE = GateGrid(REGION, GUARD)
print("  gate grid: %d walk samples inside the region" % len(GATE.pts))
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def ground_at(x, y, top=14.0):
    hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)),
                                           distance=26.0)
    return (loc.z, ob.name) if hit else (None, None)


REFUSED = []


def place(what, x, y, r, z0, z1):
    if GATE.clear_pt(x, y, r, z0, z1):
        return True
    REFUSED.append((what, round(x, 2), round(y, 2)))
    return False


POND = LM["pond"]
PX, PY, PZ = POND["pos"]
PR = POND.get("extent", 6)
JET = LM["pond-jetty"]
JX, JY, JZ = JET["pos"]
jax, jay = appr_of("pond-jetty")
JRZ = math.atan2(jay, jax) + math.pi / 2

# =============================================================================
# 1. THE JETTY — Finn's post, and the map's "where kids dare each other"
# =============================================================================
# The blockout already made the deck a `walk_pad_` (a deck IS its pad) and this pass
# must not rebuild it: it is the walk surface the cameras are solved against.  What is
# built here is everything AROUND it — the planking read, the piles, the mooring post,
# and the working clutter that says somebody fishes from it.
lx_, ly_ = math.cos(JRZ), math.sin(JRZ)              # across the jetty
fx_, fy_ = -ly_, lx_                                 # along it, out over the water
nplank = 0
for k in range(9):
    t = -2.1 + k * 0.52
    box("emb_ln_jetty_plank%02d" % k, JX + fx_ * t, JY + fy_ * t, JZ + 0.03,
        1.62, 0.44, 0.07, MAT["timber"], JRZ)
    nplank += 1
for k in range(4):
    t = -1.9 + k * 1.3
    for sgn in (-1, 1):
        px_, py_ = JX + fx_ * t + lx_ * sgn * 0.78, JY + fy_ * t + ly_ * sgn * 0.78
        # THE HEAD OF A PILE SITS UNDER THE DECK IT CARRIES.  At JZ-0.55 centre the
        # heads stood 0.25 m PROUD of the deck — three of them were the first thing a
        # walk sample's down-ray hit, which is a trip hazard modelled in wood.
        cyl("emb_ln_jetty_pile%d%d" % (k, (sgn + 1) // 2), px_, py_, JZ - 0.90, 0.13,
            1.60, MAT["tarred"], seg=8)
# the mooring post at the landward end, and the creels that make it a working jetty
mx_, my_ = JX - fx_ * 2.35, JY - fy_ * 2.35
if place("mooring post", mx_, my_, 0.20, JZ, JZ + 1.0):
    cyl("emb_ln_jetty_bollard", mx_, my_, JZ + 0.42, 0.17, 0.84, MAT["timber"], seg=8)
    box("emb_ln_jetty_bollard_cap", mx_, my_, JZ + 0.88, 0.30, 0.30, 0.09, MAT["timber"])
ncreel = 0
# SEARCHED.  Authored offsets put all three on the jetty's own deck twice running; a
# lobster creel is exactly the kind of prop that belongs beside a landing and exactly
# the kind that has nowhere authored to go.
for k in range(3):
    got = None
    for back in (3.4, 4.2, 5.0, 2.8):
        for lat in (1.6, -1.6, 2.3, -2.3, 1.0, -1.0):
            cx_ = JX - fx_ * back + lx_ * (lat + 0.42 * k)
            cy_ = JY - fy_ * back + ly_ * (lat + 0.42 * k)
            gz, gname = ground_at(cx_, cy_)
            if gz is None or (gname or "").startswith(("walk_", "water_", "emb_ln_")):
                continue
            if not GATE.clear_pt(cx_, cy_, 0.34, gz, gz + 0.7):
                continue
            got = (cx_, cy_, gz)
            break
        if got:
            break
    if got is None:
        REFUSED.append(("creel", round(JX, 2), round(JY, 2)))
        continue
    cyl("emb_ln_creel%d" % k, got[0], got[1], got[2] + 0.20, 0.30, 0.40,
        MAT.get("straw", MAT["timber"]), seg=8, r2=0.24)
    ncreel += 1
print("  jetty: %d planks, 8 piles, %d creels" % (nplank, ncreel))

# THE ROWBOAT, drawn up on the shore.  `chapter1.js` gives Pond Lane a fisherman who
# prefers fish to festivals; a boat on the bank says that before he opens his mouth.
bang = math.atan2(JY - PY, JX - PX) + 0.9
bx_, by_ = PX + (PR + 1.35) * math.cos(bang), PY + (PR + 1.35) * math.sin(bang)
if place("rowboat", bx_, by_, 1.5, PZ - 0.4, PZ + 1.1):
    brz = bang + math.pi / 2
    hull, hf = [], []
    for k in range(7):
        t = -1.0 + 2.0 * k / 6
        w = 0.62 * (1.0 - t * t * 0.82)
        c, s = math.cos(brz), math.sin(brz)
        for sgn in (-1, 1):
            ux, uy = t * 2.05, sgn * w
            hull.append((bx_ + ux * c - uy * s, by_ + ux * s + uy * c, PZ + 0.46))
        for sgn in (-1, 1):
            ux, uy = t * 1.95, sgn * w * 0.55
            hull.append((bx_ + ux * c - uy * s, by_ + ux * s + uy * c, PZ + 0.10))
    for k in range(6):
        a, b = k * 4, (k + 1) * 4
        hf += [(a, a + 2, b + 2, b), (a + 1, b + 1, b + 3, a + 3),
               (a + 2, a + 3, b + 3, b + 2), (a, b, b + 1, a + 1)]
    mesh("emb_ln_rowboat_hull", hull, hf, MAT["timber"])
    for k in (-1, 1):
        box("emb_ln_rowboat_thwart%d" % ((k + 1) // 2), bx_ + math.cos(brz) * k * 0.62,
            by_ + math.sin(brz) * k * 0.62, PZ + 0.40, 0.24, 1.05, 0.06, MAT["timber"], brz)
    box("emb_ln_rowboat_oar", bx_ + math.cos(brz) * 0.2 - math.sin(brz) * 0.55,
        by_ + math.sin(brz) * 0.2 + math.cos(brz) * 0.55, PZ + 0.52, 2.6, 0.10, 0.06,
        MAT["timber"], brz + 0.12)
    print("  rowboat drawn up on the shore at (%.1f, %.1f)" % (bx_, by_))

# =============================================================================
# 2. THE SHORE — reeds, rushes and bank stones, following the water's real edge
# =============================================================================
# The pond's authored disc is CUT against the walk footprint in the blockout, because
# the map's own note says the lane skirts it.  The reeds follow the resulting shore
# rather than the ideal circle, so the planting can never stand in open water or on the
# lane: each clump is founded by a ray onto real ground.
nreed = 0
for k in range(64):
    a = 2 * math.pi * k / 64
    for rr in (PR - 0.35, PR + 0.25, PR - 0.95):
        rx_, ry_ = PX + rr * math.cos(a), PY + rr * math.sin(a)
        gz, gname = ground_at(rx_, ry_)
        if gz is None or gname is None:
            continue
        if gname.startswith("walk_") or gname.startswith("emb_ln_"):
            continue                                  # never in the lane, never on the jetty
        if abs(gz - PZ) > 0.85:
            continue
        if not place("reeds", rx_, ry_, 0.34, gz, gz + 1.3):
            continue
        n = 3 + (h32(k, 7) % 3)
        for j in range(n):
            th = 2 * math.pi * h01(k, j, 11)
            d = 0.30 * h01(k, j, 13)
            hgt = 0.75 + 0.55 * h01(k, j, 17)
            box("veg_emb_ln_reed%02d_%d" % (k, j), rx_ + d * math.cos(th),
                ry_ + d * math.sin(th), gz + hgt / 2, 0.06, 0.06, hgt, MAT["reed"],
                rz=h01(k, j, 19) * 1.6)
        nreed += 1
        break
print("  shore: %d reed clumps, founded by ray on real ground" % nreed)

# bank stones where the brook comes in, so the confluence reads as a confluence
nstone = 0
if BPOLY:
    for k in range(14):
        t = k / 13.0
        seg = BPOLY[-2], BPOLY[-1]
        sx_ = seg[0][0] + (seg[1][0] - seg[0][0]) * t
        sy_ = seg[0][1] + (seg[1][1] - seg[0][1]) * t
        for sgn in (-1, 1):
            nx_ = -(seg[1][1] - seg[0][1])
            ny_ = (seg[1][0] - seg[0][0])
            L = math.hypot(nx_, ny_) or 1.0
            qx = sx_ + nx_ / L * sgn * (1.0 + 0.35 * h01(k, 3))
            qy = sy_ + ny_ / L * sgn * (1.0 + 0.35 * h01(k, 3))
            gz, gname = ground_at(qx, qy)
            if gz is None or (gname or "").startswith("walk_"):
                continue
            if not place("bank stone", qx, qy, 0.35, gz - 0.2, gz + 0.5):
                continue
            box("emb_ln_bankstone%02d_%d" % (k, (sgn + 1) // 2), qx, qy, gz + 0.11,
                0.56 + 0.3 * h01(k, sgn, 5), 0.48 + 0.3 * h01(k, sgn, 7), 0.28,
                MAT["stone"], rz=h01(k, sgn, 9) * 1.6)
            nstone += 1
print("  brook mouth: %d bank stones" % nstone)

# =============================================================================
# 3. THE WASHLINE GREEN — the map's own name for it, and its whole job
# =============================================================================
# Two lines of linen between posts.  It is the district's colour budget
# (docs/plans/pops-of-color.md, 5-10% of frame) and its only sign of daily life, and it
# is what makes the green read as somebody's back garden rather than as grass.
WG = LM["washline-green"]
WX, WY, WZ = WG["pos"]
WR = WG.get("extent", 3)
nline = ncloth = 0
for li in range(2):
    a0 = 0.7 + li * 1.5
    a = None
    for st in range(19):
        cand = a0 + math.radians(((st + 1) // 2) * 10 * (1 if st % 2 else -1))
        cx0, cy0 = math.cos(cand), math.sin(cand)
        t0 = (WX - cx0 * (WR + 0.9), WY - cy0 * (WR + 0.9))
        t1 = (WX + cx0 * (WR + 0.9), WY + cy0 * (WR + 0.9))
        g0t, _ = ground_at(*t0)
        g1t, _ = ground_at(*t1)
        if g0t is None or g1t is None:
            continue
        if GATE.clear_pt(t0[0], t0[1], 0.18, g0t, g0t + 2.3) and \
                GATE.clear_pt(t1[0], t1[1], 0.18, g1t, g1t + 2.3):
            a = cand
            break
    if a is None:
        REFUSED.append(("washline %d" % li, round(WX, 2), round(WY, 2)))
        continue
    ax_, ay_ = math.cos(a), math.sin(a)
    # POSTS AT THE RIM, NOT ON THE GREEN.  Inside `WR` they stand on the green's own
    # walk floor — the same lesson Festival Square's market stalls taught an hour
    # earlier, and the same answer: the washing lines FRAME the green, they do not
    # fence it.
    p0 = (WX - ax_ * (WR + 0.9), WY - ay_ * (WR + 0.9))
    p1 = (WX + ax_ * (WR + 0.9), WY + ay_ * (WR + 0.9))
    g0, _ = ground_at(*p0)
    g1, _ = ground_at(*p1)
    if g0 is None or g1 is None:
        continue
    if not (place("washpost", p0[0], p0[1], 0.16, g0, g0 + 2.3)
            and place("washpost", p1[0], p1[1], 0.16, g1, g1 + 2.3)):
        continue
    box("emb_ln_washpost%d_a" % li, p0[0], p0[1], g0 + 1.05, 0.13, 0.13, 2.10, MAT["timber"])
    box("emb_ln_washpost%d_b" % li, p1[0], p1[1], g1 + 1.05, 0.13, 0.13, 2.10, MAT["timber"])
    N = 10
    prev = None
    for s in range(N + 1):
        t = s / float(N)
        sag = 0.30 * math.sin(math.pi * t)
        p = (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t,
             g0 + 2.02 + (g1 - g0) * t - sag)
        if prev is not None:
            mid = tuple((prev[i] + p[i]) / 2 for i in range(3))
            box("emb_ln_washline%d_%02d" % (li, s), mid[0], mid[1], mid[2],
                math.dist(prev, p), 0.025, 0.025, MAT["timber"],
                rz=math.atan2(p[1] - prev[1], p[0] - prev[0]))
            if s % 3 == 1:
                w = 0.42 + 0.22 * h01(li, s, 3)
                hgt = 0.55 + 0.35 * h01(li, s, 5)
                cm = MAT["linen"] if (h32(li, s, 7) % 3) else MAT.get("awn_blue", MAT["linen"])
                quad("emb_ln_wash%d_%02d" % (li, s),
                     (mid[0] - ax_ * w / 2, mid[1] - ay_ * w / 2, mid[2]),
                     (mid[0] + ax_ * w / 2, mid[1] + ay_ * w / 2, mid[2]),
                     (mid[0] + ax_ * w / 2, mid[1] + ay_ * w / 2, mid[2] - hgt),
                     (mid[0] - ax_ * w / 2, mid[1] - ay_ * w / 2, mid[2] - hgt), cm)
                ncloth += 1
        prev = p
    nline += 1
print("  washline green: %d lines, %d hanging cloths" % (nline, ncloth))

# =============================================================================
# 4. THE FOOTBRIDGE — dressed, not rebuilt
# =============================================================================
# `brook-bridge`'s deck is already a `walk_pad_` and its rails are already `bar_`, both
# from the blockout.  Rebuilding either would put a second copy of a walk surface under
# the cameras.  So this adds only what a plank bridge has and a blockout does not:
# stringers under the deck, and abutment stones at each end.
nbr = 0
if "brook-bridge" in LM:
    BX, BY, BZ = LM["brook-bridge"]["pos"]
    bax, bay = appr_of("brook-bridge")
    BRZ = math.atan2(bay, bax) + math.pi / 2
    for sgn in (-1, 1):
        box("emb_ln_bridge_stringer%d" % ((sgn + 1) // 2),
            BX - math.sin(BRZ) * sgn * 0.72, BY + math.cos(BRZ) * sgn * 0.72,
            BZ - 0.20, 3.30, 0.14, 0.24, MAT["timber"], BRZ)
        nbr += 1
    for sgn in (-1, 1):
        ax2, ay2 = math.cos(BRZ) * sgn, math.sin(BRZ) * sgn
        # AN ABUTMENT RETAINS THE BANK — it does not bear on the deck's own pad.  At
        # 1.75 m out and BZ-0.18 tall they straddled `walk_pad_brook-bridge` and both
        # approach ribbons and were the first thing 39 walk samples hit.  Pushed clear
        # of the pad and capped WELL below the walk surface, they do the job a stone
        # abutment actually does and the rays never see them.
        qx, qy = BX + ax2 * 2.45, BY + ay2 * 2.45
        gz, _g = ground_at(qx, qy)
        if gz is None:
            continue
        top = min(BZ - 0.45, gz + 0.85)
        if top <= gz + 0.10:
            continue
        box("emb_ln_bridge_abut%d" % ((sgn + 1) // 2), qx, qy, (gz + top) / 2,
            2.30, 0.75, top - gz, MAT["stone"], BRZ)
        nbr += 1
print("  footbridge: %d dressing pieces (deck and rails left to the blockout)" % nbr)

# =============================================================================
# 5. WATERSIDE TREES — a willow habit, leaning over the water
# =============================================================================
# TWO RULES THIS SEARCH DID NOT HAVE, and the camera lane found both by measuring its
# six first drafts against the live master rather than by baking them:
#
#  (a) A TREE NEVER STANDS IN SOMEBODY ELSE'S DISTRICT.  The search was bounded by
#      REGION, which is the parcel padded by 3 m — and that padding exists so this file
#      can SEE its neighbours' geometry, not so it can plant in their districts.  Three
#      trees walked out: tree2 to (43.6, 33.8) inside p-gatefield, tree3 to (37.2, 30.6)
#      on the north lane, tree4 to (39.8, 20.6) at the pond lane's own mouth.  The rule
#      is NOT "inside p-lane" — that would forbid the wood east and north of the pond,
#      which belongs to no parcel and is where a waterside wood actually stands — it is
#      "inside p-lane, or in nobody's parcel".  `REGION` stays the READING window.
#
#  (b) A CROWN CLEARS EVERY LANE BY ITS OWN RADIUS.  `place()` tests a 1.0 m trunk
#      against the walk gate, which is right for the gate and useless for occlusion: the
#      thing that stands between a camera and its subject is the CROWN, 3 m across and
#      leaning.  This is Festival Square's 5.4 m lesson (trees planted 2.6 m off the rim
#      were a wall of green in every hero frame; the fix for an occluder is to move the
#      occluder) applied where it was never applied — and it is the same measurement
#      seam-canon §9.3 asks for, taken against the map's own roads instead of by eye.
CROWN_R = 3.0                                   # widest crown this pass plants + its lean
LANE_CLEAR = 1.0


def _polyd(x, y, q):
    best = 1e9
    for n in range(len(q)):
        a, b = q[n], q[(n + 1) % len(q)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        best = min(best, math.hypot(x - a[0] - t * dx, y - a[1] - t * dy))
    return best


WALKQ = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(("walk_e_", "walk_pad_")):
        continue
    P = [o.matrix_world @ v.co for v in o.data.vertices]
    if len(P) < 8:
        continue
    WALKQ.append([(p.x, p.y) for p in P[:4]])


def lane_clear(tx, ty):
    return all(_polyd(tx, ty, q) >= CROWN_R + LANE_CLEAR for q in WALKQ)


ntree = 0
TREJ = {"parcel": 0, "lane": 0, "ground": 0, "brook": 0, "gate": 0}
for k in range(8):
    a0 = 2 * math.pi * k / 8 + 0.3
    # A SEARCH THAT COMES BACK EMPTY SHOULD SEARCH HARDER BEFORE IT GIVES UP.  With the
    # parcel and crown rules added, three radii x +/-24 degrees found seats for only 3 of
    # the 8 hosts and the waterside wood — the district's whole silhouette — went with
    # them.  Six radii x +/-48 degrees is the same rule set over a wider net.
    for rr, st in [(rr, st) for rr in (PR + 2.2, PR + 3.0, PR + 3.8, PR + 4.6,
                                       PR + 5.4, PR + 6.4) for st in range(13)]:
        a = a0 + math.radians(((st + 1) // 2) * 8 * (1 if st % 2 else -1))
        tx, ty = PX + rr * math.cos(a), PY + rr * math.sin(a)
        if any(p["id"] != PARCEL["id"]
               and p["bounds"]["min"][0] <= tx <= p["bounds"]["max"][0]
               and p["bounds"]["min"][1] <= ty <= p["bounds"]["max"][1]
               for p in D["parcels"]):
            TREJ["parcel"] += 1
            continue
        gz, gname = ground_at(tx, ty)
        if gz is None or (gname or "").startswith(("walk_", "water_", "emb_ln_")):
            TREJ["ground"] += 1
            continue
        if BPOLY and brook_d(tx, ty) < 1.6:
            TREJ["brook"] += 1
            continue
        if not lane_clear(tx, ty):
            TREJ["lane"] += 1
            continue
        if not place("tree", tx, ty, 1.0, gz, gz + 8.0):
            TREJ["gate"] += 1
            continue
        ht = 5.6 + 2.4 * h01(k, 13)
        lean = 0.55 * (1.0 if rr < PR + 3.5 else 0.2)   # the near ones lean over the water
        lx2, ly2 = math.cos(a + math.pi), math.sin(a + math.pi)
        box("veg_emb_ln_tree%d_trunk" % k, tx, ty, gz + ht * 0.30, 0.32, 0.32,
            ht * 0.64, MAT["timber"])
        leaf = MAT["leaf_green"] if (h32(k, 19) % 5) < 3 else MAT["leaf_autumn"]
        for c_ in range(3):
            rr2 = (2.2 + 0.8 * h01(k, 23 + c_)) * (1.0 - 0.18 * c_)
            cyl("veg_emb_ln_tree%d_crown%d" % (k, c_),
                tx + lx2 * lean * (c_ + 1) * 0.7, ty + ly2 * lean * (c_ + 1) * 0.7,
                gz + ht * 0.58 + c_ * 1.25, rr2, 1.8, leaf, seg=8, r2=rr2 * 0.6)
        ntree += 1
        break
print("  waterside: %d trees of 8 hosts, the near ones leaning over the pond" % ntree)
print("    tree feet refused — outside the parcel %d, crown over a lane %d, "
      "no ground %d, on the brook %d, walk gate %d"
      % (TREJ["parcel"], TREJ["lane"], TREJ["ground"], TREJ["brook"], TREJ["gate"]))

# =============================================================================
# ACCEPTANCE
# =============================================================================
print("-" * 78)
if REFUSED:
    print("  REFUSED (would have stood in the walk gate's own rays) — %d:" % len(REFUSED))
    for nm, x, y in REFUSED[:16]:
        print("      %-22s at (%.2f, %.2f)" % (nm, x, y))
else:
    print("  REFUSED: none")

dg = bpy.context.evaluated_depsgraph_get()
NEWNAMES = {o.name for o in NEW if o.type == 'MESH'}
offenders = {}
for (sx, sy, sz) in GATE.pts:
    for org, dvec, dist in (((sx, sy, sz + 0.90), (0, 0, -1), 1.90),
                            ((sx, sy, sz + 0.06), (0, 0, 1), 1.94)):
        hit, _l, _n, _i, ob, _m = sc.ray_cast(dg, Vector(org), Vector(dvec), distance=dist)
        if hit and ob is not None and ob.name in NEWNAMES:
            floor = "?"
            fh, _fl, _fn, _fi, fo, _fm = sc.ray_cast(dg, Vector((sx, sy, sz + 0.05)),
                                                     Vector((0, 0, -1)), distance=0.60)
            if fh and fo is not None:
                floor = fo.name
            offenders.setdefault(ob.name, []).append(floor)
print("  GATE RE-CHECK (master_walk_qa's own two rays, %d walk samples): %d offenders"
      % (len(GATE.pts), len(offenders)))
for nm in sorted(offenders)[:20]:
    print("      %-30s %3d samples on %s"
          % (nm, len(offenders[nm]), ", ".join(sorted(set(offenders[nm])))[:70]))

heart = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.energy > 2000]
assert len(heart) == 1, "Emberbrook has exactly one Heartlight — found %d" % len(heart)
mine = [o for o in bpy.data.objects if o.name.startswith(MINE)]
print("  still exactly one magical light town-wide (%s)" % heart[0].name)
print("  BUILT: %d objects, %d vertices under %s"
      % (len(mine), sum(len(o.data.vertices) for o in mine if o.type == 'MESH'),
         "/".join(MINE)))

if DIGEST:
    h = hashlib.sha256()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        h.update(o.name.encode())
        if o.type == 'MESH':
            for v in o.data.vertices:
                h.update(("%.4f,%.4f,%.4f;" % (v.co.x, v.co.y, v.co.z)).encode())
    print("DIGEST %s" % h.hexdigest())

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
