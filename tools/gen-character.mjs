#!/usr/bin/env node
// The character art playbook: one script generates a character's full art
// set from a small JSON config, in a fixed chain:
//
//   key   (text only)        →  assets/busts/<name>-key.png
//   bust  (ref: key)         →  assets/busts/<name>.png       (colored pencil)
//   expr  (ref: bust, each)  →  assets/busts/<name>-<expr>.png
//   sheet (ref: bust)        →  assets/sprite-<name>.png      (chibi cel 4×4)
//
// Existing outputs are SKIPPED, so iteration = edit the config text and
// reroll only what you're unhappy with:
//
//   node tools/gen-character.mjs june                 # fill in whatever's missing
//   node tools/gen-character.mjs june --redo bust     # reroll the bust (and nothing else)
//   node tools/gen-character.mjs june --redo expr:happy
//   node tools/gen-character.mjs june --redo expr     # all expressions
//   node tools/gen-character.mjs june --redo all
//   node tools/gen-character.mjs june --plan          # show what would run, run nothing
//
// Config: tools/characters/<name>.json — identity text only; every style/
// layout template lives here so all characters share one look.
// Each run updates public/assets/char-manifest.json, which
// public/workflow-characters.html renders (prompt left, image right).

import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';

const root = path.join(import.meta.dirname, '..');
const rel = (p) => path.relative(root, p);

/* ---------- playbook templates (the standardized recipes) ---------- */
const T = {
  key: (c) =>
    `Character portrait bust for a JRPG dialogue box. Half-body, facing slightly toward the viewer, lit by warm lantern light at night, plain very dark brown background, no text, no watermark, no frame, no border. ${c.desc} Art style: modern JRPG key art — crisp anime line work with soft painterly cel shading, glowing warm rim light, rich color depth.`,
  bust: () =>
    `Redraw this exact character faithfully — same face, same features, same hairstyle, same expression, same outfit and colors, same pose and framing — but as a traditional colored pencil drawing on warm toned paper: visible directional pencil strokes, soft cross-hatching in the shadows, waxy layered color, highlights left as bare paper, charming hand-made linework. The background should be a soft warm toned-paper vignette. Absolutely not digital airbrush, no cel shading, no smooth gradients. No text, no watermark, no frame.`,
  expr: (c, text) =>
    `Redraw this exact colored-pencil portrait of the exact same character — same face, same hairstyle, same outfit, same pose and framing, same colored-pencil-on-warm-toned-paper medium and background — changing ONLY the facial expression: ${text}. Every other detail stays identical. No text, no watermark, no frame.`,
  sheet: (c) =>
    `Create a video game character sprite sheet of this exact character (${c.sheetHint}), full body, in crisp cel-shaded anime JRPG style with clean outlines — like a modern Japanese RPG field sprite. Proportions: SLIGHTLY chibi, about 3 heads tall — cute but not extreme, head modestly enlarged, body still elegant. The image is EXACTLY a 4 by 4 grid of equal-size cells on a completely flat uniform bright magenta background (#FF00FF), no gradients, no shadows on the background. Row 1: 4-frame walk cycle facing the viewer (front view) — legs clearly in different positions each frame: right leg forward, passing pose, left leg forward, passing pose. Row 2: the same 4-frame walk cycle from behind (back view). Row 3: the same 4-frame walk cycle in left side profile — legs clearly striding. Row 4: the same 4-frame walk cycle in right side profile. Character perfectly centered in every cell, identical size in every cell, feet on the same baseline. No grid lines, no borders, no text, no labels.`,
};

const DEFAULT_EXPRESSIONS = {
  happy: 'a bright open smile, eyes lit up with warmth',
  worried: 'brows knit together, a small anxious frown, eyes glancing slightly aside',
  surprised: 'wide eyes, raised brows, lips parted in a small gasp',
  determined: 'a firm set jaw, focused steady eyes, the faintest confident smirk',
};

/* ---------- cli ---------- */
const [name, ...flags] = process.argv.slice(2);
if (!name) { console.error('usage: node tools/gen-character.mjs <name> [--redo stage[:sub]]... [--plan]'); process.exit(1); }
const plan = flags.includes('--plan');
const redo = new Set();
for (let i = 0; i < flags.length; i++) if (flags[i] === '--redo') redo.add(flags[++i]);

const cfgPath = path.join(root, 'tools/characters', name + '.json');
if (!fs.existsSync(cfgPath)) { console.error('no config at', rel(cfgPath)); process.exit(1); }
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
cfg.expressions = cfg.expressions || DEFAULT_EXPRESSIONS;
const files = Object.assign({
  key: `public/assets/busts/${name}-key.png`,
  bust: `public/assets/busts/${name}.png`,
  sheet: `public/assets/sprite-${name}.png`,
}, cfg.files || {});
const exprFile = (e) => `public/assets/busts/${name}-${e}.png`;

/* ---------- stage list ---------- */
const stages = [
  { id: 'key', file: files.key, refs: [], prompt: T.key(cfg) },
  { id: 'bust', file: files.bust, refs: [files.key], prompt: T.bust() },
  ...Object.entries(cfg.expressions).map(([e, text]) =>
    ({ id: 'expr:' + e, file: exprFile(e), refs: [files.bust], prompt: T.expr(cfg, text) })),
  { id: 'sheet', file: files.sheet, refs: [files.bust], prompt: T.sheet(cfg) },
];

/* ---------- run ---------- */
const wants = (s) => redo.has('all') || redo.has(s.id) || redo.has(s.id.split(':')[0]) ||
  !fs.existsSync(path.join(root, s.file));
const manifestPath = path.join(root, 'public/assets/char-manifest.json');
const manifest = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : {};
manifest[name] = manifest[name] || { stages: {} };
manifest[name].desc = cfg.desc;

let spent = 0;
for (const s of stages) {
  const run = wants(s);
  const status = run ? (fs.existsSync(path.join(root, s.file)) ? 'REROLL' : 'GENERATE') : 'keep';
  console.log(`${status.padEnd(9)} ${s.id.padEnd(16)} ${s.file}`);
  manifest[name].stages[s.id] = {
    file: s.file.replace('public/', ''),
    refs: s.refs.map(r => r.replace('public/', '')),
    prompt: s.prompt,
    generatedAt: run && !plan ? new Date().toISOString() : (manifest[name].stages[s.id]?.generatedAt || null),
  };
  if (!run || plan) continue;
  for (const r of s.refs) {
    if (!fs.existsSync(path.join(root, r))) { console.error(`  !! missing ref ${r} — run its stage first`); process.exit(1); }
  }
  const args = [path.join(root, 'tools/genart.mjs'), path.join(root, s.file)];
  for (const r of s.refs) args.push('--ref', path.join(root, r));
  args.push(s.prompt);
  execFileSync('node', args, { stdio: 'inherit' });
  spent++;
}
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(`\n${plan ? 'plan only — nothing generated' : spent + ' image(s) generated (~$' + (spent * 0.039).toFixed(2) + ')'} · manifest updated`);
console.log('review at http://localhost:3000/workflow-characters.html');
