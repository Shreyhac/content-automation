# Content Automation

The production system for four creators' short-form and long-form video. Clone it, open
Claude Code inside it, hand it an A-roll and a brief, and it produces a finished cut at the
standard these channels already ship at.

This repo is the **method**, not the archive. It carries the pipeline, the measured geometry,
the per-creator rules, the tooling and the reference builds. It does not carry raw footage or
render output, and it should never start to.

---

## Read this first

If you are a new operator, read in this order. It is about 45 minutes and it is the difference
between a first render that gets approved and one that gets rejected.

| # | File | Why |
|---|---|---|
| 1 | `docs/01-pipeline.md` | The eight stages, in order. Skipping one is how videos get rejected. |
| 2 | `docs/03-quality-bar.md` | What "good" means here: the measured delivery contract, and the five rejection classes that account for almost every rework. |
| 3 | `creators/<the creator>/PROFILE.md` | Hard rules. These override everything else in the repo. |
| 4 | `docs/02-safe-zones.md` | Instagram geometry. A hard gate, audited every render round. |
| 5 | `playbooks/gates.md` | Why the built-in gates pass real bugs, and what to run instead. |
| 6 | `playbooks/README.md` | Index of techniques. Read the two or three the job actually needs. |

Then watch one cut in `reference-cuts/` for the creator you are building for. That is the bar,
and it is faster to absorb than to read.

`CLAUDE.md` is loaded automatically by Claude Code and tells the agent the same thing in the
form it needs.

---

## The four creators

Each has a folder under `creators/` with three files: `PROFILE.md` (who they are and their
hard rules), `GRAMMAR.md` (the approved visual system, with measured numbers), and
`HISTORY.md` (every video shipped for them and what each review round changed). A creator with
unanswered review notes also has an `open-notes/` folder holding the marked-up frames; read it
before you start on them.

| Folder | Who | Format | Signature |
|---|---|---|---|
| `creators/nader/` | Nader Nadernejad, Nadernejad Media. Agency client, ORM and AI-search. | 16:9 YouTube long-form (3 to 4 min) plus 9:16 cutdowns | Chunked long-form architecture, gaze-gated face windows, split with graphics above and face below |
| `creators/gaurav/` | thepmfguy, also called "gaurav" in older files. Same person. | 9:16 Instagram Reels, 30 to 45s | Paper split band, face on screen continuously, one persistent object in the graphics zone |
| `creators/shreyansh/` | shreyansharora05. The "slot 1" creator. | 9:16 Instagram Reels, 25 to 45s | Floating face card as the default mode, the paper theme, drawn marginalia, machine-event scene grammar |
| `creators/demi/` | demi.ai. Product client, paid Meta placements. | 9:16 ad cuts, 30 to 40s | Sub-1.5s mean shot via static crop-cuts, the client's own icon system, zero added SFX |

**Identify the creator from the footage before anything else.** A brief can arrive from the
wrong account, and the channel decides the entire system. One contact sheet against
`reference-cuts/` settles it.

---

## Layout

```
docs/                 The method. Pipeline, safe zones, quality bar, design system,
                      audio, delivery, troubleshooting, review workflow.
creators/             Per-creator profile, grammar and history. Hard rules live here.
playbooks/            One file per reusable technique, each with the measured numbers
                      and the failure that produced the rule.
library/
  fonts/              29 deduped faces used across the portfolio.
  sfx/house/          The licensed house pack (96 files).
  sfx/saas/           Gaurav's own supplied pack (17 files). He expects to hear it.
  vendor/             three.min.js (UMD r150). Vendored deliberately, see playbooks/threejs.md.
  templates/          Starter scaffolds.
reference-builds/     Eight shipped compositions, code only, each with an ASSETS.md saying
                      exactly what media it expected and where that media came from.
                      One current build per creator, plus the earlier ones worth reading.
reference-cuts/       Fifteen 720p proxies of shipped finals. This is the quality bar,
                      watchable. Start with the current cut for your creator.
tools/
  vision/ aroll/      Measurement and preparation.
  captions/ sfx/      Caption and audio assembly.
  chunking/ stock/    Long-form assembly and stock fetch.
  gates/              guard.py, the pre-render gate that measures what actually paints,
                      and derive_config.py, which bootstraps its config for a new film.
  qa/                 The beat contact sheet, the exact-frame extractor, and
                      benchmark.py, which scores a delivered file against the bar.
  deliver/            The CTA .docx builder.
  generative/         Cloned voice, AI plates, i2v drift measurement, licensed music.
  review/             Reel Review: the local player, the markup canvas and the client link.
web/                  The product surface. Upload, watch the edit, mark up the frame,
                      download. Node built-ins only, no install. See web/README.md.
.claude/skills/       hyperframes, hyperframes-cli and gsap skills. Auto-discovered.
```

