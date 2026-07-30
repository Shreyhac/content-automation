# Reference builds

Four shipped compositions, **code only**. Each carries an `ASSETS.md` naming every media file it
expected, where that file came from, and how to regenerate it.

They are here to be read and scaffolded from, not to be re-rendered as-is. Re-rendering one means
re-fetching or re-shooting its media, which the manifest tells you how to do.

| Build | Creator | What it demonstrates |
|---|---|---|
| `gaurav-vid47/` | gaurav | The paper split band. One accordion carrying ten items. Two moves per beat tied to specific words. three.js re-lit for a paper world. |
| `nader-vid46-short/` | Nader | A 9:16 short derived from a finished long-form. Frame-defined timeline, baked crops, complete-sentence excerpting, the floating face card as a move. |
| `nader-vid46-longform/` | Nader | The chunked 16:9 architecture: shared `base.css` and `chunk.js`, the recurring three.js field, one specimen chunk. |
| `shreyansh-vid42/` | shreyansh | The floating card, three.js as a recurring object, machine-event scene grammar, stock footage as a ground layer. |

Watch the shipped result first: `reference-cuts/` holds a 720p proxy of each.

---

## Scaffolding a new video from one

```bash
cp -R reference-builds/gaurav-vid47 work/vid48
cd work/vid48
mkdir -p assets/fonts assets/sfx
cp ../../library/fonts/{clash-600,clash-700,satoshi-500,satoshi-700,satoshi-900,geist-mono}.woff2 assets/fonts/
cp ../../library/vendor/three.min.js assets/
# then gut the scene content, keep the systems
```

**Order matters: scaffold first, then transcode the A-roll in.** Copying a donor project on top of
a directory where ffmpeg is writing has silently replaced a fresh transcode with the donor's
A-roll. Verify the A-roll's duration after any copy step.

---

## What is deliberately not here

- Raw and transcoded A-roll, b-roll, VO masters.
- Screenshots, logo files and brand marks.
- Renders and QA frame dumps.
- Per-video SFX subsets (the source pools are in `library/sfx/`; each manifest lists which cues the
  build used).

The original working repo still holds all of it if a specific file is ever needed again.
