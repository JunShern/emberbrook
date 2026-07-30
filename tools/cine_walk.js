// CINE WALK — play the whole of Dellhollow through fixed cameras in a real browser,
// with the runtime's own physics and the runtime's own camera cuts, and write down
// what a player would have seen.
//
// Companion to tools/cine_test.mjs (which proves the SHOT LIST in Node) exactly as
// tools/slice_walk.js is to slice_test.mjs: the static test cannot walk, and the
// browser cannot see a shot nobody wired. Both are needed, and the brief's bar is the
// walk — "proven by simulated playthrough".
//
// Paste into the play3d console on ?scene=del-cine, or drive over CDP / the Chrome MCP
// javascript_tool.
//
//   await CINEWALK.tour()        fetch public/world/cine_tour.json and walk the whole
//                               town, recording every camera cut, every prompt, and
//                               whether each arrival landed on the walk network
//   await CINEWALK.seam(i, n)    cross cut edge i n times; asserts EXACTLY n cuts
//   CINEWALK.probe()             GL READBACK: is the character actually drawn under
//                               the current shot's depth map? (screenshots of a hidden
//                               tab are stale — slice finding 7 — so this reads pixels)
//   CINEWALK.shots               which shots have been visited, in order
//   CINEWALK.log                 the transcript (kept in sessionStorage)
window.CINEWALK = (function(){
  const LOGKEY='cine_log';
  const log=JSON.parse(sessionStorage.getItem(LOGKEY)||'[]');
  const save=()=>sessionStorage.setItem(LOGKEY,JSON.stringify(log));
  const rec=(o)=>{const c=SIM.cine(); o.t=new Date().toISOString().slice(11,19);
                  o.shot=c&&c.shot; log.push(o); save(); return o;};
  const shots=[];
  const P=()=>{const p=SIM.pos();return {x:+p.x.toFixed(2),y:+p.y.toFixed(2),z:+p.z.toFixed(2)};};
  const onNet=()=>{const p=SIM.pos();return SIM.walkFloors(p.x,p.z).some(y=>Math.abs(y-p.y)<0.35);};
  const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));

  // A cut is a FADE: transitionTo holds the veil while the next shot's art loads, so
  // the walker has to wait it out. Poll for the busy flag clearing instead of guessing
  // a duration (a cold shot's PNG fetch is longer than the 350 ms fade).
  async function settle(max){
    max=max||6000; const t0=Date.now();
    while(Date.now()-t0<max){
      const b=document.getElementById('sgp');
      if(!window.__sgBusyProbe && SIM.cine()) {}
      // the veil is the observable: opacity back to 0 and the shot applied
      const v=document.querySelector('div[style*="z-index:9"]');
      const op=v?parseFloat(getComputedStyle(v).opacity):0;
      if(op<0.02) return Date.now()-t0;
      await sleep(40);
    }
    return -1;
  }

  // Steer with the real walker, watching for the shot to change under us. Returns the
  // cuts that fired during the leg — which is the thing being tested: a player walks,
  // and the camera changes by itself.
  async function step(tx,tz,opt){
    opt=opt||{};
    const near=opt.near||0.4, cap=opt.ticks||600;
    let cutsHere=[], before=SIM.cine().cuts;
    for(let n=0;n<cap;n++){
      const p=SIM.pos(), dx=tx-p.x, dz=tz-p.z, d=Math.hypot(dx,dz);
      if(d<=near) return {ok:true, ticks:n, cuts:cutsHere};
      SIM.move(dx/d,dz/d,1);
      const c=SIM.cine();
      if(c.cuts!==before){                          // a silent cut fired mid-stride
        const waited=await settle();
        const now=SIM.cine();
        cutsHere.push({to:now.shot, waitedMs:waited, at:P(), onNet:onNet(),
                       cached:now.cached.length});
        if(shots[shots.length-1]!==now.shot) shots.push(now.shot);
        before=now.cuts;
        return {ok:true, ticks:n, cuts:cutsHere, cutMidLeg:true};
      }
    }
    const p=SIM.pos();
    return {ok:false, why:'tickcap', cuts:cutsHere,
            dist:+Math.hypot(tx-p.x,tz-p.z).toFixed(2), pos:P(),
            blocked:SIM.blocked(p.x+(tx-p.x)*0.05, p.z+(tz-p.z)*0.05, p.y)};
  }

  return {
    log, shots,
    reset(){ log.length=0; shots.length=0; save(); return 'log cleared'; },

    // GL readback: with the shot's depth map writing gl_FragDepth, is the character
    // actually rasterised? A wrong near/far after a texture swap makes them vanish and
    // NOTHING else notices — not the console, not a screenshot of a background tab.
    probe(){
      const c=SIM.cine(), o=SIM.occ();
      const raw=SIM.paint();                     // depth test OFF: is it drawn at all
      const tst=SIM.paint({tested:true});        // depth test ON: does it survive the shot
      // The pair is the diagnosis. raw==0 means the model is gone or off-screen. raw>0
      // with tested==0 means the DEPTH MAP is burying it — a wrong near/far after a
      // texture swap looks exactly like this and nothing else in the page notices.
      return rec({step:'probe', shot:c&&c.shot, depth:c&&c.depth,
                  camNearFar:c&&c.cam?[c.cam.near,c.cam.far]:null,
                  charNdc:raw.charNdc, onScreen:raw.onScreen,
                  drawn:raw.magentaPixels, survivesDepth:tst.magentaPixels,
                  occMarker:o.ring, occFirst:o.first, camDist:o.camDist,
                  verdict: !raw.onScreen ? 'CHARACTER OFF SCREEN in this shot'
                         : raw.magentaPixels<40 ? 'CHARACTER NOT RASTERISED — model or camera suspect'
                         : tst.magentaPixels>40 ? 'visible through the shot\'s depth map'
                         : o.ring ? 'occluded by the shot, and the presence marker is showing (correct)'
                         : 'OCCLUDED WITH NO MARKER — depth near/far after the swap is suspect'});
    },

    // walk the generated grand tour: every shot entered, over the map's own network
    async tour(url){
      const T=await (await fetch(url||'world/cine_tour.json?v='+Date.now())).json();
      rec({step:'tour-start', legs:T.legs.length, shotsExpected:T.shots.length,
           startCam:SIM.cine().shot, pos:P(), onNet:onNet()});
      shots.push(SIM.cine().shot);
      let walked=0, failed=[], cuts=[];
      for(const leg of T.legs){
        let ok=true, note=null;
        for(const [x,z] of leg.walk){
          const r=await step(x,z);
          for(const c of r.cuts) cuts.push({...c, on:`${leg.from}->${leg.to}`});
          if(!r.ok){ ok=false; note=r; break; }
        }
        walked++;
        if(!ok) failed.push({leg:`${leg.from}->${leg.to}`, ...note});
        rec({step:'leg', leg:`${leg.from}->${leg.to}`, pts:leg.walk.length, ok,
             pos:P(), onNet:onNet(), cutsSoFar:SIM.cine().cuts, fail:note});
      }
      const missed=T.shots.filter(s=>!shots.includes(s));
      return rec({step:'tour-done', legsWalked:walked, legsFailed:failed.length,
                  failures:failed, cuts:cuts.length, shotsVisited:[...new Set(shots)].length,
                  ofShots:T.shots.length, missed, order:shots.slice()});
    },

    // HYSTERESIS, for real: walk back and forth across one seam and count the cuts.
    // A promptless auto edge that oscillates would strobe the screen, and the
    // arm/disarm rule plus the arrival's clearance are what stop it.
    async seam(i,n){
      n=n||4;
      const e=SIM.edges()[i];
      if(!e||!e.auto) return rec({step:'seam', i, error:'edge '+i+' is not a camera cut'});
      const A=e.spawn.slice();
      const back=SIM.edges().find(x=>x.cam===e.camFrom&&x.camFrom===e.cam);
      const B=(back?back.spawn:e.at).slice();
      const c0=SIM.cine().cuts, shot0=SIM.cine().shot;
      SIM.tp(B[0],B[2],B[1]);
      const seq=[];
      for(let k=0;k<n;k++){
        for(const tgt of [A,B]){
          const r=await step(tgt[0],tgt[2],{near:0.5,ticks:400});
          seq.push({to:SIM.cine().shot, ok:r.ok, cut:r.cuts.length});
        }
      }
      const fired=SIM.cine().cuts-c0;
      return rec({step:'seam', i, id:e.id, crossings:n*2, cutsFired:fired,
                  expected:n*2, exact:fired===n*2, endedIn:SIM.cine().shot,
                  startedIn:shot0, seq});
    },

    // jump to a shot and prove it renders + the character is visible in it
    async visit(id){
      await SIM.shot(id);
      await sleep(120);
      const c=SIM.cine();
      const sp=c.baked&&c.baked.spawn;
      if(sp) SIM.tp(sp[0],sp[2],sp[1]);
      SIM.tick(1);
      return rec({step:'visit', id, name:c.name, pos:P(), onNet:onNet(),
                  spawnFrom:c.baked&&c.baked.visibleFrac, probe:this.probe()});
    },
  };
})();
