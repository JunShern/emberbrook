// [groundv2] Ground-system-V2 texture candidates for the director's re-pick.
// Structured materials (cobble, plank) are generated FLAT top-down with STRAIGHT
// axis-aligned courses/boards so the engine's iso-aware sampler can project them
// along the grid diagonals. Warmed-B forest is an organic sibling variant.
// Writes raw Gemini output to candidates/raw/<id>.png; proc_ground_candidates.py squares/tiles.
// Usage: node tools/gen_groundv2_tex.mjs [idFilter]
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

const TAIL = 'FLAT orthographic top-down view only, NO 3D edges, NO isometric diamond, '
  + 'NO perspective, even flat lighting. Seamless and perfectly tileable, no visible '
  + 'seams. Absolutely NO objects sitting on the surface: no roots, no branches, no '
  + 'twigs, no loose rocks, no props, no plants, no text, no watermark. Keep '
  + 'all detail LOW-FREQUENCY and clearly softer/blurrier than a foreground game prop; '
  + 'keep the overall value range NARROW and gently muted so this reads as a quiet '
  + 'RECEDING background surface beneath painted characters. STYLE B, cel-painterly, '
  + 'matched to a warm hand-painted autumn-festival RPG: soft cel shading in 2-3 tone '
  + 'steps with gentle blends, every edge drawn as a DARKENED shade of its own LOCAL '
  + 'color (never black, never neutral grey), no palette quantization or posterization '
  + 'banding, soft warm dusk lighting.';
// Structured tail: the sampler projects these onto the iso grid, so the source
// must be axis-aligned and REGULAR — straight courses/boards, no rotation.
const STRUCT = ' The pattern MUST be laid out in STRAIGHT rows aligned to the image '
  + 'axes (horizontal and vertical), perfectly regular and repeating, NOT rotated, NOT '
  + 'diagonal, NOT herringbone — the courses run straight across the tile.';

const P = (desc) => `A seamless tileable FLAT top-down ground texture: ${desc} ${TAIL}`;

const ITEMS = [
  // ---- FOREST warmed-B: B's soft low-frequency painterly + A's warmer, more saturated hue
  ['gv2-forestfloor', P("a soft-painterly autumn forest floor, gentle LOW-FREQUENCY cloudy mottling and slow value drift like softly brushed gouache (NO individual leaves, no discrete shapes), but in a WARMER, MORE SATURATED palette than a muted floor: warm russet, toasted amber and warm umber with a glow of autumn color, still calm and receding")],
  ['gv2-forestpath', P("a soft-painterly packed-earth footpath, sibling to that warm floor, gentle LOW-FREQUENCY mottling in a warm saturated sandy ochre a little lighter than the floor, NO individual leaves or pebbles, softly brushed, sharing the same warm autumn glow")],

  // ---- VILLAGE cobble: warm muted stone, honest small ~0.2m stones, straight iso-alignable courses
  ['gv2-cobbleA', P("a quiet lane surfaced with lots of little rounded paving stones set close together in even straight lines (roughly eight or nine stones spanning the tile), painted in gentle warm neutral stone: soft greige, warm taupe and dusty sand, each pebble softly shaded with an edge that is just a deeper tone of the same stone, kept LOW in contrast, tasteful and calm, only a rare faint warm speck, definitely no rainbow patchwork" + STRUCT)],
  ['gv2-cobbleB', P("a tidy cobblestone lane of SMALL squarish setts (about nine across the tile) in warm muted grey-brown and taupe stone, packed tight in straight even courses with faint darker mortar seams, gentle cel shading, very low contrast, quiet and calm, absolutely no technicolor quilt" + STRUCT)],
  ['gv2-cobbleC', P("a worn cobblestone street of SMALL smooth river cobbles (about eight across the tile) in warm sandy-greige and soft ochre-brown stone, set in straight regular rows, softly cel-shaded and rounded with darkened-local-color edges, warm muted and low contrast, a couple of quiet warm flecks, never a technicolor quilt" + STRUCT)],

  // ---- INTERIOR plank: honest narrow boards, straight, iso-alignable
  ['gv2-plankA', P("a tidy floor of slim honey-oak floorboards laid parallel and running straight across the frame (roughly seven or eight boards spanning the tile), gently cel-shaded warm golden timber with a whisper of grain, a thin recessed seam of deeper wood tone between each board, quiet and even" + STRUCT)],
  ['gv2-plankB', P("a soft-painterly weathered wooden PLANK floor of narrow boards running straight across (about eight boards across the tile), muted grey-brown timber with gentle LOW-FREQUENCY wear and soft grain, thin darker seams between boards, calm and receding" + STRUCT)],
  ['gv2-plankC', P("a warm timber wooden PLANK floor of medium boards running straight across (about six boards across the tile), a clean simplified grain motif in warm toasted-brown wood with soft cel shading and fine darker seams between boards, tidy and even" + STRUCT)],
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
  fs.writeFileSync(path.join(OUT, id + '.png'), Buffer.from(data, 'base64'));
  console.log('wrote', id);
  return true;
}

let ok = 0, fail = 0;
for (const [id, prompt] of list) {
  let done = false;
  for (let t = 0; t < 2 && !done; t++) { done = await gen(id, prompt); if (!done) await new Promise(r => setTimeout(r, 2500)); }
  done ? ok++ : fail++;
  await new Promise(r => setTimeout(r, 900));
}
console.log(`DONE ok=${ok} fail=${fail} (of ${list.length})`);
