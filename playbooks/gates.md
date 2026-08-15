# Gates

The doctrine. The code is `tools/gates/guard.py` and its README; this is when to add a
gate, why gates lie, and the order to run them in.

A gate is a script that fails a build for a defect a human would have to notice. This
system has grown about eighteen of them (`card_guard`, `band_guard`, `safe_zones`,
`paint_guard`, `motion_guard`, `snap_guard`, `sched_guard`, `asset_guard`, `broll_guard`,
`audio_guard`, `cut_guard`, `facesafe_guard`, `contrast_guard`, `css_guard`, `dead_guard`,
`pii_guard`, `clip_guard`, `frames_guard`), and `guard.py` is the portable distillation of
the ones every film needs. What they taught, past what any one of them checks, is below.

---

## Running order

Everything before `render` is cheap. Everything after it costs minutes to an hour. Push
work leftwards.

| # | Step | Catches | Cost |
|---|---|---|---|
| 1 | `npx hyperframes lint` | markup and schema errors | seconds |
| 2 | `npx hyperframes validate` | WCAG contrast against **declared** CSS colours | seconds |
| 3 | `npx hyperframes inspect` | layout overflow | seconds |
| 4 | `python3 tools/gates/guard.py <film>/guard.json` | assets, paint, safe zones, text on text, voids, contrast over video, video windows | ~1 min |
| 5 | Playwright `pageerror` | a dead page. Folded into 4 and into the contact sheet, but assert it separately if you script your own probe: a page that threw on load screenshots perfectly well | seconds |
| 6 | `python3 tools/qa/shoot-sheet.py <film>/guard.json` | a beat that reads empty, a colour that dies, a character in the wrong place | ~1 min |
| 7 | `npx hyperframes render -q high -f 30` | | minutes |
| 8 | Frame QA on the render, `playbooks/frame-qa.md` | everything the model of the renderer got wrong | minutes |

Steps 4 to 6 are the whole point of this file. They did not exist for the first dozen
films and every defect they check for shipped at least once.

**Fix `lint` and `validate` before running 4.** They are faster and their failures cascade.

**A render in flight is not a sunk cost.** A caption defect found four chunks into a
45-minute render was worth stopping immediately: twelve minutes lost against forty-five
plus a film to throw away.

---

## Why gates lie

### A gate that has never run is not a gate

On one film the first build passed `lint`, `validate` and three custom gates and was
queued to render. Then:

- the privacy gate read a JSON file that a different script had never written. On a film
  about published home addresses, it had **never executed once**.
- the CSS gate was hardcoded to `c1..c11`, a chunk list from an earlier plan.
- the card gate **defaulted to `["c1"]`**: one OK line, reading as a clean film-wide pass.
- the band gate was correct and had simply never been run. Four chunks were printing
  graphics under the caption band, confirmed later in an actual render frame.
- Playwright's browser binary was missing, so every DOM gate was **crashing, not
  checking**.

A green run and a gate that silently did nothing produce the identical console output.

**Derive scope from the plan file, never from a literal. Print what the gate measured,
every run: element count, beat count, chunk list, hit-test count.** `guard.py` prints a
coverage line before its verdict for this reason, and warns loudly when not one element it
measured carried text.

### A gate that runs in only one mode is not a gate for the other mode

`card_guard` enforced the graphics/face split **only while the face was carded**. In
full-bleed there is no card edge, so nothing checked anything, and elements were placed by
eye into the middle band, where he is. 180 frame-hits of text on his face across 23
elements: a rail across his chin, caveats across his mouth, the CTA on his chest.

Same shape, different gate: two gates walked `document.querySelectorAll('.scene')` and one
chunk's hook markup did not carry that class, so the film's **first nineteen seconds**, the
thing every viewer sees, were never measured by either gate, on any film, in any run.

**Before trusting a gate, check what it does NOT look at.** Enumerate the states, and give
every state its own rule.

### Position is not visibility

The vid56 short shipped with **no captions for 27 of its 43 seconds** and every gate
passed. `.cs` carried no `z-index`, so it computed to `auto` (0) while the face video sits
at 2. The captions were exactly where they belonged, y1396, inside every Instagram zone.

- `lint` and `validate` read the document and the console. A caption behind a video is
  neither a markup error nor a console error.
- a safe-zone gate measures WHERE an element is. It has no concept of which element owns
  the pixel that lands there.
- WCAG contrast passed too, because contrast is computed from **declared** colours.

The only test that settles it is `elementFromPoint` at the element's own centre returning
that element. Two things make it honest, and both were found by it failing wrongly first:

1. **Probe at the composition's real size.** A scaled-down viewport puts the coordinates
   outside it, `elementFromPoint` returns null, and **null reads as a pass**. `guard.py`
   drops the stage to `scale(1)` and sizes the viewport to the stage, and counts nulls as
   `NOPROBE` failures rather than silence.
2. **Replicate the renderer's clip scheduling before hit-testing.** A plain page load
   stacks all 22 caption clips at identical coordinates, so the last one in the DOM wins
   every hit test, reporting a failure on the other 21 and telling you nothing.

And the corollary for reading feedback: **when a note says an element is in the wrong
place, check whether a different element is invisible.** The note on that film was drawn
around the hook, "put the captions at the bottom, not on top like this". They were already
at the bottom. They were underneath the picture.

### Every check asks half a question

Every rule in this system asked "did it paint when it should". Nothing asked "did it paint
when it should NOT". An `<svg class="clip">` with `data-start` 15.35 painted for an entire
film, showing up beside chips at 0:05, on cards at 0:07 and in the graph at 0:13, because
the framework gives visibility control to div, video and img clips only. The owner found
it by watching. No gate could have: the per-element contact sheet samples an element's own
window, which is the one stretch where that element is supposed to be there.

`guard.py` now checks both halves (`TIMEDLEAK`). The general form is worth applying to any
new gate: **write down the negation of what you just checked, and ask whether anything
tests it.**

Same discipline, different axis: a gate scanning from `#stage` misses a timed element that
is a **sibling** of the stage rather than a child of it. Scan from the composition root and
let geometry be the only thing that is stage-scoped.

### A splice needs its own two checks

A marker-to-marker text splice swallowed the scene that lived between the markers. The
removed beat's tweens kept firing at nothing, every gate passed, and it played as bare
footage plus caption for **three delivered versions**, because the QA sheets in those
rounds sampled around 9.x and never inside it.

1. **Diff the element ID list before and after.** A disappeared id is a disappeared beat.
2. **Count `<div>` opens against closes.** An imbalance closes `#root` early, browsers
   silently repair it, and the render is wrong while the page looks right. That shipped too.
3. And generate the delivery contact sheet **from the clip list**, so every element's own
   window is sampled at least once (`shoot-sheet.py --from-clips`).

### A gate that dies is a gate that did not run

When the probe throws on a beat, report that beat as unmeasured and keep going. A Python
traceback on beat 2 of 41 tells you nothing about the other 39, and the throw is usually
the composition's own code, not the gate: a `tl.call` writing into an element a splice
deleted takes out the probe that would have named the splice.

### Whitelist, not blacklist, for presenter rules

A gaze gate that listed the spans his face may **not** paint in cannot catch what its
detector missed, and per-sample thresholds failed three times before the shape changed.
It is now a whitelist: the windows his face MAY paint in, everywhere else forbidden.

**A missing window costs a beat of face. A missing blacklist entry ships the defect.
Choose which way the gate fails.** Two windows on that film carried documented overrides,
both found by eye and both real: the cover frame, and his sign-off, where the median dips
because his eyes narrow when he smiles. A classifier confident enough to cut the presenter
out of his own goodbye needs a human check, not more thresholds.

### An allowlist entry that matches nothing is worse than no entry

A motion gate's ALLOW carried `("c15", 0.0, 99.0, "the CTA")` from an earlier chunk plan.
In the current plan c15 was the comparison scene, **blanket-exempted for its entire
duration**, hiding 15.8s of genuine staleness, while its sibling entry pointed past the end
of a 17.9s chunk and matched nothing at all while reading as if it had been considered.

`guard.py` counts hits per `allow` entry and fails the run on any entry that matched
nothing (`ALLOWDEAD`). **Re-derive exemptions per film, from measurement.**

Same shape outside the gates: a caption price-correction table matched `"$420"`, but
whisper emits a **leading space** on ordinary words, so the real token is `" $420"` and the
table had never matched anything across three films of reuse, read as a safety net the
whole time. **A correction table needs a test that proves it FIRES**, not just that it
exists.

### Two gates that sound complementary can both miss the same bug

A malformed CSS comment silently dropped every rule after it (the browser resynchronises
past it) and `lint`, `validate` and `inspect` all passed, because none of them parse the
cascade. `css_guard` was built for it and proved by replanting the exact defect. Its
sibling `dead_guard`, which looks for elements that should paint and do not, reported
**CLEAN on that same defect**: the dropped rule was the element's only paint source, so it
has no background, border or text and gets filtered out as "not a painting element" before
the zero-area test runs.

