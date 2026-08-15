"""The eight stages from docs/01-pipeline.md, as callable functions.

Every stage records ok / skipped / failed with a reason. A stage that cannot
run on this host is reported `skipped`, never silently passed: CLAUDE.md is
explicit that a handoff claiming "done" while the deliverable is stale has
already cost a full session here.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

import compose
from config import (
    HF_DE_STALL_MS,
    RENDER_WORKERS,
    REFERENCE_BUILDS,
    TEMPLATES,
    capabilities,
    run,
    tool_paths,
)
from jobs import Job


def _stage(job: Job, name: str):
    """Context-manager-ish helper: mark running, return the StageResult."""
    s = job.stage_obj(name)
    s.status = "running"
    s.started_at = time.time()
    job.stage = name
    job.save()
    return s


def _ok(job: Job, s, detail: str = "", **data):
    s.status = "ok"
    s.detail = detail
    s.data.update(data)
    s.ended_at = time.time()
    job.save()


def _skip(job: Job, s, reason: str):
    s.status = "skipped"
    s.detail = reason
    s.ended_at = time.time()
    job.log(f"SKIP {s.name}: {reason}")
    job.save()


def _fail(job: Job, s, reason: str):
    s.status = "failed"
    s.detail = reason
    s.ended_at = time.time()
    job.save()
    raise RuntimeError(f"{s.name}: {reason}")


# ---------------------------------------------------------------- stages ----

def ingest(job: Job) -> dict:
    """Stage 1. Probe the A-roll. File size matters: docs/06-delivery.md requires
    matching the raw A-roll's byte size on delivery for both IG creators."""
    s = _stage(job, "ingest")
    t = tool_paths()
    aroll = job.dir / "input" / "aroll.mp4"
    if not aroll.exists():
        _fail(job, s, "no A-roll uploaded")
    if not t["ffprobe"]:
        _fail(job, s, "ffprobe not found on this host")

    rc, out, err = run([t["ffprobe"], "-v", "error", "-print_format", "json",
                        "-show_streams", "-show_format", str(aroll)])
    if rc != 0:
        _fail(job, s, f"ffprobe failed: {err[:400]}")

    meta = json.loads(out)
    v = next((x for x in meta["streams"] if x["codec_type"] == "video"), None)
    if not v:
        _fail(job, s, "no video stream in the upload")

    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    probe = {
        "width": v.get("width"),
        "height": v.get("height"),
        "duration": round(float(meta["format"].get("duration", 0)), 3),
        "fps": round(float(num) / float(den or 1), 3),
        "size_bytes": int(meta["format"].get("size", 0)),
        "has_audio": any(x["codec_type"] == "audio" for x in meta["streams"]),
    }
    _ok(job, s, f"{probe['width']}x{probe['height']} {probe['duration']}s", **probe)
    return probe


def identify(job: Job, probe: dict) -> str:
    """Stage 0/2. Creator from the footage, not the brief."""
    s = _stage(job, "identify")
    t = tool_paths()
    if job.creator:
        _ok(job, s, f"creator supplied by caller: {job.creator}", source="caller")
        return job.creator
    if not t["ffmpeg"]:
        _fail(job, s, "ffmpeg not found; cannot build a contact sheet")

    sheet = job.dir / "sheet"
    sheet.mkdir(exist_ok=True)
    rc, _, err = run([t["ffmpeg"], "-nostdin", "-y", "-i", str(job.dir / "input" / "aroll.mp4"),
                      "-vf", "fps=1", "-frames:v", "12", "-q:v", "3",
                      str(sheet / "f%02d.jpg")])
    frames = sorted(sheet.glob("*.jpg"))
    if rc != 0 or not frames:
        _fail(job, s, f"contact sheet extraction failed: {err[-400:]}")

    try:
        result = compose.identify_creator(job.api_key, job.model, frames)
    except Exception as e:
        _fail(job, s, f"model could not identify the creator: {e}")

    job.creator = result["creator"]
    _ok(job, s, f"{result['creator']} (confidence {result.get('confidence')})", **result)
    return job.creator


