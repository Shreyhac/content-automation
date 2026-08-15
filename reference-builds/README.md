# Reference builds

Eight shipped compositions, **code only**. Each carries an `ASSETS.md` naming every media file it
expected, where that file came from, and how to regenerate it.

They are here to be read and scaffolded from, not to be re-rendered as-is. Re-rendering one means
re-fetching or re-shooting its media, which the manifest tells you how to do.

| Build | Creator | What it demonstrates |
|---|---|---|
| `shreyansh-vid67/` | shreyansh | **Current shreyansh grammar.** A reference reel copied shot for shot on his own A-roll, re-timed word by word. First build with a pre-render gate script and a beat contact sheet, and a chunked render of a short. |
| `nader-vid62-short/` | Nader | **Current Nader vertical.** Nine beats cut from a long-form with no new recording. Split and card states off one camera, and the card collapsing inside its own rect. |
| `demi-demi2/` | Demi | **The new client.** The only composition authored as ONE file and chunked afterwards. Its chunking scripts are the artefact. Voice plus music, zero SFX. |
| `gaurav-vid50/` | gaurav | **Current gaurav grammar.** The paper split as it settled, and the build where the hook was already in the footage: the lid shuts by frame 22 and the title lands on it. His supplied `saas` SFX pack across 28 placements. |
| `gaurav-vid47/` | gaurav | The paper split band. One accordion carrying ten items. Two moves per beat tied to specific words. three.js re-lit for a paper world. |
| `nader-vid46-short/` | Nader | A 9:16 short derived from a finished long-form. Frame-defined timeline, baked crops, complete-sentence excerpting, the floating face card as a move. |
| `nader-vid46-longform/` | Nader | The chunked 16:9 architecture: shared `base.css` and `chunk.js`, the recurring three.js field, one specimen chunk. |
| `shreyansh-vid42/` | shreyansh | The floating card, three.js as a recurring object, machine-event scene grammar, stock footage as a ground layer. Superseded by vid67 as the shreyansh reference. |

Watch the shipped result first: `reference-cuts/` holds a 720p proxy of each.

Three of these render in **chunks** rather than in one pass (`shreyansh-vid67`, `demi-demi2`,
`nader-vid46-longform`). In each, the whole-film `index.html` is the readable source of truth and
the per-chunk documents are what actually rendered. Each manifest says which file is which, and
why.

---

## Scaffolding a new video from one

Start from the current build for that creator, not from vid42.

```bash
cp -R reference-builds/shreyansh-vid67 work/vid68
cd work/vid68
mkdir -p assets/fonts assets/sfx
cp ../../library/fonts/{inter-400,inter-600,inter-800,fraunces-italic,Gaegu-400,Gaegu-700}.woff2 assets/fonts/
# then gut the scene content, keep the systems: the two-state face machine, the
# caption engine, guard67.py and shoot67.py
```

`library/fonts/` now also carries **Gaegu** (`Gaegu-400`, `Gaegu-700`), which every shreyansh build
from hf63 onward loads, and **IBM Plex** (`IBMPlexSans-VF.woff2`, `IBMPlexMono-Regular.ttf`,
`IBMPlexMono-Medium.ttf`), which is Demi's body and mono stack.

`SeasonMixUprightsVF.woff2`, Demi's display face, is **not** in `library/fonts/` and never will be:
it is a paid client licence. A Demi rebuild falls back to a system serif silently, with no error
and no gate firing. See `demi-demi2/ASSETS.md`.

For Nader, scaffold from `nader-vid62-short/` for a vertical and `nader-vid46-longform/` for a
16:9. For gaurav, `gaurav-vid47/`.

**Order matters: scaffold first, then transcode the A-roll in.** Copying a donor project on top of
a directory where ffmpeg is writing has silently replaced a fresh transcode with the donor's
A-roll. Verify the A-roll's duration after any copy step.

**A scaffold inherits the last film's device kit.** Whatever is in the donor's `base.css`, its font
folder and its SFX folder arrives with it. vid67's `assets/fonts/` carried 22 files and the
composition declares 3. Prune deliberately rather than shipping a donor's leftovers.

---

## What is deliberately not here

- Raw and transcoded A-roll, b-roll, VO masters.
- Screenshots, logo files and brand marks.
- Renders and QA frame dumps.
- Fonts of any kind. Open faces live in `library/fonts/`; licensed ones must be obtained.
- Per-video SFX subsets (the source pools are in `library/sfx/`; each manifest lists which cues the
  build used).

The original working repo still holds all of it if a specific file is ever needed again, except
where a manifest says otherwise. Two things named in these manifests are gone or unreachable:
vid62's `master.mov` was deleted, and several A-roll and B-roll masters live on an external drive
that has to be mounted.
