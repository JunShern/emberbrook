"""ladder_derate.py — THE FALSE LADDERS, MADE VISIBLY UNUSABLE.

WHY THIS EXISTS (FIXLOG round 26, director ruling 2026-08-05).
--------------------------------------------------------------
`dellhollow.map.json` carries three ways off the weave tier down to the water, and
`dellhollow.routes.json` marks two of them `blocked: true`:

    weave:weave-huts__fish-dock    ladder   blocked  [71.45,7.83,-24.0] -> [59.09,1.0,-28.0]
    lockhead:lockhead__lock-five   ladder   blocked  [80.73,14.0,-16.0] -> [86.91,0.0,-28.0]
    weave-huts__moorage            stairs   --       the real one, a double switchback

The shipped game DREW ALL THREE THE SAME.  `route_overlay.js` has known since it was
written that a ladder edge ships no walk ribbon ("a legibility trap worth seeing"),
but the overlay is a debug key and nothing a player can see carried the distinction.
Round 24's playtest agent spent 22 of its first 24 steps at the foot of two painted
ladders it could not climb.  The fix is ART, not a marker: a blocked ladder must
LOOK blocked.

WHAT THIS MODULE IS
-------------------
Pure geometry — no bpy, so it is importable from a builder, from a carrier script
and from a test.  It answers one question: given the ladder a builder was ABOUT to
lay, which parts of it survive?  Callers keep their own primitives and materials.

The vocabulary is Dellhollow's own — rot, a missing run, a plank nailed across:

  * THE LOWER RUN IS GONE.  The two rails part company at DIFFERENT heights
    (`BREAK`), so the silhouette ends ragged in mid-air rather than cut square.
    This is the read that survives to a 2688 px plate seen from 40 m: a ladder
    that does not reach the deck is not a way down.
  * ROTTED RUNGS.  Every third rung above the break is gone, and the break took
    its two neighbours with it.
  * ONE RUNG STILL HANGING by a single nail below the break.
  * A PLANK NAILED DIAGONALLY ACROSS THE HEAD — the read from ABOVE, which is the
    direction a player on the weave tier meets both of these.

PARAMETERISATION.  Everything is in the ladder's own frame:
    s     0 at the head (the top, where it is still attached), 1 at the foot
    side  lateral offset in units of the rail half-separation (-1 = left rail)
A span is (s0, side0, s1, side1) and the caller maps it with

    P(s, side) = HEAD + (FOOT - HEAD) * s + n * (side * halfw)

where `n` is the horizontal unit normal of the run.  `s` is the BUILT run's own
parameter: a builder that already trimmed its ladder short of the walk network
passes its trimmed ends as HEAD/FOOT and this module never has to know.
"""

# The two rails break here — DIFFERENT values on purpose.  A square cut reads as a
# ladder that was shortened; two ragged ends read as one that failed.
BREAK = (0.55, 0.64)

# The break takes the rungs within this much of it (measured in `s`).
BREAK_BITE = 0.12

# Every Nth rung above the break has rotted out.  Phase 1 so the top rung — which
# at the Lockhead is authored deck furniture (lk_build clamps `rung00` flush with
# the pad and opens the parapet rail for it) — always survives.
ROT_EVERY, ROT_PHASE = 3, 1


def rails(head_s=0.0):
    """The two surviving rails, ragged. -> [(s0, side0, s1, side1), ...]"""
    return [(head_s, -1.0, BREAK[0], -1.0),
            (head_s, +1.0, BREAK[1], +1.0)]


def rungs(ss, head_s=0.0):
    """Filter a builder's own rung positions down to the ones still there.

    `ss` is the list of `s` values the builder would have laid rungs at.  Anything
    below the first break is gone with the run; the survivors lose every third and
    the two nearest the break.
    """
    out = []
    kept = 0
    for s in ss:
        if s < head_s - 1e-6 or s > BREAK[0] - BREAK_BITE:
            continue
        if kept % ROT_EVERY == ROT_PHASE:
            kept += 1
            continue
        kept += 1
        out.append(s)
    return out


def bar(head_s=0.0):
    """The plank nailed diagonally across the head. -> (s0, side0, s1, side1)"""
    return (head_s + 0.010, -1.35, head_s + 0.055, +1.35)


def dangle():
    """The one rung still hanging by a nail, below the break."""
    return (BREAK[0] + 0.020, -1.0, BREAK[0] + 0.052, +0.10)


def spans(rung_ss, head_s=0.0):
    """Everything, tagged. -> [(kind, s0, side0, s1, side1), ...]"""
    out = [("rail",) + r for r in rails(head_s)]
    out += [("rung", s, -1.0, s, +1.0) for s in rungs(rung_ss, head_s)]
    out.append(("bar",) + bar(head_s))
    out.append(("dangle",) + dangle())
    return out


def report(rung_ss, head_s=0.0):
    """One line for a builder's log."""
    kept = rungs(rung_ss, head_s)
    return ("lower run GONE below s=%.2f/%.2f (ragged), %d of %d rungs left, "
            "one hanging, a plank across the head" %
            (BREAK[0], BREAK[1], len(kept), len(rung_ss)))
