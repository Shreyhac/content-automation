# Nader: visual grammar

The current approved system is **vid62 round 3** for long-form and **vid58's short rebuild
(hf58s/)** for vertical. Reference builds: `reference-builds/nader-vid46-longform/` and
`reference-builds/nader-vid46-short/` still hold, but the sections below flag what a later video
changed. vid46 round 3 established the carrier-variety and type-scale rules that still stand;
vid62 round 3 is what proved the device kit those rules imply, reused rather than reinvented, and
took kit usage from 0 of 12 devices to 9 of 12 while designed-stage share went 44% to 70%. vid46-
short v3's floating-card geometry is still the correct BAKE for a face card; vid58's short rebuild
is what proved the layout it sits inside (see "9:16 vertical" below), and vid59's short reused that
layout without change.

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

**Carrier variety is not MATERIAL variety.** vid56 round 1 shipped seven distinct carrier shapes
(spines, rails, redaction bars, two-lane tracks, tick fields, seals, cycles) with zero repeats and
was still rejected as "all text based," because all seven were thin vector line-work on dark: no
photography, no product surface, no generated art in four minutes. **Every act must contain at
least one NON-VECTOR element**: real footage, a real product surface, or a generated image.
Line-work is the connective tissue between those, never the substance. Counting shapes is
necessary and not sufficient; count materials too.

### The device kit

`base.css` in a scaffolded project carries the full, client-approved kit: `.trail .plate .wcard
.bcard .chip .stair .mark .pull .attrib .nostamp .dash .srch`, each documented inline with its own
already-fixed bugs. **Before writing any scene CSS, list what the kit already defines against what
the chunks actually use.** vid62 copied vid58's `base.css` wholesale and then built eighteen chunks
of bespoke dark rounded boxes, using zero of twelve kit devices, which is the entire content of
"only a text-based thing is really too shitty" and "we have been doing better in the previous
ones." Rebuilding on the kit took about twenty minutes per beat and took kit usage to 9 of 12,
designed-stage share from 44% to 70%, and stillness (motion_guard) from 56% to 35%. **A scaffolded
project inherits the previous film's whole kit; use it before inventing a parallel one.**

---

## The recurring three.js object

`field.js` is a single 750-instance plate field with named layouts (`scatter`, `wall`, `dome420`,
`dome200`, `twin`, `converge`) used at four points across four minutes. Because the *same plates*
rearrange, a density comparison two acts later is legible without explanation.

`InstancedMesh` plus a **body and LED split**: body is dark brushed metal, state colour is a thin
LED strip child using `instanceColor`. It is the one device he named as good, twice. Do not
redesign it. See `playbooks/threejs.md`.

**The field is a subject or it is nothing.** On vid46 the field WAS the subject (750 instances were
the 750 broker groups, the dome was the 420 sites, alpha 0.92). vid56 demoted it to an ambient
background at alpha 0.05-0.14 behind unrelated scenes, and at that opacity its thin plate edges
alias frame-to-frame at 4K (read by the owner as flicker) while the LED `instanceColor` bleeds
through as stray coloured lines behind text. **Never run the field below about 0.6 alpha, and
never behind unrelated content.** Reusing a hero device as texture destroys it and dirties
everything in front of it. And a signature layout (the same 750-wall, same 420-dome) reused
unchanged in the next film for the same client reads as a stale repeat, not a callback, even
where the device itself is right, so vary the arrangement or retire it for that film.

vid58 and vid59 both moved past `field.js` toward a purpose-built field per claim rather than one
recurring wallpaper object, and the lessons generalise to any such device: **a replacement for a
rejected hero device has to be an ARGUMENT, not another ambient shape.** vid58's `coverage.js` (640
tiles) makes the LIT AREA the claim itself: each tier lights its real count and stops at a visible
gate, a competitor lights the whole field at once, and an unverified category renders as hollow
outlines rather than a footnote. vid59's rebuild fixed a purely technical failure underneath the
same idea: `MeshBasicMaterial` throughout ignores the scene's own light, and at `TILE=34` (17px at
delivery) no material choice was visible at all regardless of lighting; `TILE=90` took the same
device from a 46%x27% strip to 62% of frame. **Scale places a device; pitch shapes it; tile size
decides whether any material can be seen at all**: proof-render a new field device as a still
before it touches a timeline. Also: setting a competitor's instance colour to neutral grey is not
enough if the environment map and rim light are the sponsor's own colour (vid59's OneRep field
rendered periwinkle, the sponsor's brand blue, until `envMapIntensity` dropped to 0.22 with a
white rim). A neutral albedo is not a neutral render.

**Different denominators must never share one field.** A grid built to hold two figures that come
from different bases (e.g. total registered broker groups vs. one competitor's site count) asserts
a relationship nobody established, letting the viewer compute an invented percentage. Use the field
for coverage SHAPE (narrow-and-deep vs. wide across categories) and let independently sourced
numerals carry COUNT beside it, never inside one tile-per-unit mapping.

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
height, so a cover crop puts it inside the UI band. Whether a WIDER take clears it is a
measurement, not an assumption: vid56's shipped chin p97 landed clear (y1408 at cover scale
0.8889), vid58's landed at y1575, "25px of clearance that is a coincidence, not a margin," and
vid59's whole-take figure read as another coincidence (y1538) until re-measured on the actual beat
being cut (y1465-1474, genuinely clear). **A percentile over a whole take is a property of the
take, not of the beat you are cutting**: re-measure the specific beat before letting a take-wide
figure veto or approve a shot.

