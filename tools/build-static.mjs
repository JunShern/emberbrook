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
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync, readdirSync, rmSync, copyFileSync, renameSync } from 'fs';
import { join, dirname, relative, basename } from 'path';
import { execFileSync } from 'child_process';
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

const log = (...a) => console.log(...a);
const warn = (...a) => console.warn('  ! ', ...a);
const die = (m) => { console.error('\nBUILD FAILED: ' + m + '\n'); process.exit(1); };

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
if (KEEP_STORY) claim('story.html', 'code', 'story/world review page (linked from the front door)');

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
  if (SHIPPED_REVIEW.has('townmap/viewer.html')) {
    claim(`townmap/${t}.cameras.json`, 'code', 'townmap viewer (linked from the front door)');
    claim(`townmap/${t}.cameras.solved.json`, 'code', 'townmap viewer');
  }
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
for (const p of PLAN) {
  mkdirSync(dirname(p.dest), { recursive: true });
  if (p.inline != null) writeFileSync(p.dest, p.inline);
  else copyFileSync(p.src, p.dest);
}

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
  const targets = walk(OUT).filter(f => {
    const r = relative(OUT, f);
    if (!f.endsWith('.png') || NEVER_LOSSY.test(r)) return false;
    if (/(^|\/)(bg|background|stylized|main|festival|gray|open)\.png$/.test(r)) return true;
    // portraits: busts, cut-ins and expression plates. Pictures, every one — the
    // runtime draws them and never samples them.
    return r.startsWith('assets/characters/') && r.endsWith('.png');
  });
  const depth = WEBP_DEPTH ? walk(OUT).filter(f => NEVER_LOSSY.test(relative(OUT, f))) : [];
  const listFile = join(ROOT, '.webp-list.tmp');
  writeFileSync(listFile, JSON.stringify({ lossy: targets, lossless: depth, plateMax: PLATE_MAX }));
  try {
    const out = execFileSync('python3', [py, listFile], { encoding: 'utf8', maxBuffer: 1 << 28 });
    log(out.trim().split('\n').map(l => '    ' + l).join('\n'));
  } catch (e) {
    die('--webp pass failed (depth round-trip check is fatal by design):\n' + (e.stdout || '') + (e.stderr || e.message));
  } finally { rmSync(listFile, { force: true }); rmSync(py, { force: true }); }
  // rewrite the references the runtime builds by name
  patchPlateExtensions();
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
    h = h.replace(/<script/, `<script>/*EB_WEBP_SHIM*/(function(){
  var RE=/((^|\\/)(bg|background|stylized|main|festival|gray|open)\\.png(\\?|$))|(assets\\/characters\\/[^?]*\\.png(\\?|$))/;
  var D=/(^|\\/)(depth|mask|maskraw)[\\w-]*\\.png/i;
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
  let before = 0, after = 0;
  for (const g of glbs) {
    const b0 = statSync(g).size; before += b0;
    // textures first: draco shrinks the buffer the texture pass would otherwise
    // have to walk, and running it second keeps each step's log honest.
    const t1 = g + '.webp', t2 = g + '.draco';
    run(['webp', g, t1]); rmSync(g); renameSync(t1, g);
    run(['draco', g, t2]); rmSync(g); renameSync(t2, g);
    const b1 = statSync(g).size; after += b1;
    log(`    ${relative(OUT, g).padEnd(44)} ${(b0 / 1048576).toFixed(1)} -> ${(b1 / 1048576).toFixed(1)} MB`);
  }
  log(`    GLB total ${(before / 1048576).toFixed(0)} MB -> ${(after / 1048576).toFixed(0)} MB`);
  // decoder + loader into dist, and wire it into every page that makes a GLTFLoader
  mkdirSync(join(OUT, 'lib/draco'), { recursive: true });
  for (const f of readdirSync(vendor)) copyFileSync(join(vendor, f), join(OUT, 'lib/draco', f));
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
log('\n  compression: webp=' + (WEBP ? 'ON' : 'off') + '  webp-depth=' + (WEBP_DEPTH ? 'ON' : 'off (depth.png stays lossless PNG)') + '  glb=' + (GLB ? 'ON' : 'off'));
log('='.repeat(72) + '\n');

writeFileSync(join(OUT, 'BUILD.json'), JSON.stringify({
  built: new Date().toISOString(),
  generator: 'tools/build-static.mjs',
  flags: { webp: WEBP, webpDepth: WEBP_DEPTH, glb: GLB, noDevScenes: NO_DEV_SCENES, story: KEEP_STORY },
  totals: { bytes: total, files: files.length, byCategory: Object.fromEntries(CATS.map(c => [c, size[c]])) },
  scenes: perScene, cast: [...cast].sort(), missing: MISSING,
}, null, 2));
