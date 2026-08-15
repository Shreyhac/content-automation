/* Reel Review — frame-pinned comments + markup over a local render. */

const $ = (s) => document.querySelector(s);
const slug = decodeURIComponent(location.pathname.split('/v/')[1] || '');

// One build serves two homes: the local server (./rr) and the Cloudflare worker a
// client opens with ?k=<share key>. Hosted mode carries the key on every request.
const KEY = new URLSearchParams(location.search).get('k') || '';
const HOSTED = !!KEY;
const API = HOSTED ? `/api/p/${slug}` : `/api/project/${slug}`;
const wk = (u) => (KEY ? u + (u.includes('?') ? '&' : '?') + 'k=' + encodeURIComponent(KEY) : u);

const S = {
  proj: null,
  comments: [],
  v: 0,            // active version (0 → load() picks the newest)
  cmp: 0,          // compare version (0 = off)
  fps: 30,
  dur: 0,
  tool: 'box',
  color: '#E5372B',
  shapes: [],      // normalized, current draft
  sel: null,       // selected comment id
  filter: 'open',
  composing: false,
};

const COLORS = ['#E5372B', '#DA7756', '#E8B33C', '#3CE6AC', '#FFFFFF'];

const vidA = $('#vidA'), vidB = $('#vidB');
const frameEl = $('#frame'), draw = $('#draw'), ghost = $('#ghost');
const dctx = draw.getContext('2d'), gctx = ghost.getContext('2d');

const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const fmt = (t) => {
  if (!isFinite(t)) t = 0;
  const m = Math.floor(t / 60), s = t - m * 60;
  return `${m}:${s.toFixed(2).padStart(5, '0')}`;
};
const frameOf = (t) => Math.round(t * S.fps);
const isOpen = (c) => c.status !== 'resolved' && c.status !== 'wontfix';

let toastTimer;
function toast(msg, ms = 2600) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('on');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('on'), ms);
}

const api = async (url, opts = {}) => {
  const r = await fetch(url, {
    ...opts,
    headers: opts.body ? { 'content-type': 'application/json' } : undefined,
  });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
  return r.json();
};

/* ── boot ────────────────────────────────────────────────── */

async function load() {
  const p = await api(wk(API));
  S.proj = p;
  S.comments = p.comments || [];
  const latest = p.versions[p.versions.length - 1];
  if (!S.v || !p.versions.find((x) => x.v === S.v)) S.v = latest.v;
  const ver = p.versions.find((x) => x.v === S.v);
  S.fps = ver.fps || 30;
  S.dur = ver.duration;

  $('#name').textContent = p.name || p.slug;
  $('#meta').textContent = `${ver.width}×${ver.height} · ${ver.fps}fps · ${ver.duration.toFixed(2)}s` +
    (HOSTED ? '' : ` · ${ver.path}`);
  if (HOSTED) $('#backLink').style.display = 'none';
  document.title = (p.name || p.slug) + ' · Reel Review';

  if (vidA.dataset.v !== String(S.v)) {
    vidA.src = wk(`/media/${slug}/${S.v}`);
    vidA.dataset.v = String(S.v);
  }
  renderVersions();
  renderAll();
}

function renderVersions() {
  const box = $('#vpills');
  box.innerHTML = '';
  S.proj.versions.forEach((ver) => {
    const b = document.createElement('button');
    b.className = 'vpill' + (ver.v === S.v ? ' on' : '') + (ver.v === S.cmp ? ' cmp' : '');
    b.textContent = 'v' + ver.v;
    b.title = `${ver.path} · added ${new Date(ver.added).toLocaleString()}` +
      (ver.label ? `\n${ver.label}` : '');
    b.onclick = () => {
      if (S.cmp && ver.v === S.v) return;
      S.v = ver.v;
      S.cmp = 0;
      frameEl.classList.remove('compare');
      load();
    };
    box.appendChild(b);
  });
}

/* ── layout: fit the frame to the viewport ───────────────── */

