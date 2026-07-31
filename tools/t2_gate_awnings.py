"""t2_gate_awnings.py — THE GATE STAIR'S NAMED OCCLUDERS, TAKEN OFF IT.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t2_gate_awnings.py -- [dry] [save] [revert]

WHAT WAS WRONG, MEASURED THREE WAYS BEFORE ANYTHING MOVED.
`tools/t2_color_pops.py` placed two pop-of-colour awnings from screen-space probe
rectangles that carried no idea of what was UNDER them:

    t2c_G3_awning_tollyard   x 18.10..20.90  y 4.50.. 6.55  z 23.65..25.70
    t2c_GB5_road_marketrow   x 19.80..24.20  y 5.90.. 9.15  z 22.95..25.00

The gate road's top surface is z 24.20 and the walk graph runs at z 24.00, so both
canopies hung 0.8-1.5 m over a carriageway — chest height — with their posts driven
a metre THROUGH it, parked over the town's arrival staircase.  Three standing
instruments had already said so, independently:

  * `geometry_audit` region 14,28,0,8 — G3 inside GB5, inside_frac 0.208, depth 1.24 m
  * `master_walk_qa`  region 14,28,0,8 — GB5 a COVERAGE offender (37 samples) and a
    HEADROOM offender (44 samples, 9.40%); G3 31 samples, 6.62%
  * `tools/t2_occluder_census.py` from the SOLVED gate camera — of 82 rays at the
    town's arrival staircase (`valley-gate__inn`), G3 takes 19.5% and GB5 14.6%,
    against 7.3% CLEAR.  The pair is 34.1% of the block, and they sit BEHIND the rim
    foliage, which is why trimming the planting plateaued at +2.5 points.

THE SITE IS SEARCHED, NOT CHOSEN.  A bay is offered only where ALL of these hold:

  1  flat GROUND — `gate_ground`/`gate_road`/`shelf_ground` under every sample of
     the footprint, within the gate bench and varying by less than FLAT;
  2  >= WALK_CLEAR of the route ribbon in xy — a stall stands BESIDE a road;
  3  the whole VOLUME empty: a 5 x 5 grid of up-rays to HEADROOM plus two
     horizontal sweeps at ridge and counter height;
  4  ZERO of 100 camera->staircase sightlines crossed, from the SOLVED `gate` and
     `shelf-west`, at feet and head height, by exact segment/AABB;
  5  inside the gate frustum with margin, ranked by the frame the canopy covers.

Two kinds of bay: free-standing (four posts) and WALL-MOUNTED (front posts on
measured ground, brackets into a ray-verified host), because an awning over a
counter is normally fixed to a wall and the parcel has almost no open ground.

WHAT THE DISTRICT ANSWERED, and every line of it cost a revision:

  * A down-ray dropped from z 34 over the gate road hits BUNTING, the arch beam or
    a rim crown long before the road, so "what is the ground here" answered ARCH for
    most of the parcel.  DOWN_TOP fixes it.
  * A 3.0 m ridge does not fit under a street strung with bunting at z 24-28:
    3.1 m of demanded clear air cut the one usable verge into 0.5 m offcuts.
  * `gate_yard` is NOT ground.  It presents a walkable-looking top face at z 24.20
    and is a built assembly spanning z 23.86..28.31; with it in GROUNDY the search
    put both stalls INSIDE the Porters' Yard and geometry_audit found them there
    (G3 frac 0.412 depth 0.81, GB5 frac 0.212 depth 0.58).  Its footprint (x < 12)
    is now excluded outright — a stall does not belong in somebody else's building.
  * AND THEN THE PARCEL SAID NO.  With those three corrections the gate district
    contains exactly ONE site satisfying every constraint.  G3 takes it, at 35% of
    its old canopy area; GB5 has nowhere lawful to stand and is REMOVED rather than
    squeezed somewhere that fails an audit.  The colour cost is re-measured with
    `tools/t2_probe_chroma.py` against pops-of-colour's [5%, 11%] band, not assumed.

OWNERSHIP.  Both ids are HANDED OFF from tools/t2_color_pops.py, which lists them in
HANDED_OFF and no longer builds them, so a re-run of the pops pass cannot put them
back on the staircase.

`revert` deletes what this script built and rebuilds nothing.
"""
import bpy, sys, os, json, math
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
DRY = "dry" in argv
REVERT = "revert" in argv
MANIFEST = ROOT + "/tools/blends/districts/t2_gate_awnings.json"
COLL = "DIST_legibility"
EDGE = "valley-gate__inn"

