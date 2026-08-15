# Frame QA

**The only gate that catches the bugs that matter.** Lint, validate and inspect have collectively
passed: occluded thesis lines, elements rendered at the wrong position, dead pages, empty cards,
a document whose body had been deleted, and a mark drawn on empty space.

Run it every round. Extract a frame at every beat plus frame 0, and read them all as images.

---

## Step 0: shoot the contact sheet BEFORE the render

```bash
python3 tools/gates/guard.py hf67/guard.json        # geometry, paint, assets, voids
python3 tools/qa/shoot-sheet.py hf67/guard.json     # every beat, as an image
```

A render round costs minutes; the sheet costs seconds and answers the question no
geometry gate can: does this beat look like anything? A void, a colour that dies, a
character standing in the wrong place, a card open before its content, all read instantly
on a tiled sheet and are invisible to every structural check. This is the single most
repeated round-one defect in this system's history.

`shoot-sheet.py` reads the same JSON as `guard.py` (one beat list for both) and burns the
timecode plus your label under each tile, so a note can name the beat instead of a tile
number.

**For a delivery sheet, use `--from-clips`, not the beat list.**

```bash
python3 tools/qa/shoot-sheet.py hf64/guard.json --from-clips --cols 6 --rows 4
```

It reads every element's own `data-start`/`data-duration` and samples inside each window
(start + 0.30s, past the entrance ease, plus the midpoint for anything over 1.2s), then
labels each tile with the element it is there to check. A fixed beat grid never samples an
element whose window falls between two beats: a marker-to-marker splice once swallowed a
whole GRID scene, its tweens kept firing at nothing, every gate passed, and the beat
played as bare footage plus caption for **three delivered versions**, because the sheets in
those rounds sampled around 9.x and never inside it. Three things make its frames real, and each was found by the sheet lying first:

- **it replicates the renderer's clip scheduling.** On a plain page load every element
  with a `data-start` is in the tree at once and the sheet shows a pile, not a beat.
- **it seeks every `<video>` by hand** to `t` minus that clip's own `data-start`, and
  waits for `seeked`. Without it every beat shows frame 0 of the A-roll.
- **it replays the caption cues**, because `tl.time(t, false)` suppresses events and the
  caption is written by a `tl.call()`. See `playbooks/gates.md`.

It also listens for `pageerror`: a page that threw on load screenshots perfectly well.

### After any splice, two checks before anything else

```bash
python3 tools/gates/guard.py hf64/guard.json --ids hf64/ids.json   # before the splice
# ... splice ...
python3 tools/gates/guard.py hf64/guard.json --ids hf64/ids.json   # after
```

1. **Diff the element ID list.** A disappeared id is a disappeared beat. That is how the
   swallowed GRID scene above would have been caught on the day.
2. **Count `<div>` opens against closes.** An imbalance closes `#root` early and **browsers
   silently repair it**, so the page looks correct and the render is not. That one shipped
   as well.

Both run automatically in `guard.py`; the id diff needs the `--ids` baseline.

Doctrine and the full gate order: `playbooks/gates.md`.

---

## Extract by frame number, not by time

```bash
bash tools/qa/exact-frame-qa.sh render.mp4 tag 12 87 143 210 ...
```

One decode pass with `-vf "select='eq(n\,A)+eq(n\,B)+...'" -vsync 0`. Exact, and it costs seconds.

**Never `-ss` before `-i`.** Fast seek lands on the nearest preceding keyframe; at `-g 15` that
returns frames up to 0.4s early, which looks exactly like scene bleed, half-drawn strips and empty
beats. It invented a whole round of phantom bugs once.

**Frame numbers are the only unambiguous currency.**

---

## Where to sample

| Sample at | Because |
|---|---|
| Frame 0 | It is the cover. |
| Every scene's first frame | Every hard cut needs a composed frame. |
| Word onset + 0.05s for any slam | Sampling 0.25s later shows the settled state and hides the clipping. |
| Reveal onset + 0.3s **and** + 0.5s | A `*.in` ease keeps opacity near zero for most of a short scene. |
| Two ticks after a stamp lands | To confirm a flash beat is actually visible before its cover. |
| Every 1.0s inside a gaze window | Edge sampling passed a window map that was wrong. |
| Sub-second offsets after a parent enters | Late-entering children flicker in that gap. |
| The last frame | It is the loop point. |

---

## Contact sheets lie, at every tile size anyone has tried

- At **250px**, two frames looked like they had face ghosts bleeding through the graphics.
  Re-extracted at **420px** they were clean: the "ghost" was neighbouring tiles blurring
  together.
