"""t3_rock_projection.py — THE CLIFF UV-STRETCH FIX.  One cause, one line, four
materials.  Task #35, the user's "no tiled-looking repeats, no UV stretch" rule.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t3_rock_projection.py -- [save]
  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P tools/t3_rock_projection.py -- revert [save]

THE FINDING, AND IT IS NOT WHAT THE NAME SAYS.  `scene_redteam` run
20260731-dellhollow2 raised "severe vertical texture stretching" on the cliff
face of **loop-stairs, lockhead and cottage** (six findings, sev1-2), and the
user's own ruling names the same thing.  On those three frames the cliff is one
object — `cliff_town_a`, 21-24% of frame — and it wears `mat_rock_townwall`.

MEASURED, not reasoned.  Every rock material in Dellhollow already runs its
Image Textures in **BOX projection** (blend 0.35), which picks one of three
planar projections from the shading normal and therefore cannot stretch on its
own.  What is different about `mat_rock_townwall` is one number:

    mat_rock_townwall   Mapping rotation X = 90 deg     <- only this one
    mat_gate_cliff / mat_shelf_cliff / mat_qm_cliff / mat_rock / mat_rock_far
                        Mapping rotation   = 0

`tools/t2_cliff_south.py` added that rotation to cure a DIFFERENT defect (see
its AS BUILT note 2 in docs/plans/cliff-completion.md: a 2D image fed a 3D
vector uses only X and Y, so a flat-projected wall in the x-z plane got no
height variation).  BOX projection had made that rotation unnecessary — and
actively harmful, because **the Mapping node rotates the COORDINATE and not the
NORMAL.**  The box's axis is chosen from the untransformed normal; the
coordinates handed to it have already been spun 90 degrees about X.  On a wall
facing -Y the normal selects the Y plane, and the Y plane reads the rotated
vector's (X, Z) = (world x, world **y**) — the wall's run and its 0.35-5.9 m of
depth relief.  **The texture therefore does not vary with height at all.**  That
is the vertical streak, exactly, and it is the same failure the rotation was
added to fix, re-entered through the other door.

PROVED BY RENDER, four probes at the shipped camera and grade, 1344x768/40 spp:
    docs/qa/districts/t3tex105_lockhead.png   rot 90, scale 1.05 (as shipped)
                                              — hard vertical combing
    docs/qa/districts/t3tex030_lockhead.png   rot 90, scale 0.30
                                              — the streaks get BIGGER: this
                                                refutes "minification aliasing"
    docs/qa/districts/t3rot0_lockhead.png     rot  0, scale 1.05
                                              — streak GONE, tile repeat visible
    docs/qa/districts/t3rot0s55_lockhead.png  rot  0, scale 0.55  <- shipped here
                                              — streak gone, repeat gone

WHAT THIS TOOL CHANGES.  Two numbers on four materials, and nothing else:

  1. `mat_rock_townwall` Mapping rotation 90 deg -> 0.  This is the defect.
  2. Mapping scale 1.05 -> 0.55 on `mat_rock_townwall`, `mat_gate_cliff`,
     `mat_shelf_cliff`, `mat_qm_cliff`: a 0.95 m rock tile on a face read at
     28-60 m is a visible chequer, which is the user's second rule ("no
     tiled-looking repeats").  0.55 is a 1.82 m tile.  The value is a taste
     call made against the four probes above and is parked on the board as such.

NO GEOMETRY MOVES.  Not one vertex, not one object, no new material datablocks.
`master_walk_qa` and `geometry_audit` are bit-identical by construction; the
gate that matters is the plate bake.

DERIVED REBAKE LIST (any camera that sees any of the four materials, from
tools/t2_probe_leak.py's per-object screen tally on the pre-change master):
    loop-stairs 33.45%  lockhead 26.70%  gate 25.32%  cottage 19.29%
    shelf-west 12.78%   quay-west 11.23% weave 11.14% shelf-east 6.17%
    deep-stairs 1.20%   lockfive 0.04%
"""
import bpy, os, sys, math, json

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = os.path.join(ROOT, "tools/blends/districts/t3_rock_projection.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv

# material -> (rotation_x_deg, mapping_scale) AFTER  /  BEFORE
AFTER = {
    "mat_rock_townwall": (0.0, 0.55),
    "mat_gate_cliff":    (0.0, 0.55),
    "mat_shelf_cliff":   (0.0, 0.55),
    "mat_qm_cliff":      (0.0, 0.55),
}
BEFORE = {
    "mat_rock_townwall": (90.0, 1.05),
    "mat_gate_cliff":    (0.0, 1.05),
    "mat_shelf_cliff":   (0.0, 1.05),
    "mat_qm_cliff":      (0.0, 1.05),
}

WANT = BEFORE if REVERT else AFTER
rows = []
for mn, (rx, sc) in sorted(WANT.items()):
    m = bpy.data.materials.get(mn)
    if m is None or not m.use_nodes:
        print("MISSING %s — skipped" % mn)
        continue
    maps = [n for n in m.node_tree.nodes if n.type == 'MAPPING']
    if len(maps) != 1:
        print("REFUSED %s: expected exactly 1 Mapping node, found %d" % (mn, len(maps)))
        sys.exit(1)
    n = maps[0]
    orx = tuple(round(math.degrees(v), 3) for v in n.inputs['Rotation'].default_value)
    osc = tuple(round(v, 4) for v in n.inputs['Scale'].default_value)
    n.inputs['Rotation'].default_value = (math.radians(rx), 0.0, 0.0)
    n.inputs['Scale'].default_value = (sc, sc, sc)
    # the box projection is what makes the zero rotation correct; assert it.
    proj = sorted(set(t.projection for t in m.node_tree.nodes if t.type == 'TEX_IMAGE'))
    if proj != ['BOX']:
        print("REFUSED %s: Image Textures are %s, not BOX — the zero rotation is "
              "only correct under box projection" % (mn, proj))
        sys.exit(1)
    rows.append(dict(material=mn, rot_deg_before=list(orx), rot_deg_after=[rx, 0.0, 0.0],
                     scale_before=list(osc), scale_after=[sc] * 3,
                     tile_m_before=round(1.0 / osc[0], 3), tile_m_after=round(1.0 / sc, 3),
                     projection="BOX"))
    print("%-20s rot %-22s -> (%.1f, 0, 0)   scale %-8s -> %.3f  (tile %.2f m -> %.2f m)"
          % (mn, orx, rx, osc[0], sc, 1.0 / osc[0], 1.0 / sc))

users = {}
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    for s in o.material_slots:
        if s.material and s.material.name in WANT:
            users.setdefault(s.material.name, []).append(o.name)
for mn in sorted(users):
    print("   %-20s worn by %d objects: %s" % (mn, len(users[mn]), ", ".join(sorted(users[mn]))))

if not REVERT:
    json.dump(dict(
        _doc=("GENERATED by tools/t3_rock_projection.py — the cliff UV-stretch fix. "
              "The Mapping node rotates the coordinate but not the normal, so a "
              "90-degree rotation desynchronises BOX projection's axis choice from "
              "the vector it is handed and the texture stops varying with height."),
        generator="tools/t3_rock_projection.py",
        plan="docs/plans/cliff-completion.md",
        finding="scene_redteam run-20260731-dellhollow2: loop-stairs/lockhead/cottage "
                "'severe vertical texture stretching' (6 findings, sev1-2)",
        probes=["docs/qa/districts/t3tex105_lockhead.png",
                "docs/qa/districts/t3tex030_lockhead.png",
                "docs/qa/districts/t3rot0_lockhead.png",
                "docs/qa/districts/t3rot0s55_lockhead.png",
                "docs/qa/districts/t3fixA_loop-stairs.png",
                "docs/qa/districts/t3fixA_cottage.png",
                "docs/qa/districts/t3fixB_shelf-west.png"],
        materials=rows, users={k: sorted(v) for k, v in users.items()},
        rebake=["loop-stairs", "lockhead", "gate", "cottage", "shelf-west",
                "quay-west", "weave", "shelf-east", "deep-stairs", "lockfive"],
    ), open(MANIFEST, "w"), indent=1)
    print("manifest -> %s" % os.path.relpath(MANIFEST, ROOT))

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the master)")
