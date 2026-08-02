# MORNING BRIEF — 2026-08-02

Written at ~04:00 while the last plates bake. Supersedes RESUME.md (that file described
the paused state; the lanes have since run). ~95 commits, all pushed and verified.

---

## DO THIS FIRST

**Open `localhost:3000` and press NEW GAME.** Until tonight there was no front door: every
hub card was a developer jump and a bare `/play.html` dropped you into Dellhollow. There is
now a NEW GAME / CONTINUE door, and Chapters One and Two run **in the 3D world** — the story
fires as you walk it, the Old Gate opens when you open it, and the valley road between the
two towns is walked rather than skipped.

Then open **`localhost:3000/story.html`** — the whole world on one self-updating page (see
below), and the place to read what the dialogue now sounds like.

---

## THE HEADLINE FINDING (it reframes "wire it up")

**The story was in the wrong runtime.** `chapter1.js` / `chapter2.js` were loaded by exactly
one page — `join-legacy.html`, the old 2D canvas engine. `play.html` had no chapter runner,
no cutscene player, no story flag, no end card, no second player. Your hub page had been
saying so in plain text the whole time. The chapters were the script, the 3D towns were the
stage, and nothing joined them. That bridge is what got built tonight.

---

## WHAT SHIPPED

**Dialogue — the flagship.** Every style failure is gone: **166 → 0**. No line runs three
sentences (133 did), none breaks the word ceiling (25 did), nothing exceeds a 10-year-old's
reading grade. It got *shorter while breathing more*: 12,534 → 11,880 words across 933 →
1,016 boxes — the split-don't-gut trade. Chapter Two carried nearly all the fat (−8.4%); its
examine text had been running as short essays. `docs/exemplars.md` holds the 42-line ratified
style set, every quote verified verbatim against the shipped script.

**The story layer.** A chapter director in the 3D runtime, Chapters One and Two as data
(`public/game/story.json`), a front door, save-state v2 that knows *where you are* with a
migration that refuses to eat a v1 playthrough, and the Old Gate as a conditional edge that
opens the frame the story flag turns.

**Cut-ins.** Vesper (shipped yesterday), **Maren's suite (13 plates)**, Lake's suite, and 11
NPC characters promoted from salvaged art to proper studio sets. **Rowan is parked red** —
his ratified candidate-B identity is blocked on one mood (`hollow`), measured and recorded
rather than forced.

**Emberbrook is populated.** 11 NPCs were scened only to the dev walk bundle, so the town you
actually play through was empty of people. Now dual-scened, with five posts re-measured
against the cinematic bundle's own ground.

**The invisible wall you annotated on a screenshot is fixed.** `fx_dam4_spray` — a water-spray
*effect card* — was standing across the Dellhollow slipway boardwalks as solid collision:
the town's third-largest blocker and **87% of every blocked step in the boatyard district**.
One regex, no rebake.

**Dellhollow exits.** The gate stops being a place you can only leave from; the Boatmen's Rest
gets its own building (see the question below); a new `passages` map record covers prompted
transitions the player is meant to make but cannot walk.

**The story page is now the single world view** (`/story.html`) and it **rebuilds itself** —
change a line, refresh, see it. It telescopes world → chapters → beats → every line, plus
per-character sheets (every line they speak anywhere, their canon, their voice, where they
stand), per-town sheets, the NPC conversation graph, and a continuity-check panel.

**Three new gates guard the story:** `dialogue_style.mjs`, `story_test.mjs` (971 assertions),
`playthrough_test.mjs` (real Chrome, new game to end of Chapter Two). The style gate earned
its keep immediately — widened to cover `story.json`, it caught 28 regressions where lifted
lines had been re-condensed into walls of text.

**Cameras.** Every Emberbrook shot got closer; the mechanism turned out to be **the lens, not
the angle** (fov 35 → 20). gateroad went **21.9% → 68.8% visible** — the worst frame in the
town is now one of the better ones — and the square's long-red ratchet retires green.

---

## DECISIONS WAITING FOR YOU

