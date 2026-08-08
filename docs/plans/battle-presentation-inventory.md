# Battle presentation — inventory and structural slate

2026-08-08, battle-graphics-audit lane. **This is an audit and a brief, not a build.** No
shipped runtime file was edited in this lane; every claim below names the instrument that
produced it. Board with the captures: `docs/qa/battle-audit/index.html`.

**The directive** (user, verbatim): *"the battle arena is pretty unimpressive and uses some
cheap heuristics and a fixed camera angle. We could do a lot to spice this up and bring it to
a more modern look and feel."*

**The framing that matters before anything else.** `docs/plans/director-slate.md` **Bet 10 —
COMBAT PERFORMS (battle juice)** proposes "attack lunges/tweens, hit flash + shake, damage
number motion, turn camera punch-ins, KO/victory beats." **All five of those already shipped**,
on 2026-08-02 (`docs/qa/battle3d/BEFORE-AFTER.md`). The user is looking at the result of the
juice pass and calling it unimpressive. **Bet 10 is spent. The remaining gap is structural**,
and the four structural facts are:

1. the camera does not move (measured: **12.6 mm ≈ 1.4 screen pixels in 3 s**), and it *cannot*
   move, because the backdrop is one flat painted band pinned to its exact pose;
2. the arena is a **procedural diorama with four static images**, standing in front of a
   **real-time 3D region that the game was already rendering better**;
3. the attacker **never reaches the target** (lunge 1.35 m against a 5.21 m minimum gap = 26%);
4. the battle runs a **second renderer with a second lighting model** — no environment map, no
   tone mapping, 174 of 182 materials with no texture — while the scene it replaces has a
   solved key, a PMREM environment, GTAO and bloom.

---

## §0 Instruments used

| instrument | what it produced |
|---|---|
| `node tools/battle_shots.mjs --port=3000 --tag=audit --out=docs/qa/battle-audit` | the four zone frames (whole-frame + `-arena` synchronous renders), the impact pair, the two fallback tiers |
| `node tools/arena_playtest.mjs --port=3000 --gpu --eval=<probe>` | every number in §1–§4: camera pose samples, `renderer.info`, a full scene census (meshes / materials / lights / triangles), `stage.anchor()` for every body, `stage.clipsOf()`, and the `seq-*` sequence frames (opening → swing → impact → KO → settled → "victory") |
| source read, `public/js/battle_stage3d.js` (2256 ln), `battle_turnbased.js` (1962 ln), `battle_rules.js`, `encounters.js` | every `file:line` citation |
| `public/assets/battle/MANIFEST.md`, `public/assets/scenes/ow-valley/zones.json` | plate provenance and the encounter surface |

Everything was shot at 1600×813, `--gpu` (real GL, not swiftshader), `nomusic=1`, party
[vesper, maren] unless stated, seed 4242. `stage.frames` was asserted climbing before every
capture — an instrument that photographs a canvas must prove the canvas was not stalled.

---

## §1 THE CAMERA — it is fixed, and this is the measurement

`battle_stage3d.js` builds exactly **one** camera pose and returns to it every frame:

```
battle_stage3d.js:651   const restPos = camPose(CFG.cam.dist, CFG.cam.pitch, camYaw);
battle_stage3d.js:2094      camera.position.copy(restPos);      // every frame, forever
battle_stage3d.js:2124/2126 camera.lookAt(target …)             // target is a FIXED world point
```

`CFG.cam = {fov 34, dist 11.6, pitch 13, yawMag 14, target [0, 1.15, 0.15]}` — the eye sits
3.9 m up, 11.6 m out, and `target` is the arena **origin**, never the actor and never the
victim. There are four things that ever perturb it, and all four are decorations on one pose:

| perturbation | amplitude | period | what it is worth on screen |
|---|---|---|---|
| intro sweep (`CFG.intro`) | dist ×1.34, pitch +8°, yaw +6° | **once**, 1050 ms, then never again | the only real camera move in a battle |
| idle drift (`CFG.drift`) | 0.075 / 0.05 / 0.045 m | **103 s / 153 s / 217 s** | see below |
| push-in on a strike (`CFG.fx.pushIn`) | 5.5% of 11.6 m = 0.64 m, 620 ms | per strike | a lean, no fov change, no cut |
| hit shake (`CFG.fx.shake`) | 0.10 m (0.19 on a KO), 260 ms | per hit | |

