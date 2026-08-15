# Reel Factory

**Upload a raw talking-head take. Get back a finished, posting-ready vertical reel, and mark up
anything you want changed by drawing on the frame itself.**

Built on a production system that has shipped **67 reels across 4 template systems**. The editing rules in
this repository are not invented for a demo: every one of them is the residue of a real video
being rejected and re-cut.

---

## The problem

A creator records a good 40 second take in five minutes. Turning it into something postable takes
**six to eight hours**: cutting the dead air, transcribing and timing captions to the word,
building graphics, keeping text off their own face, checking Instagram's safe zones, sound design,
and then three rounds of "no, not like that".

So most creators do one of three things, and all three are bad.

| What they do | What it costs |
|---|---|
| Edit it themselves | The eight hours. Output volume collapses to whatever they can personally cut. |
| Hire an editor | Money, plus a feedback loop conducted over voice notes and screenshots. |
| Use a template tool | Every reel looks like every other reel, and the template does not know where their chin is. |

The second one has a specific failure that nobody solves: **feedback about video is almost
impossible to express in text.** "The caption thing at the start looks weird" is not actionable.
The editor guesses, burns a render, and guesses again.

---

## What Reel Factory does

**1. It edits.** Word-level transcription, beats taken from the audio envelope rather than the
transcriber, face geometry measured with Vision, captions timed to word onsets, graphics composed
in HTML and rendered at 4K.

**2. It refuses to ship its own mistakes.** A pre-render gate drives the composition timeline and
measures what actually **paints** on every beat: text landing on the face, an element outside the
Instagram safe band, two graphics colliding, a beat that is one element over blank space. These
are the four classes of defect that shipped past conventional linting on real videos.

**3. Feedback happens on the frame.** Scrub to 0:12, drag a box over the problem, type the note.
Coordinates are stored normalised, so a note left on a laptop lands in the right place on a phone.
No more "the thing near the start".

**4. It knows when it is wrong.** `tools/qa/benchmark.py` scores a finished file against 13
measured thresholds, each one carrying the film and the client reaction that set it.

> When this was built, it was run against three already-delivered, client-approved films.
> **All three failed.** It found banned punctuation in 19 delivered caption packs, 9.1 seconds of
> frozen video in an approved cut, and one place where the written documentation contradicted what
> the creator actually wanted. That is the tool doing its job.

---

## Try it

Node 18 or newer. Nothing else. No `npm install`, no API key, no network.

```bash
node web/server.js
# open http://localhost:8787
```

Then:

1. **Access.** Click **Skip, use demo account**. Or bring your own Anthropic or OpenAI key: it is
   validated by shape in your browser and is never sent to the server or to the provider.
2. **Source.** Drop in any video file.
3. **Build.** Watch the pipeline run, about 40 seconds.
4. **Review.** Pause, drag a red box over anything, type a note. Click a note to seek back to it.
5. **Delivery.** Download the finished MP4.

### What is real, and what is staged

Judges reasonably ask this, so it is stated up front rather than buried.

**Real:** the upload, the review canvas, the notes (stored, seekable, deletable), the download,
the HTTP range requests that make scrubbing work, and the reel you are watching, which is a real
shipped and client-approved film.

**Staged:** the 40 seconds between upload and result run on a timer rather than invoking the
renderer. The stage names are the real pipeline steps, but a genuine 4K render takes 10 to 25
minutes. That does not fit in a demo slot, and pretending otherwise would be the actual dishonesty.

The real pipeline is the rest of this repository. It is not a mock, it just is not a web request.

---

## How it is built

```
web/server.js        Node built-ins only. No dependencies at all.
web/public/          Vanilla JS, hand-rolled animation, four colours, three typefaces.
tools/gates/         guard.py, the pre-render gate. Drives the timeline in a real browser
                     and hit-tests what paints.
tools/qa/            benchmark.py, the measured quality bar. Contact sheets, frame extraction.
tools/vision/        Head measurement. Crown from person segmentation, chin from face contour.
tools/review/        The same on-frame review loop, as a CLI, used in real production.
docs/  playbooks/    The method. Every rule carries the failure that produced it.
```

**Storage** is a local JSON file by default, with an optional Supabase mirror
(`web/config.example.json`, `web/schema.sql`). The mirror is deliberately fire-and-forget: the
local store stays authoritative so a slow network cannot blank a live demo.

**Design** is deliberately not generic SaaS. Four colours, no rounded corners, no gradients on
type, one accent used sparingly.

---

## Engineering notes worth a look

- **The gate refuses to run on an unfinished config.** Some values, like which rectangle the
  graphics are supposed to own, cannot be derived from the composition. `derive_config.py`
  bootstraps everything derivable and marks the rest `TODO`, and the gate exits rather than
  running half-blind. A gate that reports PASS without having measured anything is worse than no
  gate.
- **A coverage check that could never fail.** The blank-space check summed overlapping rectangles,
  so a full-frame video measured 212% covered and the floor was mathematically unreachable. Now it
  computes true union area. Same film measures 100%.
- **Notes survive resizing** because rectangles are normalised at write time, not at read time.
- **Range requests are implemented properly**, including 416 on an unsatisfiable range. Without
  206 responses the scrubber cannot seek, and the review step is the entire product.

---

## Status

A working prototype, built in one sitting on top of a production system that predates it. Payment
tiers on the final screen are mocked and clearly labelled. Every state has been driven end to end
in a headless browser with zero page errors, at both 1440px and 390px.