function fit() {
  const vp = $('#viewport');
  const w = vidA.videoWidth || 1080, h = vidA.videoHeight || 1920;
  const availW = Math.max(120, vp.clientWidth - 36);
  const availH = Math.max(120, vp.clientHeight - 36);
  const scale = Math.min(availW / w, availH / h, 1.5);
  frameEl.style.width = Math.floor(w * scale) + 'px';
  frameEl.style.height = Math.floor(h * scale) + 'px';
  for (const c of [draw, ghost]) {
    c.width = frameEl.clientWidth;
    c.height = frameEl.clientHeight;
  }
  paintDraft();
  paintGhost();
  renderPins();
}
window.addEventListener('resize', fit);

vidA.addEventListener('loadedmetadata', () => {
  S.dur = vidA.duration || S.dur;
  fit();
  renderRuler();
  tick();
});

/* ── transport ───────────────────────────────────────────── */

function seek(t) {
  t = clamp(t, 0, Math.max(0, (S.dur || vidA.duration) - 1 / S.fps));
  vidA.currentTime = t;
  if (S.cmp) vidB.currentTime = t;
  tick();
}
const step = (n) => { vidA.pause(); seek(vidA.currentTime + n / S.fps); };

$('#bPlay').onclick = () => (vidA.paused ? play() : pause());
$('#bPrev').onclick = () => step(-1);
$('#bNext').onclick = () => step(1);

function play() {
  if (S.composing) return;
  vidA.play();
  if (S.cmp) { vidB.currentTime = vidA.currentTime; vidB.play(); }
  $('#bPlay').textContent = '❚❚';
}
function pause() {
  vidA.pause(); vidB.pause();
  $('#bPlay').textContent = '▶';
}
vidA.addEventListener('play', () => ($('#bPlay').textContent = '❚❚'));
vidA.addEventListener('pause', () => ($('#bPlay').textContent = '▶'));

/* ── playback speed ──────────────────────────────────────── */
// a switched src resets playbackRate to 1, so applyRate() re-runs on every load
const RATES = [0.5, 0.75, 1, 1.25, 1.5, 2];
S.rate = Number(localStorage.getItem('rr.rate')) || 1;
if (!RATES.includes(S.rate)) S.rate = 1;

function applyRate() {
  vidA.playbackRate = vidB.playbackRate = S.rate;
  const b = $('#bSpeed');
  b.textContent = (S.rate === 1 ? '1' : String(S.rate)) + '×';
  b.classList.toggle('on', S.rate !== 1);
  localStorage.setItem('rr.rate', String(S.rate));
}
// the button cycles (wraps); the < / > keys nudge and stop at the ends
function setRate(n, wrap) {
  const at = RATES.indexOf(S.rate) + n;
  S.rate = RATES[wrap ? (at + RATES.length) % RATES.length : clamp(at, 0, RATES.length - 1)];
  applyRate();
  toast(`speed ${S.rate}×`, 900);
}
$('#bSpeed').onclick = (e) => setRate(e.shiftKey ? -1 : 1, true);
$('#bSpeed').oncontextmenu = (e) => { e.preventDefault(); setRate(-1, true); };
vidA.addEventListener('loadedmetadata', applyRate);
vidB.addEventListener('loadedmetadata', applyRate);
applyRate();

// while paused the rAF loop is idle, so the readout has to follow the seek itself
vidA.addEventListener('seeked', () => tick());
vidA.addEventListener('timeupdate', () => { if (vidA.paused) tick(); });

function tick() {
  const t = vidA.currentTime || 0;
  $('#tc').innerHTML = `<b>${fmt(t)}</b> / ${fmt(S.dur)} · f<b>${frameOf(t)}</b>`;
  const pc = S.dur ? (t / S.dur) * 100 : 0;
  $('#playhead').style.left = pc + '%';
  $('#played').style.width = pc + '%';
  renderPins();
}
function loop() {
  if (!vidA.paused) tick();
  requestAnimationFrame(loop);
}
loop();

/* ── timeline ────────────────────────────────────────────── */

