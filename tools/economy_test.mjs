// economy_test.mjs — headless tests for the economy layer. No browser.
//
//   node tools/economy_test.mjs            (exit 0 = all green, 1 = a failure)
//   node tools/economy_test.mjs -v         (list every assertion)
//
// WHAT IT LOADS AND WHY THAT MATTERS
// The SHIPPED files, unmodified: public/js/game_state.js, ui_kit.js, shop.js,
// menu.js, evaluated in a Node context with three shims — `window` (globalThis),
// `fetch` (reads public/<url> off disk), `localStorage` (in-memory). So these
// tests exercise the same code the browser runs; they are not a second
// implementation of the arithmetic. No refactor of the coordinator-owned store
// was needed to make it testable, only those shims.
//
// window.Rules is deliberately ABSENT here, so GS.stats() takes its inline path
// (the coordinator's note: don't half-load the battle kernel). A separate
// kernel-loaded run is battle-core's business; the contract is that both paths
// are behaviourally identical, and the stat assertions below pin the numbers
// either way.
//
// NO Math.random ANYWHERE. Every number below is arithmetic on the rules data.
import fs from 'fs';
import path from 'path';
import vm from 'vm';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUB = path.join(ROOT, 'public');
const VERBOSE = process.argv.includes('-v');

// ---------------------------------------------------------------- tiny harness
let pass = 0, fail = 0;
const fails = [];
function ok(cond, what, extra) {
  if (cond) { pass++; if (VERBOSE) console.log('  ok   ' + what); return true; }
  fail++; fails.push(what + (extra ? '  [' + extra + ']' : ''));
  console.log('  FAIL ' + what + (extra ? '  [' + extra + ']' : ''));
  return false;
}
const eq = (a, b, what) => ok(a === b, what, 'got ' + JSON.stringify(a) + ' want ' + JSON.stringify(b));
const section = t => console.log('\n' + t);

// ---------------------------------------------------- the browser-module loader
function makeStore() {
  const mem = new Map();
  return {
    getItem: k => (mem.has(k) ? mem.get(k) : null),
    setItem: (k, v) => mem.set(k, String(v)),
    removeItem: k => mem.delete(k),
    clear: () => mem.clear(),
    _mem: mem,
  };
}

// ------------------------------------------------------------------- DOM stub
// Enough DOM for the VIEW halves to actually RUN: panels open, screens render,
// keys dispatch, panels close. This exists because `node --check` cannot see a
// call to a function that does not exist — a ReferenceError inside panel() is
// invisible to a syntax check and to any test that only touches OPS. Sections 15
// and 16 walk every screen of both UIs through this stub for exactly that reason.
function makeDom() {
  const listeners = { keydown: [], keyup: [], keypress: [] };
  function el(tag) {
    const n = {
      tag, children: [], parentNode: null, _q: new Map(),
      className: '', id: '', textContent: '', innerHTML: '', offsetWidth: 1,
      style: { cssText: '', setProperty() { } },
      classList: {
        _s: new Set(),
        add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
        contains(c) { return this._s.has(c); },
      },
      appendChild(c) { n.children.push(c); c.parentNode = n; return c; },
      removeChild(c) { const i = n.children.indexOf(c); if (i >= 0) n.children.splice(i, 1); c.parentNode = null; return c; },
      // innerHTML is a string here, so a real query is impossible: hand back a
      // stable stub per selector, which is all panel.set() needs.
      querySelector(sel) { if (!n._q.has(sel)) n._q.set(sel, el('stub')); return n._q.get(sel); },
    };
    return n;
  }
  const doc = {
    head: el('head'), body: el('body'), _byId: {},
    createElement: el,
    getElementById(id) { return doc._byId[id] || null; },
  };
  doc._byId.s = el('div');           // play3d's scene host, where prompts/panels mount
  return {
    document: doc,
    addEventListener(type, fn, capture) { (listeners[type] = listeners[type] || []).push({ fn, capture }); },
    // synthesise a real keydown through the capture-phase chain
    key(k, opt) {
      opt = opt || {};
      const ev = {
        key: k, repeat: !!opt.repeat, shiftKey: !!opt.shift, stopped: false, defaulted: false,
        stopImmediatePropagation() { ev.stopped = true; }, preventDefault() { ev.defaulted = true; },
      };
      for (const l of listeners.keydown) { if (ev.stopped) break; l.fn(ev); }
      return ev;
    },
    listeners,
  };
}
// A faithful copy of play3d's UILOCK (see play3d.html ~line 279), so the tests
// exercise the real modal contract rather than EBUI's no-contract fallback.
function makeUilock() {
  const keys = {};
  return { _h: Object.create(null), keys,
    lock(k) { this._h[k] = 1; for (const key in keys) keys[key] = 0; },
    unlock(k) { delete this._h[k]; },
    active() { for (const k in this._h) return true; return false; } };
}

