#!/usr/bin/env python3
# make_qa_index.py — regenerate docs/qa/index.html: a static gallery of every QA
# render, grouped by folder, newest first. Static because the dev server does no
# directory listings. Re-run after adding renders (agents: end of each version).
import os, html, time
ROOT = os.path.join(os.path.dirname(__file__), "..", "docs", "qa")
groups = {}
for dirpath, _, files in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    pngs = [(os.path.getmtime(os.path.join(dirpath, f)), f) for f in files if f.lower().endswith(".png")]
    if pngs:
        groups[rel] = sorted(pngs, reverse=True)
out = ["<meta charset='utf-8'><title>QA renders</title><style>",
       "body{background:#140f0c;color:#ece0d0;font:14px system-ui;margin:24px}",
       "h2{color:#e9a24b;margin:28px 0 8px}",
       ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}",
       "a{color:inherit;text-decoration:none}img{width:100%;border-radius:8px;display:block}",
       ".c{font-size:12px;color:#a89179;margin-top:3px}</style>",
       "<h1>QA renders</h1><p style='color:#a89179'>regenerated %s — newest first per folder</p>" % time.strftime("%Y-%m-%d %H:%M")]
for rel in sorted(groups, key=lambda r: -groups[r][0][0]):
    out.append("<h2>%s</h2><div class='g'>" % html.escape(rel))
    for mt, f in groups[rel]:
        p = ("%s/%s" % (rel, f)) if rel != "." else f
        out.append("<a href='%s' target='_blank'><img loading='lazy' src='%s'><div class='c'>%s · %s</div></a>"
                   % (p, p, html.escape(f), time.strftime("%m-%d %H:%M", time.localtime(mt))))
    out.append("</div>")
open(os.path.join(ROOT, "index.html"), "w").write("\n".join(out))
print("index.html:", sum(len(v) for v in groups.values()), "renders in", len(groups), "folders")
