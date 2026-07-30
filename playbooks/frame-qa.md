# Frame QA

**The only gate that catches the bugs that matter.** Lint, validate and inspect have collectively
passed: occluded thesis lines, elements rendered at the wrong position, dead pages, empty cards,
a document whose body had been deleted, and a mark drawn on empty space.

Run it every round. Extract a frame at every beat plus frame 0, and read them all as images.

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
grep -n "—" index.html *.srt *caption*.md
```

---

## Cadence

Expect two to three fix, render, QA rounds. **Renders are cheap.** A 40-second 1080 composition
renders in one to three minutes; never batch doubtful fixes on the assumption that renders are
slow. Five surgical rounds cost less than one skipped QA pass.

**Read your own render before handing it over.** The owner should not be your first QA pass. On
one film, a self-QA pass found two defects the client did not mention, and a client review that
finds bugs you could have found is a round spent on nothing.
