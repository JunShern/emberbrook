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

---

# E. Foliage, rock and meadow QUALITY (2026-07-30)

The user judged the forests, ground and rock against a modern FF-remake reference
and asked for its TEXTURE QUALITY — not its lighting, not its post, not its scale.
The ruling that reframed the problem, and it is the whole pass: **at this world's
scale a whole FOREST occupies the screen area that one of the reference's BUSHES
occupies, so a forest mass must be built the way a bush is built.** Lobed core,
dense shell of leaf-cluster cards, real material response.

New files, all off the shared pipeline: `tools/foliage_atlas.py` (the atlas),
`tools/bushlang.py` (the construction), `tools/valley_veg.py` (the region's
forest, rock and meadow), `tools/foliage_lineup.py` + `tools/foliage_stand.py`
(the two taste gates). Artifacts: `docs/qa/overworld/foliage_lineup{,_aerial,
_density}.png`, `foliage_stand{,_aerial}.png`, `valley_leafcard_atlas.png`.

## E1. Three forests failed on the ATLAS, and all three had the same atlas

Iteration 1 was a blanket, 2 was packed crown domes, 3 was a painted texture over
a gentle swell. Three different geometries — and the user said "flakes" to all
three, because every one of them was textured by the SAME primitive:
`_stamp_wrap_cell`, a rotated ellipse with a radial shade ramp, stamped up to 2400
times a cell. An ellipse with a radial ramp has

* **no leaf silhouette** — a leaf is pointed, asymmetric, serrated;
* **no shared light** — each blob is lit from its own centre outward, so a cluster
  of them has no top and no underside, only a field of little spheres;
* **no occlusion** — later stamps overwrite earlier ones with no depth test, so
  there are no layers, and with no layers there is no interior;
* **no normal that means anything** — the normal map came from a HEIGHT field
  built out of the same ellipses, so it described bumps, not leaves.

Changing the geometry over that texture could not have worked, and three passes
were spent proving it. **When a look fails three times on three different
geometries, the failure is in the material.**

## E2. Draw the atlas by RENDERING it, not by stamping it

`foliage_atlas.py` renders a small 3-D scene per atlas cell in numpy: a dome of
leaf SPRAYS, each spray a rachis carrying alternating lanceolate blades with a
midrib fold, every blade rasterised through a **Z-BUFFER** that writes colour and
a real **per-pixel normal** in the same test. All of them are then lit by ONE key
+ one sky term + a depth-driven AO + a translucency term, so a clump has a lit
top, a dark interior and a backlit rim. 16 cells: 8 big clumps, 8 edge fuzz.
~35 s for the whole set, and it is a one-off asset (finding 148).

Three corrections, each found by looking at the sheet at 200%:

* **Counting leaves is not a way to fill a disc.** 430 small blades over the
  interior covered 28% of it, so the middle of every big card was SKY — and a card
  you can see the sky through in its middle is a flake whatever its rim looks
  like. The mass needs a FLOOR: an opaque noise-broken backdrop at 0.80 of the
  silhouette, with the rim still made of individual blades so it never reads as a
  painted disc.
* **A buried blade must not go black.** At AO floor 0.20 over a deep green the
  interior blades landed at 0.01, and a black leaf-shaped hole reads as damage,
  not as shade. Floor 0.40, and lift the deep green. On the OPEN (fuzz) cards the
  interior mat has to use SHADE greens rather than interior greens, because an
  open card's inner blades are seen against the sky.
* **Premultiply before downsampling.** A supersampled alpha edge averaged against
  transparent black gives every leaf a dark fringe, and a dark fringe on every
  leaf edge is precisely what reads as "flakes" at distance.

## E3. A CARD SEEN FLAT IS A FLAKE — the clamp, not the rule

The brief says shell the cards "along the surface normal", and that cannot be
taken literally: at the top of a dome the surface normal is straight up, so a card
aligned to it lies horizontally, and the 35° follow camera sees it face-on with
nothing behind it — a sticker. `bushlang.BETA_MAX` clamps how far a card may lie
back from vertical (56° + 13° jitter), so a mass's crown is shelled with steeply
pitched cards that still show their silhouette. This is round-2 style H's lesson
and `tree_c`'s fringe restriction, generalised into one clamp instead of a rule
about where cards are allowed.

## E4. The shell has to STAND OUT of the core, or the core keeps the silhouette

With each card's base sitting on the core surface, half of every card was inside
the thing it was supposed to hide, and the mass read as **mossy boulders with
leaves along the top**. Two changes fixed it: the card straddles its sample point
instead of standing on it (so a shell over a vertical flank covers the flank, not
just its upper half), and its centre stands `CARD_OUT` = 0.16 of its size outside
the surface. The shell then owns the volume and the core is demoted to what it
should be: the dark interior nothing can see through.

## E5. COLOR_0 on a shell must be RELATIVE, and only the GLB said so

