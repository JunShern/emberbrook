# depth_bake.py — bake a CORRECT-BY-CONSTRUCTION scene bundle: background render,
# per-pixel depth map, and collision GLB all from the same blend in one session,
# so the image and the occlusion mask physically cannot disagree.
#
# Run: /Applications/Blender.app/Contents/MacOS/Blender -b <blend> -P tools/depth_bake.py -- <sceneKey>
# Produces public/assets/scenes/<sceneKey>/{background.png, stylized.png, depth.png, depth.json, scene.glb}
#
# depth.png encodes linear view-space depth (distance along the camera forward
# axis — NOT euclidean ray length; the runtime converts view-z to clip-z) packed
# 24-bit across RGB: v = (d - near) / (far - near), n = round(v * 0xFFFFFF),
# R = n>>16, G = (n>>8)&255, B = n&255. Zero radiance (no surface) = far plane.
# Baked at the runtime canvas resolution (1344x768), sampled with NearestFilter.

import bpy, os, sys, json, struct, zlib, contextlib, io

argv = sys.argv[sys.argv.index("--") + 1:]
scene_key = argv[0]
OUT = "/Users/junshernchan/projects/multiplayer-rpg/public/assets/scenes/" + scene_key
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
DW, DH = 1344, 768                       # depth = runtime drawing-buffer resolution

# --- GPU ---------------------------------------------------------------------
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

# --- camera ------------------------------------------------------------------
cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
cam = next((c for c in cams if 'int' in c.name.lower() or 'cam' in c.name.lower()), cams[0] if cams else None)
assert cam, "no camera in blend"
sc.camera = cam

# --- 1) background: the art render, scene untouched --------------------------
# (cutaway walls are visible_camera=False but still shadow/bounce light — they
#  must exist for this render, so nothing is deleted yet)
sc.render.engine = 'CYCLES'
sc.cycles.samples = min(getattr(sc.cycles, 'samples', 160), 160)
sc.render.resolution_x, sc.render.resolution_y = 2688, 1536
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.filepath = os.path.join(OUT, "background.png")
if os.environ.get('SKIP_BG') and os.path.exists(os.path.join(OUT, "background.png")):
    print("background reused (SKIP_BG)")
else:
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
import shutil
shutil.copyfile(os.path.join(OUT, "background.png"), os.path.join(OUT, "stylized.png"))
print("background rendered")

# --- 2) depth pass -----------------------------------------------------------
# Delete render-only volumes FIRST (a fog cube under material override becomes a
# solid emissive box). visible_camera=False objects need no handling: Cycles
# already hides them from camera rays, which is exactly the semantics we want —
# the depth map shows precisely what the background image shows.
VL = set(bpy.context.view_layer.objects.keys())
for o in list(bpy.data.objects):
    if o.type != 'MESH': continue
    n = o.name.lower()
    # 'smoke' catches the weapon shop's FORGE_SMOKE — an 8-vert volume DOMAIN box
    # exactly like the fog/steam cubes; under the override it would bake as a
    # solid 1.2 m slab of depth hanging over the forge.
    if ('fog' in n) or ('haze' in n) or ('steam_vol' in n) or ('smoke' in n) or ('shadow_ceiling' in n) or (o.name not in VL):
        bpy.data.objects.remove(o, do_unlink=True)

