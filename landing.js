/* Reel Factory landing behaviour.
   Everything here is optional polish: if any block throws, the page still reads. */
(function () {
  'use strict';

  // Arm the reveal convention FIRST, before anything can throw.
  try { document.documentElement.classList.add('js'); } catch (e) {}

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {

    // 1. Ticker: clone the set once so the -50% loop is seamless.
    try {
      var track = document.getElementById('ticker');
      if (track && track.children.length === 1) {
        var clone = track.children[0].cloneNode(true);
        clone.setAttribute('aria-hidden', 'true');
        track.appendChild(clone);
      }
    } catch (e) {}

    // 2. Scroll reveal + number count-up.
    var risers = [];
    try { risers = Array.prototype.slice.call(document.querySelectorAll('[data-rise]')); } catch (e) {}

    function countUp(scope) {
      try {
        var nodes = scope.matches && scope.matches('[data-count]')
          ? [scope]
          : Array.prototype.slice.call(scope.querySelectorAll('[data-count]'));
        nodes.forEach(function (n) {
          if (n.dataset.done) return;
          n.dataset.done = '1';
          var target = parseInt(n.getAttribute('data-count'), 10);
          if (!isFinite(target)) return;
          var t0 = null, dur = 900;
          function step(ts) {
            if (t0 === null) t0 = ts;
            var p = Math.min(1, (ts - t0) / dur);
            var eased = 1 - Math.pow(1 - p, 3);
            n.textContent = String(Math.round(target * eased));
            if (p < 1) requestAnimationFrame(step);
          }
          n.textContent = '0';
          requestAnimationFrame(step);
        });
      } catch (e) {}
    }

    var reduce = false;
    try {
      reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches;
    } catch (e) {}

    function show(el) {
      try {
        if (!el || el.classList.contains('in')) return;
        el.classList.add('in');
        countUp(el);
      } catch (e) {}
    }

    // The hard failsafe. A blank section on stage is far worse than an element
    // that appears without animating, so after this everything is visible, always.
    function revealAll() {
      risers.forEach(show);
    }
    try { setTimeout(revealAll, 1200); } catch (e) { revealAll(); }
    try { window.addEventListener('load', function () { setTimeout(revealAll, 400); }); } catch (e) {}

    function inViewNow(el) {
      try {
        var r = el.getBoundingClientRect();
        var h = window.innerHeight || document.documentElement.clientHeight;
        return r.top < h * 1.1 && r.bottom > -40;
      } catch (e) { return true; }
    }

    try {
      if (!('IntersectionObserver' in window) || reduce) {
        revealAll();
      } else {
        // 3a. Anything already on screen reveals synchronously, before the observer exists.
        risers.forEach(function (el, i) {
          el.style.transitionDelay = (Math.min(i, 4) * 55) + 'ms';
          if (inViewNow(el)) show(el);
        });

        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (!en.isIntersecting) return;
            show(en.target);
            try { io.unobserve(en.target); } catch (e) {}
          });
        }, { rootMargin: '0px 0px -10% 0px', threshold: 0 });

        risers.forEach(function (el) {
          if (!el.classList.contains('in')) io.observe(el);
        });
      }
    } catch (e) {
      revealAll();
    }

    // 3. In-page anchors scroll smoothly under the sticky nav.
    try {
      document.addEventListener('click', function (ev) {
        var a = ev.target && ev.target.closest ? ev.target.closest('a[href^="#"]') : null;
        if (!a) return;
        var id = a.getAttribute('href');
        if (!id || id === '#') return;
        var t = document.querySelector(id);
        if (!t) return;
        ev.preventDefault();
        var y = t.getBoundingClientRect().top + window.pageYOffset - 72;
        window.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
      });
    } catch (e) {}
  });
})();
