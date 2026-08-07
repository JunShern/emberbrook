"""pit_lantern.py — THE BLACK PIT UNDER THE QUAY DECKS, GIVEN A LANTERN.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/pit_lantern.py -- [save] [restore] [--energy 680]

WHAT THE PIT IS.  Red-team 20260806-2 checklist, quay-west item 17 FAILING (bbox
0.50,0.65..0.62,0.85): "the lower gorge area is completely black and devoid of any
water shaders" — but the render-faithful ray census (hide_render + volume-only
excluded) finds NO water there at all: the pixels are `wf_ground` rock at
z 6.5..12.1 and `qm_deck_frame` timber in the shadow of the decks above.  The
verdict's "no water" premise is wrong; the crush-black is real.  The class fix is
the DAYLOG night doctrine: ADDING a source is what has moved this town's dark
frames; adjusting existing ones has not.

THE FIX, in the town's own vocabulary: one hanging lantern of the shipped
`lantern_N` prop family (192-vert mesh clone + hanger, mat_iron +
mat_lantern_glass) under the deck frame over the pit, paired with the shipped
lantern light class (`KEYQ_lantern_*`: POINT, colour 1.0/0.58/0.24) at reduced
energy — the pit is enclosed, and the sibling class is tuned for open deck.  No
authorless glow: the prop and the light ship together (cine_bake's own rule).

Placement is MEASURED FROM THE COMPLAINED PIXELS, not from a guessed box: the
first siting (a down-ray census over x 45..54) hung the lantern 7 m east of the
region and moved the bbox median 5.3 -> 4.9/255, i.e. NOT AT ALL — a paid
lesson in auditing geometry WHERE IT LANDS.  The quay-west camera's own rays
through the FAILING bbox (0.50,0.65..0.62,0.85) land on: `wf_ground`'s pit face
x 41.3..42.8 y 12.7..17.9 z 6.7..12.1 (normal -X, facing camera),
`wv_hut_weave-north_0`'s north wall y 17.1..19.7 (normal -Y), and two dark
`veg_wf_rimclump` crowns between them.  So the lantern hangs INSIDE that bay at
the measured anchor (41.5, 15.2), 0.45 m under whatever deck member an up-ray
finds there — west of the rock face and south of the hut wall, so its light
lands on both.

Idempotent: re-running replaces its own objects.  `restore` removes them.
"""
import bpy, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
RESTORE = "restore" in argv
ENERGY = float(argv[argv.index("--energy") + 1]) if "--energy" in argv else 300.0

PROP = "KEYQ_pit_lantern_prop"
HANG = "KEYQ_pit_lantern_hanger"
LIGHT = "KEYQ_pit_lantern_light"

# remove any previous run (also the restore path)
for nm in (PROP, HANG, LIGHT):
    o = bpy.data.objects.get(nm)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)

if not RESTORE:
    dg = bpy.context.evaluated_depsgraph_get()
    scene = bpy.context.scene
    # ---- the measured anchor (see docstring): under the deck frame, west of the
    # rock face (x >= 41.3) and south of the hut wall (y >= 17.1), ABOVE the
    # rock overhang at z 8.77 that a lower anchor found first.
    cx, cy = 41.2, 13.8
    ok, loc, nrm, idx, obj, mw = scene.ray_cast(dg, Vector((cx, cy, 9.5)), Vector((0, 0, 1)))
    assert ok and obj.name.startswith(("qm_deck", "qm_plank", "qm_ground", "qm_cookhouse")), \
        "expected a deck/building member above the anchor, found %s" % (obj.name if ok else None)
    dz = loc.z
    okf, locf, *_ = scene.ray_cast(dg, Vector((cx, cy, 9.5)), Vector((0, 0, -1)))
    fz = locf.z if okf else float("nan")
    hang_z = dz - 0.45
    print("PIT anchor (%.1f, %.1f): overhead %s at z %.2f, pit floor z %.2f, "
          "lantern at z %.2f" % (cx, cy, obj.name, dz, fz, hang_z))

    src = bpy.data.objects.get("lantern_3")
    hsrc = bpy.data.objects.get("lantern_3_hanger")
    assert src is not None and hsrc is not None, "lantern_3(+hanger) prop family missing"

    def clone(source, name, dx, dy, dzz):
        ob = source.copy()          # shares mesh datablock deliberately: same prop
        ob.name = name
        ob.location = source.location + Vector((dx, dy, dzz))
        bpy.context.scene.collection.objects.link(ob)
        return ob

    sb = [src.matrix_world @ Vector(c) for c in src.bound_box]
    scx = (min(v.x for v in sb) + max(v.x for v in sb)) / 2
    scy = (min(v.y for v in sb) + max(v.y for v in sb)) / 2
    sctop = max(v.z for v in sb)
    prop = clone(src, PROP, cx - scx, cy - scy, hang_z - sctop)
    hb = [hsrc.matrix_world @ Vector(c) for c in hsrc.bound_box]
    clone(hsrc, HANG, cx - (min(v.x for v in hb) + max(v.x for v in hb)) / 2,
          cy - (min(v.y for v in hb) + max(v.y for v in hb)) / 2,
          hang_z - sctop)           # hanger keeps its offset above the body
    ld = bpy.data.lights.new(LIGHT, type='POINT')
    ld.energy = ENERGY
    ld.color = (1.0, 0.58, 0.24)    # the shipped lantern class colour
    ld.shadow_soft_size = 0.25
    lob = bpy.data.objects.new(LIGHT, ld)
    lob.location = (cx, cy, hang_z - 0.25)
    bpy.context.scene.collection.objects.link(lob)
    print("BUILT %s + %s + %s (POINT %.0f W at %.1f, %.1f, %.2f)"
          % (PROP, HANG, LIGHT, ENERGY, cx, cy, hang_z - 0.25))
else:
    print("RESTORED: pit lantern objects removed")

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED BLEND %s" % bpy.data.filepath)
