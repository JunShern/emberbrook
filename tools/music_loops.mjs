// music_loops.mjs — find the loop points for the generated soundtrack and write
// them into public/game/music.json.
//
//   node tools/music_loops.mjs            analyse every looping track, patch music.json
//   node tools/music_loops.mjs battle     just one
//   node tools/music_loops.mjs --dry      print, change nothing
//
// WHY THIS EXISTS: music.js loops on sample-exact loopStart/loopEnd, which is the
// only way a loop is genuinely seamless — but somebody has to CHOOSE those two
// numbers, and choosing them by ear across seven tracks is both slow and not
// reproducible. Lyria hands back a composed piece with an intro and an outro, so
// the honest question is "which two moments in this recording sound most alike?",
// and that is a measurement.
//
// METHOD: decode to mono 22.05 kHz with afconvert (macOS ships it; no ffmpeg here),
// take a 24-band log-spaced spectrum every ~46 ms, then search for the pair of
// times (a, b) whose surrounding context windows are most similar — that pair is a
// place where the music has come back around to the same harmonic and rhythmic
// position, which is exactly what makes a loop seam inaudible. The search is
// coarse-to-fine because the full pair space is ~2M candidates.
//
// The intro is excluded from `a` and the outro decay from `b` by an energy
// envelope, so the loop body never contains the fade-in or the final ritard.
//
// NOTE ON MP3 DECODER DELAY: the browser's decodeAudioData and afconvert can differ
// by ~25 ms of encoder padding at the head of the file. That offset applies equally
// to both loop points, so the loop LENGTH and the seam alignment are unaffected —
// only the absolute position shifts, which is inaudible.
import fs from 'fs';
import path from 'path';
import os from 'os';
import { execFileSync } from 'child_process';

const root = path.join(import.meta.dirname, '..');
const MUSIC = path.join(root, 'public/assets/music');
const JSON_PATH = path.join(root, 'public/game/music.json');

const SR = 22050;
const N = 2048;          // FFT size (~93 ms)
const HOP = 1024;        // ~46 ms
const BANDS = 24;
const CTX = 16;          // context frames each side (~0.75 s) for the similarity cost

// ---- wav ------------------------------------------------------------------
function decode(mp3) {
  const wav = path.join(os.tmpdir(), 'mloop_' + path.basename(mp3) + '.wav');
  execFileSync('/usr/bin/afconvert', ['-f', 'WAVE', '-d', `LEI16@${SR}`, '-c', '1', mp3, wav]);
  const buf = fs.readFileSync(wav);
  fs.unlinkSync(wav);
  let off = 12, dataOff = 0, dataLen = 0;
  while (off < buf.length - 8) {
    const id = buf.toString('latin1', off, off + 4), len = buf.readUInt32LE(off + 4);
    if (id === 'data') { dataOff = off + 8; dataLen = len; break; }
    off += 8 + len + (len & 1);
  }
  const n = Math.min(dataLen, buf.length - dataOff) >> 1;
  const x = new Float32Array(n);
  for (let i = 0; i < n; i++) x[i] = buf.readInt16LE(dataOff + i * 2) / 32768;
  return x;
}

// ---- fft ------------------------------------------------------------------
function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = -2 * Math.PI / len, wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const ur = re[i + k], ui = im[i + k];
        const vr = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci;
        const vi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
        re[i + k] = ur + vr; im[i + k] = ui + vi;
        re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi;
        const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr;
      }
    }
  }
}

