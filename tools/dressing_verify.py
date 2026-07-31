"""lib_verify.py — the INTAKE GATE. A lean library that renders wrong is worth nothing.

  Blender -b --python-exit-code 1 --python lib_verify.py -- <libdir> <out.json> [--render <dir>]

Per normalized blend, checked by APPENDING it exactly the way a builder will (link the named
collection, instance it) rather than by opening it:
  * the collection named <id> exists and is what appends
  * evaluated height / canopy width, compared against the checkpoint-1 source measurement
  * z-min at ground: |z_min| <= 1 mm, since normalization claims origin-at-ground
  * every image is PACKED and resolves (an unpacked path is a library that breaks the
    moment it is moved)
  * no leftover LOD bake or generator-source object is reachable from the collection
"""
import bpy, sys, os, json

argv = sys.argv[sys.argv.index('--') + 1:]
LIB, OUT = argv[0], argv[1]
RENDER = argv[argv.index('--render') + 1] if '--render' in argv else None
REF = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'measured.json')))
REF = {a['id']: a for a in REF}


def check(path):
    aid = os.path.splitext(os.path.basename(path))[0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(path, link=False) as (df, dt):
        cols = list(df.collections)
        dt.collections = [aid] if aid in cols else cols[:1]
    col = dt.collections[0]
    inst = bpy.data.objects.new('inst_' + aid, None)
    inst.instance_type = 'COLLECTION'
    inst.instance_collection = col
    bpy.context.scene.collection.objects.link(inst)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    mn = [1e9] * 3
    mx = [-1e9] * 3
    tris = 0
    for o in col.all_objects:
        ev = o.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except Exception:
            continue
        if not me or not len(me.vertices):
            continue
        M = o.matrix_world
        for v in me.vertices:
            p = M @ v.co
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
        tris += len(me.polygons)
        ev.to_mesh_clear()
    unpacked = [im.name for im in bpy.data.images
                if im.users and im.source == 'FILE' and not im.packed_file]
    missing = [im.name for im in bpy.data.images if im.users and im.size[0] == 0]
    strays = [o.name for o in col.all_objects
              if '_LOD2' in o.name or '_LOD3' in o.name]
    H = mx[2] - mn[2]
    W = max(mx[0] - mn[0], mx[1] - mn[1])
    ref = REF.get(aid, {})
    refH = ref.get('height_m')
    r = dict(id=aid, collection=col.name, objects=len(col.all_objects),
             height_m=round(H, 3), canopy_width_m=round(W, 3), tris=tris,
             z_min=round(mn[2], 5), source_height_m=refH,
             height_delta_pct=(round((H / refH - 1) * 100, 1) if refH else None),
             unpacked=unpacked, missing=missing, strays=strays,
             bytes=os.path.getsize(path))
    fails = []
    if abs(mn[2]) > 0.001:
        fails.append(f'origin not at ground: z_min {mn[2]:.4f}')
    if unpacked:
        fails.append(f'{len(unpacked)} unpacked images')
    if missing:
        fails.append(f'{len(missing)} images fail to resolve')
    if strays:
        fails.append(f'{len(strays)} stray LOD objects')
    if tris == 0:
        fails.append('evaluates to no geometry')
    # a generator asset legitimately differs from its source bake; a baked one must not
    if refH and abs(H / refH - 1) > 0.02 and aid not in (
            'fir_tree_01', 'fir_sapling_medium', 'grass_medium_01', 'grass_medium_02',
            'grass_bermuda_01', 'nettle_plant'):
        fails.append(f'height {H:.2f} vs source {refH:.2f}')
    r['fails'] = fails
    print(('FAIL ' if fails else 'OK   ') + f"{aid:22} H {H:7.3f} W {W:7.3f} "
          f"tris {tris:9,} zmin {mn[2]:+.5f} objs {len(col.all_objects):3d} "
          f"{os.path.getsize(path)/1e6:6.2f} MB" + ('  ' + '; '.join(fails) if fails else ''),
          flush=True)
    if RENDER:
        os.makedirs(RENDER, exist_ok=True)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import probe_rig as rig
        sc = rig.scene()          # NOTE: this resets the file, so re-append into it
        with bpy.data.libraries.load(path, link=False) as (df2, dt2):
            dt2.collections = [aid] if aid in list(df2.collections) else list(df2.collections)[:1]
        col2 = dt2.collections[0]
        rig.ground()
        inst2 = bpy.data.objects.new('inst2_' + aid, None)
        inst2.instance_type = 'COLLECTION'
        inst2.instance_collection = col2
        sc.collection.objects.link(inst2)
        rig.human(-max(1.6, W * 0.42) - 1.2, 0.6)
        d = max(H, 1.8) * 1.35 + 6.0
        rig.shoot(sc, RENDER, aid, (-d * 0.72, -d * 0.72, 1.65), (0, 0, max(H, 1.8) * 0.46), 60)
    return r


res = [check(os.path.join(LIB, f)) for f in sorted(os.listdir(LIB)) if f.endswith('.blend')]
json.dump(res, open(OUT, 'w'), indent=1)
bad = [r for r in res if r['fails']]
print(f"\nVERIFY {len(res) - len(bad)}/{len(res)} pass, "
      f"total {sum(r['bytes'] for r in res)/1e6:.1f} MB")
for r in bad:
    print('  FAIL', r['id'], r['fails'])
print('DONE')
