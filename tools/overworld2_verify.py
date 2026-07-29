"""overworld2_verify.py — round-2 glTF round-trip proof + the world-scale perf table.

  Blender -b --factory-startup -P tools/overworld2_verify.py -- [e,f,g,h]

Two jobs, one Blender launch:

 1. ROUND TRIP.  Re-import each shipped GLB into an EMPTY blend (nothing from the
    authoring file can prop it up) and report what actually arrived: COLOR_0,
    baseColorTexture, normalTexture, metallicRoughnessTexture, emissiveTexture,
    alphaMode, the second UV set style G's detail normal rides on, and the
    walk_ / water_ / veg_ naming the runtime keys off.

 2. PERF.  Parse the GLB's own JSON chunk for the numbers that decide whether a
    style can cover a WORLD rather than one 120x90 tile: draw calls (primitives),
    verts, tris, embedded texture bytes, file size.  Writes docs/qa/overworld/PERF2.md.
"""
import bpy, os, sys, json, struct
import numpy as np

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
OUT = os.path.join(ROOT, "docs/qa/overworld")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STYLES = argv[0].split(",") if argv else ["e", "f", "g", "h"]


def glb_json(path):
    with open(path, "rb") as f:
        magic, ver, total = struct.unpack("<III", f.read(12))
        ln, kind = struct.unpack("<II", f.read(8))
        return json.loads(f.read(ln).decode("utf-8"))


