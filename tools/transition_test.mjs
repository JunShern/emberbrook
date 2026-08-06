// transition_test.mjs — PROVE THE IN-PLACE SCENE SWAP, ON THE REAL PAGE.
//
//   node tools/transition_test.mjs                    (needs a server on :8123)
//   node tools/transition_test.mjs --port=3000
//   node tools/transition_test.mjs --doors=24 --head
//   node tools/transition_test.mjs --reload           drive the ?reload=1 fallback
//
// play3d's transitionTo() used to be a full page load, and the comment beside it
// said why: "state-free — robust, no leaked state, correct by construction". That
// robustness was FREE. An in-place swap has to buy it, and this file is the
// receipt. It drives a real Chrome over CDP (the same no-dependency harness
// tools/arena_playtest.mjs uses — CDP over the `ws` package the server already
// ships) through 20+ mixed transitions and asserts the six things a reload gave
// away for nothing:
//
//   SCENE     every door lands in the scene the edge names, with location.search
//             telling the same story (deep links and every ?scene=-reading module
//             depend on it) and SIM.scene() agreeing with both.
//   SPAWN     the arrival point stands ON THE WALK NETWORK of the scene it landed
//             in. An arrival that misses the network is a player in a void, and it
//             is the one failure a swap can produce that a reload could not.
//   GPU       renderer.info returns to BASELINE across the whole gauntlet. This is
//             the leak test and it is the reason the disposal contract exists:
//             three.js only decrements its counters when it is told, so anything
//             dropped without dispose() stays uploaded and invisible to everything
//             except this number.
//   MUSIC     across a door into a scene mapped to the SAME track, Music.current()
//             is the same id and its position advances by roughly the wall time
//             that passed — i.e. the AudioBufferSourceNode was never touched. This
//             is the whole point of the refactor; a resume-from-playhead would
//             pass "same id" and fail this. Measured MODULO THE TRACK'S OWN LOOP
//             (read from public/game/music.json): the playhead is a circle, and a
//             door across the loop point is continuity, not drift. The ruler's own
//             arithmetic is asserted first, against a stall, a restart and a resume.
//   STATE     GS survives the journey untouched, with NO save and NO load. Gold,
//             xp and inventory are compared against a deliberately-dirtied
//             baseline, and GS.save is booby-trapped so a save/load round trip
//             would be caught rather than merely not-needed.
//   CONSOLE   zero errors and zero unhandled rejections for the whole run.
//
// Plus two integration walks the unit assertions cannot reach:
//   BATTLE    a fight mid-town, then a door. Proves the UILOCK interplay: no
//             transition can fire under a panel, and the door still works after.
//   REFRESH   F5 on the swapped URL reproduces the same scene and spawn, which is
//             what makes history.replaceState (rule 5) worth anything.
import { spawn } from 'child_process';
import { readFileSync, rmSync } from 'fs';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { freePort, killOrphans, findPage, GAME_PAGE, sweepStaleProfiles } from './cdp.mjs';
const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '8123'), 10);
// PORT: a free one unless --cdp says otherwise. Two tools shipped 9351 and
// would have collided; a fixed port also collides with an orphan of yourself.
const CDP_PORT = parseInt(arg('cdp', '0'), 10) || await freePort();   // was 9347
const HEAD = argv.includes('--head');
const RELOAD_PATH = argv.includes('--reload');
const DOORS = parseInt(arg('doors', '24'), 10);
const CHROME = process.env.CHROME_BIN ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

// The gauntlet is silent by default for the same reason every other harness here
// is (coordinator standing order): an agent's playtests are audible on the user's
// own machine. But MUSIC CONTINUITY IS UNDER TEST, so ?nomusic=1 would disable the
// very thing being measured — the module is left live and MUTED at the source
// instead. Muting is a master-gain ramp; it does not touch the voice, which is the
// object whose survival across a door this file exists to prove.
const START = 'del-cine';
const URL = `http://localhost:${PORT}/play3d.html?scene=${START}` +
            (RELOAD_PATH ? '&reload=1' : '');

