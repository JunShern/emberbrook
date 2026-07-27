'use strict';
/* ============================================================
   ISO-EXPLAIN — registration-mark proving round.
   Standalone (no engine): everything on this page is drawn from
   assets/iso/blocks9/sheet.png + blocks9-metrics.json, i.e. the
   raw generated sheet and what tools/slice_blocks9.py measured
   from the magenta marks. Three views per prop:
     a) raw sheet crop — the prop standing on its mark
     b) keyed sprite on checkerboard + the fitted mark (ground
        contact patch) + measured anchor
     c) KEY VIEW — the sprite with the iso grid drawn on top of
        it from the MEASURED anchor + cell size: red = declared
        footprint cells, faint grey = neighbor cells.
   ============================================================ */
(() => {

  const ORDER = ['barrel', 'crate', 'lamppost', 'bench', 'planter', 'firewood',
                 'stall', 'well', 'tree'];
  const $ = s => document.querySelector(s);
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };
  const loadImage = src => new Promise((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => rej(new Error('image failed: ' + src));
    im.src = src;
  });

  // iso basis from a measured cell size (2:1)
  const basis = c => [[c / 2, c / 4], [-c / 2, c / 4]];

  function cellPath(g, ox, oy, e1, e2, a, b) {
    const p = (i, j) => [ox + i * e1[0] + j * e2[0], oy + i * e1[1] + j * e2[1]];
    const q = [p(a, b), p(a + 1, b), p(a + 1, b + 1), p(a, b + 1)];
    g.beginPath();
    g.moveTo(q[0][0], q[0][1]);
    for (let k = 1; k < 4; k++) g.lineTo(q[k][0], q[k][1]);
    g.closePath();
  }

  function view(label, w, h, k, checker, draw) {
    const box = el('div', 'view');
    const cv = el('canvas', checker ? 'checker' : null);
    cv.width = Math.ceil(w * k);
    cv.height = Math.ceil(h * k);
    const g = cv.getContext('2d');
    g.setTransform(k, 0, 0, k, 0, 0);
    g.imageSmoothingEnabled = true;
    g.imageSmoothingQuality = 'high';
    draw(g, k);
    box.appendChild(cv);
    box.appendChild(el('div', 'lbl', label));
    return box;
  }

  function anchorDot(g, k, x, y) {
    g.fillStyle = '#ffd866';
    g.beginPath(); g.arc(x, y, 4 / k, 0, Math.PI * 2); g.fill();
    g.strokeStyle = '#ffd866'; g.lineWidth = 1.6 / k;
    g.beginPath();
    g.moveTo(x - 10 / k, y); g.lineTo(x + 10 / k, y);
    g.moveTo(x, y - 10 / k); g.lineTo(x, y + 10 / k);
    g.stroke();
  }

  function caption(name, m) {
    const [dw, dh] = m.declared, [mw, mh] = m.measured || [0, 0];
    const shapeOff = m.axisErr > 0.15;
    const oh = m.overhang || {};
    const spill = oh.baseSpillPx || 0;
    const bits = [];
    bits.push(`declared <span class="num">${dw}×${dh}</span> · ` +
              `measured <span class="num">${mw}×${mh}</span> (cells of ` +
              `<span class="num">${m.cellPx}px</span>, per-axis ` +
              `<span class="num">${m.cellPxPerAxis[0]}/${m.cellPxPerAxis[1]}</span>) · ` +
              `anchor <span class="num">(${m.anchorSprite[0]}, ${m.anchorSprite[1]})</span> · ` +
              `mark-fit confidence <span class="num">${m.confidence.toFixed(2)}</span>`);
    if (!shapeOff && m.confidence >= 0.9) {
      bits.push(`<span class="ok">✓ mark matches the declared footprint; ` +
                `base spill ${spill.toFixed(1)}px — art sits in its claimed cells.</span>`);
    } else if (shapeOff) {
      bits.push(`<span class="bad">✗ painted mark does not match the declaration: ` +
                `principal axis ${m.markAxisDeg}° (a true 2:1 strip lies at ±26.6°), ` +
                `per-axis cell sizes disagree ${m.cellPxPerAxis[0]} vs ${m.cellPxPerAxis[1]}px. ` +
                `The art registers on the pad the model painted — an elongated strip mirrored ` +
                `against the declared axis — so the declared ${dw}×${dh} overlay (red) misses it. ` +
                `Measured, not guessed: this is the defect the convention exists to catch.</span>`);
    } else {
      bits.push(`<span class="warn">⚠ mark fit degraded (confidence ` +
                `${m.confidence.toFixed(2)}) — treat the measurement with care.</span>`);
    }
    const legit = { stall: 'awning', tree: 'canopy' }[name];
    if ((oh.left > 4 || oh.right > 4) && legit) {
      bits.push(`overhang L ${oh.left}px / R ${oh.right}px beyond the footprint — the ${legit}; ` +
                `legitimate visual overhang, not a registration error.`);
    } else if (oh.left > 4 || oh.right > 4) {
      bits.push(`<span class="warn">⚠ art extends L ${oh.left}px / R ${oh.right}px past the ` +
                `mark — check whether that is body or acceptable dressing.</span>`);
    }
    if (spill > 4) {
      bits.push(`<span class="bad">✗ base spill: painted art reaches ${spill.toFixed(1)}px below ` +
                `the mark's front corner — the base leaks out of the footprint.</span>`);
    }
    return bits.join('<br>');
  }

  function buildRow(name, m, sheet, sprite) {
    const row = el('div', 'prop');
    row.id = 'prop-' + name;
    row.appendChild(el('h2', null,
      `${name} — ${m.declared[0]}×${m.declared[1]}`));
    const views = el('div', 'views');
    const [rx, ry, rw, rh] = m.region;

    // (a) raw sheet crop
    const ka = Math.min(1, 250 / rw);
    views.appendChild(view('a · raw sheet crop (prop on its mark)', rw, rh, ka, false,
      g => g.drawImage(sheet, rx, ry, rw, rh, 0, 0, rw, rh)));

    if (!m.fitSprite) {
      views.appendChild(el('div', 'lbl', 'mark missing — nothing to measure'));
      row.appendChild(views);
      row.appendChild(el('div', 'cap', m.error || 'mark not found'));
      return row;
    }

    const w = sprite.width, h = sprite.height;
    const f = m.fitSprite, A = m.anchorSprite;

    // (b) keyed sprite + fitted ground patch + anchor
    {
      const pad = 12;
      const xs = [0, w, f.T[0], f.R[0], f.B[0], f.L[0]];
      const ys = [0, h, f.T[1], f.R[1], f.B[1], f.L[1]];
      const x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad;
      const y0 = Math.min(...ys) - pad, y1 = Math.max(...ys) + pad;
      const k = Math.min(1, 250 / (x1 - x0), 330 / (y1 - y0));
      views.appendChild(view('b · cut-out sprite + detected ground patch', x1 - x0, y1 - y0, k, true,
        g => {
          g.translate(-x0, -y0);
          g.drawImage(sprite, 0, 0);
          g.setLineDash([5 / k, 4 / k]);
          g.strokeStyle = 'rgba(255,255,255,0.9)';
          g.lineWidth = 1.6 / k;
          g.beginPath();
          g.moveTo(f.T[0], f.T[1]); g.lineTo(f.R[0], f.R[1]);
          g.lineTo(f.B[0], f.B[1]); g.lineTo(f.L[0], f.L[1]);
          g.closePath(); g.stroke();
          g.setLineDash([]);
          anchorDot(g, k, A[0], A[1]);
        }));
    }

    // (c) KEY VIEW — measured anchor + declared footprint grid over the art
    {
      const [fw, fh] = m.declared;
      const [e1, e2] = basis(m.cellPx);
      // grid origin: back corner of the declared footprint, from the anchor
      const ox = A[0] - (fw * e1[0] + fh * e2[0]) / 2;
      const oy = A[1] - (fw * e1[1] + fh * e2[1]) / 2;
      const RING = 2;
      let x0 = 0, y0 = 0, x1 = w, y1 = h;
      for (const [a, b] of [[-RING, -RING], [fw + RING, -RING],
                            [fw + RING, fh + RING], [-RING, fh + RING]]) {
        x0 = Math.min(x0, ox + a * e1[0] + b * e2[0]);
        x1 = Math.max(x1, ox + a * e1[0] + b * e2[0]);
        y0 = Math.min(y0, oy + a * e1[1] + b * e2[1]);
        y1 = Math.max(y1, oy + a * e1[1] + b * e2[1]);
      }
      x0 -= 8; y0 -= 8; x1 += 8; y1 += 8;
      const k = Math.min(1, 420 / (x1 - x0), 380 / (y1 - y0));
      views.appendChild(view('c · KEY VIEW — measured grid over the art (red = declared footprint)',
        x1 - x0, y1 - y0, k, true,
        g => {
          g.translate(-x0, -y0);
          g.drawImage(sprite, 0, 0);
          // neighbor rings, faint
          g.strokeStyle = 'rgba(240,230,210,0.30)';
          g.lineWidth = 1 / k;
          for (let b = -RING; b < fh + RING; b++) {
            for (let a = -RING; a < fw + RING; a++) {
              if (a >= 0 && a < fw && b >= 0 && b < fh) continue;
              cellPath(g, ox, oy, e1, e2, a, b);
              g.stroke();
            }
          }
          // declared footprint cells, red
          g.strokeStyle = 'rgba(255,80,64,0.95)';
          g.lineWidth = 2 / k;
          for (let b = 0; b < fh; b++) {
            for (let a = 0; a < fw; a++) {
              cellPath(g, ox, oy, e1, e2, a, b);
              g.stroke();
            }
          }
          anchorDot(g, k, A[0], A[1]);
        }));
    }

    row.appendChild(views);
    row.appendChild(el('div', 'cap', caption(name, m)));
    return row;
  }

  async function main() {
    const M = await (await fetch('assets/iso/blocks9/blocks9-metrics.json')).json();
    const sheet = await loadImage('assets/iso/blocks9/sheet.png');
    const holder = $('#rows');
    let ok = 0, bad = 0;
    for (const name of ORDER) {
      const m = M[name];
      let sprite = null;
      if (m.sprite) sprite = await loadImage('assets/iso/blocks9/' + m.sprite);
      holder.appendChild(buildRow(name, m, sheet, sprite));
      (m.confidence >= 0.9 && m.axisErr <= 0.15 ? ok++ : bad++);
    }
    $('#status').textContent =
      `measured live from blocks9-metrics.json: ${ok}/9 registered clean, ${bad}/9 flagged.`;
    window.__explain = { done: true, ok, bad };
  }

  main().catch(e => {
    $('#status').textContent = 'failed: ' + e.message;
    console.error(e);
  });
})();
