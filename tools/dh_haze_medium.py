"""dh_haze_medium.py — THE CAMERAS LOOK WITH THE SUN, AND THE RENDER PAYS FOR NO SECOND
VOLUME BOUNCE.  Dellhollow graphics round 6.

  /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-master.blend \
      --python-exit-code 1 -P tools/dh_haze_medium.py -- [save] [restore] \
      [--aniso -0.25] [--mid 3.5] [--far 2.5] [--x1 140.5]

  SHIPPED:  `--aniso -0.25 --mid 3.5 --far 2.5 save`

WHAT ROUND 5 HANDED OVER, AND WHAT MEASUREMENT SAYS ABOUT IT.

Round 5's item was one sentence: `fx_haze_east` is still a 6 m CURTAIN AT ONE X
(x 124..130), so aerial perspective is keyed to A PLANE IN THE WORLD rather than to
distance along the view, and the judge's surviving frame-edge row had moved its subject
to the card's own edge on FIVE plates — gate, shelf-east, weave, waterfront,
north-landing.

THE FIVE PLATES ARE NOT ONE FINDING.  The report merges a checklist row across plates
under the FIRST plate's wording, so "Dense cloud layer cuts off somewhat abruptly
against cliff geometry" is gate's sentence, printed over four other plates' answers.
Read per plate out of `findings.json`, with each plate's own judge bbox put on the
geometry by `dh_seam_census box`:

  gate           WEAK     u 0.00..0.47 v 0.00..0.38  86.5% cliff_east_closure,
                          meeting cliff_town_d/a at u 0.456..0.468.  THE HANDOVER'S
                          MECHANISM, AND IT IS REAL: measured step across that seam on
                          the shipped plate, v 0.00..0.10, closure L 153.0 vs town wall
                          79.2 -> |step| 73.8.
  weave          WEAK     u 0.00..0.45 v 0.00..0.20  45.3% cliff_east_closure +
                          23.2% cliff_town_a/d.  NOT A STEP: 6.4 / 3.2 / 8.9 L across
                          the same three bands.  It is DARKNESS — box L p50 19.2,
                          53.3% crushed — i.e. round 4's own named residual ("weave is
                          still the darkest of the four ... if any plate wants a second
                          rung it is that one"), not a card edge.
  shelf-east     WEAK     u 0.50..1.00 v 0.00..0.30  cliff_far_toe 19.4% + cliff_far
                          15.1% + fx_far_town_base 15.6% + fx_ridge_upstream(_mid)
                          15.5%.  THE UPSTREAM FAR FIELD, 38.7% crushed, L p50 13.6.
                          ZERO rays cross fx_haze_east.  Round 4 never reached it.
  waterfront     FAILING  u 0.78..0.82 v 0.00..0.10  65.7% fx_ridge_upstream_mid.
                          Upstream again.  ZERO rays cross fx_haze_east.
  north-landing  FAILING  u 0.00..0.34 v 0.00..0.075  91.7% `lf_ground` at 19..30 m,
                          L p50 145.6, 4.9% crushed, NO VOLUME CARD CROSSED BY ANY RAY.
                          REFUTED: the box holds bright near ground, not a void.

So the handover's mechanism owns ONE of the five (gate), and the other four are:
darkness on the east side that round 4 half-lifted (weave), the SAME defect round 4
fixed but on the UPSTREAM side, which no round has touched (shelf-east, waterfront),
and one finding aimed at nothing (north-landing).

THE CLASS IS ATMOSPHERE — not light, not grade.  Nothing is added, moved or
re-energised; no exposure, view transform or tone curve is touched.  The town's
lighting doctrine ("adjusting an existing light has never moved this town; ADDING a
source always has") is about lights and does not govern here, and round 4 already
recorded why the light lever is unavailable on the east wall in particular:
`KEY_gorgewall` exists at 3 W and raising it prints `mat_rock_gorgewall`'s 16.7 m
texture period as a quilt across a 98 m wall.

REFUSED, AND IT IS THE FINDING OF THE ROUND — MAKING THE CURTAIN A MEDIUM (`--x1`).
The obvious structural answer to "tau is keyed to a plane" is to give the medium DEPTH:
move `fx_haze_east`'s far face from x = 130 to x = 140.5 (`cliff_east_closure`'s own
front face), leave the near face where the spill census measured it, and divide the
world-Z density ramp by the same 2.75 the card is thickened by.  OPTICAL DEPTH THROUGH A
FULL CROSSING IS THEN UNCHANGED TO THE LAST DIGIT (0.102 x 6.00 = 0.037091 x 16.50 =
0.612000), so round 4's swept level looks preserved by construction.  IT IS NOT, and the
draft A/B says so in two ways:

  * **TAU IS NOT THE WASH.  A MEDIUM MOVED AGAINST A WALL MOVES INTO ITS SHADOW.**
    Extinction is a property of the medium; IN-SCATTER is a property of how much light
    reaches it.  Hard against the closure, most of the slab stands in the wall's and the
    buttresses' shadow, so the same tau delivered a far dimmer wash.  Measured on the
    far field (pixels >= 90 m by the shipped depth.png), shipped -> slab:
        gate     p05 14.7 -> 7.6   p50 47.7 -> 46.2   crushed 12.8% -> 15.3%
        weave    p05 13.9 -> 4.5   p50 18.3 -> 7.8    crushed 83.5% -> 83.3%
        lockfive p05 17.3 -> 6.1   p50 37.1 -> 38.0   crushed 25.8% -> 26.6%
    i.e. it gives back most of what round 4 won.
  * **AND IT DOES NOT REACH THE THING IT WAS AIMED AT.**  The grading was supposed to
    come from `cliff_town_a`/`_d` standing inside the medium.  The town wall's measured
    luminance across the gate seam moved 81.0 -> 79.5 / 67.8 -> 65.6 / 43.7 -> 42.5 —
    NOTHING.  Round 5's seam census gives the wall-side hits as x 103.9..134.1, and the
    MASS of that is nearer than x = 124: the medium was thickened past most of its
    subject.  The gate step at v 0..0.10 did fall 71.5 -> 38.2, but by killing the
    haze's brightness, not by lifting the wall's — and the two bands below it got WORSE
    (41.7 -> 56.6, 26.5 -> 34.2).
`--x1` is kept as the reproduction of that refusal.  Do not ship it.

WHAT SHIPPED INSTEAD, AND IT IS ONE NUMBER FOR BOTH ENDS OF THE PROBLEM.

  EAST — THE PHASE FUNCTION, NOT THE DENSITY.  `mat_haze_east`'s Volume Scatter
  anisotropy goes 0.30 (forward) to **-0.25** (slightly backward).  Tau is untouched,
  the scattering albedo is untouched, the geometry is untouched: only the ANGULAR
  distribution of the scattered light changes.  TWO FACTS MAKE THAT THE RIGHT LEVER HERE
  AND NEITHER IS A PREFERENCE:
    (1) DELLHOLLOW'S CAMERAS LOOK WITH THE SUN, NOT INTO IT.  For a camera with the key
        behind it the sun->medium->lens path is a near-180-degree turn, which a
        forward-scattering phase function SUPPRESSES.  `gate` is the one camera that
        looks across the rake — which is exactly why `gate` was the one plate that blew
        out white while the other four went black.  THEY ARE THE TWO ENDS OF ONE PHASE
        FUNCTION, so one number moves both, in opposite directions, correctly.
    (2) `bpy.context.scene.cycles.volume_bounces == 0`.  THE RENDER DOES NO MULTIPLE
        VOLUME SCATTERING AT ALL, and multiple scattering is precisely what makes real
        forward-scattering haze bright in back-scatter.  A negative g is the
        single-scatter stand-in for the bounces this bake does not pay for.
  Swept on the far-field mask at 1008x576/28 spp (g = 0.30 shipped, then 0.00, -0.25,
  -0.50), the STOPPING RULE IS THE p05 KNEE — past -0.25 the black stops lifting and
  only the median keeps climbing, which is the "featureless bank" direction round 4
  refused by eye:
        gate      p05 14.7 / 17.2 / 18.0 / 17.8     p50 47.7 / 51.8 / 55.0 / 59.2
        weave     p05 13.9 / 17.1 / 17.5 / 17.1     p50 18.3 / 24.4 / 27.5 / 30.0
        lockfive  p05 17.3 / 22.8 / 25.0 / 25.8     p50 37.1 / 41.6 / 44.3 / 47.1
        crossing  p05  8.0 / 10.2 / 11.7 / 11.3     p50 38.5 / 42.8 / 45.7 / 49.7
  and gate's blowout falls with it (far p95 166.0 -> 137.1) while the near field does
  not move (REST p50 77.4 -> 77.4, 49.2 -> 49.1, 24.5 -> 25.1).

  WEST — THE UPSTREAM LADDER, WHICH ALREADY HAD THE STRUCTURE.  `fx_haze_mid` (24 m) /
  `fx_haze_far` (24 m) / `fx_haze_rim` (44 m) are ALREADY slabs at graded distance: THE
  TOWN KNEW THE ANSWER ON ONE SIDE.  Their defect is level — a ray to the upstream far
  field at 100-140 m collected tau 0.086 + 0.024 against the east closure's 0.612 — so
  `--mid` / `--far` scale their densities.  The rung shipped (x3.5 / x2.5) is the one
  that KEEPS THE LADDER MONOTONE IN DISTANCE: crosswise tau mid 0.286 < far 0.480 <
  rim 0.594.  The next rung up (x5.0 / x3.5) puts `far` at 0.672, PAST the rim behind
  it, which is an inverted depth cue again — the very defect round 4 was fixing.
  `fx_haze_rim` is deliberately untouched: it is crossed by 0 of 138,240 rays across all
  fifteen cameras and is already the second-densest card in town.  Raising something no
  camera can see is not a fix.

THREE GATES IT ASSERTS RATHER THAN ASSUMES.  Two are round 4's and one is new.
  1. every material touched has EXACTLY ONE user (a material-scoped edit is only safe
     when the material is not shared);
  2. every card touched keeps `visible_shadow = False` (DAYLOG 2026-08-01: a dense slab
     nearly parallel to the sun's rake stopped being atmosphere and rendered the gate's
     whole south wall black);
  3. NEW — NO SOLVED CAMERA MAY LIE INSIDE ANY CARD, with its margin printed.
     `north-landing`'s eye sits at x = 121.12, which is 2.88 m in front of the east
     card's near face.  Growing that card TOWARD the town instead of toward the wall —
     the other obvious way to give it depth — would have swallowed that camera and
     washed its entire frame, and nothing else in the pipeline would have said so: the
     plate would simply have come back milky.  The margin is a DISTANCE TO THE BOX, not
     to the nearest face plane; every camera in this gorge is a hair from some card's z
     plane while being a hundred metres outside it in x, and reporting that would make
     the gate read as a near miss on every run.

`restore` is exact: the manifest records the eight vertex X coordinates, the ramp's two
`To` values, the anisotropy and every density this tool scaled.
"""
import bpy, os, sys, json, math

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/dh_haze_medium.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
RESTORE = "restore" in argv


