# The quality bar

**A technically-correct first render is a draft, never the deliverable.** It nails structure,
timing and beat-matching, which is necessary and not sufficient. Budget three review rounds.
This is the job, not scope creep.

The owner will not itemise a fix list that solves the problem. He describes a feeling. Almost
every rejection this system has seen falls into one of four classes, and each has a known fix
that is structural rather than cosmetic. Diagnosing the class correctly is most of the work.

---

## Class 1: "boring", "text based", "the animations are basic"

**This is a scene-form rejection, not a typography note.**

The tell: every scene is a card with words in it. The fix is not a bigger font, a livelier
entrance or more decoration. It is to find the **physical event** each line describes and animate
that.

Worked examples from this system:

| The line | The wrong scene | The scene that shipped |
|---|---|---|
| "one prompt that fixes it" | A card with the prompt text | A glass ampoule filling with amber serum, five etched ticks lighting as the meniscus passes them |
| "it verifies" | A four-item checklist | A capsule descending a track through four gates that close on it, one per spoken word |
| "confidence score" | A number in a box | A 240 degree dial with a red sector and a needle that hunts before it stalls |
| "it retries" | A retry label | The rejected pod physically ejecting and travelling a dashed return path back into the dial |
| "Claude has the memory of a goldfish" | A claim pill on the face | Brain pops out of a dashed head, goldfish swims in, a CONTEXT REMEMBERED meter drains 100 to 0 |

**Test for the next build: if a beat can only be expressed as a sentence in a box, it is the
wrong beat.**

Two supporting rules:

- **Characters doing an activity beat icons with labels.** A personified prop performing the
  verb outperforms an abstract metaphor every time. When the VO names a physical verb, the panel
  must perform that verb on the word.
- **Synchronised is not simultaneous.** A card fading up while a name is spoken is merely
  simultaneous. Two distinct moves, each tied to a specific word (the name opens the row, the
  predicate lands the stamp), is what "sync up with what we're saying" actually asks for.

---

## Class 2: "cheap"

**Count your carrier shapes before you fix any individual scene.**

The diagnostic case: a four-minute film was rejected as "very cheap" with exactly one positive,
"the globe animations are nice." The 3D field was the only device in the film that was not a
rounded rectangle. Record card, buyer tiles, action rows, module slabs, ledger tiles, price
carriages, router tokens, reason cards and the coupon card were all the same primitive with the
same `y:+20` fade entrance.

The fix is to **replace the carrier, not the content**. And once you strip the box everywhere,
the one box you keep becomes a device: the coupon was the only card left in the rebuild, which
is why the payoff read as a payoff.

Related: at 4K, **the working type sizes are what read as cheap, not the display sizes.** Labels
at 32px and body at 56px in a 3840-wide frame are proportionally a 16px label on a 1920 frame.
A 1.3x lift on everything below headline level changed the read more than any scene rebuild.
Check working sizes as a fraction of frame width, not against a web instinct.

---

## Class 3: "not premium", "not professional", "looks vibecoded"

**Treatment before hue.** Two palettes were rejected in a row before this landed: monochrome read
as dead, hot crimson-to-orange read as a gaming thumbnail. Half the unprofessional signal was
palette-independent:

- **No gradient-filled display type.** A `background-clip:text` ramp on a large number is the
  single biggest tell.
- **No glow shadows on type.** `text-shadow: 0 0 44px` and `drop-shadow(0 0 70px)` belong on a
  light source, not a numeral. A lab instrument may glow on its own hardware; letterforms may not.
- **One background wash, not three.** Three coloured radials is a gamer-desk look. One low-opacity
  falloff plus a dot grid as a banding guard.
- **Hairlines, not coloured borders.** `1px rgba(255,250,240,.09)` beats a 2px tinted border with
  a 40px glow.
- **No RGB chromatic splits** on a hook headline. State the line.
- **Reserve the accent by counting where it appears.** The rule that made a muted gold work: the
  accent marks the subject, every rival and every label is neutral. About seven elements across
  34 seconds. An accent used everywhere is a second background colour.

**But a saturated accent is mandatory.** Theme-per-subject picks the family; the reel still needs
one saturated colour carrying every number, bar and border. A brand-faithful monochrome build was
technically correct, passed every gate, and was rejected on sight: it read as two different
videos spliced together next to a warm A-roll. If the subject's brand will not supply an accent,
borrow one from the story, and **colour-code the conflict** so the palette carries the argument.

**And motion and colour are substitutes, not additions.** Once the palette carries the energy,
strip the decorative motion rather than layering both.

**Grammar and theme are independent axes.** "It feels dead" is a grammar problem; "it feels
cheap" is a theme problem. Never trade one for the other, and never assume a rejection of one is
a rejection of both. Ask which.

---

## Class 4: "text on my face", "too weird, coming on the face"

**This is a layout-mode failure, not a nudge.** Patching instances one at a time generates more.

The structural rule:

> A beat is either **CARD mode** (the A-roll owns its rect, graphics own the rest, zero overlap)
> or **FULL-BLEED mode** (at most one self-grounded element in measured clear space).
> **There is no third mode.**

Supporting facts, each learned the expensive way:

- **Above the chin is the face.** The chin is the head's lower bound, so clear space is only ever
  below it. A stack placed at y1000 to y1346 "on his chest" was on his nose and lower lip.
- **A tight 16:9 close-up has no usable space in a 9:16 crop at all.** If the chin sits near the
  bottom of the source frame, a cover crop puts it inside the UI band and the scale that clears
  the band puts it where captions start. The answer is a face **band** with graphics in their own
  zone, not a smaller graphic.
- **A full-width band across a torso is a different device from a floating card.** A card is a
  frame (the subject is deliberately placed inside it); a bottom slab is a cover (something has
  been laid over the subject). The same creator approved one and rejected the other in one reel.
- **Prove any such layout by compositing one real frame with ffmpeg before writing HTML.** It
  costs 30 seconds and it is the only thing that catches this class in advance.

---

## Things that are round-scoped, not law

An owner's earlier correction can be reopened by a later verdict. A locked-off frame and a ban
on wipes were both correct responses to "too much", and both were reversed by a later "this is
boring". **Only the treatment rules survived every round.**

So: when a new note contradicts an old one, the new one wins for that video, and the old one goes
into `HISTORY.md` with its date rather than into the grammar as law.

---

## Process rules that protect the bar

- **Mock the style in HTML plus Playwright before building.** A three-frame static mock renders in
  two minutes. One was rejected and its replacement approved in a single round, and the second
  mock's fixes became the build's design rules. Cost of learning in mocks: minutes. In renders:
  hours.
- **Offer palettes as previews before building.** Three rounds of re-theming cost three full
  renders. ASCII palette previews in a question let the owner reject a direction in seconds.
- **Validate a new look on one chunk before mass-producing.** The 4K type-scale finding came out
  of reading chunk one three times and applied to all eight. Finding it on chunk seven would have
  meant re-authoring six.
- **Read your own render before handing it over.** The owner should not be your first QA pass.
  A round-one review that finds bugs you could have found is a round spent on nothing.
- **Two failed passes on a decorative element means cut it, not tune it.** Negative space beats a
  graphic that needs explaining.
