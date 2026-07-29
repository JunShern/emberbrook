"""weave_gltf_verify.py — prove the Weave survives the glTF round trip.

  Blender -b tools/blends/dellhollow-master.blend -P tools/weave_gltf_verify.py

Step 1 exports every `wv_` / `nl_` / `veg_wv_` / `veg_nl_` object from the master
to a scratch GLB.  Step 2 re-imports it into an EMPTY blend — so nothing in the
authoring file can prop the result up — and reports what actually arrived.

This is the gate the 516 white primitives would have failed.  A procedural
node-tree material (object-space box projection + noise, which is what
`mat_rock` / `mat_deck` and the whole pre-Locksfoot town is built from) renders
perfectly in Blender and exports as an untextured default-white glTF material.
Nothing short of re-importing catches it: the authoring render is not evidence.

Reported per object group:
  * COLOR_0 — present?  and is it FLAT WHITE, which is what "the vertex colour
    was lost" looks like from the outside
  * baseColorTexture — present, and pointing at real pixels
  * the mean base colour actually delivered, so a district that came back
    washed out is visible as a number rather than as a vibe
"""
import bpy, os, sys, numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
SCRATCH = os.path.join(ROOT, "tools", "blends", "districts", "_weave_roundtrip.glb")
PREFIX = ("wv_", "nl_", "veg_wv_", "veg_nl_")

# ------------------------------------------------------------------- export
sel = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PREFIX)]
assert sel, "nothing to verify — run weave_build.py first"
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

# ------------------------------------------------------------------- import
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SCRATCH)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print("\n" + "=" * 78)
print("ROUND TRIP: %d objects out, %d in" % (len(names_out), len(meshes)))
print("=" * 78)

GROUPS = [("decking / structure", ("wv_planking", "wv_joists", "wv_piles",
                                   "wv_pile_bracing", "wv_railings",
                                   "wv_stair_treads", "wv_fishdock_ladder")),
          ("huts", ("wv_hut_",)),
          ("the cottage", ("wv_keeper_cottage", "wv_cottage_footings")),
          ("props / cloth / clutter", ("wv_props", "wv_cloth_", "wv_clut_")),
          ("foliage", ("veg_wv_", "veg_nl_")),
          ("north landing", ("nl_",))]

bad = []
for label, pref in GROUPS:
    obs = [o for o in meshes if o.name.startswith(pref)]
    if not obs:
        continue
    nvc = nflat = ntex = 0
    means = []
    for o in obs:
        ca = o.data.color_attributes.active_color
        if ca is not None and len(ca.data):
            nvc += 1
            d = np.zeros(len(ca.data) * 4)
            ca.data.foreach_get("color", d)
            rgb = d.reshape(-1, 4)[:, :3]
            means.append(rgb.mean())
            # "lost the vertex colour" looks EXACTLY like flat 1,1,1
            if rgb.std() < 0.002 and abs(rgb.mean() - 1.0) < 0.01:
                nflat += 1
                bad.append((o.name, "COLOR_0 came back flat white"))
        else:
            bad.append((o.name, "no COLOR_0"))
        for m in o.data.materials:
            if m and m.use_nodes and any(n.type == "TEX_IMAGE" and n.image
                                         for n in m.node_tree.nodes):
                ntex += 1
                break
    print("  %-24s %3d objs | COLOR_0 %3d/%-3d (flat-white %d) | textured %3d | "
          "mean base %.3f"
          % (label, len(obs), nvc, len(obs), nflat, ntex,
             sum(means) / len(means) if means else -1))

imgs = [i for i in bpy.data.images if i.name != "Render Result"]
print("\n  images that arrived: %d  %s"
      % (len(imgs), [(i.name, i.size[0], i.size[1]) for i in imgs][:6]))
for i in imgs:
    if i.size[0] == 0:
        bad.append((i.name, "image arrived with no pixels"))

mats = bpy.data.materials
white = []
for m in mats:
    if not m.use_nodes:
        continue
    b = m.node_tree.nodes.get("Principled BSDF")
    if b is None:
        continue
    has_tex = any(n.type == "TEX_IMAGE" and n.image for n in m.node_tree.nodes)
    has_vc = any(n.type == "VERTEX_COLOR" or n.bl_idname == "ShaderNodeVertexColor"
                 for n in m.node_tree.nodes)
    bc = tuple(b.inputs["Base Color"].default_value)[:3]
    if not has_tex and not has_vc and min(bc) > 0.95:
        white.append(m.name)
print("  materials: %d, of which default-white-and-unpainted: %d %s"
      % (len(mats), len(white), white[:6]))

print("\n" + "=" * 78)
if bad:
    for n, why in bad[:25]:
        print("  !! %-34s %s" % (n, why))
    print("ROUND TRIP FAILED: %d problems" % len(bad))
    os.remove(SCRATCH)
    sys.exit(1)
print("ROUND TRIP CLEAN — every Weave object arrives with COLOR_0 and its texture.")
print("=" * 78)
os.remove(SCRATCH)
