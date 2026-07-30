# char_inspect.py — headless structural report for a character GLB/FBX.
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/char_inspect.py -- a.glb [b.glb ...]
#
# The factory's acceptance instrument: whatever produced a character (Tripo via
# tools/gen3d.mjs, the web app, or a hand build), this answers the same four
# questions about the file the runtime will actually load — how heavy is the
# mesh, is there a rig and whose bone names does it use, are there clips, and
# what do the textures weigh. Pass several files to get them side by side.
import bpy, sys, os, json

def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def load(p):
    ext = os.path.splitext(p)[1].lower()
    if ext in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=p)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=p)
    else:
        raise SystemExit('unsupported: ' + p)

MIXAMO_HINTS = ('mixamorig', 'Hips', 'Spine', 'LeftArm', 'RightUpLeg')

def report(p):
    clear(); load(p)
    verts = tris = 0
    meshes = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        m = o.data
        m.calc_loop_triangles()
        verts += len(m.vertices); tris += len(m.loop_triangles)
        quads = sum(1 for f in m.polygons if len(f.vertices) == 4)
        ngons = sum(1 for f in m.polygons if len(f.vertices) > 4)
        meshes.append({
            'name': o.name, 'verts': len(m.vertices), 'tris': len(m.loop_triangles),
            'polys': len(m.polygons), 'quads': quads, 'ngons': ngons,
            'uv_layers': [uv.name for uv in m.uv_layers],
            'vgroups': len(o.vertex_groups),
            'armature_mod': any(mo.type == 'ARMATURE' for mo in o.modifiers),
        })

    arms = []
    for o in bpy.data.objects:
        if o.type != 'ARMATURE':
            continue
        names = [b.name for b in o.data.bones]
        roots = [b.name for b in o.data.bones if b.parent is None]
        arms.append({
            'name': o.name, 'bones': len(names), 'roots': roots,
            'naming': 'mixamo' if any(h.lower() in n.lower() for n in names for h in MIXAMO_HINTS) else 'other',
            'sample': names[:14],
        })

    mats = []
    for m in bpy.data.materials:
        imgs = []
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
                    imgs.append(n.image.name)
        mats.append({'name': m.name, 'images': imgs})
    images = [{'name': i.name, 'size': list(i.size), 'channels': i.depth,
               'bytes': (i.packed_file.size if i.packed_file else None)}
              for i in bpy.data.images if i.size[0]]

    clips = [{'name': a.name, 'frames': [round(v) for v in a.frame_range],
              'fcurves': len(a.fcurves)} for a in bpy.data.actions]

    # world-space bounds of everything visible => real-world height check
    lo = [1e9] * 3; hi = [-1e9] * 3
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ __import__('mathutils').Vector(c)
            for i in range(3):
                lo[i] = min(lo[i], w[i]); hi[i] = max(hi[i], w[i])
    dims = [round(hi[i] - lo[i], 4) for i in range(3)] if hi[0] > -1e8 else None

    return {
        'file': os.path.relpath(p), 'mb': round(os.path.getsize(p) / 1048576, 2),
        'totals': {'verts': verts, 'tris': tris, 'meshes': len(meshes)},
        'dims_xyz': dims, 'min_y': round(lo[1], 4) if dims else None,
        'meshes': meshes, 'armatures': arms, 'materials': mats,
        'images': images, 'clips': clips,
    }

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = [report(os.path.abspath(a)) for a in argv]
print('\n===CHAR_INSPECT_JSON===')
print(json.dumps(out, indent=2))
for r in out:
    a = r['armatures']
    print(f"\n{r['file']}  {r['mb']} MB")
    print(f"  mesh    {r['totals']['verts']:,} v / {r['totals']['tris']:,} tri "
          f"across {r['totals']['meshes']} object(s); dims {r['dims_xyz']}")
    print(f"  rig     " + (', '.join(f"{x['name']} {x['bones']} bones ({x['naming']})" for x in a) if a else 'NONE'))
    print(f"  clips   " + (', '.join(f"{c['name']} {c['frames']}" for c in r['clips']) if r['clips'] else 'none'))
    print(f"  tex     " + (', '.join(f"{i['name']} {i['size'][0]}x{i['size'][1]}" for i in r['images']) if r['images'] else 'none')
          + f"   materials {len(r['materials'])}")
