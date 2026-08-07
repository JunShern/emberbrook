"""ds_shelf.py — BATHYMETRY AT THE DEEP-STAIRS REACH.
docs/plans/water-transparency.md, W1-W2, applied to the one pool floor the
tranche never reached.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/ds_shelf.py -- [save]
  ... -- revert save          (deletes the patch; the pool bed is untouched)

RUN tools/t2_water_shader.py AFTERWARDS — this is bathymetry, and the alpha that
reads it is BAKED, not evaluated.  This script prints that instruction and
refuses to pretend it did it.

WHAT WAS MEASURED (graphics round 3, item 2).  The round-3 worklist called the
deep-stairs sheet "a sheet the round-1 water restore missed".  IT IS NOT.  A
pixel ray-census replaying deep-stairs' own solved camera says the sheet is
`water_pool-mid`, and the master census says that sheet HAS the restored bake
(`Col` present, `t2ws` set, 8648 verts; manifest median 4.10 m, ramp scale
0.976).  The bake is there.  It has nothing to encode:

  * down-ray census of the bed under the camera's whole visible water band
    (x 38..58, y 21..31, walk meshes and water hidden): z = -3.90, the untouched
    `riverbed` slab, in 108 of 121 cells — a CONSTANT 4.10 m of depth;
  * the alpha those cells carry, sampled through the camera: p10 0.641,
    p50 0.970, p90 0.970, with 68.1% of the frame's water pixels at or above
    0.95.

One flat depth gives one flat alpha, which is exactly what the judge saw ("flat
untextured cyan plane, hard polygonal edges").  W2 built three shelves —
lockfive, boatyard, cottage-steps — nominated by `t2_probe_shore` against the
cameras that existed then; this reach was not one of them, and the plan's own
sentence still governs: **the bathymetry is the deliverable, the shader is the
cheap part.**

WHY A RELIEF PATCH AND NOT A FOURTH SHORE SHELF.  A shelf is a shore-parallel
strip welded to a bank, and there is no bank here to weld to: the deep-stairs
water is seen through gaps in a plank wharf, and the ray-cast that hunted a
crest across y 22.6..27.4 came back holding DRY LAND at 12 of 23 x stations
(the wharf ground, not a waterline).  An apron built off that would have filled
the pocket with a 3.4 m shoal.  So the patch does the one thing the measurement
asks for and nothing more: it replaces a single plane with a floor that varies,
deterministically, between DEEP_MIN and the slab, and it tapers to the slab at
its own border so the weld has no seam.  It never comes within SURF_KEEP of the
surface, so it cannot breach and cannot foul `wf_skiff_walk` (z 0.37), and it
never sinks below what the terrain already puts there (`bed + 0.06`, so no
z-fighting with the bank toe at y 25).

It is `mat_rock`, the material the bank already wears, for the reason W2 gives:
the material transition has to be invisible or the bed reads as a prop.
"""
import bpy, os, sys, json, math, random
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/ds_shelf.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

NAME = "t2w_bed_deep-stairs"
MAT = "mat_rock"
SURF = 0.20                 # water_pool-mid's surface
SLAB = -3.90                # the riverbed slab this reach sits on
X0, X1 = 36.0, 60.0
Y0, Y1 = 20.0, 32.0
STEP = 0.80
DEEP_MIN = 1.70             # the shallowest the new floor may be, in metres
SURF_KEEP = 0.75            # and never nearer the surface than this
EDGE = 2.4                  # metres over which the relief dies into the slab
JITTER = 0.14
SEED = 20260807

# two incommensurate wavelengths, so the floor never repeats inside the patch
WAVE = ((9.7, 6.3, 0.00), (4.9, 3.1, 1.37))

sc = bpy.context.scene

old = bpy.data.objects.get(NAME)
if REVERT:
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
        print("REMOVED %s" % NAME)
    else:
        print("%s not present — nothing to revert" % NAME)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

if old:
    bpy.data.objects.remove(old, do_unlink=True)
    print("(rebuilding: removed the previous %s)" % NAME)

hidden = []
for o in sc.objects:
    if o.type != 'MESH':
        continue
    if (o.name.startswith("walk_") or o.name.startswith("bar_")
            or any(s.material and s.material.name == "m_water" for s in o.material_slots)):
        if not o.hide_viewport:
            o.hide_viewport = True
            hidden.append(o.name)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def bed(x, y):
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, y, SURF - 0.05)),
                                            Vector((0, 0, -1)), distance=40.0)
    return (loc.z, ob.name) if hit else (None, None)


def taper(x, y):
    """1 in the middle, 0 at the border — the weld."""
    return min(1.0, (x - X0) / EDGE, (X1 - x) / EDGE,
               (y - Y0) / EDGE, (Y1 - y) / EDGE, 1.0) if (
        X0 <= x <= X1 and Y0 <= y <= Y1) else 0.0


