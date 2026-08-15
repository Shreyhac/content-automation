# paper-split: visual grammar

Current approved system: **vid47 v2, the paper split band**, with the band construction itself
refined by **vid50 v3 (2026-08-01): no scale, translate only.** Reference build:
`reference-builds/paper-split-vid47/`. The creator specified the split by sending a frame from
vid41 (hf41); the no-zoom correction is a standing instruction, not a one-off ("No need to zoom
his frame. Just keep the original frame.").

---

## The paper split band

Graphics on paper above, face in a rounded band below, **face on screen continuously**.

```
eyebrow   y168
content   y206 to y900
caption   y940 to y996        x130 to x950, clears the like/comment rail
band      y1080 to y1920      840px, 44% of the frame
```

```css
#faceBandBg{ top:1080px; height:840px; background:var(--paper2);
             border-radius:36px 36px 0 0; }
video.band { top:380px; width:1080px; height:1920px; object-fit:cover;
             clip-path:inset(700px 0 0 0 round 36px 36px 0 0); }
             /* the visible cut IS the band's own rounded edge */
```

**The technique is portable, the constants are not.** This has been true three separate times.
Re-solve the crop per take so the head fills the band and the chin clears y1600.

vid47's solve, as a worked example: `crop=1854:3296:36:212` on the master gives head 430px, face
centred x540.6, crown y1130, chin y1560, clearing y1600 by 40px.

**Re-solving for a re-shoot: fit the percentile, not the median.** vid47 v3 reused the script in
a new room; same head size (Vision face-width .242 vs .239) but the subject sat ~490px higher and
wandered vertically nearly twice as far. Reproducing take one's crop put the chin past y1600 on
11% of frames (approved cut: 2%). Search `(top, scale)` against a spread/percentile constraint,
never a median-only fit: widening to 0.95× (`crop=2036:3620:0:0`, `top:596`, clip inset `484`)
brought it back to 2.7% over.

Band top **y1080** rather than hf41's 1150 when the note is "show the face more": it took face
presence from 45% to 91%.

**A rounded band cut needs every layer to agree.** Round the clip *and* the band background to
the same radius, and delete any straight full-width edge line, or the corners mismatch and it
reads as "the rounded edges look off".

**Re-lighting a re-shoot: match the approved cut's measured stats, not your eye.** A new room
runs warmer/darker; solve `eq`/`colorbalance` against the old band's Y/U/V/SAT numbers. vid47 v3
landed Y 148.6 vs target 147.3, U/V within 0.1.

**A band top can be geometrically unreachable, not just wrong.** With crop scale `s` and top
offset `oy≥0`: `crown_out ≤ min(crownY·s, 1560 − (chinY−crownY)·s)`. vid50's master crown y1418,
chin y2176 gave a ceiling of crown_out ≤ 1016 at s=0.7166: no crop puts a high-sitting subject's
crown at hf47's y1130 (zoom raises the head; zoom-out isn't available past 1:1). Check this
inequality before laying out the graphics zone: a low ceiling means the graphics zone is bigger
than expected, and scenes should be designed for that, not retrofitted.

### No-zoom construction (vid50 v3), current preferred build

The owner's standing instruction ("No need to zoom his frame. Just keep the original frame.")
rules out the scale-based band above whenever the geometry allows it. Build the band as an
untransformed video plus an overlaid panel instead:

```css
video.band { top:170px; /* translate DOWN, not scaled */ width:1080px; height:1920px;
             object-fit:cover; /* scale stays 1 */ }
#panel      { top:0; height:820px; background:var(--paper2); border-radius:0 0 36px 36px; }
```

Solve from the same measurements as any band: crown-min + translate vs panel edge (vid50:
696+170=866 against panel 820, 46px clearance) and chin-max + translate vs y1600 (1126+170=1296,
well clear). This also removes the clip-path-local-space trap below entirely, since there's no
transform on the video to divide by. Compare both constructions on real frames before choosing:
no-transform (panel must clear the crown minimum directly, smaller graphics zone) vs
translate-down (bigger graphics zone, identical face size); translate-down is strictly better
whenever the subject has room to give at the bottom of frame.