let pass = 0, fail = 0;
const ok = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); }
  else { fail++; console.log('  FAIL ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
const note = (m) => console.log('       ' + m);
const head = (s) => console.log('\n== ' + s);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- MUSIC DRIFT, MEASURED ON A CIRCLE --------------------------------------
// The MUSIC assertion is "the playhead advanced by the wall time that passed", i.e.
// the AudioBufferSourceNode was never touched. THE PLAYHEAD IS NOT A LINE. A looping
// track's position runs loopStart..loopEnd and then jumps back, so a door that happens
// to straddle the loop point sees the position go DOWN, and a linear drift reads the
// whole loop as error.
//
// MEASURED (2026-08-01, from the gauntlet's own failure rows): drift asserted 71.989 s
// across a door where the position went 97.38 -> 29.36. The dellhollow track's loop is
// loopEnd 100.124 - loopStart 28.143 = 71.981 s (public/game/music.json, measured off
// the audio by tools/music_loops.mjs). 97.38 + 3.969 s of wall clock = 101.349, past
// loopEnd, so the voice wrapped to 28.143 + 1.225 = 29.37 — which is where it was.
// The node was never touched; the RULER was wrong. Modulo the loop the residual is
// 71.989 - 71.981 = 0.008 s. This fired repeatedly across runs (flip lane door 12,
// liveliness doors 10 and 19), so it was costing a red line roughly every third run.
//
// THE LENGTH IS READ, NOT HARDCODED, and that is load-bearing rather than tidiness:
// "the ~68.02 s loop" is the obvious reading of the raw jump (97.38 - 29.36 = 68.02)
// and it is WRONG — 68.02 is the jump, which is the loop MINUS the wall time. A
// hardcoded 68.02 would leave a residual of 3.97 s and the assertion would still be
// red, for a subtler reason. music.json is where the loop points live.
const MUSIC_JSON = join(HERE, '..', 'public/game/music.json');
const MUSIC_CFG = JSON.parse(readFileSync(MUSIC_JSON, 'utf8'));
// The loop body length of a track, or 0 for a one-shot / an unlooped voice — the same
// condition public/js/music.js makeVoice() uses to decide `looping` at all.
function loopLen(id) {
  const t = (MUSIC_CFG.tracks || {})[id];
  if (!t || t.loop === false) return 0;
  const a = Number(t.loopStart) || 0, b = Number(t.loopEnd) || 0;
  return b > a ? b - a : 0;
}
// Drift on the circle: how far the playhead is from where the wall clock says it
// should be, given that the track's own loop makes position + L the same instant as
// position. |d| when the track does not loop.
const wrapDrift = (d, L) => L > 0 ? Math.min(Math.abs(d), Math.abs(d - L), Math.abs(d + L))
                                  : Math.abs(d);

// WHAT THIS MUST STILL CATCH. Reducing modulo L can only hide an error within the
// tolerance of a whole multiple of L, so the one thing to prove is that a REAL stall
// — the voice re-created, or restarted from a saved playhead, which is the exact
// regression this whole assertion exists to catch — still reads as drift.
//
// It does, and the margin is not close. A stalled voice has post.position ==
// pre.position, so d = -wall; the nearest other term is |L - wall|. For the gauntlet's
// measured ~4 s doors that is 3.97 s vs 68.01 s, and the assertion fires on 3.97.
// The modulus could only launder a stall lasting within 0.35 s of a multiple of 71.98
// s — a single door taking 72 seconds, when the whole 24-door run takes under a
// minute. Unreachable by construction, and asserted below rather than argued: an
// instrument that has just had its arithmetic changed proves the arithmetic.
function driftSelfCheck() {
  const L = loopLen('dellhollow');
  const CASES = [
    // [what, pre, post, wall, loopLen, must be under 0.35 ?]
    ['the real failure: a door across the loop point', 97.38, 29.36, 3.969, L, true],
    ['an ordinary door, nowhere near the loop point', 40.00, 43.97, 3.970, L, true],
    ['A STALL: the playhead frozen across the door', 40.00, 40.00, 3.970, L, false],
    ['A RESTART: the voice re-created from zero', 40.00, 0.00, 3.970, L, false],
    ['A RESUME from a saved playhead 2 s behind', 40.00, 41.97, 3.970, L, false],
    ['a stall on a ONE-SHOT track (no loop to hide in)', 40.00, 40.00, 3.970, 0, false],
    ['a wrap the instrument must NOT credit: 2 loops', 97.38, 29.36 - L, 3.969, L, false],
  ];
  head('MUSIC ARITHMETIC — the drift ruler, before it is trusted on a real voice');
  note(`dellhollow loop body = ${L.toFixed(3)}s (loopEnd - loopStart, ${MUSIC_JSON.split('/').slice(-2).join('/')})`);
  ok(Math.abs(L - 71.981) < 1e-3, `the loop length is READ from music.json (${L.toFixed(3)}s), not assumed`);
  for (const [what, pre, post, wall, len, quiet] of CASES) {
    const d = wrapDrift((post - pre) - wall, len);
    ok((d < 0.35) === quiet,
       `${what}: drift ${d.toFixed(3)}s -> ${d < 0.35 ? 'PASSES' : 'FAILS'} ` +
       `(must ${quiet ? 'pass' : 'fail'})`, {raw: +((post - pre) - wall).toFixed(3), L: len});
  }
}

// ---- chrome + CDP (no puppeteer; `ws` is already a dependency) --------------
// PER-PID PROFILE, PLUS A SWEEP OF STALE SIBLINGS. Both halves are load-bearing and
// each one fixes a bug the other caused, so do not "simplify" this back either way.
//   The original was ONE fixed directory, reused, because a per-pid profile is ~500 MB
// of Chrome scratch and a suite that mints one per run without cleaning up filled the
// disk in a dozen runs — it did, and it broke every other write on the box.
//   But a FIXED path is shared mutable state between concurrent runs, and this repo now
// runs lanes in parallel: `killOrphans(profile)` SIGKILLs any Chrome holding it and
// rmSync deletes it, so a second lane starting this gate DESTROYS the first lane's run
// mid-flight. Measured 2026-08-02 — one lane's first three attempts died three
// different ways (a door assertion, a boot timeout, an instant exit) purely because
// neighbours kept resetting the profile under it. Every failure was a lie about the
// game. That is EXACTLY the freePort() lesson in CLAUDE.md, moved from the port to the
// profile: AN INSTRUMENT MUST NOT SHARE MUTABLE STATE WITH A COPY OF ITSELF.
//   So: unique per process (isolation), swept on exit AND at startup for anything a
// crashed predecessor left behind (disk). The sweep is what makes per-pid safe.
const profile = join(process.env.TMPDIR || '/tmp', 'transition-test-profile-' + process.pid);
sweepStaleProfiles('transition-test-profile-');
killOrphans(profile);   // a live Chrome still holding this profile makes the rmSync a lie
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-gpu',
  // no gesture exists in a headless run, and the music state machine is under test
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,800', ...(HEAD ? [] : ['--headless=new']), URL,
], { stdio: 'ignore' });
let closing = false;
const kill = () => {
  if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  // Chrome needs a moment to unlink its own files; rmSync after the kill is
  // synchronous and safe to run inside an 'exit' handler, which is the only
  // handler guaranteed to run on every path out of this process.
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { }
};
process.on('exit', kill);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP'])
  process.on(sig, () => { kill(); process.exit(130); });
process.on('uncaughtException', (e) => { console.error('UNCAUGHT:', e && e.message); kill(); process.exit(4); });

