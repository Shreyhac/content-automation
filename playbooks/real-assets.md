# Real assets and fact-gating

"Show the real asset of everything you say" is a standing rule on at least one channel and good
practice on all three. A reel is debunkable exactly where it invents.

---

## Verify before you plan

**Verify every repo, product and figure through its API or source before writing a word of the
plan.**

- **GitHub**: paths move. `All-Hands-AI/OpenHands` now redirects to `OpenHands/OpenHands`, and the
  on-screen path has to be the current one. Star counts, language and SPDX come from the same call.
  **Re-check immediately before delivery**: they moved 29 stars in one hour on one build.
- **A named feature may live one layer down.** A script said "companion mode"; the product's blog,
  changelog, help centre and every search result had nothing by that name. It existed as a run-shape
  documented only in the product's own repo skill files, found with
  `gh api "search/code?q=companion+repo:<org>/<repo>"`. **When marketing pages come up empty on a
  named feature, code-search the product's repo before concluding the claim is false.**
- **Verify the NUMBER in a claim, not just the concept.** "Pitches five creative directions" turned
  out to be verbatim spec, which made the scene: five rows, two tail chips. A claim that survives
  literal verification is worth designing literally.
- **Vendor prose contradicts vendor tables.** Quote the softer number. Preview-post figures go
  stale at GA. Read numbered lists carefully: captions *under* items have been welded into one
  claim.
- **The story is usually not in the vendor's announcement.** Independent evals and buried system-card
  sections have carried everything worth posting.
- **The vendor's caveat usually sits in the same paragraph as the damning quote.** Include it.
  Omitting it makes the reel debunkable; including it makes the narrator trustworthy.
- **A registry/marketplace page is the source of truth for "is this the real X," ahead of star
  counts or search results.** `https://skills.sh/api/search?q=<name>` returns canonical
  `owner/repo/id` triples with install counts, and the page carries the exact install command in a
  copy box: every command shown on screen was sourced from there, not written from memory.
- **Verify a filtered capture actually applied the filter before it goes in the frame.** A
  screenshot of `openrouter.ai/models?max_price=0` still showed a `from $0.13/second` card because
  the URL param silently no-op'd, and the on-screen claim ended up asserting the opposite of the
  headline. A screenshot is a *claim*; prefer the underlying API (e.g. `/api/v1/models`) over a
  filtered page URL for anything the frame is counting.
- **Run the larger transcription model on numbers before auditing a claim.** `whisper small`
  dropped a figure entirely ("405 plus or 635 plus" → "435 plus") and separately mangled a correct
  number into a wrong one, on two different productions: on each, the small model's error was
  read as the *creator's* error before the medium/large model corrected it. **Numbers spoken at
  speed are exactly what a small model mangles, and a claim audit is nothing but numbers.** Keep
  the small model's word timings (they are already solved) but re-run the big model over any take
  whose on-screen text is numeric.
- **Resolve a named person's identity through an account you have already verified, not through
  the domain that matches their name.** A script named "Emil Kowalski"; `emilkowalski.com` belongs
  to a different person entirely (a Polish marketing founder, photo on the page). The actual
  design engineer is at `emilkowal.ski`, found via the GitHub API's `blog` field on his verified
  account. Screenshotting the obvious domain would have put a stranger's face on screen as the
  subject.

---

## When the recorded VO is wrong

**A fabricated claim in an already-cut VO is a decision, not a blocker.**

Ask it as a scoped choice (soften on screen / build literally / hold for a re-record) rather than
stopping. Then write the fact gate at the top of the breakdown and repeat it in the caption pack,
so whoever posts it knows what a commenter can and cannot be shown.

**The honest-edit pattern**: the VO keeps the drama, the frame carries the truth. A KILLED stamp
with a `→ merged` chip under it. A correction rendered as evidence: "REMOVAL ATTEMPTS: JUN 22 ✕
JUL 7 ✕ JUL 19 ?" turned a fact-check that contradicted the hook into support for its thesis.

**Where a figure does not exist, show that.** An unpublished count became a deliberately empty
dashed region with a "?" rather than an invented second number.

**Sponsored work has no margin.** Resolve promo codes against the partner URL, never against
whisper. Attribute every figure on screen. A competitor's figures are attributed to the competitor
and never rendered in the alert colour. A verdict carries the VO's own qualifier.

---

## Capture

`tools/qa/playwright-capture.py`. `color_scheme="dark"`, `device_scale_factor=2`, viewport around
760px wide for 1080-wide placement. Over-capture in one run: variants and a full-page tall shot
are cheap; going back for a missed shot is not.

