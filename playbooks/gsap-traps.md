# GSAP and HyperFrames traps

Every entry here cost at least one render round. Most passed lint, validate and inspect.

---

## Initial state and the cover frame

**`from()` and `fromTo()` default to `immediateRender:true`.** An entrance scheduled at t > 0 parks
its element in the from-state from frame zero. That breaks the Reels cover, and the invisible
geometry still trips the inspector.

**A zero-duration `tl.set(sel,{opacity:0}, 0)` does not reliably paint while the playhead sits
exactly on 0.** It worked in one chunk and failed in two others in the same film. `hyperframes
lint` flags it as `gsap_timeline_set_initial_hide`. It is not a style nit, it is a wrong frame.

> **Use `gsap.set()` outside the timeline, or author the state in CSS, for every initial hidden
> state. Keep `tl.set(...,t)` for every t > 0.**

One blanket `gsap.set([...selectors], {autoAlpha:0})` block kills the entire premature-reveal
defect class in one place.

**But a blanket hide-guard creates a new failure mode: an element with no reveal tween.** One
element driven only by a `textContent` onUpdate was parked hidden by the guard and never revealed,
so the typing ran invisibly for 3.4s, and lint, validate and inspect all passed. **After adding a
hide-guard, diff the guard list against the entrance tweens.**

**Cover-scene elements must animate position or scale only, never opacity, and be scheduled at
exactly 0.** The framework hides any clip whose `data-start` > 0 at frame 0, so `data-start="0.02"`
also hides a cover element. Use `data-start="0"` with a plain `tl.set(...,0)` instead of an
entrance, and re-slam on the true spoken onset.

---

## Late children

- **A non-clip child entering more than about 0.3s after its scene's start is visible for the
  entire scene, then re-pops.** It needs an explicit hide. This is the animation-side sibling of
  the `position:absolute` bug.
- **`immediateRender:false` hides NOTHING before the tween.** Every late entrance needs its own
  hide at time 0.
- **A `fromTo({autoAlpha:0},...,{immediateRender:false})` on a child whose PARENT is already
  visible** renders visible from parent entry, blinks off at its tween start, then fades in. **The
  parent's hide does not cover the child after the parent enters.** Hit at least seven times.
- **Any child that animates later than its wrapper's reveal needs an explicit `tl.set(opacity:0)`**,
  or you get a one to two frame pop that is invisible in the gates.

Once you find one, **audit every scene, not the one that bit you.** One build found the same gap in
six other scenes, up to 0.4s of pre-visible content each.

---

## fromTo semantics

- **`fromTo` IGNORES from-only props.** `fromTo(el,{clipPath:A,autoAlpha:1},{clipPath:B})` never
  applies the autoAlpha. **Every prop you need applied must appear in the TO vars.** Hit at least
  seven times, including a tower roof that simply never rendered.
- **Count-up elements leak their hardcoded HTML before the tween starts.** Author the DOM default
  as the **starting** value; the proxy tween owns the rest. Seeking fires `onUpdate` at progress 0,
  so an end-value DOM shows the wrong number on every pre-tween frame.

---

## Transforms

- **A CSS `transform` on an element GSAP also transforms is silently discarded.** GSAP rewrites the
  whole transform, so `transform:scale()` or `transform:scaleX(0)` in CSS vanishes and the element
  renders as clipped fragments. **Set the initial pose via `tl.set(...,0)`**, not CSS. Lint catches
  this as `gsap_css_transform_conflict`.
- **A rotated strike-through must set its rotation in the SAME tween state it animates**, or the
  scaleX-from-0 reveal fires before the transform applies and the bar flashes horizontal.
- **`transformOrigin` in px on an SVG `<g>` is measured from the bbox corner, not user space.** It
  threw a whole gate across the frame and put a stray ring 600px from where it belonged. Use
  `svgOrigin:"540 1120"`, or avoid the transform (an `attr:{r}` pulse worked).
- **Switch transform-origin only at scale 1.** An origin swap at scale != 1 jumps the frame.
- **Tween x/y transforms, never left/top.** Lint flags `gsap_non_transform_motion`.
- **`letterSpacing` tweens are a hard lint error.** They snap to integer device pixels under the
  seek-by-frame capture engine. Replacements: a uniform tracking pulse becomes `scaleX`; a
  per-letter spread-in becomes spans with function-based `x:(i)=>(i-mid)*N`.

---

## clip-path

- **It will not interpolate with `round Npx` present inconsistently.** Every state must carry
  `round Npx` in the same format, or GSAP snaps instead of tweening. A plain `inset()` tween works
  and the element's CSS `border-radius` still renders.
- **Browsers collapse `inset()` shorthand when serializing computed clip-path.** `left == right`
  gives three values and `round 0px` is dropped, so GSAP's number-index interpolation mispairs
  every later slot. Keep all four insets slightly distinct and never use a 0 radius. Full detail
  in `playbooks/face-card-device.md`.
- **A clip-path end state clips overflowing children.** A nowrap line wider than the clipped card is
  cut at the card edge even after the reveal finishes.
- **`clip-path` resolves in element space BEFORE transform**, so any scale drags the card edge.
  Either drop a breathing tween or re-solve the clip per scale value.
