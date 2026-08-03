/* gauntlet_gallery.mjs — build docs/qa/gauntlet/index.html from what is on disk.
 *
 * The user asked for "a page that shows screenshots from each iteration of the loop,
 * round 0 (before), then round 1, etc., multiple screenshots per round." This builds
 * exactly that and NOTHING ELSE: it reads rounds.json and the plates directory, and
 * it never invents a round. A round with no plates yet renders as "not yet captured"
 * rather than being silently skipped — a gallery that hides a missing round is a
 * gallery that lies about progress, which is the whole thing this page exists to show.
 *
 *   node tools/gauntlet_gallery.mjs
 */
import { readFileSync, writeFileSync, existsSync, readdirSync } from 'fs';
import { join } from 'path';

const ROOT = new URL('..', import.meta.url).pathname;
const OUT = join(ROOT, 'docs/qa/gauntlet/index.html');
const ROUNDS = join(ROOT, 'docs/qa/gauntlet/rounds.json');
const PLATES = join(ROOT, 'docs/qa/ow-refs/plates');
const rounds = JSON.parse(readFileSync(ROUNDS, 'utf8'));
const have = existsSync(PLATES) ? readdirSync(PLATES) : [];

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const rel = p => '../' + p.replace(/^docs\/qa\//, '');

let body = '';
for (const r of rounds.rounds) {
  const shots = (r.views || []).map(v => {
    const f = r.prefix ? `${r.prefix}-${v}.png` : null;
    const ok = f && have.includes(f);
    return { v, f, ok, src: ok ? rel(`docs/qa/ow-refs/plates/${f}`) : null };
  });
  const captured = shots.filter(s => s.ok).length;
  body += `<section class="round">
    <h2>Round ${esc(r.n)} — ${esc(r.title)}</h2>
    <p class="when">${esc(r.when || '')} &middot; ${captured}/${shots.length} frames captured</p>
    ${r.verdict ? `<p class="verdict"><b>Critic verdict:</b> ${esc(r.verdict)}</p>` : ''}
    ${r.deficits ? `<div class="deficits"><b>What the critic asked for</b><ol>${r.deficits.map(d => `<li>${esc(d)}</li>`).join('')}</ol></div>` : ''}
    <div class="grid">${shots.map(s => s.ok
      ? `<figure><a href="${s.src}"><img src="${s.src}" alt="${esc(s.v)}"></a><figcaption>${esc(s.v)}</figcaption></figure>`
      : `<figure class="missing"><div class="ph">not yet captured</div><figcaption>${esc(s.v)}</figcaption></figure>`).join('')}</div>
  </section>`;
}

const refs = (rounds.references || []).map(p =>
  `<figure><a href="${rel(p)}"><img src="${rel(p)}" alt="reference"></a><figcaption>${esc(p.split('/').pop())}</figcaption></figure>`).join('');

writeFileSync(OUT, `<!doctype html><meta charset="utf-8"><title>Overworld gauntlet loop</title>
<style>
 body{background:#14161a;color:#dfe3ea;font:15px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;padding:32px 40px;max-width:1600px}
 h1{font-size:26px;margin:0 0 4px} h2{font-size:19px;margin:0 0 2px;color:#fff}
 .lede{color:#9aa3b2;margin:0 0 28px;max-width:80ch}
 .round{border-top:1px solid #2a2f38;padding:26px 0}
 .when{color:#7d8798;font-size:13px;margin:0 0 10px}
 .verdict{background:#1c2029;border-left:3px solid #5b8dd6;padding:9px 14px;margin:0 0 12px;border-radius:0 4px 4px 0}
 .deficits{background:#1a1d24;padding:10px 16px;border-radius:5px;margin:0 0 16px}
 .deficits ol{margin:6px 0 0;padding-left:20px} .deficits li{margin:3px 0;color:#c3cad6}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
 figure{margin:0}
 img{width:100%;border-radius:5px;display:block;border:1px solid #2a2f38}
 figcaption{color:#8b94a4;font-size:12px;padding-top:5px}
 .missing .ph{aspect-ratio:16/9;background:#1a1d24;border:1px dashed #333a45;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#5a6272;font-size:13px}
 .refs{border-top:1px solid #2a2f38;padding-top:26px;margin-top:10px}
</style>
<h1>Overworld gauntlet loop</h1>
<p class="lede">${esc(rounds.lede)}</p>
${body}
<section class="refs"><h2>The references</h2>
<p class="when">The bar. FFIX-reimagined overworld screenshots &mdash; same shot type as ours: a character walking between towns.</p>
<div class="grid">${refs}</div></section>
`);
console.log('  wrote ' + OUT.replace(ROOT, ''));
for (const r of rounds.rounds) {
  const n = (r.views || []).filter(v => r.prefix && have.includes(`${r.prefix}-${v}.png`)).length;
  console.log(`    round ${r.n}: ${n}/${(r.views || []).length} frames`);
}
