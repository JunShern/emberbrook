"""owdraft_render.py — EEVEE renders of the hanging-valley PROPOSAL blockout.

  Blender --python-exit-code 1 -b tools/blends/owdraft-embercorridor.blend \
          -P tools/owdraft_render.py -- [shots] [samples]

RENDER NORM (migration canon): EEVEE, Standard view transform — the three.js
runtime tone-maps nothing, so a Standard EEVEE frame is the honest prediction.
Writes docs/qa/overworld-draft/embercorridor_<shot>.png at 1344x768.

*** PROPOSAL DRAFT. NOT CANON. ***
"""
import bpy
import contextlib
import io
import os
import sys
import time

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(ROOT, "docs/qa/overworld-draft")
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOTS = argv[0].split(",") if argv and argv[0] != "all" else ["aerial", "fromgate", "fromdell"]
SAMPLES = int(argv[1]) if len(argv) > 1 else 64

sc = bpy.data.scenes["embercorridor"]
if bpy.context.window:
    bpy.context.window.scene = sc
try:
    sc.render.engine = "BLENDER_EEVEE"
except TypeError:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
try:
    sc.eevee.taa_render_samples = SAMPLES
except Exception:
    pass

for shot in SHOTS:
    cam = sc.objects.get("cam_%s__draft" % shot)
    if not cam:
        print("MISSING cam_%s__draft" % shot)
        continue
    sc.camera = cam
    fp = os.path.join(OUT, "embercorridor_%s.png" % shot)
    sc.render.filepath = fp
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True, scene=sc.name)
    print("RENDERED %s  (%.1fs)" % (fp, time.time() - t0))
