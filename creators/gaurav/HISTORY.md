# gaurav: shipped work and what each round changed

Newest first. **The most recent approved grammar supersedes older entries.** He has reversed
himself several times; entries are dated so you can tell law from a round-scoped correction.

---

## vid47 v3, re-shooting the same script's A-roll in a new location (2026-08-01)

`gaurav5 new.mp4`, same ten-tool script, second location. Looks like a file swap; budget a full
production round for it, not a re-render.

**A re-shoot of the same script is a full re-time, not a file swap.** Take two ran 0.64→36.44
against take one's 0.00→33.00 (33.2s → 36.7s). All ten accordion beats, three wipes, the flash,
every caption and all thirty SFX cues had to re-anchor **word by word**: a constant offset is
wrong, because the two performances drift apart internally (the Dify beat moved +2.38s while the
first beat moved +0.60s). Verify by asserting every anchor lands on a real word onset in the new
stream.

**Whisper `small` renamed a product in the new room**: it heard "Coolify" as "Qualifier";
`medium` on a 1.6s window fixed it. Re-check every proper noun on a new take even when the
script is known, and patch the word-stream table, not the captions.

**Re-solve the band from the new take's measured SPREAD, not its median.** Same head size
(Vision face-width .242 vs .239) but he sat ~490 master-px higher and wandered vertically nearly
twice as far. Reproducing take one's head size put his chin past y1600 on **11%** of frames
against the approved cut's 2%. Widening the crop to 0.95× (`crop=2036:3620:0:0`, `top:596`, clip
inset `484`) gave head 397px and 2.7% over. Search `(top, scale)` against a percentile
constraint; a median-only fit hides the tail.

**Match the approved cut's measured band colour stats when the room changes.** The new room ran
warmer and darker; solving `eq`/`colorbalance` against the old band's Y/U/V/SAT (not by eye)
landed Y 148.6 vs target 147.3 and U/V within 0.1.

**A pre-turn beat must still be a composed frame.** Owner spec: "monitor look = hook, turn = the
video starts." Built literally (band up from frame 0, only the eyebrow lit), the cover was
1080px of empty paper plus a half-faded label. Fix: give the pre-turn beat the full bleed
instead: 0→0.55 is him at the monitor with no type, and the turn becomes a hard cut into the
split. Composed cover, graphics-free hook, a real event on the turn.

**Two clips pointing at one large source file kills the render.** `openVid` and `fullVid` both
referenced the 46MB `aroll.mp4`; the frame extractor decoded it twice and every capture worker
died on `Runtime.callFunctionOn timed out`. A dedicated 703KB `open.mp4` fixed it outright. This
is a different failure from the `HF_DE_STALL_MS` watchdog: the tell is *all* workers dying at
once on a protocol timeout, not a stall at a fixed frame.

**The 2048-sample audio delay is real and constant**: every render came out exactly 2048
samples (42.67ms) late, confirmed on three renders. Cheap fix that preserves the SFX bed:
`-af "atrim=start_sample=2048,asetpts=PTS-STARTPTS,apad=pad_dur=0.043"` before loudnorm.

**A card safe at the top is not safe at the bottom.** Owner note: the CTA card cut across his
forehead (crown y496, card base y620). Moving it below the chin was only half the fix, because
the like/comment rail lives at **x>960 between y900 and y1600**, which the top position never
had to avoid. The card had to narrow 940→880px as well as move.

### Delivering at the source's resolution, not just its byte count

The owner asked for the final "in the original size I gave it to you" **after** the byte match
was already done: the 2160×3840 of his master. `--resolution=portrait-4k` does this without
touching the composition (Chrome renders at DPR2; aspect must match, scale must be an integer
multiple).

- **Rebuild the A-roll assets at 4K first, or you ship an upscale.** The project's transcodes
  were 1080×1920; a 4K render off them would leave graphics/type sharp and his face soft.
  Re-cut `aroll` / `aroll-band` / `open` from the 2160×3840 master with the same crop and grade.
  Keep the 1080 set in `assets/_1080/` so a revert costs nothing.
- **The band crop is the one honest upscale.** `crop=2036:3620` filling a 2160-wide frame is a
  1.06× enlargement inherent to the crop, not the render. Say so rather than implying everything
  is native.
- Cost: **6m51 at `-q high --workers 2`** against 1m40 at 1080; size-match passes get
  proportionally slower too. Budget the round.
