# Nader: shipped work and what each round changed

Newest first. **The most recent approved grammar supersedes older entries.**

> **Open before you start.** Two client notes on vid46 have never been answered. See
> "Round 4" below and `open-notes/`.

---

## vid62, Incogni ep5 comparison, sponsored 16:9 long-form (hf62/, date not stated in source)

v1 passed every structural gate (`lint`, `validate`, `card_guard`, `dead_guard`, `css_guard`) and
was queued to render with defects none of them could see. Full detail in `vid62-breakdown.md` §8.

### A gate that has never run is not a gate
- `pii_guard.py` read a `rec-placements.json` that the recording builder never wrote. **On a film
  about published home addresses, the privacy gate had never executed once.**
- `css_guard.py` was hardcoded to `c1..c11` from an earlier chunk count.
- `card_guard.py` defaulted to `["c1"]`, one clean chunk reading as a film-wide pass.
- `band_guard.py` was correct and had simply never been run; four chunks printed graphics under
  the caption band.
- Playwright's browser binary was missing, so every DOM gate was crashing, not checking.

**Derive gate scope from the plan (`chunks.json`), never a literal. Print what a gate actually
measured, not just its verdict.**

### Two ways to write a beat against the wrong chunk clock
Scheduled past the chunk end: the tween never runs, the element sits staged at `opacity:0`, c2
held one still frame for 17s. Scheduled before the chunk start: GSAP does not clamp, it **shifts
the whole timeline**, c7 landed 1.272s late across the whole chunk. `sched_guard.py` now checks
every `L(x)` against `[t0, t0+dur]` across the whole script, not just direct `tl.*` calls
(`K.settle`/`K.cut` wrap `tl.*` inside `chunk.js`, and that hole hid the worse of the two bugs).

### A `<video>` revealed outside its own scheduling window renders BLACK
Every recording placement was surfaced by `autoAlpha` instead of by scheduling, true of the DOM,
false of the renderer. **Seven of nine dashboard placements rendered black**, on the film whose
brief was "add the actual screen recordings more." Fixed with explicit local-second scheduling
plus `rec_sched_guard.py`. Also: default punch-in `scale=1.35` cut every line of on-screen text
in half; `1.05` keeps words readable.

### The filesystem needs its own gate
`hf62/assets/shots/` did not exist: c10's 13.3s Krebs-article beat rendered as a blank white card,
invisible to any structural gate because the CARD paints and only the `<img>` inside it is 0x0.
`asset_guard.py` now resolves every referenced path on disk, and preflight frame-counts every
A-roll and probes every recording (five clips were truncated with no moov atom, and `-s` passed
all of them).

### Compressed staggers are what "boring" means, measured
`motion_guard` read **71% held**, worse than vid59's 66% ("very boring b roll, need better
animations"). Cause: `stagger:.16` brought six cards in inside one second while he spent 6.7s
naming them, then held 8.4s. Rebuilt onto word onsets: 264.4s to 208.2s held (71% to 56%),
longest hold 17.0s to 4.2s. Also: `borderColor`/`boxShadow` tweens register as nothing in a
motion fingerprint (id, rect, opacity, transform) and are barely visible on screen; use lifts,
scale pulses and opacity reveals instead. An `ALLOW` exemption inherited from an earlier chunk
plan blanket-exempted c15 for its entire duration (hiding 15.8s of real stillness) while a stale
c14 entry matched nothing. **Re-derive exemptions per film, from measurement.**

## vid62 round 2, the owner rejected v1 for framing, and he was right

*"framing is off, Nader's face is not in frame, text is on Nader's face, animations are later, a
lot of weird stuff."*

v1's own frame QA had sampled about 13 frames at 640 to 760px inside 3x3 tiles, a smoke test too
coarse to judge framing at all. Round 2's method: a 2fps sweep of the delivery (746 frames) with
face detection on every one.

### A gate that runs in only one MODE is not a gate
`card_guard` enforced the graphics/card split only while the face was carded. In full-bleed there
was no card edge, so nothing checked anything, and elements were placed by eye into the band where
he actually sits: **180 frame-hits of text on his face across 23 elements**, a promise rail across
his chin (22% of his face), OneRep caveats across his mouth (15%), two headlines across his neck,
the CTA on his chest.

