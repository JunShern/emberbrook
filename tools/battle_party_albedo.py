#!/usr/bin/env python3
"""battle_party_albedo.py — WHAT COLOUR IS THE PARTY, MEASURED THE SAME WAY THE
MONSTERS WERE.

    python3 tools/battle_party_albedo.py                       # the table
    python3 tools/battle_party_albedo.py --json docs/qa/battle-party/albedo.json

WHY THIS EXISTS. `tools/monster_regrade.py` regraded the six creatures INTO the
party's own value/saturation band, taking the band as given:

    S50 0.333-0.452   V05 0.192-0.216   V50 0.306-0.443   V95 0.718-0.784

That was the right gate for CAST COHERENCE. It says nothing at all about whether
the party's own range is wide enough to sit against ow-valley, because the valley
was never in the comparison. This file is the first half of asking that: it
re-measures the party rigs, and it re-measures them WITH monster_regrade's OWN
sampler — imported, never copied. Two rulers is not a comparison, and this repo
has paid for that shape (walk_bodygate reading the file while the engine read
something else).

WHAT IT ADDS over the four numbers above, all of which it also reprints:
  * the FULL area-weighted V and S distributions (deciles + a 32-bin histogram),
    because "is the range wide enough" is a question about a distribution and
    cannot be answered from three quantiles;
  * a PER-MATERIAL breakdown, because a proposal to regrade a ratified character
    has to be able to say which part of her moves;
  * the same numbers for the four graded monsters, so the party band and the band
    the monsters were pulled into are on one sheet.

ALBEDO IS NOT SCREEN COLOUR. Nothing here is a claim about what the player sees:
the rig is lit, tone-mapped and graded before it reaches a pixel. The screen-side
half is tools/battle_party.mjs, which measures the SAME bodies in the frame and
against the terrain ring immediately around them. Read the two together or not at
all.
"""
import argparse, importlib.util, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ONE RULER. sample_albedo/stats come out of the tool that set the band; if that
# tool's sampler changes, this file changes with it and the comparison stays
# honest by construction.
_spec = importlib.util.spec_from_file_location('monster_regrade', os.path.join(ROOT, 'tools', 'monster_regrade.py'))
MR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MR)

PARTY = {
    'vesper': 'public/assets/characters/vesper/vesper-v2.glb',
    'maren':  'public/assets/characters/maren/maren-v1.glb',
    'lake':   'public/assets/characters/lake/lake-v1.glb',
}
MONSTERS = 'public/assets/monsters/3d'

# The band monster_regrade.py states in its header, quoted so a drift between it
# and a fresh measurement is VISIBLE rather than silently absorbed.
STATED = dict(S50=(0.333, 0.452), V05=(0.192, 0.216), V50=(0.306, 0.443), V95=(0.718, 0.784))

NB = 32


def dist(pairs):
    """Area-weighted quantiles and a 32-bin histogram of V and of S. Weighted by
    triangle AREA for the same reason monster_regrade is: a 4-pixel eye is not
    half a character."""
    import colorsys
    tot = sum(w for w, _ in pairs) or 1.0
    vs, ss = [], []
    hv = [0.0] * NB
    hs = [0.0] * NB
    for w, c in pairs:
        h, s, v = colorsys.rgb_to_hsv(*c)
        vs.append((v, w)); ss.append((s, w))
        hv[min(NB - 1, int(v * NB))] += w
        hs[min(NB - 1, int(s * NB))] += w
    def q(arr, p):
        arr = sorted(arr)
        acc = 0.0
        for x, w in arr:
            acc += w
            if acc >= p * tot: return round(x, 4)
        return round(arr[-1][0], 4)
    return dict(
        Vq={('p%02d' % int(p * 100)): q(vs, p) for p in (.05, .1, .25, .5, .75, .9, .95)},
        Sq={('p%02d' % int(p * 100)): q(ss, p) for p in (.05, .1, .25, .5, .75, .9, .95)},
        histV=[round(x / tot, 5) for x in hv], histS=[round(x / tot, 5) for x in hs], nbins=NB)


