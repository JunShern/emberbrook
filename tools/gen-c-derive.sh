#!/bin/bash
# Candidate C derivation: occupancy mask + walk-behind prop isolations
cd "$(dirname "$0")/.."
C=public/assets/sq-full-c.png

node tools/genart.mjs public/assets/sq-c-mask.png --ref $C --ar 16:9 "Repaint this exact scene with ONE change: fill every area of open walkable ground with FLAT PURE NEON GREEN (#00FF00) — the cobblestone plaza, ALL the dirt roads continuing to the very edges of the image, and the open grass areas. The green is completely solid and uniform, no texture, no shading, no lighting. Everything that is NOT open walkable ground stays exactly as it is, drawn on top of the green: all buildings, all market stalls, the stone pedestal and crystal, all lamp posts, hay bales, the hand cart, the notice board, barrels, crates, pumpkins, firewood, trees, bushes and forest. The green must reach exactly to the base of every object. No text, no watermark."

ISO="reproduce it EXACTLY as it appears in the scene — same angle, same dusk lighting, same colors, same details — alone on a completely flat uniform bright magenta background (#FF00FF). Nothing else from the scene, no ground beneath it, no cast shadow on the ground, no text, no watermark."

node tools/genart.mjs public/assets/c-prop-pedestal.png --ref $C "From this scene, isolate ONLY the central stone pedestal together with its glowing amber crystal and flame: $ISO"
node tools/genart.mjs public/assets/c-prop-stall-baker.png --ref $C "From this scene, isolate ONLY the market stall with the RED-AND-WHITE STRIPED awning on the left side (the baker's stall with pies and buns): $ISO"
node tools/genart.mjs public/assets/c-prop-stall-sausage.png --ref $C "From this scene, isolate ONLY the market stall at the top-center with the GREEN scalloped awning and hanging sausages: $ISO"
node tools/genart.mjs public/assets/c-prop-stall-right.png --ref $C "From this scene, isolate ONLY the market stall on the right side with the GREEN awning full of baked goods: $ISO"
node tools/genart.mjs public/assets/c-prop-stall-bgreen.png --ref $C "From this scene, isolate ONLY the market stall at the bottom-left with the GREEN awning: $ISO"
node tools/genart.mjs public/assets/c-prop-stall-blue.png --ref $C "From this scene, isolate ONLY the market stall at the bottom with the DEEP BLUE awning: $ISO"
node tools/genart.mjs public/assets/c-prop-lamp.png --ref $C "From this scene, isolate ONLY one of the single-headed wrought-iron lamp posts with its glowing lantern: $ISO"
node tools/genart.mjs public/assets/c-prop-lamp2.png --ref $C "From this scene, isolate ONLY the double-headed wrought-iron lamp post on the right side with both lanterns glowing: $ISO"
node tools/genart.mjs public/assets/c-prop-hay.png --ref $C "From this scene, isolate ONLY one pair of stacked hay bales: $ISO"
node tools/genart.mjs public/assets/c-prop-cart.png --ref $C "From this scene, isolate ONLY the wooden hand cart with the barrels of ice on the right side: $ISO"
node tools/genart.mjs public/assets/c-prop-board.png --ref $C "From this scene, isolate ONLY the wooden notice board with its posts and pinned papers near the left road: $ISO"

echo "=== C derivation done ==="
