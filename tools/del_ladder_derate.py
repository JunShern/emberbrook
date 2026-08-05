"""del_ladder_derate.py — A CARRIER: make Dellhollow's two BLOCKED ladders look blocked.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
          -P tools/del_ladder_derate.py -- [save] [--lamp]

WHY A CARRIER AND NOT A DISTRICT REBUILD (measured, 2026-08-05)
---------------------------------------------------------------
The obvious route was `weave_build.py -- all save`, which owns `wv_fishdock_ladder`.
IT IS NO LONGER FAITHFUL TO THE LIVE MASTER.  Run on a byte copy of
`dellhollow-master.blend` it produced **85** `wv_/nl_/veg_wv_/veg_nl_` objects where
the master has **138** — the huts (`wv_hut_weave-huts_*`), the North Landing dressing
and 48 vegetation clumps are in the master and are NOT in a fresh run's output.  A
rebuild would have deleted 55 objects of shipped art to change one ladder.  Same
class as `gate_rimchop.py` / `gate_roadchop.py` on the Emberbrook side, and the same
rule: **for a district already dressed, carry the edit; never re-run the builder.**

The faithfulness gate below is what makes that safe: this script prints, and asserts,
that the ONLY objects it added or removed are the ladder parts it names.

WHAT IT DOES
------------
The geometry decisions live in `tools/ladder_derate.py` (pure, importable, shared with
the two builders that would lay these ladders from scratch).  This script applies them
to the live master:

  LADDER A — `wv_fishdock_ladder` (map edge `weave-huts -> fish-dock`, routes
    `blocked: true`).  A whole, evenly-runged, 25-rung timber ladder from the fish
    dock up to the weave tier, and the most inviting object in the `lockfive` plate.
    Rebuilt on ITS OWN measured run (see `run_of()` — the built ladder is already
    walked-in clear of the walk network, so re-deriving from the map line would
    re-open a settled question): rails ragged at s=0.55/0.64, rotted rungs, one
    hanging, a plank across the head.

  LADDER B — `e_lockhead__lock-five_rung00..30` (map edge `lockhead -> lock-five`,
    routes `blocked: true`).  These are BLOCKOUT output that never got district art:
    31 detached 0.7 x 0.3 x 0.06 slabs with no stiles at all, floating in mid-air
    diagonally across the `lockfive` and `weave` plates.  They do not read as a
    ladder — they read as a flight of floating steps, which is worse.  The lower run
    is deleted; the survivors get the two ragged stiles they never had (so the top
    reads as a ladder head, which is what the Lockhead district was built around —
    `lk_build` clamps `rung00` flush with the pad, opens the parapet rail at
    `LADDER_GAP` and cuts a slot in the deck paving for it), plus the plank and the
    hanging rung.

  --lamp  the counterpart the ruling allows: a lantern at the head of the REAL way
    down (`walk_e_weave-huts__moorage_l0_t00`, the switchback's top tread), built to
    `waterfront_build.py`'s own `wf_lantern_stairmouth` recipe — the town already
    marks a discreet stair with a light.  Named `wv_lantern_stairhead`, so it lives
    under weave_build's own `wv_` prefix and a future weave rebuild clears it.

NOT DONE HERE, ON PURPOSE: nothing walkable is touched.  No `walk_` or `bar_` object
is read, moved or deleted; both ladders were already non-walkable (that is the whole
defect), so the walk network, `routes_derive` and every reachability instrument see
exactly the same town before and after.  What changes is the picture, which is where
the defect was.
"""
import bpy, sys, os, math
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
sys.path.insert(0, REPO + "/tools")
import ladder_derate as LD
from boatyard_lib import beam, obox, cyl, join_meshes, link, coll, world_bbox
from weave_lib import MAT, PAL, finish

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
LAMP = "--lamp" in argv
BLEND = bpy.data.filepath

COLL_A = "DIST_weave_DECK"
COLL_B = "PATHS"

LOG = []
def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-8s %-32s %s" % (kind, what, why))


# ---------------------------------------------------------------- census BEFORE
def census():
    return {o.name: (o.type, len(o.data.vertices) if o.type == 'MESH' else 0)
            for o in bpy.data.objects}
BEFORE = census()


