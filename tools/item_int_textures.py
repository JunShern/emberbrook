#!/usr/bin/env python3
"""Fetch the extra PolyHaven maps the INTERIOR scenes need.

The kit's outdoor manifest (tools/textures/_manifest.json) is shared and is
being written by other agents, so interior additions go into their own
manifest file (_manifest_itemint.json). Interior material builders merge both.

Usage: python3 tools/int_textures.py
"""
import json, os, subprocess, sys, urllib.request

TEXDIR = "/Users/junshernchan/projects/multiplayer-rpg/tools/textures"
MANI = os.path.join(TEXDIR, "_manifest_itemint.json")
RES = "1k"

# material name -> polyhaven asset id
WANT = {
    "tex_int_floor":   "old_wood_floor",
    "tex_int_beam":    "medieval_wood",
    "tex_int_wall":    "weathered_brown_planks",
    "tex_int_shelf":   "brown_planks_03",
    "tex_burlap":      "hessian_230",
    "tex_rust":        "rust_coarse_01",
}
MAPS = ("Diffuse", "Rough", "nor_gl", "AO")


def fetch(asset):
    # urllib gets a 403 from the API; curl is what the kit scripts use.
    url = "https://api.polyhaven.com/files/%s" % asset
    out = subprocess.run(["curl", "-sSL", url], check=True, capture_output=True)
    return json.loads(out.stdout)


def main():
    os.makedirs(TEXDIR, exist_ok=True)
    mani = {}
    if os.path.exists(MANI):
        mani = json.load(open(MANI))
    for name, asset in WANT.items():
        files = fetch(asset)
        maps = {}
        for m in MAPS:
            if m not in files:
                print("  skip %s: no %s" % (asset, m))
                continue
            e = files[m][RES]["jpg"]
            dest = os.path.join(TEXDIR, "%s_%s.jpg" % (asset, m))
            if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
                subprocess.run(["curl", "-sSL", "-o", dest, e["url"]], check=True)
            maps[m] = dest
        mani[name] = {"asset": asset, "res": RES, "maps": maps}
        print("ok %-16s %-24s %s" % (name, asset, sorted(maps)))
    json.dump(mani, open(MANI, "w"), indent=1)
    print("wrote", MANI)


if __name__ == "__main__":
    main()
