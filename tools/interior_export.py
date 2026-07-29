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

# strip objects the ROOM's camera never sees but which would depth-occlude the
# runtime character: cutaway near-wall/ceiling (visible_camera=False in Cycles —
# a flag glTF ignores!) and volume fog boxes. Without this the character renders
# but is hidden behind invisible geometry.
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        continue
    name = o.name.lower()
    hidden = (not o.visible_camera) or o.hide_render or o.hide_viewport
    if o.name.startswith('walk_'):
        continue          # collision pads are hide_render by design — keep
    if hidden or ('fog' in name) or ('shadow_ceiling' in name):
        bpy.data.objects.remove(o, do_unlink=True)

# furniture -> invisible collision blockers (bar_ class): the walk_floor is a
# plain rectangle, so without these the character walks through tables/hearths.
# Heuristic: floor-standing (min z < 0.5), solid-height (max z >= 0.7), and a
# real footprint (>= 0.45 each axis, < 6u so room shells are skipped).
import mathutils
bpy.context.view_layer.update()
made = 0
for o in [x for x in bpy.data.objects if x.type == 'MESH']:
    if o.name.startswith(('walk_', 'bar_')):
        continue
    bb = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    xs=[v.x for v in bb]; ys=[v.y for v in bb]; zs=[v.z for v in bb]
    sx, sy = max(xs)-min(xs), max(ys)-min(ys)
    if min(zs) < 0.5 and max(zs) >= 0.7 and 0.45 <= sx < 6 and 0.45 <= sy < 6:
        mesh = bpy.data.meshes.new('bar_auto'); ob = bpy.data.objects.new('bar_auto_%03d' % made, mesh)
        import bmesh
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0); bm.to_mesh(mesh); bm.free()
        ob.scale = (max(sx,0.5)/2, max(sy,0.5)/2, 0.9)
        ob.location = ((min(xs)+max(xs))/2, (min(ys)+max(ys))/2, 0.9)
        bpy.context.scene.collection.objects.link(ob)
        made += 1
print("furniture blockers:", made)

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
