'use strict';
/* ============================================================
   ITEMS — Phase 1 TREASURE engine slice (MECHANICS.md Part 1).
   - ITEMS: static item definitions (the Seed Ten + wick-oil,
     pennies). Content, not state.
   - Inventory: the one runtime state object. Display-
     authoritative, display-rendered, JSON-clean (toJSON /
     restore) for the future save system.
   - BOAT_MOUNTS / BoatShelf: the ~8 named mounts + the
     placed-item render pass over the boat prop (§1.4).
   - Pack: the per-player TV pack panels (§1.2). B toggles,
     stick browses, A acts, handover by adjacency.
   - ItemInteract: the generic chest / pickup / shop / gift /
     mount interact patterns (§1.3) — chapters declare, the
     engine plays them.
   - DevItems: the dev-key test harness (I / T / U, see H).
   Loads after story.js (Choice lives there), before chapters.
   ============================================================ */

/* ---------- static definitions (§1.1) ----------
   icon/sprite are art slots — null until the asset exists; the
   glyph is the placeholder the panels and boat shelf draw. */
const ITEMS = {
  'honeybun-tin': {
    name: 'Poppy’s honeybun tin', short: 'the honeybun tin',
    desc: 'Dented tin, painted poppies. The count inside is a lie in Poppy’s favor.',
    cls: 'story', glyph: '🍪', icon: null, sprite: null,
    boat: { mount: 'lockerTop' }, tags: {},
  },
  'moon-map': {
    name: 'Pip’s map to the MOON', short: 'the moon map',
    desc: 'Crayon, folded eight ways. The route is impossible and the arrow is confident.',
    cls: 'story', glyph: '🗺', icon: null, sprite: null,
    boat: { mount: 'tillerPocket' }, tags: {},
  },
  'hand-lamp': {
    name: 'Grandmother’s hand-lamp', short: 'the hand-lamp',
    desc: 'Small tin lamp, wick trimmed by a steady hand for sixty years.',
    cls: 'story', glyph: '🪔', icon: null, sprite: null,
    boat: { mount: 'cabinDoor' }, tags: {},
  },
  'pumpkin': {
    name: 'Hobb’s pumpkin', short: 'the pumpkin',
    desc: 'One pumpkin of forty tons. It rides with dignity.',
    cls: 'story', glyph: '🎃', icon: null, sprite: null,
    boat: { mount: 'deck' }, tags: {},
  },
  'festival-ribbon': {
    name: 'The festival ribbon', short: 'the ribbon',
    desc: 'Emberwake weave, ember-orange. It wants wind.',
    cls: 'story', glyph: '🎗', icon: null, sprite: null,
    boat: { mount: null },              // player's choice — the §1.4 tutorial
    tags: {},
  },
  'biscuit-collar': {
    name: 'Biscuit’s collar', short: 'the collar',
    desc: 'Leather collar, brass tag worn to a shine: BISCUIT.',
    cls: 'find', glyph: '📿', icon: null, sprite: null,
    boat: null,                          // worn by Biscuit, someday
    tags: {},
  },
  'striker': {
    name: 'A lamplighter’s striker', short: 'the striker',
    desc: 'Order brass, flint jaw. Volume Nine is said to be clear about these.',
    cls: 'find', glyph: '⚒', icon: null, sprite: null,
    boat: { mount: 'rail' }, tags: { verb: 'light' },
  },
  'wick-oil': {
    name: 'Wick-oil', short: 'the wick-oil',
    desc: 'A stoppered flask of the Order’s slow oil. Banks a lantern for a bad night.',
    cls: 'consumable', glyph: '🏺', icon: null, sprite: null,
    boat: null, tags: { cap: 2 },
  },
  'smoked-eel': {
    name: 'Smoked eel', short: 'the smoked eel',
    desc: 'A yard of Dellhollow’s finest. Ask her yourself.',
    cls: 'find', glyph: '🐟', icon: null, sprite: null,
    boat: null,                          // eaten, eventually, by somebody small
    tags: {},
  },
  'boat-hook': {
    name: 'A river-pilot’s boat-hook', short: 'the boat-hook',
    desc: 'Ash shaft, bronze head, initials burned near the grip. Kept dry a long time.',
    cls: 'find', glyph: '🪝', icon: null, sprite: null,
    boat: { mount: 'stern' }, tags: { giftFor: 'maren' },
  },
  'creel-rope': {
    name: 'Creel’s rope', short: 'the rope',
    desc: 'Forty feet of fresh splice. It tells you before it goes.',
    cls: 'find', glyph: '🪢', icon: null, sprite: null,
    boat: { mount: 'stern' }, tags: { verb: 'climb' },
  },
  'sorrel-loaf': {
    name: 'A Sorrel loaf', short: 'the loaf',
    desc: 'A whole loaf, still warm. Half the town runs on these.',
    cls: 'find', glyph: '🍞', icon: null, sprite: null,
    boat: null, tags: { giftFor: 'creel' },
  },
  'penny': {
    name: 'Penny', short: 'a penny',
    desc: 'River-worn copper. Single digits buy most things worth having.',
    cls: 'coin', glyph: '🪙', icon: null, sprite: null,
    boat: null, tags: {},
  },
};

