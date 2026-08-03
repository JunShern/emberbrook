/* adapter_emberbrook.mjs — LAYER 2: THE GAME. ALL THE COUPLING LIVES HERE.
 *
 * This is the thick, unglamorous, deliberately game-specific layer, and the user
 * accepted that explicitly: checkpointing and motor control cannot be abstract.
 * Everything that knows about play3d.html, SIM, GS, story.json, the save schema,
 * three.js cameras and the walk network is in this file and nowhere else. Layer 1
 * (agent.mjs) and layer 3 (episode.mjs) never import play3d concepts.
 *
 * THE CONTRACT IT IMPLEMENTS:
 *   await adapter.open()                      launch Chrome, attach, boot the page
 *   await adapter.setup(plan)                 new game | checkpoint | repro save
 *   await adapter.observe()   -> {screenshot, text, percept, framePath}
 *   await adapter.truth()     -> harness-only ground truth (NEVER to the agent)
 *   await adapter.act(intent) -> {summary, legs, transcript}
 *   await adapter.settle()                    wait out fades and empty modals
 *   adapter.checkpoints()     -> derived from story.json AT RUN TIME
 *   await adapter.close()
 *
 * ============================== THE HARD RULE ===============================
 * SETUP MAY USE THE SAVE SYSTEM. GAMEPLAY IS KEYBOARD ONLY.
 * A human loads a save, so constructing one and loading it is fair. A human does
 * not teleport, so once the first frame is up, every metre in this file is walked
 * by a key held down over CDP. `SIM.tp` appears nowhere; the resume URL's
 * &sx/&sy/&sz appear only inside setup(). If you ever find yourself reaching for
 * SIM during play, you are rebuilding playthrough_test, which is the blind test
 * this whole instrument exists to replace.
 *
 * ============================ THE MOTOR CONTROL =============================
 * A waypoint is a pixel. Turning it into a walk is three steps:
 *   1. UN-PROJECT. Build the camera basis from the LIVE camera (SIM.cam(): world
 *      position, forward, VERTICAL fov in degrees, aspect) — not from cine.json,
 *      so it is right the instant after a cut. Make the ray for the normalised
 *      coordinate exactly as nav_eval.mjs's rayOf does, then MARCH it until it
 *      passes under the walk network (SIM.walkFloors) and bisect the crossing.
 *      Falls back to all floors and says so: "you pointed somewhere you cannot
 *      stand" is a finding, not an error.
 *      WHAT IT DOES NOT MODEL: there is no depth plate here, so the ray does not
 *      stop at an occluder — aim at a wall and the march can find the floor
 *      behind it. That is not silently wrong: the executor then walks into the
 *      wall, and the leg is recorded as a stall with its intended and closed
 *      distances. The failure shows up in the data instead of hiding in the target.
 *   2. STEER. Project the vector to the target onto the camera's own ground basis
 *      and pick the 8-way key combination nearest to it. This is what a person
 *      does: they see where they want to go and push the stick that way. It is
 *      also exactly the basis play3d's phys() uses, so the keys mean on the way in
 *      what they mean on the way out.
 *   3. CLOSE THE LOOP. Hold for one short burst, re-measure, repeat. Stop on
 *      arrival, on six bursts without gain, on five bursts without movement, on a
 *      modal opening, or on the time budget.
 *
 * FAILING TO REACH A WAYPOINT IS A FREE BUG SIGNAL, and it is the highest-yield
 * detector here: every leg reports DISTANCE INTENDED vs DISTANCE CLOSED, so "the
 * agent asked for 9 m and got 0.3 m" is captured without the model having to
 * notice it was blocked or be articulate about it.
 *
 * ================================ CHECKPOINTS ===============================
 * DERIVED FROM story.json AT RUN TIME, never stored. Each beat already declares
 * its scene, cam, `at` and the flags it sets, so the state "just before beat N" is
 * the union of everything beats 1..N-1 did — about two dozen checkpoints for free,
 * and none of them can rot, because there is no blob to go stale. The BRIEF (what
 * am I supposed to be doing here) is derived the same way: the last `objective`
 * any earlier beat set, which is literally the line the game would be drawing.
 * docs/qa/playtest/briefs.json may add a sentence per beat; a brief naming a beat
 * story.json no longer has is WARNED about, so a stale instruction is loud.
 *
 * ================================= FRAME RATE ===============================
 * Headless rAF here runs at ~118 Hz, not 60, so the body walks about twice as fast
 * as it does for a person (play3d's SPD is per physics tick and physics rides rAF).
 * The executor is a CLOSED LOOP — it measures metres closed, never seconds held —
 * so this changes pacing, not verdicts. It does mean an overshoot is a harness
 * artefact rather than a game bug, and it is why ARRIVE_M is a body-width, not a
 * centimetre.
 */
