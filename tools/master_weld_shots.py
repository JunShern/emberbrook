"""master_weld_shots.py — QA renders for the Boatyard seam weld in the master.

  Blender -b tools/blends/dellhollow-master.blend -P tools/master_weld_shots.py

Writes docs/qa/districts/master-weld_*.png (1344x768, EEVEE, the master's own
sunset grade).  Volume/haze helpers stay in — they are part of the look — but the
cameras are placed inside the gorge, where the town is actually seen from.
"""
import bpy, os, math, contextlib, io, sys
from mathutils import Vector

OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/districts"
os.makedirs(OUT, exist_ok=True)

SHOTS = {
    # the hand-over: detailed yard decking -> blockout ribbon east to the fish dock
    "seam-east": dict(pos=(41.2, 30.6, 6.6), aim=(34.0, 24.6, 1.7), fov=44),
    # the same seam from the land side: bank, kerbs, gate posts, handline
    "seam-gate": dict(pos=(30.0, 20.6, 6.2), aim=(37.0, 26.0, 2.0), fov=46),
    # detailed ground -> blockout cliff/stairs: the new bank under the deep stairs
    "seam-bank": dict(pos=(45.0, 31.0, 13.0), aim=(35.5, 21.5, 5.0), fov=46),
    # does the walk route read as the path?
    "yard-path": dict(pos=(34.0, 36.0, 13.5), aim=(18.0, 26.0, 2.5), fov=52),
    # the whole gorge from high above the south rim (the export camera's own 3/4
    # direction, but steep enough to clear the 37 m south cliff)
    "overview": dict(pos=(104.0, -22.0, 132.0), aim=(48.0, 19.0, 7.0), fov=46),
    # the district in its neighbourhood
    "district": dict(pos=(62.0, -10.0, 58.0), aim=(22.0, 25.0, 4.0), fov=48),
}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = argv[0].split(",") if argv else None

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1344, 768
try:
    sc.eevee.taa_render_samples = 64
except Exception:
    pass


def town_ortho_cam():
    xs, ys, zs = [], [], []
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith("walk_"):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                xs.append(w.x); ys.append(w.y); zs.append(w.z)
    cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    span = max(max(xs) - min(xs), (max(zs) - min(zs)) * 1.75) * 1.08
    cd = bpy.data.cameras.new("cam_ov"); cd.type = 'ORTHO'
    cd.ortho_scale = span; cd.clip_end = 500
    cam = bpy.data.objects.new("cam_ov", cd)
    sc.collection.objects.link(cam)
    cam.location = (cx + 60, cy - 55, cz + 62)
    cam.rotation_euler = (Vector((cx, cy, cz)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    return cam


for name, s in SHOTS.items():
    if WHICH and name not in WHICH:
        continue
    if s.get("ortho"):
        cam = town_ortho_cam()
    else:
        cd = bpy.data.cameras.new("cam_" + name)
        cd.sensor_fit = 'HORIZONTAL'
        cd.angle_x = math.radians(s["fov"])
        cd.clip_start, cd.clip_end = 0.05, 900
        cam = bpy.data.objects.new("cam_" + name, cd)
        sc.collection.objects.link(cam)
        cam.location = Vector(s["pos"])
        cam.rotation_euler = (Vector(s["aim"]) - Vector(s["pos"])).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    fp = os.path.join(OUT, "master-weld_%s.png" % name)
    sc.render.filepath = fp
    with contextlib.redirect_stdout(io.StringIO()):
        bpy.ops.render.render(write_still=True)
    print("RENDERED", fp)
