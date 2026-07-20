# Chapter 2 expansion scene deltas — painted reality vs. addendum §(a)

The three expansion backdrops (`vista`, `stairs`, `cottage`) are final. Where the
paintings landed POIs/exits at different coordinates than
`docs/chapter2-expansion-script.md` §(a), THESE values override the doc; anything
not listed landed where the script said. `stairs` and `cottage` masks are baked
(`tools/bakemask.py`, authored `bake.json` in each scene dir) and BFS-verified on
the final mask.png: **stairs 10/10 check points in one component, cottage 7/7 in
one component** (all pairs connect; components=1 for both). `vista` is
cutscene-only and has NO mask by design (do not add it to the bake list).

Gate B numbers (final baked masks):
- `stairs`: coverage 44%, 1 component holding 100% of green, both exit mouths +
  door mouth green, 0 clearance carves needed (authored corridors covered all).
- `cottage`: coverage 14%, 1 component holding 100% of green, exit mouth green,
  4 clearance carves (wall-adjacent interacts; standard stage-3 behavior).
  14% is below the 25% floor by scene nature — an interior room in a full-canvas
  painting (exterior surround dominates). Same accepted deviation as lockfive
  (18%) and landing (22%).

## vista (cutscene-only — mapping for the `playValley` pan)

The painting reads left-to-right, south-to-north, as specced; positions drifted:

- **River enters from the TOP edge** at x≈250–420 (not upper-left (120,260)).
  Upper pool spans (240–470, 0–230).
- **Rafted queue**: barges at (325, 95) and (420, 150); **Hobb's pumpkin barge
  is clearly orange-loaded at (440, 170)** (stronger than the specced faint
  read — still reads easter-egg at cutscene zoom).
- **Lock chain**: steps down from the upper pool to the town's shoulder.
  Gate rows land at approx Lock 1 (500, 300), Lock 2 (610, 350),
  Lock 3 (650, 510), Lock 4 (790, 450), and **Lock 5 under a timber roof at
  (895, 530)** — the roofed-chamber requirement painted exactly.
- **Town**: near (south-west) wall houses stacked (120–560, 320–630) — NOT
  380–900; far wall quay + houses (420–1000, 30–320). Color rule holds: red /
  green / teal roofs and facades, teal-painted house ~(320, 465), lantern-string
  bead-lines along the streets at ~(250–336, 264–282) and ~(276–372, 390–414).
- **Stair-street seam**: legible as a pale stepped seam (560, 440) down to
  (670, 650) — closer to scene center than the specced (700,380)–(820,560).
- **Woodsmoke**: columns at ~(200, 120), (175, 300), (240, 310), (365, 340),
  (445, 60) — all leaning the same way (right).
- **Bunting / rope-bridge catenaries across the gorge**: (1010–1240, 320–390)
  and (1010–1210, 470–540) — on the right (north) half, not mid-gorge.
- **Flume hairline**: the scratch/ladder line in the right cliff runs
  (1190, 530) down to (1230, 600) — much lower-right than specced.
- **Tailwater + landing**: timber jetty at (1030, 650) in steaming water
  (950–1150, 600–700).
- **The river runs north off the TOP-RIGHT edge** (1150–1344, 0–250) into
  layered haze — not the right edge at 480–620. The end pan rest below accounts
  for this.
- **Foreground rim**: bottom-left rock + grass (0–672, 510–768), wheel-rut road
  curling out of frame (0–350, 640–768), the last moth at ~(330, 610).
- Gulls near the falls (~(745, 405)) and over the tailwater (~(1055, 535)).
  No figures anywhere. No text.

**Pan path (REPLACES the §(a) table — clamped to the painting, viewH-safe):**

| Order | Camera rect (`cam`) | What it frames |
|---|---|---|
| start | `{ x: 455, y: 265, viewH: 520 }` | river in from the top, queue + pumpkin barge, Locks 1–2 |
| mid | `{ x: 672, y: 400, viewH: 520 }` | the town both walls, lock stair, strings |
| end | `{ x: 854, y: 420, viewH: 560 }` | Lock 5 roof, bunting lines, flume line, jetty/tailwater, north haze top-right |

## stairs

