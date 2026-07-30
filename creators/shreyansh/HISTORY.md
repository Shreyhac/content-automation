# shreyansh: shipped work and what each round changed

Newest first.

---

## vid42, ElevenLabs Vocals (2026-07-28)

1053 frames. **Twelve render rounds across three structures.** The same launch as gaurav's vid35,
different creator, same asset pool reused verbatim.

His brief: *"no need to show my face too much, only at important lines and with split screen,
rest keep the edit same as last time. If you feel we can pull this off way better, please do that
as well."* Mid-build he added: *"can you also try 3.js animation skills in this?"*

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

Mid-build he asked: *"refer to vid39, can we do the split screen in this format? Also, need to
show my face for like 11.5 seconds at the very start and then switch to split screen or full
screen animation."* Face share 27% to 44%.

- **The reference card is portable, its constants are not.** Ported as-is it sliced his hair off,
  because his head is about 975px against the reference's 600px. Solve the card top from the head.
- **A soft radial scrim is not enough ground for a busy room.** His lower third holds a lit wall
  and a large action figure. A hard panel is what works.
- **No headroom means no top lockup.** Everything goes in y1064 to y1380, at roughly +30% type.
- **The x960 rail bites lower-third rows, not just captions.** Two rows shipped inside the rail
  and every gate passed them.

### Rounds 8 to 10: "this is very weird"

The 11.5s face-led opening with a full-width dark panel under his chin was **rejected**; the
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
  whoever posts it knows what a commenter can be shown. He chose literal.
- **A reference reel's own screen recording can hand you the real artefact.** The pasted prompt is
  legible in a full-res frame of the reference; the reel's entire spine came from two frames.
- **`data-layout-allow-overflow` on a container hides your own bug from `inspect`.** A stamp
  wrapped to two lines and rendered outside its box; inspect passed 19 timestamps because the
  wrapper was marked. Fix the copy to fit, then *remove* the marker.
- **A grid that fills over 2.3s must ghost first.**

### v2: the rework round

His verbatim review: new hook clip, *"dont show my face here"*, *"fast forward the video a bit"*,
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
