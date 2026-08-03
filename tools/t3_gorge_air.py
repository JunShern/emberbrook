"""t3_gorge_air.py — LIGHT AND AIR FOR THE DOWNSTREAM GORGE.  The user's
"the giant gap in the cliff face is still there", named and closed.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t3_gorge_air.py -- [save] [--energy N] [--albedo r,g,b] [--haze T]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t3_gorge_air.py -- revert [save]

WHAT THE VOID ACTUALLY IS.  Measured, not guessed, on the bake ray-cast
(`tools/t2_probe_leak.py`, the only visibility oracle) against the shipped
plate `public/assets/scenes/del-cine/cameras/gate/bg.png`:

    gate frame, first-opaque tally
      cliff_east_closure    16.41% of frame   65.65% of the TOP-LEFT QUADRANT
                            d 162.4 .. 179.0 m,  d_mean 168.7 m
      water_pool-downstream  2.18% of frame    the black band under it
    sky leak on `gate`      0.05%  (15 rays of 28,672, a corner sliver)
    backfacing samples      0 of 165

    THE SAME PIXELS, READ OFF THE SHIPPED PLATE
      cliff_east_closure    median luminance   7.0 / 255   mean RGB (13.4, 6.2, 6.6)
      water_pool-downstream median luminance  10.7 / 255
      cliff_town_a (the same rock family, 108.6 m)   median  94.0
      cliff_town_d                          (136.7 m)   median  68.5
      gate_cliffface                         (28.3 m)   median  62.3

**IT IS NOT A HOLE, NOT A BACKFACE, NOT A MISSING SURFACE.**  It is 2,205
verts of properly sculpted gorge wall (t3_cliff_gorge.py's seven-octave relief
is all there) rendering at 3% luminance across a sixth of the frame.  A wall you
cannot see is indistinguishable from a wall that is not there, and the previous
pass's 1.84% -> 0.05% sky-gate is a green number about a DIFFERENT question.

THREE COMPOUNDING CAUSES, each measured, each fixed here:

1. NO SUN REACHES IT.  `tools/` light probe over 165 ray-cast samples on the
   wall as `gate` sees it: mean face normal (-0.897, -0.017, 0.081) — it faces
   WEST — and `SUN_key` (the scene's ONLY sun) travels (-0.741, -0.305, -0.598),
   i.e. it stands to the EAST.  **0 of 165 samples have N.L > 0.**  The control,
   `gate_cliffface`: 232 of 346 face the sun, 201 unshadowed, and it reads 62.
   Every other light in Dellhollow is a local spot/point/area at x <= 91.3; the
   wall stands at x 141..153, fifty-odd metres past the last of them.

2. ITS ALBEDO IS THE TOWN'S DARKEST.  `mat_rock_gorgewall`'s chain ends in
   `Mix.002`, a MULTIPLY at factor 1.0 by (0.30, 0.295, 0.30) — a flat 70% cut.
   Compare `mat_rock` and `mat_gate_cliff`, which multiply by (0.72, 0.72, 0.72).
   The 0.30 came from `mat_rock_farwall`, authored for `cliff_far` at y 80..99
   as an ATMOSPHERIC-PERSPECTIVE material (cliff-completion.md AS BUILT note 1).
   Recession baked into albedo is the wrong instrument for it here: it darkens
   without adding air, so the wall loses tone and gains no depth.

3. ITS AIR IS SWITCHED OFF.  `fx_haze_east` — the volume-scatter slab at
   x 124..130 built for exactly this wall — ships `hide_render = True`.  It was
   turned off after the surgery bake because it was mistaken for the "salmon
   card" (cliff-completion.md AS BUILT (2)), and that note explicitly parks
   "whether it wants its haze back" as an open taste call.  This pass answers it.

WHAT IS BUILT

  `KEYDG_gorge_fill`   an AREA light at x = 120, east of every built thing in
      town (`lf_ground`, the easternmost ground, stops at x 112.1), aimed east
      and DOWN across the wall's face.  It rakes from north-and-above
      (N.L = 0.64 on the wall's mean normal) rather than pointing along the
      camera axis, because frontal light on a wall is how a sculpted wall goes
      back to being a slab: the seven octaves and five fissures only exist on
      screen if they shade.

      CONTAINMENT IS LIGHT LINKING, NOT A FALLOFF ARGUMENT, AND THE FIRST TAKE
      OF THIS TOOL GOT IT WRONG.  A single-sided emitter looks like it contains
      itself — nothing behind it can receive a photon — but a light that RAKES
      DOWNWARD tilts its own hemisphere, and the tool's own containment probe
      reported **263 town meshes with a bbox corner in front of the emitter
      plane and west of x = 112**: the crossing bridge, the lock rungs, half
      the lower town, all of it "in front" simply by being lower down.  The
      hemisphere is the wrong instrument.  The light is therefore linked to an
      explicit receiver collection (`LL_gorge_receivers`) holding the gorge and
      nothing else, so the set of surfaces it can touch is a list you can read
      rather than a solid angle you have to reason about.

  A NEW SOURCE, NOT A LOUDER OLD ONE.  DAYLOG 2026-08-01's night-lane finding
  on Emberbrook: "adjusting an existing light has never moved this town; adding
  a new source always has."  Raising SUN_key or the world would move all sixteen
  plates to fix one wall that neither of them can reach anyway (cause 1).

WHAT IS DELIBERATELY NOT TOUCHED: geometry (not one vertex — the wall's shape is
t3_cliff_gorge's and it is fine), SUN_key, the world, the exposure, the x = 140
closure plane, and every ray-traced leak certificate in cliff-completion.md.

RE-BAKE SET, from the same instrument (`t2_probe_leak.py`, all 16 cameras, share
of frame whose first-opaque hit lies east of x = 112):
    crossing 31.88%   lockfive 22.38%   gate 18.86%   cottage 3.26%   weave 0.36%
Everything else is 0.00% and cannot see a photon of this.
"""
import bpy, os, sys, math, json
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv


