"""waterfront_landings.py — THE LANDINGS THE FOOTPRINT RULING OWES, and the reason it owes them.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/waterfront_landings.py -- measure
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/waterfront_landings.py -- build save

WHY.  The stilt-waterfront ruling replaced four `area` landmarks' extent-discs with measured
`footprint` rect-lists, and that removed 93.5 m2 of pad that was standing on the river.  It
also removed the one thing the discs were doing that nothing else did: COVERING THE POINT THE
RIBBONS CONVERGE ON.  `town_blockout.py` draws every edge's ribbon to the landmark's own
`pos`, and in all four cases `pos` is NOT inside the landmark's built landing — it is in the
water gap between two wharves (fish-dock, north-landing), off the deck's south edge
(drying-decks), or 4.3 m short of the staging (moorage).  Measured on the shipped bundle with
a connected-component sweep over walk_bodygate's own step rule: before the stamp all four pads
sat in the big component; after it, `walk_lm_fish-dock`, `walk_lm_north-landing` and
`walk_lm_drying-decks` were islands of their own and `walk_lm_moorage` kept only its 3.0 m2
west-store rect.  A landing you cannot reach is a worse defect than one you can stand on the
river at, so this is not optional dressing.

WHAT IT BUILDS.  One CONNECTIVE LANDING per landmark: a plank deck on joists and piles, in the
same vocabulary `locksfoot_build.staging()` uses (boatyard_lib.plank_fill + beam + cyl), that
carries the landmark's own position onto its own footprint.  Pier, not plaza — 2.0 m wide,
which is `town_blockout`'s own stair-landing pad size and wider than its 1.6 m deck ribbon,
so the landing is exactly as wide as the walkway it has to carry and no wider.

EVERY NUMBER IS DERIVED, NOT TYPED:
  * the rect comes from the map — 2.0 m about `pos`, run along the axis that separates `pos`
    from the footprint rects whose x-range it overlaps, ending at their near edges;
  * the deck's height comes from the deck it continues (the mean top of whatever is already
    built under the landmark's stamped rects), so the new planking lands flush with the old;
  * the deck's MATERIAL is read off that same neighbour, so a fish-dock landing is made of
    the fish dock;
  * only the part of the rect that is NOT already decked is built, found by a 0.05 m scan
    along the run and butted to the first decked row on each side.  Nothing is planked twice.

IDEMPOTENT: every object it makes is `wfd_*` and every run deletes the previous `wfd_*` first.
`measure` changes nothing and prints the same numbers `build` would act on.
"""
import bpy, json, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, join_meshes, beam, cyl, link, coll, M,
                          plank_fill, stable_hash)

MAP = json.load(open(REPO + "/public/townmap/dellhollow.map.json"))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PHASE = "build" if "build" in argv else "measure"
SAVE = "save" in argv
COLL = "DIST_wfdeck"
MASTER = REPO + "/tools/blends/dellhollow-master.blend"

PAD_W = 2.0                 # town_blockout's own landing-pad size; its deck ribbon is 1.6
SCAN = 0.05                 # along-run resolution for the butt joint
SKIP = ("water_", "riverbed", "fx_", "walk_", "bar_", "wfd_")
sc = bpy.context.scene


def dg():
    return bpy.context.evaluated_depsgraph_get()


def log(kind, what, why=""):
    print("  %-9s %-30s %s" % (kind, what, why))


PASS_THROUGH = ("walk_", "bar_", "fx_", "cam", "CAM", "REF_", "KEY", "lm_")
WATER = ("water", "riverbed")


def solid_below(x, y, z, depth=40.0):
    """First render-visible non-water hit below z: (height, object) or None.

    walk_water_audit's rule and landing_footprint's rule, third instance — the three
    instruments have to agree about what counts as built or the footprint measured by one
    cannot be decked by the other.  AND AGREEING MEANS PASSING THROUGH the classes a player
    cannot see: `scene.ray_cast` returns the nearest hit whatever it is, so a ray that stops
    on the walk ribbon crossing a gap and then rejects it by name reports bare water over a
    real deck.  landing_footprint carried the same bug and it cost four correctly-built
    landings their verification; the fix belongs in every copy of the rule, not one.
    """
    left = depth
    for _ in range(24):
        hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg(), Vector((x, y, z)), Vector((0, 0, -1)),
                                                 distance=left)
        if not hit or ob is None:
            return None
        if ob.name.startswith(PASS_THROUGH) or ob.hide_render:
            left -= (z - loc.z) + 1e-4
            z = loc.z - 1e-4
            if left <= 0:
                return None
            continue
        if ob.name.startswith(WATER):
            return None
        return loc.z, ob
    return None