- **`autoAlpha` on a clip element trips `gsap_animates_clip_element`.** The framework owns clip
  visibility. Full-frame transition overlays must animate plain `opacity`, with `opacity:0` in CSS
  instead of `visibility:hidden`.

---

## Exits and hard kills

- **An exit fade touching a clip boundary needs a literal `tl.set(sel,{autoAlpha:0},end)`.**
- **The linter wants the kill's selector to match the exit tween's element list as ONE combined
  string**: `tl.set("#a, #b, #c", {autoAlpha:0}, t)`. Per-element sets at the same time are not
  recognised, and neither is an array form.
- **It false-positives on a loop-scoped `tl.set(el,...)`**, because the static pass only recognises
  literal string selectors. Confirm by frame QA that no stale cards survive.
- **A clip element cannot take the exit hard-kill.** Put a gradient scrim on an inner non-clip div
  and tween that.

---

## Timing and easing

- **Never `*.in` on anything whose legibility is the point.** `power4.in` over 0.26s kept a product
  name's opacity near zero right up to its transition, so the most important beat rendered blank.
  A slam or reveal must front-load opacity: `back.out` or `power3.out`.
- **Keep a value and its meter in the same ease family.** A counter at `power2.out` against a bar at
  `power2.inOut` visibly disagreed mid-animation. Check it by comparing the fraction shown against
  the fill fraction in one frame.
- **`back.out()` overshoot can push a wide element past the frame.** Use `power3.out` near full
  width.
- **An effect's duration must fit inside its cadence.** Moving a pulse from every-other-step to
  every-step with an unchanged duration made consecutive tweens fight over the same property.
- **Typing and fill animations must finish before the scene's fade-out starts**, not before its
  clip end. Sample the last-line frame, not the card entrance.
- **A second typewriter tween on the same element restarts from index 0.** Use a `typeFrom(sel,
  text, startIdx, t0, dur)` helper that resumes from the existing prefix, and `clearAt()` the
  source buffer when typed content moves into a "sent" bubble.
- **Character hops must be scale pops, not y tweens**, or a second y tween collides with a
  continuous bob loop (`overlapping_gsap_tweens`).
- **Never include self-animating elements in a group dim.** A pulse that ends each cycle at
  opacity 0 gets *raised* to the dim value by `autoAlpha:0.2`. Dim containers; stop per-element
  loops before the beat.

---

## HyperFrames framework

- **Every media element needs an `id`.** Without it `<video>` renders FROZEN and `<audio>` renders
  SILENT. Lint catches it as `media_missing_id`, and it would otherwise ship a whole SFX bed as
  silence.
- **A `<video>` with `data-start` cannot be nested inside another element with `data-start`.**
  Inspect says it plainly: "video will be FROZEN in renders." Put the timing on the `<video>`, leave
  the styled wrapper untimed, and gate the wrapper's `autoAlpha` by hand.
- **Stacking follows DOM order, not `data-track-index`.** Move the element *after* the thing it must
  sit on top of.
- **A styled `#id{left;top;width;height}` with no `position` renders at flow y0.** The single most
  repeated defect in this system. Grep for it at author time.
- **A non-clip wrapper renders its own decoration for the entire composition.** Any wrapper carrying
  a ring, glow, border or backdrop needs its opacity switched on and off with the clip it frames.
- **Text on a z-indexed card needs its own higher z-index.** A sibling with `z-index:auto` loses to
  any positive-z sibling regardless of DOM order.
- **A background wash never lives on the element that hosts scene text.** Put washes on their own
  track below the video layer, or they occlude the video and nothing overflows so inspect reports
  zero issues.
- **An untimed wrapper around a timed `<video>` stays on screen as an empty rectangle** when the
  clip window ends. Cut every b-roll clip to cover the full on-screen life of its card.
- **A big card needs a CSS-hidden initial state** (`visibility:hidden;opacity:0` plus `fromTo`), or
  `gsap_fullscreen_overlay_starts_visible` fires and it covers early frames.
- **DOM measurement inside a GSAP callback is seek-order dependent**
  (`gsap_callback_dom_measurement`). A caret positioned with `el.offsetWidth` renders wrong in a
  parallel render. Use a monospace face and compute `left + k * (fontSize * 0.6)`.
- **Never place a marker by load-time `getBoundingClientRect` inside FLOW text.** Wrap at measure
  time is not wrap at render time, and the mark lands a line low. Put the mark *inside* the phrase
  span (`position:relative;white-space:nowrap` on the span, `position:absolute;inset:-8px;
  z-index:-1` on the mark): zero measurement, immune to font metrics.
- **A marker or underline over a screenshot must be `mix-blend-mode:multiply`**, or it paints over
  the text it highlights.
- **A mark inside innerHTML that repaints per frame is lost by GSAP.** Keep it as a sibling
  absolute div, or sweep only after the stream's final paint.
- **`visible_markup_comment` false-positives on literal `path/*.md` on-screen text.** Encode the
  asterisk as `&#42;`.
- **Do not set `className` from the timeline.** Tween `color` and svg `fill` directly.
- **Leave 0.02s gaps between same-track clips**, or float-precision overlaps fail lint.
