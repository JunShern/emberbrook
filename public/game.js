'use strict';
/* ============================================================
   EMBERBROOK — Chapter One: The Dimming Heartlight
   The TV browser runs the whole simulation; phones send input.
   ============================================================ */

// ---------- canvas ----------
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let cw = 0, ch = 0, dpr = 1;
function resize() {
  dpr = Math.min(window.devicePixelRatio || 1, 2);
  cw = window.innerWidth; ch = window.innerHeight;
  canvas.width = cw * dpr; canvas.height = ch * dpr;
  canvas.style.width = cw + 'px'; canvas.style.height = ch + 'px';
}
window.addEventListener('resize', resize);
resize();

// ---------- constants ----------
const T = 16, MAP_W = 48, MAP_H = 36;
const GRASS = 0, PATH = 1, PLAZA = 2, WATER = 3, SAND = 4, DOCK = 5;
const SPEED = 72;

const PALETTES = [
  { tunic: '#6f9f4f', hair: '#5b3a29' }, // Clover
  { tunic: '#4f7fae', hair: '#2e2b3a' }, // Bluebell
  { tunic: '#c96a8b', hair: '#402a20' }, // Rose
  { tunic: '#d9a441', hair: '#8a4b23' }, // Marigold
];
const SKIN = '#eec39a';

// ---------- state ----------
let time = 0;
const players = [null, null];
const flags = { questGiven: false, gateOpen: false, gateOpening: 0, ended: false, endT: 0 };
let dlg = null;             // { lines:[{who,color,text}], i, chars, onFinish }
let banner = null;          // { title, sub, t, dur }
let shake = 0;
const particles = [];       // smoke, hearts, petals, motes
const cam = { x: MAP_W * T / 2, y: MAP_H * T / 2, zoom: 3 };

// seeded rng for deterministic map decoration
let seed = 20260718;
function rnd() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }

/* ============================================================
   WORLD
   ============================================================ */
const tiles = [], coll = [];
for (let y = 0; y < MAP_H; y++) { tiles.push(new Array(MAP_W).fill(GRASS)); coll.push(new Array(MAP_W).fill(0)); }

function fillT(x0, y0, x1, y1, t) {
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++)
    if (x >= 0 && y >= 0 && x < MAP_W && y < MAP_H) tiles[y][x] = t;
}

// paths & plaza
fillT(23, 0, 25, 12, PATH);                       // north road through the gate
for (let y = 0; y < MAP_H; y++) for (let x = 0; x < MAP_W; x++) {
  const dx = (x + 0.5 - 24.5) / 4.6, dy = (y + 0.5 - 15.5) / 4.6;
  if (dx * dx + dy * dy < 1) tiles[y][x] = PLAZA;
}
fillT(12, 14, 20, 15, PATH);                      // west lane to the bakery
fillT(23, 19, 24, 28, PATH);                      // south lane
fillT(10, 27, 23, 28, PATH);                      // to the cottage
fillT(25, 27, 30, 28, PATH);                      // to the pond

// pond + sand + dock
for (let y = 0; y < MAP_H; y++) for (let x = 0; x < MAP_W; x++) {
  const dx = (x + 0.5 - 37.5) / 7.8, dy = (y + 0.5 - 28.5) / 5.4;
  const dx2 = (x + 0.5 - 37.5) / 6.5, dy2 = (y + 0.5 - 28.5) / 4.2;
  if (dx2 * dx2 + dy2 * dy2 < 1) { tiles[y][x] = WATER; coll[y][x] = 1; }
  else if (dx * dx + dy * dy < 1 && tiles[y][x] === GRASS) tiles[y][x] = SAND;
}
for (let x = 31; x <= 35; x++) { tiles[28][x] = DOCK; coll[28][x] = 0; }

// houses  {tx,ty,tw,th, style}
const houses = [
  { tx: 11, ty: 7,  tw: 6, th: 6, style: 'bakery' },
  { tx: 29, ty: 6,  tw: 7, th: 6, style: 'elder'  },
  { tx: 8,  ty: 21, tw: 5, th: 6, style: 'cottage'},
];
houses.forEach(h => { for (let y = h.ty; y < h.ty + h.th; y++) for (let x = h.tx; x < h.tx + h.tw; x++) coll[y][x] = 1; });

// map border (leave the gate opening x 23..25 at the top)
for (let y = 0; y < MAP_H; y++) for (let x = 0; x < MAP_W; x++) {
  if (x < 1 || x >= MAP_W - 1 || y >= MAP_H - 1) coll[y][x] = 1;
  if (y < 1 && !(x >= 23 && x <= 25)) coll[y][x] = 1;
}

// the Old Gate (closed until the sigils are lit)
const gate = { x0: 21, x1: 27, y0: 2, y1: 4 };
const gateCells = [];
for (let y = gate.y0; y <= gate.y1; y++) for (let x = gate.x0; x <= gate.x1; x++) {
  coll[y][x] = 1; if (x >= 23 && x <= 25) gateCells.push([x, y]);
}
function openGate() { gateCells.forEach(([x, y]) => coll[y][x] = 0); }

// heartlight pedestal
const heartlight = { x: 25 * T, y: 15.5 * T + 6, name: 'the Heartlight' };
coll[15][24] = 1; coll[15][25] = 1;

// sigil plates
const plates = [
  { x: 22.5 * T, y: 6.5 * T, hold: 0 },
  { x: 26.5 * T, y: 6.5 * T, hold: 0 },
];

// trees — forest ring + scattered clumps
const trees = [];
function addTree(tx, ty) {
  if (tiles[ty] === undefined || tiles[ty][tx] !== GRASS || coll[ty][tx]) return;
  coll[ty][tx] = 1;
  trees.push({ x: tx * T + 8, y: ty * T + 14, big: rnd() > 0.5 });
}
for (let x = 1; x < MAP_W - 1; x += 2) {
  if (!(x >= 21 && x <= 27)) addTree(x, 1 + (x % 3 === 0 ? 1 : 0));
  addTree(x + (x % 4 === 0 ? 1 : 0), MAP_H - 2 - (x % 3));
}
for (let y = 3; y < MAP_H - 2; y += 2) { addTree(1 + (y % 3 === 0 ? 1 : 0), y); addTree(MAP_W - 2 - (y % 3 === 0 ? 1 : 0), y); }
for (let i = 0; i < 46; i++) addTree(2 + Math.floor(rnd() * (MAP_W - 4)), 2 + Math.floor(rnd() * (MAP_H - 4)));

// flowers
const FLOWER_COLORS = ['#e8788a', '#f2d16b', '#e8e2f2', '#e8a04c'];
const flowers = [];
for (let i = 0; i < 90; i++) {
  const tx = 1 + Math.floor(rnd() * (MAP_W - 2)), ty = 1 + Math.floor(rnd() * (MAP_H - 2));
  if (tiles[ty][tx] === GRASS && !coll[ty][tx])
    flowers.push({ x: tx * T + 3 + rnd() * 10, y: ty * T + 3 + rnd() * 10, c: FLOWER_COLORS[Math.floor(rnd() * 4)], ph: rnd() * 6 });
}

/* ============================================================
   NPCS & DIALOGUE
   ============================================================ */
function bothPresent() { return players[0] && players[1]; }
function bothNear(x, y, r) {
  return bothPresent() && players.every(p => Math.hypot(p.x - x, p.y - y) < r);
}

const ELDER_C = '#8a6bae', POPPY_C = '#c9584a', FINN_C = '#4f7fae', CAT_C = '#d9a441';
const L = (who, color, text) => ({ who, color, text });

