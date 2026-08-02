"""gate_bunting_rehang.py — RE-HANG THE BUNTING'S END SPAN OFF THE GATE STAIR.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/gate_bunting_rehang.py -- [save]

WHAT WAS HANDED TO THIS PASS, AND WHY IT IS WRONG.  `gate_cloth_headroom.py`'s
`UNFIXED` note (and the DAYLOG entry it fed) records `t2c_G7_bunting_gate2` as a
CLOTH headroom problem that "spans several walk levels", needing a per-span
re-hang because a 2.150 m lift of its bottom edge (18.990 -> 21.140) still leaves
0.669 m.  Measured on this master, that is a wrong model of the object.  The run
has 24 loose parts:

    part  0        the WEST mast   x  5.92.. 6.08  y 8.92..9.08  z 24.245..26.600
    parts 1..22    11 rope segments and 11 pennants, z 25.798..26.620 throughout
    part 23        the EAST mast   x 23.92..24.08  y 3.92..4.08  z 18.990..26.600

Every piece of cloth in the run hangs between 25.798 and 26.620, which is 1.73 m
or more over the gate road at 24.07 and 6.7 m over anything else.  **NO CLOTH IN
THIS OBJECT IS A BLOCKER.**  All 560 of its `walk_bodygate` steps are the EAST
MAST — a 7.61 m timber pole, 0.16 m square, standing at the FOOT of the gate
stair and brushing past its treads on the way up.  "18.990" is not a hem, it is
that pole's footing on `shelf_paving` at the inn tier.

WHY THE POLE IS 7.61 M.  `t2_color_pops.py`'s `bunting` builder ends each run
with `ground_below(top, 8.0)` and stands a mast on whatever it finds.  At the
west end that is the gate road, 2.36 m down — a bunting pole.  At the east end
the run's last node overhangs the head of the stair, so the down-ray falls past
three walk levels and lands on the inn tier 7.61 m below.  The builder had no
idea it had authored a flagstaff through a staircase.  Measured ground under the
run's own chord, run hidden, first hit down from z 25.9:

    x 22.00 y 4.56   gate_road    23.991   drop 2.51
    x 22.50 y 4.42   gate_road    23.972   drop 2.53      <- the last road
    x 23.00 y 4.28   bar_..._railB 21.774  drop 4.73
    x 23.50 y 4.14   walk_..._t02 19.770   drop 6.73
    x 24.00 y 4.00   shelf_paving 18.990   drop 7.51      <- where the mast stands

SO THE FIX IS TO THE RUN'S END POINT, NOT TO ITS CLOTH.  This pass walks the
run's own chord back from the east node until the ground under it is within
`MAX_MAST` of the rope AND the mast's body-inflated footprint is clear of every
walk triangle it could stand in, then re-hangs THE LAST SPAN there: the rope's
end node, its pennant and the mast move together on a linear warp that pins the
second-to-last node and leaves the other ten spans untouched to the micron.  The
mast comes out the length of its twin, standing on the road at the head of the
steps, which is where a bunting pole belongs.

WHY NOT RE-RUN `t2_color_pops.py`.  Same reason `gate_cloth_headroom.py` gives:
it places by screen-space probe rectangle and re-running it re-commits the
original mistake.  The height a mast may drop is a property of the walk graph
under it, which is what is measured here.  The fix belongs in that placer's
`ground_below` eventually (cap the drop, search back along the run); this is the
interim with its measurement attached.

CLEARANCE IS TESTED AGAINST REAL TRIANGLES, NOT BBOXES.  A bunting run's bbox is
its whole 18 m diagonal envelope; refusing or accepting sites by that box is the
error that once killed 13 of 23 parapet posts.  Every walk triangle within reach
is tested by nearest-point in xy against the mast's footprint, and only counted
when a body standing on it (`BODY_H` tall) would actually share z with the mast.

AS BUILT 2026-08-02.  The east mast moved 1.45 m back along the run's own chord,
(24.000, 4.000) -> (22.602, 4.385), and came down from 7.610 m to 2.629 m,
standing on `gate_road` at 23.971 with 1.176 m of body clearance to the nearest
walk triangle that shares its height.  23 of the run's 137 verts moved; the other
114 are BIT-IDENTICAL and the town digest over the master's 2054 other meshes is
unchanged (the digest is negative-controlled: a 0.02 mm nudge of one vertex of
`gate_arch` changes it).  `walk_bodygate --scene del-cine` before and after:
t2c_G7_bunting_gate2 560 blocked steps -> ABSENT, town-wide 205677 -> 205117
(exactly the 560), the gate-stair region 3659 -> 3099, and 88 samples that could
not slide out in any direction became passable.  Re-running is a no-op (0 verts).

AND IT WAS NEVER VISIBLE.  Ray-cast from every solved camera against the master,
the old 7.61 m pole was 0/7 samples visible from ALL SIXTEEN — behind gate_arch
from the gate shot, behind shelf_item_shop from shelf-east, behind its own cloth
from shelf-west.  It was an invisible wall in the town's front door, which is the
user's original gate-tier complaint word for word.  The re-hung mast IS visible
(gate 1/5, shelf-west 2/5, shelf-east 2/5 of its sample column), so those three
plates are the frustum-affected re-bake list and no others.
"""
import bpy, hashlib, json, math, os, sys
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
MANIFEST = REPO + "/tools/blends/districts/gate_bunting_rehang.json"

