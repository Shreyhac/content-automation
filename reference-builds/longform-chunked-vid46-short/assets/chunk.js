/* ============================================================================
   vid46-short — shared chunk kit (vertical, 1080x1920).

   Two HyperFrames projects have to behave like one continuous 40s film, so
   everything that must be identical across the join lives here:

     mountGround(tl, T0, D)   the ground light rig, phased off ABSOLUTE film time
     shortKit(tl, T0)         the face band's edge sweep, swaps, local/abs time
     splitWords / wordRise    THE text entrance (one device, repeated)
     digitSettle              a published figure ARRIVING, never counting from 0
     packet                   an event emitting a particle at a target

   v2 CHANGES. There is now exactly ONE A-roll placement in the whole short (a
   1080x1000 band at y0, baked by bake_clips.py from short-transforms.json), so the
   kit no longer picks between placements — it only sweeps the band in and out.
   And the flash cut, which v1 fired at 11 of 12 beat boundaries, is now used once.
   ============================================================================ */

/* Ground motion is LINEAR and keyed to absolute film time: a chunk starting at T0
   tweens rotation from 360*T0/P to 360*(T0+D)/P, so the second chunk resumes
   exactly where the first left off. Anything eased, or restarted per chunk, is
   visible at the cut.

   The stage lift (.gS) and the sheen (.gSh) do NOT move: they are the floor and
   the surface highlight of a lit set, and drifting them reads as the room sliding. */
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
  drift("bgDots", 140, -46, 46);
};

/* ============================================================================
   TEXT MOTION — one signature device.

   Everything typographic enters by masked per-word rise, so the film has one
   handwriting instead of eight. The DOM split happens ONCE at parse time; it must
   never happen inside an onUpdate, because the renderer seeks non-linearly and a
   DOM mutation driven by tween progress is seek-order dependent.
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
     splits as "One" / "job" / "," / "done" and renders as `One job , done`. */
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

/* The entrance. yPercent 124 clears the mask's descender padding (.18em).
   The .028/.52 stagger/duration pair is the house standard: eleven headlines in
   the film's round 2 ran slower than this and rendered half-formed at their beat. */
window.wordRise = function (tl, sel, t, o) {
  o = o || {};
  var els = document.querySelectorAll(sel), all = [];
  for (var i = 0; i < els.length; i++) {
    var ws = window.splitWords(els[i]);
    for (var j = 0; j < ws.length; j++) all.push(ws[j].firstChild);
  }
  if (!all.length) return;
  tl.fromTo(all, { yPercent: 124 },
    { yPercent: 0, duration: o.dur || 0.52, ease: o.ease || "expo.out",
      stagger: o.stagger === undefined ? 0.028 : o.stagger }, t);
  return all.length;
};

/* A published figure ARRIVING.

   Round 1 of the film ticked 750, 245M and 200 up from zero, so the first third of
   each beat showed a figure that is simply wrong — under an audited attribution
   line. `spread` therefore defaults to 0: the number arrives by masked rise and is
   correct in every frame it exists. The parameter stays for a genuinely live count.

   The displayed value is a PURE function of tween progress, which is what makes it
   safe under non-linear seeking. */
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
  tl.fromTo(el, { yPercent: 26, opacity: 0 },
    { yPercent: 0, opacity: 1, duration: 0.42, ease: "expo.out" }, t);
};

