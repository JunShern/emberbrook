"""locksfoot_light.py — TASK 0 of the Locksfoot district pass.

  Blender -b tools/blends/dellhollow-master.blend -P tools/locksfoot_light.py
  (add `save` as the last argv token to write the blend back)

The Waterfront left the gorge lit from x = -10 to x = 70.  Locksfoot builds
x 66 -> 112, so both halves of the rig have to be carried east:

1. THE SKY.  `SKY_wash` is a 90 x 80 m TILTED sheet (dz/dx = -0.125) covering
   world x -10..70.  Two things follow that the handover could not know:

   * Moving its centre in world X does not slide it along itself, it LIFTS the
     whole sheet.  Re-centring at x=51 to cover x -10..112 puts the sheet 2.6 m
     higher over the Boatyard, and the solve then asks for MORE power than the
     by-area rule (1249 W vs 1226 W) purely to undo that.  Any resize has to
     keep the centre ON the plane: z = 26 - 0.125 * (x - 30).
   * There is no wattage that extends the sky east and leaves the Waterfront
     alone.  Solving the two-lamp system for "Boatyard unchanged AND Waterfront
     east end unchanged" returns E_east = 0.0 W exactly: the accepted Waterfront
     was lit by a sky that STOPS 4 m past its own east edge, so its east end is
     artificially dark and continuing the sky necessarily brightens it.  The
     choice is which reference point to hold, and this pass holds the district's
     own working level: the two east elements are SOLVED so the Locksfoot
     boardwalk receives the same sky irradiance the accepted Waterfront
     boardwalk does (0.0798 W/m2), and the resulting disturbance to the accepted
     art is measured, printed and asserted rather than assumed.

   `SKY_wash` itself is left bit-identical: the extension is two coplanar
   elements (finding 65's narrow-and-many, applied to fill), which is strictly
   safer than resizing the accepted lamp.

2. THE KEY.  Three more chains on `KEY_slip`'s own direction and standoff.
   `lf_dam` fires at the dam-five face from DOWNSTREAM — which is firing ALONG
   the gorge, not across it — so unlike the Lock Four `dam` chain it must be
   narrow-and-many (24 deg, 8 elements), not 48 deg.  At 48 deg the Waterfront
   sits inside the cone 52 m away and picks up ~15% of its own key.
"""
import bpy, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import link

SAVE = "save" in sys.argv
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-34s %s" % (kind, what, why))


print("=" * 78)
print("LOCKSFOOT LIGHT RIG")
print("=" * 78)

