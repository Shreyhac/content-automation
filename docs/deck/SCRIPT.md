# Presenter script

Two presenters, nine slides, about five minutes. Deck at
`https://shreyhac.github.io/content-automation/deck/`. Arrow keys or scroll.

**S** = Shreyansh, the creator side. **SID** = Siddhant, the engineering side.
Swap them if you prefer, but keep one voice per slide. Two people alternating
inside one slide reads as under-rehearsed.

Say the numbers out loud. They are the strongest thing in this deck and they are
all verifiable.

---

## Slide 1 &middot; Eight hours of editing. One command.

**S** (about 30 seconds)

> I post reels. A good forty second take takes me five minutes to record and about
> eight hours to turn into something postable. Cutting the dead air, timing captions
> to the word, building the graphics, keeping text off my own face, sound design,
> then three rounds of notes with an editor.
>
> So we built the thing that does the eight hours. Four reels it made have done
> **four hundred and thirty four thousand views**. I will show you the Instagram
> insights in a minute.

Let the counters finish before you speak over them. They take about a second.

---

## Slide 2 &middot; A five minute take costs eight hours

**S** (about 25 seconds)

> Every creator picks one of three bad options. Edit it yourself and your output
> collapses to whatever you personally can cut. Hire an editor and you are paying,
> plus you are describing video problems in text.
>
> That last part is the one nobody solves. **"The caption thing at the start looks
> weird"** is not something anyone can act on. So the editor guesses, burns a render,
> and guesses again. Round three is usually round one restated.

Point at the red quote. Do not read the three cards aloud, the room can read.

---

## Slide 3 &middot; The flow

**SID** (about 60 seconds, the longest slide)

> Eight stages. I will call out the three that are not obvious.
>
> **Stage two.** Beats do not come from the transcriber. Whisper smears emphatic
> delivery, so we take onsets off the audio envelope instead. On one film fifty four
> of sixty nine beats moved by more than sixty milliseconds.
>
> **Stage three.** We measure the presenter's head with Apple Vision before any
> layout happens. Crown from person segmentation, chin from the face contour. The
> face bounding box is not the head, it stops at the hairline, and that mistake puts
> captions on someone's chin.
>
> **Stage five is the one I care about.** A gate drives the composition in a real
> browser and hit-tests what actually paints at every beat. Not what is positioned,
> what paints.
>
> And **stage seven** is the differentiator. Feedback happens on the frame. Scrub,
> drag a box, type the note.

Gesture at the screenshot on the right when you say stage seven.

---

## Slide 4 &middot; Four template systems

**S** (about 20 seconds)

> These are real frames from real shipped films, four different systems out of one
> pipeline. A floating face card, a paper split, a chunked long form, and a fast cut
> ad format at under a second and a half per shot.
>
> Fifteen more finished films ship inside the repo as proxies, so the standard is
> watchable, not described.

---

## Slide 5 &middot; 434,738 views. Not a mockup.

**S** (about 35 seconds, this is the slide that wins it)

> This is my account, it is public, and these are Instagram's own insight screens.
>
> One fifty two thousand. One thirty. Seventy nine. Seventy three.
>
> But the number I would look at is **saves and sends**. Instagram ranks on sends per
> reach, and these four were saved fifteen thousand times and sent to another person
> nearly ten thousand times. That pulled fourteen hundred follows off four videos.

Slow down here. Let each number land. This is the proof, do not rush it.

---

## Slide 6 &middot; It refuses to ship its own mistakes

**SID** (about 40 seconds)

> Every check in this table exists because something shipped broken.
>
> The best one: captions sat at exactly the right coordinates, correct position, no
> z-index, so they painted **under** a full bleed video. No captions for twenty seven
> of forty three seconds, and every conventional linter passed it. Coordinates are
> not a paint test.
>
> On top of the gates there is a benchmark that scores the finished file against
> thirteen thresholds. We ran it against three films that had already been delivered
> and approved by a client. **All three failed.** It found banned punctuation in
> nineteen delivered caption packs and nine seconds of frozen video inside an
> approved cut.
>
> That is the system catching what a human reviewer already missed.

---

## Slide 7 &middot; Two paths, both in the repo

**SID** (about 25 seconds)

> We are being straight about scope. The web app genuinely edits your file: crops it
> to nine sixteen, cuts the dead air, burns captions clear of the Instagram UI band,
> normalises loudness. Nine seconds.
>
> The full pipeline is forty to fifty minutes, because an agent is authoring a
> composition and rendering 4K. A web request cannot do that, so we do not pretend it
> can. Both paths ship and the README says which is which.

If a judge is going to poke a hole, it is here. Saying it first removes the hole.

---

## Slide 8 &middot; Reel Review: stop describing video in words

**S** (about 40 seconds, this is your slide, you are the one who leaves the notes)

> This is the part I actually use every day.
>
> When a cut comes back wrong, I do not type a paragraph. I scrub to the frame, drag a
> box over the problem, and type one line. The frame with my drawing baked into it is
> what the editor sees, so there is no interpreting what I meant.
>
> Those notes export as the brief for the next round. When it goes to a client, one
> private link, and a re-render stacks as v2 under the same link so they can wipe the
> old cut against the new one instead of comparing from memory.
>
> And the order is enforced: fix, reply to every note, push, and only then share. Send
> the new cut first and every note you just addressed still looks ignored.

**SID** can add one line if there is time:

> Coordinates are stored normalised, so a note left on a laptop lands in exactly the
> right place on a phone.

## Slide 9 &middot; Clone it. Run it.

**S** (about 20 seconds)

> Clone it, one script checks your environment, and you are running. No install for
> the web app, no API key, no network.
>
> Every editing rule in there carries the failure that produced it. So whoever clones
> this inherits our mistakes without having to pay for them.

Leave this slide up during questions. The repo URL stays on screen.

---

## Questions you will get, and the honest answers

**"Is the demo real or is it a canned video?"**
Both, and the app says which. Upload is real, the edit is real, the review canvas
and the notes are real, the download is real. The pipeline stages between them run
on a timer instead of the renderer, because a 4K render is forty to fifty minutes.
Offer to upload their phone video on the spot. It comes back cropped, cut and
captioned in under ten seconds.

**"How is this different from CapCut or Opus Clip?"**
Two things. A template tool does not know where your chin is, so it puts text on
your face; we measure the head with Vision per take and the constants never travel
between videos. And nothing else lets you leave feedback by drawing on the frame,
which is the actual bottleneck in working with an editor.

**"Did you build this during the hackathon?"**
The production system predates it and has shipped 67 reels. The web app, the
benchmark, the gate bootstrapper and the deck were built here. Say that plainly.

**"What is the business?"**
Creators who talk more than they edit, and small studios where one editor caps how
much the channel can publish. Pricing tiers in the app are mocked and labelled.

**"What broke?"**
Good question to answer with specifics, it builds credibility. A coverage check that
summed overlapping rectangles, so a full frame video measured 212 percent covered
and the gate could never fail. And a display font that had never once loaded,
because the woff2 we grabbed was the Cyrillic subset.

---

## Before you walk up

- Open the deck **and** `localhost:8787` in separate tabs, already loaded.
- Have one short vertical video on the desktop, ready to drag in.
- Know which slide you own. Do not narrate each other's slides.
- If the local server is dead, the deck alone carries the pitch. Keep going.
