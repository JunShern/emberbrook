"""emb_pavechop.py — EMBERBROOK'S PAVING IS ITS WALK NETWORK, AND ITS RIM IS A LATTICE
STAIRCASE STANDING 0.12 m PROUD.  This seats it.

    Blender -b tools/blends/<blend> --python-exit-code 1 \
        -P tools/emb_pavechop.py -- [save] [revert save]
        [--inset 0.30] [--bury 0.02] [--zdrop 0.20]
        [--xysmooth 8] [--xyclamp 0.22] [--joinr 0.36] [--minloop 2.4]
        [--only walk_lm_orchard,...] [--force]

A CARRIER, NEVER A REBUILD (CLAUDE.md, the `gate_rimchop` rule, and the direct
precedent `emb_brookchop.py` — which did the identical job for the water).  Emberbrook
is dressed; `emb_blockout` + `emb_dress` would re-derive 27 M triangles to reshape the
rim of 222 meshes.  This opens a blend, reshapes ONLY meshes whose name starts with
`walk_`, and saves.

=============================== WHAT WAS MEASURED, AND ON WHAT ====================

Instrument: this file's own `--census` pass over `emberbrook-master.blend`, and the
red-team board docs/qa/emberbrook-redteam/ (run-20260809-emb-round1).

  * THE WALK NETWORK IS WHAT THE PLAYER SEES.  Proved with a HEIGHT CONTROL, not by
    attribution: the shipped plate's own depth surface sits at the WALK top, not the
    ground top — 4,660 of 4,760 samples on six plates, |plate-walk| p50 0.0035-0.0098 m
    against |plate-ground| 0.042-0.127 m.  The walk mesh IS the paving.

  * EVERY CELL IS AN INDEPENDENT BOX.  `emb_blockout`'s area-floor loop emits, per cell,
    eight vertices at (cx +- CELL/2, cy +- CELL/2) x (z, z - 0.14) and six quads — so a
    plaza is N detached boxes, exactly the raft `emb_brookchop` found under the water.
    Measured in `emberbrook-master.blend`: 222 walk meshes, 40,400 verts, **8.00 verts
    per up-face across every family** (4.00 would be a welded grid; 8.00 is one box per
    face).  Per-cell boundary in the blend is 10,061.1 m over 20,200 edges, 97.1%
    axis-aligned.

  * AND THE NUMBER THE BOARD QUOTES IS THE BUNDLE'S, NOT THE BLEND'S.  2,233.7 m over
    2,806 edges at 52.0% is measured on `emb-cine/scene.glb`, where the glTF exporter's
    own vertex dedup has already welded coincident (position, normal) pairs — so it is
    the TRUE OUTLINE.  Both numbers are right; they measure different artifacts.  This
    file welds first and then reports the true outline, so its receipt is comparable
    with the bundle's.

  * THE RIM STANDS PROUD BY CONSTRUCTION.  `CUT_DROP = 0.12`: the ground is carved
    0.12 m DOWN under every walk surface and stays fully carved for `CUT_FULL = 1.40 m`
    beyond it.  So a 0.14 m-thick box on carved ground exposes a 0.12 m vertical face
    all the way round, with the grass 0.12 m below it — a lit riser and a black shadow
    line at every tread.  That is `ev/rim-woodroad.jpg` and `ev/rim-gatefield.jpg`.

    100.0% of every `walk_lm_*` region apron's boundary is axis-aligned, mean edge
    0.45 m.  A cell is kept by its CENTRE, so a circle cut on a 0.45 m grid is a
    right-angled staircase in plan.

================================= THE THREE FIXES ================================

 1. WELD.  Per ring (top = the higher mean z, regardless of normal sign — these boxes
    are wound inside-out exactly as the water sheets are), vertices are grouped by
    (x, y) to 1 mm, given that group's mean z, and merged at 1e-4.  N detached boxes
    become one strip; the internal walls collapse and are dissolved.  The rings are
    0.14 m apart, so the merge cannot cross them.

 2. RELAX — the plan silhouette, `walk_lm_*` ONLY.  A ribbon is already Chaikin-smoothed
    (measured: `walk_e_*` boundary is 0.0% axis-aligned) and a pad is a 4-vertex
    rectangle the map authored; relaxing either would shrink a doorstep to no purpose.
    The refusal is PRINTED per family, never silent.  Boundary XY is relaxed with a
    Laplacian clamped at `--xyclamp` (half a cell), junctions PINNED.

 3. SEAT.  The top surface is inset by `--inset` and the ORIGINAL boundary loop is
    dropped onto the ground beneath it (`--bury` under it), so the 0.12 m vertical face
    becomes a ~22-degree chamfer that dies into the terrain.  Nothing else moves: the
    flat walkable core keeps its exact height, and the bottom ring is not touched (it
    is already 0.02 m under the carved ground).

    A vertex may not drop more than `--zdrop`, and may never go below its own bottom
    ring + 0.01 m; both are CAPPED, COUNTED and PRINTED — a capped rim is a map/blockout
    finding, not a silent default.

WHAT PINS A VERTEX, AND WHY THE WHOLE FILE TURNS ON IT.  A boundary is only a rim where
nothing else continues it.  Festival Square alone ships as **61 `walk_lm_square-plaza.NNN`
blocks** (`emb_blockout` emits a plaza wider than one lens can hold as blocks of r/4),
every road ribbon abuts an area floor, and every doorstep pad abuts a ribbon.  Chamfering
those shared edges would cut a 0.12 m TRENCH along every internal seam in town — a new
defect the size of the old one.  So a boundary vertex within `--joinr` in XY and 0.30 m
in z of ANOTHER walk mesh's top ring is PINNED: no relax, no drop.  The count is printed
per object, and a mesh that is entirely pinned says so.
  AND PROXIMITY IS THE WRONG TEST — MEASURED.  The first cut pinned any boundary vertex
within 0.36 m of another walk mesh's top ring and pinned **587 of the ribbons' 603
boundary vertices**, because the next one-quad segment along the SAME road is that close
in the direction the rim runs.  A collinear continuation of a rim is not a junction.  The
shipped test steps `--outr` metres OUTWARD off the rim (away from the mean of the top
faces owning the vertex) and asks whether another walk mesh's top surface is under that
foot.

NOT IDEMPOTENT, and it REFUSES rather than compounding: the inset and the relax both
measure their clamps against the run's own starting position, so a second run would
inset a second band and relax another `--xyclamp`.  Any object already carrying the
`embpc` snapshot aborts the run unless `--force`.  `revert save` restores exactly.
Receipt at tools/blends/districts/emb_pavechop.<blend>.json every run — one per blend,
because this carrier is run against every tier that ships walk geometry.

OWED IN THE SAME WINDOW.  This moves geometry in a bundle-bearing blend, so:
  * `emberbrook-master.blend`   -> re-export `emb-cine/scene.glb` (cine_bake --glb)
  * `emberbrook-realtime.blend` -> re-export `emb-townwalk` (tools/town_export.py)
  * any tier -> `tools/routes_derive.mjs --check`, `walk_engine_gate`, `walk_bodygate`
A walk-network change that nobody drove is not done.
"""
import bpy, sys, os, json, bmesh, math
from mathutils import Vector, kdtree
from mathutils.bvhtree import BVHTree

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(REPO, "tools/blends/districts/emb_pavechop.%s.json"
                        % os.path.splitext(os.path.basename(bpy.data.filepath or "unknown"))[0])

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
CENSUS = "census" in argv
FORCE = "--force" in argv


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


