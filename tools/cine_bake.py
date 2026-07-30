# cine_bake.py — bake DELLHOLLOW'S CINEMATIC SHOTS out of the live master.
#
#   Blender -b tools/blends/dellhollow-master.blend -P tools/cine_bake.py -- [opts]
#     --glb              export the shared collision GLB + meta.json only, no rendering
#     --cams a,b,c       bake only these camera ids (default: all in the solved file)
#     --samples N        Cycles samples for the beauty render (default 128, denoised)
#     --res WxH          beauty resolution (default 2688x1536)
#     --skip-existing    leave a camera alone if its bg.png is already on disk
#
# WHAT THIS IS. tools/depth_bake.py is the canon bundle exporter for a scene with ONE
# camera: one Blender session on the ORIGINAL blend (read-only — never copy a blend,
# relative texture paths break, manifest 63) renders the background, bakes the
# view-space depth map from the SAME camera, and exports the collision GLB, so the
# image and the occlusion physically cannot disagree. This is that pipeline
# generalised to N cameras over ONE town:
#
#   * the depth contract is IDENTICAL, per camera: bg.png and depth.png come from the
#     same session, same transform, same camera. Nothing about exact-pixel occlusion
#     is weakened by there being sixteen of them.
#   * the collision GLB is exported ONCE and SHARED. A master-baked bundle carries the
#     whole town's collision (canon), so eighteen per-camera bundles would have meant
#     ~330 MB of byte-identical GLB in git and a multi-second bundle reload on every
#     camera cut — which is not a cut, it is a loading screen. One bundle, N art
#     pairs, and the runtime's scene-internal handoff swaps two textures.
#   * every camera NUMBER comes from townmap/dellhollow.cameras.solved.json, which the
#     runtime also reads (through cine.json). Nothing about a camera is typed here.
#
# ORDER IS LOAD-BEARING: all beauty renders first, THEN the volume deletion + depth
# override, THEN all depth renders, THEN the GLB. The depth pass destroys the scene
# for beauty work (fog cubes deleted, every surface overridden with an emission
# shader), so it cannot be interleaved.
#
# Output: public/assets/scenes/del-cine/
#   scene.glb                    shared collision + walk_ surfaces (whole town)
#   cine.json                    per camera: pos/aim/fov/clip, depth near/far, spawn
#   cameras/<id>/bg.png          THE DELIVERABLE ART (Cycles, AgX, the accepted grade)
#   cameras/<id>/depth.png       rgb24 view-space depth at runtime canvas resolution
#   meta.json                    export stamp (the HUD shows master@<time>)

import bpy, os, sys, json, struct, zlib, contextlib, io, math, time
# unbuffered: a 60-minute bake must report progress as it happens, not at exit
try: sys.stdout.reconfigure(line_buffering=True)
except Exception: pass
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
SOLVED = os.path.join(REPO, "public/townmap/dellhollow.cameras.solved.json")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def opt(name, default=None):
    if name in argv:
        i = argv.index(name)
        return argv[i + 1] if (default is not None and i + 1 < len(argv)) else True
    return default

GLB_ONLY = "--glb" in argv
SKIP_EXISTING = "--skip-existing" in argv
SAMPLES = int(opt("--samples", "128"))
RES = opt("--res", "2688x1536")
BW, BH = [int(v) for v in RES.split("x")]
DW, DH = 1344, 768                      # depth = the runtime drawing buffer, exactly

S = json.load(open(SOLVED))
OUT = os.path.join(REPO, "public/assets/scenes", S["sceneKey"])
ART = os.path.join(OUT, "cameras")
os.makedirs(ART, exist_ok=True)
CAMS = {c["id"]: c for c in S["cameras"]}
want = opt("--cams", "")
ids = [i for i in (want.split(",") if want and want is not True else list(CAMS))if i in CAMS]
if want and want is not True:
    missing = [i for i in want.split(",") if i not in CAMS]
    assert not missing, "unknown camera ids: %s" % missing

sc = bpy.context.scene
D = S["defaults"]
T0 = time.time()

# --- GPU ----------------------------------------------------------------------
prefs = bpy.context.preferences.addons.get('cycles')
if prefs:
    cp = prefs.preferences
    try:
        cp.compute_device_type = 'METAL'
        cp.get_devices()
        for d in cp.devices: d.use = True
        sc.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, CPU fallback:", e)

# --- the grade: one place, from the data ---------------------------------------
sc.view_settings.view_transform = D.get("view_transform", "AgX")
sc.view_settings.look = D.get("look", "AgX - Medium High Contrast")
sc.view_settings.exposure = D.get("exposure", 0.0)

