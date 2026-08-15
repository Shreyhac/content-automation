"""Pipeline stage 1: deconstruct a supplied reference video.

docs/01-pipeline.md is explicit that a reference must be *measured*, not
described from memory, so every number in the breakdown comes off the file:
ffprobe for dims and duration, a 2fps frame strip for the shot table, and
whisper for the verbatim VO. The model only reads what the tools produced.

Whisper is optional on this host (see config.capabilities): a breakdown without
the VO is still worth having, so a missing whisper degrades to a note under
`skipped` rather than killing the stage. ffmpeg is not optional, since without
frames there is nothing to deconstruct.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import compose
from config import run, tool_paths

# docs/01-pipeline.md stage 1: `-vf fps=2`, and read them ALL as images. The
# full strip stays on disk for later measurement passes; only what goes into the
# one model call is capped, since a 40s reference is 80 frames and the request
# would be mostly redundant pixels.
FRAME_FPS = 2
MAX_MODEL_FRAMES = 12


def _even_sample(items: list[Path], cap: int) -> list[Path]:
    """Spread the sample across the whole file.

    Taking the first N frames describes the opening and nothing else, which is
    how a breakdown ends up missing the back half's layout entirely.
    """
    if len(items) <= cap:
        return items
    step = (len(items) - 1) / (cap - 1)
    return [items[round(i * step)] for i in range(cap)]


def _image_block(f: Path) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64.standard_b64encode(f.read_bytes()).decode(),
        },
    }


def _probe(ffprobe: str, ref_path: Path) -> dict:
    rc, out, err = run([ffprobe, "-v", "error", "-print_format", "json",
                        "-show_streams", "-show_format", str(ref_path)])
    if rc != 0:
        raise RuntimeError(f"ffprobe failed on the reference: {err[-400:]}")
    meta = json.loads(out)
    v = next((x for x in meta["streams"] if x["codec_type"] == "video"), None)
    if not v:
        raise RuntimeError("the reference has no video stream")
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    return {
        "width": v.get("width"),
        "height": v.get("height"),
        "duration": round(float(meta["format"].get("duration", 0)), 3),
        "fps": round(float(num) / float(den or 1), 3),
        "has_audio": any(x["codec_type"] == "audio" for x in meta["streams"]),
    }


def _whisper_vo(t: dict, ref_path: Path, ref_dir: Path, log) -> tuple[dict, str | None]:
    """Verbatim VO off the reference audio. Returns (transcript, skip reason)."""
    wav = ref_dir / "audio.wav"
    rc, _, err = run([t["ffmpeg"], "-nostdin", "-y", "-i", str(ref_path),
                      "-vn", "-ar", "16000", "-ac", "1", str(wav)])
    if rc != 0 or not wav.exists():
        return {"words": [], "text": ""}, f"audio extract failed: {err[-300:]}"

    log("reference: whisper (model small, word timestamps)")
    rc, _, err = run([t["whisper"], str(wav), "--model", "small",
                      "--word_timestamps", "True", "--output_format", "json",
                      "--output_dir", str(ref_dir)],
                     timeout=3600)
    out = next(iter(sorted(ref_dir.glob("*.json"))), None) if rc == 0 else None
    if not out:
        return {"words": [], "text": ""}, f"whisper failed: {err[-300:]}"

    raw = json.loads(out.read_text(encoding="utf-8", errors="replace"))
    words = [
        {"word": w.get("word", "").strip(), "start": w.get("start"), "end": w.get("end")}
        for seg in raw.get("segments", [])
        for w in seg.get("words", [])
        if w.get("start") is not None
    ]
    return {"words": words, "text": raw.get("text", "").strip()}, None


def deconstruct(api_key: str, model: str, ref_path: Path, work_dir: Path, log) -> dict:
    """Measure a reference video and return its breakdown.

    Writes `<work_dir>/reference-breakdown.json` and returns the same dict.
    """
    t = tool_paths()
    ref_path = Path(ref_path)
    work_dir = Path(work_dir)
    if not ref_path.exists():
        raise RuntimeError(f"reference not found: {ref_path}")
    if not t["ffmpeg"]:
        raise RuntimeError("ffmpeg not found on this host; the reference cannot be deconstructed")

    ref_dir = work_dir / "ref"
    ref_dir.mkdir(parents=True, exist_ok=True)
    skipped: list[str] = []

    probe: dict = {}
    if t["ffprobe"]:
        probe = _probe(t["ffprobe"], ref_path)
        log(f"reference: {probe['width']}x{probe['height']} {probe['duration']}s {probe['fps']}fps")
    else:
        skipped.append("ffprobe not found; dims, duration and fps were not measured")
        log("reference: ffprobe missing, skipping the probe")

    log(f"reference: extracting frames at {FRAME_FPS}fps")
    rc, _, err = run([t["ffmpeg"], "-nostdin", "-y", "-i", str(ref_path),
                      "-vf", f"fps={FRAME_FPS}", "-q:v", "3",
                      str(ref_dir / "f%04d.jpg")], timeout=1800)
    frames = sorted(ref_dir.glob("f*.jpg"))
    if rc != 0 or not frames:
        raise RuntimeError(f"reference frame extraction failed: {err[-400:]}")
    log(f"reference: {len(frames)} frames")

    transcript: dict = {"words": [], "text": ""}
    if not t["whisper"]:
        skipped.append("whisper not found; the verbatim VO was not transcribed")
        log("reference: whisper missing, skipping the VO")
    elif probe and not probe.get("has_audio"):
        skipped.append("the reference has no audio track; there is no VO to transcribe")
        log("reference: no audio track, skipping the VO")
    else:
        transcript, reason = _whisper_vo(t, ref_path, ref_dir, log)
        if reason:
            skipped.append(reason)
            log(f"reference: VO unavailable, {reason}")
        else:
            log(f"reference: {len(transcript['words'])} words transcribed")

    sample = _even_sample(frames, MAX_MODEL_FRAMES)
    log(f"reference: sending {len(sample)} frames to the model")

    # Frame times let the model tie each image to the shot table it is writing,
    # which is the whole point of the table: time, layer layout, visual.
    stamps = ", ".join(f"{frames.index(f) / FRAME_FPS:.1f}s" for f in sample)
    vo = transcript.get("text") or "(not transcribed on this host)"
    word_lines = "\n".join(
        f"{w['start']:.2f}-{w['end']:.2f} {w['word']}" for w in (transcript.get("words") or [])[:1200]
    ) or "(no word timestamps)"

    content: list[dict] = [_image_block(f) for f in sample]
    content.append(
        {
            "type": "text",
            "text": f"""These frames are an evenly spaced sample of one reference video, in order, at {stamps}.