import { spawn } from 'child_process';
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { createRequire } from 'module';
import { freePort, killOrphans, findPage, sweepStaleProfiles } from '../cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const ROOT = join(dirname(new URL(import.meta.url).pathname), '../..');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------------------------------------------------------------------------
// PERCEPTION. THIS EXPRESSION TOUCHES `document` AND NOTHING ELSE. Before adding a
// reading, ask whether it is DRAWN ON THE SCREEN. If it is not, it belongs in
// TRUTH_JS and the agent must never see it.
//   #story-obj    the objective line (story_runtime.js:129)
//   #story-card   the full-screen chapter card (story_runtime.js:154)
//   #sgp          play3d's own doorway banner (play3d.html:1828)
//   .ebui-banner  ui_kit's prompt banner — NPC talk prompts, shop counters
//   .ebui-veil    any modal panel: dialogue, menu, shop (ui_kit.js:473)
// ---------------------------------------------------------------------------
const PERCEPT_JS = `(()=>{
  const vis = (e) => { if(!e) return false;
    const s = getComputedStyle(e);
    if (s.display==='none' || s.visibility==='hidden' || parseFloat(s.opacity||'1') < 0.06) return false;
    const r = e.getBoundingClientRect();
    return r.width > 2 && r.height > 2 && r.bottom > 0 && r.top < innerHeight; };
  const txt = (e) => e ? e.textContent.replace(/\\s+/g,' ').trim() : null;
  const out = { objective:null, prompts:[], dialogue:null, card:null };
  const ob = document.getElementById('story-obj');
  if (vis(ob)) out.objective = (txt(ob)||'').replace(/^[^A-Za-z0-9]+/, '');
  const sg = document.getElementById('sgp');
  if (vis(sg) && txt(sg)) out.prompts.push(txt(sg));
  for (const b of document.querySelectorAll('.ebui-banner')) if (vis(b) && txt(b)) out.prompts.push(txt(b));
  const veil = [...document.querySelectorAll('.ebui-veil')].filter(vis).pop();
  if (veil) {
    const rows = [...veil.querySelectorAll('.ebui-row, .ebui-choice, li, .row, .choice')].filter(vis)
      .map(r=>({ text: txt(r), selected: /sel|active|cursor/.test(r.className||'') }));
    out.dialogue = { speaker: txt(veil.querySelector('.ebui-title')) || null,
      text: txt(veil.querySelector('.ebui-body')) || null,
      foot: txt(veil.querySelector('.ebui-foot')) || null,
      choices: rows.length > 1 ? rows : null };
  }
  const c = document.getElementById('story-card');
  if (vis(c)) out.card = { title: txt(c.querySelector('.t')), sub: txt(c.querySelector('.s')),
                           prose: txt(c.querySelector('p')), hint: txt(c.querySelector('.k')) };
  return out; })()`;

