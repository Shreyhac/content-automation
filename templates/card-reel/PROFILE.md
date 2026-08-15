# card-reel

A different presenter, room and system from `paper-split`. Older files call this the "slot 1"
template after the folder its A-rolls arrive in.

| | |
|---|---|
| Format | 9:16 Instagram Reels, 30 to 40s |
| Subjects | AI product launches, prompt and workflow tips |
| Setting | Seated indoors, tight close-up, a lit wall and a large action figure in the lower third |
| Current grammar | The paper theme (vid63 onward): ivory paper, ink, one alert red, card-format face. No build has been named the canonical template yet. See `GRAMMAR.md`. |
| Older grammar | vid42 v3: face-led open into the floating card, three.js as a recurring object. Reference build: `reference-builds/card-reel-vid42/` |

---

## Hard rules

### 1. Do not show the creator's face too much

"No need to show my face too much, only at important lines and with split screen."

The shape that landed: a **1.4s full-bleed open**, then card beats at the important lines. Four
card beats plus the short open reads as "present throughout" at about 30% face share, with no
full-bleed talking stretch after the hook.

### 2. The floating card is approved. A full-width lower-third slab is NOT

The creator approved one and rejected the other **in the same reel**. The distinction is real:

> A card is a **frame**: the subject is deliberately placed inside it.
> A bottom slab is a **cover**: something has been laid over the subject.

An 11.5s face-led opening with a full-width dark panel under the chin was "very weird"; the
floating card was "this format is good".

**Rule: on a full-bleed face, graphics either sit in self-grounded chips or they do not exist.
Never a full-width ground.**

### 3. A short face intro needs composed furniture, not entrances

At 1.4s there is no room for elements to arrive. Corner brackets, a status chip and a scan sweep,
with the brackets and chip **already present at t=0** and only settling (scale, letter-spacing).
Frame 0 is the Reels cover: an element that starts at 0.06 is an element the cover does not have.

### 4. No headroom means no top lockup

The crown sits near y45 in a native close-up. There is nowhere above the head for a title, so a
face-led opening puts **everything** in y1064 to y1380. That band then dictates type sizes:
roughly +30% over what reads fine on a designed dark scene, because it competes with skin and
motion behind it. Landed at 104px display, 27px instrument labels, 24px mono.

### 5. This lower third needs a hard panel, not a soft scrim

A lit wall and a large action figure sit behind the presenter. A `radial-gradient(.90 to 0)` left
every graphic washed out and effectively illegible. What works:

```css
linear-gradient(180deg, transparent 0%, rgba(...,.50) 17%, rgba(...,.90) 22%, rgba(...,.93) 100%)
```

from about y820, plus a hairline at the join. It also reads as a deliberate device rather than a
fix.

### 6. Match the raw A-roll's file size on delivery

Same standing rule as `paper-split`. See `docs/06-delivery.md` step 3.

### 7. No em dashes

### 8. No camera zoom, ever: "make it stagnant"

vid57 round 2: *"The entire frame just zooms in and zooms out a lot of times. Make it
stagnant."* A whole-frame zoom-entrance-plus-micro-punch grammar (`rigIn`, `punch()`, `par()`
parallax) had been ported wholesale from another template's file
(`feedback_premium_motion_grammar`, a **paper-split** finding) without ever checking whether it
was wanted here. Removed globally across 16 call sites and the slow push on the A-roll.

**Rule: camera grammar is per-template, not a house default.** Element-level entrances
(lift/drop/fade/slam/pop/fly, things arriving) are still fine; the camera itself must never
move. Before porting any motion rule from another video's file, check which template it came from.

### 9. "An animation" means a drawn CHARACTER that acts, not an interface that represents the thing

Two separate instances, same misread each time. vid53: *"better spiderman animations"* (asked
twice) turned out to mean giving the Spider-Man figure AGENCY: a figure that causes the cuts
(recoil web-shots, a rappel, a landing that jolts the page), not one that reacts to them. vid57
round 2: *"Told you to make an animation where an AI icon is showing and he is forgetting from
its memory. Visual cartoonish animation I want from motion graphics itself."* Round 1 had built
an agent *terminal* (UI); the ask was a bot character that bobs, blinks, and visibly breaks down.

**Rule: when an animation of a thing is requested, build a drawn character that acts, never a
UI, meter, or panel standing in for it.** Cartoon animation is a choreography problem (values
that read as acting: a limb a different colour from the body, a light that goes red, eyes that
squash flat), not an asset problem.

### 10. Full-bleed is an opening device only: CARD and SPLIT are the two ways the face returns, never a mid-film slab

