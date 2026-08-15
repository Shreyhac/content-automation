#!/usr/bin/env python3
"""Pick the 8 chunk boundaries on the RE-CUT timeline.

Every boundary must land on a word onset that follows a gap of >= MIN_GAP, so a
chunk join never falls inside a spoken word and the VO master can be sliced per
chunk for QA without clipping a syllable. Boundaries are frame-exact.

The 8 chunks also have to stay near-equal in length: HyperFrames renders one
composition at a time and an oversized chunk is the one that runs out of memory.
"""
import json, sys

FPS = 30
TOTAL_F = 6702                 # 223.400s
N = 8
MIN_GAP = 0.20
SEARCH = 3.5                   # seconds either side of the ideal split

words = []
for s in json.load(open("recut/vo-master.json"))["segments"]:
    for w in s.get("words", []):
        words.append((float(w["start"]), float(w["end"]), w["word"].strip()))
words.sort()

# candidate boundaries: a word onset preceded by real silence
cands = []
for i, (a, b, t) in enumerate(words):
    prev_end = words[i-1][1] if i else 0.0
    gap = a - prev_end
    if i and gap >= MIN_GAP:
        cands.append((a, gap, t))

print(f"{len(words)} words · {len(cands)} candidate boundaries (gap >= {MIN_GAP}s)\n")

bounds = [0]
for k in range(1, N):
    ideal = TOTAL_F * k / N / FPS
    near = [c for c in cands if abs(c[0] - ideal) <= SEARCH]
    if not near:
        print(f"!! no candidate within {SEARCH}s of {ideal:.2f}s"); sys.exit(1)
    # prefer the widest gap, then the closest to ideal, a wide gap is a real
    # sentence break, which is where a cut wants to be
    best = max(near, key=lambda c: (round(c[1], 2), -abs(c[0] - ideal)))
    f = int(round(best[0] * FPS))
    bounds.append(f)
    print(f"  split {k}: ideal {ideal:7.2f}s -> {best[0]:7.2f}s "
          f"(f{f}, gap {best[1]:.2f}s) before {best[2]!r}")
bounds.append(TOTAL_F)

# strictly increasing, no zero-length chunk
for i in range(1, len(bounds)):
    assert bounds[i] > bounds[i-1], bounds

print()
lines = []
for i in range(N):
    a, b = bounds[i], bounds[i+1]
    name = f"c{i+1}"
    lines.append(f"{name}:{a}:{b}")
    print(f"  {name}  f{a:5d}-{b:5d}  {b-a:4d} frames  "
          f"{a/FPS:7.3f}-{b/FPS:7.3f}s  ({(b-a)/FPS:6.3f}s)")
tot = sum(bounds[i+1]-bounds[i] for i in range(N))
print(f"\n  total {tot} frames (want {TOTAL_F})")
assert tot == TOTAL_F

open("recut/chunks.txt", "w").write("\n".join(lines) + "\n")
json.dump({"fps": FPS, "total_frames": TOTAL_F,
           "chunks": [{"name": f"c{i+1}", "a": bounds[i], "b": bounds[i+1],
                       "t0": round(bounds[i]/FPS, 6),
                       "dur": round((bounds[i+1]-bounds[i])/FPS, 6),
                       "frames": bounds[i+1]-bounds[i]} for i in range(N)]},
          open("recut/chunks.json", "w"), indent=1)
print("wrote recut/chunks.txt + recut/chunks.json")
