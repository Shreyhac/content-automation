# The pipeline

Eight stages, in order, every time. The order is not arbitrary: each stage produces the input
the next one measures against. Most rejected videos in this system's history skipped or
reordered one of them.

---

## 0. Identify the creator

Extract one frame from the A-roll and compare against `reference-cuts/`. The creator decides
the palette, the face treatment, the type stack, the SFX volumes and the layout grammar.

A brief has arrived from one creator's account carrying another creator's footage. The footage
wins, every time. Getting this wrong wastes the whole build.

Then read `creators/<creator>/PROFILE.md` and `GRAMMAR.md` before anything else.

---

## 1. Deconstruct the reference (only if one exists)

If the owner supplied a reference video or named a prior video by name as the style target,
**measure that file, do not describe it from memory.**

```bash
ffprobe -v error -show_streams reference.mp4
ffmpeg -i reference.mp4 -vf fps=2 ref/f%04d.jpg          # read them ALL as images
ffmpeg -i reference.mp4 -vn -ar 16000 ref/audio.wav
whisper ref/audio.wav --model small --word_timestamps True --output_format json
```

Write a `<video>-breakdown.md`: verbatim VO, beat map, shot-by-shot table (time, layer layout,
visual), design language, asset checklist.

**When the owner points at a prior video by name, open the file and take numbers off it.**
"vid39's face card" reads as "a portrait bottom-centre"; the file says x216 to x864, y1020 to
y1880, and its `bandOpen()` tweens clip-path and scale together over 0.34s. The move is what he
is reacting to, and you only find that by measuring.

If there is no reference, build from the brief using the creator's `GRAMMAR.md`.

---

## 2. Fact-gate and collect real assets

**Verify every claim and every repo before writing a word of the plan.**

- Repos: GitHub API. Paths move (`All-Hands-AI/OpenHands` now redirects). Star counts, language
  and SPDX come from the same call. Re-check immediately before delivery.
- Products: go to the source. A feature a VO names may live one layer down and not appear on any
  marketing page. Code-search the product's repo before concluding a claim is false.
- Numbers: vendor prose contradicts vendor tables. Quote the softer number. Preview-post figures
  go stale at GA.
- A **fabricated claim in an already-recorded VO is a decision, not a blocker.** Ask it as a
  scoped choice (soften / build literally / hold for a re-record) and write the fact gate at the
  top of the breakdown so whoever posts it knows what a commenter can be shown.
- **Sponsored work: resolve promo codes against the partner URL, never against whisper.** A
  wrong code in a sponsored video is the one unrecoverable error.

Capture real surfaces with `tools/qa/playwright-capture.py` (dark scheme, `device_scale_factor=2`,
viewport around 760px for 1080-wide placement). Over-capture in one run.

**Then rebuild what you captured as native HTML at reel type sizes.** A real screenshot scaled
into a card is unreadable and reads as vague. Keep the real chrome and the real URL for trust;
rebuild the body for legibility. See `playbooks/real-assets.md`.

---

## 3. Prepare the A-roll

**Whisper it before trusting any pasted script.** The audio is the source of truth.

```bash
whisper aroll.wav --model small --word_timestamps True --output_format json
```

Then:

- **Run the gap analysis before assuming a cut pass is due.** Two productions here needed no cut
  at all, which kept every word timestamp valid for the whole build. Deliberate pauses after
  listicle numbers are animation slots, not gaps.
- If cutting: trim video and audio together with the same in and out points, then **re-whisper
  the cut file**. Every timestamp after the first cut is otherwise wrong.
- **Whisper's word table is not a beat map for emphatic delivery.** A halting, staccato line
  (four separate stressed words) can get smeared into one or two long "words" spanning several
  seconds. Run an RMS envelope over the cut audio to find the real onsets and land each stress as
  its own beat: a transcriber optimises for text, not for where the emphasis actually falls. Not
  every gap in a halting delivery is dead air to cut: the gap is worth keeping when it sits
  *between* stressed words (his emphasis) and worth removing when it sits *inside* a stumble.
- **If the creator delivers a pre-cut, graded, mixed take, ship it untouched.** Transcode only.
  Do not loudnorm, denoise or regrade someone's own mix.
