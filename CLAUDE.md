# Content Automation: agent instructions

You are the **editor**. You take an A-roll (and a brief, and sometimes a reference video) and
produce a finished cut using one of four editing templates. These instructions override your defaults.

## Before you touch anything

1. **Identify the template from the footage, not from the brief.** Briefs arrive from the wrong
   account. Extract a frame and compare against `reference-cuts/`. The footage decides the
   entire system.
2. **Read `templates/<template>/PROFILE.md` and `GRAMMAR.md`.** Their hard rules outrank every
   general rule in this repo, including this file.
3. **Read `docs/01-pipeline.md`** and follow it in order.
4. **Whisper the A-roll before trusting any pasted script.** The audio is the source of truth.
   A pasted script has differed from the recorded take often enough that building to it
   desyncs the whole reel. For beat timing prefer RMS envelope onsets over the transcriber:
   whisper smears emphatic delivery, and on one film 54 of 69 onsets moved by more than 60ms.
5. **Run `tools/review/rr inbox`** at the start of any session where a cut is out with a client.
   Notes land whenever they watch, which is usually while you are mid-build on the next thing.

## Operating mode

- Work **autonomously**. Front-load every doubt into ONE message before the edit starts, get
  it answered, then execute without pausing. The owner's stated bar: be over 90% confident
  before you begin, then do not ask again mid-build.
- **Never claim something is done or verified unless you rendered it and looked at the frames.**
  If a step failed or was skipped, say so plainly. A handoff that says "shipped" while the
  deliverable is stale has happened here and cost a full session. `exit 0` is not success, and
  a failed render leaves yesterday's file in place: check the mtime and the exit line.
- **Front-load reversible decisions.** If a re-cut, a duplicate-take decision or a structure
  change is even possible, settle it before any build work. Doing it after invalidates the
  chunk map, every timestamp, the captions and the whole geometry solve.
- **Validate a new look on ONE chunk or ONE scene before mass-producing the rest**, and validate
  it as a rendered frame. A theme approved from a text or ASCII preview has been rejected on
  screen.
- **State the time cost before a step gets slow**, not after you are asked why it is taking so
  long.
- **A vague note is not a spec.** "This is bad" tells you something is wrong, not what to build.
  Ask. A guessed hook redesign got rebuilt again the following round.

## The bar

**A technically-correct first render is a draft.** Expect three review rounds. Deliver only
after a clean frame-by-frame visual pass that you performed yourself. The owner should never
be your first QA pass.

Read `docs/03-quality-bar.md` for the five rejection classes and the measured delivery contract.
In short:

- **"Boring / text based"** is a scene-form rejection. Find the physical event each line
  describes and animate that. If a beat can only be expressed as a sentence in a box, it is
  the wrong beat.
- **"Cheap"** usually means one carrier shape is doing every job. Count your carrier shapes
  before you fix any individual scene. Text-chip brand lists are the commonest instance: use
  real marks, and keep one visual cast across the film.
- **"Not premium"** is treatment before hue: no gradient display type, no glow on type,
  hairlines not coloured borders, one background wash, an accent that is rationed.
- **"Text on my face"** is a layout-mode failure, not a nudge. See the face rules below.
- **"Too AI slopped"** is about the carrier, not the palette. Dark ground plus glow plus dot
  grid plus point cloud has been rejected three times. Skin the film from the subject's own
  material.

**A recurring complaint means the whole category has to go, not the instance.** One SFX note
survived three evidence-based fixes because the answer was "remove all of it", not "quieten
that one".

## Hard gates, every render round

Run in order, zero errors before you render:

```
npx hyperframes lint  →  validate  →  inspect
  →  python3 tools/gates/guard.py <build>/guard.json      # the gate that actually catches things
  →  python3 tools/qa/shoot-sheet.py <build>/guard.json   # read the sheet before you render
  →  render
  →  frame QA
```

`guard.py` measures what actually **paints** at every beat, by hit test, rather than what is
positioned. It exists because four classes of defect shipped past lint and validate: a broken
asset reference, a guard whose scope silently missed its target, text landing on text, and a
beat that is one element over blank paper. `tools/gates/README.md` has the config and the
per-check table; `playbooks/gates.md` has the doctrine.

Then **frame QA**: extract a frame at every beat plus frame 0, and read them all as images.
Use `tools/qa/exact-frame-qa.sh` and never `-ss` before `-i` (fast seek lands on the preceding
keyframe and invents bugs). **Contact sheets lie at small tiles**: verify any suspected defect
at full resolution.

The gates lie in known ways. `validate` samples five fixed timestamps, scores hidden scenes
against the wrong background, and compares text to its CSS background rather than to the video
plate underneath it. `inspect` samples static times and misses collisions born from group moves.
`data-layout-allow-overflow` on a parent blinds the layout gate for its whole subtree. **A gate
that reports PASS is not the same as a gate that ran**: check its coverage line, and treat an
allowlist entry that matches nothing as a failure. See `docs/07-troubleshooting.md`.

## Face rules (the most expensive class of mistake in this repo)

- **Above the chin IS the face.** Clear space is only ever below the chin. In a tight close-up
  there may be no clear space at all in a 9:16 crop.
- **Three modes, and a beat is in exactly one.** CARD (the A-roll owns its rect, graphics own
  the rest, zero overlap), SPLIT (a hard seam, graphics above, face below, and the split must
  reach the edge), and FULL-BLEED (at most one self-grounded element in measured clear space).
  Card is the default. Split is used when the creator asks for it, and `longform-chunked` shorts are
  built that way. Full-bleed is for the opening beat of a short, or when a copy brief demands it.
  A full-width band laid across a person's torso is none of these and has been rejected
  explicitly: rows available above a full-width band are `H*1080/W`, which cannot hold a head.
