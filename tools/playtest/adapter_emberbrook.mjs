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
 *   await adapter.observe()   -> {screenshot, text, percept, framePath,
 *                                 ready, why, frozen, meanL, waitedMs}
 *                              READY IS NOT DECORATION: it is false when the harness
 *                              could not get a painted frame, and layer 3 must not
 *                              show the agent a frame that says so. See FRAME_GATE_JS.
 *   await adapter.truth()     -> harness-only ground truth (NEVER to the agent)
 *   await adapter.act(intent) -> {summary, legs, transcript}
 *   await adapter.choose(n)                   pick entry n of the open list
 *   await adapter.settle()                    wait for a frame the player would see
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
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { createRequire } from 'module';
import { freePort, killOrphans, findPage, sweepStaleProfiles } from '../cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
// The luminance backstop needs a PNG decoder. pngjs is what nav_eval, findability_test
// and scene_redteam already read plates with. If it is ever gone, SAY SO — a silently
// disabled backstop is exactly the failure this whole gate exists to stop.
const PNG = (() => { try { return require('pngjs').PNG; } catch (e) {
  console.warn('  WARN pngjs is not installed: the playtester CANNOT measure whether a frame is black.\n' +
               '       The page-side readiness gate still runs, but the backstop that caught\n' +
               '       PT-20260803-005 is off. Install pngjs before trusting a clean run.');
  return null; } })();
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
//   .ebb-root     THE BATTLE SCREEN (battle_turnbased.js:766)
// ---------------------------------------------------------------------------
// THE BATTLE WAS MISSING FROM THIS LIST AND THAT MADE THE AGENT BLIND IN COMBAT
// (2026-08-03). A random encounter fired in the overworld; the whole percept was
// "OBJECTIVE ON SCREEN: Follow the road north", because a battle is not a
// .ebui-veil. The readiness gate then called a fully drawn, fully playable
// turn-based battle "a modal lock with nothing drawn on it" and the run stalled on
// it for four and a half minutes. The screen was at 117 luminance the whole time.
// A PERCEPT THAT OMITS A WHOLE GAME MODE IS NOT A NARROW PERCEPT, IT IS A BLIND ONE.
// ---------------------------------------------------------------------------
/* What a percept is when the page would not answer for one. NOT a percept the agent
 * is shown — observe() has already flagged the frame unready by then — but the shape
 * flattenPercept and the run log expect, so a busy moment is a blank rather than a
 * TypeError three layers up. */
const EMPTY_PERCEPT = { objective: null, prompts: [], dialogue: null, card: null, battle: null };

