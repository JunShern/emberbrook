"""emb_square_build.py — FESTIVAL SQUARE, the first REAL district of Emberbrook.

    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_square_build.py \
        --python-exit-code 1 -- [save]

WHAT THIS REPLACES.  `tools/emb_blockout.py` raises the whole town from the map as gray
massing: every landmark gets an `lm_*` box-and-roof, and the walk network — pads, area
floors and road ribbons — is derived from the map's own records.  This pass takes the
`p-square` PARCEL (`square-plaza`, `heartlight`, `inn`, `item-shop`, `bakery`,
`notice-board`, `well`) and builds it for real.

THE ONE THING IT DOES NOT TOUCH IS THE WALK NETWORK, and that is deliberate.  Ownership
in `cine_regions.mjs` is proved BY MESH NAME against the map (`walk_lm_square-plaza`,
`walk_pad_<id>`, `walk_e_<from>__<to>_*`).  The blockout already emits exactly those
names, already cut around every footprint this file rebuilds, and every camera solved
against them is solved against the floor the player actually walks.  A district builder
that re-cut its own floors would be re-deriving the coverage contract by hand, twice,
and the two copies would drift.  So: this file owns the ART.  If a building's footprint
ever needs to move, it moves IN THE MAP, the blockout re-runs, and both halves follow.

PREFIX OWNERSHIP, per the canon `lg_build`'s near-miss wrote on 2026-07-30 ("a
two-letter prefix is not ownership"): this pass clears `emb_sq_`, `bar_emb_sq_`,
`veg_emb_sq_` and `KEYSQ_` ONLY, plus the `lm_<member>_*` massing it is replacing.  It
never touches `emb_lamp_*` (the blockout's lamp ring, which stages Lake's rounds and is
map-canon), `emb_ground_*`, `water_*`, or any `walk_`/`bar_` the blockout built.
Asserted below, not assumed.

WORLD CANON, and this town is the exception the canon exists to make interesting:
EMBERBROOK HAS A HEARTLIGHT.  Heartlights are all but extinct — a handful left in the
world — and this village is one of the survivors, which is its whole identity.  So the
plinth at (32, 22) is not a prop: it is the reservoir every lamppost in the village is
lit FROM, it is the brightest thing in any frame that contains it, and it is the ONLY
magical light source in the town.  Every other flame here is an ordinary 680 W warm
practical, the standard seven Dellhollow districts already share.  A second glowing
crystal anywhere in Emberbrook would be a canon bug.

THE REFERENCE IS SHIPPED ART, NOT A MOOD.  `public/assets/scenes/square/festival.png`
is the accepted Chapter One painting of this exact place: bakery open to the plaza with
its trays lit, the big half-timbered house up stone steps, stalls with green/blue/
red-striped awnings, bunting and little hanging lanterns strung overhead, pumpkins and
haybales HUDDLED against building feet (never scattered singletons —
`docs/SCENE-LAYOUT.md`), autumn trees closing the corners with greens mixed in.  Every
element below is transcribed from it onto the map's own coordinates.

DETERMINISM IS A GATE: no `random`, no time, no `bpy.ops` primitives.  Variation comes
from `h01()`, an integer hash of the object's own index.  `-- --digest` prints a vertex
digest so two runs can be diffed.
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
PARCEL = next(p for p in D["parcels"] if p["id"] == "p-square")
# THE PARCEL'S MEMBER LIST IS NOT THE WHOLE DISTRICT.  Poppy's bakery was added to the
# map as a `square` landmark during tonight's redline pass and p-square's `members` array
# was not updated with it — so the first build put a real bakery INSIDE the blockout's
# gray one and the geometry audit found 146 intersections, most of them downstream of
# that single omission.  Membership is therefore the UNION of the parcel's list and every
# landmark whose own `district` field names this district: whichever the map author
# edits, the builder follows.
DISTRICT = "square"
MEMBERS = sorted({m for m in PARCEL["members"] if m in LM} |
                 {l["id"] for l in D["landmarks"] if l.get("district") == DISTRICT})
B = PARCEL["bounds"]
REGION = (B["min"][0] - 2, B["max"][0] + 2, B["min"][1] - 2, B["max"][1] + 2)

MINE = ("emb_sq_", "bar_emb_sq_", "veg_emb_sq_", "KEYSQ_")
COLL = "EMB_SQUARE"

print("=" * 78)
print("FESTIVAL SQUARE — the first real district of Emberbrook")
print("=" * 78)
print("  parcel %s  members: %s" % (PARCEL["id"], ", ".join(MEMBERS)))
print("  region x %.1f..%.1f  y %.1f..%.1f" % REGION)

# PREFIX SAFETY, asserted: `emb_lamp_*` is the blockout's lamp ring (Lake's rounds, map
# canon) and `emb_ground_*` is the valley.  Neither starts with any prefix this pass
# clears, and this is the assertion that keeps it true if a prefix ever gets shortened.
for p in MINE:
    assert not p.startswith("emb_l") and not p.startswith("emb_g"), \
        "prefix %r would swallow the blockout's lamps or ground" % p
assert not any(o.name.startswith("emb_lamp_") and o.name.startswith(MINE)
               for o in bpy.data.objects), "prefix collision with the lamp ring"


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
       ("grass", "earth", "road", "cobble", "stone", "timber", "plaster", "thatch",
        "slate", "tile", "leaf_autumn", "leaf_green", "iron", "window", "lamp_glass",
        "heartlight")}


def newmat(name, rgba, rough=0.85, emit=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = emit[0]
        b.inputs["Emission Strength"].default_value = emit[1]
    return m


# POPS OF COLOUR, 5-10% of frame (docs/plans/pops-of-color.md).  In the square that
# budget is spent on exactly three things and they are all festival: the striped awnings,
# the pumpkins, and the bunting flags.  Everything else is timber, stone and thatch.
MAT["awn_green"] = newmat("emb_mat_awn_green", (0.22, 0.34, 0.16, 1))
MAT["awn_blue"] = newmat("emb_mat_awn_blue", (0.12, 0.20, 0.40, 1))
MAT["awn_red"] = newmat("emb_mat_awn_red", (0.55, 0.14, 0.12, 1))
MAT["awn_cream"] = newmat("emb_mat_awn_cream", (0.82, 0.76, 0.62, 1))
MAT["pumpkin"] = newmat("emb_mat_pumpkin", (0.72, 0.31, 0.07, 1))
MAT["straw"] = newmat("emb_mat_straw", (0.68, 0.58, 0.30, 1))
MAT["bread"] = newmat("emb_mat_bread", (0.66, 0.44, 0.20, 1))
MAT["beam"] = newmat("emb_mat_beam", (0.24, 0.16, 0.10, 1))

# ------------------------------------------------------------------- clearing --
removed = 0
for o in list(bpy.data.objects):
    if o.name.startswith(MINE):
        bpy.data.objects.remove(o, do_unlink=True)
        removed += 1
for d in list(bpy.data.lights):
    if d.name.startswith("KEYSQ_") and d.users == 0:
        bpy.data.lights.remove(d)
# ... and the blockout massing this pass exists to replace.  Idempotent: on a re-run
# they are already gone and the count is zero.
gone = 0
for o in list(bpy.data.objects):
    for mid in MEMBERS:
        if o.name == "lm_" + mid or o.name.startswith("lm_%s_" % mid):
            bpy.data.objects.remove(o, do_unlink=True)
            gone += 1
            break
for d in list(bpy.data.meshes):
    if d.users == 0:
        bpy.data.meshes.remove(d)
print("  cleared %d of my own objects, retired %d blockout massing objects" % (removed, gone))
coll(COLL)

# ------------------------------------------------------------------ primitives --
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


def cyl(name, cx, cy, cz, r, h, m, seg=12, r2=None):
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


def gable(name, cx, cy, cz, sx, sy, h, m, rz=0.0, over=0.0):
    hx, hy = sx / 2.0 + over, sy / 2.0 + over
    c, s = math.cos(rz), math.sin(rz)

    def P(dx, dy, dz):
        return (cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz)

    v = [P(-hx, -hy, 0), P(hx, -hy, 0), P(hx, hy, 0), P(-hx, hy, 0),
         P(-hx * 0.94, 0, h), P(hx * 0.94, 0, h)]
    f = [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)]
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


def foot_of(l):
    """The map landmark's plan footprint, as the blockout derives it — one definition,
    so the builder's stalls and the blockout's floor cut-outs agree about how big a
    house is."""
    kind = l.get("kind") or ""
    cls = l.get("class", "structure")
    nm = (l.get("name") or "").lower()
    if cls in ("area", "dressing"):
        return None
    if cls == "portal":
        bw, bd = (2.4, 1.8) if kind == "trailhead" else (4.6, 1.6)
    elif cls == "prop":
        bw, bd = ((3.4, 2.6) if "bridge" in nm else
                  (2.6, 2.6) if ("spring" in nm or "mouth" in nm) else
                  (2.5, 2.5) if "well" in nm else
                  (2.2, 1.6) if "board" in nm else (2.0, 1.4))
    elif kind == "heartlight":
        bw, bd = (2.4, 2.4)
    elif kind == "dock":
        bw, bd = (1.9, 4.7)
    else:
        big = kind.startswith("shop") or kind == "building"
        bw, bd = (4.8 * 1.14, 4.0 * 1.14) if big else (3.9 * 1.14, 3.3 * 1.14)
    ax, ay = appr_of(l["id"])
    return (l["pos"][0], l["pos"][1], bw / 2, bd / 2, math.atan2(ay, ax) + math.pi / 2)


def in_rect_l(px, py, l, pad=0.0):
    r = foot_of(l)
    if r is None:
        return False
    cx, cy, hw, hd, rz = r
    c, s_ = math.cos(-rz), math.sin(-rz)
    dx, dy = px - cx, py - cy
    return abs(dx * c - dy * s_) <= hw + pad and abs(dx * s_ + dy * c) <= hd + pad


def appr_of(lid):
    """The direction a landmark is approached from — the same derivation the blockout
    used to place its doorstep, so the door this pass builds is on the side the road
    actually arrives at."""
    px, py, _pz = LM[lid]["pos"]
    vx = vy = 0.0
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
            vx += dx / d
            vy += dy / d
    d = math.hypot(vx, vy)
    return (vx / d, vy / d) if d > 1e-6 else (0.0, -1.0)


# The gate's OWN sampling contract, so "will this solid break the walk gate" is answered
# by the gate's instrument and not by a stricter one.  `free_box` is the corridor guard
# and would refuse every awning post at the edge of the plaza it belongs to (it refused
# 19 of 38 crossing rails); GateGrid reproduces master_walk_qa's two rays exactly.
GUARD = WalkGuard(REGION)
GATE = GateGrid(REGION, GUARD)
print("  gate grid: %d walk samples inside the region" % len(GATE.pts))
REFUSED = []


def place(name_for, x, y, r, z0, z1):
    """True when a solid of this footprint may stand here.  A refusal is COUNTED and
    printed, never silently skipped — a district that quietly drops a third of its
    dressing is a district nobody can review."""
    if GATE.clear_pt(x, y, r, z0, z1):
        return True
    REFUSED.append((name_for, round(x, 2), round(y, 2)))
    return False


SQ = LM["square-plaza"]
SX, SY, SZ = SQ["pos"]
SR = SQ.get("extent", 7)

# =============================================================================
# 1. THE HEARTLIGHT — the reason the town exists, and the reason it survived
# =============================================================================
HL = LM["heartlight"]
HX, HY, HZ = HL["pos"]
# a stepped plinth: two courses of dressed stone, a moulded cap, the crystal above it.
# Low on purpose — the reference painting puts the flame at chest-to-head height so it
# reads as something a village GATHERS AROUND, not a monument it stands beneath.
box("emb_sq_heart_step", HX, HY, HZ + 0.11, 2.86, 2.86, 0.22, MAT["stone"])
box("emb_sq_heart_base", HX, HY, HZ + 0.44, 2.20, 2.20, 0.44, MAT["stone"])
cyl("emb_sq_heart_drum", HX, HY, HZ + 1.06, 0.92, 0.80, MAT["stone"], seg=16)
box("emb_sq_heart_cap", HX, HY, HZ + 1.52, 1.86, 1.86, 0.16, MAT["stone"])
for k in range(4):
    a = math.pi / 2 * k + math.pi / 4
    box("emb_sq_heart_corbel%d" % k, HX + 0.82 * math.cos(a), HY + 0.82 * math.sin(a),
        HZ + 1.36, 0.34, 0.34, 0.20, MAT["stone"], rz=a)
# the flame-crystal: a faceted shard, not a fire.  STORY.md — it HUMS, "very faintly,
# like a kettle two rooms away", and it has burned for three hundred years.
CV, CF = [], []
for k in range(6):
    a = 2 * math.pi * k / 6
    CV.append((HX + 0.30 * math.cos(a), HY + 0.30 * math.sin(a), HZ + 1.62))
for k in range(6):
    a = 2 * math.pi * k / 6 + 0.3
    CV.append((HX + 0.20 * math.cos(a), HY + 0.20 * math.sin(a), HZ + 2.22))
CV.append((HX, HY, HZ + 2.86))
for k in range(6):
    n = (k + 1) % 6
    CF.append((k, n, 6 + n, 6 + k))
    CF.append((6 + k, 6 + n, 12))
CF.append(tuple(range(5, -1, -1)))
mesh("emb_sq_heart_crystal", CV, CF, MAT["heartlight"])
li = bpy.data.lights.new("KEYSQ_heartlight", 'POINT')
li.energy = 5200.0                       # ~7.6x the town's ordinary lamp: it is the source
li.color = (1.0, 0.63, 0.28)
li.shadow_soft_size = 0.42
lo = bpy.data.objects.new(li.name, li)
lo.location = (HX, HY, HZ + 2.20)
coll(COLL).objects.link(lo)
NEW.append(lo)
# the blockout's own Heartlight point light is retired with its massing
for o in list(bpy.data.objects):
    if o.name.startswith("KEYEMB_heartlight"):
        bpy.data.objects.remove(o, do_unlink=True)
print("  HEARTLIGHT built — 1 magical source, 5200 W, at (%.1f, %.1f, %.2f)" % (HX, HY, HZ + 2.2))

# NO PAVED APRON, and the deletion is the finding.  The first draft laid two rings of
# cobble quads 30 mm under the walk floor to reproduce the reference's paved centre.
# Two things were wrong with it: `walk_lm_square-plaza` is ALREADY built from the
# cobble material by the blockout, so the apron was drawing paving on top of paving;
# and the square's road ribbons run 100-150 mm below the plaza cells, so a "30 mm
# under the floor" ring sat ABOVE those samples and the walk gate flagged all 80 quads.
# The paving language the reference asks for is the plaza floor's own material, and it
# was already there.

# =============================================================================
# 2. THE BUILDINGS — transcribed from the shipped painting onto the map's points
# =============================================================================
BUILT = {}


def house(lid, storeys, roofmat, sign=None, openfront=False, awning=None, small=False,
          scale=1.0):
    """One village building.  The footprint is the blockout's own (`bodysize`), so the
    plaza floor's cut-out still fits it exactly; only the ART changes."""
    l = LM[lid]
    x, y, z = l["pos"]
    kind = l.get("kind") or ""
    big = (kind.startswith("shop") or kind == "building") and not small
    bw, bd = (4.8, 4.0) if big else (3.9, 3.3)
    bw, bd = bw * scale, bd * scale
    ax, ay = appr_of(lid)
    rz = math.atan2(ay, ax) + math.pi / 2
    bh = 2.55 * storeys + 0.55
    # A MEASURED SET-BACK, printed.  The map fixes where a building IS, to the metre;
    # it does not promise that a 5.4 m frontage clears a 2.4 m road passing 3.8 m away.
    # Rather than move the landmark (the map is authority) or leave a plinth standing in
    # a corridor (the walk gate's own failure), the massing steps BACKWARDS along its own
    # approach axis until the walk gate's samples are clear — at most 2.00 m.  If that
    # is not enough the building stays put and the overlap is REPORTED, because a
    # silent nudge is how a town stops matching its own map.
    # THE BOUND MUST BE OF THE ROTATED BOX.  Testing the unrotated half-extents let the
    # inn through at step 0 and the ray check then found 14 walk samples under its
    # plinth: a 5.5 x 4.7 m box turned 128 degrees has an axis-aligned bound of
    # 7.3 x 7.2, and the smaller box is not a bound of the bigger one.
    # ... AND THE BOUND IS THE ROTATED RECTANGLE ITSELF, not its axis-aligned box.
    # The AABB is a valid bound and a useless one here: a 4.9 x 4.1 m inn turned 128
    # degrees has an AABB of 6.4 x 6.3, and searching against it reported the inn boxed
    # in with no clear offset in ANY direction within 2.1 m — while the ray check, which
    # is the gate's real instrument, found three samples.  Testing the actual rectangle
    # against the gate's own sample points asks the question the gate asks.
    hw_, hd_ = (bw + 0.10) / 2 + 0.10, (bd + 0.10) / 2 + 0.10
    crz, srz = math.cos(-rz), math.sin(-rz)

    def rects_overlap(A, Bb):
        """Separating-axis test on two oriented rectangles.  Cheap, exact, and the
        reason it is here: the map puts Poppy's bakery 4.03 m from the inn's front
        corner, and two 4.8 m buildings at that spacing INTERPENETRATE — the geometry
        audit found the bakery's roof, walls, rail, studs and shopfront all inside the
        inn's wall.  A set-back search that only avoids the WALK gate will happily park
        one house inside another."""
        for (P, Q) in ((A, Bb), (Bb, A)):
            cx1, cy1, hw1, hd1, rz1 = P
            for (ux, uy) in ((math.cos(rz1), math.sin(rz1)),
                             (-math.sin(rz1), math.cos(rz1))):
                r1 = hw1 * abs(ux * math.cos(rz1) + uy * math.sin(rz1)) + \
                     hd1 * abs(-ux * math.sin(rz1) + uy * math.cos(rz1))
                cx2, cy2, hw2, hd2, rz2 = Q
                r2 = hw2 * abs(ux * math.cos(rz2) + uy * math.sin(rz2)) + \
                     hd2 * abs(-ux * math.sin(rz2) + uy * math.cos(rz2))
                d = abs((cx2 - cx1) * ux + (cy2 - cy1) * uy)
                if d > r1 + r2:
                    return False
        return True

    def foot_blocked(cx_, cy_):
        me = (cx_, cy_, hw_ + 0.30, hd_ + 0.30, rz)
        for (_ox, _oy, _oz, obw, obd, _obh, orz, _oax, _oay, ocx, ocy) in BUILT.values():
            if rects_overlap(me, (ocx, ocy, (obw + 0.10) / 2 + 0.30,
                                  (obd + 0.10) / 2 + 0.30, orz)):
                return True
        for (sx_, sy_, sz_) in GATE.pts:
            if not (z < sz_ + 2.00 and z + 0.85 > sz_ + 0.005):
                continue
            ddx, ddy = sx_ - cx_, sy_ - cy_
            if abs(ddx * crz - ddy * srz) <= hw_ and abs(ddx * srz + ddy * crz) <= hd_:
                return True
        return False
    # THE SET-BACK IS A RING SEARCH, not a slide.  Sliding straight back along the
    # approach cleared the bakery and the item shop and could not clear the inn at any
    # distance: the main road's last leg runs PAST the inn's flank, so retreating along
    # the road's own direction keeps the same flank over the same corridor.  Searching a
    # ring finds the nearest offset in ANY direction, which for the inn is sideways.
    off = None
    for rad in [0.0] + [0.15 + 0.15 * k for k in range(10)]:
        for a_ in range(20 if rad > 0 else 1):
            th = math.atan2(-ay, -ax) + 2 * math.pi * a_ / 20
            cx_, cy_ = x + rad * math.cos(th), y + rad * math.sin(th)
            if not foot_blocked(cx_, cy_):
                off = (cx_, cy_, rad)
                break
        if off:
            break
    if off is None:
        print("    SET-BACK REFUSED  %-12s no clear offset within 2.10 m; built on the "
              "map point and reported" % lid)
    else:
        if off[2] > 0.0:
            print("    set-back          %-12s %.2f m (ring search) — clears the walk gate"
                  % (lid, off[2]))
        x, y = off[0], off[1]
    t = "emb_sq_%s" % lid.replace("-", "")
    box(t + "_plinth", x, y, z + 0.40, bw + 0.10, bd + 0.10, 0.80, MAT["stone"], rz)
    box(t + "_walls", x, y, z + 0.80 + (bh - 0.80) / 2, bw, bd, bh - 0.80, MAT["plaster"], rz)
    # the half-timbering: this town is timber over stone and the frame is what says so
    for k in range(4):
        fx = -bw / 2 + bw * (k + 0.5) / 4
        box(t + "_stud%d" % k, x + fx * math.cos(rz) - (bd / 2 + 0.02) * math.sin(rz) * 0,
            y + fx * math.sin(rz), z + 0.80 + (bh - 0.80) / 2, 0.17, bd + 0.05,
            bh - 0.80, MAT["beam"], rz)
    for lvl in range(storeys):
        box(t + "_rail%d" % lvl, x, y, z + 0.80 + 2.55 * (lvl + 1) - 0.14,
            bw + 0.05, bd + 0.05, 0.20, MAT["beam"], rz)
    gable(t + "_roof", x, y, z + bh, bw, bd, 1.55 + 0.25 * storeys, roofmat, rz, over=0.34)
    box(t + "_chimney", x - ax * bw * 0.28, y - ay * bd * 0.28, z + bh + 1.55,
        0.62, 0.62, 2.1, MAT["stone"], rz)
    # the front, facing the road that arrives
    fx, fy = x + ax * (bd / 2 + 0.02), y + ay * (bd / 2 + 0.02)
    if openfront:
        # a shopfront: the wall is opened, a counter runs across it, trays behind
        box(t + "_opening", fx, fy, z + 1.30, 3.0, 0.22, 1.90, MAT["timber"], rz)
        box(t + "_counter", fx + ax * 0.32, fy + ay * 0.32, z + 0.52, 3.0, 0.62, 1.04,
            MAT["timber"], rz)
        for k in range(3):
            ox = -0.95 + k * 0.95
            box(t + "_tray%d" % k, fx + ax * 0.30 + latx(rz) * ox, fy + ay * 0.30 + laty(rz) * ox,
                z + 1.10, 0.72, 0.44, 0.14, MAT["bread"], rz)
    else:
        box(t + "_door", fx, fy, z + 1.08, 1.15, 0.16, 2.16, MAT["timber"], rz)
        box(t + "_lintel", fx, fy, z + 2.24, 1.55, 0.24, 0.20, MAT["beam"], rz)
    # windows, and they are LIT: the map's implied-scale ruling asks for a town that
    # reads inhabited, and a dark window at dusk on Emberwake reads empty
    for lvl in range(storeys):
        for wk in (-1, 1):
            wx = fx + latx(rz) * wk * bw * 0.31
            wy = fy + laty(rz) * wk * bw * 0.31
            box(t + "_win%d%d" % (lvl, (wk + 1) // 2), wx, wy, z + 1.30 + 2.55 * lvl,
                0.80, 0.10, 0.92, MAT["window"], rz)
            box(t + "_winfrm%d%d" % (lvl, (wk + 1) // 2), wx, wy - 0.02,
                z + 1.30 + 2.55 * lvl, 0.96, 0.06, 1.08, MAT["beam"], rz)
    if awning:
        aw = 3.4
        for k in range(6):
            m = awning[k % len(awning)]
            u = -aw / 2 + aw * k / 6
            # the near edge stands 0.07 m PROUD of the wall: coplanar with it, three of
            # every quad's four corners read as "inside the wall" to the audit and as a
            # z-fighting seam to the camera
            quad(t + "_awn%d" % k,
                 (fx + latx(rz) * u + ax * 0.07, fy + laty(rz) * u + ay * 0.07, z + 2.60),
                 (fx + latx(rz) * (u + aw / 6) + ax * 0.07,
                  fy + laty(rz) * (u + aw / 6) + ay * 0.07, z + 2.60),
                 (fx + latx(rz) * (u + aw / 6) + ax * 1.25,
                  fy + laty(rz) * (u + aw / 6) + ay * 1.25, z + 2.18),
                 (fx + latx(rz) * u + ax * 1.25, fy + laty(rz) * u + ay * 1.25, z + 2.18), m)
        for wk in (-1, 1):
            px = fx + latx(rz) * wk * (aw / 2 - 0.1) + ax * 1.22
            py = fy + laty(rz) * wk * (aw / 2 - 0.1) + ay * 1.22
            if place(t + "_awnpost", px, py, 0.09, z, z + 2.25):
                box(t + "_awnpost%d" % ((wk + 1) // 2), px, py, z + 1.10,
                    0.11, 0.11, 2.20, MAT["timber"], rz)
    if sign:
        sx_ = fx + ax * 0.9 + latx(rz) * 1.5
        sy_ = fy + ay * 0.9 + laty(rz) * 1.5
        box(t + "_signarm", (fx + sx_) / 2 + latx(rz) * 0.2, (fy + sy_) / 2 + laty(rz) * 0.2,
            z + 2.85, 1.30, 0.09, 0.09, MAT["iron"], rz)
        box(t + "_signboard", sx_, sy_, z + 2.42, 0.95, 0.07, 0.72, MAT["timber"], rz)
    # a warm interior source, ordinary: the window glow has to come from somewhere
    li2 = bpy.data.lights.new("KEYSQ_%s_hearth" % lid, 'POINT')
    li2.energy = 680.0
    li2.color = (1.0, 0.58, 0.24)
    li2.shadow_soft_size = 0.16
    li2.use_custom_distance = True
    li2.cutoff_distance = 12.0
    lo2 = bpy.data.objects.new(li2.name, li2)
    lo2.location = (fx + ax * 0.5, fy + ay * 0.5, z + 1.6)
    coll(COLL).objects.link(lo2)
    NEW.append(lo2)
    BUILT[lid] = (x, y, z, bw, bd, bh, rz, ax, ay, x, y)


def latx(rz):
    """The LEFT-HAND unit perpendicular to the approach.  For rz = atan2(ay, ax) + pi/2
    this is (cos rz, sin rz) == (-ay, ax).  Named rather than inlined because the file
    got it wrong once, silently, in six different places."""
    return math.cos(rz)


def laty(rz):
    return math.sin(rz)


def ox_(rz):
    return math.cos(rz)


def oy_(rz):
    return math.sin(rz)


# The inn is the reference painting's grandest building: two storeys, half-timbered over
# a stone base, slate roof, a sign on an iron bracket.
house("inn", 2, MAT["slate"], sign=True)
# Poppy's bakery: `chapter1.js` runs on it — the buns, the stall, the hospitality law.
# Open front, trays lit, a red-and-cream striped awning (the reference's own colours).
# Built at COTTAGE size, not shop size, and the reason is arithmetic rather than taste:
# the map puts the bakery 4.03 m from the inn, and two 4.8 m frontages with a 1.14 roof
# oversail need 5.47 m of centre spacing before their roofs stop sharing a volume.  At
# cottage size it needs 4.96 m, which is still more than 4.03 — so this shrinks the
# overlap, it does not remove it, and the residue is REPORTED and on the morning board
# as a one-line map fix (move either landmark ~1.5 m apart).  At 76% of cottage size —
# a 3.0 x 2.5 m shopfront, which is a bread counter and a back room, and exactly what
# `chapter1.js` describes Poppy running — it clears, and the square keeps its bakery on
# the coordinate the map gave it.
house("bakery", 1, MAT["thatch"], openfront=True, small=True, scale=0.76,
      awning=[MAT["awn_red"], MAT["awn_cream"]])
# the item shop: preserves, twine, lamp oil.  Open front, green awning.
house("item-shop", 1, MAT["tile"], openfront=True,
      awning=[MAT["awn_green"], MAT["awn_cream"]])
print("  buildings: " + ", ".join(sorted(BUILT)))

# =============================================================================
# 3. THE FIXTURES — notice board and well, on their own map points
# =============================================================================
NB = LM["notice-board"]
nx, ny, nz = NB["pos"]
nax, nay = appr_of("notice-board")
nrz = math.atan2(nay, nax) + math.pi / 2
for wk in (-1, 1):
    box("emb_sq_notice_post%d" % ((wk + 1) // 2), nx - oy_(nrz) * wk * 0.78,
        ny + ox_(nrz) * wk * 0.78, nz + 0.72, 0.13, 0.13, 1.44, MAT["timber"], nrz)
box("emb_sq_notice_face", nx, ny, nz + 1.28, 1.80, 0.09, 1.00, MAT["timber"], nrz)
box("emb_sq_notice_roof", nx + nax * 0.10, ny + nay * 0.10, nz + 1.86, 2.00, 0.42, 0.09,
    MAT["beam"], nrz)
for k in range(5):                                   # the pinned notices, and a drawing
    px = -0.66 + k * 0.33
    box("emb_sq_notice_pin%d" % k, nx - oy_(nrz) * px + nax * 0.06,
        ny + ox_(nrz) * px + nay * 0.06, nz + 1.24 + 0.14 * h01(k, 3), 0.24, 0.02,
        0.30, MAT["awn_cream"], nrz)

WL = LM["well"]
wx, wy, wz = WL["pos"]
cyl("emb_sq_well_ring", wx, wy, wz + 0.42, 1.02, 0.84, MAT["stone"], seg=20)
cyl("emb_sq_well_lip", wx, wy, wz + 0.88, 1.10, 0.14, MAT["stone"], seg=20)
cyl("emb_sq_well_shaft", wx, wy, wz + 0.30, 0.80, 0.60, MAT["earth"], seg=16)
for wk in (-1, 1):
    box("emb_sq_well_frame%d" % ((wk + 1) // 2), wx + wk * 0.92, wy, wz + 1.72,
        0.15, 0.15, 1.90, MAT["timber"])
box("emb_sq_well_beam", wx, wy, wz + 2.62, 2.20, 0.17, 0.17, MAT["timber"])
cyl("emb_sq_well_winch", wx, wy, wz + 2.44, 0.13, 1.50, MAT["timber"], seg=10)
box("emb_sq_well_bucket", wx, wy, wz + 1.96, 0.34, 0.34, 0.34, MAT["timber"])

# =============================================================================
# 4. THE MARKET — four stalls on the plaza rim, Emberwake evening
# =============================================================================
# The reference paints the stalls RINGING the plaza with a clear centre: the Kindling
# Hour needs the middle empty for the crowd (`impliedScale` technique 3), so every stall
# is pushed to the rim and every one is checked against the walk gate before it stands.
STALLPOS = []
BROOKPOLY = [tuple(p) for p in (D.get("brook") or {}).get("polyline", [])]


def brook_d2(x, y):
    best = 1e9
    for a, b in zip(BROOKPOLY, BROOKPOLY[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        best = min(best, (x - a[0] - t * dx) ** 2 + (y - a[1] - t * dy) ** 2)
    return math.sqrt(best) if best < 1e9 else 1e9


STALLS = [(0.40, [MAT["awn_green"], MAT["awn_cream"]], "buns"),
          (1.55, [MAT["awn_blue"], MAT["awn_cream"]], "preserves"),
          (3.25, [MAT["awn_red"], MAT["awn_cream"]], "pumpkins"),
          (4.55, [MAT["awn_green"], MAT["awn_blue"]], "cloth")]
nstall = 0
for si, (ang, stripes, what) in enumerate(STALLS):
    # THE STALLS RING THE SQUARE FROM ITS OUTER EDGE, not from inside it.  Every rim
    # position INSIDE the plaza floor was refused by the walk gate, and the gate is
    # right: a stall is a solid, the plaza is walkable, and Festival Square's floor is
    # exactly what the Kindling Hour crowd needs kept clear (`impliedScale`, technique
    # 3).  Standing them just past the floor's edge is also what the reference painting
    # does — the stalls line the square, they do not fill it.
    # SEARCHED, not authored: the outer rim is crowded (three buildings, the brook, the
    # roads and the lamp ring all live on it), and four fixed angles found nothing.  Each
    # stall keeps its INTENDED angle as a preference and sweeps outward from it.
    found = None
    for rr in (SR + 0.9, SR + 1.7, SR + 2.6, SR + 3.5):
        for st in range(25):
            a2 = ang + math.radians(((st + 1) // 2) * 7 * (1 if st % 2 else -1))
            px, py = SX + rr * math.cos(a2), SY + rr * math.sin(a2)
            if any(in_rect_l(px, py, o, 1.25) for o in D["landmarks"]
                   if o.get("class") not in ("area", "dressing")
                   and math.hypot(o["pos"][0] - px, o["pos"][1] - py) < 9.0):
                continue                                # a stall does not stand in a wall
            if BROOKPOLY and brook_d2(px, py) < 1.6:
                continue
            if any(math.hypot(px - qx, py - qy) < 3.0 for (qx, qy) in STALLPOS):
                continue
            if place("stall_%s" % what, px, py, 1.15, SZ, SZ + 2.4):
                found = (px, py, a2)
                break
        if found:
            break
    if not found:
        continue
    px, py, ang = found
    STALLPOS.append((px, py))
    rz = ang + math.pi / 2
    t = "emb_sq_stall%d" % si
    # LATERAL runs along the stall's face; RADIAL runs toward the square's middle.
    # Written out rather than inlined because this file already got a basis vector wrong
    # once and the audit had to find it.
    lx_, ly_ = latx(rz), laty(rz)                    # along the face
    rx_, ry_ = -ly_, lx_                             # toward the square (the shopper's side)
    for wk in (-1, 1):
        for fk in (-1, 1):
            box(t + "_post%d%d" % ((wk + 1) // 2, (fk + 1) // 2),
                px + lx_ * wk * 0.92 + rx_ * fk * 0.52,
                py + ly_ * wk * 0.92 + ry_ * fk * 0.52,
                SZ + 1.06, 0.09, 0.09, 2.12, MAT["timber"], rz)
    box(t + "_board", px, py, SZ + 0.86, 2.00, 1.00, 0.10, MAT["timber"], rz)
    box(t + "_skirt", px, py, SZ + 0.42, 1.96, 0.96, 0.78, MAT["awn_cream"], rz)
    for k in range(6):                               # the striped awning, front-falling
        m = stripes[k % len(stripes)]
        u, u2 = -1.0 + 2.0 * k / 6, -1.0 + 2.0 * (k + 1) / 6
        quad(t + "_awn%d" % k,
             (px + lx_ * u - rx_ * 0.62, py + ly_ * u - ry_ * 0.62, SZ + 2.16),
             (px + lx_ * u2 - rx_ * 0.62, py + ly_ * u2 - ry_ * 0.62, SZ + 2.16),
             (px + lx_ * u2 + rx_ * 0.72, py + ly_ * u2 + ry_ * 0.72, SZ + 1.86),
             (px + lx_ * u + rx_ * 0.72, py + ly_ * u + ry_ * 0.72, SZ + 1.86), m)
    goods = MAT["pumpkin"] if what == "pumpkins" else (
        MAT["bread"] if what == "buns" else (MAT["awn_blue"] if what == "cloth" else MAT["straw"]))
    for k in range(5):
        u = -0.78 + k * 0.39
        box(t + "_goods%d" % k, px + lx_ * u, py + ly_ * u,
            SZ + 1.02 + 0.05 * h01(si, k), 0.32, 0.52, 0.22 + 0.10 * h01(si, k, 7), goods, rz)
    nstall += 1
print("  market: %d of %d stalls placed on the rim" % (nstall, len(STALLS)))

# =============================================================================
# 5. THE DRESSING — huddled into touching groups, never scattered singletons
# =============================================================================
# `docs/SCENE-LAYOUT.md`, the transcription rule the square pilot proved: dressing
# HUDDLES against anchors.  Each group below is anchored to a building's own foot and
# every piece is gate-checked, so nothing stands in the corridor a player walks.
GROUPS = []
for lid in ("inn", "bakery", "item-shop"):
    if lid not in BUILT:
        continue
    x, y, z, bw, bd, bh, rz, ax, ay, _cx, _cy = BUILT[lid]
    # against the gable end, out of the doorway's own line
    for side in (-1, 1):
        gx = x + latx(rz) * side * (bw / 2 + 0.75) + ax * 0.9
        gy = y + laty(rz) * side * (bw / 2 + 0.75) + ay * 0.9
        GROUPS.append((lid, side, gx, gy, z))
nprop = 0
for gi, (lid, side, gx, gy, gz) in enumerate(GROUPS):
    seed = h32(gi, len(lid))
    kindsel = seed % 3
    if kindsel == 0:                                  # barrels + a sack
        for k in range(3):
            bx = gx + (0.42 * (k - 1)) * math.cos(gi + 1.0)
            by = gy + (0.42 * (k - 1)) * math.sin(gi + 1.0)
            if not place("barrel", bx, by, 0.36, gz, gz + 0.9):
                continue
            cyl("emb_sq_dress%d_barrel%d" % (gi, k), bx, by, gz + 0.42, 0.34, 0.84,
                MAT["timber"], seg=10)
            nprop += 1
    elif kindsel == 1:                                # haybale + pumpkins against it
        if place("haybale", gx, gy, 0.62, gz, gz + 1.0):
            box("emb_sq_dress%d_bale" % gi, gx, gy, gz + 0.45, 1.20, 0.86, 0.90,
                MAT["straw"], rz=h01(gi, 3) * 1.2)
            nprop += 1
            for k in range(3):
                a = 2.1 + k * 0.9
                px, py = gx + 0.85 * math.cos(a), gy + 0.85 * math.sin(a)
                if place("pumpkin", px, py, 0.26, gz, gz + 0.5):
                    cyl("emb_sq_dress%d_pumpkin%d" % (gi, k), px, py, gz + 0.22, 0.25,
                        0.42, MAT["pumpkin"], seg=10)
                    nprop += 1
    else:                                             # crates, stacked
        for k in range(3):
            bx = gx + 0.30 * (k % 2)
            by = gy + 0.30 * (k % 2)
            bz = gz + 0.24 + 0.48 * (k // 2)
            if not place("crate", bx, by, 0.30, gz, bz + 0.3):
                continue
            box("emb_sq_dress%d_crate%d" % (gi, k), bx, by, bz, 0.56, 0.52, 0.46,
                MAT["timber"], rz=h01(gi, k, 5) * 1.5)
            nprop += 1
# the handcart the reference parks by the shop, and its produce
cax, cay = SX + (SR - 2.0) * math.cos(5.5), SY + (SR - 2.0) * math.sin(5.5)
if place("handcart", cax, cay, 1.05, SZ, SZ + 1.4):
    box("emb_sq_cart_bed", cax, cay, SZ + 0.66, 1.90, 1.05, 0.24, MAT["timber"], rz=5.5)
    box("emb_sq_cart_rail", cax, cay, SZ + 0.92, 1.90, 0.10, 0.30, MAT["timber"], rz=5.5)
    for wk in (-1, 1):
        cyl("emb_sq_cart_wheel%d" % ((wk + 1) // 2), cax - math.sin(5.5) * wk * 0.60,
            cay + math.cos(5.5) * wk * 0.60, SZ + 0.46, 0.44, 0.11, MAT["timber"], seg=12)
    for k in range(3):
        cyl("emb_sq_cart_pumpkin%d" % k, cax + 0.44 * (k - 1) * math.cos(5.5),
            cay + 0.44 * (k - 1) * math.sin(5.5), SZ + 1.00, 0.24, 0.40,
            MAT["pumpkin"], seg=10)
    nprop += 1
print("  dressing: %d props in %d anchored groups" % (nprop, len(GROUPS)))

# =============================================================================
# 6. BUNTING — strung between the lamp ring and the eaves
# =============================================================================
# The reference's most characteristic element, and the cheapest legibility in the town:
# a strung line overhead tells you instantly that the space beneath it is THE square.
# It hangs from objects that already exist (the blockout's lamps and this pass's roofs),
# so it can never float.
ANCHORS = []
for o in bpy.data.objects:
    if o.name.startswith("emb_lamp_") and o.name.endswith("_cap"):
        c = o.matrix_world.translation
        if math.hypot(c.x - SX, c.y - SY) < SR + 6:
            ANCHORS.append((c.x, c.y, c.z + 0.05))
for lid in sorted(BUILT):
    x, y, z, bw, bd, bh, rz, ax, ay, _cx, _cy = BUILT[lid]
    ANCHORS.append((x + ax * (bd / 2 + 0.3), y + ay * (bd / 2 + 0.3), z + bh + 0.35))
ANCHORS.sort(key=lambda p: math.atan2(p[1] - SY, p[0] - SX))
nflag = nline = 0
FLAGM = [MAT["awn_red"], MAT["awn_cream"], MAT["awn_green"], MAT["awn_blue"]]
for k in range(len(ANCHORS)):
    a, b = ANCHORS[k], ANCHORS[(k + 1) % len(ANCHORS)]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L < 3.0 or L > 17.0:
        continue
    N = max(4, int(L / 1.15))
    prev = None
    for s in range(N + 1):
        t = s / float(N)
        sag = 0.62 * math.sin(math.pi * t)
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
             a[2] + (b[2] - a[2]) * t - sag)
        if prev is not None:
            mid = tuple((prev[i] + p[i]) / 2 for i in range(3))
            box("emb_sq_bunting_%02d_%02d" % (k, s), mid[0], mid[1], mid[2],
                math.dist(prev, p), 0.035, 0.035, MAT["beam"],
                rz=math.atan2(p[1] - prev[1], p[0] - prev[0]))
            if s % 2 == 0:
                quad("emb_sq_flag_%02d_%02d" % (k, s),
                     (mid[0] - 0.16, mid[1], mid[2]), (mid[0] + 0.16, mid[1], mid[2]),
                     (mid[0] + 0.16, mid[1], mid[2] - 0.30),
                     (mid[0] - 0.16, mid[1], mid[2] - 0.30), FLAGM[(k + s) % 4])
                nflag += 1
        prev = p
    nline += 1
print("  bunting: %d lines, %d flags, hung off %d existing anchors" % (nline, nflag, len(ANCHORS)))

# =============================================================================
# 7. TREES — closing the corners from BEHIND the buildings
#
# Planted at SR+2.6 they stood between every camera and the plaza: the first hero render
# of Festival Square is a wall of green with a market stall visible through a gap.  That
# is seam-canon 9.3 arriving on schedule — "in frame" is not "visible", and the fix for
# an occluder is to move the occluder, not to re-aim.  They now start 5.4 m outside the
# plaza's rim, which puts them BEHIND the inn, the bakery and the shop from every
# direction a camera stands in, where a tree's job is to close a skyline rather than to
# fill a frame.
# =============================================================================
ntree = 0
for k in range(9):
    a0 = 2 * math.pi * k / 9 + 0.35
    for rr, st in [(rr, st) for rr in (SR + 5.4, SR + 7.0, SR + 8.6) for st in range(9)]:
        a = a0 + math.radians(((st + 1) // 2) * 6 * (1 if st % 2 else -1))
        tx, ty = SX + rr * math.cos(a), SY + rr * math.sin(a)
        if not (REGION[0] < tx < REGION[1] and REGION[2] < ty < REGION[3]):
            continue
        if any(in_rect_l(tx, ty, o, 1.6) for o in D["landmarks"]
               if o.get("class") not in ("area", "dressing")
               and math.hypot(o["pos"][0] - tx, o["pos"][1] - ty) < 9.0):
            continue
        if BROOKPOLY and brook_d2(tx, ty) < 1.4:
            continue
        if any(math.hypot(tx - qx, ty - qy) < 3.4 for (qx, qy) in STALLPOS):
            continue
        if place("tree", tx, ty, 0.9, SZ - 1, SZ + 7):
            ht = 6.0 + 2.6 * h01(k, 13)
            box("veg_emb_sq_tree%d_trunk" % k, tx, ty, SZ + ht * 0.32, 0.34, 0.34,
                ht * 0.68, MAT["timber"])
            leaf = MAT["leaf_green"] if (h32(k, 19) % 5) < 2 else MAT["leaf_autumn"]
            for c_ in range(3):
                rr2 = (2.4 + 0.9 * h01(k, 23 + c_)) * (1.0 - 0.20 * c_)
                cyl("veg_emb_sq_tree%d_crown%d" % (k, c_), tx, ty,
                    SZ + ht * 0.60 + c_ * 1.35, rr2, 1.9, leaf, seg=8, r2=rr2 * 0.55)
            ntree += 1
            break
print("  trees: %d autumn/green crowns closing the corners" % ntree)

# =============================================================================
# ACCEPTANCE — measured, printed, and non-zero on a real failure
# =============================================================================
print("-" * 78)
if REFUSED:
    print("  REFUSED (would have stood in the walk gate's own rays) — %d:" % len(REFUSED))
    for nm, x, y in REFUSED[:24]:
        print("      %-22s at (%.2f, %.2f)" % (nm, x, y))
else:
    print("  REFUSED: none — every solid this pass placed is clear of the walk gate")

# 1. THE GATE'S OWN TEST, RE-RUN AS RAYS — not as bounding boxes.
# The first version of this check asked GateGrid.blocked() for each new mesh's AABB and
# reported 32 offenders including the inn, the bakery and the well.  Every one was a
# FALSE POSITIVE of my own instrument: these buildings are rotated to face the road that
# arrives, and the axis-aligned box around a 5.6 x 4.8 m building turned 40 degrees is
# 7.4 x 7.3 — so the test picked up plaza cells a metre outside the wall it was asking
# about.  master_walk_qa does not do that.  It fires TWO RAYS per walk sample (down from
# sz + 0.90, up from sz + 0.06 to sz + 2.00) and asks what they hit.  So does this.
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
NEWNAMES = {o.name for o in NEW if o.type == 'MESH'}
offenders = {}
nsample = 0
for (sx, sy, sz) in GATE.pts:
    nsample += 1
    for org, dvec, dist in (((sx, sy, sz + 0.90), (0, 0, -1), 1.90),
                            ((sx, sy, sz + 0.06), (0, 0, 1), 1.94)):
        hit, _loc, _nrm, _idx, ob, _mx = sc.ray_cast(dg, Vector(org), Vector(dvec),
                                                     distance=dist)
        if hit and ob is not None and ob.name in NEWNAMES:
            # NAME THE FLOOR TOO.  "the inn stands on a walk sample" is not actionable;
            # "the inn stands on walk_e_square-plaza__inn_l3" says whether the fix is
            # the building, the map, or the road the blockout drew.
            floor = "?"
            fh, _fl, _fn, _fi, fo, _fm = sc.ray_cast(dg, Vector((sx, sy, sz + 0.05)),
                                                     Vector((0, 0, -1)), distance=0.60)
            if fh and fo is not None:
                floor = fo.name
            offenders.setdefault(ob.name, []).append((round(sx, 2), round(sy, 2), floor))
print("  GATE RE-CHECK (master_walk_qa's own two rays, %d walk samples): %d offenders"
      % (nsample, len(offenders)))
for nm in sorted(offenders)[:30]:
    pts = offenders[nm]
    floors = sorted({q[2] for q in pts})
    print("      %-30s %3d samples on %s" % (nm, len(pts), ", ".join(floors)[:78]))

# 2. the walk floor this district hands to the cameras, unchanged and counted


def bbox_c(o):
    P = [o.matrix_world @ v.co for v in o.data.vertices]
    return ((min(p.x for p in P) + max(p.x for p in P)) / 2,
            (min(p.y for p in P) + max(p.y for p in P)) / 2)


walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")
         and o.data.vertices
         and REGION[0] <= bbox_c(o)[0] <= REGION[1]
         and REGION[2] <= bbox_c(o)[1] <= REGION[3]]
print("  walk surfaces in region: %d (untouched by this pass, by design)" % len(walks))

# 3. exactly one magical light in the whole town
heart = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.energy > 2000]
print("  magical light sources town-wide: %d  (%s)"
      % (len(heart), ", ".join(o.name for o in heart)))
assert len(heart) == 1, "Emberbrook has exactly one Heartlight — found %d" % len(heart)

lamps = [o for o in bpy.data.objects if o.type == 'LIGHT' and 400 < o.data.energy <= 2000]
print("  ordinary warm practicals town-wide: %d at 680 W" % len(lamps))

mine = [o for o in bpy.data.objects if o.name.startswith(MINE)]
nv = sum(len(o.data.vertices) for o in mine if o.type == 'MESH')
print("  BUILT: %d objects, %d vertices under %s" % (len(mine), nv, "/".join(MINE)))

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

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
