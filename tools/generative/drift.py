#!/usr/bin/env python3
"""drift.py, the measurement that decides whether a generated clip is usable.

    python3 tools/generative/drift.py clip.mp4 \
        --region face:300,240,520,620 --region hand-l:120,1180,340,360

    python3 tools/generative/drift.py clip.mp4 --grid 4x6          # fallback
    python3 tools/generative/drift.py clip.mp4 --ref-image plate.jpg --grid 4x6

MEASURE DRIFT ON A CROP AROUND EVERY FACE AND EVERY HAND, NEVER GLOBALLY.

Global mean|delta| against frame 0 looked acceptable on a client take while a
hand was morphing into a second face at the subject's hairline. Cropping to the head
region exposed it climbing 12 to 24. A global average over a mostly static
plate cannot see a local catastrophe, and the local catastrophe is the only
thing a viewer will look at. This script therefore reports per region and fails
on the WORST region, never on the mean of them.

It also samples 0.1s, mid and end explicitly, because a held pose drifts mid
clip, not only at the end: on vid15 the subject's arms uncrossed and a hand melted into
their sweater within 1 second, and a last-frame check passed it.

When a take is clean early and rots late, trim to the clean window and mirror
it back, forward plus a reversed tail. The clean-window line at the bottom of
the report is the number to trim on.

With --ref-image the reference is a still rather than the clip's own frame 0.
That is the background-redress check: asking an image model for a new
expression makes it silently redress the room, and two of three variants did.
Diff the new plate against the approved plate, not just the face.

No API, no key, no cost. Run it on every generated clip before it enters a cut.
"""
import argparse
import json
import subprocess
import sys

import numpy as np


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height", "-show_entries", "format=duration",
        "-of", "json", path])
    d = json.loads(out)
    s = d["streams"][0]
    return int(s["width"]), int(s["height"]), float(d["format"]["duration"])


def gray_frames(path, w, h, fps):
    """Decode to 8-bit gray rawvideo and reshape. Luma only: a colour drift big
    enough to matter moves luma too, and gray is a third of the memory, which
    is what lets this run at full resolution instead of on a downscale that
    hides a 40px hand."""
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps}",
           "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[:n * w * h], dtype=np.uint8).reshape(n, h, w)


def gray_image(path, w, h):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf",
           f"scale={w}:{h}:flags=lanczos", "-pix_fmt", "gray",
           "-frames:v", "1", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw[:w * h], dtype=np.uint8).reshape(h, w)


def parse_regions(specs, w, h):
    out = []
    for s in specs:
        name, _, box = s.partition(":")
        if not box:
            raise SystemExit(f"bad --region {s!r}, want name:x,y,w,h")
        x, y, rw, rh = (int(v) for v in box.split(","))
        x, y = max(0, x), max(0, y)
        rw, rh = min(rw, w - x), min(rh, h - y)
        if rw <= 0 or rh <= 0:
            raise SystemExit(f"region {name} falls outside the {w}x{h} frame")
        out.append((name, x, y, rw, rh))
    return out


