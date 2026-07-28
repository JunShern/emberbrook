// [groundpicker] Generate ground-tileset CANDIDATES for the director's decision kit.
// Writes raw Gemini output to public/assets/iso/blocks/candidates/raw/<id>.png.
// A separate Python pass (proc_ground_candidates.py) squares/resizes/tileable-fies.
// Usage: node tools/gen_ground_candidates.mjs [idFilter]
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

const OUT = path.join(root, 'public/assets/iso/blocks/candidates/raw');
fs.mkdirSync(OUT, { recursive: true });

// Every prompt ends with this. Enforces: flat top-down, seamless, LOW-FREQUENCY
// detail, NARROW muted value range (recede), and NO baked objects, plus Style B.
const TAIL = 'FLAT orthographic top-down view only, NO 3D edges, NO isometric diamond, '
  + 'NO perspective, even flat lighting. Seamless and perfectly tileable, no visible '
  + 'seams. Absolutely NO objects sitting on the surface: no roots, no branches, no '
  + 'twigs, no sticks, no loose rocks, no props, no plants, no text, no watermark. Keep '
  + 'all detail LOW-FREQUENCY and clearly softer/blurrier than a foreground game prop; '
  + 'keep the overall value range NARROW and gently muted so this reads as a quiet '
  + 'RECEDING background surface beneath painted characters. STYLE B, cel-painterly, '
  + 'matched to a warm hand-painted autumn-festival RPG: soft cel shading in 2-3 tone '
  + 'steps with gentle blends, every edge drawn as a DARKENED shade of its own LOCAL '
  + 'color (never black, never neutral grey), no palette quantization or posterization '
  + 'banding, soft warm dusk lighting.';

const P = (desc) => `A seamless tileable FLAT top-down ground texture: ${desc} ${TAIL}`;

