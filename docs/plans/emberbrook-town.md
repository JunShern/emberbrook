# EMBERBROOK — THE TOWN PLAN

**What this is.** The founding document for the game's namesake town: a **translation
of `public/townmap/emberbrook.map.json` into a build order, a camera grammar and a set
of gates**. It is not an invention. The map is Stage 0 and it is already authored —
twenty landmarks, five districts, eighteen edges, five parcels — by the same
landmarks-first process that founded Dellhollow. Landmark ids, names, positions and
premises in that file are canon here. Where the scripts and the map disagree, this
document *raises the conflict for the morning board* (§8) rather than silently moving
anything.

**Status.** Founded 2026-07-31. Blockout: the whole map's massing. Real build:
**Festival Square** (plaza + Heartlight + the shop/inn cluster). Cameras: six, solved
and baked as `emb-cine`, entry at the Village Arch. Everything else is honest gray.

---

## 0. The authorities, in order

| authority | what it settles |
|---|---|
| **`public/townmap/emberbrook.map.json`** | **the town: what exists, what it is called, where it stands, what it is for.** Stage 0. |
| `STORY.md` + `docs/VOICES.md` | what the Heartlight *is*, what the lamps are *for*, what the Hush costs |
| `public/js/chapter1.js` | the cast's posts and the beats each place must stage |
| `public/assets/scenes/{square,lane,entrance,gate}/*.png` | the **look** — the shipped Ch. 1 backdrops are accepted art direction |
| `docs/plans/seam-canon.md` | every camera rule below, each one a Dellhollow scar |

Additions made to the map tonight, and they are schema only, not content: the
`walkSceneKey` / `playSceneKey` / `cameraFile` triple that `dellhollow.map.json`
carries and `emberbrook.map.json` predates (§7), plus `kind: "water"` handling so the
pond builds as `water_` rather than as walkable floor.

---

## 1. The town's identity — and it is the exception, gloriously

**Emberbrook HAS a Heartlight.** Globally these are nearly extinct: three centuries of
recalls, a handful left, most towns living perfectly well on ordinary lanterns and
plain human warmth. Emberbrook is one of the survivors, on two accidents — an unbroken
keeper line and a sealed gate — and **that fact is the town's whole identity**.

Which makes the build rule the opposite of the one Dellhollow follows:

> **This is a village of magical lanterns.** The Heartlight on its pedestal in Festival
> Square is the reservoir; every lamppost in the village is lit *from* it and carries
> its radiance out to the doors. A lit lamp bathes its street in three hundred years of
> the village's own best days. "Dark lamp, dull street" is literal (STORY.md §2).

Three consequences that are design instructions, not flavour:

1. **The Heartlight pedestal is a primary camera subject.** It is the brightest thing
   in every frame that contains it, it is what Chapter One takes away, and a player has
   to have *stood in its light* for the Hush to cost anything.
2. **Lake's round is the camera spine.** The lamplighter's job — *"carry the flame from
   the village's heart to a lamppost near every home"* — walks the plaza, the pond
   lane, the home lane and back. That circuit is the sequence of shots, in that order,
   and evening ambience should be authored as *the round arriving*: the square lit
   first, the lanes still dark, then each one warming as its lamp takes the flame.
3. **Lantern placement is a storytelling layer.** A lamp says *somebody lives inside
   30 m of here and is inside the warmth*. The Old Gate — the one place in the village
   nobody's warmth reaches — gets no lamp at all, and the shipped `gate/gray.png` is
   correct to be nearly monochrome.

---

## 2. The shape of the map

Emberbrook is a **flame-village on a high valley** (Odessa, Ch. 2), three hundred years
old, founded from a carried ember. Five districts on a rise, drawn to the map's own
coordinates (`x` west→east, `y` south→north, `z` height, 1u ≈ 1 m):