# A LANDING WHOSE AIRSPACE IS ALREADY SPOKEN FOR, with the measurement that moved it.
# The generic rule puts the landing 2.0 m about `pos`, and for three of the four that is
# also where a ribbon arrives with clear air over it.  Not at the drying decks: `pos` is
# (65.27, 26.0) on the deck's south edge, and the Weave hangs `t2c_W1_laundry_deckA`
# (z 7.02..8.57 along y 25.92..26.07) and `t2c_WV2_dryingdeck_awning` (canopy to z 7.90)
# directly over it — a body standing on a 6.915 m pad occupies 7.57..8.21, so walk_bodygate
# measured 3445 + 1733 blocked steps there and the south approach is not a way in at any
# width.  The east end is: `walk_e_weave-huts__drying-decks_l0` arrives at x 67.29..70.91
# and nothing hangs over x > 67.60.  So this landing goes where the walker can actually
# stand, and the airspace finding is recorded rather than built into.
OVERRIDES = {
    "drying-decks": [67.20, 68.77, 26.25, 26.70],
}


def connective_rect(lm):
    """The rect that carries `pos` onto the footprint. See the module docstring."""
    if lm["id"] in OVERRIDES:
        return list(OVERRIDES[lm["id"]]), [r for r in lm["footprint"]]
    px, py = lm["pos"][0], lm["pos"][1]
    x0, x1 = px - PAD_W / 2, px + PAD_W / 2
    ys = [py]
    used = []
    for r in lm["footprint"]:
        if r[1] < x0 or r[0] > x1:          # not in this landing's own column
            continue
        used.append(r)
        if r[3] < py:
            ys.append(r[3])
        elif r[2] > py:
            ys.append(r[2])
        else:
            ys += [r[2], r[3]]
    return [round(x0, 2), round(x1, 2), round(min(ys), 2), round(max(ys), 2)], used


def neighbour_deck(lm):
    """Mean top height and material of what is already built under the stamped rects."""
    top = lm["pos"][2] + 0.245
    zs, mats = [], {}
    for r in lm["footprint"]:
        nx = max(2, int((r[1] - r[0]) / 0.2))
        ny = max(2, int((r[3] - r[2]) / 0.2))
        for j in range(ny + 1):
            for i in range(nx + 1):
                x = r[0] + (r[1] - r[0]) * i / nx
                y = r[2] + (r[3] - r[2]) * j / ny
                s = solid_below(x, y, top - 0.06)
                if s and (top - s[0]) <= 0.60:
                    zs.append(s[0])
                    mn = s[1].data.materials[0].name if s[1].data.materials else None
                    if mn:
                        mats[mn] = mats.get(mn, 0) + 1
    if not zs:
        return None, None
    best = max(mats.items(), key=lambda kv: kv[1])[0] if mats else "mat_deck"
    return sum(zs) / len(zs), best


def walk_floor_over(rect, lid, z_hint):
    """The LOWEST walk surface standing over `rect` — the ceiling this landing must fit under.

    A connective landing is built where ribbons already cross, and those ribbons are at their
    own heights: the fish dock's cross the gap at z 0.93..1.07 while the wharf either side
    decks at 1.09.  Planking at the neighbour's height would therefore stand ABOVE the walk
    record it is supposed to support — the ribbon would be buried, master_walk_qa's ray
    coverage would stop first-hitting a walk mesh, and the audit would call the deck the
    player's support while the player walked inside it.
    A BOUNDING BOX CANNOT ANSWER THIS and was tried first: `walk_e_moorage__lock-five_l0`
    slopes from 1.07 down to 0.53 over 4.6 m and only its high end is over the moorage's
    band, so its bbox zmin would have driven the pier 0.73 m under the pad — out of the
    landed window entirely.  So the polygons are read, and only the ones actually over the
    rect count.
    """
    polys = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith("walk_") or o.name == "walk_lm_" + lid:
            continue
        Mx = o.matrix_world
        N = Mx.to_3x3().inverted().transposed()
        for p in o.data.polygons:
            if (N @ p.normal).normalized().z <= 0.5:
                continue
            ws = [Mx @ o.data.vertices[i].co for i in p.vertices]
            ax0, ax1 = min(w.x for w in ws), max(w.x for w in ws)
            ay0, ay1 = min(w.y for w in ws), max(w.y for w in ws)
            if ax1 < rect[0] or ax0 > rect[1] or ay1 < rect[2] or ay0 > rect[3]:
                continue
            z = min(w.z for w in ws)
            if abs(z - z_hint) > 3.0:            # a different tier passing overhead
                continue
            polys.append((z, ax0, ax1, o.name))
    if not polys:
        return None, polys
    lo = min(polys)
    return (lo[0], lo[3]), polys


