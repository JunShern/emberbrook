"""master_mat_dedup.py — collapse `<name>.NNN` material copies back onto `<name>`.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_mat_dedup.py -- [save]

Finding 130 caught the IMAGE half of the kit-append leak and fixed it; the
MATERIAL half was never noticed, because a material datablock is invisible in a
render and `use_fake_user = True` keeps it from ever being purged.

`kit_load()` runs `libraries.load(...)` once per group of kit assemblies and each
call asks for `dst.materials = [m for m in src.materials if m.startswith("lf_")]`
— so every call appends a FRESH copy of all eight kit materials, and each placed
assembly ends up pointing at its own private copy.  The master carried **2207**
material datablocks, of which 204 were referenced by a mesh and 2000 were unused
`lf_*.NNN` copies; the 19 kit-derived objects between them used 152 different
datablocks for what are eight materials.

Two costs, and the second is the one that matters:
  * the .blend is ~2x bigger than its geometry needs;
  * a town-wide material fix (the queued glTF white-material bake) would have to
    edit 152 datablocks instead of 8, and any district that reuses a kit material
    by name gets `lf_deck` — the unused copy — and silently renders on a
    different datablock from the art beside it.

This is a pure datablock remap: every copy whose node signature matches the
canonical one is `user_remap`ped onto it and removed.  Copies that DIFFER are
listed and left alone, so a deliberately re-toned variant is never eaten.
No object, mesh, vertex or material VALUE changes, so both gates must return
identical numbers.
"""
import bpy, re, sys
from collections import defaultdict

SAVE = "save" in sys.argv
PREFIXES = ("lf_",)          # only the kit's own append leak, nothing else

print("=" * 78)
print("MASTER MATERIAL DEDUP")
print("=" * 78)


def sig(m):
    """Node-tree signature: identical signature == interchangeable datablock."""
    if not m.node_tree:
        return ("nonodes", tuple(round(c, 6) for c in m.diffuse_color))
    out = []
    for n in sorted(m.node_tree.nodes, key=lambda n: (n.bl_idname, n.name)):
        row = [n.bl_idname]
        if n.bl_idname == "ShaderNodeTexImage":
            row += [n.image.name if n.image else None,
                    n.image.filepath if n.image else None]
        elif n.bl_idname == "ShaderNodeVertexColor":
            row.append(n.layer_name)
        elif n.bl_idname == "ShaderNodeBsdfPrincipled":
            for k in ("Base Color", "Roughness", "Metallic",
                      "Emission Color", "Emission Strength"):
                v = n.inputs[k].default_value
                row.append((k, tuple(round(x, 5) for x in v)
                            if hasattr(v, "__len__") else round(v, 5)))
        elif n.bl_idname == "ShaderNodeMix":
            row += [n.data_type, n.blend_type]
        out.append(tuple(row))
    return tuple(out)


groups = defaultdict(list)
for m in bpy.data.materials:
    base = re.sub(r"\.\d{3}$", "", m.name)
    if base.startswith(PREFIXES):
        groups[base].append(m)

before_mats = len(bpy.data.materials)
used_before = {s.name for o in bpy.data.objects if o.type == 'MESH'
               for s in o.data.materials if s}
removed = kept_variants = 0

for base in sorted(groups):
    fam = groups[base]
    canon = bpy.data.materials.get(base) or fam[0]
    csig = sig(canon)
    same = [m for m in fam if m is not canon and sig(m) == csig]
    diff = [m for m in fam if m is not canon and sig(m) != csig]
    for m in same:
        m.user_remap(canon)
        bpy.data.materials.remove(m)
        removed += 1
    canon.use_fake_user = True
    if canon.name != base:                       # the canonical name was free
        canon.name = base
    kept_variants += len(diff)
    print("  %-14s %4d copies -> 1 (%d removed)%s"
          % (base, len(fam), removed and len(same),
             "  [%d genuinely different, LEFT ALONE: %s]" % (len(diff), [m.name for m in diff][:4])
             if diff else ""))

used_after = {s.name for o in bpy.data.objects if o.type == 'MESH'
              for s in o.data.materials if s}
print("\n  material datablocks %d -> %d   (%d removed, %d divergent kept)"
      % (before_mats, len(bpy.data.materials), removed, kept_variants))
print("  distinct materials referenced by a mesh: %d -> %d"
      % (len(used_before), len(used_after)))
assert not [n for n in used_after if re.search(r"\.\d{3}$", n) and n.startswith(PREFIXES)], \
    "a mesh still points at a suffixed kit material"
print("=" * 78)
if SAVE:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
