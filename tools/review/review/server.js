#!/usr/bin/env node
/**
 * Reel Review — a local frame.io for this repo.
 *
 * Zero dependencies (Node core + ffprobe). Serves a scrubbable player with
 * frame-pinned comments, freehand/box/arrow markup, whole-video notes and a
 * version stack, then exports the round as `<slug>-feedback-round<N>.md` at the
 * repo root so the editor can just read it.
 *
 *   node review/server.js out/vid47-final.mp4     # open one video
 *   node review/server.js                         # gallery of everything in out/
 */

const http = require('http');
const fs = require('fs');
const fsp = require('fs/promises');
const path = require('path');
const { execFile } = require('child_process');
const { promisify } = require('util');
const execFileP = promisify(execFile);

// RR_ROOT lets the tool sit anywhere in a repo. In the production repo it lived at the
// root, so `..` was correct. Here it is vendored under tools/review/, and the launcher
// exports RR_ROOT so `out/` and the -feedback-roundN.md files still land at the repo root.
const ROOT = process.env.RR_ROOT
  ? path.resolve(process.env.RR_ROOT)
  : path.resolve(__dirname, '..');
const DATA = path.join(__dirname, 'data');
const PUBLIC = path.join(__dirname, 'public');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.mp4': 'video/mp4',
  '.mov': 'video/quicktime',
  '.webm': 'video/webm',
  '.jpg': 'image/jpeg',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

/* ── slug + project store ─────────────────────────────────────────── */

// out/vid47-final.mp4 → vid47 ; out/vid46-short.mp4 → vid46-short
function slugFor(file) {
  let s = path.basename(file).replace(/\.[^.]+$/, '').toLowerCase();
  s = s.replace(/[ _]+/g, '-');
  s = s.replace(/-(final|preview|render|export|out)$/g, '');
  s = s.replace(/-v\d+$/g, '').replace(/-round\d+$/g, '');
  s = s.replace(/-(final|preview)$/g, '');
  return s.replace(/[^a-z0-9.-]/g, '') || 'video';
}

const projDir = (slug) => path.join(DATA, slug);
const projFile = (slug) => path.join(projDir(slug), 'project.json');

async function readProject(slug) {
  try {
    return JSON.parse(await fsp.readFile(projFile(slug), 'utf8'));
  } catch {
    return null;
  }
}

async function writeProject(p) {
  await fsp.mkdir(projDir(p.slug), { recursive: true });
  await fsp.writeFile(projFile(p.slug), JSON.stringify(p, null, 2));
  return p;
}

async function probe(file) {
  const { stdout } = await execFileP('ffprobe', [
    '-v', 'error',
    '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height,r_frame_rate,nb_frames',
    '-show_entries', 'format=duration,size',
    '-of', 'json', file,
  ]);
  const j = JSON.parse(stdout);
  const st = (j.streams && j.streams[0]) || {};
  const [num, den] = String(st.r_frame_rate || '30/1').split('/').map(Number);
  const fps = den ? num / den : 30;
  const duration = Number(j.format?.duration || 0);
  return {
    width: st.width || 1080,
    height: st.height || 1920,
    fps: Math.round(fps * 1000) / 1000,
    frames: Number(st.nb_frames) || Math.round(duration * fps),
    duration,
    bytes: Number(j.format?.size || 0),
  };
}

/**
 * Register `file` under its slug. A file whose path+size+mtime differs from the
 * newest version becomes the next version; an identical one is reused.
 */
