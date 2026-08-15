# Delivery

Done last, after the file has already passed frame QA, safe zones and contrast.

---

## 1. Render settings

```bash
HF_DE_STALL_MS=420000 FFMPEG_ENCODE_TIMEOUT_MS=3600000 PRODUCER_ENABLE_CHUNKED_ENCODE=true \
  npx hyperframes render -q high --workers 3 --video-bitrate 16M
```

**Set the delivery bitrate at render time, not in a re-encode.** `-q high` alone gives about
6 Mbps at 1080 and **15.5 Mbps at 4K, roughly half what the creator's phone writes**; pushing that through a
second lossy pass to raise it is worse than asking for it up front. `--video-bitrate` and `--crf`
are mutually exclusive.

**The delivery contract is the master's resolution AND the master's bitrate**, measured, both
verified with `ffprobe` on every render round. `docs/03-quality-bar.md` carries the evidence: the
84% sharpness loss from a downscaled asset, what `-q high` actually picks, and why CRF cannot be a
delivery contract. The operational form:

```bash
# 1. measure the master, every project, before choosing anything
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,bit_rate,r_frame_rate -show_entries format=duration,size \
  -of default=nw=1 "$MASTER"

# 2. render at that number, pinned
npx hyperframes render --resolution portrait-4k --video-bitrate <master_Mbps>M -f 30

# 3. verify the delivered file against the master, not against last project's number
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,bit_rate -of default=nw=1 out/vidNN-final.mp4
```

`--resolution portrait-4k` is not optional on a 4K project: without it a 1080x1920 composition
renders at 1080p, delivers a quarter of the pixels, and looks like a success.

Delivered numbers on record, for calibration: vid59 38.4 Mbps against a 43.9 Mbps master (round 1
shipped 26.7); vid60 v5 28.3 Mbps against 28.0; vid61 36.8 Mbps against 36.25; vid62 37.18 against
32.78; vid67 38.28 against 33.15; the fast-cut-ad demo 75.1 Mbps against sources running
52.0 / 64.7 / 99.9 min,
median and max. **The number to aim at comes from the source in front of you.**

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

**This is the one colour fault that breaks the never-grade rule without anyone applying a grade.**
The A-roll has no filter on it, nobody touched it, and it still ships shifted, because a single
imported B-roll clip changed the output colour space for everything. `docs/03-quality-bar.md` says
never grade the creator's footage; this is how it happens by accident. `ffprobe` the colour tags of every
non-generated clip at intake, not at delivery.

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
across pipeline stages: a full composed frame samples your own graphics, not the creator's footage, and
will report numbers that look catastrophic and mean nothing.

---

## 3. Match the original file size (both Instagram creators)

**Standing rule for both Instagram creators, the `card-reel` and `paper-split` templates.** A delivered file at a perfectly
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

### Pin the rate, not the quality

`docs/03-quality-bar.md` has the measurements. Operationally: use CRF when the goal is a quality
floor, and `--video-bitrate <N>M` at the master's own measured bitrate when the number itself is
the deliverable. Never carry a CRF value across projects, and never call a file delivered until
`ffprobe` has been run on it against the master.

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
EMDASH=$(printf '\u2014')     # zsh; the literal character never enters this file
grep -n "$EMDASH" index.html captions.srt caption-pack.md
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
  vidNN-caption-pack.md      # paste-ready blocks only
  docs/<Payload-Title>.docx  # only when the script says "comment X and I'll send you Y"
```

**Verify each of these with `ls` and `ffprobe` on the real path.** Spotlight indexing is disabled
on this machine (`mdutil -s /System/Volumes/Data` reports "Indexing disabled"), so Finder Recents
and `mdfind` will never surface a file written since it was turned off: `mdfind -name "vid66"`
returns nothing for files that exist and decode fine. Hand the owner the folder with `open <dir>`
rather than telling them to scroll a Spotlight view. Re-enabling needs the owner's password and a
full reindex that grinds the disk, so flag it as their call rather than running it.

### Instagram caption practice: no hashtags

This changed and the old guidance in this system was wrong. Researched 2026-08-12.

- **No hashtags at all.** Mosseri, July 2026: hashtags are a *context* signal, not distribution,
  and Instagram removed hashtag-following in December 2024. An early pass cut 15 tags to 4 on the
  "still useful for context" line and the owner pushed back twice, *"you just said hashtags are not
  relevant then why to use them"*, and that was right. The keywords are already in the caption body,
  so `#claudecode` under a caption whose first sentence says "Claude Code" repeats a signal rather
  than adding one. **Default to none**, and justify any topic tag against what the body already
  says.
- **The caption body is the ranking surface.** Instagram has real keyword search and reads the
  caption, so the primary keywords go in the **first two sentences**.
- **Only about 125 characters show** before "... more". The hook and the keyword both have to fit
  inside it. Measure the first line, do not eyeball it.
- **Sends per reach is a top-3 ranking signal** (Mosseri, January 2025), alongside watch time and
  likes per reach. The caption has to be worth DMing to a friend, which means **putting the actual
  commands and steps in it** rather than withholding them behind the comment trigger.
