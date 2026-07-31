# emb_export.py — export the Emberbrook master as the `emb-walk` runtime bundle.
#
#   Blender -b tools/blends/emberbrook-master.blend -P tools/emb_export.py \
#       --python-exit-code 1 -- [--out <dir>] [--preview]
#
# Produces public/assets/scenes/emb-walk/{background.png, stylized.png, scene.glb}:
# the whole-town REAL-TIME bundle, which is (a) the developer's explore view and (b)
# the geometry every camera tool measures — `cine_solve.mjs --town emberbrook` reads
# `assets/scenes/<map.walkSceneKey>/scene.glb` and derives every camera's region from
# the `walk_` meshes inside it.  If this file is stale, every camera number is stale.
#
# WHY NOT tools/town_export.py, which already does this and has a TOWNWALK_OUT
# override.  Because its one framing heuristic is Dellhollow-shaped:
#
#     span = max(max(xs)-min(xs), (max(zs)-min(zs)) * 1.75) * 1.08
#
# — the vertical extent it fits is the town's HEIGHT.  Dellhollow is a canyon wall and
# that is nearly its whole depth; Emberbrook is 3 m tall and 40 m deep, so the ortho
# frame came out 36.7 units and cropped two thirds of the village off the top.  This
# file fits the walk network's own footprint through the actual view axes instead, and
# is otherwise the same export with the same flags.
#
# The GLB carries EVERY mesh, not only the walkable ones: `walk_` pads are
# `hide_render` by design and must still export (they are the collision), and every
# other mesh is what the runtime depth-tests the character against.

import bpy, os, sys, shutil, contextlib, io, re, math, json, time
from mathutils import Vector

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(flag, default):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUT = opt("--out", os.path.join(REPO, "public/assets/scenes/emb-walk"))
PREVIEW = "--preview" in argv
SAMPLES = int(opt("--samples", "24"))
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene

# ---- frame the PLAYABLE town, not stray helpers ------------------------------
P = [o.matrix_world @ Vector(c) for o in bpy.data.objects
     if o.type == 'MESH' and o.name.startswith("walk_") for c in o.bound_box]
assert P, "no walk_ geometry in this blend — is it the Emberbrook master?"
cx = (min(p.x for p in P) + max(p.x for p in P)) / 2
cy = (min(p.y for p in P) + max(p.y for p in P)) / 2
cz = (min(p.z for p in P) + max(p.z for p in P)) / 2
ctr = Vector((cx, cy, cz))

cd = bpy.data.cameras.new("cam_emb_walk")
cd.type = 'ORTHO'
cd.clip_start, cd.clip_end = 0.1, 800
cam = bpy.data.objects.new("cam_emb_walk", cd)
sc.collection.objects.link(cam)
# the classic 3/4: south-east and above, looking back into the valley
cam.location = ctr + Vector((46.0, -46.0, 52.0))
cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam

# THE FIT IS MEASURED, not guessed: project every walk corner through the camera's own
# axes and take the span that actually has to fit.  (town_export's heuristic fits the
# town's HEIGHT vertically, which is right for a canyon and wrong for a village.)
Mx = cam.matrix_world
right = (Mx.to_3x3() @ Vector((1, 0, 0))).normalized()
up = (Mx.to_3x3() @ Vector((0, 1, 0))).normalized()
hw = max(abs((p - ctr).dot(right)) for p in P)
hh = max(abs((p - ctr).dot(up)) for p in P)
ASPECT = 2688.0 / 1536.0
cd.ortho_scale = max(hw * 2, hh * 2 * ASPECT) * 1.10
print("ortho fit: half-span right %.1f up %.1f -> ortho_scale %.1f" % (hw, hh, cd.ortho_scale))

# ---- backdrop render ---------------------------------------------------------
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 2688, 1536
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.join(OUT, "background.png")
t = time.time()
with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.render.render(write_still=True)
print("background.png  %.1fs" % (time.time() - t))
shutil.copyfile(os.path.join(OUT, "background.png"), os.path.join(OUT, "stylized.png"))

if PREVIEW:
    print("PREVIEW ONLY — no GLB written")
    raise SystemExit(0)

# ---- strip render-only helpers before the GLB --------------------------------
# fog volumes / haze slabs / backdrop planes are Cycles-only atmosphere; in a runtime
# GLB they become giant opaque boxes.  Convention, town-wide: fx_* is render-only.
FX = re.compile(r"^(fx_|FOG|.*haze)", re.I)
stripped = 0
for o in list(bpy.data.objects):
    if o.type == 'MESH' and FX.match(o.name):
        bpy.data.objects.remove(o, do_unlink=True)
        stripped += 1

with contextlib.redirect_stdout(io.StringIO()):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "scene.glb"),
                              export_format='GLB',
                              # walk meshes under a detailed district are render-hidden
                              # (collision only): they MUST still export.
                              use_visible=False, use_renderable=False, use_selection=False,
                              export_yup=True, export_cameras=True, export_lights=False)

n = {p: sum(1 for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(p))
     for p in ("walk_", "bar_", "veg_", "water_", "lm_", "emb_")}
json.dump({"exported": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "source": "tools/blends/emberbrook-master.blend",
           "tool": "tools/emb_export.py",
           "counts": n,
           "note": "Emberbrook's whole-town REAL-TIME bundle (map walkSceneKey emb-walk). "
                   "The camera tools measure their regions against the walk_ meshes in "
                   "here, so a stale scene.glb makes every solved camera stale too."},
          open(os.path.join(OUT, "meta.json"), "w"), indent=1)
print("EXPORT OK -> %s" % OUT)
print("  " + "  ".join("%s%d" % (k, v) for k, v in n.items()) + "   fx stripped %d" % stripped)
