# Battle backdrop plates (v1)

Generated 2026-07-30 via tools/genart.mjs (Gemini gemini-2.5-flash-image, the
repo's own art pipeline — same as the character busts), one per encounter zone,
prompted as FF9-style pre-rendered battle backgrounds with an empty foreground
clearing for combatants, late-afternoon golden-hour light (matching the
ratified variant-C town look), style-referenced to our own renders:

- meadow.png  ref: docs/qa/overworld/valley_record_midvalley.png
- forest.png  ref: docs/qa/overworld/foliage_stand.png
- crag.png    ref: docs/qa/districts/golden_gate.png
- water.png   ref: docs/qa/districts/golden_waterfront.png

Resolved by convention in the battle screen: assets/battle/<zoneKey>.png,
gradient fallback when absent. Regenerate any plate with tools/genart.mjs +
the prompt patterns in git history (commit message of this file's commit).
