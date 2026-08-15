# Revising a shipped film without re-rendering it

For a change that lands on a delivered, approved cut: a client supplies real footage after ship, a
mock has to become a real capture, one beat's audio is wrong. The whole film is not the unit of
work. **Re-render only the chunks that changed and stream-copy the rest**, so every untouched
frame in the delivered file is byte-for-byte the frame the client already approved.

`playbooks/longform-chunking.md` covers building a film chunked from the start: layout, the
`data-duration` contract, continuity, the SFX bed. This file is the other case, a revision against
something already out the door, and the second half covers the harder version: a composition that
was authored as **one** file and has to be chunked after the fact.

Worked cases: vid46, vid56 and vid58 (longform-chunked Incogni dashboard retrofit, 2026-08-13) and
the fast-cut-ad build (2026-08-13).

---

## Part 1: a film that is already chunked

`assemble.sh` concatenates chunk renders with `-c copy`, so two re-renders replace eight. vid46 was
a delivered 4-minute 4K film, 2 of 8 chunks changed: 6702 frames, keyframes landing exactly on
139.233 / 168.267 / 197.467, **28.19 Mbps against the original's 28.47**.

### Check the precondition first

**The untouched chunk renders must still exist.** vid46 had all 8. vid56 kept 2 of 8 and vid58
kept 5 of 11; the rest had been deleted in a cleanup, so the same surgery cost 6 extra renders
there purely to rebuild what the delivered file already contains.

They do not have to be local. Symlink `cN/renders` at the archive and the concat reads them off
the external drive.

Where the renders are gone entirely, recover them from the delivered MP4 with the segment muxer at
the known chunk boundaries. **Recovered renders carry no `.pichash`**, so `assemble.sh` will refuse
every chunk. Stamping the untouched ones by hand is correct and safe here for a specific reason
worth stating out loud: those renders are byte-copies of the approved delivery, so their picture
cannot depend on what their HTML now says, and an SFX injector that only rewrites the `<audio>`
block changes nothing `pichash.py` looks at anyway.

### Determinism survives a version bump visually, not bitwise

An earlier note in this system claimed chunk renders were bit-identical across runs. That only
held **within one HyperFrames version.** Re-rendering an unchanged chunk after a version bump gave
identical codec, profile, level, `pix_fmt`, fps and exactly the same 876 frames, and a different
hash: **PSNR 47 dB, mean error about 1 level in 255.** That is x264 noise, not a changed picture.
A real layout difference shows as localised spikes and far lower PSNR.

**So validate a mixed-render concat with stream parameters plus PSNR, never with hashes.**

```bash
# stream params must match across every chunk before concat
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,profile,level,pix_fmt,r_frame_rate,width,height \
  -of default=nw=1 cN/renders/latest.mp4

# an unchanged chunk re-rendered: expect high-40s dB, flat
ffmpeg -i new.mp4 -i old.mp4 -lavfi psnr -f null -
```

**A stale reference is worse than no reference.** A PSNR run on the fast-cut-ad build against an
earlier probe render reported a "failure" that was really a source edit made after that probe was
rendered ("Still at it, Jon?" became "Still at it?"). Confirm what the baseline actually contains
before believing a delta.

### Verify the joins, not the film

Read the frame pair either side of every boundary. Caption text, overlay count and element
positions must be identical across the cut. That is the only thing the surgery can break; the
interiors are the approved file.

### Price the change before doing it

- **Check whether audio is coupled to picture.** `build_bed.py` lays the bed from the cue table at
  assembly and `assemble.sh` discards the chunk renders' own audio, so adding two cues on vid46
  cost seconds, not a render. An audio-only change is a **remux**, about 30 seconds, picture
  untouched. Assert it shipped: the cue count in `sfx.py` must equal the count `build_bed` reports
  (188 on vid46).
- **Measure a suspected transition fault before re-rendering it.** A handoff that "froze on a
  muddy double exposure" turned out, sampled frame by frame, to overlap for **2 frames**: a normal
  0.3s dissolve. Any dissolve looks like mush in a still.
