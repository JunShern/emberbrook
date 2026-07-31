"""valley_verify.py — the valley region's glTF round-trip proof, gates and perf table.

  Blender -b --factory-startup -P tools/valley_verify.py

Five jobs, one Blender launch (round 3's verifier, re-aimed at the region):

 1. ROUND TRIP.  Re-import the shipped GLB into an EMPTY blend and report what
    actually arrived: COLOR_0, baseColor/normal/roughness, alphaMode, and the
    walk_/water_/veg_/fx_ naming the runtime keys off.  WHITE-MATERIAL GATE
    (MIGRATION canon, glTF-survival): any mesh whose COLOR_0 is flat white AND
    whose material carries no baseColor texture did not survive.
 2. SPAWN.  The runtime's own priority: meta.json pin first, then the scan.
 3. WALK-RIBBON CLEARANCE.  Every ribbon vertex against the treated ground.
 4. ZONES.  Decode zones.json exactly as the runtime does and check the region's
    own overrides landed (gorge rims crag, settlements safe, road along the road).
 5. PERF.  docs/qa/overworld/PERF_VALLEY.md — the region against the F2 tile, both
    absolutely and per 1000 square units, which is the only fair axis.
"""
import bpy
import json
import os
import struct
import sys

import numpy as np
from mathutils import Vector

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(ROOT, "docs/qa/overworld")
KEY = "ow-valley"
BUNDLE = os.path.join(ROOT, "public/assets/scenes", KEY)
GLB = os.path.join(BUNDLE, "scene.glb")
ZP = os.path.join(BUNDLE, "zones.json")
MP = os.path.join(BUNDLE, "meta.json")
F2 = dict(tile=(120.0, 90.0), draws=48, verts=116492, tris=53952, glb=22.50,
          tex=17.03, imgs=29, mats=17, build=2.07)

ok_all = True


def fail(m):
    global ok_all
    ok_all = False
    print("  *** FAIL: %s" % m)


def glb_json(path):
    with open(path, "rb") as f:
        struct.unpack("<III", f.read(12))
        ln, kind = struct.unpack("<II", f.read(8))
        return json.loads(f.read(ln).decode("utf-8"))


J = glb_json(GLB)
prims = sum(len(m["primitives"]) for m in J.get("meshes", []))
acc = J.get("accessors", [])
verts = tris = 0
attrbytes = {}
for m in J.get("meshes", []):
    for p in m["primitives"]:
        verts += acc[p["attributes"]["POSITION"]]["count"]
        tris += acc[p["indices"]]["count"] // 3 if "indices" in p else 0
        for a, ai in p["attributes"].items():
            bv = acc[ai].get("bufferView")
            if bv is not None:
                attrbytes[a] = attrbytes.get(a, 0) + J["bufferViews"][bv]["byteLength"]
        if "indices" in p:
            bv = acc[p["indices"]].get("bufferView")
            if bv is not None:
                attrbytes["INDICES"] = attrbytes.get("INDICES", 0) + J["bufferViews"][bv]["byteLength"]
texbytes = sum(J["bufferViews"][im["bufferView"]]["byteLength"]
               for im in J.get("images", []) if "bufferView" in im)
mats = J.get("materials", [])
n_norm = sum(1 for m in mats if "normalTexture" in m)
n_mr = sum(1 for m in mats
           if "metallicRoughnessTexture" in m.get("pbrMetallicRoughness", {}))
n_mask = sum(1 for m in mats if m.get("alphaMode") == "MASK")
n_blend = sum(1 for m in mats if m.get("alphaMode") == "BLEND")
sz = os.path.getsize(GLB) / 1e6

print("=== THE VALLEY (ow-valley) ==============================")
print("  %d meshes / %d primitives (draw calls), %d verts, %d tris"
      % (len(J.get("meshes", [])), prims, verts, tris))
print("  %.2f MB GLB, %.2f MB embedded texture, %d images, %d materials"
      % (sz, texbytes / 1e6, len(J.get("images", [])), len(mats)))
print("  geometry bytes: %s"
      % {k: "%.2f MB" % (v / 1e6) for k, v in sorted(attrbytes.items(), key=lambda kv: -kv[1])})
