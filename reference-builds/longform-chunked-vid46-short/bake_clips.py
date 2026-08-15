#!/usr/bin/env python3
"""Bake the A-roll's HERO pixels and the b-roll cards as ready-to-place video.

FACE. One bake per face block, at the HERO size (1080 x 1210, lanczos from the 3840
master). The CARD state is a CSS transform of those same pixels rather than a second
bake, which is the whole point: the move between the two states has to be a continuous
tween (vid39's device), and you cannot tween between two different files. The extra
0.6786 downscale in card mode happens in the browser, where it is a downscale of an
already-sharp image and softness does not read.

B-ROLL. Carded, never full-bleed, and cut to the exact rect it will occupy so the
browser never resamples it either. The clips are the ones already sourced and graded
for the long-form, so they are on-theme and in the film's own palette.

A re-solve re-bakes; nothing is hand-typed into the HTML.
"""
import json, subprocess, os
from beats import resolve, FACE_CLIPS, FPS

AROLL = "../hf46/assets/aroll"
BROLL = "../hf46/assets/broll"
# chunk t0 on the re-cut timeline -> which clip holds a given source time
CHUNK_T0 = [("c1", 0.0), ("c2", 28.7), ("c3", 54.033333), ("c4", 83.633333),
            ("c5", 112.066667), ("c6", 139.233333), ("c7", 168.266667),
            ("c8", 197.466667)]
X264 = ["-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-g", "15", "-keyint_min", "15", "-r", str(FPS), "-an"]

# name, source clip, in-point, seconds, output WxH.
# Each rect is the card it is placed into, so nothing is scaled at runtime.
BROLL = [
    dict(out="b3-aisle",   src="aisle",   ss=1.0, dur=3.20, w=936, h=240,
         note="server aisle under 'data broker websites and private databases'"),
    dict(out="b6-bundle",  src="bundle",  ss=0.6, dur=4.20, w=936, h=300,
         note="a laptop at night: the bundle you are already paying for"),
    dict(out="b7-pricing", src="pricing", ss=0.8, dur=1.70, w=936, h=300,
         note="a card being handed over, cut in on 'paying twice'"),
]

T = json.load(open("short-transforms.json"))
resolve()
os.makedirs("assets/aroll", exist_ok=True)
os.makedirs("assets/broll", exist_ok=True)


def src_of(t):
    name, t0 = [c for c in CHUNK_T0 if c[1] <= t + 1e-6][-1]
    return f"{AROLL}/{name}.mp4", t - t0


def probe(p):
    return subprocess.run(["ffprobe", "-v", "error", "-count_frames",
                           "-select_streams", "v",
                           "-show_entries", "stream=nb_read_frames,width,height",
                           "-of", "csv=p=0", p], capture_output=True,
                          text=True).stdout.strip()


for c in FACE_CLIPS:
    r = T["clips"][c["clip"]]
    clip, local = src_of(c["src_a"])
    want = c["frames"]
    out = f"assets/aroll/{c['clip']}.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{local:.6f}", "-i", clip,
         "-frames:v", str(want + 2),
         "-vf", f"scale={r['scale_w']}:{r['scale_h']}:flags=lanczos,"
                f"crop={r['crop_w']}:{r['crop_h']}:{r['crop_x']}:{r['crop_y']},"
                f"tpad=stop_mode=clone:stop=2",
         *X264, "-frames:v", str(want), out], check=True)
    got = probe(out)
    print(f"FACE {c['clip']:3} {os.path.basename(clip)} @{local:7.3f}  {want:4}f "
          f"({c['dur']:.3f}s)  crop_x={r['crop_x']}  -> {out}  {got}")
    assert got.startswith(f"{r['crop_w']},{r['crop_h']},"), (out, got)
    assert got.endswith(f",{want}"), (out, got, want)

for b in BROLL:
    src = f"../hf46/assets/broll/{b['src']}.mp4"
    out = f"assets/broll/{b['out']}.mp4"
    n = round(b["dur"] * FPS)
    # cover the rect, then centre-crop it: never letterbox, never squash
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{b['ss']}", "-i", src,
         "-frames:v", str(n + 2),
         "-vf", f"scale={b['w']}:-2:flags=lanczos,"
                f"crop={b['w']}:{b['h']}:0:(ih-{b['h']})/2,"
                f"tpad=stop_mode=clone:stop=2",
         *X264, "-frames:v", str(n), out], check=True)
    print(f"BROLL {b['out']:12} {b['src']:9} {b['dur']:5.2f}s  {b['w']}x{b['h']}  "
          f"-> {out}  {probe(out)}")

print("\nface clips baked at 1080x1210 (HERO); b-roll baked to its exact card rect.")
