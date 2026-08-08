"""dh_haze_east_depth.py — THE EAST WALL IS NOT A HAZE CARD, AND THE HAZE CARD IS NOT
DOING ITS JOB.  Graphics round 4, and the worklist item it closes was named wrong.

  /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-master.blend \
      --python-exit-code 1 -P tools/dh_haze_east_depth.py -- [save] [restore] [--base 0.060]

WHAT THE ROUND-3 WORKLIST SAID, AND WHAT THE MEASUREMENT SAYS.

Round 3 handed this over as round 4's top item: "`fx_haze_east` / `mat_haze_east` is the
most-hit object in the crushed-pixel sample on lockfive (42 of 220) and weave (54 of 220),
`fx_haze_south` on quay-west … NEITHER MATERIAL CARRIES A PRINCIPLED BSDF AT ALL."  Three
claims, and measurement refuses all three as stated:

  1. NO PRINCIPLED BSDF IS THE DESIGN, NOT A DEFECT.  `mat_haze_east` is a two-node
     Volume Scatter (0.48/0.50/0.60, anisotropy 0.3) with no surface shader — and so are
     `mat_haze_far`, `_mid`, `_rim`, `_south` and `mat_spray`.  An albedo resolver that
     walks the tree looking for a surface BSDF returns nothing on all six.  The resolver
     found its own blind spot, not a broken material.

  2. THE CARD IS AN ATTENUATOR, NOT A SURFACE, AND THE CENSUS THAT NAMED IT DID NOT MARCH
     THROUGH IT.  `tools/dh_pixel_census.py` re-ran the crushed sample marching past
     render-only volumes, and the pixels land on `cliff_east_closure | mat_rock_gorgewall`
     — lockfive 83.2%, weave 96.0%, gate 91.8% of a 400-sample draw, at 92-170 m.  The
     card's own optical depth over those same rays is tau 0.055-0.060: A 5.4% WASH.  It
     was standing in front of the answer, which is exactly the failure DAYLOG already
     records twice ("volume cards are meshes to a ray-caster"; "a first-hit tally that
     does not drop hide_render objects is a lie about the frame").

  3. `fx_haze_south` ON QUAY-WEST IS REFUTED OUTRIGHT.  Quay-west's largest crushed region
     is `qm_stair_underworks | mat_qm_stone_dark` 62.8% + `seam_bank | mat_rock` 26.0% at
     24-27 m, and ZERO rays through it cross any haze card.  Untouched here.

SO WHAT IS THE DEFECT.  The most distant surface in Dellhollow is also its darkest, which
INVERTS the depth cue: `cliff_east_closure` is 6,020 m2 of wall at 92-170 m reading L 9.8
(weave) to 44.6 (crossing) with 84% / 26% / 8% / 8% of its pixels crushed, while the town
20 m from the lens reads 25-76.  There is no aerial perspective in this town's far field.
The object that exists to supply it is this card, and it under-delivers by an order of
magnitude for a structural reason: IT IS A 6 m CURTAIN, NOT A MEDIUM.  Its optical depth
is set by its own thickness, so it is the same 5.4% whether the thing behind it is 90 m
away or 170 m away.  A distance cue that does not vary with distance is not a distance cue.

THE FIX, AND ITS CLASS.  This is an ATMOSPHERE change — not a light (nothing is added,
moved or re-energised) and not a grade (no exposure, no view transform, no tone curve).
The town's lighting doctrine ("adjusting an existing light has never moved this town;
adding a source always has") is therefore not the governing rule here, and saying so
matters: `KEY_gorgewall` already exists, a 3 W sun at N.L +0.842 dedicated to this very
wall, and the gate lane already PROBED AND REJECTED raising it, because at 3 W it starts
printing `mat_rock_gorgewall`'s 16.7 m texture period as a quilt across a 98 m wall.  More
light on this surface makes a tiling artefact legible.  More haze hides it AND lifts the
black, which is why the haze is the correct lever and not merely the available one.

Density becomes a WORLD-Z RAMP rather than a constant: dense in the gorge floor, thin at
the rim, which is both what valley haze does and what keeps the wash from reading as one
flat card.  Swept at 1008x576/28 spp against the shipped plate's own measured wall mask
(pixels reconstructing to world x >= 138 out of `depth.png`), lockfive + gate:

  variant                 lockfive wall L p05/p50/p95      gate wall p05/p95   REST p50
  shipped   0.009167        7.3 / 38.3 / 60.3               11.3 / 105.6       24.8 / 76.2
  uniform   0.060          18.7 / 38.3 / 54.6               22.8 / 184.6       24.9 / 76.2
  uniform   0.110          23.1 / 36.8 / 49.7               27.1 / 202.2       24.7 / 76.2
  ramp 0.068->0.018        17.4 / 38.5 / 55.6               20.0 / 151.2       24.7 / 76.2
  ramp 0.102->0.027  <--   20.7 / 37.9 / 53.3               23.1 / 168.0       24.7 / 76.2

The shipped ramp DOMINATES the uniform 0.060 on both ends at equal cost: more black lifted
(lockfive p05 20.7 vs 18.7) and less forward-scatter blowout where the sun rakes through
the card toward the gate camera (p95 168.0 vs 184.6).  Uniform 0.110 lifts more and was
REFUSED BY EYE: it dissolves the wall into a featureless bank, which trades one of the
judge's words for the other.

WHY RAISING IT IS SAFE, MEASURED.  This repo has paid once for a haze card that became
visible as a card (DAYLOG "THE SALMON CARD"), so the question is not "is 11x more density
a lot" but "what else is behind this card".  `dh_pixel_census.py frustum` casts a 128x72
grid per camera and splits the rays that cross the card into BEHIND (they land on the far
wall / far water, where the wash is the intended effect) and SPILL (they land on anything
else, where the wash would print the card's silhouette over a near object):

  camera      card%    behind%   spill%   spill objects
  lockfive    20.55     20.55     0.00    —
  gate        16.13     16.08     0.05    world background x5
  crossing    14.85     14.77     0.09    cliff_town_d x8
  weave        8.13      7.99     0.14    cliff_town_d x11, lf_riverbed_tail x2
  the other 11 cameras   0.00     0.00    — (0 of 9,216 rays cross the card)

Spill is 0.00-0.14% of frame.  The card washes the subject it was built to wash and
essentially nothing else, and the rebake list is exactly those four plates — the other
eleven are REFUSED WITH A NUMBER, not baked out of completeness.

THE DEPTH PASS IS UNAFFECTED BY CONSTRUCTION.  `cine_bake` deletes every haze/fog/smoke
object before the depth pass, so `depth.png` cannot move; a byte-identical depth map on all
four rebaked plates is the proof that no walk cell, body box or camera solve is implicated.

`restore` is exact here (unlike `dh_albedo_floor`'s): the change is one socket plus three
nodes, and the manifest records the socket's original value.
"""
import bpy, os, sys, json

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/dh_haze_east_depth.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
RESTORE = "restore" in argv
BASE = float(argv[argv.index("--base") + 1]) if "--base" in argv else 0.060
LO, HI = 1.70, 0.45              # multipliers at Z0 (gorge floor) and Z1 (rim)
Z0, Z1 = -16.0, 36.0             # the card's own world-Z extent
NODES = ("DH_HAZE_Z", "DH_HAZE_SEP", "DH_HAZE_RAMP")