- **Comment-trigger CTAs beat "link in bio"** (one vendor dataset: 444 against 293 average reach).
  Keep the mechanic and phrase it as a real deliverable: "like if you agree" phrasing trips the
  engagement-bait classifier. And the CTA converts on topic strength, not on the mechanic, see
  `playbooks/scripting-and-research.md`.
- **The creator's own first comment should be a sentence, not an emoji.** Multi-word comments and reply
  threads weigh more. Reply inside the first hour.

Caveat on all of the above: it is secondhand reporting of Mosseri plus agency blogs, not a Meta
spec. The 125-character preview is solid; the specific reach numbers are directional. Re-check
before treating it as current.

### The caption pack is paste-ready only

The verbatim note on a pack that opened with a researched "what changed and why" section, a character-count
analysis of the preview cutoff, posting tips and a sources list: *"in the md file just give
captions or any other stuff that needs to be there on my video, no other jargon please."*

**It is a clipboard, not a report.** The creator opens it on a phone while posting, and anything
that cannot be pasted is in the way. The file contains only paste-ready blocks:

- two or three caption options
- the comment trigger
- bracketed meta keywords
- the creator's own first comment

No preambles, no rationale, no character counts, no source links, no emojis unless asked. The
research still happens and still shapes the writing; it goes in the chat message or in
`vidNN-breakdown.md`.

Two things that do belong in the pack because they are facts needed at posting time: **say so if
the video is a paid placement** (YouTube needs the paid-promotion flag), and **credit any CC BY
assets used**. No em dashes.

### The CTA document is a required deliverable at first delivery

Any time the script's CTA is "comment X and I'll send you Y", the payload `.docx` ships **alongside
the caption pack, at first delivery, without being asked**. On vid66 the on-screen CTA was "comment
APPLE and I'll send you the skill", the video and caption pack were delivered, and the owner had to ask
"is the shareable doc ready for this?" before it existed. Treating it as optional makes the CTA a
promise with nothing behind it.

Build it with `tools/deliver/make_cta_doc.py`. What the document has to contain:

- **Every claim sourced live** (repo API, npm registry, docs), the same way the video's claims were
  verified, never from memory.
- **A "what the reel says that this doc corrects" section.** The VO overstates something more often
  than not: see `playbooks/scripting-and-research.md`. vid67's doc leads with the fact that the
  reel's "never touching the terminal" claim is false.
- **What the video had no room for**: prerequisites, scope limits, cost, and a manual path for
  anyone who will not run the one-liner.

House format, matching the sixteen generators already on disk: Letter, 1.25in side margins and 1in
top and bottom, Calibri 11pt body, 28pt bold title, 16pt bold accent headings, Consolas 10.5pt
code, `space_after` 8pt, line spacing 1.15. Colours `INK #1A1A17`, `MUTE #6E685C`, terracotta
accent `#B24A32`. Section shape that works: title, one paragraph of framing, "two things to know
before you start", "setup, exactly" (numbered, with code), "what you end up with", the undocumented
extra, "good first agents", "fair warnings", then the repo line and a license / created /
verified-date footer. **No em dashes**, owner rule, same as everywhere else.

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

**The review tooling is vendored at `tools/review/`**: the `rr` CLI, the local frame.io player, and
the Cloudflare worker that serves the same player to a client on a private link. This section is
the contract; **`docs/08-review-workflow.md` is the manual**: read it before running any `rr`
command for the first time on a machine, and whenever the local or hosted review loop is behaving
unexpectedly.

Two channels, and they are not the same reviewer:

| Channel | Who | How notes arrive |
|---|---|---|
| Local | The owner | `./rr out/vidNN-final.mp4`, then "Send to editor" writes `vidNN-feedback-roundN.md` |
| Hosted | The client (`longform-chunked`, `paper-split`) | `./rr share out/vidNN-final.mp4 --name "<client>"` prints one private link; `./rr pull vidNN` brings notes and markup frames in as `source: "client"` |

Rules that cost real rework when skipped:

- **Run the inbox at the start of any session where a cut is out for review.** Client notes land
  whenever the client watches, which is often while you are already building the next thing.
- **Read every markup frame as an image.** The drawing is the note; the text is a caption on it.
- **Notes come in two kinds.** A frame note (timecode + drawing) is a local fix. A whole-video note
  ("change the theme", "SFX too loud") applies to the whole cut regardless of the timecode it was
  written at.
- **Write `status` and `reply` back for every note you address**, then push. Both render on the
  card, so the next round opens with the old notes answered. **A note left `open` reads as
  ignored**. That is how two client notes on a `longform-chunked` film sat unanswered, see
  `templates/longform-chunked/HISTORY.md`.
- Re-sharing a new render stacks as v2 on the **same** link, so the reviewer can wipe the old cut
  against the new one. Never hand-edit an existing `-feedback-roundN.md`.
- **`rr share` caps at 2 GiB**, which is about 46 Mbps on a six-minute film. Over that, the
  deliverable and the review copy are two different files. See `docs/08-review-workflow.md`.
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

Update `templates/<creator>/HISTORY.md` with what each review round actually changed, and promote
anything reusable into `playbooks/`. A lesson that stays in a chat log gets paid for twice.
