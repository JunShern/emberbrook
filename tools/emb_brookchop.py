"""emb_brookchop.py — EMBERBROOK'S WATER IS A RAFT OF FLOATING BOXES; this seats it.

    Blender -b tools/blends/emberbrook-dressed.blend --python-exit-code 1 \
        -P tools/emb_brookchop.py -- [save] [revert save]
        [--zclamp 0.12] [--zsmooth 60] [--xysmooth 6] [--xyclamp 0.28]
        [--skirt 0.90] [--bury 0.03] [--sheets a,b]

A CARRIER, NEVER A REBUILD (CLAUDE.md, the gate_rimchop rule).  Emberbrook is dressed;
`emb_blockout` + `emb_dress` would re-derive 27 M triangles to move five sheets.  This
opens the dressed master, reshapes ONLY the meshes wearing `emb_dress_water`, and saves.
`tools/emb_blockout.py`'s `water_field` carries the same three fixes in the same commit,
so a future full rebuild agrees with what shipped (search WATER SEATING there).

ORDER OF OPERATIONS — THIS FILE REFUSES TO RUN OUT OF IT.  `emb_water_shader.py`
SUBDIVIDES the sheets and bakes a `Col` depth->alpha layer keyed to their vertices; its
own snapshot (`embws`) holds the PRE-subdivision geometry.  Reshaping subdivided sheets
would orphan that bake.  So:

    1. Blender -b ...dressed.blend -P tools/emb_water_shader.py -- revert save
    2. Blender -b ...dressed.blend -P tools/emb_brookchop.py     -- save
    3. Blender -b ...dressed.blend -P tools/emb_water_shader.py -- save

Step 2 asserts step 1 has happened.  Step 3 is OWED: the shipped alpha comes from the
per-vertex depth, and this file changes the geometry that depth is measured on.

================================ WHAT WAS MEASURED, AND ON WHAT ====================

Instrument: `tools/glb_read.mjs` over the SHIPPED collision bundle
`public/assets/scenes/emb-cine/scene.glb` — every up-facing water triangle's centroid,
and the highest non-water surface directly under it (emb_ground_*/emb_pondbed_*/walk_*,
point-in-triangle, no BVH needed at 95 k tris).  2026-08-07:

    sheet              up faces   water surface ABOVE its own bed (min/p10/p50/p90/max)
    water_emb_brook       750     -0.016 / 0.208 / 0.287 / 0.420 / 5.745 m
    water_emb_pond       1416     -0.020 / 0.054 / 0.233 / 0.772 / 4.955 m
    water_emb_millpond    164      1.795 / 1.855 / 2.037 / 2.182 / 2.299 m

Every sheet is built by `water_field()` as INDEPENDENT 0.55 m boxes **0.12 m thick**.
A surface 0.29 m above its bed on a 0.12 m box is 0.17 m OF AIR under the water: the
box's underside and its four walls are lit, and it casts a shadow onto the bed it is
supposed to be lying in.  That is the whole of the judge's "stacked mitred slabs" and
most of "no believable wet shore contacts" — it is GEOMETRY, and the ratified
depth->alpha recipe (correctly ported, 2026-08-07) moved 269 px of 4.1 M because a
shader cannot close an air gap.

And two more, from the same census:

  * THE BROOK'S TOP IS A STAIRCASE.  `brook_level()` snaps each cell to the z of the
    NEAREST course vertex, so 750 top faces carry 196 distinct heights (1 mm bins) with
    steps to 0.106 m.  Adjacent 0.55 m cells therefore stand on visible 1-10 cm risers
    the whole 3.1 m fall.
  * THE PLAN SILHOUETTE IS THE LATTICE.  A cell is in if its CENTRE is within `BW/2`,
    so a 1.2 m brook is two cells wide and its bank is a 0.55 m staircase in plan.

=================================== THE THREE FIXES ================================

 1. WELD.  Each ring's vertices are grouped by (x, y) to 1 mm and given that group's mean
    z, then merged.  375 detached boxes become ONE strip; the internal walls collapse and
    are dissolved.  The rings are 0.12 m apart, so a 1e-4 merge cannot cross them — the
    z-averaging is what makes the merge possible and it is applied PER RING.

 2. SMOOTH — THE PLAN SILHOUETTE ONLY, because the z half was measured inert and then
    harmful.  The boundary loop's XY is relaxed, clamped at `--xyclamp` 0.28 m (half a
    cell), and every vertex with other than two boundary neighbours is PINNED so a
    junction (the brook meeting the pond) cannot be pulled apart.  Bottom-ring vertices
    take the same XY delta as their partner, so the walls stay vertical.

    THE Z RELAXATION IS REFUTED AND SHIPS AT `--zsmooth 0`.  The hypothesis was the
    census's 196 distinct top heights with steps to 0.106 m.  It does not survive the
    weld: once the ring is ONE surface, edge-to-edge z differences on the brook are
    p90 0.023 / max 0.083 m over a 0.55 m span, which IS the channel's own 4% fall and
    not a riser — the 0.106 m figure was the gap between two SEPARATE cells' heights,
    not a step you can see.  Run against it (same blend, same everything, `--zsmooth 60`
    vs `0`): risers p90/max 0.023/0.083 -> **0.024/0.093**, distinct levels 376 -> 514.
    The relaxation made the surface rougher, because a clamped average that then has to
    be repaired against the bed is noise. The knob stays, at 0, with its refutation.

 3. SEAT.  Every bottom-ring vertex drops to `bed_under(x, y) - bury`, capped at
    `--skirt` metres below its own top vertex.  The cap exists because seating is only
    right where the bed IS the bottom: `water_emb_millpond` floats 2.0 m over
    `emb_ground_valley` (its basin is massing, not a carve), and a 2 m wall of water with
    no dam under it is a worse frame than a thin box.  Sheets that hit the cap are
    PRINTED with their count — a capped sheet is a map/blockout finding, not a silent
    default.  Open sheets (`water_emb_river`, `emb_dress_wheelpit_water` — one ring, no
    bottom) are reported and skipped; they have no air gap to close.

WHAT THIS FILE MAY NOT DO: it must not move a top surface more than `--zclamp`, must not
move any vertex in XY more than `--xyclamp`, and must not put a water surface below its
own bed.  All three are asserted after the edit, per sheet, and printed.

Invertible, and NOT IDEMPOTENT — read this before running it twice.  The weld and the
seat are both fixed points (a welded mesh re-welds to itself, a seated bottom re-seats to
the same bed), but `--xysmooth` RELAXES AGAIN: a second run moves the boundary another
`--xyclamp` because the clamp is measured against THAT run's starting position.  To re-run
with different flags, `revert save` FIRST.  Pre-edit geometry lives in each object's
`embbc` prop, so the revert is exact.  Receipt at
tools/blends/districts/emb_brookchop.<blend>.json every run — one per blend, because this
carrier is run against both tiers.

THE REALTIME TIER TAKES THE WELD AND THE SEAT, NOT THE SILHOUETTE (shipped
`--xysmooth 0`).  `emberbrook-realtime.blend` carries the same sheets after
`emb_decimate`, and decimation tilts faces out of the up-ring: the brook reports 924
boundary vertices of 1042 and a 570 m top-ring boundary against the dressed tier's 438 and
241 m.  On that mesh "the boundary loop" is largely interior seams, and relaxing them
would tear the surface rather than round a staircase.  The air gap is the defect that
carries; the silhouette relaxation is refused where the instrument cannot see one.
"""
import bpy, sys, os, json, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
# ONE RECEIPT PER BLEND. This carrier runs against BOTH tiers (the dressed plate master
# and emberbrook-realtime.blend) and a single filename let the second run overwrite the
# first's numbers, which is exactly the kind of quiet loss a receipt exists to prevent.
MANIFEST = os.path.join(REPO, "tools/blends/districts/emb_brookchop.%s.json"
                        % os.path.splitext(os.path.basename(bpy.data.filepath or "unknown"))[0])

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


