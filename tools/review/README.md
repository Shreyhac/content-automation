# Reel Review

The feedback loop, vendored. This is the actual running tool, not a description of one.

Before this existed here, `docs/08-review-workflow.md` documented the workflow and said the
tooling lived only in the production repo. A collaborator reading the method could not run it.
Now they can.

```sh
tools/review/rr out/vid47-final.mp4       # local review, opens a browser
tools/review/rr                           # gallery of everything in out/
tools/review/rr share out/vid47-final.mp4 --name "Nader"
tools/review/rr pull vid47
tools/review/rr push vid47
tools/review/rr inbox
```

Symlink it to the repo root if you prefer the short form: `ln -s tools/review/rr rr`.

`docs/08-review-workflow.md` is the operating manual: what the two channels are, what the tool
gets wrong, and the order the fix, reply, push, share sequence has to happen in. Read that.
This file is only about running the code.

---

## What is here

| Path | What |
|---|---|
| `rr` | The launcher. Dispatches to the local server or the share CLI. |
| `review/server.js` | The local player, the markup canvas, the round exporter. |
| `review/share.js` | The client channel CLI: `share`, `pull`, `push`, `inbox`, `shared`, `revoke`, `unshare`. |
| `review/public/` | The player front end. |
| `share/worker.js` | The Cloudflare Worker that serves a private link to a client. |
| `share/setup.js` | One time setup: registers the subdomain, creates the KV namespace, writes `config.json`. |
| `share/public/` | The hosted player, the same UI as the local one. |

Node 18 or newer, plus `ffprobe`, which the pipeline already requires. Nothing else.

---

## Paths, because this moved

In the production repo the tool sat at the repo root, so it resolved `out/` and wrote
`<slug>-feedback-round<N>.md` relative to its own parent directory. Vendored two levels down that
would put both inside `tools/review/`, which is wrong.

The launcher now exports `RR_ROOT`, defaulting to the repo root two levels up, and both Node
entry points honour it. Everything still lands where it should: renders are read from `out/` at
the repo root, and exported rounds are written there too.

Set `RR_ROOT` yourself if you keep deliverables somewhere else.

State that is not tracked in git: `review/data/` (notes and markup frames) and
`share/config.json` (your keys). Both are gitignored.

---

## The hosted channel needs setup once

```sh
tools/review/rr setup
```

It registers a `workers.dev` subdomain, creates a KV namespace, and writes `share/config.json`.
`share/config.example.json` shows the shape: `base`, `adminKey`, `repo`, `tag`, `kvId`,
`ghToken`. The GitHub token needs `repo` scope and points at a private repository whose release
assets hold the renders.

Two things that will bite you, both learned the hard way and both covered in
`docs/08-review-workflow.md`:

- Setup must be re-runnable. A half finished run leaves a KV namespace behind, so it looks one up
  by title before creating a new one. If you create one by hand, put the id in `config.json`.
- A GitHub release asset is capped at 2 GiB. A 4K long form above roughly 45 Mbps will not
  upload, and needs a separately encoded review copy.

---

## Verified

The vendored copy was booted from this repo on 2026-08-15, served the gallery, and discovered
`out/` at the repo root through `RR_ROOT`. Every JS entry point passes `node --check` and the
launcher passes `sh -n`. The Cloudflare Worker was not deployed from here, only syntax checked.