```
   y
   45 ┤                          ▓▓ THE SIGIL GATE ▓▓  (38,41) z2.7
      │                              sealed, Ch1 set-piece
   40 ┤                    ╔═══════════════╗        ▪ trailhead (45,39)
      │        GATE FIELD  ║  gate-court   ║────────── into the WHISPERWOOD
      │            z2.5    ║   (38,37)     ║
   35 ┤                 ▪ barn (33,34)  ╱     ╲
      │                    │        ╱            ╲   back path
      │   ▪ bench (14,29)  │     ╱                  ╲
   30 ┤   ╲   ▪ elder-house│  ╱  ▪ washline green (41,30)
      │     ╲    (19,31)   │╱            │
      │       ▪ vesper-home│             │    HOME ROW z2   LANES z1
   25 ┤  ▪ lake-home (22,27)             ▪ pond-jetty (43,24)
      │   (17,24)  ╲       │            ╱      ~~~~~~~~~~~
      │             ╲      │         ╱      ~~~ THE POND ~~~  (46,26)
      │              ╲     │      ╱        ~~~~~~~~~~~~~~~
      │               ╲  ╔═╧════╗╱
   20 ┤     ▪ inn (27,18)║ ✦ THE ║  ▪ well (29,24)
      │                  ║ HEART ║  ▪ notice-board (34.5,19.5)
      │   FESTIVAL SQUARE║ LIGHT ║  ▪ item-shop (37,19)
      │             z1.5 ╚═══╤═══╝    (32,22)
   15 ┤                      │  the road curls up the rise
      │  ▪ orchard (20,12)   │      — the square reveals LATE
      │        ╲             │
   10 ┤          ▪ waystone (27,9)
      │  ENTRANCE z0         │
    5 ┤              ╔═══════╧═══════╗
      │              ║ THE VILLAGE   ║  road-gate (30,4)
      │              ║     ARCH      ║  → exit: valley-road-south
    0 ┤              ╚═══════════════╝     to the OVERWORLD
      └────┬────┬────┬────┬────┬────┬────┬────┬────┬────  x
          15   20   25   30   35   40   45   50
```

**Read it as three moves.**

1. **The spine runs south to north and it climbs.** Arrive at the arch (z 0), pass the
   waystone, take the road that *curls* up the rise (the map's own waypoints at
   `(28.5,13)` and `(30.8,17.5)`) and step out onto the square at z 1.5. North of the
   square the lane keeps climbing past the tithe barn to the gate court at z 2.5 and
   the Sigil Gate at z 2.7. The map's curl is doing real work: **the square reveals
   late**, which is exactly the arrival the shipped `entrance/main.png` stages.
2. **Two lanes hang off the square, one each side.** West and *up*, Home Row — where
   the cast lives, ending at the hilltop bench with the whole village in view. East and
   *down*, the pond lane to the jetty and the washline green. Both are quiet; both end
   somewhere worth standing. That is the FF9 move: the plaza is the junction, and
   everything else is *a place you go to*, not a corridor you pass along.
3. **The town closes a loop.** `washline-green__gate-court` is the map's own back path:
   square → pond → green → gate court → barn → square is a real circuit. A town whose
   only topology is a line teaches the player nothing about where they are.

**Lake's round, on this plan**, and it is why the map reads as a village rather than a
diagram: plaza (the source) → home lane west, a lamp at each door → back across the
plaza → pond lane east, the jetty lamp last, and the pond takes the whole thing back as
a reflection. `chapter1.js` counts exactly three lamps on festival night; the map has
exactly the doors to hang them on.

---

## 3. The districts, and the build order

| # | district | parcel | scene key | tonight |
|---|---|---|---|---|
| 1 | **Festival Square** | `p-square` | `emb-square` | **REAL BUILD** |
| 2 | Village Entrance | `p-entrance` | `emb-entrance` | blockout (owns the entry camera) |
| 3 | Pond Lane | `p-lane` | `emb-lane` | blockout |
| 4 | Home Row | `p-homerow` | `emb-homerow` | blockout |
| 5 | Gate Field | `p-gatefield` | `emb-gatefield` | blockout |

(Parcel scene keys are the map's own, unchanged. The two *new* keys this plan adds are
the town-level pair: `emb-walk` and `emb-cine`.)

**Why the square ships first** — four reasons, in order of weight:

1. It is the game's premise made of geometry. The Heartlight on its pedestal is the
   thing Chapter One takes away.
2. Every Chapter One beat above the pact happens on it: the arrival, the Kindling Hour,
   the Hush, the naming, the send-off. The rest of the town is where people live; this
   is where the story happens.
