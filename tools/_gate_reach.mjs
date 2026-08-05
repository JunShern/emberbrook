/* scratch: ask the running game whether a body can get from A to B in ow-valley */
import { spawn } from 'child_process';
import { rmSync } from 'fs';
import { join } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from '/Users/junshernchan/projects/multiplayer-rpg/tools/cdp.mjs';
import { INSTALL } from '/Users/junshernchan/projects/multiplayer-rpg/tools/reach_probe.mjs';
import { mkArg } from './argv.mjs';

// `--k v` AND `--k=v` (tools/argv.mjs): the bare indexOf form silently

// ignored the `=` spelling and used the DEFAULT instead.

const { arg } = mkArg(process.argv);
const PAIRS = JSON.parse(arg('pairs','[]'));   // [{name,a:[x,y,z],b:[x,y,z]}]
const PORT=parseInt(arg('port','3000'),10);
const CDP=await freePort();
const CHROME=process.env.CHROME_BIN||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL=`http://localhost:${PORT}/play.html?scene=ow-valley&rt=1&nomusic=1&v=${Date.now()}`;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const profile=join(process.env.TMPDIR||'/tmp','ow-reach-profile');
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
  const cdp=await connect(await findPage(CDP,{tries:320,label:'reach'}));
  await cdp.send('Runtime.enable');
  let ok=false;
  for(let i=0;i<200;i++){ if(await ev(cdp,`(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`)===true){ok=true;break} await sleep(250) }
  if(!ok){console.error('never populated');kill();process.exit(2)}
  await sleep(800);
  console.log('scene:', await ev(cdp,'SIM.scene()'));
  console.log('install:', await ev(cdp, INSTALL));
  for(const p of PAIRS){
    const r=await ev(cdp,`window.__ebReach(${JSON.stringify(p.a)},${JSON.stringify(p.b)},{step:0.4,tol:2.0,ms:120000}).then(o=>JSON.stringify(o))`);
    console.log('\n== '+p.name+' ==');
    console.log(typeof r==='string'&&r.startsWith('{')?JSON.stringify(JSON.parse(r),null,1):r);
  }
  cdp.close();kill();process.exit(0);
})().catch(e=>{console.error('FAILED:',e&&e.message);kill();process.exit(1)});