const npcs = [
  {
    name: 'Elder Rowan', x: 27.5 * T, y: 14.5 * T, dir: 'down', kind: 'elder', talked: 0,
    lines() {
      if (!flags.questGiven) {
        if (!bothNear(this.x, this.y, 96)) return [
          L('Elder Rowan', ELDER_C, players.filter(Boolean).length < 2
            ? 'Hm? Just the one of you? This concerns two hearts, dear — fetch your partner, and come find me together.'
            : 'Come closer, the both of you. Old ears, old eyes — I’ll not shout across the square.'),
        ];
        return [
          L('Elder Rowan', ELDER_C, 'Ah — there you are. Both of you. Good, good.'),
          L('Elder Rowan', ELDER_C, 'You’ve seen the Heartlight. Dim as a spent candle, and Emberbrook grows colder by the week.'),
          L('Elder Rowan', ELDER_C, 'Three hundred years it has burned — kindled long ago at a shrine deep in the Whisperwood, beyond the Old Gate.'),
          L('Elder Rowan', ELDER_C, 'The flame must be carried home again. And it cannot be done alone... the old paths were made for two.'),
          L('Elder Rowan', ELDER_C, 'Take this ember. Keep it warm between you. Will you go?'),
          L('Elder Rowan', ELDER_C, '...Ha! I knew you would. The Gate answers only to two who stand as one — the twin sigils before it will show you the way.'),
        ];
      }
      if (!flags.gateOpen) return [L('Elder Rowan', ELDER_C, 'Stand on the twin sigils by the Old Gate — together. The Gate will know you.')];
      return [L('Elder Rowan', ELDER_C, 'Walk close, and walk kindly. Come home to us.')];
    },
    onFinish() { if (!flags.questGiven && bothNear(this.x, this.y, 96)) giveQuest(); },
  },
  {
    name: 'Baker Poppy', x: 13.5 * T, y: 14.7 * T, dir: 'down', kind: 'baker', talked: 0,
    lines() {
      this.talked++;
      if (this.talked === 1) return [
        L('Baker Poppy', POPPY_C, 'Fresh honeybuns! Mind the steam, loves.'),
        L('Baker Poppy', POPPY_C, 'You’re the pair from the little cottage on the south lane, aren’t you? Sweet as spring, the both of you.'),
        L('Baker Poppy', POPPY_C, 'Oh — Elder Rowan’s been asking after you. He’s in the square, by the Heartlight. Can’t miss him.'),
      ];
      return [L('Baker Poppy', POPPY_C, 'The buns are hot. Blow on them twice — once for luck, and once because they are genuinely very hot.')];
    },
  },
  {
    name: 'Fisher Finn', x: 35 * T + 12, y: 28 * T + 4, dir: 'right', kind: 'finn', talked: 0,
    lines() {
      this.talked++;
      if (this.talked === 1) return [
        L('Fisher Finn', FINN_C, 'The fish stopped bitin’ the day the Heartlight went dim. Fish know things, I reckon.'),
        L('Fisher Finn', FINN_C, 'If Rowan sends you past the Old Gate — bring a coat. And snacks. Mostly snacks.'),
      ];
      return [L('Fisher Finn', FINN_C, 'Some folk say talkin’ to fish is odd. The fish and I ignore them.')];
    },
  },
  {
    name: 'Mochi', x: 16 * T, y: 17 * T, dir: 'left', kind: 'cat', talked: 0,
    home: { x: 16 * T, y: 17 * T }, tx: 16 * T, ty: 17 * T, wanderT: 2,
    lines() {
      this.talked++;
      const meows = [
        'Mrrraow. (Mochi headbutts your ankle, then pretends it never happened.)',
        '(Mochi has become a loaf. Disturb at your peril.)',
        'Prrrrb?',
      ];
      return [L('Mochi', CAT_C, meows[(this.talked - 1) % meows.length])];
    },
  },
];

const interactables = [
  ...npcs,
  { name: 'the Heartlight', x: heartlight.x, y: heartlight.y, kind: 'heartlight',
    lines: () => [L('✦', '#e8a04c', 'The Heartlight of Emberbrook. Its glow is thin as morning mist — it used to warm the whole square.')] },
];

function startDialog(thing, talker) {
  const lines = thing.lines();
  if (!lines || !lines.length) return;
  if (thing.dir !== undefined && talker) {
    const dx = talker.x - thing.x, dy = talker.y - thing.y;
    thing.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
  }
  dlg = { lines, i: 0, chars: 0, onFinish: thing.onFinish ? thing.onFinish.bind(thing) : null };
  Audio1.blip(520);
}
function advanceDialog() {
  if (!dlg) return;
  const line = dlg.lines[dlg.i];
  if (dlg.chars < line.text.length) { dlg.chars = line.text.length; return; }
  dlg.i++; dlg.chars = 0;
  if (dlg.i >= dlg.lines.length) {
    const fin = dlg.onFinish; dlg = null;
    if (fin) fin();
  } else Audio1.blip(520);
}

function giveQuest() {
  flags.questGiven = true;
  banner = { title: '✦ Quest — The Dimming Heartlight ✦', sub: 'Carry the ember to the shrine in the Whisperwood', t: 0, dur: 6 };
  Audio1.chime();
  net.broadcast({ type: 'buzz', ms: 150 });
}

function objectiveText() {
  if (flags.ended) return '';
  if (!players[0] && !players[1]) return 'Waiting for two travellers…';
  if (!flags.questGiven) return 'Explore Emberbrook — speak with the townsfolk';
  if (!flags.gateOpen) return 'Stand on the twin sigils before the Old Gate — together';
  return 'Step through the Old Gate — together';
}

/* ============================================================
   NETWORKING (display side)
   ============================================================ */
const net = {
  ws: null,
  send(msg) { if (this.ws && this.ws.readyState === 1) this.ws.send(JSON.stringify(msg)); },
  broadcast(msg) { this.send(msg); },
  to(id, msg) { msg.to = id; this.send(msg); },
  connect() {
    this.ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host);
    this.ws.onopen = () => this.send({ type: 'hello', role: 'display' });
    this.ws.onclose = () => setTimeout(() => this.connect(), 1500);
    this.ws.onmessage = (ev) => {
      let m; try { m = JSON.parse(ev.data); } catch { return; }
      handleNet(m);
    };
  },
};

function playerById(id) { return players.find(p => p && p.id === id); }

function makePlayer(slot, id, name, hero, kb) {
  const spawn = [{ x: 11 * T, y: 28.5 * T }, { x: 13 * T, y: 28.5 * T }][slot];
  return {
    id, name, slot, kb: !!kb, pal: PALETTES[hero % 4],
    x: spawn.x, y: spawn.y, dir: 'up', moving: false, animT: 0,
    input: { x: 0, y: 0 }, a: false, aEdge: false,
    connected: true, lastPrompt: '',
  };
}

function assignPlayer(m) {
  // reclaim a seat after a phone or TV refresh (matched by name)
  let slot = players.findIndex(p => p && p.name === m.name && (!p.connected || p.kb));
  if (slot === -1) slot = players.findIndex(p => p === null);
  if (slot === -1) { net.to(m.from, { type: 'full' }); return; }
  const old = players[slot];
  players[slot] = makePlayer(slot, m.from, m.name, m.hero || 0, false);
  if (old) { players[slot].x = old.x; players[slot].y = old.y; }
  net.to(m.from, { type: 'assign', slot, name: m.name });
  Audio1.sparkle();
  if (!banner && !flags.questGiven) banner = { title: 'Emberbrook', sub: 'Chapter One — The Dimming Heartlight', t: 0, dur: 6 };
  updatePanel();
}