def build_cam(c):
    """The ONLY place a Blender camera is created. Every number comes from the
    solved file, which play3d.html also reads — bake and runtime cannot disagree
    about where a camera stands (supervisor condition 1)."""
    name = "cine_" + c["id"]
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(c["fov"])
    cd.clip_start, cd.clip_end = c["clip"][0], c["clip"][1]
    ob = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(ob)
    ob.location = Vector(c["pos"])
    ob.rotation_euler = (Vector(c["aim"]) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob

def visibility(c, cam):
    """Can this camera SEE the region it owns? Ray-cast the solved probe points
    (character-head height, spread over every owned walk mesh). The map's draft
    cameras were buried INSIDE the cliffs by a fixed standoff and no number in the
    file said so — this is the number that says so."""
    dg = bpy.context.evaluated_depsgraph_get()
    origin = cam.matrix_world.translation
    seen = 0
    probes = c.get("probes", [])
    for p in probes:
        tgt = Vector(p)
        vec = tgt - origin
        L = vec.length
        if L < 1e-4: continue
        hit, *_ = sc.ray_cast(dg, origin, vec.normalized(), distance=L - 0.35)
        if not hit: seen += 1
    return (seen / len(probes)) if probes else 0.0, len(probes)

def pick_spawn(c, cam):
    """Bundle-level fallback spawn for this shot: the candidate nearest the region
    centre that the camera can actually see. (The runtime's ?sx&sy&sz arrival from a
    graph edge OUTRANKS this — bundle spawns are the fallback, per the brief.)
    Returned in RUNTIME coords (x, h, -y)."""
    dg = bpy.context.evaluated_depsgraph_get()
    origin = cam.matrix_world.translation
    # Test the CHEST and the HEAD, and require both. Head-only testing picked a spawn
    # on the rim road that the runtime rendered fully hidden behind the road's palisade:
    # a 1.4 m fence is transparent to a 1.7 m probe and opaque to a walking character.
    for cand in c.get("spawnCandidates", []):
        p = cand["at"]
        clear = True
        for hgt in (0.85, 1.6):
            tgt = Vector((p[0], p[1], p[2] + hgt))
            vec = tgt - origin
            if vec.length < 1e-4: clear = False; break
            hit, *_ = sc.ray_cast(dg, origin, vec.normalized(), distance=vec.length - 0.4)
            if hit: clear = False; break
        if clear:
            return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)], cand["from"], True
    if c.get("spawnCandidates"):
        p = c["spawnCandidates"][0]["at"]
        return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)], c["spawnCandidates"][0]["from"], False
    return None, None, False

def png_rgb24(depth_floats, w, h, near, rng, path):
    """Pack linear view depth into a 24-bit RGB PNG, top-down, no PIL.
    v = (d-near)/(far-near); n = round(v*0xFFFFFF); R=n>>16, G=(n>>8)&255, B=n&255.
    Zero radiance (no surface hit) = the far plane. Identical encoding to
    depth_bake.py, which is what public/play3d.html's fragment shader decodes."""
    rows = []
    for y in range(h - 1, -1, -1):                       # EXR is bottom-up
        row = bytearray([0])                             # PNG filter type 0
        base = y * w
        for x in range(w):
            v = depth_floats[base + x]
            n = 0xFFFFFF if v <= 1e-6 else max(0, min(0xFFFFFF, round((v - near) / rng * 0xFFFFFF)))
            row += bytes(((n >> 16) & 255, (n >> 8) & 255, n & 255))
        rows.append(bytes(row))
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 6))
        + chunk(b"IEND", b""))

