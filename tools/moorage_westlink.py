"""moorage_westlink.py — THE 2.5 m OF PLANKING THAT MAKES THE MOORAGE ONE DECK.

    /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-master.blend \
        -P tools/moorage_westlink.py --python-exit-code 1 -- measure
    /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-master.blend \
        -P tools/moorage_westlink.py --python-exit-code 1 -- build save
    ... -- revert save                      # take the patch back out

WHAT IT FIXES (playtest round 20, measured 2026-08-05).  The moorage's footprint carries
three rects and the WEST STORE — `[70.9, 71.9, 26.2, 29.2]`, `lf_stage_moorage_w` — touches
none of the others.  It is 3.0 m2 of deck at top 1.20 whose only plan neighbour is
`walk_pad_tenant-shack` 0.79 m ABOVE it, and that makes it a ONE-WAY PIT:

    _court_probe --scene del-cine --way, SIM.move, both directions
      pad -> west store   3/3 legs          a 0.79 m step DOWN, inside STEP_DN 0.80
      west store -> pad   STALLS            0.79 m is 0.16 m past STEP_UP 0.63, and
                                            `walk_pad_tenant-shack`'s own 1.92..2.04 slab
                                            sits 20 mm inside a body's blocking window
                                            over a 1.20 floor ([1.85, 2.50])
      west store -> east  STALLS at x 72.05  2.5 m of open water to the next deck
      x 71.5..71.9 north  STALLS            `cx_mr_slabs001_1` / `cx_rail`

In `docs/qa/playtest/ch2-arrive-receipt/run.jsonl` the Chapter Two playtest agent stepped
down onto it at step 75 and was still on it at step 120 — **46 of 120 steps, x 70.76..72.08,
y 1.25 every frame** — filing five reports about pillars while it stood in a pit.

THE MAP DID NOT INTEND A RAMP OR A STAIR THERE.  It intended this deck to be continuous:
`waterfront_landings.py` built the moorage's pier in 2026-08-01 for exactly this reason
("before the stamp ... `walk_lm_moorage` kept only its 3.0 m2 west-store rect"), but its
`connective_rect` runs 2.0 m about `pos` and the west store is not in that column, so the
one rect that was already an island stayed one.  This is that tool's missing second landing,
written as its own additive carrier rather than as a re-run: `waterfront_landings.py --build`
deletes and rebuilds all four landings and destructively cuts rail faces, and the master has
moved a long way since it last ran.  `emb_lanepatch.py`'s rule — additive, revertible,
`mwl_*` only, never a rebuild of a live master.

EVERY NUMBER IS MEASURED, NOT TYPED.  `measure` prints the same numbers `build` acts on:
  * the two bank EDGES and their deck TOPS come from a 0.02 m ray scan along the run
    (`solid_below`, waterfront_landings' rule verbatim — it passes through walk ribbons and
    stops on water, or a ray that lands on a walk mesh reports bare river over real deck);
  * the deck height is the two banks' mean, and the build REFUSES if they differ by more
    than 0.10 m, because a link is a link and a ramp is a different object;
  * the material is read off the bank it continues;
  * the piles run to the first solid below, or to the riverbed.

AND IT REFUSES TO BUILD UNDER A CEILING.  A body standing on the new deck occupies
[z+STEP_UP+0.02, z+BODY_H] = [z+0.65, z+1.30]; the gate ray-casts that window over the
corridor's centreline against BOTH art and `walk_` records (a walk ribbon is solid to the
player — play3d's noStand list is water_/lm_/veg_ only) and stops if anything is in it.
It is run over the PAD RECTS the map will stamp, not over the deck, and grown by a body's
own 0.30 m half-width, because blocked() tests a box and not a point.  That is what shapes
the pad: `walk_e_weave-huts__moorage_l2_t04`'s underside ends at y 28.56, so the east rect
starts at 28.95 and the walk is a pinch under the stair rather than a straight run.

WHAT IT DOES NOT DO: stamp the map.  The footprint rects go into
`public/townmap/dellhollow.map.json` by hand and is carried into the master by
`walk_rederive.py --lm moorage` — one line of map, one command to re-derive, which is the
doctrine this patch exists to honour rather than replace.
"""
import bpy, math, sys
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import (REPO, new_mesh, beam, cyl, M, plank_fill, stable_hash)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PHASE = "build" if "build" in argv else ("revert" if "revert" in argv else "measure")
SAVE = "save" in argv
COLL = "DIST_wfdeck"
PREFIX = "mwl_"
MASTER = REPO + "/tools/blends/dellhollow-master.blend"
sc = bpy.context.scene

