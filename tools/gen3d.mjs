#!/usr/bin/env node
// gen3d.mjs — the CHARACTER FACTORY's mesh stage: turnaround images in, rigged GLB
// out, entirely headless. Uses Tripo (platform.tripo3d.ai) v3 OpenAPI with the
// TRIPO_API_KEY already in .env beside GEMINI_API_KEY (same parse as genart.mjs).
//
//   node tools/gen3d.mjs vesper --views front.jpg,left.jpg,right.jpg,back.jpg --rig
//   node tools/gen3d.mjs vesper --views f.jpg,l.jpg,r.jpg,b.jpg --quality standard
//   node tools/gen3d.mjs vesper --views f.jpg --out public/.../vesper-try2.glb --force
//   node tools/gen3d.mjs vesper --views ... --rig --anim preset:idle,preset:walk
//   node tools/gen3d.mjs vesper --views ... --no-poll     create task, print id, exit
//   node tools/gen3d.mjs --resume <task_id> --out out.glb  download a finished task
//
// Views may be given positionally (front,left,right,back) or keyed
// (--views front=a.jpg,back=b.jpg). Two or more views => multiview-to-model;
// one view => image-to-model. Missing views are simply omitted.
//
// ============================================================================
// THE FACTORY PATTERN (per character, all headless)
// ============================================================================
//   1. turnaround   tools/gen-character.mjs / genart.mjs  -> 4 A-pose views
//   2. mesh         tools/gen3d.mjs <name> --views ...    -> textured GLB
//   3. rig          same run, --rig                       -> skinned GLB (Mixamo names)
//   4. normalize    Blender pass (scale to 1.65 m, feet at origin, +Z forward,
//                   material/atlas cleanup) — ours, not Tripo's
//   5. retarget     tools/vesper_retarget.py or --anim presets -> clip library
// Every stage is a file on disk with a .json record next to it, so any stage can
// be rerolled without redoing the ones before it.
//
// ============================================================================
// WHAT THE API ACTUALLY EXPOSES (probed live 2026-07-30, not just read in docs)
// ============================================================================
//   POST /v3/files                       multipart `file`  -> {file_token}   FREE
//   POST /v3/generation/image-to-model    single view
//   POST /v3/generation/multiview-to-model  `inputs` view-keyed array
//   POST /v3/animations/rig-check        cheap biped-compatibility probe
//   POST /v3/animations/rig              -> SKINNED model. RIGGING IS API-EXPOSED.
//   POST /v3/animations/retarget         preset animation library onto the rig
//   GET  /v3/tasks/{task_id}             status/progress/output/credits_consumed
// There is NO v3 balance endpoint (every /v3/balance, /v3/wallet, /v3/user/... 404s);
// the v2 one still answers and is authoritative:
//   GET https://api.tripo3d.ai/v2/openapi/user/balance -> {balance, frozen}
//   node tools/gen3d.mjs --balance
//
// BILLING, VERIFIED THE HARD WAY (2026-07-31): the key in .env authenticates fine
// and /v3/files uploads succeed — uploads are FREE — but the account balance is 0,
// so EVERY generation endpoint returns 2010 "You don't have enough credit",
// including the cheapest possible call (v2.5-20250123, texture:false). Nothing on
// this API has a free tier. Upload success is therefore NOT evidence the pipeline
// works; only a task id is. Check `--balance` before booking a generation run.
//
// ============================================================================
// WEB APP vs API — the tradeoffs found building this
// ============================================================================
//   + API wins: fully headless, so a character is one command and a diff, not a
//     browser session; deterministic via model_seed/texture_seed; face_limit and
//     texture_quality are dials the web UI does not expose as precisely; the rig
//     comes back with MIXAMO BONE NAMES on request (`spec: "mixamo"`), which is
//     exactly what our retarget pass wants — the web export does not offer that.
//   + API wins: rigging needs no web step at all, so the factory is 100% scriptable.
//   - Web wins: you see the mesh before you pay for the texture pass; the API
//     bills the whole job whether or not you like the silhouette. Budget one
//     `--quality standard` probe run per character before a `detailed` art pass.
//   - Web wins: interactive re-pose / part editing. The API's `generate_parts`
//     exists but is a different (pricier) product path.
//   - GOTCHA: `quad: true` FORCES the output format to FBX. A quad GLB is not a
//     thing you can ask for. Since the game loads GLB, quad is OFF by default and
//     `--quad` is a deliberate "I want this for Blender/ZBrush, not for the game"
//     switch. This is the one place tonight's "quad topology if exposed" default
//     had to yield to the pipeline.
//   - GOTCHA: `texture_quality: "extreme"` is 8K — huge and slow. "detailed" is
//     the 4K tier and is our default.
//   - GOTCHA: rig `model` v1.0-20240301 is biped-only but carries the 90+ preset
//     animation library; v2.5-20260210 adds quadruped/avian/etc. Default is v1.0
//     for humans because the preset library is the point.
//
// ============================================================================
// STATE OF THE SMOKE TEST (2026-07-31)
// ============================================================================
// Everything up to the till was exercised for real on the Vesper A-pose set:
// four uploads succeeded, and the multiview task body passed Tripo's schema
// validation (it failed at the CREDIT check, which happens after validation —
// so the request shape below is confirmed good, not merely hoped for). The run
// stops there until the account has credit. The command to finish it:
//
//   node tools/gen3d.mjs vesper \
//     --views public/assets/refs/vesper_apose_front.jpg,public/assets/refs/vesper_apose_left.jpeg,\
// public/assets/refs/vesper_apose_right.jpeg,public/assets/refs/vesper_apose_back.jpeg \
//     --quality standard --rig \
//     --out public/assets/characters/vesper/vesper-api-smoke.glb
//
// The acceptance instrument is tools/char_inspect.py (Blender -b). The baseline
// it must be compared against — the user's WEB-MADE model, measured, not quoted:
//   public/assets/characters/vesper/vesper.glb  12.86 MB
//     66,823 v / 93,067 tri, 2 mesh objects, 1 material
//     Armature, 41 bones, Mixamo-style names
//     no animation clips
//     4096x4096 basecolor + normal + roughness/metal  (4K PBR)
//     bounds 1.909 x 2.000 x 2.000 — i.e. NOT real-world scale; it comes out of
//     the web app fitted to a 2-unit box, which is exactly why step 4 of the
//     factory (normalization) is ours and not the vendor's.
// Expect the API run at face_limit 50000 to land materially lighter than 93k tri;
// that is the point of the dial, and the reason the API is worth the plumbing.
//
// Observed credit cost is written into every <stem>.json (`creditsConsumed`, per
// task and total) and appended to public/assets/characters/MANIFEST.md.
import fs from 'fs';
import path from 'path';

