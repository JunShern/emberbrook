/**
 * tools/three_shots.mjs — many viewpoints across SEVERAL scenes in one Chrome.
 *
 * Built for the r128 -> modern-three before/after strip: the same shot list has to
 * be replayable against two different builds of the page, so the shot list is data
 * and the only thing that changes between runs is --outdir.
 *
 * Shot list is JSON: [{scene, expr, out, settle}] — `scene` triggers a full page
 * navigate when it differs from the page that is up (a cine bundle re-derives its
 * camera graph on boot, so a scene change here is deliberately NOT an in-place
 * swap: we want the same boot path the player gets). `expr` runs in the page and
 * may set window.ORBIT / call SIM.tp / await SIM.shot(...).
 *
 * node tools/three_shots.mjs --shots <json> --port 3000 --outdir docs/qa/three-upgrade/before
 */
import { spawn } from 'child_process';
import { rmSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import WebSocket from 'ws';
import { freePort, killOrphans, findPage } from './cdp.mjs';
import { mkArg } from './argv.mjs';
// `--k v` AND `--k=v` (tools/argv.mjs): the bare indexOf form silently
// ignored the `=` spelling and used the DEFAULT instead.
const { arg } = mkArg(process.argv);
const SHOTS=JSON.parse(readFileSync(arg('shots'),'utf8'));
const PORT=parseInt(arg('port','3000'),10), CDP=await freePort();
const OUTDIR=arg('outdir','docs/qa/three-upgrade/shots');
const CHROME=process.env.CHROME_BIN||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
// no ?rt= : the page derives RT from the scene name (ow-*/townwalk are real-time,
// a cine bundle is not). Forcing rt=1 on a cine bundle turns OFF the baked plate
// and the depth map, i.e. it would photograph a different game than the player's.
// ?nostory=1 so a story beat's dialogue box does not sit over half the plate in
// one run and not the other — a before/after strip has to differ only in the build.
// --q "postfx=off&ao_i=0" appends page knobs to EVERY shot's URL. A tuning A/B is
// the same shot list against a different build OR against a different setting, and
// the second kind used to mean editing the source between runs — which is exactly
// the thing a before/after strip must not have done.
const QEXTRA=arg('q','');
const urlFor=s=>`http://localhost:${PORT}/play3d.html?scene=${s}&nomusic=1&nostory=1${QEXTRA?'&'+QEXTRA:''}&v=${Date.now()}`;
const profile=join(process.env.TMPDIR||'/tmp','three-shots-profile');
killOrphans(profile); rmSync(profile,{recursive:true,force:true});
const chrome=spawn(CHROME,[`--remote-debugging-port=${CDP}`,`--user-data-dir=${profile}`,
  '--no-first-run','--no-default-browser-check','--autoplay-policy=no-user-gesture-required',
  '--window-size=1400,820','--headless=new',urlFor(SHOTS[0].scene)],{stdio:'ignore'});
let closing=false;
const kill=()=>{if(closing)return;closing=true;try{chrome.kill('SIGKILL')}catch(e){};try{rmSync(profile,{recursive:true,force:true,maxRetries:3})}catch(e){}};
process.on('exit',kill); for(const s of ['SIGINT','SIGTERM','SIGHUP'])process.on(s,()=>{kill();process.exit(130)});
const CONSOLE=[];
function connect(url){return new Promise((res,rej)=>{const ws=new WebSocket(url,{perMessageDeflate:false,maxPayload:256*1024*1024});
  const pend=new Map();let id=0;
  ws.on('message',d=>{const m=JSON.parse(d.toString());
    if(m.method==='Runtime.consoleAPICalled'&&/error|warning/.test(m.params.type||''))
      CONSOLE.push(m.params.type+': '+(m.params.args||[]).map(a=>a.value||a.description||'').join(' ').slice(0,220));
    if(m.method==='Runtime.exceptionThrown')
      CONSOLE.push('EXCEPTION: '+((m.params.exceptionDetails||{}).exception||{}).description);
    if(m.method==='Log.entryAdded'&&/error|warning/.test(m.params.entry.level||''))
      CONSOLE.push(m.params.entry.level+': '+String(m.params.entry.text).slice(0,220));
    if(m.id&&pend.has(m.id)){pend.get(m.id)(m);pend.delete(m.id)}});
  ws.on('open',()=>res({send:(m,p={})=>new Promise(ok=>{const i=++id;pend.set(i,ok);ws.send(JSON.stringify({id:i,method:m,params:p}))}),close:()=>ws.close()}));
  ws.on('error',rej)})}
const ev=async(cdp,e)=>{const r=await cdp.send('Runtime.evaluate',{expression:e,returnByValue:true,awaitPromise:true});
  const d=r.result||{}; if(d.exceptionDetails)return 'EXC '+(d.exceptionDetails.exception?.description||JSON.stringify(d.exceptionDetails));
  return d.result?d.result.value:undefined;};
async function waitLive(cdp){
  for(let i=0;i<400;i++){ if(await ev(cdp,`(()=>{try{return !!(window.SIM&&SIM.pos()&&isFinite(SIM.pos().x))}catch(e){return false}})()`)===true) return true; await sleep(250) }
  return false;
}
(async()=>{
  const cdp=await connect(await findPage(CDP,{tries:320,label:'three_shots'}));
  await cdp.send('Runtime.enable');
  const errs=[], console_=[];
  // AN INSTRUMENT THAT FINDS NOTHING MUST PROVE IT COULD HAVE FOUND SOMETHING:
  // a shader that fails to compile still screenshots — as a black frame or, worse,
  // as a frame missing one object nobody was looking at. The console is the only
  // place three.js says so, so it is captured and printed with the run.
  await cdp.send('Runtime.addBinding',{name:'__none'}).catch(()=>{});
  await cdp.send('Log.enable').catch(()=>{});
  if(!await waitLive(cdp)){console.error('never populated');kill();process.exit(2)}
  let cur=SHOTS[0].scene;
  await sleep(2500);
  for(const s of SHOTS){
    if(s.scene!==cur){
      await cdp.send('Page.navigate',{url:urlFor(s.scene)});
      await sleep(1200);
      if(!await waitLive(cdp)){console.error('scene never populated: '+s.scene);continue}
      cur=s.scene; await sleep(2500);
    }
    const r=await ev(cdp,`(async()=>{try{${s.expr}; return 'ok'}catch(e){return 'EXC '+e.message}})()`);
    if(String(r).startsWith('EXC')){console.error(s.out,r);errs.push(s.out);continue}
    await sleep(s.settle||1400);
    const out=join(OUTDIR,s.out);
    const shot=await cdp.send('Page.captureScreenshot',{format:'png'});
    const b64=shot.result&&shot.result.data;
    if(!b64){console.error('no data',s.out);errs.push(s.out);continue}
    mkdirSync(dirname(out),{recursive:true}); writeFileSync(out,Buffer.from(b64,'base64'));
    const meta=await ev(cdp,'JSON.stringify({pos:SIM.pos(),cine:window.__cine&&window.__cine.cam,shotRes:window.__S,cl:window.__charlight&&{gain:window.__charlight.gain,key:window.__charlight.intens&&window.__charlight.intens.key}})');
    console.log('WROTE '+out+'  '+meta);
  }
  console.log(errs.length?('MISSED '+errs.join(',')):'ALL SHOTS OK');
  const uniq=[...new Set(CONSOLE)];
  console.log(uniq.length?('CONSOLE ('+uniq.length+' distinct):\n  '+uniq.join('\n  ')):'CONSOLE CLEAN');
  cdp.close();kill();process.exit(0);
})().catch(e=>{console.error('FAILED:',e&&e.message);kill();process.exit(1)});
