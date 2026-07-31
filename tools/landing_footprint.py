"""landing_footprint.py — WHAT IS ACTUALLY BUILT UNDER AN `area` LANDMARK'S PAD.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/landing_footprint.py

WHY. A map landmark of class `area` carries an `extent`, and the derive turns it into a
FILLED SQUARE of side 2*extent centred on pos. At the waterfront that square is parked on
the river: walk_water_audit (2026-08-01) found the town's four worst walk-on-water records
are exactly the four `area` pads — moorage, fish-dock, drying-decks, north-landing — and
locksfoot_build.py's own comment already said so out loud ("`walk_lm_moorage` is a FILLED
disc, so everything the moorage WORKS with has to stand off it").

The coordinator's ruling (stilt waterfront, 2026-08-01) is that each of those landmarks
gets a footprint MEASURED OFF THE BUILT LANDING rather than a default square. This is the
tape that measures it, so the number in the map is derived and can be re-derived.

METHOD. Over the pad's own extent, sample on a 0.2 m grid; from just under the pad's top
surface, ray DOWN and take the first RENDER-VISIBLE hit — the same rule walk_water_audit
uses, so the two instruments cannot disagree. A sample is LANDED when that hit is a solid
within 0.60 m of the foot (a landing is close under you; a deck four metres down is a
different tier, not this pad's floor). Then the LARGEST ALL-LANDED axis-aligned rectangle
is computed by the standard histogram scan — the honest rectangle, not the bounding box of
the landed samples, which for a scattered mask is just the square you started with.

READ-ONLY. Prints, and writes nothing.
"""
import bpy, json, math
from mathutils import Vector
REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MAP = json.load(open(REPO + "/public/townmap/dellhollow.map.json"))
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
SKIP = ("water_", "riverbed", "fx_", "walk_", "bar_")
STEP = 0.2
TARGETS = None   # None = every class-'area' landmark that has an extent
res = {}
for l in MAP["landmarks"]:
    if l.get("class") != "area" or "extent" not in l: continue
    if TARGETS and l["id"] not in TARGETS: continue
    rec = bpy.data.objects.get("walk_lm_" + l["id"])
    ws = [rec.matrix_world @ Vector(v) for v in rec.bound_box]
    x0, x1 = min(w.x for w in ws), max(w.x for w in ws)
    y0, y1 = min(w.y for w in ws), max(w.y for w in ws)
    top = max(w.z for w in ws)
    nx = int(round((x1 - x0) / STEP)) + 1
    ny = int(round((y1 - y0) / STEP)) + 1
    grid = []
    for j in range(ny):
        row = []
        for i in range(nx):
            xx = x0 + i * STEP; yy = y0 + j * STEP
            hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, Vector((xx, yy, top - 0.06)),
                                                    Vector((0, 0, -1)), distance=40.0)
            ok = bool(hit and ob and not ob.name.startswith(SKIP) and not ob.hide_render
                      and (top - loc.z) <= 0.60)   # a LANDING is close under the foot
            row.append(1 if ok else 0)
        grid.append(row)
    # maximal all-ones rectangle (histogram method)
    best = (0, None)
    h = [0] * nx
    for j in range(ny):
        for i in range(nx):
            h[i] = h[i] + 1 if grid[j][i] else 0
        st = []
        for i in range(nx + 1):
            cur = h[i] if i < nx else 0
            start = i
            while st and st[-1][1] >= cur:
                s, ht = st.pop()
                area = ht * (i - s)
                if area > best[0]:
                    best = (area, (s, i - 1, j - ht + 1, j))
                start = s
            st.append((start, cur))
    a, r = best
    if r:
        i0, i1, j0, j1 = r
        rect = [round(x0 + i0 * STEP, 2), round(x0 + i1 * STEP, 2),
                round(y0 + j0 * STEP, 2), round(y0 + j1 * STEP, 2)]
        w = rect[1] - rect[0]; d = rect[3] - rect[2]
        res[l["id"]] = {"pad": [round(x0,2), round(x1,2), round(y0,2), round(y1,2)],
                        "padArea": round((x1-x0)*(y1-y0),1), "padTop": round(top,3),
                        "landingRect": rect, "landingSize": [round(w,2), round(d,2)],
                        "landingArea": round(w*d,1),
                        "landedFrac": round(sum(sum(rw) for rw in grid)/(nx*ny),3)}
        print("%-15s pad %-28s %5.1f m2  ->  landing %-28s %4.1f x %4.1f = %5.1f m2  (landed %.0f%% of the square)"
              % (l["id"], str(res[l['id']]['pad']), res[l['id']]['padArea'],
                 str(rect), w, d, w*d, 100*res[l['id']]['landedFrac']))
print()
print(json.dumps(res, indent=1))
