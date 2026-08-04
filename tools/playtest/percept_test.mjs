/* percept_test.mjs — DOES THE HARNESS SEE THE GAME? (no LLM, no game server, seconds)
 *
 * WHY THIS EXISTS. On 2026-08-03 the playtest harness had five perception failures in
 * one day. Every one of them was the same class — THE ADAPTER REPORTED THE GAME'S STATE
 * WRONGLY — and every one cost a 30-60 minute LLM run to find and another to prove
 * fixed. The worst was PT-20260803-00x: a fully drawn, fully playable turn-based battle
 * whose entire percept was "OBJECTIVE ON SCREEN: Follow the road north", because
 * PERCEPT_JS had no .ebb-root in it. The run stalled 4.5 minutes on a screen that was
 * never blank.
 *
 * THE INSTRUMENT IS NOT THE GAME. This file feeds the adapter's OWN perception code
 * (PERCEPT_JS, FRAME_GATE_JS, flattenPercept — imported, never copied) four known
 * screens and asks what it reports. It runs headless Chrome on about:blank, so there is
 * a real layout engine, a real getComputedStyle and real rects — jsdom cannot do this
 * job, because the percept's visibility test IS getBoundingClientRect and jsdom returns
 * zeroes for every box, which would make every fixture invisible and every test pass.
 * No server, no bundle, no API key, no model.
 *
 * WHAT IT COVERS
 *   §1 DOM   four screens: overworld idle · dialogue with choices · battle, your turn ·
 *            transition veil. Assertions on the percept AND on the readiness gate.
 *   §2 REPLAY the 13 recorded runs in docs/qa/playtest/runs — real percepts from real
 *            play. flattenPercept must name the battle on every recorded battle step
 *            (the text is what the model actually reads), and the newest run must obey
 *            the publication invariants: nothing ready and black, no unready frame ever
 *            handed to the model, every refusal carrying a reason.
 *   §3 CENSUS every class the percept queries must still exist in the shipping UI
 *            source. A FIXTURE THAT AGREES WITH ITSELF PROVES NOTHING: this is the only
 *            thing standing between hand-written markup and silent drift the day
 *            somebody renames .ebb-cmds.
 *
 * WHAT IT DOES NOT COVER, said plainly. The walk executor's stall detection, the
 * PageSilent deadline and the two-captures-disagree check in observe() all need a live
 * page walking a real bundle; §2 catches the last of those after the fact (from the run
 * log) but none of the three before the run. Those stay the playtester's job.
 *
 *   node tools/playtest/percept_test.mjs [--headed]
 */
import { spawn } from 'child_process';
import { readFileSync, existsSync, readdirSync, rmSync } from 'fs';
import { join, dirname } from 'path';
import { createRequire } from 'module';
import { freePort, killOrphans, chromeArgs } from '../cdp.mjs';
import { PERCEPT_JS, FRAME_GATE_JS, BLACK_L, flattenPercept } from './adapter_emberbrook.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const ROOT = join(dirname(new URL(import.meta.url).pathname), '../..');
const HEADED = process.argv.includes('--headed');
const PROFILE_PREFIX = 'percept-test-profile-';
const HARD_EXPIRY_MS = 120000;   // this process may not outlive its own usefulness

// ---------------------------------------------------------------------------
let fails = 0, checks = 0, known = 0, warns = 0;
/* `note` turns a failure into a KNOWN DEFECT: it still prints, in full, but it does not
 * fail the gate. Used only for a blindness this file FOUND and deliberately did not fix
 * (fixing the adapter while testing it is how a test comes to agree with the bug).
 * Delete the note when the defect is fixed and the check starts guarding it. */
function ok(state, what, cond, claimed, truth, note) {
  checks++;
  if (cond) return true;
  if (note) { known++; console.log(`  KNOWN [${state}] ${what}`); }
  else { fails++; console.log(`  FAIL  [${state}] ${what}`); }
  console.log(`        the adapter reported: ${claimed}`);
  console.log(`        what was on screen:   ${truth}`);
  if (note) console.log(`        KNOWN DEFECT, not fixed here: ${note}`);
  return false;
}
function warn(state, what, cond, detail) {
  checks++;
  if (cond) return true;
  warns++;
  console.log(`  WARN  [${state}] ${what}: ${detail}`);
  return false;
}
const j = (v) => JSON.stringify(v);

