# gaurav: shipped work and what each round changed

Newest first. **The most recent approved grammar supersedes older entries.** He has reversed
himself several times; entries are dated so you can tell law from a round-scoped correction.

---

## vid47, "10 free GitHub tools" (2026-07-30)

33.19s, 995 frames. Eight render rounds across two structures. No reference video.

### v1: REJECTED on look

Built on a three-band grammar with a GitHub-dark palette. His note, with a reference frame from
hf41:

> "We need the split-screen template like this. The colour seems very off and too coded, think of
> premium colours and premium fonts. We need to show the face more. The animations look good, the
> off-the-blocks animation doesn't sync up with the exact thing that we have been trying to say."

Three findings, all of which generalise:

1. **A dark IDE palette for a developer-tools subject reads as "coded", not premium.** Paper is
   the distance that makes it feel made.
2. **Synchronised is not simultaneous.** Two moves per beat, each on a specific word.
3. "Show the face more" is answered by the band top, not by more face beats.

What survived from v1 into v2: the 0.20s scene lead rule, the exact-frame QA method, the
real-asset method, and the three.js findings.

### v2: the paper split band

Ported hf41's Director's Desk wholesale because he had already approved it. Band top y1080,
face presence 45% to 91%. Ten tools as one accordion for 24.5s.

Cost a render round: **light and white brand marks vanish on paper.** Coolify, Langflow and
OpenHands shipped as blank tiles.

Other lessons: a paper wipe on a paper ground is an invisible cut. A card size drives the crop,
not the other way round, and a crop short on the left shows the previous column (check the sign
against the artefact). Absolutely-positioned siblings take no flow space.

**Stock footage was declined with the reason stated**: all ten beats already carry the tool's own
live interface, and generic tech b-roll under a beat with a real product surface is the same
failure as an earlier reel's borrowed rocket tiles. Offering the one honest place for it and
waiting beats assuming.

**Delivery**: this is the video where the file-size rule was set. See `docs/06-delivery.md`.

---

## vid43, Musk's AI U-turn (2026-07-28)

First three.js build in the repo. Three owner rounds landed on the **three-band layout**, which
is the answer to "text on my face" and "I want to be visible" at the same time:

```
TOP     y150 to y640    graphics, rebuilt posts, b-roll cards
MIDDLE  y700 to y1380   the A-roll, windowed and UNGRADED, nothing ever laid over it
BOTTOM  y1410           captions, on the dark bed below the window
```

**Don't move the text, move the face.** Every overlay landing on the presenter traces to a
full-bleed A-roll whose head occupies the band the type wants. Once the face has its own window
the scrim can be deleted entirely and he reads at full brightness.

Also: an abstract 3D glyph reads as a mistake, a 3D glyph carrying a real subject reads as an
idea. Putting his actual face on the U-turn track made the same geometry instantly legible.

Two failed passes on a decorative element means cut it, not tune it.

---

## vid41, HeyGen companion mode (2026-07-28)

First paper-world build for him. Source of the Director's Desk system that vid47 v2 ports.

- **The feature a VO names may live one layer down.** Nothing called "companion mode" existed on
  any marketing page; it is a HyperFrames run-shape documented only in the product's own repo
  skill files. Code-search the repo before concluding a claim is false.
- **A masthead BAR is the reliable way to put type behind a person on light footage.** Green type
  over his white wall was invisible and a scrim could not fix it, because the same line also
  crosses dark framed artwork. A solid ink bar with knocked-out type makes contrast independent
  of what is behind.
- **But text-behind-person needs a gap wider than the head at that y.** The bar at y528 put the
  word across his crown and it was half-eaten by hair. On a seated take with headroom, move the
  lockup into the headroom instead of restyling it.
- **Ship two transcodes of a wide-composed A-roll**: cropped for full-bleed beats, uncropped for
  the bottom band. Cheaper than forcing one geometry to do both jobs.
- **Never borrow a demo's SUBJECT as filler.** Storyboard tiles taken from the vendor's own launch
  film put six SpaceX rockets in a reel that never mentions SpaceX. A contact-sheet scene should
  be posters of **this reel's own beats**, re-cropped from the previous render.
- SFX pulled to 0.09 to 0.16 on "SFX quite high".

---

## vid35, ElevenLabs Vocals (2026-07-26)

Studio Void re-skin. Established the **rebuilt X-post card kit** and the **browser window
device**.

- **Screenshots of posts and UI read as "vague", so rebuild them as native HTML at reel type
  sizes.** Real data plus rebuilt chrome is authentic and readable.
- **When the VO describes a product's UI, show the real surface as a visible browser visit.**
  Window springs in, URL types, real page renders. Feature-film montage cuts read as decoration;
  the browser frame reads as proof.
- **`hyperframes render` happily renders a dead page.** A `ReferenceError` before timeline
  registration passes every gate. Add the Playwright pageerror check.
- **Round the band corners on the CLIP, not the element.**
- X-only launches hide from search engines; `cdn.syndication.twimg.com/tweet-result?id=<id>&token=a`
  returns full JSON for any public tweet.

---

## vid33, Kimi K3 (2026-07-25)

Nine versions. The most instructive rejection sequence in the repo, and the source of the
"round-scoped, not law" principle.

| Version | Verdict and lesson |
|---|---|
| v1, v2 | Handheld POV template, then hf-style scenes inside it |
| v3 | "Why tf everything is in black and white": **brand-faithful can be dead.** Theme-per-subject picks the family, but the reel still needs a saturated accent. Colour-code the conflict. |
| v4 | "Make it clean and polished": every device added to fix "too subtle" became clutter. **Motion and colour are substitutes, not additions.** Camera rig killed entirely. |
| v5 | "Not professional" is a treatment problem before a hue problem: no gradient type, no glow shadows, one wash, hairlines. Reserve the accent by counting where it appears. |
| v6 | **"Boring" outranks every earlier constraint.** The stripped locked-off cut came back rejected. Shipped: visual objects acting out each claim, a flat acid accent, the cinematic rig restored. |
| v7 to v9 | Punch-and-hold camera. Rebuild screenshots as UI. Split-band caption position. |

Also from v6: **mock the style in HTML plus Playwright before building.** Mock 1 was rejected and
mock 2 approved in one round, and mock 2's fixes became the build's design rules. Minutes in
mocks against hours in renders.

---

## Earlier era (vid5 to vid20, 2026-07-08 to 07-14)

**Largely superseded.** Kept for the standing rules it produced:

- **vid5, vid6 (07-09), the channel-wide corrections.** "The animation looks childish": retire the
  whole pixel and game family. "Show the real asset of everything you say." "The face is too
  zoomed in, he shot it zoomed out on purpose."
- **vid6 v2.** Navy dark scenes read childish; espresso was the answer, and espresso was itself
  retired at vid11 r2 as "very weird".
- **vid10 (07-10).** His footage ships exactly as delivered, mirrored or not. Crop the dead
  headroom at the ffmpeg stage so the face reads big without zooming.
- **vid19 r2, r3 (07-13).** One hook idea gets one text layer. Ink pill slabs read cheap. **The
  hook must visualise its metaphor, not caption it.** Abstract match-card metaphors are boring;
  give characters an activity.
- **vid18 r2, vid20 r2 (07-14).** Static pills popping on the face are still a text stack. On both
  channels the hook is an acted micro-story with the creator visible, never a type lockup. Props
  on live footage read as noise; props on a panel read as story.
- **vid9 (07-10).** Theme is per-SUBJECT, not per-creator. The premium bar is STORY, not styling.
  A CTA needs a payload. On a news reel the reference video is a source of errors, not truth.
