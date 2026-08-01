// glb_read.mjs — minimal GLB reader for the scene-graph tooling.
//
// Why: the scene graph and its verifier both need to answer geometric questions
// about a SHIPPED bundle ("where is walk_pad_inn?", "is this point standing on
// the walk network?") from Node, with no Blender and no browser. Blender owns
// authoring; this reads the bundle the runtime actually loads, so the answers
// cannot drift from what the player gets.
//
// Scope on purpose: node hierarchy + world matrices, POSITION/indices of the
// primitives of named meshes, an AABB per node, and a down-ray over triangles.
// No materials, no animations, no textures, no glTF-JSON (.gltf+.bin) variant.
//
// Coordinates are the GLB's own = the runtime's (+x east, +y up, +z south) —
// every exporter in this repo writes y-up GLB.
import fs from 'fs';

const CT_POSITION = 'POSITION';
const COMPONENT = {5120:[Int8Array,1],5121:[Uint8Array,1],5122:[Int16Array,2],
                   5123:[Uint16Array,2],5125:[Uint32Array,4],5126:[Float32Array,4]};
const NCOMP = {SCALAR:1, VEC2:2, VEC3:3, VEC4:4, MAT4:16};

function mul(a,b){                       // column-major 4x4, a*b
  const o=new Float64Array(16);
  for(let c=0;c<4;c++)for(let r=0;r<4;r++){let s=0;
    for(let k=0;k<4;k++) s+=a[k*4+r]*b[c*4+k];
    o[c*4+r]=s;}
  return o;
}
function ident(){const m=new Float64Array(16);m[0]=m[5]=m[10]=m[15]=1;return m;}
function trs(t,r,s){
  const m=ident();
  if(r){ const[x,y,z,w]=r;
    const x2=x+x,y2=y+y,z2=z+z;
    m[0]=1-(y*y2+z*z2); m[1]=x*y2+w*z2;     m[2]=x*z2-w*y2;
    m[4]=x*y2-w*z2;     m[5]=1-(x*x2+z*z2); m[6]=y*z2+w*x2;
    m[8]=x*z2+w*y2;     m[9]=y*z2-w*x2;     m[10]=1-(x*x2+y*y2); }
  if(s){ for(let c=0;c<3;c++)for(let r2=0;r2<3;r2++) m[c*4+r2]*=s[c]; }
  if(t){ m[12]=t[0]; m[13]=t[1]; m[14]=t[2]; }
  return m;
}
const xf=(m,p)=>[m[0]*p[0]+m[4]*p[1]+m[8]*p[2]+m[12],
                 m[1]*p[0]+m[5]*p[1]+m[9]*p[2]+m[13],
                 m[2]*p[0]+m[6]*p[1]+m[10]*p[2]+m[14]];

