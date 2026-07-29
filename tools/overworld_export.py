"""overworld_export.py — bundle one styled overworld tile into a playable scene.

  Blender -b tools/blends/overworld-proto.blend -P tools/overworld_export.py -- <style>

Produces public/assets/scenes/ow-proto-<style>/{background.png, stylized.png, scene.glb}
  background/stylized = that style's vista render (the runtime's backdrop)
  scene.glb           = the styled terrain + props + one camera

Runtime contract (public/play3d.html):
  * every mesh that is NOT named water_* is standable AND blocking (raw geometry
    collision), so the terrain top surface is the walkable ground with no extra work
  * walk_* meshes are the designed walk network and drive spawn placement
  * water_* is the non-standable convention — used for the river surface and for
    style B's fog bands, which must never become invisible floors in mid-air
"""
import bpy, os, sys, re, shutil, contextlib, io

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:]
STYLE = argv[0]
KEY = "ow-proto-" + STYLE
OUT = os.path.join(ROOT, "public/assets/scenes", KEY)
os.makedirs(OUT, exist_ok=True)

vista = os.path.join(ROOT, "docs/qa/overworld/style_%s_vista.png" % STYLE)
shutil.copyfile(vista, os.path.join(OUT, "background.png"))
shutil.copyfile(vista, os.path.join(OUT, "stylized.png"))

sc = bpy.data.scenes["style_" + STYLE]
if bpy.context.window:
    bpy.context.window.scene = sc
keep = set(sc.objects)

# strip everything that is not this style's scene, then drop the __<style> suffix so
# the runtime's ^walk / ^water_ regexes see clean names
for o in list(bpy.data.objects):
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(sc.objects):
    # the 1.45u scale capsules are a render-only measuring stick
    if o.name.startswith("ref_char"):
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(sc.objects):
    o.name = re.sub(r"__%s(\.\d+)?$" % STYLE, "", o.name)
    if o.data and hasattr(o.data, "name"):
        o.data.name = re.sub(r"__%s(\.\d+)?$" % STYLE, "", o.data.name)

cam = sc.objects.get("cam_chase__%s" % STYLE) or sc.objects.get("cam_chase")
if cam:
    sc.camera = cam

meshes = [o for o in sc.objects if o.type == "MESH"]
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
walk = [o.name for o in meshes if o.name.lower().startswith("walk")]
water = [o.name for o in meshes if o.name.lower().startswith("water_")]

kw = dict(filepath=os.path.join(OUT, "scene.glb"), export_format="GLB",
          export_yup=True, export_cameras=True, export_lights=False,
          export_apply=True, export_vertex_color="ACTIVE", use_active_scene=True,
          export_materials="EXPORT", export_image_format="JPEG")
while True:
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.export_scene.gltf(**kw)
        break
    except TypeError as e:
        m = re.search(r'"([A-Za-z_]+)"', str(e)) or re.search(r"'([A-Za-z_]+)'", str(e))
        if m and m.group(1) in kw:
            print("  (exporter does not accept %s — dropping)" % m.group(1))
            kw.pop(m.group(1))
            continue
        raise

sz = os.path.getsize(os.path.join(OUT, "scene.glb")) / 1e6
print("EXPORT OK %s | %d meshes | %d tris | glb %.2f MB | cam=%s"
      % (KEY, len(meshes), tris, sz, cam.name if cam else "-"))
print("  walk_:  %s" % ", ".join(walk))
print("  water_: %s" % ", ".join(water))
print("  URL:    play3d.html?scene=%s&rt=1" % KEY)
