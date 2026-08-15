# `gates/` the pre-render gate

`guard.py` drives the composition's own GSAP timeline in Chromium and measures what
**actually paints** at every beat. It runs before `render`, because a render round costs
minutes and every defect below has shipped past `hyperframes lint` and `hyperframes
validate`, which read the document and the console and nothing else.

```bash
python3 tools/gates/guard.py hf67/guard.json          # the whole film
python3 tools/gates/guard.py hf67/guard.json -v       # one line per beat
python3 tools/gates/guard.py hf67/guard.json --beats 4.3,5.2
python3 tools/gates/guard.py hf67/guard.json --ids hf67/ids.json   # before AND after a splice
```

`--ids` keeps the element-id baseline. Run it once before a splice and again after: the
second run names anything that disappeared. A baseline that just reported a disappearance
is **kept, not overwritten**, or the next run silently forgets what the last one found.

Exit 0 means every check **ran** and passed. Read the coverage line before believing it.

Doctrine, when to add a gate and why gates lie: `playbooks/gates.md`.
Symptom to cause: `docs/07-troubleshooting.md`.

---

## Configure it for a new film

Copy `guard.example.json` next to the film's `index.html` as `guard.json` and edit it.
`tools/qa/shoot-sheet.py` reads the same file, so the beat list is written once.

**Every number in that file is a measurement of one film. Re-derive them, never inherit
them.** An inherited exemption list once carried an entry naming elements the current
build no longer had (matching nothing while reading as considered) and a second that
blanket-exempted a whole scene's duration, hiding 15.8s of genuine staleness.

| Key | What it is |
|---|---|
| `project` | dir holding `index.html`. Relative paths resolve against the config's own dir. |
| `timeline` | the key in `window.__timelines`. The composition must expose it. |
| `stage_id`, `stage_w`, `stage_h` | the stage element and its **unscaled** size, normally 1080x1920. |
| `beats` | every scene boundary **plus** the frames inside a beat where something lands. Numbers, or `{"t": 4.3, "label": "the slam"}`. |
| `bands` | the Instagram safe zones. Defaults are the 2026 numbers in `docs/02-safe-zones.md`. |
| `caption_replay` | `{"array": "__CAPS", "target": "cap"}`. See the note below: without it every caption rule is inert. |
| `face` | `element` (the clip-path carrier), ordered `rules` mapping inset numbers to a state name, `default`, `off_state`. |
| `states` | per face state: `text_must_clear_y`, `text_forbidden_rects`, `text_must_stay_left_of_x`, `videos_painting`, `ink_zone`, `min_ink_frac`. |
| `face_windows` | the windows his face MAY paint in. A whitelist, see below. |
| `void` | `after_t` (skip the hook) and the fallback `min_ink_frac`. |
| `contrast` | `bright` (150), `max_bright_frac` (0.35), `min_area`. |
| `stylesheets` | every stylesheet the staleness hash covers. Anything the page loads that is missing here fails. |
| `allow` | exemptions: `{"kind","match","t0","t1","reason"}`. An entry that matches nothing **fails the run**. |
| `root_id` | the composition root, default `root`. Timed elements are scanned from HERE, not from the stage: a timed element can be a **sibling** of `#stage`, and a stage-scoped query never looks at it. |
| `apply_clip_schedule` | default true. Hides managed clips outside their window before measuring, so the probe sees what the renderer sees. |
| `managed_tags` | default `["DIV","VIDEO","IMG"]`, the tags the framework gives visibility control to. |

### The face state rules

`clip-path` is how the face moves between full-bleed, split and card. State is named from
the inset numbers, first matching rule wins:

```json
{ "state": "split", "when": { "left": ["==", 540] } }
```

**Chromium collapses `inset(700px 0px 0px 0px)` to `inset(700px 0px 0px)` when left equals
right**, and collapses further from there. A guard that assumed four numbers came back
treated every collapsed value as "no clip" and reported the wrong state for a whole film.
`inset_numbers()` expands the shorthand, so write rules against `top/right/bottom/left`
and not against positions in a list.

### `caption_replay` is not optional if the film has captions

