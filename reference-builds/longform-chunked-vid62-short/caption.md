# vid62 short: client ep5, vertical cut

**Delivered v1, 2026-08-11.** `out/vid62-short.mp4`
1080×1920 · 23.976 · **1438 frames · 59.977s** · 23.1 Mbps · 175 MB · −14.0 LUFS / 4.4 LU

Built in `hf62s/`, cut entirely from the long-form's own A-roll chunks
(`hf62/assets/aroll/c*.mp4`, 59.8 Mbps), no new recording, no new footage.

---

## Instagram / Shorts caption

Type your own name into Google and add your city. That address on the screen is
probably yours.

Privacy Rights Clearinghouse and the EFF have counted at least 750 registered data
broker groups in the US. Incogni's removal engine requests, and re-requests,
removal from over 420 of the sites that publish your home address, and its exposure
scanner surfaces what's out there so you can clear it in a click or two.

Code CODEWORD, 60% off the annual plan. incogni.com/PARTNER

#dataprivacy #databrokers #incogni #privacy #deleteyourdata #onlineprivacy
#identitytheft #personaldata #privacytips #cybersecurity

[data removal service] [data broker opt out] [incogni review] [remove personal
information from internet] [people search removal] [privacy tools 2026]

---

## What's in the cut

| # | in-out (source) | dur | line | picture |
|---|---|---|---|---|
| 1 | 0.00-6.10 | 6.10 | "I want you to do something. Type your own name into Google…" | BAND, whole beat |
| 2 | 6.40-10.14 | 3.74 | "…you just saw your home address, your phone number," | BAND, whole beat |
| 3 | 14.18-20.52 | 6.34 | "All sitting on a data broker site… sold to anyone… with a credit card." | CARD, off for the last 0.4s |
| 4 | 51.52-62.32 | 10.80 | "Privacy Rights Clearinghouse, working with the EFF… 750 unique data broker groups registered across the US" | BAND 2.3s, then off |
| 5 | 234.32-242.82 | 8.50 | "…requests and re-requests removal from over 420 plus data broker sites that publish your home address," | CARD 2.5s, then off |
| 6 | 260.28-267.08 | 6.80 | "Incogni searches broadly across the web… removed in a click or two." | off, the presenter reads the whole line |
| 7 | 334.90-342.42 | 7.51 | "And on that specific outcome, on that price point, Incogni is what I would recommend to a friend…" | BAND, whole beat |
| 8 | 342.64-346.80 | 4.17 | "You can use the code CODEWORD for 60% off Incogni's annual plan." | CARD 2.3s, then off |
| 9 | 364.36-370.38 | 6.01 | "So the question is, are you going to let brokers keep profiting off it? Or are you going to do something about it?" | BAND, whole beat |

Placement alternates **band · band · card · band · card · none · band · card · band**;
the presenter's picture is on screen 38.6s of 60.0s.

---

## Four things that changed against the approved script

1. **Runtime is 59.98s, not ~56s.** Four out-points had no room in front of the next
   word and would have chopped one: b4 ended on "…groups" with "registered" starting
   on the same frame, b5 on "…sites" with "that" starting on the same frame. Both
   were extended to the end of their clause instead. This is the defect that produced
   two of vid58's four client notes.
2. **b7 and b9 gained a 0.12s / 0.14s pre-roll.** A fresh transcription of the first
   delivered mix heard "On that specific outcome" and "The question is", the leading
   "And" and "So" were gone. Measured against the master, whisper's onset for "So"
   runs ~20ms late, so cutting on it shaved the attack. Both cuts moved back into
   measured silence; the re-transcription now hears every word.
3. **No full-bleed close.** vid58's client note asked for one and vid59's short had
   one. On THIS take the presenter's head measures 1371×1110 source px, so a 1215px-wide 9:16
   window holds 91% of the presenter's face before the presenter moves, solved full-bleed, the presenter's contour ran
   x−13..1153 of 1080, both cheeks outside the frame, chin at y1574. The close plays
   as a band. Numbers are printed by `hf62s/solve_short62.py`.
4. **Beat 3 keeps the presenter's full sentence** and the picture arrives 0.6s into the beat,
   rather than cutting into "…a data broker site" and losing the connective.

## Ships with NO SFX

By design, matching the long-form. vid59's beds drew *"the SFX is very irritating"*.

## Notes for you

- **The middle 11.4s has no face** (end of the 420+ beat through the whole scanner
  beat). `hf62/camera-windows.json`, the hand-checked whitelist from the long-form's
  round-3 rebuild, has no window anywhere inside those spans; the presenter is reading for every
  second of them. The presenter's dashboard owns that stretch instead, across four separate
  recordings so it is never a held still.
- **The client's email is not in the cut.** `p3-activity` carried `media@castellano.com` in the
  account nav; the clip is cropped at the source (`p3-activity-s.mp4`), verified across
  five sample points.
- **One recording was dropped**: `p6-modal` ("Found your info exposed online? …") is
  cut off mid-sentence *in the source recording itself*, the right edge of the modal
  is outside the capture, so it reads as a broken frame at any crop. b6 runs on
  `p5-scanner` and `p1-resubmit` instead.
- **Not sent to the client.** Per the repo rule, this is out for your eyes first.
