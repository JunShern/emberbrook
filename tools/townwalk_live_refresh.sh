#!/bin/bash
# townwalk_live_refresh.sh — keep the playable town views tracking the working blends.
# Runs from cron every 10 min. Per target: skip if the blend hasn't changed, export
# to a staging dir, move files into place atomically (a page load never sees a
# half-written GLB), stamp meta.json for the HUD freshness display.
# Targets: the LIVE master -> townwalk. A district BRANCH blend gets its own preview
# scene key for as long as the branch is live; the west branch (gate + shelf tiers) was
# merged into the master and retired 2026-07-30, so there is no branch target now.
# Also regenerates the QA render gallery index (cheap).
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
# SPAWN IS A MAP COORDINATE AND THE MAP MOVED — and the plaza CENTRE is the
# Heartlight's plinth (user spawned inside it, stuck). Spawn on the approach road at
# the plaza's south edge instead. Runtime coords are (x, z_up, -y).
refresh_one "$REPO/tools/blends/emberbrook-master.blend"             "$REPO/public/assets/scenes/emb-townwalk" "[62,1.5,-32]" || rc=1
# A live branch adds one line here, with a SPAWN in runtime coords so the district under
# construction is in view rather than the unchanged town center — e.g. the retired west
# branch used "[26.0,19.3,-7.0]" (the Valley Gate) into public/assets/scenes/gate-branch.

# world-map fast loop: when armed (tools/.fastloop exists, created once the v2
# pipeline landed), rebuild ow-valley whenever the map JSONs change — so the
# world behaves like the town: edit lands, world refreshes itself.
WSTAMP=$REPO/public/assets/scenes/ow-valley/.last_map_mtime
if [ -f "$REPO/tools/.fastloop" ] && [ -x "$REPO/tools/valley_rebuild.sh" ]; then
  wmt=$(stat -f %m "$REPO/public/world/world.json" "$REPO/public/world/regions/valley.region.json" | sort -rn | head -1)
  if [ ! -f "$WSTAMP" ] || [ "$(cat "$WSTAMP")" != "$wmt" ]; then
    node "$REPO/tools/worldmap_validate.mjs" > /tmp/valley_rebuild.log 2>&1 \
      && bash "$REPO/tools/valley_rebuild.sh" >> /tmp/valley_rebuild.log 2>&1 \
      && echo "$wmt" > "$WSTAMP" || rc=1
  fi
fi
python3 "$REPO/tools/make_qa_index.py" >/dev/null 2>&1
exit $rc
