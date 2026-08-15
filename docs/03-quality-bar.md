# The quality bar

**A technically-correct first render is a draft, never the deliverable.** It nails structure,
timing and beat-matching, which is necessary and not sufficient. Budget three review rounds.
This is the job, not scope creep.

Two halves to the bar. The first is **measured**: resolution, bitrate, held time, void area,
colour against the master. Those are arithmetic and there is no argument about them. The second is
the **rejection taxonomy**: the owner will not itemise a fix list that solves the problem, they
describe a feeling, and almost every rejection this system has seen falls into one of five
classes, each with a known fix that is structural rather than cosmetic. Diagnosing the class
correctly is most of the work.

Passing the measured half is not passing the bar. Failing it is failing the bar without a
conversation.

---

## Class 1: "boring", "text based", "the animations are basic"

**This is a scene-form rejection, not a typography note.**

The tell: every scene is a card with words in it. The fix is not a bigger font, a livelier
entrance or more decoration. It is to find the **physical event** each line describes and animate
that.

Worked examples from this system:

| The line | The wrong scene | The scene that shipped |
|---|---|---|
| "one prompt that fixes it" | A card with the prompt text | A glass ampoule filling with amber serum, five etched ticks lighting as the meniscus passes them |
| "it verifies" | A four-item checklist | A capsule descending a track through four gates that close on it, one per spoken word |
| "confidence score" | A number in a box | A 240 degree dial with a red sector and a needle that hunts before it stalls |
| "it retries" | A retry label | The rejected pod physically ejecting and travelling a dashed return path back into the dial |
| "Claude has the memory of a goldfish" | A claim pill on the face | Brain pops out of a dashed head, goldfish swims in, a CONTEXT REMEMBERED meter drains 100 to 0 |

**Test for the next build: if a beat can only be expressed as a sentence in a box, it is the
wrong beat.**

Two supporting rules:

- **Characters doing an activity beat icons with labels.** A personified prop performing the
  verb outperforms an abstract metaphor every time. When the VO names a physical verb, the panel
  must perform that verb on the word.
- **Synchronised is not simultaneous.** A card fading up while a name is spoken is merely
  simultaneous. Two distinct moves, each tied to a specific word (the name opens the row, the
  predicate lands the stamp), is what "sync up with what we're saying" actually asks for.

---

## Class 2: "cheap"

**Count your carrier shapes before you fix any individual scene.**

The diagnostic case: a four-minute film was rejected as "very cheap" with exactly one positive,
"the globe animations are nice." The 3D field was the only device in the film that was not a
rounded rectangle. Record card, buyer tiles, action rows, module slabs, ledger tiles, price
carriages, router tokens, reason cards and the coupon card were all the same primitive with the
same `y:+20` fade entrance.

The fix is to **replace the carrier, not the content**. And once you strip the box everywhere,
the one box you keep becomes a device: the coupon was the only card left in the rebuild, which
is why the payoff read as a payoff.

Related: at 4K, **the working type sizes are what read as cheap, not the display sizes.** Labels
at 32px and body at 56px in a 3840-wide frame are proportionally a 16px label on a 1920 frame.
A 1.3x lift on everything below headline level changed the read more than any scene rebuild.
Check working sizes as a fraction of frame width, not against a web instinct.

---

## Class 3: "not premium", "not professional", "looks vibecoded"

**Treatment before hue.** Two palettes were rejected in a row before this landed: monochrome read
as dead, hot crimson-to-orange read as a gaming thumbnail. Half the unprofessional signal was
palette-independent:

- **No gradient-filled display type.** A `background-clip:text` ramp on a large number is the
  single biggest tell.
- **No glow shadows on type.** `text-shadow: 0 0 44px` and `drop-shadow(0 0 70px)` belong on a
  light source, not a numeral. A lab instrument may glow on its own hardware; letterforms may not.
- **One background wash, not three.** Three coloured radials is a gamer-desk look. One low-opacity
  falloff plus a dot grid as a banding guard.
- **Hairlines, not coloured borders.** `1px rgba(255,250,240,.09)` beats a 2px tinted border with
  a 40px glow.
- **No RGB chromatic splits** on a hook headline. State the line.
- **Reserve the accent by counting where it appears.** The rule that made a muted gold work: the
  accent marks the subject, every rival and every label is neutral. About seven elements across
  34 seconds. An accent used everywhere is a second background colour.

