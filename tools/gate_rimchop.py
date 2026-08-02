"""gate_rimchop.py — THE APRON CHOP, applied surgically to the live master.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_rimchop.py -- [save] [--report <json>]

THE REDLINE.  User, left ellipse of docs/qa/refs/user_gate_tier_annotated.png:
*"Unused space, just chop off to keep the lane narrow, replace with the
more-realistic cliff face?"*  The edit itself is ONE LIST — `Terrain.rim()`'s
control points in tools/gate_lib.py — and this file is only the machine that
carries that list onto the geometry that already exists.

WHY THIS FILE EXISTS AT ALL, i.e. WHY NOT JUST RE-RUN `gate_build.py`.
The staged plan (DAYLOG 2026-08-02) was "apply the list, rebuild the BRANCH,
ga_build, merge".  Measured 2026-08-02 on this repo, that route is closed:

  * `tools/blends/dellhollow-master-gate-branch.blend` NO LONGER EXISTS.  The
    only gate-branch files on disk are three 2026-07-29 backups, which predate
    the shelf, quay-market, weave, cliff and gate-stair work.
  * `gate_build.py` run against the LIVE master (dry, in memory, no save)
    rebuilds 36 objects where the master carries 147.  Diffed object by object:
      - ALL 111 `veg_gate_*` meshes are lost and NONE are rebuilt.  The placer
        clones from bare-named kit sources (`rimclump_3`, `rimtree_0`,
        `seam_tuft_0`, `creeper_4`); those objects live in the BRANCH and are
        not in the master, so every `clone()` returns 0.
      - the 7 `KEYG_approach_*` / `KEYG_gate_*` lights that `gate_light.py`
        owns are cleared by the `KEYG_` prefix sweep and never rebuilt.
      - `gate_ground` drops 14,271 -> 4,752 verts: `t2_cliff_res.py`'s west-lobe
        refinement (phase C3) is not in `gate_build.py` and would be undone.
      - `gate_clutter` 2,636 -> 2,260, `gate_yard` 424 -> 288, `gate_bunting`
        926 -> 916 (the Corridor tests now see districts the branch never had).
    So `gate_build.py` is NOT idempotent against the live master.  Re-running it
    is a regression, with or without `ga_build.py` after it.

WHAT THIS PASS DOES INSTEAD — the three consumers of `T.rim()`, and nothing else:

  1. `gate_ground`  rebuilt from gate_build's OWN section-1 lattice (copied
     verbatim, same ST/GX/GY/NODE/cell/skirt code), then re-refined over the
     west lobe with `t2_cliff_res.py`'s own refine() at its own numbers
     (x 1..15, 0.50 m target edge, 30 mm displacement).  The skirt rule is
     "wherever the sheet stops", so the CUT FACE IS THE CLIFF FACE — that is the
     second half of the user's sentence, and it costs nothing extra.
  2. `gate_parapet` rebuilt from gate_build's OWN section-7 search (copied
     verbatim): start at `T.rim(x) - 0.55` and walk outward 0.12 m at a time
     until the walk corridor releases.  Placed off the rim, so it follows.
  3. everything SEATED on the ground that the new lip no longer carries —
     `veg_gate_*` objects and the loose components of `gate_yard` /
     `gate_clutter` — is removed.  The test is DIFFERENTIAL, `has_ground` under
     the old lip AND NOT under the new one, because "is there ground under this"
     alone deletes the winch head, which hangs over the lip on purpose.
  4. rim vegetation is RE-SEATED on the new lip, `mode="rim"` off `T.rim`
     exactly as `clone()` does it, from the smallest surviving instance of each
     tag.  A cull without a re-seat is only half the edit: the first pass
     shipped a bare timber fence over raw rock where the frame had carried an
     autumn crown line, and that was found by LOOKING at the draft, not by any
     number in this file.

FAITHFULNESS IS GATED, NOT ASSERTED.  Section 1 is run TWICE — once with the
pre-chop control points and once with the shipped ones — and the pass prints:
  (a) old-rim rebuild vs `t2_cliff_res_backup.json`'s pre-refine `gate_ground`
      snapshot: proves this copy of section 1 still reproduces the shipped base
      ground on today's master;
  (b) old-rim rebuild vs new-rim rebuild, restricted to the region INSIDE both
      rims: proves the chop moves nothing it was not asked to move.
Both are printed with their numbers whether they pass or not.

REVERT: tools/blends/districts/gate_rimchop_backup.json holds the pre-chop
`gate_ground` / `gate_parapet` meshes and the culled objects' transforms;
`-- revert save` restores them.  Written ONCE, never overwritten.
"""
import bpy, bmesh, math, os, sys, json, hashlib
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
REPORT = argv[argv.index("--report") + 1] if "--report" in argv else None
BACKUP = REPO + "/tools/blends/districts/gate_rimchop_backup.json"
MANIFEST = REPO + "/tools/blends/districts/gate_rimchop.json"
COLL = "GATE_DISTRICT"

