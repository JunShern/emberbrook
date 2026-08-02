# DEPLOY — putting Emberbrook online

The game needs **no server at runtime**. Input is the Gamepad API and the keyboard,
the save is `localStorage`, and the two-player phone-controller path was dropped
(SINGLE-PLAYER FOR THE PROTOTYPE, user ruling 2026-08-02). `server.js` is a *dev*
server; nothing in the shipped client talks to it.

    node tools/build-static.mjs        # -> dist/, a static site
    node tools/static_verify.mjs       # serves dist off python3 -m http.server and plays it

`dist/` is gitignored. It is a build artefact — never commit it.

---

## What the build replaces

`server.js` does four things the game depended on. The build does all four at build time:

| server.js | dist |
|---|---|
| `GET /play.html` → sends `public/play3d.html` | `dist/play.html` is a **real file** (byte copy of `play3d.html`) |
| `GET /story.html` + `/assets/story-manifest.json` → rebuild the manifest per request | the manifest is **built once** by the build script and shipped |
| `express.static('public')` | `dist` *is* public, by inclusion |
| `express.static('docs')`, `POST /dev/save|promote|rebake`, `GET /join`, `GET /qr` | **not shipped** (dev-only, plus the dropped phone-controller path) |

**Nothing in the shipped client calls a `/dev/*` endpoint.** The three `/dev/*` posts
are used only by `public/assets.html` and `public/bake-square.html`, and `/qr` only by
`public/join-legacy.html` — all three are dev pages that the build does not include.
`play3d.html` and its modules make no request that a plain file server cannot answer.

## Inclusion, not exclusion

The build never copies `public/` and then deletes. Every file in `dist` is there
because something named it:

- **pages** — `index.html` (with the review-tool links pruned to what ships),
  `play3d.html`, `play.html`, `story.html`
- **code** — the `<script src>` list read out of `play3d.html` itself, plus
  `js/battle_stage3d.js` (which `battle_turnbased.js` loads at runtime), `lib/`, and
  every `public/game/*.json`
