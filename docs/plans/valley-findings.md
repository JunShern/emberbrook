# The Valley region — build findings

The first real overworld region (chapters 1-2), built from the user-ratified
geography hierarchy in style F2. Written here rather than into KITLIB_MANIFEST.md
because the manifest is being renumbered concurrently — the coordinator folds these
in and assigns numbers.

Pipeline: `tools/valley_map.py` (map -> analytic field + zone grid, pure numpy),
`tools/valley_layout.py` (the cheap taste-gate preview), `tools/valley_build.py`
(the Blender tile), `tools/valley_export.py`, `tools/valley_verify.py`,
`tools/valley_render.py`. Bundle: `public/assets/scenes/ow-valley/`.

---

## A. Map-change requests (topology is the coordinator's — nothing here was edited)

**A1. The road and the river are topologically inconsistent, and this is the one
that matters.** Emberbrook's road runs the river's RIGHT bank from `[72,138]` to
`[130,95]`; the Valley Gate approach runs its LEFT bank from `[160,75]` to
`[215,65]`. Between them is the parent spine's "second meander back west" (apex
`[138,82]`), a hairpin whose neck the road cuts across — so the road changes bank,
i.e. it crosses the river, while `region.crossings.list` is empty by ruling
("Dellhollow's dam crest is the only span"). No lateral nudge can fix a bank change.
Three ways out, all the coordinator's call:

1. add a crossing at ~`[142,87]` (the river is ~12.5u wide there — a bridge, not a
   ford);
2. move the road's first half onto the LEFT bank (it can join it around the river's
   HEAD at `[70,150]` without crossing anything — the left bank is continuous from
   there to Dellhollow's rim). Costs ~16u of lateral shift through the emberwood and
   moves the waystone;
3. re-route the road around the hairpin's outside and accept that it then arrives at
   the gorge's SOUTH-WEST rim, which contradicts `forests[south-bank].note`
   ("far bank — Ch3 territory, uncrossable this side of Dellhollow").

**Until then the build lays a low culverted causeway at the span** and flags it as
its one unauthorised object. `valley_map.CAUSEWAY = False` removes it, and the
clearance pass becomes a no-op the moment the map is fixed. The layout preview marks
it `UNLISTED CROSSING` in red.

**A2. The road's gorge-rim climb is laid on top of the channel.** Road points
`[190,68] [200,68] [208,66] [215,65]` sit 0.1-3.2u from the river centreline where
the parent spine says the river is 12-14u wide, so the "rim road" is inside the
water. Both ends of that run are on the LEFT bank, so it is a double crossing — an
authoring accident rather than a topology problem. The build pushes those stations to
the left bank at `hw + 1.6` (44 stations, max 9.6u). **Request: move road points
12-15 and the `dellhollow-valley-gate` portal ~6-9u north-east**, e.g. gate at
`[218,70]`. The build already puts the gate MARKER at the pushed endpoint, so the map
and the tile currently disagree by ~8u on where the portal is.

**A3. The plateau blob does not contain Emberbrook.** `elevation.plateau.blob`
`[[25,120],[95,185],[130,155],[70,100]]` puts the `[50,160]` anchor **12.3u outside**
its NW edge, although the anchor's own height is 26 = the plateau height and
world.json calls Emberbrook a "high forested plateau" town. Left alone, the town
becomes a separate 26u knoll with a dip behind it. The build unions the anchor's
impression disc into the plateau mask. **Request: extend the blob's NW edge past the
anchor** (e.g. `[18,132]` / `[86,196]`).

**A4. Two of the four floor control points stand inside the river's own channel.**
`[250,35]` is 1.1u from the centreline where the river is ~19u wide; `[200,70]` is
4.2u out. "Valley floor height 3" cannot mean the water surface at -1.6, so the
build reads them as *the height of the floor beside the channel* and calibrates a
downstream bank profile to hit them there. Residuals after calibration: `[110,130]`
+0.9, `[150,90]` +0.4, `[200,70]` +2.7, `[250,35]` +0.2. The `[200,70]` residual is
honest terrain relief (±2.5u rolling floor). **Request: move floor controls off the
channel, or document that they mean bank height.**

**A5. `forests` cover only ~9.6% of the tile at full density** (emberwood 3243u²,
valley-fringe 963u², south-bank ~1150u² of 56000u²). After the channel, crag and
slope guards, planted forest lands at 14.1% of cells — and 8% of that is a stand the
build DERIVED, not one the map authored (see A6). If the emberwood is meant to read
as the dense wood the fiction describes over more than the road corridor, the stamp
wants enlarging northward over the plateau.

**A6. `rim.west = "forestwall"` has no forest stamp behind it.** The build reads the
rim treatment directly and derives a wooded band for `x < 34` (105 trees). Flagged
because it is content derived from an adjective rather than from geometry.
**Request: either an explicit stamp, or a documented rule that a `forestwall` rim
plants itself.**

