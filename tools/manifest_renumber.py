#!/usr/bin/env python3
"""manifest_renumber.py — make KITLIB_MANIFEST's finding numbers strictly monotonic.

  python3 tools/manifest_renumber.py            # dry run: prints every edit
  python3 tools/manifest_renumber.py --write     # applies them

WHY.  Districts were built by concurrent agents, and each numbered its findings from
the max it could see when it STARTED, so three separate pairs of passes collided:

    Waterfront            65-79    |  Locksfoot PREP  79-88     -> 79 used twice
    Gate Approach POLISH  121-131  |  Overworld ROUND 2 121-138 -> 11 numbers twice
    Overworld ROUND 3 139-156      |  Weave           139-162   -> 24 numbers twice
    + Shelf tier          157-165

and the Gate POLISH block also sits BEFORE Locksfoot's 104-120 in the file, so the
document does not even read in ascending order.  36 numbers were ambiguous: "finding
131" meant the deletions-manifest lesson to the gate and shelf agents and the alpha-
atlas lesson to the overworld agents.

WHAT.  Numbers are reassigned by FILE ORDER, contiguously from the first collision
(so everything <= 78, which is what most of the corpus cites, is untouched):

    section (in file order)          old        new
    Locksfoot PREP                   79-88      80-89
    Gate Approach                    89-103     90-104
    Gate Approach POLISH             121-131    105-115
    Locksfoot                        104-120    116-132
    Overworld ROUND 2                121-138    133-150
    Overworld ROUND 3                139-156    151-168
    Shelf tier                       157-165    169-177
    Weave                            139-162    178-201

Cross-references are rewritten with a PER-FILE scope, because the same number has to
resolve differently depending on which agent wrote the citation: the shelf and gate
scripts mean the Gate POLISH block by 121-131, the overworld scripts mean Overworld
ROUND 2, and only the weave scripts mean the Weave block.  Every rewrite is printed
with the headline of the finding it now points at, so a wrong scope is visible rather
than silent.
"""
import re, os, sys, json

REPO = "/Users/junshernchan/projects/multiplayer-rpg"
MANIFEST = REPO + "/tools/blends/KITLIB_MANIFEST.md"
WRITE = "--write" in sys.argv

# ---------------------------------------------------------------- the sections
# (heading substring that opens it, old first, old last, new first)
SECTIONS = [
    ("Locksfoot PREP findings",          79, 88,  80),
    ("Gate Approach findings",           89, 103, 90),
    ("Gate Approach POLISH findings",   121, 131, 105),
    ("Locksfoot findings",              104, 120, 116),
    ("Overworld ROUND 2 findings",      121, 138, 133),
    ("Overworld ROUND 3 findings",      139, 156, 151),
    ("Shelf tier findings",             157, 165, 169),   # heading inserted by this script
    ("Weave findings",                  139, 162, 178),
]
MAXNUM = 201

# scope name -> how a cited number maps.  'neutral' can only resolve numbers that
# are unambiguous; anything ambiguous in a neutral file is reported, not guessed.
SHIFT = {
    # (lo, hi, scope-or-None, delta)
    "prep":     (80, 88, +1),
    "gate":     (89, 103, +1),
    "lf":       (104, 120, +12),
    "gpol":     (121, 131, -16),
    "ow2":      (121, 138, +12),
    "ow3":      (139, 156, +12),
    "shelf":    (157, 165, +12),
    "weave":    (139, 162, +39),
}

# Which numbering era each citing file belongs to, for the two ambiguous bands.
#   'gate'  -> 121-131 means Gate Approach POLISH
#   'ow'    -> 121-138 means Overworld ROUND 2, 139-156 Overworld ROUND 3
#   'weave' -> 139-162 means the Weave
FILE_SCOPE = [
    (re.compile(r"tools/(gate|shelf)_[a-z_]*\.py$"),               "gate"),
    (re.compile(r"docs/plans/shelf-tier-handover\.md$"),           "gate"),
    (re.compile(r"districts/shelf_branch_deletions\.json$"),       "gate"),
    (re.compile(r"tools/overworld\d*_[a-z_]*\.py$"),               "ow"),
    (re.compile(r"tools/weave_[a-z_]*\.py$"),                      "weave"),
    (re.compile(r"tools/(master_|merge_)[a-z_]*\.py$"),            "weave"),
    (re.compile(r"districts/gate_branch_base\.json$"),             "weave"),
]

