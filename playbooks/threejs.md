# three.js in HyperFrames

It works, and the renderer expects it (there is a built-in `missing_three_script` lint rule).
WebGL is real hardware: the render browser reports `ANGLE (Apple, ANGLE Metal Renderer)` and logs
`browserGpuMode auto → hardware (WebGL probe succeeded)`.

**Spike it in a throwaway composition before writing any production 3D.** Twenty lines, three
seconds, read the frames. Five minutes settles the question.

---

## Three non-negotiables

### 1. Vendor the library locally, and use the UMD build

`library/vendor/three.min.js` (UMD). Two reasons, both fatal otherwise:

- A second CDN request is exactly what killed one render: the script died before
  `window.__timelines` registered, and lint, validate and render all reported success on a page of
  static DOM.
- **An ES-module script defers.** The capture engine reads `window.__timelines` synchronously
  after load, so a module build silently produces a dead page. The lint rule scans for a script
  tag and never sees `import`.

r150 and r160 are the last UMD releases. They log a deprecation warning; harmless.

### 2. Every pixel must be a pure function of timeline time

Capture runs three to four parallel workers that seek and screenshot. `requestAnimationFrame`
desyncs instantly.

```js
// preferred: onUpdate fires after that tick's tweens apply, so it is order-safe by construction
gsap.timeline({ onUpdate(){ GL.render(this.time()); } })
```

A driver-tween (`tl.to(drv,{v:1,duration:D,ease:'none',onUpdate(){GL.render(drv.v*D)}})`) also
works, but the timeline `onUpdate` is order-safe rather than lucky.

`paint(t)` derives morph, rotation, colour and scale from `t` with smoothstep. No
`requestAnimationFrame`, no `Date.now`, seeded PRNG only. **Reading state that other tweens mutate
is the trap**: tween update order within a tick is not guaranteed, so a seek can render a stale
frame. Derive from `t`.

**Verify determinism by rendering twice and diffing per-frame SHAs.** A correct build is
bit-identical. Confirmed at `-w 2` against `-w 3`.

### 3. Size against the screen, by arithmetic

You cannot eyeball this, and both builds that tried shipped a broken hero beat.

```
visible_height_at_z0 = 2 * cam.z * tan(fov/2)
px_per_unit          = frame_height / visible_height
```

Worked: at fov 42 / cam z 6 the visible height is 4.606 units over 1920px, so 1px = 0.0024u.
At fov 40 / cam z 9 it is 6.55 units, so 293px per unit.

**Method:** measure the free vertical band between the layout's real elements, halve it, convert,
and set the base radius from that. Then multiply by the **wobble maximum**, not the mean.

Failures from skipping it: a sphere about 1670px across that swamped the title and ran under the
captions; an arrow crossing both the title and the face.

---

## Flat objects need oscillating rotation, not a monotonically increasing one

A layout deliberately flat in its own XY plane (a page, a seal, a card, a stack of rows) inherited
a steadily increasing Y rotation (`rot = t * 0.20`) from a build whose objects were genuinely 3D
(spheres, clusters, cones). A monotonic spin **sweeps through 90 and 270 degrees**, and at those
angles a flat object is a vertical smear. The earlier, related lesson was "a torus built in the XZ
plane is invisible to a front camera": this is the same fault from the other axis. **Check the
rotation against the dimensionality of the layout, not just the plane it lives in**: 3D layouts can
spin freely; flat ones need `rot = A * sin(t * w)`, `A` around 0.17 rad, so they never turn
side-on. The tell is a narrow bright column where a wide object should be: easy to misdiagnose as
a density or alpha problem.

## Tile/point size decides whether a material can be seen at all, before any shading question

