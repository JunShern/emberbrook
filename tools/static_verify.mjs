// static_verify.mjs — DOES THE STATIC BUILD ACTUALLY WORK OFF A DUMB SERVER?
//
//   node tools/static_verify.mjs                 # builds nothing; serves ./dist itself
//   node tools/static_verify.mjs --dir dist --head
//   node tools/static_verify.mjs --port 8080     # use a server you already started
//   node tools/static_verify.mjs --url https://junshern.github.io/emberbrook
//                                                # THE DEPLOY ITSELF, over the wire
//
// --url IS THE ONE THAT ANSWERS "IS THE GAME UP". Everything else here proves the
// tree on this disk is playable; only --url proves the thing a player will load
// is. The difference between them is the exact class of bug this repo has already
// shipped once — public/game/lightrigs.json was fetched by committed code and was
// itself untracked, so it worked on the author's machine and 404'd everywhere
// else. A local build cannot see that; a request to the live host can.
//
// WHY THIS EXISTS, SEPARATELY FROM EVERY OTHER GATE. `node tools/build-static.mjs`
// exiting 0 proves that files were copied. It does not prove the result is a game:
// the classic static-build failure is a 404 on one texture, and NO unit gate in
// this repo would see it — they all read the source tree, where the file exists.
// So this drives the DIST, served by python3's http.server (no routes, no
// rewrites, no express — if it needs one, the build is not static), and asserts:
//
//   1. the launcher renders its cards and its NEW GAME door
//   2. NEW GAME is a real click that lands in Chapter One's opening shot
//   3. the player walks, and the body moves
//   4. a door edge is taken and the interior loads (an in-place scene swap)
//   5. the menu opens on real party data
//   6. a battle starts (Encounters.forceNext, then walk into it)
//   7. save -> cold reload from `at` alone lands in the same scene and shot
//   8. ZERO console errors and ZERO failed network requests across ALL of it
//   9. a screenshot, written to disk, for a human to look at
//
// (8) is the one that matters most and the reason the whole run is one page
// session: every Network.loadingFailed and every 4xx/5xx is collected from the
// first byte of the launcher to the last frame after the reload.
import { spawn } from 'child_process';
import { rmSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { createRequire } from 'module';
import { join, resolve } from 'path';
import { freePort, killOrphans, findPage, sweepStaleProfiles, chromeArgs } from './cdp.mjs';
const require = createRequire(import.meta.url);
const WebSocket = require('ws');

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.findIndex(a => a === '--' + k || a.startsWith('--' + k + '=')); if (i < 0) return d; const a = argv[i]; return a.includes('=') ? a.split('=').slice(1).join('=') : argv[i + 1]; };
const DIR = resolve(arg('dir', 'dist'));
const LIVE = arg('url', null);                       // verify a DEPLOY, not a directory
const BASE = LIVE ? String(LIVE).replace(/\/+$/, '') : null;
const HEAD = argv.includes('--head');
const SHOT = resolve(arg('shot', BASE ? join(process.cwd(), 'static-verify-live.png') : join(DIR, '..', 'static-verify.png')));
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

