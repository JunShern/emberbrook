// TEMPLATE V2 generator — compose the placeholder-recipe prompt from
// specs.json + the region map, and generate the sheet via Gemini.
//
// The template sheet (grey placeholder blocks standing on magenta pads, cyan
// background) is passed as the reference image; the prompt instructs the model
// to REPLACE each block with its object, standing exactly as the block stands
// (proven interior recipe), inheriting footprint + height from the geometry.
// Per-object identity and height phrasing are lifted from specs.json so the
// prompt stays spec-driven.
//
// Usage: node tools/gen_props_v2.mjs <blocks9|festival> <template.png> <regions.json> <out.png>
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

const [catalog, tmpl, regionsPath, outFile] = process.argv.slice(2);
if (!outFile) { console.error('usage: node tools/gen_props_v2.mjs cat template.png regions.json out.png'); process.exit(1); }

const specsDoc = JSON.parse(fs.readFileSync(path.join(root, 'public/assets/iso/specs.json')));
const specs = Object.fromEntries(specsDoc.assets.map(a => [a.id, a]));
const STYLE = specsDoc.style.recipe;   // canonical STYLE B block, used verbatim
const rmap = JSON.parse(fs.readFileSync(regionsPath));

// identity = first sentence of the spec prompt; height = the CRITICAL HEIGHT clause.
function identity(p) {
  const m = p.match(/^(.*?[.])\s/);
  return (m ? m[1] : p.split('.')[0]).trim();
}
function heightClause(sp) {
  const m = sp.prompt.match(/CRITICAL HEIGHT:\s*(.*?)(?:\.\s*hand-painted|\. hand-painted)/is);
  let c = m ? m[1].replace(/\s+/g, ' ').trim().replace(/[.\s]+$/, '')
            : `${sp.targetHeightM} m tall, about ${(sp.targetHeightCells / 2).toFixed(1)} times its pad width`;
  // strip the leading "the <id> stands/is" so "It must stand <clause>" reads cleanly
  return c.replace(/^the\s+\w+\s+(stands|is|reaches)\s+/i, '');
}

// visual reading order: cluster regions into rows by y0, left-to-right within a row
const regs = rmap.regions.map(r => ({ ...r, cx: r.region[0] + r.region[2] / 2,
                                      cy: r.region[1] + r.region[3] / 2 }));
const rowsY = [];
[...regs].sort((a, b) => a.region[1] - b.region[1]).forEach(r => {
  const row = rowsY.find(g => Math.abs(g.y - r.region[1]) < 120);
  if (row) { row.items.push(r); row.y = Math.min(row.y, r.region[1]); }
  else rowsY.push({ y: r.region[1], items: [r] });
});
rowsY.forEach(g => g.items.sort((a, b) => a.region[0] - b.region[0]));
const ordered = rowsY.flatMap((g, ri) => g.items.map((r, ci) => ({ ...r, ri, ci, rowN: g.items.length })));

const posName = (ri, ci, n, nrows) => {
  const rowLabel = nrows === 1 ? '' : ri === 0 ? 'top ' : ri === nrows - 1 ? 'bottom ' : `row-${ri + 1} `;
  const colLabel = n === 1 ? 'only' : ci === 0 ? 'leftmost' : ci === n - 1 ? 'rightmost' : `#${ci + 1} from left`;
  return `${rowLabel}${colLabel}`.trim();
};
const nrows = rowsY.length;

const lines = ordered.map((r, i) => {
  const sp = specs[r.name];
  return `${i + 1}. The ${posName(r.ri, r.ci, r.rowN, nrows)} block `
    + `(${r.declared[0]}x${r.declared[1]} footprint, ${r.declared[1] > r.declared[0] ? 'an ELONGATED base, ' : ''}`
    + `its block ${r.targetHeightCells >= 4 ? 'notably TALL' : r.targetHeightCells <= 1.3 ? 'short' : 'medium'}) `
    + `-> ${identity(sp.prompt)} It must stand ${heightClause(sp)}.`;
});

const prompt =
`This is a reference sheet on a flat CYAN background. Each framed cell holds a GREY PLACEHOLDER BLOCK standing on a flat MAGENTA registration pad. Repaint the sheet: REPLACE every grey block with the object named for it, standing EXACTLY where and how its block stands.

Rules, applied to every cell:
- The object's base sits ON the magenta pad, filling the SAME footprint shape as the block (a long block = a long object along the same axis).
- The object's TOP reaches exactly the top of the grey block it replaces — no shorter, no taller. Match the block's height precisely: a very tall block becomes a very tall object, a short block stays short. Do not average the heights toward each other.
- Keep the flat magenta pad visible as a rim around the base of each object (do not paint over the whole pad).
- Keep the CYAN background flat and empty. Do not move, resize, add, or reproportion any cell.

The ${ordered.length} objects, cell by cell:
${lines.join('\n')}

${STYLE}.`;

console.error('--- PROMPT ---\n' + prompt + '\n--------------');

const parts = [
  { inline_data: { mime_type: 'image/png', data: fs.readFileSync(tmpl).toString('base64') } },
  { text: prompt },
];
const res = await fetch(
  `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${KEY}`,
  { method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ contents: [{ parts }], generationConfig: { responseModalities: ['IMAGE'] } }) });
const j = await res.json();
if (!res.ok) { console.error('API error:', JSON.stringify(j).slice(0, 800)); process.exit(1); }
const part = j.candidates?.[0]?.content?.parts?.find(p => p.inlineData || p.inline_data);
const data = part?.inlineData?.data || part?.inline_data?.data;
if (!data) { console.error('no image:', JSON.stringify(j).slice(0, 500)); process.exit(1); }
fs.writeFileSync(outFile, Buffer.from(data, 'base64'));
console.log('wrote', outFile, `(${Math.round(Buffer.from(data, 'base64').length / 1024)} KB)`);
