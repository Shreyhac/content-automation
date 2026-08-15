# Backend: frontend integration contract

An HTTP service that wraps the editor pipeline in `docs/01-pipeline.md`. You POST an A-roll plus
a script, poll a job, and download the artifacts it produced. One job runs at a time.

Files:

| File | What it owns |
| --- | --- |
| `app.py` | FastAPI routes (the contract below) |
| `jobs.py` | `Job`, `StageResult`, the in-memory store and the single worker thread |
| `pipeline.py` | The eight stages as callable functions, plus `run_job()` |
| `compose.py` | The three model calls: identify, plan, compose |
| `config.py` | Paths, external-binary discovery, host capability probe |

## Quickstart

```bash
pip install fastapi uvicorn python-multipart anthropic
cd backend
python -m uvicorn app:app --reload --port 8000
```

Then `GET http://localhost:8000/api/capabilities` and check the `degraded` list before you
promise a user a finished cut.

External binaries the pipeline shells out to (all optional at boot, all reported by
`/api/capabilities`): `ffmpeg`, `ffprobe`, `node`, `npx`, `whisper`, `swift`. The Playwright
page-error gate additionally needs `pip install playwright && playwright install chromium`.

Job state lives under `backend/work/<job_id>/`, and each job mirrors its public projection to
`backend/work/<job_id>/status.json` so a restart can still report what happened. The in-memory
store itself does not survive a restart, so `GET /api/jobs` is empty after a reboot.

Environment overrides: `HF_DE_STALL_MS` (default `420000`; the 60s no-frame-progress watchdog
kills healthy renders, so do not lower this) and `HF_RENDER_WORKERS` (default `2`; raise on a
16GB+ host).

## API key handling

`api_key` is a required form field on `POST /api/jobs` and is used per job, per model call.
It is:

- held on the in-memory `Job` record only,
- excluded from `Job.public()` by construction, so it can never appear in any API response or
  in `status.json`,
- set to `""` the moment the job leaves the running state (success, failure or cancel), and
  also on cancel of a still-queued job.

It is never written to disk and never logged. The frontend must therefore send it with every
job; there is no server-side key store and no way to resume a job without it.

## Concurrency

`MAX_CONCURRENT_JOBS = 1`. A single daemon worker thread drains a FIFO queue, because renders
are memory bound. A second POST returns `201`-style success immediately with a `job_id`, but the
job sits in `queued` until the one ahead of it finishes. Show queue position in the UI rather
than implying work has started.

## Endpoints

### `POST /api/jobs`

`multipart/form-data`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `aroll` | file | yes | The A-roll video. Stored as `work/<id>/input/aroll.mp4`. |
| `script` | text | yes | The pasted brief/script. Advisory only: the whisper transcript wins wherever they disagree. |
| `reference` | file | no | Optional reference video. |
| `creator` | text | no | One of `nader`, `gaurav`, `shreyansh`. Omit to let the `identify` stage decide from the footage. |
| `model` | text | no | Defaults to `claude-opus-5`. |
| `api_key` | text | yes | Anthropic API key. See above. |

```bash
curl -X POST http://localhost:8000/api/jobs \
  -F "aroll=@vid64-aroll.mp4" \
  -F "script=Here is the take as written..." \
  -F "creator=nader" \
  -F "api_key=sk-ant-..."
```

```json
{ "job_id": "8f21c0a4b7de" }
```

### `GET /api/jobs/{id}`

Returns `Job.public()`.

```bash
curl http://localhost:8000/api/jobs/8f21c0a4b7de
```

```json
{
  "job_id": "8f21c0a4b7de",
  "status": "running",
  "stage": "compose",
  "creator": "nader",
  "model": "claude-opus-5",
  "error": null,
  "created_at": 1755250801.412,
  "ended_at": null,
  "stages": [
    {
      "name": "ingest",
      "status": "ok",
      "detail": "1080x1920 41.733s",
      "started_at": 1755250801.5,
      "ended_at": 1755250802.1,
      "data": {
        "width": 1080,
        "height": 1920,
        "duration": 41.733,
        "fps": 30.0,
        "size_bytes": 84213770,
        "has_audio": true
      }
    },
    {
      "name": "identify",
      "status": "ok",
      "detail": "creator supplied by caller: nader",
      "started_at": 1755250802.1,
      "ended_at": 1755250802.1,
      "data": { "source": "caller" }
    },
    {
      "name": "transcribe",
      "status": "skipped",
      "detail": "whisper or ffmpeg not available on this host",
      "started_at": 1755250802.2,
      "ended_at": 1755250802.2,
      "data": {}
    },
    {
      "name": "plan",
      "status": "ok",
      "detail": "11 beats",
      "started_at": 1755250802.3,
      "ended_at": 1755250874.8,
      "data": { "beat_count": 11 }
    },
    {
      "name": "compose",
      "status": "running",
      "detail": "",
      "started_at": 1755250874.9,
      "ended_at": null,
      "data": {}
    },
    { "name": "gates",   "status": "pending", "detail": "", "started_at": null, "ended_at": null, "data": {} },
    { "name": "render",  "status": "pending", "detail": "", "started_at": null, "ended_at": null, "data": {} },
    { "name": "deliver", "status": "pending", "detail": "", "started_at": null, "ended_at": null, "data": {} }
  ],
  "artifacts": ["beats.json"],
  "logs": ["[11:20:01] start (model=claude-opus-5)"]
}
```

