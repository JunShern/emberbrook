"""master_rail_trim.py — trim stair railings back off the FLAT deck they start on.

  Blender -b <blend> -P tools/master_rail_trim.py -- [--apply] [--save]

Why this exists
---------------
The town's `bar_*_rail*` meshes are generated one per stair LEG.  When a leg is a
flat approach across a deck (the generator emits `l0` as a landing-level run
before the flight actually starts), its railing is a 4 m fence standing on open
decking.  With volume collision that fence is a real wall: on the quay it closes
the market -> quay crossing.

Rule (from the map generator, mirrored here): **a rail only earns its length
where it is guarding something.**  A sample of the rail is "guarding" when either

  * the walk surface under it is SLOPED (it is following a flight), or
  * the ground within 1.6 m to either side is >= 0.30 m lower, or missing
    entirely (the rail stands on the lip of a drop / a deck edge over water).

Contiguous runs of NON-guarding samples at the HEAD or the TAIL of a rail are
flat-deck overshoot and are trimmed away.  The rail is shortened, never deleted:
a 0.60 m newel stub is always left at the flight end so the guard still reads as
starting somewhere.  Middles are never carved (a rail that dips across a landing
between two flights is one rail).

Every `bar_*` rail is an 8-vertex extruded box, so the trim is exact: each vertex
is slid along the rail's own end-to-end vector (which carries the slope with it),
which preserves the section, the material and the vertex count.

The trimmed rails are a DELIBERATE, documented departure from the topology
reference.  Run this against BOTH `dellhollow-master.blend` and the topology
reference `dellhollow-town.blend` and delete the reference cache, so
`master_walk_qa.py` keeps comparing like with like.
"""
import bpy, sys, os, math
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import Corridor, dist_poly2, plane_z_fn

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
APPLY = "--apply" in argv
SAVE = "--save" in argv
# --only NAME[,NAME...]  — apply to these rails and REPORT the rest.
# Added with the fouling criterion (finding 226): that criterion finds 13 rails
# town-wide, in six districts, and a custodian may only edit its own.  The two
# the vertical-slice audit assigned to the quay-market tier are applied; the other
# eleven are reported for the custodians who own them.  A lint that quietly
# reaches into someone else's parcel is how the merge lesson (git-index
# discipline) got written.
ONLY = None
if "--only" in argv:
    ONLY = set(argv[argv.index("--only") + 1].split(","))

DROP = 0.30          # a guard needs this much fall beside it
SLOPE = 0.14         # ... or this much rise per metre under it (a flight)
PROBE = 1.6          # how far to either side we look for the drop
STUB = 0.60          # never shorten past this much rail at the flight end
MIN_TRIM = 0.45      # ignore nibbles
PLAYER = 0.45        # a walking body's half-width, for the FOULING test below

# --------------------------------------------------------------------------
# CRITERION 2, added 2026-07-30 (quay-market custodian, finding 226): FOULING
# --------------------------------------------------------------------------
# The guard test above asks whether a rail EARNS its length.  It cannot see the
# other failure, which the vertical-slice agent's walkability audit found twice in
# one night: a rail that earns every metre of its length by guarding its own drop,
# and spends some of those metres standing in SOMEONE ELSE'S walking line.
# Two real cases, both measured before this code was written:
#
#   bar_e_deep-stairs-head__deep-stairs-foot_l2_railB — the Deep Stairs are a
#   hairpin, and this rail runs 0.66 m PAST the foot of its own flight, which
#   puts its last 1.3 m directly inside `..._l3_t01/t02/t03` (measured d = 0.00,
#   rail 1.4..1.8 m above those treads).  A body descending l3 walks into a rail
#   at head height: the flight is impassable and nothing in the guard test can
#   tell, because the rail IS guarding a drop the whole way down.
#
#   bar_e_shelf-homes__market-stalls_l0_railB — the shop street's two flights to
#   the market interleave in plan (both leave `walk_pad_shelf-homes` eastward
#   through y 8.1..9.7 at different rates), so this rail runs 0.45 m off the edge
#   of `walk_e_shelf-homes__quay-deck_landing` and 1.7..2.0 m above it, i.e.
#   inside that landing's 2.05 m corridor, for 1.5 m of its length.
#
# A sample FOULS when it lies within PLAYER of a walk face that is
#   * not its own leg's, and
#   * not a LANDING of its own route (a rail legitimately starts and ends at the
#     landings of the flight it belongs to), and
#   * not a pad or landmark slab of either of its own endpoints,
# and its own height is inside that face's walking corridor.
#
# Head and tail are then cut to the LAST foul on the way in and the FIRST foul on
# the way out.  Middles are still never carved — where the only fouls are in the
# middle the rail is reported and left alone for a human, because carving a
# railing in half is a modelling decision, not a lint.

walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
COR = Corridor(walks, margin=0.0)

FACES = []
for _o in walks:
    _M = _o.matrix_world
    _N = _M.to_3x3().inverted().transposed()
    for _p in _o.data.polygons:
        if (_N @ _p.normal).normalized().z <= 0.5:
            continue
        _raw = [_M @ _o.data.vertices[i].co for i in _p.vertices]
        FACES.append((_raw, plane_z_fn(_raw), _o.name))


def rail_route(name):
    """('walk_e_A__B_lN' own-leg prefix, 'walk_e_A__B' own route, (A, B))."""
    core = name[len("bar_"):].split("_rail")[0]        # e_A__B_lN
    leg = "walk_" + core
    route = leg.rsplit("_l", 1)[0]
    ab = route[len("walk_e_"):].split("__")
    return leg, route, ab


def fouling(ob, A, B, n=24):
    """Per-sample: does the rail stand in a walking line that is not its own?"""
    leg, route, ab = rail_route(ob.name)
    mine = {route + "_landing"}
    pads = tuple("walk_pad_" + a for a in ab) + tuple("walk_lm_" + a for a in ab)
    run = B - A
    out = []
    for i in range(n + 1):
        p = A + run * (i / n)
        bad = None
        for raw, fn, nm in FACES:
            if nm.startswith(leg) or nm.startswith(pads):
                continue
            if any(nm.startswith(m) for m in mine):
                continue
            if dist_poly2(p.x, p.y, raw) > PLAYER:
                continue
            z = fn(p.x, p.y)
            if z - 0.25 <= p.z <= z + COR.height + 0.05:
                bad = nm
                break
        out.append(bad)
    return out


def ends(ob):
    """The rail's two end centroids in world space, plus a per-vertex parameter."""
    Mx = ob.matrix_basis
    P = [Mx @ v.co for v in ob.data.vertices]
    best = (-1.0, 0, 0)
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = Vector((P[i].x - P[j].x, P[i].y - P[j].y, 0.0)).length
            if d > best[0]:
                best = (d, i, j)
    L, i, j = best
    if L < 1e-6:
        return None
    axis = Vector((P[j].x - P[i].x, P[j].y - P[i].y, 0.0)).normalized()
    ts = [(p.x - P[i].x) * axis.x + (p.y - P[i].y) * axis.y for p in P]
    t0, t1 = min(ts), max(ts)
    lo = [k for k in range(len(P)) if ts[k] < t0 + (t1 - t0) * 0.5]
    hi = [k for k in range(len(P)) if k not in lo]
    A = sum((P[k] for k in lo), Vector()) / len(lo)
    B = sum((P[k] for k in hi), Vector()) / len(hi)
    return P, axis, t0, t1, A, B, [(t - t0) / (t1 - t0) for t in ts]


def guarding(ob, A, B, n=24):
    """Sample the rail; True where the ground STEPS ACROSS it.

    The town's decks are big flat pads (`walk_lm_quay-deck` is 11 x 11 m) and the
    flights that leave them lie ON them, so "is the ground below the rail lower
    than the ground beside it" answers 0 for a rail standing beside its own
    treads.  The question that actually separates a guard from a fence is
    whether the surface is at DIFFERENT HEIGHTS on the two sides — a tread edge,
    a deck lip, or a void.  Missing ground counts as infinitely low.
    """
    run = B - A
    perp = Vector((-run.y, run.x, 0.0))
    perp = perp.normalized() if perp.length > 1e-6 else Vector((1, 0, 0))
    OFF = (0.0, 0.5, 1.0, PROBE)
    out = []
    for i in range(n + 1):
        p = A + run * (i / n)
        hs = []
        void = False
        for s in (1.0, -1.0):
            for d in OFF:
                if d == 0.0 and s < 0:
                    continue
                q = p + perp * (d * s)
                t = COR.top_at(q.x, q.y)
                if t is None:
                    void = True
                else:
                    hs.append(t)
        step = (max(hs) - min(hs)) if len(hs) >= 2 else 0.0
        out.append(void or step >= DROP)
    return out


