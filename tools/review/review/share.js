#!/usr/bin/env node
/**
 * Reel Review · client sharing
 *
 *   ./rr share out/vid48-final.mp4          upload + print the private client link
 *   ./rr pull vid48                         bring client notes into review/data/vid48/
 *   ./rr push vid48                         send your replies + resolved marks back
 *   ./rr inbox                              anything a client left that you have not pulled
 *   ./rr shared                             what is live, and who has commented
 *   ./rr revoke vid48                       rotate the key (old link dies)
 *   ./rr unshare vid48                      delete the video + notes from R2
 *
 * Config lives in share/config.json (gitignored): { "base": "...", "adminKey": "..." }
 */

const fs = require('fs');
const fsp = require('fs/promises');
const path = require('path');
const os = require('os');
const { execFile } = require('child_process');
const { promisify } = require('util');
const execFileP = promisify(execFile);

// RR_ROOT lets the tool sit anywhere in a repo. In the production repo it lived at the
// root, so `..` was correct. Here it is vendored under tools/review/, and the launcher
// exports RR_ROOT so `out/` and the -feedback-roundN.md files still land at the repo root.
const ROOT = process.env.RR_ROOT
  ? path.resolve(process.env.RR_ROOT)
  : path.resolve(__dirname, '..');
const CONFIG = path.join(ROOT, 'share', 'config.json');

const c = {
  dim: (s) => `\x1b[2m${s}\x1b[0m`,
  b: (s) => `\x1b[1m${s}\x1b[0m`,
  ok: (s) => `\x1b[32m${s}\x1b[0m`,
  warn: (s) => `\x1b[33m${s}\x1b[0m`,
};

function loadConfig() {
  if (!fs.existsSync(CONFIG)) {
    console.error(`\nNot set up yet. Run:\n\n  ${c.b('node share/setup.js')}\n`);
    process.exit(1);
  }
  const cfg = JSON.parse(fs.readFileSync(CONFIG, 'utf8'));
  for (const f of ['base', 'adminKey', 'repo', 'tag']) {
    if (!cfg[f]) {
      console.error(`share/config.json is missing "${f}" — re-run ./rr setup`);
      process.exit(1);
    }
  }
  cfg.base = cfg.base.replace(/\/+$/, '');
  return cfg;
}

async function adminFetch(cfg, route, opts = {}) {
  // a freshly registered workers.dev subdomain can miss DNS for a few seconds
  let r, lastErr;
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      r = await fetch(`${cfg.base}/api/admin/${route}`, {
        ...opts,
        headers: {
          'x-admin-key': cfg.adminKey,
          ...(opts.body && typeof opts.body === 'string' ? { 'content-type': 'application/json' } : {}),
          ...(opts.headers || {}),
        },
      });
      break;
    } catch (e) {
      lastErr = e;
      await new Promise((res) => setTimeout(res, 1500 * (attempt + 1)));
    }
  }
  if (!r) throw new Error(`${route}: ${lastErr?.message || 'network error'}`);
  const text = await r.text();
  let body;
  try { body = JSON.parse(text); } catch { body = { raw: text }; }
  if (!r.ok) throw new Error(`${route}: ${r.status} ${body.error || body.raw || ''}`);
  return body;
}

async function probe(file) {
  const { stdout } = await execFileP('ffprobe', [
    '-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height,r_frame_rate',
    '-show_entries', 'format=duration', '-of', 'json', file,
  ]);
  const j = JSON.parse(stdout);
  const st = j.streams?.[0] || {};
  const [n, d] = String(st.r_frame_rate || '30/1').split('/').map(Number);
  return {
    width: st.width || 1080,
    height: st.height || 1920,
    fps: Math.round((d ? n / d : 30) * 1000) / 1000,
    duration: Number(j.format?.duration || 0),
  };
}

function slugFor(file) {
  let s = path.basename(file).replace(/\.[^.]+$/, '').toLowerCase().replace(/[ _]+/g, '-');
  s = s.replace(/-(final|preview|render|export|out)$/g, '').replace(/-v\d+$/g, '');
  return s.replace(/[^a-z0-9.-]/g, '') || 'video';
}

