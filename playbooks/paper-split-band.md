# The paper split band

The paper-split creator's approved 9:16 split. Graphics on paper above, face in a rounded band
below, **face on screen continuously**. Reference build: `reference-builds/paper-split-vid47/`.

They specified it by sending a frame from an earlier approved build, which is worth remembering:
when the creator references a video, go and measure that file.

---

## Geometry

```
eyebrow   y168
content   y206 to y900
caption   y940 to y996        x130 to x950, clears the like/comment rail
band      y1080 to y1920      840px, 44% of the frame
```

```css
#faceBandBg{ top:1080px; height:840px; background:var(--paper2);
             border-radius:36px 36px 0 0; }

video.band { top:380px; width:1080px; height:1920px; object-fit:cover;
             clip-path:inset(700px 0 0 0 round 36px 36px 0 0); }
             /* the visible cut IS the band's own rounded edge */
```

**Band top y1080 rather than 1150** when the note is "show the face more": it took face presence
from 45% to 91%.

---

## The constants are not portable

Third time this has been true across this system. **Re-solve the crop per take** so the head fills
the band and the chin clears y1600. See `playbooks/face-geometry.md` for the measurement pass.

vid47's solve as a worked example:

```
crop=1854:3296:36:212   →   head 430px, face centred x540.6,
                            crown y1130, chin y1560   (clears y1600 by 40px)
```

---

## Mechanics

- **Round the clip AND the band background to the same radius, and delete any straight full-width
  edge line.** That mismatch is what "the rounded edges look off" means.
- **Clip any three.js canvas to the graphics zone permanently** (`inset(150px 0 1010px 0)`). A
  loose field drifting onto the presenter's face reads as dirt on the lens.
- **A paper wipe on a paper ground is an invisible cut.** Wipe colour must contrast the scene it
  covers: a deep green works where the world is ivory.
- **Light and white brand marks vanish on paper.** Verify every mark on the actual card colour in
  one headless page before wiring them in.

---

## Pair it with one persistent object

Do not build a scene per beat in the graphics zone. **One carrier that persists, with the event
under it changing.**

On vid47 the ten tools are ONE accordion for 24.5 seconds:

- the spoken **name** opens its row to 420px and the list slides so the open row pins to the mask
  top;
- the spoken **predicate** lands the stamp on that row's real screenshot.

Two moves per beat, each tied to a specific word. That is what "the animation doesn't sync with
what we're saying" actually asks for. A card fading up while a name is spoken is not synchronised,
it is merely simultaneous.

### Solve the whole stack from one formula, every beat

```js
topOf(j, n) = j <= n
            ? j * PITCH
            : n * PITCH + OPEN + GAP + (j - n - 1) * PITCH
list.y      = -(n * PITCH)
```

Applied to all rows every beat, it cannot drift. The first build pushed rows below the open one
down and never brought them back up, so a row pushed down at beat n was still down at beat n+1 and
by beat 7 the open row was half off the mask. **Never nudge; re-solve.**

### The mask needs the right escape hatch

**`data-layout-ignore`, not `data-layout-allow-overflow`.** The `clipped_text` rule fires on the
mask element regardless of allow-overflow, which is correct for a text box and wrong for a
viewport. Marking it is the honest fix; leaving errors in the gate is not.

---

## The alternative face cadence

Where the band is not wanted, the approved listicle cadence is **FACE, GFX, GFX**: face beats at
items 1, 4, 7 and 10 plus hook and CTA, giving about 45% face share with no stretch of talking
head. The cycle is what stops a ten-item list reading as a slideshow.

Both shapes are approved. The band is current.