- **Dismiss a cookie banner by clicking it, never by `remove()`ing DOM nodes.** Nuking wrappers has
  blanked a capture. Click "Reject non-essential", then `scrollIntoView({block:'center'})`.
- **Some hosts hard-403 headless Chromium** including referer tricks. A plain browser User-Agent
  plus `--disable-blink-features=AutomationControlled` gets past some bot challenges. Otherwise
  have the owner Save-Page-Complete into Downloads.
- **A Next.js site's compiled CSS `:root` is the fastest exact source for a brand's system**:
  `curl` `_next/static/css/*.css` and regex the block. Better than screenshots, especially on
  scroll-animated sites which screenshot mid-animation.
- **Charts often embed their own data** inline in the page or system card. Rebuilding a chart from
  that data out-renders a screenshot and stays on-brand. Grep is unusable on 800KB single-line HTML;
  use Python.
- **A maintainer's own README hero images are the fastest real product surfaces there are**:
  `api.github.com/repos/.../readme`, base64, regex the image URLs.
- **A marketing page can be the real product UI, even when the app itself is login-gated, if the
  page plays a scroll-triggered demo of it.** One product's marketing site auto-played its own
  playbook editor (slash menu, block chips, an agent dropdown) as an `IntersectionObserver`
  animation. Static full-page captures showed **empty panels** because the sections render on
  scroll. Fix: `wait_until="load"` (these sites keep sockets open, so `networkidle` times out on
  them), scroll slowly first to trigger the observers, then screenshot per-`<section>` at ~1–1.5s
  intervals. Delete any support-chat widget/iframe before shooting or it lands in every frame.
  **Before rebuilding a product's UI from scratch, check whether its own marketing page animates
  the real thing.**
- **The real screenshot already brings its own cursor.** Compositing a synthetic pointer over a
  captured UI plate that already contains one puts two arrows on screen. If the capture shows a
  pointer, do not add one.
- **A copyrighted/IP character generator refuses by name and often by careful paraphrase too.**
  One image model refused a named superhero in every phrasing across four attempts (some only
  after ~70s of silent moderation); a different model (Nano Banana Pro /
  `gemini-3-pro-image-preview`) produced it correctly on the first try. Keep a fallback order for
  IP characters rather than iterating prompts on a model that has already refused a plain
  description. Prompt pattern that mattered: explicitly state **"absolutely NO panel border, the
  background extends to all four edges"**. Without it the model draws a comic-panel frame welded
  to the figure's own silhouette, which then keys badly.

---

## Rebuild what you captured

**A real screenshot inside a browser device still fails the legibility rule.** A 1280-wide docs page
scaled into a 960 card is unreadable, which is exactly the "reads as vague" failure.

> **Keep the real chrome and the real URL, which is the trust device. Rebuild the page BODY as
> native HTML at reel type sizes** (30px+ body, 58px heading), quoting the real wording.

**"The actual UI" means an accurate REBUILD that can perform, not a capture of the real one.** A
note that reads as "use the real pixels" can mean the opposite once the client sees a screenshot on
screen: it is inert (cannot type, cannot focus a field, cannot be zoomed without going soft, and
at 1080-wide it reads as a blurry rectangle: literally "vague"). The capture's real value is as a
**design spec**: copy the real chip shapes, field styling and colours from it, then build a version
that types character-by-character with a caret, opens its own menus, and takes a camera move. A
zoom on rebuilt content is only legible if the content can survive the scale: solve the container
width so `content_width * max_scale < view_width` **before** animating the push-in, not after the
first render clips a line.

Trust comes from the frame and the link; legibility comes from the rebuild.

- **Crop from the 2x capture, never downscale the whole page.** A 1440-wide viewport shot at 820px
  display is 0.5x and its text is 7px. Cropping a roughly 1300px-wide *detail* of the 2x capture
  displays at about 1.3x CSS and is readable at reel scale.
- **Derive crops from source pixels, never by eye.** Pick a region containing whole elements
  (`x0,y0,x1,y1` in source px), then `scale = boxWidth/(x1-x0)`, `img.width = sourceWidth*scale`,
  `left = -x0*scale`, `top = -y0*scale`. The box height falls out of the region; it is not chosen.
  **Check legibility on a full-resolution crop**, not on a downscaled QA frame.
- **A card size drives the crop, not the other way round.** And a crop that is short on the left
  shows the *previous* column: check the sign against the artefact, because the instinct to move x
  the wrong way costs a round each time.
- **Frame each state so the number being spoken is large.** Fitting a whole page into a screen made
  the payoff figure illegible on the exact beat that says it.
- **Terminal and agent UIs are HTML mocks by default** and out-render a screenshot, built from the
  real screenshots' wording so nothing reads AI-generic.
