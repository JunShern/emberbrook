"""merge_probe_branch.py — pre-append reconnaissance on the west branch.

  Blender -b tools/blends/dellhollow-master-gate-branch.blend -P tools/merge_probe_branch.py

For GATE_DISTRICT and SHELF_DISTRICT: does anything reach OUTSIDE the collection
(parent, modifier object, constraint, driver, boolean target)?  Any such reference
makes an append drag master-owned duplicates in with it — the 2207-datablock leak
(finding 141).  Also reports material/image usage and the render-flag state the
branch is handing over.  Read-only; never saves.
"""
import bpy
from mathutils import Vector

for cname in ("GATE_DISTRICT", "SHELF_DISTRICT"):
    coll = bpy.data.collections.get(cname)
    print("=" * 78)
    print("%s — %d objects, children: %s" % (cname, len(coll.objects),
                                             [c.name for c in coll.children]))
    inside = {o.name for o in coll.all_objects}
    types = {}
    outward = []
    mats, imgs = {}, set()
    hr = hv = 0
    prefixes = {}
    zmin, zmax = 1e9, -1e9
    xmin, xmax = 1e9, -1e9
    ymin, ymax = 1e9, -1e9
    for o in coll.all_objects:
        types[o.type] = types.get(o.type, 0) + 1
        prefixes[o.name.split("_")[0]] = prefixes.get(o.name.split("_")[0], 0) + 1
        if o.parent and o.parent.name not in inside:
            outward.append("%s PARENT-> %s" % (o.name, o.parent.name))
        for m in o.modifiers:
            for attr in ("object", "target", "mirror_object", "offset_object"):
                t = getattr(m, attr, None)
                if t is not None and getattr(t, "name", None) not in inside:
                    outward.append("%s MOD %s.%s -> %s" % (o.name, m.name, attr, t.name))
        for c in o.constraints:
            t = getattr(c, "target", None)
            if t is not None and t.name not in inside:
                outward.append("%s CONSTRAINT -> %s" % (o.name, t.name))
        if o.animation_data:
            outward.append("%s has animation_data" % o.name)
        if o.hide_render:
            hr += 1
        if o.hide_viewport:
            hv += 1
        for s in o.material_slots:
            if s.material:
                mats[s.material.name] = mats.get(s.material.name, 0) + 1
                for n in (s.material.node_tree.nodes if s.material.use_nodes else []):
                    if n.type == 'TEX_IMAGE' and n.image:
                        imgs.add(n.image.name)
        if o.type == 'MESH' and len(o.data.vertices):
            vs = [o.matrix_world @ Vector(c) for c in o.bound_box]
            xmin = min(xmin, min(v.x for v in vs)); xmax = max(xmax, max(v.x for v in vs))
            ymin = min(ymin, min(v.y for v in vs)); ymax = max(ymax, max(v.y for v in vs))
            zmin = min(zmin, min(v.z for v in vs)); zmax = max(zmax, max(v.z for v in vs))
    print("  types:", types)
    print("  name prefixes:", dict(sorted(prefixes.items(), key=lambda kv: -kv[1])))
    print("  world extent: x %.2f..%.2f  y %.2f..%.2f  z %.2f..%.2f" % (xmin, xmax, ymin, ymax, zmin, zmax))
    print("  hide_render=%d  hide_viewport=%d" % (hr, hv))
    print("  materials used (%d):" % len(mats))
    for k, v in sorted(mats.items()):
        print("      %-28s %d slots" % (k, v))
    print("  images referenced (%d): %s" % (len(imgs), sorted(imgs)))
    print("  OUTWARD REFERENCES (%d):" % len(outward))
    for r in outward:
        print("      !!", r)

print("=" * 78)
print("scene root children:", [c.name for c in bpy.context.scene.collection.children])
