#!/usr/bin/env python3
"""Build the burned-in caption clips and the SRT from the short's own words.json.

One source, two outputs, so the burned text and the sidecar SRT can never disagree.

Rules learned on the film:
  - A clip NEVER spans a beat boundary. The cut is a hard visual change; a caption
    that straddles it reads as a mistake.
  - A caption's POSITION follows the beat's mode. On SPLIT beats the face card owns
    y838-1574, so the caption moves up into the gap at y690-826 (class `hi`) - the
    same place vid39 puts it on its split beats. Anywhere else it sits low at
    y1396. Leaving it low on a split beat would print it on his jaw, which is the
    exact defect v1 was rejected for.
  - Two lines max at 58px/1.2 in a 936px column, so a clip is capped by MEASURED
    width, not by word count. Width is estimated from a per-character table
    calibrated against DM Sans 800 - conservative on purpose.
  - Token repair already happened in build_vo.py (the CONT rule): "$7.99" and
    "third-party" arrive here as single tokens, and CODEWORD is spelled correctly.
  - Emphasis is data, not decoration: the brand and the audited figures get <b>,
    the winner-side words get <i>, the alert words get <s>. Nothing else.
  - NO EM DASHES anywhere (owner rule). Use "·" between labels, commas in prose.
"""
import json, re, html

W_COL = 936          # caption column width in px
FS = 58              # font-size
MAX_LINES = 2
MAX_HOLD = 2.10       # a clip never sits still longer than this
GAP = 0.06           # visual gap between consecutive clips

# per-character width factors for DM Sans 800 at 1em, measured off a render
NARROW = set("iljItf'.,:;!|()[]")
WIDE = set("MWmw@%")
def wpx(s):
    w = 0.0
    for ch in s:
        if ch in NARROW: w += 0.30
        elif ch in WIDE: w += 0.92
        elif ch.isupper() or ch.isdigit() or ch == "$": w += 0.66
        else: w += 0.545
    return w * FS

# Emphasis is DATA, not decoration, and the v2 cut only contains these:
#   <b> the brand and the audited figures on Incogni's side
#   <i> the winner-side words
#   <s> the alert word, used once
# 200 is deliberately NOT bold: Aura's figure is neutral everywhere in this film.
# "codeword" is the placeholder coupon: replace with the sponsor's real code, lowercased.
BOLD = {"incogni", "incogni's", "420", "420+", "codeword", "60%", "deloitte"}
ITAL = {"more", "ground"}
ALERT = {"twice"}

def mark(word):
    k = word.lower().strip(".,?!")
    esc = html.escape(word)
    if k in BOLD: return f"<b>{esc}</b>"
    if k in ALERT: return f"<s>{esc}</s>"
    if k in ITAL: return f"<i>{esc}</i>"
    return esc

def build(words, beats):
    """Group words into clips: never crossing a beat, never over two lines."""
    clips = []
    for b in beats:
        ws = [w for w in words if w["beat"] == b["n"]]
        if not ws: continue
        cur = []
        def flush():
            if not cur: return
            clips.append(dict(beat=b["n"], words=list(cur),
                              start=cur[0]["start"], end=cur[-1]["end"]))
            cur.clear()
        for w in ws:
            trial = cur + [w]
            text = " ".join(x["word"] for x in trial)
            # greedy line wrap at the column width
            lines, line = 1, 0.0
            for tok in text.split():
                tw = wpx(tok + " ")
                if line + tw > W_COL:
                    lines += 1; line = tw
                else:
                    line += tw
            # a clip also breaks on a sentence end, so punctuation drives rhythm
            if lines > MAX_LINES and cur:
                flush()
                cur.append(w)
            else:
                cur.append(w)
                # a clip also breaks on a sentence end and on time, so a caption is
                # never a wall of text sitting still: the film ran ~1.94s per cue.
                held = cur[-1]["end"] - cur[0]["start"]
                if (re.search(r"[.?!]$", w["word"]) and len(cur) >= 3) or held >= MAX_HOLD:
                    flush()
        flush()
    return clips


