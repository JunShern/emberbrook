"""t2_probe_report.py — the reporting layer over tools/t2_probe_tally.py's JSON.

  python3 tools/t2_probe_report.py <tally.json> [all|A|B|C|D|E]

Plain python, no Blender.  Sections:
  A  per-camera screen composition by family (cliff/terrain, vista, built, roof,
     foliage, water, accent, sky/haze) plus cliff_town's own share
  B  cliff_town's screen bbox and fill per camera — the placeholder audit
  C  resolution audit: visible rock/terrain/vista surfaces ranked by visual cost
     (screen-% x coarseness), with px_per_edge
  D  existing accent (pops of colour) screen-% per camera
  E  what each camera sees: top 12 objects by screen area, for placement targeting

The family classifier and the ACCENT_MATS set are the definitions the three
tranche-2 plans are written against; change them and the plans' numbers stop
being comparable.
"""
import json, base64, struct, math, collections as C, sys, os

TALLY = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tally.json"
assert os.path.exists(TALLY), "usage: python3 tools/t2_probe_report.py <tally.json> [all|A|B|C|D|E]"
T = json.load(open(TALLY))
CAM = T["cameras"]
BW, BH = 2688, 1536

ORDER = ["gate", "shelf-west", "shelf-east", "loop-stairs", "quay-west", "quay-east",
         "lockhead", "cottage", "crossing", "weave", "deep-stairs", "boatyard",
         "waterfront", "fishdock", "cottage-steps", "lockfive", "north-landing"]

ACCENT_MATS = set("""mat_flag_blue mat_flag_green mat_flag_ochre mat_flag_red
mat_gate_flag_blue mat_gate_flag_blue2 mat_gate_flag_ochre mat_gate_flag_red mat_gate_flag_red2
mat_shelf_cloth mat_qm_cloth mat_shelf_awning mat_qm_awning
mat_paint_blue mat_paint_red mat_pumpkin
mat_shelf_paint_madder mat_shelf_paint_ochre mat_shelf_paint_rust mat_shelf_paint_slate
mat_shelf_paint_teal mat_shelf_paint_bone mat_shelf_paint_green
mat_qm_paint_blue mat_qm_paint_bone mat_qm_paint_green mat_qm_paint_ochre mat_qm_paint_red""".split())
ROOF = set("mat_shingle_mossy mat_shingle_cedar mat_shingle_slate mat_shingle_shake lf_shingle".split())
FXOBJ = set(["fx_haze_far", "fx_haze_mid", "fx_haze_rim", "fx_dam4_spray", "fx_dam4_foam",
             "fx_kettle_smoke", "fx_kettle_smoke_plume", "fx_qm_smoke"])
VISTA = set(["cliff_town", "cliff_far", "cliff_far_toe", "fx_ridge_upstream",
             "fx_ridge_upstream_mid", "fx_far_town_silhouette", "fx_far_town_base",
             "fx_far_town_base.001", "riverbed", "lf_riverbed_tail", "lf_farbank_tail"])

def family(name, mats):
    if name in FXOBJ: return "sky/haze"
    if name in VISTA: return "vista"
    ms = set(m for m in mats if m)
    if "m_water" in ms: return "water"
    if ms & ROOF: return "roof"
    if ms & ACCENT_MATS: return "accent"
    if any(("leaf" in m or "vine" in m or "frond" in m or "grass" in m) for m in ms): return "foliage"
    if name.startswith("veg_"): return "foliage"
    if any(k in m for m in ms for k in ("rock", "cliff", "ground", "stone", "paving", "gravel")): return "cliff/terrain"
    return "built"

def decode(c):
    gw, gh = c["gw"], c["gh"]
    return gw, gh, struct.unpack("<%dH" % (gw * gh), base64.b64decode(c["objid"]))

mode = sys.argv[2] if len(sys.argv) > 2 else "all"

if mode in ("all", "A"):
    print("=" * 120)
    print("A. PER-CAMERA SCREEN COMPOSITION  (224x128 ray grid, %% of frame)")
    print("=" * 120)
    hdr = ["cliff/terrain", "vista", "built", "roof", "foliage", "water", "accent", "sky/haze"]
    print("%-15s " % "camera" + "".join("%9s" % h[:9] for h in hdr) + "  %10s" % "cliff_town")
    for cid in ORDER:
        c = CAM[cid]; gw, gh, a = decode(c); tot = gw * gh
        fam = C.Counter(); ct = 0
        for v in a:
            if v == 0xFFFF: fam["sky/haze"] += 1; continue
            n = c["names"][v]
            if n == "cliff_town": ct += 1
            fam[family(n, c["objects"][n]["mats"])] += 1
        print("%-15s " % cid + "".join("%8.1f%%" % (100.0 * fam[h] / tot) for h in hdr) + "  %9.1f%%" % (100.0 * ct / tot))

