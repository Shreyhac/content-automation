# Face geometry

The most expensive class of mistake in this system. Every shortcut here has cost at least one
render round, and several have cost a full rebuild.

---

## Measure with Vision, do not look

`tools/vision/` carries three small Swift tools that run over a directory of jpgs in seconds. They
beat installing cv2 or mediapipe, and pip is PEP-668 locked on this machine anyway.

| Tool | Request | Gives you |
|---|---|---|
| `crown.swift` | `VNGeneratePersonSegmentationRequest` (`.accurate`, `OneComponent8`) | The topmost mask row with a run of >= 8 foreground px **is** the crown, per frame |
| `facebox.swift` | `VNDetectFaceLandmarksRequest` rev-3, `faceContour` | Chin, and the face-centre x |
| `gaze-detect.swift` | Face landmarks | Eye-openness and contour aspect, for the gaze pass |

```bash
ffmpeg -i aroll.mp4 -vf fps=5 stills/%05d.jpg
swift tools/vision/crown.swift   stills/ > crown.csv
swift tools/vision/facebox.swift stills/ > facebox.csv
```

**Vision's face bounding box is NOT the head.** It stops around the hairline; the crown sits about
0.5x the contour height above it. Never derive headroom from `boundingBox`.

**Anchor x on the face CONTOUR midpoint**, not on the segmentation mask. The head band widens into
the shoulders and pulled one window 230px off-centre.

The cost of skipping this: one round wrote "measured, never estimated" and then estimated. Two of
three numbers were wrong, the x by 125px, which at scale .82 is 103px of visible off-centre. The
client's note was "he is not centre-aligned in the box".

---

## The safe-zone constraints

For 9:16 at 1080x1920:

```
crown_screen  >= card_top (or >= 150 for full-bleed)
chin_screen   <= 1600
```

Where `screen_y = top + src_y * scale`.

Solve for the placement, do not pick one and check it.

---

## Worked solves from this system

Keep these as examples of the *method*. **Do not copy the numbers.**

| Take | Native geometry | Solve |
|---|---|---|
| Nader, 16:9 4K | centre x1857, y793, crown 180, chin 1414, head 1228 | card `inset(440.1 180.2 440.3 2280.4 round 40)`, scale .82 per window |
| gaurav, vid47 | after `crop=1854:3296:36:212`: head 430px, centre x540.6 | band top y1080, video `top:380`, `inset(700px 0 0 0 round 36px)`, crown y1130 chin y1560 |
| shreyansh, vid42 | crown y45 to 85, eyes y540, chin y980 to 1020, head ~940px | band top y920, video top 540, scale 1.0, `inset(380px 0 0 0 round 44px)`, chin y1500 |
| shreyansh, card | head ~975px | card top **960**, hair meets card top y960, chin y1540 |
| Nader, 9:16 short | chin at y1921 of 2160 (89% down, no chest) | no full-bleed exists; band 1080x1000 at y0, or card 560x736 at x260 to x820 |

**Four distinct sets of numbers exist for the same creator.** The formula travels, the constants
never do.

---

## Measure the free BACKGROUND, not just the head (`freespace.swift`)

crown/facebox tell you where the face is. They do not tell you whether anything else can go on
screen. `freespace.swift` runs person segmentation per horizontal band and reports the widest
background run against each edge:

| band | free left | free right | background |
|---|---|---|---|
| y0–300 | 0–58 | 118–220 | 26% |
| y700–1000 | 52–84 | 0–11 | 8% |
| **y1000–1600** | **0** | **0** | **0%** |

A take where he held a prop through the whole shot had **zero usable graphics zone** below y1000,
because head, prop and gesturing hand filled the full width. That killed a full-bleed hook before
a pixel was drawn and forced the face into a band from frame 0. Run this alongside crown/facebox on
any A-roll with a prop, a gesture, or a desk in shot; it decides band-vs-full-bleed before you
design anything.

## Measure the SUBJECT, not the face box, before placing anything over full-bleed

