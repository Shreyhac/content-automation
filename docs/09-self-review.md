# The review you owe yourself

Every good cut in this archive got there through three to twelve rounds against a real person's
reactions. demi2 went v1 to v20 in about twenty hours. vid63 took four rounds on the theme alone.
The reason the cuts are good is not that the first render was good; it is that somebody reacted to
it, badly, several times.

A new operator does not have those reactions. So round 1 of a new operator's film looks like round
1 of every film in here, and round 1 in here is usually rejected. **This document is his review,
run on yourself, before he sees it.** It substitutes for round 1 and round 2. It does not
substitute for showing him the cut, and the last section says why.

Two things make it work rather than being a reading exercise:

- **Every pass produces an artefact you look at**, not a question you answer from memory. You
  cannot self-review from the composition you just wrote. You know where everything is supposed to
  be, which is precisely the knowledge that hides the defect.
- **Every pass has a stop condition.** If a pass finds something, you fix it and re-run that pass.
  You do not carry a known defect forward to see whether he notices.

Budget: about 40 minutes for a 35 second reel the first time, most of it in pass 2. That is one
review round of his, and one review round of his costs a full re-render plus a day of latency.

---

## Pass 0: the arithmetic, before you look at anything

```bash
python3 tools/qa/benchmark.py out/vid68-final.mp4 --creator shreyansh \
    --master /path/to/camera-master.mp4 \
    --srt out/vid68-final.srt --caption-pack out/vid68-caption-pack.md \
    --composition hf68/index.html
```

About 20 to 35 seconds on a 4K reel. Every number it checks was set by a film that was sent back.
Fix every FAIL. Read every WARN and write down, in your delivery note, why you are shipping it.

**Stop condition: exit code 0, and a written sentence for each WARN.**

This pass exists because it is the only half of the bar that does not need judgement, and because
skipping it has cost re-renders repeatedly. `tools/qa/benchmarks.json` carries the provenance of
each number, so when a row fails, read its `why` before deciding what to change.

---

## Pass 1: the cold watch

Watch the delivered file once, start to finish, **on a phone, with sound on, at arm's length**, and
do not touch anything until it ends. Then write down the first three things you noticed, in the
order you noticed them.

Three rules that make this pass real:

- **Not in the browser and not scrubbed.** He watches the exported file in a player. That is where
  an unlit reserved band reads as a broken black bar and where a soft screenshot reads as blurry.
- **Not at your desk with the composition open.** If you can see the code, you are checking your
  intentions.
- **Frame 0 counts as a shot.** It is the Reels cover. Pause on it before you press play and ask
  whether it would make you stop scrolling.

If the first three things you wrote down are all defects, stop reviewing and go rebuild. That is
what a round 1 rejection is, and you just gave it to yourself for free.

**Stop condition: your three notes are observations, not defects.**

---

## Pass 2: the contact sheet

```bash
python3 tools/qa/shoot-sheet.py hf68/guard.json --from-clips
```

Tile every beat and look at every tile. `--from-clips` derives the samples from each element's own
`data-start` window, which is the part that matters: a fixed time grid never samples an element
whose window falls between two ticks, and a spliced-out grid scene on demi2 played as bare footage
for **three delivered versions** because the sheets sampled around 9.x and never inside it.

What you are looking for on each tile, in this order:

1. **Is anything drawn on his face?** See class 4 below. This is the single most recurrent note in
   the archive.
2. **Is two thirds of the frame blank?** A void passes every structural gate. Three vid61 scenes
   spent 0.8 to 1.8s as one element at the top of an 1120px column over blank paper.
3. **Is any text on top of other text?** Every gate on vid64 checked graphics against the face, the
   card and the band. Two graphics colliding was unguarded and a panel printed over a caption for
   a whole hook.
4. **Does every carrier look the same?** Count your rounded rectangles. See class 2.

**Stop condition: every tile is a frame you would put in a portfolio.**

---

## Pass 3: the literal strings, read out of context

List every eyebrow, chip, stamp, source pill, button label and caption in the film, into a flat
list, and read the list on its own with the video closed.

Three of vid62's eyebrows went through lint, validate, the safe-zone gate and a full 67-frame shoot
as build notes. "One beat of price, at the end" sat over the CTA for four seconds. "His own Incogni
account" and "What he would tell a friend" were third person about the man whose face was in the
same frame.

- Anything that describes the edit is a build note that escaped. Delete it.
- Anything in the third person about the person on screen gets recast as a label.
- Grep every caption for a bare price. Whisper wrote "three ninety-nine" as `$399` and "fourteen
  ninety-nine" as `$1499`, and that shipped as a hundred-fold error on a competitor's price in a
  sponsored comparison. Then check that your correction table actually **fired**: three films'
  worth of price tables were dead code because whisper puts a leading space on ordinary words and
  none on attaching punctuation.
- Grep for the em dash. `benchmark.py` does this, and it does it over the SRT and the caption pack
  as well as the composition, because that is where 21 of them shipped.

