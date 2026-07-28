// [ground-r3] Stone-LEDGE face sprite for the masonry platform class (the
// constructed-stone counterpart to deck-fascia). Small keyed sprite, engine-
// placed by rule; Style B + clean keying still law. Generated on flat MAGENTA
// chroma; key_deckedges.py strips it to transparency.
//   ledge-face : the vertical cut-stone WALL FACE of a constructed quay / lock
//                margin seen straight-on, dark dressed ashlar matching the
//                lockwall assets. Engine shears it onto each south/east water
//                edge, dropping to a defined waterline. NO stilts (solid wall).
// Usage: node tools/gen_ledge.mjs [idFilter]
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
  ['ledge-face', `The vertical FRONT FACE of a heavy CONSTRUCTED dressed-stone quay / lock wall seen straight-on from the front: two or three horizontal courses of DARK BLUE-GREY cut ashlar masonry blocks with tidy fine mortar joints, cool weathered dressed stone exactly like a canal lock wall, a couple of faint rust stains, a faint pale waterline mark along the very bottom edge. A cut-stone masonry wall face, a wide landscape strip. Straight horizontal band, front-on elevation (NOT top-down, NOT angled), cool dark slate-blue stone (matching heavy lock-wall masonry), solid and constructed (not natural rock, not planks).${STYLE}${KEYBG}`],
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
  let done = false;
  for (let t = 0; t < 2 && !done; t++) { done = await gen(id, prompt, '16:9'); if (!done) await new Promise(r => setTimeout(r, 2500)); }
  done ? ok++ : fail++;
  await new Promise(r => setTimeout(r, 900));
}
console.log(`DONE ok=${ok} fail=${fail} (of ${list.length})`);
