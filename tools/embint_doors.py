#!/usr/bin/env python3
"""embint_doors.py — write the DOORS NOTE for each Emberbrook interior bundle.

    python3 tools/embint_doors.py            # all built interiors
    python3 tools/embint_doors.py emb-inn-int

Writes public/assets/scenes/<sceneKey>/doors.json.

WHY THIS FILE EXISTS.  Wiring an interior into the town is `tools/
scenegraph_derive.mjs`'s job and it is fully automatic — it reads the map
landmark's `interiorSceneKey`, finds `walk_pad_<landmark>` in the town bundle
and `walk_pad_door` in the interior bundle, and emits the reciprocal door
edges.  It needs NOTHING from this file.

What this file is for is the human at the desk doing the wiring: it states, in
one place, where the door of each room actually is, which way a player faces
when they arrive on it, which map landmark it belongs to, and — the one thing
the derive cannot check — WHICH SIDE OF THE BUILDING the door is on in the
town, so the interior's door and the exterior's door pad end up on the same
wall of the same house.  A room whose door faces the square while its
exterior's door faces the lane is a defect no test in the repo can see.

COORDINATE FRAMES, stated because they have cost this project time before:
  blender   (x, y, z)          how the room is authored
  runtime   (x, z, -y)         what scenegraph.json and play3d.html use
            (the glTF y-up export; identical to `depth_bake.py`'s spawn maths
             and to scenegraph_derive's `T()` for town maps)
"""
import json, os, sys, importlib.util, math

ROOT = "/Users/junshernchan/projects/multiplayer-rpg"
TOOLS = os.path.join(ROOT, "tools")

ROOMS = [
    ("emb-inn-int", "embint_inn_build"),
    ("emb-bakery-int", "embint_bakery_build"),
    ("emb-lake-int", "embint_lake_build"),
    ("emb-item-int", "embint_item_build"),
]


def load(name):
    path = os.path.join(TOOLS, name + ".py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)          # imports bpy -> only works in Blender
    except Exception:
        return None
    return m


def emit(key, spec):
    out = os.path.join(ROOT, "public/assets/scenes", key)
    if not os.path.isdir(out):
        print("  skip %s (no bundle yet)" % key)
        return
    p = spec["padBlender"]
    o = spec["openingBlender"]
    f = spec["facing"]
    doc = {
        "_doc": ("The interior side of this room's door, for the coordinator "
                 "wiring it to the town.  tools/scenegraph_derive.mjs needs "
                 "nothing from this file — it reads walk_pad_door out of "
                 "scene.glb by name.  This is the human-readable statement of "
                 "the same fact, plus the one thing the derive cannot check: "
                 "which wall of the real building the door is in."),
        "sceneKey": key,
        "townMap": "public/townmap/emberbrook.map.json",
        "landmark": spec["landmark"],
        "interiorSceneKeyAlreadyInMap": True,
        "padName": "walk_pad_door",
        "frames": {
            "blender": "authoring frame, metres, +z up",
            "runtime": "(x, z, -y) — the glTF y-up export play3d.html reads",
        },
        "spawn": {
            "blender": [round(v, 3) for v in p],
            "runtime": [round(p[0], 3), round(p[2], 3), round(-p[1], 3)],
        },
        "opening": {
            "blender": [round(v, 3) for v in o],
            "runtime": [round(o[0], 3), round(o[2], 3), round(-o[1], 3)],
            "widthM": spec["widthM"],
            "headM": spec["headM"],
        },
        "facingIntoRoom": {
            "blenderXY": [round(f[0], 3), round(f[1], 3)],
            "runtimeXZ": [round(f[0], 3), round(-f[1], 3)],
            "yawDegBlender": round(math.degrees(math.atan2(f[1], f[0])), 1),
            "note": ("the direction a player is looking the moment they arrive "
                     "on walk_pad_door — set spawnYaw from this if the runtime "
                     "ever stops leaving it null"),
        },
        "townSide": spec["townSide"],
        "otherPads": spec["otherPads"],
    }
    with open(os.path.join(out, "doors.json"), "w") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")
    print("  wrote %s/doors.json" % key)


# The specs are stated here rather than scraped, because every number is a
# decision the room's own script already documents and a scraper would only
# re-derive them less legibly.
SPECS = {
    "emb-inn-int": dict(
        landmark="inn",
        padBlender=(7.20, 5.52, 0.02),
        openingBlender=(7.60, 6.30, 0.00),
        facing=(-0.20, -0.98),
        widthM=1.20, headM=2.20,
        townSide=("The inn stands at map (27, 18) and the square-plaza at "
                  "(32, 22): the door is on the building's NORTH-EAST face, "
                  "onto the square. In the interior's own frame that is the "
                  "back wall, +y. Put walk_pad_inn on the square side of the "
                  "exterior and the two agree."),
        otherPads=["walk_pad_counter (reception)", "walk_pad_hearth (the inglenook)",
                   "walk_pad_snug (the second room)"],
    ),
    "emb-bakery-int": dict(
        landmark="bakery",
        padBlender=(0.72, 4.65, 0.02),
        openingBlender=(0.00, 4.65, 0.00),
        facing=(1.0, 0.0),
        widthM=1.20, headM=2.15,
        townSide=("The bakery is at map (24.5, 21.5), square-plaza at (32, 22): "
                  "its face is EAST, onto the square, and the map's own note is "
                  "'warm window on the square'. In the interior's frame the "
                  "square is -x: the door AND the serving window are both in "
                  "that wall, the window south of the door."),
        otherPads=["walk_pad_counter (the serving window)",
                   "walk_pad_oven (up two steps, on the bakehouse platform)",
                   "walk_pad_bench (the work bench)"],
    ),
    "emb-lake-int": dict(
        landmark="lake-home",
        padBlender=(6.05, 4.42, 0.02),
        openingBlender=(6.55, 4.95, 0.00),
        facing=(-0.707, -0.707),
        widthM=1.20, headM=2.05,
        townSide=("Lake's cottage is at map (17, 24) on Home Row, with the lane "
                  "running east to hillside-cottage (22, 27) and the square "
                  "beyond. The door is on the SOUTH-EAST corner, onto the lane, "
                  "and the lamppost outside it is the nearest lamp on his own "
                  "round. In the interior's frame that is the CANTED corner "
                  "wall — the door is at 45 degrees, so the exterior's door pad "
                  "wants to be on the corner too, not flat on either face."),
        otherPads=["walk_pad_hearth (the mantel, the hook, the portrait)",
                   "walk_pad_table (grandmother's table)",
                   "walk_pad_bed (her alcove under the loft)"],
    ),
    "emb-item-int": dict(
        landmark="item-shop",
        padBlender=(0.0, 0.0, 0.0),
        openingBlender=(0.0, 0.0, 0.0),
        facing=(0.0, -1.0),
        widthM=1.20, headM=2.15,
        townSide="NOT BUILT YET — placeholder row.",
        otherPads=[],
    ),
}


def main():
    want = sys.argv[1:] or [k for k, _ in ROOMS]
    for key, _mod in ROOMS:
        if key not in want:
            continue
        if key not in SPECS:
            continue
        emit(key, SPECS[key])


if __name__ == "__main__":
    main()
