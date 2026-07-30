# gaurav: visual grammar

Current approved system: **vid47 v2, the paper split band.** Reference build:
`reference-builds/gaurav-vid47/`. He specified it by sending a frame from vid41 (hf41).

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

Band top **y1080** rather than hf41's 1150 when the note is "show the face more": it took face
presence from 45% to 91%.

**A rounded band cut needs every layer to agree.** Round the clip *and* the band background to
the same radius, and delete any straight full-width edge line, or the corners mismatch and it
reads as "the rounded edges look off".

---

## Palette and type

The Director's Desk paper world (ported from hf41, which he had already approved):

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

**Light and white brand marks vanish on paper.** Simple Icons takes a hex
(`cdn.simpleicons.org/coolify/101014`); where the published SVG is white, rewrite its own
`fill="white"` to ink rather than filtering it. **Verify by rendering every mark on the actual
card colour in one headless page before wiring them in.** Three shipped as blank tiles once.

**A paper wipe on a paper ground is an invisible cut.** Wipe colour must contrast the scene it
is covering, not match the world: the deep green wipe is the one that works here.

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
keeps him on screen continuously while the graphics zone changes. Both are approved shapes; the
split band is current.

---

## three.js

Clip the canvas to the graphics zone **permanently** (`inset(150px 0 1010px 0)`). A loose field
drifting across his face reads as dirt on the lens.

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
