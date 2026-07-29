"""overworld_verify.py — prove each style survives the glTF round-trip.

  Blender -b --factory-startup -P tools/overworld_verify.py -- <style> [<style>…]

A style that renders beautifully in Blender and exports GREY is a failed prototype.
This re-imports the shipped GLB into an EMPTY blend (so nothing from the authoring
file can prop it up) and reports, per style, what actually arrived:

  * COLOR_0 vertex colours — present? what is the mean/spread? (a flat 1,1,1 means
    the colour was lost and the mesh will render white in three.js)
  * baseColorTexture — present? how many pixels?
  * roughness / metallic / emissive / alpha-blend — the principled params the styles
    lean on (C's gloss, B's fog alpha, the hearth's glow)
  * the runtime naming contract: walk_* and water_* meshes
"""
import bpy, os, sys, numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STYLES = argv if argv else ["a", "b", "c", "d"]

ok_all = True
for s in STYLES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    glb = os.path.join(ROOT, "public/assets/scenes/ow-proto-%s/scene.glb" % s)
    bpy.ops.import_scene.gltf(filepath=glb)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    walk = [o.name for o in meshes if o.name.lower().startswith("walk")]
    water = [o.name for o in meshes if o.name.lower().startswith("water_")]

    print("\n=== STYLE %s  (%s)" % (s.upper(), os.path.basename(glb)))
    print("  %d meshes, %d tris, %d cameras, %.2f MB"
          % (len(meshes), tris, len(cams), os.path.getsize(glb) / 1e6))
    print("  walk_:  %s" % (", ".join(walk) or "NONE  <-- spawn will fall back"))
    print("  water_: %s" % (", ".join(water) or "NONE"))

    n_vcol, n_flat, n_tex = 0, 0, 0
    for o in meshes:
        ca = o.data.color_attributes.active_color
        if ca is not None:
            n_vcol += 1
            d = np.zeros(len(ca.data) * 4)
            ca.data.foreach_get("color", d)
            d = d.reshape(-1, 4)
            rgb = d[:, :3]
            if rgb.std() < 0.002 and abs(rgb.mean() - 1.0) < 0.01:
                n_flat += 1
    for m in bpy.data.materials:
        if m.use_nodes and any(n.type == "TEX_IMAGE" and n.image for n in m.node_tree.nodes):
            n_tex += 1
    print("  COLOR_0 present on %d/%d meshes (%d suspiciously flat-white)"
          % (n_vcol, len(meshes), n_flat))
    print("  materials with a baseColor image: %d/%d" % (n_tex, len(bpy.data.materials)))

    # sample the terrain's actual colours — the single most load-bearing check
    g = bpy.data.objects.get("ground_valley")
    if g:
        if g.data.color_attributes.active_color:
            ca = g.data.color_attributes.active_color
            d = np.zeros(len(ca.data) * 4)
            ca.data.foreach_get("color", d)
            d = d.reshape(-1, 4)[:, :3]
            print("  ground_valley COLOR_0: mean=(%.3f, %.3f, %.3f)  std=%.3f  n=%d"
                  % (*d.mean(0), d.std(), len(d)))
        else:
            mt = g.data.materials[0] if g.data.materials else None
            im = None
            if mt and mt.use_nodes:
                im = next((n.image for n in mt.node_tree.nodes
                           if n.type == "TEX_IMAGE" and n.image), None)
            print("  ground_valley: no COLOR_0, baseColor image = %s %s"
                  % (im.name if im else "NONE", tuple(im.size) if im else ""))
            if im is None:
                ok_all = False
                print("  *** FAIL: terrain has neither vertex colours nor a texture")

    print("  material params:")
    for m in sorted(bpy.data.materials, key=lambda x: x.name):
        if not m.use_nodes:
            continue
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not b:
            continue
        bc = tuple(round(v, 3) for v in b.inputs["Base Color"].default_value[:3])
        vc = any(l.from_node.type in ("VERTEX_COLOR", "ATTRIBUTE", "MIX")
                 for l in m.node_tree.links if l.to_socket == b.inputs["Base Color"])
        tx = any(l.from_node.type == "TEX_IMAGE"
                 for l in m.node_tree.links if l.to_socket == b.inputs["Base Color"])
        em = b.inputs["Emission Strength"].default_value
        print("    %-26s base=%s rough=%.2f metal=%.2f emit=%.1f blend=%-6s vcol=%s tex=%s"
              % (m.name, bc, b.inputs["Roughness"].default_value,
                 b.inputs["Metallic"].default_value, em,
                 getattr(m, "blend_method", "?"), vc, tx))

print("\nVERIFY %s" % ("OK" if ok_all else "FAILED"))
