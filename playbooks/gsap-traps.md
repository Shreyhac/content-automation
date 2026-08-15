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

### `fromTo` on a shared element flattens the whole film, and passes every gate (vid48)

Five wipe transitions reused two shared panels (`#w1`, `#w2`) with `fromTo` on each cut:

```js
tl.fromTo(el, { yPercent: from }, { yPercent: 0, duration: 0.20 }, t - 0.20);  // WRONG
```

`fromTo` defaults `immediateRender:true`. On a **paused timeline the renderer seeks**, five
overlapping `fromTo`s targeting the same two elements all resolve at build time to the
*last-written* tween's FROM value, not the one whose position the playhead is actually at. `#w2`
sat at `yPercent:0`, covering the canvas, for all 816 frames. Every frame was identical and
`lint`, `validate` and `inspect` all passed clean; nothing was malformed, the composition was
simply wrong.

- **The tell is the render's file size.** 2.1 MB for 27s at 1080x1920 where 39 MB was expected,
  a near-constant frame compresses to almost nothing. Check output size before extracting frames;
  it is a one-second check that catches this whole class. Second tell: sample two distant frames'
  mean RGB: they were byte-identical.
- **The rule: never target one element with two `fromTo`s in a seeked timeline.** One element per
  transition (`#wp1..#wp5`), initial state via `gsap.set()` **outside** the timeline, and only
  `to()` tweens inside it. `to()` resolves its start lazily and unwinds correctly on a backward
  seek.

### The trap is broader than "two `fromTo`s on one element," and it hit the SAME film twice

Round 1's fix ("never two `fromTo`s on one shared element") was too narrow. Round 2's rebuild put
a **single** `fromTo` on `#faceframe` for a beat at 24.52s, on an element that also had a plain
`to()` at 4.00s, and the card was invisible from frame 0 through the entire film, because a
`fromTo` **anywhere** on the timeline applies its FROM state at build time, regardless of its
position. Recurred at least twice more (vid52's CTA card blanked for the first half of its film;
vid58s's close-camera `scale/x/y` stamped itself onto `#faceCam` before frame 0 rendered, so the
cover shipped at the wrong size with the eyebrow at opacity 0).

> **The real rule: in a paused-and-seeked timeline, a `fromTo` anywhere applies its FROM state at
> build time.** If the element must be visible before the tween's position, the FROM state wins
> at t=0. For any entrance later than t=0, use `tl.set(el, fromState, t - 0.02)` then
> `tl.to(el, toState, t)`.
>
> **Generalised: an element NOT inside a `class="clip"` has no framework-managed visibility, so it
> must never be driven by `fromTo`.** Use an explicit `set` + `to` pair for every state change.
> Clip children are safe because the framework hides them until their window.

**File size does not catch the partial case.** Round 1 was 2.1 MB of flat colour and file size
caught it instantly. Round 2 rendered a healthy-looking 34.3 MB and only reading frame 0 as an
image showed the card missing. **File size catches "the whole film is one element"; frame QA is
still the only thing that catches "one element is gone."**

### The mirror fault: `immediateRender:false` fixes the pop and introduces a snap-back

Setting `defaults:{immediateRender:false}` on the timeline stops the from-state stamping the
cover, and now an element sits at its **final** tween value from frame 0 (inherited from CSS or
a later state) until its tween actually starts, at which point it **snaps back** to the from-state
and replays. A rule drawn full across the frame from t=0 vanished at 4.92s and drew itself again.
Neither default is safe unmonitored; render both ways and read frame 0 and every tween-start frame.

### `gsap.from()` reads the element's CURRENT value as its target, not a fixed one

Every scene in one film started at `opacity:0` in CSS (because a zero-duration `tl.set` at
position 0 does not reliably paint at frame 0: see above). `gsap.from(sel, {opacity: .58})` on
such a scene animates **.58 → 0**: it renders perfectly at the cut frame, then fades to nothing
half a second later and stays gone for the rest of the chunk. It is `from()`, not `fromTo()`, that
has no defined "current" state independent of the DOM: **use `fromTo()` for anything whose CSS
start state might be hidden.**

`gsap.from()` combined with a `keyframes` array is separately unreliable (no well-defined start
state): use `fromTo()` with the keyframe array in the *to* vars instead.

### `.stg`/hide state on a parent does not stage its children