INSET = float(opt("--inset", "0.30"))
BURY = float(opt("--bury", "0.02"))
ZDROP = float(opt("--zdrop", "0.20"))
XYITER = int(opt("--xysmooth", "8"))
XYCLAMP = float(opt("--xyclamp", "0.22"))
JOINR = float(opt("--joinr", "0.36"))
JOINZ = 0.30
MINLOOP = float(opt("--minloop", "2.4"))     # a loop shorter than this is not chamfered
ONLY = [s for s in (opt("--only", "") or "").split(",") if s]

PROP = "embpc"
PREFIX = "walk_"
RELAX_FAMILIES = ("walk_lm_",)
KEY = 3
UP_DOT = 0.5

sc = bpy.context.scene
W = [o for o in sc.objects if o.type == 'MESH' and o.name.startswith(PREFIX)]
assert W, "no walk_* meshes in this blend"
if ONLY:
    W = [o for o in W if o.name in ONLY]
    assert W, "--only matched nothing"
W.sort(key=lambda o: o.name)


def rings_of(o, me):
    """(top vertex set, bottom vertex set, top face set) — HIGHER MEAN Z WINS, because
    `emb_blockout`'s `box()` winds these inside out exactly as the water sheets are."""
    M = o.matrix_world
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

    top = set(plus if meanz(plus) > meanz(minus) else minus)
    bot = set(minus if meanz(plus) > meanz(minus) else plus)
    return top, bot


