'use strict';
/* ============================================================
   ISO-EXPLAIN — explainer + debug inspection page.
   Read-only companion to iso-proto. Loads the REAL engine
   (registry.js + engine.js run on a hidden canvas) and reuses
   its actual functions and data: sx/sy, Images, drawBlock,
   drawContactShadow, sortKey, loadScene, G, IsoBlocks.
   ============================================================ */
(() => {

  /* engine.js preventDefaults arrows/space for gameplay; on this page we
     want normal scrolling, so swallow those keys before the engine sees
     them (capture phase runs first). */
  addEventListener('keydown', e => {
    const k = e.key.toLowerCase();
    if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(k)) {
      e.stopImmediatePropagation();
    }
  }, true);

  const $ = s => document.querySelector(s);
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };

  const C = {
    solidFill: 'rgba(224,64,48,0.35)', solidLine: 'rgba(255,107,94,0.95)',
    walkFill: 'rgba(88,200,112,0.18)', walkLine: 'rgba(111,208,138,0.85)',
    footProp: 'rgba(255,177,78,0.95)', footBack: 'rgba(180,138,255,0.95)',
    anchor: '#ffd866', grid: 'rgba(240,230,210,0.32)',
    trig: 'rgba(80,200,255,0.4)', spawn: '#ff7ad9',
  };

  let METRICS = {};
  const SCAN = {};          // name -> { low, top } lowest/highest opaque row
  const BADGES = { bad: [], warn: [] };

  // setTimeout (not rAF): rAF is throttled to zero in background tabs and
  // would stall the page build until the tab is focused
  const wait = fn => new Promise(r => {
    const t = () => fn() ? r() : setTimeout(t, 120);
    t();
  });

  /* ---------------- pixel scan ---------------- */
  function scanImage(img) {
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const g = c.getContext('2d', { willReadFrequently: true });
    g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, img.width, img.height).data;
    let low = -1, top = -1;
    for (let y = img.height - 1; y >= 0 && low < 0; y--) {
      for (let x = 0; x < img.width; x++) {
        if (d[(y * img.width + x) * 4 + 3] > 16) { low = y; break; }
      }
    }
    for (let y = 0; y < img.height && top < 0; y++) {
      for (let x = 0; x < img.width; x++) {
        if (d[(y * img.width + x) * 4 + 3] > 16) { top = y; break; }
      }
    }
    return { low, top };
  }

  async function ensureImage(name) {
    if (!Images[name]) Images[name] = await loadImage('assets/iso/blocks/' + name + '.png');
    return Images[name];
  }

  /* ---------------- geometry helpers ---------------- */
  // cell (di,dj) offset -> screen offset (same math as engine sx/sy)
  const rel = (di, dj) => [(di - dj) * (TW / 2), (di + dj) * (TH / 2)];

  // anchor cell coordinates (which corner/centre of the footprint the sprite
  // is pinned to), per engine drawBlock
  function anchorMode(def) {
    if (def.kind === 'ground' || def.kind === 'flat') return 'back';
    if (def.kind === 'slab' || (def.kind === 'backdrop' && def.anchor !== 'free')) return 'front';
    return def.ax != null ? 'free-ax' : 'free-bc';
  }

  function solidCells(def) {
    if (def.kind === 'flat') return [];
    if (def.solid) return def.solid;
    if (def.walk) return [];
    const out = [];
    for (let b = 0; b < def.foot[1]; b++)
      for (let a = 0; a < def.foot[0]; a++) out.push([a, b]);
    return out;
  }

  // replicate drawBlock's placement to get a block's sprite rect in world px
  function spriteRectWorld(p) {
    const im = Images[p.name];
    if (!im) return null;
    const def = p.def, s = def.s || 1;
    const w = im.width * s, h = im.height * s;
    const dy = ((def.dy || 0) + ((p.opts && p.opts.dy) || 0)) * s;
    const dx = ((p.opts && p.opts.dx) || 0) * s;
    let px, py;
    if (def.kind === 'ground' || def.kind === 'flat') {
      px = sx(p.i, p.j) - w / 2; py = sy(p.i, p.j) - 1;
    } else if (def.kind === 'slab' || (def.kind === 'backdrop' && def.anchor !== 'free')) {
      const fx = p.i + def.foot[0], fy = p.j + def.foot[1];
      px = sx(fx, fy) - w / 2; py = sy(fx, fy) - h;
    } else {
      const cx = p.i + def.foot[0] / 2, cy = p.j + def.foot[1] / 2;
      if (def.ax != null) { px = sx(cx, cy) - def.ax * s; py = sy(cx, cy) - def.ay * s; }
      else { px = sx(cx, cy) - w / 2; py = sy(cx, cy) - h; }
    }
    return [px + dx, py + dy, w, h];
  }

  function diamondPath(ctx, x0, y0, i0, j0, i1, j1) {
    const [ax, ay] = rel(i0, j0), [bx, by] = rel(i1, j0),
          [cx, cy] = rel(i1, j1), [dx, dy] = rel(i0, j1);
    ctx.beginPath();
    ctx.moveTo(x0 + ax, y0 + ay);
    ctx.lineTo(x0 + bx, y0 + by);
    ctx.lineTo(x0 + cx, y0 + cy);
    ctx.lineTo(x0 + dx, y0 + dy);
    ctx.closePath();
  }

  /* ---------------- automatic anchor check ---------------- */
  function autoCheck(name, def) {
    const scan = SCAN[def.tex || name];
    if (!scan) return null;
    const s = def.s || 1;
    const bottom = scan.low + 1;                    // raw px, bottom of art
    const kind = def.kind;
    if (kind === 'ground' || kind === 'flat') return null;
    if (kind === 'free' && def.ax != null) {
      const dev = (bottom - def.ay) * s;            // + = art extends below anchor line (good)
      const tip = (def.foot[0] + def.foot[1]) * 8;  // anchor line -> footprint front tip, screen px
      if (dev < -3) return { level: 'bad', msg: `art base ends ${(-dev).toFixed(1)}px ABOVE its anchor line — this sprite will float` };
      if (dev > tip + 8) return { level: 'bad', msg: `art extends ${(dev - tip).toFixed(1)}px past the footprint front tip — sits too low / spills forward` };
      return { level: 'ok', msg: `base reaches ${dev.toFixed(1)}px below the anchor line (footprint front tip is ${tip}px below) — consistent` };
    }
    if (kind === 'free') {
      return { level: 'warn', msg: 'no measured anchor (ax/ay) — the engine guesses image bottom-centre = footprint centre. Registration unverified; prime suspect if this prop looks off.' };
    }
    if (kind === 'slab' && (!def.foot[0] || !def.foot[1])) {
      return { level: 'ok', msg: 'registration slice — anchored pixel-identically to its partner block, no ground contact of its own' };
    }
    // slab / backdrop: image bottom tip should be the last painted row
    const pad = (def.s ? ((Images[name].height - bottom) * s) : 0);
    if (pad > 3 && !def.dy) return { level: 'bad', msg: `art ends ${pad.toFixed(1)}px above the image bottom the renderer pins to the front corner — will float` };
    if (def.dy) return { level: 'ok', msg: `bottom tip pinned to front corner, then nudged dy=${def.dy}px (deliberate registration offset)` };
    return { level: 'ok', msg: 'bottom tip of the art = bottom of the image, pinned to the footprint front corner — consistent' };
  }

  /* ---------------- block card ---------------- */
  function buildCard(name) {
    const def = IsoBlocks[name];
    const s = def.s || 1;
    const [fw, fh] = def.foot;
    const imgName = def.tex || name;
    const img = Images[imgName];
    const mode = anchorMode(def);
    const card = el('div', 'card');

    // --- ground materials: texture swatch + explanation, no anchor math ---
    if (def.tex) {
      const cv = el('canvas', 'checker');
      const k = Math.min(240 / img.width, 150 / img.height, 1);
      cv.width = Math.round(img.width * k); cv.height = Math.round(img.height * k);
      const g = cv.getContext('2d');
      g.drawImage(img, 0, 0, cv.width, cv.height);
      // one 64x32 diamond to show the clip shape
      g.save();
      g.translate(cv.width / 2, cv.height / 2);
      g.beginPath();
      g.moveTo(0, -TH / 2); g.lineTo(TW / 2, 0); g.lineTo(0, TH / 2); g.lineTo(-TW / 2, 0);
      g.closePath();
      g.strokeStyle = C.footProp; g.lineWidth = 2; g.stroke();
      g.restore();
      card.appendChild(cv);
      card.appendChild(el('div', 'cap',
        `<b>${name}</b> · ground material (<span class="num">tex: ${imgName}</span>)<br>` +
        `foot ${fw}×${fh} supertile, walkable. The engine never draws this image directly: at load it ` +
        `clips one 64×32 diamond per cell out of the seamless texture (orange shape) and bakes the whole floor once.`));
      return card;
    }

    // --- local layout: origin = the ground point the sprite is pinned to ---
    const w = img.width * s, h = img.height * s;
    const dyOff = (def.dy || 0) * s;
    let sx0, sy0;              // sprite top-left rel ground point
    let ac, aw;                // anchor cell coords within footprint
    if (mode === 'back') { sx0 = -w / 2; sy0 = 0; ac = [0, 0]; }
    else if (mode === 'front') { sx0 = -w / 2; sy0 = -h + dyOff; ac = [fw, fh]; }
    else if (mode === 'free-ax') { sx0 = -def.ax * s; sy0 = -def.ay * s + dyOff; ac = [fw / 2, fh / 2]; }
    else { sx0 = -w / 2; sy0 = -h + dyOff; ac = [fw / 2, fh / 2]; }

    // bounds: sprite rect + footprint diamond + anchor marker
    let x0 = Math.min(sx0, 0), x1 = Math.max(sx0 + w, 0);
    let y0 = Math.min(sy0, -10), y1 = Math.max(sy0 + h, 10);
    const corners = [[0, 0], [fw, 0], [fw, fh], [0, fh]];
    for (const [a, b] of corners) {
      const [rx, ry] = rel(a - ac[0], b - ac[1]);
      x0 = Math.min(x0, rx); x1 = Math.max(x1, rx);
      y0 = Math.min(y0, ry - TH / 2); y1 = Math.max(y1, ry + TH / 2);
    }
    x0 -= 8; x1 += 8; y0 -= 8; y1 += 8;
    const bw = x1 - x0, bh = y1 - y0;
    const k = Math.min(280 / bw, 330 / bh, 1);

    const cv = el('canvas', 'checker');
    cv.width = Math.ceil(bw * k); cv.height = Math.ceil(bh * k);
    const g = cv.getContext('2d');
    g.setTransform(k, 0, 0, k, -x0 * k, -y0 * k);
    g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
    g.drawImage(img, sx0, sy0, w, h);

    // per-cell footprint diamonds, colour-coded
    const solids = solidCells(def);
    const isSolid = (a, b) => solids.some(([p, q]) => p === a && q === b);
    for (let b = 0; b < fh; b++) {
      for (let a = 0; a < fw; a++) {
        const [ox, oy] = rel(a - ac[0], b - ac[1]);
        diamondPath(g, ox, oy, 0, 0, 1, 1);
        const sol = isSolid(a, b);
        g.fillStyle = sol ? C.solidFill : C.walkFill;
        g.fill();
        g.strokeStyle = sol ? C.solidLine : C.walkLine;
        g.lineWidth = 1 / k;
        g.stroke();
      }
    }
    // whole-footprint outline
    if (fw && fh) {
      const [ox, oy] = rel(-ac[0], -ac[1]);
      diamondPath(g, ox, oy, 0, 0, fw, fh);
      g.strokeStyle = def.kind === 'backdrop' ? C.footBack : C.footProp;
      g.lineWidth = 2.5 / k;
      g.stroke();
    }
    // anchor line (horizontal, dotted, at the ground point's height)
    g.strokeStyle = C.anchor; g.lineWidth = 1.5 / k;
    g.setLineDash([5 / k, 4 / k]);
    g.beginPath(); g.moveTo(x0, 0); g.lineTo(x1, 0); g.stroke();
    // lowest painted pixel line (white dashed)
    const scan = SCAN[imgName];
    if (scan) {
      const lowY = sy0 + (scan.low + 1) * s;
      g.strokeStyle = 'rgba(255,255,255,0.9)';
      g.beginPath(); g.moveTo(x0, lowY); g.lineTo(x1, lowY); g.stroke();
    }
    g.setLineDash([]);
    // anchor crosshair
    g.strokeStyle = C.anchor; g.lineWidth = 2 / k;
    g.beginPath();
    g.moveTo(-9 / k, 0); g.lineTo(9 / k, 0);
    g.moveTo(0, -9 / k); g.lineTo(0, 9 / k);
    g.stroke();
    g.fillStyle = C.anchor;
    g.beginPath(); g.arc(0, 0, 3 / k, 0, Math.PI * 2); g.fill();

    // badge drawn into the canvas (top-right)
    const check = autoCheck(name, def);
    if (check && check.level !== 'ok') {
      g.setTransform(1, 0, 0, 1, 0, 0);
      const col = check.level === 'bad' ? '#e04030' : '#e09a30';
      g.fillStyle = col;
      g.beginPath(); g.arc(cv.width - 16, 16, 11, 0, Math.PI * 2); g.fill();
      g.fillStyle = '#fff'; g.font = 'bold 15px system-ui';
      g.textAlign = 'center'; g.fillText('!', cv.width - 16, 21);
    }

    const anchorDesc = {
      'free-ax': `anchor pixel (${def.ax}, ${def.ay}) → footprint centre`,
      'free-bc': 'image bottom-centre → footprint centre (no measured anchor)',
      'front': 'image bottom tip → footprint front corner',
      'back': 'image top → footprint back corner',
    }[mode];
    const checkHtml = check
      ? `<br><span class="badge-${check.level}">${check.level === 'ok' ? '✓' : '⚠'} ${check.msg}</span>`
      : '';
    card.appendChild(cv);
    card.appendChild(el('div', 'cap',
      `<b>${name}</b> · ${def.kind}${def.walk ? ' · walkable' : ''}<br>` +
      `<span class="num">foot ${fw}×${fh} · scale ${s}` +
      (def.solid ? ` · solid ${JSON.stringify(def.solid)}` : '') +
      (def.dy ? ` · dy ${def.dy}` : '') + `</span><br>` +
      `${anchorDesc}` + checkHtml));
    return { card, check };
  }

  async function buildInspector() {
    const holder = $('#cards');
    for (const name of Object.keys(IsoBlocks)) {
      const def = IsoBlocks[name];
      const imgName = def.tex || name;
      try { await ensureImage(imgName); } catch (e) {
        holder.appendChild(el('div', 'card', `<b>${name}</b> — image missing`));
        continue;
      }
      if (!SCAN[imgName]) SCAN[imgName] = scanImage(Images[imgName]);
      const built = buildCard(name);
      const card = built.card || built;
      if (built.check && built.check.level === 'bad') BADGES.bad.push(name);
      if (built.check && built.check.level === 'warn') BADGES.warn.push(name);
      card.id = 'block-' + name;
      holder.appendChild(card);
    }
  }

  /* ---------------- scene snapshot + X-ray ---------------- */
  function snapshot() {
    return {
      name: G.sceneName, W: G.W, H: G.H, bg: G.scene.bg || '#161014',
      solid: G.solid.slice(), spawn: G.scene.spawn.slice(),
      flats: G.flats.slice(), backdrops: G.backdrops.slice(),
      props: G.props.slice(),
      triggers: G.triggers.map(t => ({ cells: t.cells, to: t.to })),
      bake: G.groundBake,
    };
  }

  function sceneBounds(snap) {
    let xMin = sx(0, snap.H) - 24, xMax = sx(snap.W, 0) + 24;
    let yMin = -40, yMax = sy(snap.W, snap.H) + 28;
    for (const p of [...snap.flats, ...snap.backdrops, ...snap.props]) {
      const r = spriteRectWorld(p);
      if (!r) continue;
      xMin = Math.min(xMin, r[0] - 8); xMax = Math.max(xMax, r[0] + r[2] + 8);
      yMin = Math.min(yMin, r[1] - 8); yMax = Math.max(yMax, r[1] + r[3] + 8);
    }
    return { xMin, xMax, yMin, yMax };
  }

  function drawSpawnChar(ctx, snap) {
    const f = CharFrames.down[0];
    if (!f) return;
    const s = CHAR_H / f.height, w = f.width * s;
    ctx.drawImage(f, sx(snap.spawn[0], snap.spawn[1]) - w / 2,
                  sy(snap.spawn[0], snap.spawn[1]) - CHAR_H + 4, w, CHAR_H);
  }

  // full render through the engine's own draw path
  function renderFull(snap, cv, ox, oy) {
    const ctx = cv.getContext('2d');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = snap.bg;
    ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.setTransform(1, 0, 0, 1, ox, oy);
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    if (snap.bake) ctx.drawImage(snap.bake.cv, snap.bake.x, snap.bake.y);
    for (const p of snap.flats) drawBlock(ctx, p);
    for (const p of snap.backdrops) drawBlock(ctx, p);
    for (const p of snap.props) drawContactShadow(ctx, p);
    const ck = snap.spawn[0] + snap.spawn[1];
    let drawn = false;
    for (const p of snap.props) {
      if (!drawn && ck < sortKey(p)) { drawSpawnChar(ctx, snap); drawn = true; }
      drawBlock(ctx, p);
    }
    if (!drawn) drawSpawnChar(ctx, snap);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  const LAYERS = [
    ['grid', 'grid', true],
    ['cells', 'walkable / solid', true],
    ['foot', 'footprints', true],
    ['anchors', 'anchors + names', false],
    ['keys', 'sort keys', false],
    ['doors', 'spawn + doors', true],
  ];

  function renderOverlay(snap, cv, ox, oy, on, bg) {
    const ctx = cv.getContext('2d');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, cv.width, cv.height);
    if (bg) { ctx.fillStyle = bg; ctx.fillRect(0, 0, cv.width, cv.height); }
    ctx.setTransform(1, 0, 0, 1, ox, oy);

    if (on.cells) {
      for (let j = 0; j < snap.H; j++) {
        for (let i = 0; i < snap.W; i++) {
          diamondPath(ctx, sx(i, j), sy(i, j), 0, 0, 1, 1);
          ctx.fillStyle = snap.solid[j * snap.W + i] ? C.solidFill : C.walkFill;
          ctx.fill();
        }
      }
    }
    if (on.grid) {
      ctx.strokeStyle = C.grid; ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i <= snap.W; i++) { ctx.moveTo(sx(i, 0), sy(i, 0)); ctx.lineTo(sx(i, snap.H), sy(i, snap.H)); }
      for (let j = 0; j <= snap.H; j++) { ctx.moveTo(sx(0, j), sy(0, j)); ctx.lineTo(sx(snap.W, j), sy(snap.W, j)); }
      ctx.stroke();
    }
    if (on.foot) {
      for (const list of [snap.backdrops, snap.props, snap.flats]) {
        for (const p of list) {
          const [fw, fh] = p.def.foot;
          if (!fw || !fh) continue;
          diamondPath(ctx, sx(p.i, p.j), sy(p.i, p.j), 0, 0, fw, fh);
          ctx.strokeStyle = list === snap.backdrops ? C.footBack : C.footProp;
          ctx.lineWidth = 2;
          ctx.stroke();
          // solid subset marked inside the footprint
          for (const [a, b] of solidCells(p.def)) {
            diamondPath(ctx, sx(p.i + a, p.j + b), sy(p.i + a, p.j + b), 0, 0, 1, 1);
            ctx.strokeStyle = C.solidLine; ctx.lineWidth = 1.4;
            ctx.stroke();
          }
        }
      }
    }
    if (on.anchors || on.keys) {
      ctx.textAlign = 'center';
      for (const list of [snap.backdrops, snap.props]) {
        for (const p of list) {
          const def = p.def, mode = anchorMode(def);
          const [ai, aj] = mode === 'front'
            ? [p.i + def.foot[0], p.j + def.foot[1]]
            : [p.i + def.foot[0] / 2, p.j + def.foot[1] / 2];
          const px = sx(ai, aj), py = sy(ai, aj);
          if (on.anchors) {
            ctx.fillStyle = C.anchor;
            ctx.beginPath(); ctx.arc(px, py, 4, 0, Math.PI * 2); ctx.fill();
            ctx.font = 'bold 13px system-ui';
            ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.85)';
            const label = `${p.name} ${p.i},${p.j}`;
            ctx.strokeText(label, px, py + 16);
            ctx.fillStyle = '#ffe9b0';
            ctx.fillText(label, px, py + 16);
          }
          if (on.keys && list === snap.props) {
            ctx.font = 'bold 15px system-ui';
            ctx.lineWidth = 3.5; ctx.strokeStyle = 'rgba(0,0,0,0.9)';
            ctx.strokeText(sortKey(p).toFixed(1), px, py - 6);
            ctx.fillStyle = '#fff';
            ctx.fillText(sortKey(p).toFixed(1), px, py - 6);
          }
        }
      }
      ctx.textAlign = 'left';
    }
    if (on.doors) {
      ctx.textAlign = 'center';
      for (const tr of snap.triggers) {
        for (const [a, b] of tr.cells) {
          diamondPath(ctx, sx(a, b), sy(a, b), 0, 0, 1, 1);
          ctx.fillStyle = C.trig; ctx.fill();
        }
        const [a, b] = tr.cells[0];
        ctx.font = 'bold 14px system-ui';
        ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.9)';
        ctx.strokeText('door → ' + tr.to, sx(a + 0.5, b + 0.5), sy(a + 0.5, b + 0.5) - 12);
        ctx.fillStyle = '#aee6ff';
        ctx.fillText('door → ' + tr.to, sx(a + 0.5, b + 0.5), sy(a + 0.5, b + 0.5) - 12);
      }
      // spawn
      const [sxp, syp] = snap.spawn;
      ctx.fillStyle = C.spawn;
      ctx.beginPath(); ctx.arc(sx(sxp, syp), sy(sxp, syp), 5, 0, Math.PI * 2); ctx.fill();
      ctx.font = 'bold 13px system-ui';
      ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.9)';
      ctx.strokeText('spawn', sx(sxp, syp), sy(sxp, syp) + 18);
      ctx.fillStyle = C.spawn;
      ctx.fillText('spawn', sx(sxp, syp), sy(sxp, syp) + 18);
      ctx.textAlign = 'left';
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  function buildXray(snap) {
    const { xMin, xMax, yMin, yMax } = sceneBounds(snap);
    const w = Math.ceil(xMax - xMin), h = Math.ceil(yMax - yMin);
    const ox = -xMin, oy = -yMin;

    const sec = el('div');
    sec.appendChild(el('h3', null,
      `${snap.name}.json — ${snap.W}×${snap.H} cells, ${snap.props.length} sorted props, ` +
      `${snap.backdrops.length} backdrop(s), ${snap.triggers.length} door trigger(s)`));

    const toggles = el('div', 'toggles');
    const boxes = {};
    for (const [key, label, def] of LAYERS) {
      const lab = el('label');
      const cb = el('input');
      cb.type = 'checkbox'; cb.checked = def;
      boxes[key] = cb;
      lab.appendChild(cb);
      lab.appendChild(document.createTextNode(' ' + label));
      toggles.appendChild(lab);
    }
    sec.appendChild(toggles);

    const row = el('div', 'row');
    const stackA = el('div', 'stack');
    const base = el('canvas'); base.width = w; base.height = h;
    const over = el('canvas', 'over'); over.width = w; over.height = h;
    stackA.appendChild(base); stackA.appendChild(over);
    stackA.appendChild(el('div', 'viewcap', 'Full render (engine draw path) + metadata overlays'));
    const stackB = el('div', 'stack');
    const meta = el('canvas'); meta.width = w; meta.height = h;
    stackB.appendChild(meta);
    stackB.appendChild(el('div', 'viewcap', 'Metadata only — same camera, no art. What the engine believes.'));
    row.appendChild(stackA); row.appendChild(stackB);
    sec.appendChild(row);

    renderFull(snap, base, ox, oy);
    const redraw = () => {
      const on = {};
      for (const k of Object.keys(boxes)) on[k] = boxes[k].checked;
      renderOverlay(snap, over, ox, oy, on);
    };
    for (const k of Object.keys(boxes)) boxes[k].addEventListener('change', redraw);
    redraw();

    // metadata-only view: dark ground plane + all layers always on
    renderOverlay(snap, meta, ox, oy,
      { grid: true, cells: true, foot: true, anchors: true, keys: false, doors: true }, '#161019');

    $('#xrays').appendChild(sec);
    return { base, over, meta, ox, oy, redraw, boxes };
  }

  /* ---------------- workflow section ---------------- */
  function pre(txt) { const p = el('pre'); p.textContent = txt; return p; }

  function buildWorkflow(squareView, squareJsonText) {
    const wf = $('#wf');

    // step 1 — the sheet
    const s1 = el('div', 'card wfstep');
    s1.appendChild(el('h3', null, 'Step 1 — paint a sheet'));
    const sheet = el('img', 'shot');
    sheet.src = 'assets/iso/sheets/out-props-raw.png';
    sheet.style.maxWidth = '420px';
    s1.appendChild(sheet);
    s1.appendChild(el('div', 'cap',
      'A real generated sheet (<span class="num">assets/iso/sheets/out-props-raw.png</span>): a 3×3 grid on a ' +
      'magenta key. Each prop is painted standing on a throwaway dirt slab so the painting has believable ground contact.'));

    // step 2 — sliced blocks
    const s2 = el('div', 'card wfstep');
    s2.appendChild(el('h3', null, 'Step 2 — slice &amp; de-slab'));
    const strip = el('div', 'row');
    for (const n of ['well', 'lamppost', 'bench', 'barrel']) {
      const im = el('img', 'checker');
      im.src = 'assets/iso/blocks/' + n + '.png';
      im.style.maxHeight = '120px';
      im.title = n;
      strip.appendChild(im);
    }
    s2.appendChild(strip);
    s2.appendChild(el('div', 'cap',
      'Each cell is cut out, the magenta and the throwaway slab are removed, and the result is a transparent ' +
      'PNG in <span class="num">assets/iso/blocks/</span> (here: well, lamppost, bench, barrel — the actual files).'));

    // step 3 — measure (metadata)
    const s3 = el('div', 'card wfstep');
    s3.appendChild(el('h3', null, 'Step 3 — measure the base'));
    const built = buildCard('barrel');
    s3.appendChild(built.card ? built.card : built);
    s3.appendChild(el('div', 'cap',
      'The centre of the painted base diamond becomes the <b>anchor</b> (yellow cross), recorded with the ' +
      'footprint and collision rules. This is the real metadata for the barrel:'));
    s3.appendChild(pre(
      "// registry.js\n'barrel': " + JSON.stringify(IsoBlocks.barrel) + '\n\n' +
      '// blocks-metrics.json\n"barrel": ' + JSON.stringify(METRICS.barrel || {}, null, 1)));

    // step 4 — place (scene JSON + the very cells it produces)
    const s4 = el('div', 'card');
    s4.appendChild(el('h3', null, 'Step 4 — place blocks in a scene'));
    let snippet = '// square.json (excerpt — real entries)\n"blocks": [\n';
    try {
      const sq = JSON.parse(squareJsonText);
      const pick = sq.blocks.filter(([n, i, j]) =>
        i >= 17 && j <= 11 && ['cottage-teal', 'barrel', 'crates', 'tree-a', 'stall-green', 'tree-round'].includes(n));
      snippet += pick.map(e => '  ' + JSON.stringify(e)).join(',\n');
      snippet += '\n  …\n]';
    } catch (e) { snippet += '  (could not parse scene json)\n]'; }
    const row4 = el('div', 'row');
    row4.appendChild(pre(snippet));
    if (squareView) {
      const crop = el('canvas');
      const CX0 = 120, CY0 = -160, CW = 780, CH = 740, K4 = 0.72;
      crop.width = CW * K4; crop.height = CH * K4;
      crop.getContext('2d').drawImage(squareView.base,
        CX0 + squareView.ox, CY0 + squareView.oy, CW, CH, 0, 0, CW * K4, CH * K4);
      crop.style.maxWidth = '440px'; crop.style.borderRadius = '6px';
      const wrap = el('div');
      wrap.appendChild(crop);
      wrap.appendChild(el('div', 'cap',
        'The same entries rendered by the engine (crop of the full square render below): cottage-teal at ' +
        '(21,3), the barrel at (20,5) and crates at (21,8) behind it, tree-a at (23,0), stall-green at (17,10).'));
      row4.appendChild(wrap);
    }
    s4.appendChild(row4);
    s4.appendChild(el('div', 'cap',
      'A scene is a charmap of 2×2 ground supertiles plus a flat list of <span class="num">[block, i, j]</span> ' +
      'placements. No pixel positions anywhere — the metadata from step 3 decides where pixels land.'));

    // step 5 — render
    const s5 = el('div', 'card wfstep');
    s5.appendChild(el('h3', null, 'Step 5 — render'));
    s5.appendChild(el('div', 'cap',
      'At load the engine bakes the floor once (diamond-clipped texture fills), then each frame draws: floor → ' +
      'flat decals → <b>backdrops</b> (buildings — always first, therefore always behind) → contact shadows → ' +
      'sorted props with the character slotted in by her <span class="num">x+y</span> key. ' +
      'See the full result in the Scene X-ray below.'));

    for (const s of [s1, s2, s3, s4, s5]) wf.appendChild(s);
  }

  /* ---------------- boot ---------------- */
  async function main() {
    await wait(() => window.__iso && __iso.groundBake && CharFrames.down.length);
    METRICS = await (await fetch('assets/iso/blocks-metrics.json')).json();
    const squareJsonText = await (await fetch('assets/iso/scenes/square.json')).text();

    $('#status').textContent = 'engine loaded — building views…';

    const snapSquare = snapshot();
    await buildInspector();
    const squareView = buildXray(snapSquare);
    buildWorkflow(squareView, squareJsonText);

    await loadScene('bakery-int');
    const snapBak = snapshot();
    buildXray(snapBak);

    $('#status').textContent =
      `live · automatic anchor check: ${BADGES.bad.length} mismatch(es), ${BADGES.warn.length} unmeasured anchor(s).`;
    window.__explain = { done: true, badges: BADGES, scenes: ['square', 'bakery-int'] };
  }

  main().catch(e => {
    $('#status').textContent = 'failed: ' + e.message;
    console.error(e);
  });
})();