REF = re.compile(r"\b(findings?|manifest(?:\s+findings?)?)\b([- –]*)"
                 r"((?:\d+\s*(?:[-/,–]|and|to)\s*)*\d+)", re.I)


def load(path):
    return open(path, encoding="utf-8").read()


# ------------------------------------------------------- 1. map the manifest
text = load(MANIFEST)
lines = text.split("\n")

# The Shelf tier's 9 findings were appended into the Overworld ROUND 3 section with
# no heading of their own, which is half of why they read as overworld findings.
# Give them one; it also defines the section boundary this script needs.
shelf_start = None
for i, l in enumerate(lines):
    if re.match(r"^157\.\s+\*\*", l):
        shelf_start = i
        break
assert shelf_start is not None, "could not find old finding 157 (the Shelf block)"

SHELF_HEADING = [
    "---",
    "",
    "## Shelf tier findings (the west branch's SECOND district — `tools/shelf_*.py`)",
    "",
    "The shop street one tier below the gate (`p-shelf-w` + `p-shelf-e`: inn, item,",
    "weapon and armor shops, shelf-homes), built on the same branch blend under the",
    "same additive-only protocol.  These nine were written into the Overworld ROUND 3",
    "section with no heading of their own and read as overworld findings for it.",
    "",
]
lines = lines[:shelf_start] + SHELF_HEADING + lines[shelf_start:]

# Section index per line, built from explicit START LINES rather than by resetting on
# every `## ` line: the Overworld ROUND 3 heading is WRAPPED across two `## ` lines,
# and treating its continuation as an unknown section silently left that whole block
# unrenumbered (its 139-156 then collided with Overworld ROUND 2's new 139-150).
starts = []
for name, o0, o1, n0 in SECTIONS:
    hit = [i for i, l in enumerate(lines) if l.startswith("## ") and name in l]
    assert len(hit) == 1, "%r matches %d headings" % (name, len(hit))
    starts.append((hit[0], name))
starts.sort()
assert [n for _, n in starts] == [s[0] for s in SECTIONS], \
    "SECTIONS is not in file order: %s" % [n for _, n in starts]
sec_of = [None] * len(lines)
for idx, (ln, name) in enumerate(starts):
    end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
    for i in range(ln, end):
        sec_of[i] = name

SECBY = {name: (o0, o1, n0) for name, o0, o1, n0 in SECTIONS}
themap = {}          # (section, old) -> new
out = []
renumbered = 0
for i, l in enumerate(lines):
    m = re.match(r"^(\d+)\.(\s+\*\*.*)$", l)
    if m and sec_of[i] in SECBY:
        old = int(m.group(1))
        o0, o1, n0 = SECBY[sec_of[i]]
        assert o0 <= old <= o1, "%s: finding %d outside its section's %d-%d" % (
            sec_of[i], old, o0, o1)
        new = n0 + (old - o0)
        themap[(sec_of[i], old)] = new
        out.append("%d.%s" % (new, m.group(2)))
        if new != old:
            renumbered += 1
        continue
    out.append(l)
lines = out

# headline lookup for the verification print
head = {}
for l in lines:
    m = re.match(r"^(\d+)\.\s+\*\*(.{0,64})", l)
    if m:
        head[int(m.group(1))] = m.group(2).replace("**", "").strip()

print("=" * 78)
print("MANIFEST RENUMBER — %d findings renumbered, new max %d" % (renumbered, MAXNUM))
print("=" * 78)
for name, o0, o1, n0 in SECTIONS:
    print("  %-32s %3d-%-3d -> %3d-%d" % (name, o0, o1, n0, n0 + (o1 - o0)))

nums = [int(re.match(r"^(\d+)\.", l).group(1)) for l in lines if re.match(r"^\d+\.\s+\*\*", l)]
assert len(nums) == len(set(nums)), "still duplicated: %s" % [
    n for n in set(nums) if nums.count(n) > 1]
assert nums == sorted(nums), "not monotonic at %s" % [
    (a, b) for a, b in zip(nums, nums[1:]) if b <= a][:5]
