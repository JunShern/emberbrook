"""shelf_light.py — the Shelf tier's self-contained KEYSH_* rig.

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/shelf_light.py -- [save]
  ... -- report        measure only, add nothing

MUST run AFTER `shelf_build.py`: the build clears every `shelf_*` / `KEYSH_*`
object, and the lantern practicals this district hangs are `KEYSH_*` too.

Discipline is the Waterfront's, unchanged across four districts now
(manifest 65-70):

  * a chain that fires ALONG the gorge is narrow-and-many; at <= 26 deg the
    neighbour falls outside the cone (65).
  * `spot_blend = 1.0`, so the cones cross-fade instead of scalloping (66).
  * each chain carries a LEVEL against KEY_slip's peak, not against its own (67).
  * area sources are solved by integrating the emitter, never scaled by area (68).
  * faked bounce cards cast no shadow and carry a cutoff, because EEVEE's shadow
    budget overflows silently (70) — and on THIS tier it already does: a check
    render reports 4045 shadow casters against a 2048 pool with the pool set to
    its maximum, so every value call below is a MEASURED irradiance and not a
    frame.

WHAT IS DIFFERENT HERE.  This district is being added to a tier that is ALREADY
lit by three other districts' rigs — the Waterfront's `KEY_gorge_wf_*` at
32..56 m, the gate's `KEYG_gate_*` at 20..25 m, plus the shared sun, sky wash,
rim and bounce.  So the first thing this script does is MEASURE what is already
arriving, and the chain that gets added is deliberately small: a shop street
that spends its day in the shadow of a gallery wants rather less from a key and
rather more from its practicals.

Spill is asserted against THREE accepted regions, not two (the handover's
instruction): the Boatyard reference, the Waterfront boardwalk, AND the gate
tier's arch, whose west-facing value the gate solved to 1.8166 W/m2 = 66% of its
sunlit top.  If this rig moves that number it has re-valued accepted art.
"""
import bpy, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import link, coll

SAVE = "save" in sys.argv
REPORT = "report" in sys.argv
COLL = "SHELF_DISTRICT"
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-38s %s" % (kind, what, why))


print("=" * 78)
print("SHELF TIER LIGHT RIG")
print("=" * 78)

