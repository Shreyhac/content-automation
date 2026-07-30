# Design system

There is no single house palette. **Theme follows the SUBJECT, type and layout follow the
CREATOR.** Those are two independent axes and confusing them has caused rejections in both
directions.

---

## Theme per subject

Pick a video's visual world from the subject company's design world, not from the creator's
channel default. A launch reel about OpenAI built in the channel's Claude terracotta was rejected
with "this is Claude's theme, this is for OpenAI."

Where to get it, fastest first:

1. **The subject's own compiled CSS.** `curl` a Next.js site's `_next/static/css/*.css` and regex
   the `:root{...}` block. That returns the whole system, including radii and eases, in one shot.
   Beats eyeballing screenshots, and scroll-triggered sites screenshot mid-animation anyway.
2. **The subject's own charts and launch visuals.** Anthropic's Opus 5 charts already gave the
   hero one saturated colour and rendered rivals near-invisible grey, which is exactly the rule
   below, with no invention required.
3. **The supplied hook clip.** If the owner supplies generated footage, sample it. A Kling clip of
   an amber serum going into a robot supplied the palette, the metaphor and the story, and made
   the whole reel cohere.
4. **What is physically in the raw footage.** One client A-roll had his own site on an ultrawide
   behind his head for 70 seconds, so the theme had to be sampled from it or every designed scene
   would clash with the in-frame screen. Check the footage before researching externally.

**Audit whatever you sample against WCAG.** Brands ship text colours that fail on their own panel
colours. And **reserve a darker step of the accent for TEXT**: an accent that works for fills,
bars and borders usually fails as small type. Splitting one token into `--accent` and
`--accentText` has cleared 17 contrast warnings without touching the palette family.

### The floor

Brand-faithful can be dead. A monochrome brand world produced a technically faithful build that
was rejected on sight. **The reel still needs one saturated accent carrying every number, bar and
border.** If the subject will not supply one, borrow it from the story, and prefer an accent that
*means* something: colour-coding the conflict (hero hot, rivals cold, nothing that is not the
hero may use the hot ramp) makes a leaderboard readable without reading it.

### When the subject is software

**Do not dress a software film in the subject's own chrome.** A dark IDE palette for a
developer-tools subject reads as "coded", not premium: it collapses the film and its subject and
looks like a screenshot of a terminal rather than an authored film. **Paper is the distance that
makes it feel made.** Watch for the corollary: light and white brand marks vanish on paper.
Simple Icons takes a hex (`cdn.simpleicons.org/<slug>/101014`); where the published SVG is white,
rewrite its own fill rather than filtering it. Verify by rendering all marks on the actual card
colour in one headless page before wiring them in.

---

## Grounds

**Backgrounds are never flat, and radial only.** Full-screen linear gradients band visibly in
H.264 on dark scenes.

On a 1080 canvas: one or two radial glows plus a faint dot grid on dark, a warm radial falloff on
light.

**At 4K that is not enough.** Two radial glows and a 3.5% dot grid read as flat near-black. The
six-layer ground that works:

1. Key glow at about 21%
2. Cool counter-glow at about 10% (17% turned the bottom of the frame into a green murk)
3. A second brand-colour bloom under the graphics field
4. A **ledger line grid**: hard-stop `linear-gradient(colour 2px, rgba(colour,0) 2px)`. This is a
   line, not a ramp, so the no-linear-gradients rule does not apply.
5. **SVG `feTurbulence` grain at about 5%** as an inline data-URI background. This is the layer
   that kills H.264 banding on a near-black ground.
6. A radial vignette so the grid reads in the middle and the edges stay deep.

Never stop a grid gradient at `transparent`: it is `rgba(0,0,0,0)` and premultiplies to a dark
fringe. Use `rgba(<colour>,0)`.

**A radial glow on a near-black ground shows its own edge.** Make it much larger than the content
it lights and use six stops with a long tail. Three stops is not enough falloff for H.264 at that
black level.

**Animate the ground with linear, absolute-time-phased motion** or chunk joins flash. Tween
rotation from `360*T0/P` to `360*(T0+D)/P` so a chunk starting mid-orbit resumes exactly. Anything
eased or restarted per chunk is visible at the cut, and budget for it: a permanently moving
background roughly triples the chunk bitrate.