// findPage's failure carries its evidence (every CDP target it saw, and whether
// CDP answered at all). The old body threw 'chrome never exposed a play3d page',
// which named four different worlds with one sentence — see tools/cdp.mjs.
const targetWs = () => findPage(CDP_PORT, { tries: 120, label: 'transition_test' });
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); const evs = [];
    let id = 0;
    ws.on('open', () => res({
      send(method, params) {
        return new Promise((okk, no) => { const mid = ++id; pend.set(mid, { ok: okk, no });
          ws.send(JSON.stringify({ id: mid, method, params: params || {} })); });
      },
      events: evs, close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok: okk, no } = pend.get(m.id); pend.delete(m.id);
        m.error ? no(new Error(m.error.message)) : okk(m.result); return; }
      if (m.method) evs.push(m);
    });
  });
}
async function ev(cdp, expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', {
    expression: expr, awaitPromise: true, returnByValue: true,
    userGesture: true, timeout: timeoutMs || 180000,
  });
  if (r.exceptionDetails) {
    const e = r.exceptionDetails;
    throw new Error('page exception: ' + ((e.exception && e.exception.description) || e.text));
  }
  return r.result && r.result.value;
}

// Wait for a scene to be genuinely PLAYABLE, not merely loaded: the collision
// meshes exist, a camera exists, and (in a cinematic bundle) a shot is up.
//
// PLUS the town's PEOPLE. npc.js builds its billboards over a fetch and a chroma
// key, so they land some hops AFTER the scene is playable and after 'eb-scene' is
// handled — and every one of them is a geometry, a material and a texture that
// renderer.info counts. A baseline read in that window is a baseline with ten
// villagers missing from it, and then every later visit to the same (scene, shot)
// reads as a leak that is really just the module finishing its work. So the wait
// is extended to the settle signal the module publishes for exactly this. It is a
// READINESS wait and nothing more: no assertion below is relaxed by it, and a page
// with no npc.js (or a scene with nobody in it) resolves it immediately.
//
// Raced against a ceiling so a signal that never resolves degrades into the OLD
// behaviour — a GPU delta the assertions below catch and print — rather than
// hanging the run inside a readiness helper, where a failure has nothing to say.
const NPCSETTLED = `(!window.Npc || !Npc.ready ? Promise.resolve(true)
  : Promise.race([Npc.ready(), new Promise(r=>setTimeout(()=>r('npc-settle-timeout'),20000))]))`;
// "the object exists" and "renderer.info has counted it" are two different moments:
// three.js registers a geometry and uploads a texture when it is first DRAWN, so an
// object built after the last frame is invisible to the very counter this suite
// asserts on. Two frames after the world goes quiet is the cheap way to be sure the
// snapshot is measuring a rendered world. Raced against a ceiling because rAF is
// throttled — sometimes to a standstill — in a background tab, which is where every
// headless verification in this project lives.
const FRAMES = `Promise.race([new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))),
  new Promise(r=>setTimeout(r,1500))])`;
const READY = (n) => `(async()=>{for(let i=0;i<${n || 400};i++){
  const S=window.SIM; if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy){
    const c=S.cine&&S.cine(); if(!c||c.shot){ await ${NPCSETTLED}; return true; } }
  await new Promise(r=>setTimeout(r,100));} return false;})()`;

// ---- the journey ------------------------------------------------------------
// Mixed on purpose: town <-> interior exercises a small bundle against the whole
// town's collision; town <-> region exercises fixed-camera against real-time
// (different camera rig, different depth mode, different light setup); and the
// interiors differ in which shot the return edge pins, so the cinematic art cache
// is warmed and dropped from several directions rather than one.
const ITINERARY = [
  ['del-inn-int', 'del-cine'], ['del-item-int', 'del-cine'],
  ['ow-valley', 'del-cine'],
  ['del-weapon-int', 'del-cine'], ['del-armor-int', 'del-cine'],
  ['del-cookhouse-int', 'del-cine'], ['del-cottage-int', 'del-cine'],
  ['ow-valley', 'del-cine'],
  ['del-inn-int', 'del-cine'], ['del-item-int', 'del-cine'],
  ['ow-valley', 'del-cine'], ['del-cottage-int', 'del-cine'],
];

