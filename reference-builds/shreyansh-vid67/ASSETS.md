# vid67 assets manifest

A reference reel rebuilt shot for shot on the creator's own A-roll, and the first build in the
portfolio that runs a **pre-render gate script** and a **beat contact sheet** before any render,
and that ships a **chunked render of a short**.

Shipped result: `reference-cuts/shreyansh-vid67-launch-your-agent.mp4` (720p proxy).
Delivered original `out/vid67-final.mp4`: **1057 frames, 2160x3840 @ 30fps, 38.28 Mbps, 35.233333s,
168.6 MB.** His master runs 33.15 Mbps, so delivery sits above it, which is the rule.

Ships here: `index.html`, the three chunk documents `index-c1/c2/c3.html`, `package.json`,
`transcript.json`, `caption.md`, the two gate scripts from `hf67/`, and the pipeline scripts and
solved JSON from the working folder `vid67/`.

**Which HTML is canonical.** `index.html` is the full 35.233333s composition and the readable
source of truth: every constant and every reason is commented in it. It is **not** the file that
produced the delivered frames. It never rendered: the capture engine stalled at frame 746 of 1057
on this machine with 18 videos in the page, and again at 743 with 2. `index-c1/c2/c3.html` are the
emitted chunks (346 + 343 + 368 = 1057 frames) that did render, in 2 to 2.5 minutes each, and were
stream-copied together. Read `index.html` to understand the film, regenerate the chunks with
`build_chunks.py` after any edit, and never hand-edit a chunk.

---

## A-roll, `assets/aroll.mp4`

Master `/Volumes/Shreyansh/shreyanshs set 4/edited/agentss.mp4`: 35.233s, 2160x3840 HEVC,
33.15 Mbps, 30fps, his own manual cut, no CapCut watermark (checked top-left and bottom-right at
full resolution). **The drive is external.** If it is not mounted the master is not fetchable and
the transcode in the project is the only copy.
**Verified present and readable 2026-08-15** with the drive mounted: 35.233s, 2160x3840 HEVC,
33.15 Mbps, exactly as recorded above.

Transcoded at **native 2160x3840**, codec change only, no scale filter: h264 crf 14, which measured
43.23 Mbps. A 1080x1920 transcode here would have shipped a 4K container carrying 1080p of his
face.

**Face geometry, measured over all 176 samples of the take** (`vid67/facebox.csv`, Apple Vision,
in 1080x1920 stage space): crown y280 to y375, chin y1003 to y1166, **886px head worst case**.

As built, two states and nothing else:

| State | clip-path on `#faceScene` | camera on `#faceCam` |
|---|---|---|
| `full` | `inset(0px 0px 0px 0px)` | `x0 y0 scale 1` |
| `split` | `inset(620px 0px 0px 0px)` | `x0 y380 scale 1` |

Seam at **y620**, picture pushed down **380**. That puts the worst crown at y660, which is 40px
below the seam, and the worst chin at **y1546**, 54px above Instagram's y1600 band. Delivered chin
maximum measured **1548.7**.

The reference seams at y955 because Cintas sits further from his lens. Copying that number would
have buried this chin. **Copy the shot list, re-derive the geometry.**

There is no tween between the two states anywhere in the file. Every change is a `gsap.set` on a
cut, and **no CSS transform ever animates on a box containing a `<video>`**, which is what
deadlocked the capture engine on the previous build.

---

## The B-roll band, `assets/bandtrack.mp4`

One pre-composed 2160x1240 track at 2.85 Mbps, always playing, revealed only on `split` beats by
`#btop`. It replaced seventeen separate `<video>` elements. That did not fix the render stall (the
ceiling is per-frame accumulation on an 8 GB machine, not video count) but it is what an editor
would build anyway: they are one track, not seventeen layers, and with a single always-on element
there is no `data-start` window for a clip to fall outside of.

Built by `vid67/build_band.py` from the seventeen source clips in `assets/broll/`:

| Group | Files | Origin |
|---|---|---|
| Lifted | `b01_tree` … `b11_reply` (11) | Windows cut out of `refs/DbqcQUgxlyC.mp4`, the reference reel |
| Rebuilt | `m1_claude`, `m2_env`, `m3_launch`, `m4_spec`, `m5_meeting`, `m6_inbox` (6) | HTML mocks rendered by `vid67/render_mocks.py` |

