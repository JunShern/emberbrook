# The battle stage, 2026-08-02 — the real cast, and a look pass

Shot with `node tools/battle_shots.mjs --tag=before|after`, which drives the REAL
`play3d.html` over CDP on a real GPU, parks a battle at its command menu, and
captures two kinds of picture per scenario:

| file | what it is |
|---|---|
| `<tag>-<zone>.png` | `Page.captureScreenshot` — **the whole frame**, arena and every battle window. What the game looks like. |
| `<tag>-<zone>-arena.png` | `stage.snapshot()` — the WebGL canvas alone, rendered **synchronously**. Screenshot timing cannot catch a 150 ms hit flash; a synchronous render can, so VFX frames come from here. |

Every capture asserts `stage.frames` climbed by ≥30 first: an instrument that
photographs a canvas must prove the canvas was not stalled.

**What is committed here is a SUBSET.** The tool shoots five zones plus two
fallback tiers in both kinds; the board keeps the four before/after composite
pairs and the four `-arena` frames that carry a claim a composite cannot (the
impact timing, the two killed tiers). Re-shoot the rest in one command — the
scenarios are the tool's own shot list, not a note here.

---

## What the frames look like, side by side

### `before-meadow.png` → `after-meadow.png`

**Before.** Two identical emerald-green hooded chibi figures stand on the left —
the same borrowed CC0 KayKit rogue twice, one of them nominally dyed teal and
indistinguishable from the other. The turn-order panel at bottom right shows two
distinct painted busts, Maren and Vesper, so the panel and the field flatly
contradict each other about who is in this battle. The floor is a large, evenly
lit olive-tan pancake: its mottling is faint, its trodden centre barely reads,
and it changes material visibly where it meets the painted plate at the horizon
line. Nothing casts a shadow — each body has only a small dark smudge, and the
two heroes look like they are hovering a centimetre up. The corners of the frame
are exactly as bright as the middle. The painted backdrop, meanwhile, is a graded
golden-hour photograph with a bloomed sun, a silver river and dark bushes. Two
pictures in one frame.

**After.** Vesper (auburn braid, teal coat, satchel) and Maren (cream headband,
striped shirt over a teal vest, boots) stand where the rogues were — two
different people, and the same two people the busts in the panel show. Both throw
long, soft, warm-edged cast shadows across the grass toward the camera, and so do
the two reed nibblers, the grass tufts and the log. The floor is a warm green-gold
meadow with a sunlit sweep behind the party and a cooler shadowed foreground; a
vignette darkens all four corners so the frame has a centre. The sun still blooms
at the horizon — but only the sun and the river's specular, not the grass. The
seam where the 3D ground meets the plate now reads as haze rather than as a
material change.

### `before-crag.png` → `after-crag.png`

**Before.** *Three* identical green rogues — Vesper, Lake and Maren — against a
huge, flat, shadowless pale-tan dune. The wolf and the scree shell sit on the
surface without touching it. Three distinct painted busts in the panel; one
borrowed body on the field, three times.

**After.** Maren, Lake (brown hair, grey-blue coat over a rust waistcoat) and
Vesper, three readable silhouettes staggered in depth. Every rock on the dune has
a dark side and a shadow; so do all five combatants. The dune reads as sunlit
sand with cool hollows instead of as one value.

### `after-impact-swing.png` and `after-impact-arena.png`

Two synchronous frames from the same strike, 210 ms and ~340 ms in.

- **Swing.** Vesper has travelled a body-length toward the wolves and is leaning
  through the blow; her ground marker has travelled with her. The target marker
  under the far wolf is the new one — a warm amber disc with a bright rim and four
  tick arcs that turn.
- **Impact.** The struck wolf is hot white while its twin beside it is grey, so
  there is no question which one took the hit. Amber sparks are scattered out of
  its silhouette, a white shock ring is expanding on the ground under it, and a
  faint puff of dirt hangs where Vesper planted her foot.

### `after-fb-plate-arena.png`, `after-fb-proxy-arena.png`

