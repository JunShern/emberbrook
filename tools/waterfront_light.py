"""waterfront_light.py — TASK 0 of the Waterfront district pass.

  Blender -b tools/blends/dellhollow-master.blend -P tools/waterfront_light.py
  (add `save` as the last argv token to write the blend back)

Two jobs, both left over from the 3x river widening:

1. THE WIDENED GORGE HAS NO KEY OUTSIDE THE BOATYARD.
   `KEY_slip` is a 48 deg spot standing 28.6 m off its aim point in the yard.
   Its cone is 12.7 m across at that distance, so everything past y~42 (two
   thirds of the extended Lock Four dam) and everything east of x~33 (the whole
   Waterfront) is lit by the 5 W sun and the sky wash alone and renders as a
   black silhouette.  Widening the one spot is wrong — a 100 m cone has no
   modelling left in it.  Instead the key is REPLICATED along the gorge:

     * every clone carries KEY_slip's own light datablock values (colour, cone,
       blend, soft size), so the quality of the light is identical;
     * every clone stands at exactly KEY_slip's 28.6 m standoff along exactly
       KEY_slip's direction vector, so the shadows stay parallel to the accepted
       ones and fall the same way;
     * the per-clone wattage is SOLVED, not guessed: the chain's summed
       irradiance along its aim line is matched to KEY_slip's own peak
       irradiance at its aim point (manifest finding 53 / 58 — the value gap is
       what reads as two datasets), and the chain's spill into the accepted
       Boatyard is measured and reported.

   The sky wash and the cool river bounce are extended the same way: SKY_wash
   grows across the gorge with its power scaled by the area so its RADIANCE is
   unchanged, and the small bounce cards are replicated rather than enlarged so
   the yard's own bounce is untouched.

2. THE FAR RIM IS A STRAIGHT-TOPPED BOX WITH BLOCKS FLOATING AT ITS FOOT.
   The widening left `cliff_far` an 8-vertex slab (dead-straight skyline,
   manifest finding 7) and moved `farwallcrown_*` 26 m north in Y ONLY — they
   were sitting on the OLD 17 m wall top, so they now hang at z~15 against the
   foot of a 58 m wall: blocky silhouettes attached to nothing.  Here the wall
   is rebuilt with a modulated crest and a shelf, and the crowns are re-seated
   ON that crest as broad canopy masses (finding 15: distant vegetation is
   MASS), clustered into groves so the skyline is broken rather than dotted.
   `farcrown_*` — the upstream ridge crowns that read as separate blocks on the
   hero skyline — are re-seated onto their own ridge crest the same way.
"""
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import new_mesh, link, coll, M, world_bbox, box

SAVE = "save" in sys.argv
LOG = []


def log(kind, what, why=""):
    LOG.append((kind, what, why))
    print("  %-9s %-34s %s" % (kind, what, why))