**`clip-path` resolves in the element's local box, before any transform: a trap specific to the
scale-based version above.** With `translate(-145px,2px) scale(1.379)` on the band video,
`clip-path:inset(900px …)` clips at screen y1243, not y900: `local_inset = (screen_row − ty) / k`
(here `(900−2)/1.379 = 651`), same divide-by-k for the corner radius. This applies to any static
clip on a scaled element, and it's one more reason the no-zoom construction is preferred when it
fits.

---

## Palette and type

The Director's Desk paper world (ported from hf41, which the creator had already approved):

| Token | Value | Use |
|---|---|---|
| `--paper` | `#F3F1EA` | ground |
| `--card` | `#FBFAF6` | cards |
| `--ink` | `#101014` | type |
| `--go` | `#3CE6AC` | THE accent, strictly the GO semantic |
| `--goDeep` | `#0B7A57` | the accent as type, and on ivory where mint is invisible |
| alert red | reserved | held back, never decorative |

Solid fills and hairlines. No glow on type. No gradient display type.

| Role | Face |
|---|---|
| Display | Clash 600/700 |
| Body and captions | Satoshi 500/700/900 |
| Labels | Geist Mono |
| Second voice | Instrument Serif italic, rationed |

**Cap simultaneous type voices at two per block.** Clash + Instrument Serif + Geist Mono + a pill
in one 700px block drew "font is very off" on vid50; cutting to two voices fixed more than any
size change did. Clash also eats its own word spaces at high tracking:
`letter-spacing:-.045em` collapsed "Your AI keeps" into "YourAIkeeps" at 112px; ease to `-.03em`
with `word-spacing:.16em`, and treat 92px as the practical ceiling before a serif sub wraps a
second line.

**Light and white brand marks vanish on paper.** Simple Icons takes a hex
(`cdn.simpleicons.org/coolify/101014`); where the published SVG is white, rewrite its own
`fill="white"` to ink rather than filtering it. **Verify by rendering every mark on the actual
card colour in one headless page before wiring them in.** Three shipped as blank tiles once.

**A paper wipe on a paper ground is an invisible cut.** Wipe colour must contrast the scene it
is covering, not match the world: the deep green wipe is the one that works here.

---

## Type over full-bleed footage

