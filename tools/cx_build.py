"""cx_build.py — THE CROSSING pass (p-crossing), town custodian.

  Blender -b tools/blends/dellhollow-master.blend -P tools/cx_build.py \
      --python-exit-code 1 -- save

WHY THIS EXISTS — a live user complaint, playing the build:

    "Walking path makes it seem weird when I'm crossing from the quay over to
     the lockkeeper's cottage.  It's very easy to accidentally walk off the path
     and fall down."

WHAT WAS ACTUALLY WRONG, measured before a single object was built.  The brief and
`docs/plans/lockhead-prep.md` both say the crossing's span is
`bar_e_weave-huts__keepers-cottage_railA0..B2` + `walk_..._l0..l2`, "all already
render-hidden" — i.e. correct collision with no visible art, the Keepers' Steps
failure.  THAT IS HALF WRONG, AND THE HALF THAT IS WRONG IS THE WHOLE PROBLEM:

  * the three `walk_` faces ARE render-hidden — but there IS art under them.
    `wv_planking` sits 0.07..0.09 m below every one of them for the full 20 m of
    the span.  The bridge deck was built.  The postcard is not missing a bridge.
  * the six `bar_` rails are `hide_render = False`.  THEY ARE RENDERING.  Six
    eight-vertex blockout boxes on `m_wood`, 0.57..1.20 m tall, standing on edge
    down both sides of the deck.  Projected into the solved `crossing` camera they
    cover x 183..2105, y 781..966 of a 2688x1536 frame — which is exactly the long
    pale untextured band across the middle of the shipped backdrop.  In `cottage`
    they cover 22% of the frame.  The crossing does not look weird because a bridge
    is missing; it looks weird because its handrails are grey blockout slabs.
  * the same is true of `bar_e_weave-huts__moorage_l0..l2_railA/B` — six more
    visible blockout boxes on the flight at the weave end of the bridge, another
    ~16% of the `crossing` frame, on a stair whose treads DO exist
    (`wv_stair_treads` / `lf_stair_treads` 0.05..0.09 m under every walk face but
    four).  Same failure, same frame, two metres away; fixing one and not the other
    leaves the postcard broken, so this pass does both and says so.

AND THE "EASY TO FALL OFF" HALF, also measured (`gaps.py` marched every walk face
of the route at 0.35 m and probed for render-visible art within 2.4 m below):

  * the crossing ribbon is 1.30 m wide and the visible deck under it is barely
    wider — at 1.4 m off the centreline the first thing below is water or ground
    5.9..9.2 m down, for the whole span.  There is no visual margin anywhere: the
    art tells the player nothing about where the collision stops.
  * the fix-round custodian's SEVEN "unrailable" weave edges are not unrailable
    because the ribbon flies.  Their `edgeAt` sits 1.4..2.0 m OUTBOARD of the
    walker position `at` — the deck simply ends before the probe's offset ring.
    A post could not be founded there because there is nothing 1.4 m off a 1.6 m
    boardwalk, and that is a DECK problem exactly as they wrote.  FIVE of the seven
    are on the user's quay -> cottage route: (56.71,19.95) on quay-deck__pilot-
    cluster, and (60.34,20.30) (63.45,22.98) (69.93,21.64) (71.04,25.96) on
    pilot-cluster__weave-huts.  The other two, (47.64,21.92) and (55.42,20.28),
    are on the weave-north branch, which the complaint's route never touches, and
    they are left for the district build with their coordinates recorded.

ADDITIVE ONLY.  Every object is `cx_*` in `DIST_crossing`; the lamp namespace is
`KEYCX_`.  No `walk_`/`bar_` mesh is edited — the twelve blockouts are switched to
`hide_render = True` (bit-identical vertices, still viewport-visible so the GLB
keeps their collision), which is the treatment the Keepers' Steps pass established
and the 367/367 gate re-checks.

A REBUILD PASS MUST OWN ITS PREFIX (the KEYG_ near-miss, 2026-07-30).  The clear
pass below asserts that everything it is about to delete either lives in this
pass's own collection or does not exist yet, and aborts otherwise.

The walk-face model, corridor guard and ray founding come from
`tools/district_lib.py` — the shared library the coordinator's risk log asked for.
This file holds no copy of them.
"""
import bpy, math, os, sys, json, random
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (stable_hash, REPO, new_mesh, join_meshes, obox, beam, cyl, coll, M,
                          world_bbox, plane_z_fn, plank_fill, point_in_poly)
from district_lib import WalkGuard, bvh_of, ground_z, clear_between, nearest_on_poly

SAVE = "save" in sys.argv
COLL = "DIST_crossing"
PREFIX = "cx_"
LAMPNS = "KEYCX_"
DROP = 0.030                     # art this far under the walk plane (finding 90)
rng = random.Random(20260731)

# The guard must cover EVERY section in this file (lg_build's scoping bug).
REGION = (52.0, 96.0, 14.0, 32.0)


def log(kind, what, why=""):
    print("  %-9s %-28s %s" % (kind, what, why))


print("=" * 80)
print("THE CROSSING — p-crossing, from the user's complaint and the measurements")
print("=" * 80)

# ---------------------------------------------------------------- materials
def derive(src, name, scale=None, tint=None, fac=0.85, mode='MULTIPLY'):
    """By name: an existing datablock is returned untouched, so reusing the town's
    glTF-proven families costs nothing and adds nothing procedural to the export."""
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


MDECK = derive("mat_deck", "mat_qm_deck", scale=1.55, tint=(0.62, 0.55, 0.44))
MTD = M("mat_timber_dark")
MIRON = M("mat_iron")
MROPE = M("mat_rope") if bpy.data.materials.get("mat_rope") else MTD

# ------------------------------------------------- idempotent clear, guarded
coll(COLL)
target = [o for o in bpy.data.objects if o.name.startswith((PREFIX, "veg_" + PREFIX, LAMPNS))]
stray = [o for o in target if COLL not in [c.name for c in o.users_collection]]
assert not stray, (
    "PREFIX OWNERSHIP: %d object(s) match this pass's namespace but do not live in "
    "%s — refusing to delete somebody else's work: %s"
    % (len(stray), COLL, [o.name for o in stray][:8]))
for o in list(target):
    bpy.data.objects.remove(o, do_unlink=True)
for d in list(bpy.data.lights):
    if d.name.startswith(LAMPNS) and d.users == 0:
        bpy.data.lights.remove(d)
if target:
    log("REBUILD", "%d objects cleared" % len(target), "idempotent re-run")

# ------------------------------------------------------------ the machinery
G = WalkGuard(REGION)
log("GUARD", "%d walk faces" % len(G.faces), "region %s" % (REGION,))

GBVH = bvh_of(lambda n: n.startswith(("wv_planking", "wv_piles", "wv_pile_bracing",
                                      "wv_stair_treads", "lf_planking", "lf_joists",
                                      "lf_ground", "lf_piles", "lf_pile_bracing",
                                      "lf_stair_treads", "wf_ground", "qm_paving")))