(async function main() {
  const cdp = await connect(await targetWs());
  await cdp.send('Runtime.enable');
  await cdp.send('Log.enable');
  await cdp.send('Page.enable');

  // ---- console watch (assertion CONSOLE) ----------------------------------
  // A bundle that ships no zones.json / cine.json / depth.json / meta.json is the
  // DOCUMENTED "absent is fine" path for that feature — every interior takes it —
  // and the browser logs a network 404 for each. Those are classified by URL, not
  // by message text (the Log domain's `text` is just "Failed to load resource").
  // Anything else is a real error and fails the run.
  const OPTIONAL = /zones\.json|cine\.json|depth\.json|meta\.json|routes\.json|stylized\.png|favicon/;
  const errors = [];
  const drainConsole = () => {
    for (const m of cdp.events.splice(0)) {
      if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error')
        errors.push({ kind: 'console.error', url: '',
          text: (m.params.args || []).map(a => a.value || a.description).join(' ') });
      if (m.method === 'Runtime.exceptionThrown')
        errors.push({ kind: 'exception', url: '',
          text: (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text) });
      if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error')
        errors.push({ kind: 'log', url: m.params.entry.url || '', text: m.params.entry.text });
    }
  };
  const realErrors = () => errors.filter(e => !OPTIONAL.test(e.url) && !OPTIONAL.test(e.text));

  // ---- ?reload=1 : THE FALLBACK MUST STAY WORKING (design constraint 4) ----
  // Driven by its own loop rather than the gauntlet's, because the gauntlet's
  // machinery cannot survive here BY DESIGN: SIM.door() resolves a promise inside
  // the page, and on this path the page is destroyed mid-door. That difference is
  // the entire thing being measured — so the door is taken and then the NEW
  // document is waited for from outside, which is also the only way to time the
  // gap the in-place swap exists to remove.
  if (RELOAD_PATH) {
    head('FALLBACK PATH — ?reload=1 restores the full page load');
    let r0 = await ev(cdp, READY(600), 120000);
    ok(r0 === true, 'the start scene became playable on the reload path');
    const legs = [['del-inn-int'], ['del-cine'], ['ow-valley'], ['del-cine'],
                  ['del-cottage-int'], ['del-cine']];
    const gaps = [];
    for (const [to] of legs) {
      const from = await ev(cdp, 'SIM.scene()');
      const t0 = Date.now();
      const fired = await ev(cdp, `(()=>{ const i=SIM.edges().findIndex(e=>e.to===${JSON.stringify(to)});
        if(i<0) return {error:'no edge'}; const r=SIM.go(i); return r||{error:'busy'}; })()`);
      if (fired.error) { ok(false, `reload door -> ${to}`, fired); continue; }
      // wait for a NEW document that is playable again
      let landed = null;
      for (let i = 0; i < 900; i++) {
        await sleep(100);
        try {
          const s = await ev(cdp, `(()=>{ const S=window.SIM;
            return S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy
              ? {scene:S.scene(), url:location.search, pos:S.pos(),
                 walk:S.walkFloors(S.pos().x,S.pos().z), n:S.transitions().n} : null; })()`, 20000);
          if (s && s.scene === to) { landed = s; break; }
        } catch (e) { /* the context is being replaced — that IS the reload */ }
      }
      const ms = Date.now() - t0;
      ok(!!landed, `reload door ${from} -> ${to} landed in a fresh document (${ms}ms)`, landed);
      if (landed) {
        gaps.push(ms);
        ok((landed.walk || []).some(y => Math.abs(y - landed.pos.y) < 0.35),
           `  and its arrival stands on ${to}'s walk network`, landed.pos);
        ok(new URLSearchParams(landed.url).get('scene') === to, '  and ?scene= is the new scene');
        ok(new URLSearchParams(landed.url).get('reload') === '1',
           '  and reload=1 propagated, so the whole journey stays on the old path');
        ok(landed.n <= 1, '  and the page has no in-place swap in its log (it really reloaded)', landed.n);
      }
      drainConsole();
    }
    if (gaps.length) {
      const g = gaps.slice().sort((a, b) => a - b);
      note(`FULL-RELOAD door cost (fade + navigation + full re-init + first playable frame): ` +
           `median ${g[g.length >> 1]}ms, min ${g[0]}ms, max ${g[g.length - 1]}ms`);
    }
    head('CONSOLE (reload path)');
    drainConsole();
    const rr = realErrors();
    ok(rr.length === 0, `no console errors on the fallback path (${errors.length} total, ` +
       `${errors.length - rr.length} optional-asset 404s)`, rr.slice(0, 6));
    console.log(`\n${fail ? 'FAIL' : 'PASS'}  ${pass} assertions ok, ${fail} failed  (?reload=1 fallback)`);
    cdp.close(); kill(); process.exit(fail ? 1 : 0);
  }

  head('BOOT');
  const ready = await ev(cdp, READY(600), 120000);
  ok(ready === true, 'the start scene became playable');
  if (!ready) { console.log('\nFAIL — the page never became ready'); kill(); process.exit(2); }
  await ev(cdp, `(async()=>{ for(let i=0;i<200;i++){ if(window.GS&&window.GS.ok) return true;
     await new Promise(r=>setTimeout(r,100)); } return false; })()`);
  await ev(cdp, `window.Music && Music.mute(true), true`);   // silent, but LIVE
  const boot = await ev(cdp, `({scene:SIM.scene(), url:location.search, gpu:SIM.gpu(),
    gs:!!(window.GS&&GS.ok), music:!!window.Music, mods:{shop:!!window.Shop,
    enc:!!window.Encounters, routes:!!window.ROUTES}})`);
  ok(boot.scene === START, `boot scene is ${START}`, boot.scene);
  ok(boot.gs && boot.music && boot.mods.shop && boot.mods.enc && boot.mods.routes,
     'every hooked module loaded', boot.mods);
  note(`boot gpu: ${JSON.stringify(boot.gpu)}`);

  // ---- dirty the game state so "untouched" is a measurable claim -----------
  // A fresh newGame() would compare equal to another fresh newGame(), so the
  // persistence assertion would pass on a full reload too. Making the state
  // UNIQUE is what turns it into a real test of in-place persistence.
  const gsBefore = await ev(cdp, `(()=>{ GS.addGold(1234); GS.addItem('potion',7);
    GS.state.flags.__transition_probe = 'ember-' + Date.now();
    window.__SAVES=0; const s=GS.save; GS.save=function(){window.__SAVES++;return s.apply(this,arguments);};
    const l=GS.load; GS.load=function(){window.__SAVES++;return l.apply(this,arguments);};
    return {gold:GS.state.gold, potion:GS.count('potion'), flag:GS.state.flags.__transition_probe,
            party:GS.state.party.map(p=>p.id+':'+p.level+':'+p.xp).join('|')}; })()`);
  note(`GS dirtied: gold=${gsBefore.gold} potion=${gsBefore.potion} flag=${gsBefore.flag}`);

  // ---- BASELINE ------------------------------------------------------------
  // THE BASELINE IS PER (SCENE, SHOT), NOT PER PAGE, and that is a real finding
  // rather than a convenience. renderer.info.memory.geometries counts geometries
  // that have been UPLOADED, and a geometry uploads on its first render — so in a
  // town of sixteen fixed cameras the number is a property of WHICH SHOT is up.
  // Entering Dellhollow at the valley gate uploads 346 of the town's shared
  // geometries; entering it at shelf-west uploads 491. Comparing the two would
  // report a 145-geometry "leak" that is nothing but a different camera.
  //
  // So: the first time the run settles in a given (scene, shot) its counts become
  // that state's baseline, and EVERY later arrival in the same state must match
  // exactly. That is a stronger test than one town number — it holds every scene
  // and every shot the itinerary touches to its own first visit.
  const BASE = new Map();
  const gpuKey = (s) => s.scene + '|' + (s.shot || '-');
  function gpuCheck(label, s) {
    const k = gpuKey(s), b = BASE.get(k);
    if (!b) { BASE.set(k, s); note(`${label}: first visit to ${k} — baseline ` +
      `geo=${s.gpu.geometries} tex=${s.gpu.textures} meshes=${s.gpu.meshes}`); return null; }
    const d = { geo: s.gpu.geometries - b.gpu.geometries, tex: s.gpu.textures - b.gpu.textures,
                meshes: s.gpu.meshes - b.gpu.meshes, mats: s.gpu.sceneMats - b.gpu.sceneMats };
    ok(d.geo === 0 && d.tex === 0 && d.meshes === 0 && d.mats === 0,
       `${label}: ${k} is back to its baseline (geo ${b.gpu.geometries}, tex ${b.gpu.textures})`,
       { delta: d, base: b.gpu, now: s.gpu });
    return d;
  }
  head('BASELINE — one round trip, then measure');
  const warm = await door(cdp, 'del-inn-int');
  ok(!warm.error && warm.to === 'del-inn-int', 'warm-up: town -> inn', warm);
  const back = await door(cdp, 'del-cine');
  ok(!back.error && back.to === 'del-cine', 'warm-up: inn -> town', back);
  await settle(cdp);
  const base = await snap(cdp);
  BASE.set(gpuKey(base), base);
  note(`baseline gpu @${gpuKey(base)}: geometries=${base.gpu.geometries} ` +
       `textures=${base.gpu.textures} programs=${base.gpu.programs} ` +
       `meshes=${base.gpu.meshes} cineArt=${base.gpu.cineArt}`);
  drainConsole();

  // ---- MUSIC baseline ------------------------------------------------------
  driftSelfCheck();          // the ruler, before any voice is measured with it
  const m0 = await ev(cdp, `({cur: window.Music?Music.current():null,
    dbg: window.Music?Music._debug():null,
    trackTown: Music.trackFor('del-cine'), trackInn: Music.trackFor('del-inn-int'),
    trackOw: Music.trackFor('ow-valley')})`);
  note(`music: town=${m0.trackTown} inn=${m0.trackInn} ow=${m0.trackOw} ` +
       `now=${m0.cur ? m0.cur.id + '@' + m0.cur.position : 'silent'} ctx=${m0.dbg && m0.dbg.ctx}`);
  const musicLive = !!(m0.cur && m0.dbg && m0.dbg.ctx === 'running');
  if (!musicLive) note('NOTE: no sounding voice in this environment — music continuity ' +
                       'assertions become no-ops and are reported as skipped.');

  // ---- THE GAUNTLET --------------------------------------------------------
  head(`GAUNTLET — ${DOORS} mixed transitions`);
  const rows = [];
  let musicChecked = 0, musicSameTrack = 0, worstDrift = 0;
  for (let i = 0; i < DOORS; i++) {
    const [to, ret] = ITINERARY[Math.floor(i / 2) % ITINERARY.length];
    const target = (i % 2 === 0) ? to : ret;
    if (target === await ev(cdp, 'SIM.scene()')) continue;

    const sameTrack = musicLive && await ev(cdp,
      `Music.trackFor(SIM.scene()) === Music.trackFor(${JSON.stringify(target)})`);
    const pre = musicLive ? await ev(cdp, '({cur:Music.current(), t:performance.now()})') : null;

    const r = await door(cdp, target);
    if (r.error) { ok(false, `door ${i}: -> ${target}`, r); break; }
    await settle(cdp);

    const post = await snap(cdp);

    // SCENE (rules 1 + 5)
    const urlScene = new URLSearchParams(post.url).get('scene');
    ok(post.scene === target && urlScene === target,
       `door ${i}: ${r.from} -> ${target} in ${r.ms}ms (url agrees)`,
       { simScene: post.scene, urlScene });

    // GPU — every revisit of a (scene, shot) must match its own first visit
    gpuCheck(`door ${i}`, post);

    // THE FRAME IS REAL. Every assertion above this one is satisfiable by a page
    // that has the right objects in memory and renders nothing — and a screenshot
    // of a background tab is stale, so pixels are the only ground truth (the
    // SIM.paint readback exists for exactly this). Rule (3) says the veil never
    // lifts on a half-built scene; this is the half that can be measured.
    //
    // TWO readbacks, because "0 visible pixels" has two very different causes and
    // they look identical on screen. Untested = "is she drawn at all", which is
    // what proves the swap really built a frame. Depth-tested = "does she survive
    // this shot's baked depth map", which can legitimately be zero: an arrival
    // behind an occluder is a state the runtime is DESIGNED for, and the contract
    // is that the presence marker shows. (Dellhollow's weapon-shop exit is exactly
    // this case, identically on a fresh page load — see the report.) So the
    // assertion is "drawn, AND either visible or properly marked".
    const paint = await ev(cdp, `({tested:SIM.paint({tested:true}),
                                   untested:SIM.paint({}), occ:SIM.occCheck()})`);
    const drawn = paint.untested.magentaPixels > 0 && paint.untested.onScreen;
    const seen = paint.tested.magentaPixels > 0;
    ok(drawn && (seen || paint.occ.ring),
       `door ${i}: the character is really rasterised in the new frame ` +
       `(${paint.untested.magentaPixels}px drawn, ${paint.tested.magentaPixels}px through ` +
       `the shot's depth map${seen ? '' : ' — occluded, presence marker ' +
        (paint.occ.ring ? 'SHOWN' : 'MISSING')})`, paint);

    // SPAWN — on the network of the scene we actually landed in
    const onNet = (post.walk || []).some(y => Math.abs(y - post.pos.y) < 0.35);
    ok(onNet, `door ${i}: arrival stands on ${target}'s walk network`,
       { pos: post.pos, floorsUnder: post.walk });

    // MUSIC — same track means the SAME NODE, still playing
    if (musicLive && pre && pre.cur && post.cur) {
      musicChecked++;
      if (sameTrack) {
        musicSameTrack++;
        const wall = (post.t - pre.t) / 1000;
        // ON THE CIRCLE, not the line — see wrapDrift above. `looping` comes off the
        // live voice (Music.current()), so an unlooped one-shot gets no forgiveness.
        const raw = (post.cur.position - pre.cur.position) - wall;
        const L = post.cur.looping ? loopLen(post.cur.id) : 0;
        const drift = wrapDrift(raw, L);
        const wrapped = Math.abs(Math.abs(raw) - drift) > 1e-9;
        worstDrift = Math.max(worstDrift, drift);
        ok(post.cur.id === pre.cur.id && drift < 0.35,
           `door ${i}: same-track music LITERALLY uninterrupted (drift ${drift.toFixed(3)}s` +
           (wrapped ? `, across the ${L.toFixed(2)}s loop point: ${pre.cur.position} -> ` +
                      `${post.cur.position}` : '') + ')',
           { before: pre.cur, after: post.cur, wall: +wall.toFixed(3),
             raw: +raw.toFixed(3), loopLen: +L.toFixed(3) });
      }
    }

    // ENCOUNTERS — re-armed, and the doorway is not an ambush
    if (post.enc && post.enc.attached)
      ok(post.enc.graceWhy === 'scene' || post.enc.grace > 0,
         `door ${i}: encounter director re-graced on arrival`,
         { why: post.enc.graceWhy, grace: post.enc.grace });

    rows.push({ i, to: target, shot: post.shot || '-', ms: r.ms,
                geo: post.gpu.geometries, tex: post.gpu.textures,
                meshes: post.gpu.meshes, art: post.gpu.cineArt, mats: post.gpu.sceneMats });
    drainConsole();
  }

  // ---- GPU: back to where we started --------------------------------------
  head('GPU — renderer.info returns to baseline');
  const endScene = await ev(cdp, 'SIM.scene()');
  if (endScene !== START) { const rr = await door(cdp, START); note(`returned to ${START}: ${rr.ms}ms`); }
  await settle(cdp);
  const after = await snap(cdp);
  ok(rows.length >= 20, `${rows.length} transitions driven (20+ required)`, rows.length);
  gpuCheck('final', after);
  // and the whole-page picture: a leak that somehow kept every per-state count
  // honest would still show up as growth in the totals against the FIRST state.
  const first = BASE.get(gpuKey(base));
  note(`page totals now vs the ${gpuKey(base)} baseline: ` +
       `geo ${first.gpu.geometries} -> ${after.gpu.geometries}, ` +
       `tex ${first.gpu.textures} -> ${after.gpu.textures}, ` +
       `mats ${first.gpu.sceneMats} -> ${after.gpu.sceneMats}`);

  head('MEMORY TABLE');
  console.log('   door  ->scene            shot            ms   geoms   texs  meshes  mats  art');
  for (const r of rows)
    console.log(`   ${String(r.i).padStart(4)}  ${r.to.padEnd(17)} ${String(r.shot).padEnd(14)} ` +
      `${String(r.ms).padStart(4)}  ${String(r.geo).padStart(5)}  ${String(r.tex).padStart(5)}  ` +
      `${String(r.meshes).padStart(6)}  ${String(r.mats).padStart(4)}  ${String(r.art).padStart(3)}`);
  // Per-state stability, printed so the memory table can be read as a verdict and
  // not just as numbers: every repeat of a (scene, shot) with identical counts.
  const seen = new Map();
  let repeats = 0, drifted = 0;
  for (const r of rows) {
    const k = r.to + '|' + r.shot, sig = `${r.geo}/${r.tex}/${r.meshes}/${r.mats}`;
    if (!seen.has(k)) { seen.set(k, sig); continue; }
    repeats++; if (seen.get(k) !== sig) { drifted++; note(`  drift at ${k}: ${seen.get(k)} -> ${sig}`); }
  }
  ok(drifted === 0, `every repeated (scene, shot) has identical counts ` +
     `(${repeats} repeat visits across ${seen.size} distinct states)`, { drifted });
  const msList = rows.map(r => r.ms).sort((a, b) => a - b);
  if (msList.length) note(`swap cost incl. both 350ms fades: median ${msList[msList.length >> 1]}ms, ` +
    `min ${msList[0]}ms, max ${msList[msList.length - 1]}ms`);

  // ---- MUSIC verdict -------------------------------------------------------
  head('MUSIC');
  if (!musicLive) { note('skipped — no sounding voice in this environment'); }
  else {
    ok(musicSameTrack > 0, `same-track doors exercised (${musicSameTrack} of ${musicChecked})`);
    ok(worstDrift < 0.35, `worst same-track playhead drift ${worstDrift.toFixed(3)}s`);
    const md = await ev(cdp, 'Music._debug()');
    ok(md.ctx === 'running', 'the AudioContext is the SAME one, still running', md.ctx);
    // The sessionStorage dance is the FALLBACK's machinery. In-place must not need
    // it — and must not have been silently relying on it.
    ok(md.saved === null || (md.current && md.saved.trackId === md.current.id),
       'no sessionStorage resume was used to fake the continuity', md.saved);
  }

  // ---- STATE ---------------------------------------------------------------
  head('GS PERSISTENCE — no save, no load, no reset');
  const gsAfter = await ev(cdp, `({gold:GS.state.gold, potion:GS.count('potion'),
    flag:GS.state.flags.__transition_probe,
    party:GS.state.party.map(p=>p.id+':'+p.level+':'+p.xp).join('|'), saves:window.__SAVES})`);
  ok(gsAfter.flag === gsBefore.flag, 'a flag set before the journey survived it', gsAfter.flag);
  ok(gsAfter.gold === gsBefore.gold, `gold unchanged across the journey (${gsBefore.gold})`, gsAfter.gold);
  ok(gsAfter.potion === gsBefore.potion, 'inventory unchanged', gsAfter.potion);
  ok(gsAfter.party === gsBefore.party, 'party levels/xp unchanged', gsAfter.party);
  ok(gsAfter.saves === 0, 'GS.save/GS.load were never called by a door', gsAfter.saves);

  // ---- BATTLE + UILOCK -----------------------------------------------------
  head('BATTLE MID-TOWN, THEN A DOOR (UILOCK interplay)');
  // Battle.active is set BEFORE start()'s first await (its own comment says why:
  // "the phys() freeze is immediate"), so the lock state is captured SYNCHRONOUSLY
  // off the returned promise. At speed:0 a whole fight can resolve inside a few
  // microtasks — polling for `active` misses it entirely, which is what the first
  // draft of this test did.
  const bat = await ev(cdp, `(async()=>{
    if(!window.Battle||!window.Rules||!window.GS||!GS.ok) return {skip:'no battle kernel'};
    const zones = GS.data.encounters.zones||{};
    const zk = Object.keys(zones).find(k=>(zones[k].groups||[]).length);
    if(!zk) return {skip:'no hostile zone in encounters.json'};
    const grp = zones[zk].groups[0];
    const group = (grp && (grp.monsters||grp.ids||grp.group||grp)) || [];
    const before = SIM.scene(), gold0 = GS.state.gold;
    const p = Battle.start({zone:zk, group:[].concat(group), seed:7, backdrop:zk},
                           null, {speed:0, autoplay:true});
    // captured synchronously: this is the frame the world is supposed to freeze on
    const active = !!Battle.active, locked = UILOCK.active();
    // ASK for a door while the panel is up. phys() returns early under a UILOCK so
    // sgTick never runs; SIM.tick drives the real physics path, not a stub.
    SIM.tick(120);
    const sceneDuringFight = SIM.scene(), edgesArmed = SIM.edges().filter(e=>e.inRange).length;
    const res = await Promise.race([p, new Promise(r=>setTimeout(()=>r('timeout'),150000))]);
    return {zone:zk, group, before, active, locked, sceneDuringFight, edgesArmed,
            result: res==='timeout'?'timeout':((res&&res.outcome)||String(res)),
            gold0, gold: GS.state.gold};
  })()`, 180000);
  if (bat.skip) { note('skipped — ' + bat.skip); }
  else {
    note(`fought a ${bat.zone} group: ${JSON.stringify(bat.group)}`);
    ok(bat.active === true, 'a battle really started in the town');
    ok(bat.locked === true, 'UILOCK is held from the battle\'s first frame');
    ok(bat.sceneDuringFight === bat.before,
       'no door could fire during the fight (120 physics ticks under the lock)', bat);
    note(`battle result: ${bat.result}, gold ${bat.gold0} -> ${bat.gold}`);
    await ev(cdp, `(async()=>{for(let i=0;i<300;i++){ if(!UILOCK.active()&&!Battle.active) return true;
      await new Promise(r=>setTimeout(r,100)); } return false;})()`, 120000);
    const afterFight = await door(cdp, 'del-inn-int');
    ok(!afterFight.error && afterFight.to === 'del-inn-int',
       'a door taken right after the fight still works', afterFight);
    const backAgain = await door(cdp, 'del-cine');
    ok(!backAgain.error, 'and back out again', backAgain);
    await settle(cdp);
    // the fight's own GPU objects (the 3D arena) must not have moved the world's
    const afterBat = await snap(cdp);
    gpuCheck('after battle', afterBat);
  }
  drainConsole();

  // ---- IN-SCENE CAMERA CUTS still work AFTER a swap -----------------------
  // del-cine's camera cuts are the in-place precedent this whole refactor was
  // modelled on, and they take the `local` branch of transitionTo — the one
  // branch that did NOT change. But the swap now rebuilds SGE and empties the
  // cinematic art cache on every arrival, so "the cuts still work in a town you
  // walked back into" is a genuinely new thing to be able to get wrong.
  head('IN-SCENE CAMERA CUTS after a swap (the local handoff is untouched)');
  const cut = await ev(cdp, `(async()=>{
    const c0 = SIM.cine(); if(!c0) return {skip:'not a cinematic bundle'};
    const auto = SIM.edges().filter(e=>e.auto && e.cam && e.live);
    if(!auto.length) return {skip:'no live auto edge from this shot'};
    const target = auto[0], before = c0.shot, cuts0 = c0.cuts;
    const r = SIM.go(target.i);
    for(let i=0;i<400;i++){ if(!SIM.transitions().busy) break;
      await new Promise(x=>setTimeout(x,25)); }
    const c1 = SIM.cine();
    return {before, after:c1.shot, want:target.cam, cuts0, cuts:c1.cuts,
            local:r&&r.local, edges:SIM.edges().length, shots:c1.shots.length};
  })()`, 120000);
  if (cut.skip) { note('skipped — ' + cut.skip); }
  else {
    ok(cut.local === true, 'an in-scene edge is still routed as a LOCAL handoff (no swap)');
    ok(cut.after === cut.want, `the cut landed on shot '${cut.want}'`, cut);
    ok(cut.cuts === cut.cuts0 + 1, 'and it counted as exactly one cut', cut);
    // THE SHOT COUNT IS THE SHIPPED BUNDLE'S OWN, never a literal: the count was
    // hardcoded 16 and went stale the day Bet 2 it.2 deleted the loop-landing fork
    // camera (15 ratified shots) — the assertion then failed every run for a month
    // of the number being right. cine.json is what the runtime itself loads.
    const CINE_SHOTS = JSON.parse(readFileSync(join(HERE, '..',
      'public/assets/scenes/del-cine/cine.json'), 'utf8')).cameras.length;
    ok(cut.shots === CINE_SHOTS,
       `the re-entered town still knows all ${CINE_SHOTS} of its shots`, cut.shots);
    ok(cut.edges > 30, `and its ${cut.edges} edges were re-bound on arrival`, cut.edges);
  }
  drainConsole();

  // ---- read the log BEFORE the reload wipes it ----------------------------
  const log = await ev(cdp, 'SIM.transitions()');

  // ---- REFRESH: the replaced URL is a real deep link -----------------------
  head('DEEP LINK — F5 on the swapped URL lands where the swap did');
  const beforeReload = await ev(cdp, '({scene:SIM.scene(), url:location.search, pos:SIM.pos()})');
  await cdp.send('Page.reload', { ignoreCache: false });
  await sleep(1500);
  const reReady = await ev(cdp, READY(600), 120000);
  ok(reReady === true, 'the reloaded page became playable');
  const afterReload = await ev(cdp, '({scene:SIM.scene(), url:location.search, pos:SIM.pos(), arr:SIM.arrival()})');
  ok(afterReload.scene === beforeReload.scene,
     'a refresh reproduces the swapped scene', { before: beforeReload.scene, after: afterReload.scene });
  // WHAT replaceState PROMISES, precisely: the URL describes the ARRIVAL — the
  // door you came in by — not wherever the player has wandered since. A refresh
  // therefore reproduces ?sx/?sy/?sz, and that is the same contract the full page
  // load had (an in-scene camera cut never rewrote the URL either, before this
  // change or after it). Asserting against the live position instead would be
  // asserting a promise nobody made.
  const q = new URLSearchParams(beforeReload.url);
  const want = [parseFloat(q.get('sx')), parseFloat(q.get('sy')), parseFloat(q.get('sz'))];
  const near = Math.hypot(afterReload.pos.x - want[0], afterReload.pos.z - want[2]);
  ok(isFinite(near) && near < 1.0,
     `and lands on the arrival the URL declares (${near.toFixed(2)}u from ?sx/?sz)`,
     { urlArrival: want, after: afterReload.pos });
  ok(afterReload.url === beforeReload.url,
     'the query string itself round-trips through a refresh byte for byte');

  // ---- CONSOLE -------------------------------------------------------------
  head('CONSOLE');
  drainConsole();
  const real = realErrors();
  ok(real.length === 0, `no console errors across the whole run (${errors.length} total, ` +
     `${errors.length - real.length} optional-asset 404s)`, real.slice(0, 8));
  for (const e of real.slice(0, 10)) note(`  ! [${e.kind}] ${e.url} ${e.text}`);

  head('TRANSITION LOG');
  note(`${log.n} transitions recorded in the page, ` +
       `path=${log.reloadPath ? 'FULL RELOAD (?reload=1)' : 'in-place swap'}`);
  const swaps = log.log.filter(r => r.kind === 'swap');
  if (swaps.length) {
    const med = (a) => { const s = a.slice().sort((x, y) => x - y); return s[s.length >> 1]; };
    const all = swaps.map(r => r.ms), dis = swaps.map(r => r.disposeMs), ld = swaps.map(r => r.loadMs);
    note(`in-page swap work, EXCLUDING both 350ms fades:`);
    note(`  total   median ${med(all)}ms   min ${Math.min(...all)}ms   max ${Math.max(...all)}ms`);
    note(`  dispose median ${med(dis)}ms   min ${Math.min(...dis)}ms   max ${Math.max(...dis)}ms` +
         `   (the price the old full page load did not pay)`);
    note(`  load    median ${med(ld)}ms    min ${Math.min(...ld)}ms   max ${Math.max(...ld)}ms` +
         `   (fetch + parse + BVH + spawn — the reload paid this too)`);
    const worst = swaps.slice().sort((a, b) => b.ms - a.ms).slice(0, 3);
    for (const w of worst)
      note(`  worst: ${w.from} -> ${w.to}  ${w.ms}ms (dispose ${w.disposeMs} + load ${w.loadMs})`);
  }

  console.log(`\n${fail ? 'FAIL' : 'PASS'}  ${pass} assertions ok, ${fail} failed`);
  cdp.close(); kill();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('\nHARNESS ERROR:', e.message); kill(); process.exit(3); });

