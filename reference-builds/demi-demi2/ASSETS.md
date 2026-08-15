# demi2 assets manifest

The new Demi client, and the only build in this repo authored as **ONE file and chunked after the
fact**. The chunking scripts are the artefact worth reading here.

Shipped result: `reference-cuts/demi-demi2-six-tools.mp4` (720p proxy).
Delivered original `out/demi2-final.mp4`: **1133 frames, 2160x3840 @ 30fps, 85.01 Mbps, 37.766667s,
402.8 MB.** Twenty versions and ten feedback rounds, most of them design rounds with the client's
own reviewers.

Ships here: `index.html`, the eight emitted chunk documents `index-c1.html` through `index-c8.html`,
`package.json`, `hyperframes.json`, `transcript.json`, `chunks.json`, the four pipeline scripts,
`design.md` and `ref-format-brief.md`.

**Which HTML is canonical.** `index.html` (37.7667s, `data-composition-id="root"`) is the film. It
has never rendered and cannot: 28 `<video>` elements, all 2160x3840 at 52 to 100 Mbps, in one page
**hard-reset an 8 GB M2 Air three times**, blank screen, no `.panic` file. `index-c1..c8.html` are
what `build_chunks.py` emits and what actually rendered, in four minutes total with the machine
untouched. Edit `index.html`, re-emit, re-render only the chunks whose emission actually changed.

---

## Why it had to be chunked, precisely

It is **not** the worker count. `--low-memory-mode` auto-enables at 8 GB or less and already pins
one worker, which is why the crashed logs read `workerCount:1` under a header saying "auto
workers". The failure is the **video extraction stage**, which runs before any frame is captured
and pulls frames from every `<video>` in the page regardless of workers. The dead log's last line
is "Extracting frames from video 28/28". The only lever is **videos per page**: 28 became a maximum
of 5.

The evidence for the reset lives only in
`/Library/Logs/DiagnosticReports/ResetCounter-*.diag` (`Boot faults: wdog,reset_in_1`) plus a
`WindowServer_*.userspace_watchdog_timeout.spin`. The kernel gets too wedged to panic and the SoC
watchdog cuts power.

---

## The chunk plan, `chunks.json`

| chunk | t0 | t1 | frames | videos |
|---|---|---|---|---|
| c1 | 0.0000 | 4.7667 | 143 | 2 |
| c2 | 4.7667 | 8.7333 | 119 | 3 |
| c3 | 8.7333 | 14.4667 | 172 | 2 |
| c4 | 14.4667 | 17.8667 | 102 | 4 |
| c5 | 17.8667 | 20.8667 | 90 | 1 |
| c6 | 20.8667 | 27.4333 | 197 | 1 |
| c7 | 27.4333 | 32.2000 | 143 | 1 |
| c8 | 32.2000 | 37.7667 | 167 | 2 |

1133 frames total, which is what the delivered file measures.

`plan_chunks.py` places the boundaries and asserts them. `build_chunks.py` emits the eight
documents and copies each chunk's referenced assets. Everything below is a rule one of them
enforces because the film shipped wrong without it.

### `--resolution portrait-4k` is required

Without it a 1080x1920 composition renders at 1080p and silently delivers a quarter of the pixels.
The first validation render did exactly that and looked like a success.

### HyperFrames CEILS `duration * fps`

`data-duration="4.7667"` on a 143-frame chunk renders **144** frames, because 4.7667 * 30 = 143.001.
Emit `(nframes - 0.001) / FPS`. Rounding is not safe either: 126/30 is 4.2, and 4.2 * 30 is
126.00000000000001 in binary float, which ceils to 127. Only a per-chunk frame assert catches this.

### Never hand GSAP a rebased position that went negative

It does not clamp, it **shifts the whole timeline**. Drop those tweens statically, which is also
semantically right: a `.from()` that finished before the chunk began leaves the element at its
natural CSS state. Tweens landing **past** the chunk end are the opposite and must be KEPT, so
`immediateRender:false` holds the element at its from-state and it correctly stays hidden. That is
what keeps chips 4 to 6 invisible in c1.