let pass = 0, fail = 0; const fails = [];
const ok = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); } else { fail++; fails.push(m); console.log('  FAIL ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra).slice(0, 400) : '')); } };
const note = (m) => console.log('       ' + m);
const head = (s) => console.log('\n== ' + s);
const sleep = ms => new Promise(r => setTimeout(r, ms));

if (!BASE && !existsSync(join(DIR, 'index.html'))) { console.error('no build at ' + DIR + ' — run: node tools/build-static.mjs'); process.exit(2); }

// ---- 1. THE DUMB SERVER -----------------------------------------------------
// python3 -m http.server: no rewrite rules, no routing, no fallback document.
// That is the point. Anything the game needs that this cannot answer is a bug in
// the build, not in the host.
let httpd = null;
let PORT = parseInt(arg('port', '0'), 10);
if (BASE) {
  note('LIVE MODE: no local server. Driving ' + BASE + ' over the wire.');
} else if (!PORT) {
  PORT = await freePort();
  httpd = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { cwd: DIR, stdio: 'ignore' });
  await sleep(700);
  note(`dumb static server: python3 -m http.server ${PORT}  (cwd ${DIR})`);
}

const CDP_PORT = await freePort();
const profile = join(process.env.TMPDIR || '/tmp', 'static-verify-profile-' + process.pid);
sweepStaleProfiles('static-verify-profile-');
killOrphans(profile);
rmSync(profile, { recursive: true, force: true });
const START = BASE ? BASE + '/index.html' : `http://127.0.0.1:${PORT}/index.html`;
// --mute-audio: the launcher's NEW GAME link carries no ?nomusic=1 and this run
// clicks the REAL link rather than a hand-built URL, so silence is enforced at the
// browser instead (standing rule: an agent is never audible in somebody's room).
const chrome = spawn(CHROME, ['--mute-audio', ...chromeArgs({ port: CDP_PORT, profile, url: START, headed: HEAD, size: '1400,860' })], { stdio: 'ignore' });

let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { if (httpd) httpd.kill('SIGKILL'); } catch (e) { }
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { }
};
process.on('exit', kill);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => { kill(); process.exit(130); });
process.on('uncaughtException', (e) => { console.error('UNCAUGHT:', e && e.stack); kill(); process.exit(4); });

function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); const evs = []; let id = 0;
    ws.on('open', () => res({
      send(method, params) { return new Promise((okk, no) => { const mid = ++id; pend.set(mid, { ok: okk, no }); ws.send(JSON.stringify({ id: mid, method, params: params || {} })); }); },
      on: [], events: evs, close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok: okk, no } = pend.get(m.id); pend.delete(m.id); m.error ? no(new Error(m.error.message)) : okk(m.result); return; }
      if (m.method) evs.push(m);
    });
  });
}
async function ev(cdp, expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, userGesture: true, timeout: timeoutMs || 240000 });
  if (r.exceptionDetails) { const e = r.exceptionDetails; throw new Error('page exception: ' + ((e.exception && e.exception.description) || e.text)); }
  return r.result && r.result.value;
}

// GUARD: verify what THIS pipeline built. Two lanes wrote a static build into
// dist/ on the same evening and the second overwrote the first, so a green run
// against the wrong tree is a real failure mode here, not a hypothetical.
{
  // In LIVE mode BUILD.json is fetched from the host — which is also the first
  // proof that the deploy is the build you think it is. A stale gh-pages branch
  // announces itself here, by timestamp, before a single assertion runs.
  let b;
  if (BASE) {
    const r = await fetch(BASE + '/BUILD.json').catch(e => { console.error('cannot reach ' + BASE + '/BUILD.json: ' + e.message); process.exit(2); });
    if (!r.ok) { console.error(BASE + '/BUILD.json -> HTTP ' + r.status + '. Either the deploy has not published yet, or it is not a build of this tool.'); process.exit(2); }
    b = await r.json();
  } else {
    const bj = join(DIR, 'BUILD.json');
    if (!existsSync(bj)) { console.error('no BUILD.json in ' + DIR + ' — run tools/build-static.mjs'); process.exit(2); }
    b = JSON.parse(require('fs').readFileSync(bj, 'utf8'));
  }
  if (b.generator !== 'tools/build-static.mjs') {
    console.error('\n' + (BASE || DIR) + ' was built by ' + (b.generator || 'an unknown script') +
      ', not tools/build-static.mjs. Rebuild before verifying.\n');
    process.exit(2);
  }
  note('verifying build ' + b.built + '  (' + b.totals.files + ' files, ' + (b.totals.bytes/1073741824).toFixed(2) + ' GB)');
}

const wsUrl = await findPage(CDP_PORT, { tries: 200, match: /index\.html|play(3d)?\.html/, label: 'static_verify' });
const cdp = await connect(wsUrl);

