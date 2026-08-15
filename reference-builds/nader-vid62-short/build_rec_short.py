#!/usr/bin/env python3
"""Cut the short's two Incogni dashboard placements, and write the manifest pii_guard
reads.

usage: python3 build_rec_short.py

THE CLIENT ASK, AND THE TRAP INSIDE IT
--------------------------------------
Nader: "Add more clips of Incogni dashboard throughout the videos." Two placements in
a 47-second short, and both of them CORROBORATE the line they sit under:

  b3b  the request-status strip — Request processed Jul 16, 2026 -> Next removal
       Oct 14, 2026. That is 90 days to the day, which is exactly the private-broker
       cadence he states in the same sentence.
  b4   the activity log scrolling — named brokers, each "has completed our removal
       request", under "they've processed over 245 million removal requests".

NOT the broker-overview panel, which the long-form uses at c8. It reads "37 brokers
covered" — his own account's count — and the short's b2 claims "over 420 unique data
brokers". On screen together, twenty seconds apart, that is a viewer's contradiction.

THE LONG-FORM'S CROPS DO NOT WORK HERE AND THE REASON IS ARITHMETIC
------------------------------------------------------------------
Those are framed for a 3840-wide delivery. This short is 1080 wide and its graphics
zone is 890, so the c8 strip's 2676 source px would land at 0.33x and its 24px labels
would render at 8px. Every crop here is re-solved to put source text at >=0.7x:
1620 -> 890 for the strip (15px labels), 1220 -> 890 for the log (17px).

Cropping tighter is also what keeps the strip SAFE: the full-width version reaches
down past "Data removed" and the first personal value line.

MOTION IS MEASURED, NOT ASSUMED
-------------------------------
vid59's long-form shipped six "screen recordings" that were all stills. The activity
log's in-points come from a motion survey of the source (0.4s sampling, mean |diff|
of a 445px-wide luma reduction): it scrolls 4.4-7.7 and 10.8-14.0 and is otherwise
parked. b4's card therefore carries TWO clips back to back rather than one clip and
2.2s of a frozen list — and it carries them back to back rather than letting the card
outlive its clip, which renders as an empty bordered rectangle.

The strip is the exception and it is deliberate: pii_guard REFUSES a moving crop
inside the expanded-row window, because a page that scrolls 200px mid-clip puts a
stranger's home address into a crop that measured safe on frame 0. Its motion comes
from the graphic drawn over it, not from the recording.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRCDIR = "/Volumes/Shreyansh/nader new video/screen recordings"
REC2 = "Incogni Dashboard 2 - Completed Removal Requests.mov"

# out = (890 x h). h is derived from the crop so nothing is squeezed, and rounded to
# an even number of rows for yuv420p.
PLACEMENTS = {
    "b3b-resubmit": dict(
        src=REC2, ss=28.70, dur=2.30, crop=[1700, 1356, 1620, 208],
        beat="b3b @23.29  'and every 90 days for private, non-public brokers'",
        shows="the request-status strip, right half: Request processed Jul 16, 2026 -> "
              "Next removal Oct 14, 2026. Bottom row of pixels is y1564, which is 36px "
              "above the 'Data removed' heading and 167px above the first personal "
              "value. STATIC on purpose.",
        static=True),
    "b4-log-a": dict(
        src=REC2, ss=4.40, dur=3.240, crop=[560, 700, 1220, 348],
        beat="b4 @25.48  'and they've processed over 245 million removal requests'",
        shows="the activity log SCROLLING: named brokers, each 'has completed our "
              "removal request'. Measured motion across the whole window.",
        static=False),
    "b4-log-b": dict(
        src=REC2, ss=11.00, dur=2.224, crop=[560, 700, 1220, 348],
        beat="b4 @28.72  (second half of the same card — the list keeps scrolling)",
        shows="the same crop, the recording's second scroll run. The card carries two "
              "clips because the source parks between 7.7 and 10.8 and a card that "
              "outlives its clip renders as an empty bordered rectangle.",
        static=False),
}
OUT_W = 890


def main():
    if not os.path.isdir(SRCDIR):
        raise SystemExit("screen recordings not mounted: %s" % SRCDIR)
    os.makedirs(os.path.join(HERE, "assets", "rec"), exist_ok=True)
    man = {}
    for pid, c in sorted(PLACEMENTS.items()):
        src = os.path.join(SRCDIR, c["src"])
        if not os.path.exists(src):
            raise SystemExit("missing source: %s" % src)
        x, y, w, h = c["crop"]
        oh = int(round(h * OUT_W / float(w) / 2)) * 2
        rel = "assets/rec/%s.mp4" % pid
        dst = os.path.join(HERE, rel)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error",
                        "-ss", "%.4f" % c["ss"], "-i", src, "-t", "%.4f" % c["dur"],
                        "-vf", "crop=%d:%d:%d:%d,scale=%d:%d:flags=lanczos"
                        % (w, h, x, y, OUT_W, oh),
                        "-an", "-r", "24000/1001",
                        "-c:v", "libx264", "-crf", "15", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-g", "12", "-keyint_min", "12",
                        dst], check=True)
        got = subprocess.run(["ffprobe", "-v", "error", "-count_frames",
                              "-select_streams", "v", "-show_entries",
                              "stream=nb_read_frames,width,height,duration",
                              "-of", "csv=p=0", dst],
                             capture_output=True, text=True).stdout.strip()
        man[pid] = dict(id=pid, file=rel, **{k: c[k] for k in
                        ("src", "ss", "dur", "crop", "beat", "shows", "static")})
        man[pid]["out"] = [OUT_W, oh]
        man[pid]["scale"] = round(OUT_W / float(w), 4)
        print("  %-14s %s   crop %dx%d @%d,%d -> %dx%d (%.3fx)  bottom row y%d"
              % (pid, got, w, h, x, y, OUT_W, oh, OUT_W / float(w), y + h))
    json.dump(man, open(os.path.join(HERE, "rec-placements.json"), "w"), indent=1)
    print("\nwrote rec-placements.json — run pii_guard.py before composing")


if __name__ == "__main__":
    sys.exit(main())
