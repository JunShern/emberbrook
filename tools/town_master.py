# town_master.py — DEPRECATED (2026-07-29, one-time use only).
# ARCHITECTURE CANON: the town is ONE model. tools/blends/dellhollow-master.blend is the
# source of truth for FORM; public/townmap/dellhollow.map.json is the source of truth for
# TOPOLOGY (walk_/bar_ meshes + placeholders). Agents detail districts IN THE MASTER,
# serially — never in copies, never composited. This script ran exactly once to amnesty
# the Boatyard (which was built as a copy before the canon was set). Do not run it again:
# it would clobber in-master detail.
# Run: /Applications/Blender.app/Contents/MacOS/Blender -b tools/blends/dellhollow-town.blend -P tools/town_master.py
# Output: tools/blends/dellhollow-master.blend (blockout everywhere, detail where districts exist)
#
# Per district in DISTRICTS: append its objects (minus duplicates of canonical
# collision/context), then delete the blockout massing it replaces in its region.
# Walk_/bar_ meshes ALWAYS come from the blockout — collision stays canonical.

import bpy, os
from mathutils import Vector

BLENDS = "/Users/junshernchan/projects/multiplayer-rpg/tools/blends"
OUT = os.path.join(BLENDS, "dellhollow-master.blend")

DISTRICTS = [
    {"file": os.path.join(BLENDS, "districts", "boatyard.blend"),
     "name": "boatyard",
     "region": (2, 32, 19, 33),        # x0, x1, y0, y1
     # blockout prefixes to remove in-region (replaced by district detail):
     "replaces": ("lm_", "walk_pad_", "dam_dam-four", "e_", "walk_e_", "walk_lm_", "bar_")},
]
# NOTE: we keep the blockout's walk_*/bar_* (canonical collision) and DELETE the
# district's copies below; but visual blockout massing (lm_*) in-region goes.

def in_region(o, r):
    x, y = o.matrix_world.translation.x, o.matrix_world.translation.y
    return r[0] <= x <= r[1] and r[2] <= y <= r[3]

for d in DISTRICTS:
    if not os.path.exists(d["file"]):
        print("SKIP missing district", d["file"]); continue

    # 1. remove blockout VISUAL massing in-region (keep canonical walk_/bar_)
    removed = 0
    bpy.context.view_layer.update()
    for o in list(bpy.data.objects):
        if o.type != 'MESH' or not in_region(o, d["region"]):
            continue
        n = o.name
        if n.startswith(("walk_", "bar_")):
            continue                                 # canonical collision stays
        if n.startswith(("lm_", "dam_dam-four")):
            bpy.data.objects.remove(o, do_unlink=True); removed += 1

    # 2. append the district's objects, skipping its walk_/bar_ duplicates,
    #    context copies (cliff/water), and cameras
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(d["file"]) as (src, dst):
        keep = [n for n in src.objects
                if not n.startswith(("walk_", "bar_", "cliff_", "water_", "cam_", "CAM"))]
        dst.objects = keep
    coll = bpy.data.collections.new("DIST_" + d["name"])
    bpy.context.scene.collection.children.link(coll)
    added = 0
    for o in bpy.data.objects:
        if o in before or o.name.startswith(("cam", "CAM")):
            continue
        if o.users_collection:
            for c in o.users_collection: c.objects.unlink(o)
        try:
            coll.objects.link(o); added += 1
        except Exception:
            pass
    print("district %s: removed %d blockout, added %d detail" % (d["name"], removed, added))

bpy.ops.wm.save_as_mainfile(filepath=OUT)
n_walk = sum(1 for o in bpy.data.objects if o.name.startswith("walk_"))
print("MASTER OK — objects:", len(bpy.data.objects), "| walk:", n_walk, "| saved", OUT)
