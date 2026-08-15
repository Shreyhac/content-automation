# vid62-short assets manifest

The current longform-chunked vertical. Nine beats cut out of a finished long-form with **no new recording and
no new transcription**, alternating split-screen and card states, with the card collapsing inside
its own rect.

Shipped result: `reference-cuts/longform-chunked-vid62-incogni-short.mp4` (720p proxy).
Delivered original `out/vid62-short.mp4`: **1460 frames, 1080x1920 @ 24000/1001, 27.9 Mbps,
60.894167s, 214.3 MB**, audio **-14.0 LUFS integrated, -0.9 dBTP, LRA 4.3**.

Ships here: `index.html`, `package.json`, `beats.json`, `caption.md`, the solver, the bakers, the
caption builder, six guard scripts and `assemble_short62.sh`.

**Which HTML is canonical.** There is exactly one, `index.html`. It is the file that rendered
(mtime 12 Aug 00:08, render started 00:09, 1460 frames verified by the assembler before it would
concatenate). Note that its `<title>` and the header comment in `assemble_short62.sh` both still
say **1432 frames**, left over from the round-1 cut. The `FRAMES=1460` constant in the assembler
and `total_frames` in `beats.json` are the live numbers. Believe those.

Because this project was scaffolded from `hf59s/`, it also carries that film's solver, prover and
assembler (`solve_short59.py`, `proof_short59.py`, `qa59s.py`, `assemble_short.sh`). Those are not
shipped here. The `62`-suffixed files are this film's.

---

## The single source of truth, `beats.json`

Nine beats, each with its source range, frame count, visible spans, solved crop, state and chunk.
The bakes, the captions, the VO splice and `index.html` all read it. **The timeline is defined in
frames**, never in seconds.

| # | id | state | from | frames | line |
|---|---|---|---|---|---|
| 1 | b1 | band | c1 | 146 | the hook: type your own name into Google |
| 2 | b2 | band | c1 | 179 | what you just found: address, phone number |
| 3 | b3 | band | c1 | 152 | a broker site you have never heard of |
| 4 | b4 | band | c3 | 259 | 750 registered broker groups (PRC and EFF) |
| 5 | b5 | card | c12 | 204 | Incogni requests and re-requests removal, 420+ sites |
| 6 | b6 | noface | c13 | 163 | the exposure scanner |
| 7 | b7 | band | c17 | 113 | the recommendation, to camera |
| 8 | b8 | card | c17 | 100 | the code and the discount |
| 9 | b9 | closew | c18 | 144 | the close, full width, captions only |

Beat boundaries in the composition, never rounded: `0.000000, 6.089417, 13.555375, 19.894875,
30.697333, 39.206458, 46.004292, 50.717333, 54.888167, 60.894167`.
Picture-off points inside a beat: `b2 9.589417, b4 22.224875, b5 33.187333, b8 53.027333`. One
place it comes back mid-beat: `b3 14.175208`.

---

## A-roll, `assets/b1.mp4` through `b9.mp4` (8 baked clips, b6 has none)

**The master can be gone and you can still cut.** `vid62/master.mov` was deleted and its drive
unmounted. The long-form's own chunk assets, `hf62/assets/aroll/c*.mp4` at **59.8 Mbps**, ARE the
master in eighteen pieces. Check that no beat straddles a join, then seek `beat.a - chunks[c].t0`
into one file. Assert containment rather than trusting it. The `chunk` column above is which piece
each beat came out of.

Baked crops, not CSS transforms: `bake_short62.py` writes each beat at its final size so the
browser never resamples. Bake constants for the eight band/card clips: **scale 0.42218, output
1080x760, crown always on bake row 34.**

`libx264` with `yuv420p` exits 187 on odd bake dimensions. Round every computed bake width and
height to even, and derive placement from the rounded value.

### The zone map, and the constants every state shares

```
y150   graphics zone      x70 to x960 (890 wide; 70+890 lands exactly on the rail)
y640
y674   caption band       the middle band, on bare ground
y826
y838   the picture
y1574
y1600  Instagram UI band  reserved, LIT, never occupied
y1920
```

One camera for both band and card: `scale 1, x 0, y 838`, on a `#faceCam` of 1080x760. They differ
**only by clip-path**, so the presenter's head is the same size in both and the change between them is a widen,
not a resize.

