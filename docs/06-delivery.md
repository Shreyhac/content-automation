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
link. This section is the contract, not the manual.

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

---

## 9. Close the loop

Update `creators/<creator>/HISTORY.md` with what each review round actually changed, and promote
anything reusable into `playbooks/`. A lesson that stays in a chat log gets paid for twice.
