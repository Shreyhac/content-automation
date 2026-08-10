# Review workflow: the `./rr` manual

`docs/06-delivery.md` §8 is the contract (when to run it, what the two channels are). This is the
manual: how the tool works, what it gets wrong, and what to check before trusting it.

**The tooling itself is not in this repo.** It lives in the production repo as `review/` (a local
frame.io) plus the `./rr` CLI, and as a Cloudflare Worker for the hosted/client channel. This doc
is the accumulated operating knowledge for both, kept here so a fresh session or a new collaborator
does not have to relearn it by breaking it once.

---

## Local review (`review/`)

`./rr out/vidNN-final.mp4` opens a local player: scrub, draw a box/arrow/pen/pin on a paused frame,
type a note. **Send to editor** writes every open note to `vidNN-feedback-round<N>.md` at the repo
root.

- **Two kinds of note, and they are not interchangeable.** A **frame note** (timecode + drawing) is
  a local fix. A **whole-video note** ("change the theme," "SFX too loud") is written at some
  timecode but applies to the entire cut regardless of where it was written: export it into its
  own section and read it that way. Mixing the two in prose is how global notes end up half-applied.
- **The markup JPEG is the note, not the caption on it.** The paused frame with the drawing baked
  in lands in `review/data/<slug>/markup/`. Read it as an image before acting: a note that says
  only "this is off" plus a drawn box is unambiguous in a way no text description is. A drawn box
  can also enclose a second fault the note's text never mentions; read the whole frame the box
  points at, not just the element the text names.
- **Re-renders stack as versions under the same slug**, so the reviewer can wipe v1 against v2 in
  the player. The slug is derived from the filename with `-final`/`-vN` stripped.
- **A version row is metadata pointing at a shared output path, not necessarily an independent
  copy.** If every version points at the same `out/<slug>-final.mp4` and a new render overwrites
  that path, every prior version silently becomes the new render: there is nothing left to diff
  against. Confirm the tool copies the outgoing file to a version-specific path (or do it by hand)
  before delivering a second round to the same slug.
- **Close the loop in `comments.json`**: set each addressed note's `status` to `resolved` and write
  a one-line `reply`. Both render on the card, so the next round opens with old notes already
  answered. **A note left `open` reads as ignored**, whether or not it actually was.
- **Never overwrite an existing `-feedback-roundN.md`.** The exporter scans the repo root, skips
  past every existing round number, and writes with the `wx` flag (fails rather than clobbers).
  This was learned by losing one: an early test run of the tool silently destroyed a hand-written,
  untracked `-feedback-round1.md` with no way to recover it from git. **Any generator that writes
  into the repo root must assume a human may have written there first**, and refuse to overwrite
  rather than assume it's safe to.
- **Reading order matters as much as reading the notes.** "Go through the file again" after fixing
  one reported defect is worth taking literally: a second pass surfaced defects the reviewer had
  not flagged and could not have (duplicate on-screen/spoken text, a caption box that had crept
  back into a safe-zone violation already fixed once before).

---

## Sending a cut to a client (hosted channel)

`./rr share out/vidNN-final.mp4 --name "<client>"` prints one private link. `./rr pull vidNN` merges
the client's notes and markup frames into `review/data/vidNN/` as `source: "client"`, and from
there they are indistinguishable from local notes for the resolve/reply workflow above.

### Why this hosting shape, specifically

Renders sit as assets on a **private GitHub release**, proxied by a Cloudflare Worker holding a
token; comments and markup sit in Worker KV. This combination won on a genuine survey of the free
tiers, not by default:

- R2 is 10GB free with free egress but will not activate without billing details on file.
- Vercel Hobby is licensed non-commercial/personal-use only.
- Supabase free caps a single file at 50MB and total storage at 1GB: too small for most reels and
  every long-form.
- **GitHub release assets are 2GB each, free, and private**, and they support byte-range requests:
  `GET /repos/:o/:r/releases/assets/:id` with `Accept: application/octet-stream` redirects (302) to
  a signed URL that answers `206 Partial Content`, which is what makes scrubbing work at all. Cache
  that signed URL (it lasts about an hour) or every seek spends an API call against the 5,000/hour
  limit.

### Operating notes

- **A share link must not be able to enumerate other clients.** The worker has no index route,
  every path is guarded by a per-project key, and version records returned to the browser are
  stripped of the underlying repo and asset id.
- **Cloudflare's static-assets layer answers before the Worker code runs, by default.** `/` served
  `index.html` from static assets and never reached the handler until `html_handling = "none"` and
  `not_found_handling = "none"` were set.
- **A new `workers.dev` subdomain must be registered once** before any deploy succeeds, and the
  first DNS resolution after registering can fail for a few seconds: retry rather than treat the
  first failure as terminal.
- **Setup must be idempotent.** A half-finished setup run leaves a KV namespace behind; look it up
  by title before creating a new one, or re-running setup duplicates it.
- **A hosted link is opened on a phone, and the player must assume that.** Without
  `<meta name="viewport">`, mobile browsers lay out at a fixed 980px and scale the whole page
  down, so the breakpoints never fire, silently. The player chrome on a phone also needs to be
  one horizontally-scrolling toolbar; a wrapping one ate the stage entirely and left the video
  41px tall.
- **`./rr push` sends the FULL local state, not only newly-answered notes**, so retracting a reply
  propagates correctly rather than leaving a stale one visible. `pull` alone (never following up
  with resolved statuses via `push`) leaves the client staring at notes that look ignored for days.
- **Run `./rr inbox` at the start of any session where a cut is out for review.** Client notes land
  whenever the client watches, which is very often while you are already mid-build on the next
  thing: an overnight round is easy to miss without checking.
- **Cloudflare 403s a plain `python-urllib` request.** Use the CLI or `curl` against the worker, not
  a bare Python HTTP client, when scripting against it.

### The fix → reply → push → share sequence is order-sensitive

Sharing a new render **before** writing `status`/`reply` into the previous round's `comments.json`
and pushing means the client's next open of the link shows all prior notes still flagged open,
reasonably read as "my feedback was ignored" even when every one of them was actually addressed
in the new cut. The order that keeps the loop legible: fix, write `resolved` + `reply` for every
note addressed, `push`, **then** share the new render.

### A staging bug that cost a source file (fixed, worth knowing the shape of)

An early version of the share step staged its renamed upload copy inside the **source** directory
before uploading. The slugging function lowercased names, so `NAME-v2.mp4` and `name-v2.mp4` were
the same inode on a case-insensitive filesystem (macOS default): the "copy" was a no-op and the
subsequent cleanup `rm` deleted the original. Any deliverable with uppercase letters plus a `-vN`
suffix was exposed. The fix is to always stage into a system temp directory, never into the source
directory, before any rename/upload/cleanup sequence: a pattern worth checking in any script that
copies-then-deletes a working file.

---

## What no gate replaces here

Frame-pinned markup and written notes are read by a person, not validated by a script: the closest
thing to a gate in this loop is the discipline of actually reading every markup image before acting
and writing a `reply` for everything addressed. Treat a review round the same as a render round:
nothing here is "done" until you've re-opened the link yourself and confirmed the old notes read as
answered, not just fixed.
