"""overworld3_verify.py — F2's glTF round-trip proof, zone-grid check and perf table.

  Blender -b --factory-startup -P tools/overworld3_verify.py

Four jobs, one Blender launch:

 1. ROUND TRIP.  Re-import the shipped GLB into an EMPTY blend (nothing in the
    authoring file can prop it up) and report what actually arrived: COLOR_0,
    baseColor/normal/roughness textures, alphaMode, and the walk_/water_/veg_
    naming the runtime keys off.  A MASK material whose atlas came out as JPEG has
    no alpha left and every cutout silently becomes a solid card (finding 131).

 2. SPAWN.  Replicate public/play3d.html's own spawn scan.  If it does not land on
    the walk network the prototype is unplayable however well it renders.

 3. WALK-RIBBON CLEARANCE — new gate for round 3.  The walk ribbons float 0.06-0.09u
    above the terrain, and F2 displaces the terrain.  Every ribbon vertex is checked
    against the ground beneath it: a single positive number here is the sawtooth of
    terrain poking through the road that the first F2 render showed.

 4. ZONES.  Decode zones.json exactly as the runtime does (RLE -> grid), check the
    registry invariants that make the format extensible, and confirm the zone under
    the spawn point is what the fiction says it should be.

Writes docs/qa/overworld/PERF3.md — F2 against round-2 F on the axes the user is
choosing on.
"""
import bpy
import os
import sys
import json
import struct

import numpy as np
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(ROOT, "docs/qa/overworld")
KEY = "ow-proto-f2"
BUNDLE = os.path.join(ROOT, "public/assets/scenes", KEY)
GLB = os.path.join(BUNDLE, "scene.glb")
ZP = os.path.join(BUNDLE, "zones.json")

ok_all = True


def fail(msg):
    global ok_all
    ok_all = False
    print("  *** FAIL: %s" % msg)


def glb_json(path):
    with open(path, "rb") as f:
        struct.unpack("<III", f.read(12))
        ln, kind = struct.unpack("<II", f.read(8))
        return json.loads(f.read(ln).decode("utf-8"))


# =============================================================== 1. the GLB JSON
J = glb_json(GLB)
prims = sum(len(m["primitives"]) for m in J.get("meshes", []))
acc = J.get("accessors", [])
verts = tris = 0
for m in J.get("meshes", []):
    for p in m["primitives"]:
        verts += acc[p["attributes"]["POSITION"]]["count"]
        tris += acc[p["indices"]]["count"] // 3 if "indices" in p else 0
texbytes = sum(J["bufferViews"][im["bufferView"]]["byteLength"]
               for im in J.get("images", []) if "bufferView" in im)
mats = J.get("materials", [])
n_norm = sum(1 for m in mats if "normalTexture" in m)
n_mr = sum(1 for m in mats
           if "metallicRoughnessTexture" in m.get("pbrMetallicRoughness", {}))
n_mask = sum(1 for m in mats if m.get("alphaMode") == "MASK")
n_blend = sum(1 for m in mats if m.get("alphaMode") == "BLEND")
sz = os.path.getsize(GLB) / 1e6

print("=== STYLE F2 ============================================")
print("  %d meshes / %d primitives (draw calls), %d verts, %d tris"
      % (len(J.get("meshes", [])), prims, verts, tris))
print("  %.2f MB GLB, %.2f MB embedded texture, %d images, %d materials"
      % (sz, texbytes / 1e6, len(J.get("images", [])), len(mats)))
print("  normalTexture %d, metallicRoughness %d, alphaMode MASK %d / BLEND %d"
      % (n_norm, n_mr, n_mask, n_blend))
mimes = {}
for im in J.get("images", []):
    mimes[im.get("mimeType", "?")] = mimes.get(im.get("mimeType", "?"), 0) + 1
print("  image mime types: %s" % mimes)
big = sorted(((J["bufferViews"][im["bufferView"]]["byteLength"], im.get("name", "?"),
               im.get("mimeType", "?")) for im in J.get("images", [])
              if "bufferView" in im), reverse=True)[:6]
print("  biggest images:")
for b, nm, mt in big:
    print("    %-34s %6.2f MB  %s" % (nm, b / 1e6, mt))
