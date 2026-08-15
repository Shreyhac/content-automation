# Chunked long-form

For anything over about 60 seconds. Reference build:
`reference-builds/nader-vid46-longform/` (shared architecture plus one specimen chunk).

**Chunking is the right architecture, not a workaround.** Four minutes in one composition is
unreviewable and un-iterable. A bug in one act should cost a 90-second re-render, not a
20-minute one.

---

## Layout

```
hfNN/
  assets/
    base.css        palette · six-layer ground · carrier vocabulary · face-card geometry
                    · caption band · type scale
    chunk.js        mountGround · faceCard/faceFull/hideFace/blink/cut
                    · wordRise/splitWords/digitSettle · put()
    field.js        the recurring three.js object
    three.min.js
  c1/ ... cN/       one index.html each, with an `assets` symlink to the shared folder
  chunks.json       t0 and frame count per chunk
  *.py *.sh         the toolchain
```

Split on **word onsets inside gaps of >= 0.20s** (`tools/chunking/plan_chunks.py`) into projects
of 22 to 37 seconds. Frame-exact boundaries (`round(t*30)`) make the concat lossless with `-c copy`
and identical encoder settings.

### Two traps in the shared foundation

- **`@font-face` must ALSO be declared inline in every chunk.** The static guard only resolves
  faces it can see in the document; via an external stylesheet alone it reports "font used without
  @font-face" and silently falls back in the render.
- **Do NOT duplicate the ground or the palette inline.** One round did, and editing `base.css`
  then silently did nothing.

---

## The contract with the VO

**Set `data-duration` on the ROOT composition of every chunk.**

Without it, HyperFrames derives the composition length from its longest media. A 5.57s SFX file
starting at 19.45 stretched a 22.70s chunk to 25.03s. Across nine chunks the render came out
**7301 frames against a planned 7178** (+4.1s), the mux's `-shortest` then truncated the tail,
and the end card was cut off.

`assemble.sh` verifies the frame total against the plan before it concatenates. Keep that assert:
it is how that bug was caught rather than shipped.

**But a frame-total assert does not prove freshness.** `npx hyperframes render cN` resolves its
output against the CWD, not the directory argument, so running it from the project root writes
elsewhere and the *previous* render stays "latest". That assembles a stale film with a correct
frame count and a clean exit. `cd` into the chunk first (`render_chunks.sh`), and compare render
mtime against `index.html` mtime.

---

## Never concatenate the VO

Chunk renders carry the **SFX bed only**: the A-roll `<video>` stays `muted` and there is no
`<audio>` for voice. The voice is one continuous cleaned master muxed in at assembly, so none of
the joins can produce an AAC priming gap or a click.

```
amix weights='1 0.9'  →  loudnorm I=-14:TP=-1.0
```

**And build the SFX bed beside the render, never out of it.** See `docs/05-audio-and-sfx.md`.
Reconstructing the bed from each chunk render's audio couples sound to picture, so changing one
volume means re-encoding 4K video to hear it. The payoff is that an audio-only note becomes a
30-second remux with the picture untouched.

**Concatenate the video, rebuild the audio.** Video is stream-copied so every delivered frame is
bit-identical to its chunk render. Audio is laid once across the full duration from the continuous
VO plus absolute-timed cues, because **AAC has encoder priming at the start of every stream** and
joining three of them puts a discontinuity at each boundary: exactly the shape of a "weird audio
cut" note.

## Prove the joins, then prove the film

The frame pair either side of each boundary must be identical in caption, face state and face
position, with only the intended element changing.

**Then scan every frame for the one artefact the design could produce.** On a 1057-frame film that
meant a band that is black while the composition is in SPLIT, which would read as a one-frame black
flash: zero of 1057 frames had it. Reasoning about `round` against `ceil` boundaries produced two
contradictory predictions and the full-frame scan answered it in one command. **A frame scan is
cheaper than an argument about boundary arithmetic.**

A stale baseline makes this lie: a PSNR run against an earlier probe render reported a failure that
was really a source edit made after that probe. Confirm what the baseline contains first. See
`playbooks/chunk-revision.md`.

