#!/usr/bin/env node
/* ow_diag.mjs — INSPECT AND MUTATE the live overworld render, over CDP.
 *
 *   node tools/ow_diag.mjs                       # dump the shadow/light state
 *   node tools/ow_diag.mjs --out a.png           # ... and photograph it
 *   node tools/ow_diag.mjs --expr 'dl.castShadow=false' --out b.png
 *
 * WHY THIS EXISTS. ow_shot.mjs photographs whatever the page's own ?owlight=
 * flag produces, so every hypothesis costs a source edit to public/play3d.html
 * — which is coordinator-owned, and which makes a five-minute A/B into a commit.
 * This runs an arbitrary setup expression against the live scene graph first,
 * so a lighting hypothesis is a command line, not a diff. `R`, `scene`, `dl`,
 * `AMBIENT`, `RTLIGHT`, `cam` and `SIM` are all reachable: play3d's main script
 * is a CLASSIC script, so its top-level `const`s live in the global lexical
 * environment that Runtime.evaluate resolves against.
 *
 * IT DUMPS THE STATE IT ACTUALLY FOUND, always. An instrument that finds
 * nothing must prove it could have found something (CLAUDE.md): the dump names
 * the shadow-map texture, the caster/receiver counts and the frustum, so
 * "no shadows in the picture" can be separated from "no shadow pass ran".
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from './cdp.mjs';
import { mkArg } from './argv.mjs';

// `--k v` AND `--k=v` (tools/argv.mjs): the bare indexOf form silently

// ignored the `=` spelling and used the DEFAULT instead.

const { arg } = mkArg(process.argv);
const LIGHT = arg('light', '1'), SKY = arg('sky', '1'), OUT = arg('out', null);
const SCENE = arg('scene', 'ow-valley');
const PORT = parseInt(arg('port', '3000'), 10);
const QUIET = process.argv.includes('--quiet');
const CDP = parseInt(arg('cdp', '0'), 10) || await freePort();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL = `http://localhost:${PORT}/play.html?scene=${SCENE}&rt=1&owsky=${SKY}` +
            `&owlight=${LIGHT}&nomusic=1&v=${Date.now()}`;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = join(process.env.TMPDIR || '/tmp', 'ow-diag-profile');
killOrphans(profile); rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [`--remote-debugging-port=${CDP}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  // no --disable-gpu, for the same reason ow_shot.mjs gives: this tool photographs a render.
  '--window-size=1400,820', '--headless=new', URL], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) {}
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) {} };
process.on('exit', kill);
for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { kill(); process.exit(130); });

function connect(url) { return new Promise((res, rej) => {
  const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
  const pend = new Map(); let id = 0;
  ws.on('message', d => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
  ws.on('open', () => res({ send: (m, p = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method: m, params: p })); }), close: () => ws.close() }));
  ws.on('error', rej); }); }

const evalJS = async (cdp, expr) => {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  const d = r.result || {};
  if (d.exceptionDetails) return 'EXC ' + (d.exceptionDetails.exception?.description || JSON.stringify(d.exceptionDetails));
  return d.result ? d.result.value : undefined;
};

const DUMP = `JSON.stringify((()=>{ const o={};
  o.rendererShadow={enabled:R.shadowMap.enabled,type:R.shadowMap.type,autoUpdate:R.shadowMap.autoUpdate};
  o.dl={intensity:dl.intensity,castShadow:dl.castShadow,pos:dl.position.toArray(),
        target:dl.target.position.toArray(),targetInScene:!!dl.target.parent,inScene:!!dl.parent,
        color:'#'+dl.color.getHexString()};
  const c=dl.shadow.camera;
  o.shadowCam={left:c.left,right:c.right,top:c.top,bottom:c.bottom,near:c.near,far:c.far};
  o.shadowBias={bias:dl.shadow.bias,normalBias:dl.shadow.normalBias,radius:dl.shadow.radius};
  o.shadowMapTexture=dl.shadow.map?{w:dl.shadow.map.width,h:dl.shadow.map.height}:null;
  o.ambient={intensity:AMBIENT.intensity,color:'#'+AMBIENT.color.getHexString()};
  o.hemi=(typeof RTLIGHT!=='undefined'&&RTLIGHT)?{intensity:RTLIGHT.intensity}:null;
  let cast=0,recv=0,meshes=0,mats={},noRecv=[];
  scene.traverse(m=>{ if(!m.isMesh)return; meshes++;
    if(m.castShadow)cast++; if(m.receiveShadow)recv++;
    if(!m.receiveShadow&&m.visible)noRecv.push(m.name||'(anon)');
    for(const mm of (Array.isArray(m.material)?m.material:[m.material])) if(mm) mats[mm.type]=(mats[mm.type]||0)+1; });
  o.counts={meshes:meshes,casters:cast,receivers:recv}; o.matTypes=mats;
  o.notReceiving=noRecv.slice(0,40);
  o.cam={type:cam&&cam.type,pos:cam&&cam.position.toArray().map(v=>+v.toFixed(1))};
  o.player=SIM.pos();
  // --expr may hand a measurement back by assigning window.__report; the dump is
  // the only channel out, so anything an expression learns has to ride it.
  if(typeof window.__report!=='undefined') o.report=window.__report;
  return o; })(),null,1)`;

(async () => {
  const cdp = await connect(await findPage(CDP, { tries: 320, label: 'ow_diag' }));
  await cdp.send('Runtime.enable');
  let ok = false;
  for (let i = 0; i < 160; i++) {
    if (await evalJS(cdp, `(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`) === true) { ok = true; break; }
    await sleep(250);
  }
  if (!ok) { console.error('scene never populated'); kill(); process.exit(2); }
  await sleep(1200);

  const expr = arg('expr', null);
  if (expr) {
    // A material's shader program is compiled against the shadow config that was
    // live at compile time. Mutating R.shadowMap.enabled after the first frame is
    // therefore a no-op unless every material is re-flagged — the exact trap this
    // tool exists to test, so it is done for the caller, always.
    const r = await evalJS(cdp, `(()=>{try{ ${expr};
      scene.traverse(m=>{ if(!m.isMesh)return;
        for(const mm of (Array.isArray(m.material)?m.material:[m.material])) if(mm) mm.needsUpdate=true; });
      return 'ok'; }catch(e){ return 'EXC '+e.message } })()`);
    if (String(r).startsWith('EXC')) { console.error('expr failed:', r); kill(); process.exit(4); }
    await sleep(900);
  }
  if (!QUIET) console.log(await evalJS(cdp, DUMP));
  if (OUT) {
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
    const b64 = shot.result && shot.result.data;
    if (!b64) { console.error('no screenshot data'); kill(); process.exit(3); }
    mkdirSync(dirname(OUT), { recursive: true });
    writeFileSync(OUT, Buffer.from(b64, 'base64'));
    console.log('WROTE ' + OUT);
  }
  cdp.close(); kill(); process.exit(0);
})().catch(e => { console.error('FAILED:', e && e.message); kill(); process.exit(1); });
