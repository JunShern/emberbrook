"""gate_gorge_census.py — READ-ONLY measurement for the GATE GORGE FRAME lane.

  /Applications/Blender.app/Contents/MacOS/Blender -b \
      tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_gorge_census.py -- --out <json>

Answers three questions with ONE oracle (Blender's ray-cast against the
evaluated depsgraph — CLAUDE.md: the bake ray-cast is the only visibility
oracle) so nobody has to trust a bbox or a note:

  A. THE NORTH SLOT.  Down-rays on a 0.5 m grid over the strip between the gate
     tier's lip and the boatyard (x -6..40, y 6..32) from z = 45.  For each cell:
     does anything at all catch the ray, what object, at what z.  DAYLOG
     2026-08-02 recorded "863 of 3,111 cells hit NOTHING — a 5.1 x 32.5 m slot
     with no bottom" and left it OPEN; this re-measures it on today's master.

  B. THE DROP PROFILE.  Per 1 m column of x, the tier lip's y and z, the first
     y north of it where a ray hits again, and that hit's z — i.e. how the
     ground actually gets from the tier down to the boatyard today.

  C. WHAT THE GATE FRAME IS MADE OF.  First-hit object per pixel on a coarse
     grid through the SOLVED gate camera (same construction as
     cine_bake.build_cam: sensor_fit VERTICAL, angle_y = fov), with the plate's
     own luminance sampled alongside, so a region that reads BLACK in the plate
     can be NAMED instead of guessed at.

Writes JSON; prints a human summary.  Never saves the blend.
"""
import bpy, sys, json, math, os
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = None
for i, a in enumerate(argv):
    if a == "--out":
        OUT = argv[i + 1]

dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene


def cast(o, d, dist=400.0):
    hit, loc, nor, idx, obj, mat = sc.ray_cast(dg, o, d, distance=dist)
    return (hit, loc, obj)


# ------------------------------------------------------------------ A + B
X0, X1, DX = -6.0, 40.0, 0.5
Y0, Y1, DY = 6.0, 32.0, 0.5
cells = []
nx = int(round((X1 - X0) / DX)) + 1
ny = int(round((Y1 - Y0) / DY)) + 1
miss = 0
for i in range(nx):
    x = X0 + i * DX
    for j in range(ny):
        y = Y0 + j * DY
        hit, loc, obj = cast(Vector((x, y, 45.0)), Vector((0, 0, -1)), 200.0)
        if not hit:
            miss += 1
            cells.append([round(x, 2), round(y, 2), None, None])
        else:
            cells.append([round(x, 2), round(y, 2), round(loc.z, 3), obj.name])
print("A. DOWN-RAY CENSUS  x %.1f..%.1f  y %.1f..%.1f  step %.2f" % (X0, X1, Y0, Y1, DX))
print("   cells %d   MISS %d (%.1f%%)" % (len(cells), miss, 100.0 * miss / len(cells)))

# miss bbox
mx = [c[0] for c in cells if c[2] is None]
my = [c[1] for c in cells if c[2] is None]
if mx:
    print("   miss bbox  x %.1f..%.1f   y %.1f..%.1f" % (min(mx), max(mx), min(my), max(my)))

# per-column profile at 1 m
print()
print("B. PER-COLUMN DROP PROFILE (1 m columns)")
print("   x    lip_y  lip_z   |  gap_y0..gap_y1  |  land_y  land_z  land_obj")
prof = {}
for i in range(nx):
    x = X0 + i * DX
    if abs(x - round(x)) > 1e-6:
        continue
    col = [c for c in cells if abs(c[0] - x) < 1e-6]
    col.sort(key=lambda c: c[1])
    lip = None
    for c in col:
        if c[2] is not None and c[2] > 20.0:
            lip = c
    gap = [c for c in col if c[2] is None]
    after = None
    if gap:
        gy = max(g[1] for g in gap)
        for c in col:
            if c[1] > gy and c[2] is not None:
                after = c
                break
    prof[x] = dict(lip=lip, gap=[min(g[1] for g in gap), max(g[1] for g in gap)] if gap else None,
                   land=after)
    print("  %5.1f  %6s %6s  |  %13s  |  %6s %6s  %s" % (
        x,
        ("%.2f" % lip[1]) if lip else "--", ("%.2f" % lip[2]) if lip else "--",
        ("%.1f..%.1f" % (min(g[1] for g in gap), max(g[1] for g in gap))) if gap else "--",
        ("%.2f" % after[1]) if after else "--", ("%.2f" % after[2]) if after else "--",
        (after[3] if after else "--")))

# what the north side is made of
tal = {}
for c in cells:
    if c[3]:
        tal[c[3]] = tal.get(c[3], 0) + 1
print()
print("   objects catching the down-rays (top 20):")
for k, v in sorted(tal.items(), key=lambda kv: -kv[1])[:20]:
    print("     %-32s %5d" % (k, v))

# ------------------------------------------------------------------ C
CAM_POS = Vector((-15.487, 9.27, 36.601))
CAM_AIM = Vector((15.468, 6.017, 25.273))
FOV = 35.0
ASPECT = 1.75
GW, GH = 336, 192
f = (CAM_AIM - CAM_POS).normalized()
r = f.cross(Vector((0, 0, 1))).normalized()
up = r.cross(f)
tv = math.tan(math.radians(FOV) / 2.0)
th = tv * ASPECT
shot = {}
grid = []
for py in range(GH):
    yn = 1.0 - 2.0 * (py + 0.5) / GH
    for px in range(GW):
        xn = 2.0 * (px + 0.5) / GW - 1.0
        d = (f + r * (xn * th) + up * (yn * tv)).normalized()
        hit, loc, obj = cast(CAM_POS, d, 1400.0)
        nm = obj.name if hit else "__BACKGROUND__"
        shot[nm] = shot.get(nm, 0) + 1
        grid.append(nm)
tot = GW * GH
print()
print("C. GATE FRAME, first hit per pixel (%dx%d = %d rays)" % (GW, GH, tot))
for k, v in sorted(shot.items(), key=lambda kv: -kv[1])[:25]:
    print("   %-34s %6d  %5.2f%%" % (k, v, 100.0 * v / tot))

# top-left quadrant
tl = {}
for py in range(GH // 2):
    for px in range(GW // 2):
        nm = grid[py * GW + px]
        tl[nm] = tl.get(nm, 0) + 1
q = (GW // 2) * (GH // 2)
print()
print("   TOP-LEFT QUADRANT (%d rays):" % q)
for k, v in sorted(tl.items(), key=lambda kv: -kv[1])[:12]:
    print("   %-34s %6d  %5.2f%%" % (k, v, 100.0 * v / q))

if OUT:
    json.dump(dict(cells=cells, profile={str(k): v for k, v in prof.items()},
                   shot=shot, topleft=tl, grid=grid, gw=GW, gh=GH),
              open(OUT, "w"))
    print("\nSAVED %s" % OUT)
