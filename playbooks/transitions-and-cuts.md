# Transitions, cuts and scene windows

Read this on every build. The lead rule changes every scene boundary in the composition.

---

## Scene windows LEAD the spoken word

**The highest-value thing frame QA has ever found.**

On one listicle all fourteen scenes opened exactly on their word and faded content up from
`autoAlpha:0`. Lint, validate and inspect all passed. **The first frame of all ten tool beats was
a bare background.** The frame-0 cover rule generalises: every hard cut needs a composed frame, so
opening on the word ships one empty frame per item.

House constant:

```
LEAD = 0.20

scene data-start = word onset - LEAD      (and the previous scene ends there)
entrances        run from the same early time
wipe             start = cut - 0.20, duration 0.44   (so it peaks at the cut)
flash cut        at cut - 0.04
```

Captions, SFX and every per-beat event stay locked to the words. The entrance then happens
**under** the transition and the first visible frame is settled.

Two corollaries that bit in the same pass:

- **A three.js field must be dark BEFORE the next cut**, or it paints over the incoming scene.
  Kill it at `cut - 0.2`.
- **Flash cuts at `opacity .80` blow the frame to near-white.** Every sampled hard cut was a white
  card. **0.42 over 0.13s** reads as a punctuation mark instead of a fault.

---

## A transition needs a HOLD, not just a symmetric pass

Wipes sized symmetrically around the swap (in 0.22s / out 0.22s) put **full coverage at a single
instant**, but scene clips overlap for 0.20s by design (the lead rule above), so at that overlap
point two scenes were briefly on screen simultaneously through the panel. **The panel must cover
for at least as long as the clips overlap**: `in 0.20 → hold 0.16 → out 0.24`, with every outgoing
clip ending inside the hold.

## Entrances must finish under the wipe, not merely start under it

Leading a scene's `data-start` early (above) is necessary but not sufficient: the entrances
**inside** the clip have to be timed against the wipe too. A panel covering at `T` and uncovering
over `T..T+0.22` while the incoming scene's own elements start at `T+0.04` with 0.5–0.6s durations
uncovers onto a half-built scene.

- **Budget: everything the viewer must see has to be at or past 70% of its entrance by `T+0.22`.**
  Start entrances on the swap frame itself, not after it, and shorten them (0.34–0.50s ranges have
  worked).
- The **outgoing** element's exit must **end** at or before `T`, not start there.

## Every slam must clear its own transition

`$0` landed on the envelope's peak for "free" at 28.220s. The CTA wipe (0.42s centred on 28.480s)
starts at 28.270: the film's biggest number had 0.05s in the clear, one and a half frames. No
gate has any opinion about this; only the render sheet showed it. Moved the slam earlier (to the
stressed syllable of the preceding word) for 0.53s clear.

> **Rule: for every slam, check `t_land + 0.25s < t_nextcut − wipe_duration/2`.** A beat that lands
> inside its own transition is not a beat.

## A card exit must be a HANDOFF, and a scene without its own exit ghosts through the cut

A face card (or any full-frame element) exiting is not itself the fault if the space it vacates is
immediately filled by the next thing: the fault is **nothing filling it**, which leaves the frame
half-composed with a dead patch for a beat. Audit every exit against what occupies the vacated
region on the very next frame, not just whether the exit itself looks clean.

Separately: **the clip window ending is not an exit.** A scene relying only on its `data-duration`
running out (with the wipe expected to cover the seam) lifts the incoming scene in at partial alpha
**while the outgoing one is still at full opacity underneath**: a double-exposure. The wipe hides
the yank, it does not replace the need for one; give every scene its own exit tween even though a
transition covers the swap.

## A graphic that changes AT a join reads as a glitch, not an edit

A film built in chunks changed a lockup's state and a number's value exactly on the (invisible)
chunk boundary. Both sides were internally correct and the underlying data state matched exactly,
and it still read wrong, because a chunk boundary is a cut the viewer cannot see. **Graphics have
to carry visually THROUGH an invisible join and change on a spoken word afterward**, the same as
they would across any other continuous shot. Confirm by checking whether the film's other, correct
joins do this and the broken one doesn't: that contrast is the tell it was a habit, not a rule.

## Wipe timing is arithmetic

**Run every band symmetrically around the swap time**, with an inOut ease, and size the panel so
its midpoint position covers the canvas:

```
band runs from  t - dur/2   to   t + dur/2
```

Then `t` IS the swap frame, by construction. A first pass that had the panel arriving 0.15s after
the scene swap made the change happen in the clear.

---

## When NOT to wipe

- **Where the VO has no gap.** Retime every transition against the word list: wipes survive only
  where the gap is at least about 0.18 to 0.20s. Everywhere else becomes a flash cut. At a join
  with no gap at all, a wipe simply eats the caption it lands on.
