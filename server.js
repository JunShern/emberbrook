// Emberbrook — dev server: static files + the story-manifest rebuild gate +
// the asset-promote helper. The 2D-era WebSocket controller relay (/join, /qr,
// phones as gamepads) was retired with the legacy 2D runtime (Bet 6, 2026-08-05);
// it lives in git history and comes back with the two-player upgrade, if ever.

const express = require('express');
const http = require('http');
const path = require('path');

const PORT = process.env.PORT || 3000;

const fs = require('fs');

const app = express();
// / IS the chapter-select hub (public/index.html); /play.html IS the game (the
// engine file play3d.html served at the friendly path — no redirect, URL stays
// play.html)
app.get('/play.html', (_req, res) => res.sendFile(path.join(__dirname, 'public', 'play3d.html')));

// THE STORY PAGE REBUILDS ITSELF (user ruling 2026-08-02: "if we ever make a change to
// the story or the in-game dialogue, even if it's just with an NPC, this page should
// automatically reflect that simply by refreshing the page"). The manifest is derived
// from STORY.md, the chapter sources, dialogue.json, npcs.json, VOICES.md and the
// townmaps; regenerating on request is what makes a refresh equal the truth. It runs
// only when a source is NEWER than the manifest, so an idle reload costs nothing.
const STORY_SOURCES = [
  'STORY.md', 'docs/VOICES.md',
  'public/js/chapter1.js', 'public/js/chapter2.js', 'public/js/chapter3.js', 'tools/build-story.mjs',
  'public/game/dialogue.json', 'public/game/npcs.json',
  'public/townmap/emberbrook.map.json', 'public/townmap/dellhollow.map.json',
  'public/assets/characters/cutins.json', 'tools/characters/cutins.spec.json',
];
const STORY_MANIFEST = path.join(__dirname, 'public/assets/story-manifest.json');
let storyBuilding = null;
function refreshStoryManifest() {
  if (storyBuilding) return storyBuilding;                 // coalesce concurrent loads
  let built = 0;
  try { built = fs.statSync(STORY_MANIFEST).mtimeMs; } catch { /* never built */ }
  const newest = STORY_SOURCES.reduce((a, rel) => {
    try { return Math.max(a, fs.statSync(path.join(__dirname, rel)).mtimeMs); } catch { return a; }
  }, 0);
  if (built && newest <= built) return Promise.resolve('current');
  storyBuilding = new Promise((resolve) => {
    require('child_process').execFile('node', [path.join(__dirname, 'tools/build-story.mjs')],
      { cwd: __dirname }, (err, _out, stderr) => {
        // A build failure must NOT blank the page: fall through to the last good
        // manifest and let the page show its own generated-at stamp.
        if (err) console.error('[story] rebuild failed, serving last good manifest:\n' + (stderr || err.message));
        storyBuilding = null;
        resolve(err ? 'stale' : 'rebuilt');
      });
  });
  return storyBuilding;
}
const storyGate = (req, res, next) => { refreshStoryManifest().then(() => next(), () => next()); };
app.get('/story.html', storyGate);
app.get('/assets/story-manifest.json', storyGate);

app.use(express.static(path.join(__dirname, 'public'), {
  setHeaders(res, filePath) {
    // never let stale game code stick in a browser cache during development
    if (/\.(js|html|png)$/.test(filePath)) res.set('Cache-Control', 'no-store');
  },
}));
app.use('/docs', express.static(path.join(__dirname, 'docs'), {
  setHeaders(res, filePath) {
    if (/\.(js|html|png)$/.test(filePath)) res.set('Cache-Control', 'no-store');
  },
}));
app.use(express.json({ limit: '30mb' }));

// dev helper: promote a candidate asset into a live slot.
// Current slot file is backed up into candidates/ first, so picks are reversible.
app.post('/dev/promote', (req, res) => {
  const { group, name, slot, candidate } = req.body || {};
  const okName = (v) => typeof v === 'string' && /^[\w./-]+$/.test(v) && !v.includes('..');
  if (!['characters', 'scenes'].includes(group) || !okName(name) || !okName(slot) || !okName(candidate))
    return res.status(400).json({ error: 'bad request' });
  const dir = path.join(__dirname, 'public', 'assets', group, name);
  const slotPath = path.resolve(dir, slot);
  const candPath = path.resolve(dir, candidate);
  if (!slotPath.startsWith(dir + path.sep) || !candPath.startsWith(dir + path.sep) || !fs.existsSync(candPath))
    return res.status(400).json({ error: 'bad path' });
  const candDir = path.join(dir, 'candidates');
  fs.mkdirSync(candDir, { recursive: true });
  if (fs.existsSync(slotPath)) {
    const backup = path.join(candDir, 'replaced-' + slot.replace(/[/]/g, '_') + '-' + Date.now() + '.png');
    fs.copyFileSync(slotPath, backup);
  }
  fs.copyFileSync(candPath, slotPath);
  const { execFile } = require('child_process');
  execFile('node', [path.join(__dirname, 'tools', 'build-manifest.mjs')], () => res.json({ ok: true }));
});

const server = http.createServer(app);
server.listen(PORT, () => {
  console.log('\n  ✦ Emberbrook is awake ✦\n');
  console.log(`  Game →  http://localhost:${PORT}\n`);
});
