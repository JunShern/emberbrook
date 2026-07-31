"""normalize_one.py — build ONE normalized library asset for real, so the disk budget is a
measurement and not an estimate.

  Blender -b --python-exit-code 1 --python normalize_one.py -- <srcdir> <outdir> <id> [<id>...]

WHAT NORMALIZING MEANS HERE, and each clause is a measured decision from checkpoint 1:
  ONE REPRESENTATION. The source blend's top-level collection holds the generator AND both
  baked LODs as siblings, which is how the round-2 probe rendered every broadleaf three
  times. The library ships the GENERATOR where there is one (a curve plus a handful of leaf
  cards regenerates millions of triangles at evaluation time, so it is ~1 MB of geometry
  instead of ~60 MB) and the LOD0/LOD1 bakes only where there is no generator.
  ORIGIN AT GROUND. Every collection's contents are offset so the asset's own measured
  z-min sits at 0 — the builder should never have to know an asset's seating error.
  TEXTURES DOWNSAMPLED AND PACKED. 2K PNG source maps become 1K, JPEG for everything except
  ALPHA (an alpha map through JPEG gives haloed leaf edges — findings 131/143 in the
  overworld lane say the same thing), then packed into the blend so the library is one file
  per category with no external path to break.
UP AXIS: Blender is +Z up and stays +Z up; the manifest records `up: "+Z"`, and the glTF
exporter is what converts to +Y for anything that later ships in a GLB. Nothing is rotated
at intake — a rotated library is a library whose every consumer has to un-rotate it.
"""
import bpy, sys, os, json, re, shutil


argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
IDS = argv[2:]
os.makedirs(OUT, exist_ok=True)
TEXDIR = os.path.join(OUT, '_tex')
os.makedirs(TEXDIR, exist_ok=True)
MAXRES = int(os.environ.get('LIB_TEXRES', '1024'))

# id -> (generator object, extra objects to keep)  — chosen from the checkpoint-1 measurements
KEEP = {
    'island_tree_01': ('island_tree_01_geometry_nodes', []),
    'island_tree_02': ('island_tree_02_geometry_nodes', []),
    'island_tree_03': ('island_tree_03_geometry_nodes', []),
    'tree_small_02': ('tree_small_02_geometry_nodes', ['tree_small_02_trunk']),
    'jacaranda_tree': ('jacaranda_tree_geometry_nodes', []),
    'jacaranda_tree_trunk': ('__BAKED__', ['jacaranda_tree_trunk_LOD0']),
    'fir_tree_01': ('fir_tree_01_geometry_nodes', []),
    'fir_sapling_medium': ('fir_sapling_medium_geometry_nodes', []),
}
ALPHA_HINT = re.compile(r'(alpha|opacity)', re.I)
SRC_PARTS = re.compile(
    r'(_twig|_branch|_leaves|_leaf|leaf_uv|_needle|_geometry|geonodes|_dead_branch|_root)',
    re.I)
LOD_RE = re.compile(r'_LOD(\d)$', re.I)
# PER-CLASS POLICY, set from what the camera can actually resolve (checkpoint-1 heights):
#   trees/shrubs a player walks up to  -> 1k maps, LOD0 (near work) + LOD1 (scatter)
#   understory and groundcover         -> 512 maps, LOD1 only; these are 0.07-0.43 m plants
#     scattered in their thousands, and a 1k map on a 0.15 m weed is texels nobody sees
KEEP_LODS = {'LOD0', 'LOD1'}
LEAN = {'shrub_01', 'shrub_03', 'fern_02', 'nettle_plant', 'weed_plant_02', 'dandelion_01',
        'grass_medium_01', 'grass_medium_02', 'grass_bermuda_01'}
ONE_LOD = {'searsia_lucida', 'searsia_burchellii'}


def baked_keep():
    """assets with no generator ship their baked variants: LOD0 for near work, LOD1 for
       scatter. Generator SOURCE parts (twigs, branch cards, leaf cards) are excluded --
       they are inputs to a modifier that this asset does not have."""
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or SRC_PARTS.search(o.name):
            continue
        m = LOD_RE.search(o.name)
        if m and f'LOD{m.group(1)}' not in KEEP_LODS:
            continue
        out.append(o)
    return out