Two bakes for the close/carded states:

- **The band** (vid46-short v2): face band 1080x1000 at y0, graphics zone y1040 to y1380,
  captions below. The band's foot must dissolve with a `mask-image` linear gradient on the video
  *and* its scrim. A radial only reaches the frame centre and slices the chair and wall off
  either side, which is the cheapest-looking thing a cut can do.
- **The floating card** (vid46-short v3, numbers re-solved per project, never copied wholesale):
  vid58's short re-solved it to 560x736 at x260 to x820, y838 to y1574. See
  `playbooks/face-card-device.md`.

**Current approved short LAYOUT (vid58's rebuild, hf58s/, reused unchanged on vid59s): animations
TOP, A-roll BOTTOM, split-screen AND card across the cut, with stock footage.** This is the
owner's own correction after a first delivery inverted it (face top, graphics under, one placement
held the whole cut, zero stock). The face bake is **one camera, three states**, and only one of
them may change his head size:

    BAND   full width   split-screen, a full-width bottom panel
    CARD   narrower     the same camera, same head size, clipped narrower (a WIDEN, not a resize)
    CLOSE  full width   a real size change, pushed in; only safe landing on a hard cut into a new shot

**Do not read the layout off the CSS; drive the composition and measure it.** Both vid56's short
and vid58's short round 1 came out inverted (face top, graphics under) because someone read
`#faceCam`'s declared `top:0; height:1210` as a placement. It is the untransformed camera. What
lands on screen is `#faceScene`'s clip-path plus the transform `faceSet()` writes, which at frame 0
resolves to a card at the BOTTOM of frame. Seek the timeline and read `getBoundingClientRect` on
the CLIPPED result. Cost of not taking that one screenshot: a whole rebuilt short.

BAND and CARD sharing one camera is what makes cutting between two formats safe in one short:
vid46's short cut between two literal camera sizes and the owner read it as a bug. On vid59's short,
the choice between CARD and BAND for a given beat came down to a measured constraint (his contour's
sweep against the card's width), not a preference: a beat failing a residual/framing threshold was
reread by hand against both of his sway extremes before being demoted to the wider BAND, and CARD
to BAND to CLOSE was found to escalate naturally into a CTA.

**A card collapses inside the rect it started in.** One shared `off` state
(`inset(1574px 0 346px 0)`) was used for every picture exit on vid62's short, so a picture leaving
a CARD widened to full frame on the way down and slid a full-bleed strip of his neck out past an
empty card border. That single fault was BOTH of his "glitchy/weird transition" notes on that cut.
Give the card its own `cardOff` that keeps the left and right insets, and fade the card frame WITH
the picture rather than leaving the border standing.

**At a hard cut, SET the picture state. Never tween across the cut.** A wipe exists to hide the
swap, and a 0.34s `faceTo()` starting at the cut finishes after the wipe has cleared, in full view.
That was a third "weird transition" note on the same short. `faceTo` is for moves INSIDE a beat.

**Centre the card on the MEDIAN head position, not on the midpoint of his extremes.** Extremes
centring maximises the smaller margin, which answers "will his face leave the rect" and not "does
this look centred". On vid62's short one 0.4s lean dragged a card 55px and he sat off centre for
the whole beat; his note was "this is not centered aligned". If median centring then breaches
FACE_MARGIN, the beat cannot be a CARD at all and plays as a BAND.

**Solve the crop over the spans he is VISIBLE in, not over the whole beat.** Five of vid62 short's
nine beats showed him for only part of their runtime, and a beat-wide median is a median over
frames nobody sees.

**"Full screen" is not automatically a 9:16 crop.** He asked for a full-screen close on vid62's
short; a true edge-to-edge 1215px-wide 9:16 window put 43px of his cheek outside the frame on both
sides and his chin at y1601, inside the UI band. It shipped instead as a full-WIDTH 1080x1468
picture from y106 down to the same y1574 floor the band uses: whole head, caption under his chin.

On a split beat **the caption moves ABOVE the card**. Leaving it in the low band prints it on
the jaw.

**The shell arrives on the verb, the figure arrives on the figure** (house pattern since vid59s,
used three times in one film): a device's STRUCTURE (a form's field labels, a row's own labels,
category chips) lands on the cut; its CLAIM (the filled values, the numerals, the lit chips) lands
on its own spoken word. Fixes a zone holding one bare numeral in open ground and a figure appearing
before it is spoken, in the same move, and gives a form-shaped device a genuinely finished frame 0
(fully drawn, nothing filled) instead of a half-drawn one.

A device sized for the long-form's 3840px canvas is not automatically legible cropped into a
short's narrower graphics zone: a screen-recording strip framed for 3840px wide fell to 0.33x scale
and 8px labels inside vid59s's 890px zone. **Re-solve any long-form crop for the delivery width**,
targeting source text at 0.7x scale or better, not for the long-form's own framing.

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
