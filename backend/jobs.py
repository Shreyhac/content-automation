"""Job store and worker.

One job at a time (renders are memory bound). State lives in memory and is
mirrored to <job>/status.json so a restart can still report what happened.

The API key is deliberately NOT part of the persisted record. It is held on the
in-memory job only, and scrubbed the moment the job leaves the running state.
"""
from __future__ import annotations

import json
import queue
import shutil
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

from config import WORK, ensure_work

QUEUED = "queued"
RUNNING = "running"
DONE = "done"
FAILED = "failed"
CANCELLED = "cancelled"

# Mirrors docs/01-pipeline.md. Reported to the frontend up front so it can render
# a progress list before the job starts.
STAGES = [
    "ingest",
    "reference",
    "identify",
    "transcribe",
    "face_solve",
    "plan",
    "compose",
    "gates",
    "render",
    "deliver",
]


@dataclass
class StageResult:
    name: str
    status: str = "pending"      # pending | running | ok | skipped | failed
    detail: str = ""
    started_at: float | None = None
    ended_at: float | None = None
    data: dict = field(default_factory=dict)


@dataclass
class Job:
    id: str
    creator: str | None = None
    model: str = "claude-opus-5"
    script: str = ""
    status: str = QUEUED
    stage: str | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    ended_at: float | None = None
    stages: list[StageResult] = field(default_factory=lambda: [StageResult(s) for s in STAGES])
    artifacts: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)

    # never persisted, never returned by the API
    api_key: str = field(default="", repr=False)
    cancel: threading.Event = field(default_factory=threading.Event, repr=False)

    @property
    def dir(self) -> Path:
        return WORK / self.id

    def stage_obj(self, name: str) -> StageResult:
        for s in self.stages:
            if s.name == name:
                return s
        raise KeyError(name)

    def log(self, msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self.logs.append(line)
        # keep the tail bounded; whisper and ffmpeg are chatty
        if len(self.logs) > 500:
            del self.logs[: len(self.logs) - 500]
        self.save()

    def public(self) -> dict[str, Any]:
        """The API projection. Excludes api_key and the cancel event by construction."""
        return {
            "job_id": self.id,
            "status": self.status,
            "stage": self.stage,
            "creator": self.creator,
            "model": self.model,
            "error": self.error,
            "created_at": self.created_at,
            "ended_at": self.ended_at,
            "stages": [asdict(s) for s in self.stages],
            "artifacts": self.artifacts,
            "logs": self.logs[-80:],
        }

    def save(self) -> None:
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            (self.dir / "status.json").write_text(
                json.dumps(self.public(), indent=2), encoding="utf-8"
            )
        except Exception:
            pass


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._q: queue.Queue[str] = queue.Queue()
        self._runner: Callable[[Job], None] | None = None
        ensure_work()
        self._rehydrate()
        self._worker = threading.Thread(target=self._loop, daemon=True, name="job-worker")
        self._worker.start()

    def _rehydrate(self) -> None:
        """Reload finished jobs from disk so a restart does not lose history.

        Only terminal jobs come back. A job that was mid-flight when the process
        died cannot be resumed (the container, the render and the API key are all
        gone), so it is surfaced as failed rather than left looking live.
        """
        for status_file in sorted(WORK.glob("*/status.json")):
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            job = Job(
                id=data.get("job_id") or status_file.parent.name,
                creator=data.get("creator"),
                model=data.get("model", "claude-opus-5"),
                status=data.get("status", FAILED),
                stage=None,
                error=data.get("error"),
                created_at=data.get("created_at", 0.0),
                ended_at=data.get("ended_at"),
                artifacts=data.get("artifacts", []),
                logs=data.get("logs", []),
            )
            job.stages = [
                StageResult(**{k: v for k, v in s.items() if k in StageResult.__dataclass_fields__})
                for s in data.get("stages", [])
            ] or [StageResult(s) for s in STAGES]
            if job.status in (QUEUED, RUNNING):
                job.status = FAILED
                job.error = "server restarted while this job was running"
            self._jobs[job.id] = job

    def prune(self, keep: int = 20) -> int:
        """Drop the oldest finished job directories. A 4K render round costs
        about 800MB (SETUP.md), so unbounded job dirs fill a disk quickly."""
        finished = [j for j in self.list() if j.status in (DONE, FAILED, CANCELLED)]
        removed = 0
        for job in finished[keep:]:
            shutil.rmtree(job.dir, ignore_errors=True)
            with self._lock:
                self._jobs.pop(job.id, None)
            removed += 1
        return removed

    def set_runner(self, fn: Callable[[Job], None]) -> None:
        self._runner = fn

    def create(self, **kw) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], **kw)
        job.dir.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._jobs[job.id] = job
        job.save()
        self._q.put(job.id)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def cancel(self, job_id: str) -> bool:
        job = self.get(job_id)
        if not job or job.status in (DONE, FAILED, CANCELLED):
            return False
        job.cancel.set()
        if job.status == QUEUED:
            job.status = CANCELLED
            job.ended_at = time.time()
            job.api_key = ""
            job.save()
        return True

    def _loop(self) -> None:
        while True:
            job_id = self._q.get()
            job = self.get(job_id)
            if not job or job.status == CANCELLED:
                continue
            if not self._runner:
                job.status = FAILED
                job.error = "no pipeline runner registered"
                job.save()
                continue
            job.status = RUNNING
            job.save()
            try:
                self._runner(job)
                if job.cancel.is_set():
                    job.status = CANCELLED
                elif job.status == RUNNING:
                    job.status = DONE
            except Exception as e:
                job.status = FAILED
                job.error = f"{type(e).__name__}: {e}"
                job.log("FATAL " + traceback.format_exc(limit=4))
            finally:
                job.ended_at = time.time()
                job.stage = None
                job.api_key = ""      # scrub the key the moment the job leaves running
                job.save()


STORE = JobStore()
