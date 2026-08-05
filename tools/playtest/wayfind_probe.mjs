/* wayfind_probe — WHICH OF THESE RED TRIANGLES GOES TO THE OBJECTIVE?
 *
 * Round 11's instrument. Three independent playtest runs failed at the SAME place
 * (Lock Five's head-gate winches, `del-cine`), every filing reach-REFUTED: the walk
 * network is clean twice over, so what is broken is READING the way, not walking it.
 *
 * marker_probe answers the same question for the OVERWORLD (window._rtCam, one follow
 * camera). It cannot be pointed at a pre-rendered town: there the camera is CINECAM's
 * fixed shot, the scene carries FIFTEEN of them, and the edges that join them are
 * anonymous `cut` bands. So this probe is that one, re-aimed:
 *
 *   - stands the body where the failing runs stood (their own `truth.pos`),
 *   - forces the shot they were in,
 *   - reads the marker layer's OWN DOM (#exit-markers) and each marker's DRAWN pixel,
 *   - asks SIM.pick AT THAT PIXEL what the player's click would actually hit,
 *   - projects each edge's own `at` through the SHOT camera for the honest position,
 *   - and BFS's the scenegraph for the true next hop toward the objective's shot,
 * then writes the frame.
 *
 *   node tools/playtest/wayfind_probe.mjs [--port 3000] [--out <dir>]
 *      [--scene del-cine] [--target lockfive]
 *      [--stations '[["name",[x,y,z],"shot"]]']
 *
 * The lift is the thing under test: markersTick projects `at[1] + 2.1` and then lifts
 * 30 px more, so on a steep down-shot the arrow can draw on the cliff BEHIND the seam
 * it names. `liftNdcY` below is that error, measured per marker, in frame heights.
 */
import { freePort, findPage, killOrphans } from '../cdp.mjs';
import { checkpointsFromStory } from './adapter_emberbrook.mjs';
import { spawn } from 'child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import WebSocket from 'ws';

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const SC = arg('scene', 'del-cine');
const TARGET = arg('target', 'lockfive');
/* --liftcap <px>: MEASURE THE PROPOSED FIX WITHOUT MAKING IT. markersTick lifts the
 * arrow at[1]+2.1 m and then 30 px more; measured here that is 86-164 px, and half the
 * markers land a click on scenery. A CAP on the SCREEN distance between the seam's own
 * projection and the arrow keeps the "floats over the door, points down at it" grammar
 * while keeping the arrow on the ground it names. This reports where each arrow WOULD
 * draw under the cap and what SIM.pick returns there, so the change can be argued with
 * numbers before anyone edits the coordinator-owned page. 0 = do not measure it.
 *
 * IT TAKES A LIST (2026-08-05, round 19). `--liftcap 30,45,60,80` measures SEVERAL caps
 * in one boot. One value per Chrome boot made the question "at what cap does this arrow
 * stop landing on the cliff" cost a run each — and the answer is a THRESHOLD, so a
 * single sample can only ever say yes or no about a number somebody guessed. */
const LIFTCAPS = String(arg('liftcap', '0')).split(',').map(s => parseFloat(s)).filter(v => v > 0);
const LIFTCAP = LIFTCAPS.length ? LIFTCAPS[0] : 0;
/* --from <beatId>: WHICH GAME AM I MEASURING. (2026-08-05, PT-20260805-010.)
 *
 * The seed below used to be two hand-written arrays covering exactly one checkpoint,
 * `ch2.dock`. Pointed at any other stall it measured A DIFFERENT GAME THAN THE RUN:
 * with Chapter One's flags absent `pendingBeat()` resolved to a Chapter Two beat, so
 * the station printed `objective: "Midnight, at Lock Five..."` and `shown=false` over
 * a Chapter One stall — and round 15 had to file PT-010 UNDIAGNOSED because of it.
 *
 * So the seed comes from the SAME derivation the playtest runs check point from:
 * adapter_emberbrook's `checkpointsFromStory()`, which replays every beat's own
 * `setFlags` and `objective` out of story.json in file order. One source of truth,
 * no list to rot, and every beat in the chapter is now a station this probe can stand
 * at. `--from` names the beat that is PENDING — i.e. state is everything BEFORE it.
 * The default stays ch2.dock so round 14's numbers reproduce. */
