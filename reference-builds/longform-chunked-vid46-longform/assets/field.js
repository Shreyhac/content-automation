/* ============================================================================
   vid46 — THE BROKER FIELD
   One recurring 3D object for the whole film. It is the same 750 plates every
   time; only their arrangement and their state colour change:

     c2  wall      750 registered broker groups build into a slab
     c3  dome420   420 of them wrap a sphere; the Deloitte ring sweeps it green
     c4  twin      420 (left, dense) against 200 (right, sparse) — same radius,
                   so the comparison is DENSITY, not two different-sized props
     c8  converge  the field collapses into the Incogni mark, all green

   The object RECURRING is what makes it read as designed rather than decorative
   (vid42 lesson). Everything here obeys the three non-negotiables:

   1. UMD three, loaded locally by a <script src> in the chunk. No modules.
   2. Every pixel is a pure function of the proxy P, which only the timeline
      mutates; paint() is called from gsap.timeline({onUpdate}) and nowhere else.
      No rAF, no Date.now, seeded PRNG only.
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

  var COUNT = 750;

  global.createField = function (opts) {
    var canvas = opts.canvas;
    var W = opts.width || 3840, H = opts.height || 2160;
    var FOV = 38, CAMZ = 12;

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

    /* --- THE SCALE ARITHMETIC. At fov 38 / z 12 the visible height at z=0 is
       2*12*tan(19deg) = 8.2639 world units across H px. Every dimension below is
       written in PIXELS and converted, so nothing in this file is guessed. --- */
    var VIS_H = 2 * CAMZ * Math.tan((FOV / 2) * Math.PI / 180);
    var PPU = H / VIS_H;                      /* ~261.4 px per world unit */
    function u(px) { return px / PPU; }

    scene.add(new THREE.AmbientLight(0xffffff, 1.9));
    var key = new THREE.DirectionalLight(0xdae4ff, 3.4); key.position.set(4, 7, 9);
    scene.add(key);
    var rim = new THREE.DirectionalLight(0x3555ff, 2.6); rim.position.set(-7, -3, 5);
    scene.add(rim);

    /* --- the plate. Body is dark brushed metal; the state colour lives on a thin
       LED strip child, never on the body (vid43: emissive on a whole box reads as
       a flat coloured slab / bar chart column).
       The first spike shipped the body at 0x14141a / metalness .78 and only the LED
       strips survived on near-black — the field read as a grid of dashes rather than
       hardware. Same class of error as vid42's dark end of the point ramp: on this
       ground the dim end has to be lifted until it actually reads. --- */
    var PW = u(84), PH = u(54), PD = u(11);

    var bodyGeo = new THREE.BoxGeometry(PW, PH, PD);
    var bodyMat = new THREE.MeshStandardMaterial({
      color: 0x2b2b36, metalness: 0.52, roughness: 0.36,
      transparent: true, opacity: 1
    });
    var body = new THREE.InstancedMesh(bodyGeo, bodyMat, COUNT);
    body.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    scene.add(body);

    var ledGeo = new THREE.BoxGeometry(PW * 0.80, PH * 0.15, PD * 0.7);
    ledGeo.translate(0, -PH * 0.28, PD * 0.62);
    var ledMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 1 });
    var led = new THREE.InstancedMesh(ledGeo, ledMat, COUNT);
    led.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    led.instanceColor = new THREE.InstancedBufferAttribute(
      new Float32Array(COUNT * 3), 3);
    scene.add(led);

    /* The Deloitte assurance ring — a real torus that travels down the dome.
       It is tilted ~20 degrees off horizontal on purpose: a perfectly horizontal
       ring passes through edge-on at the sphere's equator and renders as a solid
       bright BAR across the frame, which is what the first spike did. Off-axis it
       always projects as an ellipse and always reads as a ring. */
    var DOME_R = 620;                          /* px — dome420's radius           */
    var ring = new THREE.Mesh(
      new THREE.TorusGeometry(1, u(9), 12, 160),
      new THREE.MeshBasicMaterial({ color: 0xbcd0ff, transparent: true, opacity: 0 }));
    ring.rotation.x = Math.PI / 2 - 0.36;
    scene.add(ring);

    var group = new THREE.Group();
    scene.add(group);
    group.add(body); group.add(led); group.add(ring);

    /* ---------------- layouts: every target position/orientation precomputed
       once at init, so paint() is a lerp and nothing allocates per frame ------ */
    var rnd = mulberry32(20460729);
    var jitter = [], phase = [], spinAx = [];
    for (var i = 0; i < COUNT; i++) {
      jitter.push([rnd() - 0.5, rnd() - 0.5, rnd() - 0.5]);
      phase.push(rnd());
      spinAx.push([rnd() - 0.5, rnd() - 0.5, rnd() - 0.5]);
    }

    var L = {};
    function blank() {
      var a = { p: new Float32Array(COUNT * 3), q: new Float32Array(COUNT * 4),
                s: new Float32Array(COUNT) };
      for (var i = 0; i < COUNT; i++) { a.q[i * 4 + 3] = 1; a.s[i] = 1; }
      return a;
    }
    var _q = new THREE.Quaternion(), _e = new THREE.Euler(),
        _v = new THREE.Vector3(), _up = new THREE.Vector3(0, 0, 1),
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
        a.p[i * 3]     = jitter[i][0] * u(4600);
        a.p[i * 3 + 1] = jitter[i][1] * u(2600);
        a.p[i * 3 + 2] = jitter[i][2] * u(2600) - u(900);
        eul(a, i, jitter[i][1] * 3.1, jitter[i][0] * 3.1, jitter[i][2] * 3.1);
      }
      return a;
    })();

    /* WALL — 30 x 25 = 750 exactly, occupying 3100 x 1450 px */
    L.wall = (function () {
      var a = blank(), COLS = 30, ROWS = 25;
      var pxW = u(3100), pxH = u(1450);
      var gx = pxW / COLS, gy = pxH / ROWS;
      for (var i = 0; i < COUNT; i++) {
        var c = i % COLS, r = (i / COLS) | 0;
        a.p[i * 3]     = (c - (COLS - 1) / 2) * gx;
        a.p[i * 3 + 1] = ((ROWS - 1) / 2 - r) * gy;
        a.p[i * 3 + 2] = jitter[i][2] * u(46);
        eul(a, i, jitter[i][1] * 0.05, jitter[i][0] * 0.07, jitter[i][2] * 0.03);
      }
      return a;
    })();

    /* DOME(n) — a Fibonacci sphere of n plates, each tangent to the surface.
       Radius in px so the sphere fits a stated band; instances past n collapse. */
    function dome(n, rpx, cx) {
      var a = blank(), R = u(rpx), GA = Math.PI * (3 - Math.sqrt(5));
      for (var i = 0; i < COUNT; i++) {
        if (i >= n) { a.s[i] = 0; a.p[i * 3] = cx; continue; }
        var y = 1 - (i / (n - 1)) * 2, r = Math.sqrt(Math.max(0, 1 - y * y));
        var th = GA * i;
        var x = Math.cos(th) * r, z = Math.sin(th) * r;
        a.p[i * 3]     = x * R + cx;
        a.p[i * 3 + 1] = y * R;
        a.p[i * 3 + 2] = z * R;
        _v.set(x, y, z).normalize();
        _q.setFromUnitVectors(_up, _v);
        setQ(a, i, _q.x, _q.y, _q.z, _q.w);
      }
      return a;
    }
    L.dome420 = dome(420, DOME_R, 0);

    /* TWIN — same radius on both sides, so 420-dense vs 200-sparse is the only
       difference the eye can find. Instances 0..419 left, 420..619 right.

       DOME200 uses the SAME instances 420..619 on a centred sphere, and parks
       0..419 at the left dome's centre with scale 0. That makes c3 -> c4 a single
       continuous move: Aura's sphere (which arrived alone in c3, unjudged) slides
       right while Incogni's 420 bloom out of nothing on the left. The comparison
       is then density on one shared object, not two new props. */
    var TWIN_R = 430, TWIN_LX = u(-820), TWIN_RX = u(820);
    var GA = Math.PI * (3 - Math.sqrt(5));

    function fib(a, off, n, R, cx) {
      for (var k = 0; k < n; k++) {
        var i = off + k;
        var y = 1 - (k / (n - 1)) * 2, r = Math.sqrt(Math.max(0, 1 - y * y));
        var th = GA * k, x = Math.cos(th) * r, z = Math.sin(th) * r;
        a.p[i * 3] = x * R + cx; a.p[i * 3 + 1] = y * R; a.p[i * 3 + 2] = z * R;
        _v.set(x, y, z).normalize(); _q.setFromUnitVectors(_up, _v);
        setQ(a, i, _q.x, _q.y, _q.z, _q.w);
      }
    }

    L.twin = (function () {
      var a = blank();
      fib(a, 0, 420, u(TWIN_R), TWIN_LX);
      fib(a, 420, 200, u(TWIN_R), TWIN_RX);
      for (var i = 620; i < COUNT; i++) { a.s[i] = 0; }
      return a;
    })();

    L.dome200 = (function () {
      var a = blank();
      fib(a, 420, 200, u(TWIN_R), 0);
      for (var i = 0; i < 420; i++) { a.s[i] = 0; a.p[i * 3] = TWIN_LX; }
      for (var i = 620; i < COUNT; i++) { a.s[i] = 0; }
      return a;
    })();

    /* CONVERGE — everything falls into the mark's position and shrinks out */
    L.converge = (function () {
      var a = blank();
      for (var i = 0; i < COUNT; i++) {
        var t = phase[i] * Math.PI * 2;
        a.p[i * 3]     = Math.cos(t) * u(40) * jitter[i][0];
        a.p[i * 3 + 1] = Math.sin(t) * u(40) * jitter[i][1];
        a.p[i * 3 + 2] = jitter[i][2] * u(40);
        a.s[i] = 0.001;
        eul(a, i, 0, 0, t);
      }
      return a;
    })();

    /* ---------------- colour rules ---------------- */
    var C = {
      off:   new THREE.Color(0x2e2e38),
      blue:  new THREE.Color(0x4a6bff),
      blueH: new THREE.Color(0x8eacff),
      /* Aura's side of every comparison is NEUTRAL, never the alert colour — but
         neutral still has to survive on near-black, so it is a light warm grey. */
      grey:  new THREE.Color(0xa8a8b6),
      red:   new THREE.Color(0xe5372b),
      green: new THREE.Color(0x2fd968)
    };

    /* The proxy. ONLY the gsap timeline writes to this. */
    var P = {
      a: "scatter", b: "scatter", k: 0,
      colour: "neutral",        /* neutral | exposed | scan | gap | verified */
      lit: 1,                   /* fraction of the active set that is powered  */
      sweep: 0,                 /* 0..1 scan progress, drives ring + colour     */
      ringOn: 0,
      rotX: 0, rotY: 0, rotZ: 0,
      ox: 0, oy: 0,             /* group offset IN PIXELS                       */
      camZ: 0,                  /* dolly IN PIXELS (positive = pull back)       */
      alpha: 0,
      scale: 1
    };

    /* How many instances the reveal counter walks through, per layout. `lit` is a
       FRACTION of this, so an on-screen counter and the field can never disagree
       about how many are on. dome200 counts its own 200 even though they are
       instances 420..619. */
    function activeCount(name) {
      if (name === "dome420") return 420;
      if (name === "twin") return 620;
      if (name === "dome200") return 200;
      return COUNT;
    }

    function paint() {
      var A = L[P.a] || L.scatter, B = L[P.b] || A;
      var k = P.k < 0 ? 0 : (P.k > 1 ? 1 : P.k);
      var ease = k * k * (3 - 2 * k);                 /* smoothstep, pure in k */

      var al = P.alpha < 0 ? 0 : (P.alpha > 1 ? 1 : P.alpha);
      bodyMat.opacity = al; ledMat.opacity = al;
      body.visible = led.visible = al > 0.002;
      ring.material.opacity = al * P.ringOn * 0.9;
      ring.visible = ring.material.opacity > 0.004;

      group.rotation.set(P.rotX, P.rotY, P.rotZ);
      group.position.set(u(P.ox), u(P.oy), 0);
      group.scale.setScalar(P.scale);
      camera.position.z = CAMZ + u(P.camZ);

      if (body.visible) {
        var layoutNow = P.k >= 0.5 ? P.b : P.a;
        var n = activeCount(layoutNow);
        /* dome200's plates ARE instances 420..619, so the reveal order has to be
           measured from 420 or `lit` would light 200 hidden instances instead. */
        var base = layoutNow === "dome200" ? 420 : 0;
        for (var i = 0; i < COUNT; i++) {
          var s = A.s[i] + (B.s[i] - A.s[i]) * ease;
          _pos.set(
            A.p[i * 3]     + (B.p[i * 3]     - A.p[i * 3])     * ease,
            A.p[i * 3 + 1] + (B.p[i * 3 + 1] - A.p[i * 3 + 1]) * ease,
            A.p[i * 3 + 2] + (B.p[i * 3 + 2] - A.p[i * 3 + 2]) * ease);
          _qq.set(A.q[i * 4], A.q[i * 4 + 1], A.q[i * 4 + 2], A.q[i * 4 + 3]);
          _q.set(B.q[i * 4], B.q[i * 4 + 1], B.q[i * 4 + 2], B.q[i * 4 + 3]);
          _qq.slerp(_q, ease);
          _sc.set(s, s, s);
          _m.compose(_pos, _qq, _sc);
          body.setMatrixAt(i, _m);
          led.setMatrixAt(i, _m);

          /* --- state colour. Index order IS the reveal order, so a counter and
             the field always agree about how many are on. --- */
          var on = (i - base) < n * P.lit;
          if (!on) { _c.copy(C.off); }
          else if (P.colour === "exposed") { _c.copy(C.red); }
          else if (P.colour === "verified") { _c.copy(C.green); }
          /* Aura's side of every comparison is NEUTRAL — painting a competitor in
             the alert colour would editorialise past what the presenter actually says. */
          else if (P.colour === "aura") { _c.copy(C.grey); }
          else if (P.colour === "gap") {
            _c.copy(i < 420 ? C.blue : C.grey);
          } else if (P.colour === "scan") {
            /* the sweep runs down the sphere in Y, which is what the ring does,
               so the plates it has passed are the plates that turn green */
            var yn = (A.p[i * 3 + 1] + (B.p[i * 3 + 1] - A.p[i * 3 + 1]) * ease);
            var frac = 0.5 - yn / (2 * u(DOME_R));
            _c.copy(frac <= P.sweep ? C.green : C.blue);
          } else { _c.copy(C.blue); }
          led.setColorAt(i, _c);
        }
        body.instanceMatrix.needsUpdate = true;
        led.instanceMatrix.needsUpdate = true;
        led.instanceColor.needsUpdate = true;
      }

      if (ring.visible) {
        /* the ring hugs the sphere: its radius IS the cross-section at its height,
           plus a small clearance so it reads as passing around the plates */
        /* Clearance has to be generous. At u(58) the torus sat among the plates
           and the parts poking out read as a bright BLADE stuck through the
           sphere rather than a ring travelling around it. A floor on the radius
           also stops it collapsing to a dot at the poles. */
        var yy = 1 - 2 * P.sweep, rr = Math.sqrt(Math.max(0.03, 1 - yy * yy));
        ring.position.set(0, u(DOME_R) * yy, 0);
        ring.scale.setScalar(Math.max(u(DOME_R) * rr, u(150)) + u(150));
      }

      renderer.render(scene, camera);
    }

    paint();
    return { P: P, paint: paint, PPU: PPU, u: u, COUNT: COUNT };
  };
})(window);