def walk_in_column(x, y, z0, z1, lid, r=0.42):
    """Does any walk surface pass through the column (x, y) between z0 and z1?

    `r` is play3d's own character radius: a pile does not have to be exactly under a foot
    to be in the way of one.  Returns the offending record's name, or None.
    """
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith("walk_") or o.name == "walk_lm_" + lid:
            continue
        Mx = o.matrix_world
        for p in o.data.polygons:
            ws = [Mx @ o.data.vertices[i].co for i in p.vertices]
            if (max(w.x for w in ws) < x - r or min(w.x for w in ws) > x + r
                    or max(w.y for w in ws) < y - r or min(w.y for w in ws) > y + r):
                continue
            zc = sum(w.z for w in ws) / len(ws)
            if z0 - 0.10 <= zc <= z1 - 0.10:
                return o.name
    return None


def rail_gap(rect, deck_z, lid):
    """Open the landing's own way on: delete rail faces standing across it.

    A landing you cannot step onto is not a landing.  The moorage's mooring stage is on the
    river side of `lf_railings`, the boardwalk guard, and walk_bodygate measured 2086 blocked
    steps against it between the new pier and the stage — so the pad reached the network and
    still could not reach the boat it exists for.  The cut is a GAP, not a deletion: only
    faces inside this landing's own rect (grown by a body radius) and inside the 2.05 m
    corridor over its deck, which is a boarding opening at a pier and nothing else.
    ls_reorigin.py cut the loop-stairs rail by the same reasoning and the same care.
    """
    import bmesh
    cut = {}
    r = 0.42
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or not o.name.endswith("_railings"):
            continue
        Mx = o.matrix_world
        doomed = [p.index for p in o.data.polygons
                  if rect[0] - r <= (Mx @ p.center).x <= rect[1] + r
                  and rect[2] - r <= (Mx @ p.center).y <= rect[3] + r
                  and deck_z <= (Mx @ p.center).z <= deck_z + 2.05]
        if not doomed:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in doomed], context='FACES')
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        cut[o.name] = len(doomed)
    return cut


def trim_for_headroom(rect, polys, px, floor_z):
    """Trim the landing's WIDTH to the columns it can actually be built in.

    A ribbon that only clips the landing's corner must not set its height for the whole
    landing: `walk_e_moorage__lock-five_l0` overlaps the moorage pier by 0.14 m of its 2.00 m
    width on the way down to the lock, and honouring it drove the pier to 0.595 m under the
    pad — inside the 0.60 m landed window by 5 mm, which the planking's own +/-0.014 jitter
    would have spent.  So the width is cut to the longest run of 0.10 m columns, containing
    the landmark's own x, in which nothing stands lower than `floor_z`.  A trim is reported;
    it is never silent.
    """
    step = 0.10
    n = max(1, int(round((rect[1] - rect[0]) / step)))
    ok = []
    for i in range(n):
        cx0, cx1 = rect[0] + i * step, rect[0] + (i + 1) * step
        ok.append(not any(z < floor_z and ax1 > cx0 and ax0 < cx1 for z, ax0, ax1, _ in polys))
    k = min(max(int((px - rect[0]) / step), 0), n - 1)
    if not ok[k]:
        return None                      # the landmark's own column is unbuildable
    a = k
    while a > 0 and ok[a - 1]:
        a -= 1
    b = k
    while b < n - 1 and ok[b + 1]:
        b += 1
    return [round(rect[0] + a * step, 2), round(rect[0] + (b + 1) * step, 2), rect[2], rect[3]]


def undecked_band(rect, padtop):
    """The contiguous run of `rect` that is NOT already decked, by the footprint's own rule.

    A row counts as DECKED when every sample across the landing's width is LANDED — a solid
    within 0.60 m under the pad top — which is exactly what `landing_footprint --verify` will
    ask of the stamped rect afterwards.  Measuring "already decked" against anything else is
    how the drying decks' apron came to be built over only 0.3 m2 of its 0.7 m2 rect and then
    verified at 67%: two rules, one rect, and the looser one won.
    Returned butted to the first decked row on each side, so the new planks meet the old.
    """
    x0, x1, y0, y1 = rect
    # THE SAME X SAMPLES `landing_footprint --verify` WILL USE — its 0.2 m grid anchored on
    # the rect's own corner.  Seven evenly-spaced probes is a different sample set, and at
    # the drying decks it declared a row decked that the verifier then failed.
    nxs = max(1, int(round((x1 - x0) / 0.2)))
    xs = [min(x0 + k * 0.2, x1) for k in range(nxs + 1)]
    rows = []
    y = y0
    while y <= y1 + 1e-9:
        n = 0
        for x in xs:
            s = solid_below(x, y, padtop - 0.06)
            if s and (padtop - s[0]) <= 0.60:
                n += 1
        rows.append((round(y, 3), n == len(xs)))
        y += SCAN
    open_rows = [r[0] for r in rows if not r[1]]
    if not open_rows:
        return None, rows
    return (min(open_rows), max(open_rows)), rows


