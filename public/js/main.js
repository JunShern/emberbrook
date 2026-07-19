'use strict';
/* ============================================================
   MAIN — boot, players & roles, loop, render (scene edition)
   ============================================================ */

window.players = [null, null];
const ROLE_INFO = {
  vesper: { charName: 'Vesper', color: '#4f9f92' },
  lake: { charName: 'Lake', color: '#e0a94e' },
};

/* ---------- chapter routing ----------
   All story hooks (update/objective/interact/promptFor/nearestThing/markers)
   go through CurrentChapter; chapters share one vocabulary. */
window.CurrentChapter = Chapter1;
function setChapter(ch) {
  if (window.CurrentChapter === ch) return;
  if (ch.build && !ch.built) ch.build();
  window.CurrentChapter = ch;
}
// Chapter One's end card hands off to Chapter Two (keypress, or on its own)
function startChapter2() {
  if (window.__ch2Handoff || window.CurrentChapter !== Chapter1) return;
  window.__ch2Handoff = true;
  FX.fadeTarget = 1;
  setTimeout(() => {
    setChapter(Chapter2);
    Chapter2.begin(window.players);
    FX.fadeTarget = 0;
  }, 1000);
}

function makePlayer(role, id, kb) {
  const sp = CurrentChapter.spawnFor(role);
  return {
    id, role, kb: !!kb,
    charName: ROLE_INFO[role].charName,
    char: role, lightCarrier: role === 'lake',
    scene: sp.scene, x: sp.x, y: sp.y, dir: sp.dir,
    moving: false, animT: 0, h: 95,
    input: { x: 0, y: 0 }, a: false, aEdge: false,
    connected: true, lastPrompt: '',
  };
}

function byRole(role) { return players.find(p => p && p.role === role); }

function assignPlayer(m) {
  if (typeof Title !== 'undefined' && Title.active) Title.dismiss();   // a phone joining wakes the game too
  const role = m.role === 'lake' ? 'lake' : 'vesper';
  const existing = byRole(role);
  if (existing && existing.connected && !existing.kb) { Net.to(m.from, { type: 'taken', role }); return; }
  let slot = existing ? players.indexOf(existing) : players.findIndex(p => p === null);
  if (slot === -1) { Net.to(m.from, { type: 'full' }); return; }
  const old = players[slot];
  players[slot] = makePlayer(role, m.from, false);
  if (old && old.role === role) {
    players[slot].scene = old.scene; players[slot].x = old.x; players[slot].y = old.y;
  }
  Net.to(m.from, { type: 'assign', role, name: ROLE_INFO[role].charName });
  Net.to(m.from, { type: 'phase', act: CurrentChapter.phase });
  AudioSys.sparkle();
  broadcastRoster();
  updatePanel();
}

function broadcastRoster() {
  Net.send({ type: 'roster', taken: players.filter(p => p && p.connected && !p.kb).map(p => p.role) });
}

Net.onMessage = (m) => {
  if (m.type === 'ready') {
    const el = document.getElementById('joinUrl');
    if (el) el.textContent = m.joinUrl;
    Net.send({ type: 'who' });
    broadcastRoster();
    Net.send({ type: 'phase', act: CurrentChapter.phase });
  }
  else if (m.type === 'join') assignPlayer(m);
  else if (m.type === 'input') {
    const p = players.find(q => q && q.id === m.from);
    if (p) { p.input.x = Math.max(-1, Math.min(1, +m.x || 0)); p.input.y = Math.max(-1, Math.min(1, +m.y || 0)); }
  }
  else if (m.type === 'btn') {
    const p = players.find(q => q && q.id === m.from);
    if (p) { if (m.down && !p.a) p.aEdge = true; p.a = !!m.down; }
  }
  else if (m.type === 'controller-left') {
    const p = players.find(q => q && q.id === m.id);
    if (p) { p.connected = false; p.input.x = 0; p.input.y = 0; p.a = false; broadcastRoster(); updatePanel(); }
  }
};

function updatePanel() {
  const panel = document.getElementById('joinPanel');
  ['vesper', 'lake'].forEach((r, i) => {
    const el = document.getElementById('slot' + i);
    const p = byRole(r);
    const nm = `<b style="color:${ROLE_INFO[r].color}">${ROLE_INFO[r].charName}</b>`;
    el.innerHTML = p
      ? (p.connected ? `♦ ${nm} — ready` : `✧ ${nm} — <i>reconnecting…</i>`)
      : `✧ ${nm} — <i>unclaimed</i>`;
  });
  const full = players[0] && players[1] && players[0].connected && players[1].connected;
  panel.classList.toggle('hidden', !!full);
}

