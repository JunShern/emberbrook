---
name: lane-status
description: Emit the recurring work-status table for this repo's parallel agent lanes — running work, queued work, decisions with the user — with ETAs, confidence flags, deltas since the last refresh, and an honest ETA-accuracy scorecard. Use when the user asks for a status table or a status refresh, and on each scheduled refresh tick.
---

# Lane status report

Ratified by the user 2026-08-02. The user runs many parallel agent lanes here and wants one
scannable table on a fixed cadence — **default every 20 minutes**, or whatever interval they
name. They said the ETAs are the point: *"you should hold yourself accountable for getting
that right — so on each refresh, if things aren't on track with what you expected, you should
own that mistake honestly and note how to improve your ETA estimation for future."*

## Format

Emit as a **markdown table in chat**, not an artifact. It is read in a terminal and it refreshes
often; a published page would churn URLs and add nothing.

Four sections, in this order. **Omit a section entirely if it is empty** — never print an empty
table.

### 1. Running

| # | Item | Doing right now | Started | ETA | Δ | Conf |
|---|---|---|---|---|---|---|

- **Item** — a full description of what the lane is delivering, in the user's vocabulary —
  not a two-word label (user correction 2026-08-02: "the lane descriptions are too short").
- **Doing right now** — the judged activity sentence (see *Gathering state*). The JUDGMENT
  goes in prose BELOW the table, not in a column of its own (user: "I don't need the
  'Judgment' column, you can give commentary outside the table") — and only where there is
  something to say: flag the off-track and the surprising, don't bless every row with a ✅.
- Never drop the ETA/Δ/Conf columns to make room for activity — the user wants BOTH the
  accountability clock and the live activity (correction 2026-08-02, after a table shipped
  with activity but no ETAs).
- **Started** — HH:MM, from the agent transcript's birth time (see *Gathering state*).
- **ETA** — HH:MM. An actual prediction, not a range dressed as one.
- **Δ** — movement since the last refresh. `—` if unchanged; `+20 ⚠️` if it slipped 20 min;
  `−10` if it pulled in. **This column is the accountability mechanism** — it makes drift
  visible without reading prose.
- **Conf** — 🟢 on track / 🟡 uncertain or open-ended / 🔴 slipping, blocked, or overdue.

### 2. Queued

| # | Item | Blocked on | Est. once started |
|---|---|---|---|

No ETA for queued work — an ETA on something that has not started is a guess about a guess.
Give the estimated *duration* once it starts, and name the blocker precisely (`GPU (lane 1)`,
`quiet tree`, not "later").

### 3. With you

| # | Item | Why it's blocking |
|---|---|---|

Decisions only the user can make. Keep this SHORT and do not re-argue it every refresh —
one line on what it gates. If a decision has sat unanswered for several refreshes, say so
once, plainly, and move on; do not nag on a timer.

### 4. ETA accuracy

The part that must never be skipped or softened.

- **Any lane that finished since the last refresh**: state predicted vs actual, and the miss
  in minutes. Score it even when it lands early — a lane that finishes in half the predicted
  time is the same estimation error as one that doubles.
- **Any lane past its ETA**: own it in the moment, do not wait for it to finish.
- **When wrong, name the mechanism, not the mood.** Not "I was too optimistic" but
  *"I priced a 4-part rebuild at a 1-part rebuild's cost"* — a reusable correction. Then apply
  it to the remaining rows in the SAME table, out loud.
- **Do not silently re-baseline.** If an ETA moves, the Δ column shows it. Quietly replacing a
  blown estimate with a fresh one is the failure this whole report exists to prevent.

## Gathering state

Do this from cheap process facts. **Never read an agent's `.output` transcript** — it is the
full JSONL and it will overflow the context.

```bash
date "+now %H:%M"
# per lane: birth time = started, mtime = last write, and idle seconds = liveness
python3 -c "
import os,time
p='<path to the agent .output symlink target>'
st=os.stat(p)
print(time.strftime('%H:%M',time.localtime(st.st_birthtime)),
      time.strftime('%H:%M',time.localtime(st.st_mtime)),
      int(time.time()-st.st_mtime))"
```

**Idle-seconds alone cannot distinguish "inside a long tool call" from "stopped and
waiting" — check the last event type** (2026-08-02, the user caught two paused lanes I had
reported as healthy). Read only the TAIL of the transcript (seek to the last ~4 KB, parse the
final JSONL line — never read the whole file):