**Stop condition: the list reads as copy a viewer wrote, not as notes an editor left.**

---

## Pass 4: the audio, on its own

Play the film with your eyes shut.

- **Every join.** "The audio cuts weird here" is usually a script fault, not an encode fault.
  Transcribe plus or minus 1.6s around each join in isolation before touching ffmpeg. Both of
  vid62's short's audio notes were clean at signal level: one join cut his sentence mid-list, the
  other opened a beat on a dangling "And" bridging two topics 68 seconds apart. Both fixes were
  editorial.
- **Verify a suspected defect against the master.** "The A-roll repeatedly says 'pit lips, pit
  lips'" was not a repeat: he had delivered the phrase as separate stabs and the cut had removed
  the pauses between them until the fragments read as a stammer. The pauses inside a halting
  delivery are load-bearing.
- **Re-transcribe after any audio fix.** One tail fix stole a word at a different join. Waveform
  arithmetic missed it; a fresh transcription caught it.
- **Count your added sounds and ask whether they should exist at all.** "Remove the typing sfx"
  survived three correctly-diagnosed, correctly-measured fixes across three rounds because he
  meant every added sound. The correct move at round 2 was one question, not three rounds of
  classifier refinement.

**Stop condition: every sentence in the film is a finished sentence, and you can name why each
remaining cue is there.**

---

## Pass 5: the rejection taxonomy, in his words

This is the list, ordered by how often it recurs across the archive. Read every row against your
cut. `docs/03-quality-bar.md` carries the full argument for the five big classes; this is the
checkable version.

| # | What he says | What it actually means | What detects it before he does | Fix class |
|---|---|---|---|---|
| 1 | "text on my face", "too weird, coming on the face", "the framing is off" | A layout-MODE failure, not a nudge. A beat is CARD mode or FULL-BLEED mode and there is no third mode | Composite one real frame with ffmpeg before writing any HTML. Run the face-safe gate over FULL-BLEED spans too: vid62's only ran while the face was carded and text landed on him 180 times across 23 elements. Read contourBot, and remember the top band is not safe because his hair is in it | Change the mode for the whole beat. Patching instances one at a time generates more |
| 2 | "boring", "text based", "the animations are basic" | A scene-FORM failure. Every scene is a card with words in it | Ask of each beat: can this only be expressed as a sentence in a box? Then it is the wrong beat. And measure: 66% held drew "very boring b roll", 71% drew "only a text-based thing is really too shitty" | Find the physical event the line describes and animate that. A character doing the verb, not an icon with a label |
| 3 | "very much compressed", "the size of this video is very low", "in the exact size of the A-roll that I gave" | The delivery contract, which is the master's resolution AND its data rate | `benchmark.py` pass 0. Resolution is not quality: a 4K container at half the source's rate passes every resolution check you can run | Re-render with the rate pinned. Never a second lossy pass to raise it |
| 4 | "the SFX is very irritating, going on and on and on", "too loud", "typing sfx" | Almost always a category, not an instance, and often sustained texture rather than level | Count cues and measure share. One cue per 4 to 5s, no file over about 8% of placements, per chunk not per film. A bed at median 0.053 still drew four "remove the SFX from here" because it was sustained | Transients only, silence allowed. When the same complaint survives two evidence-based fixes, remove the whole class and stop refining the classifier |
| 5 | "very cheap", "not premium", "looks vibecoded", "too shitty" | Either the carrier or the treatment, and they are different repairs | Count your carrier shapes. On the film rejected as "very cheap" the one positive was "the globe animations are nice", and the 3D field was the only device that was not a rounded rectangle. Then check working type sizes as a fraction of frame width: 32px labels in a 3840 frame are a 16px label on a 1920 frame, and a 1.3x lift changed the read more than any scene rebuild | Replace the carrier, not the content. No gradient-filled display type, no glow shadows on type, one background wash, hairlines not coloured borders |
| 6 | "the audio cuts weird here" | A script fault at the join, not an encode fault | Pass 4 | Re-cut the in-point and the out-point until the sentence is finished. Fades come after, not instead |
| 7 | "this is not centered aligned", "why is Nader's frame always moving left-right" | Either a centring solved off the extremes, or a follow curve that should be one constant | Centre on the MEDIAN head position: one 0.4s lean dragged a card 55px. And one constant tx per window, never a smoothed tracker: a person swaying inside a still frame is normal, a frame sliding around a person is not | Re-solve the transform. If the median itself breaches, it cannot be a card |
| 8 | "too AI slopped", "this theme looks very off and weird" | The carrier again, at film scale. Near-black ground plus a coloured radial plus a dot grid plus a drifting point cloud is *the* generic AI-video signature | Three dark grounds were rejected in a row before this landed. If your ground is dark and glowing, assume it | Skin the film in what the subject is physically made of. Collapse competing brand accents into ONE system |
| 9 | "cannot be just a screenshot", "looks very vague" | A screenshot is inert: it cannot type, cannot focus a field, and at reel resolution it reads as a blurry rectangle | Any product screen in the film that does not animate | Rebuild as live DOM that actually types, using the product's verbatim strings, driven off word onsets |
| 10 | "where the fuck are the captions", "text is not visible" | Either the caption never painted, or it painted with no ground under it | Hit-test what PAINTS. vid56's short shipped with captions invisible for 27 of its 43 seconds at exactly the right y1396, because the rule carried no z-index. And a safe zone guarantees position, not contrast: measure the bright-pixel FRACTION over the picture, never the mean | Add the z-index, or give the type its own solid surface |
| 11 | "the animation looks childish", "this looks very weird" | A retired visual family came back | `creators/<name>/GRAMMAR.md` has the retired list per account. Check it before you draw | Remove the family, do not restyle it |
| 12 | "make it stagnant", "no need to zoom his frame" | Camera grammar is per-creator and is not a house default | Grep your file for scale tweens on the stage and on any A-roll wrapper. One creator's whole zoom grammar was ported into another's film without anyone checking whose it was | Delete the camera moves. Element-level entrances are still fine |
| 13 | "too shitty" on a logo row, "why that open claw icon again" | Text chips standing in for brand marks, or two characters doing one job | Render every logo to one sheet and look at it before building: a dead mark is worse than the text it replaced. One film, one cast | Real marks. Cut the second character |
| 14 | "we haven't revealed Demi yet", a factual error in a sponsored cut | The film says something the brief or the product does not support | Resolve every promo code against the partner URL, never against whisper. Attribute every on-screen figure. Read the reference for what it CLAIMS: one lifted reference's VO said "without ever touching the terminal" and the repo's own Quickstart is three terminal commands | Fix the claim, and put the correction in the CTA doc |
| 15 | An em dash | The standing rule on all four accounts | Pass 0. It is a pre-render check, not a pre-delivery one: seven labels found late cost a full 4K re-render | Middot for label separators, comma or colon for sentence dashes |