/* ---------- title screen ---------- */
const Title = {
  active: true, t: 0, fading: -1, embers: [], img: null,
  init() {
    const im = new Image();
    im.src = 'assets/scenes/title/main.png';
    im.onerror = () => { im.src = 'assets/scenes/forest/main.png'; };
    this.img = im;
    for (let i = 0; i < 26; i++) this.embers.push(this.spawn(true));
  },
  spawn(anywhere) {
    return {
      x: Math.random(), y: anywhere ? Math.random() : 1.05,
      r: 1 + Math.random() * 2.2, v: 0.02 + Math.random() * 0.04,
      sway: Math.random() * 7, ph: Math.random() * 7, a: 0.35 + Math.random() * 0.5,
    };
  },
  dismiss() {
    if (this.fading >= 0) return;
    this.fading = 0;
    AudioSys.sparkle();
  },
  update(dt) {
    this.t += dt;
    for (const e of this.embers) {
      e.y -= e.v * dt * 2.2;
      if (e.y < -0.05) Object.assign(e, this.spawn(false));
    }
    if (this.fading >= 0) {
      this.fading += dt;
      if (this.fading > 1.1) this.active = false;
    }
  },
  draw(g) {
    const { cw, ch } = Screen;
    g.fillStyle = '#0d0906'; g.fillRect(0, 0, cw, ch);
    const im = this.img;
    if (im && im.complete && im.naturalWidth) {
      // slow cinematic drift
      const zoom = 1.07 + Math.sin(this.t * 0.045) * 0.015;
      const panX = Math.sin(this.t * 0.03) * 0.012;
      const s = Math.max(cw / im.width, ch / im.height) * zoom;
      const w = im.width * s, h = im.height * s;
      g.globalAlpha = Math.min(1, this.t / 1.6);
      g.drawImage(im, (cw - w) / 2 + panX * cw, (ch - h) / 2, w, h);
      g.globalAlpha = 1;
    }
    // depth shading
    let gr = g.createLinearGradient(0, 0, 0, ch);
    gr.addColorStop(0, 'rgba(10,6,3,.55)');
    gr.addColorStop(0.35, 'rgba(10,6,3,.08)');
    gr.addColorStop(0.8, 'rgba(10,6,3,.25)');
    gr.addColorStop(1, 'rgba(10,6,3,.7)');
    g.fillStyle = gr; g.fillRect(0, 0, cw, ch);
    // embers
    for (const e of this.embers) {
      const x = e.x * cw + Math.sin(this.t * 0.7 + e.sway) * 14;
      const y = e.y * ch;
      const tw = 0.6 + 0.4 * Math.sin(this.t * 2.4 + e.ph);
      g.fillStyle = `rgba(255,${170 + ((e.ph * 20) | 0) % 60},110,${(e.a * tw * 0.8).toFixed(2)})`;
      g.beginPath(); g.arc(x, y, e.r, 0, 7); g.fill();
    }
    // logotype
    const fade = Math.max(0, Math.min(1, (this.t - 0.9) / 1.4));
    if (fade > 0) {
      g.save();
      g.globalAlpha = fade;
      g.textAlign = 'center';
      const ty = ch * 0.30;
      g.shadowColor = 'rgba(255,170,80,.55)';
      g.shadowBlur = 34;
      let fs = Math.round(ch * 0.115);
      g.font = `600 ${fs}px ${SERIF}`;
      while (fs > 20 && g.measureText('E M B E R B R O O K').width > cw * 0.68) {
        fs -= 4; g.font = `600 ${fs}px ${SERIF}`;
      }
      const grad = g.createLinearGradient(0, ty - ch * 0.1, 0, ty + ch * 0.02);
      grad.addColorStop(0, '#ffe9bd');
      grad.addColorStop(0.55, '#e8b566');
      grad.addColorStop(1, '#b4763a');
      g.fillStyle = grad;
      g.fillText('E M B E R B R O O K', cw / 2, ty);
      g.shadowBlur = 0;
      g.font = `italic 500 ${Math.round(ch * 0.026)}px ${SERIF}`;
      g.fillStyle = 'rgba(242,228,196,.85)';
      g.fillText('a tale for two keepers', cw / 2, ty + ch * 0.052);
      // prompt
      const pulse = 0.55 + 0.35 * Math.sin(this.t * 2.2);
      g.font = `500 ${Math.round(ch * 0.024)}px ${SERIF}`;
      g.fillStyle = `rgba(242,228,196,${(0.55 + 0.35 * pulse).toFixed(2)})`;
      g.fillText('press any key to begin  ·  phones can scan in anytime', cw / 2, ch * 0.88);
      g.restore();
    }
    // dismiss fade
    if (this.fading >= 0) {
      g.fillStyle = `rgba(8,5,3,${Math.min(1, this.fading / 0.9).toFixed(2)})`;
      g.fillRect(0, 0, cw, ch);
    }
  },
};
Title.init();

