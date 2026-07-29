"""gate_light.py — the Gate Approach's self-contained KEYG_* rig.

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/gate_light.py -- [save]
  ... -- report        measure only, add nothing

Discipline is the Waterfront's (manifest 65-70), because that is what keeps two
districts looking like one town:

  * a chain that fires ALONG the gorge is narrow-and-many.  KEY_slip's own 48 deg
    cone, replicated, is 20 m across by the time it reaches its neighbour; at
    <= 26 deg the neighbour falls outside it entirely (65).
  * `spot_blend = 1.0`, so eight cones end to end cross-fade instead of scalloping (66).
  * each chain carries a LEVEL against KEY_slip's peak, not against its own peak (67).
  * area sources are solved by integrating the emitter, never scaled by area (68).
  * faked bounce cards cast no shadows and carry a cutoff, because EEVEE's shadow
    budget overflows silently and then the frame is not repeatable (70).

The one thing this district needs that the Waterfront did not: the sun travels
DOWN-gorge (SUN_key's direction is -0.86,-0.35,-0.38), so every surface the
arriving player sees first — the west face of the arch, of the toll house, of the
whole yard — is a shadow side.  `KEYG_approach_*` is the up-gorge bounce that
gives those faces a value; it is a CARD, not a key, and it casts nothing.
"""
import bpy, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import link, coll

SAVE = "save" in sys.argv
REPORT = "report" in sys.argv
COLL = "GATE_DISTRICT"
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-34s %s" % (kind, what, why))


print("=" * 78)
print("GATE APPROACH LIGHT RIG")
print("=" * 78)

