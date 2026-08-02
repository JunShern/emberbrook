// trigger_probe.mjs — PROMPTS ARE LEVEL-TRIGGERED; MARKERS COVER EVERY TRANSITION.
//
//   node tools/trigger_probe.mjs --port=3000
//   node tools/trigger_probe.mjs --static      (declared-vs-derived audit only; no browser)
//
// THREE user reports, one instrument.
//
// 1. "To get the option to pop up, I need to step away from the entry/exit and
//    then re-enter." Root cause: sgTick's arrival-suppression latch (armed) gated
//    the PROMPT as well as auto fires, and sgHandoff resets armed=null on every
//    handoff — so any arrival/cut that landed inside a pad swallowed that pad's
//    prompt until the player left and came back. The contract this file asserts:
//    the prompt is LEVEL-TRIGGERED (in pad + no lock => prompt, every frame,
//    including the frame you arrive on) while the no-return rule still holds
//    (arriving inside a pad NEVER auto-fires the transition back).
//
// 2. "Entry and exit markers are only present for doorways — include them for
//    every scene transition point." The FF7 markers skipped auto (cut-band)
//    edges. This file measures, per scene and per shot: live transition edges
//    (door/portal/cut) vs markers actually rendered in the DOM, and asserts
//    every live door/portal shows a marker in its own shot and every shot with
//    live cut seams shows at least one seam marker. The per-scene totals it
//    prints are the coverage numbers for the report.
//
// 3. "There's no entry marker for entering Emberbrook from the old gate."
//    NOT a marker bug — a coverage-inventory hole. The runtime audit above
//    enumerates scenegraph EDGES, which is blind to a transition the derive
//    never emitted. The old gate is declared in BOTH authoring files and
//    absent from the scenegraph, so no prompt and no marker CAN render there.
//    The DECLARED-vs-DERIVED section audits the authoring truth (region
//    road.portals + town map exits) against the derived edge list, BY NAME,
//    so an unwired gate is a named row instead of silence.
//
// Same no-dependency CDP harness as tools/transition_test.mjs (real Chrome,
// swiftshader, background-tab-safe: all state read through SIM, never pixels).
import { spawn } from 'child_process';
import { rmSync, readFileSync, readdirSync } from 'fs';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { freePort, killOrphans, findPage, GAME_PAGE } from './cdp.mjs';
const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '8123'), 10);
// PORT: a free one unless --cdp says otherwise. Two tools shipped 9351 and
// would have collided; a fixed port also collides with an orphan of yourself.
const CDP_PORT = parseInt(arg('cdp', '0'), 10) || await freePort();   // was 9351
const HEAD = argv.includes('--head');
const STATIC_ONLY = argv.includes('--static');
const CHROME = process.env.CHROME_BIN ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE = `http://localhost:${PORT}/play3d.html`;
const URL0 = `${BASE}?scene=emb-cine&nomusic=1`;

let pass = 0, fail = 0;
const ok = (c, m, extra) => { if (c) { pass++; console.log('  ok   ' + m); }
  else { fail++; console.log('  FAIL ' + m + (extra !== undefined ? '  ' + JSON.stringify(extra) : '')); } };
const note = (m) => console.log('       ' + m);
const head = (s) => console.log('\n== ' + s);
const sleep = ms => new Promise(r => setTimeout(r, ms));

