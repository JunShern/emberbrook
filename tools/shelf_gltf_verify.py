"""shelf_gltf_verify.py — prove the Shelf tier survives the glTF round trip.

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/shelf_gltf_verify.py

Step 1 exports every `shelf_` / `veg_shelf_` object to a scratch GLB.  Step 2
re-imports it into an EMPTY blend — so nothing in the authoring file can prop the
result up — and reports what actually arrived.

THE GATE (MIGRATION.md, 2026-07-29).  516 of 1587 townwalk primitives export
WHITE because the kit's ramps, ropes and bunting are noise/ramp node trees, and a
procedural tree does not cross glTF at all.  It renders perfectly in Blender.
The authoring render is not evidence; only a re-import is.

This district was built to two rules that are supposed to make that impossible,
and this script is what makes "supposed to" into a number:

  * every SURFACE is `derive()`d from one of the town's textured materials and
    re-tinted through a MULTIPLY mix, which is exactly baseColorTexture x
    baseColorFactor and is the only tinting form that survives;
  * every CLOTH (bunting, awnings) bakes its weave and sun-fade into VERTEX
    COLOURS read by a Color Attribute node, which is COLOR_0 and survives
    byte-for-byte — instead of the noise x fade tree that would export white.

So each object is checked for what its own kind is supposed to deliver, and
"lost it" is reported as the thing it actually looks like from outside: a
baseColorTexture with no pixels, a COLOR_0 that came back flat white, or a
material that is default-white with nothing painting it.
"""
import bpy, os, sys, numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
SCRATCH = os.path.join(ROOT, "tools", "blends", "districts", "_shelf_roundtrip.glb")
PREFIX = ("shelf_", "veg_shelf_")
# the objects whose look is carried by COLOR_0 rather than by a texture.
# `shelf_bunting_lines` is NOT one of them — it is the rope the cloth hangs from.
CLOTH = ("shelf_bunting", "shelf_awning_*")   # see is_cloth(); grouping uses it


def is_cloth(name):
    return name.startswith("shelf_awning") or name.split(".")[0] == "shelf_bunting"


# WHAT THIS GATE OWNS.  Canon (MIGRATION.md, 2026-07-29) puts every district pass
# on the hook for "its NEW materials", and queues a separate master-wide legacy
# cure for the town's procedural foliage ramps and ropes — those are shared kit
# that four accepted districts are already built on, and re-authoring them from
# inside one district would fork the kit and change accepted art.  So:
#   HARD FAIL  on any `mat_shelf_*` that does not survive, and on any object whose
#              colour is carried ONLY by shelf-owned materials and arrives white.
#   REPORTED   legacy kit materials that arrive white, by name and slot count, so
#              the queued survivability pass inherits the list instead of a vibe.
OWN = "mat_shelf_"

sel = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PREFIX)]
assert sel, "nothing to verify — run shelf_build.py first"
bpy.ops.object.select_all(action='DESELECT')
for o in sel:
    o.hide_set(False)
    o.select_set(True)
bpy.context.view_layer.objects.active = sel[0]
bpy.ops.export_scene.gltf(filepath=SCRATCH, export_format='GLB',
                          use_selection=True, export_apply=False,
                          export_materials='EXPORT')
print("exported %d objects -> %s (%.2f MB)"
      % (len(sel), SCRATCH, os.path.getsize(SCRATCH) / 1e6))
names_out = sorted(o.name for o in sel)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SCRATCH)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print("\n" + "=" * 78)
print("ROUND TRIP: %d objects out, %d in" % (len(names_out), len(meshes)))
print("=" * 78)


def mat_facts(m):
    """(has a texture with pixels, reads COLOR_0, emits, base colour) — read off
    the material that ARRIVED, not the one that was authored."""
    if m is None or not m.use_nodes:
        return False, False, False, (1.0, 1.0, 1.0)
    nt = m.node_tree
    tex = any(n.type == 'TEX_IMAGE' and n.image is not None and n.image.size[0] > 0
              for n in nt.nodes)
    vc = any(n.bl_idname == 'ShaderNodeVertexColor' or n.type == 'VERTEX_COLOR'
             for n in nt.nodes)
    b = nt.nodes.get("Principled BSDF")
    bc, em = (1.0, 1.0, 1.0), False
    if b is not None:
        bc = tuple(b.inputs["Base Color"].default_value)[:3]
        e = b.inputs.get("Emission Strength")
        ec = b.inputs.get("Emission Color")
        em = bool(e and e.default_value > 0.01
                  and ec and max(tuple(ec.default_value)[:3]) > 0.02)
    return tex, vc, em, bc


