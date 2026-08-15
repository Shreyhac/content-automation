# `generative/`

The tooling for the lane where the presenter, the room, the product shot and the music are all
generated. `playbooks/generative-assets.md` is the doctrine; these four scripts are that doctrine
with the measurements wired in, so the checks cannot be skipped by being busy.

The lane's failure mode is never "the model refused". It is that the output looks fine in
isolation and reads as fake in the cut. So the governing rule, which every tool here implements a
special case of: **measure the generated asset against the real thing it stands in for**, band by
band, region by region, frame by frame. An eyeball pass approves all of these.

## Keys

Read from the environment only. No script here opens a key file, and none writes a key anywhere.

| Var | Used by | Notes |
|---|---|---|
| `ELEVENLABS_API_KEY` | `voice.py clone/takes/sweep` | |
| `ELEVENLABS_CLONE_API_KEY` | `voice.py clone` | Optional. Cloning needs the `create_instant_voice_clone` permission; a shared engine key generally lacks it and fails 401 at `/v1/voices/add`, not at TTS. Falls back to `ELEVENLABS_API_KEY`. |
| `FAL_KEY` | `plate.py`, all providers | |
| none | `drift.py`, `music.py` | Free, offline apart from a Mixkit GET. |

`.env.example` lists them with no values. **`.gitignore` at the repo root does not currently
cover `.env` files** (checked with `git check-ignore`); that is the lead's file to fix, not this
directory's.

Every subcommand takes `--dry-run`, which prints the exact URL and request body and sends nothing.
Use it before spending a generation, because these calls cost money and minutes.

---

## `voice.py`, clone and take pipeline

```bash
voice.py clone  --sample raw-reference.mp3 --name "Creator X" --i-did-not-denoise -o voice.json
voice.py takes  --config takes.json --outdir audio --json-out takes.json.out
voice.py sweep  --voice-id RAW,DENOISED --text-file line.txt --models eleven_v3,eleven_multilingual_v2
voice.py eqfit  --source her-real-recording.wav --generated audio/cand-v3-tagged-035.mp3 -o eq-chain.txt
voice.py master --in audio/cand-v3-tagged-035.mp3 --out audio/vo-s1.mp3 \
                --eq eq-chain.txt --words 21 --target-rate 3.62
```

**Cost and latency**, measured on the Demi UGC build in 2026: a 12 to 20 second line on
`eleven_v3` returns in 8 to 20s and bills roughly one credit per character, so a four-candidate
sweep of one line is about 4x the line length in credits and under two minutes of wall time. The
clone itself is free on a paid plan.

Four rules are enforced in code, not left to memory:

- **Never pre-process a clone reference.** `clone` refuses without `--i-did-not-denoise`. Denoising
  a 20.8s reference with `afftdn` before upload cost **19% of its consonant energy**; re-cloning
  from the untouched file on identical settings **doubled** it. The cleanup chain in
  `docs/05-audio-and-sfx.md` is for a take that ships. A clone reference is training data, and
  every artefact you remove is detail the model then cannot reproduce. `clone` prints and records
  the sample's 2 to 5 kHz share so a later re-clone can be compared against it.
- **`eleven_v3` when there are audio tags at all.** It is the default model. `eleven_multilingual_v2`
  **speaks the tags aloud**: whisper caught it reading a `<break time="0.45s"/>` as "you're a king".
  The v3 fallback path on a 400 or 422 prints that the tags will now be spoken, rather than
  returning a clean-looking 200 full of nonsense.
- **Transcript-verify before scoring anything else.** Every candidate goes through whisper first
  and prints `OK` or `MANGLED`. Only transcript-clean candidates are ranked, and if none survives
  the tool says so and ranks nothing. A candidate that loses on timbre but says the right words is
  fixable; one that says the wrong words is not, and sorting by quality first means auditioning
  nonsense. `--no-asr` exists and its help text says what you are choosing.
- **Fit the EQ by iteration against the source's own band profile.** `eqfit` measures eight narrow
  bands on both files, prints the per-band deviation each round, and cuts the excess. Not one wide
  "consonant" band: that looked solved while the TTS was piling energy either side of her voice
  (her 400 to 700 Hz carried **50% of total energy** against the model's 33%, with +6.5% at
  250 to 400, +8% at 700 to 1200, +6.3% at 1200 to 2000). Seven rounds took total deviation from
  **44.9 to 7.2** and the decisive move was **−7.7 dB at 900 Hz**, which nobody picks by ear.
  Cuts only by default: a +2 dB shelf at 190 Hz, added to lift the 400 to 700 Hz share toward hers,
  spilled upward and *caused* the mud. `--allow-boost` exists; read the docstring first.
  Know the cost before running it: reshaping the envelope dropped the lip-sync correlation metric
  from **0.310 to 0.243**.

