# Review workflow: the `./rr` manual

`docs/06-delivery.md` §8 is the contract (when to run it, what the two channels are). This is the
manual: how the tool works, what it gets wrong, and what to check before trusting it.

**The tooling is vendored into this repo under `tools/review/`**: `tools/review/rr` (the CLI),
`tools/review/review/` (the local frame.io server and player) and `tools/review/share/` (the
Cloudflare Worker for the hosted/client channel). In the production repo the same three live at
the root as `./rr`, `review/` and `share/`, so paths quoted from a production session are one
level shallower than the ones here. This doc is the accumulated operating knowledge for both,
kept alongside the code so a fresh session or a new collaborator does not have to relearn it by
breaking it once.

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
- **Media responses must not be cached, and "nothing has changed" is a chain to walk.** The local
  player's byte-range media responses carried no cache headers, so after a re-render to the same
  `out/` path a browser silently replayed its cached copy of the previous version. The owner
  watched "v13", saw v12, and reported "nothing has changed" while the disk and the served bytes
  were both correct. Version URLs `/media/<slug>/<v>` all resolve to the same file path, so caching
  any media response is wrong by construction and both paths now send `cache-control: no-store`.
  When a delivery "didn't change", check the chain in order: **disk hash, then served bytes (a
  `curl` range request plus `cmp`), then browser cache.**
- **A markup drawn over the client's own face is placement approval.** One note's box spanned the
  presenter's chin. The client had already priced in the overlap, so honouring the drawn geometry beat
  re-deriving a "safer" placement nobody asked for.
- **Pre-existing faults are not this round's scope.** A collision that is identical in the already
  delivered cut gets flagged, not silently fixed. Re-cutting an approved frame nobody asked about
  spends a round and invites a note.
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

### `share` caps at 2 GiB, and a 4K long-form does not fit

GitHub rejects a release asset over **2 GiB (2,147,483,648 bytes)** with
`HTTP 422: Validation Failed ... size must be less than 2147483648`, and **it fails only after the
whole file has been staged and uploaded**, so discovering it costs a full upload cycle.

At 373s (one long-form's length) the ceiling is roughly **46 Mbps**. vid62 v2 squeaked under at
45.4 Mbps and 2.0 GB; v3 at 59.1 Mbps and 2.63 GB did not.

**The fix is two files, not a lower-quality delivery.** Keep the full-quality file as the
deliverable and encode a separate review copy under the cap:

```bash
nohup ffmpeg -i out/vidNN-final.mp4 -c:v libx264 -b:v 42M -maxrate 48M -bufsize 96M \
  -preset medium -pix_fmt yuv420p -g 12 -keyint_min 12 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a copy -movflags +faststart -y out/vidNN-final-review.mp4 &
```

then `rr share out/vidNN-final-review.mp4 --as vidNN --name "<client>"`.

- **Run the encode detached.** A 4K re-encode runs past the tool timeout, and a job killed
  mid-write leaves a file with **no `moov` atom** that probes as corrupt while looking perfectly
  plausible on disk at 1.94 GB.
- **Say in the caption pack which file is which.** The share link now carries the lower-quality
  file, so "the one on the link" is not the one to upload. vid62 ships `out/vid62-final.mp4` at
  59.1 Mbps and reviews `out/vid62-final-review.mp4` at 42.9.

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

## Reading a note correctly, before fixing anything

- **Resolve "the shot from before" to a literal filename.** One project held four fn-key takes
  that only look alike: `fnkey.mp4` (tight bed crop), `fnkey2.mp4` (marble desk),
  `fnkey-broll-raw.mp4` (wooden desk), and `fnkey3.mp4`/`fnkey3b.mp4` (dim bed, dock visible, fn
  key legible), the last pair being what actually plays at 0:02 and 0:05. "The shot from 0:02"
  was written down and a different take shipped twice running. A callback only works if it is the
  same footage: "same setup, different take" reads as an error. Read the filename out of the
  composition and diff a frame against it. Never reason from the folder name.
- **Verify a claimed defect against the master before assuming it is your encode.** A client
  reported repeated audio; the master had the same words, and what they were hearing was the cut
  tightening a halting phrase. Transcribe ±1.6s of the join in isolation first. See
  `docs/05-audio-and-sfx.md`.
- **Diagnose before theorizing.** A "won't open" report got an untested codec theory stated as
  fact, which drove two render cycles building an alternate-codec file, and the theory was wrong.
  See `docs/07-troubleshooting.md` for the three checks that each take seconds.
- **A vague note is not a spec: ask rather than guess.** "This is bad" against a hook got a
  guessed redesign, which was rebuilt again the next round. One question costs a message; a
  guessed rebuild costs a render round and burns a round of the owner's patience. Ask what the
  replacement should do, then build it once.
- **Say the time cost before the slow step, not after being asked.** On vid57's native-4K round
  the render/deliver cycle went from about 4 minutes to about 20 (render 1m34s to 5m45s, byte-match
  delivery about 50s to about 14 minutes). It was backgrounded silently and the owner had to
  interrupt with "why is this taking so much time". A genuinely-running multi-minute encode with
  no status update is indistinguishable from a hang.

---

## What no gate replaces here

Frame-pinned markup and written notes are read by a person, not validated by a script: the closest
thing to a gate in this loop is the discipline of actually reading every markup image before acting
and writing a `reply` for everything addressed. Treat a review round the same as a render round:
nothing here is "done" until you've re-opened the link yourself and confirmed the old notes read as
answered, not just fixed.