**Measured, at rest, 89 samples over 3.0 s** (probe reads `stage.camera.position` on a 33 ms
tick): span **x 0.0126 m, y 0.0024 m, z 0.0039 m**. At 11.6 m with a 34° vertical fov over
813 px, one screen pixel is **8.7 mm**, so the battle camera moves **1.4 pixels in three
seconds**. The drift's *full* amplitude is 17 px — but its period is 103 seconds and a meadow
fight is 1–4 rounds (`battle-core-design.md` §10), which at the shipped pacing
(`announce 560 + wind 300 + damage 640 + settle 320` = 1.82 s per action) is roughly 20–40 s.
**A player never sees a whole drift cycle.** The user's "fixed camera angle" is not an
impression; it is the number.

**On a turn change: nothing.** On an attack: a 0.64 m lean toward the blow. On a KO: a 0.19 m
shake for 420 ms. On victory: nothing. There is no shot for the actor, no shot for the target,
no framing that changes with who is up — `setActor`/`setTarget` move only the ground *markers*
(`battle_stage3d.js:2148–2159`), never the camera.

### §1.1 Why it is fixed — the load-bearing constraint

`public/assets/battle/MANIFEST.md` states the contract in its own words:

> The virtual camera is 3.9 metres above the ground, tilted 14 degrees downward, with a
> 34-degree vertical field of view. PLACE THE HORIZON LINE AT 42 PERCENT DOWN FROM THE TOP OF
> THE FRAME. […] Those numbers ARE `BattleStage3D.CFG.cam`. **If the arena camera moves, this
> paragraph moves with it and the plates are re-shot.**

The backdrop is a *single curved band* (`backdrop: {dist 34, arcPad 1.16, segs 44}`) built
around `restPos` and only `restPos` (`battle_stage3d.js:801` captures `restDir/restRight`
from the rest pose deliberately, because rebuilding it against the live camera mid-sweep was
non-deterministic). **A camera language is not a tuning change to this stage — it is
incompatible with the way its world is drawn.** Any bet that moves the camera must first give
the arena something to look at from another angle. That is the whole dependency graph of this
document.

---

## §2 THE STAGING — six magic numbers that never read the frame

Slots come from two closed-form functions, `partySlots()` (an offset column) and `foeSlots()`
(a chevron ≤3, two ranks ≥4), off six constants in `CFG.form`
(`partyX 3.2, partyDx 1.05, partyZ 0.35, partyDz 2.0, foeX 3.4, foeSpread 3.2, foeJog 0.78,
foeChevron 0.5, foeRank 2.1`). It **does** adapt to party/enemy count, and it **does** stage by
height (tallest creature to the deepest slot, `battle_stage3d.js:1363–1374`) — that part is
sound. What it never consults is the camera, the frame, or the creature's size.

Measured for the shipped 2×2 case (probe, `stage.anchor()` in a 1600×813 frame):

| body | screen x | screen height | % of frame height |
|---|---|---|---|
| maren (rear party) | 347 | **225 px** | 27.7% |
| vesper (front party) | 489 | **186 px** | 22.9% |
| m1 (near foe) | 1070 | **115 px** | 14.1% |
| m0 (far foe) | 1162 | **89 px** | 10.9% |

- **The middle of the frame is empty.** Nearest party body to nearest foe, **centre to centre:
  581 px = 36% of the frame width** (the bodies themselves are ~60–90 px wide, so ~30% of the
  frame is literally bare floor between the two sides). Visible in all four zone captures.
- **The foes are small.** A duskpad is 89–115 px tall in an 813 px frame. The thing the player
  is aiming at is the smallest object on screen.
- **World gaps:** party slots `[-2.68, -0.65]` and `[-3.73, 1.35]`, foe slots `[4.98, -2.40]`
  and `[2.32, 0.80]` → **min pairwise distance 5.21 m, max 9.47 m**.
- **Name tags collide with the UI.** In `audit-crag.png` the "Scree Shell" tag is half behind
  the turn-order window; the staging has no knowledge of where the windows are.

---

## §3 THE ARENA — a procedural diorama in front of four paintings

**The census** (probe, `scene.traverse`, one settled meadow battle, 2 party + 2 foes):

| | |
|---|---|
| meshes | **182** |
| triangles | **197,907** |
| skinned meshes | 10 |
| lights | **5** |
| materials (unique) | **182** — MeshPhong **157**, MeshBasic 14, MeshStandard 9, MeshLambert 1, MeshPhysical 1 |
| **materials carrying no texture map at all** | **174 of 182 (95.6%)** |
| normal maps in the entire scene | **2** |
| roughness maps | **2** |
| `scene.environment` | **null** |
| materials with an `envMap` | **0** |
| `renderer.toneMapping` | `NoToneMapping` (0) |

