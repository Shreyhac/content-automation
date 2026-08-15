# card-reel: shipped work and what each round changed

Newest first.

---

## vid42, ElevenLabs Vocals (2026-07-28)

1053 frames. **Twelve render rounds across three structures.** The same launch as `paper-split`'s
vid35, a different template, same asset pool reused verbatim.

The brief: *"no need to show my face too much, only at important lines and with split screen,
rest keep the edit same as last time. If you feel we can pull this off way better, please do that
as well."* Mid-build the creator added: *"can you also try 3.js animation skills in this?"*

### Rounds 1 to 4: the first three.js build

Established the three non-negotiables for WebGL in this pipeline (vendor the UMD build, one
timeline-driven `paint(t)`, size against the screen by arithmetic). See `playbooks/threejs.md`.

Non-3D findings from the same rounds:

- **Route-relative coordinates on frame-absolute children throw the whole scene to y0.** Labels
  written as if they were children of their route panels are actually siblings. Lint, validate and
  inspect all passed; the elements were not overflowing, they were in the wrong place. If a scene
  renders as a strip along the top edge, look for container-relative offsets.
- **A wipe eats the caption it lands on.** Retime every transition against the actual VO gaps.
- **Zooming a page screenshot inside the browser device crops the left-aligned content.** Centring
  the image is not centring the content column. Measure where the column sits in the capture and
  solve the width so it fits the window body.

### Rounds 5 to 7: the floating card restructure

Mid-build the creator asked: *"refer to vid39, can we do the split screen in this format? Also, need to
show my face for like 11.5 seconds at the very start and then switch to split screen or full
screen animation."* Face share 27% to 44%.

- **The reference card is portable, its constants are not.** Ported as-is it sliced the hair off,
  because the head is about 975px against the reference's 600px. Solve the card top from the head.
- **A soft radial scrim is not enough ground for a busy room.** The lower third holds a lit wall
  and a large action figure. A hard panel is what works.
- **No headroom means no top lockup.** Everything goes in y1064 to y1380, at roughly +30% type.
- **The x960 rail bites lower-third rows, not just captions.** Two rows shipped inside the rail
  and every gate passed them.

### Rounds 8 to 10: "this is very weird"

The 11.5s face-led opening with a full-width dark panel under the chin was **rejected**; the
floating card was **"this format is good"**. New brief: *"just show my face in the start with
animation for 1 to 1.5 seconds and then switch it to either split screen of that floating card.
Show the x post animated too."*

This produced the standing distinction between a **frame** and a **cover**, and the rule that on
a full-bleed face, graphics either sit in self-grounded chips or they do not exist.

Also: a 1.4s face intro needs composed furniture, not entrances. Four card beats beat two.
The x950 rail rule applies to UI cards too: solve the width from the centre.

### Rounds 11 to 12: stock footage

*"Can you add some relevant stock footage in this? Rest, all is fine."*

Added as a **ground layer**, not as scenes, precisely because "rest is fine". Four clips, one per
claim. Grade at the ffmpeg stage; exposure per clip, never per layer.

Delivery came off the renderer at +4.0 dBTP again. The two-pass `loudnorm` with `-c:v copy` is not
optional on this SFX-dense grammar.

---

## vid38, "The truth prompt" (2026-07-27)

843 frames, three rounds on v2. Theme "Confidence Dark". This is where the
**visual-events-not-text-cards** rule was written.

### v1

- **A fabricated claim in a recorded VO is a decision, not a blocker.** The take asserts a
  statistic and an attribution, neither of which survives a check, and the reference reel's own
  on-screen evidence is an AI answer page summarising itself. The VO was already cut, so the live
  question was only how hard to sell it on screen. Ask it as a scoped choice (soften / build
  literally / hold for a re-record), and write the fact gate at the top of the breakdown so
  whoever posts it knows what a commenter can be shown. The creator chose literal.
- **A reference reel's own screen recording can hand you the real artefact.** The pasted prompt is
  legible in a full-res frame of the reference; the reel's entire spine came from two frames.
- **`data-layout-allow-overflow` on a container hides your own bug from `inspect`.** A stamp
  wrapped to two lines and rendered outside its box; inspect passed 19 timestamps because the
  wrapper was marked. Fix the copy to fit, then *remove* the marker.
- **A grid that fills over 2.3s must ghost first.**

### v2: the rework round

The verbatim review: new hook clip, *"dont show my face here"*, *"fast forward the video a bit"*,
face in split screen on one line, *"still the animations are text based and boring, instead of
text animations we need to show visual based animations that are interesting enough"*, *"the theme
colors are very boring and dead"*, *"you already have the .md file of the libraries i gave you,
check it out once again and plan entire video again"*.

- **"The libraries I gave you" means the skill's own reference docs**
  (`.claude/skills/hyperframes/visual-styles.md`, `palettes/*.md`, `references/techniques.md`,
  `gsap/references/effects.md`). There is no separate file. `techniques.md` opens by saying every
  composition should use two or three of its ten patterns, and v1 used none. That is the whole
  note.
- **"Text based and boring" is a scene-form rejection, not a typography note.** Every v1 scene was
  a card with words in it. See `docs/03-quality-bar.md` class 1 for the five replacements that
  shipped.
- **A supplied hook clip can BE the design system.** The Kling clip carried the palette, the
  metaphor and the story, and sampling it beat inventing a theme.
- **`transformOrigin` in px on an SVG `<g>` is measured from the bbox corner.** It threw a gate
  across the frame. Use `svgOrigin`.
- Path travel without MotionPathPlugin: `getTotalLength()` plus `getPointAtLength()` driven by a
  GSAP proxy is deterministic, seek-safe, and avoids a second CDN request that could kill the
  script before the timeline registers.
- **Do not put a hard-edged graphic over a face in supplied footage either.** The injection ring
  was drawn across a researcher's face in the B-roll. Same rule as the owner's own face.

---

## vid48, "5 Claude skills" (hf48/, 2026-07-31), three.js + real registry UI

27.17s, 815 frames, three render rounds. Brief: proper three.js/motion graphics, the new SASS
SFX pack, **face only at the start then split/card/circle**, real UI and real skills.

### A `fromTo`-on-a-shared-panel bug flattens the whole film, and passes every gate

`skewWipe(t, dir)` reused two shared panels across five cuts, five `fromTo`s on two elements.
On a **paused timeline the renderer seeks**, overlapping `fromTo`s on the same property resolve
at t=0 to a *later* tween's end value, not the authored start: one panel sat at `yPercent:0`
covering the canvas for all 816 frames. `lint`/`validate`/`inspect` all passed clean.

- **Tell #1: output file size.** 2.1 MB for 27s at 1080x1920 where ~39 MB was expected: a
  near-constant frame compresses to nothing. Check output size *before* extracting frames.
- **Tell #2: pixel stats.** Frame 0 and frame 210 had byte-identical mean RGB.
- **The rule: never target one element with two `fromTo`s in a seeked timeline.** One element
  per transition, `gsap.set()` for initial state OUTSIDE the timeline, only `to()` tweens
  inside it: `to()` resolves its start lazily and unwinds correctly on backward seek.

### `hyperframes inspect` needs `data-duration` on the ROOT, not just `data-start="0"` on it

Died with an opaque `Cannot read properties of undefined (reading 'totalDuration')`: a missing
attribute, not a composition bug.

### The render's own muxed audio can be measurably late

Render's audio was **+2048 samples = +42.67ms** (AAC encoder-delay priming) versus a
source-aligned build measuring 0ms. **Never ship the render's audio track**: take video from
the render, build audio fresh (source-aligned VO + SFX bed), mux. **Correlate the raw waveform,
not the envelope**: envelope correlation over the full file gave an ambiguous 42.7ms at only
1.03x peak/runner-up; the same test on the raw waveform over a 10s speech window gave a clean
13.4x peak/background.

### Measure the free BACKGROUND, not just the face (`freespace.swift`)

Crown/facebox tell you where the face is, not whether anything else can go on screen. Person
segmentation per horizontal band found **0% free background y1000-1600**: the creator held an action
figure through the whole take, filling the full width below y1000. Killed the full-bleed hook
before a pixel was drawn; forced the face band from frame 0.

### Frame 0 as cover vs. "every element must animate in"

In S0, nothing animates `opacity:0`/`autoAlpha`/position. Animate `letterSpacing`, `skewX`+
`scaleX`, `x` with `opacity 0.58→1` (never 0), a chromatic split that settles. Every element
legible AND has an entrance.

### three.js: a flat object in the XZ plane is invisible to a front camera

A torus built in the XZ plane (horizontal disc) reads as a grey smear to a front-facing camera:
it's edge-on. Moving it to XY read as a ring immediately. **Before tuning alpha or point size
on a "smudge", check which plane the object lives in.**

### skills.sh is the source of truth for "is this skill real"

`skills.sh/api/search?q=<name>` returns canonical ids with install counts; the skill page
carries the exact install command in a copy box. All five install commands in the film were
sourced from there, not memory.

### vid48 round 2, the owner rejection: card format, no face in the body, "too white"

*"I don't want to show my face in too much zoom … show my face in the card format that I've
been doing"*, *"No need to show my face in a circle throughout the video, just show the
animations and the skill names"*, *"the colors don't look premium at all, they are too
white."*

- **The creator named a device already shipped: measure it, don't remember it.** Thresholding the
  bright region of a `vid42-final.mp4` frame gave the card exactly: **652x900, centred x214,
  top y900**. Fill-width scale = 652/1080 = **0.6037**, rendering the 1003px head at 605px
  instead of the band's 940: that number is what "too much zoom" meant.
- **A face-card film doesn't need the face in the body at all.** Card on for hook + CTA only;
  the five skill scenes carry none, freeing the whole 1080x1560 safe area for bigger type and
  UI. **Removing the face improved the graphics more than any change to the graphics would
  have.**
- **"Too white" on a dark film is three things, only one of them CSS.** Ivory display type,
  white-on-black screenshots, and the A-roll itself: **16% of pixels above 200, p95 R232/G138**.
  Fixes: warm-gradient text (never flat white), secondary copy to `#8C8194`, A-roll
  `brightness(.86) contrast(1.12) saturate(.94)`. **Measure the source's highlight population
  before blaming the palette.**

### The `fromTo` trap, narrower rule proven wrong in the same film

A **single** `fromTo` on `#faceframe` at 24.52 (a plain `to` also drove it at 4.00)
immediate-rendered its FROM state and blanked the card from frame 0 through the whole film.
**The real rule: in a paused-and-seeked timeline, a `fromTo` anywhere applies its FROM state at
build time**, regardless of what wins later. For any entrance past t=0 use
`tl.set(el, fromState, t-0.02)` then `tl.to(el, toState, t)`. **The file-size tell doesn't catch
the partial case**: round 2 rendered a healthy-looking 34.3MB; only reading frame 0 as an image
showed the card missing.

### Hitting the source file size exactly

Two-pass encode can't land on a byte. **Fit the bitrate by iteration, aiming ~40KB under
target**: run pass1+pass2 once, rescale `bv *= aim/actual`, re-run pass 2 only against the same
stats log. **Close the last few KB with an ISO-BMFF `free` box** (defined as ignorable padding:
every player skips it, `ffprobe` still reports correct duration). Landed at 110,621,201 bytes,
+0 vs source. Do the padding after all QA: it changes byte count and nothing else.

---

## vid49, five free AI certifications (hf49, one day after vid48)

Same creator, same "5 X" shape: **same skeleton, new recurring device.** vid42's card, hf48's
palette and no-face-in-the-body rule carried over untouched; the Skill Lattice did not.

### A flat XY object must not get a monotonically increasing Y rotation