/* which chapter an item was got in — recorded on grant for the save system */
function itemChapterTag() {
  const c = window.CurrentChapter;
  if (typeof Chapter3 !== 'undefined' && c === Chapter3) return 'ch3';
  if (typeof Chapter2 !== 'undefined' && c === Chapter2) return 'ch2';
  return 'ch1';
}

/* ---------- runtime state (display-authoritative; §1.1) ----------
   Everything lives in .data, which is plain JSON: owned item state,
   per-player penny stacks (coins are per-player and can't share the
   single id-keyed owned map — hence their own little table), plus
   pickup/chest/gift bookkeeping so chapters can guard their considers. */
const Inventory = {
  data: { owned: {}, pennies: {}, found: {}, chests: {}, given: {} },

  reset() { this.data = { owned: {}, pennies: {}, found: {}, chests: {}, given: {} }; },
  toJSON() { return this.data; },
  restore(d) { if (d && d.owned) this.data = d; },

  def(id) { return ITEMS[id]; },
  ownerName(role) {
    if (role === 'boat') return 'the boat';
    return (typeof ROLE_INFO !== 'undefined' && ROLE_INFO[role]) ? ROLE_INFO[role].charName : role;
  },

  // cutscene / chest / pickup / shop entry point; announces per §1.2
  grant(id, role, n, quiet) {
    const def = ITEMS[id];
    if (!def) { console.warn('[items] unknown item:', id); return; }
    n = n || 1;
    if (def.cls === 'coin') {
      this.data.pennies[role] = (this.data.pennies[role] || 0) + n;
      if (!quiet) Toasts.add(`✦ ${n} penn${n === 1 ? 'y' : 'ies'} — ${this.ownerName(role)}’s purse`);
      return;
    }
    const o = this.data.owned;
    const cap = (def.tags && def.tags.cap) || 99;
    if (o[id]) o[id].n = Math.min(cap, o[id].n + n);            // stacks keep their carrier
    else o[id] = { owner: role, n: Math.min(n, cap), mount: null, got: itemChapterTag() };
    if (!quiet) Toasts.add(`✦ ${def.name} — ${this.ownerName(o[id].owner)}’s pack`);
  },

  // player → player handover (proximity is the caller's gate; §1.2)
  transfer(id, role) {
    const o = this.data.owned[id];
    if (!o) return;
    o.owner = role; o.mount = null;
    Toasts.add(`✦ ${ITEMS[id].name} — handed to ${this.ownerName(role)}`);
  },

  // player → NPC; the payoff flag belongs to the scene, not here
  give(id, npcKey) {
    const o = this.data.owned[id];
    if (!o || ITEMS[id].cls === 'story') return;     // story items never leave the party
    if (o.n > 1) o.n--;
    else delete this.data.owned[id];
    this.data.given[id] = npcKey;
    const who = (typeof SPEAKERS !== 'undefined' && SPEAKERS[npcKey]) ? SPEAKERS[npcKey].name : npcKey;
    Toasts.add(`✦ ${ITEMS[id].name} — given to ${who}`);
  },

  // pack ↔ boat decor (§1.4)
  place(id, mount) {
    const o = this.data.owned[id];
    if (!o || !ITEMS[id].boat) return;
    o.owner = 'boat'; o.mount = mount;
    Toasts.add(`✦ ${ITEMS[id].name} — set on the boat`);
  },
  unplace(id, role) {
    const o = this.data.owned[id];
    if (!o) return;
    o.owner = role; o.mount = null;
    Toasts.add(`✦ ${ITEMS[id].name} — back in ${this.ownerName(role)}’s pack`);
  },

  // consumables
  spend(id, n, role) {
    const def = ITEMS[id];
    n = n || 1;
    if (def && def.cls === 'coin') return this.spendPennies(role, n);
    const o = this.data.owned[id];
    if (!o || o.n < n) return false;
    o.n -= n;
    if (o.n <= 0) delete this.data.owned[id];
    return true;
  },
  pennies(role) { return this.data.pennies[role] || 0; },
  spendPennies(role, n) {
    if (this.pennies(role) < n) return false;
    this.data.pennies[role] -= n;
    return true;
  },

  count(id) { const o = this.data.owned[id]; return o ? o.n : 0; },
  has(id) { return !!this.data.owned[id]; },
  carriedBy(role) {
    return Object.keys(this.data.owned).filter(id => this.data.owned[id].owner === role);
  },
  boatItems() {
    return Object.keys(this.data.owned)
      .filter(id => this.data.owned[id].owner === 'boat' && this.data.owned[id].mount)
      .map(id => ({ id, mount: this.data.owned[id].mount }));
  },
  mountedAt(mount) {
    return Object.keys(this.data.owned)
      .find(id => this.data.owned[id].owner === 'boat' && this.data.owned[id].mount === mount) || null;
  },

  // chapter-side guards for one-shot considers
  chestOpen(id) { return !!this.data.chests[id]; },
  markChest(id) { this.data.chests[id] = true; },
  found(id) { return !!this.data.found[id]; },
  markFound(id) { this.data.found[id] = true; },
};

