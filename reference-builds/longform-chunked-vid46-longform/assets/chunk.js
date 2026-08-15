/* ============================================================================
   vid46 — shared chunk kit.  ROUND 2.

   Eight separate HyperFrames projects have to behave like one continuous film.
   Everything that must be byte-identical across the seven joins lives here, so a
   fix lands in one place instead of eight:

     mountGround(tl, T0, D)  the ground light rig, phased off ABSOLUTE film time
     chunkKit(tl, T0)        face states, the ink-blink cut, local/abs time
     splitWords / wordRise   THE text entrance (one device, repeated)
     digitSettle             a published figure ARRIVING, never counting from 0
     packet                  an event emitting a particle at a target

   Window objects (W1..Wn) still live in each chunk's HTML because
   inject_windows.py rewrites them from card-transforms.json — measurements must
   never be hand-typed into a composition. Their a/b times are ABSOLUTE; every
   helper here converts, so no chunk has to remember which space it is in.
   ============================================================================ */

/* Ground motion is LINEAR and keyed to absolute film time: a chunk starting at T0
   tweens rotation from 360*T0/P to 360*(T0+D)/P, so a chunk that begins mid-orbit
   resumes exactly where the previous one left off. Anything eased, or restarted
   per chunk, is visible at the cut.

   The stage lift (.gS) and the sheen (.gSh) do NOT move. They are the floor and
   the surface highlight of a lit set; drifting them reads as the room sliding. */
window.mountGround = function (tl, T0, D) {
  function orbit(sel, P, dir) {
    if (!document.querySelector(sel)) return;
    tl.fromTo(sel, { rotation: dir * 360 * T0 / P },
      { rotation: dir * 360 * (T0 + D) / P, duration: D, ease: "none" }, 0);
  }
  orbit("#orbA", 300, 1);    /* blue key   */
  orbit("#orbV", 420, -1);   /* violet mid */
  orbit("#orbB", 380, -1);   /* green counter */
  orbit("#orbC", 240, 1);    /* navy bloom */

  function drift(id, P, dx, dy) {
    var el = document.getElementById(id);
    if (!el) return;
    var a = (T0 % P) / P, p = { k: a };
    tl.fromTo(p, { k: a }, {
      k: a + D / P, duration: D, ease: "none", immediateRender: true,
      onUpdate: function () {
        el.style.backgroundPosition =
          (p.k * dx).toFixed(2) + "px " + (p.k * dy).toFixed(2) + "px";
      }
    }, 0);
  }
  drift("bgDots", 140, -96, 96);
};

/* ============================================================================
   TEXT MOTION — one signature device.

   The owner asked for "perfect text animations"; round 1 shipped eight variants
   of y:+20/opacity:0->1. Everything typographic now enters by masked per-word
   rise, so the film has one handwriting instead of eight.

   The DOM split happens ONCE at parse time. It must never happen inside an
   onUpdate: the renderer seeks non-linearly, so a DOM mutation driven by tween
   progress is seek-order dependent (this is what forced the c1 caret to become a
   flex sibling in round 1).
   ============================================================================ */