// ============================ §1 THE FOUR SCREENS ==========================
// Markup mirrors what the shipping modules build: battle_turnbased.js:767-798,
// 884-890, 978-990, 1344, 1357 and ui_kit.js:474-485, 551, 572. §3 checks the class
// names are still real; the STRUCTURE is what is hand-held here.
const SIM_OK = `window.SIM={scene:()=>'ow-valley',pos:()=>({x:0,y:0,z:0}),
  transitions:()=>({busy:false}),gpu:()=>({meshes:47}),cine:()=>({shot:'road-a'}),
  cam:()=>({pos:[0,0,0],fwd:[0,0,1],fov:38,aspect:1.78})};`;
const SIM_BUSY = SIM_OK.replace('transitions:()=>({busy:false})', 'transitions:()=>({busy:true})');
const LOCK_ON = `window.UILOCK={active:()=>true};`;
const LOCK_OFF = `window.UILOCK={active:()=>false};`;

const BATTLE_HTML = [
  '<div class="ebb-root on">',
  '<div class="ebb-top"><div class="ebb-rail">',
  '<div class="eb-win ebb-hud"><span class="zone">FOREST</span><span class="rnd">ROUND 1</span></div>',
  '</div><div class="eb-win ebb-log"><span class="ebb-actor on"><b>Vesper</b></span>',
  '<span class="ebb-logtxt">What will you do?</span></div></div>',
  '<div class="ebb-field"><div class="ebb-stage"><div class="ebb-heroes"></div><div class="ebb-foes">',
  '<div class="ebb-foe cur"><div class="ebb-mark cur"></div><div class="ebb-stand"></div>',
  '<div class="ebb-ftags"><div class="ebb-ftag">Duskpad A</div></div></div>',
  '<div class="ebb-foe"><div class="ebb-mark"></div><div class="ebb-stand"></div>',
  '<div class="ebb-ftags"><div class="ebb-ftag">Duskpad B</div></div></div>',
  '</div></div></div>',
  '<div class="ebb-bottom"><div class="ebb-band">',
  '<div class="eb-win ebb-cmdwin"><span class="eb-wtitle"><span>Command</span></span>',
  '<div class="ebb-cmds">',
  '<div class="ebb-cmd cur"><span class="eb-cur on"></span>Attack</div>',
  '<div class="ebb-cmd"><span class="eb-cur"></span>Item</div>',
  '<div class="ebb-cmd"><span class="eb-cur"></span>Flee</div></div>',
  '<div class="eb-win ebb-sub on"><div class="ebb-item cur"><span class="eb-cur on"></span>',
  '<span class="k">Ember Tonic</span><span class="n">x2</span></div></div></div>',
  '<div class="eb-win ebb-partywin"><div class="ebb-party">',
  '<div class="ebb-prow cur"><span class="eb-cur"></span>',
  '<div class="ebb-pname"><b>Vesper</b><small>LV 1</small></div>',
  '<div class="ebb-php"><span class="nm"><b class="hp">34</b>/<span class="mx">34</span></span></div>',
  '</div></div></div></div></div></div>',
].join('');

// play3d's own #exit-markers layer: fixed, full-screen, background rgba(0,0,0,0).
// A TRANSPARENT BLACK IS NOT BLACK — matching rgb() alone once called this a veil and
// reported an unreadable screen over a frame measuring 121 luminance.
const EXIT_MARKERS = '<div id="exit-markers" style="position:fixed;inset:0;' +
  'background:rgba(0,0,0,0);pointer-events:none"></div>';