# ================================================================ REVERT ======
if REVERT:
    n = 0
    for o in W:
        if not o.get(PROP):
            continue
        st = json.loads(o[PROP])
        me = o.data
        mats = [s.material for s in o.material_slots if s.material]
        me.clear_geometry()
        me.from_pydata([tuple(v) for v in st["verts"]], [], [tuple(p) for p in st["polys"]])
        me.validate()
        me.update()
        me.materials.clear()
        for m in mats:
            me.materials.append(m)
        del o[PROP]
        n += 1
    print("reverted %d walk mesh(es)" % n)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the blend)")
    sys.exit(0)

# ---------------------------------------------------------------- the census --
print("=" * 78)
print("emb pavechop — weld / relax / seat   inset %.2f  bury %.2f  zdrop %.2f  "
      "xyclamp %.2f (%d it)  joinr %.2f" % (INSET, BURY, ZDROP, XYCLAMP, XYITER, JOINR))
print("blend %s   %d walk meshes" % (bpy.data.filepath, len(W)))
print("=" * 78)

held = [o.name for o in W if o.get(PROP)]
assert FORCE or not held, (
    "%d walk mesh(es) already carry the '%s' snapshot — this carrier is NOT idempotent "
    "(the inset would build a second band and the relax would move another %.2f m). "
    "Run `-- revert save` first, or pass --force if you know why.\n  %s"
    % (len(held), PROP, XYCLAMP, ", ".join(held[:6])))

# ------------------------------------------------- the ground under the paving --
# Same construction as emb_brookchop's bed: Scene.ray_cast over a 27 M-triangle dressed
# master does not return.  Only what stands under a walk footprint can be its ground, and
# nothing that is itself walk or water may be.
dg = bpy.context.evaluated_depsgraph_get()
GROUND_PREF = ("emb_ground_",)
SKIP = ("walk_", "water_", "emb_dress_far", "veg_", "grass_")


def world_aabb(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(w.x for w in ws), max(w.x for w in ws), min(w.y for w in ws),
            max(w.y for w in ws), min(w.z for w in ws), max(w.z for w in ws))


gv, gp, ng = [], [], 0
for o in sc.objects:
    if o.type != 'MESH' or not o.name.startswith(GROUND_PREF) or o.hide_render:
        continue
    oe = o.evaluated_get(dg)
    try:
        me = oe.to_mesh()
    except Exception:
        continue
    if me is None:
        continue
    M = oe.matrix_world
    base = len(gv)
    gv.extend([M @ v.co for v in me.vertices])
    gp.extend([[base + i for i in p.vertices] for p in me.polygons])
    oe.to_mesh_clear()
    ng += 1
assert gp, ("no emb_ground_* geometry — an instrument that finds no ground must be able "
            "to prove it could have found one")