# THE PRE-CHOP CONTROL POINTS, kept here as DATA for the faithfulness gate only.
# gate_lib.Terrain.rim is the single authority for the shipped shape; this list is
# never used to build anything that is saved.
RIM_OLD = [(1.2, 12.46), (9.5, 12.46), (12.5, 12.10), (16.0, 11.55),
           (20.0, 11.10), (24.5, 10.60), (26.8, 10.25), (27.6, 9.95),
           (30.2, 9.95), (31.9, 10.40)]


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


RIM_SHIPPED = Terrain.rim            # the edited gate_lib function


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
          "they are recorded in the backup for archaeology only."
          % len(B.get("culled", [])))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED", bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

print("=" * 78)
print("GATE RIM CHOP — the apron east of the Porters' Yard")
print("=" * 78)

T = Terrain()
COR0, COR, KEEP = T.cor0, T.cor, T.keep
MROCK = M("mat_rock")
MTURF = M("mat_gate_turf")
MSTONE = M("mat_gate_stone")
MT, MROPE = M("mat_timber"), M("mat_rope")
for nm, m in (("mat_rock", MROCK), ("mat_gate_turf", MTURF), ("mat_gate_stone", MSTONE),
              ("mat_timber", MT), ("mat_rope", MROPE)):
    assert m is not None, "material %s is missing from this blend" % nm

GROUND = bpy.data.objects.get("gate_ground")
PARAPET = bpy.data.objects.get("gate_parapet")
assert GROUND is not None and PARAPET is not None, "gate_ground / gate_parapet missing"
for ob in (GROUND, PARAPET):
    assert ob.matrix_world.to_translation().length < 1e-6, (
        "%s has a non-identity transform (%s) — this pass builds in world coords"
        % (ob.name, ob.matrix_world.to_translation()))

# the rim, column by column, so the report carries the shape it applied
print("\nTHE LIP, per metre (old -> shipped):")
row_x, row_o, row_n = [], [], []
for x in range(1, 31):
    row_x.append("%6d" % x)
    row_o.append("%6.2f" % rim_of(RIM_OLD)(T, x))
    row_n.append("%6.2f" % RIM_SHIPPED(T, x))
print("  x    " + "".join(row_x))
print("  old  " + "".join(row_o))
print("  new  " + "".join(row_n))

# =========================================================================
# SECTION 1 — the ground lattice, copied verbatim from gate_build.py
# =========================================================================
ROAD_W = 1.42
GROUND_DROP = 0.36


def ground_top(x, y):
    h = T.natural(x, y)
    for raw, fn, zt, nm in T.high:
        d = dist_poly2(x, y, raw)
        if d < 5.4:
            h = min(h, T.plane_at(raw, fn, x, y, d) - GROUND_DROP
                    + max(0.0, d - (ROAD_W + 0.50)) * 1.15)
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


ST = 0.34
NX = int(round((GX1 - GX0) / ST)) + 1
NY = int(round((GY1 - GY0) / ST)) + 1


def build_ground():
    """gate_build.py section 1, verbatim. Returns (NODE, V, F, MI)."""
    NODE = {}
    for i in range(NX):
        for j in range(NY):
            x, y = GX0 + i * ST, GY0 + j * ST
            if not T.has_ground(x, y):
                continue
            t = ground_top(x, y)
            NODE[(i, j)] = (x, y, t, T.bottom(x, y, t))
    V, F, MI = [], [], []
    topi, boti = {}, {}
    for k, (x, y, t, b) in NODE.items():
        topi[k] = len(V); V.append((x, y, t))
        boti[k] = len(V); V.append((x, y, b))

    def cell(i, j):
        return all((i + a, j + c) in NODE for a, c in ((0, 0), (1, 0), (1, 1), (0, 1)))

    for i in range(NX - 1):
        for j in range(NY - 1):
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


