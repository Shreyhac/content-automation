# fast-cut-ad: visual grammar

**The format pivoted three times across roughly twenty versions, and the two shipped films do
not share one.** Read this section before assuming any older number applies.

| Film | Approved format |
|---|---|
| the client UGC reel (`hfad/`, v16) | **Product card over A-roll**, the Cursor-ad grammar. The A-roll is soft behind the card except at the hook, the turn and the ask |
| the six-tools demo film (`hfad2/`, v20) | **Full-bleed talking head as the spine**, fast static crop-cuts, real b-roll, a two-pane split for the tool block, organic drawn overlays. **This is the current approved system**, delivered 2026-08-14 and awaiting the owner's verdict |

The delivered six-tools cut is in `reference-cuts/fast-cut-ad-demo-six-tools.mp4`. Watch it before
rebuilding anything below.

What died on the way: abstract brand-geometry graphics on a bare brand-colour ground (v1,
rejected), a product-UI rebuild that was still not the reference's format (v2, rejected), and on
the six-tools film a persistent product pill plus blobs and squiggles (v13 to v17, all removed).

---

## Palette

The client's own brand book, page 18. Not invented, and **not the website's** (see PROFILE.md
rule 2).

| token | hex | use |
|---|---|---|
| ground | `#040120` | Foresight Blue shade, the canvas |
| ground-lift | `#0B0538` | raised panels |
| blue | `#246CE0` | Foresight Blue, structure, rings, the calm state |
| blue-tint | `#DAE8FF` | text on ground, ring highlights |
| orange | `#FD8502` | Momentum Orange, **spent once per film**, on the value transfer |
| orange-tint | `#FFEDE4` | the value chip |
| pink | `#CE3DA2` | Presence Pink, gradient only, never type |
| white | `#FFFFFF` | Clarity White |
| ink-dim | `#837E97` | mono labels, secondary |

The brand gradient, top to bottom: `#040120`, `#246CE0`, `#CE3DA2`, `#FD8502`, `#FFFFFF`.
Four intensity levels are specified, the same ramp compressed toward the dark end. Level 1 is
nearly all `#040120`; level 4 is the full hero. Restrained levels for supporting surfaces.

**Radial only.** A linear ramp across this much hue travel bands in H.264, and the guideline art
itself shows the stepping.

**Pairing rule (p19): the ground decides the foreground.** Background = a shade, foreground = the
matching tint. Or background = a tint, foreground = the matching primary. **Never mix families in
one pairing.**

### No graphic sits on bare colour

The one theme note on the six-tools film was *"is the theme matching with the theme?"* over a beat
that was already brand-correct navy. The fault was **flat gradient voids**. Every graphic in the
approved cut sits over the presenter's own footage: the tool grid plays over them dimmed, the app
block over them blurred. A brand-blue panel with nothing behind it is the defect this rule exists
to prevent.

---

## Type

| role | family | notes |
|---|---|---|
| display | Season Mix VF, wght 300 to 400 | Statements only. **Paid licence, not owned.** The six-tools film shipped without it entirely |
| body and captions | IBM Plex Sans 600/700 | |
| labels, chips, numerals | IBM Plex Mono 500, uppercase, `letter-spacing: .12em` | |

Working sizes at 1080x1920 logical: statements 92 to 116px, body 34 to 40px, mono labels 22 to
26px.

Plex Sans ships to the project as woff2; Plex Mono resolves through the renderer's built-in
family. Both films are Plex throughout, on the client's instruction.

---

## Corners, depth and motion

- Radius 20 to 28px on panels, 999px on chips. Borders 2px minimum.
- **Depth is glow, never drop-shadow**: `box-shadow: 0 0 80px rgba(36,108,224,.28)`.
- Ease family is theirs: `cubic-bezier(.22,1,.36,1)`, which maps to GSAP `power3.out` / `expo.out`.
  Entrances 0.5 to 0.8s. Nothing snaps.

**The exception, measured in round 9.** The client supplied a competitor ad (a Viktor AI-employee
spot, 79s) and called it *"smooth and subtle but so elegant."* Scene detection found **no cuts at
all** in it, even at a 5% threshold: one continuous take, all visual interest from soft persistent
overlays that fade in, hold 5 to 10s, and drift gently. Translated to a spec: kill flash-cuts,
replace every `back.out`/`expo.out` with power2 fade-drifts of 0.4 to 0.5s, fade section changes
instead of hard-cutting, one calm event at a time. **Measure a style reference before translating
it.** "Elegant" was an adjective until scene detection made it a number.

That competitor grammar and rule 4's sub-1.5s pacing pull in opposite directions. What actually
shipped in v20 keeps the fast crop-cuts on the presenter and gives the b-roll and reveal beats the
long calm holds.

---

## The organic drawing language

v13 ported the reference's *devices* (a persistent pill, crossfades) in the portfolio's own
vocabulary of rounded rects, straight hairlines and cream panes, and the owner saw *"no
difference"*. Four stills later the actual ask was the reference's **drawing style**:

- curved **dotted** connectors around a central hub, not a straight lattice
- irregular blob shapes, not capsules
- white washes that melt into the footage, not opaque panes
- playful pop-with-overshoot keyframing

All of it is cheap in HTML: SVG quadratic paths with `stroke-dasharray`, irregular
`border-radius`, a linear white-to-transparent wash. **Copy the drawing style, not just the
structure.** Note that the blob and the squiggle were themselves cut by v20; what survived is the
curved dotted ring and the drawn connector lines.

---

## Face and layout, the six-tools film (the current system)

Delivered at 2160x3840; all geometry below is in the composition's 1080x1920 logical space.

