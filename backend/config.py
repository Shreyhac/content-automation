"""Paths, external-tool discovery and host capability probing.

The pipeline in docs/01-pipeline.md assumes macOS. This module is what lets the
service run anywhere and report honestly about what it cannot do, instead of
silently producing a worse cut.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
WORK = BACKEND / "work"

CREATORS = REPO / "creators"
DOCS = REPO / "docs"
PLAYBOOKS = REPO / "playbooks"
TEMPLATES = REPO / "library" / "templates"
REFERENCE_BUILDS = REPO / "reference-builds"
REFERENCE_CUTS = REPO / "reference-cuts"

KNOWN_CREATORS = ("nader", "gaurav", "shreyansh")

# docs/07-troubleshooting.md + SETUP.md: the 60s no-frame-progress watchdog kills
# healthy renders on heavy compositions. Not optional.
HF_DE_STALL_MS = os.environ.get("HF_DE_STALL_MS", "420000")

# SETUP.md:92 -- renders are memory bound. One job at a time, and a modest worker
# count inside it. Raise RENDER_WORKERS on a 16GB+ host.
MAX_CONCURRENT_JOBS = 1
RENDER_WORKERS = os.environ.get("HF_RENDER_WORKERS", "2")


def _which(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def tool_paths() -> dict[str, str | None]:
    """Resolve every external binary the pipeline shells out to.

    `python3` does not exist on Windows, so fall back to the running interpreter
    rather than letting nine shell scripts fail on a missing name.
    """
    return {
        "ffmpeg": _which("ffmpeg"),
        "ffprobe": _which("ffprobe"),
        "node": _which("node"),
        "npx": _which("npx", "npx.cmd"),
        "whisper": _which("whisper"),
        "python": _which("python3") or sys.executable,
        "swift": _which("swift"),
    }


def _has_playwright() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except Exception:
        return False


def capabilities() -> dict:
    """What this host can actually do. Served at GET /api/capabilities so the
    frontend can warn the user before they wait through a job that cannot finish.
    """
    t = tool_paths()
    is_mac = sys.platform == "darwin"
    caps = {
        "platform": sys.platform,
        "tools": {k: bool(v) for k, v in t.items()},
        "stages": {
            "ingest": bool(t["ffprobe"] and t["ffmpeg"]),
            "identify": bool(t["ffmpeg"]),
            "transcribe": bool(t["whisper"] and t["ffmpeg"]),
            "plan": True,          # model call only
            "compose": True,       # model call only
            "gates": bool(t["npx"]),
            "pageerror_gate": _has_playwright(),
            "render": bool(t["npx"]),
            "deliver": bool(t["ffmpeg"]),
            # tools/vision/*.swift use Apple's Vision framework. There is no
            # Windows/Linux equivalent in this repo, and CLAUDE.md makes the
            # measured head solve mandatory before any face geometry.
            "face_solve": is_mac and bool(t["swift"]),
        },
    }
    caps["degraded"] = [k for k, v in caps["stages"].items() if not v]
    return caps


def creator_context(creator: str) -> str:
    """PROFILE + GRAMMAR for a creator. Their hard rules outrank everything else,
    so this goes into the model's system prompt verbatim.
    """
    parts: list[str] = []
    for name in ("PROFILE.md", "GRAMMAR.md"):
        f = CREATORS / creator / name
        if f.exists():
            parts.append(f"===== creators/{creator}/{name} =====\n{f.read_text(encoding='utf-8', errors='replace')}")
    return "\n\n".join(parts)


def house_rules() -> str:
    """The general rules every creator inherits."""
    parts: list[str] = []
    for f in (REPO / "CLAUDE.md", DOCS / "02-safe-zones.md", DOCS / "03-quality-bar.md"):
        if f.exists():
            parts.append(f"===== {f.relative_to(REPO).as_posix()} =====\n{f.read_text(encoding='utf-8', errors='replace')}")
    return "\n\n".join(parts)


def ensure_work() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    return WORK


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 900, env_extra: dict | None = None):
    """Shell out with the pipeline's environment. Returns (rc, stdout, stderr)."""
    env = os.environ.copy()
    env["HF_DE_STALL_MS"] = HF_DE_STALL_MS
    if env_extra:
        env.update(env_extra)
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            errors="replace",
        )
        return p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError as e:
        return 127, "", f"binary not found: {e}"
