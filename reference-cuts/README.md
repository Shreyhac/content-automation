# Reference cuts

**This is the quality bar, watchable.** 720p proxies of shipped, owner-approved finals. Watch the
relevant one before starting a video for that creator.

The delivered originals stay in the working repo's `out/`. These are re-encoded down (CRF 30) so
the repo stays clonable: 29MB for all nine instead of about 1.8GB.

| File | Creator | What it demonstrates |
|---|---|---|
| `nader-vid39-orm-short.mp4` | Nader | The floating face card, the ORM story, five stock cuts placed one per act. **The file he now names when he wants this grammar.** |
| `nader-vid44-trustmark-longform.mp4` | Nader | First 16:9 long-form. Chunked, gaze-gated, the docking window. |
| `nader-vid46-incogni-longform.mp4` | Nader | Sponsored comparison. The recurring three.js field, the six-layer 4K ground, the rationed serif. |
| `nader-vid46-incogni-short.mp4` | Nader | A short derived from that film. One face placement, complete sentences, the card as a move. |
| `gaurav-vid47-github-tools.mp4` | gaurav | **Current grammar.** The paper split band, one accordion for ten items, 91% face presence. |
| `gaurav-vid35-elevenlabs.mp4` | gaurav | The rebuilt X-post cards and the browser-window trust device. |
| `gaurav-vid43-musk-uturn.mp4` | gaurav | The three-band layout: graphics top, ungraded A-roll middle, captions bottom. |
| `shreyansh-vid42-elevenlabs.mp4` | shreyansh | **Current grammar.** The floating card, three.js as a recurring object, stock as a ground layer. |
| `shreyansh-vid38-truth-prompt.mp4` | shreyansh | Machine-event scene grammar: the ampoule, the gates, the dial. The answer to "text based and boring". |

vid35 and vid42 are the same product launch cut for two different creators from one asset pool.
Watching them back to back is the clearest illustration in this repo of what "per-creator system"
means: same facts, unmistakably different reels.

---

## Regenerating

```bash
ffmpeg -i <original>.mp4 -vf scale=720:-2 -c:v libx264 -crf 30 -preset veryfast \
       -c:a aac -b:a 96k -movflags +faststart <name>.mp4
```

Use `scale=1280:-2` for the 16:9 long-forms.