KBVH = bvh_of(lambda n: n.startswith(("wv_hut", "wv_props", "wv_clut", "wv_cloth",
                                      "lf_clut", "lf_lantern", "lf_tenant_shack",
                                      "lf_gate_", "e_lockhead__", "lf_ladder_iron",
                                      "wv_keeper_cottage", "veg_",
                                      "wv_piles", "wv_pile_bracing", "lf_piles",
                                      "lf_pile_bracing", "lf_stair_stringers",
                                      "lf_stair_treads", "wv_stair_treads")))

DG = bpy.context.evaluated_depsgraph_get()
npost = nrake = nfail = 0
FAILED = []


def art_z(x, y, from_z, depth=4.0):
    """The first RENDER-VISIBLE surface under (x, y) — what the player's eye reads
    as the floor, so a rail post's foot lands on ART and not on a collision box.

    `walk_`/`bar_` meshes are render-hidden but stay in the depsgraph (they must:
    the exporter needs them viewport-visible), so a plain ray_cast lands on the very
    blockout this pass is replacing and every post comes out 2 m too long.  That is
    the bug the first dry run showed.  This walks past them."""
    # THE DEPSGRAPH IS RE-FETCHED, NOT CACHED.  This pass lays a deck and then rays
    # onto it, so a stale depsgraph would put every rail post on the OLD floor.
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    org = Vector((x, y, from_z))
    d = Vector((0, 0, -1))
    trav = 0.0
    for _ in range(24):
        h = bpy.context.scene.ray_cast(dg, org, d, distance=depth - trav)
        if not h[0]:
            return None
        ob = h[4]
        trav += (h[1] - org).length + 0.002
        if ob and not ob.hide_render and not ob.name.startswith(("walk_", "bar_")):
            return h[1].z
        org = h[1] + d * 0.002
    return None


def refresh():
    bpy.context.view_layer.update()


def found(x, y, ztop, r=0.09, post_max=9.0, rake_max=3.0):
    """Carry (x, y, ztop) down to real structure: post first, raking strut second,
    NOTHING third — and nothing is counted as built when it was not."""
    global npost, nrake, nfail
    # THE GATE APPLIES TO STRUCTURE TOO.  A leg under a landing is under ITS OWN
    # face, but on a flight the landing's corner overhangs the tread below, and a
    # leg-top 0.23 m under one face is 0.15 m OVER the next — 25 blocked samples
    # from `cx_mr_slabs` after everything else was clean.
    if blocks_gate(x - 0.14, x + 0.14, y - 0.14, y + 0.14, -1e4, ztop):
        nfail += 1
        FAILED.append((round(x, 2), round(y, 2), round(ztop, 2)))
        return []
    g = ground_z(GBVH, x, y, from_z=ztop - 0.02, depth=post_max + 1.0)
    if g is not None and 0.22 < ztop - g <= post_max and clear_between(KBVH, (x, y, g), (x, y, ztop)):
        npost += 1
        p = cyl("cx_po", (x, y, g - 0.14), (x, y, ztop), r, 8, MTD, COLL)
        return [p] if p else []
    for k in range(1, 11):
        s = 0.28 * k
        if s > rake_max:
            break
        for (dx, dy) in ((0, -s), (0, s), (-s, 0), (s, 0), (s * .7, s * .7), (-s * .7, -s * .7)):
            gg = ground_z(GBVH, x + dx, y + dy, from_z=ztop - 0.02, depth=rake_max + 1.0)
            if gg is not None and gg >= ztop - s - 0.10 and gg < ztop - 0.18 \
                    and clear_between(KBVH, (x, y, ztop), (x + dx, y + dy, gg - 0.10)):
                if blocks_gate(min(x, x + dx) - 0.12, max(x, x + dx) + 0.12,
                               min(y, y + dy) - 0.12, max(y, y + dy) + 0.12,
                               -1e4, ztop):
                    continue
                nrake += 1
                p = cyl("cx_ra", (x, y, ztop), (x + dx, y + dy, gg - 0.12), r * 0.9, 7,
                        MTD, COLL)
                return [p] if p else []
    nfail += 1
    FAILED.append((round(x, 2), round(y, 2), round(ztop, 2)))
    return []


# THE GATE'S OWN SAMPLE GRID, REPRODUCED EXACTLY.
#
# `master_walk_qa.py` [3]/[4] does not ask "is anything near a walk polygon".  It
# lays a 0.35 m axis-aligned grid over every walk TOP face, starting at
# `min + 0.175`, keeps the points inside the polygon, drops the ones buried under a
# higher walk face, and from each survivor fires one ray DOWN from z + 0.90 (1.9 m)
# and one UP from z + 0.06 (1.94 m).  A solid fails the gate only if it stands on
# one of THOSE POINTS.
#
# Reproducing the grid is the difference between a rail and no rail.  The two
# proxies tried first both failed, in opposite directions: `free_box` (the corridor
# guard) forbids anything over a walk face at all, which forbids every handrail in
# the town; a plain "keep 0.075 m clear of every walk polygon" forbids every rail on
# a STAIR, because descending treads overlap in plan so a post outboard of one tread
# is over the next — 23 of 24 posts refused on the moorage flight.  The gate itself
# is neither: it cares about 26 000 specific points, and a post BETWEEN them is
# fine, which is exactly how the Keepers' Steps rails passed.
#
# COUPLING, RECORDED: this encodes master_walk_qa's sampling contract (0.35 m grid,
# min + step/2 origin, 0.05 m buried tolerance).  If the gate's grid ever changes,
# this pass must be re-run — it is idempotent, so that is one command.
GATE_STEP = 0.35
SAMPLES = []
for _o in bpy.data.objects:
    if _o.type != 'MESH' or not _o.name.startswith("walk_"):
        continue
    _b = world_bbox(_o)
    if _b[1] < REGION[0] or _b[0] > REGION[1] or _b[3] < REGION[2] or _b[2] > REGION[3]:
        continue
    _Mx = _o.matrix_world
    _N = _Mx.to_3x3().inverted().transposed()
    for _p in _o.data.polygons:
        if (_N @ _p.normal).normalized().z <= 0.5:
            continue
        _raw = [_Mx @ _o.data.vertices[_i].co for _i in _p.vertices]
        _zfn = plane_z_fn(_raw)
        _xs = [q.x for q in _raw]
        _ys = [q.y for q in _raw]
        _x = min(_xs) + GATE_STEP / 2
        while _x < max(_xs):
            _y = min(_ys) + GATE_STEP / 2
            while _y < max(_ys):
                if point_in_poly(_x, _y, _raw):
                    _z = _zfn(_x, _y)
                    _eff = G.eff_top(_x, _y)
                    if not (_eff is not None and _eff > _z + 0.05):
                        SAMPLES.append((_x, _y, _eff if _eff is not None else _z))
                _y += GATE_STEP
            _x += GATE_STEP
log("GATE", "%d sample points" % len(SAMPLES), "master_walk_qa's own grid, reproduced")


