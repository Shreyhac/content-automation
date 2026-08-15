#!/usr/bin/env python3
"""Report every stretch where the GRAPHICS do not move.

usage: python3 motion_guard.py [seconds_threshold]

CLAUDE.md has said "Nothing static >1s" since vid2 and nothing has ever checked it.
Round 1 of this short shipped seven held blocks — 3.4s, 3.6s, 3.8s, 4.8s and so on —
and the owner's note was "it's not perfect as of now. Need more and better animations
on the same." The same complaint on the long-form read "The animation is very still
here."

It samples the composition's DOM every 0.2s and fingerprints only what a viewer would
register as a change: each visible element's box, opacity and transform, rounded so
sub-pixel drift does not read as motion. A run of identical fingerprints is a held
block.

VIDEO IS EXCLUDED FROM THE FINGERPRINT ON PURPOSE. A <video> element's box never
changes while its content does, so counting it would mark every beat as moving and
the gate would never fire. A slow push ON a clip does register, because that is a
transform on the element.

This REPORTS rather than fails: a held frame can be deliberate (the hook's cover
frame, a beat that wants to breathe). It exists so the decision is made on purpose
instead of discovered by the client.
"""
import asyncio, os, re, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "index.html")
STEP = 0.2
THRESHOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 1.4

PROBE = """
(t) => {
  const tl = window.__timelines[Object.keys(window.__timelines)[0]];
  const _r = document.getElementById('root');
  _r.style.width = _r.dataset.width + 'px';
  _r.style.height = _r.dataset.height + 'px';
  tl.pause(t);
  const parts = [];
  document.getElementById('root').querySelectorAll('*').forEach(el => {
    if (el.closest('#bg') || el.id === 'cover') return;
    const c = getComputedStyle(el);
    if (c.visibility === 'hidden' || parseFloat(c.opacity) < 0.05) return;
    const b = el.getBoundingClientRect();
    if (b.width < 4 || b.height < 4) return;
    const tag = el.tagName;
    // a <video>'s box is constant while its picture moves; including it would mark
    // every beat as moving. A transform ON it still shows up, which is the point.
    const key = (el.id || el.className || tag) + ':' +
                Math.round(b.x) + ',' + Math.round(b.y) + ',' +
                Math.round(b.width) + ',' + Math.round(b.height) + ',' +
                (Math.round(parseFloat(c.opacity) * 20) / 20) + ',' +
                (c.transform === 'none' ? '-' : c.transform.replace(/[\\d.]+/g,
                   m => (Math.round(parseFloat(m) * 100) / 100).toString()));
    parts.push(key);
  });
  return parts.sort().join('|');
}
"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.abspath(PAGE))
        await pg.wait_for_timeout(1000)
        dur = await pg.evaluate(
            "() => parseFloat(document.getElementById('root').dataset.duration)")
        n = int(dur / STEP)
        prints = []
        for i in range(n + 1):
            t = round(i * STEP, 2)
            prints.append((t, await pg.evaluate(PROBE, t)))
        await b.close()

    runs, start, prev = [], prints[0][0], prints[0][1]
    for t, fp in prints[1:]:
        if fp != prev:
            if t - start >= THRESHOLD:
                runs.append((start, t, t - start))
            start, prev = t, fp
    if prints[-1][0] - start >= THRESHOLD:
        runs.append((start, prints[-1][0], prints[-1][0] - start))

    print("sampled %d points across %.2fs, threshold %.1fs" % (len(prints), dur, THRESHOLD))
    if not runs:
        print("  no held block over %.1fs   PASS" % THRESHOLD)
        return 0
    total = sum(r[2] for r in runs)
    print("  %d held block(s), %.1fs total (%.0f%% of the cut):"
          % (len(runs), total, 100 * total / dur))
    # A HELD BLOCK IS NOT NECESSARILY A HELD FRAME. This guard deliberately keeps
    # <video> out of the fingerprint — a video element's box never changes while its
    # picture does, so counting it would mark every beat as moving and the gate would
    # never fire. The cost is that a card holding a SCROLLING screen recording reads
    # here exactly like a card holding a still. So each block is annotated with the
    # clips scheduled underneath it, and the difference is stated instead of guessed.
    html = open(os.path.join(HERE, "index.html")).read()
    clips = [(m.group(1), float(m.group(2)), float(m.group(3)))
             for m in re.finditer(r'<video id="([^"]+)"[^>]*?data-start="([\d.]+)"'
                                  r'[^>]*?data-duration="([\d.]+)"', html, re.S)
             if not m.group(1).startswith("f")]
    for a, b_, g in runs:
        under = [c for c, cs, cd in clips if cs < b_ and cs + cd > a]
        print("     %6.2f - %6.2f   %.1fs held%s"
              % (a, b_, g, ("   (footage playing underneath: %s)" % ", ".join(under))
                 if under else "   — NOTHING is moving in this span"))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