// Log-spaced band energies: pitch and timbre move logarithmically, so linear bins
// would let the top octave dominate a comparison that the bass should win.
function features(x) {
  const win = new Float32Array(N);
  for (let i = 0; i < N; i++) win[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (N - 1));
  const edges = [];
  for (let b = 0; b <= BANDS; b++) {
    const f = 40 * Math.pow(8000 / 40, b / BANDS);
    edges.push(Math.max(1, Math.min(N / 2 - 1, Math.round(f * N / SR))));
  }
  const frames = Math.max(0, Math.floor((x.length - N) / HOP));
  const F = [], rms = new Float32Array(frames);
  for (let t = 0; t < frames; t++) {
    const re = new Float32Array(N), im = new Float32Array(N);
    let e = 0;
    for (let i = 0; i < N; i++) { const s = x[t * HOP + i]; e += s * s; re[i] = s * win[i]; }
    rms[t] = Math.sqrt(e / N);
    fft(re, im);
    const v = new Float32Array(BANDS);
    for (let b = 0; b < BANDS; b++) {
      let s = 0;
      for (let k = edges[b]; k < Math.max(edges[b] + 1, edges[b + 1]); k++) s += re[k] * re[k] + im[k] * im[k];
      v[b] = Math.log10(1e-10 + s / Math.max(1, edges[b + 1] - edges[b]));
    }
    // normalise each frame: we want "same harmony/texture", not "same loudness"
    let m = 0; for (let b = 0; b < BANDS; b++) m += v[b]; m /= BANDS;
    let sd = 0; for (let b = 0; b < BANDS; b++) sd += (v[b] - m) * (v[b] - m);
    sd = Math.sqrt(sd / BANDS) || 1;
    for (let b = 0; b < BANDS; b++) v[b] = (v[b] - m) / sd;
    F.push(v);
  }
  return { F, rms, frames };
}

function cost(F, a, b, step) {
  let s = 0, n = 0;
  for (let i = -CTX; i <= CTX; i += step) {
    const fa = F[a + i], fb = F[b + i];
    if (!fa || !fb) return Infinity;
    let d = 0;
    for (let k = 0; k < BANDS; k++) { const t = fa[k] - fb[k]; d += t * t; }
    s += d; n++;
  }
  return n ? s / n : Infinity;
}

function analyse(file) {
  const x = decode(file);
  const dur = x.length / SR;
  const { F, rms, frames } = features(x);
  const sorted = [...rms].sort((p, q) => p - q);
  const med = sorted[sorted.length >> 1] || 1e-6;
  const peak = Math.max(...rms);

  // where the piece is actually playing (excludes the fade-in and the outro decay)
  let first = 0, last = frames - 1;
  while (first < frames && rms[first] < med * 0.45) first++;
  while (last > first && rms[last] < med * 0.45) last--;

  const T = (f) => f * HOP / SR;
  const minLoop = Math.min(30, dur * 0.35);            // seconds of loop body, at least
  const aLo = Math.max(CTX, first + Math.round(2 * SR / HOP));   // 2 s past the first real sound
  const aHi = Math.min(last - CTX, first + Math.round(dur * 0.5 * SR / HOP));
  const bLo = aLo + Math.round(minLoop * SR / HOP);
  const bHi = Math.min(frames - CTX - 1, last);
  const minF = Math.round(minLoop * SR / HOP);

  // The scale of the cost is only meaningful against a baseline: z-scored features
  // put two UNRELATED moments at roughly 2*BANDS. Sampling it makes "seam 1.2" and
  // "seam 5.6" comparable across tracks with different densities, and gives the
  // acceptance check below a threshold that means something.
  let base = 0, bn = 0;
  for (let i = 0; i < 400; i++) {
    const a = aLo + Math.floor(Math.random() * Math.max(1, aHi - aLo));
    const b = bLo + Math.floor(Math.random() * Math.max(1, bHi - bLo));
    const c = cost(F, a, b, 4);
    if (isFinite(c)) { base += c; bn++; }
  }
  base = bn ? base / bn : 1;

  let best = null;
  if (aHi > aLo && bHi > bLo) {
    // Coarse pass keeps the best candidate PER `a` rather than one global winner:
    // on percussive material the coarse grid (186 ms) can straddle the true minimum
    // and a single winner then traps the refinement in the wrong neighbourhood.
    const cands = [];
    for (let a = aLo; a <= aHi; a += 4) {
      let bestB = null;
      for (let b = Math.max(bLo, a + minF); b <= bHi; b += 4) {
        const c = cost(F, a, b, 4);
        if (!bestB || c < bestB.c) bestB = { a, b, c };
      }
      if (bestB) cands.push(bestB);
    }
    cands.sort((p, q) => p.c - q.c);
    for (const cand of cands.slice(0, 40)) {
      for (let a = cand.a - 6; a <= cand.a + 6; a++) {
        for (let b = cand.b - 6; b <= cand.b + 6; b++) {
          if (a < aLo || a > aHi || b > bHi || b - a < minF) continue;
          const c = cost(F, a, b, 1);
          if (!best || c < best.c) best = { a, b, c };
        }
      }
    }
  }
  if (best) best.rel = best.c / base;

  // loudness: RMS over the sounding part, used to even the tracks out by gain
  let e = 0, n = 0;
  for (let t = first; t <= last; t++) { e += rms[t] * rms[t]; n++; }
  const level = Math.sqrt(e / Math.max(1, n));

  return {
    duration: +dur.toFixed(2), level: +level.toFixed(4), peak: +peak.toFixed(3),
    loopStart: best ? +T(best.a).toFixed(3) : null,
    loopEnd: best ? +T(best.b).toFixed(3) : null,
    seam: best ? +best.c.toFixed(3) : null,
    // fraction of the unrelated-pair baseline: <0.1 is a seam you will not hear
    seamRel: best ? +best.rel.toFixed(3) : null,
    intro: +T(first).toFixed(2), outro: +T(last).toFixed(2),
  };
}