/* ---------- the boat shelf (§1.4) ---------- */
const BOAT_MOUNTS = {
  prow:         { dx: -95, dy: -40 },   // the lantern hook (painted into the design)
  mast:         { dx:   0, dy: -70 },
  rail:         { dx:  40, dy: -30 },
  lockerTop:    { dx: -55, dy: -25 },   // the bow locker Odessa filled
  stern:        { dx:  90, dy: -20 },
  tillerPocket: { dx:  75, dy: -35 },   // charts live here
  cabinDoor:    { dx:  20, dy: -50 },   // a hook
  deck:         { dx: -20, dy: -10 },   // loose cargo (the pumpkin)
};

const BoatShelf = {
  isBoat(e) { return !!e && e.char === 'boat-side' && !e.hidden; },
  // world-space ground point under a mount — where a keeper stands to reach it
  mountGround(boat, name) {
    const m = BOAT_MOUNTS[name];
    const flip = boat.dir === 'left' ? -1 : 1;
    return [boat.x + m.dx * flip, boat.y];
  },
  // called from Sprites.draw with the origin translated to (boat.x, boat.y):
  // draws every placed item over the prop, in the boat's own layer
  drawMounted(g, boat) {
    const flip = boat.dir === 'left' ? -1 : 1;
    for (const { id, mount } of Inventory.boatItems()) {
      const def = ITEMS[id], m = BOAT_MOUNTS[mount];
      if (!def || !m) continue;
      const x = m.dx * flip, y = m.dy;
      g.save();
      g.textAlign = 'center';
      g.font = '28px serif';
      g.strokeStyle = 'rgba(20,12,4,.55)'; g.lineWidth = 3;
      g.strokeText(def.glyph, x, y);
      g.fillStyle = '#f2e4c4';
      g.fillText(def.glyph, x, y);
      g.restore();
    }
  },
};

/* ---------- TV pack panels (§1.2) ----------
   Compact per-player card in the checkpoint-menu house style.
   P1 (Vesper) slides in on the left, P2 (Lake) on the right;
   both can be open. The game does not pause — the character
   simply stands (main.js suppresses movement while open). */
