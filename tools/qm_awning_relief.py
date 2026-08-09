"""qm_awning_relief.py — A CANVAS WITH NO NORMAL HAS NOTHING FOR THE LIGHT TO DO.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/qm_awning_relief.py -- [parts relief,restripe,board] [save]

A CARRIER, NEVER A REBUILD.  `qm_build.py` is a district builder and re-running it
against the live master is the time bomb round 5 paid for (`t2_cliff_south`'s
`derive_material` reverting `t3_rock_projection`'s measured mapping fix under a
comment reading "Idempotent" — and `qm_build` derives `mat_qm_cliff`, which
`t3_rock_projection` also owns).  So this edits the five `qm_awning_*` meshes and
one stall board IN PLACE on the live master.  `tools/qm_build.py` carries the same
three edits so a rebuild agrees; neither can silently undo the other.

WHY (measured, round 8, `dh_objmap` + the shipped crossing plate).  Eleven
independent naive judge passes across FOUR runs (170205-calib, round4haze,
round6phase, round7water) filed the same thing at crossing u 0.915..1.00
v 0.755..1.00: "an untextured white polygon clips into the bottom right corner",
"a flat white untextured plane ... revealing missing geometry".  Put on the
geometry it is 62.5% `qm_awning_0 | mat_qm_awning` AT 5.3 m — a market awning in
the near field, not missing geometry.  And BOTH HALVES OF THE JUDGE'S SENTENCE ARE
A MEASUREMENT:

    crossing subject                px    dist   L p50   local 5x5 sd
    qm_awning_0 (the wedge)      56827   5.3 m   168.8   *** 0.60 ***
    everything else 3-12 m      432589  10.6 m    85.0       4.11
    the brightest third of it    92507  10.4 m   125.8       5.05

It is the second brightest large object in the frame and **6.9x flatter than the
near field it sits in**.  It is not untextured in the DATA — `awning()` bakes
stripes into vertex colours — but projecting its 21 vertices through crossing's
own solved camera shows why that does not help: the frame edge crops the canvas
to ONE STRIPE.  Every dark column (v00/v06/v12 at colour 0.068,0.123,0.191)
projects to v > 0.93; the in-frame corner is columns 5 and 6, both the cream
0.320,0.295,0.248.  A STRIPE PATTERN OFF THE EDGE OF THE FRAME IS NOT A PATTERN.

So the lever is RELIEF, not colour: the canvas is a ruled surface with z constant
in x, i.e. its normal does not vary along its own width, so no light can print
anything on it at any crop.  `relief` scallops it between ribs.

  * `relief` — every `qm_awning_*` rebuilt at 2n+1 columns: the OLD columns become
    RIBS and rise, the new midpoints sit EXACTLY ON THE OLD SURFACE.  So NO VERTEX
    EVER MOVES DOWN and the headroom `awning_lip`/`over_walk` cleared is unchanged
    BY CONSTRUCTION (asserted below) — which matters, because the canvas is 0.19 m
    above a 2.05 m corridor and `AWN_CLEAR` exists because a 50 mm margin is not a
    margin.  The wall row is pinned (a canvas is nailed to a straight batten); the
    mid and lip rows scallop, so the lip silhouette breaks too.
  * `restripe` — `STALLC[3]` is BIT-IDENTICAL to `awning()`'s hard-coded second
    stripe colour, so `qm_awning_1` shipped 21/21 vertices at one colour: the one
    genuinely monochrome canvas in town, and nobody could see it because the tool
    that would report it reports MATERIALS and the stripes are vertex data.
  * `board` — round 3's "placeholder plane" on `qm_stall_3`, found by a blind judge
    on BOTH the before and after plates and never addressed.  It is not flat and
    not untextured — it wears `mat_wallwood`'s planks at 5x5 sd 6.15 — the defect
    is structural, was named in round 3 and was never built: `stall()` puts the
    board 0.185 m PROUD of its own four posts on the plaza side, so a 1.30 m panel
    shows the square an unbroken face with its own frame buried behind it.  The
    defect is in `stall()`, so it is ALL SEVEN boards, not the one the judge
    happened to be looking at.  Each is moved back until its plaza face is flush
    with its own posts' back face; nothing moves toward the plaza.
"""
import bpy, sys, os, hashlib, json
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
PARTS = set(argv[argv.index("parts") + 1].split(",")) if "parts" in argv else None
want = lambda p: PARTS is None or p in PARTS
SAVE = "save" in argv