vid48's lesson was "an XZ torus is edge-on." vid49 hit it from the other side: every layout in
the Resume device is deliberately flat in XY, and the paint loop inherited hf48's
`rot = t * 0.20`. A steadily increasing rotation sweeps through 90°/270°, where a flat object is
a vertical smear. **The generalised rule: check rotation against the layout's dimensionality,
not just the plane it lives in.** 3D layouts spin freely; flat ones need
`rot = A * sin(t * w)`, A ≈ 0.17 rad, so they never turn side-on. Tell: a narrow bright column
where a wide object should be: easy to misread as a density/alpha bug.

### "Dead lower third" is an alpha problem before it's a layout problem

Round 1 was top-heavy with 400px of nothing below the proof card. The fix was NOT moving the
object into that band: once rotation was fixed, the same full-frame footprint at
**alpha 0.24-0.30 instead of 0.15** filled it. hf48's 0.13-0.19 was tuned for a scene that also
carried a face PiP; without one the object has to work harder.

### Entrances must finish under the wipe, not after it

"Start the clip early" is necessary but not sufficient: entrances *inside* the clip have to be
timed against the wipe too. **Budget: everything the viewer must see has to be at or past 70% of
its entrance by T+0.22.** Start entrances on the swap frame itself, shorten to 0.34-0.50s. The
outgoing element's exit must end at or before T, not start there.

### The provider's own page is the honest qualifier

The VO says "five free certifications" but two aren't unconditionally free. Each scene prints
the provider's own wording (GitHub: "waived for GitHub Education", HubSpot: "100% free. No
credit card needed.") instead of contradicting the voice or editorialising. **Screenshot the
sentence that qualifies the claim.** Also: Simple Icons 404s on LinkedIn/Microsoft (trademark
pulls); Wikimedia Commons via the MediaWiki API is the fallback, and force `svg{width:100%;
height:auto}` or the mark renders at intrinsic size in the corner.

### Bake a colour cast out in the asset, don't grade it in CSS

17.2% of pixels above 200, p95 R229/G144/B216 (heavier magenta than vid48). A `colorbalance`
pass baked into the transcode (`rm=-0.06:gm=0.05:bm=-0.05:rh=-0.06:gh=0.04:bh=-0.07` +
`eq=brightness=-0.05:contrast=1.10:saturation=0.90`) took it to 5.1% above 200 and closed the
R-G gap from 85 to 56. Push further and skin/hair go green; test candidates as stills in a
contact sheet before committing.

### Two smaller ones

- Scene durations summed with floating point fail `lint` (`19.26+4.48 = 23.740000000000002`).
  Set each duration a hair under.
- `line-height:1.0` clips descenders under `background-clip:text`: 1.09 fixes it, no gate
  catches it.

### vid49 v2, the four-note rejection: boring hook, safe zone, screenshots, "AI slopped"

**"Too AI slopped" means the carrier, not the palette.** v1 was dark ground + terracotta glow +
dot grid + drifting point cloud: the generic AI-video signature. Repair: design language from
the subject's own tradition: ink navy stock, gold foil, guilloche engraving, wax seal, engraved
Fraunces caps. **Ask what the subject is physically made of before reaching for a palette.**

**Safe zones: the 4:5 feed crop is the gate that actually bites.** The Reels player alone
(y150-1600) said v1 was fine; the grid preview crops to 4:5, **y285-1635**, and v1's eyebrow
(y150) and hook number (y194) both sat above it: the thumbnail lost the whole claim. Audit a
cover against the 4:5 crop, not just the player.

**"Don't show screenshots, build the UI and animate it."** Five page captures became one built
UI system reused by all five scenes, sharing no colour with the certificate so software never
reads as credential. **A built panel can *perform* the claim**: the $99 gets struck through, the
total drops to $0.00 with a FEE WAIVED stamp, the badge mints under a foil sweep. A screenshot
can only assert.

**A recurring object earns its place by being literal.** An abstract point cloud was fair game
for rejection ("off and irrelevant"). A **guilloche rosette**, the actual spirograph engraving
printed on certificates and banknotes, is inarguably on-topic in the same slot.

### Guilloche in three.js: two traps

- **Never interpolate R and r.** An epitrochoid only closes when R/r is rational; lerping
  through non-integer R sweeps enormous arcs off-frame. Switch R, r, d **discretely on the cut**
  (the wipe hides the swap); lerp only centre/level/spin.
- **Guilloche is copies, not scales.** Nesting rings 0.30x-1.0x smears. Real guilloche is many
  near-identical copies each turned a fraction of a lobe: `scale 0.82-1.0`, `phase = f*2PI/lobes`.
  Skip lobe counts below 5 (reads as arms, not a rosette).

### `from()` immediate-renders: a cover frame cannot use one on a visibility property, again

`tl.from('#s0-marks .mk', {scale:0.5, autoAlpha:0}, 0.34)` blanked the frame-0 brand marks. The
fix is not to move the tween later, it's to pick a legible FROM state: `scale:0.88` with no
`autoAlpha`, starting at 0.

### SVG limbs need `svgOrigin`, not `transformOrigin`

`transformOrigin` on an SVG `<path>` resolves against the element's own bbox, not SVG user
space; each limb pivoted about a different point and detached. `svgOrigin` is the SVG-specific
API and takes user units; never combine the two on one element.

### Grain is how you honestly hit a file-size target on a flat film

A mostly-flat navy film with line art hit a quality ceiling: raising bitrate 31→38 Mbps added
only 850KB, leaving 3.3MB of `free`-box padding. A **deterministic per-frame grain layer**
(360x640 canvas, frame-indexed PRNG, scaled up, `mix-blend-mode:overlay` at 0.075) gave the
encoder real high-frequency data; padding fell to 40KB, and it also fixes H.264 banding on dark
radial falloffs. **Put grain at a z-index BELOW the face card and UI panels**: at z-39 it made
the creator's face read as a noisy low-quality video, the opposite of intent.

---

## vid52, "Claude as a web designer" (2026-07-31 window)

**Identify the script from the A-roll, never from the folder.** Two scripts were plausible for
the take the owner pointed at; a sibling file in the same export folder was a *different* script
entirely. A 40-second whisper pass settled it: transcribe first.

**A named style reference can be ruled out on arithmetic before it's ruled out on taste.** The
owner rejected a "reaction console" device because the matte wouldn't hold; `simone-style-
breakdown.md` already had the number that proves them right (1.3 head-widths against a 4.0
minimum). When an owner vetoes a device, check whether the repo already has the number.

### The `fromTo` trap, second occurrence, new shape

One `fromTo` on the CTA at t=23.96 pinned its `from` state (`autoAlpha:0`) at *creation* time
and blanked the face card for the first half of the film. Every gate passed. **The generalised
rule: an element NOT inside `class="clip"` has no framework-managed visibility, so it must never
be driven by `fromTo`.** Use `tl.set` + `tl.to` per state change.

### A safe zone is regional, and "wide" is decided by the lowest element

Content blocks ran x88→x992, 32px inside the like/comment rail for anything below y900. **Fix
the column, not the element**: 872px (x88-x960) is now standard for any composition placing
cards below y900.

### Whitespace that reads as unfinished

Scene content ran y200-1250 and stopped. **When a layout has dead space, prefer an element that
does a second job over padding or scaling**: a running spec-sheet footer that also carries the
film's spine (bars filling per skill named).

### Transitions need a HOLD, not just a pass

Symmetric wipes (in 0.22/out 0.22) put full coverage at a single instant, but scene clips
overlap 0.20s by design; two scenes were on screen simultaneously through the panel. **The
panel must cover for at least as long as the overlap**: in 0.20 → hold 0.16 → out 0.24, every
outgoing clip ending inside the hold.

### Verify the person, not just the product

`emilkowalski.com` is a *different* Emil Kowalski (a Polish marketing founder). The design
engineer named in the script is `emilkowal.ski`, found via the GitHub API's `blog` field. **For
a person, resolve identity through an account you've already verified, not the domain that
matches their name.**

### Smaller things

- skills.sh ships `class="dark"` hard-coded; `color_scheme="light"` does nothing in Playwright.
  Built cards (exact install command scraped, laid out at 4K) beat downscaled screenshots.
- Judge a render's grade on a high-quality extraction: ffmpeg's default JPEG (q≈25) made a
  clean paper film look hazy; `-q:v 2` showed it was crisp.
- `--ghost #A9A599` on paper is 2.34:1; use `#75736A`. Light terracotta `#C96442` fails on paper
  at 3.7:1: a second token `--terraTx #B3593B` for accent-on-paper.
- Em-dash grep is a pre-render check, not pre-delivery: seven `FIG. NN` caption dashes cost a
  full 4K re-render because the grep ran after the render.
- Render audio came out **21.3ms late** (1024 samples at 48k): the offset is not a fixed
  constant, measure it every time.

### vid52 round 1: three notes, and a collision the markup exposed

**"Add an image of coffee here with proper animations" (x2).** A designed placeholder is still
a placeholder: applies to content imagery inside a built mock, not just logos. Sourced from
Pexels, cropped 4:5, chosen for palette fit. "Proper animations" on an image means it **reads as
the photo rendering in**: clip-path reveal upward + inner scale settle on two separate elements
so neither fights the other.

**"This is not center aligned."** Every individual card was on the grid; the *group* as a whole
was 110px off-centre. **A cluster of elements has its own centre: compute the bounding box of
any group that reads as one object and centre that**, not its members.

**The note's markup box caught a bug the note wasn't about.** The rectangle around one element
also enclosed a caption running through the footer 8px below it. **Read the whole markup frame,
not just the element the note names.** Adding a persistent footer late silently re-imposes a
bottom bound on every scene: re-audit each scene's lowest element after adding one.

---

## vid53, herdr × Spider-Man (hf53)