const track = $('#track');
const tFromEvent = (e) => {
  const r = track.getBoundingClientRect();
  return clamp((e.clientX - r.left) / r.width, 0, 1) * S.dur;
};
let scrubbing = false;
track.addEventListener('pointerdown', (e) => {
  if (e.target.classList.contains('mk')) return;
  scrubbing = true;
  track.setPointerCapture(e.pointerId);
  vidA.pause();
  seek(tFromEvent(e));
});
track.addEventListener('pointermove', (e) => { if (scrubbing) seek(tFromEvent(e)); });
track.addEventListener('pointerup', () => (scrubbing = false));

function renderRuler() {
  const r = $('#ruler');
  r.innerHTML = '';
  if (!S.dur) return;
  const targets = [1, 2, 5, 10, 15, 30, 60];
  const stepS = targets.find((x) => S.dur / x <= 12) || 60;
  for (let t = 0; t <= S.dur + 0.001; t += stepS) {
    const s = document.createElement('span');
    s.style.left = (t / S.dur) * 100 + '%';
    s.textContent = fmt(t).replace(/\.00$/, '');
    r.appendChild(s);
  }
}

function renderMarks() {
  const box = $('#marks');
  box.innerHTML = '';
  visible().filter((c) => c.scope !== 'global').forEach((c) => {
    const d = document.createElement('div');
    d.className = 'mk' + (isOpen(c) ? '' : ' done') + (S.sel === c.id ? ' sel' : '');
    d.style.left = (c.t / S.dur) * 100 + '%';
    d.title = `${fmt(c.t)} · ${c.text.slice(0, 80)}`;
    d.onclick = (e) => { e.stopPropagation(); select(c.id, true); };
    box.appendChild(d);
  });

  const lane = $('#globalLane');
  const gs = S.comments.filter((c) => c.scope === 'global' && (S.filter === 'all' || isOpen(c)));
  lane.innerHTML = gs.length ? '<span>whole video:</span>' : '';
  gs.forEach((c) => {
    const s = document.createElement('span');
    s.className = 'gchip';
    s.textContent = c.text.replace(/\s+/g, ' ').slice(0, 60);
    s.onclick = () => select(c.id, true);
    lane.appendChild(s);
  });
}

/* ── comment list ────────────────────────────────────────── */

function visible() {
  const list = [...S.comments].sort((a, b) => {
    if ((a.scope === 'global') !== (b.scope === 'global')) return a.scope === 'global' ? -1 : 1;
    return a.t - b.t;
  });
  if (S.filter === 'open') return list.filter(isOpen);
  if (S.filter === 'global') return list.filter((c) => c.scope === 'global');
  return list;
}

function renderList() {
  const box = $('#list');
  box.innerHTML = '';
  const items = visible();
  $('#count').textContent = `${S.comments.filter(isOpen).length} open / ${S.comments.length}`;

  if (!items.length) {
    box.innerHTML = `<div class="empty">No notes yet.<br><br>
      Scrub to a frame, draw on it, press <kbd>C</kbd>.<br>
      <kbd>G</kbd> for a note about the whole video.</div>`;
    return;
  }

  items.forEach((c, i) => {
    const el = document.createElement('div');
    el.className = 'card' + (c.scope === 'global' ? ' global' : '') +
      (isOpen(c) ? '' : ' done') + (S.sel === c.id ? ' sel' : '');
    el.onclick = () => select(c.id, true);

    const head = document.createElement('div');
    head.className = 'crow';
    head.innerHTML = c.scope === 'global'
      ? `<span class="badge g">whole video</span><span class="n mono">@ ${fmt(c.t)}</span>`
      : `<span class="badge t mono">${fmt(c.t)}</span><span class="n mono">f${c.frame}</span>`;
    head.innerHTML += `<span class="badge v">v${c.version}</span>`;
    if (!isOpen(c)) head.innerHTML += `<span class="badge ok">${c.status}</span>`;
    el.appendChild(head);

    const t = document.createElement('div');
    t.className = 'txt';
    t.textContent = c.text;
    el.appendChild(t);

    if (c.markup) {
      const img = document.createElement('img');
      img.className = 'thumb';
      img.loading = 'lazy';
      img.src = wk(`/markup/${slug}/${c.markup}`);
      el.appendChild(img);
    }

    if (c.reply) {
      const r = document.createElement('div');
      r.className = 'reply';
      r.textContent = '↪ ' + c.reply;
      el.appendChild(r);
    }

    const acts = document.createElement('div');
    acts.className = 'cacts';
    const mk = (label, fn) => {
      const b = document.createElement('button');
      b.textContent = label;
      b.onclick = (e) => { e.stopPropagation(); fn(); };
      acts.appendChild(b);
    };
    mk(isOpen(c) ? '✓ resolve' : '↺ reopen', () => patch(c.id, { status: isOpen(c) ? 'resolved' : 'open' }));
    mk('edit', () => {
      const v = prompt('Edit note', c.text);
      if (v != null) patch(c.id, { text: v });
    });
    mk(c.scope === 'global' ? '→ pin to frame' : '→ whole video',
      () => patch(c.id, { scope: c.scope === 'global' ? 'frame' : 'global' }));
    mk('delete', async () => {
      if (!confirm('Delete this note?')) return;
      await api(wk(`${API}/comments/${c.id}`), { method: 'DELETE' });
      S.comments = S.comments.filter((x) => x.id !== c.id);
      if (S.sel === c.id) S.sel = null;
      renderAll();
    });
    el.appendChild(acts);
    box.appendChild(el);
  });
}

