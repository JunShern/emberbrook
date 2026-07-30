"""t2_cliff_res.py — the three targeted resolution repairs.  Phase C3 of
docs/plans/cliff-completion.md.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_cliff_res.py -- [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_cliff_res.py -- revert save

THE MEASUREMENT.  `px_per_edge = mean_edge_m x (H/2) / (d_mean x tan(fov/2))` at
the shipped 2688x1536 — how many delivered pixels one mesh edge spans.  The
town's terrain is almost all excellent (yard_ground 32, lf_ground 41-63,
gate_cliffface 43, shelf_cliffface 45-76).  Exactly three surfaces are not, and
only where a camera stands close enough to care:

  qm_stair_underworks   192 v, 1.63 m edges — 204 px/edge at quay-east's 19 m
                        (5.0% of that frame) and 189 at loop-stairs' 21 m
  gate_ground west lobe 0.88 m edges — 156 px/edge at shelf-west's 13 m, and
                        13.5% of that frame.  The one town surface genuinely
                        under-resolved at its closest camera.
  wv_hut_* walls        1.30-1.76 m edges — 118-233 px/edge across cottage,
                        lockhead, crossing, lockfive and quay-west.  These are
                        the lf_ kit's kitbash boxes and they read as boxes
                        wherever a camera stands inside 25 m.

WHY THE NUMBER MEANS WHAT IT MEANS, which the plan could not have known:
EVERY MESH IN DELLHOLLOW IS FLAT-SHADED.  Measured here — gate_cliffface 0/4524
smooth polygons, lf_ground 0/6210, shelf_ground 0/7902, yard_ground 0/4042, all
nine weave huts 0/N.  The town gets its smoothness from TESSELLATION, not from
shading.  So px/edge is not a proxy for facet size, it IS facet size: a 1.63 m
edge at 19 m is a 204-pixel flat plane with one constant normal, and that is
precisely what the eye reads as computer-generated.  It also means subdividing
alone is worth nothing on a surface that is already planar — a subdivided plane
is the same plane.  Each repair below therefore pairs refinement with the thing
that makes the refinement visible.

  1. qm_stair_underworks — subdivide to ~0.55 m and displace by a 4 cm noise
     along the face normal.  Masonry stays flat-shaded (it is a stair soffit,
     not a boulder); the noise is what turns 144 dead-flat panels into a surface
     that catches the key at slightly different angles.
  2. gate_ground west lobe (x 1..15 only) — subdivide to ~0.5 m and displace
     3 cm.  Deliberately tiny: this surface carries the gate district's walk
     corridors 0.42 m above it, and `walk QA` must come back bit-identical.
  3. wv_hut_* walls — a 6 cm two-segment bevel on the VERTICAL edges of the
     wall panels only.  Bevel only ever removes material, so it cannot newly
     intersect anything, and a lit 6 cm chamfer is what stops a box reading as
     a box.  Roofs are untouched: they carry the four new shingle variants and
     their `Col` from the house-variety pass, and rebuilding those loops would
     scramble the vertex colours.

REVERT IS EXACT AND IT IS A RESTORE, NOT AN INVERSE.  Subdivision and bevel are
not invertible, so before touching anything this script writes every target
mesh's original vertices, polygons, material indices and smooth flags to
tools/blends/districts/t2_cliff_res_backup.json, and `-- revert` rebuilds the
meshes from it.  The backup is written ONCE and never overwritten by a second
run, so re-running the repair cannot destroy the original.
"""
import bpy, os, sys, math, json, bmesh
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
BACKUP = os.path.join(ROOT, "tools/blends/districts/t2_cliff_res_backup.json")
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_cliff_res.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

HUTS = [o.name for o in bpy.data.objects
        if o.type == 'MESH' and o.name.startswith("wv_hut")]
TARGETS = ["qm_stair_underworks", "gate_ground"] + sorted(HUTS)

