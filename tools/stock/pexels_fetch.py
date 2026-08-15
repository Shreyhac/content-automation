#!/usr/bin/env python3
"""Download the six shortlisted Pexels clips, grade them to Signal Blue, and
re-encode for HyperFrames.

One cut per act, each chosen because it illustrates the line it plays under,
b-roll that does not connect to the claim is worse than no b-roll (the vid39 rule).

Grade: desaturate, cool the mids/highs, crush the blacks so the footage sits INSIDE
the near-black ground instead of punching a bright hole in it. Encoded with
-g 30 -keyint_min 30 (the compiler warns about sparse keyframes and it means it)
and no audio, the film's only voice is the VO master.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "broll", "raw")
DEST = os.path.abspath(os.path.join(HERE, "..", "hf46", "assets", "broll"))
os.makedirs(RAW, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# name        id          in-point  length  the line it plays under
# ROUND 2 replacements, decided by reading round 1's six graded midframes rather than
# by re-searching. The owner's "b-roll is very less and too shitty" is fair on three:
#   brokers 7140928  out of focus with a double-exposure ghost -> 7140931 (the same
#                    rack shot, sharp), plus 32386520 as a second angle
#   bundle  36036732 a laptop showing a generic Windows desktop full of icons. Says
#                    nothing about a security bundle -> 7988267
#   pricing 7534264  anonymous hands on a keyboard; nothing to do with price
#                    -> 7534262, a card in hand under blue rim light, already in
#                    palette before any grading
# buyers / collect / outro keep their ids, those concepts were right and the GRADE
# was what made them look cheap. "More" is served by 3 extra cuts (aisle, cubes,
# terminal) so the film has 9 rather than 6.
PICKS = [
    # name        id          in    len   the line it plays under
    # ROUND 2b: lengths are cut to cover the FULL on-screen window of the .bcard that
    # holds them, plus headroom. A .bcard is an untimed wrapper around a timed <video>,
    # so when the clip runs out the video hides and the card is left on screen as an
    # empty bordered box, c4 had 6 seconds of that before this pass.
    ("buyers",   "8865881", 2.0, 10.0),  # c2 "...marketers, government agencies, even scammers"
    ("collect",  "7568745", 1.0, 12.0),  # c2 "every time you buy something online"
    ("brokers",  "7140931", 0.5,  8.5),  # c3 "420+ data broker websites and private databases"
    ("aisle",   "32386520", 1.0,  9.5),  # c3 second angle - "and private databases"
    ("cubes",   "34719182", 0.5,  9.0),  # c4 tail - "identity and credit monitoring"
    ("bundle",   "7988267", 1.0,  5.6),  # c4 "don't you already have a VPN, a password manager"
    ("pricing",  "7534262", 0.5, 13.0),  # c6 "what each one actually costs"
    ("terminal", "8465178", 1.0, 10.0),  # c6 "$12 a month for annual billing"
    ("outro",   "37677782", 1.5,  8.4),  # c8 "your data is already out there"
]

# ROUND 2: keep the cool push and the black lift, both are needed so a cut sits
# INSIDE the near-black ground instead of punching a bright hole in it, but stop
# crushing. Round 1 ran saturation .58 / brightness -.045 / mid 0.47 and THEN .bcard
# laid a .55 vignette over the top, so the footage arrived murky and read as low
# quality even where the source was fine.
GRADE = (
    "scale=2560:-2:flags=lanczos,crop=2560:1440,"
    "eq=saturation=0.70:contrast=1.08:brightness=-0.012:gamma=0.99,"
    "colorbalance=rs=-0.06:gs=-0.02:bs=0.15:rm=-0.04:gm=-0.01:bm=0.10:"
    "rh=-0.03:bh=0.06,"
    "curves=all='0/0.015 0.5/0.50 1/0.98'"
)


def run(cmd, **kw):
    return subprocess.run(cmd, check=False, capture_output=True, text=True, **kw)


def main():
    for name, vid, ss, dur in PICKS:
        src = os.path.join(RAW, "%s_%s.mp4" % (name, vid))
        if not (os.path.exists(src) and os.path.getsize(src) > 200000):
            url = "https://www.pexels.com/download/video/%s/" % vid
            print("get  %-8s id=%-9s" % (name, vid), flush=True)
            run(["curl", "-sL", "-A", UA, "-o", src, url])
        sz = os.path.getsize(src) if os.path.exists(src) else 0
        if sz < 200000:
            print("  !! %s download failed (%d bytes)" % (name, sz), flush=True)
            continue
        out = os.path.join(DEST, "%s.mp4" % name)
        r = run(["ffmpeg", "-y", "-nostdin", "-ss", str(ss), "-i", src, "-t", str(dur),
                 "-vf", GRADE, "-an", "-r", "30",
                 "-c:v", "libx264", "-crf", "19", "-preset", "medium",
                 "-pix_fmt", "yuv420p", "-g", "30", "-keyint_min", "30",
                 out])
        if r.returncode:
            print("  !! encode %s: %s" % (name, r.stderr[-400:]), flush=True)
            continue
        print("  ok %-8s %5.1f MB raw -> %5.2f MB graded"
              % (name, sz / 1e6, os.path.getsize(out) / 1e6), flush=True)


if __name__ == "__main__":
    main()