**157 of the 182 meshes are the procedural scatter** — 22 grass tufts × 7 four-sided cones,
plus three code-built props. They are placed by `Math.random()` inside a keep-out annulus
(`battle_stage3d.js:944–954`), re-rolled every battle. In the captures they read as exactly
what they are: triangular spikes standing in a smooth field. The rocks are
`DodecahedronGeometry` with a random squash (`:909–915`); the log is a 7-sided cylinder.

**The ground is one untextured Lambert mesh** (`battle_stage3d.js:782`,
`MeshLambertMaterial({vertexColors:true})`): a 30-ring × 72-segment dished disc, 4,320
triangles, coloured by three octaves of value noise. There is **no albedo texture, no normal
map, no detail of any kind**. In `nopost-meadow.png` (the same frame with `CFG.post.on=false`)
this is unmissable — the plate above the seam is painted grass with flowers and a specular
river, and the floor below it is a pale wash with a beige smear where the "trodden centre" is.
**The grade is doing the work of hiding how flat the floor is**, which is a fine thing for a
grade to do and a terrible thing to depend on.

**The backdrop is four Gemini images.** `public/assets/battle/{meadow,forest,crag,water}.png`,
1344×768 each, generated with `tools/genart.mjs` (`gemini-2.5-flash-image`). They are the only
pre-rendered art in this game **not** baked through the repo's own Blender/Cycles/AgX plate
pipeline, and they are keyed to `encounters.json → battleBackdrop`, i.e. to the **zone type**,
not the place. `public/assets/scenes/ow-valley/zones.json` is a 224 × 160 grid at 1.25 m over a
**280 × 200 m** tile — 35,840 cells, five zone types
(`meadow 56.8%, crag 21.94%, forest 13.31%, water 6.34%, road 1.61%`). **Every encounter
anywhere in the valley resolves to one of four static images.**

### §3.1 The forest and water plates are the wrong ground

Verdict by eye, from the captures (this repo's rule: pictures for the verdict):

- **`audit-forest.png`** — the plate is a dark autumn woodland of vertical trunks. The 3D floor
  under it is `ZONES.forest.ground = 0x5e4d31 / 0x7d6540` — **bright sandy tan**, and the
  scatter tufts are **teal-green cones on sand**. The seam reads as a woodland that has been
  clear-felled and replaced with a beach.
- **`audit-water.png`** — the zone is called *water*, the plate is a sunset river, and **there
  is no water in the arena at all**. The eel and the sprite fight on a dry cream dune among
  green reed-cones planted in sand.
- **`audit-meadow.png`** — the best of the four, and still a plastic putting green against a
  painted field.
- **`audit-crag.png`** — the best floor (`grain 1.0` earns it), spoiled by a large untextured
  faceted boulder at frame right that is the single most placeholder-looking object in the game.

---

## §4 THE LIGHTING RIG — the arena and the world it replaces are two different games

**Every battle in this game happens in `ow-valley`.** `zones.json` exists for `ow-valley`
alone, so `SIM.zone()` returns null everywhere else and the director no-ops (`encounters.js`
§9: roads rate 0, unknown zone = safe). `ow-valley` is an **RT scene** (`play3d.html:45`,
`/^ow-/` ⇒ RT), which means at the instant a battle starts the page was rendering:

- honest geometry, no baked plate;
- a solved key light plus **`scene.environment` = a PMREM of the region's own sky**
  ("THE FILL IS THE SKY", `play3d.html:1184–1243`);
- the real-time postfx family: **RenderPass → GTAO → bloom → Output** (`play3d.html:273`);
- a tone-curve investigation (`?tone=`), `worldbounds.json`, and a follow camera.

The battle throws all of it away and builds a second `WebGLRenderer` in a second context with
this instead (probe, live intensities after `IU(v) = v·π`):

| light | type | intensity | colour | pos |
|---|---|---|---|---|
| hemi | Hemisphere | 1.382 | `#d9c48e` | — |
| key | Directional (casts) | 2.702 | `#ffe0b0` | −7, 9, −4.5 |
| fill | Directional | 0.691 | `#9fb6d8` | 6, 4, 7 |
| **rim** | Directional | **3.927** | `#ffebd0` | −3, 1.05, −12 |
| ambient | Ambient | 0.377 | `#ffffff` | — |

Five hand-tuned lights, per-zone hex palettes hardcoded in `ZONES`, **no environment map, no
GTAO, no tone mapping**, and a hand-rolled 4-pass grade (bright → 2× blur at ¼ res →
composite) whose constants are display-space and whose `LIN2DISP` conversion is the r185 trap
this file has already paid for once.

**The consequence is concrete, not aesthetic.** The party rigs bring 9 `MeshStandardMaterial`
and 1 `MeshPhysicalMaterial` into the arena. Those materials' entire specular response is
image-based, and **`scene.environment` is null and no material has an `envMap`**. The same
character, in the same second, is lit by an IBL in the field and by a hemisphere in the battle.
`relight()` (`battle_stage3d.js:1072`) additionally *downgrades* any `MeshBasicMaterial` from a
monster GLB to Lambert. **The arena's ceiling is Lambert/Phong.**

---

## §5 IMPACT AND FEEDBACK — the attacker never arrives

This is the most legible defect in the whole audit and it is a single number.

```
battle_stage3d.js:147   act: { lungeM: 1.35, ms: 620, flinchM: 0.42, flinchMs: 330, … }
```

Minimum party↔foe slot distance: **5.21 m**. Lunge: **1.35 m = 25.9% of it.** The attacker
travels a quarter of the way, swings, and the flash/sparks/shock-ring fire on a body **four
metres away**. `audit-impact-swing.png` and `audit-impact-arena.png` show it exactly: Vesper is
at x≈630 px in mid-lunge and the struck wolf is at x≈1170 px, with 540 px of empty grass
between the swing and the hit. **She is also empty-handed** — the turnaround spec
(`CLAUDE.md`, character factory step 2) says "hands empty", no rig carries a weapon, and the
economy's whole visible payoff ("sell drop, buy weapon, equip, hit harder",
`combat-ecosystem.md` §The vertical loop) has **zero visual consequence**.

