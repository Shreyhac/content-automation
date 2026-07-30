# shreyansh: visual grammar

Current approved system: **vid42 v3.** Reference build: `reference-builds/shreyansh-vid42/`.

---

## Structure

```
0.00 to 1.40   full-bleed face, composed at t=0, furniture settles (no entrances)
1.42 onward    card beats at the important lines; designed scenes carry the rest
```

Four card beats plus the short open. Face share about 30%, reading as "present throughout" with
no full-bleed talking stretch after the hook.

**Put the announcement where the claim is spoken.** A rebuilt X card playing under the line that
makes the claim means the source of the claim arrives exactly as the claim is made. A cascade that
reads in 1.9s: card spring, head, line 1, line 2, media, pill, meta, action row, with the view
count and the heart landing last.

---

## The floating card

One face element tweened between states, never cut between them:

```
HERO  inset(0.1px 0.2px 0.3px 0.4px round 0.5px)
CARD  inset(<solved>px ... round 32px)     video at scale .6, transform-origin 50% 0%
OFF   collapses INTO the card's own rect, so a card-in grows from where the card belongs
```

**Every number must stay non-collapsible.** Browsers collapse `inset()` shorthand when
serializing computed clip-path (`left == right` gives three values, `round 0px` is dropped
entirely), and GSAP interpolates the raw strings by number index. A five-number target against a
collapsed four-number start shifts every later slot, which once animated a 32px corner radius
inside the left inset and painted a 200px dark slab through every card open and close. Hold frames
were pixel-perfect; only transition frames broke, which is why every gate and every beat-frame QA
passed.

Use slightly distinct insets (216.1 against 215.9) and never a 0 radius (0.5px reads as square).
Verify with a seek probe reading `getComputedStyle(...).clipPath` at mid-transition times: a
mispair shows up as a radius-sized number in an inset slot.

**Do not pixel-scan for the dark slab.** It false-positives on dark wardrobe and furniture in the
footage itself.

**No scale-breathing on a clipped video.** `clip-path` resolves in element space *before*
transform, so any scale drags the card edge. The A-roll's own motion is enough life.

---

## Theme

Per subject, as always, but grounded in **his own room lighting** rather than invented. vid42's
violet was sampled from the light on his wall, which is why the same launch produced an
unmistakably different reel from gaurav's cut of the same story.

Two creators covering one launch reused the entire asset pool verbatim. The differentiation is
theme, type stack and scene grammar (machine events against rebuilt post cards), not facts.

---

## three.js as a recurring object

Used on exactly **two beats** in vid42: the hook (a rigid machine lattice collapsing into a
waveform-modulated voiceprint sphere on "your actual voice") and the analyzer's output sigil (the
same cloud re-forming from scatter inside a DOM instrument bezel).

**The object recurring is what makes it feel designed rather than decorative.**

**A DOM bezel around a WebGL core is the strongest hybrid.** The ring, tick marks and label are
crisp CSS; only the thing inside needs to be 3D.

Sizing is arithmetic, not taste. See `playbooks/threejs.md`. One round shipped a sphere about
1670px across that swamped the title and ran under the captions, and a lattice so dark the Reels
cover read as empty.

---

## Scene grammar: machine events

His reels read as instruments doing work rather than cards presenting information. The vocabulary:
dials with needles that hunt before they stall, capsules descending tracks through gates,
ampoules filling, tokens routing, pods ejecting and returning along dashed paths. Type survives
as instrument labels.

**Three saturated hues with one job each is not a multi-colour wash.** The ban is on gradient
display type and glow on *type*, not on saturation. A lab instrument is allowed emissive glow on
its own hardware.

---

## Transitions

**Do not wipe where the VO has no gap.** Retime every transition against the word list: wipes
survive only where the gap is at least about 0.18 to 0.20s, and everywhere else becomes a flash
cut. Where the VO is continuous, a wipe simply eats the caption it lands on.

---

## Captions

- **Give each caption its own `top`.** Once the face moves into a card, captions can no longer
  live at one fixed y: around y1380 while a panel hides the face, around y760 in hook and CTA
  where it does not.
- **A big lockup and a caption saying the same words is one element too many.** vid42's hook runs
  caption-free for 3.28s and the lockup carries it.
- **Counters step on the event, do not tween to it.** `count()` with an ease read "3 / 3" while the
  second of three cards was still in flight. Use a discrete `tl.call` per landing.
- **`ghost()` at 0.13 opacity is invisible on a black ground; 0.22 reads as pending.**

---

## Stock footage, when asked for

Add it as a **ground layer** (`z-index:4`, above the ambient wash, below every designed panel) so
the approved structure does not move. `blur(7px) brightness(.44)` at opacity .52, each clip with a
slow counter-drift.

- **"Relevant" means it connects to the line it plays under.** One clip per claim, not generic
  technology footage.
- **Grade at the ffmpeg stage, not in CSS.** CSS filters cost render time on every frame and are
  harder to tune per clip.
- **Exposure is per-clip, never per-layer.** Three dark booths and one white-wall clip at a shared
  setting washed out the whole scene. A shared filter is an assumption that the plates are exposed
  alike. Frame-check each plate separately.
- Refuse anything that would misrepresent the product: real singers' faces on a card representing
  AI voices, for instance.