const Pack = {
  panels: {
    vesper: { open: false, sel: 0, mode: 'list', actSel: 0, actions: null, _rep: 0 },
    lake:   { open: false, sel: 0, mode: 'list', actSel: 0, actions: null, _rep: 0 },
  },
  isOpen(role) { const pn = this.panels[role]; return !!(pn && pn.open); },
  close(role) { const pn = this.panels[role]; if (pn) { pn.open = false; pn.mode = 'list'; } },
  closeAll() { this.close('vesper'); this.close('lake'); },

  toggle(p) {
    const pn = this.panels[p.role];
    if (!pn) return;
    if (pn.open && pn.mode === 'act') { pn.mode = 'list'; AudioSys.blip(360); return; }  // B backs out
    pn.open = !pn.open;
    pn.mode = 'list'; pn.sel = 0;
    AudioSys.blip(pn.open ? 620 : 360);
  },

  update(dt, players) {
    if (Cutscene.active || (typeof Title !== 'undefined' && Title.active)) { this.closeAll(); return; }
    if (Dialog.active() || Choice.active) return;      // browsing pauses under story UI
    for (const p of players) {
      if (!p) continue;
      const pn = this.panels[p.role];
      if (!pn || !pn.open) continue;
      const items = Inventory.carriedBy(p.role);
      pn.sel = Math.max(0, Math.min(pn.sel, Math.max(0, items.length - 1)));
      pn._rep -= dt;
      const y = p.input.y;
      if (Math.abs(y) > 0.5) {
        if (pn._rep <= 0) {
          pn._rep = 0.22;
          const d = y > 0 ? 1 : -1;
          if (pn.mode === 'act' && pn.actions) {
            const n = pn.actions.length;
            pn.actSel = ((pn.actSel + d) % n + n) % n;
          } else if (items.length > 1) {
            const n = items.length;
            pn.sel = ((pn.sel + d) % n + n) % n;
          }
          AudioSys.blip(520);
        }
      } else pn._rep = 0;
    }
  },

  // A inside the panel: open the action list on the item, or run the action
  act(p, players) {
    const pn = this.panels[p.role];
    if (!pn) return;
    const items = Inventory.carriedBy(p.role);
    if (pn.mode === 'act' && pn.actions) {
      const a = pn.actions[pn.actSel];
      if (a && a.disabled) { AudioSys.blip(300); return; }
      pn.mode = 'list';
      if (a && a.run) a.run();
      return;
    }
    if (!items.length) { AudioSys.blip(300); return; }
    const id = items[pn.sel];
    // handover is the pack's one verb: adjacency-gated (< ~70 px, same scene)
    const other = players.find(q => q && q !== p && !q.hidden && !q.parked &&
      q.scene === p.scene && Math.hypot(q.x - p.x, q.y - p.y) < 70);
    const acts = [];
    if (other) acts.push({ label: `Hand to ${other.charName}`, run: () => this.handOver(p, other, id) });
    else acts.push({ label: '(nobody in arm’s reach)', disabled: true });
    acts.push({ label: 'Back' });
    pn.actions = acts; pn.actSel = 0; pn.mode = 'act';
    AudioSys.blip(620);
  },

  handOver(giver, taker, id) {
    // re-validate — the couch may have wandered while the menu was up
    if (giver.scene !== taker.scene || Math.hypot(giver.x - taker.x, giver.y - taker.y) >= 70) {
      AudioSys.blip(300); return;
    }
    Inventory.transfer(id, taker.role);
    for (const e of [giver, taker]) {
      Particles.burst(8, () => ({
        kind: 'sparkle',
        x: e.x + (Math.random() - 0.5) * 34,
        y: e.y - e.h * 0.5 - Math.random() * 24,
        life: 0.9,
      }));
      if (!e.kb && e.connected) Net.to(e.id, { type: 'buzz', ms: 80 });
    }
    AudioSys.sparkle();
  },

  draw(g, players) {
    if (Cutscene.active || (typeof Title !== 'undefined' && Title.active)) return;
    const { cw, ch } = Screen;
    for (const role of ['vesper', 'lake']) {
      const pn = this.panels[role];
      if (!pn.open) continue;
      const items = Inventory.carriedBy(role);
      const selId = items[pn.sel];
      const selDef = selId ? ITEMS[selId] : null;
      const w = 276, rowH = 30;
      const rows = Math.max(1, items.length);
      const descH = selDef ? 44 : 0;
      const h = 74 + rows * rowH + descH + 60;
      const x = role === 'vesper' ? 20 : cw - w - 20;
      const y = Math.max(16, Math.min(ch - h - 16, ch / 2 - h / 2 - 20));
      g.save();
      // card — checkpoint-menu house style
      g.fillStyle = 'rgba(12,8,5,.9)';
      roundRectPath(g, x, y, w, h, 14); g.fill();
      g.strokeStyle = '#9c7a4c'; g.lineWidth = 2;
      roundRectPath(g, x, y, w, h, 14); g.stroke();
      // header
      const info = (typeof ROLE_INFO !== 'undefined' && ROLE_INFO[role]) || { charName: role, color: '#e0a94e' };
      g.textAlign = 'left';
      g.fillStyle = info.color;
      g.beginPath(); g.arc(x + 28, y + 34, 5, 0, 7); g.fill();
      g.font = `600 20px ${SERIF}`;
      g.fillStyle = '#e0a94e';
      g.fillText(`${info.charName} — pack`, x + 42, y + 41);
      // item rows
      let ly = y + 74;
      if (!items.length) {
        g.font = `italic 14px ${SERIF}`;
        g.fillStyle = 'rgba(242,228,196,.55)';
        g.fillText('Nothing carried yet.', x + 28, ly);
        ly += rowH;
      } else {
        items.forEach((id, i) => {
          const def = ITEMS[id];
          const st = Inventory.data.owned[id];
          if (i === pn.sel) {
            g.fillStyle = 'rgba(224,169,78,.18)';
            roundRectPath(g, x + 12, ly - 19, w - 24, 27, 7); g.fill();
          }
          g.font = '16px serif';
          g.fillStyle = '#f2e4c4';
          g.fillText(def.glyph, x + 22, ly);
          g.font = `500 15px ${SERIF}`;
          g.fillStyle = i === pn.sel ? '#f2d16b' : '#c9b380';
          g.fillText(def.name + (st.n > 1 ? `  ×${st.n}` : ''), x + 48, ly);
          ly += rowH;
        });
      }
      // one-line desc of the highlighted item
      if (selDef) {
        g.font = `italic 12.5px ${SERIF}`;
        g.fillStyle = '#a89a7a';
        wrapTextLeft(g, selDef.desc, x + 24, ly + 4, w - 46, 16);
        ly += descH;
      }
      // pennies + hints
      g.strokeStyle = 'rgba(156,122,76,.45)'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(x + 16, ly + 8); g.lineTo(x + w - 16, ly + 8); g.stroke();
      const n = Inventory.pennies(role);
      g.font = '13px serif'; g.fillStyle = '#f2e4c4';
      g.fillText('🪙', x + 22, ly + 30);
      g.font = `500 14px ${SERIF}`; g.fillStyle = '#f2d16b';
      g.fillText(`Pennies · ${n}`, x + 44, ly + 30);
      g.font = `italic 11px ${SERIF}`;
      g.fillStyle = 'rgba(242,228,196,.45)';
      g.fillText('stick — browse · A — act · B — close', x + 24, y + h - 14);
      // action submenu, beside the highlighted row
      if (pn.mode === 'act' && pn.actions) {
        const aw = 172, ah = 20 + pn.actions.length * 26;
        const ax = role === 'vesper' ? x + w + 8 : x - aw - 8;
        const ay = Math.min(ch - ah - 12, y + 60 + pn.sel * rowH);
        g.fillStyle = 'rgba(12,8,5,.94)';
        roundRectPath(g, ax, ay, aw, ah, 10); g.fill();
        g.strokeStyle = '#9c7a4c'; g.lineWidth = 1.5;
        roundRectPath(g, ax, ay, aw, ah, 10); g.stroke();
        pn.actions.forEach((a, i) => {
          const ry = ay + 26 + i * 26;
          if (i === pn.actSel && !a.disabled) {
            g.fillStyle = 'rgba(224,169,78,.18)';
            roundRectPath(g, ax + 8, ry - 16, aw - 16, 23, 6); g.fill();
          }
          g.font = `500 14px ${SERIF}`;
          g.fillStyle = a.disabled ? '#7a6d55' : (i === pn.actSel ? '#f2d16b' : '#c9b380');
          g.fillText(a.label, ax + 18, ry);
        });
      }
      g.restore();
    }
  },

  // the money display rule (§1.2): within a stall's earshot the penny
  // count also shows as a tiny per-player corner tally
  drawTally(g, players) {
    if (Cutscene.active || CurrentChapter.flags.ended) return;
    const { cw, ch } = Screen;
    for (const p of players) {
      if (!p || p.hidden || p.parked || p.scene !== Field.currentKey) continue;
      if (!ItemInteract.stallNear(p)) continue;
      const info = (typeof ROLE_INFO !== 'undefined' && ROLE_INFO[p.role]) || { color: '#e0a94e' };
      const n = Inventory.pennies(p.role);
      const text = `${n} penn${n === 1 ? 'y' : 'ies'}`;
      g.save();
      g.font = `500 14px ${SERIF}`;
      const tw = g.measureText(text).width;
      const w = tw + 40, y = ch - 44;
      const x = p.role === 'vesper' ? 16 : cw - w - 16;
      g.fillStyle = 'rgba(24,16,8,.72)';
      roundRectPath(g, x, y, w, 28, 9); g.fill();
      g.strokeStyle = 'rgba(201,151,63,.55)'; g.lineWidth = 1.5;
      roundRectPath(g, x, y, w, 28, 9); g.stroke();
      g.fillStyle = info.color;
      g.beginPath(); g.arc(x + 14, y + 14, 4, 0, 7); g.fill();
      g.textAlign = 'left';
      g.fillStyle = '#f2e4c4';
      g.fillText(text, x + 26, y + 19);
      g.restore();
    }
  },
};