**A7. `zoneOverrides` has no settlement stamps.** F2 established that settled ground
is safe ground (the encounter table must not roll a wolf in the village green). The
build derives one `road` ellipse per `townAnchor` at `0.62 x impressionRadius`.
**Request: add them explicitly.** Note the consequence at Dellhollow: the anchor
`[220,60]` is 1.9u from the channel centreline, so most of its stamp is water and the
zone there stays `water` — correct (an authored stamp must never dry the river out),
but it means `SIM.zone` at the Dellhollow anchor returns `water`, not `road`.

**A8. `alongRoad: true` needs no stamp** — the derived road mask IS the road polyline
buffered to 1.9u, so that override is satisfied by construction. The build asserts it
rather than applying it. Worth saying so in the region file.

---

## B. Findings that generalise (craft, not this map)

**B1. THE MEDIAL-AXIS CREASE — the biggest single artifact of the whole build.**
Any quantity read off a river by NEAREST POINT (water level, bank profile, gorge
factor) is discontinuous along the river's medial axis, and the size of the jump is
the river's own fall between the two reaches that meet there. Referencing the ambient
land to a sharp `water_level(nearest_t)` drew **100u-long dead-straight false
escarpments down the medial axis of every meander**, ~8.5u tall, on both banks —
which the zone grid then faithfully classified as crag, and the planting then refused
to plant. Max interior slope fell from **3.77 to 0.47** when the reference field was
box-blurred (σ ≈ 10u) while the channel carve kept the sharp values (within its own
half-width the nearest reach is never ambiguous, so there is no crease to remove
there). Any region with meanders needs this.

