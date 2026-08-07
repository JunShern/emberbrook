"""dh_albedo_floor.py — THE "PITCH-BLACK SLABS" ARE A 0.9% ALBEDO, NOT A SHADOW.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/dh_albedo_floor.py -- [save] [restore] [--floor 0.055]

Graphics round 3, item (c) "boatyard black slabs" — and the measurement is why
this is a MATERIAL carrier and not another lantern.

WHAT WAS MEASURED, and with what.
  1. A crushed-black census over all 15 del-cine plates (dark AND locally flat:
     L <= 24/255 with a 5x5 sd <= 2) says boatyard carries 7.7% crushed pixels,
     and a world-space reconstruction of the plate (cine.json's camera + its own
     rgb24-viewz depth.png) localises the worst of them to x 12.0..15.8,
     y 36.9..40.6, z 5.5..5.9 — `L mean 0.1/255, sd 0.4` on a 3.8 x 0.4 m face,
     and a second, UP-FACING patch at L mean 2.2.  That is not a dark shadow.
     It is zero.
  2. A ray census replaying the boatyard camera at the master, restricted to the
     pixels at L <= 8/255, resolves each hit's BASE COLOUR — flat for a plain
     material, nearest-corner `Col` for a vertex-colour-driven one:

       lock_four_dam   mat_blackstone   Col   n=209  albedo L 0.0085 .. 0.0155  (med 0.0094)
       slipway_ramp    mat_blackstone   Col   n=  8  albedo L 0.0094 .. 0.0096
       lf_crest_bay_*  mat_blackstone   Col          albedo L 0.0156 .. 0.0258
       lf_barge_*      lf_matte         Col          albedo L 0.0305
       (flat)          mat_stone_black_cap           albedo L 0.0287

     209 of the 279 blackest pixels in the frame are ONE material at a MEDIAN
     ALBEDO OF 0.94%.  For scale, the same probe reads the town's ordinary dark
     surfaces at lf_stone 0.125, lf_shingle 0.165, m_wood 0.171, lf_deck
     0.26..0.41.  The black family is an order of magnitude below the darkest
     thing anyone intended to be dark.

WHY THIS REFUSES THE WORKLIST'S OWN FRAMING.  Round 3 filed this under the
lighting class, whose doctrine is the one this repo has paid for twice: adjusting
an existing light has never moved this town, ADDING a source always has.  That
doctrine is about light, and this is not a light problem.  A 0.94% reflector
returns 0.94% of whatever arrives; at the shipped exposure (0.15, AgX) it cannot
reach a printable value from any lamp that would not also blow out its lit
neighbours.  Hanging a lantern over it would have moved the plate by ~1/255 and
cost a bake — which is exactly the failure `pit_lantern` records paying for once
already ("moved the bbox median 5.3 -> 4.9/255, i.e. NOT AT ALL").

AND THE SAME CENSUS SAYS THE STREETS ARE A DIFFERENT DEFECT.  Run on shelf-west
and quay-west, the blackest pixels land on lf_shingle 0.150..0.181, lf_stone
0.124..0.139, lf_deck 0.26..0.34 — NORMAL reflectance in deep shade.  Those are
genuinely unlit and the lighting doctrine does govern them.  They are left alone
here on purpose: the crushed census that would size that lamp recipe is
CONTAMINATED by this material bug (mat_blackstone / lf_matte are in the top hits
of boatyard, north-landing, lockfive AND crossing), so the honest order is fix
the albedo, RE-MEASURE, then size the lights against a clean number.

WHAT THIS DOES.  Raises every base colour in the black family to a FLOOR, in
place, preserving hue:  c *= FLOOR / L(c)  for any c with L(c) < FLOOR.

  * flat Base Color sockets on the named materials;
  * per-vertex `Col`, but ONLY on the loops whose polygon wears one of the named
    materials.  THIS IS LOAD-BEARING: `lock_four_dam` is a joined mesh carrying
    eleven material slots over ONE shared `Col` layer, and its median vertex
    luminance is 1.0 because mat_wallwood's loops are white there.  A
    mesh-scoped lift would repaint the lockhouse.

THE FLOOR IS 0.055 AND IT IS STILL THE DARKEST THING IN DELLHOLLOW.  Real
references bracket it: charcoal ~0.04, fresh asphalt ~0.04-0.05, wet slate
~0.06-0.08.  It sits 2.2x below mat_timber_dark's darkest (0.124), 2.3x below
lf_stone and 5x below lf_deck, so locksfoot_build's own art direction survives
verbatim — "black ... its coursing, its wet nappe and its boil, nothing more" —
while the surface stops being unrenderable.  The gate below asserts that
ordering rather than trusting it.

Idempotent (a second run finds nothing under the floor).

`restore` IS PARTIAL AND SAYS SO.  It puts the flat Base Color sockets back from the
manifest, and it CANNOT put the vertex colours back: the lift is
`c *= floor / L(c)`, so every loop was scaled by its OWN factor and the manifest
records the layer's minimum, not 18,660 per-loop originals.  Writing a plausible-
looking inverse would silently flatten a layer that used to vary.  The way back for
the vertex colours is `git checkout tools/blends/dellhollow-master.blend`, which is
exact; the script prints that instead of pretending.  (Recording the full originals
would make this reversible and would also put ~18k colours in a manifest nobody
reads — if a future round wants that, it is a deliberate trade, not an oversight.)
"""
import bpy, os, sys, json

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/dh_albedo_floor.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
RESTORE = "restore" in argv
FLOOR = float(argv[argv.index("--floor") + 1]) if "--floor" in argv else 0.055