- **Zooming a page screenshot inside a window device crops left-aligned content.** Centring the
  image is not centring the content column: measure where the column sits in the capture and solve
  the width so it fits the window body.

---

## Logos

- **Simple Icons** for brands: `cdn.simpleicons.org/<slug>`, and it takes a hex
  (`/coolify/101014`). jsdelivr's `simple-icons` package is the fallback when the CDN returns empty.
- **Google's favicon service** for news outlets, which Simple Icons dropped:
  `google.com/s2/favicons?domain=<d>&sz=128`. White 5px-padded tiles normalise mixed-shape favicons.
- **Coloured dots and monograms read as placeholders and get called out.** Real marks read premium
  instantly. So do monospace **text chips** standing in for brand marks: called "too shitty" on
  two different beats of the same film. `cdn.jsdelivr.net/npm/@lobehub/icons-static-svg@<ver>/icons/<name>.svg`
  covers most dev-tool/AI brands (~29 pulled in one loop for a provider list); the monochrome ones
  carry `fill="currentColor"`, which resolves correctly with zero extra work on a light/ink
  background. **Render every logo to one sheet and look at it before wiring any of them in**: a
  dead mark (wrong colour, wrong background) is worse than the text it would have replaced.
- **One film, one cast: a second improvised character for the "same job" reads as two different
  productions.** A hand-drawn mascot standing in for a beat where the house pixel-sprite character
  should have appeared was flagged even though the client's note only named a different scene; the
  actual fault was two characters doing the same job. If a house character exists, reuse its
  literal asset rather than drawing a new one for a new beat.
- **SVGs render directly as `<img>`** in HyperFrames. No PNG conversion step.
- **Verify a logo asset has alpha before applying `brightness(0) invert(1)`.** Playwright element
  screenshots are RGB with no alpha unless `omit_background=True`, and a page rendered onto a white
  body never has it: two marks shipped as solid white boxes. Rewrite the real SVG's fills instead.
- **Light and white marks vanish on paper.** Verify by rendering every mark on the actual card
  colour in one headless page before wiring them in.
- **A wordmark is not a logo tile.** Horizontal lockups need the icon cropped out (`crop=H:H:0:0`)
  or a 92px tile shows three letters.
- **Recolour a mark that dies on its chip** (a light teal fill on a white chip).
- **SVG `<use>` defs must appear BEFORE every use.** Hoist a 0x0 defs svg to the top of the scene;
  forward refs render blank.
- **For an exact geometric brand mark, hand-write the official SVG paths.** It beats a generation
  round-trip.
- Prefer **public-domain** portraits over CC BY-SA: share-alike plus attribution is unworkable on a
  reel. Credit CC BY photos in the caption.

---

## Compositing a real mark onto a generated plate

An image model asked to draw a specific product's icon (or a legible UI on a screen inside a
photographic plate) draws an invented glyph or illegible type no matter how the prompt is worded.
**Compositing the real asset onto the generated plate beats regenerating the plate**:

- Build the icon once from the client's own SVG plus their documented gradient formula, matched to
  their design tokens.
- Locate the AI-drawn stand-in's silhouette in the plate via colour-range masking + convex hull,
  measure its rotation off the hull's top edge, and alpha-composite the real icon into that exact
  position/rotation/size.
- Same technique for a UI shown on a screen inside a photo: perspective-transform the real
  screenshot onto the four corners of the AI-drawn screen. Get the quad corners right: a
  mis-measured perspective warp looks worse than no attempt and should be deleted rather than
  shipped half-right.
- **This is optional, not a rule, when the screen/icon is background texture rather than the
  subject.** A soft out-of-focus screen that is never the focus of the shot can be more believable
  left un-composited than pixel-perfect and sharp. Ask which the surface is (subject or texture)
  before spending the compositing pass on it.

## Honesty guards worth copying

- **Fact-gate a logo wall.** A wall for an LSM-tree explainer means LSM-family logos only; including
  a database that is NoSQL but not LSM would make the reel debunkable.
- **Print the real licence string** and say `SELF-HOST` for source-available products rather than
  the word "free".
- **Do not render an invented command name or file path** for a pre-launch product. Build the proof
  beat from the site's own real UI copy, labels only, and leave out counters whose real values are
  unknown.
- **Leave an inflammatory adjacent item out** when the VO does not reference it.
- **Never borrow a demo's SUBJECT as filler.** Stills from a vendor's launch film put six SpaceX
  rockets in a reel that never mentions SpaceX. The vendor film is legitimate as product-UI evidence
  and never as generic imagery. A contact-sheet scene should be posters of **this reel's own beats**.
- **Refuse what would misrepresent the product**, such as photographs of real people on cards
  representing AI-generated voices.
