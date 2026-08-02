"""gate_gorge_census2.py — READ-ONLY, pass 2 of the GATE GORGE FRAME census.

Pass 1 (`gate_gorge_census.py`) reported `fx_haze_east` as 57% of the gate
plate's top-left quadrant.  That object ships `hide_render = True`, so it is in
the depsgraph and NOT in the plate: a first-hit tally that counts it is a lie
about the frame.  This pass fixes the instrument three ways and re-asks:

  * objects with `hide_render` are hidden from the depsgraph before casting;
  * FX volume cards (`fx_*` / `mat_haze_*` / spray / smoke) are skipped so the
    tally reports the FIRST OPAQUE surface, which is what the plate shows
    (the distinction cliff-completion.md's tally2 was built on);
  * every hit records its distance and world point, so a region can be located
    in the world, not just named.

Also dumps world bboxes for a named object list and a fine north-slot profile.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_gorge_census2.py -- --out <json>
"""
import bpy, sys, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = None
for i, a in enumerate(argv):
    if a == "--out":
        OUT = argv[i + 1]

sc = bpy.context.scene

# ---- instrument fix 1: hide_render objects leave the depsgraph -------------
hidden = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.hide_render and not o.hide_viewport:
        o.hide_viewport = True
        hidden.append(o.name)
print("hidden from the cast (hide_render=True): %d  %s" % (len(hidden), hidden[:12]))
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def is_fx(name):
    n = name.lower()
    return n.startswith("fx_") or "haze" in n or "spray" in n or "smoke" in n


def first_opaque(o, d, budget=64, dist=1400.0):
    """FX volume cards are see-through in the plate; step past them."""
    p = Vector(o)
    total = 0.0
    for _ in range(budget):
        hit, loc, nor, idx, obj, mat = sc.ray_cast(dg, p, d, distance=dist - total)
        if not hit:
            return None, None, None
        step = (loc - p).length
        total += step
        if not is_fx(obj.name):
            return obj.name, loc, total
        p = loc + d * 0.01
        total += 0.01
    return "__BUDGET__", None, None


CAM_POS = Vector((-15.487, 9.27, 36.601))
CAM_AIM = Vector((15.468, 6.017, 25.273))
GW, GH = 448, 256
f = (CAM_AIM - CAM_POS).normalized()
r = f.cross(Vector((0, 0, 1))).normalized()
up = r.cross(f)
tv = math.tan(math.radians(35.0) / 2.0)
th = tv * 1.75

tal, grid = {}, []
for py in range(GH):
    yn = 1.0 - 2.0 * (py + 0.5) / GH
    for px in range(GW):
        xn = 2.0 * (px + 0.5) / GW - 1.0
        d = (f + r * (xn * th) + up * (yn * tv)).normalized()
        nm, loc, dist = first_opaque(CAM_POS, d)
        nm = nm or "__BACKGROUND__"
        tal[nm] = tal.get(nm, 0) + 1
        grid.append([nm, None if loc is None else [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)]])
tot = GW * GH
print("\nGATE FRAME — FIRST OPAQUE per pixel (%dx%d)" % (GW, GH))
for k, v in sorted(tal.items(), key=lambda kv: -kv[1])[:26]:
    print("   %-34s %6d  %5.2f%%" % (k, v, 100.0 * v / tot))

for label, x0, x1, y0, y1 in [("TOP-LEFT QUADRANT", 0, GW // 2, 0, GH // 2),
                              ("LEFT-OF-CUT COLUMN 0..0.424", 0, int(0.42407 * GW), 0, GH)]:
    sub = {}
    for py in range(y0, y1):
        for px in range(x0, x1):
            nm = grid[py * GW + px][0]
            sub[nm] = sub.get(nm, 0) + 1
    n = (x1 - x0) * (y1 - y0)
    print("\n   %s (%d rays):" % (label, n))
    for k, v in sorted(sub.items(), key=lambda kv: -kv[1])[:14]:
        print("     %-34s %6d  %5.2f%%" % (k, v, 100.0 * v / n))

# ---------------------------------------------------------------- bboxes
names = ["gate_ground", "gate_parapet", "gate_cliffface", "gate_yard", "gate_road",
         "yard_ground", "riverbed", "by_v10_apron", "bank_netloft", "seam_bank",
         "cliff_east_closure", "cliff_town_b", "cliff_town_skirt", "fx_haze_east",
         "fx_haze_south", "water_pool-downstream", "water_pool-mid", "gate_palisade",
         "walk_lm_porters-yard", "yard_planking", "gate_winch", "gate_clutter"]
bb = {}
for nm in names:
    o = bpy.data.objects.get(nm)
    if not o:
        bb[nm] = None
        continue
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    bb[nm] = dict(min=[round(min(p[i] for p in pts), 2) for i in range(3)],
                  max=[round(max(p[i] for p in pts), 2) for i in range(3)],
                  verts=len(o.data.vertices) if o.type == 'MESH' else 0,
                  hide_render=o.hide_render)
print("\nBBOXES")
for nm in names:
    v = bb[nm]
    print("   %-24s %s" % (nm, "ABSENT" if v is None else
                           "%s .. %s  v=%d hr=%s" % (v["min"], v["max"], v["verts"], v["hide_render"])))

# --------------------------------------------- fine north-slot profile
print("\nNORTH SLOT, 0.25 m, x 0..34")
prof = {}
for xi in range(0, 137):
    x = xi * 0.25
    ys = []
    y = 8.0
    while y <= 26.0:
        hit, loc, nor, idx, obj, mat = sc.ray_cast(dg, Vector((x, y, 45.0)), Vector((0, 0, -1)), distance=200.0)
        ys.append((round(y, 2), None if not hit else round(loc.z, 3), None if not hit else obj.name))
        y += 0.25
    prof["%.2f" % x] = ys
gapstat = []
for k, ys in prof.items():
    g = [a for a in ys if a[1] is None]
    if g:
        gapstat.append((float(k), min(a[0] for a in g), max(a[0] for a in g), len(g)))
print("   columns with a gap: %d of %d" % (len(gapstat), len(prof)))
if gapstat:
    print("   gap y range overall: %.2f .. %.2f" % (min(g[1] for g in gapstat), max(g[2] for g in gapstat)))
    print("   x      gap_y0  gap_y1  cells")
    for g in gapstat[::4]:
        print("   %5.2f  %6.2f  %6.2f  %4d" % g)

if OUT:
    json.dump(dict(tal=tal, grid=grid, gw=GW, gh=GH, bb=bb, prof=prof, hidden=hidden), open(OUT, "w"))
    print("\nSAVED %s" % OUT)