A material rebuild (standard shading, environment map, per-tile rise, bloom) was invisible in its
first spike, and the cause was upstream of every one of those upgrades: at `TILE=34`, a tile
rasterises to 17px at delivery resolution: no room for a highlight, no visible height, nothing
bright enough for bloom to catch. Re-solved from that floor to `TILE=90`, the same device went from
a 46%×27% strip to 62% of frame, with lit-vs-unlit separation finally surviving H.264 (65–83 luma
apart, against a flat control's 38.9). **Scale places a device; pitch/spacing shapes it; and raw
element size decides whether any material property is visible at all**: check size against the
delivery resolution before tuning anything else.

A related trap: enlarging the vertical pitch of a tilted grid to "give it more room" made it read
as ten horizontal stripes instead of a grid, because the tilt's foreshortening was already
compressing the vertical axis by ~0.65×: a 54px gap became 35px on screen against a 6px
horizontal one. The geometry was already right; the fix was `scale` and vertical offset, not more
pitch. **Re-proof the sheet before re-deriving anything**: one screenshot settles which axis is
actually wrong.

## A neutral instance colour is not a neutral render

Setting an instanced object's own colour to neutral grey was not enough to make it read as neutral:
the scene's environment map (a blue sky) and rim light tinted it a visible hue: a competitor
rendered in the sponsor's own brand colour, in a paid comparison. The grey state needs
`envMapIntensity` pulled down (not just zeroed) and a neutral/white rim light, which reads as a
different **material**, not a dimmer version of the branded one. Any lit 3D object inherits colour
from more than its own material property; check the environment and rim lights too whenever colour
is doing editorial work (branded vs. neutral, ally vs. competitor).

## Different numeric claims must not share one field, and a tile is not automatically "one thing"

A script carried three different counted quantities (e.g. 750 broker groups, 319 sites, 420
brokers). Building one field of 750 elements with 319 and 420 lit inside it asserts a relationship
between the three numbers that was never established: the viewer computes ratios nobody claimed.
**A recurring field device should carry SHAPE (the comparison), never COUNT**: put each number on
its own stamped/labelled figure with its own source, and use the field only where the argument
genuinely is coverage/shape. Making a tile equal exactly "one broker" to avoid this just moves the
same false-precision problem down one level (the field's total now has to be a real, exact number),
so the fix is to stop asking the field to carry a count at all.

## Guilloche / epitrochoid curves: two traps

- **Never interpolate `R` and `r`.** A closed epitrochoid needs `R/r` rational; lerping through a
  non-integer ratio produces an OPEN curve that sweeps enormous arcs off the frame. Switch `R`,
  `r`, `d` **discretely on the cut** (the wipe already covers the canvas on that exact frame, so
  the swap is invisible) and lerp only centre/level/spin so the new figure settles into place.
- **Guilloche is copies, not scales.** Nesting rings from 0.30x to 1.0x scale produces a smear.
  Real guilloche is many near-identical copies of one curve, each turned by a fraction of a lobe
  (`scale 0.82–1.0`, `phase = f * 2PI / lobes`). Lobe count is the numerator of `R/r`: pick pairs
  giving 5–10 lobes; below 5 reads as swooping arms rather than a rosette.

## The recurring object

**One recurring object beats 3D-per-beat.**

One 750-instance plate field with named layouts (`scatter`, `wall`, `dome420`, `dome200`, `twin`,
`converge`) was used at four points across four minutes. Because the *same plates* rearrange, a
density comparison two acts later is legible without explanation: the eye already knows what a
plate is. Cost: about 90 seconds of the render per chunk, no bugs.

On a 40-second reel the same principle applies at smaller scale: two beats, one object, and the
recurrence is what makes it feel designed rather than decorative.

**A recurring 3D field is a subject or it is nothing: it does not survive demotion to ambient
texture.** The same field device that worked at alpha 0.92 as the literal subject of a film (its
instances *were* the thing being counted) was rejected when reused as low-opacity wallpaper behind
unrelated scenes in the next production: at 5–14% alpha its thin edges alias frame-to-frame at 4K
(read as flicker) and its instance-colour LEDs bleed through as stray coloured lines behind text.
**Never run a hero field below roughly 0.6 alpha, and never behind content it is not actually
illustrating.** Reusing a hero device as texture destroys the device and dirties everything in
front of it. A signature device reused for the *same client's next film* also reads as a repeat,
not a callback, unless the client explicitly asks for it back.

**A DOM bezel around a WebGL core is the strongest hybrid.** The ring, tick marks and label are
crisp CSS; only the thing inside needs to be 3D.

---

## Materials

**`InstancedMesh` plus a body and LED split.** Body is dark brushed metal
(`color 0x2b2b36, metalness .52, roughness .36`); the state colour lives on a **thin LED strip
child** with `instanceColor`.

- **Glow belongs on the detail, not the body.** Server racks with `emissive` on the whole box read
  as flat salmon bar-chart columns. Move the emissive to the LED strip and make the cabinet dark
  brushed metal, and it reads as hardware.
- **On a near-black ground the dim end of every ramp has to be lifted until it actually reads.**
  A first spike at `0x14141a / metalness .78` left only the LED strips visible and the field read
  as a grid of dashes. Third occurrence of this lesson.
- **Additive blending on near-black eats dark point colours.** One ramp's slate end had to go up
  to `(0.26,0.32,0.31)` before the lattice read at all. Shrink point size as a cloud densifies
  (0.026 to 0.016) or the formed shape blows out.
- **Re-lighting for a paper world is a full inversion**: pale ceramic body (`0xE6E2D8`,
  metalness .04, roughness .72), ambient up to 2.35, and the state colour moves to a **deep** hue
  because a mint accent is invisible on ivory.

---

## Layout traps, all frame-QA-only

- **A flipped instance hides its own LED.** A wave sweeping a wall and turning half the plates
  from red to green with a 180 degree Y flip pointed every flipped plate's lit face away from
  camera, so half the wall went dark instead of green: the entire meaning of the beat, invisible.
  Fix is one more instanced mesh at `-Z` sharing the same `instanceColor`. **Any layout that
  rotates plates past 90 degrees needs both faces lit.**
- **A layout whose MEANING depends on left/right must never rotate past a quarter turn.** A twin
  comparison tweened `rotY` 1.98 to 2.68 rad; past 90 degrees the two spheres swap sides on screen,
  so a label sat under the wrong sphere and the graphic argued the opposite of the VO. Rotate
  <= 0.2 rad, or do not label sides.
- **A horizontal torus viewed from a level camera renders as a solid BAR, not a ring.** Tilt the
  torus off-axis (`rotation.x = PI/2 - 0.36`) **and** tilt the group toward camera on that beat
  (`rotX 0.30`) so it always projects as an ellipse. Give it real clearance
  (`max(R*sin, floor) + 150px`) or the parts poking through read as a blade.
- **Pack density is a legibility budget.** 300 plates in an 820x1080 wall (55px pitch, 44px plate)
  read as fine texture, not as "your software stack". 150 plates at a 76px pitch read as apps.
  A 12x25 column reads as a barcode; 20x15 reads as records.
- **Add a per-layout X scale.** One `sx` array lerped like everything else turns a square-ish tile
  into a bar, which is the difference between "scattered dots" and "a table". 1.10 to 1.28 for
  rows, 1.35 for a wall.
- **Never open a beat on a layout that is mid-slab.** A `lattice → burst` tween spent its first
  third as a striped block behind ten logos. `scatter → converge` is never a slab and rains no
  debris.
- **A vanishing end state is not a layout.** A `converge` ending at plate scale 0.001 pinned the
  field invisible and produced 1.0s and 0.66s of black after cuts. Collapse into the next object
  instead.
- **Retire a 3D prop explicitly.** A scan ring was still orbiting a docked sphere two scenes after
  its beat because nothing set `ringOn:0`.
- **Kill the field before the next cut, not after.** Fading alpha after the boundary left one
  scene's field painting over a face. Kill at `cut - 0.2` and `gsap.set("#gl",{autoAlpha:0})` just
  after the cut.
- **Clip the canvas to its zone permanently** where a face shares the frame
  (`inset(150px 0 1010px 0)`). A loose field drifting across a face reads as dirt on the lens.

---

## Porting a layout to a different canvas

**Re-derive the px dimensions, do not scale them.** See `playbooks/short-from-longform.md`: pixels
per unit is `H / VIS_H`, so a 2160 to 1920 change makes every px constant 12.5% larger in a frame
a third as wide, and a wall's pitch can fall below its plate size and render as stripes.

---

## Other

- `setDrawRange()` on a `TubeGeometry` index count is the cleanest deterministic draw-on reveal,
  for example an arrow drawing itself along a `CatmullRomCurve3` on its spoken word.
- **Clamp a path-following element to 0.07 to 0.93 of its curve** so it parks clear of whatever
  edge the curve ends against.
- **An abstract 3D glyph reads as a mistake; a 3D glyph carrying a real subject reads as an idea.**
  A U-turn arrow drew "weird" twice; putting the subject's actual face on the track made the same
  geometry instantly legible.
- Cost is low: 4600 points and about 376 tweens had no measurable effect on render time.
