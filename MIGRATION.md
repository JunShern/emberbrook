# Emberbrook → 3D FF-Hybrid migration

Living plan + progress log for re-architecting the renderer from painted-2D backdrops to
the **pre-rendered-3D "FF-hybrid"** system (see the prototype in `../rpg-3d/` and its
`docs/TARGET_SYSTEM.md`). Working on branch `migration/3d-hybrid`; `main` (fully pushed to
`origin`) is the restore point. No back-compat: deprecated art/code is deleted **per scene
as it's migrated** (never wholesale up front — that would leave the game broken mid-flight).

---

## Guiding principle
Replace **how the world is drawn**, preserve **everything else**. The engine is cleanly
seamed: keep the entity model, collision, story/cutscene glue, exits, HUD, and
display-authoritative multiplayer; swap only the inside of the render seam.

## The four architecture decisions
1. **Orthographic pre-render.** The camera pans/zooms within the backdrop to frame both
   couch players. A perspective pre-render can't pan without parallax error; an ortho one
   pans as a pure 2D translation, and real-time 3D characters composite correctly through a
   matching ortho camera. → preserves `Field.updateCamera`, adds true depth occlusion.
2. **Geometry-derived walkmask.** Bake the 336×192 `mask.png` from the Blender geometry
   (raycast) instead of flood-painting. → `Field.walkable`, movement, exits, `navGate` all
   unchanged; the mask stays "collision authored separately, simpler than the art."
3. **WebGL world layer + existing 2D HUD.** Replace the *body* of `Field.draw` with a
   Three.js layer (stylized bg + invisible depth geometry + characters). Keep
   `Field._lastView` / `Field.worldToScreen` exactly → the whole 2D HUD (dialog, markers,
   prompts, name tags, choice cards) is untouched.
4. **Pluggable characters** bound to the existing entity contract
   (`{char,x,y,dir,moving,animT,h,tint,hidden,alpha,lightCarrier}`): each character is
   either a **3D model** (Rodin→Mixamo) or an **HD-2D billboard** (existing sprite sheet),
   decided per character. Both occlude via the depth buffer.

## What a migrated scene is (the bundle)
Per scene folder `public/assets/scenes/<key>/`:
| File | Source | Role |
|---|---|---|
| `stylized.png` (+ per state) | Blender ortho render → nano-banana | shipped background |
| `scene.glb` | Blender glTF (invisible/depth-only at runtime) | occlusion + collision-source |
| `mask.png` | raycast bake from `scene.glb` | 336×768→336×192 `Field.walkable` grid |
| `scene-cam.json` | Blender export | ortho affine: backdrop-px ↔ 3D ground (place entities) |
Exits / lamps / plates / spawns stay authored in **backdrop pixels** in the chapter file —
unchanged. States become either re-renders or the cheap tint-grade we already have.

## Seam mapping (old → new)
| Current (2D) | New (3D FF-hybrid) |
|---|---|
| `Field.draw` paints backdrop PNG + y-sorts sprites | Three.js: draw `stylized.png`, depth-write `scene.glb`, render characters with GPU z-test |
| occlusion = y-sort / (unused) occluders | GPU depth buffer (real per-pixel) |
| `Field.walkable` ← flood-painted `mask.png` | `Field.walkable` ← **geometry-baked** `mask.png` (same format) |
| sprite from sheet (`sprites2.js`) | 3D mesh **or** billboard, per entity |
| `viewH/charH` in backdrop px, perspective-free 2D cam | same values drive an **ortho** Three camera pan/zoom |
| states = duplicate PNG + tint | re-render per state, or keep tint-grade |

## Coordinate reconciliation
World stays **backdrop pixels** (1344×768, y = depth). The ortho render fixes an affine
`backdrop-px (x,y) ↔ 3D ground point`; exported in `scene-cam.json`. Runtime places each
entity's mesh/billboard at that ground point; the ortho Three camera uses the same pan/zoom
as `Field.updateCamera`. So entities keep their existing `x,y`, exits/spawns keep their
coords, and nothing in movement/story needs reprojection.

## Per-scene migration recipe (mechanical once tooling is in)
1. Model/blockout the scene in Blender (kit builders); set the **ortho** camera to frame
   the scene's 1344×768.
2. Render `background.png` (transparent) + export `scene.glb` (+ affine) atomically.
3. `genart.mjs` → `stylized.png` (shared style prompt for cohesion).
4. Raycast-bake `mask.png` (336×192) from the geometry; run `navGate` to accept.
5. Point the chapter scene def at the new bundle; keep exits/lamps/spawns.
6. Delete the scene's old painted PNG(s) once it passes.

---

