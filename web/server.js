#!/usr/bin/env node
/* Reel Factory web demo.
 *
 * Node built-ins only. No npm install, no CDN, no build step: on a hackathon
 * floor the wifi is the least reliable component, so nothing here needs it.
 *
 *   node web/server.js            -> http://localhost:8787
 *   node web/server.js --port 9000
 *
 * Storage is a local JSON file by default. If web/config.local.json exists and
 * carries Supabase credentials, notes and sessions are mirrored there too. The
 * local file stays authoritative either way, deliberately: a demo must not go
 * blank because a REST call timed out.
 */
'use strict';
const http = require('http');
const fs   = require('fs');
const fsp  = fs.promises;
const path = require('path');
const url  = require('url');
const crypto = require('crypto');

const HERE   = __dirname;
const ROOT   = path.resolve(HERE, '..');
const PUBLIC = path.join(HERE, 'public');
const DATA   = path.join(HERE, 'data');
const STORE  = path.join(DATA, 'store.json');
const CONFIG = path.join(HERE, 'config.local.json');

/* ── the artefact the demo actually serves ─────────────────────────────────
 * A real, shipped, owner-approved reel. First existing candidate wins, so the
 * demo degrades to something that plays rather than to a broken <video>. */
const CANDIDATES = [
  path.join(ROOT, 'reference-cuts', 'shreyansh-vid67-launch-your-agent.mp4'),
  path.join(ROOT, 'reference-cuts', 'shreyansh-vid63-strix.mp4'),
  path.join(ROOT, 'reference-cuts', 'nader-vid62-incogni-short.mp4'),
  path.join(HERE, 'public', 'media', 'demo.mp4'),
];
function pickArtefact() {
  for (const p of CANDIDATES) { try { if (fs.statSync(p).size > 0) return p; } catch {} }
  return null;
}
const ARTEFACT = pickArtefact();

/* ── stages. Real names, from this repo's actual pipeline. ────────────────
 * The total is ~38s so the whole demo fits inside a slot. */
const STAGES = [
  { key: 'probe',    label: 'Probing the master',            detail: 'ffprobe: resolution, bitrate, colour transfer', ms: 2200 },
  { key: 'whisper',  label: 'Transcribing, word level',      detail: 'whisper small, word timestamps',                ms: 6000 },
  { key: 'beats',    label: 'Finding beats off the envelope',detail: 'RMS onsets, not the transcriber',               ms: 3200 },
  { key: 'face',     label: 'Solving face geometry',         detail: 'Vision: crown, chin, centre-x per window',      ms: 5200 },
  { key: 'compose',  label: 'Composing the timeline',        detail: 'HyperFrames + GSAP, scenes on word onsets',     ms: 6400 },
  { key: 'gate',     label: 'Running the safe zone gate',    detail: 'guard.py: paint tests, bands, text on text',    ms: 4200 },
  { key: 'render',   label: 'Rendering',                     detail: '2160x3840, 30fps',                              ms: 7200 },
  { key: 'deliver',  label: 'Checking the delivery',         detail: 'bitrate against master, loudnorm, em dashes',   ms: 3400 },
];
const TOTAL_MS = STAGES.reduce((a, s) => a + s.ms, 0);

/* ── tiny persistent store ────────────────────────────────────────────────── */
let store = { sessions: {}, jobs: {}, notes: {} };
let supa = null;

async function loadStore() {
  await fsp.mkdir(DATA, { recursive: true });
  try { store = JSON.parse(await fsp.readFile(STORE, 'utf8')); }
  catch { /* first run */ }
  for (const k of ['sessions', 'jobs', 'notes']) if (!store[k]) store[k] = {};
}
let saveTimer = null;
function saveStore() {                       // debounced, so polling never thrashes the disk
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    fsp.writeFile(STORE, JSON.stringify(store, null, 2)).catch(() => {});
  }, 120);
}

async function loadConfig() {
  try {
    const c = JSON.parse(await fsp.readFile(CONFIG, 'utf8'));
    if (c.supabaseUrl && c.supabaseKey) {
      supa = { url: c.supabaseUrl.replace(/\/+$/, ''), key: c.supabaseKey };
      console.log('  supabase: mirroring to ' + supa.url);
    }
  } catch { /* optional by design */ }
}

/* Fire and forget. A Supabase failure must never surface to the browser:
 * the local store is authoritative and the mirror is a bonus. */