async function patch(id, body) {
  const updated = await api(wk(`${API}/comments/${id}`), {
    method: 'PATCH', body: JSON.stringify(body),
  });
  S.comments = S.comments.map((c) => (c.id === id ? updated : c));
  renderAll();
}

function select(id, doSeek) {
  S.sel = S.sel === id ? null : id;
  const c = S.comments.find((x) => x.id === id);
  if (S.sel && doSeek && c && c.scope !== 'global') {
    pause();
    if (c.version !== S.v && S.proj.versions.find((v) => v.v === c.version)) {
      S.v = c.version;
      load().then(() => setTimeout(() => seek(c.t), 120));
    } else seek(c.t);
  }
  renderAll();
  const card = [...document.querySelectorAll('.card')].find((el) => el.classList.contains('sel'));
  card?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

function renderAll() { renderList(); renderMarks(); renderPins(); paintGhost(); }

/* ── pins over the frame ─────────────────────────────────── */

function renderPins() {
  const box = $('#pins');
  box.innerHTML = '';
  const t = vidA.currentTime || 0;
  const near = S.comments.filter((c) =>
    c.scope !== 'global' && c.version === S.v && isOpen(c) &&
    (Math.abs(c.t - t) < 0.4 || c.id === S.sel));
  const order = visible().filter((c) => c.scope !== 'global');
  near.forEach((c) => {
    const anchor = (c.shapes && c.shapes[0]) || { x: 0.5, y: 0.12 };
    const d = document.createElement('div');
    d.className = 'pin' + (S.sel === c.id ? ' sel' : '');
    d.style.left = (anchor.x * 100) + '%';
    d.style.top = (anchor.y * 100) + '%';
    d.innerHTML = `<span>${order.indexOf(c) + 1}</span>`;
    d.title = c.text.slice(0, 120);
    d.onclick = () => select(c.id, false);
    box.appendChild(d);
  });
}

/* ── drawing ─────────────────────────────────────────────── */

function shapePath(ctx, s, W, H) {
  ctx.strokeStyle = s.color;
  ctx.fillStyle = s.color;
  ctx.lineWidth = Math.max(2, Math.round(W / 300));
  ctx.lineJoin = ctx.lineCap = 'round';
  const x = s.x * W, y = s.y * H;
  if (s.type === 'box') {
    ctx.strokeRect(x, y, s.w * W, s.h * H);
  } else if (s.type === 'arrow') {
    const x2 = s.x2 * W, y2 = s.y2 * H;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke();
    const a = Math.atan2(y2 - y, x2 - x), head = Math.max(10, W / 55);
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - head * Math.cos(a - 0.4), y2 - head * Math.sin(a - 0.4));
    ctx.lineTo(x2 - head * Math.cos(a + 0.4), y2 - head * Math.sin(a + 0.4));
    ctx.closePath(); ctx.fill();
  } else if (s.type === 'pen') {
    ctx.beginPath();
    s.pts.forEach((p, i) => (i ? ctx.lineTo(p[0] * W, p[1] * H) : ctx.moveTo(p[0] * W, p[1] * H)));
    ctx.stroke();
  } else if (s.type === 'pin') {
    const r = Math.max(7, W / 90);
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 2; ctx.stroke();
    ctx.beginPath(); ctx.arc(x, y, r * 2.1, 0, Math.PI * 2);
    ctx.strokeStyle = s.color; ctx.lineWidth = Math.max(2, W / 400); ctx.stroke();
  }
}

