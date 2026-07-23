# EMBERBROOK — Voice Bible

This document governs every line of dialogue in the game. It exists because the shipped
dialogue is over-styled: too many lines perform instead of communicate. The new direction,
from the game's creator: **say the thing plainly first.** Style is a spice, not the meal.
Target reader: a smart teenager enjoying a game — the modern FF/Zelda-localization register.
Adults should never find it babyish; a 14-year-old should never have to read a line twice.

Chapter-rewrite agents: when this document and your own taste disagree, this document wins.
When this document and STORY.md disagree on **lore facts**, STORY.md wins (especially §7's
dialogue registers and the reveal schedule). The lore budget at the top of STORY.md is
binding: one deep fictional system (the flame, its moths, its Warden, its shifting wood);
everything else runs on familiar human themes.

Calibration examples of the rules below applied to real scenes: `docs/dialogue-sample.md`.

---

## PART 1 — GLOBAL RULES

### 1. Plain first

Every line must communicate its content on the first read, at game-reading speed, to a
player who is half-watching the screen.

- **The skim test:** if the player skims the line, do they still get the information? If a
  fact is wrapped in a flourish, unwrap it. Put the fact in the first sentence; flavor, if
  it earns its place, comes second.
- **One idea per box.** A dialogue box carries one thought. If a draft line has a fact AND
  a feeling AND a joke, that is two or three boxes — or a cut.
- **Concrete over abstract.** "The river took him" beats "the water claimed its due."
  Characters talk about lamps, bread, rope, and weather — not about Meaning.
- **Kill the double negative, the inversion, the withheld subject.** "Not that she'd say
  so, of course, though the saying of it..." — no. "She'd never say so." — yes.
- The old register ("It is not clear the chair expects her to") is not banned — it is
  **rationed** (see rule 2) and mostly reassigned to one character (Tally, see his entry).

### 2. The aphorism budget

An aphorism is any line built to be quoted: a proverb, an epigram, a poetic turn, a line
that lands sideways. These were everywhere; now they are rare, which is what makes them work.

- **Budget: ONE per scene.** Place it at the scene's emotional peak. Earn it by making
  everything around it plain — an aphorism in a plain scene is a bell; ten aphorisms are
  traffic noise.
