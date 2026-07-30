# vid46 long-form assets manifest

The **chunked 16:9 architecture**. Shipped as 8 chunks concatenated losslessly: 3:43.4, 6702
frames, 3840x2160 at 30fps, -14.5 LUFS / -1.0 dBTP.

**This is a partial build.** The shared foundation plus one specimen chunk (`c1`), which is enough
to read the architecture. Chunks c2 to c8 stayed in the original repo.

Shipped result: `reference-cuts/nader-vid46-incogni-longform.mp4`.
Architecture: `playbooks/longform-chunking.md`. Full design notes: `design.md` in this folder.

**It is a paid placement.** The upload needs YouTube's paid-promotion flag.

---

## What ships here

| File | What it is |
|---|---|
| `assets/base.css` | Palette, the six-layer 4K ground, the carrier vocabulary, face-card geometry, caption band, type scale. One place to fix a join across eight projects. |
| `assets/chunk.js` | `mountGround`, `faceCard`/`faceFull`/`hideFace`/`blink`/`cut`, `wordRise`/`splitWords`/`digitSettle`, and `put()`. |
| `assets/field.js` | The recurring three.js object: a single 750-instance plate field with six named layouts, used at four points across four minutes. **The one device the client named as good, twice. Do not redesign it.** |
| `c1/index.html` | The specimen chunk. |
| `card-transforms.json` | The per-window solved face-card transforms. Never hand-typed; written by `tools/chunking/inject_windows.py`. |
| `face-safe-windows.json` | The gaze map: 24 windows where his face may be shown. |
| `words.json` | The word stream the whole film is anchored to. |
| `design.md` | The full design spec. |

---

## Media the build expects (none of it ships)

### A-roll, `assets/aroll/cN.mp4`

One clip per chunk, cut from the client's 4K master.

```bash
# fast seek + exact frame count. A select filter forces a full decode of the 1GB HEVC
# master once per chunk; this is about 8x quicker and still frame-exact.
ffmpeg -nostdin -ss <t0> -i <master> -frames:v <n> -c:v libx264 -crf 17 ... assets/aroll/cN.mp4
```

The film was **re-cut** before any build work (`tools/aroll/recut.sh`): 493 frames removed at two
splice points, both chosen to sit **inside note-reading runs** so the face is hidden across both
joins and neither can read as a jump cut.

### VO

One continuous cleaned master, muxed in **at assembly**. **Never concatenate the VO**: chunk
renders carry the SFX bed only, the A-roll `<video>` stays `muted`, and there is no `<audio>` for
voice, so none of the seven joins can produce an AAC priming gap or a click.

### B-roll (9 cuts)

Pexels, plus the subject's own material. Always carded, never full-bleed. Graded at the ffmpeg
stage toward the palette, encoded at display size with `-g 30 -keyint_min 30 -an`.

Three round-one clips were replaced outright after reading their midframes showed they were
genuinely poor. See `playbooks/stock-footage.md`.

### Brand marks, `assets/brand/`

Real SVGs with fills rewritten to white. Not filtered screenshots.

### Fonts (5, all in `library/fonts/`)

```
rethink-sans-var  dm-sans-var  geist-mono  fraunces-italic  fraunces-normal
```

**Declare `@font-face` inline in every chunk as well as in `base.css`**, or the static guard cannot
see the faces and the render silently falls back. **But do NOT duplicate the ground or palette
inline**: round one did, and editing `base.css` then silently did nothing.

### SFX

57 distinct files, 186 placements, top share 4.3%. Built by `tools/sfx/sfx.py` (which enforces the
caps) and rendered to one continuous bed by `tools/sfx/build_bed.py`.

**The bed is built beside the render, never extracted from it.** Reconstructing it from chunk audio
couples sound to picture, so changing one volume would mean re-encoding 4K video to hear it, about
six minutes a chunk.

---

## The measurement inputs

The gaze and geometry passes ran on 5fps stills of the re-cut master:

```bash
swift tools/vision/gaze-detect.swift stills/ > gaze.csv
swift tools/vision/crown.swift       stills/ > crown.csv
swift tools/vision/facebox.swift     stills/ > facebox.csv
python3 tools/vision/build_windows.py   # -> face-safe-windows.json
python3 tools/vision/solve_card.py      # -> card-transforms.json
```

This take needed the **three-mode** gaze classifier (eye-openness alone passed head-pitched-down
reading). `playbooks/gaze-detection.md`.

Two windows are hand-excluded by name in `build_windows.py` with the reason attached, because the
detector and a dense visual check disagreed.

---

## Regenerating

```bash
python3 tools/chunking/plan_chunks.py     # boundaries on word onsets inside >=0.20s gaps
python3 tools/chunking/inject_windows.py  # never hand-type a solved transform
python3 tools/captions/build_captions.py  # + inject_captions.py, + build_srt.py
python3 tools/sfx/sfx.py && python3 tools/sfx/build_bed.py
bash tools/chunking/render_chunks.sh      # cd's into each chunk; sets HF_DE_STALL_MS
bash tools/chunking/assemble.sh           # asserts 6702 frames before concatenating
bash tools/chunking/preview.sh c3 <t0>    # never QA a chunk silent
```

Two asserts worth keeping: the frame total in `assemble.sh` caught a `data-duration` bug that would
have shipped a truncated end card, and comparing render mtime against `index.html` mtime catches
the CWD bug that silently assembles a stale film.