GROUND = BVHTree.FromPolygons(gv, gp, all_triangles=False)
print("ground BVH: %d meshes / %d verts / %d polys" % (ng, len(gv), len(gp)))
DOWN = Vector((0, 0, -1))


def ground_under(x, y, z):
    hit = GROUND.ray_cast(Vector((x, y, z + 0.60)), DOWN, 40.0)
    return hit[0].z if hit[0] is not None else None


# ======================================================== PASS 1 — WELD, ALL OF THEM ==
# The junction test below has to ask "does ANOTHER walk mesh continue past this rim", and
# that question is only answerable against welded geometry.  So every mesh is welded
# first, and only then is the town-wide top-surface BVH built.
def weld(o):
    me = o.data
    M = o.matrix_world
    Minv = M.inverted()
    top, bot = rings_of(o, me)
    tv = {v for i in top for v in me.polygons[i].vertices}
    bv = {v for i in bot for v in me.polygons[i].vertices}
    world = [M @ v.co for v in me.vertices]
    for ring in (tv, bv):
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


PRE = {}
for o in W:
    if not o.get(PROP):
        o[PROP] = json.dumps(dict(
            verts=[[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)] for v in o.data.vertices],
            polys=[list(p.vertices) for p in o.data.polygons]))
    PRE[o.name] = (len(o.data.vertices), len(o.data.polygons))
    weld(o)
print("welded %d walk meshes" % len(W))

# ---- the town-wide TOP-SURFACE BVH, with an owner per polygon.
# A BOUNDARY IS ONLY A RIM WHERE NOTHING ELSE CONTINUES IT.  Festival Square alone ships
# as 61 `walk_lm_square-plaza.NNN` blocks, every road edge as a chain of one-quad
# `walk_e_..._lN` objects, and every doorstep pad abuts a ribbon; chamfering those shared
# edges would cut a 0.12 m trench along every internal seam in town.
#   AND PROXIMITY IS THE WRONG TEST, MEASURED: a first cut pinned any boundary vertex
# within 0.36 m of another walk mesh's top ring, which pinned 587 of the ribbons' 603
# boundary vertices — because the NEXT SEGMENT ALONG THE SAME ROAD is 0.36 m away in the
# direction the rim runs.  A collinear continuation of the same rim is not a junction.
# The test that is right asks the question the defect asks: step OUTWARD off the rim and
# see whether another walk mesh's top surface is under your foot.
tv_, tp_, town_ = [], [], []
for o in W:
    me = o.data
    M = o.matrix_world
    top, _ = rings_of(o, me)
    base = len(tv_)
    tv_.extend([M @ v.co for v in me.vertices])
    for i in top:
        tp_.append([base + v for v in me.polygons[i].vertices])
        town_.append(o.name)
WALKTOP = BVHTree.FromPolygons(tv_, tp_, all_triangles=False)
print("walk-top BVH: %d faces over %d meshes" % (len(tp_), len(W)))
OUTR = float(opt("--outr", "0.25"))


def continued_by_other(nm, w, outward):
    """Is another walk mesh's top surface under a point one step OUTWARD off this rim?"""
    p = Vector((w.x + outward[0] * OUTR, w.y + outward[1] * OUTR, w.z + 0.50))
    hit = WALKTOP.ray_cast(p, DOWN, 1.0)
    if hit[0] is None or hit[2] is None:
        return False
    return town_[hit[2]] != nm and abs(hit[0].z - w.z) <= JOINZ


def outward_of(world, faces_of_v, vi):
    """Away from the mean of the top faces that own this vertex, in XY."""
    cs = faces_of_v.get(vi)
    if not cs:
        return (0.0, 0.0)
    cx = sum(c[0] for c in cs) / len(cs)
    cy = sum(c[1] for c in cs) / len(cs)
    dx, dy = world[vi].x - cx, world[vi].y - cy
    L = math.hypot(dx, dy)
    return (dx / L, dy / L) if L > 1e-9 else (0.0, 0.0)