# ===========================================================================
# 1. THE KEY CHAIN
# ===========================================================================
KEY = bpy.data.objects["KEY_slip"]
KD = KEY.data
# KEY_slip's own light direction and standoff
DIR = (KEY.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
AIM0 = Vector((20.5, 29.83, 1.0))                 # where KEY_slip actually lands
STANDOFF = (Vector(KEY.location) - AIM0).length


def irr(E, lamp_pos, P, direction=DIR, size=None, blend=None):
    """Irradiance (W/m^2) a Blender spot delivers to a point facing it."""
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

# ---- the aim lines the chain has to cover ---------------------------------
# `cone` is the knob that keeps a chain OUT of its neighbour.  A spot aimed down
# the gorge keeps opening: KEY_slip's own 48 deg cone, replicated 19 m east of
# the yard, is still 20 m across by the time it reaches the yard and put 20% of
# KEY_slip's own key back onto accepted art.  Below ~26 deg the yard falls
# outside the cone entirely, so the Waterfront chain is narrow-and-many while the
# dam chain — which fires ACROSS the gorge, not along it — keeps the 48 deg cone.
CHAINS = {
    # the Waterfront boardwalk, from the yard's east edge out past the fish dock
    "wf_deck": dict(cone=24.0, level=0.60, aims=[Vector((x, 27.0, 1.4))
                                     for x in (34.0, 38.0, 42.0, 46.0, 50.0,
                                               54.0, 58.0, 62.0)]),
    # ... and the cliff face it hugs, which is 5 m higher and 5 m back
    "wf_cliff": dict(cone=24.0, level=0.34, aims=[Vector((x, 21.5, 5.0))
                                      for x in (37.0, 41.0, 45.0, 49.0, 53.0, 57.0)]),
    # the extended Lock Four dam: KEY_slip dies at y~42, the dam runs to y=87
    "dam": dict(cone=48.0, level=0.80, aims=[Vector((13.0, y, 3.2))
                                 for y in (45.0, 51.5, 58.0, 64.5, 71.0,
                                           77.5, 84.0)]),
}

for o in list(bpy.data.objects):
    if o.type == 'LIGHT' and o.name.startswith("KEY_gorge_"):
        bpy.data.objects.remove(o, do_unlink=True)

made = []
for tag, spec in CHAINS.items():
    for i, a in enumerate(spec["aims"]):
        d = KD.copy()
        d.name = "KEY_gorge_%s_%d" % (tag, i)
        d.spot_size = math.radians(spec["cone"])
        # a chain element is not a solo key: KEY_slip's 0.62 blend leaves a
        # flat-topped cone that scallops when eight of them are laid end to end
        # (0.6 stop between the aim points and the gaps).  A fully soft cone
        # cross-fades into its neighbours — same cutoff angle, so the same zero
        # spill into the yard, but 11% ripple instead of 33%.
        d.spot_blend = 1.0
        # a chain element only has to reach its own patch.  A custom cutoff is
        # both a hard guarantee that it cannot reach the neighbouring district
        # and what keeps EEVEE's 2048-tilemap shadow budget from overflowing
        # (an overflow silently DROPS shadows, and it made EEVEE's own frame
        # brightness non-repeatable between runs — useless for measuring).
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


def chain_range(tag, E=None, interior=True):
    """min/max irradiance along the aim line.  The ends of a chain taper by
    design (there is no next lamp), so uniformity is judged on the INTERIOR —
    the span between the first and last lamp's own aim points."""
    aims = CHAINS[tag]["aims"]
    n = len(aims) - 1
    lo_f, hi_f = (0.6, n - 0.6) if (interior and n >= 2) else (0.0, float(n))
    vals = []
    for k in range(81):
        f = lo_f + (hi_f - lo_f) * k / 80.0
        i = min(int(f), n - 1)
        vals.append(chain_at(tag, aims[i].lerp(aims[i + 1], f - i), E))
    return min(vals), max(vals)


print("=" * 78)
print("WATERFRONT LIGHT RIG")
print("=" * 78)
print("\n--- 1. key chain -----------------------------------------------------")
print("  KEY_slip: %.0f W, cone %.0f deg, blend %.2f, standoff %.2f m -> peak %.4f W/m2"
      % (KD.energy, math.degrees(KD.spot_size), KD.spot_blend, STANDOFF, PEAK))
for tag, spec in CHAINS.items():
    # KEY_slip's PEAK lands on one spot in the yard; the yard's mean is well
    # under it.  A chain that holds the peak all the way along a 28 m boardwalk
    # therefore renders the new district paler than the accepted one even though
    # the numbers "match" — so each chain carries a level against that peak.
    E = spec["level"] * KD.energy * PEAK / max(chain_range(tag, KD.energy)[1], 1e-9)
    for t, ob, a in made:
        if t == tag:
            ob.data.energy = round(E, 1)
    lo, hi = chain_range(tag)
    aims = spec["aims"]
    log("KEY", "%s: %d spots, %.0f deg, %.0f W" % (tag, len(aims), spec["cone"], E),
        "aim %.0f,%.0f -> %.0f,%.0f | irradiance %.3f..%.3f W/m2 (ripple %.0f%%), "
        "%.0f%% of KEY_slip's peak %.3f" % (aims[0].x, aims[0].y, aims[-1].x, aims[-1].y,
                                          lo, hi, 100 * (hi - lo) / hi,
                                          100 * spec["level"], PEAK))

spill = sum(irr(ob.data.energy, Vector(ob.location), AIM0, size=ob.data.spot_size,
                blend=ob.data.spot_blend) for t, ob, a in made)
log("CHECK", "spill into the accepted Boatyard",
    "%.4f W/m2 = %.1f%% of KEY_slip's own %.4f" % (spill, 100 * spill / PEAK, PEAK))
assert spill < 0.05 * PEAK, "the chain re-values the accepted yard (%.1f%%)" % (100 * spill / PEAK)

# ===========================================================================
# 2. SKY WASH + BOUNCE CARDS
# ===========================================================================
print("\n--- 2. fill ----------------------------------------------------------")
sw = bpy.data.objects["SKY_wash"]
d = sw.data
# The accepted post-river-widening state, restated so this pass is idempotent.
BASE = dict(size=90.0, size_y=34.0, energy=489.1, x=24.0)
WANT_Y, WANT_X = 80.0, 30.0        # local Y == world X for this lamp (yaw 90)


def area_irr(size_x, size_y, loc, rot, E, P, npn=Vector((0, 0, 1)), n=13):
    """Irradiance a rectangular Blender area lamp delivers to a point.

    Scaling an area lamp's POWER BY ITS AREA preserves RADIANCE, not irradiance:
    the enlarged source also subtends more solid angle, so the receiver gets
    more light.  Measured on the accepted Boatyard, the by-area rule put the
    yard 18% up.  So the wattage is solved by integrating the emitter instead.
    """
    R = rot.to_matrix()
    ex, ey, ez = R.col[0], R.col[1], -R.col[2]      # lamp faces its -Z
    A = size_x * size_y
    L = E / (math.pi * A)                            # radiance
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


rot = sw.rotation_euler
loc_old = Vector((BASE["x"], sw.location.y, sw.location.z))
I_want = area_irr(BASE["size"], BASE["size_y"], loc_old, rot, BASE["energy"], AIM0)
loc_new = Vector((WANT_X, sw.location.y, sw.location.z))
I_unit = area_irr(BASE["size"], WANT_Y, loc_new, rot, 1.0, AIM0)
E_new = round(I_want / max(I_unit, 1e-12), 1)
d.size, d.size_y, d.energy = BASE["size"], WANT_Y, E_new
sw.location.x = WANT_X
log("LIGHT", "SKY_wash", "across-gorge %.0f -> %.0f m (world x %.0f..%.0f), energy %.0f -> "
    "%.0f — solved so the ACCEPTED yard keeps %.4f W/m2 (by-area scaling would have "
    "given %.0f W and +%.0f%%)"
    % (BASE["size_y"], WANT_Y, WANT_X - WANT_Y / 2, WANT_X + WANT_Y / 2, BASE["energy"],
       E_new, I_want, BASE["energy"] * WANT_Y / BASE["size_y"],
       100 * (BASE["energy"] * WANT_Y / BASE["size_y"] / max(E_new, 1e-9) - 1)))

# Small cards are REPLICATED, never enlarged — enlarging one changes the yard.
# They are also HALVED: a card keeps its RADIANCE when its power falls with its
# area, and a half-size card at half the standoff delivers the same bounce to the
# thing in front of it while reaching a quarter as far.  That is what keeps a
# waterfront bounce card out of the accepted Boatyard 20 m away.
def replicate(src_name, prefix, spots, shrink=2.0):
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT' and o.name.startswith(prefix):
            bpy.data.objects.remove(o, do_unlink=True)
    src = bpy.data.objects[src_name]
    for i, p in enumerate(spots):
        d = src.data.copy()
        d.size /= shrink
        d.size_y /= shrink
        d.energy /= shrink * shrink
        # a faked bounce card should not also cast: it buys nothing and it is
        # the cheapest place to give the shadow budget back.
        d.use_shadow = False
        d.use_custom_distance = True
        d.cutoff_distance = 26.0
        ob = bpy.data.objects.new("%s%d" % (prefix, i), d)
        d.name = ob.name
        ob.location = Vector(p)
        ob.rotation_euler = src.rotation_euler
        link(ob, "DIST_boatyard")
    log("LIGHT", "%s x%d" % (prefix, len(spots)),
        "%s at 1/%.0f size and 1/%.0f power — identical radiance, local reach"
        % (src_name, shrink, shrink * shrink))


FILL_AT = [(42.0, 34.5, 3.4), (51.0, 35.5, 3.4), (60.0, 36.5, 3.4),
           (23.0, 54.0, 3.4), (22.0, 66.0, 3.4), (21.0, 78.0, 3.4)]
CLIFF_AT = [(44.0, 23.2, 6.4), (51.0, 23.6, 6.4), (58.0, 24.0, 6.4), (64.0, 24.4, 6.0)]
replicate("FILL_bounce", "FILL_bounce_wf_", FILL_AT)
replicate("CLIFF_BOUNCE", "CLIFF_BOUNCE_wf_", CLIFF_AT)

# the cards must not lift the accepted yard either: measure what each new card
# actually delivers to the Boatyard reference point against what the yard's own
# cards deliver there (finding 41 — measure the ROI, do not eyeball the note).
def card_irr(src_name, positions):
    src = bpy.data.objects[src_name]
    d = src.data
    sy = d.size_y if d.shape == 'RECTANGLE' else d.size
    own = area_irr(d.size, sy, Vector(src.location), src.rotation_euler, d.energy, AIM0)
    add = sum(area_irr(d.size / 2.0, sy / 2.0, Vector(p), src.rotation_euler,
                       d.energy / 4.0, AIM0) for p in positions)
    return own, add


tot_own = tot_add = 0.0
for nm, pos in (("FILL_bounce", FILL_AT), ("CLIFF_BOUNCE", CLIFF_AT)):
    own, add = card_irr(nm, pos)
    tot_own += own
    tot_add += add
    log("CHECK", "%s copies" % nm, "add %.5f W/m2 at the yard vs the original's own "
        "%.5f (%.1f%%)" % (add, own, 100 * add / max(own, 1e-12)))
sky_here = area_irr(BASE["size"], WANT_Y, loc_new, rot, E_new, AIM0)
log("CHECK", "total added fill at the yard",
    "%.5f W/m2 = %.1f%% of the yard's existing fill (%.5f incl. sky wash)"
    % (tot_add, 100 * tot_add / max(tot_own + sky_here, 1e-12), tot_own + sky_here))
assert tot_add < 0.09 * (tot_own + sky_here), "the new bounce cards re-value the yard"

# ===========================================================================
# 3. THE FAR RIM
# ===========================================================================
print("\n--- 3. far rim -------------------------------------------------------")
rng = random.Random(20260730)
MROCKF = M("mat_rock_farwall")

# ---- 3a. a wall with a crest instead of a straight edge --------------------
X0, X1 = -60.0, 150.0
YF, YB = 84.0, 99.0
BASE = -10.0


def crest(x):
    """Far-wall crest height: three octaves, so the skyline never repeats."""
    return (57.0
            + 5.6 * math.sin(x * 0.031 + 0.7)
            + 3.1 * math.sin(x * 0.084 - 1.9)
            + 1.7 * math.sin(x * 0.191 + 2.6))


def shelf(x):
    """A mid-height break so the wall is not one unmodulated plane."""
    return 22.0 + 3.4 * math.sin(x * 0.047 + 2.2) + 1.6 * math.sin(x * 0.13 - 0.4)


old = bpy.data.objects.get("cliff_far")
if old:
    coll_names = [c.name for c in old.users_collection]
    bpy.data.objects.remove(old, do_unlink=True)
else:
    coll_names = ["CONTEXT"]
NX = 108
V, F = [], []
row = {}
for i in range(NX + 1):
    x = X0 + (X1 - X0) * i / NX
    cz = crest(x)
    sz = shelf(x)
    # y wobble on the face so the wall is not a plane
    fy = YF + 1.5 * math.sin(x * 0.061 + 1.1) + 0.7 * math.sin(x * 0.17)
    col = []
    for j, (y, z) in enumerate(((fy, BASE), (fy - 0.9, sz), (fy + 1.1, sz + 5.5),
                                (fy + 0.4, cz), (YB, cz - 2.0), (YB, BASE))):
        col.append(len(V))
        V.append((x, y, z))
    row[i] = col
for i in range(NX):
    for j in range(5):
        F.append((row[i][j], row[i + 1][j], row[i + 1][j + 1], row[i][j + 1]))
cf = new_mesh("cliff_far", V, F, MROCKF, coll_names[0])
b = world_bbox(cf)
log("REBUILD", "cliff_far", "8-vert slab -> %d-vert wall, crest z %.0f..%.0f (was a dead-flat "
    "z=58 skyline), mid shelf, y face wobble" % (len(V), min(crest(x) for x in (X0, 0, X1)),
                                                 max(crest(x) for x in (X0, 60, X1))))

# ---- 3b. the crowns go ON the crest, as groves -----------------------------
def reseat(prefix, height_fn, y_fn, grove_span, scale_lo, scale_hi, note):
    obs = sorted([o for o in bpy.data.objects if o.name.startswith(prefix)],
                 key=lambda o: o.name)
    if not obs:
        return
    n = len(obs)
    groves = max(2, n // 4)
    centres = [X0 + (X1 - X0) * (k + 0.5) / groves for k in range(groves)]
    for i, o in enumerate(obs):
        if o.get("wf_reseat"):
            continue
        o["wf_reseat"] = 1
        gx = centres[i % groves] + (rng.random() - 0.5) * grove_span
        b = world_bbox(o)
        cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
        cz = (b[4] + b[5]) / 2
        s = scale_lo + rng.random() * (scale_hi - scale_lo)
        # scale about the mesh's own centre, then set the centre on the crest
        me = o.data
        for v in me.vertices:
            p = o.matrix_basis @ v.co
            q = Vector((cx + (p.x - cx) * s, cy + (p.y - cy) * s, cz + (p.z - cz) * s * 0.72))
            v.co = o.matrix_basis.inverted() @ q
        b = world_bbox(o)
        cx, cy = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2
        tz = height_fn(gx) + (b[5] - b[4]) * 0.22
        ty = y_fn(gx) + (rng.random() - 0.5) * 3.0
        o.location = o.location + Vector((gx - cx, ty - cy, tz - (b[4] + b[5]) / 2))
    log("RESEAT", "%s x%d" % (prefix, n), note)


reseat("farwallcrown_", lambda x: crest(x), lambda x: YF + 2.2, 26.0, 2.3, 3.8,
       "hanging at the FOOT of the 58 m wall -> planted on its crest in %d groves, "
       "canopy mass 2.3-3.8x (finding 15: distant vegetation is mass)" % 4)

# the upstream ridge crowns: same disease, own ridge
RID = bpy.data.objects.get("fx_ridge_upstream")
RIDM = bpy.data.objects.get("fx_ridge_upstream_mid")
rb = world_bbox(RID) if RID else (0, 0, 0, 0, 0, 20)
rbm = world_bbox(RIDM) if RIDM else rb


def ridge_top(x):
    return (rb[5] if x < (rb[0] + rb[1]) / 2 else rbm[5]) - 1.2


def ridge_y(x):
    return 30.0 + 26.0 * rng.random()


obs = sorted([o for o in bpy.data.objects if o.name.startswith("farcrown_")],
             key=lambda o: o.name)
for i, o in enumerate(obs):
    if o.get("wf_reseat"):
        continue
    o["wf_reseat"] = 1
    src = rb if i % 2 == 0 else rbm
    b = world_bbox(o)
    cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
    s = 1.05 + rng.random() * 0.35
    for v in o.data.vertices:
        p = o.matrix_basis @ v.co
        q = Vector((cx + (p.x - cx) * s, cy + (p.y - cy) * s, cz + (p.z - cz) * s * 0.7))
        v.co = o.matrix_basis.inverted() @ q
    b = world_bbox(o)
    cx, cy, cz = (b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2
    # cluster along the ridge it belongs to and sit ON its top edge
    gx = src[0] + (src[1] - src[0]) * ((i * 0.37) % 1.0)
    gy = 18.0 + 52.0 * ((i * 0.61) % 1.0)
    gz = src[5] - 0.8 + (rng.random() - 0.5) * 1.6
    o.location = o.location + Vector((gx - cx, gy - cy, gz + (b[5] - b[4]) * 0.20 - cz))
# ---- 3c. the far-town silhouette is a row of blocks standing in mid-air -----
# `fx_far_town_silhouette` is 36 rooftop blocks whose bottoms are all cut at
# z=7.0, hanging 8 m above the valley floor with sky under them.  Widened 1.6x
# by the river pass, the gaps between them opened up and one broad block over
# two narrow ones reads from the town as a giant table and chairs on the ridge.
# A distant town is a MASS with a varied roofline, so the blocks are carried
# down to a common base and a continuous base band is put under the whole run.
sil = bpy.data.objects.get("fx_far_town_silhouette")
if sil and not sil.get("wf_grounded"):
    sil["wf_grounded"] = 1
    Minv = sil.matrix_basis.inverted()
    zs = [(sil.matrix_basis @ v.co).z for v in sil.data.vertices]
    cut = min(zs) + 0.35
    BASE_Z = -2.0
    for v in sil.data.vertices:
        p = sil.matrix_basis @ v.co
        if p.z < cut:
            v.co = Minv @ Vector((p.x, p.y, BASE_Z))
    b = world_bbox(sil)
    band = box("fx_far_town_base", b[0] + 0.25, b[1] - 0.25, b[2], b[3], BASE_Z,
               min(zs) + 1.6, sil.data.materials[0] if sil.data.materials else None,
               [c.name for c in sil.users_collection][0])
    log("EDIT", "fx_far_town_silhouette", "36 rooftop blocks were cut off at z=7.0 and hung "
        "in the sky (a broad one over two narrow ones read as a giant table on the ridge); "
        "carried down to z=%.0f and given a continuous base band" % BASE_Z)

log("RESEAT", "farcrown_ x%d" % len(obs),
    "floating blobs below the ridge line -> seated on the upstream ridge crests "
    "(z %.0f / %.0f), canopy 1.05-1.4x, strung along the whole ridge" % (rb[5], rbm[5]))

print("\n" + "=" * 78)
print("LIGHT RIG: %d changes" % len(LOG))
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("saved", bpy.data.filepath)