window.shortKit = function (tl, T0) {

  function L(abs) { return abs - T0; }          /* absolute film time -> chunk time */

  /* Set a state that a chunk needs on its FIRST FRAME.

     A zero-duration tl.set() at position 0 is not reliably applied while the
     playhead sits exactly on 0 — whether GSAP treats it as already-run at time 0
     is implementation-dependent, so in the film it painted in c4 and did NOT paint
     in c2, shipping a one-frame flash of raw full-bleed A-roll at the join.

     So: for t<=0 write the value IMMEDIATELY with gsap.set (guarantees frame 0),
     and ALSO keep the timeline entry (guarantees the state is restored if a worker
     seeks back to 0 after rendering a later frame). The two agree, so writing both
     is free. */
  function put(sel, vars, t) {
    if (t <= 0) gsap.set(sel, vars);
    tl.set(sel, vars, t);
  }

  /* ---------------------------------------------------------------------------
     THE FACE — ONE PICTURE, TWO STATES, AND THE MOVE BETWEEN THEM.

     v1 changed the face's placement five times by CUTS and the presenter's head changed size
     every time the presenter appeared; the owner called the A-roll cuts weird. v3 adopts
     vid39's answer, which the client asked for by name: the face never cuts between sizes,
     it MOVES between them. #faceScene's clip-path and #faceCam's transform tween
     together over one third of a second, so the shrink reads as camera operation.

     Every inset() is written with FOUR EXPLICIT SIDES. A collapsed shorthand
     mispairs GSAP's numbers and paints a dark slab mid-tween (LEARNINGS.md).

     The geometry is solved in solve_short.py, never typed here twice:
       HERO  clip inset(0 0 710 0 round 0)          cam scale 1,      x0,   y0
       CARD  clip inset(838 260 346 260 round 30)   cam scale .6786,  x173, y799
       OFF   clip inset(1920 260 346 260 round 30)  - collapsed INTO the card's own
             rect, so a card-in grows from where the card belongs.
     ------------------------------------------------------------------------- */
  var FACE = {
    hero: { clip: "inset(0px 0px 710px 0px round 0px)",
            cam: { scale: 1, x: 0, y: 0 } },
    card: { clip: "inset(838px 260px 346px 260px round 30px)",
            cam: { scale: 0.6786, x: 173, y: 799 } },
    off:  { clip: "inset(1920px 260px 346px 260px round 30px)",
            cam: { scale: 0.6786, x: 173, y: 799 } }
  };

  function faceSet(state, t) {
    var f = FACE[state];
    put("#faceScene", { clipPath: f.clip }, t);
    put("#faceCam", Object.assign({ transformOrigin: "0 0" }, f.cam), t);
    put("#faceFx", { opacity: state === "card" ? 1 : 0 }, t);
    put("#heroEdge", { opacity: state === "hero" ? 1 : 0 }, t);
    put("#faceCam .grade", { opacity: state === "hero" ? 1 : 0 }, t);
  }

  /* The move. `dur` 0.34 is vid39's; anything faster reads as a cut and anything
     slower reads as a zoom. Dressing (the card frame, the hero shelf, the hero
     grade) crossfades UNDER the move rather than on top of it. */
  function faceTo(state, t, dur) {
    dur = dur || 0.34;
    var f = FACE[state], card = state === "card", hero = state === "hero";
    tl.to("#faceScene", { clipPath: f.clip, duration: dur,
                          ease: "power3.inOut" }, t);
    tl.to("#faceCam", Object.assign({ duration: dur, ease: "power3.inOut" },
                                    f.cam), t);
    tl.to("#faceFx", { opacity: card ? 1 : 0, duration: card ? 0.22 : 0.14,
                       ease: card ? "power2.out" : "power1.in" },
          card ? t + 0.14 : t);
    tl.to("#heroEdge", { opacity: hero ? 1 : 0, duration: 0.22, ease: "none" },
          hero ? t + 0.16 : t);
    tl.to("#faceCam .grade", { opacity: hero ? 1 : 0, duration: 0.24,
                               ease: "power1.out" }, hero ? t + 0.10 : t);
  }

  /* PUNCH AND HOLD. vid39 pushes slowly into the face for the length of a face
     beat instead of leaving it static. Applied to #faceCam ON TOP of whichever
     state it is in, so it works in either. `to` only: the state tween owns the
     base value. */
  function punch(t, dur, from, to) {
    tl.fromTo("#faceCam", { scale: from },
      { scale: to, duration: dur, ease: "none" }, t);
  }

  /* Show exactly one of the chunk's face clips. They share #faceCam, so they share
     the camera and cannot disagree about placement. */
  function faceClip(t, sel) {
    var all = document.querySelectorAll("#faceCam video");
    for (var i = 0; i < all.length; i++) {
      put("#" + all[i].id, { autoAlpha: all[i].id === sel ? 1 : 0 }, t);
    }
  }

  /* Flash cut. v1 fired one of these at 11 of its 12 beat boundaries, which in a
     40s piece is a strobe — "the cuts are very weird". v2 uses EXACTLY ONE, on
     "paying twice" in b7. Everything else is an edge sweep or nothing at all.

     The hard kill at t+0.07 is not optional: non-linear seeking can otherwise
     settle after the fade and leave the frame black. */
  function blink(t, amt) {
    var a = amt === undefined ? 1 : amt;
    tl.to("#cover", { opacity: a, duration: .06, ease: "power2.in" }, t - 0.06);
    tl.to("#cover", { opacity: 0, duration: .06, ease: "power2.out" }, t + 0.005);
    tl.set("#cover", { opacity: 0 }, t + 0.07);
  }

  /* Swap scenes WITHOUT a flash. This is the default in v2: inside an act the face
     band is not interrupted at all and only the graphics-zone content changes, and
     between acts the edge sweep is the transition. The incoming scene is COMPOSED
     on the swap frame and only settles — fading a scene up from 0 after a swap
     leaves an empty frame, which is what made v1's s1->s2 join an empty outline. */
  function swap(t, outSel, inSel) {
    if (outSel) put(outSel, { autoAlpha: 0 }, t);
    if (inSel) put(inSel, { autoAlpha: 1 }, t);
  }

  /* Swap scenes on a hard flash cut. ONE use in the whole short. */
  function cut(t, outSel, inSel, amt) {
    blink(t, amt);
    swap(t, outSel, inSel);
  }

  /* An event emitting a particle at a target. */
  function packet(sel, t, x0, y0, x1, y1, dur) {
    dur = dur || 0.40;
    tl.set(sel, { opacity: 0, x: x0, y: y0 }, t - 0.01);
    tl.to(sel, { opacity: 1, duration: .06 }, t);
    tl.to(sel, { x: x1, y: y1, duration: dur, ease: "power2.in" }, t);
    tl.to(sel, { opacity: 0, duration: .09 }, t + dur - 0.07);
  }

  /* SCREEN SHAKE. vid39 shakes the frame when a headline number lands. Two
     descending kicks in opposite directions, deterministic (no Math.random - the
     renderer seeks non-linearly and a random value would differ per frame). */
  function shake(sel, t, amp) {
    amp = amp || 14;
    tl.to(sel, { x: amp, y: -amp * 0.45, duration: 0.05, ease: "none" }, t);
    tl.to(sel, { x: -amp * 0.7, y: amp * 0.3, duration: 0.06, ease: "none" }, t + 0.05);
    tl.to(sel, { x: amp * 0.35, y: -amp * 0.15, duration: 0.06, ease: "none" }, t + 0.11);
    tl.to(sel, { x: 0, y: 0, duration: 0.09, ease: "power2.out" }, t + 0.17);
  }

  /* THE SKEWED BAND WIPE. vid39's act transition: a lit blade crosses the frame on
     a 13-degree skew with a dark panel behind it, and the incoming scene is already
     composed underneath. This is what replaces v1's flash cut at every boundary.

     `t` IS THE FRAME THE SWAP HAPPENS ON, and the geometry is solved so the dark
     panel COVERS the whole canvas on exactly that frame. All three run symmetrically
     from t-dur/2 to t+dur/2 with an inOut ease, so at t each is at the midpoint of
     its own travel:

       #wipeC  1800 wide, -2600 -> 1400, midpoint -600  => spans -600..1200, covers
       #wipeA   420 wide, -2100 -> 1900, midpoint -100  => the blue slab
       #wipeB   120 wide, -1900 -> 2100, midpoint  100  => the lit edge, on top

     The first render had the panel arriving 0.15s AFTER the swap, so the scene
     change happened in the clear. */
  function wipe(t, dur) {
    dur = dur || 0.60;
    var a = t - dur / 2;
    tl.set(["#wipeA", "#wipeB", "#wipeC"], { opacity: 1 }, a);
    tl.fromTo("#wipeC", { x: -2600 }, { x: 1400, duration: dur, ease: "power2.inOut" }, a);
    tl.fromTo("#wipeA", { x: -2100 }, { x: 1900, duration: dur, ease: "power2.inOut" }, a);
    tl.fromTo("#wipeB", { x: -1900 }, { x: 2100, duration: dur, ease: "power2.inOut" }, a);
    tl.set(["#wipeA", "#wipeB", "#wipeC"], { opacity: 0 }, a + dur + 0.02);
  }

  /* A white-blue flash. ONE use in the whole short, on "paying twice". */
  function flash(t, amt) {
    tl.set("#flash", { opacity: 0 }, t - 0.05);
    tl.to("#flash", { opacity: amt === undefined ? 0.85 : amt, duration: 0.05,
                      ease: "power2.in" }, t - 0.05);
    tl.to("#flash", { opacity: 0, duration: 0.20, ease: "power2.out" }, t);
    tl.set("#flash", { opacity: 0 }, t + 0.22);
  }

  /* One diagonal specular pass across a surface. */
  function shine(sel, t, from, to, dur) {
    tl.set(sel, { opacity: 1, x: from }, t);
    tl.to(sel, { x: to, duration: dur || 0.85, ease: "power2.inOut" }, t);
    tl.to(sel, { opacity: 0, duration: 0.14, ease: "none" }, t + (dur || 0.85) - 0.12);
  }

  /* A rule/limb that draws rather than fades. */
  function draw(sel, t, dur, ease) {
    tl.fromTo(sel, { scaleX: 0 },
      { scaleX: 1, duration: dur || 0.42, ease: ease || "power3.out" }, t);
  }

  return { L: L, put: put, blink: blink, cut: cut, swap: swap, packet: packet,
           draw: draw, faceSet: faceSet, faceTo: faceTo, faceClip: faceClip,
           punch: punch, shake: shake, wipe: wipe, flash: flash, shine: shine };
};