MAT = "mat_haze_east"
OBJ = "fx_haze_east"
m = bpy.data.materials.get(MAT)
assert m is not None and m.use_nodes, "no %s" % MAT
ob = bpy.data.objects.get(OBJ)
assert ob is not None, "no %s" % OBJ
nt = m.node_tree
vs = [n for n in nt.nodes if n.type == 'VOLUME_SCATTER']
assert len(vs) == 1, "expected exactly one Volume Scatter in %s, found %d" % (MAT, len(vs))
vs = vs[0]

# --- GATE 1: THE MATERIAL MUST HAVE EXACTLY ONE USER ---------------------------
# mat_haze_east is shared with nothing, and that is what makes a material-scoped edit
# safe.  dh_albedo_floor paid for the general version of this lesson (a mesh-scoped lift
# would have repainted the lockhouse); the material-scoped version is: assert it.
users = [o.name for o in bpy.data.objects
         if o.type == 'MESH' and any(s.material is m for s in o.material_slots)]
assert users == [OBJ], "%s is worn by %s, not by %s alone" % (MAT, users, OBJ)

# --- GATE 2: THE CARD MUST NOT CAST SHADOW -------------------------------------
# DAYLOG 2026-08-01: a haze slab lying nearly parallel to the sun's rake stopped being
# atmosphere and became an opaque curtain, and the gate frame's entire south wall
# rendered black.  Raising the density is exactly the change that would make that
# catastrophic, so it is asserted here rather than assumed.
assert ob.visible_shadow is False, "%s must keep visible_shadow = False" % OBJ

def clear_ramp():
    for n in list(nt.nodes):
        if n.name in NODES:
            nt.nodes.remove(n)

if RESTORE:
    assert os.path.exists(MANIFEST), "no manifest at %s" % MANIFEST
    man = json.load(open(MANIFEST))
    clear_ramp()
    vs.inputs['Density'].default_value = man["before"]["density"]
    print("RESTORED %s density -> %.6f" % (MAT, man["before"]["density"]))
