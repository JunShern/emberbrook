"""t2_water_bed.py — THE BATHYMETRY.  docs/plans/water-transparency.md, W1 + W2.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_water_bed.py -- [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_water_bed.py -- revert save

THE ORDERING IS THE POINT, and it is the single most important sentence in the
plan this implements: **the bathymetry is the deliverable, the shader is the
cheap part.**  The user's note was "the land terrain disappears as soon as it
hits the water; in reality you can see the terrain extend below the surface and
slowly fade out."  Measured, the terrain does NOT disappear — 94-98% of wet
samples have a bed under them.  The problem is that the bed is TWO FLAT SLABS:

    riverbed          8 vertices, z -4.20..-3.90, under a +0.20 surface
    lf_riverbed_tail  8 vertices, z -7.60..-7.30, under a -3.80 surface

4,999 of `water_pool-mid`'s 6,165 samples land in a SINGLE 0.5 m depth bin, and
`water_pool-upstream` goes from ankle-deep to seven and a half metres in one
0.75 m step.  So a depth-based transparency shader, applied to this, would
change almost nothing: there is no shallow zone to see through.  Baking a depth
attribute against the current slab would encode the very step function the pass
exists to remove, and the ramp would then be tuned to hide it.  Geometry first.

**W1 — the footprints.**  Between 43% and 79% of each pool's perimeter is not a
shoreline at all: it is the rectangle's own straight edge, ending in mid-air over
the bed.  That is the dead-straight diagonal where the turquoise stops in
`variety_waterfront.png` — the corner of a box, not a bank.  Making that edge
transparent would make it worse.  The sheets are 0.4 m thick and the fix is to
push their landward edges UNDER the bank, where the terrain hides them.

**W2 — three shelves, and only three.**  A shelf is only worth building where a
camera can see a GENTLE bank.  `tools/t2_probe_shore.py` classified every
waterline cell by bank rise and projected it into all 17 cameras: of the town's
whole shoreline, 49 metres qualify, in three places —

    lockfive       35.5 m in frame, 8.0 m of it wall  -> 27.5 m gentle
    boatyard       15.5 m in frame, 0.0 m of it wall  -> 15.5 m gentle
    cottage-steps  17.5 m in frame, 11.0 m of it wall ->  6.5 m gentle

and everywhere else the water meets a quay wall, the dam or a barge.  Each shelf
is a shore-parallel strip WELDED to the real bank at the waterline — its landward
row is ray-cast onto the terrain, not guessed — and running out to meet the slab
at its seaward edge, in the same `mat_rock` the bank already wears so the
material transition is invisible.

Revert deletes the three shelves and puts the sheet footprints back from the
recorded original edges.
"""
import bpy, os, sys, math, json
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t2_water_bed.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

MAT = "mat_rock"
PREFIX = "t2w_"

# ---- W1: push each sheet's LANDWARD edge under the bank ----------------------
# (object, the y the edge sits at now, the y to move it to)
FOOTPRINT = [
    ("water_pool-mid", 26.00, 22.80),
    # 29.60, not the 28.20 the first run tried: at 28.20 the sheet reaches
    # OVER a boatyard walk surface and master_walk_qa fails its 2.0 m
    # headroom rule on 40 samples. The bank is only 0.75 m away there.
    ("water_pool-upstream", 30.35, 29.60),
    ("water_pool-downstream", 26.00, 23.60),
]

# ---- W2: the three shelves ---------------------------------------------------
#   name, x range, shore y, out y, water surface z, slab z, profile
# profile: (metres out from the shore, metres BELOW the surface).  Beyond the
# last entry the shelf runs straight to the slab.
SHELVES = [
    # Each profile's LAST entry must equal the full surface-to-slab depth, or the
    # shelf ends in mid-water above the slab and the pass has replaced one step
    # with another. boatyard 3.60 - (-3.90) = 7.50; lockfive 4.10; cottage 3.50.
    # THE BOATYARD SHELF IS SPLIT AROUND THE SLIPWAY (x 16.9..21.8).  The slipway
    # is a walk corridor that runs down INTO the river — the one place on this
    # bank where the player's own surface is below the waterline — and a shelf
    # sampled on any grid coarse enough to be cheap will step over its narrow
    # deck somewhere.  master_walk_qa is zero-tolerance and said so, three
    # samples at 1.5 m spacing and one at 1.0 m.  Leaving the slipway's own
    # 6 m of bank unshelved costs nothing: the ramp itself is the bed there.
    ("shelf_boatyard_w", 0.0, 15.80, 30.60, 42.00, 3.60, -3.90,
     [(0.0, 0.05), (1.2, 0.45), (2.6, 1.10), (4.0, 2.20), (6.0, 3.90), (8.5, 5.60),
      (11.4, 7.50)]),
    ("shelf_boatyard_e", 22.90, 27.0, 30.60, 42.00, 3.60, -3.90,
     [(0.0, 0.05), (1.2, 0.45), (2.6, 1.10), (4.0, 2.20), (6.0, 3.90), (8.5, 5.60),
      (11.4, 7.50)]),
    ("shelf_lockfive", 60.0, 84.0, 26.60, 36.00, 0.20, -3.90,
     [(0.0, 0.05), (1.0, 0.35), (2.0, 0.60), (3.0, 0.80), (5.0, 2.00), (6.5, 3.00),
      (9.4, 4.10)]),
    ("shelf_cottage-steps", 95.0, 112.0, 26.40, 34.00, -3.80, -7.30,
     [(0.0, 0.05), (1.0, 0.30), (2.0, 0.55), (3.0, 0.80), (4.2, 1.90), (5.2, 2.80),
      (7.6, 3.50)]),
]
# 1.0 m, not 1.5: at 1.5 m the carve ray-cast stepped OVER the slipway's
# narrow walk deck and three of master_walk_qa's coverage samples first-hit
# the shelf instead of the walk mesh.
STEP_X, STEP_Y = 1.0, 0.9