### The emitter rebases only LITERAL tween positions

`forEach` and array-computed positions pass through verbatim and fire at wrong absolute times in
any chunk whose clock does not start at 0. New tween groups must be written as flat literal
statements. The hook chips dodged this in round 3 only because c1's t0 is 0.

### A straddle guard only sees the tween families it can parse

The first version matched `}, <literal>)` and so never checked the chip entrances (`}, t)` inside a
forEach) or the caption entrances (`}, t + 0.02)`, read from the DOM), which are two of the three
families in the file. It passed by luck. Enumerate every family, then **prove the guard can fail**
on a deliberately bad boundary.

### Anything meant to be present AT a bound starts ON or BEFORE the bound

Film frame 1016 sampled t=1.66667 in c8 while the outro's rebased start was 1.6667, three
microseconds short, so neither the outgoing nor the incoming video painted and a stale frame held
for 33ms. Start an incoming clip **0.2 frames early** when it begins exactly on a chunk bound. Same
class as the grid blink at 8.74 against a bound at 8.7333.

### A float on a held overlay must end inside its chunk

A relative y-drift crossing a boundary is dropped in the next chunk and the element pops 8px at the
join. Keep drift cycles short and bounded so the planner's straddle guard can represent their
yoyo/repeat arithmetic.

### Cut on shot starts

Consecutive shots overlap 13 to 27ms. Assert the incoming shot has a higher track index and is live
at the boundary, then drop the outgoing tail from the later chunk. Sub-frame spill is a cross-cut,
not a split, and dropping it is provably invisible.

### `url(...)` references are assets too

The emitter linked everything matched by `src="assets/..."` and therefore **never linked a single
`@font-face` file**, because CSS references fonts as `src:url("assets/...")`. Chrome silently
rendered every caption in a fallback font across TWO delivered cuts. Lint, validate and the frame
QA all passed it, and the client's "is this IBM flex font?" is what caught it. An emitter that
copies referenced assets must match **every reference syntax the document can contain**, not the
one that was easy to grep.

### The Studio rewrites the source

`hyperframes preview` silently stamps `data-hf-id="hf-xxxx"` on every timed element in the
project's `index.html`. Two breakages follow: every text-anchor edit script misses its target, and
the chunker's `\bid="..."` regex matches inside `data-hf-id=` because the hyphen is a word
boundary, so the planner and emitter read machine ids. The root-duration assert was the only loud
symptom. Strip the attributes before any pipeline run, and never leave the Studio server running
while editing the source. The `index.html` shipped here is clean.

### The freshness dance for a single-chunk fix

`build_chunks.py` rewrites all eight files for any source edit. Hash-prove which emissions actually
changed by regenerating pre-fix and post-fix and comparing, re-render only those, then align the
proven-identical files' mtimes to their renders. Content proof first, mtime second. Never
blind-touch.

### Verify the JOINS, not the film

Read the frame pair either side of every boundary: caption, overlay count and element positions
must be identical across the cut. And a stale reference is worse than none: a PSNR run against an
earlier probe reported a "failure" that was really a source edit made after that probe rendered.

---

## Fonts, `assets/fonts/`

`index.html` declares two faces:

| Family | File | Use |
|---|---|---|
| `Plex` | `IBMPlexSans-VF.woff2` | everything: captions, chips, UI mocks, body |
| `Season` | `SeasonMixUprightsVF.woff2` | one element, `#greet`, the app greeting inside the rebuilt Demi window |

