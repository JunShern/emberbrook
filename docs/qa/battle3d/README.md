# Battle arena v3 — review board

Shot from `tools/ui_mock.html` (the REAL modules, the REAL plates, the REAL
rogue.glb, a REAL WebGL context — nothing about the stage is stubbed) via
headless Chrome + swiftshader at 1600x900.

Reproduce any of these by serving the REPO ROOT and opening the URL:

| shot | URL query |
|---|---|
| `arena-meadow.png` | `view=battle&zone=meadow&group=reed-nibbler,reed-nibbler,brook-sprite&state=target` |
| `arena-forest.png` | `view=battle&zone=forest&group=duskpad,bramble-shade,duskpad&state=cmd` |
| `arena-crag.png` | `view=battle&zone=crag&group=scree-shell,brook-sprite&state=cmd` |
| `arena-water.png` | `view=battle&zone=water&group=weir-eel,brook-sprite&state=cmd` |

## The fallback chain, photographed one tier at a time

Each of these kills a tier at runtime (`BattleStage3D.disable`, driven by the
mock's `?kill=`) so the tier BELOW it is what gets photographed. This is the
chain verified, not asserted.

| shot | what is killed | what you are looking at |
|---|---|---|
| `fallback-1-party-billboard.png` | `kill=partyModel` | Vesper and Maren as their **chroma-keyed pose plates** on camera-facing planes, bottom-anchored on the arena floor with blob shadows. THE RULED 2D-IN-3D PATH, and how every future character appears before their model exists. Foes still on their GLBs. |
| `fallback-2-foe-pixel-billboard.png` | `kill=foeModel` | the monsters fall past the (empty) hi-res plate directory to the **16px pixel sprites**, billboarded, NearestFilter so they stay crisp. Party still on rogue.glb. |
| `fallback-3-proxy-solids.png` | `kill=foeModel,billboard,partyModel` | everything on **procedural proxy solids** — the family-palette shapes for monsters, a mannequin for the party. This is the ~200 ms state at the start of every battle while a 3.5 MB rig parses. |
| `fallback-4-dom-stage.png` | `stage=dom` (= `Battle.stage3d=false`, which is exactly what a page with no WebGL produces) | **the entire v2 DOM stage, unchanged** — one row, flat sprites, plate behind. The look the ruling rejected, kept as the no-WebGL floor. |

`?kill=` accepts `partyModel,foeModel,billboard,plate` in any combination.

## THE PARTY-LOOK FORK (open, awaiting the user's ruling)

`fallback-1` is not only a fallback — it is one of the two candidate looks for
the party in the arena, and the choice between them is **one string**:

```js
BattleStage3D.art.partyBody = 'model'      // rogue.glb first, pose plate behind it
BattleStage3D.art.partyBody = 'billboard'  // the painterly pose plate first, rig behind it
```

Both tiers are shipped and both are photographed here (`arena-*.png` are
`'model'`; `fallback-1-party-billboard.png` is what `'billboard'` produces).
Whichever loses becomes the other's fallback, so nothing is thrown away and no
code changes when the ruling lands. Default today is `'model'`.

## The built-body exception

`brook-sprite` does not come off the asset chain at all: it is built in code
(`BattleStage3D.MON['brook-sprite'].build = 'wisp'`) as an emissive core inside
two additive shells with orbiting motes. A wisp is LIGHT, and the CC0 ghost mesh
that fills the slot on disk reads as a cute monster with eyes no matter how it is
tinted. The GLB stays in `assets/monsters/3d/` as the documented fallback —
deleting the one `build:` line puts it back in play.

## Known, deliberate, not yet addressed

- The sourced monster set has a **style seam**: a realistic wolf (Ultimate
  Animated Animals) next to three textured blobs (Cute Animated Monsters). The
  3d manifest records style-matched alternates where they exist; it does **not**
  record one for the wolf, so replacing it means a fresh CC0 hunt and licence
  verification rather than a swap.
- The KayKit rogue reads greener than either character bust. Parked behind the
  party-look fork: if `'billboard'` wins, the rig becomes the fallback tier and
  the mismatch stops mattering.
