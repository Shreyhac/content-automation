# Nader: visual grammar

The current approved system is **vid46 round 3** for long-form and **vid46-short v3** for
vertical. Reference builds: `reference-builds/nader-vid46-longform/` and
`reference-builds/nader-vid46-short/`.

---

## Architecture: chunked long-form

**Chunking is the right architecture, not a workaround.** A four-minute composition is
unreviewable and un-iterable. Split on word onsets into projects of 22 to 37 seconds, each with
its own `assets` symlink to a shared folder. A bug in one act costs a 90-second re-render instead
of a 20-minute one.

```
hfNN/
  assets/
    base.css      palette · six-layer ground · carrier vocabulary · face-card geometry
                  · caption band · type scale
    chunk.js      mountGround, faceCard/faceFull/hideFace/blink/cut,
                  wordRise/splitWords/digitSettle, put()
    field.js      the recurring three.js object
    three.min.js
  c1/ ... c8/     one index.html each
  *.py, *.sh      the toolchain (mirrored in tools/)
```

Eight projects, one place to fix a join. Two traps:

- **`@font-face` must ALSO be declared inline in every chunk.** The static guard only resolves
  faces it can see in the document; via an external stylesheet alone it reports "font used without
  @font-face" and silently falls back in the render.
- **Do not duplicate the ground or the palette inline.** Round one did, and editing `base.css`
  then silently did nothing.

**Chunk-to-chunk continuity is a geometry contract.** One chunk's last frame and the next
chunk's first frame share verbatim CSS for the same elements, and a tile hands over as a real
skeleton that resolves on the next spoken word. Where no wipe can carry a join, the ground rig
gives a **light bump**: the three.js field's alpha swells over the last eight frames of one chunk
and settles over the first eight of the next, same value, `ease:"none"` on both. Because the rig
is phased off absolute film time, it is the one device that stitches two separate compositions.

See `playbooks/longform-chunking.md`.

---

## Theme

Sampled from the subject, never invented. Two shipped:

| Film | Theme | Source |
|---|---|---|
| vid39 | "Plexus Indigo", then re-skinned to light editorial in round 2 | The client's own site, which is physically on screen behind his head |
| vid46 | "Signal Blue" | incogni.com's own CSS variables |

**Check what is IN the raw footage before researching an external palette.** His A-roll carries a
wall screen behind him for the whole take, and a designed scene that clashes with it looks wrong
in a way no amount of polish fixes.

### Ground

The **six-layer 4K ground** (see `docs/04-design-system.md`). Two radial glows and a dot grid read
as flat near-black at 4K; the layer that actually fixes H.264 banding is the SVG `feTurbulence`
grain at about 5%.

---

## Type

| Role | Face |
|---|---|
| Display and all numbers | Rethink Sans 800, up to 380px, `-0.045em`, `tabular-nums` |
| Captions and body | DM Sans |
| Labels, mono, the coupon | Geist Mono |
| Second voice | **Fraunces italic, rationed to about six uses in four minutes** |

The serif is what makes the trade-off act read as a person talking rather than a slide. Register
rule: **attribution only, never a headline**, with one deliberate exception for an honest
trade-off title. He picked this over sans-only.

**At 4K, working sizes are what read as cheap.** The round-two lift that changed the read more
than any scene rebuild: eyebrow 40 to 52, mono 34 to 44, body 56 to 68, values 76 to 104.

---

## Carrier vocabulary

**Do not let one shape carry every idea.** This is the fault that got round one called "cheap":
record card, buyer tiles, action rows, module slabs, ledger tiles, price carriages, router
tokens, reason cards and coupon card were all rounded rectangles with the same `y:+20` fade.

The rebuild stripped the box nearly everywhere, which turned the one remaining box (the coupon)
into a device. Vary the carrier: rails with carriages, plates in 3D, seals, skeletons, physical
tracks and gates.

---

## The recurring three.js object

`field.js` is a single 750-instance plate field with named layouts (`scatter`, `wall`, `dome420`,
`dome200`, `twin`, `converge`) used at four points across four minutes. Because the *same plates*
rearrange, a density comparison two acts later is legible without explanation.

`InstancedMesh` plus a **body and LED split**: body is dark brushed metal, state colour is a thin
LED strip child using `instanceColor`. It is the one device he named as good, twice. Do not
redesign it. See `playbooks/threejs.md`.

---

## Face treatment

### 16:9 long-form

- **Card on the RIGHT, graphics on the LEFT** for this client. This was a round-two reversal of a
  left-card default, so never bake a side into a shared design language.
- Card geometry as built: `inset(440.1px 180.2px 440.3px 2280.4px round 40px)`, so x2280 to x3660,
  y440 to y1720.
- **Solve scale, x and y per card window** from that window's own frames, not once for the take.
  His head ran 1118 to 1548px tall and his centre swayed +/-180px across one take. Thirteen of
  fourteen windows held a house 0.82; one dropped to 0.742 because he leans into camera.
- **Mirror a split by shifting the scene WRAPPER**, not the elements: one `translateX` on each
  scene wrapper remaps every anchored graphic and nothing else moves.
- **One `<video>` element per face window**, each with its own `data-start` and
  `data-media-start`. Extra wraps carry their card transform in CSS, not GSAP, so a geometry
  change has to be made in two places.
- **The docking window** is the best 16:9 device: one stage tweened between full-frame and docked
  beside the face card. Dock it before the face cuts in, never during.

### 9:16 vertical

A tight 16:9 close-up has **no usable full-bleed 9:16 crop**: the chin sits at 89% of frame
height, so a cover crop puts it inside the UI band. Two approved answers:

- **The band** (vid46-short v2): face band 1080x1000 at y0, graphics zone y1040 to y1380,
  captions below. The band's foot must dissolve with a `mask-image` linear gradient on the video
  *and* its scrim. A radial only reaches the frame centre and slices the chair and wall off
  either side, which is the cheapest-looking thing a cut can do.
- **The floating card** (vid46-short v3, current, and what he asked for by name): re-solved to
  560x736 at x260 to x820, y838 to y1574. **Do not copy vid39's numbers.** See
  `playbooks/face-card-device.md`.

On a split beat **the caption moves ABOVE the card**. Leaving it in the low band prints it on
the jaw.

---

## Motion

- Punch-and-hold on A-roll, monotonic within a shot.
- Skewed band wipes, run **symmetrically around the swap time** (`t - dur/2` to `t + dur/2`,
  inOut ease, panel sized so its midpoint covers the canvas) so `t` is the swap frame by
  construction. See `playbooks/transitions-and-cuts.md`.
- Wipe **direction is a gaze decision**: eating a face band from the top takes his eyes out of
  frame first, which lets a conceal start before his gaze drops without ever showing a downcast
  frame.
- Headline entrance: masked per-word rise at **0.028 stagger / 0.52 duration**. Slower leaves a
  half-formed headline that reads as a render bug in a still.
- **Verified figures ARRIVE, they do not count up from zero.** These are audited published
  numbers; a spinner implies live measurement the film is not doing, and a third of each beat
  displays a wrong number.
