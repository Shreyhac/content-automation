# Reel Review · the feedback loop

> Vendored into this repo at `tools/review/`. Invoke it as `tools/review/rr`, and note that
> `review/data/` below now means `tools/review/review/data/`. Renders are still read from `out/`
> at the repo root, and rounds are still exported there. See `tools/review/README.md`.

A local frame.io for this repo. Instead of sending screenshots and describing what is wrong,
open the render, scrub to the frame, draw on it, and type the note. Pressing **Send to editor**
writes every open note to `<slug>-feedback-round<N>.md` at the repo root, which is the file the
editor reads at the start of the next round.

No dependencies beyond Node 18+ and `ffprobe` (already required by the pipeline).

## Running it

```sh
./rr out/vid47-final.mp4          # open a render (browser opens automatically)
./rr                              # gallery: everything already in review + the newest files in out/
./rr out/vid47-final.mp4 --as vid47 --label "paper split"
```

Options: `--as <slug>` force the project, `--label <text>` name the version,
`--port 7788`, `--no-open`. `npm run review -- out/vid47-final.mp4` works too.

The slug is derived from the filename (`out/vid47-final.mp4` → `vid47`), so re-rendering the
same deliverable and reopening it stacks a **v2** under the same project rather than starting over.

## Leaving notes

| | |
|---|---|
| `space` | play / pause |
| `←` `→` | one frame (`shift` = one second) |
| `1`–`5` | pointer · pin · box · arrow · pen |
| `C` | comment on this frame |
| `G` | note about the **whole video** |
| `⌘⏎` | save · `esc` cancel |

Draw first, and the composer opens by itself. The paused frame plus your markup is baked into a
JPEG under `review/data/<slug>/markup/`, so the editor sees the exact thing you circled, not a
description of it.

**Whole-video notes** ("change the theme", "SFX too loud") are pinned to the moment you wrote
them but are exported in their own section, marked as applying to the entire cut. Any note can be
flipped between the two with the *whole video* / *pin to frame* action on its card.

**Compare** puts the previous version under a draggable wipe against the current one, both scrubbing
together.

## What the editor gets

`<slug>-feedback-round<N>.md`: whole-video notes first, then a frame-note table, then one section
per note with its timecode, frame number, and the path to the markup JPEG.

The round file is **never overwritten**: the exporter skips past any existing round number,
including hand-written ones.

## Replying

Notes live in `review/data/<slug>/comments.json`. The editor sets `status` to `resolved` and fills
in `reply` as each one is addressed; both show up on the card in the UI on the next reload. So the
next round opens with your old notes struck through and answered, and the new render as v2.

---

## Sending a cut to a client

Clients get a private hosted link. Same player, same notes, no install, and it
stays up when your Mac is off.

**Nothing here needs a card.** The renders live as assets on a **private GitHub release**
(2GB per file, free, your existing `gh` login); the worker proxies them with a token, so the repo
stays private and the client never sees GitHub. Comments and markup frames live in **Cloudflare
KV**. R2 was the first choice and was dropped because it demands billing details; Vercel's free
tier is explicitly non-commercial; Supabase free caps files at 50MB and storage at 1GB, which
does not fit a 758MB long-form.

**One-time:**

```sh
./rr setup
```

Creates the private repo and its release, makes the KV namespace, deploys the worker, and writes
`share/config.json` (your keys, gitignored). Safe to re-run.

**Every round:**

```sh
./rr share out/vid48-final.mp4 --name "Client Studio"     # prints the private link
./rr inbox                                                 # anything a client left, unpulled
./rr pull vid48                                            # notes land in review/data/vid48/
./rr                                                       # open them locally, with markup frames
./rr push vid48                                            # send replies + resolved marks back
./rr shared                                                # what is live, who has commented
```

**Answering the client.** After fixing, set `"status": "resolved"` and write a one-line `"reply"`
on each note in `review/data/<slug>/comments.json`, then `./rr push <slug>`. The client sees a
green tick and your reply under their own note next time they open the link, so a round that took
three days does not look ignored. `push` sends the full local state, so clearing a reply also
propagates.

**Knowing there is something to read.** `./rr inbox` lists every client note that has not been
pulled yet, across all shared projects. Run it at the start of a session.

`share` re-run on a new render of the same file stacks it as **v2** on the *same link*, so the
client can wipe the old cut against the new one and you never send a second URL.

`pull` merges: the client's text wins, your local `status` and `reply` survive, and pulling twice
never duplicates. From there it is identical to a note left on your own machine, including the
round export.

**Phones work.** Clients open these links from WhatsApp, so the player collapses to one column
under 900px: video on top, notes underneath, a single scrolling toolbar, and the composer as a
bottom sheet. Drawing works with a finger.

**The link:** `https://reel-review.<subdomain>.workers.dev/v/vid48?k=<22-char key>`. Anyone
holding it can comment; nobody can list your other clients' work, there is no index page, and the
version records are stripped of the repo and asset id before they reach the browser. `./rr revoke
vid48` rotates the key and kills the old link. `./rr unshare vid48 --yes` deletes the notes and
the uploaded renders (local copies survive).

**Limits:** 2GB per render, and Cloudflare's free Workers plan allows 100,000 requests/day, which
is far more than a handful of reviewers scrubbing. Keep an eye on nothing.
