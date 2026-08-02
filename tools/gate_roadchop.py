"""gate_roadchop.py — THE ENTRY ROAD: the gate tier stops being a plaza.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_roadchop.py -- [save] [repro] [--dump <dir>] [--report <json>]

    repro          build NOTHING; run section 1 with the PREVIOUS parameters and
                   compare it to the shipped `gate_ground`.  Run this BEFORE the
                   walk graph is re-derived — see "THE FAITHFULNESS GATES".
    --dump <dir>   write the rebuilt meshes to JSON (verts + faces, world space)
                   so the frame can be checked by projection before a bake is spent.
    save           write the master.  Without it the pass is dry.

THE REDLINE.  USER REDLINE #4, 2026-08-02, recorded verbatim on the map's own
`valley-road` landmark: *"what you are currently calling the porter's yard is not
meant to be an occupied space ... It should literally just be the path that leads
the player into the gate of the town ... The path should extend past that bottom
edge, and it should clearly look like a path."*

WHY THE GROUND READ AS A PLAZA, measured before anything was touched.  Project
the shipped `gate_road` mesh through the solved `gate` camera and it covers the
whole bottom-right third of the plate — 2,921 upward-facing quads, a fan ~14 m
long and up to 9 m wide.  That is not a dressing accident.  `gate_build` lays the
carriageway ON THE WALK GRAPH (`road_at` -> `walk_ref`, anything within
ROAD_W + 1.6 of a walk record), and `walk_lm_porters-yard` was an 8 x 8 m filled
disc of walk.  A disc of walk paves a disc of road.  Delete the disc from the map
and THE SAME BUILDER lays a 3.74 m carriageway — the fix is a map edit plus a
re-derive, not new art.

WHAT THIS PASS CARRIES, i.e. the consumers of the three lists that changed:

  1. `gate_ground`  — `Terrain.rim()`'s first control points (12.46/12.10 ->
     9.20/9.05, REDLINE #3's own derived blue line) and `GX0` (1.20 -> -3.20, so
     the road crosses the frame's bottom edge with ground under it).  Rebuilt
     from gate_build's OWN section-1 lattice, then re-refined over the west lobe
     with t2_cliff_res's own refine() at its own numbers (0.50 m target edge,
     30 mm displacement, cuts PINNED to 1 — see gate_rimchop.py for why the cut
     count is pinned rather than re-derived).
  2. `gate_road`    — gate_build's OWN section 2, verbatim.  This is the object
     the redline is actually about, and it is the one `gate_rimchop.py` did not
     rebuild; that is the whole reason this file exists beside it.
  3. `gate_parapet` — gate_build's OWN section-7 search, verbatim, including the
     t2c_ prop refusal (nearest-point on a BVH of the prop's real triangles, NOT
     its bbox: a bbox refused 13 of 23 posts once, because a string of pennants
     has a diagonal envelope 12 m wide).  Placed off `T.rim`, so the rail follows
     the new lip and ends up at the road's shoulder instead of 4 m out on apron.
  4. THE CULL — everything seated on ground the new lip no longer carries, tested
     DIFFERENTIALLY (`has_ground` under the OLD lip AND NOT under the new one).
     Never "is there ground under this now": that test deleted 24 of gate_winch's
     44 components at columns where the rim never moved, because the winch head
     overhangs on purpose.
  5. THE YARD ITSELF — `gate_yard`'s components west of the palisade (x < 15.2)
     are removed by NAME OF THE RULE, not by the differential test, because most
     of them stand on the cliff side where the rim never reached: the porters'
     shed, the mule lines, the water trough and the tarpaulin lean-to are the
     "porter's yard or anything like that at this entry scene" the redline says
     to take out.  East of the palisade is inside the town and is left alone.
  6. THE RE-SEAT — rim vegetation cloned onto the new lip off `T.rim`, exactly as
     `clone(mode="rim")` does it.  A cull without a re-seat is half an edit: the
     first rim pass shipped a bare timber fence over raw rock where the frame had
     carried an autumn crown line, and that was found by LOOKING at the draft.

`gate_build.py` IS STILL UNRUNNABLE against the live master and this file does not
change that: it rebuilds 36 objects where the master carries 147, losing all 111
`veg_gate_*` meshes (they clone from bare-named kit sources that live only in a
now-deleted branch blend) and undoing `t2_cliff_res`'s west-lobe refinement.  See
gate_rimchop.py's docstring for the object-by-object diff that established it.

THE FAITHFULNESS GATES, and the one that had to change shape.

  `gate_rimchop.py` could prove its copy of section 1 by rebuilding with the
  PRE-CHOP control points and comparing to the shipped mesh, because the only
  thing it changed was the rim.  This pass also changes the WALK GRAPH (the yard
  disc is deleted from the map and re-derived out of the master), and section 1
  reads the walk graph.  So the reproduction check cannot be run after the
  re-derive — the "old parameters" build would be against a walk set that no
  longer matches the shipped ground.

  It is therefore split, and `repro` is the first half:

    repro (run BEFORE walk_rederive):  old rim + old GX0 + no spine clamp, against
      the master's own walk graph, compared to the shipped `gate_ground` snapshot.
      This is the claim "this copy of section 1 still reproduces the shipped base
      ground on today's master", and it is the same claim gate_rimchop gate (a)
      made.  It is written to districts/gate_roadchop_repro.json.

    the live pass:  reports (b) the ground EAST of the edit — x >= 16.0 is clear
      of the moved rim (last moved control point 10.6), clear of the deleted
      yard disc's 9.4 m clamp reach, and clear of the spine — where the rebuild
      must be identical to the shipped mesh, and it is asserted; and (c) a
      per-band table of max |dz| west of that, printed whether it passes or not,
      because west of x=16 the ground is SUPPOSED to move and a number that hides
      that would be a number fitted to the gate.

REVERT: tools/blends/districts/gate_roadchop_backup.json holds the pre-pass
`gate_ground` / `gate_road` / `gate_parapet` meshes; `-- revert save` restores
them.  Written ONCE, never overwritten.  Culled objects are recorded for
archaeology but are NOT restored by that path (the master is git-tracked).
"""
import bpy, bmesh, math, os, sys, json, random
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
sys.path.insert(0, REPO + "/tools")
from boatyard_lib import (new_mesh, join_meshes, obox, beam, cyl, link, coll, M,
                          world_bbox, point_in_poly, dist_poly2)
