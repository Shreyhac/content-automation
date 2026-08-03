# Content Automation

The production system for three creators' short-form and long-form video. Clone it, open
Claude Code inside it, hand it an A-roll and a brief, and it produces a finished cut at the
standard these channels already ship at.

This repo is the **method**, not the archive. It carries the pipeline, the measured geometry,
the per-creator rules, the tooling and the reference builds. It does not carry raw footage or
render output, and it should never start to.

---

## Read this first

If you are a new operator, read in this order. It is about 40 minutes and it is the difference
between a first render that gets approved and one that gets rejected.

| # | File | Why |
|---|---|---|
| 1 | `docs/01-pipeline.md` | The eight stages, in order. Skipping one is how videos get rejected. |
| 2 | `docs/03-quality-bar.md` | What "good" means here, and the four rejection classes that account for almost every rework. |
| 3 | `creators/<the creator>/PROFILE.md` | Hard rules. These override everything else in the repo. |
| 4 | `docs/02-safe-zones.md` | Instagram geometry. A hard gate, audited every render round. |
| 5 | `playbooks/README.md` | Index of techniques. Read the two or three the job actually needs. |

`CLAUDE.md` is loaded automatically by Claude Code and tells the agent the same thing in the
form it needs.

---

## The three creators

Each has a folder under `creators/` with three files: `PROFILE.md` (who they are and their
hard rules), `GRAMMAR.md` (the approved visual system, with measured numbers), and
`HISTORY.md` (every video shipped for them and what each review round changed). A creator with
unanswered review notes also has an `open-notes/` folder holding the marked-up frames; read it
before you start on them.

| Folder | Who | Format | Signature |
|---|---|---|---|
| `creators/nader/` | Nader Nadernejad, Nadernejad Media. Agency client, ORM and AI-search. | 16:9 YouTube long-form (3 to 4 min) plus 9:16 cutdowns | Chunked long-form architecture, gaze-gated face windows, floating face card |
| `creators/gaurav/` | thepmfguy, also called "gaurav" in older files. Same person. | 9:16 Instagram Reels, 30 to 45s | Paper split band, face on screen continuously, one persistent object in the graphics zone |
| `creators/shreyansh/` | shreyansharora05. The "slot 1" creator. | 9:16 Instagram Reels, 30 to 40s | Floating face card, three.js as a recurring object, machine-event scene grammar |

**Identify the creator from the footage before anything else.** A brief can arrive from the
wrong account, and the channel decides the entire system. One contact sheet against
`reference-cuts/` settles it.

---

## Layout

```
docs/                 The method. Pipeline, safe zones, quality bar, design system,
                      audio, delivery, troubleshooting.
creators/             Per-creator profile, grammar and history. Hard rules live here.
playbooks/            One file per reusable technique, each with the measured numbers
                      and the failure that produced the rule.
library/
  fonts/              24 deduped woff2 faces used across the portfolio.
  sfx/house/          The licensed house pack (96 files).
  sfx/saas/           Gaurav's own supplied pack (17 files). He expects to hear it.
  vendor/             three.min.js (UMD r150). Vendored deliberately, see playbooks/threejs.md.
  templates/          Starter scaffolds.
reference-builds/     Four shipped compositions, code only, each with an ASSETS.md saying
                      exactly what media it expected and where that media came from.
reference-cuts/       720p proxies of shipped finals. This is the quality bar, watchable.
tools/                The measurement and assembly scripts. Vision, a-roll, captions,
                      sfx, chunking, qa, stock.
.claude/skills/       hyperframes, hyperframes-cli and gsap skills. Auto-discovered.
```

---

## Quickstart

```bash
# 1. Environment. Verifies every binary the pipeline needs.
bash tools/check-env.sh

# 2. Start a new video from a template.
cp -R library/templates/vertical-reel work/vid48
cp library/vendor/three.min.js work/vid48/assets/    # only if the build uses 3D

# 3. Open Claude Code in the repo root. It reads CLAUDE.md and the creator profile,
#    then runs the pipeline in docs/01-pipeline.md.
```

Working directories (`work/`, `assets/`, renders) are gitignored. Nothing heavy enters the
repo. See `docs/06-delivery.md` for where finished files go.

---

## The rules that get videos rejected most often

Full detail is in `docs/03-quality-bar.md`. In one screen:

1. **A first technically-correct render is a draft.** Budget three review rounds. That is the
   job, not scope creep.
2. **Frame QA is the only gate that works.** Lint, validate and inspect pass bugs that ruin
   a cut. Extract a frame at every beat and read them as images, every round.
3. **A beat that can only be expressed as a sentence in a box is the wrong beat.** Animate the
   physical event the line describes.
4. **Never put graphics on the face.** Above the chin is the face. A beat is either card mode
   or full-bleed with one self-grounded element in measured clear space. There is no third mode.
5. **Measure, never estimate.** Face geometry, crop rectangles, marker offsets and card widths
   are all arithmetic. Every "it looked about right" in this repo's history became a render round.
6. **No em dashes** in on-screen text, captions or published copy. Owner rule, all videos, all
   creators. Grep before every delivery.
7. **Match the original file size on delivery.** Both Instagram creators. See
   `docs/06-delivery.md`.

---

## Keeping the repo smart

After every completed video, update the creator's `HISTORY.md` with what the review rounds
changed, and promote anything reusable into the relevant playbook. A lesson that stays in a
chat log is a lesson the next operator pays for again.