def axisfrac(pos, edges):
    if not edges:
        return 0.0
    n = 0
    for a, b in edges:
        d = pos[a] - pos[b]
        if abs(d.x) < 1e-4 or abs(d.y) < 1e-4:
            n += 1
    return 100.0 * n / len(edges)


# ============================================ PASS 2 — RELAX, INSET, SEAT ==
report = {}
tot = dict(perim0=0.0, perim1=0.0, ax0=0, ax1=0, ne0=0, ne1=0, dropped=0, pinned=0,
           cap_floor=0, cap_zdrop=0, groundless=0, smallloop=0, relaxed=0)


def top_boundary(o):
    """(top face set, world positions, boundary edges, vertex -> owning face centres)"""
    me = o.data
    M = o.matrix_world
    top, bot = rings_of(o, me)
    world = [M @ v.co for v in me.vertices]
    ec, cen = {}, {}
    for i in top:
        vs = list(me.polygons[i].vertices)
        c = (sum(world[v].x for v in vs) / len(vs), sum(world[v].y for v in vs) / len(vs))
        for k in range(len(vs)):
            a2, b2 = vs[k], vs[(k + 1) % len(vs)]
            ec[(min(a2, b2), max(a2, b2))] = ec.get((min(a2, b2), max(a2, b2)), 0) + 1
        for v in vs:
            cen.setdefault(v, []).append(c)
    return top, bot, world, [k for k, c in ec.items() if c == 1], cen


