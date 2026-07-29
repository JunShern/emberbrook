"""weave_light.py — TASK 0 of the Weave (mid-tier) district pass.

  Blender -b tools/blends/dellhollow-master.blend -P tools/weave_light.py -- [save]

The Weave is the first district that is neither at water level nor on the rim:
it hangs on the cliff between z 6 and z 14, directly ABOVE the Waterfront's and
Locksfoot's boardwalks and directly BELOW the Quay.  Two consequences the
water-level passes never had to think about:

1. The gorge key chains are aimed at the DECK LINE (z ~ 1) and at the CLIFF
   (`wf_cliff` / `lf_cliff`, aimed z 5..9).  The Weave tier sits in the gap
   between them, and — more importantly — the cliff chains are aimed at the ROCK
   the Weave now stands in front of, so the district is lit from behind its own
   massing.  What is missing is not brightness, it is a key that reaches the
   stilt frontages.  This rig measures first and solves for the shortfall
   against the accepted districts' own working level rather than inventing one.

2. Everything this district adds is BETWEEN an existing lamp and the art that
   lamp was solved against.  A stilt forest 10 m tall standing over the
   Waterfront's boardwalk is a shadow caster in someone else's accepted frame.
   That cost is measured (`weave_shots.py` `wfcontinuity` / `fromquay`) and
   reported, not asserted away — geometry occlusion is not something a wattage
   can undo, and pretending otherwise would mean lifting the Waterfront.

Naming: every light this pass owns is `KEYW_*` (chains, cards and practicals),
so a later pass can clear the whole rig with one prefix — and, per finding 117,
the clean-up matches the PREFIX and clears the orphaned light DATABLOCKS too.
"""
import bpy, math, sys
from mathutils import Vector, Euler

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import link

SAVE = "save" in sys.argv
COLL = "DIST_weave"
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-36s %s" % (kind, what, why))


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


coll(COLL)
print("=" * 78)
print("WEAVE LIGHT RIG   (mid tier: Westweave / pilot cluster / Weave huts / cottage)")
print("=" * 78)

