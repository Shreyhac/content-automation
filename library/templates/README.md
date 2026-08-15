# Templates

`vertical-reel/` is a 1080x1920 skeleton (2160x3840 output) carrying the CURRENT grammar.
Its parent is `reference-builds/card-reel-vid67/`, the newest delivered card-reel build, and
it was rewritten off that file: the vid42-generation template it replaces was three theme
generations stale.

## What it carries

| | |
|---|---|
| `index.html` | the composition skeleton |
| `package.json` | `dev`, `check`, `derive`, `gate`, `sheet`, `render` |
| `guard.json` | a real stub written by `tools/gates/derive_config.py` against this template |

Inside `index.html`, as working code rather than as advice:

- **the face `cut()` system**, two states (`split`, `full`), hard cuts, never a tween, with
  the clip-path SET and the camera pushed so the chin clears the y1600 band.
- **the caption engine**: one phrase bar per cue, `tl.call()` to write the text, and
  `window.__CAPS = CAPS;`. That one line is not optional. Gates and contact sheets seek with
  `suppressEvents`, so a `tl.call()` never fires for them: without the published array the
  caption element carries no text for every probe and the crown, band, rail, text-on-text
  and contrast rules all measure nothing while printing PASS.
- **the entrance conventions**: `fromTo` and never `from`, staged elements `opacity:0` in
  CSS, a 0.20s lead so the entrance finishes under the transition, `put()` writing anything
  inside the first half frame immediately so frame 0 is a composed cover.
- **the SFX bed hook**: the `<audio>` VO track plus the injection markers
  `tools/sfx/build_bed.py` writes between.
- **the one always-on graphics track**, windowed to the whole film, because a `<video>`
  painted outside its own `[data-start, +data-duration]` window renders dead grey and
  seventeen windowed tracks stalled the capture engine outright.
- **the safe-zone guides**, the one global ground stack, and the stage-space geometry.

## What you still have to supply

Everything that is a measurement or a file. The template deliberately contains **zero media**.

1. **Assets.** `assets/aroll.mp4`, `assets/bandtrack.mp4`, `assets/vo.mp4`, the SFX, and the
   faces this build needs copied from `library/fonts/` into `assets/fonts/`. Transcode the
   A-roll at the MASTER's own resolution: a 1080x1920 asset is upscaled back to 4K and
   delivers 52% of the master's detail against 95% from a 2160x3840 one.
2. **Every `REPLACE` marker.** Palette, duration, the beat map `B`, the seam, the camera
   push, the caption offsets, the CTA copy.
3. **The face geometry**, from a Vision measurement of this take (`tools/vision/`,
   `playbooks/face-geometry.md`), not from a layout instinct.
4. **The `guard.json` TODOs.** Regenerate first, then work them.
5. **The delivery bitrate.** `npm run render` carries a placeholder `16M`. Bitrate is a
   function of the source: measure the master and verify the delivered file with `ffprobe`,
   because one film shipped at correct resolution and half its master's bitrate.

## Using it

```bash
cp -R library/templates/vertical-reel work/vid68
cd work/vid68
cp ../../library/fonts/<the faces this build needs>.woff2 assets/fonts/
npm run check      # lint, validate, inspect
npm run derive     # rewrite guard.json from the composition you have now
npm run gate       # guard.py, exits 2 until every TODO is resolved
npm run sheet      # the beat contact sheet, read it as images
```

The `derive`, `gate` and `sheet` scripts use `../../tools/...`, so they assume the copy sits
one level inside this repo, as `work/<film>/`. Fix the paths if it lives anywhere else.

## When to use it, and when not

**For real work, prefer scaffolding from `reference-builds/`.** Those carry the proven
systems whole: the chunk architecture, the accordion, the recurring 3D object, a real shot
list. The template carries the grammar and no film. Use it when the build genuinely fits no
existing reference, or when you want the house rules in one readable file.
