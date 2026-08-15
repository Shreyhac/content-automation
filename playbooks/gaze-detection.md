# Gaze detection: "don't show my face when I'm reading my notes"

A constraint on the whole edit, not a decoration. Every face state in the video is driven by a
measured face-safe window map. Required for longform-chunked; applicable to any creator who reads.

Tools: `tools/vision/gaze-detect.swift`, `tools/vision/build_windows.py`.

---

## Extract and detect

```bash
ffmpeg -i aroll.mp4 -vf fps=5 stills/%05d.jpg
swift tools/vision/gaze-detect.swift stills/ > gaze.csv
python3 tools/vision/build_windows.py gaze.csv > face-safe-windows.json
```

Apple's Vision via a short Swift tool beats installing cv2 or mediapipe, and pip is PEP-668 locked
on this machine anyway. `VNDetectFaceLandmarksRequest` with `revision3`.

**`obs.pitch` comes back NA on every frame.** It cannot settle anything. Do not build on it.

---

## There are THREE gaze modes, not two

The first implementation used one signal and assumed a clean bimodal take:

- **eye-openness** = the eye landmark polygon's height/width ratio.
  About 0.33 to 0.41 camera-facing, about 0.14 to 0.20 reading. Threshold 0.30 to 0.32.

That works on a clean take and silently fails on the middle mode: **head pitched down, eyes still
open**, which sits at 0.29 to 0.32 and passes as face-safe.

The second signal: **the face contour foreshortens when the head pitches**, so

```
aspect = contourH / contourW
```

drops to about 0.83 to 0.89 pitched down, against 0.92 to 1.06 at camera.

```
unsafe  if  eyeOpen < 0.30  OR  aspect < 0.905
```

**The histogram's shallow valley looked bimodal enough and was wrong.** Only building the crop
sheets and reading them caught it.

Next signal to try if these two are not enough: `browEyeGap` separates the hard cases
(0.072 to 0.081 down against 0.087 to 0.140 at camera).

---

## Detect runs, then pad. Do not smooth a fraction

A rolling "open fraction >= 0.80" window looked fine and still put down-look frames at every
window edge.

What works:

1. Runs of **>= 2 frames** (0.4s at 5fps) below threshold are a down-look.
2. **Pad +/- 0.9s** around each down-look.
3. The complement, keeping runs **>= 1.6s**, is face-safe.

On one film: 21 windows, 38% of the video. On another: 24 windows.

**Blinks are deliberately not excluded.** A blink is not looking down, and excluding them removed
padding that was accidentally covering real down-looks.

---

## The sampling-phase trap

**`MIN_RUN=2` at 5fps does not survive a re-extraction.** A comment claiming "blinks survive by
the >= 2-frame minimum" was true only for a favourable sampling phase. Re-extracting the stills
through a re-cut's frame-select filter shifted the phase and a blink at 12.6 to 12.8s became a
two-second "reading" run in the middle of the hook.

If the source is re-cut, **re-run the whole pass**, and re-verify.

A blink and a note-read are separable by **shape**, not threshold: a blink is a V (near-closed,
bracketed by normal, head never pitches), a read is a plateau. A discriminator built on that was
measured and **deliberately left off**, because reading its crops showed genuine down-looks where
both signals read clean camera, and rejecting the short runs removed the padding that was covering
them.

---

## Verify by looking, densely

**Sampling only window edges passed a map that was still wrong.** Sample every 1.0s *inside* every
window: 92 crops across 3 contact sheets is what proved one map correct.

**When a detector and your eyes disagree, hand-exclude the frames you verified and say so in the
code.** Two 0.4s windows are excluded by name in one `build_windows.py` with the reason attached.
An earlier round shipped those same frames unflagged.

---

## Whitelist, not blacklist

