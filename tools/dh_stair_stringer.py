"""dh_stair_stringer.py — A BUILDER THAT REFUSES A STRINGER IN SILENCE LEAVES A
FLIGHT OF TREADS HANGING IN MID-AIR, AND ONLY THE PICTURE SAYS SO.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_stair_stringer.py -- [--clear 2.05] [save]

A CARRIER, NEVER A REBUILD.  `waterfront_build.py` is a district builder and
re-running it against the live master is round 5's time bomb; this appends
geometry to the existing `wf_stair_stringers` mesh in place, so the object list,
the material list and every bundle's mesh parity are unchanged.

WHY (round 9, measured).  Dellhollow's loudest standing judge verdict was
deep-stairs' floating treads — filed in FOUR runs and in BOTH naive and checklist
modes ("The wooden stair treads float individually in mid-air without any
supporting stringers, risers, or structural beams", u 0.338..0.690 v 0.428..0.698).
Round 8 handed it over as unmeasured.  It measures, and the judge is right:

    wf_stair_treads      168 components, z 1.34 .. 9.18
    wf_stair_stringers     4 components  (2 per flight, so TWO flights are carried)
    treads with no stringer within 1.3 m:  36 of 168 = 21.4%
    and they are CONTIGUOUS: 33 of the 36 sit in one band at z 5.0 .. 6.9,
    which projects to deep-stairs u 0.546..0.666 v 0.562..0.666 —
    INSIDE the box all four judge passes drew.

THE MECHANISM IS IN `waterfront_build.py` LINES 358-375 AND IT IS SILENT.  The
stringer loop walks each end of the run back out of every walk corridor it would
otherwise stand over (`clear_end`), then walks the ends in again until no sample
is `blocked_at`, and then:

    if (p1 - p0).length < 0.9 or any(blocked_at(...)): continue

`continue` — no log line, no counter, no manifest.  Its own `log("BUILD", ...)`
reports the number of TREADS and never the number of stringers, so a flight that
lost both of them looks exactly like a flight that kept them.  Same family as
`_court_probe`'s "a gate that measures its own drawing cannot measure its own
build" and `moorage_search`'s missing oracle: the refusal was the answer and
nobody was asked.

WHAT THIS BUILDS, AND WHY IT IS A DIFFERENT SHAPE.  The original stringer runs
OUTBOARD of the treads, which is exactly why it gets refused — outboard of a
zigzag flight is regularly straight over the flight below.  This one runs
UNDERNEATH, on the flight's own centre line, with its TOP FACE at the treads'
own underside: a centre carriage.  It therefore stands over nothing the treads do
not already stand over, and it cannot eat a corridor the treads did not already
eat.  That is the whole of why it is buildable where the outboard beam is not.

THE HEADROOM GATE IS STILL EXPLICIT, because "it should be fine" is not a
measurement: every 0.25 m sample of a proposed carriage asks the master's OWN
`walk_*` meshes whether any walkable surface lies within `--clear` (default
2.05 m, the master's corridor) below the beam's bottom face, and a carriage with
ANY blocked sample is refused and SAID SO by name.  The tool prints one line per
flight either way — the thing its ancestor did not do.
"""
import bpy, sys, os, math, hashlib
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SAVE = "save" in argv


def _arg(f, d=None):
    return argv[argv.index(f) + 1] if f in argv else d


CLEAR = float(_arg("--clear", "2.05"))
SEC_W, SEC_H = 0.16, 0.30      # a carriage is stouter than the 0.11x0.40 outboard beam
NEAR = 1.3                     # "a stringer already runs alongside this tread"
TARGET = "wf_stair_stringers"


def wbb(ob, idx=None):
    vs = ob.data.vertices
    ps = [ob.matrix_world @ vs[i].co for i in idx] if idx else [ob.matrix_world @ v.co for v in vs]
    return [min(p[i] for p in ps) for i in range(3)] + [max(p[i] for p in ps) for i in range(3)]


def comps(ob):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        st, c = [v], []
        seen.add(v.index)
        while st:
            q = st.pop(); c.append(q.index)
            for e in q.link_edges:
                o = e.other_vert(q)
                if o.index not in seen:
                    seen.add(o.index); st.append(o)
        out.append(c)
    bm.free()
    return out


def digest(ob):
    h = hashlib.sha256()
    for v in ob.data.vertices:
        p = ob.matrix_world @ v.co
        h.update(("%.5f %.5f %.5f " % (p.x, p.y, p.z)).encode())
    return h.hexdigest()[:16]


