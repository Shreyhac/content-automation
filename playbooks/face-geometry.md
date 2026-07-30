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