import gate_lib
from gate_lib import (Terrain, over_walk, GX0, GX1, GY0, GY1, SHELF, PLATE_BOT,
                      BASEZ, SOLID_X, HIGH_Z, DECK_DROP, CORRIDOR_H)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv
REPRO = "repro" in argv
DUMP = argv[argv.index("--dump") + 1] if "--dump" in argv else None
REPORT = argv[argv.index("--report") + 1] if "--report" in argv else None
BACKUP = REPO + "/tools/blends/districts/gate_roadchop_backup.json"
MANIFEST = REPO + "/tools/blends/districts/gate_roadchop.json"
COLL = "GATE_DISTRICT"

# THE PREVIOUS PARAMETERS, kept here as DATA for the faithfulness gates only.
# gate_lib is the single authority for what ships; nothing built from these lists
# is ever saved.
RIM_PREV = [(1.2, 12.46), (9.5, 12.46), (10.6, 12.10), (11.5, 9.60),
            (13.0, 8.40), (16.0, 7.10), (19.0, 8.60), (22.0, 9.50),
            (25.0, 10.05), (26.8, 10.25), (27.6, 9.95), (30.2, 9.95), (31.9, 10.40)]
GX0_PREV = 1.20
ROAD_W = 1.42
GROUND_DROP = 0.36


def rim_of(P):
    def f(self, x):
        if x <= P[0][0]:
            return P[0][1]
        for i in range(len(P) - 1):
            (x0, y0), (x1, y1) = P[i], P[i + 1]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0)
                return y0 + (y1 - y0) * (t * t * (3 - 2 * t))
        return P[-1][1]
    return f


RIM_SHIPPED = Terrain.rim


def snapshot(ob):
    me = ob.data
    return dict(verts=[[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)]
                       for v in me.vertices],
                polys=[list(p.vertices) for p in me.polygons],
                mati=[p.material_index for p in me.polygons],
                smooth=[bool(p.use_smooth) for p in me.polygons],
                materials=[m.name if m else None for m in me.materials])


def restore_mesh(ob, snap):
    me = ob.data
    me.clear_geometry()
    me.from_pydata([tuple(v) for v in snap["verts"]], [], [tuple(p) for p in snap["polys"]])
    me.validate()
    me.materials.clear()
    for mn in snap["materials"]:
        me.materials.append(bpy.data.materials.get(mn) if mn else None)
    for p, mi, sm in zip(me.polygons, snap["mati"], snap["smooth"]):
        p.material_index, p.use_smooth = mi, sm
    me.update()


# ============================================================== REVERT ========
if REVERT:
    assert os.path.exists(BACKUP), "no backup at %s" % BACKUP
    B = json.load(open(BACKUP))
    for name, snap in B["meshes"].items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            print("  %s is gone — cannot restore" % name)
            continue
        restore_mesh(ob, snap)
        print("RESTORED %-18s %5d verts %5d polys" % (name, len(snap["verts"]), len(snap["polys"])))
    print("NOTE: culled objects are NOT restored by this path (%d were removed); "
          "the master is git-tracked." % len(B.get("culled", [])))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED", bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

print("=" * 84)
print("GATE ROAD CHOP — the entry road (user redline #4: the gate scene is a ROAD)")
print("=" * 84)

T = Terrain()
COR0, COR, KEEP = T.cor0, T.cor, T.keep
MROCK = M("mat_rock")
MTURF = M("mat_gate_turf")
MSTONE = M("mat_gate_stone")
MROAD = M("mat_gate_road")
MT, MROPE = M("mat_timber"), M("mat_rope")
for nm, m in (("mat_rock", MROCK), ("mat_gate_turf", MTURF), ("mat_gate_stone", MSTONE),
              ("mat_gate_road", MROAD), ("mat_timber", MT), ("mat_rope", MROPE)):
    assert m is not None, "material %s is missing from this blend" % nm

GROUND = bpy.data.objects.get("gate_ground")
ROADOB = bpy.data.objects.get("gate_road")
PARAPET = bpy.data.objects.get("gate_parapet")
for nm, ob in (("gate_ground", GROUND), ("gate_road", ROADOB), ("gate_parapet", PARAPET)):
    assert ob is not None, "%s missing from this blend" % nm
    assert ob.matrix_world.to_translation().length < 1e-6, (
        "%s has a non-identity transform — this pass builds in world coords" % nm)

print("\nTHE LIP, per metre (previous -> shipped):")
row_x, row_o, row_n = [], [], []
for x in range(-3, 31, 1):
    row_x.append("%6d" % x)
    row_o.append("%6.2f" % rim_of(RIM_PREV)(T, x))
    row_n.append("%6.2f" % RIM_SHIPPED(T, x))
print("  x    " + "".join(row_x))
print("  prev " + "".join(row_o))
print("  new  " + "".join(row_n))
print("\nTHE SPINE (the carriageway past the map's last landmark): %s  z %.2f..%.2f"
      % (gate_lib.SPINE, gate_lib.spine_top(gate_lib.SPINE[0][0]),
         gate_lib.spine_top(gate_lib.SPINE[-1][0])))

# =========================================================================
# SECTION 1 — the ground lattice, copied from gate_build.py (with the spine clamp
# that gate_build.py now also carries: gate_lib is the one authority for the spine)
# =========================================================================
ST = 0.34


