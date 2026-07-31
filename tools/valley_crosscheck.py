#!/usr/bin/env python3
"""valley_crosscheck.py — the cross-FILE canon assertions for the Ember corridor.

  python3 tools/valley_crosscheck.py

worldmap_validate.mjs checks the geometry hierarchy (containment, refinement,
slopes, portals-on-road).  This checks the PROSE against the geometry, across four
files that each describe the same corridor in their own frame:

    public/world/world.json
    public/world/regions/valley.region.json
    public/townmap/emberbrook.map.json
    public/townmap/dellhollow.map.json

WHY IT EXISTS AND WHY IT LIVES IN tools/.  A sentence in a map file has the same
authority as a number and none of the enforcement: "the town's mass is on the WEST
bank" survived a validator pass, 48 cross-file assertions and a review while the
build mirrored an entire town to satisfy it.  This lane's ruling is that where a
file NAMES a bank, an assertion has to be able to fail on it — and that words and
checks move in ONE commit or the build refuses.  The previous generation of this
instrument lived in a scratch directory and is gone; a check that can evaporate is
not a check.

AMENDED 2026-08-01 BY THE CHIRALITY FLIP.  Every assertion below that names a bank
below the Old Gate was inverted, and each one carries the correction in its own
message rather than in a commit nobody re-reads.
"""
import json
import math
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = json.load(open(os.path.join(ROOT, "public/world/world.json")))
R = json.load(open(os.path.join(ROOT, "public/world/regions/valley.region.json")))
E = json.load(open(os.path.join(ROOT, "public/townmap/emberbrook.map.json")))
D = json.load(open(os.path.join(ROOT, "public/townmap/dellhollow.map.json")))

LM = {l["id"]: l for l in W["landmarks"]}
RLM = {l["id"]: l for l in R.get("landmarks", [])}
PT = {p["id"]: p for p in R["road"]["portals"]}
AN = {a["town"]: a for a in R["townAnchors"]}
EP = {l["id"]: l["pos"] for l in E["landmarks"]}
EN = {l["id"]: l.get("note", "") for l in E["landmarks"]}
DP = {l["id"]: l["pos"] for l in D["landmarks"]}
REG = [r for r in W["regions"] if r["id"] == "valley"][0]

RIV = np.array([[p[0], p[1]] for p in R["river"]["points"]], float)
SPINE = np.array([p["pos"] for p in W["riverSpine"]["points"]], float)
SPW = np.array([p["width"] for p in W["riverSpine"]["points"]], float)

N = FAIL = 0
_fails = []


def ck(name, cond, detail=""):
    global N, FAIL
    N += 1
    if not cond:
        FAIL += 1
        _fails.append("%-46s %s" % (name, detail))
        print("  FAIL  %-46s %s" % (name, detail))
    else:
        print("  ok    %-46s %s" % (name, detail))


def bank(p):
    """(signed offset, distance) of a world point from the refined channel.
    Positive offset = LEFT bank looking downstream."""
    best = (1e9, 0.0)
    for a, b in zip(RIV[:-1], RIV[1:]):
        d = b - a
        l2 = float(d @ d) or 1e-9
        t = max(0.0, min(1.0, float((np.array(p[:2], float) - a) @ d) / l2))
        c = a + t * d
        dist = float(np.hypot(*(np.array(p[:2], float) - c)))
        if dist < best[0]:
            n = math.hypot(*d) or 1.0
            best = (dist, float((np.array(p[:2], float) - c) @ np.array([-d[1], d[0]]) / n))
    return best[1], best[0]


def arc_of(p):
    s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(RIV, axis=0), axis=1))])
    j = int(np.argmin(((RIV - np.array(p[:2], float)) ** 2).sum(axis=1)))
    return float(s[j])


def says(txt, *words):
    t = str(txt).lower()
    return all(w.lower() in t for w in words)


GATE = PT["old-gate"]["at"]
GATE_ARC = arc_of(GATE)

print("=" * 92)
print("A.  THE RIVER — one course, one source, one direction")
print("=" * 92)
ck("river descends monotonically",
   all(R["river"]["points"][i][2] <= R["river"]["points"][i - 1][2] + 1e-9
       for i in range(1, len(R["river"]["points"]))))