**But a saturated accent is mandatory.** Theme-per-subject picks the family; the reel still needs
one saturated colour carrying every number, bar and border. A brand-faithful monochrome build was
technically correct, passed every gate, and was rejected on sight: it read as two different
videos spliced together next to a warm A-roll. If the subject's brand will not supply an accent,
borrow one from the story, and **colour-code the conflict** so the palette carries the argument.

**And motion and colour are substitutes, not additions.** Once the palette carries the energy,
strip the decorative motion rather than layering both.

**Grammar and theme are independent axes.** "It feels dead" is a grammar problem; "it feels
cheap" is a theme problem. Never trade one for the other, and never assume a rejection of one is
a rejection of both. Ask which.

---

## Class 4: "text on my face", "too weird, coming on the face"

**This is a layout-mode failure, not a nudge.** Patching instances one at a time generates more.

The structural rule:

> A beat is either **CARD mode** (the A-roll owns its rect, graphics own the rest, zero overlap)
> or **FULL-BLEED mode** (at most one self-grounded element in measured clear space).
> **There is no third mode.**

Supporting facts, each learned the expensive way:

- **Above the chin is the face.** The chin is the head's lower bound, so clear space is only ever
  below it. A stack placed at y1000 to y1346 "on the chest" was on the nose and lower lip.
- **A tight 16:9 close-up has no usable space in a 9:16 crop at all.** If the chin sits near the
  bottom of the source frame, a cover crop puts it inside the UI band and the scale that clears
  the band puts it where captions start. The answer is a face **band** with graphics in their own
  zone, not a smaller graphic.
- **A full-width band across a torso is a different device from a floating card.** A card is a
  frame (the subject is deliberately placed inside it); a bottom slab is a cover (something has
  been laid over the subject). The same creator approved one and rejected the other in one reel.
- **Prove any such layout by compositing one real frame with ffmpeg before writing HTML.** It
  costs 30 seconds and it is the only thing that catches this class in advance.

---

## Class 5: "too AI slopped", "this theme looks very off and weird"

**AI-slop is the carrier, not the palette.** Swapping hues does not fix it, and this system proved
that by shipping the same look twice.

The signature, exactly: near-black ground, terracotta radial glow, a visible dot grid, and a
drifting point cloud with proximity threads. Every one of those is a default and stacked together
they are *the* generic AI-video signature. vid49 v1 was rejected as "too AI slopped". vid55 v1
rebuilt the identical look from the entry that recorded the rejection and came back as "this theme
looks very off and weird". vid63 made it three dark grounds rejected in a row.

**The fix is to skin the film in what the subject is physically made of.**

| Subject | The material it is made of |
|---|---|
| Printed credentials (vid49) | Ink navy stock, gold foil stamping, guilloche engraving, a wax seal, engraved Fraunces caps |
| An API key (vid55) | A `.env` file, a terminal, an editor: dev-tool paper surfaces |
| A pentest tool (vid63) | Ivory paper, ink, one alert red, a marker ring, margin handwriting, a rubber stamp |
| Apple's design language (vid66) | Apple's own values: `#F5F5F7` page, `#1D1D1F` ink, `#0071E3` link blue, an 8-point grid |

Ask what the subject is physically made of before reaching for a palette.

Two corollaries:

- **Collapse competing brand accents into ONE system.** vid55's three vendor hues (violet, green,
  lime, one per scene) became one syntax-highlight system: keyword violet, string green, number
  orange, refusal red. That single move fixed "off and weird" better than any palette swap could,
  because the incoherence was three competing accent systems, not the individual colours.
- **A recurring object earns its place by being literal.** "The three.js is off and irrelevant"
  was fair: an abstract point cloud has nothing to do with certifications. A guilloche rosette is
  what is actually printed on certificates and banknotes.

**Authenticity does not override how a frame looks to the person whose face is in it.** "It is the
subject's own material" is a good argument and it still lost once, on vid63's green-on-black
terminal. Which is why the theme decision goes through a real mock, below.

---

## The delivery contract is measured, not assumed

The creator judges the delivered file against the one their camera produced, and has asked for it
in those words more than once: *"is this video rendered in the same file size that I gave you the a roll
as"*, then *"make sure that the final file is rendered in the exact size of the A-roll that I gave"*.

### A 4K container carrying a 1080p face shipped three times

