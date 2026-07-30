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

## The recurring object

**One recurring object beats 3D-per-beat.**

One 750-instance plate field with named layouts (`scatter`, `wall`, `dome420`, `dome200`, `twin`,
`converge`) was used at four points across four minutes. Because the *same plates* rearrange, a
density comparison two acts later is legible without explanation: the eye already knows what a
plate is. Cost: about 90 seconds of the render per chunk, no bugs.

On a 40-second reel the same principle applies at smaller scale: two beats, one object, and the
recurrence is what makes it feel designed rather than decorative.

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
