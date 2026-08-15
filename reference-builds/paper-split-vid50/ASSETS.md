# vid50 assets manifest

**The paper-split client's current grammar.** The paper split band as approved, three review rounds all spent on
the hook, and a build where the hook was already in the footage rather than drawn on top of it.

Shipped result: `reference-cuts/paper-split-vid50-current.mp4`. Measured from the delivered file, not
from the log: **835 frames, 1080x1920, 30fps, 27.866s, 25.61 Mbps**. Sixty timed elements.

Scaffolded on hf47 v2's approved paper split, so read `paper-split-vid47/` alongside this one: v47 is
where the split band was solved, v50 is where it settled. `templates/paper-split/HISTORY.md` walks the
three rounds.

Ships here: `index.html`, `package.json`. The build carried no solver scripts of its own, so
there are none to publish.

---

## A-roll, `assets/aroll-i.mp4` and `assets/aroll-audio.m4a`

A fresh single take, not a cutdown. Video and audio are separate files in this build.

The owner's only direction was *"start from when he closes the lid of the laptop, that is the
hook."* **The hook was already in the footage.** A frame-exact decode of the first 48 frames put
the lid near-vertical at frame 0 and shut by roughly frame 22 (0.73s), with the voiceover starting
at 0.52s. Nothing had to be built: the title lands on the shut, and the physical act carries the
graphic.

The general rule, and the reason this build is worth reading: **when an owner points at a moment
in the take, decode that range at full rate before designing anything.** The alternative is
drawing an entrance for a beat the footage already performs.

Re-solve the face constants for any new take. hf41 to hf47 established that the constants never
travel, and vid50 added the harder case where the head itself sits differently. See
`playbooks/face-geometry.md` and `playbooks/paper-split-band.md`.

---

## SFX, `assets/sfx/` (28 placements)

This build is the clearest example of the client's own supplied pack in use. The `s1` through `s17`
files are the client's `saas` pack, which ships in this repo at `library/sfx/saas/` and which **the
client expects to hear**. The `imp`, `rise`, `wsh`, `shine` files are the house pack at `library/sfx/house/`.

Curate with `tools/sfx/curate_saas_sfx.sh`, which peak-normalises to -3 dBFS and trims the head so
`data-volume` means the same thing across both pools. Audit the bed by **share**, not by file
count: cap any single file at about 8.5% of placements. See `docs/05-audio-and-sfx.md`.

---

## Fonts

All nine ship in `library/fonts/`, so this build needs no external face:

```
clash-600  clash-700  satoshi-500  satoshi-700  satoshi-900
geist-mono  space-grotesk-500  space-grotesk-700
instrument-serif-italic-400-it
```

```bash
cp -R reference-builds/paper-split-vid50 work/vidNN
cd work/vidNN && mkdir -p assets/fonts assets/sfx
cp ../../library/fonts/{clash-600,clash-700,satoshi-500,satoshi-700,satoshi-900,geist-mono,space-grotesk-500,space-grotesk-700,instrument-serif-italic-400-it}.woff2 assets/fonts/
```

---

## Where the media lives

The delivered final and the project were archived off the working repo on 2026-08-13 and live at
`/Volumes/EXTERNAL/Reel-Factory-Archive/archive-2026-08-13/`, `projects/hf50/` and
`out-finals/vid50-final.mp4`. Verified present and readable on 2026-08-15, which is where the
frame count and bitrate above were measured.

The A-roll master is the creator's own recording and is not in the archive under this project. Treat the
A-roll as unrecoverable for a re-render: this build is here to be read and scaffolded from, not
re-rendered as-is.
