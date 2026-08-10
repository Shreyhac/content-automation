# Stock footage

Tools: `tools/stock/pexels_search.py`, `pexels_fetch.py`.

---

## Sourcing

- **Pexels works without an API key**: hit `pexels.com/download/video/<id>/` with a plain browser
  User-Agent. The 403 is on the page HTML, not the download endpoint. The `?h=1080` param is
  ignored, so you get the top rendition and re-encode down.
- **Coverr is curl-open**, and the reliable download URL is the `og:video` meta tag on the video
  page. Scraping `cdn-staging` URLs off the page body gets unrelated sidebar and paywall videos.
- **Pixabay pages stay JS-locked to curl.**
- **Pinterest is a genuinely usable unauthenticated pipeline, and still the wrong primary
  source.** `pinterest.com/resource/BaseSearchResource/get/?source_url=…&data={"options":{...}}`
  with a plain browser UA answers unauthenticated, paginates by bookmark, and every video pin
  exposes an HLS master `ffmpeg -c copy` can download directly: confirmed working, 65 pins across
  nine queries. It loses anyway: video pins cap at 720×1280 (a ~2.5× upscale into a 2160×3840
  composition) and the pool is dominated by re-uploads, including one otherwise-great clip that
  carried another editor's watermark. **When asked to try an alternate source, report the result
  even when it loses**: "it works, here is why it still loses" is a more useful answer than
  silently reverting to the default.
- **Pexels' search page 403s a plain `curl` but not Playwright, and only the FIRST query in a
  session reliably returns results**: later queries in the same browser context come back empty
  unless each gets a fresh context and a ~6 second gap.
- **A company's own YouTube channel is the best "team" b-roll there is.** Real employees in a real
  space, on-claim in a way stock office footage can never be. Label the source on screen and it
  reads as citation rather than decoration. `yt-dlp --download-sections "*00:02:00-00:02:14"
  --force-keyframes-at-cuts` pulls 14 seconds in about 10.

---

## Ban the shoot, not just the id, and ban the metaphor too

A same-client repeat production found a "new" clip 168 ids away from one already shipped to that
client, from the shape of one photographer's batch upload: a same-video threshold of 60 ids
(generous against an earlier finding of 12-apart siblings) missed it entirely. **Widen the
near-duplicate threshold aggressively (300, not 60): a false rejection costs one candidate in
twelve; a false accept costs a clip the client has already watched: the asymmetry favours erring
wide.** Two more repeat shapes a simple id-distance check cannot see on its own:

- **Clusters within one result set.** Three same-shoot pairs turned up in a single query; picking
  two of them repeats a shot inside the same film even with no cross-film collision at all.
- **Cross-theme collisions.** Two ids one apart, from the same photographer's batch, cast for two
  *different* chunks of the same film (e.g. a magnifier beat and a stamp beat): read separately
  they look unrelated; side by side they are the same shoot appearing twice.

**A metaphor can repeat even when no id does.** Reusing a "verdict" beat's own visual metaphor (an
aerial fork in the road) in a follow-up production, sourced from an entirely different clip, is
still the same shot to a viewer who watched both. No id check catches this: it is caught only by
writing new search queries against a list of what previous productions for the same client already
spent, and checking the metaphor as well as the footage.

**A previously-rejected clip stays rejected on the facts about the clip, not on its id alone**: if
a candidate was rejected once for a specific visible reason (an operator's hand in frame, a colour
cast), re-surfacing under a new id with the same visible fault is still the same rejection.

## Always look at the footage

**Never trust the slug. Extract a midframe from every downloaded clip and look at it.**

The reject rate is about **one in three even on hand-shortlisted, premium-looking results**:
"server racks" returned a messy office AV closet, "modern data center" returned a daylight
logistics-park aerial. A night skyline had a bank logo burned in, and one search screen was in the
wrong language.

For some subjects free stock is close to useless and **dangerously so**: a search for old book
pages returned Bible pages, night sky returned a cemetery coffin. Of 22 harvested clips for one
devotional reel, six were usable.

**Audition the in-point, not just the clip.** Two cutaways were correct clips landing on the wrong
second, one on smoke and one on an abstract insert. A contact-sheet frame at t=5s does not tell you
what t=0.6s looks like. **Check the frame at the offset the edit will actually use.**

Stitch three to five candidate sections into one contact sheet with PIL and read it as a single
image.

---

## Placement

### Card it, never full-bleed

This is the rule that makes stock read as designed rather than dropped in, and it solves the 9:16
problem at the same time: **landscape stock never has to be centre-cropped and upscaled**, so it
stays sharp, and it cannot clash with the theme because the card frame and scrim are themed.

**Reuse one strip and tag-pill pair for every placement.** Consistent frame, radius, border, shadow
and mono tag make five different clips read as one system.

A card wants a Ken Burns push on the **video** (scale 1.0 to 1.08) while the **card** stays still.
Pushing the card breaks the layout grid.

Where a full-bleed treatment is unavoidable, use the blurred-plus-darkened copy of the same clip
behind a sharp card in front.

### Slot it into space the layout does not need yet

**"I want more stock footage" is a density note, not a count.** One cut per act, placed only where
the layout already has free space, so nothing gets re-timed. Five cuts across 56 seconds reads
generous; more starts competing with the UI story.

**Audit free vertical space BEFORE choosing clips, not after.** Two of four candidate slots turned
out to have none once captions were placed. Measuring first saves re-encoding.

**A b-roll strip belongs below y150.** One placement sat inside the IG top chrome band; moving the
strip, eyebrow and card down as a group fixed it without touching any timing.

### As a ground layer, when the note is "rest is fine"

Add it at `z-index:4`, above the ambient wash and below every designed panel. No beat is displaced,
no layout moves, and about 11.5 seconds of a reel starts reading as real. `blur(7px)
brightness(.44)` at opacity .52 with a slow counter-drift.

---

## Relevance

**"Relevant" means it connects to the line it plays under.** One clip per claim: a singer at a mic
under "learns your tone", a mic close-up under "only have one recording", an artist in headphones
under "screened for copyright compliance".

Generic technology b-roll under a beat that already has a real product surface is the same failure
as borrowing a vendor demo's subject. On one build stock footage was **declined with the reason
stated**, because all ten beats already carried the tool's own live interface. Offering the one
honest place for it and waiting beats assuming.

**The cut is the point.** A clip that merely sits there is wallpaper. The three that worked in one
short each cut in on a word.

---

## Grading and encoding

**Grade every clip toward the palette** so it reads as designed:

```
eq=saturation=0.62:contrast=1.04,colorbalance=rs=0.05:gs=0.01:bs=-0.06
```

pulled blue machinery and lavender renders into a paper and gold world.

**Grade at the ffmpeg stage, not in CSS.** CSS filters cost render time on every frame and are
harder to tune per clip.

**Exposure is per-clip, never per-layer.** Three dark booths and one white-wall clip at a shared
setting lifted the whole scene and washed out everything on top of it. One needed brightness .26 at
opacity .42 where the others needed .44 and .52. **A shared filter is an assumption that the plates
are exposed alike.** Frame-check each plate separately.

**Re-encode every downloaded clip** with `-g 30 -keyint_min 30 -an`. The compiler warns that sparse
keyframes cause seek failures and frame freezing, and it means it. Encode at display size.
libx264 refuses odd heights: 900x333 fails, 900x334 works.

**Do not over-grade.** One round crushed b-roll to murk and then laid a 0.55 vignette on top of it
from the card style, which was half of why the clips read as poor.