The fallback chain, photographed rather than asserted (`BattleStage3D.disable`,
driven by the shot list's `kill:`):

- `partyModel` killed → Vesper and Maren are their **chroma-keyed pose plates** on
  camera-facing planes, bottom-anchored, casting cutout shadows. Foes still on
  their rigs.
- `partyModel,foeModel,billboard` killed → everything on **procedural proxy
  solids**, still lit, still shadowed, still graded. No holes.

---

## What changed, and why those things

### 1. The real cast (`art.models`)

`art.charModel` was `assets/characters3d/rogue.glb` and it was every party
member's tier-1 body. It is now `null`, and `art.models` names each character's
own retargeted rig — **the same files play3d.html's `MODELS` registry hands the
overworld**, which is read from here and never edited. A value may be a *list*
(`vesper-v2.glb`, then `vesper.glb`): the character factory versions its
deliveries and a lane can be mid-retarget while a battle runs, so a rig that has
not landed costs a silent 404 rather than a hole. Lake's `lake-v1.glb` landed
during this pass and was picked up by exactly that mechanism, with no edit.

The dye table (`tint`) is now empty. Dye is for a borrowed model; tinting a
character's own textures only soils them.

A character with no rig now falls to **their own painted pose plate**, then to the
mannequin — never to a wrong-identity body.

### 2. Cast shadows

The single biggest "this is a diorama" tell. One shadow-mapped key at 2048, with
the ortho box wrapped to ±9 m around the fight rather than around the 20 m
clearing — a shadow camera sized to the clearing spends 90 % of its texels on
grass nobody looks at. Bodies, props and the ground all participate. The blob
shadow stays, dropped to ~0.44 opacity, as the tight contact darkening a shadow
map at this density cannot resolve — and as the only grounding a body has if a
driver refuses shadow maps at all.

**A light does not cast a shadow**: the `built` tier (the brook sprite) is
excluded, after the first water pass put a hard dark ellipse on the shore beside a
glowing spirit.

### 3. A near-horizontal rim light

Every one of the four plates is backlit — the sun is at or behind the horizon —
and the arena's key came from the front, so bodies read as flat cutouts laid on a
lit photograph. three r128 tests a light's layers against the **camera's**, never
against the object's (verified in the shipped bundle), so there is no such thing
here as a light that touches bodies and not the floor. What there is, is a sun at
the horizon: at y 1.05 over z −12 the rim is 8.7° above level, so a floor facing
straight up takes ~0.09 of it and a body's back takes ~0.99.

The hemisphere came down 0.50 → 0.44 and the ambient 0.15 → 0.12 to pay for it:
same total on the lit side, floor a stop down, which is what lets a character hold
the frame.

### 4. One grade over the whole frame (`CFG.post`)

Four hand-rolled passes — bright pass, two blurs at quarter res, composite — since
this page ships no EffectComposer and `play3d.html` is read-only. The composite
does bloom add → contrast about mid grey → split tone (highlights warm, shadows
cool) → saturation → vignette → grain, in that order, and it runs over the
**plate as well as the arena**, which is the point: one photograph, not two.

**Measured in two rounds.** Round one (bloom 0.62, threshold 0.70) put a milky
glow over the lower half of every frame — the crag's dune went white and the
meadow's trodden centre vanished under it. The grade runs in display space, where
0.70 catches sunlit *grass*, not just the sun. Round two: bloom 0.40, threshold
0.80. Kill switch: `BattleStage3D.CFG.post.on = false`.

### 5. Hit feedback (`CFG.fx`)

A budget, not a wish list — a turn-based game shows one event per beat, and
anything that lingers is still on screen when the next number lands. Per hit:
an emissive flash on the struck body (additive, so a dark monster and a pale hero
both read as *struck* rather than both reading as white), a shove with 6 cm of
air under it, an amber spark burst, a white shock ring on the ground, and a
decaying camera shake. A KO gets the loud shake and a puff of the zone's own dirt.

Two numbers were wrong on the first pass and are recorded because they are the
kind of thing that gets re-broken: spark **size is in metres**, and 0.14 m at 12 m
is under three pixels — the burst was in the frame and invisible; and white sparks
over a white flash are sparks nobody sees, hence amber.

### 6. The procedural swing — because the cast have no combat clips

The shipped rigs carry `Idle`, `Walking_A` and `Jump_Full_Short` and nothing else;
the character factory's donor set is a locomotion set. So `oneShot(b,'attack')`
finds nothing, and before this the party's whole attack was a body sliding forward
on its idle. The arena now supplies the motion: wind-up, snap through, settle,
rotated about `up × fwd` so it works for any facing, plus a recoil twin on the
hit. **It stands down the instant a clip exists** — `clipped` is the mixer's own
answer, so the day the factory ships an attack clip for Vesper, hers plays and
this code never runs for her.

> **This is the one thing here that is a workaround rather than a fix.** The real
> answer is attack/hit/death clips in the retarget pipeline. Flagged, not hidden.

### 7. Camera language and markers

The camera leans 5.5 % of its distance into a strike and back on the lunge's own
curve — no fov change, because a fov push is a zoom and reads as a cut. Markers
were a hard white annulus that read as a debug gizmo; they are now a soft additive
disc, a bright rim and four turning ticks, and they **follow the body** (read off
the pivot's world position, the same source `anchor()` uses) instead of standing
in the grass the fighter just left.

---

## Gates

`battle_sim` and `encounter_sim` green — the kernel is untouched, which is what
those two prove. `arena_playtest` green on all suites (organic, nogl, serial; no
context leak, warm heap drift 1.4 MB). `transition_test` green.
