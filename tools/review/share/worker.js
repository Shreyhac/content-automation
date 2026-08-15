/**
 * Reel Review · share worker
 *
 * Hosts a client-facing copy of the review player. The client gets one private
 * link (`/v/<slug>?k=<shareKey>`), leaves notes, and presses "Send to editor".
 * `./rr pull <slug>` brings those notes back into review/data/<slug>/ so the
 * local tool and the round export treat them identically to local notes.
 *
 * Storage, chosen so the whole thing costs nothing and needs no card on file:
 *   video     private GitHub release asset (2GB/file), proxied with a token
 *   metadata  Cloudflare KV  (p:<slug>, c:<slug>:<id>, k:<slug>:<id>.jpg)
 *
 * R2 would be tidier but requires billing details; GitHub Releases support
 * byte-range requests through their signed URLs, which is all the player needs.
 */

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

const bad = (msg, status = 400) => json({ error: msg }, status);

const newId = () => 'c' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
const newKey = () =>
  [...crypto.getRandomValues(new Uint8Array(16))].map((b) => b.toString(36).padStart(2, '0')).join('').slice(0, 22);

const pKey = (slug) => `p:${slug}`;
const cPrefix = (slug) => `c:${slug}:`;

async function getProject(env, slug) {
  return await env.KV.get(pKey(slug), 'json');
}
const putProject = (env, p) => env.KV.put(pKey(p.slug), JSON.stringify(p));

async function listComments(env, slug) {
  const out = [];
  let cursor;
  do {
    const r = await env.KV.list({ prefix: cPrefix(slug), cursor, limit: 1000 });
    for (const key of r.keys) {
      const c = await env.KV.get(key.name, 'json');
      if (c) out.push(c);
    }
    cursor = r.list_complete ? null : r.cursor;
  } while (cursor);
  return out.sort((a, b) => String(a.created).localeCompare(String(b.created)));
}