def _walk_tree(ng, objs, cols, seen_trees):
    """Collection Info / Object Info nodes INSIDE the node tree, recursively through nested
       groups. This is the path that matters: island_tree_01's generator exposes no
       Collection socket at all -- its leaves are referenced by a node inside the group. The
       first version only read MODIFIER inputs, deleted the leaf sources as unreferenced,
       and produced a 17 401-tri tree with no leaves that still opened without an error."""
    if ng is None or ng.name in seen_trees:
        return
    seen_trees.add(ng.name)
    for n in ng.nodes:
        for attr in ('object', 'collection'):
            v = getattr(n, attr, None)
            if isinstance(v, bpy.types.Object):
                objs.add(v)
            elif isinstance(v, bpy.types.Collection):
                cols.add(v)
        for inp in n.inputs:
            dv = getattr(inp, 'default_value', None)
            if isinstance(dv, bpy.types.Object):
                objs.add(dv)
            elif isinstance(dv, bpy.types.Collection):
                cols.add(dv)
        if getattr(n, 'node_tree', None) is not None:
            _walk_tree(n.node_tree, objs, cols, seen_trees)


def collect_sources(o, seen):
    """a generator is not self-contained: it reads source objects and instances leaf
       collections both through its MODIFIER INPUTS and from inside its NODE TREE"""
    objs, cols = set(), set()
    for m in o.modifiers:
        if m.type != 'NODES' or not m.node_group:
            continue
        for it in m.node_group.interface.items_tree:
            if getattr(it, 'item_type', '') != 'SOCKET' or it.in_out != 'INPUT':
                continue
            try:
                v = m[it.identifier]
            except Exception:
                continue
            if isinstance(v, bpy.types.Collection):
                cols.add(v)
            elif isinstance(v, bpy.types.Object):
                objs.add(v)
        _walk_tree(m.node_group, objs, cols, set())
    out = []
    for c in cols:
        for so in c.all_objects:
            objs.add(so)
    for so in objs:
        if so and so.name not in seen and so is not o:
            seen.add(so.name)
            out.append(so)
    return out


def downsize_and_pack():
    n_before = n_after = 0
    for im in list(bpy.data.images):
        if not im.users or im.source == 'GENERATED':
            continue
        w, h = im.size
        if w == 0:
            continue
        n_before += 1
        scale = min(1.0, MAXRES / max(w, h))
        if scale < 1.0:
            im.scale(max(1, int(w * scale)), max(1, int(h * scale)))
        alpha = bool(ALPHA_HINT.search(im.name))
        ext = '.png' if alpha else '.jpg'
        safe = re.sub(r'[^A-Za-z0-9_.-]', '_', os.path.splitext(im.name)[0]) + ext
        p = os.path.join(TEXDIR, safe)
        # im.scale() marks the image DIRTY, which sends it down save_render() -- and
        # save_render writes with the SCENE's image settings, not the image's. Setting
        # im.file_format alone therefore did nothing and every map packed as PNG: a 1k
        # normal map at 2.9 MB instead of 0.3 MB, which was 47.8 MB of the first budget.
        fmt = 'PNG' if alpha else 'JPEG'
        im.file_format = fmt
        iset = bpy.context.scene.render.image_settings
        iset.file_format = fmt
        if alpha:
            iset.color_mode = 'RGBA'
            iset.color_depth = '8'
            iset.compression = 90
        else:
            iset.color_mode = 'RGB'
            iset.quality = 92
        try:
            im.save_render(p) if im.is_dirty else im.save(filepath=p)
        except Exception:
            try:
                im.filepath_raw = p
                im.save()
            except Exception as e:
                print('   IMG-FAIL', im.name, e)
                continue
        im.filepath = p
        im.source = 'FILE'
        im.reload()
        im.pack()
        n_after += 1
    return n_before, n_after


