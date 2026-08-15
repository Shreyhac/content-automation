"""benchmark.py, the quality bar as arithmetic.

`docs/03-quality-bar.md` is the bar in prose. It is good prose and it needs three
to twelve review rounds against a real person's reactions to become judgement.
A new operator does not have those rounds. This script is the half of the bar
that does not need them: every number in `benchmarks.json` is one a film was
rejected or accepted on, and this measures a delivered file against them.

It measures the DELIVERED FILE, which is the only artefact the owner and the
clients ever see. Everything upstream (lint, validate, `tools/gates/guard.py`,
the shoot sheet) reads the composition and can pass while the file that ships is
wrong. Three concrete cases this catches that nothing upstream did:

  * vid60 shipped 2160x3840 from a 2160x3840 master at 15.5 Mbps against the
    master's 28.0, and drew "it is very much compressed". Resolution is not
    quality and no structural gate has an opinion about a data rate.
  * vid62's short shipped with 9.1s of literally frozen pixels, longest run
    1.7s, against a grammar rule that has said "nothing static over about 1
    second" since vid2.
  * Ten-plus caption packs and two SRTs shipped with em dashes against a
    standing no-em-dash rule on all four accounts, because the rule was only
    ever checked in the composition.

Usage
-----
    python3 tools/qa/benchmark.py out/vid67-final.mp4 --creator shreyansh \\
        --master hf67/assets/aroll.mp4 \\
        --srt out/vid67-final.srt --caption-pack out/vid67-caption.md

    python3 tools/qa/benchmark.py out/vid62-short.mp4 --creator nader \\
        --master-bitrate 32.78 --master-resolution 2160x3840

Exit code
---------
0 when every hard metric passed. 1 when any hard metric FAILED. 2 when the tool
could not run a check it was asked to run (missing ffprobe, unreadable file).
A WARN never changes the exit code: warnings are the metrics where the archive
records a target and also records a film that shipped past it with the owner's
approval. Read them, do not automate them away.

Dependencies
------------
ffprobe and ffmpeg are required. numpy is required for the motion and luma
passes (`--no-motion` skips them). Face presence needs `swift` and
`tools/vision/facebox.swift` and is skipped with `--no-face`.

What this CANNOT measure, and why it is not a substitute for `docs/09-self-review.md`
------------------------------------------------------------------------------------
Every rejection class in `docs/03-quality-bar.md` is invisible here. "Boring",
"cheap", "not premium", "too AI slopped" and "text on my face" are all judgements
about what is drawn, and a film can pass every number below and be rejected on
sight in under thirty seconds. This script only proves a cut is not broken.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DEFAULT_BENCHMARKS = os.path.join(HERE, "benchmarks.json")
FACEBOX = os.path.join(REPO, "tools", "vision", "facebox.swift")

EM_DASH = "\u2014"

PASS, WARN, FAIL, SKIP = "PASS", "WARN", "FAIL", "SKIP"


# ---------------------------------------------------------------- shell probes

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(binary):
    if shutil.which(binary) is None:
        sys.stderr.write("benchmark: %s is not on PATH. Run tools/check-env.sh.\n" % binary)
        sys.exit(2)


def probe(path):
    """Container and stream facts. ffprobe is the only source of truth for a
    delivered file: a render log's claimed settings and the file's actual
    parameters have disagreed before."""
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", path])
    if r.returncode != 0:
        sys.stderr.write("benchmark: ffprobe failed on %s\n%s\n" % (path, r.stderr))
        sys.exit(2)
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in d["streams"] if s.get("codec_type") == "audio"), None)
    if v is None:
        sys.stderr.write("benchmark: no video stream in %s\n" % path)
        sys.exit(2)
    fmt = d["format"]
    dur = float(fmt.get("duration") or v.get("duration") or 0)
    total_bps = float(fmt.get("bit_rate") or 0)
    vid_bps = float(v.get("bit_rate") or 0)
    if not vid_bps and dur:
        # Some containers carry no per-stream rate. Derive from bytes.
        vid_bps = float(fmt.get("size", 0)) * 8 / dur
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    return {
        "path": path,
        "width": int(v["width"]),
        "height": int(v["height"]),
        "fps": fps,
        "duration": dur,
        "video_mbps": vid_bps / 1e6,
        "total_mbps": (total_bps or vid_bps) / 1e6,
        "size_bytes": int(fmt.get("size", 0)),
        "vcodec": v.get("codec_name"),
        "acodec": a.get("codec_name") if a else None,
        "pix_fmt": v.get("pix_fmt"),
        "color_primaries": v.get("color_primaries"),
        "color_transfer": v.get("color_transfer"),
    }


def loudness(path):
    """Integrated LUFS and true peak from ffmpeg's ebur128 filter. Measured on
    the delivered file because an SFX-heavy mix lands quieter than the VO's own
    normalisation target: a VO cut to -16 came out at -16.7 integrated."""
    r = run(["ffmpeg", "-nostdin", "-hide_banner", "-i", path,
             "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr or ""
    tail = txt[-4000:]
    lufs = tp = lra = None
    m = re.search(r"^\s*I:\s*(-?[\d.]+) LUFS", tail, re.M)
    if m:
        lufs = float(m.group(1))
    m = re.search(r"Peak:\s*(-?[\d.]+) dBFS", tail)
    if m:
        tp = float(m.group(1))
    m = re.search(r"^\s*LRA:\s*(-?[\d.]+) LU", tail, re.M)
    if m:
        lra = float(m.group(1))
    return {"integrated_lufs": lufs, "true_peak_dbtp": tp, "lra": lra}


# ------------------------------------------------------------------- the video

def gray_frames(path, fps, width, height):
    """Decode the whole file once to small grayscale rawvideo. One decode pass
    feeds every pixel metric below. Never `-ss` before `-i` here: the point is
    an even sample of the real timeline, and seeking lands on a different frame
    per codec (a sharpness comparison built that way swung 69% to 274% and meant
    nothing)."""
    import numpy as np
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", path,
         "-vf", "fps=%g,scale=%d:%d" % (fps, width, height),
         "-pix_fmt", "gray", "-f", "rawvideo", "-"],
        capture_output=True)
    n = width * height
    usable = len(r.stdout) // n * n
    if usable == 0:
        return None
    return np.frombuffer(r.stdout[:usable], dtype="uint8").reshape(-1, height, width).astype("int16")


def scene_pass(path, duration, threshold=0.25):
    """Shot changes, from ffmpeg's own scene score.

    A grid-cell difference is the right tool for a frozen run and the wrong one
    for a cut: demi2's b-roll moves so hard that a cell threshold tuned to catch
    real cuts reported 218 of them in 37.8s, a 0.17s mean shot. A cut changes
    the WHOLE frame, which is what `scene` scores.

    0.25 is the value the archive already uses to tell "an edit I have to beat"
    from raw A-roll motion. It was checked both ways there: at 0.10 a vid58 scan
    reported three cuts, two of which were fast head movement.

    READ THE RESULT AS A FLOOR, NOT A COUNT. This is the least trustworthy number
    the script produces and no threshold fixes it. demi2's density comes from
    static crop-cuts of the same person against the same wall, which barely score
    as scene changes at all: its plan is 42 shots over 36.2s and the detector sees
    11 at 0.25, 16 at 0.10 and still only 19 at 0.06. The same sweep pushes vid63,
    whose 13 scenes the detector reads correctly as 10 at 0.25, up to 66 false
    cuts at 0.06. A threshold that is right for one grammar is wrong for the other.
    The shot count lives in the shot plan (`tools/aroll/beats.py`). Check it
    there; use this row to notice that a cut is nowhere near its plan."""
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "info", "-i", path,
         "-vf", "scale=320:-2,select='gt(scene,%g)',metadata=print:file=-" % threshold,
         "-f", "null", "-"], capture_output=True, text=True)
    times = [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stdout or "")]
    n = len(times)
    return {
        "shot_changes": n,
        "mean_shot_s": duration / (n + 1) if duration else None,
        "longest_shot_s": max(
            [b - a for a, b in zip([0.0] + times, times + [duration])] or [duration]),
        "scene_threshold": threshold,
    }


def motion_pass(frames, fps, grid=(6, 10), still=1.0):
    """Frozen runs, from the delivered pixels.

    The metric is the MAX GRID CELL's mean absolute difference, never the whole
    frame's. A whole-frame mean is the same mistake the contrast gate made: it
    averages a real local event down to nothing. A caption word changing inside
    a 4K frame moves about 0.3 on a whole-frame mean and about 15 on its own
    cell, and vid62's short reports 29% frozen on the frame mean against 15% on
    the cell max, which is the honest number.

    This differs from the composition-side `motion_guard` in `LEARNINGS` on
    purpose. That fingerprints the DOM (id, rect, opacity, transform) and is
    blind to a `<video>` whose box never changes while its picture does; this is
    blind to a graphic held still over a live A-roll. They catch different
    halves and neither replaces the other."""
    import numpy as np
    if frames is None or len(frames) < 3:
        return None
    d = np.abs(frames[1:] - frames[:-1])
    gy, gx = grid[1], grid[0]
    h, w = d.shape[1], d.shape[2]
    ch, cw = h // gy, w // gx
    cells = d[:, :ch * gy, :cw * gx].reshape(len(d), gy, ch, gx, cw).mean(axis=(2, 4))
    local = cells.max(axis=(1, 2))
    dt = 1.0 / fps

    frozen = local < still
    runs, start = [], None
    for i, v in enumerate(frozen):
        if v and start is None:
            start = i
        if not v and start is not None:
            runs.append((start * dt, (i - start) * dt))
            start = None
    if start is not None:
        runs.append((start * dt, (len(frozen) - start) * dt))
    held = [r for r in runs if r[1] >= 0.3]
    return {
        "frozen_fraction": float(frozen.mean()),
        "frozen_seconds": float(frozen.sum()) * dt,
        "longest_frozen_s": max([r[1] for r in runs], default=0.0),
        "held_runs": [(round(t, 2), round(l, 2)) for t, l in held][:20],
        "samples": len(frames),
    }


def band_pass(frames):
    """Mean luma of the reserved bottom band (y1600 to 1920 of 1920, the bottom
    16.67%). He sent back a frame of one with "What the fuck is this?": content
    stopped at y1530 and the bottom 390px averaged 13/255, which in a player
    reads as a broken black bar rather than as a reserved zone. A wide shallow
    stage lift took it to 28.5. Reserving a zone means keeping TEXT out of it,
    never leaving it black."""
    import numpy as np
    if frames is None:
        return None
    h = frames.shape[1]
    y0 = int(round(h * 1600.0 / 1920.0))
    band = frames[:, y0:, :]
    per_frame = band.mean(axis=(1, 2))
    return {
        "band_mean_luma": float(per_frame.mean()),
        "band_min_frame_luma": float(per_frame.min()),
        "band_y0_of_source": y0,
    }


def cover_pass(path, height_guess=1920):
    """Frame 0 is the Reels cover, so it is a delivered asset in its own right.
    Measured as ink coverage: the fraction of the frame whose luma departs from
    the frame's own modal background. `tools/gates/guard.py` uses 0.14 as the
    floor for a graphics zone after vid61 shipped three beats that were one
    element at the top of an 1120px column over blank paper, passing lint,
    validate and the safe-zone gate. A cover frame below the same floor is the
    same defect on the one frame everybody sees."""
    import numpy as np
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-frames:v", "1",
         "-vf", "scale=180:320", "-pix_fmt", "gray", "-f", "rawvideo", "-"],
        capture_output=True)
    n = 180 * 320
    if len(r.stdout) < n:
        return None
    f = np.frombuffer(r.stdout[:n], dtype="uint8").astype("int16")
    hist = np.bincount(f, minlength=256)
    ground = int(hist.argmax())
    ink = float((np.abs(f - ground) > 18).mean())
    return {"cover_ink_fraction": ink, "cover_ground_luma": ground}


# -------------------------------------------------------------------- the face

def face_pass(path, duration, sample_fps=1.0):
    """Face presence and the chin, via `tools/vision/facebox.swift`
    (`VNDetectFaceLandmarksRequest` rev-3, `faceContour`).

    Two separate numbers, two separate failures behind them:

      * presence as a fraction of runtime. "No need to show my face too much"
        settled shreyansh at about 30%; Nader's "better A-rolls and more
        A-rolls" turned out to mean b-roll, and face share falling 43.2% to
        39.4% was in a round he approved.
      * the chin. Above the chin IS the face, so a chin below y1600 is inside
        the Instagram bottom UI band. `contourBot` is the landmark to read:
        Vision's bounding box is not the head, and three rounds on one film
        measured contour, then bbox, then finally the crown before the note
        went away.

    A frame with no detection is not proof of no face (a profile, a hand across
    the jaw), so presence is a floor on the real number, not the number."""
    if shutil.which("swift") is None or not os.path.exists(FACEBOX):
        return None
    tmp = tempfile.mkdtemp(prefix="bench-face-")
    try:
        r = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-i", path,
             "-vf", "fps=%g,scale=540:-2" % sample_fps, "-q:v", "4",
             os.path.join(tmp, "%05d.jpg")], capture_output=True)
        files = sorted(f for f in os.listdir(tmp) if f.endswith(".jpg"))
        if not files:
            return None
        r = subprocess.run(["swift", FACEBOX, tmp], capture_output=True, text=True)
        rows = [l.split(",") for l in r.stdout.strip().splitlines()[1:] if l.strip()]
        if not rows:
            return None
        n = len(rows)
        detected, chins = 0, []
        for row in rows:
            if len(row) < 9 or row[1] in ("NA", "NOFACE", "ERR"):
                continue
            detected += 1
            cb = row[8]
            if cb not in ("NA", ""):
                chins.append(float(cb))
        chins.sort()
        return {
            "face_samples": n,
            "face_presence_fraction": detected / float(n),
            "chin_max_norm": chins[-1] if chins else None,
            "chin_p95_norm": chins[int(0.95 * (len(chins) - 1))] if chins else None,
            "chin_median_norm": chins[len(chins) // 2] if chins else None,
            "chin_below_band_samples": sum(1 for c in chins if c > 1600.0 / 1920.0),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------- the copy

def emdash_pass(paths):
    """Every account carries a standing no-em-dash rule and it was only ever
    enforced inside the composition. Scanned across `out/` this session: 19
    delivered caption packs and 2 delivered SRTs carry em dashes. The check has
    to cover the DELIVERABLES, and the caption pack and the SRT are
    deliverables."""
    out = {"total": 0, "files": []}
    seen = set()
    for p in paths:
        if not p or p in seen:
            continue
        seen.add(p)
        if not os.path.exists(p):
            out["files"].append({"path": p, "count": None, "note": "missing"})
            continue
        try:
            txt = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            out["files"].append({"path": p, "count": None, "note": "unreadable"})
            continue
        c = txt.count(EM_DASH)
        out["total"] += c
        lines = [i + 1 for i, l in enumerate(txt.splitlines()) if EM_DASH in l][:8]
        out["files"].append({"path": p, "count": c, "lines": lines})
    return out


# ------------------------------------------------------------------ the compare

def resolve_specs(bench, creator):
    specs = dict(bench.get("defaults", {}))
    for k, v in bench.get("creators", {}).get(creator, {}).items():
        merged = dict(specs.get(k, {}))
        merged.update(v)
        specs[k] = merged
    return specs


def judge(spec, value):
    """min/max are the hard edges, warn_min/warn_max the soft ones. `severity`
    downgrades a breach of a hard edge to a warning, which is what a metric with
    a shipped, owner-approved counter-example gets: the archive is telling you
    the number and the exception at the same time and it is not this tool's job
    to pick."""
    if value is None:
        return SKIP, "not measured"
    sev = FAIL if spec.get("severity", "fail") == "fail" else WARN
    lo, hi = spec.get("min"), spec.get("max")
    wlo, whi = spec.get("warn_min"), spec.get("warn_max")
    if lo is not None and value < lo:
        return sev, "below hard min %s" % lo
    if hi is not None and value > hi:
        return sev, "above hard max %s" % hi
    if wlo is not None and value < wlo:
        return WARN, "below target %s" % wlo
    if whi is not None and value > whi:
        return WARN, "above target %s" % whi
    return PASS, ""


def as_lines(v):
    """The `why` fields are lists of lines so the JSON stays readable at 90
    columns. Print them as prose, not as a repr."""
    if isinstance(v, list):
        return v
    return [v]


def target_text(spec):
    bits = []
    if spec.get("min") is not None:
        bits.append(">= %s" % spec["min"])
    if spec.get("max") is not None:
        bits.append("<= %s" % spec["max"])
    if spec.get("warn_min") is not None:
        bits.append("want >= %s" % spec["warn_min"])
    if spec.get("warn_max") is not None:
        bits.append("want <= %s" % spec["warn_max"])
    if spec.get("equals") is not None:
        bits.append("== %s" % spec["equals"])
    return ", ".join(bits) or "recorded only"


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Measure a delivered film against the numbers real rejections set.")
    ap.add_argument("film", help="the delivered mp4, e.g. out/vid67-final.mp4")
    ap.add_argument("--creator", default="house",
                    help="shreyansh | gaurav | nader | demi | house")
    ap.add_argument("--master", help="the CAMERA master A-roll, for the bitrate and "
                                     "resolution contract. Not the project's CRF-17 "
                                     "transcode, which carries a higher rate than the "
                                     "master it came from and makes the ratio lie.")
    ap.add_argument("--master-bitrate", type=float,
                    help="master total Mbps, when the master file is not to hand")
    ap.add_argument("--master-resolution", help="WIDTHxHEIGHT, e.g. 2160x3840")
    ap.add_argument("--srt", help="the delivered .srt")
    ap.add_argument("--caption-pack", help="the delivered caption pack .md")
    ap.add_argument("--composition", help="the project index.html")
    ap.add_argument("--benchmarks", default=DEFAULT_BENCHMARKS)
    ap.add_argument("--sample-fps", type=float, default=10.0,
                    help="motion sampling rate (default 10)")
    ap.add_argument("--face-fps", type=float, default=1.0,
                    help="face sampling rate (default 1)")
    ap.add_argument("--no-motion", action="store_true")
    ap.add_argument("--no-face", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--json", help="write the full measurement to this path")
    args = ap.parse_args()

    t0 = time.time()
    need("ffprobe")
    need("ffmpeg")
    if not os.path.exists(args.film):
        sys.stderr.write("benchmark: no such file %s\n" % args.film)
        return 2

    with open(args.benchmarks, encoding="utf-8") as fh:
        bench = json.load(fh)
    creator = args.creator if args.creator in bench.get("creators", {}) else "house"
    if creator != args.creator:
        print("note: no creator block for %r, using house defaults" % args.creator)
    specs = resolve_specs(bench, creator)

    m = {"film": probe(args.film)}

    # the master side of the delivery contract
    master = None
    if args.master:
        master = probe(args.master)
    elif args.master_bitrate or args.master_resolution:
        master = {"path": "(declared)", "total_mbps": args.master_bitrate}
        if args.master_resolution:
            w, h = args.master_resolution.lower().split("x")
            master["width"], master["height"] = int(w), int(h)
    m["master"] = master

    have_numpy = True
    try:
        import numpy  # noqa: F401
    except ImportError:
        have_numpy = False
        print("note: numpy not installed, motion / band / cover passes skipped")

    if not args.no_audio:
        m["audio"] = loudness(args.film)
    if have_numpy and not args.no_motion:
        frames = gray_frames(args.film, args.sample_fps, 180, 320)
        m["motion"] = motion_pass(frames, args.sample_fps,
                                  still=bench.get("tuning", {}).get("still_threshold", 1.0))
        m["band"] = band_pass(frames)
        m["cover"] = cover_pass(args.film)
        del frames
        m["scene"] = scene_pass(args.film, m["film"]["duration"],
                                bench.get("tuning", {}).get("scene_threshold", 0.25))
    if not args.no_face:
        m["face"] = face_pass(args.film, m["film"]["duration"], args.face_fps)
        if m["face"] is None:
            print("note: face pass unavailable (needs swift + tools/vision/facebox.swift)")
    m["copy"] = emdash_pass([args.srt, args.caption_pack, args.composition])

    # ---- derive the comparable values
    f = m["film"]
    vals = {
        "delivery.fps": f["fps"],
        "delivery.duration_s": f["duration"],
        "delivery.height": f["height"],
    }
    # Nothing scanned must read SKIP, never a green 0. A check that measured no
    # files and reported a pass is how 21 em dashes shipped in the first place.
    if any(e.get("count") is not None for e in m["copy"]["files"]):
        vals["copy.em_dashes"] = m["copy"]["total"]
    cropped = False
    if master and master.get("width"):
        ar_f = f["width"] / float(f["height"])
        ar_m = master["width"] / float(master["height"])
        cropped = abs(ar_f - ar_m) / max(ar_f, ar_m) > 0.10
    if master and master.get("total_mbps") and not cropped:
        vals["delivery.bitrate_ratio"] = f["total_mbps"] / master["total_mbps"]
    if master and master.get("width"):
        if cropped:
            # A 9:16 cutdown of a 16:9 master is a CROP, so a whole-frame pixel
            # count compares two different pictures and reads 0.25x on a cut
            # that is sampling the master above 1:1. vid62's short is exactly
            # this case. Refuse the comparison rather than report a false FAIL:
            # solve the crop's own source width by hand and check that instead.
            m["aspect_mismatch"] = (ar_f, ar_m)
        else:
            vals["delivery.pixel_ratio"] = (f["width"] * f["height"]) / float(
                master["width"] * master["height"])
    if m.get("audio"):
        vals["audio.integrated_lufs"] = m["audio"]["integrated_lufs"]
        vals["audio.true_peak_dbtp"] = m["audio"]["true_peak_dbtp"]
    if m.get("scene"):
        vals["motion.mean_shot_s"] = m["scene"]["mean_shot_s"]
    if m.get("motion"):
        vals["motion.frozen_fraction"] = m["motion"]["frozen_fraction"]
        vals["motion.longest_frozen_s"] = m["motion"]["longest_frozen_s"]
    if m.get("band"):
        vals["frame.band_mean_luma"] = m["band"]["band_mean_luma"]
    if m.get("cover"):
        vals["frame.cover_ink_fraction"] = m["cover"]["cover_ink_fraction"]
    if m.get("face"):
        vals["face.presence_fraction"] = m["face"]["face_presence_fraction"]
        vals["face.chin_max_norm"] = m["face"]["chin_max_norm"]

    # ---- report
    print("")
    print("benchmark  %s" % os.path.basename(args.film))
    print("creator    %s" % creator)
    print("delivered  %dx%d  %.3f fps  %.2fs  %.2f Mbps  %s/%s  %.1f MB"
          % (f["width"], f["height"], f["fps"], f["duration"], f["total_mbps"],
             f["vcodec"], f["acodec"], f["size_bytes"] / 1e6))
    if master:
        if master.get("width"):
            print("master     %dx%d  %.2f Mbps  %s"
                  % (master["width"], master["height"],
                     master.get("total_mbps") or 0, master["path"]))
        else:
            print("master     %.2f Mbps (declared)" % master["total_mbps"])
    else:
        print("master     not supplied. The two delivery-contract metrics are SKIPPED, "
              "and they are the two he has complained about most.")
    if m.get("aspect_mismatch"):
        print("           delivered %.3f AR against a %.3f master, so this is a CROP and "
              "not a rescale." % m["aspect_mismatch"])
        print("           Both delivery-contract metrics are refused: a whole-frame pixel "
              "count and a whole-frame data rate")
        print("           both compare two different pictures. Solve the crop's own source "
              "width by hand and check")
        print("           that it samples the master at or above 1:1 instead.")
    print("")

    order = [k for k in bench.get("order", []) if k in specs]
    order += [k for k in specs if k not in order]

    rows, fails, warns = [], 0, 0
    for key in order:
        spec = specs[key]
        v = vals.get(key)
        state, why = judge(spec, v)
        if state == FAIL:
            fails += 1
        elif state == WARN:
            warns += 1
        unit = spec.get("unit", "")
        shown = "-" if v is None else (
            "%.3f" % v if isinstance(v, float) and abs(v) < 100 else
            ("%.1f" % v if isinstance(v, float) else str(v)))
        rows.append((state, key, "%s %s" % (shown, unit), target_text(spec), why, spec))

    w1 = max(len(r[1]) for r in rows)
    w2 = max(len(r[2]) for r in rows)
    w3 = max(len(r[3]) for r in rows)
    for state, key, shown, tgt, why, spec in rows:
        print("%-4s %-*s  %-*s  %-*s  %s" % (state, w1, key, w2, shown, w3, tgt, why))

    print("")
    for state, key, shown, tgt, why, spec in rows:
        if state in (FAIL, WARN):
            print("%s %s" % (state, key))
            if spec.get("film"):
                print("     set by: %s" % spec["film"])
            for line in as_lines(spec.get("why", "no provenance recorded")):
                print("     %s" % line)
            print("")

    if m["copy"]["total"]:
        print("")
        print("em dashes found:")
        for e in m["copy"]["files"]:
            if e.get("count"):
                print("  %s  x%d  lines %s"
                      % (e["path"], e["count"], ",".join(str(x) for x in e.get("lines", []))))
    missing = [e["path"] for e in m["copy"]["files"] if e.get("note")]
    if missing:
        print("  (not scanned: %s)" % ", ".join(missing))
    if not any(e.get("count") is not None for e in m["copy"]["files"]):
        print("")
        print("note: no --srt / --caption-pack / --composition given, so the em-dash "
              "check measured nothing. That is how it shipped broken 21 times.")

    if m.get("motion") and m["motion"]["held_runs"]:
        print("")
        print("held runs >= 0.3s (start, length): %s"
              % ", ".join("%.2f/%.2fs" % r for r in m["motion"]["held_runs"]))

    print("")
    print("%d FAIL, %d WARN, %d PASS  in %.1fs"
          % (fails, warns, sum(1 for r in rows if r[0] == PASS), time.time() - t0))

    if args.json:
        m["verdict"] = {"fails": fails, "warns": warns,
                        "rows": [{"state": r[0], "metric": r[1], "measured": r[2],
                                  "target": r[3], "why": r[4]} for r in rows]}
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(m, fh, indent=2)
        print("wrote %s" % args.json)

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
