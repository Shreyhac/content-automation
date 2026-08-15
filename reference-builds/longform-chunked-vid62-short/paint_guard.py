#!/usr/bin/env python3
"""Assert every timed caption is the thing that ACTUALLY PAINTS at its own position.

usage: python3 paint_guard.py

WHY THIS EXISTS
---------------
The short shipped with no captions for 27 of its 43 seconds and every gate passed.

`.cs` carried no `z-index`, so it computed to `auto` (0) while `.face` sits at 2. The
A-roll painted straight over every caption, and they only ever appeared on the
graphics beats where no face video happened to be on top. The owner's note was "Has
captions missing", and the client was exactly right.

Nothing caught it, and the reason is worth stating plainly:

  * `lint` and `validate` check the document and the console. A caption behind a
    video is neither a markup error nor a console error.
  * `safe_zones.py` measures WHERE every element is. The captions were exactly where
    they were supposed to be — y1396, inside every Instagram zone. It has no concept
    of whether the pixel that lands there belongs to them.
  * WCAG contrast passed too, because contrast is computed from declared colours.

Position is not visibility. This asks the browser the only question that settles it:
at the caption's own centre, `document.elementFromPoint` must return the caption (or
one of its own children), not something stacked above it.

The viewport is set to the full 1080x1920 so hit-test coordinates map 1:1 to the
composition. Probing a scaled-down viewport returns null and reads as a pass.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "index.html")

PROBE = """
() => {
  const tl = window.__timelines[Object.keys(window.__timelines)[0]];
  const _r = document.getElementById('root');
  _r.style.width = _r.dataset.width + 'px';
  _r.style.height = _r.dataset.height + 'px';
  const out = [];
  document.querySelectorAll('.cs.clip').forEach(cap => {
    const a = parseFloat(cap.getAttribute('data-start'));
    const d = parseFloat(cap.getAttribute('data-duration'));
    // sample inside the clip, away from its own fade edges
    [0.25, 0.5, 0.75].forEach(f => {
      const t = a + d * f;
      tl.pause(t);
      const b = cap.getBoundingClientRect();
      if (b.width < 4 || b.height < 4) {
        out.push({ id: cap.id, t: t, why: 'zero size' });
        return;
      }
      const cs = getComputedStyle(cap);
      if (cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.5) {
        out.push({ id: cap.id, t: t, why: 'opacity ' + cs.opacity });
        return;
      }
      // Replicate the renderer's CLIP SCHEDULING before hit-testing. A plain page
      // load does not apply it, so all 22 caption clips sit stacked at the same
      // coordinates and the last one in the DOM wins every hit test — which reads
      // as a failure on all 21 others and tells you nothing about the real question.
      const hidden = [];
      document.querySelectorAll('.cs.clip').forEach(o => {
        if (o === cap) return;
        const oa = parseFloat(o.getAttribute('data-start'));
        const od = parseFloat(o.getAttribute('data-duration'));
        if (t >= oa && t <= oa + od) return;      // genuinely co-scheduled: leave it
        hidden.push([o, o.style.display]);
        o.style.display = 'none';
      });
      // probe a few points across the line: a short caption leaves its box's
      // corners empty, so the centre of the first text line is the honest test
      const y = Math.round(b.y + Math.min(30, b.height / 2));
      let ok = false, saw = null;
      for (const fx of [0.5, 0.4, 0.6]) {
        const hit = document.elementFromPoint(Math.round(b.x + b.width * fx), y);
        if (!hit) continue;
        saw = saw || (hit.id || hit.className || hit.tagName);
        if (hit === cap || cap.contains(hit)) { ok = true; break; }
      }
      hidden.forEach(([o, d]) => { o.style.display = d; });
      if (!ok) out.push({ id: cap.id, t: t, why: 'painted under ' + saw });
    });
  });
  return out;
}
"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.abspath(PAGE))
        await pg.wait_for_timeout(1000)
        bad = await pg.evaluate(PROBE)
        n = await pg.evaluate("() => document.querySelectorAll('.cs.clip').length")
        await b.close()

    if not bad:
        print("  %d captions, all painting on top at 3 samples each   PASS" % n)
        return 0
    print("  %d caption sample(s) NOT visible:" % len(bad))
    for r in bad[:20]:
        print("     %-8s t=%6.2f  %s" % (r["id"], r["t"], r["why"]))
    print("\nFAIL")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