if mode in ("all", "B"):
    print()
    print("=" * 120)
    print("B. cliff_town — 8 verts / 6 polys / m_rock (flat untextured Principled 0.166,0.156,0.146 rough 0.9)")
    print("=" * 120)
    print("%-15s %8s %8s %8s   %-34s %s" % ("camera", "screen%", "dmean", "dmin", "screen bbox in 2688x1536", "hits are a solid block?"))
    for cid in ORDER:
        c = CAM[cid]; gw, gh, a = decode(c)
        o = c["objects"].get("cliff_town")
        if not o: print("%-15s %8s" % (cid, "  --")); continue
        xs = []; ys = []
        for i, v in enumerate(a):
            if v != 0xFFFF and c["names"][v] == "cliff_town":
                xs.append(i % gw); ys.append(i // gw)
        sx, sy = BW / gw, BH / gh
        bw = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
        print("%-15s %7.1f%% %8.1f %8.1f   (%4d,%4d)-(%4d,%4d)%s  fill %.0f%% of its bbox"
              % (cid, 100.0 * o["px"] / (gw * gh), o["dmean"], o["dmin"],
                 int(min(xs) * sx), int(min(ys) * sy), int((max(xs) + 1) * sx), int((max(ys) + 1) * sy),
                 " " * 6, 100.0 * len(xs) / bw))

if mode in ("all", "C"):
    print()
    print("=" * 120)
    print("C. RESOLUTION AUDIT — visible rock/terrain/vista surfaces. px_per_edge = shipped pixels one mesh edge spans.")
    print("=" * 120)
    rows = []
    for cid in ORDER:
        c = CAM[cid]; gw, gh = c["gw"], c["gh"]
        ty = math.tan(math.radians(c["fov"]) / 2)
        for n, o in c["objects"].items():
            if o["px"] < 50: continue
            if family(n, o["mats"]) not in ("cliff/terrain", "vista"): continue
            ppe = o["edge"] * ((BH / 2.0) / (o["dmean"] * ty))
            rows.append((100.0 * o["px"] / (gw * gh), ppe, cid, n, o))
    rows.sort(key=lambda r: -(r[0] * min(r[1], 900)))
    print("%-15s %-26s %8s %9s %8s %8s %7s %7s %8s" %
          ("camera", "object", "screen%", "px/edge", "dmean", "dmin", "verts", "polys", "edge_m"))
    for scr, ppe, cid, n, o in rows[:38]:
        print("%-15s %-26s %7.1f%% %9.0f %8.1f %8.1f %7d %7d %8.2f"
              % (cid, n, scr, ppe, o["dmean"], o["dmin"], o["verts"], o["polys"], o["edge"]))

if mode in ("all", "D"):
    print()
    print("=" * 120)
    print("D. EXISTING ACCENT (pops of colour) screen-% per camera")
    print("=" * 120)
    for cid in ORDER:
        c = CAM[cid]; gw, gh, a = decode(c); tot = gw * gh
        cnt = C.Counter()
        for v in a:
            if v == 0xFFFF: continue
            n = c["names"][v]
            if family(n, c["objects"][n]["mats"]) == "accent": cnt[n] += 1
        s = sum(cnt.values())
        top = ", ".join("%s %.2f" % (n, 100.0 * k / tot) for n, k in cnt.most_common(5))
        print("%-15s %7.2f%%   %s" % (cid, 100.0 * s / tot, top or "(none)"))

if mode in ("all", "E"):
    print()
    print("=" * 120)
    print("E. WHAT EACH CAMERA SEES — top 12 objects by screen area (for placement targeting)")
    print("=" * 120)
    for cid in ORDER:
        c = CAM[cid]; gw, gh = c["gw"], c["gh"]; tot = gw * gh
        items = sorted(c["objects"].items(), key=lambda kv: -kv[1]["px"])[:12]
        print("\n-- %s  pos=%s aim=%s" % (cid, [round(v, 1) for v in c["pos"]], [round(v, 1) for v in c["aim"]]))
        for n, o in items:
            print("     %-30s %6.2f%%  d %5.1f-%5.1f  %-12s %s" %
                  (n, 100.0 * o["px"] / tot, o["dmin"], o["dmax"], family(n, o["mats"]), str(o["mats"])[:46]))