## Scene inventory & priority (16 implemented)
Hubs first (highest play value), then spokes, cutscene-only last.
| Scene | Chapter | Type | States | Priority | Status |
|---|---|---|---|---|---|
| dellhollow | 2 | hub | day/night | **P0 pilot** | in progress (prototype exists) |
| square | 1 | hub | festival/gray | P1 | todo |
| lanternstead | 3 | hub | 4 states | P1 | todo |
| stairs | 2 | spoke | day/night | P2 | todo |
| lockfive | 2 | spoke | dim/night | P2 | todo |
| cottage | 2 | interior | dusk/night | P2 | todo |
| forest,entrance,interior,lane | 1 | spokes | 1 | P2 | todo |
| road, lanternstead-int | 3 | spoke/interior | — | P3 | todo |
| descent | 2 | spoke | 1 | P3 | todo |
| vista, landing | 2 | cutscene-only (no mask) | — | P3 | todo |

~8–10 more locations (Ch4–10) are outline-only — new builds, not migrations.

## Phasing
- **Phase A (now):** renderer integration + Dellhollow pilot playable in the real engine.
- **Phase B:** migrate the two other hubs (square, lanternstead) → proves variety + states.
- **Phase C:** batch the spokes/interiors using the settled recipe + kit.
- **Phase D:** cutscene-only scenes, character roster (3D vs HD-2D per cast member), cleanup
  (delete the old 2D art pipeline `tools/*` + `iso/` POC once nothing references them).

## Open decisions for review
- **Characters:** HD-2D (reuse 2D cast) vs 3D (Rodin→Mixamo per character) vs mix. Prototyped both.
- **States:** re-render per lighting state (best) vs keep cheap tint-grade (fast). Likely mix.
- **Renderer home:** Three.js layer beside the 2D canvas (chosen) — revisit if perf/complexity bites.

---

## PROGRESS LOG (autonomous session)
- [x] Verified `main` pushed to origin (safe); created `migration/3d-hybrid` branch.
- [x] Wrote this plan + `../rpg-3d/docs/TARGET_SYSTEM.md`.
- [x] **Validated ortho pre-render** (decision #1) — dellhollow re-rendered orthographic; pans without parallax.
- [x] **Pilot scene bundle** `public/assets/scenes/dellhollow3d/`: `background.png`, `stylized.png`
      (nano-banana), `scene.glb` (347 meshes + ortho camera), `mask.png` (walkable=white, screen-space
      through the same ortho cam → drops into `Field.walkable`).
- [x] **Verified in the game repo**: `public/test3d.html` (+`public/lib/three.min.js`,`GLTFLoader.js`)
      loads the bundle with the GLB's ortho camera → painterly backdrop + invisible depth geometry +
      capsule with raycast collision + **correct depth occlusion**. This is the core of `render3d.js`.

### Verified: the whole FF-hybrid works in the target repo. Remaining = wire it into the live engine.

## NEXT (in-game integration — best done with your 2-player test setup)
1. **`public/js/render3d.js`** — promote `test3d.html`'s logic into a module:
   `Render3D.init(canvasEl, sceneBundle)`, `.setView({camX,camY,viewH})`, `.setEntities(list)`, `.frame()`.
   - Character per entity: HD-2D billboard (existing sheet) or 3D model, placed by **raycasting the
     entity's backdrop-px down the ortho camera to the visible ground** (handles the visual tiers while
     gameplay stays 2D on the mask).
2. **Hook `Field.draw`** (`field.js`) behind `Field.mode3d` (per-scene flag): when on, draw the WebGL
   world layer under the existing 2D canvas; keep `Field._lastView`/`worldToScreen` so the entire HUD
   is untouched. Old 2D scenes keep working during migration.
3. **Camera-pan alignment**: map `Field.updateCamera`'s `camX,camY,Z` to the ortho camera's frustum
   window so bg + geometry + HUD stay locked as it pans to frame both players. (Open item — the one
   piece test3d.html doesn't yet exercise; verify against a scene that scrolls.)
4. **Wire the pilot as a real scene**: point a `dellhollow3d` scene def at the bundle (states/exits can
   reuse dellhollow's), boot the game, verify 2 players + collision + exits + dialog + HUD.
5. **Characters**: drop vesper in (HD-2D sheet is proven in `../rpg-3d/web/play_hd2d.html`; Rodin-3D
   mesh is in `../rpg-3d/assets/vesper/` awaiting Mixamo rig).
6. Then batch the other scenes via the recipe; delete each scene's old 2D art as it's migrated.

## Files added this session (on `migration/3d-hybrid`)
- `MIGRATION.md` (this)
- `public/assets/scenes/dellhollow3d/{background,stylized,mask}.png`, `scene.glb`
- `public/test3d.html`, `public/lib/{three.min.js,GLTFLoader.js}`