GROUPS = [("ground / cliff / paving", ("shelf_ground", "shelf_cliffface",
                                      "shelf_paving", "shelf_stair_underworks")),
          ("buildings", ("shelf_inn", "shelf_item", "shelf_weapon", "shelf_armor",
                         "shelf_home")),
          ("cloth  (COLOR_0)", is_cloth),
          ("street furniture", ("shelf_parapet", "shelf_lantern", "shelf_sign",
                                "shelf_stalls", "shelf_clut", "shelf_bunting_lines")),
          ("foliage", ("veg_shelf_",))]

bad, legacy_white, seen = [], {}, set()
for label, pref in GROUPS:
    match = pref if callable(pref) else (lambda n, p=pref: n.startswith(p))
    obs = [o for o in meshes if match(o.name)]
    if not obs:
        continue
    seen |= {o.name for o in obs}
    ntex = nvc = nflat = nem = 0
    means = []
    for o in obs:
        cloth = is_cloth(o.name)
        ca = o.data.color_attributes.active_color
        if ca is not None and len(ca.data):
            d = np.zeros(len(ca.data) * 4)
            ca.data.foreach_get("color", d)
            rgb = d.reshape(-1, 4)[:, :3]
            means.append(float(rgb.mean()))
            nvc += 1
            # "the vertex colour was lost" looks EXACTLY like flat 1,1,1
            if rgb.std() < 0.002 and abs(rgb.mean() - 1.0) < 0.01:
                nflat += 1
                if cloth:
                    bad.append((o.name, "COLOR_0 came back flat white"))
        elif cloth:
            bad.append((o.name, "cloth arrived with no COLOR_0"))
        if not o.data.materials:
            bad.append((o.name, "arrived with no material at all"))
            continue
        own_ok = own_any = False
        for m in o.data.materials:
            tex, vc, em, bc = mat_facts(m)
            ntex += 1 if tex else 0
            nem += 1 if em else 0
            delivers = tex or em or (vc and ca is not None)
            mine = bool(m and m.name.startswith(OWN))
            if mine:
                own_any = True
                own_ok = own_ok or delivers
                if not delivers and min(bc) > 0.95:
                    bad.append((o.name, "%s (SHELF-OWNED) is default-white and "
                                        "unpainted" % m.name))
            elif not delivers and min(bc) > 0.95:
                legacy_white[m.name] = legacy_white.get(m.name, 0) + 1
        if own_any and not own_ok:
            bad.append((o.name, "no shelf-owned material on it delivers colour"))
    print("  %-24s %3d objs | textured mats %3d | COLOR_0 %3d (flat-white %d) | "
          "emissive mats %2d | mean COLOR_0 %s"
          % (label, len(obs), ntex, nvc, nflat, nem,
             "%.3f" % (sum(means) / len(means)) if means else "  -  "))

rest = [o for o in meshes if o.name not in seen]
if rest:
    print("  %-24s %3d objs  %s" % ("(ungrouped)", len(rest),
                                    [o.name for o in rest][:8]))

imgs = [i for i in bpy.data.images if i.name != "Render Result"]
print("\n  images that arrived: %d  %s"
      % (len(imgs), [(i.name, i.size[0], i.size[1]) for i in imgs][:6]))
for i in imgs:
    if i.size[0] == 0:
        bad.append((i.name, "image arrived with no pixels"))

nown = len([m for m in bpy.data.materials if m.name.startswith(OWN)])
ownwhite = [m.name for m in bpy.data.materials if m.name.startswith(OWN)
            and not any(mat_facts(m)[:3]) and min(mat_facts(m)[3]) > 0.95]
print("  materials: %d, of which shelf-owned: %d (white: %d)"
      % (len(bpy.data.materials), nown, len(ownwhite)))
if legacy_white:
    print("\n  INHERITED DEBT — shared kit materials that arrive WHITE, on shelf")
    print("  objects.  Not this district's to re-author (four accepted districts")
    print("  are built on them); this is the list the queued master-wide")
    print("  survivability pass needs (MIGRATION.md 2026-07-29):")
    for n, c in sorted(legacy_white.items(), key=lambda t: -t[1]):
        print("     %-24s %4d shelf material slots" % (n, c))

print("\n" + "=" * 78)
if bad:
    for n, why in bad[:25]:
        print("  !! %-34s %s" % (n, why))
    print("ROUND TRIP FAILED: %d problems" % len(bad))
    os.remove(SCRATCH)
    sys.exit(1)
print("ROUND TRIP CLEAN — every SHELF-OWNED material survives: %d of them, "
      "0 white." % nown)
print("(%d shared-kit materials arrive white and are listed above as inherited "
      "debt.)" % len(legacy_white))
print("=" * 78)
os.remove(SCRATCH)