The shell's vertex colour was computed from the core's ABSOLUTE shade. Darkening
the core — which region masses want, so their gaps read as canopy shadow — pushed
every card onto the clamp floor. The round trip reported `COLOR_0 min == max ==
0.521` over 28 000 cards: the shell AO was doing nothing AND was multiplying the
whole atlas by a flat half. That was the murkiness that survived three rounds of
re-lighting the atlas, and no amount of looking at the render would have named it.
Normalising against the core's own brightest vertex fixes it. **Generalises: a
gate that reports the DISTRIBUTION of an attribute (min/max/mean) catches bugs a
gate that reports its presence cannot.** (Related: 218, 219.)

## E6. Two indexing traps of the same shape, one hour apart

`base = len(self.V)` where `self.V` is a list of per-lobe vertex ARRAYS: the face
offset became the lobe count, so every lobe's triangles welded onto the first few
vertices. It renders as a fan of huge flat plates and radiating spikes, which
looks exactly like a sculpt bug — two rounds of harmonic tuning were aimed at it
before an edge-length histogram (max 6.6u on a 0.3u mesh) named it in one line.
The identical trap sat in the card emitter (`b0 = len(self.cV) * 4`) and was
invisible only because `shell()` happened to be called once. **An accumulator that
batches into a list needs an explicit element counter; `len()` of the batch list
is a different number that is right exactly once.**

## E7. A SUM OF SINUSOIDS IS A LATTICE

The meadow's patch-scale hue mottle took three attempts. Separable `sin(x)sin(y)`
at 1-3 cycles came back as diagonal **corduroy** marching across the whole
meadow. Four DIAGONAL waves at coprime-ish frequencies came back as a quilted
**cross-hatch** — a handful of pure tones summed is still periodic, it just has a
bigger cell, and the eye finds it instantly because it is the only straight thing
in a landscape. The fix is tiling NOISE, and the cheap exact way to get it is an
inverse FFT of a random-phase spectrum: every coefficient is a whole number of
cycles across the image so it wraps by construction, and random phases leave no
cell at all. Any low-frequency variation added to a texture that TILES needs this.

Two smaller meadow notes: the two-source blend must be weighted toward the green
photo (`sparse_grass` is mostly soil, and an even crossfade read as dry ground
with grass in it), and a wildflower petal must be BLENDED at ~0.78 rather than
written — a petal painted at full opacity over a photograph is a sticker.

## E8. Rock: re-weight the crag SPECTRALLY, and measure that you did

The crag treatment's three octaves of ridged noise sit at wavelengths of 6.5, 2.4
and 1.0 world units, so there is no form larger than 6.5u anywhere in it and at
region scale a cliff reads as heaped gravel. `valley_veg.patch_crag` moves them to
19u / 7u / 2.3u and adds BEDDING TERRACES — a sawtooth in the underlying height
that pulls ground toward the top of its own bed, with a slow dip so the beds are
not spirit-level flat (level beds read as contour lines, i.e. as a map).

The measurement is the finding. Over the region's 20.1% crag cells the naive
version took the displacement's sd from 0.426 to **0.608** and its peak from 1.85
to **2.57u** — a taller crag, which is a fresh clearance risk for every walk
ribbon beside one and is not what the pass was for. `AMP_TRIM = 0.70` restores the
amplitude exactly (sd 0.426, peak 1.80) and leaves only the change that was
wanted: the share of relief surviving a 7.5u blur — the share that reads as
LANDFORM — goes **0.68 -> 0.83**, and mean gradients get **27% gentler**. A
one-line read-only probe against the built field proved this without a build.

Material: `dark_rock_02` (Poly Haven, CC0) — the only rock face in their library
whose photograph already contains bedding. `cliff_side` is fetched as the warm
variant. Origins in `tools/textures/POLYHAVEN_SOURCES.md`. Rock samples are
FLAT-shaded: a smooth-shaded rock reads as a river-worn pebble however good its
texture is.

## E9. Cost, measured before the pipeline was touched

A synthetic 662 u² stand costs 70 lobes, 2457 core tris after a 56% interior cull,
and 2095 cards at DENSITY 1.0 — **3.16 cards per u² of footprint**. Extrapolated,
~9000 u² of canopy stand is ~28k cards + ~33k core tris = **~6.9 MB of geometry**,
plus **~2.2 MB** of new texture (atlas PNG 1.22, atlas normal 0.42, core tile
0.25 + 0.33). Rock and meadow are roughly neutral (they replace existing slots).
Predicted GLB ~37.5 MB against 28.4, i.e. a bundle around 41 MB — inside the 45 MB
line, with the ~9 MB of known levers still unspent.

Two things made that affordable. **Bigger cards, darker core:** a density sweep at
1.4 / 0.9 / 0.55 showed 0.55 bare, and cards of 1.95-3.05u over a darker core
bought 1.4's read at 1.0 (a saving of 2.7 MB). **No TANGENT attribute:** the
exporter emits none for a normal-mapped material, so the normal maps cost zero
geometry bytes — which had been the main budget worry about shipping them.

## E10. Open taste knobs (all in one block per file)

* `valley_veg.DENSITY` (1.0) — cards per u² of visible core. The line-up's
  `foliage_lineup_density.png` stacks 1.5 / 3.2 / 6.5 on individual bushes at
  full resolution with 1/2/3 ticks.
