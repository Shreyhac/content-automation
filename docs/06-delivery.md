# Delivery

Done last, after the file has already passed frame QA, safe zones and contrast.

---

## 1. Render settings

```bash
HF_DE_STALL_MS=420000 npx hyperframes render -q high --workers 3 --video-bitrate 16M
```

**Set the delivery bitrate at render time, not in a re-encode.** `-q high` alone gives about
6 Mbps; pushing that through a second lossy pass to raise it is worse than asking for it up front.
`--video-bitrate` and `--crf` are mutually exclusive.

Worker counts are machine-dependent. On the 8GB machine this system was built on, `--workers 2`
is the safe default and `--workers 3` to `4` works when memory is free; `--workers 4` has died
with `Runtime.callFunctionOn timed out` on all workers at about 25%.

---

## 2. Loudness

**This grammar renders hot.** Deliveries have come off the renderer at +4.0 to +4.7 dBTP: a VO
peaking at -1.0 dBFS plus 38 SFX clips sums past full scale even at correct per-cue volumes.

Two-pass `loudnorm` on the delivery, video untouched:

```bash
# Instagram
ffmpeg -i render.mp4 -c:v copy -af loudnorm=I=-14.5:TP=-1.0:LRA=9 -c:a aac -b:a 192k out.mp4
# YouTube long-form
ffmpeg -i render.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.0:LRA=9  -c:a aac -b:a 192k out.mp4
```

Check **true peak**, not just integrated loudness. And add `-shortest` if the AAC tail runs past
the last video frame.

An SFX-heavy mix measures quieter than the VO's own target, because the bed sits under the voice:
a VO normalised to -16 LUFS came out at -16.7 integrated. Re-normalise the delivery, do not chase
per-cue volumes.

### The render's own audio track is late, by a real and re-measured amount

Confirmed across several separate builds: the renderer's muxed audio track lands **behind** a
picture that is itself frame-accurate against the source. The number is the AAC encoder's priming
delay and it is not one fixed constant: measured at exactly 2048 samples (42.67ms) on some
renders and 1024 samples (21.3ms, half that) on others. **Measure it every time**, do not assume
the value from a previous project:

- **Correlate the raw waveform over a speech window, not the envelope, and not the whole file.**
  Envelope correlation over a full file gives a low-confidence peak (~1.03x the runner-up); the
  same test on the raw waveform over a ~10s speech window gives a decisive peak (10x+) at the true
  lag.
- **The reliable fix is to never ship the render's own audio track.** Take only the video stream
  from the render; build the final audio fresh (source-aligned VO + the separately-built SFX bed,
  see `playbooks/longform-chunking.md`) and mux that in. This also sidesteps needing to know the
  exact delay at all.
- Where remuxing isn't practical, `-af "atrim=start_sample=<N>,asetpts=PTS-STARTPTS,apad=pad_dur=<N/48000>"`
  before `loudnorm`, or an `-itsoffset` on a second audio input, both work once the real sample
  count is measured.

### An HDR/HLG source clip silently forces the WHOLE composition into HDR output

One 10-bit HEVC B-roll clip tagged `bt2020nc`/`arib-std-b67` (HLG) made HyperFrames auto-detect and
render the **entire** composition as `yuv420p10le`/HLG: shifting every other clip's colour,
**including untouched A-roll that had no filter applied to it**, by ~50 units on G/B versus the
source file. `ffprobe` every non-generated source clip's `color_transfer`/`color_primaries` before
compositing; if any read `arib-std-b67`/`bt2020`, either strip and re-tag to `bt709`
(`ffmpeg ... -vf format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv`)
or pass `--sdr` to `hyperframes render`: on at least one project the shift persisted with only one
of the two applied, so do both. **Diff the A-roll's rendered pixels against the source file every
round**, not just eyeball it: a 2–3% RGB delta is normal encoder drift, a 15–50 unit delta is a
colour-pipeline bug, not a grade.

### The compositing path itself shifts colour, independent of any grade applied

Measuring the same face-band crop at every stage of the pipeline (master → project transcode →
after `hyperframes render` → after a delivery pass) on more than one project shows the transcode
and delivery steps are colour-**exact**, and the shift happens entirely inside the renderer's
browser-compositing-to-encode path: roughly 10/255 on R at the high end, 3–4 on G/B (a highlight
roll-off, not a hue rotation), present even with identical `bt709`/`tv` colour metadata at every
stage. A second, distinct effect measured on another project: delivered files tagged `tv` (limited
range) against `pc` (full range) source/asset show a further **range squeeze** (R−12/G−6/B−2 in
one measurement) with zero grading filters applied anywhere in the chain. **Always measure a crop
of pure, ungraphic'd source footage** (a face band with no cards/text on it) when comparing colour
across pipeline stages: a full composed frame samples your own graphics, not his footage, and
will report numbers that look catastrophic and mean nothing.

---

## 3. Match the original file size (both Instagram creators)

