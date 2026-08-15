"""HTTP API for the content-automation pipeline.

Frontend contract: upload an A-roll plus a script (reference optional), supply
your own model id and API key, poll the job, download the artifacts.

Run:  python -m uvicorn app:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import pipeline
from config import KNOWN_CREATORS, capabilities
from compose import DEFAULT_MODEL
from jobs import STORE, STAGES

app = FastAPI(
    title="Content Automation API",
    description="A-roll + script in, finished cut out. See backend/README.md.",
    version="0.1.0",
)

# The frontend is a separate origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORE.set_runner(pipeline.run_job)


@app.get("/api/health")
def health():
    return {"ok": True, "stages": STAGES}


@app.get("/api/capabilities")
def caps():
    """What this host can actually do. The frontend should call this on load and
    warn the user about any stage in `degraded` before they upload."""
    return capabilities()


@app.post("/api/jobs")
async def create_job(
    aroll: UploadFile = File(..., description="The A-roll video"),
    script: str = Form(..., description="The script or brief"),
    api_key: str = Form(..., description="Anthropic API key. Never written to disk."),
    model: str = Form(DEFAULT_MODEL),
    creator: str | None = Form(None, description="nader | gaurav | shreyansh. Detected from the footage if omitted."),
    reference: UploadFile | None = File(None, description="Optional reference video"),
):
    if creator and creator not in KNOWN_CREATORS:
        raise HTTPException(400, f"creator must be one of {list(KNOWN_CREATORS)}")
    if not api_key.strip():
        raise HTTPException(400, "api_key is required")

    job = STORE.create(script=script, model=model or DEFAULT_MODEL,
                       creator=creator, api_key=api_key.strip())

    inp = job.dir / "input"
    inp.mkdir(parents=True, exist_ok=True)
    with open(inp / "aroll.mp4", "wb") as f:
        shutil.copyfileobj(aroll.file, f)
    if reference is not None:
        with open(inp / "reference.mp4", "wb") as f:
            shutil.copyfileobj(reference.file, f)
    (inp / "script.txt").write_text(script, encoding="utf-8")

    job.log(f"uploaded {aroll.filename}")
    return {"job_id": job.id, "status": job.status, "stages": STAGES}


@app.get("/api/jobs")
def list_jobs():
    return {"jobs": [j.public() for j in STORE.list()]}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = STORE.get(job_id)
    if not job:
        raise HTTPException(404, "no such job")
    return job.public()


@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str):
    if not STORE.cancel(job_id):
        raise HTTPException(404, "no such job, or it already finished")
    return {"job_id": job_id, "cancelled": True}


@app.post("/api/maintenance/prune")
def prune(keep: int = 20):
    """Drop the oldest finished job directories. A 4K render round costs about
    800MB, so job dirs fill a disk fast if nothing reaps them."""
    return {"removed": STORE.prune(keep=keep), "kept": keep}


@app.get("/api/jobs/{job_id}/artifacts/{name:path}")
def artifact(job_id: str, name: str):
    job = STORE.get(job_id)
    if not job:
        raise HTTPException(404, "no such job")

    # Confine the path to the job directory: `name` is caller-supplied.
    target = (job.dir / name).resolve()
    if not target.is_relative_to(job.dir.resolve()) or not target.is_file():
        raise HTTPException(404, "no such artifact")
    return FileResponse(target, filename=Path(name).name)
