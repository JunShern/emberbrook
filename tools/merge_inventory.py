"""merge_inventory.py — datablock census for the west-branch merge.

  Blender -b <blend> -P tools/merge_inventory.py -- <out.json>

Dumps object names (by collection), material names, mesh/image/node-group counts.
Read-only; never saves.  Its whole purpose is to prove an append added exactly
what it claimed and nothing else (the Weave's 2207-datablock leak, finding 180).
"""
import bpy, sys, json, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else "/tmp/inventory.json"

data = {
    "blend": bpy.data.filepath,
    "objects": sorted(o.name for o in bpy.data.objects),
    "materials": sorted(m.name for m in bpy.data.materials),
    "meshes": len(bpy.data.meshes),
    "images": sorted(i.name for i in bpy.data.images),
    "node_groups": sorted(g.name for g in bpy.data.node_groups),
    "collections": {c.name: sorted(o.name for o in c.objects)
                    for c in bpy.data.collections},
    "counts": {
        "objects": len(bpy.data.objects),
        "materials": len(bpy.data.materials),
        "meshes": len(bpy.data.meshes),
        "images": len(bpy.data.images),
        "node_groups": len(bpy.data.node_groups),
        "collections": len(bpy.data.collections),
        "lights": len(bpy.data.lights),
        "cameras": len(bpy.data.cameras),
        "actions": len(bpy.data.actions),
        "textures": len(bpy.data.textures),
        "worlds": len(bpy.data.worlds),
        "total_ids": sum(len(getattr(bpy.data, a)) for a in dir(bpy.data)
                         if not a.startswith("_")
                         and hasattr(getattr(bpy.data, a), "__len__")),
    },
}
json.dump(data, open(out, "w"), indent=1)
print("INVENTORY %s -> %s" % (os.path.basename(bpy.data.filepath), out))
for k, v in sorted(data["counts"].items()):
    print("  %-14s %d" % (k, v))
