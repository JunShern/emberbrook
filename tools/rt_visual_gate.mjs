/**
 * tools/rt_visual_gate.mjs — DOES THE EXPLORABLE WORLD ACTUALLY LOOK RIGHT.
 *
 *   node tools/rt_visual_gate.mjs --port 3000                     # check every scene
 *   node tools/rt_visual_gate.mjs --port 3000 --scene emb-townwalk
 *   node tools/rt_visual_gate.mjs --port 3000 --record            # write the ledger
 *   node tools/rt_visual_gate.mjs --port 3000 --shots docs/qa/rtvis/gate
 *   node tools/rt_visual_gate.mjs --selftest                      # 0.0 s, no browser
 *   node tools/rt_visual_gate.mjs --port 3000 --scene ow-valley --induce '^ground_valley'
 *                                                               # THE RED ARM
 *
 * =========================== WHY THIS EXISTS ==============================
 *
 * MEASURED 2026-08-12.  Nothing in this repo has ever looked at the walkable
 * town.  `walk_engine_gate` asks where a body may stand.  `cine_test` grades
 * PLATES.  `transition_test` counts GPU resources.  `glb_census` parses the
 * wire.  Three deploys in a row proved mesh attributes on the wire — and the
 * appearance of the scene the player explores was unverified BY CONSTRUCTION.
 *
 * What that hole was hiding, found the first time anybody looked:
 *
 *   emb-townwalk   3,918 of 8,367 drawn meshes wear a material that samples a
 *                  TEXTURE while their geometry carries NO UV ATTRIBUTE.
 *   townwalk       532 primitives, same shape.
 *
 * three.js samples an absent `uv` as (0,0), so every one of those meshes is
 * ONE TEXEL STRETCHED OVER THE WHOLE SURFACE — flat paint.  Every shingle
 * roof, every timber frame, every rubble wall and the ground itself.  The
 * CAUSE is one mechanism and it is not a bug in anybody's exporter: Emberbrook's
 * dressing drives its Image Textures from GENERATED/OBJECT coordinates at
 * `projection = BOX` (tri-planar), which Cycles renders natively and glTF
 * CANNOT EXPRESS.  The plate tier and the walkable tier are drawn by two
 * different projections and only one of them survives an export.
 *
 * THE DURABLE LAW: A BUNDLE THAT PARSES IS NOT A WORLD THAT DRAWS.  Every
 * instrument here reads either the file or the body; a texture that resolves
 * to a single texel is invisible to both.
 *
 * ============================ WHAT IT ASSERTS =============================
 *
 * Per scene, in REAL Chrome, against the DRAWN scene graph (not the file):
 *
 *  A. HARD, absolute, ledger-independent — these can never be "the baseline":
 *     A1  the page boots and `SIM` is live;
 *     A2  `SIM.gpu().collide !== 0` — the scene GLB is actually in (the
 *         arena_playtest lesson: modules self-arm ~250 ms before the bundle
 *         lands, and a probe that waits for the modules photographs an empty
 *         world at the default player position);
 *     A3  no uncaught exception and no console error;
 *     A4  at every viewpoint the frame is a PICTURE: not >=98% blown (>=250 in
 *         all three channels), not >=98% crushed (<=4), and not >=90% inside ONE
 *         16^3 colour bin.  The third one is the load-bearing one and it was
 *         earned: a viewpoint whose (unclamped) boom ends inside the terrain
 *         draws a flat mid-green field with the player floating in it — neither
 *         blown nor crushed, and the first two clauses passed it happily.
 *
 *  B. LEDGERED, i.e. a REGRESSION test against
 *     `docs/qa/rtvis/rt_visual.<scene>.json`, because the current numbers are
 *     terrible and a permanently-red gate is a gate that gets skipped:
 *     B1  `texNoUv.meshes` / `.tris` may not RISE (a fix lowers them; `--record`
 *         re-pins);
 *     B2  per viewpoint, `flatFrac` — the share of the frame those meshes
 *         actually PAINT, measured by hiding them and differencing the two
 *         renders — may not rise by more than `--tol` (default 0.60 points);
 *     B3  per viewpoint, `blownFrac` may not rise by more than `--tol`.
 *
 * B2 is the number that matters, and it is why this is not a glTF parser:
 * 1,477 broken primitives is a count, `flatFrac` is what the player is looking
 * at.  MEASURE THE PIXELS, NOT THE PLAN (`blockout_material_coverage`'s lesson,
 * paid for in this town).
 *
 * ========================== WHAT IT DOES NOT CATCH ========================
 *
 * Say it plainly, because the next person will trust this file more than it
 * deserves:
 *
 *  * IT IS NOT A LOOK GATE.  Wrong colour, wrong grade, wrong sun, a texture
 *    that loaded but is the wrong texture, z-fighting, a seam, a hole in the
 *    ground: all pass.  It has NO reference frames and NO perceptual judge.
 *  * IT ONLY SEES `--views`.  Five viewpoints is not a town.  A mesh nobody
 *    stands near is measured structurally (A/B1) and never in pixels.
 *  * A MESH THAT DRAWS NOTHING AT ALL IS INVISIBLE TO B2 by construction —
 *    hiding a mesh that was already contributing zero pixels changes zero
 *    pixels.  Missing geometry is `cine_test`/`walk_engine_gate`'s job.
 *  * IT CANNOT SEE INSIDE A TEXTURE.  A material with a `map` AND a `uv` is
 *    passed without ever asking whether the image decoded, or whether the UVs
 *    are sane (all-zero UVs pass B1 and look exactly like the defect above).
 *  * PROCEDURAL / VERTEX-COLOUR materials with no map are correct by design
 *    here and are not counted — so a material that SHOULD have had a texture
 *    and shipped with none is invisible to it.
 *  * IT IS BLIND TO ANIMATION, NPC behaviour, and anything past frame 1 of a
 *    viewpoint.
 *
 * ====================== PROVED RED BEFORE GREEN ===========================
 *
 * `ow-valley` is the one bundle in the tree with ZERO textured-but-UV-less
 * primitives, so it is the honest place to induce the fault.  BOTH ARMS WERE
 * RUN, and the wire one is the one that matters:
 *
 *  1. IN PAGE, reproducible, `--induce '^ground_valley'` deletes the `uv`
 *     attribute from the three drawn meshes of the valley floor:
 *       texNoUv 0 -> 3 meshes / 53,582 tris,
 *       flatFrac road-w 0% -> 97.0%, road-e 0% -> 62.5%,  exit 1, 4 FAILs.
 *     `--induce` matching nothing is itself a FAILURE — an instrument that
 *     finds nothing must prove it could have found something.
 *  2. ON THE WIRE.  Two symlink farms over the same `public/`, served by
 *     `python3 -m http.server` on two ports, differing ONLY in
 *     `assets/scenes/ow-valley/scene.glb`: the control is a faithful
 *     re-serialisation (58,006,228 B), the treatment has `TEXCOORD_0` deleted
 *     from `ground_valley`'s three primitives (58,006,184 B).
 *       CONTROL  exit 0, texNoUv 0, flatFrac 0% / 0%
 *       DOCTORED exit 1, texNoUv 3 / 53,582, flatFrac 97.0% / 62.5%
 *     A re-serialised-but-unmodified bundle passing is the half of that proof
 *     people skip, and it is what rules out "the farm itself broke the scene".
 *
 * ============================== COST ======================================
 *
 * One Chrome, one page load per scene, 3 renders per viewpoint (base, hidden,
 * restored) plus two full readPixels.  MEASURED on this laptop, warm server:
 * emb-townwalk alone 8 s, all three scenes 18 s, `--selftest` 0.05 s.  Cheap
 * enough for the standard gauntlet.
 *
 * DETERMINISM, AND IT COST ONE MEASUREMENT.  Inside one browser session the
 * numbers repeat to 0.04 points of frame.  ACROSS sessions they did not: at
 * `mill` the flat share read 34.9% and 77.4% on alternate runs, and the camera
 * position printed beside it says why — the boom was 0.75 m shorter, i.e.
 * play3d's CAMERA OCCLUSION CLAMP (`?camclip=0`) had not finished easing out.
 * The clamp is deliberately SNAP-IN / SLOW-OUT, so three rAFs after a teleport
 * it is still in flight, and 0.75 m of boom at that viewpoint is the difference
 * between standing outside the mill and standing in its wall.  A GATE MUST
 * PHOTOGRAPH A DEFINED POSE, so the probe boots with `?camclip=0` and the pose
 * is then a pure function of `ORBIT` — verified by the camera position being
 * byte-identical across sessions, which is the thing that is actually asserted.
 * `?nomusic=1&nostory=1&nofollow=1` and `Ambient.hide()` take out the rest.
 * Residual spread with the clamp off, three separate browser sessions:
 * <= 0.09 points of frame, against a `--tol` of 0.60.
 *
 * THE BASELINE THIS PINS, 2026-08-12 (`docs/qa/rtvis/rt_visual.*.json`):
 *
 *   scene          drawn  textured  texNoUv meshes/tris   flat share of frame
 *   emb-townwalk    8366      7166      3918 / 391,868    27-93%  (homerow 93.2)
 *   townwalk        2415       718       532 / 289,790    52-57%
 *   ow-valley         72        42           0 /       0    0% / 0%
 *
 * ow-valley is the proof that this is not how a bundle has to be: its dressing
 * is UV-mapped and it reads 0.
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync, readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage, sweepStaleProfiles } from './cdp.mjs';
import { mkArg } from './argv.mjs';

const { arg } = mkArg(process.argv);
const has = k => process.argv.includes('--' + k);
const REPO = '/Users/junshernchan/projects/multiplayer-rpg';
const LEDGER_DIR = join(REPO, 'docs/qa/rtvis');

// ---------------------------------------------------------------------------
// THE VIEWPOINTS ARE DATA, and every one of them is a cell the walk network
// says a body can stand on (checked with glb_read's own `tops()` over walk_*).
// A viewpoint that is not standable is not a place the player can look from,
// so it is not a place this gate is entitled to judge.
// ---------------------------------------------------------------------------
const SCENES = {
  'emb-townwalk': [
    { id: 'square', x: 66, z: -43, yaw: 2.6, pitch: 0.35, dist: 14 },
    { id: 'mill', x: 48, z: -56, yaw: -1.9, pitch: 0.30, dist: 14 },
    { id: 'pondlane', x: 79, z: -46, yaw: 0.4, pitch: 0.35, dist: 14 },
    { id: 'homerow', x: 52, z: -52, yaw: 1.2, pitch: 0.30, dist: 14 },
    { id: 'spawn', x: 62, z: -32, yaw: 0.79, pitch: 0.62, dist: 10 },
  ],
  'townwalk': [
    { id: 'court', x: 24, z: -24, yaw: 0.79, pitch: 0.35, dist: 14 },
    { id: 'shelf', x: 72, z: -32, yaw: 2.2, pitch: 0.35, dist: 14 },
  ],
  'ow-valley': [
    { id: 'road-w', x: -24, z: 16, yaw: 0.79, pitch: 0.45, dist: 30 },
    { id: 'road-e', x: 8, z: -16, yaw: 2.4, pitch: 0.45, dist: 30 },
  ],
};

const TOL = parseFloat(arg('tol', '0.60'));      // percentage POINTS of frame

// ===========================================================================
// The in-page probe.  Everything it needs lives in play3d.html's own global
// lexical scope (`scene` is a top-level `const` in a classic script, which is
// the same door followers.js/npc.js already come through) plus window.SIM.
// ===========================================================================
const PROBE = (views, induce, settle) => `(async()=>{
 const raf=()=>new Promise(r=>requestAnimationFrame(()=>r()));
 const S=window.SIM;
 if(!S||!S.pos) return {fatal:'SIM absent'};
 let root=null; try{ root=scene; }catch(e){ return {fatal:'scene root unreachable: '+e.message}; }
 try{ if(window.Ambient&&Ambient.hide) Ambient.hide(true); }catch(e){}

 // ---- structural census over the DRAWN scene -----------------------------
 // "drawn" = isMesh and every ancestor visible.  A mesh the page has parked
 // invisible is not a mesh the player is looking at, and counting it would
 // make the gate red about something that does not exist on screen.
 const SLOTS=['map','normalMap','roughnessMap','metalnessMap','aoMap','emissiveMap',
              'alphaMap','specularMap','clearcoatMap','sheenColorMap'];
 const drawn=[]; root.traverse(o=>{ if(!o.isMesh) return;
   for(let p=o;p;p=p.parent) if(!p.visible) return;
   drawn.push(o); });
 const byMat={}; let texNoUvMeshes=0, texNoUvTris=0, texMeshes=0;
 const bad=[];
 for(const o of drawn){
   const g=o.geometry, mats=Array.isArray(o.material)?o.material:[o.material];
   const n=o.isInstancedMesh?o.count:1;
   const tri=(g.index?g.index.count:(g.attributes.position?g.attributes.position.count:0))/3*n;
   let anyTex=false, miss=null;
   for(const m of mats){ if(!m) continue;
     for(const s of SLOTS){ const t=m[s]; if(!t) continue; anyTex=true;
       const ch=(t.channel|0);
       const attr=ch===0?'uv':('uv'+ch);
       if(!g.attributes[attr]) miss=(m.name||m.type)+'#'+s+'@'+attr; } }
   if(anyTex) texMeshes++;
   if(miss){ texNoUvMeshes++; texNoUvTris+=tri; bad.push(o);
     const k=miss.split('#')[0];
     (byMat[k]=byMat[k]||{meshes:0,tris:0,slot:miss.split('#')[1],names:[]});
     byMat[k].meshes++; byMat[k].tris+=tri;
     if(byMat[k].names.length<3) byMat[k].names.push(o.name||'(unnamed)'); }
 }
 ${induce ? `
 // --- INDUCED FAULT: strip the uv attribute from meshes matching a regex, in
 // the page, so the assertion can be shown firing on a tree that passes.
 { const re=new RegExp(${JSON.stringify(induce)});
   let n=0; for(const o of drawn){ if(!re.test(o.name||'')) continue;
     if(o.geometry.attributes.uv){ o.geometry.deleteAttribute('uv'); n++; } }
   if(n===0) return {fatal:'--induce matched no drawn mesh with a uv attribute — AN INSTRUMENT THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING'};
   return Object.assign(await measure(), {induced:n}); }
 ` : ''}
 async function measure(){
   // re-run the census after any induction
   const b2=[]; let m2=0,t2=0; const bm2={};
   for(const o of drawn){
     const g=o.geometry, mats=Array.isArray(o.material)?o.material:[o.material];
     const n=o.isInstancedMesh?o.count:1;
     const tri=(g.index?g.index.count:(g.attributes.position?g.attributes.position.count:0))/3*n;
     let miss=null;
     for(const m of mats){ if(!m) continue;
       for(const s of SLOTS){ const t=m[s]; if(!t) continue;
         const attr=(t.channel|0)===0?'uv':('uv'+(t.channel|0));
         if(!g.attributes[attr]) miss=(m.name||m.type)+'#'+s+'@'+attr; } }
     if(miss){ m2++; t2+=tri; b2.push(o); const k=miss.split('#')[0];
       (bm2[k]=bm2[k]||{meshes:0,tris:0,slot:miss.split('#')[1],names:[]});
       bm2[k].meshes++; bm2[k].tris+=tri;
       if(bm2[k].names.length<3) bm2[k].names.push(o.name||'(unnamed)'); } }

   const SETTLE=${settle};
   const cv=document.querySelector('canvas');
   const ctx=cv.getContext('webgl2')||cv.getContext('webgl');
   const W=cv.width,H=cv.height,N=W*H;
   const grab=()=>{ S.tick(0); const px=new Uint8Array(N*4);
     ctx.readPixels(0,0,W,H,ctx.RGBA,ctx.UNSIGNED_BYTE,px); return px; };
   const out=[];
   for(const v of ${JSON.stringify(views)}){
     S.tp(v.x,v.z);
     window.ORBIT.yaw=v.yaw; window.ORBIT.pitch=v.pitch; window.ORBIT.dist=v.dist;
     window.ORBIT.panX=window.ORBIT.panY=window.ORBIT.panZ=0;
     for(let k=0;k<SETTLE;k++) await raf();
     const cam=S.cam();
     const a=grab();
     let blown=0, crushed=0; const bins=new Int32Array(4096);
     for(let i=0;i<N;i++){ const r=a[i*4],g2=a[i*4+1],b=a[i*4+2];
       if(r>=250&&g2>=250&&b>=250) blown++;
       else if(r<=4&&g2<=4&&b<=4) crushed++;
       bins[((r>>4)<<8)|((g2>>4)<<4)|(b>>4)]++; }
     let modal=0, nbins=0; for(let i=0;i<4096;i++){ if(bins[i]){ nbins++; if(bins[i]>modal) modal=bins[i]; } }
     // FLAT SHARE: hide the offenders and difference.  An A/B against the same
     // frame is immune to the post chain — a magenta paint pass is NOT (measured:
     // tone mapping lifts pure magenta's green channel past any fixed threshold).
     const vis=b2.map(o=>o.visible); for(const o of b2) o.visible=false;
     const c=grab();
     b2.forEach((o,i)=>o.visible=vis[i]);
     let flat=0;
     for(let i=0;i<N;i++){
       const d=Math.abs(a[i*4]-c[i*4])+Math.abs(a[i*4+1]-c[i*4+1])+Math.abs(a[i*4+2]-c[i*4+2]);
       if(d>12) flat++; }
     out.push({id:v.id, W, H, cam:cam.pos, fwd:cam.fwd,
       blownFrac:+(100*blown/N).toFixed(3),
       crushedFrac:+(100*crushed/N).toFixed(3),
       modalFrac:+(100*modal/N).toFixed(3), colourBins:nbins,
       flatFrac:+(100*flat/N).toFixed(3)});
     await raf();
   }
   const gpu=S.gpu();
   return {drawn:drawn.length, texMeshes, texNoUv:{meshes:m2, tris:Math.round(t2)},
     byMat:Object.fromEntries(Object.entries(bm2).sort((x,y)=>y[1].meshes-x[1].meshes).slice(0,20)
       .map(([k,v])=>[k,{meshes:v.meshes,tris:Math.round(v.tris),slot:v.slot,eg:v.names}])),
     gpu:{collide:gpu.collide, meshes:gpu.meshes, walk:gpu.walk, geometries:gpu.geometries},
     views:out, canvas:[document.querySelector('canvas').width,document.querySelector('canvas').height]};
 }
 return await measure();
})()`;

// ===========================================================================
function judge(scene, m, led) {
  const fail = [], warn = [];
  if (m.fatal) { fail.push(`A1 ${scene}: ${m.fatal}`); return { fail, warn }; }
  if (!m.gpu || m.gpu.collide === 0)
    fail.push(`A2 ${scene}: SCENE NOT LOADED — SIM.gpu().collide === 0 (the probe photographed an empty world)`);
  for (const v of m.views || []) {
    if (v.blownFrac >= 98) fail.push(`A4 ${scene}/${v.id}: frame ${v.blownFrac}% blown white — not a picture`);
    if (v.crushedFrac >= 98) fail.push(`A4 ${scene}/${v.id}: frame ${v.crushedFrac}% crushed black — not a picture`);
    // A camera buried in the world draws ONE colour and is neither blown nor crushed.
    // `modalFrac` is the share of the frame in the single fullest 16^3 colour bin.
    if (v.modalFrac >= 90) fail.push(`A4 ${scene}/${v.id}: ${v.modalFrac}% of the frame is ONE colour (${v.colourBins} bins) — the camera is drawing a void, not a place`);
  }
  if (!led) { warn.push(`no ledger for ${scene} — run --record (regression checks B1/B2/B3 skipped)`); return { fail, warn }; }
  if (m.texNoUv.meshes > led.texNoUv.meshes)
    fail.push(`B1 ${scene}: meshes sampling a texture with no UV ${led.texNoUv.meshes} -> ${m.texNoUv.meshes}`);
  if (m.texNoUv.tris > led.texNoUv.tris)
    fail.push(`B1 ${scene}: their triangles ${led.texNoUv.tris} -> ${m.texNoUv.tris}`);
  const byId = Object.fromEntries((led.views || []).map(v => [v.id, v]));
  for (const v of m.views || []) {
    const b = byId[v.id]; if (!b) { warn.push(`${scene}/${v.id}: not in the ledger`); continue; }
    if (v.flatFrac > b.flatFrac + TOL)
      fail.push(`B2 ${scene}/${v.id}: flat-paint share of frame ${b.flatFrac}% -> ${v.flatFrac}% (tol ${TOL})`);
    if (v.blownFrac > b.blownFrac + TOL)
      fail.push(`B3 ${scene}/${v.id}: blown share ${b.blownFrac}% -> ${v.blownFrac}% (tol ${TOL})`);
  }
  return { fail, warn };
}

// --- the judgement is pure, so it is testable with no browser at all --------
if (has('selftest')) {
  const base = { gpu: { collide: 31 }, texNoUv: { meshes: 10, tris: 100 }, views: [{ id: 'a', blownFrac: 1, crushedFrac: 1, flatFrac: 5, modalFrac: 20, colourBins: 300 }] };
  const led = JSON.parse(JSON.stringify(base));
  const cases = [
    ['clean', base, led, 0],
    ['scene not loaded', { ...base, gpu: { collide: 0 } }, led, 1],
    ['boot failed', { fatal: 'SIM absent' }, led, 1],
    ['blown frame', { ...base, views: [{ id: 'a', blownFrac: 99, crushedFrac: 0, flatFrac: 5, modalFrac: 99, colourBins: 1 }] }, led, 1],
    ['crushed frame', { ...base, views: [{ id: 'a', blownFrac: 0, crushedFrac: 99, flatFrac: 5, modalFrac: 99, colourBins: 1 }] }, led, 1],
    ['camera buried in the world', { ...base, views: [{ id: 'a', blownFrac: 0, crushedFrac: 0, flatFrac: 0, modalFrac: 97, colourBins: 12 }] }, led, 1],
    ['more broken meshes', { ...base, texNoUv: { meshes: 11, tris: 100 } }, led, 1],
    ['fewer broken meshes is FINE', { ...base, texNoUv: { meshes: 2, tris: 10 } }, led, 0],
    ['flat share up past tol', { ...base, views: [{ id: 'a', blownFrac: 1, crushedFrac: 1, flatFrac: 5.7, modalFrac: 20, colourBins: 300 }] }, led, 1],
    ['flat share up inside tol', { ...base, views: [{ id: 'a', blownFrac: 1, crushedFrac: 1, flatFrac: 5.5, modalFrac: 20, colourBins: 300 }] }, led, 0],
    ['no ledger => warn, not fail', base, null, 0],
  ];
  let bad = 0;
  for (const [name, m, l, want] of cases) {
    const r = judge('x', m, l);
    const got = r.fail.length ? 1 : 0;
    console.log(`${got === want ? 'ok  ' : 'FAIL'} ${name}${r.fail.length ? '  <- ' + r.fail[0] : ''}`);
    if (got !== want) bad++;
  }
  console.log(bad ? `SELFTEST ${bad} FAILED` : `SELFTEST ${cases.length}/${cases.length} ok`);
  process.exit(bad ? 1 : 0);
}

// ===========================================================================
const PORT = parseInt(arg('port', '3000'), 10);
const ONLY = (arg('scene', '') || '').split(',').filter(Boolean);
const LIST = ONLY.length ? ONLY : Object.keys(SCENES);
const SHOTS = arg('shots', '');
const INDUCE = arg('induce', '');
const REPEAT = parseInt(arg('repeat', '1'), 10);
const SETTLE = parseInt(arg('settle', '3'), 10);
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = join(process.env.TMPDIR || '/tmp', 'rtvisgate-profile');
sweepStaleProfiles('rtvisgate-');
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const CDP = await freePort();
const url = s => `http://localhost:${PORT}/play3d.html?scene=${s}&nomusic=1&nostory=1&nofollow=1&camclip=0&v=${Date.now()}`;
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--mute-audio',
  '--window-size=1400,820', '--headless=new', url(LIST[0])], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true; try { chrome.kill('SIGKILL') } catch (e) { }; try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }) } catch (e) { } };
process.on('exit', kill); for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130) });

const CONSOLE = [];
function connect(u) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(u, { perMessageDeflate: false, maxPayload: 512 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('message', d => {
      const m = JSON.parse(d.toString());
      if (m.method === 'Runtime.consoleAPICalled' && /error/.test(m.params.type || ''))
        CONSOLE.push('console.' + m.params.type + ': ' + (m.params.args || []).map(a => a.value || a.description || '').join(' ').slice(0, 200));
      if (m.method === 'Runtime.exceptionThrown')
        CONSOLE.push('EXCEPTION: ' + (((m.params.exceptionDetails || {}).exception) || {}).description);
      if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id) }
    });
    ws.on('open', () => res({ send: (mm, p = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method: mm, params: p })) }), close: () => ws.close() }));
    ws.on('error', rej);
  });
}
const ev = async (cdp, e) => {
  const r = await cdp.send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true });
  const d = r.result || {};
  if (d.exceptionDetails) return { fatal: 'EXC ' + (d.exceptionDetails.exception?.description || JSON.stringify(d.exceptionDetails)).slice(0, 300) };
  return d.result ? d.result.value : undefined;
};
// READY IS THE BUNDLE, NOT THE MODULES.  arena_playtest's own week-long red was a
// readiness gate that waited for the self-arming modules and photographed the
// default player position in an empty world 250 ms before the GLB landed.
async function waitLive(cdp) {
  for (let i = 0; i < 600; i++) {
    const r = await ev(cdp, `(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x)&&SIM.gpu&&SIM.gpu().collide>0)}catch(e){return false}})()`);
    if (r === true) return true;
    await sleep(250);
  }
  return false;
}

const t0 = Date.now();
const cdp = await connect(await findPage(CDP, { tries: 400, label: 'rt_visual_gate' }));
await cdp.send('Runtime.enable'); await cdp.send('Log.enable').catch(() => { });
const report = { generated: new Date().toISOString(), port: PORT, tol: TOL, scenes: {} };
let FAIL = [], WARN = [];
let first = true;
for (const sc of LIST) {
  const views = SCENES[sc]; if (!views) { WARN.push(`unknown scene ${sc}`); continue; }
  if (!first) { await cdp.send('Page.navigate', { url: url(sc) }); await sleep(1200); }
  first = false;
  const cbefore = CONSOLE.length;
  if (!await waitLive(cdp)) { FAIL.push(`A1/A2 ${sc}: never became live (SIM absent or collide===0 after 150 s)`); continue; }
  await sleep(2500);
  const runs = [];
  for (let r = 0; r < REPEAT; r++) runs.push(await ev(cdp, PROBE(views, INDUCE, SETTLE)));
  const m = runs[0];
  if (REPEAT > 1) {
    m.repeat = views.map((v, i) => ({
      id: v.id,
      flatFrac: runs.map(rr => rr.views[i].flatFrac),
      blownFrac: runs.map(rr => rr.views[i].blownFrac),
    }));
  }
  const errs = CONSOLE.slice(cbefore).filter(x => !/404 \(Not Found\)/.test(x));
  if (errs.length) FAIL.push(`A3 ${sc}: ${errs.length} console error(s): ${errs[0]}`);
  const ledPath = join(LEDGER_DIR, `rt_visual.${sc}.json`);
  const led = existsSync(ledPath) && !has('record') ? JSON.parse(readFileSync(ledPath, 'utf8')) : null;
  const j = judge(sc, m, led);
  FAIL = FAIL.concat(j.fail); WARN = WARN.concat(j.warn);
  report.scenes[sc] = m;
  if (m.fatal) { console.log(`\n== ${sc}   FATAL: ${m.fatal}`); continue; }
  if (SHOTS) {
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
    mkdirSync(SHOTS, { recursive: true });
    writeFileSync(join(SHOTS, sc + '.png'), Buffer.from(shot.result.data, 'base64'));
  }
  if (has('record') && !INDUCE) {
    mkdirSync(LEDGER_DIR, { recursive: true });
    writeFileSync(ledPath, JSON.stringify({
      scene: sc, recorded: report.generated, drawn: m.drawn, texMeshes: m.texMeshes,
      texNoUv: m.texNoUv, byMat: m.byMat, gpu: m.gpu,
      views: m.views,
    }, null, 1) + '\n');
    console.log(`RECORDED ${ledPath}`);
  }
  console.log(`\n== ${sc}   drawn ${m.drawn} meshes, ${m.texMeshes} textured`);
  console.log(`   texture-with-no-UV: ${m.texNoUv.meshes} meshes / ${m.texNoUv.tris} tris`
    + (m.induced !== undefined ? `   [INDUCED on ${m.induced} meshes]` : ''));
  for (const v of m.views) console.log(`   ${v.id.padEnd(10)} flat ${String(v.flatFrac).padStart(7)}%   blown ${String(v.blownFrac).padStart(6)}%   crushed ${String(v.crushedFrac).padStart(6)}%   modal ${String(v.modalFrac).padStart(6)}%   cam ${(v.cam||[]).join(',')}`);
  if (m.repeat) for (const r of m.repeat) console.log(`   repeat ${r.id.padEnd(10)} flat ${r.flatFrac.join(' ')}  blown ${r.blownFrac.join(' ')}`);
}
const out = arg('out', join(LEDGER_DIR, 'rt_visual_run.json'));
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, JSON.stringify({ ...report, fail: FAIL, warn: WARN }, null, 1) + '\n');
console.log(`\nwrote ${out}   (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
for (const w of WARN) console.log('WARN ' + w);
for (const f of FAIL) console.log('FAIL ' + f);
console.log(FAIL.length ? `\nrt_visual_gate: ${FAIL.length} FAILED` : `\nrt_visual_gate: OK`);
cdp.close(); kill();
process.exit(FAIL.length ? 1 : 0);
