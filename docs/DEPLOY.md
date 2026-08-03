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

### MEASURED compressed total (2026-08-02, `--compress --plate-max 1920`)

Not a projection any more. `dist-c/BUILD.json`, the build that was play-tested:

    category      uncompressed  ->  shipped
    -------------------------------------------
    scenes            901.1 MB  ->  194.6 MB
    characters        322.8 MB  ->  101.5 MB
    music              22.5 MB  ->   21.4 MB
    other              11.6 MB  ->   11.0 MB
    code                2.9 MB  ->    3.6 MB
    -------------------------------------------
    TOTAL            1260.9 MB  ->  332.1 MB      (3.8x, 867 files)

**The projection above was wrong in both directions and the errors are worth keeping.**

  * DRACO was priced at 2.4% and the texture pass at 4.9x. The actual GLB pass ran
    **509 MB -> 20 MB, a 25x cut** — `ow-valley/scene.glb` went 30.2 MB to 0.1 MB. The
    per-bundle sample that produced 5.5x was not representative of a tree where most
    bundles are dominated by repeated 1K PBR maps.
  * The largest file is no longer a scene at all. It is now a **character rig**
    (`pip-v1.glb`, 14.1 MB) — the six cast GLBs total ~75 MB and the `--glb` pass never
    touches them, because it walks `assets/scenes` only. **That is the obvious next win**
    and it is deliberately NOT taken yet: those meshes are skinned and animated, and a
    geometry pass over a rig can corrupt joint indices in ways that only show up as a
    body folding inside-out mid-battle. Texture-only (no DRACO) is the low-risk half.

`--plate-max 1920` ships background plates at a 1080p TV's own pixels from the 2688x1536
masters. Depth and mask are never resized at any setting — see the note in the build script.

**2026-08-03 `--compress` (the shipped deploy): 514.0 MB, 373 files.** Bigger than the
332 MB above, because the branch grew art: `ow-valley` alone is 31.3 MB after the
overworld landscape pass. Plates went 492.1 MB → 49.3 MB; scene GLBs 522 MB → 262 MB.
Largest single file `emb-townwalk/scene.glb` at 66.9 MB — inside GitHub's 100 MB hard
limit, and the total is inside the ~1 GB soft cap, so no `--no-dev-scenes` was needed.
`emb-cine/scene.glb` is the one bundle the GLB pass does not shrink (12.4 → 12.4 MB):
it is walk geometry with vertex colours, not PBR maps, which is the same reason DRACO
was the wrong lever here.

## The encode cache — why a redeploy is cheap now

Before 2026-08-03 every build re-encoded **219 unchanged plates and 16 unchanged
scene GLBs**, ~28 minutes of work whose inputs had not moved. The cost that
mattered was never the wall clock: *a 28-minute deploy is a deploy you skip*, and
the live site drifts behind the branch. That drift was the defect.

    node tools/build-static.mjs --compress            # cache ON (default)
    node tools/build-static.mjs --compress --no-cache # re-encode everything
    node tools/build-static.mjs --cache-prune         # drop entries this build did not use
    EB_BUILD_CACHE=/elsewhere node tools/build-static.mjs …   # or --cache-dir

`.build-cache/` (gitignored) holds every encoded artifact under

    sha256(source bytes)  +  sha256(every parameter that changes the output)

**The second half is the whole design.** A cache keyed on the source file alone is
worse than no cache at all: the first time somebody changes a quality setting, a
codec or `--plate-max`, it serves the OLD bytes under the NEW settings, and the
failure is invisible until a human notices a plate looks wrong. So the recipe hash
is deliberately over-inclusive — it hashes the **encoder source itself**
(`WEBP_PY` verbatim, the `gltf-transform` argv), `--plate-max`, and the
Pillow/Python/`gltf-transform` versions. Over-keying costs a re-encode; under-keying
ships wrong art. Nobody has to remember to bump a version constant: editing the
encoder changes its hash.

Three things the cache is **not** allowed to do:

* **Fail a build.** A cache entry that is missing, empty, unreadable or has the
  wrong magic bytes (`RIFF` for a plate, `glTF` for a bundle) is demoted to a miss
  and re-encoded, loudly. Deleting `.build-cache/` at any moment costs a slow build
  and nothing else.
* **Skip a proof.** `depth.png` under `--webp-depth` is deliberately **uncached**:
  its encode carries the byte-exact round-trip gate, and that gate is the only
  reason a lossless depth plate may ship at all. Serving it from a cache would skip
  the proof to save work nobody runs by default.
