# card-reel: visual grammar

## Current state (read this before the vid42 sections below)

The approved look is no longer vid42 v3. Five builds moved it, and the mechanics below still hold
even where the skin does not:

| build | what it changed |
|---|---|
| vid49 v2 | dark ground plus terracotta glow plus dot grid plus point cloud was rejected as "AI slopped". Skin from what the subject is physically made of. |
| vid55 round 1 | the same dark ground rebuilt and rejected again. Fixed by one coherent material (dev-tool paper, one syntax-highlight system) instead of three competing accent hues. |
| vid57 | the creator's back wall is already ivory, so ink type sits directly on it and nothing reads as pasted over them. |
| vid63 round 1 | the paper theme proper: "the marked-up report". Ivory paper, ink, one alert red, physical devices only. |
| vid64, vid65 | the paper theme carried forward unchanged, plus at most one subject-owned accent. |
| vid66 | the paper theme deliberately replaced by Apple's own values, with terracotta reserved for Claude objects. |
| vid67 | no theme of its own: a shot-for-shot copy of a reference reel. |

**Open question for the owner: no build has been declared the canonical template.** The candidates
are **hf64** (the style parent vid65 was explicitly told to replicate, and the largest paper build
at 42.1s) and **hf65** (the newest paper build, and the style parent vid66 was scaffolded from).
hf63 is where the paper theme was born but its face system has since been re-solved twice. Pick one
and this file can name it; until then, scaffold from hf65 and re-derive geometry.

---

## The paper theme, as approved

Established at vid63 round 1 after a dark green-on-black TUI was rejected on screen: *"the theme
looks very shitty and vibe coded and very very weird ... needs to be changed entirely."* That was
the third dark ground this template has rejected.

- Ivory paper, ink, **one** alert red. Every device is physical: marker ring, margin handwriting
  (Gaegu), rubber stamp.
