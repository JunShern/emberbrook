/* agent.mjs — LAYER 1: THE PLAYER. GAME-AGNOSTIC ON PURPOSE.
 *
 * This file knows that it is looking at a screen, that it can point at the screen,
 * press a button, read a box of text and complain. It does NOT know about
 * Emberbrook, three.js, walk networks, cameras, beats, flags or scenes. Nothing in
 * here imports the adapter, and nothing in here should ever need to.
 *
 * THE CONTRACT, both directions:
 *
 *   IN   observation = {
 *          screenshot : {mime, data}     one frame, base64. The whole percept.
 *          text       : string           the text the GAME DREW on that frame —
 *                                        objective line, dialogue box, prompt
 *                                        banner, full-screen card. Already
 *                                        flattened by the adapter; the agent does
 *                                        not parse a DOM.
 *          history    : string[]         the last few things it did and saw.
 *          brief      : string|null      one sentence of orientation, for a
 *                                        mid-game drop-in. Null on a fresh start.
 *          nudge      : string|null      one-shot side channel (what it just read,
 *                                        or "you appear to be stuck").
 *        }
 *
 *   OUT  intent = { see, goal, action, ...fields }
 *          {action:'goto',     waypoints:[[x,y],...]}   x,y NORMALISED to the image
 *          {action:'interact'}                          the action button
 *          {action:'advance'}                           read through an open box
 *          {action:'choose',   index:N}
 *          {action:'wait',     ms:N}
 *          {action:'report',   report:{kind,title,doing,expected,happened}}
 *          {action:'giveup',   report:{...}}
 *
 * The waypoint convention is nav_eval.mjs's, deliberately: x is 0 at the left edge
 * and 1 at the right, y is 0 at the top and 1 at the bottom. One convention across
 * every instrument in this repo that asks a model to point at a picture.
 *
 * PERSONA. The one game-shaped thing a caller may inject is a short PERSONA string
 * — "you are playing a JRPG with fixed cameras" — because a player who does not
 * know what kind of game they are in plays badly, and a human always knows. It is
 * a parameter, not a hard-coded paragraph, and it is the only place the game may
 * leak in.
 *
 * WHAT THE AGENT MUST NEVER BE GIVEN — enforced upstream by the episode runner's
 * firewall, restated here because this is the file a future edit will touch:
 * no coordinates, no scene or camera names, no flags, no beat ids, no NPC ids, no
 * scene graph. If it is not drawn on the screen, it is not the player's.
 */
import { parseJson } from './models.mjs';

export const DEFAULT_PERSONA =
  'You are playtesting a video game. You control one character on screen.';

const CONTROLS = [
  'HOW YOU ACT. You do not press keys frame by frame. You POINT AT THE PICTURE and the',
  'game walks your character there. Coordinates are normalised to this image:',
  '  x = 0.0 at the LEFT edge, 1.0 at the RIGHT edge',
  '  y = 0.0 at the TOP edge,  1.0 at the BOTTOM edge',
  'Aim at GROUND you could stand on — a path, a floor, the flat ground beside a person —',
  'never at a wall, a roof, a treetop or the sky. To reach a person, aim at the ground at',
  'their FEET. Give 1 to 4 waypoints in the order you would walk them; use several when you',
  'have to go around something.',
  '',
  'YOUR ACTIONS (choose exactly one per turn):',
  '  goto      {"action":"goto","waypoints":[[0.42,0.71],[0.55,0.55]]}',
  '  interact  press the action button. Use it when a prompt like "Talk to Rowan? [E]" is',
  '            on screen, or when you are standing right next to something you want to use.',
  '            You must be CLOSE — walk there first.',
  '  advance   read through an open dialogue box or a full-screen card. Use this whenever',
  '            one is on screen; it reads the whole conversation and gives you the text back.',
  '  choose    {"action":"choose","index":0} pick from a list of choices (0 = the first).',
  '  wait      {"action":"wait","ms":800} let something on screen finish.',
  '',
  'HOW TO PLAY WELL:',
  '  - Read the objective line if there is one. Do what it says.',
  '  - Follow paths, roads, doorways and light. Lit places are where things happen.',
  '  - If a walk did not get you where you pointed, you were blocked. Go a different way.',
  '  - If you have tried the same thing three times, TRY SOMETHING ELSE.',
  '  - Find your own character in the picture before you decide where to walk.',
  '',
  'REPORTING — you are a playtester, so say so when the game fails you:',
  '  {"action":"report","report":{"kind":"blocker|confusion|bug|complaint","title":"...",',
  '   "doing":"...","expected":"...","happened":"..."}}',
  '  Report the moment something confuses you, blocks you, looks broken, or contradicts what',
  '  you were told. Reporting does NOT stop the game — keep playing afterwards. Use "giveup"',
  '  only if you truly cannot continue. Write in the FIRST PERSON, plainly, as a person would',
  '  say it to a developer. Do not speculate about code.',
  '',
  'Reply with ONE JSON object and nothing else:',
  '{"see":"<one sentence: what is on screen>","goal":"<what you are trying to do right now>",',
  ' "action":"goto|interact|advance|choose|wait|report|giveup", ...the fields for that action}',
].join('\n');