ck("spine descends monotonically",
   all(SPINE[i][2] <= SPINE[i - 1][2] + 1e-9 for i in range(1, len(SPINE))))
ck("source is the Whisperwood springs, not the falls",
   says(W["riverSpine"]["points"][0].get("note", ""), "source", "springs")
   and says(W["riverSpine"]["_doc"], "springs deep in the whisperwood"))
ck("source is UPSTREAM of Emberbrook by arc",
   arc_of(SPINE[0]) < arc_of(AN["emberbrook"]["pos"]),
   "source arc %.1f < town arc %.1f" % (arc_of(SPINE[0]), arc_of(AN["emberbrook"]["pos"])))
ck("Ember Falls is BELOW the Old Gate by arc",
   arc_of(LM["ember-falls"]["pos"]) > GATE_ARC,
   "falls arc %.1f > gate arc %.1f" % (arc_of(LM["ember-falls"]["pos"]), GATE_ARC))
ck("Ember Falls' note CORRECTS the source misreading",
   says(LM["ember-falls"]["note"], "mis-read as the river's source",
        "the source is the whisperwood springs"))
_narrow = [i for i in range(1, len(SPW)) if SPW[i] < SPW[i - 1] - 1e-9]
ck("the river narrows in exactly ONE place, and it is the notch",
   len(_narrow) == 1 and says(W["riverSpine"]["points"][_narrow[0]].get("note", ""), "notch"),
   "narrowings at %s" % _narrow)
ck("width grows everywhere else",
   all(SPW[i] >= SPW[i - 1] - 1e-9 for i in range(1, len(SPW)) if i not in _narrow))
ck("navigable width holds from 'below the locks'",
   min(SPW[i] for i, p in enumerate(W["riverSpine"]["points"])
       if arc_of(p["pos"]) >= arc_of(LM["dellhollow-moorage"]["pos"]))
   >= W["riverSpine"]["minNavigableWidth"])
def _seg_d(p, A):
    best = 1e9
    for a, b in zip(A[:-1], A[1:]):
        d = b - a
        l2 = float(d @ d) or 1e-9
        t = max(0.0, min(1.0, float((np.array(p[:2], float) - a) @ d) / l2))
        best = min(best, float(np.hypot(*(np.array(p[:2], float) - (a + t * d)))))
    return best
_drift = max(_seg_d(p, SPINE[:, :2]) for p in RIV)
ck("the refined course refines the spine within tolerance",
   _drift <= W["tolerance"]["riverRefine"], "worst drift %.2fu" % _drift)
ck("Emberbrook's town river flows south->north (downstream)",
   E["river"]["course"][-1][1] > E["river"]["course"][0][1])
ck("Emberbrook's town river runs EAST of the settled town",
   np.mean([c[0] for c in E["river"]["course"]]) >
   np.mean([v[0] for k, v in EP.items()]) + 10.0)

print()
print("=" * 92)
print("B.  THE CHIRALITY — the flip, asserted on both sides of the gate")
print("=" * 92)
CN = R["elevation"]["canyon"]
CULV = R["road"].get("culvert")
ck("region declares a culvert (the ONE bank change)", CULV is not None)
ck("crossings.list is still empty", R["crossings"]["list"] == [])
ck("crossings._doc still says NONE and names the dam crest",
   says(R["crossings"]["_doc"], "none", "dam crest"))
ck("BYTE-CANON: crossings._doc is unchanged",
   R["crossings"]["_doc"] ==
   "NONE — and none possible: the canyon geometry enforces it. Dellhollow's dam "
   "crest is the only span of the river in the world so far.",
   "the one line this lane may not touch")
ck("benchSide is E below the culvert", str(CN["benchSide"]).upper() == "E")
ck("benchSideAboveCulvert is W", str(CN["benchSideAboveCulvert"]).upper() == "W")
road = R["road"]["points"]
i0, i1 = CULV["roadStations"]
above = [bank(p)[0] for p in road[:i0 + 1] if bank(p)[1] < 25.0]
below = [bank(p)[0] for p in road[i1:] if bank(p)[1] < 25.0]
ck("every above-culvert road station is LEFT (west)", all(o > 0 for o in above),
   "%d stations, min %+.2f" % (len(above), min(above)))
