# Demi: shipped work and what each round changed

Newest first. **The most recent approved grammar supersedes older entries**, and on this account
that matters more than usual: the format was rebuilt from scratch twice.

> **Open before you start.** demi2 **v20 was delivered 2026-08-14** to the local Reel Review link
> and the owner has not yet given a verdict. He marked that round *"last attempt on this"*. Open
> `review/data/demi2/comments.json` in the production repo and check for a new round before
> assuming v20 needs more work. All 34 notes recorded there are `resolved` with replies written;
> none are `source: "client"`.

---

## demi2, "six tools", 9:16 Meta ad, 2160x3840, 37.77s (`hfdemi2/`, 2026-08-13 to 2026-08-14)

Twenty versions and ten review rounds in about twenty hours. Source: a 34.03s manual cut of a
male A-roll supplied by the owner, plus six client b-roll clips of the same desk, plus Demi's own
UI component exports. Reference supplied: four Wispr Flow Meta ads (grammar only, not tempo), and
later a Viktor AI-employee ad (motion language). Plan in `demi2-shot-plan.md`; the screen
recording asked for in `demi2-recording-brief.md` was never made and was not needed, because the
client's own exports covered every state.

**Never sent to the client.** Every round is the owner's. A `share.json` record exists for the
slug (link created 2026-08-14, version 1) while the session notes say the project stayed local
throughout; either way no client note has ever arrived on it.

### v1: the film would not render, and chunking fixed it
28 `<video>` elements at 2160x3840 in one page hard-reset the 8 GB M2 Air three times. Split into
8 chunks at frame-exact bounds, max 5 videos per page, and the whole 36.4s rendered at 4K in
**4 minutes**. Delivered 1092 frames, 75.1 Mbps. (The chunking method itself is general; it
belongs in the playbooks, not here.)

### Round 1 (v2): four notes, and the one that mattered was the theme
*"is the theme matching with demi theme?"* over a beat that was already brand-correct navy. The
real fault was flat gradient voids, and the fix set the standing rule: **every graphic sits over
his footage**, dimmed or blurred, never on bare colour. Also: the tally super over his face was
removed entirely (the hook is now his clean face plus caption), chest overlays moved to y908
against a per-frame chin measurement, and the keyboard bed came out. *"is this IBM flex font?"*
was a real defect: the chunk emitter linked `src="assets/..."` and never matched
`@font-face`'s `url(...)`, so two delivered cuts rendered every caption in a fallback.

### Round 2 (v3): the hook goes clean, and a note's drawn box is an approval
*"just show the a-roll with the tools that you are using. Not this b-roll."* He also asked for
lines and more space on the hierarchy beat and for Demi2 lifted away from his chin. One note's
markup box spanned his own chin: **he had already priced in the overlap**, so honouring the drawn
geometry beat re-deriving a safer placement.

### Round 3 (v4): one note, and the sound complaint was the music
*"remove these from here."* Separately, "typing sfx still there" after two cue purges turned out
to be the **music bed's own metronomic 0.465s percussion tick** on a strict 129 BPM grid. Swapped
to `gear.mp3`, video 1's approved bed and the least ticky candidate by the same measurement (30
transients against 75).

### Round 4 (v7): the split doubled his face, and the music died at 35s
*"frame is repeating on the top"* was the split's top pane tweening in over 7 frames while the
full-bleed A-roll still showed his face above it. **State changes at a cut, never across one.**
*"this is also overlapping"* was two card swipes overlapping mid-pane: sequence them, exit
completes then enter. *"why did the music end here"* was `sidechaincompress` truncating at the
key's real data end despite a verified `apad`; the mix moved to numpy. Also *"connect all of them
with cross going lines"*: five cross lines complete the tool mesh.

Round 4 also burned a whole cycle on a **font false negative**: Plex Sans's serifed capital "I"
disappears in a downscaled caption crop, so a true Plex render read as a fallback. The fonts had
been correct since v3.