function mirror(table, row) {
  if (!supa) return;
  const body = JSON.stringify(row);
  const req = new URL(supa.url + '/rest/v1/' + table);
  const mod = req.protocol === 'http:' ? require('http') : require('https');
  const r = mod.request(req, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'apikey': supa.key,
      'authorization': 'Bearer ' + supa.key,
      'prefer': 'resolution=merge-duplicates',
      'content-length': Buffer.byteLength(body),
    },
  }, (res) => res.resume());
  r.on('error', (e) => console.warn('  supabase mirror failed (ignored): ' + e.message));
  r.write(body); r.end();
}

/* ── helpers ──────────────────────────────────────────────────────────────── */
const id = (n = 9) => crypto.randomBytes(n).toString('base64url').slice(0, n + 3);

function json(res, code, obj) {
  const b = Buffer.from(JSON.stringify(obj));
  res.writeHead(code, { 'content-type': 'application/json; charset=utf-8', 'content-length': b.length, 'cache-control': 'no-store' });
  res.end(b);
}
function readBody(req, limit = 1 << 20) {
  return new Promise((resolve, reject) => {
    let n = 0; const chunks = [];
    req.on('data', (c) => { n += c.length; if (n > limit) { reject(new Error('body too large')); req.destroy(); return; } chunks.push(c); });
    req.on('end', () => {
      const s = Buffer.concat(chunks).toString('utf8');
      if (!s) return resolve({});
      try { resolve(JSON.parse(s)); } catch (e) { reject(new Error('bad json')); }
    });
    req.on('error', reject);
  });
}

const MIME = { '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8', '.js':'text/javascript; charset=utf-8',
  '.json':'application/json', '.mp4':'video/mp4', '.woff2':'font/woff2', '.svg':'image/svg+xml',
  '.png':'image/png', '.jpg':'image/jpeg', '.ico':'image/x-icon' };

/* Range support is not optional: without a 206 the scrubber cannot seek,
 * and the review step is the whole point of the product. */
function serveFile(req, res, abs) {
  let st; try { st = fs.statSync(abs); } catch { return json(res, 404, { error: 'not found' }); }
  if (st.isDirectory()) return json(res, 404, { error: 'not found' });
  const type = MIME[path.extname(abs).toLowerCase()] || 'application/octet-stream';
  const range = req.headers.range;
  if (range && /^bytes=/.test(range)) {
    const m = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
    let start = m && m[1] ? parseInt(m[1], 10) : 0;
    let end   = m && m[2] ? parseInt(m[2], 10) : st.size - 1;
    if (isNaN(start) || isNaN(end) || start > end || end >= st.size) {
      res.writeHead(416, { 'content-range': `bytes */${st.size}` }); return res.end();
    }
    res.writeHead(206, {
      'content-type': type,
      'content-length': end - start + 1,
      'content-range': `bytes ${start}-${end}/${st.size}`,
      'accept-ranges': 'bytes',
      'cache-control': 'no-store',
    });
    return fs.createReadStream(abs, { start, end }).pipe(res);
  }
  res.writeHead(200, { 'content-type': type, 'content-length': st.size, 'accept-ranges': 'bytes',
                       'cache-control': type.startsWith('video') ? 'no-store' : 'no-cache' });
  fs.createReadStream(abs).pipe(res);
}

/* ── job state is computed from elapsed time, never from a stored counter ──
 * so a page refresh mid-run resumes correctly instead of restarting. */
function jobView(job) {
  const elapsed = Date.now() - job.startedAt;
  let acc = 0, stageIndex = 0;
  const stages = STAGES.map((s, i) => {
    const from = acc; acc += s.ms;
    let state = 'pending';
    if (elapsed >= acc) state = 'done';
    else if (elapsed >= from) { state = 'running'; stageIndex = i; }
    return { key: s.key, label: s.label, detail: s.detail, ms: s.ms, state };
  });
  const done = elapsed >= TOTAL_MS;
  if (done) stageIndex = STAGES.length;
  return {
    id: job.id, filename: job.filename, state: done ? 'done' : 'running',
    stageIndex, stages, elapsedMs: Math.min(elapsed, TOTAL_MS), totalMs: TOTAL_MS,
    videoUrl: done ? '/api/artefact' : null,
    creator: job.creator,
  };
}