The transcode step used to say `scale=1080:1920`. These compositions render at **2160x3840** (a
1080x1920 `#stage` at `transform:scale(2)`), so a 4K master was downscaled to 1080p and then
upscaled back to 4K by the renderer: right resolution, wrong detail. Measured by swapping only the
asset and re-rasterising the same frame:

| Asset feeding the composition | Sharpness (Laplacian variance) | Against the master |
|---|---|---|
| 1080x1920, as shipped | 6.51 | about 52% |
| 2160x3840, native | 11.99 | about 95% |
| the master itself | 12.58 | 100% |

**84% sharper.** vid55, vid57 and vid60 all shipped with the loss. **Match the asset to the
composition's OUTPUT size, never to a habit**: 1080 stays correct for a client short that genuinely
outputs 1080x1920.

That measurement itself needed a controlled comparison. Frame-seeking two codecs with `-ss` lands
on different frames and the sharpness swung 69% to 274%, which is meaningless. **When a metric
disagrees with itself between samples, fix the experiment before believing either result.**

### `-q high` is not high

vid60 shipped at 2160x3840 from a 2160x3840 master, asset chain correct, and the note back was
still "it is very much compressed."

| | Resolution | Bitrate | Size |
|---|---|---|---|
| The A-roll master | 2160x3840 | 28.0 Mbps | 102 MB |
| Delivered at `-q high` | 2160x3840 | **15.5 Mbps** | 57 MB |
| Re-render at `--crf 12` | 2160x3840 | 28.3 Mbps | 103 MB |

`-q high` picked about half what a modern phone writes. **Resolution is not quality**: a 4K
container at half the source's data rate passes every resolution check you can think to run and
still reads as compressed. The re-render cost 2m46s and bought +13.2% high-frequency detail in the
face region.

### CRF is a quality target, so it cannot be a delivery contract

vid61 round 1 rendered at `--crf 10` and landed at **36.8 Mbps** against a 36.25 Mbps master, a
match. Round 2, same CRF, same resolution, same length, landed at **24.9 Mbps**, because the
content got cheaper to encode: three intricate drawn artboards were replaced by one dark screen
recording. Nothing was broken. CRF simply spent fewer bits to hit the same quality target.

And the CRF that matches one master is not portable to another. `--crf 12` was tuned against
vid60's 28 Mbps master; vid61's is 36.25.

**When matching the master's data rate is the actual requirement, pin the rate, not the quality.**
Measure the master's bitrate first, then pick the number for it specifically, then verify the
delivered file with `ffprobe`. See `docs/06-delivery.md` for the commands.

### Never grade the creator's A-roll

The verbatim rule: *"I really don't want to touch my A-roll at any given cost."* Caught three times,
vid49, vid54 and vid55, twice from a grade applied out of habit because the measured stats invited
it.

**The transcode is a codec change and nothing else.** No `colorbalance`, no `eq`, no saturation
touch, no `scale` when the master is already 9:16, and no `loudnorm` on a mix the creator made
themselves.

**The renderer shifts colour on its own, 3 to 7%**, so a grade on top is a shift nobody can
account for. Isolated on vid57 by measuring the face band only (y520 to y1300): master and the
ffmpeg transcode are bit-exact at p95 246/158/154, `hyperframes render` shifts to 235/155/150, and
the delivery pass changes nothing further. That is about 11/255 off R at the top end and 3 to 4 on
G and B: a highlight roll-off, not a hue rotation, and it lives entirely in the browser
compositing path. Per-channel ratios measured elsewhere: vid54 R 0.955 / G 0.963 / B 0.986, vid53
R 0.925 / G 0.926 / B 0.944.

**The rule can be broken with no grade applied anywhere.** One 10-bit HEVC B-roll clip tagged
`bt2020nc`/`arib-std-b67` made the renderer output the **entire** composition as HLG, shifting the
untouched A-roll by about 50 units on G and B. Nobody graded anything. `ffprobe` every
non-generated clip's colour tags at intake: `docs/06-delivery.md` has the re-tag and the `--sdr`
flag, and you need both.

**Measure the cast, report the number, do not apply a correction.** And **measure a crop of pure
ungraphic'd source footage**: a full composed frame samples your own ivory cards and reports a
catastrophe that means nothing. A separate effect on some films is a range squeeze, master and
asset tagged `pc` against a `tv` render, measured at R−12 / G−6 / B−2 on vid61 with zero grading
filters anywhere in the chain.

