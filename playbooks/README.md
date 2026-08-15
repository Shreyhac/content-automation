# Playbooks

One file per reusable technique. Each carries the measured numbers and the failure that produced
the rule, because a rule without its failure gets argued away.

Read the two or three the job actually needs, not all of them.

| Playbook | Read it when |
|---|---|
| `face-geometry.md` | Any build with a face in it. Measuring the head and solving a crop, band or card. |
| `face-card-device.md` | The owner asks for "the split screen" or names a prior video's face treatment. |
| `paper-split-band.md` | Building for paper-split, or any 9:16 where the face must stay on screen continuously. |
| `gaze-detection.md` | longform-chunked, or any creator who reads from notes. |
| `scripting-and-research.md` | Before a topic is agreed or a script is written. Read it before scoping anything. |
| `short-from-longform.md` | "Make a short of this" from a finished film. |
| `longform-chunking.md` | Anything over about 60 seconds, built chunked from the start. |
| `chunk-revision.md` | Changing a film that has already shipped, or a one-file composition that will not render. |
| `threejs.md` | Any 3D. Read before writing a line of WebGL. |
| `transitions-and-cuts.md` | Always. The 0.20s lead rule affects every scene boundary. |
| `captions.md` | Any build with a caption track or an SRT. |
| `real-assets.md` | Any claim about a real product, repo, page or person. Also screen recordings and in-app mocks. |
| `generative-assets.md` | Any cloned voice, AI plate, i2v clip or music bed. |
| `stock-footage.md` | Sourcing or placing b-roll. |
| `gates.md` | Every render round, before you render. When to add a gate, why the built-in ones lie, and the running order. |
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
   wrong-position elements, mid-tween states, dead pages and empty cards. And a gate that
   reports PASS is not the same as a gate that ran: check its coverage, not just its verdict.
4. **Compose on every cut, not just frame 0.**
5. **When two passes at a decorative element fail, cut it.**