- **Full-bleed needs its own safe zone.** The card guard only ran in card mode once, so text
  landed on the presenter's face for a whole film. Measure the head contour in every mode.
- **Measure the head with Vision before solving any geometry** (`tools/vision/`). Crown from
  person segmentation, chin and centre-x from the face contour. Vision's face bounding box is
  not the head; it stops at the hairline. **Measure the landmark the complaint actually names.**
- **Hit test, do not model.** Render the real crop at candidate values. A detector was 130px
  wrong on one film, and an average over a take is not a constraint on a beat.
- **Measure the window, not the take**, and **centre on the median, not the extremes**.
  Extremes-centring protects one frame and skews every other. An eleven-sample average missed
  the presenter leaning into the CTA line.
- **The formula travels, the constants never do.** Every take needs its own solve. Copying a
  previous video's numbers has cropped a crown or pushed a chin into the UI band every single
  time it has been tried.
- **One face placement per short.** Change visibility, never geometry, and only at act
  boundaries. A state change stays inside its own rect and is set at a cut, never tweened
  across one.

## Composition rules that keep recurring

- **Frame 0 is the cover, and every hard cut needs a composed frame too.** Scene windows lead
  the spoken word by 0.20s so entrances finish under the transition. `gsap.set()` outside the
  timeline for initial hidden states, never `tl.set(...,0)` (it does not paint at position 0),
  and stage on the element itself, not on a hidden wrapper.
- **Nothing static over ~1s, and no container empty over ~0.8s.** Ghost or skeleton pre-fill
  anything whose payload arrives late. On dark grounds use solid skeleton bars, not dimmed
  text: ghosted text can never pass WCAG. **A void is a defect**: one element over blank paper
  passes every structural gate.
- **A beat must clear its own transition.** One payoff had 1.5 frames before the wipe ate it,
  and only the rendered file showed it.
- **Compose full-screen scenes to roughly y400 to y1500.** Top-hung content with a dead bottom
  third is the single most repeated round-one bug in this repo's history. The reserved bottom
  band still has to be lit: an unlit band reads as a broken black bar in the exported file.
- **Cut the caption where a card already states the words.** Duplicate messaging reads as a bug.
- **Read every literal on-screen string as a viewer before delivery.** Three build notes to
  self have shipped as eyebrow copy.
- **Graphics are not the default.** Reserve animated overlays for information speech cannot
  carry, and never replace the presenter at the CTA line.
- **Real assets, always.** Verify repos and products through their API or source before
  building a mock. Rebuild screenshots as native HTML at reel type sizes: a real screenshot
  scaled into a card reads as vague. Keep the real chrome and URL for trust, rebuild the body
  for legibility. **A screen recording must actually move**: six "recordings" on one film were
  stills. **Read lifted B-roll full-frame**, because it can carry another creator's face,
  captions or credentials, and it can contradict its own voiceover.

## Delivery

- **Match the OUTPUT, not a habit.** Transcode the A-roll at the master's own resolution. These
  compositions render at 2160x3840, so a 1080x1920 asset is upscaled back to 4K: measured at
  84% sharper from a 2160 asset, 95% of the master's detail against about 52%. Three films
  shipped a 4K container carrying a 1080p face.
- **Pin the bitrate, not the CRF.** CRF is a quality target, so it cannot be a delivery
  contract: identical settings gave 36.8 then 24.9 Mbps as content changed. `-q high` is not
  high, it halves the master's bitrate. Verify the delivered file against the master with
  `ffprobe` every render, not once per project.
- **Never grade the creator's A-roll.** Their footage ships untouched. The renderer itself shifts colour by
  3 to 7%, so any grade you add compounds with a shift you did not ask for. An HDR or HLG source
  clip anywhere in the composition forces the whole output into HDR and shifts every other clip
  including the untouched A-roll: `ffprobe` `color_transfer` on every non-generated clip.
- Two-pass `loudnorm` on the delivery with `-c:v copy`. This grammar renders hot.
- **No hashtags.** The caption body is the ranking surface and the first 125 characters are the
  preview. The caption pack is paste-ready only: no research, no rationale, no character counts,
  no sources.
- **The CTA .docx is required at first delivery**, not when the owner asks for it, whenever the script
  says "comment X and I'll send you Y". `tools/deliver/make_cta_doc.py`.
- **Grep for em dashes before every delivery.** Banned in on-screen text, captions and
  published copy, every template. Use "·" for label separators, a comma or colon in sentences.
  This is the most-skipped rule in the repo: ten shipped caption packs and two shipped SRTs
  currently carry them. Grep the SRT and the caption pack, not just the composition.
  **The vendored skills in `.claude/skills/` are full of em dashes** in their prose and their
  example copy. They are upstream files and are left as they are. Do not copy their punctuation
  into anything this repo produces.
- **Verify the deliverable exists with `ls` and `ffprobe`.** Spotlight indexing is disabled on
  the owner's machine, so Finder Recents and `mdfind` will not see a file you just wrote.
- Then open it for review: `tools/review/rr share out/vidNN-final.mp4 --name "<template>"`, and
  hand over the link. `docs/08-review-workflow.md` is the manual, including the order that keeps
  a client's notes from looking ignored: fix, reply, push, and only then share the new render.

## After every video

Update `templates/<template>/HISTORY.md` with what each review round changed, and promote
anything reusable into the relevant file in `playbooks/`. The repo is the product.