GATE_LOBE = (1.0, 15.0)          # x range of the west lobe, from the audit
WALL_MATS = ("lf_stone", "lf_deck")
BEVEL, BEVEL_SEG = 0.06, 2


def snapshot(ob):
    me = ob.data
    return dict(
        verts=[[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)] for v in me.vertices],
        polys=[list(p.vertices) for p in me.polygons],
        mati=[p.material_index for p in me.polygons],
        smooth=[bool(p.use_smooth) for p in me.polygons],
        materials=[m.name if m else None for m in me.materials],
    )


def restore(ob, snap):
    me = ob.data
    me.clear_geometry()
    me.from_pydata([tuple(v) for v in snap["verts"]], [], [tuple(p) for p in snap["polys"]])
    me.validate()
    me.update()
    me.materials.clear()
    for mn in snap["materials"]:
        me.materials.append(bpy.data.materials.get(mn) if mn else None)
    for p, mi, sm in zip(me.polygons, snap["mati"], snap["smooth"]):
        p.material_index = mi
        p.use_smooth = sm
    me.update()


# ================================================================ REVERT ======
if REVERT:
    assert os.path.exists(BACKUP), "no backup at %s — nothing to revert to" % BACKUP
    snaps = json.load(open(BACKUP))["meshes"]
    n = 0
    for name, snap in snaps.items():
        ob = bpy.data.objects.get(name)
        if ob is None:
            print("  %s is gone — cannot restore" % name)
            continue
        restore(ob, snap)
        n += 1
        print("RESTORED %-26s %5d verts %5d polys" % (name, len(snap["verts"]), len(snap["polys"])))
    print("REVERT restored %d meshes from %s" % (n, os.path.relpath(BACKUP, ROOT)))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# ================================================================ BACKUP ======
if os.path.exists(BACKUP):
    print("backup already at %s — kept (a second run must not overwrite the "
          "original)" % os.path.relpath(BACKUP, ROOT))
else:
    snaps = {}
    for name in TARGETS:
        ob = bpy.data.objects.get(name)
        if ob is not None:
            snaps[name] = snapshot(ob)
    json.dump(dict(
        _doc=("GENERATED by tools/t2_cliff_res.py BEFORE it modified anything. "
              "Subdivision and bevel are not invertible, so the revert path for "
              "phase C3 is a restore from this file. Do not hand-edit."),
        generator="tools/t2_cliff_res.py", targets=TARGETS, meshes=snaps,
    ), open(BACKUP, "w"))
    print("backup -> %s  (%d meshes, %.0f KB)"
          % (os.path.relpath(BACKUP, ROOT), len(snaps), os.path.getsize(BACKUP) / 1024.0))


def noise3(p, f, s):
    return (math.sin(p.x * f + p.y * f * 1.7 + s) *
            math.cos(p.y * f * 0.9 - p.z * f * 1.3 + s * 2.1) *
            math.sin(p.z * f * 1.4 + p.x * f * 0.6 - s))


def mean_edge(me):
    if not me.edges:
        return 0.0
    return sum((me.vertices[e.vertices[0]].co - me.vertices[e.vertices[1]].co).length
               for e in me.edges) / len(me.edges)


report = {}


