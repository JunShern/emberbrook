# scene red-team runs

`tools/scene_redteam.mjs` writes one directory per run. Read
**run-20260731-dellhollow/index.html** — it is the report, and its first section answers
"how well does this work" before it shows a single finding.

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

A finished run can be re-derived from its own stored replies at no API cost:

    node tools/scene_redteam.mjs --calibrate --n 3 --replay 20260731-calib3 --stamp <new>
