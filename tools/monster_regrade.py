#!/usr/bin/env python3
"""monster_regrade.py — BRING THE MONSTERS' ALBEDO INTO THE PARTY'S BAND.

    python3 tools/monster_regrade.py --check      # measure only, write nothing
    python3 tools/monster_regrade.py --write      # regrade from the PRISTINE source rev

WHAT THIS IS FOR
----------------
`docs/plans/battle-presentation-inventory.md` §8 says the six creatures stand in
"at least four art directions". Measured (tools/monster_lineup.mjs + the census in
docs/qa/battle-monsters/index.html) that claim splits into five candidate axes, and
only two of them are actually about colour:

  * poly density        1000-1962 tris across all six          -> NOT the problem
  * albedo VALUE        area-weighted V50 spans 0.227 .. 0.820 -> 3.6x, 1.85 stops
  * albedo SATURATION   area-weighted S    spans 0.057 .. 0.533 -> 9.4x

THE TARGET IS NOT TASTE. It is the party's own albedo, measured off the shipping
rigs' baseColor textures (vesper-v2 / maren-v1 / lake-v1, the same files
play3d.html's MODELS registry hands the overworld):

    S50 0.333 - 0.452   V05 0.192 - 0.216   V50 0.306 - 0.443   V95 0.718 - 0.784

See BAND below for what those numbers are turned into and — more usefully — for the
version of the gate that was wrong first. A future asset can be judged against it
without asking anybody's opinion.

WHY A REGRADE AND NOT A RUNTIME TINT. `dye()` in battle_stage3d.js multiplies a
material's colour, which can only ever go DOWN and cannot touch a texture's
interior contrast at all — three of these models are one mesh with one 512^2
painted map, so a multiply is the wrong instrument. Grading the asset also keeps
the change out of a file two other lanes are editing tonight.

IDEMPOTENCY, WHICH A DESTRUCTIVE GRADE MUST HAVE. The tool never reads the file it
is about to write. It reads the PRISTINE bytes out of git (`git show <REV>:<path>`)
and writes the graded artifact over the working tree, so running it twice is the
same as running it once, and the recipe below stays the whole description of the
difference between the source rev and what ships. `--rev` overrides.

WHAT IS DELIBERATELY NOT TOUCHED
  * duskpad   -- S 0.057 V 0.475. It is already the one creature that stands
                 beside Vesper without arguing (docs/qa/battle-monsters/
                 lineup-with-party.png). Saturating a grey wolf to hit a median
                 computed over human skin and cloth would be a worse picture that
                 scores better, which is the failure mode this file exists inside.
  * brook-sprite -- also already in band (S 0.033, V50 0.494), and in any case
                 MON['brook-sprite'].build = 'wisp': the shipped body is CODE, in
                 the arena's own idiom. The GLB is only its documented fallback.
  * geometry, skins, animations, UVs -- bytes copied verbatim, accessor by
                 accessor. This tool cannot move a vertex.
"""
import argparse, io, json, math, os, struct, subprocess, sys, colorsys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MDIR = 'public/assets/monsters/3d'
# The commit that added the pristine CC0 downloads. Everything this tool writes is
# derived from THESE bytes, never from the working tree.
SOURCE_REV = '633b51fb'

# ---- THE PARTY BAND, measured off the shipping rigs' baseColor maps ----------
# Party albedo, per rig: S50 0.333-0.452, V05 0.192-0.216, V50 0.306-0.443,
# V95 0.718-0.784.
#
# THE FIRST VERSION OF THIS GATE WAS WRONG AND THE PICTURE SAID SO. It demanded a
# creature's median value equal the PARTY's median value (0.306-0.443), and it took
# the reed nibbler — a pale round grazer — down to a near-black olive lump you had
# to hunt for on the grass. The error is a statistics one: a party median is taken
# over a whole human, dark boots and hair and mid-tone cloth together, while a
# two-colour creature's median IS its body. Comparing those two medians compares
# different things.
#
# So the gate is the party's RANGE, not its centre: a creature's paint may sit
# anywhere a person's paint sits, and nowhere brighter or more saturated.
#   V50 inside [party V05, party V95]  — no body darker than her darkest, none
#                                        brighter than her brightest
#   V95 <= party V95 max               — no highlight out-glows the cast
#   S   <= party S50 max               — no creature is more saturated OVERALL
#                                        than a person is at her median
# Measured against it, duskpad and the brook sprite's fallback ghost PASS untouched
# and the other four fail — which is what the lineup frame shows by eye, and is the
# reason to trust the gate.
BAND = dict(v50=(0.192, 0.784), v95_max=0.784, s_max=0.452)