* **Get in under a weaker check than a fresh encode.** A cached bundle GLB still
  faces the `glTF` magic gate on the way in *and* the geometry gate (POSITION +
  indices digested against `public/`) at the end of the build.

### MEASURED (2026-08-03, `--compress`, same machine, 373 files / 514.0 MB both times)

| | cold (`.build-cache` deleted) | warm |
|---|---:|---:|
| encode | 0 hit / **235 miss** | **235 hit** / 0 miss, 311.7 MB served |
| wall clock (`BUILD.json.seconds`) | **337.5 s** | **3.0 s** |

**112x.** The stage step is in both numbers and is now 0.6–1.6 s for 369 files.

`BUILD.json` now records `flags.plateMax`, a `cache` block and `seconds`, so any
deploy can be read back for what it was built with. `plateMax` was missing from
that record until 2026-08-03 — the one flag that changes what a plate *looks like*
could not be recovered from a shipped tree.

**The byte-identity proof matters more than the speed.** A fast build that produces
different bytes is a far worse bug than a slow one. The cold and warm trees were
digested file by file:

    A dist-c   : 374 files   digest 92eded5999c2402772c61b791e474c69a90432ae841f67f3acddd927393e243c
    B dist-warm: 374 files   digest e57b856fe3cddee8a3c3b9ea31e9997df034d9a4fc177c48beb5b9d49da2a0c8
    only in A: 0   only in B: 0   differing: 2
      BUILD.json                  OK — identical once built/seconds/cache is removed
      assets/story-manifest.json  OK — identical once `generated` is removed
    BYTE-IDENTICAL: 372/374; the 2 that differ are the two build clocks.

The two clocks are re-read as JSON and every other key compared, so "it is only a
timestamp" is proven rather than asserted. Note what this proof is: the warm tree's
bytes are the bytes a **full fresh encode** produced, because the cold run is what
populated the cache.

**The negative control is the other half**, and it is the one that guards the
failure mode that matters — serving yesterday's art under today's settings. With a
cache holding 219 entries for exactly these sources, a build run with
`--plate-max 1920` reported **zero hits** and went straight into a full re-encode.
The parameter is in the key, not decoration.

Also on 2026-08-03: the 1.26 GB staging copy uses `COPYFILE_FICLONE`, so on APFS it
is a copy-on-write clone — **369 files staged in 1.6 s**. It is a hint, not a mode;
a filesystem that cannot clone silently gets a real copy.

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

**With `--compress` (MEASURED 332 MB, largest file 14.1 MB), both hosts fit** — so the
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

**GitHub Pages — use the script.** `bash tools/deploy-ghpages.sh dist-c` does all of
the below, plus the pre-flight checks (100 MB per-file hard limit, the ~1 GB soft cap,
`.nojekyll`) and — the part you must not skip by hand — it **verifies the push landed**
by comparing `git ls-remote` against the local SHA, because this repo has been burned
by a push that died on GitHub's pack limit while reporting success. It makes `dist-c`
its own throwaway repo and force-pushes that, so the parent repo and every other lane's
uncommitted work are never touched. Then:

    node tools/static_verify.mjs --url https://junshern.github.io/emberbrook

which drives the **deployed** site, not a local tree. That is the only check that can
see a file which is fetched by committed code and is itself untracked — the
`lightrigs.json` failure, which works on the author's machine and 404s everywhere else.

By hand, if you must — Pages serves a branch, so `dist/` has to be *on* a branch. Keep
it out of `migration/3d-hybrid`:

    git checkout --orphan gh-pages && git rm -rf .
    cp -R dist/. . && touch .nojekyll        # .nojekyll or Pages eats lib/ and _-prefixed paths
    git add -A && git commit -m "deploy" && git push -u origin gh-pages
    # then: repo Settings -> Pages -> Source: gh-pages branch, / (root)

**Anywhere else** (Netlify, S3+CloudFront, a plain nginx): upload `dist/` as the document
root. No rewrite rules, no SPA fallback, no redirects. `/` is the launcher, `/play.html`
is the game.

## The build's own gates — and why they live in the build

**Every other gate in this repo reads the source tree.** That is the hole this class of
bug lives in: the build is the only place a path, a container or a byte can change, so
`public/` is always green while `dist/` is broken. Three checks now run at the end of
every build, over the finished artifact, in about a second:

