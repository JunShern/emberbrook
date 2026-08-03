#!/usr/bin/env node
/* llm_playtester.mjs — AN LLM THAT PLAYS THE GAME THE WAY A PERSON HAS TO.
 *
 *   node tools/llm_playtester.mjs --port=3000                    a Chapter One run
 *   node tools/llm_playtester.mjs --port=3000 --agent=stub       NO LLM: smoke test
 *   node tools/llm_playtester.mjs --checkpoints                  list them (no browser)
 *   node tools/llm_playtester.mjs --port=3000 --from=ch1.pact    drop in mid-chapter
 *   node tools/llm_playtester.mjs --port=3000 --repro=PT-...-003 replay a filed bug
 *   node tools/llm_playtester.mjs --port=3000 --player-model=gemini:gemini-3.5-flash
 *   node tools/llm_playtester.mjs --port=3000 --head             watch it play
 *
 * WHY THIS EXISTS (2026-08-02, the evening the user played the build).
 * They found SIX real defects in one sitting — blocked at the Old Gate, no Lake
 * introduction, no followers, a flat hush, neutral-faced dialogue, mis-scaled
 * cut-ins. FIVE GREEN GATE SUITES HAD CAUGHT NONE OF THEM. Every gate this repo
 * owns tests MACHINERY: seam_test the camera grammar, dialogue_test the cast,
 * story_test the flag ledger, playthrough_test the spine. None of them tests BEING
 * A PLAYER, and playthrough_test is blind to this class BY CONSTRUCTION: it
 * teleports with SIM.tp() and calls Npc.talk('poppy') BY ID, so it never has to
 * FIND anybody or WALK anywhere. It fired `ch1.see.poppy` on a commit where Poppy
 * was 100% behind her own stall canopy.
 *
 * ============================ THE ONE CONSTRAINT ============================
 * THE AGENT MAY ONLY DO WHAT A HUMAN CAN DO. Give it a privileged surface and it
 * becomes another machinery test.
 *
 *   INTENT is the model's:          "walk to that stall", "talk to that person".
 *   MOTOR CONTROL is the harness's: hold W, correct the heading, notice the stall.
 *   ...and the motor control still presses REAL KEYS. A waypoint is the DECISION;
 *   the walking is a human's. Executing a waypoint with SIM.tp() would rebuild the
 *   blind test this replaces.
 *
 *   MOVEMENT     real trusted key events over CDP Input.dispatchKeyEvent — the path
 *                a person drives (play3d.html:766 reads keys[e.key]; ui_kit.js:458
 *                takes the same events in capture phase for menus).
 *   INTERACTION  press `E` when the game shows a prompt. NEVER Npc.talk(id), NEVER
 *                Story.force, NEVER Dialogue.key().
 *   PERCEPTION   a SCREENSHOT plus the text the game DRAWS ON SCREEN (#story-obj,
 *                #story-card, #sgp, .ebui-banner, .ebui-panel). NEVER the scene
 *                graph, NEVER an NPC coordinate, NEVER GS flags, NEVER SIM.pos().
 *
 * The separation is STRUCTURAL and it is ASSERTED:
 *   - the adapter's PERCEPT_JS touches `document` and nothing else;
 *   - TRUTH_JS (SIM/GS) is the HARNESS's alone — stuck detection, the run log, the
 *     repro save, triage anchors;
 *   - the agent's decide() is handed an observation, never a truth object;
 *   - THE FIREWALL: episode.mjs re-derives forbidden tokens FROM the live truth
 *     (scene id, shot id, coordinates, every flag, beat and live exit) and THROWS
 *     if any appears in the assembled prompt. A leak fails the run instead of
 *     quietly producing a better score.
 *   - THE DEV HUD IS HIDDEN. play3d draws `#h` with the live scene, shot and
 *     pos(x,y,z) in the corner (play3d.html:1702). A shipping build would not, and
 *     a screenshot containing it hands the agent the exact numbers this instrument
 *     exists to withhold. Hiding it is the ONLY change the harness makes to the
 *     page, and it REMOVES information.
 *
 * ============================== THE THREE LAYERS ============================
 * User ruling 2026-08-03: the LLM side must be decoupled from this game, and the
 * model must be swappable for benchmarking. So:
 *
 *   tools/playtest/models.mjs    THE MODEL SEAM. Provider-agnostic; Gemini
 *                                implemented. `--player-model=gemini:<id>` swaps it
 *                                without touching anything else. Aliases ending in
 *                                `latest` are REFUSED: a moving model silently
 *                                decouples every recorded number from every other.
 *   tools/playtest/agent.mjs     LAYER 1, GAME-AGNOSTIC. In: a screenshot, the text
 *                                on it, a short history. Out: an intent. It knows
 *                                nothing about Emberbrook, three.js, walk networks,
 *                                beats or cameras.
 *   tools/playtest/adapter_emberbrook.mjs
 *                                LAYER 2, ALL THE COUPLING, deliberately thick:
 *                                un-projection through the live camera, keyboard
 *                                dispatch, arrival/stall detection, on-screen text,
 *                                checkpoint construction from the save schema.
 *   tools/playtest/episode.mjs   LAYER 3, the loop: observe -> decide -> act, the
 *                                firewall, stuck detection, the golden-set log,
 *                                report filing.
 *   tools/playtest/queue.mjs     the durable report queue.
 *   tools/playtest_triage.mjs    MEASURES the claims and renders the page.
 *   tools/playtest_bench.mjs     scores models on RECORDED observations, no game.
 *
 * ONE ADAPTER EXISTS AND THAT IS ON PURPOSE. A general plugin system for one game
 * is how a week disappears; only the model is pluggable, because only the model was
 * asked for.
 *
 * ====================== THE LOOP, AND WHY IT IS WAYPOINTS ===================
 * screenshot -> the agent names WHERE ON THE PICTURE to go (or presses a button) ->
 * the harness walks there with real keys -> screenshot -> repeat. Per-frame input
 * would be tens of thousands of model calls for one playthrough; waypoints make it
 * hundreds. The coordinate convention is nav_eval.mjs's, on purpose: x is 0 at the
 * left edge and 1 at the right, y is 0 at the top and 1 at the bottom.
 *
 * ============= FAILING TO REACH A WAYPOINT IS A FREE BUG SIGNAL =============
 * Every leg reports DISTANCE INTENDED vs DISTANCE CLOSED. "The agent asked for 9 m
 * and got 0.3 m" is a blocked path captured automatically — the model never has to
 * notice it was blocked or be articulate about it. Twice at the same place files a
 * blocker, which triage then measures with the reachability probe. Highest-yield
 * detector in the instrument, and it costs nothing per step.
 *
 * =========================== STUCK DETECTION ================================
 * A HUMAN GIVES UP, and the sentence they say when they do is the bug report. The
 * harness watches position, objective, dialogue and camera over a window of steps;
 * when nothing has moved it INTERVIEWS the agent on its own last frames. "I was
 * told to speak to Poppy and Mara. I have walked around the square twice and I
 * cannot see anyone at a stall" is the report, and it is exactly the sentence no
 * gate in this repo can produce.
 *
 * ============================== CHECKPOINTS =================================
 * THE SAVE SYSTEM IS THE CHECKPOINT SYSTEM, and loading a save is something a human
 * does. THE BOUNDARY IS EXPLICIT: SETUP may write the save and use the resume URL;
 * GAMEPLAY is keyboard only.
 *   DERIVED   `--checkpoints` / `--from=<beat>` builds state FROM story.json AT RUN
 *             TIME: every beat declares its scene, cam, `at` and the flags it sets,
 *             so "just before beat N" is the union of beats 1..N-1. ~24 checkpoints
 *             free, and none can rot because nothing is stored. The BRIEF is derived
 *             the same way — the last `objective` an earlier beat set, i.e. the line
 *             the game itself would be drawing. docs/qa/playtest/briefs.json may add
 *             a sentence per beat; a brief naming a beat story.json no longer has is
 *             WARNED about, so a stale instruction is loud rather than silent.
 *   CAPTURED  every report carries a REPRO SAVE — the exact blob at the moment of
 *             the bug — STAMPED WITH THE COMMIT SHA. `--repro=<id>` loads it and
 *             says so when HEAD has moved. A bug report that ships with a loadable
 *             save is worth ten that do not.
 *
 * ============================== THE QUEUE ===================================
 * docs/qa/playtest/queue.json, rendered by tools/playtest_triage.mjs to
 * docs/qa/playtest/index.html and docs/qa/playtest-queue.md. Every entry carries a
 * VERIFICATION STATUS and starts UNVERIFIED.
 *
 * *** AN UNVERIFIED COMPLAINT IS A LEAD, NEVER A TICKET. *** This repo has a
 * documented confabulation scar (the pink plank) and a ratified workflow: a judge
 * finds a flaw -> MEASURE the claim on an instrument -> only then build. Triage is
 * that step and it is not optional: a "cannot find X" claim auto-runs
 * findability_test for X; a "cannot get there" claim auto-runs the reachability
 * probe from where the body actually was.
 *
 * ======================= WHAT THIS CANNOT DO ================================
 * IT IS A BUG-FINDER, NOT A CRITIC. Do not trust it for taste.
 *  - Of the user's six findings it would plausibly have caught the OLD GATE BLOCK
 *    (it walks into a sealed edge and the stall detector files it) and possibly the
 *    MISSING LAKE SEGMENT (an objective naming a person it never meets). It would
 *    NOT have caught "the hush is less impactful than the 2D prototype" — that
 *    compares against something it never saw — nor "Vesper's expressions are flat",
 *    which needs an aesthetic bar it has no way to hold.
 *  - THE PERCEPTION ASYMMETRY IS REAL AND IT BIASES THE OUTPUT. A person gets
 *    motion, parallax, a moving camera and the ability to lean in. The agent gets
 *    ONE still 1280x720 JPEG per step of a night-graded pre-rendered plate. It is
 *    WORSE at seeing than a human, so it WILL file "I can't find it" reports a
 *    person would not. The bias runs in the direction we care about — a false
 *    "I cannot see them" is cheap, a missed one cost us Chapter One — but it is why
 *    triage is mandatory and why REFUTED is reported as prominently as VERIFIED.
 *  - It cannot hear. Nothing here measures audio (?nomusic=1 is the standing rule:
 *    an agent must never be audible in somebody's room).
 *  - Headless rAF runs at ~118 Hz here, not 60, so the body walks about twice as
 *    fast as it does for a person. The executor is a CLOSED LOOP — metres closed,
 *    never seconds held — so this changes pacing, not verdicts. An overshoot is a
 *    harness artefact, not a game bug.
 *
 * ================================= V1 SCOPE =================================
 * NEW GAME through CHAPTER ONE in emb-cine. Chapter One is the part a human bounced
 * off. See COVERING CHAPTER TWO at the bottom of this file.
 */