- **Over a persistent face card.** A skewed full-canvas wipe crossing a continuously visible
  docked face reads as a glitch. Crossfade the incoming scene's **ground** under the card (0.18s)
  and hand the overlay type off with a fast rise-out.
- **In a short, more than once.** Eleven flash cuts in 40 seconds is a strobe. Allow exactly one,
  on the single biggest emphasis. Act boundaries get one consistent wipe.

---

## Wipe form and colour

- **A full-screen skewed wipe panel must be a BAND, not a wall.** A 1900px panel sweeping 4100px
  fills the entire frame with flat accent for about five frames mid-transit, which reads as a
  paint flood, and reviewers screenshot it. An 860px leading band with a full-size ink panel
  lagging to cover the scene switch reads as a streak.
- **Wipe colour must contrast the scene it is covering, not match the world.** A paper wipe on a
  paper ground is an invisible cut: both transitions read as the frame going blank until they
  became a deep green.
- **A white flash is invisible on paper.** Use an opaque ink blink (about 70ms in and out) on
  light scenes, white flash only on dark ones.
- **Every ink-blink cut needs a hard kill** (`tl.set("#cover",{opacity:0}, t+0.14)` after the
  fade), or non-linear seeking lands past it and leaves the frame black.
- **Cut to black via a clip window, not a tween.** A solid cover clip, opaque by CSS with no
  autoAlpha tween, gets its visibility hard-cut by its own `data-start`/`data-duration`. Cleaner
  than fades, and it dodges the exit hard-kill rule (a clip element cannot take that exit).
- **Impact flashes: measure the decay, not the peak.** `opacity 0.5` decaying over 0.17s is about
  six frames of grey veil, which reads as fog. About three frames (`0.38`, decay `0.08`) is the
  snap. With a locked-off camera, turn it down further: 0.22 to 0.28.
- **A hard-edged expanding ring is a bad impact device for video.** It freezes into a stray circle
  on whatever frame you screenshot, and reviewers screenshot. A soft radial bloom reads as light
  on every frame and still lands the hit.

---

## Direction

**A wipe's direction is a gaze decision.** Eating a face band from the **top** takes the subject's
eyes out of frame first, which lets a conceal start 0.18s before his gaze drops to his notes
without ever showing a downcast frame. Bottom-up would have kept his eyes visible longest and
shown exactly the frames the gaze map exists to avoid.

Otherwise: alternate direction between cuts for rhythm.

---

## Transitions that are moves

The strongest cut in this system is often not a transition at all:

- **The compact gesture doubles as the hook transition.** A full-bleed face compacting into its
  docked card in one keyframed move (scale plus clip-path, about 0.6s, slight overshoot) needs no
  wipe. Time it so the panel story is already alive the moment the paper is revealed.
- **The band swipe IS the hook.** A panel swiping down on the metaphor's word physically pushes
  the presenter into the bottom band in one gesture (panel `y:-948 to 0` power3.out 0.36s plus
  video `y:0 to 680` in the same beat). No blink, no waiting for the sentence to finish.
- **Overlay type exiting during a split transition must be DEAD before the face lands in its
  band.** A 0.26s drift exit ghosted a title across a forehead; 0.13s with a hard kill fixed it.
  **Time exits to the video's y-tween, not to taste.**

---

## Exits

- **No exit tweens except the final scene.** Transitions handle exits.
- **A slam scheduled less than about 0.25s before a covering transition never reads.** One at 9.34
  with the cover at 9.46 gave a 0.12s visible window. Stamp and strike beats want about 0.7s
  before a scene exit, not 0.45.
- **Check both covers' reveal times when inserting a flash between two transitions.** One face
  flash had only a 0.26s window between covers.
- **Verify flash beats by extracting the frame two ticks after the slam lands**, not at the spoken
  onset.

---

## Camera

Where the creator allows a rig: blurred zoom-through entrance, drift, origin-shifted micro-punches
toward whatever just activated, crash-zoom exit. Ambient layers sit **outside** the rig for free
parallax.

- **Chrome must live OUTSIDE a scaling camera.** Kickers, counters and CTA chips are siblings of
  the rig, never children, whenever it scales more than about 1.1. Elements authored at safe y have
  been thrown into the IG top band by the camera alone. Values of 1.02 to 1.07 are harmless.
- **Motion direction should be monotonic within a shot.** Punches that return to base read as a
  heartbeat: punch-and-hold on A-roll, settle then one linear push then cut on designed scenes.
- **A cheap full-comp upgrade**: a zoom-through entrance (`scale 1.045 to 1, 0.55s power2.out`) on
  every scene world plus micro punches (`1 to 1.014 yoyo 0.12s`) on impact beats. Seven lines,
  changes the whole feel.
- **"Keep the frame stable" means kill the rig, not soften it.** And confirm which surface the
  note is about: a zoom note about the A-roll does not apply to designed scenes.