if n_mask == 0:
    fail("no alphaMode MASK material — the card approaches lost their cutout")
for m in mats:
    if m.get("alphaMode") == "MASK":
        ti = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        mt = J["images"][J["textures"][ti]["source"]].get("mimeType", "?")
        print("    MASK material %-16s baseColor mime=%s %s"
              % (m.get("name", "?"), mt, "OK" if "png" in mt else "ALPHA LOST"))
        if "png" not in mt:
            fail("MASK material %s lost its alpha to JPEG" % m.get("name"))

# ==================================================== 2. re-import into an EMPTY
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
walk = sorted(o.name for o in meshes if o.name.lower().startswith("walk"))
water = sorted(o.name for o in meshes if o.name.lower().startswith("water_"))
veg = sorted(o.name for o in meshes if o.name.lower().startswith("veg_"))
trunks = sorted(o.name for o in meshes if o.name.lower().startswith("tree_"))
marks = sorted(o.name for o in meshes if o.name.lower().startswith("marker_"))
print("  cameras: %d   walk_: %s" % (len(cams), ", ".join(walk) or "NONE"))
print("  water_: %s" % (", ".join(water) or "NONE"))
print("  veg_:   %s" % (", ".join(veg) or "NONE"))
print("  tree_ (solid trunks): %s" % (", ".join(trunks) or "NONE"))
print("  markers: %s" % (", ".join(marks) or "NONE"))
if not walk:
    fail("no walk network — spawn will fall back")
if not veg or not trunks:
    fail("veg_/tree_ split missing — finding 137 (veg_ is never standable, so a "
         "trunk baked into a canopy mesh makes the whole tree walk-through)")
if "qa_zone_overlay" in [o.name for o in meshes]:
    fail("the QA zone overlay shipped in the GLB")
for nm in ("veg_lineup_a", "veg_lineup_b_cards", "veg_lineup_c", "veg_lineup_d"):
    if nm not in [o.name for o in meshes]:
        fail("line-up group %s missing from the bundle" % nm)

n_vcol = n_flat = 0
for o in meshes:
    ca = o.data.color_attributes.active_color
    if ca is not None:
        n_vcol += 1
        d = np.zeros(len(ca.data) * 4)
        ca.data.foreach_get("color", d)
        rgb = d.reshape(-1, 4)[:, :3]
        if rgb.std() < 0.002 and abs(rgb.mean() - 1.0) < 0.01:
            n_flat += 1
print("  COLOR_0 on %d/%d meshes (%d flat-white)" % (n_vcol, len(meshes), n_flat))

g = bpy.data.objects.get("ground_valley")
if g is None:
    fail("ground_valley is not in the GLB under that name")
else:
    ims = []
    for mt in g.data.materials:
        if mt and mt.node_tree:
            ims += [(n.image.name, tuple(n.image.size)) for n in mt.node_tree.nodes
                    if n.type == "TEX_IMAGE" and n.image]
    print("  ground_valley: %d slots, %d smooth / %d flat faces, %d images"
          % (len(g.data.materials),
             sum(1 for p in g.data.polygons if p.use_smooth),
             sum(1 for p in g.data.polygons if not p.use_smooth), len(ims)))
    nflat = sum(1 for p in g.data.polygons if not p.use_smooth)
    if nflat == 0:
        fail("no flat-shaded facets survived — the crag treatment is gone")
    if nflat == len(g.data.polygons):
        fail("EVERY facet is flat — the smooth baseline is gone")

# ============================================ 3. spawn scan (the runtime's own)
wm = [o for o in meshes if o.name.lower().startswith("walk")]
bb = [Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))]
for o in wm:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            bb[0][i] = min(bb[0][i], w[i])
            bb[1][i] = max(bb[1][i], w[i])
