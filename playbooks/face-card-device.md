# The floating face card

The house split-screen device. Approved by two of the three creators by name, and rejected in its
wrong form by both.

---

## The thing owners are actually reacting to

**The card is a MOVE, not a placement.** The face never cuts between sizes, it travels.

When an owner asks for "the face card / the split screen / the keyframing like vid39", the
technique underneath is that `bandOpen()` tweens the scene's `clip-path` **and** the video's
`scale` and `y` together over about 0.34s. A correct-but-static face that changes state by wiping
reads as a different, lesser video. One creator's v2 was geometrically correct and static, and he
asked for the reference by name because of the move.

---

## Measure the reference, do not describe it

`out/vid39-final.mp4` reads as "a portrait bottom-centre". The file says:

```
card       x216 to x864, y1020 to y1880
face       crown 1144, mouth 1571      (above y1600; the card box may extend below)
captions   move ABOVE the card on split beats, around y840
b-roll     always carded, never full-bleed
```

Proxy in this repo: `reference-cuts/nader-vid39-orm-short.mp4`.

---

## Do not copy those numbers

vid39's source is natively vertical with chest in frame, so its card is about 55% head. Two ports
failed by copying:

| Port | What happened | Re-solved to |
|---|---|---|
| To a 16:9 tight close-up (239px of collar, no chest) | A card with the same proportions is impossible; the head has to fill it | 560x736 at x260 to x820 / y838 to y1574, chin y1407 to 1481, worst 1545 |
| To a creator with a ~975px head against the reference's ~600px | Sliced his hair off | Card top **960**: crown clears the top edge, chin clears y1600 |

Copying 1020 would have put a chin under the like button.

---

## Implementation

### One bake, two states

**You cannot tween between two files.** The hero/card move forces a single lanczos bake at the
**hero** size, with the card as a CSS transform of those pixels. The browser's extra downscale in
card mode is a downscale of an already-sharp image and does not read.

Baking (rather than CSS-transforming the source) also means the browser never resamples the
A-roll, the solved geometry exists in exactly one place, and a "show exactly one clip" helper makes
the triple-pop class of bug structurally impossible.

### Three states

```
HERO   inset(0.1px 0.2px 0.3px 0.4px round 0.5px)
CARD   inset(<solved> round 32px)     video scale .6, transform-origin 50% 0%
OFF    collapses INTO the card's own rect, so a card-in grows from where the card belongs
```

### Keep every clip-path number non-collapsible

Browsers collapse `inset()` shorthand when serializing computed clip-path: `left == right` gives
three values, and `round 0px` is dropped entirely. GSAP interpolates the raw strings **by number
index**, so a five-number target against a collapsed four-number start shifts every later slot.

On one build that animated a 32px corner radius inside the LEFT INSET, painting a roughly 200px
dark slab during every card open and close. Hold frames were pixel-perfect. Every gate and every
beat-frame QA passed, because only transition frames broke.

**Rules:**

- Make the four insets slightly distinct (216.1 against 215.9; 0.1 / 0.2 / 0.3 / 0.4).
- Never use a 0 radius. 0.5px reads as square.
- Every state carries `round Npx`, or GSAP snaps instead of tweening.
- Verify with a monotonic seek probe reading `getComputedStyle(...).clipPath` at mid-transition
  times. A mispair shows up as a radius-sized number in an inset slot.
- **Do not pixel-scan for the dark slab.** It false-positives on dark wardrobe and furniture.

### The border

`clip-path` cannot carry a border. Put the border and shadow on a separate ring div.

---

## Card mode is a layout mode

On a split beat:

- **The caption moves ABOVE the card** (vid39 does this, and it is not decoration). Leaving it in
  the low band prints it on the jaw of the card, which is usually the exact defect the rebuild
  started from. **Drive it off the beat's mode** so it cannot be forgotten.
- Graphics own the rest of the frame with **zero overlap**. On 16:9 that is a hard gutter: solve
  card widths from it (`gutter - margins`), or a 2360px card runs under a face card at x2280.
- **A shared caption-emitting loop will reuse a stale loop variable.** One build left the beat
  pointer at the last beat from an earlier pass and every caption silently emitted in the low
  position. Index the beat from the clip inside the emit loop.

---

## What a card is NOT

**A full-width band across a person's torso is a different device and it reads as a mistake.**