# ---- THE RECIPE --------------------------------------------------------------
# `v` is the TARGET area-weighted median value, `s` a saturation gain, `vcap` a
# ceiling applied as a soft knee so a candy highlight cannot sit above the party's
# own brightest paint. The band above says what is ALLOWED; these say where inside
# it each creature should sit, and every one of them was set by looking at
# docs/qa/battle-monsters/lineup-after.png, not by solving. No entry is a hue
# rotation — hue is the creature's identity, and the palette problem was never
# that a green thing is green.
RECIPE = {
    # A NEON LIME JELLY next to two muted people: V 0.821 sat ABOVE the party's
    # brightest paint (0.784) at half again their median saturation, and it was the
    # loudest thing in the frame. 0.58 keeps it the pale one — it is described as a
    # "round, harmless-looking grazer" — while putting it under Vesper's highlights.
    'reed-nibbler':  dict(v=0.58, s=0.82, vcap=0.74),
    # Mint tube with a candy-red mouth. The greens were nearly in band already
    # (S 0.378); the Red / Yellow / Teeth trio at V 0.906 were not, and the vcap
    # knee is aimed at exactly those three.
    'weir-eel':      dict(v=0.52, s=0.92, vcap=0.72),
    # Painted 512^2 maps carrying baked form-shading, so they read DARK rather than
    # saturated. Both PASS the value gate as they are; the lift is a LEGIBILITY
    # call made on the picture (bramble-shade was a near-black mass whose antlers
    # vanished against the plate), and the saturation pull is what the gate wanted.
    'scree-shell':   dict(v=0.34, s=0.80, vcap=0.74),
    'bramble-shade': dict(v=0.34, s=0.88, vcap=0.74),
    # duskpad and brook-sprite: intentionally absent — both already pass. See the
    # header. Grading art that is already in band is how a style pass loses the one
    # asset it should have been converging on.
}

# =============================================================================
# glTF binary container
# =============================================================================
def read_glb(data):
    magic, ver, total = struct.unpack_from('<III', data, 0)
    assert magic == 0x46546C67, 'not a glb'
    off, js, bin_ = 12, None, None
    while off < len(data):
        ln, ty = struct.unpack_from('<II', data, off)
        chunk = data[off + 8: off + 8 + ln]
        if ty == 0x4E4F534A: js = json.loads(chunk.decode('utf-8'))
        elif ty == 0x004E4942: bin_ = chunk
        off += 8 + ln
    return js, bytearray(bin_ or b'')