# =============================================================== 1) BEAUTY =====
# The render norm's beauty-set ban does not apply here: these frames ARE the
# shipped art of the scene, not agent self-verification.
result = {}
todo = []
if not GLB_ONLY:
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = SAMPLES
    # Denoising ON for the beauty pass: these frames are the shipped art, and the
    # denoiser buys back most of what halving the sample count costs on a stylized
    # backdrop. (It is explicitly OFF for the depth pass below — a denoised depth map
    # would smear distances across silhouette edges, which is the one thing exact-pixel
    # occlusion cannot tolerate.)
    sc.cycles.use_denoising = True
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    for cid in ids:
        c = CAMS[cid]
        d = os.path.join(ART, cid)
        os.makedirs(d, exist_ok=True)
        bg = os.path.join(d, "bg.png")
        # RESUMABLE: --skip-existing reuses a beauty frame already on disk but still
        # builds the camera, re-probes visibility and bakes the depth map. Skipping the
        # camera outright would ship a background with no occlusion — the one pairing
        # this pipeline exists to make impossible. (A 3.5-minute Cycles frame is worth
        # resuming; a 20-second depth pass is not worth the risk.)
        cam = build_cam(c)
        sc.camera = cam
        vis, nprobe = visibility(c, cam)
        spawn, spawn_from, spawn_vis = pick_spawn(c, cam)
        el = 0.0
        if SKIP_EXISTING and os.path.exists(bg):
            print("REUSE %-14s existing bg.png (depth still baked)" % cid)
        else:
            sc.render.resolution_x, sc.render.resolution_y = BW, BH
            sc.cycles.samples = SAMPLES
            sc.render.filter_size = 1.5
            sc.render.filepath = bg
            t = time.time()
            with contextlib.redirect_stdout(io.StringIO()):
                bpy.ops.render.render(write_still=True)
            el = time.time() - t
        result[cid] = {"visibleFrac": round(vis, 4), "probes": nprobe,
                       "spawn": spawn, "spawnFrom": spawn_from, "spawnVisible": spawn_vis,
                       "bgSeconds": round(el, 1)}
        todo.append(cid)
        print("BG   %-14s %5.1fs  probes %d visible %.1f%%  spawn %s (%s)"
              % (cid, el, nprobe, vis * 100, spawn, spawn_from))

# ================================================================ 2) DEPTH =====
if todo:
    # Delete render-only volumes FIRST: under an emission override a fog domain
    # becomes a solid emissive box, i.e. a slab of fake depth hanging in the air.
    VL = set(bpy.context.view_layer.objects.keys())
    for o in list(bpy.data.objects):
        if o.type != 'MESH': continue
        n = o.name.lower()
        if (('fog' in n) or ('haze' in n) or ('steam_vol' in n) or ('smoke' in n)
                or ('shadow_ceiling' in n) or (o.name not in VL)):
            bpy.data.objects.remove(o, do_unlink=True)

    dm = bpy.data.materials.new("DEPTH_OVERRIDE"); dm.use_nodes = True
    nt = dm.node_tree; nt.nodes.clear()
    n_geo = nt.nodes.new('ShaderNodeNewGeometry')
    n_xf = nt.nodes.new('ShaderNodeVectorTransform')
    n_xf.vector_type = 'POINT'; n_xf.convert_from = 'WORLD'; n_xf.convert_to = 'CAMERA'
    n_sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    # Cycles' shader-space camera transform has +Z pointing INTO the scene (opposite
    # of Blender's object-space convention): negate-and-clamp renders black,
    # ABSOLUTE is correct in both (manifest 64).
    n_abs = nt.nodes.new('ShaderNodeMath'); n_abs.operation = 'ABSOLUTE'
    n_em = nt.nodes.new('ShaderNodeEmission'); n_em.inputs['Color'].default_value = (1, 1, 1, 1)
    n_out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(n_geo.outputs['Position'], n_xf.inputs['Vector'])
    nt.links.new(n_xf.outputs['Vector'], n_sep.inputs['Vector'])
    nt.links.new(n_sep.outputs['Z'], n_abs.inputs[0])
    nt.links.new(n_abs.outputs['Value'], n_em.inputs['Strength'])
    nt.links.new(n_em.outputs['Emission'], n_out.inputs['Surface'])
    bpy.context.view_layer.material_override = dm

    w = bpy.data.worlds.new("DEPTH_WORLD"); w.use_nodes = True
    for nd in w.node_tree.nodes:
        if nd.type == 'BACKGROUND': nd.inputs['Strength'].default_value = 0.0
    sc.world = w
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.view_settings.view_transform = "Standard"       # depth is DATA, never graded
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.render.filter_size = 0.01                       # no AA: never blend depths across edges
    sc.render.resolution_x, sc.render.resolution_y = DW, DH
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'

    for cid in todo:
        c = CAMS[cid]
        sc.camera = bpy.data.objects["cine_" + cid]
        exr = os.path.join(ART, cid, "_depth_raw.exr")
        sc.render.filepath = exr
        t = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(exr)
        px = list(img.pixels)
        dd = [px[i] for i in range(0, len(px), 4)]
        hit = [v for v in dd if v > 1e-6]
        near, far = (min(hit), max(hit)) if hit else (0.1, 100.0)
        rng = max(far - near, 1e-6)
        png_rgb24(dd, DW, DH, near, rng, os.path.join(ART, cid, "depth.png"))
        bpy.data.images.remove(img)
        os.remove(exr)
        # RUNTIME CLIP, derived: the fragment shader turns view depth into clip depth
        # through the RUNTIME camera's projection, so its near/far only have to
        # bracket the baked range. Bracketing it TIGHTLY instead of using Blender's
        # 0.05..1400 buys back the depth precision the character is z-tested with.
        rt_near = max(0.05, near * 0.5)
        rt_far = far * 1.6
        result[cid].update({"depth": {"near": near, "far": far, "width": DW, "height": DH,
                                      "encoding": "rgb24-viewz"},
                            "rtClip": [round(rt_near, 4), round(rt_far, 3)],
                            "depthSeconds": round(time.time() - t, 1)})
        print("DPT  %-14s %5.1fs  range %.2f .. %.2f  rtClip %.2f..%.1f"
              % (cid, time.time() - t, near, far, rt_near, rt_far))