// Each SET's materials share a palette + treatment so they blend as siblings.
const ITEMS = [
  // ============ FOREST: forestfloor + forestpath ============
  // A — near-flat cel washes (Ghibli/Zelda), sparse leaf accents
  ['forest-A-forestfloor', P('soft warm autumn forest floor as LARGE near-flat cel color fields of muted olive-brown and dusty russet, gently blended; only a FEW very sparse, soft, simplified fallen-leaf color accents dotted far apart; clean Ghibli/Zelda storybook read, minimal detail')],
  ['forest-A-forestpath', P('a well-worn earth footpath, sibling to that forest floor, as a LARGE near-flat cel wash of pale warm sandy tan a touch lighter and warmer than the floor, gently blended, a couple of very sparse soft leaf accents, so it reads as the same painted world as the floor')],
  // B — soft-painterly, muted low-frequency mottling, NO individual leaves
  ['forest-B-forestfloor', P('a soft-painterly forest floor of muted olive and warm umber, only gentle LOW-FREQUENCY cloudy mottling and slow value drift, NO individual leaves, no discrete shapes, like softly brushed gouache')],
  ['forest-B-forestpath', P('a soft-painterly packed-earth path, sibling to that floor, gentle LOW-FREQUENCY mottling in warm dusty ochre a little lighter than the floor, NO individual leaves or pebbles, softly brushed')],
  // C — stylized-pattern, deliberate simple motifs at low density
  ['forest-C-forestfloor', P('a stylized forest floor with a DELIBERATE simple repeating motif of soft dappled-light ovals and a few clean simplified leaf silhouettes at LOW density on a calm muted moss-and-earth ground, tidy graphic hand-painted look')],
  ['forest-C-forestpath', P('a stylized earth path, sibling to that floor, a DELIBERATE simple low-density motif of soft rounded pebbles and packed-earth patches in warm tan, tidy graphic hand-painted look matching the floor')],

  // ============ VILLAGE: grass + dirt + cobble ============
  // A — cel washes
  ['village-A-grass', P('tidy village lawn grass as LARGE near-flat cel fields of soft warm green with gentle 2-step shading, only faint broad value variation, clean storybook read')],
  ['village-A-dirt', P('bare packed dirt, sibling to that grass, LARGE near-flat cel wash of warm tan-brown with soft gentle shading, clean storybook read')],
  ['village-A-cobble', P('a village cobblestone street in WARM MUTED stone tones (soft greige, warm taupe, dusty sand), large simple rounded cobbles with soft cel shading and edges as darkened local color, LOW contrast, calm and tasteful, an occasional single subtle warm color fleck but NEVER a technicolor quilt')],
  // B — soft-painterly mottling
  ['village-B-grass', P('soft-painterly lawn grass, gentle LOW-FREQUENCY cloudy mottling of muted sage and warm green, NO individual blades, softly brushed')],
  ['village-B-dirt', P('soft-painterly packed dirt, sibling to that grass, gentle LOW-FREQUENCY mottling of muted warm brown, no discrete pebbles, softly brushed')],
  ['village-B-cobble', P('soft-painterly cobblestone in WARM MUTED greige and taupe stone, cobbles suggested only by soft LOW-FREQUENCY value lobes and faint darker seams, no hard outlines, calm and muted, absolutely no technicolor quilt')],
  // C — stylized pattern
  ['village-C-grass', P('stylized lawn grass, a DELIBERATE simple low-density motif of clean little grass-tuft marks on a calm muted green ground, tidy graphic hand-painted look')],
  ['village-C-dirt', P('stylized packed dirt, sibling to that grass, a DELIBERATE simple low-density motif of soft swept furrow lines in warm brown, tidy graphic look')],
  ['village-C-cobble', P('stylized cobblestone, a NEAT regular pattern of simple rounded cobbles in WARM MUTED stone (greige, taupe, warm sand), each cobble softly cel-shaded with a darkened-local-color edge, LOW contrast, occasional single quiet color fleck, tidy and tasteful, never a technicolor quilt')],

  // ============ DELLHOLLOW: deck + water + cliff (water must READ as water) ============
  // A — cel washes; water depth + soft ripple bands
  ['dell-A-water', P('calm canal WATER seen top-down, clearly reading as water: teal-to-deep-blue cel color fields showing DEPTH, with soft lighter cel highlight ripple bands and gentle curved reflections suggesting slow MOVEMENT, glassy and wet, NOT marble, NOT stone')],
  ['dell-A-deck', P('a weathered timber wharf DECK, sibling to that water, warm muted plank boards with charming soft paint-fleck weathering and gentle cel shading, planks reading as flat top-down boards')],
  ['dell-A-cliff', P('damp canal-side rock, sibling to that water and deck, near-flat cel fields of cool muted grey-brown stone with soft gentle shading, calm and receding')],
  // B — soft painterly; water flow gradients
  ['dell-B-water', P('deep still WATER top-down, clearly water: soft-painterly muted blue-green with slow LOW-FREQUENCY flow gradients and faint soft current streaks suggesting gentle movement and depth, wet and glassy, NOT marble')],
  ['dell-B-deck', P('soft-painterly weathered wharf DECK, sibling to that water, muted grey-brown planks with gentle low-frequency wear, soft and calm')],
  ['dell-B-cliff', P('soft-painterly damp rock, sibling to that water and deck, gentle LOW-FREQUENCY mottling of cool muted stone grey, soft and receding')],
  // C — stylized pattern; clear repeating ripple motif
  ['dell-C-water', P('stylized canal WATER top-down, unmistakably water: a DELIBERATE gentle repeating motif of soft curved chevron RIPPLES and simplified wave-scales in teal and blue with soft white cel glints, reading as calm moving water, tidy graphic look, NOT marble, NOT stone')],
  ['dell-C-deck', P('stylized wharf DECK, sibling to that water, a NEAT simple pattern of warm muted timber planks with charming soft paint-fleck accents and clean cel edges')],
  ['dell-C-cliff', P('stylized canal-side rock, sibling to that water and deck, a DELIBERATE simple low-density motif of stacked simplified stone blocks in cool muted grey-brown, tidy graphic look')],

  // ============ INTERIOR: plank ============
  ['interior-A-plank', P('a clean warm honey-toned wooden PLANK floor top-down, tidy cel-shaded boards with soft grain, each board edge a darkened shade of the local wood color, calm and even')],
  ['interior-B-plank', P('a soft-painterly weathered wooden PLANK floor top-down, muted grey-brown boards with gentle LOW-FREQUENCY wear and soft grain, calm and receding')],
  ['interior-C-plank', P('a stylized wide-board wooden PLANK floor top-down, a NEAT simple pattern of broad warm timber boards with a clean simplified grain motif and soft cel shading')],
];

const filter = process.argv[2];
const list = filter ? ITEMS.filter(([id]) => id.includes(filter)) : ITEMS;

async function gen(id, prompt) {
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${KEY}`,
    { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { responseModalities: ['IMAGE'], imageConfig: { aspectRatio: '1:1' } } }) });
  const j = await res.json();
  if (!res.ok) { console.error(id, 'API error', JSON.stringify(j).slice(0, 300)); return false; }
  const part = j.candidates?.[0]?.content?.parts?.find(p => p.inlineData || p.inline_data);
  const data = part?.inlineData?.data || part?.inline_data?.data;
  if (!data) { console.error(id, 'no image', JSON.stringify(j).slice(0, 300)); return false; }
  const buf = Buffer.from(data, 'base64');
  fs.writeFileSync(path.join(OUT, id + '.png'), buf);
  console.log('wrote', id, Math.round(buf.length / 1024) + 'KB');
  return true;
}

let ok = 0, fail = 0;
for (const [id, prompt] of list) {
  let done = false;
  for (let t = 0; t < 2 && !done; t++) {
    done = await gen(id, prompt);
    if (!done) await new Promise(r => setTimeout(r, 2500));
  }
  done ? ok++ : fail++;
  await new Promise(r => setTimeout(r, 900));
}
console.log(`DONE ok=${ok} fail=${fail} (of ${list.length})`);
