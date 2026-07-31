"""emb_home_build.py — HOME ROW, Emberbrook's third real district.

    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_home_build.py \
        --python-exit-code 1 -- [save] [--digest]

Where the cast lives, and the second leg of Lake's dusk round.  `p-homerow` is
`lake-home` (the keeper's cottage), `elder-house` (Rowan's), `hillside-cottage`
(Mara & Pip's) and `home-lane-end` — the hilltop bench with the whole village in view,
which the map's own note reserves for "quiet story beats".  The brook rises under that
hill and runs down past the row toward the square.

CONTRACT, identical to `emb_square_build.py` and `emb_lane_build.py`, and the sameness
IS the deliverable: own a prefix set (`emb_hr_`, `bar_emb_hr_`, `veg_emb_hr_`,
`KEYHR_`) plus the `lm_<member>_*` massing it replaces; never touch `emb_lamp_*` (map
canon, and it stages Lake's rounds), `emb_ground_*`, `water_*` or any `walk_`/`bar_`
the blockout built; never rebuild the walk network; gate every solid with
`district_lib.GateGrid`; count and print every refusal; membership is the UNION of the
parcel's array and every landmark whose own `district` names this district.

THE HOUSE RULE THIS DISTRICT INHERITS, written down after it was learned four separate
times in one night (lamp feet, market stalls, the square's trees, Pond Lane's washing
lines): A FREE-STANDING SOLID IS SEARCHED, NEVER AUTHORED.  Every gate, hedge, wood
stack and herb bed below picks its own foot out of a sweep and reports a refusal rather
than standing somewhere a player walks.

ONE CANON DETAIL THAT IS GEOMETRY, NOT FLAVOUR.  `lake-home` is the KEEPER'S cottage.
`chapter1.js`: above the hearth, Grandmother's portrait; beneath it, *"an empty brass
hook, worn bright — the lighter's place, between rounds."*  The interior is another
lane's (`emb-lake-int`), but the OUTSIDE has to say keeper: the only door in the town
with a lantern bracket beside it and a worn stone step, because somebody has left
through it at dusk every day for forty years.
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
PARCEL = next(p for p in D["parcels"] if p["id"] == "p-homerow")
DISTRICT = "homerow"
# ... MINUS the implied-scale furniture, which is the BLOCKOUT'S and must survive this
# pass.  `district: homerow` also names the two vista clusters and the closed upper lane;
# retiring their massing because they share a district would have deleted three of the
# five things the user's impliedScale ruling asks for, and nothing here rebuilds them.
def _mine(i):
    l = LM[i]
    return (l.get("class") != "dressing"
            and "closed" not in (l.get("name") or "").lower())


MEMBERS = sorted(i for i in ({m for m in PARCEL["members"] if m in LM} |
                             {l["id"] for l in D["landmarks"]
                              if l.get("district") == DISTRICT}) if _mine(i))
B = PARCEL["bounds"]
REGION = (B["min"][0] - 3, B["max"][0] + 3, B["min"][1] - 3, B["max"][1] + 3)
MINE = ("emb_hr_", "bar_emb_hr_", "veg_emb_hr_", "KEYHR_")
COLL = "EMB_HOMEROW"
BPOLY = [tuple(p) for p in (D.get("brook") or {}).get("polyline", [])]

print("=" * 78)
print("HOME ROW — Emberbrook's third real district")
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
       ("grass", "earth", "road", "stone", "timber", "plaster", "thatch", "slate",
        "tile", "leaf_autumn", "leaf_green", "iron", "window", "lamp_glass")}
for k in ("awn_red", "awn_cream", "awn_green", "awn_blue", "straw", "beam", "pumpkin"):
    m = bpy.data.materials.get("emb_mat_" + k)
    if m:
        MAT[k] = m
MAT.setdefault("beam", MAT["timber"])


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


MAT["hedge"] = newmat("emb_mat_hedge", (0.18, 0.26, 0.13, 1))
MAT["herb"] = newmat("emb_mat_herb", (0.30, 0.36, 0.20, 1))
MAT["brass"] = newmat("emb_mat_brass", (0.52, 0.38, 0.14, 1), rough=0.35)

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


def gable(name, cx, cy, cz, sx, sy, h, m, rz=0.0, over=0.0):
    hx, hy = sx / 2.0 + over, sy / 2.0 + over
    c, s = math.cos(rz), math.sin(rz)

    def Pt(dx, dy, dz):
        return (cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz)

    v = [Pt(-hx, -hy, 0), Pt(hx, -hy, 0), Pt(hx, hy, 0), Pt(-hx, hy, 0),
         Pt(-hx * 0.94, 0, h), Pt(hx * 0.94, 0, h)]
    return mesh(name, v, [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (1, 2, 5), (3, 0, 4)], m)


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


sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def ground_at(x, y, top=16.0):
    hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)),
                                           distance=30.0)
    return (loc.z, ob.name) if hit else (None, None)


GUARD = WalkGuard(REGION)
GATE = GateGrid(REGION, GUARD)
print("  gate grid: %d walk samples inside the region" % len(GATE.pts))
REFUSED = []


def free(what, x, y, r, z0, z1):
    if GATE.clear_pt(x, y, r, z0, z1):
        return True
    REFUSED.append((what, round(x, 2), round(y, 2)))
    return False


def search_foot(what, cx, cy, radii, r, dz0, dz1, avoid_walk=True):
    """The house rule, factored: sweep a ring for a foot that has real ground under it,
    stands clear of the walk gate's rays and is not in the brook.  Deterministic
    (fixed candidate order), and a refusal is counted rather than silently dropped."""
    for rad in radii:
        for k in range(16):
            th = 2 * math.pi * k / 16
            x, y = cx + rad * math.cos(th), cy + rad * math.sin(th)
            if not (REGION[0] < x < REGION[1] and REGION[2] < y < REGION[3]):
                continue
            gz, gname = ground_at(x, y)
            if gz is None:
                continue
            if avoid_walk and (gname or "").startswith(("walk_", "water_")):
                continue
            if BPOLY and brook_d(x, y) < 1.3:
                continue
            if not GATE.clear_pt(x, y, r, gz + dz0, gz + dz1):
                continue
            return (x, y, gz)
    REFUSED.append((what, round(cx, 2), round(cy, 2)))
    return None


BUILT = {}


def cottage(lid, roofmat, keeper=False, storeys=1):
    """A Home Row cottage.  Footprint is the blockout's own so the ground and the
    doorstep still fit it; only the art changes.  The set-back is the square pass's ring
    search — a nudge, not a move — and it tests the ROTATED rectangle against the walk
    gate's own samples, which is the only version of that test that ever worked."""
    l = LM[lid]
    x, y, z = l["pos"]
    kind = l.get("kind") or ""
    # HOME ROW IS THE DENSEST CORNER OF THE TOWN.  After the cottage move, Rowan's
    # house and Mara & Pip's stand 4.0 m apart with the elder-house lane threaded
    # between them, and at 4.8 m frontages neither can clear the ribbon at any offset.
    # A hill cottage is a small building; 3.4 x 2.9 is a room, a hearth and a stair,
    # which is what chapter1.js describes anyway.
    big = kind.startswith("shop") or kind == "building"
    bw, bd = (3.4, 2.9) if big else (3.2, 2.7)
    ax, ay = appr_of(lid)
    rz = math.atan2(ay, ax) + math.pi / 2
    bh = 2.45 * storeys + 0.55
    hw_, hd_ = (bw + 0.10) / 2 + 0.10, (bd + 0.10) / 2 + 0.10
    crz, srz = math.cos(-rz), math.sin(-rz)

    def blocked(cx_, cy_):
        for (bx2, by2, obw, obd, orz) in BUILT.values():
            # separating-axis on the two ORIENTED rectangles.  The first draft used an
            # axis-aligned delta with a max() fudge and refused all three cottages at
            # every offset — a bound that loose is not a test, it is a veto.
            over = True
            for (cx0, cy0, hwA, hdA, rzA, cx1, cy1, hwB, hdB, rzB) in (
                    (cx_, cy_, hw_, hd_, rz, bx2, by2, obw / 2 + 0.35, obd / 2 + 0.35, orz),
                    (bx2, by2, obw / 2 + 0.35, obd / 2 + 0.35, orz, cx_, cy_, hw_, hd_, rz)):
                for (ux, uy) in ((math.cos(rzA), math.sin(rzA)),
                                 (-math.sin(rzA), math.cos(rzA))):
                    rA = hwA * abs(ux * math.cos(rzA) + uy * math.sin(rzA)) + \
                        hdA * abs(-ux * math.sin(rzA) + uy * math.cos(rzA))
                    rB = hwB * abs(ux * math.cos(rzB) + uy * math.sin(rzB)) + \
                        hdB * abs(-ux * math.sin(rzB) + uy * math.cos(rzB))
                    if abs((cx1 - cx0) * ux + (cy1 - cy0) * uy) > rA + rB:
                        over = False
                        break
                if not over:
                    break
            if over:
                return True
        for (sx_, sy_, sz_) in GATE.pts:
            if not (z < sz_ + 2.00 and z + 0.85 > sz_ + 0.005):
                continue
            ddx, ddy = sx_ - cx_, sy_ - cy_
            if abs(ddx * crz - ddy * srz) <= hw_ and abs(ddx * srz + ddy * crz) <= hd_:
                return True
        return False

    off = None
    for rad in [0.0] + [0.15 + 0.15 * k for k in range(14)]:
        for a_ in range(20 if rad > 0 else 1):
            th = math.atan2(-ay, -ax) + 2 * math.pi * a_ / 20
            cx_, cy_ = x + rad * math.cos(th), y + rad * math.sin(th)
            if not blocked(cx_, cy_):
                off = (cx_, cy_, rad)
                break
        if off:
            break
    if off is None:
        print("    SET-BACK REFUSED  %-18s built on the map point and reported" % lid)
    else:
        if off[2] > 0.0:
            print("    set-back          %-18s %.2f m (ring search)" % (lid, off[2]))
        x, y = off[0], off[1]

    t = "emb_hr_%s" % lid.replace("-", "")
    box(t + "_plinth", x, y, z + 0.38, bw + 0.16, bd + 0.16, 0.76, MAT["stone"], rz)
    box(t + "_walls", x, y, z + 0.76 + (bh - 0.76) / 2, bw, bd, bh - 0.76, MAT["plaster"], rz)
    for k in range(3):
        fx2 = -bw / 2 + bw * (k + 0.5) / 3
        box(t + "_stud%d" % k, x + fx2 * math.cos(rz), y + fx2 * math.sin(rz),
            z + 0.76 + (bh - 0.76) / 2, 0.16, bd + 0.05, bh - 0.76, MAT["beam"], rz)
    gable(t + "_roof", x, y, z + bh, bw, bd, 1.45 + 0.25 * storeys, roofmat, rz, over=0.36)
    box(t + "_chimney", x - ax * bw * 0.30, y - ay * bd * 0.30, z + bh + 1.5,
        0.58, 0.58, 2.0, MAT["stone"], rz)
    fx, fy = x + ax * (bd / 2 + 0.02), y + ay * (bd / 2 + 0.02)
    lx_, ly_ = math.cos(rz), math.sin(rz)
    box(t + "_door", fx, fy, z + 1.06, 1.10, 0.16, 2.12, MAT["timber"], rz)
    box(t + "_lintel", fx, fy, z + 2.22, 1.50, 0.24, 0.18, MAT["beam"], rz)
    # NO SEPARATE DOORSTEP STONE.  It read well and it was a solid standing on
    # `walk_pad_<id>` — 12-14 walk samples per house.  The pad IS the step: the blockout
    # already lays a threshold slab at every door, which is the whole reason it exists.
    for lvl in range(storeys):
        for wk in (-1, 1):
            wx = fx + lx_ * wk * bw * 0.30
            wy = fy + ly_ * wk * bw * 0.30
            box(t + "_win%d%d" % (lvl, (wk + 1) // 2), wx, wy, z + 1.26 + 2.45 * lvl,
                0.74, 0.10, 0.86, MAT["window"], rz)
            box(t + "_winfrm%d%d" % (lvl, (wk + 1) // 2), wx, wy - 0.02,
                z + 1.26 + 2.45 * lvl, 0.90, 0.06, 1.02, MAT["beam"], rz)
    if keeper:
        # THE KEEPER'S DOOR.  chapter1.js: the lighter lives on a brass hook by the
        # door, and Lake takes it down at dusk.  Nothing else in Emberbrook gets a
        # bracket like this, which is the point — the outside of this house has to say
        # "somebody leaves here every evening" before anybody speaks.
        bxp = fx + lx_ * 0.92
        byp = fy + ly_ * 0.92
        box(t + "_bracket_arm", bxp + ax * 0.16, byp + ay * 0.16, z + 2.30,
            0.42, 0.06, 0.06, MAT["brass"], rz)
        box(t + "_bracket_post", bxp, byp, z + 2.10, 0.07, 0.07, 0.50, MAT["brass"], rz)
        box(t + "_lantern", bxp + ax * 0.34, byp + ay * 0.34, z + 2.06,
            0.24, 0.24, 0.30, MAT["lamp_glass"], rz)
        li = bpy.data.lights.new("KEYHR_%s_doorlamp" % lid, 'POINT')
        li.energy = 680.0
        li.color = (1.0, 0.58, 0.24)
        li.use_custom_distance = True
        li.cutoff_distance = 11.0
        lo = bpy.data.objects.new(li.name, li)
        lo.location = (bxp + ax * 0.34, byp + ay * 0.34, z + 2.06)
        coll(COLL).objects.link(lo)
        NEW.append(lo)
    li2 = bpy.data.lights.new("KEYHR_%s_hearth" % lid, 'POINT')
    li2.energy = 680.0
    li2.color = (1.0, 0.58, 0.24)
    li2.use_custom_distance = True
    li2.cutoff_distance = 11.0
    lo2 = bpy.data.objects.new(li2.name, li2)
    lo2.location = (fx + ax * 0.45, fy + ay * 0.45, z + 1.55)
    coll(COLL).objects.link(lo2)
    NEW.append(lo2)
    BUILT[lid] = (x, y, bw, bd, rz)
    return (x, y, z, bw, bd, rz, ax, ay, fx, fy)


HOUSES = {}
# Rowan's house first: the elder's, the biggest roof on the row, slate over stone.
if "elder-house" in LM:
    HOUSES["elder-house"] = cottage("elder-house", MAT["slate"], storeys=1)
# Lake's — the KEEPER'S cottage, thatched, with the lighter's bracket by the door.
if "lake-home" in LM:
    HOUSES["lake-home"] = cottage("lake-home", MAT["thatch"], keeper=True)
# Mara & Pip's, thatched and lower; the map calls it the hillside cottage.
if "hillside-cottage" in LM:
    HOUSES["hillside-cottage"] = cottage("hillside-cottage", MAT["thatch"])
print("  cottages: %s" % ", ".join(sorted(HOUSES)))

# ---------------------------------------------------------- gardens and hedges --
# Every cottage gets a small worked garden on its own gable side: a herb bed, a wood
# stack, a hedge run.  All searched, all gate-checked, all anchored to a building foot
# rather than scattered (docs/SCENE-LAYOUT.md: touching groups, never singletons).
ngarden = nhedge = 0
for lid in sorted(HOUSES):
    x, y, z, bw, bd, rz, ax, ay, fx, fy = HOUSES[lid]
    lx_, ly_ = math.cos(rz), math.sin(rz)
    tag = lid.replace("-", "")
    for side in (-1, 1):
        gx = x + lx_ * side * (bw / 2 + 1.5) + ax * 0.5
        gy = y + ly_ * side * (bw / 2 + 1.5) + ay * 0.5
        got = search_foot("garden %s" % lid, gx, gy, (0.0, 0.8, 1.5, 2.2), 0.8, -0.1, 1.1)
        if got is None:
            continue
        px, py, gz = got
        if (h32(len(lid), side) % 2) == 0:
            # a herb bed, edged in stone — the map's note on Rowan's door says herbs
            for k in range(3):
                box("emb_hr_%s_herb%d_%d" % (tag, (side + 1) // 2, k),
                    px + 0.30 * (k - 1) * lx_, py + 0.30 * (k - 1) * ly_,
                    gz + 0.16, 0.34, 0.60, 0.32, MAT["herb"], rz)
            box("emb_hr_%s_herbedge%d" % (tag, (side + 1) // 2), px, py, gz + 0.06,
                1.30, 0.86, 0.14, MAT["stone"], rz)
        else:
            # a wood stack against the gable: a village that heats itself
            for k in range(6):
                box("emb_hr_%s_wood%d_%d" % (tag, (side + 1) // 2, k),
                    px + (k % 3 - 1) * 0.26 * lx_, py + (k % 3 - 1) * 0.26 * ly_,
                    gz + 0.13 + 0.26 * (k // 3), 0.24, 0.78, 0.24, MAT["timber"], rz)
        ngarden += 1
    # a low hedge along the lane side, in segments so it follows the ground
    for k in range(5):
        hx = fx + ax * 2.6 + lx_ * (-1.6 + k * 0.8)
        hy = fy + ay * 2.6 + ly_ * (-1.6 + k * 0.8)
        gz, gname = ground_at(hx, hy)
        if gz is None or (gname or "").startswith(("walk_", "water_")):
            continue
        if not free("hedge", hx, hy, 0.42, gz, gz + 1.0):
            continue
        box("bar_emb_hr_%s_hedge%d" % (tag, k), hx, hy, gz + 0.34,
            0.80, 0.55, 0.68, MAT["hedge"], rz)
        nhedge += 1
print("  gardens: %d beds/stacks, %d hedge segments" % (ngarden, nhedge))

# ------------------------------------------------------------- the hilltop bench --
# The map reserves it for quiet story beats and gives the reason in its own note: "the
# whole village in view".  So the build's job is to make that TRUE — the bench faces
# the Heartlight, and nothing this pass plants is allowed to stand in that sightline.
nb = 0
if "home-lane-end" in LM:
    BX, BY, BZ = LM["home-lane-end"]["pos"]
    HL = next((l["pos"] for l in D["landmarks"] if (l.get("kind") or "") == "heartlight"),
              (32, 22, 1.5))
    vx, vy = HL[0] - BX, HL[1] - BY
    vl = math.hypot(vx, vy) or 1.0
    vx, vy = vx / vl, vy / vl
    brz = math.atan2(vy, vx) + math.pi / 2
    lx_, ly_ = math.cos(brz), math.sin(brz)
    # BESIDE ITS OWN PAD, not on it.  `walk_pad_home-lane-end` is where the player
    # stands to use the bench; a bench built on that pad is furniture in a doorway.  The
    # foot is searched outward from the map point, away from the view, so the seat backs
    # onto the hill and the pad stays clear in front of it.
    seat = search_foot("hilltop bench", BX - vx * 1.5, BY - vy * 1.5,
                       (0.0, 0.6, 1.2, 1.8, 2.4), 1.15, -0.1, 1.2)
    if seat is not None:
        BX, BY, gz = seat
    else:
        gz, _g = ground_at(BX, BY)
        gz = BZ if gz is None else gz
    box("emb_hr_bench_seat", BX, BY, gz + 0.44, 1.95, 0.46, 0.09, MAT["timber"], brz)
    box("emb_hr_bench_back", BX - vx * 0.24, BY - vy * 0.24, gz + 0.72,
        1.95, 0.08, 0.44, MAT["timber"], brz)
    for wk in (-1, 1):
        box("emb_hr_bench_leg%d" % ((wk + 1) // 2), BX + lx_ * wk * 0.80,
            BY + ly_ * wk * 0.80, gz + 0.20, 0.11, 0.40, 0.40, MAT["timber"], brz)
    nb = 3
    # THE SIGHTLINE IS MEASURED, not assumed: a ray from seated eye height to the
    # Heartlight's own crystal, before anything else is planted up here.
    eye = Vector((BX + vx * 0.1, BY + vy * 0.1, gz + 1.10))
    tgt = Vector((HL[0], HL[1], HL[2] + 2.2))
    ray = tgt - eye
    hit, _l, _n, _i, ob, _m = sc.ray_cast(dg, eye, ray.normalized(), distance=ray.length - 0.5)
    print("  hilltop bench: faces the Heartlight %.1f m away — sightline %s"
          % (ray.length, ("BLOCKED by " + ob.name) if hit else "CLEAR"))

# --------------------------------------------------------------- the brook spring --
# The map puts the brook's source under this hill.  A spring is a wet place with stones
# and rushes around it, and it is where the town's name begins.
nsp = 0
if "brook-spring" in LM:
    SX2, SY2, SZ2 = LM["brook-spring"]["pos"]
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        got = search_foot("spring stone", SX2 + 1.25 * math.cos(a),
                          SY2 + 1.25 * math.sin(a), (0.0, 0.5, 1.0), 0.4, -0.15, 0.5)
        if got is None:
            continue
        px, py, gz = got
        box("emb_hr_spring_stone%d" % k, px, py, gz + 0.14,
            0.62 + 0.26 * h01(k, 3), 0.54 + 0.22 * h01(k, 5), 0.32,
            MAT["stone"], rz=h01(k, 7) * 1.6)
        nsp += 1
    for k in range(9):
        a = 2 * math.pi * k / 9 + 0.9
        got = search_foot("spring rush", SX2 + 2.1 * math.cos(a), SY2 + 2.1 * math.sin(a),
                          (0.0, 0.6), 0.25, -0.1, 0.9)
        if got is None:
            continue
        px, py, gz = got
        for j in range(3):
            box("veg_emb_hr_rush%d_%d" % (k, j), px + 0.18 * h01(k, j, 3),
                py + 0.18 * h01(k, j, 5), gz + 0.32, 0.05, 0.05, 0.64,
                MAT["herb"], rz=h01(k, j, 7) * 1.6)
        nsp += 1
print("  brook spring: %d stones and rush clumps" % nsp)

# --------------------------------------------------------------------- the trees --
# BEHIND the houses, never between a camera and the row — the finding Festival Square
# paid for in a wasted hero render.
ntree = 0
for k in range(10):
    a0 = 2 * math.pi * k / 10 + 0.25
    cx0 = sum(HOUSES[l][0] for l in HOUSES) / max(1, len(HOUSES))
    cy0 = sum(HOUSES[l][1] for l in HOUSES) / max(1, len(HOUSES))
    for rad in (9.5, 11.5, 13.5):
        tx, ty = cx0 + rad * math.cos(a0), cy0 + rad * math.sin(a0)
        if not (REGION[0] < tx < REGION[1] and REGION[2] < ty < REGION[3]):
            continue
        gz, gname = ground_at(tx, ty)
        if gz is None or (gname or "").startswith(("walk_", "water_")):
            continue
        if BPOLY and brook_d(tx, ty) < 1.8:
            continue
        if any(math.hypot(tx - HOUSES[l][0], ty - HOUSES[l][1]) < 6.0 for l in HOUSES):
            continue
        if not free("tree", tx, ty, 1.0, gz, gz + 8.0):
            continue
        ht = 5.8 + 2.6 * h01(k, 11)
        box("veg_emb_hr_tree%d_trunk" % k, tx, ty, gz + ht * 0.31, 0.33, 0.33,
            ht * 0.66, MAT["timber"])
        leaf = MAT["leaf_green"] if (h32(k, 17) % 5) < 2 else MAT["leaf_autumn"]
        for c_ in range(3):
            rr = (2.3 + 0.9 * h01(k, 23 + c_)) * (1.0 - 0.19 * c_)
            cyl("veg_emb_hr_tree%d_crown%d" % (k, c_), tx, ty, gz + ht * 0.60 + c_ * 1.30,
                rr, 1.85, leaf, seg=8, r2=rr * 0.58)
        ntree += 1
        break
print("  trees: %d, planted behind the row" % ntree)

# =============================================================== acceptance ==
print("-" * 78)
print("  REFUSED (would have stood in the walk gate's own rays) — %d" % len(REFUSED))
for nm, x, y in REFUSED[:12]:
    print("      %-24s at (%.2f, %.2f)" % (nm, x, y))

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
            offenders.setdefault(ob.name, []).append(fo.name if (fh and fo) else floor)
print("  GATE RE-CHECK (master_walk_qa's own two rays, %d walk samples): %d offenders"
      % (len(GATE.pts), len(offenders)))
for nm in sorted(offenders)[:20]:
    print("      %-30s %3d samples on %s"
          % (nm, len(offenders[nm]), ", ".join(sorted(set(offenders[nm])))[:66]))

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
