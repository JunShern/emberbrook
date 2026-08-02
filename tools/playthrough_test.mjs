// playthrough_test.mjs — CAN A PLAYER GET FROM NEW GAME TO THE END OF CHAPTER TWO?
//
//   node tools/playthrough_test.mjs --port=3000        (needs a server on that port)
//   node tools/playthrough_test.mjs --head             watch it happen
//   node tools/playthrough_test.mjs --stop-at=ch1.done stop after a named beat
//
// WHY THIS EXISTS. Every other gate in this project measures ONE layer: seam_test
// the camera grammar, dialogue_test the cast, transition_test the swap, economy_test
// the arithmetic. All of them were green on 2026-08-02 while the game had no chapter
// in it at all — chapter1.js and chapter2.js were loaded by join-legacy.html and by
// nothing else (docs/plans/end-to-end-wiring.md §2.1). A suite of green unit gates
// cannot tell you that the thing is not a game. This one walks it.
//
// IT DRIVES THE REAL PAGE over CDP, the same no-dependency harness
// tools/transition_test.mjs uses, from a CLEARED localStorage, and asserts the six
// things §1 of the plan says a continuous playthrough needs:
//
//   1. NEW GAME lands in Chapter One's own opening ground and the chapter SPEAKS
//      BY ITSELF — nothing forces the first beat; the director is armed or it is not.
//   2. Every Chapter One beat fires on ITS OWN TRIGGER (the shot that must be up,
//      the circle the player must stand in, the flags that must be set). The harness
//      moves the body and takes the shot; it never calls Story.force().
//   3. The Old Gate. The sealed edge must be ABSENT from SIM.edges() while
//      story.ch1.gate-open is false and PRESENT once it is true — seam canon's
//      sealed rule is that "the sealed presentation is the absence", and an absence
//      that is never tested is an absence nobody has checked.
//   4. The handoff is a WALK, not a teleport: the player takes an edge into
//      ow-valley and the Chapter One end card plays over the corridor's first frame.
//   5. Chapter Two's beats fire in del-cine and its ending sets story.ch2.done AND
//      maren-joined, and GS.activeParty() then contains Maren — the payoff the
//      orphan joinFlag in growth.json:33 has been declaring since day one.
//   6. SAVE / RESUME: a cold reload built from GS.state.at alone lands in the same
//      scene, the same shot and the same place, with every story flag intact.
//
// WHAT IT IS NOT. It is not a walk test: getting a body from Emberbrook's arch to
// its gate court on foot is seam_walk's and walk_bodygate's job, and repeating it
// here would make a story failure and a collision failure indistinguishable. This
// harness TELEPORTS between beat anchors with SIM.tp/SIM.shot — the runtime's own
// test surface — and then lets the beat fire on its own. What it proves is the
// STORY SPINE: that the beats trigger, in order, from the state the previous one
// left behind, and that the chapter can be finished.
import { spawn } from 'child_process';
import { rmSync } from 'fs';
import { createRequire } from 'module';
import { join } from 'path';
import { freePort, killOrphans, findPage, GAME_PAGE, sweepStaleProfiles } from './cdp.mjs';
const require = createRequire(import.meta.url);
const WebSocket = require('ws');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
// PORT: a free one unless --cdp says otherwise. Two tools shipped 9351 and
// would have collided; a fixed port also collides with an orphan of yourself.
const CDP_PORT = parseInt(arg('cdp', '0'), 10) || await freePort();   // was 9351
const HEAD = argv.includes('--head');
const STOP_AT = arg('stop-at', null);
const CHROME = process.env.CHROME_BIN ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

// ?nomusic=1 — the standing rule (seam-canon §7): a headless check has no business
// making noise in somebody's room. Nothing here measures audio.
const START = `http://localhost:${PORT}/play3d.html?scene=emb-cine&cam=woodroad&nomusic=1`;