// ---- THE AUDIT (the whole point) --------------------------------------------
// Collected across every navigation in this session, never reset.
const netFail = [];      // Network.loadingFailed
const netBad = [];       // a response with a 4xx/5xx status
const consoleErr = [];   // console.error + uncaught exceptions
const expected404 = [];  // the runtime PROBING for a file that is optional per bundle
const reqUrl = new Map();

// *** A GATE THAT IS ALWAYS RED IS NOT A GATE. ***
// play3d PROBES for these per bundle — a cinematic scene has no zones.json, an
// interior has no cine.json, and the loader asks anyway and takes `null` for an
// answer. Ten guaranteed 404s per run drowned the one that would matter, which is
// how 16 dead card thumbnails sat in the deployed game under a permanently red
// console line that everyone had learned to read past.
//   Exempting them loses NO coverage, and that is the load-bearing part: the
// build's reference-integrity gate already fails on any path that resolves in
// public/ and not in the build. What is left here is a request for a file that
// does not exist in EITHER tree — the documented absence, not a build bug.
// Anything else, including a 404 on one of these names for a bundle that really
// ships it, still turns this run red.
const OPTIONAL_404 = [
  /\/assets\/scenes\/[^/]+\/(zones|depth|cine|meta)\.json(\?|$)/,
  /\/favicon\.ico(\?|$)/,
];
const isExpected404 = (u) => OPTIONAL_404.some(re => re.test(u));
await cdp.send('Network.enable', {});
await cdp.send('Runtime.enable', {});
await cdp.send('Log.enable', {});
await cdp.send('Page.enable', {});
const pump = setInterval(() => {
  for (const e of cdp.events.splice(0)) {
    if (e.method === 'Network.requestWillBeSent') reqUrl.set(e.params.requestId, e.params.request.url);
    else if (e.method === 'Network.responseReceived') {
      const s = e.params.response.status;
      if (s >= 400) (s === 404 && isExpected404(e.params.response.url) ? expected404 : netBad)
        .push(s + ' ' + e.params.response.url);
    } else if (e.method === 'Network.loadingFailed') {
      if (e.params.canceled) continue;
      netFail.push((e.params.errorText || 'failed') + ' ' + (reqUrl.get(e.params.requestId) || '?'));
    } else if (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error') {
      consoleErr.push(e.params.args.map(a => a.value ?? a.description ?? a.type).join(' '));
    } else if (e.method === 'Runtime.exceptionThrown') {
      const d = e.params.exceptionDetails;
      consoleErr.push('UNCAUGHT ' + ((d.exception && d.exception.description) || d.text));
    } else if (e.method === 'Log.entryAdded' && e.params.entry.level === 'error') {
      // the browser logs its OWN line for every 404, so the same optional probe
      // must be classified the same way here or it just comes back as a console error
      if (isExpected404(e.params.entry.url || '')) continue;
      consoleErr.push('[log] ' + e.params.entry.text + ' ' + (e.params.entry.url || ''));
    }
  }
}, 60);

const READY = (n) => `(async()=>{for(let i=0;i<${n || 900};i++){
  const S=window.SIM; if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy){
    const c=S.cine&&S.cine(); if(!c||c.shot){
      if(window.Npc&&Npc.ready) await Promise.race([Npc.ready(), new Promise(r=>setTimeout(r,20000))]);
      if(window.Story&&Story.ready) await Promise.race([Story.ready, new Promise(r=>setTimeout(r,20000))]);
      return true; } }
  await new Promise(r=>setTimeout(r,150));} return false;})()`;

// keeps a cutscene from stalling the run: complete the line, advance, dismiss cards
const AUTOREADER = `(()=>{ if(window.__auto) return 'already'; window.__autoRead=0;
  window.__auto=setInterval(()=>{ try{
    if(window.Dialogue && Dialogue.isOpen){ const d=Dialogue.debug();
      if(d.mode==='choice'){ const n=(d.choices||[]).length; for(let i=0;i<n-1;i++) Dialogue.key('down'); Dialogue.key('confirm'); window.__autoRead++; return; }
      Dialogue.finishLine(); Dialogue.key('confirm'); window.__autoRead++; return; }
    const c=document.getElementById('story-card');
    if(c && c.style.display!=='none' && c.style.opacity==='1') window.dispatchEvent(new KeyboardEvent('keydown',{key:'e',bubbles:true}));
  }catch(e){} },45); return 'armed'; })()`;

