#!/usr/bin/env node
/* build-static.mjs — TURN THIS REPO INTO A STATIC SITE.
 *
 * WHY. The game needs no server at runtime: input is the Gamepad API + keyboard,
 * the save is localStorage, and the two-player phone-controller path was dropped
 * (SINGLE-PLAYER FOR THE PROTOTYPE, user ruling 2026-08-02). server.js is a DEV
 * server. This script replaces the four things it does that the game depends on:
 *
 *   server.js                                    -> dist
 *   ------------------------------------------   ---------------------------------
 *   GET /play.html  -> sends public/play3d.html   dist/play.html is a REAL file
 *                                                 (byte copy of play3d.html)
 *   GET /story.html + /assets/story-manifest.json dist ships a manifest BUILT ONCE
 *     -> storyGate rebuilds the manifest first    here, at build time
 *   express.static(public)                        dist IS public, by inclusion
 *   express.static(docs), POST /dev/*, /join,/qr  NOT SHIPPED (dev-only + the
 *                                                 dropped phone-controller path)
 *
 * INCLUSION, NOT EXCLUSION. Nothing is copied and then deleted. Every file in dist
 * is here because something named it: a <script src>, a data file, or the scene
 * registry. That is the whole point — an orphan bundle nobody references can never
 * silently add 200 MB to a deploy, and it does not need a lane to remember to
 * exclude it. The scene list is READ FROM public/game/scenes.js AT BUILD TIME
 * (SCENE_ARCHIVE is optional and may be gone), never hardcoded here.
 *
 * USAGE
 *   node tools/build-static.mjs                  # plain build (no compression)
 *   node tools/build-static.mjs --no-dev-scenes  # drop the "Developer tools" cards
 *   node tools/build-static.mjs --webp           # plates + portraits -> WebP (see below)
 *   node tools/build-static.mjs --glb            # scene GLBs: textures -> WebP, then DRACO
 *   node tools/build-static.mjs --compress       # --webp --glb
 *   node tools/build-static.mjs --fetch-draco    # once: vendor the DRACO decoder
 *   node tools/build-static.mjs --out /some/dir
 *   node tools/build-static.mjs --no-cache       # re-encode everything (see below)
 *   node tools/build-static.mjs --cache-prune    # drop cache entries this build did not use
 *
 * THE ENCODE CACHE (on by default, .build-cache/). Every encoded plate and scene
 * GLB is kept keyed by sha256(source) + sha256(every parameter that changes the
 * bytes) — the encoder script itself, --plate-max, the Pillow/gltf-transform
 * versions. A no-op rebuild copies them back instead of re-encoding, which is the
 * difference between a 28-minute deploy and a 1-minute one, and therefore the
 * difference between a site that tracks the branch and one that drifts behind it.
 * A cache entry that is missing, truncated or has the wrong magic bytes is
 * DEMOTED TO A MISS, never a build failure. See the block comment at CACHE.
 *
 * COMPRESSION IS OFF BY DEFAULT, on purpose: the art lanes are still moving the
 * assets, and compressing a moving target is wasted work. Turn it on for the
 * deploy build.
 *
 * *** depth.png IS NOT A PICTURE. *** It is rgb24-viewz-encoded DEPTH and the
 * runtime reads exact pixel values for occlusion; a lossy re-encode corrupts
 * occlusion in ways that read as gameplay bugs. --webp therefore NEVER touches
 * depth.png. `--webp-depth` will encode it LOSSLESSLY, and only after proving a
 * byte-exact decode round-trip on every single file — one mismatch aborts the
 * build. Same for mask.png / maskraw.png / any *depth* name.
 *
 * PROOF OF THE BUILD IS THE BUILD SERVED BY A DUMB STATIC SERVER AND PLAYED, not
 * this script exiting 0. See docs/DEPLOY.md.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync, readdirSync, rmSync, copyFileSync, renameSync, cpSync, openSync, readSync, closeSync, constants as FS } from 'fs';
const { COPYFILE_FICLONE } = FS;
import { join, dirname, relative, basename } from 'path';
import { execFileSync } from 'child_process';
import { createHash } from 'crypto';
import { createContext, runInContext } from 'vm';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const PUB = join(ROOT, 'public');

// ---- args ------------------------------------------------------------------
const argv = process.argv.slice(2);
const flag = (n) => argv.includes('--' + n);
const opt = (n, d) => { const i = argv.findIndex(a => a === '--' + n || a.startsWith('--' + n + '=')); if (i < 0) return d; const a = argv[i]; return a.includes('=') ? a.split('=').slice(1).join('=') : argv[i + 1]; };
const OUT = opt('out', join(ROOT, 'dist'));
const COMPRESS = flag('compress');
const WEBP = COMPRESS || flag('webp');
const WEBP_DEPTH = flag('webp-depth');
// --plate-max <px>: longest-edge cap for BACKGROUND plates in the web build. The
// masters stay 2688x1536; this ships smaller. 1920 = a 1080p TV's own pixels.
// Depth and mask are never resized at any setting — see the note in WEBP_PY.
const PLATE_MAX = (() => {
  const i = argv.indexOf('--plate-max');
  return i >= 0 ? parseInt(argv[i + 1], 10) || 0 : 0;
})();
// --glb: the GLB pass. MEASURED 2026-08-02 on emb-bakery-int/scene.glb (18.19 MB):
//   draco alone            -> 17.76 MB   (2.4%  — these bundles are NOT geometry-bound)
//   texture webp alone     ->  3.70 MB   (4.9x)
//   texture webp + draco   ->  3.28 MB   (5.5x)
// The brief's "5-10x from DRACO" is wrong for this art: `gltf-transform inspect`
// shows a scene GLB is mostly 1024x1024 baked PBR maps, three per material. The
// texture pass is the lever; draco is the last 12%. three r128's GLTFLoader already
// declares EXT_TEXTURE_WEBP, so the texture half needs no loader wiring at all.
const GLB = COMPRESS || flag('glb') || flag('draco');
const NO_DEV_SCENES = flag('no-dev-scenes');
const KEEP_STORY = !flag('no-story');
// --no-cache: encode everything from scratch. --cache-dir <p>: put it elsewhere.
// --cache-prune: after the build, drop cache entries this build did not use.
const NO_CACHE = flag('no-cache');
const CACHE_DIR = opt('cache-dir', process.env.EB_BUILD_CACHE || join(ROOT, '.build-cache'));
const CACHE_PRUNE = flag('cache-prune');

const log = (...a) => console.log(...a);
const warn = (...a) => console.warn('  ! ', ...a);
const die = (m) => { console.error('\nBUILD FAILED: ' + m + '\n'); process.exit(1); };
const t0 = Date.now();
const secs = () => ((Date.now() - t0) / 1000).toFixed(1) + 's';

// ---- THE ENCODE CACHE -------------------------------------------------------
// WHY. The build re-encoded 219 unchanged plates and 16 unchanged scene GLBs on
// EVERY run — ~28 minutes of work whose inputs had not moved. The cost is not the
// wall clock; it is that a 28-minute deploy is a deploy you skip, and the live
// site drifts behind the branch. That drift is the actual defect this fixes.
//
// THE KEY IS THE THING THAT MATTERS. A cache keyed on the SOURCE FILE ALONE is
// worse than no cache: the first time somebody changes a quality setting, a codec
// or --plate-max, it serves the OLD bytes under the NEW settings and the failure
// is invisible until a human notices a plate looks wrong. So the key is
//
//     sha256(source bytes)  +  sha256(every parameter that changes the output)
//
// and the "recipe" half is deliberately over-inclusive: it hashes the ENCODER
// SOURCE ITSELF (WEBP_PY, the gltf-transform argv) plus the tool versions plus
// --plate-max. Over-keying costs a re-encode. Under-keying ships wrong art.
// Anything a lane edits in the encoder changes the recipe hash automatically —
// nobody has to remember to bump a version constant.
//
// A MISS IS NEVER A FAILURE. Every read from the cache is wrapped: a missing,
// truncated, unreadable or wrong-magic entry is demoted to a miss and re-encoded.
// The cache can be deleted at any moment and the only consequence is a slow build.
const CACHE = { hits: 0, misses: 0, bytesServed: 0, stored: 0, errors: 0, used: new Set() };
const sha256File = (p) => createHash('sha256').update(readFileSync(p)).digest('hex');
const recipeHash = (o) => createHash('sha256').update(JSON.stringify(o)).digest('hex').slice(0, 16);
/** cache path for (kind, recipe, source-digest, output extension) */
function cachePath(kind, recipe, srcSha, ext) {
  return join(CACHE_DIR, kind + '-' + recipe, srcSha.slice(0, 2), srcSha.slice(2) + ext);
}
/** Copy a cached artifact into place. Returns false (a MISS) on anything at all
 *  wrong with it — including a magic-byte check, so a corrupt entry can never
 *  reintroduce the silent-loader bug the .glb gate exists for. */