function handleNet(m) {
  if (m.type === 'ready') {
    const el = document.getElementById('joinUrl');
    if (el) el.textContent = m.joinUrl;
    net.broadcast({ type: 'who' });   // any phones already open re-send their join
  }
  else if (m.type === 'join') assignPlayer(m);
  else if (m.type === 'input') {
    const p = playerById(m.from);
    if (p) { p.input.x = Math.max(-1, Math.min(1, +m.x || 0)); p.input.y = Math.max(-1, Math.min(1, +m.y || 0)); }
  }
  else if (m.type === 'btn') {
    const p = playerById(m.from);
    if (p) { if (m.down && !p.a) p.aEdge = true; p.a = !!m.down; }
  }
  else if (m.type === 'controller-left') {
    const p = playerById(m.id);
    if (p) { p.connected = false; p.input.x = 0; p.input.y = 0; p.a = false; updatePanel(); }
  }
}
net.connect();

function updatePanel() {
  const panel = document.getElementById('joinPanel');
  for (let i = 0; i < 2; i++) {
    const el = document.getElementById('slot' + i);
    const p = players[i];
    el.innerHTML = p
      ? (p.connected ? `♥ <b>${p.name}</b> — ready` : `✧ <b>${p.name}</b> — <i>reconnecting…</i>`)
      : `✧ Player ${i === 0 ? 'One' : 'Two'} — <i>awaiting…</i>`;
  }
  const full = players[0] && players[1] && players[0].connected && players[1].connected;
  panel.classList.toggle('hidden', !!full);
}

/* ============================================================
   KEYBOARD FALLBACK (testing on the mac itself)
   ============================================================ */
const keys = {};
window.addEventListener('keydown', (e) => {
  keys[e.code] = true;
  if (e.code === 'KeyM') Audio1.toggleMusic();
  const P1K = ['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyE'], P2K = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter'];
  if (P1K.includes(e.code) && !players[0]) { players[0] = makePlayer(0, 'kb1', 'P1 (keys)', 0, true); updatePanel(); }
  if (P2K.includes(e.code) && !players[1]) { players[1] = makePlayer(1, 'kb2', 'P2 (keys)', 2, true); updatePanel(); }
  if (e.code === 'KeyE' && players[0] && players[0].kb) players[0].aEdge = true;
  if (e.code === 'Enter' && players[1] && players[1].kb) players[1].aEdge = true;
});
window.addEventListener('keyup', (e) => { keys[e.code] = false; });

function keyboardInput() {
  const p1 = players[0], p2 = players[1];
  if (p1 && p1.kb) {
    p1.input.x = (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0);
    p1.input.y = (keys.KeyS ? 1 : 0) - (keys.KeyW ? 1 : 0);
  }
  if (p2 && p2.kb) {
    p2.input.x = (keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0);
    p2.input.y = (keys.ArrowDown ? 1 : 0) - (keys.ArrowUp ? 1 : 0);
  }
}

/* ============================================================
   UPDATE
   ============================================================ */
function solidAt(px, py) {
  const tx = Math.floor(px / T), ty = Math.floor(py / T);
  if (tx < 0 || ty < 0 || tx >= MAP_W || ty >= MAP_H) return true;
  return coll[ty][tx] === 1;
}
function blocked(x, y) {
  return solidAt(x - 4, y - 5) || solidAt(x + 4, y - 5) || solidAt(x - 4, y - 1) || solidAt(x + 4, y - 1);
}

function update(dt) {
  time += dt;
  keyboardInput();
  const frozen = dlg !== null || flags.ended;

  for (const p of players) {
    if (!p) continue;
    let vx = p.input.x, vy = p.input.y;
    const len = Math.hypot(vx, vy);
    if (len > 1) { vx /= len; vy /= len; }
    p.moving = !frozen && len > 0.12;
    if (p.moving) {
      const nx = p.x + vx * SPEED * dt;
      if (!blocked(nx, p.y)) p.x = nx;
      const ny = p.y + vy * SPEED * dt;
      if (!blocked(p.x, ny)) p.y = ny;
      p.dir = Math.abs(vx) > Math.abs(vy) ? (vx > 0 ? 'right' : 'left') : (vy > 0 ? 'down' : 'up');
      p.animT += dt;
    }
    // A button
    if (p.aEdge) {
      p.aEdge = false;
      if (dlg) advanceDialog();
      else if (!flags.ended) {
        const near = nearestInteractable(p);
        if (near) startDialog(near, p);
      }
    }
  }

  // NPCs face whoever is close; the cat wanders
  for (const n of npcs) {
    if (n.kind === 'cat' && !frozen) {
      n.wanderT -= dt;
      if (n.wanderT <= 0) {
        n.wanderT = 2 + rnd() * 4;
        const a = rnd() * Math.PI * 2, r = 20 + rnd() * 36;
        const tx = n.home.x + Math.cos(a) * r, ty = n.home.y + Math.sin(a) * r;
        if (!solidAt(tx, ty)) { n.tx = tx; n.ty = ty; }
      }
      const dx = n.tx - n.x, dy = n.ty - n.y, d = Math.hypot(dx, dy);
      if (d > 2) { n.x += dx / d * 22 * dt; n.y += dy / d * 22 * dt; n.dir = dx > 0 ? 'right' : 'left'; }
    } else if (n.kind !== 'cat') {
      const p = closestPlayer(n.x, n.y);
      if (p && Math.hypot(p.x - n.x, p.y - n.y) < 52 && !dlg) {
        const dx = p.x - n.x, dy = p.y - n.y;
        n.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
      }
    }
  }

  // sigil plates → gate
  if (flags.questGiven && !flags.gateOpen && !flags.gateOpening) {
    let all = true;
    for (const pl of plates) {
      const on = players.some(p => p && Math.hypot(p.x - pl.x, p.y - pl.y) < 15);
      pl.hold = on ? Math.min(1, pl.hold + dt / 1.2) : Math.max(0, pl.hold - dt * 2);
      if (pl.hold < 1) all = false;
    }
    if (all && bothPresent()) {
      flags.gateOpening = 0.0001;
      Audio1.rumble();
      net.broadcast({ type: 'buzz', ms: 300 });
    }
  }
  if (flags.gateOpening && !flags.gateOpen) {
    flags.gateOpening = Math.min(1, flags.gateOpening + dt / 1.8);
    shake = Math.max(shake, 2.5 * (1 - flags.gateOpening));
    if (flags.gateOpening >= 1) { flags.gateOpen = true; openGate(); Audio1.chime(); }
  }

  // chapter end — both step through the gate
  if (flags.gateOpen && !flags.ended && bothPresent() &&
      players.every(p => p.y < 1.8 * T)) {
    flags.ended = true;
    Audio1.finale();
    net.broadcast({ type: 'end' });
  }
  if (flags.ended) flags.endT += dt;

  shake = Math.max(0, shake - dt * 4);

  // ambient particles
  if (Math.random() < dt * 2.2) {  // chimney smoke
    for (const h of houses) particles.push({ kind: 'smoke', x: (h.tx + h.tw - 1.2) * T, y: (h.ty + 0.4) * T, vy: -9, life: 3, r: 1.5 + Math.random() * 1.5 });
  }
  if (Math.random() < dt * 0.8) {  // drifting petals
    particles.push({ kind: 'petal', x: Math.random() * MAP_W * T, y: -8, vx: 8 + Math.random() * 8, vy: 13, life: 12, c: FLOWER_COLORS[Math.floor(Math.random() * 4)] });
  }
  if (bothPresent() && !flags.ended && Math.hypot(players[0].x - players[1].x, players[0].y - players[1].y) < 22 && Math.random() < dt * 1.2) {
    particles.push({ kind: 'heart', x: (players[0].x + players[1].x) / 2, y: Math.min(players[0].y, players[1].y) - 24, vy: -14, life: 1.4 });
  }
  if (Math.random() < dt * 3) {    // heartlight motes
    particles.push({ kind: 'mote', x: heartlight.x + (Math.random() - 0.5) * 26, y: heartlight.y - 8, vy: -7, life: 2.5 });
  }
  for (let i = particles.length - 1; i >= 0; i--) {
    const pt = particles[i];
    pt.life -= dt; pt.y += (pt.vy || 0) * dt; pt.x += (pt.vx || 0) * dt + Math.sin(time * 2 + i) * 6 * dt;
    if (pt.life <= 0) particles.splice(i, 1);
  }

  if (banner) { banner.t += dt; if (banner.t > banner.dur) banner = null; }

  updateCamera(dt);
  updatePrompts();
}

