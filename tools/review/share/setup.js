#!/usr/bin/env node
/**
 * One-time setup for client sharing. Needs no payment details anywhere:
 *   Cloudflare Workers + KV   free, no card    app host, API, comments, markup
 *   private GitHub release    free, no card    the renders (2GB per file)
 *
 *   node share/setup.js       (or ./rr setup)
 *
 * Safe to re-run: it redeploys and keeps your existing keys and links.
 */

const fs = require('fs');
const fsp = require('fs/promises');
const path = require('path');
const { spawn, execFile } = require('child_process');
const { promisify } = require('util');
const crypto = require('crypto');
const execFileP = promisify(execFile);

const ROOT = path.resolve(__dirname, '..');
const HERE = __dirname;
const CONFIG = path.join(HERE, 'config.json');
const TOML = path.join(HERE, 'wrangler.toml');
const REPO_NAME = 'reel-review-assets';
const TAG = 'store';
const KV_TITLE = 'reel-review';

const b = (s) => `\x1b[1m${s}\x1b[0m`;
const dim = (s) => `\x1b[2m${s}\x1b[0m`;
const green = (s) => `\x1b[32m${s}\x1b[0m`;

const run = (cmd, args, opts = {}) =>
  new Promise((resolve) => {
    const p = spawn(cmd, args, { stdio: ['inherit', 'pipe', 'pipe'], cwd: HERE, ...opts });
    let out = '';
    p.stdout?.on('data', (d) => { out += d; process.stdout.write(d); });
    p.stderr?.on('data', (d) => { out += d; process.stderr.write(d); });
    p.on('close', (code) => resolve({ code, out }));
  });

const wrangler = (args, opts) => run('npx', ['--yes', 'wrangler@latest', ...args], opts);