/* ---------- dev tools: walkability overlay (G) + help menu (H) ---------- */
const Dev = {
  mask: false, help: false, zoom: 1,
  _cache: {}, // sceneKey|state -> canvas
  maskCanvas() {
    const key = Field.currentKey + '|' + (Field.scene() ? Field.scene().state : '');
    if (this._cache[key]) return this._cache[key];
    const GS = 8, GW = 168, GH = 96;
    const c = makeCanvas(GW, GH), g = c.getContext('2d');
    const img = g.createImageData(GW, GH);
    for (let gy = 0; gy < GH; gy++) for (let gx = 0; gx < GW; gx++) {
      const ok = fieldWalkable(Field.currentKey, gx * GS + 4, gy * GS + 4);
      const i = (gy * GW + gx) * 4;
      img.data[i] = ok ? 60 : 235;
      img.data[i + 1] = ok ? 220 : 60;
      img.data[i + 2] = ok ? 90 : 60;
      img.data[i + 3] = ok ? 95 : 70;
    }
    g.putImageData(img, 0, 0);
    this._cache[key] = c;
    return c;
  },
  drawMask(g) {
    if (!this.mask || !Field.currentKey) return;
    const [x0, y0] = Field.worldToScreen(0, 0);
    const [x1] = Field.worldToScreen(1344, 0);
    const [, y2] = Field.worldToScreen(0, 768);
    g.save();
    g.imageSmoothingEnabled = false;
    g.drawImage(this.maskCanvas(), x0, y0, x1 - x0, y2 - y0);
    g.restore();
  },
  KEYS: [
    ['W A S D + E', 'Vesper — move + interact (keyboard)'],
    ['arrows + Enter', 'Lake — move + interact (keyboard)'],
    ['K', 'keyboard override (play without phones)'],
    ['M', 'music on / off'],
    ['N', 'audition music variants (town/forest)'],
    ['1 – 7', 'Chapter One checkpoints (1 = restart)'],
    ['8 9 0', 'Chapter Two checkpoints (road · swarm · morning)'],
    ['G', 'walkability overlay (green = walkable)'],
    ['- / =', 'zoom out / in (camera test)'],
    ['H', 'this help'],
  ],
  drawHelp(g) {
    if (!this.help) return;
    const { cw, ch } = Screen;
    const w = 560, lh = 34, h = 96 + this.KEYS.length * lh;
    const x = cw / 2 - w / 2, y = ch / 2 - h / 2;
    g.save();
    g.fillStyle = 'rgba(12,8,5,.88)';
    roundRectPath(g, x, y, w, h, 14); g.fill();
    g.strokeStyle = '#9c7a4c'; g.lineWidth = 2;
    roundRectPath(g, x, y, w, h, 14); g.stroke();
    g.textAlign = 'left';
    g.font = `600 22px ${SERIF}`;
    g.fillStyle = '#e0a94e';
    g.fillText('Developer keys', x + 28, y + 44);
    g.font = `500 16px ${SERIF}`;
    this.KEYS.forEach(([k, desc], i) => {
      const ly = y + 84 + i * lh;
      g.fillStyle = '#f2d16b';
      g.fillText(k, x + 28, ly);
      g.fillStyle = '#f2e4c4';
      g.fillText(desc, x + 190, ly);
    });
    g.restore();
  },
};

window.Dev = Dev;   // field.js reads the zoom multiplier via window

/* ---------- keyboard control ----------
   WASD + E → Vesper · arrows + Enter → Lake · K = override phones */
const keys = {};
let kbOverride = false;
const kbDrives = (p) => p && (p.kb || kbOverride);

