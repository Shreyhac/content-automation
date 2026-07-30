# Playbooks

One file per reusable technique. Each carries the measured numbers and the failure that produced
the rule, because a rule without its failure gets argued away.

Read the two or three the job actually needs, not all of them.

| Playbook | Read it when |
|---|---|
| `face-geometry.md` | Any build with a face in it. Measuring the head and solving a crop, band or card. |
| `face-card-device.md` | The owner asks for "the split screen" or names a prior video's face treatment. |
| `paper-split-band.md` | Building for gaurav, or any 9:16 where the face must stay on screen continuously. |
| `gaze-detection.md` | Nader, or any creator who reads from notes. |
| `short-from-longform.md` | "Make a short of this" from a finished film. |
| `longform-chunking.md` | Anything over about 60 seconds. |
| `threejs.md` | Any 3D. Read before writing a line of WebGL. |
| `transitions-and-cuts.md` | Always. The 0.20s lead rule affects every scene boundary. |
| `captions.md` | Any build with a caption track or an SRT. |
| `real-assets.md` | Any claim about a real product, repo, page or person. |
| `stock-footage.md` | Sourcing or placing b-roll. |
| `frame-qa.md` | Every render round. This is the gate that works. |
| `gsap-traps.md` | Before writing tweens. A list of bugs that each cost a render round. |

---

## The five rules that cut across all of them

1. **Measure, never estimate.** Every "it looked about right" in this system's history became a
   render round. Face geometry, crop rectangles, marker offsets, card widths, 3D scale and mono
   text widths are all arithmetic.
2. **The formula travels, the constants never do.** Porting a device between takes or creators
   means re-solving its numbers. This has been true every single time it was tested.
3. **Only frame QA catches the bugs that matter.** Lint, validate and inspect pass occlusion,
   wrong-position elements, mid-tween states, dead pages and empty cards.
4. **Compose on every cut, not just frame 0.**
5. **When two passes at a decorative element fail, cut it.**