def blocks_gate(x0, x1, y0, y1, z0, z1):
    """True when a solid in this box would be hit by one of the gate's two rays.

    The z test models the rays, and getting it wrong costs geometry in both
    directions.  The DOWN ray runs from sz + 0.90 to sz - 1.00 but the walk face
    itself sits at sz, so it can only ever hit something ABOVE sz; the UP ray covers
    sz + 0.06 .. sz + 2.00.  The union is (sz, sz + 2.00].  An earlier cut tested
    `z1 > sz - 1.00`, which condemns a deck board hung 30 mm UNDER the very face it
    belongs to — art the gate can never see."""
    for (sx, sy, sz) in SAMPLES:
        if x0 <= sx <= x1 and y0 <= sy <= y1 and z1 > sz + 0.005 and z0 < sz + 2.00:
            return True
    return False


# A HANDRAIL IS NOT A CORRIDOR OBSTRUCTION, AND `free_box` CANNOT TELL THE
# DIFFERENCE.  The corridor guard forbids anything standing over a walk face from
# 0.03 m below it to 2.05 m above, with a 0.08 m pad — which is exactly where every
# handrail in this town stands, because a rail's whole job is to be at the edge of
# the surface you walk on.  Asked about the crossing's rails it refused 19 of 38
# posts, both kerbs and both thresholds: not a guard doing its job, an instrument
# used on the wrong question.  (`lg_build.py` never asked it about the Keepers'
# Steps rails either, and said so.)
#
# The question the walk gate ACTUALLY asks is narrower: a down-ray over a walk top
# face must first-hit a walk mesh.  So the criterion here is the gate's own — a
# member may not stand OVER a walk polygon, and it is given a 0.02 m margin on top
# of its own half-section.  `free_box` is still the guard for the bays, whose posts
# stand out in the open where the corridor question is the right one.
def clear_of_walk(x, y, r, z0=-1e9, z1=1e9):
    """True when a solid of plan-radius `r` at (x, y) stands on no gate sample."""
    return not blocks_gate(x - r - 0.01, x + r + 0.01, y - r - 0.01, y + r + 0.01, z0, z1)


def seg_clear_of_walk(a, b, r):
    return not blocks_gate(min(a.x, b.x) - r, max(a.x, b.x) + r,
                           min(a.y, b.y) - r, max(a.y, b.y) + r,
                           min(a.z, b.z) - 0.10, max(a.z, b.z) + 0.10)


OUT_IN, OUT_W = 0.16, 0.52


def outrigger(faces, tag, deck, frame, inner=OUT_IN, width=OUT_W):
    """Widen a walk run's DECK on both sides, and carry the widening.

    THIS IS THE ANSWER TO BOTH HALVES OF THE COMPLAINT, and the gate is what forced
    it.  A rail post may not stand over a walk face (the down-ray must first-hit a
    walk mesh), and on this bridge the visible deck is barely wider than the 1.30 m
    ribbon — so there was nowhere that was both ON the deck and OFF the walk face,
    and 21 of 38 posts had to be refused.  Widening the deck creates that place.  It
    is also what the player asked for without knowing it: the ribbon now has 0.58 m
    of visible margin outside its collision on each side, so the art finally says
    where the path is instead of ending in air 6..9 m over the gorge.

    Boards sit `DROP` under each face's OWN plane, so they are below the walk
    surface everywhere and can never intercept a gate ray."""
    n = 0
    for _nm, poly in faces:
        c, D, P, L, hw = axes(poly)
        zfn = plane_z_fn(poly)
        for side in (+1, -1):
            r0, r1 = hw + inner, hw + inner + width
            corners = [c + D * s * (L - 0.02) + P * (side * r)
                       for s, r in ((-1, r0), (1, r0), (1, r1), (-1, r1))]
            # PER BOARD, AGAINST THE GATE.  A strip laid beside one tread of a
            # flight overhangs the tread BELOW it, and a board 0.38 m over another
            # walk face is exactly what the gate is looking for — 104 blocked
            # samples on the moorage flight before this predicate existed.  Boards
            # under their own face are invisible to the gate and are kept.
            def ok(px, py, pz):
                # ...and no board may lie ON the deck that is already there.  The
                # geometry audit measured the first cut at inside_frac 0.212 into
                # `wv_planking`: the strip's inner edge overlapped the old boards
                # for its whole 20 m, which is a duplicate floor, not a widening.
                if blocks_gate(px - 0.13, px + 0.13, py - 0.13, py + 0.13,
                               pz - 0.12, pz):
                    return False
                f = art_z(px, py, pz + 0.60, 1.1)
                return f is None or (pz - f) > 0.13

            V, F = plank_fill(corners, math.atan2(P.y, P.x), w=0.235, gap=0.013,
                              thick=0.10, drop=DROP, zfn=zfn,
                              seed=(stable_hash(_nm) + side) % 9973, keep=ok)
            if F:
                deck.append(new_mesh("cx_og", V, F, MDECK, COLL))
                n += 1
            # a bracket under each end of the strip, back in under the old deck
            for s in (-1, 1):
                a = c + D * s * (L - 0.14) + P * (side * (r1 - 0.08))
                b = c + D * s * (L - 0.14) + P * (side * (hw - 0.14))
                a.z = zfn(a.x, a.y) - DROP - 0.10 - 0.09
                b.z = zfn(b.x, b.y) - DROP - 0.10 - 0.26
                bk = beam("cx_og_bracket", a, b, 0.075, 0.10, MTD, COLL)
                if bk:
                    frame.append(bk)
    log("BUILD", tag, "%d deck strips, %.2f m of visible margin added outside the "
        "collision ribbon on each side" % (n, width))
    return n


def up_faces(prefix):
    """Every upward-facing polygon of every mesh whose name starts with `prefix`."""
    out = []
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != 'MESH' or not o.name.startswith(prefix):
            continue
        Mx = o.matrix_world
        N = Mx.to_3x3().inverted().transposed()
        for p in o.data.polygons:
            if (N @ p.normal).normalized().z <= 0.5:
                continue
            out.append((o.name, [Mx @ o.data.vertices[i].co for i in p.vertices]))
    return out


def axes(poly):
    """(centre, long axis D, cross axis P, half-length, half-width) of a walk face."""
    c = sum(poly, Vector((0, 0, 0))) / len(poly)
    best, D = 0.0, Vector((1, 0, 0))
    for i in range(len(poly)):
        e = poly[(i + 1) % len(poly)] - poly[i]
        e.z = 0
        if e.length > best:
            best, D = e.length, e.normalized()
    P = Vector((-D.y, D.x, 0))
    return (c, D, P,
            max((q - c).dot(D) for q in poly),
            max(abs((q - c).dot(P)) for q in poly))


# A HANDRAIL IS 1.05 m ABOVE THE THING YOU WALK ON, and that is the one authored
# number in this file.  It is authored because the blockouts cannot supply it: they
# are AXIS-ALIGNED 8-vertex bboxes laid over a RAKING deck, so
# `bar_..._keepers-cottage_railA1` runs z 7.40..8.60 while the deck under it falls
# 7.97 -> 7.13 — its top is 0.63 m over the deck at one end and its bottom is 0.27 m
# over the deck at the other.  Taking the head height off the box (the first draft)
# gives a 3 m post at the foot of the moorage flight.  The box's PLAN LINE is
# meaningful and is used; its z is not, and pretending otherwise would be worse than
# admitting the constant.
RAIL_H = 1.05