/* ── routes ───────────────────────────────────────────────────────────────── */
async function api(req, res, pathname) {
  const seg = pathname.split('/').filter(Boolean);   // ['api', ...]

  if (pathname === '/api/health') {
    return json(res, 200, { ok: true, artefact: ARTEFACT ? path.basename(ARTEFACT) : null, supabase: !!supa });
  }

  if (pathname === '/api/session' && req.method === 'POST') {
    const b = await readBody(req);
    const sid = id();
    store.sessions[sid] = {
      id: sid, provider: b.provider || 'demo', demo: !b.provider || b.provider === 'demo',
      createdAt: new Date().toISOString(),
    };
    saveStore();
    mirror('rf_sessions', store.sessions[sid]);
    return json(res, 200, { sessionId: sid, demo: store.sessions[sid].demo, provider: store.sessions[sid].provider });
  }

  if (pathname === '/api/jobs' && req.method === 'POST') {
    const b = await readBody(req);
    const jid = id();
    store.jobs[jid] = {
      id: jid, filename: String(b.filename || 'upload.mp4').slice(0, 200),
      sizeBytes: Number(b.sizeBytes) || 0, creator: b.creator || 'shreyansharora05',
      startedAt: Date.now(), createdAt: new Date().toISOString(),
    };
    store.notes[jid] = [];
    saveStore();
    mirror('rf_jobs', { id: jid, filename: store.jobs[jid].filename, created_at: store.jobs[jid].createdAt });
    return json(res, 200, jobView(store.jobs[jid]));
  }

  // /api/jobs/:id  and  /api/jobs/:id/notes[/:noteId]
  if (seg[0] === 'api' && seg[1] === 'jobs' && seg[2]) {
    const job = store.jobs[seg[2]];
    if (!job) return json(res, 404, { error: 'no such job' });

    if (!seg[3] && req.method === 'GET') return json(res, 200, jobView(job));

    if (seg[3] === 'notes') {
      const list = store.notes[job.id] || (store.notes[job.id] = []);
      if (req.method === 'GET') return json(res, 200, { notes: list });
      if (req.method === 'POST') {
        const b = await readBody(req);
        const r = b.rect || {};
        const note = {
          id: id(6),
          t: Math.max(0, Number(b.t) || 0),
          rect: { x: +r.x || 0, y: +r.y || 0, w: +r.w || 0, h: +r.h || 0 },   // normalised 0..1
          text: String(b.text || '').slice(0, 2000),
          createdAt: new Date().toISOString(),
        };
        list.push(note); list.sort((a, c) => a.t - c.t);
        saveStore();
        mirror('rf_notes', { id: note.id, job_id: job.id, t: note.t, text: note.text, rect: note.rect, created_at: note.createdAt });
        return json(res, 200, { note });
      }
      if (req.method === 'DELETE' && seg[4]) {
        const i = list.findIndex((n) => n.id === seg[4]);
        if (i >= 0) list.splice(i, 1);
        saveStore();
        return json(res, 200, { ok: true, removed: i >= 0 });
      }
    }
  }

  if (pathname === '/api/artefact') {
    if (!ARTEFACT) return json(res, 503, { error: 'no demo artefact on disk. See web/README.md' });
    return serveFile(req, res, ARTEFACT);
  }

  return json(res, 404, { error: 'no such endpoint' });
}

const server = http.createServer(async (req, res) => {
  let pathname = '/';
  try { pathname = decodeURIComponent(url.parse(req.url).pathname); } catch { pathname = '/'; }

  try {
    if (pathname.startsWith('/api/')) return await api(req, res, pathname);

    if (pathname === '/')    return serveFile(req, res, path.join(PUBLIC, 'index.html'));
    if (pathname === '/app' || pathname === '/app/') return serveFile(req, res, path.join(PUBLIC, 'app.html'));

    // static, with traversal refused
    const abs = path.join(PUBLIC, pathname);
    if (!abs.startsWith(PUBLIC)) return json(res, 403, { error: 'forbidden' });
    return serveFile(req, res, abs);
  } catch (e) {
    console.error('  500 ' + pathname + ': ' + e.message);
    if (!res.headersSent) json(res, 500, { error: e.message });
  }
});

(async function main() {
  const args = process.argv.slice(2);
  let port = 8787;
  const pi = args.indexOf('--port'); if (pi >= 0 && args[pi + 1]) port = Number(args[pi + 1]);

  await loadStore();
  await loadConfig();

  server.on('error', (e) => {
    if (e.code === 'EADDRINUSE') { console.error(`port ${port} is busy. try: node web/server.js --port ${port + 1}`); process.exit(1); }
    throw e;
  });
  server.listen(port, () => {
    console.log('');
    console.log('  Reel Factory  ->  http://localhost:' + port + '/');
    console.log('  artefact: ' + (ARTEFACT ? path.relative(ROOT, ARTEFACT) : 'NONE FOUND, /api/artefact will 503'));
    console.log('  storage : ' + path.relative(ROOT, STORE) + (supa ? ' + supabase mirror' : ' (local only)'));
    console.log('  ctrl-c to stop');
    console.log('');
  });
})();
