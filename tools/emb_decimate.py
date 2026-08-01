"""decim.py — decimate APPENDED ASSETS ONLY on the realtime path, and measure the artifact.

    Blender -b <realtime.blend> -P decim.py -- --ratio R --glb <out.glb>

WHAT IS TOUCHED, and the rule is by NAME because the name is the contract everywhere else
in this town: walk_* (the network), lm_* / emb_* (the blockout's own massing and ground),
veg_* (blockout proxies) and emb_dress_* (this engine's generated boxes) are ALL LEFT
ALONE.  What decimates is the appended library scans -- the meshes that came in through
`src_collection` and keep their own source names -- which is 78.8% of the faces.
  Nothing the player stands on or bumps changes, so the collision surface is byte-stable.

AND IT DECIMATES UNIQUE MESH DATABLOCKS, NOT OBJECTS.  420 instances share a couple of
dozen scans; decimating per object would either fail on multi-user data or explode it into
420 single-user copies.  Per datablock, once, and every instance inherits it.
"""
import bpy, bmesh, sys, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def opt(f, d):
    return argv[argv.index(f) + 1] if f in argv else d
RATIO = float(opt("--ratio", "0.25"))
GLB = opt("--glb", "")
# THE DECIMATION HAS TO LIVE IN THE BLEND THE CRON READS.  `townwalk_live_refresh.sh`
# re-exports `emberbrook-realtime.blend` on its own schedule, so a decimation that exists
# only in this process's memory would be undone by the next cron tick — the same
# datablock-versus-artifact trap as the texture no-op, one level up.
SAVE = opt("--save", "")
KEEP = ("walk_", "lm_", "emb_", "veg_")          # emb_ covers emb_dress_ too

def appended(o):
    return o.type == 'MESH' and not o.name.startswith(KEEP)

before = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
targets = {}
for o in bpy.data.objects:
    if appended(o):
        targets.setdefault(o.data.name, o.data)
print("  appended unique mesh datablocks: %d" % len(targets))

dg = bpy.context.evaluated_depsgraph_get()
tmp = bpy.data.objects.new("_decim_tmp", None)
done = 0
for name, me in targets.items():
    if len(me.polygons) < 64:
        continue                                  # already cheap; collapsing adds nothing
    ob = bpy.data.objects.new("_dc_" + name[:40], me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("dec", 'DECIMATE')
    m.decimate_type = 'COLLAPSE'
    m.ratio = RATIO
    m.use_collapse_triangulate = False            # keep the silhouette's own edges
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    newme = bpy.data.meshes.new_from_object(ev)
    bm = bmesh.new(); bm.from_mesh(newme); bm.to_mesh(me); bm.free()
    bpy.data.meshes.remove(newme)
    bpy.data.objects.remove(ob, do_unlink=True)
    done += 1
after = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print("  ratio %.3f -> %d datablocks decimated; faces %d -> %d (%.1f%% kept)"
      % (RATIO, done, before, after, 100.0 * after / max(1, before)))
if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=SAVE)
    print("  SAVED %s  %.1f MB" % (os.path.basename(SAVE), os.path.getsize(SAVE) / 1e6))
if GLB:
    bpy.ops.export_scene.gltf(filepath=GLB, export_format='GLB', use_visible=False,
                              use_renderable=False, use_selection=False,
                              export_yup=True, export_cameras=True, export_lights=False)
    print("  GLB %s  %.1f MB" % (os.path.basename(GLB), os.path.getsize(GLB) / 1e6))
