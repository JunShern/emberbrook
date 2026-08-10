"""crop.py — put an object's ray-derived screen box on the shipped plate and crop it.

  python3 crop.py <objmap.json> <shot> <name-substring> <out.jpg> [pad] [bundle]

The box is RAY-DERIVED (objmap's 240x135 marched grid), so it is the same pixels
the census counted, not a projection of a bbox.  LOOK AT THE PLATE.
"""
import sys, json, os
from PIL import Image, ImageDraw

om = json.load(open(sys.argv[1]))
shot = sys.argv[2]
sub = sys.argv[3]
out = sys.argv[4]
pad = float(sys.argv[5]) if len(sys.argv) > 5 else 0.06
bundle = sys.argv[6] if len(sys.argv) > 6 else "public/assets/scenes/del-cine"

c = om["cams"][shot]
W, H = c["W"], c["H"]
xs, ys = [], []
for i, o in enumerate(c["obj"]):
    if sub in o:
        xs.append(i % W); ys.append(i // W)
if not xs:
    print("NO PIXELS for %s at %s" % (sub, shot)); sys.exit(1)
u0, u1 = min(xs) / W, (max(xs) + 1) / W
v0, v1 = min(ys) / H, (max(ys) + 1) / H
print("%s @ %s: %d rays (%.3f%% of frame)  u %.3f..%.3f  v %.3f..%.3f"
      % (sub, shot, len(xs), 100.0 * len(xs) / (W * H), u0, u1, v0, v1))

im = Image.open(os.path.join(bundle, "cameras", shot, "bg.png")).convert("RGB")
PW, PH = im.size
d = ImageDraw.Draw(im)
d.rectangle([u0 * PW, v0 * PH, u1 * PW, v1 * PH], outline=(255, 0, 255), width=5)
cx0 = max(0, int((u0 - pad) * PW)); cx1 = min(PW, int((u1 + pad) * PW))
cy0 = max(0, int((v0 - pad) * PH)); cy1 = min(PH, int((v1 + pad) * PH))
cr = im.crop((cx0, cy0, cx1, cy1))
w, h = cr.size
s = min(3.0, max(1.0, 900.0 / max(w, 1)))
cr.resize((int(w * s), int(h * s))).save(out, quality=93)
print("SAVED %s (%dx%d)" % (out, int(w * s), int(h * s)))
