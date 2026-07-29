#!/bin/bash
# townwalk_live_refresh.sh — keep the playable townwalk bundle tracking the master.
# Runs from cron every 10 min: skips if the master hasn't changed, exports to a
# staging dir, then moves files into place atomically so a page load never sees
# a half-written GLB. Opens the master read-only (town_export.py never saves).
REPO=/Users/junshernchan/projects/multiplayer-rpg
MASTER=$REPO/tools/blends/dellhollow-master.blend
OUT=$REPO/public/assets/scenes/townwalk
STAGE=$OUT/.staging
STAMP=$OUT/.last_master_mtime
LOCK=/tmp/townwalk_refresh.lock

mkdir "$LOCK" 2>/dev/null || exit 0                     # a refresh is already running
trap 'rmdir "$LOCK"' EXIT

mt=$(stat -f %m "$MASTER")
[ -f "$STAMP" ] && [ "$(cat "$STAMP")" = "$mt" ] && exit 0   # master unchanged since last export

mkdir -p "$STAGE"
TOWNWALK_OUT="$STAGE" /Applications/Blender.app/Contents/MacOS/Blender -b "$MASTER" \
  -P "$REPO/tools/town_export.py" > /tmp/townwalk_refresh.log 2>&1 || exit 1

for f in background.png stylized.png scene.glb; do
  [ -s "$STAGE/$f" ] && mv -f "$STAGE/$f" "$OUT/$f"
done
printf '{"exported":"%s","master_mtime":%s}' "$(date '+%Y-%m-%d %H:%M')" "$mt" > "$OUT/meta.json"
echo "$mt" > "$STAMP"