KEY = bpy.data.objects["KEY_slip"]
KD = KEY.data
DIR = (KEY.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
AIM0 = Vector((20.5, 29.83, 1.0))                 # the ACCEPTED Boatyard reference point
WF = Vector((58.0, 27.0, 1.4))                    # the accepted Waterfront boardwalk
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

PROBES = {
    "yard  (6.0, 7.5)": Vector((6.0, 7.5, 24.2)),
    "toll  (12.5, 5.5)": Vector((12.5, 5.5, 24.2)),
    "arch  (16.7, 4.0)": Vector((16.7, 4.0, 24.2)),
    "gall. (23.0, 7.0)": Vector((23.0, 7.0, 24.2)),
    "winch (27.3, 7.5)": Vector((27.3, 7.5, 24.2)),
    "BOATYARD ref": AIM0,
}
# a west-facing wall is the surface the arriving player reads the district on
WESTN = Vector((-1.0, 0.0, 0.0))
WESTP = Vector((15.7, 4.0, 25.6))


def existing(P, npn=Vector((0, 0, 1))):
    tot = 0.0
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.name.startswith("KEYG_"):
            continue
        d = o.data
        if d.type == 'SUN':
            dv = (o.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            c = -dv.dot(npn)
            tot += d.energy * max(c, 0.0)
        elif d.type == 'AREA':
            sy = d.size_y if d.shape == 'RECTANGLE' else d.size
            tot += area_irr(d.size, sy, Vector(o.location), o.rotation_euler, d.energy, P, npn)
        elif d.type == 'SPOT':
            dv = (o.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            tot += irr(d.energy, Vector(o.location), P, dv, d.spot_size, d.spot_blend)
        else:
            r = (P - Vector(o.location)).length
            tot += d.energy / (4 * math.pi * max(r, 0.2) ** 2)
    return tot


for nm, P in PROBES.items():
    print("  %-20s up-facing %.4f W/m2" % (nm, existing(P)))
print("  %-20s WEST-facing %.4f W/m2   <- the arrival side"
      % ("arch pier", existing(WESTP, WESTN)))

if REPORT:
    sys.exit(0)

for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith(("KEYG_gate_", "KEYG_approach_")):
        bpy.data.objects.remove(o, do_unlink=True)

# ===========================================================================
# 1. THE KEY CHAIN along the tier
# ===========================================================================
print("\n--- 1. key chain -----------------------------------------------------")
CONE = 24.0
LEVEL = 0.46      # against KEY_slip's own peak: this tier already has full sun,
                  # so the chain is a shaper, not the light source
AIMS = [Vector((x, 6.4, 24.30)) for x in (4.0, 9.5, 15.0, 20.5, 26.0)]
made = []
for i, a in enumerate(AIMS):
    d = KD.copy()
    d.name = "KEYG_gate_%d" % i
    d.spot_size = math.radians(CONE)
    d.spot_blend = 1.0
    d.use_custom_distance = True
    d.cutoff_distance = 46.0
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
log("KEY", "KEYG_gate_0..%d: %.0f deg, %.0f W" % (len(made) - 1, CONE, E),
    "aim x %.0f..%.0f at y=%.1f | irradiance %.3f..%.3f W/m2 (ripple %.0f%%), "
    "%.0f%% of KEY_slip's peak %.3f"
    % (AIMS[0].x, AIMS[-1].x, AIMS[0].y, lo, hi, 100 * (hi - lo) / max(hi, 1e-9),
       100 * LEVEL, PEAK))

spill_by = chain_at(AIM0)
spill_wf = chain_at(WF)
log("CHECK", "spill onto accepted art",
    "Boatyard %.5f W/m2 (%.2f%% of KEY_slip's own %.4f), Waterfront boardwalk %.5f"
    % (spill_by, 100 * spill_by / PEAK, PEAK, spill_wf))
assert spill_by < 0.05 * PEAK and spill_wf < 0.05 * PEAK, "the gate chain re-values accepted art"

# ===========================================================================
# 2. THE APPROACH CARD — a value for the shadow side
# ===========================================================================
print("\n--- 2. approach fill -------------------------------------------------")
# The sun runs DOWN the gorge, so the arriving player looks straight into the
# shadow side of everything.  This is a faked up-gorge bounce off the valley
# wall: a card, no shadow, hard cutoff, aimed east at the gate precinct.  It is
# solved so the west faces reach a fixed fraction of what the tier's own sunlit
# top gets — measured, not chosen by eye.
CARD = [(-4.60, 5.20, 27.60), (-4.20, 9.60, 27.20)]
AIMC = Vector((13.00, 5.60, 25.40))
TOP = existing(PROBES["arch  (16.7, 4.0)"])
HAVE = existing(WESTP, WESTN)
# v6 held the shadow side at 55% of the sunlit top and stopped there, because
# above that the card was washing the raking sun off the tier.  What it was
# actually washing out was the 20 m of CLIFF behind the gate, which at the time
# wore the same `mat_rock` as the gate's own masonry — lifting the shadow side
# lifted the backdrop by the same fraction, so nothing separated and the whole
# frame just got paler.  The build now gives that veneer `mat_gate_cliff`, a
# third darker and cooler, so the backdrop absorbs what the card adds and the
# dressed stone in front of it does not.  That buys the arrival side most of
# another stop for free: 0.66, from the same measurement, sun still raking.
WANT = max(0.0, 0.66 * TOP - HAVE)
rot = (Vector(AIMC) - Vector(CARD[0])).to_track_quat('-Z', 'Y').to_euler()
unit = sum(area_irr(11.0, 7.0, Vector(p), rot, 1.0, WESTP, WESTN) for p in CARD)
EC = round(WANT / max(unit, 1e-12), 1)
for i, p in enumerate(CARD):
    d = bpy.data.lights.new("KEYG_approach_%d" % i, 'AREA')
    d.shape = 'RECTANGLE'
    d.size, d.size_y = 11.0, 7.0
    d.energy = EC
    d.color = (1.0, 0.72, 0.46)
    d.use_shadow = False
    # NOT a tight cutoff: a card with `use_shadow = False` costs the shadow budget
    # nothing, and at 34 m the cutoff SPHERE cut a hard rectangular edge straight
    # across the promontory's cliff face in `fromgorge`.  The spill assertion
    # below is the real guarantee, not the cutoff.
    d.use_custom_distance = True
    d.cutoff_distance = 75.0
    ob = bpy.data.objects.new(d.name, d)
    ob.location = Vector(p)
    ob.rotation_euler = rot
    link(ob, COLL)
add_by = sum(area_irr(11.0, 7.0, Vector(p), rot, EC, AIM0) for p in CARD)
own_by = existing(AIM0)
log("FILL", "KEYG_approach_0/1: 11 x 7 m, %.0f W each" % EC,
    "west-facing value at the arch %.4f -> %.4f W/m2 (%.0f%% -> %.0f%% of its "
    "sunlit top %.4f); no shadow, 75 m cutoff"
    % (HAVE, HAVE + WANT, 100 * HAVE / TOP, 100 * (HAVE + WANT) / TOP, TOP))
log("CHECK", "approach card at the Boatyard",
    "%.5f W/m2 = %.1f%% of the yard's existing %.5f"
    % (add_by, 100 * add_by / max(own_by, 1e-12), own_by))
assert add_by < 0.06 * own_by, "the approach card re-values the accepted Boatyard"

print("\n" + "=" * 78)
print("GATE LIGHT RIG: %d KEYG_gate spots + %d KEYG_approach cards + %d lantern practicals"
      % (len(made), len(CARD),
         len([o for o in bpy.data.objects if o.type == 'LIGHT' and "lantern" in o.name
              and o.name.startswith("KEYG_")])))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