sc = bpy.context.scene


def new_mesh(name, verts, faces, mat, cname):
    full = PREFIX + name
    old = bpy.data.objects.get(full)
    if old:
        me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(full)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    me.materials.append(bpy.data.materials[mat])
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(full, me)
    (bpy.data.collections.get(cname) or sc.collection).objects.link(ob)
    return ob


# ================================================================ REVERT ======
if REVERT:
    gone = []
    # by PREFIX, not by the current SHELVES table: renaming a shelf (the boatyard
    # one was split around the slipway) must not orphan the old object in the
    # master, and the first split did exactly that.
    for o in [o for o in bpy.data.objects if o.name.startswith(PREFIX)]:
        me = o.data
        gone.append(o.name)
        bpy.data.objects.remove(o, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for name, y_was, y_now in FOOTPRINT:
        ob = bpy.data.objects.get(name)
        if ob is None or not ob.get("t2w_edge"):
            continue
        M = ob.matrix_world
        Mi = M.inverted()
        for v in ob.data.vertices:
            w = M @ v.co
            if abs(w.y - y_now) < 1e-3:
                w.y = y_was
                v.co = Mi @ w
        del ob["t2w_edge"]
        ob.data.update()
        print("RESTORED %s landward edge to y = %.2f" % (name, y_was))
    print("REVERT removed: %s" % (", ".join(gone) or "nothing"))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    else:
        print("(dry — pass `save` to write the master)")
    sys.exit(0)

# ============================================================== W1 ============
print("=" * 78)
print("W1 — push each sheet's landward edge UNDER the bank")
print("=" * 78)
fp_report = {}
for name, y_was, y_now in FOOTPRINT:
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("  %s missing" % name)
        continue
    if ob.get("t2w_edge"):
        print("  %-24s already extended to y = %.2f" % (name, y_now))
        fp_report[name] = dict(was=y_was, now=y_now, moved=0)
        continue
    M = ob.matrix_world
    Mi = M.inverted()
    n = 0
    for v in ob.data.vertices:
        w = M @ v.co                      # compare in WORLD: a sheet may carry
        if abs(w.y - y_was) < 1e-3:       # a transform, and water_pool-upstream
            w.y = y_now                   # does — the first run moved 0 verts
            v.co = Mi @ w
            n += 1
    ob.data.update()
    if n:
        ob["t2w_edge"] = 1
    fp_report[name] = dict(was=y_was, now=y_now, moved=n)
    print("  %-24s %d vertices  y %.2f -> %.2f  (%.1f m further under the bank)"
          % (name, n, y_was, y_now, y_was - y_now))

# ============================================================== W2 ============
# the sheets have just moved, so re-derive the depsgraph before ray-casting the
# bank; and hide the WATER itself, or every down-ray stops at the surface.
hidden = []
for o in sc.objects:
    if o.type != 'MESH':
        continue
    if any(s.material and s.material.name == 'm_water' for s in o.material_slots) \
            or o.name.startswith(PREFIX):
        if not o.hide_viewport:
            o.hide_viewport = True
            hidden.append(o.name)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
print("\nhidden from the bank ray-cast: %d water sheets / previous shelves" % len(hidden))


def land_z(x, y, top=26.0):
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)),
                                            distance=60.0)
    return loc.z if hit else None


def top_here(x, y, top):
    """the highest EXISTING surface at (x, y), water and shelves excluded (they
    are hidden from the depsgraph above)."""
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)),
                                            distance=80.0)
    return loc.z if hit else None


