# Generative assets

Cloned voices, image-to-video plates, AI-drawn scenes, and the music under them. Everything here
was learned on client UGC work where the presenter, the room and the product shots were all
generated, so the failure mode is never "the model refused". It is that the output looks fine in
isolation and reads as fake in the cut.

The governing rule, which every section below is a special case of: **measure the generated asset
against the real thing it is standing in for**, band by band, region by region, frame by frame. An
eyeball pass approves all of these.

Companion reading: `playbooks/real-assets.md` for capturing and rebuilding real product surfaces,
and `docs/03-quality-bar.md` for why AI-slop is a carrier problem rather than a palette one.

---

## Voice cloning

### Fit the EQ by iteration against the source's own band profile

The fault in a clone that sounds wrong is **spectral shape, not loudness**, and it is not where
instinct puts it. A first fix measured a single 2 to 5 kHz "consonant" band and looked solved.
Splitting into eight narrow bands showed the TTS was putting its energy **either side** of the source
actual voice:

| Band | Source voice | The generated read |
|---|---|---|
| 400 to 700 Hz | **50% of total energy** | 33% |
| 250 to 400 Hz | | +6.5% excess, mud |
| 700 to 1200 Hz | | +8% excess, boxy |
| 1200 to 2000 Hz | | +6.3% excess, nasal |

**Measure, compare, adjust, repeat.** Do not choose frequencies by ear. Seven rounds took total
deviation from **44.9 to 7.2**, and the decisive move was **−7.7 dB at 900 Hz**.

**Do not "add body" to match a percentage.** A +2 dB shelf at 190 Hz, added to lift the
400 to 700 Hz share toward the source's, spilled upward into 250 to 400 Hz and *caused* the mud. Cut the
excess; do not boost the deficit.

Know what the EQ costs: reshaping the envelope dropped the lip-sync correlation metric from
**0.310 to 0.243**. Both numbers are worth having in front of you before choosing.

### Never pre-process a voice-clone sample

Denoising a 20.8s reference with `afftdn` before handing it to ElevenLabs cost **19% of its
consonant energy**. Re-cloning from the untouched audio on identical settings **doubled** consonant
energy.

The cleanup chain in `docs/05-audio-and-sfx.md` is for a take that ships. A clone reference is
training data, and every artefact you remove is detail the model then cannot reproduce.

### `eleven_v3` is mandatory when using audio tags

`eleven_multilingual_v2` **speaks the tags aloud**. Whisper caught it reading a
`<break time="0.45s"/>` as "you're a king".

**Transcript-verify every TTS candidate before scoring it on anything else.** A candidate that
loses on timbre but says the right words is fixable; one that says the wrong words is not, and
sorting by quality first means auditioning nonsense.

Match the creator's own cadence rather than the model's default: measured at **3.62 words/sec**
with clause pauses of 0.20 to 0.54s, median 0.26s. A first flat VO had exactly one 0.13s pause in
it; four tagged breaks fixed it.

### Re-master audio onto an existing clip rather than regenerating

Mux the new master onto the approved clip with `-c:v copy` and re-seat it by cross-correlating
against the old audio track (**+10 ms** on the case that produced this). That saves a full
generation per audio revision, and it keeps a picture the client has already approved.

---

## Image-to-video plates

### A deadpan plate produces a deadpan clip, whatever the model

The instinct when a generated performance is flat is to change the video model. The input still
was the problem. Regenerating the plate as **mid-sentence and engaged** (brows lifted, mouth open
mid-word, eyes live) lifted **brow motion +17% and lip-sync +8%** on the same model with the same
audio.

**But asking an image model for a new expression makes it silently redress the room**: two of three
variants did. Diff the background against the approved plate, not just the face.

### The model comparison, measured

| Model | What it does |
|---|---|
| HeyGen Avatar IV, `expressive` | **The least expressive option available**, despite the name |
| OmniHuman v1.5 | Wins lip-sync on a neutral plate, then **drifts the background in the last third** |
| Kling `ai-avatar/v2/pro` | **Holds the room locked** |

Pick for the failure you cannot fix in post. Background drift is unfixable; a slightly softer
lip-sync is not visible at reel scale.

### Measure drift on a crop around every face and hand, never globally

**Global `mean|Δ|` against frame 0 looked acceptable while a hand was morphing into a second face
at the subject's hairline.** Cropping to the head region exposed it climbing **12 to 24**.

Sample a crop around every face and every hand in a generated clip **separately**. A global average
over a mostly-static plate cannot see a local catastrophe, and the local catastrophe is the only
thing a viewer will look at.

When a take is clean early and rots late, **trim to the clean window and mirror it back**, forward
plus a reversed tail. Note that setting `--last-image` to the *input* still also forces the framing
to return, which kills a push-in that a negative prompt could not.

### Pin the target pose in the prompt AND the negative prompt