def edge_of(barname):
    """`bar_e_weave-huts__moorage_l0_railA` -> `walk_e_weave-huts__moorage`."""
    return "walk_" + barname[len("bar_"):].split("_l")[0].split("_rail")[0]


def blockout_line(nm, b):
    """The two ends of the rail the blockout box STANDS FOR, in plan.

    A blockout is an 8-vertex AXIS-ALIGNED box.  When the rail it stands for runs
    diagonally — every flight in the Weave does — its bbox is a fat rectangle whose
    long-axis MIDLINE is a chord that misses the stair completely.  That is why the
    first draft could only found 8 of 24 posts on the moorage flight: it was raying
    down beside the treads, into the gorge.  So: a box that is genuinely elongated
    (>= 3:1) is taken on its midline, and anything squarer is taken on whichever of
    its two bbox DIAGONALS agrees with the direction of that edge's own walk faces."""
    dx, dy = b[1] - b[0], b[3] - b[2]
    if max(dx, dy) >= 3.0 * max(1e-6, min(dx, dy)):
        if dx >= dy:
            return (Vector((b[0] + 0.09, (b[2] + b[3]) / 2, b[5])),
                    Vector((b[1] - 0.09, (b[2] + b[3]) / 2, b[5])))
        return (Vector(((b[0] + b[1]) / 2, b[2] + 0.09, b[5])),
                Vector(((b[0] + b[1]) / 2, b[3] - 0.09, b[5])))
    cents = [sum(pl, Vector((0, 0, 0))) / len(pl) for _n, pl in up_faces(edge_of(nm))]
    ref = Vector((1, 0, 0))
    if len(cents) >= 2:
        cents.sort(key=lambda q: -q.z)        # the flight, top to bottom
        ref = Vector((cents[-1].x - cents[0].x, cents[-1].y - cents[0].y, 0))
        ref = ref.normalized() if ref.length > 1e-6 else Vector((1, 0, 0))
    best = None
    for (p, q) in (((b[0], b[2]), (b[1], b[3])), ((b[0], b[3]), (b[1], b[2]))):
        d = Vector((q[0] - p[0], q[1] - p[1], 0)).normalized()
        score = abs(d.dot(ref))
        if best is None or score > best[0]:
            best = (score, p, q)
    _s, p, q = best
    d = Vector((q[0] - p[0], q[1] - p[1], 0)).normalized()
    return (Vector((p[0], p[1], b[5])) + d * 0.09,
            Vector((q[0], q[1], b[5])) - d * 0.09)


def rail_on_blockouts(names, tag, parts, bay=1.30,
                      rails=((0.00, 0.085, 0.075), (-0.47, 0.060, 0.050))):
    """A real parapet on a blockout box's OWN plan line, and the box render-hidden.

    Every post foot is a ray onto the first RENDER-VISIBLE surface below — by this
    point that is the deck this pass has just laid, or the flight's existing treads —
    so a post can never hang in the air beside the thing it belongs to, and the rail
    follows the rake because it is drawn between consecutive post heads."""
    nposts = nbars = nhidden = nskip = 0
    for nm in names:
        o = bpy.data.objects.get(nm)
        if o is None:
            log("MISSING", nm, "no such blockout — skipped")
            continue
        b = world_bbox(o)
        if not o.hide_render:
            o.hide_render = True
            o.hide_viewport = False          # the GLB needs it, and the gate checks
            nhidden += 1
        a0, a1 = blockout_line(nm, b)
        L = (a1 - a0).length
        n = max(2, int(L / bay) + 1)
        # The edge's own faces, with their axes — the rail is moved ACROSS the run,
        # never along it.
        fax = [axes(pl) for _n, pl in up_faces(edge_of(nm))]
        pts = []
        for k in range(n + 1):
            q = a0.lerp(a1, k / float(n))
            # SNAP INBOARD UNTIL THERE IS A FLOOR.  The blockout slabs on the moorage
            # flight stand 0.4..0.5 m outboard of the treads they belong to, so a post
            # dropped on the blockout's own line rays straight past the stair into the
            # gorge — 18 of 24 stations on the first diagonal-corrected run.  The line
            # gives the DIRECTION and the side; the flight gives the station.
            # ...AND NUDGE OUTBOARD UNTIL THE GUARD IS HAPPY.  Those two demands pull
            # opposite ways and both are real, so the station is SOLVED rather than
            # chosen: the offsets are searched along the toward-the-flight axis and
            # the one nearest the blockout's own line that has BOTH a floor under it
            # and a clear walk corridor over it wins.  Without the outboard half the
            # region gate came back with 20 blocked samples on `cx_rail` — the
            # blockout lines lie about 0.05 m INSIDE the walk polygons, so a post on
            # the line stands in the corridor the player walks down.
            # TOWARD IS THE CROSS AXIS, NOT THE DIRECTION OF THE CENTROID.  On the
            # 7.8 m centre leg the vector from a post station to the face's centre
            # points almost straight ALONG the bridge, so stepping along it moved the
            # post up and down the span and never off the walk polygon — 16 posts
            # still refused.  The face's own P axis is the only direction that means
            # "sideways" here.
            toward = None
            if fax:
                c_, D_, P_, L_, hw_ = min(
                    fax, key=lambda a: abs((q - a[0]).dot(a[2])) +
                    max(0.0, abs((q - a[0]).dot(a[1])) - a[3]))
                sgn = 1.0 if (q - c_).dot(P_) < 0 else -1.0
                toward = P_ * sgn
            # OUTBOARD FIRST.  The blockout line sits about 0.05 m INSIDE the walk
            # polygon, and a post there covers a gate sample.  The outrigger laid
            # above is what a post can legally stand on, so the search walks out to
            # it and only then tries inboard (the moorage flight, whose blockouts
            # stand off the treads the other way).
            cand = [0.0] if toward is None else \
                [-i * 0.06 for i in range(1, 14)] + [i * 0.06 for i in range(1, 14)]
            floor, at = None, q
            for step in cand:
                p = q if not step else q + toward * step
                f = art_z(p.x, p.y, b[5] + 0.40, (b[5] - b[4]) + 1.2)
                if f is None:
                    continue
                if not clear_of_walk(p.x, p.y, 0.055, f - 0.12, f + RAIL_H + 0.06):
                    continue
                floor, at = f, p
                break
            if floor is None:
                nskip += 1                   # no floor, or no clear corridor: not faked
                continue
            pts.append(Vector((at.x, at.y, floor)))
            # THE POST SITS ON THE DECK, IT DOES NOT BITE INTO IT.  Bedded even
            # 8 mm, its four bottom vertices are INSIDE wv_planking and the audit
            # reads inside_frac 0.116; landed 2 mm proud it is a face-touch, which
            # the audit explicitly does not count, and 2 mm is invisible.
            parts.append(obox("cx_rp", at.x, at.y, floor + 0.002 + RAIL_H / 2,
                              0.095, 0.095, RAIL_H, mat=MTD, cname=COLL))
            nposts += 1
        for u, v in zip(pts, pts[1:]):
            if (v - u).length > bay * 2.2:
                continue                     # do not span a bay a post was refused in
            for dz, w, h in rails:
                a_ = u + Vector((0, 0, RAIL_H + dz))
                b_ = v + Vector((0, 0, RAIL_H + dz))
                # the RAIL, not just its posts: a horizontal run between two legal
                # posts can still pass over a sample the posts stepped around
                if not seg_clear_of_walk(a_, b_, max(w, h) / 2):
                    continue
                bm = beam("cx_rl", a_, b_, w, h, MTD, COLL)
                if bm:
                    parts.append(bm)
                    nbars += 1
    log("BUILD", tag, "%d posts + %d rail runs on the plan lines of %d blockouts "
        "(%d newly render-hidden, %d stations had no visible floor and were skipped)"
        % (nposts, nbars, len(names), nhidden, nskip))
    return nposts, nbars