Everything else in the hit package is present and correctly budgeted: an emissive flash
(`flash 0.62, 150 ms`), an 18-particle amber burst at 0.30 m, a white shock ring, a 0.10 m
camera shake, a 6 cm shove with air under it, a dust puff in the zone's own dirt colour. **The
pieces are right and the geometry is wrong**: no amount of spark tuning fixes a blow landing on
a body nobody touched. There is also **no hit-stop** — the mixer and the tweens run straight
through contact, so the frame the damage lands is not held.

Two related timing facts: `CFG.act.fit` refits every donor clip to the turn's beat
(attack→620 ms, hit→330, die→1000) clamped to 0.6–2.2×, which is a good mechanism; but the
damage event fires on a fixed `pacing.wind = 300 ms` after the announce, not on the clip's own
contact frame.

---

## §6 THE CAST — what a body can actually do

`stage.clipsOf()`, measured on all four bodies in a settled meadow battle:

```
vesper: ["idle","attack","hit","die"]   maren: ["idle","attack","hit","die"]
m0:     ["idle","attack","hit","die"]   m1:    ["idle","attack","hit","die"]
```

The stage asks for **six** intents (`CLIP` = idle, attack, hit, die, item, cheer). **Two bind
nothing on every body in the game**, and those two have no procedural fallback:

| verb | code | what actually happens |
|---|---|---|
| **victory** | `battle_stage3d.js:2190` `cheer()` → `oneShot(b,'cheer')` | **nothing.** `seq-6-cheer.png` is the party standing in their idles. The victory pose of this game does not exist. |
| **item** | `battle_stage3d.js:1660` `if (kind === 'item') { oneShot(b,'item'); return; }` | **nothing**, and the early `return` also skips the lunge — using a tonic is a body standing perfectly still while a green number appears. |
| **flee** | `battle_stage3d.js:1661` `if (kind === 'flee') return;` | **nothing at all**, by construction. |

### §6.1 The KO is an evaporation

`markDead()` fades opacity to 0 over 720 ms, sinks the root 0.55 m, and then
`b.obj.visible = false` (`battle_stage3d.js:1801` and `:1821`). Measured in the sequence:
`seq-4-ko.png` (340 ms) shows the wolf on its side, translucent, with a dust puff — that beat
reads. `seq-5-ko-settled.png` (1.2 s) shows **an empty patch of grass**. No corpse, no
dissolve, no residue, the camera does not move, and **nobody else in the frame reacts**: the
survivors are back in their neutral idles the same second. The loudest event a turn can produce
leaves the frame in the same state it started.

---