- **Comment accuracy costs a re-render, so fix the notes before rendering.** `pichash.py` strips
  only `<audio>`, so correcting a stale figure in a CSS comment changes the hash and demands a
  fresh render. When a crop changes, update its comment in the same edit as the CSS.
- **Pre-existing faults are not this round's scope.** vid46's "$14.99 a month" numeral collides
  with its caption, and the delivered July film has the identical collision at the identical
  frame. Flag it. Do not silently re-cut an approved frame nobody asked about.

### Retrofitting real footage into an approved frame

- **Read the composition before proposing to replace anything in it.** From one frame, vid46's
  "J. Doe / Bay St / 1,240 signals" card looked like a fabricated stand-in worth swapping for
  the sponsor's real panel. It is a prop in a 7-second mechanic: the record assembles, gets priced,
  then sells down a spine to three named buyers, with matching geometry across the c1 to c2 join.
  And the swap was semantically backwards, because the real panel shows what Incogni **removed**
  under a line about brokers **collecting**. Placement is an argument, not a picture match.
- **Replacing a mock of the sponsor's own product is the highest-value retrofit available**, but
  check what the mock **encodes** first. vid58's hand-built panel carried ten invented rows with
  REMOVED / IN PROGRESS / RE-SENT chips, labels Incogni does not use, and its last row read "and
  412 more · RECURRING", which is how it carried the film's 420 claim. Safe to drop only because
  the next scene's "420+ / independently verified by Deloitte" figure lands 3.2s later.
- **Let the film's own honesty devices veto a crop.** The obvious replacement was the real
  "Removal from data brokers" table, rejected because its "Avg. resolution time" column reads
  6 / 39 / 45 / 63 days while the same frame carries the film's own disclaimer that Incogni
  publishes no interval. **Any number a crop imports has to agree with every claim already on that
  frame**, not just with the totals.
- **Crop a screen recording at 1:1 display size.** On a 3840-wide canvas a browser UI scaled down
  stops being readable: vid46's first crop put a 2670px panel in a 1380px card, delivering body
  copy at about 5px. Decide the card rect first, then crop exactly that many source pixels. Where
  the source is already a zoomed capture, scale to fit and pad with the page's own sampled
  background rather than cropping again, and give both clips in one slot the **same** rect so the
  card cannot resize across the cut between them.
- **Classify the motion before planning a beat around it.** A survey listed one recording as
  moving from 15.75 to 17.00. It does, but the movement is the capture tool's own auto-**pan**,
  and it only lands its framing on the file's last frame. Thresholding the blue input border per
  frame gave constant height 292px from 16.0 onward (a translate, not a zoom) with x sliding 1780
  to 406 on an ease, and until about t=16.75 the target card is physically off the right edge, so
  no in-bounds crop exists. That recording can only ever contribute a still. Ask whether it is
  content moving inside a fixed frame (scrollable, usable) or the frame moving over static content
  (pan or zoom, usable only at its endpoint).
- **A crop must be bounded in time as well as space, at both ends.** vid58's activity-log crop was
  verified on one frame and both edges were wrong for the frames either side. At the top the
  site's nav bar sat clipped in half across the panel at source 10.55, which is the scene's **cut**
  frame, so the first render shipped a half-cut element on a cut; the crop origin moved y280 to
  y380. At the bottom "Viewing 16 to 30 of 35" scrolls into view by about 13.3, so the clip stops
  live at 12.40 and freezes. Step the crop across the whole window and look at what scrolls in
  from each edge.
- **A clip's payoff frame must arrive with hold time left.** One interlude had its recording
  resolving to "our privacy specialists will handle it" at 14.35 while its card began fading at
  13.87: the sentence the beat existed for was never on screen. Cut so the money frame lands early,
  and let the video window run past the clip so the last frame **holds** through the fade.