TR = bpy.data.objects["wf_stair_treads"]
SG = bpy.data.objects[TARGET]
print("DIGEST before %s  (%s: %d verts)" % (digest(SG), TARGET, len(SG.data.vertices)))

TC = [wbb(TR, c) for c in comps(TR)]
SC = [wbb(SG, c) for c in comps(SG)]
print("CENSUS treads %d components, stringers %d components" % (len(TC), len(SC)))


def carried(p, pad=NEAR, zpad=0.6):
    return any(s[2] - zpad <= p[2] <= s[5] + zpad and s[0] - pad <= p[0] <= s[3] + pad
               and s[1] - pad <= p[1] <= s[4] + pad for s in SC)


cent = [Vector(((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2)) for b in TC]
under = [b[2] for b in TC]
orphan = [i for i, p in enumerate(cent) if not carried(p)]
print("ORPHAN treads %d of %d (%.1f%%)" % (len(orphan), len(TC), 100.0 * len(orphan) / len(TC)))
if not orphan:
    print("NOTHING TO DO")
    sys.exit(0)

# ---- cluster the orphans into flights -----------------------------------
# A flight is a run of treads whose centres are within 1.6 m of the next one down;
# 1.6 m is comfortably over a 0.38 m rise x ~0.30 m going and comfortably under the
# gap to the next flight of a switchback.
order = sorted(orphan, key=lambda i: -cent[i].z)
flights, cur = [], [order[0]]
for i in order[1:]:
    if min((cent[i] - cent[j]).length for j in cur) <= 1.6:
        cur.append(i)
    else:
        flights.append(cur); cur = [i]
flights.append(cur)
flights = [f for f in flights if len(f) >= 3]
print("FLIGHTS %d orphan flight(s) of >=3 treads" % len(flights))

# ---- the headroom oracle: the master's own walk meshes -------------------
# NOT filtered on `hide_render`: the walk network IS hide_render (it is collision,
# never a picture), so the obvious filter would have left this oracle with ONE
# object out of hundreds and silently passed every carriage.  Measured on the
# first dry run: 1 walk mesh with the filter, 452 without it.
WALKS = [o for o in bpy.data.objects
         if o.type == 'MESH' and o.name.startswith("walk_")]
WBB = [(o.name, wbb(o)) for o in WALKS]
print("ORACLE %d walk meshes are the headroom authority (clear %.2f m)" % (len(WBB), CLEAR))


def headroom(p, zbot, selfkey):
    """The nearest walkable surface below this sample, and its clearance.

    THE FLIGHT'S OWN TREADS ARE EXCLUDED BY NAME, and that exclusion is the
    measurement, not a convenience: a stair's treads are 0.38 m apart, so
    ANY carriage under any flight is inside 2.05 m of the tread below it and a
    naive oracle refuses every stair in the world.  (Measured: the first run of
    this tool refused the one real orphan flight and named
    `walk_e_deep-stairs-head__deep-stairs-foot_l1_t10` — a tread of the very
    flight it was carrying.)  Nobody walks between two treads of one flight;
    what a carriage may not do is hang into the corridor of a DIFFERENT walk,
    which is exactly what the outboard beams `waterfront_build` refuses were
    doing.  So: every other walk surface is asked, in bbox form, which
    over-covers — the direction a headroom test is allowed to be wrong in."""
    worst, who = 1e9, None
    for nm, b in WBB:
        if selfkey and selfkey in nm:
            continue
        if b[0] - 0.20 <= p.x <= b[3] + 0.20 and b[1] - 0.20 <= p.y <= b[4] + 0.20:
            if b[5] <= zbot - 0.02 and zbot - b[5] < worst:
                worst, who = zbot - b[5], nm
    return worst, who


NEW_V, NEW_F = [], []


def add_beam(a, b, w, h):
    d = b - a
    up = Vector((0, 0, 1)) if abs(d.normalized().z) < 0.98 else Vector((1, 0, 0))
    xa = d.normalized(); ya = xa.cross(up).normalized(); za = ya.cross(xa).normalized()
    n0 = len(NEW_V)
    for t in (0.0, 1.0):
        p = a + d * t
        for sy, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            NEW_V.append(p + ya * (sy * w / 2) + za * (sz * h / 2))
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        NEW_F.append(tuple(n0 + i for i in f))


built = 0
# every orphan tread here belongs to the deep-stairs run; the key names the walk
# edge whose own treads the oracle must not count against its own carriage
SELFKEY = "deep-stairs-head__deep-stairs-foot"
for fi, f in enumerate(flights):
    idx = sorted(f, key=lambda i: -cent[i].z)
    a, b = cent[idx[0]], cent[idx[-1]]
    run = (b - a)
    if run.length < 0.9:
        print("FLIGHT %d REFUSED — run %.2f m is under 0.9 m" % (fi, run.length))
        continue
    ax = run.normalized()
    pp = Vector((-ax.y, ax.x, 0.0)).normalized()
    # THE TOP FACE TOUCHES THE TREADS' OWN UNDERSIDE, at each end, so the beam is
    # NOT a floating object under a floating object: its axis z is the tread
    # underside minus half the section, taken from the treads themselves.
    ua = TC[idx[0]][2]
    ub = TC[idx[-1]][2]
    ext = ax * 0.30
    a2 = (a - ext).copy(); a2.z = ua - SEC_H / 2.0
    b2 = (b + ext).copy(); b2.z = ub - SEC_H / 2.0
    # half-width of the flight ACROSS the run, so both carriages stay INSIDE the
    # tread footprint — an outboard beam is what `waterfront_build` could not place
    # ACROSS THE FLIGHT, MEASURED AS A SIGNED SPAN, not as a max |offset| from the
    # top tread's centroid.  A step here is 5-7 plank boxes 0.66 x 0.71 m laid side
    # by side over a 2.5 m width, and the topmost box is at one edge of it — so the
    # naive half-width read 1.80 m for a flight 1.25 m half-wide and would have
    # planted a carriage a metre outboard of the stair, which is the exact failure
    # this carrier exists to avoid.
    lo, hi = 1e9, -1e9
    for i in f:
        bb = TC[i]
        for cx, cy in ((bb[0], bb[1]), (bb[3], bb[1]), (bb[3], bb[4]), (bb[0], bb[4])):
            t = (cx - a.x) * pp.x + (cy - a.y) * pp.y
            lo, hi = min(lo, t), max(hi, t)
    mid, hw = (lo + hi) / 2.0, (hi - lo) / 2.0
    off = max(0.0, hw - SEC_W / 2.0 - 0.10)
    a2 = a2 + pp * mid
    b2 = b2 + pp * mid
    n = max(4, int(run.length / 0.25))
    worst, who = 1e9, None
    for sgn in (-1, 1):
        for k in range(n + 1):
            p = a2.lerp(b2, k / n) + pp * (sgn * off)
            c, nm = headroom(p, p.z - SEC_H / 2.0, SELFKEY)
            if c < worst:
                worst, who = c, nm
    if worst < CLEAR:
        print("FLIGHT %d z %.2f..%.2f  REFUSED — %.2f m over %s, under the %.2f m bar"
              % (fi, b.z, a.z, worst, who, CLEAR))
        continue
    for sgn in (-1, 1):
        add_beam(a2 + pp * (sgn * off), b2 + pp * (sgn * off), SEC_W, SEC_H)
    built += 2
    print("FLIGHT %d z %.2f..%.2f  run %.2f m  %2d orphan treads  -> TWO CARRIAGES "
          "%.2fx%.2f m at +-%.2f m (flight half-width %.2f, so INSIDE the treads); "
          "worst clearance under them %.2f m over %s (bar %.2f)"
          % (fi, b.z, a.z, run.length, len(f), SEC_W, SEC_H, off, hw, worst,
             who or "nothing at all", CLEAR))

if not NEW_V:
    print("BUILT 0 carriages — nothing written")
    sys.exit(0)

import bmesh
me = SG.data
# the carriage wears the stringers' OWN timber; a new material would be a new
# glTF material and this carrier promises the material list is unchanged
slot = 0
for i, m in enumerate(me.materials):
    if m and m.name == "mat_timber_dark":
        slot = i
Mi = SG.matrix_world.inverted()
base = len(me.vertices)
bm = bmesh.new(); bm.from_mesh(me)
bv = [bm.verts.new(Mi @ p) for p in NEW_V]
bm.verts.index_update()
for f in NEW_F:
    try:
        face = bm.faces.new([bv[i] for i in f])
        face.material_index = slot
    except ValueError:
        pass
bm.to_mesh(me); bm.free()
me.update()
print("BUILT %d centre carriage(s) in material slot %d (%s); %s %d -> %d verts"
      % (built, slot, me.materials[slot].name if me.materials else "-", TARGET,
         base, len(me.vertices)))
print("DIGEST after  %s" % digest(SG))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("DRY RUN — pass `save` to write")
