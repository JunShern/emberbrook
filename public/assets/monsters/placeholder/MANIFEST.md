# Foe icons — DERIVED, not drawn

**Every PNG in this directory is generated. Do not hand-edit one; regenerate it.**

```
node tools/monster_icons.mjs --port 3000       # rewrite all six
python3 tools/monster_regrade.py --icons       # prove they agree with the models
```

Each file is a 256×256 alpha render of the **same GLB the battle arena stages**
(`../3d/<id>.glb`), at the same `BattleStage3D.MON` target height, under the arena's
own light rig, framed by projecting the body's bounding box. Source page:
`docs/qa/battle-monsters/icons.html`.

## Why they are generated

Until 2026-08-08 these were 16×16 hand-drawn sprites from a CC0 pixel pack
(Clint Bellanger's *Tiny Creatures 1.0*, CC0 1.0 — kept in git history at `633b51fb`
with its full licence record). They were internally consistent and **they described
different creatures from the ones on the field**
(`docs/plans/battle-presentation-inventory.md` §7.3): duskpad's sprite was salmon
over a grey wolf, scree shell's green over a red crab, bramble shade's mint over a
dark root-ball. The turn-order rail exists so a player can plan, and it was showing
colours and shapes the game does not have.

Measured mean-hue disagreement between icon and model, before → after:

| monster | before | after |
|---|---|---|
| reed-nibbler | 95.8° | **4.4°** |
| scree-shell | 105.2° | **1.5°** |
| weir-eel | 164.0° | **24.5°** |
| bramble-shade | 51.6° | **0.1°** |
| duskpad *(grey model — chroma error)* | S +0.43 | **S +0.03** |
| brook-sprite *(see below)* | S +0.49 | S +0.41 |

**brook-sprite is expected to disagree with its GLB and must not be "fixed".** Its
shipped body is CODE — `MON['brook-sprite'].build = 'wisp'`, a pale blue emissive
core in two additive shells — and the grey ghost GLB beside it is only the
documented fallback. Its icon is drawn from `BattleStage3D.PROXY.sprite`, the
module's own palette for that family, so it matches **what the player sees**. Scoring
it against the unused mesh is what would put the lie back.

## Consumers

`battle_turnbased.js` reaches both of these through one convention
(`art.monsterDir` + the monster id), so a new monster needs no entry anywhere:

* the turn-queue / command-window thumbnail (`.ebb-qic`, 28 px — **smooth**, not
  `image-rendering: pixelated`; that declaration was correct for 16 px art and wrong
  for a 256 px render);
* the DOM fallback stage's monster art (`silEl`, ~160–190 px). `fitSprite` only
  pixelates a source under 64 px, so it picks the right filter on its own.

`tools/build-static.mjs` claims this directory by name (`assets/monsters/placeholder/<id>.png`)
— the path is load-bearing in three files and was deliberately not renamed.

## Licensing

Generated from `../3d/*.glb`, which are CC0 1.0 (Quaternius). See `../3d/MANIFEST.md`
for the licence record those renders inherit.