function paintDraft() {
  dctx.clearRect(0, 0, draw.width, draw.height);
  S.shapes.forEach((s) => shapePath(dctx, s, draw.width, draw.height));
  if (live) shapePath(dctx, live, draw.width, draw.height);
}

function paintGhost() {
  gctx.clearRect(0, 0, ghost.width, ghost.height);
  const c = S.comments.find((x) => x.id === S.sel);
  if (!c || !c.shapes?.length || S.composing) return;
  c.shapes.forEach((s) => shapePath(gctx, s, ghost.width, ghost.height));
}

let live = null, drawing = false;
const norm = (e) => {
  const r = draw.getBoundingClientRect();
  return [clamp((e.clientX - r.left) / r.width, 0, 1), clamp((e.clientY - r.top) / r.height, 0, 1)];
};

draw.addEventListener('pointerdown', (e) => {
  draw.setPointerCapture(e.pointerId);
  const [x, y] = norm(e);
  drawing = true;
  if (S.tool === 'pin') {
    S.shapes.push({ type: 'pin', x, y, color: S.color });
    drawing = false;
    paintDraft();
    return;
  }
  live = S.tool === 'pen'
    ? { type: 'pen', pts: [[x, y]], x, y, color: S.color }
    : { type: S.tool, x, y, w: 0, h: 0, x2: x, y2: y, color: S.color };
  paintDraft();
});

draw.addEventListener('pointermove', (e) => {
  if (!drawing || !live) return;
  const [x, y] = norm(e);
  if (live.type === 'pen') live.pts.push([x, y]);
  else if (live.type === 'box') { live.w = x - live.x; live.h = y - live.y; }
  else { live.x2 = x; live.y2 = y; }
  paintDraft();
});

draw.addEventListener('pointerup', () => {
  drawing = false;
  if (!live) return;
  if (live.type === 'box') {
    if (live.w < 0) { live.x += live.w; live.w = -live.w; }
    if (live.h < 0) { live.y += live.h; live.h = -live.h; }
    if (live.w < 0.01 || live.h < 0.01) { live = null; paintDraft(); return; }
  }
  if (live.type === 'pen') {
    const xs = live.pts.map((p) => p[0]), ys = live.pts.map((p) => p[1]);
    live.cx = (Math.min(...xs) + Math.max(...xs)) / 2;
    live.cy = (Math.min(...ys) + Math.max(...ys)) / 2;
    live.x = Math.min(...xs); live.y = Math.min(...ys);
  }
  S.shapes.push(live);
  live = null;
  paintDraft();
  if (!S.composing) openComposer(false);
});

$('#bUndo').onclick = () => { S.shapes.pop(); paintDraft(); };

function setTool(name) {
  S.tool = name;
  document.querySelectorAll('.tool[data-tool]').forEach((x) =>
    x.classList.toggle('on', x.dataset.tool === name));
  // the pointer tool lifts the canvas so the frame itself is clickable again
  frameEl.classList.toggle('drawing', name !== 'pointer');
}
document.querySelectorAll('.tool[data-tool]').forEach((b) => {
  b.onclick = () => setTool(b.dataset.tool);
});
setTool('box');

// click the frame to play/pause, but only when no drawing tool is armed
frameEl.addEventListener('click', (e) => {
  if (S.tool !== 'pointer' || S.composing) return;
  if (e.target.closest('.pin') || e.target === $('#cmpHandle')) return;
  vidA.paused ? play() : pause();
});

