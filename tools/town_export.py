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
cd.ortho_scale = span; cd.clip_end = max(500.0, span * 6.0)
cam = bpy.data.objects.new("cam_townwalk", cd)
bpy.context.scene.collection.objects.link(cam)
# THE STAND-OFF IS SIZED TO THE TOWN, and under an ORTHO camera that is free: distance
# along the view axis does not change the image at all, only what falls behind the near
# plane.  The literal (60, -55, 62) was 103 m of stand-off against a 74 m Dellhollow;
# Emberbrook at 2x is 150 m across and its far corner was arriving 50 m from the clip.
# Same direction, same framing, more room — Dellhollow's plate is unchanged.
_dir = Vector((60.0, -55.0, 62.0)).normalized()
cam.location = Vector((cx, cy, cz)) + _dir * max(103.0, span * 1.6)
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
stripped = backdrops = 0
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        continue
    # AND THE SAME RULE AS A PROPERTY RATHER THAN A NAME, because a name convention only
    # catches the lanes that read it.  Emberbrook's `far_horizon` backdrop (emb_dress.py)
    # is 1800 m of skirt and ridge that is deliberately visible to CAMERA RAYS AND NOTHING
    # ELSE, so it cannot bounce a photon or cast a shadow — and it must not reach a runtime
    # bundle either, where walkGround and the BVH would take it for world.  IF NOTHING BUT
    # THE CAMERA MAY SEE IT, IT IS A PICTURE AND NOT A PLACE.  `tools/cine_bake.py --glb`
    # carries the identical test; Dellhollow has no such object and exports unchanged.
    backdrop = (o.visible_camera and not o.visible_diffuse
                and not o.visible_glossy and not o.visible_shadow)
    if FX.match(o.name) or backdrop:
        bpy.data.objects.remove(o, do_unlink=True)
        stripped += 1
        backdrops += 1 if backdrop else 0
print("fx helpers stripped from runtime export: %d (of which %d camera-ray-only backdrops)"
      % (stripped, backdrops))

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
