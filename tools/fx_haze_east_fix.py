"""fx_haze_east_fix.py — the constant salmon card in the east-facing frames.

  Blender -b tools/blends/dellhollow-master.blend -P tools/fx_haze_east_fix.py \
      --python-exit-code 1 -- save          # hide it
  Blender -b tools/blends/dellhollow-master.blend -P tools/fx_haze_east_fix.py \
      --python-exit-code 1 -- save restore  # put it back

WHAT IT IS, identified by raying the solved `crossing` camera through the seam
surgeon's flagged region (ndc x -0.72..-0.33, y 0.52..1.00 of
docs/qa/districts/yaw195_crossing.png — a literally constant card, RGB ~155,91,61,
per-pixel std 0.41, hard vertical edges, ~4.3% of that frame):

  `fx_haze_east` — an 8-vertex slab, x 124..130  y -10..56  z -16..26, on
  `mat_haze_east`, in the `CONTEXT` collection.

IT IS NOT DEAD-ERA BACKING AND ITS MATERIAL IS NOT BROKEN, which were the two
standing suspicions.  `mat_haze_east` is a proper Volume Scatter (colour
0.48/0.50/0.60, density 0.0092) with NO surface shader, built exactly like its four
siblings `mat_haze_far` / `_mid` / `_rim` / `_south`.  Everything else the rays find
in that region is sky (88.7% once the volume is marched through), `water_pool-
downstream`, and three walls on `mat_rock_farwall` — and `mat_rock_farwall` carries
four image textures, a noise mix and a normal map, so it cannot produce a card with
a per-pixel std of 0.41.  A uniform-density volume box CAN: it adds a CONSTANT
scattering term inside its own silhouette, which is why the edges are hard and
vertical (they are the slab's own bounds) and why the fill has no variation at all.

WHY IT HAS NEVER BEEN SEEN.  The slab is 6 m thick and 66 m long.  Every camera
before tonight looked INTO the cliff, crossing the 6 m dimension — optical depth
~0.055, invisible.  Tonight's five re-aims are the first ever pointed east, down the
66 m LENGTH, where the same density integrates to something the eye reads as an
opaque card sitting in front of a dark cliff.  Measured on the current re-solved
crossing camera it still adds +3/+7/+9 RGB inside the flagged box; at yaw 195 the
path was far longer and it dominated.

THE FIX IS `hide_render`, NOT A DELETION AND NOT A MATERIAL CHANGE.  The slab is
sound geometry with a sound material that is simply the wrong size for a sightline
that did not exist when it was authored; it contributes to ZERO of the 17 shipped
plates (the surgeon's own measurement), so hiding it costs no frame anything and
removes the artefact from all five new east-facing cameras.  Re-sizing it so its
bounds leave frame is the better long-term answer and belongs with whoever owns
CONTEXT — recorded, not attempted here at the end of a shift.

Reversible in one command (`-- save restore`), and the object, its mesh and its
material are untouched either way.
"""
import bpy, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
RESTORE = "restore" in argv
NAME = "fx_haze_east"

o = bpy.data.objects.get(NAME)
assert o is not None, "%s is not in this master" % NAME
before = o.hide_render
o.hide_render = not RESTORE
print("%s  hide_render %s -> %s   (%d verts, mats %s, collections %s)"
      % (NAME, before, o.hide_render, len(o.data.vertices),
         [m.name if m else None for m in o.data.materials],
         [c.name for c in o.users_collection]))

# It is CONTEXT scenery: it must not be, and is not, part of the walk contract.
assert not NAME.startswith(("walk_", "bar_")), "refusing to touch walk topology"
touch = [c.name for c in o.users_collection]
print("collections: %s  (CONTEXT scenery — no walk_/bar_ mesh is touched)" % touch)

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry run — pass `-- save`)")