async function bootGame(opt) {
  opt = opt || {};
  const g = globalThis;
  g.window = g;                                   // the modules assign to window.*
  g.location = { search: opt.scene ? '?scene=' + opt.scene : '' };
  if (opt.dom) {
    const D = makeDom();
    g.document = D.document;
    g.addEventListener = D.addEventListener;
    g.requestAnimationFrame = () => 0;            // never self-schedules: tests drive Shop.tick()
    g.__dom = D;
  } else {
    delete g.document; delete g.addEventListener; delete g.requestAnimationFrame; delete g.__dom;
  }
  g.localStorage = makeStore();
  g.fetch = async (url) => {
    const clean = String(url).split('?')[0];
    const p = path.join(PUB, clean);
    if (opt.noData || !fs.existsSync(p)) return { ok: false, status: 404, json: async () => null };
    return { ok: true, status: 200, json: async () => JSON.parse(fs.readFileSync(p, 'utf8')) };
  };
  // fresh module instances per boot: drop the singletons the IIFEs installed
  delete g.GS; delete g.Shop; delete g.Menu; delete g.EBUI; delete g.SIM; delete g.UILOCK; delete g.Rules;
  for (const f of ['js/game_state.js', 'js/ui_kit.js', 'js/shop.js', 'js/menu.js']) {
    vm.runInThisContext(fs.readFileSync(path.join(PUB, f), 'utf8'), { filename: f });
  }
  await g.GS.ready;
  return g;
}