CINE = json.load(open(ROOT + "/public/assets/scenes/del-cine/cine.json"))
MAP = json.load(open(ROOT + "/public/townmap/dellhollow.map.json"))
LM = {l["id"]: l for l in MAP["landmarks"]}
CAM = {c["id"]: c for c in CINE["cameras"]}

# --------------------------------------------------------------- the two stalls
# `shapes` are (half-width ALONG the stall front, half-depth OUT from it), offered
# largest first: the verge pockets are 1.2-2.0 m deep, so a 3.2 m-deep awning has
# nowhere to stand and the ladder ends small.  `area` is the id's ORIGINAL canopy
# area, kept only as the target to report against — it is not a promise, and what
# was actually recovered is printed and written to the manifest.  `prefer` is the
# search's tie-breaker anchor, not its answer.
STALLS = [
    {"id": "G3_awning_tollyard", "paint": "mat_shelf_paint_teal",
     "area": 2.80 * 2.00, "max_bays": 3,
     "shapes": [(1.20, 0.90), (1.05, 0.80), (0.90, 0.70), (0.80, 0.62)],
     "prefer": (15.0, 7.60), "note": "awning by toll table"},
    {"id": "GB5_road_marketrow", "paint": "mat_shelf_paint_rust",
     "area": 4.40 * 3.20, "max_bays": 6,
     "shapes": [(1.20, 0.90), (1.05, 0.80), (0.90, 0.70), (0.80, 0.62)],
     "prefer": (13.0, 8.00), "note": "toll-road awning row"},
]
BAY_GAP = 0.35                   # metres of daylight between neighbouring bays
PREFIX = "t2c_"
TIMBER = "mat_timber"

GZ_LO, GZ_HI = 23.40, 24.80      # the gate bench: road top 24.20, yard a little over
FLAT = 0.45                      # ground may not vary more than this under a stall
WALK_CLEAR = 0.25                # metres of xy separation from any walk_/bar_ mesh.
                                 # The walk meshes are the ROUTE RIBBON, not the
                                 # carriageway: the gate road is 11 m wide and its
                                 # ribbon is 1.6 m of it. What master_walk_qa [3]
                                 # actually forbids is a prop OVER a walk top face,
                                 # so the rule is "not on the ribbon" with a margin,
                                 # and 0.80 leaves no site at all between the ribbon
                                 # (y <= 6.43) and the rim parapet (y >= 9.74).
HEADROOM = 2.80                  # clear air needed over the footprint to build in
EAVE = 2.25                      # canopy front underside, over local ground
RIDGE = 2.65                     # canopy back edge
VALANCE = 0.25                   # valance hem at 2.00 m — head height for a 1.7 m
                                 # character, and the stall stands off the route
                                 # ribbon anyway, so master_walk_qa [4] never
                                 # samples under it.  A 3.0 m ridge was the first
                                 # take and it does not fit: the gate street is
                                 # strung with bunting at z 24-28, and demanding
                                 # 3.1 m of empty air under it cut the one usable
                                 # verge into 0.5 m offcuts.
COUNTER = 0.95
NDC = 0.80                       # keep the canopy this far inside the gate frame

SKIP = ("walk_", "bar_", "fx_", "cam", "CAM", "REF_", "GA_SRC_", "KEY", "lm_")
# GROUND MEANS GROUND.  `gate_yard` was in this list for one revision and it cost two
# geometry_audit offenders: the Porters' Yard is a built ASSEMBLY whose bbox spans
# z 23.86..28.31 and which happens to present a walkable-looking top face at 24.20, so
# a stall standing "on" it stood INSIDE it — G3 frac 0.412 depth 0.81, GB5 frac 0.212
# depth 0.58.  A surface you may stand on is not the same claim as a volume you may
# build in, and this list is the second claim.
GROUNDY = ("gate_ground", "gate_road", "shelf_ground")

sc = bpy.context.scene
coll = bpy.data.collections.get(COLL) or sc.collection

