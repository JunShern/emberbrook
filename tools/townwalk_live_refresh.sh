#!/bin/bash
# townwalk_live_refresh.sh — keep the playable town views tracking the working blends.
# Runs from cron every 10 min. Per target: skip if the blend hasn't changed, export
# to a staging dir, move files into place atomically (a page load never sees a
# half-written GLB), stamp meta.json for the HUD freshness display.
# Targets: the LIVE master -> townwalk, and any district branch blends -> their own
# preview scene keys. Also regenerates the QA render gallery index (cheap).
REPO=/Users/junshernchan/projects/multiplayer-rpg
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender

refresh_one() {
  local BLEND=$1 OUT=$2 SPAWN=$3                     # SPAWN: optional [x,y,z] runtime coords
  local STAGE=$OUT/.staging STAMP=$OUT/.last_blend_mtime
  [ -f "$BLEND" ] || return 0                        # branch merged/deleted: nothing to do
  local mt; mt=$(stat -f %m "$BLEND")
  [ -f "$STAMP" ] && [ "$(cat "$STAMP")" = "$mt" ] && return 0
  mkdir -p "$STAGE"
  TOWNWALK_OUT="$STAGE" "$BLENDER" -b "$BLEND" -P "$REPO/tools/town_export.py" \
    > /tmp/townwalk_refresh.log 2>&1 || return 1
  for f in background.png stylized.png scene.glb; do
    [ -s "$STAGE/$f" ] && mv -f "$STAGE/$f" "$OUT/$f"
  done
  if [ -n "$SPAWN" ]; then
    printf '{"exported":"%s","blend_mtime":%s,"spawn":%s}' "$(date '+%Y-%m-%d %H:%M')" "$mt" "$SPAWN" > "$OUT/meta.json"
  else
    printf '{"exported":"%s","blend_mtime":%s}' "$(date '+%Y-%m-%d %H:%M')" "$mt" > "$OUT/meta.json"
  fi
  echo "$mt" > "$STAMP"
}

LOCK=/tmp/townwalk_refresh.lock
mkdir "$LOCK" 2>/dev/null || exit 0                  # a refresh is already running
trap 'rmdir "$LOCK"' EXIT

rc=0
refresh_one "$REPO/tools/blends/dellhollow-master.blend"             "$REPO/public/assets/scenes/townwalk"    || rc=1
# gate-branch preview spawns AT the Valley Gate (runtime coords) — the district
# under construction must be in view, not the unchanged town center
refresh_one "$REPO/tools/blends/dellhollow-master-gate-branch.blend" "$REPO/public/assets/scenes/gate-branch" "[26.0,19.3,-7.0]" || rc=1
python3 "$REPO/tools/make_qa_index.py" >/dev/null 2>&1
exit $rc