rng = random.Random(SEED)
NX = int((X1 - X0) / STEP) + 1
NY = int((Y1 - Y0) / STEP) + 1
V, F, ONSLAB = [], [], []
slab_cells = 0
probe = 0
z_top = SURF - SURF_KEEP
for i in range(NX):
    x = X0 + i * STEP
    for j in range(NY):
        y = Y0 + j * STEP
        t = max(0.0, taper(x, y))
        h = 0.0
        for (lx, ly, ph) in WAVE:
            h += math.sin(x / lx * 2 * math.pi + ph) * math.cos(y / ly * 2 * math.pi + ph)
        h = (h / len(WAVE) + 1.0) / 2.0            # 0..1
        z = SLAB + (SURF - DEEP_MIN - SLAB) * h * t
        z += rng.uniform(-JITTER, JITTER) * t
        b, bn = bed(x, y)
        probe += 1
        clamped = False
        if b is not None:
            on_slab = abs(b - SLAB) < 0.05
            if on_slab:
                slab_cells += 1
            if b + 0.06 > z:
                z = b + 0.06
                clamped = not on_slab      # riding real terrain, not the slab
        z = min(z, z_top)
        V.append((x, y, z))
        ONSLAB.append(not clamped)
for i in range(NX - 1):
    for j in range(NY - 1):
        a = i * NY + j
        F.append((a, a + NY, a + NY + 1, a + 1))

me = bpy.data.meshes.new(NAME)
me.from_pydata(V, [], F)
me.validate()
mat = bpy.data.materials.get(MAT)
assert mat is not None, "material %s is not in this blend" % MAT
me.materials.append(mat)
ob = bpy.data.objects.new(NAME, me)
host = bpy.data.objects.get("riverbed")
coll = host.users_collection[0] if host and host.users_collection else sc.collection
coll.objects.link(ob)

for nm in hidden:
    o = bpy.data.objects.get(nm)
    if o is not None:
        o.hide_viewport = False

# ------------------------------------------------------------------ GATE ----
zs = [v[2] for v in V]
depths = sorted(SURF - z for z in zs)
print("=" * 78)
print("BEFORE: the bed under this patch was the flat slab in %d of %d probes "
      "(%.0f%%)" % (slab_cells, probe, 100.0 * slab_cells / probe))
print("%s: %d verts / %d quads  x %.1f..%.1f  y %.1f..%.1f  z %.2f..%.2f"
      % (NAME, len(V), len(F), min(v[0] for v in V), max(v[0] for v in V),
         min(v[1] for v in V), max(v[1] for v in V), min(zs), max(zs)))
print("  depth under the surface:  min %.2f  p25 %.2f  med %.2f  p75 %.2f  max %.2f m"
      % (depths[0], depths[len(depths) // 4], depths[len(depths) // 2],
         depths[3 * len(depths) // 4], depths[-1]))
assert max(zs) <= z_top + 1e-6, "the patch breaches the surface (max z %.3f)" % max(zs)
assert min(zs) >= SLAB - 0.02, "the patch sinks below the slab (min z %.3f)" % min(zs)
border = [abs(v[2] - (SLAB + 0.06)) for v, free in zip(V, ONSLAB) if free
          and (abs(v[0] - X0) < 1e-6 or abs(v[0] - X1) < 1e-6
               or abs(v[1] - Y0) < 1e-6 or abs(v[1] - Y1) < 1e-6)]
edge_off = max(border) if border else 0.0
print("  BREACH none (max z %.2f <= %.2f) · below-slab none · border weld: %d free "
      "border verts, off the slab by at most %.3f m (the rest sit on terrain that "
      "was already higher)" % (max(zs), z_top, len(border), edge_off))
assert edge_off <= 0.05, "the patch does not weld to the slab at its border"

print("  NEXT, and this script did NOT do it: re-run tools/t2_water_shader.py so")
print("  water_pool-mid's Col.a reads the new bed.  Compare its report against")
print("  tools/blends/districts/t2_water_shader.json — an unchanged median_depth")
print("  and ramp_scale is what proves no other camera's water moved.")

json.dump(dict(_doc=("GENERATED by tools/ds_shelf.py — bathymetry at the "
                     "deep-stairs reach. Run tools/t2_water_shader.py after it; "
                     "the alpha is baked, not evaluated."),
               generator="tools/ds_shelf.py",
               plan="docs/plans/water-transparency.md",
               object=NAME, material=MAT, surf=SURF, slab=SLAB,
               bbox=[X0, X1, Y0, Y1], step=STEP, deep_min=DEEP_MIN,
               surf_keep=SURF_KEEP, edge=EDGE, wave=WAVE, jitter=JITTER,
               seed=SEED, verts=len(V), quads=len(F),
               slab_probes=[slab_cells, probe],
               depth_min=round(depths[0], 2),
               depth_med=round(depths[len(depths) // 2], 2),
               depth_max=round(depths[-1], 2)),
          open(MANIFEST, "w"), indent=1)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
