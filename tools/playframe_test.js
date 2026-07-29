// PLAYER-FRAME SMOKE TEST — paste into the play3d console (or drive via CDP).
// The lesson of 2026-07-29 morning: numeric walk tests + character-less art renders
// each passed while the PLAYER'S FRAME was broken (invisible char, wrong scale,
// ghost-through-furniture). This tests what the player actually experiences:
//   1. visibility: pixel-diff of the frame with the character shown vs hidden (>400 px)
//   2. scale: the diff bounding-box height as % of frame (target ~15-30%)
//   3. blocking: approach every bar_auto blocker from 4 sides (skipping invalid
//      starts); the walker must never END inside a blocker footprint.
// Run AFTER teleporting to a representative open spot (spawn is door pad by default).
// See docs/qa/NIGHTLOG.md 2026-07-29 for the incident writeup.