# the scallop, at the lip.  0.11 m over a 0.98 m reach with ribs 0.42 m apart is a
# slack canvas, not a tent: peak cross-slope at the mid row is atan(0.073/0.21) =
# 19 deg, which is what a directional key needs to print anything at all.
SAG_LIP = 0.110
SAG_MID = 0.073          # 0.66 x, so the fold is deepest where the canvas is free
# ROUND 9 PULLED THE CANVAS VALUE (tools/qm_canvas_value.py, and `qm_build.CANVAS_B`
# carries the same pair).  These two must move with it or `restripe` would paint the
# one monochrome canvas back to round 8's cream on a master whose other four wear
# round 9's — two tools owning one number, which is the trap this repo has a rule for.
CREAM = (0.144, 0.133, 0.112)
CREAM_ALT = (0.068, 0.063, 0.053)   # the partner when the cloth IS the cream


def digest(names):
    h = hashlib.sha256()
    for nm in sorted(names):
        ob = bpy.data.objects.get(nm)
        if not ob or ob.type != 'MESH':
            continue
        h.update(nm.encode())
        for v in ob.data.vertices:
            p = ob.matrix_world @ v.co
            h.update(("%.5f %.5f %.5f " % (p.x, p.y, p.z)).encode())
        ca = ob.data.color_attributes.get("Col")
        if ca:
            for d in ca.data:
                h.update(("%.4f %.4f %.4f " % tuple(d.color[:3])).encode())
    return h.hexdigest()[:16]


def wbb(ob, verts=None):
    ps = [ob.matrix_world @ v.co for v in (verts or ob.data.vertices)]
    return [min(p[i] for p in ps) for i in range(3)] + [max(p[i] for p in ps) for i in range(3)]


AWN = sorted([o for o in bpy.data.objects if o.name.startswith("qm_awning_")],
             key=lambda o: o.name)
BEFORE = digest([o.name for o in AWN] +
                [o.name for o in bpy.data.objects if o.name.startswith("qm_stall_")])
print("DIGEST before %s  (%d awnings)" % (BEFORE, len(AWN)))


# ---------------------------------------------------------------- relief -----
def relief(ob):
    """Rebuild one awning at 2n+1 columns.  Old columns rise into ribs; the new
    midpoints land on the old surface, so min(z) per row is untouched."""
    me = ob.data
    M, Mi = ob.matrix_world, ob.matrix_world.inverted()
    V = [M @ v.co for v in me.vertices]
    n3 = len(V)
    assert n3 % 3 == 0, ("%s: %d verts is not 3 per column" % (ob.name, n3))
    ncol = n3 // 3
    ca = me.color_attributes.get("Col")
    col = [tuple(ca.data[3 * k].color[:3]) for k in range(ncol)] if ca else None
    zmin_before = [min(V[3 * k + r].z for k in range(ncol)) for r in range(3)]

    def at(x_t, r):
        """the OLD surface at parameter t along x, row r — it is ruled and constant
        in x, so this is exact rather than an interpolation of a curve."""
        a, b = V[0 * 3 + r], V[(ncol - 1) * 3 + r]
        return a.lerp(b, x_t)

    LIFT = (0.0, SAG_MID, SAG_LIP)
    NC = 2 * (ncol - 1) + 1
    NV, NF, NCOL = [], [], []
    for j in range(NC):
        t = j / (NC - 1.0)
        rib = (j % 2 == 0)
        for r in range(3):
            p = at(t, r).copy()
            if rib:
                p.z += LIFT[r]
            NV.append(p)
        if col:
            k = j // 2
            if not rib:                       # panel centre keeps the panel colour
                c = col[k]
            elif j == 0:
                c = col[0]
            elif j == NC - 1:
                c = col[ncol - 1]
            else:                             # the rib is where the stripe turns
                c = tuple((col[k - 1][i] + col[k][i]) / 2.0 for i in range(3))
            NCOL += [c, c, c]
    for j in range(NC - 1):
        for r in (0, 1):
            i0 = j * 3 + r
            NF.append((i0, i0 + 3, i0 + 4, i0 + 1))
    nm = me.name
    new = bpy.data.meshes.new(nm + "_relief")
    new.from_pydata([tuple(Mi @ p) for p in NV], [], NF)
    new.validate()
    for m in me.materials:
        new.materials.append(m)
    if col:
        a = new.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
        for i, c in enumerate(NCOL):
            a.data[i].color = (c[0], c[1], c[2], 1.0)
    ob.data = new
    new.name = nm
    zmin_after = [min((ob.matrix_world @ new.vertices[3 * k + r].co).z
                      for k in range(NC)) for r in range(3)]
    for r in range(3):
        assert zmin_after[r] >= zmin_before[r] - 1e-6, \
            "%s row %d DROPPED %.4f m — headroom is not ours to spend" % (
                ob.name, r, zmin_before[r] - zmin_after[r])
    return ncol, NC, zmin_before, zmin_after