**B2. Never clamp a distance field you then differentiate.**
`0.075 * np.minimum(dr, 45.0)` (round 1's valley-drain term, inherited) has a hard
gradient break exactly 45u from the channel; at region scale that is a 200u straight
ridge line the length of the valley on both banks. `3.4 * (1 - exp(-dr/26))` is the
same shape with no break.

**B3. A ridge with a straight foot and a constant crest is a WALL.** Both have to be
folded: the foot meanders (±11u) and the crest breathes (±26%), at wavelengths long
enough to read as landform from the vista ring and short enough to break the
silhouette from inside. Costs two `sin` terms per rim.

**B4. Carve the channel LAST, but carve it TWICE.** The wide bank profile (up to 20u
of lateral run inside a gorge) is what shapes the valley walls — but applied after
the works it dragged the Valley Gate's levelled apron 4u down into the notch, and
applied before them the road's rim climb hung in mid-air over the water. The answer
is two passes: the wide profile shapes the LAND, the works (road grade, settlement
shelves) are laid on it, and a second narrow pass at `hw + 1.8` guarantees the
CHANNEL. Works may then embank right to the waterline and none of them can fill it.

**B5. A mountain range is a CREST LINE, not a collection of shapes.** The vista ring
started as one cone per summit and every render came back with a picket fence of
tents. Rebuilt as continuous strips whose crest height is hashed per station, with
±0.45 steps of depth jitter, it reads as ranges. Two further traps: depth jitter at
±2.2 steps makes the crest zig-zag further in depth than it advances along the range,
and the "range" becomes a self-overlapping mass that fills the frame; and a
single-sided strip has no volume, so from a high camera you look into its hollow back
(it read as torn cardboard). Two faces meeting at the crest fixes it.

**B6. A vista ring needs a horizon APRON.** Without a low plate from the tile's cut
edge out past the far band, the gap between them is a hole straight to the world
background and the vista shot reads as a matte painting with its bottom torn off.

**B7. Impression buildings on steep ground need FOOTPRINT conforming, not centre
conforming.** A terrace pad placed at the terrain height of its centre cantilevers
off a gorge wall. Sample the pad's four corners, put its top at the lowest, and run
the retaining wall from there down to the ground beneath its outer edge. Same for
rock outcrops: place them at the minimum corner height and reject sites whose corner
spread exceeds ~1.7u, or they stick to cliff faces like barnacles.

**B8. Water depth has to scale with water width.** At 18-22u wide and 1.5u deep the
bright rock bed showed straight through 0.82-alpha water and the navigable reach read
as milk. `depth = 0.95 + 0.085 * width + 1.4 * gorge` fixed it. A river that the
story says is navigable has to *look* deep.

**B9. Segment big masonry.** One 2 x 15 x 3.4u block beside 1.6u houses reads as a
monolith, not as a lock. Six courses with hashed offsets cost the same and read as
built work.

**B10. Density thins the PLANTABLE ground, not the raw stamp.** Applying a stand's
density fraction to the whole stamp double-thins it, because the stamp has already
lost its channel, its crag and its steep ground: a 0.55-density fringe landed at
0.25. Take the noise percentile over the plantable subset.

**B11. The prototype's planting guards do not survive a change of scale.** F2's
`ALT > 1.0` (height above the local water) erased 87% of the valley-fringe stand,
because at region scale the valley floor is only 1-2u above its own river. Dry-bank
distance (`dr - halfwidth > 1.2`) is the guard that means what `ALT` was trying to
mean. Likewise F2's `slope > 0.85` cutoff left a bald band straight across the road
corridor, because the plateau skirt the emberwood grows on runs 0.5-0.9 — 1.28 is the
region's number.

**B12. The plateau skirt width is a planting decision, not a height decision.** A 14u
drop over a 9u skirt is 57°, which the zone grid calls crag and the planting refuses;
the emberwood then has a bare stripe exactly where the road corridor crosses it. 14u
of skirt (41°) is plantable and looks the same from the chase camera.

**B13. The road corridor is a property of the WOOD, not of the tile.** Keep-out from
the road centreline at 2.45u inside a stand (verge + half the 2u ribbon) and 5.5u in
open meadow: the trees crowd the road where there is a wood and stand back where
there is not. That is H's corridor lesson made local.

**B14. Region-scale distance fields need chunking.** The prototype built one
`(NX, NY, 601)` distance cube; at 280 x 200u that is 174 MB per array. Chunking the
nearest-point query over the centreline in blocks of 96 keeps it at `O(NX*NY)` and
costs nothing (the whole field builds in 0.14s).

**B15. Retargeting beats forking.** The entire F2 system set (zone grid, zone-driven
tessellation, crag treatment, tree constructions, procedural veg maps, PBR recipe,
terrain material pass, mooring basin, jetty, tar boat) runs on the region unmodified,
because it is all parameterised through `overworld_lib`'s module constants and river
functions. `valley_map.py` re-points those at map data and hands `overworld2_lib` a
basin *frame* at the Moorage landmark instead of a fork of `pool_frame`. Zero lines
of the prototype were edited.

**B16. A cheap map-derived preview pays for itself in one pass.** The numpy+PIL
layout preview (5s, no Blender) found the plateau/anchor mismatch (A3), the bald
emberwood band (B12) and the unlisted crossing (A1) before a single 3D build. Two
things make it legible: a hypsometric ramp *under* the zone tint (zone colour alone
reads as one green plain, and the descent is the thing being gated), and 4u/20u
contours widened where the ground is flat.

**B17. Don't name a 3D shot after the cheap preview.** `valley_layout.png` is the
committed taste-gate artifact; the EEVEE overview shot silently overwrote it once.
The 3D camera is now `overview`.

---

## C. Gate results

| gate | result |
|---|---|
| `tools/worldmap_validate.mjs` | **PASSED**, 0 warnings |
| zones.json RLE sanity (node, runtime decode) | **OK** — 160/160 rows, coverage matches declared, spawn cell = `road`, off-grid = `null` |
| GLB round-trip white materials | **0 white** (COLOR_0 on 19/19 meshes) |
| alphaMode MASK atlas survived as PNG | **OK** (finding 131) |
| `veg_` / `tree_` split (finding 137) | **OK** — `veg_field`, `veg_field_cards` non-standable; `tree_field_trunks` solid |
| QA zone overlay excluded from the GLB | **OK** |
| spawn pin lands on the walk network | **OK** — `walk_road` at the emberbrook-gate portal |
| walk-ribbon clearance | clean on road / green / dock / dockpath / dam crest; `walk_causeway` is deliberately buried in its own embankment |
| crag treatment survived (flat facets) | **OK** — 11735 flat / 39131 smooth |

## D. Open taste questions for the user

1. **The causeway.** Build it, bridge it, or re-route the road (A1)? It is currently
   the one object in the tile the map does not authorise.
2. **Is the emberwood dense enough?** It is as dense as the stamp allows (A5). The
   road reads as a corridor; the rest of the plateau does not read as forest.
3. **The gate is 8u from where the map puts it** (A2). Move the map, or accept the
   build's position as the refinement?
4. **GLB weight.** 37.1 MB (17.0 MB of it shared texture) — 0.66 MB per 1000 square
   units against F2's 2.08, so the region is 3x more efficient per unit area and a
   second region adds geometry only. Dropping the normal maps would save ~7 MB and
   change the F2 look. Worth it?
5. **The Heartlight** is a single standing light on a plinth at the village centre.
   World canon says Heartlights are rare and magical; is one glowing node the right
   overworld impression of the Heartlight town, or should it be larger/architectural?
6. **Dellhollow's weir flight is three stations.** Enough to say "locks", or does the
   impression need the full flight the town model has?
