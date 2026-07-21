// walkfirst.mjs — walkability-first layout guide renderer (standalone experiment).
//
// Author the walkable layout BEFORE the painting: hand-specify walkable polygons
// and typed markers in a small JSON spec, render a clean guide image to feed the
// image model as a generation input, plus a labeled overlay for human review.
//
// Usage:
//   node tools/walkfirst.mjs <spec.json> <guide-out.png> [<overlay-out.png>]
//
// Spec format (JSON):
// {
//   "size": [1344, 768],              // optional, defaults to 1344x768
//   "walkable": [                     // filled polygons, all one bold color
//     { "label": "main deck", "points": [[x,y], [x,y], ...] }
//   ],
//   "markers": [                      // typed colored dots
//     { "type": "exit",     "label": "to dellhollow", "pos": [x,y] },
//     { "type": "door",     "label": "smokehouse",    "pos": [x,y] },
//     { "type": "landmark", "label": "fish rack",     "pos": [x,y] }
//   ]
// }
//
// Colors (fixed vocabulary, keep prompts consistent with these):
//   background        #26262E  flat dark slate
//   walkable fill     #00CC44  bold green
//   exit markers      #FF2E2E  red
//   door markers      #FFD400  yellow
//   landmark markers  #00B4FF  cyan
//
// The guide is minimal on purpose: flat background, filled walkable regions,
// filled marker circles. The overlay adds outlines, rings, and text labels and
// is NEVER fed to the model — review only. Prints walkable coverage % to stdout.
import fs from 'fs';
import zlib from 'zlib';

const COLORS = {
  bg: [0x26, 0x26, 0x2e],
  walk: [0x00, 0xcc, 0x44],
  exit: [0xff, 0x2e, 0x2e],
  door: [0xff, 0xd4, 0x00],
  landmark: [0x00, 0xb4, 0xff],
};
const MARKER_R = 16;

// ---------- tiny 5x7 font (uppercase, digits, minimal punctuation) ----------
const FONT = {
  A:'0E,11,11,1F,11,11,11', B:'1E,11,11,1E,11,11,1E', C:'0E,11,10,10,10,11,0E',
  D:'1E,11,11,11,11,11,1E', E:'1F,10,10,1E,10,10,1F', F:'1F,10,10,1E,10,10,10',
  G:'0E,11,10,17,11,11,0F', H:'11,11,11,1F,11,11,11', I:'0E,04,04,04,04,04,0E',
  J:'01,01,01,01,11,11,0E', K:'11,12,14,18,14,12,11', L:'10,10,10,10,10,10,1F',
  M:'11,1B,15,15,11,11,11', N:'11,19,15,13,11,11,11', O:'0E,11,11,11,11,11,0E',
  P:'1E,11,11,1E,10,10,10', Q:'0E,11,11,11,15,12,0D', R:'1E,11,11,1E,14,12,11',
  S:'0F,10,10,0E,01,01,1E', T:'1F,04,04,04,04,04,04', U:'11,11,11,11,11,11,0E',
  V:'11,11,11,11,11,0A,04', W:'11,11,11,15,15,1B,11', X:'11,0A,04,04,04,0A,11',
  Y:'11,11,0A,04,04,04,04', Z:'1F,01,02,04,08,10,1F',
  '0':'0E,11,13,15,19,11,0E', '1':'04,0C,04,04,04,04,0E', '2':'0E,11,01,06,08,10,1F',
  '3':'0E,11,01,06,01,11,0E', '4':'02,06,0A,12,1F,02,02', '5':'1F,10,1E,01,01,11,0E',
  '6':'06,08,10,1E,11,11,0E', '7':'1F,01,02,04,08,08,08', '8':'0E,11,11,0E,11,11,0E',
  '9':'0E,11,11,0F,01,02,0C', ' ':'00,00,00,00,00,00,00', '-':'00,00,00,1F,00,00,00',
  ':':'00,04,00,00,00,04,00', '.':'00,00,00,00,00,0C,0C', '/':'01,01,02,04,08,10,10',
};