- **The fault named as "vibe coded" is not darkness and not any one colour: it is anything that
  looks like it could have come out of a generator.** Flat shapes, ink outline, no gradient, no
  glow. Dark surfaces survive only when they read as a screenshot pasted into the report (an
  install terminal, a product's own TUI).
- vid65's palette, as shipped: ivory `#F0EEE5` / `#FCFAF5` / `#EAE5D6`, ink `#14131A` / `#4E4959`,
  terracotta `#C96442` / `#DA7756`, red `#C4291C`, green `#25704A`. Fonts Satoshi 900/700/500,
  Fraunces italic, Geist Mono, Gaegu.
- **One subject-owned accent is allowed, and only on that subject's objects.** vid65 added Telegram
  blue to the mark, bubbles, node and shield and to nothing else, so the colour read as "that is
  the phone side" with no label. Contrast splits the brand hue in two: `#229ED9` for fills,
  `#1B7FAE` under white text (3.09:1 fails AA, 4.58:1 passes).
- **A marker ring has to be drawn, not revealed.** `border-radius:50%` can only fade or scale in,
  reading as a shape appearing. An SVG `<ellipse>` with tweened `strokeDashoffset` reads as a pen
  moving.
- **A token swap is never the whole job.** Redefining `:root` re-skinned 90% of vid63 for free and
  left 14 literal hex colours inside tweens invisible on the new ground. Grep the script for `#`
  hex literals after any re-skin.
- **Mock before building, always.** An ASCII preview got a theme approved that was rejected the
  moment it was rendered. Two or three real full-size frames of the actual composition cost about
  20 minutes and settle it.

---

## The three face states, as currently solved

Constants are re-derived per take, every time. The three shapes are stable:

| state | vid63 | vid64 | vid65 | vid66 |
|---|---|---|---|---|
| FULL | 0.00 to 1.50 | 0.000 to 1.660 | 0.000 to 1.340 | 0.00 to 1.40 |
| CARD | 560x700, s=0.519 | 560x700 x260,y880, s=0.70 | 560x700 x260,y880, s=0.62 | 580x720 x250,y870, s=0.72 |
| SPLIT | column x440-1080 | none in the file | none in the file | column x540-1080, s=0.85 |
| face share | 46% | 66% | 48% | 82% |

- **Solve the card scale, do not type it.** A card of width W at scale s shows W/s source columns.
  vid64's s=0.70 shows 800, which puts the head centre on the card centre while the video still
  covers the card's left edge.
- **Then hit-test it.** vid65 rendered the real crop at s=0.60/0.64/0.68 and at the shipped rect
  across 8 beats before committing. vid64 round 2 proved a detector can be 130px wrong about this.
- **Solve from the worst case, and from the contour, not the bbox.** The creator leans in and
  drifts right by the CTA (vid65: face centre x555 at t=0.5, x620 at t=23.0). vid66's split was
  solved from the face contour: worst face-left x598, worst face-right x1048.
- **OFF collapses into the card's own rect** so nothing slides in from off-frame.
- **A split is a vertical column, not a horizontal band, unless the arithmetic says otherwise.** A
  full-width band can only be 1080 wide at scale 1, and vid66's head is 745px against 755 rows of
  room above the chrome. vid66b did ship a horizontal seam, at y700 with the picture translated
  down 352 (crown y748, chin y1547), but only because it was copying a reference shot for shot.

---

## Structure

```
0.00 to 1.40   full-bleed face, composed at t=0, furniture settles (no entrances)
1.42 onward    card beats at the important lines; designed scenes carry the rest
```

Four card beats plus the short open. Face share about 30%, reading as "present throughout" with
no full-bleed talking stretch after the hook.

**Put the announcement where the claim is spoken.** A rebuilt X card playing under the line that
makes the claim means the source of the claim arrives exactly as the claim is made. A cascade that
reads in 1.9s: card spring, head, line 1, line 2, media, pill, meta, action row, with the view
count and the heart landing last.

---

## The floating card

One face element tweened between states, never cut between them:

```
HERO  inset(0.1px 0.2px 0.3px 0.4px round 0.5px)
CARD  inset(<solved>px ... round 32px)     video at scale .6, transform-origin 50% 0%
OFF   collapses INTO the card's own rect, so a card-in grows from where the card belongs
```

**Every number must stay non-collapsible.** Browsers collapse `inset()` shorthand when
serializing computed clip-path (`left == right` gives three values, `round 0px` is dropped
entirely), and GSAP interpolates the raw strings by number index. A five-number target against a
collapsed four-number start shifts every later slot, which once animated a 32px corner radius
inside the left inset and painted a 200px dark slab through every card open and close. Hold frames
were pixel-perfect; only transition frames broke, which is why every gate and every beat-frame QA
passed.

Use slightly distinct insets (216.1 against 215.9) and never a 0 radius (0.5px reads as square).
Verify with a seek probe reading `getComputedStyle(...).clipPath` at mid-transition times: a
mispair shows up as a radius-sized number in an inset slot.

**Do not pixel-scan for the dark slab.** It false-positives on dark wardrobe and furniture in the
footage itself.

**No scale-breathing on a clipped video.** `clip-path` resolves in element space *before*
transform, so any scale drags the card edge. The A-roll's own motion is enough life.

---

## Theme (the vid42-era statement, superseded in skin, intact in principle)

Per subject, as always, but grounded in **the creator's own room lighting** rather than invented.
vid42's violet was sampled from the light on that wall, which is why the same launch produced an
unmistakably different reel from the `paper-split` cut of the same story.

Two templates covering one launch reused the entire asset pool verbatim. The differentiation is
theme, type stack and scene grammar (machine events against rebuilt post cards), not facts.

The principle survived every reskin since and got sharper: **ask what the subject is physically
made of.** Printed credentials became ink navy stock and gold foil (vid49). An API key lives in a
`.env`, a terminal and an editor, so every surface became a dev-tool paper surface with one
syntax-highlight system (vid55). A film about Apple's design language could not be built in the
house paper without arguing against itself (vid66).

---

## three.js as a recurring object

Used on exactly **two beats** in vid42: the hook (a rigid machine lattice collapsing into a
waveform-modulated voiceprint sphere on "your actual voice") and the analyzer's output sigil (the
same cloud re-forming from scatter inside a DOM instrument bezel).

