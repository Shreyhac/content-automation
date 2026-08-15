# vid46 design system, "Signal Blue" (Incogni × the client, sponsored long-form 16:9)

> **ROUND 2.** The owner rejected round 1's look: *"it's looking very cheap"*, with
> one positive: *"the globe animations are nice."* The diagnosis and the full brief are
> in `vid46-feedback-round1.md`; the sections below marked **R2** are what changed.

Third production for this client, second long-form. Inherits vid44's chunked architecture and
six-layer ground craft; everything chromatic is re-derived from **incogni.com's own CSS custom
properties**, not invented and not carried over from Trustmark's gold.

## Canvas

3840×2160 @ 30fps, 8 chunks (`c1…c8`), **6702 frames** total (223.400s / 3:43.4).

**R2: the A-roll was re-cut.** The owner reversed the round-1 "keep both takes"
decision, so the two duplicated passages are gone: original frames 2733–2869
(91.100–95.667s, the Aura-coverage repeat) and 3743–4098 (124.767–136.633s, the
Incogni-focus repeat). 493 frames removed. Both splice points sit inside note-reading
runs, so the face is hidden across both joins and neither can read as a jump cut 
that is why those particular in/out points were chosen. See `recut.sh`.

Every downstream measurement was re-derived, not remapped: new word-level transcript
(`transcript.json`), new gaze map (`vid46/build_windows.py` → 17 windows, 88.0s,
39.4%), new card transforms (`vid46/solve_card.py`), new chunk boundaries
(`plan_chunks.py` → `recut/chunks.json`).

## Palette: sampled from live incogni.com

| Token | Hex | Site origin | Role |
|---|---|---|---|
| `--ink` | `#09090B` | `--shades-1000/950` | primary ground |
| `--ink2` / `--ink3` | `#131317` / `#1B1B20` | n/a | raised panel / sunk well on dark |
| `--line` / `--line2` | `#2A2A31` / `#3A3A43` | n/a | hairlines on dark |
| `--fg` / `--fgMut` / `--fgDim` | `#FAFAFA` / `#B0B0B6` / `#84848C` | `--shades-50` | type on dark |
| `--blue` | `#3555FF` | `--blue-500` | **THE** system accent |
| `--blueHi` / `--blueDeep` | `#8EACFF` / `#1B2FF5` | `--blue-300/600` | glow highlight / pressed |
| `--navy` / `--navyDeep` | `#191D8F` / `#141457` | `--blue-900/950` | deep field, card grounds |
| `--green` / `--greenDeep` | `#158038` / `#00834E` | site accent | **removed · verified · winner** |
| `--greenText` | `#4ADE80` | n/a | green type on dark (WCAG-safe) |
| `--red` | `#E5372B` | site "identity theft" red | **exposed · for sale** only |
| `--paper` / `--card` / `--sunk` | `#FFFFFF` / `#FAFAFA` / `#EBEBEB` | `--shades-0/50/100` | white card surfaces |
| `--cInk` / `--cMut` | `#000000` / `#454545` | `--shades-1000/800` | type ON white |
| `--onBlue` | `#F0F5FF` | `--blue-50` | type on a blue fill |

