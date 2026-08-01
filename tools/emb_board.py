"""emb_board.py — THE TOWN-WIDE DRESSING REVIEW BOARD, built from a spec instead of by hand.

    python3 tools/emb_board.py [--spec docs/qa/emberbrook/dressed/board.json]
                               [--out  docs/qa/emberbrook/dressed/index.html]

Reads a JSON spec of sections and frames and writes ONE self-contained HTML page — grids
of stills, before/after comparison sliders, and number tables — on a neutral dark grey,
so that nothing around a frame tints the judgement of the frame.  No CDN, no external
CSS or JS, no fonts fetched: the page opens the same off a file:// path as it does served
at :3000.  Every frame carries its own tape: pixel dimensions and file size are read off
the file with PIL at build time and printed in the caption, so a stale, half-written or
wrong-resolution render cannot pass itself off as the new one.

IT RENDERS NOTHING AND IT MEASURES NOTHING.  No bpy, no Blender, no luminance — stdlib +
PIL only.  It will not invent a number.  Levels belong to `tools/emb_lum.py` and reach
this page only because somebody ran the ruler and typed the result into the spec's table
rows.  This file is a presenter; the instruments are elsewhere and stay elsewhere.

WHY IT EXISTS.  The pilot gate's board, `docs/qa/emberbrook/styleprobe/pilot.html`, is
hand-written HTML, and that was the right shape for six frames of one mill corner.  A
town is not six frames, and a hand-written board rots the moment a frame is re-rendered,
renamed or dropped — which is the same failure mode as the ad-hoc measurement snippets
that cost the dressing gate two rounds.  A generator re-runs; a page typed out once does
not.

AND A MISSING FRAME IS SHOWN, NOT SKIPPED.  A listed image that is not on disk renders as
a placeholder tile naming the path it wanted, and the CLI prints the count found against
the count missing for every section.  A board that silently drops a frame reads as a
complete review of a town that was never fully looked at, and that is the more expensive
lie.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.parse

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEF_SPEC = os.path.join(REPO, "docs", "qa", "emberbrook", "dressed", "board.json")
DEF_OUT = os.path.join(REPO, "docs", "qa", "emberbrook", "dressed", "index.html")

# path prefixes in the spec that mean "from the repo root", not "next to the board"
REPO_PREFIXES = ("docs/", "public/", "tools/", "src/")


# ---------------------------------------------------------------- text

def esc(s):
    """escape, then allow the two inline marks the repo's boards already use:
    `code` and **bold**.  Everything else in the spec is literal text."""
    t = html.escape("" if s is None else str(s))
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t


def human_bytes(n):
    if n < 1024:
        return "%d B" % n
    if n < 1024 * 1024:
        return "%.0f kB" % (n / 1024.0)
    return "%.1f MB" % (n / 1048576.0)


def slug(s, fallback):
    t = re.sub(r"[^a-z0-9]+", "-", str(s or "").lower()).strip("-")
    return t or fallback


# ---------------------------------------------------------------- paths

def resolve(src, board_dir):
    """spec paths are relative to the board dir, unless they start with a repo prefix
    (docs/ public/ tools/ src/) or are absolute.  Returns the absolute path."""
    if not src:
        return None
    s = str(src).replace("\\", "/")
    if os.path.isabs(s):
        return os.path.normpath(s)
    if s.startswith("./"):
        s = s[2:]
    if s.startswith(REPO_PREFIXES):
        return os.path.normpath(os.path.join(REPO, s))
    return os.path.normpath(os.path.join(board_dir, s))


def href(abs_path, out_dir):
    """a relative URL from the written page to the file.  Relative is what makes the
    page work BOTH as file:// and served at :3000/docs/qa/emberbrook/dressed/."""
    rel = os.path.relpath(abs_path, out_dir).replace(os.sep, "/")
    return urllib.parse.quote(rel, safe="/._-~()")