const FROM = arg('from', 'ch2.winches');
const OUT = arg('out', 'docs/qa/playtest/wayfind');
mkdirSync(OUT, { recursive: true });
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const profile = mkdtempSync(join(tmpdir(), 'wayfind-'));
const cdpPort = await freePort();
const child = spawn(CHROME, [
  `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--autoplay-policy=no-user-gesture-required',
  '--window-size=1280,800', '--headless=new', 'about:blank',
], { stdio: 'ignore' });
let done = false;
const reap = () => { if (done) return; done = true; try { child.kill('SIGKILL'); } catch (e) {} killOrphans(profile); };
process.on('exit', reap);
for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => { reap(); process.exit(1); });
setTimeout(() => { console.error('SELF-EXPIRY at 420 s'); reap(); process.exit(2); }, 420000);

const wsUrl = await findPage(cdpPort, { tries: 240, label: 'wayfind_probe', match: /^about:blank/ });
const ws = new WebSocket(wsUrl, { perMessageDeflate: false, maxPayload: 64 * 1024 * 1024 });
await new Promise(r => ws.on('open', r));
let id = 0; const pend = new Map();
ws.on('message', m => { const o = JSON.parse(m); if (o.id && pend.has(o.id)) { pend.get(o.id)(o); pend.delete(o.id); } });
const send = (method, params = {}) => new Promise((res, rej) => {
  const i = ++id; pend.set(i, o => o.error ? rej(new Error(method + ': ' + o.error.message)) : res(o.result));
  ws.send(JSON.stringify({ id: i, method, params }));
});
const ev = async (e) => (await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true })).result.value;
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: `http://localhost:${PORT}/play3d.html?nomusic=1&scene=${SC}` });

for (let i = 0; i < 240; i++) {
  if (await ev(`(()=>{try{return !!(window.SIM&&SIM.gpu&&SIM.gpu().meshes>0&&SIM.pos)}catch(e){return false}})()`)) break;
  await new Promise(r => setTimeout(r, 1000));
}
/* CLEAR THE BOOT BEAT — AND KEEP CLEARING IT. The page boots with an EMPTY flag store,
 * so Chapter One's `ch1.open` fires on the first tick, and a dialogue box is UILOCK,
 * which HIDES #exit-markers. The first ch1 run of this probe read `shown=false` at all
 * four stations with the route correct at every one, and the frame showed the mapmaker's
 * opening line over an empty marker layer: A MARKER GATE THAT READS A LOCKED FRAME IS
 * MEASURING THE LOCK. One pass at boot is not enough either — the box opens on Story's
 * own tick, which lands AFTER the readiness check — so this is a helper, run before the
 * seed and again before every station read. */
const drain = async () => {
  for (let i = 0; i < 40; i++) {
    const open = await ev(`(()=>{try{return !!(window.Dialogue&&Dialogue.isOpen)}catch(e){return false}})()`);
    if (!open) return true;
    await ev(`(()=>{try{Dialogue.close()}catch(e){}return 1})()`);
    await new Promise(r => setTimeout(r, 250));
  }
  return false;
};
await new Promise(r => setTimeout(r, 2500));
await drain();

/* THE SEED, DERIVED. `--from <beat>` = the state in which that beat is PENDING: every
 * earlier beat's `setFlags` applied, every earlier beat in the ledger (`once` reads
 * GS.state.beats, so flags alone are the wrong game), and the objective string the last
 * beat before it posted. All three come out of story.json via the adapter, so the probe
 * and the runs it is auditing cannot drift apart. */
const CP = checkpointsFromStory().checkpoints.find(c => c.id === FROM);
if (!CP) { console.error('no checkpoint for --from ' + FROM); reap(); process.exit(2); }
console.log(`SEED --from=${FROM}: ${Object.keys(CP.flags).length} flags, ` +
  `${Object.keys(CP.beats).length} beats, objective ${JSON.stringify(CP.objective)}`);
await ev(`(()=>{GS.setFlags(${JSON.stringify(CP.flags)});
  const L=GS.state.beats||(GS.state.beats={});
  for(const b of ${JSON.stringify(Object.keys(CP.beats))})L[b]=1;return 1})()`);
if (CP.objective)
  await ev(`(()=>{try{Story&&Story.objective&&Story.objective(${JSON.stringify(CP.objective)})}catch(e){}return 1})()`);
/* AND THE PROOF THAT THE SEED TOOK. An instrument that finds nothing must prove it could
 * have found something (cdp.mjs's rule): if `pendingBeat` is not the beat named, every
 * hint below is about a different objective and the numbers are worthless. */
await new Promise(r => setTimeout(r, 1200));
await drain();
const PEND = await ev(`(()=>{try{return (Story.wayhint()||{}).beat||null}catch(e){return 'ERR '+e}})()`);
console.log('   pendingBeat = ' + JSON.stringify(PEND) + (PEND === FROM ? '  OK' : '   !! NOT THE BEAT ASKED FOR'));
await new Promise(r => setTimeout(r, 1500));

/* THE READING. Everything here comes out of the page's own bindings:
 *  - `cam` is play3d's live camera (CINECAM's, in a cine scene), so the projection IS
 *    markersTick's projection.
 *  - the marker rows are read out of #exit-markers, so the probe cannot drift from the
 *    thing it measures.
 *  - `pickAtMarker` is SIM.pick at the marker's own drawn centre: what a player aiming
 *    at that triangle actually points at.
 */
const READ_JS = (target, CAPV) => `(()=>{
  const CAPS=${JSON.stringify(LIFTCAPS)};
  const p=SIM.pos();
  // cam and SG are play3d top-level let bindings: global LEXICAL scope, NOT on window
  // (window.cam is undefined, which read as 'the edge has no position'). Bare, guarded.
  // NO BACKTICKS IN THIS COMMENT - it lives inside a template literal (CLAUDE.md).
  var C=null; try{C=cam}catch(e){}
  const cine=SIM.cine?SIM.cine():null;
  const shot=(cine&&(cine.shot||cine.cam))||null;
  const es=SIM.edges();
  const rows=[];
  const mk={};
  for(const d of document.querySelectorAll('#exit-markers > div')){
    const tf=d.style.transform||'';
    const m=/translate\\((-?[\\d.]+)px,\\s*(-?[\\d.]+)px\\)/.exec(tf);
    /* THE GLYPH'S OWN RECT, not the div's transform (2026-08-05, round 19). The
       transform is markersTick's INTENT; story_runtime clamps the routed arrow by
       writing the CSS translate property on the triangle, which the transform string
       does not carry. A probe that reads the intent cannot see the fix - and would
       have reported the arrow still on the cliff while the frame showed otherwise.
       Top-CENTRE of the triangle, which is the point the div transform also named. */
    let g=null;
    const tri=d.firstChild;
    if(tri&&tri.getBoundingClientRect){ const r=tri.getBoundingClientRect();
      if(r.width||r.height) g=[r.left+r.width/2, r.top]; }
    mk[d.dataset.edge]={shown:d.style.display!=='none', kind:d.dataset.kind,
      px:g||(m?[+m[1],+m[2]]:null), boxPx:m?[+m[1],+m[2]]:null, glyphPx:g};
  }
  for(const e of es){
    const m=mk[e.id]; if(!m) continue;
    let seam=null, arrow=null;
    if(e.at&&C){
      const v=new THREE.Vector3(e.at[0],e.at[1],e.at[2]).project(C);
      seam=[(v.x*.5+.5)*innerWidth,(-v.y*.5+.5)*innerHeight];
      const w=new THREE.Vector3(e.at[0],e.at[1]+2.1,e.at[2]).project(C);
      arrow=[(w.x*.5+.5)*innerWidth,(-w.y*.5+.5)*innerHeight-30];
    }
    let hit=null;
    if(m.shown&&m.px){ try{ const h=SIM.pick(m.px[0],m.px[1],3);
      hit=h.hits.map(q=>({name:q.name,pt:q.pt,d:q.d})); }catch(err){ hit=String(err); } }
    let caps=null;
    if(CAPS.length&&m.shown&&seam&&m.px){
      caps=[];
      for(const CAP of CAPS){
        const cx=[seam[0], seam[1]-Math.min(CAP, Math.max(0, seam[1]-m.px[1]))];
        let ch=null;
        try{ const h2=SIM.pick(cx[0],cx[1],3);
          ch=h2.hits.map(q=>({name:q.name,pt:q.pt,d:q.d})); }catch(err){ ch=String(err); }
        caps.push({cap:CAP,px:cx,pick:ch});
      } }
    const capPx=caps&&caps[0]?caps[0].px:null, capHit=caps&&caps[0]?caps[0].pick:null;
    rows.push({id:e.id,label:e.label,kind:e.kind,to:e.to,dist:e.dist,open:e.open,
      camTo:e.cam&&e.cam.key?e.cam.key:null,
      at:e.at, shown:!!m.shown, markerPx:m.px, boxPx:m.boxPx, glyphPx:m.glyphPx,
      seamPx:seam, arrowPx:arrow,
      liftPx: (m.px&&seam)?+(seam[1]-m.px[1]).toFixed(1):null,
      liftFrac:(m.px&&seam)?+((seam[1]-m.px[1])/innerHeight).toFixed(3):null,
      pick:hit, capPx:capPx, capPick:capHit, caps:caps});
  }
  return JSON.stringify({pos:[+p.x.toFixed(2),+p.y.toFixed(2),+p.z.toFixed(2)],
    scene:SIM.scene?SIM.scene():null, shot,
    canvas:[innerWidth,innerHeight],
    obj:(document.getElementById('story-obj')||{}).textContent||null,
    prompt:SIM.prompt?SIM.prompt():null,
    wayhint:(window.Story&&Story.wayhint)?Story.wayhint():null,
    target:${JSON.stringify(target)},
    markers:rows});
})()`;

/* THE TRUE NEXT HOP, over the scene's own self-edges (the graph the game reads), from
 * the shot the player is in to the shot the objective beat names. It is the answer the
 * marker layer does not carry: which ONE of these anonymous triangles is the way.
 *
 * IT RANKS BY METRES AND SHOWS ITS RUNNERS-UP (2026-08-05). This was a hop-count BFS,
 * which is exactly the bug it was pointed at: from the Lockhead, `cottage>cottage-steps`
 * and `quay-west>weave` are BOTH three hops, 21.9 m and 45.9 m, and a hop-count oracle
 * calls a route twice the length "correct". So it enumerates every simple path up to
 * MAXH hops (16 shots — exhaustive is cheap), measures each in metres along the seams'
 * own positions, and prints the best few. A TIE IN HOPS IS NOT A TIE ON THE GROUND, and
 * an oracle that cannot see the difference cannot audit the hint. The enumeration is
 * deliberately a DIFFERENT algorithm from story_runtime's Dijkstra: two implementations
 * agreeing on the number is the cross-check. */
const HOP_JS = (target, MAXH = 5) => `(()=>{
  var G=null; try{G=SG}catch(e){}; if(!G) return JSON.stringify({err:'no SG'});
  const sk=SIM.scene(), cine=SIM.cine?SIM.cine():null;
  const here=(cine&&(cine.shot||cine.cam))||null;
  const p=SIM.pos(), at0=[p.x,p.y,p.z];
  const self=G.edges.filter(e=>e.from===sk&&e.to===sk&&e.camFrom&&e.cam&&e.cam.key);
  const adj={}; for(const e of self){ (adj[e.camFrom]=adj[e.camFrom]||[]).push(e); }
  const P=e=>(e.spawn||e.at||null);
  const d=(a,b)=>(a&&b)?Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]):12;
  const found=[];
  (function walk(node, at, used, path, cost){
    if(path.length>${MAXH}) return;
    if(node===${JSON.stringify(target)}){ found.push({hops:path.length,m:cost,path:path.slice()}); return; }
    for(const e of (adj[node]||[])){ const n=e.cam.key; if(used[n]) continue;
      used[n]=1; path.push({edge:e.id,from:node,to:n});
      walk(n, P(e), used, path, cost+d(at, e.at||e.spawn));
      path.pop(); used[n]=0; }
  })(here, at0, {[here]:1}, [], 0);
  found.sort((a,b)=>a.m-b.m);
  if(!found.length) return JSON.stringify({here,path:null});
  const best=found[0];
  return JSON.stringify({here,hops:best.hops,m:best.m,path:best.path,
    alts:found.slice(1,3).map(f=>({hops:f.hops,m:f.m,first:f.path[0].edge}))});
})()`;

// The three failing filings' own positions + shots (queue.json truth blocks), plus the
// cottage door the objective starts at and the quay deck the run circled for 90 steps.
const STATIONS = arg('stations', null) ? JSON.parse(arg('stations')) : [
  ['A-cottage-door',   [92.61, 7.87, -22.0],  'cottage'],      // where ch2.dock leaves you
  ['B-lockhead',       [71.84, 14.07, -15.15],'lockhead'],     // one cut west
  ['C-quay-deck',      [48.20, 14.04, -12.0], 'quay-west'],    // 90 steps of circling
  ['D-loop-stairs',    [57.78, 15.30, -10.86],'loop-stairs'],  // PT-20260804-013 filed here
  ['E-loop-stairs-2',  [56.47, 17.40, -7.83], 'loop-stairs'],  // PT-20260804-004 filed here
  ['F-valley-gate',    [17.61, 24.07, -5.95], 'gate'],         // PT-20260804-011/012 filed here
  ['G-weave',          [59.09, 9.04, -22.0],  'weave'],        // the true corridor down
];

const rows = [];
for (const [name, pos, useShot] of STATIONS) {
  if (useShot) { await ev(`SIM.shot(${JSON.stringify(useShot)})`); await new Promise(r => setTimeout(r, 1800)); }
  await ev(`SIM.tp(${pos[0]},${pos[2]},${pos[1]})`);
  if (useShot) await ev(`SIM.shot(${JSON.stringify(useShot)})`);   // tp can cut us elsewhere
  await new Promise(r => setTimeout(r, 1200));
  await ev(`SIM.tick(3)`);
  await new Promise(r => setTimeout(r, 700));
  const clear = await drain();      // a locked frame draws no markers; see `drain`
  // AND RE-POST THE SEEDED OBJECTIVE. Draining the boot beat lets it FINISH, and a beat
  // that finishes posts its own objective over the seed — so the frame this probe writes
  // showed "Follow the road north" while it was measuring the hint for a beat five ahead.
  // The banner in the picture must be the banner the run had, or the picture is evidence
  // for a different game.
  if (CP.objective)
    await ev(`(()=>{try{Story.objective(${JSON.stringify(CP.objective)})}catch(e){}return 1})()`);
  let r, hop;
  try { r = JSON.parse(await ev(READ_JS(TARGET, LIFTCAP))); } catch (e) { r = { error: String(e) }; }
  try { hop = JSON.parse(await ev(HOP_JS(TARGET))); } catch (e) { hop = { error: String(e) }; }
  r.station = name; r.want = pos; r.hop = hop; r.uiClear = clear;
  if (!clear) console.log('    !! A DIALOGUE BOX WOULD NOT CLOSE — markers are hidden, ignore this station');
  rows.push(r);
  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 82 });
  writeFileSync(join(OUT, name + '.jpg'), Buffer.from(shot.data, 'base64'));

  console.log('\n=== ' + name + '  want ' + JSON.stringify(pos) + '  got ' + JSON.stringify(r.pos) +
    '   shot=' + r.shot);
  console.log('    objective: ' + JSON.stringify(r.obj));
  const wh = r.wayhint;
  console.log('    SHIPPED HINT: ' + (wh ? (wh.dest ? (wh.dest + '  via ' + String(wh.edge).slice(-26) +
      '  hops=' + wh.hops + '  shown=' + wh.shown + '  labelled=' + wh.labelled) : 'none (beat=' + wh.beat + ')')
    : 'Story.wayhint absent'));
  console.log('    SHORTEST BY METRES toward ' + TARGET + ': ' +
    // hop.path can be an EMPTY array: standing in the target shot already is 0 hops, not
    // "no path". It crashed the run at station B the first time this probe was pointed at
    // a target inside its own station list.
    (hop && hop.path && hop.path.length
      ? (hop.hops + ' hops / ' + hop.m.toFixed(1) + ' m, first = ' + hop.path[0].edge + ' -> ' + hop.path[0].to)
      : (hop && hop.path ? 'ALREADY IN ' + TARGET + ' (0 hops)' : 'NO PATH')));
  if (hop && hop.alts && hop.alts.length)
    console.log('       runners-up: ' + hop.alts.map(a => a.hops + ' hops / ' + a.m.toFixed(1) + ' m via ' + String(a.first).slice(-22)).join('  ·  '));
  if (hop && hop.path && hop.path.length && wh && wh.edge && wh.edge !== hop.path[0].edge)
    console.log('       !! SHIPPED HINT DISAGREES with the metre-shortest first hop');
  for (const m of (r.markers || [])) {
    if (!m.shown) continue;
    const onRoute = hop && hop.path && hop.path[0] && hop.path[0].edge === m.id;
    const top = m.pick && m.pick[0] ? m.pick[0].name : '(nothing)';
    console.log('    ' + (onRoute ? '>>' : '  ') + ' ' + (m.kind || '?').padEnd(8) +
      ' draws@' + JSON.stringify(m.markerPx && m.markerPx.map(v => Math.round(v))) +
      '  seam@' + JSON.stringify(m.seamPx && m.seamPx.map(v => Math.round(v))) +
      '  lift ' + m.liftPx + 'px (' + m.liftFrac + ' frame)' +
      '  click hits: ' + top +
      '  [' + (m.label || m.camTo || m.id.slice(-24)) + ']');
    if (m.caps) for (const c of m.caps)
      console.log('        cap ' + String(c.cap).padStart(3) + 'px -> @' +
        JSON.stringify(c.px.map(v => Math.round(v))) + '  hits: ' +
        ((c.pick && c.pick[0]) ? c.pick[0].name : '(nothing)'));
  }
}
writeFileSync(join(OUT, 'stations.json'), JSON.stringify(rows, null, 1));
console.log('\nwrote ' + OUT);
reap(); process.exit(0);
