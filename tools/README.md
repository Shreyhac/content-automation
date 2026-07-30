# Tools

The measurement and assembly scripts. All of these shipped real videos. Paths and constants inside
them refer to the build they came from, so **read before running**: most take arguments or have a
config block at the top.

`check-env.sh` verifies the whole environment. Run it first.

---

## `vision/` measure the head

| Script | What |
|---|---|
| `crown.swift` | `VNGeneratePersonSegmentationRequest`. The topmost mask row with a run of >= 8 foreground px is the crown, per frame. |
| `facebox.swift` | `VNDetectFaceLandmarksRequest` rev-3, `faceContour`. Chin and face-centre x. |
| `gaze-detect.swift` | Eye-openness and contour aspect, per frame, for the gaze pass. |
| `build_windows.py` | Turns the gaze CSV into a face-safe window map. Runs of >= 2 frames below threshold are a down-look, padded +/- 0.9s, complement kept where >= 1.6s. |
| `solve_card.py` | Per-window face-card transform, with the coverage floor and the residual veto. |

```bash
ffmpeg -i aroll.mp4 -vf fps=5 stills/%05d.jpg
swift tools/vision/crown.swift stills/ > crown.csv
```

**Vision's face bounding box is not the head.** See `playbooks/face-geometry.md` and
`playbooks/gaze-detection.md`.

---

## `aroll/` prepare the source

| Script | What |
|---|---|
| `prep_aroll.sh` | Transcode into a project. Crop, scale, keyframe density. |
| `recut.sh` | Remove ranges from a master. Put splice points inside face-hidden runs. |
| `beats.py` | The beat table for a short: source segments and frame counts. Single source of truth. |
| `solve_short.py` | Solves vertical geometry from a long-form's own measurement CSVs. |
| `bake_clips.py` | Bakes each beat's crop with ffmpeg and lanczos. One bake at hero size. |
| `build_vo.py` | Splices a VO on complete sentence bounds, cutting to measured dips. |

---

## `captions/`

| Script | What |
|---|---|
| `build_captions.py` | Groups the word stream and emits both the HTML and the SRT. Carries the `CONT` token-glue rule. |
| `inject_captions.py` | Splices between explicit markers. **Its mute ranges are argv and are not persisted**: see the warning in `docs/06-delivery.md`. |
| `fix_caption_glue.py` | Applies the token-glue rule to already-injected HTML. |
| `build_srt.py` | Standalone SRT. |

---

## `sfx/`

| Script | What |
|---|---|
| `sfx.py` | **The single source of truth for a bed.** Refuses to inject one that breaks the share cap, the median, the ceiling or the retired list. Put enforcement in the tool. |
| `build_bed.py` | Renders the bed onto one continuous timeline from `sfx.py`'s cues. **Never extracted from chunk renders.** |
| `curate_sfx.sh`, `curate_saas_sfx.sh` | Peak-normalise to -3 dBFS and head-trim a pool. |

---

## `chunking/`

| Script | What |
|---|---|
| `plan_chunks.py` | Boundaries on word onsets inside gaps >= 0.20s. |
| `inject_windows.py` | Writes solved transforms into the compositions. **Never hand-type a solved transform.** |
| `render_chunks.sh` | `cd`s into each chunk (the CLI resolves output against CWD, not the dir argument) and sets `HF_DE_STALL_MS`. |
| `assemble.sh` | Asserts the planned frame total **before** it will concatenate. Keep that assert. |
| `preview.sh` | Muxes the real VO under a chunk and prints the bed's mean and peak. **Never QA a chunk silent.** |

---

## `qa/`

| Script | What |
|---|---|
| `exact-frame-qa.sh` | One decode pass with a frame-number select expression. **Never `-ss` before `-i`.** |
| `playwright-capture.py` | Real page capture. Dark scheme, `device_scale_factor=2`. Over-capture in one run. |

---

## `stock/`

`pexels_search.py` and `pexels_fetch.py`. The download endpoint works without an API key given a
plain browser User-Agent. **Extract a midframe from every clip and look at it**: the reject rate is
about one in three even on hand-shortlisted results.
