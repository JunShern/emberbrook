"""render_tiles.py — one TRUE-SCALE tile per candidate asset, beside a 1.80 m figure.

  Blender -b --python-exit-code 1 --python render_tiles.py -- <spec.json> <outdir> [only_id ...]

Contract that makes the tile measurable rather than merely pretty: the camera is
ORTHOGRAPHIC, axis-aligned, looking along +Y, with a stated ortho_scale — so metres map to
pixels exactly and the sidecar JSON lets the sheet compositor draw a real 1 m grid over the
render instead of an eyeballed one.

The light is the RATIFIED round-2 key (probe2-c): Cycles, warm sun 3.0 W, Nishita sky,
AgX Medium High Contrast, film exposure 0.10, world strength 0.30.  Blender 5.1 dropped
ShaderNodeTexSky.dust_density — setting it silently fails the node, which is what made
round 1's sky do nothing, so it is never touched here.

ASSETS ARE RENDERED RAW — the probe's autumn hue/value grade is NOT applied.  The library
stores the scan as delivered; grading is the dressing engine's call, per scene.
"""
import bpy, sys, os, json, math

argv = sys.argv[sys.argv.index('--') + 1:]
SPEC, OUTDIR = argv[0], argv[1]
ONLY = set(argv[2:])
os.makedirs(OUTDIR, exist_ok=True)
spec = json.load(open(SPEC))

RES_X = int(os.environ.get('TILE_RES_X', '1280'))
RES_Y = int(os.environ.get('TILE_RES_Y', '960'))
SAMPLES = int(os.environ.get('TILE_SAMPLES', '64'))
HUMAN_H = 1.80


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
    except Exception as e:
        print('GPU prefs', e)
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
    # 32 transparent bounces is not a nicety: an alpha-card canopy is dozens of
    # transparent surfaces deep and a low cap renders the inside of a tree black
    sc.cycles.transparent_max_bounces = 32
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.film_exposure = 1.0
    sc.render.resolution_x, sc.render.resolution_y = RES_X, RES_Y
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.10
    return sc


def world_sky(sc):
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.30
    sky = nt.nodes.new('ShaderNodeTexSky')
    # Blender 5.1: sky_type 'NISHITA' NO LONGER EXISTS (enum is SINGLE_SCATTERING /
    # MULTIPLE_SCATTERING / PREETHAM / HOSEK_WILKIE) and `dust_density` is GONE —
    # the round-2 probe's own sky is MULTIPLE_SCATTERING, so the tiles use it too.
    for a, v in (('sky_type', 'MULTIPLE_SCATTERING'), ('sun_elevation', math.radians(16.0)),
                 ('sun_rotation', math.radians(212.0)), ('altitude', 200.0),
                 ('air_density', 2.2), ('ozone_density', 1.4),
                 ('sun_intensity', 0.30), ('sun_disc', True)):
        try:
            setattr(sky, a, v)
        except Exception as e:
            print('sky-attr', a, e)
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


def sun():
    d = bpy.data.lights.new('SUN_key', 'SUN')
    d.energy = 3.0
    d.color = (1.0, 0.80, 0.58)
    d.angle = math.radians(1.6)
    o = bpy.data.objects.new('SUN_key', d)
    o.rotation_euler = (math.radians(52), 0, math.radians(-38))
    bpy.context.scene.collection.objects.link(o)


def mat_flat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    return m