`tl.time(t, false)` **suppresses events**, so anything a `tl.call()` writes never runs for
a probe. The caption element carries no text, `isText` is false, and the crown, band, rail
and text-on-text rules all silently measure nothing. Every caption rule in this file was
inert until this was found. The composition must publish its cue array, in `hf67`:

```js
window.__CAPS = CAPS;   // gates seek with suppressEvents, so tl.call() never fires
```

If the coverage line says `0 with text`, the replay is misconfigured. That is the warning
the script prints.

---

## What each check catches, and the failure that produced it

| Kind | Catches | The failure |
|---|---|---|
| `ASSET` / `ASSETDIR` | a referenced path not on disk | `hf62/assets/shots/` did not exist, so 13.3s rendered as a blank white card. No structural gate can see it: the card paints, the `<img>` inside it is 0x0. |
| `IMG0` | an image that loaded to `naturalWidth` 0 | same class, but also catches a file that exists and is truncated. Images get their own pass because a broken `<img>` is usually an unpositioned child that the element filter skips. |
| `PAGEERR` | a page that threw on load | Playwright's browser binary was once missing on a film, so every DOM gate was **crashing rather than checking**, and the console output looked the same. |
| `CSSDROP` | a stylesheet that parsed 0 rules | one malformed CSS comment drops every rule after it (the browser resynchronises past it) and lint, validate and inspect all pass, because none of them parse the cascade. |
| `PICHASH` | a loaded stylesheet the staleness hash does not cover | `pichash` hashed `chunk.js` and `base.css` but not `vid62.css`, which held most of the film's look. The CSS fix would have invalidated nothing and shipped unapplied. |
| `OCCLUDED` | text that is positioned correctly and never paints | the vid56 short shipped with **no captions for 27 of its 43 seconds**. `.cs` carried no `z-index`, computing to auto (0), under a full-bleed `<video>` at 2. Every gate passed: safe zones check coordinates, WCAG contrast is computed from declared colours. |
| `NOPROBE` | a hit test that returned `null` | **null is not a pass.** A scaled-down viewport puts the coordinates outside it and every probe returns null, reading as a clean run. The probe drops the stage to `scale(1)` and sizes the viewport to the stage for exactly this reason. |
| `TOP` `BAND` `LEFT` `RAIL` | the Instagram safe zones | a caption box widened from 890 to 940 walked straight back into "every caption ran 50px into the right rail". Left 70 + 890 = 960, and the rail starts at 960. |
| `ONCROWN` `ONFACE` `ONSPLIT` | graphics on the presenter | 180 frame-hits of text on his face across 23 elements on one film: a rail across his chin, caveats across his mouth, the CTA on his chest. The gate that enforced this ran **only while the face was carded**, so full-bleed was unchecked. Give every state its own rule. |
| `TXTTXT` | two graphics colliding | every gate checked graphics against the face, the card and the band. Text on text was unguarded, and a panel printed on top of a caption for an entire hook. Ancestor and descendant pairs are excluded by DOM path; rotated boxes are skipped, because an axis-aligned rect is not where their ink is. |
| `VOID` | a beat that is one element over blank paper | passes lint, passes validate, passes every safe-zone rule, and reads as a hole. Ink coverage under the floor in the graphics zone is the only thing that catches it. |
| `CONTRA` | text unreadable over the picture | `validate` compares text to its **CSS** background; over an A-roll the ground is his room. 22 bare-text elements hid there. Contrast is **skipped, and the skip is counted and printed**, on any beat where a full-frame cover is up: a wipe sheet at mid-travel legitimately owns the whole frame, and seventeen WCAG failures on one film all landed at exactly `duration/2`, the midpoint of a wipe. Measured as the **fraction of area brighter than 150, never the mean**: white type on a black screen averages dark while still colliding, and a mean rated one title fine at a measured bright-fraction of 59.6%. A background counts as a ground only at **alpha >= 0.8**: a gradient at .22 is not one. |
| `VIDWIN` | a `<video>` painted outside its own window | seven of nine dashboard placements rendered dead grey, on the film whose brief was "more screen recordings". `data-start`/`data-duration` is real to the renderer even when the DOM reveals by opacity. |
| `VIDSET` | the wrong clips painting in a state | the band track must show in SPLIT and be hidden in FULL, and nothing structural checks that. |
| `FACEWIN` | the face painting outside a declared window | see below. |
| `TIMEDLEAK` | a timed element painting OUTSIDE its own window | every other check asks "did it paint when it should". Nothing asked the other half. An `<svg class="clip">` with `data-start` 15.35 painted for an **entire film**, beside chips at 0:05, on cards at 0:07, in the graph at 0:13, because the framework gives visibility control to div, video and img clips only. The owner found it; no gate did, and the per-element contact sheet could not either, because that sheet samples an element's own window and never the rest of the film. |
| `DOMBAL` | `<div>` opens not equal to closes | a splice swallowed a `</div>`, closing `#root` early. Browsers silently repair it, so the page looks fine and the render is not. That one shipped. |
| `IDGONE` | an element id that existed at the last snapshot and does not now | a marker-to-marker splice swallowed a whole GRID scene. Its tweens kept firing at nothing, every gate passed, and the beat played as bare footage plus caption for **three delivered versions**. Pass `--ids <file>`: written on first run, diffed after. A disappeared id is a disappeared beat. |
| `PROBEFAIL` | a beat the probe threw on | a gate that dies is a gate that did not run. The throw is usually the composition's own code (a `tl.call` writing to an element a splice deleted). The beat is reported as unmeasured and the run continues, rather than one traceback hiding the other 40 beats. |
| `ALLOWDEAD` | an exemption that matched nothing | see below. |

