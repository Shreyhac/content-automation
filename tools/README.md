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

## `gates/` the pre-render gate

| Script | What |
|---|---|
| `guard.py` | Drives the composition timeline in Chromium and measures what **actually paints** at every beat: assets on disk, broken images, occlusion (position is not visibility), the Instagram bands, graphics on the presenter, text on text, void beats, contrast over the picture, `<video>` windows, stylesheet coverage, timed elements painting outside their own window, and (with `--ids`) the element-id and `<div>`-balance diff a splice needs. Config-driven, nothing per-film is hardcoded. |
| `guard.example.json` | The config, annotated. Copy it next to a film's `index.html`. |

```bash
python3 tools/gates/guard.py hf67/guard.json -v
```

Read `tools/gates/README.md` for the config and the per-check table, and
`playbooks/gates.md` for the doctrine: when to add a gate, why gates lie, and the running
order. **Exit 0 means every check RAN and passed. Read the coverage line before believing
it:** a green run and a gate that silently did nothing produce identical output.

---

## `qa/`

| Script | What |
|---|---|
| `shoot-sheet.py` | The beat contact sheet, shot from the live page **before** any render. `--from-clips` derives the samples from every element's own `data-start` window, which is what a delivery sheet needs: a fixed grid never samples an element whose window falls between two beats. Replicates the renderer's clip scheduling, seeks every `<video>` to its own local time, replays the caption cues that `tl.time(t, false)` suppressed, and tiles labelled beats. A void passes every structural gate and only a sheet shows it. Reads the same JSON as `guard.py`. |
| `exact-frame-qa.sh` | One decode pass with a frame-number select expression. **Never `-ss` before `-i`.** |
| `playwright-capture.py` | Real page capture. Dark scheme, `device_scale_factor=2`. Over-capture in one run. |

---

## `deliver/`

| Script | What |
|---|---|
| `make_cta_doc.py` | The .docx behind "comment X and I'll send you Y". Content is a JSON, the house format is in the tool. |
| `cta.example.json` | The real vid67 payload as the worked example. |

**The CTA doc is a required deliverable at FIRST delivery**, not when he asks. It is also
where the reel's overstatements get corrected: one film's VO said "without ever touching
the terminal" and the repo's own Quickstart is three terminal commands. `deliver/README.md`
has the rule and the schema.

---

## `stock/`

`pexels_search.py` and `pexels_fetch.py`. The download endpoint works without an API key given a
plain browser User-Agent. **Extract a midframe from every clip and look at it**: the reject rate is
about one in three even on hand-shortlisted results.

---

## `review/` the feedback loop

The Reel Review tooling itself, vendored so a collaborator can run it and not just read about
it. `rr` is the launcher; `review/` is the local player, markup canvas and round exporter;
`share/` is the Cloudflare Worker that serves one private link to a client.

```bash
tools/review/rr out/vid68-final.mp4                     # local review
tools/review/rr share out/vid68-final.mp4 --name "..."  # private client link
tools/review/rr inbox                                   # notes left since your last pull
tools/review/rr setup                                   # once, before the client channel works
```

It assumed it sat at the repo root, so vendored two levels down it would have looked for `out/`
inside `tools/review/` and written the exported rounds there. The launcher exports **`RR_ROOT`**,
defaulting to the repo root, and both Node entry points honour it. Set it yourself if your
deliverables live elsewhere.

`review/data/` (notes and markup frames) and `share/config.json` (your keys) are gitignored.
`share/config.example.json` shows the shape. `tools/review/README.md` covers running it,
`docs/08-review-workflow.md` is the operating manual and the one that matters: it carries the
ordering rule, fix, reply, push, then share.

---

## `generative/` cloned voice, plates, drift, music

| Script | What |
|---|---|
| `voice.py` | `clone`, `takes`, `sweep`, `eqfit`, `master`. ElevenLabs. Refuses to clone without `--i-did-not-denoise`, because pre-processing a clone reference cost 19% of its consonant energy. |
| `plate.py` | `avatar`, `avatar4`, `omnihuman`, `lipsync`, `i2v`. Refuses an i2v run with no negative prompt unless you pass `--no-negative`. |
| `drift.py` | Per-region drift on a crop around every face and hand. No key, no cost. A global metric read 4.84 while a hand drifted 77.4. |
| `music.py` | `search`, `fetch`, `transients`, `treat`. Mixkit. AI-generated music has been rejected outright, so this fetches real licensed tracks. |

Keys come from the environment only, never from a file in the repo. `.env.example` names them.
Every tool takes `--dry-run`, which prints the exact request body and sends nothing.
Doctrine is in `playbooks/generative-assets.md`.

---

## `qa/benchmark.py` the quality bar, measured

```bash
python3 tools/qa/benchmark.py out/vid68-final.mp4 --creator shreyansh --master /path/to/aroll.mp4
```

Thirteen metrics from `benchmarks.json`, each carrying the film and the reaction that set it.
PASS, WARN, FAIL or SKIP per metric, non-zero exit on a hard fail, 16 to 35 seconds per film.

It refuses to compare a 9:16 cutdown's pixels or bitrate against a 16:9 master, because that
compares two different pictures. Point `--master` at the ORIGINAL take, not at the project's
CRF-17 transcode: doing the latter turns a real 1.16x pass into a 0.89x fail.

**Every shipped film tested failed at least one metric.** That is the tool working, not the tool
being wrong. `docs/09-self-review.md` covers the judgement classes no measurement reaches.