// HARNESS BOOKKEEPING ONLY: stuck detection, the run log, the repro save, and the
// anchors triage measures from. Never assembled into a prompt — episode.mjs's
// firewall proves that per step rather than trusting this comment.
const TRUTH_JS = `(()=>{ const o={};
  try{ o.scene = SIM.scene(); }catch(e){}
  try{ const p = SIM.pos(); o.pos = [ +p.x.toFixed(2), +p.y.toFixed(2), +p.z.toFixed(2) ]; }catch(e){}
  try{ o.shot = (SIM.cine()||{}).shot || null; }catch(e){}
  try{ o.locked = !!(window.UILOCK && UILOCK.active()); }catch(e){}
  try{ o.beats = Object.keys((window.GS&&GS.state&&GS.state.beats)||{}); }catch(e){}
  try{ const f=(window.GS&&GS.state&&GS.state.flags)||{}; o.flags=Object.keys(f).filter(k=>f[k]); }catch(e){}
  try{ o.exits = SIM.edges().filter(e=>e.live).map(e=>e.id); }catch(e){}
  try{ o.save = (window.GS&&GS.state) ? JSON.parse(GS.serialize()) : null; }catch(e){}
  return o; })()`;

const READY_JS = `(async()=>{for(let i=0;i<600;i++){
  const S=window.SIM; if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy){
    const c=S.cine&&S.cine(); if(!c||c.shot){
      if(window.Npc&&Npc.ready) await Promise.race([Npc.ready(), new Promise(r=>setTimeout(r,15000))]);
      if(window.Story&&Story.ready) await Promise.race([Story.ready, new Promise(r=>setTimeout(r,15000))]);
      return true; } }
  await new Promise(r=>setTimeout(r,100));} return false;})()`;

// Motor-control helpers, installed in the page. Harness code that happens to run in
// the renderer: it converts a pixel to a world point and reports the geometry of a
// leg. IT NEVER MOVES ANYBODY.
const INSTALL_MOTOR = `(()=>{ if(window.__pt) return 'already';
  const V = { add:(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]], mul:(a,s)=>[a[0]*s,a[1]*s,a[2]*s],
    dot:(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2],
    cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],
    norm:(a)=>{const l=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/l,a[1]/l,a[2]/l];} };
  function basis(){ const c=SIM.cam(); const f=V.norm(c.fwd);
    const r=V.norm(V.cross(f,[0,1,0])); const u=V.cross(r,f);
    return {pos:c.pos,f,r,u,fov:c.fov,aspect:c.aspect}; }
  // fov is VERTICAL degrees. Measured against the running page in
  // findability_test's header; reading it as horizontal moves a target most of a
  // frame width and produces a completely wrong, completely confident answer.
  function rayOf(nx,ny){ const b=basis();
    const ty=Math.tan(b.fov*Math.PI/180/2), tx=ty*b.aspect;
    const sx=nx*2-1, sy=1-ny*2;
    return {b, d:V.norm(V.add(b.f, V.add(V.mul(b.r,sx*tx), V.mul(b.u,sy*ty))))}; }
  function hit(nx,ny,far){
    const {b,d}=rayOf(nx,ny);
    const tops=(x,z,walk)=>{ try{ const ys=walk?SIM.walkFloors(x,z):SIM.floors(x,z);
      return (ys&&ys.length)?ys.slice().sort((p,q)=>q-p):[]; }catch(e){ return []; } };
    // 0.5 m near, 1.0 m far, then bisect. Each step is a BVH query against the
    // walk network and a 0.25 m march to 160 m is 640 of them per waypoint, on the
    // page's own main thread, while it is rendering — measured slow enough to
    // matter. The bisection recovers the precision the coarser march gives up.
    const march=(walk)=>{ let prev=null;
      for(let t=0.6;t<=(far||160);t+= (t<40?0.5:1.0)){
        const p=V.add(b.pos,V.mul(d,t)); const ys=tops(p[0],p[2],walk);
        const under = ys.length && p[1] <= ys[0]+0.05;
        if(under && prev && !prev.under){
          let a=prev.t, c2=t;
          for(let i=0;i<16;i++){ const m=(a+c2)/2; const q=V.add(b.pos,V.mul(d,m));
            const y2=tops(q[0],q[2],walk); (y2.length && q[1]<=y2[0]+0.05)?c2=m:a=m; }
          const q=V.add(b.pos,V.mul(d,c2)); const y2=tops(q[0],q[2],walk);
          return {t:+c2.toFixed(2), p:[+q[0].toFixed(2), +(y2.length?y2[0]:q[1]).toFixed(2), +q[2].toFixed(2)]};
        }
        prev={t,under};
      } return null; };
    const w=march(true); if(w) return {ok:true,onNetwork:true,...w};
    const f2=march(false); if(f2) return {ok:true,onNetwork:false,...f2};
    return {ok:false,reason:'the ray for that pixel never reaches a surface (sky, or past the world)'}; }
  // The direction to a world point, expressed as an octant of the CAMERA's ground
  // basis — which is the basis play3d's own phys() uses, so the keys mean the same
  // thing on the way in as on the way out. Returning the octant INDEX rather than
  // the keys is what lets the executor slide along a wall: index+/-1 is 45 degrees off.
  function dirTo(target){ const b=basis(); const p=SIM.pos();
    const v=[target[0]-p.x,0,target[2]-p.z]; const dist=Math.hypot(v[0],v[2]);
    if(dist<1e-3) return {dist:0,oct:0};
    const fwd=V.norm([b.f[0],0,b.f[2]]), rgt=V.norm([b.r[0],0,b.r[2]]);
    const a=V.dot(v,fwd)/dist, c=V.dot(v,rgt)/dist;
    // oct 0 = straight up (away from camera), then clockwise in 45 degree steps.
    const oct=((Math.round(Math.atan2(c,a)/(Math.PI/4))%8)+8)%8;
    return {dist:+dist.toFixed(2),oct}; }
  window.__pt={hit,dirTo,where(){const p=SIM.pos();return [+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)];}};
  return 'armed'; })()`;

