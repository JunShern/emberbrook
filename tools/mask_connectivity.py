import sys, collections, glob, os
try:
    from PIL import Image
except Exception as e:
    print("NO_PIL", e); sys.exit(0)

def check(path):
    im = Image.open(path).convert("L")
    W,H = im.size
    px = im.load()
    walk = [[1 if px[x,y]>128 else 0 for x in range(W)] for y in range(H)]
    total = sum(sum(r) for r in walk)
    if total==0: return (os.path.basename(os.path.dirname(path)), W,H, 0,0,0,0.0)
    seen=[[0]*W for _ in range(H)]
    comps=0; largest=0
    for sy in range(H):
        for sx in range(W):
            if walk[sy][sx] and not seen[sy][sx]:
                comps+=1; sz=0
                dq=collections.deque([(sx,sy)]); seen[sy][sx]=1
                while dq:
                    x,y=dq.pop(); sz+=1
                    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx,ny=x+dx,y+dy
                        if 0<=nx<W and 0<=ny<H and walk[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx]=1; dq.append((nx,ny))
                if sz>largest: largest=sz
    return (os.path.basename(os.path.dirname(path)), W,H, total, comps, largest, round(100*largest/total,1))

scenes = sys.argv[1:] or ['square3d','forest3d','lane3d','entrance3d','gate3d','descent3d','lockfive3d','stairs3d']
print(f"{'scene':<14}{'dims':<12}{'walkPx':>8}{'comps':>7}{'largest':>9}{'pct%':>7}")
for s in scenes:
    p=f"public/assets/scenes/{s}/mask.png"
    if not os.path.exists(p): print(f"{s:<14}(no mask.png)"); continue
    name,W,H,total,comps,largest,pct=check(p)
    flag = "" if (comps<=1 or pct>=99.5) else "  <-- DISCONNECTED"
    print(f"{s:<14}{str(W)+'x'+str(H):<12}{total:>8}{comps:>7}{largest:>9}{pct:>6}%{flag}")
