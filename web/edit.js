/* A real edit, small enough to finish while somebody watches.
 *
 * This is NOT the full pipeline. The full pipeline has an agent author a bespoke
 * composition per video and then renders it at 4K, which takes 10 to 25 minutes.
 * What runs here is the automatic subset, the part that needs no judgement:
 *
 *   probe -> transcribe -> cut dead air -> crop to 9:16 -> burn captions -> loudnorm
 *
 * It operates on the file the user actually uploaded, so what comes back is their
 * footage, changed. Every stage is independently recoverable: if one fails the
 * edit continues without it and says so, because a demo that returns something
 * imperfect beats a demo that returns an error.
 */
'use strict';
const { spawn } = require('child_process');
const fs   = require('fs');
const fsp  = fs.promises;
const path = require('path');
const os   = require('os');

function run(cmd, args, { timeout = 180000 } = {}) {
  return new Promise((resolve) => {
    let out = '', err = '', done = false;
    let p;
    try { p = spawn(cmd, args); }
    catch (e) { return resolve({ ok: false, err: cmd + ' not runnable: ' + e.message }); }
    const t = setTimeout(() => { if (!done) { try { p.kill('SIGKILL'); } catch {} } }, timeout);
    p.stdout.on('data', (d) => { out += d; });
    p.stderr.on('data', (d) => { err += d; });
    p.on('error', (e) => { done = true; clearTimeout(t); resolve({ ok: false, err: e.message }); });
    p.on('close', (code) => { done = true; clearTimeout(t); resolve({ ok: code === 0, code, out, err }); });
  });
}

async function probe(file) {
  const r = await run('ffprobe', ['-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height,r_frame_rate',
    '-show_entries', 'format=duration', '-of', 'json', file], { timeout: 30000 });
  if (!r.ok) return null;
  try {
    const j = JSON.parse(r.out);
    const s = (j.streams || [])[0] || {};
    return {
      w: +s.width || 0, h: +s.height || 0,
      dur: parseFloat((j.format || {}).duration) || 0,
    };
  } catch { return null; }
}

/* Dead air is the single biggest difference between a raw take and a cut one.
 * silencedetect gives us the gaps; we keep everything else.
 * Guard rail: if the cut would remove more than half the take the detection is
 * wrong for this recording (music bed, noisy room), so we keep the original. */
async function silenceKeeps(file, dur) {
  const r = await run('ffmpeg', ['-v', 'info', '-i', file, '-af',
    'silencedetect=noise=-32dB:d=0.35', '-f', 'null', '-'], { timeout: 120000 });
  const text = (r.err || '');
  const starts = [...text.matchAll(/silence_start:\s*([0-9.]+)/g)].map((m) => +m[1]);
  const ends   = [...text.matchAll(/silence_end:\s*([0-9.]+)/g)].map((m) => +m[1]);
  if (!starts.length) return null;

  const keeps = [];
  let cur = 0;
  for (let i = 0; i < starts.length; i++) {
    const s = starts[i];
    const e = (i < ends.length ? ends[i] : dur);
    // leave 0.12s of air either side, a hard butt cut on the word sounds clipped
    const a = Math.max(cur, 0), bEnd = Math.max(a, s + 0.12);
    if (bEnd - a > 0.35) keeps.push([a, bEnd]);
    cur = Math.max(cur, e - 0.12);
  }
  if (dur - cur > 0.35) keeps.push([cur, dur]);
  if (!keeps.length) return null;

  const kept = keeps.reduce((acc, [a, b]) => acc + (b - a), 0);
  if (kept < dur * 0.5) return null;          // detection is wrong for this take
  if (kept > dur * 0.985) return null;        // nothing worth cutting
  return keeps;
}

function srtTime(t) {
  const ms = Math.max(0, Math.round(t * 1000));
  const h = Math.floor(ms / 3600000), m = Math.floor(ms / 60000) % 60;
  const s = Math.floor(ms / 1000) % 60, x = ms % 1000;
  const p = (n, w) => String(n).padStart(w, '0');
  return `${p(h, 2)}:${p(m, 2)}:${p(s, 2)},${p(x, 3)}`;
}

/* Whisper writes an SRT next to the audio. We re-wrap it to short lines, because
 * a full sentence burned across a 1080 wide frame is unreadable on a phone. */
async function rewrapSrt(srcSrt, dstSrt, maxChars = 30) {
  let raw;
  try { raw = await fsp.readFile(srcSrt, 'utf8'); } catch { return false; }
  const blocks = raw.split(/\r?\n\r?\n/).filter(Boolean);
  const cues = [];
  for (const b of blocks) {
    const lines = b.split(/\r?\n/).filter(Boolean);
    const tl = lines.find((l) => l.includes('-->'));
    if (!tl) continue;
    const m = /([\d:,.]+)\s*-->\s*([\d:,.]+)/.exec(tl);
    if (!m) continue;
    const toS = (v) => { const p = v.replace(',', '.').split(':').map(parseFloat);
      return p.length === 3 ? p[0] * 3600 + p[1] * 60 + p[2] : p[0] * 60 + p[1]; };
    const t0 = toS(m[1]), t1 = toS(m[2]);
    const text = lines.slice(lines.indexOf(tl) + 1).join(' ').trim();
    if (!text) continue;

    const words = text.split(/\s+/);
    const chunks = []; let cur = '';
    for (const w of words) {
      if ((cur + ' ' + w).trim().length > maxChars && cur) { chunks.push(cur.trim()); cur = w; }
      else cur = (cur + ' ' + w).trim();
    }
    if (cur) chunks.push(cur);
    const step = (t1 - t0) / chunks.length;
    chunks.forEach((c, i) => cues.push({ a: t0 + i * step, b: t0 + (i + 1) * step, text: c.toUpperCase() }));
  }
  if (!cues.length) return false;
  const out = cues.map((c, i) =>
    `${i + 1}\n${srtTime(c.a)} --> ${srtTime(c.b)}\n${c.text}\n`).join('\n');
  await fsp.writeFile(dstSrt, out, 'utf8');
  return true;
}

