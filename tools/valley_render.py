"""valley_render.py — EEVEE self-verification renders for the valley region.

  Blender -b tools/blends/overworld-valley.blend -P tools/valley_render.py -- [shots]

RENDER NORM (MIGRATION canon): these are the agent's own eyes, not presentation.
EEVEE only, Standard view transform — the three.js runtime tone-maps nothing, so a
Standard EEVEE frame is the honest prediction of what ships.

Writes docs/qa/overworld/valley_<shot>.png at 1344x768.  `--` zones adds the QA
zone-overlay pass on top of the layout camera.
"""
import bpy
import contextlib
import io
import os
import sys
import time

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(ROOT, "docs/qa/overworld")
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOTS = (argv[0].split(",") if argv and argv[0] != "all"
         else ["overview", "emberbrook", "midvalley", "gorge", "moorage", "vistaring"])
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
PREFIX = argv[2] if len(argv) > 2 else "valley"

sc = bpy.data.scenes["valley"]
if bpy.context.window:
    bpy.context.window.scene = sc
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
try:
    sc.eevee.taa_render_samples = SAMPLES
except Exception:
    pass

ovl = sc.objects.get("qa_zone_overlay__valley")
for shot in SHOTS:
    want_zones = shot == "zones"
    cam = sc.objects.get("cam_%s__valley" % ("overview" if want_zones else shot))
    if not cam:
        print("MISSING cam_%s__valley" % shot)
        continue
    sc.camera = cam
    if ovl:
        ovl.hide_render = not want_zones
    fp = os.path.join(OUT, "%s_%s.png" % (PREFIX, shot))
    sc.render.filepath = fp
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    print("RENDERED %s  (%.1fs, %d samples)" % (fp, time.time() - t0, SAMPLES))
if ovl:
    ovl.hide_render = True
