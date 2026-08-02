#!/usr/bin/env node
// gen-cutin-base.mjs — OUTPAINT A BASE PLATE WHEN THE BUST DEFEATS THE PROMPT.
//
//   node tools/gen-cutin-base.mjs vesper                      # donor: shipped cutin.png
//   node tools/gen-cutin-base.mjs mara --donor path/to.png    # explicit donor
//   node tools/gen-cutin-base.mjs vesper --dry                # build the ref, no API call
//
// WHY THIS EXISTS (2026-08-01, the second Vesper pass). gemini-2.5-flash-image is
// image-conditioned to the point of composition lock: with bust.png as the single
// reference, FOUR different prompt recipes — the original, one that named the
// failure out loud ("do NOT copy the reference's crop"), one reordered to put
// FRAMING before IDENTITY, and one with the dialogue-box imagery stripped from the
// opener — produced the same sculpted head-and-shoulders bust, bot_cut 0.69 to the
// SAME two decimals every time, while a reference change (a padded canvas) changed
// the output completely and LITERALLY, tan filler band and all. The lever is the
// reference; prose does not reach the crop.
//
// So this tool makes literal copying the winning move. It builds a reference that
// already IS the target contract, minus the missing body:
//   1. take a donor image of the character (default: the shipped cutin.png — its
//      likeness and medium are ratified even where its framing was rejected),
//   2. slice off the donor's rounded bottom taper at the lowest row still >= 92%
//      of the lower body's max width — a clean straight cut through opaque torso,
//   3. paste it top-anchored on a pure #FF00FF canvas with ~1/3 empty key below,
//   4. ask the model to CONTINUE the drawing down through the empty key to the
//      waist and end in a straight horizontal slice at the bottom edge.
// The first Vesper roll under this recipe passed all three gates on the spot
// (shoulder 0.228, bot_cut 1.07, halo -20.0, key residue 0.0) after five straight
// bust.png-referenced failures.
//
// The result is written to studio/rest.png — the base plate the whole expression
// set then references via gen-cutin-art.mjs. Screen it BY EYE before drawing the
// moods: this file exists precisely because a reference propagates everything.
import fs from 'fs';
import os from 'os';
import path from 'path';
import { genart } from './genart.mjs';

// The composite is built by a Python helper — the repo has no node PNG dep and
// vendoring one for a paste is not worth it. See buildRef().
import { execFileSync } from 'child_process';

const root = path.join(import.meta.dirname, '..');
const CHARS = path.join(root, 'public/assets/characters');

const argv = process.argv.slice(2);
const id = argv.find(a => !a.startsWith('--'));
const dry = argv.includes('--dry');
const di = argv.indexOf('--donor');
if (!id) { console.error('usage: gen-cutin-base.mjs <character> [--donor <png>] [--dry]'); process.exit(1); }
const donor = di >= 0 ? argv[di + 1] : path.join(CHARS, id, 'cutin.png');
if (!fs.existsSync(donor)) { console.error(`no donor image: ${donor}`); process.exit(1); }
// The ref lives OUTSIDE studio/: gen-cutin.py's studio_sources treats every png in
// that directory as a mood plate, and a stray helper file there would be matted,
// gated and shipped as an expression called "_baseref".
const outRef = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'cutin-base-')), id + '-baseref.png');
const outBase = path.join(CHARS, id, 'studio', 'rest.png');

function buildRef() {
  fs.mkdirSync(path.dirname(outRef), { recursive: true });
  execFileSync('python3', ['-c', `
import sys
import numpy as np
from PIL import Image
donor, out = sys.argv[1], sys.argv[2]
im = Image.open(donor).convert('RGBA')
a = np.asarray(im)
solid = a[..., 3] > 128
rows = solid.sum(axis=1)
H, W = solid.shape
torso_w = rows[int(H * 0.5):].max()
wide = np.flatnonzero(rows >= 0.92 * torso_w)
cut = int(wide[-1]) if len(wide) else H - 1
fig = a[:cut + 1]
mw = mh = 1024
fh, fw = fig.shape[0], fig.shape[1]
# 0.66 -> 0.52 (2026-08-01, waist-up audit): at 0.66 the chest-up donor's head
# landed at 0.38 of the canvas (spec 0.28-0.34) and every roll inherited a
# chest-up crop from it — the head fraction is donor_head_frac * this scale, and
# the shipped donor's head is ~0.58 of its own height, so 0.52 puts the head at
# ~0.30 and leaves real room for torso down to the hips.
s = min((mw - 90) / fw, (mh * 0.52) / fh)
figim = Image.fromarray(fig, 'RGBA').resize((int(fw * s), int(fh * s)), Image.LANCZOS)
canvas = Image.new('RGBA', (mw, mh), (255, 0, 255, 255))
canvas.alpha_composite(figim, ((mw - figim.width) // 2, 18))
canvas.convert('RGB').save(out, optimize=True)
print('ref %dx%d, figure ends y=%d' % (mw, mh, 18 + figim.height))
`, donor, outRef], { stdio: 'inherit' });
}

