# Captions

Tools: `tools/captions/build_captions.py`, `inject_captions.py`, `fix_caption_glue.py`,
`build_srt.py`.

**Generate the burned captions and the SRT from the same source** so they can never disagree.

---

## Grouping

Group the word stream by: <= 6 words, <= 40 characters, punctuation, or a gap > 0.45s.

142 caption groups is generator work, not hand work. Inject by splicing between explicit markers
(`<!-- CAPTIONS -->` and `/* CAPTIONS */`).

**Whisper fixes must run on the WORD STREAM before grouping**, not per group. A name straddling a
caption boundary can never match a per-group regex. Replace token *runs* and redistribute the
timing across the replacement.

---

## The token-glue rule

**Whisper splits numbers and hyphenates into two tokens.** `$7.99` arrives as `$7` + `.99`,
`30-day` as `30` + `-day`, `Wi-Fi` as `Wi` + `-Fi`.

Joining the stream with a space printed **"$7 .99"**, "30 -day", "third -party", "risk -free", and
where the grouper happened to break between the pair, a caption clip **opened on a bare hyphen**.
Eleven clips across five chunks. No gate flags it, because the HTML is well formed.

> **A token that opens with attaching punctuation belongs to the word before it: no space, and
> never across a clip break.**

This lives in `build_captions.py` as `CONT` so the SRT inherits it. `fix_caption_glue.py` applies
the same rule to already-injected HTML.

---

## Timing

- **Clamp each caption's tail to the next group's start**: `min(end + 0.14, next - 0.02)`. Without
  it every group overlaps its neighbour on the same track and lint fails.
- **Round the two edges, then derive the duration.** Rounding start and duration independently
  produced an end of 21.334 against a next start of 21.333, and the static guard rejected it as
  overlapping. Frame-snap both edges first, then subtract.
- **Cut a caption to the spoken word, not to the next beat.** A caption that outlives its scene
  contradicts the frame.
- **A caption starting at 0.0 gets no entrance tween.** A `from` at position 0 parks it invisible,
  and frame 0 must be composed.
- **Leave 0.02s gaps between same-track clips.** Float-precision overlaps
  (`start + duration = next_start + 1e-15`) fail lint.