**`SeasonMixUprightsVF.woff2` is a paid client licence and is deliberately NOT in this repo.** The
copy in the working project is the webfont served by demi.ai, which is fine as reference and is not
a licence to ship or redistribute. **A rebuild falls back silently**: `font-display:block` swaps to
the generic `serif`, nothing errors, no gate fires, and the app greeting renders in a system serif
that is wrong for the brand. Either license Season Mix from the client, or substitute a close
high-contrast transitional serif **and flag the swap in the delivery note**. Do not quietly ship
the fallback.

IBM Plex Sans and Mono are open and are in `library/fonts/`.

**Verify glyphs at NATIVE resolution or not at all.** IBM Plex Sans's serifed capital "I"
disappears when a 2160-wide caption crop is downscaled into a comparison image, which made a TRUE
Plex render read as a fallback. That false negative launched a data-URI embed, two `@font-face`
grammar rewrites and a woff2 conversion, all chasing a ghost. One native-resolution crop settled it
in a minute. Better still, **the renderer's compile log is the ground truth**: grep for
`[Compiler] Embedded local font file: ... -> data URI` and `Fetched N font face(s) for "IBM Plex
Mono" from Google Fonts`. Only a MISSING file falls back silently, which is exactly what the
emitter's `url()` miss shipped. A glyph question is also answerable from the font file itself:
fontTools `glyf`, Plex Sans "I" is 1 contour and 12 points, a grotesque's is 4 to 8.

---

## Footage, `assets/shots/` (22 present, 14 referenced in the final)

| Prefix | Files in the final | What |
|---|---|---|
| `ar_` | `ar_a1`, `ar_a2`, `ar_a3`, `ar_sp`, `ar_f`, `ar_g1`, `ar_g2` | the client's A-roll, cut into shots |
| `b`/`bo`/`be` | `b1d`, `bo2a`, `bo2b`, `be3` | the client's desk and integrations B-roll |
| other | `dock2`, `outro2`, `s18a` | the app dock reveal, the client's own outro clip, a screen shot |

Sources, both on an external drive that must be mounted:

- A-roll `/Volumes/Shreyansh/demi new /a roll.mp4`, 34.03s, 2160x3840 HEVC, 30fps, 32.9 Mbps. The
  client's own manual cut, untouched as instructed. His three jump cuts sit at 5.47s, 10.57s and
  27.40s. `3CB79055-....mp4` (101.5s) is the raw take it was cut from.
- B-roll `/Volumes/Shreyansh/demi new /broll/b1-b6.mp4`, all 2160x3840 HEVC 30fps at 25 to 32 Mbps,
  which are `IMG_9486` to `IMG_9491` re-exported through CapCut.

**Every B-roll clip is the same desk with demi.ai already on the monitor, so no B-roll can play the
"problem" half of the script.** That is a constraint of the footage, not a preference. It was
documented on day one, a team note asked for the overlay anyway, and the client's own reviewer then
flagged the contradiction ("how can this screen have Demi's b-roll?"). Surface the constraint in
the reply instead of silently complying. A blurred variant with unreadable content is the
compromise that survived.

Two placement rules learned here:

- **Same-z videos stack by DOM order, not by `data-track-index`.** A `<video>` inserted mid-stack
  painted UNDER a later-in-DOM full-bleed video despite a higher track index. Every gate passed and
  the chunker extracted both files; the QA contact sheet was the only thing that showed it. New
  overlay videos go at the END of the video stack.
- **A crossfade needs a real underlay on BOTH sides.** Fading a video in where the previous clip
  has already ended dips to black. Fading a translucent panel over the presenter ghosts his face
  and was rejected twice. The only fades that work are footage over footage, graphic over footage,
  and clip over extended underlay, which is why `ar_a3` and `b1d` were re-cut WITH TAILS.
- **A pane that arrives by tween across a cut doubles the subject.** The split's top panel slid in
  over 7 frames while the full-bleed A-roll still showed his face above the pane's face, and the
  note was "frame is repeating". Same law as vid62's card: state changes at a cut, never tweened
  across it.

---

## Graphics assets

