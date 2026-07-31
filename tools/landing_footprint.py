"""landing_footprint.py — WHAT IS ACTUALLY BUILT UNDER AN `area` LANDMARK'S PAD.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/landing_footprint.py [-- --targets a,b --expand 3.0 --rects 3 --verify]

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
uses, so the two instruments cannot disagree. "Render-visible" is doing real work there and
is enforced by PASS_THROUGH below: the ray goes THROUGH the walk network and the other
non-drawn classes rather than stopping on them. A sample is LANDED when that hit is a solid
within 0.60 m of the foot (a landing is close under you; a deck four metres down is a
different tier, not this pad's floor). Then the LARGEST ALL-LANDED axis-aligned rectangle
is computed by the standard histogram scan — the honest rectangle, not the bounding box of
the landed samples, which for a scattered mask is just the square you started with.

THE COVER (added 2026-08-01, for the footprint stamp). One rectangle cannot describe an
L-shaped deck, and the ruled `footprint` schema is a LIST of rectangles. So the same scan
is run GREEDILY: take the largest all-landed rectangle, strike it out of the mask, repeat,
keeping only rectangles at least MIN_SIDE on both axes and MIN_AREA in plan. Every
rectangle it emits is all-landed by the same rule as the single one — the cover cannot
smuggle in a sample the tape would have refused. `coverFrac` is the share of the landed
mask the cover accounts for; what it leaves out is scatter too thin to be a deck.

`--expand M` grows the sampled window M metres beyond the pad square on all four sides:
the moorage's real staging stands OUTSIDE its own disc (locksfoot_build.py builds it
there on purpose), so the window that answers "what is built here" is wider than the pad.

READ-ONLY. Prints, and writes nothing.
"""
import bpy, json, math, sys
from mathutils import Vector
REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MAP = json.load(open(REPO + "/public/townmap/dellhollow.map.json"))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default):
    return argv[argv.index(name) + 1] if name in argv else default


sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
# THE CLASSES A PLAYER CANNOT SEE, and the ray must pass THROUGH them rather than stop on
# them.  This is walk_water_audit's NOT_DRAWN list, and it has to be, because the two
# instruments claim to share a rule: that audit filters the non-drawn meshes out of its
# index BEFORE casting, while `scene.ray_cast` has no such filter and returns whatever is
# nearest.  The first version of this file stopped on the first hit and then rejected it by
# name, which silently means "not landed" — so a deck built 0.02 m UNDER the walk ribbon it
# carries (which is how a connective landing has to be built, or it buries the ribbon) read
# as bare water.  It scored four correctly-built landings at 53-90% and would have refused
# to let them be stamped.
PASS_THROUGH = ("walk_", "bar_", "fx_", "cam", "CAM", "REF_", "KEY", "lm_")
WATER = ("water", "riverbed")
STEP = 0.2
MIN_SIDE = 0.8                   # a rectangle thinner than this is not a place to stand
MIN_AREA = 1.5                   # nor is a chip smaller than this
TARGETS = opt("--targets", None)
TARGETS = set(TARGETS.split(",")) if TARGETS else None
EXPAND = float(opt("--expand", "0"))
NRECT = int(opt("--rects", "3"))


def landed_at(x, y, top, depth=40.0):
    """Is the first thing a player would SEE under (x, y) a solid within 0.60 m of `top`?

    Returns (landed, drop) where `drop` is how far under `top` that surface is, or None.
    """
    z = top - 0.06
    left = depth
    for _ in range(24):
        hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg, Vector((x, y, z)), Vector((0, 0, -1)),
                                                 distance=left)
        if not hit or ob is None:
            return False, None
        if ob.name.startswith(PASS_THROUGH) or ob.hide_render:
            left -= (z - loc.z) + 1e-4
            z = loc.z - 1e-4
            if left <= 0:
                return False, None
            continue
        if ob.name.startswith(WATER):
            return False, top - loc.z
        return (top - loc.z) <= 0.60, top - loc.z
    return False, None


def largest_rect(grid, nx, ny):
    """Largest all-ones axis-aligned rectangle, histogram scan. -> (area, i0,i1,j0,j1)."""
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
    return best


def verify_rect(rect, top):
    """Is a STATED rect legal — all-landed on its own 0.2 m grid?  The map _doc's rule.

    The cover SEARCHES for rects; this CHECKS one that is already written down, which is the
    question that matters once a footprint has been stamped or a landing has been built under
    a rect the builder chose.  Same ray, same 0.60 m window, grid anchored on the rect's own
    corner because that is what "a 0.2 m grid over the rect" means with nothing else to
    anchor to.
    """
    x0, x1, y0, y1 = rect
    nx = max(1, int(round((x1 - x0) / STEP)))
    ny = max(1, int(round((y1 - y0) / STEP)))
    n = landed = 0
    worst = 0.0
    for j in range(ny + 1):
        for i in range(nx + 1):
            xx = min(x0 + i * STEP, x1)
            yy = min(y0 + j * STEP, y1)
            ok, drop = landed_at(xx, yy, top)
            n += 1
            if ok:
                landed += 1
                worst = max(worst, drop)
    return n, landed, worst