/* THE INTERVIEW. This is the output the whole instrument exists for: the sentence
 * a person says when they put the controller down. It is asked on the agent's own
 * last frames with its own stated goals in front of it, and never summarised by
 * the harness — a harness-written bug report is just the harness's opinion with
 * extra steps. "notabug" is offered as a first-class answer because a judge with
 * no way to say "I was wrong" will invent a finding. */
const INTERVIEW = [
  'You are the playtester. You have been stuck: for several turns you have not moved, the',
  'objective has not changed, and nothing new has happened on screen. The images are your',
  'last few frames, oldest first.',
  '',
  'Answer as a person would when they put the controller down and tell a developer why.',
  'Plain language, first person, no jargon, no guessing about code. Say what you can see and',
  'what you cannot. If you think you are actually fine and were just being impatient, say so —',
  '"notabug" is a real and useful answer and it is far better than an invented one.',
  '',
  'Reply with ONE JSON object:',
  '{"kind":"blocker|confusion|bug|complaint|notabug","severity":"P0|P1|P2",',
  ' "title":"<one short line a developer could put on a ticket>",',
  ' "doing":"<what you were trying to do, in your own words>",',
  ' "expected":"<what you expected to happen>","happened":"<what actually happened>"}',
].join('\n');

/** Assemble the prompt for one decision. Exported so the benchmark can replay a
 *  recorded observation through a different model with a byte-identical prompt —
 *  a benchmark that re-words the question is measuring the wording. */
export function decisionPrompt(obs, persona) {
  const [P, C, brief, nudge] = authoredParts(obs, persona);
  const L = [P, '', C];
  if (brief) L.push('', '=== WHERE YOU ARE ===', brief);
  L.push('', '=== WHAT YOU HAVE DONE (most recent last) ===',
    (obs.history && obs.history.length) ? obs.history.join('\n') : '(nothing yet — you have just started)');
  L.push('', '=== WHAT IS ON YOUR SCREEN RIGHT NOW ===', obs.text || '(no text on screen)');
  if (nudge) L.push('', '=== NOTE ===', nudge);
  L.push('', 'The image is your screen. Choose ONE action.');
  return L.join('\n');
}
/* EXACTLY THE PARTS OF THAT PROMPT THE HARNESS WROTE, named once and used twice —
 * decisionPrompt assembles from them, and episode.mjs's firewall runs its SOFT check
 * against them ALONE. Everything else in the prompt is either the text the game drew
 * or the agent's own recollection, and a player is allowed to know the word "square".
 *
 * WHY THIS EXISTS (2026-08-03): assertNoPrivileged's third argument used to default to
 * THE WHOLE PROMPT when it was null, and a `newgame` plan has no brief, so every
 * newgame run had the soft list checked against the game's own dialogue — the exact
 * false alarm ("A waystone. Good — the road's a real road, then.") the harnessText
 * argument was added to prevent. It killed newgame runs at step 2 while checkpoint
 * runs, which do have a brief, passed. Deriving both from this one array is what stops
 * the prompt and the soft-check target drifting apart again: a soft target that omits
 * something the harness wrote is a hole, and one that includes the screen is a wall. */