TARGET = "t2c_G7_bunting_gate2"
# MEASURED, AND DELIBERATELY NOT THIS PASS'S PROBLEM.  Dellhollow has 15 bunting-ish
# objects; a mast census over all of them (loose parts with a <0.40 m xy footprint and a
# >1 m z span) finds the over-long-mast defect in exactly ONE — this one.  The other two
# runs with big `walk_bodygate` counts are a DIFFERENT mechanism and must not be handed
# to this instrument:
#     t2c_N2_nl_bunting   1240 blocked steps   masts 3.21 m + 3.21 m — both fine
#     lf_bunting_0         976 blocked steps   NO MASTS AT ALL — the cloth itself
#     t2c_LH2_rail_bunting   0 blocked steps   one 5.91 m mast, blocking nothing
# So "the bunting runs are blocking the town" is not a true generalisation: one pole was.
MEASURED_NOT_FIXED = {
    "t2c_N2_nl_bunting": "1240 blocked steps, but its masts are 3.21 m — not this defect",
    "lf_bunting_0": "976 blocked steps and no mast at all — the cloth, not a pole",
}
MAX_MAST = 3.00      # a bunting pole; the run's west mast is 2.355 m
BODY_R = 0.30        # play3d walkStep()'s body half-width, via walk_bodygate
BODY_H = 1.30        # play3d walkStep()'s body height
MARGIN = 0.06        # a hand's width beyond the body, so we are not exactly on the bar
STEP = 0.05          # how finely the chord is walked back
NOT_GROUND = ("walk_", "bar_", "veg_", "fx_", "t2c_")   # things a mast may not stand on

sc = bpy.context.scene
ob = bpy.data.objects.get(TARGET)
if ob is None:
    raise SystemExit("%s is not in this blend" % TARGET)
M = ob.matrix_world
Minv = M.inverted()
ws = [M @ v.co for v in ob.data.vertices]
ZLO, ZHI = min(p.z for p in ws), max(p.z for p in ws)
BASE_WS = list(ws)                     # the run BEFORE anything is touched


def town_digest():
    """SHA-256 over every OTHER mesh object's world vertices, quantised to 1e-5.

    The faithfulness gate this replaces compared the target to ITSELF and could
    therefore only ever print 0 — an instrument that cannot fail (CLAUDE.md: an
    instrument that finds nothing must prove it could have found something).  This
    one hashes the 2054 objects the pass promises not to touch, so a stray edit
    anywhere in the master shows up as a changed digest."""
    h = hashlib.sha256()
    for o in sorted(bpy.data.objects, key=lambda o: o.name):
        if o.type != 'MESH' or o.name == TARGET:
            continue
        h.update(o.name.encode())
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            h.update(b"%d %d %d" % (round(p.x * 1e5), round(p.y * 1e5), round(p.z * 1e5)))
    return h.hexdigest()


DIGEST_BEFORE = town_digest()