# ===========================================================================
# shared geometry — KEY_slip's own direction and standoff, as every chain uses
# ===========================================================================
KEY = bpy.data.objects["KEY_slip"]
KD = KEY.data
DIR = (KEY.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
AIM0 = Vector((20.5, 29.83, 1.0))            # the accepted Boatyard reference
AIMWF = Vector((48.0, 27.0, 1.4))            # the accepted Waterfront boardwalk
AIMLF = Vector((80.0, 27.3, 0.8))            # the accepted Locksfoot boardwalk
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


PEAK = irr(KD.energy, Vector(KEY.location), AIM0)


def area_irr(size_x, size_y, loc, rot, E, P, npn=Vector((0, 0, 1)), n=17):
    R = rot.to_matrix()
    ex, ey, ez = R.col[0], R.col[1], -R.col[2]
    A = size_x * size_y
    L = E / (math.pi * A)
    dA = A / (n * n)
    tot = 0.0
    for i in range(n):
        for j in range(n):
            q = (Vector(loc) + ex * (((i + 0.5) / n - 0.5) * size_x)
                 + ey * (((j + 0.5) / n - 0.5) * size_y))
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


# ---------------------------------------------------------------- clean-up
# finding 117: match the PREFIX, and clear the orphaned light datablocks too, or
# the next run's lamp is KEYW_....001 and eight rebuilds stack 45 practicals.
killed = 0
for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith("KEYW_"):
        bpy.data.objects.remove(o, do_unlink=True)
        killed += 1
for d in list(bpy.data.lights):
    if d.name.startswith("KEYW_") and d.users == 0:
        bpy.data.lights.remove(d)
if killed:
    log("REBUILD", "%d KEYW_ lamps cleared" % killed, "previous rig removed before rebuild")

# ===========================================================================
# 1. MEASURE — what does the tier already receive?
# ===========================================================================
print("\n--- 1. what the tier already gets ------------------------------------")


def key_all(P):
    t = irr(KD.energy, Vector(KEY.location), P)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith(("KEY_gorge_", "KEYW_gorge_")):
            t += irr(o.data.energy, Vector(o.location), P,
                     size=o.data.spot_size, blend=o.data.spot_blend)
    return t


# the tier's own working line: the frontages of the four clusters, at the height
# a hut's wall actually faces the gorge from
TIER = [Vector(p) for p in ((46.0, 20.4, 11.4), (49.5, 21.2, 11.4), (52.5, 21.8, 11.0),
                            (56.5, 21.6, 10.2), (60.0, 23.0, 10.2), (63.5, 23.4, 9.6),
                            (66.5, 25.0, 8.0), (69.5, 24.6, 9.0), (73.0, 26.2, 9.0),
                            (76.0, 24.0, 8.6), (82.0, 23.0, 8.2), (88.0, 22.6, 8.4),
                            (92.5, 23.4, 9.2), (95.0, 24.2, 8.0))]
have = [key_all(P) for P in TIER]
REF_LEVEL = 0.60 * PEAK               # `wf_deck` / `lf_deck`'s own working level
log("MEASURE", "KEY_slip peak (the town's unit)", "%.4f W/m2" % PEAK)
log("MEASURE", "accepted deck working level (0.60)", "%.4f W/m2" % REF_LEVEL)
log("MEASURE", "the Weave tier receives", "%.4f .. %.4f W/m2 (mean %.4f) = %.0f%% of "
    "the deck level — the cliff chains are aimed at the ROCK BEHIND the tier, so "
    "its frontages are the darkest built surface in the gorge"
    % (min(have), max(have), sum(have) / len(have),
       100 * (sum(have) / len(have)) / REF_LEVEL))

# ===========================================================================
# 2. THE WEAVE KEY CHAIN
# ===========================================================================
print("\n--- 2. key chain -----------------------------------------------------")
# finding 65: a chain that fires ALONG the gorge is narrow-and-many, or it puts
# its neighbour's district back inside its own cone 20 m down the beam.  This one
# runs the whole tier, so it takes the same 24 deg the deck and cliff chains use.
AIMS = [Vector(p) for p in ((44.5, 20.0, 11.6), (48.0, 20.6, 11.6), (51.5, 21.2, 11.2),
                            (55.0, 21.4, 10.4), (58.5, 22.2, 10.2), (62.0, 23.0, 9.8),
                            (65.5, 24.2, 8.4), (69.0, 24.2, 9.0), (72.5, 25.4, 9.0),
                            (76.0, 24.0, 8.6), (79.5, 23.2, 8.2), (83.0, 23.0, 8.2),
                            (86.5, 22.8, 8.2), (90.0, 22.6, 8.6), (93.5, 23.2, 9.2),
                            (97.0, 24.0, 8.0))]
CONE = 24.0
LEVEL = 0.52          # deliberately UNDER the deck's 0.60 — see the note below

made = []
for i, a in enumerate(AIMS):
    d = KD.copy()
    d.name = "KEYW_gorge_weave_%d" % i
    d.spot_size = math.radians(CONE)
    d.spot_blend = 1.0                       # cross-fade, not a flat top (finding 66)
    d.use_custom_distance = True
    d.cutoff_distance = 46.0
    d.shadow_maximum_resolution = 0.008      # give EEVEE's budget back (finding 70)
    ob = bpy.data.objects.new(d.name, d)
    ob.location = a - DIR * STANDOFF
    ob.rotation_euler = KEY.rotation_euler
    link(ob, COLL)
    made.append((ob, a))


def chain_at(P, E=None):
    return sum(irr(E if E is not None else ob.data.energy, Vector(ob.location), P,
                   size=ob.data.spot_size, blend=ob.data.spot_blend)
               for ob, a in made)


def chain_range(E=None):
    n = len(AIMS) - 1
    vals = []
    for k in range(81):
        f = 0.6 + (n - 1.2) * k / 80.0
        i = min(int(f), n - 1)
        vals.append(chain_at(AIMS[i].lerp(AIMS[i + 1], f - i), E))
    return min(vals), max(vals)


# solve the wattage so the chain's own interior peak lands on LEVEL x PEAK, then
# subtract what the tier ALREADY has: the chain supplies the shortfall, it does
# not re-light a surface the cliff chains are already reaching.
short = max(REF_LEVEL * (LEVEL / 0.60) - sum(have) / len(have), 0.0)
E = KD.energy * short / max(chain_range(KD.energy)[1], 1e-9)
for ob, a in made:
    ob.data.energy = round(E, 1)
lo, hi = chain_range()
log("KEY", "KEYW_gorge_weave x%d: %.0f deg, %.0f W" % (len(AIMS), CONE, E),
    "aim %.0f,%.0f -> %.0f,%.0f | %.4f..%.4f W/m2 (ripple %.0f%%)"
    % (AIMS[0].x, AIMS[0].y, AIMS[-1].x, AIMS[-1].y, lo, hi,
       100 * (hi - lo) / max(hi, 1e-9)))
now = [key_all(P) for P in TIER]
log("KEY", "tier level %.4f -> %.4f W/m2" % (sum(have) / len(have), sum(now) / len(now)),
    "%.0f%% of the accepted deck level.  Held UNDER 0.60 deliberately: p-westweave's "
    "own intent is 'tucked under the quay's shadow ... the town's poorer corner', and "
    "a tier lit TO the boardwalk's level stops reading as under-the-quay at all."
    % (100 * (sum(now) / len(now)) / REF_LEVEL))

# --- spill into accepted districts ----------------------------------------
for tag, P in (("Boatyard", AIM0), ("Waterfront boardwalk", AIMWF),
               ("Locksfoot boardwalk", AIMLF)):
    sp = chain_at(P)
    log("KEY-CHK", "spill into the accepted %s" % tag,
        "%.5f W/m2 = %.2f%% of KEY_slip's peak" % (sp, 100 * sp / PEAK))
    assert sp < 0.05 * PEAK, "the weave chain re-values the accepted %s (%.1f%%)" % (
        tag, 100 * sp / PEAK)

# ===========================================================================
# 3. BOUNCE — the tier's UNDERSIDE is what the districts below actually see
# ===========================================================================
print("\n--- 3. bounce --------------------------------------------------------")
# Finding 69, used for a new reason.  The Weave's soffits, joists and pile tops
# are what the Waterfront and Locksfoot cameras look UP at, and no key in the
# town points upward.  Small up-facing cards under the tier, half size / quarter
# power off the shared FILL card, keep those undersides from going to black
# without touching a single lamp the accepted districts were solved against.
def replicate(src_name, prefix, spots, shrink=2.0, rot=None, cutoff=20.0):
    src = bpy.data.objects[src_name]
    for i, p in enumerate(spots):
        d = src.data.copy()
        d.size /= shrink
        d.size_y /= shrink
        d.energy /= shrink * shrink
        d.use_shadow = False                 # a faked card must not also cast
        d.use_custom_distance = True
        d.cutoff_distance = cutoff
        ob = bpy.data.objects.new("%s%d" % (prefix, i), d)
        d.name = ob.name
        ob.location = Vector(p)
        ob.rotation_euler = src.rotation_euler if rot is None else rot
        link(ob, COLL)
    log("LIGHT", "%s x%d" % (prefix, len(spots)),
        "%s at 1/%.0f size, 1/%.0f power — same radiance, quarter reach"
        % (src_name, shrink, shrink * shrink))


# A DOWN-facing card cannot live on this tier at all, and shrinking is not the
# answer.  Two versions were measured: eight down-facing cards from x=46 put 23%
# of the Waterfront's own fill back on it, and pulling the run east + shrinking to
# 1/3.2 only moved the problem to Locksfoot (17%).  The reason is geometric, not
# a wattage: this district hangs DIRECTLY OVER two accepted boardwalks, and a card
# that fires down over the Weave is a card that fires down onto them.  Finding 69
# (shrink, don't move) is about reach; this is about DIRECTION.
#
# What the tier actually needs lit is its FRONTAGES, which face the gorge (+y).
# So the cards stand just gorge-ward of the frontages and fire back at the cliff
# (-y, horizontal).  Any accepted deck further out in y then sits BEHIND the
# emitter, where the lamp's own cosine is negative and the contribution is zero
# by construction — the same reason the up-facing soffit cards are safe.  It also
# happens to be the physically honest card: what would really bounce onto a stilt
# frontage at dusk is the lit water and the far wall, both of them out in +y.
CLIFF_AT = [(46.0, 24.6, 11.4), (52.0, 25.0, 11.2), (58.0, 25.4, 10.6),
            (64.0, 26.0, 10.0), (70.0, 26.4, 9.6), (76.0, 25.8, 9.4),
            (84.0, 25.0, 9.2), (92.0, 25.6, 9.6)]
replicate("CLIFF_BOUNCE", "KEYW_CLIFF_", CLIFF_AT, shrink=3.0,
          rot=Euler((-math.pi / 2, 0.0, 0.0)), cutoff=16.0)

# Up-facing soffit cards: the same shared card rolled 180 deg about X so it fires
# UP.  A point BELOW one of these receives nothing by construction (the emitter's
# cosine is negative there), which is why they may stand over accepted art at all.
SOFFIT_AT = [(50.0, 21.5, 4.6), (58.0, 22.5, 3.8), (66.0, 24.5, 1.8),
             (73.0, 26.0, 1.4), (94.0, 25.0, 3.2), (105.5, 27.0, -2.2)]
replicate("FILL_bounce", "KEYW_SOFFIT_", SOFFIT_AT, shrink=3.2,
          rot=Euler((math.pi, 0.0, 0.0)), cutoff=14.0)


def area_sum(P, want):
    t = 0.0
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.data.type != 'AREA' or not want(o.name):
            continue
        d = o.data
        sy = d.size_y if d.shape == 'RECTANGLE' else d.size
        t += area_irr(d.size, sy, Vector(o.location), o.rotation_euler, d.energy, P)
    return t


mine = lambda n: n.startswith("KEYW_")
for tag, P in (("Boatyard", AIM0), ("Waterfront", AIMWF), ("Locksfoot", AIMLF)):
    base = area_sum(P, lambda n: not mine(n))
    add = area_sum(P, mine)
    log("CHECK", "cards added at the accepted %s" % tag,
        "%.6f W/m2 = %.2f%% of its existing fill %.5f" % (add, 100 * add / max(base, 1e-12), base))
    assert add < 0.09 * base, "the weave cards re-value the accepted %s" % tag

# ===========================================================================
# 4. PRACTICALS — ordinary lanterns, per world canon
# ===========================================================================
print("\n--- 4. practicals ----------------------------------------------------")
# The Heartlights are rare and magical; everything hanging in a working town is
# an ORDINARY lantern.  Same 680 W / 14 m cutoff bulb the Boatyard, Waterfront
# and Locksfoot all use, so the town has one lantern, not four.
# The MESHES are built by weave_build.py; this rig owns only the bulbs, and it
# reads their positions from the district's own lantern props if they exist yet
# (so a light-then-build order works, and a rebuild re-seats them).
LANTERNS = [
    # (x, y, z, tag)  — hut eaves, the drying decks, the bridge heads, the landing
    (47.9, 20.2, 12.1, "westweave"), (51.4, 21.6, 11.9, "westweave"),
    (56.6, 21.3, 10.9, "pilot"), (60.6, 23.2, 10.9, "pilot"), (62.6, 24.6, 10.6, "pilot"),
    # pulled off the gorge lip (y 25.6/25.4 -> 24.4/23.6): each of these hung
    # within 6 m of one of Locksfoot's own moorage lanterns, and a lantern set ON
    # a frontage silhouettes it anyway, which is what the drying decks want
    (64.6, 24.4, 8.3, "drying"), (67.4, 24.0, 9.6, "huts"), (71.6, 23.6, 9.6, "huts"),
    # TWO lanterns on the 20 m bridge, not three, and both hugging the cliff side
    # (y 22.2, not 23.2): finding 98 says the run nearest the lens is the one that
    # ruins the shot, and the bridge is in frame from Locksfoot, the Waterfront
    # and the Lockhead.  Pulled inboard they also stop hanging directly over the
    # accepted boardwalk.
    (76.0, 22.2, 9.0, "bridge"), (86.0, 22.2, 8.8, "bridge"),
    (93.2, 24.3, 8.7, "cottage"),
    (102.9, 26.0, 0.9, "landing"), (108.2, 28.1, 0.9, "landing"),
]
LAMP_W, LAMP_CUT = 680.0, 14.0
for i, (x, y, z, tag) in enumerate(LANTERNS):
    d = bpy.data.lights.new("KEYW_lantern_%d_%s" % (i, tag), 'POINT')
    d.energy = LAMP_W
    d.color = (1.0, 0.72, 0.42)
    d.shadow_soft_size = 0.06
    d.use_custom_distance = True
    d.cutoff_distance = LAMP_CUT
    ob = bpy.data.objects.new(d.name, d)
    ob.location = Vector((x, y, z))
    link(ob, COLL)
log("LIGHT", "KEYW_lantern_* x%d" % len(LANTERNS),
    "%.0f W ordinary lanterns at a %.0f m cutoff — the town's one lantern bulb "
    "(Boatyard/Waterfront/Locksfoot all use it).  Heartlights are rare and magical "
    "and there are none in the Weave." % (LAMP_W, LAMP_CUT))

# Practical spill has to be measured against the accepted district's OWN
# practicals, not against KEY_slip's peak (finding 100).  Measured the wrong way
# the two Westweave lanterns read as 132% of the shared key — which is true and
# meaningless: the Waterfront's `wf_lantern_walk_1` stands 2.4 m from the same
# point and delivers 9.4 W/m2 there, because that is what a 680 W point does at
# 2.4 m.  The number that means something is the RATIO to the lamp the accepted
# frame was actually judged under.
# ...and it has to be RAY-TRACED, which no previous district needed.  Every other
# pass is a single deck under an open sky, so line-of-sight and reality agree.
# The Weave is a stilt forest standing between two accepted boardwalks and its own
# lanterns: 8-11 m of decking, joists, piles and hut walls lie on nearly every one
# of those sight lines, and OCCLUSION IS THE DESIGN.  Measured as free space, the
# drying-decks lantern reads 19% of Locksfoot's moorage lamp; traced, the
# `walk_lm_drying-decks` deck is squarely in the way and the honest answer is 0.
# (Finding 103 in a different key: cast the ray, don't reason about it.)
DG = bpy.context.evaluated_depsgraph_get()
SC = bpy.context.scene


SKIN = 0.35        # clear the lamp's own housing at BOTH ends of the ray


def clear_los(A, B):
    """True if nothing solid stands between two points.

    The ray starts and stops SKIN metres inside each end.  Without that, the
    first version traced a district's own lantern down to the point 2 m beneath
    it, hit that lantern's own hood, scored the denominator 0.0 and reported the
    Weave as adding 34 000 000 000% — a self-occlusion artefact, not a result.
    """
    d = B - A
    r = d.length
    if r < 2 * SKIN + 0.05:
        return True
    u = d.normalized()
    hit = SC.ray_cast(DG, A + u * SKIN, u, distance=r - 2 * SKIN)[0]
    return not hit


def practical_at(P, want, trace=True):
    t = 0.0
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.data.type != 'POINT' or not want(o.name):
            continue
        L = Vector(o.location)
        r = (L - P).length
        if o.data.use_custom_distance and r >= o.data.cutoff_distance:
            continue
        if trace and not clear_los(L, P):
            continue
        t += o.data.energy / (4.0 * math.pi * max(r, 0.05) ** 2)
    return t


# ...and it has to be measured WHERE that district's practicals actually light
# something (finding 106, applied to lamps instead of cameras).  Measured at the
# SKY solve point (80, 27.3, 0.8) the same rig reads 51%, which is arithmetic
# about a spot Locksfoot's own lanterns barely reach — 2.7 W/m2 — not a statement
# about its art.  The working points are 2 m under each district's own lanterns,
# which is where a barrel, a net or a face is actually seen by one.
def under_lamps(pref):
    out = []
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'POINT' and o.name.startswith(pref):
            out.append(Vector(o.location) - Vector((0, 0, 2.0)))
    return out


for tag, pref, worst in (("Boatyard", "lantern_light_", AIM0),
                         ("Waterfront", "wf_lantern_", AIMWF),
                         ("Locksfoot", "lf_lantern_", AIMLF)):
    pts = under_lamps(pref)
    rat, raw = [], []
    for P in pts:
        # the DENOMINATOR is free-space on purpose: it is what that district's own
        # lamps were solved to put on their own art, and a lamp partly hidden from
        # its own pool of light by a barrel is not the thing being measured here
        base = practical_at(P, lambda n: not n.startswith("KEYW_"), trace=False)
        mineP = lambda n: n.startswith("KEYW_lantern_")
        rat.append(practical_at(P, mineP) / max(base, 1e-9))
        raw.append(practical_at(P, mineP, trace=False) / max(base, 1e-9))
    log("CHECK", "practicals added at the accepted %s" % tag,
        "under its own %d lanterns, TRACED: %.2f%% mean / %.2f%% worst of what "
        "they deliver there  (free-space, ignoring the decks in between: "
        "%.1f%% / %.1f%%)"
        % (len(pts), 100 * sum(rat) / max(len(rat), 1), 100 * max(rat),
           100 * sum(raw) / max(len(raw), 1), 100 * max(raw)))
    assert max(rat) < 0.12, \
        "weave practicals out-light the accepted %s's own lanterns" % tag

# ===========================================================================
# 5. INVENTORY — count the file, never the log (finding 117)
# ===========================================================================
print("\n--- 5. inventory of the SAVED state ----------------------------------")
from collections import Counter
c = Counter()
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.startswith("KEYW_"):
        c[o.name.rsplit("_", 1)[0] if o.name[-1].isdigit() else o.name] = c.get(
            o.name.rsplit("_", 1)[0] if o.name[-1].isdigit() else o.name, 0)
groups = Counter()
for o in bpy.data.objects:
    if o.type == 'LIGHT' and o.name.startswith("KEYW_"):
        for g in ("KEYW_gorge_weave", "KEYW_CLIFF_", "KEYW_SOFFIT_", "KEYW_lantern_"):
            if o.name.startswith(g):
                groups[g] += 1
for g in sorted(groups):
    print("    %-24s %3d" % (g + "*", groups[g]))
print("    %-24s %3d" % ("KEYW_ TOTAL", sum(groups.values())))
print("    %-24s %3d" % ("town lights TOTAL", sum(1 for o in bpy.data.objects if o.type == 'LIGHT')))
orph = [d.name for d in bpy.data.lights if d.users == 0]
print("    orphaned light datablocks: %d %s" % (len(orph), orph[:6]))
assert not orph, "orphaned light datablocks — the finding-117 drift is starting"
assert sum(groups.values()) == len(AIMS) + len(CLIFF_AT) + len(SOFFIT_AT) + len(LANTERNS), \
    "the saved file does not carry what this script says it made"

print("\n" + "=" * 78)
print("WEAVE LIGHT RIG: %d KEYW_ lamps" % sum(groups.values()))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
