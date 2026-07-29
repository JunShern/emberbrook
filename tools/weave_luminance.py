"""weave_luminance.py — did this pass re-value the accepted districts?

  Blender -b <blend> -P tools/weave_luminance.py -- <tag> [EEVEE|CYCLES] [samples]

Renders the three continuity cameras and prints the MEAN LUMINANCE of each frame,
so a before/after pair of runs gives the number that says "one town, not two
datasets".  Writes docs/qa/districts/weave_lum_<tag>_<name>.png alongside.

Two traps this obeys:

* finding 119 — a backup blend can only be rendered FROM THE DIRECTORY its
  relative texture paths were written for.  `master-pre-weave.blend` lives in
  `tools/blends/backups/` and references `//../textures/...`, which from there
  resolves to `tools/blends/textures` — nothing.  Every material then renders
  Blender's missing-texture magenta and the "before" number is measuring the
  measuring rig.  Copy the backup to `tools/blends/` (the same depth) first.
* finding 118 — a continuity camera is chosen for what is IN it.  All three of
  these look AWAY from the Weave, at the accepted district's own content.
"""
import bpy, os, sys, math, io, contextlib
import numpy as np
from mathutils import Vector

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TAG = argv[0] if argv else "now"
ENGINE = argv[1] if len(argv) > 1 else "CYCLES"
SAMPLES = int(argv[2]) if len(argv) > 2 else 48

SHOTS = {
    # the Boatyard v10 hero, the same camera every district pass has quoted
    "continuity":   dict(pos=(37.6, 25.4, 8.5), aim=(14.4, 30.4, 3.4), fov=35),
    # WEST along the Waterfront boardwalk: its own art, no Weave in frame
    "wfcontinuity": dict(pos=(58.6, 32.4, 5.0), aim=(38.5, 27.4, 1.5), fov=40),
    # WEST along Locksfoot: the moorage and the dam, not the tier above them
    "lfcontinuity": dict(pos=(95.0, 33.0, 4.0), aim=(78.0, 27.0, 1.0), fov=44),
}

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 672, 384      # half res: the
sc.render.resolution_percentage = 100                          # mean is the point
sc.render.image_settings.file_format = "PNG"
if ENGINE == "CYCLES":
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU setup skipped:", e)
        sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
else:
    sc.render.engine = "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = SAMPLES
    except Exception:
        pass

# a magenta frame is what a broken texture path looks like — check for it rather
# than trusting the number (finding 119)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("walk_", "bar_")) and not o.hide_render:
        o.hide_render = True

print("blend: %s" % bpy.data.filepath)
for name, s in SHOTS.items():
    cd = bpy.data.cameras.new("lum_" + name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(s["fov"])
    cd.clip_start, cd.clip_end = 0.05, 1200
    cam = bpy.data.objects.new("lum_" + name, cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(s["pos"])
    cam.rotation_euler = (Vector(s["aim"]) - Vector(s["pos"])).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    fp = os.path.join(OUT, "weave_lum_%s_%s.png" % (TAG, name))
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fp)
    px = np.array(im.pixels[:]).reshape(-1, im.channels)[:, :3]
    lum = float((px * np.array([0.2126, 0.7152, 0.0722])).sum(axis=1).mean())
    r, g, b = px.mean(axis=0)
    # a missing-texture frame is strongly magenta: R and B high, G low
    magenta = (r > 0.25 and b > 0.25 and g < 0.6 * min(r, b))
    print("LUM %-10s %-14s mean=%.4f   rgb=(%.3f, %.3f, %.3f)%s"
          % (TAG, name, lum, r, g, b, "   <-- MAGENTA: broken texture paths" if magenta else ""))
    bpy.data.images.remove(im)
