// shop.js — window.Shop: the buy/sell system for every shop in the game.
// ECONOMY-agent owned. Additive and self-contained: it no-ops silently in a
// scene that is not a shop, before its hooks land, and when the rules data is
// absent.
//
// TWO HALVES, HARD LINE BETWEEN THEM (see docs/plans/economy-design.md):
//   OPS   pure operations over GS + rules data. No DOM, no keys, no timers.
//         Everything tools/economy_test.mjs asserts lives here, so the tests
//         exercise the code the UI actually runs.
//   VIEW  a keyboard-driven overlay (EBUI) that calls OPS and re-renders from GS.
//
// NO COORDINATES, NO SHOP TABLE, NO KEEPER LABELS IN THIS FILE. Copying the rule
// play3d's scene-graph layer set for itself: adding a shop is a shops.json edit.
//   which shop is this scene?  -> the shops.json entry whose sceneKey === ?scene=
//   where is the counter?      -> the interior's own `walk_pad_counter` mesh
//                                 (every interior builder emits one)
//   what does the prompt say?  -> "Talk to the " + shops.json `keeper`
//   what does it look like?    -> the scene graph's own promptFmt/key/vTol
// A sceneKey that is not a real scene-graph node is REPORTED (console warn +
// Shop.debug().sceneKeyErrors), never silently adapted.
(function () {
  'use strict';

  const PAD = 'walk_pad_counter';   // the interaction-pad convention, emitted by
                                    // item_int_build.py / inn_int_build.py /
                                    // cookhouse_int_build.py ("interaction pads,
                                    // hidden from the beauty render")
  const PAD_MARGIN = 0.55;          // how far outside the pad box the prompt still offers
  const CIRCLE_R = 1.7;             // fallback radius when only a point is known
  const TICK_MS = 250;              // keepalive: rAF is throttled to nothing in a
                                    // background tab, and headless verification lives there

  // Anchor of last resort. These are the walk_pad_counter box centres read out of
  // the SHIPPED bundles, so they cannot disagree with what the player walks on —
  // but they are only used when SIM.pad() is unavailable (see resolveAnchor).
  // All three Dellhollow shops come off the same interior template, hence one value.
  // REGENERATE WITH:
  //   node -e "import('./tools/glb_read.mjs').then(({loadGlb})=>{for(const k of
  //     ['del-item-int','del-weapon-int','del-armor-int']){const G=loadGlb(
  //     'public/assets/scenes/'+k+'/scene.glb'),p=G.nodesNamed(/^walk_pad_counter/i)[0];
  //     console.log(k,G.nodeBox(p.i).center)}})"
  const COUNTER_FALLBACK = {
    'del-item-int':   [2.10, 0.04, 0.30],
    'del-weapon-int': [2.10, 0.04, 0.30],
    'del-armor-int':  [2.10, 0.04, 0.30],
  };

  // ==========================================================================
  // OPS — pure, headless, GS-only
  // ==========================================================================
  const GSok = () => !!(window.GS && window.GS.ok && window.GS.data);
  const shopsData = () => (GSok() && window.GS.data.shops) || null;
  const shopDef = id => { const s = shopsData(); return (s && s.shops && s.shops[id]) || null; };
  const itemDef = id => (GSok() ? window.GS.itemDef(id) : null);

  // Rate lookup goes through ONE accessor with a per-shop override already
  // honoured, so "this smith buys cheap" is a shops.json field tomorrow rather
  // than a code change.
  function rate(shopId, which) {
    const d = shopDef(shopId), s = shopsData();
    if (d && d.rates && d.rates[which] != null) return d.rates[which];
    if (s && s.rates && s.rates[which] != null) return s.rates[which];
    return which === 'sellRate' ? 0.5 : 1.0;
  }
  const money = (price, r) => Math.max(1, Math.round(price * r));

  function buyPrice(itemId, shopId) {
    const it = itemDef(itemId); if (!it || it.price == null) return null;
    return money(it.price, rate(shopId, 'buyRate'));
  }
  function sellPrice(itemId, shopId) {
    const it = itemDef(itemId); if (!it || it.price == null) return null;
    return money(it.price, rate(shopId, 'sellRate'));
  }

  // the shop that lives in a given scene key (the whole scene->shop mapping)
  function shopForScene(key) {
    const s = shopsData(); if (!s || !key) return null;
    for (const id of Object.keys(s.shops || {})) if (s.shops[id].sceneKey === key) return id;
    return null;
  }

  function stock(shopId) {
    const d = shopDef(shopId); if (!d) return [];
    return (d.stock || []).filter(id => !!itemDef(id)).map(id => ({
      id, def: itemDef(id), unit: buyPrice(id, shopId), have: window.GS.count(id),
    }));
  }

  // What the player may sell. Equipment sitting in a slot is NOT here and needs
  // no special case: GS.equip removes an item from the bag when it is equipped,
  // so a worn weapon simply is not in the inventory this reads. (Asserted in
  // tools/economy_test.mjs rather than trusted.)
  function sellable(shopId) {
    if (!GSok()) return [];
    const inv = window.GS.state.inventory || {};
    return Object.keys(inv).filter(id => {
      const it = itemDef(id);
      return it && it.price != null && !it.noSell && inv[id] > 0;
    }).map(id => ({
      id, def: itemDef(id), count: inv[id], unit: sellPrice(id, shopId),
    })).sort((a, b) => (a.def.type + a.def.name).localeCompare(b.def.type + b.def.name));
  }

  const maxAffordable = (shopId, itemId) => {
    const u = buyPrice(itemId, shopId); if (!u) return 0;
    return Math.floor(window.GS.state.gold / u);
  };

  function buy(shopId, itemId, qty) {
    qty = qty == null ? 1 : Math.floor(qty);
    if (!GSok()) return { ok: false, reason: 'nodata' };
    const d = shopDef(shopId); if (!d) return { ok: false, reason: 'noshop' };
    if (!itemDef(itemId)) return { ok: false, reason: 'noitem' };
    if ((d.stock || []).indexOf(itemId) < 0) return { ok: false, reason: 'nostock' };
    if (!(qty >= 1)) return { ok: false, reason: 'qty' };
    const unit = buyPrice(itemId, shopId), cost = unit * qty;
    if (!window.GS.spendGold(cost)) return { ok: false, reason: 'gold', cost };
    window.GS.addItem(itemId, qty);
    return { ok: true, qty, unit, spent: cost, gold: window.GS.state.gold };
  }

  function sell(itemId, qty, shopId) {
    qty = qty == null ? 1 : Math.floor(qty);
    if (!GSok()) return { ok: false, reason: 'nodata' };
    const it = itemDef(itemId); if (!it || it.price == null) return { ok: false, reason: 'noitem' };
    if (it.noSell) return { ok: false, reason: 'nosell' };
    if (!(qty >= 1)) return { ok: false, reason: 'qty' };
    const unit = sellPrice(itemId, shopId), gain = unit * qty;
    if (!window.GS.removeItem(itemId, qty)) return { ok: false, reason: 'none' };
    window.GS.addGold(gain);
    return { ok: true, qty, unit, earned: gain, gold: window.GS.state.gold };
  }

  // ==========================================================================
  // VIEW — keyboard overlay. Nothing below runs without a DOM.
  // ==========================================================================
  const U = () => window.EBUI;
  const TABS = ['BUY', 'SELL'];
  let ui = null;   // {panel, shopId, tab, cur:[0,0], mode:'list'|'qty', qty, msg}

  function statLine(def) {
    if (!def.statMods) return '';
    return Object.keys(def.statMods).map(k => k + ' ' + (def.statMods[k] > 0 ? '+' : '') + def.statMods[k]).join('  ');
  }

  function rows() { return ui.tab === 0 ? stock(ui.shopId) : sellable(ui.shopId); }

  function render() {
    if (!ui || !ui.panel) return;
    const E = U(), list = rows(), gold = window.GS.state.gold;
    ui.cur[ui.tab] = E.cursor(list.length, ui.cur[ui.tab]);
    const sel = list[ui.cur[ui.tab]] || null;

    const tabs = '<div class="ebui-tabs" style="padding:0 0 8px">' + TABS.map((t, i) =>
      '<span class="ebui-tab' + (i === ui.tab ? ' on' : '') + '">' + t + '</span>').join('') + '</div>';

    let body = '';
    if (!list.length) {
      body = '<div class="ebui-note">' + (ui.tab === 0 ? 'Nothing for sale.' : 'You have nothing to sell.') + '</div>';
    } else {
      body = list.map((r, i) => {
        const cur = i === ui.cur[ui.tab];
        const dim = ui.tab === 0 ? (r.unit > gold) : false;
        const right = ui.tab === 0
          ? '<span class="n">' + r.unit + ' g</span><span class="n" style="flex:0 0 5.5em;opacity:.7">have ' + r.have + '</span>'
          : '<span class="n">' + r.unit + ' g</span><span class="n" style="flex:0 0 5.5em;opacity:.7">x' + r.count + '</span>';
        return E.row('<span class="k">' + E.esc(r.def.name) + '</span>' + right, { cur, dim });
      }).join('');
    }

    let note = '';
    if (sel) {
      note = '<div class="ebui-note">' + E.esc(sel.def.desc || '') +
        (statLine(sel.def) ? '<br><span class="ebui-msg">' + statLine(sel.def) + '</span>' : '');
      if (ui.mode === 'qty') {
        const total = sel.unit * ui.qty;
        note += '<br>qty <b style="color:#e9a24b">&#8249; ' + ui.qty + ' &#8250;</b>' +
          '&nbsp;&nbsp;total <b>' + total + ' g</b>' +
          (ui.tab === 0 ? '&nbsp;&nbsp;&rarr; ' + (gold - total) + ' g left'
                        : '&nbsp;&nbsp;&rarr; ' + (gold + total) + ' g');
      }
      note += '</div>';
    }
    if (ui.msg) note += '<div class="ebui-msg' + (ui.msgBad ? ' bad' : '') + '">' + E.esc(ui.msg) + '</div>';

    const foot = ui.mode === 'qty'
      ? '&larr;&rarr; qty (shift x10) &middot; E/Enter ' + (ui.tab === 0 ? 'buy' : 'sell') + ' &middot; Esc/Q back'
      : '&uarr;&darr; pick &middot; &larr;&rarr; tab &middot; E/Enter choose &middot; Esc/Q leave';

    const d = shopDef(ui.shopId);
    ui.panel.set({
      title: d.name, sub: d.keeper ? '— ' + d.keeper : '', gold,
      html: tabs + '<div>' + body + note + '</div>',
      foot,
    });
  }

  function msg(text, bad) { ui.msg = text; ui.msgBad = !!bad; if (bad && ui.panel) ui.panel.shake(); render(); }

  function qtyMax(sel) {
    if (!sel) return 1;
    return ui.tab === 0
      ? Math.max(1, Math.min(99, maxAffordable(ui.shopId, sel.id)))
      : Math.max(1, Math.min(99, sel.count));
  }

  function onKey(a, ev) {
    const list = rows(), sel = list[ui.cur[ui.tab]] || null;
    const step = ev && ev.shiftKey ? 10 : 1;
    if (ui.mode === 'qty') {
      if (a === 'cancel') { ui.mode = 'list'; ui.msg = null; return render(); }
      if (a === 'left') { ui.qty = Math.max(1, ui.qty - step); return render(); }
      if (a === 'right') { ui.qty = Math.min(qtyMax(sel), ui.qty + step); return render(); }
      if (a === 'confirm') {
        if (!sel) return;
        const r = ui.tab === 0 ? buy(ui.shopId, sel.id, ui.qty) : sell(sel.id, ui.qty, ui.shopId);
        if (!r.ok) {
          msg(r.reason === 'gold' ? 'Not enough gold.' : 'Cannot do that (' + r.reason + ').', true);
          return;
        }
        ui.mode = 'list';
        msg(ui.tab === 0
          ? 'Bought ' + r.qty + ' ' + sel.def.name + ' for ' + r.spent + ' g.'
          : 'Sold ' + r.qty + ' ' + sel.def.name + ' for ' + r.earned + ' g.');
        return;
      }
      return;
    }
    // list mode
    if (a === 'cancel') return closeShop();
    if (a === 'up') { ui.cur[ui.tab] -= 1; ui.msg = null; return render(); }
    if (a === 'down') { ui.cur[ui.tab] += 1; ui.msg = null; return render(); }
    if (a === 'left' || a === 'right' || a === 'next') {
      ui.tab = (ui.tab + (a === 'left' ? TABS.length - 1 : 1)) % TABS.length;
      ui.msg = null; return render();
    }
    if (a === 'confirm') {
      if (!sel) return;
      if (ui.tab === 0 && sel.unit > window.GS.state.gold) return msg('Not enough gold.', true);
      ui.mode = 'qty'; ui.qty = 1; ui.msg = null; return render();
    }
  }

  function openShop(shopId) {
    if (!GSok()) { console.warn('[Shop] no rules data — openShop ignored'); return false; }
    if (!U() || !U().HAS_DOM) return false;
    if (ui) return false;                              // already open
    if (!shopDef(shopId)) { console.warn('[Shop] unknown shop "' + shopId + '"'); return false; }
    ui = { shopId, tab: 0, cur: [0, 0], mode: 'list', qty: 1, msg: null };
    near = false; U().prompt('shop', null);             // the counter prompt steps aside
    // name:'shop' takes UILOCK('shop') — the engine freezes phys() and the
    // scene-graph/debug key handlers for as long as this panel lives. On close the
    // player is still at the counter, so the prompt simply comes back next tick.
    ui.panel = U().panel({ name: 'shop', onKey, render, onClose() { ui = null; } });
    render();
    return true;
  }
  function closeShop() { if (ui && ui.panel) ui.panel.close(); return true; }

  // ==========================================================================
  // THE COUNTER PROMPT — arming mirrors play3d's sgTick exactly
  // ==========================================================================
  let sceneKey = null, myShop = null, anchor = null, armed = null, near = false;
  let driving = false, sceneKeyErrors = [];

  function scene() {
    try { return new URLSearchParams(location.search).get('scene') || 'dellhollow3d'; }
    catch (e) { return null; }
  }

  // 1. SIM.pad hook (zero coordinates here) > 2. shops.json `counter` >
  // 3. the GLB-derived fallback table. Re-tried each tick until it resolves,
  // because the GLB may still be loading when we first look.
  function resolveAnchor() {
    if (anchor) return anchor;
    const d = shopDef(myShop); if (!d) return null;
    try {
      if (window.SIM && window.SIM.pad) {
        const p = window.SIM.pad(PAD);
        if (p && p.center) return (anchor = { src: 'SIM.pad', at: p.center, min: p.min, max: p.max });
      }
    } catch (e) { /* SIM.pad is optional */ }
    if (d.counter && d.counter.length === 3) return (anchor = { src: 'shops.json', at: d.counter });
    const f = COUNTER_FALLBACK[d.sceneKey];
    if (f) return (anchor = { src: 'fallback', at: f });
    return null;
  }

  // Box test when the pad's extents are known (a 1.7x1.0m counter pad is not a
  // circle — the same reason the scene graph gave camera boundaries bands),
  // circle otherwise. |dy| <= the graph's own vTol.
  function hit(pos) {
    const a = anchor; if (!a || !pos) return { in: false, d: Infinity };
    const vt = U() ? U().sgDef('vTol') : 2;
    const dy = Math.abs(pos.y - a.at[1]);
    if (a.min && a.max) {
      const dx = Math.max(a.min[0] - PAD_MARGIN - pos.x, 0, pos.x - (a.max[0] + PAD_MARGIN));
      const dz = Math.max(a.min[2] - PAD_MARGIN - pos.z, 0, pos.z - (a.max[2] + PAD_MARGIN));
      const d = Math.hypot(dx, dz);
      return { d, dy, in: d <= 0.0001 && dy <= vt };
    }
    const d = Math.hypot(pos.x - a.at[0], pos.z - a.at[2]);
    return { d, dy, in: d <= CIRCLE_R && dy <= vt };
  }

  // One tick of the prompt state machine. Public and idempotent so a test — or a
  // future phys() hook — can drive it by hand instead of waiting for rAF.
  function tick() {
    if (!myShop || !GSok()) return null;
    if (!resolveAnchor()) return null;
    let pos = null;
    try { pos = window.SIM && window.SIM.pos && window.SIM.pos(); } catch (e) { }
    if (!pos) return null;
    const h = hit(pos);
    // ARRIVAL SUPPRESSION, exactly as sgTick does it: a region that already
    // contains you when you arrive starts DISARMED and arms when you step out.
    if (armed === null) { armed = !h.in; near = false; if (U()) U().prompt('shop', null); return h; }
    if (!h.in) { armed = true; if (near) { near = false; if (U()) U().prompt('shop', null); } return h; }
    // no prompt while ANY modal is up (our panel, the pause menu, a battle)
    if (!armed || (U() && U().locked)) return h;
    if (!near) {
      near = true;
      const d = shopDef(myShop);
      const label = d.keeper ? 'Talk to the ' + d.keeper : 'Shop';
      if (U()) U().prompt('shop', label, U().sgDef('key'));
    }
    return h;
  }

  function drive() {
    if (driving || !U() || !U().HAS_DOM) return;
    driving = true;
    const raf = () => { tick(); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
    setInterval(tick, TICK_MS);      // keepalive for background tabs (rAF stops there)
  }

  // Reported, never silently adapted: a shops.json sceneKey that is not a real
  // scene-graph node means the data and the world disagree.
  function auditSceneKeys() {
    const s = shopsData(); if (!s) return;
    let nodes = null;
    try { const g = window.SIM && window.SIM.graph && window.SIM.graph(); if (g && g.nodes) nodes = g.nodes; }
    catch (e) { }
    if (!nodes) return;                            // graph not loaded yet; re-audited on the next call
    sceneKeyErrors = Object.keys(s.shops || {}).filter(id => nodes.indexOf(s.shops[id].sceneKey) < 0)
      .map(id => id + ' -> ' + s.shops[id].sceneKey);
    if (sceneKeyErrors.length) {
      console.warn('[Shop] shops.json sceneKey values with no scene-graph node: ' +
        sceneKeyErrors.join(', ') + ' — reporting, not adapting.');
    }
  }

  function registerPrompts() {
    if (!GSok()) return false;
    sceneKey = scene();
    auditSceneKeys();
    myShop = shopForScene(sceneKey);
    if (!myShop) return false;                     // not a shop interior: silent no-op
    armed = null; near = false; anchor = null;
    if (U()) {
      // E at the counter. Suppressed by EBUI while any panel is open, so this can
      // never fight a panel's own keys — and returning false leaves the keystroke
      // to play3d (the door prompt) when we are not offering anything.
      U().onGlobalKey(U().sgDef('key'), () => {
        if (!near || !armed) return false;
        return openShop(myShop);
      });
    }
    drive();
    return true;
  }

  // ==========================================================================
  window.Shop = {
    // integration surface
    openShop, closeShop, registerPrompts, tick,
    // OPS (headless; what tools/economy_test.mjs asserts)
    shopForScene, shopDef, stock, sellable, buyPrice, sellPrice, rate, maxAffordable, buy, sell,
    // debug/test
    get isOpen() { return !!ui; },
    debug() {
      return {
        scene: sceneKey, shop: myShop, anchor, armed, near, open: !!ui,
        tab: ui ? ui.tab : null, mode: ui ? ui.mode : null, qty: ui ? ui.qty : null,
        sceneKeyErrors,
      };
    },
  };

  // Self-arming: the module is additive, so it registers itself as soon as the
  // store is ready. A coordinator hook that calls Shop.registerPrompts() again is
  // harmless (idempotent), and this works with no hook at all.
  if (window.GS && window.GS.ready && window.GS.ready.then) {
    window.GS.ready.then(() => { try { registerPrompts(); } catch (e) { console.error('[Shop]', e); } });
  }
})();
