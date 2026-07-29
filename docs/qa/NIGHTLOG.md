## 04:12 — Boatyard probe v11: ACCEPTED (quality gate passed)
Verdict: pilot bar met in raw render — dusk lantern bloom, vegetation (creepers = strongest),
color separation (oxblood chandlery vs green lofts + bunting), foreground work-life, hazed far
depth with far-side silhouettes. Settles the core pipeline bet: kitlib + recipes suffice; no
image-gen needed to reach presentation quality.
Coordinator ruling on the roofs question: deck-height cameras don't owe hero roof planes —
that belongs to high-camera scenes (Weave/Lockhead). Camera stays.
Carry-forwards for all detail work: KITLIB_MANIFEST items 1-17 (esp. bounded-fog-only, world
ramp lower-hemisphere trap, out-of-frame shadow casters, world_to_camera_view placement grids).
## 04:38 — Cottage interior v9: REJECTED, iterating to v10/v11
Right bones (hearth pool, green-dresser palette, warm/cool split at the river door) but: tie
beams cut the frame as black bars; upper half murky (FF9 = dim but readable); empty stage
between hearth and table. Fresh agent dispatched: beams raised/slimmed/uplit, fire 1.5x +
readability fill, mid-floor life (rug bridge, firewood, kettle arm, Mochi's basket), limewash
plaster, floorboard variation. Item-shop interior still building in parallel.
## 05:15 — Item shop v5: ACCEPTED (the shop archetype)
Shelf density, painted red/green counter, lantern pools, hanging dried fish — instantly FF9.
Two notes folded into wave 3: replace strand-nets with folded hanks; +1 stop counter key.
Dispatched: shops agent (item v6 fixes + skin refactor to data tables + weapon/armor variants,
with the dark-metal-readability warning) and inn common-room agent (wave 2a). Cookhouse (2b)
queued behind cottage v10 to cap concurrent Blender at 3. Agents running: cottage v10, shops, inn.
## 05:58 — PLAYABILITY MILESTONE: full-town grand tour 41/41 legs
Player-like walker (with human-style corrective recovery) traversed EVERY landmark end-to-end.
The path here (~2h of empirical iteration, each fix committed to data/generator so it's durable):
- wall test: walk_-only collide needs vertical-extent walls (low+high span), not any-graze
- flat features must never overhang steep ones: stairs trim outside area rims AND threshold pads
- flights must not run along/through corridors, buildings, or each other: gate stair re-sided,
  quay flights re-laid along the cliff to the deck's free north rim, moorage switchback rerouted
  east of the huts, cottage descent re-aimed, deep-stairs leg-1 relaxed (46deg post-stretch)
- hairpin switchbacks need wide amplitude so crossing legs clear vertically
- bridge takeoff swung gorge-ward off the switchback corridor
- rails exist visually (bar_) but are excluded from collision
- experimental network-collision mode (?net=town) kept behind a flag; raycast is primary
Morning validator wishlist: per-LEG slope check; corridor/flight proximity lint; flat-over-steep
overhang lint. All fixes are in map data + generator, so every future regeneration inherits them.
## 06:15 — Interior verdicts (art gate)
- cottage-int v11: ACCEPTED. Transformed from v9 — hearth pool + Mochi asleep beside it, toys,
  laid supper table, cool dusk through glazed doors vs warm room. The supper scene.
- inn-int v11: ACCEPTED w/ notes (hearth glow deserves more presence; beam stubs want warm
  uplight). LOCKS: DELAYED board, abandoned card hand, key rack, luggage — story complete.
- weapon-int v3: ACCEPTED w/ note (forge nook ember glow weak). Grindstone + polearm corner sell it.
- armor-int v3: ACCEPTED w/ note (hero harness stand deserves a spot). Dark-metal readability fix works.
- item-int v6: accepted earlier (archetype); nets + counter-key fixes reported done.
Score: 5/6 interiors at bar. Cookhouse agent (final) dispatched 06:12.
## 07:00 — Cookhouse v8: ACCEPTED — ALL SIX INTERIORS AT BAR
Bread oven glow + hearth two-height warmth, hatch + menu board, eel barrel. Notes: dining half
density, bottom-right corner lift. Exported playable (del-cookhouse-int) + hub.
## 07:06 — emberbrook.map.json drafted (town #2 in the graph system)
20 landmarks, 18 edges (all curved earth roads/paths — flat village, plan-primary), 5 draft
parcels + 4 implied interiors (item, inn, Vesper's and Lake's homes). The Heartlight encoded as
the magical centerpiece per canon (kind: heartlight). Two loops. Validator: zero errors first
pass — the tooling is town-agnostic. ALL draft-flagged for the user's morning redline; NPC
names/residents are placeholders pending chapter1.js cross-check.
## 08:05 — Boatyard district v3: playability PROVEN, art below bar, v4 iterating
The architecture headline: the first fully-DETAILED exterior preserves the town's walk meshes
byte-identically (agent QA: 0.0 vertex delta, 909/909 down-ray hits, corridors clear, headroom
clear) and browser-verified playable through the finished art (slipway->overlook, ->winch-foot,
->shed/kettle all OK). Detail passes cannot break walking — the contract holds end-to-end.
Agent also caught the p-boatyard draft camera facing 180deg wrong (yaw 170 = downstream);
adopted its correction (yaw -12) into the map. Art verdict on v3: below probe_v11 bar — blown
lock-house window, Lock Four reads white-concrete not black stone, amber-monochrome, timber-soup
values, shingle seams. v4 agent dispatched with the punch list.
## 08:55 — Boatyard v10: ACCEPTED with notes (first detailed exterior COMPLETE + playable)
Measured fixes: dam now black-stone + dark timber gates w/ iron banding (the 'concrete' was
whitewater sheets + a gloss floor reflecting sky); lock-house window de-clipped (emission 90->
6.8-10.5 w/ sill gradient); warm/cool split +0.011 -> +0.113; shingle 'seams' were moss skipping
course risers (normal-Z mask) — fixed; median luma 0.571 -> 0.479. Walk contract re-verified
after re-export (14/14 byte-preserved, 909/909 rays, QA PASSED). Notes for the user gate:
mid-ground timber values still uniform-ish; lantern bloom pools shy of probe_v11; frame denser
than the probe's open sky (honest trade, not faked with exposure). Interiors polish agent
(inn/weapon/armor/cookhouse notes) still running.
## 09:35 — Notes-polish complete: all four rooms (inn v12, weapon v4, armor v4, cookhouse v9)
Every note closed with measured diffs (weapon's 'dim' forge was 93%-clipped white — now 27%;
armor harness gets dais + spot rake; inn hearth grew 26% hot area without clipping; cookhouse
corner tiles lifted 5-13 -> 25-46). Bundles re-exported; spot-checked del-inn-int + del-armor-int
still playable. NIGHT QUEUE FULLY DRAINED — remaining work is the user's taste gates.