def opt(f, d):
    return float(argv[argv.index(f) + 1]) if f in argv else d


X1 = opt("--x1", 0.0)            # >0: move the east card's FAR face here (REFUSED, see above)
ANISO = opt("--aniso", 999.0)    # set mat_haze_east's Volume Scatter anisotropy
MID = opt("--mid", 1.0)          # density multiplier on fx_haze_mid
FAR = opt("--far", 1.0)          # density multiplier on fx_haze_far
EAST = "fx_haze_east"
WEST = (("fx_haze_mid", MID), ("fx_haze_far", FAR))

from mathutils import Vector


def bounds(ob):
    # FROM THE VERTICES, NOT `bound_box`: bound_box is a CACHE, and in background mode it
    # does not refresh after a mesh edit — the first run of this carrier moved the far face
    # to 140.5 and its own gate read back 130.0 and refused the edit it had just made.
    p = [ob.matrix_world @ v.co for v in ob.data.vertices]
    return (min(v.x for v in p), max(v.x for v in p), min(v.y for v in p),
            max(v.y for v in p), min(v.z for v in p), max(v.z for v in p))


def scatter(ob):
    m = ob.material_slots[0].material
    ns = [n for n in m.node_tree.nodes if n.type == 'VOLUME_SCATTER']
    assert len(ns) == 1, "%s: expected one Volume Scatter, found %d" % (m.name, len(ns))
    return m, ns[0]