With `immediateRender:false`, a hidden **parent** does not cascade its hidden state to a child's
own computed style. A row's numeral child computed `opacity:1` the instant the row arrived, so
"60" and "90" were on screen a full second before the presenter said either number, then snapped to
zero and re-entered on the word. Staging belongs in CSS **on the element that animates**, never
assumed from its parent: this is the same fault as the "late children" section above, found again a
chunk later, 75ms under a 0.5s stillness detector's window (a near-miss is a reason to trust the
detector, not loosen it).

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
  `svgOrigin:"540 1120"`, or avoid the transform (an `attr:{r}` pulse worked). Same fault on a
  per-limb SVG `<path>`: `transformOrigin:'84px 108px'` on a walking figure's leg resolves against
  that path's own bounding box, so each limb pivots about a different point and the legs detach
  and fly off at the hip. `svgOrigin:'84 108'` is the SVG-specific API and takes **user units**;
  never combine the two APIs on the same element.
- **Switch transform-origin only at scale 1.** An origin swap at scale != 1 jumps the frame.
- **Tween x/y transforms, never left/top.** Lint flags `gsap_non_transform_motion`.
- **`letterSpacing` tweens are a hard lint error.** They snap to integer device pixels under the
  seek-by-frame capture engine. Replacements: a uniform tracking pulse becomes `scaleX`; a
  per-letter spread-in becomes spans with function-based `x:(i)=>(i-mid)*N`, or a `spread()`
  helper that splits the string into per-glyph `<i>` and animates each glyph's `x` from an
  outward offset. **The glyph-splitter workaround cannot be used on
  `background-clip:text` gradient headings**: each glyph gets its own gradient ramp instead of
  sharing the parent's. Those need a plain transform entrance (scale + y) instead.
- **`display:inline-block` on a span whose only content is a space collapses it to zero width.**
  Any per-character animation system (a glyph splitter, a typing engine) produces exactly this
  span, so "THREE FREE" rendered as "THREEFREE" and a shell command lost every space. Fix once,
  everywhere the splitter is used: `white-space:pre` on the per-char span.

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
- **`inspect` needs `data-duration` on the ROOT composition, not just `data-start="0"`.** `lint`
  only demands the latter. Without the former `inspect` dies with `Cannot read properties of
  undefined (reading 'totalDuration')`: an opaque error for a missing attribute, not a
  composition bug.
- **`:nth-of-type()` counts elements of that TAG, not that class.** Interleaving `.keep` spans
  between `.kill` spans silently broke `#s2-demo .kill:nth-of-type(2)`. `lint` passed; `validate`
  caught it as `GSAP target … not found`, which is worth reading rather than skimming. Give each
  animated child its own explicit class instead of relying on structural selectors.
- **An absolutely-positioned element with no `left`/`top` supplied entirely by GSAP parks at the
  frame corner (0,0) until its first tween fires.** Four fact chips sat stacked there, fully
  opaque, for 2.5 seconds before their `fly()` tween set a transform. A safe-zone gate that
  measures real coordinates catches this; nothing else will. Any element whose position comes
  entirely from GSAP needs an explicit `tl.set(...,{autoAlpha:0})` at its scene start.
- **A typing/reveal helper that reads a `data-*` attribute needs that attribute checked at author
  time, not at runtime.** `typeLine()` read `el.dataset.txt`; one element had inline HTML and no
  `data-txt`, so it typed the literal string `undefined` for 3.6 seconds. Nothing checks that the
  attribute exists before the call: grep every call site against its selector's markup.
- **`gsap.timeline({defaults:{immediateRender:false}})` fixes `fromTo`-eats-the-cover and
  introduces a mirror fault: an element sits at its FINAL value from frame 0, then SNAPS to its
  FROM state when the tween starts, then replays.** Test both defaults and read frame 0 and every
  tween-start frame; neither is safe unmonitored. See "fromTo semantics" above.
- **`<use href="#sym">` cannot be stroke-drawn.** The geometry lives in the shadow tree, so
  `querySelectorAll(sel+' path')` returns nothing and every `draw()` call is a **silent no-op**,
  with no error: only a `GSAP target not found` warning in `validate`. Expand symbols to inline
  paths before animating their strokes.
- **A curved flight path with no MotionPathPlugin**: tween `x` with `ease:'none'` and `y`
  separately (out then in). Two tweens, one visible arc.
