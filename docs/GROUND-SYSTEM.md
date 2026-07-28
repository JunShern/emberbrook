# Ground System — final state (2026-07-28)

The iso world's ground layer, as settled through four director-reviewed
candidate rounds on `public/ground-picker.html`. This is the record of
what is live, how the machinery works, and which lessons are law.

## Architecture (public/js/iso/engine.js `bakeGround` + registry.js)

- **Two sampling modes, per material** (`sampling` on the ground def):
  - `organic` (grass, dirt, leaf, water, natural rock): per-cell jittered,
    feathered patches — never bands, never shows a repeat period.
  - `structured` (cobble, planks, deck): ONE world-anchored pattern space
    projected through the iso basis (`CanvasPattern.setTransform`) so
    courses run along the grid diagonals with 2:1 foreshortening — no
    per-cell jitter (jitter double-exposes structured patterns), no
    overlap. `patternScale` (cells per texture tile) renders structure at
    honest world size; it is A FREE KNOB — judge candidates on style, fix
    scale by arithmetic. (Cobble candidates shipped chainmail-tiny twice
    before this was actually applied: textures pack ~30 setts/tile →
    patternScale ≈ 11.5 for ~0.2 m setts.)
- **Boundary blending:** dithered organic blend (mode 1) is the default —
  wider feather + noise-dithered ragged edge instead of a rubber halo.
  Organic↔organic boundaries only.
- **Platform classes — structures are NOT blended:**
  - `deck` (wood pier): deck top slightly raised; auto fascia strips
    (plank sides) on south/east water-facing edges; stilt posts descending
    into water; water renders visibly UNDER the lip. Hard boundary.
  - `ledge` (constructed masonry): auto cut-stone face on south/east
    water-facing edges dropping to a defined waterline; no stilts, water
    does NOT continue underneath; no blend. Applied where CONSTRUCTED
    stone meets water (lockfive's chamber margins). Natural rock
    (`g-cliff`) keeps the soft organic edge. The constructed/natural
    distinction is a material property.
- **Skirt + fog:** ground extends 9 cells past scene bounds through the
  same bake path, rolling into dusk fog (elliptical + vertical bias);
  fills the old edge abyss including diagonal corners. Interiors (shell
  scenes) skip the skirt. `F` cycles off/skirt/skirt+fog.

## Live picks (all director-chosen from candidate rounds)

| material | pick | notes |
|---|---|---|
| forest floor + path | candidate **B** | soft-painterly, low-frequency; no baked objects |
| village grass | forest-B-derived, **unlifted** | luminance matched to forest floor exactly (0.399=0.399) — "the town is built on the same ground as the forest" |
| village dirt | tex-forestpath darkened −15% value | darker warm brown |
| village cobble | candidate **B** | warm muted setts, patternScale 11.5; director: harmony "not perfect yet" — open polish item |
| dellhollow water | candidate **B** | calm deep blue-green; quadrant seam healed (gradient-domain step removal) |
| dellhollow deck | candidate **C** finish, darkened ~10% value | small believable planks, paint-fleck charm |
| interior plank | candidate **C** | stylistic coherence with furniture; candidate A registered as `g-plank-bright` alternate (unused) |
| cliff | unchanged (natural, soft) | |

## Laws learned (bake these into any future ground work)

1. **No objects baked into ground textures** (roots/branches/props repeat
   as stamps and clash with the prop layer).
2. **Ground detail stays lower-frequency than props**; narrow value band;
   saturation that recedes rather than competes.
3. **Structured patterns need iso-aware, world-anchored sampling** —
   top-down textures draped on diamonds only work for organic noise.
4. **Structures don't blend** — decks and masonry get platform treatment
   with hard edges; only earth blends into earth.
5. **Ugliness is picked, not gated** (director): generate distinct
   candidate SETS, render on real demo maps WITH material boundaries,
   let the director choose per family. Rules catch geometry; eyes choose
   beauty. `ground-picker.html` is the standing venue.
6. **Teal/cyan-hue paint cannot survive the cyan-keyed pipeline** —
   water is white-on-dark-stone or blue-green, never teal (the keyer ate
   two assets before this was law).
7. **Settled captures only** (`fade.mode==='idle' && fade.a===0` + 1s):
   three agents shipped dark mid-fade screenshots; the assertion is
   mandatory in every capture script.

## Open items

- Village harmony polish (director: workable, not perfect) — iterate
  under playtesting.
- Water is still walkable (no water collision class) — engine item.
- Grass reads marginally more chromatic than the forest's olive litter at
  matched value (intrinsic to green); acceptable, revisit only if the
  director flags it in play.