function closestPlayer(x, y) {
  let best = null, bd = 1e9;
  for (const p of players) if (p) {
    const d = Math.hypot(p.x - x, p.y - y);
    if (d < bd) { bd = d; best = p; }
  }
  return best;
}
function nearestInteractable(p) {
  let best = null, bd = 30;
  for (const it of interactables) {
    const d = Math.hypot(p.x - it.x, p.y - it.y);
    if (d < bd) { bd = d; best = it; }
  }
  return best;
}

function updatePrompts() {
  for (const p of players) {
    if (!p || p.kb || !p.connected) continue;
    let text = '';
    if (flags.ended) text = '';
    else if (dlg) text = 'Next ▸';
    else {
      const near = nearestInteractable(p);
      if (near) text = near.kind === 'heartlight' ? 'A — look at the Heartlight' : 'A — talk to ' + near.name;
      else if (flags.questGiven && !flags.gateOpen && plates.some(pl => Math.hypot(p.x - pl.x, p.y - pl.y) < 26))
        text = 'Stand on the sigil — together';
    }
    if (text !== p.lastPrompt) { p.lastPrompt = text; net.to(p.id, { type: 'prompt', text }); }
  }
}

function updateCamera(dt) {
  const ps = players.filter(Boolean);
  let tx, ty, tz;
  if (ps.length === 0) { tx = 24.5 * T; ty = 17 * T; tz = ch / 300; }
  else {
    const xs = ps.map(p => p.x), ys = ps.map(p => p.y);
    const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
    tx = (minx + maxx) / 2; ty = (miny + maxy) / 2 - 8;
    const needW = (maxx - minx) + 220, needH = (maxy - miny) + 200;
    tz = Math.min(cw / needW, ch / needH);
    tz = Math.max(ch / 460, Math.min(ch / 235, tz));
  }
  const k = Math.min(1, dt * 4);
  cam.zoom += (tz - cam.zoom) * k;
  cam.x += (tx - cam.x) * k;
  cam.y += (ty - cam.y) * k;
  const vw = cw / cam.zoom, vh = ch / cam.zoom;
  cam.x = Math.max(vw / 2, Math.min(MAP_W * T - vw / 2, cam.x));
  cam.y = Math.max(vh / 2, Math.min(MAP_H * T - vh / 2, cam.y));
  if (vw >= MAP_W * T) cam.x = MAP_W * T / 2;
  if (vh >= MAP_H * T) cam.y = MAP_H * T / 2;
}

/* ============================================================
   AUDIO — tiny cozy sequencer + sfx
   ============================================================ */
const Audio1 = {
  ctx: null, master: null, musicGain: null, started: false, musicOn: true, step: 0, nextT: 0, timer: null,
  CHORD_ROOTS: [48, 45, 41, 43],
  CHORDS: [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]],
  MELODY: [76, 0, 79, 0, 81, 0, 79, 0, 76, 0, 74, 0, 72, 0, 74, 76,
           74, 0, 72, 0, 69, 0, 67, 0, 72, 0, 74, 0, 72, 0, 0, 0],
  STEP: 0.34,
  f(m) { return 440 * Math.pow(2, (m - 69) / 12); },
  init() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AC();
    this.master = this.ctx.createGain(); this.master.gain.value = 0.9;
    const lp = this.ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 3800;
    this.master.connect(lp); lp.connect(this.ctx.destination);
    this.musicGain = this.ctx.createGain(); this.musicGain.gain.value = 0.9;
    this.musicGain.connect(this.master);
    this.nextT = this.ctx.currentTime + 0.1;
    this.timer = setInterval(() => this.schedule(), 90);
    this.started = true;
    document.getElementById('musicHint').classList.add('gone');
  },
  note(m, t, dur, type, gain, dest) {
    const o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = type; o.frequency.value = this.f(m);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(dest || this.master);
    o.start(t); o.stop(t + dur + 0.05);
  },
  schedule() {
    if (!this.ctx || !this.musicOn || flags.ended) return;
    while (this.nextT < this.ctx.currentTime + 0.4) {
      const s = this.step % 32, chord = Math.floor(s / 8), t = this.nextT;
      const mel = this.MELODY[s];
      if (mel) this.note(mel, t, 0.55, 'triangle', 0.055, this.musicGain);
      if (s % 8 === 0) {
        this.note(this.CHORD_ROOTS[chord], t, 2.4, 'sine', 0.09, this.musicGain);
        for (const c of this.CHORDS[chord]) this.note(c, t + 0.02, 2.4, 'sine', 0.016, this.musicGain);
      }
      if (s % 8 === 4) this.note(this.CHORD_ROOTS[chord] + 7, t, 1.1, 'sine', 0.05, this.musicGain);
      if (s === 0) this.note(96, t, 1.4, 'sine', 0.02, this.musicGain);
      this.step++; this.nextT += this.STEP;
    }
  },
  toggleMusic() {
    if (!this.ctx) { this.init(); return; }
    this.musicOn = !this.musicOn;
    this.musicGain.gain.value = this.musicOn ? 0.9 : 0;
  },
  blip(freq) {
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = 'square'; o.frequency.value = freq || 520;
    g.gain.setValueAtTime(0.03, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.06);
    o.connect(g); g.connect(this.master); o.start(t); o.stop(t + 0.08);
  },
  chime() {
    if (!this.ctx) return;
    [72, 76, 79, 84].forEach((m, i) => this.note(m, this.ctx.currentTime + i * 0.1, 0.8, 'triangle', 0.09));
  },
  sparkle() {
    if (!this.ctx) return;
    [84, 88].forEach((m, i) => this.note(m, this.ctx.currentTime + i * 0.07, 0.3, 'sine', 0.05));
  },
  rumble() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime, len = 2;
    const buf = this.ctx.createBuffer(1, this.ctx.sampleRate * len, this.ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
    const src = this.ctx.createBufferSource(); src.buffer = buf;
    const lp = this.ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 130;
    const g = this.ctx.createGain(); g.gain.value = 0.5;
    src.connect(lp); lp.connect(g); g.connect(this.master); src.start(t);
  },
  finale() {
    if (!this.ctx) return;
    [60, 64, 67, 72, 76].forEach((m, i) => this.note(m, this.ctx.currentTime + i * 0.16, 2.2, 'triangle', 0.08));
  },
};
window.addEventListener('pointerdown', () => Audio1.init(), { once: false });
window.addEventListener('keydown', () => Audio1.init(), { once: true });

/* ============================================================
   RENDER
   ============================================================ */
function hash(x, y) { return ((x * 73856093) ^ (y * 19349663)) >>> 0; }