3. It is the hardest thing to retrofit. A plaza's cameras, its lamp-ring, its stall
   layout and its building fronts are one composition; building it last means building
   it against four neighbours' constraints instead of its own intent.
4. It has the strongest reference. `public/assets/scenes/square/festival.png` is an
   accepted, shipped painting of this exact place — buildings, awnings, bunting, light.

### 3.1 Festival Square — the anatomy

Map members: `square-plaza` (area, extent 7, z 1.5), `heartlight`, `item-shop`, `inn`,
`notice-board`, `well`. Parcel bounds `[23,15,-0.5] .. [41,28,5]`. Everything below is
transcribed from the shipped painting and placed on the map's own coordinates.

| element | map pos | notes |
|---|---|---|
| **the Heartlight** | (32, 22, 1.5) | the ONE magical light. Low square stone pedestal, amber flame-crystal, faintly humming. Brightest thing in frame, always. Reverence in every shot. |
| the cobble apron | around the plinth | the reference paves the centre and leaves the through-road packed earth — keep that, the paving *is* the route language |
| **the inn** | (27, 18, 1.5) | the reference's grandest building: two storeys, half-timbered over a stone base, wide door up stone steps. `emb-inn-int` hook. |
| **the item shop** | (37, 19, 1.5) | village general store — preserves, twine, lamp oil. Open front, awning, trays. `emb-item-int` hook. |
| the notice board | (34.5, 19.5, 1.5) | *"EMBERWAKE TONIGHT — bring a memory worth keeping. And a chair. We are short of chairs."* |
| the well | (29, 24, 1.5) | north side, low stone ring, bucket frame |
| market stalls | ringing the plaza | four: green, blue, red-and-white awnings; buns, pumpkins, preserves |
| **lampposts** | three around the ring | ordinary wrought iron, lit **from** the Heartlight. `chapter1.js` names exactly two in the square + one on the lane. |
| bunting | post-to-post, eave-to-eave | with small hanging lanterns, per the reference |
| autumn trees | closing the west and north corners | reds and oranges with **greens mixed in** (look canon) |
| pumpkins, haybales, barrels, handcart | huddled into **touching groups** at building feet | never scattered singletons (`docs/SCENE-LAYOUT.md`) |

**Naming canon — exactly Dellhollow's, because the runtime keys behaviour off the
prefix and it is not negotiable:** `walk_` walkable surface · `bar_` collider that is
never a floor · `veg_` foliage dressing · `water_` water · `lm_` blockout massing
(non-solid, replaced as districts land) · `emb_sq_*` this district's art · `KEYSQ_*` its
lights.

---

## 4. Camera grammar

Six shots, one per parcel plus a split of the north lane, chosen against seam-canon §8
*before* any geometry existed. Every camera owns ≥10 m of route and its own junction;
every landmark and all eighteen edges have exactly one owner.

| id | name | owns (landmarks) | owns (edges) | route m | why it is a shot |
|---|---|---|---|---|---|
| **arch** *(entry)* | The Village Arch | road-gate, waystone, orchard | `road-gate__waystone`, `waystone__orchard`, `waystone__square-plaza@0..0.45` | ~19.7 | The arrival. From inside the village looking back south through the arch — orchard rows framing, valley haze beyond. The road runs *away* from camera so the arch reads as a threshold you came through. |
| **square** | Festival Square | square-plaza, heartlight, item-shop, inn, notice-board, well | `waystone__square-plaza@0.45..1`, `square-plaza__{item-shop,inn,notice-board,well}` | ~27.0 | The postcard of home. Heartlight centre-frame, shop and inn flanking, bunting overhead. |
| **pondlane** | Pond Lane | pond, pond-jetty, washline-green | `square-plaza__pond-jetty`, `pond-jetty__washline-green` | ~17.7 | Low along the shore at dusk: jetty silhouette, the Heartlight's glow mirrored in the water. |
| **homerow** | Home Row | vesper-home, lake-home, elder-house, home-lane-end | `square-plaza__vesper-home`, `vesper-home__{lake-home,elder-house}`, `elder-house__home-lane-end` | ~27.5 | Up the home lane, the village falling away behind; ends on the bench with the whole valley in view. Lake's round, first leg. |
| **northlane** *(transit)* | The North Lane | barn | `square-plaza__barn`, `barn__gate-court` | ~18.0 | The walled climb between the square and the old edge of the village; the tithe barn is its landmark and its turn. |
| **gatefield** | The Sigil Gate | gate-court, sigil-gate, forest-trailhead | `gate-court__sigil-gate`, `gate-court__forest-trailhead`, `washline-green__gate-court` | ~19.0 | The court facing the sealed gate, trailhead stile right — Ch. 1's set-piece stage, and the only unwarm frame in the town. |