def ground(size=400.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    o = bpy.context.object
    o.name = 'GROUND'
    o.data.materials.append(mat_flat('mat_ground', (0.20, 0.19, 0.15)))
    return o


def backdrop(cx, cz, w, h):
    """a matte card behind the lineup so silhouettes read; it is NOT lit by the key"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, 26.0, cz))
    o = bpy.context.object
    o.name = 'BACKDROP'
    o.rotation_euler = (math.radians(90), 0, 0)
    o.scale = (w * 3, h * 3, 1)
    m = bpy.data.materials.new('mat_backdrop')
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.42, 0.50, 0.60, 1)
    em.inputs['Strength'].default_value = 0.85
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    o.data.materials.append(m)
    return o


def human(x):
    """1.80 m reference figure — the scale bar the whole sheet is read against."""
    m = mat_flat('mat_ref_human', (0.62, 0.16, 0.04), rough=1.0)
    parts = []

    def cyl(r, h, z, dx=0.0):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(x + dx, 0, z),
                                            vertices=20)
        parts.append(bpy.context.object)

    def sph(r, z, dx=0.0):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(x + dx, 0, z), segments=20,
                                             ring_count=12)
        parts.append(bpy.context.object)

    cyl(0.075, 0.86, 0.43, -0.10)          # legs
    cyl(0.075, 0.86, 0.43, +0.10)
    cyl(0.155, 0.62, 1.17)                 # torso
    cyl(0.048, 0.60, 1.16, -0.20)          # arms
    cyl(0.048, 0.60, 1.16, +0.20)
    cyl(0.055, 0.10, 1.53)                 # neck
    sph(0.105, 1.68)                       # head
    for p in parts:
        p.data.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = 'REF_human_1p80'
    return o


def append_object(blend, name):
    with bpy.data.libraries.load(blend, link=False) as (df, dt):
        if name not in df.objects:
            print('MISSING-OBJ', name, 'in', blend)
            dt.objects = []
            return None
        dt.objects = [name]
    o = dt.objects[0]
    bpy.context.scene.collection.objects.link(o)
    return o


def bbox_world(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    M = o.matrix_world
    pts = [M @ v.co for v in me.vertices]
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    ev.to_mesh_clear()
    return mn, mx


def render_tile(s):
    sc = clean()
    world_sky(sc)
    sun()
    ground()
    placed = []
    x = 0.0
    items = list(s['objects']) + list(s.get('trunks', []))[:1]
    for it in items:
        o = append_object(it.get('blend', s['blend']), it['name'])
        if o is None:
            continue
        o.location = (0, 0, 0)
        o.rotation_euler = (0, 0, 0)
        mn, mx = bbox_world(o)
        w = mx[0] - mn[0]
        gap = max(0.45, 0.16 * max(mx[2] - mn[2], 0.2))
        # seat on the ground and lay out left to right, measured from the object's own bbox
        o.location = (x + gap + (-mn[0]), -(mn[1] + mx[1]) / 2.0, -mn[2])
        placed.append(dict(name=it['name'], x0=x + gap, x1=x + gap + w,
                           h=round(mx[2] - mn[2], 3), w=round(w, 3), tris=it.get('tris')))
        x = x + gap + w
    if not placed:
        return None
    H = max(p['h'] for p in placed)
    hx = -max(0.9, 0.10 * H)                       # the figure stands left of the lineup
    human(hx)
    x0, x1 = hx - 0.5, x + 0.4
    need_w = x1 - x0
    need_h = max(H, HUMAN_H) * 1.12 + 0.25
    aspect = RES_X / RES_Y
    ortho = max(need_w, need_h * aspect)
    cx = (x0 + x1) / 2.0
    cz = (need_h) / 2.0 - 0.12
    backdrop(cx, cz, ortho, ortho)
    cam_d = bpy.data.cameras.new('CAM')
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = ortho
    cam_d.clip_start, cam_d.clip_end = 0.1, 200.0
    cam = bpy.data.objects.new('CAM', cam_d)
    cam.location = (cx, -40.0, cz)
    cam.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    out = os.path.join(OUTDIR, s['id'] + '.png')
    sc.render.filepath = out
    sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    meta = dict(id=s['id'], file=out, res=[RES_X, RES_Y], ortho_scale=ortho,
                cam_x=cx, cam_z=cz, px_per_m=RES_X / ortho, placed=placed,
                category=s['category'], leaf_card_m=s.get('leaf_card_m'),
                height_m=s.get('height_m'), canopy_width_m=s.get('canopy_width_m'),
                n_variants=s.get('n_variants'), disk_mb=s.get('disk_mb'))
    json.dump(meta, open(os.path.join(OUTDIR, s['id'] + '.json'), 'w'), indent=1)
    print('TILE', s['id'], 'ortho', round(ortho, 2), 'px/m', round(RES_X / ortho, 2), flush=True)
    return meta


for s in spec:
    if ONLY and s['id'] not in ONLY:
        continue
    if os.path.exists(os.path.join(OUTDIR, s['id'] + '.json')) and os.environ.get('SKIP_DONE'):
        print('SKIP', s['id'])
        continue
    render_tile(s)
print('DONE')