function render() {
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#141009';
  ctx.fillRect(0, 0, cw, ch);
  ctx.imageSmoothingEnabled = false;

  const sx = shake ? (Math.sin(time * 55) * shake) : 0;
  const sy = shake ? (Math.cos(time * 47) * shake) : 0;
  ctx.save();
  ctx.translate(cw / 2, ch / 2);
  ctx.scale(cam.zoom, cam.zoom);
  ctx.translate(-cam.x + sx, -cam.y + sy);

  drawGround();
  drawPlates();
  flowers.forEach(drawFlower);

  // depth-sorted world
  const items = [];
  houses.forEach(h => items.push({ y: (h.ty + h.th) * T - 2, d: () => drawHouse(h) }));
  trees.forEach(t => items.push({ y: t.y, d: () => drawTree(t) }));
  items.push({ y: heartlight.y + 6, d: drawHeartlight });
  items.push({ y: gate.y1 * T + T, d: drawGate });
  npcs.forEach(n => items.push({ y: n.y, d: () => (n.kind === 'cat' ? drawCat(n) : drawChar(n.x, n.y, n.dir, 0, false, n.kind)) }));
  players.forEach(p => { if (p) items.push({ y: p.y, d: () => drawChar(p.x, p.y, p.dir, p.animT, p.moving, 'hero', p.pal, p.connected) }); });
  items.sort((a, b) => a.y - b.y);
  items.forEach(it => it.d());

  drawParticles();
  ctx.restore();

  drawScreenUI();
}

// ---------- ground ----------
const GRASS_SHADES = ['#7ba254', '#79a052', '#7ea757'];
function drawGround() {
  const x0 = Math.max(0, Math.floor((cam.x - cw / 2 / cam.zoom) / T) - 1);
  const x1 = Math.min(MAP_W - 1, Math.ceil((cam.x + cw / 2 / cam.zoom) / T) + 1);
  const y0 = Math.max(0, Math.floor((cam.y - ch / 2 / cam.zoom) / T) - 1);
  const y1 = Math.min(MAP_H - 1, Math.ceil((cam.y + ch / 2 / cam.zoom) / T) + 1);
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
    const t = tiles[y][x], px = x * T, py = y * T, h = hash(x, y);
    if (t === GRASS) {
      ctx.fillStyle = GRASS_SHADES[h % 3];
      ctx.fillRect(px, py, T, T);
      if (h % 7 === 0) { ctx.fillStyle = '#6a9147'; ctx.fillRect(px + (h % 12), py + (h % 9), 1, 3); ctx.fillRect(px + (h % 12) + 2, py + (h % 9) + 1, 1, 2); }
    } else if (t === PATH) {
      ctx.fillStyle = '#d8b57e'; ctx.fillRect(px, py, T, T);
      ctx.fillStyle = '#c39c63';
      if (h % 5 === 0) ctx.fillRect(px + (h % 11), py + (h % 13), 2, 2);
      if (h % 3 === 0) ctx.fillRect(px + ((h >> 3) % 13), py + ((h >> 5) % 11), 1, 1);
    } else if (t === PLAZA) {
      ctx.fillStyle = (x + y) % 2 ? '#b8ac97' : '#c2b6a1';
      ctx.fillRect(px, py, T, T);
      ctx.strokeStyle = '#a1957f'; ctx.lineWidth = 1;
      ctx.strokeRect(px + 0.5, py + 0.5, T - 1, T - 1);
    } else if (t === SAND) {
      ctx.fillStyle = '#e0cb96'; ctx.fillRect(px, py, T, T);
      if (h % 4 === 0) { ctx.fillStyle = '#cbb47c'; ctx.fillRect(px + (h % 12), py + (h % 10), 2, 1); }
    } else if (t === WATER || t === DOCK) {
      ctx.fillStyle = '#4d7fa8'; ctx.fillRect(px, py, T, T);
      const w = (x + Math.floor(time * 1.6) + y * 3) % 7;
      if (w === 0) { ctx.fillStyle = '#6f9fc4'; ctx.fillRect(px + 2, py + (h % 10) + 2, 10, 2); }
      if (t === DOCK) {
        ctx.fillStyle = '#9c743f'; ctx.fillRect(px, py + 2, T, T - 4);
        ctx.fillStyle = '#7c5a2e'; ctx.fillRect(px, py + 7, T, 1); ctx.fillRect(px + 7 + (x % 2), py + 2, 1, T - 4);
      }
    }
  }
}

function drawFlower(f) {
  const sway = Math.sin(time * 1.6 + f.ph) * 0.8;
  ctx.fillStyle = '#5d8440'; ctx.fillRect(f.x, f.y, 1, 4);
  ctx.fillStyle = f.c;
  ctx.fillRect(f.x - 1 + sway, f.y - 3, 3, 3);
  ctx.fillStyle = '#fff7dd'; ctx.fillRect(f.x + sway, f.y - 2, 1, 1);
}

function drawPlates() {
  for (const pl of plates) {
    const active = flags.questGiven && !flags.gateOpen;
    const lit = flags.gateOpen || pl.hold > 0;
    ctx.save();
    ctx.translate(pl.x, pl.y);
    ctx.fillStyle = '#a89c85';
    ctx.beginPath(); ctx.arc(0, 0, 9, 0, 7); ctx.fill();
    ctx.fillStyle = '#8f836c';
    ctx.beginPath(); ctx.arc(0, 0, 7, 0, 7); ctx.fill();
    const glow = flags.gateOpen ? 1 : pl.hold;
    ctx.strokeStyle = active || lit ? `rgba(232,134,58,${0.35 + 0.65 * glow})` : '#7a6f5a';
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.arc(0, 0, 4.6, 0, 7); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-3, 2); ctx.quadraticCurveTo(0, -4, 3, 2); ctx.stroke();
    if (active && pl.hold > 0 && pl.hold < 1) {
      ctx.strokeStyle = '#f2d16b'; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.arc(0, 0, 11, -Math.PI / 2, -Math.PI / 2 + pl.hold * Math.PI * 2); ctx.stroke();
    }
    if (active && pl.hold === 0) {
      const p2 = 0.5 + 0.5 * Math.sin(time * 3);
      ctx.strokeStyle = `rgba(232,134,58,${0.25 + 0.3 * p2})`;
      ctx.beginPath(); ctx.arc(0, 0, 11 + p2 * 2, 0, 7); ctx.stroke();
    }
    ctx.restore();
  }
}