def make_ground_top(use_spine):
    def ground_top(x, y):
        h = T.natural(x, y)
        for raw, fn, zt, nm in T.high:
            d = dist_poly2(x, y, raw)
            if d < 5.4:
                h = min(h, T.plane_at(raw, fn, x, y, d) - GROUND_DROP
                        + max(0.0, d - (ROAD_W + 0.50)) * 1.15)
        if use_spine:
            ds = gate_lib.spine_d(x, y)
            if ds < 5.4:
                h = min(h, gate_lib.spine_top(x) - GROUND_DROP
                        + max(0.0, ds - (ROAD_W + 0.50)) * 1.15)
        for raw, fn, zt, nm in T.low:
            if x > SOLID_X:
                break
            d = dist_poly2(x, y, raw)
            if d >= 2.2:
                continue
            top = COR0.top_at(x, y)
            if top is not None and top > zt + 0.05:
                continue
            lo = zt + d * 1.15 - GROUND_DROP
            if lo < h < zt + CORRIDOR_H + d * 0.6:
                h = lo
        over = y - T.rim(x)
        if over > 0.0 and x <= SOLID_X + 0.80:
            h -= 30.0 * (over ** 1.30)
        return max(h, BASEZ)
    return ground_top


ground_top = make_ground_top(True)


def build_ground(gx0, top_fn):
    """gate_build.py section 1. Returns (NODE, V, F, MI)."""
    nx = int(round((GX1 - gx0) / ST)) + 1
    ny = int(round((GY1 - GY0) / ST)) + 1
    NODE = {}
    for i in range(nx):
        for j in range(ny):
            x, y = gx0 + i * ST, GY0 + j * ST
            if not T.has_ground(x, y):
                continue
            t = top_fn(x, y)
            NODE[(i, j)] = (x, y, t, T.bottom(x, y, t))
    V, F, MI = [], [], []
    topi, boti = {}, {}
    for k, (x, y, t, b) in NODE.items():
        topi[k] = len(V); V.append((x, y, t))
        boti[k] = len(V); V.append((x, y, b))

    def cell(i, j):
        return all((i + a, j + c) in NODE for a, c in ((0, 0), (1, 0), (1, 1), (0, 1)))

    for i in range(nx - 1):
        for j in range(ny - 1):
            if not cell(i, j):
                continue
            a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
            F.append((topi[a], topi[b], topi[c], topi[d]))
            zs = [NODE[k][2] for k in (a, b, c, d)]
            rise = max(zs) - min(zs)
            MI.append(1 if (rise < 0.34 and min(zs) > 21.0) else 0)
            F.append((boti[d], boti[c], boti[b], boti[a])); MI.append(0)
            for (na, nb, oi, oj) in ((a, d, -1, 0), (b, c, 1, 0), (a, b, 0, -1), (d, c, 0, 1)):
                if cell(i + oi, j + oj):
                    continue
                F.append((topi[na], topi[nb], boti[nb], boti[na])); MI.append(0)
    return NODE, V, F, MI


def top_columns(verts):
    d = {}
    for v in verts:
        k = (round(v[0], 2), round(v[1], 2))
        d[k] = max(d.get(k, -1e9), v[2])
    return d


def noise3(p, f, s):
    return (math.sin(p.x * f + p.y * f * 1.7 + s) *
            math.cos(p.y * f * 0.9 - p.z * f * 1.3 + s * 2.1) *
            math.sin(p.z * f * 1.4 + p.x * f * 0.6 - s))


def mean_edge(m):
    if not m.edges:
        return 0.0
    return sum((m.vertices[e.vertices[0]].co - m.vertices[e.vertices[1]].co).length
               for e in m.edges) / len(m.edges)


def refine(ob, want_edge, disp, region, pin_cuts=None):
    """t2_cliff_res.py's refine, with `cuts` PINNED — see gate_rimchop.py for why
    re-deriving the cut count off the CURRENT mean edge doubles the town's ground
    budget as a side effect of a rim edit."""
    m = ob.data
    before = (len(m.vertices), len(m.polygons), mean_edge(m))
    bm = bmesh.new(); bm.from_mesh(m)
    sel = [f for f in bm.faces if region[0] <= f.calc_center_median().x <= region[1]]
    cuts = pin_cuts if pin_cuts is not None else max(1, int(math.ceil(before[2] / want_edge)) - 1)
    edges = list({e for f in sel for e in f.edges})
    if edges and cuts >= 1:
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True)
    bm.normal_update()
    mv = 0
    for v in bm.verts:
        if not (region[0] <= v.co.x <= region[1]):
            continue
        n = v.normal
        if n.length < 1e-6:
            continue
        v.co += n.normalized() * (disp * noise3(v.co, 0.9, 1.7))
        mv += 1
    bm.to_mesh(m); bm.free(); m.update()
    after = (len(m.vertices), len(m.polygons), mean_edge(m))
    print("REFINED gate_ground   %5d -> %-6d verts   edge %.2f -> %.2f m   %d cuts, "
          "%d verts displaced by <= %.0f mm"
          % (before[0], after[0], before[2], after[2], cuts, mv, disp * 1000))
    return dict(before=dict(verts=before[0], polys=before[1], edge=round(before[2], 3)),
                after=dict(verts=after[0], polys=after[1], edge=round(after[2], 3)),
                cuts=cuts, displaced_m=disp, verts_moved=mv, region_x=list(region))


