"""hero_compare.py — the HERO-TREE and canopy_slim candidates, under probe2-c's own light.

  Blender -b --python-exit-code 1 --python hero_compare.py -- <outdir> [only ...]

Judged against `docs/qa/emberbrook/styleprobe/probe2-c.png`, so the light is copied from
`mill_probe_r2.py` rather than re-invented: EMB_sun 3.0 W (1.0,0.70,0.42) at elevation 62 /
rotation 212, a 0.30 W warm bounce sun from below-behind, MULTIPLE_SCATTERING sky at world
0.30, Cycles with 32 transparent bounces, AgX Medium High Contrast, film exposure 0.10 —
and the SAME autumn hue/value/subsurface regrade the probe applied to the canopies. A
candidate that only looks good under a different key has not been compared to anything.

TWO FRAMES PER CANDIDATE, because the defect being fixed only exists in one of them:
  wide   — the whole tree beside a 1.80 m figure, the silhouette question
  close  — 7 m from the trunk at eye height, which is where "leaf cards read large"
           was seen and is the only frame that can settle it
"""
import bpy, sys, os, math, json
from mathutils import Vector, Euler, Matrix

S = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(S, 'ph')
argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
ONLY = set(argv[1:])
os.makedirs(OUT, exist_ok=True)
SAMPLES = int(os.environ.get('CMP_SAMPLES', '96'))
RESX, RESY = int(os.environ.get('CMP_RESX', '1200')), int(os.environ.get('CMP_RESY', '900'))

# the probe's own autumn regrade, copied verbatim so the comparison is like-for-like
AUTUMN = {
    'island_tree_01': dict(hue=0.492, sat=1.05, val=0.88, mix_col=(0.46, 0.33, 0.09),
                           mix_fac=0.22, sss=0.28),
    'tree_small_02': dict(hue=0.470, sat=1.20, val=0.92, mix_col=(0.60, 0.24, 0.05),
                          mix_fac=0.55, sss=0.30),
    'jacaranda_tree': dict(hue=0.500, sat=0.98, val=0.92, mix_col=(0.50, 0.31, 0.08),
                           mix_fac=0.38, sss=0.26),
}

