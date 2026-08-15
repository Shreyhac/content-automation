# Demi (demi.ai)

**Agency client, not a personal channel, and not a creator at all: Demi is a product.** A
proactive AI teammate that ships as a **macOS app**. It surfaces your to-dos with the draft
already written and never sends anything without your approval. Positioning, from their own
site: *"Half your job is the work. The other half is keeping up with it. Demi takes that half."*
Named competitors: Viktor, Town, and Claude Tag.

The cuts are **paid Meta placements**, not organic feed posts. That is the single fact that
sets the pacing, the endcard and the error bar.

| | |
|---|---|
| Primary format | 9:16 vertical Meta ad, 36 to 44 seconds |
| Shipped | Demi UGC reel (`hfdemi/`, 1080x1920, 41.4s), demi2 "six tools" (`hfdemi2/`, 2160x3840, 37.77s) |
| Current state | demi2 **v20 delivered 2026-08-14**, awaiting the owner's verdict on what he called his last attempt round. Local review only, never sent to the client |
| Presenter | Two different ones. Video 1 is an AI avatar of a woman with a cloned voice. demi2 is a real male A-roll, one manual cut supplied by the owner, 34.03s, 2160x3840 HEVC 32.9 Mbps |
| Brand contacts | `gauravdemi` and `Prakhar Keshar` comment in their Figma. The ads Figma is a live production file, read its comments before building |

---

## The assets, and where they live

All of it is in `demi/` in the production repo (169 MB, the 71 MB product demo is gitignored).
`demi/INDEX.md` is the file map, `demi/DEMI-DEEP-DIVE.md` is the write-up.

| Path | What it is |
|---|---|
| `demi/brand-assets/` | The official marks as SVG: symbol, wordmark, primary lockup, and all 12 function icons, black and white. The brand team maintains these. Use them, not the website's SVGs |
| `demi/figma/brandbook-frames/` | Lightweight Guidelines V1.0, all 46 spreads at 1920x1080. Palette p18, combinations p19, gradient p21 to 22, icon suite p28, process illustration p29 |
| `demi/figma/recovered-lowopacity/` | Pages 36, 37, 39, 40, 41 sit at about 4% opacity in the source file and export flat grey. These are levels-stretched recoveries, accurate in layout and colour, banded. Includes the **vertical social templates** (37) |
| `demi/BRAND-COLORS.md`, `demi-tokens.css`, `demi-tokens.json` | The palette with pairing rules and the gradient spec, paste-ready |
| `demi/ui-real/`, `demi/ui-components/` | The client's own product screenshots and component exports, light and dark |
| `demi/site/integrations/logos/` | All 28 integration logos as SVG (Gmail, Slack, HubSpot, Salesforce, Notion, Linear, Zoom, Granola, Gong and the rest) |
| `demi/site/fonts/` | IBM Plex Sans variable and italic (TTF), plus the site's Season Mix Uprights VF woff2 |
| `demi/outro/9_16-outro-cta.png` | The client's endcard plate, split for animation into `cta-plate` / `cta-lockup` / `cta-tag` in `hfdemi/assets/ui/` |
| `demi/orb-lab/` | Their `demi-orb-motion-lab`, cloned. The product's signature motion |
| `demi/ads/` | 27 live Meta creatives, two personas by three formats, plus the Instagram carousel redesign |

### Fonts and licensing

Demi's brand faces are **IBM Plex** (Sans variable, Mono Regular and Medium) plus the display
face **SeasonMixUprightsVF.woff2**.

- **The IBM Plex faces ship with this repo**, in `library/fonts/`. They are open, and they are
  what both films actually rendered on.
- **Season Mix is a paid licence held by the client, so it is deliberately NOT in this repo.** A
  Demi rebuild that calls for it will silently fall back to another face and look wrong until
  someone copies it in from the client's own brand package. The woff2 sitting in the production
  repo's `demi/site/fonts/` is the site's own webfont, fine as a reference, not a licence to ship.
  Either license it, or substitute a high-contrast transitional serif and flag the swap.