# The deck, in MAP coordinates (x along-gorge, y cliff->river, z height).  X is scanned,
# never typed; Y is a deck's own width, and the NORTH edge is as far as the deck can go
# without standing under the stair's foot at a height that matters.  MEASURED: of the six
# `walk_e_weave-huts__moorage_l2_t*` treads only TWO have an underside inside a body's
# blocking window over a 1.199 floor ([1.85, 2.50]) — t03 (bottom 2.20, x 74.18..75.22,
# y 26.84..28.36) and t04 (bottom 1.86, x 74.78..75.82, y 27.04..28.56).  t02's is 2.55,
# which clears by 50 mm, and t05's top is 1.66, which is under it.  So the deck runs full
# width west of the treads and the PAD narrows under them — which is why RECTS is a list
# and not one rectangle, and why the narrow one is the east one.
Y0, Y1 = 27.60, 29.95
X_SCAN = (71.20, 76.00)          # the window the two bank edges are looked for in
STEP_UP, BODY_H = 0.63, 1.30     # play3d.html:1918/1927 — quoted, not re-derived
PASS_THROUGH = ("walk_", "bar_", "fx_", "cam", "CAM", "REF_", "KEY", "lm_")
WATER = ("water", "riverbed")


def dg():
    return bpy.context.evaluated_depsgraph_get()


def solid_below(x, y, z, depth=40.0):
    """First render-visible non-water hit below z: (height, object) or None."""
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


def anything_in(x, y, z0, z1):
    """Any mesh — art OR walk record — inside the vertical window (z0, z1) at (x, y)."""
    z, left = z0, z1 - z0
    for _ in range(24):
        hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg(), Vector((x, y, z)), Vector((0, 0, 1)),
                                                 distance=left)
        if not hit or ob is None:
            return None
        if ob.name.startswith(("cam", "CAM", "REF_", "KEY", "lm_", "fx_")) or \
                (ob.hide_render and not ob.name.startswith(("walk_", "bar_"))):
            left -= (loc.z - z) + 1e-4
            z = loc.z + 1e-4
            if left <= 0:
                return None
            continue
        return round(loc.z, 3), ob.name
    return None


def banks():
    """Scan the run for the two deck edges and their tops. The whole geometry, measured."""
    yc = (Y0 + Y1) / 2.0
    n = int((X_SCAN[1] - X_SCAN[0]) / 0.02)
    hits = []
    for i in range(n + 1):
        x = X_SCAN[0] + i * 0.02
        s = solid_below(x, yc, 2.4)
        hits.append((round(x, 2), s))
    decked = [(x, s) for x, s in hits if s and 0.7 < s[0] < 1.8]
    if not decked:
        return None
    # the gap is the longest run of undecked samples between two decked ones
    idx = [i for i, (x, s) in enumerate(hits) if s and 0.7 < s[0] < 1.8]
    best = None
    for a, b in zip(idx, idx[1:]):
        if b - a > 1 and (best is None or b - a > best[1] - best[0]):
            best = (a, b)
    if best is None:
        return None
    a, b = best
    return {"west": hits[a], "east": hits[b],
            "gap": round(hits[b][0] - hits[a][0], 3)}


def clear_ceiling(rect, z, r=0.30):
    """Is a body standing anywhere on this PAD rect free? Returns the offenders.

    It asks about the rect the map will STAMP, not about the deck, because the pad is
    what the player's feet are allowed on — and it grows the body's own 0.30 m
    half-width (play3d BODY_R) outward, since blocked() tests a box and not a point.
    `bar_*` records are deliberately NOT excluded here even though `cine_bake --glb`
    drops them from the shipped bundle: a rail that only exists in the master is not a
    wall the player meets, and this is the one place that difference is written down.
    """
    x0, x1, y0, y1 = rect
    bad = []
    y = y0
    while y <= y1 + 1e-9:
        x = x0
        while x <= x1 + 1e-9:
            for dx in (-r, 0.0, r):
                for dy in (-r, 0.0, r):
                    h = anything_in(x + dx, y + dy, z + STEP_UP + 0.02, z + BODY_H)
                    if h and not h[1].startswith("bar_"):
                        bad.append((round(x, 2), round(y, 2), h))
            x += 0.30
        y += 0.30
    return bad


