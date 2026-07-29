# interior_export.py — bundle ACCEPTED interior blends into playable runtime scenes.
# Run: /Applications/Blender.app/Contents/MacOS/Blender -b <blend> -P tools/interior_export.py -- <sceneKey> <renderPng>
# Produces public/assets/scenes/<sceneKey>/{background.png, stylized.png, scene.glb}
# background/stylized = the accepted art-gate render (no re-render); GLB carries the
# interior camera + all meshes (walk_* for collision, rest for depth-occlusion).

import bpy, os, sys, shutil, contextlib, io

argv = sys.argv[sys.argv.index("--") + 1:]
scene_key, render_png = argv[0], argv[1]
OUT = "/Users/junshernchan/projects/multiplayer-rpg/public/assets/scenes/" + scene_key
os.makedirs(OUT, exist_ok=True)

shutil.copyfile(render_png, os.path.join(OUT, "background.png"))
shutil.copyfile(render_png, os.path.join(OUT, "stylized.png"))

# ensure exactly the interior camera is exported and active
cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
cam = next((c for c in cams if 'int' in c.name.lower() or 'cam' in c.name.lower()), cams[0] if cams else None)
assert cam, "no camera in blend"
bpy.context.scene.camera = cam

with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "scene.glb"),
                              export_yup=True, export_cameras=True, export_lights=False)
n_walk = sum(1 for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('walk_'))
print("INTERIOR EXPORT OK %s | cam=%s | walk=%d" % (scene_key, cam.name, n_walk))