/* ── the edit ─────────────────────────────────────────────────────────────── */
async function edit(input, outFile, onStage) {
  const work = await fsp.mkdtemp(path.join(os.tmpdir(), 'rfedit-'));
  const notes = [];
  const stage = (k, s, d) => { try { onStage && onStage(k, s, d); } catch {} };

  try {
    stage('probe', 'running');
    const info = await probe(input);
    if (!info || !info.dur) { stage('probe', 'failed'); return { ok: false, err: 'could not read that file as video' }; }
    stage('probe', 'done', `${info.w}x${info.h}, ${info.dur.toFixed(1)}s`);

    // 1. transcribe
    stage('whisper', 'running');
    const wav = path.join(work, 'a.wav');
    await run('ffmpeg', ['-v', 'error', '-y', '-i', input, '-vn', '-ac', '1', '-ar', '16000', wav], { timeout: 120000 });
    let srt = null;
    const w = await run('whisper', [wav, '--model', 'tiny', '--output_format', 'srt',
      '--output_dir', work, '--fp16', 'False', '--verbose', 'False'], { timeout: 240000 });
    const cand = path.join(work, 'a.srt');
    if (w.ok && fs.existsSync(cand)) {
      const wrapped = path.join(work, 'burn.srt');
      if (await rewrapSrt(cand, wrapped)) { srt = wrapped; stage('whisper', 'done', 'captions timed'); }
      else { stage('whisper', 'done', 'no speech found'); notes.push('no speech detected, captions skipped'); }
    } else {
      stage('whisper', 'skipped'); notes.push('transcription unavailable, captions skipped');
    }

    // 2. dead air
    stage('cut', 'running');
    let keeps = null;
    try { keeps = await silenceKeeps(input, info.dur); } catch {}
    let cutSrc = input, cutDur = info.dur;
    if (keeps && keeps.length > 1) {
      const sel = keeps.map(([a, b]) => `between(t,${a.toFixed(3)},${b.toFixed(3)})`).join('+');
      const trimmed = path.join(work, 'cut.mp4');
      const r = await run('ffmpeg', ['-v', 'error', '-y', '-i', input,
        '-vf', `select='${sel}',setpts=N/FRAME_RATE/TB`,
        '-af', `aselect='${sel}',asetpts=N/SR/TB`,
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'aac', trimmed],
        { timeout: 240000 });
      if (r.ok && fs.existsSync(trimmed)) {
        cutSrc = trimmed;
        const ni = await probe(trimmed);
        cutDur = (ni && ni.dur) || cutDur;
        stage('cut', 'done', `${(info.dur - cutDur).toFixed(1)}s of dead air removed`);
      } else { stage('cut', 'skipped'); notes.push('silence cut failed, full take kept'); }
    } else {
      stage('cut', 'done', 'no dead air worth cutting');
    }
    // captions were timed against the uncut audio, so a cut invalidates them
    if (cutSrc !== input && srt) { srt = null; notes.push('captions dropped: timings belong to the uncut take'); }

    // 3. frame it 9:16 and burn the captions
    stage('frame', 'running');
    const vf = [
      // cover-crop to 9:16 without ever stretching the subject
      "scale=1080:1920:force_original_aspect_ratio=increase",
      "crop=1080:1920",
    ];
    if (srt) {
      const esc = srt.replace(/\\/g, '/').replace(/:/g, '\\:').replace(/'/g, "\\'");
      // These numbers are NOT in 1080x1920 space. libass lays the subtitle out on its
      // own default canvas and scales the result up, so Fontsize and MarginV are in
      // that smaller space and the multiplier is roughly 6.6x at this frame size.
      // Fontsize 9 lands near 60px on screen; MarginV 58 lifts the caption about 385px
      // off the bottom, which clears the Instagram UI band at y1600.
      //
      // Do not "fix" this by adding original_size without re-rendering and LOOKING at
      // a frame. Two attempts to make these values absolute silently produced no
      // caption at all, and the burn reports success either way.
      vf.push("subtitles='" + esc + "':force_style='FontName=Arial,Fontsize=9,Bold=1," +
              "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0," +
              "Alignment=2,MarginV=58'");
    }
    const r2 = await run('ffmpeg', ['-v', 'error', '-y', '-i', cutSrc,
      '-vf', vf.join(','), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
      '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k',
      '-movflags', '+faststart', outFile], { timeout: 300000 });
    if (!r2.ok || !fs.existsSync(outFile)) {
      stage('frame', 'failed');
      return { ok: false, err: 'the render step failed: ' + String(r2.err || '').slice(-240) };
    }
    stage('frame', 'done', srt ? '1080x1920, captions burned' : '1080x1920');

    const final = await probe(outFile);
    stage('deliver', 'done', final ? `${final.w}x${final.h}, ${final.dur.toFixed(1)}s` : 'complete');
    return { ok: true, notes, duration: final ? final.dur : cutDur, srtBurned: !!srt };
  } finally {
    fsp.rm(work, { recursive: true, force: true }).catch(() => {});
  }
}

module.exports = { edit, probe };
