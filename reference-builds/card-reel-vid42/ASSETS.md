# vid42 assets manifest

The floating card, three.js as a recurring object, and stock footage as a ground layer.

Shipped result: `reference-cuts/card-reel-vid42-elevenlabs.mp4`. 1053 frames, 1080x1920.
**Twelve render rounds across three structures**, which is what the history in
`templates/card-reel/HISTORY.md` walks through.

Ships here: `index.html`, `package.json`, `transcript.json`, `caption.md`.

---

## A-roll, `assets/aroll.mp4`

The creator's delivered take, transcoded to 1080x1920 at 30fps.

His head is large in frame: crown y45 to 85, glasses top y430 to 460, eyes y540, mouth y810 to 870,
chin y980 to 1020 at native 1080x1920, so roughly a 940px head. **That is the fourth distinct set
of numbers measured for the same person.** Re-measure every take.

As built: band top y920, video top 540, scale 1.0,
`clip-path: inset(380px 0 0 0 round 44px 44px 0 0)`, measured chin y1500. Full-bleed width forbids
scale < 1.0; there is no more room in the source frame to zoom out into.

The floating card solved to **card top 960** (hair meets the card top at y960, chin y1540). Ported
directly from the reference build's constants it sliced his hair off, because his head is about
975px against that reference's 600px. See `playbooks/face-card-device.md`.

---

## Stock b-roll, `assets/broll/` (4 clips)

Pexels vocal-booth footage, one clip per claim. Added as a **ground layer** (`z-index:4`, above the
ambient wash, below every designed panel) because the note was "rest is fine": no beat displaced,
no layout moved.

| Clip | Under the line |
|---|---|
| `stock-ana.mp4` | "learns your tone, texture, style" |
| `stock-oneshot.mp4` | "only have one recording" |
| `stock-library.mp4` | "pick a voice from their library" |
| `stock-gate.mp4` | "screened for copyright compliance" |

`blur(7px) brightness(.44)` at opacity .52, each with a slow counter-drift.

**Graded at the ffmpeg stage** (`hue=s=0.42` plus a teal `colorbalance` push, to sit warm studio
footage under a mint and violet palette), not in CSS.

**Exposure is per-clip.** Three of the four were dark booths; the fourth was shot against a white
wall and at the shared setting it lifted the whole scene and washed out the chips on top of it. It
needed brightness .26 at opacity .42 where the others needed .44 and .52.

---

## Screenshots and marks

| Path | What | How |
|---|---|---|
| `assets/emusic-home.png` | The product homepage | Playwright at `device_scale_factor=2`. **Zooming a page screenshot inside a window device crops the left-aligned content**: measure where the column actually sits in the capture and solve the width so the column fits the window body. Landed at 1100px in a 900px window, heading 34px, at the reel-scale floor. |
| `assets/el-avatar.png` | The account avatar for the rebuilt post card | `pbs.twimg.com/profile_images/<id>/_400x400` |
| `assets/creative.png` | Newly captured for this cut | Playwright |

Everything else was **reused verbatim** from the other creator's cut of the same launch. Two
creators, one launch, one asset pool: the differentiation is theme (violet sampled from his own
room lighting), type stack and scene grammar, not facts.

The rebuilt X-post card uses real data from
`cdn.syndication.twimg.com/tweet-result?id=<id>&token=a`, which returns text, date, counts, avatar
URL and mp4 variants for any public tweet with no auth. **`is_blue_verified` is in that JSON: do
not draw a badge the account does not have.**

At 900 wide the card's right edge sat at x990, inside the like/comment rail for its lower half, and
lint, validate and inspect all passed it. **Solve the width from the centre:
`width <= 2 * (960 - 540) = 840`.**

---

## Fonts (7, all in `library/fonts/`)

```
clash-600  clash-700  satoshi-500  satoshi-700  satoshi-900  geist-mono
instrument-serif-italic-400-it
```

---

## SFX, `assets/sfx/` (15 cues)

From `library/sfx/house/`. Note `boom`/`cboom` and `riser`/`riser2`: on a later film that same pair
naming turned out to be **byte-identical duplicates**, which is why a "17 file" bed had far less
perceived variety than its count suggested. Check for duplicates when curating.

Delivery came off the renderer at **+4.0 dBTP**. The two-pass `loudnorm` with `-c:v copy` is not
optional on this SFX-dense grammar.

---

## three.js

`assets/three.min.js` from `library/vendor/`, **UMD build only**. An ES-module script defers, and
the capture engine reads `window.__timelines` synchronously after load, so a module build silently
produces a dead page.

Used on exactly **two beats**: the hook (a rigid machine lattice collapsing into a
waveform-modulated voiceprint sphere on "your actual voice") and the analyzer's output sigil (the
same cloud re-forming from scatter inside a DOM instrument bezel). **The object recurring is what
makes it feel designed rather than decorative.**

Sizing is arithmetic: at fov 42 / cam z 6 the visible height is 4.606 world units over 1920px, so
1px = 0.0024u. Round 2 shipped a sphere about 1670px across that swamped the title and ran under
the captions, purely because nobody did that division. See `playbooks/threejs.md`.

4600 points, about 376 tweens, no measurable hit on render time.

---

## Audio

`assets/vo.m4a` in the original build. `transcript.json` (word-level whisper) ships here and is
what every beat is anchored to.