ck("every below-culvert road station is RIGHT (east)", all(o < 0 for o in below),
   "%d stations, max %+.2f" % (len(below), max(below)))
ck("the culvert is ON the channel", abs(bank(CULV["at"])[0]) < 1.0,
   "offset %+.2f" % bank(CULV["at"])[0])
ck("the culvert is AT the Old Gate", abs(arc_of(CULV["at"]) - GATE_ARC) < 8.0,
   "%.2fu of arc apart" % abs(arc_of(CULV["at"]) - GATE_ARC))
ck("both culvert mouths are on the channel",
   all(abs(bank(m)[0]) < 1.0 for m in CULV["mouths"]))
ck("Dellhollow's anchor is on the RIGHT (east) bank", bank(AN["dellhollow"]["pos"])[0] < 0,
   "offset %+.2f" % bank(AN["dellhollow"]["pos"])[0])
ck("Dellhollow's Valley Gate is on the RIGHT bank", bank(PT["dellhollow-valley-gate"]["at"])[0] < 0)
ck("the Moorage is on the RIGHT (road-side) bank", bank(LM["dellhollow-moorage"]["pos"])[0] < 0)
ck("the tar boat sits at the Moorage",
   math.dist(RLM["boat-tar"]["pos"][:2], LM["dellhollow-moorage"]["pos"][:2]) < 0.5)
ck("waterAccess is at the Moorage",
   math.dist(CN["waterAccess"][0]["at"][:2], LM["dellhollow-moorage"]["pos"][:2]) < 0.5)
ck("the waystone is on the RIGHT bank", bank(RLM["waystone"]["pos"])[0] < 0)
ck("the shelf pocket is on the RIGHT bank", bank(CN["shelf"]["pockets"][0]["at"])[0] < 0)
ck("every shelf-overrun point is on the RIGHT bank",
   all(bank(p)[0] < 0 for p in CN["shelf"]["overrun"]["points"]))
ck("Emberbrook's anchor is on the LEFT (west) bank", bank(AN["emberbrook"]["pos"])[0] > 0)
ck("the Old Gate doorway is on the LEFT (west) bank", bank(GATE)[0] > 0,
   "offset %+.2f" % bank(GATE)[0])
ck("the Whisperwood entrance is on the LEFT (west) bank", bank(LM["whisperwood-entrance"]["pos"])[0] > 0)
ck("Dellhollow's impression carries NO mirrorY",
   "mirrorY" not in AN["dellhollow"]["impression"],
   "deleted, not set false — a reader must not mistake it for a choice")
ck("Emberbrook's impression is unmirrored", AN["emberbrook"]["impression"]["mirrorY"] is False)
ck("Dellhollow's pin is the Valley Gate and matches the portal",
   AN["dellhollow"]["impression"]["pin"] == "valley-gate"
   and math.dist(AN["dellhollow"]["impression"]["pinAt"][:2],
                 PT["dellhollow-valley-gate"]["at"][:2]) < 0.05)

print()
print("=" * 92)
print("C.  THE PROSE — every sentence that names a bank, checked against the geometry")
print("=" * 92)
ck("world: Dellhollow's note says EAST/RIGHT bank",
   says(LM["dellhollow"]["note"], "east bank", "right bank")
   and not re.search(r"mass is on the WEST", LM["dellhollow"]["note"]))
ck("world: the Moorage note says EAST bank", says(LM["dellhollow-moorage"]["note"], "east"))
ck("world: the far wall is the WEST / left-bank wall",
   says([m for m in W["massifs"] if m["id"] == "farwall"][0]["note"], "west", "left-bank"))
ck("world: the north rim no longer calls itself reachable",
   not says([m for m in W["massifs"] if m["id"] == "northwall"][0]["note"], "reachable (left-bank) side"))
ck("world: the pocket terrace note says the road's (east) bank",
   says(W["riverSpine"]["points"][10]["note"], "east"))
ck("world: the notch note names the culvert",
   says(W["riverSpine"]["points"][5]["note"], "culvert"))
ck("world: the Old Gate note names the crossing and denies a bridge",
   says(LM["old-gate"]["note"], "culverted", "no bridge"))
ck("region: _doc says the bench is EAST below the gate",
   says(" ".join(R["_doc"]), "east wall", "right bank looking downstream"))