# ================================================================= LADDER A
def run_of(ob):
    """The built ladder's OWN centreline, measured off its own vertices.

    The stringers are `beam()`s laid between two points; `beam` extends nothing
    along its own axis and the lateral offset is horizontal (perpendicular to the
    run in plan), so the extreme projections onto the run direction ARE the ends.
    Measuring here rather than re-deriving from the map line is deliberate: the
    original build walked both ends in until the run cleared the walk corridor
    (weave_build finding 98), and that answer is already in the file.
    """
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    u = (min(vs, key=lambda v: v.z) - max(vs, key=lambda v: v.z)).normalized()
    # THROUGH THE CENTROID, not through the topmost vertex.  The topmost vertex is a
    # corner of ONE stringer, half a separation off the centreline, and a run laid
    # down that line comes out ~0.9 m sideways of where the original stood — over the
    # walk corridor the original build spent finding 98 walking clear of.
    C = sum(vs, Vector()) / len(vs)
    ts = [(v - C).dot(u) for v in vs]
    return C + u * min(ts), C + u * max(ts)


def ladder_A():
    old = bpy.data.objects.get("wv_fishdock_ladder")
    if old is None:
        log("SKIP", "wv_fishdock_ladder", "not in this blend")
        return
    head, foot = run_of(old)
    nverts = len(old.data.vertices)
    me = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    if me.users == 0:
        bpy.data.meshes.remove(me)

    d = foot - head
    L = d.length
    n = Vector((-d.y, d.x, 0)).normalized()
    HALF = 0.46                     # weave_build's own stringer offset
    P = lambda s, side: head + d * s + n * (side * HALF)

    # the rungs weave_build would have laid: every 0.33 m along the run
    rung_ss = [k * 0.33 / L for k in range(int(L / 0.33) + 1) if k * 0.33 <= L]

    M = MAT("lf_deck")
    parts = []
    for s0, c0, s1, c1 in LD.rails():
        parts.append(beam("lr", P(s0, c0), P(s1, c1), 0.10, 0.13, M, COLL_A))
    for s in LD.rungs(rung_ss):
        parts.append(beam("lg", P(s, -0.96), P(s, +0.96), 0.07, 0.05, M, COLL_A))
    s0, c0, s1, c1 = LD.bar()
    parts.append(beam("lb", P(s0, c0), P(s1, c1), 0.10, 0.045, M, COLL_A))
    s0, c0, s1, c1 = LD.dangle()
    parts.append(beam("ld", P(s0, c0), P(s1, c1), 0.06, 0.045, M, COLL_A))
    parts = [p for p in parts if p]
    ob = join_meshes(parts, "wv_fishdock_ladder", COLL_A)
    tints = {"lf_deck": PAL["timber"]}
    finish(ob, tints, jitter=0.06)
    log("DERATE", "wv_fishdock_ladder",
        "%s (%d verts -> %d); head %.2f,%.2f,%.2f foot %.2f,%.2f,%.2f, "
        "the run now ends at z %.2f with the dock at z %.2f" %
        (LD.report(rung_ss), nverts, len(ob.data.vertices),
         head.x, head.y, head.z, foot.x, foot.y, foot.z,
         head.z + d.z * LD.BREAK[1], foot.z))
    return ob