assert max(nums) == MAXNUM, "max is %d, expected %d" % (max(nums), MAXNUM)
print("  -> %d findings, strictly ascending, no duplicates, max %d"
      % (len(nums), max(nums)))

# ------------------------------------------- 2. rewrite the cross-references
def scope_for(path, lineno, seclist=None):
    rel = path.replace(REPO + "/", "")
    if rel.endswith("KITLIB_MANIFEST.md"):
        s = seclist[lineno]
        if s in ("Gate Approach findings", "Gate Approach POLISH findings",
                 "Shelf tier findings"):
            return "gate"
        if s in ("Overworld ROUND 2 findings", "Overworld ROUND 3 findings"):
            return "ow"
        if s == "Weave findings":
            return "weave"
        return "neutral"
    for rx, sc in FILE_SCOPE:
        if rx.search(rel):
            return sc
    return "neutral"


AMBIG = []


def remap(n, scope, whole):
    """Map one cited number.  `whole` is the full citation text, used only for the
    one genuinely ambiguous bare number in the corpus: 79."""
    if n <= 78:
        return n
    if n == 79:
        # Waterfront 79 ("a district must register its assemblies") stays 79;
        # Locksfoot PREP 79 ("kitlib cannot ship through glTF") becomes 80, and it
        # is only ever cited as the range 79-81.
        return 80 if re.search(r"79\s*[-–]\s*8[01]", whole) else 79
    if 80 <= n <= 88:
        return n + 1
    if 89 <= n <= 103:
        return n + 1
    if 104 <= n <= 120:
        return n + 12
    if 121 <= n <= 131:
        if scope == "gate":
            return n - 16
        if scope in ("ow",):
            return n + 12
        AMBIG.append((n, scope, whole))
        return n
    if 132 <= n <= 138:
        return n + 12
    if 139 <= n <= 156:
        if scope == "weave":
            return n + 39
        if scope in ("ow", "gate", "neutral"):
            return n + 12
        AMBIG.append((n, scope, whole))
        return n
    if 157 <= n <= 162:
        if scope == "weave":
            return n + 39
        return n + 12
    if 163 <= n <= 165:
        return n + 12
    return n


targets = []
for root, dirs, fs in os.walk(REPO):
    dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "scratchpad")]
    for f in fs:
        if f.endswith((".py", ".md", ".json", ".html")):
            targets.append(os.path.join(root, f))

edits = 0
for path in sorted(targets):
    if path.endswith("manifest_renumber.py"):
        continue
    if path == MANIFEST:
        src = lines
        seclist = sec_of
    else:
        try:
            src = load(path).split("\n")
        except Exception:
            continue
        seclist = None
    changed, newsrc = False, []
    for ln, l in enumerate(src):
        if re.match(r"^\d+\.\s+\*\*", l) and path == MANIFEST:
            newsrc.append(l)          # a header, already handled
            continue
        sc = scope_for(path, ln, seclist)

        def sub(m):
            body = m.group(3)
            new_body = re.sub(r"\d+", lambda d: str(remap(int(d.group(0)), sc, m.group(0))), body)
            return m.group(1) + m.group(2) + new_body

        nl = REF.sub(sub, l)
        if nl != l:
            changed = True
            edits += 1
            cited = [int(x) for x in re.findall(r"\d+", nl)]
            tgt = [n for n in cited if n in head]
            print("  %s:%d  [%s]" % (path.replace(REPO + "/", ""), ln + 1, sc))
            print("      - %s" % l.strip()[:150])
            print("      + %s" % nl.strip()[:150])
            for n in tgt[:3]:
                print("        %d = %s" % (n, head.get(n, "?")[:80]))
        newsrc.append(nl)
    if changed and WRITE:
        open(path, "w", encoding="utf-8").write("\n".join(newsrc))
    if path == MANIFEST:
        lines = newsrc

if WRITE:
    open(MANIFEST, "w", encoding="utf-8").write("\n".join(lines))

print("\n  %d cross-reference lines rewritten" % edits)
if AMBIG:
    print("\n  !! AMBIGUOUS, LEFT ALONE — decide by hand:")
    for n, sc, w in AMBIG:
        print("     %s (scope %s) in: %s" % (n, sc, w[:90]))
print("=" * 78)
print("WROTE the files" if WRITE else "dry run — nothing written")
