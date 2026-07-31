# scene red-team runs

`tools/scene_redteam.mjs` writes one directory per run. Read
**run-20260731-dellhollow2/index.html** — it is the current report, all 16 Dellhollow
plates, and its first section answers "how well does this work" before it shows a single
finding. Section 4 opens with the table saying which plates were judged this round and
which are replayed; read that before you read a finding, because they are not all the same
age and two of them are against a bake the town no longer ships.

Each run directory holds `findings.json` (the whole run, including every checklist item's
ray census), `refuted.json` (what stage 2 threw away — kept so the filter can be checked),
`raw/<shot>.json` (every reply the judge gave, verbatim), `plates/` (the display copies),
and, where a human has read the quotes, `adjudication.json`.

**The judging inputs are not committed.** They are 1344x768 downscales of the shipped
plates and are reproducible from the plate plus this tool; `plates/` holds a smaller
quantised copy for the report. Run with `--keep-inputs` to keep the exact bytes.

Four runs are kept as `raw/` + `findings.json` only, because they are the evidence behind
four fixes recorded in the DAYLOG and in the tool's header, and their pixels are not:

| run | what it is |
|---|---|
| `run-20260731-calib`  | first gate. The context-free sceptic refuted 31 of the checklist's claims for "the object does not exist"; checklist scored 0/5. |
| `run-20260731-calib2` | after the two-sceptic split. Showed N=1 is noise (6 findings vs 2 on the same plate across runs). |
| `run-20260731-calib3` | N=3, clean, 0 errors — **the reply set `run-20260731-dellhollow` is replayed from**. |
| `run-20260731-calib4` | abandoned: the shared GEMINI_API_KEY ran out of prepayment credit mid-run (5 plates returned nothing). Kept as the record of why the sweep stops at 12 plates. |
| `run-20260731-dh2-fresh` | the five plates judged live in the second sweep — gate (recomposed by 96114cc, so its old replies are void) plus the four calib4 never reached. 28 calls, 0 errors. **`run-20260731-dellhollow2` is half replayed from here.** |

Two full reports exist. `run-20260731-dellhollow` is the 12-plate first pass and is kept
because its adjudication is the record of the pink-plank confabulation; `run-20260731-dellhollow2`
supersedes it and covers all 16.

A finished run can be re-derived from its own stored replies at no API cost:

    node tools/scene_redteam.mjs --calibrate --n 3 --replay 20260731-calib3 --stamp <new>

`--replay` takes a LIST, newest first, and resolves each shot from the first run that holds
it. That is how a partly re-swept town becomes ONE report — and every plate records which
run its replies came from, so nothing pretends to be fresher than it is:

    node tools/scene_redteam.mjs --town dellhollow --calibrate --n 3 \
      --replay 20260731-dh2-fresh,20260731-dellhollow \
      --plates <pinned bake> --stamp 20260731-dellhollow2

**Pin the bake, and pin it PER SHOT if the shots disagree.** The `--plates` directory used
for that run is a composite: 14 cameras are the shipped `del-cine` bake, and `shelf-east` /
`shelf-west` are held at the older bake their stored replies were actually made about
(re-rendered at 17:30 and 17:04 the same day; cameras unmoved, pixels not). The tool
compares the pin against the shipped `cine.json` and marks any such shot
**against-superseded-bake** in the report by itself — a critique never gets annotated onto a
picture it was not made about.