First time the owner named a theme by NAME with no reference video ("Spider-Man, actual webs,
Spider-Man hanging"). The subject-material rule still decided the design: herdr is panes in one
terminal, a comic page is panels on one sheet: the film became a **Spider-Man comic page**
(newsprint `#F3EDDF`, Ben-Day halftone, ink panels with offset shadows, Fraunces-italic caption
boxes, web silk that *carries* UI). **A named theme is a costume; the metaphor mapping is still
the design work.**

### Generating copyrighted characters (masonry CLI)

- **gpt-image-2 refused Spider-Man in every phrasing** (named, unnamed-described, "fan art"):
  four failures. **Nano Banana Pro (`gemini-3-pro-image-preview`) produced it first try.**
  Fallback order for IP characters: gemini-3-pro first.
- Prompt pattern: cel-shaded fan art + "plain solid uniform bright green chroma-key background,
  no shadow, no text" + **"absolutely NO panel border: background extends to all four edges"**
  (without it the model draws a comic frame welded to the figure's silhouette).
- Keying: green-dominant mask (`g>100 & g>r+40 & g>b+40`) + despill, crop to alpha bbox.
- **Compute rendered height before placing a cutout**: `h = w × (imgH/imgW)`. A figure at
  `width:280` was 583px tall and crossed the owner's eyes at the CTA.

### The full-bleed ↔ hanging-panel morph

One video element serves both full-bleed and the approved 652×900 panel: wrapper `clip-path`
tweened between two non-collapsible inset states + inner video transform (0.6037 = 652/1080).
**`set`+`to` only on both elements** (the vid52 fromTo-outside-a-clip trap); a yoyo hang needs an
even iteration count so it ends at y0 before the reverse morph grabs `y`.

### Web-yank transitions double-draw if the incoming box doesn't wait

Dropping the incoming caption box at the same instant the outgoing one was yanked from the same
slot double-rendered two boxes for ~8 frames. **Restage: outgoing yank at cut-0.24…-0.20,
incoming top element at cut-0.02.**

### Delivery when no single original exists

A/roll cut from a 47s raw take: no "file the creator sent" to byte-match. Matched the cut 4K master
instead. `build_bed.py` now **parses the cue table out of index.html** so the preview bed and
delivery bed can't drift.

### vid53 round 1: the face panel mid-film was one format too many

Three structural notes: (1) the hero device must appear in the hook itself: a themed film that
holds its mascot until second 5 reads as bait. (2) The hanging face panel through S2-S4 was
rejected: *"no need to show my face from here, just show the animations and the content in the
full screen."* **vid52's shape (face at hook + CTA, absent in between) was already the proven
answer; a mid-film face panel is a tax on canvas, not an upgrade.** (3) "Better spiderman
animations" both times meant **AGENCY, not more sway**: the figure had to *cause* the cuts
(recoil web-shots firing before every yank, a rappel down the status wall, the landing jolting
the page). **A figure that reacts is decoration; a figure that causes the cuts is a character.**

Timing note: a `sine.inOut` crossing entering off-frame left needs its tween to start **~0.3s
before the frame the figure must be seen on**: the ease's slow head keeps it off-canvas for the
first fifth of the tween.

### vid53 round 2: captions are not optional on this channel

*"where the fuck are the captions and supers."* The reel shipped with lockups and scene text
but NO spoken-word caption track, misapplying `feedback_no_duplicate_caption` at the wrong
altitude (that rule trims caption chunks per-beat; it doesn't license dropping the layer).
**Word-synced captions + kinetic supers are a standing requirement on this channel.** Per-scene
y so captions never touch a face or the bottom band (face scenes y1360, others y574/y1390/y1500).
Duplicate-rule application that survived: hook and CTA run caption-free (a lockup/burst already
speaks the words); everything else is captioned even when a burst shares one word.

---

## vid54, DoMyWork.ai collab: "Ghost jobs" (hf54, 2026-08-02)

64.66s, first paid-collab build. Brief: "replicate the actual UI." The film runs entirely
inside DoMyWork's own design system (indigo `#6C5CE7`, Poppins/Inter/Gaegu), delivered
byte-matched to the sent master (275,684,793 B @ 2160×3840).

### A marketing page IS the app-UI reference, if you film its demo animation

The real app is login-gated, but the marketing site plays the real playbook editor as a
scroll-triggered demo (slash menu, block chips, run buttons, agent dropdown). **Screenshot the
demo over time** (14 frames at 1.6s intervals after slow-scrolling to trigger
IntersectionObservers): static full-page captures showed EMPTY panels. `networkidle` also
times out on marketing sites with keep-alive sockets; use `wait_until="load"` + slow scroll +
per-section screenshots.

### When the VO speaks a document into existence, the document IS the caption layer

The playbook beat types instructions word-by-word on whisper onsets: running captions
underneath would double every word. **Per-WORD reveal beats per-char typing**: perfect sync for
free, and it reads as writing.

### A scene without its own yank ghosts through the next scene's entrance

S0 had no exit (only the wipe). The incoming board lifted in at partial alpha WITH the hook
still at full opacity underneath: read as a double-exposure bug. **The clip window ending is
not an exit**: the wipe hides the yank, it doesn't replace it.

### Data that backs a spoken number must be derived, not eyeballed

"14 older than 90 days" over 25 pills: hand-written ages had 15 over 90. Generate/verify the
array against the claim before it ships. Same family: a counter's HTML initial state must equal
the tween's from-value, or it shows a visible stutter (25→0→25).

### An empty doc mid-film reads unfinished; the product's own empty-state fixes it

Ghost rows (pill + text bar, `#EEF0F8`) filled the 4s dead body the way the real editor's empty
state would, each fading exactly when its block starts typing. Extends vid52's "whitespace
reads as unfinished": prefer the subject's own empty-state furniture over decorative filler.

### Pexels without an API key

The search page HTML embeds direct `videos.pexels.com/video-files/...mp4` URLs. Curl with a
browser UA; UHD variants included.

### vid54 misc

- Whisper mishears fixed in every on-screen text pass: "been life since"→live,
  "to do my work"→to DoMyWork, "Come in, Ghost"→Comment GHOST.
- `deliver.py` gained `-vf scale=2160:3840:flags=lanczos` on both passes: byte-matching at the
  SOURCE resolution is one flag, not a separate upscale step.

### vid54 round 1: ten notes, two roots

**"Boring animations" across a whole film usually means entrances without SUSTAINED motion.**
Every scene entered correctly then held still until the wipe. **Audit each scene for motion in
its MIDDLE, not just its first 0.5s**: per-scene ambient motion that's diegetic (rows breathe,
the live row pulses, a check-sweep runs, the real-UI plate slow-pans for its whole 17s).

**"Not vibecoded" means the real product, and a marketing site is a usable source.** Scrolling
to the marketing page's product demo and screenshotting every ~1.1s yielded the real editor
animating: six frames cut on VO beats, inside a built browser chrome, beat a CSS rebuild on
every axis including accuracy. Capture notes: `wait_until="load"`, scroll first, `clip=` the
panel's own bbox, delete the support-chat widget before shooting.

**The real screenshot brings its own cursor.** Compositing a synthetic cursor over a plate that
already had one put two arrows on screen.

### Structural bugs that only frame QA finds, again

String-surgery on a scene block dropped **4 closing `</div>`s**: everything after nested inside
an `overflow:hidden` card, S3/S4 rendered EMPTY, and `lint`/`validate`/`inspect` all passed
clean. Cheap guard: a depth walk over the body before rendering (every scene comment must report
the same depth; final depth must be 0). Also: animating `y` on the element that **is** the
browser's clipped viewport slides the viewport itself over the URL bar: pan the plate inside it,
not the container. **Renders were killed with no error at 97-98% disk**: `df -h` is worth a
look the moment a render dies silently.

### vid54 round 2: "rebuilt exactly, with zoom-ins and actual typing", not a screenshot

Round 1's note read as "use the real pixels"; round 2 corrected it: *"cannot be just a
screenshot … rebuilt exactly how it is being shown, with proper zoom-ins and zoom-outs, and
actual typing … looks very vague."* **"The actual UI" means an accurate REBUILD that can
perform, not a capture of the real one.** A screenshot is inert: can't type, can't focus a
field, goes soft under a zoom. The capture's real value is as a **design spec** (chip shapes,
field styling, brand pills): the rebuild types character by character with a caret, opens the
slash menu, and takes a camera.

- **A zoom is only legible if the content can survive it.** Content 824px in a 904px view clips
  above scale 1.10. Fix the layout: narrow the doc to 780px (content 724 × 1.24 = 898 < 904),
  `transformOrigin:'50% 0'`, animate scale+y only.
- **Ambient `img` rules leak into rebuilt UI.** `.bw-view img{position:absolute}` (written for a
  full-bleed screenshot plate) grabbed an icon inside the rebuilt editor. Scope such rules to
  `>` direct children once real content shares the container.
- **A CSS filter drains everything under it, including what must stay hot.**
  `filter:saturate(.12)` on a ghosting card killed the red stamp sitting inside it. Wrap fading
  contents in an inner div; leave the stamp a sibling above.
- **Icon + text in a small pill: icon on the LEFT in its own tile.** Right-aligned emoji over
  `nowrap` text collided on 25 pills. `left` tile + `text-overflow:ellipsis` makes overlap
  structurally impossible.
- **Where a brand's UI is the proof, build the brand's UI.** "Show the job as active on
  LinkedIn": the hook is a LinkedIn posting rebuilt in brand blue that flips to red, ghosts,
  and reveals "Posted 1,938 days ago." **The claim is performed by the artefact the claim is
  about.**

### vid54 round 3: "boring background, make it classy" (the library catalogue pass)

Owner pointed at `~/Desktop/libraries.md` (230+ design libraries). Most is scroll/framework-
shaped and useless to a *rendered* composition (no scroll, no React, every frame a pure function
of frame index). **The value of a library catalogue for video is the TECHNIQUE, not the
package**: port the idea inline, keep the render deterministic and offline. Three that
translated:

1. **MeshGradient**: five radial blobs on independent sine paths, drawn at 310x520 and
   blurred up 46px in CSS. Tiny canvas + big blur removes the flat-grey ground that reads cheap.
2. **DotOrbit**: 64 dots on seeded value noise with proximity threads (`1 - dist/LINK` alpha).
   Structured motion, not decoration: 2,016 pair tests/frame, free.
3. **`simplex-noise`/`alea` replaced with inline value-noise + mulberry32**: `Math.random()` is
   banned; a seeded hash gives the same frame every seek.

**Stacking order is the whole ballgame with background layers.** The mesh went in as a sibling
inside the same wrapper as the washes and silently sat OVER the moving grid, deleting the grid
the owner had asked for one round earlier. Write the back-to-front contract down: ground → mesh
→ dot-texture → moving grid → constellation → sweep → vignette → grain. Verify by cropping an
empty region of a rendered frame at 2x, not by trusting the DOM.

**Three cheap devices that buy "premium" on any light-ground film:** a **vignette** (~11% radial
falloff at corners), a **specular sheen** (one 230px white diagonal, `overlay`, crossing each
hero panel once as it settles), and **depth parallax** (content drifting 10-12px against the
ground). All non-diegetic, none touch the story.

**A repeated motif beats a one-off flourish.** A three-dot pulse used only where the agent is
literally working (three moments, same vocabulary) reads as a system rather than an effect.

---

## vid55, "Three websites, free API keys" (hf55, 2026-08-03)

29.83s, 3-item listicle. Handed over as "re-edit this CapCut export better": it was not an edit
at all.

### "Re-edit this better" can mean "there is nothing there yet"

Scene detection found **2 weak hits, no real cuts**: 60 frames at 2fps were one continuous
selfie take. **Run scene detection before deconstructing a "reference"**: it distinguishes "an
edit I must beat" from "raw A-roll and a script," which are different pipelines.

### The contrast pass is a background-composition detector, not just a colour check

31 WCAG warnings, ratios inside a single word swinging 1.04→2.93 per glyph: **per-glyph
variance means something structured is sitting behind the text.** A full-bleed talking head sat
behind item scenes for 23s because it was never clipped after the hook cut, only overlaid.
`tl.set('#faceCard',{clipPath:'inset(50% 50% 50% 50%)'},1.50)` cleared all 31. **A transparent
overlay does not mean the thing under it is gone.**

### `letterSpacing` is banned by the linter (glyph snap under seek-by-frame capture)

Replaced with a `spread()` helper (per-glyph `<i>`, animate each `x`). **Cannot be used on
`background-clip:text` gradient headings**: each glyph would get its own gradient ramp instead
of sharing the parent's; use a plain transform entrance there instead.

### A "non-visibility entrance" is not automatically a composed frame 0

Animating characters with `scale`+`autoAlpha` staggered from 0.10 left every character invisible
at t=0: an **empty black box** on the cover. **Frame 0 is only safe when the element's settled
state IS its t=0 state**: characters static and present, motion carried by a caret blink/settle
from the final value.

### Whose UI is on screen must agree with the number above it

`?max_price=0` never applied the URL filter; the shot capture showed unfiltered pricing under a
"14/337 free" headline. **Verify the capture shows the state you asked for before it goes in the
frame**, and prefer the API over a filtered page URL for anything counted on screen.

### The fact-check saved the reel by relocating the claim, not deleting it

Free GLM/Kimi/Qwen were attributed to OpenRouter, where all three were delisted, but
build.nvidia.com carries them with real Free Endpoint badges. Fix: **move the payoff to S2**
(real vendor badges) and give S3 an honest redirect. **When a claim is false, check whether it's
misattributed before you cut it**: a relocated truth beats either a lie or a retraction.

### Misc

- Whisper mishearings: Kimmy→Kimi, Quinn→Qwen, Bytes→Bytez, Olama→Ollama.
- Warm cast (not vid49's magenta): 4.6%→4.1% above 200 with light `colorbalance` + `contrast=1.06`.
- 100 words in 29.6s, only 6 gaps over 0.3s: gap-cutting was pointless, straight transcode kept
  whisper onsets valid within 0.1s.

### vid55 round 1: "hook boring", "show animations with a card", "theme very off and weird"

**I rebuilt the exact look this creator rejected on vid49, from the entry that records it.**
Dark ground + terracotta glow + dot grid + drifting point cloud: the generic AI-video
signature LEARNINGS already names. **Reading LEARNINGS for the pipeline is not the same as
checking it against the thing you just built**: the rejection was filed under a different
video and never surfaced while writing CSS. Cheap guard: before the first render, list the
background layers and grep for each one's past verdict.

**The fix that generalises: skin the film in what the subject is physically made of.** An API
key lives in a `.env`/terminal/editor: every surface became dev-tool paper (editor cards,
gutters, `bash` tabs), and three competing vendor hues collapsed into **one syntax-highlight
system**. Fixed "off and weird" better than any palette swap because the incoherence was three
competing accent systems, not the individual colours.

**Mocking before building paid for itself immediately.** Three static frames screenshotted with
Playwright (~4 minutes) caught a wrapped card number, two overlapping stamps, and a wrong
face-card scale, approved before a single render. **After any theme rejection, the next
artefact should be a mock, not a cut.**

**"Show actual X animations with a card" means build the object and let it fail on camera.** A
real Visa card slides in, takes a red slash, gets a NO CARD stamp; a trial badge's bar drains to
zero before a NO TRIAL stamp lands. **A built artefact can enact a claim; a pill can only assert
it.**

### The space-collapse bug that hits every per-character animation

`display:inline-block` on a space-only span collapses it to zero width: "THREE FREE" rendered
as "THREEFREE". One-line fix: `white-space:pre` on the per-char span, needed from the start of
any glyph splitter.

### Two rules the layout inspector cannot see

- **Safe zones are not overflow.** `left:640 width:440` = x1080, flush with the frame edge:
  `inspect` passed it clean because nothing overflowed its parent. Safe-zone extents have to be
  audited by arithmetic every round.
- **A scene can pass every gate and still be empty for most of its life.** A terminal entered at
  17.02 of a 13.40-18.62 scene: blank for 3.6 of 5.2s. Fix is an *earlier* entrance with content
  waiting under a blinking caret, not a later one.

### Performing a rate limit beats printing one

v2 runs real `curl` against the real host and shows the real response codes (`200 OK`, then
`429 Too Many Requests`) instead of a labelled meter. **A status code is evidence; a labelled bar
is a claim.**

### vid55 round 2: "did you change the colour in my A-roll?" and a hook still not acting

**Never grade this creator's A-roll: second time this happened.** A warm-cast pull +
contrast/saturation was applied in the transcode because the measured stats invited it; the
creator explicitly vetoed touching it. **The pipeline documents a grade step and the numbers will always
look improvable; do it anyway and it reads as touching their footage. Measure the cast, REPORT
it, don't apply it**, and verify the shipped A-roll against the master (p95 R/G/B within a
couple of units). Audio cleanup is a separate axis the creator hasn't objected to: say so
explicitly so they can veto it too.

**A hook rejected twice for "animations" is never a typography problem.** Round 1 got per-glyph
slams and a caret; round 2, same note. **What finally worked: the hook performs the film's
thesis instead of announcing it**: frame 0 is `$ curl api.bytez.com/v1/chat` returning a red
`401 Unauthorized`, the header types in, the request flips green `200 OK`. Whole story, 1.4s, in
the film's own vocabulary. **When a note says "animations" twice, stop animating and ask what
the scene could DO.**

**The linter knows the gotcha my own memory file documents.** A confirm-flash fading to zero
exactly on the 1.42s blink-clip boundary tripped `lint`'s hard-kill check: verbatim the trap
already recorded. Any fade landing on a clip edge needs `tl.set(sel,{autoAlpha:0},end)` after it.

### vid55 round 3: shipped 1080p when the standing rule is byte-match the master

*"the size of this video is very low, need it to be in the actual size of my a roll or more than
that … we decided it to be on that size itself."* The note was right: the raw 1080x1920 render
(29,314,793 B) shipped without ever running `deliver.py`. **`deliver.py` is part of the
deliverable, not an optional polish step**: loudnorm to -14 LUFS, upscale to master resolution,
fit bitrate by iterating pass 2, close the last KB with a `free` box. Corrected delivery: 118.7MB,
delta +0: 4.05x the size, 4x the pixels. **Add it to the render→QA→deliver checklist
explicitly**: copying the script into a new scaffold isn't the same as running it.

**Honest limitation to state when shipping:** the composition renders at its `data-width`
(1080x1920) and `deliver.py` upscales: the file has the master's dimensions/byte count but the
graphics were composed at 1080 and interpolated up. True native 4K means authoring at 2160x3840
directly. Worth offering, don't let byte-match imply it (this becomes the vid57/vid60/vid61
resolution thread below).