## §7 THE UI / 3D JOIN

Sound in architecture, with two measured problems.

The join itself is good: in arena mode every combatant's DOM furniture becomes a zero-width
anchor that `syncAnchors()` (`battle_turnbased.js:946`) parks over the projected body every
frame — six style writes per combatant per frame, no layout, and the whole DOM stage survives
as the fallback if `BattleStage3D.create()` returns null. `UILOCK` is held for the battle's
whole life, a capture-phase key listener swallows input, and `destroy()` drops the context.

1. **DPR asymmetry.** `battle_stage3d.js:610` calls
   `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`. **`play3d.html` never calls
   `setPixelRatio` at all** (`play3d.html:163` is `new WebGLRenderer({antialias:true});
   R.setSize(W,H,false)`), so the field renders at CSS pixels. On the user's Retina display the
   battle therefore renders **4× the fragments the field does**. Nobody has measured what that
   costs; a DPR capture lane is live tonight under `docs/qa/dpr/` and this belongs in its
   findings. Headless (dpr 1, 1600×813) the arena idles at **120 fps** (vsync-capped), so this
   is not a *measured* problem — it is an unmeasured one.
2. **`preserveDrawingBuffer: true` ships on by default** (`battle_stage3d.js:608`, gated on
   `CFG.snapshots !== false`) — a per-frame readback cost carried in the shipping build for a
   QA feature. Its own comment names the trade; nobody has priced it.
3. **The turn-order panel disagrees with the field.** Foe icons are the 16×16 placeholder
   sprites (`foeIcon: (mid) => monsterUrl(mid)`, `battle_turnbased.js:1833`). Duskpad's icon is
   **salmon-pink**; the duskpad on the field is a **grey wolf**. Bramble Shade's icon is
   **bright green**; the model is a **black root-ball**. The panel that exists so the player can
   plan shows monsters in colours and shapes they do not have. Party rows next to them carry
   30 px painted busts — two art registers in one table.

---

## §8 THE MONSTERS — six creatures, at least four art directions

By eye across the four zone captures: a semi-realistic grey **wolf** (duskpad); a bright green
cartoon **blob with one black dot** (reed nibbler); a glossy **crimson blob** (scree shell —
described in `monsters.json` as "a boulder with legs"); a green cartoon **snake with a red
tongue** (weir eel); a black gnarled **root-ball** (bramble shade — the best of them); and a
**solid white sphere** (brook sprite, the hand-built `wisp`, whose two additive shells read as
an opaque pearl once the bloom hits it). They are sourced CC0 GLBs from unrelated packs,
normalised only for *height* through the `MON` table. Nothing normalises their style.

---

## §9 WHAT IS ALREADY RIGHT (do not spend a bet re-doing these)

Recorded because a rebuild that discards them is a regression:

- **The fallback chain is real and photographed**, not asserted: model → pose-plate billboard →
  proxy solid → DOM stage, each killable at runtime via `BattleStage3D.disable`
  (`audit-fb-plate.png`, `audit-fb-proxy.png`).
- **The party is the real cast** and it is the same GLB files `play3d.html`'s `MODELS` registry
  hands the overworld, resolved through a versioned preference list.
- **The seam is architecturally clean**: `BattleStage3D` owns pixels and geometry only —
  8 verbs, no battle state, no `GS`, no event stream. `battle_rules.js` is untouched by any
  bet below and must stay that way.
- **Cast shadows, the near-horizontal rim, the grade, the hit package, the markers, the turn
  queue, the pacing beats and the victory tally** are all shipped and all tuned against
  pictures. The grade in particular is the reason the frames hold together at all.
- **Teardown is total**: renderer disposed, context force-lost, rAF cancelled, tweens dropped,
  shared canvases spared by identity. `arena_playtest` gates it.

---

## §10 THE SLATE — ranked by player-visible impact ÷ risk

Each bet states what it changes **structurally**, its cost, what could go wrong, and what would
**prove** it worked. Ranks 1–3 are the recommendation.

