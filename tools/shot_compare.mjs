/**
 * node tools/shot_compare.mjs <dirA> <dirB> [--region x,y,w,h]
 * Per-shot luminance percentiles for two runs of tools/three_shots.mjs, so a
 * before/after strip carries NUMBERS and not only an impression. Display-space
 * (the PNG is what the player sees), sRGB-luma, HUD rows excluded.
 */
import { readdirSync, readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { PNG } from 'pngjs';
const [A, B] = process.argv.slice(2).filter(a => !a.startsWith('--'));
const stats = f => {
  const p = PNG.sync.read(readFileSync(f));
  const L = [];
  let r = 0, g = 0, b = 0, n = 0;
  for (let y = 26; y < p.height - 40; y++) for (let x = 0; x < p.width; x += 2) {
    const i = (p.width * y + x) << 2;
    const R = p.data[i] / 255, G = p.data[i + 1] / 255, Bl = p.data[i + 2] / 255;
    L.push(0.2126 * R + 0.7152 * G + 0.0722 * Bl); r += R; g += G; b += Bl; n++;
  }
  L.sort((a, c) => a - c);
  const q = t => L[Math.floor(L.length * t)];
  return { L05: q(0.05), L50: q(0.5), L95: q(0.95), sat: (Math.max(r, g, b) - Math.min(r, g, b)) / n };
};
const rows = [];
for (const f of readdirSync(A).filter(f => f.endsWith('.png')).sort()) {
  if (!existsSync(join(B, f))) { rows.push([f, 'MISSING IN ' + B]); continue; }
  const a = stats(join(A, f)), b = stats(join(B, f));
  rows.push([f,
    `L05 ${a.L05.toFixed(3)}->${b.L05.toFixed(3)}`,
    `L50 ${a.L50.toFixed(3)}->${b.L50.toFixed(3)}  (x${(b.L50 / Math.max(a.L50, 1e-4)).toFixed(2)})`,
    `L95 ${a.L95.toFixed(3)}->${b.L95.toFixed(3)}`,
    `chroma ${a.sat.toFixed(3)}->${b.sat.toFixed(3)}`]);
}
const w = Math.max(...rows.map(r => r[0].length));
for (const r of rows) console.log(r[0].padEnd(w) + '  ' + r.slice(1).join('  '));