# =========================================================================== run
print("=" * 92)
print("WATERFRONT LANDINGS — %s" % PHASE)
print("=" * 92)

if PHASE == "build":
    gone = [o for o in bpy.data.objects if o.name.startswith("wfd_")]
    for o in gone:
        bpy.data.objects.remove(o, do_unlink=True)
    if gone:
        log("CLEAN", "wfd_*", "%d object(s) from a previous run removed" % len(gone))

made, report = [], {}
for lm in MAP["landmarks"]:
    if lm.get("class") != "area" or not lm.get("footprint"):
        continue
    lid = lm["id"]
    rect, used = connective_rect(lm)
    deck_z, mat_name = neighbour_deck(lm)
    if deck_z is None:
        log("SKIP", lid, "nothing is built under its stamped rects — nothing to continue")
        continue
    padtop = lm["pos"][2] + 0.245
    deck_raw = deck_z
    # A landing may sit no more than LANDED_MARGIN under the pad it carries (the 0.60 m
    # all-landed rule, kept 0.15 m clear of its edge so plank jitter cannot spend it).
    LANDED_MARGIN = 0.45
    ceil, polys = walk_floor_over(rect, lid, deck_z)
    trimmed = None
    if ceil is not None and ceil[0] - 0.02 < padtop - LANDED_MARGIN:
        trimmed = trim_for_headroom(rect, polys, lm["pos"][0], padtop - LANDED_MARGIN + 0.02)
        if trimmed is not None and trimmed != rect:
            rect = trimmed
            ceil, polys = walk_floor_over(rect, lid, deck_z)
    if ceil is not None and ceil[0] - 0.02 < deck_z:
        deck_z = ceil[0] - 0.02
    band, rows = undecked_band(rect, padtop)
    print("\n%s  pos (%.2f, %.2f, %.2f)  pad top %.3f" % (lid, lm["pos"][0], lm["pos"][1],
                                                          lm["pos"][2], padtop))
    print("   connective rect [%.2f..%.2f, %.2f..%.2f]  %.1f x %.1f = %.1f m2  "
          "(bridges %d stamped rect(s))"
          % (rect[0], rect[1], rect[2], rect[3], rect[1] - rect[0], rect[3] - rect[2],
             (rect[1] - rect[0]) * (rect[3] - rect[2]), len(used)))
    if trimmed is not None:
        print("   WIDTH TRIMMED to [%.2f..%.2f] (%.2f m) — a lower walk surface clips the "
              "full-width rect" % (rect[0], rect[1], rect[1] - rect[0]))
    print("   neighbour deck top %.3f, material %s" % (deck_raw, mat_name))
    if ceil is not None:
        print("   lowest walk surface over the rect %.3f (%s) -> deck z %.3f, %.3f under the pad top%s"
              % (ceil[0], ceil[1], deck_z, padtop - deck_z,
                 "  [CAPPED so the ribbon is not buried]" if deck_z < deck_raw else ""))
    if padtop - deck_z > 0.60:
        print("   !! %.3f m under the pad top — OUTSIDE the 0.60 m landed window; this rect "
              "cannot be stamped as a footprint" % (padtop - deck_z))
    if band is None:
        print("   ALREADY DECKED end to end — no planking owed here")
        report[lid] = {"rect": rect, "build": None}
        continue
    by0, by1 = band
    print("   un-decked run y %.2f..%.2f (%.2f m of the %.2f m rect) -> %.1f m2 to build"
          % (by0, by1, by1 - by0, rect[3] - rect[2], (rect[1] - rect[0]) * (by1 - by0)))
    report[lid] = {"rect": rect, "build": [rect[0], rect[1], round(by0, 2), round(by1, 2)],
                   "deckZ": round(deck_z, 3), "mat": mat_name}
    if PHASE != "build":
        continue

    # -------------------------------------------------------------- the landing
    MD = M(mat_name) or M("mat_deck")
    MT = M("mat_timber") or MD
    MWET = M("mat_wet") or MT
    # THE DECK OVERHANGS THE RECT ACROSS THE PLANKS, by half a plank gap either side.
    # Without it the last plank's outer edge IS the rect's boundary, the 0.2 m verification
    # grid samples exactly there, and every one of those samples falls in the gap past the
    # last plank: measured, the whole east column of all four landings read as open water
    # (moorage 20 of 230 samples, and it was the only thing still failing). A deck a
    # finger's breadth wider than the walkway it carries is also just how a deck is built.
    OVERHANG = 0.06
    # ...and it runs a plank-edge past the measured band ALONG the run too, clamped to the
    # rect.  The drying decks' apron ended exactly on y 26.45 and the verifier's row at
    # y 26.45 fell past the last plank: 9 of its 27 samples, one whole row, read as river.
    by0 = max(rect[2], by0 - OVERHANG)
    by1 = min(rect[3], by1 + OVERHANG)
    poly = [Vector((rect[0] - OVERHANG, by0, deck_z)), Vector((rect[1] + OVERHANG, by0, deck_z)),
            Vector((rect[1] + OVERHANG, by1, deck_z)), Vector((rect[0] - OVERHANG, by1, deck_z))]
    # planks run ACROSS the pier, the way a jetty is boarded (and the way
    # locksfoot_build.staging boards the moorage's own stage)
    v, f = plank_fill(poly, math.radians(90), w=0.30, gap=0.016, thick=0.12, jitter=0.014,
                      drop=0.0, zfn=lambda X, Y: deck_z, seed=stable_hash("wfd_" + lid) & 0xffff)
    parts = [new_mesh("wfd_%s_deck" % lid, v, f, MD, COLL)]
    # joists along the run, one per 1.5 m of width, and a pile pair per 1.6 m of length
    nx = max(1, int((rect[1] - rect[0]) / 1.5))
    piles = 0
    skipped = []
    for k in range(nx + 1):
        u = rect[0] + 0.25 + k * (rect[1] - rect[0] - 0.5) / max(nx, 1)
        parts.append(beam("wfd_%s_joist%d" % (lid, k), (u, by0, deck_z - 0.22),
                          (u, by1, deck_z - 0.22), 0.13, 0.20, MT, COLL))
        m = max(1, int((by1 - by0) / 1.6))
        for q in range(m + 1):
            w = by0 + 0.30 + q * (by1 - by0 - 0.60) / max(m, 1)
            g = solid_below(u, w, deck_z - 0.40)
            zb = (g[0] if g else deck_z - 5.0) - 0.35
            if deck_z - 0.30 - zb < 0.8:
                continue
            # A PILE MAY NOT STAND IN A LOWER TIER'S CORRIDOR.  The drying decks are 5 m
            # above the fish dock's walkway and the first version dropped four piles
            # straight through it — walk_bodygate measured 446 blocked steps on
            # walk_e_tenant-shack__fish-dock at z 1.53, an invisible post in a street,
            # which is the same class of defect as the gate stair's rail.  The town's own
            # builders guard this with a Corridor; here it is one query per pile.
            crossed = walk_in_column(u, w, zb, deck_z - 0.28, lid)
            if crossed:
                skipped.append((round(u, 2), round(w, 2), crossed))
                continue
            parts.append(cyl("wfd_%s_pile%d_%d" % (lid, k, q), (u, w, zb), (u, w, deck_z - 0.28),
                             0.14, 7, MWET, COLL))
            piles += 1
    ob = join_meshes(parts, "wfd_%s_landing" % lid, COLL)
    made.append(ob.name)
    log("BUILD", ob.name, "%.1f m2 of planking, %d joists, %d piles, top z %.3f"
        % ((rect[1] - rect[0]) * (by1 - by0), nx + 1, piles, deck_z))
    for u, w, why in skipped:
        log("NO PILE", "at (%.2f, %.2f)" % (u, w), "its column crosses %s" % why)
    for rn, n in rail_gap(rect, deck_z, lid).items():
        log("RAIL GAP", rn, "%d face(s) cut inside the landing's own 2.05 m corridor — "
            "the way onto it" % n)

print("\n" + "-" * 92)
print("FOOTPRINT RECTS THESE LANDINGS MAKE LEGAL (measure them with landing_footprint.py "
      "before stamping):")
for lid, r in report.items():
    print("   %-15s connective %s" % (lid, r["rect"]))
print(json.dumps(report, indent=1))

if PHASE == "build" and SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=MASTER)
    print("\nSAVED %s  (%d landing(s))" % (MASTER, len(made)))
elif PHASE == "build":
    print("\n(dry build — pass `save` to write the master)")