const sw = $('#swatches');
COLORS.forEach((c, i) => {
  const b = document.createElement('button');
  b.className = 'sw' + (i === 0 ? ' on' : '');
  b.style.background = c;
  b.onclick = () => {
    S.color = c;
    [...sw.children].forEach((x) => x.classList.toggle('on', x === b));
  };
  sw.appendChild(b);
});

/* ── composer ────────────────────────────────────────────── */

function openComposer(global) {
  pause();
  S.composing = true;
  $('#composer').classList.remove('hidden');
  $('#cmpGlobal').checked = !!global;
  const t = vidA.currentTime || 0;
  $('#cmpMeta').innerHTML = global
    ? `<span class="badge g">whole video</span><span class="mono">noted at ${fmt(t)}</span>`
    : `<span class="badge t mono">${fmt(t)}</span><span class="mono">frame ${frameOf(t)} · v${S.v}</span>` +
      (S.shapes.length ? `<span class="mono" style="color:var(--terra)">${S.shapes.length} mark${S.shapes.length > 1 ? 's' : ''}</span>` : '');
  paintGhost();
  $('#cmpText').focus();
}

function closeComposer() {
  S.composing = false;
  S.shapes = [];
  live = null;
  paintDraft();
  $('#cmpText').value = '';
  $('#composer').classList.add('hidden');
  paintGhost();
}

$('#bComment').onclick = () => openComposer(false);
$('#bGlobal').onclick = () => openComposer(true);
$('#cmpCancel').onclick = closeComposer;
$('#cmpGlobal').onchange = () => openComposerRefresh();
function openComposerRefresh() {
  const keep = $('#cmpText').value;
  openComposer($('#cmpGlobal').checked);
  $('#cmpText').value = keep;
}

/** Bake the paused frame + markup into a JPEG so the editor sees exactly this. */
function bakeMarkup() {
  if (!S.shapes.length) return null;
  const W = vidA.videoWidth, H = vidA.videoHeight;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const x = c.getContext('2d');
  try { x.drawImage(vidA, 0, 0, W, H); } catch { return null; }
  S.shapes.forEach((s) => shapePath(x, s, W, H));
  return c.toDataURL('image/jpeg', 0.82);
}

$('#cmpSave').onclick = save;

// Saving a 4K markup frame takes a moment; without this guard a second ⌘⏎ or
// click while the first is in flight files the same note twice.
let saving = false;
async function save() {
  if (saving) return;
  const text = $('#cmpText').value.trim();
  if (!text) { $('#cmpText').focus(); return toast('Write the note first'); }
  saving = true;
  $('#cmpSave').disabled = true;
  try {
    await doSave(text);
  } catch (e) {
    toast('Could not save: ' + e.message, 6000);
  } finally {
    saving = false;
    $('#cmpSave').disabled = false;
  }
}

async function doSave(text) {
  const global = $('#cmpGlobal').checked;
  const t = vidA.currentTime || 0;
  const body = {
    version: S.v,
    scope: global ? 'global' : 'frame',
    t, frame: frameOf(t),
    text,
    shapes: S.shapes,
    markupData: bakeMarkup(),
  };
  const c = await api(wk(`${API}/comments`), { method: 'POST', body: JSON.stringify(body) });
  S.comments.push(c);
  closeComposer();
  renderAll();
  toast(global ? 'Whole-video note saved' : `Note saved at ${fmt(t)}`);
}

/* ── compare ─────────────────────────────────────────────── */

$('#btnCompare').onclick = () => {
  if (S.cmp) {
    S.cmp = 0;
    frameEl.classList.remove('compare');
    renderVersions();
    return;
  }
  const others = S.proj.versions.filter((v) => v.v !== S.v);
  if (!others.length) return toast('Only one version so far');
  // the one just before the active version, so the default read is before → after
  const older = others.filter((v) => v.v < S.v);
  const prev = older.length ? older[older.length - 1] : others[others.length - 1];
  S.cmp = prev.v;
  vidB.src = wk(`/media/${slug}/${prev.v}`);
  vidB.currentTime = vidA.currentTime;
  frameEl.classList.add('compare');
  $('#cmpLabels .l').textContent = 'v' + prev.v;
  $('#cmpLabels .r').textContent = 'v' + S.v;
  renderVersions();
  toast(`Comparing v${prev.v} (left) against v${S.v} (right), drag the handle`);
};

