// game_state.js — THE game-state store (coordinator-owned).
// One serializable object holds everything that persists: party, inventory,
// gold, equipment, flags. Systems (battle/shop/menu/encounters) read and write
// ONLY through this API and never keep their own copies. GS.serialize() is the
// save format. Loads its rules data from public/game/*.json; every consumer
// must await GS.ready before touching it. No-ops safely if data files 404.
(function () {
  const DATA_FILES = { monsters: 'game/monsters.json', items: 'game/items.json',
    encounters: 'game/encounters.json', growth: 'game/growth.json', shops: 'game/shops.json' };
  const SAVE_KEY = 'emberbrook-save-v1';
  const listeners = {};

  const GS = window.GS = {
    data: null,          // rules data (read-only after load)
    state: null,         // the serializable save state
    ready: null,         // Promise — await before use
    ok: false,           // data loaded and state initialised

    on(ev, cb) { (listeners[ev] = listeners[ev] || []).push(cb); },
    emit(ev, arg) { (listeners[ev] || []).forEach(cb => { try { cb(arg); } catch (e) { console.error('[GS]', ev, e); } }); },

    // ---- lifecycle -------------------------------------------------------
    async init() {
      const data = {};
      try {
        for (const [k, url] of Object.entries(DATA_FILES)) {
          const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status);
          data[k] = await r.json();
        }
      } catch (e) { console.warn('[GS] rules data unavailable — game systems disabled:', e.message); return; }
      GS.data = data;
      if (!GS.load()) GS.newGame();
      GS.ok = true; GS.emit('ready', GS.state);
    },

    newGame() {
      const g = GS.data.growth;
      const party = Object.entries(g.characters).map(([id, c]) => ({
        id, active: !!c.active, level: 1, xp: 0,
        hp: c.base.hp, equip: Object.assign({ weapon: null, armor: null }, c.startEquip || {}),
      }));
      GS.state = { v: 1, party, gold: g.startGold || 0,
        inventory: Object.assign({}, g.startInventory || {}), flags: {} };
      // start equipment lives in equip slots, not inventory
      GS.emit('change', GS.state);
    },

    // ---- derived stats ---------------------------------------------------
    charDef(id) { return GS.data.growth.characters[id]; },
    baseStats(ch) {                    // level-scaled, before equipment
      const c = GS.charDef(ch.id), L = ch.level - 1, out = {};
      for (const k of ['hp', 'atk', 'def', 'spd']) out[k] = Math.floor(c.base[k] + c.growth[k] * L);
      return out;
    },
    stats(ch) {                        // with equipment statMods
      const s = GS.baseStats(ch);
      for (const slot of ['weapon', 'armor']) {
        const it = ch.equip[slot] && GS.data.items.items[ch.equip[slot]];
        if (it && it.statMods) for (const [k, v] of Object.entries(it.statMods)) s[k] = (s[k] || 0) + v;
      }
      s.maxHp = s.hp; return s;
    },
    activeParty() { return GS.state.party.filter(p => p.active); },

    // ---- xp / leveling ---------------------------------------------------
    xpToNext(level) { const c = GS.data.growth.curve; return Math.floor(c.k * level * level); },
    grantXp(amount) {                  // split across active members; returns level-up events
      const alive = GS.activeParty(), events = [];
      const share = Math.max(1, Math.floor(amount / Math.max(1, alive.length)));
      for (const ch of alive) {
        ch.xp += share;
        while (ch.xp >= GS.xpToNext(ch.level)) {
          ch.xp -= GS.xpToNext(ch.level); ch.level++;
          const s = GS.baseStats(ch); ch.hp = s.hp;   // level-up heals to new max
          events.push({ char: ch.id, level: ch.level });
        }
      }
      if (events.length) GS.emit('levelup', events);
      GS.emit('change', GS.state); return events;
    },

    // ---- inventory / gold ------------------------------------------------
    itemDef(id) { return GS.data.items.items[id]; },
    count(id) { return GS.state.inventory[id] || 0; },
    addItem(id, n) { n = n == null ? 1 : n; GS.state.inventory[id] = GS.count(id) + n;
      if (GS.state.inventory[id] <= 0) delete GS.state.inventory[id];
      GS.emit('change', GS.state); },
    removeItem(id, n) { if (GS.count(id) < (n == null ? 1 : n)) return false;
      GS.addItem(id, -(n == null ? 1 : n)); return true; },
    addGold(n) { GS.state.gold = Math.max(0, GS.state.gold + n); GS.emit('change', GS.state); },
    spendGold(n) { if (GS.state.gold < n) return false; GS.addGold(-n); return true; },

    // ---- equipment -------------------------------------------------------
    equip(charId, itemId) {            // itemId null = unequip slot back to bag
      const ch = GS.state.party.find(p => p.id === charId); if (!ch) return false;
      const it = itemId && GS.itemDef(itemId);
      if (itemId && (!it || !it.slot)) return false;
      if (itemId && !GS.removeItem(itemId)) return false;
      const slot = itemId ? it.slot : arguments[2];      // unequip needs explicit slot
      if (!slot) return false;
      if (ch.equip[slot]) GS.addItem(ch.equip[slot]);
      ch.equip[slot] = itemId || null;
      const s = GS.stats(ch); if (ch.hp > s.maxHp) ch.hp = s.maxHp;
      GS.emit('change', GS.state); return true;
    },

    // ---- battle boundary -------------------------------------------------
    applyBattleResult(res) {           // the ONLY way battles touch the world
      if (res.partyHp) for (const ch of GS.state.party) if (res.partyHp[ch.id] != null) ch.hp = res.partyHp[ch.id];
      if (res.outcome === 'victory') {
        if (res.gold) GS.addGold(res.gold);
        (res.drops || []).forEach(d => GS.addItem(d));
        if (res.xp) GS.grantXp(res.xp);
      }
      GS.emit('battle-applied', res); GS.emit('change', GS.state);
    },

    // ---- save / load -----------------------------------------------------
    serialize() { return JSON.stringify(GS.state); },
    save() { try { localStorage.setItem(SAVE_KEY, GS.serialize()); GS.emit('saved'); return true; }
      catch (e) { console.warn('[GS] save failed', e); return false; } },
    load() { try { const raw = localStorage.getItem(SAVE_KEY); if (!raw) return false;
      const st = JSON.parse(raw); if (st.v !== 1) return false; GS.state = st;
      GS.emit('change', GS.state); return true; } catch (e) { return false; } },
    reset() { localStorage.removeItem(SAVE_KEY); GS.newGame(); },
  };

  GS.ready = GS.init();
})();