def ramp(m):
    ns = [n for n in m.node_tree.nodes if n.name == "DH_HAZE_RAMP"]
    return ns[0] if ns else None


# --- GATE 1 + GATE 2, on every card this tool may touch ------------------------
TOUCH = [EAST] + [n for n, _ in WEST]
for nm in TOUCH:
    ob = bpy.data.objects.get(nm)
    assert ob is not None, "no %s" % nm
    mat, _ = scatter(ob)
    users = [o.name for o in bpy.data.objects
             if o.type == 'MESH' and any(s.material is mat for s in o.material_slots)]
    assert users == [nm], "%s is worn by %s, not by %s alone" % (mat.name, users, nm)
    assert ob.visible_shadow is False, "%s must keep visible_shadow = False" % nm

east = bpy.data.objects[EAST]
mat_e, vs_e = scatter(east)
mr = ramp(mat_e)
assert mr is not None, ("%s carries no DH_HAZE_RAMP — run tools/dh_haze_east_depth.py "
                       "first; this carrier scales that ramp, it does not create one" % mat_e.name)

b0 = bounds(east)
X0 = b0[0]
before = {"east_verts_x": [round(v.co.x, 6) for v in east.data.vertices],
          "east_bounds": [round(v, 4) for v in b0],
          "ramp_to": [float(mr.inputs['To Min'].default_value),
                      float(mr.inputs['To Max'].default_value)],
          "aniso": float(vs_e.inputs['Anisotropy'].default_value),
          "west": {n: float(scatter(bpy.data.objects[n])[1].inputs['Density'].default_value)
                   for n, _ in WEST}}