Composition: top arch upper-center-RIGHT (not center); one big central flight;
plaza mid-left; cistern court lower-left; terraces right. All §(a) required
color content present (painted doors — boat-red (215,290), gate-green (855,460),
orange (925,190), teal (1040,235) and (1135,585), purple (1280,290); laundry
lines; striped awning; chalk hop-grid (880,650) and drawings; hanging goods;
bunting/laundry over the upper street; gulls).

- **Top exit (to descent)**: arch is at (740–880, 0–120). Zone
  `{ x: 700, y: 0, w: 180, h: 80 }` (was 560–800). Spawn arriving from descent:
  **(800, 150, 'down')** (was [672,120]). Top landing under the arch:
  (672, 110) → **(800, 140)**.
- **Bottom exit (to dellhollow)**: descending stair at (620–810, 690–768). Zone
  `{ x: 620, y: 700, w: 190, h: 68 }` (was 540–800). Spawn arriving from
  dellhollow: **(720, 680, 'up')**. The dellhollow-side spawn **(210, 110)
  is reused unchanged** (proven shipped value — not drifted).
- **Keepers' cottage door**: (880, 350) → **(985, 505)** — plain wood door with
  the carved lintel at (960–1030, 445–475) on the mid-right terrace. Exit zone
  `{ x: 940, y: 490, w: 90, h: 80 }`; door interact (870, 405) →
  **(985, 585)**, radius 75. Story marker (880, 300) → **(985, 470)**.
  Spawn stepping out of the cottage onto stairs: **(985, 610, 'down')**
  (was [880, 430]). Supper-exit player placements (§c run block):
  vesper (830,420) → **(940, 600)**, lake (895,435) → **(1020, 610)**.
- **Landings** (social floors, all masked generously): mid plaza (420, 300) →
  **(450, 320)**; lower-right landing (760, 470) → **(940, 650)**; quay gate
  (672, 690) → **(720, 720)**; plus the cistern court **(400, 640)**.
- **Sorrel's bread-window**: (350, 340) → **window at (285, 530)** (striped
  awning above, warm light, loaves). Sorrel's station behind the counter
  ~**(300, 555)**; player approach mouth **(400, 620)**.
- **Public cistern**: basin (500, 470) → **(455, 540)**; interact (520, 505) →
  **(520, 610)**, radius 70. Basin itself is a blockedRect.
- **Laundry lines**: overhead at (300–1000, 40–190); look-up interact
  (620, 320) → **(500, 330)** on the mid plaza, radius 70.
- **Gull rail**: (900, 520) → rail/fence at (800–950, 680–740), gulls painted
  there; interact (880, 560) → **(860, 650)**, radius 65.
- **Barrel-hoist**: (1010, 360) → **barrel + beam at (1130, 220)** on the right
  wall, chalk tallies + rude gull nearby; interact (990, 420) → **(1130, 310)**
  from the upper-right terrace, radius 70.
- **NPC stations** (suggested, walkable-verified): Sorrel (360,355) →
  **(300, 555)** (behind counter — give her a larger interaction radius, Poppy
  pattern); Old Creel (820,435) → **(940, 610)** on the landing-to-terrace
  steps; Nib (560,565) → **(800, 660)** by the gulls.
- **Lamps** (§(a) list is superseded by painted reality): two painted lamp-posts
  at **(297, 185)** and **(858, 200)**; suggested lantern-string glow points
  **(500, 120), (640, 105), (950, 80)** along the overhead lines. All no-id,
  engine glow, lit at night.
- Mask notes: the upper-right terrace ↔ mid-right terrace link is an authored
  corridor at x1080–1150 crossing a painted fence line (accepted corridor
  recipe; the alternative was no connection). The keeper-door face itself is
  walkable up to the wall base — players stop visually AT the door.

## cottage

Composition flipped/compressed vs sketch: hearth back-left, tool wall
back-center-right, dresser + window mid-right (not far right), curtained
sleeping nook far-right corner. Warmth/color spec landed: boat-color glazed
bowls on the dresser (teal/red/ochre), bright rag rugs, gate-green bread tin on
the hearth shelf, dried peppers, dusk window. Storytelling props all present
and bare-wood as specced.

