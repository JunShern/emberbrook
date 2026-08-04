(function(){
  // THE CLOSEUP CAMERA, verbatim from scratchpad/t2/spec.json's first entry — the
  // cones were read off t2-closeup.png, so the probe must stand where that plate stood.
  var fs=SIM.floors(-57.8,60.6); var y=(fs&&fs.length)?Math.max.apply(null,fs):null;
  SIM.tp(-57.8,60.6,y);
  var O=window.ORBIT; O.yaw=-1.5426; O.pitch=0.18; O.dist=7; O.panX=0; O.panY=0; O.panZ=0;
  if(window.OWD) OWD.rebuild(true);
  SIM.tick(2);

  // THE ORBIT RIG CONVERGES IN THE RENDER LOOP, NOT IN SIM.tick — the first version of
  // this probe raycast synchronously and every hit came back 38 m away, on the far side
  // of the valley, from a camera that had not moved yet. A ray cast through a camera
  // that is not the plate's camera names the wrong object with total confidence. So the
  // pick RE-RUNS on an interval and the report carries the camera it was cast from:
  // if that position is not the plate's, the answer is visibly not to be trusted.
  var pts=[["cream-L1",293,715],["cream-L1b",300,722],["cream-L2",318,712],["cream-L2b",325,726],
           ["mint-R1",1058,672],["mint-R1b",1050,682],["mint-R2",1065,660],
           ["cream-R",1105,718],["cream-Rb",1100,725]];
  var PW=1400, PH=733;
  var rc=new THREE.Raycaster(); rc.far=400;

  function pick(){
    var out=[];
    for(var i=0;i<pts.length;i++){
      var nm=pts[i][0], px=pts[i][1], py=pts[i][2];
      rc.setFromCamera({x:(px/PW)*2-1, y:-(py/PH)*2+1}, cam);
      var hits=rc.intersectObjects(scene.children, true);
      var rec=[];
      for(var h=0; h<hits.length && rec.length<2; h++){
        var it=hits[h], ob=it.object;
        if(!ob.visible) continue;
        var chain=[], p=ob;
        while(p && p!==scene){ chain.push(p.name||"("+p.type+")"); p=p.parent; }
        var mat=Array.isArray(ob.material)?ob.material[0]:ob.material;
        rec.push({name:ob.name||"(anon)", type:ob.type,
                  inst:(it.instanceId===undefined?null:it.instanceId),
                  mat:mat?(mat.name||"(unnamed)")+"/"+mat.type:null,
                  map:!!(mat&&mat.map),
                  col:mat&&mat.color?"#"+mat.color.getHexString():null,
                  d:+it.distance.toFixed(2),
                  pt:[+it.point.x.toFixed(2),+it.point.y.toFixed(2),+it.point.z.toFixed(2)],
                  chain:chain.join(" < ")});
      }
      out.push({px:nm+" ("+px+","+py+")", hits:rec});
    }
    var cv=document.querySelector("canvas");
    window.__report=JSON.stringify({
      cam:{pos:cam.position.toArray().map(function(v){return +v.toFixed(2)}),
           fov:cam.fov, aspect:+cam.aspect.toFixed(3)},
      canvas:{w:cv.width,h:cv.height,cw:cv.clientWidth,ch:cv.clientHeight},
      picks:out});
  }
  var t=setInterval(pick, 120);
  setTimeout(function(){ clearInterval(t); }, 5000);
})();
