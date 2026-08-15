#!/usr/bin/env python3
"""Flatten the 17 B-roll slots into ONE 35.233s band track.

WHY. The first 4K render stalled at frame 746/1057 — "Sequential drawElement
capture stalled". The page held 18 <video> elements (the A-roll plus one per
shot); extraction of all 18 succeeded, so the cost was in the per-frame capture,
which must service every video element on every frame. hf66b survived 25 videos
at 796 frames; this composition is 1057 frames on an 8 GB machine already pinned
to 1 worker in low-memory mode, and that was the difference.

Pre-composing the band is what an editor would do anyway: the clips play
back-to-back in a fixed order, so they are ONE track, not seventeen layers. The
page now holds 2 videos. It also removes an entire defect class — a <video>
painted outside its own data-start window renders dead grey, and with one
always-on element there is no window to fall outside of.

FRAME EXACTNESS. Segment lengths are taken as DIFFERENCES OF ROUNDED cumulative
boundaries, never as rounded differences, so the parts sum to exactly 1057
frames with no drift. (HyperFrames ceils duration*fps, so an off-by-one here
becomes a desync that only the rendered file shows.)
"""
import json, math, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BR   = os.path.join(ROOT, "hf67", "assets", "broll")
OUT  = os.path.join(ROOT, "hf67", "assets", "bandtrack.mp4")
TMP  = os.path.join(HERE, "_band")
FPS, W, H = 30, 2160, 1240
DUR = 35.233333
TOTAL = int(round(DUR * FPS))          # 1057

shots = json.load(open(os.path.join(HERE, "shots.json")))
os.makedirs(TMP, exist_ok=True)
for f in os.listdir(TMP): os.remove(os.path.join(TMP, f))

edges = [int(round(r["his"][0] * FPS)) for r in shots] + [TOTAL]
parts, log = [], []
for i, r in enumerate(shots):
    n = edges[i+1] - edges[i]
    assert n > 0, r
    dst = os.path.join(TMP, "p%02d.mp4" % i)
    if r["kind"] == "full":
        # the band is hidden on these beats; black keeps the track continuous
        subprocess.run(["ffmpeg","-y","-v","error","-f","lavfi","-i",
            f"color=c=black:s={W}x{H}:r={FPS}:d={n/FPS:.6f}","-frames:v",str(n),
            "-c:v","libx264","-crf","18","-preset","veryfast","-pix_fmt","yuv420p",
            "-g","15","-keyint_min","15",dst],check=True)
    else:
        src = os.path.join(BR, r["id"] + ".mp4")
        subprocess.run(["ffmpeg","-y","-v","error","-i",src,"-frames:v",str(n),
            "-an","-vf",f"fps={FPS},scale={W}:{H}","-c:v","libx264","-crf","14",
            "-preset","slow","-pix_fmt","yuv420p","-g","15","-keyint_min","15",
            dst],check=True)
    got = int(subprocess.run(["ffprobe","-v","error","-count_frames",
        "-select_streams","v:0","-show_entries","stream=nb_read_frames",
        "-of","csv=p=0",dst],capture_output=True,text=True).stdout.strip().rstrip(","))
    assert got == n, f"{r['id']}: asked {n} frames, got {got}"
    parts.append(dst); log.append((r["kind"], r["id"] or "-", n, got))

lst = os.path.join(TMP, "list.txt")
open(lst,"w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",lst,
    "-c:v","libx264","-crf","14","-preset","slow","-pix_fmt","yuv420p",
    "-r",str(FPS),"-g","15","-keyint_min","15",OUT],check=True)

n = int(subprocess.run(["ffprobe","-v","error","-count_frames","-select_streams",
    "v:0","-show_entries","stream=nb_read_frames","-of","csv=p=0",OUT],
    capture_output=True,text=True).stdout.strip().rstrip(","))
d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
    "-of","csv=p=0",OUT],capture_output=True,text=True).stdout.strip())
for k,i,want,got in log: print(f"  {k:5s} {i:11s} {want:4d} frames")
print(f"\nbandtrack: {n} frames ({d:.3f}s)  expected {TOTAL} ({DUR:.3f}s)  "
      f"{'OK' if n==TOTAL else 'FRAME COUNT MISMATCH'}")
print(f"size {os.path.getsize(OUT)/1e6:.1f} MB")
