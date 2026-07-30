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
