// battle_turnbased.js — window.Battle: BATTLE V1 (battle-core agent).
//
// THE ONLY THING THE REST OF THE GAME KNOWS:
//   Battle.start(spec, party, opts) -> Promise<result>
//   spec   {zone, group:[monsterId], seed, backdrop}
//   result {outcome:'victory'|'defeat'|'fled', xp, gold, drops:[itemId], turns,
//           partyHp:{charId:hp}, log:[events]}
//   Battle.active — true from the first frame of the entry fade to the last frame
//                   of the exit fade (the overworld freezes itself via UILOCK).
// Nothing else. No state leaks out, xp/gold/drops are REPORTED and never applied
// (GS.applyBattleResult is the world's job), so a real-time battle module can
// replace this file wholesale and the overworld cannot tell.
//
// WHAT LIVES HERE vs IN THE KERNEL: this file is PRESENTATION AND SEATS. Every
// number, the turn order, the damage roll, the scheduler and the AI live in
// battle_rules.js, which runs in node — so tools/battle_sim.mjs balance-tests the
// engine that ships rather than a copy of it. This file adds: the screen, the
// human decision menus, the fade, and the GS plumbing for the Item command.
//
// UI IDIOM: play3d's own HUD/prompt palette (warm off-white #e7ddd0 on near-black,
// #3a2c20 borders, #e9a24b accent, 8px radii, text-shadow 0 1px 2px #000) and the
// economy agent's EBUI key map, so battle keys are the same keys as every other
// panel in the game. EBUI's pure helpers are reused when present; its panel()
// factory is not (a centred 620-900px dialog is the wrong shape for a full-bleed
// battle screen, and innerHTML-swapping bodies cannot host in-flight animations).
(function () {
  'use strict';

  const HAS_DOM = typeof document !== 'undefined' && !!document.createElement;
  const EB = () => (typeof window !== 'undefined' ? window.EBUI : null);

  // ---- shared-kit helpers, with fallbacks so this module never hard-depends --
  const KEYMAP = {
    arrowup: 'up', w: 'up', arrowdown: 'down', s: 'down',
    arrowleft: 'left', a: 'left', arrowright: 'right', d: 'right',
    enter: 'confirm', e: 'confirm', ' ': 'confirm',
    escape: 'cancel', q: 'cancel', backspace: 'cancel',
  };
  function act(ev) {
    const k = EB();
    if (k && k.act) { try { return k.act(ev); } catch (e) { /* fall through */ } }
    return KEYMAP[String(ev.key).toLowerCase()] || null;
  }
  function esc(s) {
    const k = EB();
    if (k && k.esc) { try { return k.esc(s); } catch (e) { /* fall through */ } }
    return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }
  const wrapIdx = (n, i) => (n <= 0 ? 0 : ((i % n) + n) % n);
  const clamp01 = v => v < 0 ? 0 : v > 1 ? 1 : v;
  const wait = (ms) => ms > 0 ? new Promise(r => setTimeout(r, ms))     // setTimeout, not rAF:
                              : Promise.resolve();                      // rAF is throttled in background tabs

  // ---- UILOCK (coordinator-owned modal-input contract) ----------------------
  function lockWorld(on) {
    try {
      const L = window.UILOCK;
      if (L) { on ? L.lock('battle') : L.unlock('battle'); }
    } catch (e) { /* no contract on this page */ }
    try { if (window.SIM && window.SIM.keys) window.SIM.keys({}); } catch (e) { }
  }

  // ===== STYLE ==============================================================
  // One injected sheet. Geometry is mine; every colour is play3d's / EBUI's.
  const CSS = `
.ebb-veil{position:fixed;inset:0;background:#000;z-index:26;pointer-events:none;opacity:0}
.ebb-root{position:fixed;inset:0;z-index:24;display:flex;flex-direction:column;
  overflow:hidden;color:#e7ddd0;text-shadow:0 1px 2px #0008;
  font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;
  opacity:0;transition:opacity 160ms linear}
.ebb-root.on{opacity:1}
.ebb-bg{position:absolute;inset:0;z-index:0}
.ebb-vig{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(115% 85% at 50% 44%,#0000 38%,#000000b0 100%)}
.ebb-hud{position:relative;z-index:3;display:flex;gap:12px;align-items:baseline;
  padding:8px 14px;font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#a99a86}
.ebb-hud b{color:#e7ddd0;font-weight:600}
.ebb-hud .sp{margin-left:auto}
.ebb-field{position:relative;z-index:3;flex:1 1 auto;display:flex;align-items:center;
  justify-content:space-between;gap:min(4vw,40px);padding:0 min(5vw,60px)}
.ebb-foes{display:flex;align-items:flex-end;gap:min(4vw,40px);flex-wrap:wrap}
.ebb-party{display:flex;flex-direction:column;gap:7px;width:min(300px,32vw)}

.ebb-foe{position:relative;display:flex;flex-direction:column;align-items:center;gap:5px;
  transition:opacity 300ms linear,transform 300ms ease-in}
.ebb-foe.dead{opacity:0;transform:translateY(12px) scale(.9)}
.ebb-mark{height:14px;font-size:13px;color:#e9a24b;opacity:0}
.ebb-foe.cur .ebb-mark{opacity:1}
.ebb-sil{filter:drop-shadow(0 8px 10px #0009);animation:ebb-bob 2.8s ease-in-out infinite}
.ebb-sil.hit{animation:ebb-hit 200ms linear}
.ebb-fname{font-size:12.5px;color:#c9bcab;white-space:nowrap}
.ebb-foe.cur .ebb-fname{color:#e9a24b}

.ebb-card{border:1px solid #3a2c2099;border-radius:8px;padding:7px 10px;background:#12100dc4}
.ebb-card.cur{border-color:#e9a24b99;background:#1a150fdd}
.ebb-card.down{opacity:.55}
.ebb-crow{display:flex;gap:8px;align-items:baseline}
.ebb-cname{font-weight:600;letter-spacing:.02em}
.ebb-lv{font-size:11.5px;color:#a99a86;font-family:ui-monospace,Menlo,monospace}
.ebb-hpn{margin-left:auto;font-family:ui-monospace,Menlo,monospace;font-size:12.5px;
  font-variant-numeric:tabular-nums}
.ebb-bar{height:6px;border-radius:3px;background:#3a2c20;overflow:hidden;margin:4px 0 1px}
.ebb-bar>i{display:block;height:100%;background:#e9a24b;transition:width 220ms linear}
.ebb-bar.low>i{background:#e07a5f}
.ebb-fbar{width:64px;height:3px;border-radius:2px;background:#00000066;overflow:hidden}
.ebb-fbar>i{display:block;height:100%;background:#c9bcab99;transition:width 220ms linear}

.ebb-num{position:absolute;left:50%;top:22%;transform:translateX(-50%);pointer-events:none;
  font:600 22px/1 ui-monospace,Menlo,monospace;color:#f2e6d2;text-shadow:0 2px 3px #000,0 0 8px #0008;
  animation:ebb-float 900ms ease-out forwards}
.ebb-num.heal{color:#8fbf6a}
.ebb-num.miss{color:#a99a86;font-size:16px}

.ebb-log{position:relative;z-index:3;min-height:2.1em;padding:0 min(5vw,60px) 8px;
  font-size:14px;color:#e7ddd0}
.ebb-log em{color:#e9a24b;font-style:normal}
.ebb-bottom{position:relative;z-index:3;display:flex;gap:14px;align-items:center;
  padding:9px min(5vw,60px);border-top:1px solid #3a2c20;background:#12100df2}
.ebb-cmds{display:flex;gap:7px}
.ebb-cmd{padding:4px 16px;border:1px solid #3a2c20;border-radius:6px;color:#c9bcab;
  font-size:13.5px}
.ebb-cmd.cur{background:#e9a24b;border-color:#e9a24b;color:#12100d;font-weight:600}
.ebb-cmds.idle .ebb-cmd{opacity:.4}
.ebb-cmds.idle .ebb-cmd.cur{background:#3a2c20;border-color:#3a2c20;color:#c9bcab}
.ebb-hint{margin-left:auto;font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#6f6558}
.ebb-sub{position:absolute;left:min(5vw,60px);bottom:100%;margin-bottom:8px;
  min-width:220px;max-height:44vh;overflow:auto;background:#12100dfa;
  border:1px solid #3a2c20;border-radius:8px;padding:5px;display:none}
.ebb-sub.on{display:block}
.ebb-item{display:flex;gap:10px;align-items:baseline;padding:3px 8px;border-radius:5px;
  border:1px solid transparent;font-size:13.5px}
.ebb-item.cur{background:#e9a24b1f;border-color:#e9a24b66}
.ebb-item.dim{color:#6f6558}
.ebb-item .n{margin-left:auto;font-family:ui-monospace,Menlo,monospace;font-size:12.5px}

.ebb-outro{position:absolute;inset:0;z-index:5;display:flex;align-items:center;
  justify-content:center;background:#00000055}
.ebb-obox{min-width:min(420px,80vw);background:#12100dfa;border:1px solid #3a2c20;
  border-radius:10px;box-shadow:0 10px 40px #000a;overflow:hidden}
.ebb-ohead{padding:10px 16px;border-bottom:1px solid #3a2c20;background:#1a150fcc;
  font-weight:600;letter-spacing:.03em}
.ebb-obody{padding:10px 16px}
.ebb-orow{display:flex;gap:10px;padding:2px 0;font-size:13.5px}
.ebb-orow .n{margin-left:auto;font-family:ui-monospace,Menlo,monospace;color:#e9a24b;
  font-variant-numeric:tabular-nums}
.ebb-ofoot{padding:7px 16px;border-top:1px solid #3a2c20;background:#1a150fcc;
  font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#a99a86}
.ebb-toast{position:fixed;left:50%;top:12%;transform:translateX(-50%);z-index:27;
  background:#12100dfa;border:1px solid #e9a24b66;border-radius:8px;padding:7px 16px;
  color:#e7ddd0;font:13.5px system-ui,sans-serif;text-shadow:0 1px 2px #000;
  opacity:0;transition:opacity 180ms linear;pointer-events:none}
.ebb-toast.on{opacity:1}

@keyframes ebb-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes ebb-hit{0%,100%{transform:translateX(0)}25%{transform:translateX(-7px)}
  75%{transform:translateX(7px)}}
@keyframes ebb-float{0%{opacity:0;transform:translate(-50%,6px) scale(.9)}
  20%{opacity:1;transform:translate(-50%,-6px) scale(1.05)}
  100%{opacity:0;transform:translate(-50%,-42px) scale(1)}}
@media (prefers-reduced-motion:reduce){
  .ebb-sil{animation:none}.ebb-num{animation-duration:1ms}}`;
  let styled = false;
  function style() {
    if (styled || !HAS_DOM) return;
    styled = true;
    const s = document.createElement('style');
    s.id = 'ebb-style'; s.textContent = CSS;
    document.head.appendChild(s);
  }

  // ===== SWAPPABLE ART LOOKUPS ==============================================
  // BACKDROPS: keyed by encounters.json `battleBackdrop`. A value is either a CSS
  // background string or a function(ctx) returning one (or an element to mount) —
  // so replacing a placeholder gradient with a pre-rendered PNG, or with a canvas
  // that animates, is ONE TABLE ENTRY and touches nothing else in this file.
  const backdrops = {
    meadow: 'radial-gradient(60% 40% at 50% 26%,#ffe6b83d 0%,#0000 70%),' +
            'linear-gradient(180deg,#a9c3d4 0%,#d9cfae 33%,#cbbf95 46%,#6f8046 47%,#55643a 70%,#2b3220 100%)',
    forest: 'radial-gradient(45% 32% at 62% 16%,#ffe6b833 0%,#0000 70%),' +
            'linear-gradient(180deg,#22301f 0%,#3c4b33 24%,#2f3a27 47%,#28331f 48%,#131b0e 100%)',
    crag:   'radial-gradient(60% 40% at 42% 22%,#ffd9a83a 0%,#0000 70%),' +
            'linear-gradient(180deg,#c9c0a8 0%,#b39a72 30%,#8d6f4d 46%,#6a4f37 47%,#3b2a1d 100%)',
    water:  'radial-gradient(60% 40% at 50% 24%,#cfe8f03a 0%,#0000 70%),' +
            'linear-gradient(180deg,#9fc0cf 0%,#cfd9cf 30%,#4d8496 47%,#2f6072 48%,#173540 100%)',
    default:'linear-gradient(180deg,#3b3630 0%,#2a2620 48%,#171410 100%)',
  };
  // SILHOUETTES: keyed by monsters.json `family`, so a new monster of a known
  // family needs no code. Placeholder art by contract — no 3D work in battle v1.
  const sprites = {
    nibbler: { w: 92, h: 68, lit: '#c8b877', dark: '#6c5f34', radius: '52% 52% 46% 46%' },
    sprite:  { w: 56, h: 76, lit: '#bfe9f2', dark: '#3f8ea6', clip: 'polygon(50% 0,100% 46%,50% 100%,0 46%)' },
    duskpad: { w: 104, h: 72, lit: '#8b7f92', dark: '#413a4c',
               clip: 'polygon(4% 100%,9% 44%,24% 26%,46% 22%,70% 30%,88% 24%,96% 42%,98% 100%,78% 100%,74% 70%,28% 70%,24% 100%)' },
    shade:   { w: 88, h: 84, lit: '#6a5a78', dark: '#2c2436',
               clip: 'polygon(50% 0,62% 20%,84% 12%,76% 36%,100% 50%,78% 62%,88% 88%,58% 78%,50% 100%,40% 78%,14% 90%,22% 62%,0 50%,24% 36%,16% 12%,38% 20%)' },
    shell:   { w: 112, h: 62, lit: '#c3a173', dark: '#6b4f31', radius: '54% 54% 14% 14%' },
    eel:     { w: 118, h: 52, lit: '#79c9ae', dark: '#2f6a58',
               clip: 'polygon(0 44%,28% 16%,62% 30%,100% 4%,88% 52%,100% 96%,58% 72%,26% 88%)' },
    default: { w: 84, h: 70, lit: '#a2957f', dark: '#4b4237', radius: '48%' },
  };

  function bgFor(key, ctx) {
    let v = backdrops[key];
    if (v === undefined) v = backdrops.default;
    if (typeof v === 'function') { try { v = v(ctx); } catch (e) { v = backdrops.default; } }
    return v;
  }

  // ===== THE SCREEN =========================================================
  // Owns DOM and nothing else: it renders events, runs the cursor, and resolves
  // one action per request. It never computes a number and never reads GS
  // directly (the bag adapter does that), so a different screen is a drop-in.
  function makeScreen(cfg) {
    style();
    const host = document.body;
    const S = {
      speed: cfg.speed == null ? 1 : cfg.speed,
      nodes: {},                 // combatantId -> {el, sil, fill, txt}
      pending: null,             // the live decision request
      state: cfg.state,
      round: 0,
      cmds: ['Attack', 'Item', 'Flee'],
    };

    const root = document.createElement('div');
    root.className = 'ebb-root';
    root.innerHTML =
      '<div class="ebb-bg"></div><div class="ebb-vig"></div>' +
      '<div class="ebb-hud"><b class="zone"></b><span class="rnd"></span>' +
      '<span class="sp seat"></span></div>' +
      '<div class="ebb-field"><div class="ebb-foes"></div><div class="ebb-party"></div></div>' +
      '<div class="ebb-log"></div>' +
      '<div class="ebb-bottom"><div class="ebb-sub"></div>' +
      '<div class="ebb-cmds idle"></div><div class="ebb-hint"></div></div>';
    host.appendChild(root);
    const q = (c) => root.querySelector('.ebb-' + c);
    const qq = (c) => root.querySelector('.' + c);

    q('bg').style.background = bgFor(cfg.backdrop, cfg);
    qq('zone').textContent = (cfg.zone || 'battle').toUpperCase();
    q('hint').innerHTML = 'move <b>WASD/arrows</b> · confirm <b>Enter</b> · back <b>Esc</b>';

    // --- build combatant nodes ---
    function silEl(family, i) {
      const d = sprites[family] || sprites.default;
      const e = document.createElement('div');
      e.className = 'ebb-sil';
      e.style.width = d.w + 'px'; e.style.height = d.h + 'px';
      e.style.background = 'linear-gradient(165deg,' + d.lit + ' 0%,' + d.dark + ' 78%)';
      if (d.clip) e.style.clipPath = d.clip;
      if (d.radius) e.style.borderRadius = d.radius;
      e.style.animationDelay = (i * 0.37).toFixed(2) + 's';
      return e;
    }
    const foesBox = q('foes'), partyBox = q('party');
    (cfg.state.foes || []).forEach((c, i) => {
      const el = document.createElement('div');
      el.className = 'ebb-foe';
      const mark = document.createElement('div'); mark.className = 'ebb-mark'; mark.textContent = '▾';
      const sil = silEl(cfg.familyOf ? cfg.familyOf(c.ref) : 'default', i);
      const name = document.createElement('div'); name.className = 'ebb-fname'; name.textContent = c.name;
      const bar = document.createElement('div'); bar.className = 'ebb-fbar';
      const fill = document.createElement('i'); fill.style.width = '100%'; bar.appendChild(fill);
      el.appendChild(mark); el.appendChild(sil); el.appendChild(name);
      if (Battle.showFoeHp) el.appendChild(bar);
      foesBox.appendChild(el);
      S.nodes[c.id] = { el: el, sil: sil, fill: fill, txt: null, name: name };
    });
    (cfg.state.party || []).forEach((c) => {
      const el = document.createElement('div');
      el.className = 'ebb-card';
      el.innerHTML = '<div class="ebb-crow"><span class="ebb-cname"></span>' +
        '<span class="ebb-lv"></span><span class="ebb-hpn"></span></div>' +
        '<div class="ebb-bar"><i></i></div>';
      el.querySelector('.ebb-cname').textContent = c.name;
      el.querySelector('.ebb-lv').textContent = 'Lv ' + (c.level || 1);
      partyBox.appendChild(el);
      S.nodes[c.id] = { el: el, sil: el, fill: el.querySelector('.ebb-bar>i'),
                        txt: el.querySelector('.ebb-hpn'), bar: el.querySelector('.ebb-bar') };
    });

    // --- rendering ---
    function nameOf(id) {
      const c = window.Rules.findById(S.state, id);
      return c ? c.name : id;
    }
    function syncHp(state) {
      S.state = state || S.state;
      for (const c of S.state.party.concat(S.state.foes)) {
        const n = S.nodes[c.id]; if (!n) continue;
        const f = clamp01(c.maxHp ? c.hp / c.maxHp : 0);
        n.fill.style.width = (f * 100).toFixed(1) + '%';
        if (n.txt) n.txt.textContent = c.hp + '/' + c.maxHp;
        if (n.bar) n.bar.classList.toggle('low', f <= 0.3);
        if (c.side === 'foe') n.el.classList.toggle('dead', !!c.dead);
        else n.el.classList.toggle('down', !!c.dead);
      }
      qq('rnd').textContent = 'round ' + S.round;
    }
    function logLine(html) { q('log').innerHTML = html; }
    function floatNum(id, text, kind) {
      const n = S.nodes[id]; if (!n) return;
      const e = document.createElement('div');
      e.className = 'ebb-num' + (kind ? ' ' + kind : '');
      e.textContent = text;
      n.el.style.position = 'relative';
      n.el.appendChild(e);
      setTimeout(() => { if (e.parentNode) e.parentNode.removeChild(e); }, 1000);
    }
    function hitShake(id) {
      const n = S.nodes[id]; if (!n) return;
      n.sil.classList.remove('hit'); void n.sil.offsetWidth; n.sil.classList.add('hit');
    }

    // --- the event feed (this is what makes `emit` awaited in the kernel) -----
    async function play(events, state) {
      for (const ev of events) {
        S.state = state || S.state;
        switch (ev.t) {
          case 'round':
            S.round = ev.n; syncHp(state); break;
          case 'action':
            if (ev.kind === 'attack') logLine('<em>' + esc(nameOf(ev.by)) + '</em> attacks.');
            else if (ev.kind === 'item') logLine('<em>' + esc(nameOf(ev.by)) + '</em> uses ' + esc(cfg.itemName(ev.item)) + '.');
            else if (ev.kind === 'flee') logLine('<em>' + esc(nameOf(ev.by)) + '</em> tries to flee…');
            else logLine('<em>' + esc(nameOf(ev.by)) + '</em> ' + esc(ev.kind) + 's.');
            await wait(170 * S.speed);
            break;
          case 'damage':
            syncHp(state); hitShake(ev.target); floatNum(ev.target, String(ev.amount));
            logLine('<em>' + esc(nameOf(ev.target)) + '</em> takes ' + ev.amount + ' damage.');
            await wait(400 * S.speed);
            break;
          case 'heal':
            syncHp(state); floatNum(ev.target, '+' + ev.amount, 'heal');
            logLine('<em>' + esc(nameOf(ev.target)) + '</em> recovers ' + ev.amount + ' HP.');
            await wait(380 * S.speed);
            break;
          case 'ko':
            syncHp(state);
            logLine('<em>' + esc(nameOf(ev.id)) + '</em> ' + (ev.side === 'foe' ? 'is defeated.' : 'falls.'));
            await wait(300 * S.speed);
            break;
          case 'flee':
            logLine(ev.ok ? 'Got away safely!' : 'Cornered — no escape!');
            await wait(400 * S.speed);
            break;
          case 'noop':
            if (ev.why === 'round-cap') logLine('The fight breaks off.');
            break;
          case 'end':
            syncHp(state); break;
        }
      }
      syncHp(state);
    }

    // --- the decision cursor -------------------------------------------------
    // One request at a time per screen; a second seat would get its own cursor
    // object (the scheduler already collects seats concurrently).
    function promptAction(actorId, state, api) {
      S.state = state;
      return new Promise((resolve) => {
        S.pending = { actorId, api, resolve, mode: 'cmd', ci: 0, ti: 0, ii: 0, items: [] };
        for (const c of state.party) {
          const n = S.nodes[c.id]; if (n) n.el.classList.toggle('cur', c.id === actorId);
        }
        qq('seat').textContent = (api && api.seatName ? api.seatName + ' · ' : '') + nameOf(actorId);
        renderMenu();
      });
    }
    function livingFoes() { return S.state.foes.filter(c => !c.dead); }
    function renderMenu() {
      const p = S.pending;
      const cmds = q('cmds'), sub = q('sub');
      cmds.classList.toggle('idle', !p);
      cmds.innerHTML = S.cmds.map((c, i) =>
        '<span class="ebb-cmd' + (p && p.ci === i ? ' cur' : '') + '">' + c + '</span>').join('');
      if (!p) { sub.classList.remove('on'); markFoe(-1); return; }
      if (p.mode === 'target') {
        sub.classList.remove('on');
        const fs = livingFoes();
        markFoe(fs.length ? fs[wrapIdx(fs.length, p.ti)].id : -1);
        logLine('Attack which?');
      } else if (p.mode === 'items') {
        markFoe(-1);
        sub.classList.add('on');
        sub.innerHTML = p.items.length
          ? p.items.map((it, i) => '<div class="ebb-item' + (p.ii === i ? ' cur' : '') +
              (it.count > 0 ? '' : ' dim') + '"><span class="ebb-cur">' + (p.ii === i ? '▸' : ' ') +
              '</span><span>' + esc(it.name) + '</span><span class="n">x' + it.count + '</span></div>').join('')
          : '<div class="ebb-item dim">no usable items</div>';
        logLine('Use what?');
      } else {
        sub.classList.remove('on'); markFoe(-1);
        logLine('<em>' + esc(nameOf(p.actorId)) + '</em> — what will you do?');
      }
    }
    function markFoe(id) {
      for (const c of S.state.foes) {
        const n = S.nodes[c.id]; if (n) n.el.classList.toggle('cur', c.id === id);
      }
    }
    function settle(action) {
      const p = S.pending; if (!p) return;
      S.pending = null;
      for (const c of S.state.party) { const n = S.nodes[c.id]; if (n) n.el.classList.remove('cur'); }
      markFoe(-1);
      renderMenu();
      p.resolve(action);
    }
    // returns true if the key was consumed
    function onKey(a) {
      const p = S.pending;
      if (S.outro) { if (a === 'confirm' || a === 'cancel') { const f = S.outro; S.outro = null; f(); } return true; }
      if (!p) return true;                       // battle is resolving: swallow, never leak to the world
      const step = (a === 'down' || a === 'right') ? 1 : (a === 'up' || a === 'left') ? -1 : 0;
      if (p.mode === 'cmd') {
        if (step) { p.ci = wrapIdx(S.cmds.length, p.ci + step); renderMenu(); return true; }
        if (a === 'confirm') {
          if (p.ci === 0) { p.mode = 'target'; p.ti = 0; }
          else if (p.ci === 1) { p.items = p.api.bag.list(); p.mode = 'items'; p.ii = 0; }
          else { settle({ type: 'flee', by: p.actorId }); return true; }
          renderMenu(); return true;
        }
        return true;
      }
      if (p.mode === 'target') {
        const fs = livingFoes();
        if (step) { p.ti = wrapIdx(fs.length, p.ti + step); renderMenu(); return true; }
        if (a === 'cancel') { p.mode = 'cmd'; renderMenu(); return true; }
        if (a === 'confirm') {
          if (!fs.length) { p.mode = 'cmd'; renderMenu(); return true; }
          settle({ type: 'attack', by: p.actorId, target: fs[wrapIdx(fs.length, p.ti)].id });
          return true;
        }
        return true;
      }
      if (p.mode === 'items') {
        if (step) { p.ii = wrapIdx(p.items.length, p.ii + step); renderMenu(); return true; }
        if (a === 'cancel') { p.mode = 'cmd'; renderMenu(); return true; }
        if (a === 'confirm') {
          const it = p.items[p.ii];
          if (!it || it.count <= 0) return true;
          // party-of-N: a second living member opens a target step. v1 has one.
          const targets = S.state.party.filter(c => !c.dead);
          const tgt = targets.length === 1 ? targets[0].id : (targets[0] && targets[0].id);
          if (!p.api.bag.use(it.id)) { logLine('None left.'); return true; }
          settle({ type: 'item', by: p.actorId, target: tgt, item: it.id, effect: it.effect });
          return true;
        }
        return true;
      }
      return true;
    }

    // --- outro ---------------------------------------------------------------
    function outro(result) {
      const titles = { victory: 'Victory', defeat: 'Defeated', fled: 'Escaped' };
      const box = document.createElement('div');
      box.className = 'ebb-outro';
      const drops = (result.drops || []).map(id => cfg.itemName(id));
      const rows = [];
      if (result.outcome === 'victory') {
        rows.push(['Experience', result.xp]);
        rows.push(['Gold', result.gold]);
        if (drops.length) rows.push(['Found', drops.join(', ')]);
      }
      rows.push(['Rounds', result.turns]);
      box.innerHTML = '<div class="ebb-obox"><div class="ebb-ohead">' +
        esc(titles[result.outcome] || result.outcome) + '</div><div class="ebb-obody">' +
        rows.map(r => '<div class="ebb-orow"><span>' + esc(r[0]) + '</span><span class="n">' +
          esc(r[1]) + '</span></div>').join('') +
        '</div><div class="ebb-ofoot">Enter to continue</div></div>';
      root.appendChild(box);
      logLine('');
      if (cfg.autoConfirm) return wait(700 * S.speed);
      return new Promise((resolve) => {
        S.outro = resolve;
        // never strand a player on a summary screen if a key event is eaten
        setTimeout(() => { if (S.outro === resolve) { S.outro = null; resolve(); } }, 30000);
      });
    }

    return {
      el: root, play, promptAction, onKey, outro, syncHp,
      show() { root.classList.add('on'); },
      destroy() { if (root.parentNode) root.parentNode.removeChild(root); },
      _state() { return S; },
    };
  }

  // ===== INPUT ==============================================================
  // ONE capture-phase listener for the page lifetime, gated on Battle.active.
  // Capture on window runs before play3d's bubble-phase handlers, so while a
  // battle is up the world cannot see a keystroke — belt and braces with UILOCK,
  // and it wins the registration race against any other capture listener as long
  // as this file loads first.
  let wired = false, screenRef = null;
  function wire() {
    if (wired || !HAS_DOM) return; wired = true;
    const swallow = (ev) => {
      if (!Battle.active) return;
      ev.stopImmediatePropagation();
      ev.preventDefault();
    };
    window.addEventListener('keydown', (ev) => {
      if (!Battle.active) return;
      ev.stopImmediatePropagation();
      ev.preventDefault();
      if (!screenRef) return;
      const a = act(ev);
      if (a) { try { screenRef.onKey(a); } catch (e) { console.error('[Battle] key', e); } }
    }, true);
    window.addEventListener('keyup', swallow, true);
    window.addEventListener('keypress', swallow, true);
  }

  // ===== FADE ===============================================================
  // Battle owns its veil: play3d's sgFade is module-internal. Same duration and
  // easing as the scene-graph transition so a cut to battle feels like a cut to a
  // shot. opts.fade lets a caller (or a future in-place transition layer) supply
  // its own.
  const FADE_MS = 350;
  let veil = null;
  function veilEl() {
    if (veil) return veil;
    style();
    veil = document.createElement('div');
    veil.className = 'ebb-veil';
    document.body.appendChild(veil);
    return veil;
  }
  function fadeTo(to, ms) {
    if (!HAS_DOM) return Promise.resolve();
    ms = ms == null ? FADE_MS : ms;
    const v = veilEl();
    v.style.transition = 'opacity ' + ms + 'ms linear';
    v.style.opacity = String(to);
    return wait(ms + 20);
  }

  // ===== BAG ADAPTER ========================================================
  // The one place a battle touches the inventory. Items are consumed through GS
  // immediately (a fled or lost battle must still have spent its tonics) but the
  // HEAL is applied inside the battle state, never through GS.useItem — in-battle
  // HP is battle state and is written back once, via result.partyHp.
  function makeBag(gs, itemsMap, override) {
    if (override) return override;
    return {
      list() {
        const out = [];
        if (!gs || !gs.state) return out;
        for (const id in gs.state.inventory) {
          const d = itemsMap[id];
          if (!d || d.type !== 'consumable' || !d.effect) continue;
          out.push({ id, name: d.name || id, count: gs.state.inventory[id], effect: Object.assign({}, d.effect) });
        }
        out.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
        return out;
      },
      use(id) { return gs && gs.removeItem ? gs.removeItem(id) : true; },
      count(id) { return gs && gs.count ? gs.count(id) : 0; },
    };
  }

  // ===== TOAST (level-up pings etc; used by encounters.js) ==================
  let toastEl = null, toastT = 0;
  function toast(text, ms) {
    if (!HAS_DOM) return;
    style();
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'ebb-toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = text;
    toastEl.classList.add('on');
    clearTimeout(toastT);
    toastT = setTimeout(() => { if (toastEl) toastEl.classList.remove('on'); }, ms || 2600);
  }

  // ===== THE CONTRACT =======================================================
  const Battle = window.Battle = {
    version: 1,
    active: false,
    showFoeHp: true,      // classic FF hides it; on by default while art is placeholder
    backdrops, sprites,   // swappable lookups, mutable by anyone
    router: null,         // the LIVE router of the running battle (remap mid-battle)
    scheduler: null,      // the policy object in use
    last: null,           // last result (debug)
    toast,

    // ---- Battle.start(spec, party, opts) -> Promise<result> ----------------
    async start(spec, party, opts) {
      opts = opts || {};
      const RU = window.Rules;
      if (!RU) { console.warn('[Battle] battle_rules.js not loaded — battle skipped'); return null; }
      if (Battle.active) { console.warn('[Battle] already running'); return null; }
      spec = spec || {};

      const gs = opts.gs !== undefined ? opts.gs : (typeof window !== 'undefined' ? window.GS : null);
      const data = (gs && gs.data) || {};
      const monstersMap = opts.monsters || (data.monsters && data.monsters.monsters) || {};
      const itemsMap = opts.items || (data.items && data.items.items) || {};
      const growth = opts.growth || data.growth;

      // party: given, else derived from GS (so a console one-liner works)
      let members = party;
      if (!members && gs && gs.ok && growth) {
        members = gs.activeParty().map(ch => RU.derive.partyMember(growth, itemsMap, ch));
      }
      members = (members || []).filter(m => m && m.hp > 0);
      if (!members.length) { console.warn('[Battle] no living party — battle skipped'); return null; }

      const group = (spec.group || []).filter(id => monstersMap[id]);
      if (!group.length) { console.warn('[Battle] empty monster group — battle skipped'); return null; }

      const seed = (spec.seed != null ? spec.seed : RU.hashSeed(spec.zone || '', group.join(','))) >>> 0;
      const rng = RU.mulberry32(seed);
      const state0 = RU.makeState({ party: members, foes: RU.derive.foesFromGroup(monstersMap, group) });

      Battle.active = true;              // set BEFORE the first await: the phys() freeze is immediate
      lockWorld(true);
      wire();

      const log = [];
      const speed = opts.speed == null ? 1 : opts.speed;
      const headless = !HAS_DOM || opts.headless === true;
      let screen = null, result = null;
      const fade = opts.fade || fadeTo;

      try {
        if (!headless) {
          await fade(1);
          screen = makeScreen({
            state: state0, zone: spec.zone, backdrop: spec.backdrop || spec.zone,
            speed: speed, autoConfirm: !!opts.autoplay || speed === 0,
            familyOf: (mid) => (monstersMap[mid] && monstersMap[mid].family) || 'default',
            itemName: (id) => (itemsMap[id] && itemsMap[id].name) || id,
          });
          screenRef = screen;
          screen.show(); screen.syncHp(state0);
          await fade(0);
        }

        // ---- seats -----------------------------------------------------------
        const bag = makeBag(gs, itemsMap, opts.bag);
        const human = screen ? {
          name: 'menu',
          decide: (actorId, state, api) => screen.promptAction(actorId, state,
            Object.assign({ seatName: Battle.router && Battle.router.seatFor(actorId) }, api)),
        } : null;
        // The party autopilot doubles as the drop-out seat. It keeps its own
        // inventory tally, so the real bag is spent by this wrapper.
        const invSnapshot = {};
        for (const it of bag.list()) invSnapshot[it.id] = it.count;
        const partyAi = RU.policies.partyAi({ items: itemsMap, inventory: invSnapshot });
        const autopilot = {
          name: 'party-ai',
          async decide(actorId, state, api) {
            const a = await partyAi.decide(actorId, state, api);
            if (a && a.type === 'item' && a.item && !bag.use(a.item)) return { type: 'attack', by: actorId };
            return a;
          },
        };
        // THE 'ai' SEAT IS SIDE-AWARE, and that is not a detail: it is what makes
        // "player 2 drops out -> router.set(charId,'ai')" work mid-battle. Monsters
        // get the monster policy, a party member routed to 'ai' gets the autopilot.
        const foeAi = RU.policies.monsterAi();
        const aiSeat = {
          name: 'ai',
          decide(actorId, state, api) {
            const c = RU.findById(state, actorId);
            return (c && c.side === 'foe' ? foeAi : autopilot).decide(actorId, state, api);
          },
        };
        const seats = Object.assign({
          p1: human || autopilot,       // no screen (headless) -> the autopilot plays
          p2: human || autopilot,       // unbound until a second seat exists
          ai: aiSeat,
        }, opts.seats);
        // v1 routes every party member to p1; the table is REAL and remappable
        // mid-battle (Battle.router.set('vesper','p2')) — that is the co-op seam.
        const router = opts.router || RU.makeRouter({
          seats: seats,
          defaults: { party: opts.autoplay ? 'ai' : 'p1', foe: 'ai' },
        });
        Battle.router = router;
        const scheduler = opts.scheduler || RU.schedulers.commitThenResolve;
        Battle.scheduler = scheduler;

        const emit = async (events, state) => {
          for (const ev of events) log.push(ev);
          if (screen) await screen.play(events, state);
        };

        const final = await RU.engine.run({
          state: state0, rng, router, seats, scheduler, emit,
          api: { bag, items: itemsMap, seatName: null },
          maxRounds: opts.maxRounds,
        });

        result = RU.engine.result(final, { monsters: monstersMap, rng, log });
        Battle.last = result;
        if (screen) await screen.outro(result);
      } catch (e) {
        console.error('[Battle] failed', e);
        // A crashed battle must never eat the party or freeze the world.
        result = { outcome: 'fled', xp: 0, gold: 0, drops: [], turns: 0,
                   partyHp: members.reduce((o, m) => (o[m.id] = m.hp, o), {}), log: log, error: String(e) };
      } finally {
        if (screen) { await fade(1); screen.destroy(); }
        screenRef = null;
        Battle.active = false;
        lockWorld(false);
        if (screen) await fade(0);
      }
      return result;
    },

    // ---- conveniences (console + coordinator playtest) ---------------------
    // Battle.demo('meadow') — build a spec from encounters.json and fight it.
    demo(zone, opts) {
      const gs = window.GS;
      if (!gs || !gs.ok) { console.warn('[Battle] GS not ready'); return null; }
      const RU = window.Rules;
      const zd = gs.data.encounters.zones[zone || 'meadow'];
      if (!zd) { console.warn('[Battle] no such zone', zone); return null; }
      const seed = (opts && opts.seed != null) ? opts.seed : RU.hashSeed('demo', zone, gs.state.party[0].xp);
      const group = RU.derive.pickGroup(zd, RU.mulberry32(seed)) || [];
      return Battle.start({ zone: zone, group: group, seed: seed, backdrop: zd.battleBackdrop }, null, opts);
    },
    _debug() {
      return {
        active: Battle.active, scheduler: Battle.scheduler && Battle.scheduler.name,
        router: Battle.router && Battle.router.table(),
        rules: !!window.Rules, dom: HAS_DOM, last: Battle.last,
        ebui: !!(EB() && EB().act), showFoeHp: Battle.showFoeHp,
        backdrops: Object.keys(backdrops), sprites: Object.keys(sprites),
      };
    },
  };
  wire();
})();
