"""emb_skylevel.py — WHAT DOES THE PILOT'S WORLD ACTUALLY EMIT?

    Blender -b --python-exit-code 1 -P tools/emb_skylevel.py

Renders a 96x54 frame of NOTHING BUT THE WORLD — no geometry, no lamps, Standard view
transform, exposure 0 — to a 32-bit EXR and reads the linear pixels back, so the answer is
RADIANCE and not a tone-mapped guess.  It prints the flat background colour `emb_dress.py`
writes, then the `ShaderNodeTexSky` it links over that colour, at the same strength.

WHY IT EXISTS.  Two rounds of the dressing gate hunted an "additive term" on the mill's
stone.  It was the world.  `light_key()` writes a flat colour (0.30, 0.31, 0.42) at
strength 0.30 and then LINKS A SKY NODE OVER IT, so the flat value is dead code and the
only number anyone ever wrote down was the strength socket — and a strength socket is not
a level.  Measured here on Blender 5.1.1:

    flat colour (0.30, 0.31, 0.42) x 0.30   mean 0.0947  peak 0.0947  RGB 0.090/0.093/0.126
    Nishita sky node          x 0.30        mean 0.4458  peak 1.9073  RGB 0.474/0.440/0.421

4.7x the level, in a near-white instead of a blue.  A number nobody had ever put an
instrument on was the dominant light on every sky-facing surface in the frame.  The view
is aimed at the horizon band 180 deg from the sun, so the mean is the DOME and not the sun
disc — the disc is a separate double-count of the key light and is not what this measures.

NOTE THE CAMERA AIM IS PART OF THE MEASUREMENT.  A sky is not uniform; a mean over a
different band is a different number.  This one holds the pilot's own sun rotation (212)
and looks away from it at the elevation the mill's base masses see.
"""
import bpy
import math
import numpy as np

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

cd = bpy.data.cameras.new("c")
cd.lens_unit = 'FOV'
cd.angle = math.radians(120)
co = bpy.data.objects.new("c", cd)
bpy.context.scene.collection.objects.link(co)
co.location = (0, 0, 0)
co.rotation_euler = (math.radians(72), 0, math.radians(32))
bpy.context.scene.camera = co

scn = bpy.context.scene
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = 16
scn.cycles.use_denoising = False
scn.render.resolution_x, scn.render.resolution_y = 96, 54
scn.view_settings.view_transform = 'Standard'
scn.view_settings.exposure = 0.0
scn.view_settings.look = 'None'
scn.render.image_settings.file_format = 'OPEN_EXR'
scn.render.image_settings.color_depth = '32'
_n = [0]


def shoot(label):
    # 'Render Result' carries no readable pixels in background mode, so the frame goes to
    # a 32-bit EXR and is loaded back as a file image, which does.
    fp = "/tmp/_emb_skylevel_%d.exr" % _n[0]
    _n[0] += 1
    scn.render.filepath = fp
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(fp)
    px = np.zeros(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    a = px.reshape(-1, 4)[:, :3]
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    print("  %-36s  linear radiance  mean %8.4f  median %8.4f  peak %8.4f   "
          "RGB %6.3f %6.3f %6.3f"
          % (label, lum.mean(), np.median(lum), lum.max(), *a.mean(0)), flush=True)


w = bpy.data.worlds.new("W")
scn.world = w
w.use_nodes = True
nt = w.node_tree
bg = nt.nodes["Background"]
bg.inputs[0].default_value = (0.30, 0.31, 0.42, 1)
bg.inputs[1].default_value = 0.30
shoot("FLAT colour (0.30,0.31,0.42) x 0.30")

sky = nt.nodes.new("ShaderNodeTexSky")
for a_, v in (('sky_type', 'MULTIPLE_SCATTERING'), ('sun_elevation', math.radians(8.0)),
              ('sun_rotation', math.radians(212)), ('altitude', 200),
              ('air_density', 2.2), ('dust_density', 5.5), ('ozone_density', 1.4),
              ('sun_intensity', 0.30), ('sun_disc', True)):
    try:
        setattr(sky, a_, v)
    except Exception as e:
        print("  (Blender %s dropped %s: %s)" % (bpy.app.version_string, a_, e))
nt.links.new(sky.outputs["Color"], bg.inputs[0])
shoot("NISHITA sky node x 0.30 (the pilot's)")

for s in (0.15, 0.08, 0.04):
    bg.inputs[1].default_value = s
    shoot("NISHITA sky node x %.2f" % s)
print("DONE")
