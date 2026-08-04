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
 *     the parts the HARNESS composed: the persona, the controls, the brief and the
 *     nudge, which agent.mjs names once in authoredParts() and hands back as
 *     `_authored`. They are NOT checked against the text the game drew or the
 *     agent's own recollection, because a player is allowed to know the word
 *     "square".
 *
 * `harnessText` IS REQUIRED, and null is a legal value meaning "the harness wrote
 * nothing in this prompt". It used to DEFAULT TO THE WHOLE PROMPT when it was null,
 * which quietly undid the distinction above for any run whose plan has no brief —
 * i.e. every `newgame` run, the only kind that starts at the beginning. Those died at
 * step 2 on the soft token the game itself had just spoken, while checkpoint runs
 * (which do carry a brief) passed, so the instrument could only be pointed at the
 * middle of the game. The HARD list is untouched: it still scans the entire prompt,
 * and it is the half that actually stops a leak.
 */
export function assertNoPrivileged(prompt, truth, harnessText) {
  if (harnessText === undefined) throw new Error(
    'FIREWALL: assertNoPrivileged needs its third argument. Pass the harness-authored ' +
    'text (agent.mjs sets it on every reply as `_authored`), or an explicit null to ' +
    'mean the harness wrote nothing. It must not be inferred: the old fallback used ' +
    'the whole prompt and turned every soft token into a false alarm on the game\'s ' +
    'own dialogue.');
  const whole = String(prompt || '').toLowerCase();
  const authored = String(harnessText || '').toLowerCase();
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
    /* A STEP IN WHICH THE BODY IS NOT ALLOWED TO MOVE IS NOT EVIDENCE THAT IT
     * CANNOT. This detector measures metres, and a battle, a conversation or a
     * full-screen card is exactly a window where zero metres is CORRECT play.
     * Such a step is DROPPED — it neither counts toward the window nor resets it —
     * so six genuinely motionless free-roaming steps still fire.
     *
     * Paid for on 2026-08-03, run-20260803-203813: a ten-step overworld battle
     * (fought and WON — "Duskpad is defeated!" at step 12, the Victory card at
     * 13-15, walking again at 16) tripped the six-step window at step 12, and the
     * interview it paid for produced PT-20260803-019, "Battle softlocks after
     * defeating the enemy", P0, against a battle that had already ended. The
     * detector was right that nothing moved and wrong about what that meant.
     *
     * This does NOT hide a real modal freeze: "UILOCK held with nothing drawn on
     * it" is a different question, asked by the frame gate's `frozen`, which files
     * its own blocker. Two different sentences about two different things. */
    if (truth.locked || percept.battle || percept.dialogue || percept.card) return null;
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
    spineScenes = null,
    // sceneKind(scene) -> 'town' | 'region' | 'interior' | null, out of scenegraph.json.
    // See the spine detector: an interior is a room, not a wrong turn.
    sceneKind = null } = cfg;
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
  // A NUDGE IS A CONTAINER, NOT AN AUTHOR. One of the two things that go in it is a
  // fixed harness sentence; the other is THE TEXT THE GAME JUST DREW, read back to the
  // agent. `nudgeAuthored` carries only the harness's own words, so the firewall's soft
  // check can tell them apart — without it, the read-back of "A waystone. Good — the
  // road's a real road, then." counted as the harness naming a camera, and killed the
  // run three steps in. Same lesson as the brief, one layer down.
  let nudge = null, nudgeAuthored = null;
  let finished = null, steps = 0, offSpine = 0, offSpineFiled = false, lastLeg = null;
  // Consecutive steps with nothing painted. Bounded so a blind harness stops loudly
  // instead of grinding a hundred black frames through a paid model.
  let unready = 0; const UNREADY_MAX = 6;
  // Consecutive steps frozen under a modal lock with nothing drawn. That is the
  // GAME's defect, not the harness's, so it is filed rather than swallowed.
  let frozenN = 0; const FROZEN_MAX = 5;
  // Consecutive steps inside an `interior` node, and whether anything in it ever
  // answered. Round 7 measured the cost of a room with nobody in it: 18 of 70 steps
  // in The Boatmen's Rest, talking to its own party. 12 is under that and well over
  // the 3-4 steps a shop visit or a look round costs.
  let roomSteps = 0, roomAnswered = false, emptyRoomFiled = false; const EMPTY_ROOM_MAX = 12;

  // The objective sentence QUOTES the game's own banner, so it is shown to the agent
  // but is NOT part of what the harness authored — see agent.mjs authoredParts().
  const brief = [plan.brief, plan.objective ? `Your current objective is: ${plan.objective}` : null]
    .filter(Boolean).join(' ') || null;
  const briefAuthored = plan.brief || null;
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
      why: obs.ready ? undefined : obs.why, frozen: obs.frozen || undefined,
      meanL: obs.meanL, waitedMs: obs.waitedMs,
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

    /* A GAME THAT TAKES CONTROL AND DRAWS NOTHING IS A BUG, AND IT IS THE GAME'S.
     * Distinct from the case above: the picture is up and measurable, the body is
     * frozen under a modal lock, and no dialogue, card or battle is on screen for
     * the player to answer. observe() has already waited its short budget. Filed
     * once, with the frames, so a human can see what "nothing" looked like. */
    if (obs.frozen) {
      frozenN++;
      log(`  (step ${step}: ${obs.frozen} — waited ${obs.waitedMs} ms, screen is up at ${obs.meanL} luminance)`);
      if (frozenN === FROZEN_MAX) {
        fileReport('blocker', {
          title: 'The game took control and never gave it back, with nothing on screen to answer',
          doing: 'I was playing normally when the game froze my character.',
          expected: 'Either something to read or answer, or my controls back.',
          happened: `Nothing I press does anything. There is a picture on screen but no dialogue box, ` +
            `no card and no menu — the game is holding me still and showing me nothing. ` +
            `This lasted ${FROZEN_MAX} turns.`,
        }, step, obs.percept, truth, lastFrames.slice(), 'freeze-detector', 'P1');
        finished = 'frozen'; log('\n== FROZEN: the game held control with nothing drawn. Stopping.'); break;
      }
      continue;
    }
    frozenN = 0;

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
    /* AN INTERIOR IS A ROOM, NOT A WRONG TURN. Eight of this detector's reports were
     * the same design question; the eighth (PT-20260803-029) fired because the agent
     * walked into a pub and left again six steps later. The rule "you left the set of
     * scenes holding an un-fired beat and stayed gone" is true and damning about a
     * region, and simply wrong about an optional interior entered by a door that is
     * still behind you. `kind` comes from the scenegraph, so this is the game's own
     * classification and not a name-suffix guess. What IS worth saying about that pub
     * is a different sentence, and the emptyRoom detector below says it. */
    const inInterior = !!(sceneKind && sceneKind(truth.scene) === 'interior');
    if (inInterior) {
      roomSteps++;
      // EVERY ui_kit SURFACE IS AN `.ebui-veil`, so the percept reports a shop, a pause
      // menu and a conversation in the same `dialogue` field — which is exactly the
      // question here: did anything at all open. `card` is the story-card, same test.
      const d = obs.percept.dialogue;
      if ((d && (d.text || d.choices)) || obs.percept.card) roomAnswered = true;
      if (roomSteps === EMPTY_ROOM_MAX && !roomAnswered && !emptyRoomFiled) {
        emptyRoomFiled = true;
        fileReport('bug', {
          title: `I spent ${roomSteps} turns inside ${truth.scene} and nothing in the room answered me`,
          doing: 'I went through a door the game offered me and tried to talk to everyone and everything inside.',
          expected: 'Somebody to talk to, something to buy, or something to do — a room the game lets me into should hold something.',
          happened: `${roomSteps} turns in this room and not one dialogue box, shop or menu opened. ` +
            `The only figures in here are the party I walked in with.`,
        }, step, obs.percept, truth, lastFrames.slice(), 'empty-room-detector', 'P1');
      }
    } else { roomSteps = 0; roomAnswered = false; }

    if (spineScenes && truth.scene) {
      const live = spineScenes(truth.beats || []);
      if (live && live.size && !live.has(truth.scene) && !inInterior) offSpine++; else offSpine = 0;
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
        // `_authored` is what agent.mjs actually wrote, not our guess at it.
        if (iv) { assertNoPrivileged(iv._prompt, truth, iv._authored);
          if (iv.notabug) log('  (interview: the agent says it is not really stuck — nothing filed)');
          else { if (lastLeg && lastLeg.from && lastLeg.target)
                   iv.probe = { kind: 'reach', from: lastLeg.from, to: lastLeg.target, scene: truth.scene };
                 fileReport(iv.kind, iv, step, obs.percept, truth, lastFrames.slice(), 'stuck-interview', iv.severity); } }
      } catch (e) { log('  interview failed: ' + e.message); if (/FIREWALL/.test(e.message)) throw e; }
      nudge = nudgeAuthored =
              'You appear to be stuck: you have not moved for a while and nothing has changed. ' +
              'Do something DIFFERENT — walk somewhere else, or go back the way you came.';
    }

    let intent;
    try {
      intent = await agent.decide({ screenshot: obs.screenshot, text: obs.text,
                                    history: history.slice(-8), brief, briefAuthored, nudge, nudgeAuthored });
      // THE ASSEMBLER SAYS WHAT IT WROTE. agent.mjs returns `_authored` — the persona,
      // the controls, the brief and the nudge, built from the same array the prompt is
      // — and everything else in the prompt is either drawn on screen or the agent's
      // own recollection. Passing `brief` here was close but not the same thing, and
      // passing nothing at all silently meant "scan everything" (see the firewall's
      // own note above).
      assertNoPrivileged(intent._prompt, truth, intent._authored);
    } catch (e) {
      if (/FIREWALL/.test(e.message)) throw e;
      log('  agent error: ' + e.message);
      intent = { see: '(error)', goal: 'recover', action: 'wait', ms: 700 };
    }
    nudge = nudgeAuthored = null;

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
          /* THREE REASONS A LEG DID NOT HAPPEN, AND ONLY ONE OF THEM IS ABOUT THE
           * GROUND. `unready` is the harness saying it could not measure — the page
           * was not painting, so the walk never started. Calling that "not ground you
           * can walk to" would hand the agent a fact about the world that the harness
           * never established, which is the same class of lie as an unready frame. */
          if (leg.reason === 'unready') {
            log(`  leg not run: the page was not painting — ${(leg.starvedWhy || []).join('; ')}`);
            parts.push('the game was still loading, so that walk never started');
          } else parts.push(leg.reason === 'modal'
            ? 'the game took over part-way (a scene or a conversation started)'
            : `[${wx.toFixed(2)},${wy.toFixed(2)}] is not ground you can walk to`);
          break;
        }
        parts.push(`[${wx.toFixed(2)},${wy.toFixed(2)}] ${leg.arrived ? 'reached' : `only closed ${leg.closed} m of ${leg.intended} m`}`);
        if (!leg.arrived && leg.intended >= 3 && leg.closed < 0.75) {
          /* A STARVED LEG IS NOT A BLOCKED PATH. If the executor's hard ceiling cut the
           * slide short, it never learned whether the world refuses — see walkLeg's note
           * and PT-20260803-010/011/012, three P1s filed off `bursts: 1` against ground
           * that is open in every direction. Say it out loud in the run log, because a
           * harness this slow is a finding about the machine, and carry on without a
           * ticket. Only `exhausted` — all five headings pushed, nothing moved — may file. */
          if (!leg.exhausted) {
            /* THREE OUTCOMES, THREE SENTENCES (2026-08-04). `noGain` used to print the
             * starvation line — "the headings were never all tried" — over a leg on which
             * every heading WAS tried and the body moved every round. On a healthy link
             * (Dellhollow, 164 ms/burst) that read as a slow machine and hid the actual
             * answer: walkable, but not toward the goal. Neither files a blocker. */
            log(leg.noGain
              ? `  leg not conclusive: NO GAIN after ${leg.bursts} burst(s) at ~${leg.msPerBurst} ms/burst ` +
                `— the body moved every round and never got closer. The headings WERE tried; ` +
                `the ground is walkable and the approach is not. No blocker filed.`
              : `  leg not conclusive: ${leg.starved ? 'STARVED' : 'gave up'} after ${leg.bursts} burst(s) ` +
                `at ~${leg.msPerBurst} ms/burst — no blocker filed (the headings were never all tried)` +
                // WHY it starved, measured while the condition was live. "Starved" with
                // a reason is a finding about the machine; without one it is a shrug.
                (leg.starvedWhy && leg.starvedWhy.length ? `\n      because: ${leg.starvedWhy.join('; ')}` : ''));
            break;
          }
          const cell = leg.target.map(v => Math.round(v / 3)).join(',');
          stallSeen.set(cell, (stallSeen.get(cell) || 0) + 1);
          if (stallSeen.get(cell) === 2) {
            const f2 = await adapter.observe('stall');
            fileReport('blocker', {
              title: `Walk blocked: the body closed ${leg.closed} m of an intended ${leg.intended} m, twice at the same place`,
              doing: `I tried to walk to a point on screen at [${wx.toFixed(2)}, ${wy.toFixed(2)}]; my goal was "${intent.goal || '(none stated)'}".`,
              expected: `To walk about ${leg.intended} m and arrive there.`,
              happened: `The character moved ${leg.travelled} m and stopped ${leg.remaining} m short — twice in this run. ` +
                `All five headings were pushed (${leg.bursts} bursts at ~${leg.msPerBurst} ms each) and none of them ` +
                'moved the body, so this is the world refusing rather than the harness running out of time. ' +
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
      // The label is ours; every line under it is the game's own dialogue.
      if (seen.length) { nudge = 'What you just read:\n' + seen.join('\n');
                         nudgeAuthored = 'What you just read:'; }
    } else if (intent.action === 'choose') {
      const c = await adapter.choose(intent.index || 0);
      detail = `chose ${intent.index || 0}` + (c && c.from >= 0 ? ` (cursor was on ${c.from})` : '');
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