# id: (blend id, gn object, kind, scale-spec, label)
#   obj:sx,sy,sz  scales the OBJECT   (round-2's method — leaves stretch with the tree)
#   crv:sx,sy,sz  scales the SKELETON (leaves are instanced afterwards, untouched)
CANDIDATES = [
    ('A-control-2.6x', 'island_tree_01', 'island_tree_01_geometry_nodes', 'obj:2.6,2.6,2.6',
     'ROUND-2 CONTROL: island_tree_01 object-scaled 2.6x'),
    ('B-skeleton-2.5', 'island_tree_01', 'island_tree_01_geometry_nodes', 'crv:2.5,2.5,2.5',
     'HERO CAND: skeleton grown 2.5x, leaves native'),
    ('C-skeleton-3.0', 'island_tree_01', 'island_tree_01_geometry_nodes', 'crv:3.0,3.0,3.0',
     'HERO CAND: skeleton grown 3.0x, leaves native'),
    ('D-jacaranda-native', 'jacaranda_tree', None, 'obj:1,1,1',
     'HERO CAND: jacaranda_tree at native 19.47 m'),
    ('E-jacaranda-0.7', 'jacaranda_tree', None, 'obj:0.7,0.7,0.7',
     'HERO CAND: jacaranda_tree at 0.7 (13.6 m)'),
    ('F-slim-control', 'island_tree_01', 'island_tree_01_geometry_nodes', 'obj:1.37,1.37,2.6',
     'ROUND-2 SLIM CONTROL: object stretch to village size'),
    ('G-slim-skeleton', 'island_tree_01', 'island_tree_01_geometry_nodes', 'crv:0.6,0.6,3.0',
     'canopy_slim CAND: skeleton columnar 11.7 m, leaves native'),
    ('H-slim-skeleton-tight', 'island_tree_01', 'island_tree_01_geometry_nodes',
     'crv:0.5,0.5,3.4', 'canopy_slim CAND: skeleton columnar, tighter'),
    # REFILLED: growing the skeleton grows the crown's VOLUME faster than the generator
    # adds foliage into it, so C reads bare. These raise the generator's own density inputs
    # to refill it, and hold leaf_scale_multiplier at its native value so the CARD SIZE --
    # the thing this whole exercise is about -- is not quietly bought back.
    ('K-skeleton-3.0-refilled', 'island_tree_01', 'island_tree_01_geometry_nodes',
     'crv:3.0,3.0,3.0', 'HERO CAND: skeleton 3.0x, canopy refilled at native leaf size',
     dict(density_multiplier=170.0, branch_density=2.4)),
    ('L-slim-skeleton-refilled', 'island_tree_01', 'island_tree_01_geometry_nodes',
     'crv:0.6,0.6,3.0', 'canopy_slim CAND: columnar, canopy refilled at native leaf size',
     dict(density_multiplier=190.0, branch_density=2.2)),
]


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
    """the probe's scanned ground pair, so the floor under the tree is the ratified floor"""
    bpy.ops.mesh.primitive_plane_add(size=300)
    o = bpy.context.object
    m = bpy.data.materials.new('mat_ground_scan')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tex = os.path.join(PH, 'tex')
    d = nt.nodes.new('ShaderNodeTexImage')
    try:
        d.image = bpy.data.images.load(os.path.join(tex, 'leafy_grass_Diffuse.jpg'))
    except Exception as e:
        print('ground tex', e)
    n = nt.nodes.new('ShaderNodeTexImage')
    try:
        n.image = bpy.data.images.load(os.path.join(tex, 'leafy_grass_nor_gl.jpg'))
        n.image.colorspace_settings.name = 'Non-Color'
    except Exception:
        n = None
    co = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (60, 60, 60)
    nt.links.new(co.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], d.inputs['Vector'])
    nt.links.new(d.outputs['Color'], b.inputs['Base Color'])
    if n:
        nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(n.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.92
    o.data.materials.append(m)
    return o


def human(x, y):
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


def retint(objs, kw):
    mats = set()
    for ob in objs:
        for slot in ob.material_slots:
            if slot.material:
                mats.add(slot.material)
        # instanced leaf materials live on the generator's source collection
        for m in getattr(ob, 'modifiers', []):
            if m.type == 'NODES' and m.node_group:
                for it in m.node_group.interface.items_tree:
                    if getattr(it, 'socket_type', '') == 'NodeSocketCollection':
                        c = m.get(it.identifier)
                        if c:
                            for o2 in c.all_objects:
                                for s2 in o2.material_slots:
                                    if s2.material:
                                        mats.add(s2.material)
    for m in mats:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not b:
            continue
        inp = b.inputs['Base Color']
        if inp.links:
            src = inp.links[0].from_socket
            hs = nt.nodes.new('ShaderNodeHueSaturation')
            hs.inputs['Hue'].default_value = kw.get('hue', 0.5)
            hs.inputs['Saturation'].default_value = kw.get('sat', 1.0)
            hs.inputs['Value'].default_value = kw.get('val', 1.0)
            nt.links.new(src, hs.inputs['Color'])
            out = hs.outputs['Color']
            if kw.get('mix_col') and kw.get('mix_fac'):
                mx = nt.nodes.new('ShaderNodeMixRGB')
                mx.blend_type = 'COLOR'
                mx.inputs['Fac'].default_value = kw['mix_fac']
                mx.inputs['Color2'].default_value = (*kw['mix_col'], 1)
                nt.links.new(out, mx.inputs['Color1'])
                out = mx.outputs['Color']
            nt.links.new(out, inp)
        if kw.get('sss'):
            low = m.name.lower()
            if any(h in low for h in ('leaf', 'leaves', 'grass', 'blad', 'island', 'jacaranda')):
                try:
                    b.inputs['Subsurface Weight'].default_value = kw['sss']
                    b.inputs['Subsurface Radius'].default_value = (0.55, 0.32, 0.08)
                except Exception:
                    pass


def apply_gn(o, over):
    """set generator inputs by socket NAME (identifiers are Input_N and not readable)"""
    if not over:
        return
    for m in o.modifiers:
        if m.type != 'NODES' or not m.node_group:
            continue
        for it in m.node_group.interface.items_tree:
            if getattr(it, 'item_type', '') != 'SOCKET' or it.in_out != 'INPUT':
                continue
            if it.name in over:
                before = m[it.identifier]
                m[it.identifier] = over[it.name]
                print(f'  GN {it.name}: {before} -> {over[it.name]}')
    o.update_tag()


def load_tree(aid, gn, spec, gnover=None):
    """append the ONE object that is the plant — never the whole source collection"""
    blend = os.path.join(PH, aid, aid + '.blend')
    name = gn or (aid + '_LOD0')
    with bpy.data.libraries.load(blend, link=False) as (df, dt):
        want = [name] if name in df.objects else []
        if not want:
            raise SystemExit(f'no object {name} in {blend}: {list(df.objects)[:8]}')
        dt.objects = want
    o = dt.objects[0]
    bpy.context.scene.collection.objects.link(o)
    kind, vals = spec.split(':')
    sx, sy, sz = (float(v) for v in vals.split(','))
    if kind == 'obj':
        o.scale = (sx, sy, sz)
    else:
        o.data.transform(Matrix.Diagonal((sx, sy, sz, 1.0)))
    o.location = (0, 0, 0)
    apply_gn(o, gnover)
    bpy.context.view_layer.update()
    return o


def measure(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    M = o.matrix_world
    P = [M @ v.co for v in me.vertices]
    mn = [min(p[i] for p in P) for i in range(3)]
    mx = [max(p[i] for p in P) for i in range(3)]
    tris = len(me.polygons)
    ev.to_mesh_clear()
    return mn, mx, tris


def shoot(sc, name, loc, aim, fov):
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
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('WROTE', sc.render.filepath, flush=True)


meta = []
for cand in CANDIDATES:
    cid, aid, gn, spec, label = cand[:5]
    gnover = cand[5] if len(cand) > 5 else None
    if ONLY and cid not in ONLY:
        continue
    sc = scene()
    ground()
    o = load_tree(aid, gn, spec, gnover)
    if aid in AUTUMN:
        retint([o], AUTUMN[aid])
    mn, mx, tris = measure(o)
    o.location = (0, 0, -mn[2])
    bpy.context.view_layer.update()
    H = mx[2] - mn[2]
    W = max(mx[0] - mn[0], mx[1] - mn[1])
    human(-max(1.6, W * 0.42) - 1.2, 0.6)
    # WIDE: the whole tree in frame at probe2-c's 60 deg lens, camera at eye height
    d = H * 1.35 + 6.0
    shoot(sc, cid + '-wide', (-d * 0.72, -d * 0.72, 1.65), (0, 0, H * 0.46), 60)
    # CLOSE: 7 m out at eye height, aimed into the crown — where the defect lives
    shoot(sc, cid + '-close', (-5.0, -5.0, 1.65), (0, 0, min(H * 0.55, 7.0)), 60)
    meta.append(dict(id=cid, label=label, asset=aid, spec=spec, gn=gnover,
                     height_m=round(H, 3),
                     width_m=round(W, 3), slenderness=round(H / max(W, 1e-6), 2), tris=tris))
    print('CAND', cid, meta[-1], flush=True)

p = os.path.join(OUT, 'candidates.json')
old = json.load(open(p)) if os.path.exists(p) else []
by = {m['id']: m for m in old}
by.update({m['id']: m for m in meta})
json.dump([by[k] for k in sorted(by)], open(p, 'w'), indent=1)
print('DONE')
