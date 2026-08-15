-- Reel Factory demo schema. Run once in the Supabase SQL editor.
-- The web server treats Supabase as a MIRROR, never as the source of truth:
-- the local JSON store stays authoritative so a slow network cannot blank the demo.

create table if not exists rf_sessions (
  id          text primary key,
  provider    text,
  demo        boolean default false,
  created_at  timestamptz default now()
);

create table if not exists rf_jobs (
  id          text primary key,
  filename    text,
  created_at  timestamptz default now()
);

create table if not exists rf_notes (
  id          text primary key,
  job_id      text references rf_jobs(id) on delete cascade,
  t           double precision,          -- seconds into the cut
  rect        jsonb,                     -- {x,y,w,h} normalised 0 to 1, so it survives any player size
  text        text,
  created_at  timestamptz default now()
);

create index if not exists rf_notes_job_idx on rf_notes(job_id);

-- Demo posture: the server holds the key and is the only writer, so RLS is on
-- with no public policy. Do not hand the anon key to the browser in this build.
alter table rf_sessions enable row level security;
alter table rf_jobs     enable row level security;
alter table rf_notes    enable row level security;