if "--verify" in argv:
    print("VERIFY — every stamped footprint rect against the map _doc's all-landed rule")
    bad = 0
    for l in MAP["landmarks"]:
        if l.get("class") != "area" or not l.get("footprint"):
            continue
        if TARGETS and l["id"] not in TARGETS:
            continue
        top = l["pos"][2] + 0.245
        for k, r in enumerate(l["footprint"]):
            n, landed, worst = verify_rect(r, top)
            mark = "OK  " if landed == n else "FAIL"
            if landed != n:
                bad += 1
            print("  %s %-15s r%d [%8.2f..%8.2f, %8.2f..%8.2f]  %4d samples, %4d landed "
                  "(%5.1f%%), deepest %.3f m under the pad top"
                  % (mark, l["id"], k, r[0], r[1], r[2], r[3], n, landed,
                     100.0 * landed / n, worst))
    print("  %d rect(s) fail the rule" % bad)
    sys.exit(0)

res = {}
for l in MAP["landmarks"]:
    if l.get("class") != "area" or "extent" not in l:
        continue
    if TARGETS and l["id"] not in TARGETS:
        continue
    rec = bpy.data.objects.get("walk_lm_" + l["id"])
    ws = [rec.matrix_world @ Vector(v) for v in rec.bound_box]
    x0, x1 = min(w.x for w in ws) - EXPAND, max(w.x for w in ws) + EXPAND
    y0, y1 = min(w.y for w in ws) - EXPAND, max(w.y for w in ws) + EXPAND
    top = max(w.z for w in ws)
    nx = int(round((x1 - x0) / STEP)) + 1
    ny = int(round((y1 - y0) / STEP)) + 1
    grid = []
    for j in range(ny):
        row = []
        for i in range(nx):
            xx = x0 + i * STEP
            yy = y0 + j * STEP
            ok, _drop = landed_at(xx, yy, top)   # a LANDING is close under the foot
            row.append(1 if ok else 0)
        grid.append(row)
    landed = sum(sum(rw) for rw in grid)
    a, r = largest_rect(grid, nx, ny)
    if not r:
        continue
    i0, i1, j0, j1 = r
    rect = [round(x0 + i0 * STEP, 2), round(x0 + i1 * STEP, 2),
            round(y0 + j0 * STEP, 2), round(y0 + j1 * STEP, 2)]
    w = rect[1] - rect[0]
    d = rect[3] - rect[2]
    # --- the greedy cover: strike each rectangle out and go again -----------
    work = [row[:] for row in grid]
    cover, covered = [], 0
    for _ in range(NRECT):
        aa, rr = largest_rect(work, nx, ny)
        if not rr:
            break
        ci0, ci1, cj0, cj1 = rr
        cw = (ci1 - ci0) * STEP
        cd = (cj1 - cj0) * STEP
        if cw < MIN_SIDE or cd < MIN_SIDE or cw * cd < MIN_AREA:
            break
        cover.append([round(x0 + ci0 * STEP, 2), round(x0 + ci1 * STEP, 2),
                      round(y0 + cj0 * STEP, 2), round(y0 + cj1 * STEP, 2)])
        for j in range(cj0, cj1 + 1):
            for i in range(ci0, ci1 + 1):
                work[j][i] = 0
        covered += aa
    res[l["id"]] = {"pad": [round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2)],
                    "padArea": round((x1 - x0) * (y1 - y0), 1), "padTop": round(top, 3),
                    "landingRect": rect, "landingSize": [round(w, 2), round(d, 2)],
                    "landingArea": round(w * d, 1),
                    "landedFrac": round(landed / (nx * ny), 3),
                    "cover": cover,
                    "coverArea": round(sum((c[1] - c[0]) * (c[3] - c[2]) for c in cover), 1),
                    "coverFrac": round(covered / landed, 3) if landed else 0.0}
    print("%-15s pad %-28s %5.1f m2  ->  landing %-28s %4.1f x %4.1f = %5.1f m2  (landed %.0f%% of the square)"
          % (l["id"], str(res[l['id']]['pad']), res[l['id']]['padArea'],
             str(rect), w, d, w * d, 100 * res[l['id']]['landedFrac']))
    for c in cover:
        print("%-15s   cover rect [%7.2f..%7.2f, %7.2f..%7.2f]  %4.1f x %4.1f = %5.1f m2"
              % ("", c[0], c[1], c[2], c[3], c[1] - c[0], c[3] - c[2],
                 (c[1] - c[0]) * (c[3] - c[2])))
    print("%-15s   cover %d rect(s) %.1f m2, %.0f%% of the landed mask"
          % ("", len(cover), res[l["id"]]["coverArea"], 100 * res[l["id"]]["coverFrac"]))
print()
print(json.dumps(res, indent=1))