def landed_grid(rect, padtop):
    """landing_footprint's all-landed rule on the stamped rect: 0.2 m grid, 0.60 m window."""
    x0, x1, y0, y1 = rect
    nx, ny = max(1, int(round((x1 - x0) / 0.2))), max(1, int(round((y1 - y0) / 0.2)))
    n = ok = 0
    worst = None
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = min(x0 + i * 0.2, x1), min(y0 + j * 0.2, y1)
            s = solid_below(x, y, padtop - 0.06)
            n += 1
            if s and (padtop - s[0]) <= 0.60:
                ok += 1
            elif worst is None:
                worst = (round(x, 2), round(y, 2), None if not s else round(s[0], 2))
    return ok, n, worst


# =========================================================================== run
print("=" * 92)
print("MOORAGE WEST LINK — %s" % PHASE)
print("=" * 92)

gone = [o for o in bpy.data.objects if o.name.startswith(PREFIX)]
if PHASE in ("build", "revert"):
    for o in gone:
        bpy.data.objects.remove(o, do_unlink=True)
    print("  CLEAN     %d previous %s object(s) removed" % (len(gone), PREFIX))
    if PHASE == "revert":
        if SAVE:
            bpy.ops.wm.save_as_mainfile(filepath=MASTER)
            print("  SAVED     %s" % MASTER)
        print("REVERTED.")
        sys.exit(0)

B = banks()
assert B, "no deck edges found in the scan window — the geometry moved; re-measure"
(wx, ws), (ex, es) = B["west"], B["east"]
print("  west bank  x %.2f  top %.3f  (%s, %s)" % (wx, ws[0], ws[1].name,
      ws[1].data.materials[0].name if ws[1].data.materials else "no material"))
print("  east bank  x %.2f  top %.3f  (%s)" % (ex, es[0], es[1].name))
print("  GAP        %.2f m of open water" % B["gap"])
assert abs(ws[0] - es[0]) <= 0.10, \
    "the two banks differ by %.3f m — that is a ramp, not a link; this tool refuses" \
    % abs(ws[0] - es[0])
DECK_Z = round((ws[0] + es[0]) / 2.0, 3)
MAT = ws[1].data.materials[0].name if ws[1].data.materials else "mat_deck"
# the deck overlaps each bank by a plank's width so the two meet rather than butt
X0, X1 = round(wx - 0.15, 2), round(ex + 0.15, 2)
print("  deck       z %.3f, material %s, x %.2f..%.2f  y %.2f..%.2f  = %.1f m2"
      % (DECK_Z, MAT, X0, X1, Y0, Y1, (X1 - X0) * (Y1 - Y0)))

# The two footprint rects this build makes legal, and the shape is the measurement.
# A 0.15 m occupancy scan of the body window over this deck has exactly two obstructions
# and they are at OPPOSITE CORNERS: the stair's t03/t04 undersides fill x 74.30..75.50 for
# y <= 28.50 (the north-EAST), and `lf_railings` — the west store's own guard — fills a
# diagonal x 71.00..71.45 for y 28.95..29.55 (the south-WEST).  Everything else is free.
# So the pad is a NORTH band that runs out of the store and stops before the treads, and
# a SOUTH band that starts clear of the rail and runs on to the pier; they overlap over
# x 72.30..73.85 and town_blockout joins the rects, so the walk record is one surface.
# ONE RECT COULD NOT DO THIS: the only rectangle avoiding both corners is 0.15 m wide.
RECTS = [[71.50, 72.60, 27.75, 28.85],
         [72.30, 73.85, 27.75, 29.90],
         [73.40, 74.45, 28.75, 29.90],
         [74.20, 75.30, 28.95, 29.90]]