const mb = (b) => (b / 1048576).toFixed(1) + ' MB';

/* ── upload ───────────────────────────────────────────────────── */

/**
 * Renders live as assets on a private GitHub release: 2GB per file, free, and
 * their signed URLs honour byte ranges, which is all the player needs. The repo
 * stays private; only the worker (holding a token) can read them.
 */
async function upload(cfg, file, assetName) {
  const size = (await fsp.stat(file)).size;
  // Stage the renamed copy OUTSIDE the source directory. Putting it alongside the
  // original destroys it on case-insensitive filesystems (macOS default): a file
  // named FOO-v2.mp4 and an assetName of foo-v2.mp4 are the same inode, so the
  // copy is a no-op and the cleanup rm below deletes the original.
  const stage = await fsp.mkdtemp(path.join(os.tmpdir(), 'rr-upload-'));
  const tmp = path.join(stage, assetName);
  const renamed = path.basename(file) !== assetName;
  if (renamed) await fsp.copyFile(file, tmp);

  process.stdout.write(`  uploading ${mb(size)} to ${cfg.repo} … `);
  try {
    await execFileP('gh', ['release', 'upload', cfg.tag, renamed ? tmp : file,
      '--repo', cfg.repo, '--clobber'], { maxBuffer: 1 << 24 });
  } finally {
    await fsp.rm(stage, { recursive: true, force: true });
  }

  const { stdout } = await execFileP('gh', ['api',
    `repos/${cfg.repo}/releases/tags/${cfg.tag}`,
    '--jq', `.assets[] | select(.name=="${assetName}") | .id`]);
  const id = Number(stdout.trim().split('\n')[0]);
  if (!id) throw new Error('uploaded, but could not read the asset id back');
  console.log(c.ok('done'));
  return { repo: cfg.repo, id, size, contentType: 'video/mp4' };
}

/* ── commands ─────────────────────────────────────────────────── */

async function cmdShare(args) {
  const cfg = loadConfig();
  const file = args.find((a) => !a.startsWith('-'));
  if (!file) { console.error('usage: ./rr share out/vidN-final.mp4 [--as slug] [--name "Client Name"] [--label "v2 notes"]'); process.exit(1); }
  const abs = path.resolve(ROOT, file);
  if (!fs.existsSync(abs)) { console.error('no such file: ' + file); process.exit(1); }

  const flag = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
  const slug = flag('--as') || slugFor(abs);
  const name = flag('--name');
  const label = flag('--label') || '';

  const info = await probe(abs);
  const size = (await fsp.stat(abs)).size;
  console.log(`\n${c.b(slug)}  ${info.duration.toFixed(2)}s · ${info.fps}fps · ${info.width}×${info.height} · ${mb(size)}`);

  // how many versions already exist decides this asset's name
  const existing = await adminFetch(cfg, `pull/${slug}`).catch(() => null);
  const v = (existing?.project.versions.length || 0) + 1;
  const asset = await upload(cfg, abs, `${slug}-v${v}.mp4`);

  const proj = await adminFetch(cfg, 'project', {
    method: 'POST',
    body: JSON.stringify({
      slug,
      name: name || undefined,
      version: { ...info, bytes: size, path: path.basename(abs), label, asset },
    }),
  });

  const link = `${cfg.base}/v/${slug}?k=${proj.shareKey}`;
  console.log(`\n  ${c.b('Send this:')}\n  ${link}\n`);
  console.log(c.dim(`  v${v} is live. Anyone with the link can comment; nobody can list your other videos.`));
  console.log(c.dim(`  When they are done:  ./rr pull ${slug}\n`));

  // keep a local copy of the link so it is never lost
  const dir = path.join(ROOT, 'review', 'data', slug);
  await fsp.mkdir(dir, { recursive: true });
  await fsp.writeFile(path.join(dir, 'share.json'),
    JSON.stringify({ slug, link, base: cfg.base, version: v, shared: new Date().toISOString() }, null, 2));
  return link;
}