# --- (a) the OLD-rim rebuild, for the faithfulness gates only -----------------
Terrain.rim = rim_of(RIM_OLD)
T._ylo = {}
NODE_OLD, V_OLD, F_OLD, MI_OLD = build_ground()
Terrain.rim = RIM_SHIPPED
T._ylo = {}
NODE_NEW, V_NEW, F_NEW, MI_NEW = build_ground()

print("\nSECTION 1 REBUILD   old rim %d nodes / %d faces   ->   new rim %d nodes / %d faces"
      % (len(NODE_OLD), len(F_OLD), len(NODE_NEW), len(F_NEW)))

# gate (a): the old-rim rebuild against the shipped pre-refine snapshot
GATE_A = {"ran": False}
snapf = REPO + "/tools/blends/districts/t2_cliff_res_backup.json"
if os.path.exists(snapf):
    shipped = json.load(open(snapf))["meshes"].get("gate_ground")
    if shipped:
        want = {(round(v[0], 3), round(v[1], 3)): round(v[2], 3) for v in shipped["verts"]}
        got = {(round(v[0], 3), round(v[1], 3)): round(v[2], 3) for v in V_OLD}
        # a lattice column carries TWO verts (top, bottom) at one (x,y); compare the
        # SET of (x,y,z) triples instead, which is what a mesh identity actually is.
        wset = {(round(v[0], 3), round(v[1], 3), round(v[2], 3)) for v in shipped["verts"]}
        gset = {(round(v[0], 3), round(v[1], 3), round(v[2], 3)) for v in V_OLD}
        diff = sorted((wset - gset) | (gset - wset))
        # WHERE the drift is matters more than how much: a vertex on the underside at
        # z=-8 is never in any frame, a vertex on the walking surface is.
        vis = [v for v in diff if v[2] > 21.0]
        GATE_A = dict(ran=True, shipped_verts=len(shipped["verts"]), rebuilt_verts=len(V_OLD),
                      shared=len(wset & gset), only_shipped=len(wset - gset),
                      only_rebuilt=len(gset - wset), differing_above_z21=len(vis),
                      differing_x_range=[round(min(v[0] for v in diff), 2),
                                         round(max(v[0] for v in diff), 2)] if diff else None,
                      differing_z_range=[round(min(v[2] for v in diff), 2),
                                         round(max(v[2] for v in diff), 2)] if diff else None)
        print("GATE (a) section-1 vs the shipped pre-refine snapshot: "
              "%d shipped / %d rebuilt verts, %d identical, %d only-shipped, %d only-rebuilt"
              % (GATE_A["shipped_verts"], GATE_A["rebuilt_verts"], GATE_A["shared"],
                 GATE_A["only_shipped"], GATE_A["only_rebuilt"]))
        print("         the differing verts: x %s  z %s  — %d of %d are above z=21 "
              "(i.e. on the walked surface rather than the underside)"
              % (GATE_A["differing_x_range"], GATE_A["differing_z_range"], len(vis), len(diff)))
        # HOW BIG is the drift, column by column: max |dz| where BOTH carry a top vert
        # at the same (x, y), and how many columns exist in only one of the two.
        def tops(vs):
            d = {}
            for v in vs:
                k = (round(v[0], 2), round(v[1], 2))
                d[k] = max(d.get(k, -1e9), v[2])
            return d
        ts, tg = tops(shipped["verts"]), tops(V_OLD)
        both = set(ts) & set(tg)
        dz = sorted(((abs(ts[k] - tg[k]), k) for k in both), reverse=True)
        GATE_A["top_columns_both"] = len(both)
        GATE_A["top_max_dz"] = round(dz[0][0], 4) if dz else 0.0
        GATE_A["top_over_10mm"] = sum(1 for d_, _ in dz if d_ > 0.010)
        GATE_A["columns_only_shipped"] = len(set(ts) - set(tg))
        GATE_A["columns_only_rebuilt"] = len(set(tg) - set(ts))
        print("         top surface, same (x,y): %d columns, max |dz| %.4f m, %d over "
              "10 mm; columns present in only one: %d shipped-only / %d rebuilt-only"
              % (GATE_A["top_columns_both"], GATE_A["top_max_dz"],
                 GATE_A["top_over_10mm"], GATE_A["columns_only_shipped"],
                 GATE_A["columns_only_rebuilt"]))