def profile_z(surf, slab, prof, d, out_len):
    """depth at distance d from the shore, running to the slab at out_len"""
    if d <= prof[0][0]:
        return surf - prof[0][1]
    for i in range(len(prof) - 1):
        d0, z0 = prof[i]
        d1, z1 = prof[i + 1]
        if d <= d1:
            t = (d - d0) / (d1 - d0)
            return surf - (z0 + (z1 - z0) * t)
    d0, z0 = prof[-1]
    last = surf - z0
    if out_len <= d0:
        return slab
    t = min(1.0, (d - d0) / (out_len - d0))
    return last + (slab - last) * t


print("\n" + "=" * 78)
print("W2 — three shelves, at the only 49 m of camera-visible gentle bank")
print("=" * 78)
sh_report = {}
for name, x0, x1, y_shore, y_out, surf, slab, prof in SHELVES:
    nx = max(2, int(round((x1 - x0) / STEP_X)) + 1)
    ny = max(2, int(round((y_out - y_shore) / STEP_Y)) + 1)
    out_len = y_out - y_shore
    verts, faces = [], []
    welded = 0
    carved = 0
    for i in range(nx):
        x = x0 + (x1 - x0) * i / (nx - 1)
        # WELD: the landward row sits on the real bank, ray-cast, not guessed
        bank = land_z(x, y_shore - 0.35)
        for j in range(ny):
            y = y_shore + out_len * j / (ny - 1)
            d = y - y_shore
            z = profile_z(surf, slab, prof, d, out_len)
            if j == 0 and bank is not None:
                # WELD AT THE WATERLINE, NEVER ABOVE IT. A shelf is underwater
                # bathymetry; the bank above the water is already modelled by
                # yard_ground / lf_ground. Letting the weld row reach surf + 0.35
                # put three samples of t2w_shelf_boatyard through a walk surface
                # and failed master_walk_qa's ray-coverage check.
                z = max(z, min(bank, surf - 0.05))
                welded += 1
            # a little cross-shore variation so the shelf is not a ruled surface
            z += 0.11 * math.sin(x * 0.53 + y * 0.19) * math.sin(y * 0.41)
            # CARVE UNDER WHAT IS ALREADY THERE. The plan's three regions are
            # rectangles over a bank that is not empty: the boatyard slipway
            # ramp, the Lock Five wall, the moorings and two landing stages all
            # stand inside them, and the first build drove the shelf straight
            # through all of them (slipway_ramp 93% of its vertices INSIDE).
            # A shelf is bathymetry — it is always allowed to be lower, never
            # higher — so clamp it under the topmost existing surface.
            t = top_here(x, y, surf + 12.0)
            if t is not None and z > t - 0.45:
                z = t - 0.45          # margin: the grid samples, the ramp does not
                carved += 1
            verts.append((x, y, min(z, surf - 0.05)))
    for i in range(nx - 1):
        for j in range(ny - 1):
            a = i * ny + j
            faces.append((a, a + ny, a + ny + 1, a + 1))
    coll = "DIST_boatyard" if "boatyard" in name else "DIST_locksfoot"
    ob = new_mesh(name, verts, faces, MAT, coll)
    zs = [v[2] for v in verts]
    sh_report[name] = dict(x=[x0, x1], y=[y_shore, y_out], verts=len(verts),
                           polys=len(faces), welded_columns=welded,
                           carved_verts=carved,
                           z=[round(min(zs), 2), round(max(zs), 2)],
                           surface=surf, slab=slab, profile=prof)
    print("  %-22s %4d verts %4d polys  x %.0f..%.0f  y %.1f..%.1f  z %.2f..%.2f"
          "  (%d columns welded, %d verts carved under existing build)"
          % (PREFIX + name, len(verts), len(faces), x0, x1, y_shore, y_out,
             min(zs), max(zs), welded, carved))

for nm in hidden:
    o = bpy.data.objects.get(nm)
    if o is not None:
        o.hide_viewport = False

tv = sum(s["verts"] for s in sh_report.values())
print("\nTOTAL %d shelf vertices / %d polys" % (tv, sum(s["polys"] for s in sh_report.values())))

json.dump(dict(
    _doc=("GENERATED by tools/t2_water_bed.py — W1 (sheet footprints pushed under "
          "the bank) and W2 (the three shelves). Geometry BEFORE shader: baking a "
          "depth attribute against the current flat slab would encode the step "
          "function this pass exists to remove."),
    generator="tools/t2_water_bed.py", plan="docs/plans/water-transparency.md",
    prefix=PREFIX, material=MAT, step=[STEP_X, STEP_Y],
    footprints=fp_report, shelves=sh_report, total_shelf_verts=tv,
), open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