async function register(file, opts = {}) {
  const abs = path.resolve(ROOT, file);
  const st = await fsp.stat(abs);
  const slug = opts.slug || slugFor(abs);
  const rel = path.relative(ROOT, abs);
  const info = await probe(abs);

  let p = await readProject(slug);
  if (!p) {
    p = { slug, name: slug, created: new Date().toISOString(), versions: [], rounds: [] };
  }
  const stamp = { path: rel, bytes: st.size, mtime: st.mtimeMs };
  const last = p.versions[p.versions.length - 1];
  const same = last && last.path === stamp.path && last.bytes === stamp.bytes &&
    Math.abs(last.mtime - stamp.mtime) < 1000;

  if (!same) {
    p.versions.push({
      v: p.versions.length + 1,
      ...stamp,
      ...info,
      added: new Date().toISOString(),
      label: opts.label || '',
    });
    await writeProject(p);
  }
  return p;
}

/* ── comments ─────────────────────────────────────────────────────── */

const commentsFile = (slug) => path.join(projDir(slug), 'comments.json');

async function readComments(slug) {
  try {
    return JSON.parse(await fsp.readFile(commentsFile(slug), 'utf8'));
  } catch {
    return [];
  }
}

async function writeComments(slug, list) {
  await fsp.mkdir(projDir(slug), { recursive: true });
  await fsp.writeFile(commentsFile(slug), JSON.stringify(list, null, 2));
}

const newId = () => 'c' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

/* ── round export ─────────────────────────────────────────────────── */

const fmtT = (t) => {
  const m = Math.floor(t / 60);
  const s = t - m * 60;
  return `${m}:${s.toFixed(2).padStart(5, '0')}`;
};

function describeShapes(shapes = []) {
  if (!shapes.length) return '';
  return shapes.map((s) => {
    const pc = (n) => `${Math.round(n * 100)}%`;
    if (s.type === 'box') return `box at x${pc(s.x)} y${pc(s.y)}, ${pc(s.w)}×${pc(s.h)}`;
    if (s.type === 'arrow') return `arrow ${pc(s.x)},${pc(s.y)} → ${pc(s.x2)},${pc(s.y2)}`;
    if (s.type === 'pin') return `pin at x${pc(s.x)} y${pc(s.y)}`;
    if (s.type === 'pen') return `freehand around x${pc(s.cx ?? s.x)} y${pc(s.cy ?? s.y)}`;
    return s.type;
  }).join('; ');
}

/**
 * Next free `<slug>-feedback-round<N>.md`. These files are hand-written by the
 * owner too, and are often untracked — never, ever clobber one.
 */
async function nextRoundFile(slug, recorded) {
  let names = [];
  try { names = await fsp.readdir(ROOT); } catch {}
  const re = new RegExp(`^${slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}-feedback-round(\\d+)\\.md$`);
  let n = recorded;
  for (const f of names) {
    const m = re.exec(f);
    if (m) n = Math.max(n, Number(m[1]));
  }
  n += 1;
  let file = path.join(ROOT, `${slug}-feedback-round${n}.md`);
  while (fs.existsSync(file)) {
    n += 1;
    file = path.join(ROOT, `${slug}-feedback-round${n}.md`);
  }
  return { file, n };
}