- **23.976 to 30fps: map frames 1:1 with `setpts=PTS*1.251564`, do not duplicate.** The clip plays
  at 79.9% speed, invisible on a UI scroll; duplicated frames on a linear scroll are not. vid56 and
  vid58 are 23.976 films natively and needed no conversion at all.

### Gates go stale between the original build and the retrofit

Every one of these reported PASS while never measuring the new material. Ask "would this guard
fail if I broke it?" rather than trusting the word.

- `broll_guard.py` filtered on `if "broll" not in src`, so every card video outside
  `assets/broll/` was skipped. Three new clips in `assets/rec/` were never measured. Fixed to match
  the **wrapper** (a `<video>` inside a `.bcard`, depth-counted so child `.tint`/`.stamp` divs do
  not truncate the slice), not the folder name.
- `card_guard.py` skipped any element with no text, no img/svg and no background, which is exactly
  what a `.bcard` is: a transparent bordered div around a `<video>`. Card and video were both
  exempt, so it would have reported OK on a panel overhanging the card edge. With a border or a
  `<video>` counted as painting, vid56's panel had to come in from 1840px to 1828px wide to sit
  inside x2080: a real constraint the guard had never been able to state.
- Same guard, third bug: it resolved `src` against the project root. hf56 symlinks
  `cN/assets -> ../assets` so both paths work; hf58 gives each chunk a real assets dir, and a
  present file was reported missing. **Resolve asset paths the way the renderer does, per chunk.**

Numbers from the round: vid56 5844 frames, 16.34 Mbps against v1's 16.28, 53 cues. vid58 9586
frames, 1 chunk re-rendered. Every untouched chunk stream-copied.

---

## Part 2: chunking a composition that was authored as one file

The fast-cut-ad build would not render at all. 28 `<video>` elements, every one 2160x3840 at 52 to
100 Mbps, in one page: three attempts **hard-reset the 8GB M2 Air** with a blank screen. After
chunking, the whole 36.4s film rendered at 4K in **4 minutes** with the machine untouched.

**It is the video EXTRACTION stage, not the worker count.** `--low-memory-mode` auto-enables at
8GB or less and already pins one worker, which is why the crashed logs read `workerCount:1` under
a header saying "auto workers". Extraction runs *before* any frame is captured and pulls frames
from every `<video>` in the page regardless of workers; the log died on "Extracting frames from
video 28/28". The only lever is **videos per page**, and chunking is the only thing that moves it:
28 down to a maximum of 5. See `docs/07-troubleshooting.md` for the diagnostic trail.

### Split the film by generator, not by hand

Three scripts: `plan_chunks.py` (boundary assertions), `build_chunks.py` (the emitter),
`render_chunks.sh`, then the existing `assemble.sh`. Hand-editing eight copies of a composition
guarantees they drift.

**Cut on shot starts, and treat sub-frame spill as a cross-cut, not a split.** Consecutive shots
overlap 13 to 27ms. Assert the incoming shot has a higher track index and is live at the boundary,
then drop the outgoing tail from the later chunk: provably invisible.

### Ceil sets the frame count

**HyperFrames ceils `duration * fps`.** `data-duration="4.7667"` on a 143-frame chunk rendered
**144** frames, because 4.7667 * 30 = 143.001. Emit `(nframes - 0.001) / FPS`.

Rounding is not safe either: 126/30 is 4.2, and 4.2 * 30 is 126.00000000000001 in binary float,
which ceils to 127. This is the +4.1s desync from `playbooks/longform-chunking.md` in miniature,
and **only a per-chunk frame assert catches it.**

### Never hand GSAP a negative rebased position

A rebased position that goes negative is not clamped: it **shifts the whole timeline** by the
overshoot. Drop those statically, which is also semantically right, because a `.from()` that
finished before the chunk began leaves the element at its natural CSS state.

**Tweens landing past the chunk end are the opposite case and must be KEPT.** With
`immediateRender` holding the element at its from-state, it correctly stays hidden. Dropping them
is what makes late chips appear early.

