# Nader Nadernejad, Nadernejad Media

**Agency client, not a personal channel.** nadernejadmedia.com: "Online Reputation Management and
AI Business Solutions." The work is client-facing and sometimes sponsored, which raises the cost
of every factual error.

| | |
|---|---|
| Primary format | 16:9 YouTube long-form, 3 to 4 minutes, 3840x2160 at 30fps |
| Secondary | 9:16 vertical cutdowns derived from the long-form, about 45s |
| Shipped | vid39 (9:16 short), vid44 (16:9 long-form), vid46 (16:9 sponsored long-form plus a 9:16 short) |
| Studio | Seated at a desk, tight to medium close-up, a wall-mounted screen behind him |

---

## Hard rules

### 1. Never show his face while he reads his notes

**This is a constraint on the whole edit, not a decoration.** He reads from notes for a large
fraction of a long take (about 45% of seconds in one 60 to 150s stretch). Every face state in the
video is driven by a **measured face-safe window map**, never by taste.

Run the gaze pass before composing anything: `tools/vision/gaze-detect.swift` then
`tools/vision/build_windows.py`. Full method in `playbooks/gaze-detection.md`.

**Err toward hiding him.** An extra second of graphics is a soft cost; showing him reading is a
hard failure.

### 2. The hook line plays on the clean face; the acted scene starts on the NEXT beat

Overlaying the hero animation on his face during the hook was rejected even though every
individual piece of it had been approved. Give the hook line the face, then cut.

### 3. The split is a floating CARD, not a band

Ink side rails on a narrow band read to him as "weird black bars". The approved device is a
centred rounded card with content full-bleed behind it. And **the card is a MOVE, not a
placement**: the face never cuts between sizes, it travels. See
`playbooks/face-card-device.md`.

### 4. No graphics on the face, ever

Card mode or full-bleed mode, no third mode. Three of eight round-one complaints on one film were
this. See `docs/03-quality-bar.md` class 4.

### 5. No face-tracking tween

A smoothed per-window follow curve was built to hold him centred as he sways, and he read it as a
bug: "why is Nader's frame always moving left-right, you have added some issue." A person swaying
inside a still frame is normal; a frame sliding around a person is not. **One constant `tx` per
window.** Keep all the measurement, keep the residual veto, just resolve it to a single number.

### 6. Real logos and favicons, never placeholders

Coloured dots next to engine names read as placeholders and get called out. Simple Icons for
brands (`cdn.simpleicons.org/<slug>`), Google's favicon service for news outlets
(`google.com/s2/favicons?domain=<d>&sz=128`). White 5px-padded tiles normalise mixed-shape
favicons on dark chips.

### 7. He explicitly wants stock b-roll. Do not propose dropping it

"More stock footage" is a **density** note, not a count: one cut per act, placed only where the
layout already has free space so nothing gets re-timed. Always carded, never full-bleed. Grade
every clip toward the palette. See `playbooks/stock-footage.md`.

"Better A-rolls and more A-rolls" from him means **b-roll, not face time.** Confirmed directly.
Face share fell from 43.2% to 39.4% in a round he approved.

### 8. Sponsored work has a zero-error bar

Resolve promo codes against the partner URL, never against whisper. Every on-screen figure needs
a primary source, attributed on screen. A competitor's figures are attributed to the competitor
and never rendered in the alert colour. A verdict carries the VO's own qualifier. The caption
pack must flag paid promotion.

---

## Delivery

- Two-pass `loudnorm` to **-14 LUFS / -1.0 dBTP** for YouTube.
- No em dashes.
- The file-size matching rule does **not** apply to him (that is the two Instagram creators).
- SFX: median **0.060**, ceiling 0.096, bed 0.055. He has halved it on each complaint from 0.20.

---

## How he reviews

He gives a feeling plus an itemised list, and the list is usually a symptom of one structural
fault. On the round that mattered most, he disliked almost everything and offered one positive:
"the globe animations are nice." That single positive was the whole diagnosis, because the 3D
field was the only device in the film that was not a rounded rectangle.

**He also reverses decisions, and that is the expensive kind.** He chose to keep a duplicated
take, then wanted the repeated line cut, which invalidated the chunk map, every T0, every caption
offset and the whole gaze and card solve. **Get any cut decision confirmed before any build
work.**