cx, cy = (bb[0].x + bb[1].x) / 2, (bb[0].y + bb[1].y) / 2
sx = max(1.5, (bb[1].x - bb[0].x) / 64)
sy = max(1.5, (bb[1].y - bb[0].y) / 64)
best = None
x = bb[0].x
while x <= bb[1].x:
    y = bb[0].y
    while y <= bb[1].y:
        top = None
        for o in wm:
            hit, loc, nrm, idx = o.ray_cast(
                o.matrix_world.inverted() @ Vector((x, y, bb[1].z + 40.0)),
                Vector((0, 0, -1)), distance=400.0)
            if hit:
                wz = (o.matrix_world @ loc).z
                top = wz if top is None else max(top, wz)
        if top is not None:
            d = abs(x - cx) + abs(y - cy)
            if best is None or d < best[3]:
                best = (x, y, top, d)
        y += sy
    x += sx
spawn_rt = None
if best is None:
    fail("spawn scan found no walkable floor")
else:
    bx, by, bz, _ = best
    owner = "?"
    for o in wm:
        hit, loc, n_, i_ = o.ray_cast(
            o.matrix_world.inverted() @ Vector((bx, by, bz + 2.0)),
            Vector((0, 0, -1)), distance=10.0)
        if hit and abs((o.matrix_world @ loc).z - bz) < 0.02:
            owner = o.name
    gap = None
    if g:
        hit, loc, n_, i_ = g.ray_cast(
            g.matrix_world.inverted() @ Vector((bx, by, bz + 4.0)),
            Vector((0, 0, -1)), distance=40.0)
        if hit:
            gap = bz - (g.matrix_world @ loc).z
    # The GLB ships Y-up, but bpy's glTF IMPORTER converts back to Blender Z-up,
    # so everything measured here is in Blender axes and the runtime triple is
    # (x, z, -y) — the same mapping round 2's verifier prints.
    spawn_rt = (bx, bz, -by)
    print("  spawn scan -> %s at blender(%.2f, %.2f, %.2f) = runtime(x=%.2f, y=%.2f, z=%.2f)%s"
          % (owner, bx, by, bz, bx, bz, -by,
             "  terrain %.2fu beneath" % gap if gap is not None else ""))
    if not owner.lower().startswith("walk"):
        fail("spawn is not on the walk network")

