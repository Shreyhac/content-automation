# Nader: shipped work and what each round changed

Newest first. **The most recent approved grammar supersedes older entries.**

> **Open before you start.** Two client notes on vid46 have never been answered. See
> "Round 4" below and `open-notes/`.

---

## vid56, Incogni vs DeleteMe, sponsored 16:9 long-form (IN FLIGHT, from 2026-08-03)

Fourth Nader production, third long-form, second Incogni sponsorship. **243.6s of A-roll**, 44
segments. Scaffolded directly off vid46: same toolchain, same brand assets, vid46's design doc
carried in as the reference.

Solved so far: crown, face box and gaze. The **three-mode** thresholds from vid46 transfer
unchanged (`eye_threshold 0.32`, `pad 0.9`, `min_run 2`, `min_sustain 4`, `min_window 1.6`, 5fps)
and give **46.1% face-safe coverage** across 8 confirmed glances, so he reads about as much as he
did on vid46. Nothing composed yet.

The subject is a **head-to-head between two paid services**, which is the vid46 comparison problem
again and a harder version of it: DeleteMe is a named competitor in a sponsored film. Every rule in
PROFILE.md section 8 applies, plus the vid46 grammar rules that came out of the Aura comparison:
the competitor's figures are attributed to the competitor, rendered in neutral grey and never in
the alert colour, and a verdict carries the VO's own qualifier. The VO's own framing ("they don't
even measure themselves in the same way") is the honest spine of the film; do not flatten it into
a winner.

The opening also cites **Privacy Rights Clearinghouse with the EFF, 750 registered broker groups**.
Verify against the primary source before it goes on screen.

---

## vid46, Incogni vs Aura, sponsored 16:9 long-form (2026-07-30)

3:43.4, 6702 frames, 8 chunks. Plus a 9:16 short. Theme "Signal Blue" from incogni.com's own CSS.
Delivered at -14.5 LUFS / -1.0 dBTP. **Paid placement: the upload needs YouTube's
paid-promotion flag.**

Every on-screen claim verified against a primary source. The coupon is `NADER`, not the "NAUTTER"
whisper hears.

### Round 1: REJECTED, "it's looking very cheap"

Also "the earlier one was way better", with one positive: **"the globe animations are nice."**

That positive was the diagnosis. The 3D field was the only device in the film that was not a
rounded rectangle. Every other beat used the same primitive with the same fade entrance. This
produced the standing rule: **when a review says cheap, count your carrier shapes before fixing
any individual scene.**

Other round-1 faults:

- Three of eight complaints were "text on the face". Structural, not patchable one at a time.
- The smoothed face-tracking curve read as a bug. Killed, replaced with one constant per window.
- "You're only using two or three SFX" about a bed of 17 files and 236 placements: four files were
  45% of hits. Audit by share.
- Verified figures counted up from zero, so a third of each beat showed a wrong number.
- **He reversed the duplicate-take decision.** Previously "keep both takes", now cut the repeated
  line. That invalidated the chunk map, every T0, the captions and the whole gaze and card solve.

### Round 2: the rebuild

Re-cut first (493 frames removed, both splice points inside note-reading runs so the face is
hidden across both joins and neither can read as a jump cut), then rebuilt.

- Working type sizes lifted about 1.3x. This changed the read more than any scene rebuild.
- Boxes stripped nearly everywhere; the coupon became the only card and therefore a device.
- Grounding scrims measured, not assumed: bare type over his back wall measured 1.21:1.
- B-roll 6 cuts to 9, three round-one clips replaced outright after reading their midframes. The
  grade was half the problem: round one crushed it to murk and then laid a 0.55 vignette on top.
- SFX bed **decoupled from the video render**, built straight from the cue dict.
- The supplied 17-file "saas" pack measured, normalised and class-substituted in: 57 distinct
  files, 186 placements, top share 4.3%.

### Round 2b: the recovery pass

The round-2 session died before assembly while claiming "shipped", with `out/` still holding the
round-1 film. Systemic defects every gate had passed:

- Frame-0 state leak from zero-duration `tl.set` at position 0.
- A three.js layout pinned on a vanishing end state, producing black after cuts.
- Whisper token splits printing "$7 .99" and "30 -day" across 11 clips.
- 11 headline rises slower than standard, rendering half-formed at their beats.
- `npx hyperframes render cN` resolving output against CWD, so a stale render assembled cleanly.

### Round 3: five items

- A label past 60% of a rail right-aligned into frame. Now the default for any such knob.
- The a-roll triple-pop: two short face windows separated by a down-look gap should not both be
  carded. One card exit into a **persistent device** that holds across the scene cut, and that
  device must live outside the scene divs or `cut()` kills it.
- A figure landing where a body line sits: the line **yields** before the figure arrives.
- **Em dashes banned everywhere.** 13 on-screen instances plus 14 in the caption pack.
- SFX x0.6 to median 0.060.

Also: "stuck at frame 851/888" six times was the CLI's 60-second watchdog killing a healthy
render, not disk pressure. `HF_DE_STALL_MS=420000`.

### Round 4: TWO CLIENT NOTES, STILL OPEN

**Rounds 1 to 3 were the owner. These two are Nader himself**, left on the round-3 final through
the hosted review link on 2026-07-30 at 20:09, three minutes after it was shared. They were never
answered: both still sit at `status: "open"` with a null `reply`, and the film was archived to an
external drive the next day. **Anyone picking up Nader work opens with these.**

Frames are in `open-notes/`. Link: `reel-review.shreyansh-reels.workers.dev/v/vid46`.

| t | Frame | Note | What is on screen |
|---|---|---|---|
| 63.886 | 1917 | "make this better" (red box) | c3's Deloitte beat: eyebrow "THE COVERAGE CLAIM, CHECKED", a green ring with a check and a two-line `INDEPENDENTLY ASSESSED` label, attribution in Fraunces italic below |
| 78.633 | 2359 | "this is looking off need to rework on this please" (yellow circle, with a hook drawn at the object's top-left) | c?'s 245M beat: "245" at display scale far left under "REMOVALS ACTUALLY PROCESSED", the three.js dome420 hard against the right frame edge |

Both frames are the same composition problem, and it is the **round-1 "cheap" diagnosis in its
last unfixed form**: one small object, alone, in a mostly empty 4K frame.

- The seal occupies about 17% of frame width, sits left of centre, and the entire right half of a
  3840px frame is bare ground. It is also **static** at that instant, in a film whose one praised
  device moves.
- The 245 beat splits into a far-left figure and a far-right object with a dead gutter between
  them, and the dome runs to within about 190px of the right edge with no counterweight. He
  circled the object, not the number.

**The nuance that matters: the boxed dome is the same `field.js` device he praised** ("the globe
animations are nice"). A device being right does not make every instance of it right. What he is
reacting to here is placement and balance, not the object. **Do not redesign `field.js` on the
strength of this note.**

Neither note has been diagnosed with him, so treat the reading above as a diagnosis and not as his
words. His words are in the table.

---

## vid46-short, 9:16 cutdown (2026-07-30)

45.000s, 1350 frames. First short derived from a shipped film rather than an A-roll. Method and
traps in `playbooks/short-from-longform.md`.

### v1: REJECTED

"too weird, coming on the face, the a roll cutts are weird, the ending as well seems very off and
the cuts are very weird, audio sentences are not clear, jump cuts are not perfect."

Five faults, four of them planning errors:

1. **Above the chin is the face.** Graphics placed "on his chest" were on his nose and lower lip.
2. **A tight 16:9 close-up has no usable 9:16 full-bleed crop.** Face gets a band, graphics get
   their own zone.
3. **"Sentences are not clear" means sentence fragments.** 9 of 12 beats opened mid-clause. Word-
   onset cutting is right for animation timing inside a continuous take and wrong for excerpting.
4. **One face placement per short.** v1 alternated two scales five times.
5. **11 flash cuts in 40s is a strobe.** Allow exactly one.

### v2: the rebuild on complete sentences

Ten complete sentences asserted against the film's 41-sentence list, one fixed face band,
one flash cut, the closing question promoted to its own beat so the offer lockup is never an
amputation.

New findings: whisper's sentence ends **undershoot** (a word still decaying 0.32s past its mark),
so cut to the measured `volumedetect` dip. Never drop a natural pause inside a face block. The
band's foot must dissolve with a linear mask, not a radial.

### v3: vid39's grammar, ported

He asked for `out/vid39-final.mp4` by name: "the animation and keyframing like this one, the face
card, the split screen, a roll framing like this one, also add relevant stock footages."

- **Measure the named reference, do not describe it.** vid39's card is x216 to x864, y1020 to
  y1880, and `bandOpen()` tweens clip-path and scale together over 0.34s. **The card is a MOVE,
  not a placement.** That single fact is what he was reacting to.
- Its numbers do not transfer: re-solved to 560x736 for this head.
- **One bake, two states.** You cannot tween between two files.
- Three of the film's own graded b-roll clips carded in, each cutting on a word.
- Colours, type and the three.js field untouched. He confirmed those were right.

---

## vid44, Trustmark Advisory, 16:9 long-form (2026-07-29)

3:59, 3840x2160. First YouTube long-form and first 16:9 in the system. Nine chunks.

Established: the chunked architecture, the gaze-gated face window map, the six-layer 4K ground,
the caption generator, the docking window device.

Round 2 lessons:

- Round 1 wrote "measured, never estimated" and then **estimated**. Two of three face numbers were
  wrong, the x by 125px, which at scale .82 is 103px of visible off-centre. That is exactly what
  "he is not centre-aligned in the box" meant. **Get the crown from person segmentation.**
- **The card goes on the RIGHT** for this client (a reversal of round one's left default).
- **"The black looks flat and unprofessional"**: the six-layer ground.
- A full beat-by-beat frame pass found eight defects the linter passed with zero errors, including
  an element that was styled and animated but never existed in the DOM.
- Six of nine chunk frame-0s cut to a near-empty frame.

---

## vid39, "Make AI say good things", 9:16 short (2026-07-28)

First reel for the client. Seven review rounds. This is where most of his standing rules came
from.

| Round | What changed |
|---|---|
| r2 | "No animation in hook, blue-yellow very often": the two classic rejections arrived together. Hook rebuilt as an acted object; theme re-skinned to light editorial, keeping every timing. |
| r3 | Real logos via Simple Icons. **The hook line plays on the clean face, the acted scene starts on the next beat.** A tight close-up cannot band-crop at scale 1.0. |
| r4 | **The floating card template**, not a band. Ink side rails read as "weird black bars". Packets flying into real destination cards instead of an abstract burst. Favicons for outlets. |
| r5 | The black-bar bug was **clip-path serialization**, not geometry. Browsers collapse `inset()` shorthand, so GSAP mispaired the numbers and animated the corner radius inside the left inset. Keep every number non-collapsible. |
| r6 | Stock b-roll as **cards**, never full-bleed. Carding also solves the 9:16 problem for landscape stock. |
| r7 | "More stock footage" is a density note: one cut per act, only where the layout already has free space. Audit free space **before** choosing clips. |

`out/vid39-final.mp4` is the file he now points at by name when he wants this grammar.

---

## vid40

Planned as the second cut from vid39's A-roll ("Two Steps", about 50s). Never produced; it was
waiting on an A-roll.