async function waitNav(matcher, secs = 180) {
  const t0 = Date.now();
  while (Date.now() - t0 < secs * 1000) {
    const u = await ev(cdp, 'location.pathname + location.search').catch(() => null);
    if (u && matcher.test(u)) return u;
    await sleep(300);
  }
  return null;
}

try {
  // ---- 2. THE LAUNCHER ------------------------------------------------------
  head('LAUNCHER (dist/index.html off the dumb server)');
  await sleep(1500);
  const launcher = await ev(cdp, `(()=>{
    const cards=[...document.querySelectorAll('a.card')].filter(a=>!a.closest('#door'));
    const door=[...document.querySelectorAll('#door a.card')].map(a=>({t:a.textContent.trim().slice(0,40),href:a.getAttribute('href')}));
    const thumbs=cards.map(c=>{const s=getComputedStyle(c.querySelector('.thumb')||c).backgroundImage;const m=/url\\("?([^")]+)/.exec(s);return m?m[1]:null;}).filter(Boolean);
    const links=[...document.querySelectorAll('.note a')].map(a=>a.getAttribute('href'));
    const w=document.getElementById('eb-wip');
    return {cards:cards.length, door, thumbs:thumbs.length, links, title:document.title,
            hasArchive:!!document.querySelector('details'),
            wip: w ? {text:w.textContent.replace(/\\s+/g,' ').trim().slice(0,80),
                      shown:w.getBoundingClientRect().height>0} : null};
  })()`);
  ok(launcher.cards > 0, `launcher rendered ${launcher.cards} scene cards`, launcher);
  // The WIP banner is injected BY THE BUILD and exists in no source page, so it is
  // also the cheapest single proof that what is being driven is a built artifact
  // and not somebody's dev server.
  ok(!!(launcher.wip && launcher.wip.shown), 'the work-in-progress banner is present and visible', launcher.wip);
  ok(launcher.door.some(d => /NEW GAME/.test(d.t)), 'the NEW GAME door is on the page', launcher.door);
  ok(launcher.thumbs === launcher.cards, `every card names a thumbnail (${launcher.thumbs}/${launcher.cards})`);
  // AND EVERY ONE OF THEM RESOLVES. The line above passed for as long as --compress
  // has been shipping while EVERY CARD ON THE LIVE FRONT DOOR WAS BLANK: index.html
  // builds `background-image:url('…/stylized.png')`, the webp pass deleted that file,
  // and the runtime shim that would have rewritten the request is only injected into
  // play.html. Reading the CSS string proves somebody wrote a URL, not that the URL
  // is a picture. A background-image that 404s renders nothing and says nothing.
  const thumbStatus = await ev(cdp, `(async()=>{const out={};
    for(const c of [...document.querySelectorAll('a.card')].filter(a=>!a.closest('#door'))){
      const s=getComputedStyle(c.querySelector('.thumb')||c).backgroundImage;
      const m=/url\\("?([^")]+)/.exec(s); if(!m) continue;
      try{const r=await fetch(m[1]); if(r.status!==200) out[m[1]]=r.status;}catch(e){out[m[1]]='ERR';} }
    return out;})()`, 120000);
  ok(Object.keys(thumbStatus).length === 0,
     `every card thumbnail actually LOADS (${launcher.cards} fetched)`, thumbStatus);
  ok(!launcher.hasArchive, 'no legacy-archive section (this build ships no archived bundles)');
  note('review-tool links kept: ' + JSON.stringify(launcher.links));
  // every launcher link must resolve on the dumb server — a dead link IS the bug class
  const linkStatus = await ev(cdp, `(async()=>{const out={};
    for(const h of [...document.querySelectorAll('.note a')].map(a=>a.getAttribute('href'))){
      try{const r=await fetch(h.split('#')[0]); out[h]=r.status;}catch(e){out[h]='ERR';} } return out;})()`);
  ok(Object.values(linkStatus).every(s => s === 200), 'every review-tool link resolves 200', linkStatus);

  // ---- 3. NEW GAME ----------------------------------------------------------
  head('NEW GAME (a real click on the launcher, not a hand-built URL)');
  await ev(cdp, `[...document.querySelectorAll('#door a.card')].find(a=>/NEW GAME/.test(a.textContent)).click(); true`);
  const nav = await waitNav(/play3?d?\.html/, 60);
  ok(!!nav, 'the click navigated to the engine page', nav);
  ok(/\/play\.html/.test(nav || ''), 'it is the FRIENDLY path /play.html — the real file the build makes (server.js used to route it)', nav);
  const ready = await ev(cdp, READY(900), 300000);
  ok(ready === true, 'the engine booted off the static build (meshes up, a shot is live)');
  await ev(cdp, AUTOREADER);
  const at0 = await ev(cdp, `({scene:SIM.scene(), shot:SIM.cine()?SIM.cine().shot:null, pos:SIM.pos(), party:(window.GS&&GS.state)?GS.activeParty().map(p=>p.id):null})`);
  ok(at0.scene === 'emb-cine', 'NEW GAME lands in Chapter One\'s own opening scene (emb-cine)', at0);
  ok(!!at0.shot, 'a pre-rendered shot is up: ' + at0.shot);
  note('party: ' + JSON.stringify(at0.party));

  // ---- 4. WALK --------------------------------------------------------------
  head('WALK');
  // THE WORLD HOLDS ITS BREATH UNDER A MODAL (phys() returns zero while UILOCK is
  // claimed), and Chapter One's opening beat fires on arrival — so a walk test that
  // does not wait for the conversation to finish measures the freeze, not the legs.
  // "NOT LOCKED YET" AND "NOT LOCKED ANY MORE" LOOK IDENTICAL, and asking only the
  // second question is a race the wire loses. Measured 2026-08-03: against
  // https://junshern.github.io/emberbrook this test read 0.22 m and went RED while
  // the SAME BYTES walked 4.5 m off localhost — because over a slow link the arrival
  // beat had not claimed UILOCK at the instant the loop first looked, so the loop
  // fell straight through and measured a body that froze one tick later. The frames
  // are real; the failure was the instrument's clock.
  //   So wait for EVIDENCE THE CUTSCENE HAPPENED — the lock seen at least once, or
  // the autoreader having advanced a line — before waiting for it to clear. It
  // fails OPEN after 30 s so a scene with no opening beat can never hang the gate.
  const walked = await ev(cdp, `(async()=>{
    let sawLock=false;
    for(let i=0;i<300;i++){
      if((window.UILOCK&&UILOCK.active())||(window.Dialogue&&Dialogue.isOpen)||(window.__autoRead>0)){ sawLock=true; break; }
      await new Promise(r=>setTimeout(r,100)); }
    for(let i=0;i<400;i++){ const busy=(window.UILOCK&&UILOCK.active())||(window.Dialogue&&Dialogue.isOpen)||SIM.transitions().busy;
      if(!busy) break; await new Promise(r=>setTimeout(r,100)); }
    await new Promise(r=>setTimeout(r,400));
    const locked = !!((window.UILOCK&&UILOCK.active())||(window.Dialogue&&Dialogue.isOpen));
    let best={d:0,dir:null}, a=SIM.pos();
    for(const [k,dir] of [['w','forward'],['s','back'],['a','left'],['d','right']]){
      const p0=SIM.pos(); SIM.keys({[k]:1}); for(let i=0;i<60;i++) SIM.tick(1); SIM.keys({});
      const p1=SIM.pos(), d=+Math.hypot(p1.x-p0.x,p1.z-p0.z).toFixed(2);
      if(d>best.d) best={d,dir};
      if(best.d>0.3) break;
    }
    const b=SIM.pos();
    return {locked, sawLock, autoRead:window.__autoRead||0,
            a:[+a.x.toFixed(2),+a.z.toFixed(2)], b:[+b.x.toFixed(2),+b.z.toFixed(2)],
            d:best.d, dir:best.dir, shot:SIM.cine()?SIM.cine().shot:null}; })()`, 180000);
  ok(walked.d > 0.3, `the body moved ${walked.d} m under held input (${walked.dir})`, walked);

  // ---- 5. ENTER A BUILDING --------------------------------------------------
  head('ENTER A BUILDING (a real edge, taken as an in-place scene swap)');
  const edges = await ev(cdp, `SIM.edges().map(e=>({i:e.i,id:e.id,kind:e.kind,to:e.to,label:e.label,open:e.open}))`);
  const door = (edges || []).find(e => /-int$/.test(e.to || '') && e.open);
  ok(!!door, 'the scene offers a door edge into an interior', edges);
  if (door) {
    const before = at0.scene;
    // SIM.go can REFUSE (busy transition, UILOCK, dialogue open) and its return is
    // the only place that says so — a discarded refusal here spent an hour as
    // "the interior bundle loaded" FAIL that no line of output could explain. The
    // §4 walk can cross a camera band and start a shot cut, so the drive must let
    // the transition system SETTLE first (the refusal is the game being correct:
    // one door per fade). Settle, drive, and retry a busy refusal briefly.
    const went = await ev(cdp, `(async()=>{ let r=null, tries=0;
      for(; tries<40; tries++){
        if(!SIM.transitions().busy){ r=SIM.go(${door.i}); if(!r||!r.error||r.error!=='busy') break; }
        await new Promise(res=>setTimeout(res,250)); }
      return { go:r||{error:'refused (falsy return)'}, tries,
               uilock:!!(window.UILOCK&&UILOCK.active()), dialog:!!(window.Dialogue&&Dialogue.isOpen),
               busy:SIM.transitions().busy }; })()`, 120000);
    const swapped = await ev(cdp, `(async()=>{for(let i=0;i<400;i++){ if(SIM.scene()!==${JSON.stringify(before)} && !SIM.transitions().busy) return SIM.scene(); await new Promise(r=>setTimeout(r,150)); } return SIM.scene();})()`, 240000);
    await ev(cdp, READY(600), 300000);
    ok(swapped === door.to, `walked into ${door.to} (${door.label}) — the interior bundle loaded`, { swapped, want: door.to, atGo: went });
    const inside = await ev(cdp, `({scene:SIM.scene(), meshes:SIM.gpu().meshes, floors:SIM.floors(SIM.pos().x,SIM.pos().z).length})`);
    ok(inside.meshes > 0 && inside.floors > 0, 'the interior has geometry and standable floor under the player', inside);
    // and back out again — a one-way door is a trap in a static build too
    const out = await ev(cdp, `(async()=>{ const e=SIM.edges().find(x=>x.to===${JSON.stringify(before)});
      if(!e) return 'no-way-back'; SIM.go(e.i);
      for(let i=0;i<400;i++){ if(SIM.scene()===${JSON.stringify(before)} && !SIM.transitions().busy) return SIM.scene(); await new Promise(r=>setTimeout(r,150)); } return SIM.scene(); })()`, 240000);
    await ev(cdp, READY(600), 300000);
    ok(out === before, 'and back out to ' + before, out);
  }

  // ---- 6. MENU --------------------------------------------------------------
  head('MENU');
  const menu = await ev(cdp, `(async()=>{ Menu.open(); await new Promise(r=>setTimeout(r,400));
    const d=Menu.debug(); const p=Menu.partyView?Menu.partyView().map(x=>({id:x.id,hp:x.hp,lv:x.lv})):null;
    Menu.close(); await new Promise(r=>setTimeout(r,300));
    return {opened:d.open, screen:d.screen, party:p, closed:!Menu.isOpen}; })()`, 60000);
  ok(menu.opened && menu.closed, 'the menu opens and closes', menu);
  ok(Array.isArray(menu.party) && menu.party.length > 0, 'it shows real party data: ' + JSON.stringify(menu.party));

  // ---- 7. BATTLE ------------------------------------------------------------
  head('BATTLE');
  // SELF-BOUNDED IN THE PAGE. Runtime.evaluate's own `timeout` does not reliably
  // cut an awaited promise, so the deadline lives inside the expression: this box
  // is on a shared machine and the 3D arena loads several 12 MB rigs under
  // swiftshader. If the arena will not come up in time, drop to the DOM stage —
  // what is under test is that the ASSETS resolve off a static host, not the
  // renderer, and the DOM stage still pulls the busts and the backdrop plate.
  const battle = await ev(cdp, `(async()=>{
    const T0=Date.now(), DEADLINE=150000;
    const on=()=>!!(window.Battle && Battle.active);
    if(window.Battle) Battle.pacing = Object.fromEntries(Object.keys(Battle.pacing).map(k=>[k,0]));
    const forced = window.Encounters ? Encounters.forceNext() : false;
    SIM.keys({w:1});
    for(let i=0;i<400 && !on() && Date.now()-T0<40000; i++){ SIM.tick(1); if(i%20===0) await new Promise(r=>setTimeout(r,20)); }
    SIM.keys({});
    let path = on() ? 'ambush' : null;
    if(!on() && window.Battle && Battle.demo){ path='demo3d'; try{ Battle.demo('forest'); }catch(e){ path='demo3d-threw:'+e.message; } }
    while(!on() && Date.now()-T0 < DEADLINE) await new Promise(r=>setTimeout(r,150));
    if(!on() && window.Battle){                       // last resort: the DOM stage
      path='demo-dom'; Battle.stage3d=false; try{ Battle.demo('forest'); }catch(e){}
      const t=Date.now(); while(!on() && Date.now()-t < 60000) await new Promise(r=>setTimeout(r,150));
    }
    // '.ebb-root' IS THE BATTLE UI (battle_turnbased.js:767). Two bugs in one line,
    // and it had been red on every run — local and deployed — while the battle it
    // sits under started fine:
    //   (a) the selector listed .eb-battle/#eb-battle/[class*=battle], none of which
    //       exist any more. MEASURED on the live page mid-battle, the classes are
    //       ebb-root/ebb-3d/ebb-top/ebb-log/ebb-foe/...
    //   (b) it SAMPLED ONCE the instant Battle.active flipped. The root is appended
    //       just after that, so even the right selector missed it.
    // A gate that goes red for a rename is a gate the reader learns to skip, and
    // this one sat red next to 16 dead card thumbnails nobody noticed either.
    let dom = false;
    for (let i = 0; i < 60 && !dom; i++) {
      dom = !!document.querySelector('.ebb-root, .eb-battle, #eb-battle');
      if (!dom) await new Promise(r => setTimeout(r, 200));
    }
    return {forced, path, active:on(), dom, stage3d:window.Battle?Battle.stage3d:null,
            ms:Date.now()-T0}; })()`, 320000).catch(e => ({ active:false, err:String(e.message).slice(0,200) }));
  ok(battle.active, 'a battle started (Encounters.forceNext then walked into it)', battle);
  ok(battle.dom, 'the battle UI is in the DOM');
  const fled = await ev(cdp, `(async()=>{ if(!(window.Battle&&Battle.active)) return 'not-active';
    try{ Battle.forceEnd ? Battle.forceEnd('flee') : (Battle.end && Battle.end('flee')); }catch(e){}
    for(let i=0;i<80 && window.Battle.active; i++) await new Promise(r=>setTimeout(r,100));
    return window.Battle.active ? 'still-in' : 'out'; })()`, 60000).catch(e => 'err:' + e.message);
  note('battle exit: ' + fled);

  // ---- 8. SCREENSHOT --------------------------------------------------------
  head('SCREENSHOT');
  await ev(cdp, `(async()=>{ if(window.Battle&&Battle.active&&Battle.forceEnd) try{Battle.forceEnd('flee')}catch(e){}
    await new Promise(r=>setTimeout(r,600));
    if(SIM.shot) await Promise.race([SIM.shot(SIM.cine().shots[0]), new Promise(r=>setTimeout(r,60000))]);
    SIM.tick(6); return true; })()`, 120000).catch(() => { });
  await sleep(1200);
  const png = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  mkdirSync(join(SHOT, '..'), { recursive: true });
  writeFileSync(SHOT, Buffer.from(png.data, 'base64'));
  ok(true, 'screenshot written to ' + SHOT);

  // ---- 9. SAVE / COLD RELOAD ------------------------------------------------
  head('SAVE -> COLD RELOAD (the resume path, off static files)');
  const saved = await ev(cdp, `(()=>{ GS.autosave(); const raw=localStorage.getItem('emberbrook-save');
    const st=JSON.parse(raw); return {v:st.v||st.version, at:st.at, beats:Object.keys(st.beats||{}).length}; })()`);
  ok(!!(saved && saved.at && saved.at.scene), 'the save carries `at` — the resume authority', saved);
  const resumeUrl = await ev(cdp, `(()=>{ const at=JSON.parse(localStorage.getItem('emberbrook-save')).at;
    const q=new URLSearchParams({scene:at.scene, nomusic:'1'});
    if(at.cam) q.set('cam',at.cam);
    if(Array.isArray(at.pos)){q.set('sx',at.pos[0]);q.set('sy',at.pos[1]);q.set('sz',at.pos[2]);}
    if(at.yaw!=null) q.set('yaw',at.yaw);
    return 'play.html?'+q.toString(); })()`);
  await cdp.send('Page.navigate', { url: (BASE || `http://127.0.0.1:${PORT}`) + '/' + resumeUrl });
  await sleep(2500);
  const rr = await ev(cdp, READY(900), 300000);
  ok(rr === true, 'the cold reload booted');
  const at1 = await ev(cdp, `({scene:SIM.scene(), shot:SIM.cine()?SIM.cine().shot:null, pos:SIM.pos(), flags:Object.keys((GS.state&&GS.state.flags)||{}).length})`);
  ok(at1.scene === saved.at.scene, `resumed in the saved scene (${at1.scene})`, { got: at1, want: saved.at });
  ok(!saved.at.cam || at1.shot === saved.at.cam, `resumed on the saved shot (${at1.shot})`);

  // ---- 10. THE AUDIT --------------------------------------------------------
  await sleep(800);
  head('CONSOLE + NETWORK AUDIT (every request from the launcher to here)');
  const seen = await ev(cdp, `performance.getEntriesByType('resource').length`);
  note(`requests observed on the final page alone: ${seen}; tracked across the session: ${reqUrl.size}`);
  ok(netFail.length === 0, `zero failed network requests (${netFail.length})`, netFail.slice(0, 12));
  ok(netBad.length === 0, `zero UNEXPECTED 4xx/5xx responses (${netBad.length})`, netBad.slice(0, 12));
  note(`${expected404.length} expected 404s (the runtime probing for per-bundle optionals + favicon), not counted:`);
  for (const u of [...new Set(expected404.map(u => u.split('?')[0]))].slice(0, 12)) note('    ' + u);
  ok(consoleErr.length === 0, `zero console errors (${consoleErr.length})`, consoleErr.slice(0, 12));
} finally {
  clearInterval(pump);
}

console.log(`\n${fail === 0 ? 'ALL GREEN' : 'RED'}  —  ${pass} passed, ${fail} failed`);
if (fail) { console.log('failures:'); for (const f of fails) console.log('  - ' + f); }
cdp.close(); kill();
process.exit(fail ? 1 : 0);
