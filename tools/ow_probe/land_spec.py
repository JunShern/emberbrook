#!/usr/bin/env python3
"""land_spec.py — expand tools/ow_probe/land_cams.json into an ow_multi.mjs spec.

  python3 tools/ow_probe/land_spec.py <outdir> <prefix> [--inject-all] > spec.json

<prefix> names the plates (<outdir>/<prefix>-<key>.png).  With --inject-all the FIRST
entry calls OWL.all() before its shot, so one Chrome launch can photograph the shipped
state and the probe state back to back on the SAME camera — which is the only way the
port's numbers and the probe's numbers are comparable at all.

  python3 ... plates L0            > /tmp/a.json      # shipped
  python3 ... plates LA --inject-all > /tmp/b.json    # + OWL.all()
  node tools/ow_probe/ow_multi.mjs --spec /tmp/a.json [--inject tools/ow_probe/land.js]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAMS = json.load(open(os.path.join(HERE, "land_cams.json")))["cams"]


def main():
    outdir = os.path.abspath(sys.argv[1])
    prefix = sys.argv[2]
    inject = "--inject-all" in sys.argv
    spec = []
    for i, c in enumerate(CAMS):
        pre = "window.OWL.all(); " if (inject and i == 0) else ""
        spec.append(dict(
            out=os.path.join(outdir, "%s-%s.png" % (prefix, c["key"])),
            expr=("%swindow.__tp(%r,%r); var O=window.ORBIT; O.yaw=%r; O.pitch=%r; "
                  "O.dist=%r; O.panX=0;O.panY=0;O.panZ=0; SIM.tick(2);"
                  % (pre, c["x"], c["z"], c["yaw"], c["pitch"], c["dist"])),
            settle=1600 if (inject and i == 0) else 1000))
    json.dump(spec, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