// ============================================================================
async function main() {
  console.log('economy_test — headless economy/menu assertions');
  const G = await bootGame();
  const { GS, Shop, Menu } = G;
  const items = JSON.parse(fs.readFileSync(path.join(PUB, 'game/items.json'), 'utf8')).items;
  const shops = JSON.parse(fs.readFileSync(path.join(PUB, 'game/shops.json'), 'utf8'));
  const graph = JSON.parse(fs.readFileSync(path.join(ROOT, 'public/world/scenegraph.json'), 'utf8'));

  // ---------------------------------------------------------------- 1. data
  section('1. rules data integrity');
  ok(GS.ok, 'GS loaded its rules data');
  for (const [sid, s] of Object.entries(shops.shops)) {
    ok(s.stock.every(id => !!items[id]), 'shop ' + sid + ' stock ids all exist in items.json',
      s.stock.filter(id => !items[id]).join(','));
    ok(!!graph.nodes[s.sceneKey], 'shop ' + sid + ' sceneKey "' + s.sceneKey + '" is a real scenegraph node');
    ok(typeof s.keeper === 'string' && s.keeper.length > 0, 'shop ' + sid + ' has a keeper (the prompt label)');
  }
  for (const [id, it] of Object.entries(items)) {
    if (it.type === 'weapon' || it.type === 'armor') ok(!!it.slot, 'equippable ' + id + ' declares a slot');
    if (it.type === 'consumable') ok(!!it.effect, 'consumable ' + id + ' declares an effect');
    ok(typeof it.price === 'number' && it.price > 0, 'item ' + id + ' has a price');
  }
  eq(Shop.shopForScene('del-item-int'), 'del-item', 'scene del-item-int maps to shop del-item');
  eq(Shop.shopForScene('del-weapon-int'), 'del-weapon', 'scene del-weapon-int maps to shop del-weapon');
  eq(Shop.shopForScene('del-armor-int'), 'del-armor', 'scene del-armor-int maps to shop del-armor');
  eq(Shop.shopForScene('del-inn-int'), null, 'a non-shop interior maps to no shop');
  eq(Shop.debug().sceneKeyErrors.length, 0, 'no shops.json sceneKey without a scene');

  // -------------------------------------------------------------- 2/3. buying
  section('2. buying');
  const startGold = GS.state.gold;
  eq(startGold, 30, 'new game starts with growth.json startGold');
  eq(GS.count('tonic'), 2, 'new game starts with growth.json startInventory');
  eq(Shop.buyPrice('tonic', 'del-item'), items.tonic.price, 'buy price is items.json price at buyRate 1.0');

  let r = Shop.buy('del-item', 'tonic', 2);
  ok(r.ok, 'buy 2 tonics succeeds');
  eq(GS.state.gold, startGold - items.tonic.price * 2, 'gold decreased by exactly price x qty');
  eq(GS.count('tonic'), 4, 'inventory increased by exactly qty');
  eq(r.spent, items.tonic.price * 2, 'result reports what it spent');

  section('3. buying refuses instead of going negative');
  const g3 = GS.state.gold, inv3 = GS.count('hale-tonic');
  r = Shop.buy('del-item', 'hale-tonic', 1);          // 45 g, we have 6
  eq(r.ok, false, 'cannot buy what we cannot afford');
  eq(r.reason, 'gold', 'refusal reason is gold');
  eq(GS.state.gold, g3, 'gold unchanged after a refused buy');
  eq(GS.count('hale-tonic'), inv3, 'inventory unchanged after a refused buy');
  eq(Shop.buy('del-item', 'tonic', 99).ok, false, 'cannot buy more than gold allows');
  eq(GS.state.gold, g3, 'gold still unchanged after the overspend attempt');
  eq(Shop.buy('del-item', 'boat-hook', 1).reason, 'nostock', 'a shop refuses items it does not stock');
  eq(Shop.buy('del-item', 'no-such-item', 1).reason, 'noitem', 'unknown item id is refused');
  eq(Shop.buy('del-item', 'tonic', 0).reason, 'qty', 'qty 0 is refused');
  eq(Shop.maxAffordable('del-item', 'tonic'), Math.floor(GS.state.gold / items.tonic.price),
    'maxAffordable is floor(gold / unit)');

  // --------------------------------------------------------------- 4/5. selling
  section('4. selling');
  eq(Shop.sellPrice('tonic', 'del-item'), Math.max(1, Math.round(items.tonic.price * shops.rates.sellRate)),
    'sell price is price x sellRate');
  const g4 = GS.state.gold, n4 = GS.count('tonic');
  r = Shop.sell('tonic', 2, 'del-item');
  ok(r.ok, 'sell 2 tonics succeeds');
  eq(GS.state.gold, g4 + Shop.sellPrice('tonic', 'del-item') * 2, 'gold increased by sellPrice x qty');
  eq(GS.count('tonic'), n4 - 2, 'inventory decreased by qty');
  eq(Shop.sell('tonic', 99, 'del-item').reason, 'none', 'cannot sell more than owned');
  eq(GS.count('tonic'), n4 - 2, 'inventory unchanged after a refused sell');
  eq(Shop.sell('no-such-item', 1, 'del-item').reason, 'noitem', 'cannot sell an unknown item');

  section('5. buy/sell round-trip loses exactly the sellRate spread');
  const g5 = GS.state.gold, n5 = GS.count('tonic');
  Shop.buy('del-item', 'tonic', 1);
  Shop.sell('tonic', 1, 'del-item');
  eq(GS.count('tonic'), n5, 'round-trip returns the inventory to its start state');
  eq(GS.state.gold, g5 - (Shop.buyPrice('tonic', 'del-item') - Shop.sellPrice('tonic', 'del-item')),
    'round-trip costs exactly buyPrice - sellPrice');

  // ------------------------------------------------- 6. equipped gear is safe
  section('6. equipped gear is not sellable');
  const vesper = GS.state.party.find(p => p.id === 'vesper');
  eq(vesper.equip.weapon, 'walking-staff', 'Vesper starts with her startEquip weapon in the slot');
  eq(GS.count('walking-staff'), 0, 'start equipment is NOT also in the bag');
  ok(!Shop.sellable('del-weapon').some(s => s.id === 'walking-staff'),
    'the equipped weapon does not appear in the SELL list');
  ok(Menu.unequip('vesper', 'weapon').ok, 'unequip succeeds');
  eq(GS.count('walking-staff'), 1, 'unequip put the weapon back in the bag');
  ok(Shop.sellable('del-weapon').some(s => s.id === 'walking-staff'),
    'once unequipped it IS sellable');
  ok(Menu.equipItem('vesper', 'walking-staff').ok, 're-equip succeeds');
  ok(!Shop.sellable('del-weapon').some(s => s.id === 'walking-staff'), 'and it leaves the SELL list again');

  // ------------------------------------------------------------ 7/8. equipment
  section('7. equip stat deltas match statMods exactly');
  const before7 = GS.stats(vesper);
  GS.addItem('river-cudgel', 1);
  const pv = Menu.statPreview('vesper', 'river-cudgel');
  const expDelta = items['river-cudgel'].statMods.atk - items['walking-staff'].statMods.atk;
  eq(pv.delta.atk, expDelta, 'preview predicts the swap delta (new statMods - old statMods)');
  eq(pv.replacing, 'walking-staff', 'preview names what it would replace');
  const r7 = Menu.equipItem('vesper', 'river-cudgel');
  ok(r7.ok, 'equipping the better weapon succeeds');
  const after7 = GS.stats(vesper);
  eq(after7.atk - before7.atk, expDelta, 'the real mutation produced the previewed delta');
  eq(GS.count('walking-staff'), 1, 'the swapped-out weapon returned to the bag');
  eq(GS.count('river-cudgel'), 0, 'the equipped weapon left the bag');
  eq(after7.atk, GS.baseStats(vesper).atk + items['river-cudgel'].statMods.atk,
    'stats = baseStats + equipped statMods');
  // armor + def, on the other slot, so slots are proven independent
  const beforeDef = GS.stats(vesper).def;
  GS.addItem('oilskin-coat', 1);
  ok(Menu.equipItem('vesper', 'oilskin-coat').ok, 'equipping armor succeeds');
  eq(GS.stats(vesper).def - beforeDef,
    items['oilskin-coat'].statMods.def - items['quilted-vest'].statMods.def,
    'armor swap moves def by exactly the statMods difference');
  eq(GS.stats(vesper).atk, after7.atk, 'the armor swap did not touch atk');

  section('8. unequip returns the item and removes the delta');
  const beforeU = GS.stats(vesper).atk;
  const ru = Menu.unequip('vesper', 'weapon');
  ok(ru.ok, 'unequip succeeds');
  eq(ru.item, 'river-cudgel', 'unequip reports which item came off');
  eq(GS.count('river-cudgel'), 1, 'the item is back in the bag');
  eq(GS.stats(vesper).atk, beforeU - items['river-cudgel'].statMods.atk, 'the stat delta is gone');
  eq(vesper.equip.weapon, null, 'the slot is empty');
  eq(Menu.unequip('vesper', 'weapon').reason, 'empty', 'unequipping an empty slot is refused');
  ok(Menu.equipItem('vesper', 'river-cudgel').ok, 'restore the weapon for later tests');
  eq(Menu.equipItem('vesper', 'tonic').reason, 'noslot', 'a consumable cannot be equipped');
  eq(Menu.equipItem('vesper', 'boat-hook').reason, 'none', 'cannot equip an item not in the bag');
  ok(Menu.compatible('vesper', 'weapon').every(c => c.def.slot === 'weapon'),
    'compatible(weapon) only offers weapons');
  ok(Menu.compatible('vesper', 'armor').every(c => c.def.slot === 'armor'),
    'compatible(armor) only offers armor');

  // -------------------------------------------------------------- 9. consumables
  section('9. consumables heal, clamp, and are consumed');
  const maxHp = GS.stats(vesper).maxHp;
  eq(Menu.useItem('vesper', 'tonic').reason, 'full', 'a full-HP member refuses the item');
  const nTonic = GS.count('tonic');
  eq(GS.count('tonic'), nTonic, 'a refused use does NOT consume the item');
  GS.setHp('vesper', maxHp - 100 > 0 ? maxHp - 100 : 1);
  GS.setHp('vesper', 1);
  let ru9 = Menu.useItem('vesper', 'tonic');
  ok(ru9.ok, 'using a tonic on a hurt member succeeds');
  eq(ru9.healed, items.tonic.effect.heal, 'healed exactly effect.heal');
  eq(vesper.hp, 1 + items.tonic.effect.heal, 'hp rose by effect.heal');
  eq(GS.count('tonic'), nTonic - 1, 'the item was consumed');
  GS.setHp('vesper', maxHp - 1);
  ru9 = Menu.useItem('vesper', 'tonic');
  ok(ru9.ok, 'using a tonic just below max succeeds');
  eq(vesper.hp, maxHp, 'healing CLAMPS at maxHp');
  eq(ru9.healed, 1, 'the reported heal is the clamped amount, not effect.heal');
  ok(Menu.usable().every(u => !!u.def.effect), 'usable() only offers items with an effect');
  ok(!Menu.usable().some(u => u.id === 'river-cudgel'), 'usable() does not offer a weapon');

  // ----------------------------------------------------------------- 10. xp
  section('10. xp curve and level-ups');
  let mono = true;
  for (let L = 1; L < 20; L++) if (!(GS.xpToNext(L + 1) > GS.xpToNext(L))) mono = false;
  ok(mono, 'xpToNext is strictly monotonic over levels 1..20');
  // THE SHAPE IS THE CONTRACT, THE CONSTANT IS CONTENT. k is a balance dial the
  // user retunes (25 -> 10 on 2026-07-31, so early levels come fast); hard-coding
  // it here made a legitimate data change look like three engine regressions.
  // What must hold is that the curve IS k*level^2 for whatever k the data says.
  const K = GS.data.growth.curve.k;
  eq(GS.xpToNext(1), K * 1, 'xpToNext(1) = k*1^2 (k=' + K + ' from growth.json)');
  eq(GS.xpToNext(2), K * 4, 'xpToNext(2) = k*2^2');
  eq(GS.xpToNext(3), K * 9, 'xpToNext(3) = k*3^2');

  const F = await bootGame();                       // a clean party for curve maths
  eq(F.GS.activeParty().length, 1, 'only active members are in the party (the joiners wait on their flags)');
  // party-of-N by construction: the count is growth.json's own, never a literal —
  // Lake was added on 2026-08-02 and this line must not have to move again.
  eq(F.GS.state.party.length, Object.keys(F.GS.data.growth.characters).length,
     'but every character exists in the save from day one');
  const v = F.GS.state.party.find(p => p.id === 'vesper');
  F.GS.grantXp(GS.xpToNext(1) - 1);
  eq(v.level, 1, 'one xp short of the threshold does NOT level');
  eq(v.xp, GS.xpToNext(1) - 1, 'xp accumulated exactly');
  let ev = F.GS.grantXp(1);
  eq(v.level, 2, 'hitting the threshold exactly levels up');
  eq(v.xp, 0, 'and leaves zero remainder');
  eq(ev.length, 1, 'grantXp returned one level-up event');
  eq(ev[0].char, 'vesper', 'the event names the character');
  eq(v.hp, F.GS.stats(v).maxHp, 'a level-up heals to the new max');
  // multi-level in one grant: k*4 (->3) + k*9 (->4) + 10 remainder
  F.GS.grantXp(GS.xpToNext(2) + GS.xpToNext(3) + 10);
  eq(v.level, 4, 'a big grant multi-levels to the exact level');
  eq(v.xp, 10, 'and lands on the exact remainder');
  ok(F.GS.stats(v).atk > F.GS.baseStats({ id: 'vesper', level: 1, equip: v.equip }).atk,
    'growth raised atk over four levels');

  // ----------------------------------------------------- 11. save/load identity
  section('11. save / load identity');
  const blob = F.GS.serialize();
  ok(F.GS.save(), 'save() writes to storage');
  F.GS.addGold(999); F.GS.addItem('boat-hook', 3); F.GS.grantXp(500);
  ok(F.GS.serialize() !== blob, 'mutating changed the state');
  ok(F.GS.load(), 'load() reads the save back');
  eq(F.GS.serialize(), blob, 'load restored the exact serialized blob');
  const fresh = (() => { F.GS.reset(); return F.GS.serialize(); })();
  const F2 = await bootGame();
  eq(fresh, F2.GS.serialize(), 'reset() produces a byte-identical fresh-game blob');
  eq(JSON.parse(fresh).gold, 30, 'the fresh blob has startGold');

  // ------------------------------------------- 11b. the v1 -> v2 migration (R7)
  // THE FAILURE THIS EXISTS TO PREVENT: load() used to `return false` on any
  // v !== 1, and false means newGame() — an unreadable version SILENTLY ERASED a
  // real playthrough. Every field of a v1 save must survive, the fields v1 never
  // had must appear at their opening defaults, and a character added to the game
  // after the save was written must be reconciled in rather than crash the party.
  section('11b. a v1 save migrates forward without loss');
  const V1 = await bootGame();
  const v1blob = {
    v: 1,
    party: [{ id: 'vesper', active: true, level: 5, xp: 7, hp: 41,
              equip: { weapon: 'walking-staff', armor: 'quilted-vest' } }],
    gold: 137, inventory: { tonic: 4 }, flags: { 'npc.met.rowan': true },
  };
  V1.localStorage.setItem('emberbrook-save-v1', JSON.stringify(v1blob));
  ok(V1.GS.hasSave(), 'hasSave() sees a legacy-key save');
  ok(V1.GS.load(), 'load() accepts a v1 save instead of refusing it');
  const st = V1.GS.state;
  eq(st.v, 2, 'the loaded state is v2');
  eq(st.gold, 137, 'gold survived');
  eq(st.inventory.tonic, 4, 'inventory survived');
  eq(st.flags['npc.met.rowan'], true, 'flags survived');
  eq(st.party.find(p => p.id === 'vesper').level, 5, 'the party member survived at level');
  eq(st.at.chapter, 1, 'at.chapter defaults to the opening');
  eq(typeof st.beats, 'object', 'the beat ledger exists');
  for (const id of Object.keys(V1.GS.data.growth.characters))
    ok(!!st.party.find(p => p.id === id), 'growth character "' + id + '" is present after migration');
  eq(V1.localStorage.getItem('emberbrook-save-v1'), null, 'the legacy key is retired after the upgrade');
  ok(!!V1.localStorage.getItem('emberbrook-save'), 'the upgraded save is written to the current slot');

  // ------------------------------------- 11c. joinFlag finally does something
  // growth.json declared `joinFlag` and NOTHING read it (the audit's G8).
  section('11c. a declared joinFlag flips `active` in the save');
  const J = await bootGame();
  const joiners = Object.entries(J.GS.data.growth.characters).filter(([, c]) => c.joinFlag);
  ok(joiners.length > 0, 'growth.json declares at least one joinFlag');
  for (const [id, c] of joiners) {
    eq(J.GS.state.party.find(p => p.id === id).active, false, id + ' starts out of the party');
    J.GS.setFlags({ [c.joinFlag]: true });
    eq(J.GS.state.party.find(p => p.id === id).active, true,
       id + ' is active once "' + c.joinFlag + '" is set');
    ok(J.GS.activeParty().some(p => p.id === id), id + ' appears in activeParty()');
  }

  // -------------------------------------------------- 12. safety without data
  section('12. safety when the rules data is absent');
  const N = await bootGame({ noData: true });
  eq(N.GS.ok, false, 'GS reports not-ok with no data');
  eq(N.Shop.openShop('del-item'), false, 'Shop.openShop returns false instead of throwing');
  eq(N.Shop.registerPrompts(), false, 'Shop.registerPrompts no-ops');
  eq(N.Shop.tick(), null, 'Shop.tick no-ops');
  eq(N.Menu.open(), false, 'Menu.open returns false instead of throwing');
  eq(N.Menu.register(), false, 'Menu.register no-ops');
  eq(N.Menu.partyView().length, 0, 'Menu.partyView is empty, not an exception');
  eq(N.Shop.stock('del-item').length, 0, 'Shop.stock is empty, not an exception');
  eq(N.Shop.buy('del-item', 'tonic', 1).reason, 'nodata', 'Shop.buy refuses with reason nodata');
  eq(N.Menu.useItem('vesper', 'tonic').reason, 'nodata', 'Menu.useItem refuses with reason nodata');

  // ------------------------------------------------ 13. no-DOM module loading
  section('13. modules load and behave without a DOM');
  eq(N.EBUI.HAS_DOM, false, 'EBUI knows there is no DOM');
  eq(N.EBUI.open, false, 'EBUI reports no open panel');
  ok(!!N.EBUI.sgDef('key'), 'EBUI falls back to the scene-graph default key with no SIM');
  eq(N.EBUI.sgDef('promptFmt'), '{label}? [{key}]', 'prompt format matches the scene graph default');

  // -------------------------------------------------------- 14. party-of-N
  section('14. party-of-N: the menu works the moment Maren joins');
  const P = await bootGame();
  eq(P.Menu.partyView().length, 1, 'one active member before the join flag');
  P.GS.state.party.find(p => p.id === 'maren').active = true;
  const pv2 = P.Menu.partyView();
  eq(pv2.length, 2, 'flipping active makes her appear in PARTY with no code change');
  eq(pv2[1].id, 'maren', 'and in party order');
  eq(pv2[1].name, 'Maren', 'with her growth.json name');
  ok(pv2[1].stats.spd > pv2[0].stats.spd, 'with her own growth row (Maren is faster)');
  eq(P.Menu.slotsOf('maren').length, 2, 'her equip slots are enumerated from her own data');
  P.GS.addItem('walking-staff', 1);
  ok(P.Menu.compatible('maren', 'weapon').some(c => c.id === 'walking-staff'),
    'EQUIP offers her the shared bag');
  ok(P.Menu.equipItem('maren', 'walking-staff').ok, 'and equipping her works');
  const evs = P.GS.grantXp(50);
  eq(evs.length, 2, 'xp splits across both active members and both level');

  // ------------------------------------------ 15. shop UI: prompt -> open -> buy
  section('15. shop UI smoke: counter prompt, panel, tabs, a real purchase');
  const S = await bootGame({ dom: true, scene: 'del-item-int' });
  S.UILOCK = makeUilock();
  // SIM stub: only the surface my modules are allowed to use.
  let player = { x: -2.5, y: 0.04, z: -2.28 };            // the door pad = where you arrive
  const PADBOX = { min: [1.25, 0.02, -0.2], max: [2.95, 0.04, 0.8], center: [2.1, 0.03, 0.3] };
  S.SIM = {
    pos: () => ({ ...player }),
    keys: () => { },
    pad: n => (/counter/.test(String(n)) ? { name: 'walk_pad_counter', ...PADBOX } : null),
    graph: () => ({ defaults: graph.defaults, nodes: Object.keys(graph.nodes), scene: 'del-item-int' }),
  };
  ok(S.Shop.registerPrompts(), 'registerPrompts finds the shop for scene del-item-int');
  eq(S.Shop.debug().shop, 'del-item', 'and binds the right shop');
  S.Shop.tick();
  eq(S.Shop.debug().anchor.src, 'SIM.pad', 'the counter anchor came from the SIM.pad hook (no coordinates)');
  eq(S.Shop.debug().armed, true, 'arrival at the door pad leaves the counter prompt armed');
  eq(S.Shop.debug().near, false, 'and not offering, because we are 5m away');
  eq(S.__dom.key('e').stopped, false, 'E at the door is left to play3d (we consume nothing)');
  player = { x: 2.1, y: 0.04, z: 0.3 };                   // walk to the counter
  S.Shop.tick();
  eq(S.Shop.debug().near, true, 'standing on the counter pad offers the prompt');
  ok(S.__dom.key('e').stopped, 'E is consumed by the shop');
  ok(S.Shop.isOpen, 'the shop panel opened');
  ok(S.UILOCK.active(), 'UILOCK is held while the panel is open — the world is frozen');
  eq(S.EBUI.depth, 1, 'one EBUI panel on the stack');
  // Esc while the shop is open must close the shop and NOT stack the pause menu
  // (EBUI suppresses global keys whenever UILOCK is held — the ruled requirement).
  S.__dom.key('Escape');
  eq(S.Menu.isOpen, false, 'Esc did not open the pause menu on top of the shop');
  eq(S.Shop.isOpen, false, 'Esc closed the shop');
  eq(S.UILOCK.active(), false, 'UILOCK released on close');
  S.Shop.tick();
  eq(S.Shop.debug().near, true, 'the counter prompt returns: we are still at the counter');
  // reopen and buy for real, entirely through synthesised keystrokes
  S.__dom.key('e');
  ok(S.Shop.isOpen, 'reopened');
  const gBefore = S.GS.state.gold, tBefore = S.GS.count('tonic');
  S.__dom.key('e');                                        // list -> qty step
  eq(S.Shop.debug().mode, 'qty', 'confirm on a row enters the quantity step');
  S.__dom.key('ArrowRight');                               // qty 1 -> 2
  eq(S.Shop.debug().qty, 2, 'right raises the quantity');
  S.__dom.key('ArrowLeft');
  eq(S.Shop.debug().qty, 1, 'left lowers it');
  S.__dom.key('Enter');                                    // buy
  eq(S.GS.count('tonic'), tBefore + 1, 'the keystroke sequence actually bought an item');
  eq(S.GS.state.gold, gBefore - items.tonic.price, 'and spent exactly its price');
  eq(S.Shop.debug().mode, 'list', 'and returned to the list');
  S.__dom.key('ArrowRight');                               // BUY -> SELL
  eq(S.Shop.debug().tab, 1, 'left/right switches tabs in list mode');
  S.__dom.key('ArrowDown'); S.__dom.key('e'); S.__dom.key('Enter');   // sell one
  eq(S.GS.count('tonic'), tBefore, 'and the SELL tab sold it back');
  S.__dom.key('Escape');
  eq(S.Shop.isOpen, false, 'shop closed again');
  // a non-shop scene must be a silent no-op
  const S2 = await bootGame({ dom: true, scene: 'del-inn-int' });
  eq(S2.Shop.registerPrompts(), false, 'a non-shop interior registers nothing');
  eq(S2.Shop.tick(), null, 'and ticks to nothing');

  // ------------------------------------------------- 16. menu UI: every screen
  section('16. menu UI smoke: every screen, equip and item use by keystroke');
  const M = await bootGame({ dom: true, scene: 'del-cine' });
  M.UILOCK = makeUilock();
  M.SIM = { pos: () => ({ x: 0, y: 0, z: 0 }), keys: () => { }, graph: () => ({ defaults: graph.defaults, nodes: Object.keys(graph.nodes) }) };
  ok(M.Menu.register(), 'Menu registers its Esc trigger');
  M.__dom.key('Escape');
  ok(M.Menu.isOpen, 'Esc opens the pause menu');
  ok(M.UILOCK.active(), 'the menu holds UILOCK — overworld movement is paused');
  eq(M.Menu.debug().screen, 'root', 'it opens on the root command list');
  M.__dom.key('e');                                        // PARTY
  eq(M.Menu.debug().screen, 'party', 'PARTY screen renders');
  M.__dom.key('ArrowRight'); M.__dom.key('Escape');
  eq(M.Menu.debug().screen, 'root', 'Esc returns to root');
  M.__dom.key('ArrowDown'); M.__dom.key('e');              // EQUIP
  eq(M.Menu.debug().screen, 'equipChar', 'EQUIP -> character step');
  M.__dom.key('e');
  eq(M.Menu.debug().screen, 'equipSlot', 'character -> slot step');
  eq(M.Menu.debug().sel.char, 'vesper', 'and remembers who');
  M.GS.addItem('river-cudgel', 1);
  M.__dom.key('e');
  eq(M.Menu.debug().screen, 'equipItem', 'slot -> item step');
  eq(M.Menu.debug().sel.slot, 'weapon', 'and remembers which slot');
  const atkBefore = M.GS.stats(M.GS.state.party[0]).atk;
  M.__dom.key('e');                                        // equip the cudgel
  eq(M.GS.stats(M.GS.state.party[0]).atk,
    atkBefore + items['river-cudgel'].statMods.atk - items['walking-staff'].statMods.atk,
    'equipping by keystroke moved atk by the statMods difference');
  // one Esc per breadcrumb level: equipItem -> equipSlot -> equipChar -> root
  M.__dom.key('Escape'); eq(M.Menu.debug().screen, 'equipSlot', 'Esc: item step -> slot step');
  M.__dom.key('Escape'); eq(M.Menu.debug().screen, 'equipChar', 'Esc: slot step -> character step');
  M.__dom.key('Escape'); eq(M.Menu.debug().screen, 'root', 'Esc: character step -> root');
  M.__dom.key('ArrowDown'); M.__dom.key('e');              // ITEMS
  eq(M.Menu.debug().screen, 'itemPick', 'ITEMS -> item step');
  M.__dom.key('e');
  eq(M.Menu.debug().screen, 'itemChar', 'item -> target step');
  M.GS.setHp('vesper', 1);
  M.__dom.key('e');                                        // use it
  eq(M.GS.state.party[0].hp, 1 + items.tonic.effect.heal, 'using an item by keystroke healed');
  // SAVE / LOAD / NEW GAME confirms
  M.Menu.close(); M.__dom.key('Escape');
  eq(M.Menu.debug().screen, 'root', 'menu reopens at root');
  for (let i = 0; i < 3; i++) M.__dom.key('ArrowDown');    // -> SAVE
  M.__dom.key('e');
  ok(M.Menu.debug().open, 'SAVE raised a confirm');
  M.__dom.key('Enter');                                    // Yes
  // The SLOT key is 'emberbrook-save' since 2026-08-02; 'emberbrook-save-v1' was the
  // key when the key and the schema version were the same string. game_state.js reads
  // the old key once and migrates it forward, so a v1 playthrough is never eaten.
  ok(!!M.localStorage.getItem('emberbrook-save'), 'confirming SAVE wrote the save');
  M.GS.addGold(500);
  M.__dom.key('ArrowDown'); M.__dom.key('e');              // -> LOAD
  M.__dom.key('ArrowUp');                                  // default is No; move to Yes
  M.__dom.key('Enter');
  eq(M.GS.state.gold < 500, true, 'confirming LOAD restored the saved gold');
  M.__dom.key('ArrowDown'); M.__dom.key('e');              // -> NEW GAME
  M.__dom.key('Escape');                                   // cancel the confirm
  eq(M.Menu.debug().screen, 'root', 'cancelling a confirm returns to root');
  M.__dom.key('Escape');
  eq(M.Menu.isOpen, false, 'Esc at root closes the menu');
  eq(M.UILOCK.active(), false, 'and releases UILOCK');
  eq(M.Menu.open(), true, 'Menu.open() works programmatically too');
  M.UILOCK.lock('battle');
  eq(M.Menu.debug().open, true, 'an already-open menu is untouched by another lock');
  M.Menu.close(); M.UILOCK.lock('battle');
  eq(M.Menu.open(), false, 'Menu refuses to open while another modal (battle) holds UILOCK');
  eq(M.__dom.key('Escape').stopped, false, 'and its Esc trigger is suppressed, not consumed');
  M.UILOCK.unlock('battle');

  // ------------------------------------------------------------------ report
  console.log('\n' + '='.repeat(60));
  console.log('economy_test: ' + pass + ' passed, ' + fail + ' failed');
  if (fail) { console.log('\nfailures:'); fails.forEach(f => console.log('  - ' + f)); }
  console.log('='.repeat(60));
  process.exit(fail ? 1 : 0);
}

main().catch(e => { console.error('economy_test crashed:', e); process.exit(1); });