---

## Quickstart

```bash
# 1. Environment. Verifies every binary the pipeline needs.
bash tools/check-env.sh

# 2. Start a new video from the current reference build for that creator.
cp -R reference-builds/shreyansh-vid67 work/vid68
# read its ASSETS.md, it tells you exactly what media to supply and how to regenerate it

# 3. Open Claude Code in the repo root. It reads CLAUDE.md and the creator profile,
#    then runs the pipeline in docs/01-pipeline.md.
```

Prefer scaffolding from `reference-builds/` over `library/templates/`: the template carries the
skeleton, a reference build carries the proven systems.

Working directories (`work/`, `assets/`, renders) are gitignored. Nothing heavy enters the
repo. See `docs/06-delivery.md` for where finished files go.

---

## Reviewing a cut

```bash
tools/review/rr out/vid68-final.mp4                    # local: scrub, draw, leave notes
tools/review/rr share out/vid68-final.mp4 --name "..." # one private link for a client
tools/review/rr inbox                                  # what clients left since your last pull
```

Notes come back as `<slug>-feedback-round<N>.md` at the repo root, with the marked-up frames
alongside. `docs/08-review-workflow.md` is the manual, and the ordering rule in it is not
optional: fix, write the replies, push, and only then share the new render. Sharing first makes
every addressed note look ignored.

Run `tools/review/rr setup` once before the client channel works. `share/config.example.json`
shows what it writes.

---

## The rules that get videos rejected most often

Full detail is in `docs/03-quality-bar.md`. In one screen:

1. **A first technically-correct render is a draft.** Budget three review rounds. That is the
   job, not scope creep.
2. **Frame QA is the only gate that works.** Lint, validate and inspect pass bugs that ruin
   a cut. Run `tools/gates/guard.py`, shoot a contact sheet before the render, and read a frame
   at every beat afterwards. A gate that reports PASS is not the same as a gate that ran.
3. **A beat that can only be expressed as a sentence in a box is the wrong beat.** Animate the
   physical event the line describes. A beat that is one element over blank paper is a defect.
4. **Never put graphics on the face.** Above the chin is the face. Every beat is CARD, SPLIT or
   FULL-BLEED, and each mode has its own safe-zone solve. A full-width band across a torso is
   none of them.
5. **Measure, never estimate.** Face geometry, crop rectangles, marker offsets and card widths
   are all arithmetic, and the answer is a hit test on the real crop, not a model. Every "it
   looked about right" in this repo's history became a render round.
6. **No em dashes** in on-screen text, captions or published copy. Owner rule, all videos, all
   creators. Grep the composition, the SRT and the caption pack before every delivery. This is
   the most-skipped rule here: a sweep on 2026-08-15 found them in 19 delivered caption packs,
   2 delivered SRTs and one composition with 45. `tools/qa/benchmark.py` now fails on it.
7. **Match the master's resolution AND its bitrate on delivery**, verified with `ffprobe`
   against the master. Not the CRF: the same CRF has delivered 36.8 and 24.9 Mbps.
   `tools/qa/benchmark.py <file> --creator <who> --master <take>` checks this and twelve more.
   Run it before you deliver, and read `docs/09-self-review.md` for what it cannot measure.
8. **No hashtags.** The caption body is the ranking surface. The caption pack is paste-ready
   only, and the CTA .docx ships at first delivery, not on request.

---

## Keeping the repo smart

After every completed video, update the creator's `HISTORY.md` with what the review rounds
changed, and promote anything reusable into the relevant playbook. A lesson that stays in a
chat log is a lesson the next operator pays for again.