import { writeFileSync, mkdirSync, readdirSync, unlinkSync, readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { makeModel, Usage } from './playtest/models.mjs';
import { makeAgent } from './playtest/agent.mjs';
import { makeAdapter, checkpointsFromStory, PERSONA } from './playtest/adapter_emberbrook.mjs';
import { run as runEpisode, HEAD_SHA } from './playtest/episode.mjs';
import * as Q from './playtest/queue.mjs';

const ROOT = join(dirname(new URL(import.meta.url).pathname), '..');
const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const has = (k) => argv.includes('--' + k);

const PORT = parseInt(arg('port', '3000'), 10);
const MAX_STEPS = parseInt(arg('steps', '120'), 10);
const MAX_REPORTS = parseInt(arg('max-reports', '8'), 10);
const STOP_BEAT = arg('stop-beat', 'ch1.sendoff');
const STUCK_N = parseInt(arg('stuck-window', '6'), 10);
const KEEP = arg('keep', 'reports');
const FROM = arg('from', null);
const REPRO = arg('repro', null);

/* THE MODELS ARE PINNED. nav_eval and scene_redteam both pin theirs and both say
 * why: an alias like `gemini-flash-latest` MOVES under you and every number
 * recorded against it silently stops being comparable to the one above it.
 *   PLAYER — one call per step: image in, one action out. The hard part here is
 *            SPATIAL ("where on this picture is the ground beside that stall"),
 *            not classification, so it was chosen by measurement rather than by
 *            reputation — docs/qa/playtest/model-bakeoff.md.
 *   JUDGE  — the stuck interview and the report prose. Rare, and worth more.
 * Swap either with --player-model / --judge-model; nothing else changes. */
const PLAYER_MODEL = arg('player-model', 'gemini:gemini-3.6-flash');
const JUDGE_MODEL = arg('judge-model', 'gemini:gemini-3.1-pro-preview');

// ----------------------------------------------------------- --checkpoints --
if (has('checkpoints')) {
  const { checkpoints, staleBriefs } = checkpointsFromStory();
  console.log('checkpoints DERIVED from public/game/story.json at run time — nothing is stored,');
  console.log('so nothing can go stale. --from=<id> drops the playtester in just before that beat.\n');
  for (const c of checkpoints) {
    console.log(`  ${c.id.padEnd(18)} ${String(c.scene).padEnd(16)} cam=${String(c.cam || '-').padEnd(10)} ` +
      `pos=${c.pos ? '[' + c.pos.join(', ') + ']' : '(shot spawn)'}`);
    console.log(`  ${''.padEnd(18)} objective: ${c.objective || '(none set yet)'}`);
    if (c.brief) console.log(`  ${''.padEnd(18)} brief: ${c.brief}`);
  }
  for (const k of staleBriefs)
    console.warn(`\n  WARN briefs.json names "${k}", which story.json no longer has. A stale brief is a stale instruction.`);
  process.exit(0);
}

// -------------------------------------------------------------- start plan --
// A NEW GAME STARTS WHERE story.json SAYS IT DOES, not where this file remembers. The
// front door (public/index.html) and playthrough_test read the same `start` block; when
// this line carried its own literal, the playtester was certifying a boot the player
// never gets — and the position in question is exactly the one PT-20260803-002 was about.
const STORY_START = JSON.parse(readFileSync(join(ROOT, 'public/game/story.json'), 'utf8')).start || {};
let plan = { kind: 'newgame', scene: arg('scene', STORY_START.scene || 'emb-cine'),
             cam: arg('cam', STORY_START.cam || 'woodroad'),
             pos: STORY_START.pos || null, brief: null, objective: null };
if (REPRO) {
  const e = Q.load().entries.find(x => x.id === REPRO);
  if (!e) { console.error('no queue entry ' + REPRO); process.exit(2); }
  if (!e.repro || !e.repro.save) { console.error(REPRO + ' carries no repro save'); process.exit(2); }
  if (e.repro.sha && HEAD_SHA && e.repro.sha !== HEAD_SHA)
    console.warn(`  WARN this repro was captured at ${e.repro.sha.slice(0, 8)} and HEAD is ${HEAD_SHA.slice(0, 8)}.\n` +
      '       Geometry, flags or beats may have moved under it. A replay that behaves differently is NOT\n' +
      '       evidence until you check out that commit — this is the staleness trap, made detectable.');
  plan = { kind: 'repro', id: REPRO, scene: e.truth.scene, cam: e.truth.shot, pos: e.truth.pos, save: e.repro.save,
    brief: 'You are being dropped back into a moment where a bug was reported. Try to continue playing normally.',
    objective: (e.onscreen || {}).objective || null };
} else if (FROM) {
  const c = checkpointsFromStory().checkpoints.find(x => x.id === FROM);
  if (!c) { console.error(`no beat "${FROM}" in story.json. Try --checkpoints`); process.exit(2); }
  plan = { kind: 'checkpoint', id: c.id, scene: c.scene, cam: c.cam, pos: c.pos, yaw: c.yaw, brief: c.brief, objective: c.objective,
    patch: { flags: c.flags, beats: c.beats, at: { chapter: c.chapter, scene: c.scene, cam: c.cam, pos: c.pos, yaw: null } } };
}

// ------------------------------------------------------------------ wiring --
const RUN_ID = 'run-' + new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '').replace('T', '-');
const RUNDIR = join(ROOT, 'docs/qa/playtest/runs', RUN_ID);
const FRAMES = join(RUNDIR, 'frames');
mkdirSync(FRAMES, { recursive: true });

