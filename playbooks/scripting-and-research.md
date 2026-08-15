# Scripting and research

Everything upstream of the A-roll: what the reel should be about, what shape the script takes, and
what has to be verified before a word of it is spoken. This is the stage with the largest
multiplier on the finished file, and the one this system spent longest without a written method.

The evidence base is one creator's own 36-post history plus 16 competitor reels deconstructed into
buildable scripts, both audited 2026-08-06.

---

## The script bank

Four artefacts, and they are read before scripting or scoping anything new:

| File | What it is |
|---|---|
| `scripts-only.md` | **The build source.** 16 entries, each a competitor transcript plus the script to shoot from it |
| `refs/` | The reference reels. MP4s are gitignored, `refs/fetch.sh` rebuilds them. `refs/sheets/*.jpg` are contact sheets (read as images to recover an edit), `refs/tx/` word-timestamped transcripts, `refs/README.md` the manifest |
| `reference-editing-language.md` | Cross-cutting style analysis of all 16 |
| `instagram-performance-2026-08-06.md` | His own 36-post performance audit, the *why* behind the script shapes |

**The method is: match a new A-roll to a script in the bank and continue.** The bank is not a
library of ideas to browse, it is a set of proven shapes with a transcript attached, so a new take
either fits one of them or the shape has to be argued for on its own. vid60 was the first build off
the bank (entry 16).

Where the creator has recorded a reference's script **verbatim**, the reference's own edit becomes
the shot list. **Re-time by word, not by ratio.** vid67 mapped 39.53s of reference onto 35.23s of
delivery: `difflib` over the two normalised word sequences anchored **136 of 148 words**, each
reference cut was mapped through the piecewise-linear result and then snapped to the nearest word
onset in his take. Every boundary landed within 0.24s of an onset, most inside 0.10s. A flat ratio
would have drifted a third of a second by the CTA.

---

## Grievance beats tutorial, by up to 140x

He made three videos on the same topic, agents losing memory:

| Framing | Plays |
|---|---|
| The **joke** about it | 143,621 |
| The **warning** about it | 2,443 |
| The **tutorial** for it | 1,016 |

Monotonic. He has 1,453 followers against a 2,874 median and a 143k best, so nearly all reach comes
from strangers, and a tutorial only lands on people who already care.

**Write the complaint first. Add the fix only if there is room.**

The qualifying test for any hook: *would someone who has never used Claude Code understand the
first line and think "yes, that annoys me too"?* If not, it caps near 2k.

**The hook shape, taken from his own winners:** *[the tool] does [annoying human thing], [absurd
image or hard number]*. Personify the AI as a bad coworker. A number or a picture, never an
adjective.

---

## What the performance audit actually says

Pulled 2026-08-06 from the Instagram web feed API: 1,453 followers, 36 posts (35 video, 1 image),
401,315 total plays.

| Metric | Value |
|---|---|
| Median plays | 2,874 |
| Mean plays | 11,466 |
| Top 2 videos' share of all reach | **67.8%** |
| Bottom 17 videos' share | 8.1% |

The median post reaches roughly 2x the follower count. **Two videos carry the account.**

**The two breakouts** (both from the July 10 to 12 window, 51s and 49s, the longest tech posts in
the catalogue): goldfish memory / "first date with your codebase" at 143,621 plays, 2,186 likes and
1,034 comments; token burn / "$40 deep by 9am" at 128,305 / 1,924 / 561. They share a shape nothing
else in the catalogue has: Claude Code personified as a bad employee, **no lead-magnet CTA** (the
caption opens on the shared frustration), complaint not tutorial, and comment rates of 0.72% and
0.44%. The arguing is what carried the reach. Next tier down: "Claude builds ugly websites" at
20,488 with 239 comments, and a model-price index chart at 20,097.

**Reach is trending down about 35% in a month.** Median by window: Jul 5 to 15 gave 3,139 across 12
posts, Jul 16 to 26 gave 3,000 across 8, Jul 28 to Aug 4 gave 2,039 across 10. The July spike never
lifted the floor.

**The dead lanes, measured:**

- **Careers and jobs.** Free certs 799 (0.6x median); ghost job listings 1,872 (0.6x), 65s, the
  longest video on the account, and the weakest-performing sponsored post in the set. Worth knowing
  before pricing that sponsor's next slot.
- **Tool demos with no pain framing.** AI music 843, a canvas/Figma replacement 1,207, a face swap
  2,206 (0.8x).
- Two Spanish-caption lifestyle posts (5,837 plays on an 8s clip) are teaching the algorithm the
  wrong audience.

**The comment-CTA is not the problem, topic strength is.** The naive read was CTA fatigue: no-CTA
median 3,215 against 2,502 with one. Comment rates kill that read. DESIGN 1.17%, API 1.12%, MEMORY
0.89%, certs 0.50%, ElevenLabs 0.00%. A CTA post converts above 1.1% when the payload is genuinely
wanted (DESIGN 239 comments on 20,488 plays; API 58 on 5,199) and near 0% when the topic is soft.
**Keep the mechanic, fix the topic.** The no-CTA gap is an artefact of the two July outliers.

**Do not read duration as the lever.** The best four are 51s, 49s, 27s and 37s; the worst recent is
65s. Completeness of the story is the variable.

Caveats on the data: these are public play/like/comment counts only, so they show *that* a reel
failed, not whether the hook or the hold killed it. Retention, saves and shares live in Insights
and have not been pulled.