window.addEventListener('keydown', (e) => {
  keys[e.code] = true;
  AudioSys.init();
  if (Title.active) { Title.dismiss(); return; }   // first press wakes the game
  if (e.code === 'KeyM') AudioSys.toggleMusic();
  // N — audition the composed candidates for the current mood (town/forest)
  if (e.code === 'KeyN') {
    const VARIANTS = {
      festivalA: ['festivalB', 'town — candidate B (market bustle)'],
      festivalB: ['festivalA', 'town — candidate A (village waltz)'],
      forestA: ['forestB', 'forest — candidate B (old roots)'],
      forestB: ['forestA', 'forest — candidate A (the deep wood)'],
    };
    const v = VARIANTS[AudioSys.ALIAS[AudioSys.mood] || AudioSys.mood];
    if (v) { AudioSys.setMood(v[0]); Toasts.add('♪ ' + v[1], '#8fb0c9'); }
    else Toasts.add('♪ no variants for this mood', '#8fb0c9');
  }
  if (e.code === 'KeyG') { Dev.mask = !Dev.mask; Dev._cache = {}; Toasts.add('⚙ walkability overlay ' + (Dev.mask ? 'ON' : 'off'), '#8fb0c9'); }
  if (e.code === 'KeyH') Dev.help = !Dev.help;
  if (e.code === 'Minus' || e.code === 'Equal') {
    Dev.zoom = Math.round(Math.max(0.6, Math.min(2.2, Dev.zoom + (e.code === 'Minus' ? 0.1 : -0.1))) * 10) / 10;
    Toasts.add('⚙ zoom ×' + (1 / Dev.zoom).toFixed(2) + (Dev.zoom === 1 ? ' (default)' : ''), '#8fb0c9');
  }
  if (e.code === 'KeyK') {
    kbOverride = !kbOverride;
    Toasts.add(kbOverride ? '⌨ keyboard override ON — WASD/E Vesper · arrows/Enter Lake' : '⌨ keyboard override off', '#8fb0c9');
  }
  // dev checkpoints: 1–7 Chapter One, 8/9/0 Chapter Two
  if (/^Digit[1-7]$/.test(e.code)) {
    window.__ch2Handoff = false;
    setChapter(Chapter1);
    Chapter1.applyCheckpoint(+e.code.slice(5));
  }
  if (/^Digit[890]$/.test(e.code)) {
    window.__ch2Handoff = false;
    setChapter(Chapter2);
    Chapter2.applyCheckpoint(e.code === 'Digit8' ? 1 : e.code === 'Digit9' ? 2 : 3);
  }
  // the Chapter One end card advances into Chapter Two on a keypress
  if (CurrentChapter === Chapter1 && Chapter1.flags.ended && Chapter1.flags.endT > 2.5)
    startChapter2();
  const P1K = ['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyE'], P2K = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter'];
  if (P1K.includes(e.code) && !byRole('vesper')) {
    const slot = players.findIndex(p => p === null);
    if (slot !== -1) { players[slot] = makePlayer('vesper', 'kb1', true); updatePanel(); }
  }
  if (P2K.includes(e.code) && !byRole('lake')) {
    const slot = players.findIndex(p => p === null);
    if (slot !== -1) { players[slot] = makePlayer('lake', 'kb2', true); updatePanel(); }
  }
  const j = byRole('vesper'), c = byRole('lake');
  if (e.code === 'KeyE' && kbDrives(j)) { if (!j.a) j.aEdge = true; j.a = true; }
  if (e.code === 'Enter' && kbDrives(c)) { if (!c.a) c.aEdge = true; c.a = true; }
});
window.addEventListener('keyup', (e) => {
  keys[e.code] = false;
  const j = byRole('vesper'), c = byRole('lake');
  if (e.code === 'KeyE' && kbDrives(j)) j.a = false;
  if (e.code === 'Enter' && kbDrives(c)) c.a = false;
});
window.addEventListener('pointerdown', () => AudioSys.init());

const kbWasMoving = { vesper: false, lake: false };
function keyboardInput() {
  const j = byRole('vesper'), c = byRole('lake');
  if (kbDrives(j)) {
    const x = (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0);
    const y = (keys.KeyS ? 1 : 0) - (keys.KeyW ? 1 : 0);
    if (x || y || j.kb || kbWasMoving.vesper) { j.input.x = x; j.input.y = y; }
    kbWasMoving.vesper = !!(x || y);
  }
  if (kbDrives(c)) {
    const x = (keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0);
    const y = (keys.ArrowDown ? 1 : 0) - (keys.ArrowUp ? 1 : 0);
    if (x || y || c.kb || kbWasMoving.lake) { c.input.x = x; c.input.y = y; }
    kbWasMoving.lake = !!(x || y);
  }
}

/* ---------- update ---------- */
function activePlayers() {
  const roles = CurrentChapter.activeRoles();
  return players.filter(p => p && roles.includes(p.role) && !p.hidden && !p.parked);
}