# --------------------------------------------------------------------- repro ---
if REPRO:
    # THE PREVIOUS PARAMETERS, against the master's own (still-unchanged) walk graph.
    Terrain.rim = rim_of(RIM_PREV)
    T._ylo = {}
    NODE_P, V_P, F_P, MI_P = build_ground(GX0_PREV, make_ground_top(False))
    Terrain.rim = RIM_SHIPPED
    T._ylo = {}
    # THE REFERENCE IS THE LIVE `gate_ground`, NOT a historical snapshot.  The
    # obvious reference — districts/t2_cliff_res_backup.json, which gate_rimchop's
    # gate (a) used — is the PRE-CHOP ground, and gate_rimchop has since moved the
    # rim; measured against it this rebuild reports 307 missing columns and 32 m of
    # dz, which is the chop, not a defect.  So the claim is made against what is
    # actually in the blend, refinement included: build at the previous parameters,
    # apply the same pinned refine over the previous lobe, and the vertex SETS must
    # be identical.
    tmp_me = bpy.data.meshes.new("gate_ground_repro")
    tmp_me.from_pydata(V_P, [], F_P)
    tmp_me.validate()
    # RECALC BEFORE REFINE, exactly as the live path does.  `refine` displaces along
    # VERTEX NORMALS, so a mesh whose face winding has not been made consistent
    # displaces 330 of its 13,127 verts the other way — which is what the first cut
    # of this gate measured and mistook for nondeterminism.
    _bm = bmesh.new(); _bm.from_mesh(tmp_me)
    bmesh.ops.recalc_face_normals(_bm, faces=_bm.faces)
    _bm.to_mesh(tmp_me); _bm.free()
    tmp_ob = bpy.data.objects.new("gate_ground_repro", tmp_me)
    bpy.context.scene.collection.objects.link(tmp_ob)
    refine(tmp_ob, 0.50, 0.030, (GX0_PREV - 0.2, 15.0), pin_cuts=1)
    got = {(round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4)) for v in tmp_ob.data.vertices}
    want = {(round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4)) for v in GROUND.data.vertices}
    bpy.data.objects.remove(tmp_ob, do_unlink=True)
    ts, tg = top_columns([list(v) for v in want]), top_columns([list(v) for v in got])
    both = sorted(set(ts) & set(tg))
    dz = sorted(((abs(ts[k] - tg[k]), k) for k in both), reverse=True)
    rep = dict(shipped_verts=len(want), rebuilt_verts=len(got),
               identical_verts=len(want & got),
               only_shipped=len(want - got), only_rebuilt=len(got - want),
               top_columns_both=len(both),
               max_dz=round(dz[0][0], 6) if dz else 0.0,
               over_1mm=sum(1 for d_, _ in dz if d_ > 0.001),
               columns_only_shipped=len(set(ts) - set(tg)),
               columns_only_rebuilt=len(set(tg) - set(ts)))
    print("\nREPRO — section 1 + the pinned refine at the PREVIOUS parameters, "
          "vs the LIVE gate_ground")
    print("  %d shipped verts / %d rebuilt; %d identical, %d only-shipped, %d only-rebuilt"
          % (rep["shipped_verts"], rep["rebuilt_verts"], rep["identical_verts"],
             rep["only_shipped"], rep["only_rebuilt"]))
    print("  top surface: %d shared columns, max |dz| = %.6f m, %d over 1 mm; "
          "columns in only one: %d shipped-only / %d rebuilt-only"
          % (rep["top_columns_both"], rep["max_dz"], rep["over_1mm"],
             rep["columns_only_shipped"], rep["columns_only_rebuilt"]))
    out = REPO + "/tools/blends/districts/gate_roadchop_repro.json"
    json.dump(dict(_doc="gate_roadchop.py `repro`: this copy of gate_build section 1, "
                        "run at the PREVIOUS rim/GX0/no-spine parameters against the "
                        "master's walk graph, versus the shipped pre-refine gate_ground.",
                   **rep), open(out, "w"), indent=1)
    print("  -> %s" % os.path.relpath(out, REPO))
    assert rep["max_dz"] < 1e-4 and rep["columns_only_shipped"] == 0 and \
        rep["columns_only_rebuilt"] == 0, "REPRO FAILED — this copy of section 1 does " \
        "not reproduce the shipped ground; do not build from it"
    print("  REPRO OK")
    sys.exit(0)

# --------------------------------------------------------------- the live pass --
NODE_PREV_PARAMS = None
Terrain.rim = rim_of(RIM_PREV)
T._ylo = {}
NODE_P, V_P, F_P, MI_P = build_ground(GX0_PREV, make_ground_top(False))
Terrain.rim = RIM_SHIPPED
T._ylo = {}
NODE_N, V_N, F_N, MI_N = build_ground(GX0, ground_top)
print("\nSECTION 1   prev-params %d nodes / %d faces   ->   shipped %d nodes / %d faces"
      % (len(NODE_P), len(F_P), len(NODE_N), len(F_N)))

# gate (b) + (c), band by band.  THE REFERENCE IS THE PREV-PARAMETER LATTICE, not
# the shipped mesh, and that is not a softening: the shipped mesh has been REFINED
# (subdivided one cut, displaced 30 mm along its normals), so its vertices do not
# sit on the 0.34 m lattice at all and a column-for-column comparison against it
# shares ZERO columns and measures nothing.  `repro` is what ties the prev-parameter
# lattice to the shipped mesh — bit-exact, refinement included — so the chain
# shipped == prev-params == (this table) == new is complete across the two runs.
SHIPPED_TOPS = top_columns(V_P)
NEW_TOPS = top_columns(V_N)
BANDS = [(-3.3, 1.2), (1.2, 4.0), (4.0, 8.0), (8.0, 12.0), (12.0, 16.0),
         (16.0, 22.0), (22.0, 29.6)]
band_rows = []
for x0, x1 in BANDS:
    ks = [k for k in NEW_TOPS if x0 <= k[0] < x1]
    both = [k for k in ks if k in SHIPPED_TOPS]
    d = [abs(NEW_TOPS[k] - SHIPPED_TOPS[k]) for k in both]
    only_new = len(ks) - len(both)
    only_old = len([k for k in SHIPPED_TOPS if x0 <= k[0] < x1 and k not in NEW_TOPS])
    band_rows.append(dict(x0=x0, x1=x1, columns=len(ks), shared=len(both),
                          max_dz=round(max(d), 4) if d else 0.0,
                          over_10mm=sum(1 for v in d if v > 0.010),
                          gained=only_new, lost=only_old))