- The byte target doesn't change with resolution, and at 4K it stops being padding and starts
  being real: 148,119,682 bytes / 36.7s ≈ 32 Mbps, the source's own bitrate, so delivery matches
  the master on **both** axes.

---

## vid50, "Three markdown files that fix your brand" (2026-08-01)

27.87s / 836 frames, 1080×1920. Reference reel existed (@gregisenberg) but the A-roll was a
fresh single take. Owner's only direction: *"start from when he closes the lid of the laptop,
that is the hook."* Scaffolded on hf47 v2's approved paper split. `out/vid50-final.mp4`. Three
review rounds, all against the hook.

**The hook was already in the footage.** Frame-exact decode of the first 48 frames found the lid
near-vertical at frame 0 and shut by frame ~22 (0.73s), VO starting at 0.52. Nothing had to be
built: the title lands on the shut and the physical act carries the graphic. When an owner
points at a moment in the take, decode that range at full rate before designing anything.

**A band top can be geometrically unreachable, not just wrong.** With crop scale `s`, top offset
`oy≥0`, master crown y1418 and chin y2176: `crown_out ≤ min(1418s, 1560−758s) = 1016` at
`s=0.7166`. He sits high enough that no crop puts his crown at hf47's y1130 (zoom raises the
head, and zoom-out isn't available past 1:1). Ceiling was y956; built at y900, s=0.690. Check the
inequality before laying out the graphics zone, not after.

**`clip-path` resolves in the element's local box, before the transform.** The band was
`translate(-145px,2px) scale(1.379)`; `clip-path:inset(900px …)` clipped at screen y1243, not
y900, and round 1 shipped a slab of empty paper under every caption.
`local_inset = (screen_row − ty) / k` (here `(900−2)/1.379 = 651`); same for the corner radius.

**Two different renderer stalls, same symptom ("frames stop, no error").**
1. Three clips (`fullVid`, `bandVid`, `<audio>`) on one file (`aroll.mp4`) deadlocks the frame
   producer: 62 of 836 frames, then zero. Give every clip its own file; put VO on an extracted
   `.m4a`.
2. Long-GOP sources hang each worker at ~110 frames, a per-worker plateau at the same COUNT that
   means seek exhaustion, not a bad beat. Re-encode all-intra (`-crf 20 -g 1 -keyint_min 1
   -sc_threshold 0`) and the full 836 frames render in about a minute.
   Diagnose by counting frames on disk twice 45s apart, not by log.

**AAC priming delay is exactly 2048 samples**, confirmed again by cross-correlation (0.989):
`-itsoffset -0.042667` on the audio input took it to a measured 0ms. Same constant as vid47 v3.

**Exact file-size export needs a loop, not a formula.** x264 lands a few tenths of a percent off
its requested bitrate; the first pass overshot by 384KB with no headroom left. Scale the rate by
`(target − 400000) / actual` and retry (≤5 attempts), then pad with the `free` box.