function cacheGet(cp, dest, magic) {
  if (NO_CACHE) return false;
  try {
    if (!existsSync(cp)) return false;
    const st = statSync(cp);
    if (!st.isFile() || st.size === 0) return false;
    if (magic) {
      const fd = openSync(cp, 'r'); const b = Buffer.alloc(magic.length);
      readSync(fd, b, 0, magic.length, 0); closeSync(fd);
      if (b.toString('latin1') !== magic) { warn('cache entry has the wrong magic, re-encoding: ' + cp); CACHE.errors++; return false; }
    }
    mkdirSync(dirname(dest), { recursive: true });
    copyFileSync(cp, dest);
    CACHE.hits++; CACHE.bytesServed += st.size; CACHE.used.add(cp);
    return true;
  } catch (e) { warn('cache read failed (treating as a miss): ' + e.message); CACHE.errors++; return false; }
}
/** Store a freshly encoded artifact. Written to a temp name and renamed, so a
 *  build killed mid-write leaves no half-file for the next build to trust. */
function cachePut(cp, src) {
  if (NO_CACHE) return;
  try {
    mkdirSync(dirname(cp), { recursive: true });
    const tmp = cp + '.' + process.pid + '.tmp';
    copyFileSync(src, tmp); renameSync(tmp, cp);
    CACHE.stored++; CACHE.used.add(cp);
  } catch (e) { warn('cache write failed (harmless, next build re-encodes): ' + e.message); CACHE.errors++; }
}
/** Tool versions belong in the key: a Pillow or gltf-transform upgrade changes
 *  the bytes and nothing else in the key would notice. Probed once, cheaply. */
const probe = (cmd, args) => { try { return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { return 'unknown'; } };

// *** ONE DEFINITION OF "WHICH .png BECOMES A .webp", SHARED BY THREE READERS. ***
// (a) the webp pass picks its targets with it, (b) the runtime shim injected into
// the shipped page rewrites requests with it, and (c) the reference-integrity gate
// at the bottom of this file decides with it whether a vanished .png is still
// reachable. They used to be three hand-copied regexes; a build that converts a
// file the shim cannot rewrite is a silent 404, and a build that rewrites a request
// for a file it did not convert is the same 404 backwards. Both are now impossible
// to write by hand: there is exactly one source and the shim is serialised from it.
const SWAP_RE = /((^|\/)(bg|background|stylized|main|festival|gray|open)\.png(\?|$))|(assets\/characters\/[^?]*\.png(\?|$))/;
const SWAP_DENY = /(^|\/)(depth|mask|maskraw)[\w-]*\.png/i;
const willSwap = (rel) => SWAP_RE.test(rel) && !SWAP_DENY.test(rel);
const swapped = (rel) => rel.replace(/\.png(\?|$)/, '.webp$1');
/** every .png the webp pass removed from the output (rel paths) — the gate's evidence */
const WEBP_DELETED = [];

// *** THE SHIM CANNOT SEE A CSS BACKGROUND. ***
// patchPlateExtensions hooks HTMLImageElement.prototype.src and window.fetch —
// every way the runtime loads a PLATE. It is not every way the runtime loads a
// PORTRAIT: `EBUI.portrait()` (ui_kit.js:664, the party list and the 210 px bust in
// the pause menu), dialogue.js's framed-thumbnail fallback and battle_turnbased's
// status row all build `background-image:url("…/bust.png")` INTO AN HTML STRING.
// A CSS url() never touches an HTMLImageElement and never touches fetch, so the shim
// never sees it, and after the webp pass the file it names is gone.
//   MEASURED on the compressed build: assets/characters/vesper/bust.png -> 404 from
// the built tree, 200 from public/; bust.webp is the mirror image. Every party
// portrait in the menu was a blank frame in the deploy, and no gate saw it — a CSS
// background that 404s logs nothing the console gate reads and breaks no gameplay.
//
// THE FIX IS AT THE BUILDER, NOT THE LOADER. Rewriting the six URL builders means
// both the <img> path and the CSS path get a name that exists, and the shim becomes
// redundant for portraits rather than load-bearing. Only assets/characters/ builders
// are touched: assets/battle/ and assets/monsters/ are NOT converted and must keep
// their .png.
//   EVERY ENTRY MUST MATCH EXACTLY ONCE. If a lane edits one of these lines the
// build FAILS LOUDLY instead of shipping blank portraits — which is the whole point,
// because the failure this replaces was invisible.
const PORTRAIT_URL_REWRITES = [
  ['js/ui_kit.js',
    `return assetBase + 'characters/' + String(id) + '/bust.png';`,
    `return assetBase + 'characters/' + String(id) + '/bust.webp';`],
  ['js/ui_kit.js',
    `const POSE_NAMES = ['pose.png', 'pose-front.png'];`,
    `const POSE_NAMES = ['pose.webp', 'pose-front.webp'];`],
  ['js/dialogue.js',
    `return expr ? d + 'expr-' + expr + '.png' : d + 'bust.png';`,
    `return expr ? d + 'expr-' + expr + '.webp' : d + 'bust.webp';`],
  ['js/dialogue.js',
    `return d + 'cutin-' + expr + '.png';`,
    `return d + 'cutin-' + expr + '.webp';`],
  ['js/dialogue.js',
    `return d + 'cutin.png';`,
    `return d + 'cutin.webp';`],
  ['js/battle_turnbased.js',
    `return 'assets/characters/' + String(charId) + '/bust.png';`,
    `return 'assets/characters/' + String(charId) + '/bust.webp';`],
];

// ---- --audit <dir> : run ONLY the reference-integrity gate, then exit --------
// Re-check a tree somebody else built (or a deploy you are about to upload) in a
// few seconds, without rebuilding. It touches nothing.
if (flag('audit')) {
  const dir = opt('audit', null);
  if (!dir || !existsSync(dir)) die('--audit needs a built directory: node tools/build-static.mjs --audit dist-c');
  log('\n  reference-integrity audit of ' + dir + '\n');
  referenceAudit(dir, null);
  log('');
  process.exit(0);
}

// The WebP worker. Kept as a string so this tool stays one file with no deps
// beyond Pillow, which is what the repo already has.
const WEBP_PY = `
import json, sys, os
from PIL import Image
spec = json.load(open(sys.argv[1]))
PLATE_MAX = spec.get('plateMax', 0)   # 0 = ship at the master's own size

# THE DOWNSCALE, and WHY IT LIVES HERE AND NOT IN THE BAKE (2026-08-02).
# The plates are baked at 2688x1536 — 2.5x the PIXELS of the 1080p TV this game is
# played on. The obvious "fix" is to bake smaller; that is a ONE-WAY DOOR, because
# getting the resolution back costs a re-bake of every plate in the town (~4 min
# each, and the bake is the most expensive thing in this repo). So the masters stay
# at 2688 and the WEB BUILD downscales. Archive high, ship low.
#   LANCZOS, not the default: a nearest/bilinear downscale of a photographic plate
# aliases the high-frequency detail these renders are full of (roof tiles, foliage,
# cobbles) into shimmer.
#   DEPTH IS NEVER TOUCHED, at any size. It is rgb24-viewz data the runtime samples
# for exact-pixel occlusion; resampling it invents depths that were never rendered
# and the error lands exactly on silhouette edges, where occlusion is decided. A
# lossless-but-resized depth plate is still a corrupted one.
def fit(im):
    if not PLATE_MAX or max(im.size) <= PLATE_MAX: return im
    w, h = im.size
    s = PLATE_MAX / float(max(w, h))
    return im.resize((round(w * s), round(h * s)), Image.LANCZOS)

def enc(paths, lossless):
    saved = before = 0; n = 0
    for p in paths:
        im = Image.open(p); im.load()
        if not lossless: im = fit(im)          # never resize depth/mask
        out = os.path.splitext(p)[0] + '.webp'
        if lossless:
            im.save(out, 'WEBP', lossless=True, quality=100, method=6, exact=True)
            # *** THE GATE: a depth plate must decode to the SAME BYTES. ***
            a = Image.open(p).convert('RGB').tobytes()
            b = Image.open(out).convert('RGB').tobytes()
            if a != b:
                os.remove(out)
                raise SystemExit('DEPTH ROUND-TRIP MISMATCH: ' + p + ' - refusing to ship a lossy depth plate')
        else:
            im.save(out, 'WEBP', quality=88, method=6)
        before += os.path.getsize(p); saved += os.path.getsize(out); n += 1
        os.remove(p)
    return n, before, saved
n, b, a = enc(spec['lossy'], False)
print('lossy  %4d plates  %.1f MB -> %.1f MB' % (n, b/1048576, a/1048576))
if spec['lossless']:
    n, b, a = enc(spec['lossless'], True)
    print('LOSSLESS (byte-exact verified) %4d depth/mask  %.1f MB -> %.1f MB' % (n, b/1048576, a/1048576))
else:
    print('depth.png / mask.png left as lossless PNG (use --webp-depth to convert)')
`;

// ---- --fetch-draco : vendor the decoder, then exit ---------------------------
// three.min.js here is r128 (2021), so the DRACOLoader that matches is the
// CLASSIC non-module examples/js build — the module build would not attach to
// the global THREE these pages use.
if (flag('fetch-draco')) {
  const dest = join(ROOT, 'tools/vendor/draco');
  mkdirSync(join(dest, 'gltf'), { recursive: true });
  const B = 'https://unpkg.com/three@0.128.0/examples/js';
  const files = [
    [`${B}/loaders/DRACOLoader.js`, 'DRACOLoader.js'],
    [`${B}/libs/draco/gltf/draco_decoder.js`, 'draco_decoder.js'],
    [`${B}/libs/draco/gltf/draco_decoder.wasm`, 'draco_decoder.wasm'],
    [`${B}/libs/draco/gltf/draco_wasm_wrapper.js`, 'draco_wasm_wrapper.js'],
  ];
  for (const [url, name] of files) {
    execFileSync('curl', ['-fsSL', '-o', join(dest, name), url]);
    log('  fetched ' + name + '  ' + (statSync(join(dest, name)).size / 1024).toFixed(0) + ' KB');
  }
  log('\n  vendored into tools/vendor/draco — `--draco` will now work.\n');
  process.exit(0);
}

// ---- the plan: every copy is a claim with a reason --------------------------
/** @type {{src:string,dest:string,why:string,cat:string}[]} */
const PLAN = [];
const claimed = new Set();
function claim(relSrc, cat, why, relDest = relSrc) {
  const src = join(PUB, relSrc);
  if (claimed.has(relDest)) return;
  if (!existsSync(src)) { warn(`missing (${why}): public/${relSrc}`); MISSING.push(relSrc); return; }
  claimed.add(relDest);
  PLAN.push({ src, dest: join(OUT, relDest), cat, why, rel: relDest });
}
function claimDir(relDir, cat, why, filter = () => true) {
  const abs = join(PUB, relDir);
  if (!existsSync(abs)) { warn(`missing dir (${why}): public/${relDir}`); MISSING.push(relDir + '/'); return; }
  for (const f of walk(abs)) {
    const r = relative(PUB, f).split('/').join('/');
    if (filter(basename(f), r)) claim(r, cat, why);
  }
}
function walk(dir, out = []) {
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) walk(p, out); else if (e.isFile()) out.push(p);
  }
  return out;
}
const MISSING = [];

