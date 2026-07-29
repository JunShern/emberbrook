#!/usr/bin/env python3
"""Fetch the INTERIOR texture set (PolyHaven public API) for del-cottage-int.

Plain python3 (no bpy) -- run once:
    python3 tools/cottage_textures.py
Writes tools/textures/<asset>_<Map>.jpg and tools/textures/_manifest_int.json
in the same shape as _manifest.json so cottage_materials.py can read either.
"""
import json, os, sys, urllib.request

TEXDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")
OUT = os.path.join(TEXDIR, "_manifest_int.json")
RES = "1k"
MAPS = ["Diffuse", "Rough", "nor_gl", "AO", "Displacement"]

# material name -> polyhaven asset id
ASSETS = {
    "mat_int_floor":   "wood_floor_worn",
    "mat_int_wood":    "wood_table_worn",
    "mat_int_plaster": "plaster_stone_wall_01",
    "mat_int_stone":   "rustic_stone_wall_02",
    "mat_int_rug":     "dirty_carpet",
    "mat_int_linen":   "rough_linen",
    "mat_int_plank":   "brown_planks_09",
    "mat_int_hearth":  "old_stone_wall_02",
}


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "dellhollow-kit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def main():
    os.makedirs(TEXDIR, exist_ok=True)
    man = {}
    if os.path.exists(OUT):
        man = json.load(open(OUT))
    for mat, asset in ASSETS.items():
        url = "https://api.polyhaven.com/files/%s" % asset
        req = urllib.request.Request(url, headers={"User-Agent": "dellhollow-kit/1.0"})
        info = json.loads(urllib.request.urlopen(req, timeout=60).read())
        maps = {}
        for m in MAPS:
            node = info.get(m)
            if not node:
                continue
            res = node.get(RES) or node.get("2k") or node.get("4k")
            if not res:
                continue
            fmt = res.get("jpg") or res.get("png")
            if not fmt:
                continue
            dest = os.path.join(TEXDIR, "%s_%s.jpg" % (asset, m))
            fetch(fmt["url"], dest)
            maps[m] = dest
            print("  %-12s %s" % (m, os.path.basename(dest)))
        man[mat] = {"asset": asset, "maps": maps, "available": sorted(info.keys())}
        print("%s <- %s (%d maps)" % (mat, asset, len(maps)))
    json.dump(man, open(OUT, "w"), indent=1)
    print("manifest ->", OUT)


if __name__ == "__main__":
    sys.exit(main())
