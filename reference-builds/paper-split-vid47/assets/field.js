/* ============================================================================
   vid47 — THE STACK
   One recurring 3D object for the whole reel. It is the same 700 plates every
   time; only their arrangement, their state colour and their flip change:

     HOOK-B   wall     a 25x28 slab of RED plates = the paid stack, and a wave
                       sweeps across it flipping half of them to GREEN on the
                       word "half"
     03 Maxun rows     the plates leave the page and land as table rows
     06 Langflow graph six node clusters with plates strung along the edges
     09 Crawl4AI lattice a chaotic cloud collapses into an ordered lattice
     CTA      converge everything falls to the centre and burns out

   Recurrence is what makes a 3D object read as designed rather than decorative
   (vid42/vid46). Three non-negotiables, all inherited:

   1. UMD three, loaded locally by a <script src>. No ES modules — the lint rule
      `missing_three_script` scans for a script tag and never sees an import.
   2. Every pixel is a pure function of the proxy P, which ONLY the timeline
      mutates; paint() is called from gsap.timeline({onUpdate}) and nowhere
      else. No rAF, no Date.now, seeded PRNG only. Renders are bit-identical.
   3. Size is COMPUTED from the camera, never eyeballed — see PPU below.
   ============================================================================ */
(function (global) {
  "use strict";

  /* deterministic PRNG — the same field every seek, every worker, every run */
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  var COUNT = 300;                 /* 15 x 20 wall, 25 x 12 rows, 6x30+5x24 graph */

  global.createField = function (opts) {
    var canvas = opts.canvas;
    var W = opts.width || 1080, H = opts.height || 1920;
    var FOV = 40, CAMZ = 9;

    var renderer = new THREE.WebGLRenderer({
      canvas: canvas, antialias: true, alpha: true,
      preserveDrawingBuffer: true            /* the capture screenshots the page */
    });
    renderer.setPixelRatio(1);
    renderer.setSize(W, H, false);
    renderer.setClearAlpha(0);

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(FOV, W / H, 0.1, 400);
    camera.position.set(0, 0, CAMZ);

    /* --- THE SCALE ARITHMETIC. At fov 40 / z 9 the visible height at z=0 is
       2*9*tan(20deg) = 6.5517 world units across H px. Every dimension below is
       written in PIXELS and converted, so nothing in this file is guessed. --- */
    var VIS_H = 2 * CAMZ * Math.tan((FOV / 2) * Math.PI / 180);
    var PPU = H / VIS_H;                      /* ~293.1 px per world unit */
    function u(px) { return px / PPU; }

    scene.add(new THREE.AmbientLight(0xffffff, 2.35));
    var key = new THREE.DirectionalLight(0xfff6e8, 1.9); key.position.set(3, 7, 9);
    scene.add(key);
    var rim = new THREE.DirectionalLight(0xbfe8d6, 1.1); rim.position.set(-7, -3, 5);
    scene.add(rim);

    /* --- the plate. Body is dark brushed metal; the state colour lives on a thin
       LED strip child, never on the body — emissive on a whole box reads as a flat
       coloured slab (vid43's server racks). On a near-black ground the DIM end of
       every ramp has to be lifted or the field reads as a grid of dashes rather
       than hardware; that has now bitten on vid42, vid46 and this build. --- */
    var PW = u(44), PH = u(34), PD = u(9);

    var bodyGeo = new THREE.BoxGeometry(PW, PH, PD);
    var bodyMat = new THREE.MeshStandardMaterial({
      color: 0xE6E2D8, metalness: 0.04, roughness: 0.72,
      transparent: true, opacity: 1
    });
    var body = new THREE.InstancedMesh(bodyGeo, bodyMat, COUNT);
    body.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    var ledMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 1 });
    function strip(z) {
      var g = new THREE.BoxGeometry(PW * 0.86, PH * 0.40, PD * 0.72);
      g.translate(0, -PH * 0.18, z);
      var m = new THREE.InstancedMesh(g, ledMat, COUNT);
      m.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      m.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(COUNT * 3), 3);
      return m;
    }
    var led = strip(PD * 0.62), ledB = strip(-PD * 0.62);

    var group = new THREE.Group();
    scene.add(group);
    group.add(body); group.add(led); group.add(ledB);

    /* ---------------- layouts: every target position/orientation precomputed
       once at init, so paint() is a lerp and nothing allocates per frame ------ */
    var rnd = mulberry32(4710730);
    var jitter = [], phase = [], spinAx = [];
    for (var i = 0; i < COUNT; i++) {
      jitter.push([rnd() - 0.5, rnd() - 0.5, rnd() - 0.5]);
      phase.push(rnd());
      spinAx.push([rnd() - 0.5, rnd() - 0.5, rnd() - 0.5]);
    }

    var L = {};
    function blank() {
      var a = { p: new Float32Array(COUNT * 3), q: new Float32Array(COUNT * 4),
                s: new Float32Array(COUNT), sx: new Float32Array(COUNT),
                xn: new Float32Array(COUNT) };
      for (var i = 0; i < COUNT; i++) { a.q[i * 4 + 3] = 1; a.s[i] = 1; a.sx[i] = 1; }
      return a;
    }
    var _q = new THREE.Quaternion(), _e = new THREE.Euler(),
        _q2 = new THREE.Quaternion(), _ey = new THREE.Euler(),
        _m = new THREE.Matrix4(), _c = new THREE.Color(),
        _pos = new THREE.Vector3(), _qq = new THREE.Quaternion(),
        _sc = new THREE.Vector3();

    function setQ(a, i, qx, qy, qz, qw) {
      a.q[i * 4] = qx; a.q[i * 4 + 1] = qy; a.q[i * 4 + 2] = qz; a.q[i * 4 + 3] = qw;
    }
    function eul(a, i, rx, ry, rz) {
      _e.set(rx, ry, rz); _q.setFromEuler(_e);
      setQ(a, i, _q.x, _q.y, _q.z, _q.w);
    }

    /* SCATTER — the entry state: a loose cloud, deep, tumbling */
    L.scatter = (function () {
      var a = blank();
      for (var i = 0; i < COUNT; i++) {
        a.p[i * 3]     = jitter[i][0] * u(2600);
        a.p[i * 3 + 1] = jitter[i][1] * u(3000);
        a.p[i * 3 + 2] = jitter[i][2] * u(2400) - u(700);
        a.xn[i] = 0.5 + jitter[i][0];
        eul(a, i, jitter[i][1] * 3.1, jitter[i][0] * 3.1, jitter[i][2] * 3.1);
      }
      return a;
    })();

    /* WALL — 25 x 28 = 700 exactly, occupying 960 x 1230 px. The hook's stack.
       `xn` is the normalised column, which is what the flip wave sweeps along. */
    var WCOLS = 14, WROWS = 11, WN = 154;
    L.wall = (function () {
      var a = blank();
      var pxW = u(900), pxH = u(640);
      var gx = pxW / WCOLS, gy = pxH / WROWS;
      for (var i = 0; i < COUNT; i++) {
        if (i >= WN) { a.s[i] = 0; a.xn[i] = 1.4; continue; }
        a.sx[i] = 1.35;
        var c = i % WCOLS, r = (i / WCOLS) | 0;
        a.p[i * 3]     = (c - (WCOLS - 1) / 2) * gx;
        a.p[i * 3 + 1] = ((WROWS - 1) / 2 - r) * gy;
        a.p[i * 3 + 2] = jitter[i][2] * u(40);
        a.xn[i] = c / (WCOLS - 1);
        eul(a, i, jitter[i][1] * 0.05, jitter[i][0] * 0.06, jitter[i][2] * 0.03);
      }
      return a;
    })();

    /* ROWS — Maxun. 12 table rows of 26 plates inside an 820 x 600 px band; the
       remaining 388 park off the right edge at scale 0 so they can stream IN. */
    L.rows = (function () {
      var a = blank(), RC = 12, RR = 8, N = RC * RR;
      var pxW = u(700), pxH = u(430);
      var gx = pxW / RC, gy = pxH / RR;
      for (var i = 0; i < COUNT; i++) {
        if (i >= N) {
          a.s[i] = 0;
          a.p[i * 3] = u(1000); a.p[i * 3 + 1] = jitter[i][1] * u(600);
          a.xn[i] = 1; continue;
        }
        var c = i % RC, r = (i / RC) | 0;
        a.p[i * 3]     = (c - (RC - 1) / 2) * gx;
        a.p[i * 3 + 1] = ((RR - 1) / 2 - r) * gy;
        a.p[i * 3 + 2] = 0;
        a.xn[i] = c / (RC - 1);
        a.s[i] = 1; a.sx[i] = 1.28;
        eul(a, i, 0, 0, 0);
      }
      return a;
    })();

    /* PAGE — Maxun's "before": the same plates packed as a dense unstructured
       block, i.e. a web page. rows is what it becomes. */
    L.page = (function () {
      var a = blank(), RC = 12, RR = 8, N = RC * RR;
      for (var i = 0; i < COUNT; i++) {
        if (i >= N) { a.s[i] = 0; a.p[i * 3] = u(1000); a.xn[i] = 1; continue; }
        var c = i % RC, r = (i / RC) | 0;
        a.p[i * 3]     = (c - (RC - 1) / 2) * u(700 / RC) + jitter[i][0] * u(58);
        a.p[i * 3 + 1] = ((RR - 1) / 2 - r) * u(430 / RR) + jitter[i][1] * u(46);
        a.p[i * 3 + 2] = jitter[i][2] * u(120);
        a.xn[i] = c / (RC - 1);
        eul(a, i, jitter[i][1] * 0.9, jitter[i][0] * 1.2, jitter[i][2] * 0.9);
      }
      return a;
    })();

    /* GRAPH — Langflow. Six node clusters (60 plates each = 360) plus five edges
       carrying 68 plates apiece (340). One object, and it reads as a wired graph
       because the edge plates literally lie on the segment between two nodes. */
    L.graph = (function () {
      var a = blank();
      var nodes = [
        [-270,  330], [ 270,  330],
        [-270,    0], [ 270,    0],
        [-270, -330], [ 270, -330]
      ];
      var edges = [[0, 2], [2, 4], [0, 3], [3, 5], [2, 3]];
      var PER = 30, EPER = 24, NC = 6, NR = 5, NGX = 30, NGY = 26;
      var i = 0, n, k, e;
      for (n = 0; n < nodes.length; n++) {
        for (k = 0; k < PER; k++, i++) {
          var c = k % NC, r = (k / NC) | 0;
          a.p[i * 3]     = u(nodes[n][0] + (c - (NC - 1) / 2) * NGX);
          a.p[i * 3 + 1] = u(nodes[n][1] + ((NR - 1) / 2 - r) * NGY);
          a.p[i * 3 + 2] = 0;
          a.xn[i] = (nodes[n][0] + 340) / 680;
          a.s[i] = 0.60;
          eul(a, i, 0, 0, 0);
        }
      }
      for (e = 0; e < edges.length; e++) {
        var A0 = nodes[edges[e][0]], B0 = nodes[edges[e][1]];
        for (k = 0; k < EPER && i < COUNT; k++, i++) {
          var f = k / (EPER - 1);
          a.p[i * 3]     = u(A0[0] + (B0[0] - A0[0]) * f);
          a.p[i * 3 + 1] = u(A0[1] + (B0[1] - A0[1]) * f);
          a.p[i * 3 + 2] = 0;
          a.xn[i] = f;
          a.s[i] = (k % 3 === 0) ? 0.42 : 0;
          eul(a, i, 0, 0, Math.atan2(B0[1] - A0[1], B0[0] - A0[0]));
        }
      }
      for (; i < COUNT; i++) { a.s[i] = 0; }
      return a;
    })();

    /* SOUP — Crawl4AI's "before": raw HTML, a turbulent cloud with no order. */
    L.soup = (function () {
      var a = blank();
      for (var i = 0; i < COUNT; i++) {
        a.p[i * 3]     = jitter[i][0] * u(800);
        a.p[i * 3 + 1] = jitter[i][1] * u(920);
        a.p[i * 3 + 2] = jitter[i][2] * u(620);
        a.xn[i] = 0.5 + jitter[i][0];
        a.s[i] = 0.9 + phase[i] * 0.5;
        eul(a, i, jitter[i][1] * 2.6, jitter[i][0] * 2.6, jitter[i][2] * 2.6);
      }
      return a;
    })();

    /* LATTICE — Crawl4AI's "after": clean, ordered, flat. 20 x 35 in 700 x 900. */
    L.lattice = (function () {
      var a = blank(), C2 = 20, R2 = 15;
      var gx = u(740) / C2, gy = u(540) / R2;
      for (var i = 0; i < COUNT; i++) {
        var c = i % C2, r = (i / C2) | 0;
        a.p[i * 3]     = (c - (C2 - 1) / 2) * gx;
        a.p[i * 3 + 1] = ((R2 - 1) / 2 - r) * gy;
        a.p[i * 3 + 2] = 0;
        a.xn[i] = c / (C2 - 1);
        a.s[i] = 0.94; a.sx[i] = 1.10;
        eul(a, i, 0, 0, 0);
      }
      return a;
    })();

    /* CONVERGE — everything falls into the centre and shrinks out */
    L.converge = (function () {
      var a = blank();
      for (var i = 0; i < COUNT; i++) {
        var t = phase[i] * Math.PI * 2;
        a.p[i * 3]     = Math.cos(t) * u(34) * jitter[i][0];
        a.p[i * 3 + 1] = Math.sin(t) * u(34) * jitter[i][1];
        a.p[i * 3 + 2] = jitter[i][2] * u(34);
        a.xn[i] = 0.5;
        a.s[i] = 0.001;
        eul(a, i, 0, 0, t);
      }
      return a;
    })();

    /* BURST — the CTA's exhale: outward along each plate's own bearing */
    L.burst = (function () {
      var a = blank();
      for (var i = 0; i < COUNT; i++) {
        var t = phase[i] * Math.PI * 2;
        var rr = 500 + phase[i] * 900;
        a.p[i * 3]     = Math.cos(t) * u(rr) * 0.8;
        a.p[i * 3 + 1] = Math.sin(t) * u(rr);
        a.p[i * 3 + 2] = jitter[i][2] * u(500);
        a.xn[i] = 0.5;
        a.s[i] = 0.7;
        eul(a, i, jitter[i][1] * 2, jitter[i][0] * 2, t);
      }
      return a;
    })();

    /* ---------------- colour rules ----------------
       Every one of these is lifted off the near-black ground on purpose. The
       "off" grey is #2E2E38 and not #14141A for exactly that reason. */
    var C = {
      off:   new THREE.Color(0xC9C4B8),   /* unlit tile, warm grey on warm paper  */
      paid:  new THREE.Color(0xE5372B),   /* the subscription you already pay for */
      free:  new THREE.Color(0x0B7A57),   /* the GO semantic, deep enough to read */
      raw:   new THREE.Color(0x8A8A93),
      go:    new THREE.Color(0x0B7A57),
      terra: new THREE.Color(0xDA7756)
    };

    /* The proxy. ONLY the gsap timeline writes to this. */
    var P = {
      a: "scatter", b: "scatter", k: 0,
      colour: "raw",       /* raw | paid | free | flip | wave | terra          */
      lit: 1,              /* fraction of the field that is powered            */
      sweep: 0,            /* 0..1 wave progress in x, drives flip and colour  */
      flip: 0,             /* 0..1 how much of a half-turn the wave imparts    */
      rotX: 0, rotY: 0, rotZ: 0,
      ox: 0, oy: 0,        /* group offset IN PIXELS (positive oy = up)        */
      camZ: 0,             /* dolly IN PIXELS (positive = pull back)           */
      alpha: 0,
      scale: 1
    };

    function paint() {
      var A = L[P.a] || L.scatter, B = L[P.b] || A;
      var k = P.k < 0 ? 0 : (P.k > 1 ? 1 : P.k);
      var ease = k * k * (3 - 2 * k);                 /* smoothstep, pure in k */

      var al = P.alpha < 0 ? 0 : (P.alpha > 1 ? 1 : P.alpha);
      bodyMat.opacity = al; ledMat.opacity = al;
      body.visible = led.visible = ledB.visible = al > 0.002;

      /* A layout whose MEANING depends on left/right never rotates past 0.2 rad
         (vid46 c4 swapped its two labelled spheres and argued the opposite of
         its own VO). Nothing here is authored past that; the clamp is the guard. */
      group.rotation.set(P.rotX, P.rotY, P.rotZ);
      group.position.set(u(P.ox), u(P.oy), 0);
      group.scale.setScalar(P.scale);
      camera.position.z = CAMZ + u(P.camZ);

      if (body.visible) {
        var layoutNow = P.k >= 0.5 ? P.b : P.a;
        for (var i = 0; i < COUNT; i++) {
          var s = A.s[i] + (B.s[i] - A.s[i]) * ease;
          _pos.set(
            A.p[i * 3]     + (B.p[i * 3]     - A.p[i * 3])     * ease,
            A.p[i * 3 + 1] + (B.p[i * 3 + 1] - A.p[i * 3 + 1]) * ease,
            A.p[i * 3 + 2] + (B.p[i * 3 + 2] - A.p[i * 3 + 2]) * ease);
          _qq.set(A.q[i * 4], A.q[i * 4 + 1], A.q[i * 4 + 2], A.q[i * 4 + 3]);
          _q.set(B.q[i * 4], B.q[i * 4 + 1], B.q[i * 4 + 2], B.q[i * 4 + 3]);
          _qq.slerp(_q, ease);

          /* the wave: a plate's own column decides when it is reached, so the
             flip and the colour change are the same event by construction */
          var xn = A.xn[i] + (B.xn[i] - A.xn[i]) * ease;
          var w = (P.sweep - xn) * 5.5;
          w = w < 0 ? 0 : (w > 1 ? 1 : w);
          var passed = w > 0.5;

          if (P.flip > 0.001 && w > 0) {
            _ey.set(0, w * Math.PI * P.flip, 0);
            _q2.setFromEuler(_ey);
            _qq.multiply(_q2);
          }

          var sx = A.sx[i] + (B.sx[i] - A.sx[i]) * ease;
          _sc.set(s * sx, s, s);
          _m.compose(_pos, _qq, _sc);
          body.setMatrixAt(i, _m);
          led.setMatrixAt(i, _m);
          ledB.setMatrixAt(i, _m);

          /* --- state colour. Index order IS the reveal order, so an on-screen
             counter and the field can never disagree about how many are on. --- */
          var on = i < COUNT * P.lit;
          if (!on)                          { _c.copy(C.off); }
          else if (P.colour === "flip")     { _c.copy(passed ? C.free : C.paid); }
          else if (P.colour === "wave")     { _c.copy(passed ? C.free : C.raw); }
          else if (P.colour === "paid")     { _c.copy(C.paid); }
          else if (P.colour === "free")     { _c.copy(C.free); }
          else if (P.colour === "go")       { _c.copy(C.go); }
          else if (P.colour === "terra")    { _c.copy(C.terra); }
          else                              { _c.copy(C.raw); }
          led.setColorAt(i, _c); ledB.setColorAt(i, _c);
        }
        body.instanceMatrix.needsUpdate = true;
        led.instanceMatrix.needsUpdate = true; ledB.instanceMatrix.needsUpdate = true;
        led.instanceColor.needsUpdate = true; ledB.instanceColor.needsUpdate = true;
      }

      renderer.render(scene, camera);
    }

    paint();
    return { P: P, paint: paint, PPU: PPU, u: u, COUNT: COUNT };
  };
})(window);
