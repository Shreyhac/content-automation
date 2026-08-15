#!/usr/bin/env python3
"""The short's copy of the long-form privacy gate, pointed at the short's placements.

usage: python3 pii_guard.py

The gate itself is `hf59/pii_guard.py` and is not duplicated here — the measurement of
WHEN the expanded row is on screen, the geometry test and the scroll test are the same
three questions and re-typing them is how one copy drifts from the other. This file
re-points its module globals at hf59s and adds one test the long-form does not need:

  A CLIP DECLARED STATIC MUST ACTUALLY BE STATIC. The b3b strip sits inside the
  expanded-row window, 36px above a real person's name and 167px above their home
  address, and it is safe only because the page does not move under the crop. The
  long-form's gate already refuses a crop that scrolls; this also refuses one that
  was declared static and is not, measured on the BUILT clip rather than on the
  source, because the built clip is what ships.

Recording 2 shows, in legible 4K, a real full name, a real email address and a full
street address. This film is about data brokers publishing people's home addresses.
A gate that silently no-ops when the drive is absent is worse than no gate, so this
fails rather than skips — that behaviour is inherited, not re-implemented.
"""
import os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "hf59")))
import pii_guard as G  # noqa: E402

G.HERE = HERE
G.PLACEMENTS = os.path.join(HERE, "rec-placements.json")

STATIC_MAX = 0.30       # mean |frame diff| in 8-bit levels over a "static" clip


def static_check():
    import json
    P = json.load(open(G.PLACEMENTS))
    ok = True
    print("\nDECLARED-STATIC CLIPS — measured on the BUILT file:\n")
    for pid, c in sorted(P.items()):
        if not c.get("static"):
            continue
        f = os.path.join(HERE, c["file"])
        w, h = c["out"]
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf",
                            "format=gray,scale=%d:%d" % (w // 4, h // 4),
                            "-f", "rawvideo", "-"], capture_output=True)
        n = (w // 4) * (h // 4)
        fr = [np.frombuffer(r.stdout[i * n:(i + 1) * n], np.uint8).astype(np.float32)
              for i in range(len(r.stdout) // n)]
        d = max((float(np.abs(fr[i] - fr[0]).mean()) for i in range(1, len(fr))),
                default=0.0)
        bad = d > STATIC_MAX
        ok = ok and not bad
        print("   %-14s %3d frames   worst mean|diff| vs frame 0 = %.3f   %s"
              % (pid, len(fr), d, "<<< NOT STATIC" if bad else "static"))
    return ok


if __name__ == "__main__":
    rc = G.main()
    sys.exit(1 if (rc or not static_check()) else 0)