print("\nGROUND vs THE PREV-PARAMETER LATTICE, by x band (top surface, same (x,y) column):")
print("  %-14s %8s %8s %10s %10s %8s %8s" % ("x band", "columns", "shared", "max|dz|",
                                             ">10mm", "gained", "lost"))
for r in band_rows:
    print("  %5.1f..%-7.1f %8d %8d %10.4f %10d %8d %8d"
          % (r["x0"], r["x1"], r["columns"], r["shared"], r["max_dz"],
             r["over_10mm"], r["gained"], r["lost"]))
east = [r for r in band_rows if r["x0"] >= 16.0]
# WHAT THE GATE CAN HONESTLY CLAIM EAST OF x=16.  Not "identical": the WALK GRAPH
# changed too (the yard disc is gone and the road edge has new waypoints), and
# `Terrain.ylo` — the eastern gallery plate's south edge — is DERIVED from the walk
# graph, so a handful of columns near the arch legitimately stop existing.  What the
# rim/GX0/spine edit must not do east of its own reach is MOVE a surviving column or
# CREATE one, and that is what is asserted; every lost column is printed with its
# position so "a handful" is a number somebody can look at rather than a word.
lost_east = sorted(k for k in SHIPPED_TOPS if k[0] >= 16.0 and k not in NEW_TOPS)
assert all(r["max_dz"] < 1e-4 and r["gained"] == 0 for r in east), (
    "the edit MOVED or CREATED ground east of x=16, which is clear of the moved rim "
    "(last control point 10.6) and of the spine: %s" % east)
assert all(r["lost"] == 0 for r in band_rows if r["x0"] >= 22.0), (
    "columns lost east of x=22, past every walk record the map edit touched: %s"
    % [r for r in band_rows if r["x0"] >= 22.0])
print("  GATE: east of x=16 nothing moved (max |dz| 0) and nothing was created; %d "
      "column(s) stopped existing, all from Terrain.ylo following the new walk graph:"
      % len(lost_east))
for k in lost_east:
    print("        lost (%6.2f, %6.2f)  ylo=%.2f" % (k[0], k[1], T.ylo(k[0])))

# --- write the new ground -----------------------------------------------------
BK = {"meshes": {}, "culled": []}
if not os.path.exists(BACKUP):
    for nm, ob in (("gate_ground", GROUND), ("gate_road", ROADOB), ("gate_parapet", PARAPET)):
        BK["meshes"][nm] = snapshot(ob)

g_before = (len(GROUND.data.vertices), len(GROUND.data.polygons))
me = bpy.data.meshes.new("gate_ground_tmp")
me.from_pydata(V_N, [], F_N)
me.validate()
for m in (MROCK, MTURF):
    me.materials.append(m)
for p, mi in zip(me.polygons, MI_N):
    p.material_index = mi
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
old_me = GROUND.data
GROUND.data = me
bpy.data.meshes.remove(old_me)
me.name = "gate_ground"

# --- t2_cliff_res's west-lobe refinement, at ITS OWN numbers -------------------
# The lobe's west end follows GX0: the newly-extended sheet is the part of this
# ground the gate camera stands nearest to, so it is exactly the part that must
# not read as a 0.9 m lattice.
GATE_LOBE = (GX0 - 0.2, 15.0)


REFREP = refine(GROUND, 0.50, 0.030, GATE_LOBE, pin_cuts=1)
g_after = (len(GROUND.data.vertices), len(GROUND.data.polygons))
print("gate_ground   %d verts / %d polys  ->  %d / %d"
      % (g_before[0], g_before[1], g_after[0], g_after[1]))

# =========================================================================
# SECTION 2 — THE CARRIAGEWAY, copied verbatim from gate_build.py
# =========================================================================
def walk_ref(x, y):
    """gate_build's own: (surface z, plan distance) of the nearest tier walk."""
    inside = None
    for raw, fn, zt, nm in T.high:
        if point_in_poly(x, y, raw):
            inside = fn(x, y) if inside is None else max(inside, fn(x, y))
    if inside is not None:
        return inside, 0.0
    best, bz = 1e9, None
    for raw, fn, zt, nm in T.high:
        d = dist_poly2(x, y, raw)
        if d < best:
            best, bz = d, T.plane_at(raw, fn, x, y, d)
    return bz, best


def road_at(x, y):
    z, d = walk_ref(x, y)
    if d < ROAD_W + 1.6:
        return z - DECK_DROP, d
    ds = gate_lib.spine_d(x, y)
    if ds < 2.55:
        return gate_lib.spine_top(x) - DECK_DROP, ds
    return None


def road_blocked(x, y, ztop):
    for raw, fn, zt, nm in T.low:
        if zt >= ztop - 0.10 or zt < ztop - GROUND_DROP - CORRIDOR_H:
            continue
        if dist_poly2(x, y, raw) < 0.02:
            top = COR0.top_at(x, y)
            if top is not None and top > zt + 0.05:
                continue
            return True
    return False


RST = 0.26
RNX = int(round((GX1 - GX0) / RST)) + 1
RNY = int(round((GY1 - GY0) / RST)) + 1
RN = {}
for i in range(RNX):
    for j in range(RNY):
        x, y = GX0 + i * RST, GY0 + j * RST
        r = road_at(x, y)
        if r is None:
            continue
        z, d = r
        if d > ROAD_W + 0.45:
            continue
        if road_blocked(x, y, z):
            continue
        crown = -0.030 * (d / max(ROAD_W, 0.1)) ** 2
        rut = -0.026 * math.exp(-((d - 0.62) / 0.26) ** 2) - 0.026 * math.exp(-((d - 1.10) / 0.26) ** 2)
        n = (math.sin(x * 2.9 + y * 1.7) * 0.5 + math.sin(x * 6.1 - y * 4.3) * 0.3) * 0.018
        zz = z + crown + rut + n
        for raw, fn, zt, nm in T.high:
            dd = dist_poly2(x, y, raw)
            if dd < 0.95:
                zz = min(zz, T.plane_at(raw, fn, x, y, dd) - DECK_DROP)
        RN[(i, j)] = (x, y, zz)

