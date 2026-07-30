"""ga_shot.py — one EEVEE record frame from a SOLVED del-cine camera.

  Blender -b tools/blends/dellhollow-master.blend -P tools/ga_shot.py \
      --python-exit-code 1 -- <camId> <out.png> [samples]

The record-shot norm (2026-07-29): agent renders are SELF-VERIFICATION and nobody
polishes a camera.  `tools/lg_shot.py` aims a camera at a bounding box, which is
the right tool for looking at a build and the WRONG tool for judging an ARRIVAL:
the only frame that matters there is the one the player actually gets.  So every
number here — pos, aim, fov, aspect, clip, and the grade — is read from
`public/townmap/dellhollow.cameras.solved.json` and its `defaults`, exactly as
`tools/cine_bake.py:build_cam()` reads them, so this frame and the baked backdrop
cannot disagree about where the camera stands.  Cycles/denoise and the depth pass
are deliberately NOT reproduced: this is EEVEE self-verification, not a re-bake.

`record()` is importable so `tools/ga_build.py` can look at what it just did
without a second copy of the camera numbers or a write to the master.
Never saves the blend.
"""
import bpy, os, sys, math, io, json, contextlib
import numpy as np
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import REPO

SOLVED = REPO + "/public/townmap/dellhollow.cameras.solved.json"


def record(camid, outpng, samples=96):
    S = json.load(open(SOLVED))
    D = S["defaults"]
    c = next(c for c in S["cameras"] if c["id"] == camid)

    sc = bpy.context.scene
    asp = c.get("aspect", D.get("aspect", 1.75))
    sc.render.resolution_y = 768
    sc.render.resolution_x = int(round(768 * asp))
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = samples
    try:
        sc.eevee.shadow_pool_size = '1024'
    except Exception as e:
        print("shadow_pool_size NOT SET: %s" % e)
    sc.view_settings.view_transform = D.get("view_transform", "AgX")
    sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
    sc.view_settings.exposure = D.get("exposure", 0.0)

    old = bpy.data.objects.get("rec_cine_" + camid)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    cd = bpy.data.cameras.new("rec_cine_" + camid)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(c.get("fov", D.get("fov", 35)))
    cd.clip_start, cd.clip_end = c.get("clip", D["clip"])
    cam = bpy.data.objects.new("rec_cine_" + camid, cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(c["pos"])
    cam.rotation_euler = (Vector(c["aim"]) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    print("cine camera %s  pos (%.3f, %.3f, %.3f)  aim (%.3f, %.3f, %.3f)  fov %.1f  %dx%d"
          % (camid, *c["pos"], *c["aim"], c.get("fov", 35),
             sc.render.resolution_x, sc.render.resolution_y))

    os.makedirs(os.path.dirname(outpng), exist_ok=True)
    sc.render.filepath = outpng
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bpy.ops.render.render(write_still=True)
    px = np.asarray(bpy.data.images.load(outpng).pixels[:],
                    dtype=np.float32).reshape(-1, 4)[:, :3]
    lum = float((px * np.array([0.2126, 0.7152, 0.0722])).sum(axis=1).mean())
    r, g, b = px.mean(axis=0)
    print("RECORD %-10s %s  mean=%.4f  rgb=(%.3f, %.3f, %.3f)"
          % (camid, os.path.basename(outpng), lum, r, g, b))
    return lum


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    record(argv[0], argv[1], int(argv[2]) if len(argv) > 2 else 96)