# The family, named by the ray census — nothing is guessed and nothing is swept in
# by a name pattern.  `mat_iron` (0.0391) is deliberately EXCLUDED: it is small
# ironwork, it reads as ironwork, and no judge or census complained about it.
TARGETS = ["mat_blackstone", "mat_stone_black_cap", "lf_matte"]

# The town's next-darkest materials — the gate's ordering assertion runs against
# these, so a floor that crossed them would fail the build rather than ship.
DARKEST_NEIGHBOURS = {"lf_stone": 0.1244, "mat_timber_dark": 0.1238, "lf_shingle": 0.1503}


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def lifted(c, floor):
    L = lum(c)
    # THE EPSILON IS THE IDEMPOTENCE.  Without it the round-trip through the
    # colour attribute's float32 storage lands a hair under `floor`, the second
    # run "lifts" every loop it already lifted by 1.0000001, and the manifest
    # reports thousands of edits that are not edits — a receipt that lies.
    if L >= floor - 1e-5 or L <= 1e-6:
        return None
    k = floor / L
    return (c[0] * k, c[1] * k, c[2] * k)


rec = {"_doc": "generator receipt; see tools/dh_albedo_floor.py",
       "generator": "tools/dh_albedo_floor.py", "floor": FLOOR,
       "targets": TARGETS, "flat": {}, "vcol": {}}

prev = {}
if os.path.exists(MANIFEST):
    try:
        prev = json.load(open(MANIFEST))
    except Exception:
        prev = {}

# ------------------------------------------------------------------ flat -----
for name in TARGETS:
    m = bpy.data.materials.get(name)
    if not m or not m.use_nodes:
        continue
    for n in m.node_tree.nodes:
        if n.type != 'BSDF_PRINCIPLED':
            continue
        s = n.inputs['Base Color']
        if s.is_linked:
            continue
        c = tuple(s.default_value[:3])
        if RESTORE:
            old = (prev.get("flat", {}) or {}).get(name)
            if old:
                s.default_value = (old["before"][0], old["before"][1], old["before"][2], 1.0)
                print("RESTORE flat %-24s -> %s" % (name, old["before"]))
            continue
        nc = lifted(c, FLOOR)
        if nc:
            s.default_value = (nc[0], nc[1], nc[2], 1.0)
            rec["flat"][name] = {"before": [round(v, 5) for v in c],
                                 "after": [round(v, 5) for v in nc],
                                 "L_before": round(lum(c), 5), "L_after": round(lum(nc), 5)}
            print("FLAT  %-24s L %.4f -> %.4f  %s -> %s"
                  % (name, lum(c), lum(nc), [round(v, 4) for v in c], [round(v, 4) for v in nc]))
        break

