#!/usr/bin/env python3
"""battle_party_stats.py — DOES THE PARTY SHARE THIS VALLEY'S PAINT.

    python3 tools/battle_party_stats.py --tag pair
    python3 tools/battle_party_stats.py --tag pair --json docs/qa/battle-party/stats-pair.json

Reads what tools/battle_party.mjs measured (census-<tag>.json + hist-<tag>.json) and
answers the four questions the lane was opened on, in this order, because the order
is what keeps it honest:

 1. THE TERRAIN. Across the census, what value/saturation does the background
    BEHIND A PARTY BODY actually occupy — the ring around that body's own mask,
    read off the frame with the cast removed. Reported as a distribution, by zone.

 2. THE OVERLAP, PER BODY. Each party body's own on-screen V/S distribution
    against that ring's, as a histogram INTERSECTION (1 = the body's paint and the
    terrain's paint occupy the same values entirely). Plus the signed median gap.

 3. THE CONTROL THAT DECIDES IT. The two FOES are in the frame, measured by the
    same ruler, at the same sites — and bet H graded them INTO the party's band.
    If the party fails to read where creatures wearing the party's own band read
    fine, the shared band is not what is failing.

 4. THE COUNTERFACTUAL. For each body the shift of its measured V histogram that
    MINIMISES overlap with its own terrain ring, and the overlap it reaches. This
    prices a regrade before anyone proposes one: if the terrain's own distribution
    is broad, the best reachable overlap is still high and no albedo escapes it.

DISCRIMINATION IS AUC, not a correlation: "does this axis separate the bodies that
fail to read from the ones that do" is a ranking question, which is what the
placement lane used and what makes these numbers comparable with its 0.922/0.843.
FAILS TO READ is edgeRGB < 5, the rim spike's own threshold, unchanged.
"""
import argparse, json, math, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA = 'docs/qa/battle-party'
FAIL = 5.0          # edgeRGB below this = the body does not read (rim spike's threshold)


def pct(xs, p):
    if not xs: return None
    a = sorted(xs)
    return round(a[min(len(a) - 1, int(len(a) * p))], 4)


def auc(pos, neg):
    """P(a random positive ranks above a random negative). Ties count a half."""
    if not pos or not neg: return None
    n = 0.0
    for a in pos:
        for b in neg:
            n += 1.0 if a > b else (0.5 if a == b else 0.0)
    return round(n / (len(pos) * len(neg)), 3)


def qh(h, p):
    a = 0.0
    for i, v in enumerate(h):
        a += v
        if a >= p: return (i + 0.5) / len(h)
    return 1.0


def inter(a, b):
    return sum(min(x, y) for x, y in zip(a, b))