const PERCEPT_JS = `(()=>{
  const vis = (e) => { if(!e) return false;
    const s = getComputedStyle(e);
    if (s.display==='none' || s.visibility==='hidden' || parseFloat(s.opacity||'1') < 0.06) return false;
    const r = e.getBoundingClientRect();
    return r.width > 2 && r.height > 2 && r.bottom > 0 && r.top < innerHeight; };
  const txt = (e) => e ? e.textContent.replace(/\\s+/g,' ').trim() : null;
  const out = { objective:null, prompts:[], dialogue:null, card:null, battle:null };
  const cur = (e) => /(^|\\s)(cur|sel|selected|active)(\\s|$)/.test(e.className||'');
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
  const br = [...document.querySelectorAll('.ebb-root')].filter(vis).pop();
  if (br) {
    const rows = (sel, root) => [...(root||br).querySelectorAll(sel)].filter(vis)
      .map(e => ({ text: txt(e), selected: cur(e) })).filter(r => r.text);
    const cmdbox = br.querySelector('.ebb-cmds');
    const sub = br.querySelector('.ebb-sub');
    const subOpen = sub && vis(sub);
    out.battle = {
      zone: txt(br.querySelector('.ebb-hud .zone')), round: txt(br.querySelector('.ebb-hud .rnd')),
      actor: txt(br.querySelector('.ebb-actor')), log: txt(br.querySelector('.ebb-logtxt')),
      // .ebb-cmds carries the class "idle" while it is somebody else's turn
      // (battle_turnbased.js:322) — that is the difference between a menu you may
      // drive and a menu you are watching.
      yourTurn: !!cmdbox && !/(^|\\s)idle(\\s|$)/.test(cmdbox.className||''),
      commands: rows('.ebb-cmd', cmdbox),
      submenu: subOpen ? rows('.ebb-item, .ebb-cmd, .ebb-prow, li', sub) : null,
      // A FOE IS A TRANSFORMED SILHOUETTE and its box does not always satisfy vis()'s
      // size test, so ask only whether it is DISPLAYED — a monster you are fighting
      // and cannot see the name of is the one thing you must not drop from a percept.
      foes: [...br.querySelectorAll('.ebb-foe')]
        .filter(f => { const s=getComputedStyle(f);
          return s.display!=='none' && s.visibility!=='hidden' && parseFloat(s.opacity||'1')>0.06; })
        .map(f => ({ name: txt(f.querySelector('.ebb-ftag')), targeted: cur(f) || !!f.querySelector('.ebb-mark.cur') }))
        .filter(f => f.name),
      // textContent runs the spans together ("VesperLV 134/34"). Read the parts.
      party: [...br.querySelectorAll('.ebb-party .ebb-prow')].filter(vis).map(r => ({
        text: [txt(r.querySelector('.ebb-pname b')), txt(r.querySelector('.ebb-pname small')),
               (txt(r.querySelector('.hp'))||'?') + '/' + (txt(r.querySelector('.mx'))||'?') + ' HP']
              .filter(Boolean).join(' '), selected: cur(r) })),
    };
    // The doorway banner is still in the DOM underneath a full-screen battle, and a
    // player cannot see it. Reporting it would be reporting something not drawn.
    out.prompts = [];
  }
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

/* ================== IS THERE A FRAME THE PLAYER WOULD SEE? ==================
 * PT-20260803-005/006 (2026-08-03). The agent left Emberbrook, saw four black
 * frames in a row, and filed a P1 blocker: "Screen remains black after leaving
 * Emberbrook". THE GAME WAS FINE. What it photographed was play3d's own fade veil
 * while a 45 MB real-time bundle loaded — settle() waited its flat 10 s, timed out,
 * and observe() captured anyway. The run log even said so three times ("held a
 * modal lock for 10 s with nothing on screen") and the frame went to the model
 * regardless, labelled as what the player sees.
 *
 * AN INSTRUMENT THAT CANNOT SEE MUST SAY SO RATHER THAN EMIT A BLACK FRAME.
 * So readiness is now a question whose true answer implies a PAINTED frame, and it
 * is asked two ways that fail for different reasons:
 *
 *   IN THE PAGE  the transition is not in flight, the bundle has meshes, a
 *                pre-rendered scene has chosen its shot, NO full-screen black veil
 *                is over the picture (play3d's sgVeil is an anonymous fixed div at
 *                z-index 9 — found here by what it DOES, since it has no id), and
 *                the game is not holding a modal lock with nothing drawn on it.
 *   ON THE FRAME the mean luminance of the captured picture. This is the backstop:
 *                it does not care WHY nothing is on screen, and it would have caught
 *                this bug on its own. Measured on this build: the veil reads 0.4,
 *                emb-cine 32.9, ow-valley 113-121.
 *
 * The old predicate's conjuncts were all TRUE the whole time — SIM.gpu().meshes is
 * renderer bookkeeping (47 in ow-valley), SIM.cam is a function, and SGbusy went
 * false as soon as the swap finished. None of them is a statement about pixels.
 */
const BLACK_L = 2.0;              // mean luminance below this = nothing is drawn
const FRAME_BUDGET_MS = 45000;    // a cold 45 MB real-time bundle is a legitimate wait

/* ================= THE HARNESS OWNS ITS OWN CLOCK =========================
 * `Runtime.evaluate` accepts a `timeout`, and IT IS NOT A TIMEOUT THE HARNESS MAY
 * RELY ON. Measured on this build, against a live playtester page whose main thread
 * was busy: an evaluate sent with `timeout: 3000` had still not answered TWENTY
 * SECONDS later, and neither had one sent with no timeout at all — while
 * `Performance.getMetrics` on the same socket answered instantly. The reason is
 * mechanical: that parameter is implemented by asking V8 to terminate a script it
 * is RUNNING, and a request that the main thread never dequeues has no script to
 * terminate. So the parameter is a cap on execution, never on the wait.
 *
 * Every round-trip therefore carries a deadline the harness enforces itself, with
 * Promise.race, and an overrun raises PageSilent — a DISTINCT OUTCOME, never a
 * measurement. That distinction is the whole point: `no answer` and `the body did
 * not move` are the same bytes on the wire and opposite facts about the game.
 *
 * The old default was 120 000 ms and most of the walk loop passed nothing at all,
 * so a single blocking evaluate could sail past a 54 s hard ceiling that was only
 * ever checked BETWEEN calls. That is how one burst came to be reported at 210 s.
 */
const EV_MS = 12000;              // default deadline for one page round-trip
const KEY_MS = 4000;              // one Input.dispatchKeyEvent ack
const BOOT_MS = 240000;           // a cold boot may be slow; it may not be endless
class PageSilent extends Error {
  constructor(ms, expr) {
    super(`the page did not answer in ${ms} ms (${String(expr).replace(/\s+/g, ' ').slice(0, 60)})`);
    this.pageSilent = true; this.waitedMs = ms;
  }
}
/* A deadline the caller can hand to every await in a loop, so the ceiling is
 * enforced DURING the calls instead of discovered after one of them returns. */
function deadline(ms) { const at = Date.now() + ms; return () => Math.max(250, at - Date.now()); }

const FRAME_GATE_JS = `(()=>{ const why=[];
  const S=window.SIM;
  if(!S||!S.scene) return {why:['the page has no SIM yet — it is still booting']};
  try{ if(S.transitions().busy) why.push('a scene transition is still in flight'); }
  catch(e){ why.push('SIM.transitions() threw: '+e.message); }
  try{ if(!(S.gpu().meshes>0)) why.push('the loaded bundle has no meshes'); }
  catch(e){ why.push('SIM.gpu() threw: '+e.message); }
  try{ const c=S.cine&&S.cine(); if(c && !c.shot) why.push('a pre-rendered scene with no shot chosen'); }catch(e){}
  try{ for(const el of document.body.children){ const s=getComputedStyle(el);
      if(s.position!=='fixed') continue;
      const op=parseFloat(s.opacity||'1'); if(!(op>0.5)) continue;
      const r=el.getBoundingClientRect();
      if(r.width<innerWidth*0.9||r.height<innerHeight*0.9) continue;
      // THE ALPHA CHANNEL IS PART OF THE COLOUR. Matching only rgb() called
      // play3d's own #exit-markers layer — fixed, full-screen, background
      // rgba(0,0,0,0) — a black veil, and reported an unreadable screen over a
      // frame measuring 121 luminance. A transparent black is not black.
      const m=String(s.backgroundColor||'').match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
      if(!m || +m[1]>24 || +m[2]>24 || +m[3]>24) continue;
      const al=m[4]===undefined?1:parseFloat(m[4]);
      if(!(op*al>0.5)) continue;
      why.push('a full-screen black veil is over the picture (opacity '+(op*al).toFixed(2)+
               ') — play3d fades to black across a transition');
      break; } }catch(e){}
  /* FROZEN IS NOT BLIND, AND CONFLATING THEM COST A RUN. A modal lock with nothing
   * drawn is a statement about the GAME (it took control and showed nothing); a
   * black frame is a statement about the INSTRUMENT. Reported separately so the
   * runner can wait out the first and refuse to photograph the second. */
  let frozen=null;
  try{ const p=${PERCEPT_JS};
    if(!!(window.UILOCK&&UILOCK.active()) && !(p.dialogue||p.card||p.battle))
      frozen='the game holds a modal lock with nothing drawn on it'; }catch(e){}
  return {why, frozen}; })()`;

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
const PROFILE_PREFIX = 'llm-playtester-profile-';

/* REAP OUR OWN ORPHANS, AND ONLY OUR OWN.
 *
 * This tool will run more browser sessions than anything else in the repo, so a
 * leak of one Chrome per episode is the dominant memory cost on the machine at any
 * useful N. It is not hypothetical: another tool leaked six root Chromes tonight
 * and they sat on 7.6 GB of swap with 675 MB free, and every browser gate on the
 * box went slow for half an hour.
 *
 * cdp.mjs's sweepStaleProfiles has a two-hour age floor — deliberately, so a
 * concurrent sibling is never destroyed mid-run — which means a three-minute-old
 * orphan survives it. But our profile directory carries the pid of the node that
 * launched it, so we can do better than an age heuristic: ASK WHETHER THAT PROCESS
 * IS STILL ALIVE. kill(pid, 0) is the question; ESRCH is the answer.
 *
 * NEVER PATTERN-KILL CHROME BY NAME. Most of the Chrome processes on this machine
 * belong to the person using it. The only matcher used here is our own
 * --user-data-dir prefix, via cdp.mjs's killOrphans, and only after the owning pid
 * is confirmed dead.
 */
function reapDeadProfiles() {
  const tmp = process.env.TMPDIR || '/tmp';
  let n = 0;
  try {
    for (const name of readdirSync(tmp)) {
      if (!name.startsWith(PROFILE_PREFIX)) continue;
      const pid = parseInt(name.slice(PROFILE_PREFIX.length), 10);
      if (!pid || pid === process.pid) continue;
      try { process.kill(pid, 0); continue; }            // still alive: not ours to touch
      catch (e) { if (e.code !== 'ESRCH') continue; }    // EPERM etc: assume alive, leave it
      const full = join(tmp, name);
      killOrphans(full);                                  // matches --user-data-dir=<full>
      try { rmSync(full, { recursive: true, force: true, maxRetries: 2 }); } catch (e) { }
      n++;
    }
  } catch (e) { }
  return n;
}

// --------------------------------------------------------------------------
export function checkpointsFromStory() {
  const STORY = JSON.parse(readFileSync(join(ROOT, 'public/game/story.json'), 'utf8'));
  let BRIEFS = {};
  const bp = join(ROOT, 'docs/qa/playtest/briefs.json');
  if (existsSync(bp)) { try { BRIEFS = JSON.parse(readFileSync(bp, 'utf8')).briefs || {}; } catch (e) { } }
  const out = []; const flags = {}; const beats = {};
  // SEEDED FROM story.json's `start`, not from nothing. The chapter's first beats
  // declare no `at` — they fire anywhere in emb-cine — so before this seed a
  // `--from=ch1.open` drop-in carried pos:null and fell through to the SHOT'S BAKED
  // SPAWN, which is the arrival clearing's exit pad: the exact standing position
  // PT-20260803-002 is about. A checkpoint that reproduces the bug it was meant to
  // start after is worse than no checkpoint.
  const ST = STORY.start || {};
  let objective = null, lastAt = ST.pos || null, lastScene = ST.scene || null, lastCam = ST.cam || null;
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
  if (p.battle) {
    const b = p.battle;
    const list = (rs) => rs.map((r, i) => `[${i}]${r.selected ? ' >' : ''} ${r.text}`).join('   ');
    L.push(`A BATTLE IS UNDER WAY${b.zone ? ` — ${[b.zone, b.round].filter(Boolean).join(', ')}` : ''}` +
      (b.foes.length ? `. You are fighting: ${b.foes.map(f => f.name + (f.targeted ? ' (targeted)' : '')).join(', ')}` : ''));
    if (b.actor || b.log) L.push('  ' + [b.actor, b.log].filter(Boolean).join(': '));
    if (b.commands && b.commands.length)
      L.push(`  ${b.yourTurn ? 'IT IS YOUR TURN. Commands' : 'Commands (someone else is acting)'}: ` + list(b.commands));
    if (b.submenu && b.submenu.length) L.push('  THE OPEN SUB-MENU: ' + list(b.submenu));
    if (b.party && b.party.length) L.push('  your party: ' + b.party.map(r => r.text).join(' | '));
    L.push('  "> " marks where the cursor is. Use choose to pick a numbered entry; ' +
      'use advance or wait to let the other side act.');
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
  /* EVERY round-trip through this adapter goes through one raced primitive. See the
   * PageSilent note above for why CDP's own `timeout` cannot be trusted to do it. */
  async function raced(method, params, ms, label) {
    let timer = null;
    const r = await Promise.race([
      cdp.send(method, params).then(v => ({ v })),
      new Promise(res => { timer = setTimeout(() => res({ silent: true }), ms); }),
    ]);
    if (timer) clearTimeout(timer);
    if (r.silent) throw new PageSilent(ms, label || method);
    return r.v;
  }
  async function ev(expr, t) {
    const ms = t || EV_MS;
    const r = await raced('Runtime.evaluate',
      { expression: expr, awaitPromise: true, returnByValue: true, userGesture: true, timeout: ms }, ms, expr);
    if (r.exceptionDetails) throw new Error('page exception: ' + ((r.exceptionDetails.exception || {}).description || r.exceptionDetails.text));
    return r.result && r.result.value;
  }
  /* A read that a busy page is ALLOWED to refuse. Anything the run can carry on
   * without — a percept, a truth dump, a UILOCK poll — asks through this and gets
   * `fallback` when the page is silent, so a slow moment does not become a stack
   * trace three layers up. Anything the run cannot carry on without uses ev(). */
  async function evSoft(expr, t, fallback) {
    try { return await ev(expr, t); } catch (e) { if (e.pageSilent) return fallback; throw e; }
  }
  function keyEvent(type, k, ms) {
    const p = { type, key: k.key, code: k.code, windowsVirtualKeyCode: k.vk, nativeVirtualKeyCode: k.vk };
    if (type === 'keyDown' && k.key.length === 1) p.text = k.key;
    return raced('Input.dispatchKeyEvent', p, ms || KEY_MS, 'key ' + type + ' ' + k.key);
  }
  /* A KEY THAT WENT DOWN COMES BACK UP, EVEN WHEN THE PAGE STOPS ANSWERING.
   * `Input.dispatchKeyEvent` is acked by the renderer's main thread, so it starves
   * exactly like an evaluate — and a keyDown whose keyUp was skipped by a thrown
   * timeout leaves the body walking for the rest of the run. The release is in a
   * finally, best-effort, and the starvation is reported rather than swallowed. */
  async function hold(names, ms, budget) {
    const ks = names.map(n => KEYS[n]).filter(Boolean);
    const down = [];
    let silent = null;
    try {
      for (const k of ks) { await keyEvent('keyDown', k, budget); down.push(k); }
      await sleep(ms);
    } catch (e) { if (e.pageSilent) silent = e; else throw e; }
    finally { for (const k of down) { try { await keyEvent('keyUp', k, budget); } catch (e) { if (!e.pageSilent) throw e; } } }
    if (silent) throw silent;
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

  /* THE FRAME, MEASURED. A 64-px-wide PNG of the whole viewport: cheap enough to
   * take every quarter-second, and it answers the only question that matters here
   * without believing anything the page says about itself.
   * NOT gl.readPixels on the default framebuffer — after compositing the drawing
   * buffer is cleared unless preserveDrawingBuffer is set, so that probe reads black
   * for EVERY scene including ones that demonstrably render. play3d's own probes
   * render immediately before reading (play3d.html:1806); a harness must not, because
   * forcing a render is perturbing the thing it is measuring. A screenshot is not. */
  async function frameLum() {
    if (!PNG) return null;
    try {
      const w = 64, s = w / viewport[0];
      const r = await raced('Page.captureScreenshot', { format: 'png',
        clip: { x: 0, y: 0, width: viewport[0], height: viewport[1], scale: s } }, EV_MS, 'captureScreenshot');
      const img = PNG.sync.read(Buffer.from(r.data, 'base64'));
      const n = img.width * img.height; let sum = 0, nb = 0;
      for (let i = 0; i < n; i++) { const o = i * 4;
        const l = img.data[o] * 0.299 + img.data[o + 1] * 0.587 + img.data[o + 2] * 0.114;
        sum += l; if (l > 10) nb++; }
      return { meanL: +(sum / n).toFixed(2), nonblackPct: +(100 * nb / n).toFixed(1) };
    } catch (e) { return { meanL: null, nonblackPct: null, error: e.message }; }
  }

  async function frameGate() {
    let g;
    try { g = await ev(FRAME_GATE_JS, 6000); }
    catch (e) {
      /* PAGE-SILENT IS A READINESS ANSWER, NOT A CRASH. The gate not answering means
       * the main thread is busy, which is precisely the condition in which nothing is
       * being painted and nothing may be measured. It reads as not-ready, in words,
       * and the run waits it out like any other unpainted frame. */
      return { why: [e.pageSilent
        ? `the page's main thread did not answer the readiness gate in ${e.waitedMs} ms — it is busy (a bundle load, a parse, or the machine)`
        : 'the readiness gate could not run in the page: ' + e.message], lum: null, silent: !!e.pageSilent };
    }
    const why = (g && g.why) ? g.why.slice() : ['the readiness gate returned nothing'];
    const lum = await frameLum();
    if (lum && lum.meanL != null && lum.meanL < BLACK_L)
      why.push(`the picture is black (mean luminance ${lum.meanL}, only ${lum.nonblackPct}% of pixels above black)`);
    return { why, lum, frozen: (g && g.frozen) || null };
  }

  /* Wait PROPERLY, then be honest. The old settle() capped at a flat 10 s, which is
   * shorter than a cold real-time bundle load — and then let the capture happen
   * anyway, so its own timeout reached the agent as a fact about the game.
   * TWO CLOCKS, because the two conditions mean different things: an unpainted frame
   * gets the long budget (a bundle load is legitimately slow), while an empty modal
   * gets a short one and is then HANDED BACK as a fact about the game rather than
   * waited on forever. */
  async function waitForFrame(budgetMs, frozenMs = 8000) {
    const t0 = Date.now();
    for (;;) {
      const g = await frameGate();
      const el = Date.now() - t0;
      if (!g.why.length && (!g.frozen || el >= frozenMs)) return { ...g, ready: true, waitedMs: el };
      if (el >= budgetMs) return { ...g, ready: !g.why.length, waitedMs: el };
      await sleep(250);
    }
  }

  return {
    PERSONA, flattenPercept,
    checkpoints() { return checkpointsFromStory(); },
    url: urlFor,

    async open(startUrl) {
      const cdpPort = await freePort();
      profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);
      const reaped = reapDeadProfiles();
      if (reaped) console.log(`  reaped ${reaped} orphaned playtester Chrome profile(s) whose owner was gone`);
      sweepStaleProfiles(PROFILE_PREFIX);
      killOrphans(profile);
      rmSync(profile, { recursive: true, force: true });
      /* TEARDOWN ON EVERY PATH, and the abnormal ones are the ones that leak: a
       * crash, a timeout, a Ctrl-C, an outer harness pkill. `exit` covers the
       * normal and thrown cases; the signals cover the rest. All idempotent. */
      process.on('exit', () => { try { chrome && chrome.kill('SIGKILL'); } catch (e) { }
        try { profile && rmSync(profile, { recursive: true, force: true }); } catch (e) { } });
      for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => {
        try { chrome && chrome.kill('SIGKILL'); } catch (e) { }
        try { profile && rmSync(profile, { recursive: true, force: true }); } catch (e) { }
        process.exit(130);
      });
      process.on('uncaughtException', (e) => {
        console.error('UNCAUGHT: ' + (e && e.message));
        try { chrome && chrome.kill('SIGKILL'); } catch (x) { }
        try { profile && rmSync(profile, { recursive: true, force: true }); } catch (x) { }
        process.exit(4);
      });
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
      // A COLD BOOT MAY BE SLOW; IT MAY NOT BE ENDLESS. READY_JS is an in-page poll,
      // so its own 60 s cap only starts once the main thread dequeues it — which on
      // a thrashing machine has been measured at eleven minutes. The harness's clock
      // is the one that decides, and it says so out loud rather than hanging.
      const boot = await evSoft(READY_JS, BOOT_MS, '__silent__');
      if (boot === '__silent__') { console.error(`  the page's main thread never answered in ${BOOT_MS} ms`); return false; }
      return boot;
    },

    /* ------------------------------------------------------------------ SETUP
     * THE ONLY PLACE THE SAVE SYSTEM AND THE RESUME URL MAY BE TOUCHED.
     * plan = {kind:'newgame'} | {kind:'checkpoint', scene, cam, pos, patch}
     *      | {kind:'repro', scene, cam, pos, save}
     */
    async setup(plan) {
      if (plan.kind === 'newgame') {
        await ev(`(()=>{try{localStorage.removeItem('emberbrook-save');localStorage.removeItem('emberbrook-save-v1');}catch(e){}return 1})()`);
        // plan.pos comes from story.json's `start` — a new game boots where the front
        // door sends the player, not on whatever fallback spawn the shot happens to bake.
        await send('Page.navigate', { url: urlFor(plan.scene, plan.cam, plan.pos) });
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
      const ok = await evSoft(READY_JS, BOOT_MS, false);
      if (ok === false) console.error(`  the page did not become playable within ${BOOT_MS} ms`);
      // HIDE THE DEV HUD. play3d draws `#h` with the live scene, shot and pos(x,y,z)
      // in the top-left corner (play3d.html:1702). A shipping build would not, and a
      // screenshot containing it hands the agent the exact numbers this instrument
      // exists to withhold. This is the ONLY change the harness makes to the page,
      // and it REMOVES information.
      await ev(`(()=>{const s=document.createElement('style');s.textContent='#h{display:none!important}';document.head.appendChild(s);return 1})()`);
      await ev(INSTALL_MOTOR);
      await sleep(500);
      // BOOT IS HELD TO THE SAME BAR AS EVERY STEP. "The page became playable" used
      // to mean SIM answered its own questions; it now also means something is drawn.
      const f = await waitForFrame(FRAME_BUDGET_MS);
      if (!f.ready) { console.error('  the page never painted a frame: ' + f.why.join('; ')); return false; }
      return ok;
    },

    /* A veil, a fade, or a modal with nothing drawn on it is not a decision — it is
     * a wait, and paying a model call to watch a transition is paying for nothing.
     * Returns TRUE only when a painted frame is up; see FRAME_GATE_JS for why the
     * old version of this could return false while the game was perfectly fine. */
    async settle(maxMs = FRAME_BUDGET_MS) { return (await waitForFrame(maxMs)).ready; },

    /* observe() EITHER HANDS BACK A FRAME THE PLAYER WOULD SEE, OR SAYS IT COULD
     * NOT GET ONE. It never does both silently. `ready:false` carries `why` (the
     * gate's own reasons, in plain language) and `meanL`, the frame is written with
     * an -UNREADY suffix so the evidence survives the retention sweep, and layer 3
     * is responsible for not paying a model to look at it. */
    async observe(tag, opt) {
      const budget = (opt && opt.budgetMs != null) ? opt.budgetMs : FRAME_BUDGET_MS;
      const g = await waitForFrame(budget);
      // A percept the busy page refused is EMPTY, never stale and never a hang. The
      // frame gate above has already said `ready:false`, so layer 3 will not pay a
      // model to read it.
      const percept = await evSoft(PERCEPT_JS, EV_MS, EMPTY_PERCEPT) || EMPTY_PERCEPT;
      const r = await raced('Page.captureScreenshot', { format: 'jpeg', quality: 72 }, EV_MS, 'captureScreenshot');
      let framePath = null;
      if (framesDir) {
        mkdirSync(framesDir, { recursive: true });
        framePath = join(framesDir, 'step-' + String(++frameN).padStart(3, '0') +
          (tag ? '-' + tag : '') + (g.ready ? '' : '-UNREADY') + '.jpg');
        writeFileSync(framePath, Buffer.from(r.data, 'base64'));
      }
      return { screenshot: { mime: 'image/jpeg', data: r.data }, text: flattenPercept(percept), percept, framePath,
        ready: g.ready, why: g.why, frozen: g.frozen, meanL: g.lum ? g.lum.meanL : null, waitedMs: g.waitedMs };
    },

    async truth() { return await evSoft(TRUTH_JS, EV_MS, {}); },

    /* ONE WALK LEG. Real keys, closed loop, and it reports the geometry —
     * intended vs closed — which is the free bug signal. */
    async walkLeg(nx, ny, budgetMs) {
      /* A LEG MAY NOT BEGIN WHILE THE PAGE IS NOT PAINTING. Walking is measured by
       * asking the body where it is before and after real key events; a page whose
       * main thread is loading a bundle answers neither, and phys() is not running to
       * move anybody anyway. Every metre of "0 m closed of 20.87 m" ever filed by this
       * executor was measured across exactly that. The frame gate already knows how to
       * ask the question — readiness plus the measured luminance of a real screenshot
       * — so the leg asks it FIRST and refuses to start rather than mis-measuring.
       * `starved`, never `exhausted`: what the world would have done is unknown. */
      const pre = await waitForFrame(FRAME_BUDGET_MS);
      if (!pre.ready)
        return { ok: false, nx, ny, reason: 'unready', starved: true, exhausted: false,
          detail: 'the walk never started: ' + pre.why.join('; '), starvedWhy: pre.why,
          intended: 0, closed: 0, bursts: 0, msPerBurst: null, waitedMs: pre.waitedMs };
      try { await ev(INSTALL_MOTOR); }
      catch (e) { if (!e.pageSilent) throw e;
        return { ok: false, nx, ny, reason: 'unready', starved: true, exhausted: false,
          detail: 'the page stopped answering before the walk started', starvedWhy: [e.message],
          intended: 0, closed: 0, bursts: 0, msPerBurst: null }; }
      // A LEG THAT NEVER GOT TO RUN IS NOT A BLOCKED PATH. If a beat fired or a
      // conversation opened between the screenshot and the first key, phys() is
      // frozen under UILOCK and the body cannot move — recording that as "closed
      // 0 m of 15 m" would manufacture a blocker out of a cutscene. Measured on the
      // first bring-up run: the waystone beat fired mid-route and produced exactly
      // that false leg.
      if (await ev(`(()=>{try{return !!(window.UILOCK&&UILOCK.active())}catch(e){return false}})()`))
        return { ok: false, nx, ny, reason: 'modal', detail: 'the game took control before the walk started', intended: 0, closed: 0 };
      // The pixel-to-world march is 640 BVH queries on the page's own main thread —
      // the one expensive read in this loop, and it gets a budget of its own.
      const h = await ev(`window.__pt.hit(${nx},${ny})`, 30000);
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
      /* "BLOCKED" MEANS THE HEADINGS WERE TRIED AND REFUSED — NOT THAT THE CLOCK RAN OUT.
       *
       * The budget below is WALL CLOCK, but almost none of it is spent walking: it is
       * spent on CDP round-trips. On a loaded machine one 150 ms burst plus its two
       * position reads measured 7-66 SECONDS (run-20260803-122026, `ms` 14810-132928 for
       * legs of one and two bursts), against ~500 ms on an idle one. So the old inner
       * `if (elapsed > budget) break` fired after the FIRST heading, the slide never ran,
       * and `moved < 0.10` was then read as "every heading refused: blocked". Three P1
       * blockers (PT-20260803-010/011/012) were filed that way against ground the engine
       * says is open in all 24 directions and that a real 150 ms burst crosses at 0.9 m.
       * Their own payload recorded `bursts: 1`. ONE HEADING IS NOT EVERY HEADING.
       *
       * So a round of headings is never cut short by the ordinary budget. Only a hard
       * ceiling stops it, and when that ceiling is what stopped it the leg says STARVED
       * and is not allowed to be a blocker. Same rule as the frame gate: an instrument
       * that could not look must say so rather than report what it did not see. */
      const BUDGET = budgetMs || 9000;
      const HARD = BUDGET * 6;                  // a full round of 5 headings, however slow the link
      /* THE CEILING IS NOW ENFORCED DURING THE CALLS, NOT BETWEEN THEM. It used to be
       * a `Date.now()` test sitting AFTER an await with no deadline of its own, so one
       * blocking round-trip sailed straight past 54 s and the leg only noticed
       * afterwards — which is how a single burst came to be reported at 210 402 ms.
       * `left()` is what remains of the ceiling, and every await in the loop is capped
       * by it, so the worst case is one call's own budget past HARD instead of forever. */
      const left = deadline(HARD);
      const cap = (n) => Math.min(n, left());
      let exhausted = false, starved = false, rounds = 0, starvedWhy = null;
      try {
        while (Date.now() - t0 < BUDGET) {
          if (left() <= 250) { starved = true; break; }
          const st = await ev(`window.__pt.dirTo(${JSON.stringify(h.p)})`, cap(EV_MS));
          if (st.dist <= ARRIVE_M) break;
          let moved = 0, now = last, tried = 0;
          for (const off of OFFSETS) {
            await hold(OCT_KEYS[(((st.oct + off) % 8) + 8) % 8], BURST_MS, cap(KEY_MS)); bursts++; tried++;
            now = await ev(`window.__pt.where()`, cap(EV_MS));
            moved = Math.hypot(now[0] - last[0], now[2] - last[2]);
            if (moved >= 0.10) { if (off !== 0) slides++; break; }
            if (Date.now() - t0 > HARD) { starved = true; break; }
          }
          rounds++;
          last = now;
          const d = Math.hypot(h.p[0] - now[0], h.p[2] - now[2]);
          if (d < best - 0.15) { best = d; sinceGain = 0; } else sinceGain++;
          // Every heading refused — but only say so if every heading was actually TRIED.
          if (moved < 0.10) { exhausted = (tried === OFFSETS.length && !starved); break; }
          if (sinceGain >= 8) break;                // moving, but not getting closer
          // A camera cut, a doorway or a story beat changes the world under the leg.
          if (await ev(`(()=>{try{return !!(window.UILOCK&&UILOCK.active())}catch(e){return false}})()`, cap(EV_MS))) break;
        }
      } catch (e) {
        /* THE PAGE STOPPED ANSWERING MID-LEG. Not a blocked path, not a refusal — an
         * absence of evidence, and the one outcome that must never become `exhausted`.
         * Ask the frame gate WHY while the condition is still live, because "starved"
         * with a reason is a finding about the machine and "starved" without one is a
         * shrug the next reader has to re-investigate. */
        if (!e.pageSilent) throw e;
        starved = true; exhausted = false;
        const g = await frameGate().catch(() => ({ why: [] }));
        starvedWhy = [e.message, ...(g.why || [])];
      }
      const end = await evSoft(`window.__pt.where()`, EV_MS, last);
      const stoppedByModal = await evSoft(`(()=>{try{return !!(window.UILOCK&&UILOCK.active())}catch(e){return false}})()`, EV_MS, false);
      const dEnd = Math.hypot(h.p[0] - end[0], h.p[2] - end[2]);
      if (stoppedByModal)
        return { ok: false, nx, ny, reason: 'modal', detail: 'the game took control part-way through the walk',
          target: h.p, from, end, intended: +d0.toFixed(2), closed: +(d0 - dEnd).toFixed(2) };
      return { ok: true, nx, ny, onNetwork: h.onNetwork, target: h.p, from, end,
        intended: +d0.toFixed(2), remaining: +dEnd.toFixed(2), closed: +(d0 - dEnd).toFixed(2),
        travelled: +Math.hypot(end[0] - from[0], end[2] - from[2]).toFixed(2),
        closedFrac: d0 > 0.5 ? +((d0 - dEnd) / d0).toFixed(2) : 1,
        bursts, slides, rounds, arrived: dEnd <= ARRIVE_M, ms: Date.now() - t0,
        // THE TWO WORDS THAT MAY NOT BE CONFUSED, and the per-burst cost that decides
        // which one it is. `exhausted`: all five headings pushed, the body did not move
        // — the world refused, and this is the finding worth filing. `starved`: the
        // round was cut off by the hard ceiling, so what the world would have done is
        // UNKNOWN and no blocker may be built on it.
        exhausted, starved, starvedWhy,
        msPerBurst: bursts ? Math.round((Date.now() - t0) / bursts) : null };
    },

    /* Read a whole conversation with real presses and hand back the transcript. A
     * player sees every line at once; paying one model call per line is paying to
     * read. A CHOICE IS THE PLAYER'S — the loop stops the moment one appears. */
    async readThrough(max = 40) {
      const seen = [];
      for (let n = 0; n < max; n++) {
        // A page that stops answering ends the read; the transcript so far is real
        // and a half-read conversation is not a reason to abort the run.
        const p = await evSoft(PERCEPT_JS, EV_MS, null);
        if (!p) break;
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
        try { await tap('e'); } catch (e) { if (e.pageSilent) break; throw e; }
        await sleep(320);
      }
      return seen;
    },

    async press(name) { await tap(name); await sleep(700); },
    async menuDown(n) { for (let i = 0; i < n; i++) { await tap('down'); await sleep(120); } },

    /* PICK ENTRY N OF THE LIST THAT IS OPEN. The agent is shown numbered entries and
     * where the cursor is; it does not count keypresses. menuDown(index) only landed
     * on the right row when the cursor happened to start at the top — true for a
     * fresh dialogue choice, false for a battle command menu that remembers where it
     * was. So MEASURE the cursor and move relative to it. */
    async choose(index) {
      const at = await evSoft(`(()=>{ const sel=(l)=>{ let i=-1;
          [...l].forEach((e,k)=>{ if(/(^|\\s)(cur|sel|selected|active)(\\s|$)/.test(e.className||'')) i=k; }); return i; };
        const br=document.querySelector('.ebb-root');
        if(br){ const sub=br.querySelector('.ebb-sub');
          const open = sub && getComputedStyle(sub).display!=='none' && sub.getBoundingClientRect().height>2;
          return sel(open ? sub.querySelectorAll('.ebb-item,.ebb-cmd,.ebb-prow,li')
                          : br.querySelectorAll('.ebb-cmds .ebb-cmd')); }
        const v=[...document.querySelectorAll('.ebui-veil')].pop();
        if(v) return sel(v.querySelectorAll('.ebui-row,.ebui-choice,li,.row,.choice'));
        return -1; })()`, EV_MS, -1);
      const d = index - (at >= 0 ? at : 0);
      for (let i = 0; i < Math.abs(d); i++) { await tap(d > 0 ? 'down' : 'up'); await sleep(130); }
      await tap('e'); await sleep(700);
      return { from: at, to: index };
    },

    async close() {
      if (closed) return; closed = true;
      try { chrome && chrome.kill('SIGKILL'); } catch (e) { }
      // The spawned process is the ROOT Chrome; its renderers and GPU process are
      // children and normally follow it down. killOrphans is the belt to that
      // brace, matching on OUR profile path and nothing else — never on the name
      // "Chrome", most of which on this machine belongs to the person using it.
      try { profile && killOrphans(profile); } catch (e) { }
      try { profile && rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) { }
    },
    _ev: ev, _hold: hold, _frameGate: frameGate,
  };
}
