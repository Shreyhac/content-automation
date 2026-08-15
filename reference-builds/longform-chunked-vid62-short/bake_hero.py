#!/usr/bin/env python3
"""Bake the short's A-roll: eight beats, two cameras, frame-exact.

TWO BAKES, NOT ONE — AND THAT IS A CHANGE FROM vid58
----------------------------------------------------
vid58's short had three states off ONE bake, because its close was a pushed-in
full-width panel that had to be able to TWEEN out of the band. vid59's close is a
genuine full-bleed 9:16 crop of the source — b7's own 34 samples put his chin at
canvas y1465 against the y1600 band, where the whole take says y1538 — so it is its
own shot, cut to on a hard cut, and it shares nothing with the band camera.

  BAND / CARD   scale the source by 0.460315, crop 1080x760 -> #faceCam, scale(1)
                BAND is the full width of that crop; CARD is the same pixels clipped
                to x260-820. ONE camera, so his head cannot change size between them
                and the change is a WIDEN rather than a resize.
  CLOSE         crop 1215x2160 of the source, lanczos to 1080x1920. Its own element.

Baking the band at exactly its delivered scale (k=1) means the picture is resampled
once. vid58 baked at the larger of its two scales and let CSS scale down, which was
forced by the shared file and is no longer.

WHICH FILE IS THE SOURCE
------------------------
`vid59/aroll-cut.mov` — the CUT master, 351.893s, because short-beats.json is timed
against it. The scaffold arrived pointing at
"/Volumes/EXTERNAL/client new video/raw/Incogni Video 3.mov", which is 399.8s and is
**vid58's take**: a stale path that still resolves to a real 4K file of the same man
in the same chair. vid59's raw is "Incogni Video 4.mov" (370.3s), and it is not
wanted here anyway — cutting from the raw would need every beat mapped back across
the two removed retake spans.

The cut master is 43.9 Mbps, so nothing is lost by going through it.

WHY THE FRAMING IS PER-BEAT HORIZONTALLY AND CONSTANT VERTICALLY
----------------------------------------------------------------
crop_x is a per-beat CONSTANT centred on that beat's own median head position — never
a tracking tween, because a smoothed follow reads as a glitch (vid46 round 2, the
owner's "why is the presenter's frame always moving left-right"). crop_y puts his crown on
the same bake row in every band beat, which is what lets one state transform serve
all seven without his head jumping between cuts.

FRAME-EXACT, PER BEAT
---------------------
Each beat's duration is snapped to a whole number of frames at 24000/1001 and the cut
is made on that count, so the eight clips sum to the composition's frame total
exactly. vid44 shipped +4.1s of drift because nobody asserted this.
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
V59 = os.path.abspath(os.path.join(HERE, "..", "vid59"))
SRC = os.path.join(V59, "aroll-cut.mov")
FPS_N, FPS_D = 24000, 1001
SRC_W, SRC_H = 3840, 2160

T = json.load(open(os.path.join(V59, "short-transforms2.json")))
BEATS = json.load(open(os.path.join(V59, "short-beats.json")))

os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)


def frames(d):
    return int(round(d * FPS_N / FPS_D))


def main():
    if not os.path.exists(SRC):
        raise SystemExit("cut master missing: %s" % SRC)
    plan, total, t = [], 0, 0.0
    for i, b in enumerate(BEATS, 1):
        rec = T["beats"][i - 1]
        n = frames(b["b"] - b["a"])
        d = n * FPS_D / FPS_N
        plan.append({"i": i, "id": b["id"], "a": b["a"], "n": n, "dur": round(d, 6),
                     "t": round(t, 6), "why": b["why"], "state": rec["state"],
                     "crop_x": rec["crop_x"], "crop_y": rec["crop_y"],
                     "crop_w": rec["crop_w"], "crop_h": rec["crop_h"],
                     "s": rec["s"]})
        total += n
        t += d
    print("%d beats, %d frames, %.4fs" % (len(plan), total, total * FPS_D / FPS_N))

    for p in plan:
        dst = os.path.join(HERE, "assets", "%s.mp4" % p["id"])
        if p["state"] == "close":
            # crop THEN scale: the close is a crop of the frame, not a crop of a
            # resampled frame, and doing it in this order keeps every source row
            if p["crop_x"] + p["crop_w"] > SRC_W:
                raise SystemExit("!! %s crop runs outside the source" % p["id"])
            vf = ("crop=%d:%d:%d:%d,scale=1080:1920:flags=lanczos"
                  % (p["crop_w"], p["crop_h"], p["crop_x"], p["crop_y"]))
        else:
            sw, sh = round(SRC_W * p["s"]), round(SRC_H * p["s"])
            if p["crop_x"] + p["crop_w"] > sw or p["crop_y"] + p["crop_h"] > sh:
                raise SystemExit("!! %s crop runs outside the scaled source" % p["id"])
            # scale FIRST, then crop: the transform is solved in source pixels, so it
            # has to be applied before anything is cut away.
            vf = ("scale=%d:%d:flags=lanczos,crop=%d:%d:%d:%d"
                  % (sw, sh, p["crop_w"], p["crop_h"], p["crop_x"], p["crop_y"]))
        # NO grade, NO curve, NO saturation touch — his footage ships as shot.
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error",
                        "-ss", "%.6f" % p["a"], "-i", SRC,
                        "-frames:v", str(p["n"]), "-vf", vf, "-an",
                        "-r", "%d/%d" % (FPS_N, FPS_D),
                        "-c:v", "libx264", "-crf", "15", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-g", "12", "-keyint_min", "12",
                        dst], check=True)
        got = subprocess.run(["ffprobe", "-v", "error", "-count_frames",
                              "-select_streams", "v", "-show_entries",
                              "stream=nb_read_frames,width,height", "-of", "csv=p=0",
                              dst], capture_output=True, text=True).stdout.strip()
        n_got = int(got.split(",")[-1])
        p["frames_actual"] = n_got
        print("  %-3s %7.2f  %4d frames  %-11s crop %4d,%4d  %-6s %-40s %s"
              % (p["id"], p["a"], n_got, got.rsplit(",", 1)[0], p["crop_x"],
                 p["crop_y"], p["state"], p["why"][:40],
                 "ok" if n_got == p["n"] else "!! WANT %d" % p["n"]))

    bad = [p for p in plan if p["frames_actual"] != p["n"]]
    json.dump({"fps": FPS_N / FPS_D, "total_frames": total,
               "duration": round(total * FPS_D / FPS_N, 6),
               "bake": T["bake"], "close_bake": T["close_bake"],
               "states": T["states"], "zones": T["zones"], "beats": plan},
              open(os.path.join(HERE, "beats.json"), "w"), indent=1)
    if bad:
        raise SystemExit("!! %d beat(s) came out the wrong length" % len(bad))
    print("\nwrote beats.json — %d frames total, %.6fs"
          % (total, total * FPS_D / FPS_N))


if __name__ == "__main__":
    main()