const KEYS = {
  up: { key: 'w', code: 'KeyW', vk: 87 }, down: { key: 's', code: 'KeyS', vk: 83 },
  left: { key: 'a', code: 'KeyA', vk: 65 }, right: { key: 'd', code: 'KeyD', vk: 68 },
  e: { key: 'e', code: 'KeyE', vk: 69 }, enter: { key: 'Enter', code: 'Enter', vk: 13 },
  space: { key: ' ', code: 'Space', vk: 32 }, escape: { key: 'Escape', code: 'Escape', vk: 27 },
};
const BURST_MS = 150;    // one push of the stick
const ARRIVE_M = 1.2;    // "near enough" — a body is 0.6 m wide

// --------------------------------------------------------------------------
export function checkpointsFromStory() {
  const STORY = JSON.parse(readFileSync(join(ROOT, 'public/game/story.json'), 'utf8'));
  let BRIEFS = {};
  const bp = join(ROOT, 'docs/qa/playtest/briefs.json');
  if (existsSync(bp)) { try { BRIEFS = JSON.parse(readFileSync(bp, 'utf8')).briefs || {}; } catch (e) { } }
  const out = []; const flags = {}; const beats = {};
  let objective = null, lastAt = null, lastScene = null, lastCam = null;
  for (const b of STORY.beats || []) {
    // A CAM AND A POSITION ONLY CARRY WITHIN A SCENE, and the reset has to happen
    // BEFORE the inheritance or it does not happen at all. Carrying `square` across
    // a door into an interior builds a checkpoint naming a camera that bundle has
    // never heard of: ignored at best, an undefined shot at worst.
    if (b.scene && b.scene !== lastScene) { lastScene = b.scene; lastCam = null; lastAt = null; }
    out.push({ id: b.id, chapter: b.chapter || 1, scene: b.scene,
      cam: b.cam || lastCam, pos: b.at || lastAt,
      objective, flags: { ...flags }, beats: { ...beats }, brief: BRIEFS[b.id] || null });
    beats[b.id] = true;
    for (const d of b.do || []) {
      if (d.setFlags) Object.assign(flags, d.setFlags);
      if (d.objective !== undefined) objective = d.objective;
    }
    if (b.cam) lastCam = b.cam;
    if (b.at) lastAt = b.at;
  }
  const known = new Set(out.map(c => c.id));
  const stale = Object.keys(BRIEFS).filter(k => !known.has(k));
  return { checkpoints: out, staleBriefs: stale };
}

