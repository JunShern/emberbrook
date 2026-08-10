"""rawrate.py — RAW PER-LOOK JUDGE RATES, NEVER SURVIVOR COUNTS.

  python3 rawrate.py <runA> <runB>

Round 12's law: a survivor count is the judge's FIRST look convolved with the
adversarial refuter's SECOND, and the two can move in opposite directions.  This
reads `raw/<shot>.json`'s `naive_k` replies — the judge's own first look, N of
them per plate — and reports findings per look, overall and by phrase class,
with the standard deviation across looks.
"""
import sys, os, json, re
import numpy as np

CLASSES = {
    "untextured / flat / plain": r"untextur|flat[- ]?(shad|colou?r|surface)|plain|no texture|featureless|blank",
    "block / box / cube / primitive": r"\bcube|\bbox(es|y)?\b|block(y|s)?\b|primitive|placeholder|rectangular prism",
    "floating / clipping": r"float|clip|intersect|hover|unsupported|mid-?air|not connected|sink(ing)? into",
    "dark / shadow / obscured": r"dark|shadow|obscur|unlit|murk|gloom",
    "cave / pitch-black / void": r"pitch[- ]?black|void|cave|abyss|black hole|completely black",
    "vegetation / foliage": r"foliage|vegetat|plant|leaf|leaves|shrub|bush|tree",
    "mesh / grid / screen / weave": r"\bmesh\b|grid|screen[- ]?door|gauze|wire|weave|lattice",
    "white / blown": r"\bwhite\b|blown|overexpos|washed[- ]?out|glaring",
    "water / foam": r"water|foam|ripple|wave|spill|waterline",
    "cloth / awning / canvas": r"awning|canvas|cloth|tarp|fabric|sail",
}


def looks(run):
    out = {}
    rp = os.path.join(run, "raw")
    for fn in sorted(os.listdir(rp)):
        shot = fn[:-5]
        d = json.load(open(os.path.join(rp, fn)))
        per = []
        for k in sorted([k for k in d if k.startswith("naive_")],
                        key=lambda s: int(s.split("_")[1])):
            t = d[k]
            try:
                j = json.loads(re.sub(r"^```(json)?|```$", "", t.strip(), flags=re.M))
                fs = j.get("findings", [])
            except Exception:
                fs = []
            per.append([(f.get("desc", "") + " " + str(f.get("where", ""))).lower()
                        for f in fs])
        out[shot] = per
    return out


def report(name, L):
    shots = sorted(L)
    n = len(next(iter(L.values())))
    tot = np.array([sum(len(L[s][k]) for s in shots) for k in range(n)], float)
    print("\n%s — %d plates x N=%d looks" % (name, len(shots), n))
    print("  TOTAL findings per look   %.2f  sd %.2f" % (tot.mean(), tot.std(ddof=1)))
    rows = {}
    for lab, pat in CLASSES.items():
        r = re.compile(pat)
        v = np.array([sum(1 for s in shots for d in L[s][k] if r.search(d))
                      for k in range(n)], float)
        rows[lab] = (v.mean(), v.std(ddof=1))
        print("  %-34s %5.2f  sd %.2f" % (lab, v.mean(), v.std(ddof=1)))
    print("  per plate (findings per look):")
    for s in shots:
        v = np.array([len(L[s][k]) for k in range(n)], float)
        print("     %-14s %5.2f sd %.2f" % (s, v.mean(), v.std(ddof=1)))
    return tot, rows


A, B = sys.argv[1], sys.argv[2]
la, lb = looks(A), looks(B)
ta, ra = report("BEFORE " + os.path.basename(A), la)
tb, rb = report("AFTER  " + os.path.basename(B), lb)
print("\n=== RAW PER-LOOK, BEFORE -> AFTER ===")
print("%-34s %8s %8s" % ("class", "before", "after"))
print("%-34s %8.2f %8.2f" % ("TOTAL", ta.mean(), tb.mean()))
for lab in CLASSES:
    print("%-34s %8.2f %8.2f" % (lab, ra[lab][0], rb[lab][0]))
print("\nper plate, findings per look:")
for s in sorted(set(la) & set(lb)):
    va = np.mean([len(la[s][k]) for k in range(len(la[s]))])
    vb = np.mean([len(lb[s][k]) for k in range(len(lb[s]))])
    print("  %-14s %5.2f -> %5.2f" % (s, va, vb))
