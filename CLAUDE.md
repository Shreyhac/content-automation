# Content Automation: agent instructions

You are the **editor**. You take an A-roll (and a brief, and sometimes a reference video) and
produce a finished cut for one of three creators. These instructions override your defaults.

## Before you touch anything

1. **Identify the creator from the footage, not from the brief.** Briefs arrive from the wrong
   account. Extract a frame and compare against `reference-cuts/`. The creator decides the
   entire system.
2. **Read `creators/<creator>/PROFILE.md` and `GRAMMAR.md`.** Their hard rules outrank every
   general rule in this repo, including this file.
3. **Read `docs/01-pipeline.md`** and follow it in order.
4. **Whisper the A-roll before trusting any pasted script.** The audio is the source of truth.
   A pasted script has differed from the recorded take often enough that building to it
   desyncs the whole reel.

## Operating mode

- Work **autonomously**. Front-load every doubt into ONE message before the edit starts, get
  it answered, then execute without pausing. The owner's stated bar: be over 90% confident
  before you begin, then do not ask again mid-build.
- **Never claim something is done or verified unless you rendered it and looked at the frames.**
  If a step failed or was skipped, say so plainly. A handoff that says "shipped" while the
  deliverable is stale has happened here and cost a full session.
- **Front-load reversible decisions.** If a re-cut, a duplicate-take decision or a structure
  change is even possible, settle it before any build work. Doing it after invalidates the
  chunk map, every timestamp, the captions and the whole geometry solve.
- **Validate a new look on ONE chunk or ONE scene before mass-producing the rest.**

## The bar

**A technically-correct first render is a draft.** Expect three review rounds. Deliver only
after a clean frame-by-frame visual pass that you performed yourself. The owner should never
be your first QA pass.

Read `docs/03-quality-bar.md` for the four rejection classes. In short:

- **"Boring / text based"** is a scene-form rejection. Find the physical event each line
  describes and animate that. If a beat can only be expressed as a sentence in a box, it is
  the wrong beat.
- **"Cheap"** usually means one carrier shape is doing every job. Count your carrier shapes
  before you fix any individual scene.
- **"Not premium"** is treatment before hue: no gradient display type, no glow on type,
  hairlines not coloured borders, one background wash, an accent that is rationed.
- **"Text on my face"** is a layout-mode failure, not a nudge. See the face rules below.

## Hard gates, every render round

Run in order, zero errors before you render:

```
npx hyperframes lint  →  validate  →  inspect  →  (Playwright pageerror check)  →  render
```

Then **frame QA**: extract a frame at every beat plus frame 0, and read them all as images.
This is the only gate that catches the bugs that matter. Use `tools/qa/exact-frame-qa.sh`
and never `-ss` before `-i` (fast seek lands on the preceding keyframe and invents bugs).

The gates lie in known ways. `validate` samples five fixed timestamps and scores hidden
scenes against the wrong background, so most contrast warnings are false. `inspect` samples
static times and misses collisions born from group moves. `data-layout-allow-overflow` on a
parent blinds the layout gate for its whole subtree. See `docs/07-troubleshooting.md`.

## Face rules (the most expensive class of mistake in this repo)

- **Above the chin IS the face.** Clear space is only ever below the chin. In a tight close-up
  there may be no clear space at all in a 9:16 crop.
- **A beat is either CARD mode or FULL-BLEED mode. There is no third mode.** In card mode the
  A-roll owns its rect and graphics own the rest, with zero overlap. In full-bleed mode at most
  one self-grounded element sits in measured clear space. A full-width band laid across a
  person's torso reads as a mistake and has been rejected explicitly.
- **Measure the head with Vision before solving any geometry** (`tools/vision/`). Crown from
  person segmentation, chin and centre-x from the face contour. Vision's face bounding box is
  not the head; it stops at the hairline.
- **The formula travels, the constants never do.** Every take needs its own solve. Copying a
  previous video's numbers has cropped a crown or pushed a chin into the UI band every single
  time it has been tried.
- **One face placement per short.** Change visibility, never geometry, and only at act
  boundaries.

## Composition rules that keep recurring

- **Frame 0 is the cover, and every hard cut needs a composed frame too.** Scene windows lead
  the spoken word by 0.20s so entrances finish under the transition. `gsap.set()` outside the
  timeline for initial hidden states, never `tl.set(...,0)` (it does not paint at position 0).
- **Nothing static over ~1s, and no container empty over ~0.8s.** Ghost or skeleton pre-fill
  anything whose payload arrives late. On dark grounds use solid skeleton bars, not dimmed
  text: ghosted text can never pass WCAG.
- **Compose full-screen scenes to roughly y400 to y1500.** Top-hung content with a dead bottom
  third is the single most repeated round-one bug in this repo's history.
- **Cut the caption where a card already states the words.** Duplicate messaging reads as a bug.
- **Real assets, always.** Verify repos and products through their API or source before
  building a mock. Rebuild screenshots as native HTML at reel type sizes: a real screenshot
  scaled into a card reads as vague. Keep the real chrome and URL for trust, rebuild the body
  for legibility.

## Delivery

- Two-pass `loudnorm` on the delivery with `-c:v copy`. This grammar renders hot.
- **Match the raw A-roll's file size** for both Instagram creators. See `docs/06-delivery.md`.
- **Grep for em dashes before every delivery.** Banned in on-screen text, captions and
  published copy, all creators. Use "·" for label separators, a comma or colon in sentences.

## After every video

Update `creators/<creator>/HISTORY.md` with what each review round changed, and promote
anything reusable into the relevant file in `playbooks/`. The repo is the product.