`master` nudges toward the creator's measured rate with pitch-preserving `atempo`, and only ever
speeds up, clipped at 0.88. Slowing a TTS read down to hit a rate target sounds drugged, and the
reason a take is slow is almost always that v3 dramatised a short full-stop sentence, which is a
text fix (join the sentences with commas), not a tempo fix.

`takes.example.json` is the worked config. `target_rate` and `source_consonant` are measurements of
the real person, 3.62 words/sec of speech and a 4.80% share in 2 to 5 kHz on the build this came
from, not defaults: without them the scorer has nothing to be right about.

---

## `plate.py`, image to video and talking avatars

```bash
plate.py avatar    plate.jpg vo.mp3 out/shot01.mp4 --fit 1080x1920
plate.py avatar4   plate.jpg vo.mp3 out/shot01.mp4 --style expressive
plate.py omnihuman plate.jpg vo.mp3 out/shot01.mp4
plate.py lipsync   approved.mp4 vo-v2.mp3 out/shot01-v2.mp4
plate.py i2v       still.jpg out/pickup.mp4 --model seedance --last-image approved-frame0.jpg \
                   --negative-prompt "seated, sitting down, arms crossed"
```

`fal_client` is imported lazily, so `--help` and `--dry-run` work on a machine that has never
installed it.

**Cost and latency** at FAL list price, recorded on the same build: Kling `ai-avatar/v2/pro` about
**$1.40 for a 10s clip, 4 to 9 minutes in queue**; HeyGen Avatar IV similar money, **3 to 6
minutes**. Budget one failed take per beat.

**A deadpan plate produces a deadpan clip, whatever the model.** The instinct when a generated
performance is flat is to change the video model. The input still was the problem. Regenerating the
plate as mid-sentence and engaged, brows lifted, mouth open mid-word, eyes live, lifted brow motion
**+17%** and lip-sync **+8%** on the same model with the same audio.

**But asking an image model for a new expression makes it silently redress the room: two of three
variants did.** Diff the background against the approved plate, not just the face:
`drift.py new-plate-clip.mp4 --ref-image approved-plate.jpg --grid 4x6`.

The model choice, measured on the same plate and audio:

| Model | What it does |
|---|---|
| HeyGen Avatar IV, `expressive` | **The least expressive option available**, despite the name |
| OmniHuman v1.5 | Wins lip-sync on a neutral plate, then **drifts the background in the last third** |
| Kling `ai-avatar/v2/pro` | **Holds the room locked** |

Pick for the failure you cannot fix in post. Background drift is unfixable; a slightly softer
lip-sync is not visible at reel scale. OmniHuman has been renamed under FAL more than once, so
`omnihuman` tries three endpoint names in order rather than losing a session to a 404.

**`i2v` refuses to run without a `--negative-prompt`.** Kling's reference image drags the reference
*pose* along with the likeness, and the fix is both halves together: the target pose in the prompt
**and** the reference pose named in the negative prompt. A held pose then drifts mid-clip in the
opposite direction: on vid15 her arms uncrossed and a hand melted into her sweater **within 1
second**. `--no-negative` overrides deliberately.

**Pick the i2v model for keyframe control, not the house habit.** Kling 2.6 i2v has no last-image
control; `seedance` does, and `--last-image` is rejected on the model that cannot honour it. That
control is what makes the backwards extension possible: generate a take that *ends* on an approved
take's first frame, and because the approved take was i2v'd from that same still, its frame 0 **is**
the still, so the two clips join with no cut at all (measured average colour across the join
`86766b` against `877569`, one to two levels per channel). Its cost: `--last-image` set to the input
still also forces the framing to return, which kills a push-in.

**Re-master onto the approved clip rather than regenerating.** If only the audio master changed and
not the words, do not even lip-sync: mux with `-c:v copy` and re-seat by cross-correlating against
the old track (+10 ms on the case that produced this rule). That saves a full generation per audio
revision and keeps a picture the client has already approved.

---

## `drift.py`, the measurement that decides whether a clip is usable