| State | clip-path |
|---|---|
| `band` | `inset(838px 0px 346px 0px round 0px)` |
| `card` | `inset(838px 260px 346px 260px round 30px)` (560 wide, x260 to x820) |
| `bandOff` | `inset(1574px 0px 346px 0px round 0px)` |
| `cardOff` | `inset(1574px 260px 346px 260px round 30px)` |

**`cardOff` is round 2's main repair, and it is the whole reason this build earns a slot.** A
single shared `off` state collapsing to `inset(1574 0 346 0)` animated the left and right insets
from 260 to 0, so a picture leaving a CARD **widened to full frame on the way down**, sliding a
full-bleed strip of the presenter's neck out past an empty card border. That one fault was BOTH of the client's
"glitchy / weird transition" notes. **A card has to collapse inside its own edges**, and the card
frame (`#faceFx`) has to fade WITH the picture rather than outliving it as an empty rectangle.

**At a hard cut the state is SET, never tweened.** Round 1 tweened across every cut, so the wipe
cleared while the picture was still growing into place. A wipe exists to hide a swap; if the swap
outlives the wipe it is not hidden. `faceTo()` is for a move INSIDE a beat only.

### Solving the crop, `solve_short62.py`

- **Solve over the spans the presenter is VISIBLE in, not over the beat.** Five of nine beats show the presenter for
  only part of their runtime, and a beat-wide median is a median over frames nobody sees.
- **Centre on the MEDIAN head position, not the midpoint of the presenter's extremes.** Extremes-centring
  maximises the smaller margin, which answers "will the presenter's face leave the rect" and not "does this
  look centred". One 0.4s lean dragged a card 55px and the presenter sat off-centre for the whole beat. The presenter's
  note was "this is not centered aligned". If median centring then breaches `FACE_MARGIN`, the beat
  cannot be a CARD and plays as a BAND.

### b9, the close: `closew`, not a full-bleed

The client asked for "full screen". A true 1215px-wide 9:16 window put **43px of the presenter's cheek outside the
frame on both sides with the presenter's chin at y1601**, inside the UI band. The presenter's head measures 1371x1110
source px and the presenter sways 274px over this beat. The first pass at scale 0.75 left only 44px between
the presenter's face and the screen edge at the presenter's widest lean.

Shipped instead as a full-WIDTH picture: **1588x2160 of the source, scale 0.68, to 1080x1468 at
y106 to the same y1574 floor every other beat uses.** Whole head, caption under the presenter's chin. Cropping
the presenter's head is the defect this client has raised most often.

### The lighting device, not a grade

The set puts a lit "incogni" wordmark on the TV behind the presenter's head and the band crop cuts it into
fragments ("ncog", "coa", "inco"), which read as broken type rather than as branding. `#faceCam
.lift` is a radial centred on the presenter's face that pushes the fragments and the practical lamps at both
edges down into ambient, plus a 34px `.wall` gradient at the top of the bake where the band edge
crosses the bright wall. **The presenter's footage is baked with no curve, no eq and no saturation touch
anywhere.** Never grade the presenter's A-roll.

---

## Screen recordings, `assets/rec/` (11 present, 4 used)

`p9-list`, `p3-activity-s`, `p5-scanner`, `p1-resubmit`, cut by `build_rec_short.py` from the
long-form's Incogni dashboard captures.

Both dashboard placements **corroborate the line they sit under**: the request-status strip reads
Jul 16 to Oct 14 2026, which is 90 days to the day and exactly the cadence the presenter states in the same
sentence; the activity log scrolls named brokers each marked "has completed our removal request"
under "over 245 million removal requests". The broker-overview panel the long-form uses at c8 is
deliberately NOT here: it reads "37 brokers covered", the count from the presenter's own account, twenty seconds away
from the short claiming "over 420 unique data brokers". On screen together that is a viewer's
contradiction.

**The long-form's crops do not work here and the reason is arithmetic.** Those are framed for a
3840-wide delivery. This short is 1080 wide and its graphics zone is 890, so the c8 strip's 2676
source px would land at 0.33x and its 24px labels would render at 8px. Every crop is re-solved to
put source text at **0.7x or better**: 1620 to 890 for the strip (15px labels), 1220 to 890 for the
log (17px). Cropping tighter is also what keeps the strip safe, since the full-width version
reaches past "Data removed" into the first personal value line.

`pii_guard.py` reads the manifest `build_rec_short.py` writes.

---

## B-roll, `assets/broll/` (8 present, 2 used)

`conveyor.mp4` and `archive.mp4`, carried from the long-form already graded. The other six
(`coins`, `desk`, `forms`, `racks`, `shelves`, `warehouse`) are in the pool and unused in this cut.