rows = []
ok_all = True
for s in STYLES:
    glb = os.path.join(ROOT, "public/assets/scenes/ow-proto-%s/scene.glb" % s)
    if not os.path.exists(glb):
        print("MISSING", glb)
        ok_all = False
        continue
    J = glb_json(glb)

    prims = sum(len(m["primitives"]) for m in J.get("meshes", []))
    verts = tris = 0
    acc = J.get("accessors", [])
    for m in J.get("meshes", []):
        for p in m["primitives"]:
            verts += acc[p["attributes"]["POSITION"]]["count"]
            tris += acc[p["indices"]]["count"] // 3 if "indices" in p else 0
    texbytes = sum(J["bufferViews"][im["bufferView"]]["byteLength"]
                   for im in J.get("images", []) if "bufferView" in im)
    mats = J.get("materials", [])
    n_norm = sum(1 for m in mats if "normalTexture" in m)
    n_mr = sum(1 for m in mats if "metallicRoughnessTexture" in m.get("pbrMetallicRoughness", {}))
    n_emis = sum(1 for m in mats if "emissiveTexture" in m)
    n_mask = sum(1 for m in mats if m.get("alphaMode") == "MASK")
    n_blend = sum(1 for m in mats if m.get("alphaMode") == "BLEND")
    n_2uv = sum(1 for m in mats
                if any(v.get("texCoord", 0) > 0 for v in
                       [m.get("normalTexture", {}),
                        m.get("pbrMetallicRoughness", {}).get("baseColorTexture", {}),
                        m.get("emissiveTexture", {})]))
    sz = os.path.getsize(glb) / 1e6

    print("\n=== STYLE %s ===============================================" % s.upper())
    print("  %d meshes / %d primitives (draw calls), %d verts, %d tris"
          % (len(J.get("meshes", [])), prims, verts, tris))
    print("  %.2f MB GLB, %.2f MB embedded texture, %d images, %d materials"
          % (sz, texbytes / 1e6, len(J.get("images", [])), len(mats)))
    print("  normalTexture %d, metallicRoughness %d, emissiveTexture %d, "
          "alphaMode MASK %d / BLEND %d, TEXCOORD_1 users %d"
          % (n_norm, n_mr, n_emis, n_mask, n_blend, n_2uv))
    mimes = {}
    for im in J.get("images", []):
        mimes[im.get("mimeType", "?")] = mimes.get(im.get("mimeType", "?"), 0) + 1
    print("  image mime types: %s" % mimes)
    # a MASK material whose baseColor image came out as JPEG has NO alpha left and
    # the cutout silently becomes a solid card — check it explicitly
    for m in mats:
        if m.get("alphaMode") == "MASK":
            ti = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
            src = J["textures"][ti]["source"]
            mt = J["images"][src].get("mimeType", "?")
            print("    MASK material %-14s baseColor image mime=%s %s"
                  % (m.get("name", "?"), mt, "OK" if "png" in mt else "*** ALPHA LOST"))
            if "png" not in mt:
                ok_all = False

    # ---- re-import into an empty blend ------------------------------------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
    walk = sorted(o.name for o in meshes if o.name.lower().startswith("walk"))
    water = sorted(o.name for o in meshes if o.name.lower().startswith("water_"))
    veg = sorted(o.name for o in meshes if o.name.lower().startswith("veg_"))
    boat = [o.name for o in meshes if o.name.lower().startswith("boat_")]
    print("  cameras: %d   walk_: %s" % (len(cams), ", ".join(walk) or "NONE <-- spawn falls back"))
    print("  water_: %s" % (", ".join(water) or "NONE"))
    print("  veg_:   %s   boat: %s" % (", ".join(veg) or "NONE", ", ".join(boat) or "NONE"))
    if not walk or not boat:
        ok_all = False
        print("  *** FAIL: missing walk network or boat_tar")

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
    if g:
        uvs = [u.name for u in g.data.uv_layers]
        mt = g.data.materials[0] if g.data.materials else None
        ims = []
        if mt and mt.node_tree:
            ims = [(n.image.name, tuple(n.image.size)) for n in mt.node_tree.nodes
                   if n.type == "TEX_IMAGE" and n.image]
        print("  ground_valley: %d slots, uv sets %s, images %s"
              % (len(g.data.materials), uvs, ims))
        if not ims and not g.data.color_attributes.active_color:
            ok_all = False
            print("  *** FAIL: terrain has neither COLOR_0 nor a texture")

    # ---- replicate the runtime's own spawn scan --------------------------
    # public/play3d.html: bbox over walk_ meshes, 64-step grid, highest walk floor,
    # nearest the bbox centre by manhattan distance.  If this lands off the network
    # the prototype is unplayable no matter how it renders.
    from mathutils import Vector
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
    dep = bpy.context.evaluated_depsgraph_get()
    best = None
    x = bb[0].x
    while x <= bb[1].x:
        y = bb[0].y
        while y <= bb[1].y:
            top = None
            for o in wm:
                hit, loc, nrm, idx = o.ray_cast(o.matrix_world.inverted()
                                                @ Vector((x, y, bb[1].z + 40.0)),
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
    if best is None:
        ok_all = False
        print("  *** FAIL: spawn scan found no walkable floor")
    else:
        bx, by, bz, _ = best
        owner = "?"
        gap = None
        for o in wm:
            hit, loc, n_, i_ = o.ray_cast(o.matrix_world.inverted()
                                          @ Vector((bx, by, bz + 2.0)),
                                          Vector((0, 0, -1)), distance=10.0)
            if hit and abs((o.matrix_world @ loc).z - bz) < 0.02:
                owner = o.name
        gr = bpy.data.objects.get("ground_valley")
        if gr:
            hit, loc, n_, i_ = gr.ray_cast(gr.matrix_world.inverted()
                                           @ Vector((bx, by, bz + 4.0)),
                                           Vector((0, 0, -1)), distance=40.0)
            if hit:
                gap = bz - (gr.matrix_world @ loc).z
        print("  spawn scan -> %s at blender(%.2f, %.2f, %.2f) = runtime(x=%.2f, y=%.2f, z=%.2f)"
              "%s" % (owner, bx, by, bz, bx, bz, -by,
                      "  terrain %.2fu beneath" % gap if gap is not None else ""))
        if not owner.lower().startswith("walk"):
            ok_all = False
            print("  *** FAIL: spawn is not on the walk network")

    rows.append(dict(style=s.upper(), prims=prims, verts=verts, tris=tris, mb=sz,
                     texmb=texbytes / 1e6, imgs=len(J.get("images", [])),
                     mats=len(mats), norm=n_norm, mr=n_mr, emis=n_emis,
                     mask=n_mask, uv2=n_2uv))

BUILD = {"E": "2 Cycles bakes (albedo + dusk lighting) per tile",
         "F": "no bake — tiled PBR slots, per-material only",
         "G": "2 Cycles bakes (albedo + AO) per tile",
         "H": "1 Cycles bake (albedo) per tile + one-off card atlases"}
try:
    COST = {k.upper(): "%.1f" % v for k, v in
            json.load(open(os.path.join(OUT, "build_times.json"))).items()}
except Exception:
    COST = {}

md = ["# Overworld round 2 — perf per style (one 120 x 90u tile)", "",
      "| style | draws | verts | tris | GLB MB | tex MB | imgs | mats | "
      "nrm | rough | emis | MASK | UV1 | build s/tile | per-tile bake work |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append("| %s | %d | %d | %d | %.2f | %.2f | %d | %d | %d | %d | %d | %d | %d | %s | %s |"
              % (r["style"], r["prims"], r["verts"], r["tris"], r["mb"], r["texmb"],
                 r["imgs"], r["mats"], r["norm"], r["mr"], r["emis"], r["mask"],
                 r["uv2"], COST.get(r["style"], "?"), BUILD.get(r["style"], "")))
md += ["",
       "`build s/tile` is wall-clock inside overworld2_build.py on an M1 Max "
       "(Cycles baking on Metal).  It is the number that decides whether a style "
       "can cover a world: E and G pay it AGAIN for every new tile, F and H "
       "essentially do not.",
       "", "Texture MB is what is embedded in the GLB.  F's is the shared PolyHaven "
       "set at 1k (diffuse+normal+roughness x 4 terrain classes x 5 prop classes); "
       "E/G/H's is dominated by their single baked 2048 terrain map."]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "PERF2.md"), "w").write("\n".join(md) + "\n")
print("\n" + "\n".join(md))
print("\nVERIFY %s" % ("OK" if ok_all else "FAILED"))