---

## vid57, "Your AI agent forgets everything" (hf57/, 2026-08-05)

36.93s, Opus 5 memory cost (effort/cache/batch), 153,451,594 B byte-matched. Handed over as
"edit it the way we have been doing," A-roll explicitly hands-off.

### The colour shift is the RENDERER, and now it's isolated

Measured the whole chain on a crop of the face band only (y520-1290):

| stage | p95 R,G,B @ t=4.0 |
|---|---|
| the master | 246, 158, 154 |
| ffmpeg transcode | 246, 158, 154, bit-exact |
| after `hyperframes render` | 235, 155, 150 |
| after `deliver.py` | 235, 155, 150, unchanged |

**The browser compositing path in the renderer is the entire source of the shift** (~11/255 on R
at the top end, a highlight roll-off, not a hue rotation). Colour metadata is `bt709/tv`
identically at all four stages, so not a tagging bug. Every reel vid49-vid56 shipped through the
same path, not a regression, but now a measured number rather than a suspicion.
**Measure the face band, not the frame**: full-frame p95 first reported an R-B gap collapsing
66→9, which was measuring the ivory cards, not the creator's footage.

### "Don't touch the audio" reaches `deliver.py`

`deliver.py` loudnorms to -14 LUFS first: audio processing the creator vetoed for this video.
Measured instead: render mix -21.83 LUFS vs the source -22.25 (SFX bed adds 0.4dB, nothing else). Added
`--raw-audio` to remux the mix untouched. **A standing delivery script can quietly contain the
exact step a per-video instruction forbids: re-read what the script does when an instruction
changes, don't just run it.**

### The creator's room is the design system

**The back wall is already ivory**: the same paper the approved hf55 theme is built on. Ink
type sits directly on that wall on face beats and nothing reads as pasted over the presenter.
Subject-material rule pointed at the *footage* rather than the subject: **before inventing a
ground, check what colour the room already is.** Band law: A y170-470 (wall) · B y510-1300 (face/
content) · C y1400-1570 (captions). Full-bleed safe on every beat, no crop needed.

### Every claim verified, and that changed the build

First reel here where the fact-check found nothing to relocate: the film could be built
*directly on the real API surface* instead of around a hole. **Run the fact-check before
designing, not after: a verified script buys you literal objects to animate.**

### Two bugs only frame QA could catch

1. `typeLine()` printed the literal string `undefined` for 3.6s: reads `el.dataset.txt`, one
   element had inline HTML and no `data-txt`. **Grep that every `typeLine` selector has a
   `data-txt`.**
2. The effort cursor rendered off-frame: `left:930px` *inside* a card at `left:88` = absolute
   x1018. The safe-zone guard missed it (rail check is text-only, cursor is an empty div).
   **Nested absolute positioning is card-relative.**

### `qa_guards.py`: three guards combined and ported

