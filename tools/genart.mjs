// Generate an image via the Gemini API (gemini-2.5-flash-image, ~$0.039/image).
// Usage: node tools/genart.mjs <outfile.png> [--ref image.png]... [--ar 4:5] "<prompt>"
//
// ALSO A LIBRARY. `import { genart } from './genart.mjs'` gets the same call as a
// function. The CLI is what gen-character.mjs and gen-turnaround.mjs spawn per
// image, which is right for a chain of four; gen-cutin-art.mjs asks for a hundred
// and thirty-eight in one run, and a batch that size needs three things a spawned
// CLI cannot give it: a concurrency pool, backoff on the API's own 429/503, and a
// failure that RETURNS instead of exiting the process. Rather than let a second
// copy of the endpoint drift away from this one, the endpoint moved in here and
// the CLI became a caller like everybody else. Existing spawners see no change.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const root = path.join(import.meta.dirname, '..');

function apiKey() {
  let env = {};
  try {
    env = Object.fromEntries(
      fs.readFileSync(path.join(root, '.env'), 'utf8')
        .split('\n')
        .filter(l => l.includes('=') && !l.trim().startsWith('#'))
        .map(l => [
          l.slice(0, l.indexOf('=')).trim(),
          l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, ''),
        ])
    );
  } catch { /* no .env: the environment may still carry the key */ }
  return env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;
}

const MODEL = 'gemini-2.5-flash-image';
export const PRICE = 0.039;

/** Generate one image. Returns {ok:true,bytes} or {ok:false,error}. Never exits. */
export async function genart({ out, refs = [], prompt, aspect = null, tries = 4 }) {
  const KEY = apiKey();
  if (!KEY) return { ok: false, error: 'no GEMINI_API_KEY in .env' };

  const parts = [];
  for (const r of refs) {
    parts.push({ inline_data: { mime_type: 'image/png', data: fs.readFileSync(r).toString('base64') } });
  }
  parts.push({ text: prompt });
  const body = JSON.stringify({
    contents: [{ parts }],
    generationConfig: {
      responseModalities: ['IMAGE'],
      ...(aspect ? { imageConfig: { aspectRatio: aspect } } : {}),
    },
  });

  let last = 'unknown';
  for (let t = 0; t < tries; t++) {
    // Backoff is exponential from 2 s and applies only to a RETRY, so every
    // image's first call is immediate — the caller's pool, not a sleep, is what
    // paces a batch.
    if (t) await new Promise(r => setTimeout(r, 2000 * (2 ** (t - 1))));
    let res, j;
    try {
      res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${KEY}`,
        { method: 'POST', headers: { 'content-type': 'application/json' }, body });
      j = await res.json();
    } catch (e) { last = 'fetch: ' + e.message; continue; }
    if (!res.ok) {
      last = 'HTTP ' + res.status + ' ' + JSON.stringify(j).slice(0, 300);
      // A 4xx that is not a rate limit will not become true by being asked again.
      if (res.status >= 400 && res.status < 500 && res.status !== 429) break;
      continue;
    }
    const part = j.candidates?.[0]?.content?.parts?.find(p => p.inlineData || p.inline_data);
    const data = part?.inlineData?.data || part?.inline_data?.data;
    if (!data) {
      // A refusal or a text-only answer. The safety filters are not deterministic,
      // so one more roll is worth it; a third is superstition.
      last = 'no image in response: ' + JSON.stringify(j).slice(0, 300);
      continue;
    }
    const buf = Buffer.from(data, 'base64');
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, buf);
    return { ok: true, bytes: buf.length };
  }
  return { ok: false, error: last };
}

/* ------------------------------------------------------------------ cli ---- */
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const args = process.argv.slice(2);
  const refs = [];
  let outFile = null, aspect = null;
  const promptParts = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--ref') { refs.push(args[++i]); }
    else if (args[i] === '--ar') { aspect = args[++i]; }
    else if (!outFile) outFile = args[i];
    else promptParts.push(args[i]);
  }
  const prompt = promptParts.join(' ');
  if (!outFile || !prompt) { console.error('usage: node tools/genart.mjs out.png [--ref img.png] "prompt"'); process.exit(1); }
  const r = await genart({ out: outFile, refs, prompt, aspect });
  if (!r.ok) { console.error('genart failed:', r.error); process.exit(1); }
  console.log('wrote', outFile, `(${Math.round(r.bytes / 1024)} KB)`);
}
