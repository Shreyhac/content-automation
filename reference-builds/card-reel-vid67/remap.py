"""Map reference shot boundaries onto the presenter's delivery, word by word.

The two scripts are the same words (the presenter recorded the reference transcript
verbatim), so the honest way to re-time a 39.5s shot list onto a 35.2s take is
not a linear squeeze — it is: for each reference cut, find the word being
spoken, then place the cut on THAT word's onset in the presenter's take.

Whisper mishears a few tokens in both files ("Cloud Code", "A&N"), so the
alignment is a difflib match on normalised words, not an index zip.
"""
import json, re, difflib, sys

def words(path):
    d = json.load(open(path))
    out = []
    for seg in d["segments"]:
        for w in seg.get("words", []):
            t = re.sub(r"[^a-z0-9]", "", w["word"].lower())
            if t:
                out.append((t, float(w["start"]), float(w["end"]), w["word"].strip()))
    return out

REF = words("/private/tmp/reel-factory-scratch/ref3/refaudio.json")
TAKE = words("hf67/transcript.json")
print(f"ref {len(REF)} words ({REF[-1][2]:.2f}s)   take {len(TAKE)} words ({TAKE[-1][2]:.2f}s)")

sm = difflib.SequenceMatcher(None, [w[0] for w in REF], [w[0] for w in TAKE], autojunk=False)
pairs = []                      # (ref_onset, take_onset, word)
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        pairs.append((REF[a+k][1], TAKE[b+k][1], REF[a+k][3]))
pairs.sort()
print(f"{len(pairs)} anchored words of {len(REF)}")

def remap(rt):
    """reference time -> take time, piecewise-linear between anchored words"""
    if rt <= pairs[0][0]:
        return max(0.0, rt * (pairs[0][1] / pairs[0][0]) if pairs[0][0] > 0 else rt)
    if rt >= pairs[-1][0]:
        # tail: hold the last local rate
        r0, h0, _ = pairs[-2]; r1, h1, _ = pairs[-1]
        rate = (h1 - h0) / (r1 - r0) if r1 > r0 else 1.0
        return h1 + (rt - r1) * rate
    for i in range(len(pairs) - 1):
        r0, h0, _ = pairs[i]; r1, h1, _ = pairs[i+1]
        if r0 <= rt <= r1:
            f = 0.0 if r1 == r0 else (rt - r0) / (r1 - r0)
            return h0 + f * (h1 - h0)
    return rt

def snap(t):
    """land the cut on the nearest word onset in THE TAKE (within 0.18s)"""
    best, bd = t, 9e9
    for w in TAKE:
        d = abs(w[1] - t)
        if d < bd:
            bd, best = d, w[1]
    return (best, bd) if bd <= 0.18 else (t, bd)

# the reference's own cuts, from top-region scene detection + the sub-shots the
# detector merges (progressive typing reads as one shot to a scene detector)
REF_CUTS = [0.000, 1.150, 2.300, 3.600, 5.100, 6.567, 8.000, 9.333, 10.400,
            11.300, 12.400, 13.633, 15.100, 15.967, 17.500, 19.367, 20.067,
            21.200, 22.300, 23.400, 24.900, 26.300, 27.200, 28.267, 30.800,
            32.067, 34.300, 36.600]

print(f"\n{'ref':>7} {'->take':>7} {'snapped':>8} {'d':>6}  word at that moment")
rows = []
for rc in REF_CUTS:
    ht = remap(rc)
    st, d = snap(ht)
    near = min(TAKE, key=lambda w: abs(w[1] - st))
    rows.append((rc, ht, st))
    print(f"{rc:7.3f} {ht:7.3f} {st:8.3f} {d:6.3f}  {near[3]!r}")

json.dump([{"ref": a, "his": round(c, 3)} for a, b, c in rows],
          open("vid67/shotmap.json", "w"), indent=1)
print("\n-> vid67/shotmap.json")
