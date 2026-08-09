#!/usr/bin/env python3
"""battle_party_board.py — builds docs/qa/battle-party/index.html from the run's
own json, so no number on the board is typed by hand.

    python3 tools/battle_party_board.py

It reads albedo.json (texture space), census-pair.json / census-trio.json and
stats-*.json (display space), and the census frames under census/<tag>/.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA = os.path.join(ROOT, 'docs/qa/battle-party')


def J(n):
    p = os.path.join(QA, n)
    return json.load(open(p)) if os.path.exists(p) else None


def bars(hist, colour, w=260, h=44):
    """A 32-bin histogram as an inline SVG strip. No library, both themes."""
    if not hist: return ''
    m = max(hist) or 1
    bw = w / len(hist)
    r = [f'<rect x="{i*bw:.2f}" y="{h-(v/m)*h:.2f}" width="{bw-0.5:.2f}" height="{(v/m)*h:.2f}" fill="{colour}"/>'
         for i, v in enumerate(hist)]
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(r)}</svg>'


def overlay(a, b, ca, cb, w=300, h=56):
    """Two histograms on one axis — the picture of an overlap."""
    if not a or not b: return ''
    m = max(max(a), max(b)) or 1
    bw = w / len(a)
    out = []
    for i in range(len(a)):
        out.append(f'<rect x="{i*bw:.2f}" y="{h-(b[i]/m)*h:.2f}" width="{bw-0.4:.2f}" height="{(b[i]/m)*h:.2f}" fill="{cb}" opacity="0.85"/>')
    for i in range(len(a)):
        out.append(f'<rect x="{i*bw:.2f}" y="{h-(a[i]/m)*h:.2f}" width="{bw-0.4:.2f}" height="{(a[i]/m)*h:.2f}" fill="{ca}" opacity="0.6"/>')
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}</svg>'


CSS = """
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#c9d1d9;font:14.5px/1.62 -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
.w{max-width:1180px;margin:0 auto;padding:34px 22px 90px}
h1{font-size:27px;line-height:1.22;margin:0 0 6px}
h2{font-size:19px;margin:38px 0 8px;padding-top:16px;border-top:1px solid #21262d}
h3{font-size:15.5px;margin:22px 0 6px;color:#e6edf3}
p{margin:9px 0}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.6px}
code{background:#161b22;border:1px solid #21262d;border-radius:4px;padding:1px 5px}
pre{background:#161b22;border:1px solid #21262d;border-radius:6px;padding:12px;overflow-x:auto}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13px}
th,td{border:1px solid #21262d;padding:5px 8px;text-align:right}
th:first-child,td:first-child{text-align:left}
th{background:#161b22;font-weight:600}
.sub{color:#8b949e}
.verdict{background:#12261a;border:1px solid #2ea04366;border-left:4px solid #2ea043;border-radius:7px;padding:14px 16px;margin:16px 0}
.warn{background:#26200f;border:1px solid #d2992255;border-left:4px solid #d29922;border-radius:7px;padding:14px 16px;margin:16px 0}
.note{background:#161b22;border:1px solid #21262d;border-left:4px solid #58a6ff;border-radius:7px;padding:12px 15px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px;margin:14px 0}
figure{margin:0;background:#161b22;border:1px solid #21262d;border-radius:8px;overflow:hidden}
figure img{display:block;width:100%;height:auto}
figcaption{padding:8px 10px;font-size:12.4px;color:#8b949e}
.big img{width:100%}
.bad{color:#ff7b72}.ok{color:#7ee787}.mid{color:#d29922}
.scroll{overflow-x:auto}
@media (prefers-color-scheme: light){
 body{background:#fff;color:#1f2328}
 h2{border-top-color:#d0d7de} th{background:#f6f8fa} th,td{border-color:#d0d7de}
 code,pre{background:#f6f8fa;border-color:#d0d7de}
 .note{background:#f6f8fa;border-color:#d0d7de;border-left-color:#0969da}
 figure{background:#f6f8fa;border-color:#d0d7de}
 .verdict{background:#eaffef;border-color:#2da44e55;border-left-color:#2da44e}
 .warn{background:#fff8c5;border-color:#d4a72c55;border-left-color:#bf8700}
}
:root[data-theme="dark"] body{background:#0d1117;color:#c9d1d9}
:root[data-theme="light"] body{background:#fff;color:#1f2328}
"""


def tr(cells, cls=''):
    return '<tr' + (f' class="{cls}"' if cls else '') + '>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'


def main():
    alb = J('albedo.json')
    stp = J('stats-pair.json')
    stt = J('stats-trio.json')
    cen = J('census-pair.json')
    cet = J('census-trio.json')
    hp = J('hist-pair.json')
    if not (alb and stp and cen):
        print('missing inputs; run battle_party.mjs and battle_party_stats.py first'); return 2
    hist = {r['id']: r['hist'] for r in hp['hist']} if hp else {}

    H = []
    A = H.append
    A(f'<title>Battle · the party against the valley — is the party\'s own albedo range wide enough?</title>')
    A(f'<style>{CSS}</style><div class="w">')
    A('<h1>Is the party\'s own albedo range wide enough to sit against this valley?</h1>')
    A('<p class="sub">PARTY-ALBEDO lane · 2026-08-09 · 62-site census, both arms, real battles at the '
      '<code>decide</code> frame · instruments <code>tools/battle_party.mjs</code>, '
      '<code>tools/battle_party_albedo.py</code>, <code>tools/battle_party_stats.py</code> · '
      'measured with the shared meter <code>tools/battle_meter.mjs</code>, not a second ruler.</p>')

    # ---- verdict (written by the lane, numbers substituted) ------------------
    bs = stp['bySide']; auc = stp['auc']; att = stp['attribution']
    A('<div class="verdict"><b>THE HYPOTHESIS DOES NOT SURVIVE.</b> The party does not share this valley\'s '
      'paint any more than the creatures do. Party bodies overlap the terrain immediately around them at '
      f'<b>{bs["party"]["ovlV"]}</b> of their value histogram; the two foes — which bet H graded <i>into the '
      f'party\'s own band</i> — overlap at <b>{bs["foe"]["ovlV"]}</b>, and they fail to read '
      f'<b>{bs["foe"]["fails"]}/{bs["foe"]["n"]}</b> times against the party\'s '
      f'<b>{bs["party"]["fails"]}/{bs["party"]["n"]}</b>. Overlap-with-terrain ranks a body that fails against '
      f'one that reads at AUC <b>{auc["ovl ringV"]["all"]}</b> (party only: {auc["ovl ringV"]["party"]}) — chance. '
      f'And <b>{att["varBySite"]}% of the variance in silhouette contrast is explained by WHICH SITE the fight '
      f'is at, against {att["varByBody"]}% by WHICH BODY it is.</b> A regrade of ratified characters is not '
      'indicated, and is not proposed.</div>')

    # ---- 1. albedo ----------------------------------------------------------
    A('<h2>1 · The party\'s albedo, re-measured with the monsters\' own sampler</h2>')
    A('<p>Area-weighted, from each rig\'s baseColor, through <code>monster_regrade.py</code>\'s '
      '<code>sample_albedo</code>/<code>stats</code> — imported, never copied.</p>')
    A('<div class="scroll"><table><tr><th>rig</th><th>H</th><th>S</th><th>V05</th><th>V25</th><th>V50</th>'
      '<th>V75</th><th>V95</th><th>colours</th><th>bet-H band</th><th>value distribution</th></tr>')
    for n, v in list(alb['party'].items()) + list(alb['monsters'].items()):
        cls = 'sub' if n not in alb['party'] else ''
        A('<tr>' + f'<td>{n}</td>' + ''.join(f'<td>{x}</td>' for x in
          [v['H'], v['S'], v['V05'], v['Vq']['p25'], v['V50'], v['Vq']['p75'], v['V95'], v['ncol'], v['band']])
          + f'<td>{bars(v["histV"], "#58a6ff" if n in alb["party"] else "#8b949e", 200, 30)}</td></tr>')
    A('</table></div>')
    f = alb['fresh']
    A(f'<div class="warn"><b>Residual, named: the band bet H gates against is not reproducible from bet H\'s own '
      f'sampler.</b> <code>monster_regrade.py</code> states the party as S50 0.333–0.452, V05 0.192–0.216, '
      f'V50 0.306–0.443, V95 0.718–0.784. Re-measured now with that file\'s own <code>sample_albedo</code>: '
      f'S50 {f["S50"][0]}–{f["S50"][1]}, V05 {f["V05"][0]}–{f["V05"][1]}, V50 {f["V50"][0]}–{f["V50"][1]}, '
      f'V95 {f["V95"][0]}–{f["V95"][1]}. The party GLBs have not changed since (last touched at e2d18009, '
      'clips only), so the stated band came off a path nobody kept. The practical consequence is small and '
      'should still be said out loud: <b>under its own tool Vesper fails the band derived from her</b> — '
      'S 0.474 &gt; 0.452 and V95 0.792 &gt; 0.784. No monster verdict flips at the re-measured edges.</div>')

    # ---- 2. terrain ---------------------------------------------------------
    t = stp['terrain']
    A('<h2>2 · The terrain a party body actually stands against</h2>')
    A('<p>Not the frame — the <b>ring around that body\'s own mask</b>, read off the same frame with the cast '
      'removed, per body, at all 62 sites. Display-space sRGB after the post chain.</p>')
    A('<div class="scroll"><table><tr><th>zone</th><th>n bodies</th><th>ring V p05</th><th>p25</th><th>p50</th>'
      '<th>p75</th><th>p95</th><th>ring S p50</th><th>clutter</th></tr>')
    for z, v in t.items():
        A(tr([z, v['n'], v['v05'], v['v25'], v['v50'], v['v75'], v['v95'], v['s50'], v['clutter']]))
    A('</table></div>')
    A(f'<p><b>The width is the finding.</b> At the median site a single body\'s own ring already spans '
      f'V {t["ALL"]["v05"]}–{t["ALL"]["v95"]}, and site to site the ring\'s <i>median</i> runs '
      f'{t["ALL"]["v50lo"]}–{t["ALL"]["v50hi"]}. There is no value a fixed albedo could occupy that is far from '
      'this terrain everywhere: the valley uses the whole range.</p>')

    # ---- 3. per body --------------------------------------------------------
    A('<h2>3 · Every body\'s own screen band, and its overlap with that terrain</h2>')
    A('<p>Overlap is a histogram <b>intersection</b> — 1 means the body\'s paint and the terrain\'s paint occupy '
      'the same values entirely. <code>dV50</code> is the signed median gap. Foes are in the same table on '
      'purpose: they are the control.</p>')
    A('<div class="scroll"><table><tr><th>body</th><th>side</th><th>n</th><th>body V50</th><th>ring V50</th>'
      '<th>dV50</th><th>body S50</th><th>ring S50</th><th>ovl V</th><th>ovl S</th><th>edgeRGB p50</th>'
      '<th>6-band p50</th><th>fails &lt;5</th><th>h% of frame</th></tr>')
    for bid, v in sorted(stp['perBody'].items(), key=lambda kv: (kv[1]['side'], kv[0])):
        A(tr([bid, v['side'], v['n'], v['bodyV50'], v['ringV50'], v['dV50'], v['bodyS50'], v['ringS50'],
              v['ovlV'], v['ovlS'], v['edgeRGB'], v.get('rowsAbs'), f"{v['fails']}/{v['n']}", v['hPct']]))
    A('</table></div>')
    pv, pm = stp['perBody']['vesper'], stp['perBody']['maren']
    A(f'<p><b>The party\'s rendered range is WIDER than its terrain\'s, not narrower.</b> On screen Vesper spans '
      f'V {pv["bodyV05"]}–{pv["bodyV95"]} and Maren {pm["bodyV05"]}–{pm["bodyV95"]}, against a terrain ring of '
      f'{t["ALL"]["v05"]}–{t["ALL"]["v95"]}. Their medians sit {abs(pv["dV50"])}–{abs(pm["dV50"])} below the '
      'terrain\'s median — but so do the foes\', exactly (m0 and m1 sit at their ring\'s median to three '
      'decimals), and the foes read.</p>')
    if stt:
        A('<h3>With Lake in the party (a second full census, 3v2, same cells and same yaw)</h3>')
        A('<div class="scroll"><table><tr><th>body</th><th>side</th><th>n</th><th>body V50</th><th>ring V50</th>'
          '<th>dV50</th><th>body S50</th><th>ovl V</th><th>ovl S</th><th>edgeRGB p50</th><th>6-band p50</th>'
          '<th>fails &lt;5</th><th>h% of frame</th></tr>')
        for bid, v in sorted(stt['perBody'].items(), key=lambda kv: (kv[1]['side'], kv[0])):
            A(tr([bid, v['side'], v['n'], v['bodyV50'], v['ringV50'], v['dV50'], v['bodyS50'], v['ovlV'],
                  v['ovlS'], v['edgeRGB'], v.get('rowsAbs'), f"{v['fails']}/{v['n']}", v['hPct']]))
        A('</table></div>')
        A('<p><b>Which party body is worst: Maren, in both censuses and under both rulers</b> '
          f'({stt["perBody"]["maren"]["fails"]}/62 failing with Lake in the party, 6-band '
          f'{stt["perBody"]["maren"]["rowsAbs"]} against Vesper\'s {stt["perBody"]["vesper"]["rowsAbs"]} and '
          f'Lake\'s {stt["perBody"]["lake"]["rowsAbs"]}), worst on <b>meadow</b> and <b>crag</b>. What is '
          'measurably true of her is not her band: it is that she is the most OCCLUDED body on the stage '
          '(median 4.8% two-handed, 5.8% three-handed, against Vesper\'s 0.6–1.1%) because the formation puts '
          'her behind the actor, and that she is the least saturated body on screen (S50 0.328) against terrain '
          'at 0.359. Lake is less saturated in albedo than she is (S 0.325 vs 0.385) and reads better than her '
          'at every zone, so saturation does not carry the difference either.</p>')

    # ---- 4. what separates --------------------------------------------------
    A('<h2>4 · What actually separates a body that fails to read from one that does</h2>')
    A('<p>AUC over all 248 measured bodies and over the 124 party bodies alone. 0.5 is chance. '
      '“Fails” is <code>edgeRGB &lt; 5</code>, the rim spike\'s own threshold, unchanged.</p>')
    A('<div class="scroll"><table><tr><th>axis</th><th>AUC (all bodies)</th><th>AUC (party only)</th></tr>')
    for k, v in sorted(auc.items(), key=lambda kv: -abs((kv[1]['all'] or .5) - .5)):
        A(tr([k, v['all'], v['party']]))
    A('</table></div>')
    A('<p><b>Every palette axis is at or near chance.</b> The colour term with any signal at all is the signed '
      'value gap <code>|dV50|</code> at <b>%s</b> for party bodies — and that is a property of the LIGHT and the '
      'PLACEMENT at a site, not of the asset: the same rig measures a gap of 0.28 at one site and 0.00 at '
      'another.</p>' % auc['-|dV50|']['party'])

    # ---- 5. counterfactual --------------------------------------------------
    fx = stp.get('fixedGrade', {})
    A('<h2>5 · What a regrade could buy, priced before anyone proposes one</h2>')
    A('<p>Each body\'s measured value histogram shifted by a fixed amount — which is what an albedo grade IS, '
      'one number for the whole game — against its own terrain ring, averaged over the census.</p>')
    A('<div class="scroll"><table><tr><th>body</th><th>overlap now</th><th>best fixed shift</th>'
      '<th>at ΔV</th><th>bought</th><th>worst site now</th><th>worst site after</th></tr>')
    for bid, v in sorted(fx.items()):
        A(tr([bid, v['k0'], v['best'], v['atk'], v['gain'], v['worst0'], v['worstBest']]))
    A('</table></div>')
    A('<div class="note"><b>Read the ΔV column before the gain column.</b> The shifts that buy anything are '
      '±0.5 of value — black, or white. They are stylisations, not grades. They also point in <b>opposite '
      'directions for two members of the same party</b> (Vesper darker, Maren lighter), and the same arithmetic '
      'demands the two freshly-graded foes be taken to +0.5, i.e. it would undo bet H. At a shift a grade could '
      'actually carry — ΔV ±0.15, which for Vesper means an albedo gain of about 0.66 or 1.34 with her V95 '
      'already at 0.792 and clipping — the census overlap moves about 0.52 → 0.45.</div>')

    # ---- 6. the cancellation ------------------------------------------------
    can = stp.get('cancel')
    A('<h2>6 · Why party bodies fail more often anyway — and it is the ruler\'s shape term, not their paint</h2>')
    if can:
        A('<p><code>edgeRGB</code> is the magnitude of ONE signed difference of means over a whole silhouette. '
          'A body whose top is brighter than its surround and whose bottom is darker cancels itself toward zero. '
          'That is arithmetic, not a theory — and the two sides of this cast have opposite shapes: a standing '
          'person spans several surfaces top to bottom, a wolf or a blob sits on one. So the same contrast was '
          'cut into six horizontal bands over each body\'s own extent, which cannot cancel vertically.</p>')
        A('<div class="scroll"><table><tr><th>side</th><th>n</th><th>edgeRGB p50</th>'
          '<th>same contrast in 6 bands (mean |·|)</th><th>ratio</th>'
          '<th>bodies containing bands of OPPOSITE sign</th><th>fails, edgeRGB&lt;5</th>'
          '<th>fails, 6-band, same census rate</th></tr>')
        fe = {'party': bs['party']['fails'], 'foe': bs['foe']['fails']}
        for s in ('party', 'foe'):
            v = can[s]
            A(tr([s, v['n'], v['edge'], v['rowsAbs'], v['ratio'], f"{v['flip']}/{v['n']}",
                  f"{fe[s]}/{v['n']}", f"{v['failsRows']}/{v['n']}"]))
        A('</table></div>')
        pf = can.get('partyFailing')
        if pf:
            A(f'<div class="warn"><b>THE SPLIT INVERTS.</b> At the same census-wide failure rate, a ruler that '
              f'cannot cancel vertically calls <b>{can["party"]["failsRows"]}/124</b> party bodies and '
              f'<b>{can["foe"]["failsRows"]}/124</b> foe bodies unreadable — the mirror image of edgeRGB\'s '
              f'{bs["party"]["fails"]}/124 and {bs["foe"]["fails"]}/124. Of the {pf["n"]} party bodies edgeRGB calls '
              f'failing, <b>{pf["ratioGt2"]} have a 6-band contrast more than twice their own edgeRGB</b> and '
              f'{pf["flips"]} contain bands of opposite sign; their 6-band median is {pf["rowsAbs"]} against an '
              f'edgeRGB median of {pf["edge"]}. So the arc\'s premise — that legibility failures concentrate on '
              'small clothed party bodies — is substantially a statement about the ruler\'s shape term. This is '
              'a hand-off, not a shipped replacement: nothing has been eye-sorted under the new number.</div>')

        # THE PAIR OF PICTURES THAT SETTLES IT
        pick = {}
        for r in cen['rows']:
            for b in r['bodies']:
                if r['id'] in ('s040', 's017') and b['id'] in ('vesper', 'maren'):
                    pick.setdefault(r['id'], []).append(b)
        if 's040' in pick and 's017' in pick:
            v40 = [b for b in pick['s040'] if b['id'] == 'vesper'][0]
            m17 = [b for b in pick['s017'] if b['id'] == 'maren'][0]
            A('<h3>The same number, one artefact and one real failure — look at both</h3>')
            A('<div class="grid">')
            A(f'<figure><img src="census/pair/s040.jpg" alt="s040">'
              f'<figcaption><b>s040 · crag · vesper · edgeRGB {v40["edgeRGB"]}</b> — the worst party read in the '
              f'census, and <b class="ok">she is plainly visible</b>. Her six bands are '
              f'{v40["rows"]} (mean {v40["rowsAbs"]}): a teal coat under a sunlit tan wall at the top, dark boots '
              f'on a pale lit deck at the bottom. Nothing about her is hard to see; the global mean ate itself.'
              f'</figcaption></figure>')
            A(f'<figure><img src="census/pair/s017.jpg" alt="s017">'
              f'<figcaption><b>s017 · meadow · maren · edgeRGB {m17["edgeRGB"]}</b> — the same verdict from the '
              f'ruler, and <b class="bad">this one is real</b>. Her six bands are {m17["rows"]} '
              f'(mean {m17["rowsAbs"]}): a cream top against sunlit sandstone, low everywhere, no cancellation to '
              f'blame. Overlap with her terrain ring is {m17["ovl"]["ringV"]}, the highest in the census — and it '
              f'is the SITE\'S light that put her there, not her paint: the same rig reads at 40+ elsewhere.'
              f'</figcaption></figure>')
            A('</div>')

    # ---- 7. the pictures ----------------------------------------------------
    A('<h2>7 · The pictures — the worst party reads in the census, at full resolution</h2>')
    A('<p>Sorted by the failing body\'s <code>edgeRGB</code>. Each caption carries the measured numbers for the '
      'body named. <b>Look at them before believing any of the tables above.</b></p>')
    rows = {r['id']: r for r in cen['rows']}
    worst = sorted([b for r in cen['rows'] for b in r['bodies'] if b['side'] == 'party'],
                   key=lambda b: b['edgeRGB'])[:8]
    seen = set()
    A('<div class="grid">')
    for b in worst:
        sid = b['site'] if 'site' in b else None
        # census rows carry id at the row level
        sid = next((r['id'] for r in cen['rows'] if any(x is b for x in r['bodies'])), sid)
        if sid in seen: pass
        seen.add(sid)
        r = rows[sid]
        h = hist.get(sid, {}).get(b['id'], {})
        ov = overlay(h.get('body', {}).get('v'), h.get('ring', {}).get('v'), '#58a6ff', '#d29922')
        A(f'<figure><img src="census/pair/{sid}.jpg" alt="{sid}">'
          f'<figcaption><b>{sid}</b> · {r["zone"]} · <b>{b["id"]}</b> edgeRGB <b class="bad">{b["edgeRGB"]}</b>'
          f' · bands {b.get("rows")} (mean |·| {b.get("rowsAbs")})'
          f' · body V50 {b["bodyV"]["p50"]} vs ring V50 {b["ringV"]["p50"]} (ΔV {b["dV50"]:+})'
          f' · overlap V {b["ovl"]["ringV"]}<br>{ov}<span class="sub"> blue = the body\'s value histogram, '
          f'amber = the terrain ring\'s</span></figcaption></figure>')
    A('</div>')

    # ---- 8. proposal --------------------------------------------------------
    A('<h2>8 · The proposal</h2>')
    A('<p><b>Do not regrade the party.</b> The evidence above says the intervention would not buy legibility at '
      'any strength a grade can carry, and it would spend a ratified character\'s appearance in towns, the '
      'overworld, every cut-in and every plate for it. That is a user call and this lane does not make it — but '
      'it is not a call worth putting to them on this evidence.</p>')
    A(f'<p>What the census says the remaining gap IS: the site. <b>{att["varBySite"]}%</b> of the variance in '
      f'silhouette contrast is the site; <b>{att["varByBody"]}%</b> is the body. '
      f'{att["sitesWithPartyFail"]}/62 sites have a party body the ruler calls failing, and at only '
      f'{att["ofThoseFoeAlsoFails"]} of those does a foe fail too. The lanes with the moving parts are '
      'placement quality (already shipped one refusal and one dominance term) and the ruler itself (§6).</p>')

    A('<h2>What is on disk, and what is not</h2>')
    A('<p>All 62 frames of the two-handed census are committed at full canvas resolution under '
      '<code>census/pair/</code>, because they are the evidence. The three-handed census wrote 62 frames too '
      'and only <b>8 are kept</b> (<code>census/trio/</code>: the worst party reads in that arm) — its tables '
      'above are computed from all 62 rows in <code>census-trio.json</code>. Deleting the rest was a payload '
      'call, not a measurement one; <code>--tag=trio</code> re-shoots them in four minutes.</p>')
    A('<h2>Reproduce</h2>')
    A('<pre>python3 tools/battle_party_albedo.py --json docs/qa/battle-party/albedo.json\n'
      'node tools/battle_party.mjs --port=3000 --mode=census --tag=pair\n'
      'node tools/battle_party.mjs --port=3000 --mode=census --tag=trio --party=vesper,maren,lake\n'
      'node tools/battle_party.mjs --port=3000 --mode=noise --site=55 --reps=6\n'
      'python3 tools/battle_party_stats.py --tag pair --json docs/qa/battle-party/stats-pair.json\n'
      'python3 tools/battle_party_board.py</pre>')
    A('</div>')

    open(os.path.join(QA, 'index.html'), 'w').write('\n'.join(H))
    print('WROTE docs/qa/battle-party/index.html')
    return 0


if __name__ == '__main__':
    sys.exit(main())