# ================================================================= LADDER B
def ladder_B():
    rungs = sorted([o for o in bpy.data.objects
                    if o.name.startswith("e_lockhead__lock-five_rung")],
                   key=lambda o: o.name)
    if not rungs:
        log("SKIP", "e_lockhead__lock-five_rung*", "not in this blend")
        return
    N = len(rungs)
    head = rungs[0].location.copy()
    foot = rungs[-1].location.copy()
    # the generator lays rung r at head + (b-a)*r/N, so the FOOT of the run is one
    # more step past the last rung
    d = (foot - head) * (N / (N - 1.0))
    HALF = 0.35                      # the rungs' own half-length, in world X
    nx = Vector((1, 0, 0))           # ...and they are world-X aligned: keep that,
                                     # so the deck slot lk_build cut still fits
    P = lambda s, side: head + d * s + nx * (side * HALF)
    ss = [r / float(N) for r in range(N)]
    keep = set(round(s, 6) for s in LD.rungs(ss))

    M = rungs[0].data.materials[0] if rungs[0].data.materials else None
    ndel = 0
    for o, s in zip(rungs, ss):
        if round(s, 6) in keep:
            continue
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
        ndel += 1

    # the stiles it never had: ragged, and only over the surviving run
    made = []
    for i, (s0, c0, s1, c1) in enumerate(LD.rails()):
        b = beam("e_lockhead__lock-five_stile%d" % i, P(s0, c0), P(s1, c1),
                 0.09, 0.09, M, COLL_B)
        if b:
            made.append(b)
    s0, c0, s1, c1 = LD.bar()
    b = beam("e_lockhead__lock-five_bar", P(s0, c0), P(s1, c1), 0.10, 0.05, M, COLL_B)
    if b:
        made.append(b)
    s0, c0, s1, c1 = LD.dangle()
    b = beam("e_lockhead__lock-five_hang", P(s0, c0), P(s1, c1), 0.07, 0.05, M, COLL_B)
    if b:
        made.append(b)
    for o in made:
        o.name = o.name.split(".")[0]
    log("DERATE", "e_lockhead__lock-five_*",
        "%d of %d floating rungs deleted, %d parts added (2 ragged stiles, a plank "
        "across the head, one hanging rung); the run now ends at z %.2f with the "
        "lock-five deck at z %.2f" %
        (ndel, N, len(made), head.z + d.z * LD.BREAK[1], (head + d).z))
    return made


# ================================================================= THE LAMP
def stairhead_lamp():
    """waterfront_build's `wf_lantern_stairmouth` recipe, at the REAL way down.

    THE POST IS SEARCHED, NEVER AUTHORED (the town's own doctrine for a free-standing
    solid).  Hand-placing it 0.42 m off the tread's south edge put its 2.6 m post
    straight through `bar_e_weave-huts__moorage_l0_railB` — an INVISIBLE canonical
    rail box, so nothing would have looked wrong and the flight's own guard would
    have been solid where the art showed air.  So: a ring search around the top
    tread, every candidate's whole column tested against every mesh in the blend,
    nearest clear one wins.
    """
    t00 = bpy.data.objects.get("walk_e_weave-huts__moorage_l0_t00")
    if t00 is None:
        log("SKIP", "wv_lantern_stairhead", "the switchback's top tread is not here")
        return []
    b = world_bbox(t00)             # (x0,x1,y0,y1,z0,z1)
    cx, cy, ztop = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, b[5]

    # AABB prefilter, then an EXACT surface-distance test.  The prefilter alone
    # refuses every candidate in the town: the cliff, the water and the terrain each
    # carry a world AABB tens of metres across, and a bound loose enough to refuse
    # everything is a veto, not a test.
    CAND = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.data.polygons:
            continue
        if o.name.startswith("wv_lantern_stairhead"):
            continue
        CAND.append((o, world_bbox(o), o.matrix_world.inverted()))

    def clear(px, py, z0, z1, r=0.16):
        col = [(px, py, z0 + (z1 - z0) * i / 10.0) for i in range(11)]
        for o, (x0, x1, y0, y1, bz0, bz1), inv in CAND:
            if px + r < x0 or px - r > x1 or py + r < y0 or py - r > y1:
                continue
            if z1 < bz0 - r or z0 > bz1 + r:
                continue
            for p in col:
                try:
                    ok, loc, _n, _i = o.closest_point_on_mesh(inv @ Vector(p))
                except RuntimeError:
                    break            # a template with no evaluated mesh (WRD_SRC_*)
                if ok and ((o.matrix_world @ loc) - Vector(p)).length < r:
                    return False
        return True

    found = None
    for rad in [0.95 + 0.30 * i for i in range(11)]:          # out to 3.95 m
        for k in range(36):
            a = k * math.pi / 18.0
            px, py = cx + rad * math.cos(a), cy + rad * math.sin(a)
            if clear(px, py, ztop - 0.05, ztop + 2.70):
                found = (px, py, rad, math.degrees(a))
                break
        if found:
            break
    if not found:
        log("SKIP", "wv_lantern_stairhead",
            "no clear 2.7 m column within 3.95 m of the stair head — a lamp that "
            "stands inside the guard is worse than no lamp")
        return []
    lx, ly, rad, ang = found
    lz = ztop
    MT, MIRON, MGLASS = MAT("lf_matte"), MAT("lf_iron"), MAT("lf_glass")
    # the bracket reaches back TOWARD the tread, so the light hangs over the flight
    bx, by = (cx - lx), (cy - ly)
    bl = math.hypot(bx, by) or 1.0
    bx, by = bx / bl * 0.40, by / bl * 0.40
    parts = [obox("lp", lx, ly, lz + 1.30, 0.11, 0.11, 2.60, mat=MT, cname=COLL_A),
             beam("lb", (lx, ly, lz + 2.46), (lx + bx, ly + by, lz + 2.52), 0.055,
                  0.055, MIRON, COLL_A)]
    gx, gy, gz = lx + bx, ly + by, lz + 2.30
    for _ in (0,):
        parts.append(obox("cg", gx, gy, gz, 0.028, 0.028, 0.34, mat=MIRON, cname=COLL_A))
    parts.append(obox("gl", gx, gy, gz, 0.155, 0.155, 0.26, mat=MGLASS, cname=COLL_A))
    parts.append(obox("cp", gx, gy, gz + 0.17, 0.20, 0.20, 0.055, mat=MIRON, cname=COLL_A))
    parts.append(obox("bs", gx, gy, gz - 0.16, 0.19, 0.19, 0.04, mat=MIRON, cname=COLL_A))
    ob = join_meshes([p for p in parts if p], "wv_lantern_stairhead", COLL_A)
    finish(ob, {"lf_matte": PAL["timber"], "lf_iron": PAL["iron"],
                "lf_glass": PAL["glass"]}, jitter=0.05)
    li = bpy.data.lights.new("wv_lantern_stairhead_light", 'POINT')
    li.energy, li.color, li.shadow_soft_size = 680.0, (1.0, 0.58, 0.24), 0.10
    li.use_custom_distance = True
    li.cutoff_distance = 14.0
    li.shadow_maximum_resolution = 0.01
    lo = bpy.data.objects.new("wv_lantern_stairhead_light", li)
    lo.location = (gx, gy, gz + 0.02)
    link(lo, COLL_A)
    log("BUILD", "wv_lantern_stairhead",
        "post + bracket + lantern + a 680 W / 14 m practical, glass at %.2f,%.2f,%.2f "
        "(post SEARCHED: %.2f m / %.0f deg off the top tread, first clear 2.7 m "
        "column) — waterfront_build's own stair-mouth recipe, at the head of the ONE "
        "flight that works" % (gx, gy, gz, rad, ang))
    return [ob, lo]