const PROMPT = [
  'Complete this unfinished JRPG character portrait. The character is already drawn',
  'from the head down to mid-torso, where the drawing stops abruptly in a straight',
  'horizontal cut; the area below that cut is empty flat magenta. CONTINUE the',
  'drawing seamlessly downward through that empty magenta area: extend the clothing,',
  'any straps, and both sleeves down past the stomach to the WAIST, at the top of',
  'the hips, in exactly the same drawing medium, linework, colours and lighting as',
  'the existing drawing. Do not change anything already drawn: the same face, the',
  'same hair, the same clothes, untouched. The completed figure is then sliced off',
  'by the BOTTOM EDGE of the image in one clean, perfectly straight horizontal line',
  'at the waist: fully opaque torso right down to the bottom edge, full width, no',
  'rounded taper, no narrowing, no fading. The background stays a single perfectly',
  'flat, uniform, solid pure bright magenta (#FF00FF) from edge to edge and corner',
  'to corner. No text, no watermark, no frame, no border, no signature.',
].join(' ');
// DO NOT ADD AN EMPTY-HANDS CLAUSE HERE. It was tried on 2026-08-02, across twelve
// NPCs, and it is REFUTED — recorded because it is the obvious next idea and it is
// the wrong one.
//
// The problem it was aimed at is real: the donors are the shipped salvage cut-outs,
// salvaged in turn from busts drawn while props were still allowed, so the outpaint
// faithfully preserves Sorrel's peel, Creel's rope, Elder-woman's knitting and
// Hobb's coil — and since the MOOD prompt bans held objects, the set ends up with a
// prop that sits in the resting portrait and vanishes the moment the character feels
// anything. The fix looked like one sentence: hold nothing, and if the drawing shows
// something held, remove it and redraw the hand empty.
//
// What came back, on the same donors that had just produced gate-passing bases:
// Odessa and Creel DECAPITATED — a torso and a hand, no head at all.
//
// THE ATTRIBUTION WAS THEN CHECKED, because the same batch also looked wrong in
// ways that had nothing to do with the clause, and reading them all as one failure
// would have been the confabulation this repo keeps warning about. Re-rolling the
// clause-free prompt reproduced the anthropomorphic Mochi, the modern jackets on
// Finn/Fisher/Armorer/Weaponsmith and Pip's shouldered stick EXACTLY — so those come
// from the DONOR (each character's shipped salvage cut-out is their real design, or
// in Mochi's case a cat that this recipe insists on giving a waist), and the clause
// owns only the decapitation. Recorded that way: one effect, one cause.
//
// The mechanism is this file's own thesis turned against it. The recipe works
// because it asks for LITERAL COPYING — "do not change anything already drawn" is
// what pins identity, medium and crop simultaneously. An instruction to REMOVE
// something contradicts that clause head-on, and the model resolves the
// contradiction by treating the whole figure as re-drawable, head included. There is
// no wording of "change this one thing" that does not cost the copying.
//
// So the prop stays, and it is the cheaper defect: a resting portrait holding a tool
// is odd, a headless one is unusable. If the props ever have to go, the lever is the
// DONOR — hand a prop-free donor in with --donor — not the prompt.
//
// AND THIS RECIPE IS FOR PEOPLE. A character whose spec declares its own `framing`
// is not promised a waist: outpainting Mochi "down to the waist, at the top of the
// hips" produces an upright cat in a robe, every time, because the instruction has
// no other reading. Those characters take the ordinary gen-cutin-art.mjs rest path,
// which uses their own framing text.

buildRef();
if (dry) { console.log('ref at ' + outRef + ' — dry run, no API call'); process.exit(0); }
fs.mkdirSync(path.dirname(outBase), { recursive: true });
const r = await genart({ out: outBase, refs: [outRef], prompt: PROMPT });
if (!r.ok) { console.error('FAIL ' + r.error); process.exit(1); }
console.log(`base written: ${path.relative(root, outBase)}  ${Math.round(r.bytes / 1024)} KB — screen it BY EYE before drawing moods`);
