# vid47 assets manifest

`index.html` references the paths below. None of the media ships in this repo. Shipped result:
`reference-cuts/gaurav-vid47-github-tools.mp4`.

**Video**: 1080x1920, 995 frames, 33.19s. Delivered at -14.5 LUFS / -1.2 dBTP.

---

## A-roll (2 files)

| Path | What | How to regenerate |
|---|---|---|
| `assets/aroll.mp4` | Full-bleed transcode | From the creator's delivered master. Transcode only, no regrade or denoise. |
| `assets/aroll-band.mp4` | The split-band crop | `ffmpeg -i <master> -vf "crop=1854:3296:36:212,scale=1080:1920" -r 30 -c:v libx264 -crf 17 -g 15 -keyint_min 15 -c:a copy assets/aroll-band.mp4` |

That crop gives head 430px, face centred x540.6, crown y1130, chin y1560. **Those constants belong
to that take only.** Re-solve per take: `playbooks/face-geometry.md`.

Shipping two transcodes of one take (cropped for full-bleed, differently cropped for the band) is
cheaper than forcing one geometry to do both jobs.

---

## Fonts (6 used, all in `library/fonts/`)

```
clash-600  clash-700  satoshi-500  satoshi-700  satoshi-900  geist-mono
instrument-serif-italic-400-it        (the rationed second voice)
```

```bash
mkdir -p assets/fonts && cp ../../library/fonts/{clash-600,clash-700,satoshi-500,satoshi-700,satoshi-900,geist-mono,instrument-serif-italic-400-it}.woff2 assets/fonts/
```

---

## Logo tiles, `assets/logo/` (10 files)

The ten tools' brand marks, rendered on the paper card colour.

| Source | Marks |
|---|---|
| Simple Icons, ink-tinted: `cdn.simpleicons.org/<slug>/101014` | coolify, dify, langflow, supabase (svg) |
| The project's own published SVG, with `fill="white"` rewritten to ink | openhands |
| Project README or site, icon cropped out of a horizontal lockup (`crop=H:H:0:0`) | browseruse, crawl4ai (png) |
| Project README or site | maxun, openwebui, stirling (png) |

**Light and white marks vanish on paper.** Coolify, Langflow and OpenHands all shipped as blank
tiles on the first render. **Verify by rendering all ten on the actual card colour in one headless
page before wiring them in.** See `playbooks/real-assets.md`.

**A wordmark is not a logo tile.** Browser Use and Crawl4AI ship horizontal lockups; without the
crop a 92px tile shows three letters.

---

## Product screenshots, `assets/ui/` (10 files)

One real interface per tool, **cropped at 560x300 (1.867:1)** to match the accordion row plate.

Two sources:

1. **The maintainers' own README hero images**, which are the fastest real product surfaces there
   are: `api.github.com/repos/<owner>/<repo>/readme`, base64, regex the image URLs.
2. **Live Playwright captures** at `device_scale_factor=2` (`tools/qa/playwright-capture.py`).

**Crop from the 2x capture, never downscale the whole page.** A 1440-wide viewport shot at 820px
display is 0.5x and its text is 7px; a roughly 1300px-wide *detail* of the 2x capture displays at
about 1.3x CSS and is readable at reel scale.

**The card size drives the crop, not the other way round.** Three of the ten needed two extra
passes: a crop that is short on the left shows the *previous* column, and the instinct to move x
the wrong way costs a round each time. Check the sign against the artefact.

---

## SFX, `assets/sfx/` (23 distinct files)

**80% of triggers come from the creator's own supplied pack**, `library/sfx/saas/`. He expects to
hear it. The remaining risers and impacts come from `library/sfx/house/` where the saas library has
no equivalent (`imp2`, `rise2`, `shine1`, `tick3`, `wsh1`, `wsh3`).

Volumes **0.10 to 0.15**. No single cue over 10% share.

The `s1` through `s17` names are the per-beat picks from the saas pack, renamed short. Rebuild with
`tools/sfx/curate_saas_sfx.sh`, which peak-normalises to -3 dBFS and head-trims so `data-volume`
means the same thing everywhere. See `docs/05-audio-and-sfx.md`.

---

## Vendored

| Path | Source |
|---|---|
| `assets/three.min.js` | `library/vendor/three.min.js`. UMD build, **never an ES module**: a module defers and the capture engine reads `window.__timelines` synchronously, producing a dead page. |
| `assets/field.js` | Ships in this build. The three.js field, re-lit for paper: pale ceramic body `0xE6E2D8`, metalness .04, roughness .72, ambient 2.35, state colour on the deep green. |

The canvas is clipped to `inset(150px 0 1010px 0)` permanently so it can never drift onto his face.

---

## The ten repos

All verified through the GitHub API before the plan was written. Total 988,629 stars, which is the
hook's stat. **`All-Hands-AI/OpenHands` now redirects to `OpenHands/OpenHands`** and the on-screen
path must be the current one. Star counts moved 29 in one hour during the build, so re-check
immediately before delivery.

Honesty guard: the real SPDX string is printed for each, and the three source-available tools
(Open WebUI, Stirling PDF, Dify) are labelled `SELF-HOST` rather than "free".
