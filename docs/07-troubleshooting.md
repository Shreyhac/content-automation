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

**Render dies at the same frame with `Protocol error (Runtime.callFunctionOn): Target closed`, or
hangs at 0% CPU, with plenty of memory free.**
Single-worker screenshot leak, not RAM. On <= 8GB, HyperFrames forces low-memory mode (one worker
plus screenshot capture), and Chrome leaks per screenshot until a session crashes. Bigger frames
exhaust it sooner. Two levers together: transcode every A-roll to `scale=1080:1920` (an oversized
master is 2.25x the pixels), and render with `--no-low-memory-mode --workers 4` so each session
captures fewer frames. Raising `--protocol-timeout` only makes a hang wait longer.

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

---

## Bugs no gate catches

These are all frame-QA-only, and each has cost at least one round.

- **A styled `#id{left;top;width;height}` with no `position`** renders at flow y0 and covers the
  scene above it. This is the single most repeated defect in this system's history. Author-time
  gate: `grep -nE '^  #[a-zA-Z0-9]+\{left:' index.html | grep -v position` and confirm every hit
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
  Put the timing on the video, leave the wrapper untimed.
- **An element styled and animated but never present in the DOM.** GSAP no-ops silently on an empty
  selector. Grep every `#id` used in the timeline against the markup.
- **A scene background painting over its own video.** An opaque wash on the same element that
  hosts scene text, at a z above the video layer. Nothing overflows, so inspect reports zero
  issues. Washes go on their own track below the video layer.
- **A `.bcard` is an untimed wrapper around a timed `<video>`.** When the clip window ends the
  video hides and the bordered card stays on screen as an empty rectangle.
- **A logo's `width` is not its height.** A 74x24 mark at `width:480` renders 156px tall and prints
  through whatever is below it.
- **`transformOrigin` in px on an SVG `<g>`** is measured from the bbox corner, not user space.
  Use `svgOrigin:"540 1120"`.
- **Absolutely-positioned siblings take no flow space**, so a `margin-top` on the next element
  lands at the top of the column.

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