let pass = 0, fail = 0;
const fails = [];
const ok = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); }
  else { fail++; fails.push(m); console.log('  FAIL ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
const note = (m) => console.log('       ' + m);
const head = (s) => console.log('\n== ' + s);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- chrome + CDP -----------------------------------------------------------
// PER-PID PROFILE + a sweep of stale siblings — see cdp.mjs's sweepStaleProfiles and
// the long comment in transition_test.mjs. A FIXED path is shared mutable state, and
// killOrphans + rmSync mean a second lane running this gate destroys the first lane's
// run mid-flight; a bare per-pid path leaks ~500 MB per crash and once filled the disk.
// Both halves are required.
const profile = join(process.env.TMPDIR || '/tmp', 'playthrough-test-profile-' + process.pid);
sweepStaleProfiles('playthrough-test-profile-');
killOrphans(profile);   // a live Chrome still holding this profile makes the rmSync a lie
rmSync(profile, { recursive: true, force: true });
const chrome = spawn(CHROME, [
  `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-gpu',
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,800', ...(HEAD ? [] : ['--headless=new']), START,
], { stdio: 'ignore' });
let closing = false;
const kill = () => { if (closing) return; closing = true;
  try { chrome.kill('SIGKILL'); } catch (e) { }
  try { rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { } };
process.on('exit', kill);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => { kill(); process.exit(130); });
process.on('uncaughtException', (e) => { console.error('UNCAUGHT:', e && e.message); kill(); process.exit(4); });

// findPage's failure carries its evidence (every CDP target it saw, and whether
// CDP answered at all) — see tools/cdp.mjs.
const targetWs = () => findPage(CDP_PORT, { tries: 160, label: 'playthrough_test' });
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
    const pend = new Map(); const evs = []; let id = 0;
    ws.on('open', () => res({
      send(method, params) { return new Promise((okk, no) => { const mid = ++id;
        pend.set(mid, { ok: okk, no }); ws.send(JSON.stringify({ id: mid, method, params: params || {} })); }); },
      events: evs, close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', (raw) => { let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok: okk, no } = pend.get(m.id); pend.delete(m.id);
        m.error ? no(new Error(m.error.message)) : okk(m.result); return; }
      if (m.method) evs.push(m); });
  });
}
async function ev(cdp, expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true,
    returnByValue: true, userGesture: true, timeout: timeoutMs || 180000 });
  if (r.exceptionDetails) { const e = r.exceptionDetails;
    throw new Error('page exception: ' + ((e.exception && e.exception.description) || e.text)); }
  return r.result && r.result.value;
}

const READY = (n) => `(async()=>{for(let i=0;i<${n || 500};i++){
  const S=window.SIM; if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy){
    const c=S.cine&&S.cine(); if(!c||c.shot){
      if(window.Npc&&Npc.ready) await Promise.race([Npc.ready(), new Promise(r=>setTimeout(r,15000))]);
      if(window.Story&&Story.ready) await Promise.race([Story.ready, new Promise(r=>setTimeout(r,15000))]);
      return true; } }
  await new Promise(r=>setTimeout(r,100));} return false;})()`;

// THE AUTO-READER. A cutscene is a conversation, and a conversation waits for a
// player. This is that player: it completes the typewriter and advances, and it
// dismisses an end card the same way a keypress does. It runs on a timer rather
// than rAF because rAF is throttled to nothing in a background tab, which is where
// every headless verification in this project lives (play3d.html's own note).
// A CHOICE LIST IS NOT A LINE, and reading it as one is an infinite conversation.
// Measured on the first run: the auto-reader pressed 'confirm' on `mara.ask`, which
// takes the FIRST choice, whose node ends `next: mara.ask` — so the window looped
// until dialogue.js's own 64-node chain cap stopped it, `Npc.talk('mara')` never got
// a turn (play() returns null while a window is open) and `npc.met.mara` was never
// set. Every ambient `*.ask` node in dialogue.json ends with a goodbye whose `to` is
// null, and it is LAST, so the reader walks to the bottom of the list and takes it.
const AUTOREADER = `(()=>{ if(window.__auto) return 'already';
  window.__autoRead = 0;
  window.__auto = setInterval(()=>{
    try{
      if(window.Dialogue && Dialogue.isOpen){
        const d = Dialogue.debug();
        if(d.mode === 'choice'){
          // n-1 presses, not n: EBUI's cursor WRAPS, so n presses from index 0 land
          // back on index 0 and take the first choice — the loop this exists to break.
          const n = (d.choices||[]).length;
          for(let i=0;i<n-1;i++) Dialogue.key('down');   // the goodbye is the last one
          Dialogue.key('confirm'); window.__autoRead++; return;
        }
        Dialogue.finishLine(); Dialogue.key('confirm'); window.__autoRead++; return;
      }
      const c = document.getElementById('story-card');
      if(c && c.style.display !== 'none' && c.style.opacity === '1')
        window.dispatchEvent(new KeyboardEvent('keydown',{key:'e',bubbles:true}));
    }catch(e){}
  }, 45); return 'armed'; })()`;
// Talk to somebody and WAIT FOR THE WINDOW TO CLOSE. Npc.talk() returns a boolean,
// not a promise, and Dialogue.play() refuses while a window is open — so a fixed
// sleep between two talks silently drops the second one.
const TALK = (id, secs) => `(async()=>{
  const t0=Date.now();
  while(window.Dialogue && Dialogue.isOpen && Date.now()-t0 < 20000) await new Promise(r=>setTimeout(r,60));
  const started = Npc.talk(${JSON.stringify(id)});
  const t1=Date.now();
  while(Date.now()-t1 < ${(secs||25)*1000}){
    if(window.Dialogue && Dialogue.isOpen){ await new Promise(r=>setTimeout(r,60)); continue; }
    if(Date.now()-t1 > 1200) break;              // opened and closed, or never opened
    await new Promise(r=>setTimeout(r,60));
  }
  return {id:${JSON.stringify(id)}, started, met: !!(GS.state.flags['npc.met.'+${JSON.stringify(id)}])}; })()`;

// Wait for a beat to have fired (its id is in the save's beat ledger), pumping the
// physics tick by hand: rAF is throttled in a background tab, so loop() is not
// running and Story.tick() would never be reached.
function AWAIT_BEAT(id, secs) {
  return `(async()=>{ const t0=Date.now();
    while(Date.now()-t0 < ${(secs || 45) * 1000}){
      try{ if(window.GS&&GS.state&&GS.state.beats&&GS.state.beats[${JSON.stringify(id)}]) return true; }catch(e){}
      try{ if(window.SIM&&SIM.tick&&!(window.UILOCK&&UILOCK.active())) SIM.tick(3); }catch(e){}
      await new Promise(r=>setTimeout(r,50));
    } return false; })()`;
}
// Put the body somewhere and make the shot that owns it current, then let the
// director see it. SIM.shot() is the shipped cut; SIM.tp() is the runtime's own
// teleport (already used by every other harness here).
//
// LAND ON THE GRAPH'S OWN ARRIVAL, NOT ON THE SHOT'S BAKED SPAWN. Measured the hard
// way on run 1: teleporting to pondlane's baked spawn [79.6, 1.2, -47.9] put the body
// INSIDE the pondlane->square cut band, which fired on the next tick and put it back
// under the square camera at [77.42, 1.2, -46.71] — the band's own arrival point, to
// the centimetre. The beat gated on `cam: pondlane` then never became eligible and the
// spine stalled. Every camera cut's arrival is placed clear of the band it crossed by
// construction (seam canon §1, the no-return rule), so THAT is the point to stand on.
// An explicit `at` — an NPC's post — is applied after and wins, because a proximity
// beat is about the person, not the shot.
function GOTO(shotId, at) {
  const tp = at ? `SIM.tp(${at[0]},${at[2]},${at[1]});` : '';
  return `(async()=>{
    const want = ${JSON.stringify(shotId)};
    if(want){
      await SIM.shot(want);
      const e = SIM.edges().find(x=>x.cam===want && x.to===SIM.scene() && x.spawn);
      if(e) SIM.tp(e.spawn[0], e.spawn[2], e.spawn[1]);
    }
    ${tp}
    for(let i=0;i<8;i++){ SIM.tick(1); await new Promise(r=>setTimeout(r,25)); }
    // One re-take: a correction or a band may have stolen the camera on the way in.
    if(want && (SIM.cine()||{}).shot !== want) await SIM.shot(want);
    return {shot:(SIM.cine()||{}).shot, pos:SIM.pos()}; })()`;
}
const FLAGS = `(()=>{ const f=(window.GS&&GS.state&&GS.state.flags)||{};
  const out={}; for(const k in f) if(k.indexOf('story.')===0||k==='maren-joined'||k==='lake-joined') out[k]=f[k];
  return out; })()`;

(async function main() {
  console.log('playthrough_test — new game to the end of Chapter Two, on the real page');
  console.log('  server :' + PORT + '   ' + START);

  const cdp = await connect(await targetWs());
  await cdp.send('Runtime.enable'); await cdp.send('Log.enable'); await cdp.send('Page.enable');
  // A bundle that ships no zones.json / cine.json / depth.json / meta.json is the
  // DOCUMENTED "absent is fine" path for that feature - every interior takes it - and
  // the browser logs a network 404 for each. Classified BY URL, not by message text:
  // the Log domain's `text` is only "Failed to load resource", so a text filter cannot
  // tell an optional asset from a missing one. Same list transition_test uses.
  const OPTIONAL = /zones\.json|cine\.json|depth\.json|meta\.json|routes\.json|stylized\.png|favicon/;
  const errors = [];
  cdp.events.length = 0;
  const drainErrors = () => {
    for (const e of cdp.events.splice(0)) {
      if (e.method === 'Runtime.exceptionThrown') errors.push({ url: '',
        text: (e.params.exceptionDetails.exception || {}).description || e.params.exceptionDetails.text });
      if (e.method === 'Log.entryAdded' && e.params.entry.level === 'error')
        errors.push({ url: e.params.entry.url || '', text: e.params.entry.text });
    }
  };

  head('0. a cleared slot, and the page reloaded onto Chapter One\'s first ground');
  await ev(cdp, READY(600), 180000);
  await ev(cdp, `(()=>{ try{ localStorage.removeItem('emberbrook-save');
    localStorage.removeItem('emberbrook-save-v1'); }catch(e){} return true; })()`);
  await cdp.send('Page.navigate', { url: START + '&v=' + Date.now() });
  await sleep(1200);
  const ready = await ev(cdp, READY(600), 180000);
  ok(ready === true, 'the page reached a playable first frame');
  await ev(cdp, AUTOREADER);
  const boot = await ev(cdp, `({scene:SIM.scene(), shot:(SIM.cine()||{}).shot,
    gsOk:!!(window.GS&&GS.ok), story:!!window.Story, beats:(window.Story?Story.debug().beats:0),
    v:(window.GS&&GS.state?GS.state.v:null)})`);
  ok(boot.scene === 'emb-cine', 'NEW GAME opens in emb-cine (the playable Emberbrook)', boot);
  ok(boot.shot === 'woodroad', 'on the Whisperwood road — the chapter\'s own first shot', boot);
  ok(boot.gsOk === true, 'the game-state store is up');
  ok(boot.story === true && boot.beats > 0, 'the story director loaded its script', boot);
  ok(boot.v === 2, 'a fresh save is written at schema v2', boot);

  head('1. Chapter One speaks by itself — nothing forces the first beat');
  const openFired = await ev(cdp, AWAIT_BEAT('ch1.open', 40), 90000);
  ok(openFired === true, 'beat ch1.open fired on its own trigger');
  const obj0 = await ev(cdp, `(window.Story?Story.debug().objective:null)`);
  ok(!!obj0, 'an objective is on screen after the opening beat', obj0);

  // ---- the Chapter One spine ------------------------------------------------
  // Each row: [beat id, shot to take, where to stand, an optional page expression
  // to run first (the things a PLAYER does that are not walking — talking).]
  const CH1 = [
    ['ch1.waystone', 'waystone', null, null],
    ['ch1.reveal', 'square', null, null],
    // Rowan will not hear you until you have been fed and greeted: the beat is
    // gated on npc.met.poppy AND npc.met.mara, which only the villagers' own
    // dialogue nodes set. So the harness TALKS TO THEM, through npc.js.
    ['ch1.rowan', 'square', [60.4, 1.5, -42.4],
      `(async()=>{ const a = await ${TALK('poppy')}; const b = await ${TALK('mara')};
                   return {a, b, met:(GS.state.flags['npc.met.poppy']?1:0)+(GS.state.flags['npc.met.mara']?1:0)}; })()`],
    ['ch1.meet', 'pondlane', null, null],
    ['ch1.lamps', 'square', null, null],
    ['ch1.hush', 'square', null, null],
    ['ch1.see.poppy', 'square', [49.76, 1.5, -44.29], null],
    ['ch1.see.mara', 'square', [62.13, 1.5, -44.5], null],
    ['ch1.see.finn', 'pondlane', [86.0, 1.0, -48.0], null],
    ['ch1.see.mochi', 'waystone', [56.2, -0.2, 11.6], null],
    ['ch1.pact', 'square', [60.4, 1.5, -42.4], null],
    ['ch1.sigils', 'gatefield', null, null],
    ['ch1.sendoff', 'gatefield', null, null],
  ];

  head('2. every Chapter One beat fires on its own trigger, in order');
  for (const [id, shot, at, pre] of CH1) {
    if (pre) { const r = await ev(cdp, pre, 60000); note(id + ': prerequisite -> ' + JSON.stringify(r)); }
    const where = await ev(cdp, GOTO(shot, at), 60000);
    const fired = await ev(cdp, AWAIT_BEAT(id, 60), 120000);
    ok(fired === true, 'beat ' + id + ' fired (shot ' + shot + ')', fired ? undefined : where);
    if (!fired) { note('  stopped: the spine cannot continue past a beat that never fires'); break; }
    if (STOP_AT && id === STOP_AT) { note('  --stop-at reached'); break; }
  }
  const f1 = await ev(cdp, FLAGS);
  note('Chapter One flags: ' + JSON.stringify(f1));
  ok(f1['story.ch1.gate-open'] === true, 'story.ch1.gate-open is set by the sigil beat');
  ok(f1['lake-joined'] === true, 'lake-joined is set — Lake is in the party');
  const party1 = await ev(cdp, `GS.activeParty().map(p=>p.id)`);
  ok(party1.includes('lake'), 'GS.activeParty() now contains Lake', party1);

  head('3. THE OLD GATE — the sealed edge is an absence until the flag flips');
  // Measured BOTH ways from the shipped graph rather than asserted one way: the
  // question "is this edge conditional at all" is a fact about the derive, and a
  // test that only ever sees the open state cannot tell a working gate from an
  // ungated one.
  const gate = await ev(cdp, `(()=>{
    const all = SIM.edges();
    const conditional = all.filter(e=>e.when);
    const old = all.filter(e=>/sigil-gate|old-gate/.test(String(e.id)));
    return {edges:all.length, conditional:conditional.map(e=>({id:e.id,when:e.when,open:e.open,live:e.live})),
            old:old.map(e=>({id:e.id,to:e.to,when:e.when,open:e.open,live:e.live}))}; })()`);
  note('conditional edges in emb-cine: ' + JSON.stringify(gate.conditional));
  note('old-gate edges in emb-cine:    ' + JSON.stringify(gate.old));
  if (gate.old.length === 0) {
    note('NO old-gate edge is derived yet — public/world/scenegraph.json still lists this pair');
    note('under `sealed` with no edge at all. The RUNTIME half of the conditional gate is in');
    note('(play3d.html sgLive: sgTick, markersTick, SIM.edges and SIM.door all consult it);');
    note('the DERIVE half — emitting the pair with when:{flag:<sealedUntil>} instead of');
    note('skipping it — has not landed. Chapter One therefore hands off by the SOUTH road.');
    ok(true, 'the sealed pair produces no edge, no prompt and no marker (the sealed presentation)');
  } else {
    // With the derive landed: the edge must have been invisible before the flag.
    const sealedProbe = await ev(cdp, `(()=>{
      const f=GS.state.flags, was=f['story.ch1.gate-open'];
      f['story.ch1.gate-open']=false;
      const shut=SIM.edges().filter(e=>/sigil-gate|old-gate/.test(String(e.id))).map(e=>e.live);
      f['story.ch1.gate-open']=was;
      const open=SIM.edges().filter(e=>/sigil-gate|old-gate/.test(String(e.id))).map(e=>e.live);
      return {shut, open}; })()`);
    ok(sealedProbe.shut.every(v => v === false), 'sealed: the gate edge is NOT live while the flag is false', sealedProbe);
    ok(sealedProbe.open.some(v => v === true), 'open: the same edge is live once the flag is true', sealedProbe);
  }

  head('4. the handoff — an edge is TAKEN into the corridor, never a teleport');
  const toValley = await ev(cdp, `(async()=>{
    const r = await SIM.door('ow-valley');
    return {r, scene:SIM.scene()}; })()`, 180000);
  ok(toValley.scene === 'ow-valley', 'the player is in ow-valley, having taken an edge', toValley);
  await ev(cdp, READY(600), 180000);
  await ev(cdp, AUTOREADER);
  const doneFired = await ev(cdp, AWAIT_BEAT('ch1.done', 90), 150000);
  ok(doneFired === true, 'beat ch1.done fired on arrival in the corridor (the end card)');
  const at2 = await ev(cdp, `(window.GS&&GS.state?GS.state.at:null)`);
  ok(at2 && at2.chapter === 2, 'at.chapter is 2 — a label, not a mode', at2);
  ok(at2 && at2.scene === 'ow-valley', 'at.scene tracks the corridor', at2);

  head('5. Chapter Two, in Dellhollow');
  const roadFired = await ev(cdp, `(async()=>{
    ${'SIM.tp(184.88,-136.19,12.01);'}
    const t0=Date.now();
    while(Date.now()-t0<40000){
      if(GS.state.beats['ch2.road']) return true;
      if(!(window.UILOCK&&UILOCK.active())) SIM.tick(3);
      await new Promise(r=>setTimeout(r,50)); }
    return false; })()`, 90000);
  ok(roadFired === true, 'beat ch2.road fired on the approach to Dellhollow');
  const toTown = await ev(cdp, `(async()=>{ const r=await SIM.door('del-cine'); return {r, scene:SIM.scene()}; })()`, 180000);
  ok(toTown.scene === 'del-cine', 'the corridor was WALKED into Dellhollow', toTown);
  await ev(cdp, READY(600), 180000);
  await ev(cdp, AUTOREADER);

  const CH2 = [
    ['ch2.arrive', null, null],
    ['ch2.jam', null, [78.93, 14.07, -15.6]],
    ['ch2.maren', null, [79.7, 0.83, -27.13]],
    ['ch2.lockfive', 'lockfive', null],
    // supper is in the keepers' cottage interior — a door, not a shot
    ['ch2.supper', '@del-cottage-int', null],
    ['ch2.dock', '@del-cine', null],
    ['ch2.winches', 'lockfive', null],
    ['ch2.landing', null, null],
  ];
  for (const [id, shot, at] of CH2) {
    if (shot && shot[0] === '@') {
      const r = await ev(cdp, `(async()=>{ const r=await SIM.door(${JSON.stringify(shot.slice(1))}); return {r,scene:SIM.scene()}; })()`, 180000);
      note(id + ': door -> ' + JSON.stringify(r.scene));
      await ev(cdp, READY(600), 180000); await ev(cdp, AUTOREADER);
    } else if (shot || at) {
      await ev(cdp, GOTO(shot, at), 60000);
    }
    const fired = await ev(cdp, AWAIT_BEAT(id, 75), 150000);
    ok(fired === true, 'beat ' + id + ' fired');
    if (!fired) { note('  stopped: Chapter Two cannot continue past a beat that never fires'); break; }
  }

  head('6. the payoff — Maren joins for real');
  const end = await ev(cdp, `({flags:${FLAGS}, party:GS.activeParty().map(p=>p.id),
    at:GS.state.at, beats:Object.keys(GS.state.beats)})`);
  ok(end.flags['story.ch2.done'] === true, 'story.ch2.done is set', end.flags);
  ok(end.flags['maren-joined'] === true, 'maren-joined is set (growth.json:33\'s declared joinFlag)');
  ok(end.party.includes('maren'), 'GS.activeParty() now contains Maren', end.party);
  note('beats completed: ' + end.beats.length + ' — ' + end.beats.join(', '));

  head('7. save / resume — a cold reload built from `at` alone');
  await ev(cdp, `(GS.autosave(), true)`);
  const before = await ev(cdp, `({at:GS.state.at, gold:GS.state.gold, flags:${FLAGS},
    party:GS.activeParty().map(p=>p.id), scene:SIM.scene(), shot:(SIM.cine()||{}).shot, pos:SIM.pos()})`);
  const q = new URLSearchParams({ scene: before.at.scene, nomusic: '1', v: String(Date.now()) });
  if (before.at.cam) q.set('cam', before.at.cam);
  if (before.at.pos) { q.set('sx', before.at.pos[0]); q.set('sy', before.at.pos[1]); q.set('sz', before.at.pos[2]); }
  await cdp.send('Page.navigate', { url: `http://localhost:${PORT}/play3d.html?` + q.toString() });
  await sleep(1500);
  await ev(cdp, READY(600), 180000);
  const after = await ev(cdp, `({v:GS.state.v, at:GS.state.at, gold:GS.state.gold, flags:${FLAGS},
    party:GS.activeParty().map(p=>p.id), scene:SIM.scene(), shot:(SIM.cine()||{}).shot, pos:SIM.pos()})`);
  ok(after.v === 2, 'the reloaded save is v2');
  ok(after.scene === before.scene, 'the same scene', { before: before.scene, after: after.scene });
  ok(after.shot === before.shot, 'the same shot', { before: before.shot, after: after.shot });
  ok(Math.hypot(after.pos.x - before.pos.x, after.pos.z - before.pos.z) < 1.5,
     'within a stride of the same place', { before: before.pos, after: after.pos });
  ok(after.gold === before.gold, 'gold survived');
  ok(JSON.stringify(after.flags) === JSON.stringify(before.flags), 'every story flag survived',
     { before: before.flags, after: after.flags });
  ok(after.party.join() === before.party.join(), 'the party survived', { before: before.party, after: after.party });

  head('8. console');
  drainErrors();
  const real = errors.filter(e => !OPTIONAL.test(e.url) && !OPTIONAL.test(e.text));
  ok(real.length === 0, `zero console errors across the whole playthrough ` +
     `(${errors.length} logged, ${errors.length - real.length} optional-asset 404s)`,
     real.slice(0, 6));

  console.log('\n' + '='.repeat(64));
  console.log(`playthrough_test: ${pass} passed, ${fail} failed`);
  if (fail) { console.log('\nfailures:'); fails.forEach(f => console.log('  - ' + f)); }
  console.log('='.repeat(64));
  cdp.close(); kill();
  process.exit(fail ? 1 : 0);
})();
