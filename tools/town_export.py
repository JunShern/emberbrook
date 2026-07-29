# town_export.py — export the whole-town blockout as a playable runtime bundle.
# Run headless: /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-master.blend -P tools/town_export.py
#   (the MASTER is the source of truth for form; dellhollow-town.blend is topology reference only)
# Produces public/assets/scenes/townwalk/{background.png, stylized.png, scene.glb}
# (stylized = copy of background for the gray-walk build; collision = walk_* meshes;
#  every mesh exports for depth-occlusion.)

import bpy, os, shutil, contextlib, io
from mathutils import Vector

OUT = os.environ.get("TOWNWALK_OUT",           # override for staged live-refresh exports
      "/Users/junshernchan/projects/multiplayer-rpg/public/assets/scenes/townwalk")
os.makedirs(OUT, exist_ok=True)

# --- one wide ortho camera covering the whole town, classic 3/4 -------------
xs, ys, zs = [], [], []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith("walk_"):   # frame the PLAYABLE town, not stray helpers
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            xs.append(w.x); ys.append(w.y); zs.append(w.z)
cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
span = max(max(xs)-min(xs), (max(zs)-min(zs)) * 1.75) * 1.08

cd = bpy.data.cameras.new("cam_townwalk"); cd.type = 'ORTHO'
cd.ortho_scale = span; cd.clip_end = 500
cam = bpy.data.objects.new("cam_townwalk", cd)
bpy.context.scene.collection.objects.link(cam)
cam.location = (cx + 60, cy - 55, cz + 62)
cam.rotation_euler = (Vector((cx, cy, cz)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
sc = bpy.context.scene
sc.camera = cam

# --- backdrop render ---------------------------------------------------------
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 2688; sc.render.resolution_y = 1536
sc.render.filepath = os.path.join(OUT, "background.png")
with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.render.render(write_still=True)
shutil.copyfile(os.path.join(OUT, "background.png"), os.path.join(OUT, "stylized.png"))

# --- strip render-only helpers before GLB export ------------------------------
# fog volumes / haze slabs / backdrop planes are Cycles-only atmosphere: in the
# runtime GLB they become giant opaque boxes. Convention: fx_* = render-only.
import re
FX = re.compile(r"^(fx_|FOG|.*haze|ridge_upstream|far_town|v10_)", re.I)
stripped = 0
for o in list(bpy.data.objects):
    if o.type == 'MESH' and FX.match(o.name):
        bpy.data.objects.remove(o, do_unlink=True); stripped += 1
print("fx helpers stripped from runtime export:", stripped)

# --- GLB (all meshes + the camera) -------------------------------------------
with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "scene.glb"),
                              export_format='GLB',
                              # walk meshes under a detailed district are render-hidden
                              # (collision only): they MUST still export.
                              use_visible=False, use_renderable=False, use_selection=False,
                              export_yup=True, export_cameras=True, export_lights=False)
n_walk = sum(1 for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('walk_'))
print("EXPORT OK -> %s | ortho %.1f | walk meshes: %d" % (OUT, span, n_walk))