print("  normalTexture %d, metallicRoughness %d, alphaMode MASK %d / BLEND %d"
      % (n_norm, n_mr, n_mask, n_blend))
big = sorted(((J["bufferViews"][im["bufferView"]]["byteLength"], im.get("name", "?"),
               im.get("mimeType", "?")) for im in J.get("images", [])
              if "bufferView" in im), reverse=True)[:6]
print("  biggest images:")
for b, nm, mt in big:
    print("    %-34s %6.2f MB  %s" % (nm, b / 1e6, mt))
if n_mask == 0:
    fail("no alphaMode MASK material — the card fringe lost its cutout")
for m in mats:
    if m.get("alphaMode") == "MASK":
        ti = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        mt = J["images"][J["textures"][ti]["source"]].get("mimeType", "?")
        print("    MASK material %-16s baseColor mime=%s %s"
              % (m.get("name", "?"), mt, "OK" if "png" in mt else "ALPHA LOST"))
        if "png" not in mt:
            fail("MASK material %s lost its alpha to JPEG" % m.get("name"))

# ==================================================== re-import into an EMPTY
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
names = [o.name for o in meshes]
walk = sorted(n for n in names if n.lower().startswith("walk"))
water = sorted(n for n in names if n.lower().startswith("water_"))
veg = sorted(n for n in names if n.lower().startswith("veg_"))
trunks = sorted(n for n in names if n.lower().startswith("tree_"))
fx = sorted(n for n in names if n.lower().startswith("fx_"))
print("  cameras: %d" % len(cams))
print("  walk_:  %s" % (", ".join(walk) or "NONE"))
print("  water_: %s" % (", ".join(water) or "NONE"))
print("  veg_:   %s" % (", ".join(veg) or "NONE"))
print("  tree_:  %s" % (", ".join(trunks) or "NONE"))
print("  fx_:    %s" % (", ".join(fx) or "NONE"))
if not walk:
    fail("no walk network — spawn will fall back")
if not veg or not trunks:
    fail("veg_/tree_ split missing (finding 137: veg_ is never standable, so a trunk "
         "baked into a canopy mesh makes the whole tree walk-through)")
if not fx:
    fail("the fx_ vista ring did not ship")
if "qa_zone_overlay" in names:
    fail("the QA zone overlay shipped in the GLB")
for nm in ("ground_valley", "water_river", "walk_road", "boat_tar",
           "emberbrook", "dellhollow", "portal_markers"):
    if nm not in names:
        fail("%s is not in the GLB under that name" % nm)

# ---- THE WHITE-MATERIAL GATE ------------------------------------------------
n_vcol = n_white = 0
whites = []
for o in meshes:
    ca = o.data.color_attributes.active_color
    has_tex = False
    for mt in o.data.materials:
        if mt and mt.node_tree:
            has_tex = has_tex or any(n.type == "TEX_IMAGE" and n.image
                                     for n in mt.node_tree.nodes)
    if ca is not None:
        n_vcol += 1
        d = np.zeros(len(ca.data) * 4)
        ca.data.foreach_get("color", d)
        rgb = d.reshape(-1, 4)[:, :3]
        if rgb.std() < 0.002 and abs(rgb.mean() - 1.0) < 0.01 and not has_tex:
            n_white += 1
            whites.append(o.name)
    elif not has_tex:
        n_white += 1
        whites.append(o.name)
print("  COLOR_0 on %d/%d meshes; WHITE (no vcol AND no texture): %d %s"
      % (n_vcol, len(meshes), n_white, whites or ""))
if n_white:
    fail("%d mesh(es) export white: %s" % (n_white, whites))

g = bpy.data.objects.get("ground_valley")
if g is not None:
    nflat = sum(1 for p in g.data.polygons if not p.use_smooth)
    print("  ground_valley: %d slots, %d smooth / %d flat faces"
          % (len(g.data.materials), len(g.data.polygons) - nflat, nflat))
    if nflat == 0:
        fail("no flat-shaded facets survived — the crag treatment is gone")
    if nflat == len(g.data.polygons):
        fail("EVERY facet is flat — the smooth baseline is gone")