def by_material(js, bin_):
    """Same sampler, one primitive at a time, keyed by the material's own name."""
    out = {}
    meshes = js.get('meshes', [])
    for mi, mesh in enumerate(meshes):
        for pi, p in enumerate(mesh.get('primitives', [])):
            sub = dict(js)
            sub = json.loads(json.dumps(js))          # a private copy; we prune meshes
            sub['meshes'] = [{'primitives': [json.loads(json.dumps(p))]}]
            pairs = MR.sample_albedo(sub, bin_)
            mat = js['materials'][p['material']] if p.get('material') is not None else {}
            name = mat.get('name') or ('mat%d' % (p.get('material') if p.get('material') is not None else -1))
            key = '%s/%s' % (mesh.get('name', 'mesh%d' % mi), name)
            st = MR.stats(pairs)
            st['areaFrac'] = sum(w for w, _ in pairs)
            out[key] = st
    tot = sum(v['areaFrac'] for v in out.values()) or 1.0
    for v in out.values(): v['areaFrac'] = round(v['areaFrac'] / tot, 4)
    return out


def measure(path):
    js, bin_ = MR.read_glb(open(os.path.join(ROOT, path), 'rb').read())
    pairs = MR.sample_albedo(js, bin_)
    st = MR.stats(pairs)
    st.update(dist(pairs))
    st['band'] = MR.in_band(st)
    st['mats'] = by_material(js, bin_)
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', default=None)
    ap.add_argument('--monsters', action='store_true', default=True)
    a = ap.parse_args()

    out = {'stated': STATED, 'party': {}, 'monsters': {}}
    print(f'{"rig":16} {"H":>6} {"S":>6} {"V05":>6} {"V50":>6} {"V95":>6} '
          f'{"V25":>6} {"V75":>6} {"S25":>6} {"S75":>6}   band')
    for n, p in PARTY.items():
        st = measure(p)
        out['party'][n] = st
        print(f'{n:16} {st["H"]:6} {st["S"]:6} {st["V05"]:6} {st["V50"]:6} {st["V95"]:6} '
              f'{st["Vq"]["p25"]:6} {st["Vq"]["p75"]:6} {st["Sq"]["p25"]:6} {st["Sq"]["p75"]:6}   {st["band"]}')
    if a.monsters:
        print()
        for f in sorted(os.listdir(os.path.join(ROOT, MONSTERS))):
            if not f.endswith('.glb'): continue
            n = f[:-4]
            st = measure(f'{MONSTERS}/{f}')
            out['monsters'][n] = st
            print(f'{n:16} {st["H"]:6} {st["S"]:6} {st["V05"]:6} {st["V50"]:6} {st["V95"]:6} '
                  f'{st["Vq"]["p25"]:6} {st["Vq"]["p75"]:6} {st["Sq"]["p25"]:6} {st["Sq"]["p75"]:6}   {st["band"]}')

    # THE DRIFT CHECK, PRINTED NOT SWALLOWED. The band in monster_regrade's header
    # is a quoted measurement; if a fresh run of the same sampler disagrees, the
    # disagreement is data about the assets, not a rounding detail to absorb.
    p = out['party']
    fresh = dict(S50=(min(v['S'] for v in p.values()), max(v['S'] for v in p.values())),
                 V05=(min(v['V05'] for v in p.values()), max(v['V05'] for v in p.values())),
                 V50=(min(v['V50'] for v in p.values()), max(v['V50'] for v in p.values())),
                 V95=(min(v['V95'] for v in p.values()), max(v['V95'] for v in p.values())))
    out['fresh'] = {k: [round(x, 4) for x in v] for k, v in fresh.items()}
    print('\nband as stated by monster_regrade.py :', STATED)
    print('band re-measured now                 :', out['fresh'])
    for k in STATED:
        d = max(abs(fresh[k][0] - STATED[k][0]), abs(fresh[k][1] - STATED[k][1]))
        print(f'   {k:4} max drift {d:+.4f}' + ('   <- MOVED' if d > 0.01 else ''))

    if a.json:
        os.makedirs(os.path.dirname(os.path.join(ROOT, a.json)), exist_ok=True)
        with open(os.path.join(ROOT, a.json), 'w') as fh: json.dump(out, fh, indent=1)
        print('WROTE ' + a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
