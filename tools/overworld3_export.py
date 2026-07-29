"""overworld3_export.py — bundle style F2 into the playable scene.

  Blender -b tools/blends/overworld-proto3.blend -P tools/overworld3_export.py

Produces public/assets/scenes/ow-proto-f2/{background.png, stylized.png, scene.glb}
alongside the zones.json the build script already wrote there.

Runtime contract (public/play3d.html), unchanged from round 2:
  * every mesh that is NOT water_* / lm_ / veg_ is standable AND blocking
  * walk_* meshes are the designed walk network and drive spawn placement
  * veg_* is removed from collision entirely — no standing, no blocking (so the
    trunks MUST be separate meshes from the canopies, and they are)
NEW in round 3: zones.json beside scene.glb. The runtime loads it if present, and
its absence is not an error — every other ow-proto bundle still works.
"""
import bpy
import os
import re
import shutil
import contextlib
import io

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
STYLE = "f2"
KEY = "ow-proto-" + STYLE
OUT = os.path.join(ROOT, "public/assets/scenes", KEY)
os.makedirs(OUT, exist_ok=True)

vista = os.path.join(ROOT, "docs/qa/overworld/f2_vista.png")
shutil.copyfile(vista, os.path.join(OUT, "background.png"))
shutil.copyfile(vista, os.path.join(OUT, "stylized.png"))

sc = bpy.data.scenes["style_" + STYLE]
if bpy.context.window:
    bpy.context.window.scene = sc
keep = set(sc.objects)

for o in list(bpy.data.objects):
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)
# render-only scaffolding: the 1.45u scale capsules and the QA zone overlay.  The
# runtime builds its own overlay from zones.json, so shipping this one would only
# be 13 824 triangles of duplicate truth.
for o in list(sc.objects):
    if o.name.startswith("ref_char") or o.name.startswith("qa_"):
        bpy.data.objects.remove(o, do_unlink=True)
for o in list(sc.objects):
    o.name = re.sub(r"__%s(\.\d+)?$" % STYLE, "", o.name)
    if o.data and hasattr(o.data, "name"):
        o.data.name = re.sub(r"__%s(\.\d+)?$" % STYLE, "", o.data.name)
# round 1 named the terrain ground_valley; the .001 suffix is an artefact of
# rebuilding it beside the copied blockout, and overworld3_verify keys off the name
for o in sc.objects:
    o.name = re.sub(r"\.\d+$", "", o.name)
    if o.data and hasattr(o.data, "name"):
        o.data.name = re.sub(r"\.\d+$", "", o.data.name)

cam = sc.objects.get("cam_chase")
if cam:
    sc.camera = cam

meshes = [o for o in sc.objects if o.type == "MESH"]
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
walk = sorted(o.name for o in meshes if o.name.lower().startswith("walk"))
water = sorted(o.name for o in meshes if o.name.lower().startswith("water_"))
veg = sorted(o.name for o in meshes if o.name.lower().startswith("veg_"))

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
zp = os.path.join(OUT, "zones.json")
print("EXPORT OK %s | %d meshes | %d tris | glb %.2f MB | cam=%s"
      % (KEY, len(meshes), tris, sz, cam.name if cam else "-"))
print("  walk_:  %s" % ", ".join(walk))
print("  water_: %s" % ", ".join(water))
print("  veg_:   %s" % ", ".join(veg))
print("  zones.json: %s" % ("%.1f kB" % (os.path.getsize(zp) / 1e3)
                            if os.path.exists(zp) else "*** MISSING"))
print("  URL:    play3d.html?scene=%s&rt=1" % KEY)
