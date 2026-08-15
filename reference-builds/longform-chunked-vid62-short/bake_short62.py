#!/usr/bin/env python3
"""Bake the short's A-roll — nine beats, one camera, frame-exact.

WHERE THE PICTURES COME FROM, AND WHY IT IS NOT THE MASTER
-----------------------------------------------------------
vid59's short baked from one continuous file. vid62's raw master lives on
/Volumes/EXTERNAL, which is not mounted, and `vid62/master.mov` was deleted to free
space after the long-form shipped. What IS here is the long-form's own A-roll assets:
`hf62/assets/aroll/c1..c18.mp4`, 3840x2160 at 59.8 Mbps, each one an exact cut of the
master at the boundaries in `hf62/chunks.json`. They are the master, in eighteen
pieces, and nothing is lost by going through them.

Every beat was checked against those boundaries before this file was written and NOT
ONE straddles a join, so each bake is a single seek into a single chunk:

    local_in = beat.a - chunks[beat.chunk].t0

If a beat ever did straddle a join this script raises rather than silently baking the
wrong side of it.

ONE BAKE, TWO STATES — unchanged from vid59
-------------------------------------------
BAND and CARD are the same 1080x760 bake at s=0.42446 (solved from his own crown and
chin over the spans he is VISIBLE in), placed by one transform and differing only by
clip-path, so his head is the same size in both and the change between them is a
widen. There is no CLOSE bake: solve_short62.py rules a full-bleed 9:16 crop out on
this take's own numbers and prints them.

b6 gets no clip at all — the picture is off for the whole beat because he is reading
for the whole beat — so it is absent here rather than baked and hidden.

NO GRADE. No curve, no eq, no saturation touch. His footage ships as shot.
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
V62 = os.path.join(ROOT, "vid62")
AROLL = os.path.join(ROOT, "hf62", "assets", "aroll")
FPS_N, FPS_D = 24000, 1001
SRC_W, SRC_H = 3840, 2160

T = json.load(open(os.path.join(V62, "short-transforms.json")))
BEATS = json.load(open(os.path.join(V62, "short-beats.json")))
CHUNKS = {c["name"]: c for c in json.load(open(os.path.join(ROOT, "hf62",
                                                           "chunks.json")))["chunks"]}

os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)


def frames(d):
    return int(round(d * FPS_N / FPS_D))


def main():
    plan, total, t = [], 0, 0.0
    for i, b in enumerate(BEATS, 1):
        rec = next(r for r in T["beats"] if r["id"] == b["id"])
        c = CHUNKS[b["chunk"]]
        if b["a"] < c["t0"] - 1e-6 or b["b"] > c["t0"] + c["dur"] + 1e-6:
            raise SystemExit("!! %s (%.2f-%.2f) is not inside chunk %s (%.3f-%.3f)"
                             % (b["id"], b["a"], b["b"], b["chunk"], c["t0"],
                                c["t0"] + c["dur"]))
        n = frames(b["b"] - b["a"])
        d = n * FPS_D / FPS_N
        p = {"i": i, "id": b["id"], "a": b["a"], "n": n, "dur": round(d, 6),
             "t": round(t, 6), "why": b["why"], "says": b["says"],
             "state": rec["state"], "chunk": b["chunk"],
             "local_a": round(b["a"] - c["t0"], 6), "vis": b["vis"]}
        if rec["state"] != "noface":
            p.update({k: rec[k] for k in ("crop_x", "crop_y", "crop_w", "crop_h", "s")})
            # the visible spans, expressed on the SHORT's own timeline
            p["vis_t"] = [[round(t + (a - b["a"]), 6), round(t + (z - b["a"]), 6)]
                          for a, z in b["vis"]]
        else:
            p["vis_t"] = []
        plan.append(p)
        total += n
        t += d
    print("%d beats, %d frames, %.4fs" % (len(plan), total, total * FPS_D / FPS_N))

    for p in plan:
        if p["state"] == "noface":
            print("  %-3s %7.2f  %4d frames  %-30s  no clip (picture off all beat)"
                  % (p["id"], p["a"], p["n"], p["why"][:30]))
            continue
        src = os.path.join(AROLL, "%s.mp4" % p["chunk"])
        dst = os.path.join(HERE, "assets", "%s.mp4" % p["id"])
        if p["state"] == "closew":
            # CROP THEN SCALE for the full-width close: it is a crop of the frame,
            # not a crop of a resampled frame, and this order keeps every source row.
            if p["crop_x"] + p["crop_w"] > SRC_W:
                raise SystemExit("!! %s crop runs outside the source" % p["id"])
            vf = ("crop=%d:%d:%d:%d,scale=%d:%d:flags=lanczos"
                  % (p["crop_w"], p["crop_h"], p["crop_x"], p["crop_y"],
                     T["closew_bake"]["w"], T["closew_bake"]["h"]))
        else:
            sw, sh = round(SRC_W * p["s"]), round(SRC_H * p["s"])
            if p["crop_x"] + p["crop_w"] > sw or p["crop_y"] + p["crop_h"] > sh:
                raise SystemExit("!! %s crop runs outside the scaled source" % p["id"])
            # scale FIRST, then crop — the transform is solved in source pixels
            vf = ("scale=%d:%d:flags=lanczos,crop=%d:%d:%d:%d"
                  % (sw, sh, p["crop_w"], p["crop_h"], p["crop_x"], p["crop_y"]))
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error",
                        "-ss", "%.6f" % p["local_a"], "-i", src,
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
        print("  %-3s %7.2f  %4d frames  %-11s %s@%7.3f  crop %4d,%4d  %-5s %s"
              % (p["id"], p["a"], n_got, got.rsplit(",", 1)[0], p["chunk"],
                 p["local_a"], p["crop_x"], p["crop_y"], p["state"],
                 "ok" if n_got == p["n"] else "!! WANT %d" % p["n"]))

    bad = [p for p in plan if p.get("frames_actual", p["n"]) != p["n"]]
    json.dump({"fps": FPS_N / FPS_D, "total_frames": total,
               "duration": round(total * FPS_D / FPS_N, 6),
               "bake": T["bake"], "closew_bake": T["closew_bake"],
               "states": T["states"], "zones": T["zones"],
               "beats": plan},
              open(os.path.join(HERE, "beats.json"), "w"), indent=1)
    if bad:
        raise SystemExit("!! %d beat(s) came out the wrong length" % len(bad))
    print("\nwrote beats.json — %d frames total, %.6fs"
          % (total, total * FPS_D / FPS_N))


if __name__ == "__main__":
    main()
