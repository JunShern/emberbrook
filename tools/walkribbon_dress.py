"""walkribbon_dress.py — THE WHITE POLYGON PLANE IN FIVE PLATES, NAMED AND DRESSED.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/walkribbon_dress.py -- [save] [restore]

WHAT THE PLANE IS.  Red-team 20260806-2 checklist, loop-stairs frame-edge FAILING:
"an untextured white polygon plane at the bottom-left edge breaks the picture and
reads as unfinished world geometry" (bbox 0,730..265,970/1000) — plus lockhead's
three naive "untextured white strip/plank" findings.  Named on a render-faithful
ray census (hide_render + volume-only excluded from the depsgraph first — the
gate lane's own instrument note):

    walk_e_market-stalls__lockhead_l0   8 verts, m_wood, z 14.02..14.07
        visible in FIVE frames: loop-stairs 40px, crossing 61px, lockhead 19px,
        weave 4px, quay-west 4px (of 2304 at 64x36)

It is the market->lockhead walk corridor ribbon.  The merge custodian render-hid
118 blockout ribbons BY MAP PARCEL BOUNDS and qm_build.py 0b did its own parcel;
this ribbon SPANS the parcel seam (bbox x 59.75..68.57 crosses qm's x-max 63.60),
so its centre fell in neither sweep and it renders — bare m_wood (0.45,0.36,0.26)
reads blown white under the golden key.

WHY A MATERIAL SWAP AND NOT hide_render.  A 24x8 down-ray census over its
footprint: 172/192 samples are directly over qm_paving / lk_surface / qm_planking
at 0.0-0.2 m, but 20/192 (the south edge row, x 64.3..68.3 y 12.7) have NOTHING
beneath — the ribbon itself is the only surface over the gorge lip there.  Hiding
it would open a hole; dressing it in the market's own sett paving
(`mat_qm_paving`, the material both floors under it already wear) makes it read
as the paved corridor it is.  Geometry untouched: no walk gate is owed
(hide_render/material are not exported walk semantics; the GLB keeps the mesh).

Idempotent; `restore` puts m_wood back.  Proof is printed from the artifact:
the object's material slot list after the edit.
"""
import bpy, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
RESTORE = "restore" in argv

NAME = "walk_e_market-stalls__lockhead_l0"
WANT = "m_wood" if RESTORE else "mat_qm_paving"

o = bpy.data.objects.get(NAME)
assert o is not None and o.type == 'MESH', "%s is not in this master" % NAME
m = bpy.data.materials.get(WANT)
assert m is not None, "%s is not in this master" % WANT
assert len(o.data.materials) == 1, \
    "expected exactly one slot on %s, found %d" % (NAME, len(o.data.materials))

before = o.data.materials[0].name if o.data.materials[0] else None
o.data.materials[0] = m
print("%s  material %s -> %s   (verts %d, hide_render %s)"
      % (NAME, before, o.data.materials[0].name, len(o.data.vertices), o.hide_render))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED BLEND %s" % bpy.data.filepath)