# ---------------------------------------------------------------- the walk set
WTRIS = []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith("walk_"):
        continue
    m, me = o.matrix_world, o.data
    for p in me.polygons:
        vs = [m @ me.vertices[i].co for i in p.vertices]
        for k in range(1, len(vs) - 1):
            WTRIS.append((vs[0], vs[k], vs[k + 1], o.name))


def seg_pt_d2(p, a, b):
    ab = b - a
    L2 = ab.dot(ab)
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, (p - a).dot(ab) / L2))
    return (a + ab * t - p).length_squared


def tri_xy_dist(px, py, a, b, c):
    """nearest distance in xy from (px,py) to a triangle — 0 inside it."""
    p = Vector((px, py))
    A, B, C = Vector((a.x, a.y)), Vector((b.x, b.y)), Vector((c.x, c.y))
    d1 = (p - C).x * (A - C).y - (A - C).x * (p - C).y
    d2 = (p - A).x * (B - A).y - (B - A).x * (p - A).y
    d3 = (p - B).x * (C - B).y - (C - B).x * (p - B).y
    if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
        return 0.0
    return math.sqrt(min(seg_pt_d2(p, A, B), seg_pt_d2(p, B, C), seg_pt_d2(p, C, A)))


def walk_conflict(x, y, half, z0, z1):
    """walk triangles a mast of half-width `half` spanning z0..z1 would obstruct.

    A conflict is a triangle whose xy nearest point is inside BODY_R + half +
    MARGIN of the mast axis AND whose own height puts a BODY_H body into the
    mast's z span — the same test `walk_bodygate` scores a step with."""
    reach = BODY_R + half + MARGIN
    out = {}
    for a, b, c, nm in WTRIS:
        zt = max(a.z, b.z, c.z)
        zb = min(a.z, b.z, c.z)
        if zb > z1 or zt + BODY_H < z0:
            continue
        if tri_xy_dist(x, y, a, b, c) <= reach:
            out[nm] = out.get(nm, 0) + 1
    return out


def walk_margin(x, y, half, z0, z1):
    """How much room the mast has: nearest walk triangle in xy, MINUS the body reach.

    `walk_conflict` answers yes/no at a fixed reach; a yes/no with no margin cannot
    tell "1 cm clear" from "3 m clear", and a site chosen at 1 cm is a site that the
    next map edit re-blocks.  Only triangles whose own height shares the mast's z
    span with a body count — the same filter `walk_conflict` uses."""
    best, bn = 1e9, None
    for a, b, c, nm in WTRIS:
        zt = max(a.z, b.z, c.z)
        zb = min(a.z, b.z, c.z)
        if zb > z1 or zt + BODY_H < z0:
            continue
        d = tri_xy_dist(x, y, a, b, c)
        if d < best:
            best, bn = d, nm
    return (best - (BODY_R + half)), bn


def ground_at(x, y, ztop):
    """first non-dressing surface under (x, y, ztop), with the run hidden."""
    dg = bpy.context.evaluated_depsgraph_get()
    z = ztop
    for _ in range(12):
        hit, loc, n, fi, o, mw = sc.ray_cast(dg, Vector((x, y, z)), Vector((0, 0, -1)),
                                             distance=z - (ZLO - 12.0))
        if not hit:
            return None, None
        if not o.name.startswith(NOT_GROUND):
            return loc.z, o.name
        z = loc.z - 0.02          # skip a ribbon/rail and keep looking down
    return None, None


# ------------------------------------------------------- find the masts, by shape
# A mast is a loose box: a tiny xy footprint and a tall z span.  Everything else in
# the run is rope or pennant and lives in the top 1 m.
import bmesh
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
seen, comps = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        u = stack.pop(); comp.append(u.index)
        for e in u.link_edges:
            w = e.other_vert(u)
            if w.index not in seen:
                seen.add(w.index); stack.append(w)
    comps.append(comp)
bm.free()

masts = []
for comp in comps:
    xs = [ws[i].x for i in comp]; ys = [ws[i].y for i in comp]; zs = [ws[i].z for i in comp]
    if max(xs) - min(xs) < 0.40 and max(ys) - min(ys) < 0.40 and max(zs) - min(zs) > 1.0:
        masts.append(dict(idx=comp, x=(min(xs) + max(xs)) / 2, y=(min(ys) + max(ys)) / 2,
                          half=max(max(xs) - min(xs), max(ys) - min(ys)) / 2,
                          base=min(zs), top=max(zs)))
