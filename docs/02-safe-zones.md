# Instagram safe zones (1080x1920)

Researched against 2026 platform guides and merged with this system's own hard-learned rules.
**These are hard gates, audited on EVERY render round, not once per project.** A donor project
carrying a violation does not grandfather it.

---

## The zones

| Zone | Pixels | What lives there |
|---|---|---|
| TOP | y 0 to 150 | Status bar, Reels wordmark, camera icon. No text above y150. |
| BOTTOM | y 1600 to 1920 | Username, caption, audio row, nav. No faces, captions or key UI below y1600. |
| RIGHT RAIL | x 960 to 1080, y 900 to 1600 | Like / comment / share / save stack. No text crosses x960 in this band. |
| LEFT | x 0 to 60 | Crop and curvature buffer. No critical text starts left of x60. Imagery may bleed. |

**Placement guidance**

- Hook and title text: **y200 to y600**. Safe across notches and Dynamic Island devices.
- Central safe area is roughly 1080x1420 centred. Keep load-bearing content there.
- Feed preview crops to 4:5 (about y285 to y1635). Frame 0 should still make sense inside that crop.
- Talking-head chin at or above y1600.

---

## Frame 0 is the cover

It must be a fully composed frame. No mid-entrance states, no offset boxes, no invisible titles.

Chromatic-split and glitch initial states are fine because they read as intentional. Half-entered
elements are not.

Two mechanics cause almost every broken cover:

1. **`gsap.from()` and `fromTo()` default to `immediateRender:true`.** An entrance scheduled at
   t > 0 parks its element in the from-state from frame zero. Cover-scene elements must animate
   position or scale only, never opacity, and be scheduled at exactly 0.
2. **A zero-duration `tl.set(sel,{opacity:0}, 0)` does not reliably paint while the playhead sits
   on 0.** Use `gsap.set()` outside the timeline, or author the state in CSS. `hyperframes lint`
   flags this as `gsap_timeline_set_initial_hide`. It is not a style nit, it is a wrong frame.

**Every hard cut needs a composed frame too**, not just frame 0. In a listicle that means one
composed frame per item; in a concatenated long-form it means every chunk's frame 0. See
`playbooks/transitions-and-cuts.md` for the 0.20s lead rule that fixes this class.

**The last frame is the loop point and it gets solved, not taken.** If the creator finishes a
line looking down, every frame at the end of that window is a bad last frame. Cut to a composed
lockup, or hold the last good frame with `tpad=stop_mode=clone`.

---

## The audit, per round

For every overlay, assert:

- `top >= 150`
- `top + height <= 1600` (including `text-shadow`: `hyperframes inspect` measures the visual box,
  so a 116px figure with `text-shadow: 0 2px 16px` occupies 151px)
- `left >= 60`
- `left + width <= 950` for anything that extends below y900, including rotation slop

Recurring traps this audit exists to catch:

- **Band headers and eyebrow chips creep into the top band.** y46, y74, y76, y80 to 88 have all
  shipped. Put them at y152 or below.
- **A camera that scales more than about 1.1 breaks safe values.** Chrome, kickers, counters and
  CTA chips must be **siblings of the camera rig, never children**. Elements authored at safe y
  have been thrown to y30 by the camera alone.
- **A `.sup.lo` bottom-anchored caption container silently breaks inline `top:` on its spans.** A
  zero-height bottom-anchored container makes `top:250px` resolve to about y1650.
- **An on-face caption span's inline `top` is relative to its container's offset.** To land at
  absolute y1300 in a container offset `top:214`, set `top: 1086`.
- **A wide slam bleeds past both edges at overshoot.** Budget: rest width x slam scale <= about
  960px. Drop the global slam start scale to 1.7 and two-line-stack the widest labels.
- **`back.out()` overshoot pushes wide elements past the frame.** Use `power3.out` near full width.
- **A scrim must run to the frame edge.** One that stops at y1680 leaves 240px of unscrimmed
  bright footage reading as a hard horizontal band.

---

## Measure the window the placement plays over, not the take

A sparse sample of a talking head measures the pose the presenter **holds**, not the pose they
move into.
vid60's chin was measured at 11 points over 29 seconds, worst case y1080, and the full-bleed
lower plate was placed at y1190 off that number. It rendered with the plate cutting across the
neck **in the CTA**, because the presenter leans toward the lens over the last three seconds and
the chin
there is at y1145. Re-measuring the CTA window alone against a 20px ruler gave chin y1145 and
collar y1280, and the plate moved to y1300.

- Measure per placement window, and always re-measure **the close**, where the presenter leans in to make
  the ask. A whole-take percentile is a description of the take, not a constraint on a beat.
  vid59's whole-take chin p97 said "no full-bleed close"; b7's own 34 samples said chin y1648,
  canvas y1465, worst frame y1474, and the close shipped full-bleed.
- **Solve the crop over the spans the presenter is visible in, not over the beat.** Five of
  vid62-short's nine beats showed them for only part of their runtime: a beat-wide median is a median over
  frames nobody sees.
- **A geometry heuristic that returns a number is not one that returns the right number.** A
  skin-mask plus width-collapse solver returned "chin y424 to y492" because it locked onto the
  presenter's glasses, which break the skin run. Sanity-check against one hand-read frame before believing
  174 of them.

## Centre on the median head position, not the midpoint of the extremes

Extremes-centring maximises the smaller margin, which is the right answer to "will the face leave
the rect" and the wrong answer to "does this look centred". One 0.4s lean dragged a vid62-short
card 55px and the presenter sat off-centre for the whole beat. The note back was "this is not
centered aligned".

**If median centring then breaches the face margin, the beat cannot be a CARD: it plays as a
BAND.** Related: a residual is a proxy. One beat failed on `RESID 138 > 130`, an inherited
threshold; measured directly, the contour swept 508 canvas px against a 560px card, 26px either
side, and at the left extreme the jaw sat at x252 against a card edge at x260. Not centrable at
any offset. Raising the threshold would have shipped the defect; measuring the thing the residual
stands in for turned the beat into a BAND, which also read better because CARD to BAND to CLOSE
escalates into the CTA instead of stepping down into it.

---

## 16:9 long-form

The Instagram zones do not apply, but the discipline does:

- Frame 0 of every chunk is a cut in the assembled film, so it must be composed.
- Anything that only appears while a stage is docked must be sized for the **docked** scale. 34px
  type inside a stage docked at 0.586 renders at 20px.
- Solve card and gutter widths by arithmetic: a card from x260 to x2620 runs under a face card at
  x2280. Width = gutter minus margins.
- A knob or label past about 60% of a rail gets `right:-8; left:auto; text-align:right;
  white-space:nowrap` with `width:0` on the knob, or it runs off the frame edge.