ZCLAMP = float(opt("--zclamp", "0.12"))
ZITER = int(opt("--zsmooth", "0"))          # REFUTED — see the docstring; 0 is the ship
XYITER = int(opt("--xysmooth", "6"))
XYCLAMP = float(opt("--xyclamp", "0.28"))
SKIRT = float(opt("--skirt", "0.90"))
BURY = float(opt("--bury", "0.03"))
ONLY = [s for s in (opt("--sheets", "") or "").split(",") if s]

MAT = "emb_dress_water"
WATERISH_MATS = ("emb_dress_water", "emb_dress_waterfall", "emb_dress_mist")
PROP = "embbc"
WSPROP = "embws"
UP_DOT = 0.5
KEY = 3                       # (x, y) rounding for the weld, decimal places = 1 mm

sc = bpy.context.scene
mat = bpy.data.materials.get(MAT)
assert mat is not None, "no %s in this blend — is this the dressed master?" % MAT


def mats_of(o):
    return {s.material.name for s in o.material_slots if s.material}


WOBJ = [o for o in sc.objects if o.type == 'MESH' and MAT in mats_of(o)]
assert WOBJ, "no meshes wear %s" % MAT
if ONLY:
    WOBJ = [o for o in WOBJ if o.name in ONLY]
    assert WOBJ, "--sheets matched nothing"