# ------------------------------------------------------------------- revert ---
if REVERT:
    n = 0
    for s in STALLS:
        ob = bpy.data.objects.get(PREFIX + s["id"])
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me.users == 0:
                bpy.data.meshes.remove(me)
            n += 1
    print("reverted: %d stalls removed" % n)
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("saved")
    sys.exit(0)

# ------------------------------------------------------- record the before-state
def wbb(ob):
    ws = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return [round(min(p.x for p in ws), 3), round(max(p.x for p in ws), 3),
            round(min(p.y for p in ws), 3), round(max(p.y for p in ws), 3),
            round(min(p.z for p in ws), 3), round(max(p.z for p in ws), 3)]


before = {}
for s in STALLS:
    ob = bpy.data.objects.get(PREFIX + s["id"])
    before[s["id"]] = {"bbox": wbb(ob), "verts": len(ob.data.vertices)} if ob else None
    print("before  %-24s %s" % (s["id"], before[s["id"]]))

# ------------------------------------------------- pull the offenders + helpers
hidden = []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    mine = o.name in [PREFIX + s["id"] for s in STALLS]
    if mine or o.hide_render or o.name.startswith(SKIP):
        if not o.hide_viewport:
            o.hide_viewport = True
            hidden.append(o.name)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

walks = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("walk_", "bar_")):
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        walks.append((min(p.x for p in ws), max(p.x for p in ws),
                      min(p.y for p in ws), max(p.y for p in ws),
                      min(p.z for p in ws), max(p.z for p in ws)))


DOWN_TOP = 26.0                  # START THE GROUND RAY BELOW THE OVERHEAD DRESSING.
                                 # A ray dropped from z 34 over the gate road hits
                                 # gate_bunting (z 23.6..28.2), the arch beam
                                 # (to 29.9) or a rim crown long before the road,
                                 # so "what is the ground here" answered ARCH for
                                 # most of the parcel and the verge came back
                                 # sliced into 1 m strips that no stall could fit.
                                 # Overhead obstruction is `up_clear`'s question,
                                 # not the ground ray's.


def down(x, y, top=DOWN_TOP, reach=22.0):
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((x, y, top)), Vector((0, 0, -1)), distance=reach)
    return (loc.z, ob.name if ob else "?") if hit else (None, None)


def up_clear(x, y, z0, reach):
    hit, *_ = sc.ray_cast(dg, Vector((x, y, z0 + 0.06)), Vector((0, 0, 1)), distance=reach)
    return not hit


def walk_dist(x0, x1, y0, y1):
    d = 99.0
    for b in walks:
        dx = max(b[0] - x1, 0.0, x0 - b[1])
        dy = max(b[2] - y1, 0.0, y0 - b[3])
        d = min(d, math.hypot(dx, dy))
    return d


# ---------------------------------------------------- the staircase, and the rays
def stations(key, n=24):
    fr, to = key.split("__")
    e = next(x for x in MAP["edges"] if x["from"] == fr and x["to"] == to)
    pts = [LM[fr]["pos"]] + (e.get("waypoints") or []) + [LM[to]["pos"]]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L, out = cum[-1], []
    for i in range(n + 1):
        s = L * i / n
        j = max(0, min(len(pts) - 2, next((k for k in range(len(cum) - 1) if cum[k + 1] >= s), len(pts) - 2)))
        t = (s - cum[j]) / ((cum[j + 1] - cum[j]) or 1.0)
        a, b = pts[j], pts[j + 1]
        out.append(Vector([a[i2] + (b[i2] - a[i2]) * t for i2 in range(3)]))
    return out


ST = stations(EDGE)
EYES = [Vector(CAM[c]["pos"]) for c in ("gate", "shelf-west")]
SIGHT = [(eye, Vector((s.x, s.y, s.z + dz)))
         for eye in EYES for s in ST for dz in (0.05, 1.70)]


def rays_crossed(x0, x1, y0, y1, z0, z1):
    """How many camera->staircase sightlines pass through this box.  A segment/AABB
    slab test: exact, and the constraint that has to be ZERO."""
    n = 0
    for eye, tgt in SIGHT:
        d = tgt - eye
        t0, t1 = 0.0, 1.0
        ok = True
        for lo, hi, o, dd in ((x0, x1, eye.x, d.x), (y0, y1, eye.y, d.y), (z0, z1, eye.z, d.z)):
            if abs(dd) < 1e-9:
                if o < lo or o > hi:
                    ok = False
                    break
                continue
            a, b = (lo - o) / dd, (hi - o) / dd
            if a > b:
                a, b = b, a
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                ok = False
                break
        if ok:
            n += 1
    return n