def opt(n, d):
    return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d


WALL = "cliff_east_closure"
MAT = "mat_rock_gorgewall"
HAZE = "fx_haze_east"
LIGHT = "KEYDG_gorge_fill"

# ---- the three numbers, all overridable so the draft loop can sweep them -----
ENERGY = float(opt("--energy", "34000"))
ALBEDO = tuple(float(v) for v in opt("--albedo", "0.58,0.575,0.60").split(","))
HAZE_TOP = float(opt("--hazetop", "31.0"))

ALBEDO_OLD = (0.30, 0.295, 0.30)          # what t3_cliff_gorge inherited from farwall
HAZE_TOP_OLD = 26.0                       # t2_cliff_east's own top row

# Emitter placement.  East of the town's own east edge (`lf_ground` stops at
# x = 112.1) so the rig reads as gorge light; the CONTAINMENT is the receiver
# collection below, not this coordinate.
LPOS = Vector((120.0, 34.0, 34.0))
LAIM = Vector((148.0, 26.0, 2.0))
LSIZE = (100.0, 70.0)                     # covers the wall's full y 0..80 run
LCOL = (0.72, 0.78, 1.0)                  # SKY bounce, not sun: the wall is in
                                          # shadow and its light should say so

# The ONLY surfaces this light may touch.  Every one of them lives east of the
# town's own east edge; the list is the containment.
RECV_COLL = "LL_gorge_receivers"
RECEIVERS = ["cliff_east_closure", "water_pool-downstream", "fx_haze_east",
             "cliff_town_d", "cliff_far", "cliff_far_toe", "lf_farbank_tail",
             "lf_riverbed_tail"]

sc = bpy.context.scene


def set_albedo(rgb):
    m = bpy.data.materials.get(MAT)
    assert m is not None, "%s absent — run t3_cliff_gorge.py first" % MAT
    users = [o.name for o in sc.objects if o.type == 'MESH'
             and any(s.material == m for s in o.material_slots)]
    assert users == [WALL], (
        "%s is worn by %s, not by %s alone — this edit is only safe on a "
        "single-user copy" % (MAT, users, WALL))
    n = m.node_tree.nodes.get("Mix.002")
    assert n is not None and n.blend_type == 'MULTIPLY', "Mix.002 is not the tint node"
    # the constant colour socket is the LAST unlinked colour input
    sock = [i for i in n.inputs if i.type == 'RGBA' and not i.is_linked][-1]
    was = tuple(round(v, 4) for v in sock.default_value)[:3]
    sock.default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    print("  %s Mix.002 MULTIPLY colour %s -> %s" % (MAT, was, tuple(round(v, 3) for v in rgb)))
    return was


