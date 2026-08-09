#!/usr/bin/env python3
"""battle_place_stats.py — WHICH AXIS SEPARATES THE PILES.

Reads the hand-written sort (docs/qa/battle-placement/sort.json: id -> good |
acceptable | bad, plus a one-line reason) and the measured bundle
(sites*.json), and asks of EVERY recorded axis the same two questions:

  * how far apart are the good and bad piles on it (AUC of the good-vs-bad
    ranking — 0.5 is chance, 1.0 is a perfect separator, and BELOW 0.5 means the
    axis runs the other way, which is a result and not an error);
  * what does the best single threshold on it buy (balanced accuracy).

NEGATIVE RESULTS ARE PRINTED WITH THE POSITIVE ONES, in the same table, ranked.
An axis that does not separate is the more expensive thing to learn and the
cheapest thing to forget.

  python3 tools/battle_place_stats.py
  python3 tools/battle_place_stats.py --json docs/qa/battle-placement/axes.json
"""
import argparse, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('--sites', nargs='*', default=['docs/qa/battle-placement/sites.json',
                                               'docs/qa/battle-placement/sites-b.json'])
ap.add_argument('--sort', default='docs/qa/battle-placement/sort.json')
ap.add_argument('--json', default='docs/qa/battle-placement/axes.json')
a = ap.parse_args()

rows = []
for f in a.sites:
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        rows += json.load(open(p))['rows']
sort = json.load(open(os.path.join(ROOT, a.sort)))
verdict = sort['verdict'] if 'verdict' in sort else sort


def flat(r, prefix=''):
    """every numeric leaf of a site record, named by its path"""
    out = {}
    for k, v in r.items():
        if k in ('id', 'from', 'anchors', 'tiers', 'bands'):
            continue
        n = prefix + k
        if isinstance(v, dict):
            out.update(flat(v, n + '.'))
        elif isinstance(v, bool):
            out[n] = 1.0 if v else 0.0
        elif isinstance(v, (int, float)):
            out[n] = float(v)
    return out


feat = {}
for r in rows:
    if r['id'] not in verdict:
        continue
    f = flat(r)
    # DERIVED AXES, each named in the brief as a candidate and each built from
    # numbers already recorded — never a new measurement smuggled in after the sort.
    s, sr, g, ry = r.get('sil', {}), r.get('surf', {}), r.get('ground', {}), r.get('rays', {})
    fl = r.get('frameL', {})
    if s.get('ok'):
        if fl.get('L50'):
            f['d.castVsFrameL'] = (s.get('castL') or 0) - fl['L50']
        if s.get('ringL') is not None and fl.get('L50'):
            f['d.ringVsFrameL'] = s['ringL'] - fl['L50']
        if s.get('bands'):
            f['d.bandSpread'] = max(s['bands']) - min(s['bands'])
    if ry.get('dNear') and ry.get('dMed'):
        f['d.nearBandFrac'] = ry['dNear'] / max(0.01, ry['dMed'])
    feat[r['id']] = f

good = [i for i, v in verdict.items() if v.startswith('good') and i in feat]
acc = [i for i, v in verdict.items() if v.startswith('acc') and i in feat]
bad = [i for i, v in verdict.items() if v.startswith('bad') and i in feat]
print('sorted piles: good %d  acceptable %d  bad %d  (measured %d of %d)'
      % (len(good), len(acc), len(bad), len(feat), len(rows)))

keys = sorted(set().union(*[set(f) for f in feat.values()])) if feat else []


def auc(pos, neg):
    """P(a random pos ranks above a random neg); ties count a half"""
    n = 0.0
    t = 0
    for p in pos:
        for q in neg:
            t += 1
            n += 1.0 if p > q else (0.5 if p == q else 0.0)
    return n / t if t else None


def best_thresh(pos, neg):
    vals = sorted(set(pos + neg))
    best = (0.0, None, None)
    for i in range(len(vals)):
        for direction in (1, -1):
            th = vals[i]
            tp = sum(1 for v in pos if v * direction >= th * direction)
            tn = sum(1 for v in neg if v * direction < th * direction)
            ba = 0.5 * (tp / len(pos) + tn / len(neg))
            if ba > best[0]:
                best = (ba, th, direction)
    return best


out = []
for k in keys:
    gv = [feat[i][k] for i in good if k in feat[i]]
    bv = [feat[i][k] for i in bad if k in feat[i]]
    av = [feat[i][k] for i in acc if k in feat[i]]
    if len(gv) < 3 or len(bv) < 3:
        continue
    A = auc(gv, bv)
    ba, th, d = best_thresh(gv, bv)
    mean = lambda x: sum(x) / len(x)
    out.append({'axis': k, 'auc': round(A, 3), 'sep': round(abs(A - 0.5) * 2, 3),
                'balAcc': round(ba, 3), 'thresh': round(th, 4) if th is not None else None,
                'dir': ('good is HIGHER' if d > 0 else 'good is LOWER'),
                'goodMean': round(mean(gv), 3), 'accMean': round(mean(av), 3) if av else None,
                'badMean': round(mean(bv), 3), 'n': [len(gv), len(av), len(bv)]})

out.sort(key=lambda r: -r['sep'])
w = max(len(r['axis']) for r in out) if out else 10
print('\n%-*s  %6s %6s %6s   %10s %10s %10s  %s' % (w, 'axis', 'AUC', 'sep', 'balAcc', 'good', 'accept', 'bad', 'direction'))
for r in out:
    print('%-*s  %6.3f %6.3f %6.3f   %10.3f %10s %10.3f  %s'
          % (w, r['axis'], r['auc'], r['sep'], r['balAcc'], r['goodMean'],
             ('%10.3f' % r['accMean']) if r['accMean'] is not None else '        --',
             r['badMean'], r['dir']))

json.dump({'piles': {'good': good, 'acceptable': acc, 'bad': bad}, 'axes': out},
          open(os.path.join(ROOT, a.json), 'w'), indent=2)
print('\nwrote ' + a.json)