Recorded on vid15 round 1 rather than in the main log, but it is the same class of fault. Kling's
`--ref` drags the **reference pose** along with the likeness. The fix is both halves together:
state the target pose in the prompt, **and** name the reference pose in the negative prompt
("seated, sitting down, phone held upright, phone screen toward the subject's face").

**And a held pose drifts mid-clip, in the opposite direction.** At the i2v stage the subject's arms uncrossed
and a hand melted into their sweater **within 1 second**. Name the body part that must not move, and
verify frames at **0.1s, mid and end**, not just the last frame.

### Extend a generated shot backwards with `--last-image`

When a note asks for an earlier shot to cover a gap and there is no footage left, generate a take
that **ends** on the approved take's first frame:

```
--image <slightly tighter crop of the source still>  --last-image <the source still>
```

Because the approved take was i2v'd from that same still, its frame 0 **is** the still, so the two
clips join with no cut at all. Measured average colour across the join: `86766b` against `877569`,
one to two levels per channel. The start frame is a real crop of the source, never an outpaint, so
nothing is invented at either end.

**Pick the model for the keyframe control, not the house habit: Kling 2.6 i2v has no
`--last-image`, `seedance-1-5-pro` does.**

---

## Compositing onto a generated plate

An image model asked for a specific product's icon, or for legible UI on a screen inside a
photographic plate, draws an invented glyph or illegible type **no matter how the prompt is
worded**. `playbooks/real-assets.md` carries the method (colour-range mask, convex hull, rotation
off the hull's top edge, alpha-composite; perspective-transform for a screen). Two rules belong
with the generative side of it:

**A mis-measured perspective warp looks worse than no attempt and gets deleted rather than shipped
half right.** That happened once here and the beat shipped without the composite that round, which
was the correct call.

**Any hard-edged region operation on a photographic plate reads as pasted, however good the content
inside it is.** Defocusing a laptop screen with `crop` then `gblur` then `overlay` gives an
axis-aligned rectangle, but the screen is a **trapezoid in perspective**, so the box overhung the
bezel onto the cushion and the client's note was "the window is being stitched". They were
describing the blur, not the UI under it.

The fix: build a **feathered polygon mask of the actual glass quad**, `alphamerge` it onto the
blurred copy, and `overlay` that. **Pull the quad in about 6px** so the soft edge lands on the
bezel rather than past it.

This applies to every region operation, not just blur: a crop, a tint, a censor box, a colour lift.
If it has a straight edge that does not follow a real edge in the plate, it reads as a paste.

---

## Music

**AI-generated music gets rejected.** An ElevenLabs bed was generated, tempo-matched and
sidechain-ducked carefully to the cut's beat grid, and came back as **"too shitty music bro, eww"**,
followed by "can't you find one pre-existing non-copyright music". The production effort spent on
it counted for nothing, because the objection was to the category.

**Use a real royalty-free library.** Mixkit works and is scriptable:

- Track pages 301-redirect to `mixkit.co/free-stock-music/discover/<slug>/`, and the direct mp3
  sits at `https://assets.mixkit.co/music/<id>/<id>.mp3`.
- `curl -A "Mozilla/5.0" -L <url>` fetches it, no auth. Tag pages such as
  `mixkit.co/free-stock-music/tag/technology/` embed the asset URLs.
- Licence: Stock Music Free License, commercial use including paid ads, no attribution required.
- The SFX side of the same site uses a different pattern, documented in `docs/05-audio-and-sfx.md`.

**Pixabay does not script.** Its music pages return 403 to automated fetching even on public search
URLs, its SFX downloads are login-walled (a full hover-and-click crawl returned 0 files), and its
stock pages stay JS-locked to `curl`.

**Then audition the bed for ticks before choosing it.** The track that replaced the AI bed on one
film was itself swapped later because it carried a metronomic 0.465s percussion tick on a 129 BPM
grid that three rounds of SFX purges got blamed for. Transient-count candidates: the winner
measured **30 transients against 75** for the one it replaced, and verified at **4 non-VO
transients, none periodic**. See `docs/05-audio-and-sfx.md`.

**A client's own supplied clip keeps its own audio** at unity in the bed, with the music fading
underneath. A zero-SFX instruction is about added cues. And probe that clip before designing a
handover to it: one client outro's track was digital silence at **−240 dBFS**.

---

## The checklist

1. Clone from untouched reference audio. Never denoise it first.
2. `eleven_v3` if there are audio tags at all, and transcript-verify every candidate before
   scoring it on anything else.
3. Fit EQ by measured band deviation against the real voice, cutting excess rather than boosting
   deficit.
4. Build the plate mid-sentence and engaged, then diff its background against the approved one.
5. Measure i2v drift on a crop around every face and every hand, at 0.1s, mid and end.
6. Pin the pose in the prompt and the negative prompt both.
7. Composite real marks and real UI onto the plate. Delete a warp you cannot measure.
8. No straight edges that do not follow a real edge in the plate.
9. Licensed music, transient-counted before it is chosen.
10. Re-master onto the approved clip with `-c:v copy` rather than regenerating it.