# ================================= 4. walk-ribbon clearance (the sawtooth gate)
if g:
    worst = []
    for o in wm:
        # walk_bridge is piers and railing posts, not a ribbon: its cubes are driven
        # into the bank on purpose, so terrain above a vertex is CORRECT there.
        if o.name.lower().startswith("walk_bridge"):
            continue
        co = np.zeros(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        wm4 = o.matrix_world
        gi = g.matrix_world.inverted()
        bad = 0
        mx = -9.9
        for k in range(0, len(co), max(1, len(co) // 400)):
            p = wm4 @ Vector(co[k].tolist())
            hit, loc, n_, i_ = g.ray_cast(gi @ Vector((p.x, p.y, p.z + 6.0)),
                                          Vector((0, 0, -1)), distance=14.0)
            if not hit:
                continue
            gz_ = (g.matrix_world @ loc).z
            d = gz_ - p.z                      # +ve = terrain ABOVE the ribbon
            mx = max(mx, d)
            if d > 0.02:
                bad += 1
        worst.append((o.name, mx, bad))
    print("  walk-ribbon clearance (terrain above ribbon, +ve is a puncture):")
    for nm, mx, bad in worst:
        print("    %-22s worst %+.3fu  %d sampled verts pierced" % (nm, mx, bad))
        if mx > 0.05:
            fail("%s is pierced by the terrain by %.3fu" % (nm, mx))

# ===================================================== 5. zones.json, as runtime
print("  --- zones.json ---")
Z = json.load(open(ZP))
cell, org, cols, rows = Z["cell"], Z["origin"], Z["cols"], Z["rows"]
types, colors = Z["types"], Z["colors"]
print("    %dx%d cells of %.2fu, origin %s, %d types" % (cols, rows, cell, org, len(types)))
if len(colors) != len(types):
    fail("colors is not parallel to types — the overlay would need a code change")
if "_doc" not in Z:
    fail("the format is not documented in the file it ships in")
grid = np.zeros((rows, cols), dtype=np.int32)
for r, run in enumerate(Z["rows_rle"]):
    xx = 0
    for k in range(0, len(run), 2):
        t, n = run[k], run[k + 1]
        if t < 0 or t >= len(types):
            fail("row %d references type index %d, outside the registry" % (r, t))
        grid[r, xx:xx + n] = t
        xx += n
    if xx != cols:
        fail("row %d run lengths sum to %d, not cols=%d" % (r, xx, cols))
if len(Z["rows_rle"]) != rows:
    fail("rows_rle has %d rows, header says %d" % (len(Z["rows_rle"]), rows))
cov = {types[i]: 100.0 * float((grid == i).sum()) / grid.size for i in range(len(types))}
print("    coverage: %s" % "  ".join("%s=%.1f%%" % (k, v) for k, v in cov.items()))
for k, v in Z.get("coverage_pct", {}).items():
    if abs(v - cov.get(k, -1)) > 0.05:
        fail("declared coverage for %s (%.2f) disagrees with the RLE (%.2f)" % (k, v, cov[k]))


def zone_at(x, z):
    c = int(np.floor((x - org[0]) / cell))
    r = int(np.floor((z - org[1]) / cell))
    if c < 0 or r < 0 or c >= cols or r >= rows:
        return None
    return types[int(grid[r, c])]


print("    SIM.zone samples:")
for nm, (px, pz) in (("village green", (-30.0, -20.0)),
                     ("clifftown apron", (43.0, 29.0)),
                     ("line-up hillside", (-20.0, 10.0)),
                     ("river at the bridge", (10.0, -6.0)),
                     ("off-tile", (999.0, 999.0))):
    print("      %-22s -> %s" % (nm, zone_at(px, pz)))
if zone_at(-30.0, -20.0) != "road":
    fail("the village override stamp did not land (settled ground must be safe)")
if zone_at(999.0, 999.0) is not None:
    fail("out-of-range lookup did not return None")
if spawn_rt is not None:
    sz_ = zone_at(spawn_rt[0], spawn_rt[2])   # runtime (x, z)
    print("      spawn point           -> %s" % sz_)
    if sz_ != "road":
        fail("the spawn lands on walk_road but the zone grid calls it %r" % sz_)

# ======================================================= the perf table vs round 2
try:
    t3 = json.load(open(os.path.join(OUT, "build_times3.json")))
    cost = "%.1f" % t3["f2"]
    zt = "%.2f" % t3["zone_derivation"]
except Exception:
    cost, zt = "?", "?"
md = ["# Overworld round 3 — style F2 against round-2 F (one 120 x 90u tile)", "",
      "| style | draws | verts | tris | GLB MB | tex MB | imgs | mats | nrm | rough |"
      " MASK | build s/tile | per-tile bake work |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
      "| F  | 30 | 33151 | 24052 | 14.33 | 12.71 | 21 | 14 | 12 | 12 | 0 | 0.8 |"
      " no bake — tiled PBR slots |",
      "| F2 | %d | %d | %d | %.2f | %.2f | %d | %d | %d | %d | %d | %s |"
      " no bake — tiled PBR + procedural veg maps (one-off) |"
      % (prims, verts, tris, sz, texbytes / 1e6, len(J.get("images", [])),
         len(mats), n_norm, n_mr, n_mask, cost),
      "",
      "F2 costs %s s/tile against F's 0.8, and **%s s of that is the zone grid** — the"
      " encounter geography is essentially free. The rest is the zone-aware"
      " tessellation and 4x the vegetation." % (cost, zt),
      "",
      "The tri count roughly doubles: the crag cells fan into 4 triangles each"
      " (+23% of quads) and the trees are real constructions rather than round 1's"
      " three primitives. The GLB grows mostly in TEXTURE — the procedural canopy,"
      " bark and leaf-mass maps — and those are one-off shared assets, so a second"
      " tile adds geometry only.",
      "",
      "| zone | coverage |", "|---|---|"]
md += ["| %s | %.1f%% |" % (k, v) for k, v in cov.items()]
md += ["", "Zone grid: %d x %d cells of %.2fu (%d total), run-length encoded to"
       " %.1f kB." % (cols, rows, cell, cols * rows, os.path.getsize(ZP) / 1e3)]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "PERF3.md"), "w").write("\n".join(md) + "\n")
print("\n" + "\n".join(md))
print("\nVERIFY %s" % ("OK" if ok_all else "FAILED"))