window.splitWords = function (el) {
  if (el.__words) return el.__words;
  var nodes = [], n;
  while (el.firstChild) { nodes.push(el.firstChild); el.removeChild(el.firstChild); }

  function mask(content) {
    var wm = document.createElement("span"); wm.className = "wm";
    var w = document.createElement("span"); w.className = "w";
    if (typeof content === "string") w.textContent = content;
    else w.appendChild(content);
    wm.appendChild(w);
    return wm;
  }

  /* Tokens carry a GLUE flag: true means "there was no whitespace before me in the
     source, so I belong to the previous word". Without it, `One <em>job</em>, done`
     splits as "One" / "job" / "," / "done" and renders as `One job , done` — a
     floating comma with a space either side. That shipped into c3's first render. */
  var toks = [], prevEndsWithSpace = true;
  for (var i = 0; i < nodes.length; i++) {
    n = nodes[i];
    if (n.nodeType === 3) {
      var txt = n.textContent;
      if (!txt) continue;
      var lead = /^\s/.test(txt);
      var parts = txt.split(/\s+/).filter(Boolean);
      for (var j = 0; j < parts.length; j++) {
        toks.push({ c: parts[j], glue: j === 0 && !lead && toks.length > 0 });
      }
      if (parts.length) prevEndsWithSpace = /\s$/.test(txt);
    } else {
      /* an inline accent (<em>/<i>/<b>) travels as ONE unit so the coloured word
         is not torn apart mid-rise */
      toks.push({ c: n, glue: !prevEndsWithSpace && toks.length > 0 });
      prevEndsWithSpace = false;
    }
  }

  var out = [];
  for (var t = 0; t < toks.length; t++) {
    if (toks[t].glue && out.length) {
      /* fold into the previous mask rather than becoming its own word */
      var w = out[out.length - 1].firstChild;
      if (typeof toks[t].c === "string") w.appendChild(document.createTextNode(toks[t].c));
      else w.appendChild(toks[t].c);
    } else {
      out.push(mask(toks[t].c));
    }
  }
  for (var k = 0; k < out.length; k++) {
    if (k) el.appendChild(document.createTextNode(" "));
    el.appendChild(out[k]);
  }
  el.__words = out;
  return out;
};

/* The entrance. yPercent 124 clears the mask's descender padding (.16em). */
window.wordRise = function (tl, sel, t, o) {
  o = o || {};
  var els = document.querySelectorAll(sel), all = [];
  for (var i = 0; i < els.length; i++) {
    var ws = window.splitWords(els[i]);
    for (var j = 0; j < ws.length; j++) all.push(ws[j].firstChild);
  }
  if (!all.length) return;
  tl.fromTo(all, { yPercent: 124 },
    { yPercent: 0, duration: o.dur || 0.66, ease: o.ease || "expo.out",
      stagger: o.stagger === undefined ? 0.052 : o.stagger }, t);
  return all.length;
};

/* A published figure ARRIVING.

   Round 1 ticked 750, 245M and 200 up from zero, so the first third of each beat
   showed a figure that is simply wrong — and these are audited numbers with an
   attribution line under them.

   Round 2's first attempt was "roll in from within ~2% and lock", which still put
   "418+" on screen under a verified-by-Deloitte line for about 0.2s. So `spread`
   now defaults to 0 for every audited figure in this film: the number ARRIVES by
   masked rise and is correct in every frame it exists. The parameter stays for a
   count that is genuinely live rather than published.

   The displayed value is a PURE function of tween progress, which is what makes
   it safe under non-linear seeking. */
window.digitSettle = function (tl, sel, t, finalNum, o) {
  o = o || {};
  var el = typeof sel === "string" ? document.querySelector(sel) : sel;
  if (!el) return;
  var pre = o.pre || "", post = o.post || "";
  var dur = o.dur || 0.34;
  var fmt = o.fmt || function (v) { return Math.round(v).toLocaleString("en-US"); };
  var from = finalNum * (1 - (o.spread === undefined ? 0 : o.spread));
  var p = { v: from };
  el.textContent = pre + fmt(finalNum) + post;
  tl.fromTo(p, { v: from }, {
    v: finalNum, duration: dur, ease: "power3.out", immediateRender: true,
    onUpdate: function () { el.textContent = pre + fmt(p.v) + post; }
  }, t);
  /* and it lands with the same masked-rise energy as the type around it */
  tl.fromTo(el, { yPercent: 26, opacity: 0 },
    { yPercent: 0, opacity: 1, duration: 0.42, ease: "expo.out" }, t);
};

