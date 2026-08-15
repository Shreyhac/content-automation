#!/usr/bin/env python3
"""Emit out/vid46-final.srt from the SAME caption source the burned-in text uses.

build_captions.py groups the word stream into clips per chunk; this walks the whole
film in one pass with the identical grouping and correction rules, so the uploaded
caption track and the burned text can never disagree. Hand-writing the SRT is how
they drift.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_captions as bc  # noqa: E402  (path set above)

DURATION = 6702 / 30.0


def ts(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:            # rounding can carry into the next second
        s += 1
        ms = 0
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def strip(html):
    return html.replace("<b>", "").replace("</b>", "") \
               .replace("<i>", "").replace("</i>", "") \
               .replace("&#x27;", "'").replace("&amp;", "&") \
               .replace("&lt;", "<").replace("&gt;", ">")


def main():
    words = bc.fix_word_stream([w for w in bc.WORDS if w["start"] < DURATION])
    groups = bc.group(words)

    out, n = [], 0
    for i, cur in enumerate(groups):
        st, en = cur[0]["start"], cur[-1]["end"]
        # clamp each cue's tail to the next cue's start so no two ever overlap
        if i + 1 < len(groups):
            en = min(en + 0.14, groups[i + 1][0]["start"] - 0.02)
        en = min(en, DURATION)
        if en - st < 0.10:
            continue
        n += 1
        out.append("%d\n%s --> %s\n%s\n" % (n, ts(st), ts(en), strip(bc.render(cur))))

    path = os.path.abspath(os.path.join(HERE, "..", "out", "vid46-final.srt"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write("\n".join(out))
    print("wrote %s, %d cues, last ends %s" % (path, n, ts(en)))


if __name__ == "__main__":
    main()
