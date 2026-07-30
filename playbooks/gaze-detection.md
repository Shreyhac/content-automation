# Gaze detection: "don't show my face when I'm reading my notes"

A constraint on the whole edit, not a decoration. Every face state in the video is driven by a
measured face-safe window map. Required for Nader; applicable to any creator who reads.

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

## Bias

**Err toward hiding him.** An extra second of graphics is a soft cost. Showing him reading is a
hard failure, and it is the one thing the client actually asked for.

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
  the end of that window is a bad last frame, and holding an earlier one freezes him mid-sentence.
  Cut to a composed lockup instead, which for a paid placement is also the correct thing to end on.
