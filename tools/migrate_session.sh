#!/usr/bin/env bash
# migrate_session.sh — carry a Claude Code session from the legacy rpg-3d project
# directory to the multiplayer-rpg one, so `claude --resume` in the repo can pick it up.
#
#   RUN THIS AFTER QUITTING the old session, not during it: the transcript is appended
#   to live, so a copy taken mid-session is missing everything said after the copy.
#
# Usage:  bash tools/migrate_session.sh [SESSION_ID]
#         (default SESSION_ID is the 2026-07/08 Emberbrook build session)
#
# Claude Code keys sessions by a slugified cwd, which is why moving the session root
# needs this at all: the transcript, its subagent transcripts and its cached tool
# results all live under the OLD directory's key and are invisible from the new one.
set -euo pipefail

SESSION="${1:-0e1c40c3-51e1-4ef0-8908-896c9d91202e}"
SRC="$HOME/.claude/projects/-Users-junshernchan-projects-rpg-3d"
DST="$HOME/.claude/projects/-Users-junshernchan-projects-multiplayer-rpg"

[ -f "$SRC/$SESSION.jsonl" ] || { echo "no transcript: $SRC/$SESSION.jsonl"; exit 1; }
mkdir -p "$DST"

# rsync, not cp: it is restartable. Plain flags only — macOS ships rsync 2.6.9, which
# has no --info. The transcript is ~200 MB and the companion directory (subagent
# transcripts + cached tool results) ~1 GB.
echo "copying transcript ($(du -h "$SRC/$SESSION.jsonl" | cut -f1))..."
rsync -a "$SRC/$SESSION.jsonl" "$DST/$SESSION.jsonl"
if [ -d "$SRC/$SESSION" ]; then
  echo "copying companion dir ($(du -sh "$SRC/$SESSION" | cut -f1))..."
  rsync -a "$SRC/$SESSION/" "$DST/$SESSION/"
fi

# Verify by content, not by exit code (CLAUDE.md's own rule): line counts must match.
a=$(wc -l < "$SRC/$SESSION.jsonl" | tr -d ' ')
b=$(wc -l < "$DST/$SESSION.jsonl" | tr -d ' ')
echo "transcript lines: source=$a copy=$b"
if [ "$a" != "$b" ]; then
  echo
  echo "SHORT COPY — the source grew while rsync ran, which means THE SESSION IS STILL"
  echo "LIVE. Quit Claude Code first, then run this again; the copy would otherwise be"
  echo "missing whatever was said after it started. (Re-running is cheap: rsync only"
  echo "ships the delta.)"
  exit 1
fi
echo "OK. Now: cd $HOME/projects/multiplayer-rpg && claude --resume"
echo "(the original is left in place; delete it yourself once the resume is proven)"