---

## Continuity is a geometry contract

- One chunk's **last frame** and the next chunk's **first frame** share verbatim CSS for the same
  elements.
- A tile hands over as a real **skeleton** that resolves on the next spoken word in the next chunk.
- Where one chunk's last second draws the identical rail the next opens on, the join disappears.

**Frame 0 of every chunk is a cut in the assembled film.** Six of nine chunk frame-0s once cut to
a near-empty frame because content animated in from about 0.30. The field must be **composed** and
only settle. And when you compose a b-roll card at frame 0, its `<video data-start>` has to be 0
too, or the card paints as a black rectangle on the cut.

**Where no wipe can carry a join** (an act boundary landing on a chunk join with the face already
down on both sides), the ground rig gives a **light bump**: the three.js field's alpha swells over
the last eight frames of one chunk and settles over the first eight of the next, same value,
`ease:"none"` on both. Because the rig is phased off absolute film time, it is the one device that
can stitch two separate compositions.

**Animate the ground with linear, absolute-time-phased motion** for the same reason. Tween
rotation from `360*T0/P` to `360*(T0+D)/P` so a chunk starting mid-orbit resumes exactly. Anything
eased or restarted per chunk is visible at the cut. Budget for it: a permanently moving background
roughly triples the chunk bitrate.

---

## Process

- **Front-load the reversible decision.** An A-roll re-cut invalidates the chunk map, every T0,
  the captions and the whole gaze and card solve. Doing it first cost one morning; doing it after
  any build work would have cost the build twice.
- **Validate a new look on ONE chunk before mass-producing.** One chunk was built, rendered and
  read three times before the others were authored, and the type-scale finding that came out of
  that read applied to all eight. Discovering it on chunk seven would have meant re-authoring six.
- **Run `hyperframes inspect` per chunk at 12 to 14 samples and fix every error.** It catches the
  overlapping-text-block family that a previous round's owner had to find by watching: a figure
  inside its own caption, a scene never hidden riding over four later ones, a unit line landing on
  its attribution.

---

## Render economics

`-q high -w 4` runs about 4x realtime at 4K on this machine: a 23.7s chunk in about 90 seconds, a
239s pass in about 16 minutes. **4K is affordable because of chunking**, since you almost never
re-render everything.

**Pass `--resolution portrait-4k` explicitly.** Without it a 1080x1920 composition renders at
1080p, delivers a quarter of the pixels, and looks like a clean success.

**Chunking is also the only lever on videos-per-page, which is a hard machine limit rather than a
tuning knob.** 28 `<video>` elements at 4K in one page hard-reset an 8GB machine three times at the
frame-extraction stage, before any worker ran. Split to a maximum of 5 per chunk and the same film
rendered in 4 minutes. Separately, one composition stalled at the same frame with 18 videos and
with 2 (frames 746 and 743 of 1057), and collapsing seventeen B-roll clips into one pre-composed
band track did not move it: that ceiling is per-frame accumulation, not video count, and three
chunks of about 350 frames each rendered in 2 to 2.5 minutes. See `docs/07-troubleshooting.md`.

**`data-duration` gets emitted, not typed.** HyperFrames **ceils** `duration * fps`, so 4.7667 on a
143-frame chunk renders 144 frames, and rounding is not safe either because 4.2 * 30 is
126.00000000000001 in binary float. Emit `(nframes - 0.001) / FPS` and assert the count per chunk.
`playbooks/chunk-revision.md` has the arithmetic and the boundary rules that go with it.

Set `HF_DE_STALL_MS=420000`. A render dying at the same frame number repeatedly is the 60-second
watchdog killing a healthy render, not a hang. See `docs/07-troubleshooting.md`.

Prune `cN/renders` between rounds: a 4K round costs about 800MB.

---

## A staleness stamp must be taken BEFORE the work, not after