**Colour discipline.** Blue is the system: structure, UI, Incogni. Green means *removed,
verified, the winner* and never decorates. Red means *exposed / for sale* and appears in exactly
three places (the hook's exposed record, the broker-sale burst, the "paying twice" ledger).
Aura's side of every comparison is **neutral**: `--fgMut` on `--ink2`, never red. Painting a
competitor in the alert colour would be editorialising past what he actually says.

## Type

- **Rethink Sans 800**: display: the big numbers (750, 420+, 245M, $7.99), verdicts, act titles.
- **DM Sans 700 / 500 / 400**: captions, UI labels, card body, chart labels. The site's own face.
- **Geist Mono**: data labels, URLs, plan names, coupon code, timestamps. `tabular-nums` on
  every number column.
- Caps labels carry `letter-spacing: .08em`. Both brand fonts ship as latin variable woff2 in
  `assets/fonts/` (`dm-sans-var`, `rethink-sans-var`).

## R2: THE CARRIERS: what replaced the box

The round-1 rejection was not a list of bugs, it was one structural fault. Ten
different beats, the record card, the buyer tiles, the action rows, the "up for
sale" panel, the module slabs, the ledger tiles, the price carriages, the router
tokens, the reason cards, the coupon, were all the same rounded rectangle with the
same fade-up entrance. The three.js field was the only device that was not a box,
which is exactly why it was the only thing he liked.

So round 2 replaced the *carrier*, not the contents. Defined in `assets/base.css`:

| Carrier | Where | What it is |
|---|---|---|
| `.rec` **redaction** | c1 hook, c1/c2 "your record" | values on lit rules with black bars that slide off; the bar's own glowing left edge is the scan line |
| `.ev` **emitter** | c2 "how it gets collected" | three events drawn as line art on the ground, each firing a `.pkt` at the FOR SALE stamp |
| `.slab` **stack** | c4/c5 Aura's modules | real drawn icons on slabs that physically pile up, so the tower becomes top-heavy |
| `.rail` + `.knob` | c4 coverage, c5/c6 price | ONE shared axis; a gap becomes a length instead of two numbers |
| `.figure` | 750, 420+, 245M | a verified number on the bare ground with a rule and its attribution |
| `.seal` | Deloitte, 30-day | verification that STAMPS in with an overshoot |
| `.spine` / `.limb` / `.it` | c1/c2 buyers, c3 types, c7 trade-off | a connector with items hanging off it; nothing has a fixed height, so copy cannot overflow |
| `.ldg` / `.strk` | c5 "you already pay" | the strike lands on the slab that already exists |
| `.wcard` | **c8 coupon ONLY** | the one card left in the film |

That last row is the point. Stripping the box everywhere else is what lets the coupon
read as the payoff rather than as the tenth rounded rectangle.

**Type motion: one device.** Round 1 had eight variants of `y:+20, opacity:0→1`.
Round 2 has one signature: the per-word masked rise (`wordRise`, `.wr`), plus two
specialised cases, `digitSettle` for figures and a character stagger used exactly
once, on the coupon code. Published numbers ARRIVE: `digitSettle` rolls in from
within ~2% and locks, because round 1 ticked 750/245M/200 up from zero and so spent a
third of each beat displaying a figure that was simply wrong under an audited
attribution line.

**The two-mode layout rule.** Three of his eight complaints were "text/box on the
face". Patching them individually would have kept producing more, so every beat is
now either **CARD** (A-roll in the right-hand card, graphics own x180–2080, a 200px
gutter, zero overlap by construction) or **FULL-BLEED** (the face is the whole
picture, and at most ONE self-grounded pill sits in space measured from
`facebox.csv` / `crown.csv` for that window, over a feathered scrim). There is no
third mode.

## The ground: six layers, never flat

**R2: the ground was the other half of "cheap".** Round 1 filled the frame with
`#09090B`, floated glows at .09–.20 over it, and then pushed the corners to 86% black.
Net result: roughly 90% of every 4K frame sat within three RGB values of `#0A0A0C`. It
read as a black slide, not a lit set, and he asked for "a little more premium with
gradients" twice, the second time *"I beg you for this"*.

It is now an actual light rig. Base dropped to `#06060A` so the key has somewhere to
lift FROM, and luminance travels roughly `#05050A → #1B2140` across the diagonal:

| Layer | Spec |
|---|---|
| `.gA` | **blue key** `#3A5CFF`, 4400px, **34%** core: the frame's one real light source, upper left, orbits P=300s |
| `.gV` | **violet mid** `#5A3CDC`, 3600px, 20%, upper right, P=420s: breaks the single hue so the dark half is a different COLOUR, not just dimmer |
| `.gS` | **stage lift**: a wide shallow ellipse along the floor, 17%. Static: this is the floor, and drifting it reads as the room sliding. Stops the bottom third going dead behind the caption band |
| `.gB` | green counter-glow `#158038`, 3000px, **7%**, P=380s: rationed; .17 turned the frame swampy in test |
| `.gC` | navy bloom `#191D8F`, 2800px, 16%, P=240s |
| `.gSh` | **sheen**: one 6000×2000 ellipse at 6%, static. Enormous and faint on purpose: at 4K this is what separates "lit" from "tinted" |
| `.grid` | dot grid, **96px at 3.4%** (was 68px at 5%) |
| `.grain` | inline SVG `feTurbulence` + `feColorMatrix saturate 0`, 300px tile, **7.5%**: raised because the ground now has real ramps to dither |
| `.vig` | radial vignette, **off-centre at 42%/40%** so it shapes toward the key light instead of flattening |

**The scan grid is gone.** Round 1's 240px blue line grid plus the 68px dot grid read
as graph paper at 4K, my own round-1 QA flagged it as a likely contributor to
"cheap". One texture layer is enough.

**Radial only for ramps.** The scan grid is a hard-stop linear gradient (a line, not a ramp) so
it cannot band. Smooth linear gradients stay banned on the ground.

**Phase continuity across the 7 joins.** Every motion is linear and keyed to *absolute film
time*: a chunk starting at `T0` tweens `rotation` from `360·T0/P` to `360·(T0+D)/P`; the grids
tween a proxy that writes `backgroundPosition` by the same rule. Nothing resets at a join.

## Face grammar: measured, tracked, and self-limiting

Standing client rule: **never show his face while he reads off-camera.** See
`vid46-breakdown.md` for how this take broke vid44's single-signal detector and why the
classifier is now `eyeOpen < 0.30 OR faceAspect < 0.905`.

**Card (CARD-R: this client's standing default since vid44 round 2):**
`x2280→3660 · y440→1720` (1380×1280), 32px radius, 1px `--line2` hairline, soft outer shadow.

In `vid46/solve_card.py` → `card-transforms.json`:

1. **Coverage floor.** `s ≥ 1280/2160 = 0.597`, or the scaled frame stops covering the card and
   the ground shows through. The first solve ignored this and produced `s = 0.486` transforms
   that ffmpeg refused to crop, the bug that caught it.
2. **R2: ONE CONSTANT `tx` PER WINDOW. The tracking curve is gone.** Round 1 gave each window
   a smoothed tx track (±1.4s moving average at 0.4s spacing), reasoning that a constant is only
   right at the median. The owner's read of the result was *"why is the presenter's frame always moving
   left-right… you have added some issue."* A follow that slow does not register as camera
   operation, it registers as a bug. Subdivision of long windows went with it: splitting at 5.5s
   is only safe if every sub-boundary is also a cut, or the face jumps mid-shot.
3. **A self-limiting card test, now measured against the constant.** `resid > 120px` (8.7% of
   card width) ⇒ that window is **never carded** and plays full-bleed, where the source framing
   already holds him. Sway is read over a robust p05–p95 range, not min–max, so one bad contour
   detection cannot veto a stable window. **12 of 17 windows card (73.9s); 5 are full-bleed only
   (14.1s).**

Vertical: crown sits at 42% of the leftover slack, so there is more room below the chin than
above the crown and the head never looks glued to the card's top edge.

**Never crop the crown**: he has flagged that twice across previous productions.

## Split and layout

- A-roll **RIGHT** in the card, graphics/b-roll **LEFT**: the vid44 round-2 reversal, now the
  default. Graphics field is `x180 → x2080`, leaving a 200px gutter before the card.
- **The hook plays on the clean full-bleed face** (W01–W03, 0→17.05s). Only a small kicker pill
  and the engine chips may sit over him. The acted animation starts at the next beat.
- Full-frame graphics scenes (no face) use the whole 3840 width.

## The two duplicate takes: R2: CUT

Round 1 kept both repeated passages and escalated the picture across each repeat. The
owner flagged the first one as a defect (*"this line is repeating twice… we need to
make it a single line itself"*) and confirmed both cuts.

| Passage | Kept | Dropped | Why |
|---|---|---|---|
| Aura coverage | 85.18–90.80 | **91.30–95.46** | take 1 carries the "third-party reviews" attribution, which is the cover a competitor claim needs in a sponsored video; take 2 states it as fact |
| Incogni focus | 136.74–146.96 | **124.88–136.58** | take 2 is 1.5s tighter and is the only one of the two that overlaps face-safe windows |

The escalation devices did not go to waste, the *gap bar* became c4's shared coverage
rail and the *guarantee stamp* became c5's seal.

## Signature devices

- **Exposure record**: a white data-broker record card that fills in with his own details as
  the hook lands, then multiplies into a wall of 750.
- **The 750 wall**: 750 broker chips build on a grid, five state registries labelled; PRC+EFF
  credit line locked to the corner.
- **Deloitte seal**: the 420+/245M numbers arrive stamped, with the assurance-report line.
- **Head-to-head rail**: Incogni blue vs Aura neutral, a single shared axis so the 420/200
  gap is a length, not two numbers.
- **The bundle ledger**: Aura's five extras as tiles that each pick up a "you already pay for
  this" strike, resolving to the doubled cost.
- **Price rail**: $7.99 vs $12 on one axis with the annual billing line underneath.
- **The coupon lockup**: `CODEWORD` in Geist Mono on a blue chip, 60% OFF, `incogni.com/<partner>`,
  both placeholders for the sponsor's real code and affiliate URL,
  30-day guarantee, all verified live.

## Motion + audio

- Scene boundaries land on word onsets from `transcript.json`. Nothing static longer than 1s.
- Layout first (static hero frames), then `gsap.from()` entrances. No exit tweens except the
  final scene, transitions handle exits.
- Every field is **composed at frame 0** of its chunk and only settles; in a concatenated film
  each chunk's frame 0 is a hard cut, and vid44 shipped six near-empty ones before this rule.
- **R2: SFX.** His note: *"why the fuck are you just using two or three SFX… reduce the
  volume of ALL the SFX a bit, it's too loud… the Riser SFX is very weird. Same with the
  thud."* Round 1 measured 236 placements over what looked like 17 files, but
  `boom.mp3`/`cboom.mp3` were byte-identical and so were `riser.mp3`/`riser2.mp3`, so it
  was 15 distinct sounds, and boom alone carried 48 hits. The top four distinct sounds
  were 55% of every transient in the film; his "two or three" was a fair description.

  Now: **40 distinct sounds** curated from the repo's own `sfx-library/` (`curate_sfx.sh`),
  each peak-normalised to −3 dBFS and **head-trimmed**: several library files carried
  20–80ms of digital black that landed the transient late against its word. `thud` and
  both risers are retired by name. `sfx.py` is the single source of truth for the bed and
  it *enforces* the budget rather than trusting the author: no file over 8.5% of
  placements, median volume ≤ 0.125, ceiling ≤ 0.18, sustained beds ≤ 0.085, and a hard
  refusal on the retired files. Volumes now run 0.08–0.16 with a 0.10 median.
- No music bed. One continuous cleaned VO master muxed at assembly, the chunk renders
  carry SFX only, so no join can click.
- Full burned-in captions, generated from the word-level transcript, never hand-typed.