const usage = new Usage();
const playerModel = makeModel(PLAYER_MODEL);
const judgeModel = makeModel(JUDGE_MODEL);
const player = makeAgent({ model: playerModel, persona: PERSONA, usage });
const judge = makeAgent({ model: judgeModel, persona: PERSONA, usage });
// One object to the runner: the player decides, the judge is interviewed. Two
// models, one seam — this IS the cheap/expensive split, and either half swaps alone.
const agent = { id: `${player.id} + ${judge.id}`, decide: player.decide, interview: judge.interview };

const adapter = makeAdapter({ port: PORT, headed: has('head'), framesDir: FRAMES });
const START = adapter.url(plan.scene, plan.cam, plan.pos, null, plan.yaw);

console.log('llm_playtester — one LLM, one screen, one keyboard');
console.log('  server  :' + PORT + '   ' + START);
console.log('  player  ' + playerModel.id + '   judge ' + judgeModel.id);
console.log('  start   ' + plan.kind + (plan.id ? ' ' + plan.id : ''));
console.log('  run     ' + RUN_ID + '  (' + MAX_STEPS + ' steps max)');

let result = null, err = null;
try {
  console.log('\n== BOOT');
  if (!await adapter.open(START)) { console.error('the page never became playable'); await adapter.close(); process.exit(13); }
  console.log(`== SETUP (${plan.kind})`);
  if (!await adapter.setup(plan)) { console.error('the page never became playable after setup'); await adapter.close(); process.exit(13); }
  console.log('== PLAY');
  /* THE SPINE, as a question the runner can ask without knowing what a beat is:
   * given the beats that have fired, which SCENES still hold one that has not?
   * Leaving that set is leaving the story, and it is the harness's job to notice
   * because the player cannot — the objective banner follows you out. */
  const ALL_BEATS = checkpointsFromStory().checkpoints;
  const SPINE_LOOKAHEAD = parseInt(arg('spine-lookahead', '3'), 10);
  /* THE NEXT FEW BEATS, NOT ANY BEAT. Measured the first time this ran: "a scene
   * holding an un-fired beat" put ow-valley on the spine, because ch1.done and
   * ch2.road live there — an hour of play away. The player who leaves Emberbrook on
   * frame two is standing in a scene the story does get to eventually, and a
   * detector that accepts that detects nothing. Three is the lookahead because
   * Chapter One's own Lake detour is a two-beat hop into an interior and back; a
   * lookahead of one would call that leaving the story. */
  const spineScenes = (fired) => {
    const f = new Set(fired);
    const next = ALL_BEATS.filter(b => !f.has(b.id) && b.scene).slice(0, SPINE_LOOKAHEAD);
    return new Set(next.map(b => b.scene));
  };
  result = await runEpisode({ adapter, agent, plan, runDir: RUNDIR, runId: RUN_ID, port: PORT,
    maxSteps: MAX_STEPS, maxReports: MAX_REPORTS, stopBeat: STOP_BEAT, stuckWindow: STUCK_N,
    spineScenes, noQueue: has('no-queue') });
} catch (e) {
  err = e;
  console.error('\nFATAL: ' + (e && e.stack || e));
} finally {
  await adapter.close();
}
if (!result) process.exit(err && /FIREWALL/.test(err.message) ? 9 : 1);

