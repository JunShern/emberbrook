#!/bin/bash
# valley_rebuild.sh — THE fast-loop command: map files -> playable ow-valley.
#   1. validate the geography hierarchy (refuses to build a broken map)
#   2. layout preview (pure numpy, seconds — the taste-gate image)
#   3. build the region blend (Blender headless, deterministic)
#   4. export the bundle (background/stylized/scene.glb/meta.json + zones.json)
#   5. verify (glTF round trip, white-material gate, spawn, ribbons, zones)
# Called by hand or by the live-refresh tick when the map JSONs change
# (tools/.fastloop arms the tick path).
set -e
REPO=/Users/junshernchan/projects/multiplayer-rpg
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
cd "$REPO"
node tools/worldmap_validate.mjs
python3 tools/valley_layout.py
"$BLENDER" --python-exit-code 1 -b --factory-startup -P tools/valley_build.py
"$BLENDER" --python-exit-code 1 -b tools/blends/overworld-valley.blend -P tools/valley_render.py -- overview
"$BLENDER" --python-exit-code 1 -b tools/blends/overworld-valley.blend -P tools/valley_export.py
"$BLENDER" --python-exit-code 1 -b --factory-startup -P tools/valley_verify.py
python3 tools/make_qa_index.py >/dev/null
echo "VALLEY REBUILD OK $(date '+%H:%M')"