def write_glb(js, bin_):
    """Rebuild the container. Every bufferView is re-laid-out in its ORIGINAL ORDER
    with 4-byte alignment, because an image whose bytes changed length invalidates
    every offset after it — and a stale offset is not an error, it is a mesh made
    of somebody else's floats."""
    order = sorted(range(len(js.get('bufferViews', []))),
                   key=lambda i: js['bufferViews'][i].get('byteOffset', 0))
    out, newbv = bytearray(), {}
    for i in order:
        bv = js['bufferViews'][i]
        src = bytes(bin_[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']])
        while len(out) % 4: out.append(0)
        newbv[i] = len(out)
        out += src
    for i, o in newbv.items(): js['bufferViews'][i]['byteOffset'] = o
    while len(out) % 4: out.append(0)
    js['buffers'] = [{'byteLength': len(out)}]
    jb = json.dumps(js, separators=(',', ':')).encode('utf-8')
    jb += b' ' * ((4 - len(jb) % 4) % 4)
    total = 12 + 8 + len(jb) + 8 + len(out)
    return (struct.pack('<III', 0x46546C67, 2, total)
            + struct.pack('<II', len(jb), 0x4E4F534A) + jb
            + struct.pack('<II', len(out), 0x004E4942) + bytes(out))


def replace_view(js, bin_, idx, payload):
    """Swap one bufferView's bytes for a different-length payload. Offsets are
    fixed up by write_glb; here we only need the view's own length right."""
    bv = js['bufferViews'][idx]
    o, n = bv.get('byteOffset', 0), bv['byteLength']
    bin_[o:o + n] = payload
    bv['byteLength'] = len(payload)
    # every later view slides by the delta so write_glb's ORDER key stays sane
    d = len(payload) - n
    if d:
        for j, other in enumerate(js['bufferViews']):
            if j != idx and other.get('byteOffset', 0) > o:
                other['byteOffset'] = other.get('byteOffset', 0) + d
    return bin_


# =============================================================================
# the grade itself
# =============================================================================
def srgb2lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def lin2srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def grade_rgb(r, g, b, vgain, sgain, vcap):
    """One pixel, in sRGB 0..1. Hue is never touched — hue is the creature.

    VALUE MOVES BY A GAIN, NOT A GAMMA, and that was a measured choice. A gamma
    solved on the area-weighted median is fine for a 300-colour painted map and
    catastrophic for a 2-colour flat one: reed-nibbler's median IS its body, so
    the solve wanted gamma 4.17, which took the body from 0.821 to 0.459 and its
    black eyes from 0.117 to 0.000 in the same stroke. A gain is a ratio, so the
    darks stay in proportion to the lights and the paint's own form-shading —
    which is the only detail three of these models have — survives the move.
    The bright end is protected by a soft knee instead."""
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    v = v * vgain
    s = min(1.0, s * sgain)
    if v > vcap:                      # soft knee, so a highlight compresses rather than clips
        v = vcap + (v - vcap) * 0.35
    return colorsys.hsv_to_rgb(h, s, min(1.0, v))


def solve_gain(v50, target):
    """v50 * gain == target."""
    return target / max(1e-4, v50)


# =============================================================================
# measurement — area-weighted, because a 4-pixel eye is not half a monster
# =============================================================================
CT = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
FMT = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}


def accessor(js, bin_, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    n = NC[a['type']]; cs = CT[a['componentType']]
    stride = bv.get('byteStride') or cs * n
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    f = FMT[a['componentType']]
    return [struct.unpack_from('<' + f * n, bin_, base + k * stride) for k in range(a['count'])]


def sample_albedo(js, bin_):
    """[(area, (r,g,b) in sRGB 0..1)] for every triangle in the file, from either
    the baseColorTexture at the triangle's UV centroid or the flat baseColorFactor.
    ONE measurement path for both kinds of model is the whole point — otherwise
    'textured vs flat' is not an axis, it is two incomparable numbers."""
    imgs = {}
    for ti, tex in enumerate(js.get('textures', [])):
        src = js['images'][tex['source']]
        bv = js['bufferViews'][src['bufferView']]
        raw = bytes(bin_[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']])
        imgs[ti] = Image.open(io.BytesIO(raw)).convert('RGB')
    out = []
    for mesh in js.get('meshes', []):
        for p in mesh.get('primitives', []):
            pos = accessor(js, bin_, p['attributes']['POSITION'])
            idx = ([v[0] for v in accessor(js, bin_, p['indices'])] if 'indices' in p
                   else list(range(len(pos))))
            mat = js['materials'][p['material']] if p.get('material') is not None else {}
            pbr = mat.get('pbrMetallicRoughness', {})
            tex = pbr.get('baseColorTexture')
            im = imgs.get(tex['index']) if tex else None
            uv = accessor(js, bin_, p['attributes']['TEXCOORD_0']) if im else None
            flat = None
            if im is None:
                bc = pbr.get('baseColorFactor', [1, 1, 1, 1])
                flat = tuple(lin2srgb(max(0.0, min(1.0, c))) for c in bc[:3])
            W, H = (im.size if im else (0, 0))
            px = im.load() if im else None
            for k in range(0, len(idx) - 2, 3):
                a, b, c = pos[idx[k]], pos[idx[k + 1]], pos[idx[k + 2]]
                u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
                v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                ar = 0.5 * math.sqrt((u[1] * v[2] - u[2] * v[1]) ** 2 +
                                     (u[2] * v[0] - u[0] * v[2]) ** 2 +
                                     (u[0] * v[1] - u[1] * v[0]) ** 2)
                if im is None:
                    out.append((ar, flat)); continue
                cu = sum(uv[idx[k + j]][0] for j in range(3)) / 3
                cv = sum(uv[idx[k + j]][1] for j in range(3)) / 3
                x = min(W - 1, max(0, int(cu * W))); y = min(H - 1, max(0, int((1 - cv) * H)))
                r, g, bb = px[x, y]
                out.append((ar, (r / 255, g / 255, bb / 255)))
    return out


def stats(pairs):
    tot = sum(w for w, _ in pairs) or 1.0
    sx = sy = ss = 0.0; vs = []
    for w, c in pairs:
        h, s, v = colorsys.rgb_to_hsv(*c)
        sx += w * math.cos(h * 2 * math.pi); sy += w * math.sin(h * 2 * math.pi)
        ss += w * s; vs.append((v, w))
    vs.sort()

    def pct(p):
        acc = 0.0
        for v, w in vs:
            acc += w
            if acc >= p * tot: return v
        return vs[-1][0]
    return dict(H=round((math.degrees(math.atan2(sy, sx)) + 360) % 360, 1),
                S=round(ss / tot, 3), V05=round(pct(.05), 3),
                V50=round(pct(.5), 3), V95=round(pct(.95), 3), ncol=len({c for _, c in pairs}))


def in_band(st):
    """Which axes are in band, named — never one opaque boolean. A single OK/FAIL
    hides that a grey wolf fails the SATURATION band for a reason that is correct,
    and a report that cannot say which axis moved is a report you argue with.

    SATURATION IS A CEILING, NEVER A FLOOR, and that is deliberate. duskpad (S 0.055)
    and the brook sprite's fallback ghost (S 0.033) are grey by design; a two-sided
    saturation band measured over Vesper's red hair would fail them and demand a
    coloured wolf, which is a worse picture that scores better."""
    bad = []
    if st['S'] > BAND['s_max']: bad.append('S')
    if not (BAND['v50'][0] <= st['V50'] <= BAND['v50'][1]): bad.append('V50')
    if st['V95'] > BAND['v95_max']: bad.append('V95')
    return 'in band' if not bad else 'out: ' + ','.join(bad)


# =============================================================================
def source_bytes(rev, path):
    return subprocess.check_output(['git', 'show', f'{rev}:{path}'], cwd=ROOT)


ICONDIR = 'public/assets/monsters/placeholder'


def icon_stats(path_or_bytes):
    """Area-weighted hue/S/V of an ICON, opaque pixels only. The alpha matters: a
    render on a transparent field is mostly nothing, and averaging the nothing in
    gives every icon the same colour."""
    im = (Image.open(io.BytesIO(path_or_bytes)) if isinstance(path_or_bytes, (bytes, bytearray))
          else Image.open(path_or_bytes)).convert('RGBA')
    px = im.load()
    pairs = []
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, al = px[x, y]
            if al < 128: continue
            pairs.append((1.0, (r / 255, g / 255, b / 255)))
    return stats(pairs) if pairs else None


def icons_report(rev):
    """THE AGREEMENT MEASURE the audit asked for: 'icon and model matched by measured
    mean hue'. Hue is circular, so the error is the SHORT WAY ROUND — a naive
    subtraction calls 350 deg and 10 deg a 340 deg disagreement.

    WHEN THE MODEL IS GREY THE ERROR IS A CHROMA ERROR, NOT A HUE ONE — and the
    first version of this report got that wrong in a way that hid the headline
    defect. duskpad's albedo is S 0.055; its old icon was a salmon H 354. Comparing
    hues printed 'grey' and said nothing, because a grey model has no meaningful
    hue to disagree with. What the icon actually did was invent 0.44 of saturation
    the wolf does not have, so for an achromatic model the reported error is that
    excess: 'S+0.44'."""
    names = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, MDIR)) if f.endswith('.glb'))
    print(f'{"monster":16} {"model H":>8} {"mdl S":>6} {"icon H":>8} {"ic S":>6} '
          f'{"was H":>8} {"was S":>6} {"err":>8} {"was err":>8}')
    for n in names:
        path = f'{MDIR}/{n}.glb'
        js, bin_ = read_glb(open(os.path.join(ROOT, path), 'rb').read())
        model = stats(sample_albedo(js, bin_))
        ipath = os.path.join(ROOT, ICONDIR, n + '.png')
        now = icon_stats(ipath) if os.path.exists(ipath) else None
        try:
            was = icon_stats(source_bytes(rev, f'{ICONDIR}/{n}.png'))
        except subprocess.CalledProcessError:
            was = None

        def err(ic):
            if not ic: return None
            if model['S'] < 0.12:
                return 'S+%.2f' % max(0.0, ic['S'] - model['S'])
            if ic['S'] < 0.12: return 'S-%.2f' % (model['S'] - ic['S'])
            d = abs(model['H'] - ic['H']) % 360
            return '%.1f' % min(d, 360 - d)
        print(f'{n:16} {model["H"]:8} {model["S"]:6} {(now["H"] if now else "-"):>8} '
              f'{(now["S"] if now else "-"):>6} {(was["H"] if was else "-"):>8} '
              f'{(was["S"] if was else "-"):>6} {str(err(now)):>8} {str(err(was)):>8}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rev', default=SOURCE_REV)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--icons', action='store_true',
                    help='compare the turn-queue foe icons against the models they name')
    ap.add_argument('--only', default=None)
    a = ap.parse_args()
    if a.icons: icons_report(a.rev); return 0
    if not (a.write or a.check): a.check = True

    names = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, MDIR)) if f.endswith('.glb'))
    if a.only: names = [n for n in names if n in a.only.split(',')]
    print(f'source rev {a.rev}   band: V50 in {BAND["v50"]}  V95<={BAND["v95_max"]}  S<={BAND["s_max"]}')
    print(f'{"monster":16} {"":>4} {"H":>6} {"S":>6} {"V05":>6} {"V50":>6} {"V95":>6} {"cols":>6}  band')
    for n in names:
        path = f'{MDIR}/{n}.glb'
        js, bin_ = read_glb(source_bytes(a.rev, path))
        before = stats(sample_albedo(js, bin_))
        print(f'{n:16} {"src":>4} {before["H"]:6} {before["S"]:6} {before["V05"]:6} '
              f'{before["V50"]:6} {before["V95"]:6} {before["ncol"]:6}  {in_band(before)}')
        r = RECIPE.get(n)
        if not r:
            # HELD AS REFERENCE ART — and RESTORED, not merely skipped. A model that
            # leaves the recipe must go back to its pristine bytes in the same run,
            # or an earlier grade of it silently keeps shipping and the recipe stops
            # being the whole description of the difference.
            print(f'{"":16} {"keep":>4}   (no recipe: held as reference art — see the header)')
            if a.write:
                cur = os.path.join(ROOT, path)
                src = source_bytes(a.rev, path)
                if not os.path.exists(cur) or open(cur, 'rb').read() != src:
                    with open(cur, 'wb') as fh: fh.write(src)
                    print(f'{"":16} {"":>4} RESTORED {path}  {len(src)} bytes')
            continue
        gain = solve_gain(before['V50'], r['v'])
        # 1. the flat baseColorFactors
        for m in js.get('materials', []):
            pbr = m.get('pbrMetallicRoughness')
            if not pbr or 'baseColorFactor' not in pbr or 'baseColorTexture' in pbr: continue
            bc = pbr['baseColorFactor']
            s = [lin2srgb(max(0.0, min(1.0, c))) for c in bc[:3]]
            g = grade_rgb(*s, gain, r['s'], r['vcap'])
            pbr['baseColorFactor'] = [srgb2lin(max(0.0, min(1.0, c))) for c in g] + [bc[3] if len(bc) > 3 else 1]
        # 2. the painted maps — every pixel, same transform, so a flat model and a
        #    painted one are graded by ONE rule and not by two that agree by luck.
        base_imgs = set()
        for m in js.get('materials', []):
            t = (m.get('pbrMetallicRoughness', {}) or {}).get('baseColorTexture')
            if t: base_imgs.add(js['textures'][t['index']]['source'])
        for si in sorted(base_imgs):
            src = js['images'][si]
            if 'bufferView' not in src: continue
            bv = js['bufferViews'][src['bufferView']]
            raw = bytes(bin_[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']])
            im = Image.open(io.BytesIO(raw)); mode = im.mode
            rgb = im.convert('RGB'); px = rgb.load()
            for y in range(rgb.height):
                for x in range(rgb.width):
                    cr, cg, cb = px[x, y]
                    gr = grade_rgb(cr / 255, cg / 255, cb / 255, gain, r['s'], r['vcap'])
                    px[x, y] = tuple(int(round(max(0.0, min(1.0, c)) * 255)) for c in gr)
            buf = io.BytesIO()
            (rgb if mode != 'RGBA' else rgb.convert('RGBA')).save(buf, format='PNG', optimize=True)
            bin_ = replace_view(js, bin_, src['bufferView'], buf.getvalue())
        after = stats(sample_albedo(js, bin_))
        print(f'{"":16} {"->":>4} {after["H"]:6} {after["S"]:6} {after["V05"]:6} '
              f'{after["V50"]:6} {after["V95"]:6} {after["ncol"]:6}  {in_band(after)}')
        if a.write:
            out = write_glb(js, bin_)
            with open(os.path.join(ROOT, path), 'wb') as fh: fh.write(out)
            print(f'{"":16} {"":>4} WROTE {path}  {len(out)} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
