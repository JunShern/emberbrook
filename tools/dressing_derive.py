"""derive_build.py — build the DERIVED library assets: the heroes and the slims.

  Blender -b --python-exit-code 1 --python derive_build.py -- <srcdir> <outdir> [id ...]

A derived asset is not a new scan. It is either
  SKELETON-DERIVED  — a shipped generator whose SKELETON CURVE is scaled (which grows the
                      tree while its instanced leaf cards stay at native size, the whole
                      point of this phase) plus recorded generator-input overrides; or
  PROCEDURAL        — a Sapling tree, skinned with CC0 bark and the CC0 single-leaf atlas,
                      whose leaf size is SET in metres rather than inherited from a 3.4 m
                      specimen.
Both come out through the same normalize-and-gate path as the scans: one named collection,
origin at ground, textures packed, then tools/dressing_verify.py.

LICENSE: the Sapling add-on is GPL-3.0 and that binds its CODE, not the geometry it
generates, so the procedural assets carry NO attribution obligation. Bark is PolyHaven
`jolcham_oak_bark_01` (CC0); leaves are the single-leaf alpha atlas PolyHaven ships with
`island_tree_01` (CC0).
"""
import bpy, sys, os, json, re
from mathutils import Matrix

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
sys.path.insert(0, os.path.join(S, 'sapling_ext'))
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
ONLY = set(argv[2:])
os.makedirs(OUT, exist_ok=True)
BARK = os.path.join(S, 'tex_extra')
LEAF = os.path.join(S, 'ph', 'island_tree_01', 'textures')
MAXRES = 1024
ALPHA_HINT = re.compile(r'(alpha|opacity)', re.I)

SKELETON = {
    'hero_broad_12m': dict(base='island_tree_01', gn='island_tree_01_geometry_nodes',
                           scale=(3.0, 3.0, 3.0),
                           overrides={'density_multiplier': 170.0, 'branch_density': 2.4}),
    'slim_skeleton_12m': dict(base='island_tree_01', gn='island_tree_01_geometry_nodes',
                              scale=(0.6, 0.6, 3.0),
                              overrides={'density_multiplier': 190.0,
                                         'branch_density': 2.2}),
}
OAK = dict(levels=4, scale=11.0, scaleV=1.0, shape='7',
           customShape=(0.7, 1.0, 0.35, 0.6), branches=(0, 45, 25, 12),
           segSplits=(0.2, 0.35, 0.3, 0.0), splitAngle=(28, 32, 30, 0),
           baseSize=0.28, ratio=0.018, ratioPower=1.15, curveRes=(8, 6, 4, 3),
           curve=(0, -25, -25, 0), curveV=(60, 80, 80, 80),
           downAngle=(0, 60, 50, 45), downAngleV=(0, -40, 20, 10),
           leaves=28, leafScale=0.14, leafScaleX=0.6, leafShape='hex', leafDist='6',
           bevel=True, showLeaves=True, useArm=False)
COLUMN = dict(levels=3, scale=12.0, scaleV=0.8, shape='4', branches=(0, 55, 28, 12),
              baseSize=0.12, ratio=0.014, ratioPower=1.3,
              downAngle=(0, 20, 25, 30), downAngleV=(0, 8, 10, 10),
              attractUp=(0, 3.0, 2.5, 2.0), curve=(0, -8, -8, 0),
              curveV=(30, 40, 40, 40), curveRes=(10, 5, 3, 2),
              segSplits=(0.1, 0.15, 0.1, 0), splitAngle=(12, 14, 12, 0),
              length=(1, 0.28, 0.32, 0.4), lengthV=(0, 0.12, 0.1, 0),
              leaves=22, leafScale=0.10, leafScaleX=0.55, leafShape='hex',
              bevel=True, showLeaves=True, useArm=False)
PROC = {'slim_poplar_14m': COLUMN, 'mid_broad_13m': OAK}


def pack_textures():
    n = 0
    tmp = os.path.join(OUT, '_tex')
    os.makedirs(tmp, exist_ok=True)
    for im in list(bpy.data.images):
        if not im.users or im.source == 'GENERATED' or im.size[0] == 0:
            continue
        w, h = im.size
        sc = min(1.0, MAXRES / max(w, h))
        if sc < 1.0:
            im.scale(max(1, int(w * sc)), max(1, int(h * sc)))
        alpha = bool(ALPHA_HINT.search(im.name))
        fmt = 'PNG' if alpha else 'JPEG'
        safe = re.sub(r'[^A-Za-z0-9_.-]', '_', os.path.splitext(im.name)[0]) + (
            '.png' if alpha else '.jpg')
        p = os.path.join(tmp, safe)
        im.file_format = fmt
        iset = bpy.context.scene.render.image_settings
        iset.file_format = fmt
        # save_render writes with the SCENE's settings, and im.scale() makes every image
        # dirty -- setting im.file_format alone silently writes PNG (see the DAYLOG)
        if alpha:
            iset.color_mode, iset.color_depth, iset.compression = 'RGBA', '8', 90
        else:
            iset.color_mode, iset.quality = 'RGB', 92
        try:
            im.save_render(p) if im.is_dirty else im.save(filepath=p)
        except Exception as e:
            print('  IMG-FAIL', im.name, e)
            continue
        im.filepath = p
        im.source = 'FILE'
        im.reload()
        im.pack()
        n += 1
    return n


