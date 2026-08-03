#!/usr/bin/env node
/* playtest_triage.mjs — MEASURE THE CLAIM, THEN RENDER THE QUEUE.
 *
 *   node tools/playtest_triage.mjs                 triage what needs no browser, render
 *   node tools/playtest_triage.mjs --port=3000     also run the in-page reachability probe
 *   node tools/playtest_triage.mjs --render-only   just rebuild the page and the markdown
 *   node tools/playtest_triage.mjs --id=PT-...     one entry
 *   node tools/playtest_triage.mjs --recheck       re-measure entries already triaged
 *
 * *** WHY THIS FILE IS NOT OPTIONAL ***
 * tools/llm_playtester.mjs produces an LLM's opinion about a picture. This repo has
 * a documented confabulation scar — the pink plank: a judge described a defect that
 * did not exist and a builder built against it — and the workflow the user ratified
 * out of it is: A JUDGE FINDS A FLAW -> MEASURE THE CLAIM ON AN INSTRUMENT -> ONLY
 * THEN BUILD. scene_redteam's own note says its second stage filters WEAK
 * CRITICISM, not CONFABULATION. So every report in the queue starts UNVERIFIED and
 * this is the step that moves it.
 *
 *   VERIFIED    an instrument agreed. `instrument` names it; `evidence` is the line
 *               it printed.
 *   REFUTED     an instrument disagreed. JUST AS VALUABLE, and printed just as
 *               loudly: the false-positive rate IS the calibration of the whole
 *               playtester, and the agent's perception is deliberately poorer than
 *               a human's (one still frame of a night plate, no parallax, no
 *               camera control), so it is BIASED TOWARD "I cannot find it".
 *   UNVERIFIED  nobody measured it. A LEAD, NEVER A TICKET. The entry still names
 *               the instrument somebody should point at it.
 *
 * WHAT IT CAN MEASURE AUTOMATICALLY
 *   "I cannot find / cannot see <person>"   -> tools/findability_test.mjs, and the
 *       specific person's rows out of it. That gate asks whether that body's pixel
 *       column survives the plate's own depth map — precisely the question "I
 *       couldn't see her" is asking. No browser, ~0.4 s.
 *   "the walk was blocked" (every walk-executor report, and any prose claim about
 *       being unable to get somewhere) -> tools/reach_probe.mjs INSIDE THE RUNNING
 *       PAGE, flood-filling from where the body actually stood to the point it was
 *       walking at. Needs --port. The report carries `probe:{from,to}` for exactly
 *       this reason: a triage that has to guess the claim from prose is measuring
 *       its own guess.
 *
 * WHAT IT CANNOT, and says so rather than pretending: taste ("the hush is flat"),
 * comparisons to something the agent never saw, anything about audio, and any
 * claim whose subject it cannot name. Those stay UNVERIFIED with a suggested
 * instrument and a human's name on the next move.
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { execFileSync, spawn } from 'child_process';
import { join, dirname } from 'path';
import { createRequire } from 'module';
import * as Q from './playtest/queue.mjs';
import { freePort, killOrphans, findPage, sweepStaleProfiles } from './cdp.mjs';
import { CALL, verdict } from './reach_probe.mjs';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(new URL(import.meta.url).pathname), '..');
const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const has = (k) => argv.includes('--' + k);
const PORT = parseInt(arg('port', '0'), 10);
const ONLY = arg('id', null);
const RENDER_ONLY = has('render-only');
const RECHECK = has('recheck');
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ------------------------------------------------------------- the cast -----
// Names the queue may be talking about, so "I couldn't find Poppy" resolves to a
// row in findability_test rather than to a guess.
const CAST = (() => {
  try {
    const j = JSON.parse(readFileSync(join(ROOT, 'public/game/npcs.json'), 'utf8'));
    return (j.npcs || []).map(n => ({ id: n.id, name: n.name || n.id, scenes: [].concat(n.scene || []) }));
  } catch (e) { return []; }
})();
function namesIn(text) {
  const t = ' ' + String(text || '').toLowerCase() + ' ';
  const hit = [];
  for (const c of CAST) {
    const n = String(c.name).toLowerCase();
    if (n.length < 3) continue;
    if (new RegExp('\\b' + n.replace(/[^a-z]/g, '') + '\\b').test(t.replace(/[^a-z ]/g, ''))) hit.push(c);
  }
  return hit;
}

// ------------------------------------------------------- the classifier -----
const RE_FIND = /can(?:no|')?t (?:find|see|spot)|cannot (?:find|see|spot)|couldn'?t (?:find|see)|nobody|no ?one (?:is|was) (?:there|here)|where is|not there|isn'?t (?:there|here)|invisible|hidden/i;
const RE_REACH = /block|can(?:no|')?t (?:get|reach|walk|go)|cannot (?:get|reach|walk|go)|in the way|won'?t let me|stuck|wall|barrier|closed off|no way (?:through|past)/i;
function classify(e) {
  const prose = [e.title, e.doing, e.expected, e.happened].filter(Boolean).join(' ');
  // THE SPINE REPORT IS ALREADY A MEASUREMENT. Unlike everything the model says,
  // it is a mechanical fact: the scene the body is in holds none of the next
  // un-fired beats in story.json. There is nothing left to confirm — only a design
  // decision about what to do, which is a human's.
  if (e.source === 'spine-detector') return { kind: 'spine', why: 'a harness measurement, not a model opinion' };
  if (e.probe && e.probe.kind === 'reach') return { kind: 'reach', probe: e.probe, why: 'the executor recorded the exact pair' };
  if (e.source === 'walk-executor') return { kind: 'reach', probe: e.probe, why: 'a walk-executor stall' };
  const who = namesIn(prose);
  if (RE_FIND.test(prose) && who.length) return { kind: 'find', who, why: 'the claim names a person it could not see' };
  if (RE_REACH.test(prose) && e.truth && e.truth.pos) return { kind: 'reach-vague', why: 'a blocked-path claim with no recorded target' };
  if (RE_FIND.test(prose)) return { kind: 'find-vague', why: 'a cannot-see claim naming nobody this triage recognises' };
  return { kind: 'none', why: 'no instrument in this repo answers this claim' };
}

// ------------------------------------------------------ findability_test ----
let FIND_CACHE = null;
function findability() {
  if (FIND_CACHE) return FIND_CACHE;
  try {
    FIND_CACHE = execFileSync('node', [join(ROOT, 'tools/findability_test.mjs'), '--verbose'],
      { encoding: 'utf8', cwd: ROOT, maxBuffer: 8 * 1024 * 1024 });
  } catch (e) { FIND_CACHE = (e.stdout || '') + (e.stderr || ''); }
  return FIND_CACHE;
}
function triageFind(e, cls) {
  const out = findability();
  const lines = out.split('\n');
  const hits = [];
  for (const c of cls.who) {
    const mine = lines.filter(l => new RegExp('\\b' + c.id + '\\b', 'i').test(l) && /^\s*(fail|warn)/i.test(l));
    for (const l of mine) hits.push(l.trim());
  }
  const who = cls.who.map(c => c.name).join(', ');
  if (hits.length) return { status: 'VERIFIED', instrument: 'tools/findability_test.mjs',
    evidence: hits.join('\n') };
  // The gate is clean. That REFUTES the pixel claim and nothing more — see the
  // perception-asymmetry note in llm_playtester's header.
  return { status: 'REFUTED', instrument: 'tools/findability_test.mjs',
    evidence: `findability_test reports no failure or warning for ${who}: the body column is in frame and ` +
      'survives the plate\'s depth map. The agent sees ONE still frame of a night-graded plate with no ' +
      'parallax and no camera control, so it is biased toward "I cannot find them". A human may still ' +
      'struggle here — this refutes "the pixels are missing", not "the figure reads at a glance".' };
}

// ----------------------------------------------------- the reach probe ------
// The same fill playthrough_test's §W uses, inside the running game: SIM.walkFloors,
// SIM.ground, SIM.blocked, SIM.edges — the engine's own rays and the player's own
// body box, never the file.
async function withPage(scene, cam, pos, fn) {
  const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  const WebSocket = require('ws');
  const cdpPort = await freePort();
  const profile = join(process.env.TMPDIR || '/tmp', 'playtest-triage-profile-' + process.pid);
  sweepStaleProfiles('playtest-triage-profile-'); killOrphans(profile);
  const q = new URLSearchParams({ scene, nomusic: '1' });
  if (cam) q.set('cam', cam);
  if (pos) { q.set('sx', pos[0]); q.set('sy', pos[1]); q.set('sz', pos[2]); }
  const chrome = spawn(CHROME, [`--remote-debugging-port=${cdpPort}`, `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions',
    '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-gpu',
    '--headless=new', '--window-size=1000,600',
    `http://localhost:${PORT}/play3d.html?` + q.toString()], { stdio: 'ignore' });
  try {
    const url = await findPage(cdpPort, { tries: 200, label: 'playtest_triage' });
    const cdp = await new Promise((res, rej) => {
      const ws = new WebSocket(url, { perMessageDeflate: false, maxPayload: 128 * 1024 * 1024 });
      const pend = new Map(); let id = 0;
      ws.on('open', () => res({ send(m, p) { return new Promise((ok, no) => { const mid = ++id; pend.set(mid, { ok, no }); ws.send(JSON.stringify({ id: mid, method: m, params: p || {} })); }); } }));
      ws.on('error', rej);
      ws.on('message', raw => { let m; try { m = JSON.parse(raw); } catch (e) { return; }
        if (m.id && pend.has(m.id)) { const { ok, no } = pend.get(m.id); pend.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); } });
    });
    await cdp.send('Runtime.enable');
    const ev = async (expr, t) => {
      const r = await cdp.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, timeout: t || 180000 });
      if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception || {}).description || r.exceptionDetails.text);
      return r.result && r.result.value;
    };
    await ev(`(async()=>{for(let i=0;i<600;i++){const S=window.SIM;
      if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy) return true;
      await new Promise(r=>setTimeout(r,100));} return false;})()`, 180000);
    return await fn(ev);
  } finally {
    try { chrome.kill('SIGKILL'); } catch (e) { }
    try { require('fs').rmSync(profile, { recursive: true, force: true, maxRetries: 2 }); } catch (e) { }
  }
}
async function triageReach(e, cls) {
  if (!PORT) return { status: 'UNVERIFIED', instrument: 'tools/reach_probe.mjs (NOT RUN)',
    evidence: 'the reachability probe needs a running server: re-run this with --port=3000.' };
  const p = cls.probe;
  if (!p || !p.from || !p.to) return { status: 'UNVERIFIED', instrument: 'tools/reach_probe.mjs (NOT RUN)',
    evidence: 'this report claims a blocked path but records no from/to pair, so there is nothing exact to ' +
      'measure. Reproduce it with --repro and let the walk executor record the pair.' };
  const scene = p.scene || (e.truth && e.truth.scene);
  try {
    const res = await withPage(scene, e.truth && e.truth.shot, p.from, async (ev) =>
      await ev(CALL(p.from, p.to, { step: 0.4, tol: 1.5, budget: 250000 }), 300000));
    const line = verdict('where I stood', 'where I pointed', p.from, p.to, res);
    if (res.ok) return { status: 'REFUTED', instrument: 'tools/reach_probe.mjs (in the running page)',
      evidence: line + '\n  The ground IS connected, so the walk was not blocked by the world. The likely ' +
        'causes are the executor giving up (a narrow gap, a step it could not take at its 150 ms burst) ' +
        'or a body-box snag that the cell fill does not model — confirm with tools/walk_bodygate.mjs.' };
    return { status: 'VERIFIED', instrument: 'tools/reach_probe.mjs (in the running page)', evidence: line };
  } catch (err) {
    return { status: 'UNVERIFIED', instrument: 'tools/reach_probe.mjs (FAILED)',
      evidence: 'the probe itself failed: ' + err.message };
  }
}

// ------------------------------------------------------------ the render ---
const ESC = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const BADGE = { VERIFIED: '#3fa96a', REFUTED: '#b25a4a', UNVERIFIED: '#8a7a5a' };
const RANK = { P0: 0, P1: 1, P2: 2 };
const STATRANK = { VERIFIED: 0, UNVERIFIED: 1, REFUTED: 2 };

function render(q) {
  const es = q.entries.slice().sort((a, b) =>
    (STATRANK[a.verification.status] - STATRANK[b.verification.status]) ||
    ((RANK[a.severity] ?? 9) - (RANK[b.severity] ?? 9)) || a.id.localeCompare(b.id));
  const n = s => es.filter(e => e.verification.status === s).length;
  const html = `<!doctype html><meta charset="utf-8"><title>Emberbrook — playtest queue</title>
<style>
 body{background:#14120f;color:#e6dccb;font:14px/1.6 -apple-system,Segoe UI,sans-serif;margin:0;padding:28px 32px;max-width:1180px}
 h1{font:600 22px/1.3 Georgia,serif;color:#f2e2c8;margin:0 0 4px} .sub{color:#9b8d78;margin:0 0 22px}
 .tally{display:flex;gap:18px;margin:0 0 26px;flex-wrap:wrap}
 .tally div{background:#1e1a15;border:1px solid #2e281f;border-radius:8px;padding:8px 14px}
 .tally b{font-size:20px;display:block}
 .e{background:#1b1815;border:1px solid #2d2720;border-radius:10px;padding:16px 18px;margin:0 0 16px}
 .hd{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
 .id{font:12px monospace;color:#8d8171} .ttl{font-weight:600;color:#f0e4d0;flex:1;min-width:280px}
 .b{font:11px monospace;padding:2px 8px;border-radius:99px;color:#0e0c0a;font-weight:700}
 .sev{font:11px monospace;color:#c8a86a;border:1px solid #4a3f2c;padding:1px 7px;border-radius:99px}
 dl{display:grid;grid-template-columns:118px 1fr;gap:4px 14px;margin:12px 0 0}
 dt{color:#8d8171;font-size:12px} dd{margin:0}
 pre{white-space:pre-wrap;background:#100e0c;border:1px solid #2a241c;border-radius:6px;padding:9px 11px;margin:6px 0 0;font:12px/1.5 monospace;color:#c9bda8;overflow-x:auto}
 .fr{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 0} .fr img{max-width:340px;border-radius:6px;border:1px solid #332c22}
 .meta{color:#6f6558;font:11px monospace;margin-top:10px}
 .warn{background:#241c14;border:1px solid #4a3a22;border-radius:8px;padding:12px 15px;color:#d8c08a;margin:0 0 22px}
 a{color:#c8a86a}
</style>
<h1>Emberbrook — LLM playtest queue</h1>
<p class="sub">Filed by <code>tools/llm_playtester.mjs</code>, measured by <code>tools/playtest_triage.mjs</code>. Generated ${ESC(new Date().toISOString())}.</p>
<div class="warn"><b>An UNVERIFIED complaint is a lead, never a ticket.</b> These are an LLM's opinions about
screenshots. This repo has a confabulation scar; the ratified workflow is judge&nbsp;→&nbsp;<b>measure on an
instrument</b>&nbsp;→&nbsp;build. REFUTED entries matter as much as VERIFIED ones: the agent sees one still frame
of a night-graded plate with no parallax and no camera control, so it is biased toward "I cannot find it",
and the false-positive rate is this tool's calibration.</div>
<div class="tally">
 <div><b style="color:${BADGE.VERIFIED}">${n('VERIFIED')}</b>verified</div>
 <div><b style="color:${BADGE.UNVERIFIED}">${n('UNVERIFIED')}</b>unverified</div>
 <div><b style="color:${BADGE.REFUTED}">${n('REFUTED')}</b>refuted</div>
 <div><b>${es.length}</b>total</div>
</div>
${es.map(e => `<div class="e">
 <div class="hd"><span class="b" style="background:${BADGE[e.verification.status] || '#666'}">${ESC(e.verification.status)}</span>
  <span class="sev">${ESC(e.severity || '-')} · ${ESC(e.kind)}</span>
  <span class="ttl">${ESC(e.title)}</span><span class="id">${ESC(e.id)}</span></div>
 <dl>
  ${e.doing ? `<dt>I was doing</dt><dd>${ESC(e.doing)}</dd>` : ''}
  ${e.expected ? `<dt>I expected</dt><dd>${ESC(e.expected)}</dd>` : ''}
  ${e.happened ? `<dt>What happened</dt><dd>${ESC(e.happened)}</dd>` : ''}
  ${e.onscreen && e.onscreen.objective ? `<dt>On screen</dt><dd>objective: ${ESC(e.onscreen.objective)}</dd>` : ''}
  <dt>Measured by</dt><dd>${ESC(e.verification.instrument || '(nothing yet)')}</dd>
 </dl>
 ${e.verification.evidence ? `<pre>${ESC(e.verification.evidence)}</pre>` : ''}
 <div class="fr">${(e.frames || []).map(f => `<img src="${ESC(relToDocs(f))}" loading="lazy">`).join('')}</div>
 <div class="meta">run ${ESC(e.run)} step ${ESC(e.step)} · found by ${ESC(e.source)} · ${e.truth ? ESC(e.truth.scene + ' / ' + (e.truth.shot || '-') + ' @ ' + (e.truth.pos || []).join(',')) : ''}
 ${e.repro && e.repro.save ? `· repro: <code>node tools/llm_playtester.mjs --port=3000 --repro=${ESC(e.id)}</code> (captured at ${ESC((e.repro.sha || '').slice(0, 8))})` : '· no repro save'}</div>
</div>`).join('\n')}`;
  mkdirSync(Q.QDIR, { recursive: true });
  writeFileSync(join(Q.QDIR, 'index.html'), html);

  const md = [
    '# Emberbrook — LLM playtest queue',
    '',
    `Generated ${new Date().toISOString()} by \`tools/playtest_triage.mjs\`. Source of truth: \`docs/qa/playtest/queue.json\`.`,
    '',
    '**An UNVERIFIED complaint is a lead, never a ticket.** Filed by an LLM playing the game through',
    'screenshots and real key events; measured by instruments before anybody builds. REFUTED entries are',
    'as informative as VERIFIED ones — the agent sees one still frame with no parallax, so it is biased',
    'toward "I cannot find it", and that false-positive rate is this tool\'s calibration.',
    '',
    `| status | sev | id | title | measured by |`,
    `|---|---|---|---|---|`,
    ...es.map(e => `| ${e.verification.status} | ${e.severity || '-'} | ${e.id} | ${String(e.title).replace(/\|/g, '/')} | ${e.verification.instrument || '—'} |`),
    '',
    '## Detail',
    '',
    ...es.map(e => [
      `### ${e.id} — ${e.title}`,
      '',
      `- **status** ${e.verification.status} (${e.verification.instrument || 'nothing measured yet'})`,
      `- **severity** ${e.severity || '-'} · **kind** ${e.kind} · **found by** ${e.source}`,
      e.doing ? `- **I was doing** ${e.doing}` : null,
      e.expected ? `- **I expected** ${e.expected}` : null,
      e.happened ? `- **What happened** ${e.happened}` : null,
      e.verification.evidence ? '\n```\n' + e.verification.evidence + '\n```' : null,
      e.repro && e.repro.save ? `- **repro** \`node tools/llm_playtester.mjs --port=3000 --repro=${e.id}\` (captured at ${(e.repro.sha || '').slice(0, 8)})` : '- **repro** none',
      '',
    ].filter(x => x !== null).join('\n')),
  ].join('\n');
  writeFileSync(join(ROOT, 'docs/qa/playtest-queue.md'), md);
  return { html: join(Q.QDIR, 'index.html'), md: join(ROOT, 'docs/qa/playtest-queue.md'), counts: { v: n('VERIFIED'), u: n('UNVERIFIED'), r: n('REFUTED') } };
}
// frames are stored repo-relative; the page lives in docs/qa/playtest/
function relToDocs(p) { return String(p).replace(/^docs\/qa\/playtest\//, ''); }

// ------------------------------------------------------------------ main ---
(async function main() {
  const q = Q.load();
  if (!q.entries.length) { console.log('the queue is empty — nothing to triage.'); render(q); process.exit(0); }
  if (!RENDER_ONLY) {
    for (const e of q.entries) {
      if (ONLY && e.id !== ONLY) continue;
      if (!RECHECK && e.verification.status !== 'UNVERIFIED') continue;
      if (!RECHECK && e.verification.instrument) continue;
      const cls = classify(e);
      let v;
      if (cls.kind === 'spine') v = { status: 'VERIFIED',
        instrument: 'llm_playtester spine detector (public/game/story.json vs the running scene)',
        evidence: `The body was in "${e.truth.scene}" for three consecutive steps while none of the next ` +
          `un-fired beats in story.json lives there. Beats fired at the time: ` +
          `${(e.truth.beats || []).join(', ') || '(none)'}. This is a mechanical fact about the game, not a ` +
          'model opinion — there is nothing left to measure. What to DO about it is a design decision.' };
      else if (cls.kind === 'find') v = triageFind(e, cls);
      else if (cls.kind === 'reach') v = await triageReach(e, cls);
      else if (cls.kind === 'reach-vague') v = { status: 'UNVERIFIED', instrument: 'tools/reach_probe.mjs (needs a target)',
        evidence: 'a blocked-path claim with no recorded destination. Re-run it with --repro so the walk ' +
          'executor records the from/to pair, then triage again.' };
      else if (cls.kind === 'find-vague') v = { status: 'UNVERIFIED', instrument: 'tools/findability_test.mjs (needs a name)',
        evidence: 'a cannot-see claim that names nobody in public/game/npcs.json. A human has to say who.' };
      else v = { status: 'UNVERIFIED', instrument: null,
        evidence: 'no instrument in this repo answers this claim — it is about taste, audio, or a comparison ' +
          'the agent could not have made. A human judges this one, or it is dropped.' };
      v.at = new Date().toISOString();
      Q.update(e.id, { verification: v });
      console.log(`  ${e.id}  ${v.status.padEnd(10)} ${cls.kind.padEnd(11)} ${v.instrument || '—'}`);
    }
  }
  const out = render(Q.load());
  console.log('\n== QUEUE');
  console.log(`  ${out.counts.v} verified · ${out.counts.u} unverified · ${out.counts.r} refuted`);
  console.log('  ' + out.html.replace(ROOT + '/', ''));
  console.log('  ' + out.md.replace(ROOT + '/', ''));
  if (out.counts.u) console.log('\n  UNVERIFIED entries are LEADS. Do not build against one.');
  process.exit(0);
})().catch(e => { console.error('FATAL: ' + (e && e.stack || e)); process.exit(1); });