- **world data** — `world/scenegraph.json`, `world/world.json`, `world/regions/`, and
  the `townmap/<town>.map.json` + `.routes.json` the runtime fetches (town names come
  from the scenegraph's own `origin` strings)
- **scene bundles** — the union of *(a)* `public/game/scenes.js`'s `SCENE_REGISTRY`,
  *(b)* every `world/scenegraph.json` node, *(c)* every `game/story.json` beat's scene.
  `scenes.js` is **evaluated at build time**, never hardcoded here, and `SCENE_ARCHIVE`
  is optional — it has since been deleted and the build did not notice.
- **characters** — the cast is the union of every speaker in `dialogue.json` and
  `story.json`, every id in `npcs.json` and `growth.json`, and every key in
  `cutins.json`. For each, only the names the runtime builds:
  `bust.png`, `expr-*.png`, `cutin.png`, `cutin-*.png`. Rigs are claimed one at a time
  from `play3d.html`'s `MODELS`, `battle_stage3d.js`'s models table (primary URL only)
  and `npcs.json`'s `body.src` — so `studio/`, `candidates/`, `turnaround*/`,
  superseded busts and retired rigs are simply never named.
- **audio / battle / monsters** — from `music.json`, `encounters.json`'s
  `battleBackdrop`, and `monsters.json`'s ids.

Why it matters: an orphan bundle nobody references can never silently add 200 MB to a
deploy, and nobody has to remember to exclude it.

`dist/game/scenes.js` is **regenerated** from the filtered registry rather than copied,
which is what makes `--no-dev-scenes` honest.

## Measured size (build of 2026-08-02, no compression)

| category | size | files |
|---|---:|---:|
| scene bundles (16) | 859.4 MB | 116 |
| characters (73 in the cast) | 307.9 MB | 185 |
| music | 21.4 MB | 8 |
| code + data | 2.8 MB | 43 |
| battle plates, monsters | 11.0 MB | 17 |
| **TOTAL** | **1.17 GB** | **369** |

Largest single files — this is the number a host's per-file cap is measured against:

    87.2 MB  assets/scenes/emb-townwalk/scene.glb
    49.5 MB  assets/scenes/townwalk/scene.glb
    49.4 MB  assets/scenes/del-cine/scene.glb
    41.1 MB  assets/scenes/del-inn-int/scene.glb
    39.9 MB  assets/scenes/del-cookhouse-int/scene.glb

The two biggest bundles are the two **developer** free-roam scenes:
`emb-townwalk` (95.3 MB) and `townwalk` (54.8 MB), 150 MB of the total. They are cards
in the registry's "Developer tools (not part of the game)" group, and
`node tools/build-static.mjs --no-dev-scenes` drops them **and** their launcher cards:
**≈1.03 GB**.

`dist/BUILD.json` carries the full per-scene table for whichever build you ran.

### What claiming by name rather than by directory saved

`background.png` — the pre-tonemap plate the bakers write — sits in every bundle and
**nothing** in `public/js` or `play3d.html` ever fetches it. 75.6 MB across 16 bundles.
A `cp -R` of each bundle would have shipped all of it. The build instead claims the
seven names the runtime reads (`meta.json`, `stylized.png`, `depth.json`, `depth.png`,
`cine.json`, `scene.glb`, `zones.json`) plus, for a cinematic bundle, the per-camera
plates **named by that bundle's own `cine.json`** (`c.art.bg` / `c.art.depth`) — so the
plate paths come out of the data, not out of a guess about the directory layout.

## What the 1.17 GB actually is

| | size |
|---|---:|
| scene GLBs (16) | 508.9 MB |
| camera plates `bg.png` | 177.0 MB |
| character portraits (bust / cut-in / expr) | 228.7 MB |
| `stylized.png` (thumbnails + scene backdrops) | 86.4 MB |
| camera **`depth.png`** | 87.1 MB |
| character rigs (`.glb`) | 78.5 MB |
| music | 21.4 MB |

## Compression (present, OFF by default)

Off by default because the art lanes are still moving assets; compressing a moving
target is wasted work. Turn it on for the deploy build.

    node tools/build-static.mjs --fetch-draco     # once: vendor the DRACO decoder
    node tools/build-static.mjs --compress        # = --webp --glb

### `--glb` — and why DRACO alone is the wrong tool here

Measured 2026-08-02 on `emb-bakery-int/scene.glb` (18.19 MB), with `gltf-transform`:

| pass | result |
|---|---|
| DRACO alone | 17.76 MB — **2.4%** |
| texture → WebP alone | 3.70 MB — **4.9×** |
| texture → WebP, then DRACO | 3.28 MB — **5.5×** |

`gltf-transform inspect` says why: a scene GLB is almost entirely 1024×1024 baked PBR
maps, three per material (diffuse / normal / roughness). **These bundles are not
geometry-bound**, so the expected "5–10× from DRACO" does not happen. The texture pass
is the lever and DRACO is the last 12%; `--glb` runs both. three r128's `GLTFLoader`
already declares `EXT_TEXTURE_WEBP`, so the texture half needs no loader wiring at all —
only the DRACO half needs the vendored decoder.

Character rigs are deliberately **not** in this pass: they are a live art lane's output
and skinned geometry is the one case where DRACO has a quality argument against it.

### `--webp` — plates and portraits

Re-encodes the background plates (`bg/background/stylized/main/festival/gray/open`.png)
and every `assets/characters/**.png` portrait at q88, then injects a shim that rewrites
exactly those `.png` requests to `.webp`. Measured on `emb-cine/woodroad/bg.png`:
**6.7 MB → 0.7 MB**.

### depth.png stays lossless — and here is the proof it has to

`depth.png` is not a picture. It is rgb24-viewz-encoded depth and the runtime reads exact
pixel values for occlusion; a lossy re-encode corrupts occlusion in ways that read as
gameplay bugs, not as compression artefacts. Measured on `emb-cine/woodroad/depth.png`:

    lossless WebP  2.3 MB -> 1.0 MB   decoded RGB bytes identical to the PNG: TRUE
    lossy q88      same plate          3068 of 3106 sampled bytes DIFFER

So `--webp` **never touches** `depth.png`, `mask.png` or `maskraw.png` — they stay PNG,
and the shim's rewrite rule has them on an explicit deny list. `--webp-depth` will convert
them, but only as **lossless** WebP and only after decoding both files back to RGB and
comparing the bytes; a single mismatch aborts the build rather than shipping the plate.

### Projected compressed total

Applying the measured per-file ratios above to the category table (a **projection** from
measured ratios, not a measured build — `--compress` on the full tree is a ~20-minute run
and the art is still moving):

    scene GLBs      508.9 MB  ->  ~93 MB   (5.5x, measured on one bundle)
    camera bg.png   177.0 MB  ->  ~19 MB   (9.5x, measured on one plate)
    portraits       228.7 MB  ->  ~25 MB
    stylized.png     86.4 MB  ->   ~9 MB
    depth.png        87.1 MB  ->   87 MB   (unchanged; ~38 MB with --webp-depth)
    character rigs   78.5 MB  ->   78 MB   (not in the pass)
    music            21.4 MB  ->   21 MB
    ------------------------------------
    TOTAL          1202.5 MB  -> ~330 MB

and the largest single file falls from 87.2 MB to roughly 16 MB.
**Re-measure before you deploy** — `dist/BUILD.json` records what you actually got.

## Picking a host

The build is plain files. Any static host works — the acceptance test deliberately uses
`python3 -m http.server`, with no rewrite rules, so nothing depends on host routing.

| | GitHub Pages | Cloudflare Pages |
|---|---|---|
| size cap | **1 GB soft** | no practical cap |
| per-file cap | 100 MB (git's own) | **25 MiB** |
| bandwidth | 100 GB/month soft | **unlimited, free** |
| files per deploy | — | 20,000 (we ship 369) |

**Uncompressed (1.17 GB), neither host takes it:**

- GitHub Pages is over the 1 GB soft cap. `--no-dev-scenes` gets it to ≈1.03 GB — still
  marginally over.
- Cloudflare Pages rejects five files over its 25 MiB per-file limit: `emb-townwalk`
  (87.2 MB), `townwalk` (49.5), `del-cine` (49.4), `del-inn-int` (41.1) and
  `del-cookhouse-int` (39.9) `scene.glb`.

**With `--compress` (projected ~330 MB, largest file ~16 MB), both hosts fit** — so the
choice comes down to bandwidth. A fresh playthrough pulls a few hundred MB; on GitHub
Pages' 100 GB/month that is a few hundred players before the soft cap is an argument.

**Recommendation: Cloudflare Pages, with `--compress`.** Free unlimited bandwidth is the
thing that actually matters for a game shipping this much art, the deploy is one
`wrangler` command with nothing committed to the repo, and the compression work is needed
for GitHub Pages anyway — so it is not a Cloudflare-specific tax. Railway would also
work, but you would be paying for a server the game does not need.

If you would rather ship *today* without waiting on a compression pass: GitHub Pages with
`--no-dev-scenes` at ≈1.03 GB is a soft cap, not a hard one, and will very likely serve.
It is the fastest path to a URL; it is not the one to leave running.

## Deploying, once you have picked

Run the build, verify it, then upload `dist/`.

    node tools/build-static.mjs --no-dev-scenes --compress
    node tools/static_verify.mjs          # must be ALL GREEN before you upload

**Cloudflare Pages** (direct upload, no repo, nothing committed):

    npx wrangler pages project create emberbrook     # once
    npx wrangler pages deploy dist --project-name=emberbrook

**GitHub Pages** — Pages serves a branch, so `dist/` has to be *on* a branch. Keep it out
of `migration/3d-hybrid`:

    git checkout --orphan gh-pages && git rm -rf .
    cp -R dist/. . && touch .nojekyll        # .nojekyll or Pages eats lib/ and _-prefixed paths
    git add -A && git commit -m "deploy" && git push -u origin gh-pages
    # then: repo Settings -> Pages -> Source: gh-pages branch, / (root)

**Anywhere else** (Netlify, S3+CloudFront, a plain nginx): upload `dist/` as the document
root. No rewrite rules, no SPA fallback, no redirects. `/` is the launcher, `/play.html`
is the game.

## The acceptance test

`node tools/static_verify.mjs` is the receipt. It serves `dist` with
`python3 -m http.server` — no routes, no rewrites, no express — and drives a real Chrome
through: the launcher renders its cards and every review link resolves; a real click on
NEW GAME lands in `emb-cine`/`woodroad`; the body walks; a door edge swaps into an
interior and back out; the menu opens on real party data; a battle starts; save and a
cold reload from `at` alone land in the same scene and shot. Throughout, it collects
**every** `Network.loadingFailed`, every 4xx/5xx, and every console error, and fails on
any of them — a 404 on one texture is the classic static-build failure and no other gate
in this repo would see it, because they all read the source tree, where the file exists.
It writes a screenshot next to `dist/` for a human to look at.