async function exportRound(slug) {
  const p = await readProject(slug);
  if (!p) throw new Error('unknown project ' + slug);
  const all = await readComments(slug);
  const ver = p.versions[p.versions.length - 1];
  const { file: outFile, n: roundNo } = await nextRoundFile(slug, p.rounds?.length || 0);

  // Everything open, regardless of which version it was left on.
  const live = all.filter((c) => c.status !== 'resolved' && c.status !== 'wontfix');
  const globals = live.filter((c) => c.scope === 'global')
    .sort((a, b) => a.created.localeCompare(b.created));
  const frames = live.filter((c) => c.scope !== 'global').sort((a, b) => a.t - b.t);

  const L = [];
  L.push(`# ${p.name || slug} · review round ${roundNo}`);
  L.push('');
  L.push(`Source: \`${ver.path}\` (v${ver.v}) · ${ver.duration.toFixed(2)}s · ` +
    `${ver.fps}fps · ${ver.width}×${ver.height}`);
  L.push(`Exported ${new Date().toLocaleString()} · ` +
    `${globals.length} whole-video note${globals.length === 1 ? '' : 's'}, ` +
    `${frames.length} frame note${frames.length === 1 ? '' : 's'}`);
  L.push('');

  if (globals.length) {
    L.push('## Whole-video notes');
    L.push('');
    L.push('These apply to the entire cut, not the frame they were written on.');
    L.push('');
    globals.forEach((c, i) => {
      L.push(`**G${i + 1}.** ${c.text.trim()}`);
      L.push(`  <sub>written at ${fmtT(c.t)} · v${c.version}${c.markup ? ` · markup: \`review/data/${slug}/markup/${c.markup}\`` : ''}</sub>`);
      L.push('');
    });
  }

  if (frames.length) {
    L.push('## Frame notes');
    L.push('');
    L.push('| # | Time | Frame | Note |');
    L.push('|---|------|-------|------|');
    frames.forEach((c, i) => {
      const one = c.text.trim().replace(/\s+/g, ' ');
      L.push(`| ${i + 1} | ${fmtT(c.t)} | ${c.frame} | ${one.length > 90 ? one.slice(0, 87) + '…' : one} |`);
    });
    L.push('');
    frames.forEach((c, i) => {
      L.push(`### ${i + 1} · ${fmtT(c.t)} · frame ${c.frame} (v${c.version})`);
      L.push('');
      L.push(c.text.trim());
      L.push('');
      if (c.markup) {
        L.push(`Markup frame: \`review/data/${slug}/markup/${c.markup}\``);
        const d = describeShapes(c.shapes);
        if (d) L.push(`Drawn: ${d}`);
        L.push('');
      }
    });
  }

  if (!globals.length && !frames.length) {
    L.push('_No open notes._');
    L.push('');
  }

  // 'wx' — refuse to overwrite, even if something raced us to the name.
  await fsp.writeFile(outFile, L.join('\n'), { flag: 'wx' });
  const out = outFile;

  p.rounds = p.rounds || [];
  p.rounds.push({
    n: roundNo,
    version: ver.v,
    file: path.relative(ROOT, out),
    at: new Date().toISOString(),
    open: live.length,
    ids: live.map((c) => c.id),
  });
  await writeProject(p);

  return { file: path.relative(ROOT, out), round: roundNo, count: live.length };
}

/* ── http plumbing ────────────────────────────────────────────────── */

const json = (res, code, body) => {
  const b = Buffer.from(JSON.stringify(body));
  res.writeHead(code, { 'content-type': MIME['.json'], 'content-length': b.length });
  res.end(b);
};

function readBody(req, limit = 40 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let n = 0;
    req.on('data', (c) => {
      n += c.length;
      if (n > limit) { reject(new Error('body too large')); req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', () => {
      try { resolve(chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {}); }
      catch (e) { reject(e); }
    });
    req.on('error', reject);
  });
}

function serveStatic(res, file) {
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, {
      'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'content-length': st.size,
      'cache-control': 'no-cache',
    });
    fs.createReadStream(file).pipe(res);
  });
}

// Byte-range streaming — without this, scrubbing a 30MB reel re-downloads it.
function serveMedia(req, res, file) {
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404); res.end('not found'); return; }
    const type = MIME[path.extname(file).toLowerCase()] || 'video/mp4';
    const range = req.headers.range;
    if (!range) {
      res.writeHead(200, { 'content-type': type, 'content-length': st.size, 'accept-ranges': 'bytes', 'cache-control': 'no-store' });
      fs.createReadStream(file).pipe(res);
      return;
    }
    const m = /bytes=(\d*)-(\d*)/.exec(range);
    let start = m[1] ? parseInt(m[1], 10) : 0;
    let end = m[2] ? parseInt(m[2], 10) : st.size - 1;
    if (isNaN(start) || start >= st.size) { res.writeHead(416, { 'content-range': `bytes */${st.size}` }); res.end(); return; }
    end = Math.min(end, st.size - 1);
    res.writeHead(206, {
      'content-type': type,
      'content-range': `bytes ${start}-${end}/${st.size}`,
      'accept-ranges': 'bytes',
      'content-length': end - start + 1,
      'cache-control': 'no-store',
    });
    fs.createReadStream(file, { start, end }).pipe(res);
  });
}