A resumable-render staleness check stamped a content hash once a chunk **finished** rendering. A
chunk takes minutes, so any edit landing during that window was recorded as if the finished render
already contained it: a chunk rendered its old timeline, a fix landed two minutes later, and the
stamp taken after both declared the stale render fresh. The assembler would have shipped it, and
every downstream frame-count check would have passed: exactly the failure the guard exists to
prevent. **Capture the hash before the work starts, write it after the work finishes.** The stamp
then describes what the renderer actually read; a later edit correctly reads as stale. Any
"is this output current?" check has this shape: fingerprinting at the end measures the wrong
moment.

A related trap in the same hashing scheme: if the hash strips only the `<audio>` **element** and
not an HTML comment sitting beside it (documenting what the cue lands on), every audio-only edit
still changes the hash and forces an unnecessary picture re-render. Strip comments too, since they
never reach a pixel, but **a change to a guard's hash function invalidates every stored stamp at
once**, so make that specific fix at the *start* of a delivery round, never mid-round.

## Beats scheduled against the wrong chunk's clock fail in two different, both silent, ways

A helper that converts an absolute film timecode to a chunk-local one is a trap at exactly one
input: **the chunk's own start time**, which every chunk uses at least once (its opening beat).
`t0 + epsilon` (a tiny floating-point remainder above zero) is "not frame 0" to a numeric
comparison and "frame 0" to the renderer, so a call meant to fire immediately silently waits for a
`tl.set` that is not reliably applied while the playhead sits exactly on 0, and a full-bleed
graphic prints across a face for one frame at the hard join.

The other direction fails differently and worse: a beat scheduled **before** its chunk's start does
not get clamped by GSAP: it **shifts the entire timeline** by the overshoot. A cue meant for
121.1s scheduled against a chunk starting at 122.372 put every tween in that chunk 1.272s late,
uniformly.

A gate that checks every scheduled position against `[t0, t0+duration]` must scan the **whole
script**, not just literal timeline-method calls: helper functions that wrap `tl.to`/`tl.set`
internally hide violations from a gate that only greps for `tl.*(`. Strip comments before scanning;
a commented-out call with a bad position still matches a naive regex.

## A cue landing exactly on a chunk join needs the join's own stored value, not a hand-typed one

Using a chunk's `data-duration` (deliberately written a quarter-frame *below* its true boundary, so
`ceil(duration * fps)` doesn't add a spurious extra frame) as if it were the chunk's **extent**
leaves a fractional-second hole at every join: a cue landing exactly there belongs to no chunk at
all and is silently dropped. Nothing catches this from frame counts or gate passes alone: the
frame-total assert still balances, because dropped cues don't cost frames. **A chunk's extent
should come from its rendered frame count**, not from re-deriving it off the duration value, and
any generator that fans a list of cues out across several chunk files should assert the total count
it emitted against the total count requested: "I emitted these" and "these landed" are different
claims, and only counting both catches the gap.

A related, quieter version: a hand-typed timecode meant to coincide with a join (`183.85` for a
join actually at `183.8503`) is not a rounding error, it is a different chunk: it lands one frame
early, on the tail of the previous chunk. Anything that must coincide with a join takes the join's
own stored value from the plan file, never a hand-copied approximation of it.

## Long-form QA finds a specific family of bug

Nine chunks, a frame at every beat, read as images. The linter passed all of them with zero errors
and every one of these was invisible to it:

- A callout printed over a chart bar. Any label inside a chart needs its y checked against the
  tallest bar's computed top.
- Two texts at the same coordinates: a "struck-out old, new" beat had both strings in the same
  row, and the composite read as a single sentence saying the opposite of the script. When a beat
  replaces text, the replacement gets its **own line**.
- A window title printed over its own traffic-light dots.
- An element that was styled and animated but **never existed in the DOM**. GSAP no-ops silently
  on an empty selector. Grep every `#id` used in the timeline against the markup.
- Two 5 to 7 second dead halves where the second card of a pair waited for its spoken word.
- **Anything that only appears while a stage is docked must be sized for the docked scale.** 34px
  type inside a stage docked at 0.586 renders at 20px, below every other label in the film.
