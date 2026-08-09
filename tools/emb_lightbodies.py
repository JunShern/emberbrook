"""emb_lightbodies.py — EMBERBROOK'S FOURTEEN LAMPS ARE SEALED INSIDE THEIR OWN OPAQUE
SHELLS, AND ITS HEARTLIGHT'S FLAME EMITS AT 0.24.  This unseals them.

    Blender -b tools/blends/<blend> --python-exit-code 1 \
        -P tools/emb_lightbodies.py -- [save] [revert save]
        [--lamps 1] [--flame 1.0]

======================= 1. THE LAMPS HAVE NEVER LIT THIS TOWN =====================

MEASURED, 2026-08-09, and it explains a doctrine entry that has stood unexplained for a
week.  CLAUDE.md's night-grade note records, as measured history: *"adjusting an existing
light has never moved this town; adding a new source always has (sky ladder, LAMP WATTAGE
TWICE, moon colour: inert or exhausted)"*.  Here is why lamp wattage was inert.

  * `emb_dress_lampglass` is an EMISSIVE Principled surface at strength 3.5 (emb_dress's
    `--lampglow`, swept), Alpha 1.0, no transmission — i.e. an OPAQUE box.
  * `emb_lamp_<id>_glass` is a 0.30 x 0.30 x 0.34 m closed box.
  * `KEYEMB_lamp_<id>` is a 680 W POINT light standing INSIDE it (lake-home: light at
    (38.011, 47.267, 4.690), glass z 4.500..4.840 on the same post).

So every shadow ray from the town toward a lamp terminates on that lamp's own housing.
Instrument: a 16 x 12 grid of shadow rays from the pad outside Lake's home toward
`KEYEMB_lamp_04_lake-home` — **165 of 192 blocked by `emb_lamp_04_lake-home_glass`
(85.9%)**, the remaining 27 by the cottage.  Not one sample reached the light.  What
lights Emberbrook at night is the emissive SHELL, and the fourteen 680 W lights inside
the shells contribute nothing at all.

THE CONTROL, at draft (1008x576 / 28 spp, the noise floor is 0.01% of frame): setting
`visible_shadow = False` on the fourteen glass shells and changing NOTHING else —

    shot      changed >4/255   L<=8/255        L<=24/255       clipped >=250
    homerow   65.31%           66.1% -> 37.9%  84.2% -> 59.7%  0.00% -> 0.00%
    square    71.54%           41.6% -> 19.6%  74.1% -> 52.5%  0.10% -> 0.10%

Half of the crushed frame goes away and NOTHING NEW CLIPS.  That is the red-team board's
item #2 ("Emberbrook's shadows go to absolute zero", crushed 6.8-15.6% of frame, 12 of 94
survivors about not being able to see the ground), and it is one flag.

WHY `visible_shadow` AND NOT A MATERIAL OR AN ENERGY.  This is what glass physically
does: it stays a visible, warm, emissive lantern to the camera and stops blocking the
light that is supposed to come from inside it.  The lamp's iron hood (`emb_lamp_*_cap`)
is a SEPARATE mesh and keeps casting, so a lamp still throws a shadow upward and still
pools its light downward.  **No light's energy, colour or position is touched** — the
ratified 680 W is what the town was designed around and it now actually reaches the town,
which is the doctrine's own "ADD a source" and not its "adjust one".

===================== 2. THE HEARTLIGHT'S FLAME IS BUILT AND INVISIBLE ============

The red-team board ranks "the Heartlight is a blown-out white box" #3 and attributes it
`lm_heartlight_cap` 67.9% + `lm_heartlight_flame` 11.5%.  **`lm_heartlight_flame` does
not exist in the dressed master** — it is the blockout's proxy, `kit_heartlight` kills it,
and the attribution came from `emb-cine/scene.glb`, which is exported from the GRAY
BLOCKOUT.  What the dressed master actually holds, censused:

    lm_heartlight_cap        2.00 x 2.00 x 0.20   z 2.45..2.65   emb_dress_town_stone
    lm_heartlight_plinth     2.30 x 2.30 x 0.95   z 1.50..2.45   emb_dress_town_stone
    emb_dress_heartflame0    0.64 x 0.56 x 1.37   z 2.38..3.75   EMIT 0.24
    emb_dress_heartflame1..4                      z 2.4..3.5     EMIT 0.44 / 0.76 / 1.28 / 2.08
    emb_dress_heartember0..6                      z 2.38..2.45   EMIT 0.24

So the flame IS built — five nested translucent shells and a seven-piece ember bed — and
it is not hidden.  It emits at **0.24 on the outer shell, the only one that draws the
silhouette**, against the lamp glass's 3.5.  Looked at, at native resolution
(`docs/qa/emberbrook-redteam/ev/heartlight-square.jpg`): there is no fire in the picture
at all, only a pale stone slab.

AND THE GATE IS WHY.  `kit_heartlight`'s own bar was *"ZERO CLIPPED PIXELS ON THE FLAME at
an eye-level standoff"* — **a bar with a ceiling and no floor.**  A flame you cannot see
passes it perfectly.  Same family as `blockout_material_coverage`: a one-sided report is
not a report.

`--flame` multiplies all five shells and the ember bed, preserving the swept RATIOS
between them (which are what make the fire read as a body rather than a lamp).  The level
is chosen by a RUNG TEST on `square`, not by taste, and the ceiling half of the old bar is
kept: it must not clip.

Idempotent by refusal: the pre-edit state is stored in scene['embl b'] and a second run
without `revert` aborts.  Nothing here moves a vertex.
"""
import bpy, sys, json

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAVE = "save" in argv
REVERT = "revert" in argv