class Img {
  constructor(w, h, rgb) {
    this.w = w; this.h = h;
    this.d = Buffer.alloc(w * h * 3);
    for (let i = 0; i < w * h; i++) this.d.set(rgb, i * 3);
  }
  set(x, y, rgb) {
    x = Math.floor(x); y = Math.floor(y);
    if (x < 0 || y < 0 || x >= this.w || y >= this.h) return;
    this.d.set(rgb, (y * this.w + x) * 3);
  }
  fillPoly(pts, rgb) {
    const ys = pts.map(p => p[1]);
    const y0 = Math.max(0, Math.floor(Math.min(...ys))), y1 = Math.min(this.h - 1, Math.ceil(Math.max(...ys)));
    for (let y = y0; y <= y1; y++) {
      const yc = y + 0.5, xs = [];
      for (let i = 0; i < pts.length; i++) {
        const [ax, ay] = pts[i], [bx, by] = pts[(i + 1) % pts.length];
        if ((ay <= yc && by > yc) || (by <= yc && ay > yc))
          xs.push(ax + (yc - ay) / (by - ay) * (bx - ax));
      }
      xs.sort((a, b) => a - b);
      for (let k = 0; k + 1 < xs.length; k += 2)
        for (let x = Math.max(0, Math.round(xs[k])); x <= Math.min(this.w - 1, Math.round(xs[k + 1])); x++)
          this.set(x, y, rgb);
    }
  }
  fillCircle(cx, cy, r, rgb) {
    for (let y = Math.floor(cy - r); y <= cy + r; y++)
      for (let x = Math.floor(cx - r); x <= cx + r; x++)
        if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r) this.set(x, y, rgb);
  }
  ring(cx, cy, r, w, rgb) {
    for (let y = Math.floor(cy - r - w); y <= cy + r + w; y++)
      for (let x = Math.floor(cx - r - w); x <= cx + r + w; x++) {
        const d = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
        if (d >= r && d <= r + w) this.set(x, y, rgb);
      }
  }
  line(a, b, r, rgb) {
    const dx = b[0] - a[0], dy = b[1] - a[1], n = Math.max(1, Math.ceil(Math.hypot(dx, dy)));
    for (let i = 0; i <= n; i++)
      this.fillCircle(a[0] + dx * i / n, a[1] + dy * i / n, r, rgb);
  }
  strokePoly(pts, r, rgb) {
    for (let i = 0; i < pts.length; i++) this.line(pts[i], pts[(i + 1) % pts.length], r, rgb);
  }
  text(x, y, str, rgb, scale = 2) {
    let cx = x;
    for (const ch of str.toUpperCase()) {
      const rows = (FONT[ch] || FONT[' ']).split(',').map(h => parseInt(h, 16));
      for (let ry = 0; ry < 7; ry++)
        for (let rx = 0; rx < 5; rx++)
          if (rows[ry] & (1 << (4 - rx)))
            for (let sy = 0; sy < scale; sy++)
              for (let sx = 0; sx < scale; sx++) {
                this.set(cx + rx * scale + sx + 1, y + ry * scale + sy + 1, [0, 0, 0]); // shadow
                this.set(cx + rx * scale + sx, y + ry * scale + sy, rgb);
              }
      cx += 6 * scale;
    }
  }
  toPNG() {
    const raw = Buffer.alloc((this.w * 3 + 1) * this.h);
    for (let y = 0; y < this.h; y++) {
      raw[y * (this.w * 3 + 1)] = 0; // filter none
      this.d.copy(raw, y * (this.w * 3 + 1) + 1, y * this.w * 3, (y + 1) * this.w * 3);
    }
    const chunk = (type, data) => {
      const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
      const td = Buffer.concat([Buffer.from(type), data]);
      const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td) >>> 0);
      return Buffer.concat([len, td, crc]);
    };
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(this.w, 0); ihdr.writeUInt32BE(this.h, 4);
    ihdr[8] = 8; ihdr[9] = 2; // 8-bit RGB
    return Buffer.concat([
      Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
      chunk('IHDR', ihdr),
      chunk('IDAT', zlib.deflateSync(raw, { level: 9 })),
      chunk('IEND', Buffer.alloc(0)),
    ]);
  }
}
const CRC_T = new Int32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c;
});
function crc32(buf) {
  let c = -1;
  for (const b of buf) c = CRC_T[(c ^ b) & 0xff] ^ (c >>> 8);
  return ~c;
}

// ---------- main ----------
const [specPath, guideOut, overlayOut] = process.argv.slice(2);
if (!specPath || !guideOut) {
  console.error('usage: node tools/walkfirst.mjs <spec.json> <guide-out.png> [<overlay-out.png>]');
  process.exit(1);
}
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const [W, H] = spec.size || [1344, 768];

const guide = new Img(W, H, COLORS.bg);
for (const poly of spec.walkable) guide.fillPoly(poly.points, COLORS.walk);
for (const m of spec.markers || []) {
  const c = COLORS[m.type];
  if (!c) { console.error(`unknown marker type: ${m.type}`); process.exit(1); }
  guide.fillCircle(m.pos[0], m.pos[1], MARKER_R, c);
}
fs.writeFileSync(guideOut, guide.toPNG());

// coverage stat
let walk = 0;
for (let i = 0; i < W * H; i++)
  if (guide.d[i * 3] === COLORS.walk[0] && guide.d[i * 3 + 1] === COLORS.walk[1] && guide.d[i * 3 + 2] === COLORS.walk[2]) walk++;
console.log(`wrote ${guideOut} — walkable coverage ${(100 * walk / (W * H)).toFixed(1)}%`);

if (overlayOut) {
  const ov = new Img(W, H, COLORS.bg);
  for (const poly of spec.walkable) ov.fillPoly(poly.points, COLORS.walk);
  for (const poly of spec.walkable) {
    ov.strokePoly(poly.points, 1.5, [255, 255, 255]);
    const cx = poly.points.reduce((s, p) => s + p[0], 0) / poly.points.length;
    const cy = poly.points.reduce((s, p) => s + p[1], 0) / poly.points.length;
    ov.text(cx - 3 * poly.label.length * 2, cy - 7, poly.label, [255, 255, 255]);
  }
  for (const m of spec.markers || []) {
    ov.fillCircle(m.pos[0], m.pos[1], MARKER_R, COLORS[m.type]);
    ov.ring(m.pos[0], m.pos[1], MARKER_R + 2, 2.5, [255, 255, 255]);
    const label = `${m.type}: ${m.label}`;
    const tx = Math.min(Math.max(4, m.pos[0] - 3 * label.length * 2), W - label.length * 12 - 4);
    const ty = m.pos[1] > H - 60 ? m.pos[1] - MARKER_R - 24 : m.pos[1] + MARKER_R + 8;
    ov.text(tx, ty, label, [255, 255, 255]);
  }
  fs.writeFileSync(overlayOut, ov.toPNG());
  console.log(`wrote ${overlayOut}`);
}
