/* episode.mjs — LAYER 3: THE RUNNER. observe -> decide -> act -> observe.
 *
 * Mostly game-agnostic: it talks to an ADAPTER (layer 2) through a small contract
 * and to an AGENT (layer 1) through a smaller one. What it owns is the loop, the
 * budget, the firewall, stuck detection, the golden-set log, and filing reports.
 *
 * ============================== THE FIREWALL ===============================
 * The agent may only see what a player sees. That is asserted, not promised:
 * before every model call, assertNoPrivileged() re-derives the forbidden tokens
 * FROM THE LIVE TRUTH — the scene id, the shot id, the body's coordinates, every
 * set flag, every fired beat, every live exit id — and throws if any of them
 * appears in the assembled prompt. A leak FAILS THE RUN rather than quietly
 * producing a better score, because a playtester that can read the scene graph is
 * just playthrough_test with a bigger bill.
 *
 * ========================= THE GOLDEN-SET LOG ==============================
 * Every (observation, intent) pair is written to observations.jsonl with the frame
 * beside it and the OUTCOME the adapter measured. That file is the benchmark
 * substrate: tools/playtest_bench.mjs replays those observations through other
 * models WITHOUT RUNNING THE GAME, which turns a model comparison from hours of
 * gameplay into minutes of API calls.
 *
 * ITS LIMIT, stated because it is easy to over-trust: FULL EPISODES DIVERGE. A
 * model that decides differently at step 12 sees a different step 13, so agreeing
 * with a recorded good decision is necessary, not sufficient. Single-step replay is
 * a FILTER — cheap scoring to shortlist candidates — and a full episode is the
 * verdict. Two stages, in that order.
 *
 * ========================= STUCK DETECTION =================================
 * A HUMAN GIVES UP, and the sentence they say when they do is the bug report. The
 * detector is HARNESS-SIDE and uses privileged state ON PURPOSE: "did the body
 * actually move" is a question about the world, not the picture, and asking the
 * picture would let a camera cut look like progress. It decides only WHEN to
 * interview the agent; none of it reaches the agent's context.
 *
 * ================== FAILING A WAYPOINT IS A FREE BUG SIGNAL ================
 * The adapter reports intended vs closed metres for every leg. Intending 3 m or
 * more and closing under 0.75 m of it, TWICE at the same place, files a blocker
 * without the model ever having to notice it was blocked. This is the cheapest and
 * highest-yield detector in the instrument.
 */
import { readFileSync, appendFileSync, writeFileSync, mkdirSync } from 'fs';
import { execFileSync } from 'child_process';
import { join, dirname } from 'path';
import * as Q from './queue.mjs';