async function listProjects() {
  let dirs = [];
  try { dirs = await fsp.readdir(DATA); } catch { return []; }
  const out = [];
  for (const d of dirs) {
    const p = await readProject(d);
    if (!p) continue;
    const cs = await readComments(d);
    const last = p.versions[p.versions.length - 1];
    out.push({
      slug: p.slug,
      name: p.name,
      versions: p.versions.length,
      open: cs.filter((c) => c.status !== 'resolved' && c.status !== 'wontfix').length,
      total: cs.length,
      rounds: p.rounds?.length || 0,
      path: last?.path,
      duration: last?.duration,
      updated: last?.added,
    });
  }
  out.sort((a, b) => String(b.updated).localeCompare(String(a.updated)));
  return out;
}

/** mp4/mov sitting in out/ that have never been opened for review. */
async function listUnregistered(known) {
  const dir = path.join(ROOT, 'out');
  let files = [];
  try { files = await fsp.readdir(dir); } catch { return []; }
  const seen = new Set(known.map((p) => p.path));
  const res = [];
  for (const f of files) {
    if (!/\.(mp4|mov|webm)$/i.test(f)) continue;
    const rel = path.join('out', f);
    if (seen.has(rel)) continue;
    const st = await fsp.stat(path.join(dir, f));
    res.push({ path: rel, name: f, bytes: st.size, mtime: st.mtimeMs, slug: slugFor(f) });
  }
  res.sort((a, b) => b.mtime - a.mtime);
  return res.slice(0, 12); // newest dozen — the rest are archive, open them by path
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = decodeURIComponent(url.pathname);

  try {
    /* API */
    if (p === '/api/projects') {
      const list = await listProjects();
      return json(res, 200, { projects: list, unregistered: await listUnregistered(list) });
    }

    if (p === '/api/open' && req.method === 'POST') {
      const b = await readBody(req);
      const proj = await register(b.path, { slug: b.slug, label: b.label });
      return json(res, 200, proj);
    }

    let m;
    if ((m = /^\/api\/project\/([^/]+)$/.exec(p))) {
      const proj = await readProject(m[1]);
      if (!proj) return json(res, 404, { error: 'no such project' });
      return json(res, 200, { ...proj, comments: await readComments(m[1]) });
    }

    if ((m = /^\/api\/project\/([^/]+)\/comments$/.exec(p)) && req.method === 'POST') {
      const slug = m[1];
      const b = await readBody(req);
      const list = await readComments(slug);
      const c = {
        id: newId(),
        version: b.version || 1,
        scope: b.scope === 'global' ? 'global' : 'frame',
        t: Number(b.t) || 0,
        frame: Number(b.frame) || 0,
        text: String(b.text || '').slice(0, 4000),
        shapes: Array.isArray(b.shapes) ? b.shapes : [],
        markup: null,
        status: 'open',
        reply: null,
        created: new Date().toISOString(),
      };
      if (b.markupData && /^data:image\/jpeg;base64,/.test(b.markupData)) {
        const dir = path.join(projDir(slug), 'markup');
        await fsp.mkdir(dir, { recursive: true });
        const name = `${c.id}.jpg`;
        await fsp.writeFile(path.join(dir, name),
          Buffer.from(b.markupData.split(',')[1], 'base64'));
        c.markup = name;
      }
      list.push(c);
      await writeComments(slug, list);
      return json(res, 200, c);
    }

    if ((m = /^\/api\/project\/([^/]+)\/comments\/([^/]+)$/.exec(p))) {
      const [, slug, id] = m;
      const list = await readComments(slug);
      const i = list.findIndex((c) => c.id === id);
      if (i < 0) return json(res, 404, { error: 'no such comment' });
      if (req.method === 'DELETE') {
        const [gone] = list.splice(i, 1);
        if (gone.markup) {
          await fsp.rm(path.join(projDir(slug), 'markup', gone.markup), { force: true });
        }
        await writeComments(slug, list);
        return json(res, 200, { ok: true });
      }
      const b = await readBody(req);
      for (const k of ['text', 'status', 'reply', 'scope']) {
        if (k in b) list[i][k] = b[k];
      }
      list[i].updated = new Date().toISOString();
      await writeComments(slug, list);
      return json(res, 200, list[i]);
    }

    if ((m = /^\/api\/project\/([^/]+)\/round$/.exec(p)) && req.method === 'POST') {
      return json(res, 200, await exportRound(m[1]));
    }

    if ((m = /^\/api\/project\/([^/]+)\/rename$/.exec(p)) && req.method === 'POST') {
      const proj = await readProject(m[1]);
      if (!proj) return json(res, 404, { error: 'no such project' });
      proj.name = String((await readBody(req)).name || proj.slug).slice(0, 120);
      await writeProject(proj);
      return json(res, 200, proj);
    }

    /* media: /media/<slug>/<v> */
    if ((m = /^\/media\/([^/]+)\/(\d+)$/.exec(p))) {
      const proj = await readProject(m[1]);
      const ver = proj?.versions.find((v) => v.v === Number(m[2]));
      if (!ver) { res.writeHead(404); return res.end('no such version'); }
      return serveMedia(req, res, path.join(ROOT, ver.path));
    }

    /* markup images */
    if ((m = /^\/markup\/([^/]+)\/([\w.-]+)$/.exec(p))) {
      return serveStatic(res, path.join(projDir(m[1]), 'markup', m[2]));
    }

    /* app */
    if (p === '/' ) return serveStatic(res, path.join(PUBLIC, 'gallery.html'));
    if (/^\/v\/[^/]+$/.test(p)) return serveStatic(res, path.join(PUBLIC, 'index.html'));

    const file = path.join(PUBLIC, p.replace(/^\/+/, ''));
    if (!file.startsWith(PUBLIC)) { res.writeHead(403); return res.end('nope'); }
    return serveStatic(res, file);
  } catch (e) {
    return json(res, 500, { error: String(e.message || e) });
  }
});

