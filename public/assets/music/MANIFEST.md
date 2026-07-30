# Emberbrook soundtrack — provenance

Every file in this directory, where it came from, and what it is for. Regenerating
any of it is one command; nothing here was hand-placed.

## Source and licence

**All seven tracks are machine-generated**, by Google's **Lyria 3** through the
Gemini API, using the project's existing `.env` `GEMINI_API_KEY` — the same key
`tools/genart.mjs` uses for the background plates. No third-party music was used,
so there is no external licence to honour, no attribution string to carry in the
credits, and no CC-BY obligation anywhere in the shipping build.

- Generator: `tools/genmusic.mjs` (prompts live in that file's `TRACKS` table, so the
  brief and the thing it produced can never drift apart)
- Models: `lyria-3-pro-preview` (full ~2-minute composed pieces) and
  `lyria-3-clip-preview` (~30 s, the raw material for the two stingers)
- Endpoint: `generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`
- Generated: **2026-07-30**
- Returned format: MP3 (`audio/mpeg`) 192 kbps 44.1 kHz stereo, straight from the API
  — no transcode step, and therefore no ffmpeg dependency (there is no ffmpeg on this
  machine; `afconvert` is used for *analysis* only, never to produce a shipped file)
- Per-file generation record, including the exact prompt and the model's own section
  markers: `<id>.gen.json` beside each track

Usage terms are Google's for Gemini API output. Anything generated with Lyria carries
an inaudible **SynthID** watermark; that is a property of the audio itself and is not
affected by the trimming below.

## Tracks

Loop points and gains are **measured from the audio** by `tools/music_loops.mjs` and
written into `public/game/music.json` — see that tool's header for the method. The
brief is the one-line musical intent the prompt was written to serve.

| id | brief | model | length | size | loop |
|---|---|---|---|---|---|
| `emberbrook` | Gentle home theme — solo flute over warm strings, 3/4, nostalgic and unhurried | pro | 147.1 s | 3.37 MB | 26.2 → 86.2 s |
| `dellhollow` | River-town workaday theme — concertina and plucked strings over a water-wheel lilt | pro | 116.7 s | 2.68 MB | 28.1 → 100.1 s |
| `valley` | Overworld journey theme — open, striding, hopeful; horn and strings over a walking pulse | pro | 149.5 s | 3.43 MB | 58.3 → 130.4 s |
| `interior` | Cozy hearth air — sparse solo harp and clarinet, very soft, room-tone quiet | pro | 170.7 s | 3.91 MB | 25.5 → 115.5 s |
| `battle` | Driving battle theme — minor key, urgent percussion, brass stabs, relentless strings | pro | 155.4 s | 3.56 MB | 33.2 → 97.2 s |
| `victory` | The fanfare — short, bright, triumphant brass flourish resolving to a warm major chord | clip | 12.0 s | 0.28 MB | one-shot |
| `defeat` | Somber sting — descending minor strings, the air going out of the room | clip | 7.0 s | 0.17 MB | one-shot |

Total **17.4 MB** for the whole soundtrack.

`victory` and `defeat` were generated at ~30 s and cut to length on an MP3 frame
boundary — the only edit you can make to an MP3 without decoding and re-encoding it.
The cut is structural, not musical, so `music.js` fades the last 0.9 s / 1.2 s at
playback time rather than baking a fade into the file.

## Reproducing

```sh
node tools/genmusic.mjs --list          # the track table and its briefs
node tools/genmusic.mjs --all           # generate whatever is missing
node tools/genmusic.mjs --force battle  # re-roll one track
node tools/music_loops.mjs              # re-measure loop points + gains into music.json
```

Lyria is not deterministic: `--force` gives a genuinely different take on the same
brief. Re-run `music_loops.mjs` afterwards or the loop points will belong to the
previous recording.

## Notes for whoever replaces these

These are a first soundtrack, not a final one — they establish the shape (which scene
families get which mood, how long a loop body should be, how loud) so the system could
be built and heard against real material. Dropping in composed or licensed music later
means replacing the MP3s, re-running `music_loops.mjs`, and adding the source and
licence for each new file to this table. `music.js` reads all of it from
`public/game/music.json` and knows nothing about where the audio came from.