- **Frame-exact boundaries double-draw for one frame.** When a caption's `data-start +
  data-duration` lands exactly on a frame time AND equals the next clip's start, both clips render
  on that frame: two captions superimposed. Lint does not catch it (it only flags `end >
  next_start`), and because only frame-aligned boundaries do it, it looks intermittent.
  **Fix: `duration = next_start - start - 0.001`.** Do not shave more than about 1ms: a
  0.01 to 0.017s shave puts a frame time inside the gap and produces a blank caption frame instead.

---

## A word belongs to exactly ONE chunk

In a chunked long-form, filtering caption words by **overlap** (`word.end > chunk.start and
word.start < chunk.end`) puts any word straddling a join into BOTH chunks: five of fourteen joins
on one film duplicated a word across the seam ("OneRep also" / "**Also** rolled out..."). Filtering
by **onset alone** instead drops words, because chunk boundaries are frame-snapped and whisper's
onset for the word the chunk was actually cut on can sit a few milliseconds earlier than the
boundary. **Fix: key on onset plus a small frame-snap slack (~0.06s).** Proofread the assembled
caption track end to end, in order: duplicates are invisible chunk by chunk and obvious in one
list.

## Numeric tokens need exact-token repair, including trailing punctuation

Whisper writes spoken numbers as bare digits ("three ninety-nine" → `$399`, "fourteen ninety-nine"
→ `$1499`), and an exact-token fix table can correct `$1499` while missing `$1499.` at a sentence
end: the trailing period makes it a different token. In a sponsored comparison this is a
**hundred-fold error on a competitor's price**, burned in. Grep every caption file for
`\$[0-9]{3,}` before delivery on any film that quotes prices; it is the check that would have
caught this.

## Repairing a chopped word at a cut join

An out-point that trims cleanly by the transcript's timestamp can still cut the word's actual
**sound**, because whisper's marks undershoot (see `playbooks/short-from-longform.md`). The fix is
an L-cut, not moving the cut: extend the outgoing beat's audio (faded) under the incoming one,
**measured per join, not chosen**: extend until the signal has been under the noise floor for
three consecutive 20ms windows.

Two ways that repair itself goes wrong:

- **A tail scan that walks forward from the cut can cross into the next word.** Capping only at
  silence, with no ceiling, laid 124ms of the *next sentence's* word over the close: a fragment of
  a different word appearing where none belongs reads exactly like "a word got cut." Every tail
  must be capped at `min(measured_silence, next_word_onset − 50ms)`.
- **A fade shape can destroy a word without clipping a single sample of it.** A `curve=exp` fade
  starting at the cut's own t=0 is already well down by 100ms, so the release is inaudible under
  the incoming line even though the word is technically present in the file. Hold full level for
  ~60% of the tail and taper only the last portion: the tail is the same voice continuing, and
  ducking it from sample zero is what makes it sound truncated.
- The cheap way to verify a word survived: **transcribe the delivered span and the same words cut
  from the clean master, and compare the two transcripts**: seconds, versus a full-file pass, and
  it controls for the transcription model's own mishearings rather than chasing them as if they
  were audio bugs.

## A caption behind an A-roll is invisible and every position-based gate passes

A caption `div` with no explicit `z-index` computes to `auto` (stacking-context 0); a full-bleed
`<video>` above it in stacking order paints over it completely, for the video's entire on-screen
life. `safe_zones`-style gates measure *where* an element is, not *what actually paints there*.
The caption was exactly inside every Instagram safe zone and simply never visible. See
`playbooks/frame-qa.md`'s "position is not visibility" note; the caption-specific fix is
`autoAlpha`/explicit `z-index` on any caption layer that shares a stack with full-bleed video.

## A suppression keyed to a composition must be re-derived when the composition changes

Mute ranges (spans where a card already states the words, so the caption layer is deliberately
silent there: see "When NOT to caption" below) are computed against a specific cut. When the
composition is rebuilt and the graphics that justified the mute move or disappear, the old mute
ranges can outlive them: one rebuild shipped **~30 seconds of speech with no subtitle at all**,
because four legitimate mute ranges from an earlier cut had never been re-derived. Regenerating the
caption track from the current composition (rather than reusing a hand-patched one) is what
surfaces this: see the "regenerate derived artefacts" note in `playbooks/frame-qa.md`.

## Per-word animation

- **Later words must be parked at time 0.** A generic per-word rise built as
  `fromTo(yPercent:112 → 0, immediateRender:false)` leaves every later word visible from clip start
  (CSS state y=0), then dips it down and re-raises it at its onset, which reads as a glitch on
  every multi-word caption. Park with `tl.set(wi,{yPercent:112},0)`.
  Round-one frames looked fine because fully formed captions do not look broken in stills. Only the
  onset-sample frames exposed it.
- **Auto-stagger drifts off the VO on long lines.** Use per-word `data-t` onsets from whisper with
  a monotonic clamp (each word >= previous + 0.05).
- **Slam words must SKIP an overflow mask.** Scaled glyphs clip inside it; alpha-pop them instead.
- **A masked per-word rise needs more leading** than the same type unmasked, because each mask
  extends about .18em below the baseline for descenders. On a wrapped headline a descender on line
  one lands in the cap height of line two. Give the masked class its own leading.
- **Tune the stagger for the STILL frame, not the motion.** 11 words at .055 stagger with a .68s
  duration is 1.28s of half-formed headline, and a masked half-line reads as a render bug rather
  than a reveal. **.028 / .52** is the standard. If a QA still at any beat shows a headline sliced
  in half, the entrance is too slow regardless of how it plays.
- **Adjacent slam words need explicit margins.** `.cap b{margin:0 .12em;display:inline-block}`
  fixes every instance at once; em-padding alone is not enough at display sizes and renders
  "werePRETENDING".

---

## Placement

- **Give each caption its own `top` once the face moves.** A single fixed y stops working the
  moment a face card exists: around y1380 while a panel hides the face, around y760 in hook and CTA
  where it does not.
- **On a split beat the caption moves ABOVE the card.** Leaving it low prints it on the jaw.
  **Drive it off the beat's mode** so it cannot be forgotten. And index the beat from the clip
  inside the emit loop: a shared loop variable left pointing at the last beat from an earlier pass
  silently emitted every caption in the low position.
- **An on-face caption span's inline `top` is relative to its container's offset.** To land at
  absolute y1300 in a container offset `top:214`, set `top: 1086`.
- **A `.sup.lo` bottom-anchored container breaks inline `top:` on its spans.** A zero-height
  bottom-anchored container makes `top:250px` resolve to about y1650, off-screen. Use the
  top-anchored class for face supers.
- **An absolutely positioned `.w` with `width:1080px` turns a pill into a full-bleed subtitle bar**,
  because its *background* spans edge to edge. Wrap it: a non-animated positioner
  (`position:absolute;left:0;width:1080px;text-align:center`) around an `inline-block` word with a
  `max-width`.
- **Caption band against bottom-anchored props**: anything living in the caption band's y range
  collides. Either lift the prop or push that beat's captions, keeping the bottom above y1600.

---

## When NOT to caption

- **Where a card already states the words.** Duplicate messaging reads as a bug. Cut those clips;
  the prop IS the caption. This has been reconfirmed on four separate builds.
- **Where a big lockup says the same thing.** A 96px lockup plus a caption of the same words is one
  element too many. Run the hook caption-free and let the lockup carry it.
- **Where whisper cannot resolve the word.** Rather than caption a word that cannot be confirmed,
  run that beat caption-free and let the logotype assemble on it. Stronger design, zero risk.
- **In a listicle, captions carry the predicate only.** The tool name is already a 60px lockup;
  repeating it is the chyron problem ten times over. About four on-screen words per beat.

**If a script takes decisions as argv, it has to persist them.** Mute ranges (the spans where a
card already states the words) passed on a command line and written down nowhere meant that
re-running the injector would silently resurrect deliberately suppressed captions. Fixing the
injected HTML in place was the safer option there, which is the opposite of the usual advice.

---

## Copy

- **Captions follow the creator's voice; cards follow the record.** A VO paraphrase is fine spoken
  and fine as a caption, but a rebuilt post on screen must carry the literal wording. Never wrap a
  paraphrase in quote marks against a real person's name.
- **Captions follow the script, timings follow whisper.** Whisper mishears product names constantly.
- **No em dashes.**
- **A count-up must be grammatical at every intermediate value.** "hundreds of {N} SSTABLES" read
  "hundreds of 69 SSTABLES" mid-tween. Copy around a counter has to parse at every value.