# ================================================================= RUN
print("\n=== del_ladder_derate ===")
ladder_A()
ladder_B()
if LAMP:
    stairhead_lamp()

# ---------------------------------------------------------- FAITHFULNESS GATE
AFTER = census()
added = sorted(set(AFTER) - set(BEFORE))
gone = sorted(set(BEFORE) - set(AFTER))
changed = sorted(k for k in set(AFTER) & set(BEFORE) if AFTER[k] != BEFORE[k])

ALLOW = ("wv_fishdock_ladder", "e_lockhead__lock-five_", "wv_lantern_stairhead")
bad = [n for n in added + gone + changed if not n.startswith(ALLOW)]

print("\n--- faithfulness gate ---")
print("  objects %d -> %d   added %d, removed %d, changed-in-place %d"
      % (len(BEFORE), len(AFTER), len(added), len(gone), len(changed)))
for n in added:
    print("    + %s" % n)
for n in gone:
    print("    - %s" % n)
for n in changed:
    print("    ~ %s %s -> %s" % (n, BEFORE[n], AFTER[n]))
if bad:
    print("  FAIL — touched objects outside the ladder set:")
    for n in bad:
        print("    !! %s" % n)
    sys.exit(1)
# nothing walkable may have moved: the whole point is that reachability is unchanged
walkish = [n for n in added + gone + changed if n.startswith(("walk_", "bar_"))]
if walkish:
    print("  FAIL — a walk/bar object changed: %s" % walkish)
    sys.exit(1)
print("  OK — only the ladder set (and the lamp, if asked) moved.")

if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("SAVED %s (%d bytes)" % (BLEND, os.path.getsize(BLEND)))
else:
    print("DRY RUN — pass `save` to write the master.")
