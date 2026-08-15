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

**`ffprobe` the colour tags of every non-generated clip at intake**, before it enters a
composition. One 10-bit HEVC clip tagged `arib-std-b67`/`bt2020` flips the whole render to HLG and
shifts the untouched A-roll with it. See `docs/06-delivery.md`.

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
- Transcode into the project **at the resolution the composition actually outputs**, codec change
  only: `-r 30 -g 15 -keyint_min 15`, libx264 crf 17, and no `scale` filter at all if the master
  is already the right aspect. These compositions render at 2160x3840 (a 1080x1920 `#stage`
  scaled 2x), so a 1080x1920 asset is upscaled back to 4K and the delivered file is a 4K container
  carrying 1080p of his face. Measured on vid60: the composition rasterises **84% sharper** from a
  2160x3840 asset than from a 1080x1920 one, 95% of the master's detail against about 52%. vid55
  and vid57 both shipped with that loss. If a composition genuinely outputs 1080x1920 (client
  shorts), 1080 is correct. **Match the asset to the OUTPUT, not to a habit.** An oversized master
  does drive render memory pressure, so pay for it with worker count and `HF_DE_STALL_MS`, not by
  throwing away resolution. See `docs/03-quality-bar.md` for the delivery contract this serves.
- **Never grade his A-roll.** No LUT, no curves, no `eq`, no loudnorm on a delivered mix. The
  renderer already shifts colour 3 to 7% on its own, so a grade on top is a shift nobody can
  account for. Grades were caught and removed on vid49, vid54 and vid55.
- **Measure the head with Vision** (`tools/vision/crown.swift`, `facebox.swift`) and solve the
  face geometry. See `playbooks/face-geometry.md`.
- If the creator has a "don't show me reading my notes" constraint, run the gaze pass now:
  `tools/vision/gaze-detect.swift` then `tools/vision/build_windows.py`. See
  `playbooks/gaze-detection.md`.

### A raw take and a cut master are two clocks, and the folder does not say which

`crown.csv`, `facebox.csv` and `gaze.csv` on one project were measured on `frames5/`, 1851 frames
at 5fps off the **raw** take, 370.2s. `short-beats.json` was timed against `aroll-cut.mov`, the
raw take minus two retake spans totalling 18.41s, so 351.9s. Beats 1 to 5 agreed because they all
sit before the first cut; beats 6 and 7 were 18.41s apart, so the solver framed **the close**, the
one beat the client had already sent a note about, against footage six seconds of speech away from
what actually plays. Every number it printed looked plausible.

- **When two files in one folder are both "seconds", check which clock.** Put the mapping in one
  `cut_to_raw()` built from `cuts.json`, and have the sampler assert no beat straddles a removed
  span rather than assume it.
- **Confirm the mapping by matching frames, not by re-reading the arithmetic.** Cut t=331.06
  best-matched raw `f_01748` (349.4s) at a mean luma error of 1.5, against 9.0 for the unmapped
  frame. Arithmetic that is wrong still produces a number; a frame match does not.

### Read any lifted B-roll full-frame, alone, before it goes near a card

"Use the B-roll from that reference" does not mean the clip you cut out is the clip you saw. On
vid66 the reference composited Apple's product footage into the **top half** over its own
creator's talking head, with his word-captions on the seam. Scene detection gave correct shot
boundaries, the extracted clips were at the right timestamps, and every contact sheet looked
right, because a 6-across tile at 270px cannot resolve a second face and a centre-weighted
`object-fit:cover` crop lands exactly on the seam. It reached a finished 4K render.

Extract one frame from the clip itself at full size and read it alone, not in a tile and not
composited. If the source is a layered reel, crop at extraction time with `crop=W:H:X:Y`, never
with an `object-position` nudge: the nudge only moves the window over the same contaminated frame.
Lifted footage can also carry visible credentials, or contradict its own VO.

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
- Match the raw A-roll's byte size for both Instagram creators, and verify the delivered
  resolution and bitrate with `ffprobe` against the master. Pin the bitrate; CRF is not a
  delivery contract.
- Grep for em dashes in on-screen text and in the caption pack.
- Ship the MP4, the SRT and a paste-ready caption pack. **No hashtags**, current Instagram
  practice: the caption body is the ranking surface.
- If the script says "comment X and I'll send you Y", the payload `.docx` ships with the first
  delivery, not when he asks (`tools/deliver/make_cta_doc.py`).
- Update `creators/<creator>/HISTORY.md` and promote reusable lessons into `playbooks/`.