- So the tile size went up, and it lied again. At **420px** a working 0.36s dissolve looked
  like a tween that had never fired.
- At **300px** an arm rotation looked correct. At **2160** it was lying across the slab it
  was supposed to be reaching past.

**A sheet is for finding candidates, never for confirming one.** Re-extract the single
suspect frame at full resolution before changing any code. Two of the three cases above
would have cost a code change that fixed nothing.

---

## Reading the frames

Ask, in order:

1. **Is anything empty?** A container idle more than about 0.8s, a card open before its content, a
   bare background on a cut, a dead half of the frame. This is the single most repeated round-one
   defect in this system's history, across at least twelve productions.
2. **Is anything on the face?** Above the chin is the face.
3. **Is anything in a safe zone?** Top 150, bottom 1600, right rail x960 in y900 to 1600.
4. **Does anything overlap anything?** Two texts at the same coordinates, a label over a bar, a
   title over its own window dots, a caption on a jaw.
5. **Is anything cut off?** A slam past both edges, a nowrap line past a card, a label past a rail.
6. **Does the frame say what the VO says?** A layout that rotated past 90 degrees once argued the
   opposite of the narration. A count-up mid-tween once displayed a wrong audited figure.
7. **Is anything visible that should not be?** A stale card, a retired 3D prop still orbiting, a
   wrapper's ring floating over the cover for 30 seconds.

---

## Show the artefact, not an abstraction of it

A compression beat drew 168 cells for a 10,000-token prompt and then threw them away,
leaving an empty rectangle still labelled "10,000 TOKENS". The note was *"need better and
relevant animations here"*. The fix was to stop abstracting: the actual verbose prompt, the
actual compressed prompt, and **one answer card under an equals sign**, which is literally
what "keeping nearly the same output" claims. When a frame has to argue something, show the
real thing being argued about.

---

## Look at the assets before you build with them

- **Text chips are not brands.** 24 providers and 11 fallback-tier members rendered as
  monospace text in rounded pills drew "too shitty", twice, on two different beats. Real
  marks: `cdn.jsdelivr.net/npm/@lobehub/icons-static-svg@1.91.0/icons/<name>.svg`. The
  monochrome ones carry `fill="currentColor"`, which resolves to black inside an `<img>`:
  correct on ivory paper with no work. **Render every logo to one sheet and look at it
  before building.** A dead mark is worse than the text it replaced.
- **One film, one cast.** One round had the real Claude pixel sprite in the hook and a
  hand-drawn white robot for the limit beat. The note named the hook; the fault was two
  characters doing one job. Lift the house sprite and let it act through its body (one
  build kills it with `rotate(104deg)` plus a hue shift). Gotcha: `.mascot` is
  `position:relative`, so an unpositioned copy lands at flow origin, half off frame, and
  reads as "it did not render". Position every instance.

---

## Artefacts that are not bugs

- **A solid wipe colour is a correct transition frame.**
- **Sampling at a cut lands on an impact flash's brightest frame.** That frame is supposed to look
  washed.
- **Fast-seek near EOF gives pure-black JPEGs** for frames that render fine. Probe with an
  average-pixel check before treating a black tail as a comp bug.
- **ffmpeg's native VP9 decoder drops alpha**, so a matte composite shows the full frame and lies.
  Decode with `-c:v libvpx-vp9` before the input.
- **Subtract a contact sheet's frame x-offset before judging centring.** A "right-shifted" element
  was dead centre.
- **A perceived colour cast may be in the source.** Compare same-timestamp crops of source against
  render before touching a CSS grade: "bloody" footage turned out to be the room's warm key light.

---

## Verify numerically where you can

- **"Stable" is a pixel diff, not an opinion.** Diff a static region between two times inside one
  scene and report the column-peak shift and max luma delta. 0 to 1px and <= 9 luma is locked.
- **Determinism is a SHA diff.** Render twice, extract matched timestamps, compare. A correct
  three.js build is bit-identical.
- **A mispaired clip-path is a computed-style probe.** Read `getComputedStyle(...).clipPath` at
  mid-transition times; a radius-sized number in an inset slot is the tell. Do not pixel-scan for
  the dark slab, because it false-positives on dark wardrobe and furniture.
- **A dead page is a Playwright check.** Load for ten seconds, listen for `pageerror`, assert
  `window.__timelines` has keys.
- **Mono text width is arithmetic.** Geist Mono advances **0.609em**, not 0.600, and
  `letter-spacing` on the same element silently adds to it. Compute characters x
  (fontsize * 0.6 + letter-spacing) against the container's inner width before choosing a string:
  a 45-character query at 27px is 756px and a 644px field will not say so.