# ------------------------------------------------------------ the gate frustum
GC = CAM["gate"]
_eye, _aim = Vector(GC["pos"]), Vector(GC["aim"])
_fwd = (_aim - _eye).normalized()
_right = _fwd.cross(Vector((0, 0, 1))).normalized()
_up = _right.cross(_fwd).normalized()
_ar = GC["depth"]["width"] / GC["depth"]["height"]
_tan = math.tan(math.radians(GC["fov"]) / 2.0)      # cine fov is the VERTICAL half-angle*2


def ndc(p):
    v = Vector(p) - _eye
    f = v.dot(_fwd)
    if f <= 0.01:
        return None
    return (v.dot(_right) / (f * _tan * _ar), v.dot(_up) / (f * _tan), f)


# ============================================================ the site search ==
# ONE GENERATOR, TWO KINDS OF BAY, and the second kind is here because the parcel
# said so.  A free-standing stall needs a whole rectangle of open, flat,
# ribbon-clear, head-clear ground, and the gate parcel contains exactly one:
# x 4.25..7.75, y 1.75..3.00 — 3.5 x 1.25 m, enough for three small bays between
# the two ids and nowhere near their 19.7 m2 of canopy.  An awning does not have
# to stand in the open, though: the ordinary one is FIXED TO A WALL over the
# counter it shades, needing ground only under its two front posts.  So the
# search offers both and takes whatever the district can actually carry.
print("\n" + "=" * 78)
print("SITE SEARCH — %d sightlines to %s from gate + shelf-west" % (len(SIGHT), EDGE))
print("=" * 78)

NORMALS = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)]


def solid_behind(bx, by, z, nx, ny, reach=0.55):
    """Is there a wall immediately behind this back edge?  Returns the object, or
    None.  Ground, planting and the route ribbon are not walls."""
    hit, loc, nrm, fi, ob, mw = sc.ray_cast(dg, Vector((bx + nx * 0.04, by + ny * 0.04, z)),
                                            Vector((-nx, -ny, 0)), distance=reach)
    if not hit or ob is None:
        return None
    n = ob.name
    if n in GROUNDY or n.startswith(("veg_", "walk_", "bar_", "fx_")):
        return None
    return n


chosen = []
for s in STALLS:
    px, py = s["prefer"]
    cands = []
    rej = {"ground": 0, "flat": 0, "walk": 0, "head": 0, "sight": 0, "frame": 0, "back": 0}
    for hw, hd in s["shapes"]:
      for nx, ny in NORMALS:
        tx, ty = -ny, nx                       # tangent along the wall / stall front