ck("region: _doc still puts the west bank above the gate",
   says(" ".join(R["_doc"]), "above the old gate the road holds the river's west bank"))
ck("region: canyon _doc says benchSide E",
   says(CN["_doc"], "benchside e"))
ck("region: the shelf doc says EAST (right) bank, river on the LEFT",
   says(CN["shelf"]["_doc"], "east (right) bank", "traveller's left"))
ck("region: road _doc says it crosses exactly once, at the gate",
   says(R["road"]["_doc"], "crosses exactly once", "no bridge"))
ck("region: the old 'NEVER CROSSES' claim survives only as a quoted correction",
   R["road"]["_doc"].count("NEVER CROSSES") == 1
   and "the old text" in R["road"]["_doc"])
ck("region: crossings.note names the culvert court",
   says(R["crossings"]["note"], "culverted gate court"))
ck("region: the valley-gate portal note says EAST rim",
   says(PT["dellhollow-valley-gate"]["note"], "east rim"))
ck("region: farwall-crown is atop the WEST wall",
   says([f for f in R["forests"] if f["id"] == "farwall-crown"]["note"]
        if False else [f for f in R["forests"] if f["id"] == "farwall-crown"][0]["note"], "west"))
ck("region: bench-fringe is right-bank woodland",
   says([f for f in R["forests"] if f["id"] == "bench-fringe"][0]["note"], "right-bank"))
ck("region: the far-wall crag override says WEST",
   any(says(z.get("note", ""), "west") for z in R["zoneOverrides"] if z["type"] == "crag"))
ck("region: the benchSide doc records the flip and its instrument",
   says(CN["_doc_benchSide"], "flipped", "0cebd6a"))
ck("region: the impression doc records the deleted mirror",
   says(AN["dellhollow"]["impression"]["_doc"], "no mirrory any more"))
ck("world: the impoundment sentence is stated",
   any(says(s, "impoundment") and says(s, "east drainage") for s in W["_doc"]))

print()
print("=" * 92)
print("D.  THE PINCH, THE COURT AND THE TOWN MAPS")
print("=" * 92)
gr_t = 6.95                       # the town's grate, as built (round 4)
door_t, found_t = 4.90, 3.55
off_t = door_t / 2 + found_t + gr_t / 2
hw_w = float(np.interp(GATE[1], SPINE[:, 1], SPW)) / 2
ck("the town's own doorway ratio is 2.727 half-widths",
   abs(off_t / (gr_t / 2) - 2.727) < 0.01, "%.3f" % (off_t / (gr_t / 2)))
_rw, _rt = bank(GATE)[0] / hw_w, off_t / (gr_t / 2)
ck("the world doorway keeps that ratio within 3%",
   abs(_rw - _rt) / _rt < 0.03,
   "world %.3f vs town %.3f half-widths (%.1f%%; the two half-widths are the SPINE's "
   "interpolated width here and the refined course's there, so 2%% IS the agreement "
   "between two derivations, not slop)" % (_rw, _rt, 100 * abs(_rw - _rt) / _rt))
court_ratio = 8.0 / gr_t
ck("the court's length is the town court's ratio, capped by the sill",
   CULV["lengthU"] <= court_ratio * 2.0 * hw_w + 1e-6,
   "%.2fu built, ratio wanted %.2fu" % (CULV["lengthU"], court_ratio * 2.0 * hw_w))
ck("Emberbrook's gate court is BEFORE its gate (the town says so too)",
   EP["gate-court"][1] < EP["sigil-gate"][1])
ck("the Old Gate seat is the town's sigil-gate at the impression scale",
   abs(math.dist(GATE[:2], AN["emberbrook"]["pos"][:2]) - 26.61) < 0.6,
   "%.2fu out (derived 26.61)" % math.dist(GATE[:2], AN["emberbrook"]["pos"][:2]))
ck("Emberbrook's impression scale is stated and positive",
   AN["emberbrook"]["impression"]["scale"] > 0)
ck("Dellhollow's scale keeps the towns comparable (ratio 0.7..1.0)",
   0.7 < AN["dellhollow"]["impression"]["scale"] / AN["emberbrook"]["impression"]["scale"] < 1.0,
   "%.3f" % (AN["dellhollow"]["impression"]["scale"] / AN["emberbrook"]["impression"]["scale"]))