### Round 5 (v8): "typing sfx" meant ALL of it
Five timestamped notes landed exactly on the five surviving whoosh, impact and riser cues, the
ones every acoustic measure said were not clicks. **Three evidence-based purges had each removed
a plausible offender while he was naming a category: any added sound at all.** The film is now
voice plus music only. See PROFILE.md rule 8.

### Round 6 (v11, team notes): the split becomes real, and the b-roll gets to breathe
The tool-count block moved onto full-bleed b-roll; 5.53 to 8.73 became a genuine two-pane split
with six HTML tool-UI mocks swiping above him; the context beat gained drawn connector lines and
three flowing packets; **block E went from 7 cuts to 3 held shots**; and the endcard became the
client's own outro clip, with its own audio in the bed. *"The split screen should be there, bro.
What the fuck?"* is the note that produced the split's final shape.

### Rounds 9 and 10: the competitor's grammar, measured
*"smooth and subtle but so elegant"* turned out to have a number: the reference ad has **zero
detectable cuts in 79 seconds**. Translated into fade-drifts, held overlays and one calm event at
a time. This round also produced the b-roll constraint rule: **Demi's own b-roll cannot play the
problem half of the script**, and the blurred variant is the compromise.

### v13: the reference-format hybrid, ported wrong
Ported the reference's devices (a persistent product pill, crossfades) into the portfolio's own
rounded-rect vocabulary. He saw *"no difference"*. Also settled that a crossfade needs a real
underlay on both sides: fading a translucent panel over him ghosts his face, rejected twice.

### v15: "like the reference" means its DESIGN LANGUAGE
Four stills later, the actual ask was the reference's **organic drawing style**: curved dotted
connectors around a hub, irregular blobs, white washes melting into footage, pop-with-overshoot.
The misses here were design reading, not engineering.

### v16: a spliced-out beat had shipped three times
A marker-to-marker text splice swallowed the whole grid scene between its markers. Its tweens
kept firing at nothing, every gate passed, and the beat played as bare footage plus caption for
**three delivered versions**, because the QA contact sheets sampled around it and never in it.

### v17: the always-on SVG, and the reveal must play clean
A timed squiggle-arrow `<svg class="clip">` painted for the **entire film** (an SVG clip's
visibility is not managed by the framework). Two design decisions landed for good in this round
and are now PROFILE.md rules: **no branded hub or product-shaped tile before the reveal**, and
the persistent pill is redundant over b-roll that already shows the product. Plus: two long
b-roll holds beat three medium ones.

### v20 (delivered 2026-08-14): the last-attempt round, five fixes
1. Opener 0:03 to 0:05.5: the dark scrim replaced by `boxblur=12:2` at cut time (two scrim
   strengths had failed); hook chips flipped to a vertical 150px column; captions clear below.
2. Graph beat 0:11 to 0:14 re-aligned to a strict 2-column grid at x216 and x864 (organic scatter
   rejected twice, a loose grid once).
3. The graph now dissolves at 14.10, **before** the Mac window reveal. Its persistence had been
   rejected twice: *"not required, this is the Mac window opening."* Reveals play clean.
4. "connected to all of them" (17.87 to 20.87) is a new cut from b5, the shot showing all tools at
   once, held 2.99s.
5. Music starts 0.5s into `gear.mp3` (skipping its quiet head) with a 0.35s fade, measured at
   -13.9 dB at t=0. Its slow fade-in had read as a late start.

Verified before delivery with an 8-timestamp frame extraction across all five changed beats read
as images, plus numpy dB analysis of the **delivered file's** audio track. That is the standard to
repeat every round on this account.

**Studio warning from this round:** `hyperframes preview` silently rewrote `index.html`, stamping
`data-hf-id` on every timed element, which broke every edit script's text anchor and the chunker's
id regex. If the Studio has been opened, strip those attributes before any pipeline run.

---

## Demi UGC reel, 9:16, 1080x1920, 41.4s (`hfdemi/`, 2026-08-04 to 2026-08-07)

