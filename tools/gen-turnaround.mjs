// gen-turnaround.mjs — CHARACTER FACTORY, stage 1: image-to-3D turnaround sets.
//
//   node tools/gen-turnaround.mjs lake pip maren        # named characters
//   node tools/gen-turnaround.mjs --all                 # every tools/characters/*.json
//   node tools/gen-turnaround.mjs lake --redo back      # re-roll one view (or --redo all)
//   node tools/gen-turnaround.mjs lake --style path.jpg # different style anchor
//   node tools/gen-turnaround.mjs --dry                 # print the plan, generate nothing
//
// WHAT IT MAKES: public/assets/characters/<name>/turnaround/{front,left,right,back}.png
// — a neutral A-pose set in ONE shared render style, which is exactly what
// image-to-3D wants (multiview conditioning). Views are IDENTITY-CHAINED:
// front is conditioned on the character's own bust (+ pose art if present) and
// the STYLE ANCHOR; left/right/back are conditioned on that front, so the
// character stays themselves from every angle.
//
// STYLE ANCHOR (default): public/assets/refs/vesper_apose_front.jpg — the
// user-authored Vesper A-pose whose render style (soft painterly 3D toon,
// ~5-head proportions, flat gray studio) is the proportion/style canon the
// user ratified 2026-07-31. Change it deliberately, for everyone at once.
//
// THE FACTORY CHAIN this feeds (per character):
//   1. THIS TOOL       -> turnaround set (user reviews/re-rolls the art here)
//   2. Tripo           -> mesh+rig: user via web app, or tools/gen3d.mjs --views
//   3. normalization   -> skeleton repair (broken exports; see vesper_fix_glb.py),
//                         scale/origin/facing
//   4. retarget        -> Idle/Walking_A/Jump from the library, with the measured
//                         pose gates (arms <=15 deg off vertical at idle, etc.)
//   5. in-game         -> MODELS registry / npcs.json body slot
//
// CHARACTER IDENTITY comes from tools/characters/<name>.json:
//   - desc                 (required) the canonical visual description
//   - turnaround.extraNote (optional) details the bust can't show (footwear,
//                          held props, cape length...) appended to the prompt
//   - turnaround.skip      (optional true) exclude from --all (e.g. animals
//                          whose body plan won't survive a humanoid A-pose)
//
// Image generation itself is delegated to tools/genart.mjs (one implementation
// of the Gemini image call, refs, retries). PROMPT RULES learned the hard way:
// describe style by attributes, never name third-party IP; full-scene style
// refs pass content filters, close character crops may not; keep lighting flat
// and even or it bakes into the 3D texture.
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';

const root = path.join(import.meta.dirname, '..');
const args = process.argv.slice(2);
const DRY = args.includes('--dry');
const ALL = args.includes('--all');
const redoIx = args.indexOf('--redo');
const REDO = redoIx >= 0 ? (args[redoIx + 1] || 'all') : null;
const styleIx = args.indexOf('--style');
const STYLE = styleIx >= 0 ? args[styleIx + 1]
  : 'public/assets/refs/vesper_apose_front.jpg';
const names = args.filter((a, i) => !a.startsWith('--')
  && !(redoIx >= 0 && i === redoIx + 1) && !(styleIx >= 0 && i === styleIx + 1));

const charDir = path.join(root, 'tools/characters');
const roster = ALL
  ? fs.readdirSync(charDir).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''))
  : names;
if (!roster.length) { console.error('usage: gen-turnaround.mjs <names...> | --all  [--redo view|all] [--style ref] [--dry]'); process.exit(1); }

const VIEWS = {
  front: null, // special-cased below
  left:  'rotated to an exact LEFT PROFILE side view',
  right: 'rotated to an exact RIGHT PROFILE side view',
  back:  'rotated to a direct BACK view',
};
// "hands empty" is a hard rule for every turnaround: held props (Pip's walking stick)
// fuse into the mesh during image-to-3D conversion and break the rig.
const TAIL = 'hands empty and open at the sides holding nothing, full body head to toe visible with a clear readable body silhouette, plain flat light gray studio background, soft even studio lighting, no text, no watermark';

function gen(out, refs, prompt) {
  if (DRY) { console.log('[dry]', out, '\n  refs:', refs.join(', ')); return true; }
  try {
    execFileSync('node', ['tools/genart.mjs', out,
      ...refs.flatMap(r => ['--ref', r]), '--ar', '3:4', prompt],
      { cwd: root, stdio: 'inherit' });
    return fs.existsSync(path.join(root, out));
  } catch (e) { console.error('  FAILED', out, e.status ?? e.message); return false; }
}