RV, RF = [], []
rt, rb = {}, {}
for k, (x, y, z) in RN.items():
    rt[k] = len(RV); RV.append((x, y, z))
    rb[k] = len(RV); RV.append((x, y, z - GROUND_DROP))


def rcell(i, j):
    return all((i + a, j + c) in RN for a, c in ((0, 0), (1, 0), (1, 1), (0, 1)))


for i in range(RNX - 1):
    for j in range(RNY - 1):
        if not rcell(i, j):
            continue
        a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
        RF.append((rt[a], rt[b], rt[c], rt[d]))
        RF.append((rb[d], rb[c], rb[b], rb[a]))
        for (na, nb, oi, oj) in ((a, d, -1, 0), (b, c, 1, 0), (a, b, 0, -1), (d, c, 0, 1)):
            if not rcell(i + oi, j + oj):
                RF.append((rt[na], rt[nb], rb[nb], rb[na]))

r_before = (len(ROADOB.data.vertices), len(ROADOB.data.polygons))
rme = bpy.data.meshes.new("gate_road_tmp")
rme.from_pydata(RV, [], RF)
rme.validate()
rme.materials.append(MROAD)
bm = bmesh.new(); bm.from_mesh(rme)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(rme); bm.free()
old_rme = ROADOB.data
ROADOB.data = rme
bpy.data.meshes.remove(old_rme)
rme.name = "gate_road"
r_after = (len(ROADOB.data.vertices), len(ROADOB.data.polygons))

# THE MEASUREMENT THE REDLINE IS ABOUT: how wide is the carriageway, per metre.
print("\ngate_road   %d nodes   %d verts / %d polys  ->  %d / %d"
      % (len(RN), r_before[0], r_before[1], r_after[0], r_after[1]))
wid = {}
for (x, y, z) in RN.values():
    k = round(x)
    lo, hi = wid.get(k, (1e9, -1e9))
    wid[k] = (min(lo, y), max(hi, y))
widths = [(k, hi - lo, lo, hi) for k, (lo, hi) in sorted(wid.items())]
print("CARRIAGEWAY WIDTH, per metre of x  (a road is ~3.7 m; a plaza is not):")
for k, w, lo, hi in widths:
    print("   x %5d   %5.2f m wide   y %5.2f .. %5.2f  %s"
          % (k, w, lo, hi, "#" * int(round(w * 2))))
wmax = max(w for _, w, _, _ in widths)
print("   widest: %.2f m" % wmax)

# =========================================================================
# SECTION 7 — the parapet search, copied verbatim from gate_build.py
# =========================================================================
from mathutils.bvhtree import BVHTree
_dg = bpy.context.evaluated_depsgraph_get()
T2C = []
for _o in bpy.data.objects:
    if _o.type == 'MESH' and _o.name.startswith("t2c_") and len(_o.data.vertices):
        try:
            T2C.append((_o.name, BVHTree.FromObject(_o, _dg)))
        except Exception:
            pass


def in_prop(x, y, z0, z1, pad=0.22):
    """A BBOX IS NOT A FOOTPRINT (gate_rimchop.py, 13 of 23 posts refused by a
    string of pennants' diagonal envelope). Nearest point on the prop's own
    triangles, sampled up the post's axis."""
    for nm, bvh in T2C:
        for k in range(5):
            p = Vector((x, y, z0 + (z1 - z0) * k / 4.0))
            loc, nrm, idx, d = bvh.find_nearest(p, pad)
            if loc is not None:
                return nm
    return None


parts, posts = [], []
skipped_prop = []
x = GX0 + 0.50
last = None
while x < 29.4:
    yr = T.rim(x)
    y = yr - 0.55
    z = ground_top(x, y)
    tries = 0
    while over_walk(COR, x, y, z + 0.55, pad=0.24) and tries < 26:
        y += 0.12
        z = ground_top(x, y)
        tries += 1
    if tries >= 26 or not T.has_ground(x, y):
        x += 0.95
        last = None
        continue
    if 25.9 < x < 29.2:
        x += 0.95
        last = None
        continue
    hit = in_prop(x, y, z, z + 1.22)
    if hit is not None:
        skipped_prop.append(dict(x=round(x, 2), y=round(y, 2), prop=hit))
        x += 0.95
        last = None
        continue
    p = Vector((x, y, z))
    posts.append(p)
    parts.append(obox("pp", x, y, z + 0.52, 0.19, 0.19, 1.16, mat=MT, cname=COLL))
    parts.append(obox("pc", x, y, z + 1.13, 0.27, 0.27, 0.09, mat=MT, cname=COLL))
    if last is not None and (p - last).length < 2.4:
        for zr, sag in ((1.00, 0.10), (0.58, 0.06)):
            mid = (last + p) / 2 + Vector((0, 0, zr - sag))
            parts.append(cyl("hl", last + Vector((0, 0, zr)), mid, 0.028, 5, MROPE, COLL))
            parts.append(cyl("hl", mid, p + Vector((0, 0, zr)), 0.028, 5, MROPE, COLL))
        c = (last + p) / 2
        parts.append(obox("kb", c.x, c.y, c.z + 0.20, (p - last).length + 0.24, 0.40, 0.44,
                          rz=math.atan2(p.y - last.y, p.x - last.x), mat=MSTONE, cname=COLL))
    last = p
    x += 0.95

p_before = (len(PARAPET.data.vertices), len(PARAPET.data.polygons))
tmp = join_meshes(parts, "gate_parapet_tmp", COLL)
assert tmp is not None, "the parapet search found nothing to build"
old_pm = PARAPET.data
PARAPET.data = tmp.data
bpy.data.objects.remove(tmp, do_unlink=True)
bpy.data.meshes.remove(old_pm)
PARAPET.data.name = "gate_parapet"
p_after = (len(PARAPET.data.vertices), len(PARAPET.data.polygons))
print("\ngate_parapet  %d posts   %d verts / %d polys  ->  %d / %d"
      % (len(posts), p_before[0], p_before[1], p_after[0], p_after[1]))
