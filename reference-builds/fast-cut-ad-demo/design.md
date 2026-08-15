# The client's design system

Source: the client's Lightweight Guidelines V1.0 (`client/figma/brandbook-frames/`), palette p18,
gradient p21-22, iconography p27. Not invented, every value below is theirs.

## Palette

| token | hex | use |
|---|---|---|
| ground | `#040120` | Foresight Blue shade, the canvas |
| ground-lift | `#0B0538` | raised panels |
| blue | `#246CE0` | Foresight Blue, structure, rings, the calm state |
| blue-tint | `#DAE8FF` | text on ground, ring highlights |
| orange | `#FD8502` | Momentum Orange, **spent once**, on the value transfer |
| orange-tint | `#FFEDE4` | the value chip |
| pink | `#CE3DA2` | Presence Pink, gradient only, never type |
| white | `#FFFFFF` | Clarity White |
| ink-dim | `#837E97` | mono labels, secondary |

The brand gradient, top→bottom: `#040120 → #246CE0 → #CE3DA2 → #FD8502 → #FFFFFF`.
**Radial only**, a linear ramp across this much hue bands in H.264.

## Type

| role | family | notes |
|---|---|---|
| display | Season Mix VF | wght 300-400. Statements only. |
| body | IBM Plex Sans | |
| mono | IBM Plex Mono | uppercase, `letter-spacing: .12em`. Chips, stage labels, numerals. |

Video scale: statements 92-116px, body 34-40px, mono labels 22-26px.

## Corners & depth

Radius 20-28px on panels, 999px on chips. Depth is glow, never drop-shadow,
`box-shadow: 0 0 80px rgba(36,108,224,.28)`. Borders 2px minimum.

## Motion

Ease family `cubic-bezier(.22,1,.36,1)` (their `--ease-brand`) → GSAP `power3.out` /
`expo.out`. Calm energy: entrances 0.5-0.8s. Nothing snaps.

## Transitions

**Primary, blur crossfade, 0.5s, `sine.inOut`.** Premium/luxury per the transitions
table; matches the client's own "quiet confidence and restraint".
Face shots always start video **and** audio at the same instant, lip sync is
non-negotiable, so the incoming face fades up *over* the outgoing scene rather than
the outgoing scene fading down early.

## What NOT to do

- No impacts, no risers, no glitch. the client product is "omnipresent, not intrusive".
- Orange appears exactly once, on the value transfer. Never decorative.
- No flat solid backgrounds, radial glow + the gradient bleeding from the bottom.
- No linear gradients anywhere.
- No drop-shadows. Glow only.
- Never let a graphic replace the presenter at the direct ask.