const STATES = [
  {
    name: 'overworld-idle',
    setup: SIM_OK + LOCK_OFF,
    html: '<div id="story-obj">Follow the road north</div>' +
      '<div id="sgp">Leave Emberbrook? [E]</div>' +
      '<div class="ebui-banner" id="ebui-p-poppy">Talk to Poppy [E]</div>' + EXIT_MARKERS,
    check(p, g, text) {
      ok(this.name, 'the objective line on screen is read',
        p.objective === 'Follow the road north', j(p.objective), 'Follow the road north');
      ok(this.name, 'the doorway prompt is read',
        p.prompts.some(s => /Leave Emberbrook/.test(s)), j(p.prompts), 'Leave Emberbrook? [E]');
      ok(this.name, "the NPC talk banner is read (it is how the player knows they can talk)",
        p.prompts.some(s => /Talk to Poppy/.test(s)), j(p.prompts), 'Talk to Poppy [E]');
      ok(this.name, 'nothing modal is invented',
        !p.dialogue && !p.card && !p.battle,
        `dialogue=${j(p.dialogue)} card=${j(p.card)} battle=${j(p.battle)}`,
        'a plain overworld frame with no modal open');
      ok(this.name, 'the frame is called ready',
        g.why.length === 0, j(g.why), 'the scene is painted and nothing is over it');
      ok(this.name, "play3d's transparent #exit-markers layer is NOT called a black veil",
        !g.why.some(w => /veil/.test(w)), j(g.why),
        'a full-screen layer with background rgba(0,0,0,0) — transparent, not black');
      ok(this.name, 'the flattened text carries the objective',
        /Follow the road north/.test(text), j(text), 'Follow the road north');
    },
  },
  {
    name: 'dialogue-with-choices',
    setup: SIM_OK + LOCK_ON,
    html: '<div class="ebui-veil on"><div class="ebui-panel">' +
      '<div class="ebui-head"><span class="ebui-title">Poppy</span></div>' +
      '<div class="ebui-body">The lamps want watching, not worrying.</div>' +
      '<div class="ebui-row cur"><span class="k">Ask about the gate</span></div>' +
      '<div class="ebui-row"><span class="k">Say nothing</span></div>' +
      '<div class="ebui-foot">E/Enter</div></div></div>',
    check(p, g, text) {
      ok(this.name, 'the dialogue box is seen at all', !!p.dialogue, j(p.dialogue), 'a dialogue box is open');
      const d = p.dialogue || {};
      ok(this.name, 'the speaker is read', d.speaker === 'Poppy', j(d.speaker), 'Poppy');
      ok(this.name, 'the line is read', /lamps want watching/.test(d.text || ''), j(d.text),
        'The lamps want watching, not worrying.');
      ok(this.name, 'both choices are read', (d.choices || []).length === 2,
        j(d.choices), 'two choices: Ask about the gate / Say nothing');
      ok(this.name, 'the cursor is on the first choice',
        // FOUND BY THIS FILE, 2026-08-03. ui_kit's row() marks the selected row with the
        // class 'cur' (ui_kit.js:572); PERCEPT_JS tested dialogue rows with
        // /sel|active|cursor/, which does not match it, so every ui_kit list (dialogue
        // choices, the pause menu, the shop) reached the model with selected:false on
        // every row. FIXED TWICE: the first fix inlined a regex with single-escaped \s
        // inside PERCEPT_JS's template literal, where it collapses to a literal 's' —
        // the fix shipped, this assertion stayed red, and nobody read it. It now calls
        // the percept's own cur() helper, which was correct all along.
        !!((d.choices || [])[0] || {}).selected, j(d.choices), 'the first row carries .cur');
      ok(this.name, 'a drawn modal is not called frozen',
        !g.frozen, j(g.frozen), 'UILOCK is held AND a dialogue box is drawn');
      ok(this.name, 'the flattened text offers the choices to the model',
        /CHOICES/.test(text) && /Ask about the gate/.test(text), j(text), 'two selectable choices');
    },
  },
  {
    // ===================== THE ONE THAT MATTERS ============================
    // This is PT-20260803's battle blindness, in a form that costs 3 seconds instead
    // of a 45-minute run: a whole game mode, fully drawn, with the harness holding a
    // modal lock. If PERCEPT_JS loses .ebb-root again, every assertion below fails.
    name: 'battle-your-turn',
    setup: SIM_OK + LOCK_ON,
    // The doorway banner is still in the DOM under a full-screen battle, and a player
    // cannot see it. Reporting it would be reporting something not drawn.
    html: '<div id="story-obj">Follow the road north</div><div id="sgp">Leave Emberbrook? [E]</div>' + BATTLE_HTML,
    check(p, g, text) {
      const seen = ok(this.name, 'THE BATTLE IS SEEN AT ALL', !!p.battle, j(p.battle),
        'a drawn turn-based battle: FOREST ROUND 1, two Duskpads, command menu open');
      // These two are the DOWNSTREAM HARM of not seeing it — the 4.5-minute stall and
      // the "nothing is drawn" prompt — so they are asserted even when the percept is
      // empty. A test that stops at the first symptom hides the damage.
      ok(this.name, 'A DRAWN BATTLE IS NOT "a modal lock with nothing drawn on it"',
        !g.frozen, j(g.frozen), 'UILOCK is held AND a whole battle screen is drawn');
      ok(this.name, 'THE TEXT THE MODEL READS SAYS THERE IS A BATTLE',
        /A BATTLE IS UNDER WAY/.test(text), j(text), 'a battle is under way');
      if (!seen) return;
      const b = p.battle;
      ok(this.name, 'both foes are named', b.foes.length === 2 && /Duskpad A/.test(j(b.foes)),
        j(b.foes), 'Duskpad A (targeted) and Duskpad B');
      ok(this.name, 'the targeted foe is marked', !!(b.foes[0] || {}).targeted, j(b.foes[0]),
        'the first foe carries .cur and a .ebb-mark.cur');
      ok(this.name, 'the commands are readable', b.commands.length === 3, j(b.commands),
        'Attack / Item / Flee');
      ok(this.name, 'the cursor position is reported', !!(b.commands[0] || {}).selected,
        j(b.commands[0]), 'Attack carries .cur');
      ok(this.name, 'it knows the menu is DRIVABLE (.ebb-cmds without .idle)',
        b.yourTurn === true, `yourTurn=${j(b.yourTurn)}`, 'the command box is not .idle — it is your turn');
      ok(this.name, 'the open sub-menu is read', (b.submenu || []).length === 1,
        j(b.submenu), 'the item sub-menu is open with Ember Tonic x2');
      ok(this.name, 'the party HP is read', /34\/34 HP/.test(j(b.party)), j(b.party), 'Vesper LV 1 34/34 HP');
      ok(this.name, 'the zone and round are read', b.zone === 'FOREST' && /ROUND/.test(b.round || ''),
        `${j(b.zone)} ${j(b.round)}`, 'FOREST / ROUND 1');
      ok(this.name, 'the doorway banner under the battle is NOT reported',
        p.prompts.length === 0, j(p.prompts), 'the banner is covered by a full-screen battle');
      ok(this.name, 'the frame is called ready', g.why.length === 0, j(g.why), 'the battle is painted');
      ok(this.name, 'the text names the foes and the commands',
        /Duskpad A/.test(text) && /Attack/.test(text), j(text), 'Duskpad A, Duskpad B, Attack/Item/Flee');
      ok(this.name, 'the text says whose turn it is',
        /IT IS YOUR TURN/.test(text), j(text), 'the command menu is drivable');
    },
  },
  {
    /* THE PAUSE MENU IS A DIFFERENT SHAPE OF PANEL, and the percept was blind to it.
     * menu.js renders with layout:'full', whose nav list is .mn-nav > .mn-navrow —
     * not the .ebui-row every other ui_kit panel draws. Measured on the live game
     * 2026-08-04: Escape opens it (Menu.isOpen true, one visible .ebui-veil,
     * "PARTY EQUIP ITEMS SAVE LOAD NEW GAME" in the DOM) and the percept returned
     * ZERO rows, so an agent that paused was handed an empty list. Markup below is
     * copied from that live dump. */
    name: 'pause-menu',
    setup: SIM_OK + LOCK_ON,
    html: '<div class="ebui-veil on"><div class="ebui-panel full">' +
      '<div class="ebui-head"><span class="ebui-title">PAUSE</span>' +
      '<span class="ebui-sub">Chapter 1 &middot; del-cine</span></div>' +
      '<div class="ebui-body"><div class="mn-grid"><div class="eb-win mn-nav">' +
      '<div class="mn-navrow cur">PARTY</div><div class="mn-navrow">EQUIP</div>' +
      '<div class="mn-navrow">ITEMS</div><div class="mn-navrow">SAVE</div>' +
      '<div class="mn-navrow">LOAD</div><div class="mn-navrow">NEW GAME</div>' +
      '</div></div></div></div></div>',
    check(p, g, text) {
      const d = p.dialogue || {};
      ok(this.name, 'the pause menu is seen at all', !!p.dialogue, j(p.dialogue), 'a panel is open');
      ok(this.name, 'all six commands are read', (d.choices || []).length === 6,
        j((d.choices || []).map(c => c.text)), 'PARTY EQUIP ITEMS SAVE LOAD NEW GAME');
      ok(this.name, 'SAVE is one of them', (d.choices || []).some(c => /^SAVE$/.test(c.text || '')),
        j((d.choices || []).map(c => c.text)), 'a player can find SAVE');
      ok(this.name, 'the cursor is read', !!((d.choices || [])[0] || {}).selected,
        j(d.choices), 'the first row carries .cur');
    },
  },
  {
    name: 'transition-veil',
    setup: SIM_BUSY + LOCK_OFF,
    html: '<div id="story-obj">Follow the road north</div>' +
      '<div style="position:fixed;inset:0;background:#000;opacity:1;z-index:9"></div>',
    check(p, g, text) {
      ok(this.name, 'the black veil is seen', g.why.some(w => /veil/.test(w)), j(g.why),
        'a full-screen opaque black div over the picture');
      ok(this.name, 'the in-flight transition is seen', g.why.some(w => /transition/.test(w)),
        j(g.why), 'SIM.transitions().busy is true');
      ok(this.name, 'THE FRAME IS REFUSED, not published',
        g.why.length > 0, 'ready (no reasons)', 'nothing a player could see is on screen');
    },
  },
];