function update(dt) {
  time += dt;
  if (Title.active) { Title.update(dt); return; }
  keyboardInput();
  FX.update(dt);
  Dialog.update(dt);
  Banner.update(dt);
  Objective.update(dt);
  Toasts.update(dt);
  Cutscene.tick(dt, players);
  Particles.update(dt);

  const frozen = Dialog.active() || Cutscene.active || CurrentChapter.flags.ended || Field.transitioning;
  const act = activePlayers();

  // keep the visible scene glued to the active player(s)
  if (!Field.transitioning && act.length && Field.currentKey !== act[0].scene)
    Field.enter(act[0].scene, null, null), Field.cam.x = act[0].x, Field.cam.y = act[0].y;

  for (const p of players) {
    if (!p) continue;
    const active = act.includes(p);
    if (!active) { p.moving = false; p.aEdge = false; continue; }
    const s = Field.scenes[p.scene];
    let vx = p.input.x, vy = p.input.y;
    const len = Math.hypot(vx, vy);
    if (len > 1) { vx /= len; vy /= len; }
    p.moving = !frozen && len > 0.12;
    p.h = s.charH * (p.role === 'lake' ? 1.04 : 1);   // Lake reads slightly taller
    if (p.moving) {
      const spd = s.speed;
      const nx = p.x + vx * spd * dt;
      const ny = p.y + vy * spd * dt;
      // if somehow outside walkable space, never lock movement — let them wiggle back in
      const curOk = fieldWalkable(p.scene, p.x, p.y);
      let moved = false;
      if (vx && (fieldWalkable(p.scene, nx, p.y) || !curOk)) { p.x = nx; moved = true; }
      if (vy && (fieldWalkable(p.scene, p.x, ny) || !curOk)) { p.y = ny; moved = true; }
      if (!moved) {
        // slide along curved walls: pure perpendicular nudge to the input
        const px2 = -vy, py2 = vx;
        for (const sgn of [1, -1]) {
          const sx2 = p.x + px2 * sgn * spd * dt * 0.9;
          const sy2 = p.y + py2 * sgn * spd * dt * 0.9;
          if (fieldWalkable(p.scene, sx2, sy2)) { p.x = sx2; p.y = sy2; break; }
        }
      }
      // hysteresis: only change facing when one axis clearly dominates,
      // so diagonal joystick input doesn't flicker the sprite
      if (Math.abs(vx) > Math.abs(vy) * 1.25) p.dir = vx > 0 ? 'right' : 'left';
      else if (Math.abs(vy) > Math.abs(vx) * 1.25) p.dir = vy > 0 ? 'down' : 'up';
      p.animT += dt;
    }
    if (p.aEdge) {
      p.aEdge = false;
      if (Dialog.active()) Dialog.advance();
      else if (CurrentChapter.flags.ended) {
        if (CurrentChapter === Chapter1 && Chapter1.flags.endT > 2.5) startChapter2();
      }
      else if (!Cutscene.active) CurrentChapter.interact(p);
    }
  }

  // exits — all active players must stand in the zone.
  // players arriving from a transition must leave all zones once first.
  if (!frozen && act.length && !window.__navGateActive) {
    const s = Field.scenes[act[0].scene];
    for (const p of act) {
      if (!p._justArrived) continue;
      const inAny = (s.exits || []).some(ex =>
        p.x > ex.zone.x && p.x < ex.zone.x + ex.zone.w && p.y > ex.zone.y && p.y < ex.zone.y + ex.zone.h);
      if (!inAny) p._justArrived = false;
    }
    for (const ex of (s.exits || [])) {
      if (act.some(p => p._justArrived)) break;
      const allIn = act.every(p =>
        p.scene === act[0].scene &&
        p.x > ex.zone.x && p.x < ex.zone.x + ex.zone.w &&
        p.y > ex.zone.y && p.y < ex.zone.y + ex.zone.h);
      if (!allIn) { ex._warned = false; continue; }
      if (ex.enabled && !ex.enabled()) {
        if (!ex._warned && ex.deniedLine && !Dialog.active()) {
          ex._warned = true;
          Dialog.start([{ who: ex.deniedLine[0], text: ex.deniedLine[1] }]);
          // nudge players back out of the zone
          for (const p of act) { p.y += (ex.zone.y > 400 ? -30 : 30); }
        }
        continue;
      }
      if (ex.to) {
        const ferry = [...act];
        ferry.forEach(p => { p._justArrived = true; });
        // followers (cat, friar) ride along if the player they follow is in the ferry
        const tagalong = Object.values(CurrentChapter.npcs).filter(n => n.follow && !n.hidden &&
          (n.follow === 'party' || ferry.some(p => p.role === n.follow)));
        Field.transition(ex, ferry, () => {
          tagalong.forEach((n, i) => { n.scene = ferry[0].scene; n.x = ferry[0].x - 50 - i * 34; n.y = ferry[0].y + 10 + i * 8; });
        });
      }
      break;
    }
  }

  CurrentChapter.update(dt, players);
  // the Chapter One end card also advances on its own, eventually
  if (CurrentChapter === Chapter1 && Chapter1.flags.ended && Chapter1.flags.endT > 16)
    startChapter2();
  Objective.set(CurrentChapter.objective());
  updatePrompts();
}

// feet may not stand within a few px below a blocked top edge — stops tall
// sprites from visually overlapping the art above them
const TOP_STANDOFF = 7;
function fieldWalkable(sceneKey, x, y) {
  return fieldWalkableAt(sceneKey, x, y) && fieldWalkableAt(sceneKey, x, y - TOP_STANDOFF);
}
function fieldWalkableAt(sceneKey, x, y) {
  const s = Field.scenes[sceneKey];
  // the gate arch is baked walkable in the mask, but passable only when open
  if (s.archBlock && s.state !== 'open') {
    const a = s.archBlock;
    if (x > a.x && x < a.x + a.w && y > a.y && y < a.y + a.h) return false;
  }
  // walkExtra rects are unioned with the polygon
  for (const r of (s.walkExtra || [])) {
    if (r.state && r.state !== s.state) continue;
    if (x > r.x && x < r.x + r.w && y > r.y && y < r.y + r.h) {
      // still respect blocked shapes
      let ok = true;
      for (const b of (s.blocked || [])) {
        if (b.kind === 'rect' && x > b.x && x < b.x + b.w && y > b.y && y < b.y + b.h) ok = false;
        if (b.kind === 'circle' && Math.hypot(x - b.x, y - b.y) < b.r) ok = false;
      }
      if (ok) return true;
    }
  }
  return Field.walkable(x, y, sceneKey);
}

