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
- **A company's own YouTube channel is the best "team" b-roll there is.** Real employees in a real
  space, on-claim in a way stock office footage can never be. Label the source on screen and it
  reads as citation rather than decoration. `yt-dlp --download-sections "*00:02:00-00:02:14"
  --force-keyframes-at-cuts` pulls 14 seconds in about 10.

---

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