**The object recurring is what makes it feel designed rather than decorative.**

**A DOM bezel around a WebGL core is the strongest hybrid.** The ring, tick marks and label are
crisp CSS; only the thing inside needs to be 3D.

Sizing is arithmetic, not taste. See `playbooks/threejs.md`. One round shipped a sphere about
1670px across that swamped the title and ran under the captions, and a lattice so dark the Reels
cover read as empty.

---

## Scene grammar: machine events

These reels read as instruments doing work rather than cards presenting information. The vocabulary:
dials with needles that hunt before they stall, capsules descending tracks through gates,
ampoules filling, tokens routing, pods ejecting and returning along dashed paths. Type survives
as instrument labels.

**Three saturated hues with one job each is not a multi-colour wash.** The ban is on gradient
display type and glow on *type*, not on saturation. A lab instrument is allowed emissive glow on
its own hardware.

---

## Transitions

**Do not wipe where the VO has no gap.** Retime every transition against the word list: wipes
survive only where the gap is at least about 0.18 to 0.20s, and everywhere else becomes a flash
cut. Where the VO is continuous, a wipe simply eats the caption it lands on.

---

## Entrances

**No opacity cross-fade on arrivals.** vid66 stripped `opacity` out of every arrival helper
(`bring`, `bringX`, `pop`, `slam`), leaving motion-only entrances. They read as harder cuts, suit
a fast edit better, and remove every frame where legible copy sits at 20% alpha over paper.

**Hook elements are composed AT t=0.** vid64 shipped an eyebrow arriving at 0.14 and a claim plate
at 0.40, so the Instagram thumbnail carried no text at all. Put the first second's motion into a
rule drawing or a number taking a hit, never into the copy arriving.

---

## Captions

- **Size the caption band against its worst-case line count.** vid64 shipped 66px at line-height
  1.06, which is 140px tall, into a 104px gap above the card. Every one-line caption passed and
  every two-line caption put its second line on the creator's face, twice in one film.
- **Measure the ink box, not the block box.** A centred 940px caption has a block box that reaches
  the right rail while its glyphs sit nowhere near it. Use a Range over the text nodes; chasing the
  block box shrinks type for nothing. Corollary from vid66b: a full-width centred text container
  measures 1080px wide, so wrap the word in an inline-block span and the box becomes the ink.
- **Give each caption its own `top`.** Once the face moves into a card, captions can no longer
  live at one fixed y: around y1380 while a panel hides the face, around y760 in hook and CTA
  where it does not.
- **A big lockup and a caption saying the same words is one element too many.** vid42's hook runs
  caption-free for 3.28s and the lockup carries it.
- **Counters step on the event, do not tween to it.** `count()` with an ease read "3 / 3" while the
  second of three cards was still in flight. Use a discrete `tl.call` per landing.
- **`ghost()` at 0.13 opacity is invisible on a black ground; 0.22 reads as pending.**

---

## Stock footage, when asked for

Add it as a **ground layer** (`z-index:4`, above the ambient wash, below every designed panel) so
the approved structure does not move. `blur(7px) brightness(.44)` at opacity .52, each clip with a
slow counter-drift.

- **"Relevant" means it connects to the line it plays under.** One clip per claim, not generic
  technology footage.
- **Grade at the ffmpeg stage, not in CSS.** CSS filters cost render time on every frame and are
  harder to tune per clip.
- **Exposure is per-clip, never per-layer.** Three dark booths and one white-wall clip at a shared
  setting washed out the whole scene. A shared filter is an assumption that the plates are exposed
  alike. Frame-check each plate separately.
- Refuse anything that would misrepresent the product: real singers' faces on a card representing
  AI voices, for instance.
