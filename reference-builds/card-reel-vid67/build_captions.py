#!/usr/bin/env python3
"""Word-level caption chunks in the reference's cadence.

The reference changes its caption 1-4 words at a time, roughly every 0.4s, and
that sticker rhythm is part of the edit being copied — a phrase-bar engine would
be a different film. Chunks are built from THE TAKE'S word onsets so every change lands
on a word, never on a timer.

Rules that come from past rounds:
  - a word belongs to exactly ONE chunk, keyed on its onset
  - a chunk never straddles a scene cut: the cut gets a fresh caption, so the
    picture and the words change together
  - max 4 words and max 26 characters, so the pill stays one line at 44px in a
    1080-wide stage (a wrapped pill grows downward into the presenter's crown)
  - a chunk never starts a new sentence mid-pill: "to start. This" reads as one
    thought and is two
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAXW, MAXC, MAXDUR = 4, 26, 0.62

tj = json.load(open(os.path.join(ROOT, "hf67", "transcript.json")))
words = []
for seg in tj["segments"]:
    for w in seg.get("words", []):
        t = w["word"].strip()
        if t:
            words.append((float(w["start"]), float(w["end"]), t))
words.sort()

cuts = sorted(r["his"][0] for r in json.load(open(os.path.join(HERE, "shots.json"))))
def crosses(a, b):
    return any(a < c < b for c in cuts)

chunks, cur = [], []
def flush():
    global cur
    if cur:
        txt = " ".join(w[2] for w in cur)
        txt = re.sub(r"\s+([,.!?])", r"\1", txt)
        chunks.append((round(cur[0][0], 3), txt))
        cur = []

for w in words:
    if cur:
        nxt = cur + [w]
        txt = " ".join(x[2] for x in nxt)
        if (len(nxt) > MAXW or len(txt) > MAXC
                or (w[1] - cur[0][0]) > MAXDUR
                or crosses(cur[0][0], w[0])
                or cur[-1][2].rstrip().endswith((".", "?", "!"))):
            flush()
    cur.append(w)
flush()

# every chunk must be visible for at least 4 frames
out = []
for i, (t, txt) in enumerate(chunks):
    end = chunks[i+1][0] if i+1 < len(chunks) else 35.233
    if end - t < 0.133 and out:
        out[-1] = (out[-1][0], out[-1][1] + " " + txt)
        continue
    out.append((t, txt))

print(f"{len(out)} caption chunks over {35.233:.2f}s "
      f"(one every {35.233/len(out):.2f}s; the reference averages 0.76s)")
longest = max(out, key=lambda c: len(c[1]))
print(f"longest: {len(longest[1])} chars  {longest[1]!r}")
js = "var CAPS = [\n" + "".join(
    '  [%6.3f, %s],\n' % (t, json.dumps(txt)) for t, txt in out) + "];\n"
open(os.path.join(HERE, "captions.js"), "w").write(js)
print("-> vid67/captions.js")
for t, txt in out[:8]: print(f"   {t:6.3f}  {txt}")