if RESTORE:
    assert os.path.exists(MANIFEST), "no manifest at %s" % MANIFEST
    man = json.load(open(MANIFEST))
    for v, x in zip(east.data.vertices, man["before"]["east_verts_x"]):
        v.co.x = x
    mr.inputs['To Min'].default_value = man["before"]["ramp_to"][0]
    mr.inputs['To Max'].default_value = man["before"]["ramp_to"][1]
    if "aniso" in man["before"]:
        vs_e.inputs['Anisotropy'].default_value = man["before"]["aniso"]
    for n, d in man["before"]["west"].items():
        scatter(bpy.data.objects[n])[1].inputs['Density'].default_value = d
    east.data.update()
    print("RESTORED east bounds -> x %.3f..%.3f, ramp -> %.6f..%.6f, west -> %s"
          % (bounds(east)[0], bounds(east)[1], man["before"]["ramp_to"][0],
             man["before"]["ramp_to"][1], man["before"]["west"]))
else:
    k = 1.0
    if X1 > 0:
        t_old = b0[1] - b0[0]
        t_new = X1 - X0
        assert t_new > t_old, ("--x1 %.2f would THIN the card (%.2f -> %.2f m); the far "
                               "face moves outward, never inward" % (X1, t_old, t_new))
        k = t_old / t_new
        for v in east.data.vertices:             # 8-vert box, unit scale, no rotation
            if abs((east.matrix_world @ v.co).x - b0[1]) < 1e-4:
                v.co.x += (X1 - b0[1])
        east.data.update()
        mr.inputs['To Min'].default_value = before["ramp_to"][0] * k
        mr.inputs['To Max'].default_value = before["ramp_to"][1] * k
    if ANISO != 999.0:
        vs_e.inputs['Anisotropy'].default_value = ANISO
        print("EAST  mat_haze_east anisotropy %.3f -> %.3f  (PHASE FUNCTION: same tau, "
              "same albedo, different angular distribution)"
              % (before["aniso"], ANISO))
    for n, f in WEST:
        if f != 1.0:
            scatter(bpy.data.objects[n])[1].inputs['Density'].default_value = \
                before["west"][n] * f
    b1 = bounds(east)
    assert abs(b1[0] - X0) < 1e-4, "the NEAR face moved (%.4f -> %.4f)" % (X0, b1[0])
    if X1 > 0:
        assert abs(b1[1] - X1) < 1e-4, "the far face landed at %.4f, not %.4f" % (b1[1], X1)
    json.dump({"object": EAST, "before": before,
               "after": {"east_bounds": [round(v, 4) for v in b1], "ramp_scale": k,
                         "aniso": float(vs_e.inputs['Anisotropy'].default_value),
                         "ramp_to": [float(mr.inputs['To Min'].default_value),
                                     float(mr.inputs['To Max'].default_value)],
                         "west": {n: before["west"][n] * f for n, f in WEST}}},
              open(MANIFEST, "w"), indent=1)
    if X1 > 0:
        print("EAST  %s  x %.2f..%.2f -> %.2f..%.2f   thickness %.2f -> %.2f m (x%.3f)"
              % (EAST, b0[0], b0[1], b1[0], b1[1], b0[1] - b0[0], b1[1] - b1[0],
                 (b1[1] - b1[0]) / (b0[1] - b0[0])))
        print("      density ramp scaled x%.6f: %.6f..%.6f -> %.6f..%.6f"
              % (k, before["ramp_to"][0], before["ramp_to"][1],
                 mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value))
        print("      OPTICAL DEPTH THROUGH A FULL CROSSING IS UNCHANGED: %.6f x %.2f = "
              "%.6f  ->  %.6f x %.2f = %.6f  (floor rung).  THE WASH IS NOT — see the "
              "docstring; a medium moved against a wall moves into its shadow."
              % (before["ramp_to"][0], b0[1] - b0[0],
                 before["ramp_to"][0] * (b0[1] - b0[0]),
                 mr.inputs['To Min'].default_value, b1[1] - b1[0],
                 mr.inputs['To Min'].default_value * (b1[1] - b1[0])))
    else:
        print("EAST  geometry UNCHANGED (x %.2f..%.2f) — pass --x1 to thicken (refused in "
              "round 6, see the docstring)" % (b1[0], b1[1]))
    for n, f in WEST:
        print("WEST  %-14s density %.6f -> %.6f  (x%.2f)"
              % (n, before["west"][n], before["west"][n] * f, f))