| Path | Files | Origin |
|---|---|---|
| `assets/logos/` | `gcal`, `gdocs`, `gmail`, `hubspot`, `openai`, `slack` (6 svg) | real vendor marks, one per tool the script names |
| `assets/ui/demi-app-icon.png` | 1 | the real Demi app icon, composited onto the rebuilt window |
| `assets/brand/` | `demi-primary-white.svg`, `demi-symbol-white.svg` | the client's own brand book vectors |

`assets/ui/` in the working project carries eighteen more PNGs from earlier versions
(`cta-plate.png`, `gmail-reply-draft.png`, `app-window.png` and so on). The final references exactly
one of them. Everything else on screen is rebuilt in HTML.

Two client rules that shaped this: **the client rejects a branded hub before the product reveal**
("we haven't revealed Demi yet"), and a "?" tile also reads as product-shaped, so graph beats before
the reveal are plain interconnecting lines only. And the persistent product pill died the same
round: over B-roll that already shows the product's site, a brand pill is redundant clutter.

---

## Palette and type, `design.md`

Every value is Demi's own, from Demi Lightweight Guidelines V1.0, not invented.

```
ground #040120   ground-lift #0B0538   blue #246CE0   blue-tint #DAE8FF
orange #FD8502 (spent ONCE, on the value transfer)   orange-tint #FFEDE4
pink #CE3DA2 (gradient only, never type)   white #FFFFFF   ink-dim #837E97
```

The app chrome tokens (`--appbg #0B0F26`, `--appcard #141A38`, and so on) are sampled from the real
product, not from the brand book. **The demi.ai website is a blue-only reduction of the brand**: it
aliases every pink and orange token to blue, so matching the site does not match the brand book.

---

## Audio, `bed.wav` via `build_audio.py`

**The film is VOICE plus MUSIC only. There are zero `<audio>` SFX elements in `index.html`, and
that is deliberate and permanent.**

Five timestamped notes (14.32, 17.31, 19.03, 21.43, 33.85) landed exactly on the five surviving
whoosh / impact cues, the ones every acoustic measure said were NOT clicks. Three earlier purges
had removed what the analysis called typing (ticks, then the music's percussion grid, then
click-attack reveal cues) while the client was naming a **category**: any added effect at all.
**When the same complaint survives two evidence-based fixes, stop refining the classifier and
remove the whole class.** The correct move in round 2 was one question, "should ALL added sounds go
or just the clicky ones", instead of three rounds.

The route there is still worth keeping, because each step was a real measurement:

- Classify SFX by **measured envelope**, not by name or intent: audible duration 0.13s or less with
  attack 50ms or less splits tick from sustained objectively.
- "Typing sfx still there" after two cue purges turned out to be **the music**. The bed carried a
  metronomic 0.465s percussion tick through the whole back half, on a strict 129 BPM grid, with no
  SFX cue involved. Found by transient-onset scanning the mixed bed against each component: clicks
  either matched the VO's own consonants 1:1 (innocent) or fell on the grid (the music). Swapped to
  `gear.mp3`, the least ticky candidate at 30 transients versus 75.

Mechanical notes:

- VO is `assets/vo/aroll.m4a`, laid at 0, **unity gain, no filters**. It is his A-roll's own audio.
- Music enters at 15.99s so the track's lift lands at 30.45s, at a static gain roughly 13 dB under
  the voice.
- **With zero SFX inputs the mix graph's trailing bare `apad` spins ffmpeg forever** (the bounded
  SFX inputs had been terminating it). Use `apad=whole_dur=DUR`.
- **`sidechaincompress` truncates at the key's REAL data end in this ffmpeg build.** `apad` on the
  key, verified at 39.8s in isolation, does not stop it: main 37.8s plus key 39.8s still yielded
  34.8s out. The ducked bed died at about 35s across two versions and only the client's "why did
  the music end here" caught it. The mix is now computed in numpy (envelope-follower duck, static
  bed gain, fades), every branch sample-verifiable. Bisect a filtergraph empirically before
  trusting any filter's documented behaviour at a boundary.