**Rules held, and how:**

- **One plaza, one camera.** The square is not split. `quay-east` owned 5.8 m of route
  and two meshes inside its neighbour's own pad, and produced a user complaint inside
  an hour of live play (§3). A tighter shot on the same floor is a zoom, not a cut.
- **Every shot owns its own junction.** `square` owns the plaza *and* the heads of all
  four departing roads, so no seam has to sit inside a junction (§8). The loop stairs
  taught this by needing two seams inside seven metres.
- **The one mid-edge split is on the rise**, `waystone__square-plaza` at t≈0.45 — a
  climb, which is an articulation, not open floor (§4). This is the FF move of the
  camera changing as you walk on. **RATIFIED 2026-07-31**, and it is also the answer to
  the validation panel's one real complaint: the `p-entrance` / `p-square` gutter has
  travel implied and no parcel covering it. Splitting the approach edge between the two
  neighbouring shots closes it. It does **not** get a shot of its own: the middle 55 %
  of that edge is ~7.7 m and the no-sliver floor is 10 m (§3), so a third camera there
  would be `quay-east` again.
- **`frameExits: true` town-wide, from the first commit.** Dellhollow opts out because
  its backdrops predate the flag; Emberbrook has no such debt and never will.
- **Arrivals measured, not assumed.** Every cut's arrival must land ≥0.5 m past the
  band on the band's own normal (§1); `seam_test` measures it rather than trusting the
  solver. Overrides are authored only where the derived point is out of the receiving
  camera's sight, and `cutGeometry` rejects any override that is off-network, on a
  neighbour's ground, or inside the band it just crossed.
- **`thresholdPair` on nothing, tonight.** Emberbrook has no bridge and no stairwell in
  the current map. It is declared the day one appears, and on nothing else (§2).

---

## 5. The pipeline this town inherits

Unchanged from Dellhollow, and reused rather than reinvented — the tools were made
town-aware (a `--town` flag, defaulting to `dellhollow`) rather than forked:

```
emberbrook.cameras.json          authoring; the grade lives in defaults.exposure
  -> tools/cine_solve.mjs   --town emberbrook   -> emberbrook.cameras.solved.json
  -> tools/scenegraph_derive.mjs                -> the runtime cut edges
  -> tools/cine_bake.py     --town emberbrook   -> emb-cine/cameras/<id>/{bg,depth}.png
gates: seam_test (design) · seam_walk (shipped bytes) · cine_test · slice_test
       · plate_flat · master_walk_qa · geometry_audit · glTF export
perceptual: tools/nav_eval.mjs, judge PINNED gemini-3.6-flash
```

**The bake ray-cast is the only visibility oracle.** Offline occlusion models ran
pessimistic three times on Dellhollow. Look canon carried over: greens mixed into
autumn, varied house colours, flowing water with depth-faded banks, pops of colour
5–10 % per frame, and no unaudited sightline into the naked world (the t2 vista lesson
— constant fill plus far-plane depth).

---

## 6. Wiring

