#!/usr/bin/env python3
"""Emit hf67/index.html from shots.json + captions.js.

Generated rather than hand-written so the composition cannot drift from the shot
table: change a boundary in build_shots.py, re-run both, and the HTML follows.
(vid62 shipped a round-1 caption set into a round-2 cut because a derived file
was hand-patched instead of regenerated.)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOTS = json.load(open(os.path.join(HERE, "shots.json")))
CAPS  = open(os.path.join(HERE, "captions.js")).read().strip()
NCAP  = CAPS.count("],")
DUR   = 35.233333
FPS   = 30

# ── geometry, solved from HIS landmarks (vid67/facebox.csv, 176 samples) ────
BAND   = 620     # B-roll band height
SHIFT  = 380     # how far the picture drops in SPLIT
CROWN  = 280     # worst-case (highest) crown in the source
CHIN   = 1166    # worst-case (lowest) chin in the source
CAP_S  = 548     # caption top on SPLIT
CAP_F  = 1246    # caption top on FULL
assert CROWN + SHIFT > BAND, "crown would be cut off by the seam"
assert CHIN + SHIFT < 1600, "chin would land in Instagram's bottom band"

# ONE pre-composed band track (vid67/build_band.py), not one <video> per shot.
# 18 video elements stalled the capture engine at frame 746/1057; this page
# holds 2. See build_band.py for the whole reasoning.
vids = ['      <video id="vband" src="assets/bandtrack.mp4"\n'
        f'             data-start="0" data-duration="{DUR:.6f}" data-track-index="1"\n'
        '             muted playsinline></video>']
cuts = []
for r in SHOTS:
    state = "full" if r["kind"] == "full" else "split"
    cuts.append(f'cut("{state}", {r["his"][0]:6.3f});   // {r["note"]}')

# ── SFX: one soft mark per cut, louder only on the three structural beats ──
sfx, k = [], 0
FIRST_FULL = [r["his"][0] for r in SHOTS if r["kind"] == "full"]
for r in SHOTS:
    t = r["his"][0]
    if t <= 0.001:
        f, v, d = "riser.mp3", 0.16, 0.60
    elif t in FIRST_FULL:
        f, v, d = "wsh2.mp3", 0.13, 0.35
    elif r["kind"] == "mock":
        f, v, d = "wsh.mp3", 0.12, 0.32
    else:
        f, v, d = ("click.mp3" if k % 2 else "click2.mp3"), 0.11, 0.20
    sfx.append(f'  <audio id="sx{k:02d}" src="assets/sfx/{f}" data-start="{t:.3f}" '
               f'data-duration="{d:.2f}" data-track-index="{40+k}" data-volume="{v}"></audio>')
    k += 1
sfx.append(f'  <audio id="sx{k:02d}" src="assets/sfx/shine2.mp3" data-start="32.900" '
           f'data-duration="0.90" data-track-index="{40+k}" data-volume="0.15"></audio>')

HTML = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>vid67 — launch-your-agent, the reference cut shot for shot</title>
<style>
@font-face{{font-family:'Inter';src:url('assets/fonts/inter-800.woff2')format('woff2');font-weight:800;font-display:block}}
@font-face{{font-family:'Inter';src:url('assets/fonts/inter-600.woff2')format('woff2');font-weight:600;font-display:block}}
@font-face{{font-family:'Fraunces';src:url('assets/fonts/fraunces-italic.woff2')format('woff2');font-style:italic;font-weight:900;font-display:block}}

/* ═══════════════════════════════════════════════════════════════════════════
   vid67 · Dr Alvaro Cintas' `DbqcQUgxlyC` rebuilt shot for shot on his A-roll

   HIS INSTRUCTION  "can you do the exact same editing for me? You can use the
   exact same visuals from the creator's video as well."

   So there are no invented graphics here. This is the reference's shot list,
   its cut rhythm, its two-layout grammar and its word-sticker captions, re-timed
   onto the creator's 35.233s delivery. The creator recorded the reference's script
   verbatim, so the two timelines are aligned WORD BY WORD (136 of 148 words
   anchored by difflib) rather than scaled — every cut lands on the same spoken
   word it lands on in the reference.

   ── WHAT IS LIFTED, AND WHAT COULD NOT BE ────────────────────────────────
   11 shots are the reference's own footage, cropped to this band.
   6 are rebuilt, each because the reference's frame is unusable:
     the Claude app is titled "Dr Cintas" throughout · the .env shows a live
     ANTHROPIC_API_KEY · the run FAILS on screen ("insufficient credit balance")
     under a VO saying it deployed · the spec page reads PLANNED . NOT LAUNCHED ·
     the meeting notes belong to a third party · the inbox is a real person's.
   3 are his face full-bleed, exactly where the reference plays its own.

   ── THE CROPS ────────────────────────────────────────────────────────────
   The reference burns its captions into the picture at y924-975 (measured), so
   no lift may extend past y920. Each is a 1080x620 window with a per-shot y
   offset chosen so that shot's payload survives, then 2x lanczos to 2160x1240.
   The reference is 1080x1920, so lifted footage carries half this composition's
   detail; the 6 rebuilds are the only shots at true resolution.

   ── THE GEOMETRY IS HIS, NOT THE REFERENCE'S ─────────────────────────────
   Measured over all 176 samples of the take (vid67/facebox.csv, Vision):
     crown y{CROWN}-375 · chin y1003-{CHIN} · head {CHIN-CROWN}px worst case
   The reference seams at y955 because Cintas sits further from his lens. Here
   that would bury the chin. Solved instead:
     seam y{BAND} · picture pushed down {SHIFT} · worst crown y{CROWN+SHIFT} ({CROWN+SHIFT-BAND}px below the
     seam) · worst chin y{CHIN+SHIFT} ({1600-CHIN-SHIFT}px above Instagram's bottom band)

   LAYOUTS   SPLIT  B-roll y0-{BAND} full width · his face below, scale 1, +{SHIFT}y
             FULL   his face full-bleed, untouched
   CAPTIONS  1-4 words on a dark pill, {NCAP} of them, every change on a word
             onset. On SPLIT the pill sits in the band's lower edge, which is
             where the reference puts its own; on FULL it drops below his chin.
   TRANSITIONS  hard cuts. The reference has none and neither does this. No CSS
             transform ever animates on a box containing a <video> — that is
             what deadlocked the capture engine on vid66b.
   ═══════════════════════════════════════════════════════════════════════ */

*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:2160px;height:3840px;background:#000;overflow:hidden}}
#stage{{position:absolute;left:0;top:0;width:1080px;height:1920px;
  transform:scale(2);transform-origin:0 0;overflow:hidden;background:#000;}}

#faceScene{{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:3;
  clip-path:inset(0px 0px 0px 0px);}}
#faceCam{{position:absolute;left:0;top:0;width:1080px;height:1920px;
  transform-origin:0 0;transform:translate(0px,0px) scale(1);}}
#faceCam video{{position:absolute;left:0;top:0;width:1080px;height:1920px;
  object-fit:cover;display:block;}}

/* the B-roll band: ONE track, always playing, revealed only on SPLIT beats.
   Seventeen separate <video> elements stalled the capture engine; one cannot,
   and with a single always-on element there is no data-start window for a clip
   to fall outside of. */
#btop{{position:absolute;left:0;top:0;width:1080px;height:{BAND}px;z-index:5;
  overflow:hidden;background:#0A0A0C;}}
#btop video{{position:absolute;left:0;top:0;width:1080px;height:{BAND}px;
  object-fit:cover;display:block;}}
#seam{{position:absolute;left:0;top:{BAND-2}px;width:1080px;height:4px;z-index:6;
  background:rgba(0,0,0,.55);}}

#capW{{position:absolute;left:0;top:{CAP_S}px;width:1080px;text-align:center;z-index:8;}}
#capW.full{{top:{CAP_F}px;}}
/* inline-block so the BOX is the ink — a full-width centred container measures
   1080px wide and trips every edge gate falsely (vid66b) */
#cap{{display:inline-block;font-family:'Inter';font-weight:800;font-size:44px;
  letter-spacing:-.018em;line-height:1.14;color:#FFFFFF;
  background:rgba(10,10,12,.70);border-radius:12px;padding:9px 20px 12px;
  text-shadow:0 2px 10px rgba(0,0,0,.5);white-space:nowrap;}}

/* the CTA the reference stamps under its own last shot, rebuilt: its version
   carries Cintas's profile photo in the pill */
#cta{{position:absolute;left:0;top:1392px;width:1080px;text-align:center;z-index:8;
  opacity:0;visibility:hidden;}}
#ctaP{{display:inline-flex;align-items:center;gap:18px;
  background:rgba(18,18,20,.86);border:2px solid rgba(255,255,255,.16);
  border-radius:999px;padding:16px 30px 18px;}}
#ctaT{{font-family:'Inter';font-weight:800;font-size:52px;color:#fff;letter-spacing:-.01em}}
#ctaA{{width:54px;height:54px;border-radius:50%;background:#D97757;
  display:inline-flex;align-items:center;justify-content:center;
  font-family:'Inter';font-weight:800;font-size:34px;color:#fff}}

#flash{{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:9;
  background:#FFFFFF;opacity:0;pointer-events:none;}}
</style>
</head>
<body>
<div id="root" data-composition-id="vid67" data-start="0"
     data-duration="{DUR:.6f}" data-fps="{FPS}" data-width="2160" data-height="3840">
  <div id="stage">

    <div id="faceScene" data-layout-ignore>
      <div id="faceCam">
        <video id="aroll" src="assets/aroll.mp4" data-start="0" data-duration="{DUR:.6f}"
               data-track-index="0" muted playsinline></video>
      </div>
    </div>

    <div id="btop" data-layout-ignore>
{chr(10).join(vids)}
    </div>
    <div id="seam" data-layout-ignore></div>

    <div id="capW"><div id="cap"></div></div>
    <div id="cta"><div id="ctaP"><span id="ctaT">Comment AGENT</span><span id="ctaA">↑</span></div></div>

    <div id="flash" data-layout-ignore></div>
  </div>

  <audio id="vo" src="assets/vo.mp4" data-start="0" data-duration="{DUR:.6f}"
         data-track-index="30" data-volume="1"></audio>
{chr(10).join(sfx)}
</div>

<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
var tl = gsap.timeline({{ paused: true, defaults: {{ immediateRender: false }} }});
window.__timelines = {{ vid67: tl }};
var HALF = 0.5 / {FPS};

function put(sel, vars, t){{ if (t <= HALF) gsap.set(sel, vars); tl.set(sel, vars, t); }}

/* ── THE FACE. Two states, hard cuts, never a tween. ─────────────────────── */
var FACE = {{
  full:  {{ clip:"inset(0px 0px 0px 0px)",   cam:{{ x:0, y:0,     scale:1 }} }},
  split: {{ clip:"inset({BAND}px 0px 0px 0px)", cam:{{ x:0, y:{SHIFT}, scale:1 }} }}
}};
function cut(state, t){{
  var f = FACE[state];
  put("#faceScene", {{ clipPath: f.clip }}, t);
  put("#faceCam", Object.assign({{ transformOrigin:"0 0" }}, f.cam), t);
  put("#btop", {{ autoAlpha: state === "split" ? 1 : 0 }}, t);
  put("#seam", {{ autoAlpha: state === "split" ? 1 : 0 }}, t);
  put("#capW", {{ className: state === "split" ? "" : "full" }}, t);
}}

{chr(10).join(cuts)}

/* ── CAPTIONS ───────────────────────────────────────────────────────────── */
{CAPS}
window.__CAPS = CAPS;   // gates seek with suppressEvents, so tl.call() never
                        // fires for them; they set the text from this instead
(function(){{
  var el = document.getElementById("cap");
  for (var i = 0; i < CAPS.length; i++){{
    (function(c){{
      tl.call(function(){{ el.textContent = c[1]; }}, null, c[0]);
      tl.fromTo("#cap", {{ scale:0.94 }}, {{ scale:1, duration:0.10, ease:"power2.out",
        transformOrigin:"50% 50%" }}, c[0]);
    }})(CAPS[i]);
  }}
  tl.to("#cap", {{ opacity:0, duration:0.24, ease:"power2.in" }}, {DUR:.3f} - 0.30);
}})();

/* the CTA arrives on the word "comment" and holds to the end */
put("#cta", {{ autoAlpha:0 }}, 0);
tl.set("#cta", {{ autoAlpha:1 }}, 32.900);
tl.fromTo("#cta", {{ scale:0.90, y:16 }}, {{ scale:1, y:0, duration:0.28,
  ease:"back.out(2.0)", transformOrigin:"50% 50%" }}, 32.900);

/* one white frame on the two hardest cuts — the only effect in the file */
[{SHOTS[1]["his"][0]:.3f}, {[r for r in SHOTS if r["kind"]=="full"][1]["his"][0]:.3f}].forEach(function(t){{
  tl.fromTo("#flash", {{ opacity:0 }}, {{ opacity:0.40, duration:0.05, ease:"none" }}, t - 0.05);
  tl.to("#flash", {{ opacity:0, duration:0.06, ease:"none" }}, t);
}});
</script>
</body>
</html>
'''

open(os.path.join(ROOT, "hf67", "index.html"), "w").write(HTML)
print(f"hf67/index.html  (1 band track, {len(SHOTS)} shots, {len(sfx)} sfx cues, 2 videos on the page)")
print(f"  SPLIT: seam y{BAND}, shift +{SHIFT} -> crown y{CROWN+SHIFT} "
      f"({CROWN+SHIFT-BAND}px below seam), chin y{CHIN+SHIFT} ({1600-CHIN-SHIFT}px above band)")
