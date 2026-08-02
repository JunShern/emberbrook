import WebSocket from 'ws';
import { writeFileSync, mkdirSync } from 'fs';
const CDP = process.argv[2], OUT = process.argv[3], NAV = process.argv[4];
const sleep = ms => new Promise(r => setTimeout(r, ms));
const list = await (await fetch(`http://127.0.0.1:${CDP}/json/list`)).json();
const page = list.find(t => t.type === 'page' && /play3?d?\.html/.test(t.url));
if (!page) { console.error('no play3d page'); process.exit(2); }
const ws = new WebSocket(page.webSocketDebuggerUrl, { maxPayload: 256*1024*1024 });
const pend = new Map(); let id = 0;
ws.on('message', d => { const m = JSON.parse(d.toString()); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
await new Promise(r => ws.on('open', r));
const send = (m, p={}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({id:i, method:m, params:p})); });
await send('Runtime.enable'); await send('Page.enable');
if (NAV) { await send('Page.navigate', { url: NAV }); await sleep(3000); }
let st = null;
for (let i = 0; i < 120; i++) {
  const e = await send('Runtime.evaluate', { expression:
    `(()=>{try{const s=window.scene;if(!s)return null;let m=0,sky=false,rg=0;s.traverse(o=>{if(o.isMesh)m++;if(o.name==='__owsky')sky=true;if(o.name==='__owridge')rg++;});return JSON.stringify({m,sky,rg,fog:!!s.fog,bg:s.background&&s.background.getHexString?s.background.getHexString():null});}catch(err){return 'ERR '+err.message}})()`,
    returnByValue: true });
  st = e.result?.result?.value;
  if (st && st.startsWith('{') && JSON.parse(st).m > 20) break;
  await sleep(500);
}
await sleep(2000);
const shot = await send('Page.captureScreenshot', { format: 'png' });
if (!shot.result?.data) { console.error('no data'); process.exit(3); }
mkdirSync(OUT.replace(/\/[^/]+$/, ''), { recursive: true });
writeFileSync(OUT, Buffer.from(shot.result.data, 'base64'));
console.log(OUT, st);
process.exit(0);