- **Scene keys** (added to the map tonight, mirroring Dellhollow's schema):
  `walkSceneKey: "emb-walk"` — the whole-town real-time bundle, the developer's explore
  view and the geometry every gate measures. `playSceneKey: "emb-cine"` — the town
  played as fixed pre-rendered shots, where the game routes players.
  `cameraFile: "townmap/emberbrook.cameras.json"`.
- **Overworld seam.** `ow-valley` ↔ `emb-cine` at `road-gate` (the map's own
  `valley-road-south` exit), mirroring Dellhollow's `dellhollow-valley-gate`. A second
  exit, `forest-north` at `forest-trailhead`, is authored and left unwired.
- **`public/play3d.html` is the coordinator's file and this lane does not touch it.**
  The WALKLOCK regex extension to `emb-*` and the scenegraph node wiring go to main as
  an exact diff, by message.
- **Forward hooks, deliberately left open:** `emb-inn-int`, `emb-item-int`,
  `emb-lake-int`, `emb-vesper-int`; the Sigil Gate's `state: sealed → open`; and the
  square's `festival → gray` state pair, which is the Hush and is the single most
  valuable thing this town's art pipeline will ever be asked to do.

---

## 7. FOR THE MORNING BOARD — where the map and the scripts disagree

These are **raised, not resolved.** The map is authority and nothing has been moved or
deleted; the geometry built tonight follows the map exactly. Each of these is a
one-line ruling for the user, and each is cheap to act on now and expensive later.

1. **`vesper-home` — "Vesper's home", Home Row.** `STORY.md` and `chapter1.js` are
   emphatic that Vesper is a *stranger* who walks in from the south road an hour before
   the Hush, and that this is precisely why the Hush cannot touch her: *"she arrived an
   hour ago and told Emberbrook's flame nothing."* Her birthplace is Ashfield (the
   Ch. 5 reveal). **Options:** (a) keep as authored and treat the house as canon-shift;
   (b) re-badge the same building — same position, same camera, same geometry — as a
   villager's cottage or the mapmaker's *lodging*; (c) leave it and decide at Ch. 10,
   when Emberbrook is revisited. Costs nothing today; the building exists either way.
2. **`item-shop` and `inn` — "The Ember Hearth".** `docs/MECHANICS.md` states: *"No
   shops, no chests, no pickups in Emberbrook — the festival runs on gifts, by LAW."*
   Money first appears in Dellhollow. **Options:** (a) keep the buildings and open them
   as *shops from Ch. 10 onward* (the return visit), closed and lamplit in Ch. 1 —
   which costs nothing and keeps the map intact; (b) accept an economy in Ch. 1.
   Separately: **"The Ember Hearth" is the only invented proper noun in the town** and
   the handover forbids inventing them; recommend either dropping the name or getting
   it ratified explicitly.
3. **`sigil-gate` — "The Sigil Gate".** `chapter1.js` calls it **the Old Gate**, in
   every line that names it; the *sigils* are the twin plates set in the ground before
   it. Recommend `name: "The Old Gate"`, id unchanged, plates as a separate prop.
   Zero build cost — it is a display string.
4. **`lake-home` at (17, 24), Home Row.** The shipped `lane/main.png` *is* Lake's
   cottage, with the pond, the lamp and the jetty in one frame, and `chapter1.js`'s
   cottage interior exits onto the **lane**. The map puts it on the opposite side of
   the village from the pond. **Options:** (a) keep as authored — Home Row is a fine
   home and the painting becomes a different cottage; (b) swap `lake-home` and a pond
   lane parcel member so the shipped painting stays literal. This is the only one of
   the four with a real geometry consequence, and it is still only a name swap between
   two houses that both get built.
5. **The town is called Ember*brook* and no water in the map is a brook.** The pond is
   authored; a stream is not. Not proposed as a change — noted because the name is
   asking a question the map does not answer, and the pond may simply be the answer.

---

## 8. What was built tonight, and what was not

Written in advance so the morning report has something to be checked against.
**As built, 2026-07-31:** the blockout and Festival Square are done and gated; the six
cameras are authored in this document and hand off to the bake lane rather than being
solved here, per the night's parallelism contract.

- **Built:** this plan; the map's schema completed (`walkSceneKey`/`playSceneKey`/
  `cameraFile`, water handling); a deterministic whole-town blockout with the real
  walk/collision network derived from the map's own landmarks and edges; **Festival
  Square as real geometry**; six cameras authored, solved, baked and gated;
  `routes.json` for nav-eval; a contact sheet.
- **Not built, and named so nobody has to rediscover it:** every district but the
  square is `lm_` massing. No NPCs. No interiors. No Hush state pair. The Sigil Gate
  does not open. The pond has a surface and no shader work. No perceptual score beyond
  a single N=5 sweep (the metric's own noise floor is ±0.20/shot at N=5 — see DAYLOG
  01:3x — so no per-shot claim is made from it).

Foundations over square metres. Dellhollow reached 70–80 % polish by having its
mistakes written down first; Emberbrook starts from the written-down version.