`safe_zones` + `paint` + `motion` in one file. Exclude `.rig`/`.par`/`.ov` shells (inset:0, whose
measured edges aren't ink: 8 of 20 false positives). Result: **0 safe-zone violations, 0 paint
failures, 0 held blocks**: first cut in the repo to hit that. Micro-punches from a low origin
are the usual top-band cause (1.05x lifted y186 to y141, inside the 150px Reels chrome).

### vid57 round 1: "only text animations, no icons, no keyframing, no Claude logo"

Six notes, one root, and LEARNINGS already had the number: *"When a note says 'animations'
twice, stop animating and ask what the scene could DO"* (vid55); *"the problem is the SCENE
CONCEPT and the CAMERA"* (`feedback_premium_motion_grammar`). **I thought I had complied and had
not**: an array that empties, a price that changes, a ladder that gets clicked are all *text
mutating inside a card*. Not a single drawn object in 37 seconds. **An acted scene needs a DRAWN
THING that moves through space, not a string that changes value.** Ask of every scene: if I
muted the type, would anything still be happening?

- **An icon set is not decoration, it's the difference between a film and a document.** Inline
  SVG symbols, one per scene, stroke-drawn with `stroke-dasharray`/`stroke-dashoffset`.
- **`<use href="#sym">` cannot be stroke-drawn.** The geometry lives in the shadow tree:
  `querySelectorAll(sel+' path')` returns nothing and every `draw()` call is a silent no-op, only
  surfaced as `GSAP target not found` in `validate`. Expand symbols to inline paths to draw them.
- **A curved flight path without MotionPathPlugin**: tween `x` with `ease:'none'`, `y` separately
  (out then in). Two tweens, one arc.
- **Absolutely-positioned elements with no `left`/`top` park at the frame corner.** Four fact
  chips sat stacked at (0,0), opaque, for 2.5s before their `fly()` set a transform. Caught only
  by `safe_zones`. Any element whose position comes entirely from GSAP needs an explicit
  `tl.set(...,{autoAlpha:0})` at scene start.

### Face structure: the CARD, not full-bleed

*"Show my frame at the start for 1-1.5 seconds, then my face should go off and come only at
important lines in the form of those small cards."* **Full-bleed is an opening device, not a
mode.** Round 2: full-bleed 0.00-1.50 only, then a 640x840 card at (220,560) on three lines
(claim, promise, ask). Verified pixel-identical at all four appearances: two sizes in one reel
already read as a bug once (vid46).

### Moving one element restages its whole scene

Raising panes to make room for a flight lane pushed them into the eyebrow; moving the face card
put it under two other elements; raising a card ran it past y1600 under a punch. **A layout
change is never local: re-run `inspect` and `safe_zones` after every reposition, not at the
end.**

### vid57 round 2: the camera is a per-template setting, and "animation" means a CHARACTER

**1. "The entire frame just zooms in and zooms out a lot of times. Make it stagnant."**
`feedback_premium_motion_grammar`'s wrap-every-scene-in-a-rig zoom entrance is a **paper-split**
finding, applied here without ever checking if it was wanted. Removed globally: `rigIn` scale
entrances, all `punch()` calls, `par()` parallax, the slow push on the A-roll. Element-level
entrances (lift/drop/fade/slam/pop/fly) stayed: those are things arriving, not the camera
moving. **Camera grammar is per-template, not a house default: a rule filed under one template is
evidence, not law.**

**2. "Told you to make an animation where an AI icon is showing and he is forgetting from its
memory. Visual cartoonish animation I want from motion graphics itself."** Round 1's hook was UI
(a terminal); the ask was a **character**. Third time this pattern appeared (vid53's Spider-Man
was the first): **when an animation of a thing is requested, it means a drawn character that
acts, not an interface that represents the thing.** Shipped: a CSS bot (head, eyes, mouth, antenna
light) holding four memory chips: bobs, blinks, breathes; on the spoken close the light goes
red, tethers snap, chips fall with spin, eyes squash flat, mouth rotates 180° into a frown, head
droops 4°, a "?" pops. Every one a cheap transform on a div. **Cartoon animation is a
choreography problem, not an asset problem.**

**Frame 0 regression, caught again**: converting the hook to the character put `autoAlpha:0` on
its entrance at 0.04, losing everything but the headline on the cover. Third time the cover has
broken on this project. **On the first scene, animate only non-visibility properties, from a
state that's already legible.** Never `autoAlpha` on anything that must exist at t=0.

### vid57 round 3: native 4K, and what the byte-match rule actually costs

*"Is the video rendered in the same size I gave the A-roll to you?"* Honest answer: no.
Composition renders at `data-width`/`data-height` and `deliver.py` upscales: the file carries
the master's dimensions/byte count while graphics were drawn at 1080 and interpolated up. **The
fix is one wrapper, not a re-layout**: keep all geometry in 1080×1920 logical px, make the root
2160×3840, and scale `#stage` 2× inside it (`transform:scale(2); transform-origin:0 0`). The
browser then rasterises every glyph/border/card at 4K. Measured: **+7-9% edge energy** over the
upscaled cut.

**Budget for it, 4x pixels hits twice:**

| stage | 1080 | native 4K |
|---|---|---|
| `hyperframes render` | 1m 34s | 5m 45s |
| `deliver.py` byte-match | ~50s | ~14 min |

`--native` switches to `preset medium` (drops the redundant scale filter); `preset slow` doesn't
finish in a reasonable time at 2160×3840. **When an iteration gets 5x more expensive, front-load
the frame QA.** Run the cheap 1080 pass, fix everything, only then switch to native resolution:
this build rendered 4K, delivered it, THEN found a label overlap, forcing a second full cycle.

### vid57 round 3, addendum: silence during a 10x-more-expensive operation reads as a stall

Kicked off the byte-match delivery in the background after switching to native 4K and went
quiet; the cycle really had gone from ~4 min to ~20, and the owner stopped to ask why it was
taking so long. **When a step is about to cost noticeably more than the previous one, say the new number
BEFORE running it, not after being asked.** One sentence converts a silence that reads as broken
into an expected wait.

---

## vid60, OmniRoute (2026-08-07)

### Eleven samples measure a take that holds still

Chin measured at 11 points over 29s (worst y1080), plate placed at y1190. It cut across the neck
in the CTA: the creator leans in over the last three seconds, chin there is y1145. Re-measuring the CTA
window alone gave chin y1145/collar y1280; plate moved to y1300. **A sparse sample of a talking
head measures the pose they hold, not the pose they move into.** Measure the window each
placement actually plays over, and measure the beat where they are most likely to change (the
close). Corollary: a skin-mask heuristic returned "chin y424-492"; it had locked onto the glasses. **A
geometry heuristic that returns a number is not the same as one that returns the right number**:
sanity-check against one hand-read frame before trusting 174 of them.

### GSAP resolves selectors at tween-creation time, so builder order is load-bearing

JS-generated grids sat at the bottom of the script; tweens written against them (`.gc`, `#sqAg
i`) resolved to nothing before the builders ran. `lint` passed, render completed, nothing
happened. **`validate` is the only gate that catches this** (`GSAP target .gc not found`):
generated DOM must be built before the timeline. Second half: a JS-built element has no staged
state to inherit, so with `immediateRender:false` it sits at its CSS value until its tween fires:
24 chips visible from 3.5s, three seconds early. Fix: `opacity:0` in the class itself.

### Don't tune a gradient against moving video to rescue a contrast ratio

A wash over the shirt measured 1.08:1 (eyebrow) and 1.56:1 (label). Deepening the wash means
redoing it every time the presenter moves. **A real paper card gives every glyph a known background**: the
house device anyway, and lights the reserved band for free.

### Build the motion gate, then try to break it

`motion_guard` first reported **50% of the cut held** while a decode/slam/stamp were firing
inside it: it was fingerprinting scene *wrappers*, not their moving children. After walking
descendants, 0% held, which needed its own control: a frozen timeline should still register as
frozen (proves the gate can see a hold), and 120 consecutive hook frames gave 96 distinct states,
longest run 0.40s (proves the 0% is real). **A gate that swings from 50% to 0% after one edit is
telling you about the gate.** Same session: the paint gate flagged a caption "covered by
wipeA/wipeB" at the exact frame a wipe was mid-travel: cut devices have to be whitelisted or the
gate reports the transition working as a defect.

### Verify the claim before you design the frame around it

VO says "over 200 free API providers" and drops "billion" from "1.6 free tokens." Repo documents
290 providers/90+ free and ~1.53B/month: the true numbers are also the stronger ones, frames
carry them, audio untouched. The one unsourceable number (a price to count down from) was cut
rather than invented.

### vid60 round 2: the two faults behind four of seven notes

**Text chips are not brands.** 24 providers as monospace pills: "too shitty," twice. Real marks
from `cdn.jsdelivr.net/npm/@lobehub/icons-static-svg`, ~29 in one loop, `fill="currentColor"`
resolving black on ivory. **Render every logo to one sheet and look at it before building**: a
dead mark is worse than the text it replaced.

**One film, one cast.** A hand-drawn white robot competed with the house Claude pixel sprite in
the same film. The note named only one beat; the fault was two characters doing one job. **The
sprite in `hf/`/`hf2/` is the house character: lift it, don't redraw.** Gotcha: `.mascot` is
`position:relative`, so an unpositioned copy lands at flow origin (canvas 0,-7, half off frame):
position every instance.

**"Adjust the animation frame as well" is half of the face note.** Pulling the A-roll card off
four beats without rebuilding the graphics leaves a floating column of type. **Fill what the
face vacated with real data, not scale.**

**A transform can push a compliant box into a no-text zone.** An element measured safe at rest
and 16px inside the rail only while `accent()` scaled it 1.04 from its left edge. **Any
safe-zone gate that measures untransformed geometry is blind to this: probe live, mid-tween, at
real pixel size.**

**Card size is arithmetic, not taste.** A card of width W at scale s shows W/s source pixels
across and H/s rows, so `s >= W/1080` and **rows <= H*1080/W**. At 700x640, ceiling is 987
rows: a head, always. Card had to get NARROWER (560x700 → 1349 rows) to show more of the head.

### vid60 round 3: "split screen" and the abstraction that stated the opposite

**A full-width band cannot hold a talking head.** The bottom half of a 9:16 split is ~700px; at
s=1 a 1080-wide band shows exactly 700 source rows while the crown-to-chin is 720. Band had to
be **narrower than the frame** (960×740 at s=0.889 → 832 rows): same `rows <= H*1080/W`
inequality, hit from the other direction.

**An abstraction can state the opposite of what it means.** A compression beat drew 168 cells
for 10,000 tokens and threw them out, leaving an empty rectangle still labelled "10,000 TOKENS."
The note: *"need better and relevant animations here."* Fix: show the actual verbose prompt, the
actual compressed prompt, one answer card under an equals sign: the same answer from either
side, which is literally the claim. **Write the content the way the tool really behaves.**

**A `transform-origin:50% 100%` scale grows in BOTH horizontal directions.** A mascot at
`left:24px` and `scale(2.6)` reached 195px to its own left, off-canvas. Solve placement from the
*scaled* half-width.

**Deleting a dead block can take a live one with it.** A "from this comment to the grain
builder" slice removed a token-fountain builder inserted between them: `TOK is not defined`, the
whole composition went blank. **Slice by both ends and check for JS errors
(`page.on("pageerror")`) before screenshotting**: a blank shoot looks like a layout problem, not
a thrown exception.

### vid60 round 4: a "split" has to reach the edge

Round 3's split was a 960x740 rounded card floating at y860: correctly placed and sized, but not
a split, a card in a frame. **A split half must run to the frame edge**, full width, to y1920:
on a full-bleed beat the video already covers y1600-1920 and nobody reads it as a violation; the
reserved-zone rule is about TEXT and the CHIN, not pixels. Running to y1920 buys **1140 rows at
s=1** instead of 832 at s=0.889: the top edge solves cleanly (crown 60px below the band edge,
chin y1560, 40px clear of the UI band). **A full-bleed band has no border to draw**: its frame
is the top edge alone (a hairline + upward shadow); a `border` on a full-width element is three
invisible sides.

**Client timecodes can lie; the markup frame does not.** A note stamped t=24.06 (the compression
beat) had a markup JPEG showing the split at ~2s. **Always verify the delivered frame at the
stated timecode before interpreting a note**, then trust the picture over the number, and say in
the reply which one you acted on.

### The 4K deliverables were carrying 1080p faces: vid55, vid57, vid60 all shipped it

*"is this video rendered in the same file size that I gave you the a roll as"* exposed that the
project A-roll asset was downscaled to 1080p (CLAUDE.md said `scale=1080:1920`) then upscaled
back to 4K by the renderer. Measured on a controlled comparison (same frame index, only asset
swapped):

| asset feeding the composition | sharpness (laplacian var) | vs master |
|---|---|---|
| 1080x1920 (as shipped) | 6.51 | ~52% |
| 2160x3840 (native) | 11.99 | ~95% |
| the master itself | 12.58 | 100% |

**+84%.** Fix: stop scaling at all when the master is already 9:16: codec change only. hf55 and
hf57 both shipped with the same loss. **Match the asset to the composition's OUTPUT size, never
to a habit.** Measuring this needed a *controlled* comparison: frame-seeking two codecs with
`-ss` lands on different frames and gave meaningless numbers (69% to 274% swing) until frame
index and asset swap were isolated.

### `-q high` is not "high": it halves your master's bitrate

Delivered at the right resolution (2160x3840 from a 2160x3840 master) and still got "it is very
much compressed":

| | resolution | bitrate | size |
|---|---|---|---|
| the A-roll master | 2160x3840 | 28.0 Mbps | 102 MB |
| delivered, `-q high` | 2160x3840 | 15.5 Mbps | 57 MB |
| re-render, `--crf 12` | 2160x3840 | 28.3 Mbps | 103 MB |

`hyperframes render -q high` picked ~half the source's data rate for 4K. **Always pass `--crf
12` for a delivery render**: cost 2m46s, +13.2% high-frequency detail, landed within 1% of the
master's bitrate, which is the number the creator judges against.

**The pipeline also JPEGs your A-roll before compositing** (`--video-frame-format` defaults to
`auto`=JPEG for opaque sources: 40.5 dB PSNR against a lossless PNG extraction of the same
frame). `--video-frame-format png` fixes it but **deadlocks the drawElement capture path**
(stalls deterministically; `--experimental-fast-capture=false` does NOT disable it). The knob
that actually forces the screenshot path is `--low-memory-mode` (pins 1 worker, ~4x slower;
untested at time of writing). **A render that prints `EXIT=0` can still have failed**: both PNG
attempts exited 0 with `✗ Render failed` in the log and no output file. Check for the artefact,
not the exit code.

---

## vid61, OpenDesign (hf61/, 2026-08-08)

First build where the A-roll needed **four** segments, not one: a restarted phrase and two
0.4-0.6s holes inside a staccato delivery. 37.90s → 31.37s.

### Whisper's word table is not a beat map

Whisper smeared four staccato stabs into two long "words." An RMS envelope on the cut file found
the real onsets. **Run the envelope, not just the transcriber, wherever the delivery is
emphatic**: the transcriber optimises for text, and a caption boundary on a smeared word lands
on silence. Corollary: a halting delivery is not automatically a defect to cut: the difference
is whether the gap sits *between* stressed words or *inside* a stumble.

### A void is a defect, and the shoot sheet is what shows it

Three scenes passed every gate and still had 0.8-1.8s where one element sat over blank paper.
**Nothing measures this**: `lint` has no opinion, motion guard sees plenty of movement, safe
zones see nothing out of bounds. Only a contact sheet of every beat shows it. Fix that
generalises: **the scene's structure arrives on the cut, its content arrives on the spoken words.**
Scenes open on empty/skeleton states that fill as the creator speaks, never on a hole. **A placeholder
must sit BEHIND its replacement, never be removed**: keeps the no-exit-tweens rule intact.

### The gate that had to be fixed before it could be trusted

Porting a QA script forward exposed its element sweep never measured `<b>`, `<s>`, `<em>`, `<i>`,
`<u>`: every filename, dimension chip, slide title in this film. **A gate's scope is a claim
about coverage, and it has to be audited like any other claim.** Widening it broke two things
usefully: accent words became false "collisions" with their own caption (fixed by comparing tree
paths, skipping ancestor/descendant pairs), and `elementFromPoint` on a caption returned the
child it hit (fixed by resolving to the nearest caption ancestor). A wrapper with text split into
a child was skipped by a `hasElemChild` test: **skip a wrapper only when it has no direct text
node of its own.**

### Three faults the fixed gate then caught

Every eyebrow in the film crossed into the Instagram chrome (entering from 10px above resting,
y141-150 for four frames: **an entrance is geometry too**, same class as vid60's transform-scale
bug). A dimension chip rode a scaling drag box because `place()` scales the parent and the chip
is a child: a drag has no dimension label until it stops. A skill grid reached x962 inside the
rail because its entrance slid each chip ±26px: fixed by arithmetic (two 425px columns), not
nudging, entrance no longer moves sideways.

**Exemptions get logged, not swallowed.** Samples genuinely in flight skip the overlap check, and
the gate prints that it skipped them and why: a gate that silently drops a window reports PASS
for coverage it never had.

### Match the delivery to the master's BITRATE, not just its resolution

*"make sure that the final file is rendered in the exact size of the A-roll that I gave."*
Master 2160×3840 @ 36.25 Mbps; `--crf 10` delivered 36.82 Mbps (+1.3%). `--crf 12` was tuned
against vid60's 28 Mbps master. **The CRF that matches a source is a function of that source:
measure the master first and pick the CRF for it**, then verify with ffprobe.

### Two pipeline characteristics worth knowing precisely

- **Colour**: master and asset identical (mean Δ +0.3). Delivered file drops p95 by R-12/G-6/B-2:
  master/asset tagged `pc` (full range), render is `tv` (limited). A range squeeze, not a
  grade: numerically identical to vid60's shift.
- **Audio**: the voice is bit-faithful (correlation 0.986 once aligned) but sits **21.31ms**
  behind the asset: 1024 samples at 48kHz, exactly the AAC encoder priming delay, present in
  every reel this repo has shipped. **A raw correlation of -0.13 between two AAC files means
  "sweep the lag," not "it's broken"**: at 16kHz a 21ms offset destroys sample-level correlation.

### Content: show the true output, caption around the false claim

VO says the tool hands back "a PDF, presentation, videos"; it doesn't, OpenDesign's output is
HTML. Frames show the real artefacts under real filenames; **on-screen captions skip the false
clause entirely while the `.srt` stays verbatim.** A caption that omits is not a caption that
lies: the accessibility transcript is a different contract from the burned-in type.

### vid61 round 2: the note that was my own edit talking back

*"The audio a-roll is kind of wrong from my side. It repeatedly says 'pit lips, pit lips.'"*
There was no duplicated audio. Proved it with envelope correlation against two controls:

| | envelope correlation |
|---|---|
| the two "repeated" blocks | +0.375 |
| control: two genuinely different phrases | +0.459 |
| control: same audio, offset 30ms | +0.701 |

The suspect pair correlated **worse than different words do**: nothing repeats. Round 1's cut
had removed the pauses between four separate stabbed phrases, pushing fragments together until
they read as a stammer. **Tightening a halting phrase manufactured the exact defect it was meant
to remove.** Fix: drop the stranded fragment and both long holes instead. **When a client reports
a defect in their own footage, verify it against the master before touching anything**: the
master is the only thing that can tell you whether you caused it. A correlation test needs a
control on both sides.

### CRF is a quality target, so it cannot be a delivery contract

Round 1 at `--crf 10` landed at 36.8 Mbps (matched). Round 2, same CRF/resolution/length, landed
at 24.9 Mbps because the content got cheaper to encode (drawn artboards replaced by a screen
recording). **When matching the master's data rate is the actual requirement, pin the rate, not
the quality**: `--video-bitrate 36M` delivered 41.7 Mbps. Use CRF for a quality floor; use a
bitrate target when the number IS the deliverable.

### Real footage: survey for motion, then crop for what is IN the frame

The repo's own showcase GIFs are real footage of the real product. **It has to move**: ranked
every 2.9s window by mean frame-diff and longest static run; a "no hold at all" threshold was
wrong (an agent working legitimately pauses to think): the fault to guard is a still presented
as a capture, not a clip that breathes. **The best-scoring window is not automatically usable**:
the global winner came from a different GIF's frame, showing another recording's desktop
wallpaper. **Scan the frame for what doesn't belong to you**: one capture had the repo author's
personal email in the sidebar; measured where the app window actually ends (saturation walk from
the bottom row) rather than eyeballing it.

### A validator that samples 5 timestamps will eventually sample a transition

17 WCAG failures all at t=15.367s = duration/2, landing inside a 0.44s wipe. Re-running with
duration nudged so the midpoint cleared the wipe: 38/38 pass. **Before fixing a contrast report,
check whether the failures share a timestamp: if they all do, the sampler found a transition,
not a contrast problem.**

---

## vid63, Strix (hf63/, 2026-08-09)

New instructions: the hook must be *perfect*, show a hacker actually attacking software, and
**stop opening on the full face**: split-screen or card, only at important beats (this last
one turned out to be a misread, see round 1 below).

### A CapCut watermark is a delivery defect, and `delogo` costs nothing

`delogo=x=70:y=75:w=410:h=135` on smooth ceiling reconstructs with no visible patch, verified on
three frames: costs nothing, versus a 1.05x upscale to `crop` it out. Check the top-left of
every supplied A-roll for a prior editor's watermark before designing around it.

### THE PINTEREST EXPERIMENT: IT WORKS, AND IT IS STILL THE WRONG SOURCE

Unauthenticated `pinterest.com/resource/BaseSearchResource/get/?...` answers with paginated
results, and every video pin's HLS master downloads directly with `ffmpeg -c copy`. But: **video
pins cap at 720×1280** (a ~2.5x upscale for a 2160×3840 composition), and **the pool is
re-uploads**: the one genuinely good clip carried another editor's watermark. Pexels supplied
all four plates at native 4K instead; the one Pinterest idea worth keeping was redrawn, not
lifted. **Report the experiment's result, don't quietly drop it**: the owner asked to try something,
and the answer is "it works, here is why it still loses." Also: Pexels' search page 403s plain
curl but not Playwright, and only the FIRST query in a session returns: each subsequent query
needs a fresh browser context + ~6s gap.

### A wrapper's opacity is not its children's opacity

`put("#sbar", {opacity: 0})` hid a status bar visually while the safe-zone gate still saw its
text as live (130 violations): `getComputedStyle(child).opacity` doesn't inherit, `visibility`
does. **Use `autoAlpha` on any wrapper a gate will walk into.**

### A full-width centred box cannot be scaled

`#zero` was `left:0;width:890px;text-align:center` scaled from `scale:2.1`: the glyphs stayed
centred but the *box* reached x-77. **Give a display numeral a box the size of the numeral**
before scaling it.

### The transition ate the payoff, and only the render showed it

`$0` landed at 28.220 on the envelope peak for "free"; the CTA wipe (0.42s centred on 28.480)
started at 28.270: the film's biggest number had **0.05s in the clear, one and a half frames.**
Nothing in `lint`, `validate`, or the DOM gate has an opinion; the render sheet did. Moved to
27.740 → **0.53s clear**. **Rule: for every slam, check `t_land + 0.25s < t_nextcut - wipe/2`.**

### Three more the render caught that the DOM could not

A label wrapped to a second line and fell out of its bar (invisible to a text-vs-text overlap
check because a dotted rule carries no text); a stolen chip was red-on-dark-red and illegible at
full resolution, at a timestamp `validate` never sampled; a floor wash read hotter in H.264 than
in the browser.

### The three face states, and the arithmetic that picks between them

CARD 560×700 at s=0.519 (chin y1372, 228px clear of the band). SPLIT is a native 1:1 right
column (x440-1080, x=250): chosen because s=1 shows 640 source columns and the head spans
x210-800 **in the CTA window specifically** (a percentile over the whole take would have
mis-centred it). OFF collapses into the card's own rect. **A vertical split is the only way to
show the presenter at 1:1 without a punch-in**: a full-width band of height H shows H source rows
and the chin lands wherever the band puts it (usually deep in the reserved zone); a full-height column
has no such constraint.

### `transform-origin:100%` inverts the sign you expect

An arm anchored at the shoulder (`transform-origin:100% 50%`) and extending left: `rotation:-9`
**drops** the far end, +9 raises it. The first render had the arm lying across a slab instead of
reaching into the field above it: correct in a 300px contact sheet, obviously wrong at 2160.

### Numbers

903 frames, 30.100s, 2160×3840 at 37.18 Mbps against a 32.78 Mbps master (+13%,
`--video-bitrate 34M`). -21.2 LUFS delivered vs -21.6 master. Face on 13.9s of 30.1 (46%), never
full-bleed mid-film. `motion_guard` 0 blocks held >1.0s, 0% of the cut. 13 scenes, mean 2.3s.

### vid63 round 1: the theme was approved at the gate and rejected on screen

**An approval at the question gate is not an approval of the frame.** Asked with an ASCII
preview whether to skin the film in Strix's green-on-black TUI; the creator picked it, then
watched it:
*"the theme looks very shitty and vibe coded and very very weird … needs to be changed
entirely."* Third dark ground this repo has had rejected. **Render two or three real frames of
the actual composition, at full size, and get the pick off those**: the three-way mock sheet
built after the rejection cost 20 minutes; it would have cost the same before. Also: "it's the
subject's own material" is a good argument and it still lost: authenticity doesn't override how
a frame looks to the person whose face is in it.

**The misread, and why it was avoidable.** *"As we have been doing in the very start from 1.5 to
1.5 seconds, my full face is shown. Either split-screen it or switch it to card format."* Read as
**stop** opening on the face; the creator meant **keep** the 1-1.5s open and split *after* it. **When a
brief describes current behaviour before asking for a change, the described behaviour is the
baseline being kept unless they say otherwise.** The confidence gate got spent on the theme (the
question that felt less sure) rather than the sentence that was actually load-bearing.

**The replacement, and the rule it follows.** "The marked-up report": ivory paper, ink, one
alert red: marker ring, margin handwriting (Gaegu), rubber stamp, all physical. **The fault
named as "vibe coded" is not darkness or any one colour: it's anything that looks like it could
have come out of a generator.** The two dark surfaces that survive (install terminal, Strix's
own TUI) read as screenshots pasted into a report, which is what they are: the contrast beat is
worth more than consistency.

- **A marker ring has to be drawn, not revealed.** `border-radius:50%` can only fade/scale in,
  reading as a shape appearing. An SVG `<ellipse>` with tweened `strokeDashoffset` reads as a pen
  moving.
- **The palette flip leaves JS colours behind.** Redefining `:root` tokens re-skinned 90% for
  free; 14 literal hex colours inside tweens (e.g. `tl.to("#g1 b",{color:"#FFFFFF"})`) were
  invisible on the new paper ground: `validate` caught them as 26 contrast warnings. **A token
  swap is never the whole job: grep the script for `#` hex literals after any re-skin.**
- **A full-width split band has to reach the bottom edge.** `inset(820px 0 340px 0)` stopped at
  y1580 to "respect" the reserved zone, leaving 340px of bare paper under the picture. **The
  reserved zone protects the chin, not the chest.** Extended to `inset(820px 0 0 0)`: same rule as vid60
  round 4, met and lost to a wrong reading of the safe-zone rule.
- **A border-box print moves everything inside it.** A 14px border on `box-sizing:border-box`
  shrank the content box by 28px/axis; two labels positioned against the old box fell outside it.

### vid63 round 2, one note, and the framing on it: "if the hook is not fine, the audience drops"

Asked for the hook to be literal: a hooded cartoon hacker at a laptop, firing at it. Built flat
ink shapes, no gradient, no glow (the fault repeatedly named is anything that looks generated):
the only warm colour is the fire, which is what the eye should follow.

- **A character's ARM has to be a different value from its BODY, not just a different element.**
  Arms built the same `var(--ink)` as the torso were technically present and animated:
  invisible on screen. Any limb/tool/actuator on a flat-shape character needs a value step
  against its own body, checked at full render resolution, not assumed from the DOM.
- **A projectile's travel distance is a per-shot calculation, not one number reused three
  times.** All three bolts shared 176px travel and each died short of its own hole. Solve
  `distance = hole.x - muzzle.x` per shot.
- **A shot needs a muzzle.** Bolts appeared already in flight. A one-frame radial flash at the
  origin (~0.18s) is the cheapest fix and the one that makes "the hacker fired at it" read.

**The theme fix held; the hook did not survive a text description alone.** Round 1's theme
mock-sheet process worked (zero notes on the paper theme in round 2), but round 1's hook was
also described in the creator's own words ("switch to split screen for animations, this animation is also
very shitty") and got built as a *different* animation (a red pen marking up code) instead of
being asked what was actually wanted. **When a note says an animation is wrong but doesn't specify
what's wrong with it, that is not enough to redesign from: ask, or wait for the literal
follow-up rather than guessing a replacement direction.**

### vid63: QuickLook wouldn't open the delivered file, and the first diagnosis was wrong

The owner reported the file "just stuck here, not playing." **Without testing anything**, reasoned from
container metadata (H.264 vs the master's HEVC) to a stated theory: "macOS hardware-decodes
HEVC at this size and falls back to software for H.264", and spent two render cycles building
an HEVC companion file. **The theory was never tested and it was wrong.** When the SAME hang
recurred on a plain re-share (nothing codec-related changed), running `qlmanage -t -s <timeout>`
against all three candidates settled it in seconds:

```
A-roll master (the owner's own HEVC file) HUNG >25s
vid63-final.mp4 (H.264 delivery)     ok in 1s
vid63-final-hevc.mp4 (HEVC "fix")    ok in 1s
```

Both of *my* files opened instantly; the owner's untouched original was the one that hung: ruling
out the codec theory outright. Real cause: **QuickLook caches a preview per file path**, and
`out/vid63-final.mp4` had been overwritten at the same path four times across two rounds. A
stuck cache entry doesn't invalidate just because the bytes under it changed. Confirmed by
`qlmanage -r cache` + `killall quicklookd`, and by copying to a fresh path: both opened clean.

**Diagnose before theorizing when the fix is expensive.** `qlmanage -t -s <timeout>` against the
actual files takes seconds and would have shown "the owner's file hangs too, mine don't" on the
FIRST report: immediately ruling out the encode and pointing at that file or the OS preview cache.
Building and shipping a second deliverable (a 4-minute HEVC render, twice) on an untested
hypothesis wasted two render cycles and stated something false with full confidence that had to
be walked back. **When a claim is checkable in under a minute, check it before stating it,
especially before it drives a build decision.** Corollary: `lsof`, `xattr -l`, and a full `ffmpeg
-f null -` decode pass are three free checks that rule out "the file itself is broken" before
blaming the app that opens it: all three were clean on the first report and would have pointed
straight at the cache/path issue.

---

## vid64, "Claude builds the $10,000 website" (hf64/, 2026-08-11)

1264 frames, 42.133s, 2160x3840 at 35.30 Mbps against a 33.35 Mbps master. Style parent vid63:
same paper theme, same face rules. Six award-winning websites shown as real recordings.

### Award-winning sites mostly do not scroll, and two capture pipelines died finding out

`document.documentElement.scrollHeight == innerHeight` with `window.scrollY` never leaving 0 is
the signature of a **virtual scroller**: the wheel drives an eased WebGL scene, not the document.
Five of six sites were that (igloo.inc, garden-eight, lusion, oio, exoape); only jacobandco,
basement and locomotive scrolled a document, and **bruno-simon.com is a driving game** that needs
arrow keys. **Write the probe before building anything.**

The failure modes in the order they bit:

1. Step the scroll, screenshot per frame: **3.8s a frame** even headed with a real GPU. 110 frames
   times 6 sites is not a plan.
2. Screenshotting 70ms after a wheel tick catches an eased scroller **mid-flight**, so the scene
   rocks back and forth instead of travelling. It looked like a bug in the site.
3. `Page.startScreencast` fixes the cost and then throttles to ~3fps, because `wait_for_timeout`
   does not pump CDP events in sync Playwright. Tick with `pg.evaluate("1")`.
4. Chrome throttles rAF and compositor commits for windows it thinks are backgrounded. Needs
   `--disable-background-timer-throttling --disable-backgrounding-occluded-windows
   --disable-renderer-backgrounding --disable-features=CalculateNativeWinOcclusion` plus
   `bring_to_front()`.
5. `Page.startScreencast` returns **CSS-pixel frames** and ignores the deviceScaleFactor override.
   Ask for a bigger window, not a bigger DPR.

**Then the owner screen-recorded all six in about five minutes** on their own Mac, and measured
motion came out **4 to 80 times better** than anything the pipeline produced. **When a capture
problem has eaten more than two approaches, ask: the owner's machine is a tool in the kit.**

### Cutting someone else's screen recording

- **Speed it up.** A 6s pass compressed to about 2s is what makes a 1.1s scene read as movement
  rather than a still. Cut each clip to its longest usage so the whole chosen window plays inside
  the scene.
- **Pick the window by motion survey, then override by eye.** Three of six moved after the survey:
  one landed on a newsletter footer, one on a contact footer, one opened on a headline containing
  a word that should not go on this account's feed.
- **Some sites cannot be shown whole.** garden-eight sizes its hero type to overflow the viewport;
  in a wide short window its last line sits below the fold at *every* scroll position. Use a
  different section rather than shipping what reads as a crop error.

### Three composition faults

- **Stage the scene CONTAINERS, not just their children.** Every `#sN` div was visible from frame
  0 until its own `show()`, so any child without a staging class painted early: a scene-7 arrowhead
  sat on the first website beat for its whole duration. One `put("#s1,#s2,...", {autoAlpha:0}, 0)`
  closes the class; chasing each unstaged child does not.
- **`object-fit: cover` silently shaves video when the picture area's ratio differs from the
  source.** 916x582 against a 1600x1000 clip is 1.573 against 1.600: small enough to look like a
  design choice, large enough to cut a headline. Make the picture area *exactly* the source ratio
  and cover becomes a no-op.
- **Entrance animations on the hook leave the cover blank.** An eyebrow arriving at 0.14 and a
  claim plate at 0.40 means frame 0, the Instagram thumbnail, carries no text at all.

### vid64 round 1: "the split screen looks weird, use the card format instead"

Plus *"we need to show the screen recording for website ... proper motion should be there in the
recordings"*. The rebuild has **no split state in the file at all**: FULL 0.000 to 1.660, CARD on
10 beats (27.8s of 42.1, **66%**) at 560x700, x260,y880, video `scale 0.70`, `translate(260,730)`,
and OFF collapsing into the card's own rect. The scale is solved, not typed: a card of width W at
scale s shows W/s source columns, so s=0.70 shows 800, putting the head centre (source x400) on
the card centre (x540) while the video still covers the card's left edge. Crown lands y1017,
chin y1490, 110px above the y1600 band.

### vid64 round 2: three faults with a general form

- **A hit test beats a model of where the head is.** The card had been solved from a head centre
  averaged over the take; the note was "the frame here is shifted to the right". A head detector
  written to settle it produced a *third* number, 130px off the hand-read. What settled it was
  rendering the **real card crop**, same scale and same rect, at five candidate centres across
  four beats and reading the sheet. **When a geometry question is about what lands on screen,
  render what lands on screen.**
- **A caption band has a height, and two lines is a different height.** 66px at line-height 1.06
  is 140px tall; the gap between caption top and card top was 104px. Every one-line caption passed
  and every two-line caption put its second line on the face, twice in one film, reported as two
  separate notes. **Size type against the worst-case line count.**
- **A render that fails still leaves yesterday's file on disk.** v2 stalled deterministically at
  frame 568/1264 twice and both times `renders/vid64.mp4` was still v1: right duration, right
  bitrate, right frame count, wrong film. `ffprobe` cannot tell you it is stale. **Check the mtime
  and the CLI's exit line: exit 0 is not success and a valid file is not a fresh one.** The cause
  was **repeated `<video>` sources**, two clips at five referencing elements each. The repo already
  carried "repeated `<video>` src renders black" and two uses had been getting away with it, so it
  read as survivable rather than a limit. **One element, one physical file:** copy the clip per
  usage.

---

## vid65, "Control Claude Code from your phone" (hf65/, 2026-08-11)

735 frames, 24.500s, 2160x3840 at **38.63 Mbps** against a 32.28 Mbps master. Style parent hf64,
on the note *"replicate the editing style of the last video."* Brief: quirkier animations, a Claude
cartoon that actually works at a desk, Telegram visibly connecting to Claude, **card format, not
split**.

**This film shipped with no LEARNINGS writeup.** Everything below is reconstructed from
`vid65-breakdown.md` and the delivered file. No review round is recorded for it, so either it
drew no notes or the notes were never written down.

- **The claim was verified before anything was drawn.** Anthropic's own first-party plugin,
  `anthropics/claude-plugins-official/external_plugins/telegram`, and all six on-screen commands
  are the real ones in the real order. The restart step is genuinely mandatory, so the "restart
  once" beat is the step people skip rather than padding.
- **Beats came off the RMS envelope, not whisper.** 69 onsets over 24.51s; **54 of whisper's word
  starts moved by more than 60ms.**
- **Face law re-measured on this take.** FULL 0.000 to 1.340 only. CARD 560x700 at x260,y880,
  `scale 0.62`, `translate(174,753)`, solved from the worst-case landmarks (crown including flyaway
  hair y350, chin y1160, face centre x590) and then **hit-tested** at s=0.60/0.64/0.68 and at the
  shipped rect across 8 beats. Crown lands y970, chin y1472, 108px above the band. The creator leans in and
  drifts right by the CTA, x555 at t=0.5 to x620 at t=23.0, the same thing that bit vid64. Face on
  screen 11.7s of 24.5 (**48%**) and **the CTA is a CARD beat, never graphics-only**.
- **One new accent, and only because the subject is.** vid64's warm paper carried over intact plus
  Telegram blue, which appears **only on Telegram objects**: the mark, its bubbles, its node, its
  shield. Nothing else in the film is blue, so the colour reads as "that is the phone side" with no
  label. It splits in two for contrast: brand `#229ED9` for fills, `#1B7FAE` under white text
  (3.09:1 fails AA, 4.58:1 passes).
- **Four as-built fixes that each came from a frame, not from taste.** The cartoon alone in 940x502
  of blank paper was a void by the repo's own definition, so the zone became one `agent session`
  window. The empty-room beat needed furniture and an **empty chair**, which is the beat. A setup
  timer that counted *down* to `0s` under a label reading TOTAL SETUP TIME says the setup took no
  time at all, so it counts up 0 to 60 and the number takes the hit on "sixty". The door was
  animating the wrong way, collapsing to nothing, which read as the door vanishing rather than
  shutting.
- **Two band numbers moved by 16px and 4px of type.** The CARD graphics zone is 486px, not 502: at
  502 the zone's bottom edge landed exactly on the caption's first ink row. The OFF caption is 48px
  in an 820px column, because 52px in 940 put a long line's real glyphs at x967, inside the rail.
- **Measure the ink box, not the block box.** `guard65.py` walked 122 beats and 3,417 painted
  elements, 1,105 of them text, using a Range over the text nodes. A centred 940px caption has a
  block box that reaches the rail while its glyphs are nowhere near it; chasing that phantom would
  have shrunk type for no reason.

---

## vid66, Apple's design language as a skill (hf66/, 2026-08-12)

796 frames, 26.533s, 2160x3840 at 40.24 Mbps. Style parent hf65. Brief: proper animations,
cartoon acting allowed, face full-bleed for the first 1.5s then **card and split**, licensed stock,
fast paced. Face on screen 21.6s of 26.5 (**82%**): FULL 1.4, CARD 15.9, SPLIT 4.3.

### A reference's B-roll carries the reference creator's face and burned-in captions

The brief asked for the Apple footage out of a reference reel. Scene detection gave clean boundaries,
three clips came out at the right timestamps, every contact sheet looked right, and the render
showed **the reference creator's face across the bottom half of the plate with their own
word-captions over it**. That reel composites the Apple footage into the TOP half over a talking head; a 6-across tile at 270px
is too small to see that, and a centre-weighted `object-fit:cover` crop lands exactly on the seam.
**Read an extracted clip full-frame, on its own, before it goes anywhere near a card.** The fix was
a crop at extraction (`crop=1080:514:0:180`), not an `object-position` nudge.

### A `<video>`'s `data-duration` must cover every frame its wrapper paints

S13's stock plate was cut to 1.1s and the beat ran 1.82s, so the last 0.72s rendered as a dead grey
rectangle with a red X on it. Nothing structural sees this: the element is present, positioned,
opaque and inside every band. The guard now walks every `<video>` at every beat and checks
`painted && t in [data-start, data-start+data-duration]`, and was **verified by shortening a window
on purpose and watching it fire**.

### A full-width bottom band cannot hold a head, and that is arithmetic

The head is 745px crown to chin worst case in a 1080-wide frame. A full-width band can only be 1080
wide at `scale 1`, and the room above the Instagram chrome is `1600 - 845 = 755` rows. Every wider
band fails harder. **When "split screen" is asked for and the numbers rule out top-graphics over
bottom-face, the split is vertical:** a column at x540 to x1080, `scale 0.85`, `translate(343,0)`,
which the same face contour clears by 58px. Solved from the contour, not the bbox: worst face-left
lands x598, worst face-right x1048. CARD this film is 580x720 at x250,y870, `scale 0.72`.

### Skin the film in the subject's own material, and reserve the house colour

A film about Apple's design language built in hf65's warm marked-up paper argues against itself.
Every value came from Apple (`#F5F5F7` page, `#1D1D1F` ink, `#0071E3` link blue, `#30D158` and
`#FF3B30` system colours, an 8-point ground grid), with **Anthropic terracotta reserved only for
Claude objects**. That two-colour rule made the S9 handover, the skill file crossing from the blue
side into the terracotta terminal, legible with no label on it.

### Three cheap checks this film added

- **Check free disk before a 4K render and do not pass `--video-frame-format png`.** The first
  render died on ENOSPC at 95% full: a 26.5s 2160x3840 render with PNG frame extraction wants over
  15GB of scratch. It rendered fine on the default extractor.
- **Diff the validator's warning count against a shipped project.** 45 "GSAP target not found"
  warnings looked like noise until hf65 returned 0 for the same check: `#capW` had CSS and a caption
  engine but no element in the DOM. One comparison, one line to fix.
- **Contrast warnings clustered on scene starts are the wipe, not the design.** All 11 sat inside a
  `wipe()`'s own 0.28s window, measuring type against the transition panel covering it.

### Cross-fading text into a fast cut is a cost with no benefit

Stripping `opacity` out of every arrival helper (`bring`, `bringX`, `pop`, `slam`) left motion-only
entrances, which read as harder cuts, suit a fast edit better, and remove every frame where legible
copy sits at 20% alpha over paper.

---

## vid66b, the same reel rebuilt shot-for-shot from its reference (hf66b/, 2026-08-13)

*"Save this edit as well, but can we copy the exact b roll and editing from the reference reel."*
**Both cuts ship**: hf66 is the original build, hf66b the replica of the reference reel `DboEouole47`.
796 frames, 26.533s, 42.74 Mbps.

- **A reference reel's B-roll is a layered composite, not a clip.** It plays its Apple footage in
  the top ~47% over its creator's talking head and burns word-captions on the seam at **y960 on
  split shots and y1290 on full-bleed ones**. Every lifted clip needs a crop window chosen per
  shot, 1080x700 here, with the offset picked so the content survives (the magnifier lens at y846,
  the GitHub breadcrumb at y847, the prompt box at y864, the progress bar at y1190). **Three of 24
  needed re-cutting** because the first offset landed on blank paper or on a forehead, and the
  only way to know is to read each cropped clip.
- **Copy the shot list, re-derive the geometry.** The reference splits at y900 because its
  presenter sits further from their lens; on this take that puts the chin at y1645, inside the chrome. The seam moved
  to **y700 with the picture translated down 352**, landing worst-case crown y748 and worst-case
  chin y1547. **The rhythm is copyable, the numbers never are.**
- **A CSS transform on a box containing a `<video>` deadlocks the capture engine.** A 0.20s
  `scale:1.045 to 1` punch-in on 24 B-roll wrappers stalled the render at 40% with 15 workers alive
  and no frames for ten minutes. Removing it (the reference cuts hard anyway) captured all 796
  frames. Same fault family as "repeated `<video>` src renders black".
- **ffmpeg's encode step has its own 600s timeout, separate from the render.** 2160x3840 at 42 Mbps
  encoded at `speed=0.015x` and was killed at exactly 10:00 after a *successful* capture, throwing
  the whole capture away. Set `FFMPEG_ENCODE_TIMEOUT_MS=3600000` and
  `PRODUCER_ENABLE_CHUNKED_ENCODE=true` for any 4K render.
- **Chromium collapses `inset(700px 0px 0px 0px)` to three numbers.** A state detector requiring
  four back from `getComputedStyle` called 24 SPLIT beats FULL and produced 28 confident, wrong
  failures. **Parse defensively, then prove the detector by driving it to a known state.**
- **A full-width centred text container measures 1080px wide.** `#serif` tripped the left-edge and
  right-rail gates on its box while its ink sat dead centre. Wrap the word in an inline-block span
  so the box IS the ink, otherwise every edge gate lies about centred text.

---

## vid67, "launch your agent" (hf67/, 2026-08-14)

*"Do the exact same editing ... you can use the exact same visuals from the creator's video as
well. No block around that."* Same instruction as vid66b, different reference (the reel
`DbqcQUgxlyC`), and this time **the creator had recorded the reference's script verbatim**, which is what
made the method possible. 1057 frames, 35.233s, 2160x3840 at **38.28 Mbps** against a 33.15 Mbps
master, 168.6 MB. 11 lifted shots, 6 rebuilt, 3 full-bleed, 70 captions. Delivered chin max
**1548.7** against the y1600 band. VO -22.6 LUFS in, -22.5 out.

### When the script is verbatim, re-time by WORD, not by ratio

39.53s of reference onto 35.23s of delivery is not a linear squeeze. difflib over the two
normalised word sequences anchored **136 of 148 words**; each reference cut is mapped through the
piecewise-linear result and snapped to the nearest word onset in the delivery take. Every boundary landed
within 0.24s of an onset, most inside 0.10s. A ratio would have drifted a third of a second by the
CTA.

### "Use the creator's visuals" still has content that cannot ship

Permission was not the constraint. Six windows were unusable on their own terms: the creator's
account name in four shots, their **live `ANTHROPIC_API_KEY` in plaintext**, a third party's meeting
notes, and a real person's inbox. Two mattered more than all of those: the reference's own screen
shows the launch **failing** ("insufficient credit balance") and the spec page stamped `PLANNED ·
NOT LAUNCHED`, underneath a voiceover claiming it deployed and runs daily. **Read the reference for
what its frames SAY, not just whether they are clean.** The creator faked the payoff; lifting it
would have shipped a contradiction at the beat the reel exists to sell.

### A guard that has never fired is not a guard

The first face detector thresholded skin fraction at 0.10 and passed a clip cut deliberately from a
known face segment, which measured 0.059. Calibrating at the crop geometry the clips actually use
showed **skin does not separate at all**: a face frame measures 0.0455 and a UI lift 0.0452. But
**luminance separates by 28 levels with no overlap** (face 107 to 113, UI 37 to 80). Requiring both
in the same frame flags all eight known-face cuts and passes all eleven UI lifts. **Verify a
detector by driving it to the state it is supposed to catch, every time.**

Related: **vision misses a face that is only a forehead.** It found two full-bleed segments in the
reference; a skin-fraction sweep over the band found three, and the one it missed (19.40 to 20.10,
only forehead and eyes in frame) is exactly the one that bled into two lifted clips.

### Two gate holes that made the caption invisible to every caption rule

`tl.time(t, false)` suppresses events, so the `tl.call()` that writes the caption never fires for a
gate: `#cap` carried no text and `isText` was false. And `#cap` is `display:inline-block` and
statically positioned, so a `position === absolute|relative` filter skipped it, while its parent
`#capW` has no text node of its own. Between them the top-band, bottom-band, left-edge, right-rail,
crown and text-on-text rules were **all measuring nothing**, in this project and probably in hf66b
too. Any element carrying its own text is now measured regardless of position.

### Three mechanical findings

- **`-t` before `-i` limits what is READ, after `-i` it truncates the RESULT.** With `setpts`
  slowing a clip, `-t` as an output option silently cut two clips back to their source length, so
  they were shorter than the slots they had to fill. Frame-count asserts caught it.
- **A slot must not be able to contain a cut, and seeking is approximate.** Slots on eyeballed
  midpoints crossed cuts twice, one clip ending on the creator's forehead. Deriving slots from the
  detected cut list makes that structurally impossible, and every source window is pulled with
  **0.13s of pad at both ends** because input seeking lands where it likes.
- **The render stalled at the same frame with 18 videos and with 2.** Frames 746 and 743 of 1057,
  "Sequential drawElement capture stalled". Collapsing seventeen B-roll clips into ONE pre-composed
  band track did not move it, which is how we know the ceiling is per-frame accumulation on this
  8GB machine, not video count. Three chunks of about 350 frames rendered in 2 to 2.5 minutes each,
  with boundaries on real cuts so every join is a hard cut the edit already had.

### Concatenate the video, rebuild the audio, then prove both

Video is stream-copied so every delivered frame is bit-identical to its chunk render. Audio is laid
once over the full 35.233s from the continuous VO plus absolute-timed cues, because AAC has encoder
priming at the start of every stream and joining three of them puts a discontinuity at each
boundary: the exact shape of a "weird audio cut" note.

**Prove the joins, then prove the film.** The frame pair either side of each boundary must be
identical in caption, face state and face position, with only the B-roll changing. Then scan EVERY
frame for the artifact the design could produce: here, a band black while the composition is in
SPLIT would be a one-frame black flash. Zero of 1057 frames had it. Reasoning about `round` against
`ceil` boundaries produced two contradictory predictions; the full-frame scan answered it in one
command.