masts.sort(key=lambda m: m["x"])

print("=" * 78)
print("GATE BUNTING RE-HANG — %s: %d loose parts, %d masts" % (TARGET, len(comps), len(masts)))
print("=" * 78)
for m in masts:
    print("  mast at (%6.3f, %6.3f)  half-width %.3f  z %7.3f..%7.3f  = %.3f m"
          % (m["x"], m["y"], m["half"], m["base"], m["top"], m["top"] - m["base"]))
    c = walk_conflict(m["x"], m["y"], m["half"], m["base"], m["top"])
    print("      walk triangles it obstructs: %s" % (sorted(c.items(), key=lambda kv: -kv[1])[:4] or "none"))

# ------------------------------------------------- the run's node chord, from the rope
rope = [i for i in range(len(ws)) if ws[i].z > ZHI - 1.2]
A = min((ws[i] for i in rope), key=lambda p: p.x)
B = max((ws[i] for i in rope), key=lambda p: p.x)
NSPAN = 11                              # t2_color_pops' bunting N
chordxy = Vector((B.x - A.x, B.y - A.y))
report = {}
changed = 0

for m in masts:
    drop = m["top"] - m["base"]
    conflict = walk_conflict(m["x"], m["y"], m["half"], m["base"], m["top"])
    if drop <= MAX_MAST and not conflict:
        print("\n  mast at (%.2f, %.2f): %.3f m and clear — untouched" % (m["x"], m["y"], drop))
        report["mast_%.1f_%.1f" % (m["x"], m["y"])] = dict(moved=False, length=round(drop, 4))
        continue
    # WHICH END is this, and which way does the run go from here
    outward = 1.0 if abs(m["x"] - B.x) < abs(m["x"] - A.x) else -1.0
    inward = -outward
    E = Vector((m["x"], m["y"], m["top"]))
    # the second-to-last node: one span in from this end along the chord
    N0 = Vector((E.x + inward * chordxy.x / NSPAN, E.y + inward * chordxy.y / NSPAN, 0.0))
    print("\n  mast at (%.2f, %.2f) is %.3f m%s — SEARCHING back along the run"
          % (m["x"], m["y"], drop, " and obstructs walk" if conflict else ""))
    hit = None
    steps = int((chordxy.length / NSPAN) / STEP)
    for k in range(1, steps + 1):
        u = k * STEP / chordxy.length
        x = E.x + inward * chordxy.x * u
        y = E.y + inward * chordxy.y * u
        # the rope's height at this station: linear between the two nodes
        f = (k * STEP) / (chordxy.length / NSPAN)
        # rope z at the end node and one span in — read off the rope verts nearest each
        g, gn = ground_at(x, y, m["top"] - 0.30)
        if g is None or m["top"] - g > MAX_MAST:
            continue
        c2 = walk_conflict(x, y, m["half"], g, m["top"])
        if c2:
            continue
        hit = dict(x=x, y=y, g=g, gn=gn, back=k * STEP)
        break
    if hit is None:
        print("      NO SITE within one span — mast left alone and REPORTED")
        report["mast_%.1f_%.1f" % (m["x"], m["y"])] = dict(moved=False, length=round(drop, 4),
                                                           reason="no clear site within one span")
        continue
    Ep = Vector((hit["x"], hit["y"], 0.0))
    d = Vector((E.x - N0.x, E.y - N0.y, 0.0))
    L = d.length
    dn = d / L
    delta = Vector((Ep.x - E.x, Ep.y - E.y, 0.0))
    mg, mgn = walk_margin(hit["x"], hit["y"], m["half"], hit["g"], m["top"])
    print("      site found %.2f m back: (%.3f, %.3f) on %s, ground %.3f -> mast %.3f m"
          % (hit["back"], hit["x"], hit["y"], hit["gn"], hit["g"], m["top"] - hit["g"]))
    print("      body clearance to the nearest walk triangle sharing its height: "
          "%.3f m (%s)" % (mg, mgn))
    # LINEAR WARP OF THE LAST SPAN ONLY: t = 0 at the second-to-last node, 1 at the end
    # node, so the other ten spans do not move at all and the seam stays welded.
    mastset = set(m["idx"])
    moved = 0
    for i, p in enumerate(ws):
        t = (Vector((p.x - N0.x, p.y - N0.y, 0.0)).dot(dn)) / L
        if t <= 0.0:
            continue
        if i in mastset:
            nx, ny = p.x + delta.x, p.y + delta.y
            nz = hit["g"] if p.z < m["top"] - 0.5 else p.z
            ob.data.vertices[i].co = Minv @ Vector((nx, ny, nz))
        else:
            ob.data.vertices[i].co = Minv @ Vector((p.x + delta.x * t, p.y + delta.y * t, p.z))
        moved += 1
    changed += moved
    ob.data.update()
    ws2 = [M @ v.co for v in ob.data.vertices]
    nb = min(ws2[i].z for i in m["idx"]); nt = max(ws2[i].z for i in m["idx"])
    nx = sum(ws2[i].x for i in m["idx"]) / len(m["idx"])
    ny = sum(ws2[i].y for i in m["idx"]) / len(m["idx"])
    c3 = walk_conflict(nx, ny, m["half"], nb, nt)
    print("      mast %.3f m -> %.3f m at (%.3f, %.3f); walk obstructed %s; %d verts moved"
          % (drop, nt - nb, nx, ny, sorted(c3.items(), key=lambda kv: -kv[1])[:3] or "NONE", moved))
    report["mast_%.1f_%.1f" % (m["x"], m["y"])] = dict(
        moved=True, verts=moved, pulled_back_m=round(hit["back"], 4),
        from_xy=[round(m["x"], 4), round(m["y"], 4)], to_xy=[round(nx, 4), round(ny, 4)],
        length_before=round(drop, 4), length_after=round(nt - nb, 4),
        stands_on=hit["gn"], walk_conflict_after=c3,
        walk_margin_m=round(mg, 4), nearest_walk=mgn)
    ws = ws2

