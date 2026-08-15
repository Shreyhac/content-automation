#!/usr/bin/env python3
"""Assert every visible element against the Instagram safe zones, by MEASUREMENT.

usage: python3 safe_zones.py

WHY THIS EXISTS
---------------
Reading a tiled contact sheet is not good enough for this: at thumbnail scale I
misread the caption band as sitting inside the bottom UI band when it was
comfortably above it, and simultaneously missed that every caption was running
50px into the right rail. Overlay screenshots show you roughly where things are;
only getBoundingClientRect tells you exactly.

ZONES (SAFE-ZONES.md, 2026 numbers)
  top 150px              status bar / Reels chrome    -> no text
  y >= 1600              bottom UI band               -> no text, no face below
  x > 960, y 900..1600   like / comment / share rail  -> no text
  left 60px              crop buffer                  -> no text

The runtime controls .clip visibility, so this drives the timeline and checks each
caption only within its own scheduled window rather than trusting the DOM.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
TOP, BOTTOM, RAIL_X, RAIL_Y0, RAIL_Y1, LEFT = 150, 1600, 960, 900, 1600, 60

PROBE = """(t) => {
  const tl = window.__timelines[Object.keys(window.__timelines)[0]];
  const _r = document.getElementById('root');
  _r.style.width = _r.dataset.width + 'px';
  _r.style.height = _r.dataset.height + 'px';
  tl.pause(t);
  const bad = [], seen = [];
  document.querySelectorAll('#root *').forEach(el => {
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || parseFloat(s.opacity) < 0.06) return;
    // a .clip element is only really on screen inside its own scheduled window
    if (el.classList.contains('clip')) {
      const a = parseFloat(el.dataset.start || '0');
      const d = parseFloat(el.dataset.duration || '0');
      if (t < a || t > a + d) return;
    }
    const txt = (el.textContent || '').trim();
    const tag = el.tagName.toLowerCase();
    // Only INK is measured. A full-frame wrapper (.scene, #bg, #hook) is inset:0
    // by design and reporting its extent is pure noise — what matters is where
    // the text and images actually land.
    // THE LEAF RULE HAS A HOLE AND IT IS THE CAPTIONS. A cue that contains a <b>
    // accent has children, so it failed `el.children.length === 0` and was never
    // measured as a box — only its bold fragment was. Six of this film's 22 cues
    // carry one, including every cue that prints a figure, and a two-line cue is
    // exactly the thing that can reach the y1600 band. So a caption is ink by
    // class, whatever it contains.
    const isInk = (txt.length > 0 && el.children.length === 0) ||
                  el.classList.contains('cs') ||
                  tag === 'img' || tag === 'svg';
    if (!isInk) return;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return;
    const f = [];
    if (r.top < TOPZ) f.push('TOP_STRIP');
    if (r.bottom > BOTTOMZ) f.push('UI_BAND +' + Math.round(r.bottom - BOTTOMZ));
    if (r.right > RAILX && r.bottom > RAILY0 && r.top < RAILY1)
      f.push('RIGHT_RAIL +' + Math.round(r.right - RAILX));
    if (r.left < LEFTZ) f.push('LEFT_BUFFER');
    seen.push(el.id || el.className || el.tagName);
    if (f.length) bad.push({ id: el.id || el.className || el.tagName,
                             t: Math.round(r.top), b: Math.round(r.bottom),
                             l: Math.round(r.left), r: Math.round(r.right),
                             f: f.join(' '), txt: txt.slice(0, 34) });
  });
  return { bad: bad, seen: seen };
}""".replace("TOPZ", str(TOP)).replace("BOTTOMZ", str(BOTTOM)) \
    .replace("RAILX", str(RAIL_X)).replace("RAILY0", str(RAIL_Y0)) \
    .replace("RAILY1", str(RAIL_Y1)).replace("LEFTZ", str(LEFT))


async def main():
    dur = json.load(open(os.path.join(HERE, "beats.json")))["duration"]
    seen, n, measured = {}, 0, set()
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto("file://" + os.path.join(HERE, "index.html"))
        await pg.wait_for_timeout(2200)
        # 240 samples = one every 0.195s, which is shorter than the SHORTEST caption
        # clip in the file (0.30s). At 120 the step was 0.39s and six captions were
        # never sampled at all — the gate passed without ever having looked at them.
        SAMPLES = 240
        for i in range(SAMPLES + 1):
            t = dur * i / SAMPLES
            res = await pg.evaluate(PROBE, t)
            measured.update(res["seen"])
            for x in res["bad"]:
                key = (str(x["id"]), x["f"])
                if key not in seen:
                    seen[key] = (round(t, 2), x)
                n += 1
        await b.close()

    # A GATE REPORTING PASS OVER AN EMPTY SELECTOR IS INDISTINGUISHABLE FROM A GATE
    # REPORTING PASS OVER A CLEAN FILM. vid59's long-form ran card_guard and
    # band_guard over `.scene` for an entire production while the film's hook did
    # not carry the class — both said PASS, having measured nothing. So this says
    # WHAT it looked at, every run, and refuses to pass on a suspiciously small set.
    print(f"sampled {SAMPLES + 1} times across {dur:.2f}s")
    print(f"  measured {len(measured)} distinct ink elements: "
          + ", ".join(sorted(str(m)[:22] for m in measured)))
    if len(measured) < 20:
        print("  !! that is too few to be a real audit of this composition")
        return 1
    if not seen:
        print("  OK — every visible element is inside the Instagram safe zones")
        return 0
    for (eid, flags), (t, x) in sorted(seen.items(), key=lambda kv: kv[1][0]):
        print(f"  ✗ t={t:6.2f}  {eid[:26]:26} "
              f"l={x['l']:5d} r={x['r']:5d} t={x['t']:5d} b={x['b']:5d}  "
              f"{flags}  {x['txt']!r}")
    print(f"\n  {len(seen)} distinct violations ({n} sample hits)")
    return 1


sys.exit(asyncio.run(main()))