A coupon/panel/graphic placed against the measured FACE contour still collides with a shoulder or
a gesturing hand: the face box is not a body box. Two tools that build a subject mask instead:

- **`measure_body_edge.py`**: per-pixel **temporal variance** over the window. The wall, chair,
  monitor and speakers are bolted down, so the only thing that varies is him: the mask owes
  nothing to skin tone or clothing. One placement measured "safe" against a face box had **2.9%
  of its pixels in motion** from his hand; the replacement, placed against the real reach, had
  0.0%.
- **`fullbleed_guard`** (same technique, applied to graphic-zone gutters): a face contour measured
  x1409–2407; his real reach, shoulders and gesturing hands, was **x1168 to x2704**. Every panel
  in the film had been placed over him.

The fix is never a narrower graphic in the same place; it is a graphic placed above or beside the
zone his body actually works in.

## A percentile over a whole take is a property of the take, not of the beat you are cutting

A global chin p97 measurement is real and still the wrong veto for a specific shot. Twice:

- A whole-take chin p97 at y1575/y1730 (of 2160), 25–62px of "clearance" that reads as a
  coincidence rather than a margin, correctly ruled out a full-bleed **band** across the whole
  film.
- Measured on the **one beat actually being cut** instead, chin p97 came in far higher (y1541 →
  canvas y1374, 226px of clearance; or y1648 → canvas y1465). The global figure was true and it
  was vetoing a shot it was never measuring.

**Re-measure per beat before letting a global figure veto a shot**, especially when the veto is
what makes the film worse. This is the same discipline as the gaze-safety exclusion check in
`playbooks/gaze-detection.md`: always check the raw signal against the window you are actually
using, not the summary statistic.

## Sparse sampling measures the pose he HOLDS, not the pose he moves into

A talking-head chin measured at 11 points over 29 seconds gave worst-case y1080, and a plate
placed off that number cut across his neck **in the CTA**, because he leans toward the lens in the
last three seconds and his chin there is y1145. **Measure densely inside the window a placement
actually plays over, and measure the beat where he is most likely to change: the close, where he
leans in to make the ask.**

A geometry heuristic can fail the same way from the tooling side: a skin-mask + width-collapse
solver built to automate exactly this measurement locked onto his glasses (which break the skin
run) and returned a confidently wrong "chin y424–492". **A heuristic that returns a number is not
the same as a heuristic that returns the right number: sanity-check it against one hand-read
frame before trusting it across an entire take.**

## A residual is a proxy; when it fails, measure the thing it stands in for

A planned card failed a residual-drift threshold inherited from a different take (`RESID 138 >
130`). Hand-reading both sway extremes composited into the card showed the shot was fine: he
drifts 400px right across the first 2.8s and then settles, so the card centred on where he ends up
works. **The constraint a residual stands in for is whether his face stays inside the rect this
beat shows him in. Measure that directly** (his contour swept 508px against a 560px card, 26px clear
either side at the widest frame) rather than trusting the proxy number, which would have vetoed a
real shot in one direction and shipped a real defect (a 26px-either-side sweep against a narrower
card) in the other.

## Measure the landmark the complaint literally names, not the one the API hands you

Four client notes said "framing is off" with a box round a face card. Two successive measurement
passes both said the framing was fine: one checked the Vision face **contour** (brow-to-chin,
hair excluded), the next checked the face **bounding box** (hairline). Both were wrong. Person
segmentation gave the real number:

```
contour top (brow)        y1084
face bbox top (hairline)  y 879
TRUE crown (hair)         y 439    (441px above the bbox top)
```

Under the shipped transform, the true crown landed at y76 against a card top of y440: his head was
cut off in essentially every carded frame, not the "28%" an earlier pass had computed off the
bbox. **Three successive measurements, each more careful than the last, each still measuring the
wrong landmark.** The tell was available the whole time: draw the landmark on a frame and look.
One hand-read frame settles what several rounds of arithmetic cannot.

## A static object of known geometry answers "did the camera move?" directly

