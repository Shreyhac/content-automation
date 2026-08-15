# Nader Nadernejad, Nadernejad Media

**Agency client, not a personal channel.** nadernejadmedia.com: "Online Reputation Management and
AI Business Solutions." The work is client-facing and sometimes sponsored, which raises the cost
of every factual error.

| | |
|---|---|
| Primary format | 16:9 YouTube long-form, 3 to 4 minutes, 3840x2160 at 30fps |
| Secondary | 9:16 vertical cutdowns derived from the long-form, about 45s |
| Shipped | vid39 (9:16 short), vid44 (16:9 long-form), then five sponsored Incogni long-forms with a 9:16 cutdown each: vid46, vid56, vid58, vid59, vid62 |
| Latest | vid62 (Incogni ep5, 16:9 long-form) and vid62 short (60.89s vertical, v2, 2026-08-12) |
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

**As of vid62 round 3, the gate is a WHITELIST, not a blacklist**: the windows he MAY appear in are
enumerated; everywhere else defaults to hidden. A blacklist only flags what its detector produced a
span for, and vid62's `read_guard` missed two of three client "framing is off" notes because
eyelid aperture alone cannot see gaze DIRECTION (it measured 0.347/0.361 at those moments against a
0.379 film median, indistinguishable from looking at the lens). The signal that actually separates
a blink from a read is pupil position inside the eye opening plus head pitch, on a rolling ~1s
median (hand-labelled reads: 0.153-0.326; camera: 0.375-0.440, no overlap). A missing whitelist
window costs a beat of face; a missing blacklist entry ships the defect on screen. **Choose which
way the gate fails.**

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

vid62 round 2 hit the same fault at a new scale: the guard that enforces this only ran while the
face was carded, so full-bleed sections went unchecked and text landed on him 180 times across 23
elements (a promise rail across his chin, competitor caveats across his mouth, headlines across his
neck, the CTA on his chest). **Do not card the face just to clear it either**: the obvious fix
cleared his face and emptied the other half of frame, a different defect for the same one. The
correct fix is a measured-safe column outside his real contour (`facesafe_guard.py` against the
source face track), and the top band is not automatically safe: his hair sits in it.

### 9. Graphics are not the default; showing him is

*"No need to show any animation here when Nader says real is what are you going and whatever it
is, just the A-roll should be shown. Any animation, error, just A-roll with captions should be
there. At the last line ... CTA."* (vid56 short, round 4, on the closing/direct-ask beat)

**He said this explicitly generalises: it applies to the long-form too, and names a repeated
pattern across videos, not a one-off note on this beat.** The beat in question had been
graphics-only for its whole 4.6s (an offer card, no face) on the line where he makes the direct
ask, because a gaze-safety exclusion had (wrongly, on inspection) flagged that source range as
unsafe. Reach for an animated overlay when it's carrying information that cannot come from him
speaking (a number, a comparison, a mechanism); do not reach for it to fill a beat, and never let
it replace him at the moment he is making the direct ask. Audit every closing/CTA beat against this
before the next round, not after the note.

**This has a precondition, found the round after:** *"nader is reading here in this frame, need to
replace it with animations ... as we cant show the a roll here as he is looking down."* (vid58
short round 2, on a span already measured as him reading, eyeOpen 0.45→0.13 for 32 consecutive
samples). An unwatchable shot at a smaller size is still an unwatchable shot: showing him is the
default only when showing him is worth doing. When the take itself is unusable for a span, take the
picture off and let graphics own the frame; do not shrink the problem instead of removing it.

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

Confirmed again on vid58's short, which delivered with zero stock despite eleven graded clips
already cut into the long-form: the owner's corrective instruction was **"animations on TOP, A-roll
on the BOTTOM, split-screen AND card, with stock footage."** Treat that as the standing shape for
his shorts, not a one-off correction; see GRAMMAR.md.

### 8. Sponsored work has a zero-error bar

Resolve promo codes against the partner URL, never against whisper. Every on-screen figure needs
a primary source, attributed on screen. A competitor's figures are attributed to the competitor
and never rendered in the alert colour. A verdict carries the VO's own qualifier. The caption
pack must flag paid promotion.

### 10. A short leads with substance, not with price

His note after vid58: lead with what the sponsor DOES, coverage, re-requests and verification, the
exposure scanner, the automation. **Price is one beat near the end, never the spine of the cut.**
vid62's short was written to this and it decides what gets left out as much as what goes in: the
four-competitor price comparison was dropped from a 56s cut because the competitors' prices need
their caveats to be fair, which is 90s of the long-form, and naming them without the caveats is
exactly the pricing-led cut he had already rejected. Only the discount code survives as a price,
at beat 8 of 9.

---

## Delivery

- Two-pass `loudnorm` to **-14 LUFS / -1.0 dBTP** for YouTube.
- No em dashes.
- The file-size matching rule does **not** apply to him (that is the two Instagram creators).
- SFX: median **0.060**, ceiling 0.096, bed 0.055. He has halved it on each complaint from 0.20.
- **A sustained bed reads as "going on and on" regardless of level.** vid56 round 1 kept median
  0.053 (below the vid46 ceiling) but added sustained texture beds under long builds, and still
  drew "the SFX is very irritating, going on and on and on" plus four separate "remove the SFX from
  here." Transients only; silence is allowed; roughly one cue per 4-5s.

---

## How he reviews

He gives a feeling plus an itemised list, and the list is usually a symptom of one structural
fault. On the round that mattered most, he disliked almost everything and offered one positive:
"the globe animations are nice." That single positive was the whole diagnosis, because the 3D
field was the only device in the film that was not a rounded rectangle.

**There are two review channels and they are not the same person.** The owner reviews locally and
his notes are the ones the round numbers count. Nader reviews through the hosted share link, and
his notes arrive as `source: "client"` in `review/data/<slug>/comments.json` with a markup frame
each. They can land minutes after a share and they are easy to miss while a cutdown is in flight,
which is exactly how two of them went unanswered on vid46. **Run the inbox before starting, and
write a `status` and a `reply` back for every client note you address**. He sees the reply, and a
note left open reads as ignored.

**"The audio cuts weird here" is usually a script fault, not an encode fault.** Transcribe plus or
minus 1.6s around the join in isolation BEFORE touching ffmpeg. Both of vid62 short's audio notes
were clean at signal level: one join cut his sentence mid-list, the other opened a beat on a
dangling "And" bridging two topics 68 seconds apart. Both fixes were editorial, re-cutting the
in-point and the out-point, and they traded against each other (+3.7s and -2.8s on runtime). Only
after the script reads as a finished sentence is a fade or a tail worth measuring.

**Verify a reported defect against the MASTER before accepting it as his.** The failure that
produced this rule is another creator's (vid61 round 2, "the A-roll repeatedly says 'pit lips, pit
lips'"), and it belongs here because he reviews his own footage the same way: there was no repeat.
He had delivered the phrase as separate stabs and the cut had removed the PAUSES between them until
the fragments read as a stammer. A client hears the delivered file, never the master, so a defect
they describe as theirs can be one the edit manufactured. Correlate the suspect span in the master
with 10ms energy envelopes and run two controls, two genuinely different phrases and the same audio
offset by about 30ms, before planning any fix. Corollary: the pauses inside a halting delivery are
load-bearing. Cut the stranded fragments, not the air between them.

**He also reverses decisions, and that is the expensive kind.** He chose to keep a duplicated
take, then wanted the repeated line cut, which invalidated the chunk map, every T0, every caption
offset and the whole gaze and card solve. **Get any cut decision confirmed before any build
work.**