function keyEq(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

const isAdmin = (req, env) => keyEq(req.headers.get('x-admin-key') || '', env.ADMIN_KEY || '\0');

/* ── video: private release asset → signed URL → range passthrough ── */

/**
 * Resolve a release asset to its signed CDN URL. GitHub's is valid about an
 * hour; cache it so a scrubbing client does not spend the API rate limit one
 * seek at a time.
 */
async function signedUrl(env, asset) {
  const ck = `s:${asset.repo}:${asset.id}`;
  const hit = await env.KV.get(ck);
  if (hit) return hit;

  const r = await fetch(`https://api.github.com/repos/${asset.repo}/releases/assets/${asset.id}`, {
    headers: {
      authorization: `Bearer ${env.GITHUB_TOKEN}`,
      accept: 'application/octet-stream',
      'user-agent': 'reel-review',
    },
    redirect: 'manual',
  });
  const loc = r.headers.get('location');
  if (!loc) throw new Error(`could not resolve asset ${asset.id} (${r.status})`);
  await env.KV.put(ck, loc, { expirationTtl: 2400 }); // well inside the ~1h signature
  return loc;
}

async function serveVideo(env, asset, req) {
  const url = await signedUrl(env, asset);
  const range = req.headers.get('range');
  const upstream = await fetch(url, { headers: range ? { range } : {} });

  const h = new Headers();
  // force inline playback: the signed URL asks for attachment, which some
  // browsers honour even for a media element
  h.set('content-type', asset.contentType || 'video/mp4');
  h.set('accept-ranges', 'bytes');
  h.set('cache-control', 'private, max-age=600');
  for (const f of ['content-range', 'content-length', 'etag']) {
    const v = upstream.headers.get(f);
    if (v) h.set(f, v);
  }
  return new Response(upstream.body, { status: upstream.status, headers: h });
}

/* ── worker ────────────────────────────────────────────────────── */

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const p = url.pathname;
    const k = url.searchParams.get('k') || '';

    try {
      /* ── owner API ─────────────────────────────────────────── */
      if (p.startsWith('/api/admin/')) {
        if (!isAdmin(req, env)) return bad('unauthorized', 401);
        const tail = p.slice('/api/admin/'.length);

        if (tail === 'project' && req.method === 'POST') {
          const b = await req.json();
          let proj = await getProject(env, b.slug);
          if (!proj) {
            proj = {
              slug: b.slug,
              name: b.name || b.slug,
              shareKey: newKey(),
              created: new Date().toISOString(),
              versions: [],
              submissions: [],
            };
          }
          if (b.name) proj.name = b.name;
          if (b.version) {
            proj.versions.push({ ...b.version, v: proj.versions.length + 1, added: new Date().toISOString() });
          }
          await putProject(env, proj);
          return json(proj);
        }

        if (tail === 'list') {
          const out = [];
          let cursor;
          do {
            const r = await env.KV.list({ prefix: 'p:', cursor, limit: 1000 });
            for (const key of r.keys) {
              const proj = await env.KV.get(key.name, 'json');
              if (!proj) continue;
              const cs = await listComments(env, proj.slug);
              out.push({
                slug: proj.slug,
                name: proj.name,
                shareKey: proj.shareKey,
                versions: proj.versions.length,
                comments: cs.length,
                open: cs.filter((c) => c.status !== 'resolved').length,
                submissions: proj.submissions?.length || 0,
              });
            }
            cursor = r.list_complete ? null : r.cursor;
          } while (cursor);
          return json({ projects: out });
        }

        let m;
        if ((m = /^pull\/([\w.-]+)$/.exec(tail))) {
          const proj = await getProject(env, m[1]);
          if (!proj) return bad('no such project', 404);
          return json({ project: proj, comments: await listComments(env, m[1]) });
        }

        if ((m = /^markup\/([\w.-]+)\/([\w.-]+)$/.exec(tail))) {
          const buf = await env.KV.get(`k:${m[1]}:${m[2]}`, 'arrayBuffer');
          if (!buf) return new Response('not found', { status: 404 });
          return new Response(buf, { headers: { 'content-type': 'image/jpeg' } });
        }

        // the editor answering the client: status + reply flow back the other way
        if ((m = /^reply\/([\w.-]+)$/.exec(tail)) && req.method === 'POST') {
          const slug = m[1];
          const b = await req.json();
          let n = 0;
          for (const u of b.updates || []) {
            const c = await env.KV.get(`c:${slug}:${u.id}`, 'json');
            if (!c) continue;
            if ('status' in u) c.status = u.status;
            if ('reply' in u) c.reply = u.reply;
            c.answered = new Date().toISOString();
            await env.KV.put(`c:${slug}:${u.id}`, JSON.stringify(c));
            n++;
          }
          return json({ ok: true, updated: n });
        }

        if ((m = /^revoke\/([\w.-]+)$/.exec(tail)) && req.method === 'POST') {
          const proj = await getProject(env, m[1]);
          if (!proj) return bad('no such project', 404);
          proj.shareKey = newKey();
          await putProject(env, proj);
          return json(proj);
        }

        if ((m = /^delete\/([\w.-]+)$/.exec(tail)) && req.method === 'POST') {
          const slug = m[1];
          let cursor;
          do {
            const r = await env.KV.list({ prefix: `c:${slug}:`, cursor, limit: 1000 });
            for (const key of r.keys) await env.KV.delete(key.name);
            cursor = r.list_complete ? null : r.cursor;
          } while (cursor);
          do {
            const r = await env.KV.list({ prefix: `k:${slug}:`, cursor, limit: 1000 });
            for (const key of r.keys) await env.KV.delete(key.name);
            cursor = r.list_complete ? null : r.cursor;
          } while (cursor);
          await env.KV.delete(pKey(slug));
          return json({ ok: true });
        }

        return bad('unknown admin route', 404);
      }

      /* ── client API ────────────────────────────────────────── */

      const guard = async (slug) => {
        const proj = await getProject(env, slug);
        if (!proj) return { err: bad('no such project', 404) };
        if (!keyEq(k, proj.shareKey)) return { err: bad('bad or missing link key', 403) };
        return { proj };
      };

      let m;
      if ((m = /^\/api\/p\/([\w.-]+)$/.exec(p))) {
        const { proj, err } = await guard(m[1]);
        if (err) return err;
        const { shareKey, ...safe } = proj;
        safe.versions = safe.versions.map(({ asset, ...v }) => v); // never leak the repo
        return json({ ...safe, comments: await listComments(env, m[1]) });
      }

      if ((m = /^\/api\/p\/([\w.-]+)\/comments$/.exec(p)) && req.method === 'POST') {
        const slug = m[1];
        const { proj, err } = await guard(slug);
        if (err) return err;
        const b = await req.json();
        const c = {
          id: newId(),
          version: Number(b.version) || proj.versions.length,
          scope: b.scope === 'global' ? 'global' : 'frame',
          t: Number(b.t) || 0,
          frame: Number(b.frame) || 0,
          text: String(b.text || '').slice(0, 4000),
          shapes: Array.isArray(b.shapes) ? b.shapes.slice(0, 60) : [],
          markup: null,
          status: 'open',
          reply: null,
          source: 'client',
          created: new Date().toISOString(),
        };
        if (typeof b.markupData === 'string' && b.markupData.startsWith('data:image/jpeg;base64,')) {
          const bin = Uint8Array.from(atob(b.markupData.split(',')[1]), (ch) => ch.charCodeAt(0));
          if (bin.length < 20 * 1024 * 1024) {
            await env.KV.put(`k:${slug}:${c.id}.jpg`, bin);
            c.markup = `${c.id}.jpg`;
          }
        }
        await env.KV.put(`c:${slug}:${c.id}`, JSON.stringify(c));
        return json(c);
      }

      if ((m = /^\/api\/p\/([\w.-]+)\/comments\/([\w.-]+)$/.exec(p))) {
        const [, slug, id] = m;
        const { err } = await guard(slug);
        if (err) return err;
        const c = await env.KV.get(`c:${slug}:${id}`, 'json');
        if (!c) return bad('no such comment', 404);

        if (req.method === 'DELETE') {
          if (c.source !== 'client') return bad('not yours to delete', 403);
          await env.KV.delete(`c:${slug}:${id}`);
          if (c.markup) await env.KV.delete(`k:${slug}:${c.markup}`);
          return json({ ok: true });
        }
        const b = await req.json();
        for (const f of ['text', 'status', 'scope']) if (f in b) c[f] = b[f];
        c.updated = new Date().toISOString();
        await env.KV.put(`c:${slug}:${id}`, JSON.stringify(c));
        return json(c);
      }

      if ((m = /^\/api\/p\/([\w.-]+)\/submit$/.exec(p)) && req.method === 'POST') {
        const { proj, err } = await guard(m[1]);
        if (err) return err;
        const cs = await listComments(env, m[1]);
        const open = cs.filter((c) => c.status !== 'resolved').length;
        proj.submissions = proj.submissions || [];
        proj.submissions.push({ at: new Date().toISOString(), open, version: proj.versions.length });
        await putProject(env, proj);
        return json({ ok: true, open, submissions: proj.submissions.length });
      }

      if ((m = /^\/media\/([\w.-]+)\/(\d+)$/.exec(p))) {
        const { proj, err } = await guard(m[1]);
        if (err) return err;
        const ver = proj.versions.find((v) => v.v === Number(m[2]));
        if (!ver?.asset) return new Response('no such version', { status: 404 });
        return serveVideo(env, ver.asset, req);
      }

      if ((m = /^\/markup\/([\w.-]+)\/([\w.-]+)$/.exec(p))) {
        const { err } = await guard(m[1]);
        if (err) return err;
        const buf = await env.KV.get(`k:${m[1]}:${m[2]}`, 'arrayBuffer');
        if (!buf) return new Response('not found', { status: 404 });
        return new Response(buf, {
          headers: { 'content-type': 'image/jpeg', 'cache-control': 'private, max-age=3600' },
        });
      }

      /* ── the app ───────────────────────────────────────────── */

      // no index route on purpose: a client link must never enumerate other work
      if (p === '/') return new Response('Reel Review', { status: 200 });
      if (/^\/v\/[\w.-]+$/.test(p)) {
        return env.ASSETS.fetch(new Request(new URL('/index.html', url), req));
      }
      return env.ASSETS.fetch(req);
    } catch (e) {
      return bad(String(e.message || e), 500);
    }
  },
};
