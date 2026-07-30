# shreyansharora05 (the "slot 1" creator)

A different person from thepmfguy/gaurav. Older files call him "slot 1" after the folder his
A-rolls arrive in.

| | |
|---|---|
| Format | 9:16 Instagram Reels, 30 to 40s |
| Subjects | AI product launches, prompt and workflow tips |
| Setting | Seated indoors, tight close-up, a lit wall and a large action figure in the lower third |
| Current grammar | vid42 v3: face-led open into the floating card, three.js as a recurring object. Reference build: `reference-builds/shreyansh-vid42/` |

---

## Hard rules

### 1. Do not show his face too much

"No need to show my face too much, only at important lines and with split screen."

The shape that landed: a **1.4s full-bleed open**, then card beats at the important lines. Four
card beats plus the short open reads as "present throughout" at about 30% face share, with no
full-bleed talking stretch after the hook.

### 2. The floating card is approved. A full-width lower-third slab is NOT

He approved one and rejected the other **in the same reel**. The distinction is real:

> A card is a **frame**: the subject is deliberately placed inside it.
> A bottom slab is a **cover**: something has been laid over the subject.

An 11.5s face-led opening with a full-width dark panel under his chin was "very weird"; the
floating card was "this format is good".

**Rule: on a full-bleed face, graphics either sit in self-grounded chips or they do not exist.
Never a full-width ground.**

### 3. A short face intro needs composed furniture, not entrances

At 1.4s there is no room for elements to arrive. Corner brackets, a status chip and a scan sweep,
with the brackets and chip **already present at t=0** and only settling (scale, letter-spacing).
Frame 0 is the Reels cover: an element that starts at 0.06 is an element the cover does not have.

### 4. No headroom means no top lockup

His crown sits near y45 in a native close-up. There is nowhere above the head for a title, so a
face-led opening puts **everything** in y1064 to y1380. That band then dictates type sizes:
roughly +30% over what reads fine on a designed dark scene, because it competes with skin and
motion behind it. Landed at 104px display, 27px instrument labels, 24px mono.

### 5. His lower third needs a hard panel, not a soft scrim

A lit wall and a large action figure sit behind him. A `radial-gradient(.90 to 0)` left every
graphic washed out and effectively illegible. What works:

```css
linear-gradient(180deg, transparent 0%, rgba(...,.50) 17%, rgba(...,.90) 22%, rgba(...,.93) 100%)
```

from about y820, plus a hairline at the join. It also reads as a deliberate device rather than a
fix.

### 6. Match the raw A-roll's file size on delivery

Same standing rule as gaurav. See `docs/06-delivery.md` step 3.

### 7. No em dashes

---

## Face geometry

**Re-derived every take. Four distinct sets of numbers exist for the same person.** The formula
travels, the constants never do.

His head is large in frame (roughly 940 to 975px at native 1080x1920), far bigger than most takes
in this system, which is what kills a naive band:

- Solving `top + 380 = B` (cut at mid-forehead) against `top + 1020 <= 1580` forces **B <= 940**.
- As built on vid42: band top y920, video top 540, scale 1.0,
  `clip-path: inset(380px 0 0 0 round 44px 44px 0 0)`. Measured chin in the render: y1500.
- **Full-bleed width forbids scale < 1.0.** There is no more room in the source frame to zoom out
  into.
- For the floating card: the reference card's constants sliced his hair off when ported directly,
  because his head is about 975px against that reference's 600px. **Solve the card top from the
  head**: crown must clear the top edge and chin must clear y1600, which gave **960**. Measured:
  hair meets the card top at y960, chin y1540.

---

## The right rail bites his layouts specifically

Because his content sits low (see rule 4), the x960 rail is a lower-third problem here, not just a
caption problem. Lint, validate and inspect have all passed rows running to x1098 and x970 inside
the like/comment rail.

**Cheap guard**: after laying out any lower-third row, assert `left + width <= 950` for every
element in it. For a centred UI card, solve the width from the centre:
`width <= 2 * (960 - 540) = 840`.

---

## How he reviews

Direct and specific, often mid-build. He adds scope in a useful way ("can you also try 3.js
animation skills in this?", "can you add some relevant stock footage in this? Rest, all is fine")
and he says which parts are fine, which makes the diagnosis easy.

**When he says "rest is fine", add the new thing as a LAYER, not as scenes.** Stock footage went
in as a `z-index:4` ground above the ambient wash and below every designed panel: no beat
displaced, no layout moved, and about 11.5 seconds of the reel started reading as real.
