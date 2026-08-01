"""emb_boardfill.py — fill the town-wide board's spec from the frames and the run log.

    python3 tools/emb_boardfill.py [--log <path>] [--spec docs/qa/emberbrook/dressed/board.json]

WHAT THIS IS.  `tools/emb_board.py` renders a board from a JSON spec; this writes the parts
of that spec which are FACTS ABOUT A RUN — which frames exist, what camera each was taken
from, and which of them the solver reported occluded.  Those three things are printed by
`emb_dress --shotset town` and nowhere else, so typing them into the spec by hand would be
transcription, and transcription is what this repo's own documentation bar exists to
refuse.  The prose in the spec is written by a person; everything with a number in it comes
through here.

WHAT IT IS NOT.  It does not judge a frame and it does not choose one.  A frame that the
solver reported occluded is carried onto the board WITH that report attached, because a
board that quietly drops its worst frame is not a review board.
"""
import json
import os
import re
import sys

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
DRESSED = os.path.join(REPO, "docs/qa/emberbrook/dressed")

DISTRICT_TITLE = {
    "district-entrance": "Village Entrance — the arch, the orchard, the cider press",
    "district-square": "Festival Square — the Heartlight, the dais, the stalls",
    "district-lane": "Pond Lane — the pond, the jetty, the weir",
    "district-homerow": "Home Row — the households, the mill, the brook",
    "district-gateroad": "The Gate Road — the tithe barn and the dovecote",
    "district-gatefield": "The Gate Field — the Old Gate court",
    "district-woodroad": "Whisperwood Road — the arrival clearing and the Waystone",
}
AERIAL_TITLE = {
    "aerial-south": "From the south, on the arrival bearing — the whole village",
    "aerial-east": "From the east, over the river",
    "aerial-core": "The core, at 0.55x the town's radius",
}


def opt(f, d):
    return sys.argv[sys.argv.index(f) + 1] if f in sys.argv else d


def parse_log(path):
    """Per frame: the label the solver printed, its camera line, and its report lines."""
    out, cur = {}, None
    for ln in open(path, errors="replace"):
        m = re.match(r"\s*SHOT ([a-z0-9-]+)\s+(.*)$", ln)
        if m:
            cur = m.group(1)
            out[cur] = {"label": m.group(2).strip(), "rep": [], "cam": ""}
            continue
        if cur is None:
            continue
        if "camera (" in ln:
            out[cur]["cam"] = ln.strip()
        elif ln.startswith("           ") and ln.strip():
            out[cur]["rep"].append(ln.strip())
        elif ln.startswith("  WROTE") or ln.startswith("  SHOT"):
            pass
    return out


def main():
    spec_p = opt("--spec", os.path.join(DRESSED, "board.json"))
    logp = opt("--log", "")
    log = parse_log(logp) if logp and os.path.exists(logp) else {}
    spec = json.load(open(spec_p))
    tag = opt("--tag", "town")
    have = sorted(f for f in os.listdir(DRESSED) if f.endswith(".png"))

    def shots_for(prefix, titles):
        out = []
        for key in titles:
            fn = "%s-%s.png" % (tag, key)
            if fn not in have:
                continue
            info = log.get(key, {})
            occ = [r for r in info.get("rep", []) if "OCCLUDED" in r or "NO TREAD" in r]
            cap = titles[key]
            if occ:
                cap += "  **The solver reported this frame occluded and it is on the board "
                cap += "anyway.**"
            meta = " · ".join(x for x in (info.get("cam", ""), info.get("label", "")) if x)
            for r in info.get("rep", []):
                if r.startswith("target ") or "NO TREAD" in r or "OCCLUDED" in r:
                    meta += " · " + r
            out.append({"src": fn, "caption": cap, "meta": meta})
        return out

    for s in spec["sections"]:
        if s["id"] == "aerials":
            s["shots"] = shots_for("aerial", AERIAL_TITLE)
        elif s["id"] == "districts":
            s["shots"] = shots_for("district", DISTRICT_TITLE)
        elif s["id"] == "beforeafter":
            pairs = []
            for key in list(AERIAL_TITLE) + list(DISTRICT_TITLE):
                a = "%s-%s.png" % (tag, key)
                b = "%s-nodress-%s.png" % (tag, key)
                if a in have and b in have:
                    pairs.append({
                        "before": b, "after": a,
                        "before_label": "blockout", "after_label": "dressed",
                        "caption": AERIAL_TITLE.get(key) or DISTRICT_TITLE.get(key, key),
                        "meta": (log.get(key, {}) or {}).get("cam", "")})
            s["pairs"] = pairs
    json.dump(spec, open(spec_p, "w"), indent=2)
    n = sum(len(s.get("shots", [])) + len(s.get("pairs", [])) for s in spec["sections"])
    print("  %d frames on disk, %d placed into %s" % (len(have), n, spec_p))
    for s in spec["sections"]:
        k = len(s.get("shots", [])) + len(s.get("pairs", []))
        print("    %-14s %d" % (s["id"], k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