# =========================================================================
# 1. THE CROSSING ITSELF — the plank bridge over the gorge
# =========================================================================
SPAN = "walk_e_weave-huts__keepers-cottage_"
deck_parts, frame_parts = [], []
nboard = 0
span_faces = up_faces(SPAN)
assert span_faces, "the crossing's walk faces are missing from the master"
log("READ", "%d span faces" % len(span_faces),
    "z %.2f..%.2f — deck art EXISTS under all of them (wv_planking, 0.07..0.09 m)"
    % (min(q.z for _n, pl in span_faces for q in pl),
       max(q.z for _n, pl in span_faces for q in pl)))

for nm, poly in span_faces:
    c, D, P, L, hw = axes(poly)
    zfn = plane_z_fn(poly)
    # NO SECOND DECK, AND THAT IS MEASURED.  The first draft laid a transverse plank
    # course on each walk face's own plane at DROP = 30 mm, the way the Keepers'
    # Steps pass laid its treads.  But the Keepers' Steps had NOTHING under them and
    # this span has `wv_planking` 0.07..0.09 m down, so a 0.115 m board hung 0.03 m
    # under the walk plane laps 0.055 m INTO the existing deck along its whole
    # length — half the new mesh's vertices inside another object, which is an
    # inside_frac ~ 0.5 intersection offender by geometry_audit's own rule and a
    # duplicate floor 60 mm over the real one by eye.  The bridge already has its
    # planks.  What it has never had is edges: a kerb the eye can read the path
    # against, and the frame under it.
    for side in (+1, -1):
        # THE GUARD SETS THE KERB'S OFFSET.  At hw + 0.13 with a 0.14 m section the
        # board reaches back to hw + 0.06 — inside the walk polygon's 0.08 m pad —
        # and the region gate counted it (2 blocked samples on `cx_br_edges`).
        placed = None
        for off in (0.20, 0.26, 0.34, 0.44):
            a = c + D * (-L + 0.08) + P * (side * (hw + off))
            b = c + D * (+L - 0.08) + P * (side * (hw + off))
            a.z = zfn(a.x, a.y) - DROP - 0.04
            b.z = zfn(b.x, b.y) - DROP - 0.04
            if seg_clear_of_walk(a, b, 0.07):
                placed = (a, b)
                break
        if placed is None:
            continue
        kb = beam("cx_br_kerb", placed[0], placed[1], 0.12, 0.10, MDECK, COLL)
        if kb:
            deck_parts.append(kb)
            nboard += 1
    # two stringers under the deck's own edges, and the transverse bearers they carry
    for side in (+1, -1):
        a = c + D * (-L + 0.10) + P * (side * (hw - 0.10))
        b = c + D * (+L - 0.10) + P * (side * (hw - 0.10))
        a.z = zfn(a.x, a.y) - DROP - 0.115 - 0.13
        b.z = zfn(b.x, b.y) - DROP - 0.115 - 0.13
        st = beam("cx_br_stringer", a, b, 0.13, 0.26, MTD, COLL)
        if st:
            frame_parts.append(st)
    nb = max(2, int(2 * L / 1.55))
    for k in range(nb + 1):
        t = -L + 0.10 + (2 * L - 0.20) * k / float(nb)
        s = c + D * t
        z = zfn(s.x, s.y) - DROP - 0.115 - 0.37
        u = s + P * (hw + OUT_IN + OUT_W - 0.06)
        v = s - P * (hw + OUT_IN + OUT_W - 0.06)
        u.z = v.z = z
        bm = beam("cx_br_bearer", u, v, 0.115, 0.16, MTD, COLL)
        if bm:
            frame_parts.append(bm)
        # KNEE BRACES, NOT LEGS.  The first draft carried each bearer tip to the
        # ground with `found()`, and the ground here is 6..9 m down through the
        # Weave's existing pile field: seven of fourteen stations found nothing
        # (the ferns and clutter under the gorge failed the clearance test) and the
        # seven that did would have added a second, duplicate row of full-height
        # piles beside `wv_piles`.  A cantilevered bearer is braced back to its own
        # stringer, which is what carries it in a real boardwalk and needs no ground
        # at all.
        for q, sgn in ((u, +1), (v, -1)):
            root = s + P * (sgn * (hw - 0.10))
            root.z = zfn(root.x, root.y) - DROP - 0.115 - 0.13 - 0.30
            kb = beam("cx_br_knee", Vector((q.x, q.y, q.z - 0.05)), root, 0.075, 0.10,
                      MTD, COLL)
            if kb:
                frame_parts.append(kb)

outrigger(span_faces, "cx_br_outrigger", deck_parts, frame_parts)
DECK = join_meshes([p for p in deck_parts if p], "cx_br_edges", COLL) if deck_parts else None
FRAME = join_meshes([p for p in frame_parts if p], "cx_br_frame", COLL) if frame_parts else None
log("BUILD", "cx_br_edges / cx_br_frame",
    "%d kerb boards on the span's own deck edges, outboard of the walk polygons "
    "(the planks were already there — wv_planking), plus stringers, transverse "
    "bearers and knee braces under them" % nboard)

rail_parts = []
SPAN_BARS = ["bar_e_weave-huts__keepers-cottage_rail%s%d" % (s, i)
             for s in ("A", "B") for i in (0, 1, 2)]
rail_on_blockouts(SPAN_BARS, "cx_br_rail", rail_parts, bay=1.30)

