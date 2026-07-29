"""master_glb_survival.py — the glTF-survival gate for ANY district in the master.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_glb_survival.py \
      -- --prefix gate_,veg_gate_ --own mat_gate_

Exports the named objects to a scratch GLB, re-imports it into an EMPTY blend and
reports what actually arrived.  Same contract as `shelf_gltf_verify.py`, which is
this script's district-specific ancestor — the difference is that the groups are
derived from the object names instead of being listed, so a district that never
had a verifier (the GATE tier predates the 2026-07-29 gate) can be checked without
writing a third copy of the round-trip.

MIGRATION.md 2026-07-29: a district HARD-FAILS on its OWN materials arriving white
and REPORTS shared-kit materials that arrive white as inherited debt — the town's
procedural foliage ramps and ropes are queued for a separate master-wide cure and
four accepted districts are built on them.
"""
import bpy, os, sys, re
import numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


PREFIX = tuple(opt("--prefix", "gate_,veg_gate_").split(","))
OWN = opt("--own", "mat_gate_")
TAG = opt("--tag", PREFIX[0].strip("_"))
SCRATCH = os.path.join(ROOT, "tools", "blends", "districts", "_%s_roundtrip.glb" % TAG)

sel = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(PREFIX)]
assert sel, "no meshes match %s" % (PREFIX,)
bpy.ops.object.select_all(action='DESELECT')
for o in sel:
    o.hide_set(False)
    o.select_set(True)
bpy.context.view_layer.objects.active = sel[0]
bpy.ops.export_scene.gltf(filepath=SCRATCH, export_format='GLB',
                          use_selection=True, export_apply=False,
                          export_materials='EXPORT')
print("exported %d objects -> %s (%.2f MB)"
      % (len(sel), os.path.basename(SCRATCH), os.path.getsize(SCRATCH) / 1e6))
n_out = len(sel)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SCRATCH)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print("\n" + "=" * 78)
print("GLB SURVIVAL (%s) — %d objects out, %d in" % (TAG, n_out, len(meshes)))
print("=" * 78)


def mat_facts(m):
    """(textured with real pixels, reads COLOR_0, emits, base colour) — read off the
    material that ARRIVED, never the one that was authored."""
    if m is None or not m.node_tree:
        return False, False, False, (1.0, 1.0, 1.0)
    nt = m.node_tree
    tex = any(n.type == 'TEX_IMAGE' and n.image is not None and n.image.size[0] > 0
              for n in nt.nodes)
    vc = any(n.bl_idname == 'ShaderNodeVertexColor' or n.type == 'VERTEX_COLOR'
             for n in nt.nodes)
    b = nt.nodes.get("Principled BSDF")
    bc, em = (1.0, 1.0, 1.0), False
    if b is not None:
        bc = tuple(b.inputs["Base Color"].default_value)[:3]
        e = b.inputs.get("Emission Strength")
        ec = b.inputs.get("Emission Color")
        em = bool(e and e.default_value > 0.01
                  and ec and max(tuple(ec.default_value)[:3]) > 0.02)
    return tex, vc, em, bc


# group by the object-name stem, so the report reads per KIND of thing without a
# hand-written group table
def stem(n):
    n = re.sub(r"[._]\d+$", "", n)
    parts = n.split("_")
    return "_".join(parts[:3]) if parts[0] == "veg" else "_".join(parts[:2])


bad, legacy_white, groups = [], {}, {}
for o in meshes:
    groups.setdefault(stem(o.name), []).append(o)

for g in sorted(groups):
    obs = groups[g]
    ntex = nvc = nflat = nem = nown = 0
    means = []
    for o in obs:
        ca = o.data.color_attributes.active_color
        if ca is not None and len(ca.data):
            d = np.zeros(len(ca.data) * 4)
            ca.data.foreach_get("color", d)
            rgb = d.reshape(-1, 4)[:, :3]
            means.append(float(rgb.mean()))
            nvc += 1
            if rgb.std() < 0.002 and abs(rgb.mean() - 1.0) < 0.01:
                nflat += 1                     # a lost COLOR_0 looks exactly like this
        if not o.data.materials:
            bad.append((o.name, "arrived with no material at all"))
            continue
        own_any = own_ok = False
        for m in o.data.materials:
            tex, vc, em, bc = mat_facts(m)
            ntex += 1 if tex else 0
            nem += 1 if em else 0
            delivers = tex or em or (vc and ca is not None)
            if m and m.name.startswith(OWN):
                nown += 1
                own_any = True
                own_ok = own_ok or delivers
                if not delivers and min(bc) > 0.95:
                    bad.append((o.name, "%s (DISTRICT-OWNED) is default-white and unpainted" % m.name))
            elif not delivers and min(bc) > 0.95:
                legacy_white[m.name] = legacy_white.get(m.name, 0) + 1
        if own_any and not own_ok:
            bad.append((o.name, "no district-owned material on it delivers colour"))
    print("  %-26s %3d objs | textured mats %3d | COLOR_0 %3d (flat-white %d) | "
          "emissive %2d | own-mat slots %3d | mean COLOR_0 %s"
          % (g, len(obs), ntex, nvc, nflat, nem, nown,
             "%.3f" % (sum(means) / len(means)) if means else "  -  "))

imgs = [i for i in bpy.data.images if i.name != "Render Result"]
print("\n  images that arrived: %d" % len(imgs))
for i in imgs:
    if i.size[0] == 0:
        bad.append((i.name, "image arrived with no pixels"))

own_mats = [m for m in bpy.data.materials if m.name.startswith(OWN)]
own_white = [m.name for m in own_mats
             if not any(mat_facts(m)[:3]) and min(mat_facts(m)[3]) > 0.95]
print("  materials: %d, of which %s*: %d  (white: %d %s)"
      % (len(bpy.data.materials), OWN, len(own_mats), len(own_white), own_white))
if legacy_white:
    print("\n  INHERITED DEBT — shared kit materials arriving WHITE on this district's")
    print("  objects.  Queued master-wide cure (MIGRATION.md 2026-07-29), not this")
    print("  district's to re-author:")
    for n, c in sorted(legacy_white.items(), key=lambda t: -t[1]):
        print("     %-24s %4d material slots" % (n, c))

print("\n" + "=" * 78)
os.remove(SCRATCH)
if bad:
    for n, why in bad[:25]:
        print("  !! %-34s %s" % (n, why))
    print("GLB SURVIVAL FAILED: %d problems" % len(bad))
    sys.exit(1)
print("GLB SURVIVAL CLEAN — %d district-owned materials, 0 white." % len(own_mats))
print("(%d shared-kit materials arrive white, listed above as inherited debt.)"
      % len(legacy_white))
print("=" * 78)