report = []
for aid in (IDS or sorted(KEEP)):
    base = aid.replace('_trunk', '') if aid.endswith('_trunk') else aid
    src = os.path.join(SRC, base, base + '.blend')
    if not os.path.exists(src):
        print('MISSING', src)
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=src)
    MAXRES = 512 if aid in LEAN else int(os.environ.get('LIB_TEXRES', '1024'))
    KEEP_LODS = ({'LOD1'} if aid in LEAN or aid in ONE_LOD else {'LOD0', 'LOD1'})
    gen, extra = KEEP.get(aid, (None, []))
    keep_objs = []
    seen = set()
    if gen == '__BAKED__':
        gen = None
    if gen and gen in bpy.data.objects:
        # ONLY the generator itself. Its leaf and branch source objects are NOT collected
        # and NOT moved: they live in collections the node tree instances FROM, and
        # unlinking them to gather them into one place empties those collections -- which
        # is how island_tree_01 shipped at 21 777 tris with almost no leaves and still
        # passed a naive "does it open" check. libraries.write pulls them as dependencies.
        o = bpy.data.objects[gen]
        keep_objs.append(o)
        seen.add(o.name)
    for n in extra:
        if n in bpy.data.objects and n not in seen:
            keep_objs.append(bpy.data.objects[n])
            seen.add(n)
    if not keep_objs and not extra:
        keep_objs = baked_keep()
        seen = {o.name for o in keep_objs}
    if not keep_objs:
        print('NO KEEP SET for', aid)
        continue

    # ------------------------------------------------------------------ assemble
    # DEPENDENCIES ARE BLENDER'S JOB, NOT MINE. Two earlier versions tried to keep the
    # generator alive by hand -- moving its source objects into one flat collection, then
    # re-linking the source COLLECTIONS as children -- and both shipped a tree with no
    # leaves that opened without an error (17 401 tris instead of 1.6 M). The generators
    # reference their leaf sources from INSIDE the node tree, and hand-tracking that is a
    # losing game. `bpy.data.libraries.write` writes a datablock WITH its full dependency
    # graph, so the library is assembled by linking only the top-level objects into one
    # collection and letting the writer pull everything they need.
    tops = list(keep_objs)
    # THE SOURCE FILE ALREADY OWNS THIS NAME. bpy.data.collections.new(aid) silently
    # returned "<id>.001", the library shipped a collection nobody would look for, and the
    # consumer's fallback grabbed the first collection in the file -- a bag of leaf cards.
    # The manifest names the collection, so the collection must have that name exactly.
    old = bpy.data.collections.get(aid)
    if old is not None:
        old.name = aid + '_SRC_DISCARDED'
    col = bpy.data.collections.new(aid)
    assert col.name == aid, f'collection name collision: got {col.name}'
    bpy.context.scene.collection.children.link(col)
    for o in tops:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)

    # ------------------------------------------------- origin at ground, PER OBJECT
    # Every top-level object is seated on its own origin: (x centre, y centre, z min)
    # -> (0, 0, 0). The source file lays variants out APART, which is what made a 0.16 m
    # dandelion measure 4.21 m wide; a library must not carry the source file's layout.
    # ITERATED, because a generator's realised geometry can shift when its object moves.
    zmin = 0.0
    for _pass in range(4):
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
            dx, dy, dz = (mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0, mn[2]
            worst = max(worst, abs(dx), abs(dy), abs(dz))
            o.location.x -= dx
            o.location.y -= dy
            o.location.z -= dz
        if worst < 1e-4:
            break
    bpy.context.view_layer.update()

    nb, na = downsize_and_pack()
    dst = os.path.join(OUT, aid + '.blend')
    bpy.data.libraries.write(dst, {col}, fake_user=True, compress=True)
    sz = os.path.getsize(dst)
    srcsz = os.path.getsize(src) + sum(
        os.path.getsize(os.path.join(SRC, base, 'textures', f))
        for f in os.listdir(os.path.join(SRC, base, 'textures'))) if os.path.isdir(
            os.path.join(SRC, base, 'textures')) else os.path.getsize(src)
    report.append(dict(id=aid, objects=len(keep_objs), images=na, z_offset=round(zmin or 0, 4),
                       out_bytes=sz, src_bytes=srcsz,
                       ratio=round(srcsz / max(sz, 1), 1)))
    print(f'NORMALIZED {aid}: {len(keep_objs)} objs, {na} textures, '
          f'{sz/1e6:.2f} MB (source {srcsz/1e6:.1f} MB, {srcsz/max(sz,1):.0f}x smaller)',
          flush=True)

shutil.rmtree(TEXDIR, ignore_errors=True)
json.dump(report, open(os.path.join(OUT, 'budget.json'), 'w'), indent=1)
tot_o = sum(r['out_bytes'] for r in report)
tot_s = sum(r['src_bytes'] for r in report)
print(f'TOTAL normalized {tot_o/1e6:.1f} MB from {tot_s/1e6:.1f} MB of source')
print('DONE')
