#!/usr/bin/env python3
"""Per-frame gaze -> face-safe windows.

vid44 used a single signal (eye openness) because that take was cleanly bimodal.
This take is NOT: Nader reads from two different note positions.

  mode A  eyes dropped, head level   -> eyeOpen 0.10-0.22          (vid44's signal catches it)
  mode B  head pitched down          -> eyeOpen 0.29-0.32, but the face contour
                                        FORESHORTENS: aspect (h/w) 0.83-0.89 vs 0.92-1.06
  camera                             -> eyeOpen 0.37-0.46, aspect 0.92-1.06

Mode B sits right on vid44's 0.30 threshold and passed as "safe" until the crops were
read. Both signals are required; either one firing means he is reading.

ROUND 2 — a blink discriminator was built, measured, and deliberately LEFT OFF.

MIN_RUN=2 is documented as "blinks survive by the >=2-frame minimum". That is only
true for a favourable sampling phase. Re-extracting the 5fps stills through the
re-cut's frame-select filter shifted the phase, and a blink at 12.6-12.8s landed on
two consecutive samples:

    t=12.4  eye .375  aspect 1.002
    t=12.6  eye .159  aspect  .980   <- fully closed
    t=12.8  eye .284  aspect  .939   <- reopening
    t=13.0  eye .374  aspect  .997

which the base rule scores as a 2s "reading" run in the middle of the HOOK.

A blink is a V (one or two near-closed samples bracketed by normal ones, head never
pitching); a read is a PLATEAU. Adding "a short run only counts if it lasts >=0.8s
or the aspect signal corroborates it" (BLINK_REJECT below) removes 26 such runs and
lifts face-safe coverage from 41.1% to 62.8%.

IT IS OFF, because reading the crops it produced showed it is not safe yet. At
t=114.0 and t=117.0 he is genuinely glancing down at notes, and BOTH signals read
clean camera there (eye .34, aspect 1.03-1.08) — so those frames are only excluded
today as a side effect of the padding around neighbouring blink runs. Rejecting the
blinks removes that padding and puts real down-looks on screen, which breaks the
client's one hard rule.

The signal that does separate them is browEyeGap, which the detector already emits:
across 113.4-114.6 (down) it sits at .072-.081, against .087-.140 at camera. That is
a promising third signal but it is unvalidated across the whole take, and pitch —
which would settle it directly — is NA on all 1117 frames from this Vision revision.

So round 2 ships the rule the owner already accepted in round 1. It errs toward
hiding him, which is the correct direction to err: an extra second of graphics is a
soft cost, showing him reading is a hard failure. Its one artifact — the 11.7-13.7
hole in the hook — lands inside the head-to-head lockup, where the face is hidden
anyway, so it costs nothing.
"""
import csv, json

FPS        = 5.0
EYE_T      = 0.30    # below => eyes down
ASPECT_T   = 0.905   # below => head pitched down (plateau p95 .893 | camera p05 .920)
MIN_RUN    = 2       # >=2 frames (0.4s) => a candidate, not noise
MIN_SUSTAIN= 4       # >=4 frames (0.8s) => sustained on its own, no blink lasts this
BLINK_REJECT = False # see the module docstring — measured, not trusted yet
PAD        = 0.9
MIN_WIN    = 1.6

def key(f): return round((int(f.split("_")[1].split(".")[0]) - 1) / FPS, 1)

eye, asp = {}, {}
for r in csv.DictReader(open("gaze/gaze.csv")):
    try: eye[key(r["file"])] = (float(r["eyeOpenL"]) + float(r["eyeOpenR"])) / 2
    except ValueError: eye[key(r["file"])] = 0.0
for r in csv.DictReader(open("facebox.csv")):
    try:
        h = (float(r["contourBot"]) - float(r["contourTop"])) * 2160
        w = (float(r["contourRight"]) - float(r["contourLeft"])) * 3840
        asp[key(r["file"])] = h / w
    except ValueError: asp[key(r["file"])] = 0.0

ks = sorted(set(eye) | set(asp))
N  = len(ks)
DUR = N / FPS
lowe = [eye.get(k, 0.0) < EYE_T    for k in ks]
lowa = [asp.get(k, 0.0) < ASPECT_T for k in ks]
down = [lowe[i] or lowa[i] for i in range(N)]

runs, blinks, i = [], [], 0
while i < N:
    if down[i]:
        j = i
        while j < N and down[j]: j += 1
        n = j - i
        pitched = any(lowa[i:j])
        keep = n >= MIN_RUN and (not BLINK_REJECT or n >= MIN_SUSTAIN or pitched)
        if keep:
            tags = set()
            if any(lowe[i:j]): tags.add("eye")
            if pitched:        tags.add("pitch")
            runs.append((i / FPS, (j - 1) / FPS, "+".join(sorted(tags))))
        if n >= MIN_RUN and not (n >= MIN_SUSTAIN or pitched):
            blinks.append((i / FPS, (j - 1) / FPS))
        i = j
    else: i += 1

merged = []
for a, b, _ in runs:
    a, b = max(0.0, a - PAD), min(DUR, b + PAD)
    if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])

safe, cur = [], 0.0
for a, b in merged:
    if a - cur >= MIN_WIN: safe.append([round(cur, 2), round(a, 2)])
    cur = b
if DUR - cur >= MIN_WIN: safe.append([round(cur, 2), round(DUR, 2)])

# Frames the detector scores as camera but which reading the stills proves are not.
# Both are inside W08 and both are eyes-down glances at notes with the head level and
# the lids still wide, so eye-openness (.34) and contour aspect (1.03-1.08) are both
# clean — see the docstring. Round 1 shipped these same frames (its W06 117.30-123.10
# maps here through the splice) and they were not flagged, but a verified down-look has
# no business sitting inside a safe window on a client whose one hard rule this is.
MANUAL_EXCLUDE = [(113.6, 114.8), (116.8, 117.6)]
for xa, xb in MANUAL_EXCLUDE:
    out = []
    for a, b in safe:
        if xb <= a or xa >= b: out.append([a, b]); continue
        if a < xa: out.append([a, round(xa, 2)])
        if xb < b: out.append([round(xb, 2), b])
    safe = out
safe = [w for w in safe if w[1] - w[0] >= MIN_WIN]

tot = sum(b - a for a, b in safe)
byeye   = sum(1 for _,_,t in runs if t == "eye")
bypitch = sum(1 for _,_,t in runs if t == "pitch")
print(f"duration {DUR:.1f}s · down-look runs {len(runs)} "
      f"(eye-only {byeye} · pitch-only {bypitch} · both {len(runs)-byeye-bypitch})")
print(f"blink-shaped runs (kept; BLINK_REJECT={BLINK_REJECT}): {len(blinks)}  " +
      " ".join(f"{a:.1f}-{b:.1f}" for a, b in blinks))
print(f"face-safe windows {len(safe)} · total {tot:.1f}s = {100*tot/DUR:.1f}% of runtime\n")
for k, (a, b) in enumerate(safe, 1):
    print(f"  W{k:02d}  {a:7.2f} → {b:7.2f}   ({b-a:5.2f}s)")

json.dump({"fps": FPS, "eye_t": EYE_T, "aspect_t": ASPECT_T, "pad": PAD,
           "min_win": MIN_WIN, "min_sustain": MIN_SUSTAIN, "duration": DUR, "safe": safe,
           "down_runs": [[round(a,2), round(b,2), t] for a,b,t in runs],
           "rejected_blinks": [[round(a,2), round(b,2)] for a,b in blinks]},
          open("face-safe-windows.json", "w"), indent=1)