# override every surface with emission = view-space depth
dm = bpy.data.materials.new("DEPTH_OVERRIDE"); dm.use_nodes = True
nt = dm.node_tree; nt.nodes.clear()
n_geo  = nt.nodes.new('ShaderNodeNewGeometry')
n_xf   = nt.nodes.new('ShaderNodeVectorTransform')
n_xf.vector_type = 'POINT'; n_xf.convert_from = 'WORLD'; n_xf.convert_to = 'CAMERA'
n_sep  = nt.nodes.new('ShaderNodeSeparateXYZ')
# NOTE: Cycles' shader-space "camera" transform has +Z pointing INTO the scene
# (opposite of Blender's object-space camera convention) — negate-and-clamp
# renders black. ABSOLUTE is correct in both conventions.
n_neg  = nt.nodes.new('ShaderNodeMath'); n_neg.operation = 'ABSOLUTE'
n_em   = nt.nodes.new('ShaderNodeEmission'); n_em.inputs['Color'].default_value = (1, 1, 1, 1)
n_out  = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(n_geo.outputs['Position'], n_xf.inputs['Vector'])
nt.links.new(n_xf.outputs['Vector'],   n_sep.inputs['Vector'])
nt.links.new(n_sep.outputs['Z'],       n_neg.inputs[0])
nt.links.new(n_neg.outputs['Value'],   n_em.inputs['Strength'])
nt.links.new(n_em.outputs['Emission'], n_out.inputs['Surface'])
bpy.context.view_layer.material_override = dm

w = bpy.data.worlds.new("DEPTH_WORLD"); w.use_nodes = True
for nd in w.node_tree.nodes:
    if nd.type == 'BACKGROUND': nd.inputs['Strength'].default_value = 0.0
sc.world = w
sc.cycles.samples = 1
sc.cycles.use_denoising = False
sc.cycles.film_exposure = 1.0
sc.render.filter_size = 0.01                       # no AA: never blend depths across edges
sc.render.resolution_x, sc.render.resolution_y = DW, DH
sc.render.image_settings.file_format = 'OPEN_EXR'
sc.render.image_settings.color_mode = 'RGB'
sc.render.image_settings.color_depth = '32'
exr = os.path.join(OUT, "_depth_raw.exr")
sc.render.filepath = exr
with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.render.render(write_still=True)

img = bpy.data.images.load(exr)
px = list(img.pixels)                              # RGBA float, bottom-up rows
d = [px[i] for i in range(0, len(px), 4)]          # R channel = view depth
hit = [v for v in d if v > 1e-6]
near, far = min(hit), max(hit)
rng = max(far - near, 1e-6)
print("depth range: %.3f .. %.3f" % (near, far))

# pack 24-bit RGB PNG (top-down rows; pure-python zlib encoder, no PIL)
rows = []
for y in range(DH - 1, -1, -1):                    # EXR bottom-up -> PNG top-down
    row = bytearray([0])                           # filter type 0
    base = y * DW
    for x in range(DW):
        v = d[base + x]
        n = 0xFFFFFF if v <= 1e-6 else max(0, min(0xFFFFFF, round((v - near) / rng * 0xFFFFFF)))
        row += bytes(((n >> 16) & 255, (n >> 8) & 255, n & 255))
    rows.append(bytes(row))
def chunk(tag, data):
    c = tag + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", DW, DH, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(b"".join(rows), 6))
       + chunk(b"IEND", b""))
open(os.path.join(OUT, "depth.png"), "wb").write(png)
json.dump({"near": near, "far": far, "width": DW, "height": DH, "encoding": "rgb24-viewz"},
          open(os.path.join(OUT, "depth.json"), "w"))
os.remove(exr)
print("depth.png + depth.json written")

# --- 3) collision GLB (same strip semantics as interior_export.py) -----------
bpy.context.view_layer.material_override = None
for o in list(bpy.data.objects):
    if o.type != 'MESH': continue
    name = o.name.lower()
    hidden = (not o.visible_camera) or o.hide_render or o.hide_viewport
    if o.name.startswith('walk_'): continue        # collision pads: hide_render by design
    if hidden:
        bpy.data.objects.remove(o, do_unlink=True)
with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "scene.glb"),
                              export_yup=True, export_cameras=True, export_lights=False)
n_walk = sum(1 for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('walk_'))
print("DEPTH BUNDLE OK %s | cam=%s | walk=%d | near=%.3f far=%.3f" % (scene_key, cam.name, n_walk, near, far))