(async () => {
  console.log(`\n${b('Reel Review · client sharing setup')}\n`);
  let cfg = {};
  try { cfg = JSON.parse(await fsp.readFile(CONFIG, 'utf8')); } catch {}

  /* 1. GitHub: where the renders live */
  console.log('→ GitHub (renders)\n');
  let login;
  try {
    ({ stdout: login } = await execFileP('gh', ['api', 'user', '--jq', '.login']));
    login = login.trim();
  } catch {
    console.error('  `gh` is not authenticated. Run:  gh auth login\n');
    process.exit(1);
  }
  const repo = cfg.repo || `${login}/${REPO_NAME}`;

  let repoOk = true;
  try { await execFileP('gh', ['repo', 'view', repo, '--json', 'name']); }
  catch { repoOk = false; }
  if (!repoOk) {
    console.log(`  creating private repo ${repo}`);
    await execFileP('gh', ['repo', 'create', repo, '--private',
      '--description', 'Private storage for client review renders']);
    const tmp = path.join(HERE, '.seed');
    await fsp.rm(tmp, { recursive: true, force: true });
    await fsp.mkdir(tmp, { recursive: true });
    await fsp.writeFile(path.join(tmp, 'README.md'),
      '# reel-review-assets\n\nPrivate blob store for Reel Review client links.\n' +
      'Renders live as release assets on the `store` tag.\n');
    const git = (...a) => execFileP('git', a, { cwd: tmp });
    await git('init', '-q');
    await git('add', '-A');
    await git('-c', 'user.email=noreply@github.com', '-c', `user.name=${login}`,
      'commit', '-qm', 'init');
    await git('branch', '-M', 'main');
    await git('remote', 'add', 'origin', `https://github.com/${repo}.git`);
    await git('push', '-q', 'origin', 'main');
    await fsp.rm(tmp, { recursive: true, force: true });
  }
  try { await execFileP('gh', ['release', 'view', TAG, '--repo', repo]); }
  catch {
    await execFileP('gh', ['release', 'create', TAG, '--repo', repo,
      '--title', 'review assets', '--notes', 'renders served to client review links']);
  }
  console.log(`  ${green('ok')}  ${repo} @ ${TAG}\n`);

  /* 2. a token the worker can read those assets with */
  let ghToken = cfg.ghToken;
  if (!ghToken) {
    try {
      const { stdout } = await execFileP('gh', ['auth', 'token']);
      ghToken = stdout.trim();
    } catch {}
  }
  if (!ghToken) {
    console.error('  Could not read a GitHub token (`gh auth token`).\n');
    process.exit(1);
  }

  /* 3. Cloudflare auth */
  console.log('→ Cloudflare\n');
  if (process.env.CLOUDFLARE_API_TOKEN) {
    console.log('  using CLOUDFLARE_API_TOKEN from the environment');
  } else {
    const who = await wrangler(['whoami']);
    if (who.code !== 0 || /not authenticated/i.test(who.out)) {
      console.log('\n  Not logged in. A browser window will open; log in, then come back.\n');
      const login = spawn('npx', ['--yes', 'wrangler@latest', 'login'], { cwd: HERE, stdio: 'inherit' });
      const code = await new Promise((r) => login.on('close', r));
      const after = await wrangler(['whoami']);
      if (code !== 0 || /not authenticated/i.test(after.out)) {
        console.error('\n  Still not logged in.\n\n' +
          '  If the browser said "No CSRF value available in the session cookie":\n' +
          '    1. sign in at https://dash.cloudflare.com first\n' +
          '    2. close that tab, then run:  npx wrangler login\n\n' +
          '  Or skip OAuth: create a token at https://dash.cloudflare.com/profile/api-tokens\n' +
          '  ("Edit Cloudflare Workers" template), then\n' +
          '    export CLOUDFLARE_API_TOKEN=<token> && ./rr setup\n');
        process.exit(1);
      }
    }
  }

  /* 4. KV namespace for comments + markup */
  let kvId = cfg.kvId;
  if (!kvId) {
    // a previous half-finished run may already have made it, so look first
    const listed = await wrangler(['kv', 'namespace', 'list']);
    try {
      const arr = JSON.parse(listed.out.slice(listed.out.indexOf('[')));
      kvId = arr.find((n) => n.title === KV_TITLE || n.title.endsWith(`-${KV_TITLE}`))?.id;
    } catch {}
  }
  if (!kvId) {
    const r = await wrangler(['kv', 'namespace', 'create', KV_TITLE]);
    const m = /id\s*=\s*"([0-9a-f]{32})"/i.exec(r.out) || /"?id"?\s*:\s*"([0-9a-f]{32})"/i.exec(r.out);
    if (!m) {
      console.error('\n  Created the namespace but could not read its id. ' +
        'Run `npx wrangler kv namespace list`, then put the id in share/config.json as "kvId".\n');
      process.exit(1);
    }
    kvId = m[1];
  }
  let toml = await fsp.readFile(TOML, 'utf8');
  toml = toml.replace(/^id = ".*"$/m, `id = "${kvId}"`);
  await fsp.writeFile(TOML, toml);
  console.log(`  ${green('ok')}  KV ${kvId}\n`);

  /* 5. bundle the player, verbatim from the local tool */
  const pub = path.join(HERE, 'public');
  await fsp.rm(pub, { recursive: true, force: true });
  await fsp.mkdir(pub, { recursive: true });
  for (const f of ['index.html', 'app.js', 'style.css']) {
    await fsp.copyFile(path.join(ROOT, 'review', 'public', f), path.join(pub, f));
  }

  /* 6. secrets + deploy */
  const adminKey = cfg.adminKey || crypto.randomBytes(24).toString('base64url');
  for (const [name, value] of [['ADMIN_KEY', adminKey], ['GITHUB_TOKEN', ghToken]]) {
    const put = spawn('npx', ['--yes', 'wrangler@latest', 'secret', 'put', name],
      { cwd: HERE, stdio: ['pipe', 'ignore', 'inherit'] });
    put.stdin.write(value + '\n');
    put.stdin.end();
    await new Promise((r) => put.on('close', r));
  }

  console.log('→ deploying\n');
  const dep = await wrangler(['deploy']);
  if (dep.code !== 0) {
    console.error('\nDeploy failed. Fix the error above and re-run.\n');
    process.exit(1);
  }
  const m = /https:\/\/[\w.-]*workers\.dev/.exec(dep.out);
  const base = cfg.base || (m ? m[0] : null);

  await fsp.writeFile(CONFIG, JSON.stringify({ base, adminKey, repo, tag: TAG, kvId, ghToken }, null, 2));

  console.log(`\n${green('Ready.')}  ${base}\n`);
  console.log('  Share a cut:   ./rr share out/vidN-final.mp4 --name "Client"');
  console.log('  Get notes:     ./rr pull vidN');
  console.log('  What is live:  ./rr shared\n');
  console.log(dim('  share/config.json holds your keys. Gitignored. Keep it.\n'));
})();