### ⭐ 1. BET C — CONTACT (the attacker reaches the target, and the frame holds)
**Structural change.** Replace the fixed 1.35 m lunge with an **approach to a strike station**
derived from the target's own body: travel to `target − n̂ · (rA + rB) · 1.1`, strike there,
return. Time the damage event to the clip's own contact frame instead of a fixed 300 ms
`pacing.wind`. Add a **hit-stop**: freeze both bodies' mixers and every tween for ~80–110 ms at
contact, then release. All of it inside `act()`/`flinch()` plus one `Battle.pacing` field.
**Cost.** Small. One file, no art, no new asset, no `play3d.html` edit, kernel untouched. The
travel time must come *out of* the existing announce/wind budget, not be added to it.
**Risk.** Turns get longer if the budget is not respected; a body approaching another body can
interpenetrate (needs a stand-off floor); ranged/caster actions will need a projectile path
instead — none exist today, so this is future work not blocking work.
**Proof.** A six-frame strip of one strike; **attacker–target centre distance at the `damage`
event ≤ 1.4 m** (assertable from `stage.anchor()`); total turn wall-clock unchanged within
±5%; `arena_playtest` and `battle_sim` green.
**Why it is first.** It is the frame the player looks at on *every single turn*, the failure is
a single measured ratio (26%), and it is the cheapest, least risky, most independent item on
this list. If exactly one thing ships, ship this.

### ⭐ 2. BET B — A CAMERA LANGUAGE (a shot per beat, not one angle)
**Structural change.** A **shot table plus a solver**, the live analogue of the town's
`cameras.json → cine_solve → shot` pipeline: `shot(kind, actorId, targetId) → pose`, with a
per-kind transition policy (cut vs. move vs. hold) and a rest pose it always returns to. Six
kinds to start: `round` (wide), `decide` (medium on the deciding character), `strike`
(low three-quarter favouring the attacker), `impact` (a hold, paired with BET C's hit-stop),
`ko`, `victory`. Plus real idle drift — the current one is a 103-second cycle and should be a
3–6 second one.
**Cost.** Medium, contained in `battle_stage3d.js` + one data table. **Gated on the backdrop:
it cannot ship against a single band pinned to `restPos` (§1.1).** It rides BET A, or it needs
BET E's wide/cube plate first.
**Risk.** A battle camera that cuts every beat is unreadable and can be nauseating. It needs a
rule set, and the rules are already implied by this repo's own doctrine: **never cross the
axis** (`CFG.partySide` is the only place handedness is written down — the party stays on the
left in *every* shot), at most one cut per action, always settle back to rest, and no fov push
(the file's existing argument: a zoom reads as a cut).
**Proof.** A contact sheet of the six shot kinds; an **automated 180°-rule assertion** — for
every shot in the table, every party body projects left of every foe body; a blind read (the
`nav_eval` pattern) on "whose turn is it / who is being hit" against the current build.
**Why it is second.** It is the thing the user actually named.

### ⭐ 3. BET A — FIGHT WHERE YOU STAND (the arena becomes the world)
**Structural change.** Stop building a diorama. **Every battle in this game already happens in
`ow-valley`, a real-time GTAO+bloom region with a solved key, a PMREM environment and 280×200 m
of authored terrain** (§4). The battle borrows `play3d.html`'s scene and camera instead of
replacing them: freeze the player, place the party and the foes on the real ground at the
player's own position, drive the existing camera, run the fight, restore. This **deletes** the
procedural dish, the four Gemini plates, the backdrop band, the mist ribbon, the five-light
rig, the hand-rolled grade, the second WebGL context and the 157 scatter cones — and it
**unpins the camera** (there is no painted band to honour), which is what makes BET B and BET D
nearly free.
**Cost.** Large, and mostly political: `play3d.html` is coordinator custody and exposes no
render hook, which is one of the three stated reasons the stage owns its own renderer
(`battle_stage3d.js:30–42`). Needs a "battle borrow" mode with a proven restore, foe placement
against `SIM.walkFloors`/`SIM.ground`, and the stage's verbs (rings, flash, sparks, shock ring)
re-homed into the field scene.
**Risk.** **HIGH, and it lands in a known-bad area**: `docs/qa/playtest/queue.json` already
carries four open tickets about exactly this failure mode — PT-20260803-009 (*camera detached
or character missing after battle*), -019 (*battle softlocks after defeating the enemy*), -025
(*camera clipped under map geometry after battle*), -028 (*glitched view and out-of-bounds
geometry after battle*). Borrowing the world's camera makes those tickets' blast radius bigger,
not smaller. Also: the party+foes must not enter `collide`/`walkRef`/`allMeshes` (the
`followers.js` rule), and the encounter can fire anywhere — including places with no room to
stage a fight.
**Mitigation, and it is the repo's own idiom.** Ship it behind a switch (`?arena=world`) with
**the diorama kept as the fallback exactly the way the DOM stage is kept behind the arena
today**. One flag, both paths shipped, the ruling on which is the game's look is the user's.
**Proof.** The same encounter fired at three different positions in `ow-valley` producing three
visibly different frames; GTAO visible at the party's feet; `arena_playtest` (contexts, heap,
teardown) green; `transition_test` green; the four queue tickets re-driven.
**Why it is third and not first.** Highest ceiling *by a distance* — it solves the two-pictures
problem, the four-plates problem, the two-lighting-models problem and the camera-pinning
problem in one move — but the highest risk, and it needs a coordinator decision before a lane
starts.

---

### 4. BET F — THE CAST FIGHTS (clip coverage + a weapon socket)
Extend the retarget donor set to cover the intents the stage already asks for and gets nothing
for — **cheer/victory** and **item-use** (§6) — plus guard and flee. Add a **weapon socket**: a
named bone attachment fed by `GS`'s equipped weapon, so the economy's payoff is visible.
*Cost:* medium, character-factory lane (`vesper_retarget.py`, gated by `vesper_verify.py`).
*Risk:* retarget quality; the gates exist. *Proof:* `stage.clipsOf()` returns ≥6 kinds for every
party member, one photo each; the same character photographed with two different equipped
weapons. **This is the cheapest bet that fixes a *nothing happens*.**

### 5. BET G — STAGING SOLVED AGAINST THE FRAME
Replace the six magic constants with a solve: choose slots so every body's projected box lands
inside a target band, no two overlap on screen, nothing lands under the command or status
windows, and the 36% empty centre closes. The town pipeline's own idea (fit the region to the
camera), applied to four bodies. *Cost:* small–medium, one file. *Risk:* tighter staging fights
BET C's approach — ship them together. *Proof:* an anchor census over every encounter shape
(1–5 foes × 1–3 party) asserting minimum pairwise screen separation, a foe height floor
(say ≥18% of frame height), and empty-centre fraction < 20%.