# THE PORTERS' YARD IS EXCLUDED BY ITS FOOTPRINT, not by hoping a ray misses it.
# x < 12 is `gate_yard` + `gate_gatehouse`: a dense built assembly of decking,
# posts, tarps and mule lines with a walkable-looking top face at z 24.20. Two
# revisions of this search kept finding "open ground" inside it, and geometry_audit
# kept finding the stalls inside it back. A stall does not belong in somebody
# else's building; the search does not get to look there.
        for ix in range(int(12.0 * 4), int(27.0 * 4) + 1):
          cx = ix / 4.0
          for iy in range(int(0.5 * 4), int(12.0 * 4) + 1):
            cy = iy / 4.0
            # front edge (the eave, where the posts stand) and back edge (the ridge)
            fx, fy = cx + nx * hd, cy + ny * hd
            bx, by = cx - nx * hd, cy - ny * hd
            # 1. ground under the two FRONT posts, always
            gs = []
            bad = False
            for st in (-0.94, 0.0, 0.94):
                z, nm = down(fx + tx * hw * st, fy + ty * hw * st)
                if z is None or not (GZ_LO <= z <= GZ_HI) or nm not in GROUNDY:
                    bad = True
                    break
                gs.append(z)
            if bad:
                rej["ground"] += 1
                continue
            gz = max(gs)
            # 2. WALL or OPEN GROUND behind?
            kind = None
            host = solid_behind(bx, by, gz + RIDGE - 0.20, nx, ny)
            if host and all(solid_behind(bx + tx * hw * st, by + ty * hw * st,
                                         gz + RIDGE - 0.20, nx, ny) == host
                            for st in (-0.85, 0.85)):
                kind = "wall"
            else:
                bg = []
                for st in (-0.94, 0.0, 0.94):
                    z, nm = down(bx + tx * hw * st, by + ty * hw * st)
                    if z is None or not (GZ_LO <= z <= GZ_HI) or nm not in GROUNDY:
                        bg = None
                        break
                    bg.append(z)
                if bg is None:
                    rej["back"] += 1
                    continue
                gs += bg
                gz = max(gs)
                kind = "ground"
            if (max(gs) - min(gs)) > FLAT:
                rej["flat"] += 1
                continue
            x0, x1 = sorted((cx - abs(tx) * hw - abs(nx) * hd, cx + abs(tx) * hw + abs(nx) * hd))
            y0, y1 = sorted((cy - abs(ty) * hw - abs(ny) * hd, cy + abs(ty) * hw + abs(ny) * hd))
            # 3. never over the route ribbon
            dw = walk_dist(x0, x1, y0, y1)
            if dw < WALK_CLEAR:
                rej["walk"] += 1
                continue
            # 4. THE WHOLE VOLUME MUST BE EMPTY, sampled densely enough to find a beam
            #    between two columns.  Three columns missed the Porters' Yard's own
            #    structure standing 0.9 m off the sampled line and the stalls were
            #    built INSIDE it; this is a 5 x 5 grid over the full footprint (a wall
            #    bay skips only the 15% strip against its own host) plus two horizontal
            #    sweeps at ridge and counter height, which is what catches an overhang
            #    no vertical ray meets.
            span = ([0.15 + 0.85 * k / 4 for k in range(5)] if kind == "wall"
                    else [-1.0 + 2.0 * k / 4 for k in range(5)])
            cross = [-0.95 + 1.90 * k / 4 for k in range(5)]
            okair = True
            for u in span:
                for st in cross:
                    ax = cx + nx * hd * u + tx * hw * st
                    ay = cy + ny * hd * u + ty * hw * st
                    if not up_clear(ax, ay, gz - 0.02, HEADROOM):
                        okair = False
                        break
                if not okair:
                    break
            if okair:
                for h in (RIDGE - 0.05, COUNTER):
                    for st in cross:
                        s0 = Vector((cx + nx * hd * -1.02 + tx * hw * st,
                                     cy + ny * hd * -1.02 + ty * hw * st, gz + h))
                        hit, loc, nr2, fi, ob, mw = sc.ray_cast(
                            dg, s0, Vector((nx, ny, 0.0)), distance=2.04 * hd)
                        # a wall bay is ALLOWED to find its own host on the way in
                        if hit and not (kind == "wall" and (loc - s0).length < 0.12):
                            okair = False
                            break
                    if not okair:
                        break
            if not okair:
                rej["head"] += 1
                continue
            # 5. out of every sightline to the staircase
            if rays_crossed(x0, x1, y0, y1, gz - 0.05, gz + RIDGE + 0.05):
                rej["sight"] += 1
                continue
            # 6. in the gate frame, scored by the frame the canopy covers
            corners = [(fx + tx * hw, fy + ty * hw, gz + EAVE),
                       (fx - tx * hw, fy - ty * hw, gz + EAVE),
                       (bx - tx * hw, by - ty * hw, gz + RIDGE),
                       (bx + tx * hw, by + ty * hw, gz + RIDGE)]
            nd = [ndc(c) for c in corners]
            if any(c is None or abs(c[0]) > NDC or abs(c[1]) > NDC for c in nd):
                rej["frame"] += 1
                continue
            us = [c[0] for c in nd]
            vs = [c[1] for c in nd]
            area = (max(us) - min(us)) * (max(vs) - min(vs)) / 4.0
            pref = math.hypot(cx - px, cy - py)
            cands.append({"kind": kind, "host": host, "at": (cx, cy, gz), "n": (nx, ny),
                          "half": (hw, hd), "d_walk": round(dw, 2), "frame": area,
                          "pref": pref, "box": (x0, x1, y0, y1)})
    # biggest canopy first, then the one that covers most frame, then nearest anchor
    cands.sort(key=lambda c: (-c["half"][0] * c["half"][1], c["pref"], -c["frame"]))
    print("  %-22s rejected: %s   (%d sites passed)" % (s["id"], rej, len(cands)))
    if cands:
        print("     passing hosts: %s"
              % sorted({(c["kind"], str(c["host"])) for c in cands})[:10])
    if not cands:
        print("  !! %s: NO SITE satisfies the constraints" % s["id"])
        sys.exit(1)
    bays, got = [], 0.0
    for c in cands:
        if len(bays) >= s["max_bays"] or got >= s["area"] * 0.98:
            break
        hw, hd = c["half"]
        a = 4 * hw * hd
        if got + a > s["area"] * 1.15:
            continue
        clash = False
        for o in [b for st in chosen for b in st["bays"]] + bays:
            ox0, ox1, oy0, oy1 = o["box"]
            if not (c["box"][1] + BAY_GAP < ox0 or c["box"][0] - BAY_GAP > ox1
                    or c["box"][3] + BAY_GAP < oy0 or c["box"][2] - BAY_GAP > oy1):
                clash = True
                break
        if clash:
            continue
        bays.append(c)
        got += a
    # A STALL THAT CANNOT BE LAWFULLY PLACED IS NOT PLACED. The parcel is allowed
    # to say no: once `gate_yard` stopped counting as ground and the Porters' Yard
    # footprint was excluded, the gate district contains exactly ONE site that
    # satisfies every constraint, and one site cannot hold two market rows. The id
    # that misses out is DELETED rather than squeezed in somewhere that fails an
    # audit — a coloured sheet nobody can justify is worse than a missing one, and
    # the colour cost is re-measured with t2_probe_chroma instead of assumed.
    if not bays:
        print("  !! %s: NO LAWFUL SITE — this id will be removed, not relocated" % s["id"])
        chosen.append({"id": s["id"], "paint": s["paint"], "bays": [],
                       "area_m2": 0.0, "area_target_m2": round(s["area"], 2),
                       "frame_pct": 0.0, "note": s["note"], "removed": True})
        continue
    for b in bays:
        print("     bay %-6s host %-20s at (%5.2f,%5.2f) g %.2f  n (%+.0f,%+.0f)  "
              "%.2f x %.2f m  d_walk %.2f  frame %.3f%%"
              % (b["kind"], str(b["host"])[:20], b["at"][0], b["at"][1], b["at"][2],
                 b["n"][0], b["n"][1], 2 * b["half"][0], 2 * b["half"][1],
                 b["d_walk"], 100 * b["frame"]))
    print("     %-22s recovered %.2f m2 of %.2f (%.0f%%) in %d bay(s)"
          % (s["id"], got, s["area"], 100 * got / s["area"], len(bays)))
    chosen.append({"id": s["id"], "paint": s["paint"], "bays": bays,
                   "area_m2": round(got, 2), "area_target_m2": round(s["area"], 2),
                   "frame_pct": round(100 * sum(b["frame"] for b in bays), 4),
                   "note": s["note"]})


