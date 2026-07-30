// genmusic.mjs — generate the Emberbrook soundtrack with Google's Lyria 3 via the
// Gemini API (same .env GEMINI_API_KEY as tools/genart.mjs).
//
//   node tools/genmusic.mjs --all            generate every missing track
//   node tools/genmusic.mjs battle victory   generate just these
//   node tools/genmusic.mjs --force --all    regenerate everything
//   node tools/genmusic.mjs --list           print the track table and exit
//
// WHY TWO MODELS: lyria-3-pro-preview returns a ~150 s composed piece with section
// markers (verses/bridges) — that is a field/battle theme. lyria-3-clip-preview
// returns ~30 s — that is the right raw material for a fanfare or a sting, which we
// then frame-trim (see `trim`). Both hand back audio/mpeg directly, so there is no
// transcode step and no ffmpeg dependency: what the API returns is what ships.
//
// Output: public/assets/music/<id>.mp3 plus <id>.gen.json (prompt, model, response
// section markers, byte/duration facts) so every file's provenance is reproducible.
import fs from 'fs';
import path from 'path';

const root = path.join(import.meta.dirname, '..');
const OUT = path.join(root, 'public/assets/music');

const env = Object.fromEntries(
  fs.readFileSync(path.join(root, '.env'), 'utf8')
    .split('\n')
    .filter(l => l.includes('=') && !l.trim().startsWith('#'))
    .map(l => [
      l.slice(0, l.indexOf('=')).trim(),
      l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, ''),
    ])
);
const KEY = env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;

const PRO = 'lyria-3-pro-preview';    // ~150 s, structured — looping themes
const CLIP = 'lyria-3-clip-preview';  // ~30 s — stingers we trim

// The soundtrack. `brief` is the one-line musical intent that goes in MANIFEST.md;
// `prompt` is what Lyria actually gets. Kept together so the two can never drift.
export const TRACKS = [
  {
    id: 'emberbrook', model: PRO,
    brief: 'Gentle home theme — solo flute over warm strings, 3/4, nostalgic and unhurried.',
    prompt: 'A gentle pastoral village theme for a fantasy role-playing game. Solo wooden flute ' +
      'carrying a simple singable melody over warm sustained strings and soft harp arpeggios. ' +
      'Slow 3/4 waltz, major key, tender and nostalgic, the feeling of coming home to a small ' +
      'village at dusk. Acoustic chamber orchestra, no drums, no vocals, fully instrumental.',
  },
  {
    id: 'dellhollow', model: PRO,
    brief: 'River-town workaday theme — concertina and plucked strings over a water-wheel lilt.',
    prompt: 'A cheerful working river-town theme for a fantasy role-playing game. Lead concertina ' +
      'and pizzicato strings trading a folk melody, acoustic guitar and light hand percussion ' +
      'keeping a steady turning rhythm like a water wheel. Moderate tempo, major key, busy and ' +
      'friendly, market stalls and boat traffic. Folk chamber ensemble, no vocals, instrumental.',
  },
  {
    id: 'valley', model: PRO,
    brief: 'Overworld walking theme — cautiously optimistic, sweet, nostalgic, a little homesick (user brief 2026-07-31).',
    prompt: 'A gentle wandering overworld theme for a fantasy role-playing game. A sweet, wistful '+
      'lead melody on oboe or tin whistle over soft warm strings and quietly fingerpicked '+
      'acoustic guitar, at an unhurried walking pace. Cautiously optimistic and nostalgic, '+
      'tender and a little homesick, like remembering the village you left that morning; '+
      'hopeful but never triumphant, no fanfares, no march. A gentle lilting swing, small '+
      'folk ensemble, intimate and melodic. No vocals, fully instrumental.',
  },
  {
    id: 'interior', model: PRO,
    brief: 'Cozy hearth air — sparse solo harp and clarinet, very soft, room-tone quiet.',
    prompt: 'A quiet cozy indoor theme for a fantasy role-playing game inn or cottage. Very sparse ' +
      'and soft: solo harp with long pauses, a warm low clarinet phrase, faint sustained strings ' +
      'underneath. Slow, gentle, intimate, firelight in a small room. Restful background music ' +
      'that never draws attention. No percussion, no vocals, fully instrumental.',
  },
  {
    id: 'battle', model: PRO,
    brief: 'Driving battle theme — minor key, urgent percussion, brass stabs, relentless strings.',
    prompt: 'An urgent turn-based battle theme for a fantasy role-playing game. Fast driving ' +
      'percussion, relentless minor-key string ostinato, punchy brass stabs on the accents, and ' +
      'a heroic horn melody riding on top. Energetic, tense but exciting, never hopeless. ' +
      'Orchestral with rock drum kit energy. No vocals, fully instrumental.',
  },
  {
    id: 'victory', model: CLIP, trim: 12.0, brief:
      'The fanfare — short, bright, triumphant brass flourish resolving to a warm major chord.',
    prompt: 'A short triumphant victory fanfare for a fantasy role-playing game, starting ' +
      'immediately with no introduction. Bright brass flourish with timpani rolls and a cymbal ' +
      'swell, rising into a broad major-key resolution with full orchestra. Celebratory and ' +
      'proud. No vocals, fully instrumental.',
  },
  {
    id: 'defeat', model: CLIP, trim: 7.0, brief:
      'Somber sting — descending minor strings, the air going out of the room.',
    prompt: 'A short somber defeat sting for a fantasy role-playing game, starting immediately ' +
      'with no introduction. Slow descending minor-key strings with a low mournful cello, a ' +
      'single soft timpani hit, fading into quiet. Sad and final, dignified rather than ' +
      'melodramatic. No vocals, fully instrumental.',
  },
];