// ----------------------------------------------------------- the receipt ----
const summary = {
  run: RUN_ID, when: new Date().toISOString(), sha: HEAD_SHA,
  scene: plan.scene, cam: plan.cam, start: plan.kind, from: plan.id || null,
  playerModel: playerModel.id, judgeModel: judgeModel.id,
  steps: result.steps, finished: result.finished, beatsFired: result.beatsFired,
  endTruth: result.endTruth, legs: result.legs,
  reports: result.reports.map(r => r.id),
  usage: { calls: usage.calls, in: usage.in, out: usage.out, thought: usage.thought,
    apiSeconds: +(usage.ms / 1000).toFixed(0), estUSD: usage.estUSD(), byModel: usage.byModel },
};
writeFileSync(join(RUNDIR, 'run.json'), JSON.stringify(summary, null, 2));
writeFileSync(join(RUNDIR, 'legs.json'), JSON.stringify(result._legs, null, 2));

/* FRAME RETENTION. A 1280x720 JPEG is ~120 kB and a run is hundreds of them;
 * committing all of that puts a gigabyte of screenshots in the history for the sake
 * of the six pictures anyone will look at. Default keeps the frames a report cites
 * plus every 10th as a contact sheet. --keep=all keeps everything. */
if (KEEP !== 'all') {
  const cited = new Set(result.reports.flatMap(r => (r.frames || []).map(f => join(ROOT, f))));
  let dropped = 0;
  for (const f of readdirSync(FRAMES)) {
    const p = join(FRAMES, f);
    const n = parseInt((f.match(/step-(\d+)/) || [])[1] || '0', 10);
    // -UNREADY frames are the evidence that the INSTRUMENT went blind, and they are
    // the first thing anyone debugging that will want. They are never dropped.
    if (cited.has(p) || /-UNREADY\.jpg$/.test(f) || (n % 10 === 0 && /^step-\d+\.jpg$/.test(f))) continue;
    try { unlinkSync(p); dropped++; } catch (e) { }
  }
  console.log(`  frames: dropped ${dropped} uncited (kept every 10th + every frame a report cites; --keep=all keeps all)`);
}