const ROOT = join(dirname(new URL(import.meta.url).pathname), '../..');
const sleep = ms => new Promise(r => setTimeout(r, ms));
export const HEAD_SHA = (() => {
  try { return execFileSync('git', ['-C', ROOT, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); } catch (e) { return null; }
})();

/* THE FIREWALL, and the distinction it has to make was paid for on the first real
 * episode. It failed the run on the token "waystone" — which is a camera id AND a
 * word the game's own dialogue says out loud ("A waystone. Good — the road's a real
 * road, then."). A player reads that. A firewall that cannot tell a leak from a
 * noun is a firewall that gets switched off, so:
 *
 *   HARD tokens can NEVER legitimately appear on a player's screen — a scene id
 *     (emb-cine), a flag or beat id (story.ch1.waystone), an edge id
 *     (emb-cine>ow-valley@emberbrook-gate), a body coordinate (-47.92). These are
 *     checked against the WHOLE prompt, and one of them anywhere fails the run.
 *     This is also the backstop for the dev HUD: if hiding `#h` ever stops working,
 *     "pos(52.0,-0.6,28.0)" lands in the drawn text and this catches it.
 *   SOFT tokens are ordinary English that happens to also be an id — the camera
 *     names (square, waystone, pondlane, gatefield). They are checked only against
 *     the parts the HARNESS composed: the persona and the brief. They are NOT
 *     checked against the text the game drew or the agent's own recollection,
 *     because a player is allowed to know the word "square".
 */
export function assertNoPrivileged(prompt, truth, harnessText) {
  const whole = String(prompt || '').toLowerCase();
  const authored = String(harnessText == null ? prompt : harnessText).toLowerCase();
  const bad = [];
  const hard = [];
  if (truth.scene) hard.push(truth.scene);
  for (const b of truth.beats || []) if (b.indexOf('.') > 0) hard.push(b);
  for (const f of truth.flags || []) if (f.indexOf('.') > 0) hard.push(f);
  for (const e of truth.exits || []) hard.push(e);
  for (const p of truth.pos || []) { const s = String(p); if (s.includes('.') && s.length >= 4) hard.push(s); }
  for (const t of hard) { const s = String(t).toLowerCase();
    if (s.length >= 5 && whole.includes(s)) bad.push(t + ' (hard)'); }
  const soft = truth.shot ? [truth.shot] : [];
  for (const t of soft) { const s = String(t).toLowerCase();
    if (s.length >= 4 && authored.includes(s)) bad.push(t + ' (soft, in harness-authored text)'); }
  if (bad.length) throw new Error(
    'FIREWALL: the agent prompt contains privileged state it must never see: ' + JSON.stringify(bad) +
    '\n  This is a build error in the harness, not a game bug. The agent may only be given the ' +
    'screenshot and the text the game DRAWS on it.');
}

class Stuck {
  constructor(n) { this.n = n; this.buf = []; this.lastFire = -99; }
  push(step, truth, percept) {
    this.buf.push({ step, pos: truth.pos || [0, 0, 0], scene: truth.scene, shot: truth.shot,
      obj: percept.objective || '', dlg: (percept.dialogue && percept.dialogue.text) || '',
      beats: (truth.beats || []).length });
    if (this.buf.length > this.n) this.buf.shift();
    if (this.buf.length < this.n || step - this.lastFire < this.n * 2) return null;
    const a = this.buf, p0 = a[0].pos;
    const moved = Math.max(...a.map(x => Math.hypot(x.pos[0] - p0[0], x.pos[2] - p0[2])));
    const same = k => a.every(x => x[k] === a[0][k]);
    const talking = new Set(a.map(x => x.dlg).filter(Boolean)).size > 1;
    if (moved < 1.5 && same('scene') && same('shot') && same('obj') && same('beats') && !talking)
      { this.lastFire = step; return { moved: +moved.toFixed(2), steps: this.n, since: a[0].step }; }
    return null;
  }
}

/**
 * run({adapter, agent, plan, runDir, runId, ...}) — one episode.
 * plan: {kind, scene, cam, pos, patch|save, brief, objective}
 */
export async function run(cfg) {
  const { adapter, agent, plan, runDir, runId, maxSteps = 120, maxReports = 8,
    stopBeat = null, stuckWindow = 6, port = 3000, log = console.log, noQueue = false,
    // spineScenes(firedBeats) -> Set of scenes where an un-fired beat still lives.
    // Supplied by the CLI, which owns story.json; the runner only needs the answer.
    spineScenes = null } = cfg;
  mkdirSync(runDir, { recursive: true });
  const jsonl = join(runDir, 'run.jsonl');
  const obsLog = join(runDir, 'observations.jsonl');

  const stuck = new Stuck(stuckWindow);
  const history = [];
  const beatsSeen = new Set();
  const legs = [];
  const reports = [];
  const stallSeen = new Map();
  const lastFrames = [];
  let nudge = null, finished = null, steps = 0, offSpine = 0, offSpineFiled = false, lastLeg = null;
  // Consecutive steps with nothing painted. Bounded so a blind harness stops loudly
  // instead of grinding a hundred black frames through a paid model.
  let unready = 0; const UNREADY_MAX = 6;

  const brief = [plan.brief, plan.objective ? `Your current objective is: ${plan.objective}` : null]
    .filter(Boolean).join(' ') || null;
  if (brief) log('  brief: ' + brief);

  function fileReport(kind, r, step, percept, truth, frames, source, severity) {
    if (reports.length >= maxReports) return null;
    // AN EMPTY REPORT IS NOISE IN THE QUEUE, and it costs a human the same look as
    // a real one. Measured: a `giveup` reply that carried no report body filed
    // "untitled" with three nulls at P0, straight to the top of the list.
    if (!r || (!r.title && !r.doing && !r.expected && !r.happened)) {
      log(`  (a ${source} report arrived with nothing in it — not filed)`);
      return null;
    }
    const e = {
      run: runId, step, source, kind: kind || 'confusion', severity: severity || r.severity || 'P1',
      title: String(r.title || 'untitled').slice(0, 160),
      doing: r.doing || null, expected: r.expected || null, happened: r.happened || null,
      probe: r.probe || null,
      frames: frames.filter(Boolean).map(Q.relative),
      onscreen: { objective: percept.objective, prompts: percept.prompts,
        dialogue: percept.dialogue ? (percept.dialogue.speaker || '') + ': ' + (percept.dialogue.text || '') : null,
        card: percept.card ? percept.card.title : null },
      // GROUND TRUTH, for the human triaging this and for the instruments. The
      // agent never saw any of it; recording it here is the whole point.
      truth: { scene: truth.scene, shot: truth.shot, pos: truth.pos, beats: truth.beats,
        flags: truth.flags, exits: truth.exits },
      // THE REPRO SAVE, stamped. A stale repro must be DETECTABLE, not silently wrong.
      repro: { sha: HEAD_SHA, capturedAt: new Date().toISOString(), save: truth.save || null,
        how: `node tools/llm_playtester.mjs --port=${port} --repro=<this id>` },
    };
    const stored = noQueue ? { ...e, id: 'DRY-' + (reports.length + 1) } : Q.append(e);
    reports.push(stored);
    log(`  >> REPORT ${stored.id} [${stored.kind}/${stored.severity}] ${stored.title}`);
    return stored;
  }

  for (let step = 1; step <= maxSteps; step++) {
    steps = step;
    // observe() WAITS for a painted frame and tells us whether it got one. It used
    // to photograph whatever was there when its own 10 s timer expired, which on
    // 2026-08-03 handed the agent four black transition veils and earned two P1
    // blockers against the harness's own timeout (PT-20260803-005/006). The game was
    // rendering the whole time.
    const obs = await adapter.observe();
    const truth = await adapter.truth();
    if (obs.ready && obs.framePath) { lastFrames.push(obs.framePath); if (lastFrames.length > 3) lastFrames.shift(); }
    for (const b of truth.beats || []) if (!beatsSeen.has(b)) { beatsSeen.add(b); log(`  [beat] ${b}`); }
    appendFileSync(jsonl, JSON.stringify({ step, percept: obs.percept, ready: obs.ready,
      why: obs.ready ? undefined : obs.why, meanL: obs.meanL, waitedMs: obs.waitedMs,
      truth: { ...truth, save: undefined }, frame: Q.relative(obs.framePath) }) + '\n');

    if (stopBeat && (truth.beats || []).includes(stopBeat)) {
      finished = stopBeat; log(`\n== FINISH LINE: ${stopBeat} fired at step ${step}`); break;
    }

    /* NOTHING ON SCREEN IS THE HARNESS'S PROBLEM, NOT THE AGENT'S.
     * If there is no painted frame, no model call is made, no report can be filed
     * and no black picture enters anybody's context. Persist and the run STOPS and
     * says the instrument went blind — which is a sentence about this tool, and must
     * never be dressed up as a sentence about the game. */
    if (!obs.ready) {
      unready++;
      log(`  (step ${step}: NO PLAYABLE FRAME after ${obs.waitedMs} ms — ${obs.why.join('; ')}` +
          `${obs.meanL != null ? `; mean luminance ${obs.meanL}` : ''}. Nothing was shown to the agent.)`);
      if (unready >= UNREADY_MAX) {
        finished = 'harness-blind';
        log(`\n== THE HARNESS COULD NOT SEE. ${UNREADY_MAX} consecutive steps with no painted frame.\n` +
            `   ${obs.why.join('; ')}\n` +
            `   This is an INSTRUMENT FAULT. No bug was filed against the game, on purpose.`);
        break;
      }
      await sleep(1000);
      continue;
    }
    unready = 0;

    /* THE SPINE DETECTOR. Found on the second real episode, and it is the same
     * shape as the walk-executor's free signal: cheap, harness-side, and it does
     * not need the model to be articulate.
     *
     * The agent read the opening narration by pressing E, and the very next frame
     * offered "Leave Emberbrook? [E]" on the tile it was standing on. It pressed
     * the button the game had just spent three lines teaching it to press, and was
     * put in the overworld with "Follow the road north" still on the HUD and
     * nothing in that scene able to advance the chapter.
     *
     * A player cannot see that they have left the story; the harness can, because
     * it knows which scenes still hold an un-fired beat. Leaving that set and
     * staying gone is a defect whether the player noticed or not. Filed ONCE. */
    if (spineScenes && truth.scene) {
      const live = spineScenes(truth.beats || []);
      if (live && live.size && !live.has(truth.scene)) offSpine++; else offSpine = 0;
      if (offSpine === 3 && !offSpineFiled) {
        offSpineFiled = true;
        fileReport('bug', {
          title: 'The player can leave the chapter on its first frame, and the objective follows them out',
          doing: 'I read the opening narration by pressing the action button, then used the only prompt on screen.',
          expected: 'To carry on with the objective the game was showing me.',
          happened: `I ended up somewhere with no way to advance the story, and the objective on screen ` +
            `("${obs.percept.objective || 'none'}") still refers to where I was. Nothing here can continue the chapter.`,
        }, step, obs.percept, truth, lastFrames.slice(), 'spine-detector', 'P1');
      }
    }

    const s = stuck.push(step, truth, obs.percept);
    if (s) {
      log(`  ** STUCK: ${s.moved} m over ${s.steps} steps (since step ${s.since}). Interviewing.`);
      try {
        const frames = lastFrames.map(p => ({ mime: 'image/jpeg', data: readFileSync(p).toString('base64') }));
        const iv = await agent.interview({ screenshots: frames, text: obs.text, history: history.slice(-10) });
        if (iv) { assertNoPrivileged(iv._prompt, truth, brief);
          if (iv.notabug) log('  (interview: the agent says it is not really stuck — nothing filed)');
          else { if (lastLeg && lastLeg.from && lastLeg.target)
                   iv.probe = { kind: 'reach', from: lastLeg.from, to: lastLeg.target, scene: truth.scene };
                 fileReport(iv.kind, iv, step, obs.percept, truth, lastFrames.slice(), 'stuck-interview', iv.severity); } }
      } catch (e) { log('  interview failed: ' + e.message); if (/FIREWALL/.test(e.message)) throw e; }
      nudge = 'You appear to be stuck: you have not moved for a while and nothing has changed. ' +
              'Do something DIFFERENT — walk somewhere else, or go back the way you came.';
    }

    let intent;
    try {
      intent = await agent.decide({ screenshot: obs.screenshot, text: obs.text, history: history.slice(-8), brief, nudge });
      // `brief` is the only text in this prompt the HARNESS wrote; the persona is a
      // reviewed constant in the adapter, and everything else is either drawn on
      // screen or the agent's own recollection.
      assertNoPrivileged(intent._prompt, truth, brief);
    } catch (e) {
      if (/FIREWALL/.test(e.message)) throw e;
      log('  agent error: ' + e.message);
      intent = { see: '(error)', goal: 'recover', action: 'wait', ms: 700 };
    }
    nudge = null;

    // ---- act ---------------------------------------------------------------
    let detail = '', outcome = null;
    if (intent.action === 'goto') {
      const parts = [];
      for (const [wx, wy] of intent.waypoints) {
        const leg = await adapter.walkLeg(wx, wy);
        legs.push({ step, ...leg });
        // THE FIRST LEG IS THE ONE THE LABEL IS ABOUT. The golden set scores a
        // model on waypoints[0]; recording the LAST leg's outcome next to it made
        // every multi-waypoint row lie about which decision succeeded.
        if (outcome === null) outcome = leg;
        if (leg.from && leg.target) lastLeg = leg;
        if (!leg.ok) {
          parts.push(leg.reason === 'modal'
            ? 'the game took over part-way (a scene or a conversation started)'
            : `[${wx.toFixed(2)},${wy.toFixed(2)}] is not ground you can walk to`);
          break;
        }
        parts.push(`[${wx.toFixed(2)},${wy.toFixed(2)}] ${leg.arrived ? 'reached' : `only closed ${leg.closed} m of ${leg.intended} m`}`);
        if (!leg.arrived && leg.intended >= 3 && leg.closed < 0.75) {
          const cell = leg.target.map(v => Math.round(v / 3)).join(',');
          stallSeen.set(cell, (stallSeen.get(cell) || 0) + 1);
          if (stallSeen.get(cell) === 2) {
            const f2 = await adapter.observe('stall');
            fileReport('blocker', {
              title: `Walk blocked: the body closed ${leg.closed} m of an intended ${leg.intended} m, twice at the same place`,
              doing: `I tried to walk to a point on screen at [${wx.toFixed(2)}, ${wy.toFixed(2)}]; my goal was "${intent.goal || '(none stated)'}".`,
              expected: `To walk about ${leg.intended} m and arrive there.`,
              happened: `The character moved ${leg.travelled} m and stopped ${leg.remaining} m short — twice in this run. ` +
                'Something is in the way, or that ground is not connected to where I was standing.',
              // THE CLAIM, IN THE FORM AN INSTRUMENT CAN MEASURE. Triage runs the
              // reachability probe over exactly this pair rather than re-deriving
              // it from prose — a triage that has to guess what was claimed is
              // measuring its own guess.
              probe: { kind: 'reach', from: leg.from, to: leg.target, scene: truth.scene },
            }, step, obs.percept, truth, [obs.framePath, f2.framePath], 'walk-executor', 'P1');
          }
          break;                             // do not grind the rest of the route into a wall
        }
        if (!leg.arrived) break;
      }
      detail = parts.join('; ');
    } else if (intent.action === 'interact') {
      await adapter.press('e');
    } else if (intent.action === 'advance') {
      const seen = await adapter.readThrough();
      detail = seen.length ? `read ${seen.length} line(s)` : 'nothing to read';
      outcome = { lines: seen.length };
      if (seen.length) nudge = 'What you just read:\n' + seen.join('\n');
    } else if (intent.action === 'choose') {
      await adapter.menuDown(intent.index || 0); await adapter.press('e');
      detail = 'chose ' + (intent.index || 0);
    } else if (intent.action === 'report' || intent.action === 'giveup') {
      // Hand the last walk's from/to along. When the complaint is "I cannot get
      // there", triage can then measure THAT pair instead of parsing prose for a
      // destination it will only guess at.
      if (intent.report && lastLeg && lastLeg.from && lastLeg.target)
        intent.report.probe = { kind: 'reach', from: lastLeg.from, to: lastLeg.target, scene: truth.scene };
      if (intent.report)
        fileReport(intent.report.kind, intent.report, step, obs.percept, truth, lastFrames.slice(), 'agent',
          intent.action === 'giveup' ? 'P0' : intent.report.severity);
      if (intent.action === 'giveup') { finished = 'gaveup'; log('\n== THE PLAYER GAVE UP'); break; }
    } else {
      await sleep(intent.ms || 500);
    }

    // THE GOLDEN SET. One line per decision: what it saw, what it chose, what
    // happened. tools/playtest_bench.mjs replays these through other models.
    appendFileSync(obsLog, JSON.stringify({
      step, frame: Q.relative(obs.framePath), text: obs.text, brief,
      history: history.slice(-8),
      intent: { ...intent, _prompt: undefined }, outcome,
    }) + '\n');

    log(`  ${String(step).padStart(3)} ${intent.action.padEnd(9)} goal="${(intent.goal || '').slice(0, 50)}"${detail ? '  ' + detail.slice(0, 90) : ''}`);
    history.push(`step ${step}: I saw "${(intent.see || '').slice(0, 80)}"; I wanted to "${(intent.goal || '').slice(0, 60)}"; ` +
      `I did ${intent.action}${detail ? ' — ' + detail.slice(0, 110) : ''}.`);
    if (history.length > 12) history.shift();
  }

  const endTruth = await adapter.truth();
  const okLegs = legs.filter(l => l.ok);
  const med = (a) => { const s = a.slice().sort((x, y) => x - y); return s.length ? s[s.length >> 1] : null; };
  return {
    steps, finished, beatsFired: [...beatsSeen], reports,
    endTruth: { ...endTruth, save: undefined },
    legs: { n: legs.length, arrived: legs.filter(l => l.arrived).length,
      offNetwork: okLegs.filter(l => !l.onNetwork).length,
      unprojectable: legs.filter(l => !l.ok && l.reason === 'unprojection').length,
      interrupted: legs.filter(l => !l.ok && l.reason === 'modal').length,
      medianClosedFrac: med(okLegs.map(l => l.closedFrac)) },
    _legs: legs,
  };
}