**Grain belongs to the paper world, never to the face.** A 5% grain layer is invisible on ivory
and reads as a grey wash over lit footage. Toggle it per scene.

---

## The heavy-overlay budget

`lint` counts elements carrying radial-gradient, blur or clip-path. Past roughly 40 the renderer
has produced solid-black capture fields. One global ground stack beats per-band grounds: it drops
the count from about 30 to about 6 and prevents per-band grounds silently covering the ambient
layers.

The exception: **any band above the face layer must carry its own opaque ground**, because a
global ground sitting at low z cannot help it, and the face will bleed through.

---

## Type

Per project, not per house. The pairings that have shipped:

| Stack | Where it belongs |
|---|---|
| Clash Display + Satoshi + Geist Mono | Gaurav's paper world (current) |
| Rethink Sans + DM Sans + Geist Mono + rationed Fraunces italic | Nader's long-form (current) |
| Space Grotesk + Instrument Serif italic + Geist Mono | Music and audio subjects |
| Inter 400 to 800 + SF Mono chips | Tech launch subjects. A swashy display serif reads as rubbish here. |
| Fraunces + Poppins + coral/amber | The paper listicle family |

**"Fonts should be better" on a sans-only film means add a second voice, not a bigger sans.**
The answer that landed was a rationed serif: about six uses in four minutes, confined to source
attributions and the one act where the presenter stops selling. The register rule is
**attribution only, never a headline**, with at most one deliberate exception.

Practical traps:

- **A display serif has glyph holes.** Fraunces has no `≈`, and its italic lowercase z reads as a
  wave squiggle at display size. Any math glyph or letterform-as-prop goes in a sans, and gets one
  glyph audit on a rendered frame before shipping.
- **`line-height` unset on a display size is a collision waiting to happen.** 104px with default
  leading occupies 125px.
- **A masked per-word rise needs more leading than the same type unmasked**, because each mask
  extends below the baseline for descenders. Give the masked class its own leading.
- **`@font-face` must be declared inline in every chunk** of a chunked build. The static guard
  only resolves faces it can see in the document, and via an external stylesheet alone it reports
  "font used without @font-face" and silently falls back in the render.
- **Style SVG `<text>` in CSS, never with a `font-family` presentation attribute.**

---

## Motion grammar

The premium layer, in this order:

1. **Scene equals an acted product story.** Not "three cards light up": a real window where
   something happens. Cursor choreography sells it: move (`power2.inOut` about 0.22s), click
   (scale 0.8 yoyo plus a target brightness pulse plus a click SFX), result.
2. **Camera grammar on top**, where the creator allows it. Blurred zoom-through entrance, drift,
   origin-shifted micro-punches toward whatever just activated, crash-zoom exit. Keep ambient
   layers outside the rig for free parallax.

Restraint rules: prefer `power3.out` and `expo.out`; drop `back`, `bounce` and `elastic`
overshoots on entrances. Never `*.in` on anything whose legibility is the point, because power-in
ramps opacity so slowly that a short scene renders near-invisible right up to its transition.

**Motion direction should be monotonic within a shot.** Punches that return to base read as a
heartbeat. Punch-and-hold on A-roll; settle, one linear push, cut on designed scenes.

**Zoom tolerance is per-creator and take-resolution-gated.** Scaling a 1080-fitted video
resamples and reads as grain on low-light footage. A 1620x2880 transcode makes punch-ins up to
about 1.4x sample at or below native pixels. Check the creator profile.

---

## Devices worth reusing

- **The browser window** (`.bwin`: traffic lights, lock, typed URL, page inside). Real chrome and
  real URL for trust, rebuilt body for legibility. A window that springs in before its content
  paints is a dead white box: overlap the URL typing and the body paint.
- **The identity strip** for listicles: one constant carrier that opens every beat the same way,
  with a completely different physical event beneath it.
- **The docking window** for 16:9: one object tweened between full-frame and docked beside the
  face card. It replaces four scenes and reads as one continuous product. Dock it **before** the
  face cuts in, never during.
- **Ghost and skeleton pre-fill.** On dark, solid skeleton bars. On light, full-opacity content
  from card open with the spoken word triggering emphasis rather than reveal. Ghosted text can
  never pass WCAG, so opacity is not a "not yet" state.
- **The three.js recurring object.** One instanced object with several layouts reused across acts.
  See `playbooks/threejs.md`.
