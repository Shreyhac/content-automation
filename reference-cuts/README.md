# Reference cuts

**This is the quality bar, watchable.** 720p proxies of shipped, owner-approved finals. Watch the
relevant one before starting a video for that template.

The delivered originals stay in the working repo's `out/`. These are re-encoded down (CRF 30) so
the repo stays clonable: **47MB for all fifteen**. The three newest originals alone are 786MB
(vid67 168.6MB, vid62-short 214.3MB, the fast-cut-ad demo film 402.8MB), and the full set runs to gigabytes.

| File | Template | What it demonstrates |
|---|---|---|
| `card-reel-vid67-launch-your-agent.mp4` | card-reel | **Current grammar.** A reference reel copied shot for shot on the creator's own take, re-timed word by word rather than by ratio. Two layouts, hard cuts only, 70 word-sticker captions, and one white frame as the entire effects budget. |
| `card-reel-vid63-strix.mp4` | card-reel | The first film with **zero full-bleed face**: split-screen and card only, opening on 1.84s of graphics. Skinned in Strix's own terminal rather than in the house palette. |
| `card-reel-vid42-elevenlabs.mp4` | card-reel | The floating card, three.js as a recurring object, stock as a ground layer. Superseded by vid67 as the current reference. |
| `card-reel-vid38-truth-prompt.mp4` | card-reel | Machine-event scene grammar: the ampoule, the gates, the dial. The answer to "text based and boring". |
| `longform-chunked-vid62-incogni-short.mp4` | longform-chunked | **Current longform-chunked vertical.** Nine beats cut from a long-form with no new recording. Band and card off one camera, differing only by clip-path, and the card collapsing inside its own edges. |
| `longform-chunked-vid46-incogni-short.mp4` | longform-chunked | An earlier short derived from a film. One face placement, complete sentences, the card as a move. |
| `longform-chunked-vid62-incogni-longform.mp4` | longform-chunked | **Current longform-chunked long-form.** 6m13s, 3840x2160, the chunked architecture at full scale. Eleven client notes, all answered. |
| `longform-chunked-vid46-incogni-longform.mp4` | longform-chunked | Sponsored comparison. The recurring three.js field, the six-layer 4K ground, the rationed serif. |
| `longform-chunked-vid44-trustmark-longform.mp4` | longform-chunked | First 16:9 long-form. Chunked, gaze-gated, the docking window. |
| `longform-chunked-vid39-orm-short.mp4` | longform-chunked | The floating face card, the ORM story, five stock cuts placed one per act. **The file the client names when they want this grammar.** |
| `fast-cut-ad-demo-six-tools.mp4` | fast-cut-ad | **Current fast-cut-ad grammar.** The client's own organic language: hub-and-spoke dotted connectors, blobs, white washes melting into footage, long soft holds, no flash cuts. Voice plus music, zero SFX. |
| `paper-split-vid50-current.mp4` | paper-split | **Current paper-split grammar.** The paper split as it settled. Three review rounds all spent on the hook, which turned out to be in the footage already: the laptop lid shuts by frame 22 and the title lands on the shut. |
| `paper-split-vid47-github-tools.mp4` | paper-split | The paper split band, one accordion for ten items, 91% face presence. Superseded by vid50. |
| `paper-split-vid35-elevenlabs.mp4` | paper-split | The rebuilt X-post cards and the browser-window trust device. |
| `paper-split-vid43-musk-uturn.mp4` | paper-split | The three-band layout: graphics top, ungraded A-roll middle, captions bottom. |

vid35 and vid42 are the same product launch cut for two different creators from one asset pool.
Watching them back to back is the clearest illustration in this repo of what "per-template system"
means: same facts, unmistakably different reels.

vid42 and vid67 are the same creator two months apart, and the direction of travel is visible:
fewer invented graphics, no full-bleed opening, geometry re-derived per take rather than ported.

---

## Regenerating

```bash
ffmpeg -i <original>.mp4 -vf scale=720:-2 -c:v libx264 -crf 30 -preset veryfast \
       -c:a aac -b:a 96k -movflags +faststart <name>.mp4
```

Use `scale=1280:-2` for the 16:9 long-forms.
