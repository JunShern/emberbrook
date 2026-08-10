"""r13_probe.py — one Blender pass, every property question round 13 asks.

  Blender -b tools/blends/dellhollow-master.blend --python-exit-code 1 \
      -P r13_probe.py -- --out r13_probe.json
"""
import bpy, sys, json, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else "/tmp/r13_probe.json"

res = {"objects": {}, "lights": {}, "materials": {}}


def wverts(o):
    m = o.matrix_world
    return [m @ v.co for v in o.data.vertices]


def rec(o):
    ws = wverts(o)
    if not ws:
        return None
    xs = [v.x for v in ws]; ys = [v.y for v in ws]; zs = [v.z for v in ws]
    d = {
        "verts": len(o.data.vertices),
        "faces": len(o.data.polygons),
        "mats": [m.name if m else None for m in o.data.materials],
        "bbox": [min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)],
        "dims": [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)],
        "loc": list(o.location),
        "uv": len(o.data.uv_layers),
        "col": [c.name for c in o.data.color_attributes],
        "hide_render": o.hide_render,
        "coll": [c.name for c in o.users_collection],
    }
    # mean stored Col
    if o.data.color_attributes:
        ca = o.data.color_attributes[0]
        n = len(ca.data)
        if n:
            s = [0.0, 0.0, 0.0]
            for i in range(n):
                c = ca.data[i].color
                s[0] += c[0]; s[1] += c[1]; s[2] += c[2]
            d["col_mean"] = [x / n for x in s]
    return d


PFX = ("t2c_", "qm_awning", "lf_crest_bay", "lf_spill_bay", "qm_stair_underworks",
       "veg_lf_rimclump", "veg_nl_clump", "veg_wv_clump")
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    if any(o.name.startswith(p) for p in PFX):
        r = rec(o)
        if r:
            res["objects"][o.name] = r

for o in bpy.data.objects:
    if o.type == 'LIGHT':
        res["lights"][o.name] = {
            "type": o.data.type, "energy": o.data.energy,
            "loc": list(o.location), "rot": list(o.rotation_euler),
            "size": getattr(o.data, "size", None),
            "size_y": getattr(o.data, "size_y", None),
            "shadow": getattr(o.data, "use_shadow", None),
            "cutoff": (o.data.cutoff_distance if o.data.use_custom_distance else None),
            "color": list(o.data.color),
        }

for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    res["materials"][m.name] = {
        "nodes": len(m.node_tree.nodes),
        "types": sorted(set(n.type for n in m.node_tree.nodes)),
        "images": sorted(set(n.image.name for n in m.node_tree.nodes
                             if n.type == 'TEX_IMAGE' and n.image)),
    }

json.dump(res, open(OUT, "w"), indent=0)
print("SAVED %s  objects=%d lights=%d materials=%d"
      % (OUT, len(res["objects"]), len(res["lights"]), len(res["materials"])))