// ---------------------------------------------------------------------------
async function runDom() {
  console.log('§1 THE FIVE SCREENS (real DOM, headless Chrome, no game)');
  const port = await freePort();
  const profile = join(process.env.TMPDIR || '/tmp', PROFILE_PREFIX + process.pid);
  let chrome = null;
  const reap = () => {
    try { chrome && chrome.kill('SIGKILL'); } catch (e) { }
    try { killOrphans(profile); } catch (e) { }
    try { rmSync(profile, { recursive: true, force: true }); } catch (e) { }
  };
  process.on('exit', reap);
  for (const s of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(s, () => { reap(); process.exit(130); });
  // A HARD SELF-EXPIRY. Anything that spawns a browser here gets one: leaked Chrome
  // cost this machine 7.6 GB in a morning.
  const expiry = setTimeout(() => {
    console.log('  FAIL  the DOM section did not finish in ' + HARD_EXPIRY_MS + ' ms — killing Chrome');
    reap(); process.exit(9);
  }, HARD_EXPIRY_MS);

  rmSync(profile, { recursive: true, force: true });
  // State-only assertions: software rasterisation is fine and faster. Nothing here
  // photographs a render.
  chrome = spawn(process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    chromeArgs({ port, profile, url: 'about:blank', gpu: false, size: '1280,800', headed: HEADED }),
    { stdio: 'ignore' });

  // AN INSTRUMENT THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING: this
  // matcher is about:blank, not cdp.mjs's GAME_PAGE, and its failure dumps the targets.
  let wsUrl = null, targets = null, reached = false;
  for (let i = 0; i < 200 && !wsUrl; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/list`);
      targets = await r.json(); reached = true;
      const p = targets.find(t => t.type === 'page');
      if (p) wsUrl = p.webSocketDebuggerUrl;
    } catch (e) { }
    if (!wsUrl) await new Promise(r => setTimeout(r, 100));
  }
  if (!wsUrl) {
    console.log('  FAIL  Chrome never exposed a page on port ' + port +
      (reached ? ` — CDP answered with ${targets.length} target(s): ` + j(targets.map(t => t.url))
        : ' — CDP was never reachable, so Chrome did not start'));
    fails++; clearTimeout(expiry); reap(); return;
  }
  const cdp = await new Promise((res, rej) => {
    const ws = new WebSocket(wsUrl, { perMessageDeflate: false });
    const pend = new Map(); let id = 0;
    ws.on('open', () => res({
      send(m, p) { return new Promise((okk, no) => { const mid = ++id; pend.set(mid, { okk, no }); ws.send(JSON.stringify({ id: mid, method: m, params: p || {} })); }); },
      close() { try { ws.close(); } catch (e) { } },
    }));
    ws.on('error', rej);
    ws.on('message', raw => {
      let m; try { m = JSON.parse(raw); } catch (e) { return; }
      if (m.id && pend.has(m.id)) { const { okk, no } = pend.get(m.id); pend.delete(m.id); m.error ? no(new Error(m.error.message)) : okk(m.result); }
    });
  });
  await cdp.send('Runtime.enable'); await cdp.send('Page.enable');
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  const ev = async (expr) => {
    const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error('page exception: ' +
      ((r.exceptionDetails.exception || {}).description || r.exceptionDetails.text));
    return r.result && r.result.value;
  };

  for (const st of STATES) {
    await ev(`(()=>{ document.body.innerHTML=${j(st.html)}; ${st.setup} return 1; })()`);
    const p = await ev(PERCEPT_JS);
    const g = await ev(FRAME_GATE_JS);
    const before = fails;
    st.check(p, g || { why: [] }, flattenPercept(p));
    console.log(`  ${fails === before ? 'ok  ' : 'FAIL'}  ${st.name}`);
  }
  clearTimeout(expiry);
  cdp.close(); reap();
}

// ======================= §2 THE RECORDED RUNS ==============================
function runReplay() {
  console.log('§2 THE RECORDED RUNS (real percepts from real play)');
  const dir = join(ROOT, 'docs/qa/playtest/runs');
  const runs = existsSync(dir) ? readdirSync(dir).filter(d => d.startsWith('run-')).sort() : [];
  if (!runs.length) { console.log('  FAIL  no recorded runs to replay'); fails++; return; }
  const readJsonl = (f) => existsSync(f)
    ? readFileSync(f, 'utf8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch (e) { return null; } }).filter(Boolean)
    : [];

  // (a) THE TEXT THE MODEL READS, over every battle step ever recorded.
  let battleSteps = 0;
  for (const r of runs) {
    for (const rec of readJsonl(join(dir, r, 'run.jsonl'))) {
      const b = rec.percept && rec.percept.battle;
      if (!b) continue;
      battleSteps++;
      const text = flattenPercept(rec.percept);
      ok(`replay/${r}#${rec.step}`, 'a recorded battle survives flattening into the model prompt',
        /A BATTLE IS UNDER WAY/.test(text), j(text.slice(0, 120)),
        `battle: ${b.foes.map(f => f.name).join(', ')} — ${b.log || ''}`);
      for (const f of b.foes) ok(`replay/${r}#${rec.step}`, 'the foe is named in the prompt',
        text.includes(f.name), j(text.slice(0, 160)), f.name);
    }
  }
  ok('replay', 'THERE WAS A RECORDED BATTLE TO CHECK AT ALL', battleSteps > 0,
    '0 battle steps in 13 runs', 'run-20260803-122026 fought one');
  console.log(`  ${battleSteps} recorded battle step(s) replayed through flattenPercept`);

  // (b) PUBLICATION INVARIANTS on the newest run. An unready frame must never have
  // reached the model — PT-20260803-005 is exactly that: four black frames handed over
  // as facts about the game, and a P1 blocker filed against a game that was fine.
  const latest = runs[runs.length - 1];
  const steps = new Map();
  for (const rec of readJsonl(join(dir, latest, 'run.jsonl'))) if ('ready' in rec) steps.set(rec.step, rec);
  const shown = new Set(readJsonl(join(dir, latest, 'observations.jsonl')).map(o => o.step));
  ok(`replay/${latest}`, 'the newest run has a readiness log to check', steps.size > 0,
    'no run.jsonl steps carrying `ready`', 'a run that recorded its own readiness');
  for (const [n, rec] of steps) {
    if (rec.ready && rec.meanL != null) ok(`replay/${latest}#${n}`, 'a frame called ready is not black',
      rec.meanL >= BLACK_L, `ready:true, mean luminance ${rec.meanL}`, `black (< ${BLACK_L})`);
    if (!rec.ready) {
      ok(`replay/${latest}#${n}`, 'a refusal says why', (rec.why || []).length > 0,
        'ready:false with no reason', 'the harness could not see, and must say so');
      ok(`replay/${latest}#${n}`, 'AN UNREADY FRAME WAS NOT SHOWN TO THE MODEL',
        !shown.has(n), 'the step is in observations.jsonl', `unready: ${(rec.why || []).join('; ')}`);
    }
  }
  console.log(`  ${steps.size} step(s) of ${latest} checked; ${shown.size} shown to the model`);
}