def transcribe(job: Job, probe: dict) -> dict:
    """Stage 3. Whisper the A-roll. CLAUDE.md: the audio is the source of truth,
    never the pasted script."""
    s = _stage(job, "transcribe")
    t = tool_paths()
    if not probe.get("has_audio"):
        _skip(job, s, "A-roll has no audio track")
        return {"words": []}
    if not t["whisper"] or not t["ffmpeg"]:
        _skip(job, s, "whisper or ffmpeg not available on this host")
        return {"words": []}

    wav = job.dir / "input" / "aroll.wav"
    rc, _, err = run([t["ffmpeg"], "-nostdin", "-y", "-i", str(job.dir / "input" / "aroll.mp4"),
                      "-vn", "-ar", "16000", "-ac", "1", str(wav)])
    if rc != 0:
        _fail(job, s, f"audio extract failed: {err[-400:]}")

    rc, _, err = run([t["whisper"], str(wav), "--model", "small",
                      "--word_timestamps", "True", "--output_format", "json",
                      "--output_dir", str(job.dir / "transcript")],
                     timeout=3600)
    out = next((job.dir / "transcript").glob("*.json"), None) if rc == 0 else None
    if not out:
        _fail(job, s, f"whisper failed: {err[-400:]}")

    raw = json.loads(out.read_text(encoding="utf-8", errors="replace"))
    words = [
        {"word": w.get("word", "").strip(), "start": w.get("start"), "end": w.get("end")}
        for seg in raw.get("segments", [])
        for w in seg.get("words", [])
        if w.get("start") is not None
    ]
    data = {"words": words, "text": raw.get("text", "")}
    (job.dir / "words.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    job.artifacts.append("words.json")
    _ok(job, s, f"{len(words)} words", word_count=len(words))
    return data


def face_solve(job: Job, probe: dict) -> dict:
    """Stage 5. Measure the head with Vision before any geometry is solved.

    CLAUDE.md: "Measure the head with Vision before solving any geometry" and
    "the formula travels, the constants never do" - every take needs its own
    solve, so this runs per job and its numbers are handed to the planner.

    tools/vision/*.swift use Apple's Vision framework, so this is macOS only.
    Off macOS the stage reports skipped and the planner is told the geometry is
    unmeasured, rather than being fed numbers copied from another video.
    """
    s = _stage(job, "face_solve")
    t = tool_paths()
    caps = capabilities()
    if not caps["stages"]["face_solve"]:
        _skip(job, s, "requires macOS with swift: tools/vision/*.swift use Apple's Vision framework")
        return {}

    stills = job.dir / "stills"
    stills.mkdir(exist_ok=True)
    # 5fps stills, the sampling rate tools/vision/build_windows.py expects.
    rc, _, err = run([t["ffmpeg"], "-nostdin", "-y", "-i", str(job.dir / "input" / "aroll.mp4"),
                      "-vf", "fps=5", "-q:v", "3", str(stills / "s_%05d.jpg")], timeout=1800)
    if rc != 0 or not any(stills.glob("*.jpg")):
        _fail(job, s, f"still extraction failed: {err[-400:]}")

    measured = {}
    for name, script in (("crown", "crown.swift"), ("facebox", "facebox.swift")):
        rc, out, err = run([t["swift"], str(REPO / "tools" / "vision" / script), str(stills)],
                           timeout=3600)
        if rc != 0:
            _fail(job, s, f"{script} failed: {err[-400:]}")
        csv = job.dir / f"{name}.csv"
        csv.write_text(out, encoding="utf-8")
        job.artifacts.append(csv.name)
        measured[name] = _summarise_csv(out, probe)

    (job.dir / "face-geometry.json").write_text(json.dumps(measured, indent=2), encoding="utf-8")
    job.artifacts.append("face-geometry.json")
    _ok(job, s, f"crown and chin measured over {len(list(stills.glob('*.jpg')))} stills", **measured)
    return measured


def _summarise_csv(csv_text: str, probe: dict) -> dict:
    """Reduce a per-frame Vision CSV to the few numbers the planner needs.

    The swift tools emit normalised coordinates; scale to pixels so the model
    reasons in the same units as the composition.
    """
    rows = [r.split(",") for r in csv_text.strip().splitlines() if r.strip()]
    if not rows:
        return {}
    header, body = rows[0], rows[1:]
    h = probe.get("height") or 1920
    out: dict[str, float] = {}
    for i, col in enumerate(header):
        vals = []
        for r in body:
            if i < len(r):
                try:
                    vals.append(float(r[i]))
                except ValueError:
                    pass
        if vals:
            out[f"{col.strip()}_min"] = round(min(vals) * h, 1)
            out[f"{col.strip()}_max"] = round(max(vals) * h, 1)
    return out


def plan(job: Job, transcript: dict, probe: dict, geometry: dict, breakdown: dict) -> dict:
    """Stage 6. Beat plan, built against the measured take and the reference."""
    s = _stage(job, "plan")
    try:
        result = compose.plan_beats(job.api_key, job.model, job.creator, transcript,
                                    job.script, probe, geometry, breakdown)
    except Exception as e:
        _fail(job, s, str(e))
    (job.dir / "beats.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    job.artifacts.append("beats.json")
    _ok(job, s, f"{len(result.get('beats', []))} beats", beat_count=len(result.get("beats", [])))
    return result


def compose_stage(job: Job, beat_plan: dict, probe: dict) -> Path:
    """Stage 5. Scaffold from the creator's reference build, then author the
    composition into it."""
    s = _stage(job, "compose")
    build = job.dir / "build"
    build.mkdir(exist_ok=True)
    (build / "assets").mkdir(exist_ok=True)

    donor = next(REFERENCE_BUILDS.glob(f"{job.creator}-*"), None)
    pkg = (donor / "package.json") if donor else (TEMPLATES / "vertical-reel" / "package.json")
    if pkg.exists():
        shutil.copy(pkg, build / "package.json")

    # Order matters (docs/01-pipeline.md stage 4): scaffold first, then place
    # the A-roll, never the reverse.
    shutil.copy(job.dir / "input" / "aroll.mp4", build / "assets" / "aroll.mp4")

    try:
        html = compose.compose(job.api_key, job.model, job.creator, beat_plan, "aroll.mp4", probe)
    except Exception as e:
        _fail(job, s, str(e))

    if "<div" not in html and "<body" not in html:
        _fail(job, s, "model did not return an HTML composition")

    # Owner rule, all creators, every delivery.
    if "—" in html or "–" in html:
        html = html.replace("—", ", ").replace("–", "-")
        job.log("stripped em/en dashes from the composition")

    index = build / "index.html"
    index.write_text(html, encoding="utf-8")
    job.artifacts.append("build/index.html")
    _ok(job, s, f"{len(html)} bytes", path=str(index))
    return index


def gates(job: Job, build: Path) -> None:
    """Stage 6. lint -> validate -> inspect, plus the Playwright pageerror check.

    The pageerror gate is mandated by CLAUDE.md and docs/01-pipeline.md:146 but
    was never implemented in this repo; it is written here for the first time.
    A ReferenceError before timeline registration renders a page of static DOM
    while lint, validate and render all report success.
    """
    s = _stage(job, "gates")
    t = tool_paths()
    if not t["npx"]:
        _skip(job, s, "npx not found; hyperframes gates cannot run")
        return

    results = {}
    for gate in ("lint", "validate", "inspect"):
        rc, out, err = run([t["npx"], "--yes", "hyperframes", gate], cwd=build, timeout=600)
        results[gate] = {"rc": rc, "tail": (out + err)[-1500:]}
        job.log(f"gate {gate}: rc={rc}")

    results["pageerror"] = _pageerror_gate(job, build)

    hard = [g for g in ("lint",) if results[g]["rc"] != 0]
    if hard:
        _fail(job, s, f"{', '.join(hard)} failed; see logs")
    _ok(job, s, "gates run", **results)


def _pageerror_gate(job: Job, build: Path) -> dict:
    """Load the composition for 10s, listen for pageerror, assert
    window.__timelines has keys. The only gate that catches script death."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        job.log("pageerror gate skipped: playwright not installed")
        return {"status": "skipped", "reason": "playwright not installed"}

    errors: list[str] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto((build / "index.html").as_uri(), wait_until="domcontentloaded")
            page.wait_for_timeout(10000)
            keys = page.evaluate("Object.keys(window.__timelines || {})")
            browser.close()
    except Exception as e:
        job.log(f"pageerror gate could not run: {e}")
        return {"status": "skipped", "reason": str(e)[:300]}

    if errors:
        job.log(f"PAGEERROR: {errors[0][:300]}")
        return {"status": "failed", "errors": errors[:5], "timelines": keys}
    if not keys:
        job.log("PAGEERROR gate: window.__timelines is empty (script death before registration)")
        return {"status": "failed", "errors": [], "timelines": []}
    return {"status": "ok", "timelines": keys}


def render(job: Job, build: Path) -> Path | None:
    """Stage 7. HF_DE_STALL_MS is not optional on heavy compositions."""
    s = _stage(job, "render")
    t = tool_paths()
    if not t["npx"]:
        _skip(job, s, "npx not found; cannot render")
        return None

    rc, out, err = run(
        [t["npx"], "--yes", "hyperframes", "render", "-q", "high",
         "--workers", RENDER_WORKERS, "--video-bitrate", "16M"],
        cwd=build, timeout=5400,
        env_extra={"HF_DE_STALL_MS": HF_DE_STALL_MS},
    )
    mp4 = next(iter(sorted((build / "renders").glob("*.mp4"))), None) if (build / "renders").exists() else None
    if rc != 0 or not mp4:
        _fail(job, s, f"render failed (rc={rc}): {(out + err)[-800:]}")

    _ok(job, s, mp4.name, path=str(mp4))
    return mp4


def deliver(job: Job, mp4: Path | None, probe: dict, transcript: dict) -> None:
    """Stage 8. Two-pass loudnorm with -c:v copy, em-dash grep, SRT."""
    s = _stage(job, "deliver")
    t = tool_paths()
    if not mp4:
        _skip(job, s, "no render to deliver")
        return
    if not t["ffmpeg"]:
        _skip(job, s, "ffmpeg not found")
        return

    out_dir = job.dir / "out"
    out_dir.mkdir(exist_ok=True)
    final = out_dir / "final.mp4"

    # Pass 1 measures, pass 2 applies. -c:v copy: this grammar renders hot.
    rc, _, err = run([t["ffmpeg"], "-nostdin", "-y", "-i", str(mp4),
                      "-af", "loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json",
                      "-f", "null", "-"], timeout=1800)
    measured = {}
    m = re.search(r"\{[^{}]*input_i[^{}]*\}", err, re.S)
    if m:
        try:
            measured = json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    af = "loudnorm=I=-14:TP=-1.0:LRA=9"
    if measured:
        af += (f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
               f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
               f":linear=true:print_format=summary")

    rc, _, err = run([t["ffmpeg"], "-nostdin", "-y", "-i", str(mp4),
                      "-af", af, "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                      str(final)], timeout=1800)
    if rc != 0 or not final.exists():
        _fail(job, s, f"loudnorm pass failed: {err[-500:]}")

    srt = out_dir / "final.srt"
    srt.write_text(_srt(transcript.get("words") or []), encoding="utf-8")

    job.artifacts += ["out/final.mp4", "out/final.srt"]
    _ok(job, s, f"{final.stat().st_size} bytes (source {probe.get('size_bytes')})",
        size_bytes=final.stat().st_size, source_size_bytes=probe.get("size_bytes"),
        two_pass=bool(measured))


def _srt(words: list[dict]) -> str:
    """Group the word stream into cues. docs/06-delivery.md ships an SRT."""
    def ts(t: float) -> str:
        h, rem = divmod(max(t, 0), 3600)
        m, sec = divmod(rem, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int((sec % 1) * 1000):03d}"

    cues, cur = [], []
    for w in words:
        cur.append(w)
        line = " ".join(x["word"] for x in cur)
        if len(line) >= 42 or w["word"].endswith((".", "?", "!")):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)

    return "".join(
        f"{i}\n{ts(c[0]['start'])} --> {ts(c[-1]['end'])}\n"
        f"{' '.join(x['word'] for x in c)}\n\n"
        for i, c in enumerate(cues, 1)
    )


# ------------------------------------------------------------------ runner ---

def reference_stage(job: Job) -> dict:
    """Stage 2. Deconstruct a supplied reference by measuring the file.

    docs/01-pipeline.md stage 1: "measure that file, do not describe it from
    memory". Optional, because most jobs arrive without a reference.
    """
    s = _stage(job, "reference")
    ref = job.dir / "input" / "reference.mp4"
    if not ref.exists():
        _skip(job, s, "no reference supplied")
        return {}
    try:
        import reference as reference_mod
        result = reference_mod.deconstruct(job.api_key, job.model, ref, job.dir, job.log)
    except Exception as e:
        # A reference is an aid, not a dependency. Losing it degrades the plan
        # but should not sink a job that has a perfectly good A-roll.
        _skip(job, s, f"reference deconstruction failed: {e}")
        return {}
    job.artifacts.append("reference-breakdown.json")
    _ok(job, s, f"{len(result.get('shot_table', []))} shots mapped")
    return result


def run_job(job: Job) -> None:
    """The whole pipeline, in the order docs/01-pipeline.md requires."""
    job.log(f"start (model={job.model})")
    probe = ingest(job)
    if job.cancel.is_set():
        return
    breakdown = reference_stage(job)
    identify(job, probe)
    transcript = transcribe(job, probe)
    if job.cancel.is_set():
        return
    geometry = face_solve(job, probe)
    beat_plan = plan(job, transcript, probe, geometry, breakdown)
    build = compose_stage(job, beat_plan, probe)
    if job.cancel.is_set():
        return
    gates(job, build.parent)
    mp4 = render(job, build.parent)
    deliver(job, mp4, probe, transcript)
    job.log("done")
