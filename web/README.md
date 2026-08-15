# Reel Factory: the web demo

The product surface for the pipeline in this repo. Upload a raw take, watch it get edited, leave
notes on the frame, download the cut.

```bash
node web/server.js          # http://localhost:8787
node web/server.js --port 9000
```

Node 18 or newer. **No npm install, no CDN, no build step.** On a hackathon floor the wifi is the
least reliable component in the room, so nothing here needs it. Fonts, styles and scripts are all
local files.

---

## What is real and what is staged

Being straight about this matters, because a judge will ask.

**Real:** the upload, the review canvas, the notes (stored, listed, seekable, deletable), the
download, the range requests that make scrubbing work, and the reel you are watching, which is
`reference-cuts/shreyansh-vid67-launch-your-agent.mp4`, an actual shipped and owner-approved film.

**Staged:** the pipeline stages between upload and result. They run on a timer of about 38 seconds
instead of invoking ffmpeg, whisper, HyperFrames and the render. Those stage names are not
decoration, they are the real steps in `docs/01-pipeline.md`, but a genuine 4K render takes 10 to
25 minutes and has hard-reset an 8GB machine before now. That does not belong in a demo slot.

The real pipeline is the rest of this repository. `tools/` runs it.

---

## Storage

Local JSON at `web/data/store.json` by default. Nothing else is required.

To mirror into Supabase, copy `config.example.json` to `config.local.json` (gitignored) and fill in
the two values, then run `schema.sql` in the Supabase SQL editor:

```json
{ "supabaseUrl": "https://<project-ref>.supabase.co", "supabaseKey": "<service_role key>" }
```

The mirror is **fire and forget on purpose**. The local store stays authoritative and a Supabase
error is logged and swallowed rather than surfaced, because a demo must not go blank because a
REST call timed out. If you want Supabase to be the source of truth, that is a different build.

The server holds the key and is the only writer, so `schema.sql` enables RLS with no public policy.
Do not move the key into the browser in this build.

---

## Auth

Two ways in, and both are honest about what they are.

- **Continue with Claude / Continue with Codex.** Neither Anthropic nor OpenAI publishes a
  third-party OAuth flow a site like this can use, so these pick a provider and then ask for that
  provider's API key. There is no fake consent screen anywhere in this build.
- **Paste a key directly**, with a provider picker.
- **Skip, use demo account.** The path to use on stage. Nobody should be typing a credential in
  front of an audience.

A pasted key is validated by **shape only** (prefix plus length) and is never sent anywhere, not to
this server and not to the provider. The session row records which provider was chosen, nothing
more.

---

## API

```
GET    /api/health                     -> {ok, artefact, supabase}
POST   /api/session                    -> {sessionId, demo, provider}
POST   /api/jobs                       -> job view
GET    /api/jobs/:id                   -> job view (poll this)
GET    /api/jobs/:id/notes             -> {notes:[...]}
POST   /api/jobs/:id/notes             -> {note}
DELETE /api/jobs/:id/notes/:noteId     -> {ok}
GET    /api/artefact                   -> the reel, with range support
```

Job progress is computed from elapsed time rather than from a stored counter, so refreshing the
page mid-run resumes at the right stage instead of starting over.

Note rectangles are stored **normalised, 0 to 1**. A note left on a laptop lands in the same place
on a phone.

---

## If the video does not play

`/api/artefact` serves the first file that exists from a candidate list, so the demo degrades to
something that plays rather than to a broken element. If all of them are missing it returns 503
with a readable message. Check with:

```bash
curl -s localhost:8787/api/health
```

Drop any mp4 at `web/public/media/demo.mp4` as a last-resort fallback.
