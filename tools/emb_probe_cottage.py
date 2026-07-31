"""emb_probe_cottage.py — WHERE MAY MARA & PIP'S COTTAGE STAND?  A read-only probe.

    Blender -b tools/blends/emberbrook-master.blend -P tools/emb_probe_cottage.py \
        --python-exit-code 1 -- [--id hillside-cottage] [--radius 2.5]

NEVER SAVES.  It answers one question with three measurements and prints a ranked
table; a human stamps the map and the deterministic build chain does the rest.

THE QUESTION.  `hillside-cottage` sits at the junction of three lanes (to the square,
to `lake-home`, to `elder-house`) and all three walk ribbons pass under its footprint —
it is the only building in Home Row the set-back ring cannot clear at any offset, and
it accounts for every gate offender in the district.  Separately, the hilltop bench,
which the map reserves for quiet story beats *because* "the whole village in view",
cannot see the Heartlight: the ray is blocked by this same cottage's wall.

One move might fix both, and the house rule says the lawful position is SEARCHED, not
authored.  So each candidate within `--radius` of the authored point is scored on three
things, and a candidate has to pass all three:

  (a) JUNCTION — the set-back ring finds a clear offset for the cottage's own rotated
      footprint against the walk gate's own sample points, within 2.10 m.  This is the
      exact test `emb_home_build.py` runs, so a pass here means a pass there.
  (b) SIGHTLINE — the segment from the built bench's seated eye to the Heartlight's
      crystal misses the cottage's wall rectangle.  Measured at the ray's own height,
      which is inside the wall band, so a plan-space test is the right one.
  (c) BELONGING — the cottage still touches its three lanes.  A junction cottage that
      has stopped touching its junction is not the building the map is describing, so
      this is a real constraint and not a courtesy: the distance from the footprint to
      each of its three edge polylines must stay under `TOUCH`.

Candidates are ranked by displacement from the authored point, because the smallest
lawful move is the one that keeps the map's intent.
"""
import bpy, json, math, os, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from district_lib import GateGrid, WalkGuard

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


TARGET = opt("--id", "hillside-cottage")
RADIUS = float(opt("--radius", "2.5"))
TOUCH = float(opt("--touch", "2.6"))

D = json.load(open(os.path.join(REPO, "public/townmap/emberbrook.map.json")))
LM = {l["id"]: l for l in D["landmarks"]}
T = LM[TARGET]
TX, TY, TZ = T["pos"]
PARCEL = next(p for p in D["parcels"] if p["id"] == "p-homerow")
B = PARCEL["bounds"]
REGION = (B["min"][0] - 3, B["max"][0] + 3, B["min"][1] - 3, B["max"][1] + 3)

print("=" * 78)
print("COTTAGE PROBE — where may %r stand?  (read-only)" % TARGET)
print("=" * 78)

# The cottage must not occlude the ray it is being tested against, so its own built
# geometry comes out of the depsgraph first.  In memory only; this file never saves.
killed = 0
for o in list(bpy.data.objects):
    if o.name.startswith("emb_hr_%s" % TARGET.replace("-", "")):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
bpy.context.view_layer.update()
print("  removed %d objects of the cottage's own build so it cannot occlude itself" % killed)

# --- where the bench actually IS.  It was searched at build time, not authored, so the
# only honest source is the object that got built.
bench = next((o for o in bpy.data.objects if o.name == "emb_hr_bench_seat"), None)
assert bench is not None, "no emb_hr_bench_seat in the master — run emb_home_build first"
BP = [bench.matrix_world @ v.co for v in bench.data.vertices]
BX = (min(p.x for p in BP) + max(p.x for p in BP)) / 2
BY = (min(p.y for p in BP) + max(p.y for p in BP)) / 2
BZ = max(p.z for p in BP)
HL = next(l["pos"] for l in D["landmarks"] if (l.get("kind") or "") == "heartlight")
EYE = (BX, BY, BZ + 0.66)                       # seated eye height above the seat
TGT = (HL[0], HL[1], HL[2] + 2.20)              # the crystal itself
print("  bench seat  (%.2f, %.2f, %.2f)   seated eye z %.2f" % (BX, BY, BZ, EYE[2]))
print("  Heartlight  (%.2f, %.2f, %.2f)   ray length %.1f m"
      % (TGT[0], TGT[1], TGT[2], math.dist(EYE[:2] + (EYE[2],), TGT)))