# ================================================================ REVERT ======
if REVERT:
    n = 0
    for o in WOBJ:
        if not o.get(PROP):
            continue
        st = json.loads(o[PROP])
        me = o.data
        me.clear_geometry()
        me.from_pydata([tuple(v) for v in st["verts"]], [], [tuple(p) for p in st["polys"]])
        me.validate()
        me.update()
        me.materials.clear()
        me.materials.append(mat)
        del o[PROP]
        n += 1
        print("RESTORED %-26s %d verts %d polys" % (o.name, len(st["verts"]), len(st["polys"])))
    print("reverted %d sheet(s)" % n)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the blend)")
    sys.exit(0)

# THE ORDER GATE.  A sheet still carrying the water shader's snapshot is a SUBDIVIDED
# sheet with a baked Col keyed to vertices this file is about to move.
held = [o.name for o in WOBJ if o.get(WSPROP)]
assert not held, (
    "these sheets still carry emb_water_shader's '%s' snapshot (they are subdivided and "
    "carry a baked Col keyed to their current vertices): %s\n"
    "Run first:  Blender -b %s --python-exit-code 1 -P tools/emb_water_shader.py -- revert save\n"
    "and AFTER this file:  ... -P tools/emb_water_shader.py -- save"
    % (WSPROP, ", ".join(held), os.path.relpath(bpy.data.filepath, REPO)))

print("=" * 78)
print("emb brookchop — weld / smooth / seat   zclamp %.2f (%d it)  xyclamp %.2f (%d it)  "
      "skirt %.2f  bury %.2f" % (ZCLAMP, ZITER, XYCLAMP, XYITER, SKIRT, BURY))
print("=" * 78)

# ------------------------------------------------------------- the bed, once --
# Same construction as emb_water_shader: Scene.ray_cast over a 27 M-triangle dressed
# master did not return 57 k rays in sixteen minutes.  Only what stands under a sheet's
# own footprint can be its bed.
dg = bpy.context.evaluated_depsgraph_get()
WATERISH = {o.name for o in sc.objects
            if o.type == 'MESH' and (mats_of(o) & set(WATERISH_MATS))}


def world_aabb(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(w.x for w in ws), max(w.x for w in ws),
            min(w.y for w in ws), max(w.y for w in ws),
            min(w.z for w in ws), max(w.z for w in ws))


FOOT = [world_aabb(o) for o in WOBJ]
PAD = 2.0


def overlaps_any(bb):
    for f in FOOT:
        if (bb[0] <= f[1] + PAD and bb[1] >= f[0] - PAD and
                bb[2] <= f[3] + PAD and bb[3] >= f[2] - PAD and
                bb[4] <= f[5] + 1.0 and bb[5] >= f[4] - 60.0):
            return True
    return False


bverts, bpolys, nobj = [], [], 0
for o in sc.objects:
    if o.type != 'MESH' or o.name in WATERISH:
        continue
    try:
        bb = world_aabb(o)
    except Exception:
        continue
    if not overlaps_any(bb):
        continue
    oe = o.evaluated_get(dg)
    try:
        me = oe.to_mesh()
    except Exception:
        continue
    if me is None:
        continue
    M = oe.matrix_world
    base = len(bverts)
    bverts.extend([M @ v.co for v in me.vertices])
    bpolys.extend([[base + i for i in p.vertices] for p in me.polygons])
    oe.to_mesh_clear()
    nobj += 1