# ================================================================== 3) GLB =====
if GLB_ONLY:
    bpy.context.view_layer.material_override = None
    for o in list(bpy.data.objects):
        if o.type != 'MESH': continue
        if o.name.startswith('walk_'): continue        # collision pads: hide_render by design
        if (not o.visible_camera) or o.hide_render or o.hide_viewport:
            bpy.data.objects.remove(o, do_unlink=True)
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "scene.glb"),
                                  export_yup=True, export_cameras=False, export_lights=False)
    n_walk = sum(1 for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('walk_'))
    json.dump({"exported": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "source": "tools/blends/dellhollow-master.blend",
               "tool": "tools/cine_bake.py --glb",
               "walkMeshes": n_walk,
               "note": "SHARED collision for every cinematic camera of del-cine. "
                       "The art (background + depth per camera) lives in cameras/<id>/ "
                       "and is indexed by cine.json."},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)
    print("GLB OK  walk=%d  %.1fs" % (n_walk, time.time() - T0))

# ------------------------------------------------------- 4) cine.json (merge) --
# Merged, not overwritten, so a PARTIAL re-bake is a first-class operation: the
# quay-market tier is under another agent's custody tonight and its three shots get
# re-baked alone once it lands (staleness is the only risk — bakes are read-only).
if result:
    p = os.path.join(OUT, "cine.json")
    doc = json.load(open(p)) if os.path.exists(p) else {}
    doc.setdefault("_doc", [
        "BAKED CINEMATIC CAMERAS for del-cine — what tools/cine_bake.py actually",
        "rendered, per camera. GENERATED; the authored intent is",
        "public/townmap/dellhollow.cameras.json and the solved numbers are",
        "public/townmap/dellhollow.cameras.solved.json (this file must agree with it —",
        "tools/cine_test.mjs asserts every link of that chain).",
        "public/play3d.html builds its THREE.PerspectiveCamera from pos/aim/fov/rtClip",
        "here, and its depth quad from depth.near/far + cameras/<id>/depth.png, so the",
        "shipped image and the shipped occlusion come from one bake of one camera.",
        "pos/aim are MAP/Blender coords [x, y, h]; spawn is RUNTIME [x, h, -y].",
    ])
    doc["sceneKey"] = S["sceneKey"]
    doc["generator"] = "tools/cine_bake.py"
    doc["defaults"] = {"aspect": D["aspect"], "charH": D["charH"],
                       "exposure": D["exposure"], "view_transform": D["view_transform"],
                       "look": D["look"], "beautyRes": [BW, BH], "samples": SAMPLES, "denoised": True}
    cams = {c["id"]: c for c in doc.get("cameras", [])}
    for cid in todo:
        c, r = CAMS[cid], result[cid]
        cams[cid] = {
            "id": cid, "name": c["name"], "entry": c.get("entry", False),
            "transit": c.get("transit", False),
            "pos": c["pos"], "aim": c["aim"], "fov": c["fov"], "clip": c["clip"],
            "rtClip": r.get("rtClip"), "depth": r.get("depth"),
            "art": {"bg": "cameras/%s/bg.png" % cid, "depth": "cameras/%s/depth.png" % cid},
            "spawn": r.get("spawn"), "spawnFrom": r.get("spawnFrom"),
            "visibleFrac": r.get("visibleFrac"), "probes": r.get("probes"),
            "baked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seconds": round((r.get("bgSeconds") or 0) + (r.get("depthSeconds") or 0), 1),
        }
    # stable order = the solved file's order (the player's route down the town)
    doc["cameras"] = [cams[c["id"]] for c in S["cameras"] if c["id"] in cams]
    json.dump(doc, open(p, "w"), indent=1)
    print("cine.json updated: %d of %d cameras baked (%s)"
          % (len(doc["cameras"]), len(S["cameras"]), ",".join(todo)))
print("CINE BAKE DONE %.1fs" % (time.time() - T0))