**A safe zone is not a ground.** Clearing every Instagram safe zone is necessary, not
sufficient: vid50's hook type cleared every zone and still failed ("text is not visible")
because it sat directly on wall art, crossing a green painting and a picture frame's brown edge
and changing contrast *inside one word*. On full-bleed footage, display type needs its own
surface (a paper panel in the film's world), not merely empty-looking pixels.

**Panel depth comes from the crown's highest point across the whole window, not its value at the
cut.** A punch-in or handheld drift can move the subject after the frame you designed against:
vid50's crown was y860 at the cut but reached y696 by t=1.5s under the source's own punch-in.
Take `min(crownY)` over the clip and subtract a margin.

**A 12%-alpha pill over a bright wall is invisible.** Any claim pill sitting directly on
full-bleed footage needs a solid `--card2` fill, not a tinted one; save the tinted pill for
scenes already on the paper ground.

**On a HOOK, "I need animations, not just text" means show the claim's subject in a correct
state at frame 0, then break it on the physical gesture**, not add kinetic type. vid50 held
three brand outputs consistent at t=0 and broke them into their own palette/typeface on the
exact frame the laptop lid shut, which also pre-built the payoff for the beat where they rebuild
in register later in the film.

## Motion language for a "wrong" or corruption beat

vid50 round 2 ("this animation is weird") replaced arbitrary tilt + linear drift with rules that
now apply to any beat expressing "broken" or "wrong":

1. **Never rotate.** Arbitrary tilt is the cheapest chaos signal and the first thing that reads
   unpolished.
2. **Never drift linearly.** Every move gets a settle (`power4.out`) and then holds.
3. **Keep the grid, corrupt the content.** Geometry stays aligned; palette/typeface/value go
   wrong instead, and that's usually also the literal claim.
4. **One designed gesture beats N independent random ones** (a single sweep crossing the row,
   each element snapping as the sweep reaches it, beats a set of unrelated per-element drifts).
5. **Repeat it, don't sustain it.** Re-roll once more on a stagger instead of holding a broken
   state for seconds.

**"Better animations at the start" is usually the first ~0.6s being a still frame.** Fix without
breaking the frame-0-cover rule: keep every element present at frame 0 and move them *in
register* (a shared ink-scan / pulse crossing all of them) so the opening shows the system
working, which gives the later break something to mean.

**GSAP gotcha:** only the FIRST beat of a repeated move may be written as `fromTo`: every
`fromTo` on the same target pins its "from" state back to t=0, so three pulses written as
`fromTo` collided in [0, 0.08] and tripped `overlapping_gsap_tweens`. Subsequent repeats must be
plain `to`.

---

## One persistent object, not a scene per beat

The structural idea a fast listicle needs:

> **Rhythm from a constant carrier, variety from the event under it.**

Ten beats averaging 2.4s cannot each invent a layout, and ten identical cards is exactly the
"cheap" failure. The answer on vid47: one **identity strip** opening every beat the same way
(`01` chip · real logo tile · name · `owner/repo · LANG · LICENCE` · `★ 59.8k`) over a ten-tick
progress rail, with a completely different physical event beneath it each time.

The ten rows exist for the whole 24.5s as **one accordion**. The spoken **name** opens its row and
the list slides so the open row pins to the mask top; the spoken **predicate** lands the stamp on
that row's real screenshot. **Two moves per beat, each tied to a specific word.** That is what
"the animation doesn't sync with what we're saying" actually asks for. A card fading up while a
name is spoken is not synchronised, it is merely simultaneous.

Two mechanics:

- **Solve the whole stack from one formula every beat, never nudge it.**
  `topOf(j,n) = j<=n ? j*PITCH : n*PITCH + OPEN + GAP + (j-n-1)*PITCH`, applied to all ten rows
  plus `list.y = -(n*PITCH)`. The first build pushed rows down and never brought them back, so by
  beat 7 the open row was half off the mask.
- **A scrolling mask needs `data-layout-ignore`, not `data-layout-allow-overflow`.** The
  `clipped_text` rule fires on the mask regardless of allow-overflow, which is correct for a text
  box and wrong for a viewport.

---

## Face cadence

**FACE, GFX, GFX** on a listicle: face beats at items 1, 4, 7, 10 plus hook and CTA. The cycle is
what stops a ten-item list reading as a slideshow.

That was v1 at 45% face share. v2's split band pushed it to **91% presence**, because the band
keeps the creator on screen continuously while the graphics zone changes. Both are approved
shapes; the split band is current.

---

## three.js

Clip the canvas to the graphics zone **permanently** (`inset(150px 0 1010px 0)`). A loose field
drifting across the face reads as dirt on the lens.

Re-lighting for paper is a full inversion: pale ceramic body (`0xE6E2D8`, metalness .04,
roughness .72), ambient up to 2.35, and the state colour moves to the **deep** green because mint
is invisible on ivory.

See `playbooks/threejs.md` for pack density, per-layout X scale and the flipped-instance trap.

---

## Superseded systems

Kept because older reference material still shows them. Do not build in these.

| System | Where it came from | Status |
|---|---|---|
| Pixel / gamified world | vid5, vid6 | Retired, "childish" |
| Espresso dark | vid6 v2 | Retired, "very weird" |
| Warm-ink triple radial ground | vid19 r2 | Superseded by paper |
| Anton all-caps supers | vid10, vid11 | Superseded by Clash + Satoshi |
| Fraunces + Poppins paper | vid20 r2 | Superseded by Director's Desk paper |
| Handheld POV template | vid33 | Specific to that build |
| Studio Void dark | vid35 | Subject-specific (ElevenLabs) |
| Three-band layout | vid43 | Still valid where the subject wants a dark world |
| GitHub-dark | vid47 v1 | Rejected, "too coded" |
| Scale-based band fill (`crop`+`scale(1.379)` on the band video) | vid47 v2 to vid50 v2 | Superseded by the no-zoom translate construction, vid50 v3 |