function updatePrompts() {
  for (const p of players) {
    if (!p || p.kb || !p.connected) continue;
    const text = CurrentChapter.promptFor(p) || '';
    if (text !== p.lastPrompt) { p.lastPrompt = text; Net.to(p.id, { type: 'prompt', text }); }
  }
}

/* ---------- render ---------- */
function render(dt) {
  const g = Screen.ctx;
  const { cw, ch, dpr } = Screen;
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.imageSmoothingEnabled = true;

  if (Title.active) { Title.draw(g); return; }

  const act = activePlayers();
  Field.draw(g, CurrentChapter.entities.concat(players.filter(Boolean)), dt, act);

  Dev.drawMask(g);

  FX.post(g);
  FX.bars(g);

  drawNameTags(g);
  drawMarkers(g);
  Objective.draw(g);
  Banner.draw(g);
  Dialog.draw(g);
  Cutscene.drawHold(g, players);
  Toasts.draw(g);
  Dev.drawHelp(g);
  if (CurrentChapter.flags.ended) drawEnd(g);

  const vg = g.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * 0.42, cw / 2, ch / 2, Math.max(cw, ch) * 0.72);
  vg.addColorStop(0, 'rgba(16,10,6,0)');
  vg.addColorStop(1, 'rgba(16,10,6,.38)');
  g.fillStyle = vg; g.fillRect(0, 0, cw, ch);

  FX.black(g);
}

function drawNameTags(g) {
  if (Cutscene.active) return;
  for (const p of players) {
    if (!p || p.hidden || p.scene !== Field.currentKey) continue;
    const [sx, sy] = Field.worldToScreen(p.x, p.y - p.h - 12);
    g.font = `600 13px ${SERIF}`;
    g.textAlign = 'center';
    const label = p.connected ? p.charName : p.charName + ' …';
    const w = g.measureText(label).width;
    g.fillStyle = 'rgba(20,12,4,.55)';
    roundRectPath(g, sx - w / 2 - 7, sy - 12, w + 14, 17, 8); g.fill();
    g.fillStyle = ROLE_INFO[p.role].color;
    g.beginPath(); g.arc(sx - w / 2 - 0.5, sy - 3.5, 3, 0, 7); g.fill();
    g.fillStyle = '#f2e4c4';
    g.fillText(label, sx + 3, sy + 1);
  }
}

function drawMarkers(g) {
  if (Dialog.active() || Cutscene.active || CurrentChapter.flags.ended) return;
  // ✦ over whoever holds the next story beat (chapter hook)
  const sm = CurrentChapter.storyMarker && CurrentChapter.storyMarker();
  if (sm) {
    const [sx, sy] = Field.worldToScreen(sm.x, sm.y);
    const bounce = Math.sin(time * 3) * 4;
    g.font = `700 24px ${SERIF}`;
    g.textAlign = 'center';
    g.strokeStyle = 'rgba(20,12,4,.6)'; g.lineWidth = 3;
    g.strokeText('✦', sx, sy + bounce);
    g.fillStyle = '#f2d16b';
    g.fillText('✦', sx, sy + bounce);
  }
  // ✧ over unlit story lamps during the rounds — visible across the scene
  if (CurrentChapter.lampHintActive && CurrentChapter.lampHintActive()) {
    const s = Field.scenes[Field.currentKey];
    for (const l of (s.lamps || [])) {
      if (!l.id || l.lit) continue;
      const [sx, sy] = Field.worldToScreen(l.x, l.y - 34);
      const bounce = Math.sin(time * 3 + l.x) * 4;
      g.font = `700 22px ${SERIF}`;
      g.textAlign = 'center';
      g.strokeStyle = 'rgba(20,12,4,.6)'; g.lineWidth = 3;
      g.strokeText('✧', sx, sy + bounce);
      g.fillStyle = '#ffd98a';
      g.fillText('✧', sx, sy + bounce);
    }
  }
  // "!" over interactables near each player
  const shown = new Set();
  for (const p of activePlayers()) {
    if (p.scene !== Field.currentKey) continue;
    const t = CurrentChapter.nearestThing(p);
    if (!t) continue;
    const key = t.kind + (t.key || '') + (t.lamp ? t.lamp.x : '');
    if (shown.has(key)) continue;
    shown.add(key);
    let x, y;
    if (t.ent) { x = t.ent.x; y = t.ent.y - t.ent.h - 14; }
    else if (t.lamp) { x = t.lamp.base[0]; y = t.lamp.base[1] - 160; }
    else if (t.kind === 'heartlight') { x = 672; y = 250; }
    else if (t.kind === 'waystone') { x = 565; y = 300; }
    else if (t.kind === 'notice') { x = 320; y = 400; }
    else if (t.kind === 'hearth') { x = 500; y = 220; }
    else if (t.at) { x = t.at[0]; y = t.at[1]; }
    else continue;
    const [sx, sy] = Field.worldToScreen(x, y);
    const bounce = Math.sin(time * 4) * 3;
    g.fillStyle = '#f2e4c4';
    roundRectPath(g, sx - 9, sy - 22 + bounce, 18, 18, 5); g.fill();
    g.strokeStyle = '#9c7a4c'; g.lineWidth = 1.5;
    roundRectPath(g, sx - 9, sy - 22 + bounce, 18, 18, 5); g.stroke();
    g.fillStyle = '#c9584a'; g.font = `700 13px ${SERIF}`;
    g.textAlign = 'center';
    g.fillText('!', sx, sy - 8.5 + bounce);
  }
}

