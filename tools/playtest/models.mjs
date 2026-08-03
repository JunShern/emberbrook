/* models.mjs — THE MODEL SEAM. The one thing in the playtester that is genuinely
 * pluggable, because the user asked for exactly one thing to be:
 *
 *   "We should also make it pretty easy to swap in and out different LLM models
 *    that drive the playtester, because we will want to benchmark different models
 *    to find the Pareto optimum for cost and effectiveness."  (user, 2026-08-03)
 *
 * A model is:
 *     { id, provider, model, ask({images, text, temperature}) -> {text, usage} }
 *
 * `images` is [{mime, data}] with data base64. `text` is a prompt. The reply is
 * expected to be JSON; enforcing that is the provider's business. `usage` is
 * {in, out, thought, ms} and is accumulated by the Usage class below so a run can
 * report tokens measured rather than cost guessed.
 *
 * NOTHING ELSE IN THE PLAYTESTER KNOWS A PROVIDER NAME. Swapping the model is
 * `--player-model=gemini:gemini-3.5-flash` on the command line; layers 2 and 3
 * (the adapter, the episode runner) are untouched.
 *
 * ADDING A SECOND PROVIDER is one function and one entry in PROVIDERS: take
 * {images, text, temperature}, post it, return {text, usage}. The two shapes that
 * differ in practice are how images are attached and where token counts live in
 * the response; everything else is already normalised here. Nothing is abstracted
 * beyond that on purpose — a general plugin system for one game is how a week
 * disappears (YAGNI, and the user said so).
 *
 * PINNING. nav_eval and scene_redteam both pin their judge and both say why: an
 * alias like `gemini-flash-latest` MOVES under you and every number recorded
 * against it silently stops being comparable to the one above it. The playtester
 * pins the same way — see tools/llm_playtester.mjs's header for which models and
 * the bake-off that chose them. `latest` aliases are refused here, loudly, rather
 * than quietly poisoning a benchmark.
 */
import { readFileSync } from 'fs';
import { join, dirname } from 'path';

const ROOT = join(dirname(new URL(import.meta.url).pathname), '../..');

/* Prices are an ASSUMPTION and are labelled as one everywhere they surface. THE
 * MEASUREMENT IS TOKENS; cost is tokens times a number that changes without
 * telling anyone. USD per million tokens. Override with --price-in / --price-out
 * if these have moved. */
export const PRICES = {
  'gemini-3.6-flash': { in: 0.30, out: 2.50 },
  'gemini-3.5-flash': { in: 0.30, out: 2.50 },
  'gemini-3.5-flash-lite': { in: 0.10, out: 0.40 },
  'gemini-3.1-flash-lite': { in: 0.10, out: 0.40 },
  'gemini-3.1-pro-preview': { in: 1.25, out: 10.00 },
  'gemini-3-pro-preview': { in: 1.25, out: 10.00 },
  _default: { in: 0.30, out: 2.50 },
};
export const priceOf = (m) => PRICES[m] || PRICES._default;

export class Usage {
  constructor() { this.calls = 0; this.in = 0; this.out = 0; this.thought = 0; this.ms = 0; this.byModel = {}; }
  add(id, u) {
    this.calls++; this.in += u.in || 0; this.out += u.out || 0; this.thought += u.thought || 0; this.ms += u.ms || 0;
    const m = this.byModel[id] || (this.byModel[id] = { calls: 0, in: 0, out: 0, thought: 0, ms: 0 });
    m.calls++; m.in += u.in || 0; m.out += u.out || 0; m.thought += u.thought || 0; m.ms += u.ms || 0;
  }
  /* Billed output includes thinking tokens; leaving them out understates a
   * reasoning model by more than half, which would make exactly the wrong model
   * look cheap in a Pareto plot. */
  estUSD() {
    let t = 0;
    for (const [id, m] of Object.entries(this.byModel)) {
      const p = priceOf(id.split(':').pop());
      t += (m.in / 1e6) * p.in + ((m.out + m.thought) / 1e6) * p.out;
    }
    return +t.toFixed(4);
  }
  report() {
    const L = [`${this.calls} calls, ${this.in} in / ${this.thought} thought / ${this.out} out tokens, ` +
      `${(this.ms / 1000).toFixed(0)} s of API latency, ~$${this.estUSD()} (ASSUMED prices, see models.mjs)`];
    for (const [id, m] of Object.entries(this.byModel))
      L.push(`    ${id}: ${m.calls} calls  ${m.in} in  ${m.thought} thought  ${m.out} out  ${(m.ms / 1000).toFixed(0)} s`);
    return L.join('\n');
  }
}

