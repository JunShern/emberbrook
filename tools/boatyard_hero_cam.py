# boatyard_hero_cam.py — recreate the accepted Boatyard v10 hero camera in the
# master (no cameras are saved in the blend; shot scripts build theirs
# transiently). Chain before depth_bake.py:
#   Blender -b tools/blends/dellhollow-master.blend -P tools/boatyard_hero_cam.py -P tools/depth_bake.py -- del-boatyard
# Params match waterfront_shots.py "continuity" == boatyard_render.py v10 grade.
import bpy, math
from mathutils import Vector

sc = bpy.context.scene
cd = bpy.data.cameras.new("cam_boatyard_hero")
cd.sensor_fit = 'VERTICAL'
cd.angle_y = math.radians(35)
cd.clip_start, cd.clip_end = 0.05, 1200
cam = bpy.data.objects.new("cam_boatyard_hero", cd)
sc.collection.objects.link(cam)
cam.location = Vector((37.6, 25.4, 8.5))
cam.rotation_euler = (Vector((14.4, 30.4, 3.4)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = -0.52
print("boatyard hero cam created")