`facesafe_guard.py` closes it against the SOURCE face track (full-bleed means the A-roll paints
1:1, so it's checkable in seconds instead of after a 25-minute render). Getting the measurement
right took three passes: box for painted elements, glyph rects for bare text (a centred headline
has a full-width box but its ink sits dead centre), and skip frames where a full-frame cover is up.

**Do not card the face just to clear it.** The obvious fix, card him so graphics own a half,
cleared his face and emptied the other half of frame. Caught only by screenshotting the
composition before rendering. Fix instead: keep him full-bleed, confine graphics to the
measured-safe column (his contour spanned x938 to x2568, so LEFT under 900 / RIGHT over 2600,
solved per chunk). **The top band is not automatically safe either, his hair sits in it.**

### validate cannot see contrast over an A-roll
It compares text to its declared CSS background; over video the real ground is his room. Hid 22
bare-text elements, including every eyebrow in the film. `contrast_guard.py` now uses the
**fraction of area brighter than about 150, not the mean** (white type on a mostly-black screen
averages dark while still colliding, mean rated "60% OFF" fine, bright-fraction measured 59.6% and
it was unreadable), and only treats a background as a ground when its alpha is at least 0.8.

Also: `.fig{position:absolute}` inherited in `base.css` from an earlier film collided with this
project's own `figure()` helper of the same name, printing "420+" on top of its own label for a
whole beat, invisible to lint/validate, found by measuring child boxes. And `pichash` hashed
`chunk.js`/`base.css` but not `vid62.css`, which holds most of the film's look; a fix there would
have shipped without ever re-rendering.

"Animations are late" was not a sync offset: whisper onsets vs audio-energy rise across 913 words
measured median **minus 25ms** (marginally early). What reads as late is sparse frames, one small
card in a large empty frame every 2 to 3s feels laggy even landing exactly on its word.

### The finding that explains round 3
`hf62/assets/base.css` is vid58's device kit, copied wholesale (514 lines against 512): `.trail
.plate .wcard .bcard .chip .stair .mark .pull .attrib .nostamp .dash .srch`, each already
documented with its own fixed bugs. **vid62 used zero of them, across eighteen chunks**, building
bespoke dark rounded boxes instead. That is the entire content of *"only a text-based thing is
really too shitty"* and *"we have been doing better in the previous ones."* **Before writing any
scene CSS in a scaffolded project, list what the kit already defines against what the chunks
actually use; if the second list is much shorter, stop and read the kit.**

## vid62 round 3, the rebuild on the existing kit

Rebuilding one beat with the kit took about twenty minutes and landed at vid58's level; the whole
film followed.

### Measure the landmark the complaint names, not the one the API hands you
Four of eleven notes were "framing is off" with a red box on the face card. Round 2 measured the
face **contour** (brow to chin) and called it clean; round 3's own plan then measured the face
**bounding box** and reported "28% of frames crop." Both were wrong. Person segmentation put the
TRUE crown 441px above the bbox top:

    contour top (brow)        y1084
    face bbox top (hairline)  y 879
    TRUE crown (hair)         y 439

Under the shipped transform the crown landed at y76 against a card top of y440: **his head was cut
off in essentially every carded frame, not 28% of them.** Crown-to-chin ran 1590px against a
1280px card, so no `ty` offset could fix it; scale came down from 0.9569 to 0.6792. Three
successive measurements, each more careful, each still wrong; the tell was available the whole
time: draw the landmark on a frame and look.

### A blacklist gate cannot catch what its detector never saw
Two of the three framing notes landed at times where `read_guard` had never generated a span at
all, because eyelid aperture alone can't see gaze DIRECTION; at those two moments it measured
0.347 and 0.361 against a film median of 0.379, indistinguishable from looking at the lens. Fixed
two ways. **The signal** is now pupil position inside its own eye opening plus head pitch, on a
rolling roughly 1s median (hand-labelled reads: 0.153 to 0.326; camera: 0.375 to 0.440, no
overlap; per-sample thresholds had already failed three times). **The shape** is now a WHITELIST,
windows his face MAY paint in, everywhere else forbidden, because a missing whitelist window only
costs a beat of face, while a missing blacklist entry ships the defect. **Choose which way the
gate fails.**

### Regenerating a derived artefact exposes what was hand-patched into the old one
Re-running the caption generator to fill four gaps surfaced defects nobody had reported: every
price rendered as a bare number ("833", "1075", "1499"; the existing fix table only matched
`$`-prefixed tokens and had never fired, a hundred-fold error next to four competitors' real
prices in a sponsored comparison); every clip capitalised its first word; five brand mis-hears the
old block had been hand-corrected for; and `transcript.json` was missing from the project
entirely, which is presumably why round 2 hand-edited captions instead of regenerating them. The
four caption gaps themselves came from a legitimate mute-range rule that had outlived the graphics
it was muting, about 30s with no subtitle. **A suppression keyed to a composition has to be
re-derived when the composition changes, or deleted with it.**

An `ALLOW` entry naming `#turn`/`#payoff` matched nothing in the rebuilt c1; an exemption that
matches nothing reads as "considered and handled" while handling nothing.

### Numbers

| | round 2 | round 3 |
|---|---|---|
| designed stage | 44% | **70%** |
| stillness (motion_guard) | 56% | **35%** |
| dashboard on screen | 26.6s, small cards | **39.0s at 2070px** |
| frames cropping his head | ~100% | **0** |
| speech with no caption | ~30s | **0** |
| kit devices used | 0 of 12 | 9 of 12 |

---

## vid59 short, the 47s vertical (hf59s/, 2026-08-08)

### Two timelines in one folder, and the solver read the wrong one
`crown.csv`/`facebox.csv`/`gaze.csv` are measured on the RAW take (370.2s); `short-beats.json` is
timed against the cut master with two retake spans removed (351.9s, 18.41s shorter). Beats before
the first cut are identical in both clocks; b6/b7 are not, and the inherited solver framed the
CLOSE, the one beat this client had already sent a note about, against footage six seconds of
speech away from what it actually plays. Confirmed by matching frames (cut t=331.06 best-matches
raw f_01748 at luma error 1.5 against 9.0 for the unmapped frame), not by re-reading the
arithmetic. **When two files in one folder are both "seconds," check which clock.** `cut_to_raw()`
now maps every beat off `cuts.json`, and sampling asserts no beat straddles a removed span.

### A percentile over a take is not a constraint on a beat, second time of asking
vid58 vetoed a full-frame close on a whole-take chin p97 and the client overruled it ("show nader
in full frame here with captions"). vid59's whole-take figure said the same thing (chin p97
canvas y1538 against y1600, a 62px coincidence) but b7's own 34 samples put chin p97 at canvas
**y1465**, worst frame y1474, 226px clearer. The close shipped full-bleed with its own bake. Cost:
caption room, paid in advance, his jaw at y1474 leaves y1478 to y1590 for two 56px lines, ten
pixels of clearance, since a 9:16 crop of a 16:9 frame already uses every row.

### A residual is a proxy; measure the thing it stands in for
b6 was planned as a CARD and failed `RESID 138 > 130` (a threshold inherited from vid58). Hand-read
against both sway extremes, the shot was fine for 2.8s then settled; raising the threshold would
have shipped a real defect. Measured directly, his contour sweeps 508px against a 560px card (26px
either side at the widest frame; at the left extreme his jaw sat at x252 against a card edge at
x260), not centrable at any offset. b6 became a BAND instead, which also reads better: CARD to
BAND to CLOSE escalates into the CTA.

### Gate scope, again: the leaf rule has a caption-shaped hole
`safe_zones.py` decided what to measure by `el.children.length === 0`. A caption with a bolded
accent has children, so **six of twenty-two cues were never measured as a box**, only their bold
fragments were, and it also sampled 0.39s apart against a shortest cue of 0.30s, missing six more
entirely. It now prints the distinct element set it measured and refuses to pass under 20. Same
shape in the contrast checker: it read `textContent`, so `#root` counted as "having text,"
inherited the UA default black, and reported 1.14:1 five times; fixed by declaring the inherited
colour, not by silencing the check.

### `.stg` on a parent does not stage its children
With `immediateRender:false`, an element sits at its CSS value until its own tween starts. `.cad`
was hidden but its `.num` child's computed opacity was 1 the moment the row arrived: "60" and "90"
were on screen a second before he says either. `#brkLine` had the identical fault and slipped under
the 0.5s stillness detector by 75ms; an unrelated 140ms retiming exposed it. **Staging belongs in
CSS on the element that animates, not on its parent**, vid58's "420+ four and a half seconds
early" recurring.

### The shell arrives on the verb, the figure arrives on the figure
New house pattern, now used three times in one film: the STRUCTURE (a form's five field labels, two
cadence rows, four category chips) lands at the cut; the CLAIM (the values, numerals, lit chips)
lands on its own spoken word. Fixes a zone holding one bare numeral in 400px of ground and a figure
on screen before it's spoken, in one move. Also fixed frame 0: a cover with one of five rows filled
and four staged reads as half-drawn; the whole empty form at t=0 is both a finished cover and the
better idea.

### A hole is not an overflow, and no gate looks for one
A picture-off move and a dashboard's arrival were sequenced wrong twice: crossed, the panel landed
over his half-collapsed face; staggered to wait for the collapse, it left 0.3s of frame with an
empty 780px hole. No gate catches a hole (not an overflow, not a contrast fail, not a snap, not
static, it's mid-tween). Found only by extracting the mid-move frame. Fix: exploit the clip-path's
own collapse direction, his face is gone in the first third of the move, so the panel can arrive
0.06s later without ever landing on him.

### The dashboard crop is decided by delivery width, not by the long-form
The long-form's dashboard crops are framed for 3840px wide; at this short's 890px graphics zone a
2676px source strip lands at 0.33x and its 24px labels render at 8px. Every crop was re-solved for
source text at 0.7x or better (1620 to 890 for one strip, 1220 to 890 for another). Tighter
cropping also kept it SAFE, the full-width version reached past "Data removed" into the first
personal-value line. `pii_guard` gained a declared-static test measured on the BUILT clip (not the
source), negative-controlled.

### Other costs
`apad` with no explicit length is an infinite source; a bare downstream `atrim` doesn't reliably
end the graph, a 13-cue mix spun at 99% CPU for nine minutes and wrote a short file until
`apad=whole_dur=` plus `-t` fixed it. `--video-frame-format png` stalled capture and exited 0;
default extraction worked. A 40ms floor on an L-cut tail was too high for the film's opening join
(39ms was the whole remaining tail, not a scrap); writing it took that join from 5.5x to 2.5x its
budget.

**Numbers:** 1125 frames, 46.92s, 1080x1920 at 12.7 Mbps (`--crf 12`), -14.0 LUFS/-0.9 dBTP.
`motion_guard` 3.4% genuinely still (one 1.6s breath; a scrolling activity-log card no longer
counts as held). Three stock clips, two dashboards, 13 SFX cues.

---

## vid59, Incogni vs OneRep, sponsored 16:9 long-form (hf59/, 2026-08-06), deconstruction + postmortem

6:10 source, locked camera, cut to 5:51.6.

### A frame count and a duration cannot see content
The single-pass cut used `select`/`setpts` for video and `aselect`/`asetpts`/`atrim` for audio. The
video compacted; the audio kept its source timings and a trailing `atrim` just chopped the end. The
delivered "cut master" still contained BOTH duplicate reads and had lost its last 18.4s (discount
code, URL, guarantee line, sign-off). Every mechanical check passed (frame count exact, AV
durations identical to the microsecond, right dimensions and rate). **I verified the container and
never the content.** `cut_guard.py` now transcribes the DELIVERED file fresh and asks: does each
removed phrase appear exactly once, does the file still end on the take's last words, is the word
count consistent with what was removed, does any word straddle a join. For audio, explicit `atrim`
segments rebased with `asetpts=PTS-STARTPTS` and `concat`, not `aselect`.

**One anchor is not a content check; four are.** The gate's first version matched long literal
phrases and failed a CORRECT file, because whisper heard "which HAD the expanded" on one pass and
"which ADD the expanded" on another. Rewritten to key on numeric/proper-noun anchors, then failed
a correct file again because the tokeniser strips punctuation and whisper emits `$15.95` as two
tokens, so `15.95` never survived (**a check that cannot match is a check that cannot fail**). On
the actually-broken file, the phrase anchor `similar territory on entry price` PASSED because
whisper split it across a segment boundary; four other anchors caught it. A single-anchor gate
would have cleared a catastrophically broken film.

### Ban the shoot at 300, not 60, and ban the metaphor
Three levels of stock repeat: ID (same clip), SHOOT (vid58's known siblings were 12 ids apart;
vid59 returned an id **168** away from a shipped one, from the same photographer's batch;
threshold raised to 300, since a false rejection costs one candidate in twelve and a false accept
costs a clip the client has already watched), and **METAPHOR** (vid58's verdict beat was an aerial
fork in the road; vid59's verdict is the same beat, a fresh clip of the same shot is still the same
shot to the viewer, and only a list of what previous films spent catches it). Also caught: same-
shoot pairs within one result set, and cross-theme collisions (two ids one apart used for two
different chunks). A previously rejected id stays rejected on facts about the clip, not just its id.

### The three.js fault was never the shader, it was the tile size
vid58's field ran `MeshBasicMaterial` throughout (ignoring the scene's own light), identity scale
on every instance, camera never moving. Rebuilt with standard materials, a procedural PMREM
environment, per-tile rise/tilt toward the key light, camera parallax, hand-rolled bloom (r150 UMD
three.js has no `EffectComposer`, verified, not assumed). **All of it was invisible at `TILE=34`**:
17px at delivery, no room for a highlight, nothing bright enough to bloom. Re-solved to `TILE=90`:
the same device went from a 46% by 27% strip to 62% of frame, lit-vs-unlit separation of 65 to 83
luma after H.264 against a flat control's 38.9. **Scale places a device; pitch shapes it; tile size
decides whether any material can be seen at all.**

Setting a competitor's instance colour to neutral grey was not enough: the env map is a blue sky
and the rim light was sponsor-blue, so the competitor rendered **periwinkle**, the sponsor's own
brand colour, in a paid comparison. Fix: drop `envMapIntensity` to 0.22 and use a white rim on the
grey state, which reads as a different material rather than a dimmer version of the same one. **A
neutral albedo is not a neutral render.**

### Different denominators must not share a field
The script carries three figures with three different bases (broker groups registered with five
states; one competitor's site count; the sponsor's brokers-and-databases count). One grid with two
of the three lit is the obvious build, and it asserts a relationship nobody established, the viewer
computes an invented percentage. The owner's own instinct killed the combined grid as "weird and
absurd" before this was diagnosed. Fix: one figure became a stamped number beside a physical pile;
the field is used only where coverage-shape (narrow-and-deep vs wide across categories) is the
actual argument, never a raw count. **A tile is not one broker** either; making it one just moves
the same trap down a level.

### Numbers
Camera locked across all 741 samples (zero deviation, no baked-in punch-in unlike vid58). Face-safe
77.5% (vid58: 70.7%). Full-bleed 9:16 clears by 24px at the worst frame against y1600. Claim audit
clean, every figure verified against a published source and agreed by both whisper models, one
unsourceable clause about a named person handled by keeping it off screen entirely.

### Postmortem: three defects the gates missed by being scoped too narrowly, not by being absent
`card_guard`/`band_guard` both walked `.scene` only. c1's `#s1` doesn't carry the class, so **the
film's opening nineteen seconds, the hook, the thing every viewer sees, was never measured by
either gate, on any run, on any film**, and a panel and a caption printed on top of each other,
both illegible. Found only by reading extracted frames. Two more of the same shape: both guards
stopped their ancestor walk at `.scene`, so a decorative child of a card whose own parent sat at
`opacity:0` was still measured (two overlays reported "1543px past a boundary" they were nowhere
near); and `band_guard` measured `el.textContent`, which includes descendants, so an `inset:0`
wrapper "had text" and was measured at full frame size. **Before trusting a gate, print the
element count it actually measured. A gate reporting PASS over an empty selector is
indistinguishable from a gate reporting PASS over a clean film.**

A stale price-correction table is a known trap; an INERT one is worse. Three films' worth of
correction entries had been written to match `"$420"`, but whisper puts a leading space on
ordinary words and none on attaching punctuation, the actual token is `" $420"`, so **none of them
had ever fired**, and the broker count shipped as `$420 plus` in a film quoting eight real prices.
**A correction table needs a test that proves it fires, not just that it exists.**

A `.bcard` outlives its `<video>` and no preview tool can show it: `shoot.py` seeks every video by
hand without the renderer's own clip scheduling, so its contact sheet looked perfect while the
render shipped a bordered rectangle with nothing in it. `clip_guard.py` now reads the schedule
instead of the picture.

Every full-bleed column had been placed against his measured face contour; his real reach
(shoulders, gesturing hands) ran further, x1168 left, x2704 right, and every panel sat over him.
**Solve card layouts against motion, not against the face box.** Also: filtering caption words by
time-overlap put a boundary-straddling word into both chunks (five of fourteen joins duplicated);
filtering by onset alone dropped five instead. Fix: onset plus a 0.06s frame-snap slack, and
proofread the assembled caption track end to end in one pass, since duplicates are invisible chunk
by chunk. **Stopping a render early cost twelve minutes when the caption duplicate was found four
chunks into a 45-minute run; finishing would have cost 45 minutes for a film to throw away, a
render in flight is not a sunk cost.**

---

## vid58 short, the 47s vertical (hf58s/, 2026-08-05)

### Round 1 shipped the wrong format
vid58's chin p97 sits at y1575 against the y1600 band, "25px of clearance that is a coincidence,
not a margin," so round 1 took vid46-short's band (face 1080x1000 at y0, graphics zone under it,
caption at y1396), solved from his own crown/chin composited onto his sway extremes and baked into
all seven clips so no transform could differ between beats. The graphics zone was built at 940px
wide; `safe_zones.py` immediately flagged sixteen elements 50px inside the right rail: **70
(margin) plus 890 (caption width) equals 960, exactly where the like/comment rail starts, and the
rule was about the BAND, not about captions, so it did not carry across automatically.**
`motion_guard` measured **86% of the cut holding still** (every graphics zone composed at its own
cut, then sat 5 to 6s); staging arrivals on his actual word onsets fixed both the stillness and
surfaced a real sync error: the "420+" figure had been on screen 4.5s before he says the number.
And two near-identical VO lines 0.22s apart ("I'd give the edge to Incogni" / "Optery Ultimate
wins by absolute coverage") were merged in the plan, removing a pointless jump cut but keeping the
concession; dropping every concession would have made the 47s cut a less believable film than the
6:39 it came from.

Owner's instruction after delivery: **"animations on TOP, A-roll on the BOTTOM, split-screen AND
card, with stock footage."** Round 1 shipped the inverse: face on top, graphics under, one
placement held for the whole 47s, and zero stock despite eleven graded clips already cut into the
long-form.

### The rebuild, and the file was never actually wrong
The brief for the rebuild claimed the repo and `LEARNINGS.md` disagreed about which way up vid56's
short was, because `#faceCam` is declared `top:0; height:1210`. **That reading is wrong, and it is
the whole reason round 1 came out inverted.** `#faceCam` is the untransformed camera; what lands on
screen is `#faceScene`'s clip-path plus its transform, and at frame 0 that resolves to a 560x736
card at the BOTTOM of frame. Driving the timeline and measuring `getBoundingClientRect` on the
CLIPPED result took one script and settled it. It also caught a trap in the probe itself: Chrome
serialises `inset(838px 260px 346px 260px)` with the left side collapsed, so a naive 4-number parse
reads the corner radius as the left inset and reports the card 128px too wide, the same shorthand
hazard already known from GSAP. **A declared `top`/`height` on an element inside a
clip-path-and-transform rig tells you nothing about where its pixels land; measure the clipped
result, don't read the CSS box.** The only actual error in the record was a round NUMBER (it was
round three that inverted vid56, not round two); one wrong digit was enough to make a correct file
look like it disagreed with a correct note.

