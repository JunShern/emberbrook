// [groundv2] Deck-platform EDGE sprites for the auto-placed pier system.
// Small keyed sprites, engine-placed by rule (so registration precision is not
// critical) — but Style B + clean keying still law. Generated on a flat MAGENTA
// chroma field; key_deckedges.py strips it to transparency.
//   deck-fascia : the SIDE / cut edge of the decking — a horizontal weathered
//                 plank-edge + beam band, seen straight-on (engine shears it onto
//                 each iso front face).
//   deck-stilt  : a single weathered timber post descending into water, with a
//                 faint waterline splash at its foot.
// Usage: node tools/gen_deckedges.mjs [idFilter]
import fs from 'fs';
import path from 'path';

const root = path.join(import.meta.dirname, '..');
const env = Object.fromEntries(
  fs.readFileSync(path.join(root, '.env'), 'utf8').split('\n')
    .filter(l => l.includes('=') && !l.trim().startsWith('#'))
    .map(l => [l.slice(0, l.indexOf('=')).trim(),
               l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, '')]));
const KEY = env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;
if (!KEY) { console.error('no GEMINI_API_KEY'); process.exit(1); }

const OUT = path.join(root, 'public/assets/iso/dellhollow/raw');
fs.mkdirSync(OUT, { recursive: true });

const STYLE = ' STYLE B, cel-painterly, warm hand-painted autumn-festival RPG look: soft cel '
  + 'shading in 2-3 tone steps, every edge a DARKENED shade of its own LOCAL color (never '
  + 'pure black), no banding, soft warm dusk light. The object fills the frame. NO ground, '
  + 'NO water, NO shadow on the background, NO other objects, NO text.';
const KEYBG = ' The entire background behind the object is one FLAT PURE MAGENTA (#FF00FF) fill, '
  + 'absolutely uniform, so it can be keyed out — do not put magenta anywhere on the object itself.';

const ITEMS = [
  ['deck-fascia', `The SIDE EDGE of a weathered timber wharf deck seen straight-on from the front: a horizontal band showing the cut ENDS/edge of the deck planks along the top and a stout weathered support BEAM below them, warm muted painted timber with soft paint-fleck weathering, gentle grain, a wide landscape strip. Straight horizontal band, front-on elevation (NOT top-down, NOT angled).${STYLE}${KEYBG}`],
  ['deck-stilt', `A single stout weathered timber STILT POST standing vertically, a wharf piling descending straight down, warm muted painted timber with soft weathering and a couple of iron bands, seen front-on as a tall narrow post, a faint pale waterline ring near its lower end. Vertical post filling a tall narrow frame.${STYLE}${KEYBG}`],
];

const filter = process.argv[2];
const list = filter ? ITEMS.filter(([id]) => id.includes(filter)) : ITEMS;

async function gen(id, prompt, ar) {
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${KEY}`,
    { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { responseModalities: ['IMAGE'], imageConfig: { aspectRatio: ar } } }) });
  const j = await res.json();
  if (!res.ok) { console.error(id, 'API error', JSON.stringify(j).slice(0, 300)); return false; }
  const part = j.candidates?.[0]?.content?.parts?.find(p => p.inlineData || p.inline_data);
  const data = part?.inlineData?.data || part?.inline_data?.data;
  if (!data) { console.error(id, 'no image', JSON.stringify(j).slice(0, 300)); return false; }
  fs.writeFileSync(path.join(OUT, id + '.png'), Buffer.from(data, 'base64'));
  console.log('wrote', id);
  return true;
}

let ok = 0, fail = 0;
for (const [id, prompt] of list) {
  const ar = id === 'deck-stilt' ? '9:16' : '16:9';
  let done = false;
  for (let t = 0; t < 2 && !done; t++) { done = await gen(id, prompt, ar); if (!done) await new Promise(r => setTimeout(r, 2500)); }
  done ? ok++ : fail++;
  await new Promise(r => setTimeout(r, 900));
}
console.log(`DONE ok=${ok} fail=${fail} (of ${list.length})`);
