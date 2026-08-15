/* Reel Factory: the app flow. Vanilla, no build step, no CDN.
   Five states in one document. The server contract is in the brief; if the server is
   unreachable we degrade to a local simulation so a stage demo never shows a blank screen. */
(function () {
  'use strict';

  var FPS = 30;
  var $ = function (id) { return document.getElementById(id); };

  var STATES = [
    { id: 's-auth', label: '01 Access' },
    { id: 's-upload', label: '02 Source' },
    { id: 's-pipe', label: '03 Build' },
    { id: 's-review', label: '04 Review' },
    { id: 's-done', label: '05 Delivery' }
  ];

  var app = {
    state: 0,
    provider: 'anthropic',
    session: null,
    job: null,
    file: null,
    duration: 0,
    notes: [],
    activeNote: null,
    offline: false,
    poll: null,
    started: 0
  };

  /* ---------------------------------------------------------------- helpers */

  function show(err, msg) {
    if (!err) return;
    if (msg) { err.textContent = msg; err.hidden = false; }
    else { err.textContent = ''; err.hidden = true; }
  }

  function tcode(t) {
    t = Math.max(0, t || 0);
    var m = Math.floor(t / 60), s = t - m * 60;
    return m + ':' + (s < 10 ? '0' : '') + s.toFixed(2);
  }

  function api(method, path, body) {
    var opt = { method: method, headers: { 'Accept': 'application/json' } };
    if (body !== undefined) {
      opt.headers['Content-Type'] = 'application/json';
      opt.body = JSON.stringify(body);
    }
    var timer, ctrl;
    if (typeof AbortController === 'function') {
      ctrl = new AbortController();
      opt.signal = ctrl.signal;
      timer = setTimeout(function () { ctrl.abort(); }, 8000);
    }
    return fetch(path, opt).then(function (r) {
      if (timer) clearTimeout(timer);
      if (!r.ok) throw new Error(method + ' ' + path + ' returned ' + r.status);
      return r.json();
    }, function (e) {
      if (timer) clearTimeout(timer);
      throw e;
    });
  }

  /* ------------------------------------------------------------ header/nav */

  function buildSteps() {
    var n = $('steps');
    n.innerHTML = '';
    STATES.forEach(function (s, i) {
      var b = document.createElement('span');
      b.className = 'step' + (i === app.state ? ' on' : (i < app.state ? ' past' : ''));
      b.textContent = s.label;
      n.appendChild(b);
    });
  }

  function goto(i) {
    app.state = i;
    STATES.forEach(function (s, k) { $(s.id).hidden = k !== i; });
    $('signout').hidden = i === 0;
    buildSteps();
    window.scrollTo(0, 0);
    if (i === 3) setTimeout(sizeCanvas, 60);
  }

  /* ------------------------------------------------------------------ AUTH */

  function keyShapeOK(provider, key) {
    key = (key || '').trim();
    if (provider === 'anthropic') {
      if (key.indexOf('sk-ant-') !== 0) return 'An Anthropic key starts with sk-ant-';
      if (key.length < 40) return 'That key is too short. Anthropic keys run well past 40 characters.';
      return null;
    }
    if (key.indexOf('sk-') !== 0) return 'An OpenAI key starts with sk-';
    if (key.indexOf('sk-ant-') === 0) return 'That is an Anthropic key. Switch the provider to Anthropic.';
    if (key.length < 20) return 'That key is too short to be a real OpenAI key.';
    return null;
  }

  function startSession(provider, shape, demo) {
    show($('autherr'), '');
    api('POST', '/api/session', { provider: provider, keyShape: shape, demo: !!demo })
      .then(function (d) {
        app.session = d.sessionId || ('local-' + Date.now());
        app.demo = !!d.demo;
        localStorage.setItem('rf.session', app.session);
        localStorage.setItem('rf.provider', provider);
        $('sessid').textContent = 'session ' + app.session;
        goto(1);
      })
      .catch(function () {
        /* Server down. Do not strand the user: run offline and say so plainly. */
        app.offline = true;
        app.session = 'offline-' + Date.now().toString(36);
        localStorage.setItem('rf.session', app.session);
        $('sessid').textContent = 'session ' + app.session + ' (offline)';
        show($('autherr'), 'Server unreachable, running in offline demo mode. The pipeline is simulated locally.');
        goto(1);
      });
  }

  function bindAuth() {
    Array.prototype.forEach.call(document.querySelectorAll('.prov'), function (b) {
      b.addEventListener('click', function () {
        app.provider = b.getAttribute('data-prov');
        Array.prototype.forEach.call(document.querySelectorAll('.prov'), function (o) {
          o.classList.toggle('sel', o === b);
        });
        $('provsel').value = app.provider;
        $('keyin').placeholder = app.provider === 'anthropic' ? 'sk-ant-...' : 'sk-...';
        $('keyin').focus();
        show($('keyerr'), '');
      });
    });

    $('provsel').addEventListener('change', function () {
      app.provider = $('provsel').value;
      $('keyin').placeholder = app.provider === 'anthropic' ? 'sk-ant-...' : 'sk-...';
      show($('keyerr'), '');
    });

    $('keygo').addEventListener('click', function () {
      var p = $('provsel').value, k = $('keyin').value;
      var bad = keyShapeOK(p, k);
      if (bad) { show($('keyerr'), bad); return; }
      show($('keyerr'), '');
      /* Shape only. The key itself never leaves this tab. */
      startSession(p, p + ':' + k.slice(0, 7) + ':' + k.length, false);
    });

    $('keyin').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') $('keygo').click();
    });

    $('demo').addEventListener('click', function () {
      startSession('demo', 'demo', true);
    });

    $('signout').addEventListener('click', function () {
      localStorage.removeItem('rf.session');
      if (app.poll) { clearInterval(app.poll); app.poll = null; }
      app.session = null; app.job = null; app.notes = []; app.file = null;
      $('sessid').textContent = '';
      $('meta').hidden = true;
      show($('autherr'), '');
      goto(0);
    });
  }

  /* ---------------------------------------------------------------- UPLOAD */

  function takeFile(f) {
    if (!f) return;
    if (f.type && f.type.indexOf('video/') !== 0) {
      show($('uperr'), 'That is a ' + (f.type || 'unknown') + ' file. Reel Factory needs a video.');
      return;
    }
    show($('uperr'), '');
    app.file = f;
    $('m-name').textContent = f.name;
    $('m-size').textContent = (f.size / 1048576).toFixed(1) + ' MB';
    $('m-type').textContent = f.type || 'video';
    $('m-dur').textContent = 'reading...';
    $('meta').hidden = false;

    var probe = $('probe');
    var url = URL.createObjectURL(f);
    probe.onloadedmetadata = function () {
      app.duration = probe.duration || 0;
      $('m-dur').textContent = isFinite(app.duration) ? tcode(app.duration) : 'unknown';
      URL.revokeObjectURL(url);
    };
    probe.onerror = function () {
      $('m-dur').textContent = 'unreadable';
      URL.revokeObjectURL(url);
    };
    probe.src = url;
  }

  function bindUpload() {
    var drop = $('drop'), input = $('file');
    drop.addEventListener('click', function () { input.click(); });
    drop.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
    });
    input.addEventListener('change', function () { takeFile(input.files[0]); });

    ['dragenter', 'dragover'].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('hot'); });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('hot'); });
    });
    drop.addEventListener('drop', function (e) {
      var dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length) takeFile(dt.files[0]);
    });

    $('go').addEventListener('click', startJob);
  }

  function bindPipe() {
    $('fallgo').addEventListener('click', useSample);
  }

  /* -------------------------------------------------------------- PIPELINE */

  var FALLBACK_STAGES = [
    { key: 'probe', label: 'Probing the master (codec, bitrate, chroma)', ms: 2200 },
    { key: 'transcribe', label: 'Transcribing with word timestamps', ms: 6500 },
    { key: 'beats', label: 'Deriving beats from the RMS envelope', ms: 3800 },
    { key: 'face', label: 'Solving face geometry, crown to chin', ms: 5200 },
    { key: 'script', label: 'Cutting gaps and building the caption track', ms: 4200 },
    { key: 'compose', label: 'Composing the HyperFrames timeline', ms: 6000 },
    { key: 'gate', label: 'Running the Instagram safe zone gate', ms: 3200 },
    { key: 'render', label: 'Rendering 2160x3840 at 30fps', ms: 7000 },
    { key: 'bitrate', label: 'Verifying delivery bitrate against the master', ms: 2200 }
  ];

  /* Client-side ceiling. A stuck server must never hang the demo. */
  var POLL_CEILING_MS = 60000;
  var SAMPLE_URL = '/api/artefact';

  function setMode(mode) {
    var real = mode === 'real';
    var txt = real
      ? 'Real edit: this ran on the file you uploaded.'
      : 'Sample reel: a bundled cut, not your upload.';
    ['modetag', 'revmode', 'donemode'].forEach(function (id) {
      var n = $(id);
      if (!n) return;
      n.textContent = txt;
      n.hidden = false;
    });
    app.mode = mode || 'demo';
  }

  function stageKeys(stages) {
    return stages.map(function (s) { return s.key || s.label || ''; }).join('|');
  }

  /* Server-driven. Per stage `state` wins when the server sends one; otherwise we
     fall back to the running index, which is what the local simulation gives us. */
  function paintStages(stages, index, jobState) {
    stages = stages || [];
    var ol = $('stages');
    if (ol.getAttribute('data-keys') !== stageKeys(stages)) {
      ol.innerHTML = '';
      stages.forEach(function (s) {
        var li = document.createElement('li');
        li.className = 'stg';
        li.innerHTML = '<span class="dot"></span><span class="lab">' +
          '<span class="labt"></span><span class="nte" hidden></span></span><span class="t"></span>';
        li.querySelector('.labt').textContent = s.label || s.key || '';
        ol.appendChild(li);
      });
      ol.setAttribute('data-keys', stageKeys(stages));
    }

    var finished = jobState === 'done';
    var settled = 0;
    Array.prototype.forEach.call(ol.children, function (li, i) {
      var s = stages[i] || {};
      var st = s.state;
      if (!st) st = finished || i < index ? 'done' : (i === index ? 'running' : 'pending');
      if (finished && (st === 'pending' || st === 'running')) st = 'done';

      var cls = 'stg';
      if (st === 'done') cls += ' done';
      else if (st === 'running') cls += ' run';
      else if (st === 'failed') cls += ' fail';
      else if (st === 'skipped') cls += ' skip';
      li.className = cls;

      var t = li.querySelector('.t');
      if (st === 'done') t.textContent = s.ms ? (s.ms / 1000).toFixed(1) + 's' : 'done';
      else if (st === 'running') t.textContent = 'running';
      else if (st === 'failed') t.textContent = 'failed';
      else if (st === 'skipped') t.textContent = 'skipped';
      else t.textContent = 'queued';

      /* The note carries the measured detail. It is the proof the edit is real. */
      var nte = li.querySelector('.nte');
      var note = s.note || s.detail || '';
      if (note) { nte.textContent = note; nte.hidden = false; }
      else { nte.textContent = ''; nte.hidden = true; }

      if (st === 'done' || st === 'skipped' || st === 'failed') settled++;
    });

    var total = stages.length || 1;
    $('barfill').style.width = (finished ? 100 : Math.round((settled / total) * 100)) + '%';
  }

  function showFallback(on) {
    var row = $('fallrow');
    if (row) row.hidden = !on;
  }

  function stopPoll() {
    if (app.poll) { clearInterval(app.poll); app.poll = null; }
  }

  /* Real bytes, real progress. XHR because fetch cannot report upload progress. */
  function uploadSource(jobId, file) {
    return new Promise(function (resolve, reject) {
      var x = new XMLHttpRequest();
      x.open('POST', '/api/jobs/' + encodeURIComponent(jobId) + '/source', true);
      /* Headers must be ASCII, so an accented filename cannot throw here. */
      x.setRequestHeader('x-filename', String(file.name || 'upload.mp4').replace(/[^\x20-\x7e]/g, '_'));
      x.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
      $('uprow').hidden = false;
      $('upfill').style.width = '0%';
      $('uplab').textContent = 'Uploading ' + (file.size / 1048576).toFixed(1) + ' MB';
      if (x.upload) {
        x.upload.onprogress = function (e) {
          if (!e.lengthComputable) { $('upfill').style.width = '100%'; return; }
          var pct = Math.round((e.loaded / e.total) * 100);
          $('upfill').style.width = pct + '%';
          $('uplab').textContent = 'Uploading your file, ' + pct + '%';
        };
      }
      x.onload = function () {
        if (x.status >= 200 && x.status < 300) {
          $('upfill').style.width = '100%';
          $('uplab').textContent = 'Upload complete, ' + (file.size / 1048576).toFixed(1) + ' MB sent';
          var d = null;
          try { d = JSON.parse(x.responseText); } catch (e) { d = null; }
          resolve(d || { ok: true });
        } else {
          reject(new Error('upload returned ' + x.status));
        }
      };
      x.onerror = function () { reject(new Error('upload connection failed')); };
      x.onabort = function () { reject(new Error('upload aborted')); };
      x.send(file);
    });
  }

  function startJob() {
    if (!app.file) { show($('uperr'), 'Pick a video first.'); return; }
    show($('piperr'), '');
    showFallback(false);
    goto(2);
    $('stages').innerHTML = '';
    $('stages').removeAttribute('data-keys');
    $('barfill').style.width = '0%';
    $('uprow').hidden = true;
    app.started = Date.now();

    if (app.offline) { setMode('demo'); simulate(FALLBACK_STAGES); return; }

    api('POST', '/api/jobs', { filename: app.file.name, sizeBytes: app.file.size })
      .then(function (j) {
        app.job = j;
        setMode(j.mode || 'demo');
        var stages = j.stages && j.stages.length ? j.stages : FALLBACK_STAGES;
        $('pipesub').textContent = stages.length + ' passes on your file. Roughly fifteen to sixty seconds.';
        paintStages(stages, 0, 'running');

        return uploadSource(j.id, app.file).then(function () {
          pollJob();
        }, function (e) {
          /* In demo mode the server may not want the bytes at all: keep going. */
          if ((j.mode || 'demo') === 'demo') { $('uprow').hidden = true; pollJob(); return; }
          failJob('The upload failed (' + e.message + ').');
        });
      })
      .catch(function (e) {
        show($('piperr'), 'Could not reach the job service (' + e.message + '). Running the pipeline locally instead.');
        app.offline = true;
        setMode('demo');
        simulate(FALLBACK_STAGES);
      });
  }

  function failJob(msg) {
    stopPoll();
    show($('piperr'), msg + ' Nothing is lost, you can carry on with the bundled sample.');
    showFallback(true);
  }

  function pollJob() {
    var fails = 0;
    var t0 = Date.now();
    stopPoll();
    app.poll = setInterval(function () {
      if (Date.now() - t0 > POLL_CEILING_MS) {
        failJob('The job has been running for over 60 seconds without finishing.');
        return;
      }
      api('GET', '/api/jobs/' + encodeURIComponent(app.job.id))
        .then(function (j) {
          fails = 0;
          if (!$('fallrow').hidden) return;
          show($('piperr'), '');
          if (j.mode && j.mode !== app.mode) setMode(j.mode);
          var stages = j.stages && j.stages.length ? j.stages : (app.job.stages || FALLBACK_STAGES);
          app.job.stages = stages;
          paintStages(stages, j.stageIndex || 0, j.state);

          if (j.state === 'failed') {
            failJob(j.error || 'The edit failed on the server.');
            return;
          }
          if (j.state === 'done') {
            stopPoll();
            app.job.videoUrl = j.videoUrl || app.job.videoUrl || null;
            app.job.poster = j.poster;
            if (j.notes && j.notes.length) app.notes = j.notes;
            openReview();
          }
        })
        .catch(function (e) {
          fails++;
          show($('piperr'), 'Lost the job service, retrying (' + fails + '/6). ' + e.message);
          if (fails >= 6) failJob('The job service did not come back.');
        });
    }, 700);
  }

  /* The demo must never dead-end: fall back to the bundled sample reel. */
  function useSample() {
    stopPoll();
    showFallback(false);
    show($('piperr'), '');
    app.offline = true;
    app.notes = [];
    app.job = { id: (app.job && app.job.id) || 'local-' + Date.now().toString(36), videoUrl: SAMPLE_URL };
    setMode('demo');
    $('uprow').hidden = true;
    $('stages').innerHTML = '';
    $('stages').removeAttribute('data-keys');
    $('pipesub').textContent = 'Running the bundled sample through the same review flow.';
    /* Quick: the viewer already waited once. */
    simulate(FALLBACK_STAGES.map(function (s) {
      return { key: s.key, label: s.label, ms: Math.round(s.ms / 8) };
    }));
  }

  function simulate(stages) {
    var i = 0, t0 = Date.now();
    paintStages(stages, 0, 'running');
    if (app.poll) clearInterval(app.poll);
    app.poll = setInterval(function () {
      var el = Date.now() - t0, acc = 0, idx = stages.length;
      for (var k = 0; k < stages.length; k++) {
        acc += stages[k].ms;
        if (el < acc) { idx = k; break; }
      }
      if (idx !== i) { i = idx; }
      if (idx >= stages.length) {
        clearInterval(app.poll); app.poll = null;
        paintStages(stages, stages.length, 'done');
        app.job = app.job || { id: 'local-' + Date.now().toString(36) };
        if (!app.job.videoUrl) app.job.videoUrl = URL.createObjectURL(app.file);
        openReview();
      } else {
        paintStages(stages, idx, 'running');
      }
    }, 250);
  }

  /* ---------------------------------------------------------------- REVIEW */

  var vid, cv, ctx, drawing = null;

  function openReview() {
    goto(3);
    vid = $('vid');
    app.triedLocalSrc = false;
    /* The server names the file, always. Never hardcode an artefact path here. */
    var src = (app.job && app.job.videoUrl) || '';
    if (!src && app.file) src = URL.createObjectURL(app.file);
    if (!src) {
      show($('viderr'), 'The job finished without a video URL. Nothing to review.');
      return;
    }
    show($('viderr'), '');
    if (vid.getAttribute('src') !== src) vid.setAttribute('src', src);
    if (app.job && app.job.poster) vid.setAttribute('poster', app.job.poster);
    vid.load();
    loadNotes();
  }

  function sizeCanvas() {
    if (!cv || !vid) return;
    var r = vid.getBoundingClientRect();
    if (!r.width || !r.height) return;
    var dpr = window.devicePixelRatio || 1;
    cv.width = Math.round(r.width * dpr);
    cv.height = Math.round(r.height * dpr);
    cv.style.width = r.width + 'px';
    cv.style.height = r.height + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    redraw();
  }

  function cssSize() {
    var r = vid.getBoundingClientRect();
    return { w: r.width || 1, h: r.height || 1 };
  }

  function redraw() {
    if (!ctx) return;
    var s = cssSize();
    ctx.clearRect(0, 0, s.w, s.h);
    var box = null;
    if (drawing) box = drawing;
    else if (app.activeNote) {
      var n = findNote(app.activeNote);
      if (n) box = { x: n.rect.x * s.w, y: n.rect.y * s.h, w: n.rect.w * s.w, h: n.rect.h * s.h };
    }
    if (!box) return;
    ctx.strokeStyle = '#e40014';
    ctx.lineWidth = 3;
    ctx.strokeRect(box.x, box.y, box.w, box.h);
    ctx.fillStyle = 'rgba(228,0,20,.14)';
    ctx.fillRect(box.x, box.y, box.w, box.h);
  }

  function findNote(id) {
    for (var i = 0; i < app.notes.length; i++) if (app.notes[i].id === id) return app.notes[i];
    return null;
  }

  function pointer(e) {
    var r = cv.getBoundingClientRect();
    return { x: Math.min(Math.max(e.clientX - r.left, 0), r.width),
             y: Math.min(Math.max(e.clientY - r.top, 0), r.height) };
  }

  function bindReview() {
    cv = $('cv');
    ctx = cv.getContext('2d');
    vid = $('vid');

    vid.addEventListener('loadedmetadata', function () {
      sizeCanvas();
      $('seek').max = 1000;
      updTime();
    });
    vid.addEventListener('timeupdate', updTime);
    vid.addEventListener('play', function () { $('play').textContent = 'Pause'; });
    vid.addEventListener('pause', function () { $('play').textContent = 'Play'; });
    vid.addEventListener('error', function () {
      /* One recovery step, then say so plainly rather than show a black rectangle. */
      if (!app.triedLocalSrc && app.file) {
        app.triedLocalSrc = true;
        show($('viderr'), 'The rendered file would not load, showing your original upload instead.');
        vid.setAttribute('src', URL.createObjectURL(app.file));
        vid.load();
        return;
      }
      show($('viderr'), 'The rendered file would not load from ' + (vid.currentSrc || 'the job URL') + '. The notes tools still work.');
    });
    window.addEventListener('resize', sizeCanvas);

    $('play').addEventListener('click', function () {
      if (vid.paused) { var p = vid.play(); if (p && p.catch) p.catch(function () {}); }
      else vid.pause();
    });
    $('prev').addEventListener('click', function () { vid.pause(); vid.currentTime = Math.max(0, vid.currentTime - 1 / FPS); });
    $('next').addEventListener('click', function () {
      vid.pause();
      var d = isFinite(vid.duration) ? vid.duration : 1e9;
      vid.currentTime = Math.min(d, vid.currentTime + 1 / FPS);
    });
    $('seek').addEventListener('input', function () {
      if (!isFinite(vid.duration) || !vid.duration) return;
      vid.currentTime = (this.value / 1000) * vid.duration;
    });

    /* drag a box */
    cv.addEventListener('pointerdown', function (e) {
      vid.pause();
      cv.setPointerCapture(e.pointerId);
      var p = pointer(e);
      drawing = { x0: p.x, y0: p.y, x: p.x, y: p.y, w: 0, h: 0 };
      app.activeNote = null;
      redraw();
    });
    cv.addEventListener('pointermove', function (e) {
      if (!drawing) return;
      var p = pointer(e);
      drawing.x = Math.min(drawing.x0, p.x);
      drawing.y = Math.min(drawing.y0, p.y);
      drawing.w = Math.abs(p.x - drawing.x0);
      drawing.h = Math.abs(p.y - drawing.y0);
      redraw();
    });
    cv.addEventListener('pointerup', function () {
      if (!drawing) return;
      if (drawing.w < 8 || drawing.h < 8) { drawing = null; redraw(); return; }
      openComposer();
    });
    cv.addEventListener('pointercancel', function () { drawing = null; redraw(); });

    $('csave').addEventListener('click', saveNote);
    $('ccancel').addEventListener('click', function () {
      drawing = null; $('composer').hidden = true; redraw();
    });
    $('send').addEventListener('click', finish);
  }

  function updTime() {
    $('tc').textContent = tcode(vid.currentTime);
    if (isFinite(vid.duration) && vid.duration) {
      $('seek').value = Math.round((vid.currentTime / vid.duration) * 1000);
    }
  }

  function openComposer() {
    $('composer').hidden = false;
    $('ctime').textContent = tcode(vid.currentTime);
    $('ctext').value = '';
    $('ctext').focus();
    show($('noteerr'), '');
  }

  function saveNote() {
    var text = $('ctext').value.trim();
    if (!text) { show($('noteerr'), 'Write the note before saving it.'); return; }
    if (!drawing) { show($('noteerr'), 'The box was lost. Drag a new one.'); return; }
    var s = cssSize();
    var rect = {
      x: +(drawing.x / s.w).toFixed(4),
      y: +(drawing.y / s.h).toFixed(4),
      w: +(drawing.w / s.w).toFixed(4),
      h: +(drawing.h / s.h).toFixed(4)
    };
    var body = { t: +vid.currentTime.toFixed(3), rect: rect, text: text };
    var jid = app.job && app.job.id;

    var local = function () {
      var n = { id: 'n' + Date.now().toString(36), t: body.t, rect: rect, text: text, createdAt: Date.now() };
      app.notes.push(n);
      app.activeNote = n.id;
      drawing = null;
      $('composer').hidden = true;
      renderNotes();
      redraw();
    };

    if (app.offline || !jid) { local(); return; }

    api('POST', '/api/jobs/' + encodeURIComponent(jid) + '/notes', body)
      .then(function (d) {
        var n = (d && d.note) || null;
        if (!n) { local(); return; }
        app.notes.push(n);
        app.activeNote = n.id;
        drawing = null;
        $('composer').hidden = true;
        show($('noteerr'), '');
        renderNotes();
        redraw();
      })
      .catch(function (e) {
        show($('noteerr'), 'Could not save to the server (' + e.message + '). Keeping the note locally.');
        local();
      });
  }

  function loadNotes() {
    var jid = app.job && app.job.id;
    if (app.offline || !jid) { renderNotes(); return; }
    api('GET', '/api/jobs/' + encodeURIComponent(jid) + '/notes')
      .then(function (d) { app.notes = (d && d.notes) || []; renderNotes(); })
      .catch(function () { renderNotes(); });
  }

  function delNote(id) {
    var jid = app.job && app.job.id;
    var drop = function () {
      app.notes = app.notes.filter(function (n) { return n.id !== id; });
      if (app.activeNote === id) app.activeNote = null;
      renderNotes(); redraw();
    };
    if (app.offline || !jid) { drop(); return; }
    api('DELETE', '/api/jobs/' + encodeURIComponent(jid) + '/notes/' + encodeURIComponent(id))
      .then(drop)
      .catch(function (e) {
        show($('noteerr'), 'Server refused the delete (' + e.message + '). Removed it from this view.');
        drop();
      });
  }

  function renderNotes() {
    var ul = $('notelist');
    ul.innerHTML = '';
    app.notes.sort(function (a, b) { return a.t - b.t; });
    app.notes.forEach(function (n) {
      var li = document.createElement('li');
      li.className = 'note' + (app.activeNote === n.id ? ' on' : '');
      var row = document.createElement('div');
      row.className = 'noterow';
      var k = document.createElement('span');
      k.className = 'kicker';
      k.textContent = tcode(n.t);
      var d = document.createElement('button');
      d.className = 'del';
      d.type = 'button';
      d.textContent = 'Delete';
      d.addEventListener('click', function (e) { e.stopPropagation(); delNote(n.id); });
      row.appendChild(k); row.appendChild(d);
      var p = document.createElement('p');
      p.className = 'notetext';
      p.textContent = n.text;
      li.appendChild(row); li.appendChild(p);
      li.addEventListener('click', function () {
        app.activeNote = n.id;
        if (vid) { vid.pause(); if (isFinite(vid.duration)) vid.currentTime = n.t; }
        renderNotes(); redraw();
      });
      ul.appendChild(li);
    });
    $('ncount').textContent = app.notes.length;
    $('noteempty').hidden = app.notes.length > 0;
  }

  /* ------------------------------------------------------------------ DONE */

  var TIERS = [
    { nm: 'Solo', pr: '$0', d: 'One reel a month, watermarked, 1080p.' },
    { nm: 'Studio', pr: '$49 / mo', d: 'Twelve reels, 4K delivery, safe zone gate, review links.', best: true },
    { nm: 'Agency', pr: '$199 / mo', d: 'Unlimited reels, client review portal, brand kits, priority render.' }
  ];

  function finish() {
    goto(4);
    var src = (app.job && app.job.videoUrl) || (vid && vid.currentSrc) || '';
    var d = $('dvid');
    if (src) {
      d.src = src;
      $('dl').href = src;
      $('dl').setAttribute('download', 'reel-factory-cut.mp4');
    } else {
      $('dl').removeAttribute('href');
      $('dl').setAttribute('aria-disabled', 'true');
    }
    var ul = $('tiers');
    if (!ul.childElementCount) {
      TIERS.forEach(function (t) {
        var li = document.createElement('li');
        li.className = 'tier' + (t.best ? ' best' : '');
        var h = document.createElement('div');
        h.className = 'tierhead';
        var nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = t.nm;
        var pr = document.createElement('span'); pr.className = 'pr'; pr.textContent = t.pr;
        h.appendChild(nm); h.appendChild(pr);
        var p = document.createElement('p'); p.className = 'fineprint'; p.textContent = t.d;
        var b = document.createElement('button');
        b.className = 'btn btn--ghost btn--sm';
        b.type = 'button';
        b.disabled = true;
        b.textContent = 'Mocked for the prototype';
        li.appendChild(h); li.appendChild(p); li.appendChild(b);
        ul.appendChild(li);
      });
    }
  }

  function bindDone() {
    $('again').addEventListener('click', function () {
      app.job = null; app.notes = []; app.file = null; app.activeNote = null;
      $('meta').hidden = true;
      $('file').value = '';
      goto(1);
    });
  }

  /* ------------------------------------------------------------------ boot */

  function boot() {
    document.documentElement.classList.add('js');
    bindAuth(); bindUpload(); bindPipe(); bindReview(); bindDone();
    var s = localStorage.getItem('rf.session');
    if (s) {
      app.session = s;
      app.provider = localStorage.getItem('rf.provider') || 'anthropic';
      $('sessid').textContent = 'session ' + s;
      goto(1);
    } else {
      goto(0);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.addEventListener('unhandledrejection', function (e) {
    e.preventDefault();
    var t = document.querySelector('.state:not([hidden]) .err');
    if (t) show(t, 'Something failed in the background: ' + (e.reason && e.reason.message ? e.reason.message : e.reason));
  });
})();