**Standing rule for `shreyansharora05` and `thepmfguy`/gaurav.** A delivered file at a perfectly
healthy 8.4 Mbps looked "too small" next to the 108MB raw A-roll when compared side by side in
WhatsApp. The stated belief is "no views for low file size videos." Whether or not the platform
weighs it, this is a hard delivery requirement.

```bash
raw_bytes=$(stat -f%z "/path/to/raw-aroll.mp4")
# total kbps = raw_bytes * 8 / duration / 1000 ; subtract 192 for audio
```

Then re-render with `--video-bitrate=<N>M` at that number and confirm the delivered byte count is
within 1 to 2% of the original. Resolution, duration and content do not change; only the encode
bitrate rises.

Do the loudnorm pass after this. `-c:v copy` does not change the size.

### Hitting an exact byte count, not just an approximate one

A two-pass x264 encode cannot land on a byte by formula alone; it takes an iteration loop:

1. **Fit the bitrate by iteration, aiming ~40KB under the target.** Run pass 1 + pass 2 once,
   measure the actual output, then rescale `bitrate *= (target − headroom) / actual` and re-run
   **pass 2 only** against the same stats log (≤5 attempts). Reusing a stats log written for a very
   different bitrate is what makes an early attempt overshoot badly: regenerate pass 1 when the
   first guess is far off.
2. **Close the last few KB with an ISO-BMFF `free` box**, appended after all QA:
   `struct.pack('>I', gap) + b'free' + b'\x00'*(gap-8)`. `free` is defined as ignorable padding;
   every player skips it, `ffprobe` still reports the correct duration and streams, and decode
   stays clean. Do this last: it changes the byte count and nothing else.
3. **A near-flat, mostly-vector film can hit a quality ceiling before the byte target**, because
   there is no more real detail to spend bits on: raising the bitrate barely moves the file size
   and the gap has to be closed almost entirely with `free`-box padding. A **deterministic
   per-frame grain layer** (small canvas, frame-indexed PRNG, scaled up,
   `mix-blend-mode:overlay` at ~0.075 opacity) gives the encoder real high-frequency data to spend
   bits on, which shrinks the padding needed and also fixes the H.264 banding that large radial
   gradients cause on a dark ground: worth doing on any near-flat film regardless of the byte
   rule. **Keep the grain layer below any face card or product UI in z-order**: at the very top of
   the stack it makes a real face read as a noisy, low-quality video, the opposite of the intent.

### CRF is a quality target; it is not a delivery contract

The same `--crf` value on the same resolution and duration can land on very different bitrates
depending on content: one round measured 36.8 Mbps against a 36.25 Mbps master (a match) at a
given CRF, and the next round at the **identical CRF** landed at 24.9 Mbps because the content got
cheaper to encode (an intricate drawn scene replaced by a static screen recording). Nothing was
broken; CRF simply spent fewer bits to hit the same quality target.

**When matching a specific master's data rate is the actual requirement, pin the rate, not the
quality**: `--video-bitrate <N>M` at the master's own measured bitrate, not a CRF guessed from a
different production. Use CRF when the goal is a quality floor; use a bitrate target when the
number itself is the deliverable. And the CRF that matches one master is not portable to
another: measure the new master's bitrate first, pick CRF (or bitrate) for it specifically, then
verify the delivered file with `ffprobe` rather than assuming the last project's number still
applies.

### Rendering genuinely native at a higher output resolution

A composition authored in 1080×1920 logical px and delivered by upscaling in the encode carries the
master's byte count and dimensions with only 1080p of actual detail: a byte-match is not a
resolution claim. To render genuinely native at 2160×3840 without re-authoring geometry, wrap the
whole composition in a 2× scale:

```css
#root{width:2160px;height:3840px;}                       /* data-width/height */
#stage{width:1080px;height:1920px;transform:scale(2);transform-origin:0 0;}
```

The browser then rasterises every glyph, border and card at 4K instead of ffmpeg interpolating them
after the fact: measured **+7–9% edge energy** over the equivalent upscaled cut on code-heavy
scenes. Any pixel-based gate (safe-zone constants, viewport size assumptions) needs its zone
constants and viewport doubled and its reported values halved; nothing else in the composition
changes.

**Budget for it: 4× the pixels hits render time and delivery time both**, and delivery is the
expensive half because hitting an exact byte count at native resolution means a two-pass encode,
measurement, correction, and a pass-2 re-run, each retry a full high-resolution encode. `preset
slow` does not finish in reasonable time at 2160×3840: drop to `preset medium` and remove any
redundant `scale` filter once the composition itself is already native. **When an iteration cycle
gets several times more expensive, front-load the frame QA**: run the cheap lower-resolution pass,
fix everything visible, and only then switch to the expensive native render. **When a step is
about to take noticeably longer than the last one, say the new expected time before running it, not
after being asked**: a genuinely-running multi-minute encode with no status update reads as an
identical hang.

---

## 4. Text sweep