Field notes:

- `status`: `queued` | `running` | `done` | `failed` | `cancelled`.
- `stage`: the stage currently running, or `null` when queued or finished.
- `error`: set only on `failed`, formatted `"<ExceptionType>: <message>"`.
- `created_at` / `ended_at`: unix epoch seconds (float), not ISO strings.
- `stages`: always all eight entries in pipeline order, present from creation, so the UI can
  render the progress list before the job starts. Per-stage `status` is
  `pending` | `running` | `ok` | `skipped` | `failed`; `detail` is the human-readable reason and
  is the string to surface for a skip or a failure; `data` is stage-specific and free-form.
- `artifacts`: relative paths under the job directory, appended as they are produced. Possible
  values in order: `words.json`, `beats.json`, `build/index.html`, `out/final.mp4`,
  `out/final.srt`.
- `logs`: last 80 lines only (the full in-memory tail is capped at 500).

Poll every 2 to 5 seconds. There is no websocket or SSE channel.

### `GET /api/jobs`

List of the same projection, newest first by `created_at`.

```bash
curl http://localhost:8000/api/jobs
```

```json
[
  { "job_id": "8f21c0a4b7de", "status": "running", "stage": "compose", "creator": "nader", "...": "..." },
  { "job_id": "3ac9911f0021", "status": "done",    "stage": null,      "creator": "gaurav", "...": "..." }
]
```

### `GET /api/jobs/{id}/artifacts/{name}`

Downloads one artifact. `name` is the exact string from the `artifacts` array, which may
contain a slash (`out/final.mp4`, `build/index.html`); pass it as a path suffix.

```bash
curl -O -J http://localhost:8000/api/jobs/8f21c0a4b7de/artifacts/out/final.mp4
curl http://localhost:8000/api/jobs/8f21c0a4b7de/artifacts/beats.json
```

Only names present in the job's `artifacts` list are downloadable.

### `DELETE /api/jobs/{id}`

Requests cancellation. A `queued` job flips to `cancelled` immediately. A `running` job has its
cancel flag set and stops at the next checkpoint (after `ingest`, after `transcribe`, after
`compose`), so an in-flight model call or render finishes first and cancellation is not
instant. A job already in `done` / `failed` / `cancelled` is not cancellable.

```bash
curl -X DELETE http://localhost:8000/api/jobs/8f21c0a4b7de
```

```json
{ "cancelled": true }
```

Cancelling does not delete `work/<job_id>/`.

### `GET /api/capabilities`

What this host can actually do. Call it before submitting so the user is warned before waiting
through a job that cannot finish.

```bash
curl http://localhost:8000/api/capabilities
```

```json
{
  "platform": "win32",
  "tools": {
    "ffmpeg": true,
    "ffprobe": true,
    "node": true,
    "npx": true,
    "whisper": false,
    "python": true,
    "swift": false
  },
  "stages": {
    "ingest": true,
    "identify": true,
    "transcribe": false,
    "plan": true,
    "compose": true,
    "gates": true,
    "pageerror_gate": false,
    "render": true,
    "deliver": true,
    "face_solve": false
  },
  "degraded": ["transcribe", "pageerror_gate", "face_solve"]
}
```

