#!/usr/bin/env python3
"""make_review_board.py — assemble the morning review board for Dellhollow.

Scans render outputs + the town map and emits public/review/dellhollow-morning.html
(served at http://localhost:8899/review/dellhollow-morning.html). Idempotent; run
whenever new renders land. Static HTML, no deps; paths relative to /public.
"""
import json, os, glob, html, datetime

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MAP = json.load(open(REPO + "/public/townmap/dellhollow.map.json"))
OUT = REPO + "/public/review/dellhollow-morning.html"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def rel(p):  # repo path -> web path relative to /public root
    return p.split("/public/")[-1] if "/public/" in p else "../" + p.split(REPO + "/")[-1]

def latest(pattern):
    fs = sorted(glob.glob(pattern))
    return fs[-1] if fs else None

def all_versions(pattern):
    return sorted(glob.glob(pattern))

lm_by_id = {l["id"]: l for l in MAP["landmarks"]}
now = datetime.datetime.now().strftime("%H:%M")

S = []
S.append("""<meta charset="utf-8"><title>Dellhollow — morning review board</title>
<style>
 :root{--bg:#140f0c;--card:#221913;--ink:#ece0d0;--dim:#a89179;--warm:#e9a24b;--line:#3a2c20;--ok:#7ec97e;--warn:#e0b050}
 *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
 main{max-width:1200px;margin:0 auto;padding:24px}
 h1{font-size:24px;margin:8px 0} h1 em{color:var(--warm);font-style:normal}
 h2{font-size:15px;text-transform:uppercase;letter-spacing:1.4px;color:var(--warm);margin:36px 0 10px}
 .sub{color:var(--dim)} .note{background:#1c150f;border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:10px 0;font-size:13.5px}
 .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
 .card img{width:100%;display:block} .card .m{padding:8px 12px;font-size:13px}
 .card .m b{font-size:14px} .pill{display:inline-block;font-size:11px;border:1px solid var(--line);border-radius:12px;padding:0 8px;color:var(--dim);margin-left:6px}
 .pair{display:grid;grid-template-columns:1fr 1fr;gap:0} .pair figure{margin:0} .pair figcaption{text-align:center;font-size:11px;color:var(--dim);padding:2px}
 details{margin:6px 12px 12px} summary{cursor:pointer;color:var(--dim);font-size:13px}
 ul.decisions li{margin:6px 0} .big a{color:var(--warm)}
 .versions{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 12px} .versions a{color:var(--dim);font-size:12px}
</style><main>""")
S.append(f"<h1>Dellhollow — <em>morning review board</em> <span class='sub'>(generated {now})</span></h1>")

# ---- 0. decisions queue ----
S.append("<h2>Decisions queued for you</h2><ul class='decisions'>")
for dec in [
  "Projection: <b>ortho vs persp</b> — flip through the shot pairs below and call it (persp recommended).",
  "Approve / redline each of the <b>13 draft scene cameras</b> (framing, direction, intimacy).",
  "Quality gate: does the <b>Boatyard probe</b> hit the pilot bar? (My verdicts + iterations below.)",
  "Interior approvals: each interior's latest version below — accept or name the fix.",
  "The Crossing parcel has no landmarks (pure bridge transit) — bless the concept or fold it into Weave/Cottage.",
]:
    S.append(f"<li>{dec}</li>")
S.append("</ul>")

# ---- 1. walk the town ----
S.append("<h2>Walk the gray town</h2>")
S.append("<div class='note big'>Whole-town walkable build: <a href='../play3d.html?scene=townwalk&char=vesper'>play3d.html?scene=townwalk</a> — WASD; the full network is verified connected (all 33 landmarks, one component). Map/contract viewer: <a href='../townmap/viewer.html?town=dellhollow'>townmap viewer</a>.</div>")

# ---- 2. shot pairs ----
S.append("<h2>Draft scene shots — 13 scenes, ortho vs persp</h2><div class='grid'>")
for p in MAP["parcels"]:
    key = p["sceneKey"]
    o = latest(REPO + f"/docs/qa/shots/dellhollow/{key}_ortho.png")
    pe = latest(REPO + f"/docs/qa/shots/dellhollow/{key}_persp.png")
    if not (o or pe):
        continue
    cam = p.get("camera", {})
    members = ", ".join(p.get("members", [])) or "(transit scene — no landmarks)"
    S.append("<div class='card'><div class='pair'>")
    for img, lbl in ((o, "ortho"), (pe, f"persp 35°")):
        if img:
            S.append(f"<figure><img src='{rel(img)}' loading='lazy'><figcaption>{lbl}</figcaption></figure>")
    S.append("</div><div class='m'>")
    S.append(f"<b>{html.escape(p['name'])}</b><span class='pill'>{key}</span><span class='pill'>draft</span><br>")
    S.append(f"<span class='sub'>{html.escape(cam.get('note',''))}</span>")
    S.append(f"<details><summary>contract</summary><div class='sub'>contains: {html.escape(members)}<br>intent: {html.escape(p.get('intent',''))}</div></details>")
    S.append("</div></div>")
S.append("</div>")

# ---- 3. quality probe ----
S.append("<h2>Boatyard quality probe (exterior detail bar)</h2>")
probes = all_versions(REPO + "/docs/qa/dellhollow-rebuild/probe_v*.png")
if probes:
    S.append(f"<div class='card'><img src='{rel(probes[-1])}'><div class='m'><b>latest: {os.path.basename(probes[-1])}</b> — judged against the pilot slice; my iteration critiques are in the morning report.</div>")
    S.append("<div class='versions'>" + " ".join(f"<a href='{rel(v)}'>{os.path.basename(v)}</a>" for v in probes) + "</div></div>")
else:
    S.append("<div class='note'>No probe renders found.</div>")

# ---- 4. interiors ----
S.append("<h2>Interiors (quality-first; latest version each)</h2><div class='grid'>")
INTERIORS = [("cottage-int","Keepers' Cottage — supper"), ("item-int","Item Shop (chandlery)"),
             ("inn-int","Inn — The Boatmen's Rest"), ("cookhouse-int","Cookhouse"),
             ("weapon-int","Weapon Shop"), ("armor-int","Armor Shop")]
for key, name in INTERIORS:
    v = latest(REPO + f"/docs/qa/interiors/{key}_v*.png")
    if v:
        vers = all_versions(REPO + f"/docs/qa/interiors/{key}_v*.png")
        S.append(f"<div class='card'><img src='{rel(v)}' loading='lazy'><div class='m'><b>{name}</b><span class='pill'>{os.path.basename(v)}</span></div>")
        S.append("<div class='versions'>" + " ".join(f"<a href='{rel(x)}'>{os.path.basename(x).split('_')[-1].split('.')[0]}</a>" for x in vers) + "</div></div>")
    else:
        S.append(f"<div class='card'><div class='m'><b>{name}</b><span class='pill'>not yet built</span></div></div>")
S.append("</div>")

S.append("<h2>Everything else</h2><div class='note'>Full overnight log + verdicts: see the morning report in the chat. All work committed on <b>migration/3d-hybrid</b>; nothing pushed to main; all cameras/parcels flagged draft pending your review.</div>")
S.append("</main>")

open(OUT, "w").write("\n".join(S))
print("board ->", OUT)
