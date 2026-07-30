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
volume means re-encoding 4K video to hear it.

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

Set `HF_DE_STALL_MS=420000`. A render dying at the same frame number repeatedly is the 60-second
watchdog killing a healthy render, not a hang. See `docs/07-troubleshooting.md`.

Prune `cN/renders` between rounds: a 4K round costs about 800MB.

---

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