# gate (b): old vs new rebuild, restricted to the region inside BOTH rims
rold, rnew = rim_of(RIM_OLD), RIM_SHIPPED
moved, inside, maxd = 0, 0, 0.0
worst = None
for k, (x, y, t, b) in NODE_NEW.items():
    if y > min(rold(T, x), rnew(T, x)) - 1e-9:
        continue
    inside += 1
    o = NODE_OLD.get(k)
    if o is None:
        moved += 1
        continue
    d = max(abs(o[2] - t), abs(o[3] - b))
    if d > maxd:
        maxd, worst = d, (round(x, 2), round(y, 2), round(o[2], 4), round(t, 4))
    if d > 1e-6:
        moved += 1
lost = [k for k in NODE_OLD if k not in NODE_NEW]
gained = [k for k in NODE_NEW if k not in NODE_OLD]
print("GATE (b) inside BOTH rims: %d nodes, %d moved, max |dz| = %.6f m %s"
      % (inside, moved, maxd, ("at %s" % (worst,)) if worst else ""))
print("         nodes cut by the chop: %d   nodes gained: %d" % (len(lost), len(gained)))

# --- write the new ground -----------------------------------------------------
BK = {"meshes": {}, "culled": []}
if not os.path.exists(BACKUP):
    BK["meshes"]["gate_ground"] = snapshot(GROUND)
    BK["meshes"]["gate_parapet"] = snapshot(PARAPET)

g_before = (len(GROUND.data.vertices), len(GROUND.data.polygons))
me = bpy.data.meshes.new("gate_ground_tmp")
me.from_pydata(V_NEW, [], F_NEW)
me.validate()
for m in (MROCK, MTURF):
    me.materials.append(m)
for p, mi in zip(me.polygons, MI_NEW):
    p.material_index = mi
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
old_me = GROUND.data
GROUND.data = me
bpy.data.meshes.remove(old_me)
me.name = "gate_ground"

# --- re-apply t2_cliff_res's west-lobe refinement, at ITS OWN numbers ----------
GATE_LOBE = (1.0, 15.0)


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
    # `cuts` IS PINNED, not re-derived, and this is the whole reason the argument
    # exists.  t2_cliff_res computes cuts from the mesh's CURRENT mean edge, and the
    # chop changes that mean: the shipped repair ran at mean edge 0.932 m -> 1 cut
    # (4,774 -> 14,271 verts, districts/t2_cliff_res.json), while the chopped sheet
    # measures 1.065 m -> 2 cuts and lands at 28,014.  The rise is an artefact of the
    # cut — a longer skirt means more 32 m vertical edges in the average — not a
    # statement that the surface got coarser.  Re-deriving the parameter would double
    # the town's ground budget as a side effect of a rim edit, so the repair is
    # reproduced at ITS OWN number.
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


REFREP = refine(GROUND, 0.50, 0.030, GATE_LOBE, pin_cuts=1)
g_after = (len(GROUND.data.vertices), len(GROUND.data.polygons))
print("gate_ground   %d verts / %d polys  ->  %d / %d"
      % (g_before[0], g_before[1], g_after[0], g_after[1]))

# =========================================================================
# SECTION 7 — the parapet search, copied verbatim from gate_build.py
# =========================================================================
parts, posts = [], []
x = 2.10
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
print("gate_parapet  %d posts   %d verts / %d polys  ->  %d / %d"
      % (len(posts), p_before[0], p_before[1], p_after[0], p_after[1]))

# =========================================================================
# THE CULL — anything the new lip no longer carries
# =========================================================================
# THE TEST IS DIFFERENTIAL, and the first cut of it was wrong in a way worth
# recording.  "Is there ground under this piece now?" removed 24 of `gate_winch`'s
# 44 components at columns where the rim did not move at all (9.95 -> 9.95): the
# winch head HANGS OVER the lip on purpose — its rope goes down 23 m to the quay —
# so it was never admitted by `has_ground` and never should have been.  The
# question is not "is it over ground" but "did THIS EDIT take its ground away":
#
#     cull  <=>  has_ground(OLD rim) and not has_ground(NEW rim)
#
# which is exactly the seat `clone()` / `clear()` would have granted before and
# refused after, and which is inert on everything the rim did not move.
# Crest crowns sit on `cliff_crest`, 14+ m above the tier, and are keyed out by
# height as well.
TIER_CEIL = 30.0            # anything based above this is not seated on the tier