/* ---------- generic interact patterns (§1.3) ----------
   Chapters declare things; the engine plays them. Handled kinds:
   - {kind:'chest', id, flavor, grants:[[id,n]], after?} — one-shot, small
     stage moment (Cutscene), grants announce.  Guard: Inventory.chestOpen(id).
   - {kind:'pickup', id, itemId?, flavor} — flavor line, then the grant.
     Guard: Inventory.found(id).
   - {kind:'shop', id, name, patter:[[who,text]], stock:[{id,price}],
     sell?:[{id,price}]} — stall patter, then one `choice` question.
   - gift: NPC wants-table (setWant) — the A-prompt near the NPC becomes
     the give, played through the choice primitive.
   - boat mounts: place/take-back prompts near a visible boat prop.
   Chapters may also handle any of this themselves; this layer only runs
   for declared shapes it recognizes. */
const ItemInteract = {
  wants: {},        // npcKey -> { id, onGift, keep }  ('*' = any NPC — dev)
  stalls: [],       // { scene, x, y, r, dev } — earshot zones for the tally
  devThings: [],    // harness-injected considered things

  setWant(npcKey, id, onGift) { this.wants[npcKey] = { id, onGift }; },
  clearWant(npcKey) { delete this.wants[npcKey]; },
  registerStall(scene, x, y, r, dev) { this.stalls.push({ scene, x, y, r: r || 220, dev: !!dev }); },
  stallNear(p) {
    return this.stalls.some(s => s.scene === p.scene && Math.hypot(p.x - s.x, p.y - s.y) < s.r);
  },

  wantFor(npcKey, p) {
    const w = this.wants[npcKey] || this.wants['*'];
    if (!w) return null;
    const st = Inventory.data.owned[w.id];
    if (!st || st.owner !== p.role) return null;
    if (ITEMS[w.id].cls === 'story') return null;
    return w;
  },

  findBoat(p) {
    return (CurrentChapter.entities || []).find(e => BoatShelf.isBoat(e) && e.scene === p.scene);
  },

  // engine-side considered things: dev spawns + boat mounts
  nearest(p) {
    let best = null, bd = Infinity;
    const consider = (x, y, thing, r) => {
      const d = Math.hypot(p.x - x, p.y - y);
      if (d > (r || 75)) return;
      if (d < bd) { bd = d; best = thing; }
    };
    for (const t of this.devThings) {
      if (t.scene !== p.scene) continue;
      if (t.kind === 'chest' && Inventory.chestOpen(t.id)) continue;
      consider(t.x, t.y, t, t.r);
    }
    const boat = this.findBoat(p);
    if (boat) {
      const placeable = Inventory.carriedBy(p.role).filter(id => ITEMS[id].boat);
      for (const name of Object.keys(BOAT_MOUNTS)) {
        const [mx, my] = BoatShelf.mountGround(boat, name);
        const anchor = [mx, boat.y + BOAT_MOUNTS[name].dy - 26];
        const heldId = Inventory.mountedAt(name);
        if (heldId) consider(mx, my, { kind: 'unmount', mount: name, id: heldId, at: anchor }, 58);
        else if (placeable.length) consider(mx, my, { kind: 'mount', mount: name, items: placeable, at: anchor }, 58);
      }
    }
    return best;
  },

  promptFor(p) {
    const t = this.nearest(p);
    if (t) {
      if (t.kind === 'chest') return t.prompt || `A — open ${t.name || 'the chest'}`;
      if (t.kind === 'shop') return `A — ${t.name || 'the stall'}`;
      if (t.kind === 'pickup') return `A — take ${ITEMS[t.itemId || t.id].short}`;
      if (t.kind === 'mount') return `A — set ${ITEMS[t.items[0]].short} here`;
      if (t.kind === 'unmount') return `A — take ${ITEMS[t.id].short} back`;
    }
    const tc = CurrentChapter.nearestThing(p);
    if (tc) {
      if (tc.kind === 'npc') {
        const w = this.wantFor(tc.key, p);
        if (w) {
          const who = (typeof SPEAKERS !== 'undefined' && SPEAKERS[tc.key]) ? SPEAKERS[tc.key].name : tc.key;
          return `A — give ${who} ${ITEMS[w.id].short}`;
        }
      }
      if (tc.kind === 'chest' && tc.grants) return tc.prompt || `A — open ${tc.name || 'the chest'}`;
      if (tc.kind === 'pickup') {
        const d = ITEMS[tc.itemId || tc.id];
        if (d) return `A — take ${d.short}`;
      }
      if (tc.kind === 'shop' && tc.stock) return `A — ${tc.name || 'the stall'}`;
    }
    return '';
  },

  // returns true if the interact was consumed by the engine layer
  handle(p) {
    const t = this.nearest(p);
    if (t) { this.dispatch(p, t); return true; }
    const tc = CurrentChapter.nearestThing(p);
    if (tc && tc.kind === 'npc') {
      const w = this.wantFor(tc.key, p);
      if (w) { this.giftFlow(p, tc, w); return true; }
    }
    if (tc && ((tc.kind === 'chest' && tc.grants) || (tc.kind === 'pickup' && ITEMS[tc.itemId || tc.id]) ||
               (tc.kind === 'shop' && tc.stock))) {
      this.dispatch(p, tc);
      return true;
    }
    return false;
  },

  dispatch(p, t) {
    if (t.kind === 'chest') return this.chestFlow(p, t);
    if (t.kind === 'pickup') return this.pickupFlow(p, t);
    if (t.kind === 'shop') return this.shopFlow(p, t);
    if (t.kind === 'mount') return this.mountFlow(p, t);
    if (t.kind === 'unmount') {
      Inventory.unplace(t.id, p.role);
      AudioSys.sparkle();
      return;
    }
  },

  // chest: one-shot container, public event — a small stage moment
  chestFlow(p, t) {
    if (Inventory.chestOpen(t.id)) return;
    Inventory.markChest(t.id);
    const steps = [{ say: ['system', t.flavor || '(The lid fights, then gives.)'] },
      { run: () => {
        for (const gr of (t.grants || [])) Inventory.grant(gr[0], p.role, gr[1] || 1);
        AudioSys.chime();
        Particles.burst(10, () => ({
          kind: 'sparkle', x: t.x + (Math.random() - 0.5) * 50,
          y: t.y - 20 - Math.random() * 30, life: 1.1,
        }));
      } }];
    for (const l of (t.after || [])) steps.push({ say: l });
    Cutscene.play(steps);
  },

  // pickup: small find, announced like everything else
  pickupFlow(p, t) {
    if (Inventory.found(t.id)) return;
    const itemId = t.itemId || t.id;
    Dialog.start([{ who: 'system', text: t.flavor || '(Half-buried, but whole.)' }], () => {
      Inventory.markFound(t.id);
      Inventory.grant(itemId, p.role, t.n || 1);
      AudioSys.sparkle();
    });
  },

  // shop: stall patter (Dialog), then one question (the choice primitive).
  // A market stall is a conversation with one question in it (§1.3).
  shopFlow(p, t) {
    const openChoice = () => {
      const options = [];
      for (const s of (t.stock || []).slice(0, 2)) {
        const name = ITEMS[s.id].short.replace(/^(the|a) /, '');
        const label = `${name[0].toUpperCase() + name.slice(1)} — ${s.price} penn${s.price === 1 ? 'y' : 'ies'}`;
        const afford = Inventory.pennies(p.role) >= s.price;
        options.push({
          label: afford ? label : label + '  (short)',
          disabled: !afford,
          run: () => {
            Inventory.spendPennies(p.role, s.price);
            Inventory.grant(s.id, p.role);
            AudioSys.chime();
          },
        });
      }
      const sellable = (t.sell || []).find(s => Inventory.carriedBy(p.role).includes(s.id) &&
        ITEMS[s.id].cls !== 'story');
      if (sellable && options.length < 2) {
        options.push({
          label: `Sell ${ITEMS[sellable.id].short} — ${sellable.price} penn${sellable.price === 1 ? 'y' : 'ies'}`,
          run: () => {
            Inventory.spend(sellable.id, 1);
            Inventory.grant('penny', p.role, sellable.price, true);
            Toasts.add(`✦ sold — ${ITEMS[sellable.id].short} (+${sellable.price})`);
            AudioSys.chime();
          },
        });
      }
      options.push({ label: 'Not today' });
      Choice.start({
        prompt: t.prompt || 'What’ll it be?',
        options, player: p, canCancel: true,
        at: [t.x, t.y - 70],
      });
    };
    if (t.patter && t.patter.length)
      Dialog.start(t.patter.map(l => ({ who: l[0], text: l[1] })), openChoice);
    else openChoice();
  },

  // gift: giving happens in the world, via the A-prompt (§1.2)
  giftFlow(p, tc, w) {
    const key = tc.key, ent = tc.ent;
    const who = (typeof SPEAKERS !== 'undefined' && SPEAKERS[key]) ? SPEAKERS[key].name : key;
    Choice.start({
      prompt: `Give ${who} ${ITEMS[w.id].short}?`,
      options: [
        { label: 'Give it', run: () => {
          Inventory.give(w.id, key);
          AudioSys.sparkle();
          if (ent) Particles.burst(8, () => ({
            kind: 'sparkle', x: ent.x + (Math.random() - 0.5) * 34,
            y: ent.y - ent.h * 0.55 - Math.random() * 20, life: 1,
          }));
          if (!p.kb && p.connected) Net.to(p.id, { type: 'buzz', ms: 80 });
          if (w.onGift) w.onGift(p, tc);
        } },
        { label: 'Keep it' },
      ],
      player: p, canCancel: true,
      at: ent ? [ent.x, ent.y - ent.h - 20] : [p.x, p.y - p.h - 20],
    });
  },

  // place: nearest free mount within reach; several carried decor items
  // become one small question (max three options, per the choice rule)
  mountFlow(p, t) {
    if (t.items.length === 1) { Inventory.place(t.items[0], t.mount); AudioSys.sparkle(); return; }
    Choice.start({
      prompt: 'Set what here?',
      options: t.items.slice(0, 2).map(id => ({
        label: ITEMS[id].name,
        run: () => { Inventory.place(id, t.mount); AudioSys.sparkle(); },
      })).concat([{ label: 'Nothing' }]),
      player: p, canCancel: true,
      at: t.at,
    });
  },
};