```bash
drift.py clip.mp4 --region face:300,240,520,620 --region hand-l:120,1180,340,360
drift.py clip.mp4 --grid 4x6                       # fallback, prints a warning
drift.py clip.mp4 --ref-image approved-plate.jpg --grid 4x6   # background redress check
```

No key, no cost. Run it on every generated clip before it enters a cut. Exit 1 when the worst
region breaches `--fail`.

**Measure drift on a crop around every face and every hand, never globally.** Global `mean|Δ|`
against frame 0 looked acceptable while a hand was morphing into a second face at her hairline;
cropping to the head region exposed it climbing **12 to 24**, which is where the default
`--fail 12` comes from. A global average over a mostly static plate cannot see a local catastrophe,
and the local catastrophe is the only thing a viewer will look at. The report prints the global
number last, labelled as the one that lies.

It samples **0.1s, mid and end** explicitly, because a held pose drifts mid-clip and a last-frame
check passes it. `--grid` is a fallback that finds *a* local catastrophe without knowing where the
face is; it warns, because a face straddling four tiles dilutes into all four.

When a take is clean early and rots late, the report ends with a **clean window**. Trim there and
mirror it back, forward plus a reversed tail, rather than regenerating a take whose first half is
good.

---

## `music.py`, licensed music

```bash
music.py search --tag technology
music.py fetch https://assets.mixkit.co/music/<id>/<id>.mp3 -o bed-src.mp3
music.py transients bed-src.mp3
music.py treat bed-src.mp3 assets/music/bed.mp3 --src-bpm 129 --target-bpm 120 --length 41.5
```

**AI-generated music gets rejected outright, so a real licensed track is the default.** An
ElevenLabs bed was generated, tempo-matched and sidechain-ducked carefully to the cut's beat grid,
and came back as **"too shitty music bro, eww"**, followed by "can't you find one pre-existing
non-copyright music". The production effort counted for nothing, because the objection was to the
category. There is no version of the AI bed that wins that argument, and this directory ships no
tool to generate one.

Mixkit works and is scriptable: tag pages such as `mixkit.co/free-stock-music/tag/technology/`
embed the asset URLs, track pages 301-redirect to `mixkit.co/free-stock-music/discover/<slug>/`,
and the direct mp3 sits at `https://assets.mixkit.co/music/<id>/<id>.mp3`, no auth, browser user
agent only. Licence: Stock Music Free License, commercial use including paid ads, no attribution
required. **Pixabay does not script**: 403 to automated fetching even on public search URLs, SFX
downloads login-walled (a full hover-and-click crawl returned 0 files), stock pages JS-locked to
`curl`.

**Audition for ticks before choosing.** The track that replaced the AI bed on one film was itself
swapped later because it carried a metronomic **0.465s** percussion tick on a 129 BPM grid that
three rounds of SFX purges got blamed for. `transients` counts RMS-flux onsets and then tests the
inter-onset gaps for periodicity, which is the actual disqualifier: the winner measured **30
transients against 75** for the one it replaced, verified at **4 non-VO transients, none periodic**.
It exits 1 on a periodic result.

`treat` stretches to the **edit's** grid, not a genre default, so every scene change lands within a
quarter beat, then high-passes at 45 Hz, loudnorms to **I=−20** and fades. A bed at the VO's own
I=−16 is the "music too loud" note before anyone plays it. `atempo` is chained automatically
outside its 0.5 to 2.0 range, which otherwise errors out after the download. A client's own
supplied clip keeps its own audio at unity with the music fading underneath, and probe that clip
first: one client outro's track was digital silence at **−240 dBFS**.

---

## The gate these tools sit behind

**Approve the still, then the clip, then render.** On every reference-driven build, the frame gets
signed off before a second of video is generated, because a plate is one cheap image and a clip is
$1.40 and nine minutes, and the note that comes back on the clip is nearly always a note about the
plate. Nothing here goes into a full composition render until both halves of that gate have passed
and `drift.py` has returned PASS on named face and hand crops.

The order, end to end:

1. Clone from untouched reference audio. Never denoise it first.
2. `eleven_v3` if there are audio tags at all, transcript-verify every candidate before scoring it.
3. Fit EQ by measured band deviation against the real voice, cutting excess rather than boosting deficit.
4. Build the plate mid-sentence and engaged, then diff its background against the approved one.
5. Approve the still.
6. Generate the clip. Measure drift on a crop around every face and every hand, at 0.1s, mid and end.
7. Approve the clip.
8. Licensed music, transient-counted before it is chosen.
9. Re-master onto the approved clip with `-c:v copy` rather than regenerating it.
