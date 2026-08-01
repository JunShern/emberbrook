#!/usr/bin/env node
// gen-cutin-art.mjs — DRAW THE PORTRAITS FOR THE MATTE, not around it.
//
//   node tools/gen-cutin-art.mjs --plan            # what would run, and what it costs
//   node tools/gen-cutin-art.mjs --check           # assert the spec covers every used mood
//   node tools/gen-cutin-art.mjs                   # fill in everything missing
//   node tools/gen-cutin-art.mjs odessa lake       # just these characters
//   node tools/gen-cutin-art.mjs odessa --redo rest
//   node tools/gen-cutin-art.mjs odessa --redo grave,warm
//   node tools/gen-cutin-art.mjs odessa --only rest --key green --suffix _grn   # trial roll
//
// WHY THIS FILE EXISTS. tools/gen-cutin.py salvaged cut-outs from bust.png, and the
// user looked at the result on 2026-08-01 and ruled the approach wrong: "we should
// explicitly regenerate the images with the cut-in in mind... very amenable to the
// background being masked out." The busts were drawn to sit INSIDE a frame, on warm
// toned paper with a radial glow behind the figure, and no matte can be crisp against
// a background that has no edge in it — the measured evidence is docs/qa/cutins:
// 43 of 62 salvaged plates fail tools/cutin_edge.py, most of them on a +15 to +67
// level bright paper fringe. So this draws NEW plates whose background is a key.
//
//   public/assets/characters/<id>/bust.png                (identity anchor, ratified)
//        -> studio/rest.png                               (chest-up, on the key)
//        -> studio/<mood>.png                             (ref = studio/rest.png)
//
// FOUR THINGS THE PROMPT HAS TO WIN, and the reason each is worded the way it is:
//
//  1. THE BACKGROUND IS A KEY, NOT A BACKDROP. "Flat" alone gets a flat colour with
//     a soft vignette in it, because that is what a portrait background looks like in
//     the training data. The prompt therefore names the failure modes one at a time
//     — no gradient, no vignette, no texture, no cast shadow, no glow, no rim light
//     spilling onto it — and calls the thing a chroma-key screen, which is a concept
//     the model has and "flat background" is not.
//
//  2. THE SILHOUETTE IS DRAWN. A soft-edged figure on a flat key mattes no better
//     than a hard-edged one on paper; the fringe just changes colour. So the prompt
//     asks for a definite drawn outline all the way round and forbids wisps that
//     dissolve into the background.
//
//  3. IDENTITY IS THE REFERENCE IMAGE, NOT THE TEXT. bust.png is the cast's ratified
//     look and it is passed as the ref for every `rest` plate; each mood then refs the
//     character's OWN rest plate, so a mood inherits the new framing, the new key and
//     the new likeness in one hop instead of drifting from a two-hop chain. The only
//     text identity is the config's `sheetHint` — the wardrobe line, which exists
//     precisely because it carries clothes and hair and NO expression. `desc` is
//     deliberately NOT used: half the archetype descs contain the words "neutral
//     expression", and this pass is the ruling against exactly that.
//
//  4. THE EXPRESSION IS PUSHED. The user's second ruling: the shipped art reads
//     "emotionless and dead". A cut-in is read at a glance at ~500 px, so the spec's
//     mood text names a brow, a mouth and a posture, and the prompt says out loud that
//     theatrical is correct here — with the identity clauses immediately after, so
//     "more expression" never becomes "different person".
//
// THE PLATES ARE NOT COMMITTED (.gitignore: **/studio/). They are 2 MB each and there
// are 138 of them; the repo is already 6.6 GB and CLAUDE.md records a push that died
// on GitHub's pack limit. What ships is the matte — the same drawing minus a colour
// nobody sees. Losing a studio plate costs a re-roll of that plate, and this file
// plus tools/characters/cutins.spec.json is what makes a re-roll one command.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { genart, PRICE } from './genart.mjs';

const root = path.join(import.meta.dirname, '..');
const CHARS = path.join(root, 'public/assets/characters');
const SPEC = path.join(root, 'tools/characters/cutins.spec.json');