export function authoredParts(obs, persona) {
  return [persona || DEFAULT_PERSONA, CONTROLS, obs.brief || '', obs.nudge || ''];
}

const VALID = new Set(['goto', 'interact', 'advance', 'choose', 'wait', 'report', 'giveup']);

/** Coerce whatever came back into a legal intent. A malformed reply must degrade
 *  to a harmless action, never to a crash and never to a silent no-op that the
 *  stuck detector then blames the game for. */
export function normalise(j) {
  if (!j || typeof j !== 'object') return { see: '(unparsed reply)', goal: 'recover', action: 'wait', ms: 500, malformed: true };
  const out = { see: String(j.see || '').slice(0, 300), goal: String(j.goal || '').slice(0, 300),
    action: VALID.has(j.action) ? j.action : 'wait' };
  if (out.action === 'goto') {
    let w = j.waypoints || j.points || (j.x !== undefined ? [[j.x, j.y]] : []);
    if (!Array.isArray(w)) w = [];
    out.waypoints = w.map(p => Array.isArray(p) ? [+p[0], +p[1]] : [+p.x, +p.y])
      .filter(p => Number.isFinite(p[0]) && Number.isFinite(p[1]))
      .map(p => [Math.max(0, Math.min(1, p[0])), Math.max(0, Math.min(1, p[1]))])
      .slice(0, 4);
    if (!out.waypoints.length) { out.action = 'wait'; out.ms = 400; out.malformed = true; }
  } else if (out.action === 'choose') out.index = Math.max(0, Math.min(9, parseInt(j.index, 10) || 0));
  else if (out.action === 'wait') out.ms = Math.max(150, Math.min(4000, +j.ms || 500));
  else if (out.action === 'report' || out.action === 'giveup') {
    const r = j.report || j;
    // No default title. An empty report must LOOK empty so the runner can refuse
    // it — 'untitled' with three nulls at P0 is worse than nothing, because it
    // costs a human the same look as a real finding.
    out.report = { kind: r.kind || 'confusion', severity: r.severity || null,
      title: r.title ? String(r.title).slice(0, 140) : (out.goal || null),
      doing: r.doing || null, expected: r.expected || null, happened: r.happened || null };
  }
  return out;
}

/**
 * makeAgent({model, persona, temperature}) -> { decide(obs), interview(obs) }
 * `model` is anything from models.mjs. Swapping it is the whole point.
 */
export function makeAgent({ model, persona = DEFAULT_PERSONA, temperature = 0.55, usage = null }) {
  const call = async (parts, text, temp) => {
    const r = await model.ask({ images: parts, text, temperature: temp });
    if (usage) usage.add(model.id, r.usage);
    return r.text;
  };
  return {
    id: model.id, persona,
    async decide(obs) {
      const text = decisionPrompt(obs, persona);
      const raw = await call([obs.screenshot], text, temperature);
      const j = normalise(parseJson(raw));
      j._prompt = text;                 // the runner's firewall inspects this
      j._authored = authoredParts(obs, persona).join('\n');   // ...and only this for soft tokens
      return j;
    },
    /* frames: [{mime,data}] oldest first. Returns a report object or null when the
     * agent says it is not actually stuck. */
    async interview(obs) {
      const text = INTERVIEW + '\n\n=== WHAT YOU HAVE BEEN DOING (most recent last) ===\n' +
        (obs.history || []).join('\n') + '\n\n=== THE TEXT ON YOUR SCREEN NOW ===\n' + (obs.text || '(none)');
      const raw = await call(obs.screenshots || [obs.screenshot], text, 0.3);
      const j = parseJson(raw);
      if (!j) return null;
      j._prompt = text;
      // The interview prompt's only harness-authored part is the INTERVIEW constant;
      // the history and the on-screen text are the agent's and the game's.
      j._authored = INTERVIEW;
      if (j.kind === 'notabug') return { notabug: true, _prompt: text, _authored: INTERVIEW };
      return j;
    },
  };
}