- **`text-shadow` is part of the box.** `hyperframes inspect` measures the visual box, so a 116px
  figure with `text-shadow: 0 2px 16px` occupies 151px. Stack off the shadow, not the type box.
- **Do the arithmetic for every absolutely positioned child**: `left + width <= parent width`,
  `top + height <= parent height`, at authoring time. A non-clipping parent hides nothing and the
  inspector will not flag it.

---

## Author-time greps that pre-empt whole classes

```bash
# a styled #id with no position renders at flow y0 and covers the scene above it
grep -nE '^  #[a-zA-Z0-9]+\{left:' index.html | grep -v position

# every #id used in the timeline must exist in the markup (GSAP no-ops silently)
# every literal colour in <script> after a palette change
grep -nE '#[0-9a-fA-F]{3,6}|rgba?\(' index.html

# em dashes, before every delivery
# em dashes, before every delivery. The pattern is built with printf so this
# file itself stays clean of the character it is hunting.
grep -n "$(printf '\xe2\x80\x94')" index.html *.srt *caption*.md
```

---

## Custom gates: design rules learned from building them

This system has grown project-specific gates beyond lint/validate/inspect (`card_guard`,
`band_guard`, `safe_zones`, `paint_guard`, `motion_guard`, `snap_guard`, `sched_guard`,
`asset_guard`, `broll_guard`, `audio_guard`, `cut_guard`, `facesafe_guard`, `contrast_guard`,
`css_guard`, `dead_guard`, `pii_guard`). What they all taught, past what any one of them checks:

**A gate that has never run is not a gate.** On one film, `pii_guard.py` read a file that a
different script had never written; `card_guard.py` had silently defaulted to `["c1"]`, reading as
a clean film-wide pass; `css_guard.py` was hardcoded to a chunk list from an earlier plan;
Playwright's browser binary was missing, so every DOM gate was **crashing**, not checking. A green
run and a gate that silently did nothing produce the identical console output. **Derive scope from
the plan file (e.g. `chunks.json`), never a literal, and print what a gate actually measured
(element count, chunk list) every run, not just its verdict.**

**A gate that excludes a scene is not a gate for that scene.** Two gates walked
`document.querySelectorAll('.scene')`; one chunk's hook markup did not carry that class, so the
film's first nineteen seconds, the thing every viewer sees, were never measured by either gate,
in any run, on any film. What that hid: a panel and a caption printed on top of each other,
illegible, for the entire hook. Found only by extracting frames from the finished render and
reading them. **Before trusting a gate, check what it does NOT look at.**

**A stale-looking correction table can be worse than stale: it can be inert.** A price-correction
table matched `"$420"` because that is how the token looks in a caption. Whisper emits a **leading
space** on ordinary words and none on attaching punctuation, so the actual token is `" $420"`, and
the table had never matched anything across three films' worth of reuse: read, in review, as a
safety net the whole time. **A correction table needs a test that proves it FIRES**, not just that
it exists: one assert that a known-bad input comes out corrected is enough.

**Run a negative control on every new gate; a gate that sounds like it covers a case often does
not.** A malformed CSS comment silently dropped every rule after it (browser error-recovery
resynchronises past it), and `lint`, `validate` and `inspect` all passed clean: none of them parse
the cascade. The new `css_guard.py`, which asserts every source selector survives into
`document.styleSheets`, was proved by replanting the exact defect and confirming it FAILS. Its
sibling `dead_guard.py` (looks for elements that should paint and don't) reported **CLEAN on that
same defect**, because the dropped rule was the element's only paint source, so the element has no
background/border/text and gets filtered out as "not a painting element" before the zero-area test
even runs. Two gates that sound complementary can both miss the same bug for different reasons: negative-control each one independently.

**A permissive change to a gate is not done until a planted defect still fails it.** Widening a
band-check to intersect an element's rect with every clipping ancestor (correct fix for a false
positive) also made the gate pass a **planted** violation, because the root element computed to
height 0 on a plain page load and the ancestor-clip walk clipped everything in the film to
nothing. The gate reported PASS having tested nothing at all.

**An allowlist/exemption list must be re-derived per film, from measurement: an inherited one
exempts the wrong thing.** A motion-gate allowlist carried an entry naming elements the current
build no longer has (matches nothing, silently "handles" nothing while reading as if it were
considered) and a second entry that blanket-exempted an entire scene's full duration when only a
few seconds of it were legitimately held, hiding 15.8s of genuine staleness. Grep an allowlist's
selectors against the current build before trusting it, every round.