/* ── boot ─────────────────────────────────────────────────────────── */

(async function main() {
  const args = process.argv.slice(2);
  let target = null, slug = null, label = '', port = 7788, open = true;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--as') slug = args[++i];
    else if (a === '--label') label = args[++i];
    else if (a === '--port') port = Number(args[++i]);
    else if (a === '--no-open') open = false;
    else if (!a.startsWith('-')) target = a;
  }

  let landing = '/';
  if (target) {
    try {
      const proj = await register(target, { slug, label });
      landing = '/v/' + proj.slug;
      const v = proj.versions[proj.versions.length - 1];
      console.log(`▸ ${proj.slug}  v${v.v}  ${v.duration.toFixed(2)}s  ${v.fps}fps  ${v.width}×${v.height}`);
    } catch (e) {
      console.error('could not open ' + target + ': ' + e.message);
      process.exit(1);
    }
  }

  server.on('error', (e) => {
    if (e.code === 'EADDRINUSE') {
      console.error(`port ${port} is busy — already running? open http://localhost:${port}${landing}`);
      process.exit(1);
    }
    throw e;
  });

  server.listen(port, () => {
    const url = `http://localhost:${port}${landing}`;
    console.log(`\n  Reel Review → ${url}\n  ctrl-c to stop\n`);
    if (open) execFile('open', [url], () => {});
  });
})();