def stranded(cx, cy, base):
    """True iff the OLD lip carried this footprint and the new one does not."""
    if base > TIER_CEIL:
        return False
    Terrain.rim = rim_of(RIM_OLD); T._ylo = {}
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
                       rim_old=round(rold(T, cx), 3), rim_new=round(rnew(T, cx), 3),
                       why="the old lip carried this footprint, the new one does not"))
    bpy.data.objects.remove(ob, do_unlink=True)
print("\nVEGETATION   %d veg_gate_* kept, %d culled (stranded past the new lip)"
      % (kept, len(culled)))
for c in culled:
    print("   CULL %-28s at (%6.2f,%6.2f)  rim %5.2f -> %5.2f"
          % (c["name"], c["x"], c["y"], c["rim_old"], c["rim_new"]))


def cull_components(name):
    """Remove the connected components of a joined prop mesh whose own footprint
    the new lip no longer carries — the same admission test, applied per piece
    because these props ship as one joined object."""
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
        if not stranded(cx, cy, cz):
            keptc += 1
            continue
        drop.extend(comp)
        rows.append(dict(x=round(cx, 3), y=round(cy, 3), z=round(cz, 3),
                         verts=len(comp), rim_old=round(rold(T, cx), 3),
                         rim_new=round(rnew(T, cx), 3)))
    nb = len(bm.verts)
    if drop:
        bmesh.ops.delete(bm, geom=drop, context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    print("%-14s %d components: %d kept, %d cut (%d -> %d verts)"
          % (name, len(comps), keptc, len(rows), nb, len(ob.data.vertices)))
    for r in rows:
        print("   CUT  piece at (%6.2f,%6.2f) %3d verts  rim %5.2f -> %5.2f"
              % (r["x"], r["y"], r["verts"], r["rim_old"], r["rim_new"]))
    return dict(components=len(comps), kept=keptc, cut=rows,
                verts_before=nb, verts_after=len(ob.data.vertices))


print()
COMP = {}
for nm in ("gate_yard", "gate_clutter", "gate_bunting", "gate_winch", "gate_road"):
    r = cull_components(nm)
    if r:
        COMP[nm] = r

# =========================================================================
# THE RE-SEAT — the third consumer of T.rim(), and the half of the chop a pure
# cull gets wrong
# =========================================================================
# LOOKED AT, not inferred: the first pass culled 63 rim plants and seated none, and
# the `gate` draft came back with the tier edge reading as a bare timber fence over
# raw rock where it had been a soft autumn crown line.  A rebuild would not have done
# that — `clone(..., mode="rim")` re-seats off `T.rim` every run, which is why the
# staged plan calls rim vegetation the third thing the one-list edit carries.
#
# THE PROTOTYPES ARE THE SURVIVORS.  gate_build clones from bare-named kit sources
# (`rimclump_3`, `seam_tuft_0`, ...) that live in the branch blend and are not in the
# master — that is the same absence that makes `gate_build.py` unrunnable here.  So
# each tag's prototype is the lowest-named SURVIVING clone of that tag, and the scale
# range is narrowed to ~1x because the prototype has already been through the
# original near-field size ceiling once and a second full-range scaling would compound.
#
# NO TREES AND NO CREEPERS, and both refusals are measured, not stylistic.  Every
# creeper was culled (they hang on the FACE, `mode="face"`, past the lip) so no
# prototype survives; and the new verge is ~1.5 m, which is narrower than a
# `veg_gate_rimtree` crown — a tree seated there stands in the lane, which is the
# thing the redline is asking to clear.
RESEED_TAGS = [
    # (tag, prototype prefix, attempts, x range, scale lo/hi, cull-in-near-field)
    ("clump", "veg_gate_rimclump_", 22, (10.6, 26.0), 0.75, 1.15, True),
    ("tuft",  "veg_gate_tuft_",     70, (10.6, 27.5), 0.85, 1.25, True),
    ("fern",  "veg_gate_fern_",     24, (10.6, 26.0), 0.85, 1.15, True),
]
SOLIDS = [(2.90, 9.10, -0.25, 3.25), (0.40, 5.10, 2.30, 5.45),
          (9.15, 14.00, -0.60, 4.90), (14.60, 15.75, 2.85, 9.00),
          (15.80, 17.55, 0.80, 7.20), (16.05, 17.20, -0.60, 10.70),
          (25.45, 29.25, 3.70, 6.40), (10.60, 14.70, 9.55, 10.60),
          (18.40, 21.10, 7.55, 9.90)]


def in_solid(x, y):
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, x1, y0, y1 in SOLIDS)