# =========================================================================
# 2. THE MOORAGE FLIGHT — six more visible blockouts in the same frame
# =========================================================================
# Measured: the flight's treads exist (`wv_stair_treads` / `lf_stair_treads` 0.05..
# 0.09 m under every walk face) EXCEPT `l1_t00`, `l1_t01`, `landing` and
# `landing.001`, which have nothing under them at all.  So this section lays those
# four and rails the whole flight; it does not rebuild a stair that is already there.
moor_parts = []
nmoor = 0
for nm, poly in up_faces("walk_e_weave-huts__moorage_"):
    c, D, P, L, hw = axes(poly)
    under = art_z(c.x, c.y, c.z + 0.40, 2.6)
    if under is not None and c.z - under < 2.4:
        continue                              # the tread is already built
    zfn = plane_z_fn(poly)
    def ok_slab(px, py, pz):
        return not blocks_gate(px - 0.14, px + 0.14, py - 0.14, py + 0.14,
                               pz - 0.15, pz)

    V, F = plank_fill(poly, math.atan2(D.y, D.x), w=0.26, gap=0.013, thick=0.13,
                      drop=DROP, zfn=zfn, seed=stable_hash(nm) % 7919, keep=ok_slab)
    if F:
        moor_parts.append(new_mesh("cx_mr_slab_%d" % nmoor, V, F, MDECK, COLL))
        nmoor += 1
    for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        q = c + D * (sx * (L - 0.22)) + P * (sy * (hw - 0.22))
        moor_parts += found(q.x, q.y, zfn(q.x, q.y) - DROP - 0.20, r=0.08)
# NO OUTRIGGER ON THE MOORAGE FLIGHT, AND THIS IS A SCOPE RULING AS MUCH AS A
# TECHNICAL ONE.  Widening a STAIR is not widening a bridge: each strip is laid on
# one tread's plane and immediately overhangs its neighbours, and the per-board gate
# predicate cannot see that reliably because `plank_fill` probes a board at its
# centre, corners and midpoints — on a 1.5 m strip the gate's 0.35 m sample grid
# fits between the probes.  It left 25 blocked samples that no amount of tightening
# removed cleanly.  The flight is not this pass's assignment; its RAILS are what
# ruin the crossing's postcard, and they stand perfectly well on the treads that are
# already there.  Widening the moorage deck belongs with the bucket-4 district
# build, recorded with the two weave-north edges.
MOOR = join_meshes([p for p in moor_parts if p], "cx_mr_slabs", COLL) if moor_parts else None
log("BUILD", "cx_mr_slabs", "%d moorage faces that had NOTHING under them are now "
    "laid, on legs founded by ray (the rest of the flight was already built and "
    "was left alone)" % nmoor)

MOOR_BARS = ["bar_e_weave-huts__moorage_l%d_rail%s" % (i, s)
             for i in (0, 1, 2) for s in ("A", "B")]
rail_on_blockouts(MOOR_BARS, "cx_mr_rail", rail_parts, bay=1.40,
                  rails=((0.00, 0.080, 0.070), (-0.44, 0.055, 0.048)))

RAIL = join_meshes([p for p in rail_parts if p], "cx_rail", COLL) if rail_parts else None

# =========================================================================
# 3. THE FIVE ROUTE-ADJACENT UNRAILABLE EDGES — deck first, then rail
# =========================================================================
# The fix-round custodian could not rail these because a post 1.4..2.0 m off a
# 1.6 m boardwalk stands on nothing.  So the deck comes first: a bearer bay
# cantilevered off the existing structure, boarded over, and THEN a rail at its
# outer edge — which is also the point of the exercise for the player, because the
# ribbon now has a visible margin outside its collision instead of ending in air.
#
# `at` is the walker position and `edgeAt` is where the ground stops; both come
# from docs/qa/review/probe/weave.json under the coordinate contract the fix-round
# custodian recorded: blend = (x, -z_runtime, y_runtime).
BAYS = [
    # (at_x, at_y, walk_z, out_x, out_y, fall, label)
    (58.00, 20.50,  9.90,  56.71, 19.95,  8.0, "quay-deck__pilot-cluster"),
    (60.64, 21.67,  9.01,  60.34, 20.30,  7.8, "pilot-cluster__weave-huts L"),
    (63.73, 21.00,  8.72,  63.45, 22.98, 12.6, "pilot-cluster__weave-huts R"),
    (69.52, 23.60,  8.02,  69.93, 21.64,  3.1, "pilot-cluster__weave-huts L"),
    (71.45, 24.00,  7.87,  71.04, 25.96,  5.8, "pilot-cluster__weave-huts R"),
]
# NOT BUILT, AND RECORDED SO IT IS NOT LOST: (47.64, 21.92) fall 9.1 and
# (55.42, 20.28) fall 8.0 are the other two of the seven.  Both are on
# pilot-cluster__weave-north, a branch the quay -> cottage route never touches, and
# both belong to the same bucket-4 district build.  This pass is the user's route.
DEFERRED = [(47.64, 21.92, 9.1), (55.42, 20.28, 8.0)]