```python
# last line's "type": "assistant" with no tool call in flight => the lane has STOPPED
# and is waiting; a send via SendMessage resumes it with context intact. Kick it, then
# report it as "stopped — kicked", never as running.
```

A lane whose last event is a tool call and whose last write is minutes old is genuinely
*working* on something slow (a bake, a browser gate) — report that as running. A lane can
also die outright on an API/session limit; that is not a code failure and the work is
usually resumable, so say which of the three states it was: working / stopped-kicked / dead.

**Every Running row carries a "Doing" sentence, and it is a JUDGED sentence** (user
requirement 2026-08-02: *"it also helps us catch if the subagent has been stuck for a long
time doing something unexpected — and it's part of your job to recognize when that
happens"*). From the same transcript tail (last ~8 KB, never the whole file), pull the last
tool call's name and its command/description — that is what the lane is doing *right now*.
Then do two things with it:

1. **Compress it into one short sentence in the table** ("baking arch, batch 2 of 4",
   "running transition_test", "diffing donor clips"). "Working" alone is the proxy this
   exists to replace.
2. **Judge it against the lane's brief and phase.** A lane 40 minutes in that is still
   reading context is off-track. A lane whose last five checks show the same command is
   looping. A lane doing something its brief never asked for gets a ⚠️ and a direct
   question via SendMessage — recognizing this is the coordinator's job, not the user's.

**PROCESS CHECKS MUST BE CASE-INSENSITIVE AND MUST EXCLUDE WAITER SHELLS** (2026-08-03,
both halves paid for within an hour):
  * The Blender binary is `/Applications/Blender.app/Contents/MacOS/**B**lender` — capital B —
    and `pgrep -f` is CASE-SENSITIVE. `pgrep -f blender` returns 0 while a bake is mid-render.
    I reported "zero Blender" all evening on that reading and told a lane to re-spawn a bake
    that was ten minutes into its beauty pass; it correctly refused, because re-spawning would
    have recreated a write-race this repo has already paid for. **Always `pgrep -if`.**
  * The converse bit a lane the same hour: its `pgrep -f playthrough_test` matched three
    WAITER SHELLS whose command lines merely contained the string, inventing a 25-minute
    blocker on an idle machine. Exclude `zsh -c`/`sh -c` wrappers, as `cdp.mjs killOrphans`
    already does.
  * The rule this yields is cdp.mjs's law plus its converse: AN INSTRUMENT THAT FINDS NOTHING
    MUST PROVE IT COULD HAVE FOUND SOMETHING — **and one that finds something must prove it
    found the right thing.**
  * A stale artifact mtime NEVER proves a bake is dead: `cine_bake` writes `bg.png` only at
    the very end, so an hours-old plate is normal until the process is gone. Check the
    process, case-insensitively, before concluding.

Practical extraction: walk the tail's JSONL lines backwards to the most recent
`tool_use` (name + first ~120 chars of its `command`/`description`/`prompt` input) or,
failing that, the last assistant text snippet. Record WHEN that event happened — an
activity sentence from 9 minutes ago is a stall indicator, not an activity.

## Estimating

Anchor on **this repo's own measured lane durations**, not on intuition. The 2026-08-02
baseline, from seven completed lanes:

| Lane shape | Measured |
|---|---|
| Read-only search / Explore | ~5 min |
| Runtime-only change + gates | 16–40 min |
| Image-generation batch (12 plates, gated) | 16–40 min |
| Blender rebuild + plate bakes + gates | 63–87 min |

Adjustments that have actually bitten:
- **Plate bakes are serial here.** Measured on both towns: N-wide gives no throughput gain
  over 1-wide once a plate saturates the GPU. Price bakes at ~180 s each, sequentially.
- **Count the parts.** A brief with 3 sub-jobs is not a 1-job lane. Multiply, do not hand-wave.
- **Open-ended visual polish is the softest class** — flag it 🟡 from the start. It has no
  natural stopping point, so it runs until the agent decides it looks right.
- **Gates cost real time** and are mandatory; do not price a lane as if it ends at the build.

## Cadence

Schedule with `CronCreate`, default `*/20 * * * *` (or the user's interval). Two notes:

- Cron jobs are **session-only** and **auto-expire after 7 days** — tell the user when setting
  one up, and re-create it if the session restarts.
- **Refresh on every tick, even when nothing moved.** The user asked for a heartbeat; a silent
  tick is indistinguishable from a broken one. When nothing has changed, say so in one line
  above the table rather than padding it.

Keep the whole report short enough to take in at a glance. If it needs a scrollbar, it has
stopped being a status table.