// ---- read the game's own data ----------------------------------------------
const readJson = (rel) => JSON.parse(readFileSync(join(PUB, rel), 'utf8'));

/** Evaluate public/game/scenes.js in a sandbox and take what it declares.
 *  Deliberately tolerant: a parallel lane is removing SCENE_ARCHIVE, so its
 *  absence must be normal, not a crash. */
function readSceneRegistry() {
  const src = readFileSync(join(PUB, 'game/scenes.js'), 'utf8');
  const win = {};
  const ctx = createContext({ window: win, globalThis: win });
  try { runInContext(src, ctx, { filename: 'scenes.js' }); }
  catch (e) { die('could not evaluate public/game/scenes.js: ' + e.message); }
  const reg = win.SCENE_REGISTRY;
  if (!reg || typeof reg !== 'object') die('public/game/scenes.js declared no window.SCENE_REGISTRY');
  return { registry: reg, archive: win.SCENE_ARCHIVE || null };
}

const { registry: RAW_REGISTRY, archive: ARCHIVE } = readSceneRegistry();
const isDevGroup = (g) => /developer tools/i.test(g);
const REGISTRY = {};
for (const [group, list] of Object.entries(RAW_REGISTRY)) {
  if (NO_DEV_SCENES && isDevGroup(group)) continue;
  REGISTRY[group] = list;
}
const stripFlags = (k) => String(k).split('&')[0];

// scene bundles the shipped game can reach:
//   the registry (what the launcher offers and the H dev menu jumps to)
//   + every scenegraph node (an edge into a bundle that is not here is a dead end)
//   + every story beat's scene (a beat cannot fire in a scene that was not shipped)
const sceneKeys = new Set();
const sceneWhy = new Map();
const addScene = (k, why) => { const s = stripFlags(k); if (!s) return; if (!sceneKeys.has(s)) sceneWhy.set(s, why); sceneKeys.add(s); };
for (const [group, list] of Object.entries(REGISTRY)) for (const [k] of list) addScene(k, 'scenes.js registry: ' + group);
const SG = readJson('world/scenegraph.json');
for (const id of Object.keys(SG.nodes || {})) addScene(id, 'world/scenegraph.json node');
const STORY = readJson('game/story.json');
for (const b of Object.values(STORY.beats || {})) if (b && b.scene) addScene(b.scene, 'story.json beat');
for (const n of Object.values(STORY.nodes || {})) if (n && n.scene) addScene(n.scene, 'story.json node');

// ---- 1. pages ---------------------------------------------------------------
// index.html gets ONE build-time transform: the "Review tools" strip names pages
// that are dev artefacts. Whatever of them is shipped stays a link; the rest are
// dropped, because a front door with a dead link is a broken deploy. The source
// file is not edited (another lane owns it).
const SHIPPED_REVIEW = new Set(KEEP_STORY ? ['story.html', 'townmap/viewer.html'] : ['townmap/viewer.html']);
{
  let html = readFileSync(join(PUB, 'index.html'), 'utf8');
  const before = html;
  // (a) prune the review-tool strip down to the pages this build actually ships
  html = html.replace(/<a href="([^"]+)"(?:\s[^>]*)?>[\s\S]*?<\/a>\s*(?:·\s*)?/g, (m, href) => {
    if (/^https?:/.test(href)) return m;
    const bare = href.split('?')[0].split('#')[0];
    if (bare.endsWith('.html') && !SHIPPED_REVIEW.has(bare)) return '';
    if (!bare.endsWith('.html')) return '';          // cine_regions.svg etc: dev artefacts
    return m;
  });
  html = html.replace(/(<b>Review tools:<\/b>)\s*·\s*/, '$1\n  ');
  html = html.replace(/·\s*(<\/div>)/, '$1');
  // (b) drop the legacy-archive section. SCENE_ARCHIVE may already be gone from
  //     scenes.js (a lane is removing it) and this build never ships archived
  //     bundles, so the collapsed section would only ever render empty.
  html = html.replace(/\/\/ legacy scenes live behind[\s\S]*?m\.appendChild\(det\);\n/,
    '// (legacy archive section removed by tools/build-static.mjs: this build ships\n' +
    '//  only the current registry, so there is nothing behind it)\n');
  if (html === before) warn('index.html transform matched nothing — check the front door for dead links');
  mkdirSync(OUT, { recursive: true });
  PLAN.push({ inline: html, dest: join(OUT, 'index.html'), cat: 'code', why: 'the front door (review-tool links pruned to what ships)', rel: 'index.html' });
  claimed.add('index.html');
}
claim('play3d.html', 'code', 'the engine page');
// server.js served public/play3d.html AT /play.html. dist has no router, so the
// friendly path has to be a real file. A byte copy (not a redirect) keeps every
// relative asset path identical and keeps cdp.mjs's GAME_PAGE matcher honest.
PLAN.push({ src: join(PUB, 'play3d.html'), dest: join(OUT, 'play.html'), cat: 'code', why: 'replaces server.js GET /play.html', rel: 'play.html' });
claimed.add('play.html');
if (KEEP_STORY) {
  // Same treatment index.html gets, for the same reason: story.html's top strip
  // links `assets.html`, a DEV page this build does not ship, so the deployed page
  // carried a 404 behind a visible link. Caught by the reference-integrity gate at
  // the bottom of this file, which is exactly what it is for.
  let h = readFileSync(join(PUB, 'story.html'), 'utf8');
  h = h.replace(/(?:\s*·\s*)?<a href="([^"]+)"[^>]*>[\s\S]*?<\/a>/g, (m, href) => {
    if (/^(https?:|\/|#)/.test(href)) return m;
    const bare = href.split('?')[0].split('#')[0];
    return (bare.endsWith('.html') && !SHIPPED_REVIEW.has(bare)) ? '' : m;
  });
  PLAN.push({ inline: h, dest: join(OUT, 'story.html'), cat: 'code', why: 'story/world review page (links pruned to what ships)', rel: 'story.html' });
  claimed.add('story.html');
}