Scene detection finds cuts, not gradual zooms. Face-box scale conflates a zoom with him leaning in.
Background-strip differencing conflates a zoom with a gesturing arm crossing the strip. What
actually settled it was a static object of fixed real-world geometry in the shot (here, a TV on
the wall), which gives absolute framing per frame from its edge positions on a scanline, immune
to anything the subject does. Look for one before reaching for a proxy signal.

## Three rules past "measure it"

### 1. A coverage floor

```
s >= card_height / source_height
```

A solver optimising only "head fills 66% of the card" returned 0.486 against a 0.597 floor, and
ffmpeg refused to crop it. The scaled frame has to still cover the card.

### 2. One constant per window, not a tracking curve

A smoothed follow (moving average, keyframes every 0.4s) was built to hold a swaying presenter
centred, and the client read it as a bug: *"why is Nader's frame always moving left-right, you
have added some issue."*

**A person swaying inside a still frame is normal. A frame sliding around a person is not.**

Keep the measurement, keep the veto below, and resolve it to a single `tx` per window.

### 3. A residual test that vetoes carding

Where the subject oscillates faster than a constant can cover, the residual stays large (187px on
one take). **Play those windows full-bleed instead.** Eight of 24 windows on one film.

Killing the tracking curve also changes which windows can be carded, so re-measure the residual
against the constant. And window subdivision goes with it: splitting a long window is only safe if
every sub-boundary is also a cut, or the face jumps mid-shot, which is worse than drift.

---

## Tight close-ups

**A tight 16:9 close-up does not crop to a full-bleed 9:16.** If the chin sits near the bottom of
the source frame there is no scale that works: the scale that covers the frame puts the chin
inside the UI band, and the scale that clears the band puts the chin where captions start.

Two answers, both approved:

- **A band.** Face 1080x1000 at y0, graphics zone below, captions below that.
- **A card.** Solved from the head, with a ground filling the frame around it.

**Prove any such layout by compositing one real frame with ffmpeg before writing HTML.** It costs
30 seconds and it is the only thing that catches this in advance.

**The band's foot must dissolve, and a radial will not do it.** A radial `.foot` only reaches the
centre of the frame, so the chair and wall either side get sliced clean off and the band reads as
a pasted-in rectangle. Use `mask-image: linear-gradient(to bottom, #000 0 92%, transparent)` on
the video **and on its scrim**, or the scrim outlives it. Put the mask start below the lowest chin
the solver measured in any block.

---

## Text behind the person

The device works, but it needs a **gap wider than the head at that y**. A masthead bar at a y that
crosses the crown had its word half-eaten by hair, and a matte cannot save a word whose middle is
where the head is.

- Measure the clear vertical space above the crown before committing.
- On a seated take with real headroom, move the lockup **into** that headroom rather than
  restyling it.
- On light footage where no single text colour works over everything behind it (a white wall and
  a dark framed artwork on the same line), use a **solid ink bar with knocked-out type**. Contrast
  becomes independent of the background, and the matte makes the bar read as passing behind the
  head. **Bar first, colour second.**
- A short second line can vanish completely inside the head's width. A single wide line beats
  stacked short lines under a matte subject.
- Matte the subject with `npx hyperframes remove-background <seg>.mp4 -o subject.webm
  --quality best`. QA the matte over magenta before building, and decode VP9 with
  `-c:v libvpx-vp9` before the input or ffmpeg drops the alpha and the check lies to you.

---

## Bands and cards: mechanics

- **Round the corners on the CLIP, not the element.** `border-radius` on the element box rounds
  corners that sit offscreen, so the visible cut stays sharp.
- **Every layer must agree on the radius.** A rounded clip over a square band background with a
  straight full-width edge line is what "the rounded edges look off" means.
- **Switch transform-origin only at scale 1.** An origin swap at scale != 1 jumps the frame.
- **No scale-breathing on a clipped video.** `clip-path` resolves in element space before
  transform, so any scale drags the card edge.
- **One `<video>` per face window** in a chunked build, each with its own `data-start` and
  `data-media-start`. Watch that extra wraps carrying their transform in CSS need the geometry
  change made in two places.
