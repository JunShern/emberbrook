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

export function assertNoPrivileged(prompt, truth) {
  const hay = String(prompt || '').toLowerCase(); const bad = [];
  const tok = [];
  if (truth.scene) tok.push(truth.scene);
  if (truth.shot) tok.push(truth.shot);
  for (const p of truth.pos || []) tok.push(String(p));
  for (const b of truth.beats || []) tok.push(b);
  for (const f of truth.flags || []) if (f.indexOf('.') > 0) tok.push(f);
  for (const e of truth.exits || []) tok.push(e);
  for (const t of tok) {
    const s = String(t).toLowerCase();
    if (s.length < 5) continue;              // '1.5' is a duration, not a leak
    if (hay.includes(s)) bad.push(t);
  }
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
    stopBeat = null, stuckWindow = 6, port = 3000, log = console.log, noQueue = false } = cfg;
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
  let nudge = null, finished = null, steps = 0;

  const brief = [plan.brief, plan.objective ? `Your current objective is: ${plan.objective}` : null]
    .filter(Boolean).join(' ') || null;
  if (brief) log('  brief: ' + brief);

  function fileReport(kind, r, step, percept, truth, frames, source, severity) {
    if (reports.length >= maxReports) return null;
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
    const settled = await adapter.settle();
    const obs = await adapter.observe();
    const truth = await adapter.truth();
    if (obs.framePath) { lastFrames.push(obs.framePath); if (lastFrames.length > 3) lastFrames.shift(); }
    for (const b of truth.beats || []) if (!beatsSeen.has(b)) { beatsSeen.add(b); log(`  [beat] ${b}`); }
    appendFileSync(jsonl, JSON.stringify({ step, percept: obs.percept, settled,
      truth: { ...truth, save: undefined }, frame: Q.relative(obs.framePath) }) + '\n');

    if (stopBeat && (truth.beats || []).includes(stopBeat)) {
      finished = stopBeat; log(`\n== FINISH LINE: ${stopBeat} fired at step ${step}`); break;
    }
    // Frozen with a modal up and nothing drawn: not a decision the agent can make,
    // and a real defect if it persists. settle() already waited it out.
    if (!settled) log(`  (step ${step}: the game held a modal lock for 10 s with nothing on screen)`);

    const s = stuck.push(step, truth, obs.percept);
    if (s) {
      log(`  ** STUCK: ${s.moved} m over ${s.steps} steps (since step ${s.since}). Interviewing.`);
      try {
        const frames = lastFrames.map(p => ({ mime: 'image/jpeg', data: readFileSync(p).toString('base64') }));
        const iv = await agent.interview({ screenshots: frames, text: obs.text, history: history.slice(-10) });
        if (iv) { assertNoPrivileged(iv._prompt, truth);
          if (iv.notabug) log('  (interview: the agent says it is not really stuck — nothing filed)');
          else fileReport(iv.kind, iv, step, obs.percept, truth, lastFrames.slice(), 'stuck-interview', iv.severity); }
      } catch (e) { log('  interview failed: ' + e.message); if (/FIREWALL/.test(e.message)) throw e; }
      nudge = 'You appear to be stuck: you have not moved for a while and nothing has changed. ' +
              'Do something DIFFERENT — walk somewhere else, or go back the way you came.';
    }

    let intent;
    try {
      intent = await agent.decide({ screenshot: obs.screenshot, text: obs.text, history: history.slice(-8), brief, nudge });
      assertNoPrivileged(intent._prompt, truth);
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
        legs.push({ step, ...leg }); outcome = leg;
        if (!leg.ok) { parts.push(`[${wx.toFixed(2)},${wy.toFixed(2)}] is not ground you can walk to`); break; }
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
      unprojectable: legs.length - okLegs.length,
      medianClosedFrac: med(okLegs.map(l => l.closedFrac)) },
    _legs: legs,
  };
}