**Stop condition: you have a specific answer for every row, and "not applicable" counts only when
you can say why.**

---

## Pass 6: the reversal check

Before you act on anything in pass 5, check whether it was reversed.

An owner's earlier correction can be reopened by a later verdict. A locked-off frame and a ban on
wipes were both correct answers to "too much" and both were reversed by a later "this is boring".
Demi asked for a sub-1.5s mean shot in round 1 and by rounds 6 and 9 was asking for held b-roll and
"smooth and subtle", measured against a reference ad with zero detectable cuts.

- Read `creators/<name>/HISTORY.md` for what was reversed and when.
- When a new note contradicts an old one, the new one wins **for that video**, and the old one goes
  into HISTORY.md with its date rather than into the grammar as law.
- Only the treatment rules survived every round: no gradient-filled type, no glow shadows on type,
  hairlines rather than coloured borders.

**Stop condition: nothing you are about to ship is a rule that was already retired, and nothing you
are about to "fix" was already asked for.**

---

## Pass 7: the deliverables

The film is not the deliverable on its own.

- The MP4 in `out/`, named `vidN-final.mp4`, verified with `ffprobe` and not with a render log.
  A failed render leaves yesterday's file in place with a plausible size: check the mtime and the
  exit line.
- The caption pack, paste-ready. No research, no rationale, no character counts, no sources in it.
  It is a clipboard, not a report. No hashtags.
- The `.docx` behind any "comment X and I'll send you Y" line, at FIRST delivery and not when he
  asks. `tools/deliver/make_cta_doc.py`.
- The share link, opened for review without being asked.

**Stop condition: every file above exists and you have opened each one.**

---

## The honest limit

This protocol substitutes for round 1 and round 2. It does not substitute for showing him the cut.

Three reasons, all of them observed rather than theoretical:

1. **A vague note is not a spec, and neither is your guess at one.** vid63's hook came back as
   "very shitty and weird, think of something better please" with no description of what better
   meant. A replacement was designed and rendered, and round 2 spelled out something entirely
   different. When you cannot tell what the requirement is, ask. Mock when the CHOICE is unclear,
   ask when the REQUIREMENT is.
2. **Authenticity does not override how a frame looks to the person whose face is in it.** "It is
   the subject's own material" is a good argument and it lost once, on a green-on-black terminal
   theme that was correct by every rule in this repo.
3. **Nothing here can tell you the film is boring.** Every rejection class in pass 5 has a detector
   and none of the detectors is the judgement. A cut can pass pass 0 through pass 7 and be rejected
   in thirty seconds.

What this protocol buys you is that his round 1 is about the film rather than about defects you
could have found yourself. That is the whole difference between a four-round production and a
twelve-round one.

**And use the cheap gate that exists before any of this: mock the look as real rendered frames and
get the theme approved before you build.** A three-frame static mock costs about four minutes
including the screenshots. A theme approved from an ASCII preview was rejected thirty seconds after
he watched the render. The round-2 mock sheet that replaced it drew zero notes on the theme. Cost
of learning in mocks: minutes. In renders: hours. After any theme rejection, the next artefact is a
mock, not a cut.