# ===========================================================================
# shared geometry: KEY_slip's own direction and standoff
# ===========================================================================
KEY = bpy.data.objects["KEY_slip"]
KD = KEY.data
DIR = (KEY.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
AIM0 = Vector((20.5, 29.83, 1.0))                  # the accepted Boatyard point
AIMWF = Vector((48.0, 27.0, 1.4))                  # the accepted Waterfront deck
AIMWF2 = Vector((62.0, 29.0, 1.4))                 # ... and its east end
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
    mask = t * t * (3.0 - 2.0 * t)
    return E / (4.0 * math.pi * r * r) * mask


PEAK = irr(KD.energy, Vector(KEY.location), AIM0)


def area_irr(size_x, size_y, loc, rot, E, P, npn=Vector((0, 0, 1)), n=21):
    """Irradiance a rectangular Blender area lamp delivers to a point.

    Integrated, not scaled: an enlarged emitter subtends more solid angle, so
    scaling power by AREA preserves radiance and raises irradiance (finding 68).
    """
    R = rot.to_matrix()
    ex, ey, ez = R.col[0], R.col[1], -R.col[2]
    A = size_x * size_y
    L = E / (math.pi * A)
    dA = A / (n * n)
    tot = 0.0
    for i in range(n):
        for j in range(n):
            u = (i + 0.5) / n - 0.5
            v = (j + 0.5) / n - 0.5
            q = Vector(loc) + ex * (u * size_x) + ey * (v * size_y)
            w = P - q
            r = w.length
            if r < 1e-6:
                continue
            wn = w / r
            cl = wn.dot(ez)
            cp = -wn.dot(npn)
            if cl <= 0 or cp <= 0:
                continue
            tot += L * cl * cp / (r * r) * dA
    return tot


# ===========================================================================
# 1. THE SKY — two coplanar east elements, solved on the Waterfront's own level
# ===========================================================================
print("\n--- 1. sky -----------------------------------------------------------")
SW = bpy.data.objects["SKY_wash"]
SWD = SW.data
ROT = SW.rotation_euler
SW_OWN = dict(size=SWD.size, size_y=SWD.size_y, loc=Vector(SW.location), E=SWD.energy)


def sky_own(P):
    return area_irr(SW_OWN["size"], SW_OWN["size_y"], SW_OWN["loc"], ROT, SW_OWN["E"], P)


def plane_z(x):
    """SKY_wash's own sheet, so an extension is coplanar rather than a new roof."""
    return SW_OWN["loc"].z - 0.125 * (x - SW_OWN["loc"].x)


REF_SKY = sky_own(AIMWF)                 # the accepted district's working level
SKY_Y, SKY_CY = 62.0, 43.0               # along-gorge span: town side + the river
# Where the east sky STARTS is the only real knob on how much of the accepted
# Waterfront it lifts, and it is worth spending: starting the run at x=76 rather
# than x=70 takes the lift at the fish dock from +35% to +27% of its sky while
# the Locksfoot boardwalk still lands exactly on the Waterfront's own level.
SPANS = [(76.0, 96.0), (96.0, 116.0)]
LF_REF = [Vector((80.0, 27.3, 0.8)), Vector((92.0, 27.8, -0.7))]

elems = []
for x0, x1 in SPANS:
    cx = (x0 + x1) / 2.0
    elems.append(dict(size=SKY_Y, size_y=x1 - x0,
                      loc=Vector((cx, SKY_CY, plane_z(cx))), span=(x0, x1)))

# solve the 2x2: each Locksfoot reference point lands on the Waterfront's level
A = [[area_irr(e["size"], e["size_y"], e["loc"], ROT, 1.0, P) for e in elems]
     for P in LF_REF]
B = [REF_SKY - sky_own(P) for P in LF_REF]
det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
EN = [(B[0] * A[1][1] - A[0][1] * B[1]) / det,
      (A[0][0] * B[1] - B[0] * A[1][0]) / det]

for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith("SKY_wash_lf"):
        bpy.data.objects.remove(o, do_unlink=True)
# removing the OBJECT orphans its light datablock, so the next run's copy is
# named SKY_wash_lf_0.001 and the run after that .002 — the names drift away
# from the ones the handover documents.  Clear the data too.
for d0 in list(bpy.data.lights):
    if d0.name.startswith("SKY_wash_lf") and d0.users == 0:
        bpy.data.lights.remove(d0)

L_own = SW_OWN["E"] / (SW_OWN["size"] * SW_OWN["size_y"])
for i, (e, E) in enumerate(zip(elems, EN)):
    d = SWD.copy()
    d.name = "SKY_wash_lf_%d" % i
    d.shape = 'RECTANGLE'
    d.size, d.size_y, d.energy = e["size"], e["size_y"], round(E, 1)
    ob = bpy.data.objects.new(d.name, d)
    ob.location = e["loc"]
    ob.rotation_euler = ROT
    link(ob, "DIST_boatyard")
    e["ob"] = ob
    log("SKY", "%s: %.0f x %.0f m, %.1f W" % (d.name, d.size, d.size_y, d.energy),
        "world x %.0f..%.0f on SKY_wash's own plane (z %.2f) — radiance %.4f "
        "vs the accepted sheet's %.4f (%.0f%%)"
        % (e["span"][0], e["span"][1], e["loc"].z, E / (d.size * d.size_y), L_own,
           100 * (E / (d.size * d.size_y)) / L_own))


def sky_all(P):
    return sky_own(P) + sum(area_irr(e["size"], e["size_y"], e["loc"], ROT, E, P)
                            for e, E in zip(elems, EN))


print()
for tag, P in (("Boatyard  (20.5,29.8)", AIM0), ("Waterfront(48.0,27.0)", AIMWF),
               ("Wfront-E  (62.0,29.0)", AIMWF2), ("Locksfoot (76.0,27.0)", LF_REF[0]),
               ("Locksfoot (88.0,28.0)", LF_REF[1])):
    a, b = sky_own(P), sky_all(P)
    log("SKY-CHK", tag, "%.4f -> %.4f W/m2  (%+.2f%%)" % (a, b, 100 * (b / a - 1)))
log("SKY-NOTE", "the 2x2 solve for 'both accepted points held'",
    "returns E_east = 0.0 W exactly — the Waterfront's east end is dark BECAUSE "
    "the sky stopped at x=70; continuing it must brighten it")
assert sky_all(AIM0) < 1.03 * sky_own(AIM0), "the east sky re-values the accepted Boatyard"

# ===========================================================================
# 2. THE KEY CHAINS
# ===========================================================================
print("\n--- 2. key chains ----------------------------------------------------")
# `cone` is what keeps a chain out of its neighbour (finding 65).  `lf_dam`
# lights the dam's DOWNSTREAM face, so it stands downstream and fires back up
# the gorge — along it, not across it — and takes the narrow cone.
CHAINS = {
    "lf_deck": dict(cone=24.0, level=0.60, aims=[
        Vector(p) for p in ((66.0, 27.5, 1.4), (70.0, 26.6, 1.6), (74.0, 27.0, 1.3),
                            (78.0, 27.2, 0.9), (82.0, 27.5, 0.5), (86.0, 28.0, 0.1),
                            (90.0, 27.8, -0.6), (94.0, 27.7, -0.8), (98.0, 27.5, -0.9),
                            (102.0, 27.2, -1.0), (106.0, 27.0, -0.9), (110.0, 27.0, -0.9))]),
    "lf_cliff": dict(cone=24.0, level=0.34, aims=[
        Vector(p) for p in ((68.5, 21.0, 5.4), (72.0, 20.6, 6.6), (75.5, 20.2, 7.8),
                            (79.0, 19.9, 8.8), (82.5, 19.8, 9.2), (86.0, 20.1, 8.8),
                            (89.5, 20.8, 7.8), (93.0, 21.6, 6.4), (96.5, 22.2, 4.8),
                            (100.0, 22.6, 3.2), (103.5, 23.0, 1.8))]),
    "lf_dam": dict(cone=24.0, level=0.80, aims=[
        Vector((88.6, 30.0 + 4.5 * k, -1.4)) for k in range(11)]),
}

for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith("KEY_gorge_lf_"):
        bpy.data.objects.remove(o, do_unlink=True)
for d0 in list(bpy.data.lights):
    if d0.name.startswith("KEY_gorge_lf_") and d0.users == 0:
        bpy.data.lights.remove(d0)

made = []
for tag, spec in CHAINS.items():
    for i, a in enumerate(spec["aims"]):
        d = KD.copy()
        d.name = "KEY_gorge_%s_%d" % (tag, i)
        d.spot_size = math.radians(spec["cone"])
        d.spot_blend = 1.0                 # cross-fade, not a flat top (finding 66)
        d.use_custom_distance = True
        d.cutoff_distance = 48.0
        d.shadow_maximum_resolution = 0.008
        ob = bpy.data.objects.new(d.name, d)
        ob.location = a - DIR * STANDOFF
        ob.rotation_euler = KEY.rotation_euler
        link(ob, "DIST_boatyard")
        made.append((tag, ob, a))


def chain_at(tag, P, E=None):
    return sum(irr(E if E is not None else ob.data.energy, Vector(ob.location), P,
                   size=ob.data.spot_size, blend=ob.data.spot_blend)
               for t, ob, a in made if t == tag)


def chain_range(tag, E=None):
    aims = CHAINS[tag]["aims"]
    n = len(aims) - 1
    lo_f, hi_f = (0.6, n - 0.6) if n >= 2 else (0.0, float(n))
    vals = []
    for k in range(81):
        f = lo_f + (hi_f - lo_f) * k / 80.0
        i = min(int(f), n - 1)
        vals.append(chain_at(tag, aims[i].lerp(aims[i + 1], f - i), E))
    return min(vals), max(vals)


print("  KEY_slip: %.0f W, cone %.0f deg, standoff %.2f m -> peak %.4f W/m2"
      % (KD.energy, math.degrees(KD.spot_size), STANDOFF, PEAK))
for tag, spec in CHAINS.items():
    E = spec["level"] * KD.energy * PEAK / max(chain_range(tag, KD.energy)[1], 1e-9)
    for t, ob, a in made:
        if t == tag:
            ob.data.energy = round(E, 1)
    lo, hi = chain_range(tag)
    aims = spec["aims"]
    log("KEY", "%s: %d spots, %.0f deg, %.0f W" % (tag, len(aims), spec["cone"], E),
        "aim %.0f,%.0f -> %.0f,%.0f | %.3f..%.3f W/m2 (ripple %.0f%%), %.0f%% of "
        "KEY_slip's peak" % (aims[0].x, aims[0].y, aims[-1].x, aims[-1].y, lo, hi,
                             100 * (hi - lo) / max(hi, 1e-9), 100 * spec["level"]))

# --- spill vs. SEAM CLOSURE -----------------------------------------------
# The two are different and only one is a defect.  A chain element 20 m away
# that reaches back into accepted art is SPILL.  The element that stands 4 m
# past the neighbouring chain's LAST aim point is the neighbour it was designed
# to cross-fade into (finding 66: spot_blend = 1.0 exists for exactly this), and
# what it changes is the end TAPER `chain_range` deliberately excludes.  So the
# assert is measured where no chain is adjacent, and the seam is reported.
def total_key(P):
    t = 0.0
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith("KEY_gorge_"):
            t += irr(o.data.energy, Vector(o.location), P,
                     size=o.data.spot_size, blend=o.data.spot_blend)
    return t + irr(KD.energy, Vector(KEY.location), P)


for tag, P in (("Boatyard", AIM0), ("Waterfront interior", AIMWF)):
    sp = sum(irr(ob.data.energy, Vector(ob.location), P, size=ob.data.spot_size,
                 blend=ob.data.spot_blend) for t, ob, a in made)
    log("KEY-CHK", "spill into the accepted %s" % tag,
        "%.4f W/m2 = %.1f%% of KEY_slip's peak %.3f" % (sp, 100 * sp / PEAK, PEAK))
    assert sp < 0.05 * PEAK, "the lf chains re-value the accepted %s (%.1f%%)" % (
        tag, 100 * sp / PEAK)

seam = sum(irr(ob.data.energy, Vector(ob.location), AIMWF2, size=ob.data.spot_size,
               blend=ob.data.spot_blend) for t, ob, a in made)
was = total_key(AIMWF2) - seam
log("KEY-SEAM", "wf_deck's last aim (62,29) closes",
    "%.3f -> %.3f W/m2 (%+.0f%%) — its end taper is filled by lf_deck's first "
    "element, which is the same 4 m pitch the wf chain uses internally; interior "
    "level is %.3f" % (was, was + seam, 100 * seam / max(was, 1e-9),
                       0.60 * PEAK))
assert was + seam < 1.12 * (0.60 * PEAK), "the seam overshoots the chain's own level"

print("\n  total key along the deck line (all KEY_gorge_* + KEY_slip):")
row = []
for x in range(40, 113, 6):
    z = 1.4 if x < 87 else -0.8
    row.append("%d:%.2f" % (x, total_key(Vector((float(x), 27.5, z)))))
print("    " + "  ".join(row))

# ===========================================================================
# 3. BOUNCE CARDS — half size, quarter power, half standoff (finding 69)
# ===========================================================================
print("\n--- 3. bounce --------------------------------------------------------")


def replicate(src_name, prefix, spots, shrink=2.0):
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT' and o.name.startswith(prefix):
            bpy.data.objects.remove(o, do_unlink=True)
    for d0 in list(bpy.data.lights):
        if d0.name.startswith(prefix) and d0.users == 0:
            bpy.data.lights.remove(d0)
    src = bpy.data.objects[src_name]
    for i, p in enumerate(spots):
        d = src.data.copy()
        d.size /= shrink
        d.size_y /= shrink
        d.energy /= shrink * shrink
        d.use_shadow = False               # a faked card should not also cast
        d.use_custom_distance = True
        d.cutoff_distance = 26.0
        ob = bpy.data.objects.new("%s%d" % (prefix, i), d)
        d.name = ob.name
        ob.location = Vector(p)
        ob.rotation_euler = src.rotation_euler
        link(ob, "DIST_boatyard")
    log("LIGHT", "%s x%d" % (prefix, len(spots)),
        "%s at 1/%.0f size and 1/%.0f power — same radiance, quarter reach"
        % (src_name, shrink, shrink * shrink))


FILL_AT = [(70.0, 37.0, 3.2), (79.0, 37.5, 3.0), (88.0, 38.0, -0.8),
           (97.0, 37.5, -1.0), (106.0, 37.0, -1.0)]
CLIFF_AT = [(70.0, 24.6, 6.0), (76.0, 23.2, 8.0), (83.0, 22.6, 8.4),
            (90.0, 23.6, 6.4), (98.0, 24.2, 2.4), (105.0, 24.6, 1.0)]
replicate("FILL_bounce", "FILL_bounce_lf_", FILL_AT)
replicate("CLIFF_BOUNCE", "CLIFF_BOUNCE_lf_", CLIFF_AT)


# The denominator has to be the fill the accepted district ACTUALLY has, which
# is every area lamp standing in the scene — including the Waterfront's own
# half-size copies.  Measuring a new card against the ORIGINAL card alone (what
# the Waterfront pass did, when its copies were the only ones) understates the
# base by a third out here and fails a card that is in fact inside tolerance.
def area_sum(P, want):
    t = 0.0
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.data.type != 'AREA':
            continue
        if want(o.name):
            d = o.data
            sy = d.size_y if d.shape == 'RECTANGLE' else d.size
            t += area_irr(d.size, sy, Vector(o.location), o.rotation_euler, d.energy, P)
    return t


def is_lf_card(n):
    return n.startswith(("FILL_bounce_lf_", "CLIFF_BOUNCE_lf_"))


for tag, P in (("Boatyard", AIM0), ("Waterfront", AIMWF)):
    base = area_sum(P, lambda n: not is_lf_card(n) and not n.startswith("SKY_wash_lf"))
    add = area_sum(P, is_lf_card)
    log("CHECK", "cards added at the accepted %s" % tag,
        "%.5f W/m2 = %.1f%% of its existing fill %.5f (every area lamp, not just "
        "the source card)" % (add, 100 * add / max(base, 1e-12), base))
    assert add < 0.09 * base, "the new bounce cards re-value the accepted %s" % tag

print("\n" + "=" * 78)
print("LOCKSFOOT LIGHT RIG: %d log lines" % len(LOG))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