`degraded` is exactly the keys of `stages` whose value is `false`. Note `stages` here carries two
extra keys beyond the eight job stages: `pageerror_gate` (a sub-check inside `gates`) and
`face_solve` (a step that is not tracked in the job's `stages` array at all; see Known gaps).

### `GET /api/health`

Liveness only.

```bash
curl http://localhost:8000/api/health
```

```json
{ "ok": true }
```

## The eight stages

| # | Name | What it does | Can be `skipped`? |
| --- | --- | --- | --- |
| 1 | `ingest` | `ffprobe` the upload; records `width`, `height`, `duration`, `fps`, `size_bytes`, `has_audio`. `size_bytes` matters because delivery must match the raw A-roll's file size for both IG creators. | No. Fails if the A-roll is missing, `ffprobe` is missing, or there is no video stream. |
| 2 | `identify` | Decides the creator from the footage, never the brief. If `creator` was posted it is taken as-is (`data.source = "caller"`); otherwise `ffmpeg` pulls a 12-frame contact sheet at 1fps and the model picks among the three profiles, returning `creator`, `confidence`, `reasoning`. | No. Fails if `ffmpeg` is missing, extraction fails, or the model returns an unknown creator. |
| 3 | `transcribe` | Extracts 16kHz mono WAV and runs `whisper --model small --word_timestamps True`, flattening segments into a word stream written to `words.json`. The audio is the source of truth; the pasted script is not. | **Yes**, if the A-roll has no audio track, or `whisper`/`ffmpeg` is not on this host. Downstream stages then run with an empty word list, which means beat boundaries are un-anchored and the SRT comes out empty. |
| 4 | `plan` | Model call. Transcript plus brief plus probe to a beat plan (`beats[]` with `start`, `end`, `mode` CARD/FULL_BLEED, `line`, `visual`, `carrier`). Written to `beats.json`. | No. Model-only, so it runs on any host; fails only if the call fails. |
| 5 | `compose` | Scaffolds `build/` from the creator's donor in `reference-builds/` (falling back to `library/templates/vertical-reel`), copies the A-roll to `build/assets/aroll.mp4`, then the model authors `build/index.html`. Em and en dashes are stripped from the result before writing. | No. Model-only; fails if the model returns something that is not HTML. |
| 6 | `gates` | Runs `npx hyperframes lint`, then `validate`, then `inspect` in `build/`, then the Playwright page-error gate (loads the page for 10s, listens for `pageerror`, asserts `window.__timelines` is non-empty). Only `lint` is a hard failure; `validate` and `inspect` results are recorded in `data` for the UI to show. | **Yes**, if `npx` is not found. The page-error sub-check independently reports `{"status": "skipped"}` inside `data.pageerror` when Playwright is not installed or the browser cannot launch. |
| 7 | `render` | `npx hyperframes render -q high --workers $HF_RENDER_WORKERS --video-bitrate 16M`, with `HF_DE_STALL_MS` set. Picks up the mp4 from `build/renders/`. | **Yes**, if `npx` is not found. Otherwise a non-zero rc or a missing mp4 is a hard failure. |
| 8 | `deliver` | Two-pass `loudnorm` (I=-14, TP=-1.0, LRA=9) with `-c:v copy` and AAC 320k to `out/final.mp4`, plus `out/final.srt` from the word stream. `data` reports `size_bytes`, `source_size_bytes` and `two_pass`. | **Yes**, if there is no render to deliver or `ffmpeg` is not found. |

A skipped stage is always reported as `skipped` with a reason in `detail`, never silently passed
as `ok`.

## Known gaps

**The Vision face solve does not run off macOS.** `tools/vision/*.swift` use Apple's Vision
framework and there is no Windows or Linux equivalent in this repo, so `face_solve` requires
macOS plus `swift`. Elsewhere it is skipped with a log line and nothing else. It is not one of
the eight tracked stages, so it will not appear in the job's `stages` array; check
`capabilities().stages.face_solve` instead. This matters because `CLAUDE.md` makes the measured
head solve mandatory before any face geometry: crown from person segmentation, chin and centre-x
from the face contour. Without it, any composition that places graphics near the head is guessing,
and copied constants from a previous video have cropped a crown every single time they have been
tried. On a non-mac host, treat every face-adjacent placement as unverified.

**Whisper, npx and Playwright must be installed for their stages to run.** Without `whisper`,
`transcribe` skips and the whole build is planned against the pasted script, which has differed
from the recorded take often enough to desync a reel. Without `npx`, both `gates` and `render`
skip, so the job ends with an authored `build/index.html` and no video at all. Without
Playwright, the page-error gate skips, and that is the only gate that catches script death: a
ReferenceError before timeline registration renders a page of static DOM while lint, validate and
render all report success.

**One-shot output is a draft, not a delivery.** The repo's quality bar expects roughly three
review rounds, and a technically-correct first render is explicitly a draft. This service
performs no frame QA: nobody has extracted a frame at every beat and read them as images, which
is the only gate that catches the bugs that matter. Nothing here has been visually verified, and
the four rejection classes in `docs/03-quality-bar.md` ("boring / text based", "cheap", "not
premium", "text on my face") are all invisible to `lint`, `validate` and `inspect`. Present
`out/final.mp4` to the user as a first draft awaiting review rounds, never as shipped.