function drawEnd(g) {
  const { cw, ch } = Screen;
  const two = CurrentChapter === Chapter2;
  const t = CurrentChapter.flags.endT;
  const a = Math.min(1, t / 2.5);
  g.fillStyle = `rgba(14,9,6,${a * 0.85})`;
  g.fillRect(0, 0, cw, ch);
  const ta = Math.min(1, (t - 0.8) / 1.5);
  if (ta <= 0) return;
  g.save();
  g.globalAlpha = ta;
  g.textAlign = 'center';
  g.fillStyle = '#e8b25c';
  g.font = `600 52px ${SERIF}`;
  g.fillText(two ? 'End of Chapter Two' : 'End of Chapter One', cw / 2, ch * 0.36);
  g.font = `italic 24px ${SERIF}`;
  g.fillStyle = '#c9b380';
  g.fillText(two ? '— The Lanternstead —' : '— Emberwake —', cw / 2, ch * 0.36 + 40);
  g.font = `italic 19px ${SERIF}`;
  g.fillStyle = '#e8d5b0';
  if (two) {
    g.fillText('the necklace has its first light', cw / 2, ch * 0.36 + 92);
  } else {
    g.fillText('A mapmaker who dreams of roads. A lamplighter with the last warm flame.', cw / 2, ch * 0.36 + 92);
    g.fillText('A village that will forget it ever existed — unless they remember it back.', cw / 2, ch * 0.36 + 122);
  }
  g.font = `17px ${SERIF}`;
  g.fillStyle = 'rgba(232,178,92,.75)';
  g.fillText('— to be continued —', cw / 2, ch * 0.36 + 178);
  if (!two && t > 2.5) {
    const pulse = 0.5 + 0.4 * Math.sin(time * 2.4);
    g.font = `500 18px ${SERIF}`;
    g.fillStyle = `rgba(242,228,196,${pulse.toFixed(2)})`;
    g.fillText('A — onward: Chapter Two', cw / 2, ch * 0.36 + 226);
  }
  const hb = 1 + Math.sin(time * 3) * 0.1;
  g.font = `${Math.round(30 * hb)}px serif`;
  g.fillStyle = two ? '#e8b25c' : '#e86e6e';
  g.fillText(two ? '🏮' : '🕯', cw / 2, ch * 0.36 - 70);
  g.restore();
}

/* ---------- dev: navigation quality gate ----------
   Acceptance test for a scene mask. Models a real player: BFS pathfinding
   on the walkability grid (like a human reading the screen), then the real
   movement code drives waypoint-to-waypoint. A pair fails if (a) no path
   with adequate clearance exists, or (b) the simulated player still stalls.
   Failures carry pinch locations so the bake can auto-repair. */