**Negative-control each gate independently.** And **a permissive change to a gate is not
done until a planted defect still fails it**: widening a band check to intersect with every
clipping ancestor (a correct fix for a false positive) also made the gate pass a planted
violation, because the root computed to height 0 on a plain page load and the ancestor walk
clipped the whole film to nothing. It reported PASS having tested nothing at all.

### `tl.time(t, false)` suppresses events

Seeking a GSAP timeline with `suppressEvents` does not run `tl.call()`. Anything written by
a call, and the caption engine is exactly that, is **absent from every probe and every
screenshot**. The caption element carries no text, `isText` is false, and every caption
rule silently measures nothing. Every caption rule in `guard.py` was inert until this was
found, and it looked like a clean run the whole time.

The composition publishes its cue array (`window.__CAPS`) and both the gate and the contact
sheet replay it after seeking. If the coverage line says `0 with text`, the gate measured
nothing.

### The staleness hash must cover every shared stylesheet

`pichash` hashed `chunk.js` and `base.css` but **not** `vid62.css`, which held most of the
film's look. A CSS fix in it would have invalidated no stamp and the resumable render would
have reused the stale chunks and shipped without the fix. One film did ship stale.

Related: the hash strips `<audio>` deliberately, so picture edits still fail the guard and
audio-only edits correctly do not. Recovered renders carry no stamp at all. **Check the
stamps actually went stale before a resumable render.**

### A missing asset directory passes every structural check

`hf62/assets/shots/` did not exist, so a 13.3s scene rendered as a blank white card. No
structural gate can see it: the card paints, it is the `<img>` inside it that is 0x0. And
the media has to be **readable**, not merely present: five A-roll cuts were truncated with
no moov atom by killed writers, and `-s` (file exists and is nonempty) passed all of them.
Resolve every referenced path on disk, assert `naturalWidth` at runtime, and frame-count
every A-roll before the flight.

### A void is a defect, and no structural gate has an opinion about emptiness

One element over blank paper passes lint, passes validate, passes every safe-zone rule and
reads as a hole. So does a frame mid-tween, between one element finishing its exit and the
next starting its entrance: not static, not overflowing, not a contrast failure. Two
answers, and use both:

1. the **ink-coverage floor** in `guard.py`, a percentage of the graphics zone that must
   be covered, per face state.
2. the **contact sheet**, `tools/qa/shoot-sheet.py`, before you believe the film is
   composed. Ink coverage cannot see a colour that dies or a character standing in the
   wrong place.

### Contrast over video needs its own check

`validate` compares text to its CSS background. Over an A-roll the ground is his room, and
22 bare-text elements hid there on one film, including every eyebrow in it.

Two subtleties, both learned by getting them wrong: use the **fraction of area brighter
than about 150, not the mean** (white type on a black screen averages dark while still
colliding; the mean rated one title fine at a measured bright-fraction of 59.6% and it was
unreadable), and treat a background as a ground only when its **alpha is >= 0.8**, because
a gradient at .22 is not one.

### Guard text against text

Every gate on one film checked graphics against the face, the card and the band. Two
graphics colliding with **each other** was unguarded, and a panel printed on top of a
caption for an entire hook, illegible, found only by reading frames out of the finished
render. Measure by box, exclude by DOM ancestry (a parent overlapping its own child is not
a collision), and skip rotated boxes, because an axis-aligned rect is not where their ink
is.

---

## When to add a gate

Add one when **a defect reached a render, or a human, twice**, or once if it reached the
client. The trigger is not "this could go wrong": it is a specific frame that shipped.

Then:

1. **Name the failure in the docstring**, with the film and the measured number. Every
   check in `guard.py` carries its own, so nobody deletes one thinking it is theoretical.
2. **Negative-control it.** Replant the defect, watch it FAIL, remove it, watch it pass.
3. **Print what it measured**, not just its verdict.
4. **Make its scope a config, derived from the plan.** Hardcoded chunk lists and inherited
   allowlists are the top two ways a gate quietly stops covering the film.
5. **Prefer a whitelist** wherever a detector, not a rule, decides what is bad.

And the counterpart: put enforcement in the tool rather than in a checklist. The SFX
builder refuses to inject a bed that breaks the share cap, the median or the ceiling,
which is why the bed rules have not been broken since.

---

## See also

- `tools/gates/README.md`, the config reference and the per-check table.
- `playbooks/frame-qa.md`, what to do after the render, and the contact sheet step.
- `docs/07-troubleshooting.md`, symptom to cause for the render and delivery failures a
  gate does not catch.
- `docs/02-safe-zones.md`, where the band numbers come from.