/** The text the game DREW, flattened into the string the agent reads. */
export function flattenPercept(p) {
  const L = [];
  L.push(p.objective ? `OBJECTIVE ON SCREEN: ${p.objective}` : 'OBJECTIVE ON SCREEN: (none shown)');
  if (p.card) L.push(`FULL-SCREEN CARD: ${[p.card.title, p.card.sub, p.card.prose, p.card.hint].filter(Boolean).join(' / ')}`);
  if (p.dialogue) {
    L.push(`A DIALOGUE BOX IS OPEN — speaker: ${p.dialogue.speaker || '(none)'}`);
    if (p.dialogue.text) L.push(`  says: ${p.dialogue.text}`);
    if (p.dialogue.choices) L.push('  CHOICES: ' + p.dialogue.choices.map((c, i) => `[${i}] ${c.text}`).join('   '));
    if (p.dialogue.foot) L.push(`  footer: ${p.dialogue.foot}`);
  }
  if (p.prompts && p.prompts.length) L.push('PROMPT BANNER ON SCREEN: ' + p.prompts.join(' ; '));
  return L.join('\n');
}

export const PERSONA = [
  'You are playtesting Emberbrook, a JRPG with pre-rendered backgrounds in the style of',
  'Final Fantasy IX. You control ONE character. The camera is FIXED for each area and you',
  'cannot turn it. You see exactly what a player sees: this screenshot and the text the game',
  'draws on it. You have no map, no coordinates and no quest log beyond what is on screen.',
  'Your character is a small figure standing somewhere in the picture.',
].join('\n');

