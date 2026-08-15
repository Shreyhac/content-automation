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
in `Click/`, wooshes in `Wooshes/`, a soft kit for paper worlds). `library/sfx/saas/` is the
`paper-split` client's own supplied pack.

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
- **When the owner supplies a pack, they expect to hear it.** Seed it into the loudest act-opener
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
| `paper-split` | 0.10 to 0.19, and the bottom half under a quiet VO |
| `longform-chunked`, after three rounds | median 0.060, ceiling 0.096, bed 0.055 |

**The ratified trajectory is halving per complaint.** 0.20 ("too loud") to 0.10 ("still very
high") to 0.060. When an owner says loud, halve it; do not trim it.

### Density

A bed of transients alone measures quiet and reads as empty. One chunk shipped at -36 dB mean
because the bed was 14 transients over 30 seconds. The fix is **sustained beds under every build**
plus transient-and-tail pairs on each hit.

Watch declared durations: a 1.00s file with a longer `data-duration` is silently truncated, so a
sustained tick under a 2.6s count has to be **chained**, not declared long. `validate` catches
short SFX in long slots. ffprobe every new SFX once.

### "Still there" converges by component subtraction, not by another cue purge

When a sound complaint survives a fix, stop editing cues and scan the **whole mix by component**.
Transient-onset scan the delivered mix, subtract every onset that matches the VO's own consonants,
and what remains names the offender.

The fast-cut-ad demo film's "typing sfx" ran four rounds this way. Round 3's offender was the **music**: the chosen bed
carried a metronomic **0.465s** percussion tick through the whole back half, with no SFX cue
involved at all, identified because its clicks fell on a strict **129 BPM** grid while the innocent
ones matched the VO's consonants 1:1. The replacement was picked by the same measurement, **30
transients against 75**, and verified to have only 4 non-VO transients, none periodic. Round 4's
offender was the click-attack reveal cues, 2ms attack.

Classify by measured envelope, never by filename or intent: audible duration plus attack time
(<= 0.13s and <= 50ms) splits a library objectively into tick against sustained, and it correctly
predicted which cue sat at the timestamp the owner flagged.

**And know when to stop measuring.** Round 5's five notes landed on the five surviving whoosh and
impact cues, the ones every acoustic measure said were not clicks: the owner meant the whole
category. See
`docs/03-quality-bar.md`.

### An audio-only change is a remux, not a re-render

`assemble.sh` discards the chunk renders' own audio and muxes the separately-built bed and VO, so
changing a volume, moving a cue or stripping the whole bed costs about **30 seconds with the
picture untouched**. Establish this before pricing any audio note: the same edit against a
picture-coupled bed means re-encoding 4K video to hear it, roughly six minutes a chunk.

Two mechanics that bite inside the mix graph itself:

- **`sidechaincompress` truncates its output at the key input's REAL data end** in this ffmpeg
  build. `apad` on the key does not stop it, with either `whole_dur` or `pad_dur`, verified at
  39.8s in isolation: main 37.8s plus key 39.8s still yielded **34.8s out**. An old comment in the
  script claimed the pad fixed exactly this, and it no longer does. The ducked bed died at about
  35s across two delivered versions and only the client's "why did the music end here" caught it,
  because the design faded the music around there anyway. That mix is now computed in numpy
  (envelope-follower duck, static bed gain, fades), where every branch is sample-verifiable.
- **Bisect a filtergraph empirically before trusting any filter's documented behaviour at a
  boundary.** Probe the graph in halves rather than reasoning about which filter should be
  authoritative.
- **Probe a delivered clip's audio before designing a handover to it.** One client outro's track
  was digital silence at −240 dBFS.
- **A client's own supplied clip keeps its own audio.** It goes into the bed at its picture window
  at unity with the music fading out underneath. A zero-SFX instruction is about *added* cues, not
  about the client's asset.

See `docs/07-troubleshooting.md` for the zero-input `apad` hang.

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

### Re-verify every audio fix with a fresh transcription

Waveform math is not proof a fix worked. On vid58's short a clipped word was fixed with an L-cut
tail sized by silence detection alone and declared fixed on the measurement. The owner came back
with "run the whisper model once again, there are a few words being cut": a fresh transcription
found the fix had stolen 124ms of the **next** beat's first word at a different join, because the
tail-length scan found no silence there and ran to its cap. A stolen word fragment still measures
as "signal present", so no envelope check can see it.

- **A dropped leading word in the re-transcription is the signal, and a pre-roll is the fix.**
  vid62's short re-transcribed as "On that specific outcome" and "The question is" where the cut
  says "And on..." and "So the question is...". Both were beat in-points landing exactly on
  whisper's word onset. Against 10ms RMS windows the signal for "So" rises about 20ms **before**
  whisper's mark: whisper's onsets run late on soft function words, so cutting on the onset shaves
  the attack. Fixed by pulling each in-point back into measured silence, 0.12s and 0.14s, both
  still clear of the previous word's end.
- Every in-point lands on a word onset with clear space in front of it and is pulled back into
  that gap by a measured pre-roll. This is not optional and skipping it is invisible until
  something re-reads the audio.
- A targeted-span re-transcription against a clean-master control is fast and sufficient. Do it
  before reporting the fix, not after being asked a second time.

### "The audio cuts weird here" is usually a script fault

Transcribe ±1.6s of the join in isolation before touching an encode. Both of vid62-short's audio
notes were clean at signal level: one cut the presenter's sentence mid-list, the other opened a beat on a
dangling "And" bridging topics 68s apart. The fixes were editorial, and they traded against each
other (+3.7s and −2.8s).

**And `afade=t=in:st=X` silences everything BEFORE X.** Meant as 45ms on one beat's head, applied
to the assembled VO it muted 46 of 61 seconds. The assembler's own loudness print caught it, LRA
4.4 to 25.6 LU. Absolute-time filters belong on the segment, not on the assembly.