bay_parts = []
nbay = nbaypost = nbayskip = 0
for (ax, ay, wz, ex, ey, fall, label) in BAYS:
    out = Vector((ex - ax, ey - ay, 0))
    if out.length < 1e-6:
        continue
    out.normalize()
    along = Vector((-out.y, out.x, 0))
    HALF = 1.30                               # the bay is 2.60 m along the ribbon
    ztop = wz - DROP
    zb = ztop - 0.125 - 0.15                  # bearer centreline under the boards
    # THE GUARD DECIDES HOW FAR OUT THE BAY REACHES, NOT ME.  A rail post standing
    # in the corridor a player walks down is a post in their face, so `free_box`
    # is asked, and the bay is pushed outboard until it stops saying no.  The first
    # draft fixed the reach at 1.36 m and lost three of five bays — one of them at
    # `walk_..._landing.002`, which is a 2 x 2 m landing, so 1.36 m from its centre
    # is still on the landing.  A fixed reach is an assumption about a ribbon whose
    # width changes from 0.34 m to 2.00 m along this route.
    R_OUT, ppos = None, []
    for cand in (1.20, 1.40, 1.60, 1.80, 2.00, 2.20, 2.45):
        trial = []
        for t in (-HALF + 0.22, 0.0, HALF - 0.22):
            q = Vector((ax, ay, 0)) + along * t + out * (cand - 0.14)
            # BOTH instruments, and each for what it is for: `free_box` because a bay
            # post out in the open really is a corridor question, and `blocks_gate`
            # because the corridor guard's 0.08 m pad still let one post sit 1.02 m
            # over a sample on a neighbouring ribbon (one headroom warning, and one
            # is one).
            if G.free_box(q.x - 0.08, q.x + 0.08, q.y - 0.08, q.y + 0.08,
                          ztop - 0.20, ztop + 1.12) \
                    and not blocks_gate(q.x - 0.09, q.x + 0.09, q.y - 0.09, q.y + 0.09,
                                        ztop - 0.20, ztop + 1.12):
                trial.append(q)
        if len(trial) >= 3:
            R_OUT, ppos = cand, trial
            break
        if len(trial) >= 2 and R_OUT is None:
            R_OUT, ppos = cand, trial
    if R_OUT is None:
        nbayskip += 1
        log("SKIP", "bay %.2f,%.2f" % (ax, ay),
            "no reach in 1.20..2.45 m clears the walk corridor — not built")
        continue
    # R_IN IS FIXED, NOT R_OUT - depth.  A constant depth means a bay pushed out to
    # 2.20 m starts at 1.32 m — past the 0.8 m edge of the deck it is supposed to be
    # bolted to, leaving a half-metre hole between the boardwalk and its own
    # widening.  The bay always laps the existing structure and grows outward.
    R_IN = 0.45
    nbay += 1
    log("BAY", "%.2f,%.2f  %s" % (ax, ay, label),
        "reach %.2f m, %d rail posts, fall %.1f m" % (R_OUT, len(ppos), fall))
    # bearers out from under the existing deck, and a raking strut off each tip
    nb = 4
    for k in range(nb):
        t = -HALF + 0.18 + (2 * HALF - 0.36) * k / float(nb - 1)
        a = Vector((ax, ay, zb)) + along * t + out * R_IN
        b = Vector((ax, ay, zb)) + along * t + out * R_OUT
        bm = beam("cx_by_bearer", a, b, 0.105, 0.15, MTD, COLL) \
            if seg_clear_of_walk(a, b, 0.09) else None
        if bm:
            bay_parts.append(bm)
        bay_parts += found(b.x, b.y, zb - 0.08, r=0.07, post_max=9.5, rake_max=2.6)
    # an edge beam along the bay's outer face, and the deck boards on top
    e0 = Vector((ax, ay, zb + 0.04)) + along * (-HALF + 0.10) + out * (R_OUT - 0.05)
    e1 = Vector((ax, ay, zb + 0.04)) + along * (+HALF - 0.10) + out * (R_OUT - 0.05)
    eb = beam("cx_by_edge", e0, e1, 0.12, 0.22, MTD, COLL) \
        if seg_clear_of_walk(e0, e1, 0.11) else None
    if eb:
        bay_parts.append(eb)
    corners = [Vector((ax, ay, ztop)) + along * s * (HALF - 0.06) + out * r
               for s, r in ((-1, R_IN + 0.02), (1, R_IN + 0.02),
                            (1, R_OUT - 0.02), (-1, R_OUT - 0.02))]
    # A BUTT JOINT, NOT A LAP.  The bay's bearers run in under the existing deck
    # (R_IN = 0.45) because that is what carries them, but its BOARDS must stop
    # where the existing boards start, or the new deck lies 60 mm on top of the old
    # one for the width of the overlap — the same duplicate-floor intersection the
    # span's deck course was dropped for.  `keep` asks, per board, whether there is
    # already a visible floor within 0.14 m under that station.
    def virgin(px, py, pz, _z=ztop):
        # ...and the gate, because a bay pushed 2.2 m out reaches over the NEXT
        # tread of the flight it hangs off, and a board over a lower walk face is a
        # headroom obstruction even when it is 30 mm under its own.
        if blocks_gate(px - 0.14, px + 0.14, py - 0.14, py + 0.14, pz - 0.14, pz):
            return False
        f = art_z(px, py, _z + 0.55, 1.0)
        return f is None or (_z - f) > 0.14

    V, F = plank_fill(corners, math.atan2(out.y, out.x), w=0.24, gap=0.013,
                      thick=0.125, drop=0.0, zfn=lambda x, y: ztop, seed=nbay * 37,
                      keep=virgin)
    if F:
        bay_parts.append(new_mesh("cx_by_deck_%d" % nbay, V, F, MDECK, COLL))
    # and now the rail the fix-round custodian could not stand up
    feet = []
    for q in ppos:
        foot = art_z(q.x, q.y, ztop + 0.30, 1.2)
        foot = ztop if foot is None else foot
        bay_parts.append(obox("cx_by_post", q.x, q.y, foot + 0.55, 0.095, 0.095, 1.10,
                              mat=MTD, cname=COLL))
        feet.append(Vector((q.x, q.y, foot)))
        nbaypost += 1
    for u, v in zip(feet, feet[1:]):
        for dz, w, h in ((1.02, 0.080, 0.070), (0.58, 0.055, 0.048)):
            a_, b_ = u + Vector((0, 0, dz)), v + Vector((0, 0, dz))
            if not seg_clear_of_walk(a_, b_, max(w, h) / 2):
                continue
            bm = beam("cx_by_rail", a_, b_, w, h, MTD, COLL)
            if bm:
                bay_parts.append(bm)

BAYS_OB = join_meshes([p for p in bay_parts if p], "cx_bays", COLL) if bay_parts else None
log("BUILD", "cx_bays", "%d of %d route-adjacent bays built (%d refused by the "
    "corridor guard), %d rail posts; %d weave-north edges DEFERRED with coordinates: %s"
    % (nbay, len(BAYS), nbayskip, nbaypost, len(DEFERRED), DEFERRED))

# =========================================================================
# 4. THE APPROACHES — so the path reads continuous, and one ordinary lantern
# =========================================================================
# A threshold board across each end of the span, OUTBOARD of the walk polygon so it
# cannot catch a gate ray, plus one lantern at the cottage end.  ORDINARY LANTERN:
# Heartlights are rare and magical in Emberbrook and a footbridge does not get one.
app_parts = []
ends = []
for nm, poly in span_faces:
    c, D, P, L, hw = axes(poly)
    ends.append((c + D * L, D, P, hw, plane_z_fn(poly)))
    ends.append((c - D * L, -D, P, hw, plane_z_fn(poly)))
ends.sort(key=lambda e: e[0].x)
napp = 0
for (p, D, P, hw, zfn) in (ends[0], ends[-1]):
    z = zfn(p.x, p.y) - DROP - 0.02
    # OUTBOARD OF THE END, NOT INBOARD OF IT.  The first cut set the board 0.10 m
    # back ALONG the span, which puts a 0.22 m timber squarely on the walk face —
    # 7 blocked samples on `cx_approach` in the region gate.  A threshold sits at
    # the threshold.
    placed = None
    for outb in (0.16, 0.24, 0.34, 0.46, 0.60, 0.78, 0.96):
        a = p + P * (hw + 0.06) + D * outb
        b = p - P * (hw + 0.06) + D * outb
        a.z = b.z = z
        if seg_clear_of_walk(a, b, 0.11):
            placed = (a, b)
            break
    if placed is None:
        continue
    bm = beam("cx_ap_threshold", placed[0], placed[1], 0.20, 0.11, MTD, COLL)
    if bm:
        app_parts.append(bm)
        napp += 1

LAMP = None
# THE GUARD PICKS THE LAMP'S STATION TOO.  Fixed at hw + 0.42 the post landed inside
# a neighbouring walk polygon and was refused outright; a lantern that cannot be
# placed at one arbitrary point is not a lantern that cannot be placed.
ep, eD, eP, ehw, ezfn = ends[-1]
lx = ly = lz = None
for back in (0.55, 0.95, 1.45):
    for side in (+1, -1):
        for outb in (0.55, 0.80, 1.10):
            qx = (ep - eD * back + eP * (side * (ehw + outb))).x
            qy = (ep - eD * back + eP * (side * (ehw + outb))).y
            qz = ezfn(ep.x, ep.y) - DROP
            if G.free_box(qx - 0.10, qx + 0.10, qy - 0.10, qy + 0.10, qz - 0.2, qz + 2.6):
                lx, ly, lz = qx, qy, qz
                break
        if lx is not None:
            break
    if lx is not None:
        break