**One bake, three states, and only one may change his head size:**

    BAND   x0-1080  y838-1574   split-screen, full-width bottom panel
    CARD   x260-820 y838-1574   the same pixels, clipped
    CLOSE  x0-1080  y300-1360   a real size change, pushed in, caption in the low band

BAND and CARD share one camera and differ only by clip-path, so a cut between them is a WIDEN, not
a resize, safe in one cut in a way vid46's two-face-size short (read as a bug) was not. CLOSE is a
genuine size change and is only allowed because it lands on a hard cut into a new shot.

The rebuild also re-checked a face-safety exclusion (296.4 to 302.8) rather than trusting it, per
the vid56 lesson; this one was real (`eyeOpen` 0.45 to 0.13 for 32 consecutive samples, frames show
him reading; a blink is 2 to 4 samples). That turned a safety flag into an editorial decision: the
picture moves to CARD for that span (he stays visible, smaller, while graphics carry the price
argument) and returns to full BAND once he's square to camera again.

`gsap.fromTo` defaults to `immediateRender:true`: every from-state in the file was stamped onto its
element at BUILD time regardless of timeline position, so the CLOSE camera's scale/position was
baked onto `#faceCam` before a frame ran, and frame 0 (the Instagram cover) shipped with his
picture at the wrong size and both price columns at opacity 0.35. Every gate passed it: valid
markup, no console error, elements in their safe zones, motion_guard only checks for change.
`defaults:{immediateRender:false}` fixes it and introduces the mirror fault, an element sits at its
FINAL value until its own tween starts, then snaps back and replays (`#mRule` was drawn full-width
from t=0, vanished at 4.92, redrew itself).

