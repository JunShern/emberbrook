"""Effective ALBEDO per material out of the SHIPPED GLB (the artifact, not the log).

For every primitive: its material's baseColorTexture mean (linear) x baseColorFactor
x the mean of that primitive's own COLOR_0.  That product is what the shader
multiplies before any light, so its Rec.709 luminance IS the wall-vs-roof value the
critic is looking at.  Reported per material and, for the house materials, per
COLOR_0 CLUSTER so the per-house tint families are visible.
"""
import json, struct, sys, io
import numpy as np
from PIL import Image

def load(path):
    d = open(path,'rb').read()
    assert d[:4]==b'glTF'
    off=12; js=None; bina=None
    while off < len(d):
        ln, ty = struct.unpack_from('<II', d, off); off += 8
        ch = d[off:off+ln]; off += ln
        if ty==0x4E4F534A: js=json.loads(ch)
        elif ty==0x004E4942: bina=ch
    return js, bina

def acc(js, bina, i):
    a=js['accessors'][i]
    bv=js['bufferViews'][a['bufferView']]
    ncomp={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dt={5120:'i1',5121:'u1',5122:'i2',5123:'u2',5125:'u4',5126:'f4'}[a['componentType']]
    base=bv.get('byteOffset',0)+a.get('byteOffset',0)
    stride=bv.get('byteStride') or ncomp*np.dtype(dt).itemsize
    n=a['count']
    raw=np.frombuffer(bina, dtype=np.uint8, count=stride*n, offset=base).reshape(n,stride)
    out=np.zeros((n,ncomp), np.float64)
    v=raw[:, :ncomp*np.dtype(dt).itemsize].copy().view(dt).reshape(n,ncomp).astype(np.float64)
    if a.get('normalized'):
        v = v / {'u1':255.,'u2':65535.,'i1':127.,'i2':32767.}[dt]
    return v

def srgb2lin(c):
    c=np.asarray(c,float)
    return np.where(c<=0.04045, c/12.92, ((c+0.055)/1.055)**2.4)

def teximg(js, bina, ti):
    im = js['images'][js['textures'][ti]['source']]
    bv = js['bufferViews'][im['bufferView']]
    o=bv.get('byteOffset',0)
    return Image.open(io.BytesIO(bina[o:o+bv['byteLength']])).convert('RGB')

_TM={}
def texmean(js,bina,ti):
    if ti in _TM: return _TM[ti]
    a=np.asarray(teximg(js,bina,ti),dtype=np.float32)/255.
    m=srgb2lin(a.reshape(-1,3)).mean(0)
    _TM[ti]=m; return m

L709=lambda c: float(0.2126*c[0]+0.7152*c[1]+0.0722*c[2])

def main(path, only=None):
    js,bina=load(path)
    rows={}
    for mesh in js['meshes']:
        for pr in mesh['primitives']:
            mi=pr.get('material')
            if mi is None: continue
            name=js['materials'][mi].get('name','mat%d'%mi)
            if only and only not in name: continue
            pbr=js['materials'][mi].get('pbrMetallicRoughness',{})
            fac=np.array(pbr.get('baseColorFactor',[1,1,1,1]))[:3]
            tm=np.ones(3)
            if 'baseColorTexture' in pbr:
                tm=texmean(js,bina,pbr['baseColorTexture']['index'])
            ci=pr['attributes'].get('COLOR_0')
            if ci is None: continue
            c=acc(js,bina,ci)[:,:3]
            rows.setdefault(name,{'tm':tm,'fac':fac,'c':[]})['c'].append((mesh['name'],c))
    for name,r in sorted(rows.items()):
        allc=np.concatenate([c for _,c in r['c']])
        eff=r['tm']*r['fac']*allc.mean(0)
        print('%-18s n=%7d  tex_lin %.4f %.4f %.4f  COLOR_0 mean %.4f %.4f %.4f  -> eff albedo %.4f %.4f %.4f  L709 %.4f'
              % (name, len(allc), *r['tm'], *allc.mean(0), *eff, L709(eff)))
        # COLOR_0 clusters (rounded) so tint families show
        q=np.round(allc,2)
        u,cnt=np.unique(q,axis=0,return_counts=True)
        o=np.argsort(-cnt)[:6]
        for k in o:
            e=r['tm']*r['fac']*u[k]
            print('      col %.2f %.2f %.2f  x%-7d  effL %.4f' % (*u[k],cnt[k],L709(e)))

if __name__=='__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)