// ---- MP3 frame walker -------------------------------------------------------
// Used for two things: reporting true duration (no ffprobe here) and trimming the
// stinger clips. Trimming on a frame boundary is the one edit you can make to an
// MP3 without decoding it — cut anywhere else and the decoder chokes on a partial
// frame. The audible tail is handled at playback time (music.js fades stingers out),
// so a clean structural cut is all this needs to do.
const BITRATES = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320];
const RATES = [44100, 48000, 32000];

export function mp3Frames(buf) {
  let i = 0;
  if (buf.slice(0, 3).toString('latin1') === 'ID3') {
    i = 10 + (((buf[6] & 0x7f) << 21) | ((buf[7] & 0x7f) << 14) | ((buf[8] & 0x7f) << 7) | (buf[9] & 0x7f));
  }
  const frames = [];
  let dur = 0, sr = 0, br = 0;
  while (i < buf.length - 4) {
    if (buf[i] === 0xff && (buf[i + 1] & 0xe0) === 0xe0) {
      const ver = (buf[i + 1] >> 3) & 3, layer = (buf[i + 1] >> 1) & 3;
      const bi = (buf[i + 2] >> 4) & 15, si = (buf[i + 2] >> 2) & 3, pad = (buf[i + 2] >> 1) & 1;
      if (ver === 3 && layer === 1 && bi > 0 && bi < 15 && si < 3) {
        br = BITRATES[bi]; sr = RATES[si];
        const len = Math.floor(144000 * br / sr) + pad;
        if (len > 4) { frames.push({ off: i, len, t: dur }); dur += 1152 / sr; i += len; continue; }
      }
    }
    i++;
  }
  return { frames, dur, sr, br, bytes: buf.length };
}

function trimTo(buf, seconds) {
  const info = mp3Frames(buf);
  if (!info.frames.length || info.dur <= seconds) return buf;
  const cut = info.frames.find(f => f.t >= seconds) || info.frames[info.frames.length - 1];
  return buf.slice(0, cut.off);
}

// ---- generation -------------------------------------------------------------
async function generate(track, attempt = 1) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${track.model}:generateContent?key=${KEY}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ contents: [{ parts: [{ text: track.prompt }] }] }),
  });
  const j = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = j?.error?.message || res.status;
    // 429/5xx are worth another swing; a 400 means the prompt is the problem.
    if (attempt < 3 && (res.status === 429 || res.status >= 500)) {
      const wait = 8000 * attempt;
      console.log(`  ${track.id}: ${res.status}, retrying in ${wait / 1000}s`);
      await new Promise(r => setTimeout(r, wait));
      return generate(track, attempt + 1);
    }
    throw new Error(`${track.id}: API ${res.status} ${msg}`);
  }
  const parts = j.candidates?.[0]?.content?.parts || [];
  const audio = parts.map(p => p.inlineData || p.inline_data).find(Boolean);
  if (!audio?.data) throw new Error(`${track.id}: no audio in response`);
  const sections = parts.filter(p => p.text).map(p => p.text).join(' ').trim();
  return { buf: Buffer.from(audio.data, 'base64'), mime: audio.mimeType || audio.mime_type, sections };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--list')) {
    for (const t of TRACKS) console.log(`${t.id.padEnd(12)} ${t.model.padEnd(24)} ${t.brief}`);
    return;
  }
  if (!KEY) { console.error('no GEMINI_API_KEY in .env'); process.exit(1); }
  const force = args.includes('--force');
  const all = args.includes('--all');
  const want = args.filter(a => !a.startsWith('--'));
  const list = TRACKS.filter(t => all || want.includes(t.id));
  if (!list.length) { console.error('usage: node tools/genmusic.mjs [--all|--force] <id>...'); process.exit(1); }

  fs.mkdirSync(OUT, { recursive: true });
  for (const t of list) {
    const dest = path.join(OUT, `${t.id}.mp3`);
    if (fs.existsSync(dest) && !force) { console.log(`= ${t.id} exists (use --force)`); continue; }
    console.log(`* ${t.id} via ${t.model} ...`);
    let r;
    try { r = await generate(t); }
    catch (e) { console.error(`! ${e.message}`); continue; }

    let buf = r.buf;
    const raw = mp3Frames(buf);
    if (t.trim) buf = trimTo(buf, t.trim);
    const info = mp3Frames(buf);
    fs.writeFileSync(dest, buf);
    fs.writeFileSync(path.join(OUT, `${t.id}.gen.json`), JSON.stringify({
      id: t.id, model: t.model, generated: new Date().toISOString(),
      brief: t.brief, prompt: t.prompt, mime: r.mime, sections: r.sections || null,
      rawSeconds: +raw.dur.toFixed(2), seconds: +info.dur.toFixed(2),
      trimmedTo: t.trim || null, bytes: info.bytes, sampleRate: info.sr, kbps: info.br,
    }, null, 2) + '\n');
    console.log(`  -> ${t.id}.mp3  ${info.dur.toFixed(1)}s  ${(info.bytes / 1024 / 1024).toFixed(2)} MB` +
      (t.trim ? `  (trimmed from ${raw.dur.toFixed(1)}s)` : '') + (r.sections ? `  sections ${r.sections.replace(/\s+/g, ' ')}` : ''));
  }
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