window.chunkKit = function (tl, T0) {
  var CARD_CP = "inset(440.1px 180.2px 440.3px 2280.4px round 40px)";
  var FULL_CP = "inset(0.1px 0.2px 0.3px 0.4px round 0.5px)";

  function L(abs) { return abs - T0; }          /* absolute film time -> chunk time */

  /* Set a state that a chunk needs on its FIRST FRAME.

     A zero-duration tl.set() at position 0 is not reliably applied while the
     playhead sits exactly on 0 — whether GSAP treats it as already-run at time 0
     is implementation-dependent, so it painted in c4 and did NOT paint in c2.
     c2's frame 0 shipped as a single frame of raw full-bleed A-roll before the
     card snapped in, with the record column illegible over the presenter's back wall. Every
     chunk boundary is a join in the assembled film, so a missed frame 0 is a
     one-frame flash at six of the seven joins.

     So: for t<=0 write the value IMMEDIATELY with gsap.set (guarantees frame 0),
     and ALSO keep the timeline entry (guarantees the state is restored if a
     worker seeks back to 0 after rendering a later frame). The two agree, so
     writing both is free. */
  function put(sel, vars, t) {
    if (t <= 0) gsap.set(sel, vars);
    tl.set(sel, vars, t);
  }

  function faceFull(t) {
    put("#faceWrap", { autoAlpha: 1, clipPath: FULL_CP }, t);
    put("#face", { scale: 1, x: 0, y: 0 }, t);
    put("#faceFx", { autoAlpha: 0 }, t);
  }

  /* Card a window: ONE constant transform for the whole window.

     Round 1 tweened x along a smoothed per-window tracking curve, meant to read
     as a camera operator following the presenter as they swayed. The owner's read was
     "why is the presenter's frame always moving left-right, you have added some issue."
     A follow that slow is not legible as camera work — it is legible as drift.
     One constant tx (the window median) is correct at the median and never
     draws attention to itself. */
  function faceCard(t, w) {
    put("#faceWrap", { autoAlpha: 1, clipPath: CARD_CP }, t);
    put("#faceFx", { autoAlpha: 1 }, t);
    put("#face", { scale: w.s, x: w.tx, y: w.ty }, t);
  }

  function hideFace(t) {
    put("#faceWrap", { autoAlpha: 0 }, t);
    put("#faceFx", { autoAlpha: 0 }, t);
  }

  /* Flash cut. The hard kill at t+0.07 is not optional: non-linear seeking can
     otherwise settle after the fade and leave the frame black. */
  function blink(t) {
    tl.to("#cover", { opacity: 1, duration: .06, ease: "power2.in" }, t - 0.06);
    tl.to("#cover", { opacity: 0, duration: .06, ease: "power2.out" }, t + 0.005);
    tl.set("#cover", { opacity: 0 }, t + 0.07);
  }

  /* Swap scenes on a hard cut. The incoming scene is COMPOSED on the cut and only
     settles — fading a field up from 0 after a cut leaves an empty frame, which is
     the bug that shipped in the first c1 render. */
  function cut(t, outSel, inSel) {
    blink(t);
    if (outSel) put(outSel, { autoAlpha: 0 }, t);
    if (inSel) put(inSel, { autoAlpha: 1 }, t);
  }

  /* An event emitting a particle at a target. The carrier for "how data gets
     collected" — three things that HAPPEN, not three rows in a list. */
  function packet(sel, t, x0, y0, x1, y1, dur) {
    dur = dur || 0.46;
    tl.set(sel, { opacity: 0, x: x0, y: y0 }, t - 0.01);
    tl.to(sel, { opacity: 1, duration: .07 }, t);
    tl.to(sel, { x: x1, y: y1, duration: dur, ease: "power2.in" }, t);
    tl.to(sel, { opacity: 0, duration: .10 }, t + dur - 0.08);
  }

  return { L: L, faceFull: faceFull, faceCard: faceCard, hideFace: hideFace,
           blink: blink, cut: cut, packet: packet,
           CARD_CP: CARD_CP, FULL_CP: FULL_CP };
};
