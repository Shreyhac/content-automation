# Making a short from a finished long-form

The default method for any "make a short of this". Reference build:
`reference-builds/nader-vid46-short/`. About three hours end to end and three render rounds when
the film's measurements already exist.

---

## Derive, do not re-measure

The film's gaze pass (`crown.csv`, `facebox.csv`) and its `words.json` are on the same timeline as
the shipped film, so **a new solver over the same data gives the vertical geometry for free**.
Nothing gets re-transcribed, re-graded or re-recorded.

`beats.py` is the single source of truth: each beat with its source segments and frame count. The
VO splice, the baked crops, the captions, the SRT and the chunk HTML all read it.

---

## Define the timeline in FRAMES, never seconds

Each beat's frame count is fixed and its audio out-point is derived from it, so audio and video
cannot drift (17ms slack per beat, zero cumulative). `assemble.sh` asserts the total frame count
before it will concatenate.

---

## Excerpt on complete sentences, not word onsets

**This is the fault that gets a short rejected.** "Audio sentences are not clear" means sentence
fragments: 9 of 12 beats opening mid-clause ("and get this,", "don't") or closing on a comma.

Word-onset cutting is right for animation timing **inside a continuous take** and wrong for
excerpting, because the listener has no preceding clause to resolve a fragment against.

Method:

1. Split the source word transcript on `.?!` to regenerate its complete-sentence list.
2. Select whole sentences.
3. **Assert in the beat table that every beat equals a sentence's exact bounds.**
4. Prefer a long sentence that carries its own attribution over a short fragment that strands it.

### Whisper's sentence ends undershoot

A word marked as ending at 68.92 was still decaying at -28 dB until 69.24. Cutting on the marks
amputates word tails, which is half of what "sentences are not clear" actually is.

**Scan each candidate boundary with `volumedetect` at 40ms resolution and run the beat to the
measured dip.** Across ten sentences that cost 2.1s and was worth every frame.

### Joining

- Sentence-end to sentence-start with 25ms fades.
- **Room tone only where there is nowhere to fall.** Of nine joins, seven had real silence after
  the sentence and could simply extend into it. Only two needed tone lifted from elsewhere in the
  master. Blanket-inserting 80ms everywhere is worse than measuring.
- **Never drop a natural pause inside a face block.** If beat 1 ends at 2.92 and beat 2 starts at
  3.30, a "tight" cut drops 0.38s, and because both beats show the face that is a 0.38s jump cut
  on a talking head. Run the first beat to the second's start.
  **Assert it: face clips take a continuous source range, never a concatenation.**

### Cutting the audio moves attributions onto the frame

Dropping "Privacy Rights Clearinghouse, working with the EFF, has identified" and "an independent
Deloitte Assurance Report confirmed" makes four published claims unsourced unless the frame
carries them. **Audit this the moment a segment list exists, not at QA.**

---

## One face placement, full stop

v1 alternated full-bleed (s=0.794) and card (s=0.399) five times with a 2.1s face island in the
middle, so his head changed size every time he appeared.

**Change visibility, never geometry. Only at act boundaries. No block under about 3.2s.**

For the geometry itself see `playbooks/face-geometry.md`. The short version for a tight 16:9
source: there is no full-bleed 9:16 treatment, so the face gets a band or a card and the graphics
get their own zone.

---

## Bake the crops, do not CSS-transform the video

Each beat gets a clip already at its final size, so the browser never resamples the A-roll and the
solved geometry exists in exactly one place. A `only()` helper then shows exactly one clip, which
makes the "a-roll triple-pop" class of bug structurally impossible.

Where a window ends a few frames early, `tpad=stop_mode=clone` holds the last good frame instead
of leaving empty ground.

If the build needs a hero/card **move**, bake once at hero size and do the card as a CSS
transform. See `playbooks/face-card-device.md`.

---

## Cuts

**A flash cut at every beat boundary is a strobe.** 11 in 40 seconds was called "the cuts are very
weird". Allow exactly **one**, on the single biggest emphasis.

Act boundaries get one consistent wipe. Inside an act the face is never interrupted and only the
graphics zone's content changes, by its carrier's own motion.

**A scene arriving on a hard cut must be composed on the cut frame.** Fading an eyebrow and
running a per-word rise 0.04s after the cut leaves the cut frame empty. Cut-arriving scenes get a
whole-block settle; only mid-scene headlines get the signature per-word rise.

---

## Porting a 3D layout to the new canvas

**Re-derive the pixel dimensions, do not scale them.** Pixels-per-unit is `H / VIS_H`, so 2160 to
1920 makes every px constant 12.5% larger in a frame a third as wide.

The film's 830px-wide 25-column wall gave a 33px pitch against a 52px plate: the plates overlapped
and the field rendered as a **barcode of horizontal stripes**. Pitch must exceed the plate in both
axes (1650x1480 gave 66x49). No gate catches this; only frames do.

---

## Ending

**Never truncate a sentence to reach an end card.** One version cut to the offer lockup for the
last 14 frames mid-sentence, because every frame at the end of the closing line was a downcast
blink.

The right answer is to make the closing question its **own complete-sentence beat**. On that film
the gaze data forced it to be a graphics beat anyway, so the lockup became that beat legitimately.

---

## Two more things frames taught

- **Cross-hand a card into a chip, do not scale it.** Shrinking a coupon card takes its type
  illegible. Instead the card and the chip tween on the same half second with the same ease and
  the same centre travel: it reads as one object changing size, and the code stays on screen
  continuously.
- **The object must arrive carrying its content.** A card tweening up from `opacity:0` and then
  holding a blank white rectangle for half a second while its contents arrive on their words is a
  dead frame. Give it its permanent content on the cut, and let the one thing the beat is about
  stamp into the empty slot waiting for it.

---

## Render economics

A 1080x1920 chunk renders in about 1.5 minutes against about 4 minutes for a 4K three.js chunk.
Budget the clock for composing and frame QA, not for rendering.