- **Exit door (to stairs)**: arched front door at (385–470, 460–630). Zone
  `{ x: 390, y: 560, w: 130, h: 150 }` (was x180). Spawn arriving from stairs:
  **(490, 600, 'right')** (was [300, 560]).
- **Height-tally doorframe**: the tallies painted on the INNER doorway alcove
  (255–340, 280–460), marks at ~(233, 335) stopping below the lintel — not on
  the exit door. Door POI (250, 470) → **(300, 370)**; interact (270, 560) →
  **(310, 500)**, radius 75. The §c supper cam cut `{x:420,y:480,viewH:460}`
  still frames the marks — keep it.
- **Father's oilskin**: (340, 350) → **(295, 375)**, square on its peg inside
  the alcove; interact (340, 445) → **(340, 480)**, radius 70. The empty peg
  below reads faintly (peg rail at the coat's shoulder) — the §c system line
  carries it; nothing else depends on it.
- **Locked chart drawer**: dresser under the window at (770–895, 260–410),
  drawer face (1050, 430) → **(825, 330)**; interact (1035, 520) →
  **(830, 450)**, radius 75. No key painted anywhere (verified).
- **Eel-spears / winch-parts**: (900, 300) → **spears (700–800, 70–300), winch
  gears + chain (570–700, 220–340)**; interact (900, 400) → **(690, 380)**,
  radius 75.
- **Table + seats**: center (740, 520) → **(595, 545)**; interact (740, 590) →
  **(700, 610)**, radius 80. The pale NEW stool is at **(560, 600)** — clearly
  younger wood, as specced. **Deviation: the painting has THREE chairs + the
  stool (4 seats), not two + one.** The extra chair is small (reads
  child-sized). The §c interact text ("two chairs… and a third seat") still
  lands; do not stage anyone on the fourth seat. Supper placements (walkable,
  around the table blockedRects): vesper chair **(545, 470, 'right')**, lake
  chair **(680, 480, 'left')**, Maren THE STOOL **(560, 600, 'up')**.
- **Hearth**: (520, 380) → **stew-pot at (500, 330)**, fire lit; interact
  (540, 460) → **(520, 450)**, radius 75 — still the supper trigger.
- **Window**: over the dresser at (845–925, 145–290), gorge going dark. Night
  state = tint, per spec.
- **Odessa at the pot**: (560, 420) → **(520, 445, 'right')**. **Maren
  pre-supper**: (820, 540) → **(750, 600, 'left')**. **Mochi doorstep**:
  (300, 600) → **(460, 640, 'up')**. Checkpoint-4 player placements
  (620,590)/(700,600) → **(750, 620)/(820, 580)** (the doc values fall inside
  the table blockedRect).
- Bake center [650, 550]; blockedRects: table + upper chairs, lower seats
  (stool + small chair). The alcove floor and door threshold are authored
  corridors.

## Verification summary

- Cottage main.png: 4 rolls (cand1 rejected — oilskin coat missing; cand2
  rejected — no height-tallies, stool not readable as newer wood, stray chart
  on the table; cand3 rejected — coat missing again; cand4 = cand3 + additive
  coat/tally edit, ACCEPTED — all five storytelling props verified in-frame).
- maskraws: 1 roll each for stairs and cottage, both accepted first try.
- BFS (final mask.png, 4-connected, ±3-cell tolerance as in the baker):
  - stairs: top mouth (800,90), quay mouth (720,730), cottage-door mouth
    (985,585), Sorrel (400,620), cistern (520,610), laundry (500,330),
    gull rail (860,650), hoist (1130,310), Creel (870,450), Nib (640,660) —
    ALL in the single main component.
  - cottage: exit mouth (460,620), tallies (320,500), coat (340,480), hearth
    (520,450), table (700,610), toolwall (690,380), drawer (830,450) — ALL in
    the single main component.
- Composite overlays (mask over painting) checked by eye: walkability follows
  stairs/landings/floor; no leaks onto roofs, cliffs, water or drops.
- `public/js/bake-core.js` SCENES += 'stairs', 'cottage' (NOT vista);
  manifest rebuilt via `node tools/build-manifest.mjs`.