// ---------- structures ----------
function drawHouse(h) {
  const x = h.tx * T, y = h.ty * T, w = h.tw * T, hh = h.th * T;
  const wallTop = y + hh * 0.42;
  const st = h.style;
  const wall = st === 'elder' ? '#c9bfa8' : '#ead6ae';
  const roofA = st === 'bakery' ? '#a5563b' : st === 'elder' ? '#6d7b8a' : '#c29a52';
  const roofB = st === 'bakery' ? '#8d4630' : st === 'elder' ? '#5c6977' : '#a87f3e';

  // walls
  ctx.fillStyle = wall; ctx.fillRect(x, wallTop, w, y + hh - wallTop);
  ctx.fillStyle = 'rgba(0,0,0,.08)'; ctx.fillRect(x, y + hh - 3, w, 3);
  if (st !== 'elder') {
    ctx.fillStyle = '#8a6a45';
    ctx.fillRect(x, wallTop, 2, y + hh - wallTop); ctx.fillRect(x + w - 2, wallTop, 2, y + hh - wallTop);
    ctx.fillRect(x, wallTop, w, 2);
    ctx.fillRect(x + Math.floor(w / 2) - 1, wallTop, 2, y + hh - wallTop);
  } else {
    ctx.strokeStyle = 'rgba(90,80,60,.25)'; ctx.lineWidth = 1;
    for (let i = 1; i < 3; i++) { ctx.beginPath(); ctx.moveTo(x, wallTop + i * 9); ctx.lineTo(x + w, wallTop + i * 9); ctx.stroke(); }
  }
  // roof
  ctx.fillStyle = roofB;
  ctx.beginPath();
  ctx.moveTo(x - 5, wallTop); ctx.lineTo(x + w + 5, wallTop);
  ctx.lineTo(x + w - 8, y - 8); ctx.lineTo(x + 8, y - 8);
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = roofA;
  ctx.beginPath();
  ctx.moveTo(x - 5, wallTop); ctx.lineTo(x + w * 0.5, wallTop);
  ctx.lineTo(x + w * 0.5 - 3, y - 8); ctx.lineTo(x + 8, y - 8);
  ctx.closePath(); ctx.fill();
  // chimney
  ctx.fillStyle = '#8f836c'; ctx.fillRect(x + w - T * 1.4, y - 14, 7, 12);
  ctx.fillStyle = '#6f6552'; ctx.fillRect(x + w - T * 1.4 - 1, y - 15, 9, 3);
  // door
  const dx = x + w / 2 - 6, dy = y + hh - 15;
  ctx.fillStyle = '#5b3a24';
  ctx.fillRect(dx, dy + 4, 12, 11);
  ctx.beginPath(); ctx.arc(dx + 6, dy + 4, 6, Math.PI, 0); ctx.fill();
  ctx.fillStyle = '#e8a04c'; ctx.fillRect(dx + 9, dy + 8, 1.6, 1.6);
  // windows
  const wy = wallTop + 7;
  for (const wx of [x + 7, x + w - 17]) {
    ctx.fillStyle = st === 'elder' ? '#f2c56d' : '#bcd6e2';
    ctx.fillRect(wx, wy, 10, 8);
    ctx.strokeStyle = '#6b5335'; ctx.lineWidth = 1.4; ctx.strokeRect(wx, wy, 10, 8);
    ctx.beginPath(); ctx.moveTo(wx + 5, wy); ctx.lineTo(wx + 5, wy + 8); ctx.stroke();
  }
  // bakery sign
  if (st === 'bakery') {
    ctx.fillStyle = '#8a6a45'; ctx.fillRect(x + w - 8, wallTop + 2, 1.6, 8);
    ctx.fillStyle = '#e8d1a0'; ctx.fillRect(x + w - 13, wallTop + 9, 12, 8);
    ctx.strokeStyle = '#8a6a45'; ctx.lineWidth = 1; ctx.strokeRect(x + w - 13, wallTop + 9, 12, 8);
    ctx.fillStyle = '#b3792f';
    ctx.beginPath(); ctx.ellipse(x + w - 7, wallTop + 13, 4, 2.4, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#e8d1a0'; ctx.fillRect(x + w - 9.5, wallTop + 12.4, 5, 0.8);
  }
}

function drawTree(t) {
  const sway = Math.sin(time * 0.9 + t.x * 0.05) * 0.8;
  const s = t.big ? 1.25 : 1;
  ctx.fillStyle = 'rgba(0,0,0,.18)';
  ctx.beginPath(); ctx.ellipse(t.x, t.y + 1, 8 * s, 3, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#7c5432'; ctx.fillRect(t.x - 2, t.y - 10 * s, 4, 11 * s);
  const cy = t.y - 14 * s;
  ctx.fillStyle = '#41682f';
  ctx.beginPath(); ctx.arc(t.x + sway, cy + 3, 9.5 * s, 0, 7); ctx.fill();
  ctx.fillStyle = '#4f7a3a';
  ctx.beginPath(); ctx.arc(t.x + sway - 3, cy - 1, 7.5 * s, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.arc(t.x + sway + 4, cy, 7 * s, 0, 7); ctx.fill();
  ctx.fillStyle = '#639347';
  ctx.beginPath(); ctx.arc(t.x + sway - 2, cy - 4, 4.5 * s, 0, 7); ctx.fill();
}

function drawHeartlight() {
  const x = heartlight.x, y = heartlight.y;
  const pulse = 0.10 + 0.05 * Math.sin(time * 1.4);
  // glow
  const g = ctx.createRadialGradient(x, y - 14, 2, x, y - 14, 34);
  g.addColorStop(0, `rgba(240,170,80,${pulse * 2.2})`);
  g.addColorStop(1, 'rgba(240,170,80,0)');
  ctx.fillStyle = g; ctx.fillRect(x - 34, y - 48, 68, 68);
  // pedestal
  ctx.fillStyle = '#a89c85'; ctx.fillRect(x - 11, y - 6, 22, 7);
  ctx.fillStyle = '#8f836c'; ctx.fillRect(x - 9, y - 10, 18, 5);
  ctx.fillStyle = '#7a6f5a'; ctx.fillRect(x - 11, y, 22, 2);
  // crystal
  ctx.save();
  ctx.translate(x, y - 10);
  ctx.fillStyle = '#f2cf95';
  ctx.beginPath(); ctx.moveTo(0, -22); ctx.lineTo(7, -9); ctx.lineTo(0, 0); ctx.lineTo(-7, -9); ctx.closePath(); ctx.fill();
  ctx.fillStyle = `rgba(224,138,60,${0.35 + pulse})`;
  ctx.beginPath(); ctx.moveTo(0, -18); ctx.lineTo(4, -9); ctx.lineTo(0, -2); ctx.lineTo(-4, -9); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,250,230,.8)'; ctx.fillRect(-1.6, -17, 1.6, 5);
  ctx.restore();
}

function drawGate() {
  const x0 = gate.x0 * T, y0 = gate.y0 * T, x1 = (gate.x1 + 1) * T, y1 = (gate.y1 + 1) * T;
  const openW = flags.gateOpen ? 1 : flags.gateOpening;
  // pillars
  for (const px of [x0, x1 - 2 * T]) {
    ctx.fillStyle = '#a89c85'; ctx.fillRect(px, y0 - 14, 2 * T, y1 - y0 + 14);
    ctx.fillStyle = '#8f836c';
    for (let i = 0; i < 4; i++) ctx.fillRect(px + (i % 2 ? 2 : 6), y0 - 8 + i * 12, 2 * T - 10, 1.6);
    ctx.fillStyle = '#bdb29b'; ctx.fillRect(px - 2, y0 - 18, 2 * T + 4, 6);
  }
  // doors (slide into the pillars)
  const doorW = (3 * T / 2) * (1 - openW);
  ctx.fillStyle = '#4d3520';
  if (doorW > 0.5) {
    ctx.fillRect(x0 + 2 * T, y0 - 4, doorW, y1 - y0 + 4);
    ctx.fillRect(x1 - 2 * T - doorW, y0 - 4, doorW, y1 - y0 + 4);
    ctx.fillStyle = '#5f4128';
    for (let i = 1; i < 4; i++) {
      ctx.fillRect(x0 + 2 * T + (doorW * i / 4), y0 - 4, 1.4, y1 - y0 + 4);
      ctx.fillRect(x1 - 2 * T - (doorW * i / 4), y0 - 4, 1.4, y1 - y0 + 4);
    }
  } else {
    // path glimpsed beyond
    ctx.fillStyle = '#1d2818'; ctx.fillRect(x0 + 2 * T, y0 - 4, 3 * T, 6);
  }
  // arch
  ctx.fillStyle = '#bdb29b'; ctx.fillRect(x0, y0 - 26, x1 - x0, 10);
  ctx.fillStyle = '#a89c85'; ctx.fillRect(x0 + 4, y0 - 24, x1 - x0 - 8, 6);
  // twin-sigil emblem on the arch
  const lit = flags.questGiven;
  ctx.strokeStyle = lit ? `rgba(232,134,58,${0.6 + 0.4 * Math.sin(time * 2.5)})` : '#7a6f5a';
  ctx.lineWidth = 1.5;
  const cx = (x0 + x1) / 2;
  ctx.beginPath(); ctx.arc(cx - 4, y0 - 21, 3.4, 0, 7); ctx.stroke();
  ctx.beginPath(); ctx.arc(cx + 4, y0 - 21, 3.4, 0, 7); ctx.stroke();
}

// ---------- characters ----------
function drawChar(x, y, dir, animT, moving, kind, pal, connected = true) {
  const f = moving ? Math.floor(animT * 8) % 4 : 0;
  const bob = (f === 1 || f === 3) ? -1 : 0;
  const legL = f === 1 ? -2 : 0, legR = f === 3 ? -2 : 0;
  ctx.save();
  ctx.translate(Math.round(x), Math.round(y));
  if (!connected) ctx.globalAlpha = 0.45;

  ctx.fillStyle = 'rgba(0,0,0,.18)';
  ctx.beginPath(); ctx.ellipse(0, 0, 6, 2.4, 0, 0, 7); ctx.fill();

  const isElder = kind === 'elder', isBaker = kind === 'baker', isFinn = kind === 'finn';
  const tunic = pal ? pal.tunic : isElder ? '#7a6d8f' : isBaker ? '#c9584a' : '#5b7a8f';
  const hair = pal ? pal.hair : isElder ? '#cfc8bd' : isBaker ? '#a34d2c' : '#4a3826';

  if (isElder) {
    ctx.fillStyle = tunic; ctx.fillRect(-5, -14 + bob, 10, 14);
    ctx.fillStyle = 'rgba(0,0,0,.15)'; ctx.fillRect(-5, -3 + bob, 10, 3);
    // staff
    ctx.fillStyle = '#8a6a45'; ctx.fillRect(7, -18, 1.6, 18);
    ctx.fillStyle = '#e8a04c'; ctx.beginPath(); ctx.arc(7.8, -19, 2, 0, 7); ctx.fill();
  } else {
    ctx.fillStyle = '#3f3428';
    ctx.fillRect(-4, -4 + legL, 3, 4 - Math.min(0, legL));
    ctx.fillRect(1, -4 + legR, 3, 4 - Math.min(0, legR));
    ctx.fillStyle = tunic; ctx.fillRect(-5, -12 + bob, 10, 8);
    ctx.fillStyle = 'rgba(0,0,0,.2)'; ctx.fillRect(-5, -6 + bob, 10, 1.4);
    // arms
    ctx.fillStyle = tunic;
    ctx.fillRect(-7, -11 + bob + (f === 1 ? 1 : 0), 2, 5);
    ctx.fillRect(5, -11 + bob + (f === 3 ? 1 : 0), 2, 5);
    if (isBaker) { ctx.fillStyle = '#f2e8d0'; ctx.fillRect(-3, -11 + bob, 6, 7); }
  }
  // head
  const hy = (isElder ? -22 : -20) + bob;
  ctx.fillStyle = SKIN; ctx.fillRect(-5, hy, 10, 8);
  ctx.fillStyle = hair;
  ctx.fillRect(-5, hy - 2, 10, 4);
  if (dir === 'up') ctx.fillRect(-5, hy, 10, 7);
  if (dir === 'left') ctx.fillRect(-5, hy, 2.4, 7);
  if (dir === 'right') ctx.fillRect(2.6, hy, 2.4, 7);
  if (isElder) { ctx.fillStyle = '#cfc8bd'; ctx.fillRect(-3, hy + 6, 6, 4); } // beard
  if (isBaker) { ctx.fillStyle = '#f2e8d0'; ctx.fillRect(-5.5, hy - 4, 11, 3.4); } // puff hat
  if (isFinn) { ctx.fillStyle = '#6d5a3a'; ctx.fillRect(-6.5, hy - 2.4, 13, 3); ctx.fillRect(-4.5, hy - 4.4, 9, 2.4); } // bucket hat
  // eyes
  ctx.fillStyle = '#241708';
  if (dir === 'down') { ctx.fillRect(-2.6, hy + 3, 1.4, 2); ctx.fillRect(1.2, hy + 3, 1.4, 2); }
  if (dir === 'left') ctx.fillRect(-3.4, hy + 3, 1.4, 2);
  if (dir === 'right') ctx.fillRect(2, hy + 3, 1.4, 2);
  ctx.restore();
}

function drawCat(n) {
  const wig = Math.sin(time * 3 + 1) * 2;
  const flip = n.dir === 'left' ? -1 : 1;
  ctx.save();
  ctx.translate(Math.round(n.x), Math.round(n.y));
  ctx.scale(flip, 1);
  ctx.fillStyle = 'rgba(0,0,0,.15)';
  ctx.beginPath(); ctx.ellipse(0, 0, 5, 1.8, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#d9a441';
  ctx.fillRect(-5, -5, 8, 5);           // body
  ctx.fillRect(1, -8, 5, 5);            // head
  ctx.fillStyle = '#b3792f';
  ctx.fillRect(-4, -5, 1.4, 5); ctx.fillRect(-1, -5, 1.4, 5);   // stripes
  ctx.beginPath();                       // tail
  ctx.moveTo(-5, -4); ctx.quadraticCurveTo(-8, -6 + wig, -7, -9 + wig);
  ctx.strokeStyle = '#d9a441'; ctx.lineWidth = 1.6; ctx.stroke();
  ctx.fillStyle = '#d9a441';             // ears
  ctx.beginPath(); ctx.moveTo(1.4, -8); ctx.lineTo(2.4, -10.4); ctx.lineTo(3.4, -8); ctx.fill();
  ctx.beginPath(); ctx.moveTo(3.8, -8); ctx.lineTo(4.8, -10.4); ctx.lineTo(5.8, -8); ctx.fill();
  ctx.fillStyle = '#241708'; ctx.fillRect(4.4, -6.4, 1, 1.2);   // eye
  ctx.restore();
}

function drawParticles() {
  for (const pt of particles) {
    const a = Math.max(0, Math.min(1, pt.life));
    if (pt.kind === 'smoke') {
      ctx.fillStyle = `rgba(230,225,215,${0.25 * a})`;
      ctx.beginPath(); ctx.arc(pt.x, pt.y, pt.r + (3 - pt.life), 0, 7); ctx.fill();
    } else if (pt.kind === 'petal') {
      ctx.fillStyle = pt.c;
      ctx.globalAlpha = Math.min(1, pt.life / 2) * 0.8;
      ctx.fillRect(pt.x, pt.y, 2, 2);
      ctx.globalAlpha = 1;
    } else if (pt.kind === 'heart') {
      ctx.fillStyle = `rgba(232,110,110,${a})`;
      ctx.font = '6px serif';
      ctx.fillText('♥', pt.x, pt.y);
    } else if (pt.kind === 'mote') {
      ctx.fillStyle = `rgba(240,190,110,${0.5 * a})`;
      ctx.fillRect(pt.x, pt.y, 1.6, 1.6);
    }
  }
}

// ---------- screen-space UI ----------
function worldToScreen(wx, wy) {
  return [(wx - cam.x) * cam.zoom + cw / 2, (wy - cam.y) * cam.zoom + ch / 2];
}
const SERIF = '"Iowan Old Style", Palatino, Georgia, serif';

function drawScreenUI() {
  // name tags
  for (const p of players) {
    if (!p) continue;
    const [sx, sy] = worldToScreen(p.x, p.y - 26);
    ctx.font = `600 13px ${SERIF}`;
    ctx.textAlign = 'center';
    const label = p.connected ? p.name : p.name + ' …';
    ctx.fillStyle = 'rgba(20,12,4,.55)';
    const w = ctx.measureText(label).width;
    roundRect(sx - w / 2 - 7, sy - 12, w + 14, 17, 8); ctx.fill();
    ctx.fillStyle = p.pal.tunic;
    ctx.beginPath(); ctx.arc(sx - w / 2 - 0.5, sy - 3.5, 3, 0, 7); ctx.fill();
    ctx.fillStyle = '#f6ead0';
    ctx.fillText(label, sx + 3, sy + 1);
  }

  // "!" bubble over whichever interactable someone is near
  if (!dlg && !flags.ended) {
    const shown = new Set();
    for (const p of players) {
      if (!p) continue;
      const near = nearestInteractable(p);
      if (near && !shown.has(near)) {
        shown.add(near);
        const bounce = Math.sin(time * 4) * 3;
        const [sx, sy] = worldToScreen(near.x, near.y - (near.kind === 'cat' ? 16 : near.kind === 'heartlight' ? 40 : 32));
        ctx.fillStyle = '#f6ead0';
        roundRect(sx - 8, sy - 20 + bounce, 16, 16, 5); ctx.fill();
        ctx.strokeStyle = '#9c7a4c'; ctx.lineWidth = 1.5; roundRect(sx - 8, sy - 20 + bounce, 16, 16, 5); ctx.stroke();
        ctx.fillStyle = '#c9584a'; ctx.font = `700 12px ${SERIF}`;
        ctx.fillText('!', sx, sy - 8 + bounce);
      }
    }
  }

  // quest-giver marker over the elder before the quest
  if (!flags.questGiven && !dlg && players.some(Boolean)) {
    const elder = npcs[0];
    const [sx, sy] = worldToScreen(elder.x, elder.y - 34);
    const bounce = Math.sin(time * 3) * 3;
    ctx.font = `700 20px ${SERIF}`;
    ctx.textAlign = 'center';
    ctx.fillStyle = '#f2d16b';
    ctx.strokeStyle = 'rgba(20,12,4,.6)'; ctx.lineWidth = 3;
    ctx.strokeText('✦', sx, sy + bounce);
    ctx.fillText('✦', sx, sy + bounce);
  }

  // objective chip
  const obj = objectiveText();
  if (obj && !flags.ended) {
    ctx.font = `italic 15px ${SERIF}`;
    ctx.textAlign = 'left';
    const w = ctx.measureText(obj).width;
    ctx.fillStyle = 'rgba(24,16,8,.68)';
    roundRect(16, 16, w + 44, 32, 9); ctx.fill();
    ctx.strokeStyle = 'rgba(201,151,63,.5)'; ctx.lineWidth = 1.5;
    roundRect(16, 16, w + 44, 32, 9); ctx.stroke();
    ctx.fillStyle = '#e8a04c'; ctx.fillText('✦', 30, 37);
    ctx.fillStyle = '#f6ead0'; ctx.fillText(obj, 48, 37);
  }

  if (banner) drawBanner();
  if (dlg) drawDialog();
  if (flags.ended) drawEnd();

  // vignette
  const vg = ctx.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * 0.42, cw / 2, ch / 2, Math.max(cw, ch) * 0.72);
  vg.addColorStop(0, 'rgba(20,12,4,0)');
  vg.addColorStop(1, 'rgba(20,12,4,.4)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, cw, ch);
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function drawBanner() {
  const fadeIn = Math.min(1, banner.t / 0.6);
  const fadeOut = Math.min(1, (banner.dur - banner.t) / 0.8);
  const a = Math.min(fadeIn, fadeOut);
  const y = ch * 0.2 - (1 - fadeIn) * 18;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.textAlign = 'center';
  ctx.font = `600 46px ${SERIF}`;
  const w = Math.max(ctx.measureText(banner.title).width, 300) + 90;
  ctx.fillStyle = 'rgba(24,16,8,.72)';
  roundRect(cw / 2 - w / 2, y - 44, w, banner.sub ? 96 : 64, 12); ctx.fill();
  ctx.strokeStyle = 'rgba(201,151,63,.65)'; ctx.lineWidth = 2;
  roundRect(cw / 2 - w / 2, y - 44, w, banner.sub ? 96 : 64, 12); ctx.stroke();
  ctx.fillStyle = '#f2d16b';
  ctx.fillText(banner.title, cw / 2, y);
  if (banner.sub) {
    ctx.font = `italic 19px ${SERIF}`;
    ctx.fillStyle = '#e8d5b0';
    ctx.fillText(banner.sub, cw / 2, y + 32);
  }
  ctx.restore();
}

function drawDialog() {
  const line = dlg.lines[dlg.i];
  dlg.chars = Math.min(line.text.length, dlg.chars + 0.9);  // ~55 chars/s at 60fps
  const shown = line.text.slice(0, Math.floor(dlg.chars));

  const bw = Math.min(760, cw - 80), bh = 118;
  const bx = cw / 2 - bw / 2, by = ch - bh - 34;
  ctx.fillStyle = '#f6ead0';
  roundRect(bx, by, bw, bh, 12); ctx.fill();
  ctx.strokeStyle = '#9c7a4c'; ctx.lineWidth = 3;
  roundRect(bx, by, bw, bh, 12); ctx.stroke();
  ctx.strokeStyle = 'rgba(156,122,76,.4)'; ctx.lineWidth = 1;
  roundRect(bx + 5, by + 5, bw - 10, bh - 10, 8); ctx.stroke();

  // name chip
  ctx.font = `700 16px ${SERIF}`;
  ctx.textAlign = 'left';
  const nw = ctx.measureText(line.who).width;
  ctx.fillStyle = '#241708';
  roundRect(bx + 20, by - 14, nw + 30, 28, 9); ctx.fill();
  ctx.fillStyle = line.color;
  ctx.beginPath(); ctx.arc(bx + 34, by, 4.5, 0, 7); ctx.fill();
  ctx.fillStyle = '#f6ead0';
  ctx.fillText(line.who, bx + 44, by + 5.5);

  // text with wrapping
  ctx.font = `17px ${SERIF}`;
  ctx.fillStyle = '#4a3826';
  const words = shown.split(' ');
  let lineStr = '', ly = by + 40;
  for (const wd of words) {
    const test = lineStr ? lineStr + ' ' + wd : wd;
    if (ctx.measureText(test).width > bw - 60) { ctx.fillText(lineStr, bx + 28, ly); lineStr = wd; ly += 24; }
    else lineStr = test;
  }
  ctx.fillText(lineStr, bx + 28, ly);

  if (Math.floor(dlg.chars) >= line.text.length && Math.sin(time * 5) > 0) {
    ctx.fillStyle = '#9c7a4c';
    ctx.font = `16px ${SERIF}`;
    ctx.textAlign = 'right';
    ctx.fillText('▾  A', bx + bw - 20, by + bh - 14);
  }
}

function drawEnd() {
  const a = Math.min(1, flags.endT / 2.5);
  ctx.fillStyle = `rgba(18,10,4,${a * 0.82})`;
  ctx.fillRect(0, 0, cw, ch);
  if (a < 0.3) return;
  const ta = Math.min(1, (flags.endT - 0.8) / 1.5);
  if (ta <= 0) return;
  ctx.save();
  ctx.globalAlpha = ta;
  ctx.textAlign = 'center';
  ctx.fillStyle = '#e8b25c';
  ctx.font = `600 54px ${SERIF}`;
  ctx.fillText('End of Chapter One', cw / 2, ch * 0.38);
  ctx.font = `italic 21px ${SERIF}`;
  ctx.fillStyle = '#e8d5b0';
  ctx.fillText('Rowan’s ember glows warm between you.', cw / 2, ch * 0.38 + 52);
  ctx.fillText('Beyond the hill, the Whisperwood murmurs…', cw / 2, ch * 0.38 + 82);
  ctx.font = `17px ${SERIF}`;
  ctx.fillStyle = 'rgba(232,178,92,.75)';
  ctx.fillText('— to be continued · tell Claude what Chapter Two should hold —', cw / 2, ch * 0.38 + 140);
  const hb = 1 + Math.sin(time * 3) * 0.1;
  ctx.font = `${Math.round(34 * hb)}px serif`;
  ctx.fillStyle = '#e86e6e';
  ctx.fillText('♥', cw / 2, ch * 0.38 - 70);
  ctx.restore();
}

/* ============================================================
   MAIN LOOP
   ============================================================ */
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  update(dt);
  render();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
