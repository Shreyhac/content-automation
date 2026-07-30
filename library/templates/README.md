# Templates

`vertical-reel/` is a 1080x1920 skeleton that encodes the house rules structurally: the safe-zone
guides, the one global ground stack, the `gsap.set` initial-state pattern, the 0.20s scene lead,
the caption markers, and the non-collapsible clip-path form.

**For real work, prefer scaffolding from `reference-builds/`.** Those carry the proven systems
(the accordion, the face-card move, the chunk architecture, the caption engine, the recurring 3D
object). The template only carries the skeleton, and `CLAUDE.md` is explicit that you should never
start from a blank composition.

Use the template when the build genuinely does not fit any existing reference, or when you want to
read the house rules in one short file.

```bash
cp -R library/templates/vertical-reel work/vid48
cd work/vid48
cp ../../library/fonts/<the faces this build needs>.woff2 assets/fonts/
npm run check
```
