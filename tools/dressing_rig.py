"""probe_rig.py — probe2-c's LIGHT AND LENS, in one place.

Every hero/canopy_slim candidate must be judged against
`docs/qa/emberbrook/styleprobe/probe2-c.png`, so the rig is copied from the probe that
produced it (`mill_probe_r2.py`) rather than re-invented: EMB_sun 3.0 W (1.0,0.70,0.42) at
elevation 62 / rotation 212, a 0.30 W warm bounce from below-behind, MULTIPLE_SCATTERING sky
at world strength 0.30, Cycles with 32 transparent bounces (an alpha-card canopy is dozens
of transparent surfaces deep and a low cap renders the inside of a tree black), AgX Medium
High Contrast, film exposure 0.10, 60 deg lens. A candidate that only looks good under a
different key has not been compared to anything.
"""
import bpy, os, math
from mathutils import Vector, Euler

S = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(S, 'ph')
SAMPLES = int(os.environ.get('CMP_SAMPLES', '96'))
RESX = int(os.environ.get('CMP_RESX', '1200'))
RESY = int(os.environ.get('CMP_RESY', '900'))


def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print('GPU', e)
        sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        sc.cycles.denoising_use_gpu = True
    except Exception:
        pass
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 4
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 32
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.film_exposure = 1.0
    sc.render.resolution_x, sc.render.resolution_y = RESX, RESY
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'
    for lk in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            sc.view_settings.look = lk
            break
        except Exception:
            pass
    sc.view_settings.exposure = 0.10

    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    bg.inputs[0].default_value = (0.30, 0.31, 0.42, 1)
    sky = nt.nodes.new('ShaderNodeTexSky')
    # Blender 5.1: 'NISHITA' is gone (SINGLE_/MULTIPLE_SCATTERING, PREETHAM, HOSEK_WILKIE)
    # and dust_density is gone with it — the round-1 sky silently did nothing on that
    for a, v in (('sky_type', 'MULTIPLE_SCATTERING'), ('sun_elevation', math.radians(8.0)),
                 ('sun_rotation', math.radians(212)), ('altitude', 200.0),
                 ('air_density', 2.2), ('ozone_density', 1.4),
                 ('sun_intensity', 0.30), ('sun_disc', True)):
        try:
            setattr(sky, a, v)
        except Exception as e:
            print('sky-attr', a, e)
    nt.links.new(sky.outputs['Color'], bg.inputs[0])
    bg.inputs[1].default_value = 0.30

    sd = bpy.data.lights.new('EMB_sun', 'SUN')
    sd.energy, sd.color, sd.angle = 3.0, (1.0, 0.70, 0.42), math.radians(2.5)
    so = bpy.data.objects.new('EMB_sun', sd)
    so.rotation_euler = Euler((math.radians(62), 0, math.radians(212)))
    sc.collection.objects.link(so)
    bd = bpy.data.lights.new('bounce', 'SUN')
    bd.energy, bd.color = 0.30, (1.0, 0.55, 0.34)
    bo = bpy.data.objects.new('bounce', bd)
    bo.rotation_euler = Euler((math.radians(108), 0, math.radians(30)))
    sc.collection.objects.link(bo)
    return sc


def ground():
    """the probe's own scanned ground, so the floor under a candidate is the ratified floor"""
    bpy.ops.mesh.primitive_plane_add(size=300)
    o = bpy.context.object
    m = bpy.data.materials.new('mat_ground_scan')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tex = os.path.join(PH, 'tex')
    co = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (60, 60, 60)
    nt.links.new(co.outputs['Object'], mp.inputs['Vector'])
    try:
        d = nt.nodes.new('ShaderNodeTexImage')
        d.image = bpy.data.images.load(os.path.join(tex, 'leafy_grass_Diffuse.jpg'))
        nt.links.new(mp.outputs['Vector'], d.inputs['Vector'])
        nt.links.new(d.outputs['Color'], b.inputs['Base Color'])
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(os.path.join(tex, 'leafy_grass_nor_gl.jpg'))
        n.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(n.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    except Exception as e:
        print('ground tex', e)
    b.inputs['Roughness'].default_value = 0.92
    o.data.materials.append(m)
    return o


def human(x, y):
    """1.80 m reference figure"""
    m = bpy.data.materials.new('mat_ref')
    m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.06, 0.055, 0.065, 1)
    bs.inputs['Roughness'].default_value = 1.0
    parts = []
    for r, h, z, dx in ((0.075, 0.86, 0.43, -0.10), (0.075, 0.86, 0.43, 0.10),
                        (0.155, 0.62, 1.17, 0), (0.048, 0.60, 1.16, -0.20),
                        (0.048, 0.60, 1.16, 0.20), (0.055, 0.10, 1.53, 0)):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(x + dx, y, z),
                                            vertices=18)
        parts.append(bpy.context.object)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105, location=(x, y, 1.68), segments=18,
                                         ring_count=10)
    parts.append(bpy.context.object)
    for p in parts:
        p.data.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    return bpy.context.object


def bbox(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    mn = [1e9] * 3
    mx = [-1e9] * 3
    tris = 0
    for o in objs:
        ev = o.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        M = o.matrix_world
        for v in me.vertices:
            p = M @ v.co
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
        tris += len(me.polygons)
        ev.to_mesh_clear()
    return mn, mx, tris


def shoot(sc, outdir, name, loc, aim, fov=60.0):
    cd = bpy.data.cameras.new(name)
    cd.lens_unit = 'FOV'
    cd.angle = math.radians(fov)
    cd.clip_start, cd.clip_end = 0.05, 1400
    co = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(co)
    co.location = loc
    co.rotation_mode = 'QUATERNION'
    co.rotation_quaternion = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y')
    sc.camera = co
    sc.render.filepath = os.path.join(outdir, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('WROTE', sc.render.filepath, flush=True)
