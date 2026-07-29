"""overworld3_render.py — EEVEE check renders for style F2.

  Blender -b tools/blends/overworld-proto3.blend -P tools/overworld3_render.py -- [shots]

EEVEE ONLY and view transform Standard: this tile renders in real time in three.js,
which tone-maps nothing, so a Standard EEVEE frame is the honest prediction of what
ships and a Cycles beauty pass would lie about it (RENDER NORM, MIGRATION.md).

Writes docs/qa/overworld/f2_{chase,vista,gorge,lineup,zones_overlay}.png at 1344x768.
The zones_overlay shot is the only one that unhides qa_zone_overlay — that object is
render-only scaffolding and never reaches the GLB.
"""
import bpy
import os
import sys
import io
import contextlib
import time

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(ROOT, "docs/qa/overworld")
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOTS = (argv[0].split(",") if argv and argv[0] != "all"
         else ["chase", "vista", "gorge", "lineup", "zones_overlay"])

sc = bpy.data.scenes["style_f2"]
if bpy.context.window:
    bpy.context.window.scene = sc
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
try:
    sc.eevee.taa_render_samples = 96
except Exception:
    pass

ovl = sc.objects.get("qa_zone_overlay__f2")

for shot in SHOTS:
    camname = "cam_zones__f2" if shot == "zones_overlay" else "cam_%s__f2" % shot
    cam = sc.objects.get(camname)
    if not cam:
        print("MISSING %s" % camname)
        continue
    sc.camera = cam
    if ovl:
        ovl.hide_render = (shot != "zones_overlay")
    fp = os.path.join(OUT, "f2_%s.png" % shot)
    sc.render.filepath = fp
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    print("RENDERED %s  (%.1fs)" % (fp, time.time() - t0))

if ovl:
    ovl.hide_render = True