Smaller things: `letter-spacing:-.045em` on Clash ate word spaces ("Your AI keeps" →
"YourAIkeeps" at 112px), eased to `-.03em` + `word-spacing:.16em`; 92px is the ceiling before a
serif sub wraps onto a second line. A 12%-alpha pill over full-bleed footage is invisible and
needs a solid `--card2` fill. The accent, Boston Clay `#B8422E`, is the real `tertiary` token of
the DESIGN.md shown on screen, so the film's accent is an instance of the system it explains, and
it stayed in the house terracotta family (the good version of theme-per-subject). SFX pulled from
2 woosh files across 8 wipes put one cue at 14.8% share; widened to 26 distinct cues / 27
triggers, max 7.4%, saas pack at 63%. neuform.ai (the reference reel's site) is login-gated so
it's neither shown nor implied reachable; `github.com/google-labs-code/design.md` and
`designmd.app` are both public and became the CTA's actual promise.

| Round | Note | Root cause and fix |
|---|---|---|
| 1 | "text is not visible" / "animations are a bit off" | Hook type cleared every safe zone but sat directly on wall art: **a safe zone is not a ground**; type on full-bleed footage needs its own paper panel. Panel depth must come from the crown's highest point across the whole window (source punch-in lifted it to y696 by t=1.5, not its y860 value at the cut), not from the value at the cut. Four type voices in one 700px block ("font is very off") cut to two. Every element in v1 entered `y:+N, autoAlpha:0` on power3/power4, one carrier reused, which reads flat regardless of sync; audit by counting distinct entrance verbs. |
| 2 | "this animation is weird" (hook break) | Arbitrary tilt (±1.4 to 3.4°) plus `ease:"none"` drift over 2.3s swung cards into each other and never settled, reading as broken, not as chaos. Rules that replaced it: never rotate, never drift linearly (settle then hold), corrupt the content not the geometry, one designed gesture beats N random ones, repeat a break rather than sustain it. First 0.6s was a still frame; fixed by moving every frame-0 element together (a shared ink-scan + pulse) instead of adding a first tween. |
| 3 | "No need to zoom his frame, just keep the original frame" / "animations should start when he closes the laptop" | The whole band construction was rebuilt with **no scale**: video at scale 1, paper panel `y0 to y820`, video translated **down 170px** (a reposition, not a zoom) so the head clears the panel edge; crown min 696+170=866 vs panel 820 (46px clearance), chin max 1126+170=1296 (well clear of y1600). This also kills the clip-path-local-space problem outright, since there's no transform to divide by. Graphics moved from frame 0 to the lid-shut gesture at 0.87s; frames 0 to 25 are pure footage. Relayout cost: graphics zone moved from y150 to y860 up to y0 to y810, captions shifted up 64px. |

---

## vid47, "10 free GitHub tools" (2026-07-30)

33.19s, 995 frames. Eight render rounds across two structures. No reference video.

### v1: REJECTED on look

Built on a three-band grammar with a GitHub-dark palette. His note, with a reference frame from
hf41:

> "We need the split-screen template like this. The colour seems very off and too coded, think of
> premium colours and premium fonts. We need to show the face more. The animations look good, the
> off-the-blocks animation doesn't sync up with the exact thing that we have been trying to say."

Three findings, all of which generalise:

1. **A dark IDE palette for a developer-tools subject reads as "coded", not premium.** Paper is
   the distance that makes it feel made.
2. **Synchronised is not simultaneous.** Two moves per beat, each on a specific word.
3. "Show the face more" is answered by the band top, not by more face beats.

What survived from v1 into v2: the 0.20s scene lead rule, the exact-frame QA method, the
real-asset method, and the three.js findings.

### v2: the paper split band

Ported hf41's Director's Desk wholesale because he had already approved it. Band top y1080,
face presence 45% to 91%. Ten tools as one accordion for 24.5s.

Cost a render round: **light and white brand marks vanish on paper.** Coolify, Langflow and
OpenHands shipped as blank tiles.

Other lessons: a paper wipe on a paper ground is an invisible cut. A card size drives the crop,
not the other way round, and a crop short on the left shows the previous column (check the sign
against the artefact). Absolutely-positioned siblings take no flow space.

**Stock footage was declined with the reason stated**: all ten beats already carry the tool's own
live interface, and generic tech b-roll under a beat with a real product surface is the same
failure as an earlier reel's borrowed rocket tiles. Offering the one honest place for it and
waiting beats assuming.

**Delivery**: this is the video where the file-size rule was set. See `docs/06-delivery.md`.

---

## vid43, Musk's AI U-turn (2026-07-28)

First three.js build in the repo. Three owner rounds landed on the **three-band layout**, which
is the answer to "text on my face" and "I want to be visible" at the same time:

```
TOP     y150 to y640    graphics, rebuilt posts, b-roll cards
MIDDLE  y700 to y1380   the A-roll, windowed and UNGRADED, nothing ever laid over it
BOTTOM  y1410           captions, on the dark bed below the window
```

**Don't move the text, move the face.** Every overlay landing on the presenter traces to a
full-bleed A-roll whose head occupies the band the type wants. Once the face has its own window
the scrim can be deleted entirely and he reads at full brightness.

Also: an abstract 3D glyph reads as a mistake, a 3D glyph carrying a real subject reads as an
idea. Putting his actual face on the U-turn track made the same geometry instantly legible.

Two failed passes on a decorative element means cut it, not tune it.

---

## vid41, HeyGen companion mode (2026-07-28)

First paper-world build for him. Source of the Director's Desk system that vid47 v2 ports.

- **The feature a VO names may live one layer down.** Nothing called "companion mode" existed on
  any marketing page; it is a HyperFrames run-shape documented only in the product's own repo
  skill files. Code-search the repo before concluding a claim is false.
- **A masthead BAR is the reliable way to put type behind a person on light footage.** Green type
  over his white wall was invisible and a scrim could not fix it, because the same line also
  crosses dark framed artwork. A solid ink bar with knocked-out type makes contrast independent
  of what is behind.
- **But text-behind-person needs a gap wider than the head at that y.** The bar at y528 put the
  word across his crown and it was half-eaten by hair. On a seated take with headroom, move the
  lockup into the headroom instead of restyling it.
- **Ship two transcodes of a wide-composed A-roll**: cropped for full-bleed beats, uncropped for
  the bottom band. Cheaper than forcing one geometry to do both jobs.
- **Never borrow a demo's SUBJECT as filler.** Storyboard tiles taken from the vendor's own launch
  film put six SpaceX rockets in a reel that never mentions SpaceX. A contact-sheet scene should
  be posters of **this reel's own beats**, re-cropped from the previous render.
- SFX pulled to 0.09 to 0.16 on "SFX quite high".

---

## vid35, ElevenLabs Vocals (2026-07-26)

Studio Void re-skin. Established the **rebuilt X-post card kit** and the **browser window
device**.

- **Screenshots of posts and UI read as "vague", so rebuild them as native HTML at reel type
  sizes.** Real data plus rebuilt chrome is authentic and readable.
- **When the VO describes a product's UI, show the real surface as a visible browser visit.**
  Window springs in, URL types, real page renders. Feature-film montage cuts read as decoration;
  the browser frame reads as proof.
- **`hyperframes render` happily renders a dead page.** A `ReferenceError` before timeline
  registration passes every gate. Add the Playwright pageerror check.
- **Round the band corners on the CLIP, not the element.**
- X-only launches hide from search engines; `cdn.syndication.twimg.com/tweet-result?id=<id>&token=a`
  returns full JSON for any public tweet.

---

## vid33, Kimi K3 (2026-07-25)

Nine versions. The most instructive rejection sequence in the repo, and the source of the
"round-scoped, not law" principle.

| Version | Verdict and lesson |
|---|---|
| v1, v2 | Handheld POV template, then hf-style scenes inside it |
| v3 | "Why tf everything is in black and white": **brand-faithful can be dead.** Theme-per-subject picks the family, but the reel still needs a saturated accent. Colour-code the conflict. |
| v4 | "Make it clean and polished": every device added to fix "too subtle" became clutter. **Motion and colour are substitutes, not additions.** Camera rig killed entirely. |
| v5 | "Not professional" is a treatment problem before a hue problem: no gradient type, no glow shadows, one wash, hairlines. Reserve the accent by counting where it appears. |
| v6 | **"Boring" outranks every earlier constraint.** The stripped locked-off cut came back rejected. Shipped: visual objects acting out each claim, a flat acid accent, the cinematic rig restored. |
| v7 to v9 | Punch-and-hold camera. Rebuild screenshots as UI. Split-band caption position. |

Also from v6: **mock the style in HTML plus Playwright before building.** Mock 1 was rejected and
mock 2 approved in one round, and mock 2's fixes became the build's design rules. Minutes in
mocks against hours in renders.

---

## Earlier era (vid5 to vid20, 2026-07-08 to 07-14)

**Largely superseded.** Kept for the standing rules it produced:

- **vid5, vid6 (07-09), the channel-wide corrections.** "The animation looks childish": retire the
  whole pixel and game family. "Show the real asset of everything you say." "The face is too
  zoomed in, he shot it zoomed out on purpose."
- **vid6 v2.** Navy dark scenes read childish; espresso was the answer, and espresso was itself
  retired at vid11 r2 as "very weird".
- **vid10 (07-10).** His footage ships exactly as delivered, mirrored or not. Crop the dead
  headroom at the ffmpeg stage so the face reads big without zooming.
- **vid19 r2, r3 (07-13).** One hook idea gets one text layer. Ink pill slabs read cheap. **The
  hook must visualise its metaphor, not caption it.** Abstract match-card metaphors are boring;
  give characters an activity.
- **vid18 r2, vid20 r2 (07-14).** Static pills popping on the face are still a text stack. On both
  channels the hook is an acted micro-story with the creator visible, never a type lockup. Props
  on live footage read as noise; props on a panel read as story.
- **vid9 (07-10).** Theme is per-SUBJECT, not per-creator. The premium bar is STORY, not styling.
  A CTA needs a payload. On a news reel the reference video is a source of errors, not truth.
