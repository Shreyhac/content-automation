#!/usr/bin/env python3
"""Catch elements that JUMP between one frame and the next outside a cut.

usage: python3 snap_guard.py

WHY THIS EXISTS
---------------
This composition sets `defaults: { immediateRender: false }` on its timeline,
because gsap's fromTo otherwise stamps every from-state onto its element at BUILD
time — which is how the cover frame shipped with the close's camera on it, the
eyebrow at opacity 0 and both price columns at 0.35.

Turning it off fixes that and introduces the opposite fault, which is quieter: an
element now sits at its FINAL css value until its tween starts, and then SNAPS back
to the from-state and replays. `#mRule` was drawn across the frame from t=0, vanished
at 4.92 and drew itself again. Every gate passed it. It is invisible to lint (valid
markup), to validate (no console error), to safe_zones (it was exactly where it
belongs, both times), to paint_guard (it is not a caption) and to motion_guard (a
snap is a change, and changes are what that guard wants to see).

So: walk the timeline frame by frame and flag any element that is visible on both
sides of a frame boundary and moves discontinuously across it — a big opacity step,
a big translate, a big scale change. Real cuts do exactly that on purpose, so the
beat boundaries, the wipe frames and the face's own state moves are excluded by
name, and everything else has to explain itself.

WHAT SEPARATES A SNAP FROM AN ENTRANCE, which is the whole difficulty: both are a
big one-frame jump, and `back.out` legitimately moves 68% of its travel in the first
16% of its duration. So the test is not the size of the jump. It is the SHAPE around
it — the fault is exactly "the element was already at its resting value, it left, and
then it came back":

    static for >= 0.5s  ->  one-frame jump  ->  returns to within 2% of the value it
                                                held before the jump

An entrance fails that test on both ends: it was not on screen beforehand, and it
does not return to where it started. Proved with a negative control at the bottom of
this file's history — reverting #mRule to a plain `draw()` makes this FAIL, and
staging it makes it PASS.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24000 / 1001.0

D_OPACITY = 0.35        # a step bigger than any single frame of a >=0.2s fade
D_TRANSLATE = 40.0      # px in one frame
D_SCALE = 0.15

PROBE = """
(args) => {
  const [times, fps] = args;
  const tl = window.__timelines.vid59short;
  const r = document.getElementById('root');
  r.style.width = r.dataset.width + 'px';
  r.style.height = r.dataset.height + 'px';
  const snap = (t) => {
    tl.pause();
    tl.time(t, false);
    const m = {};
    r.querySelectorAll('*').forEach(el => {
      if (el.closest('#bg')) return;
      const key = el.id || (el.className && el.className.toString()) || el.tagName;
      const c = getComputedStyle(el);
      const op = c.visibility === 'hidden' ? 0 : parseFloat(c.opacity);
      let sx = 1, sy = 1, tx = 0, ty = 0;
      if (c.transform && c.transform !== 'none') {
        const n = c.transform.match(/-?[\\d.e+]+/g).map(Number);
        if (n.length >= 6) { sx = Math.hypot(n[0], n[1]); sy = Math.hypot(n[2], n[3]);
                             tx = n[4]; ty = n[5]; }
      }
      // several elements share a class name; key them apart by document order
      let k = key, i = 1;
      while (k in m) { k = key + '#' + (++i); }
      m[k] = [op, sx, sy, tx, ty];
    });
    return m;
  };
  const out = [];
  const track = {};
  let prev = snap(times[0]);
  for (const k in prev) track[k] = [prev[k]];
  for (let i = 1; i < times.length; i++) {
    const cur = snap(times[i]);
    for (const k in cur) { (track[k] = track[k] || [])[i] = cur[k]; }
    for (const k in cur) {
      if (!(k in prev)) continue;
      const a = prev[k], b = cur[k];
      // only elements VISIBLE on both sides: appearing and disappearing is what
      // show()/hide() are for and is not a snap
      if (a[0] < 0.05 || b[0] < 0.05) continue;
      const dop = Math.abs(b[0] - a[0]);
      const dsc = Math.max(Math.abs(b[1] - a[1]), Math.abs(b[2] - a[2]));
      const dtr = Math.hypot(b[3] - a[3], b[4] - a[4]);
      if (dop > OP || dsc > SC || dtr > TR)
        out.push({ el: k, i: i, t: times[i], dop: +dop.toFixed(3),
                   dsc: +dsc.toFixed(3), dtr: +dtr.toFixed(1),
                   pre: a, post: b });
    }
    prev = cur;
  }
  return { jumps: out, track: track };
}
""".replace("OP", str(D_OPACITY)).replace("SC", str(D_SCALE)).replace("TR", str(D_TRANSLATE))


async def main():
    beats = json.load(open(os.path.join(HERE, "beats.json")))
    dur = beats["duration"]
    # a cut IS a discontinuity. The beat boundaries, the 0.56s wipes that straddle
    # them, and the two mid-b5 state moves are legitimate and excluded by name.
    cuts = [b["t"] for b in beats["beats"]] + [26.378, 33.258, dur]
    n = int(round(dur * FPS))
    times = [round(i / FPS, 6) for i in range(n + 1)]

    async with async_playwright() as p:
        br = await p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = await br.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.join(HERE, "index.html"))
        await pg.wait_for_timeout(2200)
        res = await pg.evaluate(PROBE, [times, FPS])
        await br.close()
    hits, track = res["jumps"], res["track"]

    def same(a, b, tol=0.02):
        return all(abs((x or 0) - (y or 0)) <= tol * max(1.0, abs(x or 0)) 
                   for x, y in zip(a, b))

    STATIC = 12        # frames of stillness that must precede a snap (0.5s)
    RETURN = 24        # ...and how long after it we look for the value coming back

    keep = []
    for h in hits:
        if any(abs(h["t"] - c) < 0.42 for c in cuts):
            continue
        tr, i = track.get(h["el"]) or [], h["i"]
        if i < STATIC + 1 or not tr:
            continue
        before = tr[i - 1]
        if before is None:
            continue
        # 1. was it STILL for half a second before the jump?
        window = [tr[j] for j in range(i - STATIC, i) if tr[j] is not None]
        if len(window) < STATIC or not all(same(w, before) for w in window):
            continue
        # 2. does it COME BACK to where it was?
        later = [tr[j] for j in range(i + 1, min(len(tr), i + RETURN + 1))
                 if tr[j] is not None]
        if not any(same(v, before) for v in later):
            continue
        keep.append(h)
    print("walked %d frames at %.3f fps; %d cut windows excluded"
          % (len(times), FPS, len(cuts)))
    if not keep:
        print("  no element jumps outside a cut   PASS")
        return 0
    seen = {}
    for h in keep:
        seen.setdefault(h["el"], h)
    for el, h in sorted(seen.items(), key=lambda kv: kv[1]["t"]):
        print("  ✗ t=%7.3f  %-22s dOpacity %.2f  dScale %.2f  dTranslate %.0fpx"
              % (h["t"], el[:22], h["dop"], h["dsc"], h["dtr"]))
    print("\n  %d element(s) jump outside a cut (%d frame hits)" % (len(seen), len(keep)))
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