if want("relief"):
    for ob in AWN:
        a, b, z0, z1 = relief(ob)
        print("RELIEF %-14s columns %2d -> %2d   min z per row %s -> %s (never down)"
              % (ob.name, a, b, ["%.3f" % z for z in z0], ["%.3f" % z for z in z1]))


# -------------------------------------------------------------- restripe -----
if want("restripe"):
    for ob in AWN:
        ca = ob.data.color_attributes.get("Col")
        if not ca:
            continue
        cs = set(tuple(round(c, 3) for c in d.color[:3]) for d in ca.data)
        if len(cs) > 1:
            continue
        # the one monochrome canvas: its cloth colour IS the constant partner
        NC = len(ob.data.vertices) // 3
        for j in range(NC):
            rib = (j % 2 == 0)
            k = j // 2
            # panel k takes CREAM when k is even (rgb_a), CREAM_ALT when odd
            if not rib:
                c = CREAM if (k % 2 == 0) else CREAM_ALT
            elif j == 0:
                c = CREAM
            elif j == NC - 1:
                c = CREAM if ((k - 1) % 2 == 0) else CREAM_ALT
            else:
                p = CREAM if ((k - 1) % 2 == 0) else CREAM_ALT
                q = CREAM if (k % 2 == 0) else CREAM_ALT
                c = tuple((p[i] + q[i]) / 2.0 for i in range(3))
            for r in range(3):
                ca.data[3 * j + r].color = (c[0], c[1], c[2], 1.0)
        print("RESTRIPE %-14s 1 colour -> 2 (cloth was bit-identical to the canvas "
              "constant %s)" % (ob.name, CREAM))


# ----------------------------------------------------------------- board -----
def components(me):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        st, c = [v], []
        seen.add(v.index)
        while st:
            q = st.pop()
            c.append(q.index)
            for e in q.link_edges:
                o = e.other_vert(q)
                if o.index not in seen:
                    seen.add(o.index)
                    st.append(o)
        comps.append(c)
    bm.free()
    return comps


STALLS = sorted([o for o in bpy.data.objects
                 if o.name.startswith("qm_stall_")], key=lambda o: o.name)

for ob in (STALLS if want("board") else []):
    me = ob.data
    M, Mi = ob.matrix_world, ob.matrix_world.inverted()
    comps = components(me)
    def dims(c):
        ps = [M @ me.vertices[i].co for i in c]
        return [max(p[k] for p in ps) - min(p[k] for p in ps) for k in range(3)], \
               [min(p[k] for p in ps) for k in range(3)], [max(p[k] for p in ps) for k in range(3)]
    board, posts = None, []
    for c in comps:
        d, lo, hi = dims(c)
        if len(c) == 8 and abs(d[2] - 1.30) < 0.02 and min(d[0], d[1]) < 0.15 and max(d[0], d[1]) > 1.5:
            board = (c, d, lo, hi)
        if len(c) == 8 and abs(d[2] - 2.12) < 0.02 and d[0] < 0.2 and d[1] < 0.2:
            posts.append((c, d, lo, hi))
    assert board and len(posts) == 4, "%s: board=%s posts=%d" % (ob.name, bool(board), len(posts))
    c, d, lo, hi = board
    a = 0 if d[0] < d[1] else 1                       # the board's thin axis
    ctr = (lo[a] + hi[a]) / 2.0
    sc = sum((p[2][a] + p[3][a]) / 2.0 for p in posts) / 4.0   # stall centre on a
    side = 1.0 if ctr > sc else -1.0
    near = [p for p in posts if ((p[2][a] + p[3][a]) / 2.0 - sc) * side > 0]
    assert len(near) == 2, "expected 2 posts on the board's own side, got %d" % len(near)
    if side > 0:
        shift = max(p[3][a] for p in near) - lo[a]
    else:
        shift = min(p[2][a] for p in near) - hi[a]
    v = Vector((0.0, 0.0, 0.0)); v[a] = shift
    for i in c:
        me.vertices[i].co = Mi @ ((M @ me.vertices[i].co) + v)
    print("BOARD %-12s backboard moved %+.3f m on axis %s — it stood PROUD of its own "
          "four posts; its plaza face is now flush with their back face"
          % (ob.name, shift, "xyz"[a]))


AFTER = digest([o.name for o in AWN] + [o.name for o in STALLS])
print("DIGEST after  %s" % AFTER)
touched = sorted(set([o.name for o in AWN] +
                     ([o.name for o in STALLS] if want("board") else [])))
print("TOUCHED %d objects: %s" % (len(touched), ", ".join(touched)))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("DRY RUN — pass `save` to write")