- **A missing face falls back silently**, with no error from any gate. Verify glyphs at **native
  resolution**, never from a downscaled QA crop: Plex Sans's serifed capital "I" disappears when
  a 2160-wide caption crop is scaled down into a comparison image, and that false negative cost a
  full round on demi2. The renderer's own compile log is the ground truth.

---

## Hard rules

### 1. The client's own icon system, exports and marks beat anything reconstructed

Demi's brand book builds every icon from five layered elliptical stages, *Observe, Think,
Prepare, Decide, Advance*, and states the structure means Demi works alongside you "with you
always in control of the final action". That is the script's argument already drawn: **a
dictation app is one ring, Demi is five.** Both graphics beats of video 1 became the same object
in two states. **When a client has a real brand book, read the iconography page before inventing
a device.** The argument may already be in their geometry.

The same holds for their PNG exports. `demi-macos-active-task__dark.png` cropped to its window
bounds is sharper than a rebuild and is what "show the actual UI" means when the element only has
to sit there. **Rebuild in HTML only what must animate.** Detect the window bounds by colour, do
not eyeball them: the first crop carried 48px of black.

**Two counter-conditions, both learned the hard way:**

- **Never composite `demi/ui-real/` PNGs raw.** They carry his personal data in task names.
  Rebuild those in HTML from the export as reference.
- **A real UI pasted onto a generated plate is optional, not a rule.** On a *background* plate
  whose screen is never the subject, a soft out-of-focus screen is more believable than a
  pixel-perfect pasted one. Ask which the screen is: subject, or texture.

### 2. The site palette is NOT the brand palette

`demi.ai` ships a **blue-only reduction**. The stylesheet still carries `--color-pink-*` and
`--color-orange-*` token names and aliases every one of them to blue, plus two site-only accents
(`--color-plum #9B4258`, `--color-violet #8D7DF5`) that are not in the brand book at all.
**Matching the website will not match the brand.** Video and social work uses the full brand-book
palette. Exact values in GRAMMAR.md.

His round-1 note on demi2 was *"is the theme matching with demi theme?"* and the honest answer was
that the navy already WAS their Foresight Blue shade. The real fault was flat gradient voids, not
the hue. See GRAMMAR.md: **no graphic sits on bare colour on this account.**

### 3. AI-generated music is rejected on sight. Use a real licensed track

An ElevenLabs Music bed was generated, tempo-matched and sidechain-ducked carefully to the cut's
beat grid, then rejected outright: *"too shitty music bro, eww"*, followed by *"can't you find one
pre-existing non-copyright music"*. The objection was that it was AI-generated at all, not the mix.

Both films now run **Mixkit `gear`**. Source two or three real candidates, build each into a
full preview of the actual cut so the choice is made in context, and audition them on a share
link (that is what `review/data/demi2-music-audition/` was).

### 4. Sub-1.5s mean shot, and the density comes from static crop-cuts

*"i really want this a fast paced edit for meta ads, plz make a note of it."* Said after a first
plan came in at a 2.28s mean shot modelled on the Wispr Flow reference ads. **The reference ads
set the grammar, not the tempo.**

demi2's plan landed at **42 shots over 36.2s, 0.86s mean, 1.46s longest.**

Every punch-in is a **pre-rendered static crop of the 4K master, hard-cut to.** A cut to a
tighter framing is not a camera move, so this hits the density without ever animating a scale on
a `<video>` wrapper (which reads as a zoom and deadlocks the capture engine). Cropping 1.25x from
2160x3840 still leaves 1728x3072 before the composition's own 2x scale, so it costs nothing in
sharpness.

**Two carve-outs where speed loses to comprehension**, deliberately the slowest shots in the cut:

- any beat where the viewer must **read** product UI (result cards, the typed composer sentence)
  gets 0.9 to 1.3s;
- the **direct-ask / CTA line stays on the presenter's face**, clean, nothing over him.

The tempo also has an upper bound found in round 6: block E was cut from 7 shots to **3 held
shots** on *"let the b-roll breathe"*, and v17 confirmed **two long b-roll holds beat three
medium ones**. Drop a shot rather than compress three.

### 5. Approve the still frame, then the clip, then render

Triggered when a full composition shipped in a format that diverged from the reference he had
sent: *"none, I will give you the frames you dumbfuck."* The standing sequence for this client:

