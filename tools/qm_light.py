"""qm_light.py — the Quay-Market tier's self-contained KEYQ_* rig.

  Blender -b tools/blends/dellhollow-master.blend -P tools/qm_light.py -- [save]
  ... -- report        measure only, add nothing

MUST run AFTER `qm_build.py`: the build clears every `qm_*` / `KEYQ_*` object and
the lantern practicals this district hangs are `KEYQ_*` too.

Discipline is the Waterfront's, unchanged across five districts (manifest 65-70):
  * a chain that fires ALONG the gorge is narrow-and-many; at <= 26 deg the
    neighbour falls outside the cone (65)
  * `spot_blend = 1.0`, so cones cross-fade instead of scalloping (66)
  * each chain carries a LEVEL against KEY_slip's peak, not against its own (67)
  * area sources are solved by INTEGRATING the emitter, never scaled by area (68)
  * faked bounce cards cast no shadow and carry a cutoff, because EEVEE's shadow
    budget overflows silently past ~40 lamps (70) — this file is added to a scene
    that already holds 185 lights, so every value below is a MEASURED irradiance
    and not a frame.

WHAT IS DIFFERENT HERE.  This tier is the only one in town with a CEILING: the
shop street's plate roofs everything south of y = 13.5 at z 16.9..17.7, and the
arcade under it is the darkest walkable place in Dellhollow.  A key spot cannot
reach it (a cone aimed down a covered arcade lights the plate), and lifting the
sky wash lifts the gorge with it, which is finding 105.  So the rig is two
pieces: a narrow chain over the OPEN half, and a bounce card that reaches UNDER
the plate from the gorge side, aimed at the north-facing revetment the market is
read against.

SPILL IS ASSERTED AGAINST FOUR ACCEPTED REGIONS, per this custody's brief: the
Boatyard hero reference, the Waterfront boardwalk, the SHOP STREET one tier up
(which this district is directly under, so it is the one most at risk), and
Locksfoot's deck downstream.  Finding 208 is why the count keeps growing: spill
budgets do not compose, and the merge that proved it moved an accepted frame by
+1.94% because two branch districts each measured only against the Boatyard.
"""
import bpy, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import link, coll

SAVE = "save" in sys.argv
REPORT = "report" in sys.argv
COLL = "DIST_quaymkt"
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-40s %s" % (kind, what, why))


print("=" * 78)
print("QUAY-MARKET TIER LIGHT RIG")
print("=" * 78)