def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d


LAMPS = int(opt("--lamps", "1"))
FLAME = float(opt("--flame", "1.0"))
PROP = "emblb"
sc = bpy.context.scene

GLASS = [o for o in sc.objects if o.type == 'MESH'
         and o.name.startswith("emb_lamp_") and o.name.endswith("_glass")]
FLAMEMATS = [m for m in bpy.data.materials
             if m.name.startswith(("emb_dress_heartflame", "emb_dress_heartember"))]


def emission_nodes(m):
    if not m.use_nodes:
        return []
    return [n for n in m.node_tree.nodes if n.type == 'EMISSION']


if REVERT:
    st = sc.get(PROP)
    assert st, "this blend carries no '%s' snapshot — nothing to revert" % PROP
    st = json.loads(st)
    for nm, v in st["glass"].items():
        o = sc.objects.get(nm)
        if o:
            o.visible_shadow = v
    for nm, v in st["emit"].items():
        m = bpy.data.materials.get(nm)
        if not m:
            continue
        for n in emission_nodes(m):
            n.inputs[1].default_value = v
    del sc[PROP]
    print("reverted %d glass shells and %d flame materials" % (len(st["glass"]), len(st["emit"])))
    if SAVE:
        bpy.ops.wm.save_mainfile()
        print("SAVED %s" % bpy.data.filepath)
    sys.exit(0)

assert not sc.get(PROP), (
    "this blend already carries the '%s' snapshot — emb_lightbodies is idempotent BY "
    "REFUSAL (a second --flame would multiply the multiplied). Run `-- revert save` "
    "first." % PROP)

assert GLASS, "no emb_lamp_*_glass meshes in this blend — is this an Emberbrook tier?"

snap = dict(glass={o.name: o.visible_shadow for o in GLASS},
            emit={m.name: (emission_nodes(m)[0].inputs[1].default_value
                           if emission_nodes(m) else None)
                  for m in FLAMEMATS})
snap["emit"] = {k: v for k, v in snap["emit"].items() if v is not None}
sc[PROP] = json.dumps(snap)

n = 0
if LAMPS:
    for o in GLASS:
        o.visible_shadow = False
        n += 1
print("LAMPS: %d glass shells no longer cast — the 680 W point light inside each one now "
      "reaches the town for the first time (nothing else about any light is touched)" % n)

if FLAME != 1.0:
    for m in FLAMEMATS:
        for nd in emission_nodes(m):
            old = nd.inputs[1].default_value
            nd.inputs[1].default_value = old * FLAME
            print("  %-28s emission %.3f -> %.3f" % (m.name, old, old * FLAME))
else:
    print("FLAME: unchanged (--flame 1.0); the outer shell stays at %s"
          % (["%.2f" % emission_nodes(m)[0].inputs[1].default_value
              for m in FLAMEMATS if m.name.endswith("flame0")] or ["?"])[0])

if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED %s" % bpy.data.filepath)
else:
    print("(dry — pass `save` to write the blend)")