Source: {probe.get('width')}x{probe.get('height')}, {probe.get('duration')}s, {probe.get('fps')}fps.

VERBATIM VO (whisper, the source of truth over any description):
{vo[:6000]}

WORD TIMESTAMPS:
{word_lines}

Deconstruct this reference as docs/01-pipeline.md stage 1 requires. Take numbers off
what you can see: positions, bands, safe areas, where the face sits, what carries each
beat. Do not describe it in general terms.

Reply with JSON only:
{{"verbatim_vo": "the spoken words, verbatim",
  "beat_map": [{{"time": 0.0, "description": "what happens on this beat"}}],
  "shot_table": [{{"time": 0.0, "layer_layout": "CARD or FULL_BLEED plus where each layer sits",
                   "visual": "the physical event on screen"}}],
  "design_language": {{"palette": "...", "type": "...", "motion": "..."}},
  "asset_checklist": ["every asset this cut would need rebuilt"]}}""",
        }
    )

    r = compose._call(api_key, model, max_tokens=compose.MAX_TOKENS, system=None, content=content)
    breakdown = compose._json_from(compose._text(r))

    result = {
        "source": str(ref_path),
        "probe": probe,
        "frames_dir": str(ref_dir),
        "frame_count": len(frames),
        "frame_fps": FRAME_FPS,
        "sampled_frames": [f.name for f in sample],
        "transcript": transcript,
        "verbatim_vo": breakdown.get("verbatim_vo") or transcript.get("text", ""),
        "beat_map": breakdown.get("beat_map", []),
        "shot_table": breakdown.get("shot_table", []),
        "design_language": breakdown.get("design_language", {}),
        "asset_checklist": breakdown.get("asset_checklist", []),
        "skipped": skipped,
    }

    out_path = work_dir / "reference-breakdown.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    log(f"reference: breakdown written to {out_path.name} "
        f"({len(result['beat_map'])} beats, {len(result['shot_table'])} shots)")
    return result