1. Generate the still frame or mock (GPT Image for anything AI-drawn, a Playwright screenshot for
   anything hand-built).
2. Share it and **stop**. No video generation on an unapproved frame.
3. Generate the short clip from that exact approved frame.
4. Share the clip and **stop again** before compositing it into the timeline.
5. Only then assemble, render and share.

Each of those steps costs real time and, for generation, real money. Skipping the gate once
already burned a full render cycle here.

### 6. No branded hub, and no product-shaped tile, before the product reveal

*"we haven't revealed Demi yet."* A graph beat that put a branded hub at the centre of its
connections was rejected, and so is a "?" tile in that position, because a tile in the hub slot
reads as product-shaped whatever is drawn on it. **Graph beats before the reveal are plain
interconnecting lines only.**

The persistent product pill died the same round for the sibling reason: over b-roll that already
shows the product's own site, a brand pill is redundant clutter.

### 7. The b-roll carries the client's brand, so it cannot play the problem half of the script

Every demi2 b-roll clip is the same desk with demi.ai already on the monitor. The shot plan
documented this on day one, a team note asked for that footage under the problem beats anyway,
and the client's own reviewer then flagged the contradiction: *"how can this screen have Demi's
b-roll?"* **When a footage constraint and a note collide, surface the constraint in the reply
rather than silently complying.** The blurred variant, content unreadable, is the compromise that
survives. Problem beats stay on the presenter with graphics.

### 8. Zero added sound effects on this account until asked otherwise

demi2 shipped voice plus music only. **"Remove the typing sfx" meant every added sound, not a
subset.** Three consecutive rounds each removed a plausible offender by measurement (the
click/tick family, then the music's own metronomic 0.465s tick grid, then the click-attack reveal
cues) and he kept hearing it, because the surviving whoosh and impact cues were still added
sound. Round 5's five timestamped notes landed exactly on those five cues.

Do not add an SFX cue back to a Demi project without asking first whether he wants sound design
at all. **The client's own outro clip's audio is not an added cue**: it goes into the bed at its
picture window at unity and the music fades underneath.

---

## Delivery

- demi2: **2160x3840, 30fps**, bitrate pinned at **40 Mbps minimum** so the master's 32.9 Mbps is
  never the ceiling. Delivered around 92 to 96 Mbps depending on the cut. Verify with ffprobe
  before handing over.
- Video 1: 1080x1920, 30fps.
- **The A-roll audio is stream-copied bit for bit.** No denoise, no EQ, no loudnorm. No grade on
  the picture either.
- Music level as delivered: about -13.9 dB at t=0 on demi2, -13.9 LUFS integrated on video 1.
- **No comment CTA on these**, so no `.docx` deliverable. The CTA is a Download for Mac pill and
  the client's own outro plate.
- No em dashes.

---

## How he reviews

**Fast, in bursts, and in many short rounds.** demi2 went from v1 to v20 inside about 20 hours
across ten review rounds. Notes are usually one line, frame-pinned, often with a box drawn on the
frame. Budget for the round count, not for the round size.

- **A markup box drawn over the presenter's own face is placement approval.** One note's box
  spanned his chin. He had already priced in the overlap, so honouring the drawn geometry beat
  re-deriving a safer placement nobody asked for.
- **Mark every addressed note `resolved` with a `reply` and push BEFORE sharing the next render.**
  A render went out once without this, and the client's next open of the link showed all 12 prior
  notes still flagged open, reasonably read as "my feedback was ignored". The order is
  fix, reply, push, then share.
- **He reverses himself, and that is normal here.** He asked for floating tool logos over blurred
  b-roll on the hook in one round and reverted it himself the next. The split-screen device was
  flipped four times before it settled.
- **When a complaint survives an evidence-based fix twice, stop refining the classifier and remove
  the whole category.** One question in round 2 ("should ALL added sounds go, or just the clicky
  ones?") would have saved three rounds.

**Two review surfaces, and they are not the same audience.** The owner reviews locally through
`./rr`. The demi.ai side reviewed video 1 through the hosted share link, and 45 of that project's
57 notes arrived as `source: "client"`. demi2 has never gone to the client at all.