def shown(abs_path):
    """the path to print at the reader — repo-relative when it is inside the repo."""
    rel = os.path.relpath(abs_path, REPO)
    return abs_path if rel.startswith("..") else rel.replace(os.sep, "/")


# ---------------------------------------------------------------- frames

class Frame(object):
    """one image slot: found or not, with its own tape."""

    def __init__(self, src, board_dir, out_dir):
        self.src = src
        self.abs = resolve(src, board_dir)
        self.ok = bool(self.abs) and os.path.isfile(self.abs)
        self.w = self.h = 0
        self.bytes = 0
        self.tape = ""
        self.href = ""
        self.shown = shown(self.abs) if self.abs else str(src)
        if not self.ok:
            return
        self.href = href(self.abs, out_dir)
        self.bytes = os.path.getsize(self.abs)
        try:
            with Image.open(self.abs) as im:
                self.w, self.h = im.size
            self.tape = "%dx%d · %s" % (self.w, self.h, human_bytes(self.bytes))
        except Exception as e:                                # a file that is not an image
            self.tape = "%s · UNREADABLE (%s)" % (human_bytes(self.bytes), e)

    @property
    def ratio(self):
        return "%d / %d" % (self.w, self.h) if self.w and self.h else "16 / 9"


def missing_tile(fr, note="frame missing"):
    return ("<div class='miss'><div class='mx'>%s</div>"
            "<div class='mp'>%s</div>"
            "<div class='mn'>expected on disk; nothing there at build time</div></div>"
            % (esc(note), esc(fr.shown)))


def meta_line(fr, meta):
    bits = [b for b in (meta, fr.tape) if b]
    return " · ".join(esc(b) for b in bits)


def img_tag(fr, cls, caption):
    return ("<img class='%s' loading='lazy' src='%s' alt='%s' "
            "data-full='%s' data-cap='%s'>"
            % (cls, fr.href, esc(caption or os.path.basename(fr.shown)),
               fr.href, html.escape("%s — %s" % (os.path.basename(fr.shown), fr.tape))))


# ---------------------------------------------------------------- sections

def render_grid(sec, board_dir, out_dir, stat):
    out = []
    cols = int(sec.get("cols") or 0)
    style = (" style='grid-template-columns:repeat(%d,minmax(0,1fr))'" % cols) if cols else ""
    out.append("<div class='grid'%s>" % style)
    for sh in sec.get("shots") or []:
        fr = Frame(sh.get("src"), board_dir, out_dir)
        stat.count(fr)
        cap = sh.get("caption") or os.path.basename(fr.shown)
        out.append("<figure class='card'>")
        out.append(img_tag(fr, "frame", cap) if fr.ok else missing_tile(fr))
        out.append("<figcaption><div class='cap'>%s</div><div class='meta'>%s</div></figcaption>"
                   % (esc(cap), meta_line(fr, sh.get("meta"))))
        out.append("</figure>")
    out.append("</div>")
    return "\n".join(out)


