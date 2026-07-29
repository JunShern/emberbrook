"""overworld_render.py — EEVEE comparison renders for the four overworld styles.

  Blender -b tools/blends/overworld-proto.blend -P tools/overworld_render.py -- [styles] [shots]

EEVEE ONLY: this world renders in real time in the engine, so a Cycles render would
lie about it.  View transform is Standard (not AgX) because the three.js runtime does
no tone mapping — a Standard render is the honest prediction of what ships.

Writes docs/qa/overworld/style_{a,b,c,d}_{chase,vista,village}.png at 1344x768.
"""
import bpy, os, sys, io, contextlib, time

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(ROOT, "docs/qa/overworld")
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STYLES = (argv[0].split(",") if argv and argv[0] != "all" else ["a", "b", "c", "d"])
SHOTS = (argv[1].split(",") if len(argv) > 1 and argv[1] != "all" else ["chase", "vista", "village"])

for s in STYLES:
    sc = bpy.data.scenes["style_" + s]
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
    for shot in SHOTS:
        cam = sc.objects.get("cam_%s__%s" % (shot, s)) or sc.objects.get("cam_" + shot)
        if not cam:
            print("MISSING cam_%s in style_%s" % (shot, s))
            continue
        sc.camera = cam
        # style C leans on a shallow "tabletop" depth of field; every other style
        # renders pinhole so the comparison is about surface treatment
        cam.data.dof.use_dof = (s == "c" and shot in ("chase", "village"))
        if cam.data.dof.use_dof:
            cam.data.dof.focus_distance = 16.0 if shot == "chase" else 15.0
            cam.data.dof.aperture_fstop = 0.85
        fp = os.path.join(OUT, "style_%s_%s.png" % (s, shot))
        sc.render.filepath = fp
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.render.render(write_still=True, scene=sc.name)
        print("RENDERED %s  (%.1fs)" % (fp, time.time() - t0))