if DRY:
    for n in hidden:
        ob = bpy.data.objects.get(n)
        if ob:
            ob.hide_viewport = False
    print("\ndry run — nothing built")
    sys.exit(0)

# =================================================================== the build ==
def quad(v, f, mi, k, a, b, c, d):
    i = len(v)
    v += [tuple(a), tuple(b), tuple(c), tuple(d)]
    f.append((i, i + 1, i + 2, i + 3))
    mi.append(k)


def boxv(v, f, mi, k, ctr, ex, ey, ez):
    i = len(v)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                v.append(tuple(Vector(ctr) + Vector(ex) * sx + Vector(ey) * sy + Vector(ez) * sz))

    def p(a, b, c):
        return i + 4 * a + 2 * b + c
    f += [(p(0, 0, 0), p(0, 1, 0), p(1, 1, 0), p(1, 0, 0)),
          (p(0, 0, 1), p(1, 0, 1), p(1, 1, 1), p(0, 1, 1)),
          (p(0, 0, 0), p(1, 0, 0), p(1, 0, 1), p(0, 0, 1)),
          (p(1, 0, 0), p(1, 1, 0), p(1, 1, 1), p(1, 0, 1)),
          (p(1, 1, 0), p(0, 1, 0), p(0, 1, 1), p(1, 1, 1)),
          (p(0, 1, 0), p(0, 0, 0), p(0, 0, 1), p(0, 1, 1))]
    mi += [k] * 6