---

## The measurable bar

Four things that can be asserted rather than argued.

### A void is a defect

Three vid61 scenes passed every gate and still had **0.8 to 1.8s** where one element sat at the top
of an 1120px column over blank paper. Nothing measures this: lint has no opinion, the motion guard
sees plenty of movement, the safe-zone gate sees nothing out of bounds. **A frame can be moving,
in-bounds and contrast-safe while two thirds of it is blank.**

Only a contact sheet of every beat shows it, and it is worth a full shoot round **before**
rendering.

The fix that generalises: **the scene's structure arrives on the cut, its content arrives on the
spoken words.** The scene opens on a node already reading `CODING AGENT` and rewrites it to `DESIGNER`;
artboard slots open empty and dashed and fill later; a repo card lands as a skeleton (bar, mark,
rule, `README.md`) and fills in. **An empty slot is composed. An absent slot is a hole.** And a
placeholder sits **behind** its replacement rather than being removed, which keeps the no-exit-tween
rule intact.

The contact sheet has to be generated from the clip list, not from hand-picked timestamps. A
spliced-out grid scene on the fast-cut-ad demo film played as bare footage for **three delivered
versions** because the
sheets sampled around 9.x and never inside it. Tile every composition element's window at least
once, and verify a timed element is absent **outside** its window too.

### Nothing static for more than about 1 second

This was in the grammar since vid2 and nothing checked it until `motion_guard.py`: fingerprint the
graphics every 0.2s (box, opacity and transform, rounded; exclude `<video>`, whose box never
changes while its picture does) and report runs with no change.

| Film | Held share |
|---|---|
| vid56 short round 1 | 10.0s held, **23% of the cut**, runs of 3.6s, 3.8s and 4.8s |
| vid58 short, first pass | **86%**, every graphics zone composed at its cut then sitting 5 to 6s |
| vid58 short round 2 | 7%, two deliberate 1.6s breaths |
| vid59 | 66%, the cut that drew "very boring b roll" |
| vid62 round 1 | 71%, rebuilt onto word onsets to 56%, then 35% |
| vid57 | 0 held blocks across 36.93s, the first cut in the system to hit it |
| vid63 | 0 blocks held over 1.0s, 13 scenes, mean 2.3s |

A held frame can be deliberate, so this is not a hard fail. **The point is that the decision gets
made on purpose instead of discovered by the client.** Staging arrivals on actual word onsets is
what fixes it, and doing that on vid58 also surfaced that the "420+" figure was on screen 4.5
seconds before the presenter says the number.

Two gate traps worth knowing: `borderColor` and `boxShadow` tweens **register as nothing**, because
the fingerprint is id, rect, opacity and transform. And a guard that fingerprints scene *wrappers*
rather than descendants reports 50% on a hook where a decode, a slam and a stamp all fire. A gate
that swings from 50% to 0% after one edit is telling you about the gate.

### Position is not visibility

vid56's short shipped with **captions invisible for 27 of its 43 seconds** and every gate passed.
The caption rule carried no `z-index`, so it computed to `auto` while the A-roll sat at 2.

Lint and validate check the document and the console; a caption behind a video is neither. The
safe-zone gate measures **where** an element is, and the captions were exactly where they belonged
at y1396. WCAG contrast passed because contrast is computed from declared colours. **Hit-test what
actually paints**, at the composition's real pixel size, with the renderer's clip scheduling
replicated. See `docs/07-troubleshooting.md`.

### The reserved bottom band must be lit, not black

The owner sent back a frame with "What the fuck is this?". Measured on the delivered file: content stopped
at y1530 and the bottom **390px, 20% of the frame, averaged 13/255**, with a pure-black seam at
y1000 to y1040 where the face band's feather ran to solid.

The owner reviews the exported 9:16 file in a player, where an unlit reserved zone reads as a broken
black
bar. **Reserving a zone means keeping text out of it, never leaving it black.** A wide shallow
stage lift along the floor took the band from 13.4 to 28.5 mean and softened the seam to 7.0.

---

## Rebuild the UI, do not screenshot it

The note on vid54, on real screenshots that had already replaced a mock: *"cannot be just a
screenshot... rebuilt exactly how it is being shown, with proper zoom-ins and zoom-outs, and actual
typing... looks very vague."*