// THE KEY COLOURS, and how the winner was chosen. Both were rolled on Odessa (whose
// palette — dark oilskin, cream knit, grey hair — is the cast's most neutral) and on
// Lake (dark green vest, the green key's worst case) before the batch, and measured
// with tools/cutin_edge.py rather than looked at. See docs/qa/DAYLOG.md.
export const KEYS = {
  magenta: { hex: '#FF00FF', name: 'pure bright magenta', rgb: [255, 0, 255] },
  green: { hex: '#00E000', name: 'pure bright chroma-key green', rgb: [0, 224, 0] },
};
export const DEFAULT_KEY = 'magenta';

/* ------------------------------------------------------------- the prompt ---- */
// One template, three callers (this file, gen-cutin-base.mjs's sibling recipe, and
// gen-cutin-poses.mjs — which is why it is exported). `ref` is always the image
// immediately upstream, so the wording that protects identity is the same for a rest
// plate (from the bust) and a mood plate (from the rest) — "this exact character,
// redrawn" either way. `chain` (0/1/2) is the count of PRIOR-POSE references attached
// AFTER the upstream ref by the pose-diversity chain; `avoid` is the text-only
// fallback that describes those prior poses in words instead of attaching them.
// `calm` (2026-08-01, pose-matrix review): the rest plate was inheriting the moods'
// "push it — theatrical" block and came back over-acting. Rest is the pose the
// player sees for 90% of a conversation; its whole job is to be the quiet baseline
// the emotions jump FROM. calm swaps the theatrical push and the gesture mandate
// for at-ease composure while keeping framing/identity/background identical.
export function promptFor({ hint, key, expression, framing, extra, gesture, first,
                            chain = 0, avoid = null, calm = false }) {
  const K = KEYS[key];
  return [
    // THE USAGE CONTEXT, said out loud (user ruling 2026-08-01, Vesper review): the
    // model must know the plate fires in hundreds of unrelated conversations, so an
    // emotion aimed at a specific thing (a notebook, a page, an event in-frame) is
    // wrong even when it is beautifully drawn. Theatrical but GENERALIZABLE.
    // WORDED WITH CARE, and re-worded on a measurement: the first draft opened with
    // "art that rises out of a dialogue box", and three consecutive base rolls came
    // back as sculpted head-and-shoulders busts (bot_cut 0.69/0.69/0.69) where the
    // previous shorter opener had produced nine stomach-up plates from the same
    // reference. A dialogue-box portrait IS a bust in the training data; naming the
    // box primes the crop. The context now names the REUSE, never the widget, and
    // FRAMING speaks before IDENTITY hands the microphone to the reference.
    `Redraw this exact character as a waist-up JRPG character portrait for a large`,
    `story game. This exact image will be reused in hundreds of different`,
    `conversations in every location of the game, so the emotion must be theatrical`,
    `but GENERALIZABLE — addressed to the unseen person the character is talking`,
    `to, who stands just past the edge of the frame, and never aimed at any object,`,
    `page, item or event inside the picture.`,

    `FRAMING — ${framing}. Fill the frame: the subject should occupy almost the whole`,
    `image with only a small margin of background around it. Facing slightly toward`,
    `the viewer. Nothing is cropped off the left or right edges.`,

    `IDENTITY — copy from the reference image and do not invent: the same face, the`,
    `same bone structure and age, the same skin tone, the same hair colour and`,
    `hairstyle, the same eyes, the same outfit in the same colours, and the same`,
    `drawing medium, rendering style, linework and shading technique as the`,
    `reference.${hint ? ` The character: ${hint}.` : ''}`,
    // THE REFERENCE'S OWN CROP IS THE ENEMY, for the base plate only. Both Mara
    // rolls and two Vesper base rolls came back as head-and-shoulders busts with a
    // sculpted taper: the ratified bust.png is composed exactly that way, and an
    // image reference outweighs framing prose the prompt never aims at it. Naming
    // the mismatch is the aim. Mood plates skip this — their reference (the base)
    // is framed RIGHT, and they are told to copy it.
    first ?
      `IMPORTANT: the reference image is cropped far tighter than this portrait and` +
      ` ends in a rounded sculpted bust shape — do NOT copy the reference's crop or` +
      ` that bust shape. Draw MORE of the body than the reference shows: torso,` +
      ` chest, stomach and waist, all the way down to the bottom edge of the image,` +
      ` where the figure is sliced off flat and straight at the waist.` : '',

    `BACKGROUND — DISCARD the reference image's background entirely. Its paper tone,`,
    `its soft glow behind the figure and the way the figure fades out towards the`,
    `bottom are all thrown away and must not be recoloured or reproduced. The new`,
    `background is a single perfectly flat, uniform, solid ${K.name} (${K.hex}),`,
    `exactly one colour from edge to edge, like a chroma-key screen in a studio.`,
    `NO paper texture, NO paper grain, NO gradient, NO vignette, NO shading, NO cast`,
    `shadow, NO glow, NO halo, NO rim light or colour spilling onto the background,`,
    `NO scenery, NO props. The background is empty colour and nothing else, and it`,
    `must be the same ${K.name} in the corners as it is beside the subject's cheek.`,
    // Two failure modes seen in the first batch of 138, each worth naming out loud.
    // Sorrel's `happy` came back as a STICKER: a magenta rectangle with a white
    // outline sitting on a white page, which mattes to a pink block behind her and
    // passes every geometric metric because a rectangle has excellent edges. Maren's
    // and Rowan's came back on PAPER, the key ignored entirely.
    `The ${K.name} FILLS THE WHOLE IMAGE, right out to all four edges — the corner`,
    `pixels of the image are ${K.name}. Do NOT draw this as a sticker, a card, a`,
    `badge, a panel or a framed insert: no white page behind it, no white or coloured`,
    `outline around the portrait, no border, no margin, no rounded rectangle, no drop`,
    `shadow. Do not put the character on paper or on any other backdrop — the only`,
    `background that exists in this image is the flat ${K.name}.`,
    // KEY SPILL PAINTED AS ART (2026-08-01, pose-matrix review): the model invents
    // magenta "reflections" ON the figure — pink-tinted hair strand tips, fuchsia
    // wisps — and chained rolls AMPLIFY them by copying earlier rolls' spill as if
    // it were character design (measured: 67 -> 206 -> 1564 pink px along one rest
    // chain, against 1 px in the clean base). Named out loud like the other
    // failure modes, because the matte cannot fix paint that is genuinely part of
    // the figure.
    `The ${K.name} exists ONLY behind the character and never ON the character: no`,
    `${K.name} or pink reflections, tints, strands, streaks or highlights in the`,
    `hair or anywhere on the figure. If a reference image shows pink or magenta`,
    `tinted hair strands, that is background contamination — do NOT copy it; the`,
    `character's hair is its natural colour throughout, exactly as in the first`,
    `reference image.`,

    `EDGE — the subject's silhouette is crisp and completely separated from the`,
    `background the whole way round, with a definite DARK drawn outline. No soft`,
    `fade, no blur, no feathering, and no strands or wisps dissolving into the`,
    `background colour. Do NOT draw a pale rim light, a bright outline, a white or`,
    `cream edge, a glow or any halo around the subject — the edge of the character`,
    `is a dark line, and the pixel next to it is plain background. The figure does`,
    `NOT fade out at the bottom of the image: it is cut off cleanly by the edge of`,
    `the frame, fully opaque right up to it. A cut-out will be made along this`,
    `outline, so anything glowing around the subject would be cut out with it.`,

    calm ?
      `EXPRESSION — ${expression}. This is the character's NEUTRAL RESTING portrait, ` +
      `the one on screen for most of every conversation: calm, composed and quiet. ` +
      `Do NOT push the expression — no wide eyes, no open mouth, no raised brows, no ` +
      `dramatic tilt. The character is simply present and listening, at ease, with ` +
      `their personality showing only as a subtle cast of the face. The pose is ` +
      `relaxed and natural — weight settled, shoulders easy, arms resting naturally ` +
      `(at the sides, loosely clasped, or another quiet at-ease position). No ` +
      `gesturing, no pointing, no raised hands.` :
      `EXPRESSION — ${expression}. Push it: this portrait is read at a glance, so the ` +
      `expression is theatrical and unmistakable — clearly shaped brows, a clearly ` +
      `shaped mouth, and a shift of the head and shoulders that carries the feeling.`,
    `Everything else about the character stays exactly as the reference image:`,
    `same face, same hair, same clothes, same colours, same medium.`,

    // POSE, NOT HANDS (user ruling 2026-08-01, suite v2 review). The first wording of
    // this block opened with a hands mandate ("the hands and arms are IN THE PICTURE
    // and doing something") and the user's verdict on the resulting suite was that
    // the gesture DIRECTION was approved but the execution collapsed into repetitive
    // hand gesticulation — pointing and palming in nearly every mood, because a hands
    // mandate plus a per-character menu of hand moves repeated verbatim in all eight
    // prompts is a hands lottery, not staging. The primary instruction is now the
    // SILHOUETTE — posture, lean, weight shift, shoulder line, head angle — with the
    // hands demoted to one tool the pose may or may not call for; the animator
    // framing is the user's own wording, kept near-verbatim. The interlocutor
    // direction, the empty-hands/no-props ban and the no-wrist-crop rule all stand.
    (first || calm) ? '' :
      `POSE — stage this emotion with the WHOLE BODY, like an animator posing a key ` +
      `frame: be creative and design the character's pose the way a top-notch ` +
      `animator would. This emotion gets its own posture — a lean, a weight shift, a ` +
      `changed shoulder line, a different head angle, drawing up taller or slumping ` +
      `smaller — so that the SILHOUETTE alone, at a glance, says the feeling: an ` +
      `outline distinct from the character's resting pose and from their other ` +
      `expressions, because the outline is what a player reads first at this size. ` +
      `The hands are ONE TOOL AMONG MANY, not a requirement: they join in only when ` +
      `the pose truly calls for them, and an emotion carried by posture alone, with ` +
      `the hands quiet, is a strong answer. ${gesture ? gesture + ' ' : ''}The pose ` +
      `is addressed TO the unseen conversation partner just off-frame — eyes and ` +
      `body language toward them (unless the emotion itself naturally looks away), ` +
      `the way an actor plays to a scene partner. The HANDS ARE EMPTY: no notebook, ` +
      `no pencil, no tool, no held object of any kind, and the emotion is never ` +
      `directed at or about an object. Both hands stay INSIDE the frame — a raised ` +
      `hand may come close to the left or right edge but must never be cut off at ` +
      `the wrist, and no arm may run off the side of the image.`,

    // POSE VARIETY — the chained-diversity instruction (user-designed, 2026-08-01):
    // roll 2 of an expression attaches roll 1 as an extra reference, roll 3 attaches
    // both, so "a different pose" is defined by pictures rather than by prose. This
    // is a DELIBERATE exception to the one-reference rule below: the measured blend
    // (Maren 0.099 -> 0.494) was two refs at DIFFERENT framings; chain refs are the
    // same character at the same framing on the same key. `avoid` is the text-only
    // alternative that describes the prior poses in words instead of attaching them.
    // "different pose" alone converged (user, 2026-08-01 second review): rolls kept
    // finding the nearest neighbouring pose. The clause now demands the ACTING be
    // uniquely different — a different way of physically expressing the same
    // emotion, not the previous pose adjusted — and says plainly that resembling
    // any earlier version is failure.
    chain ?
      `POSE VARIETY — after the first reference image, the ${chain === 1
        ? 'second reference image shows' : 'later reference images show'} this SAME ` +
      `character wearing this SAME expression in ${chain === 1
        ? 'a pose that is' : 'poses that are'} already taken. Draw the same ` +
      `character, the same emotion, but express it in a UNIQUELY DIFFERENT way ` +
      `from every version already shown: not the same pose adjusted, but a ` +
      `genuinely different piece of acting — as if a top-notch animator were ` +
      `exploring a completely different take on this key frame. Change the whole ` +
      `body language at once: a different lean, a different weight, a different ` +
      `shoulder line, a different head angle, the arms doing something clearly ` +
      `different. If this new drawing would look like a variation of ${chain === 1
        ? 'the taken pose' : 'any of the taken poses'} at a glance, it is wrong — ` +
      `pick a different take entirely. The face keeps the exact same emotion.` :
    avoid ?
      `POSE VARIETY — the following pose${avoid.includes(';') ? 's are' : ' is'} ` +
      `already taken for this expression: ${avoid} Draw the same character, the ` +
      `same expression, but a DIFFERENT pose — a different silhouette from those: ` +
      `a different lean, a different shoulder line, a different head angle, the ` +
      `arms doing something clearly different.` : '',

    extra || '',
    `No text, no watermark, no frame, no border, no signature.`,
    // ONE reference, and a measured decision. Passing the ratified bust ALONGSIDE
    // the rest plate — identity from the first, framing from the second — reads as
    // the obvious improvement and is much worse: Maren's `happy` went from an
    // edge_noise of 0.099 to 0.494 with a 15% pinhole rate, because a model given
    // two images of one person at two framings blends them. One upstream image —
    // except the pose-diversity chain (above), whose extra refs share the upstream
    // ref's framing and key and exist precisely to be varied FROM.
    first ? '' : `Keep the framing, the scale and the background colour identical to the ` +
      `${chain ? 'FIRST reference image' : 'reference'}.`,
  ].filter(Boolean).join(' ');
}

