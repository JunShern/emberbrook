'use strict';
/* ============================================================
   MAIN — boot, players & roles, loop, render pipeline
   ============================================================ */

window.players = [null, null];
const ROLE_INFO = {
  june: { charName: 'June', color: '#4f9f92' },
  cole: { charName: 'Cole', color: '#e0a94e' },
};

function makePlayer(role, id, kb) {
  const sp = Chapter1.spawnFor(role);
  return {
    id, role, kb: !!kb,
    charName: ROLE_INFO[role].charName,
    look: role, lightCarrier: role === 'cole',
    x: sp.x, y: sp.y, dir: sp.dir, moving: false, animT: 0,
    input: { x: 0, y: 0 }, a: false, aEdge: false,
    connected: true, lastPrompt: '',
  };
}

function byRole(role) { return players.find(p => p && p.role === role); }

function assignPlayer(m) {
  const role = m.role === 'cole' ? 'cole' : 'june';
  const existing = byRole(role);
  if (existing && existing.connected && !existing.kb) { Net.to(m.from, { type: 'taken', role }); return; }
  let slot = existing ? players.indexOf(existing) : players.findIndex(p => p === null);
  if (slot === -1) { Net.to(m.from, { type: 'full' }); return; }
  const old = players[slot];
  players[slot] = makePlayer(role, m.from, false);
  if (old && old.role === role) { players[slot].x = old.x; players[slot].y = old.y; }
  Net.to(m.from, { type: 'assign', role, name: ROLE_INFO[role].charName });
  Net.to(m.from, { type: 'phase', act: Chapter1.phase });
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
    Net.send({ type: 'phase', act: Chapter1.phase });
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
  const roles = ['june', 'cole'];
  roles.forEach((r, i) => {
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

/* ---------- keyboard control ----------
   WASD + E  → June      arrows + Enter → Cole
   Unclaimed roles are auto-claimed by the keyboard.
   K toggles OVERRIDE: keyboard also drives phone-claimed
   characters (for development, so you can leave the phones alone). */
const keys = {};
let kbOverride = false;
const kbDrives = (p) => p && (p.kb || kbOverride);

window.addEventListener('keydown', (e) => {
  keys[e.code] = true;
  AudioSys.init();
  if (e.code === 'KeyM') AudioSys.toggleMusic();
  if (e.code === 'KeyK') {
    kbOverride = !kbOverride;
    Toasts.add(kbOverride ? '⌨ keyboard override ON — WASD/E June · arrows/Enter Cole' : '⌨ keyboard override off', '#8fb0c9');
  }
  if (e.code === 'KeyP') {
    World.painted = !World.painted;
    Toasts.add(World.painted ? '🎨 painted backdrop ON' : '🎨 painted backdrop off (pixel tiles)', '#8fb0c9');
  }
  const P1K = ['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyE'], P2K = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter'];
  if (P1K.includes(e.code) && !byRole('june')) {
    const slot = players.findIndex(p => p === null);
    if (slot !== -1) { players[slot] = makePlayer('june', 'kb1', true); updatePanel(); }
  }
  if (P2K.includes(e.code) && !byRole('cole')) {
    const slot = players.findIndex(p => p === null);
    if (slot !== -1) { players[slot] = makePlayer('cole', 'kb2', true); updatePanel(); }
  }
  const j = byRole('june'), c = byRole('cole');
  if (e.code === 'KeyE' && kbDrives(j)) { if (!j.a) j.aEdge = true; j.a = true; }
  if (e.code === 'Enter' && kbDrives(c)) { if (!c.a) c.aEdge = true; c.a = true; }
});
window.addEventListener('keyup', (e) => {
  keys[e.code] = false;
  const j = byRole('june'), c = byRole('cole');
  if (e.code === 'KeyE' && kbDrives(j)) j.a = false;
  if (e.code === 'Enter' && kbDrives(c)) c.a = false;
});
window.addEventListener('pointerdown', () => AudioSys.init());

const kbWasMoving = { june: false, cole: false };
function keyboardInput() {
  const j = byRole('june'), c = byRole('cole');
  if (kbDrives(j)) {
    const x = (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0);
    const y = (keys.KeyS ? 1 : 0) - (keys.KeyW ? 1 : 0);
    // only overwrite phone input while keys are engaged (or just released)
    if (x || y || j.kb || kbWasMoving.june) { j.input.x = x; j.input.y = y; }
    kbWasMoving.june = !!(x || y);
  }
  if (kbDrives(c)) {
    const x = (keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0);
    const y = (keys.ArrowDown ? 1 : 0) - (keys.ArrowUp ? 1 : 0);
    if (x || y || c.kb || kbWasMoving.cole) { c.input.x = x; c.input.y = y; }
    kbWasMoving.cole = !!(x || y);
  }
}

/* ---------- update ---------- */
const SPEED = 72;

function update(dt) {
  time += dt;
  keyboardInput();
  FX.update(dt);
  World.update(dt);
  Dialog.update(dt);
  Banner.update(dt);
  Objective.update(dt);
  Toasts.update(dt);
  Cutscene.tick(dt, players);
  Particles.update(dt);

  const frozen = Dialog.active() || Cutscene.active || Chapter1.flags.ended;
  const actRoles = Chapter1.activeRoles();
  for (const p of players) {
    if (!p) continue;
    const active = actRoles.includes(p.role) && !p.hidden && !p.parked;
    if (!active) { p.moving = false; p.aEdge = false; continue; }
    let vx = p.input.x, vy = p.input.y;
    const len = Math.hypot(vx, vy);
    if (len > 1) { vx /= len; vy /= len; }
    p.moving = !frozen && len > 0.12;
    if (p.moving) {
      const nx = p.x + vx * SPEED * dt;
      if (!World.blocked(nx, p.y)) p.x = nx;
      const ny = p.y + vy * SPEED * dt;
      if (!World.blocked(p.x, ny)) p.y = ny;
      p.dir = Math.abs(vx) > Math.abs(vy) ? (vx > 0 ? 'right' : 'left') : (vy > 0 ? 'down' : 'up');
      p.animT += dt;
    }
    if (p.aEdge) {
      p.aEdge = false;
      if (Dialog.active()) Dialog.advance();
      else if (!Cutscene.active && !Chapter1.flags.ended) Chapter1.interact(p);
    }
  }

  Chapter1.update(dt, players);
  Objective.set(Chapter1.objective());
  const focuses = players.filter(p => p && !p.hidden && !p.parked && actRoles.includes(p.role));
  Camera.update(dt, focuses, World.W * T, World.H * T);
  updatePrompts();
}

function updatePrompts() {
  for (const p of players) {
    if (!p || p.kb || !p.connected) continue;
    const text = Chapter1.promptFor(p) || '';
    if (text !== p.lastPrompt) { p.lastPrompt = text; Net.to(p.id, { type: 'prompt', text }); }
  }
}

/* ---------- render ---------- */
function render() {
  const g = Screen.ctx;
  const { cw, ch, dpr } = Screen;
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.fillStyle = '#10120c';
  g.fillRect(0, 0, cw, ch);
  g.imageSmoothingEnabled = false;

  const sx = FX.shake ? Math.sin(time * 55) * FX.shake : 0;
  const sy = FX.shake ? Math.cos(time * 47) * FX.shake : 0;
  g.save();
  g.translate(cw / 2, ch / 2);
  g.scale(Camera.zoom, Camera.zoom);
  g.translate(-Camera.x + sx, -Camera.y + sy);
  const ents = [...Chapter1.entities, ...players.filter(Boolean)];
  World.drawScene(g, ents);
  Particles.draw(g);
  g.restore();

  World.drawLighting(g, ents);
  FX.post(g);
  FX.bars(g);          // cinematic bars sit under the UI so dialogue is never cropped

  drawNameTags(g);
  drawMarkers(g);
  Objective.draw(g);
  Banner.draw(g);
  Dialog.draw(g);
  Cutscene.drawHold(g, players);
  Toasts.draw(g);
  if (Chapter1.flags.ended) drawEnd(g);

  // vignette
  const vg = g.createRadialGradient(cw / 2, ch / 2, Math.min(cw, ch) * 0.42, cw / 2, ch / 2, Math.max(cw, ch) * 0.72);
  vg.addColorStop(0, 'rgba(16,10,6,0)');
  vg.addColorStop(1, 'rgba(16,10,6,.42)');
  g.fillStyle = vg; g.fillRect(0, 0, cw, ch);

  FX.black(g);
}

function drawNameTags(g) {
  if (Cutscene.active) return;
  for (const p of players) {
    if (!p) continue;
    const [sx, sy] = Camera.worldToScreen(p.x, p.y - 26);
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
  if (Dialog.active() || Cutscene.active || Chapter1.flags.ended) return;
  // ✦ over Rowan when he has the next story beat
  const F = Chapter1.flags;
  const showRowan = (F.hushDone && !F.pactDone && Object.keys(F.seen).length >= 4);
  if (showRowan) {
    const r = Chapter1.npcs.rowan;
    const [sx, sy] = Camera.worldToScreen(r.x, r.y - 34);
    const bounce = Math.sin(time * 3) * 3;
    g.font = `700 20px ${SERIF}`;
    g.textAlign = 'center';
    g.strokeStyle = 'rgba(20,12,4,.6)'; g.lineWidth = 3;
    g.strokeText('✦', sx, sy + bounce);
    g.fillStyle = '#f2d16b';
    g.fillText('✦', sx, sy + bounce);
  }
  // "!" over whatever each player could interact with
  const shown = new Set();
  for (const p of players) {
    if (!p) continue;
    const t = Chapter1.nearestThing(p);
    if (!t) continue;
    const key = t.kind + (t.key || '') + (t.lamp ? t.lamp.x : '');
    if (shown.has(key)) continue;
    shown.add(key);
    const x = t.ent ? t.ent.x : t.lamp ? t.lamp.x : t.kind === 'heartlight' ? World.heartlight.x : p.x;
    const y = t.ent ? t.ent.y - (t.ent.cat ? 16 : 30) : t.lamp ? t.lamp.y - 40 : t.kind === 'heartlight' ? World.heartlight.y - 46 : p.y - 30;
    const [sx, sy] = Camera.worldToScreen(x, y);
    const bounce = Math.sin(time * 4) * 3;
    g.fillStyle = '#f2e4c4';
    roundRectPath(g, sx - 8, sy - 20 + bounce, 16, 16, 5); g.fill();
    g.strokeStyle = '#9c7a4c'; g.lineWidth = 1.5;
    roundRectPath(g, sx - 8, sy - 20 + bounce, 16, 16, 5); g.stroke();
    g.fillStyle = '#c9584a'; g.font = `700 12px ${SERIF}`;
    g.textAlign = 'center';
    g.fillText('!', sx, sy - 8 + bounce);
  }
}

function drawEnd(g) {
  const { cw, ch } = Screen;
  const t = Chapter1.flags.endT;
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
  g.fillText('End of Chapter One', cw / 2, ch * 0.36);
  g.font = `italic 24px ${SERIF}`;
  g.fillStyle = '#c9b380';
  g.fillText('— Emberwake —', cw / 2, ch * 0.36 + 40);
  g.font = `italic 19px ${SERIF}`;
  g.fillStyle = '#e8d5b0';
  g.fillText('A mapmaker who dreams of roads. A lamplighter with the last warm flame.', cw / 2, ch * 0.36 + 92);
  g.fillText('A village that will forget it ever existed — unless they remember it back.', cw / 2, ch * 0.36 + 122);
  g.font = `17px ${SERIF}`;
  g.fillStyle = 'rgba(232,178,92,.75)';
  g.fillText('— to be continued · tell Claude what Chapter Two should hold —', cw / 2, ch * 0.36 + 178);
  g.restore();
}

/* ---------- boot ---------- */
Screen.init();
Chapter1.build();
Net.connect();
Objective.set(Chapter1.objective());
Banner.show('EMBERBROOK', 'Chapter One — Emberwake', 7);

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  update(dt);
  render();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