**Grep for em dashes before every delivery.** Banned in on-screen text, captions and published
copy, all creators, owner rule.

```bash
grep -n "—" index.html captions.srt caption-pack.md
```

Replacements: "·" for label separators ("Price · annual billing"), a comma or a colon inside a
sentence.

---

## 5. Captions and the SRT

Generate both from the same source so the burned text and the uploaded track can never disagree
(`tools/captions/build_captions.py` emits the SRT alongside the injected HTML).

- Group by <= 6 words, <= 40 characters, punctuation, or a gap > 0.45s.
- **Clamp each caption's tail to the next group's start** (`min(end+0.14, next-0.02)`) or every
  group overlaps its neighbour and lint fails.
- **Round the two edges, then derive the duration.** Rounding start and duration independently
  produces an end one millisecond past the next clip's start and the static guard rejects it.
- **Cut captions to the spoken word, not to the next beat.** A caption that outlives its scene
  contradicts the frame.
- **If a script takes decisions as argv, it has to persist them.** Mute ranges (spans where a card
  already states the words) passed on a command line and written down nowhere meant re-running the
  injector would silently resurrect deliberately suppressed captions.

---

## 6. Deliverables

```
out/
  vidNN-final.mp4
  vidNN-final.srt
  vidNN-caption-pack.md      # caption, hashtags, bracketed meta keywords, short, no emojis
```

Caption pack notes:

- If the video is a paid placement, say so in the pack: YouTube needs the paid-promotion flag.
- Credit any CC BY assets used.
- No em dashes.

---

## 7. Chunked long-form assembly

- **Set `data-duration` on the root composition of every chunk**, or HyperFrames derives the
  length from its longest media and a 5.57s SFX file stretches a 22.70s chunk to 25.03s. Across
  nine chunks that produced 7301 frames against a planned 7178, and the mux's `-shortest` then
  truncated the tail and cut off the end card.
- `tools/chunking/assemble.sh` asserts the planned frame total before it will concatenate. Keep
  that assert.
- **A frame-total assert alone does not prove freshness.** `npx hyperframes render cN` resolves
  its output against the CWD, not the directory argument, so running it from the project root
  writes to the wrong place and the previous render stays "latest". `cd` into the chunk first, and
  compare render mtime against `index.html` mtime.
- Frame-exact boundaries (`round(t*30)`) make the concat lossless with `-c copy` and identical
  encoder settings.

---

## 8. The review round

**The review tooling is not in this repo.** It lives in the production repo as `review/` plus the
`./rr` CLI, backed by a Cloudflare worker that serves the same player to a client on a private
link. This section is the contract; **`docs/08-review-workflow.md` is the manual**: read it before
running any `./rr` command for the first time on a machine, and whenever the local/hosted review
loop is behaving unexpectedly.

Two channels, and they are not the same reviewer:

| Channel | Who | How notes arrive |
|---|---|---|
| Local | The owner | `./rr out/vidNN-final.mp4`, then "Send to editor" writes `vidNN-feedback-roundN.md` |
| Hosted | The client (Nader, gaurav) | `./rr share out/vidNN-final.mp4 --name "<client>"` prints one private link; `./rr pull vidNN` brings notes and markup frames in as `source: "client"` |

Rules that cost real rework when skipped:

- **Run the inbox at the start of any session where a cut is out for review.** Client notes land
  whenever the client watches, which is often while you are already building the next thing.
- **Read every markup frame as an image.** The drawing is the note; the text is a caption on it.
- **Notes come in two kinds.** A frame note (timecode + drawing) is a local fix. A whole-video note
  ("change the theme", "SFX too loud") applies to the whole cut regardless of the timecode it was
  written at.
- **Write `status` and `reply` back for every note you address**, then push. Both render on the
  card, so the next round opens with the old notes answered. **A note left `open` reads as
  ignored**. That is how two Nader notes on vid46 sat unanswered, see
  `creators/nader/HISTORY.md`.
- Re-sharing a new render stacks as v2 on the **same** link, so the reviewer can wipe the old cut
  against the new one. Never hand-edit an existing `-feedback-roundN.md`.
- **The fix → reply/status → push → share sequence is order-sensitive, not a list of steps to do
  eventually.** Sharing a new render before writing `resolved`/`reply` into the previous round's
  `comments.json` and pushing means the reviewer's next open of the link shows all prior notes
  still flagged open: reasonably read as "my feedback was ignored," even though it wasn't.
- **A review tool's "version" can be metadata pointing at a shared file path, not an independent
  copy.** If every version row points at the same `out/<slug>-final.mp4` and a new render
  overwrites that file, every prior version silently becomes the new render too: there is nothing
  left to diff the new cut against. Confirm (or fix) that the tool copies the outgoing file to a
  version-specific path before a new one lands at the shared path.

---

## 9. Close the loop

Update `creators/<creator>/HISTORY.md` with what each review round actually changed, and promote
anything reusable into `playbooks/`. A lesson that stays in a chat log gets paid for twice.