// THE FRAMING SPEC, IN NUMBERS. User ruling (2026-08-01), after browsing the gallery:
// the set drifted from shoulders-up to waist-up and "the drift IS the defect — a
// portrait system reads as a system only when every character sits in the frame the
// same way." So the frame is stated as measurements rather than adjectives, here in
// the prompt and again in tools/cutin_edge.py's framing gate, which is what actually
// makes sixty-odd images consistent. Care does not scale; a gate does.
export // WORDED POSITIVE-ONLY (2026-08-01 waist-up audit): this text used to say "NOT a
// bust" twice — and the pipeline's own dialogue-box lesson is that naming a
// failure mode can prime it. The framing now describes only what IS in frame.
const DEFAULT_FRAMING =
  'a WAIST-UP portrait, framed identically for every character in this cast. ' +
  'The bottom edge of the image cuts across the WAIST, at the top of the hips. ' +
  'The figure is SLICED OFF by the bottom edge in a clean, perfectly STRAIGHT ' +
  'HORIZONTAL line, like a photograph cropped at the waist: the torso is fully ' +
  'opaque and full width right down to the bottom edge of the image. The lower ' +
  'edge of the figure is always that one clean straight horizontal slice — never ' +
  'rounded, never tapered, never fading out, never narrowing into a sculpted ' +
  'base, never angled. ' +
  'The head is large in the frame: the crown of the head sits about one tenth of ' +
  'the image height below the top edge, and the head — crown to chin — occupies ' +
  'about a third of the image height. The eyes fall in the upper third of the ' +
  'image. The character is centred, with both shoulders and the upper arms fully ' +
  'inside the frame and a little clear space either side, so a raised hand or a ' +
  'shrug has somewhere to go. The image always includes the head, the chest, the ' +
  'stomach and the top of the hips — the full torso is in frame down to the hip ' +
  'line, and nothing below the waist: crown near the top, waist at the bottom';