// take a door and wait for it to settle
async function door(cdp, to) {
  return ev(cdp, `SIM.door(${JSON.stringify(to)})`, 180000);
}
// one full picture of the live world
async function snap(cdp) {
  return ev(cdp, `(()=>{ const p=SIM.pos(), c=SIM.cine&&SIM.cine();
    return {scene:SIM.scene(), shot:c&&c.shot||null, url:location.search, pos:p,
      gpu:SIM.gpu(), walk:SIM.walkFloors(p.x,p.z),
      cur: window.Music?Music.current():null, t:performance.now(),
      enc: window.Encounters?Encounters._debug():null,
      shop: window.Shop?Shop.debug():null, cine:c, prompt:SIM.prompt()}; })()`);
}
// let the async tail of a scene load (prefetch, zones, module handlers) quiesce so
// a GPU snapshot measures a settled world rather than one mid-fetch. The module
// handlers' OWN tails count: npc.js tears its figures down and rebuilds them on
// 'eb-scene', and the rebuild outlives the handler by a fetch and a chroma key, so
// the settle waits on its published signal too (see NPCSETTLED). Every caller of
// this function is standing in front of a snap() — that is the whole point of
// waiting here rather than sleeping there.
async function settle(cdp) {
  await ev(cdp, `(async()=>{ for(let i=0;i<200;i++){
      const c=SIM.cine&&SIM.cine();
      if(!SIM.transitions().busy && (!c || !c.pending.length)) { await new Promise(r=>setTimeout(r,120));
        const c2=SIM.cine&&SIM.cine();
        if(!c2||!c2.pending.length){ await ${NPCSETTLED}; await ${FRAMES};
          const n=window.Npc&&Npc.debug?Npc.debug():null;
          if(!n||!n.building) return true; } }
      await new Promise(r=>setTimeout(r,100)); } return false; })()`, 120000);
}
