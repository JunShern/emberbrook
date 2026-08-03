#!/usr/bin/env python3
"""imgstat.py — landscape-frame statistics, ours vs the reference.

Measures the four things the eye reads as 'production render' before it reads
any asset:  VALUE RANGE, CHROMA, the WARM/COOL SHADOW SPLIT, and LOCAL DETAIL
(high-frequency energy = does the ground have texture at pixel scale).
Crop box is given per image so HUD/watermark pixels never enter the census.
"""
import sys, json
import numpy as np
from PIL import Image

def stat(path, crop):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    x0,y0,x1,y1 = [int(round(v*s)) for v,s in zip(crop,(W,H,W,H))]
    a = np.asarray(im.crop((x0,y0,x1,y1)), dtype=np.float32)/255.0
    r,g,b = a[...,0],a[...,1],a[...,2]
    L = 0.2126*r+0.7152*g+0.0722*b
    mx, mn = a.max(-1), a.min(-1)
    S = np.where(mx>1e-6,(mx-mn)/np.maximum(mx,1e-6),0.0)
    pc = lambda x,q: float(np.percentile(x,q))
    # warm/cool split: mean (b-r) for the darkest quartile vs the brightest quartile.
    q1,q3 = np.percentile(L,25), np.percentile(L,75)
    dark, lite = L<=q1, L>=q3
    br = b-r
    # local detail: mean |laplacian| of L on a 1px kernel, per 100 px of image
    lap = np.abs(4*L[1:-1,1:-1]-L[:-2,1:-1]-L[2:,1:-1]-L[1:-1,:-2]-L[1:-1,2:])
    # hue mass: fraction of pixels in the dominant 30-deg hue bin (of the coloured ones)
    hsv = np.asarray(Image.fromarray((a*255).astype(np.uint8)).convert('HSV'),dtype=np.float32)
    hue = hsv[...,0]*360/255.0
    colf = S>0.15
    hh,_ = np.histogram(hue[colf], bins=12, range=(0,360))
    dom = float(hh.max()/max(hh.sum(),1))
    return dict(
        px=int(L.size),
        L05=round(pc(L,5),3), L25=round(pc(L,25),3), L50=round(pc(L,50),3),
        L75=round(pc(L,75),3), L95=round(pc(L,95),3),
        Lrange=round(pc(L,95)-pc(L,5),3),
        S50=round(pc(S,50),3), S90=round(pc(S,90),3),
        bmr_dark=round(float(br[dark].mean()),4),
        bmr_lite=round(float(br[lite].mean()),4),
        coolsplit=round(float(br[dark].mean()-br[lite].mean()),4),
        detail=round(float(lap.mean())*1000,2),
        detail_p90=round(float(np.percentile(lap,90))*1000,2),
        domhue=round(dom,3),
    )

if __name__=='__main__':
    spec = json.load(open(sys.argv[1]))
    rows=[]
    for name, path, crop in spec:
        try: s = stat(path, crop)
        except Exception as e: print(f'{name}: ERR {e}'); continue
        s['name']=name; rows.append(s)
    keys=['name','L05','L50','L95','Lrange','S50','S90','bmr_dark','bmr_lite','coolsplit','detail','detail_p90','domhue']
    print('  '.join(k.ljust(10) for k in keys))
    for r in rows: print('  '.join(str(r[k]).ljust(10) for k in keys))
