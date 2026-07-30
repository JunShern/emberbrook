// menu.js — window.Menu: the pause menu (party / equip / items / save-load).
// ECONOMY-agent owned. Additive and self-contained: no-ops when the rules data
// is absent, and never touches play3d's internals.
//
// TWO HALVES, HARD LINE BETWEEN THEM (see docs/plans/economy-design.md):
//   OPS   pure operations over GS. compatible / statPreview / equipItem /
//         unequip / usable / useItem / partyView. No DOM, no keys, no timers.
//         tools/economy_test.mjs asserts these, so the tests exercise the code
//         the UI actually runs.
//   VIEW  a keyboard overlay (EBUI) driven by a small screen state machine.
//
// PARTY-OF-N BY CONSTRUCTION. Nothing here names a character or assumes a party
// size: every list of members is GS.activeParty(), every slot list is that
// character's own `equip` object, every stat comes from GS.stats/baseStats.
// Maren joining is `active` flipping in the save — she then appears in PARTY,
// in EQUIP's character step and in ITEMS' target step with no code change.
//
// PAUSING: EBUI takes UILOCK('menu'), the engine's modal-input contract — phys()
// freezes, and play3d's scene-graph and debug key handlers ignore input while the
// menu is up. Esc opens it (free key: play3d uses g/2/[/]/m/z, the scene graph
// uses e, the legibility overlay uses r; M is play3d's dev settings menu).
(function () {
  'use strict';

  const PANE_MAX = 3;        // party cards visible at once; past this the pane pages
  const SLOT_LABEL = { weapon: 'weapon', armor: 'armor' };   // display only; slots come from data
  const STATS = ['atk', 'def', 'spd'];

  // ==========================================================================
  // OPS — pure, headless, GS-only
  // ==========================================================================
  const GSok = () => !!(window.GS && window.GS.ok && window.GS.data);
  const chr = id => (GSok() ? window.GS.state.party.find(p => p.id === id) : null);
  const def = id => (GSok() ? window.GS.charDef(id) : null);
  const itemDef = id => (GSok() ? window.GS.itemDef(id) : null);

  // Everything a party display needs, derived — never stored.
  function partyView() {
    if (!GSok()) return [];
    return window.GS.activeParty().map(ch => {
      const s = window.GS.stats(ch), b = window.GS.baseStats(ch);
      const need = window.GS.xpToNext(ch.level);
      const gear = {};
      for (const slot of Object.keys(ch.equip)) {
        const it = ch.equip[slot] && itemDef(ch.equip[slot]);
        gear[slot] = { id: ch.equip[slot] || null, name: it ? it.name : null };
      }
      return {
        id: ch.id, name: (def(ch.id) || {}).name || ch.id, level: ch.level,
        hp: ch.hp, maxHp: s.maxHp, xp: ch.xp, xpNext: need,
        xpFrac: need > 0 ? ch.xp / need : 0,
        stats: s, base: b,
        mods: STATS.reduce((o, k) => (o[k] = (s[k] || 0) - (b[k] || 0), o), {}),
        gear,
      };
    });
  }

  const slotsOf = charId => { const ch = chr(charId); return ch ? Object.keys(ch.equip) : []; };

  // Items in the bag that fit a slot. Equipment currently worn is NOT here —
  // GS.equip took it out of the bag when it went on — which is exactly right.
  function compatible(charId, slot) {
    if (!GSok()) return [];
    const inv = window.GS.state.inventory || {};
    return Object.keys(inv).filter(id => { const it = itemDef(id); return it && it.slot === slot && inv[id] > 0; })
      .map(id => ({ id, def: itemDef(id), count: inv[id] }))
      .sort((a, b) => (a.def.price || 0) - (b.def.price || 0));
  }

  // What equipping (or, with itemId null + a slot, removing) would do — computed
  // on a GHOST character, so a preview can never mutate the save. GS.stats reads
  // only id/level/equip, so the ghost is a faithful subject.
  function statPreview(charId, itemId, slot) {
    const ch = chr(charId); if (!ch) return null;
    const it = itemId ? itemDef(itemId) : null;
    const sl = it ? it.slot : slot;
    if (!sl) return null;
    const ghost = { id: ch.id, level: ch.level, xp: ch.xp, hp: ch.hp, active: ch.active,
      equip: Object.assign({}, ch.equip, { [sl]: itemId || null }) };
    const before = window.GS.stats(ch), after = window.GS.stats(ghost);
    const delta = {};
    for (const k of ['hp', 'maxHp'].concat(STATS)) delta[k] = (after[k] || 0) - (before[k] || 0);
    return { slot: sl, before, after, delta, replacing: ch.equip[sl] || null };
  }

  function equipItem(charId, itemId) {
    if (!GSok()) return { ok: false, reason: 'nodata' };
    const it = itemDef(itemId);
    if (!it || !it.slot) return { ok: false, reason: 'noslot' };
    if (window.GS.count(itemId) < 1) return { ok: false, reason: 'none' };
    const pv = statPreview(charId, itemId);
    if (!window.GS.equip(charId, itemId)) return { ok: false, reason: 'refused' };
    return { ok: true, slot: it.slot, delta: pv ? pv.delta : null, replaced: pv ? pv.replacing : null };
  }
  function unequip(charId, slot) {
    if (!GSok()) return { ok: false, reason: 'nodata' };
    const ch = chr(charId); if (!ch) return { ok: false, reason: 'nochar' };
    if (!ch.equip[slot]) return { ok: false, reason: 'empty' };
    const was = ch.equip[slot], pv = statPreview(charId, null, slot);
    if (!window.GS.equip(charId, null, slot)) return { ok: false, reason: 'refused' };
    return { ok: true, slot, item: was, delta: pv ? pv.delta : null };
  }

  const usable = () => {
    if (!GSok()) return [];
    const inv = window.GS.state.inventory || {};
    return Object.keys(inv).filter(id => { const it = itemDef(id); return it && it.effect && inv[id] > 0; })
      .map(id => ({ id, def: itemDef(id), count: inv[id] }))
      .sort((a, b) => (a.def.price || 0) - (b.def.price || 0));
  };
  // Heal-clamp-consume lives in GS.useItem (granted); the menu only calls it, so
  // battle item use and menu item use can never diverge.
  function useItem(charId, itemId) {
    if (!GSok()) return { ok: false, reason: 'nodata' };
    return window.GS.useItem(charId, itemId);
  }

  // ==========================================================================
  // VIEW
  // ==========================================================================
  const U = () => window.EBUI;
  const ROOT = [
    { id: 'party', label: 'PARTY' }, { id: 'equip', label: 'EQUIP' },
    { id: 'items', label: 'ITEMS' }, { id: 'save', label: 'SAVE' },
    { id: 'load', label: 'LOAD' }, { id: 'newgame', label: 'NEW GAME' },
  ];
  let ui = null;   // {panel, screen, cur:{...}, sel:{char,slot,item}, page, msg, confirm}

  const cur = k => (ui.cur[k] = ui.cur[k] || 0);
  const setCur = (k, v) => { ui.cur[k] = v; };

  function card(p, compact) {
    const E = U();
    const gear = Object.keys(p.gear).map(s =>
      '<div class="ebui-stat"><span class="l">' + (SLOT_LABEL[s] || s) + '</span><span>' +
      E.esc(p.gear[s].name || '—') + '</span></div>').join('');
    const st = STATS.map(k => '<span>' + k + ' ' + (p.stats[k] || 0) +
      (p.mods[k] ? '<span class="ebui-up">(+' + p.mods[k] + ')</span>' : '') + '</span>').join(' ');
    return '<div class="ebui-card">' +
      '<div style="display:flex;gap:8px"><b>' + E.esc(p.name) + '</b>' +
      '<span class="n" style="margin-left:auto;font-family:ui-monospace,Menlo,monospace">Lv ' + p.level + '</span></div>' +
      '<div class="ebui-stat"><span class="l">HP</span><span>' + p.hp + '/' + p.maxHp + '</span></div>' +
      E.bar(p.hp / Math.max(1, p.maxHp)) +
      '<div class="ebui-stat"><span class="l">XP</span><span>' + p.xp + '/' + p.xpNext + '</span></div>' +
      E.bar(p.xpFrac) +
      '<div class="ebui-stat" style="gap:12px">' + st + '</div>' +
      (compact ? '' : gear) + '</div>';
  }

  function pane() {
    const ps = partyView();
    if (!ps.length) return '<div class="ebui-note">No party.</div>';
    const start = ui.page * PANE_MAX, shown = ps.slice(start, start + PANE_MAX);
    const more = ps.length > PANE_MAX
      ? '<div class="ebui-msg">party ' + (start + 1) + '-' + (start + shown.length) + ' of ' + ps.length + ' &middot; &larr;&rarr; page</div>'
      : '';
    return '<div class="ebui-cols" style="grid-template-columns:repeat(' + shown.length + ',minmax(0,1fr))">' +
      shown.map(p => card(p)).join('') + '</div>' + more;
  }

  function twoCol(left, right) {
    return '<div class="ebui-cols" style="grid-template-columns:11em minmax(0,1fr)">' +
      '<div>' + left + '</div><div>' + right + '</div></div>';
  }

  function listOf(items, key, fmt) {
    const E = U(), i0 = E.cursor(items.length, cur(key));
    setCur(key, i0);
    if (!items.length) return '<div class="ebui-note">—</div>';
    return items.map((it, i) => E.row(fmt(it, i), { cur: i === i0, dim: !!it._dim })).join('');
  }

  // ---- screens -------------------------------------------------------------
  function render() {
    if (!ui || !ui.panel) return;
    const E = U(), gold = window.GS.state.gold;
    let title = 'PAUSE', html = '', foot = '&uarr;&darr; move &middot; E/Enter select &middot; Esc/Q back';

    if (ui.confirm) {
      const c = ui.confirm, i = E.cursor(2, cur('confirm'));
      html = '<div class="ebui-note">' + E.esc(c.text) + '</div>' +
        ['Yes', 'No'].map((t, k) => E.row('<span class="k">' + t + '</span>', { cur: k === i })).join('');
      title = 'PAUSE — ' + c.title;
      foot = '&uarr;&darr; choose &middot; E/Enter confirm &middot; Esc/Q cancel';
    } else if (ui.screen === 'root') {
      html = twoCol(listOf(ROOT, 'root', r => '<span class="k">' + r.label + '</span>'), pane());
    } else if (ui.screen === 'party') {
      title = 'PAUSE — PARTY';
      const ps = partyView(), start = ui.page * PANE_MAX, shown = ps.slice(start, start + PANE_MAX);
      html = '<div class="ebui-cols" style="grid-template-columns:repeat(' + Math.max(1, shown.length) + ',minmax(0,1fr))">' +
        shown.map(p => card(p)).join('') + '</div>' +
        (ps.length > PANE_MAX ? '<div class="ebui-msg">&larr;&rarr; page ' + (ui.page + 1) + '/' + Math.ceil(ps.length / PANE_MAX) + '</div>' : '');
      foot = '&larr;&rarr; page &middot; Esc/Q back';
    } else if (ui.screen === 'equipChar' || ui.screen === 'itemChar') {
      const ps = partyView();
      const isItem = ui.screen === 'itemChar';
      // NB: panel titles are set with textContent — plain text only, no entities.
      title = 'PAUSE — ' + (isItem ? 'ITEMS › on whom?' : 'EQUIP › who?');
      const it = isItem && ui.sel.item ? itemDef(ui.sel.item) : null;
      const rows = ps.map(p => {
        const full = !!(it && it.effect && it.effect.heal && p.hp >= p.maxHp);
        return { p, _dim: full };
      });
      html = twoCol(listOf(rows, 'char', r =>
        '<span class="k">' + E.esc(r.p.name) + '</span><span class="n">Lv ' + r.p.level +
        '</span><span class="n" style="flex:0 0 6em">' + r.p.hp + '/' + r.p.maxHp + '</span>'), pane());
    } else if (ui.screen === 'equipSlot') {
      const p = partyView().find(x => x.id === ui.sel.char);
      title = 'PAUSE — EQUIP › ' + (p ? p.name : '');
      const slots = slotsOf(ui.sel.char).map(s => ({ s, name: p ? (p.gear[s].name || '—') : '—' }));
      html = twoCol(listOf(slots, 'slot', r =>
        '<span class="k">' + (SLOT_LABEL[r.s] || r.s) + '</span><span class="n" style="flex:0 0 auto">' +
        E.esc(r.name) + '</span>'), p ? card(p) : '');
    } else if (ui.screen === 'equipItem') {
      const p = partyView().find(x => x.id === ui.sel.char), slot = ui.sel.slot;
      title = 'PAUSE — EQUIP › ' + (p ? p.name : '') + ' › ' + (SLOT_LABEL[slot] || slot);
      const rows = compatible(ui.sel.char, slot).map(r => ({ kind: 'item', id: r.id, def: r.def, count: r.count }));
      if (p && p.gear[slot].id) rows.push({ kind: 'remove', id: null, def: { name: '— remove —' }, count: 0 });
      const i0 = E.cursor(rows.length, cur('eqitem')); setCur('eqitem', i0);
      const sel = rows[i0] || null;
      let list = rows.length
        ? rows.map((r, i) => E.row('<span class="k">' + E.esc(r.def.name) + '</span>' +
          (r.kind === 'item' ? '<span class="n">x' + r.count + '</span>' : ''), { cur: i === i0 })).join('')
        : '<div class="ebui-note">Nothing fits this slot.</div>';
      // live delta preview for the highlighted row, BEFORE anything is committed
      if (sel) {
        const pv = statPreview(ui.sel.char, sel.kind === 'item' ? sel.id : null, slot);
        if (pv) {
          list += '<div class="ebui-note">' + (sel.def.desc ? E.esc(sel.def.desc) + '<br>' : '') +
            STATS.concat(['maxHp']).filter(k => pv.delta[k]).map(k =>
              k + ' ' + (pv.before[k] || 0) + ' &rarr; ' + (pv.after[k] || 0) + E.delta(pv.delta[k])).join('&nbsp;&nbsp;') +
            (STATS.concat(['maxHp']).some(k => pv.delta[k]) ? '' : '<span class="ebui-msg">no stat change</span>') +
            '</div>';
        }
      }
      html = twoCol(list, p ? card(p) : '');
    } else if (ui.screen === 'itemPick') {
      title = 'PAUSE — ITEMS';
      const rows = usable();
      const i0 = E.cursor(rows.length, cur('item')); setCur('item', i0);
      const sel = rows[i0] || null;
      let list = rows.length
        ? rows.map((r, i) => E.row('<span class="k">' + E.esc(r.def.name) + '</span><span class="n">x' + r.count + '</span>',
          { cur: i === i0 })).join('')
        : '<div class="ebui-note">No usable items.</div>';
      if (sel) list += '<div class="ebui-note">' + E.esc(sel.def.desc || '') + '</div>';
      html = twoCol(list, pane());
    }

    if (ui.msg) html += '<div class="ebui-msg' + (ui.msgBad ? ' bad' : '') + '">' + E.esc(ui.msg) + '</div>';
    ui.panel.set({ title, sub: '', gold, html, foot });
  }

  function msg(t, bad) { ui.msg = t; ui.msgBad = !!bad; if (bad && ui.panel) ui.panel.shake(); render(); }
  const go = (screen, keepMsg) => { ui.screen = screen; if (!keepMsg) ui.msg = null; render(); };
  function ask(title, text, action, defaultNo) {
    ui.confirm = { title, text, action };
    setCur('confirm', defaultNo ? 1 : 0);
    render();
  }

  function pages() { return Math.max(1, Math.ceil(partyView().length / PANE_MAX)); }

  function onKey(a, ev) {
    if (ui.confirm) {
      const i = cur('confirm');
      if (a === 'up' || a === 'down') { setCur('confirm', (i + 1) % 2); return render(); }
      if (a === 'cancel') { ui.confirm = null; return render(); }
      if (a === 'confirm') {
        const c = ui.confirm; ui.confirm = null;
        if (i === 0) c.action(); else render();
        return;
      }
      return;
    }
    const step = ev && ev.shiftKey ? 5 : 1;

    if (ui.screen === 'root') {
      if (a === 'cancel') return close();
      if (a === 'up') { setCur('root', cur('root') - step); return render(); }
      if (a === 'down') { setCur('root', cur('root') + step); return render(); }
      if (a === 'left' || a === 'right') { ui.page = (ui.page + (a === 'left' ? pages() - 1 : 1)) % pages(); return render(); }
      if (a === 'confirm') return chooseRoot(ROOT[U().cursor(ROOT.length, cur('root'))].id);
      return;
    }
    if (ui.screen === 'party') {
      if (a === 'cancel') return go('root');
      if (a === 'left' || a === 'right') { ui.page = (ui.page + (a === 'left' ? pages() - 1 : 1)) % pages(); return render(); }
      return;
    }
    if (ui.screen === 'equipChar' || ui.screen === 'itemChar') {
      const ps = partyView();
      if (a === 'cancel') return go(ui.screen === 'itemChar' ? 'itemPick' : 'root');
      if (a === 'up') { setCur('char', cur('char') - 1); return render(); }
      if (a === 'down') { setCur('char', cur('char') + 1); return render(); }
      if (a === 'confirm') {
        const p = ps[U().cursor(ps.length, cur('char'))]; if (!p) return;
        if (ui.screen === 'equipChar') { ui.sel.char = p.id; setCur('slot', 0); return go('equipSlot'); }
        const r = useItem(p.id, ui.sel.item);
        if (!r.ok) return msg(r.reason === 'full' ? p.name + ' is unhurt.' : 'Cannot use that (' + r.reason + ').', true);
        const name = (itemDef(ui.sel.item) || {}).name || ui.sel.item;
        // the item may have been the last one: fall back to the list, which
        // re-derives from GS and will simply not contain it any more
        const left = window.GS.count(ui.sel.item);
        ui.screen = left > 0 ? 'itemChar' : 'itemPick';
        return msg(name + ' restored ' + r.healed + ' HP to ' + p.name + '.');
      }
      return;
    }
    if (ui.screen === 'equipSlot') {
      const slots = slotsOf(ui.sel.char);
      if (a === 'cancel') return go('equipChar');
      if (a === 'up') { setCur('slot', cur('slot') - 1); return render(); }
      if (a === 'down') { setCur('slot', cur('slot') + 1); return render(); }
      if (a === 'confirm') { ui.sel.slot = slots[U().cursor(slots.length, cur('slot'))]; setCur('eqitem', 0); return go('equipItem'); }
      return;
    }
    if (ui.screen === 'equipItem') {
      const rows = compatible(ui.sel.char, ui.sel.slot).map(r => ({ kind: 'item', id: r.id }));
      const p = partyView().find(x => x.id === ui.sel.char);
      if (p && p.gear[ui.sel.slot].id) rows.push({ kind: 'remove', id: null });
      if (a === 'cancel') return go('equipSlot');
      if (a === 'up') { setCur('eqitem', cur('eqitem') - 1); return render(); }
      if (a === 'down') { setCur('eqitem', cur('eqitem') + 1); return render(); }
      if (a === 'confirm') {
        const sel = rows[U().cursor(rows.length, cur('eqitem'))]; if (!sel) return;
        const r = sel.kind === 'item' ? equipItem(ui.sel.char, sel.id) : unequip(ui.sel.char, ui.sel.slot);
        if (!r.ok) return msg('Cannot do that (' + r.reason + ').', true);
        return msg(sel.kind === 'item'
          ? 'Equipped ' + (itemDef(sel.id) || {}).name + '.'
          : 'Removed ' + ((itemDef(r.item) || {}).name || 'gear') + '.');
      }
      return;
    }
    if (ui.screen === 'itemPick') {
      const rows = usable();
      if (a === 'cancel') return go('root');
      if (a === 'up') { setCur('item', cur('item') - 1); return render(); }
      if (a === 'down') { setCur('item', cur('item') + 1); return render(); }
      if (a === 'confirm') {
        const sel = rows[U().cursor(rows.length, cur('item'))]; if (!sel) return;
        ui.sel.item = sel.id; setCur('char', 0); return go('itemChar');
      }
      return;
    }
  }

  function chooseRoot(id) {
    if (id === 'party') { ui.page = 0; return go('party'); }
    if (id === 'equip') { setCur('char', 0); return go('equipChar'); }
    if (id === 'items') { setCur('item', 0); return go('itemPick'); }
    if (id === 'save') return ask('SAVE', 'Write the current game to this browser?', () => {
      const ok = window.GS.save(); msg(ok ? 'Game saved.' : 'Save failed.', !ok);
    });
    if (id === 'load') return ask('LOAD', 'Discard unsaved progress and load the last save?', () => {
      const ok = window.GS.load(); ui.page = 0; ui.cur = {}; msg(ok ? 'Game loaded.' : 'No save found.', !ok);
    }, true);
    if (id === 'newgame') return ask('NEW GAME', 'Erase the save and start over? This cannot be undone.', () => {
      window.GS.reset(); go('root'); msg('New game started.');
    }, true);
  }

  // ---- open / close --------------------------------------------------------
  function open() {
    if (!GSok()) { console.warn('[Menu] no rules data — open ignored'); return false; }
    if (!U() || !U().HAS_DOM) return false;
    if (ui) return false;
    if (U().locked) return false;                 // another modal owns the screen
    ui = { screen: 'root', cur: {}, sel: {}, page: 0, msg: null, confirm: null };
    ui.panel = U().panel({ name: 'menu', onKey, render, onClose() { ui = null; } });
    render();
    return true;
  }
  function close() { if (ui && ui.panel) ui.panel.close(); return true; }

  function register() {
    if (!GSok() || !U()) return false;
    // Esc opens the menu. EBUI suppresses global keys while any modal is up, so
    // Esc inside the shop closes the shop and never stacks a menu on top of it.
    U().onGlobalKey('escape', () => open());
    return true;
  }

  // ==========================================================================
  window.Menu = {
    open, close, register,
    // OPS (headless; what tools/economy_test.mjs asserts)
    partyView, slotsOf, compatible, statPreview, equipItem, unequip, usable, useItem,
    get isOpen() { return !!ui; },
    debug() { return { open: !!ui, screen: ui ? ui.screen : null, sel: ui ? ui.sel : null, page: ui ? ui.page : 0 }; },
  };

  if (window.GS && window.GS.ready && window.GS.ready.then) {
    window.GS.ready.then(() => { try { register(); } catch (e) { console.error('[Menu]', e); } });
  }
})();