if __name__ == "__main__":
    from beats import resolve, chunk_of, FPS
    beats, total = resolve()
    words = json.load(open("words.json"))
    clips = build(words, beats)

    # ---- emit per-chunk caption HTML ------------------------------------------
    idx = {b["n"]: i for i, b in enumerate(beats)}
    per = {"s1": [], "s2": []}
    t0 = {b["n"]: 0.0 for b in beats}
    from beats import CHUNKS
    off = {}
    for name, lo, hi in CHUNKS:
        off[name] = beats[lo]["ta"]

    # GAP lets a clip breathe past its last word, but it must never run into the next
    # clip or past its own beat: two captions on screen at once reads as a bug, and a
    # caption surviving a hard cut reads as a worse one.
    # Snap every caption edge to a FRAME. Emitting 3-decimal seconds lets a rounded
    # duration land one thousandth past the next clip's start, which the static guard
    # rejects as overlapping_clips_same_track — and rightly: nothing can happen
    # between two frames anyway.
    q = lambda t: round(t * FPS) / FPS
    for i, c in enumerate(clips):
        b = beats[idx[c["beat"]]]
        nxt = clips[i + 1]["start"] if i + 1 < len(clips) else 1e9
        c["in"] = q(c["start"])
        c["out"] = q(min(c["end"] + GAP, b["tb"], nxt))
        if c["out"] <= c["in"]: c["out"] = c["in"] + 1 / FPS
    for i, c in enumerate(clips[:-1]):
        c["out"] = min(c["out"], clips[i + 1]["in"])

    # Round the two EDGES to 3dp, then derive the duration from the rounded pair.
    # Rounding start and duration independently is what let clip N print an end of
    # 21.334 against clip N+1's start of 21.333 even after frame-snapping.
    for i, c in enumerate(clips):
        ch = chunk_of(idx[c["beat"]])
        st = round(c["in"] - off[ch], 3)
        dur = round(c["out"] - off[ch], 3) - st
        txt = " ".join(mark(w["word"]) for w in c["words"])
        # NOT the loop variable `b` from the edge-rounding pass above: that one is
        # left pointing at the LAST beat, which silently put every caption low.
        cls = ("cap hi clip" if beats[idx[c["beat"]]].get("mode") == "SPLIT"
               else "cap clip")
        per[ch].append(
            f'  <div id="{ch}cap{len(per[ch])+1}" class="{cls}" '
            f'data-start="{st:.3f}" data-duration="{dur:.3f}" '
            f'data-track-index="9">{txt}</div>')

    for ch, rows in per.items():
        p = f"{ch}/index.html"
        s = open(p).read()
        new = "<!-- CAPTIONS -->\n" + "\n".join(rows) + "\n  <!-- /CAPTIONS -->"
        s = re.sub(r"<!-- CAPTIONS -->.*?<!-- /CAPTIONS -->", new, s, flags=re.S)
        open(p, "w").write(s)
        print(f"{ch}: {len(rows)} caption clips")

    # ---- emit the SRT ---------------------------------------------------------
    def ts(t):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    out = []
    for i, c in enumerate(clips, 1):
        txt = " ".join(w["word"] for w in c["words"])
        out.append(f"{i}\n{ts(c['in'])} --> {ts(c['out'])}\n{txt}\n")
    open("captions.srt", "w").write("\n".join(out))
    print(f"captions.srt: {len(clips)} cues")

    # ---- guard: no em dash anywhere, and every clip inside its beat -----------
    bad = [c for c in clips if "—" in " ".join(w["word"] for w in c["words"])]
    assert not bad, bad
    for i, c in enumerate(clips):
        b = beats[idx[c["beat"]]]
        assert b["ta"] - 2e-3 <= c["start"] and c["end"] <= b["tb"] + 2e-3, (c, b)
    print("guards passed: no em dashes, every clip inside its beat")