`snap_guard.py`: the hard part is that a snap and a legitimate fast entrance (`back.out(2.4)` moves
68% of its travel in 16% of its duration) are the same SHAPE by raw threshold. The real signature
is **static for 0.5s or more, then a one-frame jump, then a return to within 2% of the held
value**, which reduced sixteen false reports to two, both real (b-roll stamps visible from their
card's own cut, snapping to zero, fading back in 0.8s later). Negative-controlled by reverting
`#mRule`.

`shoot.py`'s screenshots do not show the right VIDEO frame: `tl.time(t,false)` places every
graphic correctly but never sets `<video>.currentTime`, so a colour comparison came back 90 levels
apart before anyone noticed. **Preview is authoritative for layout and timing, not for which frame
of the A-roll is under it.**

The delivered short measures 3 to 5% darker than its own baked source with no grade applied
anywhere in the pipeline, confirmed as the renderer's own capture path (not a bug) by measuring the
same channel-ordering shift on an already-shipped film (`out/vid58-final.mp4`: minus 4.6/3.3/2.2
against its own A-roll chunk). Verifying delivered sync the same way (transcribing the delivered
file and checking every caption against the audio underneath it) kept "finding" faults that
evaporated on inspection: whisper mis-spelling proper nouns, tokenisation splitting `60%`
differently, a word attributed to whichever side of a cue boundary whisper's own segmentation
preferred. **The measurement that actually settles it is drift** (anchor distinctive words at each
beat's head/tail, compare expected vs heard): median plus 0.022s, half a frame, flat start to end.
A comparator that keeps finding faults that evaporate is measuring the wrong thing; change what you
measure, don't lower the threshold.

**Numbers:** round 1 motion_guard 86% held; the rebuild, 7% (two deliberate 1.6s breaths). Three
stock clips (each picked on meaning, checked for shoot adjacency). Worst chin y1511 against y1600;
the close's worst y1301.

### Round 2 feedback: four notes, four real defects
A word's SOUND does not stop where whisper says it stops: *"the word everyone has weird cut in the
audio"*, and it was worse than it looked: his "every one" was still at 0.129 RMS on the last sample
and hit digital silence on the next. The beat plan's own tail-scan was careful in principle (cap at
the next word's onset) and still shipped a chop, because the cap trusted whisper's boundary mark,
which undershoots by design; the real envelope decayed continuously to 56.73 with no onset until
56.95. **Fix is an L-cut, not a moved cut**: a measured, faded tail of the outgoing beat carried
over the incoming one, length set per join by extending until the signal has sat under the noise
floor for three consecutive 20ms windows. He flagged two joins; measuring all six found the same
shape, lower level, on three more. **When a note names an instance, check the class.**

*"nader is reading here in this frame, need to replace it with animations... as we cant show the a
roll here as he is looking down"*: this was the exact span already measured and moved to CARD in
the rebuild, on the theory that a smaller size solved it. **It didn't: an unwatchable shot at a
smaller size is still an unwatchable shot.** "Graphics are not the default, showing him is" has a
precondition, that showing him is worth doing, and when the take itself is unusable for a span, the
fix is to take the picture OFF, not shrink the problem.

*"show nader in full frame here with captions"*: full-frame had been ruled out film-wide on the
whole-take chin p97 (y1575, 25px, "a coincidence"). Re-measured on just that beat's own 31 samples,
chin p97 landed at canvas y1374, 226px of clearance. **A percentile over a whole take is a property
of the take, not of the shot being cut**; re-measure per beat before letting a global figure veto a
specific shot, especially when the veto makes the film worse.

### Round 2b: the fix for a chopped word smuggled one in
*"run the whisper model once again, there are few words which are being cut."* The L-cut tail added
for "everyone" measured SILENCE ONLY at that join, but at the b6/b7 join there is no silence,
"That's" starts 146ms after the out-point, so the scan ran to its 220ms cap and laid **124ms of the
next sentence's word over the close.** A fragment of a word where no word belongs reads exactly
like a chopped word. The beat plan's own header comment already warned *"a tail scan that can cross
a word boundary is not recovering a tail, it is stealing a word,"* written after reading it, then
violated by a new scan that could cross a boundary anyway. **The rule belongs to any scan that
walks forward from a cut, not only to the one that first needed it.** Every tail is now capped at
`min(silence, next_word_onset - 50ms)`.

Separately, a fade shape destroyed a word without clipping it: whisper-medium heard delivered
"automatically" as "automatic" because the `curve=exp` fade starting at t=0 was already well down
by 100ms, attenuating the release under the incoming line. Fix: hold full level for 60% of the
tail, taper only the end.

`audio_guard.py` asks four questions per join (does the out-point chop a word, does a tail reach
into the next one, does an in-point clip an attack, is any join still a cliff in the delivered mux),
every other gate (frame count, loudness, captions, drift) is blind to all four. Its first version
had a section that could not fail (it recomputed the tail length and compared it to its own cap
instead of measuring the actual tail file written); fixed to measure the assembler's real output,
negative-controlled by replanting the 220ms tail.

---

## vid58, Incogni vs Optery, sponsored 16:9 long-form (hf58/, 2026-08-05)

6:39, the longest take in the repo. Deconstruction, then an 11-chunk, 9586-frame composition round.

### Measure the SET, not the subject, to answer "did the camera move?"
Three wrong-ish methods before the right one: scene detection found cuts, not gradual zooms;
face-box scale conflated a lean-in with a zoom; background-strip differencing separated the two
but a gesturing arm produced a false positive. What settled it: a fixed-geometry object in the
background (a dark TV rectangle on a light wall) gives absolute framing per frame, immune to
anything he does, exactly 810px of 960 for the whole take except one 1.4s punch-in to 1.152x. **A
static object of known geometry in the background is the only signal that answers the camera
question directly; everything else answers a proxy.** And that punch-in is a real edit baked into
the "raw" supplied take; check for baked-in zooms before solving any crop, since no face card or
vertical crop may straddle that window without the subject jumping 15% mid-shot.

### Never audit numbers off a small-model transcript
whisper `small` rendered *"405 plus or 635 plus with expanded reach"* as *"435 plus with expanded
reach,"* it dropped a figure and mangled another, which nearly got his most accurate line logged as
his worst error. `medium` got it right. **Numbers spoken at speed are exactly what a small model
mangles, and a claim audit is nothing but numbers**; run the big model over any take with on-screen
figures, keep the small model's word timings if those are already solved.

### Understated competitor figures are a fairness problem, not a cosmetic one
Every stale number in the script made the named competitor look smaller, worse than an ordinary
error in a paid placement. Fix that needs no re-record: stamp the figures that are right, and for
stale ones carry the tier, the price, and a gate that visibly stops short, with no count on screen.
Related: he credits Incogni with "human attention on more complex cases" right after saying it
assigns no human agent, reads as a flat contradiction, but Incogni's own pricing page confirms it's
true and scoped to one plan (Unlimited). **Before logging a "contradiction," check whether the
vendor's own pages make both statements true at once**; the fix is narrower than "don't show it":
carry the plan qualifier.

### A different id from the same shoot is still a repeat
Three b-roll candidates (ids ending 518/529/532) were adjacent to an id already shipped to this
client on vid46 (ending 520), same shoot, same set, same lighting. **Ban the shoot, not the id.**

### The replacement for a rejected hero device has to be an ARGUMENT
vid56 killed the plate field as ambient texture ("that shitty globe"). Its replacement isn't
another ambient shape: `coverage.js` is a 640-tile field where **the lit area IS the claim**, each
tier lights its real site count and stops at a visible gate, the competitor's lights the whole
field at once, and "expanded reach" tiles render as hollow outlines because the sponsor's own copy
says those brokers don't yet meet its removal-verification standard, the caveat becomes geometry
instead of a footnote. Caught only by rendering a still and reading it: reveal direction was
backwards once (plus-y mapped to far, not near, under the tilt), and a 40x16 grid foreshortened
into an unreadable band where 64x10 read cleanly. **Proof-render a new device before it touches a
timeline; it costs one screenshot.**

### Composition-round findings
**Preview the timeline in a browser before rendering it.** `shoot.py` drives the real timeline in
Chromium and screenshots in about 20s per chunk, catching (before a single frame rendered) two
postage-stamp wordmarks, a shutter reading as five empty boxes, a headline printing under a b-roll
card, a cloned figure block, a label sitting on its own step name, and four scene cuts opening on a
near-empty frame. Two things have to be faked by hand or the preview lies: seek with
`suppressEvents=false` (GSAP's `pause`/`seek` default it to true and skip every `onUpdate`, which
the renderer does not), and give `#root` its `data-width`/`data-height` manually (a plain page load
computes it to 0 and every screenshot comes back black).

`gsap.from()` on a scene whose CSS start state is hidden animates TO hidden, not from it: `from()`
reads the CURRENT value as its end value, so a scene starting at `opacity:0` in CSS fades to
nothing half a second after its own cut and stays gone. Renders perfectly at the cut frame, which
is exactly where a QA pass would look. Fixed with `fromTo()`, now `K.settle()` in the shared kit.
A settle from a text opacity is wrong for large opaque surfaces, a sheet of paper at 62% over
near-black reads as a loading skeleton; `K.settle(sel, t, {op:1})` settles position only for those.
And a masked word-rise can never open a chunk: however tight the stagger, every word starts below
its mask, so a chunk's frame 0 under a `wordRise` is empty. Chunk-frame-0 headlines get a
whole-block settle; `wordRise` stays a mid-scene device.

**An element that is finished should be HIDDEN, not transparent.** `opacity:0` on a wrapper leaves
every child fully measurable (and `overflow:hidden` on an ancestor doesn't shrink a child's own
bounding rect); `card_guard` found paper shutters "1101px inside the face card" and a b-roll tint
"1553px" in, both actually clipped to nothing on screen. `visibility:hidden` genuinely removes a
subtree; use it for anything that's DONE, not just off-screen.

**The b-roll bug the guard was built for, and still missed:** `broll_guard` asserted each clip's
window fit inside its source file and its chunk, true of all twelve placements, eleven of which
were still wrong, because `data-start` on a `<video>` is CHUNK-LOCAL and copying it between chunks
silently means something different (c8's clip played from 265.84s while its card didn't appear
until 288.18s, a 3.6s empty bordered rectangle). **The real question is whether the CARD is on
screen when the video is not**, not whether the clip's window is legal; `broll_guard --cards` now
drives the timeline and asserts the card's actual visible interval is contained in its clip's
window.

A PERMISSIVE gate change must be negative-controlled: intersecting each rect with its clipping
ancestors (to stop flagging a word-rise clipped inside its own mask) made the gate pass a PLANTED
violation, because `#root` computed to height 0 on a plain load and the clamp clipped everything in
the film to nothing. **A change that makes a gate more permissive is not done until a planted
defect still fails it.**

Verify a contrast WARNING on pixels before believing or dismissing it: `validate` reported 16 WCAG
failures down to 1.03:1, all sampled mid-settle while the scene was still `visibility:hidden`,
measured on the actual rendered PNG, the same elements were 8.97:1 and 8.00:1. Neither "the tool
says fail" nor "the tool is probably wrong" is an answer; sample the pixels.

Hardlinked shared assets (`base.css`/`chunk.js`/`coverage.js` in every chunk dir) break silently
when an editor REPLACES a file instead of truncating it, a new inode leaves every other chunk
pointing at the old file, a stale-render bug with no symptom and no failing gate. `render_chunks.sh`
now re-links and asserts the SHA of every shared file against the project copy before rendering.

Scale places a device; pitch shapes it: raising `PITCH_Y` to give the coverage field more vertical
run made it worse, because the -0.86 tilt already foreshortens the vertical axis by 0.652, a 54px
gap becomes 35px on screen against a 6px horizontal gap, and ten rows read as ten stripes instead
of a grid. Fixed with `P.scale=1.35`/`P.oy=-40` instead, one re-proof, no re-derivation.
Separately, lit-vs-unlit has to survive depth falloff AND 4K H.264: at the device's original grey,
150 lit tiles were barely distinguishable from 490 unlit ones, and the lit area IS the claim.

`tl.call()` callbacks and cloned DOM nodes are both seek-order hazards: a non-linear render worker
can draw frame 900 before frame 100, applying a text swap out of order and leaving one beat
carrying the wrong price for twenty seconds; correct in a linear preview, wrong in a cold render.

**Captions transcribe him; graphics assert on the film's behalf.** Three stale Optery figures in
the script all understate the competitor. The graphics carry the corrected tier/price/gate and
stamp no numeral; the captions say what he said, stale figure included, a caption track is what a
deaf viewer has instead of the audio, and suppressing his own words there is a worse failure than
the honesty problem it would avoid. Separately, the caption pipeline needs numeric repair per token
WITH trailing punctuation preserved: an exact-token fix corrected `$1499` mid-sentence but let
`$1499.` at a sentence end sail through, a hundred-fold price error in a sponsored comparison,
found only by grepping every caption for `$[0-9]{3,}`.

Render QA sampled 108 beats on no uniform grid (every frame 0, every join, every card/figure/b-roll
edge) and found seven defects, six of them AT a cut. The worst: c2's frame 0 rendered a graphic
full-bleed across his face for exactly one frame because `L()` on a chunk's OWN start returns
0.0014, above zero to a comparison, frame 0 to the renderer, so the immediate `gsap.set` was
skipped. Fixed three ways (call site takes 0; `put()` treats anything inside the first half-frame
as frame 0; `frames_guard` statically rejects `K.face*(L(<chunk's own t0>))`). **An
absolute-to-local helper is a trap at exactly one input, the chunk's own start, and every chunk
uses that input.** Related: a graphic that legitimately changes state exactly AT a chunk join (both
sides internally correct, field state matching) still reads as a glitch rather than an edit,
because a chunk boundary is invisible to the viewer; graphics must carry THROUGH the join and
change on a word after it.

Frame arithmetic, again: `chunks.json` stores `dur` a quarter-frame below each chunk's true
boundary (so the renderer's `ceil()` doesn't add a frame), correct for RENDERING, but using that
same number as the chunk's EXTENT for scheduling leaves a 0.0104s hole at every join, silently
dropping any cue placed exactly on it (three opening SFX cues vanished this way, at c6/c9/c10, the
most audible placement in the film). **A chunk's extent comes from its FRAME COUNT, not its
`dur`.** And a cue landing on a join must read the chunk's own `t0` value, not a hand-typed
rounding of it: 183.85 vs a true t0 of 183.8503 put a cue on the wrong side of its join, audibly
identical, editorially wrong, invisible to every check.

`pichash` strips `<audio>` elements but not the HTML comments beside them, so an audio-only edit
(`sfx58.py` writes each cue with a reasoning comment) still changed the hash and forced two
unnecessary re-renders. **A guard that's correct but expensive to change gets changed at the START
of a round, never in the middle of one.**

---

## vid56, Incogni vs DeleteMe, sponsored 16:9 long-form (hf56/, 2026-08-03), round 1 REJECTED

Fourth Nader production, third long-form. 3840x2160 at **23.976** (first non-30fps build in the
repo), 5844 frames, 4:03, 8 chunks. Round 1 shipped clean on every gate and was rejected on look:
*"the fuck? Everything is just text-based. Can't we add better animations, better motion
graphics?"* Full diagnosis and rebuild order: `vid56-round2-brief.md`. The lessons below are the
ones that generalise.

### The field is a subject or it is nothing
Six of 31 frame notes were one object: the three.js plate field used as an ambient background at
alpha 0.05 to 0.14 behind almost every scene. The owner read it as "flickering at many places," "the
red lines are showing on behind," "why the fuck is this green thing flickering again and again,"
"remove this globe sign."

**Why it worked on vid46 and failed here.** On vid46 the field was the SUBJECT, 750 instances WERE
the 750 broker groups, the dome WAS the 420 sites, at alpha 0.92, and it was the only device the
owner liked. On vid56 it was demoted to wallpaper. At 5 to 14% opacity its thin plate edges alias
frame-to-frame at 4K (that is the flicker), and the LED `instanceColor` bleeds through as stray red
and green lines behind text.

**Rule: never run the field below about 0.6 alpha, and never behind unrelated content. Reusing a
hero device as texture destroys it and dirties everything in front.**

### Carrier variety is not MATERIAL variety
vid46's lesson was "count your carrier shapes before you fix any individual scene." I did exactly
that (spines, rails, redaction bars, two-lane tracks, tick fields, seals, cycles: seven carriers, no
repeats) and was rejected for being "all text based." Seven SHAPES made of one MATERIAL: thin
vector line-work on dark. No photography, no product surface, no generated art in four minutes.

**The stronger rule: every act must contain at least one NON-VECTOR element**, real footage, a real
product surface, or a generated image. Line-work is the connective tissue between those, never the
substance. Counting shapes is necessary and not sufficient.

### Sustained SFX beds are what "going on and on" means
vid46 round 3 ended at median 0.060 and the note was still "too loud," so on vid56 I kept levels
low (median 0.053) but added sustained texture beds under the long builds to avoid a bare-transient
bed. Result: *"the SFX is very irritating, going on and on and on"* plus four separate "remove the
SFX from here."

**Low level does not make a sustained layer inaudible; it makes it a drone.** Transients only,
silence is allowed, roughly one cue per 4 to 5s. And when he supplies a pack, it has to carry the
majority of placements or he will not believe it was used.

### A card exit must be a HANDOFF
Three notes: *"the A-roll going from here looks very very off,"* *"the a-roll disappearing from
this looks very weird. Either cover the entire frame or add some better animations."* The card
exiting was not the fault; nothing filled the space it vacated, so the frame sat half-composed with
a dead black right half. Audit every `hideFace()` against what occupies the vacated 1760px on the
NEXT frame.

### Two new gates the built-in checks structurally cannot replace
- **`card_guard.py`**: drives the real timeline in a browser, reads the live clip-path to decide
  when the face is carded, and measures every visible graphic against the card edge. `hyperframes
  inspect` cannot catch this, the card is a clip-path on a `<video>`, so there is no DOM box to
  collide with. Caught a label 234px under the card in c1, then four more violations before they
  ever rendered. **Prove a new gate with a negative control before trusting it**, reintroducing the
  known bug confirmed it flagged at `right=2314`.
- **`safe_zones.py`** (short): measures every element's `getBoundingClientRect` against all four IG
  zones across 121 timeline samples, respecting each caption's scheduled window. Written after
  reading a tiled contact sheet and getting it BACKWARDS: called the caption band as sitting inside
  the bottom UI band (it was 60px clear) while missing that every caption ran 50px into the right
  rail. **Overlay screenshots tell you roughly where things are; only measurement tells you
  exactly. Frame reading tells you WHERE TO MEASURE, it is not the last gate.**

### Frame-0 composition, again, at a new scale
vid44 had six of nine chunk frame-0s cut to a near-empty frame. vid56 had four of eight: c5/c6/c7/c8
each opened their scene with `window.wordRise()` about 0.1s in, so the cut frame carried only an
eyebrow. **A scene arriving on a hard cut gets a whole-block settle; the per-word rise is for
mid-scene headlines only.** Three productions in a row; it belongs in the chunk scaffold, not in
review.

### Frame arithmetic: three separate off-by-one classes in one film
The renderer computes `ceil(data-duration x fps)`; a duration written at the exact frame boundary
yields N+1 frames (write `data-duration` a QUARTER FRAME BELOW the boundary). `-shortest` on the
final mux costs the last frame, the audio mix rounds a hair under the video's exact duration, so
the delivered file came out 5843 against 5844; drop `-shortest`, map streams explicitly. The
frame-total assert is what caught both, vid44 shipped +4.1s of drift and a truncated end card
because nobody asserted it.

### Never run two 4K encodes at once on this machine
A c1 re-render captured all 832 frames and was then killed mid-encode at exactly 600s, having
managed 111 frames at 0.0077x speed, because 4K x264 A-roll cuts were running concurrently. Looked
like a mystery death; the log said `ffmpegEncodeTimeout`. `render_chunks.sh` now runs strictly
sequentially and exports `HF_DE_STALL_MS=420000`, `FFMPEG_ENCODE_TIMEOUT_MS=3600000`,
`PRODUCER_ENABLE_CHUNKED_ENCODE=true`. Render time fell 15m34s to about 2m per chunk once nothing
competed.

### Gaze: run length does not separate a blink from a glance
vid46 needed two signals (eye-openness plus contour aspect). On this take the aspect signal runs
BACKWARDS (reading 1.015 vs camera 0.979) and `browEyeGap` is identical in both groups, neither
separates anything. Eye-openness alone is cleanly bimodal, threshold at 0.32 (the TOP of the
ambiguous band, not its valley).

Then the real trap: rejecting all 44 short (0.4 to 0.6s) runs as blinks on a run-length argument
(there is a genuine empty gap between 1.2s and 2.8s in the histogram) took coverage 22.5% to 55.4%,
and reading the resulting windows found him visibly reading at five timestamps inside "safe"
windows. Tiled and adjudicated all 44 by eye: 36 blinks, 8 glances. Then the same trap one level
down, single-sample dips never reach the run logic at all; 42 fell inside safe windows, 3 were real
glances no threshold change could ever reach, now named in `HAND_EXCLUDE` with reasons. Final:
46.1% across 15 windows, better than vid44 (38%) and vid46 (43%).

### Verify the effect, not the exit code
Three times in one session a tool or edit reported success while doing nothing: `ffmpeg -v error`
suppresses `showinfo` output entirely, so scene-cut detection reported "zero cuts" when the filter
was never reporting at all; a CSS `str.replace` whose pattern contained a value not in the file
silently did nothing, the new elements rendered unstyled and full-width (`card_guard.py` caught it
at `right=3840`); `hyperframes lint` rejects symlinked assets, the short would have rendered silent
with missing logos.

### Deriving a short from a 16:9 long-form: check the crop before writing HTML
vid46's tight close-up could not crop to full-bleed 9:16 (chin landed inside the UI band); vid56's
wider framing does, at cover scale 0.8889 the chin p97 lands at y1408, clear of y1600, crown at
y260 clear of the top 150. **Composite the crop with the safe zones onto real face frames before
authoring**, 30 seconds, and it is the only thing that settles it. Also: whisper sentence ends
UNDERSHOOT; scanning each beat's out-point at 40ms to the measured dip recovered 0.96s of word
tails across 8 beats.

## vid56 round 2, the rebuild (hf56/, 2026-08-04)

Round 1 was rejected on look plus 31 frame notes. What follows is what generalised.

### A malformed CSS comment silently deletes the rules after it, and NO gate sees it
An edit left prose between two rules with a closing `*/` and no opening `/*`. CSS error recovery
skipped forward and discarded the three rules that followed, so two of the three parts of c1's new
device rendered as 112x0px of transparent nothing. Every gate passed: `lint` checks the document,
not the cascade; `validate` found no console errors, a dropped rule is not one; `inspect` measured
the elements exactly where the layout said they were, 112x0 of nothing is a valid layout;
`card_guard` passed for the same reason. Only reading the 4K frame showed the beat was missing.

**`css_guard.py`** now asks the browser how many rules it actually parsed and asserts every
selector written in the source survives into `document.styleSheets`. Proved with a negative
control. **And the corollary, also proved:** `dead_guard.py`, which looks for elements that should
paint and don't, reports CLEAN on that same defect, because when the dropped rule was the
element's only paint source the element has no background, no border and no text, so it's filtered
out as "not a painting element" before the zero-area test runs. **Run the negative control on
every new gate; a gate that sounds like it covers a case often does not.**

### `hyperframes inspect` structurally cannot see a caption collision
Five of the 31 notes were one label wrapping into the caption band. `inspect` samples the timeline,
and the label and the caption clip are rarely alive in the SAME sampled frame, the collision exists
only during their overlap. **`band_guard.py`** samples 120 points per chunk and, at each, asks
whether a caption is actually scheduled before measuring every visible graphic's bottom against the
band. It immediately found a second instance nobody had noticed.

### A b-roll card is an untimed box around a timed video
`.bcard` keeps drawing after its `<video>` ends, so the card stands on screen as an empty bordered
rectangle. **`broll_guard.py`** asserts `data-media-start + duration` fits both the file's real
duration and the chunk's duration, and caught four windows overrunning by 0.02 to 0.10s that would
each have shown a frame or three of empty box at a join. `data-media-start` is what lets one shot
survive a chunk boundary; the uniqueness assert has to know the difference between a genuine repeat
and one beat split across a join.

### Measure the SUBJECT, not the face box, before placing anything over full-bleed
The coupon was placed on the claim that his body never comes below a certain x, a number from the
FACE box. A shoulder and a gesturing hand collided with it. `measure_body_edge.py` builds a subject
mask from per-pixel temporal variance over the window (the wall, the chair, the monitor and the
speakers are bolted down, so the only thing that varies is him). Round 1's box had 2.9% of its
pixels in motion; the replacement has 0.0%. The fix was not a narrower card in the same place, it
was a card above the zone his hands work in.

### A supplied SFX pack may contain no usable sound at all
He asked for the "saas sfx" pack by name. Measured (band energy plus envelope shape), not one of
its 17 files is a transient, every one classifies TONE or BED, twelve are exactly 2.847s, and in
two of them the event doesn't start until 1.7 to 2.0s in, behind two seconds of room tone. Dropped
on a timeline as supplied, that pack IS the drone he was complaining about. `curate_sfx.py` cuts
each file to its own onset window and gates the tail. **And the obvious onset detector is wrong**:
"first frame above 25% of peak, run until it goes quiet" mis-cut four of seventeen files that open
with a soft designed lead-in, latching onto the lead-in and closing before the real hit. Anchor on
the loudest 50ms and walk BACK to its attack, then assert the window contains that loudest 50ms.

### Carrier variety, then MATERIAL variety, then per-act enforcement
vid46's lesson was "count your carriers." vid56 round 1 had seven and was still rejected as
all-text. Round 2's rule, every act carries at least one non-vector element, needed the same
treatment carriers got: eight clips, one per act, uniqueness asserted in the build, midframe-
rejected before placing, and per-clip exposure derived from measured luma rather than a shared
value. Two clips that are both "an archive interior" read as one shot twice even when they are
different locations. **Adjacency across a chunk join is part of the uniqueness test, not just the
ID.**

### A staleness stamp taken AFTER the work is not a staleness stamp
`render_chunks.sh` stamped `pichash` once a chunk finished rendering. A chunk takes 3 to 5 minutes,
so any edit made during that window was recorded as though the render already contained it: c8
rendered its old timeline at 03:34, a fix landed at 03:38, and the 03:40 stamp declared the stale
render fresh. `assemble.sh` would have shipped it. **Capture the hash BEFORE the work, write it
after.** The stamp then describes what the renderer actually read, and a later edit correctly
reads as stale.

### Nine hard cuts, each opening on an empty frame
Every scene cut in the film had the headline's `wordRise` scheduled 0.16 to 0.42s AFTER the
`K.cut()` that revealed the scene, and a `wordRise` starts with all its words below their masks,
invisible. vid44 and vid56 round 1 both got this at chunk frame-0 and the rule was written for
chunk frame-0; it applies to EVERY hard cut, not just chunk boundaries. Starting the rise ON the
cut (plus 0.02) with a tighter stagger keeps the signature and means the frame is always BUILDING
rather than blank. **Sample the render AT its cuts.** A uniform time grid lands in the middle of
held scenes, which is exactly where nothing is wrong.

### The field is a subject or it is nothing, and here it was nothing (again)
Six frame notes were the three.js plate field at alpha 0.05 to 0.14, again. It came out of all
eight chunks. The two places it ran at subject strength came out too, because one note read "did
the same in the last video as well." **A signature device reused in the next film for the same
client, at the same layout, reads as a repeat, not a callback.**

## vid56 short round 2, position is not visibility

The short shipped with **no captions for 27 of its 43 seconds** and every gate passed. `.cs`
carried no `z-index`, so it computed to `auto` (0) while `.face` sits at 2. The A-roll painted over
every caption, and they only appeared on the graphics beats where no face video happened to be on
top. The owner wrote "Has captions missing" and "Captions are missing," and he was exactly right.

Why nothing caught it: `lint`/`validate` check the document and the console, a caption behind a
video is neither; `safe_zones.py` measures WHERE every element is, the captions were exactly where
they belonged, y1396, inside every Instagram zone, it has no concept of which element owns the
pixel that lands there; WCAG contrast passed too, contrast is computed from declared colours, not
from what's on screen.

**`paint_guard.py`** asks the only question that settles it: at the caption's own centre, does
`elementFromPoint` return the caption? Two things were needed to make it honest, both found by it
failing wrongly first: probe at the composition's real size (a scaled-down viewport puts the
coordinates outside it and null reads as a pass), and replicate the renderer's clip scheduling
before hit-testing (a plain page load stacks all 22 caption clips at identical coordinates and the
last one in the DOM wins every hit test). Proved with a negative control: removing the `z-index`
makes it FAIL, restoring it makes it PASS.

**The note points at the symptom, not always the cause.** Note 1 was drawn around the hook: "Need
to place the captions on the bottom." The captions were already at the bottom, underneath the
picture, so the hook was the only text on screen and reading it as a misplaced caption was
completely reasonable. **When a note says an element is in the wrong place, check whether a
different element is invisible.**

**A client note can name its own reference.** "place Nader here, in card like we did on the
previous videos" pointed straight at vid46's short, whose brief still holds the verified geometry.
Ambiguity in a follow-up note was worth one question rather than a guess; the layout it referenced
was worth reading rather than reinventing. Also: widening the caption box from 890 to 940 walked
straight back into the vid46 finding that "every caption ran 50px into the right rail." Left 70 +
890 = 960, and the rail starts at 960. `safe_zones.py` caught it immediately, the gate that exists
because of a past mistake is the one that catches its repeat.

**`motion_guard.py`**, also new: CLAUDE.md has said "Nothing static >1s" since vid2 and nothing had
ever checked it. Fingerprinting the graphics every 0.2s (box, opacity, transform, excluding
`<video>`) found **10.0s of held blocks, 23% of the cut** on this short, 3.6s, 3.8s and 4.8s
stretches where a block landed and then simply sat. That is what "the animation is very still here"
means, and it is measurable rather than a matter of taste.

## vid56 short round 3/4, stop animating over him, start showing him

Round three rebuilt the layout (graphics top, caption middle, A-roll bottom) per the round-2 note.

### WHICH WAY UP IS vid56's short? Settled, on the file, 2026-08-05
The shipped vid56 short is **graphics TOP, caption MIDDLE, A-roll BOTTOM**, in every state.
`#faceCam` is declared `top:0; height:1210`, and that is NOT a placement, it's the untransformed
camera; what's actually on screen is set by `#faceScene`'s clip-path and the transform `faceSet()`
writes onto `#faceCam`. At frame 0 the clip and transform resolve to a 560x736 portrait card at
x260 to x820, y838 to y1574, bottom of frame, centred. Chrome serialises `inset(838px 260px 346px
260px)` with the left side collapsed, so a naive 4-number parse reads the corner radius as the left
inset and reports the card 128px too wide, the same shorthand hazard the file already warns about
for GSAP. The one state where the picture IS at the top is `hero` (full-bleed with the caption low
underneath, no graphics above), used for 4.6s of a 43s cut, and it is not a split.

**The general lesson: a declared `top`/`height` on an element inside a clip-path-and-transform rig
tells you nothing about where its pixels land.** Drive the timeline and measure
`getBoundingClientRect` on the CLIPPED result, which is what `safe_zones.py` already does; the
answer was one screenshot away, and the cost of not taking it was a whole rebuilt short (this is
the same misreading vid58's short round 1 made independently).

Round 4's note, on the closing beat: *"No need to show any animation here when Nader says real is
what are you going and whatever it is, just the A-roll should be shown. Any animation, error, just
A-roll with captions should be there. At the last line ... CTA."* **He then said this explicitly
generalises: it applies to the long-form (`hf56/`) too, and it names a repeated pattern across
videos, not a one-off note on this beat.**

The closing beat had been graphics-only for its whole 4.6s (an offer-card lockup with no face at
all) on the line where the presenter is making the direct ask. Fixed: bare A-roll for the first
1.9s (no graphics, caption low, the only motion is a slow push on the picture); the CTA arrives ON
the last line, not for the whole beat, faceTo("card") lands him in the card exactly as the caption
moves to the middle band and the offer card composes above him. He is on screen for the entire
close; the ask is layered onto him rather than replacing him.

**The beat had been graphics-only because a gaze-safety scan flagged its source range as unsafe.**
Checking the raw gaze signal directly rather than trusting the exclusion: `eyeOpen` dips to 0.12 to
0.26 for 2 to 4 samples twice in that range and recovers immediately, and the extracted frames show
him square to camera throughout. **Those were blinks.** The window's padding turned two blink
clusters into one 2.4s exclusion, which is what pushed the beat to graphics-only in the first
place. Any beat a safety pass excludes is worth checking against the raw signal before accepting
the exclusion as fact, a false positive silently removes the presenter from a beat and nothing
downstream flags that as a defect.

**The general rule, stated the way he said it: graphics are not the default, showing him is.**
Reach for an animated overlay when it's carrying information that cannot come from him speaking (a
number, a comparison, a mechanism); do not reach for it to fill a beat, and never let it replace
him at the moment he's making the direct ask.

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