/* ------------------------------------------------------------------ plan ---- */
export function loadSpec() {
  const s = JSON.parse(fs.readFileSync(SPEC, 'utf8'));
  // MOOD DEFAULTS MERGE (user-ratified 2026-08-01, "leaner scheme"): the spec's
  // moodDefaults are the shared per-emotion facial grammar — the measured lessons
  // (worry-brow raised not knitted, determined = level-brow resolve, tender =
  // guard-drop event). A character's own moods{} entries OVERRIDE per key; a
  // character with no entry for a used mood inherits the default. Personality
  // lives in the overrides, the rest text and the gesture line — the default is
  // the floor, not the ceiling.
  const defaults = s.moodDefaults || {};
  for (const ent of Object.values(s.characters)) {
    const own = ent.moods || {};
    ent.moods = {};
    for (const [k, v] of Object.entries(defaults)) if (k !== '_doc') ent.moods[k] = v;
    Object.assign(ent.moods, own);
  }
  return s.characters;
}
export function hintFor(id, ent) {
  if (ent._desc) return ent._desc;
  const p = path.join(root, 'tools/characters', id + '.json');
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8')).sheetHint || null;
}
const studioDir = (id, suffix) => path.join(CHARS, id, 'studio' + (suffix || ''));

function planFor(ids, spec, { key, suffix, redo, only }) {
  const jobs = [];
  const keep = (m) => !only || only.has(m);
  for (const id of ids) {
    const ent = spec[id];
    if (!ent) { console.error(`  !! no spec entry for "${id}"`); continue; }
    // THE BASE REF'S COMPOSITION OUTWEIGHS THE PROMPT, measured the hard way: three
    // Vesper base rolls and two Mara rest rolls came back as near-identical copies
    // of bust.png's sculpted head-and-shoulders crop (bot_cut 0.69/0.69/0.69 across
    // three rolls, one of them under a prompt that named the failure out loud). The
    // fix is compositional, not textual: bust-waist.png is bust.png's exact pixels
    // on a canvas extended ~45% downward in the paper's own tone, so the reference
    // itself says "the picture continues below the chest". Identity and medium stay
    // ratified to the pixel. Built per character when the plain bust defeats the
    // framing prompt; used automatically when present.
    let bust = path.join(CHARS, id, 'bust-waist.png');
    if (!fs.existsSync(bust)) bust = path.join(CHARS, id, 'bust.png');
    if (!fs.existsSync(bust)) { console.error(`  !! no bust.png for "${id}" — identity anchor missing`); continue; }
    const dir = studioDir(id, suffix);
    const hint = hintFor(id, ent);
    const framing = ent.framing || DEFAULT_FRAMING;
    const extra = ent.extra || null;
    const gesture = ent.gesture || null;
    const rest = path.join(dir, 'rest.png');
    const want = (f, m) => redo.has('all') || redo.has(m) || !fs.existsSync(f);

    if (keep('rest')) jobs.push({
      id, mood: 'rest', out: rest, refs: [bust], first: true,
      run: want(rest, 'rest'),
      prompt: promptFor({ hint, key, framing, extra, first: true, expression: ent.rest }),
    });
    for (const [mood, text] of Object.entries(ent.moods || {})) {
      if (!keep(mood)) continue;
      const out = path.join(dir, mood + '.png');
      jobs.push({
        id, mood, out, refs: [rest], first: false,
        run: want(out, mood),
        prompt: promptFor({ hint, key, framing, extra, gesture, first: false, expression: text }),
      });
    }
  }
  return jobs;
}

