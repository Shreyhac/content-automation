#!/usr/bin/env python3
"""Concatenate the three chunk renders and lay the audio bed in one pass.

VIDEO is stream-copied, so every delivered frame is bit-identical to the frame
its chunk render produced — the concat cannot re-encode or shift anything.

AUDIO IS REBUILT FROM THE FULL-LENGTH SOURCES rather than concatenated from the
chunks. Each chunk render carries its own AAC track, and AAC has encoder priming
at the start of every stream; joining three of them puts a small discontinuity at
each boundary, which is exactly the kind of thing that comes back as a "weird
audio cut" note. The VO is one continuous file and the SFX cues have absolute
times, so building the bed once over the whole 35.233s is both simpler and
correct.

VERIFICATION (not assumed):
  - every chunk must agree on codec, profile, level, pix_fmt, resolution and fps
  - the frame counts must sum to exactly 1057
  - the assembled file must report 1057 frames and 35.233s
  - the frame pair either side of each join is written to qa/ to be looked at
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HF   = os.path.join(ROOT, "hf67")
R    = os.path.join(HF, "renders")
AS   = os.path.join(HF, "assets")
QA   = os.path.join(HF, "rqa")
FPS, TOTAL, DUR = 30, 1057, 35.233333
BOUNDS = [0, 346, 689, TOTAL]
OUT = os.path.join(ROOT, "out", "vid67-final.mp4")
os.makedirs(QA, exist_ok=True)

SHOTS = json.load(open(os.path.join(HERE, "shots.json")))
FULL_T = [r["his"][0] for r in SHOTS if r["kind"] == "full"]


def probe(p, keys):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=" + ",".join(keys), "-of", "csv=p=0", p],
        capture_output=True, text=True).stdout.strip()
    return out


def nframes(p):
    return int(subprocess.run(["ffprobe", "-v", "error", "-count_frames",
        "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
        "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip().rstrip(","))


chunks = [os.path.join(R, f"c{i}.mp4") for i in (1, 2, 3)]
for c in chunks:
    if not os.path.exists(c):
        sys.exit(f"missing {c} — render the chunks first")

KEYS = ["codec_name", "profile", "level", "pix_fmt", "width", "height", "r_frame_rate"]
sigs = [probe(c, KEYS) for c in chunks]
print("stream signatures:")
for c, s in zip(chunks, sigs):
    print(f"  {os.path.basename(c)}  {s}")
assert len(set(sigs)) == 1, "chunks disagree on stream parameters — concat would be invalid"

counts = [nframes(c) for c in chunks]
want = [BOUNDS[i+1] - BOUNDS[i] for i in range(3)]
print(f"frames {counts} (expected {want})")
assert counts == want, "a chunk rendered the wrong number of frames"
assert sum(counts) == TOTAL

# ── 1. video: stream copy ─────────────────────────────────────────────────
lst = os.path.join(R, "concat.txt")
open(lst, "w").write("".join(f"file '{c}'\n" for c in chunks))
vonly = os.path.join(R, "_video.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
    "-i", lst, "-an", "-c", "copy", vonly], check=True)
print(f"concatenated video: {nframes(vonly)} frames")

# ── 2. audio: the VO plus every SFX cue at its absolute time ──────────────
cues, k = [], 0
for r in SHOTS:
    t = r["his"][0]
    if t <= 0.001:            f, vol = "riser.mp3", 0.16
    elif t in FULL_T:         f, vol = "wsh2.mp3", 0.13
    elif r["kind"] == "mock": f, vol = "wsh.mp3", 0.12
    else:                     f, vol = ("click.mp3" if k % 2 else "click2.mp3"), 0.11
    cues.append((os.path.join(AS, "sfx", f), t, vol)); k += 1
cues.append((os.path.join(AS, "sfx", "shine2.mp3"), 32.900, 0.15))

ins, filt = ["-i", os.path.join(AS, "vo.mp4")], []
labels = ["[0:a]"]
for i, (p, t, v) in enumerate(cues, start=1):
    ins += ["-i", p]
    filt.append(f"[{i}:a]adelay={int(t*1000)}|{int(t*1000)},volume={v}[s{i}]")
    labels.append(f"[s{i}]")
filt.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:"
            f"dropout_transition=0,apad=whole_dur={DUR:.6f},"
            f"atrim=0:{DUR:.6f}[a]")
aonly = os.path.join(R, "_audio.m4a")
subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
    ";".join(filt), "-map", "[a]", "-c:a", "aac", "-b:a", "192k", aonly], check=True)
print(f"audio bed: 1 VO + {len(cues)} cues")

# ── 3. mux ────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT), exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vonly, "-i", aonly,
    "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-movflags", "+faststart",
    OUT], check=True)

n = nframes(OUT)
info = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
    "format=duration,size,bit_rate", "-of", "default=noprint_wrappers=1:nokey=0",
    OUT], capture_output=True, text=True).stdout.strip()
print(f"\n{OUT}\n  {n} frames (expected {TOTAL})\n  " + "\n  ".join(info.splitlines()))
assert n == TOTAL, "assembled frame count is wrong"

# ── 4. write the frame pair either side of each join, to be LOOKED at ─────
for b in BOUNDS[1:-1]:
    for off, tag in ((b - 1, "before"), (b, "after")):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", OUT, "-vf",
            f"select=eq(n\\,{off}),scale=540:960", "-frames:v", "1",
            os.path.join(QA, f"join{b}_{tag}_f{off}.png")], check=True)
print(f"join frames -> {QA}/join*.png")
for f in (vonly, aonly, lst):
    os.remove(f)
