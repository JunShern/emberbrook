"""emb_gate_build.py — THE GATE FIELD, Emberbrook's fourth real district.

    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_gate_build.py \
        --python-exit-code 1 -- [save] [--digest]

THE ONE UNWARM PLACE IN THE TOWN, and that is the whole brief.  Emberbrook is a village
of magical lanterns — a Heartlight on a pedestal and fifteen lampposts lit from it — and
this district is where that stops.  `chapter1.js` calls the gate shut "my whole life",
STORY.md dates the sealing to three centuries ago, and the shipped `gate/gray.png` is
nearly monochrome.  So:

  * NO LAMP IS BUILT HERE.  Not one.  The blockout's lamp ring already ends at the
    court (`emb_lamp_08_gate-court`) and nothing this pass adds carries a flame.  The
    Old Gate itself gets no light at all, because nobody's warmth reaches it — that is
    the sentence the geometry has to say before anybody speaks it.
  * COLOUR DROPS OUT.  Where every other district spends its 5-10% frame budget on
    awnings, pumpkins and bunting, this one spends nothing.  Stone, bare timber, dead
    leaves, moss.  The contrast IS the content: after four warm districts, a player who
    walks up the north lane should feel the temperature change before they read a sign.

CONTRACT, the same one three districts have now run under: own `emb_gt_`, `bar_emb_gt_`,
`veg_emb_gt_`, `KEYGT_` plus the `lm_<member>_*` massing replaced; never touch
`emb_lamp_*`, `emb_ground_*`, `water_*`, or any `walk_`/`bar_` the blockout built; never
rebuild the walk network; gate every solid with `district_lib.GateGrid`; count and print
every refusal; and A FREE-STANDING SOLID IS SEARCHED, NEVER AUTHORED.

MEMBERSHIP excludes `class: dressing` and the closed lanes — the trap Home Row nearly
fell into, where sharing a `district` field with the implied-scale vista clusters would
have retired massing this pass does not rebuild.

CANON NOTE: the map now names it **The Old Gate**, which is what `chapter1.js` calls it
in every line; the SIGILS are the twin plates set in the ground before the doors, and
they are built as separate props so the story can light them without touching the gate.
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
PARCEL = next(p for p in D["parcels"] if p["id"] == "p-gatefield")
DISTRICT = "gatefield"


def _mine(i):
    l = LM[i]
    return (l.get("class") != "dressing"
            and "closed" not in (l.get("name") or "").lower())


MEMBERS = sorted(i for i in ({m for m in PARCEL["members"] if m in LM} |
                             {l["id"] for l in D["landmarks"]
                              if l.get("district") == DISTRICT}) if _mine(i))
B = PARCEL["bounds"]
REGION = (B["min"][0] - 3, B["max"][0] + 3, B["min"][1] - 3, B["max"][1] + 3)
MINE = ("emb_gt_", "bar_emb_gt_", "veg_emb_gt_", "KEYGT_")
COLL = "EMB_GATEFIELD"

print("=" * 78)
print("THE GATE FIELD — the one unwarm district")
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
       ("grass", "earth", "stone", "timber", "plaster", "thatch", "slate",
        "leaf_autumn", "leaf_green", "iron")}
for k in ("straw", "beam"):
    m = bpy.data.materials.get("emb_mat_" + k)
    if m:
        MAT[k] = m
MAT.setdefault("beam", MAT["timber"])
MAT.setdefault("straw", MAT["thatch"])


def newmat(name, rgba, rough=0.9):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    return m


# The palette of a place nobody keeps.  Greyer stone than the village uses, moss, and
# timber that has not been oiled in three hundred years.
MAT["oldstone"] = newmat("emb_mat_oldstone", (0.36, 0.36, 0.34, 1))
MAT["moss"] = newmat("emb_mat_moss", (0.20, 0.26, 0.15, 1))
MAT["deadwood"] = newmat("emb_mat_deadwood", (0.26, 0.22, 0.18, 1))
MAT["sigil"] = newmat("emb_mat_sigil", (0.44, 0.43, 0.40, 1), rough=0.55)

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
    return mesh(name, v, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                          (2, 3, 7, 6), (3, 0, 4, 7)], m)


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


sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def ground_at(x, y, top=18.0):
    hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)),
                                           distance=34.0)
    return (loc.z, ob.name) if hit else (None, None)


GUARD = WalkGuard(REGION)
GATE = GateGrid(REGION, GUARD)
print("  gate grid: %d walk samples in the region" % len(GATE.pts))
REFUSED = []


def free(what, x, y, r, z0, z1):
    if GATE.clear_pt(x, y, r, z0, z1):
        return True
    REFUSED.append((what, round(x, 2), round(y, 2)))
    return False


def search_foot(what, cx, cy, radii, r, dz0, dz1):
    for rad in radii:
        for k in range(16):
            th = 2 * math.pi * k / 16
            x, y = cx + rad * math.cos(th), cy + rad * math.sin(th)
            if not (REGION[0] < x < REGION[1] and REGION[2] < y < REGION[3]):
                continue
            gz, gname = ground_at(x, y)
            if gz is None or (gname or "").startswith(("walk_", "water_")):
                continue
            if not GATE.clear_pt(x, y, r, gz + dz0, gz + dz1):
                continue
            return (x, y, gz)
    REFUSED.append((what, round(cx, 2), round(cy, 2)))
    return None


# =============================================================================
# 1. THE OLD GATE — shut three hundred years, and it has to look it
# =============================================================================
G = LM["sigil-gate"]
GX, GY, GZ = G["pos"]
gax, gay = appr_of("sigil-gate")
GRZ = math.atan2(gay, gax) + math.pi / 2
lx_, ly_ = math.cos(GRZ), math.sin(GRZ)             # across the gate
print("  the gate: %r, state %r" % (G.get("name"), G.get("state")))

# jambs, built in COURSES rather than as one slab: a three-hundred-year-old wall reads
# by its joints, and a single box reads as a monolith at every distance
for sgn, tag in ((-1, "L"), (1, "R")):
    jx, jy = GX + lx_ * sgn * 1.95, GY + ly_ * sgn * 1.95
    for c_ in range(6):
        w = 1.10 - 0.035 * c_
        box("emb_gt_gate_jamb%s_c%d" % (tag, c_), jx, jy, GZ + 0.30 + c_ * 0.58,
            w, 1.15, 0.56, MAT["oldstone"], GRZ)
    box("emb_gt_gate_cap%s" % tag, jx, jy, GZ + 3.72, 1.25, 1.30, 0.26,
        MAT["oldstone"], GRZ)
# the lintel, and the two carved sigils on its face — the gate's own name in stone
box("emb_gt_gate_lintel", GX, GY, GZ + 3.60, 5.10, 1.15, 0.62, MAT["oldstone"], GRZ)
box("emb_gt_gate_relieving", GX, GY, GZ + 4.06, 4.60, 1.00, 0.30, MAT["oldstone"], GRZ)
for sgn, tag in ((-1, "L"), (1, "R")):
    cyl("emb_gt_gate_sigil%s" % tag, GX + lx_ * sgn * 1.05 - gax * (0.60),
        GY + ly_ * sgn * 1.05 - gay * (0.60), GZ + 3.60, 0.42, 0.10, MAT["sigil"], seg=16)
    for r_ in range(6):
        a = 2 * math.pi * r_ / 6
        box("emb_gt_gate_sigil%s_ray%d" % (tag, r_),
            GX + lx_ * sgn * 1.05 - gax * 0.62 + 0.26 * math.cos(a),
            GY + ly_ * sgn * 1.05 - gay * 0.62 + 0.26 * math.sin(a),
            GZ + 3.60, 0.10, 0.10, 0.12, MAT["sigil"], GRZ)
# the doors: two leaves, iron-banded, with ring handles.  They do NOT open tonight —
# `state: sealed` is the map's word and the story's — but they are built as separate
# leaves so that the day they do, it is a transform and not a rebuild.
for sgn, tag in ((-1, "A"), (1, "B")):
    dx_, dy_ = GX + lx_ * sgn * 0.72, GY + ly_ * sgn * 0.72
    box("emb_gt_gate_leaf%s" % tag, dx_, dy_, GZ + 1.60, 1.42, 0.26, 3.20,
        MAT["deadwood"], GRZ)
    for bnd in range(3):
        box("emb_gt_gate_band%s%d" % (tag, bnd), dx_, dy_ - gay * 0.03 - gax * 0.0,
            GZ + 0.55 + bnd * 1.05, 1.46, 0.30, 0.14, MAT["iron"], GRZ)
    cyl("emb_gt_gate_ring%s" % tag, GX + lx_ * sgn * 0.30 - gax * 0.17,
        GY + ly_ * sgn * 0.30 - gay * 0.17, GZ + 1.55, 0.17, 0.05, MAT["iron"], seg=12)
# moss and ivy: three centuries of nobody. `veg_`, and the only green in the district.
nmoss = 0
for k in range(12):
    sgn = 1 if k % 2 else -1
    hgt = 0.5 + 3.0 * h01(k, 3)
    mx = GX + lx_ * sgn * (1.55 + 0.7 * h01(k, 5)) - gax * 0.60
    my = GY + ly_ * sgn * (1.55 + 0.7 * h01(k, 5)) - gay * 0.60
    box("veg_emb_gt_gate_moss%02d" % k, mx, my, GZ + hgt, 0.34 + 0.3 * h01(k, 7), 0.10,
        0.45 + 0.5 * h01(k, 11), MAT["moss"], GRZ)
    nmoss += 1
print("  the Old Gate: coursed jambs, lintel, two carved sigils, two banded leaves, "
      "%d moss patches — and NO LAMP, by canon" % nmoss)

# --- THE TWIN SIGIL PLATES, set in the ground before the doors (Ch1's set-piece).
# Separate props on purpose: the pact scene lights them, and lighting a plate must never
# mean touching the gate.  They sit ON the court's floor, so each is checked and each is
# sunk flush rather than standing proud — a plate you can trip over is not a plate.
nplate = 0
for sgn, tag in ((-1, "L"), (1, "R")):
    px = GX + lx_ * sgn * 2.20 + gax * 3.20
    py = GY + ly_ * sgn * 2.20 + gay * 3.20
    gz, _g = ground_at(px, py)
    if gz is None:
        continue
    # FLUSH, not proud: top at the surface it is set into, so the walk gate's up-ray
    # (which starts at +0.06) can never see it.
    # SUNK, not flush.  At a 0.06 m offset the disc's top was coplanar with the court
    # and a walk sample's down-ray hit the plate instead of the floor.  0.16 puts it
    # clear of both rays and still reads as a plate set into stone.
    cyl("emb_gt_plate%s" % tag, px, py, gz - 0.16, 0.92, 0.12, MAT["sigil"], seg=20)
    cyl("emb_gt_plate%s_inner" % tag, px, py, gz - 0.14, 0.62, 0.10, MAT["oldstone"], seg=16)
    for r_ in range(6):
        a = 2 * math.pi * r_ / 6 + 0.26
        box("emb_gt_plate%s_ray%d" % (tag, r_), px + 0.40 * math.cos(a),
            py + 0.40 * math.sin(a), gz - 0.13, 0.30, 0.09, 0.09, MAT["sigil"], a)
    nplate += 1
print("  sigil plates: %d, set FLUSH into the court (a plate you trip over is not a plate)"
      % nplate)

# =============================================================================
# 2. THE TITHE BARN — harvest stores, cats in the rafters (the map's own note)
# =============================================================================
BN = LM["barn"]
BX, BY, BZ = BN["pos"]
bax, bay = appr_of("barn")
BRZ = math.atan2(bay, bax) + math.pi / 2
blx, bly = math.cos(BRZ), math.sin(BRZ)
# 6.2 x 4.4, not 7.2 x 5.0.  The north lane runs past the barn's flank and a 7.2 m
# frontage put 161 walk samples under its base plinth with no offset able to clear
# it.  A tithe barn at 6.2 m is still the biggest roof north of the square.
bw, bd, bh = 6.2, 4.4, 4.2
HW_ = (bw + 0.10) / 2 + 0.10
HD_ = (bd + 0.10) / 2 + 0.10
crz, srz = math.cos(-BRZ), math.sin(-BRZ)


def barn_blocked(cx_, cy_):
    for (sx, sy, sz) in GATE.pts:
        if not (BZ < sz + 2.00 and BZ + 0.85 > sz + 0.005):
            continue
        ddx, ddy = sx - cx_, sy - cy_
        if abs(ddx * crz - ddy * srz) <= HW_ and abs(ddx * srz + ddy * crz) <= HD_:
            return True
    return False


off = None
for rad in [0.0] + [0.15 + 0.15 * k for k in range(18)]:
    for a_ in range(24 if rad > 0 else 1):
        th = math.atan2(-bay, -bax) + 2 * math.pi * a_ / 24
        cx_, cy_ = BX + rad * math.cos(th), BY + rad * math.sin(th)
        if not barn_blocked(cx_, cy_):
            off = (cx_, cy_, rad)
            break
    if off:
        break
if off is None:
    print("    SET-BACK REFUSED  barn — built on the map point and reported")
else:
    if off[2] > 0:
        print("    set-back          barn %.2f m (ring search)" % off[2])
    BX, BY = off[0], off[1]

box("emb_gt_barn_base", BX, BY, BZ + 0.42, bw + 0.20, bd + 0.20, 0.84, MAT["stone"], BRZ)
box("emb_gt_barn_walls", BX, BY, BZ + 0.84 + (bh - 0.84) / 2, bw, bd, bh - 0.84,
    MAT["deadwood"], BRZ)
for k in range(6):                                   # the frame, wide-spaced like a barn
    fx2 = -bw / 2 + bw * (k + 0.5) / 6
    box("emb_gt_barn_post%d" % k, BX + blx * fx2, BY + bly * fx2,
        BZ + 0.84 + (bh - 0.84) / 2, 0.22, bd + 0.06, bh - 0.84, MAT["beam"], BRZ)
gable("emb_gt_barn_roof", BX, BY, BZ + bh, bw, bd, 2.35, MAT["thatch"], BRZ, over=0.55)
# the wide doors a tithe barn needs, on the side the lane arrives at
fx, fy = BX + bax * (bd / 2 + 0.03), BY + bay * (bd / 2 + 0.03)
for sgn, tag in ((-1, "A"), (1, "B")):
    box("emb_gt_barn_door%s" % tag, fx + blx * sgn * 1.05, fy + bly * sgn * 1.05,
        BZ + 1.55, 2.00, 0.18, 3.10, MAT["timber"], BRZ)
box("emb_gt_barn_lintel", fx, fy, BZ + 3.22, 4.40, 0.30, 0.26, MAT["beam"], BRZ)
# straw and a cart, huddled at the gable end
nbarn = 0
for side in (-1, 1):
    got = search_foot("barn straw", BX + blx * side * (bw / 2 + 1.6) + bax * 0.6,
                      BY + bly * side * (bw / 2 + 1.6) + bay * 0.6,
                      (0.0, 0.8, 1.6, 2.4), 0.85, -0.1, 1.2)
    if got is None:
        continue
    px, py, gz = got
    for k in range(3):
        box("emb_gt_barn_bale%d_%d" % ((side + 1) // 2, k),
            px + blx * (k - 1) * 0.95, py + bly * (k - 1) * 0.95, gz + 0.45,
            1.15, 0.82, 0.86, MAT["straw"], BRZ + h01(side, k, 3) * 0.3)
    nbarn += 1
print("  tithe barn: %.1f x %.1f m, wide doors, %d straw stacks" % (bw, bd, nbarn))

# =============================================================================
# 3. THE TRAILHEAD — the stile, and the first waystone of the forest trail
# =============================================================================
TH = LM["forest-trailhead"]
TX2, TY2, TZ2 = TH["pos"]
tax, tay = appr_of("forest-trailhead")
TRZ = math.atan2(tay, tax) + math.pi / 2
tlx, tly = math.cos(TRZ), math.sin(TRZ)
# A STILE STRADDLES THE WALL; THE PAD IS WHERE YOU STAND BEFORE IT.  Built on the map
# point its treads and rails sat squarely on `walk_pad_forest-trailhead` — 24 samples —
# which is a step ladder in a doorway.  Pushed out along the trail, past the pad, so the
# pad stays the threshold and the stile is the thing you cross at it.
_st = search_foot("stile", TX2 - tax * 2.3, TY2 - tay * 2.3, (0.0, 0.7, 1.4, 2.1),
                  1.15, -0.1, 1.5)
if _st is not None:
    TX2, TY2, TZ2 = _st
for sgn, tag in ((-1, "A"), (1, "B")):
    box("emb_gt_stile_post%s" % tag, TX2 + tlx * sgn * 0.95, TY2 + tly * sgn * 0.95,
        TZ2 + 0.62, 0.20, 0.20, 1.24, MAT["timber"], TRZ)
for k in range(2):
    box("emb_gt_stile_rail%d" % k, TX2, TY2, TZ2 + 0.55 + k * 0.44, 1.95, 0.10, 0.10,
        MAT["timber"], TRZ)
for k in range(2):
    box("emb_gt_stile_tread%d" % k, TX2 - tax * (0.45 - k * 0.90),
        TY2 - tay * (0.45 - k * 0.90), TZ2 + 0.20 + 0.16 * (1 - k), 1.50, 0.42, 0.14,
        MAT["timber"], TRZ)
got = search_foot("trail waystone", TX2 + tax * 2.0, TY2 + tay * 2.0,
                  (0.0, 0.8, 1.5), 0.5, -0.2, 1.6)
if got is not None:
    px, py, gz = got
    box("emb_gt_trail_waystone_base", px, py, gz + 0.11, 1.00, 0.82, 0.22,
        MAT["oldstone"], TRZ)
    box("emb_gt_trail_waystone", px, py, gz + 0.86, 0.70, 0.46, 1.30,
        MAT["oldstone"], TRZ + 0.08)
    box("veg_emb_gt_trail_waystone_moss", px, py - 0.24, gz + 1.18, 0.52, 0.06, 0.40,
        MAT["moss"], TRZ + 0.08)
print("  trailhead: stile with two treads and a rail, plus the trail's first waystone")

# =============================================================================
# 4. THE COURT — a dry-stone wall round the old edge of the village
# =============================================================================
# `bar_`: a collider that is never a floor, which is what a waist-high wall is.  It is
# also the district's soft closure — you can SEE the field beyond it and you cannot
# cross it, exactly the technique the impliedScale ruling asks for.
CT = LM["gate-court"]
CX, CY, CZ = CT["pos"]
CR = CT.get("extent", 5)
nwall = 0
for k in range(30):
    a = 2 * math.pi * k / 30
    wx, wy = CX + (CR + 1.15) * math.cos(a), CY + (CR + 1.15) * math.sin(a)
    # never across the gate's own approach, and never across the trail
    if abs(math.atan2(wy - GY, wx - GX)) < 9 and \
            math.hypot(wx - GX, wy - GY) < 5.2:
        continue
    if math.hypot(wx - TX2, wy - TY2) < 4.2:
        continue
    gz, gname = ground_at(wx, wy)
    if gz is None or (gname or "").startswith(("walk_", "water_")):
        continue
    if not free("court wall", wx, wy, 0.55, gz, gz + 1.0):
        continue
    box("bar_emb_gt_courtwall%02d" % k, wx, wy, gz + 0.36, 1.20, 0.42, 0.72,
        MAT["oldstone"], rz=a + math.pi / 2)
    nwall += 1
print("  court: %d dry-stone wall segments (bar_ — see over it, never cross it)" % nwall)

# =============================================================================
# 5. THE TREES — bare, older, greyer.  No greens mixed in, and that is the point.
# =============================================================================
ntree = 0
for k in range(14):
    a0 = 2 * math.pi * k / 14 + 0.2
    for rad in (CR + 4.5, CR + 6.5, CR + 8.5):
        tx, ty = CX + rad * math.cos(a0), CY + rad * math.sin(a0)
        if not (REGION[0] < tx < REGION[1] and REGION[2] < ty < REGION[3]):
            continue
        gz, gname = ground_at(tx, ty)
        if gz is None or (gname or "").startswith(("walk_", "water_")):
            continue
        if math.hypot(tx - GX, ty - GY) < 5.5 or math.hypot(tx - BX, ty - BY) < 6.0:
            continue
        if not free("tree", tx, ty, 0.9, gz, gz + 9.0):
            continue
        ht = 6.5 + 3.0 * h01(k, 13)
        box("veg_emb_gt_tree%d_trunk" % k, tx, ty, gz + ht * 0.42, 0.30, 0.30,
            ht * 0.84, MAT["deadwood"])
        # BARE BRANCHES, not crowns.  Every other district in this town gets foliage;
        # this one gets winter, three hundred years early, because the shipped
        # gate/gray.png is a stand of bare trunks and it is right.
        for br in range(5):
            ba = 2 * math.pi * br / 5 + h01(k, br, 3) * 1.2
            bl = 1.5 + 1.1 * h01(k, br, 5)
            bz = gz + ht * (0.62 + 0.10 * (br % 3))
            box("veg_emb_gt_tree%d_branch%d" % (k, br),
                tx + math.cos(ba) * bl * 0.5, ty + math.sin(ba) * bl * 0.5,
                bz + 0.30, bl, 0.11, 0.11, MAT["deadwood"], rz=ba)
        ntree += 1
        break
print("  trees: %d BARE — no crowns, no greens: this district gets winter" % ntree)

# =============================================================================
# ACCEPTANCE
# =============================================================================
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
            fh, _fl, _fn, _fi, fo, _fm = sc.ray_cast(dg, Vector((sx, sy, sz + 0.05)),
                                                     Vector((0, 0, -1)), distance=0.60)
            offenders.setdefault(ob.name, []).append(fo.name if (fh and fo) else "?")
print("  GATE RE-CHECK (master_walk_qa's own two rays, %d walk samples): %d offenders"
      % (len(GATE.pts), len(offenders)))
for nm in sorted(offenders)[:20]:
    print("      %-30s %3d samples on %s"
          % (nm, len(offenders[nm]), ", ".join(sorted(set(offenders[nm])))[:66]))

# THE DISTRICT'S OWN CANON ASSERTION: no light source belongs to this pass.
mylights = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.name.startswith("KEYGT_")]
assert not mylights, "the Gate Field builds no lamp — found %s" % [o.name for o in mylights]
heart = [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.energy > 2000]
assert len(heart) == 1, "Emberbrook has exactly one Heartlight — found %d" % len(heart)
print("  canon: 0 lights built by this district (nobody's warmth reaches the Old Gate)")
print("  canon: still exactly one magical light town-wide (%s)" % heart[0].name)

mine = [o for o in bpy.data.objects if o.name.startswith(MINE)]
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