- Check for a **mirrored** front-camera take: readable text in frame decides it, per take, not
  per creator.
- Transcode into the project: `scale=1080:1920` for 9:16 (an oversized master is the biggest
  driver of render memory leaks), `-r 30 -g 15 -keyint_min 15`, libx264 crf 17.
- **Measure the head with Vision** (`tools/vision/crown.swift`, `facebox.swift`) and solve the
  face geometry. See `playbooks/face-geometry.md`.
- If the creator has a "don't show me reading my notes" constraint, run the gaze pass now:
  `tools/vision/gaze-detect.swift` then `tools/vision/build_windows.py`. See
  `playbooks/gaze-detection.md`.

---

## 4. Scaffold

Copy the creator's current reference build from `reference-builds/`, gut the scene assets, keep
the fonts, the SFX conventions and the package.json. Never start from a blank `index.html`.

**Order matters: scaffold first, then transcode into the new project dir.** Copying a donor
project on top of a directory where ffmpeg is writing has silently replaced a fresh transcode
with the donor's A-roll. Verify the A-roll's duration after any copy step.

Curate SFX per video from `library/sfx/`. Read `docs/05-audio-and-sfx.md` for the share cap and
the volume trajectory before picking anything.

---

## 5. Compose

Invoke the `hyperframes` and `gsap` skills first.

**Layout before animation.** Write the static hero frame for every scene, confirm the layout is
correct, and only then add entrances. No exit tweens except the final scene; transitions handle
exits.

- Scene boundaries land on word onsets, with a **0.20s lead** so the entrance completes under
  the transition. See `playbooks/transitions-and-cuts.md`.
- Every media element needs an `id`, or video renders frozen and audio renders silent.
- Initial hidden states go in `gsap.set()` outside the timeline, or in CSS. A zero-duration
  `tl.set(...,0)` does not reliably paint at position 0 and breaks the cover frame.
- Give every timed element a stable id.

Read `playbooks/gsap-traps.md` before writing tweens. It is a list of bugs that have each cost
at least one render round.

---

## 6. Gates

```
npx hyperframes lint
npx hyperframes validate      # WCAG contrast
npx hyperframes inspect       # layout, 12 to 14 samples
```

Plus a **Playwright pageerror check**: load the composition for 10 seconds, listen for
`pageerror`, and assert `window.__timelines` has keys. This is the only gate that catches script
death. A `ReferenceError` before timeline registration renders a page of static DOM, and lint,
validate and render all report success.

Fix everything. Mark genuinely intentional overflow with `data-layout-allow-overflow`, and a
scrolling viewport with `data-layout-ignore`, but understand that allow-overflow on a parent
blinds the gate for everything inside it: audit those subtrees by eye.

---

## 7. Render and frame QA

```bash
HF_DE_STALL_MS=420000 npx hyperframes render -q high --workers 3 --video-bitrate 16M
```

`HF_DE_STALL_MS` is not optional on heavy 4K or three.js compositions. A render that dies at
the same frame number repeatedly is the 60-second no-progress watchdog killing a healthy render,
not a hang and not disk pressure. See `docs/07-troubleshooting.md`.

**Then extract a frame at every beat plus frame 0 and read them all as images.**
`tools/qa/exact-frame-qa.sh` decodes once with a frame-number select expression. Never `-ss`
before `-i`: fast seek lands on the preceding keyframe and at `-g 15` returns frames up to 0.4s
early, which looks exactly like scene bleed and invents a whole round of phantom bugs.

Sample slams at onset + 0.05s, not later, or the settled state hides the clipping. Sample
reveals at onset + 0.3s and + 0.5s.

Expect two to three fix, render, QA rounds. Renders are cheap. Never batch doubtful fixes.

---

## 8. Deliver

See `docs/06-delivery.md` in full. The short version:

- Two-pass `loudnorm` with `-c:v copy`.
- Match the raw A-roll's byte size for both Instagram creators.
- Grep for em dashes in on-screen text and in the caption pack.
- Ship the MP4, the SRT and a caption pack with hashtags and keywords.
- Update `creators/<creator>/HISTORY.md` and promote reusable lessons into `playbooks/`.