def bay(v, f, mi, KP, KT, b, j):
    """A stall, not a sheet.  Front posts standing on the ground the ray found, a
    canopy sloping from the ridge at the back to the eave at the front, a valance,
    a plank counter and two crates.  A `wall` bay carries its back edge on two
    brackets into its host instead of on two more posts — which is what an awning
    over a counter actually is, and it is the only kind this parcel has room for
    in quantity."""
    cx, cy, gz = b["at"]
    hw, hd = b["half"]
    nx, ny = b["n"]
    tx, ty = -ny, nx
    T, N = Vector((tx, ty, 0.0)), Vector((nx, ny, 0.0))
    C = Vector((cx, cy, 0.0))
    grounds = []

    def at(u, w):                     # u along the wall (-1..1), w out from it
        p = C + T * (hw * u) + N * (hd * w)
        return p.x, p.y

    # --- front posts, always: they are what makes it stand rather than hover
    for su in (-0.94, 0.94):
        x, y = at(su, 0.94)
        g, _ = down(x, y)
        g = gz if g is None else g
        grounds.append(g)
        top = gz + EAVE
        boxv(v, f, mi, KT, (x, y, (g + top) / 2), (0.055, 0, 0), (0, 0.055, 0),
             (0, 0, (top - g) / 2))
    if b["kind"] == "ground":
        for su in (-0.94, 0.94):
            x, y = at(su, -0.94)
            g, _ = down(x, y)
            g = gz if g is None else g
            grounds.append(g)
            top = gz + RIDGE
            boxv(v, f, mi, KT, (x, y, (g + top) / 2), (0.055, 0, 0), (0, 0.055, 0),
                 (0, 0, (top - g) / 2))
    else:
        # two brackets from the ridge back into the host wall: a face-touch, which
        # geometry_audit scores at inside_frac ~ 0 and depth ~ 0, not an offence.
        for su in (-0.88, 0.88):
            x0b, y0b = at(su, -1.0)
            x1b, y1b = at(su, -0.55)
            boxv(v, f, mi, KT, ((x0b + x1b) / 2, (y0b + y1b) / 2, gz + RIDGE - 0.10),
                 (abs(tx) * 0.05 + abs(nx) * (hd * 0.23), 0, 0),
                 (0, abs(ty) * 0.05 + abs(ny) * (hd * 0.23), 0), (0, 0, 0.05))

    # --- the canopy: ridge at the back, eave at the front
    p00 = C + T * (-hw) + N * (-hd)
    p10 = C + T * (hw) + N * (-hd)
    p11 = C + T * (hw) + N * (hd)
    p01 = C + T * (-hw) + N * (hd)
    quad(v, f, mi, KP, (p00.x, p00.y, gz + RIDGE), (p10.x, p10.y, gz + RIDGE),
         (p11.x, p11.y, gz + EAVE), (p01.x, p01.y, gz + EAVE))
    quad(v, f, mi, KP, (p01.x, p01.y, gz + EAVE), (p11.x, p11.y, gz + EAVE),
         (p11.x, p11.y, gz + EAVE - VALANCE), (p01.x, p01.y, gz + EAVE - VALANCE))

    # --- the counter, a plank top on two trestles, under the front half
    ux, uy = at(0.0, 0.30)
    ex = (abs(tx) * hw * 0.88 + abs(nx) * min(0.34, hd * 0.42))
    ey = (abs(ty) * hw * 0.88 + abs(ny) * min(0.34, hd * 0.42))
    boxv(v, f, mi, KT, (ux, uy, gz + COUNTER), (ex, 0, 0), (0, ey, 0), (0, 0, 0.045))
    for su in (-0.72, 0.72):
        lx, ly = at(su, 0.30)
        boxv(v, f, mi, KT, (lx, ly, gz + COUNTER / 2),
             (abs(tx) * 0.05 + abs(nx) * min(0.26, hd * 0.34), 0, 0),
             (0, abs(ty) * 0.05 + abs(ny) * min(0.26, hd * 0.34), 0), (0, 0, COUNTER / 2))

    # --- two crates at the back, so the stall has stock
    for k, su in enumerate((-0.50, 0.50)):
        kx, ky = at(su, -0.45)
        g, _ = down(kx, ky)
        g = gz if g is None else g
        h = 0.24 + 0.05 * ((j + k) % 3)
        boxv(v, f, mi, KT, (kx, ky, g + h),
             (abs(tx) * min(0.30, hw * 0.34) + abs(nx) * min(0.24, hd * 0.30), 0, 0),
             (0, abs(ty) * min(0.30, hw * 0.34) + abs(ny) * min(0.24, hd * 0.30), 0),
             (0, 0, h))
    return min(grounds)


