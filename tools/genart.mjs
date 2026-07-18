// Generate an image via the Gemini API (gemini-2.5-flash-image, ~$0.039/image).
// Usage: node tools/genart.mjs <outfile.png> "<prompt>"
import fs from 'fs';
import path from 'path';

const root = path.join(import.meta.dirname, '..');
const env = Object.fromEntries(
  fs.readFileSync(path.join(root, '.env'), 'utf8')
    .split('\n')
    .filter(l => l.includes('=') && !l.trim().startsWith('#'))
    .map(l => [
      l.slice(0, l.indexOf('=')).trim(),
      l.slice(l.indexOf('=') + 1).trim().replace(/^["']|["']$/g, ''),
    ])
);
const KEY = env.GEMINI_API_KEY || process.env.GEMINI_API_KEY;
if (!KEY) { console.error('no GEMINI_API_KEY in .env'); process.exit(1); }

const [, , outFile, ...promptParts] = process.argv;
const prompt = promptParts.join(' ');
if (!outFile || !prompt) { console.error('usage: node tools/genart.mjs out.png "prompt"'); process.exit(1); }

const res = await fetch(
  `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${KEY}`,
  {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { responseModalities: ['IMAGE'] },
    }),
  }
);
const j = await res.json();
if (!res.ok) { console.error('API error:', JSON.stringify(j).slice(0, 800)); process.exit(1); }
const part = j.candidates?.[0]?.content?.parts?.find(p => p.inlineData || p.inline_data);
const data = part?.inlineData?.data || part?.inline_data?.data;
if (!data) { console.error('no image in response:', JSON.stringify(j).slice(0, 500)); process.exit(1); }
fs.writeFileSync(outFile, Buffer.from(data, 'base64'));
console.log('wrote', outFile, `(${Math.round(Buffer.from(data, 'base64').length / 1024)} KB)`);
