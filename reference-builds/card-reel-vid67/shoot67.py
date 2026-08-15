"""A beat contact sheet taken from the live page, before any render.

A render round costs minutes; this costs seconds and catches the things a
geometry gate cannot see — a beat that reads as empty, a colour that dies, a
cartoon standing in the wrong place. Videos are seeked by hand because nothing
is playing here: each <video> is parked at (t - its own data-start).

Usage:  python3 shoot67.py            # all beats
        python3 shoot67.py 4.96 6.4   # just these
"""
import os, sys, subprocess
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = "file://" + os.path.join(HERE, "index.html")
OUT = os.path.join(HERE, "qa")
os.makedirs(OUT, exist_ok=True)

BEATS = [0.0, 1.21, 2.2, 2.772, 3.24, 4.329, 5.22, 6.677, 7.869, 8.887, 9.72, 10.215, 10.62, 11.126, 11.54, 12.805, 13.84, 14.324, 14.72, 15.072, 15.36, 15.899, 16.34, 16.703, 17.0, 18.705, 20.1, 20.694, 21.18, 22.17, 22.98, 23.606, 24.119, 25.275, 26.22, 26.968, 27.58, 29.912, 31.82, 33.697, 35.1]

SEEK = """
(t) => {
  const tl = window.__timelines.vid67;
  tl.time(t, false);
  if (window.__CAPS) {                 // seeking suppresses the tl.call()
    let txt = '';
    for (const c of window.__CAPS) { if (c[0] <= t + 1e-6) txt = c[1]; else break; }
    document.getElementById('cap').textContent = txt;
  }
  const ps = [];
  for (const v of document.querySelectorAll('video')) {
    const s = parseFloat(v.getAttribute('data-start') || '0');
    const d = parseFloat(v.getAttribute('data-duration') || '999');
    let lt = t - s;
    if (lt < 0) lt = 0;
    if (lt > d) lt = Math.max(0, d - 0.05);
    if (lt > (v.duration || 999)) lt = Math.max(0, (v.duration || 0) - 0.05);
    ps.push(new Promise(res => {
      const done = () => { v.removeEventListener('seeked', done); res(); };
      v.addEventListener('seeked', done);
      try { v.currentTime = lt; } catch (e) { res(); }
      setTimeout(res, 900);
    }));
  }
  return Promise.all(ps).then(() => true);
}
"""

def main():
    want = [float(a) for a in sys.argv[1:]] or BEATS
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1080, "height": 1920},
                           device_scale_factor=1).new_page()
        pg.goto(DOC, wait_until="domcontentloaded", timeout=90000)
        for _ in range(40):
            pg.wait_for_timeout(500)
            if pg.evaluate("() => !!(window.__timelines && window.__timelines.vid67)"):
                break
        pg.wait_for_timeout(2500)
        pg.evaluate("() => { document.getElementById('stage').style.transform='scale(1)'; }")
        made = []
        for t in want:
            pg.evaluate(SEEK, t)
            pg.wait_for_timeout(260)
            f = os.path.join(OUT, "b_%06.3f.png" % t)
            pg.locator("#stage").screenshot(path=f)
            made.append(f)
            print("shot", "%.3f" % t)
        b.close()
    # one sheet per 12 beats, small enough to read as an image
    for i in range(0, len(made), 12):
        chunk = made[i:i+12]
        lst = os.path.join(OUT, "_l%d.txt" % i)
        open(lst, "w").write("".join("file '%s'\n" % c for c in chunk))
        sheet = os.path.join(OUT, "sheet%02d.jpg" % (i // 12))
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-frames:v", str(len(chunk)),
                        "-vf", "scale=270:480,tile=6x2", sheet, "-loglevel", "error"])
        print("sheet ->", sheet)

if __name__ == "__main__":
    main()