const profile = join(process.env.TMPDIR || '/tmp', 'trigger-probe-profile');
let chrome = null;
if (!STATIC_ONLY) {
  killOrphans(profile);   // a live Chrome still holding this profile makes the rmSync a lie
  rmSync(profile, { recursive: true, force: true });
  chrome = spawn(CHROME, [
    `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-gpu',
    '--autoplay-policy=no-user-gesture-required',
    '--window-size=1400,800', ...(HEAD ? [] : ['--headless=new']), URL0,
  ], { stdio: 'ignore' });
}
let closing = false;
const kill = () => { if (closing) return; closing = true;
  try { if (chrome) chrome.kill('SIGKILL'); } catch (e) {}
  try { if (chrome) rmSync(profile, { recursive: true, force: true, maxRetries: 3 }); } catch (e) {} };
process.on('exit', kill);
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP'])
  process.on(sig, () => { kill(); process.exit(130); });

// findPage's failure carries its evidence (every CDP target it saw, and whether
// CDP answered at all) — see tools/cdp.mjs.
const targetWs = () => findPage(CDP_PORT, { tries: 120, label: 'trigger_probe' });
function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 64 * 1024 * 1024 });
    const pend = new Map(); let id = 0;
    ws.on('open', () => res({
      send(method, params) {
        return new Promise((okk, no) => { const mid = ++id; pend.set(mid, { ok: okk, no });
          ws.send(JSON.stringify({ id: mid, method, params: params || {} })); });
      },
      close() { try { ws.close(); } catch (e) {} },
    }));
    ws.on('error', rej);
    ws.on('message', raw => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { ok: okk, no } = pend.get(m.id); pend.delete(m.id);
        m.error ? no(new Error(m.error.message)) : okk(m.result); }
    });
  });
}
let cdp;
async function ev(expr, timeoutMs) {
  const r = await cdp.send('Runtime.evaluate', {
    expression: expr, awaitPromise: true, returnByValue: true,
    userGesture: true, timeout: timeoutMs || 120000 });
  if (r.exceptionDetails) throw new Error('page exception: ' +
    ((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text));
  return r.result && r.result.value;
}
const READY = `(async()=>{for(let i=0;i<600;i++){
  const S=window.SIM; if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy){
    const c=S.cine&&S.cine(); if(!c||c.shot) return true; }
  await new Promise(r=>setTimeout(r,100));} return false;})()`;
// markers are painted by markersTick in the rAF frame; give the page real frames,
// raced with a ceiling because rAF can stall in a background tab.
const FRAMES = `Promise.race([new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(r)))),
  new Promise(r=>setTimeout(r,1500))])`;
const MARKERS = `[...document.querySelectorAll('#exit-markers div')]
  .filter(m=>m.style.display!=='none')
  .map(m=>({id:m.dataset.edge,kind:m.dataset.kind}))`;

async function goScene(scene) {
  await cdp.send('Page.navigate', { url: `${BASE}?scene=${scene}&nomusic=1` });
  await sleep(800);
  const r = await ev(READY, 90000);
  if (r !== true) throw new Error(scene + ' never became playable');
}

// ==== DECLARED vs DERIVED — the authoring truth, cross-checked by name =======
// The runtime sections below enumerate scenegraph EDGES, which is blind to a
// transition the derive never emitted (user report 2026-08-02: no entry marker
// at Emberbrook's old gate — the culvert-court crossing, the town's primary
// entrance). Here every declared region road portal and town map exit is
// checked against the derived edge list:
//   targeted region portal  -> MUST have its edge pair (assertion)
//   every other declared row -> must be EXPLAINED, by name, in scenegraph.json's own
//                               `sealed` / `unpaired` inventory (added 2026-08-02 with
//                               the derive fix). An unexplained row is a FAILURE here:
//                               that is the state the old gate sat in — declared on both
//                               sides, derived zero times, and nothing anywhere said so.
//
// RECONCILED 2026-08-02. The three defects this section was written to expose are fixed
// in tools/scenegraph_derive.mjs: it reads `sealed`, it pairs a region portal to the town
// exit the portal NAMES (it used to take the first land exit in the file, so 'old-gate'
// could never reach 'sigil-gate-downstream' with 'valley-road-south' listed first), and
// an unpaired portal prints a WARN carrying its own id instead of a wordless `continue`.
const EXPLAINED = 'explained';
function staticAudit() {
  head('DECLARED vs DERIVED — region portals + town exits vs scenegraph edges');
  const root = join(HERE, '..', 'public');
  const sg = JSON.parse(readFileSync(join(root, 'world/scenegraph.json'), 'utf8'));
  const edges = (sg.edges || []).filter(e => e.kind === 'portal');
  const sealedRows = sg.sealed || [];
  const unpairedTxt = (sg.unpaired || []).join('\n');
  const world = JSON.parse(readFileSync(join(root, 'world/world.json'), 'utf8'));
  const derivedTowns = new Set((world.landmarks || [])
    .filter(l => l.class === 'town' && l.refinesTo)
    .map(l => l.refinesTo.replace(/^.*\//, '').replace(/\.map\.json$/, '')));
  const rows = [];
  let unexplained = 0;
  const row = (where, what, target, status, kind) => {
    rows.push({ where, what, target, status });
    if (kind !== EXPLAINED && kind !== 'derived') unexplained++;
  };
  for (const f of readdirSync(join(root, 'world/regions')).filter(n => n.endsWith('.region.json'))) {
    const reg = JSON.parse(readFileSync(join(root, 'world/regions', f), 'utf8'));
    for (const p of ((reg.road || {}).portals || [])) {
      const got = edges.filter(e => e.id.endsWith('@' + p.id));
      const seal = sealedRows.find(s => s.portal === `${reg.region || reg.id || ''}:${p.id}` ||
                                        String(s.portal).endsWith(':' + p.id));
      let status, kind;
      if (got.length >= 2) { status = `derived (edge pair, exit '${p.exit || '(unnamed — first-in-list)'}')`; kind = 'derived'; }
      else if (seal) { status = `SEALED-PENDING — exit '${seal.exit}' is sealed; opens on ${seal.opensOn || 'NO FLAG DECLARED'}`; kind = EXPLAINED; }
      else if (unpairedTxt.includes(`'${p.id}'`)) { status = 'UNPAIRED, named in scenegraph.unpaired — no edge by design'; kind = EXPLAINED; }
      else { status = 'UNEXPLAINED — no edge, and scenegraph names no reason'; kind = 'bad'; }
      row(f, "road.portals '" + p.id + "'", p.target || 'null', status, kind);
      if (p.target && !seal) ok(got.length >= 2,
        `region portal '${p.id}' -> ${p.target}: scenegraph carries its edge pair`, got.map(e => e.id));
    }
  }
  for (const f of readdirSync(join(root, 'townmap')).filter(n => n.endsWith('.map.json'))) {
    let m; try { m = JSON.parse(readFileSync(join(root, 'townmap', f), 'utf8')); } catch (e) { continue; }
    const town = f.replace(/\.map\.json$/, '');
    for (const x of (m.exits || [])) {
      if ((x.mode || 'land') !== 'land') continue;
      const wired = edges.some(e => (e.source || '').includes(`exit '${x.id}'`));
      const seal = sealedRows.find(s => s.town === town && s.exit === x.id);
      let status, kind;
      if (wired) { status = 'derived (edge pair)'; kind = 'derived'; }
      else if (seal) { status = `SEALED-PENDING — opens on ${seal.opensOn || 'NO FLAG DECLARED'}; ${seal.effect}`; kind = EXPLAINED; }
      else if (unpairedTxt.includes(`'${x.id}'`)) { status = 'UNPAIRED, named in scenegraph.unpaired — no region portal names it'; kind = EXPLAINED; }
      else if (!derivedTowns.has(town)) { status = 'town is not in world.json — never derived, so no edge is expected'; kind = EXPLAINED; }
      else { status = 'UNEXPLAINED — no edge, and scenegraph names no reason'; kind = 'bad'; }
      row(f, "exits '" + x.id + "' at " + x.at, x.to || '?', status, kind);
    }
  }
  console.log('   declared in                what                                          target        status');
  for (const r of rows)
    console.log(`   ${r.where.padEnd(26)} ${r.what.padEnd(45)} ${String(r.target).padEnd(13)} ${r.status}`);
  ok(unexplained === 0,
    `declared-vs-derived reconciles: ${rows.length} declared rows, 0 UNEXPLAINED ` +
    `(${sealedRows.length} sealed-pending, ${(sg.unpaired || []).length} named unpaired)`,
    { unexplained });
  note('THE OLD GATE (user report 2026-08-02, "no entry marker for entering Emberbrook from');
  note('the old gate") is WIRED, and the row above says so: it derives an edge pair. The');
  note('history is worth keeping because the note that stood here for half a day said two');
  note('lines were owed and named the wrong flag for one of them. What actually shipped:');
  note('  · the DERIVE emits a sealed exit that declares a `sealedUntil` as a CONDITIONAL');
  note('    pair carrying when:{flag:...} (a sealed exit with NO sealedUntil is still no');
  note('    edge — nothing can ever open it, so an edge would be a promise data cannot keep)');
  note('  · play3d.html sgLive() evaluates `when` (and the `requires` shorthand) with');
  note('    Dialogue.check on EVERY PHYSICS TICK — not at bind time, because the frame the');
  note('    flag flips the edge and its marker must appear with nothing reloaded');
  note('  · the flag is story.ch1.gate-open, set by game/story.json\'s ch1.sigils beat');
  note('    through GS.setFlags. NOT ch1.gateOpen: nothing in the shipped game ever wrote');
  note('    that name, and tools/story_test.mjs caught it as a read with no writer.');
  note('So the sealed row is still an ABSENCE in play until the chapter opens it — no edge,');
  note('no prompt, no marker — and that absence is now asserted, not assumed');
  note('(tools/playthrough_test.mjs measures the edge both sides of the flag).');
}

(async function main() {
  staticAudit();
  if (STATIC_ONLY) {
    console.log(`\n${fail ? 'FAIL' : 'PASS'}  ${pass} assertions ok, ${fail} failed  (--static: declared-vs-derived only)`);
    process.exit(fail ? 1 : 0);
  }
  cdp = await connect(await targetWs());
  await cdp.send('Runtime.enable');
  await cdp.send('Page.enable');

  head('BOOT emb-cine');
  ok(await ev(READY, 90000) === true, 'emb-cine playable');

  // ==== PART A — THE PROMPT IS LEVEL-TRIGGERED =============================
  head('PROMPT — first entry into a pad shows the offer (control)');
  const A = await ev(`(async()=>{
    await SIM.shot('square');
    const E=()=>SIM.edges();
    const d=E().find(e=>e.kind==='door'&&e.live&&e.id.indexOf('item')>=0);
    if(!d) return {error:'no live item-shop door in square', have:E().filter(e=>e.live).map(e=>e.id)};
    // stand OFF the pad, then walk-in (tp is position-only; sgTick runs in tick()).
    // tpY, not tp: a plain ground() snap beside a shopfront can pick an awning
    // (measured: dy 2.21 > vTol 2 — the pad was never entered and the control
    // measured nothing). tpY picks the floor nearest the pad's own height.
    SIM.tpY(d.at[0]+d.r+1.4, d.at[2]+d.r+1.4, d.at[1]); SIM.tick(3);
    const offPad={prompt:SIM.prompt(), edge:E().find(e=>e.id===d.id)};
    SIM.tpY(d.at[0], d.at[2], d.at[1]); SIM.tick(2);  // FIRST frame inside the pad
    const onPad={prompt:SIM.prompt(), edge:E().find(e=>e.id===d.id)};
    return {door:d.id, label:d.label, offPad, onPad};
  })()`);
  if (A.error) { ok(false, 'setup: live door found', A); }
  else {
    ok(!A.offPad.edge.inRange, `off-pad: ${A.door} out of range (d=${A.offPad.edge.dist})`);
    ok(A.onPad.edge.inRange && !!A.onPad.prompt && A.onPad.prompt.id === A.door,
       `walking INTO the pad prompts on FIRST entry ("${A.onPad.prompt && A.onPad.prompt.text}")`, A.onPad);
  }

  head('PROMPT — an edge that CONTAINS you when it binds still prompts (the latch)');
  // This is the exact shape of every arrival and of every post-handoff rebind:
  // armed=null decided while the player is already inside. SIM.addEdge ships
  // armed:null, so it reproduces the bind state without needing a door first.
  const L = await ev(`(async()=>{
    // step clear of the door pad first: the probe edge must be the nearest
    // in-range edge (a d=0 tie goes to SGE order, i.e. to the door)
    SIM.tp(SIM.pos().x+3.4, SIM.pos().z+3.4); SIM.tick(2);
    const p=SIM.pos();
    const i=SIM.addEdge({at:[p.x,p.y,p.z], r:2.0, to:SIM.scene(), label:'PROBE-PAD', kind:'test'});
    SIM.tick(3);
    const e=SIM.edges()[i];
    return {inRange:e.inRange, armed:e.armed, prompt:SIM.prompt()};
  })()`);
  ok(L.inRange === true, 'the probe edge contains the player at bind time', L);
  ok(!!L.prompt && L.prompt.label === 'PROBE-PAD',
     `spawn-inside pad still prompts (armed=${L.armed} — the latch no longer gates the offer)`, L);

  head('PROMPT — real arrival: interior spawns ON its exit pad (seam-canon no-return)');
  const R = await ev(`(async()=>{
    const r=await SIM.door('emb-item-int');
    if(r.error) return r;
    SIM.tick(2);
    const e=SIM.edges()[0], p1=SIM.prompt();
    SIM.tick(60);                                  // ~1s of standing still on the pad
    return {landed:r.to||SIM.scene(), exitEdge:{id:e.id,inRange:e.inRange,armed:e.armed,dist:e.dist},
            prompt:p1, sceneAfter:SIM.scene(), promptAfter:SIM.prompt()};
  })()`, 120000);
  ok(R.landed === 'emb-item-int', 'entered the item shop', R);
  ok(R.exitEdge.inRange === true,
     `MEASURED: the arrival stands INSIDE the exit trigger (d=${R.exitEdge.dist} of r=1.8) — the reported repro`, R.exitEdge);
  ok(!!R.prompt && /Leave/.test(R.prompt.label || ''),
     `the exit prompt is up on arrival ("${R.prompt && R.prompt.text}") — no step-out-step-in needed`, R.prompt);
  ok(R.sceneAfter === 'emb-item-int',
     'and 60 ticks later we are STILL inside — the prompt did not auto-fire (no-return holds)', R.sceneAfter);
  const back = await ev(`SIM.door('emb-cine')`, 120000);
  ok(back.to === 'emb-cine', 'back out to the town', back);

  // ==== PART B — MARKER COVERAGE, MEASURED PER SCENE/SHOT ===================
  head('MARKERS — every transition point, counted');
  const coverage = [];
  async function coverCine(scene) {
    await goScene(scene);
    const shots = await ev(`SIM.cine().shots`);
    const rows = [];
    for (const shot of shots) {
      const row = await ev(`(async()=>{
        // The correction net is live during this measurement: cineGo's fade takes
        // ~21 rAF frames while the player still stands on the PREVIOUS shot's
        // ground, which is exactly correctionGrace — so a jump can be quietly
        // reverted before the DOM is read (measured: pondlane read square's
        // edges). Park the player on the target shot's own spawn and verify the
        // shot HELD; retry up to 3 times.
        for(let a=0;a<3;a++){
          const c=await SIM.shot(${JSON.stringify(shot)});
          if(c&&c.error) return c;
          const b=SIM.cine().baked; if(b&&b.spawn) SIM.tp(b.spawn[0],b.spawn[2],b.spawn[1]);
          await ${FRAMES}; await ${FRAMES};
          for(let i=0;i<200&&SIM.transitions().busy;i++) await new Promise(r=>setTimeout(r,25));
          if(SIM.cine().shot===${JSON.stringify(shot)}) break;
        }
        if(SIM.cine().shot!==${JSON.stringify(shot)}) return {error:'shot would not hold'};
        await ${FRAMES};
        const live=SIM.edges().filter(e=>e.live);
        const mk=${MARKERS};
        return {shot:${JSON.stringify(shot)},
          doors:live.filter(e=>!e.auto&&e.kind==='door').map(e=>e.id),
          portals:live.filter(e=>!e.auto&&e.kind==='portal').map(e=>e.id),
          passages:live.filter(e=>!e.auto&&e.kind==='passage').map(e=>e.id),
          cuts:live.filter(e=>e.auto).map(e=>e.id),
          shown:mk.map(m=>m.id)};
      })()`);
      if (row.error) { ok(false, `${scene}/${shot}: ${row.error}`); continue; }
      rows.push(row);
      // PASSAGES COUNT AS PROMPTED TRANSITIONS. They arrived 2026-08-02 with the
      // Dellhollow gate stair, and a class of transition this file does not tally is a
      // class whose markers nobody is asserting — the exact hole that hid the old gate.
      const missDP = [...row.doors, ...row.portals, ...row.passages].filter(id => !row.shown.includes(id));
      const cutShown = row.cuts.filter(id => row.shown.includes(id));
      ok(missDP.length === 0,
         `${scene}/${row.shot}: every door/portal/passage marked ` +
         `(${row.doors.length + row.portals.length + row.passages.length})`, missDP);
      if (row.cuts.length)
        ok(cutShown.length >= 1,
           `${scene}/${row.shot}: shot-exit seams marked (${cutShown.length}/${row.cuts.length} in frame)`,
           { cuts: row.cuts, shown: row.shown });
    }
    const tally = k => rows.reduce((a, r) => a + r[k].length, 0);
    const shownOf = k => rows.reduce((a, r) => a + r[k].filter(id => r.shown.includes(id)).length, 0);
    coverage.push({ scene, shots: rows.length,
      doors: `${shownOf('doors')}/${tally('doors')}`, portals: `${shownOf('portals')}/${tally('portals')}`,
      passages: `${shownOf('passages')}/${tally('passages')}`,
      cuts: `${shownOf('cuts')}/${tally('cuts')}` });
  }
  await coverCine('emb-cine');
  await coverCine('del-cine');

  // interiors: one exit door each, one fixed camera
  for (const s of ['emb-item-int', 'emb-inn-int', 'emb-lake-int', 'emb-bakery-int',
                   'del-inn-int', 'del-item-int', 'del-weapon-int', 'del-armor-int',
                   'del-cookhouse-int', 'del-cottage-int']) {
    await goScene(s);
    const r = await ev(`(async()=>{ await ${FRAMES}; await ${FRAMES};
      const live=SIM.edges().filter(e=>e.live&&!e.auto);
      return {live:live.map(e=>e.id), shown:(${MARKERS}).map(m=>m.id)}; })()`);
    const miss = r.live.filter(id => !r.shown.includes(id));
    ok(miss.length === 0, `${s}: exit door marked (${r.shown.length}/${r.live.length})`, r);
    coverage.push({ scene: s, shots: 1, doors: `${r.live.length - miss.length}/${r.live.length}`,
                    portals: '0/0', passages: '0/0', cuts: '0/0' });
  }

  // overworld: two town-gate portals under the free follow camera. Stand near
  // each, aim the orbit at it, and expect its marker.
  await goScene('ow-valley');
  const OW = await ev(`(async()=>{
    const out=[];
    for(const e of SIM.edges().filter(x=>!x.auto)){
      SIM.tp(e.at[0]+4, e.at[2]+4);
      const ux=(e.at[0]-SIM.pos().x), uz=(e.at[2]-SIM.pos().z), n=Math.hypot(ux,uz);
      if(window.ORBIT){ ORBIT.yaw=Math.atan2(-(uz/n),-(ux/n)); }
      await ${FRAMES}; await ${FRAMES};
      out.push({id:e.id, shown:(${MARKERS}).map(m=>m.id).includes(e.id)});
    }
    return out;
  })()`);
  for (const o of OW) ok(o.shown, `ow-valley: ${o.id} marked when in frame`, o);
  coverage.push({ scene: 'ow-valley', shots: 1,
    doors: '0/0', portals: `${OW.filter(o => o.shown).length}/${OW.length}`,
    passages: '0/0', cuts: '0/0' });

  head('COVERAGE — transitions found vs markers rendered (live edges, own shot)');
  console.log('   scene              shots   doors   portals   passages   cuts(seams in frame)');
  for (const c of coverage)
    console.log(`   ${c.scene.padEnd(18)} ${String(c.shots).padStart(5)}   ${c.doors.padStart(5)}   ${c.portals.padStart(7)}   ${c.passages.padStart(8)}   ${c.cuts.padStart(6)}`);
  note('dev free-roam scenes (emb-townwalk, townwalk) have no scenegraph edges: 0 transitions, 0 markers by construction.');

  console.log(`\n${fail ? 'FAIL' : 'PASS'}  ${pass} assertions ok, ${fail} failed`);
  cdp.close(); kill();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('\nHARNESS ERROR:', e.message); kill(); process.exit(3); });
