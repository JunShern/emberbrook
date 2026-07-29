"""boatyard_export.py — bundle the district as a playable runtime scene.

  Blender -b tools/blends/districts/boatyard.blend -P tools/boatyard_export.py -- <render.png>

Produces public/assets/scenes/del-boatyard/{background.png, stylized.png, scene.glb}.
background/stylized = the accepted art-gate render (no re-render); the GLB carries
the parcel camera plus every mesh — the preserved walk_* meshes for collision,
everything else for depth occlusion.

Volume/haze/prototype objects are dropped from the GLB: they are invisible boxes
that would wreck the runtime depth test.  The blend on disk is never re-saved.
"""
import bpy, os, sys, shutil, contextlib, io

argv = sys.argv[sys.argv.index("--") + 1:]
RENDER = argv[0]
OUT = "/Users/junshernchan/projects/multiplayer-rpg/public/assets/scenes/del-boatyard"
os.makedirs(OUT, exist_ok=True)

shutil.copyfile(RENDER, os.path.join(OUT, "background.png"))
shutil.copyfile(RENDER, os.path.join(OUT, "stylized.png"))

DROP_PREFIX = ("FOG_BOX", "v10_haze", "v10_src_", "kit_", "REF_human")
DROP_SUBSTR = ("spray", "smoke", "plume", "mist")
dropped = []
for ob in list(bpy.data.objects):
    if ob.type == 'LIGHT':
        bpy.data.objects.remove(ob, do_unlink=True)
        continue
    if ob.type != 'MESH':
        continue
    hidden_src = any(c.name == "PROBE_SRC" for c in ob.users_collection)
    if hidden_src or ob.name.startswith(DROP_PREFIX) or any(t in ob.name for t in DROP_SUBSTR):
        dropped.append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)
        continue
    ob.hide_viewport = False        # hide_viewport would drop it from the export
    ob.hide_set(False)
print("dropped from GLB (%d): %s ..." % (len(dropped), dropped[:10]))

cam = bpy.data.objects.get("cam_boatyard")
assert cam, "cam_boatyard missing"
cam.hide_viewport = False
bpy.context.scene.camera = cam

walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
for w in walks:
    w.hide_render = True            # collision only, never drawn
    w.hide_viewport = False

with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "scene.glb"),
                              export_format='GLB',
                              use_visible=False, use_renderable=False,
                              use_selection=False,
                              export_yup=True, export_cameras=True,
                              export_lights=False, export_apply=True)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
size = os.path.getsize(os.path.join(OUT, "scene.glb")) / 1e6
print("EXPORT OK -> %s" % OUT)
print("  background/stylized <- %s" % RENDER)
print("  scene.glb: %.2f MB | meshes %d | walk meshes %d | camera %s"
      % (size, len(meshes), len(walks), cam.name))
for w in sorted(walks, key=lambda o: o.name):
    print("    walk: %s" % w.name)