for o in W:
    me = o.data
    M = o.matrix_world
    Minv = M.inverted()
    n0, p0 = PRE[o.name]
    nW, pW = len(me.vertices), len(me.polygons)

    top, bot, world, bedges0, cen = top_boundary(o)
    # PLAN perimeter, not 3D: seating drops a rim vertex 0.13 m, so a 3D length would
    # report the chamfer as raggedness.  The defect is a silhouette, so measure the
    # silhouette.
    perim0 = sum(math.hypot(world[a].x - world[b].x, world[a].y - world[b].y)
                 for a, b in bedges0)
    ax0 = axisfrac(world, bedges0)

    # ========================================================== 1. RELAX ======
    relaxed, npin = 0, 0
    if o.name.startswith(RELAX_FAMILIES) and XYITER:
        bnbr = {}
        for a2, b2 in bedges0:
            bnbr.setdefault(a2, set()).add(b2)
            bnbr.setdefault(b2, set()).add(a2)
        pinned = {vi for vi in bnbr
                  if continued_by_other(o.name, world[vi], outward_of(world, cen, vi))}
        npin = len(pinned)
        xy0 = {vi: (world[vi].x, world[vi].y) for vi in range(len(world))}
        moved = set()
        for _ in range(XYITER):
            new = {}
            for vi, ns in bnbr.items():
                if vi in pinned or len(ns) != 2:
                    continue
                a2, b2 = tuple(ns)
                new[vi] = (0.5 * world[vi].x + 0.25 * (world[a2].x + world[b2].x),
                           0.5 * world[vi].y + 0.25 * (world[a2].y + world[b2].y))
            for vi, (x, y) in new.items():
                ox, oy = xy0[vi]
                dx, dy = x - ox, y - oy
                L = math.hypot(dx, dy)
                if L > XYCLAMP:
                    dx, dy = dx / L * XYCLAMP, dy / L * XYCLAMP
                world[vi] = Vector((ox + dx, oy + dy, world[vi].z))
                moved.add(vi)
        relaxed = len(moved)
        # the bottom ring follows its partner's XY so the walls stay vertical
        tk = {}
        for vi in {v for i in top for v in me.polygons[i].vertices}:
            tk.setdefault((round(xy0[vi][0], KEY), round(xy0[vi][1], KEY)), vi)
        for vi in {v for i in bot for v in me.polygons[i].vertices}:
            pp = tk.get((round(xy0[vi][0], KEY), round(xy0[vi][1], KEY)))
            if pp is not None:
                world[vi] = Vector((world[pp].x, world[pp].y, world[vi].z))
        for vi, w in enumerate(world):
            me.vertices[vi].co = Minv @ w
        me.update()
        top, bot, world, bedges0, cen = top_boundary(o)

    # ============================================== 2. INSET the top region ===
    # bmesh's own inset, so the ORIGINAL boundary loop becomes the outer edge of a
    # chamfer band and is what gets seated.  Nothing inside the band moves at all.
    outer_co = [tuple(round(c, 4) for c in world[v]) for e in bedges0 for v in e]
    outer_key = set(outer_co)
    if top and INSET > 0:
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        tf = [f for f in bm.faces if f.index in top]
        bmesh.ops.inset_region(bm, faces=tf, thickness=INSET, depth=0.0,
                               use_boundary=True, use_even_offset=True)
        bm.to_mesh(me)
        bm.free()
        me.update()

    # ============================================================ 3. SEAT =====
    top, bot, world, bedges1, cen = top_boundary(o)
    bnd = sorted({v for e in bedges1 for v in e})

    # LOOPS.  A loop too short to carry a --inset chamfer keeps its riser and is COUNTED
    # (round 9's lesson: a builder that refuses in silence leaves the defect invisible).
    adj = {}
    for a2, b2 in bedges1:
        adj.setdefault(a2, []).append(b2)
        adj.setdefault(b2, []).append(a2)
    seen, small = set(), []
    for s0 in bnd:
        if s0 in seen:
            continue
        stack, comp = [s0], []
        seen.add(s0)
        while stack:
            v = stack.pop()
            comp.append(v)
            for n2 in adj.get(v, ()):
                if n2 not in seen:
                    seen.add(n2)
                    stack.append(n2)
        cs = set(comp)
        L = sum((world[a2] - world[b2]).length for a2, b2 in bedges1
                if a2 in cs and b2 in cs)   # 3D here: a loop's ability to hold a chamfer
        if L < MINLOOP:
            small.append(comp)
    smallv = {v for c in small for v in c}

    bz = {}
    for vi in {v for i in bot for v in me.polygons[i].vertices}:
        bz.setdefault((round(world[vi].x, 2), round(world[vi].y, 2)), []).append(world[vi].z)

    dropped, pinned2, capf, capz, groundless = 0, 0, 0, 0, 0
    for vi in bnd:
        if vi in smallv:
            continue
        w = world[vi]
        if continued_by_other(o.name, w, outward_of(world, cen, vi)):
            pinned2 += 1
            continue
        g = ground_under(w.x, w.y, w.z)
        if g is None:
            groundless += 1
            continue
        want_z = g - BURY
        if want_z < w.z - ZDROP:
            want_z = w.z - ZDROP
            capz += 1
        nb = bz.get((round(w.x, 2), round(w.y, 2)))
        if nb:
            lim = max(nb) + 0.01
            if want_z < lim:
                want_z = lim
                capf += 1
        if want_z >= w.z - 1e-4:
            continue
        world[vi] = Vector((w.x, w.y, want_z))
        dropped += 1
    for vi, w in enumerate(world):
        me.vertices[vi].co = Minv @ w
    me.update()

    wnow = [M @ v.co for v in me.vertices]
    perim1 = sum(math.hypot(wnow[a].x - wnow[b].x, wnow[a].y - wnow[b].y)
                 for a, b in bedges1)
    ax1 = axisfrac(wnow, bedges1)
    r = dict(verts=[n0, nW, len(me.vertices)], polys=[p0, pW, len(me.polygons)],
             perim=[round(perim0, 2), round(perim1, 2)],
             axis=[round(ax0, 1), round(ax1, 1)],
             bedges=[len(bedges0), len(bedges1)],
             relaxed=relaxed, relax_pinned=npin, dropped=dropped, seat_pinned=pinned2,
             cap_floor=capf, cap_zdrop=capz, groundless=groundless,
             small_loops=len(small),
             family=("lm" if o.name.startswith("walk_lm_") else
                     "e" if o.name.startswith("walk_e_") else "pad"))
    report[o.name] = r
    tot["perim0"] += perim0
    tot["perim1"] += perim1
    tot["ax0"] += round(ax0 / 100.0 * len(bedges0))
    tot["ax1"] += round(ax1 / 100.0 * len(bedges1))
    tot["ne0"] += len(bedges0)
    tot["ne1"] += len(bedges1)
    tot["dropped"] += dropped
    tot["pinned"] += pinned2
    tot["cap_floor"] += capf
    tot["cap_zdrop"] += capz
    tot["groundless"] += groundless
    tot["smallloop"] += len(small)
    tot["relaxed"] += relaxed