# ------------------------------------------------------------- faithfulness check
# THREE CLAIMS, EACH MEASURED, none of them a self-comparison:
#   1. nothing outside the run moved              — town digest before vs after
#   2. the ten spans this pass does not touch are BIT-IDENTICAL, not "close"
#   3. the verts that did move moved by the deltas the report claims
ws3 = [M @ v.co for v in ob.data.vertices]
DIGEST_AFTER = town_digest()
deltas = [(ws3[i] - BASE_WS[i]).length for i in range(len(ws3))]
moved_ix = [i for i, d in enumerate(deltas) if d > 0.0]
exact = sum(1 for d in deltas if d == 0.0)
print("\nFAITHFULNESS")
print("  town digest (2054 other meshes)  %s -> %s   %s"
      % (DIGEST_BEFORE[:16], DIGEST_AFTER[:16],
         "UNCHANGED" if DIGEST_BEFORE == DIGEST_AFTER else "*** CHANGED — REFUSING ***"))
print("  %s: %d of %d verts moved (max %.4f m), %d BIT-IDENTICAL"
      % (TARGET, len(moved_ix), len(ws3), max(deltas) if deltas else 0.0, exact))
print("  run bbox  x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f"
      % (min(p.x for p in ws3), max(p.x for p in ws3), min(p.y for p in ws3),
         max(p.y for p in ws3), min(p.z for p in ws3), max(p.z for p in ws3)))
if DIGEST_BEFORE != DIGEST_AFTER:
    raise SystemExit("faithfulness gate FAILED: geometry outside %s changed" % TARGET)
os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
json.dump(dict(_doc=("GENERATED by tools/gate_bunting_rehang.py — the bunting run's end "
                     "span pulled back onto ground a mast can stand on, off the gate stair."),
               generator="tools/gate_bunting_rehang.py", target=TARGET,
               max_mast_m=MAX_MAST, body_r=BODY_R, body_h=BODY_H, margin_m=MARGIN,
               town_digest_unchanged=(DIGEST_BEFORE == DIGEST_AFTER),
               masts=report, measured_not_fixed=MEASURED_NOT_FIXED),
          open(MANIFEST, "w"), indent=1)
print("manifest -> %s" % os.path.relpath(MANIFEST, REPO))
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