- **An audio-only change is a REMUX, not a re-render.** 30 seconds, picture untouched.
- The client's outro clip's audio track was **digital silence at -240 dBFS**. Probe a delivered
  clip's audio before designing a handover to it.

---

## Two defects that shipped, and the QA that now prevents them

**A spliced-out beat shipped three times.** A marker-to-marker text splice swallowed the grid scene
that lived between the markers. The grid's tweens kept firing at nothing, every gate passed, and
the beat played as bare footage plus a caption for THREE delivered versions, because the contact
sheets in those rounds sampled around 9.x but never inside it. Two rules: after any splice, **diff
the element ID list** of the composition before and after, since a disappeared id is a disappeared
beat; and the per-delivery contact sheet must **tile every composition element's window at least
once, generated from the clip list**, not from hand-picked timestamps. Also count `<div>` opens
against closes after each splice, because an imbalance means a premature `#root` close that
browsers silently repair. That one shipped too.

**An `<svg class="clip">` element's visibility is NOT managed by the framework.** A timed
squiggle-arrow SVG with `data-start 15.35` painted for the ENTIRE film, appearing beside chips at
0:05, on cards at 0:07 and in the graph at 0:13. Only div, video and img clips get visibility
control. Wrap timed SVG in a timed `<div class="clip">`, or do not time SVGs directly. Found by the
client watching, not by any gate: the per-element contact sheet samples element windows, so it
cannot see an element that should be ABSENT. **Verify a timed element is absent outside its window
too.**

---

## The reference, `ref-format-brief.md`

The client's style reference is a Viktor AI-employee ad, 79s, saved at
`hfdemi2/ref/competitor-viktor-reel.mp4` in the working repo. **"Smooth and subtle but so elegant"
has a number: zero.** The reel has no cuts detectable even at a 5% scene-change threshold. It is
one continuous take, and all visual interest comes from soft persistent overlays that fade in, HOLD
for 5 to 10 seconds, and drift gently. Translated into this build: no flash cuts, every `back.out`
and `expo.out` replaced by 0.4 to 0.5s `power2` fade-drifts, section changes faded rather than cut.
**Measure a style reference before translating it.** "Elegant" was an adjective until scene
detection made it a spec.

And then the harder lesson: porting the reference's **devices** (a persistent pill, crossfades) in
this portfolio's own vocabulary of rounded rects, straight hairlines and cream panes produced "no
difference" from the client. The actual ask was the reference's **organic drawing language**:
curved dotted connectors around a central hub, irregular blob shapes, white washes that melt into
footage, playful pop-with-overshoot keyframing. Hub-and-spoke beats a lattice, a blob beats a
capsule, a wash beats a pane. All of it is cheap in HTML: SVG quadratic paths with `stroke-dasharray`,
irregular `border-radius`, a linear white-to-transparent wash.

`gsap_exit_missing_hard_kill`: an exit fade on a clip element, or one ending at a clip boundary,
needs `tl.set(..., {opacity:0})` after it, or a non-linear seek can land past the fade with stale
visibility.

---

## Regenerating

```bash
# strip any data-hf-id attributes first if the Studio has been opened on this project
python3 plan_chunks.py      # boundary placement + every straddle assertion
python3 build_chunks.py     # emits index-c1..c8 + copies each chunk's assets
bash render_chunks.sh       # per-chunk, --resolution portrait-4k, frame count asserted
python3 build_audio.py      # numpy mix: VO at unity + music, zero SFX
bash assemble.sh            # stream-copy the eight chunks, lay the bed once
```

Inputs that do not ship here: the A-roll and B-roll masters on the external drive, the cut shots in
`assets/shots/`, the client's brand SVGs, the music beds, and `SeasonMixUprightsVF.woff2`, which is
the client's paid licence and must be obtained from them.