def render_pairs(sec, board_dir, out_dir, stat):
    out = []
    for i, pr in enumerate(sec.get("pairs") or []):
        a = Frame(pr.get("before"), board_dir, out_dir)
        b = Frame(pr.get("after"), board_dir, out_dir)
        stat.count(a)
        stat.count(b)
        cap = pr.get("caption") or ""
        la = pr.get("before_label") or "before"
        lb = pr.get("after_label") or "after"
        note = ""
        out.append("<figure class='card pair'>")
        if a.ok and b.ok and (a.w, a.h) == (b.w, b.h) and a.w:
            # both present and the same size — the slider is honest
            out.append("<div class='cmp' style='aspect-ratio:%s'>" % a.ratio)
            out.append(img_tag(a, "ia", "%s — %s" % (la, cap)))
            out.append(img_tag(b, "ib", "%s — %s" % (lb, cap)))
            out.append("<span class='lab la'>%s</span><span class='lab lb'>%s</span>"
                       % (esc(la), esc(lb)))
            out.append("<span class='handle'></span>")
            out.append("<input type='range' min='0' max='100' value='50' step='0.1' "
                       "aria-label='%s wipe'>" % esc(cap or "before/after"))
            out.append("</div>")
            out.append("<div class='ptools'><button type='button' class='tg'>side by side</button>"
                       "<a href='%s' class='lk' data-full='%s'>open %s</a>"
                       "<a href='%s' class='lk' data-full='%s'>open %s</a></div>"
                       % (a.href, a.href, esc(la), b.href, b.href, esc(lb)))
        else:
            if a.ok and b.ok:
                note = ("side by side: the two frames are not the same size "
                        "(%s vs %s), so a wipe would lie" % (a.tape, b.tape))
            out.append("<div class='cmp sbs static'>")
            out.append(img_tag(a, "ia", "%s — %s" % (la, cap)) if a.ok
                       else missing_tile(a, "%s missing" % la))
            out.append(img_tag(b, "ib", "%s — %s" % (lb, cap)) if b.ok
                       else missing_tile(b, "%s missing" % lb))
            out.append("</div>")
        out.append("<figcaption><div class='cap'>%s</div>" % esc(cap))
        metas = []
        if pr.get("meta"):
            metas.append(esc(pr["meta"]))
        metas.append("%s %s" % (esc(la), esc(a.tape) if a.ok else "<span class='warn'>MISSING</span>"))
        metas.append("%s %s" % (esc(lb), esc(b.tape) if b.ok else "<span class='warn'>MISSING</span>"))
        out.append("<div class='meta'>%s</div>" % " · ".join(metas))
        if note:
            out.append("<div class='meta warn'>%s</div>" % esc(note))
        out.append("</figcaption></figure>")
    return "\n".join(out)


def cell(c):
    """a table cell is a string, or {"text": ..., "cls": "warn|ok|dim"}."""
    if isinstance(c, dict):
        return "<td class='%s'>%s</td>" % (esc(c.get("cls") or ""), esc(c.get("text")))
    return "<td>%s</td>" % esc(c)


def render_table(sec, board_dir, out_dir, stat):
    cols = sec.get("columns") or []
    out = ["<table>"]
    if cols:
        out.append("<tr>%s</tr>" % "".join("<th>%s</th>" % esc(c) for c in cols))
    for row in sec.get("rows") or []:
        cls = ""
        if isinstance(row, dict):
            cls = " class='%s'" % esc(row.get("cls") or "")
            row = row.get("cells") or []
        out.append("<tr%s>%s</tr>" % (cls, "".join(cell(c) for c in row)))
    out.append("</table>")
    if sec.get("note"):
        out.append("<p class='note'>%s</p>" % esc(sec["note"]))
    return "\n".join(out)


KINDS = {"grid": render_grid, "pairs": render_pairs, "table": render_table}


class Stat(object):
    def __init__(self, sid):
        self.sid = sid
        self.found = 0
        self.missing = []

    def count(self, fr):
        if fr.ok:
            self.found += 1
        else:
            self.missing.append(fr.shown)


# ---------------------------------------------------------------- page

CSS = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{background:#101010;color:#e4e4e4;margin:0;padding:0 0 90px;
     font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     -webkit-font-smoothing:antialiased}