assert bpolys, "no candidate bed geometry under any water footprint — an instrument that " \
               "finds no bed must be able to prove it could have found one"
BED = BVHTree.FromPolygons(bverts, bpolys, all_triangles=False)
print("bed BVH: %d meshes / %d verts / %d polys under the %d footprints"
      % (nobj, len(bverts), len(bpolys), len(WOBJ)))
DOWN = Vector((0, 0, -1))


def bed_under(x, y, z):
    hit = BED.ray_cast(Vector((x, y, z + 0.05)), DOWN, 120.0)
    return hit[0].z if hit[0] is not None else None


def med(xs):
    return sorted(xs)[len(xs) // 2] if xs else None


def qs(xs):
    if not xs:
        return "-"
    s = sorted(xs)
    return "%.3f/%.3f/%.3f/%.3f" % (s[0], s[len(s) // 10], s[len(s) // 2], s[-1])


report = {}
for o in sorted(WOBJ, key=lambda x: x.name):
    me = o.data
    M = o.matrix_world
    Minv = M.inverted()
    if not o.get(PROP):
        o[PROP] = json.dumps(dict(
            verts=[[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)] for v in me.vertices],
            polys=[list(p.vertices) for p in me.polygons]))
    ORIG = json.loads(o[PROP])
    n_before, p_before = len(me.vertices), len(me.polygons)

    # --- WHICH RING IS THE TOP (emb_water_shader's rule: these sheets' normals are
    #     inverted, so the HIGHER mean z wins, and a one-ring sheet is open).
    N = M.to_3x3().inverted().transposed()
    plus, minus = [], []
    for p in me.polygons:
        nz = (N @ p.normal).normalized().z
        if nz > UP_DOT:
            plus.append(p.index)
        elif nz < -UP_DOT:
            minus.append(p.index)

    def meanz(idxs):
        if not idxs:
            return -1e9
        vs = [v for i in idxs for v in me.polygons[i].vertices]
        return sum((M @ me.vertices[v].co).z for v in vs) / len(vs)

    zp, zm = meanz(plus), meanz(minus)
    open_sheet = not (plus and minus)
    if open_sheet:
        print("  %-26s OPEN SHEET (one ring, no bottom) — no air gap to close, SKIPPED"
              % o.name)
        report[o.name] = dict(skipped="open sheet", verts=n_before, polys=p_before)
        del o[PROP]
        continue
    top_faces = set(plus if zp > zm else minus)
    bot_faces = set(minus if zp > zm else plus)
    top_v = {v for i in top_faces for v in me.polygons[i].vertices}
    bot_v = {v for i in bot_faces for v in me.polygons[i].vertices}

    # ============================================================ 1. WELD =====
    # Per ring, group by (x, y) to 1 mm and take that group's MEAN z, so the members
    # become exactly coincident and a 1e-4 merge can join them.  The rings are 0.12 m
    # apart; the merge cannot cross them.
    world = [M @ v.co for v in me.vertices]
    # the AS-BUILT staircase, before this file touches anything (the weld's own
    # per-group z-averaging is already a smoothing, so it must be measured first)
    lv_pre = len({round(world[vi].z * 1000) for vi in top_v})
    zspan_pre = (min(world[vi].z for vi in top_v), max(world[vi].z for vi in top_v))
    for ring in (top_v, bot_v):
        groups = {}
        for vi in ring:
            w = world[vi]
            groups.setdefault((round(w.x, KEY), round(w.y, KEY)), []).append(vi)
        for g in groups.values():
            if len(g) < 2:
                continue
            zz = sum(world[i].z for i in g) / len(g)
            for i in g:
                world[i] = Vector((world[i].x, world[i].y, zz))
    for vi, w in enumerate(world):
        me.vertices[vi].co = Minv @ w
    me.update()

    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=list(bm.edges))
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    n_weld, p_weld = len(me.vertices), len(me.polygons)

    # --- re-classify after the weld (indices moved)
    N = M.to_3x3().inverted().transposed()
    plus, minus = [], []
    for p in me.polygons:
        nz = (N @ p.normal).normalized().z
        if nz > UP_DOT:
            plus.append(p.index)
        elif nz < -UP_DOT:
            minus.append(p.index)
    zp, zm = meanz(plus), meanz(minus)
    top_faces = set(plus if zp > zm else minus)
    bot_faces = set(minus if zp > zm else plus)
    top_v = sorted({v for i in top_faces for v in me.polygons[i].vertices})
    bot_v = sorted({v for i in bot_faces for v in me.polygons[i].vertices})
    # A VERTEX THAT IS BOTH A TOP AND A BOTTOM IS NOT SEATABLE, and on this town's other
    # tier it is not hypothetical: `emberbrook-realtime.blend` carries the SAME sheets
    # after `emb_decimate`, and its collapsed triangles put 375 vertices in both rings.
    # Seating one of those writes the bed height onto a surface vertex — measured, the
    # first run against the realtime tier moved a TOP vertex 0.900 m and the z clamp
    # caught it. Only bottom-exclusive vertices are seated; the count is printed, so a
    # tier where the rings have fused says so instead of being quietly half-seated.
    shared = sorted(set(top_v) & set(bot_v))
    bot_only = [v for v in bot_v if v not in set(shared)]
    world = [M @ v.co for v in me.vertices]
    z0 = {vi: world[vi].z for vi in top_v}
    xy0 = {vi: (world[vi].x, world[vi].y) for vi in range(len(world))}

    # top-ring edge graph + boundary loop (an edge with exactly one top face)
    nbr = {vi: set() for vi in top_v}
    ecount = {}
    for i in top_faces:
        vs = list(me.polygons[i].vertices)
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]
            nbr[a].add(b)
            nbr[b].add(a)
            ecount[(min(a, b), max(a, b))] = ecount.get((min(a, b), max(a, b)), 0) + 1
    bnd = set()
    bnbr = {}
    for (a, b), c in ecount.items():
        if c == 1:
            bnd.add(a)
            bnd.add(b)
            bnbr.setdefault(a, set()).add(b)
            bnbr.setdefault(b, set()).add(a)

    # THE RAGGEDNESS METRIC, taken before and after: the length of the top ring's own
    # boundary loop.  A lattice staircase walks two legs of every triangle it could have
    # walked one hypotenuse of, so a silhouette cut on a 0.55 m grid is measurably LONGER
    # than the curve it is approximating.  Perimeter is therefore the honest number for
    # "did the plan silhouette stop being the lattice", and it costs one pass.
    bedges = [(a, b) for (a, b), c in ecount.items() if c == 1]

    def perim(pos):
        return sum((pos[a] - pos[b]).length for a, b in bedges)

    perim0 = perim(world)

    # ========================================================== 2. SMOOTH =====
    # z: Laplacian over the top ring, clamped against the ORIGINAL height.  The 3.1 m
    # fall is authored; the 1-10 cm risers are the nearest-vertex snap.
    for _ in range(ZITER):
        newz = {}
        for vi in top_v:
            ns = nbr[vi]
            if not ns:
                continue
            newz[vi] = 0.5 * world[vi].z + 0.5 * (sum(world[j].z for j in ns) / len(ns))
        for vi, z in newz.items():
            z = max(z0[vi] - ZCLAMP, min(z0[vi] + ZCLAMP, z))
            world[vi] = Vector((world[vi].x, world[vi].y, z))
    # xy: the boundary loop only, clamped at half a cell.  A vertex with anything other
    # than two boundary neighbours is a junction and is PINNED (the brook meets the pond).
    for _ in range(XYITER):
        newxy = {}
        for vi in bnd:
            ns = list(bnbr.get(vi, ()))
            if len(ns) != 2:
                continue
            ax = (world[ns[0]].x + world[ns[1]].x) / 2.0
            ay = (world[ns[0]].y + world[ns[1]].y) / 2.0
            newxy[vi] = (0.5 * world[vi].x + 0.5 * ax, 0.5 * world[vi].y + 0.5 * ay)
        for vi, (x, y) in newxy.items():
            ox, oy = xy0[vi]
            dx, dy = x - ox, y - oy
            L = math.hypot(dx, dy)
            if L > XYCLAMP:
                dx, dy = dx / L * XYCLAMP, dy / L * XYCLAMP
            world[vi] = Vector((ox + dx, oy + dy, world[vi].z))

    # --- AND THE SURFACE MAY NOT SINK INTO ITS OWN BED.  Relaxing a staircase averages,
    # and an average pulls the top of a riser DOWN — where the bed rises under it (the
    # brook's ford, the pond's shore) that can put water under ground.
    # THE REPAIR IS TO RESTORE THE SHIPPED z, NOT TO LIFT.  Lifting to `bed + 1 cm` was
    # tried first and REFUTED by its own receipt: `water_emb_pond` ships as ONE flat
    # level at 0.80 and the lift put 40 distinct levels across 0.80..0.86 into it — a
    # bumpy pond, manufactured by a repair, on a sheet whose staircase was never the
    # complaint.  Restoring z0 is exactly as good against the bed (z0 is what shipped)
    # and cannot invent a height the map did not author.
    bedz, below0 = {}, 0
    for vi in top_v:
        b = bed_under(world[vi].x, world[vi].y, z0[vi])
        bedz[vi] = b
        if b is not None and z0[vi] < b - 1e-3:
            below0 += 1
    lifted = 0
    for vi in top_v:
        b = bedz[vi]
        if b is None or world[vi].z >= b - 1e-3 or z0[vi] < b - 1e-3:
            continue
        lifted += 1
        world[vi] = Vector((world[vi].x, world[vi].y, z0[vi]))

    # the bottom ring follows its partner's XY so the walls stay vertical
    tk = {}
    for vi in top_v:
        tk.setdefault((round(xy0[vi][0], KEY), round(xy0[vi][1], KEY)), vi)
    paired = 0
    for vi in bot_only:
        p = tk.get((round(xy0[vi][0], KEY), round(xy0[vi][1], KEY)))
        if p is None:
            continue
        world[vi] = Vector((world[p].x, world[p].y, world[vi].z))
        paired += 1

    # ============================================================ 3. SEAT =====
    capped, bedless, seated, depths = 0, 0, 0, []
    for vi in bot_only:
        p = tk.get((round(xy0[vi][0], KEY), round(xy0[vi][1], KEY)))
        topz = world[p].z if p is not None else world[vi].z + 0.12
        b = bed_under(world[vi].x, world[vi].y, topz)
        if b is None:
            bedless += 1
            continue
        want = b - BURY
        floor = topz - SKIRT
        if want < floor:
            want = floor
            capped += 1
        # A BOTTOM RING IS STILL A BOTTOM.  Where the bed stands ABOVE the water line
        # (every shore cell: the census measured brook/pond surfaces down to -0.02 m of
        # depth) `bed - bury` is above the top, and a sheet whose bottom is over its own
        # top renders inside out.  2 cm is the thinnest this will build.
        want = min(want, topz - 0.02)
        if want < world[vi].z - 1e-6:
            seated += 1
        depths.append(topz - want)
        world[vi] = Vector((world[vi].x, world[vi].y, want))

    for vi, w in enumerate(world):
        me.vertices[vi].co = Minv @ w
    me.update()

    # ========================================================= ASSERTIONS =====
    wnow = [M @ v.co for v in me.vertices]
    dz = [abs(wnow[vi].z - z0[vi]) for vi in top_v]
    dxy = [math.hypot(wnow[vi].x - xy0[vi][0], wnow[vi].y - xy0[vi][1]) for vi in range(len(wnow))]
    assert max(dz) <= ZCLAMP + 1e-4, "%s: a top vertex moved %.4f m in z (clamp %.2f)" % (
        o.name, max(dz), ZCLAMP)
    assert max(dxy) <= XYCLAMP + 1e-4, "%s: a vertex moved %.4f m in xy (clamp %.2f)" % (
        o.name, max(dxy), XYCLAMP)
    below = 0
    for vi in top_v:
        b = bedz.get(vi)
        if b is not None and wnow[vi].z < b - 1e-3:
            below += 1
    assert below <= below0, (
        "%s: %d top vertices ended below their own bed, up from %d as built"
        % (o.name, below, below0))

    # residual staircase, the number the whole file exists to move
    lv_before = len({round(z0[vi] * 1000) for vi in top_v})
    steps_before, steps_after = [], []
    for (a, b), c in ecount.items():
        if a in z0 and b in z0:
            steps_before.append(abs(z0[a] - z0[b]))
            steps_after.append(abs(wnow[a].z - wnow[b].z))
    report[o.name] = dict(
        verts=[n_before, n_weld, len(me.vertices)],
        polys=[p_before, p_weld, len(me.polygons)],
        top_faces=len(top_faces), bot_faces=len(bot_faces),
        boundary_verts=len(bnd), paired_bottom=paired,
        riser_max_before=round(max(steps_before), 4) if steps_before else None,
        riser_max_after=round(max(steps_after), 4) if steps_after else None,
        riser_p90_before=round(sorted(steps_before)[int(.9 * (len(steps_before) - 1))], 4) if steps_before else None,
        riser_p90_after=round(sorted(steps_after)[int(.9 * (len(steps_after) - 1))], 4) if steps_after else None,
        top_levels_asbuilt=lv_pre, top_levels_afterweld=lv_before,
        top_levels_after=len({round(wnow[vi].z * 1000) for vi in top_v}),
        top_z_span_asbuilt=[round(zspan_pre[0], 3), round(zspan_pre[1], 3)],
        top_z_span_after=[round(min(wnow[vi].z for vi in top_v), 3),
                          round(max(wnow[vi].z for vi in top_v), 3)],
        seated=seated, capped=capped, bedless=bedless,
        ring_shared_verts=len(shared), bottom_only_verts=len(bot_only),
        surface_below_bed=[below0, below], restored_to_shipped_z=lifted,
        boundary_perimeter=[round(perim0, 2), round(perim(wnow), 2)],
        wall_height_min=round(min(depths), 3) if depths else None,
        wall_height_p50=round(med(depths), 3) if depths else None,
        wall_height_max=round(max(depths), 3) if depths else None,
        dz_max=round(max(dz), 4), dxy_max=round(max(dxy), 4))
    r = report[o.name]
    print("  %-26s verts %d -> %d -> %d   polys %d -> %d -> %d" %
          (o.name, r["verts"][0], r["verts"][1], r["verts"][2],
           r["polys"][0], r["polys"][1], r["polys"][2]))
    print("      risers p90/max %.3f/%.3f -> %.3f/%.3f m   top levels %d as built -> %d "
          "welded -> %d   z span %.2f..%.2f -> %.2f..%.2f"
          % (r["riser_p90_before"] or 0, r["riser_max_before"] or 0,
             r["riser_p90_after"] or 0, r["riser_max_after"] or 0,
             r["top_levels_asbuilt"], r["top_levels_afterweld"], r["top_levels_after"],
             r["top_z_span_asbuilt"][0], r["top_z_span_asbuilt"][1],
             r["top_z_span_after"][0], r["top_z_span_after"][1]))
    print("      seated %d bottom verts (capped at %.2f m: %d, bedless: %d)   wall height "
          "min/p50/max %s/%s/%s m   moved dz<=%.3f dxy<=%.3f"
          % (r["seated"], SKIRT, r["capped"], r["bedless"],
             r["wall_height_min"], r["wall_height_p50"], r["wall_height_max"],
             r["dz_max"], r["dxy_max"]))
    print("      boundary loop %.2f m -> %.2f m (%+.1f%%; a lattice silhouette is LONGER "
          "than the curve it approximates)   %d boundary verts, %d surface verts below "
          "their own bed (%d as built)"
          % (r["boundary_perimeter"][0], r["boundary_perimeter"][1],
             100.0 * (r["boundary_perimeter"][1] / max(1e-9, r["boundary_perimeter"][0]) - 1),
             r["boundary_verts"], below, below0))

os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
json.dump(dict(
    _doc=("GENERATED by tools/emb_brookchop.py — Emberbrook's water sheets were "
          "independent 0.55 m x 0.12 m boxes floating 0.09-2.0 m above their own beds "
          "(census: tools/glb_read.mjs over emb-cine/scene.glb, DAYLOG 2026-08-07). "
          "This welds each sheet into one strip, relaxes the nearest-vertex staircase "
          "out of the brook's top, and drops each bottom ring onto the bed. "
          "OWES an emb_water_shader.py re-run: the shipped alpha is a per-vertex depth."),
    generator="tools/emb_brookchop.py", blend=bpy.data.filepath, material=MAT,
    zclamp=ZCLAMP, zsmooth=ZITER, xyclamp=XYCLAMP, xysmooth=XYITER,
    skirt=SKIRT, bury=BURY, saved=bool(SAVE), sheets=report,
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, REPO))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