// ===========================================================================
export function makeAdapter(opt) {
  const { port = 3000, headed = false, chromeBin, framesDir, viewport = [1280, 720] } = opt || {};
  const CHROME = chromeBin || process.env.CHROME_BIN ||
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  let cdp = null, chrome = null, profile = null, closed = false, frameN = 0;

  const send = (m, p) => cdp.send(m, p);
  async function ev(expr, t) {
    const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, userGesture: true, timeout: t || 120000 });
    if (r.exceptionDetails) throw new Error('page exception: ' + ((r.exceptionDetails.exception || {}).description || r.exceptionDetails.text));
    return r.result && r.result.value;
  }
  function keyEvent(type, k) {
    const p = { type, key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk };
    if (type === 'keyDown' && k.key.length === 1) p.text = k.key;
    return send('Input.dispatchKeyEvent', p);
  }
  async function hold(names, ms) {
    const ks = names.map(n => KEYS[n]).filter(Boolean);
    for (const k of ks) await keyEvent('keyDown', k);
    await sleep(ms);
    for (const k of ks) await keyEvent('keyUp', k);
  }
  async function tap(name) { const k = KEYS[name] || KEYS.e; await keyEvent('keyDown', k); await sleep(45); await keyEvent('keyUp', k); }

  function urlFor(scene, cam, pos, extra) {
    const q = new URLSearchParams({ nomusic: '1' });
    if (scene) q.set('scene', scene);
    if (cam) q.set('cam', cam);
    if (pos) { q.set('sx', pos[0]); q.set('sy', pos[1]); q.set('sz', pos[2]); }
    for (const [k, v] of Object.entries(extra || {})) q.set(k, v);
    return `http://localhost:${port}/play3d.html?` + q.toString();
  }

  return {
    PERSONA, flattenPercept,
    checkpoints() { return checkpointsFromStory(); },
    url: urlFor,

    async open(startUrl) {
      const cdpPort = await freePort();
      profile = join(process.env.TMPDIR || '/tmp', 'llm-playtester-profile-' + process.pid);
      sweepStaleProfiles('llm-playtester-profile-');
      killOrphans(profile);
      rmSync(profile, { recursive: true, force: true });
      // Real GPU: this tool PHOTOGRAPHS the render, and cdp.mjs's note says forcing
      // swiftshader while something else owns the CPU makes Chrome miss its window.
      // The four throttling flags are not decoration — play3d's whole world runs in
      // requestAnimationFrame, and a throttled rAF is a player who cannot walk.
      chrome = spawn(CHROME, [
        `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${profile}`,
        '--no-first-run', '--no-default-browser-check', '--disable-extensions',
        '--disable-background-timer-throttling', '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding', '--disable-features=CalculateNativeWinOcclusion',
        '--autoplay-policy=no-user-gesture-required',
        `--window-size=${viewport[0]},${viewport[1] + 80}`, ...(headed ? [] : ['--headless=new']),
        startUrl,
      ], { stdio: 'ignore' });
      const url = await findPage(cdpPort, { tries: 200, label: 'llm_playtester' });
      cdp = await new Promise((res, rej) => {
        const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
        const pend = new Map(); let id = 0;
        ws.on('open', () => res({ send(m, p) { return new Promise((ok, no) => { const mid = ++id; pend.set(mid, { ok, no }); ws.send(JSON.stringify({ id: mid, method: m, params: p || {} })); }); } }));
        ws.on('error', rej);
        ws.on('message', raw => { let m; try { m = JSON.parse(raw); } catch (e) { return; }
          if (m.id && pend.has(m.id)) { const { ok, no } = pend.get(m.id); pend.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); } });
      });
      await send('Runtime.enable'); await send('Page.enable'); await send('Log.enable');
      // Deterministic viewport: --window-size alone gave 1280x633 on this machine,
      // and a screen whose size depends on the host is a percept that is not
      // comparable between runs — or between models in a benchmark.
      await send('Emulation.setDeviceMetricsOverride', { width: viewport[0], height: viewport[1], deviceScaleFactor: 1, mobile: false });
      try { await send('Emulation.setFocusEmulationEnabled', { enabled: true }); } catch (e) { }
      return await ev(READY_JS, 180000);
    },

    /* ------------------------------------------------------------------ SETUP
     * THE ONLY PLACE THE SAVE SYSTEM AND THE RESUME URL MAY BE TOUCHED.
     * plan = {kind:'newgame'} | {kind:'checkpoint', scene, cam, pos, patch}
     *      | {kind:'repro', scene, cam, pos, save}
     */
    async setup(plan) {
      if (plan.kind === 'newgame') {
        await ev(`(()=>{try{localStorage.removeItem('emberbrook-save');localStorage.removeItem('emberbrook-save-v1');}catch(e){}return 1})()`);
        await send('Page.navigate', { url: urlFor(plan.scene, plan.cam) });
      } else {
        const p = plan.save ? { whole: plan.save } : { patch: plan.patch };
        await ev(`(()=>{ const p=${JSON.stringify(p)};
          if(p.whole){ localStorage.setItem('emberbrook-save', JSON.stringify(p.whole)); return 'whole'; }
          const st = JSON.parse(GS.serialize());
          Object.assign(st.flags, p.patch.flags||{}); Object.assign(st.beats, p.patch.beats||{});
          st.at = Object.assign({}, st.at, p.patch.at||{});
          localStorage.setItem('emberbrook-save', JSON.stringify(st)); return 'patched'; })()`);
        await send('Page.navigate', { url: urlFor(plan.scene, plan.cam, plan.pos, { v: String(Date.now()) }) });
      }
      await sleep(1400);
      const ok = await ev(READY_JS, 180000);
      // HIDE THE DEV HUD. play3d draws `#h` with the live scene, shot and pos(x,y,z)
      // in the top-left corner (play3d.html:1702). A shipping build would not, and a
      // screenshot containing it hands the agent the exact numbers this instrument
      // exists to withhold. This is the ONLY change the harness makes to the page,
      // and it REMOVES information.
      await ev(`(()=>{const s=document.createElement('style');s.textContent='#h{display:none!important}';document.head.appendChild(s);return 1})()`);
      await ev(INSTALL_MOTOR);
      await sleep(500);
      return ok;
    },

    /* A veil, a fade, or a modal with nothing drawn on it is not a decision — it is
     * a wait, and paying a model call to watch a transition is paying for nothing. */
    async settle(maxMs = 10000) {
      const t0 = Date.now();
      while (Date.now() - t0 < maxMs) {
        const busy = await ev(`(()=>{ try{
          const t = SIM.transitions(); const p = ${PERCEPT_JS};
          return (t&&t.busy) || (!!(window.UILOCK&&UILOCK.active()) && !(p.dialogue||p.card));
        }catch(e){ return false } })()`);
        if (!busy) return true;
        await sleep(250);
      }
      return false;                       // frozen with nothing on screen — a finding
    },

    async observe(tag) {
      const percept = await ev(PERCEPT_JS);
      const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 72 });
      let framePath = null;
      if (framesDir) {
        mkdirSync(framesDir, { recursive: true });
        framePath = join(framesDir, 'step-' + String(++frameN).padStart(3, '0') + (tag ? '-' + tag : '') + '.jpg');
        writeFileSync(framePath, Buffer.from(r.data, 'base64'));
      }
      return { screenshot: { mime: 'image/jpeg', data: r.data }, text: flattenPercept(percept), percept, framePath };
    },

    async truth() { return await ev(TRUTH_JS); },

    /* ONE WALK LEG. Real keys, closed loop, and it reports the geometry —
     * intended vs closed — which is the free bug signal. */
    async walkLeg(nx, ny, budgetMs) {
      await ev(INSTALL_MOTOR);
      // A LEG THAT NEVER GOT TO RUN IS NOT A BLOCKED PATH. If a beat fired or a
      // conversation opened between the screenshot and the first key, phys() is
      // frozen under UILOCK and the body cannot move — recording that as "closed
      // 0 m of 15 m" would manufacture a blocker out of a cutscene. Measured on the
      // first bring-up run: the waystone beat fired mid-route and produced exactly
      // that false leg.
      if (await ev(`(()=>{try{return !!(window.UILOCK&&UILOCK.active())}catch(e){return false}})()`))
        return { ok: false, nx, ny, reason: 'modal', detail: 'the game took control before the walk started', intended: 0, closed: 0 };
      const h = await ev(`window.__pt.hit(${nx},${ny})`);
      if (!h.ok) return { ok: false, nx, ny, reason: 'unprojection', detail: h.reason, intended: 0, closed: 0 };
      const from = await ev(`window.__pt.where()`);
      const d0 = Math.hypot(h.p[0] - from[0], h.p[2] - from[2]);
      const t0 = Date.now();
      let best = d0, sinceGain = 0, last = from, bursts = 0, slides = 0;
      /* THE SLIDE. A person who walks into a rock does not stand there pushing into
       * it — they angle off and go round. The first bring-up run failed exactly
       * here: the agent picked a perfectly sensible waypoint up the road, the body
       * met the road's own stone border at 45 degrees, travelled 0.0 m, and the leg
       * was recorded as a blocked path. That would have been a manufactured bug
       * report about a wall that any player walks around without noticing.
       * So: on a burst that moves nothing, try the octant 45 degrees to each side,
       * then 90. Only when NONE of the five headings moves the body is the path
       * actually blocked — and that is the finding worth filing. */
      const OFFSETS = [0, 1, -1, 2, -2];
      const OCT_KEYS = [['up'], ['up', 'right'], ['right'], ['down', 'right'],
                        ['down'], ['down', 'left'], ['left'], ['up', 'left']];
      while (Date.now() - t0 < (budgetMs || 9000)) {
        const st = await ev(`window.__pt.dirTo(${JSON.stringify(h.p)})`, 15000);
        if (st.dist <= ARRIVE_M) break;
        let moved = 0, now = last;
        for (const off of OFFSETS) {
          await hold(OCT_KEYS[(((st.oct + off) % 8) + 8) % 8], BURST_MS); bursts++;
          now = await ev(`window.__pt.where()`, 15000);
          moved = Math.hypot(now[0] - last[0], now[2] - last[2]);
          if (moved >= 0.10) { if (off !== 0) slides++; break; }
          if (Date.now() - t0 > (budgetMs || 9000)) break;
        }
        last = now;
        const d = Math.hypot(h.p[0] - now[0], h.p[2] - now[2]);
        if (d < best - 0.15) { best = d; sinceGain = 0; } else sinceGain++;
        if (moved < 0.10) break;                  // every heading refused: blocked
        if (sinceGain >= 8) break;                // moving, but not getting closer
        // A camera cut, a doorway or a story beat changes the world under the leg.
        if (await ev(`(()=>{try{return !!(window.UILOCK&&UILOCK.active())}catch(e){return false}})()`, 15000)) break;
      }
      const end = await ev(`window.__pt.where()`);
      const stoppedByModal = await ev(`(()=>{try{return !!(window.UILOCK&&UILOCK.active())}catch(e){return false}})()`);
      const dEnd = Math.hypot(h.p[0] - end[0], h.p[2] - end[2]);
      if (stoppedByModal)
        return { ok: false, nx, ny, reason: 'modal', detail: 'the game took control part-way through the walk',
          target: h.p, from, end, intended: +d0.toFixed(2), closed: +(d0 - dEnd).toFixed(2) };
      return { ok: true, nx, ny, onNetwork: h.onNetwork, target: h.p, from, end,
        intended: +d0.toFixed(2), remaining: +dEnd.toFixed(2), closed: +(d0 - dEnd).toFixed(2),
        travelled: +Math.hypot(end[0] - from[0], end[2] - from[2]).toFixed(2),
        closedFrac: d0 > 0.5 ? +((d0 - dEnd) / d0).toFixed(2) : 1,
        bursts, slides, arrived: dEnd <= ARRIVE_M, ms: Date.now() - t0 };
    },

    /* Read a whole conversation with real presses and hand back the transcript. A
     * player sees every line at once; paying one model call per line is paying to
     * read. A CHOICE IS THE PLAYER'S — the loop stops the moment one appears. */
    async readThrough(max = 40) {
      const seen = [];
      for (let n = 0; n < max; n++) {
        const p = await ev(PERCEPT_JS);
        if (p.dialogue && p.dialogue.choices) break;
        if (!p.dialogue && !p.card) break;
        // The typewriter draws the SAME line twice — once mid-type, once finished
        // with a '▼' advance caret — so a naive transcript is exactly double length
        // and reads like a stutter to whatever gets handed it. Strip the caret and
        // the narration bullet before comparing.
        const raw = p.dialogue
          ? ((p.dialogue.speaker ? p.dialogue.speaker + ': ' : '') + (p.dialogue.text || ''))
          : ('CARD: ' + [p.card.title, p.card.sub, p.card.prose].filter(Boolean).join(' — '));
        const line = raw.replace(/[▼✦▶]/g, '').replace(/\s+/g, ' ').trim();
        const prev = seen[seen.length - 1];
        if (line && prev !== line) {
          if (prev && line.startsWith(prev)) seen[seen.length - 1] = line;   // the same line, finished
          else seen.push(line);
        }
        await tap('e'); await sleep(320);
      }
      return seen;
    },

    async press(name) { await tap(name); await sleep(700); },
    async menuDown(n) { for (let i = 0; i < n; i++) { await tap('down'); await sleep(120); } },

    async close() {
      if (closed) return; closed = true;
      try { chrome && chrome.kill('SIGKILL'); } catch (e) { }
      try { profile && rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { }
    },
    _ev: ev,
  };
}