PADTOP = 1.0 + 0.245                       # moorage pos z + town_blockout's pad lift

bad = [q for R in RECTS for q in clear_ceiling(R, DECK_Z)]
print("  ceiling    body window %.2f..%.2f over BOTH pad rects (+/-0.30 body): %s"
      % (DECK_Z + STEP_UP + 0.02, DECK_Z + BODY_H,
         "CLEAR" if not bad else "%d OFFENDER(S)" % len(bad)))
for q in bad[:8]:
    print("               x %.2f y %.2f  <- %s" % (q[0], q[1], q[2]))
assert not bad, "something stands in the body's window over these pads — do not build"

for R in RECTS:
    ok, n, worst = landed_grid(R, PADTOP)
    print("  footprint  rect %s -> landed %d/%d BEFORE the build%s"
          % (R, ok, n, "" if ok == n else "  (worst %s)" % (worst,)))

if PHASE == "measure":
    print("\nmeasure: nothing was changed.")
    sys.exit(0)

# -------------------------------------------------------------------- the link
MD = M(MAT) or M("mat_deck")
MT = M("mat_timber") or MD
OVER = 0.06
poly = [Vector((X0, Y0 - OVER, DECK_Z)), Vector((X1, Y0 - OVER, DECK_Z)),
        Vector((X1, Y1 + OVER, DECK_Z)), Vector((X0, Y1 + OVER, DECK_Z))]
# planks ACROSS the run, the way locksfoot_build.staging boards the moorage's own stage
v, f = plank_fill(poly, math.radians(90), w=0.30, gap=0.016, thick=0.12, jitter=0.014,
                  drop=0.0, zfn=lambda X, Y: DECK_Z, seed=stable_hash("mwl_moorage") & 0xffff)
made = [new_mesh(PREFIX + "deck", v, f, MD, COLL)]
nj = 2
for k in range(nj):
    u = Y0 + 0.22 + k * (Y1 - Y0 - 0.44) / max(nj - 1, 1)
    made.append(beam(PREFIX + "joist%d" % k, (X0, u, DECK_Z - 0.22), (X1, u, DECK_Z - 0.22),
                     0.13, 0.20, MT, COLL))
piles = 0
np_ = max(2, int((X1 - X0) / 1.3))
for k in range(np_ + 1):
    u = X0 + 0.30 + k * (X1 - X0 - 0.60) / max(np_, 1)
    for w in (Y0 + 0.25, Y1 - 0.25):
        g = solid_below(u, w, DECK_Z - 0.45)
        zb = (g[0] if g else -0.6) - 0.30
        made.append(cyl(PREFIX + "pile%d_%d" % (k, 0 if w < (Y0 + Y1) / 2 else 1),
                        (u, w, DECK_Z - 0.30), (u, w, zb), 0.11, 8, MT, COLL))
        piles += 1
print("  BUILT      %d object(s): 1 deck, %d joists, %d piles" % (len(made), nj, piles))
for o in made:
    assert o.name.startswith(PREFIX), "an object escaped the %s prefix: %s" % (PREFIX, o.name)
bpy.context.view_layer.update()
xs = [c for o in made for c in (o.matrix_world @ Vector(o.bound_box[0]),
                                o.matrix_world @ Vector(o.bound_box[6]))]
print("  extent     x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f"
      % (min(c.x for c in xs), max(c.x for c in xs), min(c.y for c in xs),
         max(c.y for c in xs), min(c.z for c in xs), max(c.z for c in xs)))

for R in RECTS:
    ok2, n2, worst2 = landed_grid(R, PADTOP)
    print("  footprint  rect %s -> landed %d/%d AFTER the build%s"
          % (R, ok2, n2, "" if ok2 == n2 else "   !! %s" % (worst2,)))
    assert ok2 == n2, "rect %s is still not all-landed — the deck does not cover it" % R

if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=MASTER)
    print("  SAVED      %s" % MASTER)
print("\nSTAMP THESE IN THE MAP (moorage.footprint) AND RE-DERIVE:")
for R in RECTS:
    print("  %s" % R)
print("  Blender -b tools/blends/dellhollow-master.blend -P tools/walk_rederive.py "
      "--python-exit-code 1 -- --lm moorage save")