built = {}
for st in chosen:
    full = PREFIX + st["id"]
    if not st["bays"]:
        ob = bpy.data.objects.get(full)
        if ob:
            me0 = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me0.users == 0:
                bpy.data.meshes.remove(me0)
        built[st["id"]] = {**st, "verts": 0, "polys": 0, "bbox": None, "ground_min": None}
        print("  removed %-24s (no lawful site in the parcel)" % full)
        continue
    v, f, mi = [], [], []
    mats = [st["paint"], TIMBER]
    glow = min(bay(v, f, mi, 0, 1, b, j) for j, b in enumerate(st["bays"]))
    old = bpy.data.objects.get(full)
    if old:
        me0 = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me0.users == 0:
            bpy.data.meshes.remove(me0)
    me = bpy.data.meshes.new(full)
    me.from_pydata(v, [], f)
    me.validate()
    me.update()
    for m in mats:
        me.materials.append(bpy.data.materials[m])
    for p, k in zip(me.polygons, mi):
        p.material_index = k
    ob = bpy.data.objects.new(full, me)
    coll.objects.link(ob)
    ob["t2c_gate_awning"] = 1
    built[st["id"]] = {**st, "verts": len(v), "polys": len(f),
                       "bbox": wbb(ob), "ground_min": round(glow, 3)}
    print("  built %-24s verts %3d polys %3d  bbox %s" % (full, len(v), len(f), wbb(ob)))

# by NAME, not by reference: the two ids are deleted and rebuilt above, and an
# unhide through a stale pointer is `StructRNA of type Object has been removed`.
for n in hidden:
    ob = bpy.data.objects.get(n)
    if ob:
        ob.hide_viewport = False
bpy.context.view_layer.update()

# ------------------------------------------------------------------- the report
print("\n" + "=" * 78)
print("AFTER — the constraints, re-asserted against what was actually built")
print("=" * 78)
ok = True
for st in chosen:
    b = built[st["id"]]["bbox"]
    if b is None:
        print("  %-22s REMOVED — no lawful site (0.00 m2 of %.2f)"
              % (st["id"], st["area_target_m2"]))
        continue
    nr = rays_crossed(b[0], b[1], b[2], b[3], b[4], b[5])
    dw = min(walk_dist(*x["box"]) for x in st["bays"])
    a = sum(4 * x["half"][0] * x["half"][1] for x in st["bays"])
    tgt = next(s["area"] for s in STALLS if s["id"] == st["id"])
    print("  %-22s %d bay(s)  sightlines crossed %d (whole bbox)  d_walk %.2f  "
          "valance hem +%.2f m  canopy %.2f m2 of %.2f (%.0f%%)"
          % (st["id"], len(st["bays"]), nr, dw, EAVE - VALANCE, a, tgt, 100 * a / tgt))
    built[st["id"]]["area_m2"] = round(a, 2)
    built[st["id"]]["area_target_m2"] = round(tgt, 2)
    if nr or dw < WALK_CLEAR:
        ok = False

json.dump({"_doc": "t2_gate_awnings.py — the gate staircase's two named occluders, "
                   "rebuilt as stalls on the toll road's south verge.",
           "generator": "tools/t2_gate_awnings.py", "edge": EDGE,
           "before": before, "after": built,
           "constraints": {"walk_clear_m": WALK_CLEAR, "headroom_m": HEADROOM,
                           "eave_m": EAVE, "ridge_m": RIDGE, "ndc": NDC,
                           "sightlines": len(SIGHT)}},
          open(MANIFEST, "w"), indent=1)
print("\nwrote %s" % MANIFEST)

if not ok:
    print("!! a constraint failed after the build")
    sys.exit(1)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("saved %s" % bpy.data.filepath)
else:
    print("(not saved — pass `save`)")