The first Demi production. AI avatar of a woman with a cloned voice, generated b-roll, and Demi's
real UI. **Local review reached v16; the client link is still on v12**, and 45 of the project's
57 notes came from the client through the hosted share. All 57 are marked resolved.

### Rounds 3 and 4 (2026-08-07): four rounds that should have been one
Both faults were "asserted instead of checked", and the client caught both.

- **Four near-identical fn-key takes existed in the project and the wrong one shipped twice.**
  When a note says "the video we showed before", resolve it to a literal filename from the
  composition and diff a frame against it. "Same setup, different take" reads as an error.
- **A blur box is a composite too.** Defocusing a laptop screen with `crop`, `gblur`, `overlay`
  gives an axis-aligned rectangle; the screen is a trapezoid in perspective, so the box overhung
  the bezel onto the cushion and he called it *"the window is being stitched"*. He was describing
  the blur, not the UI under it. Fix: a feathered polygon mask of the actual glass quad, pulled
  in about 6px so the soft edge lands on the bezel.

### Round 3, v7: porting the client's own motion system
The orb went in, lifted from `demi-orb-motion-lab` as canvas draw code. Two other things landed:
word-level retiming fixed *"the text is not in sync"* (the build typed "Hey Demi," at 15.87s and
she says it at 18.83s), and the comparison scene's columns were rebuilt to actually **grow**,
because `opacity:0` still occupies layout so both columns had reserved their full final height
from frame one. The gap is the argument, so the gap has to open on screen.

### Round 1 (v13): one note, and a shot that had to be extended backwards
The Demi window sat still for about 4s from 15.5 and he wanted the laptop shot from 19.5 moved up
to cover it. Only 5.03s of that generated take existed and 4.6s was already spent, so a new lead-in
was generated to **end on the approved take's first frame**. The two clips join with no cut at all
(colour across the join `86766b` against `877569`). The second hook line was **dropped** rather
than flashed: the new cut left it 0.76s, and **a hook line needs about 1.5s of frame to be worth
showing.** Music switched to Mixkit `gear` here, replacing the rejected AI bed.

### v3 to v6 (2026-08-05): the format pivot that produced the current card grammar
v2 was rejected too. He sent three Cursor / trycursor Instagram ads and said *"like this reference
images on the a roll, are you clear now"*, meaning **the format itself was wrong, not the content
inside it.** The card-over-A-roll grammar reverse-engineered from those ads is in GRAMMAR.md and
is still the approved system for an avatar-led cut.

This is also the round that produced the **frame-approval workflow** (PROFILE.md rule 5), after a
full render went out on an unapproved format.

### v2 (2026-08-05): the product-UI rebuild
v1 was rejected for two structural faults: abstract graphics instead of Demi's real interface, and
her face on screen 66% of the time. Rebuilt from the shot spec rather than iterated. Face fell to
about 14% full-frame plus 10.8s as a card. This round established that **the client's own exports
beat anything reconstructed**, and that captions over her cream sweater need a scrim.

### v1 (2026-08-04): the first Demi production
The client's own icon system was the whole design: five layered elliptical stages, so a dictation
app is one ring and Demi is five, and both graphics beats became the same object in two states.
Lint-clean and still visually wrong: no display type at all, rings too thin to read at 30fps, and
about 600px of dead vertical space. Frame QA at readable size is what caught it.

### Shot 01, cloned-voice audio (`demi/ugc/`, 2026-08-04)
The avatar's VO. Two findings are specific to this client's voice and worth keeping: **her real
voice is unusually concentrated at 400 to 700 Hz (50% of total energy)** and the generated read
had only 33% there, and **her measured delivery is 3.62 words/sec with clause pauses of 0.20 to
0.54s, median 0.26s**. The first VO had the right rate and exactly one 0.13s pause in the whole
line, which is what "stagnant" meant. Four tagged breaks fixed it. The general TTS and EQ method
this produced belongs in the playbooks.