/* ----------------------------------------------------------------- check ---- */
// THE SUPERSET ASSERTION. A mood that has shipped art, or that dialogue.json asks a
// line to wear, must be in the spec — otherwise this pass silently demotes a scripted
// beat to the neutral plate, which is precisely the regression the rollout forbids.
function check(spec) {
  let bad = 0;
  const D = JSON.parse(fs.readFileSync(path.join(root, 'public/game/dialogue.json'), 'utf8'));
  const want = {};                                   // pid -> Set(mood)
  const add = (pid, m) => { if (pid && m) (want[pid] ||= new Set()).add(m); };
  const portraitOf = (id) => {
    const s = D.speakers[id];
    return s && s.portrait !== undefined ? s.portrait : id;
  };
  for (const n of Object.values(D.nodes)) {
    for (const l of n.lines || []) {
      if (l && typeof l === 'object' && (l.expr || n.expr))
        add(portraitOf(l.speaker || n.speaker), l.expr || n.expr);
    }
    if (n.expr) add(portraitOf(n.speaker), n.expr);
  }
  for (const d of fs.readdirSync(CHARS)) {
    if (!fs.statSync(path.join(CHARS, d)).isDirectory()) continue;
    for (const f of fs.readdirSync(path.join(CHARS, d))) {
      const m = /^cutin-(.+)\.png$/.exec(f);
      if (m) add(d, m[1]);
    }
  }
  for (const [pid, moods] of Object.entries(want)) {
    const ent = spec[pid];
    if (!ent) { console.log(`  FAIL "${pid}" is used but has no spec entry`); bad++; continue; }
    for (const m of moods) {
      if (!(ent.moods || {})[m]) { console.log(`  FAIL "${pid}" mood "${m}" is in use but not in the spec`); bad++; }
    }
  }
  console.log(bad ? `\n${bad} coverage gap(s)` : '\nspec covers every shipped and scripted mood');
  return bad === 0;
}