**A screenshot is inert.** It cannot type, cannot focus a field with a ring, cannot be pushed in on
without going soft, and at reel resolution a real product screenshot reads as a blurry rectangle,
which is what "vague" names. **A screenshot can only assert; a built panel can enact.**

- Keep the real captures **out** of the film and use them as the design spec.
- Rebuild as live DOM that **actually types** character by character with a blinking caret, using
  the product's verbatim strings, and that opens the product's own affordances (its slash menu, the
  highlight walking the options).
- Drive the typing off transcript word onsets, not a flat duration guess.
- **A zoom is only legible if the content survives it.** vid54: a 780px document with 724px of
  content at 1.24x maximum gives 898 against a 904 view.
- A built panel performs the claim. vid49's enrol counter runs to 1,886,772, the lessons tick off,
  the $99 is struck through and drops to $0.00 under a FEE WAIVED stamp.

**The carve-out:** compositing real UI onto a generated screen is optional, not a rule. On a
*background* plate whose screen is never the subject, a soft out-of-focus screen is more believable
than a pixel-perfect pasted one. Ask which the screen is, subject or texture. And a mis-measured
perspective transform looks worse than no attempt: delete it rather than ship it half right.

---

## Graphics are not the default. Showing the presenter is.

The note, stated explicitly to generalise to every video and not just the beat it was written
on: *"No need to show any animation here when [the presenter] says [the line]... just the A-roll should be
shown. Any animation, error, just A-roll with captions should be there. At the last line, CTA."*

What the beat had been doing: the 4.6s closer, the line where the presenter makes the direct ask,
was graphics-only for its whole duration with no face at all. Rebuilt, the first 1.9s is bare
A-roll with the caption low and the only motion a slow push on the picture itself (scale 1 to
1.02), and **the CTA arrives ON the last line** rather than owning the whole beat.

**Reach for an animated overlay when it is carrying information that cannot come from the
presenter speaking**: a number, a comparison, a mechanism. Never to fill a beat, and never to
replace the presenter at the moment they make the ask. Audit every closing and CTA beat in every project against this rather
than waiting for the note.

**The precondition is that showing the presenter is worth doing.** When the take itself is unusable
for a span (the presenter is reading from notes: eyeOpen 0.45 to 0.13 across 32 consecutive samples), the answer is
to take the picture off and let the graphics own the frame, **not to shrink the problem**. An
unwatchable shot at a smaller size is still an unwatchable shot.

And check the exclusion is real. One graphics-only beat existed because a gaze scan excluded 2.4s;
the underlying data showed `eyeOpen` dipping to 0.12 to 0.26 for two to four samples twice and
recovering immediately, with the frames showing the presenter square to camera. **They were blinks**, and
`min_sustain`/`pad` turned two blink clusters into one exclusion. A face-safety false positive
silently removes the presenter from a beat and nothing downstream flags that as a defect.

---

## When the same complaint survives a fix, remove the whole category

The fast-cut-ad demo film's "typing sfx" note survived **three** evidence-based fixes across three
rounds. Round 2
measured the click and tick family by envelope and removed it. Round 3 transient-scanned the mixed
bed and found a metronomic 0.465s percussion tick baked into the **music**, on a strict 129 BPM
grid, and swapped the bed. Round 4 removed the two remaining click-attack reveal cues (2ms attack).
Each fix was correctly diagnosed and verified.

Round 5's five timestamped notes (14.32, 17.31, 19.03, 21.43, 33.85) landed exactly on the five
surviving whoosh and impact cues, the ones every acoustic measure said were **not** clicks. The
client was naming a sound **category**: any added effect at all. The film is now voice and music only.

**When the same complaint survives two evidence-based fixes, stop refining the classifier and
remove the whole class.** A measurement-based classifier can converge on the wrong category
boundary and then get re-validated against itself round after round, because every fix looks
locally justified. The strongest signal is recurrence at the same literal timestamps a note
previously pointed at. The correct move in round 2 was one question: "should ALL added sounds go,
or just the clicky ones?" One question instead of three rounds.

---

## Things that are round-scoped, not law

An owner's earlier correction can be reopened by a later verdict. A locked-off frame and a ban
on wipes were both correct responses to "too much", and both were reversed by a later "this is
boring". **Only the treatment rules survived every round.**

So: when a new note contradicts an old one, the new one wins for that video, and the old one goes
into `HISTORY.md` with its date rather than into the grammar as law.