1. **TWO-PLAYER — the load-bearing one.** The 3D runtime is single-body. Chapter One's climax
   is two keepers on twin sigil plates; Chapter Two's is a six-hand winch. Tonight's build
   makes those completable solo (Lake acts as a companion) so nothing soft-locks, marked
   `// TWO-PLAYER PENDING:` in code. Build two bodies / re-stage as single-player + companion
   / ship single-player — this shapes everything downstream.
2. **The Boatmen's Rest building.** You asked to move its entrance "to the next building
   before the item shop." Measured: **there is no building there** — inn and item shop sit
   0.90 m apart. Also, the old prompt wasn't on a building at all; it stood on the gate
   stair's landing, 4.7 m short of its own inn. It now sits on the taproom's gallery front.
   If you meant a genuinely separate building, that's a new structure to author.
3. **A timeline that's off by a day.** Chapter Two opens with one night on the road, but Lake
   twice says "two days" / "two nights ago", and Pell's Warden sighting only works if two
   nights have passed. The opening narration is probably a night short. Untouched pending
   your ruling. (Also: a line gives Lake Vesper's eleven-day road count, and Vesper says
   she's "watched it all week" about someone she's known two days.)
4. **VOICES.md contradicts itself.** Several of its own PART 2 example lines break its
   two-sentence rule. I enforced the rule; the examples need rewriting or the rule needs a
   fragment exemption.
5. **The camera ceiling — a scope call.** FF-parity is ~115 px of character height; this
   slate delivers a median 65. The arithmetic says why: character size is bounded by *region
   size*, and Emberbrook plays 11 shots over 180 m where Dellhollow plays 16 over 100 m.
   That ~2.5× under-coverage **is** the ants complaint at root. Closing it fully is an 18–22
   shot round — more cameras, not better ones.
6. **Is Lake a stat-carrying party member or a narrative companion?** Decides whether he
   needs a `growth.json` record (he currently has none).
7. **The Chapter One ending.** It ends with both keepers stepping *through* the gate, but the
   gate notch is stamped sealed to zero reachable ground. Mint a walkable stub (map →
   blockout → dressing → re-bake) or end on the doors opening and cut away. Recommendation:
   the cut — no re-bake, better FF grammar.

---

## HONEST REDS AND OPEN ITEMS

- **Two Emberbrook seam failures**, named and routed to a seam-or-map lane: `square<->pondlane`
  (every seam position in its window overlaps `walk_pad_pips-den`) and a 4.7 m town-wide
  mismatch against a 4.1 m budget. Proven **structurally immune** to camera work — seam
  positions derive from ownership and walk geometry, never from where the camera stands — so
  nobody needs to re-test that pairing again.
- **Rowan's cut-in set** is parked on the `hollow` mood.
- **The overworld art revamp did not start.** The camera round owned the GPU all night. The
  Dellhollow apron chop is *measured and staged* as a single control-point edit, not built.
- **Two items I asked lanes to fix don't exist in the repo**: the arch banner's "0.71 m
  clearance" was never measured, and the "cookhouse door occluding the cookhouse" appears
  nowhere. You *did* report the cookhouse door in conversation — it was never written down,
  so it became unfindable. Process lesson: a verbal report that doesn't land in the repo
  turns into a phantom.

---

## THE NIGHT'S LESSON, WHICH IS WORTH MORE THAN ANY ONE FIX

**Three recorded numbers turned out to be wrong**, all found by accident: the camera file's
"interior bound" (measured at a lens no interior uses, and to the far *wall* rather than the
far walkable floor), the waystone framing note (claimed the stone reads screen-left; it is
dead centre at every lens — an *intent* that hardened into a *measurement*), and a 4.3 m seam
mismatch that has always measured 4.7.

Each was caught only because some lane happened to have a reason to re-derive it. **The ones
nobody read closely tonight are still wrong, and nothing would currently tell us.** The
flip side: all three were re-derivable in minutes *because their instrument was named* — a
number recorded without its instrument cannot even be checked.

Related, and the reason several claims in this file are trustworthy: a lane caught its own
**false verification** — "I verified against commit X" where X already contained its own
change, so the check compared a version against itself. It surfaced because a diff returned
an impossible answer ("0 of 11 changed" on a file it had personally rewritten). The rule
that came out of it: **a check that passes in a way too clean to be possible is a bug until
proven otherwise.**