---

## Brand marks, `assets/brand/` (8 files, 1 used)

The short uses `incogni-white.svg` only. `assets/brand/SOURCES.md` in the working project records
where each mark came from and the traps: Optery's brand blue `#4D81F1` is near-identical to this
film's Incogni accent, so it must be used with `alt="Optery"` or `base.css` will not grey it and
the competitor ships in the sponsor's colour. Incogni's own site serves no self-logo SVG.

---

## Fonts (4 used, all in `library/fonts/`)

```
rethink-sans-var    display and all numbers
dm-sans-var         captions and body
geist-mono          labels
fraunces-italic     the rationed second voice
```

`assets/fonts/` in the working project carries eleven; the other seven are donor leftovers.
`@font-face` is declared inline in the document, not only in a shared stylesheet.

---

## SFX, `assets/sfx/` (74 in the pool, 27 cues placed)

Volumes for this client after three rounds: **minimum 0.050, median 0.064, ceiling 0.082.** The client
halves it every time they say "loud". These are roughly a quarter of the house range.

---

## Audio, and the two ways it went wrong

The render supplies **picture only**. `assemble_short62.sh` rebuilds the audio beside it from
`hf62/assets/vo-master.wav`, cut at the same eight frame-derived ranges the picture was baked from,
so the two cannot drift. It refuses to run unless the newest render is exactly 1460 frames.

- **`afade=t=in:st=X` silences everything BEFORE X.** Meant as 45ms on one beat's head, applied to
  the assembled VO it muted **46 of 61 seconds**. The assembler's own loudness print caught it:
  LRA 4.4 to 25.6 LU. Absolute-time filters belong on the segment, never on the assembled track.
- **"The audio cuts weird here" is usually a script fault.** Transcribe 1.6s either side of the
  join in isolation first. Both of the client's audio notes were clean at signal level: one cut the presenter's sentence
  mid-list, the other opened a beat on a dangling "And" bridging topics 68 seconds apart. The fixes
  were editorial and they traded against each other, +3.7s and -2.8s.

---

## Captions

`build_short_captions.py` writes 30 caption divs into `index.html` between markers.

**A `re.sub` that matches nothing returns the input and your script prints success.** Round 1's
injection consumed its own `<!-- CAPTIONS-BEGIN -->` markers, so round 2's injection silently
no-opped and a full render shipped **round-1 captions**, up to 3s out of sync and on the wrong band
at the close. Assert the delta. Never print unconditionally.

**Read every on-screen string as a viewer before the delivery render.** Three eyebrows went through
every gate as build notes to self ("One beat of price, at the end") and as third-person narration
about the presenter in frame ("What he would tell a friend").

---

## The guards

| Script | What it measures |
|---|---|
| `safe_zones.py` | top 150 no text, y1600 no text and no face, x>960 between y900 and y1600 no text, left 60 no text, all re-audited against this film's numbers |
| `paint_guard.py` | what actually paints, not what is merely positioned |
| `snap_guard.py` | state changes land on cuts, not across them |
| `motion_guard.py` | a "screen recording" that is actually a still |
| `audio_guard.py` | the assembled bed against the plan |
| `pii_guard.py` | personal data in the dashboard crops |
| `proof_short62.py` | the per-beat proof sheet (three frames per beat) |
| `shoot.py` | the contact sheet |

---

## Regenerating

```bash
python3 solve_short62.py          # geometry from the long-form's crown.csv / facebox.csv
python3 bake_hero.py              # the hero bake
python3 bake_short62.py           # eight beat clips + the b9 close, even dimensions enforced
python3 build_rec_short.py        # the two dashboard placements + the PII manifest
python3 build_short_captions.py   # 30 captions, delta asserted
python3 safe_zones.py && python3 paint_guard.py && python3 snap_guard.py \
  && python3 motion_guard.py && python3 pii_guard.py
python3 shoot.py && python3 proof_short62.py
npx hyperframes render -q high
bash assemble_short62.sh          # asserts 1460 frames, then rebuilds the audio
```

Inputs that do not ship here: `hf62/assets/aroll/c*.mp4` (the long-form's 18 A-roll chunks, which
are the master), `hf62/assets/vo-master.wav`, and `vid62/crown.csv` / `vid62/facebox.csv` /
`vid62/camera-windows.json`. All of those still live in the working repo. `vid62/master.mov` is
gone and is not recoverable.