---

## Process rules that protect the bar

- **Mock the style in HTML plus Playwright before building.** A three-frame static mock renders in
  two minutes, or about four including the screenshots. One was rejected and its replacement
  approved in a single round, and the second mock's fixes became the build's design rules. vid55's
  mock caught a wrapped card number, two stamps overlapping their own text and a wrong face-card
  scale before a single frame was rendered. Cost of learning in mocks: minutes. In renders: hours.
- **Mock REAL frames, never ASCII.** An ASCII box inside a question is not a mock: it conveys
  structure and not look, and look is the entire thing being judged. vid63's dark terminal theme
  was approved from an ASCII preview and rejected thirty seconds after the owner watched the render, as
  "very shitty and vibe coded and very very weird". Building the three-way mock sheet after the
  rejection cost 20 minutes, and it would have cost the same before. It works: the round-2 theme
  mock sheet drew **zero** notes on the theme. This applies to any whole-film decision, theme, hook
  device or layout family.
- **After any theme rejection, the next artefact is a mock, not a cut.**
- **A vague note is not a spec: ask, do not guess.** vid63's hook was rejected as "very shitty and
  weird, think of something better please", with no description of what better meant. A replacement
  was designed and rendered, and round 2 spelled out something entirely different. When a note names
  something as wrong but gives no positive description of the fix, that is the signal to ask before
  building. This is the opposite case to the mock rule: mock when the **choice** is unclear, ask
  when the **requirement** is.
- **Validate a new look on one chunk before mass-producing.** The 4K type-scale finding came out
  of reading chunk one three times and applied to all eight. Finding it on chunk seven would have
  meant re-authoring six.
- **Read your own render before handing it over.** The owner should not be your first QA pass.
  A round-one review that finds bugs you could have found is a round spent on nothing.
- **Read every literal on-screen string as a viewer before the delivery render.** Three of vid62's
  eyebrows went through lint, validate, the safe-zone gate and a full 67-frame shoot as build
  notes: "One beat of price, at the end" sat over the CTA for four seconds, and "Their own Incogni
  account" and "What they would tell a friend" were third person about the person whose face was in
  the same frame. List every eyebrow, chip, stamp, source pill and button string and read the list on
  its own, out of context. Anything describing the edit is a build note that escaped; anything in
  the third person about the person on screen gets recast as a label.
- **Two failed passes on a decorative element means cut it, not tune it.** Negative space beats a
  graphic that needs explaining.

---

## Where the two halves of this bar are enforced

This document is the argument. Two other files are the execution, and they split along the same
line the top of this page draws.

**The measured half: `tools/qa/benchmark.py` and `tools/qa/benchmarks.json`.**

```bash
python3 tools/qa/benchmark.py out/vid68-final.mp4 --creator card-reel \
    --master /path/to/camera-master.mp4 \
    --srt out/vid68-final.srt --caption-pack out/vid68-caption-pack.md \
    --composition hf68/index.html
```

It measures the DELIVERED FILE, which is the only artefact the owner ever sees, against the numbers the
sections above were written from: the master's resolution and data rate, integrated loudness and
true peak, frozen runs and their longest block, the reserved band's mean luma, frame 0's ink
coverage, face presence and the chin against y1600, and the em dash across the composition, the
SRT and the caption pack alike. Per creator, because the targets genuinely differ. About 20 to 35
seconds on a 4K reel; non-zero exit on any hard fail.

Read `benchmarks.json` rather than only the tool's output. Every number in it carries the film and
the reaction that set it, and one entry is marked `derived: true` because its exact threshold is
calibration rather than a recorded rejection. Three things it deliberately does not settle: mean
shot length (a static crop-cut barely scores as a scene change, so the shot count lives in the shot
plan), whether a delivered crop samples its master above 1:1 (it refuses the comparison rather than
reporting a false failure), and the DOM-side held fraction that the "boring" rejections were
actually written against, which needs the composition and `tools/gates/guard.py`.

**The judgement half: `docs/09-self-review.md`.**

The five rejection classes above are diagnoses, and a new operator has never seen the reaction that
produces one. 09 turns them into a sequence with an artefact and a stop condition per pass, ordered
by how often each complaint recurs, so round 1 of a new operator's film is about the film rather
than about defects that were already findable. It ends where this page does: the protocol replaces
round 1 and round 2, and nothing replaces showing the owner the cut.