# ================================================ spawn (the runtime's priority)
M = json.load(open(MP)) if os.path.exists(MP) else {}
spawn_rt = M.get("spawn")
if spawn_rt is None:
    fail("meta.json has no spawn pin")
else:
    print("  meta.json spawn -> runtime %s  camYaw %s"
          % ([round(v, 2) for v in spawn_rt], M.get("camYaw")))
    # the runtime drops the pin onto the nearest walk floor beneath it
    bx, by, bz = spawn_rt[0], -spawn_rt[2], spawn_rt[1]
    owner, best = None, None
    for o in meshes:
        if not o.name.lower().startswith("walk"):
            continue
        hit, loc, n_, i_ = o.ray_cast(
            o.matrix_world.inverted() @ Vector((bx, by, bz + 6.0)),
            Vector((0, 0, -1)), distance=30.0)
        if hit:
            z = (o.matrix_world @ loc).z
            if best is None or abs(z - bz) < abs(best - bz):
                best, owner = z, o.name
    print("    lands on %s at z=%s (pin z=%.2f)"
          % (owner, "%.2f" % best if best is not None else "-", bz))
    if owner is None or not owner.lower().startswith("walk"):
        fail("the spawn pin does not land on the walk network")

# ===================================== walk-ribbon clearance (the sawtooth gate)
if g:
    print("  walk-ribbon clearance (terrain above ribbon, +ve is a puncture):")
    gi = g.matrix_world.inverted()
    # cast in the ground's LOCAL frame: transform the DIRECTION as well as the
    # origin — the glTF importer parks the Y-up axis conversion on the object
    # matrix, and an untransformed (0,0,-1) is a horizontal ray in local space
    # (five identical phantom "pierces" before this was caught).
    d_loc = (gi.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    for o in meshes:
        if not o.name.lower().startswith("walk"):
            continue
        co = np.zeros(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        bad, mx = 0, -9.9
        for k in range(0, len(co), max(1, len(co) // 500)):
            p = o.matrix_world @ Vector(co[k].tolist())
            hit, loc, n_, i_ = g.ray_cast(gi @ Vector((p.x, p.y, p.z + 8.0)),
                                          d_loc, distance=18.0)
            if not hit:
                continue
            d = (g.matrix_world @ loc).z - p.z
            mx = max(mx, d)
            if d > 0.02:
                bad += 1
        print("    %-24s worst %+.3fu  %d sampled verts pierced" % (o.name, mx, bad))
        # the dam crest and the causeway are DELIBERATELY driven into their banks
        if mx > 0.05 and o.name not in ("walk_dam_crest", "walk_causeway"):
            fail("%s is pierced by the terrain by %.3fu" % (o.name, mx))

# ===================================================== zones.json, as the runtime
print("  --- zones.json ---")
Z = json.load(open(ZP))
cell, org, cols, rows = Z["cell"], Z["origin"], Z["cols"], Z["rows"]
types, colors = Z["types"], Z["colors"]
print("    %dx%d cells of %.2fu, origin %s, %d types, region=%s"
      % (cols, rows, cell, org, len(types), Z.get("region")))
if len(colors) != len(types):
    fail("colors is not parallel to types")
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


# MAP-DERIVED CHECKS (fast-loop rule: the verifier reads the map, never
# fossilizes coordinates — v1's literal fixtures failed the moment the map moved).
_REG = json.load(open(os.path.join(ROOT, "public/world/regions/valley.region.json")))
_WLD = json.load(open(os.path.join(ROOT, "public/world/world.json")))
# ...and that rule now covers the FRAME, which was still fossilised right here as
# `wx - 140.0, 100.0 - wy`.  Two other tools each worked the tile out for themselves
# and disagreed by 2u; the tile is stated in world.json now and everything reads it.
_TILE = [r for r in _WLD["regions"] if r["id"] == _REG["region"]][0]["tile"]


def w2r(wx, wy):
    return wx - _TILE["origin"][0], _TILE["origin"][1] - wy


print("    SIM.zone samples (world coords -> runtime):")
# The expectations encode the REGION FILE's intent, not a guess:
#   settled ground is safe ground (the two townAnchor stamps)
#   the gorge rims are crag regardless of slope (the region's own crag stamp)
#   the road override is satisfied by derivation, not by a stamp
#   and THE DELLHOLLOW ANCHOR IS NO LONGER IN THE CHANNEL.  This check used to
#   REQUIRE 'water' there, reasoning that the town straddles the river and an
#   authored stamp never dries the river out.  Both halves died with the 2026-08-01
#   restamp: the town's mass is WEST BANK ONLY, and the anchor's 4.99u offset from a
#   12u-wide channel was a DEFECT, not a design — the field read 2.41 there against
#   the map's 12.0, i.e. the impression was being built underwater.  A verifier that
#   asserts a defect is worse than no verifier, because it defends it.  The
#   expectation is now "settled ground, and explicitly not water".
_anch = {a["town"]: a["pos"] for a in _REG["townAnchors"]}
_land = {l["id"]: l["pos"] for l in _REG.get("landmarks", [])}
_spmid = _WLD["riverSpine"]["points"][len(_WLD["riverSpine"]["points"]) // 2]["pos"]
CHECK = [("emberbrook anchor", tuple(_anch["emberbrook"][:2]), "road"),
         ("dellhollow anchor", tuple(_anch["dellhollow"][:2]), ("road", "meadow")),
         ("river spine mid", tuple(_spmid[:2]), "water"),
         ("off-tile", (9999, 9999), None)]
if "waystone" in _land:
    CHECK.insert(2, ("waystone / road", tuple(_land["waystone"][:2]), "road"))

def _inpoly(px, py, poly):
    inside = np.zeros(px.shape, bool)
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        m = ((yi > py) != (yj > py)) & (px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi)
        inside ^= m
        j = i
    return inside
# stamp-coverage assertions: an authored crag stamp must be mostly crag among its
# non-water cells; a canopy forest stamp mostly forest among plantable cells
_gx = org[0] + (np.arange(cols) + 0.5) * cell
_gz = org[1] + (np.arange(rows) + 0.5) * cell
_GX, _GZ = np.meshgrid(_gx, _gz)
_PWX, _PWY = _GX + 140.0, 100.0 - _GZ          # runtime -> world
def _cov(poly_w, target, elig):
    m = _inpoly(_PWX, _PWY, poly_w)
    tnames = np.array(types)[grid]
    el = m & np.isin(tnames, elig)
    if el.sum() == 0:
        return 0.0
    return float((tnames[el] == target).sum() / el.sum())
for st in _REG.get("zoneOverrides", []):
    if st.get("type") == "crag" and "stamp" in st:
        c = _cov(st["stamp"], "crag", ["crag", "meadow", "forest"])
        print("      crag stamp coverage    %.0f%%  (%s)" % (c * 100, st.get("note", "")[:40]))
        if c < 0.55:
            fail("crag override stamp is only %.0f%% crag" % (c * 100))
for st in _REG.get("forests", []):
    if st.get("representation") == "canopy":
        m = _inpoly(_PWX, _PWY, st["stamp"])
        tn = np.array(types)[grid]
        elig = m & np.isin(tn, ["forest", "meadow"])
        if elig.sum() < 0.10 * max(m.sum(), 1):
            # the stamp lives on override-claimed ground (e.g. the unreachable
            # farwall clifftop is zone=crag by ruling); the canopy MESH still
            # dresses it — encounter zoning and scenery are allowed to differ
            # where the player cannot stand
            print("      canopy %-14s  on override ground (%.0f%% eligible) — mesh-only, OK"
                  % (st["id"], 100.0 * elig.sum() / max(m.sum(), 1)))
            continue
        c = float((tn[elig] == "forest").sum() / elig.sum())
        print("      canopy %-14s  %.0f%% forest" % (st["id"], c * 100))
        if c < 0.45:
            fail("canopy stamp %s is only %.0f%% forest among plantable cells" % (st["id"], c * 100))
for nm, (wx, wy), want in CHECK:
    x, z = w2r(wx, wy)
    got = zone_at(x, z)
    flag = ""
    okset = want if isinstance(want, tuple) else (want,)
    if want is not None and got not in okset:
        flag = "  <-- expected %s" % (" or ".join(okset))
        fail("zone at %s (%s) is %r, expected %s" % (nm, (wx, wy), got, " or ".join(okset)))
    print("      %-20s -> %-8s%s" % (nm, got, flag))
if zone_at(9999, 9999) is not None:
    fail("out-of-range lookup did not return None")
if spawn_rt is not None:
    szn = zone_at(spawn_rt[0], spawn_rt[2])
    print("      %-20s -> %s" % ("spawn point", szn))
    if szn != "road":
        fail("the spawn is on walk_road but the zone grid calls it %r" % szn)

# ============================================================ the perf table
try:
    rec = json.load(open(os.path.join(OUT, "valley_build.json")))
except Exception:
    rec = {}
area_v = 280.0 * 200.0 / 1000.0
area_f = F2["tile"][0] * F2["tile"][1] / 1000.0
cost = rec.get("build_s", 0.0)


def per(v, a):
    return v / a


md = [
    "# The Valley region against the F2 prototype tile", "",
    "The region is **%.0f x %.0fu = %.1f k square units**, the F2 tile was "
    "%.0f x %.0fu = %.1f k — **%.1fx the area**.  Absolute numbers are what the "
    "runtime pays; the per-1000-square-unit column is the only fair comparison of "
    "the two builds."
    % (280, 200, area_v, F2["tile"][0], F2["tile"][1], area_f, area_v / area_f), "",
    "| | F2 tile | valley | F2 per 1k u2 | valley per 1k u2 |",
    "|---|---|---|---|---|",
    "| draw calls | %d | %d | %.2f | %.2f |" % (F2["draws"], prims, per(F2["draws"], area_f), per(prims, area_v)),
    "| verts | %d | %d | %.0f | %.0f |" % (F2["verts"], verts, per(F2["verts"], area_f), per(verts, area_v)),
    "| tris | %d | %d | %.0f | %.0f |" % (F2["tris"], tris, per(F2["tris"], area_f), per(tris, area_v)),
    "| GLB MB | %.2f | %.2f | %.2f | %.2f |" % (F2["glb"], sz, per(F2["glb"], area_f), per(sz, area_v)),
    "| embedded texture MB | %.2f | %.2f | - | - |" % (F2["tex"], texbytes / 1e6),
    "| images | %d | %d | - | - |" % (F2["imgs"], len(J.get("images", []))),
    "| materials | %d | %d | - | - |" % (F2["mats"], len(mats)),
    "| build s | %.2f | %.2f | %.3f | %.3f |" % (F2["build"], cost, per(F2["build"], area_f), per(cost, area_v)),
    "",
    "Where the build time goes: field %.2fs, zone grid %.3fs, terrain mesh %.2fs, "
    "planting %.2fs (%d trees).  The zone grid — the whole encounter geography of a "
    "280 x 200u region, 224 x 160 cells — costs **%.3f s**."
    % (rec.get("field_s", 0), rec.get("zone_s", 0), rec.get("terrain_s", 0),
       rec.get("veg_s", 0), rec.get("trees", 0), rec.get("zone_s", 0)),
    "",
    "Geometry byte budget inside the GLB:", "",
    "| attribute | MB |", "|---|---|",
]
md += ["| %s | %.2f |" % (k, v / 1e6)
       for k, v in sorted(attrbytes.items(), key=lambda kv: -kv[1])]
md += ["| embedded images | %.2f |" % (texbytes / 1e6), "",
       "| zone | coverage |", "|---|---|"]
md += ["| %s | %.1f%% |" % (k, v) for k, v in cov.items()]
md += ["", "Zone grid: %d x %d cells of %.2fu (%d total), run-length encoded to "
       "%.1f kB." % (cols, rows, cell, cols * rows, os.path.getsize(ZP) / 1e3)]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "PERF_VALLEY.md"), "w").write("\n".join(md) + "\n")
print("\n" + "\n".join(md))
print("\nVERIFY %s" % ("OK" if ok_all else "FAILED"))
sys.exit(0 if ok_all else 1)      # the fast-loop wrapper (set -e) must stop on FAIL
