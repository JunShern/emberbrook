// SLICE WALK — drive the connected slice through a real browser, one scene at a
// time, using the runtime's own physics (SIM.move drives phys(), the same code a
// keypress does) and the runtime's own scene graph (SIM.edges / SIM.go).
//
// Paste into the play3d console, or drive via CDP / the Chrome MCP
// javascript_tool. Companion to tools/slice_test.mjs, which asserts the GRAPH
// statically in Node; this asserts that a PLAYER can actually get from trigger to
// trigger with collision on. Both are needed: the static test cannot walk, and
// the browser test cannot see edges that no scene lists.
//
// Usage in one scene:
//   SLICE.plan([[x,z],[x,z],...])   walk a waypoint chain (runtime coords)
//   SLICE.toEdge(i)                 walk to edge i's trigger, then report the prompt
//   SLICE.take(i)                   press its key for real (navigates; the next
//                                   scene needs this file injected again)
//   SLICE.log                       the transcript so far (also kept in
//                                   sessionStorage so it survives the navigation)
window.SLICE = (function(){
  const LOGKEY='slice_log';
  const log=JSON.parse(sessionStorage.getItem(LOGKEY)||'[]');
  const save=()=>sessionStorage.setItem(LOGKEY,JSON.stringify(log));
  const rec=(o)=>{o.t=new Date().toISOString().slice(11,19); o.scene=SIM.graph().scene;
                   log.push(o); save(); return o;};
  const D=(a,b)=>Math.hypot(a.x-b[0], a.z-b[1]);

  // Steer toward (tx,tz) with the real walker.
  //
  // Straight-line steering deadlocks against a wall the way no player does (the
  // engine's step() slides, but a steerer that keeps pushing into a corner stays
  // there), so on a stall this DETOURS: swing the heading +-55deg for a burst and
  // resume, alternating sides. That is what a player does when a building is in
  // the way — and the detour count is reported, because "walkable only via a
  // detour" is a finding about the scene, not a pass to be hidden.
  function walkTo(tx,tz,opt){
    opt=opt||{};
    const near=opt.near||1.1, cap=opt.ticks||4000, maxDetour=opt.detours===undefined?8:opt.detours;
    let n=0, stall=0, last=SIM.pos(), detours=0, side=1;
    while(n<cap){
      const p=SIM.pos(), dx=tx-p.x, dz=tz-p.z, d=Math.hypot(dx,dz);
      if(d<=near) return {ok:true, ticks:n, pos:p, dist:+d.toFixed(2), detours};
      SIM.move(dx/d, dz/d, 1); n++;
      if(n%40===0){
        const q=SIM.pos();
        stall = Math.hypot(q.x-last.x,q.z-last.z) < 0.35 ? stall+1 : 0;
        last=q;
        if(stall>=2){
          if(detours>=maxDetour) return {ok:false, why:'stuck', ticks:n, pos:q, detours,
                                        dist:+Math.hypot(tx-q.x,tz-q.z).toFixed(2)};
          const a=Math.atan2(tz-q.z, tx-q.x) + side*0.96;      // ~55deg
          SIM.move(Math.cos(a), Math.sin(a), 55); n+=55;
          detours++; side=-side; stall=0; last=SIM.pos();
        }
      }
    }
    const p=SIM.pos();
    return {ok:false, why:'tickcap', ticks:n, pos:p, detours,
            dist:+Math.hypot(tx-p.x,tz-p.z).toFixed(2)};
  }

  // Resample a route to a step a straight-line steerer can follow. THE LESSON of
  // the Valley-Gate S-bend: a coarse waypoint chain lets the steerer cut the corner
  // straight into the flight's bar_ railing. Dense following (0.4-0.8u) walks the
  // town's rail-lined flights with zero detours.
  function dense(pts, step){ step=step||0.8;
    const o=[[pts[0][0], pts[0][1]]];
    for(let i=0;i<pts.length-1;i++){
      const a=pts[i], b=pts[i+1], L=Math.hypot(b[0]-a[0], b[1]-a[1]), n=Math.max(1,Math.ceil(L/step));
      for(let k=1;k<=n;k++) o.push([+(a[0]+(b[0]-a[0])*k/n).toFixed(2), +(a[1]+(b[1]-a[1])*k/n).toFixed(2)]);
    }
    return o;
  }
  // Tight follower with NO detours: a failure here is the GEOMETRY, not the
  // harness wandering, and it names the mesh that blocked. Use this to diagnose;
  // use plan()/walkTo() (which detours) to get somewhere.
  function follow(plan, near, cap){ near=near||0.35; cap=cap||400;
    let legs=0, fail=null;
    for(const [x,z] of plan){
      let n=0, d=1e9;
      for(;n<cap;n++){ const p=SIM.pos(), dx=x-p.x, dz=z-p.z; d=Math.hypot(dx,dz);
        if(d<=near) break; SIM.move(dx/d,dz/d,1); }
      if(n>=cap){ const q=SIM.pos();
        fail={to:[x,z], d:+d.toFixed(2), pos:{x:+q.x.toFixed(2),y:+q.y.toFixed(2),z:+q.z.toFixed(2)},
              blocked:SIM.blocked(q.x+(x-q.x)/d*0.4, q.z+(z-q.z)/d*0.4, q.y)};
        break; }
      legs++;
    }
    const p=SIM.pos();
    return {legs, of:plan.length, fail,
            end:{x:+p.x.toFixed(2),y:+p.y.toFixed(2),z:+p.z.toFixed(2)},
            onNet:SIM.walkFloors(p.x,p.z).some(y=>Math.abs(y-p.y)<0.3)};
  }

  return {
    log, walkTo, dense, follow,
    reset(){ log.length=0; save(); return 'log cleared'; },
    // walk a route (list of [x,z] vertices) the reliable way: densify, then follow
    route(pts,opt){ opt=opt||{};
      return rec({step:'route', ...follow(dense(pts, opt.step||0.5), opt.near, opt.ticks)}); },
    // a chain of waypoints; stops at the first leg that cannot be walked
    plan(pts,opt){
      const out=[];
      for(const [x,z] of pts){
        const r=walkTo(x,z,opt); out.push({to:[x,z], ...r});
        if(!r.ok) break;
      }
      return rec({step:'plan', legs:out.length, ok:out.every(o=>o.ok), out});
    },
    // walk to an edge's trigger and report what the player would see
    toEdge(i,opt){
      const e=SIM.edges()[i]; if(!e) return rec({step:'toEdge', i, error:'no such edge'});
      const r=walkTo(e.at[0], e.at[2], opt);
      const ed=SIM.edges()[i], pr=SIM.prompt();
      return rec({step:'toEdge', i, id:e.id, label:e.label, walk:r,
                  dist:ed.dist, dy:ed.dy, inRange:ed.inRange, armed:ed.armed,
                  prompt:pr&&pr.text, promptVisible:!!(pr&&pr.visible)});
    },
    // take the edge for real (fade + navigate or in-place handoff)
    take(i){
      const e=SIM.edges()[i]; if(!e) return rec({step:'take', i, error:'no such edge'});
      const pr=SIM.prompt();
      const r=SIM.go(i);
      return rec({step:'take', i, id:e.id, to:e.to, spawn:e.spawn,
                  promptWasVisible:!!(pr&&pr.visible), result:r});
    },
    // where did we land, and is it on the designed walk network?
    landed(){
      const p=SIM.pos(), ws=SIM.walkFloors(p.x,p.z);
      const on=ws.some(y=>Math.abs(y-p.y)<0.3);
      return rec({step:'landed', pos:{x:+p.x.toFixed(2),y:+p.y.toFixed(2),z:+p.z.toFixed(2)},
                  arrival:SIM.arrival(), onWalkNetwork:on, walkFloors:ws.map(y=>+y.toFixed(2)),
                  edges:SIM.edges().map(e=>({id:e.id,dist:e.dist,armed:e.armed,inRange:e.inRange}))});
    },
  };
})();