> A card is a **frame**: the subject is deliberately placed inside it.
> A bottom slab is a **cover**: something has been laid over the subject.

One creator approved the card and rejected the slab in the same reel. Ink side rails on a narrow
band read to another as "weird black bars".

**Rule: on a full-bleed face, graphics either sit in self-grounded chips in measured clear space,
or they do not exist. Never a full-width ground.**

---

## Card and band size are arithmetic, not taste

A card of width `W` at scale `s` shows `W/s` source pixels across, so the coverage floor from
`playbooks/face-geometry.md` gives a second inequality for free: at `H/s` visible source rows,

```
rows <= H * 1080 / W
```

A 700×640 card has a ceiling of 987 rows: a head, always, however you nudge the crop. "Only his
head is visible" was not fixed by repositioning the card; the card had to get **narrower**
(560×700, ceiling 1349 rows) to show more of him. The same inequality run the other way sizes a
full-width band: a 1080-wide band at `s=1` shows exactly 700 source rows against a 720px
crown-to-chin, so a band that must hold a talking head **has to be narrower than the frame**, or
run to full frame height so `s` can come up (see below).

## A split (or band) half must run to the frame edge

A 960×740 rounded card floating mid-frame, correctly sized and correctly placed by every gate, is
still not a split: it is a card sitting in a frame, and the note it draws is "framing looks
weird" even though nothing measured wrong. **A split half must run full width and all the way to
the frame edge** (y1920 for a bottom half), not stop short of it to respect the reserved zone: on
a full-bleed beat his video already covers y1600–1920 and nobody reads that as a violation, so a
band may do the same. The reserved-zone rule protects his **chin and any text**, not pixels below
it.

Running the band to the true edge also fixes the size arithmetic instead of fighting it: a band
stopping at y1600 has only 740px for a 720-row head (forcing a narrower `s`); run to y1920 and the
same head gets 1140 rows at `s=1`, so the crop solves cleanly with margin on both crown and chin.
**Reaching for a smaller scale is solving the wrong end of the inequality.**

A full-bleed band also has no border to draw: its only edge is the top one, a hairline plus the
shadow it casts onto the graphics above. A `border` on a full-width element is three invisible
sides and one that matters.

## Do not card the face just to clear graphics off it

The obvious fix for "text on his face" is to card the face so graphics own the other half. It
trades one defect for another: carding empties the vacated half of the frame just as hard as the
text collision it was meant to fix. **Keep him full-bleed and put graphics only in the
measured-safe column** (from his real body reach, see `playbooks/face-geometry.md`'s
"measure the subject" section): caught here only by screenshotting the composition before
rendering, not by any gate, because a correctly-carded-and-empty half passes every check.

## Only ONE of a set of face states may change his head size

A rebuild used three states off one baked camera: BAND (full-width bottom panel), CARD (the same
pixels, clipped narrower), CLOSE (a real push-in on a hard cut, caption moved to the low band).
BAND and CARD share one camera and differ only by `clip-path`, so his head is the **exact same
size** in both: the change between them is a widen, not a resize, which is what makes two formats
safe in one cut. CLOSE is a genuine size change and is allowed to be one only because it happens on
a hard cut into a new shot. Two sizes that CUT between each other (not a hard cut, mid-scene) reads
as a bug: this is the standing lesson from vid46's short, confirmed again here.

## A vertical split is the only way to show him at native 1:1 without a punch-in

A full-width band of height H shows exactly H source rows, so his chin lands wherever the band's
height puts it: usually deep in the reserved zone unless the band runs to the frame edge (above).
A full-height **column** has no such constraint: solved from the CTA window specifically (not a
whole-take percentile: see `playbooks/face-geometry.md`), a right column at `x440–1080`, native
scale, `x=250` showed his head at true 1:1 because his head span in that window, not the take's
average, decided the column position.

## Two short windows separated by a gap

Do not card both. One film carded 8.43 to 11.83 and 13.83 to 15.83 with two seconds of
note-reading between, so the A-roll popped out, in, out inside seven seconds and the owner read it
as a bug: *"a second ago the a-roll was visible, disappeared, the next second it's there."*

**One card exit into a persistent device.** A seal took the column and held it across the scene
cut, which reads as a handoff. The device must live **outside** the scene divs or `cut()` kills it.
