# Library

Shared assets. Everything here is licensed for commercial use or vendored deliberately.

---

## `fonts/` (24 faces)

Deduped across the whole portfolio, newest project wins. Copy the ones a build needs into its
`assets/fonts/` rather than referencing across directories, so a project stays self-contained.

| Family | Files | Used by |
|---|---|---|
| Clash Display | `clash-600`, `clash-700` | gaurav (display), shreyansh (display) |
| Satoshi | `satoshi-500/700/900` | gaurav, shreyansh (body and captions) |
| Rethink Sans | `rethink-sans-var` | Nader (display and all numbers) |
| DM Sans | `dm-sans-var` | Nader (captions and body) |
| Geist Mono | `geist-mono` | all three (labels, mono) |
| Fraunces | `fraunces-normal/black/italic`, `fraunces-var-a/b` | Nader (rationed second voice), the paper listicle family |
| Instrument Serif | `instrument-serif-italic-400-it` | rationed second voice |
| Instrument Sans | `instrument-sans` | |
| Inter | `inter-400/600/800` | tech-launch subjects |
| Poppins | `poppins-500/600/700/800` | the older paper listicle family |
| Space Grotesk | `space-grotesk-500/700` | music and audio subjects |

Geist Mono advances **0.609em**, not 0.600, and `letter-spacing` on the same element silently adds
to it. That matters whenever you size a typewriter or a mono field against a container.

Eleven hash-named woff2 files from the earliest projects were dropped: only two were referenced
anywhere and both duplicated named faces already here.

---

## `sfx/`

**Audit a bed by SHARE, not by file count.** Cap any single file at about 8.5% of placements,
enforced per chunk. Full method in `docs/05-audio-and-sfx.md`.

### `sfx/house/` (96 files)

The licensed house pack. Subfolders: `Click/` (UI and keyboard), `Wooshes/`, `rizer/` (risers),
`soft-kit/` (26 files curated for paper worlds: felt pops, paper slides, soft clicks, gentle
confirms, air whooshes, one marimba).

Look here **before** the internet. Most of it is still uncurated.

### `sfx/saas/` (17 files)

gaurav's own supplied pack. **He expects to hear it**: 80% of triggers on one film, 55% on another.
Fold a supplied pack in by class-matched substitution, taking over existing cues from the
most-repeated file in the same class, never by inventing new beats.

Half of it arrived named "sfx 4.mp3". Classify by measurement, not filename: low-dominant with fast
decay is an impact, high-dominant with fast decay is a click, a rising envelope is a riser, flat
across more than 1.5s is a sustained texture.

### Curating for a build

`tools/sfx/curate_sfx.sh` and `curate_saas_sfx.sh` peak-normalise to -3 dBFS and trim the head, so
`data-volume` means the same thing everywhere. Library files arrive at wildly different levels and
several carry 20 to 80ms of digital black, which lands the transient late against its word.

**Check for byte-identical duplicates.** One "17 SFX" bed was really 15.

---

## `vendor/`

`three.min.js`, UMD build.

**Vendored deliberately, and never as an ES module.** Two reasons, both fatal otherwise: a second
CDN request is exactly what killed one render (the script died before `window.__timelines`
registered, and lint, validate and render all reported success on a page of static DOM); and a
module script defers, while the capture engine reads `window.__timelines` synchronously after load.

r150 and r160 are the last UMD releases. They log a deprecation warning; harmless.

---

## `templates/`

Starter scaffolds. For real work, prefer copying a build from `reference-builds/`: it carries the
proven systems, and the template only carries the skeleton.