const handle = $('#cmpHandle');
handle.addEventListener('pointerdown', (e) => {
  handle.setPointerCapture(e.pointerId);
  const move = (ev) => {
    const r = frameEl.getBoundingClientRect();
    const pc = clamp((ev.clientX - r.left) / r.width, 0, 1);
    handle.style.left = pc * 100 + '%';
    vidB.style.clipPath = `inset(0 ${(1 - pc) * 100}% 0 0)`;
  };
  const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
  window.addEventListener('pointermove', move);
  window.addEventListener('pointerup', up);
  e.preventDefault();
});

/* ── send to editor ──────────────────────────────────────── */

$('#btnUpdate').onclick = async () => {
  const open = S.comments.filter(isOpen).length;
  if (!open) return toast('No open notes to send');
  $('#btnUpdate').disabled = true;
  try {
    if (HOSTED) {
      const r = await api(wk(`${API}/submit`), { method: 'POST' });
      toast(`Sent. ${r.open} note${r.open === 1 ? '' : 's'} are with the editor now. ` +
        'You can keep adding more, or close this tab.', 8000);
      return;
    }
    const r = await api(`/api/project/${slug}/round`, { method: 'POST' });
    toast(`Round ${r.round} sent · ${r.count} note${r.count === 1 ? '' : 's'} → ${r.file}`, 7000);
    await load();
  } catch (e) {
    toast('Failed: ' + e.message);
  } finally {
    $('#btnUpdate').disabled = false;
  }
};

$('#filter').onclick = (e) => {
  const b = e.target.closest('button[data-f]');
  if (!b) return;
  S.filter = b.dataset.f;
  [...$('#filter').children].forEach((x) => x.classList.toggle('on', x === b));
  renderAll();
};

$('#btnHelp').onclick = () => toast(
  'space play/pause · ←/→ frame · shift+←/→ 1s · , . also step · < > speed · C comment here · ' +
  'G whole-video note · 1-4 tools · ⌘⏎ save · esc cancel · click a marker to jump', 9000);

/* ── keyboard ────────────────────────────────────────────── */

document.addEventListener('keydown', (e) => {
  const typing = /input|textarea/i.test(e.target.tagName);
  if (typing) {
    if (e.key === 'Escape') { closeComposer(); e.preventDefault(); }
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { save(); e.preventDefault(); }
    return;
  }
  const k = e.key;
  if (k === ' ') { e.preventDefault(); vidA.paused ? play() : pause(); }
  else if (k === '<') { e.preventDefault(); setRate(-1); }
  else if (k === '>') { e.preventDefault(); setRate(1); }
  else if (k === 'ArrowLeft' || k === ',') { e.preventDefault(); e.shiftKey ? seek(vidA.currentTime - 1) : step(-1); }
  else if (k === 'ArrowRight' || k === '.') { e.preventDefault(); e.shiftKey ? seek(vidA.currentTime + 1) : step(1); }
  else if (k === 'c' || k === 'C') { e.preventDefault(); openComposer(false); }
  else if (k === 'g' || k === 'G') { e.preventDefault(); openComposer(true); }
  else if (k === 'Escape') { S.sel = null; renderAll(); }
  else if ('12345'.includes(k)) {
    document.querySelectorAll('.tool[data-tool]')[Number(k) - 1]?.click();
  } else if (k === 'Home') seek(0);
  else if (k === 'End') seek(S.dur);
});

load().catch((e) => {
  document.body.innerHTML = `<div class="wrap"><h1>Not found</h1><p class="lede">${e.message}</p>
    <p><a href="/">← back to all videos</a></p></div>`;
  document.body.className = 'gallery';
});
