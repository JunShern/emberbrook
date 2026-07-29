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
from boatyard_lib import Corridor

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
APPLY = "--apply" in argv
SAVE = "--save" in argv

DROP = 0.30          # a guard needs this much fall beside it
SLOPE = 0.14         # ... or this much rise per metre under it (a flight)
PROBE = 1.6          # how far to either side we look for the drop
STUB = 0.60          # never shorten past this much rail at the flight end
MIN_TRIM = 0.45      # ignore nibbles

walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
COR = Corridor(walks, margin=0.0)


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
    print("  %-52s len %.2f -> %.2f m   (head %.2f, tail %.2f trimmed)"
          % (ob.name, L, L - cut, lo * L, (1 - hi) * L))
    if APPLY:
        apply_trim(ob, lo, hi)
print("\n%d rails %s" % (len(hits), "trimmed" if APPLY else "would be trimmed"))
if APPLY and SAVE:
    bpy.ops.wm.save_mainfile()
    print("saved", bpy.data.filepath)