let made = 0, skipped = 0, failed = 0;
for (const name of roster) {
  const cfgPath = path.join(charDir, name + '.json');
  if (!fs.existsSync(cfgPath)) { console.error(`no config tools/characters/${name}.json — skipping`); failed++; continue; }
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  if (ALL && cfg.turnaround?.skip) { console.log(`${name}: turnaround.skip — excluded from --all`); skipped++; continue; }
  const desc = [cfg.desc, cfg.turnaround?.extraNote].filter(Boolean).join(' ');
  const dir = `public/assets/characters/${name}/turnaround`;
  fs.mkdirSync(path.join(root, dir), { recursive: true });

  const idRefs = [`public/assets/characters/${name}/bust.png`,
    `public/assets/characters/${name}/pose.png`,
    `public/assets/characters/${name}/pose-front.png`]
    .filter(r => fs.existsSync(path.join(root, r)));
  if (!idRefs.length) { console.error(`${name}: no bust/pose art — generate the bust first (gen-character.mjs)`); failed++; continue; }
  // STALE-REF GUARD (2026-08-02, measured on Lake). This passes EVERY identity ref
  // it finds, and a redesigned character leaves the old ones on disk: Lake's
  // pose.png was the pre-redesign man (black cropped hair, July 19) while bust.png
  // was the new one, so the model was conditioned on two different people at once
  // and returned a BLEND — not drift, a genuine third face. The cut-in pipeline
  // measured this same failure (two refs at different framings blend identities).
  // A ref materially older than the bust is a redesign leftover until proven
  // otherwise, so say so loudly rather than silently averaging two characters.
  {
    const bustM = fs.statSync(idRefs[0]).mtimeMs;
    for (const r of idRefs.slice(1)) {
      const age = (bustM - fs.statSync(r).mtimeMs) / 86400000;
      if (age > 1) console.warn(`  ⚠ ${name}: ${r} is ${age.toFixed(0)} day(s) OLDER than bust.png — ` +
        `if this character was redesigned, that is a stale ref and it WILL blend two faces. ` +
        `Move it aside and re-run.`);
    }
  }

  for (const view of Object.keys(VIEWS)) {
    const out = `${dir}/${view}.png`;
    const exists = fs.existsSync(path.join(root, out));
    if (exists && REDO !== 'all' && REDO !== view) { skipped++; continue; }
    let ok;
    if (view === 'front') {
      ok = gen(out, [STYLE, ...idRefs],
        `A 3D game character render in exactly the rendering style, proportions, material quality and studio presentation of the FIRST reference image (soft painterly 3D toon shading, about 5 heads tall, plain light gray studio background). The character depicted is the one from the other reference image(s): ${desc}. Standing in a neutral A-pose, arms slightly away from the body, facing directly forward, ${TAIL}`);
    } else {
      if (!fs.existsSync(path.join(root, `${dir}/front.png`))) { console.error(`${name}: no front to chain ${view} from`); failed++; continue; }
      ok = gen(out, [`${dir}/front.png`],
        `The exact same 3D-rendered character as the reference image, same neutral A-pose, same style, same proportions, same outfit and colors, ${VIEWS[view]}, ${TAIL}`);
    }
    ok ? made++ : failed++;
  }
  // record the stage in the character manifest so the workflow page can show it
  if (!DRY) {
    const manPath = path.join(root, 'public/assets/char-manifest.json');
    try {
      const man = JSON.parse(fs.readFileSync(manPath, 'utf8'));
      man[name] = man[name] || { stages: {} };
      man[name].stages = man[name].stages || {};
      man[name].stages.turnaround = {
        views: Object.keys(VIEWS).filter(v => fs.existsSync(path.join(root, `${dir}/${v}.png`)))
          .map(v => `assets/characters/${name}/turnaround/${v}.png`),
        styleAnchor: STYLE,
      };
      fs.writeFileSync(manPath, JSON.stringify(man, null, 2));
    } catch (e) { console.error('manifest update failed (non-fatal):', e.message); }
  }
}
console.log(`turnarounds: ${made} generated, ${skipped} skipped (exist), ${failed} failed`);
process.exit(failed ? 1 : 0);