function envKey(name) {
  try {
    const env = Object.fromEntries(readFileSync(join(ROOT, '.env'), 'utf8').split('\n')
      .filter(l => l.includes('=') && !l.trim().startsWith('#'))
      .map(l => [l.slice(0, l.indexOf('=')).trim(), l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]));
    return env[name] || process.env[name];
  } catch { return process.env[name]; }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

const PROVIDERS = {
  /* Gemini via generativelanguage — the same endpoint, key source and retry ladder
   * nav_eval.mjs and scene_redteam.mjs use. GEMINI_API_KEY out of .env. */
  gemini(model) {
    return async function ask({ images = [], text, temperature = 0.5 }) {
      const KEY = envKey('GEMINI_API_KEY');
      if (!KEY) throw new Error('no GEMINI_API_KEY in .env');
      const parts = images.map(i => ({ inline_data: { mime_type: i.mime, data: i.data } }));
      parts.push({ text });
      const body = { contents: [{ parts }], generationConfig: { temperature, responseMimeType: 'application/json' } };
      let last = null;
      for (let a = 0; a < 4; a++) {
        const t0 = Date.now();
        const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${KEY}`,
          { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
        const j = await res.json().catch(() => ({}));
        const ms = Date.now() - t0;
        if (res.ok) {
          const u = j.usageMetadata || {};
          const t = (j.candidates?.[0]?.content?.parts || []).map(p => p.text || '').join('');
          if (t.trim()) return { text: t, usage: { in: u.promptTokenCount || 0, out: u.candidatesTokenCount || 0, thought: u.thoughtsTokenCount || 0, ms } };
          last = 'empty reply ' + JSON.stringify(j).slice(0, 200);
        } else {
          last = `HTTP ${res.status} ` + JSON.stringify(j).slice(0, 300);
          if (res.status !== 429 && res.status < 500) break;
        }
        await sleep(1200 * (a + 1) * (a + 1));
      }
      throw new Error(last || 'gemini failed');
    };
  },
  /* The null provider: replies with a fixed intent. It exists so the whole rig can
   * be exercised with no key and no network, and so "the API is down" is never
   * mistaken for "the harness is broken". */
  stub() {
    return async () => ({ text: JSON.stringify({ see: 'stub', goal: 'stub', action: 'wait', ms: 300 }),
      usage: { in: 0, out: 0, thought: 0, ms: 0 } });
  },
};

/** makeModel('gemini:gemini-3.6-flash') or makeModel('stub'). */
export function makeModel(spec) {
  const s = String(spec || '').trim();
  const i = s.indexOf(':');
  const provider = i < 0 ? (s === 'stub' ? 'stub' : 'gemini') : s.slice(0, i);
  const model = i < 0 ? (s === 'stub' ? 'stub' : s) : s.slice(i + 1);
  const mk = PROVIDERS[provider];
  if (!mk) throw new Error(`unknown provider "${provider}". Have: ${Object.keys(PROVIDERS).join(', ')}`);
  if (/latest$/.test(model))
    throw new Error(`refusing the moving alias "${model}". PIN the model: an alias changes under you and ` +
      'every benchmark number recorded against it silently stops being comparable.');
  return { id: `${provider}:${model}`, provider, model, ask: mk(model) };
}

/** Tolerant JSON extraction — a model that wraps its object in prose is still useful. */
export function parseJson(text) {
  try { return JSON.parse(text); } catch (e) { }
  const m = /\{[\s\S]*\}/.exec(String(text || ''));
  if (m) { try { return JSON.parse(m[0]); } catch (e) { } }
  return null;
}