## Reading render output: more tells

- **A near-flat render compresses to almost nothing: check the delivered file's byte count before
  extracting a single frame.** 2.1 MB for 27s where 39 MB was expected caught a whole-film bug (see
  `playbooks/gsap-traps.md`) in one second. This tell only catches "the whole film is one static
  element": it does not catch "one element among many is missing," which needs the full frame
  read.
- **Sample two distant frames' mean RGB as a five-second pre-check.** Byte-identical means at
  frame 0 and frame 210 is the same signal as the file-size tell, faster than opening images.
- **"Position is not visibility."** An element can be exactly where every safe-zone gate expects
  it and still never paint, if something else sits on top of it. A caption `div` with no explicit
  `z-index` computed to `auto` (0) under a full-bleed `<video>` at `z-index:2`: captions were
  missing for 27 of 43 seconds and every gate passed, because `lint`/`validate` check the document
  and console, `safe_zones` checks coordinates, and WCAG contrast is computed from **declared**
  colours, not from what actually composites on screen. The only test that settles it:
  `elementFromPoint` at the element's own centre, actually returning that element. Two things are
  needed to make that honest: **probe at the composition's real size** (a scaled-down viewport
  returns `null`, and `null` reads as a pass), and **replicate the renderer's clip scheduling
  before hit-testing** (a plain page load stacks every clip's DOM at identical coordinates, so the
  last one wins every hit test and reports the other 21 as failing for no reason).
- **A hole is not an overflow, and no structural gate looks for one.** A frame mid-tween, between
  one element finishing its exit and the next starting its entrance, can be a genuinely empty
  region for a fraction of a second, not static, not overflowing, not a contrast failure, not a
  snap. The only way to find it is extracting the mid-move frame and looking. Fix by deciding
  which side of the move loses ground last (a `clip-path` collapsing downward can let a face
  finish leaving before the incoming panel needs to land on it).
- **A "static for N frames, one-frame jump, returns to within ~2% of the held value" is the shape
  of a real visibility snap.** The SIZE of the jump is not the test: a legitimate
  `back.out(2.4)` entrance moves most of its travel in the first sixth of its duration and looks
  identical to a snap on a raw-magnitude threshold. Require the static-hold-before and the
  return-to-value-after; that shape alone separated real bugs from fourteen honest entrances in
  one pass.
- **Regenerating a derived artefact exposes what was hand-patched into the version it replaced.**
  Re-running a caption generator to fill four gaps surfaced bare unformatted prices (a fix table
  that only matched `$`-prefixed tokens had never fired: see the gate-design note above),
  mid-sentence capitalisation on every clip, and a missing source transcript the tooling could not
  have run without: none of which had been reported, because a hand-edited version silently
  looked fine. **When something in a build was clearly hand-patched once, regenerating it from the
  real generator is itself a QA pass.**
- **`validate` sampling a fixed small number of timestamps will eventually sample a transition,
  not a contrast problem.** Seventeen WCAG failures all landed at exactly `duration/2`: the exact
  midpoint of a wipe, where a near-black sheet legitimately covers the frame and every element
  measures 1:1 against it. Before fixing a contrast report, check whether every failure shares one
  timestamp; if so, nudge the sample point and re-run before touching any colour.
- **A comparator that keeps finding faults which evaporate on inspection is measuring the wrong
  thing.** A caption-sync check against a full re-transcription reported "three cues out of sync,"
  then two, then one: each instance was the comparator itself (transcription mis-spelling a
  proper noun, a number tokenised differently in a caption vs. a transcript, a word on a cue
  boundary attributed inconsistently). The measurement that actually settles sync is **drift**
  between anchored distinctive words at the head and tail of every beat, not string similarity.
  It found a genuine, flat 0.02s offset (half a frame) that a similarity check could never have
  resolved. Fix what you measure before lowering a threshold to make failures stop.
- **A render in flight is not a sunk cost.** A caption defect found four chunks into a 45-minute
  render was worth stopping immediately: twelve minutes lost against forty-five plus a film to
  throw away. Kill it the moment a real defect is confirmed, do not let it finish "since it's
  already running."

## Cadence

Expect two to three fix, render, QA rounds. **Renders are cheap.** A 40-second 1080 composition
renders in one to three minutes; never batch doubtful fixes on the assumption that renders are
slow. Five surgical rounds cost less than one skipped QA pass.

**Read your own render before handing it over.** The owner should not be your first QA pass. On
one film, a self-QA pass found two defects the client did not mention, and a client review that
finds bugs you could have found is a round spent on nothing.
