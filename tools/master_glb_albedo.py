"""master_glb_albedo.py — what albedo does the RUNTIME actually receive?

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_glb_albedo.py -- --mats mat_grass,mat_rope
  Blender -b tools/blends/dellhollow-master.blend -P tools/master_glb_albedo.py           # all cured mats

WHY THIS EXISTS, and why it does NOT re-import the GLB.

`master_glb_survival.py` answers "did colour survive at all" by exporting a GLB,
re-importing it and reading the materials that arrive.  That is the right shape
for a survival question, but it is NOT a faithful readout of the file, because
Blender's glTF IMPORTER supplies its own defaults for anything the GLB leaves
out.  A material that exports with `baseColorFactor` ABSENT — the correct, most
common case for a COLOR_0-driven material, meaning the glTF default 1.0 — comes
back into Blender as a Principled whose Base Color default is **0.8 grey**,
Blender's own node default.  Read that number and you will conclude the runtime
is getting a 20% dark albedo when the file says nothing of the kind.

That is not hypothetical: it happened during the survivability pass, produced a
confident "every baked material ships 20% dark" diagnosis, and was only undone by
reading the GLB's own JSON — where `baseColorFactor` was absent both before and
after the "fix" (finding 219).  The re-import tells you what Blender would show
if Blender loaded it; only the JSON tells you what three.js will read.

So this tool parses the GLB chunk table directly and reports, per material:
  * baseColorFactor as WRITTEN (absent -> the glTF default 1,1,1,1)
  * whether a baseColorTexture is attached
  * whether the primitives using it carry COLOR_0
  * the effective albedo = factor x mean COLOR_0, which is the product three.js
    multiplies and therefore the only number that describes the walkable town

An effective albedo near 1.0 in all channels is the failure this whole pass
exists to remove; the tool flags it rather than leaving it to be eyeballed.
"""
import bpy, os, sys, json, struct
import numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SCRATCH = ROOT + "/tools/blends/districts/_albedo.glb"

DEFAULT = ["mat_grass", "mat_fern", "mat_leaf_autumn", "mat_leaf_creeper",
           "mat_leaf_autumn_far", "mat_rope", "mat_blackstone", "mat_darkfall",
           "mat_gate_flag_blue", "mat_gate_flag_blue2", "mat_gate_flag_bone",
           "mat_gate_flag_ochre", "mat_gate_flag_red", "mat_gate_flag_red2",
           "mat_flag_blue", "mat_flag_green", "mat_flag_ochre", "mat_flag_red"]
MATS = set((argv[argv.index("--mats") + 1].split(",")) if "--mats" in argv else DEFAULT)

sel = [o for o in bpy.data.objects if o.type == 'MESH'
       and any(m and m.name in MATS for m in o.data.materials)]
assert sel, "no objects carry %s" % sorted(MATS)
bpy.ops.object.select_all(action='DESELECT')
for o in sel:
    o.hide_set(False)
    o.hide_viewport = False
    o.hide_render = False
    o.select_set(True)
bpy.context.view_layer.objects.active = sel[0]
bpy.ops.export_scene.gltf(filepath=SCRATCH, export_format='GLB', use_selection=True,
                          export_apply=False, export_materials='EXPORT')

raw = open(SCRATCH, 'rb').read()
assert raw[:4] == b'glTF', "not a GLB"
off, js, bin_chunk = 12, None, None
while off < len(raw):
    ln, ty = struct.unpack_from('<II', raw, off)
    body = raw[off + 8: off + 8 + ln]
    if ty == 0x4E4F534A:
        js = json.loads(body.decode('utf-8'))
    elif ty == 0x004E4942:
        bin_chunk = body
    off += 8 + ln
assert js is not None

CT = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_accessor(i):
    a = js["accessors"][i]
    fmt, sz = CT[a["componentType"]]
    n = NC[a["type"]]
    v = js["bufferViews"][a["bufferView"]]
    base = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = v.get("byteStride") or (sz * n)
    out = np.empty((a["count"], n), dtype=np.float64)
    for k in range(a["count"]):
        out[k] = struct.unpack_from('<' + fmt * n, bin_chunk, base + k * stride)
    if a["componentType"] == 5121:
        out /= 255.0
    elif a["componentType"] == 5123:
        out /= 65535.0
    return out


# gather COLOR_0 per material across every primitive that uses it
col = {}
for me in js.get("meshes", []):
    for pr in me["primitives"]:
        mi = pr.get("material")
        if mi is None:
            continue
        name = js["materials"][mi].get("name", "?").split('.')[0]
        if name not in MATS:
            continue
        acc = pr["attributes"].get("COLOR_0")
        if acc is None:
            col.setdefault(name, [])
            continue
        c = read_accessor(acc)[:, :3]
        col.setdefault(name, []).append(c)

print("=" * 100)
print("RUNTIME ALBEDO, read from the GLB's own JSON (not from a re-import)")
print("=" * 100)
print("%-24s %-26s %-4s %-8s %-24s" % ("material", "baseColorFactor (written)", "tex", "COLOR_0", "effective albedo"))
seen, bad = set(), []
for mt in js.get("materials", []):
    name = mt.get("name", "?").split('.')[0]
    if name not in MATS or name in seen:
        continue
    seen.add(name)
    p = mt.get("pbrMetallicRoughness", {})
    f = p.get("baseColorFactor")
    fac = np.array(f[:3]) if f else np.ones(3)
    tex = "yes" if "baseColorTexture" in p else "-"
    cs = col.get(name, [])
    if cs:
        c0 = np.concatenate(cs).mean(axis=0)
        has = "yes"
    else:
        c0 = np.ones(3)
        has = "-"
    eff = fac * c0
    white = eff.min() > 0.9 and tex == "-"
    if white:
        bad.append(name)
    print("%-24s %-26s %-4s %-8s %-24s%s"
          % (name, "absent (=1,1,1)" if not f else str(np.round(fac, 4)), tex, has,
             str(np.round(eff, 4)), "   <-- EFFECTIVELY WHITE" if white else ""))
missing = sorted(MATS - seen)
if missing:
    print("\n  did not reach the GLB at all: %s" % missing)
print("\n" + "=" * 100)
if bad:
    print("EFFECTIVELY WHITE in the runtime: %d materials -> %s" % (len(bad), bad))
    os.remove(SCRATCH)
    sys.exit(1)
print("ALL %d materials deliver a real albedo to the runtime." % len(seen))
print("=" * 100)
os.remove(SCRATCH)