import random
rng = random.Random(20260802)
for ob in list(bpy.data.objects):
    if ob.name.startswith("veg_gate_chop_"):
        bpy.data.objects.remove(ob, do_unlink=True)

SEEDED = {}
for tag, pfx, attempts, xr, lo, hi, cull in RESEED_TAGS:
    # THE SMALLEST SURVIVOR, and the tie broken by name so it is deterministic.
    # The old lip was a 4-6 m apron and could carry a 1.4 m crown; the new one is a
    # ~1.5 m verge, and the biggest surviving clump seated on it cost the ARRIVAL
    # frame two of its own region probes (gate visibleFrac 0.781 bare -> 0.750).
    # Small is not a taste here, it is what the verge is wide enough for.
    cands = sorted(((max(world_bbox(o)[1] - world_bbox(o)[0],
                         world_bbox(o)[3] - world_bbox(o)[2],
                         world_bbox(o)[5] - world_bbox(o)[4]), o.name)
                    for o in bpy.data.objects
                    if o.type == 'MESH' and o.name.startswith(pfx)
                    and "crest" not in o.name and not o.name.startswith("veg_gate_chop_")
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
        if over_walk(KEEP, px, py, pz + 0.45, pad=0.35 * s) or in_solid(px, py):
            continue
        b0 = world_bbox(src)
        ext = max(b0[1] - b0[0], b0[3] - b0[2], b0[5] - b0[4]) * s
        nf = gate_lib.near_field(px, py, pz + 0.45 * ext, ext)
        if cull and rng.random() > nf:
            continue
        s = min(s, lo + (hi - lo) * max(nf, 0.0 if cull else 0.20))
        ob = src.copy(); ob.data = src.data.copy()
        ob.name = "veg_gate_chop_%s_%d" % (tag, i)
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
                       x_range=list(xr), scale=[lo, hi])
    print("RESEED %-6s %2d of %d attempts seated on the new lip (prototype %s)"
          % (tag, made, attempts, src.name))

# =========================================================================
MAN = dict(
    _doc=("GENERATED by tools/gate_rimchop.py — the apron chop (user redline, "
          "gate tier).  The shape itself is Terrain.rim()'s control points in "
          "tools/gate_lib.py; this records what carrying them onto the master did."),
    generator="tools/gate_rimchop.py",
    rim_old=RIM_OLD,
    rim_new=[[1.2, 12.46], [9.5, 12.46], [10.6, 12.10], [11.5, 9.60],
             [13.0, 8.40], [16.0, 7.10], [19.0, 8.60], [22.0, 9.50],
             [25.0, 10.05], [26.8, 10.25], [27.6, 9.95], [30.2, 9.95], [31.9, 10.40]],
    gate_a=GATE_A,
    gate_b=dict(nodes_inside_both=inside, moved=moved, max_dz=round(maxd, 6),
                nodes_cut=len(lost), nodes_gained=len(gained)),
    ground=dict(before=dict(verts=g_before[0], polys=g_before[1]),
                after=dict(verts=g_after[0], polys=g_after[1]), refine=REFREP),
    parapet=dict(posts=len(posts), before=dict(verts=p_before[0], polys=p_before[1]),
                 after=dict(verts=p_after[0], polys=p_after[1])),
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
        json.dump(dict(_doc=("GENERATED by tools/gate_rimchop.py BEFORE it modified "
                             "anything.  `-- revert save` restores the two meshes."),
                       generator="tools/gate_rimchop.py", **BK), open(BACKUP, "w"))
        print("backup  -> %s (%.0f KB)" % (os.path.relpath(BACKUP, REPO),
                                           os.path.getsize(BACKUP) / 1024.0))
    else:
        print("backup already at %s — kept" % os.path.relpath(BACKUP, REPO))
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