const root = path.join(import.meta.dirname, '..');
const rel = (p) => path.relative(root, p);

const env = Object.fromEntries(
  fs.readFileSync(path.join(root, '.env'), 'utf8')
    .split('\n')
    .filter(l => l.includes('=') && !l.trim().startsWith('#'))
    .map(l => [
      l.slice(0, l.indexOf('=')).trim(),
      l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, ''),
    ])
);
const KEY = env.TRIPO_API_KEY || process.env.TRIPO_API_KEY;

const API = 'https://openapi.tripo3d.ai/v3';
const V2 = 'https://api.tripo3d.ai/v2/openapi';

// Defaults tuned for a game-ready JRPG character.
const MESH_MODEL = 'v3.1-20260211';   // newest H-series
const RIG_MODEL = 'v1.0-20240301';    // biped + the 90-odd animation presets
const FACE_LIMIT = 50000;             // ~25k verts after triangulation; plenty for a field character
const VIEW_KEYS = ['front', 'left', 'right', 'back'];

/* ---------------- http ---------------- */
const auth = { Authorization: `Bearer ${KEY}` };

async function api(method, route, body) {
  const res = await fetch(`${API}${route}`, {
    method,
    headers: { ...auth, ...(body ? { 'content-type': 'application/json' } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const j = await res.json().catch(() => ({}));
  if (!res.ok || (j.code !== 0 && j.code !== undefined)) {
    // The one failure that is not a bug: the wallet is empty. Say so plainly
    // rather than making the next reader decode a 403 from a stack trace.
    if (j.code === 2010 || /enough credit/i.test(j.message || '')) {
      const bal = await fetch(`${V2}/user/balance`, { headers: auth })
        .then(r => r.json()).then(r => r.data).catch(() => null);
      console.error(`\nOUT OF CREDIT — Tripo refused the task before doing any work, so nothing was billed.` +
        `\n  balance: ${bal ? `${bal.balance} (frozen ${bal.frozen})` : 'unknown'}` +
        `\n  top up at https://platform.tripo3d.ai/billing, then re-run this exact command.` +
        `\n  (uploads are free and already succeeded; only generation costs credit)\n`);
      process.exit(2);
    }
    throw new Error(`${method} ${route} -> ${res.status} ${j.message || JSON.stringify(j).slice(0, 300)}`);
  }
  return j.data ?? j;
}

async function upload(file) {
  const abs = path.isAbsolute(file) ? file : path.join(process.cwd(), file);
  if (!fs.existsSync(abs)) throw new Error(`no such view image: ${file}`);
  const type = /\.png$/i.test(abs) ? 'image/png' : /\.webp$/i.test(abs) ? 'image/webp' : 'image/jpeg';
  const fd = new FormData();
  fd.append('file', new Blob([fs.readFileSync(abs)], { type }), path.basename(abs));
  const res = await fetch(`${API}/files`, { method: 'POST', headers: auth, body: fd });
  const j = await res.json().catch(() => ({}));
  if (j.code !== 0) throw new Error(`upload ${file}: ${j.message || JSON.stringify(j).slice(0, 200)}`);
  return j.data.file_token;
}

// Poll until terminal. One progress line, rewritten in place when on a tty.
async function waitFor(taskId, label) {
  const t0 = Date.now();
  let last = -1;
  for (;;) {
    const d = await api('GET', `/tasks/${taskId}`);
    const secs = ((Date.now() - t0) / 1000).toFixed(0);
    if (d.progress !== last || d.status !== 'running') {
      last = d.progress;
      const line = `  ${label} ${d.status} ${String(d.progress ?? 0).padStart(3)}%  ${secs}s`;
      if (process.stdout.isTTY) process.stdout.write('\r' + line.padEnd(60));
      else console.log(line);
    }
    if (d.status === 'success') {
      if (process.stdout.isTTY) process.stdout.write('\n');
      return { ...d, seconds: +((Date.now() - t0) / 1000).toFixed(1) };
    }
    if (d.status === 'failed' || d.status === 'cancelled' || d.status === 'banned' || d.status === 'expired') {
      if (process.stdout.isTTY) process.stdout.write('\n');
      throw new Error(`${label} ${d.status}: ${d.error_message || d.error_code || 'no reason given'}`);
    }
    await new Promise(r => setTimeout(r, 4000));
  }
}

async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download ${res.status} ${url.slice(0, 80)}`);
  const buf = Buffer.from(await res.arrayBuffer());
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, buf);
  return buf.length;
}

const modelUrl = (out = {}) =>
  out.pbr_model || out.model_url || out.model || out.rigged_model || out.base_model || null;

/* ---------------- cli ---------------- */
const argv = process.argv.slice(2);
const flag = (n) => argv.includes(n);
const opt = (n, d = null) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };

// Flags that consume the next argv entry — so the bare <name> is never mistaken
// for a flag's value (and `--force vesper` still finds `vesper`).
const VALUE_FLAGS = new Set(['--views', '--out', '--quality', '--anim', '--faces',
  '--model', '--rig-model', '--rig-spec', '--rig-type', '--seed', '--resume']);
const name = (() => {
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) { if (VALUE_FLAGS.has(argv[i])) i++; continue; }
    return argv[i];
  }
  return null;
})();

if (flag('--help') || (!name && !opt('--resume') && !flag('--balance'))) {
  console.log(`usage: node tools/gen3d.mjs <name> --views front.png[,left,right,back] [options]

  --views <list>       comma-separated images; positional front,left,right,back
                       or keyed  front=a.png,back=b.png.  >=2 => multiview
  --out <path.glb>     default public/assets/characters/<name>/<name>-gen.glb
  --quality <q>        standard | detailed   (default detailed = 4K PBR + ultra geo)
  --rig                also run auto-rig; the downloaded GLB is the SKINNED one
  --anim <list>        after rigging, retarget presets e.g. preset:idle,preset:walk
  --poll               poll to completion (default on; --no-poll to fire and forget)
  --force              overwrite an existing output file
  --faces <n>          face budget (default ${FACE_LIMIT})
  --quad               quad topology — NOTE: forces FBX output, not GLB
  --model <ver>        ${MESH_MODEL} | v3.0-20250812 | v2.5-20250123
  --rig-model <ver>    ${RIG_MODEL} (biped, preset library) | v2.5-20260210
  --rig-spec <s>       mixamo (default, retarget-friendly) | tripo
  --rig-type <t>       biped (default) | quadruped | hexapod | octopod | avian | ...
  --seed <n>           model_seed for reproducible geometry
  --resume <task_id>   skip generation, just download an already-finished task
  --balance            print the (v2) credit balance and exit
`);
  process.exit(flag('--help') ? 0 : 1);
}
if (!KEY) { console.error('no TRIPO_API_KEY in .env'); process.exit(1); }

if (flag('--balance')) {
  const r = await fetch(`${V2}/user/balance`, { headers: auth }).then(r => r.json());
  console.log(JSON.stringify(r.data ?? r));
  process.exit(0);
}

const quality = opt('--quality', 'detailed');
if (!['standard', 'detailed'].includes(quality)) { console.error('--quality must be standard|detailed'); process.exit(1); }
const doPoll = !flag('--no-poll');
const force = flag('--force');
const rig = flag('--rig');
const anims = (opt('--anim') || '').split(',').map(s => s.trim()).filter(Boolean);

const outPath = path.resolve(root, opt('--out') ||
  `public/assets/characters/${name}/${name}-gen.glb`);
const stem = outPath.replace(/\.(glb|fbx)$/i, '');
const recordPath = `${stem}.json`;
if (fs.existsSync(outPath) && !force) {
  console.error(`refusing to overwrite ${rel(outPath)} — pass --force`);
  process.exit(1);
}

/* ---------------- resume path ---------------- */
if (opt('--resume')) {
  const d = await waitFor(opt('--resume'), 'task');
  const url = modelUrl(d.output);
  if (!url) { console.error('task has no model output:', JSON.stringify(d.output)); process.exit(1); }
  const bytes = await download(url, outPath);
  console.log(`-> ${rel(outPath)}  ${(bytes / 1048576).toFixed(2)} MB  ${d.credits_consumed ?? '?'} credits`);
  process.exit(0);
}

/* ---------------- views ---------------- */
const viewArg = opt('--views');
if (!viewArg) { console.error('--views is required'); process.exit(1); }
const views = {};
viewArg.split(',').map(s => s.trim()).filter(Boolean).forEach((spec, i) => {
  const m = spec.match(/^(front|left|right|back)=(.+)$/i);
  if (m) views[m[1].toLowerCase()] = m[2];
  else {
    if (i >= VIEW_KEYS.length) throw new Error(`too many positional views (max 4): ${spec}`);
    views[VIEW_KEYS[i]] = spec;
  }
});
if (!views.front) { console.error('a front view is required'); process.exit(1); }
const viewList = Object.entries(views);

/* ---------------- run ---------------- */
const t0 = Date.now();
const record = {
  name, generatedAt: new Date().toISOString(), tool: 'tools/gen3d.mjs',
  api: API, out: rel(outPath), views: Object.fromEntries(viewList.map(([k, v]) => [k, rel(path.resolve(v))])),
  tasks: [], creditsConsumed: 0,
};

console.log(`* ${name}: ${viewList.length} view(s) [${viewList.map(v => v[0]).join(' ')}] quality=${quality}${rig ? ' +rig' : ''}`);

const tokens = {};
for (const [k, file] of viewList) {
  tokens[k] = await upload(file);
  console.log(`  uploaded ${k.padEnd(5)} ${rel(path.resolve(file))} -> ${tokens[k].slice(0, 18)}…`);
}

const shared = {
  model: opt('--model', MESH_MODEL),
  texture: true,
  pbr: true,                                   // metal/rough/normal maps, not just albedo
  texture_quality: quality === 'detailed' ? 'detailed' : 'standard',  // detailed = 4K
  geometry_quality: quality === 'detailed' ? 'detailed' : 'standard',
  face_limit: +opt('--faces', FACE_LIMIT),
  quad: flag('--quad'),                        // NB: forces FBX output
  export_uv: true,
  ...(opt('--seed') ? { model_seed: +opt('--seed'), texture_seed: +opt('--seed') } : {}),
};

let body, route;
if (viewList.length >= 2) {
  route = '/generation/multiview-to-model';
  body = { inputs: viewList.map(([k]) => ({ [k]: tokens[k] })), ...shared };
} else {
  route = '/generation/image-to-model';
  body = { input: tokens.front, ...shared };
}
record.request = { route, ...body, inputs: undefined, input: undefined };

const created = await api('POST', route, body);
const meshTask = created.task_id;
console.log(`  ${route.split('/').pop()} task ${meshTask}`);
record.tasks.push({ stage: 'mesh', type: route.split('/').pop(), task_id: meshTask });

if (!doPoll) {
  console.log(`\nnot polling (--no-poll). resume with:\n  node tools/gen3d.mjs --resume ${meshTask} --out ${rel(outPath)}`);
  fs.mkdirSync(path.dirname(recordPath), { recursive: true });
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2) + '\n');
  process.exit(0);
}

const mesh = await waitFor(meshTask, 'mesh');
Object.assign(record.tasks[0], {
  seconds: mesh.seconds, credits: mesh.credits_consumed ?? null,
  output: mesh.output, created_at: mesh.created_at, completed_at: mesh.completed_at,
});
record.creditsConsumed += mesh.credits_consumed || 0;

let finalUrl = modelUrl(mesh.output);
let finalTask = meshTask;

if (rig) {
  const rigBody = {
    input: meshTask,
    model: opt('--rig-model', RIG_MODEL),
    rig_type: opt('--rig-type', 'biped'),
    spec: opt('--rig-spec', 'mixamo'),   // Mixamo bone names => our retarget pass just works
    out_format: flag('--quad') ? 'fbx' : 'glb',
  };
  // Cheap compatibility probe first — the docs ask for it and a failed rig still bills.
  try {
    const chk = await api('POST', '/animations/rig-check', { input: meshTask });
    const c = await waitFor(chk.task_id, 'rigchk');
    record.tasks.push({ stage: 'rig-check', task_id: chk.task_id, seconds: c.seconds, output: c.output, credits: c.credits_consumed ?? null });
    record.creditsConsumed += c.credits_consumed || 0;
    console.log(`  rig-check: ${JSON.stringify(c.output)}`);
  } catch (e) { console.log(`  rig-check skipped (${e.message.slice(0, 90)})`); }

  const r = await api('POST', '/animations/rig', rigBody);
  console.log(`  rig task ${r.task_id} (${rigBody.spec}/${rigBody.rig_type}/${rigBody.model})`);
  const rr = await waitFor(r.task_id, 'rig  ');
  record.tasks.push({ stage: 'rig', task_id: r.task_id, request: rigBody, seconds: rr.seconds, credits: rr.credits_consumed ?? null, output: rr.output });
  record.creditsConsumed += rr.credits_consumed || 0;
  finalUrl = modelUrl(rr.output) || finalUrl;
  finalTask = r.task_id;

  if (anims.length) {
    const ab = { input: r.task_id, animations: anims, out_format: 'glb', bake_animation: true, export_with_geometry: true };
    const a = await api('POST', '/animations/retarget', ab);
    console.log(`  retarget task ${a.task_id} [${anims.join(' ')}]`);
    const ar = await waitFor(a.task_id, 'anim ');
    record.tasks.push({ stage: 'retarget', task_id: a.task_id, request: ab, seconds: ar.seconds, credits: ar.credits_consumed ?? null, output: ar.output });
    record.creditsConsumed += ar.credits_consumed || 0;
    finalUrl = modelUrl(ar.output) || finalUrl;
    finalTask = a.task_id;
  }
}

if (!finalUrl) { console.error('no model url in the final task output'); process.exit(1); }
const bytes = await download(finalUrl, outPath);
record.bytes = bytes;
record.finalTask = finalTask;
record.totalSeconds = +((Date.now() - t0) / 1000).toFixed(1);

// The preview render is free provenance — keep it beside the mesh for the review board.
const preview = mesh.output?.rendered_image_url;
if (preview) {
  try { await download(preview, `${stem}-preview.png`); record.preview = rel(`${stem}-preview.png`); } catch {}
}

fs.writeFileSync(recordPath, JSON.stringify(record, null, 2) + '\n');

/* ---------------- manifest ---------------- */
const manifest = path.join(root, 'public/assets/characters/MANIFEST.md');
if (!fs.existsSync(manifest)) {
  fs.writeFileSync(manifest, `# Character models — provenance

Every generated character mesh in this tree, what made it, and what it cost.
Machine-generated by \`tools/gen3d.mjs\` through the Tripo v3 OpenAPI
(\`openapi.tripo3d.ai/v3\`, \`.env\` \`TRIPO_API_KEY\`). Full per-run records —
task ids, request bodies, timings, credits — live in the \`.json\` beside each file.

| date | character | file | views | quality | faces | rig | tasks | credits | s | MB |
|---|---|---|---|---|---|---|---|---|---|---|
`);
}
fs.appendFileSync(manifest, `| ${record.generatedAt.slice(0, 10)} | ${name} | \`${rel(outPath)}\` | ` +
  `${viewList.map(v => v[0]).join('+')} | ${quality} | ${shared.face_limit} | ` +
  `${rig ? `${opt('--rig-spec', 'mixamo')}/${opt('--rig-model', RIG_MODEL)}` : '—'} | ` +
  `${record.tasks.length} | ${record.creditsConsumed} | ${record.totalSeconds} | ${(bytes / 1048576).toFixed(2)} |\n`);

console.log(`\n-> ${rel(outPath)}  ${(bytes / 1048576).toFixed(2)} MB` +
  `  ${record.totalSeconds}s  ${record.creditsConsumed} credits` +
  `\n   record ${rel(recordPath)} · manifest ${rel(manifest)}`);
