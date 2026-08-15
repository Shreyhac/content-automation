#!/usr/bin/env python3
"""Split the film into renderable chunks, media and timeline together.

WHY. Two full-length renders stalled at frame 746 and 743 of 1057 — the same
place, once with 18 <video> elements on the page and once with 2. Video count
was not the cause; the capture process reaches a ceiling after roughly 740
frames on this 8 GB machine (already pinned to 1 worker in low-memory mode) and
stops making progress. Shorter passes stay under it.

BOUNDARIES LAND ON REAL CUTS (frames 346 and 689), so no shot straddles a join
and each join is a hard cut that already existed in the edit.

THE FOUR RULES THAT MAKE A REBASED TIMELINE CORRECT (from the fast-cut-ad demo film):
  1. HyperFrames CEILS duration*fps, so emit (nframes - 0.001)/fps. Rounding is
     not safe: 126/30 is 4.200000000000001 in binary float, which ceils to 127.
  2. Never hand GSAP a negative rebased position — it does not clamp, it SHIFTS
     THE WHOLE TIMELINE. Events before the chunk start are applied statically at
     load instead, which is also semantically right: they are `set` calls, so
     their effect is just the element's state on entry.
  3. Events past the chunk end are harmless to keep but are dropped here to keep
     the emitted file readable.
  4. Media is trimmed per chunk so every <video>/<audio> starts at 0.

Usage:  python3 vid67/build_chunks.py          # emit html + media
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HF   = os.path.join(ROOT, "hf67")
AS   = os.path.join(HF, "assets")
CH   = os.path.join(AS, "chunks")
FPS  = 30
TOTAL = 1057
BOUNDS = [0, 346, 689, TOTAL]

SHOTS = json.load(open(os.path.join(HERE, "shots.json")))
CAPSRC = open(os.path.join(HERE, "captions.js")).read()
import re as _re
CAPS = [[float(m.group(1)), json.loads(m.group(2))]
        for m in _re.finditer(r"\[\s*([\d.]+),\s*(\".*?\")\s*\]", CAPSRC)]

BAND, SHIFT, CROWN, CHIN = 620, 380, 280, 1166
CAP_S, CAP_F = 548, 1246
FULL_T = [r["his"][0] for r in SHOTS if r["kind"] == "full"]
FLASH  = [SHOTS[1]["his"][0], FULL_T[1]]

os.makedirs(CH, exist_ok=True)


def trim(src, dst, f0, n, kind):
    ss, t = f0 / FPS, n / FPS
    if kind == "v":
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.6f}", "-i", src,
               "-frames:v", str(n), "-an", "-vf", f"fps={FPS}",
               "-c:v", "libx264", "-crf", "13", "-preset", "slow",
               "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", "15",
               "-keyint_min", "15", dst]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.6f}", "-i", src,
               "-t", f"{t:.6f}", "-vn", "-c:a", "aac", "-b:a", "192k", dst]
    subprocess.run(cmd, check=True)
    return dst


def emit(ci, f0, f1):
    n = f1 - f0
    T0 = f0 / FPS
    dur = (n - 0.001) / FPS          # rule 1

    a = trim(os.path.join(AS, "aroll.mp4"),     os.path.join(CH, f"c{ci}_aroll.mp4"), f0, n, "v")
    b = trim(os.path.join(AS, "bandtrack.mp4"), os.path.join(CH, f"c{ci}_band.mp4"),  f0, n, "v")
    v = trim(os.path.join(AS, "vo.mp4"),        os.path.join(CH, f"c{ci}_vo.m4a"),    f0, n, "a")
    for p in (a, b):
        got = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames",
            "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
            "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip().rstrip(","))
        assert got == n, f"{os.path.basename(p)}: {got} frames, wanted {n}"

    # ── the face state, and the last one before the chunk starts ───────────
    pre_state, tl_cuts = "split", []
    for r in SHOTS:
        t = r["his"][0] - T0
        st = "full" if r["kind"] == "full" else "split"
        if t < -1e-9:
            pre_state = st
        elif t < dur:
            tl_cuts.append(f'cut("{st}", {t:7.3f});   // {r["note"]}')

    # ── captions: one static entry state, then the ones inside the chunk ───
    pre_cap, tl_caps = "", []
    for t, txt in CAPS:
        rt = t - T0
        if rt < -1e-9:
            pre_cap = txt
        elif rt < dur:
            tl_caps.append([round(rt, 3), txt])

    cta_t = 32.900 - T0
    cta_pre = cta_t < -1e-9
    cta_in = -1e-9 <= cta_t < dur
    flashes = [round(f - T0, 3) for f in FLASH if 0 <= f - T0 < dur]

    sfx, k = [], 0
    for r in SHOTS:
        t = r["his"][0] - T0
        if r["his"][0] <= 0.001:      f, vol, d = "riser.mp3", 0.16, 0.60
        elif r["his"][0] in FULL_T:   f, vol, d = "wsh2.mp3", 0.13, 0.35
        elif r["kind"] == "mock":     f, vol, d = "wsh.mp3", 0.12, 0.32
        else:                         f, vol, d = ("click.mp3" if k % 2 else "click2.mp3"), 0.11, 0.20
        if 0 <= t < dur:
            sfx.append(f'  <audio id="sx{k:02d}" src="assets/sfx/{f}" data-start="{t:.3f}" '
                       f'data-duration="{d:.2f}" data-track-index="{40+k}" data-volume="{vol}"></audio>')
        k += 1
    st = 32.900 - T0
    if 0 <= st < dur:
        sfx.append(f'  <audio id="sxS" src="assets/sfx/shine2.mp3" data-start="{st:.3f}" '
                   f'data-duration="0.90" data-track-index="90" data-volume="0.15"></audio>')

    html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>vid67 chunk {ci} — frames {f0}-{f1}</title>
<style>
@font-face{{font-family:'Inter';src:url('assets/fonts/inter-800.woff2')format('woff2');font-weight:800;font-display:block}}
@font-face{{font-family:'Inter';src:url('assets/fonts/inter-600.woff2')format('woff2');font-weight:600;font-display:block}}

/* vid67 chunk {ci} of 3 — source frames {f0}..{f1} ({n} frames, {dur:.6f}s).
   Generated by vid67/build_chunks.py; see hf67/index.html for the full film and
   the reasoning behind every number below. Media is pre-trimmed so both videos
   start at 0; timeline events before this chunk are applied statically at load
   because a negative GSAP position shifts the whole timeline. */

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
#btop{{position:absolute;left:0;top:0;width:1080px;height:{BAND}px;z-index:5;
  overflow:hidden;background:#0A0A0C;}}
#btop video{{position:absolute;left:0;top:0;width:1080px;height:{BAND}px;
  object-fit:cover;display:block;}}
#seam{{position:absolute;left:0;top:{BAND-2}px;width:1080px;height:4px;z-index:6;
  background:rgba(0,0,0,.55);}}
#capW{{position:absolute;left:0;top:{CAP_S}px;width:1080px;text-align:center;z-index:8;}}
#capW.full{{top:{CAP_F}px;}}
#cap{{display:inline-block;font-family:'Inter';font-weight:800;font-size:44px;
  letter-spacing:-.018em;line-height:1.14;color:#FFFFFF;
  background:rgba(10,10,12,.70);border-radius:12px;padding:9px 20px 12px;
  text-shadow:0 2px 10px rgba(0,0,0,.5);white-space:nowrap;}}
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
<div id="root" data-composition-id="vid67c{ci}" data-start="0"
     data-duration="{dur:.6f}" data-fps="{FPS}" data-width="2160" data-height="3840">
  <div id="stage">
    <div id="faceScene" data-layout-ignore>
      <div id="faceCam">
        <video id="aroll" src="assets/chunks/c{ci}_aroll.mp4" data-start="0"
               data-duration="{dur:.6f}" data-track-index="0" muted playsinline></video>
      </div>
    </div>
    <div id="btop" data-layout-ignore>
      <video id="vband" src="assets/chunks/c{ci}_band.mp4" data-start="0"
             data-duration="{dur:.6f}" data-track-index="1" muted playsinline></video>
    </div>
    <div id="seam" data-layout-ignore></div>
    <div id="capW"><div id="cap"></div></div>
    <div id="cta"><div id="ctaP"><span id="ctaT">Comment AGENT</span><span id="ctaA">↑</span></div></div>
    <div id="flash" data-layout-ignore></div>
  </div>
  <audio id="vo" src="assets/chunks/c{ci}_vo.m4a" data-start="0"
         data-duration="{dur:.6f}" data-track-index="30" data-volume="1"></audio>
{chr(10).join(sfx)}
</div>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script>
var tl = gsap.timeline({{ paused: true, defaults: {{ immediateRender: false }} }});
window.__timelines = {{ vid67c{ci}: tl }};
var HALF = 0.5 / {FPS};
function put(sel, vars, t){{ if (t <= HALF) gsap.set(sel, vars); if (t >= 0) tl.set(sel, vars, t); }}
var FACE = {{
  full:  {{ clip:"inset(0px 0px 0px 0px)",     cam:{{ x:0, y:0,     scale:1 }} }},
  split: {{ clip:"inset({BAND}px 0px 0px 0px)", cam:{{ x:0, y:{SHIFT}, scale:1 }} }}
}};
function apply(state){{
  var f = FACE[state];
  gsap.set("#faceScene", {{ clipPath: f.clip }});
  gsap.set("#faceCam", Object.assign({{ transformOrigin:"0 0" }}, f.cam));
  gsap.set("#btop", {{ autoAlpha: state === "split" ? 1 : 0 }});
  gsap.set("#seam", {{ autoAlpha: state === "split" ? 1 : 0 }});
  document.getElementById("capW").className = state === "split" ? "" : "full";
}}
function cut(state, t){{
  var f = FACE[state];
  put("#faceScene", {{ clipPath: f.clip }}, t);
  put("#faceCam", Object.assign({{ transformOrigin:"0 0" }}, f.cam), t);
  put("#btop", {{ autoAlpha: state === "split" ? 1 : 0 }}, t);
  put("#seam", {{ autoAlpha: state === "split" ? 1 : 0 }}, t);
  put("#capW", {{ className: state === "split" ? "" : "full" }}, t);
}}

/* the state this chunk is ENTERED in, applied statically */
apply({json.dumps(pre_state)});
document.getElementById("cap").textContent = {json.dumps(pre_cap)};
{"gsap.set('#cta', { autoAlpha:1, scale:1, y:0 });" if cta_pre else "gsap.set('#cta', { autoAlpha:0 });"}

{chr(10).join(tl_cuts)}

var CAPS = {json.dumps(tl_caps)};
window.__CAPS = CAPS;
(function(){{
  var el = document.getElementById("cap");
  for (var i = 0; i < CAPS.length; i++){{
    (function(c){{
      tl.call(function(){{ el.textContent = c[1]; }}, null, c[0]);
      tl.fromTo("#cap", {{ scale:0.94 }}, {{ scale:1, duration:0.10, ease:"power2.out",
        transformOrigin:"50% 50%" }}, c[0]);
    }})(CAPS[i]);
  }}
}})();
{f'''
tl.set("#cta", {{ autoAlpha:1 }}, {cta_t:.3f});
tl.fromTo("#cta", {{ scale:0.90, y:16 }}, {{ scale:1, y:0, duration:0.28,
  ease:"back.out(2.0)", transformOrigin:"50% 50%" }}, {cta_t:.3f});''' if cta_in else ""}
{f'''
tl.to("#cap", {{ opacity:0, duration:0.24, ease:"power2.in" }}, {35.233 - 0.30 - T0:.3f});''' if (35.233 - 0.30 - T0) < dur and (35.233 - 0.30 - T0) >= 0 else ""}
{chr(10).join(f'''tl.fromTo("#flash", {{ opacity:0 }}, {{ opacity:0.40, duration:0.05, ease:"none" }}, {max(0, t-0.05):.3f});
tl.to("#flash", {{ opacity:0, duration:0.06, ease:"none" }}, {t:.3f});''' for t in flashes)}
</script>
</body>
</html>
'''
    p = os.path.join(HF, f"index-c{ci}.html")
    open(p, "w").write(html)
    print(f"  c{ci}: frames {f0:4d}-{f1:4d} ({n:3d}) dur {dur:.6f}s  "
          f"{len(tl_cuts)} cuts, {len(tl_caps)} caps, {len(sfx)} sfx, "
          f"enters {pre_state}/{pre_cap!r}")
    return n


print(f"chunking {TOTAL} frames at {BOUNDS[1:-1]} (both land on real cuts)")
tot = 0
for i in range(3):
    tot += emit(i + 1, BOUNDS[i], BOUNDS[i + 1])
assert tot == TOTAL, f"{tot} != {TOTAL}"
print(f"total {tot} frames == {TOTAL}")
