# Troubleshooting

Symptoms this system has actually hit, with the real cause. Most of these passed every automated
gate.

---

## Render

**"Stuck at frame N", the same N every time.**
The CLI's 60-second no-progress watchdog killing a healthy render. On an 8GB machine a late 4K or
three.js frame legitimately takes longer than that. `export HF_DE_STALL_MS=420000`.

This was misdiagnosed as disk pressure once: freeing 4GB correlated with a success and looked
like proof. It recurred six more times on a healthy machine with 13 to 15 GiB free, including on
byte-identical content re-rendered back to back. **When a fix and a symptom's disappearance
correlate once, that is not proof.** Get a second data point before writing a cause down.

Disk is still worth checking: a 4K round costs about 800MB in renders. Prune `renders/` between
rounds. But `hf*/renders/` is not a safe bulk-delete target, because not every project's final
lives in `out/`.

**A delivered file "won't open" / spins forever in a preview app.**
Diagnose before theorizing, especially when the fix is expensive. One report ("stuck, not
playing," a spinner screenshot) got a plausible-sounding but untested codec theory
("hardware-decodes X, falls back to software for Y") stated as fact, which drove two render
cycles building an alternate-codec file, and the theory was wrong. The real cause: the preview
app caches a rendered thumbnail **per file path**, and the delivery had overwritten the same output
path across several rounds; the cache entry never invalidated even though the bytes underneath it
changed. Three checks that each take seconds and rule out most of the search space before touching
any encode settings: `qlmanage -t -s <timeout>` (or the platform equivalent) against every candidate
file including the client's own original: if *their* file also hangs, the bug isn't in your encode
at all; `lsof`/`xattr -l` (dataless/provenance flags on synced files); a full decode pass
(`ffmpeg -f null -`) to rule out a genuinely broken container. Resetting the preview cache and/or
delivering to a brand-new file path (never reusing the exact output path across rounds) both
confirm and fix a path-cache issue. **When a claim about the cause is checkable in under a minute,
check it before stating it as fact: especially before it drives a build decision.**

**Render dies at the same frame with `Protocol error (Runtime.callFunctionOn): Target closed`, or
hangs at 0% CPU, with plenty of memory free.**
Single-worker screenshot leak, not RAM. On <= 8GB, HyperFrames forces low-memory mode (one worker
plus screenshot capture), and Chrome leaks per screenshot until a session crashes. Bigger frames
exhaust it sooner. Render with `--no-low-memory-mode --workers 4` so each session captures fewer
frames. Raising `--protocol-timeout` only makes a hang wait longer.

**Do not reach for `scale=1080:1920` on the A-roll to relieve this.** An oversized master is 2.25x
the pixels and it does drive the leak, but downscaling an asset feeding a 2160x3840 composition
costs 84% of the picture's sharpness and shipped three times. See `docs/03-quality-bar.md`. Pay
for the pixels with worker count, `HF_DE_STALL_MS`, and chunking.

**`--workers 4` times out on all workers at about 25%.**
Drop to 2. Render cost varies wildly with machine state: the same length composition has taken
2m10s and 8 minutes on the same machine in different sessions.

**Solid-black capture fields.**
Heavy-overlay budget. `lint` counts elements carrying radial-gradient, blur or clip-path; past
about 40 this appears. One global ground stack instead of per-band grounds drops the count from
about 30 to about 6. The threshold is a field signal, not a guarantee: 48 elements did not
reproduce it on one machine, 31 did on another.

**EPIPE from `npx hyperframes render | tail`.**
Do not pipe the renderer's TTY output. Redirect to a log file.

**Two `<video>`/`<audio>` elements pointing at the same large media file deadlocks the frame
extractor, and the clips that survive render BLACK.** Distinct from the `HF_DE_STALL_MS` watchdog
stall below: the tell is *all* capture workers dying at once on a protocol timeout
(`Runtime.callFunctionOn timed out`), not a stall parked at one fixed frame. The log says so
outright:

```
Some video elements did not decode within 45000ms: c3.mp4, c3.mp4, c4.mp4, c4.mp4
[... affected videos will appear as blank/black frames]
```

**One element, one physical file.** A plain `cp` of the source is enough, and any spoken audio goes
on its own extracted `.m4a`. Ten `<video>` tags from 4 files was enough to trigger it; a six-clip
montage that pushed two clips to **five referencing elements each** stalled a 12-minute render
repeatedly. Copying per usage also renders **faster**, 74s against a timeout at 25%. Disk is free;
a stalled 12-minute render is not.

This is what `lint`'s `duplicate_media_discovery_risk` warning is pointing at. It reads as
cosmetic and it is not.

The deliberate exception: two `<video>` elements on the same file with the **same `data-start`**
(a blurred full-frame ground behind a clip-path card) stay in frame-sync and are fine. The failure
is decode pressure and element count, not sharing per se.

**A render that fails still leaves yesterday's file on disk.** One render stalled deterministically
at frame 568/1264 twice, and both times `renders/vidNN.mp4` was still v1: right duration, right
bitrate, right frame count, wrong film.

```
Sequential drawElement capture stalled: no frame progress for 60000ms (stuck at frame 568/1264)
```

`ffprobe` cannot tell you a file is stale. **Check the mtime and check the CLI's exit line, every
time: exit 0 is not success and a valid file is not a fresh one.** Two theories worth skipping on
this symptom, both tested and wrong: the clips all decoded clean end to end, and dropping CRF 14 to
18 with `-tune fastdecode` moved the stall by four frames.

**A CSS transform on a box containing a `<video>` deadlocks the capture engine.** A 0.20s
`scale:1.045 → 1` punch-in on 24 B-roll wrappers stalled a render at 40% with 15 workers alive and
no frames appearing for ten minutes. Removing the punch-in let the same file capture all 796
frames. This is the same fault as repeated `<video>` srcs: the engine will not survive compositing
transforms over video elements. **Get the life from the cut itself.**

**ffmpeg's encode step has its own 600s timeout, separate from the render's watchdog, and blowing
it discards the entire capture.** A 2160x3840 encode at 42 Mbps ran at `speed=0.015x` and was
killed at exactly 10:00 **after a completely successful capture**. The log reports a generic
`ffmpegEncodeTimeout`, which reads like a mystery. Always export:

```bash
export FFMPEG_ENCODE_TIMEOUT_MS=3600000
export PRODUCER_ENABLE_CHUNKED_ENCODE=true
```

**A 4K video-heavy composition hard-resets an 8GB machine, and it is the video EXTRACTION stage,
not the workers.** 28 `<video>` elements at 2160x3840 and 52 to 100 Mbps in one page reset an M2
Air with a blank screen, three times. The evidence is only ever in
`/Library/Logs/DiagnosticReports/ResetCounter-*.diag` reading `Boot faults: wdog,reset_in_1`, plus
a `WindowServer_*.userspace_watchdog_timeout.spin`. **There is never a `.panic` file**: the kernel
gets too wedged to panic and the SoC watchdog cuts power. (`rst btn_rst` in the same file is just
someone holding the power button.)

It is not the worker count. `--low-memory-mode` auto-enables at 8GB or less and already pins one
worker, which is why the crashed logs read `workerCount:1` under a header saying "auto workers".
Extraction runs **before** any frame is captured and pulls frames from every `<video>` in the page
regardless of workers; the log died on `Extracting frames from video 28/28`. The only lever is
**videos per page**, so the fix is to chunk: 28 down to a maximum of 5 rendered the whole 36.4s
film at 4K in 4 minutes with the machine untouched. See `playbooks/chunk-revision.md`. Being at
91% disk capacity is the other half of the cause, because macOS cannot grow swap enough to absorb
the spike.

**And some stalls are not fixable by any of this.** One render stalled at the same frame with 18
videos and with 2 (frames 746 and 743 of 1057). Collapsing seventeen B-roll clips into one
pre-composed band track did not move it, so the ceiling is per-frame accumulation on an 8GB
machine, not video count. Three chunks of about 350 frames each rendered in 2 to 2.5 minutes.

**Diagnose a stall by rate, not by log.** Count frames on disk twice, 45 seconds apart. Zero delta
is a hang. A per-worker plateau at the same **count** across workers (not the same absolute frame
number) is media-seek exhaustion against a long-GOP source.

**A long-GOP source video hangs each render worker at the same per-WORKER frame count, not the
same timeline position.** If N workers each stop after roughly the same count of frames produced
(not the same absolute frame number), that is seek exhaustion against a media file with sparse
keyframes, not a genuine hang. Re-encode the offending source all-intra
(`-c:v libx264 -crf 20 -g 1 -keyint_min 1 -sc_threshold 0`): file size roughly doubles, which costs
nothing since the all-intra copy never ships.

**Never run two 4K encodes concurrently on this machine.** A render captured all its frames
successfully and then died mid-encode at a fixed timeout, having managed a tiny fraction of a
frame/sec, because a second 4K x264 job was running at the same time. The log reports a generic
encode timeout, which reads like a mystery unless you check for a second ffmpeg process. Run 4K
renders strictly sequentially.

**Renders killed with no error at 97–98% disk usage.** `df -h` **before** kicking off a 4K render,
not after it dies: a 65s 1080×1920 render needs several GB of frame scratch space, a 26.5s
2160×3840 render with PNG frame extraction wants **over 15GB**, and PNG extraction of 29s of 4K is
**4.7GB** on its own. One render died on ENOSPC at 95% full and needed 7.2GB of unreferenced
intermediates moved off before it would go. A 4K round costs about 800MB in `renders/`, and the
repo grows 5 to 6 GB per film, so this recurs.

Safe to move: `hf*/.assembly/video.mp4` (a pure intermediate), superseded review copies whose
hosted version lives on release assets, and cut masters whose transcode already sits in the
project. **Do not move an `out/*.mp4` that `review/data/<slug>/project.json` still points at.**

**`apad` with no explicit length is an infinite audio source, and a bare `atrim` downstream does
not reliably terminate the graph.** A multi-cue SFX-bed mix spun at ~99% CPU for nine minutes and
wrote a short file. Give `apad` a `whole_dur=` and cap the output with `-t`.

The same graph can work for months and then hang the first time a round **removes** something. With
every SFX cue stripped out, the fast-cut-ad demo film's mix had zero bounded inputs left, and those inputs were the
only thing that had been terminating the trailing bare `apad`: ffmpeg spun forever. `whole_dur=DUR`
is not an optimisation, it is what makes the graph terminable independent of its inputs.

**`--video-frame-format png` deadlocks the capture path.** It stalls deterministically at the same
frame with many source videos and a large extracted-frame count; `--experimental-fast-capture=false`
does NOT disable the code path that stalls (confirm by grepping the render log for "Sequential
drawElement capture": it's still there). The default JPEG frame format extracts fine but is a real
quality ceiling once the delivery encode is already tuned tight (measured ~40.5 dB PSNR against a
lossless PNG extraction of the same frame): `--low-memory-mode` forces the screenshot capture path
instead of `drawElement` and may avoid the deadlock, at roughly 4x slower (single worker).

**A render or extraction step can exit `0` and still have failed.** Two separate PNG-format render
attempts both exited 0 with `✗ Render failed` in the log and no output file on disk. **Check for
the artefact's actual existence, not the exit code**, in any script that chains render steps.

**`ffmpeg -v error` suppresses `showinfo` filter output entirely.** A scene-cut detector built on
`showinfo` reported "zero cuts" once when the filter was never emitting anything at all, not when
the source genuinely had no cuts. Sanity-check any detector built on a verbose filter with an input
that MUST produce output before trusting a zero/negative result from it.

**A render silently did not happen.**
`rm renders/work-*` in a zsh `&&` chain kills the chain when the glob is empty. This has bitten
five separate times. Cleanup is always a separate command, or `rm -f ... 2>/dev/null || true`.
The same applies to watch loops: use `find -name '*.mp4'`, never a glob.

**Do not grep a render log for "error".** The JSON trace lines match spuriously. Watch for the
mp4's existence instead, and gate on `pgrep -f 'hyperframes.*render'` being empty so a background
waiter does not race the next round's `rm`.

---

## The gates lie in known ways

**`validate` reports dozens of contrast failures, most spurious.**
It samples five fixed timestamps and measures every text node at each, reading background pixels
*through* every scene sitting at opacity 0. An element that is off-screen at the sample time gets
scored against whatever is behind it. On one build 75 warnings contained exactly two real
failures; on another, 25 warnings were all on a scene whose clip window did not include four of
the five sample times.

Do not chase the list. Check the sample timestamp against the clip window, then recompute the
actual foreground and background token pairs by hand and fix only what genuinely fails.

**`inspect` crashes with `Cannot read properties of undefined (reading 'totalDuration')`.**
Two causes, and the second is the common one. It is genuinely broken on some machine and version
combinations, confirmed against an untouched previously-shipped gold-standard project. But the
identical error is also produced by a missing attribute: **`lint` only demands `data-start="0"` on
the root, and `inspect` also needs `data-duration` on the ROOT composition.** Check that before
concluding the tool is out of action.

**`inspect` passed something that is visibly broken.**
It samples static times, so it misses collisions born from group moves, and mid-tween states.
And `data-layout-allow-overflow` on a parent **blinds the gate for its whole subtree**: audit
those by eye. A scrolling viewport wants `data-layout-ignore` instead, because `clipped_text`
fires on the mask regardless of allow-overflow.

**Everything passed and the page is dead.**
A `ReferenceError` before `window.__timelines` registers renders static DOM with initial
`gsap.set`s only, and lint, validate and render all report success. The tell in frames: the rig
stuck at its entrance blur state, and elements visible that should start hidden. Add the
Playwright pageerror check to the gate list.

**`gsap_exit_missing_hard_kill` fires and the kill is present.**
The static pass only recognises literal string selectors, so a loop-scoped `tl.set(el,...)` is
invisible to it. It also wants the kill's selector to **match the exit tween's element list as one
combined string**: `tl.set("#a, #b, #c", {autoAlpha:0}, t)`, not per-element sets at the same time.

**`visible_markup_comment` fires on legitimate on-screen text.**
Literal `skills/*.md` in content text looks like a CSS comment. Encode the asterisk as `&#42;`.

**A malformed CSS comment silently deletes every rule after it, and no built-in gate sees it.**
Prose left between two rules with a closing `*/` and no opening `/*` triggers the browser's CSS
error-recovery, which resynchronises forward and discards the rules that follow: an element with
no styling left at all renders as 0×0 of nothing. `lint` checks the document, not the parsed
cascade; `validate` reports console errors, and a dropped rule is not one; `inspect` measures
elements exactly where the (absent) layout puts them, which is a valid empty layout. A gate built
specifically to catch this (`css_guard.py`-style: ask the browser how many rules it actually
parsed, assert every source selector survives into `document.styleSheets`) is the only thing that
sees it, and its natural sibling, a gate that looks for elements that should paint and don't,
reports **CLEAN** on the exact same defect, because an element with no background/border/text from
a dropped rule gets filtered out as "not a painting element" before any zero-area check runs. Two
gates that sound complementary can both miss one bug for different reasons.

**`lint` rejects symlinked assets outright.** A short built by symlinking logos from a long-form
project would have rendered silent with every missing logo. Copy real files into the project
directory instead of linking them.

**A staleness hash that misses one stylesheet ships the film without the fix.** `pichash` hashed
`chunk.js` and `base.css` but not `vid62.css`, which held most of the film's look (`.eyeb`,
`.crit`, `.svc`, `.figw`, `.lad`). A one-rule eyebrow-ground fix that changed every chunk's pixels
invalidated **no** stamps; the flight script would have reported "all chunks already current",
skipped all 18, and shipped a film without the fix while every gate passed, because the gates read
the DOM and not the render.

**Whenever a per-film stylesheet or helper script is added, add it to the hash's `SHARED` list in
the same commit**, and check the stamps actually went stale before a resumable render:

```sh
for c in c1 c9 c17; do
  [ "$(python3 pichash.py $c)" = "$(cat $c/renders/.pichash)" ] && echo "$c CURRENT (bad)"
done
```

Three siblings in the same family. The hash strips `<audio>` so audio-only edits do not force a
picture re-render, but it does **not** strip the HTML comment beside each cue, so every audio edit
changed the hash and cost two unnecessary re-renders on one film. **A guard that is correct but
expensive to change gets changed at the START of a round, never in it**, because the fix
invalidates every stored stamp at once. And a stamp taken **after** the work is not a staleness
stamp: a chunk rendered its old timeline at 03:34, a fix landed at 03:38, and the 03:40 stamp
declared the stale render fresh. Capture the hash before the work, write it after.

**A guard reporting PASS is not a guard that ran.** One build passed lint, validate and five
custom gates and every one of these would have shipped: a PII gate read a JSON file its producer
never wrote, so **on a film about published home addresses the privacy gate had never executed
once**; a CSS gate was hardcoded to `c1..c11` from when the film had eleven chunks; a card gate
defaulted to `["c1"]`, so one OK line read as a clean film-wide pass; a band gate was correct and
had simply never been run, while four chunks printed graphics under the caption band; and
**Playwright's browser binary was missing, so every DOM gate was crashing rather than checking.**

- **Derive scope from the plan file, never from a literal.**
- **Print what a gate measured, not just its verdict.** One gate's leaf rule
  (`txt.length > 0 && el.children.length === 0`) skipped every caption carrying a `<b>` accent, so
  six of twenty-two cues were never measured as a box, and its 0.39s sampling interval missed six
  more against a 0.30s shortest cue. It now prints the distinct element set it measured and refuses
  to pass on fewer than 20.
- **Grep a guard's matcher for folder-name and class-name string filters before trusting it on new
  content.** `if "broll" not in src` silently exempted three new clips in a different directory.
- **Run a negative control on every new gate**, including permissive changes to an existing one. A
  rect-intersection change made a gate pass a deliberately planted violation, because `#root` is
  `overflow:hidden` and computes to height 0 on a plain load: the gate reported PASS having tested
  nothing at all.
- **An allowlist entry that matches nothing is worse than no entry**, because it reads as "this was
  considered and handled". One inherited exemption blanket-covered a whole 15.8s chunk under a
  description of a scene that no longer lived there. Grep the allowlist's selectors against the
  current build, or delete them.

**Assert that an edit actually changed something.** A `re.sub` that matches nothing returns the
input, and the script prints success.

- Round 1's caption injection consumed its own `<!-- CAPTIONS-BEGIN -->` markers, so round 2's
  injection silently no-opped and **a full render shipped round-1 captions**, up to 3s out of sync
  with the wrong band on the close. It passed lint, validate, the safe-zone gate and a full render.
  It was caught only by grepping the file for the band class that had just been added.
- `afade=t=in:st=X` **silences everything before X.** Meant as 45ms on one beat's head, applied to
  the assembled VO it **muted 46 of 61 seconds**. The assembler's own loudness print caught it:
  LRA 4.4 to 25.6 LU, integrated down to −25.5.
- A correction table needs a test that proves it **fires**. Three films' worth of price corrections
  were dead code that read as a safety net, because whisper puts a leading space on every ordinary
  word and every entry was written to match the unspaced token.

**Read the numbers the pipeline already prints.** Loudness, LRA, frame count and duration are free
assertions, and a 6x LRA jump is not a taste question. And a render in flight is not a sunk cost:
one caption duplicate was found four chunks into a 45-minute render, and stopping cost twelve
minutes against a film to throw away.

**Hardlinked shared assets go stale when an editor REPLACES a file instead of truncating and
rewriting it.** A shared kit file (`base.css`, `chunk.js`) hardlinked into every chunk directory is
supposed to make one fix visible everywhere by construction: except some edit paths allocate a new
inode on write, which leaves every chunk still pointing at the OLD inode. Every chunk stays
internally consistent and passes every gate; the bug has no symptom until you notice the fix never
took. Re-link shared files and assert the SHA of every shared file against the canonical copy
immediately before rendering anything that depends on them.

---

## Bugs no gate catches

These are all frame-QA-only, and each has cost at least one round.

- **A styled `#id{left;top;width;height}` with no `position`** renders at flow y0 and covers the
  scene above it. This is the single most repeated defect in this system's history. Author-time
  gate: `grep -nE '^ #[a-zA-Z0-9]+\{left:' index.html | grep -v position` and confirm every hit
  inherits position from a class.
- **A non-clip child entering more than about 0.3s after its scene start** is visible for the
  whole scene, then re-pops. Needs an explicit initial hide.
- **A `fromTo({autoAlpha:0},...,{immediateRender:false})` on a child of an already-visible parent**
  renders visible from parent entry, blinks off at its tween start, then fades in. The parent's
  hide does not cover the child.
- **`fromTo` ignores from-only props.** Every prop you need applied must appear in the TO vars.
  This has been hit at least seven times.
- **A non-clip wrapper renders its own decoration for the entire composition.** A ring in a
  wrapper's `box-shadow` floated over the cover and the closing shot for 30 seconds.
- **Text without its own z-index loses to any positive-z sibling** regardless of DOM order.
- **Stacking follows DOM order, not `data-track-index`.** Move the element after the thing it must
  sit on top of.
- **A `<video>` with `data-start` nested inside another element with `data-start` renders frozen.**
  Put the timing on the video, leave the wrapper untimed. Stated as a structural rule: **`.clip`
  videos must be direct children of the stage.** Author face shots as a bare
  `<video class="clip vid">` on the stage and put per-scene chrome in a sibling timed div. `lint`
  does catch this, but only after the scene wrapper is already written.
- **Every `<audio>` needs an `id` or it is SILENT in the render.** `lint` flags it as an error and
  **the preview still plays it**, so it is invisible to the one check most likely to be run.
- **An `<svg class="clip">` element's visibility is not managed by the framework.** Only div, video
  and img clips get visibility control. A timed squiggle-arrow SVG at `data-start 15.35` painted
  for the **entire film**, appearing beside chips at 0:05, on cards at 0:07 and inside the graph at
  0:13. Wrap a timed SVG in a timed `<div class="clip">`, or do not time SVGs directly. Found by
  the owner watching, because a per-element contact sheet samples each element's own window and
  never asks whether it is absent **outside** it.
- **Same-z videos stack by DOM order, not `data-track-index`.** A `<video>` inserted mid-stack
  painted **under** a later-in-DOM full-bleed video despite carrying a higher track index. Every
  gate passed and the chunk extracted both files; the QA contact sheet was the only thing that
  showed a couch where the B-roll should have been. New overlay videos go at the **end** of the
  video stack.
- **`gsap.from()` with `keyframes` is unreliable.** `from` plus keyframes has no well-defined start
  state. Use `fromTo()` with the keyframe array in the **to** vars.
- **`letterSpacing` tweens fail the motion gate.** Layout properties snap to integer device pixels
  and stutter under seek-by-frame capture. For a type entrance use `scale` plus `y` from
  `transformOrigin:"left top"`.
- **`gsap_exit_missing_hard_kill` on a clip element is real, not a lint nit.** An exit fade on a
  clip element, or one ending at a clip boundary, needs a `tl.set(..., {opacity:0})` after it, or a
  non-linear seek lands past the fade with stale visibility. The linter's `fixHint` gives the exact
  line.
- **`opacity:0` still occupies layout, so a column that is supposed to GROW never does.** A
  comparison scene reserved its full final height from the first frame, which is why "the left one
  ends short while the right keeps going" read as two static boxes. Wrap each deferred block in
  `.grow{overflow:hidden;height:0}` and tween `height:"auto"`. Measured: both columns then start at
  232px and end at 341 against 656. **The gap is the argument, so the gap has to open on screen.**
  Related and distinct: `opacity:0` on a wrapper leaves every child fully measurable to a gate,
  whereas `visibility` **is** inherited, so `tl.set(sel,{visibility:"hidden"})` genuinely removes a
  subtree.
- **`tl.seek(t)` suppresses `onUpdate`; `tl.seek(t, false)` does not.** GSAP's second parameter is
  `suppressEvents` and it defaults to `true`, while **the renderer seeks with it false**. A canvas
  driven by the documented proxy-plus-`onUpdate` pattern renders correctly under
  `hyperframes render` and draws **nothing** in a local Playwright harness that seeks with the
  default. Half an hour went into "why is the orb blank" when the composition was fine and the
  harness was lying. **Any local seek-and-screenshot rig must pass `false`**, and the same applies
  to `tl.pause(t)`.
- **A screenshot harness does not move `<video>` elements at all.** Driving the timeline places
  every graphic correctly and leaves each `<video>` wherever it was, because nothing sets
  `currentTime`. A QA rig that seeks by hand is not applying the renderer's clip scheduling, so it
  cannot see media-timing bugs at all.
- **An element styled and animated but never present in the DOM.** GSAP no-ops silently on an empty
  selector. Grep every `#id` used in the timeline against the markup.
- **A scene background painting over its own video.** An opaque wash on the same element that
  hosts scene text, at a z above the video layer. Nothing overflows, so inspect reports zero
  issues. Washes go on their own track below the video layer.
- **A `.bcard` is an untimed wrapper around a timed `<video>`.** When the clip window ends the
  video hides and the bordered card stays on screen as an empty rectangle. In a chunked build this
  gets worse: `data-start` on the `<video>` is CHUNK-LOCAL, so copying a b-roll placement from one
  chunk's `index.html` into another carries the wrong start time silently: a clip can be entirely
  legal (fits inside its own source file, fits inside its chunk's duration) while its **card**
  stands on screen for seconds before or after the video underneath it actually plays. A guard for
  this has to walk the timeline and find the interval the CARD is actually visible in (following
  the ancestor chain for opacity/visibility), not just check the video's own window against its
  source file.
- **A `<video>` revealed only by toggling opacity/`autoAlpha`, with no `data-start` scheduling it,
  renders BLACK.** "Revealed by autoAlpha, not by scheduling" is true of the DOM and false of the
  renderer: the renderer still needs the clip's own timing to know which frame to decode. Every
  such placement needs an explicit local start time and a gate that asserts the DOM-reveal time and
  the media-schedule time agree.
- **A logo's `width` is not its height.** A 74x24 mark at `width:480` renders 156px tall and prints
  through whatever is below it.
- **`transformOrigin` in px on an SVG `<g>`** is measured from the bbox corner, not user space.
  Use `svgOrigin:"540 1120"`.
- **Absolutely-positioned siblings take no flow space**, so a `margin-top` on the next element
  lands at the top of the column.
- **A missing asset directory renders a card that paints, with a 0×0 image inside it.** No
  structural gate can see this: the card element is real and styled, it is the `<img>`/`<video>`
  src that resolves to nothing. Resolve every referenced asset path on disk before rendering, not
  just before delivery.
- **A truncated media file (no moov atom, from a killed writer) can still pass a basic size check.**
  `-s <file>` (non-empty) is not proof a video file is decodable. Frame-count every A-roll source
  and probe every recording/screen-capture asset as part of the pre-render checklist, not just
  confirm they exist.
- **A `<video>`'s `data-duration` must cover every frame its wrapper paints, or the uncovered
  frames render as a dead grey rectangle with a red X.** One stock plate was cut to 1.1s inside a
  1.82s beat, so the last 0.72s was grey. A guard for this walks every `<video>` at every beat and
  checks `painted && t ∈ [data-start, data-start + data-duration]`; verify it by shortening a
  window on purpose and watching it fire. Same family: a scene clip that expires mid-crossfade
  pops, so the window has to run past the end of the fade.
- **Staging belongs in CSS on the element that animates, not on its parent.** With
  `defaults:{immediateRender:false}` an element sits at its **own CSS value** until its tween
  starts, so a hidden wrapper does not stage its children. A staged `.cad` row whose `.num` child
  computed to `opacity:1` put "60" and "90" on screen a second before either number was spoken,
  then snapped to zero and re-entered on the word. The container version of the same bug: every
  `#sN` scene div visible from frame 0 until its own `show()` means any child without a staging
  class paints early, and an arrowhead from scene 7 sat on the first beat for its whole duration.
  One `put("#s1,#s2,...", {autoAlpha:0}, 0)` closes the whole class.
- **A beat must clear its own transition.** The film's biggest number landed at 28.220 on the
  envelope peak for "free", and the CTA wipe is 0.42s centred on 28.480, so it starts at 28.270:
  **0.05s in the clear, one and a half frames.** Nothing in lint, validate or any DOM gate has an
  opinion about this; only the render sheet showed it. Assert
  `t_land + 0.25 < t_nextcut − wipe_duration/2` before rendering, for every slam, stamp and
  counter landing. When it fails, **move the landing to the previous stressed syllable, not the
  cut.**
- **A tween scheduled past a chunk's end never runs; one scheduled before its start SHIFTS the
  whole timeline.** Four cards scheduled at 44.6 to 48.5 in a chunk ending at 42.751 never appeared
  and the chunk played 17 seconds of one still frame. In the other direction, a cue meant for
  121.100 against a chunk starting at 122.372 put **every** tween in that chunk 1.272s late,
  uniformly: GSAP does not clamp. The guard has to scan the **whole script**, not just literal
  `tl.*` position arguments, because helper functions wrap them internally, and it has to strip JS
  comments first. Chunked-build specifics are in `playbooks/longform-chunking.md` and
  `playbooks/chunk-revision.md`.
- **A font can silently fall back through every gate.** Verify glyphs at **native resolution or not
  at all**: IBM Plex Sans's serifed capital "I" disappears when a 2160-wide caption crop is
  downscaled into a comparison image, which made a true Plex render read as a fallback and launched
  a data-URI embed, two `@font-face` rewrites and a woff2 conversion, all chasing a ghost. One
  native-res crop settled it in a minute, and the same weak eyeballing had produced a false
  positive the round before. **The renderer's compile log is the ground truth**, so grep for it
  instead of squinting at glyphs:

  ```
  [Compiler] Embedded local font file: ... → data URI
  Fetched N font face(s) for "IBM Plex Mono" from Google Fonts
  ```

  The compiler embeds any local file the `@font-face` references (ttf or woff2, any `format()`
  string) and auto-fetches built-in families. **Only a MISSING file falls back silently**, which is
  what actually shipped across two delivered cuts when a chunk emitter matched `src="assets/..."`
  and never `url("assets/...")`. A glyph question is also answerable from the font file itself:
  fontTools `glyf` says Plex Sans "I" is 1 contour and 12 points (serifed), a grotesque's is 4 to 8.
- **Contact sheets lie at small tile sizes, in both directions.** At 250px two frames looked like
  they had face ghosts bleeding through; at 420px they were clean and the "ghost" was neighbouring
  tiles blurring. Then at 420px a working 0.36s dissolve looked like a tween that had never fired.
  A 6-across tile at 270px is too small to resolve another creator's face in a lifted plate.
  **Verify any suspected no-op at full resolution before touching code.**

---

## QA artefacts that are not bugs

- **`-ss` before `-i` fast-seeks to the preceding keyframe.** At `-g 15` that returns frames up to
  0.4s early and looks exactly like scene bleed, half-drawn strips and empty beats. It invented a
  whole round of phantom bugs once. Decode once with a frame-number select expression
  (`tools/qa/exact-frame-qa.sh`). Frame numbers are the only unambiguous currency.
- **Fast-seek near EOF produces pure-black JPEGs** for frames that render fine. Probe with an
  average-pixel check or re-extract with `-ss` after `-i` before treating a black tail as a bug.
- **A frame that is a solid wipe colour is a correct transition frame.**
- **Sampling at the cut time lands on an impact flash's brightest frame.** That frame is supposed
  to look washed.
- **Sampling a slam 0.25s after onset shows the clean settled state and hides the clipping.**
  Sample at onset + 0.05s.
- **ffmpeg's native VP9 decoder silently drops the alpha channel**, so a matte QA composite shows
  the full frame and lies. Decode with `-c:v libvpx-vp9` before the input.
- **Subtract a contact sheet's frame x-offset before judging centring.** A "right-shifted" element
  was dead centre.

---

## Environment

- **Broken `pyexpat` on this machine breaks yt-dlp, pip and venv.** Prefix with
  `DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib`.
- **Spotlight indexing is disabled on this machine**, so Finder Recents and `mdfind` will never
  surface a file written since it was turned off: `mdfind -name "vid66"` returns nothing for files
  that exist and decode fine. Verify every deliverable with `ls` and `ffprobe` on the real path.
  See `docs/06-delivery.md`.
- **`hyperframes preview` (the Studio) silently rewrites the project's `index.html`**, stamping
  `data-hf-id="hf-xxxx"` on every timed element. Two things break: every text-anchor edit script
  misses and its asserts fire, and a chunker's `\bid="..."` regex **matches inside `data-hf-id=`**,
  because the hyphen is a word boundary, so the planner and emitter read machine ids. The root
  duration assert was the only loud symptom. If the Studio has been opened on a project, strip the
  attributes before any pipeline run (and restore the `<!doctype html>` casing it changes), and
  never leave the Studio server running while editing the source.
- `timeout` does not exist on macOS by default.
- **zsh `set -- $var` does not word-split** (unlike bash), so `for spec in "a b c"; do set -- $spec`
  passes the whole string as `$1`. Use explicit `${spec%%:*}` parsing.
- **`ffmpeg` reads stdin and eats a `while read` loop.** `-nostdin` on every ffmpeg call inside a
  read loop, or only the first line is processed.
- **libx264 refuses odd heights.** 900x333 fails, 900x334 works.
- **Never run a DOTALL `.*?` regex to delete a block from a composition.** A comment string
  appearing in both the CSS and the JS matched across about 500 lines and silently deleted the
  document body, and lint reported the file as simply missing. Delete by explicit line markers,
  assert on the end line's content, and archive the file first.
- **Never replace a nested block by slicing to a text anchor.** One dropped `</div>` left every
  later scene nested inside an earlier one; lint, validate and inspect all passed because the HTML
  parsed. Count the closers.