**Why six had to be rebuilt rather than lifted.** Permission was not the constraint, the frames
were: the Claude app is titled `Dr Cintas` in four shots, the `.env` shows a live
`ANTHROPIC_API_KEY` in plaintext, the meeting notes belong to a third party, the inbox is a real
person's, the launch **fails on screen** ("insufficient credit balance") under a voiceover saying
it deployed, and the spec page reads `PLANNED . NOT LAUNCHED`. The last two matter most: the
creator faked his own payoff, and lifting it would have put a contradiction on the beat the reel
exists to sell.

**The crops.** The reference burns its own captions into the picture at y924 to y975 (measured), so
no lift may extend past y920. Each lift is a 1080x620 window with a per-shot y offset chosen so
that shot's payload survives, then 2x lanczos to 2160x1240. The reference is 1080x1920, so **every
lifted shot carries half this composition's detail**; the six rebuilds are the only shots at true
resolution.

Every source window is pulled **0.13s wide at both ends** because input seeking lands where it
likes, and slots are derived from the detected cut list rather than eyeballed midpoints so that a
slot cannot structurally contain a cut.

`-t` before `-i` limits what is READ, after `-i` it truncates the RESULT. With `setpts` slowing a
clip, `-t` as an output option silently cut two clips back to their source length. Frame-count
asserts caught it.

Regenerate: `refs/fetch.sh` pulls `DbqcQUgxlyC.mp4` again, then
`python3 cut_broll.py && python3 render_mocks.py && python3 build_band.py`.

---

## Re-timing the reference, `remap.py` + `shotmap.json` + `broll-manifest.json`

He recorded the reference's script **verbatim**, which is what made a shot-for-shot copy possible.
39.53s of reference onto 35.23s of delivery is **not** a linear squeeze. `remap.py` aligns the two
normalised word sequences with difflib, anchors **136 of 148 words**, maps each reference cut
through the piecewise-linear result, then snaps it to the nearest word onset in his take. Every
boundary landed within 0.24s of an onset and most inside 0.10s. A ratio would have drifted a third
of a second by the CTA.

`shotmap.json` is the 28-row reference-time to his-time map. `broll-manifest.json` is the solved
slot table (id, start, duration, source window, crop y).

---

## Chunks, `assets/chunks/` (9 files)

`c1_aroll.mp4` / `c1_band.mp4` / `c1_vo.m4a` and the same for c2 and c3, all pre-trimmed so both
videos start at 0. Durations `11.533300`, `11.433300`, `12.266633`.

Boundaries were placed on **real cuts the edit already had**, so every join is a hard cut. Timeline
events before a chunk are applied statically at load, because a negative GSAP position does not
clamp, it shifts the whole timeline.

**Video is stream-copied at assembly so every delivered frame is bit-identical to its chunk render.
Audio is rebuilt once over the full 35.233s** from the continuous VO plus absolute-timed cues,
because AAC has encoder priming at the start of every stream and joining three of them puts a
discontinuity at each boundary, which is the exact shape of a "weird audio cut" note.

Regenerate: `python3 build_chunks.py` then `python3 assemble.py`.

---

## Voiceover, `assets/vo.mp4`

His A-roll's own audio, untouched. **-22.6 LUFS in, -22.5 LUFS out.** No grade, no filter chain.

---

## Fonts (3 used of 22 present)

`index.html` declares only `inter-800`, `inter-600` and `fraunces-italic`. The build's
`assets/fonts/` folder carries 22 files inherited from the donor project, including **`Gaegu-400`
and `Gaegu-700`, which every shreyansh build from hf63 onward loads**. All of them live in
`library/fonts/`.

---

## SFX, `assets/sfx/` (21 cues, 6 distinct files)

`riser`, `wsh`, `wsh2`, `click`, `click2`, `shine2`, from `library/sfx/house/`. Volumes 0.11 to
0.16, deliberately at the floor of the house range: the reference has no sound design at all and
this cut only marks the hardest cuts.