a{color:#d8b98a;text-decoration:none}
a:hover{text-decoration:underline}
code{color:#d8b98a;font-size:.92em}
.bar{position:sticky;top:0;z-index:40;background:#161616;border-bottom:1px solid #2a2a2a;
     padding:12px 26px 10px}
.bar h1{font-size:17px;font-weight:600;margin:0;color:#f0ece6}
.bar .sub{font-size:13px;color:#9a9a9a;margin:3px 0 0;max-width:80em}
.bar .stamp{font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#7d7d7d;margin-top:5px}
.jump{margin-top:9px;display:flex;flex-wrap:wrap;gap:6px}
.jump a{font-size:12px;color:#c9c2b6;border:1px solid #2f2f2f;border-radius:3px;
        padding:3px 9px;background:#1c1c1c}
.jump a:hover{border-color:#4a443a;color:#e8dcc8;text-decoration:none}
main{padding:0 26px}
section{padding-top:26px;margin-top:14px;border-top:1px solid #232323;scroll-margin-top:118px}
section:first-of-type{border-top:0}
h2{font-size:15px;font-weight:600;color:#d8b98a;letter-spacing:.02em;margin:0 0 4px}
h2 .n{color:#6f6f6f;font-weight:400;font-size:12px;margin-left:8px;letter-spacing:0}
.blurb{max-width:74em;color:#b4b4b4;margin:6px 0 16px}
.note{max-width:74em;color:#8e8e8e;font-size:13px;margin:8px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:22px;margin:4px 0}
.card{margin:0 0 22px;background:#1a1a1a;border:1px solid #262626;border-radius:3px;padding:10px}
.card img{display:block;width:100%;height:auto;background:#1a1a1a;cursor:zoom-in}
figcaption{padding:8px 2px 2px}
.cap{font-size:13px;color:#cfcfcf}
.meta{font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:#828282;margin-top:3px;
      word-break:break-word}
.warn{color:#e0a06a}
.ok{color:#9dc08b}
.dim{color:#7d7d7d}
.miss{background:repeating-linear-gradient(45deg,#191919,#191919 9px,#1e1e1e 9px,#1e1e1e 18px);
      border:1px dashed #55483a;border-radius:2px;aspect-ratio:16/9;display:flex;
      flex-direction:column;align-items:center;justify-content:center;text-align:center;
      padding:16px;gap:6px}
.mx{color:#e0a06a;font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.mp{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:#c0b6a6;word-break:break-all}
.mn{font-size:12px;color:#7d7d7d}
/* --- before/after wipe: LEFT of the handle is `before`, RIGHT is `after`, which is
   what the two corner labels say.  Capped at 78vh so the whole comparison is on screen
   to drag; the letterbox that leaves is the same neutral grey as the card. --- */
.card.pair{max-width:1420px}
.cmp{position:relative;width:100%;max-height:78vh;overflow:hidden;background:#1a1a1a;
     user-select:none;touch-action:pan-y}
.cmp img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
.cmp .ib{clip-path:inset(0 0 0 var(--p,50%))}
.cmp .lab{position:absolute;bottom:8px;z-index:2;font:11px/1 ui-monospace,Menlo,monospace;
          letter-spacing:.08em;text-transform:uppercase;color:#dcdcdc;background:rgba(16,16,16,.72);
          border:1px solid #333;border-radius:2px;padding:4px 7px;pointer-events:none}
.cmp .la{left:8px}
.cmp .lb{right:8px}
.cmp .handle{position:absolute;top:0;bottom:0;left:var(--p,50%);width:2px;background:#e8e8e8;
             margin-left:-1px;z-index:2;pointer-events:none}
.cmp .handle:after{content:"";position:absolute;top:50%;left:50%;width:30px;height:30px;
                   margin:-15px 0 0 -15px;border-radius:50%;border:2px solid #e8e8e8;
                   background:rgba(16,16,16,.55)}
.cmp input[type=range]{position:absolute;inset:0;width:100%;height:100%;margin:0;padding:0;
     opacity:0;cursor:ew-resize;z-index:3;-webkit-appearance:none;appearance:none;
     background:transparent}
.cmp input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:40px;height:400px}
.cmp input[type=range]::-moz-range-thumb{width:40px;height:400px;border:0;background:transparent}
.cmp.sbs{position:static;aspect-ratio:auto!important;max-height:none;display:grid;
         grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px;overflow:visible}
.cmp.sbs img{position:static;width:100%;height:auto;clip-path:none!important;object-fit:fill}
.cmp.sbs .handle,.cmp.sbs input,.cmp.sbs .lab{display:none}
.ptools{display:flex;gap:14px;align-items:center;padding:8px 2px 0;font-size:12px}
.ptools button{font:12px/1 inherit;color:#c9c2b6;background:#1f1f1f;border:1px solid #333;
               border-radius:3px;padding:5px 10px;cursor:pointer}
.ptools button:hover{border-color:#4a443a;color:#e8dcc8}
.ptools .lk{font:12px/1 ui-monospace,Menlo,monospace}
.static.sbs .miss{aspect-ratio:16/9}
/* --- tables --- */
table{border-collapse:collapse;font-size:13px;margin:6px 0;font-variant-numeric:tabular-nums}
td,th{border:1px solid #2a2a2a;padding:4px 11px;text-align:left;vertical-align:top}
th{color:#d8b98a;font-weight:600;background:#181818}
tr.warn td{color:#e0a06a}
tr.ok td{color:#9dc08b}
/* --- lightbox --- */
#lb{position:fixed;inset:0;z-index:90;background:rgba(10,10,10,.965);display:none;
    flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:22px}
#lb.on{display:flex}
#lb img{max-width:97vw;max-height:86vh;object-fit:contain;background:#1a1a1a;cursor:zoom-out}
#lbc{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:#9a9a9a;text-align:center}
#lbx{position:absolute;top:14px;right:20px;color:#9a9a9a;font-size:22px;cursor:pointer;
     line-height:1;padding:6px}
@media (max-width:760px){
  .grid{grid-template-columns:1fr}
  main,.bar{padding-left:14px;padding-right:14px}
}
"""

JS = """
(function(){
  // before/after wipes
  document.querySelectorAll('.cmp input[type=range]').forEach(function(r){
    var c=r.closest('.cmp');
    var set=function(){c.style.setProperty('--p',r.value+'%');};
    r.addEventListener('input',set); set();
  });
  document.querySelectorAll('.ptools .tg').forEach(function(b){
    b.addEventListener('click',function(){
      var c=b.closest('.pair').querySelector('.cmp');
      var on=c.classList.toggle('sbs');
      b.textContent=on?'wipe':'side by side';
    });
  });
  // lightbox
  var shots=[].slice.call(document.querySelectorAll('[data-full]'));
  var lb=document.getElementById('lb'), im=document.getElementById('lbi'),
      cp=document.getElementById('lbc'), i=0;
  function show(n){
    if(!shots.length)return;
    i=(n+shots.length)%shots.length;
    var s=shots[i];
    im.src=s.getAttribute('data-full');
    cp.textContent=(s.getAttribute('data-cap')||'')+'   ['+(i+1)+'/'+shots.length+']';
    lb.classList.add('on');
  }
  function hide(){lb.classList.remove('on'); im.removeAttribute('src');}
  shots.forEach(function(s,n){
    s.addEventListener('click',function(e){e.preventDefault(); show(n);});
  });
  lb.addEventListener('click',hide);
  document.addEventListener('keydown',function(e){
    if(!lb.classList.contains('on'))return;
    if(e.key==='Escape')hide();
    else if(e.key==='ArrowRight'){e.preventDefault(); show(i+1);}
    else if(e.key==='ArrowLeft'){e.preventDefault(); show(i-1);}
  });
})();
"""


def build(spec, board_dir, out_dir):
    stats = []
    body = []
    nav = []
    for n, sec in enumerate(spec.get("sections") or []):
        sid = slug(sec.get("id") or sec.get("title"), "s%d" % (n + 1))
        st = Stat(sid)
        kind = (sec.get("kind") or "grid").lower()
        fn = KINDS.get(kind)
        # content first: the heading carries the found/missing count, so a gap in the
        # board is visible on the page itself and not only in the shell that built it
        if fn is None:
            content = ("<p class='blurb warn'>unknown section kind %s — nothing rendered. "
                       "known kinds: grid, pairs, table.</p>" % esc(kind))
        else:
            content = fn(sec, board_dir, out_dir, st)
        tail = ""
        if kind in ("grid", "pairs"):
            tail = "%d frame%s" % (st.found, "" if st.found == 1 else "s")
            if st.missing:
                tail += " · <span class='warn'>%d MISSING</span>" % len(st.missing)
        body.append("<section id='%s'>" % esc(sid))
        body.append("<h2>%s<span class='n'>%s</span></h2>"
                    % (esc(sec.get("title") or sid), tail))
        if sec.get("blurb"):
            body.append("<p class='blurb'>%s</p>" % esc(sec["blurb"]))
        body.append(content)
        body.append("</section>")
        nav.append("<a href='#%s'>%s</a>" % (esc(sid), esc(sec.get("title") or sid)))
        stats.append((st, kind))

    doc = []
    doc.append("<!doctype html>")
    doc.append("<meta charset='utf-8'>")
    doc.append("<meta name='viewport' content='width=device-width,initial-scale=1'>")
    doc.append("<title>%s</title>" % html.escape(spec.get("title") or "Emberbrook dressing review board"))
    doc.append("<style>%s</style>" % CSS)
    doc.append("<header class='bar'>")
    doc.append("<h1>%s</h1>" % esc(spec.get("title") or "Emberbrook dressing review board"))
    if spec.get("subtitle"):
        doc.append("<p class='sub'>%s</p>" % esc(spec["subtitle"]))
    if spec.get("stamp"):
        doc.append("<div class='stamp'>%s</div>" % esc(spec["stamp"]))
    doc.append("<nav class='jump'>%s</nav>" % "".join(nav))
    doc.append("</header>")
    doc.append("<main>")
    doc.extend(body)
    doc.append("</main>")
    doc.append("<div id='lb'><span id='lbx'>&times;</span><img id='lbi' alt=''>"
               "<div id='lbc'></div></div>")
    doc.append("<script>%s</script>" % JS)
    return "\n".join(doc) + "\n", stats


def main(argv):
    ap = argparse.ArgumentParser(description="build the Emberbrook dressing review board")
    ap.add_argument("--spec", default=DEF_SPEC, help="board spec JSON (default %s)" % shown(DEF_SPEC))
    ap.add_argument("--out", default=DEF_OUT, help="page to write (default %s)" % shown(DEF_OUT))
    a = ap.parse_args(argv)

    spec_path = os.path.abspath(a.spec)
    out_path = os.path.abspath(a.out)
    if not os.path.isfile(spec_path):
        print("emb_board: NO SPEC at %s" % spec_path, file=sys.stderr)
        print("           write one (see the docstring) or pass --spec", file=sys.stderr)
        return 2
    try:
        with open(spec_path) as f:
            spec = json.load(f)
    except ValueError as e:
        print("emb_board: spec is not valid JSON (%s): %s" % (spec_path, e), file=sys.stderr)
        return 2

    board_dir = os.path.dirname(spec_path)
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    page, stats = build(spec, board_dir, out_dir)

    missing = 0
    for st, kind in stats:
        note = "" if kind == "table" else "%2d found  %2d missing" % (st.found, len(st.missing))
        print("  %-22s %-6s %s" % (st.sid, kind, note or "(no frames)"))
        for m in st.missing:
            print("      MISSING  %s" % m)
        missing += len(st.missing)

    with open(out_path, "w") as f:
        f.write(page)
    print("  wrote %s  (%s)" % (shown(out_path), human_bytes(len(page.encode("utf-8")))))
    if missing:
        print("  WARNING: %d listed frame%s not on disk — shown on the board as placeholders"
              % (missing, "" if missing == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
