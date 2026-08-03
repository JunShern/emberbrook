#!/usr/bin/env node
// mood_shots.mjs — PHOTOGRAPH THE FACES, IN THE ORDER THE PLAYER SEES THEM.
//
//   node tools/mood_shots.mjs --port=3000 --out=docs/qa/moods
//   node tools/mood_shots.mjs --port=3000 --only=story.ch1.waystone,story.ch1.meet
//
// WHY IT EXISTS: a mood table that looks right in JSON can look deranged on
// screen. The expression pass assigns a portrait mood per LINE; the only way to
// know whether the protagonist reads as a person with reactions — rather than
// someone cycling expressions at random — is to shoot her lines in sequence and
// look at the strip.
//
// THE REAL PAGE, NOT THE MOCK. tools/ui_mock.html?stage=dom disables the 3D arena
// and is not admissible for judging a portrait over a plate (user ruling). This
// drives public/play3d.html itself, with a GPU and a VISIBLE window, because rAF
// is throttled to nothing in a headless or background tab and the canvas
// screenshots go stale (repo canon).
//
// It calls Dialogue.play() directly on the node ids it is given, which is the
// same entry point Story uses. It never writes a save: nothing here touches the
// beat ledger, so autosave's non-empty-`beats` guard is never armed.
import { spawn, execFileSync } from 'child_process';
import { rmSync, mkdirSync, writeFileSync } from 'fs';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join, resolve } from 'path';
import { freePort, findPage, chromeArgs, killOrphans } from './cdp.mjs';

const require = createRequire(import.meta.url);
const WebSocket = require('ws');
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const argv = process.argv.slice(2);
const arg = (k, d) => { const h = argv.find(a => a.startsWith('--' + k + '=')); return h ? h.split('=').slice(1).join('=') : d; };
const PORT = parseInt(arg('port', '3000'), 10);
const OUT = resolve(ROOT, arg('out', 'docs/qa/moods'));
const ONLY = (arg('only', '') || '').split(',').filter(Boolean);
const W = parseInt(arg('w', '1280'), 10), H = parseInt(arg('h', '720'), 10);

// Vesper's Chapter One, in beat order, as the player meets it.
const CH1 = [
  'story.ch1.open', 'story.ch1.waystone', 'story.ch1.reveal', 'story.ch1.rowan',
  'story.ch1.meet', 'story.ch1.lamps', 'story.ch1.hush',
  'story.ch1.see.poppy', 'story.ch1.see.mara', 'story.ch1.see.finn',
  'story.ch1.see.mochi', 'story.ch1.pact',
];