# ------------------------------------------------------------------ vcol -----
# MATERIAL-SCOPED, per the docstring: only loops whose polygon wears a target.
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data
    if not me.color_attributes or not me.materials:
        continue
    slots = [i for i, mm in enumerate(me.materials) if mm and mm.name in TARGETS]
    if not slots:
        continue
    ca = me.color_attributes[0]
    corner = (ca.domain == 'CORNER')
    touched, before_lo, after_lo, n_tot = 0, 1e9, 1e9, 0
    key = "%s|%s" % (ob.name, ca.name)
    oldrec = (prev.get("vcol", {}) or {}).get(key)
    for poly in me.polygons:
        if poly.material_index not in slots:
            continue
        for li in poly.loop_indices:
            idx = li if corner else me.loops[li].vertex_index
            d = ca.data[idx]
            c = tuple(d.color[:3])
            n_tot += 1
            if RESTORE:
                continue        # see the RESTORE note below — this path is honest, not lossy
            nc = lifted(c, FLOOR)
            if nc:
                before_lo = min(before_lo, lum(c))
                d.color = (nc[0], nc[1], nc[2], d.color[3])
                after_lo = min(after_lo, lum(nc))
                touched += 1
    if touched:
        rec["vcol"][key] = {"object": ob.name, "layer": ca.name, "domain": ca.domain,
                            "slots": [me.materials[i].name for i in slots],
                            "loops_in_slots": n_tot, "lifted": touched,
                            "L_min_before": round(before_lo, 5),
                            "L_min_after": round(after_lo, 5), "floor": FLOOR}
        print("VCOL  %-26s %-22s lifted %5d/%5d loops   L min %.4f -> %.4f"
              % (ob.name[:26], ",".join(rec["vcol"][key]["slots"])[:22],
                 touched, n_tot, before_lo, after_lo))
    me.update()

# ------------------------------------------------------------------ gate -----
# THE GATE IS THE ORDERING, ASSERTED, NOT ASSUMED.  The black family must end up
# above zero and still BELOW every ordinary dark material in the town, or the art
# direction locksfoot_build wrote down has been overwritten and this build fails.
if not RESTORE:
    worst = 1e9
    for name in TARGETS:
        m = bpy.data.materials.get(name)
        if not m or not m.use_nodes:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED' and not n.inputs['Base Color'].is_linked:
                worst = min(worst, lum(tuple(n.inputs['Base Color'].default_value[:3])))
    for k, v in rec["vcol"].items():
        worst = min(worst, v["L_min_after"])
    if worst < 1e9:
        assert worst >= FLOOR - 1e-4, \
            "a target surface is still under the floor: %.5f < %.5f" % (worst, FLOOR)
        lowest_neighbour = min(DARKEST_NEIGHBOURS.values())
        assert worst < lowest_neighbour, \
            ("the black family is no longer the darkest thing in town: %.4f >= %.4f (%s)"
             % (worst, lowest_neighbour, min(DARKEST_NEIGHBOURS, key=DARKEST_NEIGHBOURS.get)))
        print("GATE  black-family floor %.4f  <  darkest ordinary material %.4f (%s)  OK"
              % (worst, lowest_neighbour, min(DARKEST_NEIGHBOURS, key=DARKEST_NEIGHBOURS.get)))
    else:
        print("GATE  nothing under the floor — idempotent no-op")

    # A NO-OP MUST NOT OVERWRITE THE RECEIPT.  This script is idempotent by
    # design, so the SECOND run finds nothing and would otherwise replace the
    # manifest that records what the FIRST run actually did with an empty one —
    # deleting the only measurement of the edit that is in the master.
    if rec["flat"] or rec["vcol"]:
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        json.dump(rec, open(MANIFEST, "w"), indent=1)
        print("MANIFEST", MANIFEST)
    else:
        print("MANIFEST kept (nothing lifted this run — a no-op does not rewrite the receipt)")

if RESTORE:
    print("RESTORE covered the FLAT sockets only. The per-loop vertex colours are NOT "
          "reversible from this manifest (each loop was scaled by its own factor); "
          "use `git checkout tools/blends/dellhollow-master.blend` for those.")

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
