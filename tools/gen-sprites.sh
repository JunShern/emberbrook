#!/bin/bash
# Character sprites — chibi cel JRPG style matching June's sheet
cd "$(dirname "$0")/.."
GRID4="The image is EXACTLY a 4 by 4 grid of equal-size cells on a completely flat uniform bright magenta background (#FF00FF), no gradients, no background shadows. Row 1: 4-frame walk cycle facing the viewer (front view) with legs clearly in different positions each frame. Row 2: the same cycle from behind (back view). Row 3: the same cycle in left side profile with clear strides. Row 4: right side profile. Character centered in every cell, identical size, feet on a consistent baseline. No grid lines, no text, no labels."
GRID2="The image is EXACTLY a 2 by 2 grid of equal-size cells on a completely flat uniform bright magenta background (#FF00FF), no gradients, no background shadows. Top-left: standing idle facing the viewer. Top-right: standing idle seen from behind. Bottom-left: standing idle in left side profile. Bottom-right: standing idle in right side profile. Character centered in every cell, identical size, feet on a consistent baseline. No grid lines, no text, no labels."
STYLE="Art style: crisp cel-shaded anime JRPG field sprite with clean outlines, SLIGHTLY chibi proportions about 3 heads tall — cute but elegant, matching the style of the reference sprite sheet."

node tools/genart.mjs public/assets/sprite-cole.png --ref public/assets/busts/cole.png --ref public/assets/sprite-june-chibi.png "Create a video game character sprite sheet of the exact character from the FIRST reference image (young man, soft tousled black-indigo hair, deep indigo wool coat with brass buttons, mustard-amber knit scarf, dark trousers, brown boots). $STYLE $GRID4"

node tools/genart.mjs public/assets/sprite-rowan.png --ref public/assets/sprite-june-chibi.png "Create a video game character sprite sheet: an elderly village elder with long grey hair, heavy brows and a long grey beard, wearing a dusty violet robe with gold trim, holding a wooden staff topped with a small amber stone. $STYLE $GRID2"

node tools/genart.mjs public/assets/sprite-poppy.png --ref public/assets/sprite-june-chibi.png "Create a video game character sprite sheet: a warm middle-aged baker woman with a round friendly build, rosy cheeks, auburn hair under a cream puff baker's hat, terracotta dress with a cream apron dusted with flour. $STYLE $GRID2"

node tools/genart.mjs public/assets/sprite-finn.png --ref public/assets/sprite-june-chibi.png "Create a video game character sprite sheet: a weathered middle-aged fisherman with stubble, an olive bucket hat, a sea-blue coat, tan waders and boots. $STYLE $GRID2"

node tools/genart.mjs public/assets/sprite-pip.png --ref public/assets/sprite-june-chibi.png "Create a video game character sprite sheet: a small seven-year-old boy with messy straw-blond hair, a simple green smock over brown trousers, small boots, bright-eyed and eager. He is HALF the height of an adult. $STYLE $GRID2"

node tools/genart.mjs public/assets/sprite-mara.png --ref public/assets/sprite-june-chibi.png "Create a video game character sprite sheet: a gentle young mother with dark hair in a soft bun, a plum shawl over a rose dress, tired kind eyes. $STYLE $GRID2"

node tools/genart.mjs public/assets/sprite-mochi.png --ref public/assets/sprite-june-chibi.png "Create a video game sprite sheet of a small orange tabby cat with darker orange stripes and green eyes. $STYLE The image is EXACTLY a 2 by 2 grid of equal-size cells on flat uniform bright magenta (#FF00FF). Top-left: cat sitting facing the viewer. Top-right: cat sitting seen from behind. Bottom-left: cat standing in left side profile mid-step. Bottom-right: cat curled in a loaf position. Centered, consistent size, no grid lines, no text."

node tools/genart.mjs public/assets/sprite-stranger.png --ref public/assets/sprite-june-chibi.png "Create a video game character sprite sheet: a tall figure in a hooded grey-black cloak, face completely hidden in darkness except two faint pale glints, holding an old iron lantern that glows with trapped pale bluish light. Slightly taller and thinner than a normal villager. $STYLE $GRID2"

echo "=== sprites done ==="