A blacklist (mark the unsafe spans) can only be as good as the detector that built it: two client
notes about the presenter visibly reading landed at moments where **no excluded span existed at
all**, because eyelid aperture alone measured 0.347 to 0.361 there against a film median of 0.379,
statistically indistinguishable from looking at the lens. A detector that cannot see a fault
produces a blacklist with a hole in exactly the shape of what it cannot see.

**Rewrite the gate as a whitelist: the windows the face MAY paint in, everywhere else forbidden.**
A missing window under a whitelist costs a beat of face (safe failure). A missing entry under a
blacklist ships the defect (unsafe failure). Choose which way you want the gate to fail before you
build it.

Two changes made the whitelist correct where the blacklist wasn't:

1. **The signal.** Eyelid aperture cannot see gaze *direction*, only openness. Pupil position
   inside its own eye-opening, plus real head pitch, can, but only as a **rolling median over
   about 1 second**, not a per-sample threshold. That is what separates a blink (one depressed
   sample) from a read (the whole window depressed). Hand-labelled frames stopped overlapping
   entirely once measured this way: reads 0.153–0.326, camera 0.375–0.440. Per-sample thresholds
   had already failed three times before this.
2. **Two windows still needed a documented human override** even under the better signal: the
   film's cover frame (the classifier's lead-trim was guarding what was actually a blink) and a
   sign-off (the median dips because the presenter's eyes narrow when they smile). **A classifier
   confident enough to cut the presenter from their own sign-off needs a human check, not another
   threshold.**

## Run length alone does not separate a blink from a glance when the signal runs backwards

One take's contour-aspect signal ran **inverted** relative to camera-facing (1.015 reading vs.
0.979 at camera) and `browEyeGap` was identical in both groups: neither discriminator worked at
all on that take, and only eye-openness stayed cleanly bimodal, thresholded at the **top** of the
ambiguous band rather than its valley.

Rejecting every short (0.4 to 0.6s) run as a blink on a run-length argument alone raised coverage
from 22.5% to 55.4% and shipped windows where the presenter was **visibly reading at five
timestamps** inside
"safe" territory. The fix was to tile and hand-adjudicate all 44 short runs: 36 were genuinely
blinks, 8 were glances. A further trap one level down: `MIN_RUN=2` means single-sample dips never
reach the run logic at all: 42 of those fell inside otherwise-safe windows and 3 were real glances
no threshold change could ever reach; those 3 are now named individually in `HAND_EXCLUDE` with
their reason attached, rather than left for the next threshold tweak to rediscover.

## A confirmed exclusion is an editorial decision, not just a safety flag

Once an exclusion is checked against the raw signal and found genuine (here: eye-openness
0.45→0.13 sustained over 32 consecutive samples, frames showing the presenter visibly reading), it
stops being a binary "hide the face" switch and becomes information about the shot: the picture
moved to a smaller CARD for exactly that span, so the presenter stayed on screen at a size the
moment could support while graphics carried the argument, and returned to full size the instant the
exclusion window ended. **The answer to "is this exclusion real" is sometimes "yes, and it tells you
what the format should be", not just whether to cut away.**

## Bias

**Err toward hiding the face.** An extra second of graphics is a soft cost. Showing the presenter
reading is a hard failure, and it is the one thing the client actually asked for.

Losing face time costs nothing when the client wants graphics in exactly those gaps.

---

## Downstream consequences

The window map is not just a visibility switch. It constrains:

- **Which windows can be carded** (see `playbooks/face-geometry.md`: the residual veto is measured
  per window, and it changes when the tracking curve changes).
- **Where a re-cut's splice points can go.** Putting both splice points inside note-reading runs
  means the face is hidden across both joins, so neither can read as a jump cut. That is why those
  in and out points and not tighter ones.
- **Where the film can end.** If the closing line finishes with a downcast look, every frame at
  the end of that window is a bad last frame, and holding an earlier one freezes the presenter
  mid-sentence.
  Cut to a composed lockup instead, which for a paid placement is also the correct thing to end on.