ck("Dellhollow's moorage is UPSTREAM of lock-five in its own map",
   DP["moorage"][0] < DP["lock-five"][0])
ck("...and the world note says so too",
   says(LM["dellhollow-moorage"]["note"], "upstream of the locks"))
ck("the only 'bridge' in Emberbrook's map is the brook plank",
   [k for k in EP if "bridge" in k] == ["brook-bridge"])
# THE TWO WATERCOURSES STAY FENCED BY AN INSTRUMENT, NOT BY MEMORY.  The coordinator's
# crossing stamp (90178fe) first read "the BROOK runs under the paved court".  It is the
# RIVER: at the sigil gate's own latitude the town's river course runs 9.6 m east of it
# (the round-3 tail that brings the channel against the gate), while the brook is a
# different, named watercourse joining 76 m to the south — brook-spring -> brook-bridge
# -> brook-mouth.  The confusion matters more than a typo, because brook-bridge is the
# only thing in the world legitimately called a bridge and the assertion above depends
# on it: a note saying the brook goes under the gate gives the town a second crossing it
# does not have.  Corrected upward and fenced here in the same commit.
ck("Emberbrook's crossing stamp names the RIVER, not the brook",
   says(EN["sigil-gate"], "culvert-court")
   and "brook runs under" not in EN["sigil-gate"],
   "brook-* is a different watercourse; brook-bridge is the world's only legal bridge")
ck("...and the stamp still denies a span",
   says(EN["sigil-gate"], "no bridge, no span"))
ck("downstream-vista is still NEVER REACHED after the crossing amendment",
   says(EN["downstream-vista"], "never reached")
   and says(EN["downstream-vista"], "dam crest remains the river's only span"))
ck("Dellhollow's dam-crest-gate exists (the world's only span)",
   "dam-crest-gate" in DP)
ck("no landmark anywhere in the region is named a bridge",
   not any("bridge" in l["id"] for l in R.get("landmarks", []) + W["landmarks"]))

print()
print("=" * 92)
print("E.  THE TRIBUTARIES AND THE HANDOFF")
print("=" * 92)
TR = R.get("tributaries", {}).get("list", [])
ck("the region declares tributaries", len(TR) >= 1, "%d" % len(TR))
ck("Hollowmere has an outlet", any(t["id"] == "hollowmere-outlet" for t in TR))
for t in TR:
    ck("%s descends from head to mouth" % t["id"],
       t["points"][0][2] > t["points"][-1][2],
       "%.2f -> %.2f" % (t["points"][0][2], t["points"][-1][2]))
    ck("%s ends ON the channel" % t["id"], bank(t["points"][-1])[1] < 14.0,
       "%.2fu from the water" % bank(t["points"][-1])[1])
    ck("%s joins BELOW the Old Gate" % t["id"], arc_of(t["points"][-1]) > GATE_ARC)
ck("the tributary doc records its instrument",
   says(R["tributaries"]["_doc"], "flow accumulation", "valley_tribprobe.py"))
ck("the region hands off a still-widening river",
   W["riverSpine"]["points"][-1].get("continues") is True
   and W["riverSpine"]["points"][-1]["width"] >= 28)
ck("the water exit carries the same width the spine hands over",
   [e for e in REG["exits"] if e["id"] == "gorge-water-exit"][0]["carries"]["width"]
   == W["riverSpine"]["points"][-1]["width"])
ck("Hollowmere Pass is still sealed", LM["pass-hollowmere"].get("state") == "sealed")
ck("Hollowmere Pass is on the FAR bank now, and says so",
   bank(LM["pass-hollowmere"]["pos"])[0] > 0
   and says(LM["pass-hollowmere"]["note"], "far"))
ck("the tile is STATED, and its origin is its centre",
   abs(REG["tile"]["origin"][0] - REG["tile"]["size"][0] / 2) < 1e-9
   and abs(REG["tile"]["origin"][1] - REG["tile"]["size"][1] / 2) < 1e-9)

print()
print("=" * 92)
print("%d assertions, %d failed" % (N, FAIL))
if _fails:
    for f in _fails:
        print("  FAILED  " + f)
print("=" * 92)
sys.exit(1 if FAIL else 0)
