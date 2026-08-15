# vid46-short assets manifest

A 9:16 short derived from a finished 16:9 long-form. **Nothing was re-transcribed, re-graded or
re-recorded**: every asset is cut or baked from the film's own material.

Shipped result: `reference-cuts/longform-chunked-vid46-incogni-short.mp4` (45.000s, 1350 frames, two chunks).

Method and traps: `playbooks/short-from-longform.md`.

---

## The single source of truth

`beats.py` holds 12 beats, each with its source segments and frame count. The VO splice, the baked
crops, the captions, the SRT and both chunks' HTML all read it. **The timeline is defined in
frames, never seconds**, so audio and video cannot drift (17ms slack per beat, zero cumulative),
and `assemble.sh` asserts the 1350-frame total before it will concatenate.

`segments.json` and `short-transforms.json` are the solved outputs. `words.json` is the film's word
stream, carried over unchanged.

---

## A-roll, `assets/aroll/` (a1, a3, a5)

**Baked crops, not CSS transforms.** Each beat gets a clip already at its final size, so the
browser never resamples the A-roll and the solved geometry exists in exactly one place.

```bash
python3 solve_short.py      # solves geometry from the film's crown.csv / facebox.csv
python3 bake_clips.py       # ffmpeg + lanczos, one clip per face block
```

Two things the solver enforces:

- **One bake at HERO size**, with the card as a CSS transform of those pixels. You cannot tween
  between two files, and the hero/card move is what the owner asked for by name.
- **A continuous source range per face clip, never a concatenation.** A pause dropped inside a face
  block is a jump cut on a talking head.

Where a window ends a few frames early, `tpad=stop_mode=clone` holds the last good frame.

Solved card for this head: **560x736 at x260 to x820, y838 to y1574** (chin y1407 to 1481, worst
1545). **Do not copy these numbers.** See `playbooks/face-card-device.md`.

---

## VO, `assets/vo.wav`

Spliced from the film's own cleaned master by `build_vo.py`, on **complete sentence bounds**.

- Ten complete sentences, asserted against the film's 41-sentence list. Never a fragment.
- Beat ends run to the **measured `volumedetect` dip**, not to whisper's sentence mark, which
  undershoots (a word marked ending at 68.92 was still decaying at -28 dB until 69.24). Across ten
  sentences that cost 2.1s.
- Joins: 25ms fades. Of nine joins, seven had real silence after the sentence and could simply
  extend into it; only two needed room tone lifted from elsewhere in the master.

---

## B-roll, `assets/broll/` (3 clips)

Three of the film's own already-graded clips, re-cut. Each cuts in **on a word**:

| Clip | Under the line |
|---|---|
| `b3-aisle.mp4` | "data broker websites and private databases" |
| `b6-bundle.mp4` | the competitor's bundle |
| `b7-pricing.mp4` | a card being handed over, cutting in on "twice" |

Always carded, never full-bleed. A b-roll that merely sits there is wallpaper.

---

## Brand marks, `assets/brand/` (3 svg)

Real vectors with their fills rewritten to white. **Do not apply `brightness(0) invert(1)` to a
Playwright element screenshot**: those are RGB with no alpha unless `omit_background=True`, and a
page rendered onto a white body never has it. Both marks shipped the first render as solid white
boxes.

---

## Fonts (4, all in `library/fonts/`)

```
rethink-sans-var    display and all numbers
dm-sans-var         captions and body
geist-mono          labels
fraunces-italic     the rationed second voice
```

**`@font-face` must be declared inline in every chunk**, not only in `base.css`. The static guard
only resolves faces it can see in the document and otherwise silently falls back in the render.

---

## SFX, `assets/sfx/` (~35 cues)

Drawn from `library/sfx/house/` and the creator's supplied pack. `sfx.py` is the single source of
truth and **enforces** the share cap, the median, the ceiling and the retired list.

Volumes for this creator after three rounds: **median 0.060, ceiling 0.096, bed 0.055.** He halves
it every time he says "loud". See `docs/05-audio-and-sfx.md`.

---

## Vendored and shared

| Path | Note |
|---|---|
| `assets/three.min.js` | From `library/vendor/`. UMD only. |
| `assets/field.js` | The recurring plate field, carried from the long-form. **Its px constants were re-derived, not scaled**: pixels-per-unit is `H/VIS_H`, so 2160 to 1920 makes every px constant 12.5% larger in a frame a third as wide. The film's 25-column wall gave a 33px pitch against a 52px plate and rendered as a barcode of horizontal stripes. |
| `assets/base.css`, `assets/chunk.js` | Shared foundation, carried from the long-form. |

---

## Regenerating

```bash
python3 solve_short.py        # geometry from the film's measurement CSVs
python3 build_vo.py           # sentence-bounded VO splice
python3 bake_clips.py         # baked A-roll crops
python3 build_captions.py     # captions + SRT from beats.py
python3 sfx.py                # the bed, enforcing the caps
bash render.sh                # HF_DE_STALL_MS is set inside
bash assemble.sh              # asserts 1350 frames before concatenating
```

The film's own `crown.csv`, `facebox.csv` and `words.json` are the inputs. They live with the
long-form working material in the original repo.