let msgId = 0;
function rpc(ws, method, params = {}, sessionId, timeoutMs = 30000) {
  const id = ++msgId;
  return new Promise((res, rej) => {
    const to = setTimeout(() => rej(new Error('timeout ' + method)), timeoutMs);
    const on = (raw) => {
      let m; try { m = JSON.parse(raw); } catch { return; }
      if (m.id !== id) return;
      clearTimeout(to); ws.off('message', on);
      m.error ? rej(new Error(method + ': ' + JSON.stringify(m.error))) : res(m.result);
    };
    ws.on('message', on);
    ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
}
const evalJs = async (ws, expr, timeoutMs) => {
  const r = await rpc(ws, 'Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }, undefined, timeoutMs);
  if (r.exceptionDetails) throw new Error('page: ' + JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  return r.result.value;
};
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// playthrough_test's own readiness predicate: meshes up, no transition in flight,
// a shot resolved, and the Npc/Story modules' promises settled.
const READY = (n) => `(async()=>{for(let i=0;i<${n || 500};i++){
  const S=window.SIM; if(S&&S.gpu&&S.gpu().meshes>0&&S.cam&&!S.transitions().busy){
    const c=S.cine&&S.cine(); if(!c||c.shot){
      if(window.Npc&&Npc.ready) await Promise.race([Npc.ready(), new Promise(r=>setTimeout(r,15000))]);
      if(window.Story&&Story.ready) await Promise.race([Story.ready, new Promise(r=>setTimeout(r,15000))]);
      return true; } }
  await new Promise(r=>setTimeout(r,100));} return false;})()`;

(async () => {
  const port = await freePort();
  const profile = join('/tmp', 'moodshots-' + process.pid);
  killOrphans(profile);
  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(OUT, { recursive: true });

  const url = `http://localhost:${PORT}/play3d.html?scene=emb-cine&cam=woodroad&nomusic=1`;
  const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    chromeArgs({ port, profile, url, gpu: true, size: `${W},${H}`, headed: true }),
    { stdio: 'ignore', detached: false });

  console.log('  launching chrome on cdp :' + port);
  const wsUrl = await findPage(port, { label: 'mood_shots' });
  console.log('  found the game page');
  const ws = new WebSocket(wsUrl, { maxPayload: 256 * 1024 * 1024 });
  await new Promise(r => ws.on('open', r));
  console.log('  cdp socket open');
  await rpc(ws, 'Page.enable');
  await rpc(ws, 'Runtime.enable');
  console.log('  domains enabled');

  // FOREGROUND. rAF stops in a background tab and the canvas goes stale.
  try { execFileSync('osascript', ['-e', 'tell application "Google Chrome" to activate']); } catch {}
  await sleep(1200);

  // Wait for a playable first frame — the plate, the depth and the modules.
  // AN INSTRUMENT THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING:
  // if readiness never arrives, say which of the preconditions is missing.
  let ready = false;
  try { ready = await evalJs(ws, READY(600), 190000); } catch (e) { ready = false; }
  if (!ready) {
    const why = await evalJs(ws, `(function(){
      var S = window.SIM;
      return { url: location.href, SIM: !!S, Dialogue: !!window.Dialogue, Story: !!window.Story,
               meshes: S && S.gpu ? S.gpu().meshes : null,
               busy: S && S.transitions ? S.transitions().busy : null,
               shot: S && S.cine && S.cine() ? S.cine().shot : null,
               scene: S && S.scene ? S.scene() : null };
    })()`, 20000).catch(e => ({ evalFailed: String(e.message || e) }));
    throw new Error('never reached a playable first frame: ' + JSON.stringify(why));
  }
  await sleep(1500);
  console.log('  playable first frame reached');
  console.log('  modules: ' + JSON.stringify(await evalJs(ws,
    `({Dialogue: !!window.Dialogue, node: !!(window.Dialogue&&Dialogue.node), scene: SIM.scene()})`, 20000)));

  const want = ONLY.length ? ONLY : CH1;
  const manifest = [];

  for (const nid of want) {
    const n = await evalJs(ws, `(function(){
      var n = Dialogue.node(${JSON.stringify(nid)});
      if (!n) return null;
      var src = n.lines || [];
      return { count: src.length, speaker: n.speaker || null };
    })()`);
    if (!n) { console.log('  skip (no node): ' + nid); continue; }

    // START THE CONVERSATION AND DO NOT AWAIT IT. Dialogue.play() resolves when
    // the conversation FINISHES, and the thing that finishes it is the keypresses
    // below — so awaiting the promise here waits forever for work this loop has
    // not done yet. The IIFE drops it on the floor deliberately.
    await evalJs(ws, `(function(){ Dialogue.play(${JSON.stringify(nid)}); return true; })()`);
    await sleep(700);

    for (let i = 0; i < n.count + 2; i++) {
      // finish the typewriter so the face is settled and the box is full
      const st = await evalJs(ws, `(function(){
        var d = Dialogue.finishLine();
        if (!d || !d.open) return null;
        return { line: d.line, speaker: d.speaker, text: d.text, mode: d.mode,
                 portrait: d.portrait, cutin: d.cutin, choices: d.choices };
      })()`);
      if (!st) break;
      await sleep(320);

      const shot = await rpc(ws, 'Page.captureScreenshot', { format: 'png' });
      const idx = String(manifest.length).padStart(3, '0');
      const file = `${idx}-${nid.replace(/[^a-z0-9.]/gi, '_')}-${i}.png`;
      writeFileSync(join(OUT, file), Buffer.from(shot.data, 'base64'));
      // THE MOOD ACTUALLY ON SCREEN, read off the plate the runtime chose —
      // not off the JSON, which is the whole point of shooting this.
      const mood = /cutin-([a-z]+)\.png/.exec(st.cutin || '');
      manifest.push({
        file, node: nid, i, speaker: st.speaker, text: st.text, mode: st.mode,
        portrait: st.portrait, mood: mood ? mood[1] : (st.portrait === 'cutin' ? 'neutral' : null),
      });

      await evalJs(ws, `Dialogue.key('confirm')`).catch(() => {});
      await sleep(300);
      const open = await evalJs(ws, `!!(Dialogue.debug && Dialogue.debug().open)`);
      if (!open) break;
    }
    // make sure nothing is left open before the next node
    for (let k = 0; k < 10; k++) {
      const open = await evalJs(ws, `!!(Dialogue.debug && Dialogue.debug().open)`);
      if (!open) break;
      await evalJs(ws, `Dialogue.key('confirm')`).catch(() => {});
      await sleep(200);
    }
  }

  writeFileSync(join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 1));
  console.log(`\n${manifest.length} plates -> ${OUT}`);
  for (const m of manifest) {
    console.log(`  ${String(m.mood || '-').padEnd(11)} ${String(m.speaker || '').padEnd(8)} ${String(m.text || '').slice(0, 66)}`);
  }

  ws.close(); chrome.kill();
  rmSync(profile, { recursive: true, force: true });
})().catch(e => { console.error(e.message || e); process.exit(1); });
