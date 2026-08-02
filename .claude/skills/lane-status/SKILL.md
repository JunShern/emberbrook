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

| # | Item | Started | ETA | Δ | Conf |
|---|---|---|---|---|---|

- **Item** — one line: what it is, in the user's vocabulary, not the lane's brief.
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