# --- the cottage's own footprint and the three lanes it belongs to
kind = T.get("kind") or ""
big = kind.startswith("shop") or kind == "building"
BW, BD = (4.8 * 1.14, 4.0 * 1.14) if big else (3.9 * 1.14, 3.3 * 1.14)
HWALL, HDEP = BW / 2, BD / 2

LANES = []
for e in D["edges"]:
    if e["from"] == TARGET or e["to"] == TARGET:
        other = e["to"] if e["from"] == TARGET else e["from"]
        pts = [tuple(LM[e["from"]]["pos"])] + [tuple(w) for w in e.get("waypoints", [])] \
            + [tuple(LM[e["to"]]["pos"])]
        LANES.append((other, e.get("type", "path"), pts))
print("  lanes at this junction: %s" % ", ".join("%s (%s)" % (o, t) for o, t, _ in LANES))


def appr_for(x, y):
    """The approach the builder would derive at this position: prefer a road edge, then
    the furthest neighbour.  Recomputed per candidate because moving the cottage can
    change which lane is longest, and the door has to keep facing the road."""
    cands = []
    for other, etype, pts in LANES:
        nb = pts[1] if pts[0][:2] == (LM[TARGET]["pos"][0], LM[TARGET]["pos"][1]) else pts[-2]
        for cand in (pts[1], pts[-2]):
            if abs(cand[0] - LM[TARGET]["pos"][0]) > 1e-9 or abs(cand[1] - LM[TARGET]["pos"][1]) > 1e-9:
                nb = cand
                break
        dx, dy = nb[0] - x, nb[1] - y
        d = math.hypot(dx, dy)
        if d > 1e-6:
            cands.append((0 if etype == "road" else 1, -d, dx / d, dy / d))
    if not cands:
        return (0.0, -1.0)
    cands.sort(key=lambda c: (c[0], c[1]))
    return (cands[0][2], cands[0][3])


def seg_pt_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def lane_gap(x, y, pts):
    """Distance from the cottage's footprint (not its centre) to a lane polyline."""
    d = min(seg_pt_dist(x, y, a, b) for a, b in zip(pts, pts[1:]))
    return max(0.0, d - max(HWALL, HDEP))