---

## The competitor editing language

**Nick Saraev, Brock Mesarich and Jack Roberts have independently converged on the design language
this repo already specifies**: ivory background, terracotta accents, an Anthropic pixel mascot,
serif-italic emphasis over Inter, screenshots in rounded cards, face card at the bottom with the
graphic above. Saraev's version of it does 14k likes.

**The palette is not the gap. Layout discipline and hook writing are.**

Steal outright, **the two-caption system**: serif italic ALL-CAPS, black on ivory, when a graphic
is on screen; plain sans lowercase, white with a soft shadow, when the face is. Two registers,
switched by what is on screen. Saraev holds it across three videos and it is why 40 seconds reads
as authored rather than assembled.

Also worth lifting:

- Progressive line-art diagrams that gain labelled brackets shot by shot (Keshav Sukirya).
- A sticky title pill, so a mid-scroll viewer gets the premise.
- Figma-style green selection handles around UI (Brock Mesarich).
- Numbered serif-italic `Step N:` labels (Kallaway).
- Coloured keyword highlighting inside captions (JP Middleton).

**The story lane is a different edit entirely.** Varun Mayya's XZ video: no split screen, no CTA,
animated data-viz on black, stock footage, the face rare and full-bleed, numbers as dramatic
reveals. That is the reference for the 143k grievance lane. It got 7,608 likes and **42 comments**,
which is reach, not DMs. **Do not bolt a keyword CTA onto that format.**

---

## Fact-gating the script

`docs/01-pipeline.md` §2 is the procedure. What belongs here is the failure rate, because it is
high enough to plan around: on recent films the VO overstated a claim roughly as often as not.

- vid55's hook was true (free keys via NVIDIA NIM) and its OpenRouter claim was false.
- vid60's VO overstated the free-provider count. The repo documents 290 providers, 90+ free, and
  about 1.53B tokens a month; the frames carry the true numbers, which are also the stronger ones,
  and his audio was left alone.
- vid61's VO overstated the output formats: HTML only.
- vid67's "you never touch the terminal" is false: the quickstart is three terminal commands.

**A fabricated claim in an already-recorded VO is a decision, not a blocker.** Put the true number
on the frame, leave his audio alone, and write the fact gate at the top of the breakdown so
whoever posts it knows what a commenter can be shown. **The one number that cannot be sourced gets
cut, not invented**: vid60's hook wanted a Claude Code price to count down from, so the `$0`
decodes in place instead.

The correction also belongs in the CTA document, which is where the depth lives. vid67's generator
carries a "what the reel says that this doc corrects" block: the no-terminal claim, that it costs
API credit, that it is an unmaintained reference implementation, that it is token-heavy. See
`docs/06-delivery.md`.

### Read a reference for what its frames claim, not just whether they are clean

"Use the creator's visuals, no block around that" still has content that cannot ship. On vid67 six
windows were unusable on their own terms: the creator's account name in four shots, his **live
`ANTHROPIC_API_KEY` in plaintext**, a third party's meeting notes, and a real person's inbox.

Two more mattered more than all of those. The reference's own screen shows the launch **failing**
("insufficient credit balance") and the spec page stamped `PLANNED · NOT LAUNCHED`, underneath a
voiceover claiming it deployed and runs daily. **The creator faked his own payoff**, and lifting
the frames would have shipped a contradiction at exactly the beat the reel exists to sell.

Two mechanics for the same problem:

- **A guard that has never fired is not a guard.** vid67's first face detector thresholded skin
  fraction at 0.10 and passed a clip cut deliberately from a known face segment, which measured
  0.059. Calibrated against real data at the crop geometry the clips actually use, skin does not
  separate at all: a face frame measures 0.0455 and a UI lift 0.0452. **Luminance separates by 28
  levels with no overlap** (face 107 to 113, UI 37 to 80). Requiring both in the same frame flagged
  all eight known-face cuts and passed all eleven UI lifts. Drive a detector to the state it is
  supposed to catch, every time.
- **Vision misses a face that is only a forehead.** It found two full-bleed segments in one
  reference; a skin-fraction sweep over the band found three. The one it missed, where only a
  forehead and eyes are in frame, is exactly the one that bled into two lifted clips. When the
  detector needs a whole face and the crop contains part of one, use a statistic that does not.

And read every lifted clip full-frame before it goes near a card. See `docs/01-pipeline.md`.

---

## How to re-pull the performance data

The reels tab caps at 12 and a JS `window.scrollTo` does not trigger lazy load; real scroll events
do. The reliable path is the feed API from page context in a logged-in session:

```js
fetch('/api/v1/feed/user/<user_id>/?count=12&max_id=…',
      {headers:{'x-ig-app-id':'936619743392459'}, credentials:'include'})
```

Paginate on `next_max_id`. Output filters can block responses containing URLs, so strip
`https?://\S+` and query strings out of captions before printing.

---

## What to do with all of it

1. Read the audit's dead lanes before agreeing a topic. A career/jobs reel starts at 0.6x median.
2. Write the complaint. Test the first line against a stranger who has never used the tool.
3. Match the A-roll to a `scripts-only.md` entry, or argue for the shape on its own terms.
4. Fact-gate every claim before the plan, not before the delivery. Assume one will be wrong.
5. Pick the caption register system up front: two registers switched by what is on screen.
6. If the script promises a payload, the payload is a first-delivery deliverable. See
   `docs/06-delivery.md`.