### 6. BET D — ONE LIGHT MODEL AND ONE GRADE WITH THE FIELD
Take the rig from the same source the field does (`public/game/lightrigs.json` / the region's
own solved key), build the same PMREM environment so the cast's `MeshStandard`/`MeshPhysical`
materials have a specular response at all, and either share the field's postfx stack (free
under BET A) or re-author against it. *Cost:* low under BET A, medium standalone. *Risk:* this
file has already paid for the r185 colour-space trap once — a display-space grade must convert
explicitly (`LIN2DISP`), and the `IU() = ×π` light conversion must survive. Getting it wrong
last time cost a stop and a half **with every gate green**. *Proof:* `tools/shot_compare.mjs`
L05/L50/L95 + chroma between a field frame and a battle frame of the same place; the arena's key
direction within 1° of the region's.

### 7. BET I — THE KO AND THE VICTORY ARE EVENTS
A KO beat (a hold, a dissolve carrying the zone's own particles, survivors reacting) and a
victory beat (a camera move to the party, poses, the tally arriving on that frame). *Cost:*
low–medium. *Depends on* BET B (camera) and BET F (clips) — it is what those two are for.
*Proof:* the sequence re-shot; `seq-5-ko-settled` no longer shows an empty patch of grass.

### 8. BET H — MONSTERS THAT LOOK LIKE ONE GAME
One art direction and one pipeline for the six creatures (§8); derive the turn-queue foe icon
from an offscreen render of the actual model instead of a 16 px placeholder (§7.3). *Cost:*
high (art), but the character factory already exists. *Proof:* the six side by side; icon and
model matched by measured mean hue.

### 9. BET E — THE DIORAMA BELONGS TO THE PLACE (**only if BET A is refused**)
Keep a separate stage but bake its backdrop and its floor **from the real place**: use
`cine_bake` (Blender headless, ray-cast visibility — the repo's only visibility oracle) against
the `ow-valley` region to produce a **cube or wide plate per region** rather than four images
per zone-type, and derive the floor's albedo/normal from the region's own terrain material.
That unpins the camera (a cube map is pose-free) and gives the floor texture. *Cost:* high — a
new bake lane. *Risk:* it is the "make the diorama better" answer, which is what the 2026-08-02
pass already did once and is what the user is calling unimpressive. **Listed last on purpose.**

### Sequencing
**Wave 1 (independent, ships now):** BET C + BET G together, BET F in parallel in the character
factory. None of them touches `play3d.html`, none needs a plate, none needs a ruling.
**Wave 2 (needs a ruling first):** BET A behind `?arena=world`; if granted, BET B and BET D
follow it almost for free, then BET I.
**Wave 3:** BET H. **BET E only if BET A is refused.**

---

## §11 CONSTRAINTS — what every bet above must respect

1. **`battle_rules.js` is untouchable.** Pure, node-loadable, no DOM, no `Date.now`, no
   `Math.random`. Nothing in this slate computes a number, changes turn order, or touches
   damage. `battle_sim` and `encounter_sim` must stay green *by not being affected*.
2. **`Battle.start(spec, party, opts) → Promise<result>` is the only surface** the world knows.
   xp/gold/drops are **reported, never applied** — `GS.applyBattleResult` is the world's job. A
   presentation bet may not reach around it.
3. **`UILOCK` is the modal-input contract** (combat-ecosystem Rulings §5/§8): every panel holds
   it while open, `phys()` freezes, held keys zeroed, and modals are mutually exclusive by
   construction. BET A must hold it across a borrowed-camera battle exactly as today.
4. **The save/beat/ledger contracts.** Autosave fires on `'eb-scene'` only once `beats` is
   non-empty; the `at` block is the resume authority. **A battle must not emit `'eb-scene'`,
   must not move the player's `at.scene/at.cam/at.pos`, and must not write a save.** BET A is
   the one that could break this by accident.
5. **Module self-arming.** Every module in `public/js/` self-arms at load *and* re-arms on
   `'eb-scene'`. A parse error is invisible until an in-place scene swap. **A backtick inside a
   CSS comment inside a template literal terminates the string** — `battle_turnbased.js:207` has
   already paid for this once. `transition_test`'s console gate is what catches it.
6. **r185 colour management.** (a) A display-space grade must convert **explicitly** — r185
   renders into a non-XR target in the *linear* working space whatever the texture declares, and
   declaring `SRGBColorSpace` allocates `SRGB8_ALPHA8` and round-trips the encode away.
   (b) `IU(v) = v·π` exists because r128 scaled every light by π inside `WebGLLights` and r185
   does not. (c) A hand `convertSRGBToLinear` is now a **double** conversion. Getting (a) wrong
   cost this exact file a stop and a half with every gate green.
7. **60 fps budget, and the machine.** Headless the arena idles at 120 fps at dpr 1; the
   shipping path runs `setPixelRatio(min(dpr,2))` while the field does not (§7.1) — **price
   before adding fragments.** Max 3 concurrent heavy jobs machine-wide; browser tools go through
   `tools/cdp.mjs` and reap their own Chrome by `--user-data-dir` prefix; never pattern-kill
   Chrome by name.
8. **Single-player plus companions** (user ruling 2026-08-02, do not re-open). The router and
   the parallel-seat scheduler are real seams and must survive; staging must read
   `GS.activeParty()` and never assume a party size.
9. **The fallback chain is a feature.** model → pose plate → proxy solid → DOM stage, each
   killable at runtime and each photographed. Any bet must land with its fallback intact and
   photographed the same way (`BattleStage3D.disable`).
10. **`play3d.html` is coordinator custody.** BET A's render/camera hook is a coordinator
    decision before a lane starts, not a lane's own call.
11. **Seam canon does not govern this screen — but confirm it.** `docs/plans/seam-canon.md`
    governs **walk-triggered** camera changes in a town: cuts that happen *to* a player who is
    navigating. The battle screen is modal, exclusive, entered and left through its own 350 ms
    veil, and the player is not navigating inside it. A cut on a beat is therefore not a
    "passage". **This reading should be confirmed by the coordinator before BET B ships cuts**,
    because the doctrine's spirit ("one cut per passage") is the reason the current file
    deliberately refuses a fov push.
12. **Teardown stays total.** No leaked WebGL context, no leaked rAF, no leaked geometry —
    `arena_playtest`'s serial suite is the gate, and the four open post-battle queue tickets
    (§ BET A) are the standing evidence that this is where battles break the world.

---

## §12 OPEN QUESTIONS FOR THE USER / COORDINATOR

1. **BET A or BET E?** Borrow the world (highest ceiling, `play3d.html` hook, real risk) or
   keep a diorama and bake it from the real place (safer, and is the answer that already failed
   to satisfy once)? Everything downstream depends on this one call.
2. **May the battle camera cut?** (§11.11.) If cuts are refused, BET B degrades to moves-only,
   which is still a large improvement but a different design.
3. **Do weapons appear in hand?** BET F's socket makes the equipment economy visible and
   changes the turnaround spec's "hands empty" rule for future characters.