# --- GATE 3: NO SOLVED CAMERA MAY LIE INSIDE ANY CARD --------------------------
cams = json.load(open(os.path.join(ROOT, "public/assets/scenes/del-cine/cine.json")))["cameras"]
worst = None
for nm in TOUCH:
    bb = bounds(bpy.data.objects[nm])
    for c in cams:
        p = c["pos"]
        inside = all(bb[2 * i] <= p[i] <= bb[2 * i + 1] for i in range(3))
        assert not inside, "camera %s (%.2f, %.2f, %.2f) is INSIDE %s" % (
            c["id"], p[0], p[1], p[2], nm)
        # THE MARGIN IS THE DISTANCE FROM THE EYE TO THE BOX, not the nearest face plane:
        # every camera in this gorge is "0.1 m from" some card's z plane while being 100 m
        # outside it in x, and reporting that number would make the gate read as a hair's
        # breadth every single run.
        out = [max(bb[2 * i] - p[i], p[i] - bb[2 * i + 1], 0.0) for i in range(3)]
        gap = math.sqrt(sum(v * v for v in out))
        if worst is None or gap < worst[0]:
            worst = (gap, c["id"], nm, "xyz"[max(range(3), key=lambda i: out[i])])
print("GATE camera-inside-card: CLEAR; tightest margin %.2f m — %s vs %s (separated in %s)"
      % (worst[0], worst[1], worst[2], worst[3]))

# --- GATE 4: THE FAMILY, IN THE ONLY QUANTITY THAT COMPARES --------------------
# DENSITY IS NOT THE WASH (round 4).  These cards are 2.7 m to 44 m thick, so ranking
# them by density ranks nothing; crosswise tau = density x thinnest span is the ruler.
print("THE STATIC VOLUME FAMILY, crosswise tau (= density x thinnest span):")
rows = []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or not ob.material_slots:
        continue
    m = ob.material_slots[0].material
    if m is None or not m.use_nodes:
        continue
    ns = [n for n in m.node_tree.nodes if n.type in ('VOLUME_SCATTER', 'PRINCIPLED_VOLUME')]
    if not ns:
        continue
    n = ns[0]
    bb = bounds(ob)
    span = min(bb[1] - bb[0], bb[3] - bb[2], bb[5] - bb[4])
    if n.inputs['Density'].is_linked:
        r = ramp(m)
        if r is None:
            rows.append((m.name, ob.name, None, None, span)); continue
        d = float(r.inputs['To Min'].default_value)
    else:
        d = float(n.inputs['Density'].default_value)
    rows.append((m.name, ob.name, d, d * span, span))
for mn, on, d, t, span in sorted(rows, key=lambda r: -(r[3] or 0)):
    if d is None:
        print("   %-18s %-24s density driven (unreadable)  span %5.1f m" % (mn, on, span))
    else:
        print("   %-18s %-24s density %.6f  span %5.1f m  tau %.4f  wash %4.1f%%"
              % (mn, on, d, span, t, 100 * (1 - math.exp(-t))))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("DRY RUN (pass `save` to write the master)")