def shifted(h, k):
    """Shift a normalised histogram by k bins, piling anything that runs off the
    end into the end bin. A grade cannot move paint outside 0..1 either."""
    n = len(h)
    out = [0.0] * n
    for i, v in enumerate(h):
        out[min(n - 1, max(0, i + k))] += v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='pair')
    ap.add_argument('--json', default=None)
    a = ap.parse_args()

    cen = json.load(open(os.path.join(ROOT, QA, f'census-{a.tag}.json')))
    hf = os.path.join(ROOT, QA, f'hist-{a.tag}.json')
    hist = {r['id']: r['hist'] for r in json.load(open(hf))['hist']} if os.path.exists(hf) else {}
    rows = cen['rows']
    print(f"census {a.tag}: {len(rows)} sites, party={cen['meta']['party']}, yaw={cen['meta']['yaw']}, "
          f"{cen['meta']['secs']}s, three=r{cen['meta']['three']}")

    recs = []
    for r in rows:
        for b in r['bodies']:
            b = dict(b); b['site'] = r['id']; b['zone'] = r['zone']; recs.append(b)
    party = [b for b in recs if b['side'] == 'party']
    foes = [b for b in recs if b['side'] == 'foe']
    out = {'meta': cen['meta'], 'n': {'sites': len(rows), 'party': len(party), 'foe': len(foes)}}

    # ---------------------------------------------------------------- 1. terrain
    print('\n== 1. THE TERRAIN BEHIND A PARTY BODY (ring of that body\'s own mask, cast removed)')
    print(f'{"zone":9} {"n":>4} {"ringV p05":>10} {"p25":>7} {"p50":>7} {"p75":>7} {"p95":>7} '
          f'{"ringS p50":>10} {"clutter":>8}')
    terr = {}
    for z in ['ALL'] + sorted({b['zone'] for b in party}):
        g = party if z == 'ALL' else [b for b in party if b['zone'] == z]
        v50 = [b['ringV']['p50'] for b in g if b.get('ringV')]
        row = dict(n=len(g),
                   v05=pct([b['ringV']['p05'] for b in g if b.get('ringV')], .5),
                   v25=pct([b['ringV']['p25'] for b in g if b.get('ringV')], .5),
                   v50=pct(v50, .5), v50lo=pct(v50, .05), v50hi=pct(v50, .95),
                   v75=pct([b['ringV']['p75'] for b in g if b.get('ringV')], .5),
                   v95=pct([b['ringV']['p95'] for b in g if b.get('ringV')], .5),
                   s50=pct([b['ringS']['p50'] for b in g if b.get('ringS')], .5),
                   clutter=pct([b['clutter'] for b in g], .5))
        terr[z] = row
        print(f'{z:9} {row["n"]:4} {row["v05"]:10} {row["v25"]:7} {row["v50"]:7} {row["v75"]:7} '
              f'{row["v95"]:7} {row["s50"]:10} {row["clutter"]:8}')
    print(f'   median site ring spans V {terr["ALL"]["v05"]} .. {terr["ALL"]["v95"]}  '
          f'(that is the width ONE body sees, not the census range); '
          f'site-to-site the ring MEDIAN runs {terr["ALL"]["v50lo"]} .. {terr["ALL"]["v50hi"]}')
    out['terrain'] = terr

    # ------------------------------------------------------------- 2. per body
    print('\n== 2. EACH BODY: ITS OWN SCREEN BAND, THE TERRAIN\'S, AND THE OVERLAP')
    print(f'{"body":9} {"side":6} {"n":>3} {"bodyV50":>8} {"ringV50":>8} {"dV50":>7} '
          f'{"bodyS50":>8} {"ringS50":>8} {"ovlV":>6} {"ovlS":>6} {"edgeRGB":>8} {"6band":>6} {"fail<5":>7} {"hPct":>6}')
    per = {}
    for bid in sorted({b['id'] for b in recs}):
        g = [b for b in recs if b['id'] == bid]
        row = dict(side=g[0]['side'], n=len(g),
                   bodyV50=pct([b['bodyV']['p50'] for b in g], .5),
                   bodyV05=pct([b['bodyV']['p05'] for b in g], .5),
                   bodyV95=pct([b['bodyV']['p95'] for b in g], .5),
                   ringV50=pct([b['ringV']['p50'] for b in g], .5),
                   dV50=pct([b['dV50'] for b in g], .5),
                   absdV50=pct([abs(b['dV50']) for b in g], .5),
                   bodyS50=pct([b['bodyS']['p50'] for b in g], .5),
                   ringS50=pct([b['ringS']['p50'] for b in g], .5),
                   ovlV=pct([b['ovl']['ringV'] for b in g], .5),
                   ovlS=pct([b['ovl']['ringS'] for b in g], .5),
                   edgeRGB=pct([b['edgeRGB'] for b in g], .5),
                   edgeMean=round(sum(b['edgeRGB'] for b in g) / len(g), 2),
                   rowsAbs=pct([b['rowsAbs'] for b in g if b.get('rowsAbs') is not None], .5),
                   fails=sum(1 for b in g if b['edgeRGB'] < FAIL),
                   hPct=pct([b['hPct'] for b in g], .5))
        per[bid] = row
        print(f'{bid:9} {row["side"]:6} {row["n"]:3} {row["bodyV50"]:8} {row["ringV50"]:8} {row["dV50"]:7} '
              f'{row["bodyS50"]:8} {row["ringS50"]:8} {row["ovlV"]:6} {row["ovlS"]:6} '
              f'{row["edgeRGB"]:8} {str(row["rowsAbs"]):>6} {str(row["fails"]) + "/" + str(row["n"]):>7} {row["hPct"]:6}')
    out['perBody'] = per

    # per body x zone, worst first
    print('\n   worst body x terrain class, by median edgeRGB:')
    print(f'   {"body":9} {"zone":9} {"n":>3} {"edgeRGB":>8} {"fail<5":>7} {"ovlV":>6} {"|dV50|":>7} {"clutter":>8}')
    bz = {}
    for bid in sorted({b['id'] for b in recs}):
        for z in sorted({b['zone'] for b in recs}):
            g = [b for b in recs if b['id'] == bid and b['zone'] == z]
            if not g: continue
            bz[f'{bid}/{z}'] = dict(n=len(g), edgeRGB=pct([b['edgeRGB'] for b in g], .5),
                                    fails=sum(1 for b in g if b['edgeRGB'] < FAIL),
                                    ovlV=pct([b['ovl']['ringV'] for b in g], .5),
                                    absdV=pct([abs(b['dV50']) for b in g], .5),
                                    clutter=pct([b['clutter'] for b in g], .5),
                                    side=g[0]['side'])
    for k, v in sorted(bz.items(), key=lambda kv: kv[1]['edgeRGB']):
        bid, z = k.split('/')
        print(f'   {bid:9} {z:9} {v["n"]:3} {v["edgeRGB"]:8} {str(v["fails"]) + "/" + str(v["n"]):>7} '
              f'{v["ovlV"]:6} {v["absdV"]:7} {v["clutter"]:8}')
    out['bodyByZone'] = bz

    # --------------------------------------------------------------- 3. control
    print('\n== 3. THE CONTROL: FOES WEAR THE PARTY BAND (bet H graded them into it)')
    for side in ('party', 'foe'):
        g = [b for b in recs if b['side'] == side]
        f = [b for b in g if b['edgeRGB'] < FAIL]
        print(f'   {side:6} n={len(g):3}  edgeRGB p50={pct([b["edgeRGB"] for b in g], .5):6} '
              f'p05={pct([b["edgeRGB"] for b in g], .05):6}  fails<5 = {len(f)}/{len(g)} '
              f'({100.0 * len(f) / len(g):.1f}%)  ovlV p50={pct([b["ovl"]["ringV"] for b in g], .5)} '
              f' hPct p50={pct([b["hPct"] for b in g], .5)}  silPx p50={pct([b["silPx"] for b in g], .5)}')
    out['bySide'] = {s: dict(n=len([b for b in recs if b['side'] == s]),
                             edge50=pct([b['edgeRGB'] for b in recs if b['side'] == s], .5),
                             fails=len([b for b in recs if b['side'] == s and b['edgeRGB'] < FAIL]),
                             ovlV=pct([b['ovl']['ringV'] for b in recs if b['side'] == s], .5),
                             hPct=pct([b['hPct'] for b in recs if b['side'] == s], .5))
                     for s in ('party', 'foe')}

    # AUC: which axis separates the bodies that fail from the ones that read
    print('\n   WHICH AXIS SEPARATES A BODY THAT FAILS TO READ (edgeRGB<5) FROM ONE THAT DOES:')
    print(f'   {"axis":16} {"AUC all":>8} {"AUC party":>10}   (0.5 = chance; >0.5 = higher value means FAILS)')
    axes = {
        'ovl ringV': lambda b: b['ovl']['ringV'],
        'ovl ringS': lambda b: b['ovl']['ringS'],
        'ovl underV': lambda b: b['ovl']['underV'],
        '-|dV50|': lambda b: -abs(b['dV50']),
        '-|dS50|': lambda b: -abs(b['dS50']),
        'clutter': lambda b: b['clutter'],
        '-hPct': lambda b: -b['hPct'],
        'ringV50': lambda b: b['ringV']['p50'],
        'bodyV50': lambda b: b['bodyV']['p50'],
        'occl': lambda b: b['occl'] or 0,
    }
    aucs = {}
    for name, fn in axes.items():
        p_all = [fn(b) for b in recs if b['edgeRGB'] < FAIL]
        n_all = [fn(b) for b in recs if b['edgeRGB'] >= FAIL]
        p_p = [fn(b) for b in party if b['edgeRGB'] < FAIL]
        n_p = [fn(b) for b in party if b['edgeRGB'] >= FAIL]
        aucs[name] = dict(all=auc(p_all, n_all), party=auc(p_p, n_p))
        print(f'   {name:16} {str(aucs[name]["all"]):>8} {str(aucs[name]["party"]):>10}')
    out['auc'] = aucs

    # --------------------------------------------------------- 4. counterfactual
    if hist:
        print('\n== 4. THE COUNTERFACTUAL: THE BEST A VALUE REGRADE COULD DO')
        print('   Each body\'s measured V histogram shifted by k of 32 bins (k<0 darker, k>0 lighter),')
        print('   against ITS OWN terrain ring. "best" is the lowest overlap reachable at any shift.')
        print(f'   {"body":9} {"zone":9} {"n":>3} {"ovl now":>8} {"best":>6} {"at dV":>7} {"gain":>6}  '
              f'{"ovl at dV=+0.15":>15} {"-0.15":>7}')
        cf = {}
        for bid in sorted({b['id'] for b in recs}):
            for z in ['ALL'] + sorted({b['zone'] for b in recs}):
                cur, best, bestk, at_p, at_m = [], [], [], [], []
                for r in rows:
                    if z != 'ALL' and r['zone'] != z: continue
                    h = hist.get(r['id'], {}).get(bid)
                    if not h or not h.get('body') or not h.get('ring'): continue
                    hb, hr = h['body']['v'], h['ring']['v']
                    cur.append(inter(hb, hr))
                    scan = [(inter(shifted(hb, k), hr), k) for k in range(-16, 17)]
                    m = min(scan)
                    best.append(m[0]); bestk.append(m[1] / 32.0)
                    at_p.append(inter(shifted(hb, 5), hr))     # +0.156 in V
                    at_m.append(inter(shifted(hb, -5), hr))    # -0.156 in V
                if not cur: continue
                rec = dict(n=len(cur), now=pct(cur, .5), best=pct(best, .5), atk=pct(bestk, .5),
                           gain=round((pct(cur, .5) or 0) - (pct(best, .5) or 0), 4),
                           plus=pct(at_p, .5), minus=pct(at_m, .5))
                cf[f'{bid}/{z}'] = rec
                if z == 'ALL' or bid in ('vesper', 'maren', 'lake'):
                    print(f'   {bid:9} {z:9} {rec["n"]:3} {rec["now"]:8} {rec["best"]:6} {rec["atk"]:7} '
                          f'{rec["gain"]:6}  {rec["plus"]:15} {rec["minus"]:7}')
        out['counterfactual'] = cf

    # ---------------------------------------------- 5. THE FIXED GRADE, WHICH IS
    # WHAT A REGRADE ACTUALLY IS. Section 4 lets every site pick its own shift,
    # which prices a per-site treatment nobody can ship. An albedo grade is ONE
    # number for the whole game, so the honest question is the shift that
    # minimises overlap ACROSS the census — and whether the minimum is anywhere.
    if hist:
        print('\n== 5. ONE GRADE FOR THE WHOLE GAME: overlap vs a FIXED shift of the body\'s value')
        print(f'   {"body":9} {"k=0":>7} {"best fixed":>11} {"at dV":>7} {"gain":>7} {"worst site k=0":>15} '
              f'{"worst site best":>16}')
        fx = {}
        for bid in sorted({b['id'] for b in recs}):
            curve = {}
            for k in range(-16, 17):
                vals = []
                for r in rows:
                    h = hist.get(r['id'], {}).get(bid)
                    if not h or not h.get('body') or not h.get('ring'): continue
                    vals.append(inter(shifted(h['body']['v'], k), h['ring']['v']))
                if vals: curve[k] = (sum(vals) / len(vals), max(vals))
            if not curve: continue
            bk = min(curve, key=lambda k: curve[k][0])
            fx[bid] = dict(k0=round(curve[0][0], 4), best=round(curve[bk][0], 4), atk=round(bk / 32.0, 4),
                           gain=round(curve[0][0] - curve[bk][0], 4),
                           worst0=round(curve[0][1], 4), worstBest=round(curve[bk][1], 4),
                           curve={str(round(k / 32.0, 3)): round(v[0], 4) for k, v in sorted(curve.items())})
            f = fx[bid]
            print(f'   {bid:9} {f["k0"]:7} {f["best"]:11} {f["atk"]:7} {f["gain"]:7} {f["worst0"]:15} {f["worstBest"]:16}')
        out['fixedGrade'] = fx

    # ------------------------------------ 6. IS THE FAILURE THE BODY OR THE SITE
    print('\n== 6. IS A FAILURE A PROPERTY OF THE BODY OR OF THE SITE')
    bysite = defaultdict(list)
    for b in recs: bysite[b['site']].append(b)
    pf = [s for s, g in bysite.items() if any(b['side'] == 'party' and b['edgeRGB'] < FAIL for b in g)]
    both = [s for s in pf if any(b['side'] == 'foe' and b['edgeRGB'] < FAIL for b in bysite[s])]
    print(f'   sites with at least one party body failing: {len(pf)}/{len(bysite)}   '
          f'of those, a foe fails too at {len(both)}')
    # variance decomposition on edgeRGB: between sites vs between bodies
    gm = sum(b['edgeRGB'] for b in recs) / len(recs)
    site_m = {s: sum(b['edgeRGB'] for b in g) / len(g) for s, g in bysite.items()}
    body_m = {i: (sum(b['edgeRGB'] for b in recs if b['id'] == i) /
                  len([b for b in recs if b['id'] == i])) for i in {b['id'] for b in recs}}
    ss_tot = sum((b['edgeRGB'] - gm) ** 2 for b in recs)
    ss_site = sum(len(g) * (site_m[s] - gm) ** 2 for s, g in bysite.items())
    ss_body = sum(len([b for b in recs if b['id'] == i]) * (body_m[i] - gm) ** 2 for i in body_m)
    print(f'   edgeRGB variance explained: BY SITE {100 * ss_site / ss_tot:.1f}%   '
          f'BY BODY IDENTITY {100 * ss_body / ss_tot:.1f}%')
    out['attribution'] = dict(sitesWithPartyFail=len(pf), ofThoseFoeAlsoFails=len(both),
                              varBySite=round(100 * ss_site / ss_tot, 1),
                              varByBody=round(100 * ss_body / ss_tot, 1),
                              failSites=sorted(pf))
    print('   party failures, worst first:')
    for b in sorted([b for b in party if b['edgeRGB'] < FAIL], key=lambda b: b['edgeRGB']):
        fo = [x for x in bysite[b['site']] if x['side'] == 'foe']
        print(f'     {b["site"]} {b["zone"]:8} {b["id"]:7} edgeRGB={b["edgeRGB"]:6}  ovlV={b["ovl"]["ringV"]:6} '
              f' dV50={b["dV50"]:+.4f}  hPct={b["hPct"]:5}  foes at this site: '
              + ', '.join(f'{x["id"]}={x["edgeRGB"]}' for x in fo))

    # ------------------------------------- 7. THE RULER'S OWN SHAPE TERM
    # edgeRGB is the magnitude of ONE signed difference of means over a whole
    # silhouette, so a body brighter than its surround at the top and darker at
    # the bottom cancels itself toward zero. The same contrast in six horizontal
    # bands cannot cancel vertically. If the cast's two sides differ on this
    # ratio, then "party bodies fail more" is partly a statement about the ruler.
    if any('rowsAbs' in b for b in recs):
        print('\n== 7. DOES THE RULER CANCEL ITSELF ON A TALL BODY')
        print(f'   {"side":7} {"n":>4} {"edgeRGB p50":>12} {"6-band mean|.| p50":>19} {"ratio p50":>10} '
              f'{"sign flips":>11}')
        can = {}
        for s in ('party', 'foe'):
            g = [b for b in recs if b['side'] == s and b.get('rowsAbs') is not None]
            can[s] = dict(n=len(g), edge=pct([b['edgeRGB'] for b in g], .5),
                          rowsAbs=pct([b['rowsAbs'] for b in g], .5),
                          ratio=pct([b['cancel'] for b in g if b.get('cancel')], .5),
                          flip=sum(1 for b in g if b.get('rowSignFlip')))
            v = can[s]
            print(f'   {s:7} {v["n"]:4} {v["edge"]:12} {v["rowsAbs"]:19} {v["ratio"]:10} '
                  f'{str(v["flip"]) + "/" + str(v["n"]):>11}')
        f = [b for b in party if b['edgeRGB'] < FAIL and b.get('rowsAbs') is not None]
        if f:
            print(f'   of the {len(f)} party bodies the ruler calls FAILING, '
                  f'{sum(1 for b in f if (b.get("cancel") or 0) > 2)} have a 6-band contrast more than 2x their '
                  f'own edgeRGB, and {sum(1 for b in f if b.get("rowSignFlip"))} contain bands of OPPOSITE sign.')
            print(f'   their 6-band mean|.| p50 is {pct([b["rowsAbs"] for b in f], .5)} against an edgeRGB p50 of '
                  f'{pct([b["edgeRGB"] for b in f], .5)}.')
            can['partyFailing'] = dict(n=len(f), ratioGt2=sum(1 for b in f if (b.get('cancel') or 0) > 2),
                                       flips=sum(1 for b in f if b.get('rowSignFlip')),
                                       rowsAbs=pct([b['rowsAbs'] for b in f], .5),
                                       edge=pct([b['edgeRGB'] for b in f], .5))
        # and the same fail-rate under a ruler that cannot cancel
        thr = pct([b['rowsAbs'] for b in recs if b.get('rowsAbs') is not None], .0846)  # same census-wide rate
        for s in ('party', 'foe'):
            g = [b for b in recs if b['side'] == s and b.get('rowsAbs') is not None]
            can[s]['failsRows'] = sum(1 for b in g if b['rowsAbs'] < thr)
        can['rowsThreshold'] = thr
        print(f'   RE-COUNTED WITH THE NON-CANCELLING RULER at the same census-wide failure rate '
              f'(6-band mean < {thr}): party {can["party"]["failsRows"]}/{can["party"]["n"]}, '
              f'foe {can["foe"]["failsRows"]}/{can["foe"]["n"]} '
              f'(edgeRGB said {can["party"]["n"] and len([b for b in party if b["edgeRGB"] < FAIL])}'
              f'/{can["party"]["n"]} and {len([b for b in foes if b["edgeRGB"] < FAIL])}/{can["foe"]["n"]}).')
        out['cancel'] = can

    if a.json:
        p = os.path.join(ROOT, a.json)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(out, open(p, 'w'), indent=1)
        print('\nWROTE ' + a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