def grid_regions(w, h, spec):
    cols, rows = (int(v) for v in spec.lower().split("x"))
    cw, ch = w // cols, h // rows
    return [(f"t{c}{r}", c * cw, r * ch, cw, ch)
            for r in range(rows) for c in range(cols)]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video")
    p.add_argument("--region", action="append", default=[],
                   metavar="NAME:X,Y,W,H",
                   help="a crop around one face or one hand. Repeatable.")
    p.add_argument("--region-file", help="JSON list of the same strings")
    p.add_argument("--grid", help="fallback tiling, eg 4x6, when no regions are named")
    p.add_argument("--ref-image", help="compare against a still (the approved plate) "
                                       "instead of the clip's own frame 0")
    p.add_argument("--ref-time", type=float, default=0.0,
                   help="which second of the clip is the reference frame")
    p.add_argument("--fps", type=float, default=5.0)
    p.add_argument("--warn", type=float, default=8.0)
    p.add_argument("--fail", type=float, default=12.0,
                   help="the head crop that hid a hand morphing into a face "
                        "climbed 12 to 24. 12 is that floor.")
    p.add_argument("--json-out")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    w, h, dur = probe(a.video)
    specs = list(a.region)
    if a.region_file:
        with open(a.region_file) as f:
            specs += json.load(f)
    if specs:
        regions = parse_regions(specs, w, h)
    elif a.grid:
        regions = grid_regions(w, h, a.grid)
        print("WARNING: no named regions. A grid finds a local catastrophe but "
              "it does not know where the face is, and a face that straddles "
              "four tiles dilutes into all four. Name the crops.")
    else:
        raise SystemExit("give --region (preferred) or --grid")

    print(f"{a.video}  {w}x{h}  {dur:.2f}s  sampling {a.fps} fps  "
          f"{len(regions)} regions")
    if a.dry_run:
        print(f"ffmpeg -v error -i {a.video} -vf fps={a.fps} -pix_fmt gray "
              f"-f rawvideo -")
        if a.ref_image:
            print(f"ffmpeg -v error -i {a.ref_image} -vf scale={w}:{h} "
                  f"-pix_fmt gray -frames:v 1 -f rawvideo -")
        for name, x, y, rw, rh in regions:
            print(f"  region {name:12} x{x} y{y} {rw}x{rh}")
        print(f"metric: mean|delta| of luma against "
              f"{'the reference still' if a.ref_image else f'the frame at t={a.ref_time}'}"
              f", per region, warn {a.warn} fail {a.fail}")
        return

    frames = gray_frames(a.video, w, h, a.fps)
    if len(frames) == 0:
        raise SystemExit("decoded zero frames")
    times = [i / a.fps for i in range(len(frames))]

    if a.ref_image:
        ref = gray_image(a.ref_image, w, h).astype(np.int16)
    else:
        ri = min(int(round(a.ref_time * a.fps)), len(frames) - 1)
        ref = frames[ri].astype(np.int16)

    series = {}
    for name, x, y, rw, rh in regions:
        r = ref[y:y + rh, x:x + rw]
        series[name] = [float(np.abs(frames[i][y:y + rh, x:x + rw].astype(np.int16)
                                     - r).mean()) for i in range(len(frames))]

    glob = [float(np.abs(frames[i].astype(np.int16) - ref).mean())
            for i in range(len(frames))]

    print(f"\n{'region':14} {'peak':>6} {'at':>7} {'0.1s':>6} {'mid':>6} {'end':>6}")

    def at(t):
        return min(int(round(t * a.fps)), len(frames) - 1)

    i01, imid, iend = at(0.1), at(dur / 2), len(frames) - 1
    worst = ("", 0.0, 0.0)
    rows = []
    for name, *_ in regions:
        s = series[name]
        pk = max(s)
        pkt = times[s.index(pk)]
        rows.append(dict(region=name, peak=round(pk, 2), peak_t=round(pkt, 2),
                         t0_1=round(s[i01], 2), mid=round(s[imid], 2),
                         end=round(s[iend], 2)))
        if pk > worst[1]:
            worst = (name, pk, pkt)
        mark = "FAIL" if pk >= a.fail else ("warn" if pk >= a.warn else "")
        print(f"{name:14} {pk:6.2f} {pkt:6.2f}s {s[i01]:6.2f} {s[imid]:6.2f} "
              f"{s[iend]:6.2f} {mark}")

    print(f"{'GLOBAL':14} {max(glob):6.2f} {times[glob.index(max(glob))]:6.2f}s "
          f"{glob[i01]:6.2f} {glob[imid]:6.2f} {glob[iend]:6.2f}   "
          f"<- this number is the one that lies")

    clean_end = dur
    for i in range(len(frames)):
        if any(series[n][i] >= a.fail for n, *_ in regions):
            clean_end = times[i]
            break
    if clean_end < dur:
        keep = max(clean_end - 1 / a.fps, 0.0)
        print(f"\nclean window: 0 to {keep:.2f}s of {dur:.2f}s. Trim there and "
              f"mirror it back, forward plus a reversed tail, rather than "
              f"regenerating a take whose first half is good.")

    result = dict(video=a.video, width=w, height=h, duration=round(dur, 3),
                  fps=a.fps, warn=a.warn, fail=a.fail,
                  reference=a.ref_image or f"t={a.ref_time}",
                  regions=rows, global_peak=round(max(glob), 2),
                  clean_until=round(clean_end, 2))
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(result, f, indent=2)
        print("wrote", a.json_out)

    if worst[1] >= a.fail:
        print(f"\nFAIL {worst[0]} peaked {worst[1]:.2f} at {worst[2]:.2f}s "
              f"(threshold {a.fail}). Do not put this clip in a cut.")
        sys.exit(1)
    print(f"\nPASS worst region {worst[0]} {worst[1]:.2f} under {a.fail}")


if __name__ == "__main__":
    main()