async function cmdPull(args) {
  const cfg = loadConfig();
  const slug = args.find((a) => !a.startsWith('-'));
  if (!slug) { console.error('usage: ./rr pull <slug>'); process.exit(1); }

  const { project, comments } = await adminFetch(cfg, `pull/${slug}`);
  const dir = path.join(ROOT, 'review', 'data', slug);
  const mkDir = path.join(dir, 'markup');
  await fsp.mkdir(mkDir, { recursive: true });

  // merge: client notes win on text, local status/reply survive
  let local = [];
  try { local = JSON.parse(await fsp.readFile(path.join(dir, 'comments.json'), 'utf8')); } catch {}
  const byId = new Map(local.map((x) => [x.id, x]));
  let added = 0, pulled = 0;
  for (const rc of comments) {
    const prev = byId.get(rc.id);
    byId.set(rc.id, prev ? { ...rc, status: prev.status, reply: prev.reply } : rc);
    if (!prev) added++;
    if (rc.markup) {
      const dest = path.join(mkDir, rc.markup);
      if (!fs.existsSync(dest)) {
        const r = await fetch(`${cfg.base}/api/admin/markup/${slug}/${rc.markup}`,
          { headers: { 'x-admin-key': cfg.adminKey } });
        if (r.ok) { await fsp.writeFile(dest, Buffer.from(await r.arrayBuffer())); pulled++; }
      }
    }
  }
  await fsp.writeFile(path.join(dir, 'comments.json'),
    JSON.stringify([...byId.values()], null, 2));

  // make sure a local project exists so ./rr can open it and export a round
  const pf = path.join(dir, 'project.json');
  if (!fs.existsSync(pf)) {
    await fsp.writeFile(pf, JSON.stringify({
      slug, name: project.name, created: project.created,
      versions: project.versions.map((v) => ({ ...v, path: v.path || `${slug} v${v.v}` })),
      rounds: [],
    }, null, 2));
  }

  const open = [...byId.values()].filter((x) => x.status !== 'resolved').length;
  const subs = project.submissions?.length || 0;
  console.log(`\n${c.b(slug)}: ${comments.length} client note${comments.length === 1 ? '' : 's'} ` +
    `(${added} new), ${pulled} markup frame${pulled === 1 ? '' : 's'} downloaded.`);
  console.log(`${open} open · ${subs} submission${subs === 1 ? '' : 's'}` +
    (subs ? c.dim(`  last ${new Date(project.submissions[subs - 1].at).toLocaleString()}`) : ''));
  console.log(c.dim(`\n  Open locally:  ./rr\n  Export round:  the Send to editor button, or POST /api/project/${slug}/round\n`));
}

async function cmdShared() {
  const cfg = loadConfig();
  const { projects } = await adminFetch(cfg, 'list');
  if (!projects.length) return console.log('\nNothing shared yet.\n');
  console.log('');
  for (const p of projects) {
    console.log(`${c.b(p.slug.padEnd(18))} v${p.versions}  ` +
      `${String(p.comments).padStart(3)} notes (${p.open} open)  ` +
      `${p.submissions} submission${p.submissions === 1 ? '' : 's'}`);
    console.log(c.dim(`  ${cfg.base}/v/${p.slug}?k=${p.shareKey}`));
  }
  console.log('');
}

async function cmdRevoke(args) {
  const cfg = loadConfig();
  const slug = args.find((a) => !a.startsWith('-'));
  const p = await adminFetch(cfg, `revoke/${slug}`, { method: 'POST' });
  console.log(`\nOld link is dead. New one:\n  ${cfg.base}/v/${slug}?k=${p.shareKey}\n`);
}

async function cmdUnshare(args) {
  const cfg = loadConfig();
  const slug = args.find((a) => !a.startsWith('-'));
  if (!args.includes('--yes')) {
    console.log(`\nThis deletes every client note and markup frame for ${c.b(slug)}, and the ` +
      `uploaded renders.\nLocal copies in review/data/${slug}/ are untouched.\n` +
      `Re-run with --yes to confirm.\n`);
    return;
  }
  const { project } = await adminFetch(cfg, `pull/${slug}`).catch(() => ({ project: null }));
  await adminFetch(cfg, `delete/${slug}`, { method: 'POST' });
  for (const v of project?.versions || []) {
    if (!v.asset) continue;
    await execFileP('gh', ['api', '-X', 'DELETE',
      `repos/${v.asset.repo}/releases/assets/${v.asset.id}`]).catch(() => {});
  }
  console.log(`\n${slug} removed: notes, markup and ${project?.versions.length || 0} render(s).\n`);
}