/* ------------------------------------------------------------------ main ---- */
// Guarded so gen-cutin-poses.mjs can import the prompt machinery without this
// file's CLI spending money as a side effect of the import.
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {

const argv = process.argv.slice(2);
const ids = [], redo = new Set();
let key = DEFAULT_KEY, suffix = '', pool = 4, plan = false, doCheck = false, only = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--plan') plan = true;
  else if (a === '--check') doCheck = true;
  else if (a === '--only') only = new Set(argv[++i].split(',').map(s => s.trim()));
  else if (a === '--key') key = argv[++i];
  else if (a === '--suffix') suffix = argv[++i];
  else if (a === '--pool') pool = Math.max(1, +argv[++i] || 4);
  else if (a === '--redo') argv[++i].split(',').forEach(s => redo.add(s.trim()));
  else if (a.startsWith('--')) { console.error('unknown flag ' + a); process.exit(1); }
  else ids.push(a);
}
if (!KEYS[key]) { console.error('unknown --key ' + key + ' (have: ' + Object.keys(KEYS).join(', ') + ')'); process.exit(1); }

const spec = loadSpec();
if (doCheck) process.exit(check(spec) ? 0 : 1);

const targets = ids.length ? ids : Object.keys(spec);
const jobs = planFor(targets, spec, { key, suffix, redo, only });
const todo = jobs.filter(j => j.run);
console.log(`${jobs.length} plates across ${targets.length} characters · ` +
  `${todo.length} to draw on the ${key} key · ~$${(todo.length * PRICE).toFixed(2)}`);