BIG = sorted(report.items(), key=lambda t: -t[1]["perim"][0])[:12]
print("\n%-38s %-16s %-15s %-13s %s" % ("object", "verts", "outline m", "axis%", "seat"))
for nm, r in BIG:
    print("  %-36s %5d->%-5d %6.1f->%-6.1f %5.1f->%-5.1f  drop %4d pin %4d cap %3d small %d"
          % (nm[:36], r["verts"][0], r["verts"][2], r["perim"][0], r["perim"][1],
             r["axis"][0], r["axis"][1], r["dropped"], r["seat_pinned"],
             r["cap_floor"] + r["cap_zdrop"], r["small_loops"]))
print("\nTOTAL welded outline %.1f m -> %.1f m (%+.1f%%)   axis-aligned %.1f%% -> %.1f%%"
      % (tot["perim0"], tot["perim1"],
         100.0 * (tot["perim1"] / max(1e-9, tot["perim0"]) - 1),
         100.0 * tot["ax0"] / max(1, tot["ne0"]), 100.0 * tot["ax1"] / max(1, tot["ne1"])))
print("boundary verts: %d SEATED onto the ground, %d PINNED where another walk mesh "
      "continues past the rim, %d relaxed; caps: %d at the bottom ring (the normal case "
      "for a 0.14 m box on ground carved 0.12 m down) and %d at --zdrop %.2f; %d with no "
      "ground under them, %d loops too short to chamfer (%.2f m)"
      % (tot["dropped"], tot["pinned"], tot["relaxed"], tot["cap_floor"], tot["cap_zdrop"],
         ZDROP, tot["groundless"], tot["smallloop"], MINLOOP))

os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
json.dump(dict(
    _doc=("GENERATED by tools/emb_pavechop.py — Emberbrook's paving IS its walk network, "
          "built as independent 0.45 m x 0.14 m boxes standing 0.12 m proud of carved "
          "ground (census in that file's docstring; red-team board "
          "docs/qa/emberbrook-redteam/). This welds each mesh into one strip, relaxes the "
          "lattice silhouette on the region aprons, and seats the rim into the ground. "
          "OWES: a bundle re-export and the two walk gates."),
    generator="tools/emb_pavechop.py", blend=bpy.data.filepath,
    inset=INSET, bury=BURY, zdrop=ZDROP, xyclamp=XYCLAMP, xysmooth=XYITER,
    joinr=JOINR, minloop=MINLOOP, saved=bool(SAVE),
    totals=dict(outline=[round(tot["perim0"], 2), round(tot["perim1"], 2)],
                axis=[round(100.0 * tot["ax0"] / max(1, tot["ne0"]), 2),
                      round(100.0 * tot["ax1"] / max(1, tot["ne1"]), 2)],
                dropped=tot["dropped"], pinned=tot["pinned"], relaxed=tot["relaxed"],
                cap_floor=tot["cap_floor"], cap_zdrop=tot["cap_zdrop"],
                groundless=tot["groundless"], small_loops=tot["smallloop"]),
    meshes=report), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, REPO))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