/**
 * Send the editor's answers back to the client: resolved marks and replies,
 * read straight out of the local comments.json. Without this the client sees
 * their notes sitting untouched no matter how much got fixed.
 */
async function cmdPush(args) {
  const cfg = loadConfig();
  const slug = args.find((a) => !a.startsWith('-'));
  if (!slug) { console.error('usage: ./rr push <slug>'); process.exit(1); }

  const file = path.join(ROOT, 'review', 'data', slug, 'comments.json');
  let local;
  try { local = JSON.parse(await fsp.readFile(file, 'utf8')); }
  catch { console.error(`no local notes at ${path.relative(ROOT, file)}`); process.exit(1); }

  // Send every client note's current state, not just the answered ones: local is
  // the source of truth, so clearing a reply has to propagate too.
  const updates = local
    .filter((c) => c.source === 'client')
    .map((c) => ({ id: c.id, status: c.status || 'open', reply: c.reply || null }));

  if (!updates.length) {
    console.log(`\nNo client notes in ${path.relative(ROOT, file)} yet — nothing to answer.\n`);
    return;
  }

  const r = await adminFetch(cfg, `reply/${slug}`, {
    method: 'POST', body: JSON.stringify({ updates }),
  });
  const answered = updates.filter((u) => u.reply).length;
  const resolved = updates.filter((u) => u.status === 'resolved').length;
  console.log(`\n${c.b(slug)}: sent ${r.updated} update${r.updated === 1 ? '' : 's'} ` +
    `(${answered} with a reply, ${resolved} marked resolved).`);
  console.log(c.dim('  The client sees them on their cards the next time they open the link.\n'));
}

/**
 * Anything a client has done that has not been pulled yet. Run this at the
 * start of a session so a round left overnight is not missed.
 */
async function cmdInbox() {
  const cfg = loadConfig();
  const { projects } = await adminFetch(cfg, 'list');
  const rows = [];

  for (const p of projects) {
    if (!p.comments) continue;
    const { project, comments } = await adminFetch(cfg, `pull/${p.slug}`);
    let local = [];
    try {
      local = JSON.parse(await fsp.readFile(
        path.join(ROOT, 'review', 'data', p.slug, 'comments.json'), 'utf8'));
    } catch {}
    const known = new Set(local.map((x) => x.id));
    const fresh = comments.filter((x) => x.source === 'client' && !known.has(x.id));
    const subs = project.submissions || [];
    const last = subs[subs.length - 1];
    if (fresh.length || (last && !local.length)) {
      rows.push({ slug: p.slug, name: p.name, fresh: fresh.length, open: p.open, last });
    }
  }

  if (!rows.length) {
    console.log('\nNothing new from any client.\n');
    return;
  }
  console.log('');
  for (const r of rows) {
    console.log(`${c.b(r.slug.padEnd(16))} ${c.warn(`${r.fresh} new note${r.fresh === 1 ? '' : 's'}`)}` +
      `  ${r.open} open   ${r.name}`);
    if (r.last) console.log(c.dim(`  last sent ${new Date(r.last.at).toLocaleString()}`));
    console.log(c.dim(`  ./rr pull ${r.slug}`));
  }
  console.log('');
}

const CMDS = { share: cmdShare, pull: cmdPull, push: cmdPush, inbox: cmdInbox,
  shared: cmdShared, revoke: cmdRevoke, unshare: cmdUnshare };

(async () => {
  const [cmd, ...rest] = process.argv.slice(2);
  const fn = CMDS[cmd];
  if (!fn) {
    console.error(`unknown command "${cmd}". one of: ${Object.keys(CMDS).join(', ')}`);
    process.exit(1);
  }
  try {
    await fn(rest);
  } catch (e) {
    console.error('\n' + c.warn('failed: ') + e.message + '\n');
    process.exit(1);
  }
})();