if (plan) {
  for (const j of jobs) console.log(`  ${j.run ? 'DRAW' : 'keep'}  ${j.id}/${j.mood}`);
  console.log('\nplan only — nothing generated');
  process.exit(0);
}

// A MOOD CANNOT BE DRAWN BEFORE ITS REST PLATE, because rest.png is its reference.
// So the run is two waves rather than one pool: every rest first, then every mood.
// Within a wave the order does not matter and the pool is free to run flat out.
async function wave(list, label) {
  let i = 0, ok = 0, failed = [];
  const t0 = Date.now();
  async function worker() {
    for (;;) {
      const j = list[i++];
      if (!j) return;
      for (const r of j.refs) {
        if (!fs.existsSync(r)) { failed.push(`${j.id}/${j.mood}: missing ref ${path.relative(root, r)}`); break; }
      }
      if (!fs.existsSync(j.refs[0])) continue;
      const r = await genart({ out: j.out, refs: j.refs, prompt: j.prompt });
      if (r.ok) { ok++; console.log(`  ok   ${j.id}/${j.mood}  ${Math.round(r.bytes / 1024)} KB`); }
      else { failed.push(`${j.id}/${j.mood}: ${r.error}`); console.log(`  FAIL ${j.id}/${j.mood}  ${r.error.slice(0, 120)}`); }
    }
  }
  console.log(`\n${label}: ${list.length}`);
  await Promise.all(Array.from({ length: Math.min(pool, list.length) }, worker));
  console.log(`${label}: ${ok}/${list.length} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  return failed;
}

const failed = [];
failed.push(...await wave(todo.filter(j => j.mood === 'rest'), 'rest plates'));
// Re-test existence: a mood whose rest plate just failed has no reference to work
// from, and asking for it anyway would spend money on a drawing of nothing.
failed.push(...await wave(todo.filter(j => j.mood !== 'rest' && fs.existsSync(j.refs[0])), 'mood plates'));

console.log(`\n${jobs.length - failed.length} plates on disk · ~$${((todo.length - failed.length) * PRICE).toFixed(2)} spent`);
if (failed.length) {
  console.log('\nFAILED:');
  failed.forEach(f => console.log('  · ' + f));
  process.exit(1);
}

}