def seat_and_write(aid, tops):
    """origin at ground per object, iterated, then write with the dependency graph"""
    old = bpy.data.collections.get(aid)
    if old is not None:
        old.name = aid + '_SRC_DISCARDED'
    col = bpy.data.collections.new(aid)
    assert col.name == aid, f'collection name collision: {col.name}'
    bpy.context.scene.collection.children.link(col)
    for o in tops:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    for _ in range(4):
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        worst = 0.0
        for o in tops:
            ev = o.evaluated_get(dg)
            try:
                me = ev.to_mesh()
            except Exception:
                continue
            if not me or not len(me.vertices):
                continue
            M = o.matrix_world
            P = [M @ v.co for v in me.vertices]
            mn = [min(p[i] for p in P) for i in range(3)]
            mx = [max(p[i] for p in P) for i in range(3)]
            ev.to_mesh_clear()
            dx, dy, dz = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]
            worst = max(worst, abs(dx), abs(dy), abs(dz))
            o.location.x -= dx
            o.location.y -= dy
            o.location.z -= dz
        if worst < 1e-4:
            break
    n = pack_textures()
    dst = os.path.join(OUT, aid + '.blend')
    bpy.data.libraries.write(dst, {col}, fake_user=True, compress=True)
    print(f'DERIVED {aid}: {len(tops)} objs, {n} textures, '
          f'{os.path.getsize(dst)/1e6:.2f} MB', flush=True)
    return dst


def build_skeleton(aid, spec):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=os.path.join(SRC, spec['base'],
                                                   spec['base'] + '.blend'))
    o = bpy.data.objects[spec['gn']]
    o.data.transform(Matrix.Diagonal((*spec['scale'], 1.0)))
    applied = {}
    for m in o.modifiers:
        if m.type != 'NODES' or not m.node_group:
            continue
        for it in m.node_group.interface.items_tree:
            if getattr(it, 'item_type', '') != 'SOCKET' or it.in_out != 'INPUT':
                continue
            if it.name in spec['overrides']:
                before = m[it.identifier]
                m[it.identifier] = spec['overrides'][it.name]
                applied[it.name] = dict(before=round(float(before), 4),
                                        after=spec['overrides'][it.name])
    o.update_tag()
    print(f'  overrides {applied}')
    return seat_and_write(aid, [o]), applied


def mat_bark():
    m = bpy.data.materials.new('mat_bark_oak_cc0')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    co = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (2.5, 2.5, 2.5)
    nt.links.new(co.outputs['Object'], mp.inputs['Vector'])
    for fn, sock, ncol in (('jolcham_oak_bark_01_diff_1k.jpg', 'Base Color', False),
                           ('jolcham_oak_bark_01_nor_gl_1k.jpg', None, True)):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(os.path.join(BARK, fn))
        t.projection = 'BOX'
        t.projection_blend = 0.3
        if ncol:
            t.image.colorspace_settings.name = 'Non-Color'
        nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
        if sock:
            nt.links.new(t.outputs['Color'], b.inputs[sock])
        else:
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nt.links.new(t.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.88
    return m


def mat_leaf(cell=(0, 0), grid=(5, 2)):
    m = bpy.data.materials.new('mat_leaf_cc0')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'leafUV'
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0 / grid[0], 1.0 / grid[1], 1.0)
    mp.inputs['Location'].default_value = (cell[0] / grid[0], cell[1] / grid[1], 0.0)
    nt.links.new(uv.outputs['UV'], mp.inputs['Vector'])
    d = nt.nodes.new('ShaderNodeTexImage')
    d.image = bpy.data.images.load(os.path.join(LEAF, 'island_tree_01_leaves_diff_2k.png'))
    d.extension = 'CLIP'
    nt.links.new(mp.outputs['Vector'], d.inputs['Vector'])
    nt.links.new(d.outputs['Color'], b.inputs['Base Color'])
    a = nt.nodes.new('ShaderNodeTexImage')
    a.image = bpy.data.images.load(os.path.join(LEAF, 'island_tree_01_leaves_alpha_2k.png'))
    a.image.colorspace_settings.name = 'Non-Color'
    a.extension = 'CLIP'
    nt.links.new(mp.outputs['Vector'], a.inputs['Vector'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(a.outputs['Color'], mix.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(b.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    b.inputs['Roughness'].default_value = 0.72
    try:
        b.inputs['Subsurface Weight'].default_value = 0.28
        b.inputs['Subsurface Radius'].default_value = (0.55, 0.32, 0.08)
    except Exception:
        pass
    return m


def build_proc(aid, params):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import importlib
    m = importlib.import_module('sapling_ext')
    try:
        m.register()
    except Exception:
        pass
    bpy.ops.curve.tree_add(**params)
    tree = bpy.data.objects.get('tree')
    leaves = bpy.data.objects.get('leaves')
    if tree is None:
        raise SystemExit('sapling produced no tree')
    # the curve MUST keep its bevel or it renders as a zero-width line -- the treeline
    # arm was withheld from checkpoint 2 for exactly this
    assert tree.data.bevel_depth > 0 or tree.data.bevel_object or params.get('bevel'), \
        'tree curve has no bevel: it would render invisible'
    tree.name = aid + '_trunk'
    tree.data.materials.clear()
    tree.data.materials.append(mat_bark())
    tops = [tree]
    if leaves is not None:
        leaves.name = aid + '_leaves'
        leaves.data.materials.clear()
        leaves.data.materials.append(mat_leaf())
        tops.append(leaves)
    return seat_and_write(aid, tops), {}


report = {}
for aid, spec in SKELETON.items():
    if ONLY and aid not in ONLY:
        continue
    path, applied = build_skeleton(aid, spec)
    report[aid] = dict(path=path, overrides=applied, kind='skeleton')
for aid, params in PROC.items():
    if ONLY and aid not in ONLY:
        continue
    path, _ = build_proc(aid, params)
    report[aid] = dict(path=path, kind='procedural', leaf_card_m=params['leafScale'])
json.dump(report, open(os.path.join(OUT, 'derived.json'), 'w'), indent=1)
print('DONE')
