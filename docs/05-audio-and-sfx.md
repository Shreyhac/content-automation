# Audio and SFX

---

## The A-roll's audio

**If the creator delivers a pre-cut, graded, mixed take, ship it untouched.** Transcode format
only, `-c:a copy`. Do not loudnorm even if the mean sits below the house target: that is the
owner's mix. Two creators here deliver this way.

For a raw take, the cleanup chain that does not sound processed:

```
highpass=f=75, afftdn=nr=14:nf=-28:tn=1, adeclick, loudnorm=I=-15:TP=-1.2:LRA=9
```

Keep `nr` at or below about 15. Above that it eats consonants and sounds worse than the noise it
removed. Remux with `-c:v copy` so the video is byte-identical.

**Never concatenate the VO in a chunked build.** Chunk renders carry the SFX bed only; the voice
is one continuous cleaned master muxed in at assembly. Otherwise every join can produce an AAC
priming gap or a click.

---

## Whisper

`small` is the default. `medium` costs 40+ CPU-minutes and is not better on general speech, but
it is worth running on specific windows:

- **Hindi or Hinglish numerals.** `small` silently collapses spoken arithmetic into one token.
- **Low-probability words that change meaning.** Cross-checking two models on a p < 0.5 word is
  cheap.

Known failure modes, all of which have shipped bugs:

- **Whisper drops the "t" in "can't", confidently.** Both models agreed at p ≈ 0.98 and inverted
  an entire anecdote. **When a single word flips the meaning of a claim, ask the owner.** Captions
  follow the script, timings follow whisper.
- **Whisper can silently drop the first N seconds of a clean file.** If the first word onset is
  more than 2s into a file that `silencedetect` says is speaking, throw the pass away and whisper
  the head and the gap window separately, then merge with an offset.
- **Whisper splits numbers and hyphenates into two tokens.** `$7.99` arrives as `$7` + `.99`,
  `30-day` as `30` + `-day`. Joining the stream with a space printed "$7 .99" and opened a caption
  clip on a bare hyphen, across eleven clips, and no gate flags it because the HTML is well formed.
  A token that opens with attaching punctuation belongs to the word before it: no space, and never
  across a clip break. `tools/captions/build_captions.py` implements this as `CONT`.
- **Product names are unreliable.** SSTable becomes "SSD file", NoSQL becomes "no SQL", brand
  names come back as nonsense. **Never caption a word you cannot confirm.** One beat ran
  caption-free and let the logotype assemble instead, which was the stronger design anyway.
- **Sponsored codes: resolve against the partner URL, never against whisper.**

Word-level fixes must run on the **word stream before grouping**, not per group, or a name
straddling a caption boundary can never match.

---

## The SFX bed

### Sourcing

`library/sfx/house/` is the licensed house pack (impacts, risers in `rizer/`, clicks and keyboard
in `Click/`, wooshes in `Wooshes/`, a soft kit for paper worlds). `library/sfx/saas/` is gaurav's
own supplied pack.

**Look in the library before the internet.** Most of it is still uncurated. Where it genuinely has
no equivalent, Mixkit is curl-open: category pages carry
`data-audio-player-preview-url-value="https://assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3"`
and the preview mp3 is the full clip. Free commercial, no attribution. Pixabay is login-walled.

**Classify an unlabelled pack by measurement, not by filename.** Half of a supplied pack arrived
as "sfx 4.mp3". Band energy plus envelope shape sorts them reliably: low-dominant with fast decay
is an impact, high-dominant with fast decay is a click, a rising envelope is a riser, flat across
more than 1.5s is a sustained texture (which must then be capped as a bed, not used as a
transient). Two `volumedetect` passes over band-filtered copies plus first-half against
second-half means sorts a pack in a minute.

### Curation

**Normalise the pool once, not the volumes per cue.** Library files arrive at wildly different
levels and several carry 20 to 80ms of digital black, which lands the transient late against its
word. Peak-normalise to -3 dBFS and trim the head so `data-volume` means the same thing
everywhere. Creeping loudness across rounds is usually level-chasing.

**Check for byte-identical duplicates.** One "17 SFX" bed was really 15: two pairs were the same
file under two names, which is why perceived variety was far lower than the count suggested.

### The variety rule

**Audit a bed by SHARE, not by file count.** "You're only using two or three SFX" was said about a
bed with 17 files and 236 placements, and it was correct in the way that matters: four files were
45% of every hit.

- Cap any single file at about **8.5% of placements**, enforced **per chunk**. A film-wide
  rotation can satisfy the cap globally and break it locally.
- Rotate four to five samples per gesture class.
- When the owner names a sample as weird, **retire it, do not re-time it**.
- **When the owner supplies a pack, he expects to hear it.** Seed it into the loudest act-opener
  hits and let it carry the majority of placements (55% on one film, 80% on another). Fold it in
  by class-matched **substitution**, taking over existing cues from the most-repeated file in the
  same class, never by inventing new beats.

`tools/sfx/sfx.py` is the single source of truth for a bed and refuses to inject one that breaks
the share cap, the median, the ceiling or the retired list. Put the enforcement in the tool.

### Volumes

**Per creator, relative to their own mix.** A creator who self-mixes at -24 dB mean is overpowered
by the house range.

| Context | Band |
|---|---|
| House default | 0.16 to 0.34 |
| Gaurav / thepmfguy | 0.10 to 0.19, and the bottom half under a quiet VO |
| Nader, after three rounds | median 0.060, ceiling 0.096, bed 0.055 |

**The ratified trajectory is halving per complaint.** 0.20 ("too loud") to 0.10 ("still very
high") to 0.060. When an owner says loud, halve it; do not trim it.

### Density

A bed of transients alone measures quiet and reads as empty. One chunk shipped at -36 dB mean
because the bed was 14 transients over 30 seconds. The fix is **sustained beds under every build**
plus transient-and-tail pairs on each hit.

Watch declared durations: a 1.00s file with a longer `data-duration` is silently truncated, so a
sustained tick under a 2.6s count has to be **chained**, not declared long. `validate` catches
short SFX in long slots. ffprobe every new SFX once.

### Build the bed beside the render, never out of it

`tools/sfx/build_bed.py` lays the same cue dict the compositions use onto one continuous timeline
(absolute time = chunk `t0` + local cue time). Reconstructing the bed by extracting each chunk
render's audio couples sound to picture: changing one volume then means re-encoding 4K video to
hear it, about six minutes a chunk.

Validate the decoupled bed against a render's own audio once (mean within 0.1 dB, identical peak).
That also proves `data-volume` is linear and the chunk offsets are right. Audio iteration then
costs seconds.

**Never QA a chunk silent.** `tools/chunking/preview.sh` muxes the real VO under any chunk and
prints the bed's mean and peak.

---

## Audio QA

- `volumedetect` for mean and max. Mean around -16 dB, not -91, proves the VO mixed in.
- `astats` for the truth about peaks. A `max_volume 0.0 dB` that looks like clipping can be a
  single transient: check `Flat factor` (0.000) and `Abs Peak count`.
- **Prove the SFX bed in a VO gap, not overall.** Mean barely moves because SFX sit under the
  voice by design. In a silent gap the delta should be clearly positive.
- Phase-cancellation subtraction does **not** work to verify a bed: the AAC re-encode destroys
  phase alignment. Compare per-window RMS instead.
- A 20ms envelope lag at r ≈ 0.975 is AAC priming, under one frame at 30fps. Do not chase it.