| gate | what it asserts | the failure it was built from |
|---|---|---|
| **binary glTF** | every `.glb` starts with the `glTF` magic | `gltf-transform` picks its container from the extension: a temp file called `scene.glb.webp` made it write a **JSON** `.gltf` document under a name still ending `.glb`. `GLTFLoader` failed *silently* — no error, no scene graph, no walk meshes, no NPCs — and the game booted into an empty world |
| **scene geometry** | for every shipped bundle GLB, the POSITION bytes and the index bytes of **every primitive** digest identically to `public/` | the `--glb` pass **repacks the container**: measured on `emb-cine`, 4760 bufferViews become 2301, POSITION and NORMAL are interleaved at stride 24, and every accessor is re-indexed and re-offset. These GLBs are the **collision and walk geometry**; "the pass only touched textures" was a claim, not a fact |
| **reference integrity** | every local path a shipped page or a shipped JSON names resolves in the output — as itself, or through the plate/portrait `.webp` rewrite the runtime shim performs | the build changes paths (`bg.png` → `bg.webp`, pages pruned). Anything that names one and is not rewritten is a silent 404. It caught `story.html`'s link to `assets.html`, a dev page the build does not ship |

Run them alone against a tree you already have — a deploy you are about to upload, or
somebody else's build — without rebuilding:

    node tools/build-static.mjs --audit dist-c

Two calibration notes, both load-bearing:

* The reference gate only complains about a path that **resolves in `public/` and does
  not resolve in the build**. "A speaker with no art" and "a bundle with no
  `zones.json`" are documented, load-bearing absences; a gate that fires on those is a
  gate somebody switches off.
* The `.png` → `.webp` rule now has **one definition** (`SWAP_RE`/`SWAP_DENY` in
  `tools/build-static.mjs`). The converter picks its targets with it, the injected
  runtime shim is **serialised from it**, and the gate resolves with it. It used to be
  three hand-copied regexes, and a converter that converts what the shim cannot rewrite
  is a 404 nobody sees.

Both gates were negative-controlled: nudging one vertex by 1 cm inside a copied
`scene.glb` fails the geometry gate with both digests printed; an incomplete tree fails
the reference gate naming each missing plate.

### The shim cannot see a CSS background — so the build rewrites the builders

`--webp` injects a shim that hooks `HTMLImageElement.prototype.src` and `window.fetch`.
That is **every way the runtime loads a plate**. It is *not* every way it loads a
**portrait**: `EBUI.portrait()` (`ui_kit.js:664` — the party list and the 210 px bust in
the pause menu), `dialogue.js`'s framed-thumbnail fallback and `battle_turnbased`'s status
row all build `background-image:url("…/bust.png")` **into an HTML string**. A CSS `url()`
never touches an `HTMLImageElement` and never touches `fetch`, so the shim never sees it —
and the webp pass had already deleted the file it names.

Measured on the build of 2026-08-02: `assets/characters/vesper/bust.png` → **404 from the
built tree, 200 from `public/`**; `bust.webp` the exact mirror. **Every party portrait in
the pause menu was a blank frame in the deploy.** Nothing caught it: a CSS background that
404s logs nothing the console gate reads, breaks no gameplay, and every other gate reads
`public/`, where `bust.png` still exists.

`patchPortraitUrls()` fixes it **at the builder, not the loader** — six URL builders under
`assets/characters/` are rewritten to `.webp` in the *shipped copies*, so the `<img>` path
and the CSS path both name a file that exists and the shim becomes redundant for portraits
rather than load-bearing. `assets/battle/` and `assets/monsters/` are **not** converted and
keep their `.png`.

**Every entry must match exactly once or the build dies naming the line.** A lane that
edits a portrait path now breaks the build loudly instead of shipping blank frames — which
is the whole point, because the failure it replaces was invisible.

### What the compression pass was cleared of (measured 2026-08-02)

`--compress` was suspected of corrupting the world. It does not:

* all **16** shipped bundle GLBs digest identically to `public/` on POSITION + indices
* `node tools/walk_engine_gate.mjs --scene emb-cine` against the **built** tree
  (`--port 8129`) and against the **dev** server (`--port 3000`) return the same census
  cell for cell: **7451 standable cells, 1508.8 m², 0 lost, `SIM.bvh().fail = 0`**
* the NPC body plates survive the lossy re-encode as **chroma keys**: on
  `poppy/pose-front`, the keyed fraction moves 0.6142 → 0.6137

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