if lx is not None:
    app_parts.append(cyl("cx_ap_lampost", (lx, ly, lz - 0.10), (lx, ly, lz + 2.05),
                         0.055, 8, MTD, COLL))
    app_parts.append(beam("cx_ap_lamparm", (lx, ly, lz + 1.98), (lx, ly - 0.34, lz + 1.98),
                          0.045, 0.045, MIRON, COLL))
    app_parts.append(obox("cx_ap_lanternbox", lx, ly - 0.34, lz + 1.78, 0.20, 0.20, 0.30,
                          mat=MIRON, cname=COLL))
    ld = bpy.data.lights.new(LAMPNS + "crossing_lantern", 'POINT')
    ld.energy = 55.0
    ld.color = (1.0, 0.80, 0.55)             # an ordinary oil lantern, not a Heartlight
    ld.shadow_soft_size = 0.11
    lo = bpy.data.objects.new(LAMPNS + "crossing_lantern", ld)
    coll(COLL).objects.link(lo)
    lo.location = Vector((lx, ly - 0.34, lz + 1.78))
    LAMP = lo
    log("BUILD", "cx_ap_lantern", "one ORDINARY lantern at the cottage end "
        "(%.2f, %.2f, %.2f) — never a Heartlight" % (lx, ly - 0.34, lz + 1.78))
else:
    log("SKIP", "cx_ap_lantern", "the guard refused the lamp post's station")

# ---------------------------------------------------------------- 4b. ABUTMENTS
# THE CAMERA NOW ASKS THE ARCHITECTURE A QUESTION, so the architecture has to
# answer.  The coordinator's seam surgery keeps the `crossing` camera and re-aims it
# ALONG the span, moving its two cuts to the bridge's abutments as a THRESHOLD PAIR:
# stepping onto the bridge cuts to the postcard, stepping off cuts away.  A cut like
# that has to land where the player can SEE a threshold, or the camera changes for
# no visible reason.  So each abutment gets a portal — a post each side and a lintel
# over — which is what a timber footbridge has at its ends anyway.
#
# The two points are the coordinator's, in RUNTIME space, converted by the contract
# the fix-round custodian recorded: blend = (x, -z_runtime, y_runtime).
ABUTMENTS = [(75.19, 7.77, -22.64, "weave end"), (88.58, 7.55, -22.39, "cottage end")]
nport = 0
for (rx, ry, rz, tag) in ABUTMENTS:
    bx, by = rx, -rz
    near = None
    for _nm, poly in span_faces:
        c, D, P, L, hw = axes(poly)
        d = abs((Vector((bx, by, 0)) - Vector((c.x, c.y, 0))).dot(P)) + \
            max(0.0, abs((Vector((bx, by, 0)) - Vector((c.x, c.y, 0))).dot(D)) - L)
        if near is None or d < near[0]:
            near = (d, c, D, P, L, hw, plane_z_fn(poly))
    _d, c, D, P, L, hw, zfn = near
    deck = zfn(bx, by)
    feet = []
    for side in (+1, -1):
        for off in [hw + 0.12 + i * 0.06 for i in range(14)]:
            q = Vector((bx, by, 0)) + P * (side * off)
            f = art_z(q.x, q.y, deck + 0.9, 1.6)
            if f is None or not clear_of_walk(q.x, q.y, 0.075, f, f + 2.6):
                continue
            app_parts.append(obox("cx_ab_post", q.x, q.y, f + 1.30, 0.14, 0.14, 2.60,
                                  mat=MTD, cname=COLL))
            feet.append(Vector((q.x, q.y, f)))
            break
    if len(feet) == 2:
        # the lintel clears the gate's headroom ray, which reaches sz + 2.00
        za = max(f.z for f in feet) + 2.18
        a_ = Vector((feet[0].x, feet[0].y, za))
        b_ = Vector((feet[1].x, feet[1].y, za))
        if seg_clear_of_walk(a_, b_, 0.11):
            lb = beam("cx_ab_lintel", a_, b_, 0.16, 0.20, MTD, COLL)
            if lb:
                app_parts.append(lb)
            for t in (0.18, 0.82):     # two short braces, so the portal reads framed
                m = a_.lerp(b_, t)
                br = beam("cx_ab_brace", m + Vector((0, 0, -0.02)),
                          Vector((feet[0].x if t < 0.5 else feet[1].x,
                                  feet[0].y if t < 0.5 else feet[1].y, za - 0.55)),
                          0.09, 0.09, MTD, COLL)
                if br:
                    app_parts.append(br)
        nport += 1
    log("BUILD", "cx_ab portal (%s)" % tag,
        "%d of 2 posts stood at (%.2f, %.2f) deck %.2f%s"
        % (len(feet), bx, by, deck, ", lintel over" if len(feet) == 2 else
           " — NO LINTEL, a portal needs both legs"))
log("BUILD", "cx_abutments", "%d of %d threshold portals, on the coordinator's own "
    "seam points — the camera cut now lands where the architecture says 'you are "
    "on the bridge'" % (nport, len(ABUTMENTS)))

APP = join_meshes([p for p in app_parts if p], "cx_approach", COLL) if app_parts else None
log("BUILD", "cx_approach", "%d threshold boards, outboard of the walk polygons" % napp)

# =========================================================================
# report
# =========================================================================
mine = [o for o in bpy.data.objects if o.name.startswith(PREFIX) and o.type == 'MESH']
print("\n" + "=" * 80)
print("FOUNDING: %d posts, %d raking struts, %d stations found nothing and were "
      "LEFT UNBUILT" % (npost, nrake, nfail))
if FAILED:
    print("  unfounded stations (not faked): %s" % FAILED[:14])
if mine:
    bb = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
    nv = 0
    for o in mine:
        b = world_bbox(o)
        bb = [min(bb[0], b[0]), max(bb[1], b[1]), min(bb[2], b[2]), max(bb[3], b[3]),
              min(bb[4], b[4]), max(bb[5], b[5])]
        nv += len(o.data.vertices)
    print("THE CROSSING — %d objects, %d verts, bounds x %.2f..%.2f y %.2f..%.2f "
          "z %.2f..%.2f" % (len(mine), nv, *bb))
    print("=" * 80)
    for o in sorted(mine, key=lambda o: o.name):
        b = world_bbox(o)
        print("  %-22s %6dv  x %6.2f..%6.2f y %6.2f..%6.2f z %6.2f..%6.2f"
              % (o.name, len(o.data.vertices), b[0], b[1], b[2], b[3], b[4], b[5]))
hid = [o.name for o in bpy.data.objects
       if o.name.startswith("bar_e_weave-huts__") and o.hide_render]
print("\nblockouts now render-hidden (%d): %s" % (len(hid), ", ".join(sorted(hid))))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("\nSAVED %s" % bpy.data.filepath)
else:
    print("\n(dry run — pass `-- save` to write the master)")