KEY = bpy.data.objects["KEY_slip"]
KD = KEY.data
DIR = (KEY.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
AIM0 = Vector((20.5, 29.83, 1.0))                 # the ACCEPTED Boatyard reference
WF = Vector((58.0, 27.0, 1.4))                    # the accepted Waterfront boardwalk
SHELF = Vector((35.0, 7.0, 19.60))                # the accepted shop street, one tier up
SHELF_FRONT = (Vector((37.40, 8.62, 20.60)), Vector((0.0, -1.0, 0.0)))
GATEP = Vector((15.7, 4.0, 25.6))                 # the gate arch's west pier face
WESTN = Vector((-1.0, 0.0, 0.0))
STANDOFF = (Vector(KEY.location) - AIM0).length


def irr(E, lamp_pos, P, direction=DIR, size=None, blend=None):
    size = KD.spot_size if size is None else size
    blend = KD.spot_blend if blend is None else blend
    v = P - lamp_pos
    r = v.length
    if r < 1e-6:
        return 0.0
    ca = v.normalized().dot(direction)
    ch = math.cos(size / 2.0)
    if ca <= ch:
        return 0.0
    smooth = max((1.0 - ch) * blend, 1e-4)
    t = min(1.0, (ca - ch) / smooth)
    return E / (4.0 * math.pi * r * r) * (t * t * (3.0 - 2.0 * t))


def area_irr(size_x, size_y, loc, rot, E, P, npn=Vector((0, 0, 1)), n=11):
    R = rot.to_matrix()
    ex, ey, ez = R.col[0], R.col[1], -R.col[2]
    A = size_x * size_y
    L = E / (math.pi * A)
    dA = A / (n * n)
    tot = 0.0
    for i in range(n):
        for j in range(n):
            u, v = (i + 0.5) / n - 0.5, (j + 0.5) / n - 0.5
            q = Vector(loc) + ex * (u * size_x) + ey * (v * size_y)
            w = P - q
            r = w.length
            if r < 1e-6:
                continue
            wn = w / r
            cl, cp = wn.dot(ez), -wn.dot(npn)
            if cl <= 0 or cp <= 0:
                continue
            tot += L * cl * cp / (r * r) * dA
    return tot


PEAK = irr(KD.energy, Vector(KEY.location), AIM0)
print("\n--- 0. what the tier already gets ------------------------------------")
print("  KEY_slip: %.0f W, cone %.0f deg, blend %.2f, standoff %.2f m -> peak %.4f W/m2"
      % (KD.energy, math.degrees(KD.spot_size), KD.spot_blend, STANDOFF, PEAK))

AREA_N = 11


def existing(P, npn=Vector((0, 0, 1)), skip=("KEYQ_",)):
    tot = 0.0
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.name.startswith(skip):
            continue
        d = o.data
        if d.type == 'SUN':
            dv = (o.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            tot += d.energy * max(-dv.dot(npn), 0.0)
        elif d.type == 'AREA':
            sy = d.size_y if d.shape == 'RECTANGLE' else d.size
            tot += area_irr(d.size, sy, Vector(o.location), o.rotation_euler,
                            d.energy, P, npn, AREA_N)
        elif d.type == 'SPOT':
            dv = (o.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            tot += irr(d.energy, Vector(o.location), P, dv, d.spot_size, d.spot_blend)
        else:
            r = (P - Vector(o.location)).length
            tot += d.energy / (4 * math.pi * max(r, 0.2) ** 2)
    return tot


# ON WHAT BASIS EVERY NUMBER BELOW IS QUOTED.  A percentage is only as honest as
# its denominator, and `existing()` with every lamp in the file is a generous one:
# at the shop street's mid-street probe it answers 20.57 W/m2 because a 680 W
# globe hangs 2.4 m away, where that district SOLVED the same surface to 2.19 on
# the shared rig.  Both the arcade fill and the spill assertions are therefore
# computed on the SHARED RIG (finding 101) — sun, sky, rim, the gorge chains and
# the bounce cards, with every district's practicals excluded, ours included in
# neither.  The density check in section 4 is the one place every lamp counts,
# because there the lamps ARE the measurement.
PRACTICALS = ("KEYQ_", "KEYSH_lantern", "KEYG_lantern", "KEYW_lantern",
              "lf_lantern", "wf_lantern", "lantern_light", "kettle_fire",
              "shed_brazier")


def shared(P, N=Vector((0, 0, 1))):
    return existing(P, N, skip=PRACTICALS)


# The market's own probes, on the floor a player stands on.
FLOOR = 14.00
PROBES = {
    "arcade W    (34.0, 9.5)": Vector((34.00, 9.50, FLOOR + 0.60)),
    "arcade mid  (44.0, 9.5)": Vector((44.00, 9.50, FLOOR + 0.60)),
    "arcade E    (53.0, 9.5)": Vector((53.00, 9.50, FLOOR + 0.60)),
    "notice pad  (48.2,11.8)": Vector((48.20, 11.80, FLOOR + 0.60)),
    "quay deck   (53.4,15.5)": Vector((53.40, 15.50, FLOOR + 0.60)),
    "quay north  (53.0,18.6)": Vector((53.00, 18.60, FLOOR + 0.60)),
    "market      (59.1,13.0)": Vector((59.09, 13.00, FLOOR + 0.60)),
    "cookhouse   (40.0,12.0)": Vector((40.00, 12.00, FLOOR + 0.60)),
    "stairhead   (35.2,16.6)": Vector((35.20, 16.60, FLOOR + 0.60)),
    "BOATYARD ref": AIM0,
}
# THE VALUE THE DISTRICT IS READ ON IS THE REVETMENT, not the floor: it is the
# one surface in every interior frame, it faces the gorge (+y), and it stands in
# the shop street's shadow all day.
NORTHN = Vector((0.0, 1.0, 0.0))
SOUTHN = Vector((0.0, -1.0, 0.0))
FRONTS = {
    "revetment W (34.0, 8.0) N": (Vector((34.00, 8.00, 15.60)), NORTHN),
    "revetment M (44.0, 8.0) N": (Vector((44.00, 8.00, 15.60)), NORTHN),
    "revetment E (53.0, 8.0) N": (Vector((53.00, 8.00, 15.60)), NORTHN),
    "cookhouse N (40.0,15.7) N": (Vector((40.00, 15.70, 15.80)), NORTHN),
    "notice bd   (48.2,10.1) N": (Vector((48.20, 10.10, 15.60)), NORTHN),
}

for nm, P in PROBES.items():
    print("  %-24s up-facing   %.4f W/m2" % (nm, existing(P)))
for nm, (P, N) in FRONTS.items():
    print("  %-24s face        %.4f W/m2" % (nm, existing(P, N)))
print("  %-24s up-facing   %.4f W/m2   <- the accepted SHOP STREET, one tier up"
      % ("shelf street mid", existing(SHELF)))
print("  %-24s street-face %.4f W/m2   <- the shop street's own solved 2.19"
      % ("shelf weapon front", existing(*SHELF_FRONT)))
print("  %-24s WEST-facing %.4f W/m2   <- the GATE's accepted value"
      % ("gate arch pier", existing(GATEP, WESTN)))

# Locksfoot's reference point is FOUND, not remembered: the first walking surface
# a down-ray grid finds in its own region, so this assertion cannot drift when
# that district is rebuilt.
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
LF = None
for gx in range(72, 96, 2):
    for gy in range(24, 34, 2):
        hit, loc, nor, idx, ob, m = sc.ray_cast(dg, Vector((gx, gy, 24.0)),
                                                Vector((0, 0, -1)), distance=40.0)
        if hit and ob is not None and ob.name.startswith(("walk_", "bar_")) \
                and loc.z < 12.0:
            LF = loc + Vector((0, 0, 0.60))
            break
    if LF:
        break
if LF is None:
    LF = Vector((78.0, 27.0, 4.2))
print("  %-24s up-facing   %.4f W/m2   <- LOCKSFOOT, found at (%.1f, %.1f, %.2f)"
      % ("locksfoot deck", existing(LF), LF.x, LF.y, LF.z))

if REPORT:
    sys.exit(0)

for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith(("KEYQ_quay_", "KEYQ_arcade_")):
        bpy.data.objects.remove(o, do_unlink=True)

# ===========================================================================
# 1. THE QUAY CHAIN — over the OPEN half only
# ===========================================================================
print("\n--- 1. quay chain ----------------------------------------------------")
# Aimed at y = 15.6, which is the open deck: south of 13.5 the shop street's plate
# is in the way and a cone aimed there lights the plate's underside, not the
# market.  LEVEL is the town's lowest after the shop street's 0.30 — this tier
# already receives the shared sun and sky, the Waterfront's two chains at 20..30 m,
# the shop street's own chain 5 m overhead and twelve 680 W practicals of its own,
# and its subject is warm pools under a dark arcade.  Solved against KEY_slip's
# peak (finding 67), never against its own.
CONE = 26.0
LEVEL = 0.26
AIMS = [Vector((x, 15.60, FLOOR + 0.10)) for x in (36.0, 42.0, 48.0, 54.0, 60.0)]
made = []
for i, a in enumerate(AIMS):
    d = KD.copy()
    d.name = "KEYQ_quay_%d" % i
    d.spot_size = math.radians(CONE)
    d.spot_blend = 1.0
    d.use_custom_distance = True
    d.cutoff_distance = 44.0
    d.shadow_maximum_resolution = 0.008
    ob = bpy.data.objects.new(d.name, d)
    ob.location = a - DIR * STANDOFF
    ob.rotation_euler = KEY.rotation_euler
    link(ob, COLL)
    made.append((ob, a))


def chain_at(P, E=None):
    return sum(irr(E if E is not None else ob.data.energy, Vector(ob.location), P,
                   size=ob.data.spot_size, blend=ob.data.spot_blend) for ob, a in made)


def chain_range(E=None):
    n = len(AIMS) - 1
    vals = []
    for k in range(81):
        f = 0.6 + (n - 1.2) * k / 80.0
        i = min(int(f), n - 1)
        vals.append(chain_at(AIMS[i].lerp(AIMS[i + 1], f - i), E))
    return min(vals), max(vals)


E = LEVEL * KD.energy * PEAK / max(chain_range(KD.energy)[1], 1e-9)
for ob, a in made:
    ob.data.energy = round(E, 1)
lo, hi = chain_range()
log("KEY", "KEYQ_quay_0..%d: %.0f deg, %.0f W" % (len(made) - 1, CONE, E),
    "aim x %.0f..%.0f at y=%.1f (the OPEN deck; south of 13.5 the shop street's "
    "plate is the ceiling) | irradiance %.3f..%.3f W/m2 (ripple %.0f%%), %.0f%% of "
    "KEY_slip's peak %.4f"
    % (AIMS[0].x, AIMS[-1].x, AIMS[0].y, lo, hi, 100 * (hi - lo) / max(hi, 1e-9),
       100 * LEVEL, PEAK))

# ===========================================================================
# 2. THE ARCADE CARD — the only thing that reaches under the plate
# ===========================================================================
print("\n--- 2. arcade fill ---------------------------------------------------")
# THE PROBLEM ON THIS TIER IS THE CEILING.  `SUN_key` runs down-gorge at
# (-0.86, -0.35, -0.38) and the shop street's plate roofs everything south of
# y = 13.5, so the revetment — the surface the whole market is read against — is
# in shade all day and so is the floor in front of it.  A key cannot fix it and
# the sky wash cannot be raised without raising the gorge (finding 105).  What
# works is the answer two districts above: a faked bounce CARD, no shadow, hard
# cutoff, solved so the revetment reaches a fixed fraction of the open deck it
# faces.  It stands OVER THE GORGE and low, because the revetment faces +y and a
# card has to be in front of a surface to light it — the shop street learned the
# same lesson from the other side (its dark fronts faced -y and a gorge card
# could not reach them).
CARDS = [((37.00, 20.00, 18.60), (37.00, 8.60, 15.20)),
         ((45.50, 20.60, 18.60), (45.50, 8.60, 15.20)),
         ((54.00, 21.00, 18.60), (54.00, 8.60, 15.20))]
CW, CH = 9.0, 5.0
WANT_FRAC = 0.62
# THE MEASUREMENT IS THE ARCADE FLOOR AGAINST THE OPEN DECK, on the shared rig.
# Two earlier framings were wrong in the same way.  Facing the REVETMENT and
# including practicals answered "92% of the deck, nothing needed" — because the
# probe was 2 m from a pilaster lamp and the wall faces the open sky over the
# gorge, so it was measuring neither the ceiling nor the shade.  What is actually
# dark on this tier is the FLOOR under the plate, where a player stands.
DARKP = ["arcade W    (34.0, 9.5)", "arcade mid  (44.0, 9.5)", "arcade E    (53.0, 9.5)"]
OPENP = ["quay deck   (53.4,15.5)", "quay north  (53.0,18.6)", "market      (59.1,13.0)"]
TOPS = sum(shared(PROBES[k]) for k in OPENP) / len(OPENP)
HAVE = sum(shared(PROBES[k]) for k in DARKP) / len(DARKP)
WANT = WANT_FRAC * TOPS - HAVE
rots = [(Vector(a) - Vector(p)).to_track_quat('-Z', 'Y').to_euler() for p, a in CARDS]
if WANT <= 0.0:
    EC = 0.0
    log("FILL", "KEYQ_arcade: NOT BUILT",
        "the arcade floor already reads %.4f W/m2 on the shared rig against the "
        "open deck's %.4f = %.0f%%, over the %.0f%% target — a 0 W lamp is dead "
        "weight in a scene with 185 of them, so none is added (and this line is "
        "the record that the check ran)"
        % (HAVE, TOPS, 100 * HAVE / max(TOPS, 1e-9), 100 * WANT_FRAC))
else:
    unit = sum(area_irr(CW, CH, Vector(p), rots[i], 1.0, PROBES[k])
               for i, (p, a) in enumerate(CARDS) for k in DARKP) / len(DARKP)
    EC = round(WANT / max(unit, 1e-12), 1)
    for i, (p, a) in enumerate(CARDS):
        d = bpy.data.lights.new("KEYQ_arcade_%d" % i, 'AREA')
        d.shape = 'RECTANGLE'
        d.size, d.size_y = CW, CH
        d.energy = EC
        d.color = (1.0, 0.78, 0.55)
        d.use_shadow = False
        d.use_custom_distance = True
        d.cutoff_distance = 34.0
        ob = bpy.data.objects.new(d.name, d)
        ob.location = Vector(p)
        ob.rotation_euler = rots[i]
        link(ob, COLL)


def card_at(P, N=Vector((0, 0, 1))):
    if EC <= 0.0:
        return 0.0
    return sum(area_irr(CW, CH, Vector(p), rots[i], EC, P, N)
               for i, (p, a) in enumerate(CARDS))


if EC > 0.0:
        log("FILL", "KEYQ_arcade_0..2: %.0f x %.0f m, %.0f W each" % (CW, CH, EC),
        "the arcade floor %.4f -> %.4f W/m2 on the shared rig (%.0f%% -> %.0f%% of "
        "the open deck's own %.4f); no shadow, 34 m cutoff"
        % (HAVE, HAVE + WANT, 100 * HAVE / max(TOPS, 1e-9),
           100 * (HAVE + WANT) / max(TOPS, 1e-9), TOPS))

# ===========================================================================
# 3. SPILL — four accepted regions (finding 208: budgets do not compose)
# ===========================================================================
print("\n--- 3. spill onto accepted art ---------------------------------------")
# ON WHAT BASIS.  A percentage is only as honest as its denominator, and
# `existing()` with every lamp in the file included is a generous one: at the shop
# street's mid-street probe it answers 20.57 W/m2, because a 680 W practical hangs
# 2.4 m away, where the shop street SOLVED that surface to 2.19 on the shared rig.
# Dividing this rig's spill by 20.57 would flatter it by an order of magnitude.
# So spill is asserted on the SHARED-RIG basis (finding 101): sun, sky, rim, gorge
# chains and bounce cards, with every district's 680 W globes excluded, ours
# included in neither.
def added(P, N=Vector((0, 0, 1))):
    return (chain_at(P) if N.z > 0.5 else 0.0) + card_at(P, N)


fails = []
for nm, P, N in (
        ("Boatyard reference   (20.5, 29.8, 1.0)", AIM0, Vector((0, 0, 1))),
        ("Waterfront boardwalk (58.0, 27.0, 1.4)", WF, Vector((0, 0, 1))),
        ("SHOP STREET mid      (35.0,  7.0,19.6)", SHELF, Vector((0, 0, 1))),
        ("SHOP STREET front    (37.4,  8.6,20.6)", SHELF_FRONT[0], SHELF_FRONT[1]),
        ("GATE arch west pier  (15.7,  4.0,25.6)", GATEP, WESTN)):
    add = added(P, N)
    own = shared(P, N)
    pct = 100 * add / max(own, 1e-12)
    log("CHECK", nm, "+%.5f W/m2 on %.4f (shared rig) = %.2f%%" % (add, own, pct))
    if pct >= 5.0:
        fails.append("%s moves by %.2f%%" % (nm, pct))

# ... AND AS REGION MEANS, not only as points.  Finding 208's lesson was that the
# gate's 0.8%% assertion was a POINT probe and the merged FRAME moved by 1.94%%,
# because a point cannot see the cliff and the water that face a shadowless card
# better than the aim point does.  So each accepted region is also sampled across
# its own walking surface on the same grid the density check uses.
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def region_pts(x0, x1, y0, y1, z0, z1, step=1.2):
    pts = []
    for i in range(int((x1 - x0) / step) + 1):
        for j in range(int((y1 - y0) / step) + 1):
            ok, loc, nrm, _i, ob, _m = sc.ray_cast(
                dg, Vector((x0 + i * step, y0 + j * step, z1 + 6.0)), Vector((0, 0, -1)))
            if not ok or ob is None or not ob.name.startswith(("walk_", "bar_")):
                continue
            if not (z0 <= loc.z <= z1) or nrm.z < 0.7:
                continue
            pts.append(loc + Vector((0, 0, 0.60)))
    return pts


ACCEPTED = {
    "BOATYARD":   (2.0, 32.0, 19.0, 33.0, -2.0, 8.0),
    "WATERFRONT": (40.0, 66.0, 24.0, 33.0, 0.0, 6.0),
    "SHOP STREET": (19.0, 55.0, 1.0, 13.5, 18.4, 19.6),
    "LOCKSFOOT":  (66.0, 100.0, 20.0, 34.0, -1.0, 8.0),
}
AREA_N = 5
for nm, reg in ACCEPTED.items():
    pts = region_pts(*reg)
    if not pts:
        log("WARN", "%s region mean" % nm, "no walking surface found in the region")
        continue
    sh = sum(shared(p) for p in pts) / len(pts)
    ad = sum(added(p) for p in pts) / len(pts)
    pct = 100 * ad / max(sh, 1e-12)
    log("CHECK", "%s region mean (n=%d)" % (nm, len(pts)),
        "+%.5f W/m2 on %.4f (shared rig) = %.2f%%" % (ad, sh, pct))
    if pct >= 5.0:
        fails.append("%s region mean moves by %.2f%%" % (nm, pct))
AREA_N = 11
assert not fails, "the quay-market rig re-values accepted art: %s" % fails

# ===========================================================================
# 4. THE PRACTICALS against the accepted Boatyard's own walking surface
# ===========================================================================
print("\n--- 4. practical density ----------------------------------------------")
# Finding 101: districts are compared on the SHARED rig, because a district's own
# lanterns dominate its numbers — and the corollary (the shop street's) is that
# this makes practical DENSITY the thing to check, against a district the user has
# ACCEPTED, by sampling the WALKING SURFACE of both on the same grid rather than
# comparing two point probes whose only real difference is how far each happens to
# be from its nearest lamp.
BY_REGION = (2.0, 32.0, 19.0, 33.0, -2.0, 8.0)       # the accepted Boatyard
QM_REGION = (30.7, 63.6, 6.5, 21.5, 13.2, 15.2)      # this tier
GRID = 0.75
RATIO_MAX = 1.20


def walk_probes(x0, x1, y0, y1, z0, z1, step=GRID):
    pts = []
    for i in range(int((x1 - x0) / step) + 1):
        for j in range(int((y1 - y0) / step) + 1):
            ok, loc, nrm, _i, ob, _m = sc.ray_cast(
                dg, Vector((x0 + i * step, y0 + j * step, z1 + 6.0)), Vector((0, 0, -1)))
            if not ok or ob is None:
                continue
            # walk_/bar_ ONLY, on both sides.  Adding this district's own paving
            # to its own filter measured 264 points against the Boatyard's 103 and
            # compared two different things: the walk meshes are still ray-castable
            # under the art (that is the whole point of the DECK_DROP), so the same
            # filter samples both districts by the same rule.
            if not ob.name.startswith(("walk_", "bar_")):
                continue
            if not (z0 <= loc.z <= z1) or nrm.z < 0.7:
                continue
            pts.append(loc + Vector((0, 0, 0.60)))
    return pts


def surface_stats(region):
    pts = walk_probes(*region)
    v = sorted(existing(p, skip=("_NOSKIP_",)) for p in pts)
    n = max(len(v), 1)
    return dict(n=len(v), mean=sum(v) / n, med=v[n // 2] if v else 0.0,
                p90=v[int(0.9 * (n - 1))] if v else 0.0, mx=v[-1] if v else 0.0)


AREA_N = 5
bys, qms = surface_stats(BY_REGION), surface_stats(QM_REGION)
AREA_N = 11
for nm, s in (("BOATYARD (accepted)", bys), ("QUAY-MARKET tier", qms)):
    print("  %-22s n=%4d  mean %7.3f  median %7.3f  p90 %7.3f  max %7.3f W/m2"
          % (nm, s["n"], s["mean"], s["med"], s["p90"], s["mx"]))
ratio = qms["mean"] / max(bys["mean"], 1e-9)
nl = len([o for o in bpy.data.objects if o.type == 'LIGHT'
          and o.name.startswith("KEYQ_") and "lantern" in o.name])
log("CHECK", "walking-surface mean vs the accepted Boatyard",
    "%.2f W/m2 against %.2f = %.3fx (bar %.2fx); peaks %.1f vs %.1f. %d practicals."
    % (qms["mean"], bys["mean"], ratio, RATIO_MAX, qms["mx"], bys["mx"], nl))
assert ratio <= RATIO_MAX, (
    "the quay-market practicals are %.3fx the accepted Boatyard's walking surface "
    "— raise LANT_MIN_SEP in qm_build.py and rebuild" % ratio)
assert qms["mx"] <= 1.35 * bys["mx"], (
    "quay-market peak %.1f vs Boatyard peak %.1f — pools are blowing out"
    % (qms["mx"], bys["mx"]))

print("\n--- 5. the tier after -------------------------------------------------")
for nm, P in list(PROBES.items())[:-1]:
    print("  %-24s up-facing   %.4f -> %.4f W/m2"
          % (nm, existing(P), existing(P, skip=("_NOSKIP_",))))
for nm, (P, N) in FRONTS.items():
    print("  %-24s face        %.4f -> %.4f W/m2"
          % (nm, existing(P, N), existing(P, N, skip=("_NOSKIP_",))))

print("\n" + "=" * 78)
print("QUAY-MARKET LIGHT RIG: %d KEYQ_quay spots + %d KEYQ_arcade cards + %d "
      "lantern practicals" % (len(made), len(CARDS), nl))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
