# Battle arena v3 — review board

## The four zone arenas (`arena-*.png`) — shot off the REAL GAME

These come from **play3d.html**, not the mock, via `stage.snapshot()` — the arena
rendering one frame synchronously into a readable drawing buffer. Reproduce:

```
node tools/arena_playtest.mjs --gpu --head --eval=<a probe that calls snapshot()>
```

Two things to know when reading them:

- **They are the ARENA ONLY.** `snapshot()` returns the WebGL canvas, so the
  battle windows (message line, command list, party status) are not in frame.
  That is deliberate: it is a picture of the 3D stage, and the DOM layout is
  verified separately by reading the live DOM (see "Layout" below).
- **Every body is on its final tier** — the probe waits for all of them to leave
  the proxy tier and for the 1.05 s intro sweep to settle, ~100 rendered frames
  in. `meta.tiers` in the probe output records which tier each body ended on.

Why not the mock any more: swiftshader renders this arena at ~0.4 fps, and once
the pacing work added beats to every turn, a mock screenshot stopped finishing
inside any sane budget. A real GPU does the same frame in seconds, and the
snapshot path does not depend on a screenshot of a tab whose canvas may be stale.

The mock is still the right tool for the WINDOWS — `tools/ui_mock.html` with
`?stage=dom` or `?kill=` parks the UI where it can be photographed cheaply, which
is what the fallback board below is.

## The turn queue (`turn-queue.png`)

The bottom-right panel is an ever-updating queue of whose turn comes next,
monsters included — the panel that lets the player plan.

Its order is **never computed by the widget**: it comes from `Battle.queueFeed`,
whose default asks the kernel's `rules.order(state)` — the same function the
commit-then-resolve scheduler ranks its collected actions by. Displayed order is
resolution order by construction, not by two computations agreeing. Verified
against a live battle: the kernel said *Duskpad A, Duskpad B, Vesper, Bramble
Shade*, and the queue consumed in exactly that order, each actor greying to the
tail as it went, resetting on the next round.

- **Decision phase** shows the round's projected resolution order — you choose
  knowing who moves before you do. The character being decided for carries the
  arrow and the amber rail (Vesper, in the shot).
- **Resolution** consumes from the top; acted combatants sink greyed to the
  round's tail rather than vanishing, so the shape of the round stays readable.
- **A KO exits its row immediately**, free: `order()` returns the living only.
- Party rows stay primary (bust, name, LV, HP gauge with numerals, reserved MP);
  foe rows are slimmer on the SAME grid so the columns line up, and carry the
  monster's 16px sprite as a pixelated thumbnail plus the same name the field tag
  shows, so panel and field agree about which Duskpad is which.

**Swapping the scheduler swaps the feed, not the widget.** A future ATB policy
sets `Battle.queueFeed` to one predicting from gauge fill instead of spd order,
returns the same `{id, acted}` shape, and this panel needs no edit.

## Layout and mirror, verified in the live DOM

Read out of a `--dump-dom` of the running mock rather than eyeballed:

| fact | how it reads |
|---|---|
| the message line is at the TOP | `.ebb-log` is inside `.ebb-top`, before `.ebb-field` |
| party on the LEFT | `.ebb-heroes` precedes `.ebb-foes` in the stage |
| commands on the party's side | `.ebb-cmdwin` precedes `.ebb-partywin` in the band |

## The fallback chain, photographed one tier at a time

Each of these kills a tier at runtime (`BattleStage3D.disable`, driven by the
mock's `?kill=`) so the tier BELOW it is what gets photographed. This is the
chain verified, not asserted.

| shot | URL query | what you are looking at |
|---|---|---|
| `fallback-1-party-billboard.png` | `view=battle&zone=meadow&group=duskpad,reed-nibbler&kill=partyModel&state=cmd` | Vesper and Maren as their **chroma-keyed pose plates** on camera-facing planes, bottom-anchored on the arena floor with blob shadows. THE RULED 2D-IN-3D PATH, and how every future character appears before their model exists. Foes still on their GLBs. |
| `fallback-2-foe-pixel-billboard.png` | `view=battle&zone=forest&group=duskpad,bramble-shade&kill=foeModel&state=cmd` | the monsters fall past the (empty) hi-res plate directory to the **16px pixel sprites**, billboarded, NearestFilter so they stay crisp. Party still on rogue.glb. |
| `fallback-3-proxy-solids.png` | `view=battle&zone=crag&group=scree-shell,weir-eel&kill=foeModel,billboard,partyModel&state=cmd` | everything on **procedural proxy solids** — the family-palette shapes for monsters, a mannequin for the party. This is the ~200 ms state at the start of every battle while a 3.5 MB rig parses. |
| `fallback-4-dom-stage.png` | `view=battle&zone=forest&stage=dom&state=cmd` (= `Battle.stage3d=false`, exactly what a page with no WebGL produces) | the DOM stage — flat sprites on the plate, no arena. It MIRRORS with the arena (party left, foes right) and carries the same top message line, bottom band and turn queue, so the two stages never disagree about which side you are on. |

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

## How the foes are blocked (why nobody stands inside anybody)

Three rules, in the order they were needed, each added because a screenshot
showed the previous set was not enough:

1. **Depth is the separation.** The camera's yaw makes a slot's screen-space x
   roughly `0.97x - 0.24z`, so pushing a body along +z drags it left almost as
   fast as +x drags it right — the two nearly cancel and no realistic sideways
   offset separates two combatants horizontally. Distance does, read as size and
   as height in frame. Hence 3.2 m between foe slots.
2. **An alternating sideways jog**, because depth alone left two identical reed
   nibblers in the same screen *column*, one behind the other. At **n = 2 the
   chevron contributes nothing** (`|i - mid|` is 0.5 for both slots, so it moves
   them identically) and the jog is working alone, so it is boosted there — which
   the two-monster case can afford, and two monsters is the commonest encounter
   shape in `encounters.json`.
3. **Stage by height**: slots are handed out tallest-creature-to-deepest-slot, so
   a 1.95 m bramble-shade stands *behind* the wolves instead of eclipsing one. No
   amount of geometry stops a body that wide from covering a neighbour; blocking
   does. Group order is untouched everywhere it means anything — names, targeting,
   turn order — this only decides who stands where.

## Known, deliberate, not yet addressed

- The sourced monster set has a **style seam**: a realistic wolf (Ultimate
  Animated Animals) next to three textured blobs (Cute Animated Monsters). The
  3d manifest records style-matched alternates where they exist; it does **not**
  record one for the wolf, so replacing it means a fresh CC0 hunt and licence
  verification rather than a swap.
- The KayKit rogue reads greener than either character bust. Parked behind the
  party-look fork: if `'billboard'` wins, the rig becomes the fallback tier and
  the mismatch stops mattering.