def trim(ob):
    e = ends(ob)
    if e is None:
        return None
    P, axis, t0, t1, A, B, tn = e
    L = (B - A).length
    g = guarding(ob, A, B)
    n = len(g) - 1
    head = 0
    while head <= n and not g[head]:
        head += 1
    tail = n
    while tail >= 0 and not g[tail]:
        tail -= 1
    if head > n:                                # nothing on this rail guards anything
        head, tail = n, n                       # keep the far (flight) end only
    # CRITERION 2: begin after the last thing fouled on the way in, end before the
    # first thing fouled on the way out.
    f = fouling(ob, A, B, n)
    mid = n // 2
    fh = max([i for i in range(mid + 1) if f[i]], default=-1)
    ft = min([i for i in range(mid, n + 1) if f[i]], default=n + 1)
    why = []
    if fh >= 0:
        head = max(head, fh + 1)
        why.append("head fouls %s" % f[fh])
    if ft <= n:
        tail = min(tail, ft - 1)
        why.append("tail fouls %s" % f[ft])
    if head > tail:
        # every sample fouls something: report, never carve (see the header)
        print("  !! %-50s fouls along its whole length (%s) — LEFT ALONE"
              % (ob.name, f[mid] or f[0]))
        return None
    FOULED[ob.name] = why
    lo = head / n
    hi = tail / n
    lo = max(0.0, min(lo, 1.0 - STUB / max(L, 1e-6)))
    hi = min(1.0, max(hi, STUB / max(L, 1e-6)))
    if lo < 1e-6 and hi > 1 - 1e-6:
        return None
    cut = (lo + (1.0 - hi)) * L
    if cut < MIN_TRIM:
        return None
    return lo, hi, L, cut


def apply_trim(ob, lo, hi):
    P, axis, t0, t1, A, B, tn = ends(ob)
    run = B - A
    Minv = ob.matrix_basis.inverted()
    for k, v in enumerate(ob.data.vertices):
        t = tn[k]
        nt = min(max(t, lo), hi)
        if abs(nt - t) > 1e-9:
            v.co = Minv @ (P[k] + run * (nt - t))


FOULED = {}
applied = []
bars = sorted([o for o in bpy.data.objects
               if o.type == 'MESH' and o.name.startswith("bar_")], key=lambda o: o.name)
print("=" * 78)
print("RAIL TRIM — %d bar_ rails  (%s)" % (len(bars), "APPLY" if APPLY else "report only"))
print("=" * 78)
hits = []
for ob in bars:
    r = trim(ob)
    if not r:
        continue
    lo, hi, L, cut = r
    hits.append(ob.name)
    print("  %-52s len %.2f -> %.2f m   (head %.2f, tail %.2f trimmed)%s"
          % (ob.name, L, L - cut, lo * L, (1 - hi) * L,
             ("   [" + "; ".join(FOULED[ob.name]) + "]") if FOULED.get(ob.name) else ""))
    if APPLY and (ONLY is None or ob.name in ONLY):
        apply_trim(ob, lo, hi)
        applied.append(ob.name)
    elif APPLY:
        print("       (not applied: outside this pass's --only set)")
print("\n%d rails %s (%d of them for FOULING another route's walking line)"
      % (len(hits), "trimmed" if APPLY else "would be trimmed",
         len([h for h in hits if FOULED.get(h)])))
if APPLY:
    print("APPLIED to %d: %s" % (len(applied), ", ".join(applied) or "-"))
if APPLY and SAVE:
    bpy.ops.wm.save_mainfile()
    print("saved", bpy.data.filepath)
