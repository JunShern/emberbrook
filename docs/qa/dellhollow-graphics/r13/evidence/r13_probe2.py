"""r13_probe2.py — node links for the paint family, and the shape of every
mesh that wears mat_pumpkin (is there a donor to copy, as round 12 found?)."""
import bpy, sys, json

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "/tmp/r13_probe2.json"

res = {"mats": {}, "pumpkin_meshes": {}, "faceclass": {}}

for name in ("mat_pumpkin", "mat_shelf_paint_ochre", "mat_qm_paint_red",
             "mat_shelf_paint_green", "mat_timber", "mat_flag_red",
             "mat_qm_awning", "mat_blackstone", "m_water"):
    m = bpy.data.materials.get(name)
    if not m or not m.use_nodes:
        continue
    nt = m.node_tree
    d = {"nodes": [], "links": []}
    for n in nt.nodes:
        e = {"name": n.name, "type": n.type}
        if n.type == 'TEX_IMAGE':
            e["image"] = n.image.name if n.image else None
        if n.type == 'BSDF_PRINCIPLED':
            e["inputs"] = {k: (list(n.inputs[k].default_value)
                               if hasattr(n.inputs[k].default_value, "__len__")
                               else n.inputs[k].default_value)
                           for k in ("Base Color", "Roughness", "Metallic")
                           if k in n.inputs}
        if n.type == 'MAPPING':
            e["scale"] = list(n.inputs["Scale"].default_value)
        d["nodes"].append(e)
    for l in nt.links:
        d["links"].append("%s.%s -> %s.%s" % (l.from_node.name, l.from_socket.name,
                                              l.to_node.name, l.to_socket.name))
    res["mats"][name] = d

# every mesh wearing mat_pumpkin: what shape is it?
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render or not o.data.materials:
        continue
    names = [m.name if m else None for m in o.data.materials]
    if "mat_pumpkin" not in names:
        continue
    idx = names.index("mat_pumpkin")
    polys = [p for p in o.data.polygons if p.material_index == idx]
    vids = set()
    for p in polys:
        vids.update(p.vertices)
    mw = o.matrix_world
    ws = [mw @ o.data.vertices[i].co for i in sorted(vids)]
    if not ws:
        continue
    xs = [v.x for v in ws]; ys = [v.y for v in ws]; zs = [v.z for v in ws]
    sides = sorted(set(len(p.vertices) for p in polys))
    res["pumpkin_meshes"][o.name] = {
        "obj_verts": len(o.data.vertices), "obj_faces": len(o.data.polygons),
        "pumpkin_faces": len(polys), "pumpkin_verts": len(vids),
        "poly_sides": sides,
        "bbox": [round(min(xs), 2), round(max(xs), 2), round(min(ys), 2),
                 round(max(ys), 2), round(min(zs), 2), round(max(zs), 2)],
        "islands_est": round(len(vids) / 8.0, 2),
        "uv": len(o.data.uv_layers), "col": len(o.data.color_attributes),
        "smooth": sum(1 for p in polys if p.use_smooth),
    }

json.dump(res, open(OUT, "w"), indent=1)
print("SAVED %s" % OUT)
for k, v in res["pumpkin_meshes"].items():
    print("%-24s pumpkin %3d faces / %3d verts  sides %s  smooth %d  bbox %s"
          % (k, v["pumpkin_faces"], v["pumpkin_verts"], v["poly_sides"],
             v["smooth"], v["bbox"]))
print()
for k, v in res["mats"].items():
    print("== %s: %d nodes, %d links" % (k, len(v["nodes"]), len(v["links"])))
