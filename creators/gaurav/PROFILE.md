# thepmfguy ("gaurav")

**One person, two names.** The repo history uses "thepmfguy" and "gaurav" interchangeably. Do not
confuse him with the slot-1 creator (`shreyansharora05`), who is a different person.

| | |
|---|---|
| Format | 9:16 Instagram Reels, 30 to 45s |
| Subjects | AI tooling, model launches, developer tools, listicles |
| A-roll | Delivered **pre-cut, audio-cleaned and colour-graded**. Sometimes selfie-cam outdoors, sometimes seated indoors. |
| Current grammar | vid47 v2: the paper split band. Reference build: `reference-builds/gaurav-vid47/` |

He has the longest and most self-contradicting feedback history of the three. **Read `HISTORY.md`
before applying anything**, and treat only the rules below as standing.

---

## Hard rules

### 1. His footage ships exactly as delivered

"Whatever there is in the video, mirrored or without mirrored, keep that the same."

No hflip even when jacket or shirt text reads backwards. No denoise, no loudnorm, no regrade. He
delivers a finished mix and grade. **Transcode only** (crop and scale), `-c:a copy`.

### 2. His face is never cropped

Full head in frame on full-bleed **and** in the split. A cropped crown reads to him as a bug every
time. Make the face read big by **cropping the dead headroom at the ffmpeg stage**, not by zooming
in the composition.

### 3. The hook is an acted micro-story with him visible, never a type lockup

"We just can't show text, show animations while the man is also visible."

A face-open with kinetic supers alone is dead as a hook. Static pills popping on the face are
still a text stack. The reel should open already in the split with a story running in the graphics
zone.

### 4. Show the real asset of everything you say

Every product claim shows a real or faithfully recreated screen animating, never an abstract
metaphor. Login-gated panels become pixel-accurate recreations; public pages animate the real
screenshot. Rebuild screenshots as native HTML at reel type sizes.

### 5. No IDE palette for a developer-tools subject

Theme-per-subject says GitHub-dark for a reel about GitHub repos, and that is the trap: when the
subject *is* software, dressing the film in the subject's own chrome collapses the two and it
looks like a screenshot rather than an authored film. **Paper is the distance that makes it feel
made.** Watch the corollary: light and white brand marks vanish on paper.

### 6. Retired visual families (do not reintroduce)

| Retired | Why |
|---|---|
| Pixel and game motifs, gamified progress bars, pixel mascots | "The animation looks childish" |
| Espresso and warm-brown scene grounds | "This looks very weird", even on Claude-subject reels |
| The navy window device | Retired with the pixel family |
| Ink pill slabs behind supers | "Boring / cheap" |
| The eyebrow pill when kinetic claim type is also on screen | "Double text": one hook idea gets one text layer |
| A mascot after two consecutive reels | "Why that open claw icon again" |

### 7. SFX 0.10 to 0.19, bottom half under a quiet VO

His self-mixed VO sits around -21 to -25 dB mean, so the house 0.16 to 0.34 range overpowers it.
When he supplies a pack (`library/sfx/saas/`), **he expects to hear it**: 80% of triggers on one
film.

### 8. Match the raw A-roll's file size on delivery

A delivery at a healthy 8.4 Mbps looked "too small" next to the 108MB raw A-roll. See
`docs/06-delivery.md` step 3. Hard requirement.

### 9. No em dashes

---

## The zoom question, settled

His zoom history reads as contradictory because it is take-dependent, not preference-dependent.
The resolution:

- **Never a hard punch-in on a 1080-fitted source.** Scaling a 1080-fitted video resamples and
  reads as grain on low-light footage.
- **A 1620x2880 transcode makes punch-ins up to about 1.4x sample at or below native pixels**, so
  the device is take-resolution-gated, not banned.
- He asks for subtle zoom **animations** (breathing push and pull), not a static crop. Current
  form is punch-and-hold, monotonic within a shot: a punch that returns to base reads as a
  heartbeat.
- **Confirm which surface a zoom note is about.** "Keep the frame stable" applied to designed
  scenes meant kill the camera rig entirely; it did not apply to the A-roll.

---

## How he reviews

Blunt and short. "Looks childish", "very weird", "boring", "not premium", "too coded". Each maps
to a rejection class in `docs/03-quality-bar.md`, and none of them is a request for a nudge.

**His corrections are round-scoped, not permanent law.** A locked-off frame and a ban on wipes
were both correct answers to "too much", and both were reversed by a later "this is boring".
Only the treatment rules (no gradient type, no glow shadows, hairlines) survived every round.

**"Use the colour scheme from the last edit of the same script"** means whatever system the owner
last called premium wins over the channel's previous system. **Ask which donor** before re-skinning
a re-produced script.