**A straddle guard only sees the tween families it can parse.** The fast-cut-ad build's first
version matched `}, <literal>)` and so never checked the chip entrances (`}, t)` inside a
`forEach`) or the caption entrances (`}, t + 0.02)`, read from the DOM): two of the three families
in the file. It passed by luck. Enumerate every family, then prove the guard can fail on a deliberately bad boundary.

**The emitter has the same blind spot, and its version is worse.** It rebases only **literal**
tween positions. A `forEach` or array-computed position passes through verbatim and then fires at
the wrong absolute time in any chunk whose clock does not start at 0. The hook chips dodged this
for three rounds only because c1's `t0` happened to be 0.

**So new tween groups get written as flat literal statements**, even where a loop would be tidier.
A generated position is unrebasable by construction, and the failure is silent in exactly the
chunks a spot check does not open.

### Anything present at a boundary starts on or before it

A boundary sample can land **below** a rebased start. Film frame 1016 sampled t=1.66667 in c8 while
the outro's rebased start was 1.6667: **3e-6 short**, so neither the outgoing nor the incoming video
painted and a stale frame held for 33ms. The grid blink was the same class, an element at 8.74
against a bound at 8.7333.

**Start an incoming clip 0.2 frames EARLY when it begins exactly on a chunk bound.** The rule
generalises: anything meant to be present *at* a bound starts on or before it, never exactly on it.

**And a float on a held overlay must end inside its own chunk.** A relative y-drift crossing a
boundary is dropped in the next chunk and the element **pops 8px at the join**. The planner's
straddle guard catches literal-position floats only when their yoyo and repeat arithmetic is
representable, so keep drift cycles short and bounded rather than relying on the guard.

### The freshness-gate dance for a single-chunk fix

`build_chunks.py` rewrites all eight files for any source edit, so every chunk looks stale after a
one-line change and a naive flow re-renders the whole film.

1. **Hash-prove which emissions actually changed**: regenerate pre-fix and post-fix and compare.
2. **Re-render only those.**
3. **Then align the proven-identical files' mtimes to their renders.**

**Content proof first, mtime second, never a blind `touch`.** The order is the whole point: a
timestamp aligned before the content is proven identical is a staleness gate that has been told to
lie.

### The emitter must copy every asset reference syntax the document can contain

The fast-cut-ad build's emitter linked everything matched by `src="assets/..."`, and so never
linked a single `@font-face` file, because CSS references fonts as `src:url("assets/...")`. Chrome
silently rendered every caption in a fallback font across **two delivered cuts**; lint, validate and the
frame QA all passed it, and the owner's "is this IBM flex font?" was what caught it.

Match every reference syntax, not the one that was easy to grep. And verify the result off the
compile log, not by eye: see `docs/07-troubleshooting.md` on
`[Compiler] Embedded local font file`.

### Render settings the split does not carry for you

**`--resolution portrait-4k` is required.** Without it a 1080x1920 composition renders at 1080p
and silently delivers a quarter of the pixels. The fast-cut-ad build's first validation render did
exactly that and looked like a success.

Numbers: 8 chunks at 143/175/133/110/53/209/143/126 = 1092 frames, 2160x3840 at 30fps, 75.1 Mbps
against sources running 52.0 / 64.7 / 99.9 min / median / max, 36.400000s, 327 MB.

---

## The checklist

1. Do the untouched chunk renders exist, locally or on the archive? If not, price the rebuild.
2. Is the change picture at all, or is it audio and therefore a remux?
3. Fix comments and notes in the same edit as the CSS, before rendering.
4. Re-render only the changed chunks; stream-copy or symlink the rest.
5. Assert the per-chunk frame count, then the film's frame total.
6. Compare stream parameters across every chunk. Never compare hashes.
7. PSNR any chunk you re-rendered unchanged against a **current** baseline. High 40s dB is x264
   noise; localised spikes are a real difference.
8. Read the frame pair either side of every join as images.
9. `ffprobe` the assembled file's bitrate against the original delivery.