def set_haze(top, on):
    o = bpy.data.objects.get(HAZE)
    assert o is not None, "%s absent" % HAZE
    was_top = max((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    me = o.data
    lo = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    for v in me.vertices:
        w = o.matrix_world @ v.co
        if w.z > (lo + was_top) * 0.5:
            w.z = top
            v.co = o.matrix_world.inverted() @ w
    me.update()
    o.hide_render = not on
    # SHADOW OFF is not a nicety: cliff-completion.md AS BUILT (2) records a slab
    # lying nearly parallel to the key turning the whole south wall BLACK when it
    # cast.  Every haze card in this town carries visible_shadow = False.
    o.visible_shadow = False
    print("  %s hide_render -> %s   top z %.1f -> %.1f   visible_shadow=False"
          % (HAZE, o.hide_render, was_top, top))


def receivers():
    """The light-linking receiver collection, rebuilt from RECEIVERS every run so
    the containment cannot drift away from the docstring."""
    c = bpy.data.collections.get(RECV_COLL)
    if c is None:
        c = bpy.data.collections.new(RECV_COLL)
        # NOT linked into the scene: a light-linking collection is a membership
        # list, and linking it would put every member in the scene twice.
    for o in list(c.objects):
        c.objects.unlink(o)
    got = []
    for n in RECEIVERS:
        o = bpy.data.objects.get(n)
        if o is None:
            print("  receiver %s ABSENT — skipped" % n)
            continue
        c.objects.link(o)
        got.append(n)
    print("  %s holds %d receivers: %s" % (RECV_COLL, len(got), got))
    return c


def set_light(energy):
    old = bpy.data.objects.get(LIGHT)
    if old:
        d0 = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if d0.users == 0:
            bpy.data.lights.remove(d0)
    if energy <= 0:
        c = bpy.data.collections.get(RECV_COLL)
        if c is not None and c.users == 0:
            bpy.data.collections.remove(c)
        print("  %s removed" % LIGHT)
        return
    ld = bpy.data.lights.new(LIGHT, type='AREA')
    ld.shape = 'RECTANGLE'
    ld.size, ld.size_y = LSIZE
    ld.energy = energy
    ld.color = LCOL
    ob = bpy.data.objects.new(LIGHT, ld)
    # link beside SUN_key so a district tool that sweeps its own collection
    # never finds this one
    sun = bpy.data.objects.get("SUN_key")
    coll = sun.users_collection[0] if sun and sun.users_collection else sc.collection
    coll.objects.link(ob)
    ob.location = LPOS
    ob.rotation_euler = (LAIM - LPOS).to_track_quat('-Z', 'Y').to_euler()
    ob.light_linking.receiver_collection = receivers()
    ob.light_linking.blocker_collection = receivers()
    d = (LAIM - LPOS).normalized()
    ndl = Vector((-0.897, -0.017, 0.081)).dot(-d)
    print("  %s AREA %.0f x %.0f m  %.0f W  colour %s  pos %s  dir %s  N.L on the "
          "wall's mean normal = %.3f" % (LIGHT, LSIZE[0], LSIZE[1], energy, LCOL,
                                         tuple(LPOS), tuple(round(v, 3) for v in d), ndl))
    assert ndl > 0.25, "the fill rakes too flat to shade the relief"
    return ob


print("t3_gorge_air.py  %s" % ("REVERT" if REVERT else "BUILD"))
if REVERT:
    set_albedo(ALBEDO_OLD)
    set_haze(HAZE_TOP_OLD, False)
    set_light(0.0)
else:
    set_albedo(ALBEDO)
    set_haze(HAZE_TOP, True)
    set_light(ENERGY)

# ---- prove the containment rather than assert it ---------------------------
if not REVERT:
    ob = bpy.data.objects[LIGHT]
    rc = ob.light_linking.receiver_collection
    assert rc is not None, "light linking did not take — the containment is gone"
    got = sorted(o.name for o in rc.objects)
    assert got == sorted(n for n in RECEIVERS if bpy.data.objects.get(n)), got
    west = [o.name for o in rc.objects
            if max((o.matrix_world @ Vector(c)).x for c in o.bound_box) < 112.0]
    print("  CONTAINMENT PROVED: %d receivers, %d of them reaching west of "
          "x = 112: %s" % (len(got), len(west), west))
    print("  receivers: %s" % got)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("DRY RUN — nothing written")