def refine(name, want_edge, disp, region=None):
    """subdivide every face (optionally only those inside `region` in x) until
    its edges are under `want_edge`, then displace the new surface along its
    normal by `disp` metres of deterministic noise."""
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("  %s missing" % name)
        return
    me = ob.data
    before = (len(me.vertices), len(me.polygons), mean_edge(me))
    bm = bmesh.new()
    bm.from_mesh(me)
    sel = [f for f in bm.faces
           if region is None or (region[0] <= f.calc_center_median().x <= region[1])]
    cuts = max(1, int(math.ceil(before[2] / want_edge)) - 1)
    edges = list({e for f in sel for e in f.edges})
    if edges and cuts >= 1:
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True)
    bm.normal_update()
    lo = region[0] if region else -1e9
    hi = region[1] if region else 1e9
    moved = 0
    for v in bm.verts:
        if not (lo <= v.co.x <= hi):
            continue
        n = v.normal
        if n.length < 1e-6:
            continue
        v.co += n.normalized() * (disp * noise3(v.co, 0.9, 1.7))
        moved += 1
    bm.to_mesh(me)
    bm.free()
    me.update()
    after = (len(me.vertices), len(me.polygons), mean_edge(me))
    report[name] = dict(before=dict(verts=before[0], polys=before[1], edge=round(before[2], 3)),
                        after=dict(verts=after[0], polys=after[1], edge=round(after[2], 3)),
                        cuts=cuts, displaced_m=disp, verts_moved=moved,
                        region_x=list(region) if region else None)
    print("REFINED %-26s %5d->%-6d verts   edge %.2f -> %.2f m   %d cuts, %d verts "
          "displaced by <= %.0f mm" % (name, before[0], after[0], before[2], after[2],
                                       cuts, moved, disp * 1000))


def bevel_walls(name):
    """6 cm chamfer on the VERTICAL edges of wall-material faces only."""
    ob = bpy.data.objects.get(name)
    if ob is None:
        return
    me = ob.data
    slots = [s.material.name if s.material else None for s in ob.material_slots]
    wall_idx = {i for i, m in enumerate(slots) if m in WALL_MATS}
    if not wall_idx:
        return
    before = (len(me.vertices), len(me.polygons), mean_edge(me))
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    wall_faces = [f for f in bm.faces
                  if f.material_index in wall_idx and abs(f.normal.z) < 0.55]
    edges = [e for e in {e for f in wall_faces for e in f.edges}
             if all(f.material_index in wall_idx for f in e.link_faces)
             and abs((e.verts[1].co - e.verts[0].co).normalized().z) > 0.5]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=BEVEL, segments=BEVEL_SEG,
                        affect='EDGES', clamp_overlap=True, profile=0.5)
    bm.to_mesh(me)
    bm.free()
    me.update()
    after = (len(me.vertices), len(me.polygons), mean_edge(me))
    report[name] = dict(before=dict(verts=before[0], polys=before[1], edge=round(before[2], 3)),
                        after=dict(verts=after[0], polys=after[1], edge=round(after[2], 3)),
                        bevel_m=BEVEL, segments=BEVEL_SEG, edges_bevelled=len(edges))
    print("BEVELLED %-25s %5d->%-6d verts   %3d vertical wall edges at %.0f mm x %d"
          % (name, before[0], after[0], len(edges), BEVEL * 1000, BEVEL_SEG))


print("\n[1] the quay-market stair soffit — 204 px/edge at quay-east's 19 m")
refine("qm_stair_underworks", 0.55, 0.040)

print("\n[2] gate_ground's WEST LOBE ONLY (x %.0f..%.0f) — 156 px/edge at "
      "shelf-west's 13 m" % GATE_LOBE)
refine("gate_ground", 0.50, 0.030, region=GATE_LOBE)

print("\n[3] the nine weave huts — walls only, roofs untouched (they carry the "
      "house-variety shingle Col)")
for h in sorted(HUTS):
    bevel_walls(h)

tv = sum(r["after"]["verts"] - r["before"]["verts"] for r in report.values())
print("\nTOTAL +%d vertices across %d meshes" % (tv, len(report)))

json.dump(dict(
    _doc=("GENERATED by tools/t2_cliff_res.py — phase C3, the three targeted "
          "resolution repairs. Revert restores from t2_cliff_res_backup.json."),
    generator="tools/t2_cliff_res.py", plan="docs/plans/cliff-completion.md",
    gate_lobe_x=list(GATE_LOBE), wall_materials=list(WALL_MATS),
    bevel_m=BEVEL, bevel_segments=BEVEL_SEG,
    verts_added=tv, meshes=report,
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
