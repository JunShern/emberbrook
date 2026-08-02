// Emberbrook — tiny relay server.
// The TV browser ("display") runs the whole game; phones ("controllers")
// just send joystick + button input through this WebSocket relay.

const express = require('express');
const http = require('http');
const path = require('path');
const os = require('os');
const QRCode = require('qrcode');
const { WebSocketServer } = require('ws');

const PORT = process.env.PORT || 3000;

function lanIP() {
  const ifs = os.networkInterfaces();
  let best = null;
  for (const name of Object.keys(ifs)) {
    for (const i of ifs[name] || []) {
      if (i.family === 'IPv4' && !i.internal) {
        if (name === 'en0' || name === 'en1') return i.address;
        best = best || i.address;
      }
    }
  }
  return best || 'localhost';
}
const joinUrl = () => `http://${lanIP()}:${PORT}/join`;

const fs = require('fs');

const app = express();
// / IS the chapter-select hub (public/index.html); /play.html IS the game (the
// engine file play3d.html served at the friendly path — no redirect, URL stays
// play.html); the legacy join-panel prototype lives at /join-legacy.html
app.get('/play.html', (_req, res) => res.sendFile(path.join(__dirname, 'public', 'play3d.html')));

// THE STORY PAGE REBUILDS ITSELF (user ruling 2026-08-02: "if we ever make a change to
// the story or the in-game dialogue, even if it's just with an NPC, this page should
// automatically reflect that simply by refreshing the page"). The manifest is derived
// from STORY.md, the chapter sources, dialogue.json, npcs.json, VOICES.md and the
// townmaps; regenerating on request is what makes a refresh equal the truth. It runs
// only when a source is NEWER than the manifest, so an idle reload costs nothing.
const STORY_SOURCES = [
  'STORY.md', 'docs/VOICES.md',
  'public/js/chapter1.js', 'public/js/chapter2.js', 'public/js/chapter3.js', 'public/js/main.js',
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

// dev helper: save a canvas capture from the browser into public/assets
// (nested paths allowed, but must resolve inside assets/)
app.post('/dev/save', (req, res) => {
  const { name, dataUrl } = req.body || {};
  if (!/^[\w./-]+\.png$/.test(name || '') || name.includes('..') ||
      !/^data:image\/png;base64,/.test(dataUrl || ''))
    return res.status(400).json({ error: 'bad request' });
  const assetsRoot = path.join(__dirname, 'public', 'assets');
  const target = path.resolve(assetsRoot, name);
  if (!target.startsWith(assetsRoot + path.sep)) return res.status(400).json({ error: 'bad path' });
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, Buffer.from(dataUrl.split(',')[1], 'base64'));
  res.json({ ok: true });
});
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

// dev helper: rebake a scene's mask after its maskraw changed
app.post('/dev/rebake', (req, res) => {
  const { scene } = req.body || {};
  if (!/^[\w-]+$/.test(scene || '')) return res.status(400).json({ error: 'bad request' });
  const dir = path.join(__dirname, 'public', 'assets', 'scenes', scene);
  if (!fs.existsSync(path.join(dir, 'bake.json'))) return res.status(400).json({ error: 'no bake.json' });
  const { execFile } = require('child_process');
  execFile('python3', [path.join(__dirname, 'tools', 'bakemask.py'), dir], (err, stdout) => {
    execFile('node', [path.join(__dirname, 'tools', 'build-manifest.mjs')], () =>
      res.json({ ok: !err, output: String(stdout || err) }));
  });
});

app.get('/join', (_req, res) => res.sendFile(path.join(__dirname, 'public', 'controller.html')));
app.get('/qr', async (_req, res) => {
  const png = await QRCode.toBuffer(joinUrl(), {
    margin: 1,
    scale: 6,
    color: { dark: '#3b2d1f', light: '#f8eed7' },
  });
  res.type('png').send(png);
});

const server = http.createServer(app);
const wss = new WebSocketServer({ server });

let display = null;
const controllers = new Map(); // id -> ws
let nextId = 1;

const send = (ws, msg) => {
  if (ws && ws.readyState === 1) ws.send(JSON.stringify(msg));
};

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    let msg;
    try { msg = JSON.parse(data); } catch { return; }

    if (msg.type === 'hello') {
      if (msg.role === 'display') {
        display = ws;
        ws.meta = { role: 'display' };
        send(ws, { type: 'ready', joinUrl: joinUrl() });
      } else {
        const id = nextId++;
        ws.meta = { role: 'controller', id };
        controllers.set(id, ws);
        send(ws, { type: 'welcome', id });
        send(display, { type: 'controller-joined', id });
      }
      return;
    }

    if (!ws.meta) return;
    if (ws.meta.role === 'controller') {
      // forward everything from a phone to the display, tagged with its id
      msg.from = ws.meta.id;
      send(display, msg);
    } else {
      // display -> one controller (msg.to) or broadcast to all
      if (msg.to != null) send(controllers.get(msg.to), msg);
      else for (const c of controllers.values()) send(c, msg);
    }
  });

  ws.on('close', () => {
    if (ws.meta && ws.meta.role === 'controller') {
      controllers.delete(ws.meta.id);
      send(display, { type: 'controller-left', id: ws.meta.id });
    } else if (ws === display) {
      display = null;
    }
  });
});

server.listen(PORT, () => {
  console.log('\n  ✦ Emberbrook is awake ✦\n');
  console.log(`  TV screen   →  http://localhost:${PORT}`);
  console.log(`  Controllers →  ${joinUrl()}   (phones on the same Wi-Fi)\n`);
});