Beyond those, the only effect in the file is a **single white frame at 0.40 opacity** on the two
hardest cuts (2.200 and 16.340).

---

## Captions

70 captions, 1 to 4 words each, on a dark pill, **every change on a word onset**. On `split` the
pill sits at `top:548px`, in the band's lower edge, where the reference puts its own. On `full` it
drops to `top:1246px`, below his chin.

Two gate holes made these invisible to every caption rule for a whole film:

1. `tl.time(t, false)` suppresses events, so the `tl.call()` that writes the caption never fires
   for a gate. `#cap` carried no text and `isText` was false. The probe now resolves the caption
   from `window.__CAPS` instead.
2. `#cap` is `display:inline-block` and statically positioned, so a
   `position === absolute|relative` filter skipped it, while its parent `#capW` has no text node of
   its own. **Any element carrying its own text is now measured regardless of position.**

`#cap` is `inline-block` on purpose: a full-width centred container measures 1080px wide and trips
every edge gate falsely.

---

## The gates, `guard67.py` and `shoot67.py`

Both run **before** a render, because a render round costs minutes and these cost seconds. Both
walk the same 41-entry beat list (every scene boundary plus the frames inside a beat where
something lands).

`guard67.py` checks four things, each of which has shipped past `lint` and `validate` in this repo
before:

1. a referenced asset that does not exist on disk (a broken `<img>` is invisible to every
   structural check)
2. every absolutely-positioned element that actually **paints**, not just `.scene` children
3. text landing on text, measured by box and excluded by DOM ancestry
4. ink coverage: a beat whose graphics zone is emptier than 1.5% fails, because one element over
   blank paper passes everything else

Zone constants it enforces, in 1080x1920 stage space: `TOP_TEXT 150`, `BAND_Y 1600`, `RAIL_X 960`
between `RAIL_Y0 900` and `RAIL_Y1 1600`.

`shoot67.py` writes the beat contact sheet from the live page. Nothing is playing, so each
`<video>` is seeked by hand to `t - its own data-start`.

**A guard that has never fired is not a guard.** The first face detector in this build thresholded
skin fraction at 0.10 and passed a clip cut deliberately from a known face segment (it measured
0.059). Calibrating at the crop geometry the clips actually use showed skin does not separate at
all: a face frame measures 0.0455 and a UI lift 0.0452. **Luminance separates by 28 levels with no
overlap** (face 107 to 113, UI 37 to 80). Requiring both in the same frame flags all eight
known-face cuts and passes all eleven UI lifts. That is `facecheck.py`.

Vision itself found two full-bleed face segments in the reference. A skin-fraction sweep over the
band found three. The one Vision missed, 19.40 to 20.10, is where only his forehead and eyes are in
frame, and it is exactly the one that bled into two lifted clips.

---

## Proving the render

Two passes, in order:

1. **The joins.** The frame pair either side of each boundary must be identical in caption, face
   state and face position, with only the B-roll changing.
2. **The film.** Then scan EVERY frame for the artifact the design could produce: here, a band that
   is black while the composition is in `split` would be a one-frame black flash. Zero of 1057
   frames had it. Reasoning about `round` versus `ceil` boundaries produced two contradictory
   predictions; the full-frame scan answered it in one command.

---

## Regenerating

```bash
bash ../refs/fetch.sh DbqcQUgxlyC     # the reference reel
python3 remap.py                      # difflib word alignment, writes shotmap.json
python3 build_shots.py                # detected cut list -> slots
python3 cut_broll.py                  # 11 lifts out of the reference
python3 render_mocks.py               # the 6 rebuilds
python3 build_band.py                 # one 2160x1240 band track
python3 build_captions.py             # 70 captions -> captions.js
python3 build_index.py                # emits index.html
python3 guard67.py && python3 shoot67.py     # gates, before any render
python3 build_chunks.py               # emits index-c1/c2/c3.html + assets/chunks/
npx hyperframes render -q high -f 30  # once per chunk
python3 assemble.py                   # stream-copy video, rebuild audio once
```

Inputs that do not ship here: the A-roll master on the external drive, `vid67/facebox.csv` and
`vid67/crown.csv` (the Vision measurements), and the reference MP4 itself, which `refs/fetch.sh`
re-downloads.