- **Licensed sources only.** Aphorisms come from characters whose lives justify them:
  - **Lake quoting Grandmother** — always flagged as a quote ("Grandmother's saying," "she
    used to say"). This is his grief mechanism; it is load-bearing.
  - **Rowan's rites and proverbs** — tradition register (§7): said with total confidence,
    cheerfully unable to explain. "Light does not die — it is only ever carried" belongs here.
  - **Odessa** — maximum one per chapter, said once, sideways, usually while doing something
    with her hands. (Her Ch. 2 line: "The no was what I owed my own heart. The bag is what
    I owed yours.")
  - **The creed and Order liturgy** — via Tally or ritual moments (the pact, the sigils).
- **Tally is exempt** — over-styling is his characterization (see his entry) — but he may
  never be the *sole* carrier of a plot fact. When Tally explains something the player must
  understand, either his sentence ends plain, or a plain character (Vesper, Maren) restates
  it in one line.
- If two lines in a scene both want to be the aphorism, keep the one at the higher emotional
  peak and write the other one flat. No exceptions, no "but it's so good." Save it in a
  drawer file; the sequel will need lines too.

### 3. Line length and box shape

- **Spoken lines: aim 8–18 words, hard ceiling ~25. Maximum two sentences per box.**
- **Narration cards (`narrate`): ceiling ~30 words, two sentences.** One image per card. If
  a narration wants three images, that's two cards — or one image and trust the art.
- **A long speech is a sequence of short boxes**, each advancing one step. Never one wall.
- Cut any line whose only job is style. A scene that loses 20% of its lines and none of its
  beats got better.
- Interruptions (`—`), trailing (`…`), and beat-pauses (`{ wait }`) are cheap and good;
  subordinate clauses are expensive and usually bad.

### 4. Reading level and register

- **Modern localization English.** Contractions everywhere. No "whom," no "'tis," no
  inverted syntax ("never have I seen") — except inside Tally's and Rowan's licensed
  registers, and even there, sparingly.
- **Never babyish.** No simplified emotions, no telling the player how to feel, no
  exclamation-point padding. Teenagers detect condescension instantly; the tone is
  *clear*, not *small*. Dark beats stay dark — the Hush is frightening; write it
  frightening and plain.
- Mild regionalisms are voice tools (Finn's dropped g's, Maren's river-slang, Poppy's
  "love") — one or two markers per character, applied consistently, never phonetic soup.
  If a line needs a glossary, rewrite it.

### 5. The three channels: spoken, `system`, `narrate`

- **Spoken lines** are the character talking. Everything above applies at full strength.
- **`system` boxes** (present tense, in the dialogue box) are stage directions and examine
  text. Deadpan, observational, light wit allowed — this is Mochi's comedy channel and the
  place for "what the camera can't show." Still one idea per box. The current build uses
  system boxes as short essays; stop that. If a system box explains a relationship, cut it
  to the single physical action that shows it ("Odessa refills Maren's bowl before Maren
  notices it's empty. That is the answer.").
- **`narrate` cards** (past tense, cinematic) open and close movements. They may be the
  most written of the three channels — this is where the game's literary voice survives —
  but rule 3's ceiling applies, and even here: fact first, music second.
- **Examine text** (interact POIs) follows the `system` rules. It is optional content, so
  wit is welcome — but the first sentence still says what the thing *is*.

### 6. Parenthetical (internal) lines

The `(…)` lines are a character thinking. Current build abuses them as essays and
exposition dumps. New rules:

- **One thought. Two short sentences, maximum.**
- **Never the sole carrier of a plot fact.** If the player must know it, someone says it
  out loud. Internal lines carry *feeling about* facts, not the facts.
- **Ration: about three per character per scene.** More than that and the game becomes a
  novel with a controller.
- They are the only place Vesper and Lake get to be unguarded. Protect that: an internal
  line can be softer, sadder, or more honest than the character would ever speak. That
  contrast is the whole point of the mechanic.
- Mochi has no internal lines, ever. Cats are observed, never narrated from inside.

### 7. Lore vocabulary — must survive the rewrite

Rewriting for plainness must NOT strip the lore lexicon. These terms are canon and appear
in dialogue exactly as spelled (see STORY.md §7 for who may know what, when):

> the Heartlight · the Kindling · the Kindling Hour · Emberwake · a **telling** / "make a
> telling" / "tell it to the flame" · "bring a memory worth keeping" · keeper / keeping /
> "carrying is claiming" · "mean it" / a meant flame · the rounds / "closing the ring" ·
> "dark lamp, dull street" · moths · the Hush · "light does not die — it is only ever
> carried" · Flamebearer / Waykeeper / the walking two · the Order of Lamplighters · the
> Whisperwood · "keeper keeps his own" / "stand outside the kept" · the Last Spark

**How it's spoken — the three registers (STORY.md §7, condensed):**
1. **Plain knowledge** — villagers say it like weather: warm, proud, matter-of-fact, never
   mysterious. The Kindling Hour explanation is the model: *you bring your best memory and
   tell it to the flame; you keep the memory; the flame keeps the warmth of it and shines
   it back on everyone in the lamplight, forever.* Every rewrite of a lore explanation must
   preserve all four facts of that sentence (yearly telling · teller keeps the memory ·
   flame keeps the felt part · radiates back through the lamps to everyone in the light).
2. **Tradition** — proverbs said with confidence and no ability to explain ("it wasn't hers
   to put out," "that road was meant to be walked by two"). Characters are *cheerfully
   unable* to explain these. Do not have anyone explain them.
3. **Mystery** — the reveal schedule is law. Nobody hints early. No moth-explanations
   before Ch. 7, no hush-anatomy language about Vesper's parents before Ch. 5, the Hush
   plays as the first such event in history. Plainness applies to what characters *know*,
   not to what the writers know.

### 8. Emphasis and punctuation conventions

- CAPS for emphasis: keep the house style, **maximum one capped word per line**, and only
  where a voice actor would actually punch it.
- Em-dash for interruption and self-correction; ellipsis for hesitation. Both are voice
  tools — Maren gets many dashes, Odessa gets almost none.
- Stage tags like `(quiet)`, `(low)`, `(whisper)` stay; they're cheap and effective.
- Portrait moods (`:happy`, `:grave`, `:hollow`…) do emotional labor — a line doesn't need
  to *say* the feeling the portrait shows.

### 9. The distinctness test

Cover the nameplate. If a reader who has played one chapter cannot name the speaker of a
line, the line is in nobody's voice — rewrite it. Run this on every scene before delivery.

Quick check — who says each of these? (Answers below.)

1. "Half a loaf's a penny. The cat's credit is good."
2. "Noted. Filed under: things I refuse to call impossible twice in one week."
3. "Wash. Basin's by the door."
4. "It's not sad. It's bookkeeping."
5. "That is LAW on Emberwake, ask anyone."
6. "The books say — oh, oh no, the books SAY this—"

(Sorrel, Vesper, Odessa, Maren, Poppy/Rowan register, Tally.) Note that #5 is ambiguous
between Poppy and Rowan — hospitality-law is a shared Emberbrook value. That's acceptable
for a *value*; it would not be acceptable for a *rhythm*.

---

## PART 2 — THE VOICES

Format per entry: **Voice** (rhythm, vocabulary, sentence shape) · **Tics** (things they
actually repeat) · **Never** · three example lines (plain / emotional / funny). Examples
are new lines in the target register, safe to reuse.

---

### VESPER — traveling mapmaker, co-lead

**Voice.** Precise, quick, dry. Thinks in measurements, lists, and records; speaks in
short declaratives and colon-lists ("One road. Two exits. No name."). Corrects imprecision
reflexively — including her own ("Nine—" "Ten." "…Ten."). Deflects every personal question
with professional vocabulary: feelings become "entries," her past is "under survey," grief
is "a filing problem." The deflection is armor, and the player should be able to see
through it about one scene before she does. Allergic to mysticism — she will not say
"magic," "destiny," or "meant to be" without sarcasm around it.

**Tics.**
- "Noted." / "Filed." / "For the record—" / "New page." (notebook liturgy)
- Numbers things aloud: drawings, days, honeybuns (dishonestly — always undercounts).
- Writes mid-catastrophe; announces it: "I'm writing that down."

**Never.** Gushes. Says "I feel." Uses two adjectives where a measurement would do. Admits
the correct honeybun count. Calls the dreams anything but "the drawings" or "the mail."

**Examples.**
- *Plain:* "Two roads north. The high one's broken. So it's the river or nothing."
- *Emotional:* "I can draw the hill from memory. I just can't feel anything when I do.
  …That's the entry. There's no more to it."
- *Funny:* "I had one honeybun. The record will show one honeybun. Stop looking at the crumbs."

---

### LAKE — the last lamplighter of Emberbrook, co-lead

**Voice.** Plain and warm. Few words, all of them load-bearing. His superpower is naming
the obvious thing everyone else is talking around ("That's what's wrong with it." "You're
scared. Me too."). Short sentences, no rhetoric, drops the subject when he can ("On duty,
Poppy."). Apologizes — to people, and occasionally to lamps. His grandmother's sayings are
his one styled register: always flagged as quotes, always at real weight (rule 2 — this is
how he carries a grief he was never allowed to give away).

**Tics.**
- "Grandmother used to say—" / "Her rule." (aphorism license — flagged, rationed)
- Names people and their one true detail: "You're Poppy. You bake."
- Understates his own state: "I'll manage." "It's a good rattle."

**Never.** Speechifies. Uses sarcasm *at* someone. Explains the flame mystically —
he talks about the job the way a plumber talks about pipes. Claims certainty he doesn't
have (his doubt about the vow is arc-load-bearing through Ch. 7).

**Examples.**
- *Plain:* "Three lamps before dark. Pond lane first — that's the order. It matters."
- *Emotional:* "She died a year ago tonight. I do the rounds anyway. It's the only part of
  her I get to keep doing."
- *Funny:* "The lamp doesn't need the apology. I know that. I do it anyway."

---

### MAREN — 17, lock-keeper's daughter, pilot

**Voice.** Fast, loud, run-on. River-slang and lock-jargon as first language (fend, sculls,
tailwater, half-gate). Self-interrupts with dashes mid-sentence — her mouth runs ahead of
her plan and has to double back ("Da pulled it out — well, GRAND-da — one of them—"). On
water: precise, clipped, commanding — the run-on stops dead when she's piloting. Off water:
awkward, covers feelings with volume or a subject change. Tallies everything; counts are
sacred ("It's not sad. It's bookkeeping."). Rare `(quiet)` lines land hard because loud is
her default.

**Tics.**
- "Ma says—" / arguing with the absent Odessa mid-sentence.
- Count corrections and count pride: "Nine dives—" "Ten." "…Ten. The point stands!"
- "Mind the forty-first step, it lies." — her hospitality.

**Never.** Formal address. Long words where a shout works. Says "afraid" (the whole town
doesn't — house style of Dellhollow). Admits she's crying ("absolutely not crying").

**Examples.**
- *Plain:* "Flume drops a mile through the cliff. It wants water, a boat, and a pilot.
  That's me. That's the plan."
- *Emotional:* "(quiet) Beat your time, Da. You'd have hated that. …You'd have loved that."
- *Funny:* "I'm seventeen, which is grown. Ask anyone. Don't ask my mother."

---

### ODESSA — guildmother of the Dellhollow locks

**Voice.** Short imperatives. Never explains, never repeats, never hurries. Sentences are
rulings: subject, verb, done ("Wash. Basin's by the door."). Warmth lives entirely in
actions — refilled bowls, packed bags, a winch taken up — and the *narration* is allowed to
notice this; she is not. One-word and zero-word replies are in-voice ("Mm."). Her single
aphorism per chapter (rule 2) comes out sideways, usually while her hands are busy, and is
never remarked on afterward.

**Tics.**
- "Mind the—" (tide, beam, stair): care disguised as instruction.
- Correcting counts downward-into-truth: "Ten." (She always knows the real number.)
- Answering a question with a ruling: "My ruling stands as posted."

**Never.** Says "I love you," "I'm worried," "I'm proud" — or any feeling in first person.
Explains a decision. Raises her voice. Uses two sentences where one will rule.

**Examples.**
- *Plain:* "No boat works Lock Five while she's below. That's the ruling. It's posted."
- *Emotional:* "The no was what I owed my own heart. The bag is what I owed yours."
- *Funny:* "Sit or stir, guest. Standing in the middle of a kitchen is for weathervanes."

---

### ROWAN — village elder and ledger-keeper of Emberbrook

**Voice.** Old-fashioned courtesy, worn soft: "my dear," "child," "boy" — affection, not
condescension. Funny on purpose, usually at his own expense ("In charge! Ha! I keep the
ledger; the village keeps itself."). Ledger and bookkeeping metaphors are his native
imagery ("That is not boasting. It is bookkeeping. I checked."). Licensed carrier of the
tradition register (rule 2): he recites the old rites word-perfect and cannot explain one
of them, and says so cheerfully. **Post-Hush:** identical grammar, hollowed content — write
dissociation, never failed recall ("Every word of it true, and not one of them mine.").
His flat Ch. 3 letter is the same voice with the jokes surgically absent; that absence IS
the horror. Never write post-Hush Rowan forgetting a fact.

**Tics.**
- "…I checked." / ledger-talk for everything, including love.
- "Ha!" — a genuine bark, mid-sentence, at anything that delights him.
- Deflecting authority: "I keep the ledger; the village keeps itself."

**Never.** Pomposity he doesn't immediately puncture. Mysticism — rites are furniture to
him, comfortable and unexamined. Post-Hush: "I can't remember" (forbidden — he remembers
everything and feels none of it).

**Examples.**
- *Plain:* "Nobody opens the Old Gate, child. It hasn't a key. It has rules — and they're
  lamplighter rules, so ask him, not me."
- *Emotional:* "I wrote this page. Every line of it. And tonight I read it like the
  minutes of somebody else's village."
- *Funny:* "Guests eat first — that is LAW on Emberwake. I'd cite the statute, but the
  statute is the baker, and she's holding buns."

---

### POPPY — baker of Emberbrook

**Voice.** Bossy kitchen warmth. Feeding people is legislation ("That's not kindness,
that's LAW."). Short, loud, generous bursts; commands as endearments ("Eat two."); calls
everyone "love." Explains lore in kitchen terms — the Kindling Hour comes out of her sounding
like a recipe, which is exactly right for the plain-knowledge register: she's the best lore
explainer in the village *because* she makes it sound simple. **Post-Hush:** rebuilds
herself from a row of words — "Honeybuns. Poppy. Thumb." — the same command-voice aimed at
herself, which should hurt.

**Tics.**
- "…love." / "Eat two."
- Feeding as law: "guests eat first," half-a-bun hostage-taking.
- The thumb: burns it on the first tray every morning, swears she won't tomorrow.

**Never.** Lets someone leave hungry. Talks abstractly — everything is bread, thumbs,
sundown, soup pots. Whispers.

**Examples.**
- *Plain:* "Kindling Hour's at moonrise, love. Bring your best memory of the year — you'll
  tell it to the flame. That's the whole of it."
- *Emotional:* "Honeybuns. Poppy. Thumb. I'm keeping the words in a row where I can see them."
- *Funny:* "She says she's here to map the forest. Did you hear her? Map the forest. Eat two."

---

### MARA — Pip's mother

**Voice.** Steady, unsentimental warmth. Plain full sentences about exactly what matters,
no pet names, no fuss ("He'll sleep where he falls, and I'll carry him home like every
year."). The emotional anchor of the Hush's cruelty precisely because her baseline is so
level — **post-Hush her grammar doesn't change, only the moorings go** ("I believe every
word. It lands like a fact about a stranger."). Write her post-Hush lines with full
courtesy and zero warmth; the gap does the work.

**Tics.**
- "Pip, love—" (her one endearment, spent only on him).
- Weather-and-winters practicality: "Nights like this are what winters are for."

**Never.** Gushes or panics. Post-Hush: cries theatrically, forgets facts — her horror is
administrative calm about her own son.

**Examples.**
- *Plain:* "He's been up since dawn. He'll fall asleep mid-sentence and deny it mid-fall."
- *Emotional:* "I know he's mine. I can say it. It should weigh something when I say it,
  and it doesn't."
- *Funny:* "Pip, love, stop orbiting the nice stranger. She is not a moon."

---

### FINN — fisherman of Emberbrook

**Voice.** Laconic. Prefers fish to festivals and says so. Dropped g's ("swimmin',
circlin'") — one marker, used consistently, never thicker. Delivers alarming observations
completely flat; understatement is his whole instrument ("Didn't think so either, this
morning."). Sentences get shorter as things get stranger.

**Tics.**
- Flat escalation: "One big circle. All of 'em. Slow."
- "Funny what stays." — post-Hush; hands-know-the-knots pragmatism.

**Never.** Exclaims. Elaborates. Attends a festival willingly. Uses a metaphor when a fish
fact is available.

**Examples.**
- *Plain:* "Pond's wrong tonight. Fish are circlin'. They don't do that."
- *Emotional:* "I can say my name. It just isn't mine anymore. Hands still know the knots,
  though. Funny what stays."
- *Funny:* "Festival's up there. Fish are down here. I know which conversation I prefer."

---

### PIP — seven years old

**Voice.** Seven. Short sentences, zero subordinate clauses, questions in volleys ("Are
you a REAL mapmaker? Have you been EVERYWHERE?"). One capped word per line minimum-feels —
but obey rule 8; pick the word a seven-year-old would shout. Total conviction; instant
canon-building ("She's been to the moon."). Post-Hush he is the bravest character in the
game and should read that way: scared, and doing it anyway ("I'm teaching her me again.").

**Tics.**
- The good stick. There is one. It is important.
- "Renn says—" (offscreen kid authority for all folklore, which is accurate folklore).
- Declares things settled: "She's been to the moon."

**Never.** Irony. Adult vocabulary. More than one idea per sentence. Whimsy-cute
misspellings or babytalk — he's seven, not four.

**Examples.**
- *Plain:* "Renn says you can SEE the memories go in. I'm staying awake to check."
- *Emotional:* "You held my hand. Tonight. You said I'd remember tonight forever."
- *Funny:* "I have a stick. It's a good stick. You can hold it for one minute."

---

### TALLY — last friar of the Lanternstead

**Voice.** THE exception, on purpose: Tally keeps the old over-styled register as
characterization. Bookish over-explainer — cites volumes, rites, and observances nobody
asked about; corrects his own citations mid-sentence ("it's 'who KEEPS the dead road,' and
then YOU say—"); formal address for everyone (madam, Flamebearer, Waykeeper); names
everything liturgically (Sister Kettle, Brother Frog, the necklace). His flourishes are a
lonely man's lifetime of rehearsal finally getting an audience — play it warm, never smug.
**The joke only works against a plain background**, so the rules on everyone else make
Tally funnier for free. Constraint (rule 2): he never solely carries a plot fact — end his
speech plain, or have Vesper/Maren restate it in one line.

**Tics.**
- Citations and counts: "Volume Nine is clear—", "I checked. I checked twice."
- Formal titles for everyone, including animals and kitchenware.
- Self-interrupting corrections of his own liturgy.

**Never.** Brief when excited. Cynical. Wrong about doctrine (his facts are always good —
that's the other half of the joke). Condescending — he reveres everyone.

**Examples.**
- *Plain (for Tally):* "Harrowdel. Three days north. Their lamps still answer — the last
  on this road that do."
- *Emotional:* "You're real. The office is real. I have the whole liturgy and nobody ever
  came."
- *Funny:* "I'll fetch the kettle. Not the good kettle. The WALKING kettle. We have
  DOCTRINE about kettles—"

---

### HOBB — barge captain, stuck in the Dellhollow queue

**Voice.** Professional griper with a soft center. Grumbles in loops — returns to the
pumpkins the way a tongue returns to a sore tooth ("Forty ton. In elegant rows."). Quotes
his wife as an ongoing offstage argument ("Nineteen days of my wife saying pie."). Catches
himself when the grumbling crosses into unkindness and reverses, fully ("Don't be sorry,
be useful— no. No, forgive me."). Big feelings arrive as logistics ("Who's minding the
ovens? Somebody has to mind the ovens.").

**Tics.**
- The pumpkins. Always the pumpkins. Count and condition.
- "My wife says—" / "My cousins downriver won't believe half of it."
- Self-correcting mid-grumble.

**Never.** Actual malice. Optimism before lunch. Brevity about cargo.

**Examples.**
- *Plain:* "Nineteen days in this queue. The queue has bunting now. We've named the seagulls."
- *Emotional:* "A whole village gone flat in a night. Terrible thing. …Somebody has to mind
  the ovens. Somebody always has to mind the ovens."
- *Funny:* "'Cut them for pie,' she says. Madam, there is no fair for a November pumpkin."

---

### PELL — Dellhollow's night-watchman

**Voice.** Deadpan grievance-comedy. Precise about his trade (wicks, oil, ladders) and
militant about its dignity ("I'd thank the town to remember who carries the ladder.").
Runs a standing joke about shifts ("It is presently day, which is why I'm holding a
wick-knife and a grudge."). When he reports something genuinely strange, the deadpan stays
but the sentences shorten — that contrast is how the player knows to sit up ("Marsh-gas
doesn't stop to look back at you.").

**Tics.**
- The day-shift grudge, in every daytime line.
- Wick-and-oil professional pride: "oil goes in, light comes out."
- Understated dread: reporting the impossible in the same tone as a rota complaint.

**Never.** Panics. Embellishes a report — he is a good witness and it bothers him. Lets
ceremony near his job ("No ceremony to it, friend").

**Examples.**
- *Plain:* "Every wick, every noon, so they burn every night. That's the whole trade."
- *Emotional:* "It stopped when I raised my lamp. A long stop. Then it went on north, and
  I found I'd sat down on the wall without deciding to."
- *Funny:* "Sleep's for the day shift. Which is now. Which is the grudge."

---

### SORREL — the bread-window on the stair-street

**Voice.** Transactional warmth: everything is priced, and the pricing is the affection
("Half-loaf's a penny, whole loaf's a penny and a look at your cat."). Plural endearments
("loves"). Market-stall rhythm — short clauses strung with commas, patter-fast. Trades in
small confidences ("don't tell the gulls," "don't tell the harbormistress which way I'm
praying").

**Tics.**
- Prices everything, including non-goods (a look at your cat; a secret).
- "Don't tell—" (harmless conspiracies).

**Never.** Gives something away without naming a price, even a joke price. Speaks slowly.

**Examples.**
- *Plain:* "Bread's fresh, drip-line's not. Mind your head, loves."
- *Emotional:* "Nineteen days of stuck boats buying my bread. Best worst thing ever to
  happen to this town."
- *Funny:* "The heel's for the cat. Paid in full. Don't tell the gulls."

---

### CREEL — old rope-splicer on the stairs

**Voice.** Slow, grounded, four-hundred-years-of-town perspective. Everything routes
through rope, timber, and stairs — his proverbs are trade observations, not poetry, which
keeps him inside the aphorism budget ("Rope tells you before it goes. So do most things,
if you're the sort that listens."). Long memory, short sentences.

**Tics.**
- Rope and timber as the measure of all things, people included.
- "…since I was the boy with the gulls — and there's always a boy with the gulls."

**Never.** Hurries. Abstracts — if it can't be spliced, hauled, or trodden on, he
approaches it via something that can.

**Examples.**
- *Plain:* "Bridges are sound. I splice what they hang from. I'd know first."
- *Emotional:* "Four hundred years of stairs. The town's knees give out before the timber does."
- *Funny:* "Mind your feet going down. Coming up, mind everything else."

---

### NIB — kid on the stairs, officer of gulls

**Voice.** Blurt-truth. No filter between observation and mouth ("You're littler than the
quay said."). Proper-noun world-building at speed — every gull named and ranked. Kid logic
stated as settled law ("She knows anyway. She knows everything."). Distinct from Pip: Nib
is street-wise and appraising where Pip is orbit-and-wonder; Nib evaluates you, Pip
adopts you.

**Tics.**
- Gull administration: "That one's Bailiff, that one's Soup."
- "Don't TELL the harbormistress." (Everyone knows. Including the harbormistress.)

**Never.** Deference. Sentiment. Doubt about gull-related facts.

**Examples.**
- *Plain:* "Lock Five's shut. Eel's in it. Everyone knows. Where've YOU been?"
- *Emotional:* "Soup! SOUP! …He knows his name. He just doesn't respect it."
- *Funny:* "Are you the flame people? You're littler than the quay said."

---

### THE STRANGER / THE WARDEN OF THE KINDLING

**Voice — current chapters (1–3): none.** He does not speak. He is written entirely in
narration, and the narration follows canon rule 6: owed sympathy at every appearance,
never sneered at. His verbs are unhurried and formal: he *stands*, he *regards*, he
*bows*. The bow is his sentence — deep, slow, courteous, aimed at the carried flame and
never at its carrier. Keep narration about him spare and factual; the wrongness ("pale,
pale blue," "did not bob") is stated once per sighting, plainly, and not decorated.

**Voice — when he speaks (Ch. 6+), for future reference.** Short, complete sentences. No
contractions — the only character denied them; three centuries alone with liturgy. Law
vocabulary as native tongue: *loan, claim, recall, kept, owed, register.* Grief without
apology; courtesy without warmth ("the way a debt collector is courteous"). He answers
exactly the question asked. He never threatens, never mocks, never raises his voice — and
the script never scores points off him.

**Never.** Menace for menace's sake. Archaism-as-costume ("thou," "shalt"). Explaining
himself before the reveal chapters. Being wrong about the law — his facts are perfect;
it's the law that's obsolete.

**Examples (Ch. 6+ register).**
- *Plain:* "The light was unclaimed for a year. I read the register. I carried it home."
- *Emotional:* "I have grieved at every door. It has never once stopped me. That is what
  keeping is."
- *(He is never funny. The comedy near him belongs to Mochi's hiss.)*

---

### MOCHI — the cat

**Voice.** "Mrrp." That is the entire spoken lexicon, in four inflections: `Mrrp.`
(statement), `Mrrp?` (query), `Mrrrrp.` (emphasis/complaint), and `Hhhhhhhh.` — the hiss,
**reserved exclusively for the Warden**, currently used twice, and its scarcity is canon
(Lake counts them). Do not spend the hiss on anything else.

All other Mochi content lives in **system boxes**: present-tense, deadpan, bureaucratic
framing — Mochi *negotiates, inspects, approves, files position papers, reconsiders the
terms of his employment*. The comedy is the gap between cat behavior and official
language. Never translate his thoughts ("Mochi thinks…" is banned); report observable
conduct and let the officialese imply the rest. He is never cutesy, never "kitty," and
never wrong — his instincts are professional equipment (moth-warden, Warden-detector,
weather-vane for keeping-fire).

**Examples.**
- *Plain:* `['mochi', 'Mrrp.']`
- *Emotional:* `['system', '(Mochi leans, very briefly, against Lake's boot. Then pretends he didn't.)']`
- *Funny:* `['system', '(Mochi boards the satchel facing backward, as if the whole arrangement were his own idea and everyone else were late.)']`

---

### SYSTEM / NARRATOR

**Voice.** Two channels, one narrator (see rule 5).

- **`narrate` cards** — past tense, cinematic, the game's literary signature. Allowed one
  good image per card; fact first. This channel keeps the felt-memory vocabulary alive in
  prose ("the light of Emberbrook — three hundred years of it — stood up and left").
- **`system` boxes** — present tense, deadpan stage directions and examine text. Dry wit
  welcome; essays banned. When a system box wants to explain a relationship, cut to the
  one action that shows it and stop ("That, apparently, is the sentence." is the model —
  and note it's seven words).

**Tics.** Deadpan escalation ("It was wonderful."); the polite refusal to explain a joke;
letting objects have quiet opinions (a beam nobody will ever clean) — at most once per scene.

**Never.** Tells the player how to feel. Uses second person outside UI text. Breaks the
reveal schedule — the narrator knows everything and says only what this chapter may say.
Mocks a character the script owes sympathy (the Warden, post-Hush villagers).

**Examples.**
- *Plain (narrate):* "They reached the Lanternstead at dusk, and someone inside it was
  singing."
- *Emotional (narrate):* "It did not happen slowly. Between one heartbeat and the next,
  the light of Emberbrook stood up and left."
- *Funny (system):* "(The bucket arrives. It contains water, and one entirely unhurried
  frog.)"

---

## PART 3 — CHEAT SHEET

| Character | Voice in three words | Load-bearing tic | Absolutely never |
|---|---|---|---|
| Vesper | precise, dry, deflecting | "Noted." / "New page." | says "I feel" |
| Lake | plain, warm, few words | "Grandmother used to say—" | speechifies |
| Maren | fast, loud, self-interrupting | count corrections; "Ma says—" | says "afraid" |
| Odessa | imperatives, no explanations | "Mind the—"; "Mm." | feelings in first person |
| Rowan | courteous, funny, ledger-brained | "…I checked." | post-Hush "can't remember" |
| Poppy | bossy kitchen law | "Eat two." / "…love" | lets you leave hungry |
| Mara | steady, unsentimental | level tone at any cost | theatrical grief |
| Finn | laconic, flat, fish-first | understated escalation | exclaims |
| Pip | seven, certain, loud | the good stick; "Renn says—" | irony |
| Tally | liturgical over-explainer (licensed) | "I checked twice."; titles for all | sole carrier of plot facts |
| Hobb | looping griper, soft center | the pumpkins; "my wife says—" | actual malice |
| Pell | deadpan grievance | the day-shift grudge | embellishing a report |
| Sorrel | patter, priced warmth | prices everything | giving without a price |
| Creel | slow, rope-measured | rope tells you first | hurrying |
| Nib | blurt-truth, gull registry | "don't TELL the harbormistress" | deference |
| Warden | silent; later: law, no contractions | the bow | being sneered at |
| Mochi | "Mrrp." + officialese system lines | the hiss (Warden only) | narrated thoughts |
| Narrator | fact first, one image | deadpan escalation | telling player how to feel |

**Final check for every delivered scene:** (1) skim test passes on every line · (2) one
aphorism, at the peak, from a licensed source · (3) no box over ceiling · (4) nameplate
test passes · (5) lore terms intact, registers per STORY.md §7 · (6) reveal schedule
unbroken.

---

# PART TWO — Density & pacing rules (director-approved, 2026-07-23)

The first rewrite fixed sentences; playtesting showed the INFORMATION
ARCHITECTURE still overloads the player ("every line tries to reveal some
hidden backstory at once and I need to pause at every line"). These rules
govern the second pass and all future dialogue. Where they conflict with
Part One, these win.

## Rule D1 — Fact budget per SCENE
One new strangeness or lore fact per scene, stated plainly at the moment a
character notices it. All other mysteries wait for a scene where someone can
ask about them out loud. Facts may be RELOCATED to a later natural ask-point
within the same chapter (respecting STORY.md's reveal schedule); deleting a
canon fact is not allowed, deferring it is encouraged.

## Rule D2 — Rest lines (20–30% of boxes)
A fifth to a third of every scene's boxes must carry ZERO new information:
greetings, logistics, walking, food, plain reactions ("You're kidding."),
small kindnesses. These are not filler — they are the white space that makes
loaded lines land. After any loaded box, prefer at least one light box.

## Rule D3 — Emotion in the clear
Each principal states a real feeling plainly at least once per scene
("I don't like this road." / "I'm glad you're here."). Wit may FOLLOW a
plain feeling; it may not replace it. Persona-encrypted emotion ("There is
always an explanation") is allowed only after the plain statement has
already appeared in the scene.

## Rule D4 — Externalized confusion
The player's current question must be voiced OUT LOUD by a character —
asked to someone who answers or visibly dodges. Internal parentheticals may
color a mystery but may never be its sole carrier.

## Rule D5 — Foreshadowing is an unremarked object
Plant payoffs as innocent concrete objects and events, never as significant
phrasing. No riddle banners, no narrator winks ("somebody has recently
brushed the moss from its eyes"), no lines that exist only to be understood
later. If a detail must be noticed twice, let the SECOND occurrence do the
noticing.

## Calibration Sample C — the waystone beat (approved verbatim)
[vesper] (A waystone. Good — the road's a real road, then.)
[vesper] (…Wait.)
[vesper] (I've drawn this stone. This exact stone — the face, the crack through its chin. It's in my sketchbook right now.)
[vesper] (And I have never been here in my life.)
[mochi] Mrrp.
[vesper] GAH— …a cat. Hello. Don't sneak up on people in haunted forests.
[mochi] Mrrp.
[vesper] There are lights up the road. Come on. If anyone can explain my sketchbook, it's whoever lives here.

One clean impossibility; the sleep-drawing, the eleven days, and the
dream-mail all defer to later scenes where someone asks. This is the
density target for every scene in the game.
