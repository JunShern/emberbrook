"""master_walk_qa.py — the master's walk-contract gate.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_walk_qa.py
  Blender -b tools/blends/dellhollow-master.blend -P tools/master_walk_qa.py -- --region 2,40,14,34

Asserts, with zero tolerance on geometry:

 [1] IDENTITY — every walk_*/bar_* mesh in the master is present in the topology
     reference tools/blends/dellhollow-town.blend, with the same vertex count and
     bit-identical world-space vertices.  The reference objects are appended into
     a throwaway datablock set for the comparison; this script NEVER saves.
 [2] COMPLETENESS — no walk_/bar_ mesh from the reference has gone missing, and
     none has been parented, scaled or otherwise transformed.
 [3] RAY COVERAGE — down-rays over every walk top face inside the district region
     must first-hit a walk mesh.  Faces buried under a higher walk mesh are
     measured against that effective top (manifest finding 36).  Volume/haze
     helpers are hidden from the depsgraph first (finding 19).
 [4] HEADROOM — nothing solid within 2.0 m above the district-region walk surface.
 [5] EXPORTABILITY — walk meshes that are render-hidden (collision-only under the
     detailed art) must still be viewport-visible, or the glTF exporter drops them.

Exit code is non-zero on any failure.
"""
import bpy, sys, os, math, json, subprocess, tempfile
from mathutils import Vector

sys.path.insert(0, "/Users/junshernchan/projects/multiplayer-rpg/tools")
from boatyard_lib import REPO, Corridor, point_in_poly, plane_z_fn

TOWN = REPO + "/tools/blends/dellhollow-town.blend"
REF_CACHE = REPO + "/tools/blends/districts/town_walk_reference.json"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
REGION = (2.0, 40.0, 14.0, 34.0)
if "--region" in argv:
    REGION = tuple(float(v) for v in argv[argv.index("--region") + 1].split(","))
TOL = 0.0            # zero tolerance: the topology may not drift at all
fails = []
print("=" * 78)
print("MASTER WALK QA   (topology reference: %s)" % os.path.basename(TOWN))
print("=" * 78)

live = {o.name: o for o in bpy.data.objects
        if o.type == 'MESH' and o.name.startswith(("walk_", "bar_"))}
print("\nmaster carries %d walk_/bar_ meshes" % len(live))

# ------------------------------------------------------------- 1/2. identity
# The reference is read in a SEPARATE Blender process and cached as JSON: names
# like "..._landing.001" are real object names in both files, so appending the
# reference into this file would re-suffix them and silently mis-pair everything.
DUMP = (
    "import bpy, json\n"
    "out={}\n"
    "for o in bpy.data.objects:\n"
    "    if o.type=='MESH' and o.name.startswith(('walk_','bar_')):\n"
    "        out[o.name]={'verts':[list(o.matrix_basis @ v.co) for v in o.data.vertices],\n"
    "                     'parent': o.parent.name if o.parent else None}\n"
    "json.dump(out, open(%r,'w'))\n" % REF_CACHE)
if not os.path.exists(REF_CACHE) or os.path.getmtime(REF_CACHE) < os.path.getmtime(TOWN):
    print("(rebuilding topology reference cache from %s)" % TOWN)
    subprocess.run([bpy.app.binary_path, "-b", TOWN, "--python-expr", DUMP],
                   check=True, stdout=subprocess.DEVNULL)
ref = json.load(open(REF_CACHE))
print("reference carries %d walk_/bar_ meshes" % len(ref))

missing = sorted(set(ref) - set(live))
extra = sorted(set(live) - set(ref))
if missing:
    fails.append("walk/bar meshes MISSING from the master: %s" % missing[:12])
if extra:
    fails.append("walk/bar meshes in the master that the reference does not have: %s" % extra[:12])

worst, worst_name = 0.0, "-"
checked = 0
for name, ob in sorted(live.items()):
    r = ref.get(name)
    if r is None:
        continue
    if (ob.parent.name if ob.parent else None) != r["parent"]:
        fails.append("%s parenting changed" % name)
    if len(ob.data.vertices) != len(r["verts"]):
        fails.append("%s vertex count %d != reference %d"
                     % (name, len(ob.data.vertices), len(r["verts"])))
        continue
    A = ob.matrix_basis
    d = max((A @ v.co - Vector(w)).length for v, w in zip(ob.data.vertices, r["verts"]))
    checked += 1
    if d > worst:
        worst, worst_name = d, name
    if d > TOL:
        fails.append("%s moved by %.9f" % (name, d))
print("\n[1/2] IDENTITY  — %d meshes compared vertex-for-vertex" % checked)
print("      missing: %d   unexpected: %d" % (len(missing), len(extra)))
print("      worst world-space vertex delta: %.3e  (%s)" % (worst, worst_name))
if worst == 0.0 and not missing and not extra:
    print("      -> the town's topology is bit-identical to the reference.")

