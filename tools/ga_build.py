"""ga_build.py — THE GATE ARRIVAL PASS (legibility item 2), town custodian.

  Blender -b tools/blends/dellhollow-master.blend -P tools/ga_build.py \
      --python-exit-code 1 -- [save]

Scope, exactly as the coordinator scoped it on 2026-07-30:

  A  the town arrival (`del-cine` shot `gate`) hides the street.  The coordinator
     ray-attributed the occluders from the SOLVED cine camera and named FIVE
     objects.  This pass raises/thins THOSE FIVE and nothing else.
  B  a threshold lantern at the head of the flight down to the inn — an ORDINARY
     warm 680 W practical, the town standard.  Heartlights are Emberbrook magic
     and do not exist in Dellhollow (world canon).

COORDINATE CONTRACT, the one thing that bites every new reader of `probe/*.json`
and `routes.json`: those files are RUNTIME space (x, y_up, z); the blend is
(x, y_out, z_up); and they relate as  blend = (x, -z_runtime, y_runtime).  Every
conversion below is that one line.  The solved gate camera therefore stands at
blender (26.272, 31.800, 36.490) and the rim road runs at blender z 23.57..24.20.

THE NAME `veg_gate_rimtreeE_0_2` DOES NOT EXIST IN THE BLEND, and the resolution
is recorded here rather than guessed twice.  The master carries one object,
`veg_gate_rimtreeE_0`, whose mesh has TWO materials (mat_timber trunk +
mat_leaf_autumn cards); three.js's GLTFLoader names the per-primitive children of
a multi-primitive mesh `<node>_0`, `<node>_1`, ... so the runtime raycast that
produced the coordinator's list reported a primitive, not a node.  This pass acts
on the object `veg_gate_rimtreeE_0` and leaves its TRUNK alone — only leaf cards
are ever moved, which is what "lift the crown" means on a tree.

WHY PER-CARD AND NOT PER-OBJECT.  Each rimclump is 46 INDEPENDENT leaf quads on
`mat_leaf_autumn`; the tree is a trunk plus 110 of them.  Translating a whole
clump is what the brief asks for first, and it was tried and rendered: the lift
these sightlines need is 1.3..3.1 m on bushes 2.5..3.5 m tall, so the clump ends
up hanging two metres over its own shadow — measured, rendered, rejected.  The
sightlines are a NARROW BAND through the middle of each clump (the camera is 25 deg
above the road, so the cards that block sit at z 25.3..26.6 while the cards below
that band are already under the rays and the cards above it are already over
them).  Lifting only the band's cards is the same operation the brief names —
"lifting foliage crowns so the road shows beneath" — applied to the part of the
crown that is actually in the way, and it leaves every clump standing on its own
ground.  A card that cannot clear within `CARD_CAP` is THINNED AWAY instead, which
is the brief's fallback; on the committed geometry none needed to be.

THE SAMPLE SET IS HONEST ABOUT WHAT THESE FIVE CAN FIX.  A route sample enters it
only if the camera can see it WITH THE FIVE HIDDEN.  Samples that a cliff, the
arch, the gatehouse or an off-list clump blocks are therefore never used to
justify cutting foliage that was never the reason — and they are reported at the
end as the residue this assignment is not allowed to touch.

IDEMPOTENT ON MESHES IT DOES NOT OWN.  Section A edits objects the GATE district
built, so "clear my prefix and rebuild" does not apply.  Instead the first run
snapshots each of the five as a `GA_SRC_*` mesh datablock (fake user, no object,
never exported) and every run RESTORES from that snapshot before measuring — so a
re-run recomputes from the original geometry instead of lifting the same cards a
second time.  Section B owns the prefixes `ga_` and `KEYGA_` and clears them.

PREFIX OWNERSHIP, per the canon lg_build's near-miss wrote on 2026-07-30 ("a
two-letter prefix is not ownership"): this pass clears `ga_` and `KEYGA_` ONLY.
`gate_` and `KEYG_` are the GATE district's — 16 lights including every lantern on
the arch — and neither `"gate_arch".startswith("ga_")` nor
`"KEYG_x".startswith("KEYGA_")` is true.  Asserted below, not assumed.
"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector
from mathutils.geometry import intersect_ray_tri

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import REPO, join_meshes, obox, cyl, link, coll, M, world_bbox
from district_lib import WalkGuard, bvh_of, ground_z, clear_between

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


SAVE = "save" in argv
SHOT = opt("--shot", None)      # self-check frame from the shot's own solved camera
COLL = "GATE_DISTRICT"          # this is the gate tier's own arrival; it belongs there
LOG = []

# THE OCCLUDER LIST IS NOW DERIVED, NOT NAMED, and the reason is that the camera moved.
# The 2026-07-30 list ("veg_gate_rimclump_11", "_1", "_2", "_12", "veg_gate_rimtreeE_0")
# was ray-attributed by the coordinator from the gate camera AS IT THEN STOOD — a 29 m
# solved standoff at yaw 55 / pitch 28. On 2026-08-01 the user ruled that the entrance
# shot's framing IS a vista, and `gate` now stands 75 m out across the gorge. A hand-named
# list is a fact about one camera position; re-attributing it is one ray-cast per sample
# and cannot go stale. Kept as a fallback ONLY if the derivation finds nothing.
FIVE_2026_07_30 = ["veg_gate_rimclump_11", "veg_gate_rimclump_1", "veg_gate_rimclump_2",
                   "veg_gate_rimclump_12", "veg_gate_rimtreeE_0"]
# What this pass MAY own: gate-district vegetation. Searched-not-authored, so re-seating a
# clump is a re-run rather than art surgery. Everything else that blocks a sightline —
# cliff, arch, gatehouse, awnings, tarps — is residue this assignment may not touch and is
# reported at the end, exactly as before.
OWNABLE = ("veg_gate_rimclump_", "veg_gate_rimtree")
MAX_OCCLUDERS = int(opt("--max-occluders", "8"))
LEAFMAT = "mat_leaf_autumn"
# A RAISED CARD MUST LAND INSIDE ITS OWN CLUMP, and that rule was written by a
# render, not by taste: with a flat 2.4 m cap the pass cleared every sightline and
# left two leaf cards hanging in mid-air under the gatehouse window, a metre clear
# of the bush they came from.  So a card may rise at most to its clump's own
# ORIGINAL crown top (+CROWN_TOL) — that is what "gather the crown" means and it
# is self-limiting per card.  Anything that would need more is THINNED AWAY
# instead, which is the brief's fallback.  CARD_CAP is the second, absolute limit.
# CROWN_TOL was SOLVED against the frame, not chosen: 0.10 is so tight that it
# turns 28 of 31 raises into deletions, and a flat cap with no crown rule at all
# leaves cards 1.6..2.1 m clear of their bush.  0.50 renders with no detached card
# anywhere in the frame and keeps three times as many cards raised as deleted-and-
# raised at 0.10 — raising preferred, exactly as far as the render allows.
CARD_CAP = float(opt("--cap", "2.40"))
CROWN_TOL = float(opt("--crown-tol", "0.50"))
# WHAT COUNTS AS A SIGHTLINE.  The arrival's complaint is that the STREET is
# hidden, so the target is the road surface the player walks and the body of the
# figure walking it.  The head is deliberately not a target: nothing in the five
# blocks head height in the first place (measured), and adding it as a constraint
# only converts raises into deletions.
ALLL = {"road": 0.06, "body": 0.88, "head": 1.70}
TARGET_LIFTS = [(k, ALLL[k]) for k in opt("--targets", "road,body").split(",")]
SEAM = Vector((20.81, 3.23, 22.30))     # runtime (20.81, 22.30, -3.23), the inn seam
# PAID SIGHTLINES (coordinator ruling 2026-08-01). Two arrivals must be visible from this
# camera, and they are PAID the way camera corridors are paid in the Emberbrook blockout:
# the vegetation search may put scrub anywhere it likes EXCEPT across one of these lines.
# The floors are the values these arrivals had BEFORE the vista reshape, so the bar is
# "no worse than the shot it replaced" rather than a number invented to be passable.
# Achieved-vs-floor is printed at the end of section A and is the acceptance test.
PAID = [
    ("portal ow-valley>del-cine", Vector((13.58, 5.157, 24.07)), 0.321),
    ("cut shelf-west>gate",       Vector((17.50, 2.750, 24.04)), 1.000),
]
REGION = (12.0, 30.0, -2.0, 14.0)       # every place this file builds or measures


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-30s %s" % (kind, what, why))


print("=" * 78)
print("GATE ARRIVAL PASS  —  named-occluder lift + threshold lantern")
print("=" * 78)

assert not any(o.name.startswith(("ga_", "KEYGA_")) and o.name.startswith(("gate_", "KEYG_"))
               for o in bpy.data.objects), "prefix collision with the GATE district"

sc = bpy.context.scene


def refresh():
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


# =========================================================================
# A. THE FIVE NAMED OCCLUDERS
# =========================================================================
S = json.load(open(REPO + "/public/townmap/dellhollow.cameras.solved.json"))
CAMC = next(c for c in S["cameras"] if c["id"] == "gate")
CAM = Vector(CAMC["pos"])

# --- RESTORE FIRST, THEN DERIVE. Every object that has ever been lifted carries a
# GA_SRC_* snapshot, and all of them are restored before anything is measured — including
# ones that are no longer on the derived list. Without that, a clump the old camera needed
# lifted would keep its lift forever after it stopped being an occluder, and the pass
# would stop being idempotent the first time the list changed.
prior = [m.name[len("GA_SRC_"):] for m in bpy.data.meshes if m.name.startswith("GA_SRC_")]
restored = 0
for name in prior:
    o = bpy.data.objects.get(name)
    if o is None:
        continue
    assert o.data.users == 1, "%s shares its mesh; editing it would edit a neighbour" % name
    src = bpy.data.meshes.get("GA_SRC_" + name)
    if src is None:
        src = o.data.copy()
        src.name = "GA_SRC_" + name
        src.use_fake_user = True
    else:
        old, mname = o.data, o.data.name
        o.data = src.copy()
        bpy.data.meshes.remove(old)
        o.data.name = mname
        restored += 1
if restored:
    log("REBUILD", "%d meshes restored" % restored, "idempotent re-run from GA_SRC_*")
refresh()

def visible(dg, t):
    d = t - CAM
    return not sc.ray_cast(dg, CAM, d.normalized(), distance=d.length - 0.10)[0]


def first_hit(dg, t):
    d = t - CAM
    h = sc.ray_cast(dg, CAM, d.normalized(), distance=d.length - 0.10)
    return h[4].name if h[0] else None


# --- DERIVE THE OCCLUDER LIST from the camera as it now stands ------------------
# Ray-cast the PAID arrival body grids and the shot's own solved region probes, and
# collect the first hits this pass is allowed to own. Ranked by how many rays each costs,
# so the list is the coordinator's 2026-07-30 method (ray-attribute, name the dominant
# blockers) run by the tool instead of by hand.
dg = refresh()
_att = {}
_paidrays = {}
for label, a, floor in PAID:
    rays = [Vector((a.x + dx, a.y + dy, a.z + h))
            for h in (0.85, 1.53) for dx, dy in ((0, 0), (.25, 0), (-.25, 0), (0, .25), (0, -.25))]
    _paidrays[label] = rays
    for t in rays:
        n = first_hit(dg, t)
        if n and n.startswith(OWNABLE):
            _att[n] = _att.get(n, 0) + 3          # a paid line outranks a region probe
for pr in CAMC.get("probes", []):
    n = first_hit(dg, Vector(pr))
    if n and n.startswith(OWNABLE):
        _att[n] = _att.get(n, 0) + 1
FIVE = [n for n, _ in sorted(_att.items(), key=lambda kv: -kv[1])][:MAX_OCCLUDERS]
if not FIVE:
    FIVE = [n for n in FIVE_2026_07_30 if bpy.data.objects.get(n)]
    log("DERIVE", "no ownable occluder found", "fell back to the 2026-07-30 named list")
else:
    log("DERIVE", "%d occluders, ray-attributed" % len(FIVE),
        ", ".join("%s(%d)" % (n, _att[n]) for n in FIVE))
# snapshot any newly derived object that has never been touched before
for name in FIVE:
    o = bpy.data.objects[name]
    if bpy.data.meshes.get("GA_SRC_" + name) is None:
        assert o.data.users == 1, "%s shares its mesh" % name
        src = o.data.copy(); src.name = "GA_SRC_" + name; src.use_fake_user = True
refresh()

# --- the route samples, densified along the shot's own routes
R = json.load(open(REPO + "/public/townmap/dellhollow.routes.json"))["shots"]["gate"]
raw = []
for r in R["routes"]:
    P = [Vector((p[0], -p[2], p[1])) for p in r["points"]]
    for a, b in zip(P, P[1:]):
        n = max(1, int((b - a).length / 0.40))
        for k in range(n):
            raw.append((r["id"], a.lerp(b, k / float(n))))
    raw.append((r["id"], P[-1]))
for e in R["entries"]:
    raw.append(("entry " + e["id"], Vector((e["at"][0], -e["at"][2], e["at"][1]))))
for e in R["exits"]:
    raw.append(("exit " + e["id"], Vector((e["at"][0], -e["at"][2], e["at"][1]))))


for n in FIVE:
    bpy.data.objects[n].hide_viewport = True
dg = refresh()
SAMP, RESIDUE = [], {}
for rid, p in raw:
    for lname, lift in TARGET_LIFTS:
        t = Vector((p.x, p.y, p.z + lift))
        if visible(dg, t):
            SAMP.append((rid, lname, t))
        else:
            RESIDUE.setdefault(first_hit(dg, t), []).append((rid, lname, p))
# THE PAID LINES JOIN THE SAMPLE SET, which is the whole point of calling them paid: the
# per-card raise below only ever moves a card that blocks something IN `SAMP`, so an
# arrival that is not in it can be reported as UNDER FLOOR forever while the pass lifts
# nothing. Measured the first run: 0 cards raised, both paid lines still 0.0%. They are
# added here, after the same with-occluders-hidden filter every other sightline gets, so a
# ray that a cliff blocks anyway still cannot justify cutting foliage.
npaid = 0
for label, a, floor in PAID:
    for t in _paidrays[label]:
        if visible(dg, t):
            SAMP.append(("paid " + label, "paid", t))
            npaid += 1
        else:
            RESIDUE.setdefault(first_hit(dg, t), []).append(("paid " + label, "paid", a))
for n in FIVE:
    bpy.data.objects[n].hide_viewport = False
dg = refresh()
log("PAID", "%d of %d paid rays are winnable" % (npaid, sum(len(v) for v in _paidrays.values())),
    "the rest are blocked by geometry this pass may not touch, even with the scrub hidden")
log("MEASURE", "%d of %d sightlines" % (len(SAMP), len(raw) * len(TARGET_LIFTS)),
    "are the camera's to give once the five are out of the way — the rest are "
    "blocked by geometry this assignment may not touch and are listed at the end")

# --- per-card raise, or thin when the raise would exceed the cap
nraise = nthin = 0
CARDS = []
for name in FIVE:
    o = bpy.data.objects[name]
    Mx = o.matrix_world
    # WHICH SLOTS ARE FOLIAGE. The 2026-07-30 list was five hand-picked objects that all
    # happened to carry `mat_leaf_autumn`, so an equality test was enough. The derived list
    # is whatever the rays actually hit, and the rim scrub is cloned from twelve different
    # source bushes with their own leaf materials — `veg_gate_rimclump_26` carries none of
    # `mat_leaf_autumn` and the equality test asserted the pass to a halt. Match on the
    # MATERIAL FAMILY instead, and fall back to every slot when a clump is all foliage,
    # which a bush with no trunk is. The trunk rule is unchanged and is what matters: a
    # slot that is not foliage is never moved, so a tree still keeps its trunk.
    leaf_slots = {i for i, m in enumerate(o.data.materials)
                  if m and ("leaf" in m.name.lower() or "foliage" in m.name.lower())}
    if not leaf_slots and not any(m and ("timber" in m.name.lower() or "bark" in m.name.lower())
                                  for m in o.data.materials):
        leaf_slots = {i for i, m in enumerate(o.data.materials) if m}
    assert leaf_slots, "%s carries no foliage slot (materials: %s)" % (
        name, [m.name for m in o.data.materials if m])
    crown = world_bbox(o)[5]                # the clump's own top, BEFORE anything moves
    bm = bmesh.new()
    bm.from_mesh(o.data)
    seen, parts = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            u = stack.pop()
            comp.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
        parts.append(comp)
    kill, lifts = [], []
    for comp in parts:
        faces = {f for v in comp for f in v.link_faces}
        # THE TRUNK IS NEVER TOUCHED: a loose part with any non-leaf face is
        # structure (mat_timber), and a tree whose trunk moved is a tree that fell.
        if not faces or not all(f.material_index in leaf_slots for f in faces):
            continue
        tris = []
        for f in faces:
            vs = [Mx @ v.co for v in f.verts]
            tris += [(vs[0], vs[k], vs[k + 1]) for k in range(1, len(vs) - 1)]

        def blocks(dz, tris=tris):
            off = Vector((0, 0, dz))
            for _rid, _ln, t in SAMP:
                d = t - CAM
                L, dn = d.length, d.normalized()
                for (a, b, c) in tris:
                    h = intersect_ray_tri(a + off, b + off, c + off, dn, CAM, True)
                    if h is not None and (h - CAM).length < L - 0.10:
                        return True
            return False

        if not blocks(0.0):
            continue
        room = min(CARD_CAP, crown + CROWN_TOL - max(q.z for t in tris for q in t))
        if room <= 0.0 or blocks(room):
            kill.append(comp)
            continue
        lo, hi = 0.0, room
        for _ in range(12):
            mid = (lo + hi) / 2
            if blocks(mid):
                lo = mid
            else:
                hi = mid
        lifts.append((comp, hi))
    for comp, dz in lifts:
        for v in comp:
            v.co.z += dz
    if kill:
        bmesh.ops.delete(bm, geom=[v for comp in kill for v in comp], context='VERTS')
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    nraise += len(lifts)
    nthin += len(kill)
    CARDS.append((name, len(parts), len(lifts),
                  max([d for _c, d in lifts], default=0.0),
                  sum(d for _c, d in lifts) / len(lifts) if lifts else 0.0, len(kill)))
    print("    %-28s %3d cards: %2d raised (max %.2f m, mean %.2f), %d thinned away"
          % (name, len(parts), len(lifts), CARDS[-1][3], CARDS[-1][4], len(kill)))
log("RAISE", "%d leaf cards lifted" % nraise,
    "%d thinned away (cap %.2f m); no card moved that was not in the ray bundle, "
    "no trunk moved at all" % (nthin, CARD_CAP))

dg = refresh()
STILL = [(rid, ln, first_hit(dg, t)) for (rid, ln, t) in SAMP if not visible(dg, t)]
log("VERIFY", "%d of %d cleared" % (len(SAMP) - len(STILL), len(SAMP)),
    "camera-to-route sightlines the five were blocking")
for rid, ln, nm in STILL:
    print("        STILL BLOCKED  %-40s %-5s by %s" % (rid, ln, nm))

# --- THE PAID LINES: achieved vs floor, which is this pass's acceptance test ------
# Reported here as a RAY-CAST fraction over the same body grid the derivation used. It is
# not the same instrument as tools/arrival_probe.py (which reads the SHIPPED depth plate
# after a bake) and the two will not agree to the decimal — this one is the build-time
# prediction, arrival_probe is the acceptance. Both are printed in the DAYLOG.
print()
PAID_RESULT = []
for label, a, floor in PAID:
    rays = _paidrays[label]
    clear_n = sum(1 for t in rays if visible(dg, t))
    got = clear_n / len(rays)
    PAID_RESULT.append((label, got, floor))
    print("  PAID LINE  %-28s achieved %5.1f%%  floor %5.1f%%   %s"
          % (label, got * 100, floor * 100, "OK" if got >= floor else "UNDER"))
    if got < floor:
        blockers = {}
        for t in rays:
            if not visible(dg, t):
                n = first_hit(dg, t)
                blockers[n] = blockers.get(n, 0) + 1
        for n, k in sorted(blockers.items(), key=lambda kv: -kv[1]):
            own = "OWNABLE — a re-run should have cleared it" if n and n.startswith(OWNABLE) \
                  else "NOT this pass's to move"
            print("        %2d rays blocked by %-32s %s" % (k, n, own))
log("PAID", "%d of %d paid lines meet their floor" % (sum(1 for _l, g, f in PAID_RESULT if g >= f),
                                                      len(PAID_RESULT)),
    "floors are the values these arrivals had BEFORE the vista reshape")

# =========================================================================
# B. THE THRESHOLD LANTERN — ordinary, warm, 680 W
# =========================================================================
# Runtime (20.8, 22.3, -3.2) -> blender (20.8, 3.2, 22.3), and the blend AGREES:
# a down-ray there lands on `walk_e_valley-gate__inn_landing` at z 22.30, which is
# the first landing of the flight from the rim road down to the inn — the seam
# `seam:valley-gate__inn`, whose `visibleFrac` in the auditor's gate probe is 0.00.
# That is what a threshold lantern is for.
for o in list(bpy.data.objects):
    if o.name.startswith(("ga_", "KEYGA_")):
        bpy.data.objects.remove(o, do_unlink=True)
for d in list(bpy.data.lights):
    if d.name.startswith("KEYGA_") and d.users == 0:
        bpy.data.lights.remove(d)
coll(COLL)
refresh()

MGLASS, MIRON = M("mat_lantern_glass"), M("mat_iron")
GUARD = WalkGuard(REGION)
GBVH = bvh_of(lambda n: n.startswith(("gate_road", "gate_ground", "gate_yard",
                                      "gate_corbels", "shelf_stair_underworks",
                                      "shelf_paving", "shelf_ground")))
KBVH = bvh_of(lambda n: n.startswith(("gate_arch", "gate_clutter", "gate_bunting",
                                      "gate_lantern", "gate_palisade", "gate_parapet",
                                      "shelf_clutter", "veg_")))
hit = sc.ray_cast(refresh(), Vector((SEAM.x, SEAM.y, SEAM.z + 3.0)), Vector((0, 0, -1)),
                  distance=6.0)
log("VERIFY", "seam surface", "down-ray at (%.2f, %.2f) lands on %s at z %.2f "
    "(the brief's %.2f)" % (SEAM.x, SEAM.y, hit[4].name if hit[0] else "NOTHING",
                            hit[1].z if hit[0] else -99, SEAM.z))

# The post is SEARCHED, never authored: a ring of candidate feet around the seam,
# each one required to (a) have real ground under it, (b) stand out of the walk
# corridor, and (c) have clear air for the globe.  The nearest one that passes wins;
# if none passes, nothing is built and it is COUNTED, not floated.
best = None
for r in [0.85 + 0.15 * k for k in range(8)]:
    for i in range(24):
        a = 2 * math.pi * i / 24.0
        x, y = SEAM.x + r * math.cos(a), SEAM.y + r * math.sin(a)
        g = ground_z(GBVH, x, y, from_z=SEAM.z + 2.6, depth=4.2)
        if g is None or not (SEAM.z - 1.2 <= g <= SEAM.z + 2.2):
            continue
        if not GUARD.free_box(x - 0.14, x + 0.14, y - 0.14, y + 0.14, g - 0.10, g + 2.55):
            continue
        if not clear_between(KBVH, (x, y, g), (x, y, g + 2.30), r=0.18):
            continue
        best = (x, y, g)
        break
    if best:
        break

LAMPS = []
if best is None:
    log("REFUSED", "threshold lantern", "no foot within 1.9 m of the seam had ground "
        "under it AND room outside the walk corridor — nothing was floated")
else:
    lx, ly, lz = best
    toward = Vector((SEAM.x - lx, SEAM.y - ly, 0.0))
    toward = toward.normalized() if toward.length > 1e-6 else Vector((0, -1, 0))
    gx, gy, gz_ = lx + toward.x * 0.30, ly + toward.y * 0.30, lz + 1.94
    parts = [cyl("po", (lx, ly, lz - 0.15), (lx, ly, lz + 2.26), 0.055, 8, MIRON, COLL),
             cyl("ar", (lx, ly, lz + 2.22), (gx, gy, lz + 2.18), 0.040, 6, MIRON, COLL),
             # the town's lantern, part for part the same assembly as gate_lantern_*
             # and lk_lantern_*: glass box, iron cap, iron base, four corner bars
             obox("gl", gx, gy, gz_, 0.155, 0.155, 0.26, mat=MGLASS, cname=COLL),
             obox("cp", gx, gy, gz_ + 0.17, 0.21, 0.21, 0.055, mat=MIRON, cname=COLL),
             obox("bs", gx, gy, gz_ - 0.16, 0.19, 0.19, 0.04, mat=MIRON, cname=COLL)]
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        parts.append(obox("cg", gx + sx * 0.072, gy + sy * 0.072, gz_, 0.024, 0.024, 0.34,
                          mat=MIRON, cname=COLL))
    join_meshes([p for p in parts if p], "ga_lantern_threshold", COLL)
    li = bpy.data.lights.new("KEYGA_lantern_threshold_light", 'POINT')
    li.energy = 680.0                       # the town standard, seven districts old
    li.color = (1.0, 0.58, 0.24)            # ordinary warm; NOT a Heartlight
    li.shadow_soft_size = 0.10
    li.use_custom_distance = True
    li.cutoff_distance = 14.0
    li.shadow_maximum_resolution = 0.01
    lo = bpy.data.objects.new(li.name, li)
    lo.location = (gx, gy, gz_ + 0.02)
    link(lo, COLL)
    LAMPS.append((li.name, gx, gy, gz_ + 0.02, li.energy))
    log("BUILD", "ga_lantern_threshold", "post founded by ray at (%.2f, %.2f, %.2f), "
        "globe at (%.2f, %.2f, %.2f) — 680 W warm, 14 m cutoff, the town standard "
        "(world canon: Heartlights are Emberbrook's, not Dellhollow's)"
        % (lx, ly, lz, gx, gy, gz_))


def irr(E, P, Q):
    """Point-lamp irradiance, W/m2 — the town's lighting norm is written in this
    number and spill is MEASURED, never eyeballed."""
    return E / (4.0 * math.pi * max((Vector(P) - Vector(Q)).length_squared, 0.04))


PROBES = [("stair head  (landing/seam)", (SEAM.x, SEAM.y, SEAM.z + 0.10)),
          ("stair head, eye height", (SEAM.x, SEAM.y, SEAM.z + 1.60)),
          ("flight l0 head, on the road", (17.99, 3.76, 24.10)),
          ("flight l0 midway", (19.99, 3.32, 22.98)),
          ("flight l1 foot", (23.25, 3.02, 20.78)),
          ("rim road at the seam", (20.81, 5.20, 24.10))]
print("\n  LAMP INVENTORY — gate arrival")
for (nm, x, y, z, E) in LAMPS:
    print("    %-34s %6.1f W  at (%.2f, %.2f, %.2f)  cutoff 14.0 m" % (nm, E, x, y, z))
print("  MEASURED SPILL (W/m2)")
print("    %-30s %10s %10s" % ("probe", "this lamp", "all lamps"))
for label, P in PROBES:
    mine = sum(irr(E, (x, y, z), P) for (_n, x, y, z, E) in LAMPS)
    tot = 0.0
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.data.type not in ('POINT', 'SPOT'):
            continue
        d = (Vector(o.matrix_world.translation) - Vector(P)).length
        if o.data.use_custom_distance and d > o.data.cutoff_distance:
            continue
        tot += irr(o.data.energy, o.matrix_world.translation, P)
    print("    %-30s %10.2f %10.2f" % (label, mine, tot))

# =========================================================================
# residue this assignment is not allowed to touch
# =========================================================================
print("\n" + "=" * 78)
print("RESIDUE — sightlines the five could never have fixed (NOT touched)")
print("=" * 78)
for nm, items in sorted(RESIDUE.items(), key=lambda kv: -len(kv[1])):
    kinds = sorted({rid.split("@")[0] for rid, _ln, _p in items})
    print("  %-32s %4d  %s" % (nm, len(items), ", ".join(kinds)[:110]))

print("\n" + "=" * 78)
mine = [o for o in bpy.data.objects if o.name.startswith("ga_") and o.type == 'MESH']
for o in sorted(mine, key=lambda o: o.name):
    b = world_bbox(o)
    print("  %-26s %6dv  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f"
          % (o.name, len(o.data.vertices), *b))
for name in FIVE:
    b = world_bbox(bpy.data.objects[name])
    print("  %-26s %6dv  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f"
          % (name, len(bpy.data.objects[name].data.vertices), *b))

if SHOT:
    from ga_shot import record
    record("gate", SHOT, 64)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