for s_ in skipped_prop:
    print("   post at (%6.2f,%6.2f) REFUSED — would stand inside %s"
          % (s_["x"], s_["y"], s_["prop"]))

# =========================================================================
# THE CULL — differential, never "is there ground under this now"
# =========================================================================
TIER_CEIL = 30.0
rprev, rnew = rim_of(RIM_PREV), RIM_SHIPPED


def stranded(cx, cy, base):
    """True iff the PREVIOUS lip carried this footprint and the new one does not."""
    if base > TIER_CEIL:
        return False
    Terrain.rim = rprev; T._ylo = {}
    was = T.has_ground(cx, cy)
    Terrain.rim = RIM_SHIPPED; T._ylo = {}
    return was and not T.has_ground(cx, cy)


culled, kept = [], 0
for ob in list(bpy.data.objects):
    if ob.type != 'MESH' or not ob.name.startswith("veg_gate_"):
        continue
    b = world_bbox(ob)
    cx, cy, base = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, b[4]
    if not stranded(cx, cy, base):
        kept += 1
        continue
    culled.append(dict(name=ob.name, x=round(cx, 3), y=round(cy, 3), z=round(base, 3),
                       rim_old=round(rprev(T, cx), 3), rim_new=round(rnew(T, cx), 3),
                       why="the previous lip carried this footprint, the new one does not"))
    bpy.data.objects.remove(ob, do_unlink=True)
print("\nVEGETATION   %d veg_gate_* kept, %d culled (stranded past the new lip)"
      % (kept, len(culled)))
for c in culled[:40]:
    print("   CULL %-28s at (%6.2f,%6.2f)  rim %5.2f -> %5.2f"
          % (c["name"], c["x"], c["y"], c["rim_old"], c["rim_new"]))

# THE YARD ITSELF.  Not a differential test — a named rule, because most of these
# stand on the CLIFF side where the rim never reached, and the redline is about
# what the entry scene contains, not about what fell off the edge.
YARD_CUT_X = 15.20        # the palisade: west of it is outside the gate


def cull_components(name, extra=None, extra_why=""):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return None
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            w = stack.pop()
            comp.append(w)
            for e in w.link_edges:
                o = e.other_vert(w)
                if o.index not in seen:
                    seen.add(o.index); stack.append(o)
        comps.append(comp)
    drop, keptc, rows = [], 0, []
    for comp in comps:
        cx = sum(w.co.x for w in comp) / len(comp)
        cy = sum(w.co.y for w in comp) / len(comp)
        cz = min(w.co.z for w in comp)
        why = None
        if stranded(cx, cy, cz):
            why = "stranded past the new lip"
        elif extra is not None and extra(cx, cy, cz):
            why = extra_why
        if why is None:
            keptc += 1
            continue
        drop.extend(comp)
        rows.append(dict(x=round(cx, 3), y=round(cy, 3), z=round(cz, 3), verts=len(comp),
                         rim_old=round(rprev(T, cx), 3), rim_new=round(rnew(T, cx), 3),
                         why=why))
    nb = len(bm.verts)
    if drop:
        bmesh.ops.delete(bm, geom=drop, context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    print("%-14s %d components: %d kept, %d cut (%d -> %d verts)"
          % (name, len(comps), keptc, len(rows), nb, len(ob.data.vertices)))
    for r in rows[:30]:
        print("   CUT  piece at (%6.2f,%6.2f) %3d verts  — %s" % (r["x"], r["y"], r["verts"], r["why"]))
    return dict(components=len(comps), kept=keptc, cut=rows,
                verts_before=nb, verts_after=len(ob.data.vertices))


print()
COMP = {}
COMP["gate_yard"] = cull_components(
    "gate_yard", extra=lambda cx, cy, cz: cx < YARD_CUT_X,
    extra_why="THE YARD: west of the palisade (x<%.1f) is the entry road, and user "
              "redline #4 says there is no porters' yard on it" % YARD_CUT_X)
for nm in ("gate_clutter", "gate_bunting", "gate_winch", "gate_road_dress"):
    r = cull_components(nm)
    if r:
        COMP[nm] = r

# =========================================================================
# THE RE-SEAT — rim vegetation on the new lip
# =========================================================================
RESEED_TAGS = [
    ("clump", "veg_gate_rimclump_", 22, (10.6, 26.0), 0.75, 1.15, True),
    ("tuft",  "veg_gate_tuft_",     70, (GX0 + 0.5, 27.5), 0.85, 1.25, True),
    ("fern",  "veg_gate_fern_",     24, (GX0 + 0.5, 26.0), 0.85, 1.15, True),
]
SOLIDS = [(2.90, 9.10, -0.25, 3.25), (0.40, 5.10, 2.30, 5.45),
          (9.15, 14.00, -0.60, 4.90), (14.60, 15.75, 2.85, 9.00),
          (15.80, 17.55, 0.80, 7.20), (16.05, 17.20, -0.60, 10.70),
          (25.45, 29.25, 3.70, 6.40), (10.60, 14.70, 9.55, 10.60),
          (18.40, 21.10, 7.55, 9.90)]


def in_solid(x, y):
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in SOLIDS)


def on_road(x, y, pad=0.35):
    """Nothing may be planted on the carriageway. The road IS the subject."""
    r = road_at(x, y)
    return r is not None and r[1] < ROAD_W + 0.45 + pad


rng = random.Random(20260802)
for ob in list(bpy.data.objects):
    if ob.name.startswith("veg_gate_road_"):
        bpy.data.objects.remove(ob, do_unlink=True)