else:
    before = None if vs.inputs['Density'].is_linked else float(vs.inputs['Density'].default_value)
    if before is None and os.path.exists(MANIFEST):
        before = json.load(open(MANIFEST))["before"]["density"]      # idempotent re-run
    assert before is not None, "density is already driven and no manifest records the original"
    clear_ramp()
    n_geo = nt.nodes.new('ShaderNodeNewGeometry'); n_geo.name = NODES[0]
    n_sep = nt.nodes.new('ShaderNodeSeparateXYZ'); n_sep.name = NODES[1]
    n_map = nt.nodes.new('ShaderNodeMapRange');    n_map.name = NODES[2]
    n_geo.location = (vs.location.x - 620, vs.location.y - 200)
    n_sep.location = (vs.location.x - 440, vs.location.y - 200)
    n_map.location = (vs.location.x - 260, vs.location.y - 200)
    n_map.clamp = True
    n_map.inputs['From Min'].default_value = Z0
    n_map.inputs['From Max'].default_value = Z1
    n_map.inputs['To Min'].default_value = BASE * LO
    n_map.inputs['To Max'].default_value = BASE * HI
    nt.links.new(n_sep.inputs['Vector'], n_geo.outputs['Position'])
    nt.links.new(n_map.inputs['Value'], n_sep.outputs['Z'])
    nt.links.new(vs.inputs['Density'], n_map.outputs['Result'])
    json.dump({"material": MAT, "object": OBJ,
               "before": {"density": before},
               "after": {"ramp": "world Z", "z": [Z0, Z1],
                         "density": [BASE * LO, BASE * HI], "base": BASE,
                         "mult": [LO, HI]}},
              open(MANIFEST, "w"), indent=1)
    print("SET %s density = world-Z ramp  z %.1f -> %.1f  density %.5f -> %.5f"
          % (MAT, Z0, Z1, BASE * LO, BASE * HI))
    print("    was a constant %.6f  (x%.1f at the gorge floor, x%.1f at the rim)"
          % (before, BASE * LO / before, BASE * HI / before))

# --- GATE 3: THE FAMILY, COMPARED IN THE ONLY QUANTITY THAT IS COMPARABLE -------
# DENSITY IS NOT THE WASH.  What a camera sees is optical depth tau = density x the path
# it takes through the card, and these cards are 2.7 m to 44 m thick — so ranking them by
# density alone ranks nothing.  `fx_haze_south` at 0.0278 is 3x this card's OLD density
# and delivers a THINNER crosswise wash (2.7 m x 0.0278 = 0.075 vs 6 m x 0.0092 = 0.055),
# which is the whole reason the east card could sit an order of magnitude under its
# siblings' effect while looking like the middle of the family in a density listing.
from mathutils import Vector
def crosswise_tau(matname, dens):
    best = None
    for o in bpy.data.objects:
        if o.type != 'MESH' or not any(s.material and s.material.name == matname
                                       for s in o.material_slots):
            continue
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        dims = (max(p.x for p in pts) - min(p.x for p in pts),
                max(p.y for p in pts) - min(p.y for p in pts),
                max(p.z for p in pts) - min(p.z for p in pts))
        t = min(dims) * dens
        best = t if best is None else max(best, t)
    return best

peers = {}
for mm in bpy.data.materials:
    if not mm.use_nodes or mm is m:
        continue
    for n in mm.node_tree.nodes:
        if n.type in ('VOLUME_SCATTER', 'PRINCIPLED_VOLUME') and not n.inputs['Density'].is_linked:
            t = crosswise_tau(mm.name, float(n.inputs['Density'].default_value))
            if t is not None:
                peers[mm.name] = (float(n.inputs['Density'].default_value), t)
top = BASE * LO if not RESTORE else json.load(open(MANIFEST))["before"]["density"]
print("THE STATIC VOLUME FAMILY, density and CROSSWISE tau (= density x thinnest span):")
for k, (dd, tt) in sorted(peers.items(), key=lambda kv: -kv[1][1]):
    print("   %-18s density %.5f   tau %.4f   wash %4.1f%%" % (k, dd, tt, 100 * (1 - 2.718281828 ** -tt)))
mytau = crosswise_tau(MAT, top)
print("   %-18s density %.5f   tau %.4f   wash %4.1f%%   <- this card, at its densest rung"
      % (MAT, top, mytau, 100 * (1 - 2.718281828 ** -mytau)))
print("GATE: %s users = %s ; visible_shadow = %s" % (MAT, users, ob.visible_shadow))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("DRY RUN (pass `save` to write the master)")