window.navGate = function (pois, maxFrames = 2000) {
  const j = players.find(p => p && p.role === 'vesper') || players.find(Boolean);
  if (!j) return 'no player';
  window.__navGateActive = true;
  const save = { x: j.x, y: j.y, scene: j.scene };
  const scene = j.scene;
  // sample the live walkability into an 8px grid
  const GS = 8, GW = 168, GH = 96;
  const grid = new Uint8Array(GW * GH);
  for (let gy = 0; gy < GH; gy++) for (let gx = 0; gx < GW; gx++)
    grid[gy * GW + gx] = fieldWalkable(scene, gx * GS + 4, gy * GS + 4) ? 1 : 0;
  // clearance: walkable AND all 8 neighbours walkable (≥ ~12px of room)
  const clear = new Uint8Array(GW * GH);
  for (let gy = 1; gy < GH - 1; gy++) for (let gx = 1; gx < GW - 1; gx++) {
    let ok = grid[gy * GW + gx];
    for (let dy = -1; dy <= 1 && ok; dy++) for (let dx = -1; dx <= 1; dx++)
      if (!grid[(gy + dy) * GW + gx + dx]) { ok = 0; break; }
    clear[gy * GW + gx] = ok;
  }
  const bfs = (g2, x0, y0, x1, y1) => {
    const prev = new Int32Array(GW * GH).fill(-2);
    const s = y0 * GW + x0, t = y1 * GW + x1;
    if (!g2[s] || !g2[t]) return null;
    prev[s] = -1;
    const q = [s];
    for (let h = 0; h < q.length; h++) {
      const cur = q[h];
      if (cur === t) break;
      const cx = cur % GW;
      for (const dd of [-1, 1, -GW, GW]) {
        const n = cur + dd;
        if (n < 0 || n >= GW * GH || Math.abs((n % GW) - cx) > 1) continue;
        if (g2[n] && prev[n] === -2) { prev[n] = cur; q.push(n); }
      }
    }
    if (prev[t] === -2) return null;
    const path = [];
    for (let cur = t; cur !== -1; cur = prev[cur]) path.push([(cur % GW) * GS + 4, ((cur / GW) | 0) * GS + 4]);
    return path.reverse();
  };
  // endpoints may hug walls (lamp bases, exit mouths): snap the BFS
  // endpoints to the nearest high-clearance cell within ~3 cells.
  const snap = (gx, gy) => {
    for (let r = 0; r <= 3; r++)
      for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
        const nx = gx + dx, ny = gy + dy;
        if (nx > 0 && ny > 0 && nx < GW && ny < GH && clear[ny * GW + nx]) return [nx, ny];
      }
    return null;
  };
  const failures = [], warnings = [];
  for (let a = 0; a < pois.length; a++) {
    for (let b = 0; b < pois.length; b++) {
      if (a === b) continue;
      const [sx, sy] = pois[a], [tx, ty] = pois[b];
      const s0 = snap(Math.round(sx / GS), Math.round(sy / GS));
      const s1 = snap(Math.round(tx / GS), Math.round(ty / GS));
      if (!s0 || !s1) {
        failures.push({ from: pois[a], to: pois[b], kind: 'POI_TIGHT', pinch: s0 ? [tx, ty] : [sx, sy] });
        continue;
      }
      const [gx0, gy0] = s0, [gx1, gy1] = s1;
      let path = bfs(clear, gx0, gy0, gx1, gy1);
      if (!path) {
        // no clearance path — is there ANY path? (pinch vs. disconnect)
        const loose = bfs(grid, gx0, gy0, gx1, gy1);
        failures.push({ from: pois[a], to: pois[b], kind: loose ? 'PINCH' : 'DISCONNECT',
          pinch: loose ? loose[Math.floor(loose.length / 2)] : null });
        continue;
      }
      // dense waypoints (~24px apart) so the driver tracks the route
      // tightly instead of cutting corners into concave footprints
      const wps = path.filter((_, i) => i % 3 === 2);
      wps.push([tx, ty]);
      j.x = sx; j.y = sy;
      let g = 0, lastX = j.x, lastY = j.y, maxStuck = 0, stuck = 0, wi = 0, ok = true, sinceAdv = 0;
      while (wi < wps.length && g++ < maxFrames) {
        const [wx, wy] = wps[wi];
        if (Math.hypot(j.x - wx, j.y - wy) < (wi === wps.length - 1 ? 26 : 14)) { wi++; sinceAdv = 0; continue; }
        const dx = wx - j.x, dy = wy - j.y;
        keys.KeyD = dx > 5; keys.KeyA = dx < -5; keys.KeyS = dy > 5; keys.KeyW = dy < -5;
        update(1 / 60);
        sinceAdv++;
        if (Math.hypot(j.x - lastX, j.y - lastY) < 0.4) { stuck++; maxStuck = Math.max(maxStuck, stuck); }
        else stuck = 0;
        lastX = j.x; lastY = j.y;
        if (stuck > 120) { ok = false; break; }
        if (sinceAdv > 300) {
          // orbiting a waypoint: snap back onto the route and continue
          j.x = wx; j.y = wy;
          if (!fieldWalkable(scene, j.x, j.y)) { ok = false; break; }
          wi++; sinceAdv = 0;
          warnings.push({ from: pois[a], to: pois[b], orbitedAt: [wx, wy] });
        }
        if (Dialog.active() || Cutscene.active || Field.transitioning) break;
      }
      keys.KeyD = keys.KeyA = keys.KeyS = keys.KeyW = false;
      if (!ok || g >= maxFrames)
        failures.push({ from: pois[a], to: pois[b], kind: 'STALL',
          pinch: [Math.round(j.x), Math.round(j.y)], maxStuck });
      if (Dialog.active()) Dialog.lines = null;
      if (Field.transitioning) break;
    }
  }
  j.x = save.x; j.y = save.y; j.scene = save.scene;
  window.__navGateActive = false;
  return { pairs: pois.length * (pois.length - 1), failures, warnings };
};

/* ---------- boot ---------- */
Screen.init();
Chapter1.build();
Chapter1.built = true;
Field.enter('forest');
Net.connect();
Objective.set(CurrentChapter.objective());
Banner.show('EMBERBROOK', 'Chapter One — Emberwake', 7);

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  try {
    update(dt);
    render(dt);
  } catch (err) {
    console.error('[emberbrook] frame error:', err.message, err.stack);
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