def seg_hits_rect(p0, p1, cx, cy, hw, hd, rz):
    """Does the plan-space segment cross the oriented rectangle?  Tested in the
    rectangle's own frame, where it is an axis-aligned slab clip."""
    c, s = math.cos(-rz), math.sin(-rz)

    def to_local(p):
        dx, dy = p[0] - cx, p[1] - cy
        return (dx * c - dy * s, dx * s + dy * c)

    ax, ay = to_local(p0)
    bx, by = to_local(p1)
    t0, t1 = 0.0, 1.0
    for (p, q) in ((-(bx - ax), ax + hw), (bx - ax, hw - ax),
                   (-(by - ay), ay + hd), (by - ay, hd - ay)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
            continue
        r = q / p
        if p < 0:
            if r > t1:
                return False
            t0 = max(t0, r)
        else:
            if r < t0:
                return False
            t1 = min(t1, r)
    return t0 <= t1


GUARD = WalkGuard(REGION)
GATE = GateGrid(REGION, GUARD)
print("  gate grid: %d walk samples in the region\n" % len(GATE.pts))

HW_ = (3.9 + 0.10) / 2 + 0.10 if not big else (4.8 + 0.10) / 2 + 0.10
HD_ = (3.3 + 0.10) / 2 + 0.10 if not big else (4.0 + 0.10) / 2 + 0.10


def junction_offset(cx, cy, rz):
    """The set-back the builder would need here, or None if it cannot clear within
    2.10 m.  This is `emb_home_build.py`'s own test, verbatim in behaviour."""
    crz, srz = math.cos(-rz), math.sin(-rz)
    ax, ay = math.cos(rz - math.pi / 2), math.sin(rz - math.pi / 2)
    for rad in [0.0] + [0.15 + 0.15 * k for k in range(14)]:
        for a_ in range(20 if rad > 0 else 1):
            th = math.atan2(-ay, -ax) + 2 * math.pi * a_ / 20
            qx, qy = cx + rad * math.cos(th), cy + rad * math.sin(th)
            bad = False
            for (sx, sy, sz) in GATE.pts:
                if not (TZ < sz + 2.00 and TZ + 0.85 > sz + 0.005):
                    continue
                ddx, ddy = sx - qx, sy - qy
                if abs(ddx * crz - ddy * srz) <= HW_ and abs(ddx * srz + ddy * crz) <= HD_:
                    bad = True
                    break
            if not bad:
                return rad, qx, qy
    return None, None, None


rows = []
for rad in [0.0] + [0.3 + 0.3 * k for k in range(int(RADIUS / 0.3) + 1)]:
    if rad > RADIUS + 1e-9:
        break
    for k in range(24 if rad > 0 else 1):
        th = 2 * math.pi * k / 24
        cx, cy = TX + rad * math.cos(th), TY + rad * math.sin(th)
        ax, ay = appr_for(cx, cy)
        rz = math.atan2(ay, ax) + math.pi / 2
        # (c) BELONGING first — it is the cheapest test and it rejects the most
        gaps = [(o, lane_gap(cx, cy, pts)) for o, _t, pts in LANES]
        worst = max(g for _o, g in gaps)
        if worst > TOUCH:
            continue
        # (b) SIGHTLINE
        blocks = seg_hits_rect(EYE, TGT, cx, cy, HWALL, HDEP, rz)
        if blocks:
            continue
        # (a) JUNCTION
        off, qx, qy = junction_offset(cx, cy, rz)
        if off is None:
            continue
        rows.append((rad, cx, cy, rz, off, worst, gaps))
    if rows:
        break                                    # the smallest lawful move wins

# --- THE FALLBACK FORK, measured in the same run so the choice is informed rather
# --- than sequential: with the cottage left exactly where the map put it, how far must
# --- the BENCH move along the ridge before it can see the Heartlight?
ax0, ay0 = appr_for(TX, TY)
rz0 = math.atan2(ay0, ax0) + math.pi / 2
ridge = math.atan2(TY - BY, TX - BX) + math.pi / 2      # across the bench's own view
print("  FALLBACK PROBE — cottage stays at (%.2f, %.2f); sweeping the bench:" % (TX, TY))
found_b = None
for step in [0.5 * k for k in range(1, 17)]:
    for sgn in (1, -1):
        nx, ny = BX + math.cos(ridge) * sgn * step, BY + math.sin(ridge) * sgn * step
        if seg_hits_rect((nx, ny, EYE[2]), TGT, TX, TY, HWALL, HDEP, rz0):
            continue
        blocked_by_other = any(
            seg_hits_rect((nx, ny, EYE[2]), TGT, LM[o]["pos"][0], LM[o]["pos"][1],
                          HWALL, HDEP, rz0)
            for o in ("lake-home", "elder-house") if o in LM)
        if blocked_by_other:
            continue
        found_b = (nx, ny, step, sgn)
        break
    if found_b:
        break
if found_b:
    print("      bench -> (%.2f, %.2f): %.1f m along the ridge (%s) opens the ray"
          % (found_b[0], found_b[1], found_b[2], "north" if found_b[3] > 0 else "south"))
else:
    print("      no bench position within 8 m along the ridge opens the ray")

print("=" * 78)
if not rows:
    print("NO CANDIDATE within %.1f m satisfies all three." % RADIUS)
    print("Fall back: lane waypoint for the junction, bench ~4 m north for the sightline.")
else:
    rows.sort(key=lambda r: (round(r[0], 3), r[4], r[5]))
    print("%d lawful candidates at the smallest passing displacement (%.2f m). Best first:"
          % (len(rows), rows[0][0]))
    for (rad, cx, cy, rz, off, worst, gaps) in rows[:6]:
        print("  (%.2f, %.2f)  move %.2f m  set-back needed %.2f m  worst lane gap %.2f m"
              % (cx, cy, rad, off, worst))
        print("        lanes: " + "   ".join("%s %.2f m" % (o, g) for o, g in gaps))
    r = rows[0]
    print("\nRECOMMENDED  %s.pos -> [%.2f, %.2f, %.2f]" % (TARGET, r[1], r[2], TZ))
    print("  (a) junction  clears at a %.2f m set-back ring offset (builder's own test)" % r[4])
    print("  (b) sightline bench eye (%.2f, %.2f, %.2f) -> crystal: MISSES the footprint"
          % EYE)
    print("  (c) belonging worst lane gap %.2f m of a %.2f m allowance" % (r[5], TOUCH))
print("=" * 78)
print("(read-only — nothing was saved)")