export function loadGlb(path){
  const buf=fs.readFileSync(path);
  let json=null, bin=null, off=12;
  while(off<buf.length){
    const len=buf.readUInt32LE(off), type=buf.readUInt32LE(off+4);
    const body=buf.subarray(off+8, off+8+len);
    if(type===0x4E4F534A) json=JSON.parse(body.toString('utf8'));
    else if(type===0x004E4942) bin=body;
    off+=8+len+((4-len%4)%4);
  }
  if(!json) throw new Error('no JSON chunk in '+path);
  const G={json, bin, path};

  G.accessor=(i)=>{
    const a=json.accessors[i], v=json.bufferViews[a.bufferView];
    const [TA,sz]=COMPONENT[a.componentType], n=NCOMP[a.type];
    const base=(v.byteOffset||0)+(a.byteOffset||0);
    const stride=v.byteStride||sz*n;
    const out=new (a.componentType===5126?Float32Array:TA)(a.count*n);
    for(let e=0;e<a.count;e++){
      const o=base+e*stride;
      for(let c=0;c<n;c++){
        const p=o+c*sz;
        out[e*n+c]= a.componentType===5126 ? bin.readFloatLE(p)
                  : a.componentType===5125 ? bin.readUInt32LE(p)
                  : a.componentType===5123 ? bin.readUInt16LE(p)
                  : a.componentType===5122 ? bin.readInt16LE(p)
                  : a.componentType===5121 ? bin.readUInt8(p)
                  : bin.readInt8(p);
      }
    }
    return out;
  };

  // world matrices for every node, by walking the scene graph once
  const world=new Array((json.nodes||[]).length).fill(null);
  const local=(n)=> n.matrix ? Float64Array.from(n.matrix) : trs(n.translation,n.rotation,n.scale);
  const roots=(json.scenes&&json.scenes[json.scene||0].nodes)||[];
  const walkTree=(i,parent)=>{
    const n=json.nodes[i], m=mul(parent, local(n));
    world[i]=m;
    for(const c of (n.children||[])) walkTree(c,m);
  };
  for(const r of roots) walkTree(r, ident());
  G.world=world;

  G.nodesNamed=(re)=>(json.nodes||[]).map((n,i)=>({i,name:n.name||'',node:n}))
    .filter(o=>re.test(o.name));

  // world-space AABB of one node's own mesh (children ignored — the exporters
  // here emit flat mesh nodes)
  G.nodeBox=(i)=>{
    const n=json.nodes[i]; if(n.mesh===undefined) return null;
    const m=G.world[i]||ident(), mesh=json.meshes[n.mesh];
    const lo=[Infinity,Infinity,Infinity], hi=[-Infinity,-Infinity,-Infinity];
    for(const p of mesh.primitives){
      const ai=p.attributes[CT_POSITION]; if(ai===undefined) continue;
      const a=json.accessors[ai];
      if(!a.min||!a.max) continue;
      for(let cx=0;cx<8;cx++){
        const c=[cx&1?a.max[0]:a.min[0], cx&2?a.max[1]:a.min[1], cx&4?a.max[2]:a.min[2]];
        const w=xf(m,c);
        for(let k=0;k<3;k++){ if(w[k]<lo[k])lo[k]=w[k]; if(w[k]>hi[k])hi[k]=w[k]; }
      }
    }
    if(lo[0]===Infinity) return null;
    return {min:lo, max:hi,
            center:[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,(lo[2]+hi[2])/2]};
  };

  // world-space triangles of the nodes matching re (cached per pattern)
  const triCache=new Map();
  G.tris=(re)=>{
    const key=String(re);
    if(triCache.has(key)) return triCache.get(key);
    const out=[];
    for(const {i} of G.nodesNamed(re)){
      const n=json.nodes[i]; if(n.mesh===undefined) continue;
      const m=G.world[i]||ident();
      for(const p of json.meshes[n.mesh].primitives){
        const pi=p.attributes[CT_POSITION]; if(pi===undefined) continue;
        const pos=G.accessor(pi);
        const idx=p.indices!==undefined ? G.accessor(p.indices)
                : Uint32Array.from({length:pos.length/3},(_,k)=>k);
        for(let t=0;t+2<idx.length;t+=3){
          const tri=[];
          for(let k=0;k<3;k++){ const v=idx[t+k]*3;
            tri.push(xf(m,[pos[v],pos[v+1],pos[v+2]])); }
          out.push(tri);
        }
      }
    }
    triCache.set(key,out);
    return out;
  };

  // FLAT, STREAMED, UNCACHED triangles — the same world-space numbers `G.tris` returns,
  // in one Float64Array instead of four JS arrays per triangle, and with nothing retained.
  //
  // WHY IT EXISTS, WITH THE MEASUREMENT. `G.tris` allocates `[[x,y,z],[x,y,z],[x,y,z]]`
  // per triangle AND caches every pattern it is asked for. That is fine at blockout scale
  // and fatal at dressed scale: `emb-townwalk/scene.glb` went gray-massing -> dressed and
  // now carries 27,082,183 triangles over 7,022 nodes (counted off its own accessor
  // counts; the gray bundle it replaced has 201,488). `cine_occlude`'s occluder builder
  // asks `G.tris` once PER NODE, so 7,022 cache entries retained ~108M small arrays and
  // its accumulating plain-JS array died with `RangeError: Invalid array length` before a
  // single gate could run.
  //
  // The arithmetic is IDENTICAL — same accessor, same `xf`, same Float64 matrix, same
  // winding, same triangle order — so no verdict fed by this can move; only the container
  // changed. `node[i]` indexes `names`, so per-triangle provenance survives at four bytes
  // a triangle instead of a retained string reference.
  const _primTris=(p)=>((p.indices!==undefined ? json.accessors[p.indices].count
                        : json.accessors[p.attributes[CT_POSITION]].count)/3)|0;
  G.triCount=(re)=>{
    let n=0;
    for(const {i} of G.nodesNamed(re)){
      const nd=json.nodes[i]; if(nd.mesh===undefined) continue;
      for(const p of json.meshes[nd.mesh].primitives){
        if(p.attributes[CT_POSITION]===undefined) continue;
        n+=_primTris(p);
      }
    }
    return n;
  };
  G.trisFlat=(re)=>{
    const NT=G.triCount(re);
    const pos=new Float64Array(NT*9), node=new Int32Array(NT), names=[];
    let t=0;
    for(const {i,name} of G.nodesNamed(re)){
      const nd=json.nodes[i]; if(nd.mesh===undefined) continue;
      const m=G.world[i]||ident();
      const nameId=names.push(name)-1;
      for(const p of json.meshes[nd.mesh].primitives){
        const pi=p.attributes[CT_POSITION]; if(pi===undefined) continue;
        const P=G.accessor(pi);
        const idx=p.indices!==undefined ? G.accessor(p.indices) : null;
        const ntri=_primTris(p);
        for(let k=0;k<ntri;k++){
          for(let c=0;c<3;c++){
            const v=(idx?idx[k*3+c]:k*3+c)*3;
            const w=xf(m,[P[v],P[v+1],P[v+2]]);
            const o=t*9+c*3;
            pos[o]=w[0]; pos[o+1]=w[1]; pos[o+2]=w[2];
          }
          node[t]=nameId; t++;
        }
      }
    }
    return {count:t, pos, node, names};
  };

  // every up-facing surface height at (x,z) over the given mesh pattern.
  // Mirrors play3d.html's colTops(): down-ray, keep hits whose normal.y > .5.
  G.tops=(re,x,z)=>{
    const ys=[];
    for(const T of G.tris(re)){
      const [A,B,C]=T;
      // triangle normal
      const ux=B[0]-A[0],uy=B[1]-A[1],uz=B[2]-A[2];
      const vx=C[0]-A[0],vy=C[1]-A[1],vz=C[2]-A[2];
      const nx=uy*vz-uz*vy, ny=uz*vx-ux*vz, nz=ux*vy-uy*vx;
      const nl=Math.hypot(nx,ny,nz)||1e-12;
      if(Math.abs(ny/nl)<=0.5) continue;                 // not standable
      // barycentric containment in xz
      const d=(B[2]-C[2])*(A[0]-C[0])+(C[0]-B[0])*(A[2]-C[2]);
      if(Math.abs(d)<1e-12) continue;
      const l1=((B[2]-C[2])*(x-C[0])+(C[0]-B[0])*(z-C[2]))/d;
      const l2=((C[2]-A[2])*(x-C[0])+(A[0]-C[0])*(z-C[2]))/d;
      const l3=1-l1-l2;
      const E=-1e-6;
      if(l1<E||l2<E||l3<E) continue;
      ys.push(l1*A[1]+l2*B[1]+l3*C[1]);
    }
    return ys.sort((a,b)=>b-a);
  };

  return G;
}
export const WALK_RE=/^walk/i;