// ---- main -----------------------------------------------------------------
const args = process.argv.slice(2);
const dry = args.includes('--dry');
const only = args.filter(a => !a.startsWith('--'));
const cfg = JSON.parse(fs.readFileSync(JSON_PATH, 'utf8'));

const results = {};
for (const [id, t] of Object.entries(cfg.tracks)) {
  if (only.length && !only.includes(id)) continue;
  const file = path.join(root, 'public', t.file);
  if (!fs.existsSync(file)) { console.log(`! ${id}: ${t.file} missing`); continue; }
  const r = analyse(file);
  results[id] = r;
  if (t.loop === false) {
    console.log(`${id.padEnd(11)} ${r.duration}s  one-shot  level ${r.level}`);
  } else {
    console.log(`${id.padEnd(11)} ${r.duration}s  loop ${r.loopStart}s -> ${r.loopEnd}s ` +
      `(body ${(r.loopEnd - r.loopStart).toFixed(1)}s)  seam ${r.seam} rel ${r.seamRel}  level ${r.level}`);
  }
}

// Even the tracks out: aim every track at the same measured level, and let the
// mood ride on the writing rather than on one track simply being louder.
const TARGET = 0.11;
for (const [id, r] of Object.entries(results)) {
  const t = cfg.tracks[id];
  if (t.loop !== false && r.loopStart != null) {
    t.loopStart = r.loopStart; t.loopEnd = r.loopEnd;
    // How much crossfade music.js bakes into the seam. A measured-clean seam still
    // gets a little, because the browser's MP3 decoder and afconvert can disagree by
    // a frame of encoder padding; a weak seam gets enough to cover the join. This is
    // the standard fix and it keeps the loop itself native and gapless — the blend
    // lives in the samples, not in a scheduler that could drift.
    t.loopXfade = r.seamRel == null ? 0.2 : (r.seamRel <= 0.12 ? 0.15 : r.seamRel <= 0.22 ? 0.35 : 0.5);
  }
  t.duration = r.duration;
  const g = Math.max(0.35, Math.min(1.6, TARGET / Math.max(1e-4, r.level)));
  t.gain = +(g * (t.gainTrim || 1)).toFixed(2);
  t.analysis = { level: r.level, peak: r.peak, seam: r.seam, seamRel: r.seamRel, intro: r.intro, outro: r.outro };
}
if (dry) { console.log('\n--dry: music.json untouched'); }
else { fs.writeFileSync(JSON_PATH, JSON.stringify(cfg, null, 2) + '\n'); console.log('\nwrote', path.relative(root, JSON_PATH)); }
