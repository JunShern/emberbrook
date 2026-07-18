#!/bin/bash
# Square pilot: mask + prop library, all style-anchored to the generated stage
cd "$(dirname "$0")/.."

node tools/genart.mjs public/assets/sq-mask-raw.png --ref public/assets/sq-stage.png --ar 16:9 "Repaint this exact scene with ONE change: fill every area of open walkable ground — the cobblestone plaza, the dirt roads, the open grass fringes — with FLAT PURE NEON GREEN (#00FF00), a completely solid uniform green with no texture, no shading and no lighting on it. Leave everything that is NOT walkable ground completely unchanged: all trees, trunks, bushes and forest stay exactly as they are, drawn on top of the green where they overlap. The green must reach exactly to the base of every tree and bush. No text, no watermark."

P="A single isolated game object for a story-driven JRPG, drawn on a completely flat uniform bright magenta background (#FF00FF). No ground plane, no cast shadow on the ground, no other objects, no characters, no text, no watermark. 3/4 top-down oblique view matching the reference scene's camera angle. Art style: exactly the reference image — premium anime film background style, warm dusk palette, cel-shaded painted textures, soft warm rim light."

node tools/genart.mjs public/assets/prop-bakery.png --ref public/assets/sq-stage.png "$P Object: a cozy village bakery — two stories, warm cream plaster walls with dark timber framing, a RED clay tiled roof with a brick chimney, warmly lit windows with wooden shutters and flower boxes, an arched wooden door with a small hanging bread-sign, stone foundation."

node tools/genart.mjs public/assets/prop-hall.png --ref public/assets/sq-stage.png "$P Object: the village elder's hall — a large dignified timber-framed hall with a steep dark SLATE roof, tall arched double door, stone steps, warmly lit leaded windows, a small bell over the gable."

node tools/genart.mjs public/assets/prop-cottage.png --ref public/assets/sq-stage.png "$P Object: a small humble cottage with a thick golden THATCHED roof, rough stone walls, one warmly lit window, a plain wooden door, a stubby chimney."

node tools/genart.mjs public/assets/prop-stall.png --ref public/assets/sq-stage.png "$P Object: a wooden market stall with a red-and-white striped canvas awning, its counter stacked with golden honeybuns and pastries on wooden trays, a small barrel beside the leg."

node tools/genart.mjs public/assets/prop-pedestal.png --ref public/assets/sq-stage.png "$P Object: an ancient carved stone pedestal, waist-high, octagonal, with faint rune engravings — and hovering just above it a large glowing AMBER CRYSTAL radiating warm firelight, small embers drifting off it."

node tools/genart.mjs public/assets/prop-lamp.png --ref public/assets/sq-stage.png "$P Object: a tall wrought-iron street lamp post with an ornate four-paned glass lantern head, currently UNLIT (dark glass), a small crossbar, elegant Victorian curves."

node tools/genart.mjs public/assets/prop-board.png --ref public/assets/sq-stage.png "$P Object: a village notice board — two wooden posts holding a roofed board pinned with weathered paper notices, one nailed askew."

node tools/genart.mjs public/assets/prop-crates.png --ref public/assets/sq-stage.png "$P Object: a small cluster of two wooden crates and one round oak barrel, stacked casually together, with a folded burlap sack on top."

echo "=== square props done ==="