* `foliage_atlas.AUTUMN_RATIO` (0.048) — at 0.075 and full chroma the strays read
  as a berry crop from the follow camera; they are dulled toward warm grey now.
* `valley_veg.BIG` / `FUZZ` — card size. Bigger is cheaper and flatter.
* `valley_veg.CRAG_STRATA` (0.62) / `CRAG_BED` (2.9u) — bedding amplitude and
  thickness. `AMP_TRIM` keeps the total honest.
* `bushlang.BETA_MAX` (56°) — how far a card may lie back. Raising it flattens
  crowns toward the old flake failure.

## E11. Integrated into ow-valley (2026-07-30, after the geography session)

Rebased onto the current `valley_build.py` (canyon shelf, mesh-true ribbon conform,
three canopy stands). The whole diff there is FIVE lines plus the retirement of the
old `build_canopy`: `import valley_veg as VV`, `VV.patch_veg_maps(veg_maps)`,
`VV.patch_terrain()`, the `VV.build_canopy(...)` call, and `VV.patch_green(made)` +
`VV.stretch_rock_uv(made)` after the material pass. Every knob is a named module
constant — one block per file, so a morning taste change is a knob turn:

* `foliage_atlas.py` — `AUTUMN_RATIO`, `PALE_RATIO`, `AO_FLOOR`, `R_BIG`/`R_FUZZ`,
  `GRID`/`CELL`/`SS`/`N_BIG`, and the `PASSES`/`INTERIOR`/`BACKDROP` tables.
* `bushlang.py` — `BETA_MAX`/`BETA_JIT` (the flake clamp), `SIL_BIAS`, `CARD_OUT`,
  `CARD_SINK`, `CARD_LO`, `CORE_UV`, `FUZZ_LOW`.
* `valley_veg.py` — `LOBE_SP`, `LOBE_R`, `LOBE_R_EDGE`, `LOBE_H`, `DENSITY`, `BIG`,
  `FUZZ`, `FUZZ_FRAC`, `CORE_DEEP`/`CORE_LIFT`, `ROCK_SET`, `CRAG_STRATA`,
  `CRAG_BED`, `AMP_TRIM`, `ROCK_UV`, `MEADOW_FLOWERS`.

`bash tools/valley_rebuild.sh` green on the first integrated run and on all three
since. Gates: **0 white primitives of 24**, both alphaMode MASK materials keep a
**PNG** baseColor (`ow_valley_bushcard`, `ow_f2_leaf`), COLOR_0 on 24/24 meshes,
zones/spawn/overrides unchanged, and **walk-ribbon clearance clean on every ribbon
with 0 pierced verts** — the pre-existing `walk_dockpath` +0.053u puncture cleared,
which is the mesh-true conform plus this pass's 27% gentler crag gradients (E8).

Built: whisperwood 638 lobes / 13 536 cards, farwall-crown 150 / 4 874,
pocket-grove 26 / 826. Region totals 167 859 tris (was 123 624) and **GLB 33.03 MB
against 28.52** — a **+4.5 MB** delta for the whole pass, well inside the 45 MB
line, with the ~9 MB of levers unspent. It came in under the ~6.9 MB predicted
(E9) because two swaps paid for themselves: `patch_green` re-points the village
green at the derived meadow and drops `leafy_grass` diff+normal (**-2.67 MB**), and
`patch_veg_maps` gives the specimen lobes the bush core's tile, dropping the two
`veg3_canopy` images.

Two more faults the region caught that neither taste gate could:

* **A DE-TILED ALBEDO DOES NOT FIX A REPEAT COUNT.** `dark_rock_02` at the
  terrain's 6.2u UV run tiles a 40u canyon wall seven times, and the shelf shot
  came back as a brick-stamped clay cliff. Crossfading two rock photos on tiling
  noise (`crag_maps`, the E7 trick) fixed the near ground and did nothing for the
  wall, because there the problem is not the composition, it is that the eye can
  COUNT the repeats. `stretch_rock_uv` gives only the rock-slot faces a 2.6x
  coarser run (~16u, two and a half repeats up the wall) and the wall reads as
  sandstone bedding. The scale discontinuity at the slot boundary is free: that
  boundary is already a change of texture.
* **A RIM SPRAY IS SCALED BY THE CARD.** The atlas threw its rim sprays 1.6x
  further than its interior ones — right at line-up scale, and at region scale a
  3u card made that a metre-long spray, so the shelf camera read the mass as green
  palm fronds. 1.22x, with card size cut to 1.55-2.45u and density raised to 1.25
  to keep the coverage, reads as foliage. **An atlas tuned at one card size is not
  tuned at another**; the frond length is the term that does not scale.

**Open for the user, beyond the E10 knobs:** the grove greens read bright and limey
against the warm rock in `valley_record_midvalley.png` — that is `foliage_atlas`'s
`G_LIT`/`G_SUN` and one atlas regeneration away. And a note for the geography
session, not this pass: `valley_record_gorge.png` shows Dellhollow houses standing
proud of the gorge wall on the upper left (finding B7's footprint-conforming, on
the new canyon geometry).
