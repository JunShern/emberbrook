"""Shared render setup for the Dellhollow pre-rendered background pipeline."""
import bpy, math, io, contextlib, os


def setup_cycles(samples=128, res=(1344, 768), denoise=True, exposure=0.0):
    sc = bpy.context.scene
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
    sc.cycles.samples = samples
    sc.cycles.use_denoising = denoise
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 4
    sc.cycles.volume_bounces = 2
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = exposure
    return sc


def setup_eevee(res=(1344, 768)):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    return sc


def make_camera(name, loc, look_at, lens=35.0, coll=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 500.0
    ob = bpy.data.objects.new(name, cd)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    aim(ob, look_at)
    bpy.context.scene.camera = ob
    return ob


def aim(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def render_to(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc = bpy.context.scene
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bpy.ops.render.render(write_still=True)
    return path
