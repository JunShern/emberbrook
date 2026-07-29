# town_shots.py — render every parcel's draft camera from the town blockout,
# in BOTH projections, for the morning shot-review board.
# Run: /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-town.blend -P tools/town_shots.py
# Output: docs/qa/shots/dellhollow/<sceneKey>_{ortho,persp}.png (1344x768)
#
# Camera convention (mirrors viewer.html deriveParcelCamera):
#   yaw = compass direction the camera SITS at relative to the aim point
#         (0 = downstream/+x, 90 = over the river/+y), looking back at it.
#   pitch = elevation of the camera position above the aim point.
#   viewHeight = world units visible vertically across the full frame (intimacy).
#   Aim point = centroid of member landmarks (bounds center when memberless).

import bpy, json, math, os, contextlib, io
from mathutils import Vector

TOWN_JSON = "/Users/junshernchan/projects/multiplayer-rpg/public/townmap/dellhollow.map.json"
OUT = "/Users/junshernchan/projects/multiplayer-rpg/docs/qa/shots/dellhollow"
FOV_V = 35.0          # persp vertical fov, degrees
ASPECT = 1344 / 768
os.makedirs(OUT, exist_ok=True)

D = json.load(open(TOWN_JSON))
LM = {l["id"]: Vector(l["pos"]) for l in D["landmarks"]}

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1344
sc.render.resolution_y = 768

for p in D["parcels"]:
    cam_spec = p.get("camera", {})
    yaw = math.radians(cam_spec.get("yaw", -45))
    pitch = math.radians(cam_spec.get("pitch", 28.9))
    vh = cam_spec.get("viewHeight", 12)
    members = [LM[m] for m in p.get("members", []) if m in LM]
    if members:
        aim = sum(members, Vector()) / len(members) + Vector((0, 0, 1.0))
    else:
        mn, mx = p["bounds"]["min"], p["bounds"]["max"]
        aim = Vector(((mn[0]+mx[0])/2, (mn[1]+mx[1])/2, (mn[2]+mx[2])/2))
    d = Vector((math.cos(pitch)*math.cos(yaw), math.cos(pitch)*math.sin(yaw), math.sin(pitch)))

    for proj in ("ortho", "persp"):
        name = "shot_%s_%s" % (p["id"], proj)
        cd = bpy.data.cameras.new(name)
        if proj == "ortho":
            cd.type = 'ORTHO'
            cd.ortho_scale = vh * ASPECT      # blender ortho_scale = horizontal extent
            dist = 90.0                        # far back; ortho size is what matters
        else:
            cd.type = 'PERSP'
            cd.angle_y = math.radians(FOV_V)
            cd.sensor_fit = 'VERTICAL'
            dist = (vh / 2) / math.tan(math.radians(FOV_V) / 2)
        cd.clip_end = 600
        cam = bpy.data.objects.new(name, cd)
        sc.collection.objects.link(cam)
        cam.location = aim + d * dist
        cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.camera = cam
        sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (p["sceneKey"], proj))
        with contextlib.redirect_stdout(io.StringIO()):
            bpy.ops.render.render(write_still=True)
        print("SHOT", p["sceneKey"], proj)

print("ALL SHOTS DONE ->", OUT)