vid57: *"Show my frame at the start for 1-1.5 seconds, then my face should go off and come only
at important lines in the form of those small cards."* vid63 round 1 reconfirmed it after an
initial misread: *"As we have been doing in the very start from 1.5 to 1.5 seconds, my full face
is shown. Either split-screen it or switch it to card format."* The 1-1.5s open is kept, not
cut; what changed is that **split-screen is now an equally valid return alongside the card**,
solved by the same rail arithmetic as everything else (`rows <= H*1080/W`): CARD sizes down to
fit (e.g. 560x700 at s=0.519), SPLIT runs a native 1:1 column to the frame edge instead of
shrinking. Never a full-width lower-third slab (rule 2) and never full-bleed again after the
open: a mid-film face panel was tried and rejected once already (vid53: *"no need to show my
face from here, just show the animations and the content in the full screen"*).

**vid64 round 1 narrowed it again:** *"the split screen looks weird, use the card format
instead."* vid64 and vid65 both shipped with **no split state in the file at all**, CARD only.
vid66's brief then asked for *"card + split"* by name and shipped a vertical column at x540-1080.
So the current reading is: **the card is the default return and the split is opt-in, per film,
on the creator's say-so.** Do not add a split that was not asked for.

**The one standing exception is a shot-for-shot reference copy.** vid67 shipped three mid-film
full-bleed beats and a horizontal seam at y700, because the instruction was *"do the exact same
editing"* and the reference cuts that way. A copy brief overrides the face law; nothing else does.

### 11. Real logos, and one cast per film

vid60 round 2: 24 providers and 11 fallback members rendered as monospace text in rounded pills
were called **"too shitty", twice, on two different beats.** The fix is real marks
(`cdn.jsdelivr.net/npm/@lobehub/icons-static-svg@1.91.0/icons/<name>.svg`, ~29 in one loop).
**Render every logo to one sheet and look at it before building:** a dead mark is worse than the
text it replaced.

Same round, same class: round 1 had the real Claude pixel sprite in the hook and a hand-drawn
white robot for the limit beat. The note named the hook; the fault was **two characters doing one
job**. One film, one cast. (Gotcha: the house sprite is `position:relative`, so an unpositioned
copy lands at flow origin, half off frame, reading as "it didn't render".)

---

## House rules confirmed on client films, and why they apply here

These three came off the `longform-chunked` and `fast-cut-ad` productions rather than this
template's own reviews. They are recorded separately on purpose: rule 8 above exists because a
motion grammar was ported from another template's file without checking where it came from. These
are process and copy rules, not camera grammar, and the source explicitly reasons about how the
first one lands for this template.

### Graphics are not the default. Showing the presenter is

Stated on vid56: reach for an animated overlay when it is carrying information that cannot come
from the presenter speaking (a number, a comparison, a mechanism). Do not reach for it to fill a
beat, and **never let it replace the presenter at the moment they are making the direct ask.**

The source records the per-template resolution explicitly: it still holds here, and *how* the
presenter is on screen at the CTA is the **card**. vid65 shipped with the CTA as a CARD beat,
never graphics-only. Two preconditions the client films added: an unwatchable shot at a smaller
size is still an unwatchable shot, so if the take is unusable for a span the picture comes OFF
rather than shrinking; and a face-safety pass that excludes a window silently removes the
presenter from a beat, so check the raw signal (a blink cluster padded into a 2.4s exclusion is
not a defect).

### A recurring complaint means remove the whole category, not tune the instance

The fast-cut-ad demo film, round 5: *"typing sfx"* survived three evidence-based fixes (literal
typing cues, then the whole click/tick family by measured attack, then the music bed's 0.465s
percussion grid) because the client was naming a sound **category**: any added effect at all. The
five notes landed exactly on the five surviving whoosh and impact cues, the ones every acoustic
measure said were not clicks.

**When the same complaint survives two evidence-based fixes, stop refining the classifier and
remove the class.** The correct move at round 2 was one question: "should ALL added sounds go, or
just the clicky ones?"

### On-screen copy is not build notes

vid62 short shipped three eyebrows through every gate as notes-to-self ("One beat of price, at the
end") and as third-person narration about the man in frame ("What he would tell a friend").
**Read every literal on-screen string as a viewer before the delivery render.** No gate has an
opinion about what the words mean.

---

## Face geometry

**Re-derived every take. Four distinct sets of numbers exist for the same person.** The formula
travels, the constants never do.

The head is large in frame (roughly 940 to 975px at native 1080x1920), far bigger than most takes
in this system, which is what kills a naive band:

- Solving `top + 380 = B` (cut at mid-forehead) against `top + 1020 <= 1580` forces **B <= 940**.
- As built on vid42: band top y920, video top 540, scale 1.0,
  `clip-path: inset(380px 0 0 0 round 44px 44px 0 0)`. Measured chin in the render: y1500.
- **Full-bleed width forbids scale < 1.0.** There is no more room in the source frame to zoom out
  into.
- For the floating card: the reference card's constants sliced the hair off when ported directly,
  because this head is about 975px against that reference's 600px. **Solve the card top from the
  head**: crown must clear the top edge and chin must clear y1600, which gave **960**. Measured:
  hair meets the card top at y960, chin y1540.

---

## The right rail bites these layouts specifically

Because the content sits low (see rule 4), the x960 rail is a lower-third problem here, not just a
caption problem. Lint, validate and inspect have all passed rows running to x1098 and x970 inside
the like/comment rail.

**Cheap guard**: after laying out any lower-third row, assert `left + width <= 950` for every
element in it. For a centred UI card, solve the width from the centre:
`width <= 2 * (960 - 540) = 840`.

---

## How review works on this template

Direct and specific, often mid-build. The creator adds scope in a useful way ("can you also try
3.js animation skills in this?", "can you add some relevant stock footage in this? Rest, all is
fine") and says which parts are fine, which makes the diagnosis easy.

**When the note says "rest is fine", add the new thing as a LAYER, not as scenes.** Stock footage
went in as a `z-index:4` ground above the ambient wash and below every designed panel: no beat
displaced, no layout moved, and about 11.5 seconds of the reel started reading as real.