**Three states, and the film opens without the product.**

    OPENER   a blurred hands crop, boxblur 12:2 applied at cut time in ffmpeg
             the product is never on screen before "lives on my Mac"
    FULL     full-bleed A-roll, the spine of the film, with static crop-cuts for density
    SPLIT    a real two-pane split: cream pane on top, the presenter cropped into the bottom pane
             (splitwrap crops the native A-roll, top offset -380), captions on the seam

- The split was **flipped four times** before it settled. The final shape is the owner's own:
  animations in the top pane, the presenter in the bottom, captions at the seam between the two.
- **The split arrives fully formed AT the cut.** Tweening the top pane in over 7 frames left the
  presenter's face still showing above the pane's face and the reviewer read it as *"frame is
  repeating"*. A state change happens at a cut, never across one.
- **A scrim over the opener is dead.** Two strengths of dark scrim were rejected before the blur
  replaced it. Blur hides the screen; a scrim just dims it.

**Measured overlay bands, against the master's own chin line:**

| element | y (of 1920) | why |
|---|---|---|
| the presenter's chin, measured per frame from the master | about y810 to y900 | |
| chest-band chips and supers | y908 | first round's note was *"place these at the chest of the man, not on top of face"* |
| the app tile in the hierarchy beat | y920 | clear of the chin |
| the six tool icons under it | y1210 | |
| captions | y1245 to y1470 | above the Meta bottom UI and clear of where the hands come up |

- The hook chips are a **vertical column down the centre at 150px** (they were horizontal at
  132px and covered the captions).
- The graph beat is a **strict 2-column grid at x216 and x864 over three y-rows**. An organic
  scatter was rejected twice and a loose grid once before this landed.
- The hierarchy beat draws **trunk, rail and six drops** as dashed connector lines from the app
  tile down to the six tools. There is no seventh struck-through slot; that idea was cut.
- The endcard is the **client's own outro clip** (3.9s, 1080p, with its own audio in the bed).

---

## Face and layout, video 1 (the card-over-A-roll grammar)

Kept because it is the approved system for a UGC or avatar-led cut, and because the numbers are
solved.

Reverse-engineered from the three Cursor / trycursor Instagram ads the client sent as the literal
target:

- The A-roll runs **sharp and full-frame at the hook, the turn and the ask**, and is **softened
  behind the card everywhere else**: `blur(9px) brightness(.66) scale(1.07)`. **Never both
  blurred-behind and a small inset card at once**; the client explicitly rejected that combination.
- **The UI floats as a card**, about 860px wide, with a real drop shadow. Not full-bleed, and not
  a screenshot pasted into a box.
- **A label chip straddles the card's top edge** and renames per beat (the product name plus
  `macOS`, then `Slack`, then `Pending approval`). This is what reads as "the ad is telling you
  what you are looking at".
- **The headline rides above the card**, second line italic in the accent colour.
- **One spoken phrase, boxed, at the bottom.** Not a caption bar: a solid dark rounded chip that
  pops per word.
- Captions over the presenter's A-roll need a scrim: the cream sweater occupies exactly the y1180 to y1320
  caption band, so white text vanished into it. `rgba(5,2,24,.72)` rounded panel.

Face share after the rebuild: about **14% full-frame** (6.3s of 43.6s) plus 10.8s as a small card
beside the product. v1's 66% face was one of the two faults that forced the rebuild.

**The card over the presenter's face is why the format works**: with no lip sync visible behind a card, the
reference can hold the creator on screen through VO-only beats that have no matching footage.

**Two copies of one `<video>` at the same `data-start` stay in frame sync.** That is the whole
trick: one copy full-frame and blurred as the ground, a second copy `clip-path`-cropped and
scaled into the card. The card can drop away while the ground carries on, and un-blurring the
ground gives the return to full-frame for free, with no third clip restarting the video.

---

## The orb

`client-brand/orb-lab/` is the client's own orb motion lab. It is **the product's signature in the
cut** and it appears at three points in video 1: the fn-hold b-roll, the wake moment (monochrome
blooming into the brand gradient), and hovering over the Slack UI while a thread loads.

Port it as **draw code, not as a package.** The lab is React with a `thinking-orbs` dependency and
none of that is needed: `traceOrbPath`, `drawVoice`, `drawHoldField`, `drawFlow` and
`drawAcknowledgement` are pure canvas 2D and lift straight in. Collapse the nine state descriptors
in `public/animations/*.json` into **one lerpable param object driven by a function of local
time**, which is what buys the smooth monochrome-to-gradient transition the descriptors alone
cannot do, and lets the `voice` term ride a real RMS envelope of the actual VO instead of a loop.

It was pulled back out of beats the client had not asked for it in, twice. Use it where they asked.

---

## Captions

Word-level whisper onsets, always, on both films.

Video 1's VO arrived as five separate audio files, one per script line. Each was transcribed
independently, then each word array was offset by that line's `data-start` and merged into one
caption timeline. Grouping into 3 to 4 word cards on punctuation boundaries with each card's exit
clamped to `next_card_start - 0.04s` gives no gap and no overlap without hand-timing 42 cards.

Three words take Momentum Orange across the whole of the six-tools film and no more: **six**, the
**product name**, **both**.

---

## What NOT to do

- No impacts, no risers, no glitch, **and as of the six-tools film's round 5, no added sound of
  any kind.** The product is "omnipresent, not intrusive".
- Orange appears exactly once per film, on the value transfer. Never decorative.
- No flat solid backgrounds. No linear gradients anywhere.
- No drop-shadows on the six-tools film's graphics. Glow only.
- No camera moves. Every punch-in is a pre-rendered static crop, hard-cut to.
- Never let a graphic replace the presenter at the direct ask.
- No branded hub, and no product-shaped tile, before the product reveal.