SEEDED = {}
for tag, pfx, attempts, xr, lo, hi, cull in RESEED_TAGS:
    cands = sorted(((max(world_bbox(o)[1] - world_bbox(o)[0],
                         world_bbox(o)[3] - world_bbox(o)[2],
                         world_bbox(o)[5] - world_bbox(o)[4]), o.name)
                    for o in bpy.data.objects
                    if o.type == 'MESH' and o.name.startswith(pfx)
                    and "crest" not in o.name and not o.name.startswith("veg_gate_road_")
                    and world_bbox(o)[4] < TIER_CEIL))
    if not cands:
        print("RESEED %-6s NO SURVIVING PROTOTYPE (%s*) — skipped" % (tag, pfx))
        SEEDED[tag] = dict(made=0, prototype=None, why="no surviving prototype")
        continue
    src = bpy.data.objects[cands[0][1]]
    made = 0
    for i in range(attempts):
        px = xr[0] + rng.random() * (xr[1] - xr[0])
        py = T.rim(px) - 0.15 - rng.random() * 1.25
        if not T.has_ground(px, py):
            continue
        pz = ground_top(px, py)
        if pz < 12.0:
            continue
        s = lo + rng.random() * (hi - lo)
        if over_walk(KEEP, px, py, pz + 0.45, pad=0.35 * s) or in_solid(px, py) or on_road(px, py):
            continue
        b0 = world_bbox(src)
        ext = max(b0[1] - b0[0], b0[3] - b0[2], b0[5] - b0[4]) * s
        nf = gate_lib.near_field(px, py, pz + 0.45 * ext, ext)
        if cull and rng.random() > nf:
            continue
        s = min(s, lo + (hi - lo) * max(nf, 0.0 if cull else 0.20))
        ob = src.copy(); ob.data = src.data.copy()
        ob.name = "veg_gate_road_%s_%d" % (tag, i)
        ob.data.name = ob.name
        b = world_bbox(src)
        cx0, cy0, cz0 = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
        rot = rng.random() * 6.28
        cth, sth = math.cos(rot), math.sin(rot)
        for v in ob.data.vertices:
            p = src.matrix_basis @ v.co
            q = Vector(((p.x - cx0) * s, (p.y - cy0) * s, (p.z - cz0) * s))
            v.co = Vector((q.x * cth - q.y * sth, q.x * sth + q.y * cth, q.z))
        ob.matrix_basis.identity()
        bb = world_bbox(ob)
        ob.location = Vector((px, py, pz - bb[4] - 0.06))
        link(ob, COLL)
        made += 1
    SEEDED[tag] = dict(made=made, attempts=attempts, prototype=src.name,
                       x_range=[round(v, 2) for v in xr], scale=[lo, hi])
    print("RESEED %-6s %2d of %d attempts seated on the new lip (prototype %s)"
          % (tag, made, attempts, src.name))

# =========================================================================
if DUMP:
    os.makedirs(DUMP, exist_ok=True)
    for nm in ("gate_ground", "gate_road", "gate_parapet"):
        o = bpy.data.objects[nm]
        mw = o.matrix_world
        json.dump(dict(V=[[round((mw @ v.co).x, 3), round((mw @ v.co).y, 3),
                           round((mw @ v.co).z, 3)] for v in o.data.vertices],
                       F=[list(p.vertices) for p in o.data.polygons]),
                  open(os.path.join(DUMP, "mesh_%s.json" % nm), "w"))
    print("\ndumped rebuilt meshes -> %s" % DUMP)

MAN = dict(
    _doc=("GENERATED by tools/gate_roadchop.py — the entry road (user redline #4). "
          "The shape itself is Terrain.rim()'s control points, GX0 and SPINE in "
          "tools/gate_lib.py; this records what carrying them onto the master did."),
    generator="tools/gate_roadchop.py",
    rim_prev=RIM_PREV, gx0_prev=GX0_PREV,
    lattice_note=("GX0 is lattice-aligned: -3.22 = 1.20 - 13 x ST(0.34), so every "
                  "column east of the extension is comparable with what shipped."),
    rim_new=[[1.2, 9.20], [10.6, 9.05], [11.5, 9.60], [13.0, 8.40], [16.0, 7.10],
             [19.0, 8.60], [22.0, 9.50], [25.0, 10.05], [26.8, 10.25], [27.6, 9.95],
             [30.2, 9.95], [31.9, 10.40]],
    gx0_new=GX0, spine=[list(p) for p in gate_lib.SPINE],
    ground_bands=band_rows,
    ground=dict(before=dict(verts=g_before[0], polys=g_before[1]),
                after=dict(verts=g_after[0], polys=g_after[1]), refine=REFREP),
    road=dict(nodes=len(RN), before=dict(verts=r_before[0], polys=r_before[1]),
              after=dict(verts=r_after[0], polys=r_after[1]),
              widest_m=round(wmax, 2),
              width_per_m=[dict(x=k, w=round(w, 2), y0=round(lo, 2), y1=round(hi, 2))
                           for k, w, lo, hi in widths]),
    parapet=dict(posts=len(posts), before=dict(verts=p_before[0], polys=p_before[1]),
                 after=dict(verts=p_after[0], polys=p_after[1]),
                 refused_into_prop=skipped_prop),
    vegetation=dict(kept=kept, culled=culled, reseeded=SEEDED),
    components=COMP,
)
json.dump(MAN, open(MANIFEST, "w"), indent=1)
print("\nmanifest -> %s" % os.path.relpath(MANIFEST, REPO))
if REPORT:
    json.dump(MAN, open(REPORT, "w"), indent=1)

if SAVE:
    BK["culled"] = culled
    if not os.path.exists(BACKUP):
        json.dump(dict(_doc=("GENERATED by tools/gate_roadchop.py BEFORE it modified "
                             "anything. `-- revert save` restores the three meshes."),
                       generator="tools/gate_roadchop.py", **BK), open(BACKUP, "w"))
        print("backup  -> %s (%.0f KB)" % (os.path.relpath(BACKUP, REPO),
                                           os.path.getsize(BACKUP) / 1024.0))
    else:
        print("backup already at %s — kept" % os.path.relpath(BACKUP, REPO))
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