// ---- 2. code ----------------------------------------------------------------
// The module list is READ OUT OF play3d.html's own <script src> tags, so a module
// the coordinator adds tomorrow ships without editing this file.
const play3d = readFileSync(join(PUB, 'play3d.html'), 'utf8');
const scriptSrcs = [...play3d.matchAll(/<script[^>]*\bsrc="([^"]+)"/g)].map(m => m[1]).filter(s => !/^https?:/.test(s));
for (const s of scriptSrcs) claim(s.replace(/^\.\//, ''), 'code', 'play3d.html <script src>');
// battle_stage3d.js is deliberately NOT in that list — battle_turnbased.js loads
// it at runtime off its own script URL (see its comment at line ~676).
claim('js/battle_stage3d.js', 'code', 'loaded at runtime by battle_turnbased.js');
if (KEEP_STORY) {
  const story = readFileSync(join(PUB, 'story.html'), 'utf8');
  for (const s of [...story.matchAll(/<script[^>]*\bsrc="([^"]+)"/g)].map(m => m[1]).filter(s => !/^https?:/.test(s)))
    claim(s.replace(/^\.\//, ''), 'code', 'story.html <script src>');
}

// game data: every json under public/game (the runtime fetches these by name)
claimDir('game', 'code', 'game data read by the runtime modules', (f) => f.endsWith('.json'));
// scenes.js is REGENERATED below (filtered), not copied.

// world data actually fetched by the runtime
claim('world/scenegraph.json', 'code', 'play3d.html fetch(world/scenegraph.json)');
claim('world/world.json', 'code', 'world source referenced by the scenegraph');
claimDir('world/regions', 'code', 'region data referenced by world.json');

// townmap: play3d fetches townmap/<town>.map.json; route_overlay fetches
// townmap/<town>.routes.json. The town names come from the scenegraph's own
// origin strings, so a new town ships without touching this file.
const towns = new Set();
{
  const sgTxt = readFileSync(join(PUB, 'world/scenegraph.json'), 'utf8');
  for (const m of sgTxt.matchAll(/townmap\/([\w.-]+)\.map\.json/g)) towns.add(m[1]);
}
for (const t of towns) {
  claim(`townmap/${t}.map.json`, 'code', 'play3d.html fetch(townmap/<town>.map.json)');
  claim(`townmap/${t}.routes.json`, 'code', 'route_overlay.js fetch(townmap/<town>.routes.json)');
  // cameras.json IS RUNTIME ART, not a review file. play3d.html's charLight()
  // fetches it for defaults.lightRig — the town's own sun direction and colour,
  // read from the very file tools/cine_bake.py baked the plates from so the
  // runtime and the plate cannot disagree about where the light is. It used to be
  // claimed only under the viewer's `if`, which happened to be true and so hid the
  // dependency: drop the review page from a build and every town would silently
  // fall back to the page-default sun at (6,10,4), which is the "unlit character"
  // bug shipping again with every gate green. The viewer still needs the solved
  // pair, and that one stays where it was.
  claim(`townmap/${t}.cameras.json`, 'code', 'play3d.html charLight() fetch(defaults.lightRig)');
  if (SHIPPED_REVIEW.has('townmap/viewer.html'))
    claim(`townmap/${t}.cameras.solved.json`, 'code', 'townmap viewer');
}
if (SHIPPED_REVIEW.has('townmap/viewer.html')) claim('townmap/viewer.html', 'code', 'linked from the front door');

// ---- 3. scene bundles -------------------------------------------------------
// INSIDE a bundle the rule is the same as outside it: claim the names the runtime
// asks for, not the directory. play3d.html's own reads (all of the form BASE+…):
//   meta.json  stylized.png  depth.json  depth.png  cine.json  scene.glb  zones.json
// and, for a cinematic bundle, the per-camera plates NAMED BY cine.json itself
// (c.art.bg / c.art.depth) — so the plate paths are read out of the data rather
// than guessed from the directory layout.
//
// This is what leaves background.png behind: the bakers write it (the pre-tonemap
// plate) and NOTHING in public/js or play3d.html ever fetches it. 75.6 MB across
// 16 bundles, and a directory copy would have shipped every byte of it.
const BUNDLE_FILES = ['meta.json', 'stylized.png', 'depth.json', 'depth.png', 'cine.json', 'scene.glb', 'zones.json'];
for (const key of [...sceneKeys].sort()) {
  const why = sceneWhy.get(key);
  const dir = join(PUB, 'assets/scenes', key);
  if (!existsSync(dir)) { warn(`registry names a bundle that is not on disk: ${key} (${why})`); MISSING.push('assets/scenes/' + key + '/'); continue; }
  for (const f of BUNDLE_FILES) if (existsSync(join(dir, f))) claim(`assets/scenes/${key}/${f}`, 'scenes', why);
  const cinePath = join(dir, 'cine.json');
  if (existsSync(cinePath)) {
    let cine; try { cine = JSON.parse(readFileSync(cinePath, 'utf8')); } catch (e) { die(`${key}/cine.json is unparseable: ${e.message}`); }
    for (const c of cine.cameras || []) {
      for (const p of [c.art && c.art.bg, c.art && c.art.depth]) {
        if (!p) continue;
        claim(`assets/scenes/${key}/${p}`, 'scenes', `${key}/cine.json camera "${c.id}"`);
      }
    }
  }
  // a bundle whose files are all unclaimed is a bundle that will 404 on load
  const took = [...claimed].filter(r => r.startsWith(`assets/scenes/${key}/`)).length;
  if (!took) warn(`claimed NOTHING from bundle ${key} — check its layout`);
}

// ---- 4. characters ----------------------------------------------------------
// THE CAST is the union of everyone the shipped data can name. Anything else in
// assets/characters (studio plates, candidates, turnarounds, superseded busts,
// retired rigs) is simply never claimed.
const cast = new Set();
const addCast = (id) => { if (id && typeof id === 'string' && !id.startsWith('_')) cast.add(id); };
for (const f of ['game/dialogue.json', 'game/story.json'])
  for (const id of Object.keys(readJson(f).speakers || {})) addCast(id);
for (const id of Object.keys(readJson('game/npcs.json').npcs || {})) addCast(id);
for (const id of Object.keys(readJson('game/growth.json').characters || {})) addCast(id);
const CUTINS_REL = 'assets/characters/cutins.json';
let cutins = {};
if (existsSync(join(PUB, CUTINS_REL))) { cutins = readJson(CUTINS_REL); for (const id of Object.keys(cutins)) addCast(id); }
claim(CUTINS_REL, 'characters', 'dialogue.js reads it to pick cut-in vs framed thumbnail');

// Per-cast-member SHIPPING PATTERNS. These are the only names the runtime builds:
//   dialogue.js  bustUrl()  -> <id>/bust.png, <id>/expr-<mood>.png
//   dialogue.js  cutin()    -> <id>/cutin.png, <id>/cutin-<mood>.png
//   ui_kit.js / battle_turnbased.js -> <id>/bust.png
const CAST_PATTERNS = [/^bust\.png$/, /^expr-[\w-]+\.png$/, /^cutin\.png$/, /^cutin-[\w-]+\.png$/];
for (const id of [...cast].sort()) {
  const dir = join(PUB, 'assets/characters', id);
  if (!existsSync(dir)) continue;                     // a speaker with no art is legal
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (!e.isFile()) continue;                        // never studio/ or candidates/
    if (CAST_PATTERNS.some(re => re.test(e.name)))
      claim(`assets/characters/${id}/${e.name}`, 'characters', 'portrait for speaker "' + id + '"');
  }
}

// EXPLICIT asset paths written in the data / the code. Rigs are claimed one by
// one rather than by glob: assets/characters/<id>/ holds several versions of the
// same body and only the one the registry names is ever fetched.
const explicit = new Map();
const addExplicit = (p, why) => { if (p && p.startsWith('assets/')) explicit.set(p, why); };
{
  const npcTxt = readFileSync(join(PUB, 'game/npcs.json'), 'utf8');
  for (const m of npcTxt.matchAll(/"(assets\/[^"]+\.(?:png|glb|jpg|jpeg))"/g)) addExplicit(m[1], 'npcs.json body.src');
  // play3d.html MODELS registry — the overworld bodies
  const models = play3d.match(/const MODELS=\{[\s\S]*?\};/);
  if (models) for (const m of models[0].matchAll(/'(assets\/[^']+\.glb)'/g)) addExplicit(m[1], 'play3d.html MODELS registry');
  // play3d.html HD-2D sheet default
  for (const m of play3d.matchAll(/'(assets\/characters3d\/)'\s*\+\s*CHAR/g)) addExplicit('assets/characters3d/vesper.png', 'play3d.html default ?char sheet');
  // battle_stage3d models table — FIRST url of each list only ("the first URL
  // that PARSES wins"; the later ones are the same rig under an older name and
  // are never fetched while the first one is there).
  const bs = readFileSync(join(PUB, 'js/battle_stage3d.js'), 'utf8');
  const tbl = bs.match(/models:\s*\{[\s\S]*?\},\n/);
  if (tbl) for (const line of tbl[0].split('\n')) {
    const first = line.match(/'(assets\/[^']+\.glb)'/);
    if (first) addExplicit(first[1], 'battle_stage3d.js models table (primary rig)');
  }
}
// play3d's MODELS carries dev-only keys (?model=vesper-test). Ship what a normal
// playthrough can reach; a dev key costs a 404 nobody but a lane will see.
const DEV_MODEL_RE = /anim_test\.glb$/;
for (const [p, why] of explicit) {
  if (DEV_MODEL_RE.test(p)) continue;
  claim(p, p.includes('/characters') ? 'characters' : 'other', why);
}

// ---- 5. music, battle backdrops, monsters -----------------------------------
{
  const music = readJson('game/music.json');
  for (const t of Object.values(music.tracks || {})) if (t && t.src) claim(t.src, 'music', 'music.json track');
  const musicTxt = readFileSync(join(PUB, 'game/music.json'), 'utf8');
  for (const m of musicTxt.matchAll(/"(assets\/music\/[^"]+)"/g)) claim(m[1], 'music', 'music.json track');
}
{
  // battle_turnbased/battle_stage3d build these by convention: base + dir + key.
  const encTxt = readFileSync(join(PUB, 'game/encounters.json'), 'utf8');
  const backs = new Set([...encTxt.matchAll(/"battleBackdrop"\s*:\s*"([\w-]+)"/g)].map(m => m[1]));
  for (const b of backs) claim(`assets/battle/${b}.png`, 'other', 'encounters.json battleBackdrop');
  const mon = readJson('game/monsters.json');
  for (const id of Object.keys(mon.monsters || {})) {
    if (id.startsWith('_')) continue;
    claim(`assets/monsters/placeholder/${id}.png`, 'other', 'monsters.json sprite (tier 3)');
    const glb = `assets/monsters/3d/${id}.glb`;
    if (existsSync(join(PUB, glb))) claim(glb, 'other', 'monsters.json 3D model (tier 1)');
  }
  // monsters/3d holds CC0 rigs under their own names; battle_stage3d maps them.
  claimDir('assets/monsters/3d', 'other', 'battle_stage3d monster models (tier 1)', (f) => /\.(glb|json)$/.test(f));
}

// ---- 6. the story manifest (pre-built, replacing server.js's storyGate) ------
if (KEEP_STORY) {
  log('  building the story manifest once (server.js did this per request) …');
  try {
    execFileSync('node', [join(ROOT, 'tools/build-story.mjs')], { cwd: ROOT, stdio: 'pipe' });
  } catch (e) {
    warn('story manifest build failed; shipping the last good one: ' + (e.stderr ? String(e.stderr).slice(0, 300) : e.message));
  }
  claim('assets/story-manifest.json', 'code', 'pre-built at build time (server.js rebuilt it per request)');
}

// ---- WRITE ------------------------------------------------------------------
if (existsSync(OUT)) rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
// COPYFILE_FICLONE: on APFS this is a copy-on-write clone — the 1.2 GB stage
// becomes metadata instead of 1.2 GB of reads and writes. It is a HINT, not a
// mode: on a filesystem that cannot clone, node falls back to a real copy, so
// this is free everywhere and fast here. (Not FICLONE_FORCE, which would fail.)
for (const p of PLAN) {
  mkdirSync(dirname(p.dest), { recursive: true });
  if (p.inline != null) writeFileSync(p.dest, p.inline);
  else copyFileSync(p.src, p.dest, COPYFILE_FICLONE);
}
log(`  staged ${PLAN.length} files  [${secs()}]`);

// regenerate scenes.js from the FILTERED registry. Emitting it (rather than
// copying) is what makes --no-dev-scenes honest and what stops the launcher
// rendering an archive section for bundles this build did not ship.
{
  const body = '// GENERATED by tools/build-static.mjs — the shipped subset of the scene registry.\n' +
    '// Source of truth is public/game/scenes.js; edit there.\n' +
    'window.SCENE_REGISTRY = ' + JSON.stringify(REGISTRY, null, 1) + ';\n';
  mkdirSync(join(OUT, 'game'), { recursive: true });
  writeFileSync(join(OUT, 'game/scenes.js'), body);
  PLAN.push({ dest: join(OUT, 'game/scenes.js'), cat: 'code', why: 'generated: shipped subset of the registry', rel: 'game/scenes.js' });
}

// ---- COMPRESSION HOOKS (off by default) -------------------------------------
const NEVER_LOSSY = /(^|\/)(depth|mask|maskraw)[\w-]*\.png$/i;

if (WEBP) await webpPass();
if (GLB) await glbPass();

async function webpPass() {
  log('\n  --webp: re-encoding background plates …');
  const py = join(ROOT, 'tools/_webp_pass.py');
  writeFileSync(py, WEBP_PY);
  // THE SAME RULE THE SHIM WILL USE (SWAP_RE / SWAP_DENY above) — plates by name,
  // plus every portrait under assets/characters. Pictures, every one: the runtime
  // draws them and never samples them.
  const targets = walk(OUT).filter(f => {
    const r = relative(OUT, f);
    return f.endsWith('.png') && !NEVER_LOSSY.test(r) && willSwap(r);
  });
  for (const f of targets) WEBP_DELETED.push(relative(OUT, f));
  const depth = WEBP_DEPTH ? walk(OUT).filter(f => NEVER_LOSSY.test(relative(OUT, f))) : [];

  // THE RECIPE. Everything that can change a byte of the output: the encoder
  // script verbatim (quality, method, LANCZOS, the depth round-trip gate — all of
  // it lives in WEBP_PY, so an edit there invalidates the cache by itself),
  // --plate-max, and the Pillow/Python that will run it.
  const recipe = recipeHash({
    encoder: WEBP_PY, plateMax: PLATE_MAX,
    pillow: probe('python3', ['-c', 'import PIL,sys;print(PIL.__version__, sys.version.split()[0])']),
  });
  const hits = [], miss = []; const served0 = CACHE.bytesServed;
  for (const f of targets) {
    const cp = cachePath('webp', recipe, sha256File(f), '.webp');
    const out = f.replace(/\.png$/, '.webp');
    // 'RIFF' — a truncated or half-written .webp can never be served as a plate.
    if (cacheGet(cp, out, 'RIFF')) { rmSync(f); hits.push(f); }
    else miss.push({ f, out, cp });
  }
  CACHE.misses += miss.length;
  if (hits.length) log(`    cache: ${hits.length}/${targets.length} plates served from ${relative(ROOT, CACHE_DIR) || CACHE_DIR}` +
    ` (${((CACHE.bytesServed - served0) / 1048576).toFixed(1)} MB, no re-encode)`);

  // DEPTH IS DELIBERATELY NOT CACHED. Its encode carries its own gate — decode
  // both files back to RGB and compare every byte — and that gate is the only
  // reason a lossless depth plate is allowed to ship at all. Serving it from a
  // cache would skip the proof to save ~87 MB of work nobody runs by default.
  const listFile = join(ROOT, '.webp-list.tmp');
  writeFileSync(listFile, JSON.stringify({ lossy: miss.map(m => m.f), lossless: depth, plateMax: PLATE_MAX }));
  try {
    const out = execFileSync('python3', [py, listFile], { encoding: 'utf8', maxBuffer: 1 << 28 });
    log(out.trim().split('\n').map(l => '    ' + l).join('\n'));
  } catch (e) {
    die('--webp pass failed (depth round-trip check is fatal by design):\n' + (e.stdout || '') + (e.stderr || e.message));
  } finally { rmSync(listFile, { force: true }); rmSync(py, { force: true }); }
  for (const m of miss) if (existsSync(m.out)) cachePut(m.cp, m.out);
  // rewrite the references the runtime builds by name
  patchPlateExtensions();
  patchPortraitUrls();
}


function patchPortraitUrls() {
  const missed = [];
  const byFile = new Map();
  for (const [rel, from, to] of PORTRAIT_URL_REWRITES) {
    const p = join(OUT, rel);
    if (!existsSync(p)) { missed.push(`${rel} is not in the build at all`); continue; }
    let s = byFile.has(rel) ? byFile.get(rel) : readFileSync(p, 'utf8');
    const n = s.split(from).length - 1;
    if (n !== 1) { missed.push(`${rel}: matched ${n}x (expected exactly 1)\n      ${from}`); continue; }
    byFile.set(rel, s.split(from).join(to));
  }
  if (missed.length) die(
    'the portrait-URL rewrite table no longer matches the shipped JS. Somebody edited a\n' +
    'portrait path builder; until the table is re-derived, this build would ship CSS\n' +
    'background-image URLs pointing at .png files the webp pass deleted (blank portraits\n' +
    'in the menu and the battle status row). Fix the table in tools/build-static.mjs:\n  ' +
    missed.join('\n  '));
  for (const [rel, s] of byFile) writeFileSync(join(OUT, rel), s);
  log(`  portrait URL builders rewritten to .webp in ${byFile.size} module(s) ` +
      `(${PORTRAIT_URL_REWRITES.length} sites — a CSS url() is invisible to the shim)`);
}

// THE WORK-IN-PROGRESS BANNER (user ruling 2026-08-02: "we probably should add a
// banner to the top of the game window which says that this is a work in progress").
// INJECTED AT BUILD TIME, not written into public/ — the dev build has no need to
// tell its own author the game is unfinished, and a banner that only exists in the
// deployed artifact cannot be left behind in the source by accident.
//   It is dismissible and remembers that, because a banner you cannot get rid of is
// worse than no banner on a game you are trying to look at.
const WIP_BANNER = `<style>
#eb-wip{position:fixed;left:0;right:0;top:0;z-index:99999;background:#2b1d10ee;
  color:#f0d9b5;font:13px/1.5 system-ui,sans-serif;padding:7px 40px 7px 14px;
  border-bottom:1px solid #5c4326;text-align:center;backdrop-filter:blur(3px)}
#eb-wip b{color:#e9a24b}
#eb-wip button{position:absolute;right:6px;top:3px;background:none;border:0;
  color:#c8ab84;font-size:17px;cursor:pointer;line-height:1;padding:4px 8px}
#eb-wip button:hover{color:#fff}
@media(max-width:600px){#eb-wip{font-size:11px;padding-right:34px}}
</style>
<div id="eb-wip" role="status">
  <b>Emberbrook — work in progress.</b>
  An early prototype: expect rough edges, and a story that does not finish yet.
  <button aria-label="Dismiss" onclick="this.parentNode.remove();try{localStorage.setItem('eb-wip-hid','1')}catch(e){}">&times;</button>
</div>
<script>try{if(localStorage.getItem('eb-wip-hid'))document.getElementById('eb-wip').remove()}catch(e){}</script>`;

function injectWipBanner() {
  let n = 0;
  for (const rel of ['index.html', 'play.html', 'play3d.html', 'story.html']) {
    const p = join(OUT, rel);
    if (!existsSync(p)) continue;
    let h = readFileSync(p, 'utf8');
    if (h.includes('id="eb-wip"')) continue;
    // After <body> if there is one; these pages mostly have no <body> tag at all
    // (they open straight into <meta>), so fall back to prepending.
    h = /<body[^>]*>/i.test(h) ? h.replace(/(<body[^>]*>)/i, `$1\n${WIP_BANNER}`)
                              : WIP_BANNER + '\n' + h;
    writeFileSync(p, h); n++;
  }
  log(`  work-in-progress banner injected into ${n} page(s)`);
}

function patchPlateExtensions() {
  // The runtime asks for '<cam>/bg.png' by convention. One shim, injected into
  // the shipped engine page, remaps a .png request to .webp for the plates that
  // were converted — and CANNOT touch depth/mask, whose names are on the deny
  // list above and never rewritten.
  for (const rel of ['play.html', 'play3d.html']) {
    const p = join(OUT, rel);
    if (!existsSync(p)) continue;
    let h = readFileSync(p, 'utf8');
    if (h.includes('EB_WEBP_SHIM')) continue;
    // The two regexes are SERIALISED FROM THE BUILD'S OWN CONSTANTS, never retyped:
    // the shim and the converter are then the same rule by construction.
    h = h.replace(/<script/, `<script>/*EB_WEBP_SHIM*/(function(){
  var RE=new RegExp(${JSON.stringify(SWAP_RE.source)});
  var D=new RegExp(${JSON.stringify(SWAP_DENY.source)},'i');
  var swap=function(u){ return (typeof u==='string' && RE.test(u) && !D.test(u)) ? u.replace(/\\.png(\\?|$)/,'.webp$1') : u; };
  var IS=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
  Object.defineProperty(HTMLImageElement.prototype,'src',{get:IS.get,set:function(v){IS.set.call(this,swap(v));},configurable:true});
  var f=window.fetch; window.fetch=function(u,o){ return f.call(this,swap(u),o); };
})();</script>\n<script`);
    writeFileSync(p, h);
  }
}

async function glbPass() {
  log('\n  --glb: compressing scene GLBs (textures -> WebP, then geometry -> DRACO) …');
  const vendor = join(ROOT, 'tools/vendor/draco');
  if (!existsSync(join(vendor, 'DRACOLoader.js')))
    die('--glb needs the DRACO decoder vendored first:\n' +
        '    node tools/build-static.mjs --fetch-draco\n' +
        '  (downloads three r128 DRACOLoader.js + the draco decoder into tools/vendor/draco/)');
  let cli;
  try { cli = execFileSync('sh', ['-c', 'command -v gltf-transform || echo NPX'], { encoding: 'utf8' }).trim(); }
  catch { cli = 'NPX'; }
  const run = (args) => cli === 'NPX'
    ? execFileSync('npx', ['-y', '@gltf-transform/cli@4', ...args], { encoding: 'utf8', maxBuffer: 1 << 28 })
    : execFileSync(cli, args, { encoding: 'utf8', maxBuffer: 1 << 28 });
  const glbs = walk(join(OUT, 'assets/scenes')).filter(f => f.endsWith('.glb'));
  // THE RECIPE, same discipline as the plates: the exact argv this pass runs plus
  // the CLI's own version. `@gltf-transform/cli@4` is a RANGE — a patch release
  // that repacks differently must not be served yesterday's bytes.
  const glbRecipe = recipeHash({
    pass: ['webp'], draco: false,
    cli: cli === 'NPX' ? probe('npx', ['-y', '@gltf-transform/cli@4', '--version']) : probe(cli, ['--version']),
  });
  let before = 0, after = 0, ghit = 0;
  for (const g of glbs) {
    const b0 = statSync(g).size; before += b0;
    // A cached bundle still has to be binary glTF before it is allowed in — this
    // is the `glTF` magic gate applied to the cache, at the one place a wrong
    // container would otherwise enter the build unexamined. The geometry gate at
    // the end of the build then re-proves POSITION+indices against public/, so a
    // cache hit is held to exactly the same standard as a fresh encode.
    const cp = cachePath('glb', glbRecipe, sha256File(g), '.glb');
    if (cacheGet(cp, g, 'glTF')) {
      const b1 = statSync(g).size; after += b1; ghit++;
      log(`    ${relative(OUT, g).padEnd(44)} ${(b0 / 1048576).toFixed(1)} -> ${(b1 / 1048576).toFixed(1)} MB  (cached)`);
      continue;
    }
    CACHE.misses++;
    // textures first: draco shrinks the buffer the texture pass would otherwise
    // have to walk, and running it second keeps each step's log honest.
    // *** THE TEMP FILES MUST END IN .glb. *** gltf-transform picks its OUTPUT
    // CONTAINER from the extension, so `scene.glb.webp` made it write a .gltf JSON
    // document plus a sidecar .bin — under a filename still called scene.glb. The
    // build "succeeded", the file was 25x smaller, and GLTFLoader got JSON where it
    // expected the binary glTF magic. It failed SILENTLY: no console error, no
    // scene graph, no walk meshes, no NPCs. The game booted into an empty world and
    // the story stalled after seven beats because the beats that fire on SEEING an
    // NPC had no NPC to see. Caught by playthrough_test against the built dist, and
    // by nothing else — every unit gate reads the source tree, not the build.
    const t1 = g + '.w.glb', t2 = g + '.d.glb';
    run(['webp', g, t1]); rmSync(g); renameSync(t1, g);
    // DRACO IS DELIBERATELY NOT RUN ON SCENE BUNDLES. These GLBs are the COLLISION
    // and WALK geometry — play3d reads their triangles for walkGround() and the body
    // box. Draco is a LOSSY geometry codec: it quantizes positions (14 bits by
    // default, ~1.2 cm over a 200 m town), and a walk floor that moves by a
    // centimetre is exactly the class of defect that cost this repo a day already.
    // It is also nearly free to skip: measured, the texture pass is the whole win
    // (509 MB -> 20 MB) and draco was the last ~12%. Correctness over 12%.
    void t2;
    cachePut(cp, g);
    const b1 = statSync(g).size; after += b1;
    log(`    ${relative(OUT, g).padEnd(44)} ${(b0 / 1048576).toFixed(1)} -> ${(b1 / 1048576).toFixed(1)} MB`);
  }
  log(`    GLB total ${(before / 1048576).toFixed(0)} MB -> ${(after / 1048576).toFixed(0)} MB` +
      (ghit ? `   (${ghit}/${glbs.length} from cache)` : ''));
  // decoder + loader into dist, and wire it into every page that makes a GLTFLoader
  mkdirSync(join(OUT, 'lib/draco'), { recursive: true });
  // cpSync, NOT a readdir+copyFileSync loop: tools/vendor/draco holds a `gltf/`
  // SUBDIRECTORY (the decoder's own wasm pair), and copyFileSync on a directory
  // throws ENOTSUP — which crashed the build at its very last step, AFTER the
  // 40-minute compression pass had already succeeded.
  cpSync(vendor, join(OUT, 'lib/draco'), { recursive: true });
  for (const rel of ['play.html', 'play3d.html']) {
    const p = join(OUT, rel); if (!existsSync(p)) continue;
    let h = readFileSync(p, 'utf8');
    if (h.includes('EB_DRACO_SHIM')) continue;
    h = h.replace(/(<script[^>]*src="lib\/GLTFLoader\.js"[^>]*>\s*<\/script>)/,
      `$1\n<script src="lib/draco/DRACOLoader.js"></script>\n<script>/*EB_DRACO_SHIM*/(function(){
  var d=new THREE.DRACOLoader(); d.setDecoderPath('lib/draco/');
  var C=THREE.GLTFLoader; THREE.GLTFLoader=function(m){ var l=new C(m); l.setDRACOLoader(d); return l; };
  THREE.GLTFLoader.prototype=C.prototype;
})();</script>`);
    writeFileSync(p, h);
  }
}

// ---- MEASURE ----------------------------------------------------------------
const CATS = ['scenes', 'characters', 'music', 'code', 'other'];
const size = { }; const count = {};
for (const c of CATS) { size[c] = 0; count[c] = 0; }
const files = walk(OUT);
const catOf = (rel) => rel.startsWith('assets/scenes/') ? 'scenes'
  : (rel.startsWith('assets/characters') || rel.startsWith('assets/characters3d')) ? 'characters'
  : rel.startsWith('assets/music/') ? 'music'
  : rel.startsWith('assets/') ? 'other' : 'code';
for (const f of files) { const rel = relative(OUT, f); const c = catOf(rel); size[c] += statSync(f).size; count[c]++; }
const total = CATS.reduce((a, c) => a + size[c], 0);
const MB = (b) => (b / 1048576).toFixed(1) + ' MB';
const GB = (b) => (b / 1073741824).toFixed(2) + ' GB';

// per-scene detail — this is the table that decides what to drop if a host says no
const perScene = [...sceneKeys].sort().map(k => {
  const d = join(OUT, 'assets/scenes', k);
  let s = 0, n = 0;
  if (existsSync(d)) for (const f of walk(d)) { s += statSync(f).size; n++; }
  return { key: k, bytes: s, files: n, why: sceneWhy.get(k) };
}).sort((a, b) => b.bytes - a.bytes);

log('\n' + '='.repeat(72));
log('  STATIC BUILD  ->  ' + OUT);
log('='.repeat(72));
log(`  scenes      ${MB(size.scenes).padStart(10)}   ${String(count.scenes).padStart(5)} files   (${sceneKeys.size} bundles)`);
log(`  characters  ${MB(size.characters).padStart(10)}   ${String(count.characters).padStart(5)} files   (${cast.size} in the cast)`);
log(`  music       ${MB(size.music).padStart(10)}   ${String(count.music).padStart(5)} files`);
log(`  code+data   ${MB(size.code).padStart(10)}   ${String(count.code).padStart(5)} files`);
log(`  other       ${MB(size.other).padStart(10)}   ${String(count.other).padStart(5)} files   (battle plates, monsters)`);
log('  ' + '-'.repeat(68));
log(`  TOTAL       ${MB(total).padStart(10)}  = ${GB(total)}   ${files.length} files`);
const biggest = files.map(f => ({ f: relative(OUT, f), b: statSync(f).size })).sort((a, b) => b.b - a.b).slice(0, 8);
log('\n  largest single files (a host per-file cap is measured here):');
for (const b of biggest) log(`    ${MB(b.b).padStart(9)}  ${b.f}`);
log('\n  scene bundles:');
for (const s of perScene) log(`    ${MB(s.bytes).padStart(9)}  ${s.key.padEnd(20)} ${s.why}`);
if (MISSING.length) { log('\n  claimed but ABSENT from public/ (' + MISSING.length + '):'); for (const m of MISSING.slice(0, 20)) log('    ' + m); }
log('\n  compression: webp=' + (WEBP ? 'ON' : 'off') + '  webp-depth=' + (WEBP_DEPTH ? 'ON' : 'off (depth.png stays lossless PNG)') + '  glb=' + (GLB ? 'ON' : 'off') + '  plate-max=' + (PLATE_MAX || 'master size'));
if (WEBP || GLB) {
  log('  encode cache: ' + (NO_CACHE ? 'DISABLED (--no-cache): everything re-encoded'
    : `${CACHE.hits} hit / ${CACHE.misses} miss, ${(CACHE.bytesServed / 1048576).toFixed(1)} MB served, ` +
      `${CACHE.stored} stored${CACHE.errors ? `, ${CACHE.errors} demoted to a miss` : ''}  [${CACHE_DIR}]`));
}
log('  wall clock: ' + secs());
log('='.repeat(72) + '\n');

// --cache-prune: drop entries this build did not touch. Off by default — two
// builds with different flags legitimately use different entries, and a prune
// that runs automatically would make them evict each other's work every time.
if (CACHE_PRUNE && !NO_CACHE && existsSync(CACHE_DIR)) {
  let n = 0, b = 0;
  for (const f of walk(CACHE_DIR)) if (!CACHE.used.has(f)) { b += statSync(f).size; rmSync(f, { force: true }); n++; }
  log(`  cache pruned: ${n} unused entries, ${(b / 1048576).toFixed(1)} MB freed\n`);
}

// THE GATE THAT WOULD HAVE CAUGHT THE SILENT ONE. A .glb whose first four bytes
// are not `glTF` is a JSON document wearing a binary file's name, and GLTFLoader
// fails on it WITHOUT throwing — the game boots into an empty world. Cheap to
// check, and the failure it prevents is invisible in every other gate.
{
  const bad = walk(OUT).filter(f => f.endsWith('.glb')).filter(f => {
    const fd = openSync(f, 'r'); const b = Buffer.alloc(4);
    readSync(fd, b, 0, 4, 0); closeSync(fd);
    return b.toString('latin1') !== 'glTF';
  });
  if (bad.length) die('these .glb files are not binary glTF (the loader will fail SILENTLY):\n  ' +
    bad.map(f => relative(OUT, f)).join('\n  '));
  log('  every .glb verified binary glTF');
}

// Every build gets the banner — it is a property of "this is a deployed artifact",
// not of "this build was compressed".
injectWipBanner();

// ---- THE REFERENCE-INTEGRITY GATE -------------------------------------------
// WHY. Twice in one night the build shipped a tree that every unit gate called
// green, because EVERY OTHER GATE IN THIS REPO READS THE SOURCE TREE, where the
// file it is asking about still exists under its original name. The build is the
// only place a path can change: a compressed extension, a pruned page, a renamed
// container. So the build has to be the place that checks them.
//
// WHAT IT ASSERTS, over the FINISHED artifact, with no browser and no network:
//   1. Every local path a shipped page or a shipped JSON manifest names RESOLVES —
//      as itself, or through the plate/portrait rewrite the shim performs at
//      runtime. Restricted to paths that EXIST IN public/, because "a speaker with
//      no art" and "a bundle with no zones.json" are documented, load-bearing
//      absences; a gate that fires on those gets switched off. A path that resolved
//      in the source tree and does not resolve in the build is, always, a build bug.
//   2. Every .png the compression pass DELETED is one the shim can rewrite, and
//      its .webp is really there. This is the exact shape of the failure: the build
//      quietly moves a file and nothing tells the client.
//   3. No shipped page links a page this build did not ship (the front door and
//      story.html are both pruned above; this proves the pruning worked).
//
// It also runs ALONE against a tree somebody else built —
//     node tools/build-static.mjs --audit dist-c
// — so a deploy can be re-checked in three seconds without a 40-minute rebuild,
// and so this gate can be developed and calibrated against a real artifact.
function referenceAudit(OUT, deleted) {
  const have = new Set(walk(OUT).map(f => relative(OUT, f)));
  const inSrc = (rel) => existsSync(join(PUB, rel));
  const refs = new Map();                       // rel -> why
  const norm = (p) => p.split('?')[0].split('#')[0].replace(/^\.\//, '').replace(/^\/+/, '');
  const addRef = (p, why) => {
    if (!p || typeof p !== 'string') return;
    if (/^(https?:|data:|blob:|mailto:|javascript:|#|\/\/)/i.test(p)) return;
    const r = norm(p); if (!r) return;
    if (!refs.has(r)) refs.set(r, why);
  };
  const ASSET_EXT = /\.(png|webp|jpe?g|glb|gltf|mp3|ogg|wav|json|js|css|svg|html)$/i;
  const ROOTED = /^(assets|game|world|townmap|lib|js|docs)\//;

  // (a) pages: every src= / href= they carry, resolved against the page's own dir
  for (const rel of [...have].filter(r => r.endsWith('.html'))) {
    const h = readFileSync(join(OUT, rel), 'utf8');
    const dir = dirname(rel) === '.' ? '' : dirname(rel);
    for (const m of h.matchAll(/\b(?:src|href)\s*=\s*"([^"]+)"/g))
      addRef(dir ? join(dir, m[1]) : m[1], rel + ' src/href');
  }
  // (b) every shipped JSON, every string in it that looks like a path. A rooted
  //     path is from the site root; anything else is relative to the JSON itself,
  //     which is how a bundle's cine.json names its own plates (c.art.bg).
  for (const rel of [...have].filter(r => r.endsWith('.json'))) {
    let j; try { j = JSON.parse(readFileSync(join(OUT, rel), 'utf8')); } catch { continue; }
    const dir = dirname(rel);
    const rec = (v) => {
      if (typeof v === 'string') {
        if (ASSET_EXT.test(v) && !/[\s<>]/.test(v))
          addRef(ROOTED.test(v) ? v : join(dir, v), rel);
      } else if (Array.isArray(v)) v.forEach(rec);
      else if (v && typeof v === 'object') for (const k in v) rec(v[k]);
    };
    rec(j);
  }
  // (c) the names the RUNTIME BUILDS rather than reads — the ones no manifest
  //     spells out. dialogue.js: cutins.json says which cut-in moods were matted,
  //     and every portrait id has a neutral bust.
  const CUTINS_REL = 'assets/characters/cutins.json';
  if (existsSync(join(OUT, CUTINS_REL))) {
    const cj = JSON.parse(readFileSync(join(OUT, CUTINS_REL), 'utf8'));
    for (const [id, e] of Object.entries(cj)) {
      addRef(`assets/characters/${id}/cutin.png`, 'cutins.json manifest');
      for (const x of (e && e.expr) || []) addRef(`assets/characters/${id}/cutin-${x}.png`, 'cutins.json expr list');
    }
  }
  for (const r of have) { const m = r.match(/^assets\/characters\/([^/]+)\//);
    if (m) addRef(`assets/characters/${m[1]}/bust.png`, 'dialogue.js bustUrl() convention'); }

  const unresolved = [], deadLinks = [];
  for (const [p, why] of refs) {
    if (have.has(p)) continue;
    if (willSwap(p) && have.has(swapped(p))) continue;      // the shim finds it
    if (!inSrc(p)) continue;                                // never existed: a legal absence
    (p.endsWith('.html') ? deadLinks : unresolved).push(`${p}   <- ${why}`);
  }
  // (2) every deleted plate/portrait is reachable through the shim's own rule.
  //     In --audit mode nobody handed us the list, so it is RECOVERED from the two
  //     trees: a .png that public/ has and the build does not is a .png this build
  //     removed, whatever removed it.
  const gone = deleted || [...walk(PUB).map(f => relative(PUB, f))]
    .filter(r => r.endsWith('.png') && !have.has(r) && have.has(swapped(r)));
  const stranded = gone.filter(r => !willSwap(r) || !have.has(swapped(r)));

  // geometry first: it is the finding that costs the most to discover late, and a
  // gate that stops at the first complaint makes you run it N times for N problems.
  geometryAudit(OUT, have);

  if (stranded.length) die('the compression pass removed .png files the runtime shim cannot rewrite\n' +
    '(each of these is a silent 404 in the deployed game):\n  ' + stranded.slice(0, 30).join('\n  '));
  if (unresolved.length) die('these paths resolve in public/ and NOT in the build — the build moved them:\n  ' +
    unresolved.slice(0, 40).join('\n  '));
  if (deadLinks.length) die('these shipped pages link to a page this build did not ship:\n  ' +
    deadLinks.slice(0, 40).join('\n  '));
  // (4) A WARNING, DELIBERATELY NOT A FAILURE. Any .png basename that the webp pass
  //     converted, still written as a literal in a shipped module, is a candidate for
  //     the CSS-background blind spot patchPortraitUrls exists for — the runtime shim
  //     rescues it only if it is loaded through <img>.src or fetch, and nothing here
  //     can tell which. Warning, because a heuristic that fails a build is a heuristic
  //     that gets written around; loud, because this class shipped blank portraits.
  const convertedNames = new Set(gone.map(r => r.split('/').pop()));
  const suspects = [];
  for (const rel of [...have].filter(r => r.startsWith('js/') && r.endsWith('.js'))) {
    const src = readFileSync(join(OUT, rel), 'utf8');
    for (const m of src.matchAll(/['"`]([^'"`\s]*\.png)['"`]/g))
      if (convertedNames.has(m[1].split('/').pop())) suspects.push(`${rel}: ${m[1]}`);
  }
  if (suspects.length) {
    warn('shipped modules still name a .png this build converted to .webp. Each is fine ONLY');
    warn('if it is loaded through <img>.src or fetch (the shim rescues those) and BROKEN if it');
    warn('reaches the page as a CSS url(). See patchPortraitUrls:');
    for (const s of suspects.slice(0, 20)) warn('    ' + s);
  }

  log(`  reference integrity: ${refs.size} referenced paths all resolve` +
      (gone.length ? ` (${gone.length} via the .webp rewrite)` : ''));
}

// ---- THE GEOMETRY GATE ------------------------------------------------------
// A scene GLB in this repo is not scenery. It is the COLLISION AND WALK GEOMETRY:
// play3d reads its triangles for walkGround() and the body box, and CLAUDE.md's
// standing rule is that a walk floor moving by a centimetre is the class of defect
// that has already cost this repo a day. `--glb` runs the file through
// gltf-transform, which REPACKS the container — measured on emb-cine, 4760
// bufferViews become 2301 and every accessor is re-indexed and re-offset — so
// "the build only touched textures" is a claim, not a fact, until something checks
// it. This checks it: for every primitive of every shipped bundle, the POSITION
// bytes and the index bytes are digested out of BOTH files and must match exactly.
// It is the same shape of proof as the `glTF` magic check — read the artifact, do
// not believe the log — one level deeper.
function geometryAudit(OUT, have) {
  const COMP = { 5120: [Int8Array, 1], 5121: [Uint8Array, 1], 5122: [Int16Array, 2],
    5123: [Uint16Array, 2], 5125: [Uint32Array, 4], 5126: [Float32Array, 4] };
  const NCOMP = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
  function readGlb(p) {
    const buf = readFileSync(p);
    if (buf.length < 12 || buf.toString('latin1', 0, 4) !== 'glTF') return null;
    let off = 12, json = null, bin = null;
    const total = buf.readUInt32LE(8);
    while (off + 8 <= Math.min(total, buf.length)) {
      const len = buf.readUInt32LE(off), type = buf.toString('latin1', off + 4, off + 8);
      const body = buf.subarray(off + 8, off + 8 + len);
      if (type === 'JSON') json = JSON.parse(body.toString('utf8'));
      else if (type.startsWith('BIN')) bin = body;
      off += 8 + len;
    }
    return json && bin ? { json, bin } : null;
  }
  // the accessor's own bytes, DE-INTERLEAVED — a repack is free to change the
  // stride, so comparing raw bufferView slices would report a false difference.
  function accBytes(g, i) {
    const a = g.json.accessors[i], bv = g.json.bufferViews[a.bufferView];
    const [, sz] = COMP[a.componentType]; const n = NCOMP[a.type];
    const item = sz * n, stride = bv.byteStride || item;
    const base = (bv.byteOffset || 0) + (a.byteOffset || 0);
    const out = Buffer.alloc(item * a.count);
    for (let k = 0; k < a.count; k++) g.bin.copy(out, k * item, base + k * stride, base + k * stride + item);
    return out;
  }
  function digest(p) {
    const g = readGlb(p); if (!g) return null;
    const h = createHash('sha256');
    for (const m of g.json.meshes || []) for (const pr of m.primitives || []) {
      h.update(String(m.name || '') + '|');
      if (pr.attributes && pr.attributes.POSITION !== undefined) h.update(accBytes(g, pr.attributes.POSITION));
      if (pr.indices !== undefined) h.update(accBytes(g, pr.indices));
    }
    return h.digest('hex');
  }
  const bad = [], checked = [];
  for (const rel of [...have].filter(r => r.startsWith('assets/scenes/') && r.endsWith('.glb'))) {
    const src = join(PUB, rel); if (!existsSync(src)) continue;
    let a, b;
    try { a = digest(src); b = digest(join(OUT, rel)); }
    catch (e) { bad.push(`${rel}  (unreadable: ${e.message})`); continue; }
    if (a === null || b === null) { bad.push(`${rel}  (not parseable as binary glTF)`); continue; }
    checked.push(rel);
    if (a !== b) bad.push(`${rel}\n      public/ ${a}\n      build   ${b}`);
  }
  if (bad.length) die('the GLB pass MOVED GEOMETRY. These bundles are the walk and collision\n' +
    'meshes; a compression pass is only allowed to touch textures:\n  ' + bad.join('\n  ') +
    '\n\n  (in --audit mode there is a second reading: public/ has been rebuilt since this\n' +
    '   tree was, and what you are holding is a STALE deploy. Same action either way —\n' +
    '   rebuild — but check the bundle\'s mtime before you go looking in the compressor.)');
  log(`  scene geometry: ${checked.length} bundle GLBs byte-identical to public/ (POSITION + indices)`);
}

referenceAudit(OUT, WEBP_DELETED);

writeFileSync(join(OUT, 'BUILD.json'), JSON.stringify({
  built: new Date().toISOString(),
  generator: 'tools/build-static.mjs',
  // plateMax was MISSING from this record until 2026-08-03, which meant the one
  // build flag that changes what a plate LOOKS like could not be read back off a
  // deploy. It is also a cache key input, so it has to be written down.
  flags: { webp: WEBP, webpDepth: WEBP_DEPTH, glb: GLB, plateMax: PLATE_MAX, noDevScenes: NO_DEV_SCENES, story: KEEP_STORY },
  cache: NO_CACHE ? { enabled: false } : { enabled: true, hits: CACHE.hits, misses: CACHE.misses, stored: CACHE.stored, demoted: CACHE.errors },
  seconds: +((Date.now() - t0) / 1000).toFixed(1),
  totals: { bytes: total, files: files.length, byCategory: Object.fromEntries(CATS.map(c => [c, size[c]])) },
  scenes: perScene, cast: [...cast].sort(), missing: MISSING,
}, null, 2));
