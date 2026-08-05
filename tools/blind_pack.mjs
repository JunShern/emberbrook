#!/usr/bin/env node
/* blind_pack.mjs — pack images into an ANONYMIZED judging set.
 *
 * The problem this exists for (2026-08-04): the gauntlet loop's "blind" critics
 * were never blind. The neutral A/B/C/D labels sat on top of file paths that
 * said everything — `docs/qa/ow-refs/plates/r13-meadow.png` vs
 * `public/assets/refs/reimagine_ff9_overworld_1.jpg` — and later prompts
 * labelled images OURS / THE BAR outright and listed the previous critics'
 * charges to "confirm". A judge that knows which image is the client's and
 * what it is supposed to find does not produce findings, it produces
 * confirmations. The user caught it by reading a prompt.
 *
 * What this does:
 *   - copies each input to <outdir>/img-<letter>.png in SHUFFLED order
 *     (Fisher-Yates on a seed from the clock, letters a..z)
 *   - re-encodes everything to PNG at a common max long-edge via `sips`
 *     (macOS), stripping EXIF/metadata, so format and resolution stop leaking
 *     which images share a source
 *   - writes <outdir>/mapping.json — FOR THE COORDINATOR ONLY. Never give the
 *     judge the mapping, the outdir listing timestamps, or this script's name
 *     in the prompt.
 *
 * What this cannot do, said honestly: a reference screenshot of a released
 * game carries its own tells (UI, watermarks, recognizable characters). True
 * blindness to WHICH GAME is impossible; what this removes is the ownership
 * framing ("ours" vs "the bar") and the path leak. The judging prompt must do
 * the rest: no charge lists, no expected artifacts, no deltas in stage 1.
 * Stage 2 (targeted questions) happens only AFTER stage-1 answers are
 * recorded, via a follow-up message.
 *
 * Usage:
 *   node tools/blind_pack.mjs --out <dir> <img1> <img2> ...
 *   prints the letter->source mapping to stdout (coordinator's copy).
 */
import { execFileSync } from 'child_process';
import { mkdirSync, writeFileSync, rmSync, existsSync } from 'fs';
import { join, resolve } from 'path';

const args = process.argv.slice(2);
const oi = args.indexOf('--out');
if (oi < 0 || args.length < oi + 2) {
  console.error('usage: node tools/blind_pack.mjs --out <dir> <img...>');
  process.exit(2);
}
const outdir = resolve(args[oi + 1]);
const inputs = args.filter((a, i) => i !== oi && i !== oi + 1 && !a.startsWith('--'));
const MAXEDGE = args.find(a => a.startsWith('--maxedge='))?.split('=')[1] || '1600';
if (inputs.length < 2) { console.error('need at least 2 images'); process.exit(2); }
if (inputs.length > 26) { console.error('max 26 images'); process.exit(2); }
for (const f of inputs) if (!existsSync(f)) { console.error('missing: ' + f); process.exit(2); }

rmSync(outdir, { recursive: true, force: true });
mkdirSync(outdir, { recursive: true });

// Fisher-Yates
const order = inputs.map((_, i) => i);
for (let i = order.length - 1; i > 0; i--) {
  const j = Math.floor(Math.random() * (i + 1));
  [order[i], order[j]] = [order[j], order[i]];
}

const letters = 'abcdefghijklmnopqrstuvwxyz';
const mapping = {};
order.forEach((srcIdx, pos) => {
  const name = `img-${letters[pos]}.png`;
  const dst = join(outdir, name);
  // sips: convert to png, cap the long edge, and (by re-encoding) drop metadata.
  execFileSync('sips', ['-s', 'format', 'png', '-Z', MAXEDGE, resolve(inputs[srcIdx]), '--out', dst],
    { stdio: ['ignore', 'ignore', 'inherit'] });
  mapping[name] = inputs[srcIdx];
});

writeFileSync(join(outdir, 'mapping.json'), JSON.stringify(mapping, null, 1));
console.log('packed ' + inputs.length + ' images -> ' + outdir);
for (const [k, v] of Object.entries(mapping)) console.log('  ' + k + '  <-  ' + v);
console.log('\nmapping.json is the COORDINATOR\'S copy. Do not name it, the sources,');
console.log('or this tool in the judging prompt. Stage-1 prompt gets: the outdir');
console.log('files, the task, and NOTHING about ownership, history, or expected flaws.');