KEY = bpy.data.objects["KEY_slip"]
KD = KEY.data
DIR = (KEY.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
AIM0 = Vector((20.5, 29.83, 1.0))                 # the ACCEPTED Boatyard reference
WF = Vector((58.0, 27.0, 1.4))                    # the accepted Waterfront boardwalk
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


AREA_N = 11          # area-source integration resolution; dropped to 5 for the
                     # hundred-probe surface sweep in section 4, where the area
                     # sources are a rounding error against 680 W point lamps.


def existing(P, npn=Vector((0, 0, 1)), skip=("KEYSH_",)):
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


# The street's own probes, on the walking surface between the shopfronts.
PROBES = {
    "inn door   (25.0, 3.8)": Vector((25.00, 3.80, 19.60)),
    "street W   (27.5, 6.0)": Vector((27.50, 6.00, 19.60)),
    "item pad   (30.0, 9.0)": Vector((30.00, 9.00, 19.60)),
    "street mid (35.0, 7.0)": Vector((35.00, 7.00, 19.60)),
    "weapon pad (37.8, 5.5)": Vector((37.80, 5.50, 19.60)),
    "armor pad  (44.3, 9.0)": Vector((44.30, 9.00, 19.60)),
    "homes pad  (50.8, 9.0)": Vector((50.80, 9.00, 19.60)),
    "BOATYARD ref": AIM0,
}
# The shopfronts face the street across it, so the value the player reads the
# district on is a VERTICAL surface, not the floor.
NORTHN = Vector((0.0, 1.0, 0.0))       # a cliff-side shop's street elevation
SOUTHN = Vector((0.0, -1.0, 0.0))      # a gorge-side shop's street elevation
FRONTS = {
    "inn front      (27.0, 4.7) N": (Vector((27.00, 4.70, 20.60)), NORTHN),
    "item front     (32.6, 5.9) N": (Vector((32.60, 5.90, 20.60)), NORTHN),
    "weapon front   (37.4, 8.6) S": (Vector((37.40, 8.62, 20.60)), SOUTHN),
    "armor front    (44.5,10.7) S": (Vector((44.50, 10.72, 20.60)), SOUTHN),
}

for nm, P in PROBES.items():
    print("  %-24s up-facing   %.4f W/m2" % (nm, existing(P)))
for nm, (P, N) in FRONTS.items():
    print("  %-24s street-face %.4f W/m2" % (nm, existing(P, N)))
print("  %-24s WEST-facing %.4f W/m2   <- the GATE's accepted value"
      % ("gate arch pier", existing(GATEP, WESTN)))

if REPORT:
    sys.exit(0)

for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith(("KEYSH_street_", "KEYSH_front_")):
        bpy.data.objects.remove(o, do_unlink=True)

# ===========================================================================
# 1. THE STREET CHAIN
# ===========================================================================
print("\n--- 1. street chain --------------------------------------------------")
# A narrow chain fired along the street the way every other district fires along
# the gorge.  LEVEL is deliberately the lowest in the town: this street already
# receives the shared sun and sky plus three neighbours' chains, it is roofed for
# a third of its length by the gate's gallery, and it carries fourteen 680 W
# practicals of its own at 2-4 m.  A key that competes with those flattens the
# one thing the district has going for it — pools of warm light under a dark
# gallery.  Solved against KEY_slip's own peak, not against its own (finding 67).
CONE = 26.0
LEVEL = 0.30
AIMS = [Vector((x, 7.0, 19.70)) for x in (25.0, 31.0, 37.0, 43.0, 49.0, 54.0)]
made = []
for i, a in enumerate(AIMS):
    d = KD.copy()
    d.name = "KEYSH_street_%d" % i
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
    lo_f, hi_f = 0.6, n - 0.6
    vals = []
    for k in range(81):
        f = lo_f + (hi_f - lo_f) * k / 80.0
        i = min(int(f), n - 1)
        vals.append(chain_at(AIMS[i].lerp(AIMS[i + 1], f - i), E))
    return min(vals), max(vals)


E = LEVEL * KD.energy * PEAK / max(chain_range(KD.energy)[1], 1e-9)
for ob, a in made:
    ob.data.energy = round(E, 1)
lo, hi = chain_range()
log("KEY", "KEYSH_street_0..%d: %.0f deg, %.0f W" % (len(made) - 1, CONE, E),
    "aim x %.0f..%.0f at y=%.1f | irradiance %.3f..%.3f W/m2 (ripple %.0f%%), "
    "%.0f%% of KEY_slip's peak %.4f"
    % (AIMS[0].x, AIMS[-1].x, AIMS[0].y, lo, hi, 100 * (hi - lo) / max(hi, 1e-9),
       100 * LEVEL, PEAK))

# ===========================================================================
# 2. THE SHOPFRONT CARD
# ===========================================================================
print("\n--- 2. shopfront fill ------------------------------------------------")
# THE VALUE PROBLEM ON THIS TIER IS NOT THE FLOOR, IT IS THE FACADES.  `SUN_key`
# runs down-gorge at (-0.86, -0.35, -0.38) and the gate's gallery roofs the west
# third of the street, so both rows of shopfronts face into shade all day: the
# report shows the street-facing elevations at a fraction of the paving's own
# up-facing value.  A key cannot fix that (a spot aimed down a street lights the
# street), and lifting the sky wash lifts the cliff behind the shops by the same
# amount, which is finding 121.  What works is the gate's own answer one tier
# down: a faked bounce CARD off the opposite side of the street, no shadow, hard
# cutoff, solved so the fronts reach a fixed fraction of the paving they stand on.
# THE CARD HAS TO COME FROM THE CLIFF SIDE, and working that out from the report
# rather than from the plan is the whole value of running `-- report` first.
# The measured fronts are: inn 6.69, item 4.77 (both face +y, out over the open
# gorge, and are already at 90-109% of the paving they stand on) against weapon
# 2.19 and armor 1.72 (both face -y, into the cliff, at 55% and 47%).  So the
# problem is one SIDE of the street, not the street — and a card hung over the
# gorge, which is the obvious place for one, lights precisely the two fronts that
# do not need it and cannot reach the two that do (a -y-facing surface has its
# back to it; `area_irr` returns zero).  These stand against the cliff crest
# instead, which is also where the real bounce would come from: the sun rakes the
# cliff wall above the street all afternoon.
CARDS = [((31.50, 1.30, 27.20), (36.00, 9.60, 20.50)),
         ((45.00, 1.30, 26.80), (46.50, 11.20, 20.50))]
WANT_FRAC = 0.62
DARK = ["weapon front   (37.4, 8.6) S", "armor front    (44.5,10.7) S"]
TOPS = sum(existing(P) for P in (PROBES["street mid (35.0, 7.0)"],
                                 PROBES["weapon pad (37.8, 5.5)"],
                                 PROBES["armor pad  (44.3, 9.0)"])) / 3.0
HAVE = sum(existing(*FRONTS[k]) for k in DARK) / len(DARK)
WANT = max(0.0, WANT_FRAC * TOPS - HAVE)
rots = [(Vector(a) - Vector(p)).to_track_quat('-Z', 'Y').to_euler()
        for p, a in CARDS]
unit = sum(sum(area_irr(13.0, 8.0, Vector(p), rots[i], 1.0, *FRONTS[k])
               for k in DARK) / len(DARK)
           for i, (p, a) in enumerate(CARDS))
EC = round(WANT / max(unit, 1e-12), 1)
for i, (p, a) in enumerate(CARDS):
    d = bpy.data.lights.new("KEYSH_front_%d" % i, 'AREA')
    d.shape = 'RECTANGLE'
    d.size, d.size_y = 13.0, 8.0
    d.energy = EC
    d.color = (1.0, 0.76, 0.52)
    d.use_shadow = False
    d.use_custom_distance = True
    d.cutoff_distance = 60.0
    ob = bpy.data.objects.new(d.name, d)
    ob.location = Vector(p)
    ob.rotation_euler = rots[i]
    link(ob, COLL)


def card_at(P, N=Vector((0, 0, 1))):
    return sum(area_irr(13.0, 8.0, Vector(p), rots[i], EC, P, N)
               for i, (p, a) in enumerate(CARDS))


log("FILL", "KEYSH_front_0/1: 13 x 8 m, %.0f W each" % EC,
    "the two SHADED (south-facing) fronts %.4f -> %.4f W/m2 (%.0f%% -> %.0f%% of "
    "the paving's own %.4f); no shadow, 60 m cutoff"
    % (HAVE, HAVE + WANT, 100 * HAVE / max(TOPS, 1e-9),
       100 * (HAVE + WANT) / max(TOPS, 1e-9), TOPS))
for k in ("inn front      (27.0, 4.7) N", "item front     (32.6, 5.9) N"):
    P, N = FRONTS[k]
    log("CHECK", "the already-lit %s" % k.split("(")[0].strip(),
        "+%.4f W/m2 on %.4f = %.1f%% — a -y card cannot reach a +y face, which "
        "is the point of putting it on the cliff side"
        % (card_at(P, N), existing(P, N), 100 * card_at(P, N) / max(existing(P, N), 1e-9)))

# ===========================================================================
# 3. SPILL — three accepted regions, not two
# ===========================================================================
print("\n--- 3. spill onto accepted art ---------------------------------------")


def nlant_now():
    return len([o for o in bpy.data.objects if o.type == 'LIGHT'
                and o.name.startswith("KEYSH_") and "lantern" in o.name])


def added(P, N=Vector((0, 0, 1))):
    return (chain_at(P) if N.z > 0.5 else 0.0) + card_at(P, N)


by_add, by_own = added(AIM0), existing(AIM0)
wf_add, wf_own = added(WF), existing(WF)
gt_add = added(GATEP, WESTN)
gt_own = existing(GATEP, WESTN)
# The gate solved this face to 1.8166 W/m2 with its OWN lantern practicals
# excluded (its `existing()` skipped every KEYG_ light).  Quote it on the same
# basis or the comparison is against a 680 W globe 1.4 m from the probe.
gt_basis = existing(GATEP, WESTN, skip=("KEYSH_", "KEYG_"))
log("CHECK", "Boatyard reference (20.5, 29.8, 1.0)",
    "+%.5f W/m2 on %.4f = %.2f%%" % (by_add, by_own, 100 * by_add / max(by_own, 1e-12)))
log("CHECK", "Waterfront boardwalk (58.0, 27.0, 1.4)",
    "+%.5f W/m2 on %.4f = %.2f%%" % (wf_add, wf_own, 100 * wf_add / max(wf_own, 1e-12)))
log("CHECK", "GATE arch west pier (15.7, 4.0, 25.6)",
    "+%.5f W/m2 on %.4f (gate basis, its own KEYG_ lamps excluded: %.4f vs the "
    "1.8166 it solved) = %.2f%%"
    % (gt_add, gt_own, gt_basis, 100 * gt_add / max(gt_basis, 1e-12)))
assert by_add < 0.05 * by_own, "the shelf rig re-values the accepted Boatyard"
assert wf_add < 0.05 * wf_own, "the shelf rig re-values the accepted Waterfront"
assert gt_add < 0.05 * gt_basis, "the shelf rig re-values the accepted gate arch"

print("\n--- 4. the PRACTICALS against the accepted Boatyard -------------------")
# Finding 100 says to compare districts on the SHARED rig, because a district's
# own lanterns dominate its numbers.  The corollary this district needed is that
# the very same fact makes practical DENSITY the thing to check — and the check
# has to be a ratio against a district the user has already ACCEPTED, because
# there is no absolute number to aim a lantern at.
#
# METHOD, and why it is not the obvious one.  The first cut of this check compared
# ONE point (mid-street 35,7) against ONE point (the Boatyard hero's aim) and
# reported 2.8x, then 1.9x after thinning.  That number was mostly an artefact:
# the mid-street probe sits 2.5 m from a hung lantern while the Boatyard's aim
# point is 4.4 m from its nearest one, so the ratio was measuring LAMP PROXIMITY,
# not district exposure.  Two point probes cannot be like-for-like on districts
# with different lamp spacings.
#
# So the check samples the WALKING SURFACE of both districts by the same method
# master_walk_qa.py uses to prove coverage: a down-ray on a 0.75 m grid, accepted
# only where the first thing it hits is a walk_/bar_ mesh, probed 0.60 m above the
# hit, up-facing, every lamp in the file included.  ~100 probes a side.  It is the
# ground a player actually stands on, sampled evenly, on both sides, by one piece
# of code — and it is the number LANT_MIN_SEP in shelf_build.py was solved on.
#
# Both the MEAN and the MAX are reported.  The mean is the district's exposure and
# the thing the ratio gates.  The max matters separately: a street whose mean is
# right but whose peaks are double the reference's is blowing out material in
# pools, which is what finding 129's corollary is about.
BY_REGION = (2.0, 32.0, 19.0, 33.0, -2.0, 8.0)       # the accepted Boatyard
SH_REGION = (17.5, 55.3, 0.5, 14.0, 18.5, 20.5)      # this tier
GRID = 0.75
RATIO_MAX = 1.20


def walk_probes(x0, x1, y0, y1, z0, z1, step=GRID):
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    pts = []
    for i in range(int((x1 - x0) / step) + 1):
        for j in range(int((y1 - y0) / step) + 1):
            ok, loc, nrm, _i, ob, _m = sc.ray_cast(
                dg, Vector((x0 + i * step, y0 + j * step, z1 + 6.0)), Vector((0, 0, -1)))
            if not ok or ob is None:
                continue
            if not ob.name.startswith(("walk_", "bar_")):
                continue
            if not (z0 <= loc.z <= z1) or nrm.z < 0.7:
                continue
            pts.append(loc + Vector((0, 0, 0.60)))
    return pts


def surface_stats(region):
    pts = walk_probes(*region)
    # `skip` empty: this measurement is about the practicals, so every lamp in the
    # file counts, ours included.  n=5 on the area integration, not 11 — over a
    # hundred probes the area sources are a rounding error against 680 W points.
    v = sorted(existing(p, skip=("_NOSKIP_",)) for p in pts)
    n = max(len(v), 1)
    return dict(n=len(v), mean=sum(v) / n, med=v[n // 2] if v else 0.0,
                p90=v[int(0.9 * (n - 1))] if v else 0.0, mx=v[-1] if v else 0.0)


AREA_N = 5
bys, shs = surface_stats(BY_REGION), surface_stats(SH_REGION)
AREA_N = 11
for nm, s in (("BOATYARD (accepted)", bys), ("SHELF tier", shs)):
    print("  %-22s n=%4d  mean %7.3f  median %7.3f  p90 %7.3f  max %7.3f W/m2"
          % (nm, s["n"], s["mean"], s["med"], s["p90"], s["mx"]))
ratio = shs["mean"] / max(bys["mean"], 1e-9)
log("CHECK", "walking-surface mean vs the accepted Boatyard",
    "%.2f W/m2 against %.2f = %.3fx (gate %.2fx); peaks %.1f vs %.1f. "
    "%d practicals: %d shopfront + %d strung, LANT_MIN_SEP 3.0 m."
    % (shs["mean"], bys["mean"], ratio, RATIO_MAX, shs["mx"], bys["mx"], nlant_now(),
       nlant_now() - len([o for o in bpy.data.objects if "lantern_hang" in o.name
                          and o.type == 'LIGHT']),
       len([o for o in bpy.data.objects if "lantern_hang" in o.name and o.type == 'LIGHT'])))
MID = Vector((35.00, 7.00, 19.60))
log("NOTE", "the old single-point ratio, for the record",
    "mid-street %.2f vs the Boatyard aim point %.2f = %.2fx — kept only to show "
    "what it measures: both probes' nearest lantern (2.5 m vs 4.4 m), not the "
    "two districts"
    % (existing(MID, skip=("_NOSKIP_",)), existing(AIM0, skip=("_NOSKIP_",)),
       existing(MID, skip=("_NOSKIP_",)) / max(existing(AIM0, skip=("_NOSKIP_",)), 1e-9)))
assert ratio <= RATIO_MAX, (
    "the shelf practicals are %.3fx the accepted Boatyard's walking surface "
    "(gate %.2fx) — raise LANT_MIN_SEP in shelf_build.py and rebuild"
    % (ratio, RATIO_MAX))
assert shs["mx"] <= 1.35 * bys["mx"], (
    "shelf peak %.1f vs Boatyard peak %.1f — pools are blowing out"
    % (shs["mx"], bys["mx"]))

print("\n--- 5. the street after ----------------------------------------------")
for nm, P in list(PROBES.items())[:-1]:
    print("  %-24s up-facing   %.4f -> %.4f W/m2"
          % (nm, existing(P), existing(P, skip=("_NOSKIP_",))))
for nm, (P, N) in FRONTS.items():
    print("  %-24s street-face %.4f -> %.4f W/m2"
          % (nm, existing(P, N), existing(P, N, skip=("_NOSKIP_",))))

nlant = nlant_now()
print("\n" + "=" * 78)
print("SHELF LIGHT RIG: %d KEYSH_street spots + %d KEYSH_front cards + %d lantern "
      "practicals" % (len(made), len(CARDS), nlant))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