/* ---------- dev test harness (documented in the H menu) ----------
   I — grant a test kit (items + pennies to both keepers)
   T — toggle a test chest, a test stall (buy/sell), and a gift-want
       on every NPC, spawned around P1's position in the current scene
   U — toggle a dev boat prop beside P1 with a test item on its rail */
const DevItems = {
  _n: 0, _boat: null,

  grantKit() {
    Inventory.grant('boat-hook', 'vesper', 1, true);
    Inventory.grant('sorrel-loaf', 'vesper', 1, true);
    Inventory.grant('penny', 'vesper', 6, true);
    Inventory.grant('striker', 'lake', 1, true);
    Inventory.grant('smoked-eel', 'lake', 1, true);
    Inventory.grant('wick-oil', 'lake', 2, true);
    Inventory.grant('penny', 'lake', 4, true);
    Toasts.add('⚙ test kit — hook/loaf/6p to Vesper · striker/eel/oil/4p to Lake', '#8fb0c9');
  },

  toggleThings(players) {
    if (ItemInteract.devThings.length) {
      ItemInteract.devThings = [];
      ItemInteract.stalls = ItemInteract.stalls.filter(s => !s.dev);
      ItemInteract.clearWant('*');
      Toasts.add('⚙ test treasure off', '#8fb0c9');
      return;
    }
    const p = players.find(q => q && !q.hidden && !q.parked);
    if (!p) return;
    const n = ++this._n;
    ItemInteract.devThings.push({
      kind: 'chest', id: 'dev-cache-' + n, scene: p.scene,
      x: p.x + 150, y: p.y, at: [p.x + 150, p.y - 40], r: 75,
      name: 'the test cache',
      flavor: '(A pine test-crate, stenciled DEV. The hinge fights, then gives.)',
      grants: [['striker', 1], ['wick-oil', 1]],
    });
    ItemInteract.devThings.push({
      kind: 'shop', id: 'dev-stall-' + n, scene: p.scene,
      x: p.x - 150, y: p.y, at: [p.x - 150, p.y - 40], r: 75,
      name: 'the test stall',
      patter: [['system', '(A trestle table under a tarp. Dev goods, honestly priced.)']],
      prompt: 'Smoked eel — fresh enough.',
      stock: [{ id: 'smoked-eel', price: 2 }],
      sell: [{ id: 'boat-hook', price: 2 }, { id: 'striker', price: 1 }],
    });
    ItemInteract.registerStall(p.scene, p.x - 150, p.y, 220, true);
    ItemInteract.setWant('*', 'sorrel-loaf', () => {
      Dialog.start([{ who: 'system', text: '(Accepted, with the particular dignity owed to test data.)' }]);
    });
    Toasts.add('⚙ test treasure ON — chest east · stall west · loaf gifts to anyone', '#8fb0c9');
  },

  toggleBoat(players) {
    if (this._boat) {
      const i = CurrentChapter.entities.indexOf(this._boat);
      if (i >= 0) CurrentChapter.entities.splice(i, 1);
      this._boat = null;
      Toasts.add('⚙ dev boat away', '#8fb0c9');
      return;
    }
    const p = players.find(q => q && !q.hidden && !q.parked);
    if (!p) return;
    this._boat = {
      key: 'devboat', char: 'boat-side', scene: p.scene,
      x: p.x + 60, y: p.y + 40, dir: 'right', moving: false, animT: 0, h: 280,
    };
    CurrentChapter.entities.push(this._boat);
    if (!Inventory.mountedAt('rail')) {
      if (!Inventory.has('striker')) Inventory.grant('striker', 'lake', 1, true);
      Inventory.place('striker', 'rail');
    }
    Toasts.add('⚙ dev boat moored — striker on the rail · walk the deck to re-place', '#8fb0c9');
  },
};