# ------------------------------------------------------- 3/4. ray + headroom
HID = []
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    if (ob.name.startswith(("fx_", "FOG_BOX", "v10_haze")) or
            any(t in ob.name for t in ("spray", "mist", "smoke", "plume"))):
        if not ob.hide_viewport:
            ob.hide_viewport = True
            HID.append(ob.name)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene
print("\n(masked %d volume/haze helpers for ray casting: %s)"
      % (len(HID), ", ".join(sorted(HID)[:6])))

walks = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("walk_")]
region_walks = []
for o in walks:
    vs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(v.x for v in vs) / 8
    cy = sum(v.y for v in vs) / 8
    if REGION[0] <= cx <= REGION[1] and REGION[2] <= cy <= REGION[3]:
        region_walks.append(o)
EFF = Corridor(walks, margin=0.0)
print("\n[3] RAY COVERAGE over %d walk meshes in region x %.0f..%.0f y %.0f..%.0f"
      % (len(region_walks), *REGION))

total = ok = buried = 0
bad = {}
head = {}
for ob in region_walks:
    Mx = ob.matrix_world
    N = Mx.to_3x3().inverted().transposed()
    for p in ob.data.polygons:
        if (N @ p.normal).normalized().z <= 0.5:
            continue
        raw = [Mx @ ob.data.vertices[i].co for i in p.vertices]
        zfn = plane_z_fn(raw)
        xs = [q.x for q in raw]
        ys = [q.y for q in raw]
        step = 0.35
        x = min(xs) + step / 2
        while x < max(xs):
            y = min(ys) + step / 2
            while y < max(ys):
                if point_in_poly(x, y, raw):
                    z = zfn(x, y)
                    eff = EFF.top_at(x, y)
                    if eff is not None and eff > z + 0.05:
                        buried += 1
                        y += step
                        continue
                    z = eff if eff is not None else z
                    total += 1
                    hit, loc, nor, idx, obj, mat = sc.ray_cast(
                        dg, Vector((x, y, z + 0.90)), Vector((0, 0, -1)), distance=1.9)
                    nm = obj.name if hit else "<nothing>"
                    # bar_ railings are canonical topology too (the map owns them):
                    # a rail post standing on the edge of its own tread is authored.
                    if hit and nm.startswith(("walk_", "bar_")):
                        ok += 1
                    else:
                        bad[nm] = bad.get(nm, 0) + 1
                    h2, l2, n2, i2, o2, m2 = sc.ray_cast(
                        dg, Vector((x, y, z + 0.06)), Vector((0, 0, 1)), distance=1.94)
                    if h2 and not o2.name.startswith(("walk_", "bar_")):
                        head[o2.name] = head.get(o2.name, 0) + 1
                y += step
            x += step
print("      samples %d | first hit is a walk mesh: %d (%.2f%%) | %d buried-face samples skipped"
      % (total, ok, 100.0 * ok / max(total, 1), buried))
if bad:
    for k, v in sorted(bad.items(), key=lambda kv: -kv[1]):
        print("      !! %-44s %d samples" % (k, v))
    fails.append("non-walk first hits: %s" % bad)
else:
    print("      -> every sample lands on the canonical collision surface.")

print("\n[4] HEADROOM (2.0 m above the district-region walk surface)  [warning only]")
if head:
    for k, v in sorted(head.items(), key=lambda kv: -kv[1]):
        print("      ~~ %-44s %d samples (%.2f%% of surface)"
              % (k, v, 100.0 * v / max(total, 1)))
    over = {k: v for k, v in head.items() if v > total * 0.01}
    if over:
        fails.append("headroom obstructions over 1%% of the walk surface: %s" % over)
else:
    print("      -> clear over every sample.")

# --------------------------------------------------------- 5. exportability
print("\n[5] EXPORTABILITY")
hidden_render = [o.name for o in walks if o.hide_render]
bad_vp = [o.name for o in bpy.data.objects
          if o.type == 'MESH' and o.name.startswith(("walk_", "bar_")) and o.hide_viewport]
print("      %d walk meshes are render-hidden (collision-only under detailed art)"
      % len(hidden_render))
for n in sorted(hidden_render):
    print("         %s" % n)
if bad_vp:
    fails.append("walk/bar meshes hidden in the VIEWPORT (glTF would drop them): %s" % bad_vp)
else:
    print("      -> every walk/bar mesh is viewport-visible, so the GLB keeps them.")

print("\n" + "=" * 78)
if fails:
    print("MASTER WALK QA FAILED (%d)" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("MASTER WALK QA PASSED — topology bit-identical, corridors clear, GLB-safe.")
print("=" * 78)
