/* scratch: many shots of ow-valley in one Chrome session */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from './cdp.mjs';
const arg=(k,d)=>{const i=process.argv.indexOf('--'+k);return i>=0?process.argv[i+1]:d;};
const SHOTS=JSON.parse(readFileSync(arg('shots'),'utf8'));
const PORT=parseInt(arg('port','3000'),10), CDP=await freePort();
const CHROME=process.env.CHROME_BIN||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL=`http://localhost:${PORT}/play.html?scene=ow-valley&rt=1&nomusic=1&v=${Date.now()}`;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const profile=join(process.env.TMPDIR||'/tmp','ow-shots-profile');
killOrphans(profile); rmSync(profile,{recursive:true,force:true});
const chrome=spawn(CHROME,[`--remote-debugging-port=${CDP}`,`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,820','--headless=new',URL],{stdio:'ignore'});
let closing=false;
const kill=()=>{if(closing)return;closing=true;try{chrome.kill('SIGKILL')}catch(e){};try{rmSync(profile,{recursive:true,force:true,maxRetries:3})}catch(e){}};
process.on('exit',kill); for(const s of ['SIGINT','SIGTERM','SIGHUP'])process.on(s,()=>{kill();process.exit(130)});
function connect(url){return new Promise((res,rej)=>{const ws=new WebSocket(url,{perMessageDeflate:false,maxPayload:256*1024*1024});
  const pend=new Map();let id=0;
  ws.on('message',d=>{const m=JSON.parse(d.toString());if(m.id&&pend.has(m.id)){pend.get(m.id)(m);pend.delete(m.id)}});
  ws.on('open',()=>res({send:(m,p={})=>new Promise(ok=>{const i=++id;pend.set(i,ok);ws.send(JSON.stringify({id:i,method:m,params:p}))}),close:()=>ws.close()}));
  ws.on('error',rej)})}
const ev=async(cdp,e)=>{const r=await cdp.send('Runtime.evaluate',{expression:e,returnByValue:true,awaitPromise:true});
  const d=r.result||{}; if(d.exceptionDetails)return 'EXC '+(d.exceptionDetails.exception?.description||JSON.stringify(d.exceptionDetails));
  return d.result?d.result.value:undefined;};
(async()=>{
  const cdp=await connect(await findPage(CDP,{tries:320,label:'gate_shots'}));
  await cdp.send('Runtime.enable');
  let ok=false;
  for(let i=0;i<200;i++){ if(await ev(cdp,`(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`)===true){ok=true;break} await sleep(250) }
  if(!ok){console.error('never populated');kill();process.exit(2)}
  await sleep(1000);
  for(const s of SHOTS){
    const r=await ev(cdp,`(()=>{try{${s.expr}; return 'ok'}catch(e){return 'EXC '+e.message}})()`);
    if(String(r).startsWith('EXC')){console.error(s.out,r);continue}
    await sleep(s.settle||900);
    const shot=await cdp.send('Page.captureScreenshot',{format:'png'});
    const b64=shot.result&&shot.result.data;
    if(!b64){console.error('no data',s.out);continue}
    mkdirSync(dirname(s.out),{recursive:true}); writeFileSync(s.out,Buffer.from(b64,'base64'));
    console.log('WROTE '+s.out+'  '+(await ev(cdp,'JSON.stringify(SIM.pos())')));
  }
  cdp.close();kill();process.exit(0);
})().catch(e=>{console.error('FAILED:',e&&e.message);kill();process.exit(1)});
