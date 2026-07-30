# Setup

macOS. Run `bash tools/check-env.sh` after installing; it verifies everything below and prints
what is missing.

---

## Required

```bash
# Homebrew, if not already present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install ffmpeg node python@3.12 expat
pip3 install --user openai-whisper playwright
python3 -m playwright install chromium
```

| Tool | Used for | Notes |
|---|---|---|
| `ffmpeg` / `ffprobe` | Everything. Transcode, crop, bake, concat, loudnorm, frame extraction. | |
| `node` 18+ | `npx hyperframes` pulls itself. | No global install needed. |
| `python3` | Captions, SFX beds, chunk planning, solvers. | Standard library only, plus playwright. |
| `whisper` | Word-level transcripts. | `--model small` is the default. |
| `playwright` + chromium | Real page capture, and the pageerror gate. | |
| `swift` | The Vision measurement tools. | Ships with Xcode command line tools. |

Optional, for auditioning b-roll from YouTube:

```bash
pip3 install --user yt-dlp
```

---

## Machine-specific gotchas

These are real on the machine this system was built on and will save an hour.

### Broken pyexpat

`yt-dlp`, `pip` and `venv` fail with an expat error. Prefix affected commands:

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib yt-dlp ...
```

### zsh

- **Empty globs kill a chain.** `rm renders/work-* && npx hyperframes render` silently skips the
  render when the glob matches nothing. This has bitten five separate times. Cleanup is always a
  separate command, or `rm -f ... 2>/dev/null || true`. In watch loops use `find -name '*.mp4'`,
  never a glob.
- **`set -- $var` does not word-split** (unlike bash), so `for spec in "a b c"; do set -- $spec`
  passes the whole string as `$1`. Use explicit `${spec%%:*}` parsing.

### ffmpeg

- **It reads stdin and eats a `while read` loop.** Put `-nostdin` on every ffmpeg call inside a
  read loop, or only the first line is processed.
- **libx264 refuses odd heights.** 900x333 fails, 900x334 works.

### macOS

`timeout` does not exist by default.

---

## HyperFrames

```bash
npx hyperframes --version
npx hyperframes doctor      # environment check
npx hyperframes skills      # re-install .claude/skills if they are ever missing or stale
```

The skills in `.claude/skills/` are tracked in git and a fresh Claude Code session discovers them
automatically. If they go missing, run `npx hyperframes skills` and restart the session.

### Render environment

```bash
export HF_DE_STALL_MS=420000
```

**Not optional on heavy 4K or three.js compositions.** The default 60-second no-frame-progress
watchdog kills healthy renders whose slow frames legitimately take longer on an 8GB machine. The
symptom is a render dying at the *same frame number* every time. See `docs/07-troubleshooting.md`.

Worker counts are machine-dependent:

| Machine | Setting |
|---|---|
| 8GB | `--workers 2 --no-low-memory-mode` is the safe default; `--workers 3` when memory is free |
| 16GB+ | `--workers 3` to `4` |

On <= 8GB, HyperFrames auto-forces low-memory mode (one worker plus screenshot capture) and
Chrome leaks per screenshot until a session crashes at a deterministic frame. Both levers together
fix it: transcode every A-roll to `scale=1080:1920` (an oversized master is 2.25x the pixels), and
pass `--no-low-memory-mode --workers 4` (needs about 5GB free).

### Disk

A 4K render round costs about 800MB. Prune chunk `renders/` directories between rounds. Renders
can fail below about 1GB free.

---

## Working directories

Nothing heavy belongs in this repo. `.gitignore` already excludes:

```
work/           per-video working projects
**/renders/     draft renders
**/qa*/         frame QA dumps
**/assets/*.mp4 transcoded A-roll and b-roll
out/            deliverables
*.mp4 *.mov *.wav  (except reference-cuts/)
```

Raw A-roll masters stay outside the repo entirely. Reference builds ship code plus an `ASSETS.md`
saying what media they expected and where it came from.

---

## Verify

```bash
bash tools/check-env.sh
```

It should print `ALL CHECKS PASSED`. If it does not, it names the missing piece and the install
command.
