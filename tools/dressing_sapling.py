"""sapling_build.py — the PROCEDURAL hero + canopy_slim candidates.

  Blender -b --python-exit-code 1 --python sapling_build.py -- <outdir> [--inspect]

WHY A PROCEDURAL CANDIDATE EXISTS AT ALL: the scanned generators solve leaf scale by
keeping instanced cards native, but their SILHOUETTE is whatever was scanned. Sapling is
the control on that — it can be asked for a 12 m oak or a 13 m column directly, and its
leaf size is a parameter in metres rather than a property inherited from a 3.4 m specimen.

LICENSE, stated because it is the reason this path is allowed: the add-on is
`sapling_tree_gen` v0.3.7, GPL-3.0-or-later, fetched from extensions.blender.org and
sha256-pinned (27a478262e1c86612a9c3daffe7f4dce2802f5bc2294033462e5adc6d9c0080f). GPL binds
the ADD-ON CODE, not the geometry it generates, so the trees carry NO attribution
obligation. It is NOT bundled in Blender 5.1 (verified: bpy.ops.curve.tree_add.poll() fails
on a stock 5.1.1 — and note that a bare hasattr() on bpy.ops returns True regardless, which
is a lazy-attribute artifact and not evidence).
Bark: PolyHaven `jolcham_oak_bark_01`, CC0. Leaves: the single-leaf ALPHA ATLAS PolyHaven
ships with `island_tree_01`, CC0 — 8 individual leaves in a grid, so one atlas cell is one
leaf and a card's size in metres is set by leafScale, not inherited.
"""
import bpy, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_rig as rig

S = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
INSPECT = '--inspect' in argv
os.makedirs(OUT, exist_ok=True)
BARK = os.path.join(S, 'tex_extra')
LEAF = os.path.join(S, 'ph', 'island_tree_01', 'textures')

sys.path.insert(0, os.path.join(S, 'sapling_ext'))


def enable_sapling():
    import importlib
    m = importlib.import_module('sapling_ext')
    if hasattr(m, 'register'):
        try:
            m.register()
        except Exception as e:
            print('register', e)
    return m


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


def mat_bark():
    m = bpy.data.materials.new('mat_bark_oak_cc0')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    co = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (2.5, 2.5, 2.5)
    nt.links.new(co.outputs['Object'], mp.inputs['Vector'])
    d = nt.nodes.new('ShaderNodeTexImage')
    d.image = bpy.data.images.load(os.path.join(BARK, 'jolcham_oak_bark_01_diff_1k.jpg'))
    d.projection = 'BOX'
    d.projection_blend = 0.3
    nt.links.new(mp.outputs['Vector'], d.inputs['Vector'])
    nt.links.new(d.outputs['Color'], b.inputs['Base Color'])
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = bpy.data.images.load(os.path.join(BARK, 'jolcham_oak_bark_01_nor_gl_1k.jpg'))
    n.image.colorspace_settings.name = 'Non-Color'
    n.projection = 'BOX'
    n.projection_blend = 0.3
    nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(n.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.88
    return m


def mat_leaf(cell=(0, 0), grid=(5, 2)):
    """one atlas CELL per leaf card: the size of a leaf is leafScale, not the atlas"""
    m = bpy.data.materials.new('mat_leaf_cc0')
    m.use_nodes = True
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else m.blend_method
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    uv = nt.nodes.new('ShaderNodeUVMap')
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


def build(name, params):
    rig.scene()
    enable_sapling()
    bpy.ops.curve.tree_add(**params)
    tree = bpy.data.objects.get('tree')
    leaves = bpy.data.objects.get('leaves')
    if tree is None:
        raise SystemExit('sapling produced no tree: ' + str([o.name for o in bpy.data.objects]))
    bark = mat_bark()
    tree.data.materials.clear()
    tree.data.materials.append(bark)
    if leaves is not None:
        lm = mat_leaf()
        leaves.data.materials.clear()
        leaves.data.materials.append(lm)
        if INSPECT:
            print('LEAF UV LAYERS', [u.name for u in leaves.data.uv_layers],
                  'polys', len(leaves.data.polygons))
    return tree, leaves


def run(cid, params, label):
    tree, leaves = build(cid, params)
    rig.ground()
    objs = [o for o in (tree, leaves) if o]
    mn, mx, tris = rig.bbox(objs)
    for o in objs:
        o.location.z -= mn[2]
    bpy.context.view_layer.update()
    H, W = mx[2] - mn[2], max(mx[0] - mn[0], mx[1] - mn[1])
    rig.human(-max(1.6, W * 0.42) - 1.2, 0.6)
    sc = bpy.context.scene
    d = H * 1.35 + 6.0
    rig.shoot(sc, OUT, cid + '-wide', (-d * 0.72, -d * 0.72, 1.65), (0, 0, H * 0.46), 60)
    rig.shoot(sc, OUT, cid + '-close', (-5.0, -5.0, 1.65), (0, 0, min(H * 0.55, 7.0)), 60)
    r = dict(id=cid, label=label, asset='sapling_tree_gen v0.3.7 (GPL-3.0, geometry unencumbered)',
             spec='procedural', height_m=round(H, 3), width_m=round(W, 3),
             slenderness=round(H / max(W, 1e-6), 2), tris=tris,
             leaf_card_m=params['leafScale'],
             leaf_polys=len(leaves.data.polygons) if leaves else 0)
    print('CAND', cid, r, flush=True)
    return r


meta = [run('I-sapling-oak', OAK, 'HERO CAND: Sapling procedural oak, CC0 bark + leaf atlas'),
        run('J-sapling-column', COLUMN,
            'canopy_slim CAND: Sapling procedural column, CC0 bark + leaf atlas')]
p = os.path.join(OUT, 'candidates.json')
old = json.load(open(p)) if os.path.exists(p) else []
by = {m['id']: m for m in old}
by.update({m['id']: m for m in meta})
json.dump([by[k] for k in sorted(by)], open(p, 'w'), indent=1)
print('DONE')
