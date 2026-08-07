#!/usr/bin/env bash
# deploy-ghpages.sh — publish a built dist to GitHub Pages.
#
#   bash tools/deploy-ghpages.sh dist-c
#
# WHAT IT DOES. Makes the dist its OWN throwaway git repo, single commit, and
# force-pushes that to the `gh-pages` branch. The parent repo is never touched —
# no orphan branch checkout, no stashing, no risk of sweeping another lane's
# uncommitted work into a deploy. Each deploy REPLACES the branch rather than
# stacking on it, so the branch never grows a history of 250 MB snapshots.
#
# WHY NOT A GITHUB ACTION. The build needs Pillow, npx gltf-transform and ~40
# minutes; running it in CI on every push would be slow and would re-do work that
# is already deterministic locally. Build here, publish the artifact.
#
# THE PRE-FLIGHT CHECKS ARE THE POINT. A deploy that half-works is worse than one
# that refuses: a missing texture 404s at the exact moment a player walks into a
# room, and no unit gate in this repo can see it.
set -euo pipefail

DIST="${1:-dist-c}"
REMOTE="$(git -C . remote get-url origin)"
BRANCH="gh-pages"

[ -d "$DIST" ] || { echo "FAIL: no such build dir: $DIST"; exit 1; }

# 1. Does this even look like a build? Three files the game cannot run without.
for f in index.html play.html BUILD.json; do
  [ -f "$DIST/$f" ] || { echo "FAIL: $DIST/$f missing — that is not a finished build"; exit 1; }
done

# 2. GitHub REFUSES any file over 100 MB, and the push fails late and loudly
#    after uploading everything before it. Catch it here instead.
BIG=$(find "$DIST" -type f -size +99M | head -5)
[ -z "$BIG" ] || { echo "FAIL: files over GitHub's 100 MB hard limit:"; echo "$BIG"; exit 1; }

# 3. Pages soft-caps a published site at ~1 GB. Warn, don't block — the cap is
#    soft and the honest thing is to say the number, not to guess GitHub's mood.
BYTES=$(du -sk "$DIST" | cut -f1)
MB=$((BYTES / 1024))
echo "  build: ${MB} MB, $(find "$DIST" -type f | wc -l | tr -d ' ') files"
[ "$MB" -lt 1000 ] || echo "  ! over GitHub Pages' ~1 GB soft cap — it may still work, but this is the number to watch"

# 4. Jekyll would otherwise EAT every directory beginning with an underscore and
#    try to parse the HTML. .nojekyll is one empty file and saves a confusing hour.
touch "$DIST/.nojekyll"

echo "  publishing to $BRANCH on $REMOTE …"
(
  cd "$DIST"
  rm -rf .git
  git init -q
  git checkout -q -b "$BRANCH"
  git add -A
  git -c user.email=deploy@local -c user.name=deploy commit -q -m "deploy $(date -u +%Y-%m-%dT%H:%MZ)"
  # --force: each deploy REPLACES the branch. The old snapshot's blobs become
  # unreachable and get collected; the branch never accumulates 250 MB per push.
  git push -q --force "$REMOTE" "$BRANCH:$BRANCH"
)

# 5. VERIFY THE PUSH, never trust the exit code — this repo has been burned by a
#    3.3 GB push that died on GitHub's pack limit while reporting success.
REMOTE_SHA=$(git ls-remote --heads "$REMOTE" "$BRANCH" | cut -f1)
LOCAL_SHA=$(git -C "$DIST" rev-parse HEAD)
[ "$REMOTE_SHA" = "$LOCAL_SHA" ] || { echo "FAIL: push did not land ($REMOTE_SHA != $LOCAL_SHA)"; exit 1; }
echo "  push verified: $LOCAL_SHA"

# 6. Turn Pages on if it is not already. 409 = already configured, which is fine.
gh api -X POST repos/:owner/:repo/pages \
  -f "source[branch]=$BRANCH" -f "source[path]=/" >/dev/null 2>&1 \
  && echo "  Pages enabled on $BRANCH" \
  || echo "  Pages already configured (or needs enabling by hand in Settings > Pages)"

echo
gh api repos/:owner/:repo/pages --jq '"  LIVE AT: " + .html_url' 2>/dev/null \
  || echo "  URL will appear at Settings > Pages once the first build finishes"
echo "  (first publish takes a few minutes to go live)"

# TRIGGER THE PAGES BUILD EXPLICITLY (2026-08-07). Twice measured: a force-push to
# gh-pages did NOT auto-trigger the Pages build — the site sat on the previous
# build for 30+ min both times until a manual POST queued one. The API call is
# idempotent-safe (a queued/running build just continues).
gh api -X POST repos/:owner/:repo/pages/builds --jq '"  Pages build: " + .status' 2>/dev/null \
  || echo "  (could not queue a Pages build via API — it may still auto-build)"