### `face_windows` is a whitelist, deliberately

List the windows his face MAY paint in; everywhere else is forbidden. A gate that
enumerates the known-bad spans cannot catch what its detector missed, and a gaze detector
missed two real down-looks three times running on thresholds alone. **A missing whitelist
window costs a beat of face. A missing blacklist entry ships the defect.** Choose which
way the gate fails. Two windows on that film carried documented overrides found by eye:
the cover frame, and his sign-off, where the classifier was confident enough to cut the
presenter out of his own goodbye.

### `allow` entries are audited

Every exemption records a hit count, and an entry that matched nothing is reported as
`ALLOWDEAD` and fails the run. An allowlist entry that matches nothing is worse than no
entry: it reads as considered while handling nothing.

---

## Before you trust a new check

**Negative-control it.** Plant the exact defect, confirm the gate FAILS, then remove it and
confirm it passes. Two gates that sound complementary can both miss the same bug for
different reasons. And a permissive change is not done until a planted defect still fails:
one widening made a gate pass a planted violation because the ancestor-clip walk clipped
the whole film to nothing, and it reported PASS having tested nothing at all.

This port was proved that way against a shipped film, `hf67`:

- clean build: `PASS`, coverage 41 beats, 204 painting elements, 45 with text, 45 hit
  tests, 0 null, 41 contrast measurements, 82 `<video>` reads.
- with the vid56 `z-index` defect replanted on the caption wrapper and a nonexistent
  `<img>` added: exit 1 with `ASSET`, `PAGEERR`, `IMG0`, 39 `OCCLUDED` and 3 `CONTRA`.
- with an `<svg class="clip" data-start="15.35" data-duration="2.0">` planted (the demi2
  defect in shape): `TIMEDLEAK` at 0.0, 10.0 and 30.0 and **silence at 16.0**, inside the
  window. Coverage went from `2 timed elements (0 unmanaged)` to `3 timed (1 unmanaged)`.
- with a splice planted that ate one `</div>` and the `#cap` element: `DOMBAL` (10 opens
  against 9 closes), `IDGONE` for `cap`, and `PROBEFAIL` on the beat where the film's own
  `tl.call` then threw on a null element, with `1 of 2 beats were NOT measured` printed.

Run against a second film with a different face grammar (card/split/off, 80 `<img>` reads),
the only finding was a `CONTRA` at a scene boundary. Shooting that frame showed a blue wipe
sheet across the whole picture: a false positive from sampling the boundary itself. That is
what added the full-frame-cover skip, which reports `contrast skipped on 4 beat(s)` rather
than passing quietly. The planted-defect run still fires 39 `OCCLUDED` and 3 `CONTRA`
afterwards, so the skip did not blunt the check.

That earlier one also proved the coverage warning: with `#cap` gone the run printed
`not one element carried text`, which is the same signal a misconfigured caption replay
gives. The warning is doing real work, not decorating the output.