// ===================== §3 DOES THE FIXTURE STILL MATCH THE GAME =============
function runCensus() {
  console.log('§3 SELECTOR CENSUS (the fixture must not drift from the shipping UI)');
  const src = ['public/js/battle_turnbased.js', 'public/js/ui_kit.js', 'public/js/story_runtime.js',
    'public/js/menu.js', 'public/play3d.html']
    .map(f => existsSync(join(ROOT, f)) ? readFileSync(join(ROOT, f), 'utf8') : '').join('\n');
  ok('census', 'the shipping UI source was found to check against', src.length > 5000,
    `${src.length} bytes read`, 'battle_turnbased.js + ui_kit.js + story_runtime.js + menu.js + play3d.html');
  const classes = [...new Set((PERCEPT_JS.match(/\.(ebb|ebui|mn)-[a-z]+/g) || []))];
  const ids = ['story-obj', 'sgp', 'story-card'];
  // LOAD-BEARING: the percept has no second way to see these, so if a module renames
  // one the harness goes blind on that screen and every fixture here keeps passing.
  // The rest are alternates in a union selector (.ebui-choice sits beside li/.row) —
  // absent is untidy, not blind, so it warns.
  const LOADBEARING = new Set(['.ebb-root', '.ebb-cmds', '.ebb-cmd', '.ebb-sub', '.ebb-foe',
    '.ebb-ftag', '.ebb-prow', '.ebb-party', '.ebb-actor', '.ebb-mark',
    '.ebui-veil', '.ebui-title', '.ebui-body', '.ebui-banner',
    // The pause menu draws .mn-navrow and nothing else the percept can read; without
    // it an agent that presses Escape is handed an empty list (measured 2026-08-04).
    '.mn-navrow']);
  ok('census', 'the percept still queries a battle at all', classes.some(c => c.startsWith('.ebb-')),
    j(classes), 'a percept that can see .ebb-root');
  for (const c of classes) {
    if (LOADBEARING.has(c)) ok('census', `${c} still exists in the shipping UI`,
      src.includes(c.slice(1)), `the percept looks for ${c}`,
      'no module draws that class any more — the percept is querying a screen that moved');
    else warn('census', `${c} is queried by the percept but drawn by nothing`,
      src.includes(c.slice(1)), 'a vestigial alternate in a union selector; harmless, delete when convenient');
  }
  for (const i of ids) ok('census', `#${i} still exists in the shipping UI`,
    src.includes(i), `the percept looks for #${i}`, 'no module draws that id any more');
  // The fixtures must exercise every selector the percept relies on, or a screen the
  // adapter cannot see would still pass §1 by never appearing in it.
  const fixtures = STATES.map(s => s.html).join('') + BATTLE_HTML;
  const missed = [...LOADBEARING].filter(c => !fixtures.includes(c.slice(1)));
  ok('census', 'every load-bearing class appears in some fixture', missed.length === 0,
    `fixtures never exercise ${j(missed)}`, 'five screens covering the whole percept');
}

// ---------------------------------------------------------------------------
const t0 = Date.now();
console.log('percept_test — does the playtest harness see the game?\n');
await runDom();
runReplay();
runCensus();
const secs = ((Date.now() - t0) / 1000).toFixed(1);
console.log(`\n${fails ? 'FAILED' : 'PASS'}  ${checks - fails - known - warns}/${checks} checks in ${secs}s` +
  (known ? ` — ${known} KNOWN defect(s) printed above and NOT fixed here` : '') +
  (warns ? ` — ${warns} warning(s)` : ''));
if (fails) console.log('A failure here means the ADAPTER is wrong about the game, not that the game is broken.');
process.exit(fails ? 1 : 0);