console.log('\n== RUN ' + RUN_ID);
console.log(`  steps        ${result.steps}`);
console.log(`  finished     ${result.finished || 'ran out of steps'}`);
console.log(`  beats fired  ${result.beatsFired.length ? result.beatsFired.join(', ') : '(none)'}`);
console.log(`  walk legs    ${result.legs.n} (${result.legs.arrived} arrived, ${result.legs.offNetwork} aimed off the walk ` +
  `network, ${result.legs.unprojectable} un-projectable, ${result.legs.interrupted} interrupted by the game), ` +
  `median closed ${result.legs.medianClosedFrac}`);
console.log(`  reports      ${result.reports.length}  ${result.reports.map(r => r.id).join(' ')}`);
console.log('  model        ' + usage.report());
console.log(`  log          ${Q.relative(join(RUNDIR, 'run.jsonl'))}`);
console.log(`  golden set   ${Q.relative(join(RUNDIR, 'observations.jsonl'))}  (replay with tools/playtest_bench.mjs)`);
if (result.reports.length) {
  console.log('\n  *** THESE ARE LEADS, NOT TICKETS. Triage before anyone builds: ***');
  console.log('      node tools/playtest_triage.mjs --port=' + PORT);
}
process.exit(0);

/* =========================== COVERING CHAPTER TWO ===========================
 * V1 stops at ch1.sendoff on purpose. Chapter Two needs four things this does not
 * have, and each is real work rather than a bigger --steps:
 *
 *  1. CAMERA CONTROL IN ow-valley. The corridor between the towns is a REAL-TIME
 *     orbit scene (play3d's RT branch): the player drags the mouse to turn the
 *     camera, so "up" means "the way I am facing" rather than "away from a fixed
 *     camera". The action vocabulary needs `turn` mapped to
 *     Input.dispatchMouseEvent drags, and the agent must be told the camera is now
 *     its own responsibility. The un-projection already works there — it reads the
 *     LIVE camera, not cine.json.
 *  2. A LONGER LEASH. Ch1 in emb-cine is ~5 shots; Ch2 crosses ow-valley, del-cine
 *     and two interiors. Budget 300-500 steps.
 *  3. INTERIORS AND DOORWAYS. Doors are scenegraph edges and the prompt banner
 *     already reaches the agent, so this is mostly proving the in-place swap does
 *     not confuse it — the executor already breaks a leg when a modal opens.
 *  4. A SAVE/RESUME PROBE. Ch2 is where a player stops for the night. Driving the
 *     pause menu with the same keys and reloading would exercise the v2 save from
 *     the OUTSIDE for the first time. --from= already proves the load half.
 * ========================================================================== */
